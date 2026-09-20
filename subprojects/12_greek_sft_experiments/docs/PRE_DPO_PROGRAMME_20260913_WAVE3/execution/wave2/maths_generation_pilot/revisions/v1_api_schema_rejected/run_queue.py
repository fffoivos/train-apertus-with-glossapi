#!/usr/bin/env python3
"""Generic frozen-payload queue with bounded calls and resumable receipts.

Default invocation is a read-only plan. Execution requires --execute and the
literal acknowledgement. Acceptance is intentionally generic: declared schema
validity, exact row identity, and frozen payload/prompt/model bindings.
"""
from __future__ import annotations

import argparse
import asyncio
import datetime
import fcntl
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
ACK = "PREPARED_PAYLOAD_REVIEWED"
SUPPORTED_SCHEMA_KEYS = {"$schema", "type", "enum", "additionalProperties", "required", "properties", "items"}
QUOTA_MARKERS = ("usage limit", "rate limit reached", "insufficient_quota", "quota exceeded", "rate_limit_exceeded")


def utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_text(value: str) -> str:
    return sha_bytes(value.encode())


def canonical_sha(value: Any) -> str:
    return sha_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    # splitlines() also splits valid U+2028/U+2029 characters inside JSON strings.
    return [json.loads(line) for line in path.read_text().split("\n") if line.strip()]


def atomic_json(path: Path, value: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    os.replace(tmp, path)


def get_field(value: Any, dotted: str) -> Any:
    for key in dotted.split("."):
        if not isinstance(value, dict) or key not in value:
            raise KeyError(f"missing field {dotted!r}")
        value = value[key]
    return value


def check_schema(schema: Any, path: str = "$") -> None:
    """Fail closed on schema features outside this bundled generic subset."""
    if not isinstance(schema, dict):
        raise ValueError(f"{path}: schema must be an object")
    unsupported = set(schema) - SUPPORTED_SCHEMA_KEYS
    if unsupported:
        raise ValueError(f"{path}: unsupported schema keywords {sorted(unsupported)}")
    for key, child in schema.get("properties", {}).items():
        check_schema(child, f"{path}.properties.{key}")
    if "items" in schema:
        check_schema(schema["items"], f"{path}.items")


def validate_json(value: Any, schema: dict[str, Any], path: str = "$") -> None:
    names = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None), "number": (int, float), "integer": int}
    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(isinstance(value, names[t]) and not (t in {"number", "integer"} and isinstance(value, bool)) for t in types):
            raise ValueError(f"{path}: expected {types}, got {type(value).__name__}")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{path}: {value!r} is not in enum")
    if isinstance(value, dict):
        missing = set(schema.get("required", [])) - set(value)
        if missing:
            raise ValueError(f"{path}: missing {sorted(missing)}")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = set(value) - set(props)
            if extra:
                raise ValueError(f"{path}: additional keys {sorted(extra)}")
        for key, child in props.items():
            if key in value:
                validate_json(value[key], child, f"{path}.{key}")
    if isinstance(value, list) and "items" in schema:
        for index, child in enumerate(value):
            validate_json(child, schema["items"], f"{path}[{index}]")


def resolve(value: Any, record: dict[str, Any], accepted: dict[str, dict[str, Any]]) -> Any:
    if isinstance(value, list):
        return [resolve(x, record, accepted) for x in value]
    if not isinstance(value, dict):
        return value
    if set(value) == {"$record"}:
        return get_field(record, value["$record"])
    if "$dependency" in value:
        if set(value) != {"$dependency", "field"}:
            raise ValueError(f"invalid dependency resolver {value!r}")
        return get_field(accepted[value["$dependency"]], value["field"])
    return {k: resolve(v, record, accepted) for k, v in value.items()}


def requirements_met(job: dict[str, Any], accepted: dict[str, dict[str, Any]]) -> tuple[bool, str]:
    for req in job.get("dependency_requirements", []):
        try:
            actual = get_field(accepted[req["dependency"]], req["field"])
        except (KeyError, TypeError) as exc:
            return False, f"cannot read requirement: {exc}"
        if req["op"] == "equals" and actual != req.get("value"):
            return False, f"{req['dependency']}.{req['field']}={actual!r}, expected {req.get('value')!r}"
        if req["op"] == "nonempty_string" and (not isinstance(actual, str) or not actual.strip()):
            return False, f"{req['dependency']}.{req['field']} is not a nonempty string"
    return True, ""


def verified_assets(manifest: dict[str, Any], queue_relative: str, inputs_relative: str) -> None:
    hashes = manifest.get("artifact_sha256", {})
    required = {inputs_relative, queue_relative, "run_queue.py"}
    required |= {name for name in hashes if name.startswith("schemas/") or name.startswith("prompts/")}
    missing = required - set(hashes)
    if missing:
        raise ValueError(f"manifest lacks required artifact hashes: {sorted(missing)}")
    for relative in sorted(required):
        if sha_bytes((ROOT / relative).read_bytes()) != hashes[relative]:
            raise ValueError(f"frozen artifact changed: {relative}")


def validate_queue(jobs: list[dict[str, Any]], records: dict[str, dict[str, Any]]) -> None:
    required = {"job_id", "stage", "row_id", "model", "effort", "schema", "template", "depends_on", "payload"}
    ids = [j.get("job_id") for j in jobs]
    if len(ids) != len(set(ids)):
        raise ValueError("job_id values must be unique")
    known = set(ids)
    for job in jobs:
        missing = required - set(job)
        if missing:
            raise ValueError(f"{job.get('job_id')}: missing {sorted(missing)}")
        if job["row_id"] not in records:
            raise ValueError(f"{job['job_id']}: unknown row_id")
        if any(dep not in known for dep in job["depends_on"]):
            raise ValueError(f"{job['job_id']}: unknown dependency")
        for req in job.get("dependency_requirements", []):
            if req.get("dependency") not in job["depends_on"] or req.get("op") not in {"equals", "nonempty_string"}:
                raise ValueError(f"{job['job_id']}: invalid dependency requirement")
        schema_path, template_path = ROOT / job["schema"], ROOT / job["template"]
        if not schema_path.is_file() or not template_path.is_file() or ROOT not in schema_path.resolve().parents or ROOT not in template_path.resolve().parents:
            raise ValueError(f"{job['job_id']}: schema/template must be under pilot root")
        check_schema(json.loads(schema_path.read_text()))
    unresolved = {j["job_id"]: set(j["depends_on"]) for j in jobs}
    done: set[str] = set()
    while unresolved:
        ready = {jid for jid, deps in unresolved.items() if deps <= done}
        if not ready:
            raise ValueError("dependency cycle")
        done |= ready
        for jid in ready:
            del unresolved[jid]


def binding(job: dict[str, Any], record: dict[str, Any], accepted: dict[str, dict[str, Any]]) -> tuple[str, dict[str, str]]:
    payload = resolve(job["payload"], record, accepted)
    template = (ROOT / job["template"]).read_text()
    if template.count("{{INPUT_JSON}}") != 1:
        raise ValueError("template must contain exactly one INPUT_JSON marker")
    prompt = template.replace("{{INPUT_JSON}}", json.dumps(payload, ensure_ascii=False, indent=2))
    fields = {"job_spec_sha256": canonical_sha(job), "input_record_sha256": canonical_sha(record), "payload_sha256": canonical_sha(payload), "template_sha256": sha_bytes((ROOT/job["template"]).read_bytes()), "schema_sha256": sha_bytes((ROOT/job["schema"]).read_bytes()), "prompt_sha256": sha_text(prompt)}
    return prompt, fields


def load_and_verify_accepted(jobs: list[dict[str, Any]], records: dict[str, dict[str, Any]], accepted_dir: Path) -> dict[str, dict[str, Any]]:
    envelopes = {p.stem: json.loads(p.read_text()) for p in accepted_dir.glob("*.json")} if accepted_dir.exists() else {}
    accepted: dict[str, dict[str, Any]] = {}
    remaining = {j["job_id"]: j for j in jobs if j["job_id"] in envelopes}
    while remaining:
        progressed = False
        for jid, job in list(remaining.items()):
            if not all(dep in accepted for dep in job["depends_on"]):
                continue
            requirements_ok, requirements_detail = requirements_met(job, accepted)
            if not requirements_ok:
                raise ValueError(f"accepted output dependency gate failed: {jid}: {requirements_detail}")
            _, fields = binding(job, records[job["row_id"]], accepted)
            envelope = envelopes[jid]
            for key, expected in fields.items():
                if envelope.get(key) != expected:
                    raise ValueError(f"accepted output binding mismatch: {jid} {key}")
            if envelope.get("model") != job["model"] or envelope.get("effort") != job["effort"]:
                raise ValueError(f"accepted output model/effort mismatch: {jid}")
            result = envelope["result"]
            validate_json(result, json.loads((ROOT/job["schema"]).read_text()))
            if result.get("row_id") != job["row_id"]:
                raise ValueError(f"accepted output row mismatch: {jid}")
            accepted[jid] = result
            del remaining[jid]
            progressed = True
        if not progressed:
            raise ValueError("accepted outputs have missing or unverified dependencies")
    return accepted


async def main_async(args: argparse.Namespace) -> int:
    manifest = json.loads((ROOT / "manifest.json").read_text())
    manifest_cap = int(manifest["counts"]["absolute_call_cap"])
    retry_cap = int(manifest["counts"]["retry_cap"])
    call_cap = manifest_cap if args.call_cap is None else args.call_cap
    if call_cap > manifest_cap or call_cap < 1:
        raise SystemExit(f"call cap must be 1..{manifest_cap}")
    queue_path, input_path = (ROOT / args.queue).resolve(), (ROOT / args.inputs).resolve()
    if ROOT not in queue_path.parents or ROOT not in input_path.parents:
        raise SystemExit("queue and inputs must be under pilot root")
    verified_assets(manifest, str(queue_path.relative_to(ROOT)), str(input_path.relative_to(ROOT)))
    if args.limit_new_calls < 0 or args.timeout_seconds < 1:
        raise SystemExit("limit-new-calls must be nonnegative and timeout-seconds must be positive")
    jobs, rows = read_jsonl(queue_path), read_jsonl(input_path)
    records = {r["row_id"]: r for r in rows}
    if len(records) != len(rows):
        raise SystemExit("duplicate row_id in inputs")
    validate_queue(jobs, records)
    state_dir = ROOT / args.state_dir
    if ROOT not in state_dir.resolve().parents:
        raise SystemExit("state-dir must be under the pilot root")
    accepted_dir, attempts_dir = state_dir / "accepted", state_dir / "attempts"
    if args.execute:
        accepted_dir.mkdir(parents=True, exist_ok=True); attempts_dir.mkdir(parents=True, exist_ok=True)
    accepted = load_and_verify_accepted(jobs, records, accepted_dir)
    stage_counts: dict[str, int] = {}
    for job in jobs: stage_counts[job["stage"]] = stage_counts.get(job["stage"], 0) + 1
    prior_receipts = list(attempts_dir.glob("*.receipt.json")) if attempts_dir.exists() else []
    print(json.dumps({"mode":"execute" if args.execute else "plan","queue":str(queue_path.relative_to(ROOT)),"jobs":len(jobs),"accepted":len(accepted),"pending":len(jobs)-len(accepted),"stage_counts":stage_counts,"max_workers":args.max_workers,"manifest_call_cap":manifest_cap,"runtime_call_cap":call_cap,"global_retry_cap":retry_cap,"prior_calls":len(prior_receipts),"limit_new_calls":args.limit_new_calls,"max_attempts_per_job":2}, ensure_ascii=False, indent=2))
    if not args.execute: return 0
    if args.acknowledge_reviewed_payload != ACK:
        raise SystemExit(f"execution requires --acknowledge-reviewed-payload {ACK}")
    if not 1 <= args.max_workers <= 8: raise SystemExit("max-workers must be 1..8")
    lockfile = (state_dir / "run.lock").open("w")
    try: fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError: raise SystemExit("another process holds this run-state lock")
    lockfile.write(str(os.getpid())); lockfile.flush()
    receipts_by_job: dict[str, list[Path]] = {}
    for p in prior_receipts:
        receipt=json.loads(p.read_text()); receipts_by_job.setdefault(receipt["job_id"], []).append(p)
    reserved, new_reserved = len(prior_receipts), 0
    retry_reserved = sum(int(json.loads(p.read_text()).get("attempt", 1)) > 1 for p in prior_receipts)
    mutex, sem, stop_dispatch = asyncio.Lock(), asyncio.Semaphore(args.max_workers), asyncio.Event()
    quota_stop=False; failures: dict[str,str]={}

    async def run_one(job: dict[str, Any]) -> tuple[str,bool,str]:
        nonlocal reserved,new_reserved,retry_reserved,quota_stop
        jid=job["job_id"]
        try: prompt,fields=binding(job,records[job["row_id"]],accepted)
        except Exception as exc: return jid,False,"preflight binding error: "+str(exc)
        async with sem:
            if stop_dispatch.is_set(): return jid,False,"dispatch stopped"
            async with mutex:
                used=len(receipts_by_job.get(jid,[]))
                if used>=2: return jid,False,"two-attempt job cap reached"
                if used and retry_reserved>=retry_cap: return jid,False,"global retry cap reached"
                if reserved>=call_cap: stop_dispatch.set(); return jid,False,"runtime call cap reached"
                if args.limit_new_calls and new_reserved>=args.limit_new_calls: stop_dispatch.set(); return jid,False,"new-call probe limit reached"
                attempt=used+1; reserved+=1; new_reserved+=1; retry_reserved+=int(attempt>1); call_index=reserved
            try:
                prefix=attempts_dir/f"{jid}.{attempt}"; final=Path(str(prefix)+".response.json"); receipt_path=Path(str(prefix)+".receipt.json"); events=Path(str(prefix)+".events.jsonl"); errfile=Path(str(prefix)+".stderr.txt")
                receipt={"job_id":jid,"row_id":job["row_id"],"stage":job["stage"],"attempt":attempt,"call_index":call_index,"state":"running","started":utc(),"runner_pid":os.getpid(),"model":job["model"],"effort":job["effort"],**fields}
                atomic_json(receipt_path,receipt); receipts_by_job.setdefault(jid,[]).append(receipt_path)
                codex="/opt/homebrew/bin/codex" if Path("/opt/homebrew/bin/codex").exists() else "codex"
                cmd=[codex,"exec","--ignore-user-config","--ephemeral","--skip-git-repo-check","--sandbox","read-only","-C","/tmp","-m",job["model"],"-c",f"model_reasoning_effort={job['effort']}","-c","project_doc_max_bytes=0","-c","features.remote_plugin=false","-c","features.apps=false","-c","features.code_mode_host=false","--json","--output-schema",str(ROOT/job["schema"]),"-o",str(final),"-"]
                started=time.time(); proc=await asyncio.create_subprocess_exec(*cmd,stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
                receipt["call_pid"]=proc.pid; atomic_json(receipt_path,receipt)
                try: stdout,stderr=await asyncio.wait_for(proc.communicate(prompt.encode()),timeout=args.timeout_seconds)
                except asyncio.TimeoutError:
                    proc.kill(); stdout,stderr=await proc.communicate(); events.write_bytes(stdout); errfile.write_bytes(stderr); raise RuntimeError("finite call timeout")
                events.write_bytes(stdout); errfile.write_bytes(stderr)
                combined=(stdout+b"\n"+stderr).decode(errors="replace").lower()
                if any(marker in combined for marker in QUOTA_MARKERS): quota_stop=True; stop_dispatch.set(); raise RuntimeError("quota/rate limit: stopped new dispatch")
                if proc.returncode: raise RuntimeError(f"codex exit {proc.returncode}: {stderr.decode(errors='replace')[-350:]}")
                result=json.loads(final.read_text()); validate_json(result,json.loads((ROOT/job["schema"]).read_text()))
                if result.get("row_id")!=job["row_id"]: raise ValueError("row identity mismatch")
                usage=None
                for line in stdout.decode(errors="replace").split("\n"):
                    try:event=json.loads(line)
                    except ValueError:continue
                    if event.get("type")=="turn.completed":usage=event.get("usage")
                envelope={"job_id":jid,"row_id":job["row_id"],"stage":job["stage"],"attempt":attempt,"model":job["model"],"effort":job["effort"],**fields,"result":result}
                atomic_json(accepted_dir/f"{jid}.json",envelope)
                receipt.update(state="accepted",finished=utc(),seconds=round(time.time()-started,2),exit_code=proc.returncode,usage=usage,events_file=events.name,stderr_file=errfile.name); atomic_json(receipt_path,receipt)
                async with mutex: accepted[jid]=result
                return jid,True,"accepted"
            except Exception as exc:
                if "receipt" in locals(): receipt.update(state="failed",finished=utc(),seconds=round(time.time()-started,2) if "started" in locals() else None,error=str(exc)); atomic_json(receipt_path,receipt)
                return jid,False,str(exc)

    while True:
        remaining=[j for j in jobs if j["job_id"] not in accepted and j["job_id"] not in failures]
        if not remaining or stop_dispatch.is_set():break
        ready=[]
        for job in remaining:
            if not all(dep in accepted for dep in job["depends_on"]):continue
            ok,detail=requirements_met(job,accepted)
            if ok:ready.append(job)
            else:failures[job["job_id"]]="dependency gate failed: "+detail
        if args.limit_new_calls:
            ready=ready[:max(0,args.limit_new_calls-new_reserved)]
        if not ready:break
        for jid,ok,detail in await asyncio.gather(*(run_one(job) for job in ready)):
            if ok:print(f"accepted {jid}",flush=True)
            elif len(receipts_by_job.get(jid,[]))>=2 or "limit reached" in detail or "cap reached" in detail or "stopped" in detail or detail.startswith("preflight"): failures[jid]=detail; print(f"failed {jid}: {detail}",file=sys.stderr,flush=True)
    summary={"finished":utc(),"runner_pid":os.getpid(),"accepted":len(accepted),"queue_jobs":len(jobs),"calls_total":reserved,"retry_calls":retry_reserved,"new_calls":new_reserved,"quota_stop":quota_stop,"failures":failures}; atomic_json(state_dir/"summary.json",summary)
    return 0 if len(accepted)==len(jobs) else 2


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--queue",default="queue.jsonl"); parser.add_argument("--inputs",default="inputs.jsonl"); parser.add_argument("--state-dir",default="run_state"); parser.add_argument("--max-workers",type=int,default=8); parser.add_argument("--call-cap",type=int); parser.add_argument("--limit-new-calls",type=int,default=0,help="bounded probe without editing the frozen master queue"); parser.add_argument("--timeout-seconds",type=int,default=1200); parser.add_argument("--execute",action="store_true"); parser.add_argument("--acknowledge-reviewed-payload",choices=[ACK]); return asyncio.run(main_async(parser.parse_args()))


if __name__=="__main__": raise SystemExit(main())
