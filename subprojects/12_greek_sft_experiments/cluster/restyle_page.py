#!/usr/bin/env python3
"""Reader for a restyle pass: per row the old answer, the decision (type, expected/actual level, missing, reason) and the new answer.
Usage: python3 restyle_page.py <out.html> <restyle.jsonl> [title] [checks.jsonl] [--final]
  default: left = the ORIGINAL (v1) answer, right = the restyle output, editor block below.
  --final: left = the restyle output (writer), right = the final text after the editor (rows the editor changed carry pre_edit_messages)."""
import json, sys, html, collections, statistics as st
argv0 = [a for a in sys.argv if a != '--final']; OUT, IN = argv0[1], argv0[2]; TITLE = argv0[3] if len(argv0) > 3 else 'Restyle pass'; FINAL = '--final' in sys.argv; argv = [a for a in sys.argv if a != '--final']
CHKS = argv[4].split(',') if len(argv) > 4 else []
rows = [json.loads(l) for l in open(IN)]
checks = {}  # id -> list of verdicts (one per editor file)
for CHK in CHKS:
    for l in open(CHK):
        j = json.loads(l)
        if j.get('verdict'): checks.setdefault(j['id'], []).append(j)
e = lambda s: html.escape(str(s if s is not None else ''))
CAT = {'A': 'A Greece facts', 'B': 'B who am I', 'C': 'C identity under pressure', 'D': 'D limits', 'E': 'E refusals in our voice', 'F': 'F sensitive Greek topics', 'G': 'G register'}
TYPES = {1: 'what/who/where', 2: 'when/how much', 3: 'why/how', 4: 'comparison', 5: 'wrong assumption', 6: 'broad request', 7: 'practical', 8: 'sensitive', 9: 'who are you', 10: 'chat/opinion'}
def msgs(ms):
    return ''.join(f'<div class="m {m["role"]}"><span class="r">{e(m["role"])}</span>{e(m["content"])}</div>' for m in ms)
cats = sorted({r['category'] for r in rows}); summ = []
for c in cats:
    rs = [r for r in rows if r['category'] == c]; o = [len(r['old_messages'][-1]['content']) for r in rs]; n = [len(r['messages'][-1]['content']) for r in rs]
    summ.append(f'<tr><td>{e(CAT.get(c, c))}</td><td class="n">{len(rs)}</td><td class="n">{sum(1 for r in rs if r["decision"]=="keep")}</td><td class="n">{sum(1 for r in rs if r["decision"]=="rewrite")}</td><td class="n">{sum(1 for r in rs if r["actual_level"]=="under")}</td><td class="n">{sum(1 for r in rs if r["placeholders"])}</td><td class="n">{int(st.median(o))}</td><td class="n">{int(st.median(n))}</td></tr>')
tot_cost = ''
def cols(r, d):
    if not FINAL:
        return f'''<div class="cols"><section><h4>Before <span class="n">{len(r['old_messages'][-1]['content'])} chars</span></h4>{msgs(r['old_messages'])}</section>
<section><h4>After <span class="n">{len(r['messages'][-1]['content'])} chars</span></h4>{msgs(r['messages']) if d == 'rewrite' else '<p class="muted">kept as is</p>'}</section></div>'''
    writer = r.get('pre_edit_messages') or r['messages']; edited = bool(r.get('pre_edit_messages'))
    return f'''<div class="cols"><section><h4>Restyle output (writer) <span class="n">{len(writer[-1]['content'])} chars</span></h4>{msgs(writer)}</section>
<section><h4>After the editor (final) <span class="n">{len(r['messages'][-1]['content'])} chars</span></h4>{msgs(r['messages']) if edited else '<p class="muted">unchanged by the editor</p>'}</section></div>'''
def editor_block(r):
    return ''.join(one_editor(r, c) for c in checks.get(r['id'], []))
def one_editor(r, c):
    v = c.get('verdict'); ch = ''.join(f'<li>{e(x)}</li>' for x in (c.get('changes') or []))
    turns = c.get('edited_assistant_turns') or []; orig = [m['content'] for m in r['messages'] if m['role'] == 'assistant']
    edited = ''
    if v != 'ok' and len(turns) == len(orig):
        for k, (a, b) in enumerate(zip(orig, turns)):
            if isinstance(b, str) and b != a and not FINAL: edited += f'<div class="m assistant"><span class="r">edited assistant turn {k+1}</span>{e(b)}</div>'
    fd = (c.get('fact_doubt') or '').strip()
    return f'''<div class="editor"><h4>Editor ({e(c.get('judge'))}) <span class="pill ed-{e(v)}">{e(v)}</span> <span class="n">Greekness {e(c.get('greekness'))}</span></h4>{'<ul>' + ch + '</ul>' if ch else '<p class="muted">no changes</p>'}{edited}{'<p class="muted"><strong>Fact doubt:</strong> ' + e(fd) + '</p>' if fd else ''}</div>'''
body = []
for r in rows:
    d = r['decision']; miss = ''.join(f'<li>{e(m)}</li>' for m in (r.get('missing') or []))
    bs = ', '.join(e(x) for x in (r.get('beyond_sheet') or []))
    body.append(f'''<article class="row" data-cat="{e(r['category'])}" data-dec="{e(d)}">
<header><span class="id">{e(r['id'])}</span><span class="pill {e(d)}">{e(d)}</span><span class="meta">type {e(r.get('type'))} {e(TYPES.get(r.get('type'), ''))} · expected {e(r.get('expected_level'))} · actual {e(r.get('actual_level'))} · {e(r.get('user_type') or '')}</span></header>
{cols(r, d)}
{editor_block(r)}<div class="judge"><p><strong>Reason:</strong> {e(r.get('reason'))}</p>{'<p><strong>Purpose:</strong> ' + e(r.get('purpose')) + '</p>' if r.get('purpose') else ''}{'<p><strong>Missing:</strong></p><ul>' + miss + '</ul>' if miss else ''}{'<p class="muted"><strong>Beyond the sheet (to verify):</strong> ' + bs + '</p>' if bs else ''}{'<p class="ph">Placeholder resolved</p>' if r.get('placeholders') else ''}</div>
</article>''')
page = f'''<title>{e(TITLE)}</title>
<style>
:root{{--bg:#F6F7F4;--ink:#1C2128;--accent:#235789;--good:#4F7A2A;--short:#B4462B;--muted:#5F6B78;--rule:#D9DED6;--panel:#FFFFFF;--tint:#EEF2F6;--user:#EEF2F6;--asst:#FFFFFF}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#12161B;--ink:#E6E9EC;--accent:#7FB0E0;--good:#9CCB6A;--short:#E58A6C;--muted:#98A2AD;--rule:#2A323B;--panel:#1A2027;--tint:#1F2830;--user:#1F2830;--asst:#1A2027}}}}
:root[data-theme="dark"]{{--bg:#12161B;--ink:#E6E9EC;--accent:#7FB0E0;--good:#9CCB6A;--short:#E58A6C;--muted:#98A2AD;--rule:#2A323B;--panel:#1A2027;--tint:#1F2830;--user:#1F2830;--asst:#1A2027}}
body{{background:var(--bg);color:var(--ink);font-family:"Source Sans 3","Segoe UI",Roboto,Arial,sans-serif;font-size:16px;line-height:1.5;margin:0}}
main{{max-width:1180px;margin:0 auto;padding:2rem 1.2rem 4rem}}
h1{{font-family:Literata,Georgia,serif;font-size:1.8rem;margin:0 0 .3rem}} h4{{margin:0 0 .4rem;font-size:.85rem;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}}
.tbl{{overflow-x:auto;margin:1rem 0}} table{{border-collapse:collapse;font-size:.9rem}} th,td{{padding:.4rem .6rem;border-bottom:1px solid var(--rule);text-align:left}} th{{font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);background:var(--tint)}} td.n,.n{{font-variant-numeric:tabular-nums;text-align:right;font-family:ui-monospace,Menlo,monospace;font-size:.85rem}}
.filters{{display:flex;flex-wrap:wrap;gap:.5rem;margin:1rem 0;align-items:center;font-size:.9rem}} .filters button{{background:var(--panel);color:var(--ink);border:1px solid var(--rule);border-radius:3px;padding:.25rem .6rem;cursor:pointer;font:inherit;font-size:.85rem}} .filters button.on{{border-color:var(--accent);color:var(--accent);font-weight:600}} .filters button:focus-visible{{outline:2px solid var(--accent)}}
.row{{background:var(--panel);border:1px solid var(--rule);border-radius:4px;margin:1rem 0;padding:.8rem 1rem}} .row[hidden]{{display:none}}
header{{display:flex;flex-wrap:wrap;gap:.6rem;align-items:center;margin-bottom:.6rem}} .id{{font-family:ui-monospace,Menlo,monospace;font-size:.85rem;background:var(--tint);padding:.05em .4em;border-radius:3px}} .meta{{color:var(--muted);font-size:.85rem}}
.pill{{font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;font-weight:700;padding:.1em .5em;border-radius:2px;color:#fff}} .pill.rewrite{{background:var(--short)}} .pill.keep{{background:var(--good)}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:1rem}} @media (max-width:800px){{.cols{{grid-template-columns:1fr}}}}
.m{{padding:.5rem .7rem;border-radius:3px;margin:.3rem 0;white-space:pre-wrap;font-size:.95rem}} .m.user{{background:var(--user)}} .m.assistant{{background:var(--asst);border:1px solid var(--rule)}} .m .r{{display:block;font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-bottom:.15rem}}
.editor{{margin-top:.6rem;padding:.6rem .8rem;border-left:3px solid var(--accent);background:var(--tint);font-size:.9rem}} .editor h4{{margin:0 0 .3rem;display:flex;gap:.6rem;align-items:center}} .editor ul{{margin:.2rem 0 .3rem 1.2rem}} .pill.ed-ok{{background:var(--good)}} .pill.ed-edited{{background:var(--accent)}} .pill.ed-rewrite{{background:var(--short)}}
.judge{{margin-top:.6rem;padding-top:.5rem;border-top:1px dashed var(--rule);font-size:.9rem}} .judge p{{margin:.25rem 0}} .judge ul{{margin:.1rem 0 .3rem 1.2rem}} .muted{{color:var(--muted)}} .ph{{color:var(--accent);font-weight:600}}
</style>
<main>
<h1>{e(TITLE)}</h1>
<p class="muted">One prompt per row: classify the question (type, purpose, expected level), judge the current answer, decide keep or rewrite, and rewrite under the style guide. Left: the restyle output (writer, Opus). Right: the final text after the Opus editor; rows the editor left alone say so. The editor block lists the verdict and each change. Placeholder values in the rewrites are the settled name and the PROPOSED cutoff «περίπου ως τα μέσα του 2025» and licence «Apache 2.0».</p>
<div class="tbl"><table><tr><th>Category</th><th>Rows</th><th>Keep</th><th>Rewrite</th><th>Under level</th><th>Placeholders</th><th>Median chars before</th><th>after</th></tr>{''.join(summ)}</table></div>
<div class="filters"><span>Category:</span>{''.join(f'<button data-f="cat" data-v="{c}" class="on">{c}</button>' for c in cats)}<span> · Decision:</span><button data-f="dec" data-v="keep" class="on">keep</button><button data-f="dec" data-v="rewrite" class="on">rewrite</button><span id="count" class="muted"></span></div>
{''.join(body)}
</main>
<script>
const on={{cat:new Set({json.dumps(cats)}),dec:new Set(['keep','rewrite'])}};
function apply(){{let n=0;document.querySelectorAll('.row').forEach(r=>{{const v=on.cat.has(r.dataset.cat)&&on.dec.has(r.dataset.dec);r.hidden=!v;if(v)n++;}});document.getElementById('count').textContent=' '+n+' rows shown';}}
document.querySelectorAll('.filters button').forEach(b=>b.addEventListener('click',()=>{{const s=on[b.dataset.f];if(s.has(b.dataset.v))s.delete(b.dataset.v);else s.add(b.dataset.v);b.classList.toggle('on');apply();}}));
apply();
</script>'''
open(OUT, 'w').write(page); print(OUT, len(rows), 'rows')
