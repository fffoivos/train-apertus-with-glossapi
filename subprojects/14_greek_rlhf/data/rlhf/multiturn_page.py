#!/usr/bin/env python3
"""Page: the Greek multi-turn rows of the SFT manifest (1-G4F6P1) — what the model was trained on for conversations.
Usage: python3 data/rlhf/multiturn_page.py <samples.json> <out.html>"""
import json, html, sys, collections
E = html.escape; groups = json.load(open(sys.argv[1]))
COUNTS = [('convskills_v2 S1', 631, 'conversation as an object: quote turn N, count my questions, list my requests, what did I ask first — transcripts assembled from existing rows, targets derived mechanically, phrased by Sol; mean 11 turns'),
          ('convskills_v2 S2', 461, 'standing instructions kept over 5–12 turns, then revoked — seven checkable instruction types, content chosen to tempt breaking them'),
          ('convskills_v2 S3', 408, 'edit my previous answer: shorter, without X, one item, list ↔ prose, for a child — target computed then polished'),
          ('convskills_v2 S3c', 182, 'chained edits: shorter then without X, or the reverse; mean 6 turns'),
          ('greek_ours', 5103, 'adapted open sources with a second user turn (everyday 1,688 · apertus 1,259 · oasst 1,239 · no_robots 522 · systemchats 352 · euroblocks 43); mostly two short turns'),
          ('personality', 339, 'identity under pressure and register: the user pushes, the model keeps the settled facts and the format')]
order = [k for k, _, _ in COUNTS]; total = sum(n for _, n, _ in COUNTS)
def dialogue(d):
    msgs = ''.join(f"<div class='msg {m['role']}'><span class='role'>{E(m['role'])}</span><div>{E(m['content'])}</div></div>" for m in d['messages'])
    return f"<details class='card' data-group='{E(d['key'])}'><summary><span class='pid'>{E(d['id'])}</span><span class='grp'>{E(d['key'])}</span><span class='muted'>{sum(1 for m in d['messages'] if m['role']=='assistant')} assistant turns</span></summary><div class='conv'>{msgs}</div></details>"
cards = ''.join(dialogue(d) for k in order for d in groups.get(k, []))
rows = ''.join(f"<tr><td>{E(k)}</td><td class='num'>{n:,}</td><td>{E(t)}</td></tr>" for k, n, t in COUNTS)
page = f'''<title>Greek Multi-turn SFT Rows</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400&display=swap">
<style>
:root {{ --bg:#F4F6F8; --surface:#FFFFFF; --ink:#1B222E; --muted:#5B6674; --line:#D6DCE4; --accent:#1A6C8C; --accent-ink:#125066; --accent-soft:#E2EFF4; --user:#EEF3F7; --asst:#F7F5EE; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#11161C; --surface:#181E26; --ink:#E4E9F0; --muted:#98A3B2; --line:#2A333F; --accent:#63B4D0; --accent-ink:#8FCCE0; --accent-soft:#1B303B; --user:#1C2632; --asst:#26241C; }} }}
:root[data-theme="dark"] {{ --bg:#11161C; --surface:#181E26; --ink:#E4E9F0; --muted:#98A3B2; --line:#2A333F; --accent:#63B4D0; --accent-ink:#8FCCE0; --accent-soft:#1B303B; --user:#1C2632; --asst:#26241C; }}
* {{ box-sizing:border-box; }} body {{ background:var(--bg); color:var(--ink); font-family:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif; font-size:15px; line-height:1.5; padding-inline:clamp(16px,3vw,32px); padding-block:28px 64px; }}
.wrap {{ max-width:92ch; margin:0 auto; }} .eyebrow {{ font-size:12px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); font-weight:600; }} h1 {{ font-family:"Source Serif 4",Georgia,serif; font-weight:600; font-size:clamp(26px,3.5vw,34px); margin:6px 0 8px; }} .lede {{ color:var(--muted); max-width:72ch; margin:0 0 16px; }}
table {{ border-collapse:collapse; font-size:13.5px; background:var(--surface); border:1px solid var(--line); margin:0 0 18px; width:100%; }} th,td {{ padding:7px 11px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }} th {{ font-size:11.5px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); background:var(--bg); }} td.num {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
.filters {{ display:flex; flex-wrap:wrap; gap:8px 14px; align-items:center; margin:0 0 12px; font-size:14px; }} select {{ font:inherit; padding:4px 8px; background:var(--surface); color:var(--ink); border:1px solid var(--line); }}
.card {{ background:var(--surface); border:1px solid var(--line); margin:0 0 8px; }} .card[hidden] {{ display:none; }} .card > summary {{ cursor:pointer; padding:9px 14px; display:flex; flex-wrap:wrap; gap:6px 12px; align-items:baseline; list-style:none; }} .card > summary::-webkit-details-marker {{ display:none; }} .card[open] > summary {{ background:var(--accent-soft); border-bottom:1px solid var(--line); }}
.pid {{ font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:12px; color:var(--accent-ink); }} .grp {{ font-size:11px; text-transform:uppercase; letter-spacing:.05em; font-weight:600; color:var(--muted); }} .muted {{ color:var(--muted); font-size:12.5px; }}
.conv {{ padding:10px 14px; display:grid; gap:8px; }} .msg {{ display:grid; grid-template-columns:72px 1fr; gap:10px; padding:8px 10px; border:1px solid var(--line); white-space:pre-wrap; }} .msg.user {{ background:var(--user); }} .msg.assistant {{ background:var(--asst); }} .msg.system {{ background:var(--bg); color:var(--muted); }} .msg .role {{ font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); font-weight:600; }}
@media (max-width:560px) {{ .msg {{ grid-template-columns:1fr; }} }}
</style>
<div class="wrap">
<div class="eyebrow">το Ελληνικό Apertus · SFT manifest 1-G4F6P1 (16 Sept 2026) · Greek rows with two or more assistant turns</div>
<h1>Greek Multi-turn SFT Rows</h1>
<p class="lede">What the model was trained on for conversations in Greek: {total:,} unique rows with at least two assistant turns (replay copies not counted), out of 384,010 rows in the manifest. The conversation-skills suite v2 is the only block built for dialogue behaviour; the correcting set (owning an error) was left out of this pass. Below, {sum(len(v) for v in groups.values())} dialogues drawn at random, full text.</p>
<table><thead><tr><th>block · lane</th><th class="num">unique rows</th><th>what it teaches</th></tr></thead><tbody>{rows}</tbody></table>
<div class="filters"><label for="g">group</label><select id="g"><option value="">all</option>{''.join(f'<option value="{E(k)}">{E(k)}</option>' for k in order)}</select><span class="muted" id="count"></span></div>
<div id="cards">{cards}</div>
</div>
<script>(function(){{const g=document.getElementById('g'),c=document.getElementById('count'),cards=[...document.querySelectorAll('#cards .card')];function apply(){{let n=0;for(const el of cards){{el.hidden=!!g.value&&el.dataset.group!==g.value;if(!el.hidden)n++;}}c.textContent=n+' shown';}}g.addEventListener('change',apply);apply();}})();</script>'''
open(sys.argv[2], 'w').write(page); print('wrote', sys.argv[2], len(page), 'chars')
