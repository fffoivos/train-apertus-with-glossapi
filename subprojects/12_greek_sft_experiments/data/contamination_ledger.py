#!/usr/bin/env python3
"""Match ledger for the final arm (astra readiness review F1): re-runs the assembler's decontamination rule over every USER turn of the final
train.jsonl and writes each match (train row id, block, eval suite, eval item id, containment, matched user-turn excerpt). The rule, stated
exactly: text normalised by build_sft_mix.normalize_text (NFKC, case-fold, punctuation removed, whitespace collapsed); word 8-grams of the
training user turn; containment = share of the turn's distinct 8-grams that occur in any evaluation prompt's 8-grams; a row is contaminated when
containment >= 0.5 for any user turn. (No 13-gram rule is applied at assembly; the benchmark builders' own 8/13-gram check is a separate tool.)
Usage: python3 contamination_ledger.py <arm>  → data/arms/<arm>/contamination_ledger.jsonl + summary"""
import json, sys, os, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE)); import build_sft_mix as r1
arm = sys.argv[1]; A = HERE / 'arms' / arm
evals = []
for f in sorted((HERE / 'cache' / 'evals').glob('*.jsonl')): evals += r1.read_eval_cache(f, f.name.split('.')[0])
try: ell, _ = r1.load_ellinika_prompts(); evals += ell
except Exception: pass
grams = {}
for p in evals:
    for g in r1.ngrams(r1.normalize_text(p.text)): grams.setdefault(g, (p.suite, p.eval_id))
inv = collections.Counter(p.suite for p in evals)
n = 0; matches = []
for line in open(A / 'train.jsonl'):
    r = json.loads(line); n += 1
    for m in r['messages']:
        if m['role'] != 'user': continue
        gs = r1.ngrams(r1.normalize_text(m['content']))
        if not gs: continue
        hit = [g for g in gs if g in grams]
        if hit and len(hit) / len(gs) >= r1.CONTAINMENT_THRESHOLD: matches.append(dict(train_id=r['id'], block=r['config'], eval=grams[hit[0]][0], eval_id=grams[hit[0]][1], containment=round(len(hit) / len(gs), 3), excerpt=m['content'][:160]))
with open(A / 'contamination_ledger.jsonl', 'w') as f:
    for x in matches: f.write(json.dumps(x, ensure_ascii=False) + '\n')
summ = dict(arm=arm, train_rows=n, rule=dict(normalize='NFKC+casefold+punct-strip+ws-collapse', ngram=r1.NGRAM_SIZE, containment='distinct 8-grams of the training USER turn found in any eval prompt / distinct 8-grams of the turn', threshold=f'>= {r1.CONTAINMENT_THRESHOLD}'), eval_inventory=dict(inv), matches_in_final_train=len(matches), by_eval=dict(collections.Counter(x['eval'] for x in matches)))
json.dump(summ, open(A / 'contamination_ledger_summary.json', 'w'), indent=1, ensure_ascii=False); print(json.dumps(summ, ensure_ascii=False))
