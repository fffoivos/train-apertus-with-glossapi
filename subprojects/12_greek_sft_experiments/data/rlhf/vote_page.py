#!/usr/bin/env python3
"""Voting page: per prompt, the candidate replies side by side (columns, judge order) with Sol's verdict, tags and note; the owner records
agreement or a different pick, saved in the artifact's db (doc votes/<prompt_id>). Usage:
python3 data/rlhf/vote_page.py <out.html> --prompts P.jsonl --samples S.jsonl [--samples2 S2.jsonl] --judged J.jsonl [--judged2 J2.jsonl] [--title ...] [--note ...]"""
import json, html, argparse, collections, sys
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--prompts', required=True); ap.add_argument('--samples', required=True, action='append'); ap.add_argument('--samples2'); ap.add_argument('--judged', required=True, action='append'); ap.add_argument('--judged2')
ap.add_argument('--pairs', help='round3_pairs.jsonl: marks the chosen and rejected reply of each accepted pair'); ap.add_argument('--labels', action='store_true', help='show the prompt labels and the seed behind it'); ap.add_argument('--max-replies', type=int, default=0, help='columns per prompt (0 = every judged reply); the pair is always shown')
ap.add_argument('--title', default='Greek RLHF Votes'); ap.add_argument('--note', default=''); a = ap.parse_args()
E = html.escape
P = [json.loads(l) for l in open(a.prompts) if l.strip()]
S = collections.defaultdict(dict)
for f, off in [(x, 0) for x in a.samples] + ([(a.samples2, 4)] if a.samples2 else []):
    if not f: continue
    for l in open(f):
        if l.strip():
            s = json.loads(l)
            if s.get('k', -1) >= 0: S[s['id']][s['k'] + off] = s['text']
V = collections.defaultdict(dict); ORDER = collections.defaultdict(list); META = {}
PAIR = {x['id']: x['pair'] for x in ([json.loads(l) for l in open(a.pairs) if l.strip()] if a.pairs else []) if x.get('pair')}
for f, off in [(x, 0) for x in a.judged] + ([(a.judged2, 4)] if a.judged2 else []):
    if not f: continue
    for l in open(f):
        if not l.strip(): continue
        j = json.loads(l)
        if j.get('error') or j.get('pass', 1) != 1: continue
        for k, c in j['by_k'].items(): V[j['id']][int(k) + off] = c
        ORDER[j['id']] += [k + off for k in j['ranking_k']]; META.setdefault(j['id'], j.get('rubric_sha'))
cards = []
for p in P:
    pid = p['id']; order = list(dict.fromkeys(ORDER.get(pid) or sorted(S[pid])))      # a reply judged twice (self-agreement) is one column
    order = sorted(order, key=lambda k: {'reinforce': 0, 'neutral': 1, 'discourage': 2}.get((V[pid].get(k) or {}).get('verdict'), 3))
    hidden = 0
    if a.max_replies and len(order) > a.max_replies:                                  # keep the pair visible whatever the cap
        pr = PAIR.get(pid) or {}; must = [k for k in (pr.get('chosen_k'), pr.get('rejected_k')) if k is not None]
        head = [k for k in order if k not in must][: max(0, a.max_replies - len(must))]
        hidden = len(order) - len(head) - len(must); order = [k for k in order if k in must or k in head]
    conv = ''.join(f"<div class='msg {m['role']}'><span class='role'>{E(m['role'])}</span><div>{E(m['content'])}</div></div>" for m in p['messages'])
    cols = []
    for pos, k in enumerate(order):
        c = V[pid].get(k, {}); vd = c.get('verdict') or '—'; tags = ''.join(f"<span class='tag'>{E(t)}</span>" for t in c.get('issues', []))
        pr = PAIR.get(pid) or {}
        role = " · chosen" if pr.get('chosen_k') == k else (" · rejected" if pr.get('rejected_k') == k else '')
        cols.append(f"<div class='col{' pairpick' if role else ''}' data-k='{k}'><div class='col-head'><span class='pos'>{pos+1}</span><span class='lab'>reply {k+1}{role}</span><span class='vd {E(vd)}'>{E(vd)}</span></div><div class='tags'>{tags}</div><div class='note'>{E(c.get('note',''))}</div><pre class='text'>{E(S[pid].get(k,'(missing)'))}</pre><button class='pick' data-pid='{E(pid)}' data-k='{k}'>my best is this one</button></div>")
    more = f"<p class='note' style='padding:0 14px 10px'>{hidden} further judged replies are not shown here; every reply and verdict is in round3_samples.jsonl and the judged files.</p>" if hidden else ''
    sol_best = order[0] if order else -1
    keys = ('label', 'expected', 'level', 'profile', 'move', 'task_type', 'post_kind') + (('purpose', 'subtype', 'language', 'difficulty', 'detail', 'register', 'attitude', 'maths_content', 'scenario') if a.labels else ())
    meta = ' · '.join(E(f'{k}: {v}') for k, v in p.items() if k in keys and v)
    story = f"<details class='seed'><summary>the person the generator imagined</summary><div>{E(p.get('story'))}</div></details>" if (a.labels and p.get('story')) else ''
    cards.append(f"""<section class='card' id='c-{E(pid)}' data-pid='{E(pid)}' data-solbest='{sol_best}'>
<div class='card-head'><span class='pid'>{E(pid)}</span><span class='slice'>{E(p.get('slice') or p.get('purpose') or '')}</span><span class='muted'>{E(p.get('source',''))[:110]}{(' · ' + meta) if meta else ''}</span><span class='vote-state' id='vs-{E(pid)}'>no vote yet</span></div>
<div class='conv'>{conv}</div>{story}
<div class='cols'>{''.join(cols)}</div>{more}
<div class='vote'><button class='agree' data-pid='{E(pid)}'>agree with Sol (best = sample {sol_best+1})</button><button class='none' data-pid='{E(pid)}'>none is good</button><input class='vnote' data-pid='{E(pid)}' placeholder='note (optional)' /><button class='savenote' data-pid='{E(pid)}'>save note</button></div>
</section>""")
page = f'''<title>{E(a.title)}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400&display=swap">
<style>
:root {{ --bg:#F4F6F8; --surface:#FFFFFF; --ink:#1B222E; --muted:#5B6674; --line:#D6DCE4; --accent:#1A6C8C; --accent-ink:#125066; --accent-soft:#E2EFF4; --warn:#9A5A10; --warn-soft:#F7ECDC; --good:#3D6B2E; --good-soft:#E5F0E0; --code-bg:#F0F3F6; --user:#EEF3F7; --asst:#F7F5EE; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#11161C; --surface:#181E26; --ink:#E4E9F0; --muted:#98A3B2; --line:#2A333F; --accent:#63B4D0; --accent-ink:#8FCCE0; --accent-soft:#1B303B; --warn:#E2A65E; --warn-soft:#3A2A16; --good:#8FC77A; --good-soft:#1F2F1A; --code-bg:#0E1319; --user:#1C2632; --asst:#26241C; }} }}
:root[data-theme="dark"] {{ --bg:#11161C; --surface:#181E26; --ink:#E4E9F0; --muted:#98A3B2; --line:#2A333F; --accent:#63B4D0; --accent-ink:#8FCCE0; --accent-soft:#1B303B; --warn:#E2A65E; --warn-soft:#3A2A16; --good:#8FC77A; --good-soft:#1F2F1A; --code-bg:#0E1319; --user:#1C2632; --asst:#26241C; }}
* {{ box-sizing:border-box; }} body {{ background:var(--bg); color:var(--ink); font-family:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif; font-size:14.5px; line-height:1.5; padding-inline:clamp(16px,2vw,28px); padding-block:24px 64px; }}
h1 {{ font-family:"Source Serif 4",Georgia,serif; font-weight:600; font-size:clamp(24px,3vw,32px); margin:4px 0 6px; }} .eyebrow {{ font-size:12px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); font-weight:600; }} .lede {{ color:var(--muted); max-width:80ch; margin:0 0 10px; }}
.summary {{ display:flex; flex-wrap:wrap; gap:8px 18px; align-items:baseline; background:var(--surface); border:1px solid var(--line); padding:10px 14px; margin:0 0 16px; font-size:14px; }} .summary b {{ font-family:"Source Serif 4",Georgia,serif; font-size:20px; }} .summary .dbstate {{ margin-left:auto; color:var(--muted); font-size:12.5px; }}
.card {{ background:var(--surface); border:1px solid var(--line); margin:0 0 14px; }} .card-head {{ display:flex; flex-wrap:wrap; gap:6px 12px; align-items:baseline; padding:9px 14px; border-bottom:1px solid var(--line); }} .pid {{ font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:12px; color:var(--accent-ink); }} .slice {{ font-size:11px; text-transform:uppercase; letter-spacing:.05em; font-weight:600; color:var(--muted); }} .muted {{ color:var(--muted); font-size:12.5px; }} .vote-state {{ margin-left:auto; font-size:12.5px; font-weight:600; color:var(--accent-ink); }}
.conv {{ padding:8px 14px; display:grid; gap:6px; }} .msg {{ display:grid; grid-template-columns:68px 1fr; gap:8px; padding:6px 10px; border:1px solid var(--line); white-space:pre-wrap; font-size:13.5px; }} .msg.user {{ background:var(--user); }} .msg.assistant {{ background:var(--asst); }} .msg .role {{ font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); font-weight:600; }}
.cols {{ display:flex; gap:10px; overflow-x:auto; padding:10px 14px; align-items:stretch; }} .col {{ flex:0 0 340px; max-width:100%; border:1px solid var(--line); background:var(--bg); display:flex; flex-direction:column; }} .col.chosen {{ outline:2px solid var(--accent); }} .col.pairpick {{ box-shadow:inset 0 3px 0 var(--good); }}
details.seed {{ padding:0 14px 8px; font-size:12.5px; color:var(--muted); }} details.seed summary {{ cursor:pointer; }} .col-head {{ display:flex; gap:8px; align-items:center; padding:6px 10px; border-bottom:1px solid var(--line); }} .pos {{ font-family:"Source Serif 4",Georgia,serif; font-weight:600; font-size:18px; color:var(--accent-ink); }} .lab {{ font-size:12px; color:var(--muted); }}
.vd {{ margin-left:auto; font-size:11px; letter-spacing:.05em; text-transform:uppercase; font-weight:600; padding:2px 7px; }} .vd.reinforce {{ background:var(--good-soft); color:var(--good); }} .vd.discourage {{ background:var(--warn-soft); color:var(--warn); }} .vd.neutral {{ background:var(--code-bg); color:var(--muted); }}
.tags {{ display:flex; flex-wrap:wrap; gap:4px; padding:6px 10px 0; }} .tag {{ font-size:11px; background:var(--code-bg); color:var(--muted); padding:1px 6px; }} .note {{ font-size:12.5px; color:var(--muted); padding:6px 10px; }} pre.text {{ margin:0; padding:8px 10px; white-space:pre-wrap; font-family:inherit; font-size:13.5px; background:var(--surface); border-top:1px solid var(--line); max-height:46vh; overflow:auto; flex:1; }}
button {{ font:inherit; font-size:13px; padding:6px 10px; border:1px solid var(--line); background:var(--surface); color:var(--ink); cursor:pointer; }} button:hover {{ border-color:var(--accent); }} button.pick {{ margin:8px 10px 10px; }} button.on {{ background:var(--accent-soft); border-color:var(--accent); color:var(--accent-ink); }} button:disabled {{ opacity:.5; cursor:default; }}
.vote {{ display:flex; flex-wrap:wrap; gap:8px; padding:8px 14px 12px; border-top:1px solid var(--line); align-items:center; }} .vnote {{ font:inherit; font-size:13px; padding:6px 8px; border:1px solid var(--line); background:var(--bg); color:var(--ink); min-width:240px; flex:1; }}
@media (max-width:560px) {{ .msg {{ grid-template-columns:1fr; }} .col {{ flex-basis:88vw; }} }}
</style>
<div class="eyebrow">το Ελληνικό Apertus · RLHF votes · judge rubric {E(str(next(iter(META.values()), '')) or '—')}</div>
<h1>{E(a.title)}</h1>
<p class="lede">Each prompt, then its candidate replies side by side in the order Sol ranked them, with Sol's verdict, issue tags and note. Vote per prompt: agree with Sol, pick a different best, or none is good; a note is optional. Votes are saved to this page's database and read back for calibration.</p>
{('<p class="lede">' + E(a.note) + '</p>') if a.note else ''}
<div class="summary"><span>voted <b id="n-voted">0</b>/{len(P)}</span><span>agree <b id="n-agree">0</b></span><span>different best <b id="n-diff">0</b></span><span>none good <b id="n-none">0</b></span><span class="dbstate" id="dbstate">connecting to the vote store…</span></div>
{''.join(cards)}
<script>
(async function() {{
  const cards = [...document.querySelectorAll('.card')]; const state = {{}};
  function paint(pid, v) {{
    const card = document.getElementById('c-' + pid); if (!card) return; const vs = document.getElementById('vs-' + pid);
    card.querySelectorAll('.col').forEach(c => c.classList.toggle('chosen', v && v.choice === 'pick' && String(v.best_k) === c.dataset.k));
    card.querySelectorAll('button.agree').forEach(b => b.classList.toggle('on', v && v.choice === 'agree')); card.querySelectorAll('button.none').forEach(b => b.classList.toggle('on', v && v.choice === 'none'));
    card.querySelectorAll('button.pick').forEach(b => b.classList.toggle('on', v && v.choice === 'pick' && String(v.best_k) === b.dataset.k));
    if (v && v.note) card.querySelector('.vnote').value = v.note;
    vs.textContent = !v ? 'no vote yet' : v.choice === 'agree' ? 'you agree with Sol' : v.choice === 'none' ? 'you: none is good' : 'you: best is sample ' + (v.best_k + 1);
  }}
  function summary() {{ const vs = Object.values(state); document.getElementById('n-voted').textContent = vs.length; document.getElementById('n-agree').textContent = vs.filter(v => v.choice === 'agree').length; document.getElementById('n-diff').textContent = vs.filter(v => v.choice === 'pick').length; document.getElementById('n-none').textContent = vs.filter(v => v.choice === 'none').length; }}
  const db = await claude.use('db'); const dbstate = document.getElementById('dbstate');
  if (!db) {{ dbstate.textContent = 'vote store unavailable in this view (read-only)'; document.querySelectorAll('button').forEach(b => b.disabled = true); return; }}
  dbstate.textContent = 'vote store connected';
  db.collection('votes').onSnapshot(snap => {{ snap.docs.forEach(d => {{ state[d.id] = d.data(); paint(d.id, state[d.id]); }}); summary(); }}, err => {{ dbstate.textContent = 'vote store error: ' + (err && err.code || err); }});
  async function save(pid, patch) {{
    const card = document.getElementById('c-' + pid); const prev = state[pid] || {{}}; const doc = Object.assign({{}}, prev, patch, {{ pid, sol_best_k: Number(card.dataset.solbest), rubric: '{E(str(next(iter(META.values()), "")))}', ts: new Date().toISOString() }});
    try {{ await db.doc('votes/' + pid).set(doc); state[pid] = doc; paint(pid, doc); summary(); }} catch (e) {{ dbstate.textContent = 'save failed: ' + (e && e.code || e); }}
  }}
  document.querySelectorAll('button.agree').forEach(b => b.addEventListener('click', () => save(b.dataset.pid, {{ choice: 'agree', best_k: Number(document.getElementById('c-' + b.dataset.pid).dataset.solbest) }})));
  document.querySelectorAll('button.none').forEach(b => b.addEventListener('click', () => save(b.dataset.pid, {{ choice: 'none', best_k: -1 }})));
  document.querySelectorAll('button.pick').forEach(b => b.addEventListener('click', () => save(b.dataset.pid, {{ choice: 'pick', best_k: Number(b.dataset.k) }})));
  document.querySelectorAll('button.savenote').forEach(b => b.addEventListener('click', () => save(b.dataset.pid, {{ note: document.getElementById('c-' + b.dataset.pid).querySelector('.vnote').value.trim() }})));
}})();
</script>'''
open(a.out, 'w').write(page); print('wrote', a.out, len(page), 'chars,', len(cards), 'prompts')
