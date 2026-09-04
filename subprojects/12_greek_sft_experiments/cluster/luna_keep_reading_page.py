#!/usr/bin/env python3
"""Reading page of rows the judge KEPT, for the owner to catch the judge's misses (review F9).
Usage: python3 cluster/luna_keep_reading_page.py <out.html> <n_per_block> <block1> [block2 ...]   (reads ~/sft_annot exports + labels)"""
import json, sys, html, random, os
OUT, N = sys.argv[1], int(sys.argv[2]); BLOCKS = sys.argv[3:]; A = os.path.expanduser('~/sft_annot'); E = html.escape; random.seed(21)
css = """
:root{--bg:#edeef2;--paper:#fbfbfd;--ink:#1a1c22;--muted:#5c6170;--rule:#ccd0da;--accent:#5a3f7a;--user:#f0eef6;
--serif:"Literata",Georgia,serif;--sans:"Source Sans 3",-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;--mono:"JetBrains Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#131419;--paper:#1c1e26;--ink:#e6e7ec;--muted:#a0a4b2;--rule:#363a48;--accent:#c1a6e6;--user:#242030}}
:root[data-theme="dark"]{--bg:#131419;--paper:#1c1e26;--ink:#e6e7ec;--muted:#a0a4b2;--rule:#363a48;--accent:#c1a6e6;--user:#242030}
*{box-sizing:border-box}body{background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.5;margin:0}
main{max-width:1000px;margin:0 auto;padding:30px 24px 80px}h1{font-family:var(--serif);font-size:28px;margin:0 0 6px}h2{font-family:var(--serif);font-size:20px;margin:30px 0 8px}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--accent)}p{max-width:80ch}
article{background:var(--paper);border:1px solid var(--rule);padding:14px 16px;margin:12px 0}.meta{font-family:var(--mono);font-size:11.5px;color:var(--muted);margin-bottom:6px}
.turn{white-space:pre-wrap;padding:8px 12px;margin:6px 0;border-left:3px solid var(--rule);max-height:28em;overflow:auto;font-size:14px}.user{background:var(--user);border-color:var(--accent)}
.role{font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
"""
h = [f'<title>Judge Keep Rows, Reading</title><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,400;7..72,600&family=Source+Sans+3:wght@400;600&family=JetBrains+Mono:wght@400&display=swap"><style>{css}</style><main>']
h.append('<p class="eyebrow">rows Luna marked keep · random sample per block · the judge\'s misses are the unmeasured side</p><h1>Judge Keep Rows, Reading</h1>')
h.append('<p>Each card is a row the judge decided to keep, with its label. Read for what the judge would have missed: an identity line, a wrong answer, a foreign frame the user did not ask for, chatbot mannerisms. Note the row id of anything you would not keep.</p>')
for b in BLOCKS:
    labs = {}
    lp = f'{A}/labels/{b}.labels.jsonl'
    if not os.path.exists(lp): continue
    for l in open(lp):
        j = json.loads(l)
        if j.get('disposition') == 'keep': labs[j['id']] = j
    rows = [json.loads(l) for l in open(f'{A}/core_export/{b}.jsonl') if json.loads(l)['id'] in labs]
    sample = random.sample(rows, min(N, len(rows))); h.append(f'<h2>{E(b)} · {len(labs)} keep rows so far · {len(sample)} shown</h2>')
    for r in sample:
        j = labs[r['id']]; h.append(f'<article><div class="meta">{E(r["id"][:40])} · vantage {j.get("vantage")} · {E(str(j.get("frame_type")))} · {E(str(j.get("skill")))} · quality {j.get("quality")} · mannerism {j.get("mannerism")} · judge {E(str(j.get("judge","luna")))} · why: {E(str(j.get("why"))[:120])}</div>')
        for t in (r.get('turns') or [dict(role='user', content=r['user']), dict(role='assistant', content=r['assistant'])]):
            h.append(f'<div class="turn {E(t.get("role") or "")}"><div class="role">{E(t.get("role") or "")}</div>{E((t.get("content") or "")[:6000])}</div>')
        h.append('</article>')
h.append('</main>'); open(OUT, 'w', encoding='utf-8').write('\n'.join(h)); print('wrote', OUT)
