"""Regression tests for the CP1 independent review (21 Sept 2026). Each one fails against the code that review read.

seeded.py is exercised with a STUB generator (seeded.GENERATE pointed at a script written here), so nothing calls a model.
"""
import json, os, sqlite3, sys, tempfile, textwrap, unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from rlhf.prompts import PromptBank, BankError, SourceError, QuotaError, DuplicateError, NearDuplicateError, apportion, fill
from rlhf.prompts import seeded, slots as slotlib
from rlhf.prompts.bank import shingle_set, _max_flow

def msg(t): return [{"role": "user", "content": t}]
LONG = ["Πώς υπολογίζεται ο φόρος εισοδήματος για ελεύθερους επαγγελματίες με δύο παιδιά φέτος στην Ελλάδα",
        "Ποια είναι η ετυμολογία της λέξης θάλασσα και από πού προέρχεται ιστορικά στην ελληνική γλώσσα",
        "Θέλω να αλλάξω οθόνη στο κινητό μου μόνος μου, τι εργαλεία χρειάζομαι και τι πρέπει να προσέξω",
        "Μπορείτε να μου εξηγήσετε γιατί ο Άρης φαίνεται κόκκινος στον νυχτερινό ουρανό κάθε καλοκαίρι"]

class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory(); self.path = os.path.join(self.dir.name, "bank.sqlite"); self.bank = PromptBank(self.path)
    def tearDown(self): self.bank.db.close(); self.dir.cleanup()
    def forum(self, i, purpose="factual", language="el"):
        return self.bank.add_source("forum", "https://x.gr/t/%d" % i, forum="f", purpose=purpose, language=language, payload={"i": i}, origin="o")
    def el(self, plan): return [(r["filled"], r["maximum"]) for r in self.bank.coverage(plan) if r["key"] == "el"][0]


class H1_SetStatus(Base):
    def test_approving_a_held_prompt_cannot_overshoot_the_quota(self):
        self.bank.plan("P", 1, shares={"language": {"el": 1}})
        self.bank.submit(self.forum(1), msg(LONG[0]), plan_id="P", run="r", generator="g")
        held = self.bank.submit(self.forum(2), msg(LONG[1]), plan_id="P", run="r", generator="g", status="held")
        with self.assertRaises(QuotaError): self.bank.set_status(held, "active", "reviewer approved")
        self.assertEqual(self.el("P"), (1, 1)); self.assertEqual(self.bank.audit()["quotas_overshot"], [])

    def test_a_rejected_prompt_cannot_be_flipped_back_in(self):
        self.bank.plan("P", 1, shares={"language": {"el": 1}})
        self.bank.submit(self.forum(1), msg(LONG[0]), plan_id="P", run="r", generator="g")
        dead = self.bank.submit(self.forum(2), msg(LONG[1]), plan_id="P", run="r", generator="g", status="rejected")
        with self.assertRaises(BankError): self.bank.set_status(dead, "active", "oops")
        self.assertEqual(self.el("P"), (1, 1))

    def test_a_superseded_prompt_stays_superseded(self):
        old = self.bank.submit(self.forum(1), msg(LONG[0]), run="r", generator="g"); self.bank.supersede(old, msg(LONG[1]), run="r2", generator="g")
        with self.assertRaises(BankError): self.bank.set_status(old, "active", "resurrect")

    def test_approving_a_held_prompt_works_when_there_is_room(self):
        self.bank.plan("P", 1, shares={"language": {"el": 1}})
        held = self.bank.submit(self.forum(1), msg(LONG[0]), plan_id="P", run="r", generator="g", status="held")
        self.bank.set_status(held, "active", "approved"); self.assertEqual(self.el("P"), (1, 1))


class M1_WhatTheSchemaAloneGuarantees(Base):
    """A BARE sqlite3 connection, no PromptBank: what holds here holds for any tool that opens the file."""
    def test_not_null_source_and_one_live_prompt_per_source_hold_for_any_connection(self):
        a = self.forum(1); self.bank.submit(a, msg(LONG[0]), run="r", generator="g")
        raw = sqlite3.connect(self.path)
        with self.assertRaises(sqlite3.IntegrityError):
            raw.execute("INSERT INTO prompts VALUES ('p:n',NULL,NULL,'s1','[]',1,'forum','f','factual','el','active',NULL,NULL,'g','r','{}',0)")
        with self.assertRaises(sqlite3.IntegrityError):
            raw.execute("INSERT INTO prompts VALUES ('p:m',?,NULL,'s2','[]',1,'forum','f','factual','el','active',NULL,NULL,'g','r','{}',0)", (a,))
        raw.close()

    def test_a_bare_connection_can_orphan_a_prompt_and_audit_says_so(self):
        raw = sqlite3.connect(self.path)
        raw.execute("INSERT INTO prompts VALUES ('p:o','forum:ghost',NULL,'s3','[]',1,'forum','f','factual','el','active',NULL,NULL,'g','r','{}',0)"); raw.commit(); raw.close()
        a = self.bank.audit(); self.assertEqual((a["foreign_key_violations"], a["prompts_without_source"]), (1, 1))


class M2_JointFeasibility(Base):
    def test_a_dead_end_created_by_greedy_claiming_is_reported(self):
        self.forum(1, "everyday", "el"); self.forum(2, "math", "el"); self.forum(3, "everyday", "en")
        self.bank.plan("P", 2, shares={"purpose": {"everyday": 1, "math": 1}, "language": {"el": 1, "en": 1}})
        self.assertEqual(self.bank.feasibility("P"), [])                       # attainable: (math,el)+(everyday,en)
        everyday_el = [s for s in (self.bank.claim("P", "forum", worker="w", purpose="everyday", language="el"),)][0]
        self.bank.submit(everyday_el["source_id"], msg(LONG[0]), plan_id="P", run="r", generator="g")
        f = self.bank.feasibility("P")                                         # what is left, (everyday,en)+(math,el), fits nowhere
        self.assertEqual([r["short_by"] for r in f if "joint" in r["dimension"]], [1])

    def test_max_flow(self):
        self.assertEqual(_max_flow({"a": 1, "b": 1}, {"x": 1, "y": 1}, {("a", "x"): 5, ("b", "x"): 5}), 1)
        self.assertEqual(_max_flow({"a": 1, "b": 1}, {"x": 1, "y": 1}, {("a", "x"): 1, ("b", "y"): 1}), 2)


class M3_NearDuplicates(Base):
    def test_stripping_the_accents_does_not_launder_a_duplicate(self):
        import unicodedata
        bare = "".join(c for c in unicodedata.normalize("NFD", LONG[0]) if not unicodedata.combining(c))
        self.bank.submit(self.forum(1), msg(LONG[0]), run="r", generator="g")
        with self.assertRaises(NearDuplicateError): self.bank.submit(self.forum(2), msg(bare), run="r", generator="g")

    def test_short_prompts_are_compared_by_characters_not_all_or_nothing(self):
        self.bank.submit(self.forum(1), msg("Τι ώρα είναι"), run="r", generator="g")
        with self.assertRaises(NearDuplicateError): self.bank.submit(self.forum(2), msg("Τι ώρα είναι τώρα"), run="r", generator="g")
        self.bank.submit(self.forum(3), msg("Πού είναι το φαρμακείο"), run="r", generator="g")     # a different short prompt is fine

    def test_prompts_without_user_text_do_not_share_one_bucket(self):
        a = shingle_set([{"role": "assistant", "content": "Γεια σας"}]); b = shingle_set([{"role": "assistant", "content": "Καλημέρα"}])
        self.assertFalse(a & b)


class M6_M9_SourceStates(Base):
    def test_a_consumed_source_does_not_take_a_fresh_live_prompt(self):
        a = self.forum(1); p = self.bank.submit(a, msg(LONG[0]), run="r", generator="g"); self.bank.set_status(p, "archived", "old round")
        with self.assertRaises(SourceError): self.bank.submit(a, msg(LONG[1]), run="r2", generator="g")

    def test_recording_history_does_not_burn_a_fresh_source(self):
        a = self.forum(1); self.bank.submit(a, msg(LONG[0]), run="r", generator="g", status="archived")
        self.assertEqual(self.bank.source(a)["state"], "available")


class L1_Apportion(unittest.TestCase):
    def test_bad_weights_are_refused_as_bank_errors(self):
        for bad in ({"a": 5, "b": -1}, {"a": float("nan")}, {"a": float("inf"), "b": 1}, {"a": 0, "b": 0}):
            with self.assertRaises(BankError): apportion(10, bad)
        self.assertEqual(apportion(2, {"a": 1, "b": 1, "c": 1, "d": 1}), {"a": 1, "b": 1, "c": 0, "d": 0})


class L5_FillProbe(Base):
    def test_fill_leaves_nothing_claimed(self):
        for i in range(5): self.bank.add_source("forum", "https://x.gr/p/%d" % i, forum="f", purpose="factual", language="el", origin="o", payload={"prompt_el": LONG[i % 4] + " αριθμός %d" % i + " κάτι" * (3 * i)})
        self.bank.plan("P", 2, shares={"language": {"el": 1}}); fill(self.bank, "P", "forum", 2, run="r", generator="g")
        self.assertEqual(self.bank.db.execute("SELECT COUNT(*) FROM sources WHERE state='claimed'").fetchone()[0], 0)


T = {"within_seeded_defaults_percent": {"difficulty": {"routine": 30, "compositional": 50, "challenging": 20}, "attitude": {"cooperative": 70, "frustrated": 10, "skeptical": 15, "playful": 5},
                                          "register": {"standard": 60, "informal": 20, "formal": 15, "greeklish": 5}}}
NEEDS = [("seed", "everyday", "el"), ("seed", "math", "en"), ("dialogue", "dialogue", "el"), ("seed", "safety", "fr"), ("dialogue", "dialogue", "en")]

class Slots(Base):
    def test_build_is_deterministic_and_registers_one_source_per_need(self):
        ids = slotlib.build(self.bank, NEEDS, prefix="T1", seed=7, target=T); self.assertEqual(len(set(ids)), len(NEEDS))
        other = PromptBank(os.path.join(self.dir.name, "two.sqlite")); self.assertEqual(slotlib.build(other, NEEDS, prefix="T1", seed=7, target=T), ids); other.db.close()
        kinds = [self.bank.source(i)["kind"] for i in ids]; self.assertEqual(kinds, [k for k, _, _ in NEEDS])
        self.assertEqual([self.bank.source(i)["purpose"] for i in ids], [p for _, p, _ in NEEDS])

    def test_the_run_label_is_not_part_of_a_seeds_identity(self):
        """CP1 M5: the same seed under a new experiment prefix used to be a brand-new source."""
        a = slotlib.build(self.bank, NEEDS[:1], prefix="E1", seed=7, target=T); n = self.bank.db.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        clone = dict(self.bank.source(a[0])["payload"], slot_id="E9-S01"); key = json.dumps({k: v for k, v in clone.items() if k != "slot_id"}, ensure_ascii=False, sort_keys=True)
        b = self.bank.add_source("seed", key, purpose="everyday", language="el", payload=clone, origin="again")
        self.assertEqual(b, a[0]); self.assertEqual(self.bank.db.execute("SELECT COUNT(*) FROM sources").fetchone()[0], n)

    def test_labels_are_compatible_and_triples_never_repeat(self):
        ids = slotlib.build(self.bank, NEEDS * 8, prefix="T2", seed=3, target=T); slots_ = [self.bank.source(i)["payload"] for i in ids]
        for s in slots_:
            self.assertFalse(s["register"] == "greeklish" and s["language"] != "el"); self.assertFalse(s["packet"] and s["detail"] == "short")
        self.assertEqual(len({(s["person"], s["situation"], s["topic"]) for s in slots_}), len(slots_))
        self.assertEqual(len({s["slot_id"] for s in slots_}), len(slots_))

    def test_least_used_first(self):
        slotlib.build(self.bank, [("seed", "everyday", "de")] * 30, prefix="T3", seed=1, target=T)      # people_de has 30 entries
        people = [self.bank.source(r[0])["payload"]["person"] for r in self.bank.db.execute("SELECT source_id FROM sources")]
        self.assertEqual(len(set(people)), 30)                                                           # each used once before any is used twice


STUB = textwrap.dedent('''
    import argparse, json, pathlib, sys
    ap = argparse.ArgumentParser()
    for f in ("--run", "--manifest", "--slots", "--registry", "--runs-dir", "--workers"): ap.add_argument(f)
    ap.add_argument("--fake", action="store_true"); a = ap.parse_args()
    mode = pathlib.Path(a.manifest).parent.joinpath("MODE").read_text().strip()
    if mode == "crash": sys.exit(3)
    out = pathlib.Path(a.runs_dir) / a.run; out.mkdir(parents=True, exist_ok=True); rows = []
    for i, s in enumerate(json.load(open(a.manifest))["slots"]):
        held = (mode == "allheld") or (mode == "mixed" and i % 2 == 1 and a.run.endswith("r1"))
        if mode == "partial" and i % 2 == 1: continue
        text = "Ερώτηση για %s σχετικά με %s, περίπτωση %s, με αρκετές λέξεις ώστε να μετρά κανονικά" % (s["person"][:30], s["topic"], s["slot_id"])
        rows.append(dict(slot_id=s["slot_id"], status="held" if held else "active", held_reasons=["review"] if held else [], purpose=s["purpose"], subtype=s["subtype"],
                         messages=None if held else ("{not json" if mode == "badjson" else json.dumps([{"role": "user", "content": text}])), generator_version="0.2"))
    open(out / "prompts.jsonl", "w").write("".join(json.dumps(r, ensure_ascii=False) + "\\n" for r in rows))
    json.dump({"sol_calls": {"instance": 1}}, open(out / "receipt.json", "w"))
''')

class Seeded(Base):
    def setUp(self):
        super().setUp(); self.work = os.path.join(self.dir.name, "gen"); os.makedirs(self.work)
        self.stub = os.path.join(self.dir.name, "stub_generate.py"); open(self.stub, "w").write(STUB)
        self.legacy = os.path.join(self.dir.name, "legacy.sqlite"); sqlite3.connect(self.legacy).close()
        self._gen = seeded.GENERATE; seeded.GENERATE = self.stub
        slotlib.build(self.bank, [("seed", "everyday", "el")] * 6, prefix="S", seed=5, target=T); self.bank.plan("P", 6, shares={"language": {"el": 1}})
    def tearDown(self): seeded.GENERATE = self._gen; super().tearDown()
    def run_mode(self, mode, **kw):
        open(os.path.join(self.work, "MODE"), "w").write(mode)
        return seeded.generate_into(self.bank, "P", "seed", 6, run="T", workdir=self.work, legacy_registry=self.legacy, prior_runs=[], max_rounds=2, **kw)
    def states(self): return dict(self.bank.db.execute("SELECT state, COUNT(*) FROM sources GROUP BY 1").fetchall())

    def test_every_slot_becomes_a_prompt_traced_to_its_slot(self):
        r = self.run_mode("ok"); self.assertEqual((r["registered_active"], r["generator_hold_rate"]), (6, 0.0)); self.assertEqual(self.states(), {"consumed": 6})
        lin = self.bank.lineage(r["prompt_ids"][0]); self.assertEqual(lin["prompt"]["labels"]["slot_id"], lin["source"]["payload"]["slot_id"])

    def test_malformed_generator_output_strands_nothing(self):
        """CP1 H2: this left all six sources 'claimed', reserving six places in the plan for ever."""
        with self.assertRaises(Exception): self.run_mode("badjson")
        self.assertNotIn("claimed", self.states()); self.assertEqual(self.bank.audit()["stale_claims_older_than_a_day"], 0)

    def test_a_crashed_generator_strands_nothing(self):
        with self.assertRaises(RuntimeError): self.run_mode("crash")
        self.assertEqual(self.states(), {"available": 6})

    def test_the_hold_rate_is_the_generators_not_a_constant_zero(self):
        """CP1 H3: computed from registered-held prompts it was 0.0 by construction, so the plan's failure gate could never fire."""
        r = self.run_mode("allheld"); self.assertEqual((r["registered_active"], r["generator_held"], r["slots_issued_to_generator"], r["generator_hold_rate"]), (0, 12, 12, 1.0))
        self.assertEqual(self.states(), {"rejected": 6})

    def test_a_held_slot_is_retried_before_it_is_spent(self):
        r = self.run_mode("mixed"); self.assertEqual(r["registered_active"], 6); self.assertEqual(r["skipped"], {"held_then_retried": 3}); self.assertEqual(self.states(), {"consumed": 6})

    def test_a_slot_the_generator_skipped_is_spent_with_a_reason(self):
        r = self.run_mode("partial"); self.assertEqual((r["registered_active"], r["skipped"]["no_prompt"] >= 3), (3, True)); self.assertNotIn("claimed", self.states())


class ReleaseStale(Base):
    def test_abandoned_claims_can_be_given_back(self):
        self.forum(1); self.bank.plan("P", 1, shares={"language": {"el": 1}}); s = self.bank.claim("P", "forum", worker="dead")
        self.assertEqual(self.bank.release_stale(older_than_seconds=3600), [])
        self.assertEqual(self.bank.release_stale(older_than_seconds=-1), [s["source_id"]]); self.assertIsNotNone(self.bank.claim("P", "forum", worker="alive"))


if __name__ == "__main__": unittest.main()
