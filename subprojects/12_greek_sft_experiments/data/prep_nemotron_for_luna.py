#!/usr/bin/env python3
"""Prepare the Nemotron chat block for the judge: exact-token length filter (rows over the trainer window can never train, so do not
judge them), shuffle (the export order is not uniform), split into two halves (option C needs only the first).
Usage: <venv python> prep_nemotron_for_luna.py <in.jsonl> <out_a.jsonl> <out_b.jsonl> [max_tokens=4032]"""
import json, sys, random, collections
IN, OA, OB = sys.argv[1], sys.argv[2], sys.argv[3]; MAXT = int(sys.argv[4]) if len(sys.argv) > 4 else 4032; random.seed(2026)
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained('fffoivos/apertus-8b-greek-cpt', revision='18-avg-uniform5-tokens30B-50B')
tok.chat_template = AutoTokenizer.from_pretrained('swiss-ai/Apertus-8B-Instruct-2509').chat_template
def n_tokens(turns):
    msgs = [dict(role=t['role'], content=t.get('content') or '') for t in turns if t.get('role') in ('system', 'user', 'assistant') and (t.get('content') or '').strip()]
    if not msgs: return 10**9
    ids = tok.apply_chat_template(msgs, tokenize=True)
    if hasattr(ids, 'keys'): ids = ids['input_ids']
    return len(ids)
keep = []; c = collections.Counter()
for i, l in enumerate(open(IN)):
    r = json.loads(l); c['rows'] += 1
    n = n_tokens(r['turns']); r['tokens'] = n
    if n > MAXT: c['too_long'] += 1; continue
    keep.append(l.rstrip('\n')); c['kept'] += 1
    if i % 20000 == 0: print(i, dict(c), flush=True)
random.shuffle(keep); h = len(keep) // 2
open(OA, 'w').write('\n'.join(keep[:h]) + '\n'); open(OB, 'w').write('\n'.join(keep[h:]) + '\n')
print('DONE', dict(c), 'a', h, 'b', len(keep) - h, flush=True)
