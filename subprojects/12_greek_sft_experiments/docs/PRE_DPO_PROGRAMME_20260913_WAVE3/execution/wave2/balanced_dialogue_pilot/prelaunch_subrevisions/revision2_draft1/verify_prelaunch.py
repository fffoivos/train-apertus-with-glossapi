#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, json
from collections import Counter,defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent
RUNNER_SHA='c13862fd38c50facc721d385c9fcc3ea99a052719a52bf730d40490aa6b85005'
PROBE={'pilot48_01_true','pilot48_06_false','pilot48_10_partial','pilot48_03_unresolved'}
MISSING=object()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read_jsonl(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def strict(s,path='$'):
 if s.get('type')=='object' or 'properties' in s:
  assert s.get('additionalProperties') is False,path
  assert set(s.get('required',[]))==set(s.get('properties',{})),path
  for k,v in s.get('properties',{}).items(): strict(v,path+'.'+k)
 if 'items' in s: strict(s['items'],path+'[]')
def replay(initial,events):
 state=copy.deepcopy(initial)
 for e in events:
  if e['op']=='set':state[e['field']]=e['value']
  elif e['op']=='add':
   if isinstance(state.get(e['field']),list):
    if e['value'] not in state[e['field']]:state[e['field']].append(e['value'])
   else:state[e['field']]=state.get(e['field'],0)+e['value']
  elif e['op']=='remove':
   if isinstance(state.get(e['field']),list):state[e['field']]=[x for x in state[e['field']] if x!=e['value']]
   else:state.pop(e['field'],None)
  else:raise AssertionError(e)
 return state
def derive(e):
 state=copy.deepcopy(e['facts']);state.update(e.get('extra',{}))
 for f in e['formulas']:
  vals=[state.get(a) for a in f['args']]
  if any(v is None for v in vals):v=None
  elif f['op']=='add':v=sum(vals)
  elif f['op']=='subtract':v=vals[0]-vals[1]
  elif f['op']=='subtract_many':v=vals[0]-sum(vals[1:])
  elif f['op']=='equals':v=vals[0]==vals[1]
  elif f['op']=='greater_than':v=vals[0]>vals[1]
  elif f['op']=='graph_direct':
   edges=state[f['args'][2]];v=[vals[0],vals[1]] in edges or [vals[1],vals[0]] in edges
  elif f['op']=='graph_reachable':
   start,goal,edges=vals[0],vals[1],state[f['args'][2]];seen,todo={start},[start]
   while todo:
    n=todo.pop()
    for a,b in edges:
     nxt=b if a==n else a if b==n else None
     if nxt is not None and nxt not in seen:seen.add(nxt);todo.append(nxt)
   v=goal in seen
  else:raise AssertionError(f)
  state[f['field']]=v
 return state
def state_before(s):
 if s['oracle']['kind']=='version_edit':return replay(s['evidence']['initial'],s['evidence']['events'])
 if s['oracle']['kind']=='state_inference':return derive(s['evidence'])
 if s['oracle']['kind']=='cancellation':return replay(s['evidence']['initial'],[{'op':'set','field':e['task'],'value':e['status']} for e in s['evidence']['events']])
 raise AssertionError(s['oracle']['kind'])
def classify(state,atoms):
 vals=[]
 for a in atoms:
  actual=state.get(a['field'],MISSING);op=a.get('op','equals')
  if actual is MISSING or actual is None:vals.append(None)
  elif op=='equals':vals.append(actual==a['asserted'])
  elif op=='contains':vals.append(a['asserted'] in actual)
  elif op=='not_contains':vals.append(a['asserted'] not in actual)
  else:raise AssertionError(a)
 if any(v is None for v in vals):return'unresolved'
 if all(vals):return'true'
 if not any(vals):return'false'
 return'partial'
def apply(state,req):
 if not req or req.get('ambiguous'):return copy.deepcopy(state)
 if req['kind']=='version_ops':return replay(state,req['ops'])
 if req['kind']=='cancel':
  out=copy.deepcopy(state);out[req['target']]='cancelled';return out
 raise AssertionError(req)

m=json.loads((HERE/'manifest.json').read_text())
assert sha(HERE/'run_queue.py')==RUNNER_SHA==m['runner']['sha256']
for rel,h in m['artifact_sha256'].items():assert sha(HERE/rel)==h,rel
for p in (HERE/'schemas').glob('*.json'):strict(json.loads(p.read_text()))
for p in (HERE/'prompts').glob('*.txt'):assert p.read_text().count('{{INPUT_JSON}}')==1
inputs={'train':read_jsonl(HERE/'inputs/train.jsonl'),'dev':read_jsonl(HERE/'inputs/dev.jsonl'),'final_confirmation':read_jsonl(HERE/'sealed/final_confirmation/inputs.jsonl')}
assert {k:len(v) for k,v in inputs.items()}=={'train':32,'dev':8,'final_confirmation':8}
families=defaultdict(set);labels=Counter();kinds=Counter()
for split,rows in inputs.items():
 for r in rows:
  assert r['split']==split;rids=r['scenario_spec'];families[r['family_id']].add(split)
  assert rids['contract_version']==2
  c=rids['visible_evidence_contract'];d=rids['decision_surface_contract'];a=rids['action_contract']
  assert c['source_role']=='user' and c['must_precede_decision'] and c['assistant_assertion_is_independent_evidence'] is False
  assert c['required_user_context_core_el'].strip()
  assert d['frozen_core_el']==rids['user_decision_semantic_content_el'] and d['must_appear_verbatim']
  state=state_before(rids)
  assert state==rids['oracle']['state_before'],r['row_id']
  assert classify(state,rids['claim_atoms'])==rids['truth_category']==rids['oracle']['derived_truth'],r['row_id']
  assert apply(state,rids['current_request'])==rids['oracle']['state_after'],r['row_id']
  assert r['protected']['oracle']==rids['oracle'] and r['protected']['visible_evidence_contract']==c
  if rids['skill']=='cancellation':
   assert a['mode']=='text_record_edit' and a['external_tool_result_supplied'] is False and a['may_claim_external_action_success'] is False
  if split=='train':labels[rids['truth_category']]+=1;kinds[rids['oracle']['kind']]+=1
assert all(len(x)==1 for x in families.values())
assert labels==Counter({'true':8,'false':8,'partial':8,'unresolved':8})
assert len(inputs['train'])==32
byid={r['row_id']:r for r in inputs['train']}
for rid in ['pilot48_01_unresolved','pilot48_04_unresolved']:
 s=byid[rid]['scenario_spec'];assert s['evidence']['events']==[] and s['evidence']['initial']==s['oracle']['state_before'] and s['evidence']['missing_history'] is True
s=byid['pilot48_03_unresolved']['scenario_spec'];assert '60' not in json.dumps(s,ensure_ascii=False) and s['claim_atoms'][0]['asserted'] is None
assert 'Με βάση μόνο' in byid['pilot48_06_unresolved']['scenario_spec']['user_decision_semantic_content_el']
assert 'Από αυτό το απόσπασμα' in byid['pilot48_07_unresolved']['scenario_spec']['user_decision_semantic_content_el']
assert 'Με βάση μόνο' in byid['pilot48_08_unresolved']['scenario_spec']['user_decision_semantic_content_el']
assert byid['pilot48_02_unresolved']['scenario_spec']['evidence']['ambiguous_referents']==['Άννα','Μαρία']
assert byid['pilot48_10_unresolved']['scenario_spec']['evidence']['ambiguous_cancel_targets']==['ραντεβού','αγορές']
for r in inputs['train']:
 assert r['scenario_spec']['visible_evidence_contract']['required_user_context_core_el']
 assert r['message_plan']['context_assistant_train'] is False and r['message_plan']['decision_user_train'] is False
probe=read_jsonl(HERE/'queues/probe_semantic_repair4.jsonl');assert len(probe)==4 and {j['row_id'] for j in probe}==PROBE
assert all(j['stage']=='dialogue_semantic_repair' and not j['depends_on'] for j in probe)
for rid in PROBE:
 r=byid[rid];assert r['prior_probe_binding']['prior_primary_call_consumed'] and sha(HERE/r['prior_probe_binding']['accepted_artifact'])==r['prior_probe_binding']['accepted_artifact_sha256']
queues={'train':read_jsonl(HERE/'queues/train_remaining.jsonl'),'dev':read_jsonl(HERE/'queues/dev.jsonl'),'final':read_jsonl(HERE/'sealed/final_confirmation/queue.jsonl')}
assert {k:len(v) for k,v in queues.items()}=={'train':28,'dev':8,'final':7}
assert not ({j['row_id'] for j in queues['train']} & PROBE)
ledger=json.loads((HERE/'call_ledger.json').read_text())
assert ledger['consumed_before_revision2']['total']==4
assert ledger['revision2_runner_additional_call_cap']==114
assert ledger['reserved_next_probe']['total']==4
remaining=ledger['remaining_work_caps_after_probe']
assert remaining['primary_authoring']+remaining['retry']+remaining['semantic_repair']+remaining['greek_correction']==remaining['total']==110
assert 4+4+110==ledger['cumulative_absolute_call_cap']==118==ledger['cumulative_projection_at_all_caps']
assert m['counts']['absolute_call_cap']==114 and m['counts']['cumulative_absolute_call_cap']==118
assert not (HERE/'run_state').exists()
q=read_jsonl(HERE/'quarantine/silence_unspecified.jsonl');assert len(q)==1 and q[0]['quarantine']
gate=json.loads((HERE/'sealed/final_confirmation/gate_summary.json').read_text());assert gate['content_exposed_in_report'] is False and gate['authoring_launched'] is False
result={'status':'PASS_PRELAUNCH_REVISION2','train_visible_user_evidence_contracts':32,'truth_counts_train':dict(labels),'oracle_recomputations':48,'probe_semantic_repairs':4,'remaining_primary_calls':43,'prior_calls_preserved':4,'additional_runner_cap':114,'cumulative_cap':118,'family_leakage':False,'final_content_exposed':False,'launched':False}
(HERE/'receipts/prelaunch_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
