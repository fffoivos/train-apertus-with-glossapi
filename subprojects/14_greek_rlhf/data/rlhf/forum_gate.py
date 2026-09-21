#!/usr/bin/env python3
"""Context gate + rewrite for forum opening posts (plan §17): batches of up to 6 posts of the same forum per Sol call. Usage:
python3 data/rlhf/forum_gate.py <candidates.jsonl> <out gated.jsonl> [--batch 6] [--workers 16] [--effort medium] [--limit-per-forum N]. Resumable by id."""
import json, sys, os, argparse, concurrent.futures, collections, hashlib, pathlib, time
HERE = pathlib.Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent / 'math')); from codex_server import CodexServer
ap = argparse.ArgumentParser(); ap.add_argument('cands'); ap.add_argument('out'); ap.add_argument('--batch', type=int, default=6); ap.add_argument('--workers', type=int, default=16)
ap.add_argument('--effort', default='medium'); ap.add_argument('--model', default='gpt-5.6-sol'); ap.add_argument('--limit-per-forum', type=int, default=0); a = ap.parse_args()
PROMPT = open(HERE / 'prompts/forum_gate_rewrite_el.txt', encoding='utf-8').read(); PSHA = hashlib.sha256(PROMPT.encode()).hexdigest()[:16]
FRAMES = json.load(open(HERE / 'forum_frames.json'))
ITEM = {'type': 'object', 'properties': {'id': {'type': 'string'}, 'post_kind': {'type': 'string'}, 'false_premise': {'type': 'object', 'properties': {'present': {'type': 'boolean'}, 'what_el': {'type': ['string', 'null']}}, 'required': ['present', 'what_el'], 'additionalProperties': False}, 'self_contained': {'type': 'boolean'}, 'flags': {'type': 'object', 'properties': {k: {'type': 'boolean'} for k in ('forum_default', 'op_context', 'world_anchor')}, 'required': ['forum_default', 'op_context', 'world_anchor'], 'additionalProperties': False}, 'reason_el': {'type': 'string'}, 'prompt_el': {'type': ['string', 'null']}, 'task_type': {'type': ['string', 'null']}, 'kept_details': {'type': 'array', 'items': {'type': 'string'}}}, 'required': ['id', 'post_kind', 'self_contained', 'flags', 'reason_el', 'prompt_el', 'false_premise', 'task_type', 'kept_details'], 'additionalProperties': False}
SCHEMA = {'type': 'object', 'properties': {'items': {'type': 'array', 'items': ITEM}}, 'required': ['items'], 'additionalProperties': False}
rows = [json.loads(l) for l in open(a.cands) if l.strip()]; done = {json.loads(l)['id'] for l in open(a.out)} if os.path.exists(a.out) else set()
by_forum = collections.defaultdict(list)
for r in rows:
    if r['id'] in done: continue
    if a.limit_per_forum and len(by_forum[r['forum']]) >= a.limit_per_forum: continue
    by_forum[r['forum']].append(r)
batches = [(f, grp[i:i + a.batch]) for f, grp in by_forum.items() for i in range(0, len(grp), a.batch)]
srv = CodexServer(); srv.start()
def run(job):
    forum, grp = job; frame = FRAMES.get(forum, forum)
    posts = '\n\n'.join(f"--- POST id={r['id']} ---\nTitle: {r['title']}\n{r['text']}" for r in grp)
    text = f"{PROMPT}\n\n=== THE FORUM ===\n{frame}\n\n=== POSTS ===\n{posts}\n\n=== END ==="
    t0 = time.time()
    for attempt in range(3):
        try:
            v = srv.call(text, SCHEMA, model=a.model, effort=a.effort, timeout=900); got = {it['id']: it for it in v['items']}
            if set(got) != {r['id'] for r in grp}: raise ValueError('ids mismatch')
            return [dict(r, gate=got[r['id']], prompt_sha=PSHA, secs=round(time.time() - t0, 1)) for r in grp]
        except Exception as e: err = str(e)[:300]
    return [dict(r, gate=None, error=err, prompt_sha=PSHA) for r in grp]
print(f'{len(batches)} calls for {sum(len(g) for _, g in batches)} posts (prompt {PSHA})', flush=True)
n_ok = 0
with open(a.out, 'a') as h, concurrent.futures.ThreadPoolExecutor(a.workers) as ex:
    for i, res in enumerate(ex.map(run, batches), 1):
        for r in res:
            h.write(json.dumps(r, ensure_ascii=False) + '\n'); n_ok += bool(r.get('gate') and r['gate']['self_contained'])
        h.flush()
        if i % 5 == 0 or i == len(batches): print(f'{i}/{len(batches)} calls, {n_ok} accepted so far', flush=True)
srv.close(); print('GATE_DONE')
