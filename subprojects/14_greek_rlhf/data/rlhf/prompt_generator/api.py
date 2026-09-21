#!/usr/bin/env python3
"""Loopback HTTP API and CLI; generation is explicit, bounded, resumable."""
import argparse, concurrent.futures, hmac, json, os, pathlib, secrets, sys, threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,parse_qs
from core import BASE,DESIGN,VERSION,Store,default_config,minimum_exact_size,write_json
from worker import Worker
from sources import import_forums,screen
OPENAPI={"openapi":"3.1.0","info":{"title":"RLHF Prompt Generator","version":VERSION},"servers":[{"url":"http://127.0.0.1:8769"}],"security":[{"localToken":[]}],"components":{"securitySchemes":{"localToken":{"type":"http","scheme":"bearer"}}},"paths":{}}
for path,methods in {
 "/health":["get"],"/openapi.json":["get"],"/v1/catalogue":["get"],"/v1/runs":["post"],
 "/v1/runs/{run_id}":["get"],"/v1/runs/{run_id}/seeds":["get"],
 "/v1/runs/{run_id}/generate":["post"],"/v1/runs/{run_id}/export":["post"],
 "/v1/runs/{run_id}/dialogue":["post"],"/v1/runs/{run_id}/forum-import":["post"],"/v1/runs/{run_id}/screen":["post"],"/v1/runs/{run_id}/revise":["post"]
}.items():
 OPENAPI["paths"][path]={m:{"summary":path.rsplit("/",1)[-1],"responses":{"200":{"description":"JSON result"},"400":{"description":"Invalid request"},"401":{"description":"Local token required"},"409":{"description":"State/constraint conflict"}}} for m in methods}
OPENAPI["paths"]["/v1/runs"]["post"]["requestBody"]={"required":True,"content":{"application/json":{"schema":{"type":"object","properties":{"config":{"type":"object"},"run_id":{"type":"string"}},"required":["config"],"additionalProperties":False}}}}
for path, required, props in [
 ("/v1/runs/{run_id}/revise",["slot_id","issues","reviewer"],{"slot_id":{"type":"string"},"issues":{"type":"array","items":{"type":"string"}},"reviewer":{"type":"string"},"fixture_replacement":{"type":"object"}}),
 ("/v1/runs/{run_id}/forum-import",["records"],{"records":{"type":"array","items":{"type":"object"}}}),
 ("/v1/runs/{run_id}/dialogue",["slot_id","payload"],{"slot_id":{"type":"string"},"payload":{"type":"object"}}),
]:
 OPENAPI["paths"][path]["post"]["requestBody"]={"required":True,"content":{"application/json":{"schema":{"type":"object","required":required,"properties":props}}}}
for path in ("/health","/openapi.json"):OPENAPI["paths"][path]["get"]["security"]=[]
for path in OPENAPI["paths"]:
 if "{run_id}" in path:
  OPENAPI["paths"][path]["parameters"]=[{"name":"run_id","in":"path","required":True,"schema":{"type":"string"}}]
def serve(state,port=8769,enable_generation=False):
 state=pathlib.Path(state);state.mkdir(parents=True,exist_ok=True);store=Store(state/"registry.sqlite")
 token_path=state/"api.token"
 if token_path.exists():token=token_path.read_text().strip()
 else:
  token=secrets.token_urlsafe(32);fd=os.open(token_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,"w") as f:f.write(token)
 pool=concurrent.futures.ThreadPoolExecutor(max_workers=1)
 jobs={};lock=threading.Lock()
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,fmt,*args):pass
  def send(self,code,body):
   data=json.dumps(body,ensure_ascii=False).encode();self.send_response(code);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Cache-Control","no-store");self.send_header("X-Content-Type-Options","nosniff");self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data)
  def auth(self):
   if self.headers.get("Origin") and self.headers["Origin"] not in (f"http://127.0.0.1:{port}",f"http://localhost:{port}"):return False
   return hmac.compare_digest(self.headers.get("Authorization",""),"Bearer "+token)
  def body(self):
   n=int(self.headers.get("Content-Length","0"))
   if not 0<n<=2_000_000:raise ValueError("request body length out of range")
   return json.loads(self.rfile.read(n))
  def do_GET(self):
   try:
    parsed=urlparse(self.path);parts=parsed.path.strip("/").split("/")
    if parsed.path=="/health":return self.send(200,{"status":"ok","version":VERSION,"generation_enabled":enable_generation})
    if parsed.path=="/openapi.json":return self.send(200,OPENAPI)
    if not self.auth():return self.send(401,{"error":"local bearer token required"})
    if parsed.path=="/v1/catalogue":return self.send(200,{"design":DESIGN,"minimum_exact_primary_and_language_size":minimum_exact_size(DESIGN["purpose_shares"],DESIGN["language_default"]),"coverage_note":"Family generators implement narrower subsets; see fixture source and release limits."})
    if len(parts)>=3 and parts[:2]==["v1","runs"]:
     rid=parts[2]
     if len(parts)==3:
      result=store.report(rid)
      with lock:
       job=jobs.get(rid)
       if job and job.done():
        error=job.exception()
        result["background_job"]={"state":"failed" if error else "finished","error":str(error) if error else None}
       elif job:result["background_job"]={"state":"running"}
      return self.send(200,result)
     if len(parts)==4 and parts[3]=="seeds":
      q=parse_qs(parsed.query);offset=max(0,int(q.get("offset",[0])[0]));limit=min(100,max(1,int(q.get("limit",[50])[0])))
      rs=store.rows(rid);return self.send(200,{"items":rs[offset:offset+limit],"total":len(rs),"offset":offset,"limit":limit})
    self.send(404,{"error":"unknown route"})
   except (ValueError,KeyError,TypeError) as e:self.send(400,{"error":str(e)})
   except Exception as e:self.send(500,{"error":type(e).__name__})
  def do_POST(self):
   try:
    if not self.auth():return self.send(401,{"error":"local bearer token required"})
    parts=urlparse(self.path).path.strip("/").split("/");body=self.body()
    if parts==["v1","runs"]:
     if set(body)-{"config","run_id"}:raise ValueError("unknown fields")
     return self.send(200,store.create(body["config"],body.get("run_id")))
    if len(parts)==4 and parts[:2]==["v1","runs"]:
     rid=parts[2];store.config(rid);action=parts[3]
     if action=="generate":
      if not enable_generation:return self.send(403,{"error":"server generation disabled; run worker explicitly or restart with --enable-generation"})
      with lock:
       if rid in jobs and not jobs[rid].done():return self.send(409,{"error":"worker already running"})
       jobs[rid]=pool.submit(Worker(store,rid,state/"runs"/rid).run)
      return self.send(202,{"run_id":rid,"status":"queued","poll":"/v1/runs/"+rid})
     if action=="revise":return self.send(200,store.request_revision(rid,body["slot_id"],body["issues"],body["reviewer"],body.get("fixture_replacement")))
     if action=="forum-import":return self.send(200,import_forums(store,rid,body["records"]))
     if action=="screen":return self.send(200,screen(store,rid,state/"runs"/rid))
     if action=="export":return self.send(200,store.export(rid,state/"runs"/rid))
     if action=="dialogue":return self.send(200,store.import_dialogue(rid,body["slot_id"],body["payload"]))
    self.send(404,{"error":"unknown route"})
   except (ValueError,KeyError,TypeError) as e:self.send(400,{"error":str(e)})
   except Exception as e:self.send(500,{"error":type(e).__name__})
 server=ThreadingHTTPServer(("127.0.0.1",port),Handler)
 print(json.dumps({"url":f"http://127.0.0.1:{port}","token_file":str(token_path),"generation_enabled":enable_generation}),flush=True)
 try:server.serve_forever()
 finally:server.server_close();pool.shutdown(wait=True)
def main():
 p=argparse.ArgumentParser();p.add_argument("--state",default=str(BASE/"runtime"));sub=p.add_subparsers(dest="cmd",required=True)
 s=sub.add_parser("plan");s.add_argument("--config");s.add_argument("--size",type=int,default=100);s.add_argument("--seed",type=int,default=9162026);s.add_argument("--run-id")
 for cmd in ("report","generate","export","screen"):
  s=sub.add_parser(cmd);s.add_argument("run_id")
 s=sub.add_parser("serve");s.add_argument("--port",type=int,default=8769);s.add_argument("--enable-generation",action="store_true")
 s=sub.add_parser("import-forums");s.add_argument("run_id");s.add_argument("jsonl")
 s=sub.add_parser("openapi")
 args=p.parse_args();state=pathlib.Path(args.state)
 if args.cmd=="serve":return serve(state,args.port,args.enable_generation)
 if args.cmd=="openapi":print(json.dumps(OPENAPI,indent=2));return
 store=Store(state/"registry.sqlite")
 if args.cmd=="plan":
  config=json.loads(pathlib.Path(args.config).read_text()) if args.config else default_config(args.size,args.seed)
  result=store.create(config,args.run_id)
 elif args.cmd=="generate":result=Worker(store,args.run_id,state/"runs"/args.run_id).run()
 elif args.cmd=="screen":result=screen(store,args.run_id,state/"runs"/args.run_id)
 elif args.cmd=="import-forums":result=import_forums(store,args.run_id,[json.loads(x) for x in pathlib.Path(args.jsonl).read_text().splitlines() if x.strip()])
 elif args.cmd=="export":result=store.export(args.run_id,state/"runs"/args.run_id)
 else:result=store.report(args.run_id)
 print(json.dumps(result,ensure_ascii=False,indent=2))
 if args.cmd=="generate" and (result.get("worker_errors") or not result.get("all_non_dialogue_accepted")):sys.exit(2)
if __name__=="__main__":main()
