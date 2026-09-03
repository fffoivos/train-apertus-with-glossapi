#!/usr/bin/env python3
"""Build a self-contained, blind reading and rating page from generation runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from pathlib import Path
from typing import Any, NoReturn

FLAGS = [
    "not Greek",
    "American underneath",
    "assistant mannerism",
    "wrong fact",
    "too long",
    "too short",
]


def fail(message: str) -> NoReturn:
    raise SystemExit(f"ERROR: {message}")


def resolve_run(value: str) -> tuple[str, Path]:
    candidate = Path(value)
    if candidate.is_file():
        label = (
            candidate.parent.name
            if candidate.stem in {"dev_gen", "interviews", "transcripts"}
            else candidate.stem
        )
        return label, candidate
    candidate = Path("results") / value / "dev_gen.jsonl"
    if candidate.is_file():
        return value, candidate
    fail(f"run is neither a JSONL path nor results/<run>/dev_gen.jsonl: {value}")


def read_run(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                fail(f"invalid JSON at {path}:{line_number}: {exc.msg}")
            prompt_id = str(row.get("prompt_id") or row.get("row_id") or row.get("id") or "")
            if not prompt_id or prompt_id in rows:
                fail(f"missing or duplicate prompt id at {path}:{line_number}")
            rows[prompt_id] = row
    return rows


def clean_text(value: Any) -> str:
    return re.sub(r"<\|assistant_end\|>\s*$", "", str(value or "")).strip()


def prompt_turns(row: dict[str, Any]) -> list[dict[str, str]]:
    messages = row.get("messages") or row.get("prompt_messages") or row.get("input_messages")
    if isinstance(messages, list):
        turns = []
        for message in messages:
            if isinstance(message, dict) and message.get("role") in {"system", "user", "assistant"}:
                turns.append(
                    {"role": str(message["role"]), "content": clean_text(message.get("content"))}
                )
        if turns:
            return turns
    transcript = row.get("transcript")
    if isinstance(transcript, dict):
        transcript = transcript.get("messages") or transcript.get("turns")
    if isinstance(transcript, list):
        for turn in transcript:
            if isinstance(turn, dict) and turn.get("role") == "user":
                return [{"role": "user", "content": clean_text(turn.get("content"))}]
    prompt = row.get("prompt") or row.get("question") or row.get("input")
    return [{"role": "user", "content": clean_text(prompt)}]


def answer_turns(row: dict[str, Any]) -> list[dict[str, str]]:
    transcript = row.get("transcript")
    if isinstance(transcript, dict):
        transcript = transcript.get("messages") or transcript.get("turns")
    if isinstance(transcript, list):
        turns = []
        for turn in transcript:
            if isinstance(turn, dict) and turn.get("role") in {"user", "assistant"}:
                turns.append({"role": str(turn["role"]), "content": clean_text(turn.get("content"))})
        if turns:
            return turns
    assistants = row.get("assistant_turns")
    if isinstance(assistants, list):
        return [{"role": "assistant", "content": clean_text(text)} for text in assistants]
    value = row.get("text", row.get("response", row.get("output", row.get("raw_text", ""))))
    return [{"role": "assistant", "content": clean_text(value)}]


def json_for_script(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def build_page(run_args: list[str], seed: int) -> tuple[str, str]:
    loaded: list[tuple[str, Path, dict[str, dict[str, Any]]]] = []
    labels: set[str] = set()
    for value in run_args:
        label, path = resolve_run(value)
        if label in labels:
            fail(f"run label is not unique: {label}")
        labels.add(label)
        loaded.append((label, path, read_run(path)))
    if len(loaded) < 2:
        fail("at least two runs are required for blind reading")
    ids = set(loaded[0][2])
    for label, _path, rows in loaded[1:]:
        if set(rows) != ids:
            fail(f"prompt ids in run {label} do not match the first run")
    if len(ids) != 40:
        fail(f"reading page requires exactly 40 prompts; got {len(ids)}")

    items = []
    mapping: dict[str, dict[str, str]] = {}
    for ordinal, prompt_id in enumerate(sorted(ids), 1):
        base = loaded[0][2][prompt_id]
        answers = []
        for label, _path, rows in loaded:
            answers.append({"run": label, "turns": answer_turns(rows[prompt_id])})
        random.Random(f"{seed}:{prompt_id}").shuffle(answers)
        blind_answers = []
        mapping[prompt_id] = {}
        for answer_index, answer in enumerate(answers, 1):
            anonymous_id = f"answer-{answer_index}"
            mapping[prompt_id][anonymous_id] = answer["run"]
            blind_answers.append({"id": anonymous_id, "turns": answer["turns"]})
        items.append(
            {
                "number": ordinal,
                "prompt_id": prompt_id,
                "config": base.get("config"),
                "language": base.get("language"),
                "prompt_turns": prompt_turns(base),
                "answers": blind_answers,
            }
        )
    signature = hashlib.sha256(json_for_script(mapping).encode()).hexdigest()[:16]
    return render_html(items, mapping, signature), signature


def render_html(items: list[dict[str, Any]], mapping: dict[str, dict[str, str]], signature: str) -> str:
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Blind checkpoint reading</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,400;7..72,600&family=Inter:wght@400;500;650&display=swap">
<style>
:root {{ --bg:#f4f1ea; --paper:#fffdf8; --ink:#25241f; --muted:#706d64; --line:#d8d2c5; --accent:#165f57; --accent2:#9f512f; --soft:#e7f0ed; --flag:#fff1df; color-scheme:light; }}
:root[data-theme="dark"] {{ --bg:#171817; --paper:#222321; --ink:#eeeae1; --muted:#aaa69d; --line:#41423e; --accent:#79c7ba; --accent2:#ef9b73; --soft:#243b37; --flag:#453325; color-scheme:dark; }}
@media (prefers-color-scheme:dark) {{ :root:not([data-theme="light"]) {{ --bg:#171817; --paper:#222321; --ink:#eeeae1; --muted:#aaa69d; --line:#41423e; --accent:#79c7ba; --accent2:#ef9b73; --soft:#243b37; --flag:#453325; color-scheme:dark; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.55 Inter,system-ui,sans-serif; }}
header {{ position:sticky; top:0; z-index:10; border-bottom:1px solid var(--line); background:color-mix(in srgb,var(--bg) 92%,transparent); backdrop-filter:blur(10px); }}
.bar,.page {{ max-width:1180px; margin:auto; padding:1rem 1.25rem; }}
.bar {{ display:flex; gap:1rem; align-items:center; }}
h1 {{ margin:0; font:600 clamp(1.15rem,2vw,1.55rem) Literata,serif; flex:1; }}
button {{ border:1px solid var(--line); border-radius:999px; padding:.55rem .9rem; color:var(--ink); background:var(--paper); cursor:pointer; font-weight:600; }}
button.primary {{ background:var(--accent); color:var(--paper); border-color:var(--accent); }}
.progress {{ color:var(--muted); font-variant-numeric:tabular-nums; white-space:nowrap; }}
.intro {{ max-width:74ch; font-family:Literata,serif; color:var(--muted); margin:1rem 0 2rem; }}
.item {{ margin:0 0 3rem; scroll-margin-top:6rem; }}
.item-head {{ display:flex; gap:.7rem; align-items:baseline; margin-bottom:.7rem; }}
.num {{ font-weight:650; color:var(--accent); }}
.meta {{ color:var(--muted); font-size:.78rem; }}
.prompt {{ border-left:4px solid var(--accent); background:var(--soft); padding:.85rem 1rem; border-radius:0 10px 10px 0; margin-bottom:1rem; }}
.turn {{ white-space:pre-wrap; overflow-wrap:anywhere; font-family:Literata,serif; }}
.turn + .turn {{ margin-top:.7rem; padding-top:.7rem; border-top:1px solid var(--line); }}
.role {{ display:block; color:var(--muted); font:650 .68rem Inter,sans-serif; letter-spacing:.08em; text-transform:uppercase; margin-bottom:.2rem; }}
.answers {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr)); gap:1rem; }}
.answer {{ background:var(--paper); border:1px solid var(--line); border-radius:12px; overflow:hidden; min-width:0; }}
.answer-head {{ display:flex; gap:.8rem; align-items:center; padding:.7rem .85rem; border-bottom:1px solid var(--line); }}
.answer-name {{ font-weight:650; margin-right:auto; }}
.pick {{ display:flex; gap:.25rem; align-items:center; font-size:.78rem; }}
.response {{ padding:1rem; min-height:7rem; }}
.flags {{ display:flex; flex-wrap:wrap; gap:.35rem; padding:.7rem; border-top:1px solid var(--line); }}
.flag {{ display:flex; gap:.3rem; align-items:center; border:1px solid var(--line); border-radius:999px; padding:.28rem .5rem; font-size:.72rem; cursor:pointer; }}
.flag:has(input:checked) {{ background:var(--flag); border-color:var(--accent2); color:var(--accent2); }}
input {{ accent-color:var(--accent); }}
.saved {{ color:var(--accent); font-size:.78rem; min-width:4rem; text-align:right; }}
@media (max-width:680px) {{ .bar {{ flex-wrap:wrap; }} h1 {{ flex-basis:100%; }} .page {{ padding-inline:.8rem; }} }}
@media print {{ header, .flags, .pick {{ display:none; }} .answer {{ break-inside:avoid; }} body {{ background:white; }} }}
</style>
</head>
<body>
<header><div class="bar">
  <h1>Blind checkpoint reading</h1>
  <span class="progress" id="progress">0 / 40 rated</span>
  <span class="saved" id="saved"></span>
  <button id="theme" type="button">Theme</button>
  <button class="primary" id="save" type="button">Save + JSON</button>
</div></header>
<main class="page">
<p class="intro">For every prompt, choose one best and one worst answer, then add any applicable flags. Answer order is independently shuffled. Changes remain in this browser; “Save + JSON” also downloads resolved run names.</p>
<div id="items"></div>
</main>
<script>
const ITEMS={json_for_script(items)};
const RUN_MAP={json_for_script(mapping)};
const FLAGS={json_for_script(FLAGS)};
const STORAGE_KEY="greek-sft-reading-{signature}";
let state={{}};
try {{ state=JSON.parse(localStorage.getItem(STORAGE_KEY)||"{{}}")||{{}}; }} catch (_) {{ state={{}}; }}
const $=s=>document.querySelector(s);
function elem(tag,cls,text) {{ const e=document.createElement(tag); if(cls)e.className=cls; if(text!==undefined)e.textContent=text; return e; }}
function turnNode(turn) {{
  const box=elem("div","turn"); box.append(elem("span","role",turn.role)); box.append(document.createTextNode(turn.content)); return box;
}}
function ensure(pid) {{ if(!state[pid]) state[pid]={{best:null,worst:null,flags:{{}}}}; return state[pid]; }}
function persist() {{ localStorage.setItem(STORAGE_KEY,JSON.stringify(state)); $("#saved").textContent="saved"; setTimeout(()=>$("#saved").textContent="",900); updateProgress(); }}
function updateProgress() {{ const n=ITEMS.filter(x=>{{const s=ensure(x.prompt_id);return s.best&&s.worst;}}).length; $("#progress").textContent=`${{n}} / ${{ITEMS.length}} rated`; }}
function render() {{
  const root=$("#items"); root.replaceChildren();
  ITEMS.forEach(item=>{{
    const section=elem("section","item"); section.id="item-"+item.number;
    const head=elem("div","item-head"); head.append(elem("span","num",String(item.number).padStart(2,"0"))); head.append(elem("span","meta",[item.config,item.language,item.prompt_id].filter(Boolean).join(" · "))); section.append(head);
    const prompt=elem("div","prompt"); item.prompt_turns.forEach(t=>prompt.append(turnNode(t))); section.append(prompt);
    const grid=elem("div","answers"); const current=ensure(item.prompt_id);
    item.answers.forEach((answer,index)=>{{
      const card=elem("article","answer"); const ah=elem("div","answer-head"); ah.append(elem("span","answer-name",`Answer ${{index+1}}`));
      [["best","Best"],["worst","Worst"]].forEach(([kind,label])=>{{
        const pick=elem("label","pick"); const radio=document.createElement("input"); radio.type="radio"; radio.name=`${{kind}}-${{item.number}}`; radio.checked=current[kind]===answer.id;
        radio.addEventListener("change",()=>{{ current[kind]=answer.id; if(kind==="best"&&current.worst===answer.id) current.worst=null; if(kind==="worst"&&current.best===answer.id) current.best=null; persist(); render(); }});
        pick.append(radio,document.createTextNode(label)); ah.append(pick);
      }}); card.append(ah);
      const response=elem("div","response"); answer.turns.forEach(t=>response.append(turnNode(t))); card.append(response);
      const flagbox=elem("div","flags"); const chosen=new Set(current.flags[answer.id]||[]);
      FLAGS.forEach(flag=>{{ const lab=elem("label","flag"); const cb=document.createElement("input"); cb.type="checkbox"; cb.checked=chosen.has(flag); cb.addEventListener("change",()=>{{ const set=new Set(current.flags[answer.id]||[]); cb.checked?set.add(flag):set.delete(flag); current.flags[answer.id]=[...set]; persist(); }}); lab.append(cb,document.createTextNode(flag)); flagbox.append(lab); }}); card.append(flagbox); grid.append(card);
    }}); section.append(grid); root.append(section);
  }}); updateProgress();
}}
function exportRows() {{
  const rows=[]; ITEMS.forEach(item=>{{ const s=ensure(item.prompt_id); item.answers.forEach(answer=>rows.push({{prompt_id:item.prompt_id,run:RUN_MAP[item.prompt_id][answer.id],best:s.best===answer.id,worst:s.worst===answer.id,flags:s.flags[answer.id]||[]}})); }}); return rows;
}}
$("#save").addEventListener("click",()=>{{ persist(); const blob=new Blob([JSON.stringify(exportRows(),null,2)+"\\n"],{{type:"application/json"}}); const a=document.createElement("a"); a.href=URL.createObjectURL(blob); a.download=`reading-ratings-{signature}.json`; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),1000); }});
$("#theme").addEventListener("click",()=>{{ const root=document.documentElement; const dark=root.dataset.theme?root.dataset.theme==="dark":matchMedia("(prefers-color-scheme:dark)").matches; root.dataset.theme=dark?"light":"dark"; }});
render();
</script>
</body>
</html>
'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs="+", required=True, help="Run names or generation JSONL paths")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260904)
    args = parser.parse_args()
    html, signature = build_page(args.runs, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    print(f"wrote {args.out} prompts=40 runs={len(args.runs)} mapping={signature}")


if __name__ == "__main__":
    main()
