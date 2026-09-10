#!/usr/bin/env python3
"""Reader page for the live dialogues (owner review): profile, every turn with the responder's assessment and move, stop reason. Usage: python3 live_page.py <dialogues.jsonl> <out.html>"""
import html, json, sys
rows = [json.loads(l) for l in open(sys.argv[1])]
CSS = """<title>Live Dialogues</title><style>
:root{--bg:#f7f6f2;--ink:#1e1d1a;--muted:#6b675e;--rule:#dcd8cf;--card:#fffdf8;--user:#eef3f8;--asst:#f3f0e8;--ok:#2f7d4f;--bad:#b3402f;--warn:#a06a10;--acc:#3b5f8a}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#171613;--ink:#ece8df;--muted:#a49f93;--rule:#3a3730;--card:#211f1b;--user:#1e2a36;--asst:#2a2721;--ok:#6fc38f;--bad:#e2705c;--warn:#e0a94a;--acc:#8fb3dd}}
:root[data-theme="dark"]{--bg:#171613;--ink:#ece8df;--muted:#a49f93;--rule:#3a3730;--card:#211f1b;--user:#1e2a36;--asst:#2a2721;--ok:#6fc38f;--bad:#e2705c;--warn:#e0a94a;--acc:#8fb3dd}
body{background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,"Helvetica Neue",Arial,sans-serif;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 4px} .sub{color:var(--muted);margin-bottom:20px} .d{background:var(--card);border:1px solid var(--rule);border-radius:8px;padding:16px;margin:0 0 20px;max-width:900px}
.meta{font-size:13px;color:var(--muted);margin-bottom:8px} .prof{font-size:13px;border-left:3px solid var(--acc);padding:6px 10px;margin:8px 0 12px;white-space:pre-wrap}
.m{padding:8px 12px;border-radius:6px;margin:6px 0;white-space:pre-wrap} .u{background:var(--user)} .a{background:var(--asst)} .lab{font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);margin-bottom:2px}
.tag{display:inline-block;font-size:11px;padding:0 6px;border-radius:10px;border:1px solid var(--rule);margin-left:6px} .probe{color:var(--acc);border-color:var(--acc)} .rote{font-size:12px;color:var(--muted);border-top:1px dashed var(--rule);margin-top:10px;padding-top:6px} .rote b{color:var(--warn)} mark{background:transparent;color:var(--warn);font-weight:600} .ok{color:var(--ok);border-color:var(--ok)} .bad{color:var(--bad);border-color:var(--bad)} .warn{color:var(--warn);border-color:var(--warn)}
</style>"""
def tag(a):
    if not a: return ''
    cls = 'ok' if a == 'ok' else 'bad'; return f'<span class="tag {cls}">{html.escape(a)}</span>'
title = sys.argv[3] if len(sys.argv) > 3 else 'Live Dialogues'
out = [CSS.replace('Live Dialogues', title), f'<h1>{html.escape(title)}</h1>', f'<div class="sub">{len(rows)} dialogues · arm B on the laptop (MLX 8-bit, t=0.8, top-p 0.9, 512 tokens) · responder: Sol high effort with a profile (goal, hidden facts, a planned change of direction) and the owner\'s calm chats as examples · badges: the responder\'s assessment of each answer, the move it chose next, PROBE = a self-awareness question with the responder\'s verdict on the reply, ROTE = the model\'s recurring sentences (highlighted in the answers)</div>']
for r in rows:
    p = r['profile']; out.append(f'<div class="d"><div class="meta"><b>{html.escape(r["id"])}</b> · {html.escape(r["intent"])} · {html.escape(r["surface"])} · {html.escape(r["temperament"])} · {r["n_turns"]} turns · stop: <b>{html.escape(r["stop_reason"])}</b> · assessments {html.escape(json.dumps(r["assessments"], ensure_ascii=False))}</div>')
    out.append(f'<div class="prof">{html.escape(p["persona"])}\nGoal: {html.escape(p["goal"])} — done when: {html.escape(p["done_when"])}\nHidden facts: {html.escape("; ".join(p["facts"]))}\nTemperament: {html.escape(p["temperament"])}' + (f'\nPlanned change of direction: {html.escape(p["change_of_plan"])}' if p.get('change_of_plan') else '') + '</div>')
    rote = {x['sentence'] for x in r.get('rote', [])}
    turns = {t['i']: t for t in r['turns']}; i = 0
    for m in r['messages']:
        if m['role'] == 'user':
            pt = turns.get(i - 1, {}) if i > 0 else {}; lab = 'user' + (f' · <span class="tag probe">PROBE {html.escape(pt["probe"])}</span>' if pt.get('probe') not in (None, 'none', '') else '') + (' · <span class="tag warn">CHANGE OF DIRECTION</span>' if pt.get('move') == 'change_request' else '') + (f' · <span class="tag">{html.escape(pt["move"])}</span>' if pt.get('move') and pt.get('move') not in ('change_request',) and pt.get('probe') in (None, 'none', '') else '')
            out.append(f'<div class="m u"><div class="lab">{lab}</div>{html.escape(m["content"])}</div>')
        else:
            t = turns.get(i, {}); flags = ''.join(f'<span class="tag warn">{f}</span>' for f in ('sentence reuse' if t.get('sentence_reuse') else '', 'near-identical' if t.get('near_identical') else '') if f)
            body = html.escape(m['content'])
            for rs in sorted(rote, key=len, reverse=True): body = body.replace(html.escape(rs), '<mark>' + html.escape(rs) + '</mark>')
            verdict = f' <span class="tag probe">self-check: {html.escape(t["self_check_verdict"])}</span>' if t.get('self_check_verdict') not in (None, 'na', '') else ''
            out.append(f'<div class="m a"><div class="lab">assistant · {t.get("n_words", "")} words {tag(t.get("assessment"))}{verdict}{flags}</div>{body}</div>'); i += 1
    if r.get('rote'): out.append('<div class="rote">ROTE sentences: ' + ' · '.join(f'<b>{html.escape(x["sentence"][:90])}</b> (turns {",".join(map(str, x["turns"]))}{", tic" if x.get("tic") else ""})' for x in r['rote']) + '</div>')
    out.append('</div>')
open(sys.argv[2], 'w').write('\n'.join(out)); print('page', sys.argv[2], len(rows), 'dialogues')
