#!/usr/bin/env python3
"""Reader for the math pilot rows: M1 translated problems with the Greek solve vs the reference, M2 native problems with both solves, M3 arm B attempts, M5 held-out.
Usage: python3 rows_page.py <pilot_root> <m3_summary_dir> <out.html>"""
import html, json, os, sys
P, M3D, OUT = sys.argv[1:4]
def jl(p): return [json.loads(l) for l in open(p)] if os.path.exists(p) else []
rows = []
for r in jl(f'{P}/M1/results.jsonl'):
    rows.append(dict(pilot='M1 · translated', src=r['src'], grade=r.get('level', ''), topic=r.get('subject', 'gsm8k'), surface='', ok=r['correct'], q_en=r['problem_en'], q=r['problem_el'], changes=r.get('changes', ''), a1=r['solution_el'], f1=r['final_used'], ref=r['ref'], a2='', f2='', id=r['id']))
for r in jl(f'{P}/M2/results.jsonl'):
    rows.append(dict(pilot='M2 · native', src='native', grade=r['grade'], topic=r['topic'], surface=r['surface'], ok=r['agree'], q_en='', q=r['problem_el'], changes=r['context'], a1=r['solution_el'], f1=r['final_answer'], ref='', a2=r['solution2'], f2=r['final2'], id=r['id']))
for r in jl(f'{P}/M5_heldout/results.jsonl'):
    rows.append(dict(pilot='M5 · held-out', src='native', grade=r['grade'], topic=r['topic'], surface=r['surface'], ok=r['agree'], q_en='', q=r['problem_el'], changes=r['context'], a1=r['solution_el'], f1=r['final_answer'], ref='', a2=r['solution2'], f2=r['final2'], id=r['id']))
m3 = {r['id']: r for r in jl(f'{M3D}/armB.jsonl')}
for r in rows:
    if r['id'] in m3:
        s = m3[r['id']]['samples']; r['b_greedy'] = s[0]['solution']; r['b_ok'] = s[0]['correct']; r['b_final'] = s[0]['final']; r['b_pass_k'] = any(x['correct'] for x in s)
    else: r['b_greedy'] = ''; r['b_ok'] = None; r['b_final'] = ''; r['b_pass_k'] = None
pilots = sorted({r['pilot'] for r in rows}); grades = sorted({r['grade'] for r in rows if r['grade']}); topics = sorted({r['topic'] for r in rows})
opts = lambda xs: ''.join(f'<option value="{html.escape(x)}">{html.escape(x)}</option>' for x in xs)
n_ok = sum(1 for r in rows if r['ok'])
page = f'''<title>Greek Math Pilot Rows</title>
<style>
:root{{--bg:#f5f6f2;--ink:#1a1d1a;--muted:#646a63;--rule:#d5d9d0;--accent:#2b5d8a;--good:#2f7a3d;--bad:#b23a2a;--card:#fdfdfb;--q:#eaeeea;--hl:#fff1b8}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#14171a;--ink:#e6e9e4;--muted:#9aa19a;--rule:#343a3a;--accent:#8ab8e0;--good:#8fcf9a;--bad:#e58a70;--card:#1b1f22;--q:#22282b;--hl:#4a4020}}}}
:root[data-theme="dark"]{{--bg:#14171a;--ink:#e6e9e4;--muted:#9aa19a;--rule:#343a3a;--accent:#8ab8e0;--good:#8fcf9a;--bad:#e58a70;--card:#1b1f22;--q:#22282b;--hl:#4a4020}}
body{{background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;margin:0}} main{{max-width:1180px;margin:0 auto;padding:20px 16px 60px}} h1{{font-size:22px;margin:0 0 4px}} .sub{{color:var(--muted);margin:0 0 14px}}
.bar{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;position:sticky;top:0;background:var(--bg);padding:8px 0;border-bottom:1px solid var(--rule);z-index:2}} select,input{{font:13px inherit;padding:4px 6px;background:var(--card);color:var(--ink);border:1px solid var(--rule);border-radius:4px}} input{{min-width:200px}} .count{{color:var(--muted);margin-left:auto;font-variant-numeric:tabular-nums}}
.row{{background:var(--card);border:1px solid var(--rule);border-radius:6px;margin:10px 0;padding:10px 12px}} .meta{{display:flex;flex-wrap:wrap;gap:6px 12px;font-size:12px;color:var(--muted);margin-bottom:6px}} .meta b{{color:var(--ink);font-weight:600}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:12px}} @media(max-width:760px){{.cols{{grid-template-columns:1fr}}}} .box{{white-space:pre-wrap;word-break:break-word;padding:8px 10px;border-radius:4px;font-size:13.5px;border:1px solid var(--rule)}} .box.q{{background:var(--q);border:none}}
.lbl{{font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin:6px 0 3px}} .tag{{display:inline-block;padding:0 6px;border-radius:10px;border:1px solid var(--rule);font-size:11px}} .tag.pass{{border-color:var(--good);color:var(--good)}} .tag.fail{{border-color:var(--bad);color:var(--bad)}} .ans{{font-family:ui-monospace,Menlo,monospace;font-size:12.5px}} mark{{background:var(--hl);color:inherit}} button{{font:13px inherit;padding:6px 14px;border:1px solid var(--rule);background:var(--card);color:var(--ink);border-radius:4px;cursor:pointer}}
</style><main>
<h1>Greek math pilot, every problem</h1>
<p class="sub">{len(rows)} problems: translated GSM8K/MATH with Sol's Greek solve against the reference (M1), native problems with Sol's and Luna's solves (M2, M5 held-out), and arm B's greedy attempt where it ran (M3) · {n_ok} verified · 9 September 2026</p>
<div class="bar"><select id="fp"><option value="">all pilots</option>{opts(pilots)}</select><select id="fg"><option value="">all grades/levels</option>{opts(grades)}</select><select id="ft"><option value="">all topics</option>{opts(topics)}</select>
<select id="fo"><option value="">verified and not</option><option value="1">verified</option><option value="0">not verified</option></select><select id="fb"><option value="">arm B: any</option><option value="1">arm B correct</option><option value="0">arm B wrong</option><option value="k">arm B wrong greedy, right in samples</option></select><input id="fq" placeholder="search"><span class="count" id="cnt"></span></div>
<div id="list"></div><p style="text-align:center"><button id="more">show 100 more</button></p></main>
<script id="rows" type="application/json">{json.dumps(rows, ensure_ascii=False).replace('</', '<\\/')}</script>
<script>
const R = JSON.parse(document.getElementById('rows').textContent); const $ = id => document.getElementById(id); let shown = 0, cur = R;
const esc = s => (s || '').replace(/[&<>]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c]));
function card(r) {{
  const tag = r.ok ? '<span class="tag pass">verified</span>' : '<span class="tag fail">not verified</span>';
  const btag = r.b_ok === null ? '' : (r.b_ok ? '<span class="tag pass">arm B greedy correct</span>' : (r.b_pass_k ? '<span class="tag">arm B wrong greedy, right in a sample</span>' : '<span class="tag fail">arm B wrong</span>'));
  const left = `<div class="lbl">problem (Greek)</div><div class="box q">${{esc(r.q)}}</div>` + (r.q_en ? `<div class="lbl">original</div><div class="box q">${{esc(r.q_en)}}</div><div class="lbl">localisation notes</div><div class="box q">${{esc(r.changes)}}</div>` : (r.changes ? `<div class="lbl">context</div><div class="box q">${{esc(r.changes)}}</div>` : ''));
  const right = `<div class="lbl">Sol solution · final <span class="ans">${{esc(r.f1)}}</span>${{r.ref ? ' · reference <span class="ans">' + esc(r.ref) + '</span>' : ''}}</div><div class="box">${{esc(r.a1)}}</div>` + (r.a2 ? `<div class="lbl">Luna solution · final <span class="ans">${{esc(r.f2)}}</span></div><div class="box">${{esc(r.a2)}}</div>` : '') + (r.b_greedy ? `<div class="lbl">arm B greedy · final <span class="ans">${{esc(r.b_final)}}</span></div><div class="box">${{esc(r.b_greedy)}}</div>` : '');
  return `<div class="row"><div class="meta">${{tag}}${{btag}}<span>${{esc(r.pilot)}}</span><span>${{esc(r.src)}}</span><span><b>${{esc(r.grade)}}</b></span><span>${{esc(r.topic)}}</span><span>${{esc(r.surface)}}</span><span>${{r.id}}</span></div><div class="cols"><div>${{left}}</div><div>${{right}}</div></div></div>`;
}}
function apply() {{ const p = $('fp').value, g = $('fg').value, t = $('ft').value, o = $('fo').value, b = $('fb').value, q = $('fq').value.trim().toLowerCase();
  cur = R.filter(r => (!p || r.pilot === p) && (!g || r.grade === g) && (!t || r.topic === t) && (o === '' || (o === '1') === !!r.ok) && (b === '' || (b === '1' ? r.b_ok === true : b === '0' ? r.b_ok === false : (r.b_ok === false && r.b_pass_k))) && (!q || (r.q + ' ' + r.a1 + ' ' + r.a2 + ' ' + r.b_greedy).toLowerCase().includes(q)));
  shown = 0; $('list').innerHTML = ''; more(); }}
function more() {{ const next = cur.slice(shown, shown + 100); $('list').insertAdjacentHTML('beforeend', next.map(card).join('')); shown += next.length; $('cnt').textContent = `${{shown}} of ${{cur.length}}`; $('more').hidden = shown >= cur.length; }}
for (const id of ['fp','fg','ft','fo','fb']) $(id).addEventListener('change', apply); let tm; $('fq').addEventListener('input', () => {{ clearTimeout(tm); tm = setTimeout(apply, 250); }}); $('more').addEventListener('click', more); apply();
</script>'''
open(OUT, 'w').write(page); print(len(rows), 'rows →', OUT, f'{os.path.getsize(OUT)/1e6:.1f} MB')
