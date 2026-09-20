#!/usr/bin/env python3
"""Experiment-owned source intake: one pinned OpenMath shard, original MATH families only."""
from pathlib import Path
import argparse,collections,hashlib,json,os,re,time,unicodedata,urllib.request
from datetime import datetime,timezone

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()
def norm(s):return ' '.join(re.sub(r'[^\w\s]',' ',''.join(c for c in unicodedata.normalize('NFD',s).lower() if not unicodedata.combining(c))).split())
def family(s):return hashlib.sha256(norm(s).encode()).hexdigest()
def load(p):return [json.loads(x)for x in Path(p).read_text().split('\n') if x]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--contract',required=True);ap.add_argument('--expected-contract-sha256',required=True);args=ap.parse_args();assert sha(Path(args.contract))==args.expected_contract_sha256,'Contract bytes differ from reviewed binding';c=json.loads(Path(args.contract).read_text());assert sha(Path(__file__))==c['implementation_sha256'],'Worker implementation differs from reviewed binding';out=Path(c['output_dir']);out.mkdir(parents=True,exist_ok=True);assert not any(out.iterdir()),'Output directory is not empty; preserve prior attempt and use a new bound output';start=time.time()
 for item in c['local_inputs']:
  assert sha(Path(item['path']))==item['sha256'],item['path']
 src=c['source'];target=Path(c['shard_path']);target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists():assert target.stat().st_size==src['bytes'] and sha(target)==src['sha256']
 else:
  tmp=target.with_suffix('.download');assert not tmp.exists(),'Prior partial download requires explicit review before reuse.'
  count=0
  with urllib.request.urlopen(src['url'],timeout=90) as response,tmp.open('xb') as f:
   for chunk in iter(lambda:response.read(1<<20),b''):
    count+=len(chunk);assert count<=src['bytes'],'Source exceeds frozen byte limit';f.write(chunk)
  assert count==src['bytes'] and sha(tmp)==src['sha256'];tmp.rename(target)
 # Stream bounded row batches; never materialize the whole shard or rewrite source files.
 import pyarrow.parquet as pq
 original={}
 for lineno,r in enumerate(load(c['math_train_path']),1):
  key=family(r['problem']);original.setdefault(key,[]).append({'line':lineno,'subject':r['type'],'level':r['level'],'problem':r['problem'],'record_sha256':hashlib.sha256(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()})
 inv={r['family_sha256']:r for r in load(c['family_inventory_path'])}
 held={r['family_sha256'] for r in load(c['split_path']) if r['lane'] in ('development','final_confirmation')}
 counts=collections.Counter();labels=collections.Counter();kept={};locator=0
 file=pq.ParquetFile(target)
 assert {'problem','generated_solution','expected_answer','problem_source'}<=set(file.schema_arrow.names)
 for batch in file.iter_batches(batch_size=512):
  for r in batch.to_pylist():
   rownum=locator;locator+=1;counts['source_rows']+=1;labels[str(r['problem_source'])]+=1;key=family(r['problem'])
   if key not in original:continue
   refs=[x for x in original[key] if ' '.join(x['problem'].split())==' '.join(r['problem'].split())]
   if not refs:counts['normalized_match_without_exact_original']+=1;continue
   counts['exact_original_math_rows']+=1;assert key in inv,'Exact original family absent from bound inventory: '+key;info=inv[key]
   if key in held or info['math500_gate']['reject'] or info['current_assembly']['appeared_in_development']:
    counts['held_or_benchmark_overlap']+=1;continue
   cells={(x['subject'],x['level'])for x in refs}
   if len(cells)!=1:counts['ambiguous_source_cell']+=1;continue
   if any((ord(ch)<32 and ch not in '\t\n\r')or ord(ch)==127 for t in (r['problem'],r['generated_solution']) for ch in t):counts['invalid_controls']+=1;continue
   if not r['generated_solution'].strip():counts['empty_solution']+=1;continue
   h=hashlib.sha256(r['generated_solution'].encode()).hexdigest();row={'id':f'openmath1m_{rownum}','family_sha256':key,'source_dataset':src['repo'],'source_revision':src['revision'],'source_split':'train_1M','source_file':src['file'],'source_file_sha256':src['sha256'],'row_index':rownum,'problem_source':r['problem_source'],'expected_answer':r['expected_answer'],'original_math_source':refs,'subject':refs[0]['subject'],'level':refs[0]['level'],'messages':[{'role':'user','content':r['problem']},{'role':'assistant','content':r['generated_solution']}],'solution_sha256':h,'status':'unreviewed_source_candidate'}
   pool=kept.setdefault(key,{});pool.setdefault(h,row)
   if len(pool)>2:del pool[max(pool)]
 # Content-free inventory of eligible families; one deterministic family per cell for full proof review.
 cells=collections.defaultdict(list)
 for key,pool in kept.items():
  row=next(iter(pool.values()));cells[(row['subject'],row['level'])].append(key)
 selected=[]
 for cell,keys in sorted(cells.items()):
  key=min(keys,key=lambda k:hashlib.sha256(('openmath-original-pilot-v1:'+k).encode()).hexdigest());selected.extend(kept[key][h] for h in sorted(kept[key]))
 (out/'candidate_rows.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in selected))
 (out/'eligible_family_inventory.jsonl').write_text(''.join(json.dumps({'family_sha256':k,'subject':next(iter(v.values()))['subject'],'level':next(iter(v.values()))['level'],'retained_solution_hashes':sorted(v)},ensure_ascii=False)+'\n'for k,v in sorted(kept.items())))
 receipt={'schema_version':'openmath_original_pilot_v1','status':'passed','finished_at':datetime.now(timezone.utc).isoformat(),'seconds':round(time.time()-start,3),'counts':dict(counts),'problem_source_counts':dict(labels),'eligible_families':len(kept),'covered_cells':len(cells),'pilot_rows':len(selected),'pilot_families':len({r['family_sha256']for r in selected}),'source':src,'files':{p.name:sha(p)for p in out.glob('*.jsonl')},'limits':'One first shard of the documented1M subset; not representative of the full source. Candidates need full proof/adaptation review, actual tokenizer length/mask checks and complete assembly decontamination. Exact source matching is not proof of correct generated solutions.'}
 Path(c['receipt_path']).parent.mkdir(parents=True,exist_ok=True);Path(c['receipt_path']).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
