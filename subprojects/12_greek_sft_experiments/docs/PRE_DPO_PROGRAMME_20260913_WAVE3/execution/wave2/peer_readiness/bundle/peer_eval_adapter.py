#!/usr/bin/env python3
"""Science-side adapter for the pinned Krikri v1.5 fixed evaluation.

This adapter owns benchmark/model identity and invokes the existing evaluator
assets.  Allocation and lifecycle remain outside this file.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def binding(path: Path) -> dict:
    return {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": sha256(path)}


def verify_binding(row: dict) -> None:
    path = Path(row["path"])
    if not path.is_file():
        raise RuntimeError(f"bound file is missing: {path}")
    observed = binding(path)
    if observed["bytes"] != row["bytes"] or observed["sha256"] != row["sha256"]:
        raise RuntimeError(f"binding drift: {path}")


def check_model(manifest: dict) -> Path:
    model = manifest["model"]
    path = Path(model["snapshot_path"])
    if not path.is_dir() or path.name != model["revision"]:
        raise RuntimeError(f"pinned model snapshot unavailable: {path}")
    required = ["config.json", "tokenizer_config.json", "tokenizer.json"]
    missing = [name for name in required if not (path / name).is_file()]
    if missing:
        raise RuntimeError(f"model snapshot lacks required files: {missing}")
    for row in model["files"]:
        item = Path(row["path"])
        if not item.is_file() or item.stat().st_size != row["bytes"]:
            raise RuntimeError(f"model file missing or wrong size: {item}")
        # Hugging Face LFS snapshot links name their immutable blob by SHA-256.
        # The allocation-free canonical preflight hashes bytes; the GPU-time
        # gate repeats the cheap link/size identity only.
        if item.resolve().name != row["sha256"]:
            raise RuntimeError(f"model blob identity drift: {item}")
    for row in model["control_files"]:
        item = Path(row["path"])
        if item.parent != path:
            raise RuntimeError(f"model control file escapes pinned snapshot: {item}")
        verify_binding(row)
    config = json.loads((path / "tokenizer_config.json").read_text())
    template = config.get("chat_template")
    if not isinstance(template, str) or not template:
        template_path = path / "chat_template.jinja"
        if not template_path.is_file():
            raise RuntimeError("snapshot has neither embedded nor file chat template")
        template = template_path.read_text()
    observed = hashlib.sha256(template.encode()).hexdigest()
    if observed != model["chat_template_sha256"]:
        raise RuntimeError(f"chat template drift: {observed}")
    return path


def tokenize_fixed_inputs(manifest: dict, model: Path, bundle: Path) -> dict:
    from transformers import AutoTokenizer

    source = bundle / "data/benchmarks_el/generate.py"
    spec = importlib.util.spec_from_file_location("peer_fixed_generate", source)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=True)
    maximum = manifest["generation"]["max_model_len"]
    exclusion_doc = json.loads((bundle / "multichallenge_context_exclusions.json").read_text())
    excluded = set(exclusion_doc["excluded_union_ids"])
    source_counts, counts, maxima, excluded_overlength, unexpected_overlength = {}, {}, {}, [], []
    for task in ("math500", "ifbench", "xstest", "multichallenge"):
        for lang in ("el", "en"):
            key = f"{task}_{lang}"
            source_n = 0; n = 0; high = 0
            for item_id, messages, requested in module.items(task, lang):
                source_n += 1
                encoded = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
                tokens = encoded["input_ids"] if hasattr(encoded, "keys") else encoded
                if tokens and isinstance(tokens[0], list):
                    if len(tokens) != 1: raise RuntimeError(f"unexpected batched tokenization for {key}:{item_id}")
                    tokens = tokens[0]
                size = len(tokens)
                is_excluded = task == "multichallenge" and str(item_id) in excluded
                if not is_excluded:
                    n += 1; high = max(high, size)
                if size + requested > maximum:
                    row = {"task": key, "id": str(item_id), "input_tokens": size, "requested_output_tokens": requested, "total": size + requested}
                    (excluded_overlength if is_excluded else unexpected_overlength).append(row)
            source_counts[key] = source_n; counts[key] = n; maxima[key] = high
    expected = manifest["tasks"]["fixed"]
    count_drift = {key: {"observed": counts.get(key), "expected": value} for key, value in expected.items() if counts.get(key) != value}
    return {"source_counts": source_counts, "retained_counts": counts, "excluded_union_count": len(excluded), "max_retained_input_tokens": maxima, "max_model_len": maximum, "excluded_overlength": excluded_overlength, "unexpected_overlength": unexpected_overlength, "count_drift": count_drift, "status": "passed" if not unexpected_overlength and not count_drift else "failed"}


def preflight(manifest_path: Path, output: Path | None) -> tuple[dict, Path, dict]:
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema_version") != "krikri_v15_peer_eval_science_v1":
        raise RuntimeError("science manifest schema drift")
    for row in manifest["inputs"]:
        verify_binding(row)
    model = check_model(manifest)
    token_gate = tokenize_fixed_inputs(manifest, model, manifest_path.parent)
    if output is not None and output.exists():
        raise FileExistsError(f"output must be new: {output}")
    return manifest, model, token_gate


def wait_ready(url: str, process: subprocess.Popen, seconds: int = 1200) -> None:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"vLLM exited during startup with {process.returncode}")
        try:
            with urllib.request.urlopen(url + "/models", timeout=10) as response:
                if response.status == 200:
                    return
        except Exception:
            pass
        time.sleep(5)
    raise TimeoutError("vLLM did not become ready within 1200 seconds")


def run_checked(argv: list[str], *, env: dict, log: Path) -> None:
    with log.open("w") as stream:
        proc = subprocess.run(argv, env=env, stdout=stream, stderr=subprocess.STDOUT)
    if proc.returncode:
        raise RuntimeError(f"command failed ({proc.returncode}); see {log}")


def collect_lm_eval_summary(raw: Path, expected: dict) -> dict:
    candidates = []
    for path in raw.rglob("*.json"):
        if "samples_" in path.name:
            continue
        try:
            payload = json.loads(path.read_text())
        except Exception:
            continue
        if isinstance(payload, dict) and isinstance(payload.get("results"), dict):
            candidates.append((path.stat().st_mtime_ns, path, payload))
    if not candidates:
        raise RuntimeError("lm-eval produced no result JSON")
    _, source, payload = max(candidates)
    observed_tasks = set(payload["results"])
    if observed_tasks != set(expected):
        raise RuntimeError(f"lm-eval task/config drift: {sorted(observed_tasks)}")
    samples = {}
    for task, count in expected.items():
        matches = list(raw.rglob(f"samples_{task}_*.jsonl"))
        if len(matches) != 1:
            raise RuntimeError(f"expected one {task} sample file, found {len(matches)}")
        rows = [json.loads(line) for line in matches[0].read_text().split("\n") if line.strip()]
        ids = [str(row.get("doc_id")) for row in rows]
        if len(rows) != count or len(set(ids)) != count:
            raise RuntimeError(f"{task} sample gate failed: rows={len(rows)}, unique_doc_ids={len(set(ids))}")
        samples[task] = {"rows": len(rows), "unique_doc_ids": len(set(ids)), "binding": binding(matches[0])}
    return {"source": str(source), "results": payload["results"], "samples": samples}


def jsonl_status(path: Path, expected: int) -> dict:
    rows = [json.loads(line) for line in path.read_text().split("\n") if line.strip()]
    ids = [str(row.get("id")) for row in rows]
    errors = sum(str(row.get("finish_reason", "")).startswith("error:") for row in rows)
    lengths = sum(row.get("finish_reason") == "length" for row in rows)
    if len(rows) != expected or len(set(ids)) != expected or errors:
        raise RuntimeError(
            f"output gate failed for {path.name}: rows={len(rows)}, unique={len(set(ids))}, errors={errors}"
        )
    return {"rows": len(rows), "unique_ids": len(set(ids)), "errors": errors, "length_finishes": lengths}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--preflight-report", type=Path)
    parser.add_argument("--iteration", type=int, default=0)
    parser.add_argument("--campaign-id", default="standalone-peer-eval")
    parser.add_argument("--evaluator-id", default="krikri-v1.5-fixed")
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--contract-digest", default="standalone")
    args = parser.parse_args()
    manifest, model, token_gate = preflight(args.manifest, None if args.preflight_only else args.output)
    if args.preflight_only:
        report = {"schema_version": "krikri_v15_allocation_free_preflight_v1", "status": token_gate["status"], "model": str(model), "inputs": len(manifest["inputs"]), "token_gate": token_gate}
        rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.preflight_report:
            if args.preflight_report.exists(): raise FileExistsError(args.preflight_report)
            args.preflight_report.write_text(rendered)
        print(rendered, end="")
        return 0 if report["status"] == "passed" else 1
    if token_gate["status"] != "passed":
        raise RuntimeError(f"fixed-input token gate failed: {token_gate}")
    if args.output is None:
        raise RuntimeError("--output is required unless --preflight-only is used")
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("full evaluation requires a Slurm allocation")

    attempt_root = args.output.parent
    attempt_root.mkdir(parents=True, exist_ok=False)
    fixed_out = attempt_root / "fixed"
    ilsp_out = attempt_root / "ilsp"
    logs = attempt_root / "logs"
    fixed_out.mkdir(); ilsp_out.mkdir(); logs.mkdir()
    bundle = args.manifest.parent
    env = os.environ.copy()
    env.update(HF_HOME=manifest["runtime"]["hf_home"], HF_HUB_OFFLINE="1", HF_DATASETS_OFFLINE="1")

    lm_env = env.copy(); lm_env["CUDA_VISIBLE_DEVICES"] = "1"
    lm_env["PYTHONPATH"] = manifest["runtime"]["lm_eval_pythonpath"] + os.pathsep + lm_env.get("PYTHONPATH", "")
    lm_cmd = [
        "python3", "-m", "lm_eval", "--model", "hf",
        "--model_args", f"pretrained={model},dtype=bfloat16",
        "--tasks", "ifeval_greek,mgsm_greek", "--apply_chat_template",
        "--include_path", str(bundle / "evals/ilsp/tasks"), "--batch_size", "32",
        "--output_path", str(ilsp_out), "--log_samples",
    ]
    serve_env = env.copy(); serve_env["CUDA_VISIBLE_DEVICES"] = "0"
    vllm_cmd = [
        manifest["runtime"]["vllm_executable"], "serve", str(model),
        "--served-model-name", manifest["model"]["served_name"], "--port", "8000",
        "--dtype", "bfloat16", "--max-model-len", "4096", "--gpu-memory-utilization", "0.85",
    ]
    vllm_log = (logs / "vllm.log").open("w")
    server = subprocess.Popen(vllm_cmd, env=serve_env, stdout=vllm_log, stderr=subprocess.STDOUT)
    started = time.time()
    try:
        wait_ready("http://127.0.0.1:8000/v1", server)
        run_checked([
            "python3", str(bundle / "data/benchmarks_el/generate.py"),
            "http://127.0.0.1:8000/v1", manifest["model"]["served_name"], str(fixed_out),
            "--workers", "8", "--limit", "8", "--exclude-ids-json", str(bundle / "multichallenge_context_exclusions.json"),
        ], env=env, log=logs / "fixed_smoke.log")
        smoke_status = {key: jsonl_status(fixed_out / f"{key}.jsonl", 8) for key in manifest["tasks"]["fixed"]}
        ilsp_log = (logs / "ilsp.log").open("w")
        ilsp = subprocess.Popen(lm_cmd, env=lm_env, stdout=ilsp_log, stderr=subprocess.STDOUT)
        run_checked([
            "python3", str(bundle / "data/benchmarks_el/generate.py"),
            "http://127.0.0.1:8000/v1", manifest["model"]["served_name"], str(fixed_out),
            "--workers", "24", "--exclude-ids-json", str(bundle / "multichallenge_context_exclusions.json"),
        ], env=env, log=logs / "fixed_generate.log")
    finally:
        if server.poll() is None:
            server.send_signal(signal.SIGTERM)
            try: server.wait(timeout=60)
            except subprocess.TimeoutExpired: server.kill(); server.wait()
        vllm_log.close()

    ilsp_rc = ilsp.wait(); ilsp_log.close()
    if ilsp_rc:
        raise RuntimeError(f"lm-eval failed ({ilsp_rc}); see {logs / 'ilsp.log'}")

    run_checked(["python3", str(bundle / "data/benchmarks_el/math500/score_math500.py"), str(fixed_out / "math500_el.jsonl"), str(fixed_out / "math500_el_score.json")], env=env, log=logs / "math500_el_score.log")
    run_checked(["python3", str(bundle / "data/benchmarks_el/math500/score_math500.py"), str(fixed_out / "math500_en.jsonl"), str(fixed_out / "math500_en_score.json")], env=env, log=logs / "math500_en_score.log")
    run_checked(["python3", str(bundle / "data/benchmarks_el/ifbench/score.py"), str(fixed_out / "ifbench_el.jsonl"), str(fixed_out / "ifbench_el_score.jsonl")], env=env, log=logs / "ifbench_el_score.log")
    run_checked(["python3", str(bundle / "data/benchmarks_el/ifbench/score.py"), str(fixed_out / "ifbench_en.jsonl"), str(fixed_out / "ifbench_en_score.jsonl")], env=env, log=logs / "ifbench_en_score.log")

    expected = manifest["tasks"]["fixed"]
    output_status = {}
    for task, count in expected.items():
        output_status[task] = jsonl_status(fixed_out / f"{task}.jsonl", count)
    artifacts = [binding(path) for path in sorted(attempt_root.rglob("*")) if path.is_file() and path != args.output]
    result = {
        "schema_version": "krikri_v15_peer_eval_result_v1", "status": "completed",
        "campaign_id": args.campaign_id, "evaluator_id": args.evaluator_id,
        "iteration": args.iteration, "attempt": args.attempt, "contract_digest": args.contract_digest,
        "model": manifest["model"], "generation": manifest["generation"],
        "elapsed_seconds": time.time() - started, "allocation_free_token_gate": token_gate,
        "fixed_smoke": smoke_status, "fixed_outputs": output_status,
        "ilsp": collect_lm_eval_summary(ilsp_out, manifest["tasks"]["ilsp"]), "artifacts": artifacts,
    }
    temporary = args.output.with_suffix(".tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
