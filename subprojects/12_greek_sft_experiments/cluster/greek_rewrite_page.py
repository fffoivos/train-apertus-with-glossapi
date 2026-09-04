#!/usr/bin/env python3
"""Reading page for the Sol-written Greek rewriting set: N random rows, passage, instruction, answer, optional edited answer.
Usage: python3 cluster/greek_rewrite_page.py <gen.jsonl> <out.html> [n] [edit.jsonl]"""
import json, sys, html, random, collections
IN, OUT = sys.argv[1], sys.argv[2]; N = int(sys.argv[3]) if len(sys.argv) > 3 else 40; ED = sys.argv[4] if len(sys.argv) > 4 else None
E = html.escape
rows = [json.loads(l) for l in open(IN)]; rows = [r for r in rows if r.get('passage') and r.get('answer')]
edits = {}
if ED:
    for l in open(ED):
        j = json.loads(l); edits[j['id']] = j
random.seed(40); sample = random.sample(rows, min(N, len(rows)))
tasks = collections.Counter(r['task'] for r in rows); genres = collections.Counter(r['genre'] for r in rows)
css = """
:root{--bg:#eef0ea;--paper:#fbfbf8;--ink:#1c1e19;--muted:#5d6156;--rule:#cfd3c6;--accent:#4a5f2f;--user:#f1f4ea;--edit:#fff5dc;
--serif:"Literata",Georgia,serif;--sans:"Source Sans 3",-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;--mono:"JetBrains Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#15170f;--paper:#1e2117;--ink:#e7e9df;--muted:#a3a89a;--rule:#3a3f30;--accent:#a6c46f;--user:#232819;--edit:#2e2a18}}
:root[data-theme="dark"]{--bg:#15170f;--paper:#1e2117;--ink:#e7e9df;--muted:#a3a89a;--rule:#3a3f30;--accent:#a6c46f;--user:#232819;--edit:#2e2a18}
*{box-sizing:border-box}body{background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:15.5px;line-height:1.55;margin:0}
main{max-width:980px;margin:0 auto;padding:30px 24px 80px}h1{font-family:var(--serif);font-size:30px;margin:0 0 6px}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--accent);margin:0 0 6px}
p{max-width:80ch}.stats{font-size:13px;color:var(--muted);margin:6px 0 22px}
article{background:var(--paper);border:1px solid var(--rule);padding:16px 18px;margin:14px 0}
.meta{font-family:var(--mono);font-size:11.5px;color:var(--muted);margin-bottom:8px}
.block{white-space:pre-wrap;padding:10px 12px;margin:8px 0;border-left:3px solid var(--rule)}
.passage{background:var(--user)}.instruction{border-color:var(--accent);font-weight:600}.answer{background:var(--paper)}.edited{background:var(--edit)}
.label{font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-bottom:3px}
"""
h = [f'<title>Greek Rewriting Set, Reading</title><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,400;7..72,600&family=Source+Sans+3:wght@400;600&family=JetBrains+Mono:wght@400&display=swap"><style>{css}</style><main>']
h.append('<p class="eyebrow">Σύνολο ξαναγραψίματος και περίληψης · γραμμένο από τον Sol στα ελληνικά · δείγμα για ανάγνωση</p><h1>Greek Rewriting Set, Reading</h1>')
h.append(f'<p class="stats">{len(rows)} rows generated so far; {len(sample)} shown at random. Tasks: ' + ', '.join(f'{k} {v}' for k, v in tasks.most_common()) + '.</p>')
h.append('<p>Each card is one training row: the source passage Sol wrote in a Greek setting, the user\'s instruction, and the answer. Where a corrected answer exists it is shown below the original with the editor\'s notes. Read for: does the answer do exactly what was asked, is it faithful to the passage, is the Greek natural, is there any chatbot mannerism or foreign frame.</p>')
for r in sample:
    h.append(f'<article><div class="meta">{E(r["id"])} · {E(r["genre"])} · {E(r["register"])} · task {E(r["task"])} · {r.get("seconds","")} s</div>')
    h.append(f'<div class="label">κείμενο</div><div class="block passage">{E(r["passage"])}</div>')
    h.append(f'<div class="label">οδηγία χρήστη</div><div class="block instruction">{E(r["instruction"])}</div>')
    h.append(f'<div class="label">απάντηση</div><div class="block answer">{E(r["answer"])}</div>')
    e = edits.get(r['id'])
    if e and e.get('verdict') in ('edited', 'rewrite'):
        h.append(f'<div class="label">διορθωμένη απάντηση ({E(e["verdict"])})</div><div class="block edited">{E(e.get("edited_answer") or "")}</div><div class="meta">' + ' · '.join(E(c) for c in e.get('changes', [])) + '</div>')
    elif e: h.append('<div class="meta">επιμελητής: ok, καμία αλλαγή</div>')
    h.append('</article>')
h.append('</main>'); open(OUT, 'w', encoding='utf-8').write('\n'.join(h)); print('wrote', OUT, len(sample), 'rows of', len(rows))
