#!/usr/bin/env python3
"""Uniform per-forum sample of opening posts for the RLHF forum slice (owner, 16 Sept): every forum config, only discussions with ≥ 1 reply,
crude deterministic filter on the deidentified opening post (initial_request.prompt_text), N candidates per forum drawn uniformly (seeded).
Usage: python3 data/rlhf/forum_sample.py <snapshot_dir> <out.jsonl> [--per-forum 150] [--seed 916]"""
import json, sys, gzip, re, random, argparse, pathlib, collections
ap = argparse.ArgumentParser(); ap.add_argument('snapshot'); ap.add_argument('out'); ap.add_argument('--per-forum', type=int, default=150); ap.add_argument('--seed', type=int, default=916); ap.add_argument('--forums', default=''); a = ap.parse_args()
rng = random.Random(a.seed); stats = collections.OrderedDict(); out = []
CONT = re.compile(r'παραπάνω|πιο πάνω|στο άλλο νήμα|στο προηγούμενο|όπως είπα|όπως έγραψα|συνημμ|επισυνάπτω|attach|screenshot|φωτο', re.I)
for fdir in sorted(pathlib.Path(a.snapshot, 'data').iterdir()):
    forum = fdir.name; cands = []; n = n_reply = 0
    if a.forums and forum not in a.forums.split(','): continue
    for shard in sorted(fdir.glob('*.jsonl.gz')):
        with gzip.open(shard, 'rt') as h:
            for line in h:
                d = json.loads(line); n += 1
                if int(d.get('post_count') or 0) < 2: continue
                n_reply += 1; ir = d.get('initial_request') or {}; t = (ir.get('prompt_text') or '').strip(); w = len(t.split())
                if not (15 <= w <= 300): continue
                if not ('?' in t or ';' in t or re.search(r'\b(πώς|πως|γιατί|τι |ποι[οαεά]|μπορ|ξέρει|ξερει|βοήθ|βοηθ|θα ήθελα|ψάχνω|υπάρχει)', t, re.I)): continue
                if len(re.findall(r'[Ͱ-Ͽ]', t)) < 1.5 * max(1, len(re.findall(r'[A-Za-z]', t))): continue   # product names are Latin on tech forums
                if ir.get('referenced_images') or ir.get('quote_references') or CONT.search(t) or 'http' in t: continue   # links are NOT a hard reject (myphone attaches one to almost every post); the Sol gate rejects link-dependent questions
                cands.append(dict(forum=forum, url=d.get('canonical_url'), section=(d.get('listing') or {}).get('forum_title'), post_count=int(d.get('post_count') or 0), title=(d.get('title') or '')[:200], text=t, words=w))
    rng.shuffle(cands); take = cands[:a.per_forum]; out += take
    stats[forum] = dict(discussions=n, with_reply=n_reply, candidates=len(cands), taken=len(take)); print(forum, stats[forum], flush=True)
with open(a.out, 'w') as h:
    for i, c in enumerate(out): h.write(json.dumps(dict(id=f"forum:{c['forum']}:{i:04d}", **c), ensure_ascii=False) + '\n')
json.dump(dict(seed=a.seed, per_forum=a.per_forum, stats=stats), open(a.out.replace('.jsonl', '_stats.json'), 'w'), indent=1, ensure_ascii=False)
print('written', len(out), 'candidates ->', a.out)
