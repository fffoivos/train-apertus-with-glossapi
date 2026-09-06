#!/usr/bin/env python3
"""Metrics side by side for several runs, with mean and spread. Usage: python3 compare_runs.py <run_dir> [run_dir ...]"""
import json, sys, os, statistics
runs = [(os.path.basename(d.rstrip('/')), json.load(open(f'{d}/metrics.json'))) for d in sys.argv[1:] if os.path.exists(f'{d}/metrics.json')]
keys = ['questions', 'gate_keep_rate', 'duplicate_questions', 'rows', 'multi_turn', 'names_greece_rate', 'mannerism_rate', 'ai_boilerplate', 'exclamations_per_row', 'beyond_sheet_rows', 'answer_chars_median', 'checked', 'edit_rate', 'greekness', 'fact_doubts']
print('| metric | ' + ' | '.join(n for n, _ in runs) + ' | mean | spread |'); print('|---|' + '---|' * (len(runs) + 2))
for k in keys:
    vals = [m.get(k) for _, m in runs]; nums = [v for v in vals if isinstance(v, (int, float))]
    mean = f"{statistics.mean(nums):.3g}" if nums else '—'; spread = f"{max(nums)-min(nums):.3g}" if len(nums) > 1 else '—'
    print(f"| {k} | " + ' | '.join(str(v) if v is not None else '—' for v in vals) + f" | {mean} | {spread} |")
print('\nmedian answer chars by form:'); forms = sorted({f for _, m in runs for f in (m.get('answer_chars_median_by_form') or {})})
print('| form | ' + ' | '.join(n for n, _ in runs) + ' |'); print('|---|' + '---|' * len(runs))
for f in forms: print(f"| {f} | " + ' | '.join(str((m.get('answer_chars_median_by_form') or {}).get(f, '—')) for _, m in runs) + ' |')
