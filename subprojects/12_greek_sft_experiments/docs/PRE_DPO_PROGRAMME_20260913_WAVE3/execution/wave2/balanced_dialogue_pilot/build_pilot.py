#!/usr/bin/env python3
"""Build the 48-decision dialogue authoring pilot without launching calls."""
from __future__ import annotations

import hashlib
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLAN_ROOT = HERE.parents[2]
SPECS = HERE.parent / "correcting_dialogue_specs" / "revision2" / "pilot48_input_specs.jsonl"
SPLIT_MANIFEST = HERE.parent / "correcting_dialogue_specs" / "revision2" / "family_split_manifest.json"
PROMPT_DIR = PLAN_ROOT / "prompts"
SHARED_RUNNER = HERE.parent / "maths_generation_pilot" / "run_queue.py"
MODEL = "gpt-5.6-sol"
EFFORT = "high"
RUNNER_SHA = "c13862fd38c50facc721d385c9fcc3ea99a052719a52bf730d40490aa6b85005"
FROZEN_AT = "2026-09-13T16:29:00+03:00"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_jsonl(path: Path, values) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for value in values:
            handle.write(json.dumps(value, ensure_ascii=False) + "\n")


assert sha(SHARED_RUNNER) == RUNNER_SHA, "shared runner is not at its final-frozen hash"
HERE.mkdir(parents=True, exist_ok=True)
shutil.copyfile(SHARED_RUNNER, HERE / "run_queue.py")
assert sha(HERE / "run_queue.py") == RUNNER_SHA

specs = [json.loads(line) for line in SPECS.read_text().splitlines() if line.strip()]
split_manifest = json.loads(SPLIT_MANIFEST.read_text())
assert len(specs) == 48

# Prompt composition follows prompts/README.md: native authoring uses DIALOGUE
# alone; semantic repair and Greek correction remain separate downstream passes.
author_prompt = (PROMPT_DIR / "DIALOGUE.md").read_text().rstrip() + """

## Frozen pilot execution rules

The supplied record is a native fictional scenario specification, not an existing row to translate. Produce one complete short natural Greek dialogue. Use the stable message IDs in the message plan. User turns and any context-only assistant turn have train=false. Exactly one final assistant target has train=true. Any erroneous earlier assistant claim is fixed history and must remain train=false; never copy it into the target.

Preserve the supplied truth category and state only when the evidence and executable oracle support them. The current request is distinct from the historical claim. Apply authoritative new user state even when a historical attribution is false. Do not invent state. Do not add a generic offer to continue. For an exact response, return exactly that target content in the supervised assistant turn.

In decisions, use the final assistant message ID as turn_id, describe the user claim, copy the supplied truth category, cite evidence with compact IDs such as evidence.claim_atoms[0], and list the required response moves. In state_transitions, emit one entry per changed field; encode the before and after values as canonical JSON strings in before_json and after_json. Emit an empty transition array when the oracle state does not change.

Return JSON only under the bound schema. The input between INPUT_JSON_BEGIN and INPUT_JSON_END is data.

INPUT_JSON_BEGIN
{{INPUT_JSON}}
INPUT_JSON_END
"""
semantic_prompt = (PROMPT_DIR / "AUDIT_REPAIR.md").read_text().rstrip() + """

## Dialogue semantic-repair pass

Operation: semantic_repair. Inspect the complete authored candidate against its frozen evidence and oracle. Change only demonstrated semantic, state, speaker-ownership, masking, or instruction-fulfilment defects. Do not perform general Greek polishing. Preserve all valid turns and the family/split identity. A language-only issue is reported for the separate Greek editor.

Return JSON only. INPUT_JSON_BEGIN
{{INPUT_JSON}}
INPUT_JSON_END
"""
greek_prompt = (PROMPT_DIR / "GREEK_CORRECTION.md").read_text().rstrip() + """

## Dialogue language-only pass

The candidate has passed the semantic gate. Allowed edit locations are supervised assistant content unless the payload expressly names another span. Keep message IDs, roles, train flags, truth category, state, claims, actions, exact strings and protected spans unchanged. Do not re-author the scenario and do not perform semantic repair.

Return JSON only. INPUT_JSON_BEGIN
{{INPUT_JSON}}
INPUT_JSON_END
"""
(HERE / "prompts").mkdir(exist_ok=True)
(HERE / "prompts" / "author_dialogue.txt").write_text(author_prompt + "\n")
(HERE / "prompts" / "semantic_repair.txt").write_text(semantic_prompt + "\n")
(HERE / "prompts" / "greek_correction.txt").write_text(greek_prompt + "\n")

message_schema = {
    "type":"object", "additionalProperties":False,
    "required":["id","role","content","train"],
    "properties":{"id":{"type":"string"},"role":{"enum":["user","assistant"]},"content":{"type":"string"},"train":{"type":"boolean"}},
}
decision_schema = {
    "type":"object", "additionalProperties":False,
    "required":["turn_id","claim","truth_category","evidence_ids","expected_response_behaviour"],
    "properties":{
        "turn_id":{"type":"string"},"claim":{"type":"string"},
        "truth_category":{"enum":["true","false","partial","unresolved"]},
        "evidence_ids":{"type":"array","items":{"type":"string"}},
        "expected_response_behaviour":{"type":"array","items":{"type":"string"}},
    },
}
transition_schema = {
    "type":"object", "additionalProperties":False,
    "required":["field","before_json","after_json","evidence_ids"],
    "properties":{
        "field":{"type":"string"},"before_json":{"type":"string"},"after_json":{"type":"string"},
        "evidence_ids":{"type":"array","items":{"type":"string"}},
    },
}
author_schema = {
    "$schema":"https://json-schema.org/draft/2020-12/schema", "type":"object", "additionalProperties":False,
    "required":["row_id","status","messages","adaptation_record","decisions","state_transitions","checks_needed","issues"],
    "properties":{
        "row_id":{"type":"string"}, "status":{"enum":["candidate","blocked"]},
        "messages":{"type":"array","items":message_schema},
        "adaptation_record":{"type":"null"},
        "decisions":{"type":"array","items":decision_schema},
        "state_transitions":{"type":"array","items":transition_schema},
        "checks_needed":{"type":"array","items":{"type":"string"}},
        "issues":{"type":"array","items":{"type":"string"}},
    },
}
semantic_schema = {
    "$schema":"https://json-schema.org/draft/2020-12/schema", "type":"object", "additionalProperties":False,
    "required":["row_id","disposition","findings","candidate_messages","changes","checks_executed","checks_needed","unresolved"],
    "properties":{
        "row_id":{"type":"string"},"disposition":{"enum":["no_defect_found","repair_proposed","needs_evidence","out_of_scope"]},
        "findings":{"type":"array","items":{"type":"object","additionalProperties":False,
            "required":["domain","exact_span","severity","evidence","proposed_action"],
            "properties":{"domain":{"type":"string"},"exact_span":{"type":["string","null"]},"severity":{"enum":["minor","major","blocking"]},"evidence":{"type":"array","items":{"type":"string"}},"proposed_action":{"type":"string"}}}},
        "candidate_messages":{"type":["array","null"],"items":message_schema},
        "changes":{"type":"array","items":{"type":"object","additionalProperties":False,
            "required":["message_id","before","after","reason"],
            "properties":{"message_id":{"type":"string"},"before":{"type":"string"},"after":{"type":"string"},"reason":{"type":"string"}}}},
        "checks_executed":{"type":"array","items":{"type":"string"}},
        "checks_needed":{"type":"array","items":{"type":"string"}},
        "unresolved":{"type":"array","items":{"type":"string"}},
    },
}
greek_schema = {
    "$schema":"https://json-schema.org/draft/2020-12/schema", "type":"object", "additionalProperties":False,
    "required":["row_id","status","messages","changes","semantic_flags"],
    "properties":{
        "row_id":{"type":"string"},"status":{"enum":["unchanged","edited","needs_semantic_review"]},
        "messages":{"type":"array","items":message_schema},
        "changes":{"type":"array","items":{"type":"object","additionalProperties":False,
            "required":["message_id","before","after","error","reason"],
            "properties":{"message_id":{"type":"string"},"before":{"type":"string"},"after":{"type":"string"},"error":{"type":"string"},"reason":{"type":"string"}}}},
        "semantic_flags":{"type":"array","items":{"type":"string"}},
    },
}
write_json(HERE / "schemas" / "author_dialogue.schema.json", author_schema)
write_json(HERE / "schemas" / "semantic_repair.schema.json", semantic_schema)
write_json(HERE / "schemas" / "greek_correction.schema.json", greek_schema)

inputs = []
quarantine = []
for spec in specs:
    row_id = spec["spec_id"]
    is_quarantine = spec["expected"]["generation_status"] == "blocked"
    record = {
        "row_id": row_id,
        "family_id": spec["family_id"],
        "split": spec["split"],
        "operation": "author",
        "domain": "correcting_dialogue",
        "target_language": "el",
        "teaching_objective": "Respond to a user correction according to evidence while preserving valid current instructions and dialogue state.",
        "message_plan": {
            "optional_context_user_id": row_id + ".u_context",
            "optional_context_assistant_id": row_id + ".a_context",
            "context_assistant_train": False,
            "decision_user_id": row_id + ".u_decision",
            "decision_user_train": False,
            "target_assistant_id": row_id + ".a_target",
            "target_assistant_train": True,
            "exactly_one_supervised_assistant_turn": True,
        },
        "protected": {
            "family_id": spec["family_id"], "split": spec["split"],
            "truth_category": spec["truth_category"], "oracle": spec["oracle"],
            "exact_response": spec["expected"]["exact_response"],
        },
        "scenario_spec": spec,
        "quarantine": is_quarantine,
        "quarantine_reason": "silence_requested_but_training_representation_unspecified" if is_quarantine else None,
    }
    inputs.append(record)
    if is_quarantine:
        quarantine.append(record)

by_split = {split:[r for r in inputs if r["split"] == split] for split in ("train","dev","final_confirmation")}
write_jsonl(HERE / "inputs" / "train.jsonl", by_split["train"])
write_jsonl(HERE / "inputs" / "dev.jsonl", by_split["dev"])
write_jsonl(HERE / "sealed" / "final_confirmation" / "inputs.jsonl", by_split["final_confirmation"])
write_jsonl(HERE / "quarantine" / "silence_unspecified.jsonl", quarantine)

def author_job(record):
    return {
        "job_id":"author_" + record["row_id"], "stage":"dialogue_authoring", "row_id":record["row_id"],
        "model":MODEL, "effort":EFFORT, "schema":"schemas/author_dialogue.schema.json",
        "template":"prompts/author_dialogue.txt", "depends_on":[],
        "payload":{
            "row_id":{"$record":"row_id"},"family_id":{"$record":"family_id"},"split":{"$record":"split"},
            "message_plan":{"$record":"message_plan"},"protected":{"$record":"protected"},
            "scenario_spec":{"$record":"scenario_spec"},
        },
    }

queues = {split:[author_job(r) for r in records if not r["quarantine"]] for split,records in by_split.items()}
write_jsonl(HERE / "queues" / "train.jsonl", queues["train"])
write_jsonl(HERE / "queues" / "dev.jsonl", queues["dev"])
write_jsonl(HERE / "sealed" / "final_confirmation" / "queue.jsonl", queues["final_confirmation"])

probe_ids = ["pilot48_01_true", "pilot48_06_false", "pilot48_10_partial", "pilot48_03_unresolved"]
probe_jobs = [next(job for job in queues["train"] if job["row_id"] == rid) for rid in probe_ids]
write_jsonl(HERE / "queues" / "probe_train4.jsonl", probe_jobs)
records_by_id = {r["row_id"]:r for r in inputs}
binding_receipts = {}
for split,jobs in queues.items():
    receipts=[]
    for job in jobs:
        record=records_by_id[job["row_id"]]
        payload={"row_id":record["row_id"],"family_id":record["family_id"],"split":record["split"],"message_plan":record["message_plan"],"protected":record["protected"],"scenario_spec":record["scenario_spec"]}
        prompt=(HERE/"prompts"/"author_dialogue.txt").read_text().replace("{{INPUT_JSON}}",json.dumps(payload,ensure_ascii=False,indent=2))
        receipts.append({"job_id":job["job_id"],"row_id":job["row_id"],"split":split,"input_record_sha256":canonical_sha(record),"payload_sha256":canonical_sha(payload),"job_spec_sha256":canonical_sha(job),"assembled_prompt_sha256":hashlib.sha256(prompt.encode()).hexdigest(),"model":MODEL,"effort":EFFORT})
    binding_receipts[split]=receipts
write_jsonl(HERE/"receipts"/"train_payload_bindings.jsonl",binding_receipts["train"])
write_jsonl(HERE/"receipts"/"dev_payload_bindings.jsonl",binding_receipts["dev"])
write_jsonl(HERE/"sealed"/"final_confirmation"/"payload_bindings.jsonl",binding_receipts["final_confirmation"])
probe_payloads=[]
for job in probe_jobs:
    record=records_by_id[job["row_id"]]
    payload={"row_id":record["row_id"],"family_id":record["family_id"],"split":record["split"],"message_plan":record["message_plan"],"protected":record["protected"],"scenario_spec":record["scenario_spec"]}
    probe_payloads.append({"job":job,"outbound_payload":payload,"assembled_prompt":(HERE/"prompts"/"author_dialogue.txt").read_text().replace("{{INPUT_JSON}}",json.dumps(payload,ensure_ascii=False,indent=2))})
write_jsonl(HERE/"probe_payloads.jsonl",probe_payloads)

conditional = {
    "materialization_status":"templates_only_not_queued",
    "semantic_repair":{
        "cap":12,"split_caps":{"train":8,"dev":2,"final_confirmation":2},"trigger":"named substantive defect after oracle/full-dialogue review",
        "model":MODEL,"effort":EFFORT,"schema":"schemas/semantic_repair.schema.json","template":"prompts/semantic_repair.txt",
        "payload_fields":["scenario_spec","authored_candidate","oracle_verification","allowed_edit_locations","protected_spans"],
    },
    "greek_correction":{
        "cap":47,"split_caps":{"train":32,"dev":8,"final_confirmation":7},"trigger":"semantic acceptance; one language pass for each dispatchable candidate",
        "model":MODEL,"effort":EFFORT,"schema":"schemas/greek_correction.schema.json","template":"prompts/greek_correction.txt",
        "payload_fields":["scenario_spec","semantically_settled_candidate","allowed_edit_locations","protected_spans"],
    },
    "ordering":["author","oracle_and_full_semantic_gate","semantic_repair_if_needed","semantic_regate","greek_correction","oracle_and_semantic_regate"],
    "forbidden_shortcuts":["Greek correction cannot change truth, state, action, quantities, ownership, masks, or protected exact strings","Semantic repair cannot be folded into a language-only edit","A model assertion is not oracle evidence"],
}
write_json(HERE / "conditional_jobs.json", conditional)

call_envelope = {
    "primary_authoring_calls":47,
    "quarantined_without_call":1,
    "probe_calls":4,
    "probe_is_subset_of_primary":True,
    "retry_calls_cap":12,
    "retry_split_caps":{"train":4,"dev":4,"final_confirmation":4},
    "semantic_repair_calls_cap":12,
    "greek_correction_calls_cap":47,
    "absolute_call_cap":118,
    "max_attempts_per_primary_job":2,
    "max_workers":8,
    "split_runtime_caps":{"train":76,"dev":22,"final_confirmation":20},
    "token_planning_estimate":{
        "primary":{"calls":47,"input_tokens_per_call":2500,"output_tokens_per_call":1000},
        "retry":{"calls":12,"input_tokens_per_call":2500,"output_tokens_per_call":1000},
        "semantic_repair":{"calls":12,"input_tokens_per_call":4000,"output_tokens_per_call":1500},
        "greek_correction":{"calls":47,"input_tokens_per_call":3500,"output_tokens_per_call":1200},
        "estimated_total_input_tokens":360000,
        "estimated_total_output_tokens":133400,
        "estimated_total_tokens":493400,
        "pricing_formula":"USD = 0.36 * current_input_USD_per_million + 0.1334 * current_output_USD_per_million",
        "note":"Token counts are planning estimates, not measured usage. No dollar figure is asserted without the applicable contracted runtime rates.",
    },
}
write_json(HERE / "call_and_cost_envelope.json", call_envelope)

execution_plan = {
    "status":"prepared_not_launched",
    "runner":"run_queue.py",
    "shared_runner_sha256":RUNNER_SHA,
    "probe":{
        "order":1,"split":"train","queue":"queues/probe_train4.jsonl","inputs":"inputs/train.jsonl",
        "state_dir":"run_state/train","max_workers":4,"limit_new_calls":4,"call_cap":76,
        "gate":"Review all four complete outputs for oracle agreement, state, ownership, mask, naturalness, and new damage before any further call.",
    },
    "train_remainder":{
        "order":2,"queue":"queues/train.jsonl","inputs":"inputs/train.jsonl","state_dir":"run_state/train","max_workers":8,"call_cap":76,
        "gate":"Proceed only after the four-call probe passes; accepted probe outputs are reused by bound job IDs.",
    },
    "development":{
        "order":3,"queue":"queues/dev.jsonl","inputs":"inputs/dev.jsonl","state_dir":"run_state/dev","max_workers":8,"call_cap":22,
        "gate":"Use only for the declared development checks after the authoring prompt is frozen.",
    },
    "final_confirmation":{
        "order":4,"queue":"sealed/final_confirmation/queue.jsonl","inputs":"sealed/final_confirmation/inputs.jsonl","state_dir":"run_state/final_confirmation","max_workers":8,"call_cap":20,
        "gate":"Run only after authoring, semantic, Greek, oracle, and assembly rules are frozen. Do not use content to tune or select; expose aggregate gate summaries to root.",
    },
    "execution_acknowledgement":"PREPARED_PAYLOAD_REVIEWED",
    "authorization_note":"The active goal authorizes later execution after these gates; no additional blanket authorization is required. This preparation task itself does not launch calls.",
}
write_json(HERE / "execution_plan.json", execution_plan)
write_json(HERE / "output_layout.json", {
    "train":{"runner_state":"run_state/train","reviewed_candidates":"outputs/train"},
    "dev":{"runner_state":"run_state/dev","reviewed_candidates":"outputs/dev"},
    "final_confirmation":{"runner_state":"run_state/final_confirmation","reviewed_candidates":"sealed/final_confirmation/outputs","root_facing":"sealed/final_confirmation/gate_summary.json"},
    "stage_subdirectories":["authored","semantic_repaired","greek_corrected","accepted","held"],
    "family_rule":"No family may appear in more than one split; final-confirmation content may not be copied into train/dev review artifacts.",
})

final_summary = {
    "split":"final_confirmation","families":len({r["family_id"] for r in by_split["final_confirmation"]}),
    "specifications":len(by_split["final_confirmation"]),"dispatchable":len(queues["final_confirmation"]),
    "quarantined":sum(r["quarantine"] for r in by_split["final_confirmation"]),
    "truth_counts":dict(Counter(r["scenario_spec"]["truth_category"] for r in by_split["final_confirmation"])),
    "content_visibility":"sealed_from_tuning_and_selection; root-facing reporting is aggregate gate status only",
    "input_sha256":sha(HERE / "sealed" / "final_confirmation" / "inputs.jsonl"),
    "queue_sha256":sha(HERE / "sealed" / "final_confirmation" / "queue.jsonl"),
}
write_json(HERE / "sealed" / "final_confirmation" / "gate_summary.json", final_summary)
partition_receipt = {
    "status":"PASS","family_leakage":False,
    "train":{"families":sorted({r["family_id"] for r in by_split["train"]}),"specifications":32},
    "dev":{"families":sorted({r["family_id"] for r in by_split["dev"]}),"specifications":8},
    "final_confirmation":{"family_count":len({r["family_id"] for r in by_split["final_confirmation"]}),"specifications":8,"family_set_sha256":hashlib.sha256("\n".join(sorted({r["family_id"] for r in by_split["final_confirmation"]})).encode()).hexdigest(),"content_disclosed":False},
}
write_json(HERE / "receipts" / "family_partition.json", partition_receipt)

artifact_paths = [
    "run_queue.py", "inputs/train.jsonl", "inputs/dev.jsonl", "queues/train.jsonl", "queues/dev.jsonl", "queues/probe_train4.jsonl",
    "sealed/final_confirmation/inputs.jsonl", "sealed/final_confirmation/queue.jsonl", "sealed/final_confirmation/gate_summary.json",
    "quarantine/silence_unspecified.jsonl", "conditional_jobs.json", "call_and_cost_envelope.json",
    "execution_plan.json", "output_layout.json",
    "probe_payloads.jsonl", "receipts/family_partition.json", "receipts/train_payload_bindings.jsonl", "receipts/dev_payload_bindings.jsonl", "sealed/final_confirmation/payload_bindings.jsonl",
    "schemas/author_dialogue.schema.json", "schemas/semantic_repair.schema.json", "schemas/greek_correction.schema.json",
    "prompts/author_dialogue.txt", "prompts/semantic_repair.txt", "prompts/greek_correction.txt",
    "build_pilot.py", "verify_prelaunch.py", "verify_outputs.py", "report.md",
]
manifest = {
    "version":1,"status":"prepared_not_launched","frozen_at":FROZEN_AT,
    "source_specs":{"path":str(SPECS),"sha256":sha(SPECS),"rows":48},
    "source_split_manifest":{"path":str(SPLIT_MANIFEST),"sha256":sha(SPLIT_MANIFEST)},
    "prompt_pack":{"DIALOGUE.md":sha(PROMPT_DIR/"DIALOGUE.md"),"AUDIT_REPAIR.md":sha(PROMPT_DIR/"AUDIT_REPAIR.md"),"GREEK_CORRECTION.md":sha(PROMPT_DIR/"GREEK_CORRECTION.md"),"README.md":sha(PROMPT_DIR/"README.md")},
    "runner":{"reuse":"byte-identical copy of final-frozen generic maths runner; no new runner implementation","source":str(SHARED_RUNNER),"sha256":RUNNER_SHA},
    "counts":{
        "specifications":48,"dispatchable_primary":47,"quarantined":1,"train":32,"dev":8,"final_confirmation":8,
        "primary_calls":47,"retry_cap":4,"retry_call_cap":12,"semantic_repair_call_cap":12,"greek_correction_call_cap":47,"absolute_call_cap":118,
    },
    "probe":{"calls":4,"split":"train","row_ids":probe_ids,"queue":"queues/probe_train4.jsonl","max_workers":4},
    "execution":{"launched":False,"default_runner_mode":"plan","workers_after_probe_max":8,"final_confirmation_policy":"run only after prompts and gates freeze; do not use content for tuning or selection"},
    "artifact_sha256":{rel:sha(HERE/rel) for rel in artifact_paths},
}
write_json(HERE / "manifest.json", manifest)
write_json(HERE / "receipts" / "preparation.json", {
    "status":"PASS_PREPARED_NOT_LAUNCHED","prepared_at":FROZEN_AT,
    "manifest_sha256":sha(HERE/"manifest.json"),"specifications":48,"dispatchable":47,"quarantined":1,
    "probe_jobs":4,"max_workers_after_probe":8,"absolute_call_cap":118,
    "runner_sha256":RUNNER_SHA,"model_subprocess_calls":0,"production_writes":0,
})
print(json.dumps(manifest["counts"], ensure_ascii=False, indent=2))
