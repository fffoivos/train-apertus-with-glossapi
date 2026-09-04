#!/usr/bin/env python3
"""Owner review page for the round-two blind reading: every prompt, every answer, Claude's scores, labels revealed."""
import json,html,re,sys,statistics as st
root='results/reading2'; out=sys.argv[1]
key=json.load(open(f'{root}/blind_key.json')); flags=json.load(open(f'{root}/prompt_flags.json')); summ=json.load(open(f'{root}/summary.json'))
prompts={f"{i:02d}":json.loads(l) for i,l in enumerate(open('evals/dev/prompts/reading40.jsonl'),1)}
NAMES={'E0b':'base model (no SFT)','E1_lr1e-5_ep1':'lr 1e-5 · epoch 1','E1_lr1e-5_ep2':'PICK · lr 1e-5 · epoch 2','E1_lr1e-5_ep3':'lr 1e-5 · epoch 3',
 'E1_lr5e-6_ep1':'lr 5e-6 · epoch 1','E1_lr5e-6_ep2':'lr 5e-6 · epoch 2','E1_lr5e-6_ep3':'lr 5e-6 · epoch 3','E1_cos_ep2':'seed 43 replicate · epoch 2',
 'E1_cos_s44_ep2':'seed 44 replicate · epoch 2','E1last_ep2':'terminal CPT checkpoint · epoch 2','E2_cos_ep2':'Greek + paired English · epoch 2',
 'E3_cos_ep2':'Greek + adapted imports · epoch 2','E3prime_cos_ep2':'Greek + raw imports · epoch 2'}
ORDER=list(NAMES)
gen={r:{json.loads(l)['prompt_id']:json.loads(l) for l in open(f'results/{r}/dev/reading40_gen.jsonl')} for r in ORDER}
E=lambda t: html.escape(t).replace('\ufffd','&#xFFFD;')
css="""
:root{--bg:#f3f4f2;--paper:#ffffff;--ink:#1c1f1a;--muted:#5f645b;--rule:#d6d9d2;--accent:#2f6b4f;--bad:#a23b2a;--good:#2f6b4f;--band:#e9ede6;--pick:#fff4d6;
--sans:"IBM Plex Sans",-apple-system,Segoe UI,Helvetica,Arial,sans-serif;--serif:"Source Serif 4",Georgia,serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#141614;--paper:#1c1f1c;--ink:#e6e8e2;--muted:#a3a89d;--rule:#363a34;--accent:#8fc7a9;--bad:#e08a7a;--good:#8fc7a9;--band:#242823;--pick:#3a3320}}
:root[data-theme="dark"]{--bg:#141614;--paper:#1c1f1c;--ink:#e6e8e2;--muted:#a3a89d;--rule:#363a34;--accent:#8fc7a9;--bad:#e08a7a;--good:#8fc7a9;--band:#242823;--pick:#3a3320}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.5;margin:0}
main{max-width:1180px;margin:0 auto;padding:32px 24px 80px}
h1{font-family:var(--serif);font-size:32px;margin:0 0 4px;text-wrap:balance}
h2{font-family:var(--serif);font-size:22px;margin:40px 0 8px;border-bottom:1px solid var(--rule);padding-bottom:6px}
h3{font-size:15px;margin:18px 0 6px}
p,li{max-width:80ch}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}
.tw{overflow-x:auto;background:var(--paper);border:1px solid var(--rule);margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}
th{background:var(--band);text-align:left;padding:6px 9px;font-weight:600;border-bottom:1px solid var(--rule);white-space:nowrap}
td{padding:5px 9px;border-bottom:1px solid var(--rule);vertical-align:top}
tr.pick td{background:var(--pick)}
details{background:var(--paper);border:1px solid var(--rule);margin:14px 0;padding:0 16px}
summary{cursor:pointer;padding:12px 0;font-weight:600}
summary .cat{font-family:var(--mono);font-size:12px;color:var(--muted);font-weight:400;margin-left:8px}
.prompt{background:var(--band);padding:10px 14px;border-radius:4px;white-space:pre-wrap;font-size:14px;margin:6px 0 14px}
.ans{border-top:1px solid var(--rule);padding:10px 0 14px}
.ans .hd{display:flex;gap:12px;flex-wrap:wrap;align-items:baseline;margin-bottom:6px}
.ans .lab{font-weight:600}
.ans .lab.pick{background:var(--pick);padding:0 6px;border-radius:3px}
.sc{font-family:var(--mono);font-size:12px;color:var(--muted)}
.flag{font-family:var(--mono);font-size:12px;padding:1px 6px;border-radius:3px;border:1px solid var(--rule)}
.flag.bad{color:var(--bad);border-color:var(--bad)}
.flag.good{color:var(--good);border-color:var(--good)}
.txt{white-space:pre-wrap;font-size:14px;max-height:22em;overflow:auto;background:var(--paper);padding:6px 10px;border-left:3px solid var(--rule)}
.note{font-size:13px;color:var(--muted);margin-top:6px}
.excl{color:var(--bad);font-weight:600}
"""
def scoretab(title,d):
    cols=['answers','greek','stops','constraint_ok','warmth','command','mannerism','language_ok']
    s=f'<h3>{E(title)}</h3><div class="tw"><table><tr><th>run</th><th>n</th>'+''.join(f'<th>{c}</th>' for c in cols)+'</tr>'
    for run,v in d.items():
        cls=' class="pick"' if run=='E1_lr1e-5_ep2' else ''
        s+=f'<tr{cls}><td>{E(NAMES[run])}</td><td>{v["n"]}</td>'+''.join('<td>—</td>' if v[c] is None else f'<td>{v[c]:.2f}</td>' for c in cols)+'</tr>'
    return s+'</table></div>'
h=[f'<title>Reading Round Two</title><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap"><style>{css}</style><main>']
h.append('<div class="eyebrow">train-apertus-with-glossapi · subproject 12 · blind reading, round two · scored 2026-09-04</div><h1>Reading Round Two</h1>')
h.append('<p>Claude scored all 13 runs on all 40 prompts blind: labels hidden, answer order shuffled per prompt. Labels were revealed only after every score was written. This page is for your review of those scores. Scales: <b>answers</b>, <b>greek</b> (quality of the prompt\'s language) and <b>warmth</b> are 1–5; <b>stops</b>, <b>constraint_ok</b>, <b>language_ok</b>, <b>command</b> and <b>mannerism</b> are 0/1. <b>command</b> = an imperative-mood order the user did not ask for (requested steps do not count). <b>mannerism</b> = chatbot openers, closers or exclamation-mark enthusiasm; the quoted phrase is shown. Prompt 15 is excluded from the averages: its user message contains its own answer, and every fine-tuned run copies it.</p>')
h.append('<h2>Averages per run</h2>'+scoretab('All 39 prompts',summ['all_39'])+scoretab('Greek prompts (30)',summ['greek_30'])+scoretab('English, French, German prompts (9)',summ['nonGreek_9']))
nf=summ['rater_noise_floor_seed_pair']; h.append('<p><b>Rater noise floor</b> (the two seed replicates are the same recipe, so their gap is my own noise): '+', '.join(f'{k} {v}' for k,v in nf.items())+'. Differences smaller than these are not evidence.</p>')
h.append('<h2>Every prompt, every answer</h2><p>Open a prompt to see the 13 answers in the order I read them, with the run label now revealed. The pick is highlighted.</p>')
for n in sorted(key):
    p=prompts[n]; k=key[n]; sc=json.load(open(f'{root}/scores/prompt_{n}.json'))
    ex=f' <span class="excl">EXCLUDED: {E(flags[n])}</span>' if n in flags else ''
    h.append(f'<details><summary>Prompt {n}<span class="cat">{E(p["category"])} · {p["language"]}</span>{ex}</summary>')
    h.append('<div class="prompt">'+'\n\n'.join(f'<b>{m["role"].upper()}:</b> {E(m["content"])}' for m in p['messages'])+'</div>')
    for letter,run in k['map'].items():
        s=sc[letter]; row=gen[run][p['prompt_id']]
        lab=f'<span class="lab{" pick" if run=="E1_lr1e-5_ep2" else ""}">{letter} → {E(NAMES[run])}</span>'
        flags_=[]
        if s['command']: flags_.append('<span class="flag bad">command</span>')
        if s['mannerism']: flags_.append(f'<span class="flag bad">mannerism: {E(s["mannerism_quote"])}</span>')
        if not s['stops']: flags_.append('<span class="flag bad">no clean stop</span>')
        if not s['language_ok']: flags_.append('<span class="flag bad">language leak</span>')
        if s['constraint_ok']==0: flags_.append('<span class="flag bad">constraint missed</span>')
        if s['constraint_ok']==1: flags_.append('<span class="flag good">constraint met</span>')
        scs=f'<span class="sc">answers {s["answers"]} · greek {s["greek"]} · warmth {s["warmth"]} · {row.get("stop_reason","?")} · {row.get("generated_tokens","?")} tok</span>'
        h.append(f'<div class="ans"><div class="hd">{lab}{scs}{" ".join(flags_)}</div><div class="txt">{E(row["text"])}</div><div class="note">{E(s["note"])}</div></div>')
    h.append('</details>')
h.append('</main>')
open(out,'w').write('\n'.join(h)); print('wrote',out,len('\n'.join(h)),'chars')
