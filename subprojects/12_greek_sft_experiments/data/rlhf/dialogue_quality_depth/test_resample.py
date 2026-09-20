from __future__ import annotations

import pathlib
import tempfile
import unittest

import budget
import dqd
import export_pairs
import rank
import resample
from clients import FakeSolClient, FakeTargetClient, TargetResult
from common import append_jsonl, atomic_json, read_json, read_jsonl, sha256_text
from schemas import Selection, prefix_sha256


CHECKPOINT = "b" * 64


def _config() -> dict:
    return {
        "version": "test", "seed": 9162602,
        "smoke": {"trajectories": 1, "max_assistant_turns": 3},
        "measurement": {"target_trajectories": 1, "admission_sizes": [35, 28, 21, 14],
                        "max_assistant_turns": 8},
        "budget": {
            "max_new_sol_calls": 120,
            "sol_reservations": {
                "smoke": 6, "openings": 10, "user_continuation": 38,
                "annotation": 40, "adjudication": 10, "candidate_review": 8, "repairs": 8,
            },
            "operational_stop_eur": 4, "prime_intellect_total_eur": 5, "reserve_eur": 1,
        },
    }


def _target(text: str) -> TargetResult:
    return TargetResult(text, "stop", "fake-model", {"prompt_tokens": 5, "completion_tokens": 2}, .1)


def _verdicts(*, reinforce: str | None = None, discourage: str | None = None) -> dict:
    values = {letter: "neutral" for letter in rank.RESAMPLE_LETTERS}
    if reinforce:
        values[reinforce] = "reinforce"
    if discourage:
        values[discourage] = "discourage"
    return {
        "ranking": list(rank.RESAMPLE_LETTERS), "ties": [], "unusable": [], "verdicts": values,
        "issues": {letter: [] for letter in rank.RESAMPLE_LETTERS},
        "notes": {letter: f"note {letter}" for letter in rank.RESAMPLE_LETTERS},
        "best_vs_worst": "clear", "confidence": "high",
    }


class ResampleTests(unittest.TestCase):
    def _state(self) -> pathlib.Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = pathlib.Path(temporary.name)
        cfg = _config()
        seed = {
            "trajectory_id": "ME001", "stage": "measurement", "split": "train",
            "instance_hash": "instance", "content_family": "family", "family": "m_arithmetic",
            "task": "math", "language": "el", "difficulty": "routine", "interaction": "followup",
            "attitude": "cooperative", "register": "standard", "max_assistant_turns": 8,
            "fixture": {"content": "visible", "instruction_spec": "answer", "reference": {},
                        "checks": [], "parameters": {}},
        }
        atomic_json(root / "source_config.json", cfg)
        atomic_json(root / "manifest.json", {
            "version": "test", "seed": 9162602, "config": cfg,
            "planned_joint_counts": {}, "seeds": [seed],
        })
        atomic_json(root / "forecast.json", {
            "admission_status": "admitted", "admitted_size": 1,
            "sol_reservations": cfg["budget"]["sol_reservations"],
            "extensions": {"resample": {
                "authorised_by": "owner 2026-09-17", "max_new_sol_calls": 128,
            }},
        })
        atomic_json(root / "receipt.json", {"artifacts": {}})
        directory = root / "measurement"
        directory.mkdir()
        for name in ("selection.jsonl", "candidates.jsonl", "rankings.jsonl", "preferences.jsonl",
                     "rejected_pairs.jsonl", "resample_candidates.jsonl", "resample_rankings.jsonl",
                     "resample_judgments.jsonl"):
            (directory / name).touch()
        messages = [
            {"role": "user", "content": "q1"}, {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "q2"}, {"role": "assistant", "content": "a2"},
        ]
        append_jsonl(directory / "trajectories.jsonl", {
            "trajectory_id": "ME001", "stage": "measurement", "messages": messages,
            "assistant_turns": 2, "terminal_code": "completed",
        })
        prefix = messages[:3]
        append_jsonl(directory / "selection.jsonl", Selection(
            selection_id="SEL001", trajectory_id="ME001", kind="P", depth=2,
            prefix_messages=prefix, prefix_sha256=prefix_sha256(prefix), original_response="a2",
            inclusion_receipt={"origin": "owner-rule"}, language="el", task="math",
        ).to_dict())
        atomic_json(directory / "resample_targets.json", [
            {"trajectory_id": "ME001", "kind": "P", "depth": 2},
        ])
        return root

    def _sample32(self, root: pathlib.Path) -> FakeTargetClient:
        fake = FakeTargetClient([_target(f"fresh {index}") for index in range(1, 33)], ["fake-model"])
        result = resample.sample_responses(
            root, "measurement", root / "measurement" / "resample_targets.json", 32,
            fake, "http://offline/v1", "fake-model", CHECKPOINT,
        )
        self.assertEqual(result["written"], 32)
        return fake

    def test_prefix_identity_n_one_byte_hash_and_restart(self):
        root = self._state()
        first = FakeTargetClient([_target("  exact bytes\nδεδομένα  ")], ["fake-model"])
        fired = {"value": False}

        def crash(point, _selection_id, _sample_index):
            if point == "after_target_completion" and not fired["value"]:
                fired["value"] = True
                raise RuntimeError("injected crash")

        with self.assertRaisesRegex(RuntimeError, "injected crash"):
            resample.sample_responses(
                root, "measurement", root / "measurement" / "resample_targets.json", 4,
                first, "http://offline/v1", "fake-model", CHECKPOINT, crash_hook=crash,
            )
        second = FakeTargetClient([_target(f"fresh {index}") for index in range(2, 5)], ["fake-model"])
        result = resample.sample_responses(
            root, "measurement", root / "measurement" / "resample_targets.json", 4,
            second, "http://offline/v1", "fake-model", CHECKPOINT,
        )
        selections = read_jsonl(root / "measurement" / "selection.jsonl")
        legacy, registered = selections
        self.assertEqual(registered["selection_id"], "RS001")
        self.assertEqual(registered["prefix_messages"], legacy["prefix_messages"])
        self.assertEqual(registered["prefix_sha256"], legacy["prefix_sha256"])
        rows = read_jsonl(root / "measurement" / "resample_candidates.jsonl")
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]["text"], "  exact bytes\nδεδομένα  ")
        self.assertEqual(rows[0]["text_sha256"], sha256_text(rows[0]["text"]))
        self.assertEqual([row["batch_index"] for row in rows], [0, 0, 0, 0])
        self.assertTrue(all(call["n"] == 1 for call in first.calls + second.calls))
        self.assertEqual(result["written"], 4)
        empty = FakeTargetClient([], ["fake-model"])
        replay = resample.sample_responses(
            root, "measurement", root / "measurement" / "resample_targets.json", 4,
            empty, "http://offline/v1", "fake-model", CHECKPOINT,
        )
        self.assertEqual(replay["written"], 0)
        self.assertEqual(empty.calls, [])

    def test_batches_stop_samples_arithmetic_and_lowest_export(self):
        root = self._state()
        target_client = self._sample32(root)
        self.assertEqual(len(target_client.calls), 32)
        sol = FakeSolClient([_verdicts(discourage="D"), _verdicts(reinforce="A")])
        result = resample.judge_resamples(root, "measurement", sol)
        self.assertEqual(result["sol_calls"], 2)
        self.assertEqual(len(sol.calls), 2)
        judgment = read_jsonl(root / "measurement" / "resample_judgments.jsonl")[0]
        self.assertEqual(judgment["batches_judged"], 2)
        self.assertEqual(judgment["samples_needed"], 8)
        rankings = read_jsonl(root / "measurement" / "resample_rankings.jsonl")
        expected_lowest = rankings[0]["letter_to_candidate_id"]["D"]
        self.assertEqual(judgment["lowest_ranked_candidate_id"], expected_lowest)
        self.assertTrue(all(call["prompt"].startswith(rank.RUBRIC) for call in sol.calls))
        self.assertTrue(all("RS001:r" not in call["prompt"] for call in sol.calls))
        replay_sol = FakeSolClient([])
        replay = resample.judge_resamples(root, "measurement", replay_sol)
        self.assertEqual(replay["sol_calls"], 0)
        self.assertEqual(replay_sol.calls, [])
        exported = resample.export_resamples(root, "measurement")
        self.assertEqual(exported, {"accepted": 1, "rejected": 0, "targets": 1})
        pair = read_jsonl(root / "measurement" / "preferences.jsonl")[0]
        candidates = {row["candidate_id"]: row for row in read_jsonl(
            root / "measurement" / "resample_candidates.jsonl")}
        self.assertEqual(pair["chosen"], candidates[judgment["winning_candidate_id"]]["text"])
        self.assertEqual(pair["rejected"], candidates[expected_lowest]["text"])
        self.assertEqual(pair["origin"], "resample")
        self.assertEqual(pair["samples_needed"], 8)
        report = read_json(root / "measurement" / "resample_report.json")
        self.assertEqual(report["aggregate"]["samples_needed_histogram"], {"8": 1})
        tracked = [root / "measurement" / name for name in (
            "preferences.jsonl", "rejected_pairs.jsonl", "resample_report.json",
        )] + [root / "receipt.json"]
        before = {path: path.read_bytes() for path in tracked}
        self.assertEqual(resample.export_resamples(root, "measurement"), exported)
        self.assertEqual({path: path.read_bytes() for path in tracked}, before)
        export_pairs.export(root, "measurement")
        self.assertEqual(
            [row["id"] for row in read_jsonl(root / "measurement" / "preferences.jsonl")],
            ["PAIR-RS001"],
        )

    def test_no_reinforce_at_32(self):
        root = self._state()
        self._sample32(root)
        sol = FakeSolClient([_verdicts(discourage="D") for _ in range(8)])
        resample.judge_resamples(root, "measurement", sol)
        self.assertEqual(len(sol.calls), 8)
        judgment = read_jsonl(root / "measurement" / "resample_judgments.jsonl")[0]
        self.assertEqual(judgment["status"], "no_reinforce_at_32")
        self.assertEqual(judgment["samples_needed"], "no_reinforce_at_32")
        resample.export_resamples(root, "measurement")
        rejected = read_jsonl(root / "measurement" / "rejected_pairs.jsonl")[0]
        self.assertEqual(rejected["reason"], "no_reinforce_at_32")
        report = read_json(root / "measurement" / "resample_report.json")
        self.assertEqual(report["aggregate"]["share_no_reinforce_at_32"], 1.0)

    def test_extension_accounting_is_additive_and_phase_bounded(self):
        root = self._state()
        cfg = read_json(root / "source_config.json")
        cfg["budget"] = {"max_new_sol_calls": 2, "sol_reservations": {"base": 2}}
        atomic_json(root / "source_config.json", cfg)
        atomic_json(root / "forecast.json", {
            "sol_reservations": {"base": 2},
            "extensions": {"resample": {
                "authorised_by": "owner 2026-09-17", "max_new_sol_calls": 2,
            }},
        })
        ledger = budget.CallLedger(root, cfg)
        for index, phase in enumerate(("base", "base", "resample", "resample")):
            call_id = f"call-{index}"
            self.assertIsNone(ledger.reserve(call_id, "sol", phase, {}))
            ledger.finish(call_id, result={"ok": True})
        with self.assertRaises(budget.BudgetExceeded):
            ledger.reserve("call-4", "sol", "resample", {})
        self.assertEqual(ledger.counts()["sol_reserved_attempts"], 4)

    def test_cli_exposes_three_measurement_only_commands(self):
        parsed = dqd.parser().parse_args([
            "resample", "measurement", "--targets", "targets.json", "--max-fresh", "32",
        ])
        self.assertEqual((parsed.command, parsed.stage, parsed.max_fresh), ("resample", "measurement", 32))
        self.assertEqual(dqd.parser().parse_args(["resample-judge", "measurement"]).command,
                         "resample-judge")
        self.assertEqual(dqd.parser().parse_args(["resample-export", "measurement"]).command,
                         "resample-export")


if __name__ == "__main__":
    unittest.main()
