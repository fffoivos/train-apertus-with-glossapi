from __future__ import annotations

import json
import collections
import contextlib
import io
import pathlib
import tempfile
import threading
import unittest

import analyse
import annotate
import budget
import candidates
import dqd
import export_pairs
import forecast
import manifest
import openings
import rank
import rollout
import select
from unittest import mock
from clients import ContextLimitError, FakeSolClient, FakeTargetClient, TargetResult
from common import append_jsonl, atomic_json, read_json, read_jsonl, sha256_json, sha256_text


CHECKPOINT = "a" * 64


def config(sol_max=120, reservations=None):
    return {"version": "test", "seed": 9162602,
            "smoke": {"trajectories": 1, "max_assistant_turns": 3},
            "measurement": {"target_trajectories": 1, "admission_sizes": [35, 28, 21, 14],
                            "max_assistant_turns": 8},
            "budget": {"max_new_sol_calls": sol_max, "sol_reservations": reservations or {
                "smoke": 6, "openings": 10, "user_continuation": 38, "annotation": 40,
                "adjudication": 10, "candidate_review": 8, "repairs": 8},
                "operational_stop_eur": 4, "prime_intellect_total_eur": 5, "reserve_eur": 1}}


def seed(tid="SM001", stage="smoke", horizon=3):
    return {"trajectory_id": tid, "stage": stage, "split": "smoke" if stage == "smoke" else "train",
            "instance_hash": "i-" + tid, "content_family": "f-" + tid, "family": "m_arithmetic",
            "task": "math", "language": "en", "difficulty": "routine", "interaction": "followup",
            "attitude": "cooperative", "register": "standard", "max_assistant_turns": horizon,
            "fixture": {"content": "2 items at 3 cents", "instruction_spec": "Ask the total.",
                        "reference": {"answer": 6, "secret": "PRIVATE_SENTINEL"},
                        "checks": [{"type": "exact_number", "value": 6}], "parameters": {}}}


def make_state(root: pathlib.Path, stage="smoke", tid="SM001", horizon=3):
    cfg = config()
    atomic_json(root / "manifest.json", {"version": "test", "seed": 9162602, "config": cfg,
                                         "planned_joint_counts": {}, "seeds": [seed(tid, stage, horizon)]})
    atomic_json(root / "source_config.json", cfg)
    directory = root / stage; directory.mkdir(parents=True)
    for name in ("user_events.jsonl", "trajectories.jsonl", "annotations.jsonl", "adjudications.jsonl",
                 "selection.jsonl", "candidates.jsonl", "rankings.jsonl", "preferences.jsonl", "rejected_pairs.jsonl"):
        (directory / name).touch()
    append_jsonl(directory / "user_events.jsonl", {
        "trajectory_id": tid, "turn_index": 0, "message": {"role": "user", "content": "What is 2×3?"},
        "user_goal": "get the total", "interaction_plan": "follow up naturally"})


def target(text="answer", finish="stop"):
    return TargetResult(text, finish, "fake-model", {"prompt_tokens": 5, "completion_tokens": 2}, .1)


class PromptSafetyTests(unittest.TestCase):
    def test_opening_prompt_hides_reference_checks_and_parameters(self):
        prompt = openings.opening_prompt([seed()])
        self.assertIn("Ask the total", prompt)
        self.assertNotIn("PRIVATE_SENTINEL", prompt)
        self.assertNotIn("exact_number", prompt)

    def test_user_prompt_only_contains_visible_state(self):
        s = seed()
        s["annotation"] = "ANNOTATION_SENTINEL"
        prompt = rollout.user_prompt(s, [{"role": "user", "content": "visible"}],
                                     {"user_goal": "goal", "interaction_plan": "plan",
                                      "future": "FUTURE_SENTINEL"})
        self.assertIn("visible", prompt)
        self.assertNotIn("PRIVATE_SENTINEL", prompt)
        self.assertNotIn("ANNOTATION_SENTINEL", prompt)
        self.assertNotIn("FUTURE_SENTINEL", prompt)

    def test_annotation_packet_has_no_later_turn(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_state(root)
            messages = [{"role": "user", "content": "first"}, {"role": "assistant", "content": "six"},
                        {"role": "user", "content": "LATER_USER_SENTINEL"},
                        {"role": "assistant", "content": "LATER_ASSISTANT_SENTINEL"}]
            append_jsonl(root / "smoke" / "trajectories.jsonl", {"trajectory_id": "SM001", "messages": messages,
                                                                  "assistant_turns": 2, "terminal_code": "horizon"})
            packets = annotate.build_packets(root, "smoke")
            first = json.dumps(packets[0], ensure_ascii=False)
            self.assertNotIn("LATER_USER_SENTINEL", first)
            self.assertNotIn("LATER_ASSISTANT_SENTINEL", first)
            self.assertIn("PRIVATE_SENTINEL", first)  # private evidence is annotator-only

    def test_rank_prompt_random_letters_hide_provenance(self):
        prompt = rank.ranking_prompt([{"role": "user", "content": "q"}], {"A": "one", "B": "two", "C": "three"})
        self.assertIn("CANDIDATE A", prompt)
        self.assertNotIn("original", prompt.lower())
        ids = ["c0", "c1", "c2"]
        import random
        random.Random("9162602|SEL001").shuffle(ids)
        self.assertNotEqual(ids, ["c0", "c1", "c2"])


class RolloutTests(unittest.TestCase):
    def run_case(self, target_values, sol_values, max_turns=None):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        root = pathlib.Path(td.name); make_state(root)
        fake_target = FakeTargetClient(target_values, ["fake-model"])
        fake_sol = FakeSolClient(sol_values)
        result = rollout.rollout(root, "smoke", fake_target, fake_sol, "http://offline/v1",
                                 "fake-model", CHECKPOINT, max_turns=max_turns)
        latest = analyse.latest_trajectories(root / "smoke" / "trajectories.jsonl")["SM001"]
        return result, latest, fake_target, root

    def test_n_one_and_byte_identical_text_hash(self):
        raw = "  exact bytes\nδεδομένα  "
        _, latest, fake, root = self.run_case([target(raw)],
            [{"users": [{"trajectory_id": "SM001", "done": True, "message": "", "reason": "complete"}]}])
        self.assertEqual(fake.calls[0]["n"], 1)
        self.assertEqual(latest["messages"][1]["content"], raw)
        observed = [r for r in read_jsonl(root / "ledger.jsonl") if r.get("record") == "observed_completion"][0]
        self.assertEqual(observed["receipt"]["text_sha256"], sha256_text(raw))

    def test_measurement_three_turn_horizon_rejected_before_checks_or_clients(self):
        with tempfile.TemporaryDirectory() as td:
            target_client = mock.Mock()
            sol_client = mock.Mock()
            with mock.patch.object(rollout, "validate_generator_isolation") as generator_check:
                with self.assertRaisesRegex(ValueError, "measurement rollout horizon must be exactly 8"):
                    rollout.rollout(td, "measurement", target_client, sol_client, "http://offline/v1",
                                    "fake-model", CHECKPOINT, max_turns=3)
                with self.assertRaisesRegex(ValueError, "smoke rollout horizon must be exactly 3"):
                    rollout.rollout(td, "smoke", target_client, sol_client, "http://offline/v1",
                                    "fake-model", CHECKPOINT, max_turns=8)
            generator_check.assert_not_called()
            target_client.models.assert_not_called()
            target_client.complete.assert_not_called()
            sol_client.call.assert_not_called()

    def test_natural_completion(self):
        _, latest, _, _ = self.run_case([target("6")],
            [{"users": [{"trajectory_id": "SM001", "done": True, "message": "", "reason": "done"}]}])
        self.assertEqual(latest["terminal_code"], "completed")

    def test_truncation(self):
        _, latest, _, _ = self.run_case([target("cut", "length")], [])
        self.assertEqual(latest["terminal_code"], "truncated_output")

    def test_context_limit(self):
        _, latest, _, _ = self.run_case([ContextLimitError("too long")], [])
        self.assertEqual(latest["terminal_code"], "context_limit")

    def test_horizon_distinct(self):
        follows = [
            {"users": [{"trajectory_id": "SM001", "done": False, "message": "again", "reason": "continue"}]},
            {"users": [{"trajectory_id": "SM001", "done": False, "message": "last", "reason": "continue"}]},
        ]
        _, latest, _, _ = self.run_case([target("a"), target("b"), target("c")], follows)
        self.assertEqual(latest["terminal_code"], "horizon")
        self.assertEqual(latest["assistant_turns"], 3)

    def test_observed_completion_is_reused_after_crash(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); atomic_json(root / "source_config.json", config())
            ledger = budget.CallLedger(root, config())
            fake = FakeTargetClient([target("bad but final")])
            first = rollout.sample_assistant(ledger, fake, "smoke", "T", 1,
                                             [{"role": "user", "content": "q"}], "fake-model", CHECKPOINT)
            empty = FakeTargetClient([])
            second = rollout.sample_assistant(ledger, empty, "smoke", "T", 1,
                                              [{"role": "user", "content": "q"}], "fake-model", CHECKPOINT)
            self.assertEqual(first.text, second.text)
            self.assertEqual(len(fake.calls), 1)
            self.assertEqual(len(empty.calls), 0)

    def test_rollout_restart_at_all_persisted_crash_boundaries(self):
        for boundary in ("after_target_completion", "after_assistant_snapshot", "after_sol_completion"):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as td:
                root = pathlib.Path(td); make_state(root)
                first_target = FakeTargetClient([target("observed once")], ["fake-model"])
                first_sol = FakeSolClient([{"users": [{"trajectory_id": "SM001", "done": True,
                                                        "message": "", "reason": "complete"}]}])
                fired = {"value": False}
                def crash(point, tid, turn):
                    if point == boundary and not fired["value"]:
                        fired["value"] = True
                        raise RuntimeError("injected crash")
                with self.assertRaisesRegex(RuntimeError, "injected crash"):
                    rollout.rollout(root, "smoke", first_target, first_sol, "http://offline/v1",
                                    "fake-model", CHECKPOINT, crash_hook=crash)
                second_target = FakeTargetClient([], ["fake-model"])
                second_sol_results = ([{"users": [{"trajectory_id": "SM001", "done": True,
                                                     "message": "", "reason": "complete"}]}]
                                      if boundary != "after_sol_completion" else [])
                second_sol = FakeSolClient(second_sol_results)
                rollout.rollout(root, "smoke", second_target, second_sol, "http://offline/v1",
                                "fake-model", CHECKPOINT)
                latest = analyse.latest_trajectories(root / "smoke" / "trajectories.jsonl")["SM001"]
                self.assertEqual(latest["terminal_code"], "completed")
                self.assertEqual(len(first_target.calls), 1)
                self.assertEqual(len(second_target.calls), 0)
                self.assertEqual(len(first_sol.calls) + len(second_sol.calls), 1)


class AnnotationAnalysisTests(unittest.TestCase):
    def test_first_serious_recovery_and_no_failure(self):
        rows = [
            {"turn_index": 1, "local_quality": "good", "recovery_opportunity": False, "recovery_success": False},
            {"turn_index": 2, "local_quality": "serious", "recovery_opportunity": False, "recovery_success": False},
            {"turn_index": 3, "local_quality": "minor", "recovery_opportunity": True, "recovery_success": True},
        ]
        self.assertEqual(analyse.first_serious_and_recovery(rows), (2, 3))
        no_failure = analyse.derive_trajectory(rows[:1], "completed")
        self.assertTrue(no_failure["no_failure_observed"])
        self.assertEqual(no_failure["no_failure_kind"], "natural_completion")

    def test_batch_limits_tokens_and_no_same_trajectory(self):
        packets = []
        for i in range(12):
            packets.append({"annotation_id": str(i), "trajectory_id": f"T{i//2}",
                            "estimated_input_tokens": 1000})
        batches = annotate.batch_packets(packets)
        for batch in batches:
            self.assertLessEqual(len(batch), 8)
            self.assertLessEqual(sum(p["estimated_input_tokens"] for p in batch), 24000)
            self.assertEqual(len({p["trajectory_id"] for p in batch}), len(batch))
        long_packets = [{"annotation_id": str(i), "trajectory_id": f"L{i}", "estimated_input_tokens": 4000} for i in range(7)]
        self.assertTrue(all(len(b) <= 4 for b in annotate.batch_packets(long_packets)))

    def test_report_requires_complete_calibration_and_boundary_review(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_state(root)
            messages = [{"role": "user", "content": "q1"}, {"role": "assistant", "content": "bad"},
                        {"role": "user", "content": "repair?"}, {"role": "assistant", "content": "fixed"}]
            append_jsonl(root / "smoke" / "trajectories.jsonl", {"trajectory_id": "SM001", "messages": messages,
                "assistant_turns": 2, "terminal_code": "horizon"})
            for turn, quality, opportunity in ((1, "serious", False), (2, "good", True)):
                append_jsonl(root / "smoke" / "annotations.jsonl", {"annotation_id": f"SM001:a{turn}",
                    "trajectory_id": "SM001", "turn_index": turn, "local_quality": quality,
                    "language": "en", "task": "math", "cumulative_tokens": 10 * turn,
                    "recovery_opportunity": opportunity, "recovery_success": opportunity})
            sampled = annotate.calibration_sample(root, "smoke", n=1)
            self.assertEqual({r["annotation_id"] for r in sampled}, {"SM001:a1", "SM001:a2"})
            with self.assertRaisesRegex(ValueError, "review incomplete"):
                analyse.freeze_report(root, "smoke")
            decisions = root / "one.jsonl"
            append_jsonl(decisions, {"annotation_id": "SM001:a1", "decision": "serious", "evidence": "clear",
                                     "reviewer": "root"})
            annotate.adjudicate(root, "smoke", decisions)
            with self.assertRaisesRegex(ValueError, "review incomplete"):
                analyse.freeze_report(root, "smoke")
            decisions2 = root / "two.jsonl"
            append_jsonl(decisions2, {"annotation_id": "SM001:a2", "decision": "good", "evidence": "repair",
                                      "reviewer": "root", "recovery_opportunity": True, "recovery_success": True})
            annotate.adjudicate(root, "smoke", decisions2)
            report = analyse.freeze_report(root, "smoke")
            self.assertEqual(report["calibration_review"]["reviewed"], 2)

    def test_report_recomputes_shifted_first_serious_boundary_until_stable(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_state(root)
            messages = []
            for turn in range(1, 26):
                messages.extend(({"role": "user", "content": f"q{turn}"},
                                 {"role": "assistant", "content": f"a{turn}"}))
                append_jsonl(root / "smoke" / "annotations.jsonl", {
                    "annotation_id": f"SM001:a{turn}", "trajectory_id": "SM001", "turn_index": turn,
                    "local_quality": "serious" if turn in (1, 2) else "good", "language": "en",
                    "task": "math", "cumulative_tokens": 10 * turn,
                    "recovery_opportunity": False, "recovery_success": False})
            append_jsonl(root / "smoke" / "trajectories.jsonl", {"trajectory_id": "SM001",
                "messages": messages, "assistant_turns": 25, "terminal_code": "horizon"})
            sampled = [r for r in read_jsonl(root / "smoke" / "annotations.jsonl")
                       if r["annotation_id"] != "SM001:a2"]
            calibration_path = root / "smoke" / "calibration.jsonl"
            calibration_path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in sampled), encoding="utf-8")
            sampled_ids = [r["annotation_id"] for r in sampled]
            atomic_json(root / "smoke" / "calibration_receipt.json", {
                "required_sample_size": 24, "sampled_ids": sampled_ids,
                "mandatory_boundary_ids": ["SM001:a1"], "effective_boundary_ids": ["SM001:a1"],
                "required_review_ids": sampled_ids,
                "calibration_sha256": sha256_text(calibration_path.read_text(encoding="utf-8"))})
            decisions = root / "initial-decisions.jsonl"
            for aid in sampled_ids:
                append_jsonl(decisions, {"annotation_id": aid,
                    "decision": "minor" if aid == "SM001:a1" else "good",
                    "evidence": "independent review", "reviewer": "root"})
            annotate.adjudicate(root, "smoke", decisions)
            with self.assertRaisesRegex(ValueError, "effective-boundary recompute"):
                analyse.freeze_report(root, "smoke")
            updated = read_json(root / "smoke" / "calibration_receipt.json")
            self.assertEqual(updated["effective_boundary_ids"], ["SM001:a2"])
            shifted = root / "shifted-decision.jsonl"
            append_jsonl(shifted, {"annotation_id": "SM001:a2", "decision": "serious",
                                   "evidence": "next effective onset", "reviewer": "root"})
            annotate.adjudicate(root, "smoke", shifted)
            report = analyse.freeze_report(root, "smoke")
            self.assertEqual(report["calibration_review"]["effective_boundary_ids"], ["SM001:a2"])
            self.assertTrue(report["calibration_review"]["boundary_set_stable"])


class BudgetManifestTests(unittest.TestCase):
    def test_atomic_sol_caps_and_failed_attempts_count(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); cfg = config(sol_max=2, reservations={"x": 1})
            atomic_json(root / "source_config.json", cfg)
            ledger = budget.CallLedger(root, cfg)
            self.assertIsNone(ledger.reserve("a", "sol", "x", {}))
            ledger.finish("a", error="failed")
            with self.assertRaises(budget.BudgetExceeded):
                ledger.reserve("b", "sol", "x", {})
            rows = read_jsonl(root / "ledger.jsonl")
            self.assertEqual([r["record"] for r in rows], ["call_reserved", "call_completed"])

    def test_atomic_concurrent_reservation(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); cfg = config(sol_max=2, reservations={"x": 2})
            atomic_json(root / "source_config.json", cfg)
            outcomes = []
            def reserve(i):
                try:
                    budget.CallLedger(root, cfg).reserve(str(i), "sol", "x", {})
                    outcomes.append("ok")
                except budget.BudgetExceeded:
                    outcomes.append("blocked")
            threads = [threading.Thread(target=reserve, args=(i,)) for i in range(8)]
            [t.start() for t in threads]; [t.join() for t in threads]
            self.assertEqual(outcomes.count("ok"), 2)

    def test_deadline_shutdown(self):
        deadline = budget.conservative_deadline("2026-01-01T00:00:00+00:00", 1, 2, 1,
                                                operational_stop_eur=4, setup_reserve_eur=1, safety_factor=1)
        self.assertEqual(deadline, "2026-01-01T01:00:00+00:00")
        self.assertTrue(budget.shutdown_due(deadline, "2026-01-01T01:00:00+00:00"))
        self.assertFalse(budget.shutdown_due(deadline, "2026-01-01T00:59:59+00:00"))
        with tempfile.TemporaryDirectory() as td:
            row = budget.gpu_start(td, "pod", 2, 1, now="2026-01-01T00:00:00+00:00")
            self.assertIn("shutdown_deadline_utc", row)

    def test_manifest_families_never_cross_stages_and_exact_counts(self):
        cfg_path = pathlib.Path(__file__).resolve().parents[3] / "docs" / "RLHF_COORDINATION" / "DIALOGUE_PILOT_CONFIG_20260916.json"
        with tempfile.TemporaryDirectory() as td:
            data = manifest.initialize(td, cfg_path)
            self.assertEqual(len(data["seeds"]), 41)
            family_splits = {}
            for row in data["seeds"]:
                self.assertNotIn(row["content_family"], family_splits)
                family_splits[row["content_family"]] = (row["stage"], row["split"])
            self.assertEqual(data["actual_joint_counts"]["language"], {"de": 1, "el": 25, "en": 5, "es": 1, "fr": 1, "it": 1, "pt": 1})
            self.assertIn("task__interaction", data["actual_joint_counts"])
            self.assertIn("task__language__interaction__attitude__register__difficulty", data["actual_joint_counts"])
            self.assertTrue(all(manifest.family_compatible(row, row["family"]) for row in data["seeds"]))
            self.assertEqual(data["joint_assignment_repairs"]["after_incompatible_task_interactions"], [])
            self.assertIn("before_task_interaction_counts", data["joint_assignment_repairs"])
            smoke_prompt = openings.opening_prompt([s for s in data["seeds"] if s["stage"] == "smoke"])
            for instruction in manifest.SCENARIO_INSTRUCTIONS.values():
                self.assertIn(instruction, smoke_prompt)
            for row in data["seeds"]:
                if row["interaction"] == "revision" and row["stage"] == "measurement":
                    self.assertIn(row["family"], manifest.INTERACTION_FAMILIES["revision"])
            for size in (35, 28, 21, 14):
                reduced = manifest.reduced_admission(data["seeds"], size)
                self.assertEqual(len(reduced["trajectory_ids"]), size)
                self.assertEqual(sum(reduced["actual_counts"]["language"].values()), size)
                if reduced["feasibility"]["exact_required_margins"]:
                    self.assertEqual(reduced["deviations"], [])
                else:
                    self.assertTrue(reduced["feasibility"]["reason"])
                    self.assertTrue(reduced["deviations"])
                actual = {"task_language": reduced["actual_counts"]["task__language"],
                          **{axis: reduced["actual_counts"][axis]
                             for axis in ("interaction", "attitude", "register", "difficulty")}}
                expected_deviations = {(axis, cell, target, actual[axis].get(cell, 0))
                    for axis, targets in reduced["target_counts"].items()
                    for cell, target in targets.items() if target != actual[axis].get(cell, 0)}
                recorded_deviations = {(row["axis"], row["cell"], row["target"], row["actual"])
                                       for row in reduced["deviations"]}
                self.assertEqual(recorded_deviations, expected_deviations)
            self.assertFalse(manifest.reduced_admission(data["seeds"], 28)["feasibility"]["exact_required_margins"])
            self.assertTrue((pathlib.Path(td) / "receipt.json").exists())
            self.assertTrue((pathlib.Path(td) / "cost_ledger.json").exists())

    def test_quota_counts_only_accepted(self):
        rows = [{"language": "el", "terminal_code": None}, {"language": "en", "terminal_code": "infra_failure"},
                {"language": "el", "terminal_code": "completed"}]
        self.assertEqual(manifest.count_accepted(rows, "language"), {"el": 1})

    def test_live_generator_collision_is_rechecked(self):
        cfg_path = pathlib.Path(__file__).resolve().parents[3] / "docs" / "RLHF_COORDINATION" / "DIALOGUE_PILOT_CONFIG_20260916.json"
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); data = manifest.initialize(root, cfg_path)
            admitted = data["seeds"][6]
            forecast_row = {"admitted_size": 1, "admitted_trajectory_ids": [admitted["trajectory_id"]]}
            atomic_json(root / "forecast.json", forecast_row)
            receipt = read_json(root / "receipt.json")
            receipt["artifacts"]["forecast.json"] = {"sha256": sha256_text((root / "forecast.json").read_text()),
                                                       "frozen": True}
            atomic_json(root / "receipt.json", receipt)
            with mock.patch.object(manifest, "_external_reservations",
                                   return_value=({admitted["content_family"]}, set())):
                with self.assertRaisesRegex(ValueError, "live generator registry collision"):
                    manifest.validate_generator_isolation(root, "measurement")

    def test_forecast_uses_full_horizon_per_wave_and_freezes(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_state(root)
            cfg = read_json(root / "manifest.json")["config"]
            append_jsonl(root / "smoke" / "trajectories.jsonl", {"trajectory_id": "SM001",
                "messages": [{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"}],
                "assistant_turns": 1, "terminal_code": "completed"})
            append_jsonl(root / "smoke" / "annotations.jsonl", {"annotation_id": "SM001:a1"})
            ledger = budget.CallLedger(root, cfg)
            ledger.reserve("target:rollout:smoke:SM001:t1", "target", "raw_rollout", {})
            ledger.finish("target:rollout:smoke:SM001:t1", result={"text": "a", "finish_reason": "stop",
                "model": "fake", "usage": {"prompt_tokens": 10, "completion_tokens": 2}, "wall_seconds": 1})
            ledger.reserve("sol:annotation:smoke:x", "sol", "smoke", {"estimated_input_tokens": 100})
            ledger.finish("sol:annotation:smoke:x", result={"annotations": []})
            budget.gpu_start(root, "pod", 1, 1, now="2026-01-01T00:00:00+00:00")
            append_jsonl(root / "ledger.jsonl", {"record": "observed_completion", "provider": "target",
                "trajectory_id": "SM001", "turn_index": 1, "created_utc": "2026-01-01T00:00:05+00:00",
                "receipt": {}})
            budget.gpu_stop(root, "pod", now="2026-01-01T00:00:10+00:00")
            result = forecast.forecast(root)
            option14 = next(o for o in result["options"] if o["size"] == 14)
            self.assertEqual(option14["raw_target_completions"], 14 * 8)
            self.assertEqual(option14["sol_calls"]["user_continuation"], 7 * 2)
            self.assertEqual(option14["sol_calls"]["annotation"], 14 * 8)
            self.assertEqual(result["admitted_size"], None)  # one packet/call cannot fund even 14
            receipt = read_json(root / "receipt.json")["artifacts"]["forecast.json"]
            self.assertTrue(receipt["frozen"])
            with self.assertRaisesRegex(ValueError, "already frozen"):
                forecast.forecast(root)

    def test_forecast_rate_uses_only_sessions_with_observed_completions(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_state(root)
            cfg = read_json(root / "manifest.json")["config"]
            append_jsonl(root / "smoke" / "trajectories.jsonl", {"trajectory_id": "SM001",
                "messages": [{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"}],
                "assistant_turns": 1, "terminal_code": "completed"})
            append_jsonl(root / "smoke" / "annotations.jsonl", {"annotation_id": "SM001:a1"})
            ledger = budget.CallLedger(root, cfg)
            ledger.reserve("target:rollout:smoke:SM001:t1", "target", "raw_rollout", {})
            ledger.finish("target:rollout:smoke:SM001:t1", result={"text": "a", "finish_reason": "stop",
                "model": "fake", "usage": {"prompt_tokens": 10, "completion_tokens": 2}, "wall_seconds": 1})
            ledger.reserve("sol:annotation:smoke:x", "sol", "smoke", {"estimated_input_tokens": 100})
            ledger.finish("sol:annotation:smoke:x", result={"annotations": []})
            with ledger.db() as db:
                db.execute("INSERT INTO calls(call_id,provider,phase,status,reserved_utc,completed_utc,request,result) "
                           "VALUES(?,?,?,?,?,?,?,?)", ("sol:user:smoke:wave1:x", "sol", "smoke", "complete",
                           "2026-01-01T01:00:30+00:00", "2026-01-01T01:00:50+00:00", "{}", "{}"))
            budget.gpu_start(root, "failed-setup", 1, 1, now="2026-01-01T00:00:00+00:00")
            budget.gpu_stop(root, "failed-setup", now="2026-01-01T00:10:00+00:00")
            budget.gpu_start(root, "successful", 1, 1, now="2026-01-01T01:00:00+00:00")
            append_jsonl(root / "ledger.jsonl", {"record": "observed_completion", "provider": "target",
                "trajectory_id": "SM001", "turn_index": 1, "created_utc": "2026-01-01T01:01:00+00:00",
                "receipt": {}})
            budget.gpu_stop(root, "successful", now="2026-01-01T01:02:00+00:00")
            result = forecast.forecast(root)
            model = result["smoke"]["gpu_rate_model"]
            self.assertEqual([r["pod_id"] for r in model["included_sessions"]], ["successful"])
            self.assertEqual(model["excluded_sessions"][0]["reason"], "zero_observed_target_completions")
            self.assertAlmostEqual(model["basis_billed_seconds"], 120)
            self.assertAlmostEqual(model["productive_seconds_excluding_sol_idle"], 100)
            self.assertAlmostEqual(model["measured_sol_continuation_latency_per_wave_seconds"], 20)
            self.assertAlmostEqual(result["smoke"]["gpu_spent_eur"], 720 / 3600)
            option = next(row for row in result["options"] if row["size"] == 14)
            self.assertGreater(option["gpu_estimate"]["sol_idle_seconds_total_before_margin"], 0)
            self.assertEqual(option["gpu_estimate"]["conservative_margin_fraction"], .15)

    def test_sol_reallocation_funds_in_priority_and_never_raises_cap(self):
        configured = config()["budget"]["sol_reservations"]
        calls28 = {"annotation": 56, "user_continuation": 28, "openings": 4, "candidate_review": 6}
        allocation, receipt = forecast.reallocate_sol_reservations(120, configured, {"smoke": 6}, calls28)
        self.assertIsNotNone(allocation)
        self.assertEqual(sum(allocation.values()), 120)
        self.assertGreaterEqual(allocation["annotation"], calls28["annotation"])
        self.assertGreaterEqual(allocation["user_continuation"], calls28["user_continuation"])
        self.assertGreaterEqual(allocation["openings"], calls28["openings"])
        self.assertGreaterEqual(allocation["candidate_review"], calls28["candidate_review"])
        self.assertEqual(allocation["adjudication"], 1)
        self.assertEqual(allocation["repairs"], 1)
        self.assertTrue(receipt["fundable"])
        calls35 = {"annotation": 70, "user_continuation": 35, "openings": 5, "candidate_review": 6}
        impossible, receipt35 = forecast.reallocate_sol_reservations(120, configured, {"smoke": 6}, calls35)
        self.assertIsNone(impossible)
        self.assertFalse(receipt35["fundable"])

    def test_call_ledger_honours_forecast_reallocation_and_total_cap(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            cfg = config(sol_max=6, reservations={"smoke": 6})
            atomic_json(root / "source_config.json", cfg)
            ledger = budget.CallLedger(root, cfg)
            ledger.reserve("s0", "sol", "smoke", {})
            atomic_json(root / "forecast.json", {"sol_reservations": {
                "smoke": 1, "annotation": 2, "adjudication": 1, "repairs": 2}})
            ledger.reserve("a0", "sol", "annotation", {})
            ledger.reserve("a1", "sol", "annotation", {})
            with self.assertRaisesRegex(budget.BudgetExceeded, "phase reservation"):
                ledger.reserve("a2", "sol", "annotation", {})
            ledger.reserve("j0", "sol", "adjudication", {})
            ledger.reserve("r0", "sol", "repairs", {})
            ledger.reserve("r1", "sol", "repairs", {})
            with self.assertRaisesRegex(budget.BudgetExceeded, "total call cap"):
                ledger.reserve("overflow", "sol", "repairs", {})

    def test_forecast_refuses_after_any_measurement_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_state(root)
            append_jsonl(root / "measurement" / "user_events.jsonl", {"trajectory_id": "ME001"})
            with self.assertRaisesRegex(ValueError, "measurement artifacts"):
                forecast.forecast(root)


class SelectionCandidateExportTests(unittest.TestCase):
    def test_largest_remainders_and_trajectory_cap(self):
        self.assertEqual(select.largest_remainders({"P": 3, "R": 1}, 3, {"P": 3, "R": 1}), {"P": 2, "R": 1})
        eligible = {"C": [], "P": [], "R": []}
        for i in range(20):
            eligible["C"].append({"trajectory_id": f"C{i}", "kind": "C", "depth": i % 8 + 1,
                                  "depth_bin": select.depth_bin(i % 8 + 1), "prefix_sha256": f"pc{i}",
                                  "trajectory_no_observed_failure": True, "task": "everyday", "language": "el"})
            eligible["P"].append({"trajectory_id": f"E{i}", "kind": "P", "depth": i % 8 + 1,
                                  "depth_bin": select.depth_bin(i % 8 + 1), "prefix_sha256": f"pp{i}",
                                  "task": "everyday", "language": "el"})
            eligible["R"].append({"trajectory_id": f"E{i}", "kind": "R", "depth": i % 8 + 1,
                                  "depth_bin": select.depth_bin(i % 8 + 1), "prefix_sha256": f"pr{i}",
                                  "task": "everyday", "language": "el"})
        chosen, receipt = select.allocate_points(eligible, 35)
        counts = {}
        for row in chosen: counts[row["trajectory_id"]] = counts.get(row["trajectory_id"], 0) + 1
        self.assertEqual(len(chosen), 24)
        self.assertLessEqual(max(counts.values()), 2)
        self.assertGreaterEqual(receipt["selected_counts"]["C"], 6)

    def test_controls_reuse_second_capacity_and_shortfalls_are_receipted(self):
        controls = []
        for i in range(3):
            for depth in (1, 3):
                controls.append({"trajectory_id": f"C{i}", "kind": "C", "depth": depth,
                    "depth_bin": select.depth_bin(depth), "prefix_sha256": f"c{i}-{depth}",
                    "trajectory_no_observed_failure": True, "task": "everyday", "language": "el"})
        chosen, receipt = select.allocate_points({"C": controls, "P": [], "R": []}, 24)
        self.assertEqual(len(chosen), 6)
        self.assertEqual(receipt["selected_counts"]["C"], 6)
        self.assertTrue(any(r["reason"] == "control_second_pass_reuses_trajectory_capacity"
                            for r in receipt["redistributions"]))
        eligible = {"C": [], "P": [], "R": []}
        for i in range(6):
            base = {"trajectory_id": f"E{i}", "depth": 1, "depth_bin": "early",
                    "task": "everyday", "language": "el"}
            eligible["C"].append({**base, "kind": "C", "prefix_sha256": f"c{i}",
                                  "trajectory_no_observed_failure": True})
            eligible["P"].append({**base, "kind": "P", "prefix_sha256": f"p{i}"})
            eligible["R"].append({**base, "kind": "R", "prefix_sha256": f"r{i}"})
        _, constrained = select.allocate_points(eligible, 24)
        records = [r for r in constrained["redistributions"] if "capacity_shortfall" in r["reason"]]
        self.assertTrue(records)
        self.assertTrue(all("old_quota" in r and "new_quota" in r for r in records))

    def test_control_depth_matching_reserves_multibin_trajectory(self):
        controls = []
        for tid, depths in (("C0", (1, 6)), ("C1", (1,)), ("C2", (1,)), ("C3", (1,))):
            for depth in depths:
                controls.append({"trajectory_id": tid, "kind": "C", "depth": depth,
                    "depth_bin": select.depth_bin(depth), "prefix_sha256": f"{tid}-{depth}",
                    "trajectory_no_observed_failure": True, "task": "everyday", "language": "el"})
        errors = [{"trajectory_id": f"P{i}", "kind": "P", "depth": 1, "depth_bin": "early",
                   "prefix_sha256": f"p{i}", "task": "math", "language": "en"} for i in range(10)]
        chosen, receipt = select.allocate_points({"C": controls, "P": errors, "R": []}, 14)
        selected_controls = [p for p in chosen if p["kind"] == "C"]
        self.assertEqual(len(selected_controls), 4)
        self.assertEqual(collections.Counter(p["depth_bin"] for p in selected_controls),
                         {"early": 3, "late": 1})
        self.assertIn(("C0", "late"), {(p["trajectory_id"], p["depth_bin"]) for p in selected_controls})
        self.assertEqual(receipt["initial_control_depth_quota"], {"early": 3, "middle": 0, "late": 1})

    def test_infeasible_control_depth_quota_is_recomputed_and_receipted(self):
        controls = []
        for tid, depths in (("A", (1, 6)), ("B", (1, 6)), ("C", (3,)), ("D", (3,))):
            for depth in depths:
                controls.append({"trajectory_id": tid, "kind": "C", "depth": depth,
                    "depth_bin": select.depth_bin(depth), "prefix_sha256": f"{tid}-{depth}",
                    "trajectory_no_observed_failure": True, "task": "everyday", "language": "el"})
        errors = [{"trajectory_id": f"P{i}", "kind": "P", "depth": 1, "depth_bin": "early",
                   "prefix_sha256": f"p{i}", "task": "math", "language": "en"} for i in range(10)]
        chosen, receipt = select.allocate_points({"C": controls, "P": errors, "R": []}, 14)
        self.assertEqual(len([p for p in chosen if p["kind"] == "C"]), 4)
        records = [r for r in receipt["redistributions"] if r["reason"] == "control_depth_quota_recompute"]
        self.assertEqual(len(records), 1)
        self.assertNotEqual(records[0]["old_quota"], records[0]["new_quota"])

    def test_candidates_share_prefix_and_force_n_one(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_state(root, "measurement", "ME001", 8)
            prefix = [{"role": "user", "content": "q"}]
            append_jsonl(root / "measurement" / "selection.jsonl", {
                "selection_id": "SEL001", "trajectory_id": "ME001", "kind": "C", "depth": 1,
                "prefix_messages": prefix, "prefix_sha256": sha256_json(prefix), "original_response": "old",
                "inclusion_receipt": {}, "language": "en", "task": "math"})
            fake = FakeTargetClient([target("new 1"), target("new 2")], ["fake-model"])
            candidates.generate_candidates(root, "measurement", fake, "http://offline/v1", "fake-model", CHECKPOINT)
            rows = read_jsonl(root / "measurement" / "candidates.jsonl")
            self.assertEqual(len(rows), 3)
            self.assertEqual(len({r["prefix_sha256"] for r in rows}), 1)
            self.assertTrue(all(call["n"] == 1 for call in fake.calls))

    def test_completion_mask_all_history(self):
        self.assertEqual(export_pairs.completion_only_labels([10, 11, 12], [20, 21]), [-100, -100, -100, 20, 21])

    def test_rank_batch_maps_random_letters_back(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_state(root, "measurement", "ME001", 8)
            prefix = [{"role": "user", "content": "q"}]; ph = sha256_json(prefix)
            append_jsonl(root / "measurement" / "selection.jsonl", {"selection_id": "SEL001", "trajectory_id": "ME001",
                "kind": "C", "depth": 1, "prefix_messages": prefix, "prefix_sha256": ph,
                "original_response": "x", "language": "en", "task": "math", "inclusion_receipt": {}})
            for k in range(3):
                text = f"answer{k}"
                append_jsonl(root / "measurement" / "candidates.jsonl", {"candidate_id": f"SEL001:c{k}",
                    "selection_id": "SEL001", "source": "original" if k == 0 else "new", "text": text,
                    "text_sha256": sha256_text(text), "prefix_sha256": ph, "finish_reason": "stop",
                    "model": "fake", "usage": {}})
            value = {"selection_id": "SEL001", "ranking": ["B", "A", "C"], "ties": [], "unusable": [],
                     "verdicts": {"A": "neutral", "B": "reinforce", "C": "discourage"},
                     "issues": {"A": [], "B": [], "C": ["wrong_main_point"]},
                     "notes": {"A": "ok", "B": "best", "C": "bad"},
                     "best_vs_worst": "clear", "confidence": "high"}
            fake = FakeSolClient([{"rankings": [value]}])
            result = rank.rank_candidates(root, "measurement", fake)
            self.assertEqual(result["written"], 1)
            stored = read_jsonl(root / "measurement" / "rankings.jsonl")[0]
            self.assertEqual(set(stored["ranking_candidate_ids"]), {"SEL001:c0", "SEL001:c1", "SEL001:c2"})

    def _make_export_case(self, root, verdicts, tie_indexes=(), margin="clear"):
        directory = root / "measurement"
        directory.mkdir()
        for name in ("selection.jsonl", "candidates.jsonl", "rankings.jsonl",
                     "preferences.jsonl", "rejected_pairs.jsonl"):
            (directory / name).touch()
        prefix = [{"role": "user", "content": "q"}]
        ph = sha256_json(prefix)
        sid = "SEL001"
        ids = [sid + f":c{k}" for k in range(3)]
        append_jsonl(directory / "selection.jsonl", {"selection_id": sid, "trajectory_id": "T1",
            "kind": "R", "depth": 3, "prefix_messages": prefix, "prefix_sha256": ph,
            "original_response": "x", "language": "en", "task": "everyday", "inclusion_receipt": {}})
        for k, cid in enumerate(ids):
            text = f"answer {k}"
            append_jsonl(directory / "candidates.jsonl", {"candidate_id": cid, "selection_id": sid,
                "source": "original" if k == 0 else "new", "text": text,
                "text_sha256": sha256_text(text), "prefix_sha256": ph,
                "finish_reason": "stop", "model": "fake", "usage": {}})
        append_jsonl(directory / "rankings.jsonl", {"selection_id": sid,
            "ranking_candidate_ids": ids,
            "ties_candidate_ids": [[ids[k] for k in group] for group in tie_indexes],
            "unusable_candidate_ids": [], "verdicts": dict(zip(ids, verdicts)),
            "source_call_id": "call", "rubric_sha16": "abc", "best_vs_worst": margin})
        return directory, ids

    def test_export_keeps_reinforce_over_two_tied_neutrals(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            directory, ids = self._make_export_case(
                root, ["reinforce", "neutral", "neutral"], tie_indexes=((1, 2),),
            )
            self.assertEqual(export_pairs.export(root), {"accepted": 1, "rejected": 0})
            pair = read_jsonl(directory / "preferences.jsonl")[0]
            self.assertEqual(pair["receipt"]["candidate_ids"], [ids[0], ids[2]])

    def test_export_rejects_two_top_tied_reinforce_candidates(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            directory, _ = self._make_export_case(
                root, ["reinforce", "reinforce", "neutral"], tie_indexes=((0, 1),),
            )
            self.assertEqual(export_pairs.export(root), {"accepted": 0, "rejected": 1})
            self.assertEqual(read_jsonl(directory / "rejected_pairs.jsonl")[0]["reason"], "tie")

    def test_export_keeps_clear_reinforce_over_discourage(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            directory, ids = self._make_export_case(root, ["reinforce", "neutral", "discourage"])
            self.assertEqual(export_pairs.export(root), {"accepted": 1, "rejected": 0})
            pair = read_jsonl(directory / "preferences.jsonl")[0]
            self.assertEqual(pair["receipt"]["candidate_ids"], [ids[0], ids[2]])

    def test_export_rejects_all_neutral_as_no_acceptable_chosen(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            directory, _ = self._make_export_case(root, ["neutral", "neutral", "neutral"])
            self.assertEqual(export_pairs.export(root), {"accepted": 0, "rejected": 1})
            self.assertEqual(read_jsonl(directory / "rejected_pairs.jsonl")[0]["reason"],
                             "no_acceptable_chosen")

    def test_export_rejects_top_neutral_even_when_second_is_reinforce(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            directory, _ = self._make_export_case(root, ["neutral", "reinforce", "discourage"])
            self.assertEqual(export_pairs.export(root), {"accepted": 0, "rejected": 1})
            self.assertEqual(read_jsonl(directory / "rejected_pairs.jsonl")[0]["reason"],
                             "no_acceptable_chosen")

    def test_export_requires_clear_margin_and_reruns_byte_identically(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            directory, _ = self._make_export_case(
                root, ["reinforce", "neutral", "discourage"], margin="slight",
            )
            self.assertEqual(export_pairs.export(root), {"accepted": 0, "rejected": 1})
            rejected = read_jsonl(directory / "rejected_pairs.jsonl")[0]
            self.assertEqual(rejected["reason"], "no_substantive_preference")
            first = {name: (directory / name).read_bytes() for name in
                     ("preferences.jsonl", "rejected_pairs.jsonl", "pair_export_receipt.json")}
            self.assertEqual(export_pairs.export(root), {"accepted": 0, "rejected": 1})
            second = {name: (directory / name).read_bytes() for name in first}
            self.assertEqual(first, second)
            summary = read_json(directory / "pair_export_receipt.json")
            self.assertEqual(summary["pair_rule_version"], export_pairs.PAIR_RULE_VERSION)
            global_receipt = read_json(root / "receipt.json")
            self.assertEqual(
                global_receipt["artifacts"]["measurement/rejected_pairs.jsonl"]["pair_rule_version"],
                export_pairs.PAIR_RULE_VERSION,
            )


class CLITests(unittest.TestCase):
    def test_parser_rejects_measurement_three_before_client_construction(self):
        output = io.StringIO()
        argv = ["rollout", "measurement", "--endpoint", "http://offline/v1", "--model", "fake-model",
                "--checkpoint-sha256", CHECKPOINT, "--max-turns", "3"]
        with mock.patch.object(dqd, "HTTPApertusClient") as target_constructor, \
             mock.patch.object(dqd, "with_sol") as sol_constructor, \
             contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            code = dqd.main(argv)
        self.assertEqual(code, 2)
        self.assertIn("measurement rollout horizon must be exactly 8", output.getvalue())
        self.assertTrue(output.getvalue().strip().splitlines()[-1].startswith("DQD_FAIL parse "))
        target_constructor.assert_not_called()
        sol_constructor.assert_not_called()

    def test_parse_failures_end_with_machine_readable_line(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            code = dqd.main([])
        self.assertEqual(code, 2)
        self.assertTrue(output.getvalue().strip().splitlines()[-1].startswith("DQD_FAIL parse "))
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            code = dqd.main(["rollout", "smoke"])
        self.assertEqual(code, 2)
        self.assertTrue(output.getvalue().strip().splitlines()[-1].startswith("DQD_FAIL parse "))


if __name__ == "__main__":
    unittest.main()
