"""Drive generator 0.2 from the bank, without touching it.

generate.py is not modified -- other sessions have it open. It is run as a subprocess through flags it
already has, on exactly the slots the bank has CLAIMED:

    claim k slot-sources  ->  generate.py --manifest <those slots> --registry <private copy> --runs-dir <private>
                          ->  active  : bank.submit(...)                  fills the quota
                              held    : release and retry while rounds remain, then reject_source(...) with the
                                        generator's own reason (0.2 never writes a held prompt's text, so there is
                                        nothing to register; bank 'held' status exists for generators that do)
                              nothing : bank.reject_source(...)           the generator produced no row for it

The generator keeps its OWN duplicate memory (a registry + runs/*/instances.jsonl). It is given a private
copy of a legacy registry and symlinks to the earlier runs, so it still steers away from what it has made
before. The bank enforces the same thing independently at submit(): two fences, not one.
"""
import collections, json, os, pathlib, shutil, subprocess, sys
from .bank import DuplicateError, QuotaError

RL = pathlib.Path(__file__).resolve().parents[2] / "data" / "rlhf"
GENERATE = RL / "generator_v02" / "generate.py"

def prepare_workdir(workdir, legacy_registry, prior_runs):
    """A private registry copy and a runs dir that can SEE every earlier run but writes only its own."""
    workdir = pathlib.Path(workdir); (workdir / "runs").mkdir(parents=True, exist_ok=True)
    reg = workdir / "generator_registry.sqlite"
    if not reg.exists(): shutil.copy(legacy_registry, reg)
    for d in prior_runs:
        for run in sorted(pathlib.Path(d).iterdir()):
            link = workdir / "runs" / run.name
            if run.is_dir() and not link.exists(): os.symlink(run.resolve(), link)
    return reg, workdir / "runs"

def _still_claimed(bank, batch):
    ids = [s["source_id"] for s in batch]
    return [r[0] for r in bank.db.execute("SELECT source_id FROM sources WHERE state='claimed' AND source_id IN (%s)" % ",".join("?" * len(ids)), ids)] if ids else []

def generate_into(bank, plan_id, kind, n, *, run, workdir, legacy_registry, prior_runs, fake=False, workers=8, max_rounds=4,
                  python=sys.executable, timeout=3600, generator_script=None):
    """Register up to n ACTIVE prompts of `kind` ('seed' or 'dialogue') into the plan. Held prompts are registered too
    but do not count, so the loop keeps claiming until the quota is genuinely filled or nothing claimable is left."""
    reg, runs = prepare_workdir(workdir, legacy_registry, prior_runs)
    made, held, skipped, calls, issued = [], [], collections.Counter(), collections.Counter(), 0
    for rnd in range(1, max_rounds + 1):
        batch = []
        while len(made) + len(batch) < n:
            src = bank.claim(plan_id, kind, worker="%s#%d" % (run, rnd))
            if src is None: break
            batch.append(src)
        if not batch: break
        name = "%s-%s-r%d" % (run, kind, rnd); manifest = pathlib.Path(workdir) / ("%s.manifest.json" % name)
        manifest.write_text(json.dumps({"version": "bank-plan:%s" % plan_id, "slots": [s["payload"] for s in batch]}, ensure_ascii=False, indent=1))
        cmd = [python, str(generator_script or GENERATE), "--run", name, "--manifest", str(manifest), "--slots", ",".join(s["payload"]["slot_id"] for s in batch),
               "--registry", str(reg), "--runs-dir", str(runs), "--workers", str(workers)] + (["--fake"] if fake else [])
        # CP1 H2: everything from here to the end of the batch used to be unguarded, so ONE bad row (malformed JSON, a
        # missing file, an unexpected submit error) left the whole batch 'claimed' -- and a stuck claim reserves its place
        # in the plan for ever. Whatever happens, no source leaves this block still claimed.
        try:
            issued += len(batch)
            _one_round(bank, plan_id, batch, cmd, name, workdir, runs, rnd, max_rounds, made, held, skipped, calls, timeout)
        finally:
            for sid in _still_claimed(bank, batch): bank.release(sid)
        if len(made) >= n: break
    gen_held = skipped["held_then_retried"] + skipped["held_and_spent"]
    return {"registered_active": len(made), "registered_held": len(held), "prompt_ids": made, "held_ids": held,
            "skipped": dict(skipped), "sol_calls": dict(calls), "asked_for": n, "slots_issued_to_generator": issued,
            # CP1 H3: generator 0.2 never writes a held prompt's text, so `registered_held` is ALWAYS 0 for it and a hold
            # rate computed from it can never be anything but 0.0. The generator's real hold rate is counted here.
            "generator_held": gen_held, "generator_hold_rate": round(gen_held / float(issued), 3) if issued else None}

def _one_round(bank, plan_id, batch, cmd, name, workdir, runs, rnd, max_rounds, made, held, skipped, calls, timeout):
        try: p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired: raise RuntimeError("generate.py did not finish within %ds for %s" % (timeout, name))
        (pathlib.Path(workdir) / ("%s.log" % name)).write_text(p.stdout + "\n--- stderr ---\n" + p.stderr)
        if p.returncode != 0:
            raise RuntimeError("generate.py exited %d for %s; see %s.log\n%s" % (p.returncode, name, name, p.stderr[-800:]))
        out = runs / name
        rows = {r["slot_id"]: r for r in map(json.loads, open(out / "prompts.jsonl"))} if (out / "prompts.jsonl").exists() else {}
        rc = json.load(open(out / "receipt.json")) if (out / "receipt.json").exists() else {}
        for k, v in (rc.get("sol_calls") or {}).items(): calls[k] += v
        for s in batch:
            r = rows.get(s["payload"]["slot_id"])
            if r is None:
                bank.reject_source(s["source_id"], "generator produced no prompt (instance collision or missing)"); skipped["no_prompt"] += 1; continue
            if not r.get("messages"):
                # generator 0.2 never writes the text of a held prompt to prompts.jsonl (checked across every legacy run), so
                # there is nothing to register. While rounds remain, RELEASE the slot: it is re-claimed next round and gets a
                # fresh instance, which is what --retry-held does, and its cell stays covered. On the last round it is spent.
                why = "; ".join(map(str, r.get("held_reasons") or ["?"]))[:300]
                if rnd < max_rounds: bank.release(s["source_id"]); skipped["held_then_retried"] += 1
                else: bank.reject_source(s["source_id"], "generator held it %d times: %s" % (max_rounds, why)); skipped["held_and_spent"] += 1
                continue
            msgs = r["messages"] if isinstance(r["messages"], list) else json.loads(r["messages"])
            labels = {"slot_id": r["slot_id"], "underlying_purpose": r.get("purpose"), "subtype": r.get("subtype"), "instance_key": r.get("instance_key"),
                      "repair_rounds": r.get("repair_rounds"), "held_reasons": r.get("held_reasons"), "labels_verified": r.get("labels_verified"),
                      "maths_content": r.get("maths_content"), "generator_run": name, "code_sha16": r.get("code_sha16"), "glossary_sha16": r.get("glossary_sha16")}
            status = "active" if r["status"] == "active" else "held"
            try:
                pid = bank.submit(s["source_id"], msgs, plan_id=plan_id, run=name, generator="generator-%s" % r.get("generator_version", "0.2"),
                                  labels=labels, status=status, reason="; ".join(map(str, r.get("held_reasons") or [])) or None)
                (made if status == "active" else held).append(pid)
            except DuplicateError as e:
                bank.reject_source(s["source_id"], "%s of %s (%.2f)" % (type(e).__name__, e.existing, e.similarity)); skipped[type(e).__name__] += 1
            except QuotaError as e:
                bank.release(s["source_id"]); skipped["quota: %s" % e] += 1
