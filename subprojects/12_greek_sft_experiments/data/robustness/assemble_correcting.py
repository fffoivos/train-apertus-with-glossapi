#!/usr/bin/env python3
"""Turn correcting-set dialogues into SFT rows (one row per dialogue, per-turn train flags), with the selection rules from the design (§8):
a target turn keeps train=true only if its typed checks pass, the responder assessed it ok (or it is a recovery/misquote/closing turn whose checks pass),
and its self-check verdict is not wrong/evasive; planted turns and rejected targets are train=false (context only). Rows with no trainable turn are dropped.
Writes rows.jsonl + summary.json. Usage: python3 assemble_correcting.py <dialogues.jsonl> <out_dir>"""
import json, os, sys, collections


def main():
    src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True); rows = []; stats = collections.Counter(); kinds = collections.Counter()
    for l in open(src):
        d = json.loads(l); msgs = []; n_train = 0; ti = 0
        for m in d['messages']:
            if m['role'] == 'user': msgs.append(dict(role='user', content=m['content'])); continue
            t = d['turns'][ti] if ti < len(d['turns']) else {}; ti += 1
            ok = bool(t.get('train')) and bool(t.get('checks', {}).get('ok')) and t.get('assessment') in ('ok', 'confronted', None) and t.get('self_check_verdict') not in ('wrong', 'evasive')
            if t.get('kind', '').startswith('recovery') or t.get('kind', '').startswith('misquote'): ok = bool(t.get('train')) and bool(t.get('checks', {}).get('ok')) and t.get('self_check_verdict') not in ('wrong', 'evasive')
            stats['target_kept' if ok else ('planted' if not t.get('train') else 'target_rejected')] += 1; kinds[t.get('kind', '?').split(':')[0] + (':' + t['kind'].split(':')[1] if t.get('kind', '').count(':') else '')] += ok
            msgs.append(dict(role='assistant', content=m['content'], train=ok, kind=t.get('kind'), assessment=t.get('assessment'), verdict=t.get('self_check_verdict')))
            n_train += ok
        if n_train: rows.append(dict(source='correcting', id=d['id'], intent=d['intent'], surface=d['surface'], temperament=d['temperament'], plants=d['plants'], n_turns=len(d['turns']), n_train=n_train, turns=msgs, user=msgs[-2]['content'] if len(msgs) >= 2 else '', assistant=msgs[-1]['content']))
        else: stats['dialogue_dropped'] += 1
    with open(os.path.join(out, 'rows.jsonl'), 'w') as f: [f.write(json.dumps(r, ensure_ascii=False) + '\n') for r in rows]
    summ = dict(dialogues_in=sum(1 for _ in open(src)), rows=len(rows), trainable_turns=sum(r['n_train'] for r in rows), stats=dict(stats), trainable_by_kind=dict(kinds), plants=dict(collections.Counter(p for r in rows for p in r['plants'])))
    json.dump(summ, open(os.path.join(out, 'summary.json'), 'w'), ensure_ascii=False, indent=1); print(json.dumps(summ, ensure_ascii=False))


if __name__ == '__main__': main()
