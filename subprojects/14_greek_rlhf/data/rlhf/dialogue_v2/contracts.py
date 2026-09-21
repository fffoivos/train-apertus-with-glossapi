"""Versioned contracts, vocabularies (spec v0.5 §4.7, §4.8, §5.4) and Sol output schemas for dialogue v2."""
from __future__ import annotations

import pathlib
from typing import Any

from common import HERE, RUBRIC_PATH, sha16_file

PROTOCOL_VERSION = "dialogue-v2-dev-0.1"
GENERATOR_VERSION = "0.3-dev"
USER_POLICY_VERSION = "adaptive-user-v2.0"
WORLD_RESOLVER_VERSION = "world-resolver-v1"
OPENING_WRITER_VERSION = "dvi-opening-writer-v1"
TURN_EVAL_VERSION = "dv2-turn-eval-v1"
CONVERSATION_REVIEW_VERSION = "dv2-conversation-review-v1"
BRANCH_RULE_VERSION = "dv2-branch-4then8-v1"
BRANCH_VERIFY_VERSION = "dv2-branch-verify-v1"
SAMPLING_CONFIG_VERSION = "dv2-sampling-v1"
# 60-dialogue collection (DIALOGUE_COLLECTION_60_AMENDMENT_20260917.md)
C60_PROTOCOL_VERSION = "dialogue-c60-0.1"
C60_USER_POLICY_VERSION = "adaptive-user-v2.1"      # scheduled strategy change before reply 3, silent departure, no final assessment
C60_REVIEW_VERSION = "c60-combined-review-v1"       # one post-trajectory review per conversation
C60_BRANCH_RULE_VERSION = "c60-ab-4-v1"             # points A and B, four candidates each, optional top-up not automatic
C60_CANDIDATES = 4
INSTRUCTION_CHANGE_MOVES = {"give_example", "decompose", "simplify", "clarify", "add_context"}
C60_ENDINGS = ["natural_completion", "silent_departure", "abandonment", "turn_cap", "context_cutoff", "truncated_output",
               "infrastructure_failure", "ambiguous_timeout"]

MODEL_ID = "fffoivos/greek-apertus-8b-sft-r4-full"
MODEL_ALIAS = "G4F6P1"
MODEL_REVISION = "3a557e0842b146ccb6d24427e20b08c52fb368d5"
MODEL_SHA256 = "54d445bc639b7222ad872b4d8dca5e913dbf4c4d427fbf56183e28361006e763"
SERVED_CONTEXT = 4096

PILOT_SAMPLING = {"temperature": 0.8, "top_p": 0.95, "max_tokens": 1500, "n": 1}
# Recorded sampling-config change (brief §5.3): the per-reply cap is lowered from 1,500 to 1,024 so that six-turn
# conversations fit the 4,096-token served context. Pilot evidence: rollout completion p99 = 486 tokens, only a
# runaway exceeded 800 (126 rollout replies); 480 resampled replies max 483. Applied to every D1/D2 reply and branch.
SAMPLING = {"temperature": 0.8, "top_p": 0.95, "max_tokens": 1024, "n": 1}
NO_SYSTEM_PROMPT = True

MAX_ASSISTANT_TURNS = 6
CANDIDATES_FIRST = 4
CANDIDATES_MAX = 8
MAX_POINTS_PER_D1_CONVERSATION = 2

DEV_TAGS = {"purpose": "development_demo", "training_eligible": False, "experiment_credit": 0}

MOVES = ["restate", "point_to_defect", "give_example", "decompose", "add_context", "simplify",
         "express_frustration", "accept_partial", "abandon", "clarify", "continue", "finish"]
TERMINAL_MOVES = {"finish", "abandon"}
HELPFUL_MOVES = {"point_to_defect", "give_example", "decompose", "add_context", "simplify", "clarify"}
FAILURE_RESPONSE_MOVES = {"restate", "point_to_defect", "give_example", "decompose", "add_context", "simplify",
                          "express_frustration", "accept_partial", "abandon"}
ASSISTANCE_LEVELS = ["none", "restatement", "pointed_defect", "partial_scaffold_or_example", "supplied_solution"]
ENDING_REASONS = ["natural_completion", "abandonment", "horizon", "context_cutoff", "truncated_output",
                  "infrastructure_failure", "ambiguous_timeout"]
SAMPLING_POINT_KINDS = ["prevention", "supported_recovery", "healthy_continuation"]
SEVERITIES = ["good", "minor", "serious", "unjudgeable"]
PATIENCE_TOLERANCE = {"low": 1, "medium": 2, "high": 4}
HELPING_ABILITY = {
    # what the user can plausibly do when a reply fails (spec §4.8 "helping ability")
    "restate_only": {"restate", "express_frustration", "simplify", "accept_partial", "abandon", "clarify",
                     "add_context", "continue", "finish"},
    "can_point_defect": {"restate", "point_to_defect", "express_frustration", "simplify", "accept_partial", "abandon",
                         "clarify", "add_context", "continue", "finish"},
    "can_give_example": set(MOVES),
}

PROMPTS = HERE / "prompts"


def prompt_path(name: str) -> pathlib.Path:
    return PROMPTS / name


def prompt_text(name: str) -> str:
    return prompt_path(name).read_text(encoding="utf-8")


def component_versions() -> dict[str, Any]:
    out = {"protocol_version": PROTOCOL_VERSION, "generator_version": GENERATOR_VERSION,
           "user_policy_version": USER_POLICY_VERSION, "world_resolver_version": WORLD_RESOLVER_VERSION,
           "opening_writer_version": OPENING_WRITER_VERSION, "turn_eval_version": TURN_EVAL_VERSION,
           "conversation_review_version": CONVERSATION_REVIEW_VERSION, "branch_rule_version": BRANCH_RULE_VERSION,
           "branch_verify_version": BRANCH_VERIFY_VERSION, "sampling_config_version": SAMPLING_CONFIG_VERSION,
           "sampling": SAMPLING, "pilot_sampling_baseline": PILOT_SAMPLING, "no_system_prompt": NO_SYSTEM_PROMPT,
           "model": {"id": MODEL_ID, "alias": MODEL_ALIAS, "revision": MODEL_REVISION, "sha256": MODEL_SHA256,
                     "served_context": SERVED_CONTEXT},
           "rubric_v2_4_sha16": sha16_file(RUBRIC_PATH)}
    for name in sorted(p.name for p in PROMPTS.glob("*.txt")):
        out[f"prompt_sha16:{name}"] = sha16_file(PROMPTS / name)
    return out


# ---------------------------------------------------------------------------------------------------------------
# Sol output schemas (strict)
# ---------------------------------------------------------------------------------------------------------------
def _obj(props: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {"type": "object", "properties": props, "required": required or list(props), "additionalProperties": False}


S = {"type": "string"}
B = {"type": "boolean"}


def _enum(values) -> dict[str, Any]:
    return {"type": "string", "enum": list(values)}


USER_DECISION_SCHEMA = _obj({
    "perceived_latest_reply": _obj({"defect_present": B, "defect": S, "same_defect_as_before": B, "useful_progress": B}),
    "move": _enum(MOVES),
    "done": B,
    "message": S,
    "new_information": S,
    "trigger": S,
    "changes_task": B,
    "assistance_level": _enum(ASSISTANCE_LEVELS),
    "revealed_private_preference_ids": {"type": "array", "items": S},
    "task_progress": _enum(["not_started", "partial", "mostly_done", "done"]),
    "knowledge_updates": {"type": "array", "items": _obj({"item_id": S, "new_status": _enum(["understood", "partly_understood", "not_understood"]), "evidence_quote": S})},
    "misconception_status": _enum(["not_applicable", "held", "weakened", "revised"]),
    "transfer_attempt": _obj({"attempted": B, "attempt_text": S}),
    "private_note": S,
})

USER_ACTIONS_SCHEMA = _obj({
    "actions": {"type": "array", "items": _obj({"action": S, "from_assistant_suggestion": B, "why_plausible_for_this_user": S})},
    "skipped_suggestions": {"type": "array", "items": _obj({"suggestion": S, "reason": S})},
})

RESOLVER_SCHEMA = _obj({
    "resolutions": {"type": "array", "items": _obj({
        "action_index": {"type": "integer"}, "check_id": S, "status": _enum(["supported", "unresolved"]), "reason": S})},
})

OPENING_SCHEMA = _obj({
    "items": {"type": "array", "items": _obj({
        "case_id": S, "story": S, "message": S,
        "user_state": _obj({
            "goal": S, "known_facts": {"type": "array", "items": S}, "expertise": _enum(["novice", "intermediate", "expert"]),
            "misconception": S, "disclosed_preferences": {"type": "array", "items": S},
            "private_preferences": {"type": "array", "items": _obj({"id": S, "text": S, "reveal_when": S})},
            "patience": _enum(["low", "medium", "high"]),
            "helping_ability": _enum(list(HELPING_ABILITY)), "helping_ability_note": S}),
        "evaluator_reference": _obj({
            "checkable_constraints": {"type": "array", "items": S}, "supplied_facts": {"type": "array", "items": S},
            "what_a_good_first_reply_does": S, "maths_content": B}),
    })},
})

TURN_EVAL_SCHEMA = _obj({
    "evaluations": {"type": "array", "items": _obj({
        "packet_id": S,
        "local_quality": _enum(SEVERITIES),
        "decisive_evidence": S,
        "error_summary": S,
        "disclosed_constraints_checked": {"type": "array", "items": S},
        "undisclosed_preferences_not_counted": {"type": "array", "items": S},
        "used_latest_guidance": _enum(["yes", "partly", "no", "not_applicable"]),
        "retained_earlier_constraints": _enum(["yes", "partly", "no", "not_applicable"]),
        "repeats_earlier_failed_reply": B,
        "factual_or_subject_errors": {"type": "array", "items": S},
        "maths_content": B,
        "consistent_with_world_or_learner_state": _enum(["yes", "no", "not_applicable"]),
        "meaningful_next_task_exists": B,
        "needs_human_review": B,
        "confidence": _enum(["low", "medium", "high"]),
    })},
})

CONVERSATION_REVIEW_SCHEMA = _obj({
    "user_turns": {"type": "array", "items": _obj({
        "user_turn_index": {"type": "integer"},
        "reacts_to_visible_event": _enum(["yes", "no", "not_applicable"]),
        "reacts_to_real_defect": _enum(["yes", "no", "not_applicable"]),
        "oracle_leak": B, "oracle_leak_evidence": S,
        "move_label_correct": B, "corrected_move": S,
        "assistance_level_correct": B, "corrected_assistance_level": S,
        "genuinely_helpful": B,
        "consistent_with_user_state": B,
        "simulator_error": S})},
    "world_consistency": _obj({"applicable": B, "consistent": B, "issues": {"type": "array", "items": S}}),
    "learning": _obj({"applicable": B, "progress_supported_by_teaching": B, "transfer_attempted": B,
                      "transfer_attempt_sound": _enum(["yes", "partly", "no", "not_applicable"]),
                      "sudden_unsupported_expertise": B, "evidence": S}),
    "writing": _obj({"applicable": B, "hidden_preference_treated_as_earlier_instruction": B,
                     "reference_copied_into_conversation": B, "evidence": S}),
    "hidden_information_leaked_to_assistant": B, "leak_evidence": S,
    "target_errors": {"type": "array", "items": S},
    "simulator_errors": {"type": "array", "items": S},
    "ending_reason_agrees": B, "ending_comment": S,
    "task_result": _enum(["completed", "partially_completed", "not_completed", "unclear"]),
    "positive_replies_with_incorrect_claims": {"type": "array", "items": S},
    "possible_sampling_points": {"type": "array", "items": _obj({
        "kind": _enum(SAMPLING_POINT_KINDS), "before_assistant_turn": {"type": "integer"}, "reason": S})},
    "summary": S,
})

BRANCH_RANK_SCHEMA = _obj({
    "ranking": {"type": "array", "items": _enum("ABCD")},
    "ties": {"type": "array", "items": {"type": "array", "items": _enum("ABCD")}},
    "unusable": {"type": "array", "items": _enum("ABCD")},
    "verdicts": _obj({L: _enum(["reinforce", "neutral", "discourage"]) for L in "ABCD"}),
    "issues": _obj({L: {"type": "array", "items": S} for L in "ABCD"}),
    "notes": _obj({L: S for L in "ABCD"}),
    "best_vs_worst": _enum(["clear", "slight", "none"]),
    "confidence": _enum(["high", "medium", "low"]),
})

BRANCH_VERIFY_SCHEMA = _obj({
    "chosen_acceptable": B, "chosen_errors": {"type": "array", "items": S},
    "checkable_constraints": {"type": "array", "items": _obj({"constraint": S, "chosen_satisfies": _enum(["yes", "no", "unclear"])})},
    "rejected_meaningfully_worse": B, "maths_content": B, "notes": S,
})


BRANCH_VERIFY_V2_VERSION = "dv2-branch-verify-v2"
BRANCH_VERIFY_V2_SCHEMA = _obj({
    "constraints": {"type": "array", "items": _obj({
        "constraint": S,
        "source": _enum(["user_stated", "task_implied", "reference_derived"]),
        "applies_now": B,
        "satisfied": _enum(["yes", "no", "unclear", "not_applicable"]),
    })},
    "chosen_responsive": B, "chosen_truthful": B,
    "chosen_violations": {"type": "array", "items": S},
    "chosen_verdict": _enum(["clean", "flawed_but_better", "unacceptable"]),
    "rejected_meaningfully_worse": B, "notes": S,
})


CHANGE_TYPES = ["none", "clarification", "example", "simplification", "decomposition", "new_constraint", "changed_goal",
                "supplied_solution", "complaint_only", "restatement"]
C60_REVIEW_SCHEMA = _obj({
    "turns": {"type": "array", "items": _obj({
        "assistant_turn": {"type": "integer"}, "local_quality": _enum(SEVERITIES), "decisive_evidence": S, "error_summary": S,
        "disclosed_constraints_checked": {"type": "array", "items": S},
        "undisclosed_preferences_not_counted": {"type": "array", "items": S},
        "used_latest_guidance": _enum(["yes", "partly", "no", "not_applicable"]),
        "retained_earlier_constraints": _enum(["yes", "partly", "no", "not_applicable"]),
        "repeats_earlier_failed_reply": B, "factual_or_subject_errors": {"type": "array", "items": S},
        "maths_content": B, "consistent_with_world_or_learner_state": _enum(["yes", "no", "not_applicable"]),
        "needs_human_review": B, "confidence": _enum(["low", "medium", "high"])})},
    "user_turns": {"type": "array", "items": _obj({
        "user_turn_index": {"type": "integer"},
        "reacts_to_visible_event": _enum(["yes", "no", "not_applicable"]),
        "reacts_to_real_defect": _enum(["yes", "no", "not_applicable"]),
        "oracle_leak": B, "instruction_change": B, "change_type": _enum(CHANGE_TYPES),
        "change_quality": _enum(["helpful", "unhelpful", "contradictory", "not_applicable"]), "simulator_defect": S})},
    "world_consistency": _obj({"applicable": B, "consistent": B, "issues": {"type": "array", "items": S}}),
    "learning": _obj({"applicable": B, "progress_supported_by_teaching": B, "transfer_attempted": B,
                      "transfer_attempt_sound": _enum(["yes", "partly", "no", "not_applicable"]),
                      "sudden_unsupported_expertise": B, "evidence": S}),
    "hidden_information_leaked_to_assistant": B, "leak_evidence": S,
    "target_errors": {"type": "array", "items": S}, "simulator_defects": {"type": "array", "items": S},
    "task_result": _enum(["completed", "partially_completed", "not_completed", "unclear"]),
    "ending_reason_agrees": B, "ending_comment": S,
    "proposed_A": _obj({"exists": B, "before_assistant_turn": {"type": "integer"}, "reason": S}),
    "proposed_B": _obj({"exists": B, "after_user_turn": {"type": "integer"}, "reason": S}),
    "summary": S,
})


def dev_row(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    out.update(DEV_TAGS)
    return out


def assert_dev_row(row: dict[str, Any]) -> None:
    for key, value in DEV_TAGS.items():
        if row.get(key) != value:
            raise ValueError(f"development row lacks {key}={value!r}: {row.get('row_id') or row.get('case_id')}")
