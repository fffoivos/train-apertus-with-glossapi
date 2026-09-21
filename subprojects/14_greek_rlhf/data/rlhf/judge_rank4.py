#!/usr/bin/env python3
"""Rank four candidate replies per prompt with Sol under the frozen rubric (data/rlhf/prompts/judge_rank4_en.txt). Usage:
python3 data/rlhf/judge_rank4.py <prompts.jsonl> <samples.jsonl> <out judged.jsonl> [--workers 16] [--effort medium] [--rejudge-share 0.1]
Candidates are shuffled per call and mapped back; a share of prompts is judged twice in another order (self_agreement). Resumable."""
import json, sys, os, random, argparse, concurrent.futures, hashlib, time, pathlib
HERE = pathlib.Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent / 'math')); from codex_server import CodexServer
ap = argparse.ArgumentParser(); ap.add_argument('prompts'); ap.add_argument('samples'); ap.add_argument('out'); ap.add_argument('--workers', type=int, default=16)
ap.add_argument('--effort', default='medium'); ap.add_argument('--rejudge-share', type=float, default=0.1); ap.add_argument('--model', default='gpt-5.6-sol'); ap.add_argument('--rubric', default=str(HERE / 'prompts/judge_rank4_en.txt')); ap.add_argument('--schema', default='v1', choices=['v1', 'v2']); a = ap.parse_args()
RUBRIC = open(a.rubric, encoding='utf-8').read(); RUBRIC_SHA = hashlib.sha256(RUBRIC.encode()).hexdigest()[:16]
CAND = {'type': 'object', 'properties': {'disqualifiers': {'type': 'array', 'items': {'type': 'string'}}, 'scores': {'type': 'object', 'properties': {q: {'type': 'integer'} for q in ('Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7')}, 'required': ['Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7'], 'additionalProperties': False}, 'reason': {'type': 'string'}}, 'required': ['disqualifiers', 'scores', 'reason'], 'additionalProperties': False}
SCHEMA_V2 = {'type': 'object', 'properties': {'ranking': {'type': 'array', 'items': {'type': 'string'}}, 'ties': {'type': 'array', 'items': {'type': 'array', 'items': {'type': 'string'}}}, 'unusable': {'type': 'array', 'items': {'type': 'string'}}, 'verdicts': {'type': 'object', 'properties': {L: {'type': 'string'} for L in 'ABCD'}, 'required': ['A', 'B', 'C', 'D'], 'additionalProperties': False}, 'issues': {'type': 'object', 'properties': {L: {'type': 'array', 'items': {'type': 'string'}} for L in 'ABCD'}, 'required': ['A', 'B', 'C', 'D'], 'additionalProperties': False}, 'notes': {'type': 'object', 'properties': {L: {'type': 'string'} for L in 'ABCD'}, 'required': ['A', 'B', 'C', 'D'], 'additionalProperties': False}, 'best_vs_worst': {'type': 'string'}, 'confidence': {'type': 'string'}}, 'required': ['ranking', 'ties', 'unusable', 'verdicts', 'issues', 'notes', 'best_vs_worst', 'confidence'], 'additionalProperties': False}
SCHEMA = {'type': 'object', 'properties': {'candidates': {'type': 'object', 'properties': {L: CAND for L in 'ABCD'}, 'required': ['A', 'B', 'C', 'D'], 'additionalProperties': False}, 'ranking': {'type': 'array', 'items': {'type': 'string'}}, 'ties': {'type': 'array', 'items': {'type': 'array', 'items': {'type': 'string'}}}, 'best_has_disqualifier': {'type': 'boolean'}, 'margin_best_worst': {'type': 'integer'}}, 'required': ['candidates', 'ranking', 'ties', 'best_has_disqualifier', 'margin_best_worst'], 'additionalProperties': False}
prompts = {json.loads(l)['id']: json.loads(l) for l in open(a.prompts) if l.strip()}
samples = {}
for l in open(a.samples):
    if not l.strip(): continue
    s = json.loads(l)
    if s.get('k', -1) >= 0: samples.setdefault(s['id'], {})[s['k']] = s['text']
done = {(json.loads(l)['id'], json.loads(l).get('pass', 1)) for l in open(a.out)} if os.path.exists(a.out) else set()
def render(msgs):
    return '\n\n'.join(f"[{m['role'].upper()}]\n{m['content']}" for m in msgs)
def build(pid, order, texts):
    conv = render(prompts[pid]['messages']); cands = '\n\n'.join(f"=== CANDIDATE {L} ===\n{texts[k]}" for L, k in zip('ABCD', order))
    return f"{RUBRIC}\n\n=== CONVERSATION SO FAR ===\n{conv}\n\n{cands}\n\n=== END. Return the JSON object only. ==="
srv = CodexServer(); srv.start()
def judge(job):
    pid, pas = job; texts = samples[pid]; ks = sorted(texts); rng = random.Random(f'{pid}|{pas}'); order = ks[:]; rng.shuffle(order)
    t0 = time.time()
    for attempt in range(3):
        try:
            v = srv.call(build(pid, order, texts), SCHEMA_V2 if a.schema == 'v2' else SCHEMA, model=a.model, effort=a.effort, timeout=900)
            letters = dict(zip('ABCD', order)); rk = [letters[L] for L in v['ranking'] if L in letters]
            if len(set(rk)) != 4: raise ValueError('ranking incomplete')
            if a.schema == 'v2': by_k = {str(letters[L]): dict(note=v['notes'][L], unusable=L in v['unusable'], verdict=(v.get('verdicts') or {}).get(L), issues=(v.get('issues') or {}).get(L, [])) for L in 'ABCD'}
            else: by_k = {str(letters[L]): v['candidates'][L] for L in 'ABCD'}
            return dict(id=pid, **{'pass': pas}, order=order, ranking_k=rk, verdict=v, by_k=by_k, schema=a.schema, rubric_sha=RUBRIC_SHA, model=a.model, effort=a.effort, secs=round(time.time() - t0, 1))
        except Exception as e:
            err = str(e)[:300]
    return dict(id=pid, **{'pass': pas}, error=err, rubric_sha=RUBRIC_SHA)
jobs = [(pid, 1) for pid in prompts if pid in samples and len(samples[pid]) == 4 and (pid, 1) not in done]
rej = random.Random(916); jobs += [(pid, 2) for pid in prompts if pid in samples and len(samples[pid]) == 4 and (pid, 2) not in done and rej.random() < a.rejudge_share]
print(f'{len(jobs)} judge calls ({len(prompts)} prompts, rubric {RUBRIC_SHA})', flush=True)
with open(a.out, 'a') as h, concurrent.futures.ThreadPoolExecutor(a.workers) as ex:
    for i, r in enumerate(ex.map(judge, jobs), 1):
        h.write(json.dumps(r, ensure_ascii=False) + '\n'); h.flush()
        if i % 5 == 0 or i == len(jobs): print(f'{i}/{len(jobs)} judged', flush=True)
srv.close(); print('JUDGE_DONE')
