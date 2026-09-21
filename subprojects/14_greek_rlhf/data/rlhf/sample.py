#!/usr/bin/env python3
"""Sample n replies per prompt from an OpenAI-compatible endpoint (vLLM). Usage:
python3 data/rlhf/sample.py <endpoint_base e.g. http://127.0.0.1:8000/v1> <served_model> <prompts.jsonl> <out samples.jsonl> [--n 4] [--temperature 0.8] [--top-p 0.95] [--max-tokens 1500] [--workers 8]
Output rows: {id, k, text, finish, model, usage}; resumable (existing ids skipped)."""
import json, sys, argparse, urllib.request, concurrent.futures, time, os
ap = argparse.ArgumentParser(); ap.add_argument('base'); ap.add_argument('model'); ap.add_argument('prompts'); ap.add_argument('out')
ap.add_argument('--n', type=int, default=4); ap.add_argument('--temperature', type=float, default=0.8); ap.add_argument('--top-p', type=float, default=0.95)
ap.add_argument('--max-tokens', type=int, default=1500); ap.add_argument('--workers', type=int, default=8); a = ap.parse_args()
rows = [json.loads(l) for l in open(a.prompts) if l.strip()]
done = {json.loads(l)['id'] for l in open(a.out)} if os.path.exists(a.out) else set()
def one(r, tries=4):
    n = int(r.get('n') or a.n)   # per-row sample budget (plan §25: 4 default, 8 IF/dialogue, 16 verifiable maths)
    body = json.dumps(dict(model=a.model, messages=r['messages'], n=n, temperature=a.temperature, top_p=a.top_p, max_tokens=a.max_tokens)).encode()
    for t in range(tries):
        try:
            req = urllib.request.Request(a.base.rstrip('/') + '/chat/completions', data=body, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=600) as resp: d = json.load(resp)
            return [dict(id=r['id'], k=i, text=c['message']['content'], finish=c.get('finish_reason'), model=a.model, usage=d.get('usage')) for i, c in enumerate(d['choices'])]
        except Exception as e:
            if t == tries - 1: return [dict(id=r['id'], k=-1, error=str(e)[:300])]
            time.sleep(5 * (t + 1))
todo = [r for r in rows if r['id'] not in done]; print(f'{len(todo)} prompts to sample (n={a.n}), {len(done)} already done', flush=True)
with open(a.out, 'a') as h, concurrent.futures.ThreadPoolExecutor(a.workers) as ex:
    for i, res in enumerate(ex.map(one, todo), 1):
        for x in res: h.write(json.dumps(x, ensure_ascii=False) + '\n')
        h.flush()
        if i % 10 == 0 or i == len(todo): print(f'{i}/{len(todo)} prompts', flush=True)
print('SAMPLE_DONE')
