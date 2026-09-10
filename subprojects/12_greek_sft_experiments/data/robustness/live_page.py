#!/usr/bin/env python3
"""Reader page for the live dialogues (owner review): profile, every turn with the responder's assessment and move, stop reason. Usage: python3 live_page.py <dialogues.jsonl> <out.html>"""
import html, json, sys
rows = [json.loads(l) for l in open(sys.argv[1])]
CSS = """<title>Live Dialogues v0</title><style>
:root{--bg:#f7f6f2;--ink:#1e1d1a;--muted:#6b675e;--rule:#dcd8cf;--card:#fffdf8;--user:#eef3f8;--asst:#f3f0e8;--ok:#2f7d4f;--bad:#b3402f;--warn:#a06a10;--acc:#3b5f8a}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#171613;--ink:#ece8df;--muted:#a49f93;--rule:#3a3730;--card:#211f1b;--user:#1e2a36;--asst:#2a2721;--ok:#6fc38f;--bad:#e2705c;--warn:#e0a94a;--acc:#8fb3dd}}
:root[data-theme="dark"]{--bg:#171613;--ink:#ece8df;--muted:#a49f93;--rule:#3a3730;--card:#211f1b;--user:#1e2a36;--asst:#2a2721;--ok:#6fc38f;--bad:#e2705c;--warn:#e0a94a;--acc:#8fb3dd}
body{background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,"Helvetica Neue",Arial,sans-serif;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 4px} .sub{color:var(--muted);margin-bottom:20px} .d{background:var(--card);border:1px solid var(--rule);border-radius:8px;padding:16px;margin:0 0 20px;max-width:900px}
.meta{font-size:13px;color:var(--muted);margin-bottom:8px} .prof{font-size:13px;border-left:3px solid var(--acc);padding:6px 10px;margin:8px 0 12px;white-space:pre-wrap}
.m{padding:8px 12px;border-radius:6px;margin:6px 0;white-space:pre-wrap} .u{background:var(--user)} .a{background:var(--asst)} .lab{font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);margin-bottom:2px}
.tag{display:inline-block;font-size:11px;padding:0 6px;border-radius:10px;border:1px solid var(--rule);margin-left:6px} .ok{color:var(--ok);border-color:var(--ok)} .bad{color:var(--bad);border-color:var(--bad)} .warn{color:var(--warn);border-color:var(--warn)}
</style>"""
def tag(a):
    if not a: return ''
    cls = 'ok' if a == 'ok' else 'bad'; return f'<span class="tag {cls}">{html.escape(a)}</span>'
out = [CSS, '<h1>Live Dialogues v0</h1>', f'<div class="sub">{len(rows)} dialogues · arm B on the laptop (MLX 8-bit, t=0.8, top-p 0.9, 512 tokens) · responder: Sol high effort with a profile and the owner\'s calm chats as examples · each assistant turn carries the responder\'s assessment of it and the move it chose next</div>']
for r in rows:
    p = r['profile']; out.append(f'<div class="d"><div class="meta"><b>{html.escape(r["id"])}</b> · {html.escape(r["intent"])} · {html.escape(r["surface"])} · {html.escape(r["temperament"])} · {r["n_turns"]} turns · stop: <b>{html.escape(r["stop_reason"])}</b> · assessments {html.escape(json.dumps(r["assessments"], ensure_ascii=False))}</div>')
    out.append(f'<div class="prof">{html.escape(p["persona"])}\nGoal: {html.escape(p["goal"])} — done when: {html.escape(p["done_when"])}\nHidden facts: {html.escape("; ".join(p["facts"]))}\nTemperament: {html.escape(p["temperament"])}</div>')
    turns = {t['i']: t for t in r['turns']}; i = 0
    for m in r['messages']:
        if m['role'] == 'user': out.append(f'<div class="m u"><div class="lab">user</div>{html.escape(m["content"])}</div>')
        else:
            t = turns.get(i, {}); flags = ''.join(f'<span class="tag warn">{f}</span>' for f in ('sentence reuse' if t.get('sentence_reuse') else '', 'near-identical' if t.get('near_identical') else '') if f)
            out.append(f'<div class="m a"><div class="lab">assistant · {t.get("n_words", "")} words {tag(t.get("assessment"))}{(" <span class=\"tag\">next: " + html.escape(t["move"]) + "</span>") if t.get("move") else ""}{flags}</div>{html.escape(m["content"])}</div>'); i += 1
    out.append('</div>')
open(sys.argv[2], 'w').write('\n'.join(out)); print('page', sys.argv[2], len(rows), 'dialogues')
