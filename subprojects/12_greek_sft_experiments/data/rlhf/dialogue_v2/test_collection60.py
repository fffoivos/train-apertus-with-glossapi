#!/usr/bin/env python3
"""Offline tests for the 60-dialogue collection changes (amendment): generic world deriver, scheduled strategy change,
silent departure, A/B points (instruction changes not filtered by helpfulness), duplicate-aware judging."""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import worlds
from user_state import allowed_moves, init_state, validate_decision
import points
from common import append_jsonl, is_c60, run_tag_for, runtime_dir_for


def world():
    return {"derive": "declarative_v1", "root_cause": "x", "hidden_facts": [],
            "initial_state": {"cable": "old", "restarted": False}, "state_domains": {"cable": ["old", "new"], "restarted": [False, True]},
            "derived_rules": [{"name": "fixed", "any_of": [{"cable": "new"}]}],
            "checks": {"restart": {"description": "restart", "preconditions": "", "effects": {"restarted": True}, "conditional_effects": [],
                                   "observations": [{"when": {"fixed": True}, "text": "Works."}, {"when": {}, "text": "Still broken."}]},
                       "swap_cable": {"description": "swap", "preconditions": "", "effects": {"cable": "new"}, "conditional_effects": [],
                                      "observations": [{"when": {"fixed": True}, "text": "Works now."}, {"when": {}, "text": "No change."}]}}}


def seed(category="existing_type", cid="C60C01"):
    return {"case_id": cid, "category": category, "labels": {"attitude": "cooperative"},
            "user_state": {"goal": "g", "known_facts": [], "expertise": "novice", "patience": "low", "helping_ability": "restate_only",
                           "helping_ability_note": "n", "disclosed_preferences": [], "private_preferences": []}}


def decision(move, defect=True, message="m", done=False, level="none"):
    return {"move": move, "done": done, "message": message, "perceived_latest_reply": {"defect_present": defect, "defect": "", "same_defect_as_before": False, "useful_progress": False},
            "assistance_level": level, "revealed_private_preference_ids": [], "changes_task": move in {"simplify", "add_context"},
            "knowledge_updates": [], "transfer_attempt": {"attempted": False, "attempt_text": ""}}


class Worlds(unittest.TestCase):
    def test_declarative_world_validates_and_resolves(self):
        w = world()
        self.assertEqual(worlds.validate_world(w), [])
        text, state, _ = worlds.apply_check(w, worlds.initial_state(w), "restart")
        self.assertEqual(text, "Still broken.")
        text, state, _ = worlds.apply_check(w, state, "swap_cable")
        self.assertEqual(text, "Works now.")


class Routing(unittest.TestCase):
    def test_c60_ids_route_to_their_own_runtime(self):
        self.assertTrue(is_c60("C60T03")); self.assertEqual(run_tag_for("C60L01"), "c60")
        self.assertTrue(str(runtime_dir_for("C60C01")).endswith("collection60/runtime"))
        self.assertEqual(run_tag_for("DVI001"), "dvi")


class ScheduledChange(unittest.TestCase):
    def state_after_one_failure(self, s):
        st = init_state(s); st["moves_so_far"] = ["point_to_defect"]; st["consecutive_failed_replies"] = 1
        return st

    def test_second_failure_requires_instruction_change_even_for_low_patience(self):
        s = seed(); st = self.state_after_one_failure(s)
        moves, reasons = allowed_moves(st, "next_turn", s)
        self.assertTrue({"simplify", "clarify", "add_context"} <= set(moves))
        problems = validate_decision(decision("express_frustration"), st, moves, "next_turn", s)
        self.assertTrue(any(p.startswith("strategy change required") for p in problems))
        self.assertFalse(any(p.startswith("strategy change required") for p in validate_decision(decision("simplify", level="pointed_defect"), st, moves, "next_turn", s)))

    def test_rule_does_not_apply_when_the_second_reply_succeeds_or_outside_the_correction_group(self):
        s = seed(); st = self.state_after_one_failure(s)
        moves, _ = allowed_moves(st, "next_turn", s)
        self.assertFalse(any(p.startswith("strategy change required") for p in validate_decision(decision("continue", defect=False), st, moves, "next_turn", s)))
        t = seed("troubleshooting", "C60T01"); st2 = self.state_after_one_failure(t)
        m2, _ = allowed_moves(st2, "next_turn", t)
        self.assertFalse(any(p.startswith("strategy change required") for p in validate_decision(decision("express_frustration"), st2, m2, "next_turn", t)))

    def test_c60_abandonment_may_carry_a_message_but_old_protocol_may_not(self):
        s = seed(); st = init_state(s); st["consecutive_failed_replies"] = 3
        moves, _ = allowed_moves(st, "next_turn", s)
        self.assertNotIn("finish/abandon must have an empty message", validate_decision(decision("abandon", message="forget it", done=True), st, moves, "next_turn", s))
        old = seed(cid="DVI001")
        self.assertIn("finish/abandon must have an empty message", validate_decision(decision("abandon", message="forget it", done=True), st, moves, "next_turn", old))


class ABPoints(unittest.TestCase):
    def test_unhelpful_instruction_change_still_yields_b_and_complaint_does_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            rt = pathlib.Path(tmp); cid = "C60C09"
            msgs = [{"role": "user", "content": "u0"}, {"role": "assistant", "content": "a1"}, {"role": "user", "content": "u1 complaint"},
                    {"role": "assistant", "content": "a2"}, {"role": "user", "content": "u2 simpler please"}, {"role": "assistant", "content": "a3"}]
            append_jsonl(rt / "trajectories.jsonl", {"case_id": cid, "messages": msgs, "ending_reason": "silent_departure"})
            for t, q in ((1, "serious"), (2, "serious"), (3, "minor")):
                append_jsonl(rt / "turn_evaluations.jsonl", {"case_id": cid, "assistant_turn": t, "local_quality": q, "error_summary": "e"})
                append_jsonl(rt / "assistant_turns.jsonl", {"case_id": cid, "assistant_turn": t, "usage": {"prompt_tokens": 200}})
            append_jsonl(rt / "user_turns.jsonl", {"case_id": cid, "mode": "next_turn", "user_turn_index": 1, "move": "express_frustration", "message": "u1", "changes_task": False})
            append_jsonl(rt / "user_turns.jsonl", {"case_id": cid, "mode": "next_turn", "user_turn_index": 2, "move": "simplify", "message": "u2", "changes_task": True})
            append_jsonl(rt / "conversation_reviews.jsonl", {"case_id": cid, "user_turns": [
                {"user_turn_index": 1, "instruction_change": False, "change_type": "complaint_only", "change_quality": "not_applicable"},
                {"user_turn_index": 2, "instruction_change": True, "change_type": "simplification", "change_quality": "unhelpful"}]})
            out = points.possible_points_c60({"case_id": cid}, rt)
            kinds = {p["kind"]: p for p in out["points"]}
            self.assertEqual(kinds["A"]["before_assistant_turn"], 1)
            self.assertEqual(kinds["B"]["before_assistant_turn"], 3)
            self.assertEqual(kinds["B"]["change_quality"], "unhelpful")
            self.assertEqual(kinds["A"]["prefix_messages"], msgs[:1]); self.assertEqual(kinds["B"]["prefix_messages"], msgs[:5])
            self.assertEqual([c["instruction_change"] for c in out["change_points"]], [False, True])

    def test_no_serious_error_records_absence_reasons(self):
        with tempfile.TemporaryDirectory() as tmp:
            rt = pathlib.Path(tmp); cid = "C60L02"
            append_jsonl(rt / "trajectories.jsonl", {"case_id": cid, "messages": [{"role": "user", "content": "u"}, {"role": "assistant", "content": "a"}], "ending_reason": "natural_completion"})
            append_jsonl(rt / "turn_evaluations.jsonl", {"case_id": cid, "assistant_turn": 1, "local_quality": "good"})
            out = points.possible_points_c60({"case_id": cid}, rt)
            self.assertEqual(out["points"], []); self.assertIn("A", out["absent"]); self.assertIn("B", out["absent"])


class LeakCheck(unittest.TestCase):
    def test_strings_the_user_already_knows_are_not_hidden(self):
        import views
        state = {"known_facts": ["Google Meet is marked Always allowed."]}
        msgs = [{"role": "user", "content": "u"}, {"role": "assistant", "content": "The bell icon is crossed out."}]
        out = views.already_known(["Google Meet is marked Always allowed.", "The bell icon is crossed out.", "The hidden root cause string."], state, msgs)
        self.assertEqual(out, ["The hidden root cause string."])


if __name__ == "__main__":
    unittest.main()
