"""The bank's guarantees, attacked. Most of these tests try to do the wrong thing and require a refusal.

Several go AROUND the API with raw SQL on purpose. The registry this replaces was correct only because
its import script was careful; a guarantee that holds only when callers behave is not a guarantee.
"""
import os, sqlite3, sys, tempfile, threading, unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from rlhf.prompts import (fill, ingest_seeds, ingest_forum_gate, PromptBank, SourceError, QuotaError, DuplicateError, NearDuplicateError, apportion, source_id_for)

def msg(text): return [{"role": "user", "content": text}]

TEXTS = ["Πώς υπολογίζεται ο φόρος εισοδήματος για ελεύθερους επαγγελματίες με δύο παιδιά φέτος",
         "Ποια είναι η ετυμολογία της λέξης θάλασσα και από πού προέρχεται ιστορικά στην ελληνική",
         "Θέλω να αλλάξω οθόνη στο κινητό μου μόνος μου, τι εργαλεία χρειάζομαι και τι να προσέξω",
         "Μπορείτε να μου εξηγήσετε γιατί ο Άρης φαίνεται κόκκινος στον νυχτερινό ουρανό το καλοκαίρι",
         "Γράψε μου μια σύντομη επιστολή παραπόνων προς τον δήμο για τα σκουπίδια στη γειτονιά μας",
         "Τι διαφορά έχει ο αόριστος από τον παρακείμενο και πότε χρησιμοποιούμε τον καθένα σωστά"]

class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory(); self.path = os.path.join(self.dir.name, "bank.sqlite")
        self.bank = PromptBank(self.path)
    def tearDown(self): self.bank.db.close(); self.dir.cleanup()
    def forum(self, i, forum="lexilogia", purpose="factual"):
        return self.bank.add_source("forum", "https://x.gr/t/%d" % i, forum=forum, purpose=purpose, language="el",
                                    payload={"i": i}, origin="forum-gate-v3")
    def seed(self, i, purpose="everyday", language="el"):
        return self.bank.add_source("seed", '{"slot": %d}' % i, purpose=purpose, language=language, payload={"slot": i}, origin="gen-0.2")


class Provenance(Base):
    def test_a_prompt_needs_a_registered_source(self):
        with self.assertRaises(SourceError): self.bank.submit("forum:doesnotexist", msg(TEXTS[0]), run="r", generator="g")

    def test_raw_sql_cannot_insert_a_prompt_with_no_source(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.bank.db.execute("INSERT INTO prompts VALUES ('p:x',NULL,NULL,'sha','[]',1,'forum',NULL,'factual','el','active',NULL,NULL,'g','r','{}',0)")

    def test_raw_sql_cannot_point_a_prompt_at_a_missing_source(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.bank.db.execute("INSERT INTO prompts VALUES ('p:x','forum:ghost',NULL,'sha','[]',1,'forum',NULL,'factual','el','active',NULL,NULL,'g','r','{}',0)")

    def test_a_second_connection_is_held_to_the_same_rules(self):
        other = PromptBank(self.path)
        with self.assertRaises(sqlite3.IntegrityError):
            other.db.execute("INSERT INTO prompts VALUES ('p:y','seed:ghost',NULL,'sha2','[]',1,'seed',NULL,'factual','el','active',NULL,NULL,'g','r','{}',0)")
        other.db.close()

    def test_lineage_returns_the_source_verbatim(self):
        s = self.forum(7); p = self.bank.submit(s, msg(TEXTS[0]), run="r", generator="g")
        lin = self.bank.lineage(p)
        self.assertEqual(lin["source"]["natural_key"], "https://x.gr/t/7"); self.assertEqual(lin["source"]["payload"], {"i": 7})
        self.bank.alias("R4-0001", p); self.assertEqual(self.bank.lineage("R4-0001")["prompt"]["prompt_id"], p)

    def test_a_forum_source_must_name_its_forum_and_a_seed_must_not(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.bank.add_source("forum", "https://x.gr/none", purpose="factual", language="el", payload={}, origin="o")
        with self.assertRaises(sqlite3.IntegrityError):
            self.bank.add_source("seed", "{}", forum="lexilogia", purpose="factual", language="el", payload={}, origin="o")


class NoDuplicates(Base):
    def test_the_same_url_is_one_source_however_often_it_is_added(self):
        a = self.forum(1); b = self.forum(1)
        self.assertEqual(a, b); self.assertEqual(a, source_id_for("forum", "https://x.gr/t/1"))
        self.assertEqual(self.bank.db.execute("SELECT COUNT(*) FROM sources").fetchone()[0], 1)

    def test_a_used_source_is_never_handed_out_again(self):
        self.forum(1); self.bank.plan("P", 5, shares={"language": {"el": 1}})
        s = self.bank.claim("P", "forum", worker="w"); self.bank.submit(s["source_id"], msg(TEXTS[0]), plan_id="P", run="r", generator="g")
        self.assertIsNone(self.bank.claim("P", "forum", worker="w"))

    def test_two_workers_cannot_claim_the_same_source(self):
        for i in range(8): self.forum(i)
        self.bank.plan("P", 8, shares={"language": {"el": 1}}); got, lock = [], threading.Lock()
        def work(n):
            b = PromptBank(self.path)
            while True:
                s = b.claim("P", "forum", worker="w%d" % n)
                if s is None: break
                with lock: got.append(s["source_id"])
            b.db.close()
        ts = [threading.Thread(target=work, args=(n,)) for n in range(4)]
        [t.start() for t in ts]; [t.join() for t in ts]
        self.assertEqual(len(got), 8); self.assertEqual(len(set(got)), 8)

    def test_identical_text_is_refused_even_from_a_different_source(self):
        a, b = self.forum(1), self.forum(2); first = self.bank.submit(a, msg(TEXTS[0]), run="r", generator="g")
        with self.assertRaises(DuplicateError) as cm: self.bank.submit(b, msg("  " + TEXTS[0].replace(" ", "   ") + " "), run="r", generator="g")
        self.assertEqual(cm.exception.existing, first)

    def test_a_near_duplicate_is_refused_and_names_what_it_collides_with(self):
        a, b = self.forum(1), self.forum(2); first = self.bank.submit(a, msg(TEXTS[0]), run="r", generator="g")
        with self.assertRaises(NearDuplicateError) as cm: self.bank.submit(b, msg(TEXTS[0] + " παρακαλώ"), run="r", generator="g")
        self.assertEqual(cm.exception.existing, first); self.assertGreaterEqual(cm.exception.similarity, 0.5)
        self.assertEqual(self.bank.source(b)["state"], "available")          # the refused submit consumed nothing

    def test_different_prompts_are_not_called_duplicates(self):
        for i, t in enumerate(TEXTS): self.bank.submit(self.forum(i), msg(t), run="r", generator="g")
        self.assertEqual(self.bank.stats()["prompts"][("forum", "active")], len(TEXTS))

    def test_one_source_cannot_carry_two_live_prompts(self):
        a = self.forum(1); self.bank.submit(a, msg(TEXTS[0]), run="r", generator="g")
        with self.assertRaises(SourceError): self.bank.submit(a, msg(TEXTS[1]), run="r", generator="g")

    def test_raw_sql_cannot_give_a_source_two_live_prompts_either(self):
        a = self.forum(1); self.bank.submit(a, msg(TEXTS[0]), run="r", generator="g")
        with self.assertRaises(sqlite3.IntegrityError):
            self.bank.db.execute("INSERT INTO prompts VALUES ('p:z',?,NULL,'othersha','[]',1,'forum','lexilogia','factual','el','active',NULL,NULL,'g','r','{}',0)", (a,))

    def test_a_retry_supersedes_and_may_resemble_what_it_replaces(self):
        a = self.forum(1); old = self.bank.submit(a, msg(TEXTS[0]), run="r1", generator="g")
        new = self.bank.supersede(old, msg(TEXTS[0] + " σε απλά ελληνικά"), run="r2", generator="g")
        hist = {h["prompt_id"]: h["status"] for h in self.bank.lineage(new)["attempts_on_this_source"]}
        self.assertEqual(hist, {old: "superseded", new: "active"}); self.assertEqual(self.bank.lineage(new)["prompt"]["supersedes"], old)

    def test_a_failed_retry_leaves_the_old_prompt_live(self):
        a, b = self.forum(1), self.forum(2)
        old = self.bank.submit(a, msg(TEXTS[0]), run="r", generator="g"); self.bank.submit(b, msg(TEXTS[1]), run="r", generator="g")
        with self.assertRaises(DuplicateError): self.bank.supersede(old, msg(TEXTS[1]), run="r2", generator="g")
        self.assertEqual(self.bank.lineage(old)["prompt"]["status"], "active")

    def test_a_rejected_source_is_not_offered(self):
        a = self.forum(1); self.bank.reject_source(a, "advertisement"); self.bank.plan("P", 3, shares={"language": {"el": 1}})
        self.assertIsNone(self.bank.claim("P", "forum", worker="w"))
        with self.assertRaises(SourceError): self.bank.submit(a, msg(TEXTS[0]), run="r", generator="g")


class Distribution(Base):
    def test_quotas_sum_to_n_exactly(self):
        for n in (1, 7, 100, 333, 500, 1001):
            q = apportion(n, {"dialogue": 35, "everyday": 25, "instruction": 15, "factual": 10, "safety": 10, "math": 5})
            self.assertEqual(sum(q.values()), n)
        self.assertEqual(apportion(100, {"el": 70, "en": 20, "fr": 2, "de": 2, "es": 2, "it": 2, "pt": 2})["el"], 70)

    def test_a_full_cell_refuses_more(self):
        self.bank.plan("P", 4, shares={"purpose": {"factual": 1, "everyday": 1}})
        for i in range(2): self.bank.submit(self.forum(i), msg(TEXTS[i]), plan_id="P", run="r", generator="g")
        with self.assertRaises(QuotaError): self.bank.submit(self.forum(9), msg(TEXTS[2]), plan_id="P", run="r", generator="g")
        self.bank.submit(self.forum(10, purpose="everyday"), msg(TEXTS[3]), plan_id="P", run="r", generator="g")

    def test_a_shared_dimension_is_closed(self):
        self.bank.plan("P", 4, shares={"purpose": {"factual": 1}})
        with self.assertRaises(QuotaError): self.bank.submit(self.forum(1, purpose="astrology"), msg(TEXTS[0]), plan_id="P", run="r", generator="g")

    def test_the_astrovox_cap_holds(self):
        """The real failure: 9.4% of forum prompts came from one forum against a 3% cap, and nothing objected."""
        self.bank.plan("P", 100, shares={"language": {"el": 1}}, caps={"forum": {"astrovox": 3}})
        for i in range(10): self.forum(i, forum="astrovox")
        for i in range(10, 20): self.forum(i, forum="lexilogia")
        taken = []
        while True:
            s = self.bank.claim("P", "forum", worker="w")
            if s is None: break
            taken.append(s["forum"]); self.bank.submit(s["source_id"], msg("%s (%d)" % (TEXTS[len(taken) % 6], len(taken)) + " x" * len(taken)),
                                                        plan_id="P", run="r", generator="g", allow_near_duplicate=True)
        self.assertEqual(taken.count("astrovox"), 3); self.assertEqual(taken.count("lexilogia"), 10)

    def test_outstanding_claims_hold_their_place(self):
        self.bank.plan("P", 2, shares={"language": {"el": 1}})
        for i in range(5): self.forum(i)
        self.assertIsNotNone(self.bank.claim("P", "forum", worker="a")); self.assertIsNotNone(self.bank.claim("P", "forum", worker="b"))
        self.assertIsNone(self.bank.claim("P", "forum", worker="c"))

    def test_a_released_claim_frees_its_place(self):
        self.bank.plan("P", 1, shares={"language": {"el": 1}}); self.forum(1); self.forum(2)
        s = self.bank.claim("P", "forum", worker="a"); self.assertIsNone(self.bank.claim("P", "forum", worker="b"))
        self.bank.release(s["source_id"]); self.assertIsNotNone(self.bank.claim("P", "forum", worker="b"))

    def test_forums_fill_evenly_rather_than_in_file_order(self):
        self.bank.plan("P", 6, shares={"language": {"el": 1}})
        for i in range(30): self.forum(i, forum=("a", "b", "c")[i // 10])
        seen = []
        for k in range(6):
            s = self.bank.claim("P", "forum", worker="w"); seen.append(s["forum"])
            self.bank.submit(s["source_id"], msg(TEXTS[k]), plan_id="P", run="r", generator="g")
        self.assertEqual(sorted(seen), ["a", "a", "b", "b", "c", "c"])

    def test_claim_order_is_reproducible(self):
        def order(path):
            b = PromptBank(path); b.plan("P", 9, shares={"language": {"el": 1}})
            for i in range(9): b.add_source("forum", "https://x.gr/t/%d" % i, forum="f", purpose="factual", language="el", payload={}, origin="o")
            out = [b.claim("P", "forum", worker="w")["natural_key"] for _ in range(9)]; b.db.close(); return out
        self.assertEqual(order(os.path.join(self.dir.name, "one.sqlite")), order(os.path.join(self.dir.name, "two.sqlite")))

    def test_a_superseded_prompt_gives_its_place_to_the_retry(self):
        self.bank.plan("P", 1, shares={"language": {"el": 1}})
        p = self.bank.submit(self.forum(1), msg(TEXTS[0]), plan_id="P", run="r", generator="g")
        self.bank.supersede(p, msg(TEXTS[1]), run="r2", generator="g")
        row = [r for r in self.bank.coverage("P") if r["key"] == "el"][0]
        self.assertEqual((row["filled"], row["remaining"]), (1, 0))

    def test_an_unattainable_plan_is_reported_before_any_work_is_done(self):
        self.bank.plan("P", 10, shares={"purpose": {"factual": 5, "dialogue": 5}})
        for i in range(6): self.forum(i)
        short = self.bank.feasibility("P")
        self.assertEqual([(r["key"], r["short_by"]) for r in short], [("dialogue", 5)])

    def test_coverage_and_audit_are_clean_after_normal_use(self):
        self.bank.plan("P", 3, shares={"purpose": {"factual": 2, "everyday": 1}})
        self.bank.submit(self.forum(1), msg(TEXTS[0]), plan_id="P", run="r", generator="g")
        self.bank.submit(self.seed(1), msg(TEXTS[1]), plan_id="P", run="r", generator="g")
        cov = {r["key"]: r for r in self.bank.coverage("P")}
        self.assertEqual((cov["factual"]["target"], cov["factual"]["filled"], cov["factual"]["remaining"]), (2, 1, 1))
        a = self.bank.audit()
        self.assertEqual(a.pop("integrity"), "ok"); self.assertEqual(a.pop("quotas_overshot"), [])
        self.assertEqual(set(a.values()), {0})

class Flows(Base):
    def test_fill_registers_n_and_each_prompt_traces_to_its_own_source(self):
        for i in range(10): self.bank.add_source("forum", "https://x.gr/t/%d" % i, forum="f", purpose="factual", language="el", origin="o",
                                                 payload={"prompt_el": "%s -- %d" % (TEXTS[i % 6], i) + " λέξη" * i})
        self.bank.plan("P", 6, shares={"language": {"el": 1}})
        r = fill(self.bank, "P", "forum", 6, run="r", generator="g")
        self.assertEqual((r["registered"], r["stopped_because"]), (6, "reached n"))
        self.assertEqual(len({self.bank.lineage(p)["source"]["source_id"] for p in r["prompt_ids"]}), 6)

    def test_a_source_that_renders_a_duplicate_is_spent_and_the_loop_moves_on(self):
        ingest_seeds(self.bank, [{"purpose": "everyday", "language": "el", "slot": i} for i in range(5)], origin="gen")
        self.bank.plan("P", 5, shares={"language": {"el": 1}}); calls = []
        def render(src):
            calls.append(src["source_id"]); return msg(TEXTS[0] if len(calls) <= 2 else TEXTS[len(calls)])
        r = fill(self.bank, "P", "seed", 5, run="r", generator="g", render=render)
        self.assertEqual(r["registered"], 4); self.assertEqual(r["skipped"], {"DuplicateError": 1})
        self.assertEqual(r["stopped_because"], "no unused source fits the plan any more")
        self.assertEqual(self.bank.stats()["sources"][("seed", "rejected")], 1)

    def test_a_render_that_throws_spends_the_source_instead_of_looping_forever(self):
        ingest_seeds(self.bank, [{"purpose": "everyday", "language": "el", "slot": i} for i in range(3)], origin="gen")
        self.bank.plan("P", 3, shares={"language": {"el": 1}})
        def render(src): raise RuntimeError("Sol timed out")
        r = fill(self.bank, "P", "seed", 3, run="r", generator="g", render=render)
        self.assertEqual((r["registered"], r["skipped"]), (0, {"render_failed": 3}))

    def test_the_same_seed_offered_twice_is_one_source(self):
        rows = [{"purpose": "math", "language": "el", "task": "x"}]
        self.assertEqual(ingest_seeds(self.bank, rows, origin="a"), {"added": 1})
        self.assertEqual(ingest_seeds(self.bank, rows, origin="b"), {"already_known": 1})

    def test_fill_stops_when_the_plan_is_full_not_when_the_supply_is(self):
        for i in range(9): self.bank.add_source("forum", "https://x.gr/t/%d" % i, forum="f", purpose="factual", language="el", origin="o",
                                                payload={"prompt_el": "%s %d" % (TEXTS[i % 6], i) + " κάτι" * (i + 1)})
        self.bank.plan("P", 4, shares={"language": {"el": 1}})
        r = fill(self.bank, "P", "forum", 9, run="r", generator="g")
        self.assertEqual(r["registered"], 4); self.assertEqual(self.bank.stats()["sources"][("forum", "available")], 5)


if __name__ == "__main__": unittest.main()
