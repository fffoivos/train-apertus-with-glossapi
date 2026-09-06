#!/usr/bin/env python3
"""Gate: no row may leave with an unresolved declared placeholder ([ΟΝΟΜΑ], [ΗΜΕΡΟΜΗΝΙΑ ΓΝΩΣΗΣ], [ΑΔΕΙΑ], ...).
Declared placeholders and their settled values come from identity_facts.json ("placeholders" = declared, "settled" = value or null).
Usage: python3 placeholder_gate.py <rows.jsonl> [<rows.jsonl> ...] [--apply <out.jsonl>]
  Without --apply: prints counts per placeholder and per file, lists row ids, exits 1 if any declared placeholder remains.
  With --apply (single input): substitutes every placeholder that has a settled value, writes the result, and STILL exits 1 if
  any placeholder without a settled value remains. Other bracketed blanks (form templates such as [Ονοματεπώνυμο], [ΑΦΜ]) are
  reported as 'other brackets' and never fail the gate."""
import json, sys, os, re, collections
HERE = os.path.dirname(os.path.abspath(__file__))
ident = json.load(open(os.path.join(HERE, 'identity_facts.json')))
declared = list(ident.get('placeholders', {}).keys()); settled = ident.get('settled', {})
args = [a for a in sys.argv[1:]]; apply_out = None
if '--apply' in args:
    i = args.index('--apply'); apply_out = args[i + 1]; args = args[:i] + args[i + 2:]
    assert len(args) == 1, '--apply takes exactly one input file'
OTHER = re.compile(r'\[[^\]\n]{2,60}\]')
exit_code = 0
for path in args:
    rows = [json.loads(l) for l in open(path)]
    per = collections.Counter(); ids = collections.defaultdict(list); other = collections.Counter(); rows_hit = 0
    for r in rows:
        hit = False
        for m in r['messages']:
            for ph in declared:
                n = m['content'].count(ph)
                if n: per[ph] += n; hit = True; ids[ph].append(r.get('id'))
            for b in OTHER.findall(m['content']):
                if b not in declared: other[b] += 1
        rows_hit += hit
    print(f'== {path}: {len(rows)} rows, {rows_hit} rows with declared placeholders')
    for ph in declared:
        val = settled.get(ph); state = f'settled → «{val}»' if val else 'NO SETTLED VALUE'
        print(f'   {per[ph]:4d}  {ph}  [{state}]' + (f'  ids: {", ".join(dict.fromkeys(ids[ph]))}' if per[ph] and per[ph] <= 12 else ''))
    if other: print('   other brackets (form blanks, not gated): ' + ', '.join(f'{k}×{v}' for k, v in other.most_common(8)))
    unresolved = sum(per[ph] for ph in declared if not settled.get(ph))
    if apply_out:
        n_sub = 0
        for r in rows:
            for m in r['messages']:
                for ph in declared:
                    val = settled.get(ph)
                    if val and ph in m['content']: n_sub += m['content'].count(ph); m['content'] = m['content'].replace(ph, val)
        with open(apply_out, 'w') as f:
            for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
        print(f'   applied {n_sub} substitutions → {apply_out}')
    remaining = unresolved if apply_out else sum(per.values())
    if remaining: exit_code = 1; print(f'   GATE FAIL: {remaining} placeholder occurrences remain')
    else: print('   GATE OK')
sys.exit(exit_code)
