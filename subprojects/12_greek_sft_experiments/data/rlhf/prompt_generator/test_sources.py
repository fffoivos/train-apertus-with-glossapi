"""Transactional source import and mocked screening boundary tests."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import core
import sources
import worker


def forum_record(seed,text="Can you explain the supplied notice?"):
    return {"source_id":"forum-thread-1","source_version":"v1","source_sha256":hashlib.sha256(text.encode()).hexdigest(),
            "messages":[{"role":"user","content":text}],
            "labels":{k:seed[k] for k in ("purpose","language","register","attitude","difficulty")},
            "review":{"direct_request":True,"accepted":True,"reviewer":"human-fixture","premise_status":"not_applicable"}}


class RejectReviewServer:
    def __init__(self): self.stages=[];self.usage=[]
    def call(self,prompt,schema,**kwargs):
        stage="review" if prompt.startswith(worker.REVIEW) else "generate"
        self.stages.append(stage)
        packets=json.loads(prompt.split("\nPACKETS\n",1)[1])
        if stage=="generate":return {"items":[{"id":p["id"],"request":"Reworded request"} for p in packets]}
        return {"items":[{"id":p["id"],"accepted":False,"issues":["not suitable for this quota"],
                          "observed_purpose":p["seed"]["purpose"],"observed_language":p["seed"]["language"],
                          "observed_register":p["seed"]["register"],"observed_attitude":p["seed"]["attitude"],"rationale":"fake rejection"} for p in packets]}


class SourceTests(unittest.TestCase):
    def _setup(self,tmp):
        store=core.Store(Path(tmp)/"state.sqlite")
        store.create({"size":20,"seed":87,"max_repairs":1},"run")
        row=next(r for r in store.rows("run") if r["seed"]["purpose"]!="dialogue")
        return store,row

    def test_exact_preservation_and_transactional_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            store,row=self._setup(tmp)
            original=store.rows("run")
            good=forum_record(row["seed"])
            bad=forum_record(row["seed"],"Second request")
            bad["source_id"]="forum-thread-2"
            bad["source_sha256"]="0"*64
            with self.assertRaisesRegex(ValueError,"checksum"):
                sources.import_forums(store,"run",[good,bad])
            self.assertEqual(store.rows("run"),original)
            with store.db() as db:
                self.assertEqual(db.execute("SELECT count(*) FROM imported_sources").fetchone()[0],0)
            sources.import_forums(store,"run",[good])
            changed=next(r for r in store.rows("run") if r["id"]==row["id"])
            self.assertEqual(changed["status"],"generated")
            self.assertEqual(changed["generated"]["messages"],good["messages"])
            self.assertEqual(changed["seed"]["fixed_messages"],good["messages"])
            self.assertEqual(changed["seed"]["content_hash"],good["source_sha256"])

    def test_quota_mismatch_rejects_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            store,row=self._setup(tmp)
            rec=forum_record(row["seed"])
            rec["labels"]["purpose"]="unsupported-purpose"
            with self.assertRaisesRegex(ValueError,"no matching unfilled"):
                sources.import_forums(store,"run",[rec])
            self.assertTrue(all(r["status"]=="planned" for r in store.rows("run")))

    def test_rejected_forum_request_is_never_regenerated(self):
        with tempfile.TemporaryDirectory() as tmp:
            store,row=self._setup(tmp)
            rec=forum_record(row["seed"])
            sources.import_forums(store,"run",[rec])
            imported=next(r for r in store.rows("run") if r["id"]==row["id"])
            server=RejectReviewServer()
            w=worker.Worker(store,"run",Path(tmp)/"out",server)
            w.process_batch([imported])
            self.assertEqual(server.stages,["review"])
            final=next(r for r in store.rows("run") if r["id"]==row["id"])
            self.assertEqual(final["status"],"rejected")
            self.assertEqual(final["generated"]["messages"],rec["messages"])

    def test_screen_uses_adapter_only_on_accepted_messages(self):
        with tempfile.TemporaryDirectory() as tmp:
            store,row=self._setup(tmp)
            seed=row["seed"]
            gen=worker.assemble(seed,"Please answer using the attached source.")
            rev={"accepted":True,"issues":[],**{"observed_"+a:seed[a] for a in ("purpose","language","register","attitude")}}
            store.record("run",row["id"],"accepted",gen,rev)
            seen=[]
            class FakeDecon:
                def __init__(self,cache_dir=None,require_confirm=False):
                    self.identities={"mock":"fixture"}
                    self.require_confirm=require_confirm
                def contaminated(self,messages):
                    seen.append(messages);return False
            previous=sys.modules.get("mixlib")
            sys.modules["mixlib"]=types.SimpleNamespace(Decon=FakeDecon)
            try: receipt=sources.screen(store,"run",Path(tmp)/"screen",cache_dir=Path(tmp)/"cache")
            finally:
                if previous is None:sys.modules.pop("mixlib",None)
                else:sys.modules["mixlib"]=previous
            self.assertEqual(receipt["checked"],1)
            self.assertEqual(seen,[gen["messages"]])
            self.assertEqual(receipt["hits"],[])


if __name__=="__main__":unittest.main()
