"""Bounded SQLite and quota invariants for the prompt generator."""
import collections
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location("core",HERE/"core.py")
core=importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


class CoreTests(unittest.TestCase):
    def _accepted_row(self,store,rid):
        row=next(r for r in store.rows(rid) if r["seed"]["purpose"]!="dialogue")
        seed=row["seed"]
        request="Please complete the task using the supplied source."
        generated={"request":request,"messages":[{"role":"user","content":request+"\n\n---\n"+seed["fixture"]["content"]}],"source_hash":seed["content_hash"]}
        review={"accepted":True,"issues":[],**{"observed_"+axis:seed[axis] for axis in ("purpose","language","register","attitude")}}
        store.record(rid,row["id"],"accepted",generated,review)
        return next(r for r in store.rows(rid) if r["id"]==row["id"])

    def test_exact_margins_and_greeklish_compatibility(self):
        c,rows=core.make_slots({"size":100,"seed":19})
        self.assertEqual(len(rows),100)
        self.assertEqual(collections.Counter(r["purpose"] for r in rows),core.apportion(c["purpose_weights"],100))
        for axis in ("language","register","attitude","difficulty"):
            self.assertEqual(collections.Counter(r[axis] for r in rows),core.apportion(c[axis+"_weights"],100))
        self.assertTrue(all(r["language"]=="el" for r in rows if r["register"]=="greeklish"))
        self.assertEqual([r["id"] for r in rows],[f"S{i:04d}" for i in range(1,101)])

    def test_create_resume_and_cross_run_instance_uniqueness(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=core.Store(Path(tmp)/"state.sqlite")
            c={"size":20,"seed":17,"programme":"test","split":"train"}
            a=store.create(c,"run-a")
            self.assertEqual(a["status_counts"],{"planned":20})
            first=store.rows("run-a")
            self.assertEqual(len({r["seed"]["instance_hash"] for r in first}),20)
            with self.assertRaisesRegex(ValueError,"resume"):
                store.create(c,"run-a")
            store.create(c,"run-b")
            second=store.rows("run-b")
            self.assertFalse({r["seed"]["instance_hash"] for r in first}&{r["seed"]["instance_hash"] for r in second})
            self.assertEqual(first,store.rows("run-a"))

    def test_failed_create_rolls_back_all_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=core.Store(Path(tmp)/"state.sqlite")
            c={"size":20,"seed":17,"programme":"capacity","max_instances_per_structure":1}
            with self.assertRaisesRegex(ValueError,"structure capacity exhausted"):
                store.create(c,"too-small")
            with store.db() as db:
                for table in ("runs","slots","instances","content_families"):
                    self.assertEqual(db.execute(f"SELECT count(*) FROM {table}").fetchone()[0],0,table)

    def test_call_budget_and_idempotent_completed_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=core.Store(Path(tmp)/"state.sqlite")
            store.create({"size":5,"max_calls":1},"run")
            self.assertIsNone(store.reserve_call("run","wording","call-a"))
            with self.assertRaisesRegex(ValueError,"already reserved"):
                store.reserve_call("run","wording","call-a")
            store.finish_call("call-a",{"ok":True})
            self.assertEqual(store.reserve_call("run","wording","call-a"),{"ok":True})
            with self.assertRaisesRegex(ValueError,"budget exhausted"):
                store.reserve_call("run","wording","call-b")

    def test_call_key_cannot_replay_another_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=core.Store(Path(tmp)/"state.sqlite")
            store.create({"size":5},"first")
            store.create({"size":5},"second")
            store.reserve_call("first","wording","same-key")
            store.finish_call("same-key",{"private":"first-run-response"})
            with self.assertRaises(ValueError):
                store.reserve_call("second","wording","same-key")

    def test_invalid_status_cannot_create_fake_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=core.Store(Path(tmp)/"state.sqlite")
            store.create({"size":5},"run")
            with self.assertRaises(ValueError):
                store.record("run","S0001","accepted")
            self.assertEqual(store.report("run")["accepted_single_turn"],0)

    def test_same_source_content_stays_in_one_split(self):
        # A changed hidden parameter is not a new content family.
        with tempfile.TemporaryDirectory() as tmp:
            store=core.Store(Path(tmp)/"state.sqlite")
            purpose={p:(100 if p=="math" else 0) for p in core.PURPOSES}
            c={"size":20,"seed":23,"programme":"split-test","purpose_weights":purpose}
            store.create({**c,"split":"train"},"train")
            store.create({**c,"split":"holdout"},"holdout")
            train={r["seed"]["content_hash"] for r in store.rows("train")}
            holdout={r["seed"]["content_hash"] for r in store.rows("holdout")}
            self.assertFalse(train&holdout,"identical source content crossed train/holdout")

    def test_dialogue_import_rejects_forged_receipts_and_partial_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=core.Store(Path(tmp)/"state.sqlite")
            store.create({"size":20,"seed":3},"run")
            row=next(r for r in store.rows("run") if r["seed"]["purpose"]=="dialogue")
            seed=row["seed"]
            request="A complete opening prompt"
            opening={"role":"user","content":request+"\n\n---\n"+seed["fixture"]["content"]}
            generated={"request":request,"messages":[opening],"source_hash":seed["content_hash"]}
            review={"accepted":True,"issues":[],**{"observed_"+a:seed[a] for a in ("purpose","language","register","attitude")}}
            store.record("run",row["id"],"opening_accepted",generated,review)
            fake={"messages":[opening,{"role":"assistant","content":"answer"},{"role":"user","content":"followup"}],"assistant_receipts":[],"checkpoint_sha256":"a"*64,"goal_verification":{"goal":row["seed"]["dialogue"]["goal"],"passed":True,"evidence":"reviewed"}}
            with self.assertRaisesRegex(ValueError,"provenance"):
                store.import_dialogue("run",row["id"],fake)
            self.assertEqual(next(r for r in store.rows("run") if r["id"]==row["id"])["status"],"opening_accepted")

    def test_revision_archives_accepted_row_and_rekeys_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=core.Store(Path(tmp)/"state.sqlite")
            store.create({"size":20,"seed":97},"run")
            accepted=self._accepted_row(store,"run")
            oldseed=accepted["seed"]
            replacement=copy.deepcopy(oldseed["fixture"])
            replacement["content"] += " Editorial clarification: this is a fictional exercise."
            replacement["parameters"]["editorial_revision"]="fictional exercise"
            store.request_revision("run",accepted["id"],["source clarity"],"independent-review",replacement)
            revised=next(r for r in store.rows("run") if r["id"]==accepted["id"])
            self.assertEqual(revised["status"],"rejected")
            self.assertFalse(revised["review"]["accepted"])
            self.assertEqual(revised["seed"]["content_hash"],core.digest(replacement["content"]))
            self.assertEqual(revised["seed"]["content_family"],core.content_family_key(oldseed["underlying_family"],replacement))
            self.assertEqual(revised["seed"]["fixture"],replacement)
            with store.db() as db:
                history=db.execute("SELECT previous,issues,reviewer FROM revisions WHERE run=? AND slot=?",("run",accepted["id"])).fetchone()
                self.assertEqual(json.loads(history["previous"])["status"],"accepted")
                self.assertEqual(json.loads(history["issues"]),["source clarity"])
                self.assertEqual(history["reviewer"],"independent-review")
                self.assertEqual(db.execute("SELECT count(*) FROM accepted_texts WHERE run=? AND slot=?",("run",accepted["id"])).fetchone()[0],0)
                inst=db.execute("SELECT hash,content_family,structure FROM instances WHERE run=? AND slot=?",("run",accepted["id"])).fetchone()
                self.assertEqual(inst["hash"],revised["seed"]["instance_hash"])
                self.assertEqual(inst["content_family"],revised["seed"]["content_family"])
                self.assertEqual(inst["structure"],replacement["structure_id"])

    def test_revision_cross_split_conflict_rolls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=core.Store(Path(tmp)/"state.sqlite")
            store.create({"size":20,"seed":99,"split":"train","programme":"revision-test"},"train")
            accepted=self._accepted_row(store,"train")
            replacement=copy.deepcopy(accepted["seed"]["fixture"])
            replacement["parameters"]["new_identity"]="cross-split-collision"
            foreign_family=core.content_family_key(accepted["seed"]["underlying_family"],replacement)
            with store.db() as db: db.execute("INSERT OR REPLACE INTO content_families VALUES(?,?)",(foreign_family,"holdout"))
            with self.assertRaisesRegex(ValueError,"crosses content-family split"):
                store.request_revision("train",accepted["id"],["replace source"],"reviewer",replacement)
            after=next(r for r in store.rows("train") if r["id"]==accepted["id"])
            self.assertEqual(after,accepted)
            with store.db() as db:
                self.assertEqual(db.execute("SELECT count(*) FROM revisions").fetchone()[0],0)
                self.assertEqual(db.execute("SELECT count(*) FROM accepted_texts WHERE run=? AND slot=?",("train",accepted["id"])).fetchone()[0],1)

    def test_revision_rejects_active_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=core.Store(Path(tmp)/"state.sqlite")
            store.create({"size":20,"seed":101},"run")
            accepted=self._accepted_row(store,"run")
            token=store.claim_run("run")
            try:
                with self.assertRaisesRegex(ValueError,"active run"):
                    store.request_revision("run",accepted["id"],["needs improvement"],"reviewer")
            finally:store.release_run("run",token)
            self.assertEqual(next(r for r in store.rows("run") if r["id"]==accepted["id"]),accepted)

    def test_conditional_plan_reserves_open_and_full(self):
        _,rows=core.make_slots({"size":100,"seed":9162026})
        branches=[r["required_branch"] for r in rows if r["family"]=="if_conditional"]
        self.assertIn("open",branches)
        self.assertIn("full",branches)
        with tempfile.TemporaryDirectory() as tmp:
            store=core.Store(Path(tmp)/"state.sqlite")
            store.create({"size":100,"seed":9162026},"run")
            actual=[(r["seed"]["required_branch"],r["seed"]["fixture"]["reference"]["branch"]) for r in store.rows("run") if r["seed"]["family"]=="if_conditional"]
            self.assertTrue(actual)
            self.assertTrue(all(required==branch for required,branch in actual))


if __name__=="__main__": unittest.main()
