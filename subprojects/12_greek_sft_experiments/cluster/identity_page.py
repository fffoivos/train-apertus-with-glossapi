#!/usr/bin/env python3
"""Identity/vantage probe reader: the same 40 prompts answered by two checkpoints, side by side, grouped by category.
Usage: python3 identity_page.py <out.html> <label1> <identity40_gen.jsonl> [<label2> <file2> ...]   (2 to 4 columns)"""
import json, sys, html
OUT = sys.argv[1]; pairs = sys.argv[2:]; assert len(pairs) % 2 == 0 and 2 <= len(pairs) // 2 <= 4
LABELS = pairs[0::2]; FILES = pairs[1::2]
e = lambda s: html.escape(str(s if s is not None else ''))
def load(p): return {r['prompt_id']: r for r in (json.loads(l) for l in open(p))}
COLS = [load(f) for f in FILES]; L = COLS[0]; LL, RL = LABELS[0], LABELS[-1]
CAT = {'id': 'Who am I, limits', 'press': 'Identity under pressure', 'vantage': 'Greek vantage', 'practical': 'Practical', 'register': 'Register', 'refusal': 'Refusals', 'sensitive': 'Sensitive topics'}
def answer(r):
    if not r: return '<p class="muted">missing</p>'
    t = r.get('text') or ''; t = t.replace('<|assistant_end|>', '')
    stop = r.get('stop_reason', ''); return f'<div class="a">{e(t)}</div><div class="meta">{e(stop)} · {r.get("generated_tokens", "?")} tokens</div>'
groups = {}
for pid, r in L.items(): groups.setdefault(r['category'].split(':')[1], []).append(pid)
body = ''
for cat in ['id', 'press', 'vantage', 'practical', 'register', 'refusal', 'sensitive']:
    pids = sorted(groups.get(cat, []))
    if not pids: continue
    body += f'<h2>{e(CAT.get(cat, cat))} <span class="n">{len(pids)}</span></h2>'
    for pid in pids:
        q = L[pid]['messages'][0]['content']
        secs = ''.join(f'<section><h4>{e(lab)}</h4>{answer(col.get(pid))}</section>' for lab, col in zip(LABELS, COLS))
        body += f'<article><p class="q">{e(q)}</p><div class="cols" style="grid-template-columns:repeat({len(COLS)},1fr)">{secs}</div></article>'
page = f'''<title>Identity Probe: {e(LL)} vs {e(RL)}</title>
<style>
:root{{--bg:#F4F6F8;--ink:#14202B;--accent:#0E5C8F;--muted:#5B6B78;--rule:#D5DCE3;--panel:#FFFFFF;--tint:#E9EFF4}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#0F151B;--ink:#E4E9EE;--accent:#6FB1E3;--muted:#98A6B3;--rule:#28323C;--panel:#161E26;--tint:#1C2630}}}}
:root[data-theme="dark"]{{--bg:#0F151B;--ink:#E4E9EE;--accent:#6FB1E3;--muted:#98A6B3;--rule:#28323C;--panel:#161E26;--tint:#1C2630}}
body{{background:var(--bg);color:var(--ink);font-family:"Source Sans 3","Segoe UI",Roboto,Arial,sans-serif;font-size:16px;line-height:1.5;margin:0}} main{{max-width:1180px;margin:0 auto;padding:2rem 1.2rem 4rem}}
h1{{font-family:Literata,Georgia,serif;font-size:1.8rem;margin:0 0 .3rem}} h2{{font-family:Literata,Georgia,serif;font-weight:500;font-size:1.3rem;margin:2rem 0 .6rem;padding-top:.8rem;border-top:1px solid var(--rule)}} h4{{margin:0 0 .4rem;font-size:.8rem;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}}
.n{{font-family:ui-monospace,Menlo,monospace;font-size:.85rem;color:var(--muted)}} .muted{{color:var(--muted)}}
article{{background:var(--panel);border:1px solid var(--rule);border-radius:4px;padding:.8rem 1rem;margin:.8rem 0}} .q{{font-weight:600;margin:0 0 .6rem}}
.cols{{display:grid;gap:1rem}} @media (max-width:900px){{.cols{{grid-template-columns:1fr !important}}}}
.a{{white-space:pre-wrap;background:var(--tint);padding:.5rem .7rem;border-radius:3px;font-size:.95rem}} .meta{{font-family:ui-monospace,Menlo,monospace;font-size:.75rem;color:var(--muted);margin-top:.3rem}}
</style>
<main><h1>Identity and vantage probe: {e(" · ".join(LABELS))}</h1>
<p class="muted">Forty fixed Greek prompts, greedy decoding, 512-token cap, no system prompt. One column per checkpoint, left to right in training order.</p>
{body}</main>'''
open(OUT, 'w').write(page); print(OUT, len(L), 'prompts')
