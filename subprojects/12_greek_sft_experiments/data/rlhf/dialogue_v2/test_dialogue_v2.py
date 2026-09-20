"""Offline Stage C gates for dialogue v2 (plan §7). No network, no GPU, no Sol: fakes only.

Run: cd data/rlhf/dialogue_v2 && python3 -m unittest -v test_dialogue_v2
"""
from __future__ import annotations

import copy
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import branch  # noqa: E402
import evaluate  # noqa: E402
import points  # noqa: E402
import rollout  # noqa: E402
import seeds as seeds_module  # noqa: E402
import user_state  # noqa: E402
import views  # noqa: E402
import worlds  # noqa: E402
from clients import AmbiguousTimeout, ContextLimitError, FakeSolClient, FakeTargetClient, TargetResult  # noqa: E402
from common import SUBPROJECT, read_jsonl, sha256_json  # noqa: E402
from contracts import (BRANCH_RANK_SCHEMA, BRANCH_VERIFY_SCHEMA, CONVERSATION_REVIEW_SCHEMA, DEV_TAGS, RESOLVER_SCHEMA,  # noqa: E402
                       TURN_EVAL_SCHEMA, USER_ACTIONS_SCHEMA, USER_DECISION_SCHEMA)
from glossary import Glossary  # noqa: E402

SEEDS = seeds_module.load_all()
GLOSSARY = Glossary.load()


def decision(move="continue", message="Και μετά;", defect=False, same=False, level="none", done=False,
             revealed=(), changes=False, updates=(), misconception="not_applicable", transfer=None):
    return {"perceived_latest_reply": {"defect_present": defect, "defect": "x" if defect else "", "same_defect_as_before": same,
                                       "useful_progress": not defect},
            "move": move, "done": done, "message": "" if done else message, "new_information": "", "trigger": "latest reply",
            "changes_task": changes, "assistance_level": level, "revealed_private_preference_ids": list(revealed),
            "task_progress": "partial", "knowledge_updates": list(updates), "misconception_status": misconception,
            "transfer_attempt": transfer or {"attempted": False, "attempt_text": ""}, "private_note": "n"}


def reply(text="Απάντηση.", finish="stop", prompt_tokens=100):
    return TargetResult(text, finish, "fffoivos/greek-apertus-8b-sft-r4-full",
                        {"prompt_tokens": prompt_tokens, "completion_tokens": 20}, 0.01)


class Harness:
    def __init__(self, testcase: unittest.TestCase, sol_responder, target_responder, horizon=3):
        self.tmp = tempfile.TemporaryDirectory()
        testcase.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.sol = FakeSolClient(sol_responder)
        self.target = FakeTargetClient(target_responder, ["fffoivos/greek-apertus-8b-sft-r4-full"])
        self.ctx = rollout.Context(self.target, self.sol, GLOSSARY, "fake", dry_run=True, runtime_override=self.root,
                                   horizon=horizon)

    def run(self, case_ids):
        return rollout.collect(self.ctx, SEEDS, case_ids)

    def rows(self, cid, name):
        return [r for r in read_jsonl(self.ctx.runtime(cid) / name) if r.get("case_id") == cid]


def scripted_sol(script):
    """script: dict schema-name -> callable(prompt) -> result"""
    names = {id(USER_DECISION_SCHEMA): "user", id(USER_ACTIONS_SCHEMA): "actions", id(RESOLVER_SCHEMA): "resolver",
             id(TURN_EVAL_SCHEMA): "turn_eval", id(CONVERSATION_REVIEW_SCHEMA): "review", id(BRANCH_RANK_SCHEMA): "rank",
             id(BRANCH_VERIFY_SCHEMA): "verify"}

    def responder(prompt, schema):
        return script[names[id(schema)]](prompt)
    return responder


class Gate1AccessSeparation(unittest.TestCase):
    def test_user_and_learner_views_hold_no_evaluator_or_world_secrets(self):
        for cid, seed in SEEDS.items():
            state = user_state.init_state(seed)
            messages = [{"role": "user", "content": seed["opening"]}, {"role": "assistant", "content": "…"}]
            prompt = views.user_prompt(GLOSSARY, seed, views.user_view(seed, state, messages, "next_turn", []))
            forbidden = views.evaluator_only_strings(seed) + views.unrevealed_observation_strings(seed, state)
            self.assertEqual(views.find_leaks(prompt, forbidden), [], cid)
            self.assertFalse(views.transfer_answer_leak(seed, prompt), cid)
            self.assertNotIn("evaluator_reference", prompt, cid)
            self.assertNotIn("root_cause", prompt, cid)
            if seed.get("world"):
                aprompt = views.actions_prompt(GLOSSARY, seed, views.actions_view(seed, state, messages))
                self.assertEqual(views.find_leaks(aprompt, forbidden), [], cid)
                self.assertNotIn("Home-Guest", aprompt) if cid == "RGD003" else None

    def test_rollout_sends_apertus_only_the_public_conversation(self):
        def user(prompt):
            return decision("clarify", "Εντάξει, και τι άλλο;") if "troubleshooting" in prompt else decision("continue", "Συνέχισε.")
        sol = scripted_sol({"user": user, "actions": lambda p: {"actions": [], "skipped_suggestions": []}})
        h = Harness(self, sol, lambda m: reply(), horizon=2)
        h.run(sorted(SEEDS))
        self.assertTrue(h.target.calls)
        for call in h.target.calls:
            for i, message in enumerate(call["messages"]):
                self.assertEqual(set(message), {"role", "content"})
                self.assertEqual(message["role"], "user" if i % 2 == 0 else "assistant")
            seed = next(s for s in SEEDS.values() if s["opening"] == call["messages"][0]["content"])
            self.assertEqual(views.find_leaks(json.dumps(call["messages"], ensure_ascii=False), views.apertus_private_strings(seed)), [])
            self.assertEqual(call["max_tokens"], 1024)
        for sent in h.sol.calls:
            if sent["schema"] is USER_DECISION_SCHEMA:
                seed = next(s for s in SEEDS.values() if json.dumps(s["opening"], ensure_ascii=False)[1:-1][:60] in sent["prompt"])
                self.assertEqual(views.find_leaks(sent["prompt"], views.evaluator_only_strings(seed)), [])

    def test_learner_view_has_transfer_question_but_never_the_answer(self):
        seed = SEEDS["RGD005"]
        view = views.user_view(seed, user_state.init_state(seed), [{"role": "user", "content": seed["opening"]}], "next_turn")
        text = json.dumps(view, ensure_ascii=False)
        self.assertIn(seed["learner"]["transfer_question"], text)
        for secret in seed["evaluator_reference"]["subject_knowledge"] + [seed["evaluator_reference"]["transfer_check"]["what_to_check"]]:
            self.assertNotIn(secret, text)
        self.assertNotIn("transfer_check", text)


class Gate2WorldConsistency(unittest.TestCase):
    def test_observations_are_deterministic_and_state_changes_persist(self):
        world = SEEDS["RGD003"]["world"]
        state = worlds.initial_state(world)
        first, state, _ = worlds.apply_check(world, state, "add_printer_search")
        again, state, _ = worlds.apply_check(world, state, "add_printer_search")
        self.assertEqual(first, again)
        self.assertIn("finds no printers", first)
        _, state, _ = worlds.apply_check(world, state, "restart_router")
        self.assertIn("finds no printers", worlds.apply_check(world, state, "add_printer_search")[0])
        _, state, _ = worlds.apply_check(world, state, "printer_join_home")
        self.assertIn("finds 'PrintPro 300'", worlds.apply_check(world, state, "add_printer_search")[0])
        self.assertIn("SSID): Home;", worlds.apply_check(world, state, "printer_network_report")[0])
        for seed in SEEDS.values():
            if seed.get("world"):
                self.assertEqual(worlds.validate_world(seed["world"]), [])

    def test_revealed_observations_accumulate_append_only_and_unresolved_is_never_success(self):
        plan = {1: [("print the network page", "printer_network_report")], 2: [("do a secret factory trick", "")],
                3: [("join the printer to Home", "printer_join_home"), ("search again", "add_printer_search")]}
        turn = {"n": 0}

        def actions(prompt):
            turn["n"] += 1
            return {"actions": [{"action": a, "from_assistant_suggestion": True, "why_plausible_for_this_user": "simple"}
                                for a, _ in plan[turn["n"]]], "skipped_suggestions": []}

        def resolver(prompt):
            return {"resolutions": [{"action_index": i, "check_id": c, "status": "supported" if c else "unresolved", "reason": "r"}
                                    for i, (_, c) in enumerate(plan[turn["n"]])]}
        sol = scripted_sol({"actions": actions, "resolver": resolver, "user": lambda p: decision("clarify", "Αυτό είδα.")})
        h = Harness(self, sol, lambda m: reply(), horizon=4)
        h.run(["RGD003"])
        events = h.rows("RGD003", "world_events.jsonl")
        self.assertEqual([e["after_assistant_turn"] for e in events], [1, 2, 3])
        self.assertEqual(events[1]["observations"][0]["status"], "unresolved")
        self.assertEqual(events[1]["observations"][0]["observation"], worlds.UNRESOLVED_OBSERVATION)
        self.assertEqual(events[2]["world_state_after"]["printer_network"], "Home")
        snaps = [r["state"]["observations_obtained"] for r in h.rows("RGD003", "user_state_snapshots.jsonl") if r["row_id"].endswith("next_turn")]
        for earlier, later in zip(snaps, snaps[1:]):
            self.assertEqual(later[:len(earlier)], earlier)
        self.assertIn("SSID): Home-Guest", snaps[0][0]["observation"])


class Gate1ResolverReasonNeverReachesUser(unittest.TestCase):
    def test_unresolved_resolver_reason_is_absent_from_later_user_and_actions_prompts(self):
        secret = "SECRET-REASON printer sits on the isolated guest network; the real fix is joining Home"
        plan = {"n": 0}

        def actions(prompt):
            plan["n"] += 1
            return {"actions": [{"action": "try a special trick", "from_assistant_suggestion": True, "why_plausible_for_this_user": "x"}],
                    "skipped_suggestions": []}
        sol = scripted_sol({"actions": actions,
                            "resolver": lambda p: {"resolutions": [{"action_index": 0, "check_id": "", "status": "unresolved", "reason": secret}]},
                            "user": lambda p: decision("clarify", "Δεν μπόρεσα να το κάνω.")})
        h = Harness(self, sol, lambda m: reply(), horizon=3)
        h.run(["RGD003"])
        user_prompts = [c["prompt"] for c in h.sol.calls if c["schema"] is USER_DECISION_SCHEMA]
        action_prompts = [c["prompt"] for c in h.sol.calls if c["schema"] is USER_ACTIONS_SCHEMA]
        self.assertTrue(user_prompts and len(action_prompts) >= 2)
        for prompt in user_prompts + action_prompts:
            self.assertNotIn("SECRET-REASON", prompt)
        events = h.rows("RGD003", "world_events.jsonl")
        self.assertIn(secret, json.dumps(events[0]["resolutions"], ensure_ascii=False))  # kept for the evaluator view


class Gate9SolFailureRetry(unittest.TestCase):
    def test_failed_sol_call_is_retried_once_and_a_rerun_neither_relabels_nor_duplicates(self):
        state = {"calls": 0}

        def user(prompt):
            state["calls"] += 1
            if state["calls"] == 1:
                return RuntimeError("turn failed: transient")
            return decision("finish", done=True)
        h = Harness(self, scripted_sol({"user": user}), lambda m: reply(), horizon=3)
        h.run(["DVI004"])
        runtime = h.ctx.runtime("DVI004")
        self.assertEqual(rollout.latest_trajectories(runtime)["DVI004"]["ending_reason"], "natural_completion")
        self.assertEqual(state["calls"], 2)
        h.run(["DVI004"])
        self.assertEqual(state["calls"], 2)
        self.assertEqual(rollout.latest_trajectories(runtime)["DVI004"]["ending_reason"], "natural_completion")

    def test_twice_failed_sol_call_ends_as_infrastructure_failure_and_stays_so_on_rerun(self):
        h = Harness(self, scripted_sol({"user": lambda p: RuntimeError("turn failed")}), lambda m: reply(), horizon=3)
        h.run(["DVI004"])
        runtime = h.ctx.runtime("DVI004")
        self.assertEqual(rollout.latest_trajectories(runtime)["DVI004"]["ending_reason"], "infrastructure_failure")
        calls = len(h.sol.calls)
        h.run(["DVI004"])
        self.assertEqual(len(h.sol.calls), calls)
        self.assertEqual(rollout.latest_trajectories(runtime)["DVI004"]["ending_reason"], "infrastructure_failure")


class Gate3HiddenPreferences(unittest.TestCase):
    def test_hidden_preference_is_undisclosed_before_reveal_and_new_after(self):
        responses = iter([decision("point_to_defect", "Πιο απλό, 50–80 λέξεις.", defect=True, level="pointed_defect",
                                   revealed=["P2"], changes=True),
                          decision("finish", done=True)])
        sol = scripted_sol({"user": lambda p: next(responses)})
        h = Harness(self, sol, lambda m: reply(), horizon=3)
        h.run(["RGD001"])
        runtime = h.ctx.runtime("RGD001")
        trajectory = rollout.latest_trajectories(runtime)["RGD001"]
        packets = evaluate.turn_packets(SEEDS["RGD001"], trajectory, runtime)
        p2 = next(p["text"] for p in SEEDS["RGD001"]["user_state"]["private_preferences"] if p["id"] == "P2")
        self.assertIn(p2, packets[0]["undisclosed_preferences_at_this_point"])
        self.assertNotIn(p2, packets[0]["disclosed_preferences_at_this_point"])
        self.assertIn(p2, packets[1]["disclosed_preferences_at_this_point"])
        self.assertEqual(trajectory["ending_reason"], "natural_completion")


class Gate4AdaptiveUser(unittest.TestCase):
    def test_restate_is_not_allowed_twice_and_patience_limits_moves(self):
        seed = SEEDS["DVI001"]
        state = user_state.init_state(seed)
        state, _ = user_state.apply_decision(state, decision("restate", "Ξανά", defect=True, level="restatement"), ["a"], 1)
        allowed, reasons = user_state.allowed_moves(state)
        self.assertNotIn("restate", allowed)
        self.assertIn("give_example", allowed)
        self.assertIn("abandon", allowed)
        state, _ = user_state.apply_decision(state, decision("give_example", "— π.χ.", defect=True, same=True,
                                                             level="partial_scaffold_or_example"), ["a", "b"], 2)
        state, _ = user_state.apply_decision(state, decision("point_to_defect", "Λάθος", defect=True, same=True,
                                                             level="pointed_defect"), ["a", "b", "c"], 3)
        allowed, _ = user_state.allowed_moves(state)
        self.assertEqual(set(allowed), {"accept_partial", "abandon", "finish"})
        low = user_state.init_state(SEEDS["DVI004"])
        self.assertNotIn("give_example", user_state.allowed_moves(low)[0])
        self.assertNotIn("abandon", user_state.allowed_moves(low)[0])

    def test_repeated_restatement_triggers_one_repair_then_strategy_change_is_recorded(self):
        answers = iter([decision("restate", "Ξαναγράψ' το.", defect=True, level="restatement"),
                        decision("restate", "Ξαναγράψ' το πάλι.", defect=True, level="restatement"),
                        decision("give_example", "— Γιατί το κρατάς;\n— Είναι το εισιτήριο της γιαγιάς.", defect=True,
                                 same=True, level="partial_scaffold_or_example"),
                        decision("abandon", done=True, defect=True, same=True)])
        sol = scripted_sol({"user": lambda p: next(answers)})
        h = Harness(self, sol, lambda m: reply(), horizon=4)
        h.run(["DVI001"])
        turns = [r for r in h.rows("DVI001", "user_turns.jsonl") if r["mode"] == "next_turn"]
        self.assertEqual([t["move"] for t in turns], ["restate", "give_example", "abandon"])
        self.assertTrue(turns[1]["repair_used"])
        self.assertIn("sol:user:DVI001:t2:repair1", turns[1]["call_ids"])
        self.assertEqual(rollout.latest_trajectories(h.ctx.runtime("DVI001"))["DVI001"]["ending_reason"], "abandonment")

    def test_user_can_finish_early_without_filling_turns(self):
        sol = scripted_sol({"user": lambda p: decision("finish", done=True)})
        h = Harness(self, sol, lambda m: reply(), horizon=6)
        h.run(["DVI004"])
        trajectory = rollout.latest_trajectories(h.ctx.runtime("DVI004"))["DVI004"]
        self.assertEqual((trajectory["assistant_turns"], trajectory["ending_reason"]), (1, "natural_completion"))


class Gate5ME021(unittest.TestCase):
    def test_me021_history_permits_a_concrete_example_without_reference_leak(self):
        pilot = SUBPROJECT / "data/rlhf/dialogue_quality_depth/runtime"
        rows = [r for r in read_jsonl(pilot / "measurement/trajectories.jsonl") if r["trajectory_id"] == "ME021"]
        history = rows[-1]["messages"][:4]  # opening, reply 1, the recorded restatement, reply 2 (repeats the failure)
        manifest = json.loads((pilot / "manifest.json").read_text(encoding="utf-8"))
        fixture = next(s for s in manifest["seeds"] if s["trajectory_id"] == "ME021")["fixture"]
        seed = copy.deepcopy(SEEDS["DVI001"])
        seed["case_id"], seed["opening"] = "DVI001", history[0]["content"]
        seed["evaluator_reference"] = {"grading_rule": json.dumps(fixture["reference"], ensure_ascii=False) + " (pilot private reference)"}
        state = user_state.init_state(seed)
        state, _ = user_state.apply_decision(state, decision("restate", "…", defect=True, level="restatement"), ["r1"], 1)
        allowed, reasons = user_state.allowed_moves(state)
        self.assertIn("give_example", allowed)
        self.assertNotIn("restate", allowed)  # after an unsuccessful restatement the user changes strategy
        patient = copy.deepcopy(state)
        patient.update({"patience": "high", "tolerance": 4, "consecutive_failed_replies": 3})
        self.assertIn("give_example", user_state.allowed_moves(patient)[0])
        prompt = views.user_prompt(GLOSSARY, seed, views.user_view(seed, state, history, "next_turn"))
        self.assertNotIn("pilot private reference", prompt)
        example = decision("give_example", "Εννοώ κάτι σαν:\n— Γιατί έχεις κυκλώσει αυτά τα φυτά;\n— Αύριο γκρεμίζουν το κτίριο.\nΓράψε μια νέα ιστορία έτσι.",
                           defect=True, same=True, level="partial_scaffold_or_example")
        self.assertEqual(user_state.validate_decision(example, state, allowed, "next_turn", seed), [])
        next_request = views.public_messages(history + [{"role": "user", "content": example["message"]}])
        self.assertNotIn("pilot private reference", json.dumps(next_request, ensure_ascii=False))
        self.assertEqual(next_request[-1]["content"], example["message"])


def _fake_eval(prompt):
    packets = json.loads(prompt.split("PACKETS (JSON):\n", 1)[1])
    out = []
    for p in packets:
        serious = p["case_id"] == "DVI003" and p["judged_assistant_turn"] == 2
        out.append({"packet_id": p["packet_id"], "local_quality": "serious" if serious else "good", "decisive_evidence": "q",
                    "error_summary": "six bullets" if serious else "", "disclosed_constraints_checked": [],
                    "undisclosed_preferences_not_counted": [], "used_latest_guidance": "not_applicable",
                    "retained_earlier_constraints": "yes", "repeats_earlier_failed_reply": False,
                    "factual_or_subject_errors": [], "maths_content": False,
                    "consistent_with_world_or_learner_state": "not_applicable", "meaningful_next_task_exists": True,
                    "needs_human_review": False, "confidence": "high"})
    return {"evaluations": out}


def _fake_review(prompt):
    record = json.loads(prompt.split("CONVERSATION RECORD (JSON):\n", 1)[1])
    return {"user_turns": [{"user_turn_index": u["user_turn_index"], "reacts_to_visible_event": "yes", "reacts_to_real_defect": "yes",
                            "oracle_leak": False, "oracle_leak_evidence": "", "move_label_correct": True, "corrected_move": "",
                            "assistance_level_correct": True, "corrected_assistance_level": "", "genuinely_helpful": True,
                            "consistent_with_user_state": True, "simulator_error": ""}
                           for u in record["user_turn_records"] if u.get("mode") == "next_turn"],
            "world_consistency": {"applicable": False, "consistent": True, "issues": []},
            "learning": {"applicable": False, "progress_supported_by_teaching": False, "transfer_attempted": False,
                         "transfer_attempt_sound": "not_applicable", "sudden_unsupported_expertise": False, "evidence": ""},
            "writing": {"applicable": False, "hidden_preference_treated_as_earlier_instruction": False,
                        "reference_copied_into_conversation": False, "evidence": ""},
            "hidden_information_leaked_to_assistant": False, "leak_evidence": "", "target_errors": [], "simulator_errors": [],
            "ending_reason_agrees": True, "ending_comment": "", "task_result": "completed", "positive_replies_with_incorrect_claims": [],
            "possible_sampling_points": [], "summary": "s"}


class Gate6PrefixBoundaries(unittest.TestCase):
    def test_prevention_and_recovery_boundaries_and_identical_pair_prefix_hashes(self):
        answers = iter([decision("continue", "Τώρα κάν' το για SMS."),
                        decision("point_to_defect", "Έχει έξι κουκκίδες, θέλω πέντε.", defect=True, level="pointed_defect"),
                        decision("finish", done=True)])
        rank_counter = {"n": 0}

        def rank(prompt):
            rank_counter["n"] += 1
            return {"ranking": ["B", "A", "C", "D"], "ties": [], "unusable": [], "verdicts": {"A": "neutral", "B": "reinforce", "C": "neutral", "D": "discourage"},
                    "issues": {L: [] for L in "ABCD"}, "notes": {L: "n" for L in "ABCD"}, "best_vs_worst": "clear", "confidence": "high"}
        verify = lambda p: {"chosen_acceptable": True, "chosen_errors": [], "checkable_constraints": [], "rejected_meaningfully_worse": True,
                            "maths_content": False, "notes": ""}
        sol = scripted_sol({"user": lambda p: next(answers), "turn_eval": _fake_eval, "review": _fake_review, "rank": rank, "verify": verify})
        counter = {"n": 0}

        def target(messages):
            counter["n"] += 1
            return reply(f"reply {counter['n']}")
        h = Harness(self, sol, target, horizon=4)
        h.run(["DVI003"])
        evaluate.evaluate_turns(h.ctx, SEEDS, ["DVI003"])
        evaluate.review_conversations(h.ctx, SEEDS, ["DVI003"])
        summary = points.write_points(SEEDS, ["DVI003"], h.ctx.runtime)
        runtime = h.ctx.runtime("DVI003")
        messages = rollout.latest_trajectories(runtime)["DVI003"]["messages"]
        possible = {p["kind"]: p for p in read_jsonl(runtime / "sampling_points.jsonl")[0]["possible_points"]}
        prevention = possible["prevention"]
        self.assertEqual(prevention["prefix_messages"], messages[:3])
        self.assertEqual(prevention["prefix_messages"][-1]["role"], "user")
        recovery = possible["supported_recovery"]
        self.assertEqual(recovery["prefix_messages"], messages[:5])
        self.assertIn("έξι κουκκίδες", recovery["prefix_messages"][-1]["content"])
        self.assertEqual(recovery["prefix_sha256"], sha256_json(messages[:5]))
        self.assertEqual(len(summary["DVI003"]["selected"]), 2)
        branch.sample_candidates(h.ctx, ["DVI003"])
        branch.judge_points(h.ctx, SEEDS, ["DVI003"])
        pairs = read_jsonl(runtime / "branch_pairs.jsonl")
        self.assertEqual(len(pairs), 2)
        candidates = {c["candidate_id"]: c for c in read_jsonl(runtime / "branch_candidates.jsonl")}
        for pair in pairs:
            self.assertEqual(candidates[pair["chosen_candidate_id"]]["prefix_sha256"], pair["prefix_sha256"])
            self.assertEqual(candidates[pair["rejected_candidate_id"]]["prefix_sha256"], pair["prefix_sha256"])
            self.assertEqual(sha256_json(pair["prefix_messages"]), pair["prefix_sha256"])
            self.assertNotEqual(pair["chosen"], pair["rejected"])
        judged = read_jsonl(runtime / "branch_judgements.jsonl")
        self.assertTrue(all(j["samples_judged"] == 4 for j in judged))
        self.assertEqual(rank_counter["n"], 2)


class Gate7ContextOverflow(unittest.TestCase):
    def test_context_cutoff_is_an_ending_not_a_failure_and_history_is_not_trimmed(self):
        def target(messages):
            if len(messages) >= 5:
                return ContextLimitError("maximum context length is 4096 tokens; requested 1024 output tokens and 3100 input tokens")
            return reply()
        sol = scripted_sol({"user": lambda p: decision("continue", "Και το επόμενο;")})
        h = Harness(self, sol, target, horizon=6)
        h.run(["DVI002"])
        trajectory = rollout.latest_trajectories(h.ctx.runtime("DVI002"))["DVI002"]
        self.assertEqual(trajectory["ending_reason"], "context_cutoff")
        self.assertEqual(len(trajectory["messages"]), 5)
        self.assertEqual(trajectory["messages"][-1]["role"], "user")
        self.assertEqual(len(h.rows("DVI002", "assistant_turns.jsonl")), 2)
        self.assertEqual(h.target.calls[-1]["messages"], trajectory["messages"])


class Gate8DevelopmentOnly(unittest.TestCase):
    def test_every_output_row_is_development_only_and_no_pool_consumer_reads_these_paths(self):
        sol = scripted_sol({"user": lambda p: decision("finish", done=True), "actions": lambda p: {"actions": [], "skipped_suggestions": []}})
        h = Harness(self, sol, lambda m: reply(), horizon=2)
        h.run(sorted(SEEDS))
        for path in h.root.rglob("*.jsonl"):
            if path.name in {"call_ledger.jsonl"}:
                continue
            for row in read_jsonl(path):
                for key, value in DEV_TAGS.items():
                    self.assertEqual(row.get(key), value, f"{path.name}: {key}")
        consumers = ["data/rlhf/inventory.py", "data/rlhf/assemble_round1_pool.py", "data/rlhf/build_pilot_set.py"]
        for rel in consumers:
            source = (SUBPROJECT / rel).read_text(encoding="utf-8")
            self.assertNotIn("dialogue_v2", source, rel)
            self.assertNotIn("reference_guided_dialogue_demo", source, rel)
        for seed in SEEDS.values():
            self.assertEqual(seed["split"], "development")


class Gate9Resumption(unittest.TestCase):
    def test_rerun_replays_completed_calls_and_never_retries_ambiguous_ones(self):
        state = {"timeout": True}

        def target(messages):
            if len(messages) == 3 and state["timeout"]:
                return AmbiguousTimeout("timed out")
            return reply()
        sol = scripted_sol({"user": lambda p: decision("continue", "Επόμενο;")})
        h = Harness(self, sol, target, horizon=3)
        h.run(["DVI004"])
        first_target, first_sol = len(h.target.calls), len(h.sol.calls)
        self.assertEqual(rollout.latest_trajectories(h.ctx.runtime("DVI004"))["DVI004"]["ending_reason"], "ambiguous_timeout")
        state["timeout"] = False
        h.run(["DVI004"])
        self.assertEqual(len(h.target.calls), first_target)
        self.assertEqual(len(h.sol.calls), first_sol)
        self.assertEqual(rollout.latest_trajectories(h.ctx.runtime("DVI004"))["DVI004"]["ending_reason"], "ambiguous_timeout")
        self.assertEqual(len([r for r in h.rows("DVI004", "user_turns.jsonl") if r["mode"] == "next_turn"]), 1)


class Gate10CompletionOnlyExport(unittest.TestCase):
    def test_pairs_declare_completion_only_and_trainer_integration_is_unverified(self):
        self.assertFalse((SUBPROJECT / "cluster" / "dpo_train.py").exists(), "a DPO trainer now exists: inspect its masks")
        source = (HERE / "branch.py").read_text(encoding="utf-8")
        self.assertIn("completion-only", source)
        self.assertIn("trainer integration unverified", source)


class PodRunnerOffline(unittest.TestCase):
    def _env(self, root: pathlib.Path, scenario: str):
        fake = root / "bin"; fake.mkdir()
        runtime = root / "runtime"; (runtime / "pod").mkdir(parents=True)
        events = root / "events.log"
        key = root / "prime.key"; key.write_text("PRIME_SECRET_SENTINEL\n")
        token = root / "hf.token"; token.write_text("HF_SECRET_SENTINEL")
        ssh_key = root / "ssh.key"; ssh_key.write_text("k\n")

        def exe(name, body):
            path = fake / name
            path.write_text(textwrap.dedent(body).lstrip())
            path.chmod(0o755)
        exe("python3", r'''
            #!/usr/bin/env bash
            set -u
            first="${1:-}"
            if [[ "$first" == *dv2_provision.py ]]; then
              action="$2"; state="$3"
              if [[ "$action" == provision ]]; then
                printf '{"pod_id":"fake-pod","ssh_host":"h","ssh_user":"ubuntu","ssh_port":22,"price_hr":0.82,"created_at":1790000000}\n' > "$state"
                echo provision >> "$FAKE_EVENTS"; exit 0
              fi
              rm -f "$state"; echo teardown >> "$FAKE_EVENTS"; echo 'DELETE_CONFIRMED pod_id=fake-pod'; exit 0
            fi
            if [[ "$first" == *dv2.py ]]; then
              case " $* " in
                *" gate "*) [[ "$FAKE_SCENARIO" == gate_fail ]] && { echo 'DV2_FAIL gate {}'; exit 2; }
                            echo 'DV2_OK gate {"max_session_minutes": 30, "price_cap_usd_hr": 1.99}'; exit 0 ;;
                *" gpu-start "*) printf '{"record":"gpu_start","pod_id":"fake-pod","shutdown_deadline_utc":"2099-01-01T00:00:00+00:00"}\n' >> "$DV2_RUNTIME_DIR/gpu_ledger.jsonl"; echo gpu-start >> "$FAKE_EVENTS"; exit 0 ;;
                *" gpu-stop "*) echo gpu-stop >> "$FAKE_EVENTS"; exit 0 ;;
                *" preflight "*) echo preflight >> "$FAKE_EVENTS"; exit 0 ;;
                *" collect "*) echo collect >> "$FAKE_EVENTS"; [[ "$FAKE_SCENARIO" == stage_fail ]] && exit 33; exit 0 ;;
                *" branch-sample "*) echo branch >> "$FAKE_EVENTS"; exit 0 ;;
              esac
            fi
            exec "$REAL_PYTHON" "$@"
        ''')
        exe("ssh", r'''
            #!/usr/bin/env bash
            args=" $* "
            if [[ "$args" == *' -N '* ]]; then exec sleep 300; fi
            if [[ "$args" == *'dv2_pod_setup.sh'* ]]; then
              cat > /dev/null
              [[ "$FAKE_SCENARIO" == setup_fail ]] && { echo 'DV2_SETUP_FAIL code=45 reason=uv_install'; exit 45; }
              echo 'DV2_MODEL_SHA_OK sha256=54d445bc639b7222ad872b4d8dca5e913dbf4c4d427fbf56183e28361006e763'
              echo 'DV2_SERVE_READY model=fffoivos/greek-apertus-8b-sft-r4-full'; exit 0
            fi
            exit 0
        ''')
        exe("scp", "#!/usr/bin/env bash\nexit 0\n")
        exe("curl", "#!/usr/bin/env bash\nprintf '{\"data\":[{\"id\":\"fffoivos/greek-apertus-8b-sft-r4-full\"}]}'\n")
        exe("lsof", "#!/usr/bin/env bash\nexit 1\n")
        env = dict(os.environ)
        env.update({"PATH": f"{fake}{os.pathsep}{env['PATH']}", "REAL_PYTHON": sys.executable, "FAKE_EVENTS": str(events),
                    "FAKE_SCENARIO": scenario, "DV2_RUNTIME_DIR": str(runtime), "DV2_CONTROL_KEY_FILE": str(key),
                    "DV2_HF_TOKEN_FILE": str(token), "DV2_SSH_KEY": str(ssh_key), "DV2_LOG_FILE": str(root / "run.log"),
                    "DV2_LOCAL_PORT": "18999"})
        return env, events, root / "run.log"

    def _run(self, scenario, stage="collect"):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        env, events, log = self._env(pathlib.Path(tmp.name), scenario)
        proc = subprocess.run(["bash", str(HERE / "pod" / "run_stage.sh"), stage], env=env, capture_output=True, text=True, timeout=120)
        return proc, events.read_text().split() if events.exists() else [], log.read_text()

    def test_happy_path_order_and_receipt(self):
        proc, events, log = self._run("happy")
        self.assertEqual(proc.returncode, 0, log[-800:])
        self.assertEqual(events, ["provision", "gpu-start", "preflight", "collect", "teardown", "gpu-stop"])
        self.assertIn("teardown=confirmed", log)
        self.assertNotIn("SECRET_SENTINEL", log)

    def test_failures_always_tear_down_and_gate_failure_never_provisions(self):
        for scenario in ("setup_fail", "stage_fail"):
            proc, events, log = self._run(scenario)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("teardown", events, scenario)
            self.assertEqual(events[-2:], ["teardown", "gpu-stop"], scenario)
            self.assertNotIn("SECRET_SENTINEL", log)
        proc, events, log = self._run("gate_fail")
        self.assertNotEqual(proc.returncode, 0)
        self.assertNotIn("provision", events)

    def test_shell_scripts_parse_and_never_enable_tracing(self):
        for name in ("run_stage.sh", "watchdog.sh", "dv2_pod_setup.sh"):
            path = HERE / "pod" / name
            subprocess.run(["bash", "-n", str(path)], check=True)
            self.assertNotIn("set -x", path.read_text())


if __name__ == "__main__":
    unittest.main()
