#!/usr/bin/env python3
"""Regenerate the per-block receipt table and totals in the recipe and description docs from data/arms/<arm>/receipt.json (between the
markers '<!-- receipt-table -->' and '<!-- /receipt-table -->', inserted on first use). Usage: python3 docs/fill_recipe_tables.py R3_single"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; arm = sys.argv[1]; r = json.load(open(HERE.parent / 'data' / 'arms' / arm / 'receipt.json')); prev = json.load(open(HERE / 'receipts_R2_stage1_final_20260906.json'))
prev_tok = {b['block']: b.get('tokens') for b in prev['blocks']}; rows = []; tot = dict(uniq=0, eff=0, tok=0, sup=0, dev=0, contam=0, dup=0, cdup=0, masked=0)
for b in r['blocks']:
    if b.get('status') != 'ok': continue
    u = b.get('train_unique_rows', 0); e = b.get('train_rows_effective', 0); t = b.get('tokens_train_effective', 0); s = b.get('supervised_tokens_effective') or 0; pt = prev_tok.get(b['block'])
    ch = 'new block' if pt is None else ('same weighting (×2) as stage 1; tokens differ by dedupe and re-decontamination' if b['block'] == 'greek_ours' else f'{(t - pt) / pt:+.0%} tokens (same rule, deduplicated, re-decontaminated)')
    if b['block'] == 'personality': ch = 'new in the single mix (×4, one epoch; arm B gave ×4 for two epochs after stage 1)'
    rows.append(f"| {b['block']} | {u:,} | {b['weight']} | {e:,} | {t/1e6:.1f}M | {s/1e6:.1f}M | {b.get('dev_rows', 0)} | {b['contaminated']} | {b.get('exact_duplicates_dropped', 0) + b.get('content_duplicates_dropped', 0)} | {b.get('masked_context_turns', 0)} | {ch} |")
    for k, v in zip(tot, (u, e, t, s, b.get('dev_rows', 0), b['contaminated'], b.get('exact_duplicates_dropped', 0), b.get('content_duplicates_dropped', 0), b.get('masked_context_turns', 0))): tot[k] += v
g1 = r['g1']; nh = r['train']['tokens'] / 32.5e6
table = ('<!-- receipt-table -->\n| block | unique train rows | copies | effective rows | rendered tokens | supervised tokens | dev rows | contaminated (dropped) | duplicates dropped (exact + same content) | masked context turns (unique rows) | change vs R2_stage1 |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|\n' + '\n'.join(rows) +
         f"\n\nTotals: {tot['uniq']:,} unique train rows → {r['train']['rows']:,} effective rows, {r['train']['tokens']/1e6:.1f}M rendered tokens, {g1['supervised_tokens_effective']/1e6:.1f}M supervised tokens ({g1['supervised_tokens_effective']/r['train']['tokens']:.0%}); dev {r['dev']['rows']:,} rows ({r['dev']['tokens']/1e6:.2f}M tokens) incl. the 69 personality holdout rows; train∩dev = {g1['train_dev_intersection']} by id and {g1.get('train_dev_content_intersection', 'n/a')} by content; rows without a supervised count: {g1['rows_without_supervised_count']}; post-assembly identity scan hits (exempt blocks: personality, convskills, correcting): {r.get('post_scan_identity_hits')}; contamination drops {tot['contam']:,} rows; duplicates dropped {tot['dup'] + tot['cdup']:,} ({tot['dup']:,} exact same-id, {tot['cdup']:,} same content under different ids); masked context turns {tot['masked']:,} (unique rows). train.jsonl sha256 {r['train']['sha256']}, dev.jsonl sha256 {r['dev']['sha256']}. Projected training cost at the measured stage-1 rate (32.5M tokens per node-hour): **{nh:.1f} node-hours**; the evaluation battery about 4.3 on top.\n<!-- /receipt-table -->")
for p in (HERE / f'RECIPE_{arm}_20260911.md', HERE / 'PIPELINE_DESCRIPTION_20260911.md'):
    s = open(p).read()
    if '<!-- receipt-table -->' in s: s = re.sub(r'<!-- receipt-table -->.*?<!-- /receipt-table -->', lambda m: table, s, flags=re.S)
    else:
        i = s.index('| block | unique train rows'); j = s.index('node-hours**; the evaluation battery about 4.3 on top.', i) + len('node-hours**; the evaluation battery about 4.3 on top.'); s = s[:i] + table + s[j:]
    open(p, 'w').write(s); print('filled', p.name)
