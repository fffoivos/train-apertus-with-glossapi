#!/usr/bin/env python3
"""Final-answer check on OpenMathInstruct-2 rows: the boxed answer in generated_solution must equal expected_answer.
Usage: python3 verify_openmath.py <raw.jsonl> <out_dir>"""
import json, sys, os, re, collections
IN, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
def boxed(s):
    i = s.rfind('\\boxed{')
    if i < 0: return None
    j = i + 7; depth = 1; out = []
    while j < len(s) and depth:
        c = s[j]
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0: break
        out.append(c); j += 1
    return ''.join(out)
def norm(x):
    if x is None: return None
    x = str(x).strip().replace('\\%', '').replace('%', '').replace('$', '').replace(',', '').replace('\\,', '').strip()
    x = re.sub(r'\\text\{([^}]*)\}', r'\1', x).replace('\\dfrac', '\\frac').replace(' ', '')
    m = re.fullmatch(r'-?\d+(\.\d+)?', x)
    if m:
        f = float(x); return str(int(f)) if f == int(f) else str(f)
    m = re.fullmatch(r'\\frac\{(-?\d+)\}\{(\d+)\}', x)
    if m: return str(int(m.group(1)) / int(m.group(2)))
    return x.lower()
stats = collections.Counter(); keep, wrong, unk = [], [], []
for line in open(IN):
    r = json.loads(line); stats['rows'] += 1; rid = r.get('_row')
    b = boxed(r.get('generated_solution') or ''); e = r.get('expected_answer')
    if b is None or e in (None, ''): unk.append(rid); stats['no_box_or_answer'] += 1; continue
    if norm(b) == norm(e): keep.append(rid); stats['match'] += 1
    else: wrong.append(rid); stats['mismatch'] += 1
for name, lst in (('keep', keep), ('wrong', wrong), ('unchecked', unk)):
    open(f'{OUT}/{name}_ids.txt', 'w').write('\n'.join(str(x) for x in lst) + '\n')
json.dump(dict(stats), open(f'{OUT}/summary.json', 'w'), indent=1); print(dict(stats))
