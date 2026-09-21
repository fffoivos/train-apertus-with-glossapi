"""Regression tests for the CP2 independent review (21 Sept 2026): what 29 really-generated prompts showed."""
import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from rlhf.prompts import PromptBank, apportion, fill, ingest_forum_gate
from rlhf.prompts import slots as slotlib
from rlhf.prompts.flows import clean_forum_text

LANG = {"el": 70, "en": 20, "fr": 2, "de": 2, "es": 2, "it": 2, "pt": 2}

class Base(unittest.TestCase):
    def setUp(self): self.dir = tempfile.TemporaryDirectory(); self.bank = PromptBank(os.path.join(self.dir.name, "b.sqlite"))
    def tearDown(self): self.bank.db.close(); self.dir.cleanup()
    def gate_file(self, rows):
        p = os.path.join(self.dir.name, "gated.jsonl")
        open(p, "w").write("".join(json.dumps(dict(id="f:%d" % i, forum="mathematica", url="https://x.gr/%d" % i, title="t", section="s",
                                                     gate=dict(post_kind=k, self_contained=True, task_type=t, prompt_el=text)), ensure_ascii=False) + "\n" for i, (k, t, text) in enumerate(rows)))
        return p


class H1_SocialPosts(Base):
    def test_a_post_with_no_request_in_it_is_not_supply(self):
        p = self.gate_file([("request", "question", "Πώς λύνεται αυτή η εξίσωση δευτέρου βαθμού με παράμετρο και τι σημαίνει η διακρίνουσα"),
                            ("social", "share", "Με λένε Αναστασία και εργάζομαι ως μεταφράστρια εδώ και τέσσερα χρόνια, χαίρομαι που σας βρήκα")])
        self.assertEqual(ingest_forum_gate(self.bank, p), {"accepted": 1, "rejected_by_gate": 1})
        self.assertEqual(self.bank.stats()["sources"], {("forum", "available"): 1, ("forum", "rejected"): 1})

    def test_the_old_behaviour_is_a_switch_not_a_deletion(self):
        p = self.gate_file([("social", "share", "Δεν την έχω πει ποτέ αυτή την ιστορία από τον στρατό το ενενήντα έξι στη Θεσσαλονίκη")])
        self.assertEqual(ingest_forum_gate(self.bank, p, accept_kinds=("request", "social")), {"accepted": 1})


class H2_ScraperMarkers(Base):
    def test_math_markers_are_unwrapped_not_shipped(self):
        self.assertEqual(clean_forum_text("είναι ακριβώς [MATH 12] φορές μικρότερα"), "είναι ακριβώς 12 φορές μικρότερα")
        self.assertEqual(clean_forum_text(r"η [MATH \mathbb{R}] είναι πλήρης"), r"η $\mathbb{R}$ είναι πλήρης")

    def test_a_prompt_that_still_carries_a_marker_spends_its_source_instead_of_shipping(self):
        p = self.gate_file([("request", "question", "Δείτε το [URL] και πείτε μου αν η απόδειξη στέκει για κάθε φυσικό αριθμό μεγαλύτερο του δύο"),
                            ("request", "calculation", "Όλα εκεί είναι ακριβώς [MATH 12] φορές μικρότερα, πόσο ζυγίζει λοιπόν ένας άνθρωπος εβδομήντα κιλών")])
        ingest_forum_gate(self.bank, p); self.bank.plan("P", 2, shares={"language": {"el": 1}})
        r = fill(self.bank, "P", "forum", 2, run="r", generator="g")
        self.assertEqual((r["registered"], r["skipped"]), (1, {"render_failed": 1}))
        text = json.loads(self.bank.db.execute("SELECT messages FROM prompts").fetchone()[0])[0]["content"]
        self.assertNotIn("[MATH", text); self.assertIn("ακριβώς 12 φορές", text)


class M6_ChunkedRounds(unittest.TestCase):
    def test_fifty_small_plans_converge_on_the_target_instead_of_starving_four_languages(self):
        naive, have = {k: 0 for k in LANG}, {k: 0 for k in LANG}
        for _ in range(50):
            for k, v in apportion(10, LANG).items(): naive[k] += v
            for k, v in apportion(10, LANG, have).items(): have[k] += v
        self.assertEqual((naive["de"], naive["fr"], naive["pt"]), (50, 0, 0))                     # the bias, reproduced
        self.assertEqual(have, {"el": 350, "en": 100, "fr": 10, "de": 10, "es": 10, "it": 10, "pt": 10})

    def test_every_chunk_still_sums_to_n(self):
        have = {k: 0 for k in LANG}
        for n in (7, 10, 3, 30, 1, 19):
            q = apportion(n, LANG, have); self.assertEqual(sum(q.values()), n); self.assertTrue(all(v >= 0 for v in q.values()))
            for k, v in q.items(): have[k] += v

    def test_a_plan_can_continue_an_earlier_one(self):
        d = tempfile.TemporaryDirectory(); b = PromptBank(os.path.join(d.name, "b.sqlite"))
        b.plan("A", 10, shares={"language": LANG})
        for i, (lang, n) in enumerate([("el", 7), ("en", 2), ("de", 1)]):
            for j in range(n):
                s = b.add_source("seed", "k%d-%d" % (i, j), purpose="everyday", language=lang, payload={}, origin="o")
                b.submit(s, [{"role": "user", "content": "ερώτηση νούμερο %d-%d με αρκετές διαφορετικές λέξεις %s" % (i, j, "λέξη" * (i * 7 + j))}], plan_id="A", run="r", generator="g")
        b.plan("B", 10, shares={"language": LANG}, after=["A"])
        q = {r["key"]: r["target"] for r in b.coverage("B")}
        self.assertEqual(q["de"], 0); self.assertEqual(sum(q[k] for k in ("fr", "es", "it", "pt")), 1); self.assertEqual(sum(q.values()), 10)
        b.db.close(); d.cleanup()


T = {"within_seeded_defaults_percent": {"difficulty": {"routine": 1}, "attitude": {"cooperative": 1}, "register": {"standard": 1}}}

# CP2 M1 (a semantic near-paraphrase across plans) was first "fixed" with a hard rule: never the same situation twice for a
# language + subtype. Withdrawn the same day at the owner's correction -- a seed is the combination of ALL its elements, and
# reusing one element is not a duplicate. The real cause of M1 is that generate.py may DROP the topic, which is recorded for
# the generator's owner; see rlhf/tests/test_prompt_bank_ingredients.py for what identity means now.


if __name__ == "__main__": unittest.main()
