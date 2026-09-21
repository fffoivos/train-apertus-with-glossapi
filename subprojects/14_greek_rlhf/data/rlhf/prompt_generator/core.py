"""Versioned prompt plans, SQLite reservations and accepted-output accounting."""
from __future__ import annotations
import collections, contextlib, datetime, hashlib, json, math, pathlib, random, re, sqlite3, uuid
from fractions import Fraction
BASE=pathlib.Path(__file__).resolve().parent
VERSION="prompt-generator-0.1"
DESIGN=json.loads((BASE/"design.json").read_text())
LANGUAGES={"el":"Greek","en":"English","fr":"French","de":"German","es":"Spanish","it":"Italian","pt":"Portuguese"}
PURPOSES=DESIGN["purpose_shares"]
DIALOGUE_GOALS=["followup","revision","constraint_retention","constraint_revocation","recall","error_recovery","false_correction","uncertainty"]
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def digest(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write_json(p,x):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+"."+uuid.uuid4().hex+".tmp");tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n");tmp.replace(p)
def apportion(weights,n):
 if isinstance(n,bool) or not isinstance(n,int) or n<0:raise ValueError("size must be a nonnegative integer")
 if not weights or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in weights.values()) or sum(weights.values())<=0:raise ValueError("invalid weights")
 total=sum(Fraction(str(v)) for v in weights.values()); raw={k:Fraction(str(v))*n/total for k,v in weights.items()}
 out={k:int(v) for k,v in raw.items()}
 for k in sorted(weights,key=lambda k:-(raw[k]-out[k]))[:n-sum(out.values())]:out[k]+=1
 return out
def minimum_exact_size(*axes):
 denoms=[(Fraction(str(v))/sum(Fraction(str(z)) for z in a.values())).denominator for a in axes for v in a.values()]
 return math.lcm(*denoms)
def default_config(n=100,seed=9162026):
 return dict(size=n,seed=seed,purpose_weights=PURPOSES,language_weights=DESIGN["language_default"],attitude_weights=DESIGN["attitude_default"],register_weights=DESIGN["register_default"],difficulty_weights=DESIGN["difficulty_default"],max_calls=48,batch_size=8,concurrency=3,max_repairs=2,split="development",programme="pilot100-v1",max_instances_per_structure=40,model="gpt-5.6-sol",effort="high",generate_dialogue_openings=False)
def checked_config(raw):
 c=default_config();unknown=set(raw)-set(c)-{"task_language_counts"}
 if unknown:raise ValueError("unknown configuration keys: "+str(sorted(unknown)))
 c.update(raw)
 for key,low,high in [("size",1,100000),("batch_size",1,12),("concurrency",1,8),("max_calls",0,10000),("max_repairs",0,3),("max_instances_per_structure",1,1000)]:
  if type(c[key]) is not int or not low<=c[key]<=high:raise ValueError(f"{key} outside {low}..{high}")
 if type(c["seed"]) is not int:raise ValueError("seed must be integer")
 for key,allowed in [("purpose_weights",PURPOSES),("language_weights",LANGUAGES),("attitude_weights",DESIGN["attitude_default"]),("register_weights",DESIGN["register_default"]),("difficulty_weights",DESIGN["difficulty_default"])]:
  if set(c[key])!=set(allowed):raise ValueError(f"{key}: exact supported labels required")
  apportion(c[key],c["size"])
 if type(c["generate_dialogue_openings"]) is not bool:raise ValueError("generate_dialogue_openings must be boolean")
 if c["model"]!="gpt-5.6-sol" or c["effort"] not in ("medium","high"):raise ValueError("unsupported provider configuration")
 if c["split"] not in ("development","train","holdout"):raise ValueError("unknown split")
 if not isinstance(c["programme"],str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}",c["programme"]):raise ValueError("invalid programme")
 if apportion(c["register_weights"],c["size"])["greeklish"]>apportion(c["language_weights"],c["size"])["el"]:raise ValueError("Greeklish quota exceeds Greek")
 return c
def spread(rows,key,counts,rng,allowed=None):
 values=[k for k,v in counts.items() for _ in range(v)]
 if len(values)!=len(rows):raise ValueError("axis counts disagree")
 rng.shuffle(values); order=list(range(len(rows)));rng.shuffle(order)
 # Greeklish is assigned only to Greek rows before the unrestricted registers.
 if key=="register":
  greek=[i for i in order if rows[i]["language"]=="el"];n=counts.get("greeklish",0)
  for i in greek[:n]:rows[i][key]="greeklish"
  order=[i for i in order if key not in rows[i]]; values=[v for v in values if v!="greeklish"]
 for i,v in zip(order,values):rows[i][key]=v
def make_slots(config):
 c=checked_config(config);rng=random.Random(c["seed"]);quotas=apportion(c["purpose_weights"],c["size"]);rows=[]
 for purpose,n in quotas.items():
  if purpose=="dialogue":
   fs={goal:1 for goal in DIALOGUE_GOALS}
  else:fs={f["id"]:f["share_within_purpose"] for f in DESIGN["families"] if f["purpose"]==purpose}
  for family,count in apportion(fs,n).items():
   for _ in range(count):rows.append(dict(purpose=purpose,family=family))
 rng.shuffle(rows)
 joint=c.get("task_language_counts")
 if joint is not None:
  if set(joint)!=set(PURPOSES):raise ValueError("joint table must include every purpose")
  total=collections.Counter()
  for p,n in quotas.items():
   counts=joint[p]
   if set(counts)-set(LANGUAGES) or any(type(v)is not int or v<0 for v in counts.values()) or sum(counts.values())!=n:raise ValueError("bad joint table")
   total.update(counts);spread([r for r in rows if r["purpose"]==p],"language",counts,rng)
  if dict(total)!=apportion(c["language_weights"],c["size"]):raise ValueError("joint language margins mismatch")
 else:spread(rows,"language",apportion(c["language_weights"],c["size"]),rng)
 for axis in ("attitude","register","difficulty"):spread(rows,axis,apportion(c[axis+"_weights"],c["size"]),rng)
 branch_index=0
 for r in rows:
  if r["family"]=="if_conditional":r["required_branch"]="full" if branch_index%2 else "open";branch_index+=1
 for i,r in enumerate(rows):r["id"]=f"S{i+1:04d}";r["index"]=i
 return c,rows
def content_family_key(family,fixture):
 if fixture.get("content_family"):return fixture["content_family"]
 params=fixture["parameters"]
 if "record" in params:return digest({"kind":"fictional_record","record":params["record"]})
 if family=="f_closed" and "element_symbol" in params:return "nist-element:"+params["element_symbol"]
 return digest({"family":family,"parameters":params})
class Store:
 def __init__(self,path):
  self.path=str(path);pathlib.Path(path).parent.mkdir(parents=True,exist_ok=True)
  with self.db() as d:
   d.executescript("""
   CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, created TEXT, config TEXT, status TEXT, worker_claim TEXT);
   CREATE TABLE IF NOT EXISTS slots(run TEXT,id TEXT,seed TEXT,status TEXT,generated TEXT,review TEXT,attempts INTEGER DEFAULT 0,PRIMARY KEY(run,id));
   CREATE TABLE IF NOT EXISTS instances(hash TEXT PRIMARY KEY, programme TEXT,structure TEXT,content_family TEXT,split TEXT,run TEXT,slot TEXT);
   CREATE TABLE IF NOT EXISTS content_families(id TEXT PRIMARY KEY,split TEXT);
   CREATE TABLE IF NOT EXISTS calls(key TEXT PRIMARY KEY,run TEXT,stage TEXT,status TEXT,created TEXT,response TEXT,error TEXT);
   CREATE TABLE IF NOT EXISTS revisions(id INTEGER PRIMARY KEY AUTOINCREMENT,run TEXT,slot TEXT,created TEXT,reviewer TEXT,issues TEXT,previous TEXT);
   CREATE TABLE IF NOT EXISTS accepted_texts(hash TEXT PRIMARY KEY,run TEXT,slot TEXT,UNIQUE(run,slot));
   CREATE TABLE IF NOT EXISTS imported_sources(id TEXT PRIMARY KEY,payload TEXT);
   CREATE TABLE IF NOT EXISTS dialogues(run TEXT,slot TEXT,payload TEXT,PRIMARY KEY(run,slot));
   """)
 @contextlib.contextmanager
 def db(self):
  d=sqlite3.connect(self.path,timeout=30);d.row_factory=sqlite3.Row;d.execute("PRAGMA foreign_keys=ON");d.execute("PRAGMA busy_timeout=30000")
  try:
   with d:yield d
  finally:d.close()
 def create(self,config,run_id=None):
  import fixtures
  c,rows=make_slots(config);rid=run_id or uuid.uuid4().hex[:16]
  if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}",rid):raise ValueError("bad run id")
  with self.db() as d:
   d.execute("BEGIN IMMEDIATE")
   if d.execute("SELECT 1 FROM runs WHERE id=?",(rid,)).fetchone():raise ValueError("run exists; resume by ID")
   d.execute("INSERT INTO runs VALUES(?,?,?,?,NULL)",(rid,now(),canonical(c),"planned"))
   for r in rows:
    for variant in range(1000):
     rng=random.Random(int(digest([c["seed"],r["index"],variant]),16))
     family=r["family"] if r["purpose"]!="dialogue" else ["e_plan","e_edit","e_explain","s_general","m_arithmetic"][r["index"]%5]
     fixture=fixtures.build(family,rng,r["difficulty"],r["language"])
     if r.get("required_branch") and fixture["reference"].get("branch")!=r["required_branch"]:continue
     errors=fixtures.validate(fixture)
     if errors:raise ValueError(f"invalid fixture {family}: {errors}")
     inst=digest({"structure":fixture["structure_id"],"parameters":fixture["parameters"],"dialogue_goal":r["family"] if r["purpose"]=="dialogue" else None})
     content_family=content_family_key(family,fixture)
     split=d.execute("SELECT split FROM content_families WHERE id=?",(content_family,)).fetchone()
     if split and split["split"]!=c["split"]:continue
     if d.execute("SELECT 1 FROM instances WHERE hash=?",(inst,)).fetchone():continue
     count=d.execute("SELECT count(*) FROM instances WHERE programme=? AND structure=?",(c["programme"],fixture["structure_id"])).fetchone()[0]
     if count>=c["max_instances_per_structure"]:raise ValueError("structure capacity exhausted: "+fixture["structure_id"])
     seed={**r,"version":VERSION,"underlying_family":family,"fixture":fixture,"instance_hash":inst,"content_family":content_family,"content_hash":digest(fixture["content"]),"source_kind":"constructed","split":c["split"]}
     if r["purpose"]=="dialogue":
      seed["dialogue"]={"goal":r["family"],"assistant_origin":"target_checkpoint_only","state":"awaiting_opening","max_assistant_turns":4,"trigger":"verified actual error" if r["family"]=="error_recovery" else "verified correct answer challenged" if r["family"]=="false_correction" else "actual transcript and constraint state"}
     d.execute("INSERT OR IGNORE INTO content_families VALUES(?,?)",(content_family,c["split"]))
     d.execute("INSERT INTO instances VALUES(?,?,?,?,?,?,?)",(inst,c["programme"],fixture["structure_id"],content_family,c["split"],rid,r["id"]))
     d.execute("INSERT INTO slots(run,id,seed,status) VALUES(?,?,?,?)",(rid,r["id"],canonical(seed),"planned"));break
    else:raise ValueError("no unused valid instance available")
  return self.report(rid)
 def config(self,rid):
  with self.db() as d:r=d.execute("SELECT config FROM runs WHERE id=?",(rid,)).fetchone()
  if not r:raise KeyError("unknown run")
  return json.loads(r[0])
 def rows(self,rid):
  with self.db() as d:rs=d.execute("SELECT * FROM slots WHERE run=? ORDER BY id",(rid,)).fetchall()
  return [{**dict(r),"seed":json.loads(r["seed"]),"generated":json.loads(r["generated"]) if r["generated"] else None,"review":json.loads(r["review"]) if r["review"] else None} for r in rs]
 def report(self,rid):
  c=self.config(rid);rs=self.rows(rid);accepted=[r for r in rs if r["status"] in ("accepted","opening_accepted","dialogue_ready")]
  def counts(rows,axis):return dict(collections.Counter(r["seed"][axis] for r in rows))
  planned={a:counts(rs,a) for a in ("purpose","language","attitude","register","difficulty")}
  actual={a:counts(accepted,a) for a in planned}
  with self.db() as d:
   calls=dict(collections.Counter(r[0] for r in d.execute("SELECT status FROM calls WHERE run=?",(rid,))));state=dict(d.execute("SELECT status,worker_claim FROM runs WHERE id=?",(rid,)).fetchone())
  return dict(version=VERSION,run_id=rid,size=c["size"],state=state,planned=planned,accepted=actual,status_counts=dict(collections.Counter(r["status"] for r in rs)),calls=calls,accepted_openings_and_single_turn=len(accepted),accepted_single_turn=sum(r["status"]=="accepted" for r in rs),all_non_dialogue_accepted=all(r["status"]=="accepted" for r in rs if r["seed"]["purpose"]!="dialogue"),completed_dialogues=sum(r["status"]=="dialogue_ready" for r in rs),all_slots_reviewed=len(accepted)==len(rs),full_dialogue_distribution_realised=all(r["status"]=="dialogue_ready" for r in rs if r["seed"]["purpose"]=="dialogue"),training_eligible=False)
 def claim_run(self,rid):
  token=uuid.uuid4().hex
  with self.db() as d:
   if d.execute("UPDATE runs SET worker_claim=?,status='running' WHERE id=? AND worker_claim IS NULL",(token,rid)).rowcount!=1:raise ValueError("run busy; recover explicitly after checking worker")
  return token
 def release_run(self,rid,token,status="idle"):
  with self.db() as d:d.execute("UPDATE runs SET worker_claim=NULL,status=? WHERE id=? AND worker_claim=?",(status,rid,token))
 def record(self,rid,sid,status,generated=None,review=None):
  if status not in ("generated","rejected","accepted","opening_accepted"):raise ValueError("unsupported slot transition")
  with self.db() as d:
   d.execute("BEGIN IMMEDIATE")
   row=d.execute("SELECT * FROM slots WHERE run=? AND id=?",(rid,sid)).fetchone()
   if row is None:raise ValueError("unknown slot")
   if row["status"] in ("accepted","opening_accepted","dialogue_ready"):raise ValueError("accepted slots are immutable")
   seed=json.loads(row["seed"]);gen=generated if generated is not None else (json.loads(row["generated"]) if row["generated"] else None)
   rev=review if review is not None else (json.loads(row["review"]) if row["review"] else None)
   if status in ("generated","accepted","opening_accepted"):
    if not isinstance(gen,dict) or not gen.get("messages") or not isinstance(gen.get("request"),str):raise ValueError("generated messages required")
    if seed.get("source_kind")=="forum_import":
     if gen["messages"]!=seed["fixed_messages"]:raise ValueError("forum source changed")
    elif gen["messages"]!=[{"role":"user","content":gen["request"].strip()+"\n\n---\n"+seed["fixture"]["content"]}] or gen.get("source_hash")!=seed["content_hash"]:raise ValueError("source/message mismatch")
   if status in ("accepted","opening_accepted"):
    if not rev or rev.get("accepted") is not True or rev.get("issues"):raise ValueError("passing review required")
    if any(rev.get("observed_"+axis)!=seed[axis] for axis in ("purpose","language","register","attitude")):raise ValueError("observed quota labels mismatch")
    if (status=="opening_accepted")!=(seed["purpose"]=="dialogue"):raise ValueError("dialogue status mismatch")
    try:d.execute("INSERT INTO accepted_texts VALUES(?,?,?)",(digest(gen["messages"]),rid,sid))
    except sqlite3.IntegrityError:raise ValueError("duplicate accepted text")
   d.execute("UPDATE slots SET status=?,generated=COALESCE(?,generated),review=COALESCE(?,review),attempts=attempts+? WHERE run=? AND id=?",(status,canonical(generated) if generated is not None else None,canonical(review) if review is not None else None,int(status=="generated"),rid,sid))
 def request_revision(self,rid,sid,issues,reviewer,fixture_replacement=None):
  if not reviewer or not issues or not all(isinstance(x,str) and x.strip() for x in issues):raise ValueError("reviewer and concrete issues required")
  with self.db() as d:
   d.execute("BEGIN IMMEDIATE")
   run=d.execute("SELECT worker_claim FROM runs WHERE id=?",(rid,)).fetchone()
   if not run or run[0]:raise ValueError("unknown or active run")
   row=d.execute("SELECT * FROM slots WHERE run=? AND id=?",(rid,sid)).fetchone()
   if not row or row["status"] not in ("accepted","opening_accepted"):raise ValueError("accepted slot required for revision")
   seed=json.loads(row["seed"])
   if seed.get("source_kind")=="forum_import":raise ValueError("forum text is immutable; replace the source through a reviewed import")
   d.execute("INSERT INTO revisions(run,slot,created,reviewer,issues,previous) VALUES(?,?,?,?,?,?)",(rid,sid,now(),reviewer,canonical(issues),canonical(dict(row))))
   if fixture_replacement is not None:
    import fixtures
    problems=fixtures.validate(fixture_replacement)
    if problems:raise ValueError("replacement fixture invalid: "+str(problems))
    if fixture_replacement["structure_id"].split("/")[0]!=seed["underlying_family"]:raise ValueError("replacement changes task family")
    oldhash=seed["instance_hash"]
    newhash=digest({"structure":fixture_replacement["structure_id"],"parameters":fixture_replacement["parameters"],"dialogue_goal":seed["family"] if seed["purpose"]=="dialogue" else None})
    if newhash!=oldhash:
     if d.execute("SELECT 1 FROM instances WHERE hash=?",(newhash,)).fetchone():raise ValueError("replacement instance already used")
     d.execute("UPDATE instances SET hash=? WHERE run=? AND slot=?",(newhash,rid,sid))
    familykey=content_family_key(seed["underlying_family"],fixture_replacement)
    splitrow=d.execute("SELECT split FROM content_families WHERE id=?",(familykey,)).fetchone()
    if splitrow and splitrow[0]!=seed["split"]:raise ValueError("replacement crosses content-family split")
    d.execute("INSERT OR IGNORE INTO content_families VALUES(?,?)",(familykey,seed["split"]))
    d.execute("UPDATE instances SET content_family=?,structure=? WHERE run=? AND slot=?",(familykey,fixture_replacement["structure_id"],rid,sid))
    seed.update(fixture=fixture_replacement,instance_hash=newhash,content_family=familykey,content_hash=digest(fixture_replacement["content"]))
    d.execute("UPDATE slots SET seed=? WHERE run=? AND id=?",(canonical(seed),rid,sid))
   rev=json.loads(row["review"]);rev.update(accepted=False,issues=issues,revision_reviewer=reviewer,revision_requested_utc=now())
   d.execute("DELETE FROM accepted_texts WHERE run=? AND slot=?",(rid,sid))
   d.execute("UPDATE slots SET status='rejected',review=? WHERE run=? AND id=?",(canonical(rev),rid,sid))
   d.execute("UPDATE runs SET status='needs_review' WHERE id=?",(rid,))
  return self.report(rid)
 def reserve_call(self,rid,stage,key):
  with self.db() as d:
   d.execute("BEGIN IMMEDIATE");old=d.execute("SELECT * FROM calls WHERE key=?",(key,)).fetchone()
   if old:
    if old["run"]!=rid or old["stage"]!=stage:raise ValueError("call key belongs to another run or stage")
    if old["status"]=="complete":return json.loads(old["response"])
    raise ValueError("call is already reserved/failed; inspect before explicit retry: "+key)
   c=json.loads(d.execute("SELECT config FROM runs WHERE id=?",(rid,)).fetchone()[0]);n=d.execute("SELECT count(*) FROM calls WHERE run=?",(rid,)).fetchone()[0]
   if n>=c["max_calls"]:raise ValueError("model-call budget exhausted")
   d.execute("INSERT INTO calls VALUES(?,?,?,?,?,?,?)",(key,rid,stage,"reserved",now(),None,None))
  return None
 def finish_call(self,key,response=None,error=None):
  with self.db() as d:d.execute("UPDATE calls SET status=?,response=?,error=? WHERE key=?",("failed" if error else "complete",canonical(response) if response is not None else None,error,key))
 def export(self,rid,path):
  p=pathlib.Path(path);p.mkdir(parents=True,exist_ok=True);rs=self.rows(rid)
  public=[];openings=[];curator=[]
  for r in rs:
   if r["status"] not in ("accepted","opening_accepted","dialogue_ready"):continue
   item={"id":r["id"],"messages":r["generated"]["messages"]}
   if r["seed"]["purpose"]=="dialogue":
    if r["status"]=="dialogue_ready":
     with self.db() as d:payload=json.loads(d.execute("SELECT payload FROM dialogues WHERE run=? AND slot=?",(rid,r["id"])).fetchone()[0])
     item["messages"]=payload["messages"];public.append(item)
    else:openings.append({**item,"dialogue_spec":r["seed"]["dialogue"],"instance_hash":r["seed"]["instance_hash"]})
   else:public.append(item)
   curator.append(r)
  for name,items in [("model_requests.jsonl",public),("dialogue_openings.jsonl",openings),("curator.jsonl",curator)]:
   (p/name).write_text("".join(canonical(x)+"\n" for x in items))
  with self.db() as d:
   history=[dict(x) for x in d.execute("SELECT * FROM revisions WHERE run=? ORDER BY id",(rid,))]
  (p/"revision_history.jsonl").write_text("".join(canonical(x)+"\n" for x in history))
  write_json(p/"manifest_final.json",{"config":self.config(rid),"seeds":[r["seed"] for r in rs]})
  write_json(p/"report.json",self.report(rid))
  write_json(p/"receipt.json",{"version":VERSION,"run_id":rid,"exported_utc":now(),"config":self.config(rid),"sha256":{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in p.glob("*.jsonl")},"training_eligible":False})
  return self.report(rid)
 def import_dialogue(self,rid,sid,payload):
  row=next((r for r in self.rows(rid) if r["id"]==sid),None)
  if not row or row["status"]!="opening_accepted":raise ValueError("reviewed dialogue opening required")
  ms=payload.get("messages",[]);ev=payload.get("assistant_receipts",[])
  if len(ms)<3 or len(ms)%2!=1 or ms[0]!=row["generated"]["messages"][0]:raise ValueError("history must preserve opening and end in user")
  if any(m.get("role")!=("user" if i%2==0 else "assistant") or not isinstance(m.get("content"),str) or not m["content"].strip() for i,m in enumerate(ms)):raise ValueError("invalid transcript")
  if len(ev)!=len(ms)//2:raise ValueError("one provenance receipt per assistant required")
  checkpoint=payload.get("checkpoint_sha256","")
  if not re.fullmatch("[0-9a-f]{64}",checkpoint):raise ValueError("checkpoint SHA-256 required")
  for i,e in enumerate(ev):
   if e.get("origin")!="target_checkpoint" or e.get("checkpoint_sha256")!=checkpoint or e.get("content_sha256")!=hashlib.sha256(ms[2*i+1]["content"].encode()).hexdigest() or not e.get("sampling"):raise ValueError("assistant provenance mismatch")
  goal=row["seed"]["dialogue"]["goal"];verification=payload.get("goal_verification",{})
  if verification.get("goal")!=goal or verification.get("passed") is not True or not verification.get("evidence"):raise ValueError("verified goal evidence required")
  if goal in ("error_recovery","false_correction") and not verification.get("reference_check"):raise ValueError("correction goal requires independent reference check")
  with self.db() as d:
   d.execute("INSERT INTO dialogues VALUES(?,?,?)",(rid,sid,canonical(payload)));d.execute("UPDATE slots SET status='dialogue_ready' WHERE run=? AND id=?",(rid,sid))
  return {"status":"dialogue_ready","note":"Receipt consistency checked; provenance and semantic goal evidence remain reviewable, not cryptographically attested."}
