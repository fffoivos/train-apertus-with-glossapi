#!/usr/bin/env python3
"""Keep / Adapt / Drop reader: the judge's verdict and reason on sampled rows, per block, one tab per disposition.
Usage: python3 cluster/judge_reasons_page.py <out.html> <n_per_tab> <block1> [block2 ...]   (reads ~/sft_annot exports + labels; Sol routed labels override Luna)"""
import json, sys, html, random, os, collections
OUT, N = sys.argv[1], int(sys.argv[2]); BLOCKS = sys.argv[3:]; A = os.path.expanduser('~/sft_annot'); E = html.escape; random.seed(7)
NAMES = {'dolci_science': 'Science (Sol)', 'nemotron_chat_a': 'Nemotron chat A', 'dolci_safety': 'Dolci safety', 'dolci_chat': 'OpenAssistant chat',
         'smoltalk2_multilingual': 'Multilingual', 'dolci_tooluse_sample3k': 'Tool-use sample', 'greek_ours': 'Our Greek set', 'greek_rewrite': 'Greek rewriting set',
         'nemotron_chat_b': 'Nemotron chat B', 'dolci_precise_if_20k': 'Precise IF (Sol)', 'dolci_code_algo_20k': 'Coding (Sol)'}
def load(p):
    d = {}
    if os.path.exists(p):
        for l in open(p):
            j = json.loads(l)
            if j.get('disposition'): d[j['id']] = j
    return d
data = {}
for b in BLOCKS:
    luna = load(f'{A}/labels/{b}.labels.jsonl'); sol = load(f'{A}/labels/{b}.sol.jsonl'); sol.update(load(f'{A}/labels/{b}.sol_routed.jsonl'))
    final = {}
    for i, j in luna.items():
        if i in sol: k = dict(sol[i]); k['routed_from'] = j.get('disposition'); final[i] = k
        else: final[i] = j
    by = collections.defaultdict(list)
    for i, j in final.items(): by[j['disposition']].append(i)
    counts = {d: len(v) for d, v in by.items()}
    picks = {d: set(random.sample(v, min(N, len(v)))) for d, v in by.items()}
    want = set().union(*picks.values()); rows = {}
    with open(f'{A}/core_export/{b}.jsonl') as f:
        for l in f:
            if not want: break
            j = json.loads(l)
            if j['id'] in want:
                want.discard(j['id']); u = [t.get('content') or '' for t in j['turns'] if t['role'] == 'user']; a = [t.get('content') or '' for t in j['turns'] if t['role'] == 'assistant']
                rows[j['id']] = dict(user=(u[0] if u else '')[:700], asst=' ⏎⏎ '.join(a)[:1600], n_asst=len(a))
    facets = {}
    for d, ids in by.items():
        facets[d] = dict(skill=collections.Counter(final[i].get('skill') or '—' for i in ids).most_common(6), frame=collections.Counter(final[i].get('frame_type') or '—' for i in ids).most_common(5),
                         quality=sorted(collections.Counter(str(final[i].get('quality')) for i in ids).items()), mannerism=sum(1 for i in ids if final[i].get('mannerism')),
                         routed=sum(1 for i in ids if final[i].get('routed_from')))
    tabs = {}
    for d in ('keep', 'adapt', 'drop'):
        tabs[d] = [dict(id=i, judge=final[i].get('judge') or '', why=final[i].get('why') or '', note=final[i].get('adapt_note') or '', skill=final[i].get('skill'), frame=final[i].get('frame_type'),
                        quality=final[i].get('quality'), mannerism=bool(final[i].get('mannerism')), routed=final[i].get('routed_from'), **rows.get(i, dict(user='', asst='(export row not found)', n_asst=0)))
                   for i in sorted(picks.get(d, []))]
    data[b] = dict(name=NAMES.get(b, b), counts=counts, facets=facets, tabs=tabs)
css = """
:root{--ground:#eceef2;--paper:#ffffff;--ink:#1b1f27;--muted:#636b79;--rule:#d2d7df;--accent:#3b4f8a;--user:#f3f5f8;
--keep:#2b7a58;--keep-bg:#e6f3ec;--adapt:#a86c14;--adapt-bg:#f9efdc;--drop:#b13b3b;--drop-bg:#f8e6e6;
--display:"Fraunces",Georgia,"Times New Roman",serif;--sans:"IBM Plex Sans",-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--ground:#15181e;--paper:#1e2229;--ink:#e6e8ec;--muted:#9aa3b2;--rule:#333a46;--accent:#9fb0e6;--user:#252a33;
--keep:#7fcaa4;--keep-bg:#1f3a2e;--adapt:#e3b46a;--adapt-bg:#3d3120;--drop:#ee8f8f;--drop-bg:#40272a}}
:root[data-theme="dark"]{--ground:#15181e;--paper:#1e2229;--ink:#e6e8ec;--muted:#9aa3b2;--rule:#333a46;--accent:#9fb0e6;--user:#252a33;
--keep:#7fcaa4;--keep-bg:#1f3a2e;--adapt:#e3b46a;--adapt-bg:#3d3120;--drop:#ee8f8f;--drop-bg:#40272a}
*{box-sizing:border-box}body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.5}
header{padding:28px 24px 0;max-width:1100px;margin:0 auto}h1{font-family:var(--display);font-weight:500;font-size:34px;margin:0 0 6px;letter-spacing:-.01em;text-wrap:balance}
.lede{color:var(--muted);max-width:70ch;margin:0 0 18px}
.pills{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px}.pill{border:1px solid var(--rule);background:var(--paper);color:var(--ink);border-radius:999px;padding:6px 14px;font:inherit;font-size:14px;cursor:pointer}
.pill[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}.pill:focus-visible,.tab:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.tabs{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border:1px solid var(--rule);border-radius:10px;overflow:hidden;background:var(--paper);max-width:1100px;margin:0 auto}
.tab{border:0;background:transparent;font:inherit;padding:14px 12px;cursor:pointer;color:var(--muted);text-align:left;border-right:1px solid var(--rule)}.tab:last-child{border-right:0}
.tab .n{display:block;font-family:var(--display);font-size:26px;color:var(--ink);font-variant-numeric:tabular-nums}.tab .lbl{font-size:12px;letter-spacing:.08em;text-transform:uppercase}
.tab[aria-selected="true"]{box-shadow:inset 0 -4px 0 var(--tabc);color:var(--ink)}
main{max-width:1100px;margin:0 auto;padding:18px 24px 60px}
.facets{display:flex;flex-wrap:wrap;gap:8px 22px;color:var(--muted);font-size:13px;margin:0 0 16px;padding:12px 16px;background:var(--paper);border:1px solid var(--rule);border-radius:10px}
.facets b{color:var(--ink);font-weight:600}.facets .k{font-family:var(--mono);font-size:12px}
article{background:var(--paper);border:1px solid var(--rule);border-radius:10px;margin-bottom:16px;overflow:hidden}
.verdict{padding:12px 18px;border-left:5px solid var(--vc);background:var(--vbg);display:grid;gap:4px}
.verdict .why{font-size:15.5px;font-weight:500}.verdict .note{color:var(--muted);font-size:13.5px}
.meta{font-family:var(--mono);font-size:11.5px;color:var(--muted);display:flex;flex-wrap:wrap;gap:4px 14px}
.turn{padding:12px 18px;white-space:pre-wrap;overflow-wrap:anywhere;max-width:82ch}.turn.user{background:var(--user);color:var(--muted);font-size:14px;max-width:none}
.role{font-family:var(--mono);font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
.empty{color:var(--muted);padding:24px;text-align:center}
@media (prefers-reduced-motion:no-preference){.tab,.pill{transition:background .15s,color .15s}}
"""
out = ['<title>Keep, Adapt, Drop</title>', '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500&family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono&display=swap">', f'<style>{css}</style>',
       '<header><h1>Keep, Adapt, Drop</h1><p class="lede">Each row the judge saw ends in one of three verdicts. Pick a block, then a verdict, and read the judge\'s stated reason next to the row it judged. Where Sol re-judged a row Luna had labelled technical, the card says so and shows Sol\'s verdict.</p>',
       '<div class="pills" role="group" aria-label="block">' + ''.join(f'<button class="pill" data-block="{E(b)}" aria-pressed="{"true" if k == 0 else "false"}">{E(data[b]["name"])} · {sum(data[b]["counts"].values()):,}</button>' for k, b in enumerate(BLOCKS)) + '</div></header>',
       '<div class="tabs" role="tablist">' + ''.join(f'<button class="tab" role="tab" data-tab="{d}" aria-selected="{"true" if d == "keep" else "false"}" style="--tabc:var(--{d})"><span class="n" id="n-{d}">0</span><span class="lbl">{d}</span></button>' for d in ('keep', 'adapt', 'drop')) + '</div>',
       '<main><div class="facets" id="facets"></div><div id="cards"></div></main>',
       '<script>const DATA=' + json.dumps(data, ensure_ascii=False).replace('</', '<\\/') + ';',
       r"""
const E=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let block=Object.keys(DATA)[0],tab='keep';
function render(){const d=DATA[block];for(const t of ['keep','adapt','drop']){document.getElementById('n-'+t).textContent=(d.counts[t]||0).toLocaleString();}
document.querySelectorAll('.tab').forEach(b=>b.setAttribute('aria-selected',b.dataset.tab===tab));document.querySelectorAll('.pill').forEach(b=>b.setAttribute('aria-pressed',b.dataset.block===block));
const f=d.facets[tab];const fx=document.getElementById('facets');
fx.innerHTML=f?`<span><b>${E(tab)}</b> ${(d.counts[tab]||0).toLocaleString()} of ${Object.values(d.counts).reduce((a,b)=>a+b,0).toLocaleString()} rows</span><span>skill: ${f.skill.map(([k,v])=>`<span class="k">${E(k)}</span> ${v.toLocaleString()}`).join(' · ')}</span><span>frame: ${f.frame.map(([k,v])=>`<span class="k">${E(k)}</span> ${v.toLocaleString()}`).join(' · ')}</span><span>quality: ${f.quality.map(([k,v])=>`<span class="k">${E(k)}</span> ${v.toLocaleString()}`).join(' · ')}</span><span>mannerism flagged: ${f.mannerism.toLocaleString()}</span><span>Sol-routed: ${f.routed.toLocaleString()}</span>`:'';
const rows=d.tabs[tab]||[];const c=document.getElementById('cards');
c.innerHTML=rows.length?rows.map(r=>`<article style="--vc:var(--${tab});--vbg:var(--${tab}-bg)"><div class="verdict"><div class="why">${E(r.why)||'<i>no reason given</i>'}</div>${r.note?`<div class="note">adapt note: ${E(r.note)}</div>`:''}<div class="meta"><span>${E(r.id)}</span><span>judge ${E(r.judge)}${r.routed?` (Luna said ${E(r.routed)}, Sol re-judged)`:''}</span><span>skill ${E(r.skill)}</span><span>frame ${E(r.frame)}</span><span>quality ${E(r.quality)}</span><span>mannerism ${r.mannerism?'yes':'no'}</span><span>${r.n_asst} assistant turn${r.n_asst==1?'':'s'}</span></div></div><div class="turn user"><div class="role">user</div>${E(r.user)}</div><div class="turn"><div class="role">assistant${r.asst.length>=1600?' (first 1,600 characters)':''}</div>${E(r.asst)}</div></article>`).join(''):'<p class="empty">No rows with this verdict in this block.</p>';
window.scrollTo({top:0});}
document.querySelectorAll('.pill').forEach(b=>b.addEventListener('click',()=>{block=b.dataset.block;render();}));
document.querySelectorAll('.tab').forEach(b=>b.addEventListener('click',()=>{tab=b.dataset.tab;render();}));
try{const s=JSON.parse(localStorage.getItem('kad')||'{}');if(DATA[s.block])block=s.block;if(['keep','adapt','drop'].includes(s.tab))tab=s.tab;}catch(e){}
const _r=render;render=function(){_r();try{localStorage.setItem('kad',JSON.stringify({block,tab}));}catch(e){}};render();
</script>"""]
open(OUT, 'w').write('\n'.join(out)); print('wrote', OUT, os.path.getsize(OUT) // 1024, 'KB')
