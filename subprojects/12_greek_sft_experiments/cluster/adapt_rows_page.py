#!/usr/bin/env python3
"""Adapt rows with their adapt notes, n per dataset, for the owner's reading. Sonnet's second opinion shown where the row was in the check.
Usage: python3 cluster/adapt_rows_page.py <out.html> <n_per_block> <block1> [block2 ...]"""
import json, sys, html, random, os, glob
OUT, N = sys.argv[1], int(sys.argv[2]); BLOCKS = sys.argv[3:]; A = os.path.expanduser('~/sft_annot'); E = html.escape
NAMES = {'dolci_science': 'Science (Sol)', 'nemotron_chat_a': 'Nemotron chat A', 'dolci_safety': 'Dolci safety', 'dolci_chat': 'OpenAssistant chat', 'smoltalk2_multilingual': 'Multilingual',
         'dolci_tooluse_sample3k': 'Tool-use sample', 'greek_ours': 'Our Greek set', 'dolci_precise_if_20k': 'Precise IF (Sol)'}
sonnet = {}
for f in glob.glob(f'{A}/sonnet_check/*.jsonl'):
    for l in open(f):
        j = json.loads(l); sonnet[(j['block'], j['id'])] = j
data = {}
for b in BLOCKS:
    lab = {}
    for l in open(f'{A}/labels/{b}.labels.jsonl'):
        j = json.loads(l)
        if j.get('disposition') == 'adapt': lab[j['id']] = j
    ids = sorted(lab); random.Random(f'adapt:{b}').shuffle(ids); pick = set(ids[:N]); rows = []
    for l in open(f'{A}/core_export/{b}.jsonl'):
        if not pick: break
        r = json.loads(l)
        if r['id'] in pick:
            pick.discard(r['id']); j = lab[r['id']]; s = sonnet.get((b, r['id']))
            rows.append(dict(id=r['id'], note=j.get('adapt_note') or '', why=j.get('why') or '', vantage=j.get('vantage'), frame=j.get('frame_type'), skill=j.get('skill'), quality=j.get('quality'), judge=j.get('judge'),
                             sonnet=(f"{s['sonnet']} — {s.get('s_why') or ''}" if s else None),
                             user=[(t.get('content') or '')[:1200] for t in r['turns'] if t['role'] == 'user'][:1], asst=' ⏎⏎ '.join((t.get('content') or '') for t in r['turns'] if t['role'] == 'assistant')[:2200]))
    rows.sort(key=lambda r: r['id']); data[b] = dict(name=NAMES.get(b, b), total=len(lab), rows=rows)
css = """
:root{--ground:#eceef2;--paper:#fff;--ink:#1b1f27;--muted:#636b79;--rule:#d2d7df;--accent:#3b4f8a;--user:#f3f5f8;--adapt:#a86c14;--adapt-bg:#f9efdc;
--display:"Fraunces",Georgia,serif;--sans:"IBM Plex Sans",-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--ground:#15181e;--paper:#1e2229;--ink:#e6e8ec;--muted:#9aa3b2;--rule:#333a46;--accent:#9fb0e6;--user:#252a33;--adapt:#e3b46a;--adapt-bg:#3d3120}}
:root[data-theme="dark"]{--ground:#15181e;--paper:#1e2229;--ink:#e6e8ec;--muted:#9aa3b2;--rule:#333a46;--accent:#9fb0e6;--user:#252a33;--adapt:#e3b46a;--adapt-bg:#3d3120}
*{box-sizing:border-box}body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.5}
header{padding:28px 24px 0;max-width:1100px;margin:0 auto}h1{font-family:var(--display);font-weight:500;font-size:34px;margin:0 0 6px;letter-spacing:-.01em;text-wrap:balance}
.lede{color:var(--muted);max-width:72ch;margin:0 0 18px}
.pills{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px}.pill{border:1px solid var(--rule);background:var(--paper);color:var(--ink);border-radius:999px;padding:6px 14px;font:inherit;font-size:14px;cursor:pointer}
.pill[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}.pill:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
main{max-width:1100px;margin:0 auto;padding:0 24px 60px}
article{background:var(--paper);border:1px solid var(--rule);border-radius:10px;margin-bottom:16px;overflow:hidden}
.note{padding:12px 18px;border-left:5px solid var(--adapt);background:var(--adapt-bg);display:grid;gap:4px}
.note .n{font-size:15.5px;font-weight:600}.note .n span{font-weight:400;color:var(--muted);font-size:12px;letter-spacing:.08em;text-transform:uppercase;margin-right:8px}
.note .w{color:var(--muted);font-size:13.5px}.note .s{font-size:13.5px}
.meta{font-family:var(--mono);font-size:11.5px;color:var(--muted);display:flex;flex-wrap:wrap;gap:4px 14px}
.turn{padding:12px 18px;white-space:pre-wrap;overflow-wrap:anywhere;max-width:82ch}.turn.user{background:var(--user);color:var(--muted);font-size:14px;max-width:none}
.role{font-family:var(--mono);font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
"""
out = ['<title>Adapt Rows Reader</title>', '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500&family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono&display=swap">', f'<style>{css}</style>',
       '<header><h1>Adapt Rows Reader</h1><p class="lede">Rows the judge marked adapt: worth keeping, but framed in a foreign world or carrying one identity line. Each card leads with the judge\'s adapt note (what it would change), then its reason, then Sonnet 5\'s second opinion where the row was in the cross-check.</p>',
       '<div class="pills" role="group" aria-label="dataset">' + ''.join(f'<button class="pill" data-block="{E(b)}" aria-pressed="{"true" if k == 0 else "false"}">{E(data[b]["name"])} · {len(data[b]["rows"])} of {data[b]["total"]:,}</button>' for k, b in enumerate(BLOCKS)) + '</div></header>',
       '<main id="cards"></main>', '<script>const DATA=' + json.dumps(data, ensure_ascii=False).replace('</', '<\\/') + ';',
       r"""const E=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));let block=Object.keys(DATA)[0];
function render(){document.querySelectorAll('.pill').forEach(b=>b.setAttribute('aria-pressed',b.dataset.block===block));const d=DATA[block];
document.getElementById('cards').innerHTML=d.rows.map(r=>`<article><div class="note"><div class="n"><span>adapt note</span>${E(r.note)||'<i>none given</i>'}</div><div class="w">why: ${E(r.why)}</div>${r.sonnet?`<div class="s">Sonnet 5: ${E(r.sonnet)}</div>`:''}<div class="meta"><span>${E(r.id)}</span><span>${E(r.judge)}</span><span>vantage ${E(r.vantage)}</span><span>frame ${E(r.frame)}</span><span>skill ${E(r.skill)}</span><span>quality ${E(r.quality)}</span></div></div><div class="turn user"><div class="role">user</div>${E(r.user[0]||'')}</div><div class="turn"><div class="role">assistant${r.asst.length>=2200?' (first 2,200 characters)':''}</div>${E(r.asst)}</div></article>`).join('');window.scrollTo({top:0});}
document.querySelectorAll('.pill').forEach(b=>b.addEventListener('click',()=>{block=b.dataset.block;render();}));render();</script>"""]
open(OUT, 'w').write('\n'.join(out)); print('wrote', OUT, os.path.getsize(OUT) // 1024, 'KB')
