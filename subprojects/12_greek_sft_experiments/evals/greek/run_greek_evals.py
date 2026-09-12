#!/usr/bin/env python3
# RESOURCES: nodes=1 gpus=4 walltime=02:00 mem=220GB
"""Run or import the WP1b Greek evaluation bundle."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "greek-evals-v1"
MODEL_REPO = "fffoivos/apertus-8b-greek-cpt"
LANGUAGES = ("el", "en", "fr", "de")
NATIVE_BENCHMARKS = (
    "asep_mcqa",
    "demosqa",
    "gpcr",
    "medical_mcqa",
    "oyxoy_metaphor",
    "oyxoy_nli",
    "oyxoy_wic",
    "oyxoy_wsd_definition",
)

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
SUBPROJECTS_ROOT = REPO_ROOT.parent
DEFAULT_PYTHON = REPO_ROOT / "cluster" / "nsft_python.sh"  # persistent wrapper (system python3 + the nsft package); the old session-scratchpad venv is gone
DEFAULT_ELLINIKA = Path.home() / "Projects/apertus-local-chat/benchmark/clariden_eval.py"
DEFAULT_SCORER = (
    SUBPROJECTS_ROOT
    / "09_full_8b_cpt_results_analysis/evaluation/run_checkpoint_suite.py"
)
DEFAULT_NATIVE_RUNNER = (
    SUBPROJECTS_ROOT
    / "03_apertus_extension_and_embedding_adaptation/03_4_implementation_experiments/"
    "init_bakeoff/eval/run_native_greek_mcq_eval.py"
)
DEFAULT_REGISTRY = DEFAULT_NATIVE_RUNNER.with_name("native_greek_benchmark_registry.json")
DEFAULT_NATIVE_CONTRACT = (
    SUBPROJECTS_ROOT
    / "09_full_8b_cpt_results_analysis/evaluation/native_greek_3cp_contract.json"
)
DEFAULT_NATIVE_MANIFEST = Path(
    "/iopsstor/scratch/cscs/fffoivos/evals/full8_native_greek_3cp_20260812/"
    "frozen_examples_v2/manifest.json"
)
DEFAULT_CLEAN_MANIFEST = Path(
    "/capstor/scratch/cscs/fffoivos/cpt_runs/dataset-scheduling-0p5b/"
    "20260803T064000Z-static-prelaunch-v2/greekmmlu_clean_subset_manifest.json"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def command_record(stage: str, argv: list[str]) -> dict[str, Any]:
    return {"stage": stage, "argv": argv, "shell": shlex.join(argv)}


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"ERROR: {message}")


def read_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read {label} {path}: {exc}")
    if not isinstance(value, dict):
        fail(f"{label} is not a JSON object: {path}")
    return value


def require_file(path: Path, label: str) -> None:
    if not path.is_file():
        fail(f"missing {label}: {path}")


def git_value(path: Path, *args: str) -> str | None:
    try:
        root = subprocess.run(
            ["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"],
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()
        rel = str(path.resolve().relative_to(Path(root).resolve()))
        return subprocess.run(
            ["git", "-C", root, *args, "--", rel],
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip() or None
    except (OSError, ValueError, subprocess.CalledProcessError):
        return None


def file_provenance(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "git_commit": git_value(path, "log", "-1", "--format=%H"),
    }


def path_from_env(name: str, default: Path) -> Path:
    return Path(os.environ.get(name, str(default))).expanduser().resolve()


def external_paths() -> dict[str, Path]:
    return {
        "ellinika": path_from_env("ELLINIKA_CLARIDEN_EVAL", DEFAULT_ELLINIKA),
        "scorer": path_from_env("NATIVE_GREEK_SCORER", DEFAULT_SCORER),
        "native_runner": path_from_env("NATIVE_GREEK_RUNNER", DEFAULT_NATIVE_RUNNER),
        "registry": path_from_env("NATIVE_GREEK_REGISTRY", DEFAULT_REGISTRY),
        "native_contract": path_from_env("NATIVE_GREEK_CONTRACT", DEFAULT_NATIVE_CONTRACT),
        "native_manifest": path_from_env("NATIVE_GREEK_MANIFEST", DEFAULT_NATIVE_MANIFEST),
        "clean_manifest": path_from_env("GREEKMMLU_CLEAN_MANIFEST", DEFAULT_CLEAN_MANIFEST),
    }


def python_executable() -> str:
    override = os.environ.get("PYTHON")
    if override:
        return str(Path(override).expanduser())
    if DEFAULT_PYTHON.is_file():
        return str(DEFAULT_PYTHON)
    return sys.executable


def validate_run_name(value: str) -> str:
    if not value or value in {".", ".."} or Path(value).name != value or "/" in value or "\\" in value:
        fail("run_name must be one non-empty path component")
    return value


def resolve_model(model: str, revision: str | None) -> Path:
    candidate = Path(model).expanduser()
    if candidate.is_dir():
        return candidate.resolve()
    if candidate.exists():
        fail(f"model path is not a directory: {candidate}")
    try:
        from huggingface_hub import snapshot_download

        resolved = snapshot_download(
            repo_id=model,
            revision=revision,
            local_files_only=True,
        )
    except Exception as exc:  # noqa: BLE001 - turn library failures into a one-line preflight error
        fail(f"HF model is not fully cached for offline use ({model}@{revision or 'main'}): {exc}")
    return Path(resolved).resolve()


def validate_model_dir(path: Path) -> None:
    for name in ("config.json", "tokenizer.json"):
        require_file(path / name, f"model {name}")
    if not any(path.glob("*.safetensors")) and not (path / "pytorch_model.bin").is_file():
        fail(f"model weights are missing under {path}")


def validate_ellinika(path: Path) -> None:
    require_file(path, "ellinika clariden_eval.py")
    root = path.parent
    for name in ("bench.py", "greek.py", "config.json"):
        require_file(root / name, f"ellinika {name}")
    for language in LANGUAGES:
        data_dir = root / "data" / language
        if not data_dir.is_dir() or not any(data_dir.glob("*.jsonl")):
            fail(f"missing ellinika benchmark data for {language}: {data_dir}")


def validate_scoring_files(paths: dict[str, Path]) -> None:
    for key in ("scorer", "native_runner", "registry", "native_contract", "native_manifest", "clean_manifest"):
        require_file(paths[key], key.replace("_", " "))
    manifest = read_object(paths["native_manifest"], "native manifest")
    contract = read_object(paths["native_contract"], "native contract")
    expected_contract = manifest.get("contract", {}).get("sha256")
    if expected_contract != sha256_file(paths["native_contract"]):
        fail("native manifest/contract hash mismatch")
    examples = Path(str(manifest.get("examples", {}).get("path", ""))).expanduser()
    require_file(examples, "frozen native examples")
    if manifest.get("examples", {}).get("sha256") != sha256_file(examples):
        fail(f"frozen native example hash mismatch: {examples}")
    if int(manifest.get("examples", {}).get("rows", -1)) != 73_894:
        fail(
            "native manifest is not the strict 73,894-row population; set "
            "NATIVE_GREEK_CONTRACT and NATIVE_GREEK_MANIFEST to a matching strict bundle"
        )
    clean = read_object(paths["clean_manifest"], "GreekMMLU clean manifest")
    clean_ids = Path(str(clean.get("clean_example_ids", {}).get("path", ""))).expanduser()
    require_file(clean_ids, "GreekMMLU clean example IDs")
    if clean.get("clean_example_ids", {}).get("sha256") != sha256_file(clean_ids):
        fail(f"GreekMMLU clean-ID hash mismatch: {clean_ids}")
    if int(clean.get("clean_count", -1)) != 16_159:
        fail("GreekMMLU clean manifest does not contain 16,159 rows")
    if not contract.get("model_contract"):
        fail("native contract has no model_contract")


def preflight_cached_greekmmlu(registry_path: Path) -> None:
    registry = read_object(registry_path, "native benchmark registry")
    specs = [row for row in registry.get("benchmarks", []) if row.get("id") == "greekmmlu"]
    if len(specs) != 1:
        fail("registry does not contain exactly one GreekMMLU binding")
    spec = specs[0]
    try:
        from datasets import load_dataset

        dataset = load_dataset(
            spec["source"],
            spec.get("config"),
            revision=spec.get("revision"),
            split=spec.get("split", "test"),
        )
    except Exception as exc:  # noqa: BLE001
        fail(f"GreekMMLU benchmark data is not cached for offline use: {exc}")
    if len(dataset) != 16_632:
        fail(f"GreekMMLU cached row count is {len(dataset)}, expected 16632")


def load_module(path: Path, name: str):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        fail(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def ellinika_stage(args: argparse.Namespace) -> int:
    path = Path(args.clariden_eval).resolve()
    validate_ellinika(path)
    model_path = Path(args.model_path).resolve()
    validate_model_dir(model_path)
    upstream = load_module(path, "wp1b_clariden_eval")
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True, local_files_only=True)
    if args.mode == "chat" and not getattr(tokenizer, "chat_template", None):
        fail(f"chat mode requires a tokenizer chat template: {model_path}")
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        dtype=torch.bfloat16,
        trust_remote_code=True,
        local_files_only=True,
    ).to("cuda").eval()
    template_mode = "auto" if args.mode == "chat" else "off"
    result: dict[str, Any] = {
        "chat_template_mode": template_mode,
        "chat_template_present": bool(getattr(tokenizer, "chat_template", None)),
        "languages": {},
    }
    original_loader = upstream.bench.load_items
    for language in LANGUAGES:
        all_items = [item for item in original_loader(language) if item.get("type") != "judge"]
        if args.limit:
            all_items = all_items[: args.limit]
        pillars: dict[str, Any] = {}
        for pillar in sorted({str(item["bucket"]) for item in all_items}):
            selected = [item for item in all_items if str(item["bucket"]) == pillar]
            upstream.bench.load_items = lambda _language, rows=selected: rows
            metrics = upstream.run_lang(
                model,
                tokenizer,
                language,
                template_mode,
                args.max_new_tokens,
                0,
            )
            gen = metrics["gen_pillars"].get(pillar, {"acc": None, "n": 0})
            pillars[pillar] = {
                "accuracy_gen": gen["acc"],
                "n_gen": gen["n"],
                "accuracy_ll": metrics["mcq"]["acc_ll"],
                "n_ll": metrics["mcq"]["n"],
                "ll_population": "mcq_only",
                "format_valid_rate": metrics["format_valid_rate"],
                "flags": metrics["flags"],
            }
            print(f"HB step=ellinika-{language}-{pillar} loss=na tok/s=na mem=na", flush=True)
        upstream.bench.load_items = original_loader
        result["languages"][language] = {"n_items": len(all_items), "pillars": pillars}
    Path(args.stage_out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


def run_with_heartbeat(argv: list[str], stage: str, env: dict[str, str]) -> None:
    print(f"RUN {shlex.join(argv)}", flush=True)
    process = subprocess.Popen(argv, env=env)
    started = time.monotonic()
    next_heartbeat = started + 60
    while process.poll() is None:
        now = time.monotonic()
        if now >= next_heartbeat:
            print(
                f"HB step={stage} loss=na tok/s=na mem=na elapsed_s={int(now - started)}",
                flush=True,
            )
            next_heartbeat = now + 60
        time.sleep(2)
    if process.returncode:
        fail(f"{stage} failed with exit code {process.returncode}")


def summarize_prediction_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"accuracy": None, "n": 0}
    return {
        "accuracy": sum(bool(row["correct"]) for row in rows) / len(rows),
        "n": len(rows),
    }


def parse_native_metrics(path: Path) -> dict[str, dict[str, Any]]:
    metrics: dict[str, dict[str, Any]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("subject") == "__all__" and row.get("benchmark") in NATIVE_BENCHMARKS:
                metrics[row["benchmark"]] = {
                    "accuracy": float(row["accuracy"]),
                    "n": int(row["n"]),
                }
    if set(metrics) != set(NATIVE_BENCHMARKS):
        fail(f"native scorer returned the wrong benchmark set: {sorted(metrics)}")
    return metrics


def score_stage(args: argparse.Namespace) -> int:
    paths = {
        "scorer": Path(args.scorer).resolve(),
        "native_runner": Path(args.native_runner).resolve(),
        "registry": Path(args.registry).resolve(),
        "native_contract": Path(args.native_contract).resolve(),
        "native_manifest": Path(args.native_manifest).resolve(),
        "clean_manifest": Path(args.clean_manifest).resolve(),
    }
    validate_scoring_files(paths)
    model_path = Path(args.model_path).resolve()
    validate_model_dir(model_path)
    preflight_cached_greekmmlu(paths["registry"])

    stage_root = Path(args.stage_root).resolve()
    greek_root = stage_root / "greekmmlu"
    native_root = stage_root / "native"
    if greek_root.exists() or native_root.exists():
        fail(f"refusing to overwrite scorer stage under {stage_root}")

    python = args.python
    label = "wp1b"
    greek_cmd = [
        python,
        str(paths["native_runner"]),
        "--registry",
        str(paths["registry"]),
        "--benchmarks",
        "greekmmlu",
        "--model",
        f"{label}={model_path}",
        "--output-dir",
        str(greek_root),
        "--sample-size",
        str(args.limit),
        "--random-state",
        "42",
        "--dtype",
        "float32",
        "--max-input-tokens",
        "3072",
        "--candidate-batch-size",
        "16",
        "--example-batch-size",
        "16",
        "--trust-remote-code",
    ]
    native_cmd = [
        python,
        str(paths["scorer"]),
        "--contract",
        str(paths["native_contract"]),
        "--manifest",
        str(paths["native_manifest"]),
        "--native-runner",
        str(paths["native_runner"]),
        "--model",
        f"{label}={model_path}",
        "--output-dir",
        str(native_root),
        "--dtype",
        "float32",
        "--scorer-mode",
        "legacy",
        "--candidate-batch-size",
        "1",
        "--example-batch-size",
        "16",
        "--max-examples-per-benchmark",
        str(args.limit),
        "--benchmarks",
        "all",
    ]
    env = os.environ.copy()
    env["HF_HUB_OFFLINE"] = "1"
    env["HF_DATASETS_OFFLINE"] = "1"
    run_with_heartbeat(greek_cmd, "greekmmlu", env)
    print("HB step=greekmmlu-complete loss=na tok/s=na mem=na", flush=True)
    run_with_heartbeat(native_cmd, "native-greek", env)
    print("HB step=native-greek-complete loss=na tok/s=na mem=na", flush=True)

    predictions_path = greek_root / f"{label}_native_mcq_predictions.jsonl"
    require_file(predictions_path, "GreekMMLU predictions")
    predictions = [json.loads(line) for line in predictions_path.open(encoding="utf-8") if line.strip()]
    clean = read_object(paths["clean_manifest"], "GreekMMLU clean manifest")
    clean_ids_path = Path(clean["clean_example_ids"]["path"])
    clean_ids = {line.strip() for line in clean_ids_path.open(encoding="utf-8") if line.strip()}
    clean_rows = [row for row in predictions if str(row["example_id"]) in clean_ids]
    if args.limit == 0 and len(clean_rows) != 16_159:
        fail(f"clean GreekMMLU result contains {len(clean_rows)} rows, expected 16159")
    if args.limit > 0 and not clean_rows:
        fail("limited GreekMMLU sample contains no clean rows")

    native = parse_native_metrics(native_root / "metrics.csv")
    payload = {
        "greekmmlu": summarize_prediction_rows(clean_rows),
        "native_greek": {
            "benchmarks": native,
            "macro_accuracy": sum(row["accuracy"] for row in native.values()) / len(native),
        },
        "commands": [
            command_record("greekmmlu-upstream", greek_cmd),
            command_record("native-greek-upstream", native_cmd),
        ],
        "provenance": {
            "scorer": file_provenance(paths["scorer"]),
            "native_runner": file_provenance(paths["native_runner"]),
            "registry": file_provenance(paths["registry"]),
            "native_contract": file_provenance(paths["native_contract"]),
            "native_manifest": file_provenance(paths["native_manifest"]),
            "greekmmlu_clean_manifest": file_provenance(paths["clean_manifest"]),
        },
    }
    Path(args.stage_out).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


def select_card_entry(index: dict[str, Any], revision: str) -> dict[str, Any]:
    rows = list(index.get("checkpoints", [])) + list(index.get("averages", []))
    matches = [row for row in rows if revision in {row.get("revision"), row.get("branch")}]
    if revision == "main" and not matches:
        matches = [row for row in index.get("checkpoints", []) if row.get("revision") == "17-step18284-tokens77B"]
    if len(matches) != 1:
        fail(f"revision not found uniquely in checkpoint-index.json: {revision}")
    return matches[0]


def pull_card(revision: str, out: Path) -> int:
    try:
        from huggingface_hub import hf_hub_download

        index_path = Path(
            hf_hub_download(
                repo_id=MODEL_REPO,
                filename="checkpoint-index.json",
                revision="main",
            )
        )
    except Exception as exc:  # noqa: BLE001
        fail(f"could not fetch {MODEL_REPO}/checkpoint-index.json: {exc}")
    index = read_object(index_path, "checkpoint index")
    entry = select_card_entry(index, revision)
    native_raw = entry.get("native_greek", {})
    if set(native_raw) != set(NATIVE_BENCHMARKS):
        fail("checkpoint card does not contain the expected eight native-Greek benchmarks")
    native = {
        name: {"accuracy": float(native_raw[name]["accuracy"]), "n": int(native_raw[name]["n"])}
        for name in NATIVE_BENCHMARKS
    }
    now = utc_now()
    invocation = [sys.executable, str(Path(__file__).resolve()), "--pull-card", revision, "--out", str(out)]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "source": "card",
        "model": {"id": MODEL_REPO, "revision": revision, "resolved_path": None},
        "timestamps": {"started_utc": now, "completed_utc": now},
        "limit": None,
        "mode": "base",
        "commands": [command_record("pull-card", invocation)],
        "ellinika": {"available": False, "languages": {}},
        "greekmmlu": {
            "accuracy": float(entry["greekmmlu"]["accuracy"]),
            "n": int(entry["greekmmlu"]["n"]),
        },
        "native_greek": {
            "benchmarks": native,
            "macro_accuracy": sum(row["accuracy"] for row in native.values()) / len(native),
        },
        "provenance": {
            "checkpoint_index": {
                "repo_id": MODEL_REPO,
                "revision": "main",
                "filename": "checkpoint-index.json",
                "cached_path": str(index_path),
                "sha256": sha256_file(index_path),
                "declared_scorer": index.get("evaluation", {}).get("scorer"),
            }
        },
    }
    out = out.expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    temporary = out.with_name(out.name + ".partial")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, out)
    print(json.dumps({"ok": True, "out": str(out), "greekmmlu": payload["greekmmlu"]["accuracy"], "native_macro": payload["native_greek"]["macro_accuracy"]}, sort_keys=True))
    return 0


def launch(args: argparse.Namespace) -> int:
    run_name = validate_run_name(args.run_name)
    paths = external_paths()
    output_dir = REPO_ROOT / "results" / run_name
    output = output_dir / "greek.json"
    python = python_executable()

    display_model = args.model if not args.revision else f"{args.model}@{args.revision}"
    model_for_command = display_model if args.dry_run else str(resolve_model(args.model, args.revision))
    ellinika_out = output_dir / "ellinika_stage.json"
    scorer_out = output_dir / "scorer_stage.json"
    ellinika_cmd = [
        python,
        str(Path(__file__).resolve()),
        "--internal-ellinika",
        "--model-path",
        model_for_command,
        "--mode",
        args.mode,
        "--limit",
        str(args.limit),
        "--max-new-tokens",
        "64",
        "--clariden-eval",
        str(paths["ellinika"]),
        "--stage-out",
        str(ellinika_out),
    ]
    scorer_cmd = [
        python,
        str(Path(__file__).resolve()),
        "--internal-score",
        "--model-path",
        model_for_command,
        "--limit",
        str(args.limit),
        "--python",
        python,
        "--scorer",
        str(paths["scorer"]),
        "--native-runner",
        str(paths["native_runner"]),
        "--registry",
        str(paths["registry"]),
        "--native-contract",
        str(paths["native_contract"]),
        "--native-manifest",
        str(paths["native_manifest"]),
        "--clean-manifest",
        str(paths["clean_manifest"]),
        "--stage-root",
        str(output_dir),
        "--stage-out",
        str(scorer_out),
    ]
    resolved = {
        "model": display_model,
        "run_name": run_name,
        "mode": args.mode,
        "limit": args.limit,
        "output": str(output),
        "evaluation_populations": {
            "greekmmlu_clean_rows": 16_159,
            "native_greek_strict_rows": 73_894,
            "training_token_count": "not_applicable_to_evaluation",
        },
        "paths": {name: str(path) for name, path in paths.items()},
    }
    print(json.dumps(resolved, indent=2, sort_keys=True), flush=True)
    print(f"CMD ellinika-bench: {shlex.join(ellinika_cmd)}", flush=True)
    print(f"CMD greekmmlu+native: {shlex.join(scorer_cmd)}", flush=True)
    if args.dry_run:
        return 0

    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["HF_DATASETS_OFFLINE"] = "1"
    validate_ellinika(paths["ellinika"])
    validate_scoring_files(paths)
    preflight_cached_greekmmlu(paths["registry"])
    model_path = Path(model_for_command)
    validate_model_dir(model_path)
    if output_dir.exists():
        fail(f"refusing to overwrite run directory: {output_dir}")
    output_dir.mkdir(parents=True)
    env = os.environ.copy()
    env["HF_HUB_OFFLINE"] = "1"
    env["HF_DATASETS_OFFLINE"] = "1"
    started = utc_now()
    run_with_heartbeat(ellinika_cmd, "ellinika-bench", env)
    print("HB step=ellinika-bench-complete loss=na tok/s=na mem=na", flush=True)
    run_with_heartbeat(scorer_cmd, "greekmmlu-native", env)
    print("HB step=greekmmlu-native-complete loss=na tok/s=na mem=na", flush=True)

    ellinika = read_object(ellinika_out, "ellinika stage output")
    scores = read_object(scorer_out, "scorer stage output")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "source": "measured",
        "model": {"id": args.model, "revision": args.revision, "resolved_path": str(model_path)},
        "timestamps": {"started_utc": started, "completed_utc": utc_now()},
        "limit": args.limit or None,
        "mode": args.mode,
        "commands": [
            command_record("ellinika-bench", ellinika_cmd),
            command_record("greekmmlu+native", scorer_cmd),
            *scores["commands"],
        ],
        "ellinika": {"available": True, **ellinika},
        "greekmmlu": scores["greekmmlu"],
        "native_greek": scores["native_greek"],
        "provenance": {
            "ellinika": file_provenance(paths["ellinika"]),
            **scores["provenance"],
        },
    }
    temporary = output.with_name(output.name + ".partial")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, output)
    print(json.dumps({"ok": True, "out": str(output)}, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model")
    parser.add_argument("--run-name")
    parser.add_argument("--revision")
    parser.add_argument("--mode", choices=("chat", "base"), default="chat")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--pull-card")
    parser.add_argument("--out", type=Path)

    parser.add_argument("--internal-ellinika", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--internal-score", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--model-path", help=argparse.SUPPRESS)
    parser.add_argument("--clariden-eval", help=argparse.SUPPRESS)
    parser.add_argument("--max-new-tokens", type=int, default=64, help=argparse.SUPPRESS)
    parser.add_argument("--stage-out", help=argparse.SUPPRESS)
    parser.add_argument("--stage-root", help=argparse.SUPPRESS)
    parser.add_argument("--python", help=argparse.SUPPRESS)
    parser.add_argument("--scorer", help=argparse.SUPPRESS)
    parser.add_argument("--native-runner", help=argparse.SUPPRESS)
    parser.add_argument("--registry", help=argparse.SUPPRESS)
    parser.add_argument("--native-contract", help=argparse.SUPPRESS)
    parser.add_argument("--native-manifest", help=argparse.SUPPRESS)
    parser.add_argument("--clean-manifest", help=argparse.SUPPRESS)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.limit < 0:
        fail("--limit must be non-negative")
    if args.pull_card:
        if not args.out:
            fail("--pull-card requires --out")
        return pull_card(args.pull_card, args.out)
    if args.internal_ellinika:
        return ellinika_stage(args)
    if args.internal_score:
        return score_stage(args)
    if not args.model or not args.run_name:
        fail("normal operation requires --model and --run-name")
    return launch(args)


if __name__ == "__main__":
    raise SystemExit(main())
