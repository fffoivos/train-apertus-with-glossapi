#!/usr/bin/env python3
"""Build deterministic review manifests from immutable adaptation exports and assemblies."""
from __future__ import annotations
import hashlib, json, re
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAT = Path('/Users/foivoskarounos-zamparloukos/Projects/natural-greek-sft')
EXP = Path('/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments')
REV = 'ff2057d016a8f19002eca1ad6a9b657c80a4ac55'
SEED = 'wave2-adapted-core-v1'
CORE = ('no_robots','coconot','personas_if','smolcon','oasst','everyday','systemchats')
FOREIGN = ('no_robots_en_pov','apertus_en','euroblocks_fr','euroblocks_de')

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_obj(x): return sha_bytes(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',',':')).encode())
def rows(path):
    return [(n, json.loads(line)) for n,line in enumerate(path.open(),1) if line.strip()]
def export_path(config):
    if config == 'no_robots_en_pov':
        return NAT/'data/pilots/no_robots/export/natural_greek_sft_no_robots_en_pov.jsonl'
    return NAT/f'data/pilots/{config}/export/natural_greek_sft_{config}.jsonl'
def cache_path(config): return EXP/f'data/cache/sources/{config}.{REV}.jsonl'
def rank(stratum, rid): return (hashlib.sha256(f'{SEED}\0{stratum}\0{rid}'.encode()).digest(),rid)

def original_messages(r):
    en=r.get('en') or {}; ms=list(en.get('messages') or [])
    if en.get('system') and (not ms or ms[0].get('role')!='system'):
        ms=[{'role':'system','content':en['system']}]+ms
    return ms

def adapted_messages(r):
    sol=r.get('sol') or {}; out=[]
    if sol.get('system_el'): out.append({'role':'system','content':sol['system_el']})
    users=sol.get('user_turns_el') or []
    assists=([sol['response_el']] if sol.get('response_el') else [])+(sol.get('assistant_turns_el') or [])
    if users:
        for i,u in enumerate(users):
            out.append({'role':'user','content':u})
            if i < len(assists): out.append({'role':'assistant','content':assists[i]})
    else:
        if sol.get('prompt_el'): out.append({'role':'user','content':sol['prompt_el']})
        out += [{'role':'assistant','content':a} for a in assists]
    return out or None

def balanced(source_rows, n, label):
    groups=defaultdict(list)
    for line,r in source_rows: groups[str(r.get('category') or r.get('subcategory') or 'unknown')].append((line,r))
    for k in groups: groups[k].sort(key=lambda lr: rank(label+'\0'+k,lr[1]['row_id']))
    keys=sorted(groups); picked=[]; i=0
    while len(picked)<n and any(i<len(groups[k]) for k in keys):
        for k in keys:
            if i<len(groups[k]) and len(picked)<n: picked.append(groups[k][i])
        i+=1
    return picked

# Cache and assembly indexes prove actual downstream identities.
cache={}
for cfg in CORE+FOREIGN:
    p=cache_path(cfg); cache[cfg]={r['row_id']:(n,r) for n,r in rows(p)}
assemblies=defaultdict(list)
for arm in ('E1','E2','E3','E3prime'):
    for split in ('train','dev'):
        p=EXP/f'data/arms/{arm}/{split}.jsonl'
        for n,r in rows(p):
            variant='raw' if arm=='E3prime' and r['config'] in ('apertus_en','euroblocks_fr','euroblocks_de') else 'adapted'
            assemblies[(r['config'],r['row_id'])].append({'arm':arm,'variant':variant,'arm_path':str(p),'split':split,'line':n,'messages_sha256':sha_obj(r['messages'])})

source_manifest={
    'seed':SEED,
    'selection':'sha256(seed\\0stratum\\0row_id), category round-robin for core',
    'foreign_language_goal':['en','fr','de','es','pt','it'],
    'paired_foreign_languages_in_current_exports':['en','fr','de'],
    'missing_paired_adaptation_languages':['es','pt','it'],
    'coverage_boundary':'ES/PT/IT are checked only as nine unpaired retained multilingual records and are outside the foreign60 denominator.',
    'files':[],
}
for cfg in CORE+FOREIGN:
    ep,cp=export_path(cfg),cache_path(cfg)
    source_manifest['files'].append({'config':cfg,'export_path':str(ep),'export_sha256':sha_bytes(ep.read_bytes()),'cache_path':str(cp),'cache_sha256':sha_bytes(cp.read_bytes()),'byte_identical':ep.read_bytes()==cp.read_bytes(),'rows':sum(1 for _ in ep.open())})
(HERE/'source_manifest.json').write_text(json.dumps(source_manifest,ensure_ascii=False,indent=2)+'\n')

core_plan=[]
for cfg in CORE:
    erows=rows(export_path(cfg)); count=12 if cfg=='no_robots' else 8; initial=6 if cfg=='no_robots' else 3
    chosen=balanced(erows,count,cfg)
    for pos,(line,r) in enumerate(chosen,1):
        rid=r['row_id']; cm=cache[cfg].get(rid); raw=original_messages(r); adapt=adapted_messages(r); final=r.get('el_messages')
        missing=[]
        if not raw: missing.append('original_messages')
        if adapt is None: missing.append('adaptation_receipt_messages')
        if not final: missing.append('corrected_messages')
        if cm is None: missing.append('assembly_cache_row')
        asm=[dict(a,expected_messages_sha256=sha_obj(final) if final else None,matches_expected_variant=bool(final) and a['messages_sha256']==sha_obj(final)) for a in assemblies.get((cfg,rid),[])]
        if not asm: missing.append('assembled_row')
        core_plan.append({'manifest':'core60','initial_read':pos<=initial,'stratum':cfg,'position':pos,'row_id':rid,'category':r.get('category'),'export_line':line,
          'lineage':{'original_sha256':sha_obj(raw) if raw else None,'adaptation_sha256':sha_obj(adapt) if adapt else None,'corrected_sha256':sha_obj(final) if final else None,
                     'adaptation_equals_corrected':adapt==final if adapt else None,'edit':r.get('edit'),'cache_line':cm[0] if cm else None,'cache_row_sha256':sha_obj(cm[1]) if cm else None,'assemblies':asm,'missing':missing},
          'review_material':{'original':raw,'adaptation':adapt,'corrected':final,'sol_decisions':{k:(r.get('sol') or {}).get(k) for k in ('translation_class','prompt_match','transpositions','kept_foreign','vantage_applied','devices','constraint_check','deviations','reference_corrections')}}})

def foreign_stratum(cfg,r):
    if cfg=='no_robots_en_pov': return 'en_no_robots_twin'
    if cfg=='apertus_en': return 'en_apertus'
    return ('fr_' if cfg.endswith('_fr') else 'de_')+('math' if r.get('sample')=='M' else 'general')

foreign_groups=defaultdict(list)
for cfg in FOREIGN:
    for line,r in rows(export_path(cfg)): foreign_groups[foreign_stratum(cfg,r)].append((cfg,line,r))
foreign_plan=[]; greek_twins={r['row_id']:r for _,r in rows(export_path('no_robots'))}
for stratum in ('en_no_robots_twin','en_apertus','fr_math','fr_general','de_math','de_general'):
    group=sorted(foreign_groups[stratum],key=lambda x:rank(stratum,x[2]['row_id']))[:10]
    for pos,(cfg,line,r) in enumerate(group,1):
        rid=r['row_id']; cm=cache[cfg].get(rid); is_twin=cfg=='no_robots_en_pov'
        raw=(original_messages(r) if not is_twin else original_messages(greek_twins.get(rid,{})))
        adapt=(r.get('messages') if is_twin else adapted_messages(r)); final=(r.get('messages') if is_twin else r.get('el_messages'))
        twin=greek_twins.get(rid) if is_twin else None; missing=[]
        if not raw: missing.append('original_messages')
        if adapt is None: missing.append('adaptation_receipt_messages' if not is_twin else 'paired_english_messages')
        if is_twin: missing.append('standalone_english_adaptation_receipt_not_in_export')
        if cm is None: missing.append('assembly_cache_row')
        raw_variant=original_messages(r) if not is_twin else None
        asm=[]
        for a in assemblies.get((cfg,rid),[]):
            expected=raw_variant if a['variant']=='raw' else final
            asm.append(dict(a,expected_messages_sha256=sha_obj(expected) if expected else None,matches_expected_variant=bool(expected) and a['messages_sha256']==sha_obj(expected)))
        if not asm: missing.append('assembled_row')
        foreign_plan.append({'manifest':'foreign60','initial_read':pos<=3,'language':stratum[:2],'stratum':stratum,'position':pos,'config':cfg,'row_id':rid,'category':r.get('category'),'sample':r.get('sample'),'export_line':line,
          'lineage':{'original_sha256':sha_obj(raw) if raw else None,'adaptation_sha256':sha_obj(adapt) if adapt else None,'corrected_sha256':sha_obj(final) if final else None,'adaptation_equals_corrected':adapt==final if adapt else None,
                     'edit':r.get('edit'),'pair':r.get('pair'),'greek_twin_sha256':sha_obj(twin.get('el_messages')) if twin else None,'cache_line':cm[0] if cm else None,'assemblies':asm,'missing':missing},
          'review_material':{'original':raw,'adaptation':adapt,'corrected':final,'greek_twin':twin.get('el_messages') if twin else None,'raw_variant':raw_variant,
             'sol_decisions':{k:(r.get('sol') or {}).get(k) for k in ('translation_class','prompt_match','transpositions','kept_foreign','vantage_applied','devices','constraint_check','deviations','reference_corrections')}}})

def write_jsonl(name,data):
    with (HERE/name).open('w') as f:
        for x in data: f.write(json.dumps(x,ensure_ascii=False)+'\n')
write_jsonl('core60_manifest.jsonl',core_plan)
write_jsonl('foreign60_manifest.jsonl',foreign_plan)
write_jsonl('initial42_review_material.jsonl',[x for x in core_plan+foreign_plan if x['initial_read']])

# ES/PT/IT have no paired adaptations in the natural-greek-sft exports. Sample actual retained
# rows separately from the multilingual import, using conservative transparent language cues.
multi_path=Path('/Users/foivoskarounos-zamparloukos/sft_annot/core_export/smoltalk2_multilingual.jsonl')
r3_path=EXP/'data/arms/R3_single/train.jsonl'
r3_multi={str(r['id']):(n,r) for n,r in rows(r3_path) if r.get('config')=='smoltalk2_multilingual'}
cues={
 'es':('¿','¡',' cuál ',' cuáles ',' usted ',' ustedes ',' también ',' español ',' para ',' que ',' una ',' los ',' las '),
 'pt':(' você ',' vocês ',' não ',' qual ',' quais ',' também ',' português ',' para ',' que ',' uma ','ção','ções'),
 'it':(' quale ',' quali ',' questo ',' questa ',' italiano ',' perché ',' degli ',' delle ',' sono ',' per ',' che ',' una '),
}
def detect_target(text):
    t=' '+re.sub(r'\s+',' ',text.casefold())+' '
    scores={lang:sum(t.count(c) for c in cs) for lang,cs in cues.items()}
    ordered=sorted(scores,key=lambda k:(-scores[k],k))
    return (ordered[0],scores) if scores[ordered[0]]>=3 and scores[ordered[0]]>=scores[ordered[1]]+2 else (None,scores)
unpaired=defaultdict(list)
if multi_path.exists():
    for line,r in rows(multi_path):
        rid=str(r['id'])
        if rid not in r3_multi: continue
        msgs=r.get('turns') or []
        lang,scores=detect_target('\n'.join(m.get('content','') for m in msgs))
        if lang in cues:
            unpaired[lang].append((rank('unpaired_'+lang,rid),line,r,msgs,scores))
unpaired9=[]
for lang in ('es','pt','it'):
    for pos,(_,line,r,msgs,scores) in enumerate(sorted(unpaired[lang])[:3],1):
        rid=str(r['id']); an,ar=r3_multi[rid]
        unpaired9.append({'coverage':'unpaired-retained-record','language':lang,'position':pos,'id':rid,
          'source_path':str(multi_path),'source_line':line,'source_messages_sha256':sha_obj(msgs),
          'assembly_path':str(r3_path),'assembly_line':an,'assembly_messages_sha256':sha_obj(ar['messages']),
          'source_equals_assembly':msgs==ar['messages'],'language_detection':{'method':'declared cue-count heuristic plus manual semantic read','scores':scores},
          'paired_adaptation':None,'missing':['paired_adaptation_lineage'],'review_material':{'retained_messages':msgs}})
write_jsonl('unpaired_es_pt_it_coverage9.jsonl',unpaired9)
print(json.dumps({'core_planned':len(core_plan),'core_initial':sum(x['initial_read'] for x in core_plan),'foreign_planned':len(foreign_plan),'foreign_initial':sum(x['initial_read'] for x in foreign_plan),'unpaired_coverage':len(unpaired9),'unpaired_by_language':{k:sum(x['language']==k for x in unpaired9) for k in ('es','pt','it')},'source_files':len(source_manifest['files'])}))
