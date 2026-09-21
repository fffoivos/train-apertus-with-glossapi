"""D1 openings (generator 0.3-dev, person-and-story seeds): one Sol call writes the four fresh openings plus the
private user state and the evaluator reference; the result is validated and frozen into seeds/dvi_seeds.json."""
from __future__ import annotations

import json
from typing import Any

from clients import SolClient
from common import V2_RUNTIME, atomic_json, read_json, sha256_text, utcnow
from contracts import DEV_TAGS, MAX_ASSISTANT_TURNS, OPENING_SCHEMA, OPENING_WRITER_VERSION, prompt_text
from glossary import Glossary
from ledger import CallLedger
from seeds import DVI_SEEDS, DVI_SPECS, D1_IDS, validate_seed


def opening_prompt(glossary: Glossary, specs: list[dict[str, Any]]) -> str:
    parts = [prompt_text("opening_writer_v1.txt")]
    for spec in specs:
        labels = dict(spec["labels"])
        block = glossary.block({"task": labels["task"], "interaction": labels["interaction"],
                                "attitude": labels["attitude"], "register": labels["register"],
                                "difficulty": labels["difficulty"], "detail": labels["detail"]})
        public = {k: spec[k] for k in ("case_id", "language", "person", "situation", "task", "topic", "specific",
                                       "labels", "fixed_user_traits", "writer_constraints")}
        parts.append(f"=== SEED {spec['case_id']} ===\n{block}\n\nSEED (JSON):\n{json.dumps(public, ensure_ascii=False, indent=1)}")
    return "\n\n".join(parts)


def write_openings(sol: SolClient, glossary: Glossary) -> dict[str, Any]:
    specs = read_json(DVI_SPECS)["seeds"]
    prompt = opening_prompt(glossary, specs)
    ledger = CallLedger(V2_RUNTIME, "dvi")
    call_id = f"sol:openings:dvi:{sha256_text(prompt)[:16]}"
    cached = ledger.reserve(call_id, "sol", "openings", {"prompt_sha256": sha256_text(prompt), "glossary_sha16": glossary.sha16,
                                                          "opening_writer_version": OPENING_WRITER_VERSION, "effort": "medium"})
    if cached is None:
        try:
            result = sol.call(prompt, OPENING_SCHEMA, model="gpt-5.6-sol", effort="medium", timeout=900)
        except Exception as exc:  # noqa: BLE001
            ledger.finish(call_id, error=str(exc)[:1000], ambiguous=isinstance(exc, TimeoutError))
            raise
        ledger.finish(call_id, result=result)
        (V2_RUNTIME / "prompts_sent").mkdir(parents=True, exist_ok=True)
        (V2_RUNTIME / "prompts_sent" / (call_id.replace(":", "_") + ".txt")).write_text(prompt, encoding="utf-8")
    else:
        result = cached
    by_id = {item["case_id"]: item for item in result["items"]}
    if sorted(by_id) != D1_IDS:
        raise ValueError(f"opening ids {sorted(by_id)} != {D1_IDS}")
    seeds = []
    for spec in specs:
        item = by_id[spec["case_id"]]
        us = item["user_state"]
        traits = spec["fixed_user_traits"]
        us["patience"], us["helping_ability"] = traits["patience"], traits["helping_ability"]
        us["helping_ability_note"] = traits["helping_ability_note"]
        seed = {"case_id": spec["case_id"], "run": "D1", "category": "existing_type", "d1_kind": spec["d1_kind"],
                "language": spec["language"], "primary_purpose": "dialogue", "labels": spec["labels"],
                "source_family": f"dvi:{spec['case_id']}", "development_family": spec["development_family"],
                "related_pilot_trajectory": spec.get("related_pilot_trajectory"), "split": "development",
                "max_assistant_turns": MAX_ASSISTANT_TURNS, "opening": item["message"].strip(),
                "opening_story_private": item["story"], "user_state": us, "user_view_extras": {},
                "evaluator_reference": item["evaluator_reference"],
                "maths_content": bool(item["evaluator_reference"].get("maths_content")),
                "seed_spec": {k: spec[k] for k in ("person", "situation", "task", "topic", "specific")},
                "opening_writer": {"version": OPENING_WRITER_VERSION, "call_id": call_id, "glossary_sha16": glossary.sha16},
                **DEV_TAGS}
        validate_seed(seed)
        seeds.append(seed)
    atomic_json(DVI_SEEDS, {"seed_set": "dialogue_v2_improvements_d1_v1", "created_utc": utcnow(),
                            "held_out_evaluation_exclusion": "source families dvi:* are development-only and reserved from formal evaluation",
                            "seeds": seeds})
    return {"written": len(seeds), "call_id": call_id, "cached": cached is not None}
