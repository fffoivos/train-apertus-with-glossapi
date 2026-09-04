#!/usr/bin/env python3
"""Aggregate the native-suite shards of results/<label>/native/*/metrics.csv into the 8 benchmark accuracies + macro,
next to the CPT card's numbers for the base. Usage: native_summary.py <label> [<label> ...]"""
import csv, glob, sys, os, json
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARD = {'asep_mcqa': 0.562, 'demosqa': 0.469, 'gpcr': 0.608, 'medical_mcqa': 0.425, 'oyxoy_metaphor': 0.345, 'oyxoy_nli': 0.651, 'oyxoy_wic': 0.549, 'oyxoy_wsd_definition': 0.385}
def summarize(label):
    agg = {}
    files = glob.glob(f'{HERE}/results/{label}/native/*/metrics.csv')
    for f in files:
        for r in csv.DictReader(open(f)):
            b = r['benchmark']; n = int(float(r['n'] or 0)); c = float(r['correct'] or 0)
            a = agg.setdefault(b, [0, 0]); a[0] += c; a[1] += n
    acc = {b: (a[0] / a[1] if a[1] else None) for b, a in agg.items()}
    return acc, len(files)
out = {}
for label in sys.argv[1:]:
    acc, nf = summarize(label); out[label] = acc
    vals = [v for v in acc.values() if v is not None]
    macro = sum(vals) / len(vals) if vals else None
    print(f'== {label}: {nf} shard files, benchmarks {len(acc)}/8, macro {macro:.3f}' if macro else f'== {label}: {nf} shard files, no data')
    for b in CARD:
        v = acc.get(b); print(f'   {b:22} {v if v is None else round(v,3)!s:>8}  card(base) {CARD[b]:.3f}  {"" if v is None else f"{v-CARD[b]:+.3f}"}')
json.dump(out, open(f'{HERE}/results/native_summary.json', 'w'), indent=1)
