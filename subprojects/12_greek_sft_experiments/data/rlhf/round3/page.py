#!/usr/bin/env python3
"""Round 3 review page: every new prompt with its seed, labels, judged replies (general judge v2.4 and/or maths judge), the pair chosen by the
pair rule, and a vote store (db collection votes_r3). Data ship as script chunks next to the page (multi-file artifact).
Usage: python3 data/rlhf/round3/page.py <out_dir> [--dir data/rlhf/round3] [--title ...]"""
import argparse, collections, json, pathlib, math
HERE = pathlib.Path(__file__).resolve().parent
def J(p): return [json.loads(l) for l in open(p) if l.strip()] if pathlib.Path(p).exists() else []
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--dir', default=str(HERE)); ap.add_argument('--title', default='Round 3 Votes'); ap.add_argument('--chunk', type=int, default=40); a = ap.parse_args()
d = pathlib.Path(a.dir); out = pathlib.Path(a.out); (out / 'data').mkdir(parents=True, exist_ok=True)
rows = J(d / 'round3_all.jsonl'); pairs = {x['id']: x for x in J(d / 'round3_pairs.jsonl')}; summary = json.load(open(d / 'round3_summary.json'))
samples = collections.defaultdict(dict)
for s in J(d / 'round3_samples.jsonl'):
    if s.get('k', -1) >= 0: samples[s['id']][s['k']] = s['text']
gen, mat = collections.defaultdict(dict), collections.defaultdict(dict); rank = collections.defaultdict(dict)
for st in (1, 2, 3):
    for r in J(d / f'judged_general_s{st}.jsonl'):
        if 'ranking_k' not in r: continue
        for pos, k in enumerate(r['ranking_k']): rank[r['id']][k] = (st, r['batch'], pos)
        for k, v in r['by_k'].items(): gen[r['id']][int(k)] = dict(verdict=v.get('verdict'), issues=v.get('issues', []), note=v.get('note', ''), margin=(r.get('verdict') or {}).get('best_vs_worst'))
    for r in J(d / f'judged_maths_s{st}.jsonl'):
        if 'ranking_k' not in r: continue
        for pos, k in enumerate(r['ranking_k']): rank[r['id']].setdefault(k, (st, r['batch'], pos))
        for k, v in r['by_k'].items(): mat[r['id']][int(k)] = dict(v, margin=r.get('best_vs_worst'))
refs = {r['id']: r for r in J(d / 'maths_references.jsonl')}
VORDER = {'reinforce': 0, 'neutral': 1, 'discourage': 2}
items = []
for r in rows:
    pid = r['id']; ks = sorted(set(gen[pid]) | set(mat[pid]))
    def key(k):
        g, m = gen[pid].get(k, {}), mat[pid].get(k, {})
        return (VORDER.get(g.get('verdict') or m.get('verdict'), 3), 0 if m.get('eligible_positive') else 1, rank[pid].get(k, (9, 9, 9)))
    replies = [dict(k=k, text=samples[pid].get(k, '(missing)'), g=gen[pid].get(k), m=mat[pid].get(k)) for k in sorted(ks, key=key)]
    ref = refs.get(pid); p = pairs.get(pid, {})
    v2 = next((b for st in (1, 2, 3) for b in J(d / f'judged_maths_s{st}.jsonl') if b.get('id') == pid and b.get('own_solution')), None)
    items.append(dict(id=pid, purpose=r['purpose'], subtype=r.get('subtype'), language=r['language'], labels={k: r.get(k) for k in ('difficulty', 'detail', 'register', 'attitude') if r.get(k)}, source=r.get('source'),
                      seed={k: r.get(k) for k in ('scenario', 'person', 'situation', 'topic', 'story') if r.get(k)}, messages=r['messages'], maths=r.get('maths_content'),
                      ref=(dict(status=v2.get('question_status'), result=v2.get('own_solution'), reason="the judge's own worked solution, written before it read the replies") if v2
                           else (dict(status=ref['status'], result=ref['comparison'].get('reference') or ref['solver_a']['result'], reason=ref['comparison'].get('reason')) if ref else None)),
                      sampled=len(samples[pid]), judged=len(ks), pair=p.get('pair'), status=p.get('status'), has_positive=p.get('has_positive'), replies=replies))
n_chunks = max(1, math.ceil(len(items) / a.chunk)); files = []
for i in range(n_chunks):
    name = f'data/chunk_{i:03d}.js'; files.append(name)
    (out / name).write_text('window.R3=window.R3||[];window.R3.push(...' + json.dumps(items[i * a.chunk:(i + 1) * a.chunk], ensure_ascii=False).replace('</', '<\\/') + ');\n')
PURPOSES = ['dialogue', 'everyday', 'instruction', 'factual', 'safety', 'math']; LANGS = ['el', 'en', 'fr', 'de', 'es', 'it', 'pt']
cells = summary['by_cell']
def cell(p, l, f): return cells.get(f'{p}/{l}', {}).get(f, 0)
rows_html = ''.join(f"<tr><th>{p}</th>" + ''.join(f"<td>{cell(p,l,'eligible_pairs')}<span class='of'>/{cell(p,l,'prompts')}</span></td>" if cell(p, l, 'prompts') else "<td class='empty'>·</td>" for l in LANGS) + f"<td class='tot'>{sum(cell(p,l,'eligible_pairs') for l in LANGS)}<span class='of'>/{sum(cell(p,l,'prompts') for l in LANGS)}</span></td></tr>" for p in PURPOSES if any(cell(p, l, 'prompts') for l in LANGS))
tot = f"<tr class='total'><th>all</th>" + ''.join(f"<td>{sum(cell(p,l,'eligible_pairs') for p in PURPOSES)}<span class='of'>/{sum(cell(p,l,'prompts') for p in PURPOSES)}</span></td>" for l in LANGS) + f"<td class='tot'>{summary['eligible_pairs']}<span class='of'>/{summary['prompts']}</span></td></tr>"
held = sum(v for k, v in summary['by_status'].items() if k.startswith('held'))
page = (HERE / 'page_template.html').read_text().replace('%%TITLE%%', a.title).replace('%%SCRIPTS%%', ''.join(f'<script src="{f}"></script>' for f in files)).replace('%%TABLE%%', rows_html + tot)
page = page.replace('%%N_PROMPTS%%', str(summary['prompts'])).replace('%%N_PAIRS%%', str(summary['eligible_pairs'])).replace('%%N_POS%%', str(summary['with_positive'])).replace('%%N_HELD%%', str(held))
(out / 'index.html').write_text(page); json.dump(files, open(out / 'files.json', 'w'))
print('wrote', out / 'index.html', len(items), 'prompts in', n_chunks, 'chunks;', sum(len(x['replies']) for x in items), 'replies')
