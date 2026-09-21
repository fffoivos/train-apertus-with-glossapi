"""Source-preserving imports and benchmark screening; no upstream generation."""
import hashlib,json,pathlib,sys
from core import BASE,Store,canonical,digest,now,write_json
def import_forums(store,rid,records):
 """Attach reviewed forum records to matching unfilled quota cells; never rewrite."""
 with store.db() as d:
  d.execute("BEGIN IMMEDIATE")
  run=d.execute("SELECT config,worker_claim FROM runs WHERE id=?",(rid,)).fetchone()
  if not run:raise ValueError("unknown run")
  if run["worker_claim"]:raise ValueError("run is active")
  for rec in records:
   required={"source_id","source_version","source_sha256","messages","labels","review"}
   if not required<=rec.keys():raise ValueError("incomplete source record")
   ms=rec["messages"]
   if len(ms)!=1 or ms[0].get("role")!="user" or not isinstance(ms[0].get("content"),str) or not ms[0]["content"].strip():raise ValueError("single direct user request required")
   if hashlib.sha256(ms[0]["content"].encode()).hexdigest()!=rec["source_sha256"]:raise ValueError("source checksum mismatch")
   if rec["review"].get("direct_request") is not True or rec["review"].get("accepted") is not True or not rec["review"].get("reviewer"):raise ValueError("upstream direct-request review required")
   if rec["review"].get("premise_status") not in ("supported","contradicted","unresolved","not_applicable"):raise ValueError("premise annotation required")
   labels=rec["labels"]
   if not {"purpose","language","register","attitude","difficulty"}<=labels.keys():raise ValueError("source labels incomplete")
   if labels["purpose"]=="dialogue":raise ValueError("forums are single-turn imports")
   match=None
   for row in d.execute("SELECT * FROM slots WHERE run=? AND status='planned' ORDER BY id",(rid,)):
    seed=json.loads(row["seed"])
    if all(seed[k]==labels[k] for k in labels if k in ("purpose","language","register","attitude","difficulty")):match=(row,seed);break
   if not match:raise ValueError("no matching unfilled source quota cell; rebalance explicitly, do not rewrite forum")
   row,seed=match;source_key=digest([rec["source_id"],rec["source_version"],rec["source_sha256"]]);family="forum:"+rec["source_id"]
   old=d.execute("SELECT split FROM content_families WHERE id=?",(family,)).fetchone()
   if old and old[0]!=seed["split"]:raise ValueError("source family split conflict")
   d.execute("DELETE FROM instances WHERE run=? AND slot=?",(rid,row["id"]))
   d.execute("INSERT INTO instances VALUES(?,?,?,?,?,?,?)",(source_key,json.loads(run["config"])["programme"],"forum/"+labels["purpose"],family,seed["split"],rid,row["id"]))
   d.execute("INSERT INTO imported_sources VALUES(?,?)",(source_key,canonical(rec)))
   d.execute("INSERT OR IGNORE INTO content_families VALUES(?,?)",(family,seed["split"]))
   seed.update(source_kind="forum_import",content_family=family,instance_hash=source_key,fixed_messages=ms,source_receipt={k:rec[k] for k in ("source_id","source_version","source_sha256")})
   seed["fixture"]={"content":ms[0]["content"],"instruction_spec":"Preserve the supplied natural request exactly; assess whether it is a direct request with the annotated purpose and premise. Do not rewrite it to meet style quotas.","reference":{"upstream_review":rec["review"]},"premise_status":rec["review"]["premise_status"]}
   gen={"messages":ms,"request":ms[0]["content"],"source_hash":rec["source_sha256"]}
   seed["content_hash"]=rec["source_sha256"]
   d.execute("UPDATE slots SET seed=?,generated=?,status='generated' WHERE run=? AND id=?",(canonical(seed),canonical(gen),rid,row["id"]))
 return store.report(rid)
def screen(store,rid,output,cache_dir=None):
 sys.path.insert(0,str(BASE.parent.parent))
 from mixlib import Decon
 decon=Decon(cache_dir=cache_dir,require_confirm=True)
 results=[]
 for row in store.rows(rid):
  if row["status"] not in ("accepted","opening_accepted","dialogue_ready"):continue
  hit=decon.contaminated(row["generated"]["messages"])
  results.append({"id":row["id"],"hit":hit})
 receipt={"run":rid,"checked_utc":now(),"method":"repository mixlib.Decon: NFKC casefold 8-gram containment >=0.5 OR shared 13-gram","cache_identities":decon.identities,"checked":len(results),"hits":[x for x in results if x["hit"]],"semantic_decontamination":False,"training_eligible":False}
 write_json(pathlib.Path(output)/"benchmark_screen.json",receipt);return receipt
