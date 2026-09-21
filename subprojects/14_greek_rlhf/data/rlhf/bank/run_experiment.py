#!/usr/bin/env python3
"""One small experiment: a plan at the target distribution, filled with all three prompt types, on a COPY of the bank.

  python3 data/rlhf/bank/run_experiment.py --id E0 --n 30 --fake              # no model calls
  python3 data/rlhf/bank/run_experiment.py --id E1 --n 30                     # real Sol, medium
  python3 data/rlhf/bank/run_experiment.py --id E2 --n 10 --continue-from E1  # a second plan on E1's bank: nothing may be reused

Writes data/rlhf/bank/experiments/<id>/{bank.sqlite, report.json, PROMPTS.md, *.log}. Never touches the built bank.
Plan: docs/RLHF_COORDINATION/PROMPT_BANK_EXPERIMENT_PLAN_20260921.md
"""
import argparse, collections, json, pathlib, random, shutil, sys, time
HERE = pathlib.Path(__file__).resolve().parent; RL = HERE.parent; ROOT = RL.parents[1]
sys.path.insert(0, str(ROOT))
from rlhf.prompts import PromptBank, fill, apportion
from rlhf.prompts import slots as slotlib, seeded

def remaining(bank, plan, dim): return {r["key"]: r["remaining"] for r in bank.coverage(plan) if r["dimension"] == dim and r["mode"] == "share" and r["remaining"] > 0}

def joint_needs(bank, plan, rng):
    """Marginal quotas -> concrete (kind, purpose, language) needs. Any purpose can be written in any language by the
    seed generator, so the two marginals are paired at random; both then come out exactly."""
    P = [p for p, n in sorted(remaining(bank, plan, "purpose").items()) for _ in range(n)]
    L = [l for l, n in sorted(remaining(bank, plan, "language").items()) for _ in range(n)]
    if len(P) != len(L): raise SystemExit("marginals disagree: %d purposes vs %d languages still needed" % (len(P), len(L)))
    rng.shuffle(L)
    return [("dialogue" if p == "dialogue" else "seed", p, l) for p, l in zip(P, L)]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--id", required=True); ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--fake", action="store_true"); ap.add_argument("--continue-from", default=""); ap.add_argument("--seed", type=int, default=20260921)
    ap.add_argument("--with-dialogue", action="store_true", help="OFF by default (owner, 21 Sept: no dialogue here). Dialogue openings belong to the dialogue pipeline.")
    ap.add_argument("--report-only", action="store_true", help="write report.json + PROMPTS.md for an existing experiment directory; generate nothing")
    ap.add_argument("--max-dialogue", type=int, default=2, help="HARD cap on dialogue openings in this plan (owner, 21 Sept: 'you can run 2')")
    ap.add_argument("--cumulative", action="store_true", help="apportion against the running total of earlier plans. OPT-IN: on E3 it silently turned a "
                    "plan announced as '2 dialogue + 4 single-turn' into 6 dialogue, because E1's withdrawn dialogue places read as a deficit to catch up")
    ap.add_argument("--dry-plan", action="store_true", help="print the quotas this would create and stop. Costs nothing; run it before anything that calls a model")
    ap.add_argument("--note", default="", help="a scope change or anything else a reader needs in order to score this experiment correctly")
    ap.add_argument("--forum-share", type=float, default=1 / 3.0, help="forum's share of SINGLE-TURN prompts (legacy: 297 of 872)")
    a = ap.parse_args()
    T = json.load(open(RL / "target_distribution_v1.json")); out = HERE / "experiments" / a.id
    if a.report_only: return report(a, PromptBank(out / "bank.sqlite"), "%s-n%d" % (a.id, a.n), out, None, None, None, None, None)
    if out.exists(): raise SystemExit("%s exists; experiments are not overwritten" % out)
    out.mkdir(parents=True)
    src = (HERE / "experiments" / a.continue_from / "bank.sqlite") if a.continue_from else (HERE / "bank.sqlite")
    shutil.copy(src, out / "bank.sqlite")
    if a.continue_from and (HERE / "experiments" / a.continue_from / "gen").exists():     # the generator's own memory carries over too
        shutil.copytree(HERE / "experiments" / a.continue_from / "gen", out / "gen", symlinks=True)
    bank = PromptBank(out / "bank.sqlite"); rng = random.Random(a.seed + a.n); plan = "%s-n%d" % (a.id, a.n); t0 = time.time()

    purposes = {k: v for k, v in T["primary_purpose_shares_percent"].items() if a.with_dialogue or k != "dialogue"}   # renormalised by apportion()
    purpose_q = apportion(a.n, purposes)
    if purpose_q.get("dialogue", 0) > a.max_dialogue:                     # the cap is absolute; the places it frees go to the other purposes by their shares
        rest = apportion(a.n - a.max_dialogue, {k: v for k, v in purposes.items() if k != "dialogue"})
        purpose_q = dict(rest, dialogue=a.max_dialogue)
    purposes = {k: v for k, v in purpose_q.items() if v}                  # integer weights summing to n: apportion() returns them unchanged
    n_forum = int(round(a.forum_share * (a.n - purpose_q.get("dialogue", 0))))
    caps = {"kind": {"forum": n_forum}, "forum": {"astrovox": int(n_forum * T["forum_constraints"]["astrovox_max_percent_of_forum_prompts"] / 100.0)}}
    earlier = [r[0] for r in bank.db.execute("SELECT plan_id FROM plans ORDER BY created")] if (a.continue_from and a.cumulative) else ()
    bank.plan(plan, a.n, after=() if a.cumulative and "dialogue" in purposes else earlier, shares={"purpose": purposes, "language": T["language_shares_percent"]}, caps=caps)
    asked = {(r["dimension"], r["key"]): r["maximum"] for r in bank.coverage(plan)}
    print("QUOTAS for %s:" % plan, {"%s=%s" % k: v for k, v in asked.items() if v}, flush=True)      # always said BEFORE any model call
    if asked.get(("purpose", "dialogue"), 0) > a.max_dialogue: raise SystemExit("refusing: %d dialogue places > --max-dialogue %d" % (asked[("purpose", "dialogue")], a.max_dialogue))
    if a.dry_plan:
        bank.db.close(); shutil.rmtree(out); print("dry plan only: nothing generated, %s removed" % out); return
    before = {r[0] for r in bank.db.execute("SELECT source_id FROM sources WHERE state='consumed'")}
    backfilled = slotlib.backfill(bank)            # a bank copy from before the `slots` table existed gets its rows
    axes_before = slotlib.seed_space(bank, T)

    steps = [("forum", fill(bank, plan, "forum", n_forum, run=plan + "-forum", generator="forum-gate-v3"))]
    for rnd in (1, 2, 3):
        needs = joint_needs(bank, plan, rng)
        if not needs: break
        slotlib.build(bank, needs, prefix="%s%d" % (a.id, rnd), seed=a.seed + rnd, target=T)
        for kind in (("seed", "dialogue") if a.with_dialogue else ("seed",)):
            k = sum(1 for x in needs if x[0] == kind)
            if k: steps.append(("%s round %d" % (kind, rnd), seeded.generate_into(
                bank, plan, kind, k, run="%s-r%d" % (plan, rnd), workdir=out / "gen", fake=a.fake, max_rounds=2,
                legacy_registry=RL / "dialogue_v2" / "collection60" / "registry.sqlite",
                prior_runs=[RL / "dialogue_v2" / "collection60" / "runs", RL / "generator_v02" / "runs"])))

    return report(a, bank, plan, out, steps, asked, before, axes_before, t0)

def report(a, bank, plan, out, steps, asked, before, axes_before, t0):
    # CP2 H3: --report-only used to pass [] / {} / set() for what it had not observed, and the report then printed
    # "0 held of 0 slots issued (0%)" and "sources reused: []" -- two of the plan's five failure criteria reading GREEN
    # without having been measured. Unobserved is None, never zero. The generator's own receipts are read instead.
    live = steps is not None
    cov = bank.coverage(plan); audit = bank.audit()
    rows = [dict(r) for r in bank.db.execute("SELECT * FROM prompts WHERE plan_id=? ORDER BY kind, purpose, language, status", (plan,))]
    active = [r for r in rows if r["status"] == "active"]; held = [r for r in rows if r["status"] == "held"]
    reused = [r["source_id"] for r in rows if r["source_id"] in before] if live else None
    issued = gheld = 0; calls = collections.Counter()
    for rc in sorted((out / "gen" / "runs").glob("%s-*-seed-*/receipt.json" % plan)) + (sorted((out / "gen" / "runs").glob("%s-*-dialogue-*/receipt.json" % plan)) if a.with_dialogue else []):
        r = json.load(open(rc)); issued += r.get("slots", 0); gheld += r.get("held", 0)
        for k, v in (r.get("sol_calls") or {}).items(): calls[k] += v
    steps = steps or []
    rep = {"experiment": a.id, "plan": plan, "n": a.n, "fake_sol": a.fake, "continued_from": a.continue_from or None,
           "written_by": "the live run" if live else "--report-only, after the fact: fields the run would have observed are null, generator figures come from its receipts",
           "note": a.note or None, "seconds": round(time.time() - t0, 1) if live else None,
           "asked": {"%s=%s" % (r["dimension"], r["key"]): r["maximum"] for r in cov},
           "obtained_active": {"%s=%s" % (r["dimension"], r["key"]): r["filled"] for r in cov},
           "plan_met_exactly": all(r["remaining"] == 0 for r in cov if r["mode"] == "share") and all(r["filled"] <= r["maximum"] for r in cov),
           "unfilled": [r for r in cov if r["mode"] == "share" and r["remaining"] > 0],
           "by_kind": dict(collections.Counter(r["kind"] for r in active)), "held": len(held),
           "generator_slots_issued": issued, "generator_held": gheld,
           "generator_hold_rate": round(gheld / float(issued), 3) if issued else None, "generator_hold_rate_baseline": 0.18,
           "sources_reused_from_before_this_plan": reused, "seed_space_before": axes_before, "sol_calls": dict(calls), "audit": audit,
           "steps": [(name, {k: v for k, v in s.items() if k not in ("prompt_ids", "held_ids")}) for name, s in steps]}
    json.dump(rep, open(out / "report.json", "w"), ensure_ascii=False, indent=1, default=str)

    md = ["# %s — %d prompts, %s Sol\n" % (a.id, a.n, "FAKE" if a.fake else "real"),
          ("> **Note.** %s\n" % a.note) if a.note else "",
          "Plan met exactly: **%s** · active %d · generator held %d of %d slots issued (%.0f%%; baseline 18%%) · audit clean: **%s**\n" % (
           rep["plan_met_exactly"], len(active), gheld, issued, 100.0 * gheld / max(1, issued),
           audit["integrity"] == "ok" and not audit["quotas_overshot"] and all(v == 0 for k, v in audit.items() if k not in ("integrity", "quotas_overshot"))),
          "| dimension | key | asked | obtained |", "|---|---|---|---|"]
    md += ["| %s | %s | %s | %d |" % (r["dimension"], r["key"], r["maximum"] if r["mode"] == "share" else "≤ %d" % r["maximum"], r["filled"]) for r in cov]
    for r in rows:
        lin = bank.lineage(r["prompt_id"]); s = lin["source"]; lab = json.loads(r["labels"]) if isinstance(r["labels"], str) else r["labels"]
        origin = s["natural_key"] if s["kind"] == "forum" else "slot %s · %s/%s · %s · %s / %s / %s" % (
            s["payload"].get("slot_id"), s["payload"].get("purpose"), s["payload"].get("subtype"), s["payload"].get("difficulty"),
            s["payload"].get("register"), s["payload"].get("attitude"), s["payload"].get("detail"))
        md += ["\n---\n### `%s` · %s · %s · %s · **%s**%s" % (r["prompt_id"], r["kind"], r["purpose"], r["language"], r["status"],
               (" — " + (r["status_reason"] or "")) if r["status"] == "held" else ""),
               "source `%s` ← %s" % (s["source_id"], origin)]
        if s["kind"] != "forum": md += ["person: %s · situation: %s · topic: %s" % (s["payload"].get("person"), s["payload"].get("situation"), s["payload"].get("topic"))]
        for m in json.loads(r["messages"]) if isinstance(r["messages"], str) else r["messages"]: md += ["\n> **%s:** %s" % (m["role"], m["content"].replace("\n", "\n> "))]
    (out / "PROMPTS.md").write_text("\n".join(md) + "\n")
    print(json.dumps({k: rep[k] for k in ("plan", "plan_met_exactly", "by_kind", "generator_slots_issued", "generator_held", "generator_hold_rate", "sol_calls", "unfilled", "sources_reused_from_before_this_plan", "seconds")}, ensure_ascii=False, indent=1, default=str))
    print("audit:", {k: v for k, v in audit.items() if v not in (0, "ok", [])} or "clean"); print("->", out)

main()
