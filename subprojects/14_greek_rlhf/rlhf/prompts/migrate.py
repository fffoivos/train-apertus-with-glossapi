"""Carry the legacy registry into a PromptBank, THROUGH the constraints -- and report what they object to.

The legacy file is opened read-only and is never modified. Every legacy prompt goes in by submit(), the
same door new prompts use, so this doubles as the audit the old schema could not run on itself:
whatever it had been getting away with surfaces here as a refusal, and is reported rather than forced.

  python -m rlhf.prompts migrate <legacy registry.sqlite> <new bank.sqlite>
"""
import collections, json, sqlite3
from .bank import PromptBank, DuplicateError, NearDuplicateError, SourceError, source_id_for

FORUM_PURPOSE = {"question": "factual", "explanation": "factual", "calculation": "math", "advice": "everyday", "opinion": "everyday",
                 "share": "everyday", "translation": "everyday", "other": "everyday", "create": "everyday", "recommendation": "everyday"}
STATUS = {"active": "active", "superseded": "superseded", "archived": "archived", "excluded": "rejected"}
ORDER = {"superseded": 0, "archived": 0, "excluded": 0, "active": 1}      # live prompts last: one live prompt per source

def seed_kind(generator_version):
    if generator_version == "0.1": return "template"
    return "dialogue" if generator_version.startswith("dialogue") else "seed"

def migrate(legacy_path, bank_path):
    old = sqlite3.connect("file:%s?mode=ro" % legacy_path, uri=True); old.row_factory = sqlite3.Row
    bank = PromptBank(bank_path); rep = collections.OrderedDict(); find = collections.defaultdict(list)

    forum_sid, seed_sid = {}, {}
    for r in old.execute("SELECT * FROM sources"):
        p = json.loads(r["payload"]); rejected = r["status"] != "gate_accepted"
        forum_sid[r["source_id"]] = bank.add_source(
            "forum", r["url"], forum=r["forum"], purpose=FORUM_PURPOSE.get(p.get("task_type_v3"), "everyday"), language="el",
            payload=dict(p, legacy_source_id=r["source_id"], file=r["file"], row_id=r["row_id"], content_sha=r["content_sha"]),
            origin=r["gate_version"] or "forum-gate", state="rejected" if rejected else "available", reason=r["status"] if rejected else None)
    for r in old.execute("SELECT * FROM seeds"):
        seed_sid[r["seed_id"]] = bank.add_source(
            seed_kind(r["generator_version"]), r["seed_canonical"], purpose=(r["task"] or "unknown").split(":")[0].split("/")[0].strip(),
            language=r["language"] or "el", payload=dict(json.loads(r["seed_json"]), legacy_seed_id=r["seed_id"], legacy_status=r["status"]),
            origin="generator-" + r["generator_version"])
    rep["sources_carried"] = {"forum": len(forum_sid), "seed_like": len(seed_sid)}

    rows = sorted(old.execute("SELECT * FROM prompts").fetchall(), key=lambda r: (ORDER[r["status"]], r["logical_id"]))
    done = collections.Counter(); new_id = {}
    for r in rows:
        sid = forum_sid.get(r["source_id"]) if r["source_kind"] == "forum" else seed_sid.get(r["seed_id"])
        if sid is None:
            # the legacy row names a seed that was never in its seeds table. Do not invent a link silently:
            # register the source from what the prompt itself says, and SAY it was synthesised.
            kind = r["source_kind"] if r["source_kind"] in ("dialogue", "template") else "seed"
            sid = bank.add_source(kind, r["seed_id"] or r["logical_id"], purpose=r["primary_purpose"], language=r["language"],
                                  payload={"synthesised_during_migration": True, "legacy_seed_id": r["seed_id"], "legacy_logical_id": r["logical_id"]},
                                  origin=r["generator_version"])
            find["source_missing_in_legacy_so_synthesised"].append(r["logical_id"])
        kw = dict(run=r["round_first"] or "legacy", generator=r["generator_version"], purpose=r["primary_purpose"], language=r["language"],
                  status=STATUS[r["status"]], reason=r["status_reason"],
                  labels=dict(json.loads(r["labels"] or "{}"), task_type=r["task_type"], detail=r["detail"], register=r["register"],
                              attitude=r["attitude"], maths_content=r["maths_content"], keepable=r["keepable"], legacy_logical_id=r["logical_id"]))
        try:
            try: pid = bank.submit(sid, json.loads(r["messages"]), **kw)
            except NearDuplicateError as e:
                find["near_duplicate_admitted_as_legacy"].append("%s ~ %s (%.2f)" % (r["logical_id"], e.existing, e.similarity))
                pid = bank.submit(sid, json.loads(r["messages"]), allow_near_duplicate=True, **kw)
        except DuplicateError as e: find["REFUSED_exact_duplicate"].append("%s = %s" % (r["logical_id"], e.existing)); continue
        except SourceError as e: find["REFUSED_source"].append("%s: %s" % (r["logical_id"], e)); continue
        new_id[r["logical_id"]] = pid; bank.alias(r["logical_id"], pid, "legacy logical_id"); done[(r["source_kind"], STATUS[r["status"]])] += 1
    for a in old.execute("SELECT alias, logical_id, round FROM aliases"):
        if a["logical_id"] in new_id and a["alias"] != a["logical_id"]: bank.alias(a["alias"], new_id[a["logical_id"]], "legacy alias, %s" % a["round"])

    rep["prompts_in_legacy"] = len(rows); rep["prompts_carried"] = sum(done.values())
    rep["carried_by_kind_and_status"] = {"%s/%s" % k: v for k, v in sorted(done.items())}
    rep["findings"] = {k: {"count": len(v), "examples": v[:5]} for k, v in find.items()}
    rep["audit_after"] = bank.audit()
    live_forum = collections.Counter(r[0] for r in bank.db.execute("SELECT forum FROM prompts WHERE kind='forum' AND status='active'"))
    n = sum(live_forum.values())
    rep["legacy_forum_shares_percent"] = {f: round(100.0 * c / n, 1) for f, c in live_forum.most_common()} if n else {}
    rep["supply_unused_forum_sources"] = sum(r["n"] for r in bank.supply("forum"))
    bank.db.close(); old.close(); return rep
