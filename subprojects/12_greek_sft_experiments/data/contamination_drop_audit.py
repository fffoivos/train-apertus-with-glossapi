# Audit of the assembler's contamination drops on the ifeval_like export: which evaluation suite each dropped row matched, containment fraction, examples.
import ast, json, collections, sys
from pathlib import Path
HERE = Path('data').resolve()
src = open('data/assemble_mix_r2.py').read(); tree = ast.parse(src)
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'r1')
ns = {'__name__':'r1mod','HERE':HERE}
import datetime, os, re, random, hashlib, argparse, unicodedata
ns.update(dict(datetime=datetime, json=json, sys=sys, os=os, re=re, random=random, hashlib=hashlib, argparse=argparse, collections=collections, unicodedata=unicodedata, Path=Path))
exec(compile(ast.Module(body=[cls], type_ignores=[]), 'r1', 'exec'), ns); r1 = ns['r1']
evals=[]
for f in sorted((HERE/'cache'/'evals').glob('*.jsonl')):
    suite=f.name.split('.')[0]; evals += r1.read_eval_cache(f, suite)
try:
    ell,_ = r1.load_ellinika_prompts(); evals += ell
except Exception as e: print('ellinika prompts unavailable:', str(e)[:80])
eval_text = {(p.suite,p.eval_id): p.text for p in evals}
eval_grams={}
for p in evals:
    for g in r1.ngrams(r1.normalize_text(p.text)): eval_grams.setdefault(g,(p.suite,p.eval_id))
print('evals', len(evals), 'grams', len(eval_grams), 'N', r1.NGRAM_SIZE, 'thr', r1.CONTAINMENT_THRESHOLD, flush=True)
export = sys.argv[1]; block = sys.argv[2]
hits=[]; by_suite=collections.Counter(); n=0
for _, row in r1.read_jsonl(export):
    n+=1
    msgs = row.get('messages') or row.get('turns') or [{'role':'user','content':row.get('prompt') or row.get('instruction') or row.get('user') or ''}]
    for m in msgs:
        if m['role']!='user': continue
        gs = r1.ngrams(r1.normalize_text(m['content']))
        if not gs: continue
        h=[g for g in gs if g in eval_grams]
        if h and len(h)/len(gs) >= r1.CONTAINMENT_THRESHOLD:
            s,e = eval_grams[h[0]]; by_suite[s]+=1
            hits.append({'block':block,'row_id':row.get('id'),'suite':s,'eval_id':e,'containment':round(len(h)/len(gs),3),'user_text':m['content'][:300],'eval_text':eval_text[(s,e)][:300]})
            break
print(block, 'rows', n, 'hits', len(hits), dict(by_suite))
json.dump({'block':block,'export':export,'rows':n,'hits':len(hits),'by_suite':dict(by_suite),'examples':hits[:40],'all_hits':hits}, open(f'docs/receipts/R3_single/contamination_audit_{block}.json','w'), ensure_ascii=False, indent=1)
print('DONE')
