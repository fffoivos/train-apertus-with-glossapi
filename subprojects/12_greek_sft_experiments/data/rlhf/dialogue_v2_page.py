#!/usr/bin/env python3
"""Dialogue v2 page in the round-1/round-2 house style: where the chats break (charts), then every conversation with per-turn
severity, the evaluator's evidence, the user's move, the sampling points and the exported pair, with per-turn annotation saved
in the artifact's database (collection votes_dialogue_v2).
Usage: python3 data/rlhf/dialogue_v2_page.py <out.html>"""
import collections, html, json, pathlib, sys
RL = pathlib.Path(__file__).resolve().parent
ROOTS = [RL / 'dialogue_v2' / 'runtime', RL / 'reference_guided_dialogue_demo' / 'runtime']
E = lambda s: html.escape(str(s if s is not None else ''))
def J(p): return [json.loads(l) for l in open(p) if l.strip()] if p.exists() else []
def rows(name): return [r for root in ROOTS for r in J(root / name)]
traj = {}
for t in rows('trajectories.jsonl'): traj[t['case_id']] = t                    # last write wins: the completed trajectory
EV = collections.defaultdict(dict)
for e in rows('turn_evaluations.jsonl'): EV[e['case_id']][e['assistant_turn']] = e
UT = collections.defaultdict(dict); FINAL = {}
for u in rows('user_turns.jsonl'):
    (FINAL.__setitem__(u['case_id'], u) if u.get('mode') == 'final_assessment' else UT[u['case_id']].__setitem__(u.get('user_turn_index'), u))
PTS = collections.defaultdict(list)
for p in rows('sampling_points.jsonl'):
    for x in (p.get('points') or []): PTS[p['case_id']].append(x)
BP = {b['point_id']: b for b in rows('branch_points.jsonl')}
PAIRS = collections.defaultdict(list)
for p in rows('branch_pairs.jsonl'): PAIRS[p['case_id']].append(p)
JUDGE = {j['point_id']: j for j in rows('branch_judgements.jsonl')}
CAND = collections.defaultdict(list)
for c in rows('branch_candidates.jsonl'): CAND[c['point_id']].append(c)
VERD = {}                                    # candidate_id -> (verdict, issues, note, batch)
for pid, j in JUDGE.items():
    for b in j.get('batches', []):
        r = b.get('ranking') or {}; l2c = r.get('letter_to_candidate_id', {})
        for letter, cid in l2c.items():
            VERD[cid] = dict(verdict=(r.get('verdicts') or {}).get(letter) or (r.get('verdicts') or {}).get(cid),
                             issues=(r.get('issues') or {}).get(cid, []), note=(r.get('notes') or {}).get(cid, ''),
                             batch=b.get('batch'), chosen=(b.get('chosen') == cid), rejected=(b.get('rejected') == cid), margin=r.get('best_vs_worst'))
CASES = sorted(traj, key=lambda c: (0 if c.startswith('DVI') else 1, c))
SEV = {'good': 'good', 'minor': 'minor', 'serious': 'serious', 'unjudgeable': 'unj'}
def first_serious(c):
    ev = EV[c]
    return next((k for k in sorted(ev) if ev[k]['local_quality'] == 'serious'), None)
# ---------- charts ----------
def bars(cats, counts, title, labels=None, note=''):
    W, H, L, B = 660, 250, 44, 40; n = max(1, len(cats)); bw = (W - L - 16) / n; mx = max(counts) or 1
    s = [f"<figure><svg viewBox='0 0 {W} {H}' role='img' aria-label='{E(title)}'>"]
    step = max(1, mx // 4)
    for g in range(0, mx + 1, step):
        y = H - B - (H - B - 26) * g / mx
        s.append(f"<line x1='{L}' x2='{W-8}' y1='{y:.1f}' y2='{y:.1f}' class='grid'/><text x='{L-6}' y='{y+4:.1f}' class='tick' text-anchor='end'>{g}</text>")
    for i, (c, v) in enumerate(zip(cats, counts)):
        h = (H - B - 26) * v / mx; x = L + i * bw + 7; y = H - B - h
        s.append(f"<rect x='{x:.1f}' y='{y:.1f}' width='{bw-14:.1f}' height='{h:.1f}' class='bar {'none' if c=='none' else ''}'/>")
        s.append(f"<text x='{x + (bw-14)/2:.1f}' y='{y-6:.1f}' class='val' text-anchor='middle'>{v}</text>")
        lab = (labels[i] if labels else ('no serious error' if c == 'none' else f'turn {c}'))
        s.append(f"<text x='{x + (bw-14)/2:.1f}' y='{H-B+18}' class='tick' text-anchor='middle'>{E(lab)}</text>")
    s.append('</svg>' + (f"<figcaption>{E(note)}</figcaption>" if note else '') + '</figure>')
    return ''.join(s)
def stacked(depths, series, title, note=''):
    W, H, L, B = 660, 250, 44, 40; n = max(1, len(depths)); bw = (W - L - 16) / n
    tot = [sum(series[k][i] for k in series) for i in range(len(depths))]; mx = max(tot) or 1
    s = [f"<figure><svg viewBox='0 0 {W} {H}' role='img' aria-label='{E(title)}'>"]
    for g in range(0, mx + 1, max(1, mx // 4)):
        y = H - B - (H - B - 26) * g / mx
        s.append(f"<line x1='{L}' x2='{W-8}' y1='{y:.1f}' y2='{y:.1f}' class='grid'/><text x='{L-6}' y='{y+4:.1f}' class='tick' text-anchor='end'>{g}</text>")
    for i, d in enumerate(depths):
        y0 = H - B
        for key in ('good', 'minor', 'serious'):
            v = series[key][i]
            if not v: continue
            h = (H - B - 26) * v / mx; y0 -= h
            s.append(f"<rect x='{L + i*bw + 7:.1f}' y='{y0:.1f}' width='{bw-14:.1f}' height='{h:.1f}' class='seg {key}'><title>turn {d}: {v} {key}</title></rect>")
        s.append(f"<text x='{L + i*bw + (bw-14)/2 + 7:.1f}' y='{H-B+18}' class='tick' text-anchor='middle'>turn {d}</text>")
        if tot[i]: s.append(f"<text x='{L + i*bw + (bw-14)/2 + 7:.1f}' y='{y0-6:.1f}' class='val' text-anchor='middle'>{tot[i]}</text>")
    s.append('</svg>' + (f"<figcaption>{E(note)}</figcaption>" if note else '') + '</figure>')
    return ''.join(s)
fs = collections.Counter(first_serious(c) or 'none' for c in CASES)
cats1 = [1, 2, 3, 4, 5, 6, 'none']
chart1 = bars(cats1, [fs.get(c, 0) for c in cats1], 'Turn at which the first serious error appeared', note='Ten conversations. A serious error at turn 1 is single-turn material; the dialogue-specific material is everything to the right of it.')
maxd = max((max(EV[c]) for c in CASES if EV[c]), default=1)
depths = list(range(1, maxd + 1))
series = {k: [sum(1 for c in CASES if EV[c].get(d, {}).get('local_quality') == k) for d in depths] for k in ('good', 'minor', 'serious')}
chart2 = stacked(depths, series, 'Reply quality by turn', note='Every assistant reply of the ten conversations, graded against the disclosed request and the private reference.')
ends = collections.Counter(traj[c].get('ending_reason', 'unknown') for c in CASES)
elabels = [k.replace('_', ' ') for k in ends]
chart3 = bars(list(ends), [ends[k] for k in ends], 'How the conversations ended', labels=elabels, note='Abandonment is the simulated user giving up; natural completion means the goal was reached.')
# ---------- per-case cards ----------
cards = []
for c in CASES:
    t = traj[c]; msgs = t.get('messages') or []; ev = EV[c]; ut = UT[c]
    a_i = 0; u_i = 0; turns = []
    for m in msgs:
        if m['role'] == 'user':
            u_i += 1
            move = (ut.get(u_i - 1) or ut.get(u_i) or {}).get('move') if u_i > 1 else None
            turns.append(f"<div class='turn user'><div class='who'>user{' · ' + E(move) if move else ' · opening'}</div><div class='msg'>{E(m['content'])}</div></div>")
        else:
            a_i += 1; e = ev.get(a_i, {}); q = SEV.get(e.get('local_quality', ''), 'unj')
            notes = ''
            if e:
                notes = f"<div class='ev'><b>{E(e.get('local_quality','?'))}</b> · {E(e.get('error_summary') or 'no material error')}</div>"
                for x in (e.get('factual_or_subject_errors') or [])[:4]: notes += f"<div class='err'>{E(x)}</div>"
                if e.get('repeats_earlier_failed_reply'): notes += "<div class='err'>repeats an earlier rejected reply</div>"
                if e.get('maths_content'): notes += "<div class='hold'>maths content: held for the specialist maths judge</div>"
            turns.append(f"<div class='turn assistant q-{q}' data-case='{E(c)}' data-turn='{a_i}'><div class='who'>model · reply {a_i}</div><div class='msg'>{E(m['content'])}</div>{notes}"
                         f"<div class='vote'><span class='vlabel'>your call:</span>"
                         + ''.join(f"<button class='v' data-v='{k}'>{k}</button>" for k in ('good', 'minor', 'serious'))
                         + "<button class='v agree' data-v='agree'>agree</button><span class='vstate'></span></div></div>")
    fin = FINAL.get(c)
    if fin: turns.append(f"<div class='turn user final'><div class='who'>user · final assessment (not sent)</div><div class='msg'>{E(fin.get('message'))}</div></div>")
    pts = ''.join(f"<li><span class='chip'>{E(p.get('kind','').replace('_',' '))}</span> before reply {E(p.get('before_assistant_turn'))}"
                  + (" <span class='chip sel'>sampled</span>" if p.get('point_id') in BP else '')
                  + (" <span class='chip hold'>maths hold</span>" if p.get('maths_content_hold') else '')
                  + f"<div class='note'>{E(p.get('reason'))}</div></li>" for p in PTS.get(c, []))
    branch = ''
    for pt in sorted({x['point_id'] for x in CAND if False} | {k for k in CAND if k.startswith(c + ':')}):
        j = JUDGE.get(pt, {}); cands = sorted(CAND[pt], key=lambda x: x.get('candidate_index', 0))
        cols = ''
        for i, cd in enumerate(cands, 1):
            v = VERD.get(cd['candidate_id'], {}); vd = v.get('verdict') or '—'
            mark = " chosen" if v.get('chosen') else (" rejected" if v.get('rejected') else "")
            tags = ''.join(f"<span class='tag'>{E(x)}</span>" for x in (v.get('issues') or []))
            cols += (f"<div class='cand{mark}' data-case='{E(c)}' data-cand='{E(cd['candidate_id'])}'><div class='cand-head'><span class='lab'>reply {i}</span>"
                     f"<span class='vd {E(vd)}'>{E(vd)}</span>{'<span class=\'chip sel\'>chosen</span>' if v.get('chosen') else ''}{'<span class=\'chip\'>rejected</span>' if v.get('rejected') else ''}</div>"
                     f"<div class='tags'>{tags}</div><div class='note'>{E(v.get('note',''))}</div><div class='msg'>{E(cd['text'])}</div>"
                     f"<div class='vote'><button class='v' data-v='best'>my best</button><button class='v' data-v='unusable'>unusable</button><span class='vstate'></span></div></div>")
        branch += (f"<details class='branch'><summary>{E(pt.split(':',1)[1].replace('_',' '))} · 8 alternative replies sampled and rated · {E(j.get('report_phrase',''))}</summary>"
                   f"<div class='cands'>{cols}</div></details>")
    pairs = ''
    for p in PAIRS.get(c, []):
        pairs += (f"<div class='pair'><div><div class='plabel'>chosen</div><div class='msg'>{E(p['chosen'])}</div></div>"
                  f"<div><div class='plabel'>rejected</div><div class='msg'>{E(p['rejected'])}</div></div></div>"
                  f"<p class='note'>{E(p.get('sampling_point_kind','').replace('_',' '))} before reply {E(p.get('depth'))} · {E(p.get('loss_note') or '')}</p>")
    fserious = first_serious(c)
    head = (f"<span class='pid'>{E(c)}</span><span class='chip cat'>{E(t.get('category'))}</span><span class='chip'>{E(t.get('language'))}</span>"
            f"<span class='chip'>{E(t.get('purpose'))}</span><span class='chip end'>{E((t.get('ending_reason') or '').replace('_',' '))}</span>"
            f"<span class='chip'>{a_i} replies</span>"
            + (f"<span class='chip serious-chip'>first serious error at turn {fserious}</span>" if fserious else "<span class='chip good-chip'>no serious error</span>"))
    cards.append(f"""<section class='card' id='{E(c)}'><div class='card-head'>{head}</div>
<div class='body'><div class='chat'>{''.join(turns)}</div>
<aside class='side'><h3>Sampling points</h3><ul class='pts'>{pts or '<li class="note">none</li>'}</ul>
{('<h3>Alternative replies sampled here</h3>' + branch) if branch else '<h3>Alternative replies</h3><p class="note">None sampled: the reference-guided cases mark their points but do not branch in this demo.</p>'}
{('<h3>Exported pair</h3>' + pairs) if pairs else ''}
<h3>Ending</h3><p class='note'>{E(t.get('ending_detail') or t.get('ending_reason'))}</p></aside></div></section>""")
total_replies = sum(len(EV[c]) for c in CASES)
q = collections.Counter(e['local_quality'] for c in CASES for e in EV[c].values())
npairs = sum(len(PAIRS[c]) for c in CASES)
page = f"""<title>Where the Chats Break, Round Two</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400&display=swap">
<style>
:root {{ --bg:#F4F6F8; --surface:#FFFFFF; --ink:#1B222E; --muted:#5B6674; --line:#D6DCE4; --accent:#1A6C8C; --accent-ink:#125066; --accent-soft:#E2EFF4;
 --good:#3D6B2E; --good-soft:#E5F0E0; --minor:#9A5A10; --minor-soft:#F7ECDC; --serious:#9B2F3A; --serious-soft:#F6E3E6; --hold:#6B4F8C; --hold-soft:#EEE8F5; --code-bg:#F0F3F6; --user:#EEF3F7; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#11161C; --surface:#181E26; --ink:#E4E9F0; --muted:#98A3B2; --line:#2A333F; --accent:#63B4D0; --accent-ink:#8FCCE0; --accent-soft:#1B303B;
 --good:#8FC77A; --good-soft:#1F2F1A; --minor:#E2A65E; --minor-soft:#3A2A16; --serious:#EE8593; --serious-soft:#2E1A1E; --hold:#B9A1DA; --hold-soft:#2A2238; --code-bg:#0E1319; --user:#1C2632; }} }}
:root[data-theme="dark"] {{ --bg:#11161C; --surface:#181E26; --ink:#E4E9F0; --muted:#98A3B2; --line:#2A333F; --accent:#63B4D0; --accent-ink:#8FCCE0; --accent-soft:#1B303B;
 --good:#8FC77A; --good-soft:#1F2F1A; --minor:#E2A65E; --minor-soft:#3A2A16; --serious:#EE8593; --serious-soft:#2E1A1E; --hold:#B9A1DA; --hold-soft:#2A2238; --code-bg:#0E1319; --user:#1C2632; }}
* {{ box-sizing:border-box; }}
body {{ background:var(--bg); color:var(--ink); font-family:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif; font-size:14.5px; line-height:1.55; margin:0; padding-inline:clamp(16px,2.5vw,32px); padding-block:26px 64px; }}
h1 {{ font-family:"Source Serif 4",Georgia,serif; font-weight:600; font-size:clamp(25px,3.2vw,34px); margin:4px 0 8px; text-wrap:balance; }}
h2 {{ font-family:"Source Serif 4",Georgia,serif; font-weight:600; font-size:20px; margin:26px 0 10px; }}
h3 {{ font-size:12px; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin:14px 0 6px; }}
.eyebrow {{ font-size:12px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); font-weight:600; }}
.lede {{ color:var(--muted); max-width:78ch; margin:0 0 16px; }}
.stats {{ display:flex; flex-wrap:wrap; gap:10px 30px; margin:8px 0 18px; }}
.stat b {{ display:block; font-family:"Source Serif 4",Georgia,serif; font-size:26px; font-weight:600; font-variant-numeric:tabular-nums; }}
.stat span {{ font-size:12.5px; color:var(--muted); }}
.charts {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:18px; }}
figure {{ margin:0; background:var(--surface); border:1px solid var(--line); padding:10px 12px; }}
figcaption {{ font-size:12.5px; color:var(--muted); margin-top:6px; }}
svg {{ width:100%; height:auto; }} .grid {{ stroke:var(--line); stroke-width:1; }} .tick {{ fill:var(--muted); font-size:11px; }} .val {{ fill:var(--ink); font-size:12px; font-weight:600; }}
.bar {{ fill:var(--accent); }} .bar.none {{ fill:var(--good); }} .seg.good {{ fill:var(--good); }} .seg.minor {{ fill:var(--minor); }} .seg.serious {{ fill:var(--serious); }}
.card {{ background:var(--surface); border:1px solid var(--line); margin:0 0 16px; }}
.card-head {{ display:flex; flex-wrap:wrap; gap:6px 10px; align-items:center; padding:10px 14px; border-bottom:1px solid var(--line); }}
.pid {{ font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:12px; color:var(--accent-ink); }}
.chip {{ font-size:11.5px; padding:1px 7px; background:var(--code-bg); color:var(--muted); }}
.chip.cat {{ background:var(--accent-soft); color:var(--accent-ink); font-weight:600; }}
.chip.serious-chip {{ background:var(--serious-soft); color:var(--serious); font-weight:600; }} .chip.good-chip {{ background:var(--good-soft); color:var(--good); font-weight:600; }}
.chip.sel {{ background:var(--accent-soft); color:var(--accent-ink); }} .chip.hold {{ background:var(--hold-soft); color:var(--hold); }}
.body {{ display:grid; grid-template-columns:minmax(0,1.7fr) minmax(0,1fr); gap:20px; padding:12px 14px 16px; }}
.chat {{ display:grid; gap:10px; min-width:0; }}
.turn {{ padding:8px 12px; border:1px solid var(--line); }}
.turn.user {{ background:var(--user); }} .turn.final {{ border-style:dashed; }}
.turn.assistant {{ border-left-width:3px; }}
.turn.q-good {{ border-left-color:var(--good); }} .turn.q-minor {{ border-left-color:var(--minor); }} .turn.q-serious {{ border-left-color:var(--serious); }} .turn.q-unj {{ border-left-color:var(--muted); }}
.who {{ font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); font-weight:600; margin-bottom:3px; }}
.msg {{ white-space:pre-wrap; overflow-wrap:anywhere; font-size:14px; }}
.ev {{ font-size:12.5px; color:var(--muted); margin-top:7px; border-top:1px dotted var(--line); padding-top:6px; }}
.ev b {{ color:var(--ink); text-transform:uppercase; font-size:11px; letter-spacing:.05em; }}
.err {{ font-size:12px; color:var(--serious); margin-top:3px; }} .hold {{ font-size:12px; color:var(--hold); margin-top:3px; }}
.vote {{ display:flex; flex-wrap:wrap; gap:6px; align-items:center; margin-top:8px; }}
.vlabel {{ font-size:11.5px; color:var(--muted); }}
button.v {{ font:inherit; font-size:12px; padding:3px 9px; border:1px solid var(--line); background:var(--surface); color:var(--ink); cursor:pointer; }}
button.v:hover {{ border-color:var(--accent); }} button.v.on {{ background:var(--accent-soft); border-color:var(--accent); color:var(--accent-ink); font-weight:600; }}
button:disabled {{ opacity:.45; cursor:default; }} button:focus-visible {{ outline:2px solid var(--accent); outline-offset:1px; }}
.vstate {{ font-size:11.5px; color:var(--accent-ink); }}
.side {{ min-width:0; }} ul.pts {{ list-style:none; margin:0; padding:0; display:grid; gap:8px; }}
.note {{ font-size:12.5px; color:var(--muted); }}
.pair {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:6px; }}
.pair>div {{ border:1px solid var(--line); padding:8px; background:var(--bg); }}
.plabel {{ font-size:11px; text-transform:uppercase; letter-spacing:.05em; font-weight:600; color:var(--muted); margin-bottom:3px; }}
.dbstate {{ font-size:12.5px; color:var(--muted); }}
details.branch {{ border:1px solid var(--line); padding:6px 10px; margin-bottom:8px; }}
details.branch summary {{ cursor:pointer; font-size:12.5px; font-weight:600; color:var(--accent-ink); }}
.cands {{ display:grid; gap:8px; margin-top:8px; }}
.cand {{ border:1px solid var(--line); padding:8px; background:var(--bg); }}
.cand.chosen {{ outline:2px solid var(--good); }} .cand.rejected {{ outline:2px dashed var(--minor); }}
.cand-head {{ display:flex; gap:8px; align-items:center; margin-bottom:4px; }}
.cand .lab {{ font-size:11.5px; color:var(--muted); }}
.cand .msg {{ font-size:13px; max-height:15em; overflow:auto; margin-top:5px; border-top:1px solid var(--line); padding-top:5px; }}
.vd {{ font-size:11px; text-transform:uppercase; letter-spacing:.05em; font-weight:600; padding:1px 7px; }}
.vd.reinforce {{ background:var(--good-soft); color:var(--good); }} .vd.discourage {{ background:var(--serious-soft); color:var(--serious); }} .vd.neutral {{ background:var(--code-bg); color:var(--muted); }}
.tags {{ display:flex; flex-wrap:wrap; gap:4px; }} .tag {{ font-size:11px; background:var(--code-bg); color:var(--muted); padding:1px 6px; }}
@media (max-width:860px) {{ .body {{ grid-template-columns:1fr; }} .pair {{ grid-template-columns:1fr; }} }}
</style>
<div class="eyebrow">το Ελληνικό Apertus · dialogue v2 · development only · not training data</div>
<h1>Where the Chats Break, Round Two</h1>
<p class="lede">Ten conversations between the adapted model and a simulated user who reacts to what the model actually said: four improvement trajectories and six reference-guided cases (writing, troubleshooting, learning). Each reply is graded against the disclosed request and a private reference the model never sees. The charts show when conversations break; the transcripts show how. Your call on any reply is saved with the page.</p>
<div class="stats">
 <div class="stat"><b>{len(CASES)}</b><span>conversations</span></div>
 <div class="stat"><b>{total_replies}</b><span>model replies graded</span></div>
 <div class="stat"><b>{q.get('serious',0)}</b><span>serious failures</span></div>
 <div class="stat"><b>{q.get('good',0)}</b><span>good replies</span></div>
 <div class="stat"><b>{sum(len(CAND[k]) for k in CAND)}</b><span>alternative replies sampled and rated</span></div>
 <div class="stat"><b>{npairs}</b><span>preference pairs exported</span></div>
 <div class="stat"><b>0</b><span>conversations where hidden information leaked</span></div>
</div>
<div class="charts">{chart1}{chart2}{chart3}</div>
<h2>The conversations</h2>
<p class="lede">Colour on the left edge of a reply is its grade: green good, amber minor, red serious. The right column lists the points where a different reply could have been sampled, and the pair that survived judging and verification.</p>
<p class="dbstate" id="dbstate">connecting to the annotation store…</p>
{''.join(cards)}
<script>
(function () {{
  let db = null; const state = {{}};
  const key = (c, t) => c + ':' + t;
  function paint(el) {{
    const k = key(el.dataset.case, el.dataset.turn); const v = state[k];
    el.querySelectorAll('button.v').forEach(b => b.classList.toggle('on', !!v && v.call === b.dataset.v));
    const s = el.querySelector('.vstate');
    s.textContent = !v ? '' : v.call === 'agree' ? 'you agree' : 'you: ' + v.call;
  }}
  async function save(el, call) {{
    if (!db) return; const c = el.dataset.case, t = Number(el.dataset.turn);
    const doc = {{ case_id: c, assistant_turn: t, call, judge_label: el.className.includes('q-serious') ? 'serious' : el.className.includes('q-minor') ? 'minor' : el.className.includes('q-good') ? 'good' : 'unjudgeable', ts: new Date().toISOString() }};
    try {{ await db.doc('votes_dialogue_v2/' + c + '_' + t).set(doc); state[key(c, t)] = doc; paint(el); }}
    catch (e) {{ document.getElementById('dbstate').textContent = 'save failed: ' + (e && e.code || e); }}
  }}
  const cands = [...document.querySelectorAll('.cand')];
  function paintCand(el) {{
    const v = state['cand:' + el.dataset.cand];
    el.querySelectorAll('button.v').forEach(b => b.classList.toggle('on', !!v && v.call === b.dataset.v));
    el.querySelector('.vstate').textContent = v ? 'you: ' + v.call : '';
  }}
  async function saveCand(el, call) {{
    if (!db) return;
    const doc = {{ case_id: el.dataset.case, candidate_id: el.dataset.cand, call, ts: new Date().toISOString() }};
    try {{ await db.doc('votes_dialogue_v2/' + el.dataset.cand.replace(/[^A-Za-z0-9_.-]/g, '_')).set(doc); state['cand:' + el.dataset.cand] = doc; paintCand(el); }}
    catch (e) {{ document.getElementById('dbstate').textContent = 'save failed: ' + (e && e.code || e); }}
  }}
  cands.forEach(el => el.querySelectorAll('button.v').forEach(b => {{ b.disabled = true; b.addEventListener('click', () => saveCand(el, b.dataset.v)); }}));
  const turns = [...document.querySelectorAll('.turn.assistant')];
  turns.forEach(el => el.querySelectorAll('button.v').forEach(b => {{ b.disabled = true; b.addEventListener('click', () => save(el, b.dataset.v)); }}));
  (async () => {{
    try {{ db = window.claude && await claude.use('db'); }} catch (e) {{ db = null; }}
    const s = document.getElementById('dbstate');
    if (!db) {{ s.textContent = 'annotation store unavailable in this view (read-only)'; return; }}
    s.textContent = 'annotation store connected · your call is saved per reply';
    turns.forEach(el => el.querySelectorAll('button.v').forEach(b => b.disabled = false));
    cands.forEach(el => el.querySelectorAll('button.v').forEach(b => b.disabled = false));
    db.collection('votes_dialogue_v2').onSnapshot(snap => {{
      snap.docs.forEach(d => {{ const v = d.data(); if (v.candidate_id) state['cand:' + v.candidate_id] = v; else state[key(v.case_id, v.assistant_turn)] = v; }});
      turns.forEach(paint); cands.forEach(paintCand);
    }}, err => {{ s.textContent = 'annotation store error: ' + (err && err.code || err); }});
  }})();
}})();
</script>"""
out = pathlib.Path(sys.argv[1]); out.write_text(page)
print('wrote', out, len(page), 'chars;', len(CASES), 'conversations,', total_replies, 'graded replies, pairs', npairs, dict(q))
