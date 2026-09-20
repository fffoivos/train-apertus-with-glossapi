#!/usr/bin/env python3
"""Rendered row lengths of the launch manifest with the trainer's own tokenize_messages (astra gate-2 v6 M4): max, percentiles, rows over max_length, the
longest ids. Prints one JSON line RENDERED_LENGTHS {...}. python cluster/rendered_lengths.py --config cluster/configs/R4_full.yaml --train ... --dev ..."""
import argparse, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sft_train as T
ap = argparse.ArgumentParser(); ap.add_argument('--config', required=True); ap.add_argument('--train', required=True); ap.add_argument('--dev', required=True); a = ap.parse_args()
config = T.load_config(a.config); tok = T.prepare_tokenizer(config); tok = tok[0] if isinstance(tok, tuple) else tok; L = int(config['max_length']); res = {}
for name, path in (('train', a.train), ('dev', a.dev)):
    lens = []
    for l in open(path):
        r = json.loads(l); n = len(T.tokenize_messages(tok, r['messages'])['input_ids']); lens.append((n, r['id']))
    lens.sort(reverse=True); ns = [n for n, _ in lens]; tot = len(ns)
    pct = lambda p: sorted(ns)[min(tot - 1, int(p * tot))]
    res[name] = dict(rows=tot, tokens=sum(ns), max=ns[0], over_max_length=sum(1 for n in ns if n > L), p50=pct(0.5), p90=pct(0.9), p99=pct(0.99), longest=[dict(id=i, tokens=n) for n, i in lens[:5]])
res['max_length'] = L; res['method'] = 'sft_train.tokenize_messages (the same rendering the trainer validates every row with; a row over max_length fails the dry-run: truncation is forbidden)'
print('RENDERED_LENGTHS', json.dumps(res))
