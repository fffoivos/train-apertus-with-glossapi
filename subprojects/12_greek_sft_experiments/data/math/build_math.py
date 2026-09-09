#!/usr/bin/env python3
"""The first Greek math cut (plan §7; owner 9 September: no second-solve verification except the hardest problems).
  translated: GSM8K train (n_gsm) + MATH train levels 1–4 (n_math), Sol translation + Sol solve; a row is kept when the solve reaches the reference (free filter).
  native: n_native problems over grade × topic × context × surface, Sol writes problem + solution; Lykeio grades get a second Sol solve at high effort and are kept only when the answers agree.
Writes <out>/out/greek_math_sft.jsonl (core-export schema + meta) and summary.json. Resumable through the pilot functions' caches.
Usage: python3 build_math.py <out_dir> [n_gsm=6000] [n_math=4000] [n_native=6000]"""
import collections, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('MATH_LEVELS', 'Level 1,Level 2,Level 3,Level 4'); os.environ.setdefault('VERIFY_GRADES', 'Α΄ Λυκείου,Β΄ Λυκείου,Γ΄ Λυκείου'); os.environ.setdefault('SOLVER2', 'gpt-5.6-sol'); os.environ.setdefault('NATIVE_SEED', '4242')
import math_pilots as P, mathlib as M


def main():
    out = sys.argv[1]; n_gsm, n_math, n_native = (int(x) for x in (sys.argv[2:5] + ['6000', '4000', '6000'][len(sys.argv) - 2:]))
    os.makedirs(f'{out}/out', exist_ok=True)
    if not os.path.exists(f'{out}/translated/results.jsonl'): P.translate(f'{out}/translated', n_gsm, n_math)
    if not os.path.exists(f'{out}/native/results.jsonl'): P.native(f'{out}/native', n_native)
    rows, stats = [], collections.Counter()
    for r in (json.loads(l) for l in open(f'{out}/translated/results.jsonl')):
        stats[f"translated_{r['src']}_total"] += 1
        if not r['correct']: stats[f"translated_{r['src']}_dropped"] += 1; continue
        rows.append(dict(source='greek_math', bucket=f"translated_{r['src']}", id=f"gm_{r['id']}", user=r['problem_el'], assistant=r['solution_el'], turns=[dict(role='user', content=r['problem_el']), dict(role='assistant', content=r['solution_el'])], n_turns=2, verified='reference',
                         meta=dict(src=r['src'], level=r.get('level'), subject=r.get('subject'), answer=r['final_used'], reference=r['ref'], original=r['problem_en'], changes=r.get('changes'))))
    for r in (json.loads(l) for l in open(f'{out}/native/results.jsonl')):
        stats['native_total'] += 1; verified = r.get('agree')
        if verified is False: stats['native_dropped_disagree'] += 1; continue
        rows.append(dict(source='greek_math', bucket='native', id=f"gm_{r['id']}", user=r['problem_el'], assistant=r['solution_el'], turns=[dict(role='user', content=r['problem_el']), dict(role='assistant', content=r['solution_el'])], n_turns=2, verified=('second_solve' if verified else 'none'),
                         meta=dict(src='native', grade=r['grade'], topic=r['topic'], context=r['context'], surface=r['surface'], answer=r['final_answer'])))
    with open(f'{out}/out/greek_math_sft.jsonl', 'w') as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    fmt = collections.Counter()
    for r in rows:
        for k, v in M.fmt_checks(r['assistant']).items():
            if k != 'greek_share': fmt[k] += bool(v)
    summ = dict(rows=len(rows), by_bucket=dict(collections.Counter(r['bucket'] for r in rows)), by_verified=dict(collections.Counter(r['verified'] for r in rows)), stats=dict(stats), formatting={k: round(v / max(1, len(rows)), 3) for k, v in fmt.items()},
                by_grade=dict(collections.Counter(r['meta'].get('grade') or r['meta'].get('level') for r in rows)), mean_solution_words=round(sum(len(r['assistant'].split()) for r in rows) / max(1, len(rows))))
    json.dump(summ, open(f'{out}/out/summary.json', 'w'), ensure_ascii=False, indent=1); print(json.dumps(summ, ensure_ascii=False)); print('MATH BUILD DONE')


if __name__ == '__main__': main()
