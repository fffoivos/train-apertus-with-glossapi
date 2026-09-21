#!/usr/bin/env python3
"""Seeds for the 60-dialogue collection. Openings come from generator 0.2 (runs/C60-*/prompts.jsonl, --manifest manifest.json);
this step adds only what a dialogue needs and never rewrites an opening: the user's private state, the evaluator reference,
and a deterministic world table (troubleshooting) or a learner state (learning). Batched Sol calls at medium effort,
validated in code (seeds.validate_seed, worlds.validate_world), one repair call per failing batch, frozen to seeds.json.
Usage: python3 data/rlhf/dialogue_v2/collection60/seeds_c60.py [--traits-only]"""
from __future__ import annotations

import argparse, collections, json, pathlib, random, sys
HERE = pathlib.Path(__file__).resolve().parent; DV2 = HERE.parent; sys.path.insert(0, str(DV2))
from common import atomic_json, read_json, sha256_json, utcnow   # noqa: E402
from contracts import DEV_TAGS, MAX_ASSISTANT_TURNS, _enum, _obj, S, B        # noqa: E402
from glossary import Glossary                                                  # noqa: E402
from ledger import CallLedger                                                  # noqa: E402
import worlds                                                                  # noqa: E402
from seeds import validate_seed                                                # noqa: E402

VERSION = "c60-seed-writer-v1"
RUNTIME = HERE / "runtime"
GROUP_OF = {"C": "correction", "T": "troubleshooting", "L": "learning"}
ARR = lambda item: {"type": "array", "items": item}
FV = _obj({"flag": S, "value": S})
USER_STATE = _obj({"goal": S, "known_facts": ARR(S), "expertise": _enum(["novice", "intermediate", "expert"]), "misconception": S,
                   "disclosed_preferences": ARR(S), "private_preferences": ARR(_obj({"id": S, "text": S, "reveal_when": S}))})
REFERENCE = _obj({"checkable_constraints": ARR(S), "supplied_facts": ARR(S), "what_a_good_first_reply_does": S, "maths_content": B})
WORLD = _obj({"root_cause": S, "hidden_facts": ARR(S), "valid_resolutions": ARR(S),
              "state_flags": ARR(_obj({"flag": S, "initial": S, "domain": ARR(S)})),
              "derived_rules": ARR(_obj({"name": S, "any_of": ARR(ARR(FV))})),
              "checks": ARR(_obj({"check_id": S, "description": S, "preconditions": S, "effects": ARR(FV),
                                  "conditional_effects": ARR(_obj({"when": ARR(FV), "set": ARR(FV)})),
                                  "observations": ARR(_obj({"when": ARR(FV), "text": S}))}))})
LEARNER = _obj({"knowledge_items": ARR(_obj({"item_id": S, "text": S, "status": _enum(["understood", "partly_understood", "not_understood"])})),
                "misconception": S, "transfer_question": S, "subject_knowledge": ARR(S),
                "transfer_check": _obj({"question": S, "answer": S, "what_to_check": S}), "grading_rule": S})


def schema(group: str) -> dict:
    item = {"case_id": S, "user_state": USER_STATE, "evaluator_reference": REFERENCE}
    if group == "troubleshooting":
        item["world"] = WORLD
    if group == "learning":
        item["learner"] = LEARNER
    return _obj({"items": ARR(_obj(item))})


COMMON = """SEED WRITER v1 (60-dialogue collection, development only). Each item is a real opening message a person already wrote to a Greek-language AI assistant, with the private task instance behind it (givens, constraints, deliverable, answer conditions), the person and their story. A simulated version of this person will continue the conversation for up to six turns, reacting to what the assistant actually says. Write ONLY the private material that simulation and its evaluator need. Never rewrite, translate or extend the opening.

For every item:
- user_state.goal: what this person wants to end up with, in one sentence (English).
- user_state.known_facts: what this person knows and could tell if asked (English), consistent with the opening and the instance. Never include anything the person could not know.
- user_state.expertise: novice, intermediate or expert, from the person and story.
- user_state.misconception: a mistaken belief this person holds that matters for the task, or empty.
- user_state.disclosed_preferences: the requirements the opening already states (English, one per item).
- user_state.private_preferences: one or two plausible preferences the opening does NOT state, each with an id (P1, P2) and reveal_when (the visible situation in which this person would mention it). Keep them modest: they must not make the task impossible or contradict the opening.
- evaluator_reference: checkable_constraints (what a correct reply must satisfy, from the opening and instance), supplied_facts (facts the person supplied), what_a_good_first_reply_does (one or two sentences), maths_content (true when correctness depends on calculation or mathematics).
"""
TROUBLE = """TROUBLESHOOTING items additionally need a deterministic simulated world, so that every step the person carries out yields a fixed, consistent observation:
- root_cause: the single hidden cause of the symptom (consistent with the opening and fixable by an ordinary user).
- hidden_facts: 4-7 facts about the situation the person does not know; valid_resolutions: 1-3 ways that actually fix it (a workaround may count).
- state_flags: 2-4 flags describing the situation, each with an initial value and its full domain (short strings; use "true"/"false" for yes/no flags). At least one flag must change when the problem is fixed.
- derived_rules: 1-3 derived boolean flags, e.g. {"name": "fixed", "any_of": [[{"flag": "cable", "value": "replaced"}], [{"flag": "driver", "value": "updated"}]]}. A rule may use raw flags and earlier derived flags.
- checks: 8-14 steps an ordinary user might plausibly try or be told to try, INCLUDING the steps that reveal the cause, the steps that fix it, and plausible useless steps (restart, reinstall and so on). Each check: check_id (snake_case), description, preconditions (or empty), effects (flags the step sets), conditional_effects (flags set only when `when` matches the state before the step), observations (what the person sees, in English, factual and specific: exact messages, names, numbers). Observations are matched in order against the state AFTER the step, using raw and derived flags: list specific cases first and ALWAYS end with one observation whose `when` is empty (the default). Never use curly braces in any text. Useless steps must not fix anything. The person's known_facts must never reveal the root cause.
"""
LEARN = """LEARNING items additionally need a learner state:
- knowledge_items: 4-6 items (K1, K2, ...) with status understood / partly_understood / not_understood, describing what this learner already knows and what they do not yet understand about the topic of the opening.
- misconception: the learner's specific wrong belief behind the question (English).
- transfer_question: a small new question, in the language of the opening, that the learner could answer only with real understanding (no answer given here).
- subject_knowledge: 3-5 correct statements an evaluator needs to judge explanations (English).
- transfer_check: the same question, its correct answer, and what to check in the learner's attempt (understanding, not a repeated sentence).
- grading_rule: one sentence on what counts as a correct explanation (accept any sound method or wording).
"""
GROUP_TEXT = {"correction": "", "troubleshooting": TROUBLE, "learning": LEARN}
BATCH = {"correction": 5, "troubleshooting": 3, "learning": 5}
INTERACTION = {"correction": "revision", "troubleshooting": "uncertainty", "learning": "followup"}
CATEGORY = {"correction": "existing_type", "troubleshooting": "troubleshooting", "learning": "learning"}
# user traits are frozen in code with fixed shares, not left to the writer
PATIENCE = {"low": 20, "medium": 60, "high": 20}
HELPING = {"restate_only": 30, "can_point_defect": 40, "can_give_example": 30}
HELPING_NOTE = {"restate_only": "Can say whether something worked and repeat what they need, but cannot diagnose problems or write examples.",
                "can_point_defect": "Can point to the precise part that is wrong or missing, but will not write the answer themselves.",
                "can_give_example": "Can point to defects and give a short example or phrase of what they mean."}


def openings() -> dict[str, dict]:
    out = {}
    for f in sorted((HERE / "runs").glob("C60-*/prompts.jsonl")):
        for line in open(f):
            r = json.loads(line)
            if r["status"] == "active":
                out[r["slot_id"]] = r                      # a later retry run replaces a slot that was held earlier
    return out


def item_payload(r: dict) -> dict:
    inst = r["instance"] or {}
    return {"case_id": r["slot_id"], "language": r["language"], "opening": r["messages"][0]["content"], "person": r["person"],
            "story": r.get("story"), "situation": r["situation"],
            "instance": {k: inst.get(k) for k in ("task_summary", "givens", "constraints", "deliverable", "answer_conditions", "packet")}}


def to_world(w: dict) -> dict:
    conv = lambda v: True if v == "true" else False if v == "false" else v
    kv = lambda arr: {x["flag"]: conv(x["value"]) for x in arr}
    clean = lambda s: s.replace("{", "(").replace("}", ")")
    return {"derive": "declarative_v1", "root_cause": w["root_cause"], "hidden_facts": w["hidden_facts"],
            "initial_state": {f["flag"]: conv(f["initial"]) for f in w["state_flags"]},
            "state_domains": {f["flag"]: [conv(v) for v in f["domain"]] for f in w["state_flags"]},
            "derived_rules": [{"name": r["name"], "any_of": [kv(c) for c in r["any_of"]]} for r in w["derived_rules"]],
            "checks": {c["check_id"]: {"description": c["description"], "preconditions": c["preconditions"], "effects": kv(c["effects"]),
                                       "conditional_effects": [{"when": kv(x["when"]), "set": kv(x["set"])} for x in c["conditional_effects"]],
                                       "observations": [{"when": kv(o["when"]), "text": clean(o["text"])} for o in c["observations"]]}
                       for c in w["checks"]}}


def build_seed(r: dict, item: dict, traits: dict, call_id: str, glossary: Glossary) -> dict:
    group = GROUP_OF[r["slot_id"][3]]
    us = dict(item["user_state"], patience=traits["patience"], helping_ability=traits["helping_ability"],
              helping_ability_note=HELPING_NOTE[traits["helping_ability"]])
    seed = {"case_id": r["slot_id"], "run": "c60", "group": group, "category": CATEGORY[group], "language": r["language"],
            "primary_purpose": "dialogue", "subtype": r["subtype"],
            "labels": {"task": r["purpose"], "interaction": INTERACTION[group], "attitude": r["attitude"], "register": r["register"],
                       "difficulty": r["difficulty"], "detail": r["detail"]},
            "source_family": f"c60:{r['slot_id']}", "opening_instance_key": r.get("instance_key"),
            "opening_generator": {"version": r.get("generator_version"), "run": r.get("run"), "code_sha16": r.get("code_sha16"),
                                  "glossary_sha16": r.get("glossary_sha16")},
            "split": "development", "max_assistant_turns": MAX_ASSISTANT_TURNS, "opening": r["messages"][0]["content"],
            "opening_story_private": r.get("story"), "user_state": us, "user_view_extras": {},
            "evaluator_reference": item["evaluator_reference"], "maths_content": bool(item["evaluator_reference"].get("maths_content")),
            "seed_writer": {"version": VERSION, "call_id": call_id, "glossary_sha16": glossary.sha16}, **DEV_TAGS}
    if group == "troubleshooting":
        seed["world"] = to_world(item["world"])
        seed["evaluator_reference"] = {**seed["evaluator_reference"], "root_cause": item["world"]["root_cause"],
                                       "hidden_facts": item["world"]["hidden_facts"], "valid_resolutions": item["world"]["valid_resolutions"]}
    if group == "learning":
        learner = item["learner"]
        seed["learner"] = {"knowledge_items": learner["knowledge_items"], "misconception": {"text": learner["misconception"], "status": "held"},
                           "transfer_question": learner["transfer_question"],
                           "transfer_note": "Attempt this only with what you currently understand. You do not know the answer in advance."}
        seed["user_state"]["misconception"] = learner["misconception"]
        seed["evaluator_reference"] = {**seed["evaluator_reference"], "subject_knowledge": learner["subject_knowledge"],
                                       "transfer_check": learner["transfer_check"], "grading_rule": learner["grading_rule"]}
    return seed


def problems_for(seed: dict) -> list[str]:
    out = []
    try:
        validate_seed(seed)
    except Exception as exc:  # noqa: BLE001
        out.append(f"seed: {exc}")
    if seed.get("world"):
        try:
            out += [f"world: {p}" for p in worlds.validate_world(seed["world"])[:5]]
        except Exception as exc:  # noqa: BLE001
            out.append(f"world: {exc}")
        known = " ".join(seed["user_state"]["known_facts"]).lower()
        if seed["world"]["root_cause"].lower()[:40] in known:
            out.append("user known_facts reveal the root cause")
    return out


def frozen_traits(slot_ids: list[str]) -> dict[str, dict]:
    rng = random.Random(20260917)

    def shares(n: int, d: dict) -> list[str]:
        vals = [k for k, v in d.items() for _ in range(round(n * v / 100))]
        while len(vals) < n:
            vals.append(list(d)[1])
        rng.shuffle(vals)
        return vals[:n]
    pat, helping = shares(len(slot_ids), PATIENCE), shares(len(slot_ids), HELPING)
    return {sid: {"patience": p, "helping_ability": h} for sid, p, h in zip(slot_ids, pat, helping)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--traits-only", action="store_true")
    a = ap.parse_args()
    man = read_json(HERE / "manifest.json")
    ops = openings()
    missing = [s["slot_id"] for s in man["slots"] if s["slot_id"] not in ops]
    print(f"{len(ops)} openings; missing {len(missing)}: {missing}", flush=True)
    slot_ids = [s["slot_id"] for s in man["slots"]]                 # traits frozen over all 60 slots, stable across retries
    traits = frozen_traits(slot_ids)
    if a.traits_only:
        print(collections.Counter(t["helping_ability"] for t in traits.values()), collections.Counter(t["patience"] for t in traits.values()))
        return
    glossary = Glossary.load()
    from clients import CodexSolClient
    sol = CodexSolClient(); sol.start()
    ledger = CallLedger(RUNTIME, "c60")
    previous = {s["case_id"]: s for s in (read_json(HERE / "seeds.json")["seeds"] if (HERE / "seeds.json").exists() else [])}
    seeds = {sid: s for sid, s in previous.items() if sid in ops and s.get("opening") == ops[sid]["messages"][0]["content"]}
    failures: dict[str, list[str]] = {}
    try:
        for group in ("correction", "troubleshooting", "learning"):
            ids = [sid for sid in slot_ids if sid in ops and sid not in seeds and GROUP_OF[sid[3]] == group]
            for i in range(0, len(ids), BATCH[group]):
                batch = ids[i:i + BATCH[group]]
                prompt = (COMMON + "\n" + GROUP_TEXT[group] + "\nITEMS (JSON):\n"
                          + json.dumps([item_payload(ops[s]) for s in batch], ensure_ascii=False, indent=1))
                bad: dict[str, list[str]] = {}
                for attempt in (0, 1):
                    call_id = f"sol:c60_seeds:{group}:{'-'.join(batch)}:{sha256_json(prompt)[:10]}"
                    cached = ledger.reserve(call_id, "sol", "seed_writer", {"prompt_sha256": sha256_json(prompt), "effort": "medium", "version": VERSION})
                    if cached is None:
                        try:
                            result = sol.call(prompt, schema(group), model="gpt-5.6-sol", effort="medium", timeout=900)
                        except Exception as exc:  # noqa: BLE001
                            ledger.finish(call_id, error=str(exc)[:1000])
                            bad = {s: [f"call failed: {str(exc)[:200]}"] for s in batch}
                            break
                        ledger.finish(call_id, result=result)
                    else:
                        result = cached
                    by = {x["case_id"]: x for x in result["items"]}
                    bad = {}
                    for sid in batch:
                        if sid not in by:
                            bad[sid] = ["missing from output"]
                            continue
                        seed = build_seed(ops[sid], by[sid], traits[sid], call_id, glossary)
                        p = problems_for(seed)
                        if p:
                            bad[sid] = p
                        else:
                            seeds[sid] = seed
                    if not bad:
                        break
                    batch = [s for s in batch if s in bad]             # one repair call, only for the items that failed
                    prompt = (COMMON + "\n" + GROUP_TEXT[group] + "\nITEMS (JSON):\n"
                              + json.dumps([item_payload(ops[s]) for s in batch], ensure_ascii=False, indent=1)
                              + "\n\nA PREVIOUS ATTEMPT FAILED THESE CHECKS; return every item again, fixing them:\n"
                              + json.dumps(bad, ensure_ascii=False, indent=1))
                for sid, p in bad.items():
                    if sid not in seeds:
                        failures[sid] = p
                print(group, i, "seeds", len(seeds), "failed", len(failures), flush=True)
    finally:
        sol.close()
    atomic_json(HERE / "seeds.json", {"seed_set": "dialogue_collection60_v1", "version": VERSION, "created_utc": utcnow(),
                                      "traits": traits, "seeds": [seeds[s] for s in slot_ids if s in seeds],
                                      "failed": failures, "missing_openings": missing})
    print("SEEDS_DONE", json.dumps({"seeds": len(seeds), "failed": failures, "missing_openings": missing,
                                    "by_group": dict(collections.Counter(s["group"] for s in seeds.values()))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
