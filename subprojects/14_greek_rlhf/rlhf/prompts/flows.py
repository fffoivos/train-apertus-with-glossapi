"""The two ways a prompt gets made, each as two calls: bring the sources in, then fill a plan from them.

    ingest_forum_gate(bank, "data/rlhf/pool/forum_gated_v3.jsonl")     # gate output -> forum sources
    ingest_seeds(bank, seed_rows, origin="generator-0.3")              # seed instances -> seed sources

    fill(bank, "round4", "forum", 150, run="R4-forum", generator="forum-gate-v3")            # the gate already wrote the prompt
    fill(bank, "round4", "seed",  350, run="R4-seed",  generator="generator-0.3", render=f)  # f(source) -> messages, e.g. a Sol call

fill() is the ONLY loop a caller needs. It claims an unused source whose cell has room, renders, and
submits; a duplicate or an unrenderable source is rejected for good and the loop moves to the next one,
so the count it returns is prompts actually registered. It stops when the plan is full, the supply is
exhausted, or n is reached -- and says which.
"""
import collections, json
from .bank import DuplicateError, QuotaError, source_id_for
from .migrate import FORUM_PURPOSE

def ingest_forum_gate(bank, path, origin="forum-gate-v3"):
    """One source per URL. A thread that was gated more than once is still one source (the first row wins, as before)."""
    by_url = collections.OrderedDict()
    for line in open(path):
        if line.strip():
            r = json.loads(line); by_url.setdefault(r["url"], []).append(r)
    n = collections.Counter()
    for url, rs in by_url.items():
        r = rs[0]; g = r.get("gate") or {}
        ok = g.get("post_kind") in ("request", "social") and str(g.get("self_contained")) == "True" and bool((g.get("prompt_el") or "").strip())
        known = bank.db.execute("SELECT 1 FROM sources WHERE source_id=?", (source_id_for("forum", url),)).fetchone()
        bank.add_source("forum", url, forum=r["forum"], purpose=FORUM_PURPOSE.get(g.get("task_type"), "everyday"), language="el", origin=origin,
                        payload={"gated_ids": [x["id"] for x in rs], "task_type_v3": g.get("task_type"), "prompt_el": g.get("prompt_el"),
                                 "post_kind": g.get("post_kind"), "false_premise": g.get("false_premise"), "title": r.get("title"), "section": r.get("section")},
                        state="available" if ok else "rejected", reason=None if ok else "gate: %s, self_contained=%s" % (g.get("post_kind"), g.get("self_contained")))
        n["already_known" if known else ("accepted" if ok else "rejected_by_gate")] += 1
    return dict(n)

def ingest_seeds(bank, rows, origin, kind="seed"):
    """rows: dicts with at least `purpose` and `language`. The source's identity is the canonical JSON of the seed,
    so the same seed offered twice -- by a re-run, or by two generators -- is one source."""
    n = collections.Counter()
    for seed in rows:
        key = json.dumps({k: v for k, v in seed.items() if not k.startswith("_")}, ensure_ascii=False, sort_keys=True)
        known = bank.db.execute("SELECT 1 FROM sources WHERE source_id=?", (source_id_for(kind, key),)).fetchone()
        bank.add_source(kind, key, purpose=seed["purpose"], language=seed["language"], payload=seed, origin=origin)
        n["already_known" if known else "added"] += 1
    return dict(n)

def forum_prompt(source):
    """The forum gate has already rewritten the post into a self-contained prompt."""
    return [{"role": "user", "content": source["payload"]["prompt_el"]}]

def fill(bank, plan_id, kind, n, *, run, generator, render=None, worker="fill", labels=None, **cell):
    """Register up to n prompts of `kind` into the plan. `cell` narrows the draw (purpose=, language=, forum=)."""
    render = render or (forum_prompt if kind == "forum" else None)
    if render is None: raise ValueError("kind %r needs a render(source) -> messages" % kind)
    made, skipped = [], collections.Counter()
    while len(made) < n:
        src = bank.claim(plan_id, kind, worker=worker, **cell)
        if src is None: break
        try:
            messages = render(src)
        except Exception as e:                       # a source that cannot be rendered is spent, not retried forever
            bank.reject_source(src["source_id"], "render failed: %s" % str(e)[:200]); skipped["render_failed"] += 1; continue
        if not messages:
            bank.reject_source(src["source_id"], "render returned nothing"); skipped["render_empty"] += 1; continue
        try:
            made.append(bank.submit(src["source_id"], messages, plan_id=plan_id, run=run, generator=generator, labels=(labels(src) if callable(labels) else labels)))
        except DuplicateError as e:
            bank.reject_source(src["source_id"], "%s of %s (%.2f)" % (type(e).__name__, e.existing, e.similarity)); skipped[type(e).__name__] += 1
        except QuotaError:
            bank.release(src["source_id"]); skipped["lost_a_race_for_the_last_place"] += 1; break
    left = bank.claim(plan_id, kind, worker=worker + ":probe", **cell)
    if left: bank.release(left["source_id"])
    why = "reached n" if len(made) >= n else ("no unused source fits the plan any more" if left is None else "stopped")
    return {"registered": len(made), "prompt_ids": made, "skipped": dict(skipped), "stopped_because": why}
