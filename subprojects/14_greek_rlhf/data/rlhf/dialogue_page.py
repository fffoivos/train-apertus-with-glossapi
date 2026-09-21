#!/usr/bin/env python3
"""Render the dialogue pilot page: distribution of the turn at which the first serious error was detected, quality by depth,
and every measurement chat with per-turn severity, Sol's evidence, selected prefixes and exported pairs.
Usage: python3 dialogue_page.py <dqd runtime dir> <out.html>"""
import json, html, sys, collections, pathlib
RT = pathlib.Path(sys.argv[1]); out = sys.argv[2]; E = lambda s: html.escape(str(s if s is not None else ''))
TITLE = sys.argv[3] if len(sys.argv) > 3 else 'Where the Chats Break'
LEDE = sys.argv[4] if len(sys.argv) > 4 else None
FOOT = sys.argv[5] if len(sys.argv) > 5 else 'Root review changed 1 of 94 labels; boundary set stable.'
J = lambda p: [json.loads(l) for l in open(p) if l.strip()]
T = {t['trajectory_id']: t for t in J(RT / 'measurement/trajectories.jsonl')}
A = {a['annotation_id']: a for a in J(RT / 'measurement/annotations.jsonl')}
for d in J(RT / 'measurement/adjudications.jsonl'):
    if d['annotation_id'] in A: A[d['annotation_id']]['local_quality'] = d['decision']; A[d['annotation_id']]['adjudicated'] = True
SEL = collections.defaultdict(dict)
for s in J(RT / 'measurement/selection.jsonl'): SEL[s['trajectory_id']][int(s.get('depth') or s.get('turn_index'))] = s.get('selection_kind') or s.get('kind')
PAIR = collections.defaultdict(dict)
for p in J(RT / 'measurement/preferences.jsonl'): PAIR[p['trajectory_id']][int(p['depth'])] = p
R = json.load(open(RT / 'measurement/quality_depth_report.json'))
CAND = collections.defaultdict(list)
for c in J(RT / 'measurement/branch_candidates.jsonl'): CAND[(c['trajectory_id'], c['depth'])].append(c)
BJ = {(b['trajectory_id'], b['depth']): b for b in J(RT / 'measurement/branch_judgements.jsonl')}
# per-trajectory derived facts
info = {}
for tid, t in T.items():
    turns = [A.get(f'{tid}:a{k}') for k in range(1, t['assistant_turns'] + 1)]
    sev = [(a or {}).get('local_quality', '?') for a in turns]
    first = next((i + 1 for i, s in enumerate(sev) if s == 'serious'), None)
    info[tid] = dict(sev=sev, first=first, task=(turns[0] or {}).get('task', '?'), lang=(turns[0] or {}).get('language', '?'))
order = sorted(T, key=lambda x: (info[x]['first'] or 99, x))
# --- chart 1: first serious failure by turn (incl. none)
dist = collections.Counter(info[t]['first'] or 'none' for t in T); cats = [1, 2, 3, 4, 5, 6, 7, 8, 'none']
def bar_chart(cats, counts, title, unit='chats'):
    W, H, L, B = 640, 260, 46, 36; n = len(cats); bw = (W - L - 16) / n; mx = max(counts) or 1
    s = [f"<svg viewBox='0 0 {W} {H}' role='img' aria-label='{E(title)}'>"]
    for g in range(0, mx + 1, max(1, mx // 4)):
        y = H - B - (H - B - 24) * g / mx; s.append(f"<line x1='{L}' x2='{W-8}' y1='{y:.1f}' y2='{y:.1f}' class='grid'/><text x='{L-6}' y='{y+4:.1f}' class='tick' text-anchor='end'>{g}</text>")
    for i, (c, v) in enumerate(zip(cats, counts)):
        h = (H - B - 24) * v / mx; x = L + i * bw + 6; y = H - B - h
        s.append(f"<rect x='{x:.1f}' y='{y:.1f}' width='{bw-12:.1f}' height='{h:.1f}' class='bar {'none' if c=='none' else ''}'/>")
        s.append(f"<text x='{x + (bw-12)/2:.1f}' y='{y-6:.1f}' class='val' text-anchor='middle'>{v}</text>")
        s.append(f"<text x='{x + (bw-12)/2:.1f}' y='{H-B+18}' class='tick' text-anchor='middle'>{'no error' if c=='none' else 'turn '+str(c)}</text>")
    s.append(f"<text x='{L}' y='14' class='cap'>{E(title)}</text></svg>"); return ''.join(s)
c1 = bar_chart(cats, [dist.get(c, 0) for c in cats], 'Turn at which the first serious error appeared (28 chats)')
# --- chart 2: new-failure risk by depth
nfr = R['new_failure_risk']; depths = [d for d in ['1','2','3','4','5','6'] if nfr.get(d, {}).get('at_risk', 0) > 0]
W, H, L, B = 640, 220, 46, 36; s = [f"<svg viewBox='0 0 {W} {H}' role='img' aria-label='new failure risk by depth'>"]
for g in (0, 25, 50, 75, 100):
    y = H - B - (H - B - 24) * g / 100; s.append(f"<line x1='{L}' x2='{W-8}' y1='{y:.1f}' y2='{y:.1f}' class='grid'/><text x='{L-6}' y='{y+4:.1f}' class='tick' text-anchor='end'>{g}%</text>")
bw = (W - L - 16) / len(depths)
for i, d in enumerate(depths):
    v = nfr[d]['risk'] * 100; h = (H - B - 24) * v / 100; x = L + i * bw + 6; y = H - B - h
    s.append(f"<rect x='{x:.1f}' y='{y:.1f}' width='{bw-12:.1f}' height='{h:.1f}' class='bar risk'/><text x='{x+(bw-12)/2:.1f}' y='{y-6:.1f}' class='val' text-anchor='middle'>{nfr[d]['new_serious']}/{nfr[d]['at_risk']}</text><text x='{x+(bw-12)/2:.1f}' y='{H-B+18}' class='tick' text-anchor='middle'>turn {d}</text>")
s.append(f"<text x='{L}' y='14' class='cap'>Share of still-clean chats that break at each turn (new serious / at risk)</text></svg>"); c2 = ''.join(s)
# --- chart 3: quality by depth stacked
qbd = R.get('quality_by_depth') or {}
rows = []
for d in sorted(qbd, key=int):
    q = qbd[d]['quality']; n = qbd[d]['denominator_reached']
    rows.append(f"<tr><td>turn {d}</td><td class='num'>{n}</td>" + ''.join(f"<td class='num {k}'>{q.get(k,0)}</td>" for k in ('good','minor','serious')) + "</tr>")
tbl = "<table class='qd'><thead><tr><th>Depth</th><th>Chats reaching it</th><th>Good</th><th>Minor</th><th>Serious</th></tr></thead><tbody>" + ''.join(rows) + "</tbody></table>"
# --- dialogue-specific failures: first serious error AFTER turn 1 (owner: turn-1 errors are single-turn errors)
U = collections.defaultdict(dict)
for e in J(RT / 'measurement/user_events.jsonl'): U[e['trajectory_id']][e['turn_index']] = e
late = [tid for tid in order if info[tid]['first'] and info[tid]['first'] >= 2]
t1 = [tid for tid in order if info[tid]['first'] == 1]; none = [tid for tid in order if not info[tid]['first']]
split = bar_chart(['turn 1 (single-turn error)', 'after turn 1 (dialogue failure)', 'no serious error'], [len(t1), len(late), len(none)], 'What kind of failure each chat shows')
lrows = []
for tid in late:
    i = info[tid]; f = i['first']; ue = U[tid].get(f - 1, {}); a = A.get(f'{tid}:a{f}', {})
    pairs = ', '.join(f'depth {d}' for d in sorted(PAIR[tid])) or 'none'; sel = ', '.join(f'{v}@{k}' for k, v in sorted(SEL[tid].items())) or 'none'
    lrows.append(f"<tr><td><a href='#{tid}' class='id'>{tid}</a><br><span class='meta'>{E(i['task'])} · {E(i['lang'])}</span></td><td class='num'>{f}</td><td>{E(i['sev'][0])}</td><td class='small'>{E(str((ue.get('message') or {}).get('content',''))[:220])}</td><td class='small'>{E(' | '.join(str(x) for x in a.get('evidence', [])[:2])[:260])}</td><td class='small'>{E(sel)}<br>pairs: {E(pairs)}</td></tr>")
late_tbl = ("<div class='tw'><table class='qd late'><thead><tr><th>Chat</th><th>Fails at</th><th>Turn 1 was</th><th>What the user asked right before</th><th>Why the reply is serious</th><th>Selected prefixes / pairs</th></tr></thead><tbody>" + ''.join(lrows) + "</tbody></table></div>")
late_section = f"""<div class='panel'><h2>Dialogue-specific failures: serious error after turn 1</h2>
<p class='lede'>A serious error at turn 1 is a single-turn error and belongs to the single-turn rounds. The dialogue data is about the {len(late)} chats where the model was acceptable at turn 1 and then broke. In all {len(late)}, turn 1 was rated minor, the user's next message corrected that minor issue, and the revision made things worse: it introduced a new factual error, dropped a required number, broke the required structure, invented a condition, or repeated the old text. Only {sum(1 for tid in late if PAIR[tid])} of these chats produced an exported pair; {sum(1 for tid in late if not SEL[tid])} had no prefix selected at all because the selection quota was filled by turn-1 failures.</p>
<div class='charts'><div>{split}</div><div>{late_tbl}</div></div></div>"""
# --- collection counters panel (60-dialogue collection only; absent for the pilot)
COUNT = json.load(open(RT / 'measurement/collection_counters.json')) if (RT / 'measurement/collection_counters.json').exists() else None
LEGEND = ("prefix A = before the first serious reply, B = after the first instruction change that followed it (selected for preference pairs)"
          if COUNT else "prefix P/R/C = selected for preference pairs (prevention / recovery / control)")
counters_panel = ''
if COUNT:
    grp = COUNT['groups']; order_g = ['correction', 'troubleshooting', 'learning']
    ends = sorted({k.split(':', 1)[1] for g in grp.values() for k in g if k.startswith('ending:')})
    g_rows = ''.join(f"<tr><td>{E(g)}</td><td class='num'>{grp.get(g, {}).get('collected', 0)}/{grp.get(g, {}).get('planned', 0)}</td>"
                     + ''.join(f"<td class='num'>{grp.get(g, {}).get('ending:' + e, 0)}</td>" for e in ends)
                     + f"<td class='num'>{COUNT['ab'].get(g + ':A:present', 0)}</td><td class='num'>{COUNT['ab'].get(g + ':B:present', 0)}</td></tr>" for g in order_g)
    g_tbl = ("<div class='tw'><table class='qd'><thead><tr><th>Group</th><th>Collected</th>" + ''.join(f"<th>{E(e.replace('_', ' '))}</th>" for e in ends)
             + "<th>A exists</th><th>B exists</th></tr></thead><tbody>" + g_rows + "</tbody></table></div>")
    c = COUNT['candidates']
    cand_tbl = ("<table class='qd'><thead><tr><th>Points sampled</th><th>Replies sampled</th><th>Distinct</th><th>Acceptable</th><th>Pairs</th><th>A points / pairs</th><th>B points / pairs</th></tr></thead><tbody>"
                f"<tr><td class='num'>{c['points']}</td><td class='num'>{c['sampled']}</td><td class='num'>{c['distinct']}</td><td class='num'>{c['acceptable']}</td><td class='num'>{c['pairs']}</td>"
                f"<td class='num'>{c['by_kind']['A']['points']} / {c['by_kind']['A']['pairs']}</td><td class='num'>{c['by_kind']['B']['points']} / {c['by_kind']['B']['pairs']}</td></tr></tbody></table>")
    def kv_tbl(title, d):
        return (f"<table class='qd'><thead><tr><th>{E(title)}</th><th>Count</th></tr></thead><tbody>"
                + ''.join(f"<tr><td>{E(k.replace('_', ' '))}</td><td class='num'>{v}</td></tr>" for k, v in sorted(d.items(), key=lambda x: -x[1])) + "</tbody></table>")
    calls = COUNT['calls']; sol = sum(v for k, v in calls.items() if k.startswith('sol')); tgt = sum(v for k, v in calls.items() if k.startswith('target'))
    cost = ' · '.join(f"{E(s['stage'])} EUR {float(s['eur'] or 0):.3f}" for s in COUNT['gpu_sessions']) or 'not yet recorded'
    counters_panel = (f"<div class='panel'><h2>Collection counters</h2><p class='lede'>{COUNT['independent_conversations']} independent conversations. A reply is a sampled completion; "
                      "distinct counts exact-duplicate texts once; acceptable is the judge's absolute verdict; a pair also passed verification.</p>"
                      + g_tbl + cand_tbl + f"<div class='charts'><div>{kv_tbl('Instruction change after the first serious error', COUNT['change_types'])}</div>"
                      f"<div>{kv_tbl('Why A or B does not exist', COUNT['absent'])}</div></div>"
                      f"<div class='charts'><div>{kv_tbl('Quality of those changes', COUNT['change_quality'])}</div><div>{kv_tbl('Calls by stage', calls)}</div></div>"
                      f"<p class='meta'>Sol calls {sol} in the dialogue pipeline plus {COUNT.get('opening_generation_sol_calls', 0)} to generate the openings, all at medium effort · model completions {tgt} · GPU {cost} (total EUR {sum(float(s['eur'] or 0) for s in COUNT['gpu_sessions']):.3f})</p></div>")
# --- branch results panel (omitted when the run did not branch)
branch_panel = ''
if BJ:
    brows = ''.join(f"<tr><td><a href='#{E(b['trajectory_id'])}' class='id'>{E(b['trajectory_id'])}</a></td><td>{E(b.get('kind','').replace('_',' '))}</td><td class='num'>{E(b.get('depth'))}</td><td class='num'>{E(b.get('samples_judged'))}</td><td>{'yes' if b.get('found_within_4') else 'no'}</td><td>{'yes' if b.get('found_within_8') else 'no'}</td><td class='small'>{E(b.get('report_phrase'))}</td></tr>"
                    for b in sorted(BJ.values(), key=lambda x: (x['trajectory_id'], x['depth'])))
    branch_panel = ("<div class='panel'><h2>Alternative replies at the selected prefixes</h2>"
                    "<p class='lede'>At each selected prefix the model was asked again for a fresh reply, eight times, judged blind in fours under rubric v2.4, with a verification pass on the winner. The replies themselves sit inside each chat below.</p>"
                    "<div class='tw'><table class='qd late'><thead><tr><th>Chat</th><th>Prefix</th><th>Before turn</th><th>Replies judged</th><th>Acceptable in first 4</th><th>Acceptable in 8</th><th>Result</th></tr></thead><tbody>" + brows + "</tbody></table></div></div>")
def alts_block(tid, d):
    """The eight replies sampled at this prefix, shown where they were sampled: just before the reply they were alternatives to."""
    cands = CAND.get((tid, d))
    if not cands: return ''
    b = BJ.get((tid, d), {}); alts = []
    for cd in sorted(cands, key=lambda x: x.get('candidate_index', 0)):
        mark = "<span class='mark pair'>chosen</span>" if cd.get('chosen') else ("<span class='mark'>rejected</span>" if cd.get('rejected') else '')
        tg = ''.join(f"<span class='tag'>{E(x)}</span>" for x in cd.get('issues') or [])
        alts.append(f"<div class='col'><span class='who'>reply {cd.get('candidate_index')} <b class='sev {E(cd.get('verdict') or '')}'>{E(cd.get('verdict') or '—')}</b>{mark}</span><div class='tags'>{tg}</div><div class='txt'>{E(cd.get('text'))}</div><details><summary>Sol's note</summary><ul><li>{E(cd.get('note'))}</li></ul></details></div>")
    return (f"<details class='alts' open><summary><b>{len(cands)} replies sampled again at this point</b> · {E(b.get('kind','').replace('_',' '))} prefix · "
            f"the conversation below continues with the original reply · {E(b.get('report_phrase',''))}</summary><div class='cols'>{''.join(alts)}</div></details>")
# --- dialogues
cards = []
for tid in order:
    t = T[tid]; i = info[tid]; msgs = t['messages']; k = 0; body = []
    strip = ''.join(f"<span class='sq {s}' title='turn {j+1}: {s}'></span>" for j, s in enumerate(i['sev']))
    for m in msgs:
        if m['role'] == 'user': body.append(f"<div class='msg user'><span class='who'>user</span><div>{E(m['content'])}</div></div>")
        else:
            k += 1; body.append(alts_block(tid, k)) if (tid, k) in CAND else None
            a = A.get(f'{tid}:a{k}', {}); sev = a.get('local_quality', '?'); tags = ''.join(f"<span class='tag'>{E(x)}</span>" for x in a.get('issue_tags', []) or [])
            marks = ''
            if k in SEL[tid]: marks += f"<span class='mark {SEL[tid][k]}'>prefix {SEL[tid][k]}</span>"
            if k in PAIR[tid]: marks += "<span class='mark pair'>pair exported</span>"
            rec = ''
            if a.get('recovery_opportunity'): rec = f"<span class='mark rec'>{'repaired' if a.get('recovery_success') else 'repair missed'}</span>"
            ev = ''.join(f"<li>{E(x)}</li>" for x in a.get('evidence', []) or [])
            body.append(f"<div class='msg assistant'><span class='who'>assistant · turn {k} <b class='sev {sev}'>{sev}</b>{' <i>(root-adjudicated)</i>' if a.get('adjudicated') else ''}{marks}{rec}</span><div>{E(m['content'])}</div><details><summary>Sol's evidence {tags}</summary><ul>{ev}</ul></details></div>")
    first = f"first serious error at turn {i['first']}" if i['first'] else 'no serious error'
    cards.append(f"<article class='chat' id='{tid}'><header><span class='id'>{tid}</span><span>{E(i['task'])} · {E(i['lang'])}</span><span class='strip'>{strip}</span><span class='meta'>{first} · ended: {E(t['terminal_code'])}</span></header>{''.join(body)}</article>")
toc = ''.join(f"<a href='#{tid}'><span class='id'>{tid}</span><span class='strip'>{''.join(f'<span class=\"sq {s}\"></span>' for s in info[tid]['sev'])}</span><span class='meta'>{E(info[tid]['task'])} · {E(info[tid]['lang'])} · {('turn '+str(info[tid]['first'])) if info[tid]['first'] else 'no error'}</span></a>" for tid in order)
page = f"""<title>{E(TITLE)}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;600;700&family=Noto+Serif:ital,wght@0,400;0,600;1,400&display=swap">
<style>
:root{{--bg:#f4f5f2;--surface:#ffffff;--ink:#1e242b;--muted:#5f6b76;--line:#d8dde2;--accent:#3b5f8a;--good:#2f8f5b;--minor:#d29a2b;--serious:#c4463c;--user:#eef1f5;--chip:#e8ecef;--pair:#6a4c93}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#14181c;--surface:#1c2228;--ink:#e7ebef;--muted:#9aa6b2;--line:#2c353f;--accent:#8fb3dc;--good:#5cbf88;--minor:#e2b45a;--serious:#e0746a;--user:#232b33;--chip:#2a333c;--pair:#b39ddb}}}}
:root[data-theme="dark"]{{--bg:#14181c;--surface:#1c2228;--ink:#e7ebef;--muted:#9aa6b2;--line:#2c353f;--accent:#8fb3dc;--good:#5cbf88;--minor:#e2b45a;--serious:#e0746a;--user:#232b33;--chip:#2a333c;--pair:#b39ddb}}
body{{background:var(--bg);color:var(--ink);font-family:"Noto Sans",system-ui,sans-serif;padding-block:28px;padding-inline:20px;line-height:1.5;overflow-x:hidden}}
main{{max-width:1040px;margin:0 auto;display:grid;gap:20px;min-width:0}} main>*{{min-width:0}}
h1{{font-family:"Noto Serif",Georgia,serif;font-size:1.9rem;margin:0 0 6px;text-wrap:balance}} h2{{font-size:1.1rem;margin:0 0 8px}}
.lede{{color:var(--muted);max-width:72ch;margin:0}}
.panel{{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:16px 18px}}
.charts{{display:grid;grid-template-columns:1fr 1fr;gap:16px}} @media (max-width:760px){{.charts{{grid-template-columns:1fr}}}}
svg{{width:100%;height:auto;max-width:100%}} .grid{{stroke:var(--line);stroke-width:1}} .tick{{fill:var(--muted);font-size:11px}} .val{{fill:var(--ink);font-size:12px;font-weight:600}} .cap{{fill:var(--muted);font-size:12px}}
.bar{{fill:var(--serious)}} .bar.none{{fill:var(--good)}} .bar.risk{{fill:var(--accent)}}
table.qd{{border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%}} .qd th,.qd td{{padding:6px 10px;border-bottom:1px solid var(--line);text-align:left}} .qd .num{{text-align:right}} .qd td.good{{color:var(--good)}} .qd td.minor{{color:var(--minor)}} .qd td.serious{{color:var(--serious)}}
.toc{{display:grid;gap:6px}} .toc a{{display:grid;grid-template-columns:70px 1fr 2fr;gap:10px;align-items:center;color:inherit;text-decoration:none;padding:4px 6px;border-radius:6px}} .toc a:hover{{background:var(--user)}}
.id{{font-weight:700;color:var(--accent);letter-spacing:.04em}} .meta{{color:var(--muted);font-size:.9rem}}
.strip{{display:inline-flex;gap:3px}} .sq{{width:14px;height:14px;border-radius:3px;display:inline-block;background:var(--chip)}} .sq.good{{background:var(--good)}} .sq.minor{{background:var(--minor)}} .sq.serious{{background:var(--serious)}}
.chat{{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:14px 16px;display:grid;gap:10px;min-width:0}}
.chat>*{{min-width:0;max-width:100%}}
.chat header{{display:flex;flex-wrap:wrap;gap:12px;align-items:center;border-bottom:1px solid var(--line);padding-bottom:8px}}
.msg{{display:grid;gap:4px;padding:10px 12px;border-radius:8px;font-family:"Noto Serif",Georgia,serif;white-space:pre-wrap;word-wrap:break-word}}
.msg.user{{background:var(--user);margin-right:8%}} .msg.assistant{{border:1px solid var(--line);margin-left:8%}}
.who{{font-family:"Noto Sans",system-ui,sans-serif;font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);display:flex;flex-wrap:wrap;gap:8px;align-items:center}}
.sev{{padding:1px 8px;border-radius:10px;color:#fff;text-transform:none;letter-spacing:0}} .sev.good{{background:var(--good)}} .sev.minor{{background:var(--minor)}} .sev.serious{{background:var(--serious)}}
.mark{{padding:1px 8px;border-radius:10px;background:var(--chip);text-transform:none;letter-spacing:0;font-weight:600}} .mark.P{{color:var(--serious)}} .mark.R{{color:var(--minor)}} .mark.C{{color:var(--good)}} .mark.A{{color:var(--serious)}} .mark.B{{color:var(--minor)}} .mark.pair{{color:var(--pair)}} .mark.rec{{color:var(--accent)}}
details{{font-family:"Noto Sans",system-ui,sans-serif;font-size:.88rem;color:var(--muted)}} details summary{{cursor:pointer}} details ul{{margin:6px 0 0;padding-left:18px}} .tag{{background:var(--chip);border-radius:6px;padding:0 6px;margin-left:4px;font-size:.78rem}}
.tw{{overflow-x:auto}} .late td.small{{font-size:.82rem;max-width:260px}} .charts>div{{min-width:0}}
details.alts{{margin-left:8%;border-left:2px solid var(--line);padding-left:10px;min-width:0;max-width:100%;overflow:hidden}} details.alts>summary{{color:var(--accent);margin:4px 0 8px}}
.alts .cols{{display:flex;gap:10px;overflow-x:auto;overscroll-behavior-x:contain;align-items:stretch;padding:2px 0 8px;width:100%;max-width:100%}}
.alts .col{{flex:0 0 340px;max-width:100%;border:1px solid var(--line);border-radius:8px;background:var(--surface);padding:8px 10px;display:flex;flex-direction:column;gap:6px}}
.alts .col .txt{{font-family:"Noto Serif",Georgia,serif;white-space:pre-wrap;word-wrap:break-word;max-height:44vh;overflow:auto;flex:1}}
.alts .tags{{display:flex;flex-wrap:wrap;gap:4px}}
@media (max-width:760px){{.alts .col{{flex-basis:86vw}}}}
.legend{{display:flex;flex-wrap:wrap;gap:14px;color:var(--muted);font-size:.9rem;align-items:center}}
</style>
<main>
<div><h1>{E(TITLE)}</h1>
<p class='lede'>{E(LEDE) if LEDE else "The dialogue pilot's measurement panel: 28 simulated conversations with the Greek Apertus checkpoint (R4_full epoch 1), up to 8 assistant turns each, Sol as the user. "
"Every assistant turn was annotated for severity by Sol from the prefix alone and root-reviewed. Below: the distribution of the turn at which the first serious error appeared, the risk of a new failure at each depth, and every chat in full."}</p>
<div class='legend' style='margin-top:10px'><span><span class='sq good'></span> good</span><span><span class='sq minor'></span> minor</span><span><span class='sq serious'></span> serious</span><span>{E(LEGEND)}</span></div></div>
{late_section}
<div class='charts'><div class='panel'>{c1}</div><div class='panel'>{c2}</div></div>
<div class='panel'><h2>Quality by depth</h2>{tbl}<p class='meta'>Endings: {E(json.dumps(R['ending_reasons']))}. {E(FOOT)}</p></div>
{counters_panel}
{branch_panel}
<div class='panel'><h2>Chats</h2><div class='toc'>{toc}</div></div>
{''.join(cards)}
</main>"""
open(out, 'w').write(page); print('wrote', out, len(page), 'chars,', len(cards), 'chats')
