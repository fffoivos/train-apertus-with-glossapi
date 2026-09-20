"""Bounded Sol wording and independent review. No target-model sampling or training."""
import concurrent.futures, hashlib, json, pathlib, re, sys, time
from core import BASE,LANGUAGES,Store,canonical,digest,now,write_json
SYS="""Write natural USER requests for an LLM from complete frozen task seeds. Return JSON only; do not use tools.
Resolve authoring conditions against this actual source before writing. Do not mention alternative input formats or branches that are not part of the user task.\nDo not answer the request. Do not invent answer-bearing facts. The supplied content is appended verbatim by software AFTER your request, so refer to it naturally but do not copy it or rewrite it. Do not include curator labels, references, expected refusal behaviour, task taxonomy, difficulty labels or grading rubrics.
Use the assigned language; Greeklish means Greek transliterated into Latin characters in the request only. Standard/formal/informal register and cooperative/frustrated/skeptical/playful attitude change natural wording, not the task, facts or harmfulness. No biography is needed. Frustration must not invent prior model failures.
Every request must be direct, self-contained with the attached content, and preserve ALL operations and constraints in instruction_spec. Dates, units, unknowns and logical conditions must agree with the source.
Dialogue slots: generate ONLY the initial user request. Never fabricate assistant history, prior errors or prior correct answers. Start the underlying task naturally; its later dialogue goal will be enacted against actual Apertus responses.
Source passages describe bounded fictional or formal settings; do not pretend that fictional facts are real-world claims. Creative tasks can invite invention only within their explicit permissions.
"""
REVIEW="""Independently review these proposed USER requests and the exact appended source content against their frozen task specification.
Return JSON only; no tools. Do not rewrite the request. A rejected request will be repaired in a separate call and reviewed again.
Check: direct request; actual primary task/underlying operation; every constraint; all answer-bearing facts; answerability and deliberate premise; target language and intentional register; natural user attitude; no leaked private oracle, rubric, safety-category annotation or hidden answer.
Judge the request + source as a whole. A Greek request may refer to mathematical notation or an English/structured source; do not require translated quotations. Greeklish user text is intentional. Do not demand irrelevant biography.
For dialogue assess an opening only, not achievement of the later interaction goal. No fabricated assistant turns are permitted.
Be strict about scope drift (e.g. asking for the solution instead of the specified revision), implicit extra constraints, accidentally revealed answers, and fake variation. Private reference data is supplied for correctness checking; it must not leak into user messages.
Set accepted false on any substantive issue. Report observed task, language, register and attitude using the supplied allowed labels; matching labels are not enough to approve a bad prompt.
"""
def schema(review=False):
 props={"id":{"type":"string"}}
 if review:
  props.update({"accepted":{"type":"boolean"},"issues":{"type":"array","items":{"type":"string"}},"observed_purpose":{"type":"string"},"observed_language":{"type":"string"},"observed_register":{"type":"string"},"observed_attitude":{"type":"string"},"rationale":{"type":"string"}})
 else:props.update({"request":{"type":"string"}})
 return {"type":"object","properties":{"items":{"type":"array","items":{"type":"object","properties":props,"required":list(props),"additionalProperties":False}}},"required":["items"],"additionalProperties":False}
def public_packet(seed):
 f=seed["fixture"]
 # Crucially exclude constructive parameters and reference/check answers.
 return {"id":seed["id"],"purpose":seed["purpose"],"underlying_family":seed["underlying_family"],"language":seed["language"],"language_name":LANGUAGES[seed["language"]],"register":seed["register"],"attitude":seed["attitude"],"difficulty":seed["difficulty"],"instruction_spec":f["instruction_spec"],"source_content":f["content"],"dialogue_opening_only":seed["purpose"]=="dialogue"}
def assemble(seed,request):
 return {"messages":[{"role":"user","content":request.strip()+"\n\n---\n"+seed["fixture"]["content"]}],"request":request.strip(),"source_hash":seed["content_hash"]}
def structural(seed,candidate):
 errors=[];request=candidate.get("request","")
 if not isinstance(request,str) or not request.strip():return ["empty request"]
 if len(request)>6000:errors.append("request too long")
 if seed.get("source_kind")=="forum_import":
  return [] if candidate.get("messages")==seed["fixed_messages"] else ["forum source changed"]
 if candidate.get("messages")!=assemble(seed,request)["messages"]:errors.append("immutable source or message structure changed")
 if candidate.get("source_hash")!=seed["content_hash"]:errors.append("source hash mismatch")
 if re.search(r"\b(?:instruction_spec|private_reference|expected_response|observed_purpose)\b",request,re.I):errors.append("metadata leakage")
 # Script screen catches gross accidental language contamination, not fluency.
 letters=[c for c in request if c.isalpha()]; greek=sum("\u0370"<=c<="\u03ff" or "\u1f00"<=c<="\u1fff" for c in letters)
 if seed["language"]=="el" and seed["register"]!="greeklish" and letters and greek/len(letters)<.35:errors.append("Greek request script mismatch")
 if seed["language"]!="el" and letters and greek/len(letters)>.25:errors.append("unexpected Greek request script")
 return errors
class Worker:
 def __init__(self,store,run_id,output,server=None):
  self.store=store;self.rid=run_id;self.config=store.config(run_id);self.output=pathlib.Path(output);self.output.mkdir(parents=True,exist_ok=True);self.server=server;self.owns=False
 def start(self):
  if self.server is None:
   sys.path.insert(0,str(BASE.parent.parent/"math"))
   from codex_server import CodexServer
   self.server=CodexServer(cwd=str(self.output));self.server.start();self.owns=True
 def call(self,stage,packets,attempt):
  sc=schema(stage=="review");prompt=(REVIEW if stage=="review" else SYS)+"\nPACKETS\n"+canonical(packets)
  key=digest({"run":self.rid,"stage":stage,"packets":packets,"attempt":attempt,"model":self.config["model"],"effort":self.config["effort"],"schema":sc})
  cached=self.store.reserve_call(self.rid,stage,key)
  if cached is not None:return cached["items"]
  t=time.monotonic()
  try:
   response=self.server.call(prompt,sc,model=self.config["model"],effort=self.config["effort"],timeout=900)
   items=response["items"];expected=[p["id"] for p in packets];got=[r["id"] for r in items]
   if len(got)!=len(expected) or set(got)!=set(expected):raise ValueError("provider IDs missing, duplicated or unexpected")
   write_json(self.output/"calls"/(key+".json"),{"key":key,"stage":stage,"attempt":attempt,"ids":expected,"model":self.config["model"],"effort":self.config["effort"],"seconds":round(time.monotonic()-t,2),"prompt_sha256":hashlib.sha256(prompt.encode()).hexdigest(),"response":response,"created":now()})
   self.store.finish_call(key,response);print(canonical({"stage":stage,"ids":expected,"seconds":round(time.monotonic()-t,1)}),flush=True)
   return items
  except Exception as e:self.store.finish_call(key,error=str(e));raise
 def process_batch(self,rows):
  pending=[r for r in rows if r["attempts"]<self.config["max_repairs"]+1 or r["status"]=="generated"]
  if not pending:return len(rows)
  for attempt in range(self.config["max_repairs"]+1):
   needs=[r for r in pending if r["status"]!="generated"]
   if needs:
    packets=[]
    for r in needs:
     p=public_packet(r["seed"])
     if r["review"]:p["previous_issues"]=r["review"].get("issues",[]);p["previous_request"]=(r["generated"] or {}).get("request")
     packets.append(p)
    items=self.call("generate",packets,attempt);byid={x["id"]:x for x in items}
    for r in needs:
     gen=assemble(r["seed"],byid[r["id"]]["request"]);self.store.record(self.rid,r["id"],"generated",generated=gen);r.update(status="generated",generated=gen,attempts=r["attempts"]+1)
   packets=[]
   for r in pending:
    packets.append({"id":r["id"],"seed":public_packet(r["seed"]),"candidate":r["generated"],"private_reference":r["seed"]["fixture"]["reference"],"premise_status":r["seed"]["fixture"]["premise_status"]})
   reviews={x["id"]:x for x in self.call("review",packets,attempt)}
   again=[]
   # Exact text duplicate check covers this run and every previously accepted request in the registry.
   with self.store.db() as d:
    taken={digest(json.loads(x[0])["messages"]) for x in d.execute("SELECT generated FROM slots WHERE status IN ('accepted','opening_accepted','dialogue_ready') AND generated IS NOT NULL")}
   for r in pending:
    rev=reviews[r["id"]];issues=list(rev["issues"]);issues+=structural(r["seed"],r["generated"])
    for axis in ("purpose","language","register","attitude"):
     if rev["observed_"+axis]!=r["seed"][axis]:issues.append("observed "+axis+" mismatch")
    textkey=digest(r["generated"]["messages"])
    if textkey in taken:issues.append("duplicate final request")
    accepted=rev["accepted"] and not issues
    rev["issues"]=issues;rev["accepted"]=accepted;rev["reviewed_utc"]=now()
    status=("opening_accepted" if r["seed"]["purpose"]=="dialogue" else "accepted") if accepted else "rejected"
    self.store.record(self.rid,r["id"],status,review=rev);r.update(status=status,review=rev)
    if accepted:taken.add(textkey)
    elif r["seed"].get("source_kind")!="forum_import":again.append(r)
   pending=again
   pending=[r for r in pending if r["attempts"]<self.config["max_repairs"]+1]
   if not pending:break
  return len(pending)
 def run(self):
  token=self.store.claim_run(self.rid)
  errors=[]
  try:
   rows=[r for r in self.store.rows(self.rid) if r["status"] not in ("accepted","opening_accepted","dialogue_ready") and (self.config["generate_dialogue_openings"] or r["seed"]["purpose"]!="dialogue") and not (r["seed"].get("source_kind")=="forum_import" and r["status"]=="rejected")]
   if not rows:return self.store.export(self.rid,self.output)
   self.start()
   batches=[]
   for lang in LANGUAGES:
    group=[r for r in rows if r["seed"]["language"]==lang]
    for i in range(0,len(group),self.config["batch_size"]):batches.append(group[i:i+self.config["batch_size"]])
   with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["concurrency"]) as ex:
    futures=[ex.submit(self.process_batch,b) for b in batches]
    errors=[]
    for f in concurrent.futures.as_completed(futures):
     try:f.result()
     except Exception as e:errors.append(str(e))
   usage_path=self.output/"usage_events.json"
   previous_usage=json.loads(usage_path.read_text()) if usage_path.exists() else []
   write_json(usage_path,previous_usage+getattr(self.server,"usage",[]))
   result=self.store.export(self.rid,self.output);result["worker_errors"]=errors;write_json(self.output/"worker_result.json",result)
   return result
  except Exception as e:
   errors.append(str(e));write_json(self.output/"worker_error.json",{"error":str(e),"created":now()});raise
  finally:
   if self.owns:self.server.close()
   self.store.release_run(self.rid,token,status="needs_attention" if errors else "single_turn_ready" if self.store.report(self.rid)["all_non_dialogue_accepted"] else "needs_review")
   final_report=self.store.export(self.rid,self.output)
   if "result" in locals():
    result.update(final_report);write_json(self.output/"worker_result.json",result)
