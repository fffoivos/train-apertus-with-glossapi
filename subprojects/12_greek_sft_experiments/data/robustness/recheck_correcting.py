#!/usr/bin/env python3
"""Recompute the typed checks of every supervised turn in a correcting-set dialogues file with the current build_correcting.checks (after a check fix),
without new Sol calls. Usage: python3 recheck_correcting.py <dialogues.jsonl> [<out.jsonl>]  (default: rewrite in place, keeping a .bak)"""
import json, os, shutil, sys, collections
sys.argv += []; HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_correcting as B
src = sys.argv[1]; dst = sys.argv[2] if len(sys.argv) > 2 else src
rows = [json.loads(l) for l in open(src)]; flips = collections.Counter()
for d in rows:
    msgs = d['messages']; turns = d['turns']; ai = [i for i, m in enumerate(msgs) if m['role'] == 'assistant']
    assert len(ai) == len(turns), (d['id'], len(ai), len(turns))
    prev = []
    for t, i in zip(turns, ai):
        ans = msgs[i]['content']; user_msg = msgs[i - 1]['content'] if i and msgs[i - 1]['role'] == 'user' else ''
        kind = t.get('kind') or ''
        if not kind.startswith('planted') and t.get('checks') is not None:
            plant = kind.split(':')[1] if ':' in kind else None
            planted_text = None
            if kind == 'recovery' and prev:
                planted_text = prev[-1]; plant = turns[turns.index(t) - 1].get('kind', '').split(':')[-1] or None
            new = B.checks('recovery' if kind == 'recovery' else kind, ans, prev, user_msg, planted_text, plant)
            if bool(new['ok']) != bool(t['checks'].get('ok')): flips[(kind.split(':')[0], t['checks'].get('ok'), new['ok'])] += 1
            t['checks'] = new
        prev.append(ans)
if dst == src: shutil.copy(src, src + '.bak')
with open(dst, 'w') as f:
    for d in rows: f.write(json.dumps(d, ensure_ascii=False) + '\n')
print('rechecked', len(rows), 'dialogues; ok flips (kind, old, new):', dict(flips))
