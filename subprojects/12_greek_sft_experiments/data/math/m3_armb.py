#!/usr/bin/env python3
"""M3: difficulty calibration. A served model (OpenAI-compatible endpoint) solves the M2 native problems; accuracy against the agreed answer by grade and topic.
Usage: python3 m3_armb.py <M2_dir> <out_dir> --target NAME=URL/MODEL_ID [--samples 4] [--only-agreed]"""
import argparse, collections, json, os, sys, threading, urllib.request
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import mathlib as M
SYSTEM = None
PROMPT = 'Λύσε το παρακάτω πρόβλημα βήμα προς βήμα στα ελληνικά και δώσε την τελική απάντηση σε τελευταία γραμμή «Απάντηση: …».\n\n{p}'


def chat(url, model, prompt, temperature, seed):
    body = dict(model=model, messages=[dict(role='user', content=prompt)], temperature=temperature, top_p=0.95 if temperature else 1.0, max_tokens=900, seed=seed)
    req = urllib.request.Request(url.rstrip('/') + '/chat/completions', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as r: return json.load(r)['choices'][0]['message']['content']


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('m2'); ap.add_argument('out'); ap.add_argument('--target', required=True); ap.add_argument('--samples', type=int, default=4); ap.add_argument('--only-agreed', action='store_true'); ap.add_argument('--workers', type=int, default=32)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); name, rest = a.target.split('=', 1); url, model = rest.rsplit('/', 1)
    rows = [json.loads(l) for l in open(f'{a.m2}/results.jsonl')]
    if a.only_agreed: rows = [r for r in rows if r['agree']]
    path = f'{a.out}/{name}.jsonl'; have = {json.loads(l)['id'] for l in open(path)} if os.path.exists(path) else set(); todo = [r for r in rows if r['id'] not in have]; lock = threading.Lock(); print(name, len(todo), 'problems ×', a.samples, flush=True)
    def one(r):
        outs = []
        for k in range(a.samples):
            try: sol = chat(url, model, PROMPT.format(p=r['problem_el']), 0.0 if k == 0 else 0.7, 100 + k)
            except Exception as e: sol = f'ERROR {e}'
            fa = M.final_answer(sol); outs.append(dict(k=k, greedy=(k == 0), solution=sol, final=fa, correct=M.equiv(fa, r['final_answer']), fmt=M.fmt_checks(sol)))
        with lock, open(path, 'a') as f: f.write(json.dumps(dict(id=r['id'], grade=r['grade'], topic=r['topic'], surface=r['surface'], ref=r['final_answer'], agree=r['agree'], samples=outs), ensure_ascii=False) + '\n')
    with ThreadPoolExecutor(a.workers) as pool: list(pool.map(one, todo))
    res = [json.loads(l) for l in open(path)]; rate = lambda xs: round(sum(xs) / len(xs), 3) if xs else None
    by = lambda key: {k: dict(n=len(v), greedy=rate([x['samples'][0]['correct'] for x in v]), any_of_samples=rate([any(s['correct'] for s in x['samples']) for x in v])) for k, v in sorted(collections.defaultdict(list, {k: [x for x in res if key(x) == k] for k in {key(x) for x in res}}).items())}
    summ = dict(target=name, n=len(res), greedy_acc=rate([x['samples'][0]['correct'] for x in res]), pass_at_k=rate([any(s['correct'] for s in x['samples']) for x in res]), mean_sample_acc=rate([s['correct'] for x in res for s in x['samples']]),
                by_grade=by(lambda x: x['grade']), by_topic=by(lambda x: x['topic']), by_surface=by(lambda x: x['surface']), loop_rate=rate([len(s['solution']) > 2500 for x in res for s in x['samples']]),
                formatting={k: rate([s['fmt'][k] for x in res for s in x['samples']]) for k in ('decimal_comma_ok', 'euro_after_number', 'answer_line')})
    json.dump(summ, open(f'{a.out}/{name}_summary.json', 'w'), ensure_ascii=False, indent=1); print(json.dumps(summ, ensure_ascii=False))


if __name__ == '__main__': main()
