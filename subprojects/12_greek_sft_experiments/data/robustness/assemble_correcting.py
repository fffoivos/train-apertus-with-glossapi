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
            content_ok = bool((m.get('content') or '').strip())
            why = []
            if not t.get('train'): why.append('planted')
            if not content_ok: why.append('empty')
            if not t.get('checks', {}).get('ok'): why.append('checks:' + ','.join(k for k, v in t.get('checks', {}).items() if k != 'ok' and v and k != 'questions') + (f",questions={t.get('checks', {}).get('questions')}" if (t.get('checks', {}).get('questions') or 0) > 1 else ''))
            conditional = bool((t.get('assumption') or '').strip()) and t.get('assessment') == 'wrong' and t.get('move') in ('give_info', 'follow_up', 'change_request')
            if t.get('assessment') not in ('ok', 'confronted', None) and not conditional: why.append('assessment:' + str(t.get('assessment')))   # astra scale review H2: a clearly conditional answer (stated assumption) answered by the user supplying the facts is not wrong
            if conditional: stats['kept_conditional_despite_wrong'] += 1
            if t.get('self_check_verdict') in ('wrong', 'evasive'): why.append('verdict:' + t['self_check_verdict'])
            ok = not why   # F1 (astra pilot review): the same gate for ideal, recovery, misquote, clarify and closing turns; empty content never supervised
            if ok: stats['target_kept'] += 1
            elif not t.get('train'): stats['planted'] += 1
            else:
                stats['target_rejected'] += 1
                for w in why: stats['reject:' + w.split(':')[0]] += 1
            if ok and t.get('after_claim'): stats['kept_after_claim_' + t['after_claim']] += 1
            if ok and t.get('kind') == 'clarify': stats['kept_clarify'] += 1
            kinds[t.get('kind', '?').split(':')[0] + (':' + t['kind'].split(':')[1] if t.get('kind', '').count(':') else '')] += ok
            msgs.append(dict(role='assistant', content=m['content'], train=ok, kind=t.get('kind'), assessment=t.get('assessment'), verdict=t.get('self_check_verdict'), reject=(None if ok else ';'.join(why))))
            n_train += ok
        if n_train: rows.append(dict(source='correcting', id=d['id'], intent=d['intent'], surface=d['surface'], temperament=d['temperament'], plants=d['plants'], n_turns=len(d['turns']), n_train=n_train, turns=msgs, user=msgs[-2]['content'] if len(msgs) >= 2 else '', assistant=msgs[-1]['content']))
        else: stats['dialogue_dropped'] += 1
    with open(os.path.join(out, 'rows.jsonl'), 'w') as f: [f.write(json.dumps(r, ensure_ascii=False) + '\n') for r in rows]
    summ = dict(dialogues_in=sum(1 for _ in open(src)), rows=len(rows), trainable_turns=sum(r['n_train'] for r in rows), stats=dict(stats), trainable_by_kind=dict(kinds), plants=dict(collections.Counter(p for r in rows for p in r['plants'])))
    json.dump(summ, open(os.path.join(out, 'summary.json'), 'w'), ensure_ascii=False, indent=1); print(json.dumps(summ, ensure_ascii=False))


if __name__ == '__main__': main()
