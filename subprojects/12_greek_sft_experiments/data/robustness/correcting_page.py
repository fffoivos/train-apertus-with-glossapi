#!/usr/bin/env python3
"""Reader page for correcting-set dialogues: profile with the planned change, every turn with kind (ideal / planted [masked] / recovery / misquote recovery / closing),
the responder's assessment and probe verdict, and the typed-check outcome. Usage: python3 correcting_page.py <dialogues.jsonl> <out.html> [title] [max_dialogues]"""
import html, json, sys, random
rows = [json.loads(l) for l in open(sys.argv[1])]; title = sys.argv[3] if len(sys.argv) > 3 else 'Correcting Set Pilot'; k = int(sys.argv[4]) if len(sys.argv) > 4 else len(rows)
rows = random.Random(5).sample(rows, min(k, len(rows)))
CSS = f"""<title>{html.escape(title)}</title><style>
:root{{--bg:#f7f6f2;--ink:#1e1d1a;--muted:#6b675e;--rule:#dcd8cf;--card:#fffdf8;--user:#eef3f8;--asst:#f3f0e8;--masked:#f8e9e6;--ok:#2f7d4f;--bad:#b3402f;--warn:#a06a10;--acc:#3b5f8a}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#171613;--ink:#ece8df;--muted:#a49f93;--rule:#3a3730;--card:#211f1b;--user:#1e2a36;--asst:#2a2721;--masked:#3a2320;--ok:#6fc38f;--bad:#e2705c;--warn:#e0a94a;--acc:#8fb3dd}}}}
:root[data-theme="dark"]{{--bg:#171613;--ink:#ece8df;--muted:#a49f93;--rule:#3a3730;--card:#211f1b;--user:#1e2a36;--asst:#2a2721;--masked:#3a2320;--ok:#6fc38f;--bad:#e2705c;--warn:#e0a94a;--acc:#8fb3dd}}
body{{background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,"Helvetica Neue",Arial,sans-serif;margin:0;padding:24px}} h1{{font-size:22px;margin:0 0 4px}} .sub{{color:var(--muted);margin-bottom:20px;max-width:900px}}
.d{{background:var(--card);border:1px solid var(--rule);border-radius:8px;padding:16px;margin:0 0 20px;max-width:900px}} .meta{{font-size:13px;color:var(--muted);margin-bottom:8px}} .prof{{font-size:13px;border-left:3px solid var(--acc);padding:6px 10px;margin:8px 0 12px;white-space:pre-wrap}}
.m{{padding:8px 12px;border-radius:6px;margin:6px 0;white-space:pre-wrap}} .u{{background:var(--user)}} .a{{background:var(--asst)}} .x{{background:var(--masked);opacity:.85}} .lab{{font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);margin-bottom:2px}}
.tag{{display:inline-block;font-size:11px;padding:0 6px;border-radius:10px;border:1px solid var(--rule);margin-left:6px}} .ok{{color:var(--ok);border-color:var(--ok)}} .bad{{color:var(--bad);border-color:var(--bad)}} .warn{{color:var(--warn);border-color:var(--warn)}} .probe{{color:var(--acc);border-color:var(--acc)}}
</style>"""
out = [CSS, f'<h1>{html.escape(title)}</h1>', f'<div class="sub">{len(rows)} dialogues · every assistant turn written by the ideal writer (Sol high) except PLANTED turns (masked, never trained), which model a failure from the observed catalogue; MISQUOTE turns show the user quoting a text the assistant never wrote and the target correcting the record; badges: kind, the responder\'s assessment, probe verdicts, typed-check result</div>']
for r in rows:
    p = r['profile']; out.append(f'<div class="d"><div class="meta"><b>{html.escape(r["id"])}</b> · {html.escape(r["intent"][:60])} · {html.escape(r["surface"][:20])} · {html.escape(r["temperament"])} · {r["n_turns"]} turns · {html.escape(r["stop_reason"])} · plants {html.escape(", ".join(r["plants"]) or "none")} · verdicts {html.escape(json.dumps(r["verdicts"], ensure_ascii=False))}</div>')
    out.append(f'<div class="prof">{html.escape(p["persona"])}\nGoal: {html.escape(p["goal"])}\nHidden facts: {html.escape("; ".join(p["facts"]))}\nPlanned change: {html.escape(p.get("change_of_plan", ""))}</div>')
    turns = {t['i']: t for t in r['turns']}; i = 0
    for m in r['messages']:
        if m['role'] == 'user':
            pt = turns.get(i - 1, {}) if i > 0 else {}; lab = 'user' + (f' · <span class="tag probe">PROBE {html.escape(pt["probe"])}</span>' if pt.get('probe') not in (None, 'none', '') else '') + (' · <span class="tag warn">CHANGE OF DIRECTION</span>' if pt.get('move') == 'change_request' else '') + (' · <span class="tag bad">CONFRONTS</span>' if pt.get('assessment') == 'confronted' else '')
            out.append(f'<div class="m u"><div class="lab">{lab}</div>{html.escape(m["content"])}</div>'); continue
        t = turns.get(i, {}); kind = t.get('kind', ''); masked = not m.get('train', True); ck = t.get('checks', {}).get('ok')
        lab = ('assistant · <span class="tag bad">PLANTED, MASKED: ' + html.escape(kind.split(":")[-1]) + '</span>') if masked else ('assistant · <span class="tag ok">TARGET ' + html.escape(kind) + '</span>')
        lab += (f' <span class="tag {"ok" if ck else "bad"}">checks {"ok" if ck else "fail"}</span>' if ck is not None else '') + (f' <span class="tag">{html.escape(t["assessment"])}</span>' if t.get('assessment') else '') + (f' <span class="tag probe">self-check: {html.escape(t["self_check_verdict"])}</span>' if t.get('self_check_verdict') not in (None, 'na', '') else '')
        out.append(f'<div class="m {"x" if masked else "a"}"><div class="lab">{lab}</div>{html.escape(m["content"])}</div>'); i += 1
    out.append('</div>')
open(sys.argv[2], 'w').write('\n'.join(out)); print('page', sys.argv[2], len(rows))
