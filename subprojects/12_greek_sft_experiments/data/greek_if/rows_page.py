#!/usr/bin/env python3
"""Reader for the Greek IF pilot rows: every Sol answer with its prompt, constraints and checker verdicts, filterable in the browser.
Usage: python3 rows_page.py <pilot_dir> <out.html>"""
import collections, html, json, os, sys
P, OUT = sys.argv[1:3]
DESIGNS = {'E1': 'E1 · one constraint per family', 'E2': 'E2 · levels 1–5', 'E3': 'E3 · domains', 'E4': 'E4 · question forms', 'E5': 'E5 · Greek-only families', 'E6': 'E6 · phrasing variants (first run, discarded design)',
           'mix': 'E0 · template requests', 'mixa': 'E0 · authored requests', 'E6b': 'E6b · phrasing variants (fixed design)', 'E4x': 'E4x · translate/summarise/rewrite with form-only constraints', 'E7': 'E7 · judged families'}
def jl(fn): return [json.loads(l) for l in open(fn)] if os.path.exists(fn) else []
prompts = {}
for fn in sorted(os.listdir(P)):
    if fn.startswith('prompts_') and fn.endswith('.jsonl'):
        for r in jl(os.path.join(P, fn)): prompts[r['id']] = r
answers = {}
for fn in os.listdir(P):
    if fn.startswith('answers_') and fn.endswith('.jsonl'):
        for r in jl(os.path.join(P, fn)): answers[r['id']] = r['answer']
scores = {}
for fn in os.listdir(P):
    if fn.startswith('scores_') and fn.endswith('.jsonl'):
        for r in jl(os.path.join(P, fn)): scores[r['id']] = r
judges = collections.defaultdict(dict)
for fn, who in (('judgements_E7.jsonl', 'Opus'), ('judgements_E7_sol.jsonl', 'Sol')):
    for r in jl(os.path.join(P, fn)): judges[r['id']][who] = {v['family']: (bool(v['pass']), v['why']) for v in r['verdicts']}
rows = []
for rid, p in prompts.items():
    if rid not in answers: continue
    sc = scores.get(rid); res = {x['family']: x['ok'] for x in sc['results']} if sc else {}
    cons = []
    for c in p['constraints']:
        j = {who: judges[rid][who].get(c['family']) for who in judges.get(rid, {})}
        cons.append(dict(f=c['family'], t=c['text'], ok=res.get(c['family']), j={w: v for w, v in j.items() if v}))
    chk = [c['ok'] for c in cons if c['ok'] is not None]
    rows.append(dict(id=rid, d=DESIGNS.get(rid.split('_')[0], rid.split('_')[0]), L=p['level'], dom=p['domain'], sub=p['subtopic'], form=p['form'], per=p['persona'], ps=p['persona_style'], au=bool(p.get('authored')),
                     q=p['prompt'], a=answers[rid], c=cons, ok=(all(chk) if chk else None), nw=len(answers[rid].split())))
rows.sort(key=lambda r: (r['d'], r['L'], r['id']))
fams = sorted({c['f'] for r in rows for c in r['c']}); designs = sorted({r['d'] for r in rows}); forms = sorted({r['form'] for r in rows}); doms = sorted({r['dom'] for r in rows}); styles = sorted({r['ps'] for r in rows})
n_pass = sum(1 for r in rows if r['ok']); n_fail = sum(1 for r in rows if r['ok'] is False)
opts = lambda xs: ''.join(f'<option value="{html.escape(x)}">{html.escape(x)}</option>' for x in xs)
page = f'''<title>Greek IF Pilot Rows</title>
<style>
:root{{--bg:#f7f5f0;--ink:#1d1a16;--muted:#6b645a;--rule:#d9d2c5;--accent:#1f5f8b;--good:#2f7a3d;--bad:#b8412a;--card:#fffdf9;--q:#eef1ec;--hl:#fff3c4}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#17150f;--ink:#ece6da;--muted:#a49b8c;--rule:#3b362c;--accent:#7fb3d9;--good:#8fcf9a;--bad:#e58a70;--card:#1f1c15;--q:#24211a;--hl:#4a4020}}}}
:root[data-theme="dark"]{{--bg:#17150f;--ink:#ece6da;--muted:#a49b8c;--rule:#3b362c;--accent:#7fb3d9;--good:#8fcf9a;--bad:#e58a70;--card:#1f1c15;--q:#24211a;--hl:#4a4020}}
body{{background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;margin:0}}
main{{max-width:1180px;margin:0 auto;padding:20px 16px 60px}} h1{{font-size:22px;margin:0 0 4px}} .sub{{color:var(--muted);margin:0 0 14px}}
.bar{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;position:sticky;top:0;background:var(--bg);padding:8px 0;border-bottom:1px solid var(--rule);z-index:2}}
select,input{{font:13px inherit;padding:4px 6px;background:var(--card);color:var(--ink);border:1px solid var(--rule);border-radius:4px}} input{{min-width:220px}} .count{{color:var(--muted);margin-left:auto;font-variant-numeric:tabular-nums}}
.row{{background:var(--card);border:1px solid var(--rule);border-radius:6px;margin:10px 0;padding:10px 12px}} .meta{{display:flex;flex-wrap:wrap;gap:6px 12px;font-size:12px;color:var(--muted);margin-bottom:6px}} .meta b{{color:var(--ink);font-weight:600}}
.pair{{display:grid;grid-template-columns:1fr 1fr;gap:12px}} @media(max-width:760px){{.pair{{grid-template-columns:1fr}}}}
.q,.a{{white-space:pre-wrap;word-break:break-word;padding:8px 10px;border-radius:4px;font-size:13.5px}} .q{{background:var(--q)}} .a{{border:1px solid var(--rule)}}
.lbl{{font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin-bottom:3px}}
.cons{{margin-top:8px;display:flex;flex-direction:column;gap:3px;font-size:12.5px}} .con{{display:flex;gap:8px;align-items:baseline}} .ok{{color:var(--good);font-weight:700;min-width:1.2em}} .bad{{color:var(--bad);font-weight:700;min-width:1.2em}} .na{{color:var(--muted);min-width:1.2em}}
.fam{{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:var(--accent)}} .why{{color:var(--muted);font-style:italic}}
.tag{{display:inline-block;padding:0 6px;border-radius:10px;border:1px solid var(--rule);font-size:11px}} .tag.pass{{border-color:var(--good);color:var(--good)}} .tag.fail{{border-color:var(--bad);color:var(--bad)}}
mark{{background:var(--hl);color:inherit}} button{{font:13px inherit;padding:6px 14px;border:1px solid var(--rule);background:var(--card);color:var(--ink);border-radius:4px;cursor:pointer}}
</style>
<main>
<h1>Greek instruction-following pilot, every row</h1>
<p class="sub">{len(rows)} Sol answers (gpt-5.6-sol, medium) with their prompt, constraints and checker verdicts · {n_pass} pass every checkable constraint, {n_fail} fail at least one, {len(rows)-n_pass-n_fail} judged only · 8 September 2026</p>
<div class="bar">
<select id="fd"><option value="">all designs</option>{opts(designs)}</select>
<select id="fl"><option value="">all levels</option>{''.join(f'<option value="{i}">level {i}</option>' for i in range(1,6))}</select>
<select id="ff"><option value="">all families</option>{opts(fams)}</select>
<select id="fp"><option value="">pass and fail</option><option value="1">pass</option><option value="0">fail</option></select>
<select id="fo"><option value="">all forms</option>{opts(forms)}</select>
<select id="fs"><option value="">all writer surfaces</option>{opts(styles)}</select>
<select id="fm"><option value="">all domains</option>{opts(doms)}</select>
<input id="fq" placeholder="search prompt or answer">
<span class="count" id="cnt"></span>
</div>
<div id="list"></div>
<p style="text-align:center"><button id="more">show 200 more</button></p>
</main>
<script id="rows" type="application/json">{json.dumps(rows, ensure_ascii=False).replace('</', '<\\/')}</script>
<script>
const R = JSON.parse(document.getElementById('rows').textContent); const $ = id => document.getElementById(id); let shown = 0, cur = R;
const esc = s => s.replace(/[&<>]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c]));
function hl(s, q) {{ if (!q) return esc(s); const i = s.toLowerCase().indexOf(q.toLowerCase()); if (i < 0) return esc(s); return esc(s.slice(0,i)) + '<mark>' + esc(s.slice(i, i+q.length)) + '</mark>' + hl(s.slice(i+q.length), q); }}
function card(r, q) {{
  const cons = r.c.map(c => {{ const m = c.ok === true ? '<span class="ok">✓</span>' : c.ok === false ? '<span class="bad">✗</span>' : '<span class="na">·</span>';
    const j = Object.entries(c.j || {{}}).map(([w, v]) => `<div class="con"><span class="${{v[0] ? 'ok' : 'bad'}}">${{v[0] ? '✓' : '✗'}}</span><span>${{w}} judge: <span class="why">${{esc(v[1])}}</span></span></div>`).join('');
    return `<div class="con">${{m}}<span class="fam">${{c.f}}</span><span>${{esc(c.t)}}</span></div>${{j}}`; }}).join('');
  const tag = r.ok === true ? '<span class="tag pass">pass</span>' : r.ok === false ? '<span class="tag fail">fail</span>' : '<span class="tag">judged</span>';
  return `<div class="row"><div class="meta">${{tag}}<span>${{esc(r.d)}}</span><span>level <b>${{r.L}}</b></span><span>${{esc(r.dom)}} › ${{esc(r.sub)}}</span><span>form <b>${{r.form}}</b></span><span>writer: ${{esc(r.per)}} (${{r.ps}}${{r.au ? ', authored request' : ''}})</span><span>${{r.nw}} words</span><span>${{r.id}}</span></div>
  <div class="pair"><div><div class="lbl">user</div><div class="q">${{hl(r.q, q)}}</div></div><div><div class="lbl">assistant (Sol)</div><div class="a">${{hl(r.a, q)}}</div></div></div><div class="cons">${{cons}}</div></div>`;
}}
function apply() {{
  const d = $('fd').value, l = $('fl').value, f = $('ff').value, p = $('fp').value, o = $('fo').value, s = $('fs').value, m = $('fm').value, q = $('fq').value.trim();
  cur = R.filter(r => (!d || r.d === d) && (!l || String(r.L) === l) && (!f || r.c.some(c => c.f === f && (p === '' || (p === '1') === (c.ok === true)))) && (f || p === '' || (p === '1') === (r.ok === true)) && (!o || r.form === o) && (!s || r.ps === s) && (!m || r.dom === m) && (!q || (r.q + ' ' + r.a).toLowerCase().includes(q.toLowerCase())));
  shown = 0; $('list').innerHTML = ''; more();
}}
function more() {{ const q = $('fq').value.trim(); const next = cur.slice(shown, shown + 200); $('list').insertAdjacentHTML('beforeend', next.map(r => card(r, q)).join('')); shown += next.length; $('cnt').textContent = `${{shown}} of ${{cur.length}} rows`; $('more').hidden = shown >= cur.length; }}
for (const id of ['fd','fl','ff','fp','fo','fs','fm']) $(id).addEventListener('change', apply); let t; $('fq').addEventListener('input', () => {{ clearTimeout(t); t = setTimeout(apply, 250); }}); $('more').addEventListener('click', more); apply();
</script>'''
open(OUT, 'w').write(page); print(len(rows), 'rows →', OUT, f'{os.path.getsize(OUT)/1e6:.1f} MB')
