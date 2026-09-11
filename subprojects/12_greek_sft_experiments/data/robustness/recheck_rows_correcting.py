#!/usr/bin/env python3
"""Post-edit gate for correcting-set SFT rows (astra scale review H7 / DATA_TODO 29 analogue): re-run the typed checks on every supervised
assistant turn of the EDITED rows; a turn that fails after editing becomes context (train=false); rows left without a supervised turn are
dropped. Usage: python3 recheck_rows_correcting.py <rows_edited.jsonl> <out_rows.jsonl>"""
import json, sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import build_correcting as B
src, dst = sys.argv[1], sys.argv[2]; rows = [json.loads(l) for l in open(src)]; stats = collections.Counter(); out = []
for r in rows:
    t = r.get('turns') or r['messages']; prev = []; planted = None; changed = False
    for i, m in enumerate(t):
        if m['role'] != 'assistant': continue
        user_msg = t[i - 1]['content'] if i and t[i - 1]['role'] == 'user' else ''
        if m.get('train'):
            kind = (m.get('kind') or 'ideal').split(':')[0]; kind = 'recovery' if kind in ('recovery', 'misquote_recovery') else ('clarify' if kind == 'clarify' else 'ideal')
            c = B.checks(kind, m['content'], prev, user_msg, planted_text=(planted if kind == 'recovery' else None), plant=(m.get('kind') or '').split(':')[-1] if ':' in (m.get('kind') or '') else None)
            if not c['ok'] or not m['content'].strip():
                m['train'] = False; m['reject'] = 'post_edit:' + ','.join(k for k, v in c.items() if k != 'ok' and v and k != 'questions'); stats['demoted_after_edit'] += 1; changed = True
            else: stats['kept'] += 1
        else: stats['context'] += 1
        planted = m['content'] if (m.get('kind') or '').startswith('planted') else None; prev.append(m['content'])
    if any(m['role'] == 'assistant' and m.get('train') for m in t): out.append(r)
    else: stats['rows_dropped'] += 1
with open(dst, 'w') as f:
    for r in out: f.write(json.dumps(r, ensure_ascii=False) + '\n')
summ = dict(rows_in=len(rows), rows_out=len(out), **stats); json.dump(summ, open(dst + '.summary.json', 'w'), indent=1); print(json.dumps(summ))
