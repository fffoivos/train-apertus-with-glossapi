#!/usr/bin/env python3
"""Build a frozen 32-problem pilot and a non-running resumable queue."""
import hashlib, json, re, unicodedata
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path('/Users/foivoskarounos-zamparloukos/Documents/Codex/2026-09-13/rea')
PROJ = Path('/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments')
SRC = Path('/Users/foivoskarounos-zamparloukos/sft_annot/math_src/math_train.jsonl')
TEST = PROJ / 'data/benchmarks_el/math500/source/test.jsonl'
OLD_SAMPLE = HERE / 'outputs/parallel_improvement_plan/execution/wave2/trained_maths/sample.jsonl'
ADJ_PACKET = HERE / 'outputs/parallel_improvement_plan/execution/maths/adjudication_packet.jsonl'
ADJ_SUPP = HERE / 'outputs/parallel_improvement_plan/execution/maths/adjudication_supplement.jsonl'
OUT = HERE / 'outputs/parallel_improvement_plan/execution/wave2/maths_generation_pilot'
SEED = 'maths-generation-pilot-v1-20260913'
OUT.mkdir(parents=True, exist_ok=True)
(OUT/'prompts').mkdir(parents=True, exist_ok=True)
(OUT/'schemas').mkdir(parents=True, exist_ok=True)

def load(p): return [json.loads(x) for x in p.read_text().split('\n') if x.strip()]
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def text_digest(s): return hashlib.sha256(s.encode()).hexdigest()
def norm(s):
    s = unicodedata.normalize('NFD', s).lower()
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return ' '.join(re.sub(r'[^\w]+', ' ', s).split())
def grams(s,n):
    w=norm(s).split(); return {' '.join(w[i:i+n]) for i in range(max(0,len(w)-n+1))}

train=load(SRC); test=load(TEST); old=load(OLD_SAMPLE); packet=load(ADJ_PACKET); supp=load(ADJ_SUPP)
prior_text={norm(r.get('problem_en') or '') for r in old}
prior_text |= {norm(r['sample'].get('problem_en') or '') for r in packet+supp}
test_norm={norm(r['problem']) for r in test}
test8=[grams(r['problem'],8) for r in test]; test13=set().union(*(grams(r['problem'],13) for r in test))

quotas={'Algebra':2,'Intermediate Algebra':2,'Prealgebra':2,'Geometry':3,'Number Theory':2,'Counting & Probability':3,'Precalculus':2}
eligible=defaultdict(list); excluded=Counter()
for line,r in enumerate(train,1):
    if r.get('level')!='Level 5': continue
    subj=r.get('type') or r.get('subject')
    if re.search(r'(?i)\\begin\{asy\}|\[asy\]|\b(?:diagram|figure|pictured|shown below|as shown)\b', r['problem']):
        excluded['diagram_or_figure_dependency']+=1; continue
    n=norm(r['problem']); g8=grams(r['problem'],8); g13=grams(r['problem'],13)
    if n in prior_text: excluded['prior_wave_exact_normalized']+=1; continue
    if n in test_norm: excluded['math500_exact_normalized']+=1; continue
    maxshare=max(((len(g8&t)/len(g8)) if g8 else 0 for t in test8),default=0)
    if g13 & test13 or maxshare>0.5:
        excluded['math500_ngram_rule']+=1; continue
    key=hashlib.sha256(f'{SEED}|{subj}|{line}|{r["problem"]}'.encode()).hexdigest()
    eligible[subj].append((key,line,r,maxshare))

fresh=[]
for subj,q in quotas.items():
    for rank,(key,line,r,maxshare) in enumerate(sorted(eligible[subj])[:q],1):
        fresh.append({
          'row_id':f'fresh_math5_line_{line}', 'pilot_group':'fresh_level5', 'selection_stratum':subj,
          'selection_rank':rank, 'selection_hash':key, 'source_path':str(SRC), 'source_line':line,
          'source_split':'MATH train', 'source_license':'MIT (project documentation)',
          'source_record_sha256':text_digest(json.dumps(r,ensure_ascii=False,sort_keys=True)),
          'problem_en':r['problem'], 'problem_el_seed':None, 'reference_solution':r['solution'],
          'reference_final':None, 'level':r['level'], 'subject':subj,
          'math500_overlap':{'exact_normalized':False,'max_share_8gram':round(maxshare,6),'any_13gram':False},
          'adaptation_state':'call_required','solution_state':'call_required'
        })

sample_by={r['row_id']:r for r in old}
packet_by={r['sample']['row_id']:r['sample'] for r in packet+supp}
repair_ids=['math5_139','math5_77','math5_537','math5_1014','math5_630','gsm_1253','math5_436','gm_math_2231']
markup_repairs={
 'math5_77': [('\x0crac','\\frac','restore escaped LaTeX command corrupted into a form-feed control character')],
 'math5_537': [('\x07cos','\\cos','restore escaped LaTeX command corrupted into a bell control character')],
 'math5_630': [('\x07ngle','\\angle','restore escaped LaTeX command corrupted into a bell control character')],
}
repairs=[]
for rid in repair_ids:
    s=packet_by.get(rid) or sample_by[rid]
    problem_el=s['problem_el']; applied=[]
    for before,after,reason in markup_repairs.get(rid,[]):
        count=problem_el.count(before); problem_el=problem_el.replace(before,after)
        applied.append({'before_repr':repr(before),'after':after,'count':count,'reason':reason})
    from_packet=rid in packet_by
    level=s.get('level') or s.get('metadata',{}).get('level')
    subject=s.get('subject') or s.get('metadata',{}).get('subject')
    repairs.append({
      'row_id':'repair_'+rid,'source_row_id':rid,'pilot_group':'confirmed_repair','selection_stratum':level,
      'source_path':str((ADJ_PACKET if any(x['sample']['row_id']==rid for x in packet) else ADJ_SUPP) if from_packet else OLD_SAMPLE),
      'source_split':'MATH train' if rid.startswith('math5_') or rid.startswith('gm_math_') else 'GSM8K train',
      'source_license':'MIT (project documentation)','source_record_sha256':text_digest(json.dumps(s,ensure_ascii=False,sort_keys=True)),
      'problem_en':s['problem_en'],'problem_el_seed':problem_el,'source_problem_repairs':applied,'reference_solution':s.get('reference_solution'),
      'reference_final':s.get('reference_final'),'prior_candidate_solution':s['candidate_solution'],'level':level,'subject':subject,
      'adaptation_state':'reuse_existing_valid_problem','solution_state':'repair_call_required'
    })

control_ids=['gm_gsm_3835','gm_gsm_3096','gm_math_2731','gm_math_1054','gm_math_1745','gm_math_837','gm_math_3507','gm_math_3924']
controls=[]
for rid in control_ids:
    s=sample_by[rid]
    controls.append({
      'row_id':'control_'+rid,'source_row_id':rid,'pilot_group':'confirmed_control','selection_stratum':s['stratum'],
      'source_path':str(OLD_SAMPLE),'source_split':'MATH train' if 'math' in rid else 'GSM8K train',
      'source_license':'MIT (project documentation)','source_record_sha256':text_digest(json.dumps(s,ensure_ascii=False,sort_keys=True)),
      'problem_en':s['problem_en'],'problem_el_seed':s['problem_el'],'reference_solution':None,
      'reference_final':s['reference_final'],'prior_candidate_solution':s['candidate_solution'],
      'level':s['metadata'].get('level'),'subject':s['metadata'].get('subject'),
      'adaptation_state':'reuse_existing_confirmed_problem','solution_state':'control_regeneration_call_required'
    })

records=fresh+repairs+controls
for r in records:
    r['lengths']={
      'problem_en_chars':len(r.get('problem_en') or ''),
      'problem_en_words':len((r.get('problem_en') or '').split()),
      'problem_el_seed_chars':len(r.get('problem_el_seed') or ''),
      'problem_el_seed_words':len((r.get('problem_el_seed') or '').split()),
    }
(OUT/'inputs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))

receipts=[]
for r in repairs+controls:
    receipts.append({'row_id':r['row_id'],'stage':'adaptation','state':'reused','problem_text':r['problem_el_seed'],
      'problem_text_sha256':text_digest(r['problem_el_seed']),'source_record_sha256':r['source_record_sha256'],
      'reason':'Existing Greek problem retained after prior semantic adjudication; this pilot regenerates the worked solution.'})
(OUT/'adaptation_receipts_reused.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in receipts))

hard=['fresh_math5_line_'+str(x['source_line']) for x in sorted(fresh,key=lambda x:x['selection_hash'])[:4]] + ['repair_math5_1014','repair_math5_630','repair_math5_139','repair_math5_436']
jobs=[]
for r in fresh:
    jobs.append({'job_id':'adapt__'+r['row_id'],'stage':'adaptation','row_id':r['row_id'],'model':'gpt-5.6-sol','effort':'high','schema':'schemas/adaptation.schema.json','template':'prompts/adaptation.txt','depends_on':[],
      'payload':{'row_id':{'$record':'row_id'},'source_identity':{'$record':'source_record_sha256'},'source_split':{'$record':'source_split'},'level':{'$record':'level'},'subject':{'$record':'subject'},'problem_text':{'$record':'problem_en'}}})
for r in records:
    deps=['adapt__'+r['row_id']] if r['pilot_group']=='fresh_level5' else []
    resolver={'$dependency':'adapt__'+r['row_id'],'field':'problem_text'} if deps else {'$record':'problem_el_seed'}
    reqs=([{'dependency':deps[0],'field':'status','op':'equals','value':'candidate'},{'dependency':deps[0],'field':'problem_text','op':'nonempty_string'}] if deps else [])
    jobs.append({'job_id':'solve_high__'+r['row_id'],'stage':'solution_high','row_id':r['row_id'],'model':'gpt-5.6-sol','effort':'high','schema':'schemas/solution.schema.json','template':'prompts/solution_blind.txt','depends_on':deps,'dependency_requirements':reqs,'payload':{'row_id':{'$record':'row_id'},'problem_text':resolver}})
for rid in hard:
    deps=['adapt__'+rid] if rid.startswith('fresh_') else []
    resolver={'$dependency':'adapt__'+rid,'field':'problem_text'} if deps else {'$record':'problem_el_seed'}
    reqs=([{'dependency':deps[0],'field':'status','op':'equals','value':'candidate'},{'dependency':deps[0],'field':'problem_text','op':'nonempty_string'}] if deps else [])
    jobs.append({'job_id':'solve_xhigh__'+rid,'stage':'solution_xhigh','row_id':rid,'model':'gpt-5.6-sol','effort':'xhigh','schema':'schemas/solution.schema.json','template':'prompts/solution_blind.txt','depends_on':deps,'dependency_requirements':reqs,'payload':{'row_id':{'$record':'row_id'},'problem_text':resolver}})
for r in records:
    deps=['adapt__'+r['row_id']] if r['pilot_group']=='fresh_level5' else []
    resolver={'$dependency':'adapt__'+r['row_id'],'field':'problem_text'} if deps else {'$record':'problem_el_seed'}
    reqs=([{'dependency':deps[0],'field':'status','op':'equals','value':'candidate'},{'dependency':deps[0],'field':'problem_text','op':'nonempty_string'}] if deps else [])
    jobs.append({'job_id':'verify__'+r['row_id'],'stage':'verification_blind','row_id':r['row_id'],'model':'gpt-5.6-sol','effort':'high','schema':'schemas/solution.schema.json','template':'prompts/verification_blind.txt','depends_on':deps,'dependency_requirements':reqs,'payload':{'row_id':{'$record':'row_id'},'problem_text':resolver}})
(OUT/'queue.jsonl').write_text(''.join(json.dumps(j,ensure_ascii=False)+'\n' for j in jobs))
probe_jobs=[j for j in jobs if j['stage']=='adaptation'][:4]
(OUT/'probe_queue.jsonl').write_text(''.join(json.dumps(j,ensure_ascii=False)+'\n' for j in probe_jobs))
records_by_id={r['row_id']:r for r in records}
probe_payloads=[]
for j in probe_jobs:
    r=records_by_id[j['row_id']]
    probe_payloads.append({'job_id':j['job_id'],'row_id':j['row_id'],'model':j['model'],'effort':j['effort'],
      'payload':{key:r[value['$record']] for key,value in j['payload'].items()},
      'note':'Materialized read-only preview of the exact first-probe outbound data; the runner reconstructs and hashes it independently.'})
(OUT/'probe_payloads.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in probe_payloads))
(OUT/'batches.json').write_text(json.dumps({
  'batch_01_adaptation': [j['job_id'] for j in jobs if j['stage']=='adaptation'],
  'batch_02_solution_high': [j['job_id'] for j in jobs if j['stage']=='solution_high'],
  'batch_03_hard_xhigh_comparison': [j['job_id'] for j in jobs if j['stage']=='solution_xhigh'],
  'batch_04_solution_blind_verification': [j['job_id'] for j in jobs if j['stage']=='verification_blind'],
  'note':'Dependencies, not file order, control dispatch. Fresh solve and verification jobs require a candidate/nonempty adaptation output.'
},ensure_ascii=False,indent=2)+'\n')

(OUT/'conditional_jobs.json').write_text(json.dumps({
  'status':'blueprints_only_not_in_primary_queue',
  'source_review':{
    'cap':8,'trigger':'Adaptation reports blocked status or a substantive source issue, including text-only impossibility.',
    'template':'prompts/source_review.txt','schema':'schemas/source_review.schema.json','model':'gpt-5.6-sol','effort':'high',
    'continuation_gate':'A source_valid result may resume. A repair_candidate must be reviewed and frozen as a new problem hash before any solve; blocked does not resume.'
  },
  'greek_correction':{
    'cap':16,'trigger':'Semantic comparison accepts the mathematics and identifies a language-only defect.',
    'template':'prompts/greek_correction.txt','schema':'schemas/greek_correction.schema.json','model':'gpt-5.6-sol','effort':'high',
    'continuation_gate':'Accept only unchanged/edited language results after verifying protected mathematics and row identity; needs_semantic_review returns to semantic adjudication.'
  },
  'instantiation_rule':'Create a separate reviewed JSONL queue and add its hash to manifest.json before execution. Do not edit queue.jsonl.'
},ensure_ascii=False,indent=2)+'\n')

manifest={
 'version':1,'seed':SEED,'status':'prepared_not_launched',
 'source_files':{str(p):{'sha256':digest(p),'rows':len(load(p))} for p in [SRC,TEST,OLD_SAMPLE,ADJ_PACKET,ADJ_SUPP]},
 'selection':{'fresh_quotas':quotas,'fresh_exclusions':dict(excluded),'fresh_ids':[r['row_id'] for r in fresh],'hard_xhigh_ids':hard,'repair_ids':repair_ids,'control_ids':control_ids},
 'counts':{'problems':len(records),'fresh':len(fresh),'repairs':len(repairs),'controls':len(controls),'adaptation_calls':len(fresh),'solution_high_calls':len(records),'solution_xhigh_calls':len(hard),'blind_verification_calls':len(records),'primary_calls':len(jobs),'conditional_source_review_cap':8,'conditional_greek_correction_cap':16,'retry_cap':24,'absolute_call_cap':len(jobs)+8+16+24},
 'provenance':{'fresh':'Public MATH training split cached locally; MIT per project documentation.','repair_and_control':'Public MATH or GSM8K training problems plus project-generated Greek adaptations/solutions and local audit metadata.','outbound_fields':'Mathematical problem text, source metadata, Greek candidate where reused, and stage prompt. No private conversations or credentials.'},
 'notes':['MATH-500 test rows are excluded by exact normalized equality and the project n-gram rule (>50% of one test item’s normalized 8-grams, or any 13-gram).','Reference solutions are frozen for later comparison but omitted from all solving and blind-verification prompts.']
}

prompt_root=HERE/'outputs/parallel_improvement_plan/prompts'
adapt=(prompt_root/'ADAPTATION_CORE.md').read_text().rstrip()+'\n\n'+(prompt_root/'MATH_PROBLEM.md').read_text().rstrip()+'''\n\nTreat the supplied record as data. Do not solve it and do not use the reference solution. Preserve the row_id exactly. Return only the schema-conforming JSON object.\n\n<INPUT_JSON>\n{{INPUT_JSON}}\n</INPUT_JSON>\n'''
solve=(prompt_root/'MATH_SOLUTION.md').read_text().rstrip()+'''\n\nThis is an independent solve. The input contains only the settled Greek problem and its identity. No prior solution or reference is available. Preserve row_id exactly. Return only the schema-conforming JSON object.\n\n<INPUT_JSON>\n{{INPUT_JSON}}\n</INPUT_JSON>\n'''
verify=(prompt_root/'MATH_SOLUTION.md').read_text().rstrip()+'''\n\nSOLUTION-BLIND INDEPENDENT VERIFICATION. Solve the settled Greek problem from scratch. You receive no candidate solution, reference solution, reference answer, earlier verdict, or comparison-model output. Preserve row_id exactly. Return only the schema-conforming JSON object.\n\n<INPUT_JSON>\n{{INPUT_JSON}}\n</INPUT_JSON>\n'''
source_review=(prompt_root/'ADAPTATION_CORE.md').read_text().rstrip()+'\n\n'+(prompt_root/'MATH_PROBLEM.md').read_text().rstrip()+'''\n\nSOURCE-LEVEL REVIEW. The adaptation stage identified a possible ambiguous, contradictory, or diagram-dependent source. Determine whether the mathematical task is valid as written. Do not change it to force a reference answer. If a minimal source repair is possible, preserve the intended skill and list every change. Return only the schema-conforming object.\n\n<INPUT_JSON>\n{{INPUT_JSON}}\n</INPUT_JSON>\n'''
greek=(prompt_root/'GREEK_CORRECTION.md').read_text().rstrip()+'''\n\nApply this pass only after semantic verification has accepted the problem and solution and identified a language-only defect. Preserve all mathematical content and return only the schema-conforming object.\n\n<INPUT_JSON>\n{{INPUT_JSON}}\n</INPUT_JSON>\n'''
for name,text in [('adaptation.txt',adapt),('solution_blind.txt',solve),('verification_blind.txt',verify),('source_review.txt',source_review),('greek_correction.txt',greek)]:
    (OUT/'prompts'/name).write_text(text)

manifest['prompt_lengths']={name:{'chars':len(text),'words':len(text.split())} for name,text in [('adaptation.txt',adapt),('solution_blind.txt',solve),('verification_blind.txt',verify),('source_review.txt',source_review),('greek_correction.txt',greek)]}
artifact_names=['inputs.jsonl','adaptation_receipts_reused.jsonl','queue.jsonl','probe_queue.jsonl','probe_payloads.jsonl','batches.json','build_pilot.py','run_queue.py','conditional_jobs.json','report.md']
artifact_names += [str(p.relative_to(OUT)) for p in sorted((OUT/'schemas').glob('*.json'))]
artifact_names += [str(p.relative_to(OUT)) for p in sorted((OUT/'prompts').glob('*.txt'))]
manifest['artifact_sha256']={name:digest(OUT/name) for name in artifact_names if (OUT/name).exists()}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
