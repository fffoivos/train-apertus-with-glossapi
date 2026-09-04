#!/usr/bin/env python3
"""Greek IFEval + MGSM browser: every question, answers from ours / Krikri / Gemma side by side, checker verdicts.
Usage: python3 cluster/bench_browser.py <out.html>   (reads results/<label>/ilsp/**/samples_*.jsonl)"""
import json, glob, sys, html, re

OUT = sys.argv[1]
MODELS = [  # id, display name, results label
    ("pick", "ours · the pick (lr 1e-5, epoch 2)", "E1_lr1e-5_ep2"),
    ("ep3", "ours · lr 1e-5, epoch 3", "E1_lr1e-5_ep3"),
    ("krikri", "Llama-Krikri-8B-Instruct", "peer_krikri"),
    ("gemma", "Gemma-3-12B-it", "peer_gemma3_12b"),
]
FRIENDLY = {
 'punctuation:no_comma':'no commas','length_constraints:number_words':'N words','length_constraints:number_sentences':'N sentences',
 'keywords:forbidden_words':'forbidden words','detectable_format:number_highlighted_sections':'N *highlighted* sections','keywords:frequency':'a word N times',
 'combination:repeat_prompt':'repeat the request first','startend:quotation':'whole answer in quotes','change_case:lowercase':'all lower case',
 'keywords:existence':'must contain keywords','detectable_format:title':'a <<title>>','keywords:letter_frequency':'a letter N times',
 'detectable_format:number_bullet_lists':'N bullets','language:response_language':'respond in language X','detectable_content:number_placeholders':'N [placeholders]',
 'length_constraints:number_paragraphs':'N paragraphs','startend:end_checker':'end with a phrase','detectable_content:postscript':'postscript Υ.Γ.',
 'change_case:capital':'all capitals','change_case:capital_word_frequency':'N all-caps words','combination:two_responses':'two responses',
 'detectable_format:json_format':'JSON only','detectable_format:multiple_sections':'N labelled sections','length_constraints:nth_paragraph_first_word':'k-th paragraph starts with a word',
 'detectable_format:constrained_response':'one of three fixed replies'}

def latest(label, task):
    fs = sorted(glob.glob(f"results/{label}/ilsp/*/samples_{task}_*.jsonl"))
    if not fs: raise SystemExit(f"no samples for {label} {task}")
    return [json.loads(l) for l in open(fs[-1])]

def kw_short(kw):
    return {k: v for k, v in kw.items() if v is not None}

ifeval = {}
for mid, _, lab in MODELS:
    for r in latest(lab, "ifeval_greek"):
        d = r["doc"]; key = d["key"]
        e = ifeval.setdefault(key, {"key": key, "prompt": d["prompt"], "prompt_en": d.get("prompt_en", ""), "ids": d["instruction_id_list"],
                                     "kw": [kw_short(k) for k in d["kwargs"]], "r": {}})
        e["r"][mid] = {"t": r["resps"][0][0], "s": [bool(x) for x in r["inst_level_strict_acc"]], "l": [bool(x) for x in r["inst_level_loose_acc"]],
                       "ps": bool(r["prompt_level_strict_acc"]), "pl": bool(r["prompt_level_loose_acc"])}
mgsm = {}
for mid, _, lab in MODELS:
    for i, r in enumerate(latest(lab, "mgsm_greek")):
        d = r["doc"]
        e = mgsm.setdefault(i, {"i": i, "q": d["question"], "ans": d["answer_number"], "r": {}})
        e["r"][mid] = {"t": r["resps"][0][0], "ok": bool(r["exact_match"])}

data = {"models": [{"id": m, "name": n} for m, n, _ in MODELS], "friendly": FRIENDLY,
        "ifeval": [ifeval[k] for k in sorted(ifeval)], "mgsm": [mgsm[k] for k in sorted(mgsm)]}
# scores
def score(mid):
    rows = data["ifeval"]; ps = sum(e["r"][mid]["ps"] for e in rows) / len(rows)
    inst = [x for e in rows for x in e["r"][mid]["s"]]; isc = sum(inst) / len(inst)
    mg = sum(e["r"][mid]["ok"] for e in data["mgsm"]) / len(data["mgsm"])
    return {"strict_avg": round((ps + isc) / 2 * 100, 1), "prompt": round(ps, 3), "inst": round(isc, 3), "mgsm": round(mg, 3)}
data["scores"] = {m: score(m) for m, _, _ in MODELS}
blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")

CSS = """
:root{--bg:#e9edf1;--paper:#fbfbfc;--ink:#151a20;--muted:#5b6672;--rule:#cfd6dd;--band:#dfe5eb;--accent:#245c8a;--good:#2e7d4f;--bad:#b3402f;--goodbg:#e2f0e7;--badbg:#f6e3df;--ours:#fff3d6;
--serif:"Literata",Georgia,serif;--sans:"Source Sans 3",-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;--mono:"JetBrains Mono",ui-monospace,Menlo,Consolas,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#11161b;--paper:#1a2027;--ink:#e6e9ec;--muted:#9aa5b1;--rule:#33404c;--band:#222b34;--accent:#7fb3dc;--good:#7fc79a;--bad:#e6907f;--goodbg:#1d3328;--badbg:#3a2521;--ours:#3a3320}}
:root[data-theme="dark"]{--bg:#11161b;--paper:#1a2027;--ink:#e6e9ec;--muted:#9aa5b1;--rule:#33404c;--band:#222b34;--accent:#7fb3dc;--good:#7fc79a;--bad:#e6907f;--goodbg:#1d3328;--badbg:#3a2521;--ours:#3a3320}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.45;margin:0}
header{background:var(--paper);border-bottom:1px solid var(--rule);padding:22px 28px 14px;position:sticky;top:0;z-index:5}
h1{font-family:var(--serif);font-size:26px;margin:0 0 4px}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--accent);margin:0 0 6px}
.scores{display:flex;flex-wrap:wrap;gap:6px 22px;font-size:13px;color:var(--muted);margin:6px 0 10px}
.scores b{color:var(--ink);font-variant-numeric:tabular-nums}
.ctl{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;font-size:13px}
.ctl label{color:var(--muted)}
select,input[type=search]{font:inherit;font-size:13px;background:var(--paper);color:var(--ink);border:1px solid var(--rule);padding:4px 8px;border-radius:3px}
.tabs button{font:inherit;font-size:13px;background:var(--band);color:var(--ink);border:1px solid var(--rule);padding:5px 12px;cursor:pointer;border-radius:3px}
.tabs button[aria-pressed=true]{background:var(--accent);color:#fff;border-color:var(--accent)}
button:focus-visible,select:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
main{padding:18px 28px 60px;max-width:1500px;margin:0 auto}
.count{font-family:var(--mono);font-size:12px;color:var(--muted);margin:0 0 12px}
.card{background:var(--paper);border:1px solid var(--rule);margin:0 0 16px;padding:14px 18px}
.card .hd{display:flex;gap:12px;align-items:baseline;flex-wrap:wrap;margin-bottom:8px}
.card .id{font-family:var(--mono);font-size:12px;color:var(--muted)}
.prompt{font-family:var(--serif);font-size:16px;line-height:1.45;white-space:pre-wrap;background:var(--band);padding:10px 14px;border-left:3px solid var(--accent);margin:4px 0 8px}
.en{font-size:13px;color:var(--muted);white-space:pre-wrap;padding:0 14px;margin:0 0 8px;display:none}
.card.showen .en{display:block}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 10px}
.chip{font-family:var(--mono);font-size:11.5px;padding:2px 8px;border:1px solid var(--rule);border-radius:3px;background:var(--paper)}
.cols{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
@media (max-width:900px){.cols{grid-template-columns:1fr}}
.col{border:1px solid var(--rule);border-radius:3px;overflow:hidden}
.col .who{font-family:var(--mono);font-size:11.5px;padding:6px 10px;background:var(--band);display:flex;justify-content:space-between;gap:8px;align-items:center}
.col.ours .who{background:var(--ours)}
.badge{font-family:var(--mono);font-size:11px;padding:1px 7px;border-radius:3px;border:1px solid}
.badge.ok{color:var(--good);border-color:var(--good);background:var(--goodbg)}
.badge.no{color:var(--bad);border-color:var(--bad);background:var(--badbg)}
.badge.loose{color:var(--muted);border-color:var(--rule)}
.verd{display:flex;flex-wrap:wrap;gap:4px;padding:6px 10px;border-bottom:1px solid var(--rule)}
.verd span{font-family:var(--mono);font-size:11px;padding:1px 6px;border-radius:3px;border:1px solid}
.verd .ok{color:var(--good);border-color:var(--good);background:var(--goodbg)}
.verd .no{color:var(--bad);border-color:var(--bad);background:var(--badbg)}
.txt{white-space:pre-wrap;font-size:13.5px;padding:8px 10px;max-height:16em;overflow:auto;font-family:var(--sans)}
.txt.open{max-height:none}
.more{font:inherit;font-size:12px;background:none;border:0;color:var(--accent);cursor:pointer;padding:4px 10px 8px}
.ans{font-family:var(--mono);font-size:12px;color:var(--muted);padding:0 10px 6px}
.toggle{font:inherit;font-size:12px;background:none;border:1px solid var(--rule);color:var(--muted);cursor:pointer;padding:2px 8px;border-radius:3px}
.pager{display:flex;gap:8px;justify-content:center;margin:18px 0}
.pager button{font:inherit;font-size:13px;background:var(--paper);color:var(--ink);border:1px solid var(--rule);padding:6px 14px;cursor:pointer;border-radius:3px}
.note{font-size:13px;color:var(--muted);max-width:90ch}
"""

JS = r"""
const D = window.__DATA__;
const $ = s => document.querySelector(s);
const state = {tab:'ifeval', ours:'pick', type:'all', outcome:'all', q:'', page:0, per:40};
const PEERS = ['krikri','gemma'];
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function nameOf(id){return D.models.find(m=>m.id===id).name;}
function fmtKw(kw){return Object.entries(kw).map(([k,v])=>k+'='+(Array.isArray(v)?'['+v.join(', ')+']':v)).join(' · ');}
function scoresLine(){
  const s=D.scores; const parts=[];
  for(const m of [state.ours,...PEERS]){parts.push(`<span>${esc(nameOf(m))}: IFEval strict avg <b>${s[m].strict_avg}%</b> · MGSM <b>${s[m].mgsm}</b></span>`);}
  $('#scores').innerHTML=parts.join('');
}
function filterIfeval(){
  const q=state.q.toLowerCase();
  return D.ifeval.filter(e=>{
    if(state.type!=='all' && !e.ids.includes(state.type)) return false;
    const o=e.r[state.ours].ps, k=e.r.krikri.ps, g=e.r.gemma.ps;
    if(state.outcome==='ours_fail_krikri_pass' && !( !o && k)) return false;
    if(state.outcome==='ours_pass_krikri_fail' && !( o && !k)) return false;
    if(state.outcome==='all_pass' && !(o&&k&&g)) return false;
    if(state.outcome==='all_fail' && !(!o&&!k&&!g)) return false;
    if(state.outcome==='ours_pass' && !o) return false;
    if(state.outcome==='ours_fail' && o) return false;
    if(q && !(e.prompt.toLowerCase().includes(q)||(e.prompt_en||'').toLowerCase().includes(q))) return false;
    return true;
  });
}
function filterMgsm(){
  const q=state.q.toLowerCase();
  return D.mgsm.filter(e=>{
    const o=e.r[state.ours].ok, k=e.r.krikri.ok, g=e.r.gemma.ok;
    if(state.outcome==='ours_fail_krikri_pass' && !(!o&&k)) return false;
    if(state.outcome==='ours_pass_krikri_fail' && !(o&&!k)) return false;
    if(state.outcome==='all_pass' && !(o&&k&&g)) return false;
    if(state.outcome==='all_fail' && !(!o&&!k&&!g)) return false;
    if(state.outcome==='ours_pass' && !o) return false;
    if(state.outcome==='ours_fail' && o) return false;
    if(q && !e.q.toLowerCase().includes(q)) return false;
    return true;
  });
}
function colIfeval(e,m){
  const r=e.r[m]; const ours=m===state.ours;
  const verd=e.ids.map((id,i)=>`<span class="${r.s[i]?'ok':'no'}">${esc(D.friendly[id]||id)} ${r.s[i]?'✓':'✗'}</span>`).join('');
  const badge=r.ps?'<span class="badge ok">prompt ✓</span>':(r.pl?'<span class="badge loose">loose only</span>':'<span class="badge no">prompt ✗</span>');
  return `<div class="col${ours?' ours':''}"><div class="who"><span>${esc(nameOf(m))}</span>${badge}</div><div class="verd">${verd}</div><div class="txt">${esc(r.t)}</div><button class="more" type="button">expand</button></div>`;
}
function cardIfeval(e){
  const chips=e.ids.map((id,i)=>`<span class="chip">${esc(D.friendly[id]||id)}${Object.keys(e.kw[i]).length?' · '+esc(fmtKw(e.kw[i])):''}</span>`).join('');
  return `<article class="card" data-key="${e.key}"><div class="hd"><span class="id">key ${e.key}</span><button class="toggle" type="button" data-en>show English original</button></div><div class="prompt">${esc(e.prompt)}</div><div class="en">${esc(e.prompt_en||'')}</div><div class="chips">${chips}</div><div class="cols">${[state.ours,...PEERS].map(m=>colIfeval(e,m)).join('')}</div></article>`;
}
function colMgsm(e,m){
  const r=e.r[m]; const ours=m===state.ours;
  const badge=r.ok?'<span class="badge ok">correct ✓</span>':'<span class="badge no">wrong ✗</span>';
  return `<div class="col${ours?' ours':''}"><div class="who"><span>${esc(nameOf(m))}</span>${badge}</div><div class="txt">${esc(r.t)}</div><button class="more" type="button">expand</button></div>`;
}
function cardMgsm(e){
  return `<article class="card"><div class="hd"><span class="id">question ${e.i+1} of 250</span><span class="id">correct answer: <b>${esc(e.ans)}</b></span></div><div class="prompt">${esc(e.q)}</div><div class="cols">${[state.ours,...PEERS].map(m=>colMgsm(e,m)).join('')}</div></article>`;
}
function render(){
  scoresLine();
  const rows = state.tab==='ifeval'?filterIfeval():filterMgsm();
  const pages=Math.max(1,Math.ceil(rows.length/state.per)); if(state.page>=pages) state.page=pages-1;
  const slice=rows.slice(state.page*state.per,(state.page+1)*state.per);
  $('#count').textContent=`${rows.length} of ${state.tab==='ifeval'?D.ifeval.length:D.mgsm.length} ${state.tab==='ifeval'?'prompts':'questions'} · page ${state.page+1} of ${pages}`;
  $('#list').innerHTML=slice.map(state.tab==='ifeval'?cardIfeval:cardMgsm).join('');
  $('#pager').innerHTML=pages>1?`<button type="button" id="pp" ${state.page===0?'disabled':''}>← previous</button><button type="button" id="pn" ${state.page>=pages-1?'disabled':''}>next →</button>`:'';
  const pp=$('#pp'),pn=$('#pn'); if(pp)pp.onclick=()=>{state.page--;render();window.scrollTo(0,0);}; if(pn)pn.onclick=()=>{state.page++;render();window.scrollTo(0,0);};
  $('#typewrap').style.display=state.tab==='ifeval'?'':'none';
}
document.addEventListener('click',ev=>{
  const b=ev.target;
  if(b.classList.contains('more')){const t=b.previousElementSibling;t.classList.toggle('open');b.textContent=t.classList.contains('open')?'collapse':'expand';}
  if(b.hasAttribute('data-en')){const c=b.closest('.card');c.classList.toggle('showen');b.textContent=c.classList.contains('showen')?'hide English original':'show English original';}
});
function init(){
  const ts=$('#type'); const ids=Object.keys(D.friendly).sort((a,b)=>D.friendly[a].localeCompare(D.friendly[b]));
  ts.innerHTML='<option value="all">all instruction types</option>'+ids.map(i=>`<option value="${i}">${esc(D.friendly[i])}</option>`).join('');
  const os=$('#ours'); os.innerHTML=D.models.filter(m=>m.id.startsWith('pick')||m.id==='ep3').map(m=>`<option value="${m.id}">${esc(m.name)}</option>`).join('');
  document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{state.tab=b.dataset.tab;state.page=0;document.querySelectorAll('.tabs button').forEach(x=>x.setAttribute('aria-pressed',x===b));render();});
  ts.onchange=()=>{state.type=ts.value;state.page=0;render();};
  os.onchange=()=>{state.ours=os.value;state.page=0;render();};
  $('#outcome').onchange=e=>{state.outcome=e.target.value;state.page=0;render();};
  $('#q').oninput=e=>{state.q=e.target.value;state.page=0;render();};
  render();
}
init();
"""

page = f"""<title>Greek Benchmark Browser</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,400;7..72,600&family=Source+Sans+3:wght@400;600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>{CSS}</style>
<header>
<p class="eyebrow">Greek IFEval · 541 prompts &nbsp;|&nbsp; Greek MGSM · 250 questions &nbsp;|&nbsp; scored 2026-09-04 on one harness</p>
<h1>Greek Benchmark Browser</h1>
<div class="scores" id="scores"></div>
<div class="ctl">
<span class="tabs"><button type="button" data-tab="ifeval" aria-pressed="true">Greek IFEval</button> <button type="button" data-tab="mgsm" aria-pressed="false">Greek MGSM</button></span>
<label>ours = <select id="ours"></select></label>
<span id="typewrap"><label>type <select id="type"></select></label></span>
<label>show <select id="outcome"><option value="all">everything</option><option value="ours_fail_krikri_pass">ours fails, Krikri passes</option><option value="ours_pass_krikri_fail">ours passes, Krikri fails</option><option value="ours_pass">ours passes</option><option value="ours_fail">ours fails</option><option value="all_pass">all three pass</option><option value="all_fail">all three fail</option></select></label>
<label>search <input type="search" id="q" placeholder="word in the prompt"></label>
</div>
</header>
<main>
<p class="note">Each card shows the prompt, its checkable instructions with their parameters, and the full answer from each model with the checker's verdict per instruction (strict). "Loose only" means the prompt passes after stripping markdown and the first or last line. Answers were generated greedily with each model's own chat template, up to 1,280 tokens. The "respond in language X" instruction fails for every model here because the language detector is not installed on the scoring machine.</p>
<p class="count" id="count"></p>
<div id="list"></div>
<div class="pager" id="pager"></div>
</main>
<script>window.__DATA__ = {blob};</script>
<script>{JS}</script>
"""
page = page.replace("\ufffd", "&#xFFFD;")
open(OUT, "w", encoding="utf-8").write(page)
print("wrote", OUT, round(len(page.encode()) / 1e6, 2), "MB", "scores", data["scores"])
