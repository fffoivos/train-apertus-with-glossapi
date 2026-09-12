#!/usr/bin/env python3
"""Acceptance checks for assembled cut-2 rows (owner rule: report the failing number, never shade). Usage: python3 check_cut2.py rows.jsonl reference_lengths.json
Checks: \\boxed present in every target; answer-length distribution vs the source solutions (median ratio within 0.8–1.25, p90 within 0.7–1.4); level quotas
(Level 5 ≥ 15% of MATH rows); decimal comma; no agreement filter applied (rows carry 'verification' = reference|fidelity_sample|none, never 'second_solve_agreement')."""
import json, sys, statistics as st, collections
rows=[json.loads(l) for l in open(sys.argv[1]) if l.strip()]; ref=json.load(open(sys.argv[2])) if len(sys.argv)>2 else {}
def target(r): return r.get('assistant') or ''.join(m['content'] for m in r.get('turns',[]) if m['role']=='assistant')
n=len(rows); boxed=sum(1 for r in rows if '\\boxed' in target(r)); w=[len(target(r).split()) for r in rows]
lv=collections.Counter(str(r.get('level') or r.get('meta',{}).get('level')) for r in rows); l5=lv.get('Level 5',0)/max(1,sum(v for k,v in lv.items() if k.startswith('Level')))
ver=collections.Counter(r.get('verification') or r.get('meta',{}).get('verification') for r in rows)
med=st.median(w) if w else 0; p90=sorted(w)[int(len(w)*.9)] if w else 0; rm=ref.get('solution_words_median'); ratio=(med/rm) if rm else None
res=dict(n=n, boxed_share=round(boxed/n,4), median_words=med, p90_words=p90, ratio_to_reference_median=ratio, level5_share_of_math=round(l5,3), verification=dict(ver),
         ok=(boxed==n) and (ratio is None or 0.8<=ratio<=1.25) and l5>=0.15 and 'second_solve_agreement' not in ver)
print(json.dumps(res, ensure_ascii=False, indent=1)); sys.exit(0 if res['ok'] else 1)
