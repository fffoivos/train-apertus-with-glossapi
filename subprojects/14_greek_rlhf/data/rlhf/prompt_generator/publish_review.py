"""Publish a local read-only review snapshot. No model calls and no deployment."""
import argparse,collections,json,pathlib
from core import Store,now,write_json
def publish(store,rid,site):
 rows=store.rows(rid);report=store.report(rid)
 payload={"snapshot_utc":now(),"report":report,"rows":[{"id":r["id"],"purpose":r["seed"]["purpose"],"family":r["seed"]["family"],"language":r["seed"]["language"],"attitude":r["seed"]["attitude"],"register":r["seed"]["register"],"difficulty":r["seed"]["difficulty"],"status":r["status"],"structure":r["seed"]["fixture"].get("structure_id","forum/import"),"topic":r["seed"]["fixture"].get("topic","natural source"),"parameters":r["seed"]["fixture"].get("parameters",{}),"source":r["seed"]["fixture"]["content"],"specification":r["seed"]["fixture"]["instruction_spec"],"request":(r["generated"] or {}).get("request"),"messages":(r["generated"] or {}).get("messages"),"review":r["review"],"attempts":r["attempts"]} for r in rows],"limits":["100-slot exact programme plan; 65 single-turn requests accepted; 35 dialogues deferred.","35 dialogue slots deferred until the single-turn API handoff to Fable.","Constructed source fixtures are narrower than the full design; this pilot is not evidence of 10,000-prompt semantic coverage.","Separate Sol review is not human or cross-model validation. Difficulty is designed, not model-calibrated.","No training eligibility or target-model preference yield has been established."]}
 write_json(pathlib.Path(site)/"live-pilot.json",payload)
 return payload
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--db",required=True);p.add_argument("--run",required=True);p.add_argument("--site",required=True);a=p.parse_args();publish(Store(a.db),a.run,a.site)
