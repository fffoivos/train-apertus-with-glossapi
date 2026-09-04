#!/usr/bin/env python3
"""One table over results/<label>/: dev loss (from the run's dev_losses.json), ILSP, format gate, voice Delta,
interview rubric means. Usage: grid_table.py [--md out.md]"""
import json, glob, os, sys, statistics
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R = f'{HERE}/results'
RUNS = {'E1_lr1e-5': 'E1_lr1e-5_3ep_const', 'E1_lr5e-6': 'E1_lr5e-6_3ep_const'}
def load(p):
    try: return json.load(open(p))
    except Exception: return None
rows = []
for d in sorted(glob.glob(f'{R}/*')):
    L = os.path.basename(d); row = {'label': L}
    for prefix, run in RUNS.items():
        if L.startswith(prefix + '_ep'):
            ep = L.split('_ep')[-1]; dl = load(f'{R}/{run}/dev_losses.json') or {}
            row['dev_no_robots'] = (dl.get('no_robots') or {}).get(ep); row['dev_mean_el'] = statistics.mean([v[ep] for k, v in dl.items() if ep in v and k in ('no_robots','coconot','personas_if','smolcon','oasst','everyday','systemchats')]) if dl else None
    for f in glob.glob(f'{d}/ilsp/*/results*.json'):
        res = load(f)['results']; row['ifeval_strict'] = res.get('ifeval_greek', {}).get('prompt_level_strict_acc,none'); row['ifeval_inst'] = res.get('ifeval_greek', {}).get('inst_level_strict_acc,none')
        row['mgsm'] = (res.get('mgsm_greek') or res.get('mgsm_greek_4shot') or {}).get('exact_match,none')
    g = load(f'{d}/dev/format_gate.json')
    if g: row['gate_stop'] = g['metrics'].get('ended_on_stop'); row['gate_lang'] = g['metrics'].get('language_ok')
    v = load(f'{d}/dev/voice.json')
    if v: row['voice_delta'] = (v.get('delta') or {}).get('generated_vs_no_robots'); row['gen_words_el'] = (v.get('word_counts') or {}).get('generated_el')
    sc = load(f'{d}/interviews/scores.json')
    if sc:
        av = sc.get('averages') or {}
        for k, x in av.items():
            if isinstance(x, dict): x = x.get('mean', x.get('score'))
            if isinstance(x, (int, float)): row[f'int_{k[:12]}'] = round(x, 2)
        vals = [v for v in row if v.startswith('int_')]
        if vals: row['int_mean'] = round(statistics.mean(row[v] for v in vals), 2)
        row['int_n'] = sc.get('count')
    if len(row) > 1: rows.append(row)
cols = ['label', 'dev_no_robots', 'dev_mean_el', 'ifeval_strict', 'ifeval_inst', 'mgsm', 'gate_stop', 'gate_lang', 'voice_delta', 'gen_words_el'] + sorted({k for r in rows for k in r if k.startswith('int_')})
fmt = lambda x: '' if x is None else (f'{x:.3f}' if isinstance(x, float) else str(x))
lines = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)] + ['| ' + ' | '.join(fmt(r.get(c)) for c in cols) + ' |' for r in rows]
out = '\n'.join(lines); print(out)
if '--md' in sys.argv: open(sys.argv[sys.argv.index('--md') + 1], 'w').write(out + '\n')
