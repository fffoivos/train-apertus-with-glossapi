#!/usr/bin/env python3
"""Page for the gated forum prompts: per-forum stats, every selected prompt (rewrite + raw + kept details), a sample of rejections with reasons.
Usage: python3 data/rlhf/forum_pool_page.py <forum_pilot.jsonl> <receipt.json> <out.html> <gated.jsonl> [gated2.jsonl ...] [--rejected-per-forum 8]"""
import json, html, argparse, collections, random
ap = argparse.ArgumentParser(); ap.add_argument('selected'); ap.add_argument('receipt'); ap.add_argument('out'); ap.add_argument('gated', nargs='+'); ap.add_argument('--rejected-per-forum', type=int, default=8); a = ap.parse_args()
E = html.escape; sel = [json.loads(l) for l in open(a.selected)]; rec = json.load(open(a.receipt))
rej = collections.defaultdict(list)
for f in a.gated:
    for l in open(f):
        r = json.loads(l); g = r.get('gate')
        if g and not g['self_contained']: rej[r['forum']].append(r)
rng = random.Random(1); rej_sample = {f: rng.sample(v, min(len(v), a.rejected_per_forum)) for f, v in rej.items()}
forums = sorted({s['source'].split()[0] for s in sel}); kinds = sorted({s.get('task_type') or 'other' for s in sel})
stat_rows = ''.join(f"<tr><td>{E(f)}</td><td class='num'>{v.get('gated',0)}</td><td class='num'>{v.get('kind_declaration_or_announcement',0)+v.get('kind_advertisement',0)}</td><td class='num'>{v.get('rejected',0)}</td><td class='num'>{v.get('accepted',0)}</td><td class='num'>{v.get('kind_social',0)}</td><td class='num'>{v.get('false_premise',0)}</td><td class='num'>{v.get('selected',0)}</td></tr>" for f, v in sorted(rec['stats'].items()))
def card(s):
    forum = s['source'].split()[0]; url = s['source'].split()[1] if len(s['source'].split()) > 1 else ''
    kept = ''.join(f"<span class='kept'>{E(k)}</span>" for k in s.get('kept_details', [])[:8])
    fp = s.get('false_premise') or {}; fp_html = f"<div class='why'>false premise: {E(fp.get('what_el') or '')}</div>" if fp.get('present') else ''
    pk = f"<span class='kind pk'>{E(s.get('post_kind'))}</span>" if s.get('post_kind') else ''
    return (f"<article class='card' data-forum='{E(forum)}' data-kind='{E(s.get('task_type') or 'other')}'><div class='head'><span class='forum'>{E(forum)}</span>{pk}<span class='kind'>{E(s.get('task_type') or 'other')}</span>"
            f"<span class='words'>{len(s['messages'][0]['content'].split())} w ← {len(s.get('raw','').split())} w</span></div>"
            f"<div class='prompt'>{E(s['messages'][0]['content'])}</div>{fp_html}<div class='keptrow'>{kept}</div>"
            f"<details><summary>raw opening post</summary><div class='raw'>{E(s.get('raw',''))}</div>{('<div class=url>' + E(url) + '</div>') if url else ''}</details></article>")
def rcard(r):
    g = r['gate']; flags = ''.join(f"<span class='flag'>{E(k)}</span>" for k, v in g['flags'].items() if v)
    return f"<article class='card rej' data-forum='{E(r['forum'])}' data-kind='rejected'><div class='head'><span class='forum'>{E(r['forum'])}</span><span class='kind rejtag'>rejected</span>{flags}</div><div class='why'>{E(g['reason_el'])}</div><details><summary>raw opening post</summary><div class='raw'>{E(r['text'])}</div></details></article>"
cards = ''.join(card(s) for s in sel) + ''.join(rcard(r) for f in sorted(rej_sample) for r in rej_sample[f])
page = f'''<title>Greek Forum Prompts</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400&display=swap">
<style>
:root {{ --bg:#F4F6F8; --surface:#FFFFFF; --ink:#1B222E; --muted:#5B6674; --line:#D6DCE4; --accent:#1A6C8C; --accent-ink:#125066; --accent-soft:#E2EFF4; --warn:#9A5A10; --warn-soft:#F7ECDC; --good:#3D6B2E; --good-soft:#E5F0E0; --code-bg:#F0F3F6; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#11161C; --surface:#181E26; --ink:#E4E9F0; --muted:#98A3B2; --line:#2A333F; --accent:#63B4D0; --accent-ink:#8FCCE0; --accent-soft:#1B303B; --warn:#E2A65E; --warn-soft:#3A2A16; --good:#8FC77A; --good-soft:#1F2F1A; --code-bg:#0E1319; }} }}
:root[data-theme="dark"] {{ --bg:#11161C; --surface:#181E26; --ink:#E4E9F0; --muted:#98A3B2; --line:#2A333F; --accent:#63B4D0; --accent-ink:#8FCCE0; --accent-soft:#1B303B; --warn:#E2A65E; --warn-soft:#3A2A16; --good:#8FC77A; --good-soft:#1F2F1A; --code-bg:#0E1319; }}
* {{ box-sizing:border-box; }} body {{ background:var(--bg); color:var(--ink); font-family:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif; font-size:15px; line-height:1.5; padding-inline:clamp(16px,3vw,32px); padding-block:28px 64px; }}
.wrap {{ max-width:92ch; margin:0 auto; }} .eyebrow {{ font-size:12px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); font-weight:600; }} h1 {{ font-family:"Source Serif 4",Georgia,serif; font-weight:600; font-size:clamp(26px,3.5vw,34px); margin:6px 0 8px; }} .lede {{ color:var(--muted); max-width:72ch; margin:0 0 16px; }}
table {{ border-collapse:collapse; font-size:13.5px; background:var(--surface); border:1px solid var(--line); margin:0 0 20px; }} th,td {{ padding:6px 11px; border-bottom:1px solid var(--line); text-align:left; }} th {{ font-size:11.5px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); background:var(--bg); }} td.num,th.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
.filters {{ display:flex; flex-wrap:wrap; gap:8px 14px; align-items:center; margin:0 0 14px; font-size:14px; }} .filters select {{ font:inherit; padding:4px 8px; background:var(--surface); color:var(--ink); border:1px solid var(--line); }} .count {{ color:var(--muted); }}
.card {{ background:var(--surface); border:1px solid var(--line); padding:12px 14px; margin:0 0 10px; }} .card.rej {{ border-left:3px solid var(--warn); }} .card[hidden] {{ display:none; }}
.head {{ display:flex; flex-wrap:wrap; gap:6px 10px; align-items:center; margin-bottom:6px; }} .forum {{ font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:12px; color:var(--accent-ink); }} .kind {{ font-size:11px; letter-spacing:.05em; text-transform:uppercase; font-weight:600; background:var(--accent-soft); color:var(--accent-ink); padding:2px 7px; }} .kind.rejtag {{ background:var(--warn-soft); color:var(--warn); }} .kind.pk {{ background:var(--good-soft); color:var(--good); }} .flag {{ font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:var(--warn); }} .words {{ margin-left:auto; font-size:12px; color:var(--muted); font-variant-numeric:tabular-nums; }}
.prompt {{ font-size:15.5px; white-space:pre-wrap; margin:0 0 8px; }} .keptrow {{ display:flex; flex-wrap:wrap; gap:5px; margin:0 0 6px; }} .kept {{ font-size:12px; background:var(--good-soft); color:var(--good); padding:1px 7px; }} .why {{ color:var(--warn); margin:0 0 6px; }}
details summary {{ cursor:pointer; font-size:12.5px; color:var(--muted); }} .raw {{ white-space:pre-wrap; background:var(--code-bg); border:1px solid var(--line); padding:8px 10px; margin-top:6px; font-size:13.5px; color:var(--muted); }} .url {{ font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:11px; color:var(--muted); margin-top:4px; word-break:break-all; }}
</style>
<div class="wrap">
<div class="eyebrow">το Ελληνικό Apertus · RLHF round 1 · forum prompt pool · gate prompt data/rlhf/prompts/forum_gate_rewrite_el.txt</div>
<h1>Greek Forum Prompts</h1>
<p class="lede">Opening posts from 13 Greek forums, sampled uniformly among discussions with at least one reply, classified by post kind (announcements and advertisements dropped, requests and social posts kept), passed through the context gate (could a non-regular tell what is asked from the body alone?) and preserved as the poster's own message with only the forum mechanics removed — wording, spelling, hedges and the order of the poster's case kept (gate v3, the anthropological rule). Green chips are the details kept; a "false premise" line marks a wrong belief the answer must address; open "raw opening post" to compare. Orange cards are a sample of rejections with the gate's reason.</p>
<table><thead><tr><th>forum</th><th class="num">gated</th><th class="num">announcement / ad</th><th class="num">context rejected</th><th class="num">accepted</th><th class="num">of which social</th><th class="num">false premise</th><th class="num">selected</th></tr></thead><tbody>{stat_rows}</tbody></table>
<div class="filters"><label for="f-forum">forum</label><select id="f-forum"><option value="">all</option>{''.join(f'<option value="{E(f)}">{E(f)}</option>' for f in forums)}</select>
<label for="f-kind">show</label><select id="f-kind"><option value="">accepted, all types</option>{''.join(f'<option value="{E(k)}">{E(k)}</option>' for k in kinds)}<option value="rejected">rejected sample</option></select><span class="count" id="count"></span></div>
<div id="cards">{cards}</div>
</div>
<script>
(function(){{const f=document.getElementById('f-forum'),k=document.getElementById('f-kind'),c=document.getElementById('count'),cards=[...document.querySelectorAll('#cards .card')];
function apply(){{let n=0;for(const el of cards){{const okF=!f.value||el.dataset.forum===f.value;const kind=el.dataset.kind;const okK=k.value?kind===k.value:kind!=='rejected';el.hidden=!(okF&&okK);if(!el.hidden)n++;}}c.textContent=n+' shown';}}
f.addEventListener('change',apply);k.addEventListener('change',apply);try{{const s=JSON.parse(localStorage.getItem('forumpool')||'{{}}');if(s.f)f.value=s.f;if(s.k)k.value=s.k;}}catch(e){{}}apply();
for(const el of [f,k])el.addEventListener('change',()=>{{try{{localStorage.setItem('forumpool',JSON.stringify({{f:f.value,k:k.value}}))}}catch(e){{}}}});}})();
</script>'''
open(a.out, 'w').write(page); print('wrote', a.out, len(page), 'chars;', len(sel), 'selected cards +', sum(len(v) for v in rej_sample.values()), 'rejected cards')
