#!/usr/bin/env python3
"""Reader for the personality set: one tab per category, every row with its facts and Sol's check where present.
Usage: python3 cluster/personality_page.py <rows.jsonl> <sol_check.jsonl|-> <out.html> [max_per_category]"""
import json, sys, html, os, collections, random
ROWS, CHK, OUT = sys.argv[1], sys.argv[2], sys.argv[3]; MAXN = int(sys.argv[4]) if len(sys.argv) > 4 else 400; E = html.escape; HERE = os.path.dirname(os.path.abspath(__file__))
FACTS = {f['id']: f for f in json.load(open(f'{HERE}/../data/personality/facts_greece.json'))}
CATS = {'A': 'Ελληνοκεντρικά γεγονότα', 'B': 'Ποιος είμαι', 'C': 'Ταυτότητα υπό πίεση', 'D': 'Όρια με τη δική μας φωνή', 'E': 'Αρνήσεις με τη δική μας φωνή', 'F': 'Ευαίσθητα ελληνικά θέματα', 'G': 'Ύφος και συμβάσεις'}
rows = [json.loads(l) for l in open(ROWS)]; chk = {}; allchk = collections.defaultdict(list)  # CHK may be several files joined by ','
for f in ([] if CHK == '-' else CHK.split(',')):
    if os.path.exists(f):
        for l in open(f):
            j = json.loads(l)
            if j.get('verdict'): allchk[j['id']].append(j); chk.setdefault(j['id'], j)
by = collections.defaultdict(list)
for r in rows: by[(r.get('category') or '?')[0]].append(r)
data = {}
for c in 'ABCDEFG':
    rs = by.get(c, []); random.Random(c).shuffle(rs); shown = sorted(rs[:MAXN], key=lambda r: r['id'])
    ck = [chk[r['id']] for r in rs if r['id'] in chk]; v = collections.Counter(j['verdict'] for j in ck); g = [j['greekness'] for j in ck if isinstance(j.get('greekness'), int)]
    data[c] = dict(name=CATS.get(c, c), total=len(rs), checked=len(ck), verdicts=dict(v), greekness=(round(sum(g) / len(g), 2) if g else None), doubts=sum(1 for j in ck if (j.get('fact_doubt') or '').strip()),
                   placeholders=sum(1 for r in rs if any('[' in m['content'] and ']' in m['content'] for m in r['messages'])),
                   rows=[dict(id=r['id'], user_type=r.get('user_type'), note=r.get('note'), facts=[FACTS[i]['fact_el'] for i in (r.get('facts_used') or []) if i in FACTS], messages=r['messages'], check=chk.get(r['id']), checks=allchk.get(r['id'], [])) for r in shown])
tot = sum(d['total'] for d in data.values()); allck = [j for j in chk.values()]; vt = collections.Counter(j['verdict'] for j in allck); gt = [j['greekness'] for j in allck if isinstance(j.get('greekness'), int)]
css = """
:root{--ground:#eef0f2;--paper:#fff;--ink:#1b1f27;--muted:#626a78;--rule:#d2d7df;--accent:#2f6f8f;--user:#f2f5f8;--ok:#2b7a58;--ok-bg:#e6f3ec;--ed:#a86c14;--ed-bg:#f9efdc;--rw:#b13b3b;--rw-bg:#f8e6e6;--ph:#7a3f9a;--ph-bg:#f1e6f8;
--display:"Fraunces",Georgia,serif;--sans:"IBM Plex Sans",-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--ground:#15181e;--paper:#1e2229;--ink:#e6e8ec;--muted:#9aa3b2;--rule:#333a46;--accent:#8fc1e0;--user:#252a33;--ok:#7fcaa4;--ok-bg:#1f3a2e;--ed:#e3b46a;--ed-bg:#3d3120;--rw:#ee8f8f;--rw-bg:#40272a;--ph:#c9a6e6;--ph-bg:#33253d}}
:root[data-theme="dark"]{--ground:#15181e;--paper:#1e2229;--ink:#e6e8ec;--muted:#9aa3b2;--rule:#333a46;--accent:#8fc1e0;--user:#252a33;--ok:#7fcaa4;--ok-bg:#1f3a2e;--ed:#e3b46a;--ed-bg:#3d3120;--rw:#ee8f8f;--rw-bg:#40272a;--ph:#c9a6e6;--ph-bg:#33253d}
*{box-sizing:border-box}body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.5}
header{padding:28px 24px 0;max-width:1100px;margin:0 auto}h1{font-family:var(--display);font-weight:500;font-size:34px;margin:0 0 6px;letter-spacing:-.01em;text-wrap:balance}
.lede{color:var(--muted);max-width:74ch;margin:0 0 14px}.summary{display:flex;flex-wrap:wrap;gap:8px 22px;font-size:13.5px;color:var(--muted);margin:0 0 16px}.summary b{color:var(--ink)}
.pills{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px}.pill{border:1px solid var(--rule);background:var(--paper);color:var(--ink);border-radius:999px;padding:6px 14px;font:inherit;font-size:14px;cursor:pointer}
.pill[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}.pill:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
main{max-width:1100px;margin:0 auto;padding:0 24px 60px}.facets{display:flex;flex-wrap:wrap;gap:8px 22px;color:var(--muted);font-size:13px;margin:0 0 16px;padding:12px 16px;background:var(--paper);border:1px solid var(--rule);border-radius:10px}.facets b{color:var(--ink)}
article{background:var(--paper);border:1px solid var(--rule);border-radius:10px;margin-bottom:16px;overflow:hidden}
.turn{padding:12px 18px;white-space:pre-wrap;overflow-wrap:anywhere;max-width:84ch}.turn.user{background:var(--user);color:var(--muted);font-size:14px;max-width:none}.role{font-family:var(--mono);font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
.meta{font-family:var(--mono);font-size:11.5px;color:var(--muted);padding:8px 18px;border-top:1px solid var(--rule);display:flex;flex-wrap:wrap;gap:4px 14px}
.check{padding:10px 18px;border-left:5px solid var(--vc);background:var(--vbg);font-size:13.5px;display:grid;gap:3px}.check .v{font-weight:600}
.ph{background:var(--ph-bg);color:var(--ph);border-radius:4px;padding:0 4px;font-family:var(--mono);font-size:12px}
"""
def mark(s): return E(s).replace('[ΟΝΟΜΑ]', '<span class="ph">[ΟΝΟΜΑ]</span>').replace('[ΗΜΕΡΟΜΗΝΙΑ ΓΝΩΣΗΣ]', '<span class="ph">[ΗΜΕΡΟΜΗΝΙΑ ΓΝΩΣΗΣ]</span>').replace('[ΑΔΕΙΑ]', '<span class="ph">[ΑΔΕΙΑ]</span>')
out = ['<title>Personality Set Reader</title>', '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500&family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono&display=swap">', f'<style>{css}</style>',
       f'<header><h1>Personality Set Reader</h1><p class="lede">Greek rows written natively by Claude Opus 5 from fact sheets and briefs, for the assistant\'s identity, limits, refusals, Greek-centric knowledge and voice. Purple marks are placeholders the owner fills in: <span class="ph">[ΟΝΟΜΑ]</span> the name, <span class="ph">[ΗΜΕΡΟΜΗΝΙΑ ΓΝΩΣΗΣ]</span> the cutoff, <span class="ph">[ΑΔΕΙΑ]</span> the licence. Where Sol checked a row, its verdict and changes sit under the answer, with a Greekness score of 1 to 5 and any fact it doubts.</p>',
       f'<div class="summary"><span><b>{tot:,}</b> rows</span><span>Sol checked <b>{len(allck)}</b>: ok {vt.get("ok",0)}, edited {vt.get("edited",0)}, rewrite {vt.get("rewrite",0)}</span><span>mean Greekness <b>{(round(sum(gt)/len(gt),2) if gt else "—")}</b></span><span>fact doubts <b>{sum(1 for j in allck if (j.get("fact_doubt") or "").strip())}</b></span></div>',
       '<div class="pills" role="group" aria-label="category">' + ''.join(f'<button class="pill" data-c="{c}" aria-pressed="{"true" if k == 0 else "false"}">{c} · {E(data[c]["name"])} · {data[c]["total"]:,}</button>' for k, c in enumerate('ABCDEFG')) + '</div></header>',
       '<main><div class="facets" id="facets"></div><div id="cards"></div></main>', '<script>const DATA=' + json.dumps(data, ensure_ascii=False).replace('</', '<\\/') + ';',
       r"""const E=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));const M=s=>E(s).replace(/\[ΟΝΟΜΑ\]|\[ΗΜΕΡΟΜΗΝΙΑ ΓΝΩΣΗΣ\]|\[ΑΔΕΙΑ\]/g,m=>`<span class="ph">${m}</span>`);let c='A';
function render(){document.querySelectorAll('.pill').forEach(b=>b.setAttribute('aria-pressed',b.dataset.c===c));const d=DATA[c];const v=d.verdicts||{};
document.getElementById('facets').innerHTML=`<span><b>${d.name}</b> ${d.total.toLocaleString()} rows, ${d.rows.length} shown</span><span>Sol checked ${d.checked}: ok ${v.ok||0}, edited ${v.edited||0}, rewrite ${v.rewrite||0}</span><span>Greekness ${d.greekness??'—'}</span><span>fact doubts ${d.doubts}</span><span>rows with placeholders ${d.placeholders}</span>`;
document.getElementById('cards').innerHTML=d.rows.map(r=>{const k=r.check;const vc=k?({ok:'ok',edited:'ed',rewrite:'rw'}[k.verdict]||'ed'):null;
return `<article>${r.messages.map(m=>`<div class="turn ${m.role}"><div class="role">${E(m.role)}</div>${M(m.content)}</div>`).join('')}${(r.checks||[]).map(k=>{const vc={ok:'ok',edited:'ed',rewrite:'rw'}[k.verdict]||'ed';const who=(k.judge||'').includes('sol')?'Sol':(k.judge||'').includes('opus')?'Opus':E(k.judge||'');return `<div class="check" style="--vc:var(--${vc});--vbg:var(--${vc}-bg)"><div class="v">${who}: ${E(k.verdict)} · Greekness ${E(k.greekness)}</div>${(k.changes||[]).map(x=>`<div>• ${E(x)}</div>`).join('')}${k.fact_doubt?`<div><b>fact doubt:</b> ${E(k.fact_doubt)}</div>`:''}${k.verdict!=='ok'?`<div><b>${who}'s version:</b> ${M(k.edited_last_answer||'')}</div>`:''}</div>`}).join('')}<div class="meta"><span>${E(r.id)}</span><span>${E(r.user_type||'')}</span>${r.facts.length?`<span>facts: ${r.facts.map(f=>E(f.slice(0,90))).join(' | ')}</span>`:''}${r.note?`<span>note: ${E(r.note)}</span>`:''}</div></article>`}).join('');window.scrollTo({top:0});}
document.querySelectorAll('.pill').forEach(b=>b.addEventListener('click',()=>{c=b.dataset.c;render();}));render();</script>"""]
open(OUT, 'w').write('\n'.join(out)); print('wrote', OUT, os.path.getsize(OUT) // 1024, 'KB, rows', tot, 'checked', len(allck))
