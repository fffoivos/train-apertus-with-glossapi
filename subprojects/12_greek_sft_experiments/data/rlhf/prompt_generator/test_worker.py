"""Worker tests with a local deterministic fake server; no model calls."""
import collections
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import core
import worker


def small_config(**overrides):
    c={"size":20,"seed":77,"batch_size":12,"concurrency":1,"max_calls":20,"max_repairs":1,
       "language_weights":{"el":0,"en":100,"fr":0,"de":0,"es":0,"it":0,"pt":0},
       "register_weights":{"standard":100,"informal":0,"formal":0,"greeklish":0},
       "attitude_weights":{"cooperative":100,"frustrated":0,"skeptical":0,"playful":0},
       "generate_dialogue_openings":False}
    return {**c,**overrides}


class FakeServer:
    def __init__(self,reject_once=False,fail_stage=None):
        self.reject_once=reject_once;self.fail_stage=fail_stage;self.calls=[];self.reviewed=set();self.usage=[]
    def call(self,prompt,schema,**kwargs):
        stage="review" if prompt.startswith(worker.REVIEW) else "generate"
        if self.fail_stage==stage: raise RuntimeError("injected server failure")
        packets=json.loads(prompt.split("\nPACKETS\n",1)[1]);self.calls.append((stage,packets))
        if stage=="generate":
            return {"items":[{"id":p["id"],"request":"Please complete the task using the attached source."+(" Revised to address the review." if p.get("previous_issues") else "")} for p in packets]}
        out=[]
        for p in packets:
            seed=p["seed"]
            reject=self.reject_once and not self.reviewed
            self.reviewed.add(p["id"])
            out.append({"id":p["id"],"accepted":not reject,"issues":["request too vague"] if reject else [],
                        "observed_purpose":seed["purpose"],"observed_language":seed["language"],
                        "observed_register":seed["register"],"observed_attitude":seed["attitude"],"rationale":"fake review"})
        return {"items":out}


class WorkerTests(unittest.TestCase):
    def _setup(self,tmp,**config):
        store=core.Store(Path(tmp)/"state.sqlite")
        store.create(small_config(**config),"run")
        return store

    def test_packet_excludes_private_answers_and_assembly_preserves_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=self._setup(tmp)
            for row in store.rows("run"):
                seed=row["seed"];packet=worker.public_packet(seed)
                self.assertNotIn("reference",packet)
                self.assertNotIn("parameters",packet)
                self.assertNotIn("checks",packet)
                self.assertNotIn("premise_status",packet)
                self.assertEqual(packet["source_content"],seed["fixture"]["content"])
                assembled=worker.assemble(seed,"  Could you handle this?  ")
                self.assertEqual(assembled["messages"],[{"role":"user","content":"Could you handle this?\n\n---\n"+seed["fixture"]["content"]}])
                self.assertEqual(worker.structural(seed,assembled),[])

    def test_reject_repair_review_and_deferred_dialogue(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=self._setup(tmp)
            server=FakeServer(reject_once=True)
            w=worker.Worker(store,"run",Path(tmp)/"out",server)
            result=w.run()
            rows=store.rows("run")
            dialogue=[r for r in rows if r["seed"]["purpose"]=="dialogue"]
            single=[r for r in rows if r["seed"]["purpose"]!="dialogue"]
            self.assertEqual(len(dialogue),7)
            self.assertTrue(all(r["status"]=="planned" for r in dialogue))
            self.assertTrue(all(r["status"]=="accepted" for r in single))
            self.assertEqual(result["accepted_single_turn"],13)
            self.assertEqual(result["completed_dialogues"],0)
            stages=[s for s,_ in server.calls]
            self.assertEqual(collections.Counter(stages),{"generate":3,"review":3})
            repairs=[p for stage,packets in server.calls if stage=="generate" for p in packets if p.get("previous_issues")]
            self.assertEqual(len(repairs),1)
            for r in single:
                self.assertEqual(r["generated"]["messages"][0]["content"].split("\n\n---\n",1)[1],r["seed"]["fixture"]["content"])
            self.assertEqual(w.run()["accepted_single_turn"],13)
            self.assertEqual(len(server.calls),6,"resume should not spend calls")

    def test_identical_call_is_cached_without_server_spend(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=self._setup(tmp)
            server=FakeServer();w=worker.Worker(store,"run",Path(tmp)/"out",server)
            packet=worker.public_packet(store.rows("run")[0]["seed"])
            first=w.call("generate",[packet],0)
            second=w.call("generate",[packet],0)
            self.assertEqual(first,second)
            self.assertEqual(len(server.calls),1)

    def test_call_failure_persists_and_same_key_is_not_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=self._setup(tmp)
            server=FakeServer(fail_stage="generate");w=worker.Worker(store,"run",Path(tmp)/"out",server)
            packet=worker.public_packet(store.rows("run")[0]["seed"])
            with self.assertRaisesRegex(RuntimeError,"injected"):
                w.call("generate",[packet],0)
            with store.db() as db:
                self.assertEqual(db.execute("SELECT status FROM calls").fetchone()[0],"failed")
            server.fail_stage=None
            with self.assertRaisesRegex(ValueError,"already reserved/failed"):
                w.call("generate",[packet],0)
            self.assertEqual(len(server.calls),0)


if __name__=="__main__": unittest.main()
