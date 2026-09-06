#!/usr/bin/env python3
"""Gate: forbidden identity wording (owner 2026-09-06). Fails rows whose assistant turns say the model was trained/made on Alps or at
CSCS, or «στο πλαίσιο του έργου/προγράμματος GlossAPI». Naming CSCS as a co-creator of Apertus itself (ETH Zürich, EPFL, CSCS) is allowed.
Usage: python3 wording_gate.py <rows.jsonl> [...] → offending ids, exit 1 if any."""
import json, sys, re
BAD = re.compile(r'(Alps|υπερυπολογιστ\S* (Alps|του CSCS)|(εκπαιδεύτηκ|εκπαιδευτηκ|έγινε|εγινε|τρέχ|φτιάχτηκ)\w* (στο|στον|στην) (CSCS|υπερυπολογιστ)|(πλαίσιο|πλαισιο) του (έργου|εργου|προγράμματος|προγραμματος) GlossAPI|(πρόγραμμα|προγραμμα|έργο|εργο) GlossAPI|GlossAPI (project|programme|program)\b|trained (on|at) (Alps|CSCS))', re.I)
code = 0
for path in sys.argv[1:]:
    rows = [json.loads(l) for l in open(path)]; bad = {}
    for r in rows:
        for m in r['messages']:
            if m['role'] != 'assistant': continue
            mm = BAD.search(m['content'])
            if mm: bad[r.get('id')] = mm.group(0); break
    print(f'== {path}: {len(rows)} rows, {len(bad)} with forbidden wording' + (': ' + ', '.join(f'{k} («{v}»)' for k, v in bad.items()) if bad else ''))
    if bad: code = 1
print('GATE OK' if code == 0 else 'GATE FAIL'); sys.exit(code)
