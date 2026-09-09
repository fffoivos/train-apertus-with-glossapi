#!/usr/bin/env python3
"""Reader for the picky-user benchmark dialogues: every turn with the user's move, the model's answer, the regex flags and the judge's verdicts.
Usage: python3 dialogues_page.py <r0_dir> <out.html>"""
import html, json, os, sys
D, OUT = sys.argv[1:3]
LABEL = {'armB': 'arm B (round two)', 'stage1': 'stage 1', 'apertus': 'Apertus-8B-Instruct', 'krikri': 'Krikri'}
dl = []
for m in ('armB', 'stage1', 'apertus', 'krikri'):
    p = f'{D}/{m}.jsonl'
    if not os.path.exists(p): continue
    for r in (json.loads(l) for l in open(p)):
        T = r['turns']; broken = sum(t['loop'] or t['tail_copy'] or (not t['key_present']) for t in T); dead = len(T) >= 3 and all(t['loop'] or t['tail_copy'] for t in T[-3:])
        dl.append(dict(id=r['id'], model=m, label=LABEL[m], surface=r['surface'], intent=r['intent'], n=len(T), broken=broken, dead=dead, moves=sorted({t['move'] for t in T}), tones=sorted({t.get('j_tone', '') for t in T} - {''}),
                       coherent=round(sum(t.get('j_coherent', False) for t in T) / max(1, len(T)), 2), turns=[dict(move=t['move'], u=t['user'], a=t['answer'], loop=t['loop'], tail=t['tail_copy'], key=t['key_present'], slip=t['lang_slip'], stop=t['stop_honoured'], tone=t.get('j_tone', ''), coh=t.get('j_coherent'), prem=t.get('j_premise', -1), hon=t.get('j_honours', -1), why=t.get('j_why', '')) for t in T]))
moves = sorted({mv for d in dl for mv in d['moves']}); opts = lambda xs: ''.join(f'<option value="{html.escape(x)}">{html.escape(x)}</option>' for x in xs)
page = f'''<title>Picky-User Dialogues</title>
<style>
:root{{--bg:#f6f4ef;--ink:#1c1915;--muted:#6a6358;--rule:#d8d1c4;--accent:#8a3b2b;--good:#2f6b3a;--bad:#b23a2a;--card:#fffdf8;--u:#efe9dc;--hl:#fff1b8}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#16140f;--ink:#ebe5d9;--muted:#a49b8c;--rule:#3a352b;--accent:#e08a72;--good:#8fcf9a;--bad:#e58a70;--card:#1e1b15;--u:#26221a;--hl:#4a4020}}}}
:root[data-theme="dark"]{{--bg:#16140f;--ink:#ebe5d9;--muted:#a49b8c;--rule:#3a352b;--accent:#e08a72;--good:#8fcf9a;--bad:#e58a70;--card:#1e1b15;--u:#26221a;--hl:#4a4020}}
body{{background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;margin:0}} main{{max-width:1080px;margin:0 auto;padding:20px 16px 60px}} h1{{font-size:22px;margin:0 0 4px}} .sub{{color:var(--muted);margin:0 0 14px}}
.bar{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;position:sticky;top:0;background:var(--bg);padding:8px 0;border-bottom:1px solid var(--rule);z-index:2}} select,input{{font:13px inherit;padding:4px 6px;background:var(--card);color:var(--ink);border:1px solid var(--rule);border-radius:4px}} input{{min-width:200px}} .count{{color:var(--muted);margin-left:auto;font-variant-numeric:tabular-nums}}
.dlg{{background:var(--card);border:1px solid var(--rule);border-radius:6px;margin:12px 0;padding:10px 12px}} .meta{{display:flex;flex-wrap:wrap;gap:6px 12px;font-size:12px;color:var(--muted);margin-bottom:8px}} .meta b{{color:var(--ink)}}
.turn{{display:grid;grid-template-columns:110px 1fr;gap:8px;padding:6px 0;border-top:1px solid var(--rule)}} .mv{{font-size:11px;color:var(--accent);font-family:ui-monospace,Menlo,monospace;padding-top:6px}} .u{{background:var(--u);padding:6px 9px;border-radius:4px;margin-bottom:4px;white-space:pre-wrap}} .a{{padding:6px 9px;border:1px solid var(--rule);border-radius:4px;white-space:pre-wrap;word-break:break-word}}
.flags{{font-size:11px;color:var(--muted);margin-top:3px}} .bad{{color:var(--bad);font-weight:600}} .good{{color:var(--good);font-weight:600}} .tag{{display:inline-block;padding:0 6px;border-radius:10px;border:1px solid var(--rule);font-size:11px}} .tag.fail{{border-color:var(--bad);color:var(--bad)}} .why{{font-style:italic}} mark{{background:var(--hl);color:inherit}} button{{font:13px inherit;padding:6px 14px;border:1px solid var(--rule);background:var(--card);color:var(--ink);border-radius:4px;cursor:pointer}}
</style><main>
<h1>Picky-user benchmark, every dialogue</h1>
<p class="sub">{len(dl)} simulated dialogues (a Sol user prompted with the owner's chats) against four models; per turn: the user's move, the model's answer, regex flags (loop, tail copy, request not addressed, language slip, stop honoured) and the judge's tone, coherence and premise verdicts · 9 September 2026</p>
<div class="bar"><select id="fm"><option value="">all models</option>{opts(['armB','stage1','apertus','krikri'])}</select><select id="fv"><option value="">any move</option>{opts(moves)}</select><select id="fs"><option value="">any surface</option>{opts(['el','atonic','greeklish','formal'])}</select>
<select id="fd"><option value="">all dialogues</option><option value="dead">dead (ended in a loop)</option><option value="clean">no broken turn</option></select><select id="ft"><option value="">any tone</option>{opts(['curt','snarky','servile','fine'])}</select><input id="fq" placeholder="search text"><span class="count" id="cnt"></span></div>
<div id="list"></div><p style="text-align:center"><button id="more">show 20 more</button></p></main>
<script id="rows" type="application/json">{json.dumps(dl, ensure_ascii=False).replace('</', '<\\/')}</script>
<script>
const R = JSON.parse(document.getElementById('rows').textContent); const $ = id => document.getElementById(id); let shown = 0, cur = R;
const esc = s => (s || '').replace(/[&<>]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c]));
function turn(t) {{
  const f = []; if (t.loop) f.push('<span class="bad">loop</span>'); if (t.tail) f.push('<span class="bad">tail copy</span>'); if (!t.key) f.push('<span class="bad">request not addressed</span>'); if (t.slip) f.push('<span class="bad">language slip</span>'); if (t.stop === false) f.push('<span class="bad">stop ignored</span>'); if (t.stop === true) f.push('<span class="good">stop honoured</span>');
  if (t.tone) f.push('tone: ' + (t.tone === 'fine' ? '<span class="good">fine</span>' : '<span class="bad">' + t.tone + '</span>')); if (t.coh !== null && t.coh !== undefined) f.push(t.coh ? '<span class="good">coherent</span>' : '<span class="bad">incoherent</span>'); if (t.prem >= 0) f.push('premise ' + t.prem + '/2'); if (t.hon >= 0) f.push(t.hon ? 'honoured' : '<span class="bad">not honoured</span>');
  return `<div class="turn"><div class="mv">${{t.move}}</div><div><div class="u">${{esc(t.u)}}</div><div class="a">${{esc(t.a)}}</div><div class="flags">${{f.join(' · ')}}${{t.why ? ' · <span class="why">' + esc(t.why) + '</span>' : ''}}</div></div></div>`;
}}
function card(d) {{ return `<div class="dlg"><div class="meta"><b>${{esc(d.label)}}</b><span>${{d.surface}}</span><span>intent: ${{esc(d.intent)}}</span><span>${{d.n}} turns</span><span>${{d.broken}} broken</span>${{d.dead ? '<span class="tag fail">dead</span>' : ''}}<span>coherent ${{Math.round(d.coherent*100)}}%</span><span>${{d.id}}</span></div>${{d.turns.map(turn).join('')}}</div>`; }}
function apply() {{ const m = $('fm').value, v = $('fv').value, s = $('fs').value, dd = $('fd').value, t = $('ft').value, q = $('fq').value.trim().toLowerCase();
  cur = R.filter(d => (!m || d.model === m) && (!v || d.moves.includes(v)) && (!s || d.surface === s) && (dd === '' || (dd === 'dead' ? d.dead : d.broken === 0)) && (!t || d.tones.includes(t)) && (!q || d.turns.some(x => (x.u + ' ' + x.a).toLowerCase().includes(q))));
  shown = 0; $('list').innerHTML = ''; more(); }}
function more() {{ const next = cur.slice(shown, shown + 20); $('list').insertAdjacentHTML('beforeend', next.map(card).join('')); shown += next.length; $('cnt').textContent = `${{shown}} of ${{cur.length}} dialogues`; $('more').hidden = shown >= cur.length; }}
for (const id of ['fm','fv','fs','fd','ft']) $(id).addEventListener('change', apply); let tm; $('fq').addEventListener('input', () => {{ clearTimeout(tm); tm = setTimeout(apply, 250); }}); $('more').addEventListener('click', more); apply();
</script>'''
open(OUT, 'w').write(page); print(len(dl), 'dialogues →', OUT, f'{os.path.getsize(OUT)/1e6:.1f} MB')
