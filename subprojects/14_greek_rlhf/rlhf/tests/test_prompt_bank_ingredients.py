"""Personas, situations and topics as a data structure (owner, 21 Sept): rows and constraints, not strings in a JSON blob."""
import json, os, sqlite3, sys, tempfile, unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from rlhf.prompts import PromptBank, SlotError, SourceError
from rlhf.prompts import slots as slotlib

def slot(person="P1", situation="S1", topic="T1", language="el", subtype="calculation", **kw):
    return dict(dict(purpose="math", language=language, subtype=subtype, packet=False, difficulty="routine", attitude="cooperative",
                     register="standard", detail="short", slot_id="X-S01", person=person, situation=situation, topic=topic), **kw)

class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory(); self.path = os.path.join(self.dir.name, "b.sqlite"); self.bank = PromptBank(self.path)
        self.bank.add_ingredients("person", ["P1", "P2", "P3"], language="el", origin="t"); self.bank.add_ingredients("person", ["Q1"], language="en", origin="t")
        self.bank.add_ingredients("situation", ["S1", "S2"], origin="t"); self.bank.add_ingredients("topic", ["T1", "T2", "T3"], origin="t")
    def tearDown(self): self.bank.db.close(); self.dir.cleanup()
    def add(self, **kw): return self.bank.add_slot("seed", slot(**kw), purpose="math", language=kw.get("language", "el"), origin="t")


class Structure(Base):
    def test_pools_are_idempotent_and_a_persona_has_a_language(self):
        self.assertEqual(self.bank.add_ingredients("person", ["P1", "P9"], language="el", origin="again"), 1)
        with self.assertRaises(sqlite3.IntegrityError): self.bank.db.execute("INSERT INTO ingredients VALUES ('per:x','person',NULL,'nobody','t',0,0)")
        with self.assertRaises(sqlite3.IntegrityError): self.bank.db.execute("INSERT INTO ingredients VALUES ('top:x','topic','el','languaged topic','t',0,0)")

    def test_usage_is_a_join_not_a_parse(self):
        self.add(person="P1", topic="T1"); self.add(person="P1", situation="S2", topic="T2")
        u = {r["value"]: r["used"] for r in self.bank.ingredient_usage("person", "el")}
        self.assertEqual(u, {"P1": 2, "P2": 0, "P3": 0}); self.assertEqual([r["value"] for r in self.bank.ingredient_usage("person", "el")][:2], ["P2", "P3"])
        self.assertEqual(self.bank.exhaustion()["person:el"], {"pool": 3, "unused": 2, "max_times_one_value_used": 2})

    def test_a_slot_made_of_something_outside_the_pool_is_refused(self):
        with self.assertRaises(SlotError): self.add(person="someone nobody registered")
        self.assertEqual(self.bank.db.execute("SELECT COUNT(*) FROM sources").fetchone()[0], 0)        # and its source was rolled back with it

    def test_the_same_triple_is_refused_even_with_different_labels(self):
        self.add()
        with self.assertRaises(SlotError): self.bank.add_slot("seed", slot(difficulty="challenging", subtype="solving"), purpose="math", language="el", origin="t")

    def test_the_same_scene_is_refused_for_one_language_and_subtype_only(self):
        self.add(person="P1", topic="T1")
        with self.assertRaises(SlotError): self.add(person="P2", topic="T2")                         # same situation, same el/calculation
        self.add(person="P2", topic="T2", subtype="solving")                                        # another subtype: fine
        self.add(person="Q1", topic="T3", language="en")                                            # another language: fine

    def test_raw_sql_cannot_repeat_a_triple_or_an_enforced_scene(self):
        a = self.add(); row = self.bank.db.execute("SELECT * FROM slots WHERE source_id=?", (a,)).fetchone()
        b = self.bank.add_source("seed", "other", purpose="math", language="el", payload={}, origin="t"); raw = sqlite3.connect(self.path)
        with self.assertRaises(sqlite3.IntegrityError): raw.execute("INSERT INTO slots VALUES (?,?,?,?,?,?,1)", (b, "el", "solving", row["person_id"], row["situation_id"], row["topic_id"]))
        other = self.bank.db.execute("SELECT ingredient_id FROM ingredients WHERE value='T2'").fetchone()[0]
        with self.assertRaises(sqlite3.IntegrityError): raw.execute("INSERT INTO slots VALUES (?,?,?,?,?,?,1)", (b, "el", "calculation", row["person_id"], row["situation_id"], other))
        raw.close()

    def test_re_adding_the_same_slot_under_a_new_label_is_the_same_source(self):
        a = self.add(); b = self.bank.add_slot("seed", slot(slot_id="Y-S77"), purpose="math", language="el", origin="again")
        self.assertEqual(a, b); self.assertEqual(self.bank.db.execute("SELECT COUNT(*) FROM slots").fetchone()[0], 1)

    def test_lineage_says_what_the_prompt_was_made_of(self):
        a = self.add(); p = self.bank.submit(a, [{"role": "user", "content": "Πόσο κάνει δεκαπέντε τοις εκατό του διακόσια σαράντα, και πώς το ελέγχω γρήγορα"}], run="r", generator="g")
        m = self.bank.lineage(p)["made_of"]; self.assertEqual({k: v["value"] for k, v in m.items()}, {"person": "P1", "situation": "S1", "topic": "T1"})

    def test_a_forum_source_cannot_be_a_slot(self):
        with self.assertRaises(SourceError): self.bank.add_slot("forum", slot(), purpose="math", language="el", origin="t")


class RealPools(unittest.TestCase):
    def test_build_draws_from_the_bank_and_leaves_a_slot_row_for_every_source(self):
        d = tempfile.TemporaryDirectory(); b = PromptBank(os.path.join(d.name, "b.sqlite"))
        T = {"within_seeded_defaults_percent": {"difficulty": {"routine": 1}, "attitude": {"cooperative": 1}, "register": {"standard": 1}}}
        ids = slotlib.build(b, [("seed", "math", "el")] * 12 + [("dialogue", "dialogue", "en")] * 3, prefix="T", seed=4, target=T)
        self.assertEqual(b.db.execute("SELECT COUNT(*) FROM slots").fetchone()[0], 15); self.assertEqual(len(set(ids)), 15)
        self.assertEqual(slotlib.ingest_axes(b), {k: 0 for k in slotlib.ingest_axes(b)})                 # idempotent
        a = b.audit(); self.assertEqual((a["slot_sources_with_no_slot_row"], a["repeated_scenes_among_enforced_slots"]), (0, 0))
        self.assertEqual(b.exhaustion()["person:el"]["max_times_one_value_used"], 1)                     # least-used first
        b.db.close(); d.cleanup()


if __name__ == "__main__": unittest.main()
