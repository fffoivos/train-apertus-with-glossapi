#!/usr/bin/env python3
"""Compose the R0/R1 picky-user benchmark into a markdown section and an HTML page.
Usage: python3 report_r0.py <r0_dir> <out.md> <out.html>   (r0_dir holds <model>_summary.json, <model>.jsonl, r1_rp*/armB_summary.json)"""
import collections, glob, html, json, os, sys
D, OUT_MD, OUT_HTML = sys.argv[1:4]
ORDER = ['armB', 'stage1', 'apertus', 'krikri']; LABEL = {'armB': 'arm B (round two)', 'stage1': 'stage 1 (no personality pass)', 'apertus': 'Apertus-8B-Instruct-2509', 'krikri': 'Llama-Krikri-8B-Instruct'}
S = {m: json.load(open(f'{D}/{m}_summary.json')) for m in ORDER if os.path.exists(f'{D}/{m}_summary.json')}
R1 = {os.path.basename(os.path.dirname(p)): json.load(open(p)) for p in glob.glob(f'{D}/r1_rp*/armB_summary.json')}
pct = lambda x: '–' if x is None else f'{100*x:.1f}%'
METRICS = [('loop_rate', 'loop rate (sentence ×3 in one answer)'), ('tail_copy_rate', 'tail-copy rate (last sentence = previous answer\'s)'), ('dead_dialogues', 'dead dialogues (3 broken turns in a row)'), ('stale_rate', 'stale rate after a switch or correction'),
           ('stop_honour_rate', 'stop instructions honoured'), ('lang_slip_rate', 'language slips'), ('coherent_rate', 'coherent turns (judge)'), ('honour_rate', 'requests honoured (judge)'), ('premise_score', 'premise score 0–2 (judge)')]
def tone(s): t = s.get('tone', {}); n = sum(t.values()) or 1; return {k: round(v / n, 3) for k, v in t.items()}
# per-move breakdown for arm B vs krikri from the dialogues
def per_move(m):
    rows = [json.loads(l) for l in open(f'{D}/{m}.jsonl')] if os.path.exists(f'{D}/{m}.jsonl') else []; T = [t for r in rows for t in r['turns']]; out = {}
    for mv in sorted({t['move'] for t in T}):
        ts = [t for t in T if t['move'] == mv]; out[mv] = dict(n=len(ts), key_absent=round(sum(not t['key_present'] for t in ts) / max(1, len(ts)), 2), broken=round(sum(t['loop'] or t['tail_copy'] for t in ts) / len(ts), 3), coherent=round(sum(t.get('j_coherent', False) for t in ts) / len(ts), 3), tone_fine=round(sum(t.get('j_tone') == 'fine' for t in ts) / len(ts), 3))
    return out
PM = {m: per_move(m) for m in S}
md = [f'## R0 · picky-user benchmark baseline ({S[ORDER[0]]["dialogues"] if ORDER[0] in S else "?"} simulated dialogues per model, Sol user with the owner\'s chats as exemplars, sampling temperature 0.8, no repetition penalty)\n', '| metric | ' + ' | '.join(LABEL[m] for m in S) + ' |', '|---|' + '---:|' * len(S)]
for k, lab in METRICS: md.append(f'| {lab} | ' + ' | '.join((f"{S[m][k]:.2f}" if k == 'premise_score' and S[m].get(k) is not None else pct(S[m].get(k))) for m in S) + ' |')
md.append('| tone: fine / curt / snarky / servile | ' + ' | '.join(' / '.join(pct(tone(S[m]).get(t, 0)) for t in ('fine', 'curt', 'snarky', 'servile')) for m in S) + ' |')
md.append('| mean answer words | ' + ' | '.join(str(S[m]['mean_words']) for m in S) + ' |')
if R1:
    md.append('\n### R1 · decoding: arm B with a repetition penalty\n\n| arm | loop | tail-copy | dead | stale | coherent | tone fine |\n|---|---:|---:|---:|---:|---:|---:|')
    md.append(f"| penalty 1.0 (R0) | {pct(S['armB']['loop_rate'])} | {pct(S['armB']['tail_copy_rate'])} | {pct(S['armB']['dead_dialogues'])} | {pct(S['armB']['stale_rate'])} | {pct(S['armB']['coherent_rate'])} | {pct(tone(S['armB']).get('fine', 0))} |" if 'armB' in S else '')
    for k, s in sorted(R1.items()): md.append(f"| {k.replace('r1_rp', 'penalty ')} | {pct(s['loop_rate'])} | {pct(s['tail_copy_rate'])} | {pct(s['dead_dialogues'])} | {pct(s['stale_rate'])} | {pct(s['coherent_rate'])} | {pct(tone(s).get('fine', 0))} |")
if 'armB' in PM:
    md.append('\n### Per move (share of turns broken by regex: loop, tail copy, or the new request not addressed; and judged coherent)\n\n| move | ' + ' | '.join(f'{LABEL[m]} broken / coherent' for m in S) + ' |\n|---|' + '---:|' * len(S))
    for mv in PM['armB']: md.append(f'| {mv} | ' + ' | '.join(f"{pct(PM[m].get(mv, {}).get('broken'))} / {pct(PM[m].get(mv, {}).get('coherent'))}" for m in S) + ' |')
open(OUT_MD, 'w').write('\n'.join(md) + '\n')
bar = lambda v, good=False: f'<span class="track"><span class="fill{" good" if good else ""}" style="width:{100*(v or 0):.1f}%"></span></span><span class="val">{pct(v)}</span>'
page = f'''<title>Picky-User Benchmark R0</title>
<style>
:root{{--bg:#f6f4ef;--ink:#1c1915;--muted:#6a6358;--rule:#d8d1c4;--accent:#8a3b2b;--good:#2f6b3a;--card:#fffdf8}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#16140f;--ink:#ebe5d9;--muted:#a49b8c;--rule:#3a352b;--accent:#e08a72;--good:#8fcf9a;--card:#1e1b15}}}}
:root[data-theme="dark"]{{--bg:#16140f;--ink:#ebe5d9;--muted:#a49b8c;--rule:#3a352b;--accent:#e08a72;--good:#8fcf9a;--card:#1e1b15}}
body{{background:var(--bg);color:var(--ink);font:15px/1.5 Georgia,serif;margin:0}} main{{max-width:980px;margin:0 auto;padding:28px 20px 60px}} h1{{font-size:28px;margin:0 0 4px}} h2{{font-size:19px;margin:30px 0 8px;border-top:1px solid var(--rule);padding-top:14px}} .sub{{color:var(--muted)}}
table{{border-collapse:collapse;width:100%;font-size:14px}} td,th{{border-bottom:1px solid var(--rule);padding:6px 8px;text-align:left;vertical-align:middle}} td.n,th.n{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
.track{{display:inline-block;width:90px;height:9px;background:var(--rule);vertical-align:middle;margin-right:6px;position:relative}} .fill{{position:absolute;left:0;top:0;bottom:0;background:var(--accent)}} .fill.good{{background:var(--good)}} .val{{font-variant-numeric:tabular-nums}} .wrap{{overflow-x:auto}} p.note{{color:var(--muted);font-size:13px}}
</style><main>
<h1>Picky-user benchmark, baseline</h1>
<p class="sub">Simulated reactive users (Sol, prompted with the owner's chats) against four models; regex metrics per turn, judged rubrics per dialogue · {S[ORDER[0]]["dialogues"] if ORDER[0] in S else "?"} dialogues per model · 9 September 2026</p>
<h2>Failure rates (lower is better) and judged quality (higher is better)</h2>
<div class="wrap"><table><tr><th>metric</th>{''.join(f'<th class="n">{html.escape(LABEL[m])}</th>' for m in S)}</tr>
{''.join(f'<tr><td>{html.escape(lab)}</td>' + ''.join(f'<td class="n">{(f"{S[m][k]:.2f}" if k == "premise_score" else bar(S[m].get(k), good=k in ("stop_honour_rate", "coherent_rate", "honour_rate")))}</td>' for m in S) + '</tr>' for k, lab in METRICS)}
<tr><td>tone fine</td>{''.join(f'<td class="n">{bar(tone(S[m]).get("fine", 0), good=True)}</td>' for m in S)}</tr></table></div>
{('<h2>Decoding arm (R1): arm B with repetition penalty</h2><div class="wrap"><table><tr><th>arm</th><th class="n">loop</th><th class="n">tail-copy</th><th class="n">dead dialogues</th><th class="n">coherent</th><th class="n">tone fine</th></tr>' + (f"<tr><td>penalty 1.0</td><td class=n>{pct(S['armB']['loop_rate'])}</td><td class=n>{pct(S['armB']['tail_copy_rate'])}</td><td class=n>{pct(S['armB']['dead_dialogues'])}</td><td class=n>{pct(S['armB']['coherent_rate'])}</td><td class=n>{pct(tone(S['armB']).get('fine',0))}</td></tr>" if 'armB' in S else '') + ''.join(f"<tr><td>{k.replace('r1_rp','penalty ')}</td><td class=n>{pct(s['loop_rate'])}</td><td class=n>{pct(s['tail_copy_rate'])}</td><td class=n>{pct(s['dead_dialogues'])}</td><td class=n>{pct(s['coherent_rate'])}</td><td class=n>{pct(tone(s).get('fine',0))}</td></tr>" for k, s in sorted(R1.items())) + '</table></div>') if R1 else ''}
<h2>Per user move: share of turns broken (regex) / judged coherent</h2>
<div class="wrap"><table><tr><th>move</th>{''.join(f'<th class="n">{html.escape(LABEL[m])}</th>' for m in S)}</tr>
{''.join(f'<tr><td>{mv}</td>' + ''.join(f'<td class="n">{pct(PM[m].get(mv, {}).get("broken"))} / {pct(PM[m].get(mv, {}).get("coherent"))}</td>' for m in S) + '</tr>' for mv in (PM.get('armB') or {}))}</table></div>
<p class="note">Broken = a sentence repeated three times in the answer, or the last sentence copied from the previous answer, or the user's new request not addressed. Coherent = the judge found the answer fits the last message. Full dialogues in the results folder; program in docs/ROBUSTNESS_PROGRAM_20260909.md.</p>
</main>'''
open(OUT_HTML, 'w').write(page); print('wrote', OUT_MD, OUT_HTML, 'models', list(S), 'R1', list(R1))
