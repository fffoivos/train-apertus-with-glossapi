#!/usr/bin/env python3
"""Render the RLHF grader pilot as a page: every prompt, its candidates in judged order, disqualifiers, scores, reasons.
Usage: python3 data/rlhf/pilot_page.py <prompts.jsonl> <samples.jsonl> <judged.jsonl> <out.html> [--mapping standin_mapping.json] [--title ...] [--note ...] [--samples2 samples_batch2.jsonl --judged2 judged2.jsonl]
With --samples2/--judged2 each card shows two groups, samples 1-4 and samples 5-8, each in its own judge order."""
import json, html, argparse, collections, statistics, sys
ap = argparse.ArgumentParser(); ap.add_argument('prompts'); ap.add_argument('samples'); ap.add_argument('judged'); ap.add_argument('out')
ap.add_argument('--mapping', default=None); ap.add_argument('--title', default='Greek RLHF Pilot Ratings'); ap.add_argument('--note', default='')
ap.add_argument('--samples2', default=None, help='second batch of samples (the 5th-8th) for the same prompt ids'); ap.add_argument('--judged2', default=None, help='judged file for the second batch'); a = ap.parse_args()
P = {json.loads(l)['id']: json.loads(l) for l in open(a.prompts) if l.strip()}
S = collections.defaultdict(dict)
for l in open(a.samples):
    if l.strip():
        s = json.loads(l)
        if s.get('k', -1) >= 0: S[s['id']][s['k']] = s
J = [json.loads(l) for l in open(a.judged) if l.strip()]; M = json.load(open(a.mapping)) if a.mapping else {}
S2 = collections.defaultdict(dict)
if a.samples2:
    for l in open(a.samples2):
        if l.strip():
            s = json.loads(l)
            if s.get('k', -1) >= 0: S2[s['id']][s['k']] = s
J2 = [json.loads(l) for l in open(a.judged2) if l.strip()] if a.judged2 else []
second_batch = {j['id']: j for j in J2 if not j.get('error') and j.get('pass', 1) == 1}
TWO = bool(a.samples2 and a.judged2)
first = {}; second = {}
for j in J:
    if j.get('error'): continue
    (first if j['pass'] == 1 else second)[j['id']] = j
E = html.escape
def label(pid, k): return M.get(pid, {}).get(str(k), f'sample {k+1}')
# summary
ok = list(first.values()); errs = [j for j in J if j.get('error')]
rank_by = collections.defaultdict(list); dq = collections.Counter(); qsum = collections.defaultdict(list)
for j in ok:
    for pos, k in enumerate(j['ranking_k']): rank_by[label(j['id'], k)].append(pos + 1)
    for k, c in j['by_k'].items():
        if 'scores' in c:
            for d in c['disqualifiers']: dq[d] += 1
            qsum[label(j['id'], int(k))].append(sum(c['scores'].values()))
        else:
            if c.get('unusable'): dq['unusable'] += 1
            qsum[label(j['id'], int(k))].append(4 - j['ranking_k'].index(int(k)))
agree = sum(1 for pid in second if pid in first and first[pid]['ranking_k'][0] == second[pid]['ranking_k'][0]); n2 = sum(1 for pid in second if pid in first)
has_v = any(c.get('verdict') for j in ok for c in j['by_k'].values())
if has_v:
    npos = sum(1 for j in ok if any(c.get('verdict') == 'reinforce' for c in j['by_k'].values())); npair = sum(1 for j in ok if any(c.get('verdict') == 'reinforce' for c in j['by_k'].values()) and any(c.get('verdict') == 'discourage' for c in j['by_k'].values()))
def _vd(j): return [c.get('verdict') for c in j['by_k'].values()]
tiles8 = []
if TWO and has_v:
    allv = {pid: _vd(first[pid]) + (_vd(second_batch[pid]) if pid in second_batch else []) for pid in first}
    ext = [pid for pid in allv if pid in second_batch]
    pos8 = sum(1 for v in allv.values() if 'reinforce' in v); pair8 = sum(1 for v in allv.values() if 'reinforce' in v and 'discourage' in v)
    tiles8 = [('positives after 8 samples', f'{pos8}/{len(ok)}', f'{len(ext)} prompts resampled'), ('real pairs after 8 samples', f'{pair8}/{len(ok)}', 'reinforce + discourage anywhere')]
tiles = tiles8 + ([('prompts with a reply worth reinforcing', f'{npos}/{len(ok)}', 'absolute verdict, not rank'), ('real pairs (reinforce + discourage)', f'{npair}/{len(ok)}', 'the DPO yield')] if has_v else []) + [('prompts judged', str(len(ok)), f'{len(errs)} errors'), ('median seconds per call', f"{statistics.median(j['secs'] for j in ok):.0f}" if ok else '—', 'Sol, medium effort'),
         ('same best on re-judge', f'{agree}/{n2}' if n2 else '—', 'shuffled order'), ('disqualified / unusable', str(sum(dq.values())), ' · '.join(f'{k} {v}' for k, v in sorted(dq.items())) or 'none')]
V2 = any('scores' not in c for j in ok for c in j['by_k'].values())
rank_rows = ''.join(f"<tr><td>{E(m)}</td><td class='num'>{statistics.mean(v):.2f}</td><td class='num'>{statistics.mean(qsum[m]):.1f}</td><td class='num'>{len(v)}</td></tr>" for m, v in sorted(rank_by.items(), key=lambda x: statistics.mean(x[1])))
QN = {'Q1': 'reasoning', 'Q2': 'explicit', 'Q3': 'complete', 'Q4': 'language', 'Q5': 'attitude', 'Q6': 'pushback', 'Q7': 'format'}
def jmeta(j):
    v = j['verdict']; s = f"margin {v['margin_best_worst']}" if 'margin_best_worst' in v else ''
    if v.get('ties'): s += f" · ties {E(str(v['ties']))}"
    if 'confidence' in v: s += f" · gap {E(v.get('best_vs_worst',''))} · confidence {E(v.get('confidence',''))}"
    return s
def cand_block(pid, j, SRC, koff=0):
    """Candidates of one judged row, in judge order; koff shifts the sample numbering (4 = the 5th-8th samples)."""
    heads = []; out = []
    for pos, k in enumerate(j['ranking_k']):
        c = j['by_k'][str(k)]; lab = f'sample {k + 1 + koff}' if koff else label(pid, k)
        if 'scores' in c:
            tags = ''.join(f"<span class='tag warn'>{E(d)}</span>" for d in c['disqualifiers']); bad = bool(c['disqualifiers'])
            scores = ''.join(f"<span class='sc' title='{QN[q]}'>{q}<b>{c['scores'][q]}</b></span>" for q in QN) + f"<span class='sc total'>Σ<b>{sum(c['scores'].values())}</b></span>"; reason = c['reason']
        else:
            bad = bool(c.get('unusable')); vd = c.get('verdict')
            tags = ("<span class='tag warn'>unusable</span>" if bad else '') + (f"<span class='tag {'good' if vd == 'reinforce' else ('warn' if vd == 'discourage' else 'neutral')}'>{E(vd)}</span>" if vd else '') + ''.join(f"<span class='tag issue'>{E(x)}</span>" for x in (c.get('issues') or []))
            scores = ''; reason = c.get('note', '')
        heads.append(f"{pos+1}. {E(lab)}" + (' ✗' if bad else ''))
        text = SRC[pid].get(k, {}).get('text', '(missing)')
        out.append(f"<div class='cand'><div class='cand-head'><span class='pos'>{pos+1}</span><span class='lab'>{E(lab)}</span>{tags}<span class='scores'>{scores}</span></div><div class='reason'>{E(reason)}</div><pre class='text'>{E(text)}</pre></div>")
    return heads, ''.join(out)
cards = []
for pid, p in P.items():
    j = first.get(pid); j2 = second_batch.get(pid) if TWO else None
    conv = ''.join(f"<div class='msg {m['role']}'><span class='role'>{m['role']}</span><div>{E(m['content'])}</div></div>" for m in p['messages'])
    meta = ' · '.join(E(f'{k}: {v}') for k, v in p.items() if k in ('label', 'expected', 'level', 'profile', 'move') and v)
    if not j:
        cards.append(f"<details class='card'><summary><span class='pid'>{E(pid)}</span> <span class='slice'>{E(p['slice'])}</span> <span class='muted'>not judged</span></summary><div class='conv'>{conv}</div></details>"); continue
    heads, body = cand_block(pid, j, S, 0)
    if j2:
        heads2, body2 = cand_block(pid, j2, S2, 4)
        body = (f"<div class='ghead'>samples 1–4 <span class='muted'>{jmeta(j)}</span></div>" + body
                + f"<div class='ghead'>samples 5–8 <span class='muted'>{jmeta(j2)}</span></div>" + body2)
        rank = f"1–4: {' → '.join(heads)} ‖ 5–8: {' → '.join(heads2)}"
    else:
        rank = ' → '.join(heads)
    rj = f" · re-judge best: {E(label(pid, second[pid]['ranking_k'][0]))}" if pid in second else ''
    tail = ('' if j2 else jmeta(j)) + rj
    cards.append(f"<details class='card'><summary><span class='pid'>{E(pid)}</span> <span class='slice'>{E(p['slice'])}</span> <span class='rank'>{rank}</span> <span class='muted'>{tail}</span></summary><div class='meta'>{E(p.get('source',''))}{(' · ' + meta) if meta else ''}</div><div class='conv'>{conv}</div>{body}</details>")
page = f'''<title>{E(a.title)}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400&display=swap">
<style>
:root {{ --bg:#F4F6F8; --surface:#FFFFFF; --ink:#1B222E; --muted:#5B6674; --line:#D6DCE4; --line-strong:#B9C2CE; --accent:#1A6C8C; --accent-ink:#125066; --accent-soft:#E2EFF4; --warn:#9A5A10; --warn-soft:#F7ECDC; --good:#3D6B2E; --good-soft:#E5F0E0; --code-bg:#F0F3F6; --user:#EEF3F7; --asst:#F7F5EE; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#11161C; --surface:#181E26; --ink:#E4E9F0; --muted:#98A3B2; --line:#2A333F; --line-strong:#3A4553; --accent:#63B4D0; --accent-ink:#8FCCE0; --accent-soft:#1B303B; --warn:#E2A65E; --warn-soft:#3A2A16; --good:#8FC77A; --good-soft:#1F2F1A; --code-bg:#0E1319; --user:#1C2632; --asst:#26241C; }} }}
:root[data-theme="dark"] {{ --bg:#11161C; --surface:#181E26; --ink:#E4E9F0; --muted:#98A3B2; --line:#2A333F; --line-strong:#3A4553; --accent:#63B4D0; --accent-ink:#8FCCE0; --accent-soft:#1B303B; --warn:#E2A65E; --warn-soft:#3A2A16; --good:#8FC77A; --good-soft:#1F2F1A; --code-bg:#0E1319; --user:#1C2632; --asst:#26241C; }}
* {{ box-sizing:border-box; }} body {{ background:var(--bg); color:var(--ink); font-family:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif; font-size:15px; line-height:1.5; padding-inline:clamp(16px,3vw,32px); padding-block:28px 64px; }}
.wrap {{ max-width:96ch; margin:0 auto; }} h1 {{ font-family:"Source Serif 4",Georgia,serif; font-weight:600; font-size:clamp(26px,3.5vw,34px); margin:6px 0 8px; text-wrap:balance; }}
.eyebrow {{ font-size:12px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); font-weight:600; }} .lede {{ color:var(--muted); max-width:70ch; margin:0 0 18px; }}
.note {{ background:var(--warn-soft); color:var(--warn); border:1px solid var(--line); padding:10px 14px; margin:0 0 18px; font-size:14px; max-width:80ch; }}
.facts {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:1px; background:var(--line); border:1px solid var(--line); margin:0 0 18px; }} .fact {{ background:var(--surface); padding:12px 14px; }} .fact .k {{ font-size:12px; color:var(--muted); text-transform:uppercase; letter-spacing:.04em; }} .fact .v {{ font-family:"Source Serif 4",Georgia,serif; font-size:24px; font-weight:600; font-variant-numeric:tabular-nums; }} .fact .s {{ font-size:12.5px; color:var(--muted); }}
table {{ border-collapse:collapse; font-size:14px; background:var(--surface); border:1px solid var(--line); margin:0 0 24px; }} th,td {{ padding:7px 12px; border-bottom:1px solid var(--line); text-align:left; }} th {{ font-size:12px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); background:var(--bg); }} td.num,th.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
h2 {{ font-family:"Source Serif 4",Georgia,serif; font-weight:600; font-size:22px; margin:28px 0 10px; }}
.card {{ background:var(--surface); border:1px solid var(--line); margin:0 0 10px; }} .card > summary {{ cursor:pointer; padding:10px 14px; display:flex; flex-wrap:wrap; gap:6px 12px; align-items:baseline; list-style:none; }} .card > summary::-webkit-details-marker {{ display:none; }} .card[open] > summary {{ border-bottom:1px solid var(--line); background:var(--accent-soft); }}
.pid {{ font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:12.5px; color:var(--accent-ink); }} .slice {{ font-size:12px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); font-weight:600; }} .rank {{ font-size:14px; }} .muted {{ color:var(--muted); font-size:13px; }}
.meta {{ font-size:12.5px; color:var(--muted); padding:8px 14px 0; }} .conv {{ padding:10px 14px; display:grid; gap:8px; }} .msg {{ display:grid; grid-template-columns:70px 1fr; gap:10px; padding:8px 10px; border:1px solid var(--line); white-space:pre-wrap; }} .msg.user {{ background:var(--user); }} .msg.assistant {{ background:var(--asst); }} .msg .role {{ font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); font-weight:600; }}
.cand {{ border-top:1px solid var(--line); padding:10px 14px; }} .cand-head {{ display:flex; flex-wrap:wrap; gap:6px 10px; align-items:center; }} .pos {{ font-family:"Source Serif 4",Georgia,serif; font-weight:600; color:var(--accent-ink); font-size:18px; width:22px; }} .lab {{ font-weight:600; }}
.tag {{ font-size:11px; letter-spacing:.05em; text-transform:uppercase; font-weight:600; padding:2px 7px; border-radius:2px; }} .tag.warn {{ background:var(--warn-soft); color:var(--warn); }} .tag.good {{ background:var(--good-soft); color:var(--good); }} .tag.neutral {{ background:var(--code-bg); color:var(--muted); }} .tag.issue {{ background:var(--code-bg); color:var(--muted); border:1px solid var(--line); text-transform:none; letter-spacing:0; font-weight:500; font-size:10.5px; }}
.ghead {{ border-top:1px solid var(--line-strong); background:var(--bg); padding:6px 14px; font-size:12px; text-transform:uppercase; letter-spacing:.05em; font-weight:600; color:var(--accent-ink); }}
.scores {{ margin-left:auto; display:flex; gap:6px; flex-wrap:wrap; }} .sc {{ font-size:12px; color:var(--muted); font-variant-numeric:tabular-nums; }} .sc b {{ color:var(--ink); margin-left:2px; }} .sc.total b {{ color:var(--accent-ink); }}
.reason {{ font-size:13.5px; color:var(--muted); margin:6px 0 6px 32px; max-width:90ch; }} pre.text {{ margin:0 0 0 32px; background:var(--code-bg); border:1px solid var(--line); padding:10px 12px; white-space:pre-wrap; font-family:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif; font-size:13.5px; max-height:40vh; overflow:auto; }}
@media (max-width:560px) {{ .msg {{ grid-template-columns:1fr; }} .reason, pre.text {{ margin-left:0; }} }}
</style>
<div class="wrap">
<div class="eyebrow">το Ελληνικό Apertus · RLHF grader pilot · rubric sha {ok[0]["rubric_sha"] if ok else "—"}</div>
<h1>{E(a.title)}</h1>
<p class="lede">Every prompt, its candidates in the order the judge ranked them, which ones it called unusable, and its rationale for each. {'Rubric v2: preferences described, no scoring formula; the table\'s second column is the mean position score (4 = ranked first).' if V2 else 'Rubric v1 with seven scores.'} Open a card to read.</p>
{('<div class="note">' + E(a.note) + '</div>') if a.note else ''}
<div class="facts">{''.join(f"<div class='fact'><div class='k'>{E(k)}</div><div class='v'>{E(v)}</div><div class='s'>{E(s)}</div></div>" for k, v, s in tiles)}</div>
<table><thead><tr><th>candidate</th><th class="num">mean rank (1 best)</th><th class="num">{'mean position score (4 = first)' if V2 else 'mean Σ scores (35)'}</th><th class="num">n</th></tr></thead><tbody>{rank_rows}</tbody></table>
<h2>Prompts</h2>
{''.join(cards)}
</div>'''
open(a.out, 'w').write(page); print('wrote', a.out, len(page), 'chars,', len(cards), 'cards')
