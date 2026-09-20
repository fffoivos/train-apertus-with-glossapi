#!/usr/bin/env python3
"""Render the generator-0.2 demo page: seed → imagined story → message, with a 0.1 prompt of the same task type for contrast."""
import json, html, sys, re
demo = json.load(open(sys.argv[1])); old = [json.loads(l) for l in open(sys.argv[2])]; out = sys.argv[3]
E = lambda s: html.escape(s or '')
def old_example(task):
    purpose = task.split(':')[0]
    cands = [r for r in old if r['purpose'] == purpose and r['language'] == 'el' and '{"source_' not in r['messages'][-1]['content']]
    return cands[hash(task) % len(cands)] if cands else None
cards = []
for it in demo['items']:
    s = it['seed']; o = old_example(s['task'])
    chips = ''.join(f"<span class='chip'><b>{E(k)}</b>{E(str(s[k]))}</span>" for k in ('person', 'situation', 'topic', 'specific', 'detail') if k in s)
    meta = f"<span class='chip tone'>{E(s['register'])}</span><span class='chip tone'>{E(s['attitude'])}</span><span class='chip tone'>{E(s['language'])}</span>"
    oldblk = (f"<details class='old'><summary>Generator 0.1 prompt of the same task type ({E(o['id'])}, family {E(o['family'])})</summary>"
              f"<pre>{E(o['messages'][-1]['content'])}</pre></details>") if o else ''
    cards.append(f"""<article class='card'>
  <header><span class='id'>{E(s['id'])}</span><span class='task'>{E(s['task'])}</span></header>
  <div class='cols'>
    <div class='seed'><h3>Seed</h3><div class='chips'>{chips}</div><div class='chips'>{meta}</div>
      <details class='story' open><summary>Imagined person (private, not shown to the model)</summary><p>{E(it['story'])}</p></details></div>
    <div class='msg'><h3>What they type</h3><pre>{E(it['message'])}</pre></div>
  </div>{oldblk}</article>""")
ax = ', '.join(f"{k} {v}" for k, v in demo['axes_sizes'].items())
page = f"""<title>Prompt Generator 0.2 Demo</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;600;700&family=Noto+Serif:ital,wght@0,400;0,600;1,400&display=swap">
<style>
:root{{--bg:#f2f4f6;--surface:#ffffff;--ink:#1b2430;--muted:#5d6878;--line:#d9dee5;--accent:#0f6e74;--accent-ink:#ffffff;--chip:#e7eef0;--story:#f6f1e6;--old:#eceef1}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#12161b;--surface:#1a2028;--ink:#e6eaef;--muted:#9aa5b4;--line:#2b3441;--accent:#4fb3b9;--accent-ink:#0e1418;--chip:#232c37;--story:#2a2620;--old:#1f252d}}}}
:root[data-theme="dark"]{{--bg:#12161b;--surface:#1a2028;--ink:#e6eaef;--muted:#9aa5b4;--line:#2b3441;--accent:#4fb3b9;--accent-ink:#0e1418;--chip:#232c37;--story:#2a2620;--old:#1f252d}}
body{{background:var(--bg);color:var(--ink);font-family:"Noto Sans",system-ui,sans-serif;padding-block:32px;padding-inline:20px;line-height:1.5}}
main{{max-width:1080px;margin:0 auto;display:grid;gap:22px}}
h1{{font-family:"Noto Serif",Georgia,serif;font-size:1.9rem;margin:0 0 6px;text-wrap:balance}}
.lede{{color:var(--muted);max-width:70ch;margin:0}}
.flow{{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}}
.flow span{{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:6px 10px;font-size:.9rem}}
.flow span b{{color:var(--accent)}}
.card{{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:18px 20px;display:grid;gap:14px}}
.card header{{display:flex;gap:12px;align-items:baseline;flex-wrap:wrap}}
.id{{font-weight:700;color:var(--accent);letter-spacing:.04em}}
.task{{color:var(--muted);font-size:.95rem}}
.cols{{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:18px}}
@media (max-width:760px){{.cols{{grid-template-columns:1fr}}}}
h3{{font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:0 0 8px}}
.chips{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}}
.chip{{background:var(--chip);border-radius:6px;padding:4px 8px;font-size:.85rem}}
.chip b{{display:block;font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:600}}
.chip.tone{{color:var(--accent);font-weight:600}}
.story{{background:var(--story);border-radius:8px;padding:10px 12px;font-size:.92rem}}
.story summary{{cursor:pointer;font-weight:600;font-size:.85rem}}
.story p{{margin:8px 0 0}}
.msg pre,.old pre{{white-space:pre-wrap;word-wrap:break-word;font-family:"Noto Serif",Georgia,serif;font-size:1rem;line-height:1.6;margin:0;background:var(--bg);border-left:3px solid var(--accent);padding:12px 14px;border-radius:0 8px 8px 0}}
.old{{background:var(--old);border-radius:8px;padding:8px 12px}}
.old summary{{cursor:pointer;font-size:.85rem;color:var(--muted)}}
.old pre{{border-left-color:var(--muted);font-size:.92rem;margin-top:8px;opacity:.9}}
footer{{color:var(--muted);font-size:.85rem}}
</style>
<main>
<div><h1>Prompt Generator 0.2 Demo</h1>
<p class='lede'>Twelve prompts written by Sol from high-entropy seeds. The seed fixes who is asking, why now, the task type, and how much detail the person gives (bare 30%, terse 20%, short 20%, medium 20%, detailed 5%, rambling 5%). The imagined story stays private; names and backstory surface only at the detailed levels; it does not constrain the wording. Sol first imagines the person and their story, then writes exactly what that person would type, including anything they would paste. No framing text, no attachments by software.</p>
<div class='flow'><span><b>1</b> seed = person × situation × task × topic × specifics × register × attitude</span><span><b>2</b> Sol imagines the person (private)</span><span><b>3</b> Sol writes the message in their voice</span></div>
<p class='lede' style='margin-top:10px'>Demo axes ({E(ax)}) in one call, effort high. Production needs hundreds of values per axis plus a near-duplicate screen. Each card ends with a 0.1 prompt of the same task type for contrast.</p></div>
{''.join(cards)}
<footer>Seed {demo['seed']} · Sol prompt sha16 {E(demo['prompt_sha16'])} · data/rlhf/gen02_demo/demo_v1.json</footer>
</main>"""
open(out, 'w').write(page); print('wrote', out, len(page), 'chars')
