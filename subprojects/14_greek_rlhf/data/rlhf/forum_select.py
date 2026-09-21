#!/usr/bin/env python3
"""Select N accepted forum prompts per forum from the gated files (uniform, seeded) and write pool rows + a receipt.
Usage: python3 data/rlhf/forum_select.py <out.jsonl> <gated.jsonl> [<gated2.jsonl> ...] [--per-forum 50] [--max-words 120]"""
import json, sys, random, argparse, collections, hashlib
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('gated', nargs='+'); ap.add_argument('--per-forum', type=int, default=50); ap.add_argument('--max-words', type=int, default=0, help='0 = no length cap (owner 16 Sept: length follows context density); a rewrite longer than 1.5x the raw post is flagged instead'); ap.add_argument('--seed', type=int, default=916); a = ap.parse_args()
rng = random.Random(a.seed); by = collections.defaultdict(list); stats = collections.defaultdict(collections.Counter)
for f in a.gated:
    for l in open(f):
        r = json.loads(l); g = r.get('gate'); st = stats[r['forum']]; st['gated'] += 1
        if not g: st['error'] += 1; continue
        if g.get('post_kind') in ('declaration_or_announcement', 'advertisement'): st['kind_' + g['post_kind']] += 1; continue
        if not g['self_contained']: st['rejected'] += 1; continue
        if g.get('post_kind'): st['kind_' + g['post_kind']] += 1
        if (g.get('false_premise') or {}).get('present'): st['false_premise'] += 1
        if a.max_words and len((g['prompt_el'] or '').split()) > a.max_words: st['too_long'] += 1; continue
        if len((g['prompt_el'] or '').split()) > 1.5 * max(1, r.get('words', 0)): st['longer_than_raw'] += 1   # flagged, kept
        st['accepted'] += 1; by[r['forum']].append(r)
out = []
for forum, rows in sorted(by.items()):
    rng.shuffle(rows)
    for r in rows[:a.per_forum]:
        out.append(dict(id=f"forum:{forum}:{hashlib.sha256(r['url'].encode()).hexdigest()[:10]}", slice='forum', source=f"{forum} {r['url']}", messages=[dict(role='user', content=r['gate']['prompt_el'])], task_type=r['gate']['task_type'], post_kind=r['gate'].get('post_kind'), false_premise=r['gate'].get('false_premise'), raw=r['text'], kept_details=r['gate']['kept_details'], prompt_sha=r.get('prompt_sha')))
    stats[forum]['selected'] = min(len(rows), a.per_forum)
with open(a.out, 'w') as h:
    for o in out: h.write(json.dumps(o, ensure_ascii=False) + '\n')
json.dump(dict(per_forum=a.per_forum, max_words=a.max_words, seed=a.seed, stats={k: dict(v) for k, v in stats.items()}), open(a.out.replace('.jsonl', '_receipt.json'), 'w'), indent=1, ensure_ascii=False)
print('selected', len(out), 'prompts;', {k: dict(v) for k, v in stats.items()})
