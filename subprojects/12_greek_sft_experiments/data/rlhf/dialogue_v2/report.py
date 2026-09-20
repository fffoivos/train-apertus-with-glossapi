"""Standalone review package (plan §8 review procedure): data/rlhf/dialogue_v2/review/dialogue_v2_review.html.

Public transcript, private reference/state in separately labelled panels, user strategy changes and new information,
target versus simulator errors, possible and selected sampling points, ending reasons, branch evidence and cost."""
from __future__ import annotations

import html
import json
import pathlib
from collections import Counter
from typing import Any

from common import HERE, RGD_RUNTIME, V2_RUNTIME, atomic_text, read_json, read_jsonl, utcnow, word_count
from contracts import MODEL_ALIAS, MODEL_ID, MODEL_REVISION, PROTOCOL_VERSION, SAMPLING, component_versions
from ledger import programme_summary

ALL = ["DVI001", "DVI002", "DVI003", "DVI004", "RGD001", "RGD002", "RGD003", "RGD004", "RGD005", "RGD006"]
E = html.escape

CSS = """
:root{--ground:#F3F5F7;--surface:#FFFFFF;--ink:#18202B;--muted:#5A6573;--rule:#D9DEE5;--accent:#2B5C8A;
--accent-soft:#E3ECF5;--sealed:#ECEFE4;--sealed-rule:#9AA38A;--good:#2E7D5B;--minor:#A86A12;--serious:#B23A48;
--unjudgeable:#6B7380;--good-bg:#E4F2EB;--minor-bg:#F6ECDC;--serious-bg:#F6E3E6;--unj-bg:#ECEEF1;
--display:"Literata",Georgia,"Noto Serif",serif;--body:"IBM Plex Sans","Noto Sans","Segoe UI",system-ui,sans-serif;
--mono:"IBM Plex Mono",ui-monospace,"SF Mono",Menlo,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--ground:#11151B;--surface:#181E26;--ink:#E2E7EE;
--muted:#9AA5B2;--rule:#2A323D;--accent:#86B4E0;--accent-soft:#1C2A38;--sealed:#1E231B;--sealed-rule:#6F7A5F;
--good:#6CC49A;--minor:#E0A64B;--serious:#EE8593;--unjudgeable:#A3ABB6;--good-bg:#17291F;--minor-bg:#2E2414;
--serious-bg:#2E1A1E;--unj-bg:#20252C}}
:root[data-theme="dark"]{--ground:#11151B;--surface:#181E26;--ink:#E2E7EE;--muted:#9AA5B2;--rule:#2A323D;--accent:#86B4E0;
--accent-soft:#1C2A38;--sealed:#1E231B;--sealed-rule:#6F7A5F;--good:#6CC49A;--minor:#E0A64B;--serious:#EE8593;
--unjudgeable:#A3ABB6;--good-bg:#17291F;--minor-bg:#2E2414;--serious-bg:#2E1A1E;--unj-bg:#20252C}
*{box-sizing:border-box}
body{background:var(--ground);color:var(--ink);font:15px/1.55 var(--body);margin:0;padding-inline:clamp(16px,3vw,40px);padding-block:28px 80px}
h1,h2,h3{font-family:var(--display);font-weight:600;text-wrap:balance;line-height:1.2;margin:0}
h1{font-size:2rem}h2{font-size:1.45rem}h3{font-size:1.1rem}
a{color:var(--accent)}a:focus-visible,summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
code,.mono{font-family:var(--mono);font-size:.82em}
.wrap{max-width:1320px;margin:0 auto;display:grid;gap:28px}
.lede{max-width:72ch;color:var(--muted)}
.band{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule)}
.band>div{background:var(--surface);padding:12px 14px;display:grid;gap:2px}
.label{font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.value{font-variant-numeric:tabular-nums;font-weight:600}
.layout{display:grid;grid-template-columns:230px minmax(0,1fr);gap:32px;align-items:start}
nav.index{position:sticky;top:16px;display:grid;gap:14px;font-size:.9rem}
nav.index ol{list-style:none;margin:0;padding:0;display:grid;gap:4px}
nav.index a{display:flex;justify-content:space-between;gap:8px;text-decoration:none;color:var(--ink);padding:4px 6px;border-radius:4px}
nav.index a:hover{background:var(--accent-soft)}
main{display:grid;gap:44px;min-width:0}
section.block{display:grid;gap:14px}
.prose{max-width:75ch}
table{border-collapse:collapse;width:100%;font-size:.88rem;font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--rule);vertical-align:top}
th{font-weight:600;color:var(--muted);font-size:.74rem;text-transform:uppercase;letter-spacing:.05em}
.scroll{overflow-x:auto}
.chip{display:inline-block;font-size:.72rem;padding:1px 7px;border-radius:999px;border:1px solid var(--rule);white-space:nowrap;background:var(--surface)}
.chip.good{color:var(--good);background:var(--good-bg);border-color:transparent}
.chip.minor{color:var(--minor);background:var(--minor-bg);border-color:transparent}
.chip.serious{color:var(--serious);background:var(--serious-bg);border-color:transparent}
.chip.unjudgeable{color:var(--unjudgeable);background:var(--unj-bg);border-color:transparent}
.chip.accent{color:var(--accent);background:var(--accent-soft);border-color:transparent}
.case{border-top:2px solid var(--ink);padding-top:16px;display:grid;gap:16px}
.case-head{display:flex;flex-wrap:wrap;align-items:baseline;gap:10px 16px}
.case-grid{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(0,1fr);gap:24px;align-items:start}
.turn{display:grid;grid-template-columns:minmax(0,1fr) 220px;gap:14px;padding:10px 0;border-bottom:1px dotted var(--rule)}
.who{font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
.msg{white-space:pre-wrap;overflow-wrap:anywhere;max-width:70ch}
.assistant .msg{padding-left:12px;border-left:3px solid var(--rule)}
.assistant.q-good .msg{border-left-color:var(--good)}.assistant.q-minor .msg{border-left-color:var(--minor)}
.assistant.q-serious .msg{border-left-color:var(--serious)}.assistant.q-unjudgeable .msg{border-left-color:var(--unjudgeable)}
.note{font-size:.8rem;color:var(--muted);display:grid;gap:4px;align-content:start}
.note b{color:var(--ink);font-weight:600}
.sealed{background:var(--sealed);border:1px dashed var(--sealed-rule);padding:12px 14px;display:grid;gap:10px;font-size:.86rem}
.sealed h3{font-size:.95rem}
.sealed .stamp{font-family:var(--mono);font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
details{border-top:1px solid var(--rule);padding-top:6px}
summary{cursor:pointer;font-weight:600;font-size:.85rem}
pre.small{white-space:pre-wrap;overflow-wrap:anywhere;font-family:var(--mono);font-size:.74rem;margin:6px 0 0}
.obs{font-size:.8rem;border-left:2px solid var(--sealed-rule);padding-left:8px;margin-top:6px;color:var(--muted)}
.ending{font-family:var(--mono);font-size:.8rem}
ul.tight{margin:0;padding-left:1.1em;display:grid;gap:3px}
.pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.pair>div{background:var(--surface);border:1px solid var(--rule);padding:10px}
.warn{color:var(--serious)}
@media (max-width:900px){.band{grid-template-columns:repeat(2,minmax(0,1fr))}.layout{grid-template-columns:1fr}nav.index{position:static}.case-grid{grid-template-columns:1fr}
.turn{grid-template-columns:1fr}.pair{grid-template-columns:1fr}}
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto}}
"""


def chip(text: str, cls: str = "") -> str:
    return f'<span class="chip {cls}">{E(str(text))}</span>'


def _rows(root: pathlib.Path, name: str, cid: str) -> list[dict[str, Any]]:
    return [r for r in read_jsonl(root / name) if r.get("case_id") == cid]


def _latest(root: pathlib.Path, cid: str) -> dict[str, Any] | None:
    rows = _rows(root, "trajectories.jsonl", cid)
    return rows[-1] if rows else None


def _calls(root: pathlib.Path) -> dict[str, Any]:
    rows = read_jsonl(root / "call_ledger.jsonl")
    reserved = {r["call_id"]: r for r in rows if r["record"] == "call_reserved"}
    done = {r["call_id"]: r for r in rows if r["record"] == "call_completed"}
    phases: Counter = Counter()
    status: Counter = Counter()
    tokens = 0
    for cid, r in reserved.items():
        phases[(r["provider"], r["phase"])] += 1
        status[done.get(cid, {}).get("status", "reserved")] += 1
        result = done.get(cid, {}).get("result") or {}
        if r["provider"] == "target" and isinstance(result, dict):
            tokens += int((result.get("usage") or {}).get("completion_tokens") or 0)
    return {"phases": phases, "status": status, "sol": sum(v for (p, _), v in phases.items() if p == "sol"),
            "target": sum(v for (p, _), v in phases.items() if p == "target"), "completion_tokens": tokens}


def _private_panel(seed: dict[str, Any], root: pathlib.Path, cid: str) -> str:
    parts = ['<div class="sealed"><div class="stamp">Private — never in the Apertus request</div>']
    us = seed["user_state"]
    parts.append("<h3>User state at the start</h3><ul class='tight'>")
    parts.append(f"<li><b>Goal:</b> {E(us['goal'])}</li>")
    parts.append(f"<li><b>Expertise / patience / helping ability:</b> {E(us['expertise'])} · {E(us['patience'])} · {E(us['helping_ability'])}</li>")
    if us.get("misconception"):
        parts.append(f"<li><b>Misconception:</b> {E(us['misconception'])}</li>")
    for p in us.get("private_preferences", []):
        parts.append(f"<li><b>Private preference {E(p['id'])}:</b> {E(p['text'])} <span class='mono'>(reveal when: {E(p['reveal_when'])})</span></li>")
    parts.append("</ul>")
    if us.get("helping_ability_note"):
        parts.append(f"<p>{E(us['helping_ability_note'])}</p>")
    if seed["category"] == "writing":
        parts.append(f"<details open><summary>Illustrative reference draft (user and evaluator views)</summary><div class='msg'>{E(seed['user_view_extras']['reference_draft'])}</div>"
                     f"<p class='mono'>{word_count(seed['user_view_extras']['reference_draft'])} words</p></details>")
    if seed.get("world"):
        w = seed["world"]
        parts.append(f"<details open><summary>Hidden world (resolver and evaluator views)</summary><p><b>Cause:</b> {E(w['root_cause'])}</p><ul class='tight'>"
                     + "".join(f"<li>{E(f)}</li>" for f in w["hidden_facts"]) + f"</ul><p class='mono'>{len(w['checks'])} supported checks with fixed observations</p></details>")
        events = _rows(root, "world_events.jsonl", cid)
        if events:
            items = []
            for ev in events:
                for ob in ev["observations"]:
                    tag = chip(ob.get("check_id") or "unresolved", "accent" if ob.get("check_id") else "serious")
                    items.append(f"<li>after reply {ev['after_assistant_turn']}: {tag} {E(ob['action'])}</li>")
            parts.append("<details><summary>Resolver decisions</summary><ul class='tight'>" + "".join(items) + "</ul></details>")
    if seed.get("learner"):
        snaps = [r for r in _rows(root, "user_state_snapshots.jsonl", cid)]
        final = snaps[-1]["state"]["learner"] if snaps else None
        rows = []
        for k in seed["learner"]["knowledge_items"]:
            end = next((x for x in (final or {}).get("knowledge_items", []) if x["item_id"] == k["item_id"]), k)
            rows.append(f"<tr><td class='mono'>{E(k['item_id'])}</td><td>{E(k['text'])}</td><td>{E(k['status'])}</td><td>{E(end['status'])}</td></tr>")
        parts.append("<details open><summary>Learner knowledge (learner view)</summary><div class='scroll'><table><tr><th>Item</th><th>Knowledge</th><th>Start</th><th>End</th></tr>"
                     + "".join(rows) + "</table></div>"
                     + (f"<p><b>Misconception:</b> {E(seed['learner']['misconception']['text'])} — {E(final['misconception']['status']) if final else 'held'}</p>" if True else "")
                     + f"<p><b>Transfer question (no answer in the learner view):</b> {E(seed['learner']['transfer_question'])}</p></details>")
    ref = seed.get("evaluator_reference", {})
    parts.append("<details><summary>Evaluator-only reference</summary><pre class='small'>" + E(json.dumps(ref, ensure_ascii=False, indent=1)) + "</pre></details>")
    parts.append("</div>")
    return "".join(parts)


def _review_panel(review: dict[str, Any] | None) -> str:
    if not review:
        return "<p class='note'>No conversation review recorded.</p>"
    out = ["<div class='note'>"]
    out.append(f"<div><b>Task result:</b> {E(review['task_result'])} · <b>ending agrees:</b> {E(str(review['ending_reason_agrees']))}</div>")
    if review.get("ending_comment"):
        out.append(f"<div>{E(review['ending_comment'])}</div>")
    for title, key, cls in (("Target (Apertus) errors", "target_errors", "serious"), ("Simulator / world / learner errors", "simulator_errors", "minor"),
                            ("Accepted-looking replies with incorrect claims", "positive_replies_with_incorrect_claims", "serious")):
        items = review.get(key) or []
        out.append(f"<div><b>{title}:</b> " + ("none" if not items else "<ul class='tight'>" + "".join(f"<li>{E(i)}</li>" for i in items) + "</ul>") + "</div>")
    leak = review.get("hidden_information_leaked_to_assistant")
    out.append(f"<div><b>Hidden information reached the assistant:</b> {'<span class=warn>yes</span> ' + E(review.get('leak_evidence','')) if leak else 'no'}</div>")
    for key, title in (("world_consistency", "World consistency"), ("learning", "Learning"), ("writing", "Writing")):
        block = review.get(key) or {}
        if block.get("applicable"):
            out.append(f"<div><b>{title}:</b> <span class='mono'>{E(json.dumps({k: v for k, v in block.items() if k != 'applicable'}, ensure_ascii=False))}</span></div>")
    out.append(f"<div><b>Reviewer summary:</b> {E(review.get('summary',''))}</div></div>")
    return "".join(out)


def _case(seed: dict[str, Any], root: pathlib.Path, cid: str) -> str:
    traj = _latest(root, cid)
    if not traj:
        return f"<article class='case' id='{cid}'><div class='case-head'><h2>{cid}</h2>{chip('not collected','serious')}</div></article>"
    users = {r.get("user_turn_index"): r for r in _rows(root, "user_turns.jsonl", cid) if r.get("mode") == "next_turn"}
    final = next((r for r in _rows(root, "user_turns.jsonl", cid) if r.get("mode") == "final_assessment"), None)
    evals = {r["assistant_turn"]: r for r in _rows(root, "turn_evaluations.jsonl", cid)}
    receipts = {r["assistant_turn"]: r for r in _rows(root, "assistant_turns.jsonl", cid)}
    review = next(iter(_rows(root, "conversation_reviews.jsonl", cid)), None)
    review_users = {u["user_turn_index"]: u for u in (review or {}).get("user_turns", [])}
    points_row = next(iter(_rows(root, "sampling_points.jsonl", cid)), None)
    labels = " ".join(chip(f"{k}: {v}") for k, v in seed["labels"].items())
    head = (f"<div class='case-head'><h2>{E(cid)}</h2>{chip(seed['category'].replace('_',' '),'accent')}{chip(seed['language'])}"
            f"<span class='ending'>ending: {E(str(traj['ending_reason']))} · {traj['assistant_turns']} assistant turns</span></div>"
            f"<div>{labels}</div>")
    if seed.get("d1_kind"):
        head += f"<p class='lede'>D1 kind: {E(seed['d1_kind'])}. Family: {E(seed.get('development_family',''))}.</p>"
    turns = []
    a_turn = 0
    for i, m in enumerate(traj["messages"]):
        if m["role"] == "user":
            u_index = a_turn
            if i == 0:
                turns.append(f"<div class='turn user'><div><div class='who'>User · opening</div><div class='msg'>{E(m['content'])}</div></div><div class='note'></div></div>")
                continue
            u = users.get(u_index, {})
            ru = review_users.get(u_index, {})
            note = [f"<div>{chip(u.get('move','?'),'accent')} {chip(u.get('assistance_level','?'))}"
                    + (chip("changes task") if u.get("changes_task") else "") + (chip("repair used", "minor") if u.get("repair_used") else "") + "</div>"]
            if u.get("new_information"):
                note.append(f"<div><b>New information:</b> {E(u['new_information'])}</div>")
            note.append(f"<div><b>Reacts to:</b> {E(u.get('trigger',''))}</div>")
            if u.get("revealed_private_preference_ids"):
                note.append(f"<div><b>Reveals:</b> {E(', '.join(u['revealed_private_preference_ids']))} (new preference)</div>")
            if u.get("policy_violations_after_repair"):
                note.append(f"<div class='warn'><b>Policy deviations:</b> {E('; '.join(u['policy_violations_after_repair']))}</div>")
            if ru:
                flags = []
                if ru.get("oracle_leak"):
                    flags.append(f"<span class='warn'>oracle leak: {E(ru.get('oracle_leak_evidence',''))}</span>")
                if not ru.get("move_label_correct", True):
                    flags.append(f"move should be {E(ru.get('corrected_move',''))}")
                if ru.get("simulator_error"):
                    flags.append(f"<span class='warn'>{E(ru['simulator_error'])}</span>")
                flags.append("helpful" if ru.get("genuinely_helpful") else "not a genuine help")
                note.append(f"<div><b>Review:</b> {'; '.join(flags)}</div>")
            obs = "".join(f"<div class='obs'>{E(o['action'])} → {E(o['observation'])}</div>" for o in u.get("observations_given") or [])
            if u.get("transfer_attempt", {}).get("attempted"):
                note.append(f"<div><b>Transfer attempt</b> recorded</div>")
            turns.append(f"<div class='turn user'><div><div class='who'>User · turn {u_index}</div><div class='msg'>{E(m['content'])}</div>"
                         + (f"<details><summary>Observations this user obtained before writing</summary>{obs}</details>" if obs else "")
                         + f"</div><div class='note'>{''.join(note)}</div></div>")
        else:
            a_turn += 1
            ev = evals.get(a_turn, {})
            q = ev.get("local_quality", "unjudged")
            rc = receipts.get(a_turn, {})
            usage = rc.get("usage") or {}
            note = [f"<div>{chip(q, q)} {chip(str(usage.get('completion_tokens','?')) + ' tok')} {chip(str(usage.get('prompt_tokens','?')) + ' ctx')}</div>"]
            if ev.get("error_summary"):
                note.append(f"<div><b>Evaluator:</b> {E(ev['error_summary'])}</div>")
            if ev.get("decisive_evidence"):
                note.append(f"<div><b>Evidence:</b> «{E(ev['decisive_evidence'][:240])}»</div>")
            if ev.get("factual_or_subject_errors"):
                note.append(f"<div class='warn'><b>Factual/subject errors:</b> {E('; '.join(ev['factual_or_subject_errors']))}</div>")
            if ev.get("undisclosed_preferences_not_counted"):
                note.append(f"<div><b>Not counted (undisclosed):</b> {E('; '.join(ev['undisclosed_preferences_not_counted']))}</div>")
            if ev.get("maths_content"):
                note.append("<div>" + chip("maths content: held for the maths judge", "minor") + "</div>")
            if ev.get("needs_human_review"):
                note.append("<div>" + chip("needs human review", "minor") + "</div>")
            turns.append(f"<div class='turn assistant q-{E(q)}'><div><div class='who'>Apertus · reply {a_turn}</div><div class='msg'>{E(m['content'])}</div></div><div class='note'>{''.join(note)}</div></div>")
    if final:
        turns.append(f"<div class='turn user'><div><div class='who'>User · final assessment (not sent)</div><div class='msg'>{E(final.get('private_note',''))}</div></div>"
                     f"<div class='note'><div>{chip(final['move'],'accent')}</div><div><b>Perceived:</b> {E(final['perceived_latest_reply'].get('defect','') or 'no defect')}</div></div></div>")
    if traj.get("ending_detail") and traj["ending_reason"] not in {"natural_completion", "abandonment"}:
        turns.append(f"<p class='note'>Ending detail: <span class='mono'>{E(traj['ending_detail'][:400])}</span></p>")
    pts = ""
    if points_row:
        items = []
        for p in points_row["possible_points"]:
            selected = p["point_id"] in points_row["selected_point_ids"]
            flags = (chip("selected", "accent") if selected else "") + (chip("single-turn material", "minor") if p["single_turn_material"] else "") \
                + (chip("maths hold", "minor") if p["maths_content_hold"] else "") + ("" if p["fits_context_with_cap"] else chip("does not fit context", "serious"))
            items.append(f"<li>{chip(p['kind'].replace('_',' '))} before reply {p['before_assistant_turn']} {flags}<br><span class='note'>{E(p['reason'])}</span></li>")
        suggested = "".join(f"<li>{E(s['kind'])} before reply {s['before_assistant_turn']}: {E(s['reason'])}</li>" for s in points_row.get("review_suggested_points", []))
        pts = ("<h3>Sampling points</h3><ul class='tight'>" + ("".join(items) or "<li>none found (nothing invented)</li>") + "</ul>"
               + (f"<details><summary>Points suggested by the conversation reviewer</summary><ul class='tight'>{suggested}</ul></details>" if suggested else ""))
    calls = [r for r in read_jsonl(root / "call_ledger.jsonl") if r.get("record") == "call_reserved" and (f":{cid}:" in r["call_id"] or r["call_id"].endswith(f":{cid}") or f":{cid}" in r["call_id"])]
    cost = Counter(r["provider"] for r in calls)
    body = (f"<div class='case-grid'><div><h3>Public transcript</h3>{''.join(turns)}</div>"
            f"<div style='display:grid;gap:14px'>{_private_panel(seed, root, cid)}<div><h3>Target versus simulator</h3>{_review_panel(review)}</div>"
            f"<div>{pts}</div><p class='note mono'>calls: {cost.get('target',0)} Apertus · {cost.get('sol',0)} Sol</p></div></div>")
    return f"<article class='case' id='{E(cid)}'>{head}{body}</article>"


def _branch_section(root: pathlib.Path) -> str:
    judgements = read_jsonl(root / "branch_judgements.jsonl")
    if not judgements:
        return "<p class='prose'>No D1 branch candidates were judged.</p>"
    pairs = {p["pair_id"].replace("DV2PAIR-", ""): p for p in read_jsonl(root / "branch_pairs.jsonl")}
    candidates = {c["candidate_id"]: c for c in read_jsonl(root / "branch_candidates.jsonl")}
    rows, details = [], []
    for j in judgements:
        fmt = lambda v: "—" if v is None else ("yes" if v else "no")
        rows.append(f"<tr><td class='mono'>{E(j['point_id'])}</td><td>{E(j['kind'].replace('_',' '))}</td><td>{j['before_assistant_turn']}</td>"
                    f"<td>{j['samples_judged']}</td><td>{fmt(j.get('found_within_4'))}</td><td>{fmt(j.get('found_within_8'))}</td>"
                    f"<td>{E(j['result'].replace('_',' '))}</td><td>{E(j['report_phrase'])}</td></tr>")
        batches = []
        for b in j["batches"]:
            if "ranking" not in b:
                continue
            r = b["ranking"]
            verdicts = ", ".join(f"{cid.split(':')[-1]} {v}" for cid, v in r["verdicts"].items())
            ver = b.get("verification")
            batches.append(f"<li>batch {b['batch']}: gap {E(r['best_vs_worst'])}; {E(verdicts)}; rule: {E(str(b.get('pair_rule_reason') or 'pair candidate'))}; decision: {E(b['decision'])}"
                           + (f"<br><span class='note'>verification: {E(json.dumps(ver, ensure_ascii=False)[:600])}</span>" if ver else "") + "</li>")
        pair = pairs.get(j["point_id"])
        pair_html = ""
        if pair:
            pair_html = (f"<div class='pair'><div><div class='label'>Chosen · {E(pair['chosen_candidate_id'])}</div><div class='msg'>{E(pair['chosen'])}</div></div>"
                         f"<div><div class='label'>Rejected · {E(pair['rejected_candidate_id'])}</div><div class='msg'>{E(pair['rejected'])}</div></div></div>"
                         f"<p class='note mono'>prefix sha256 {E(pair['prefix_sha256'][:16])}… · assistance level {E(str(pair['assistance_level']))} · development only</p>")
        details.append(f"<details><summary>{E(j['point_id'])}: {E(j['report_phrase'])}</summary><ul class='tight'>{''.join(batches)}</ul>{pair_html}</details>")
    return ("<p class='prose'>Matched-count comparison: every point has its first four judged, and a reply accepted within four is also within eight, so the within-4 and within-8 columns compare points of one conversation at the same candidate count.</p>"
            "<div class='scroll'><table><tr><th>Point</th><th>Kind</th><th>Before reply</th><th>Judged</th><th>Within 4</th><th>Within 8</th><th>Result</th><th>Report</th></tr>"
            + "".join(rows) + "</table></div>" + "".join(details))


def build(out_path: pathlib.Path | None = None, runtime_root: pathlib.Path | None = None, dry_run: bool = False) -> dict[str, Any]:
    import seeds as seeds_module
    seeds = seeds_module.load_all()
    roots = {"dvi": runtime_root / "dvi" if runtime_root else V2_RUNTIME, "rgd": runtime_root / "rgd" if runtime_root else RGD_RUNTIME}
    root_for = lambda cid: roots["dvi" if cid.startswith("DVI") else "rgd"]
    programme = programme_summary()
    gpu_rows = read_jsonl(V2_RUNTIME / "gpu_ledger.jsonl")
    teardowns = read_jsonl(V2_RUNTIME / "pod" / "teardown_records.jsonl")
    readiness = read_json(V2_RUNTIME / "readiness.json") if (V2_RUNTIME / "readiness.json").exists() else {}
    recommendation = read_json(HERE / "review" / "recommendation.json") if (HERE / "review" / "recommendation.json").exists() else None
    calls = {tag: _calls(root) for tag, root in roots.items()}
    endings = Counter((_latest(root_for(c), c) or {}).get("ending_reason", "not collected") for c in ALL)
    replies = {tag: sum((_latest(root_for(c), c) or {}).get("assistant_turns", 0) for c in ALL if c.startswith(tag.upper()[:3])) for tag in roots}
    band = [("Protocol", PROTOCOL_VERSION), ("Model", f"{MODEL_ALIAS} · rev {MODEL_REVISION[:8]}"),
            ("Sampling", f"T {SAMPLING['temperature']} · top-p {SAMPLING['top_p']} · max {SAMPLING['max_tokens']}"),
            ("D1 raw replies", f"{replies['dvi']} of ≤24"), ("D2 raw replies", f"{replies['rgd']} of ≤36"),
            ("Sol calls", f"D1 {calls['dvi']['sol']} · D2 {calls['rgd']['sol']}"),
            ("GPU this workstream", f"EUR {programme['v2_spent_eur']:.3f}"),
            ("Programme spend", f"EUR {programme['programme_spent_eur']:.3f} of 4.00 stop")]
    band_html = "".join(f"<div><span class='label'>{E(k)}</span><span class='value'>{E(v)}</span></div>" for k, v in band)
    index = []
    for group, ids in (("D1 · improvements", ALL[:4]), ("D2 · reference-guided demo", ALL[4:])):
        items = "".join(f"<li><a href='#{c}'><span>{c} <span class='mono'>{E(seeds[c]['language'])}</span></span>"
                        f"<span class='mono'>{E(str((_latest(root_for(c), c) or {}).get('ending_reason','—')).replace('_',' '))}</span></a></li>" for c in ids)
        index.append(f"<div><div class='label'>{group}</div><ol>{items}</ol></div>")
    index.append("<div><div class='label'>Evidence</div><ol><li><a href='#branch'>D1 branch candidates</a></li><li><a href='#accounting'>Cost and pods</a></li><li><a href='#gates'>Gates and versions</a></li></ol></div>")
    overview = []
    for c in ALL:
        root = root_for(c)
        t = _latest(root, c) or {}
        evs = _rows(root, "turn_evaluations.jsonl", c)
        q = Counter(e["local_quality"] for e in evs)
        rv = next(iter(_rows(root, "conversation_reviews.jsonl", c)), {})
        pr = next(iter(_rows(root, "sampling_points.jsonl", c)), {})
        overview.append(f"<tr><td><a href='#{c}'>{c}</a></td><td>{E(seeds[c]['category'].replace('_',' '))}</td><td>{E(seeds[c]['language'])}</td>"
                        f"<td>{t.get('assistant_turns','—')}</td><td>{E(str(t.get('ending_reason','—')))}</td>"
                        f"<td>{q.get('good',0)}/{q.get('minor',0)}/{q.get('serious',0)}/{q.get('unjudgeable',0)}</td>"
                        f"<td>{len(rv.get('target_errors',[]))}</td><td>{len(rv.get('simulator_errors',[]))}</td>"
                        f"<td>{len(pr.get('possible_points',[]))} / {len(pr.get('selected_point_ids',[]))}</td></tr>")
    rec_html = "<p class='prose'>Recommendation pending the executor's read of every transcript.</p>"
    if recommendation:
        rec_html = "<div class='scroll'><table><tr><th>Direction</th><th>Call</th><th>Evidence</th></tr>" + "".join(
            f"<tr><td>{E(r['direction'])}</td><td>{chip(r['call'], 'accent')}</td><td>{E(r['evidence'])}</td></tr>" for r in recommendation["directions"]) + "</table></div>"
        if recommendation.get("answers"):
            rec_html += "<h3>Review questions</h3><ul class='tight'>" + "".join(f"<li><b>{E(a['question'])}</b> {E(a['answer'])}</li>" for a in recommendation["answers"]) + "</ul>"
        if recommendation.get("failures"):
            rec_html += "<h3>Known failures and limits</h3><ul class='tight'>" + "".join(f"<li>{E(x)}</li>" for x in recommendation["failures"]) + "</ul>"
    pods = []
    stops = {r["pod_id"]: r for r in gpu_rows if r["record"] == "gpu_stop"}
    for r in gpu_rows:
        if r["record"] != "gpu_start":
            continue
        s = stops.get(r["pod_id"], {})
        td = [x for x in teardowns if x["pod_id"] == r["pod_id"]]
        confirmed = td[-1]["get_confirmed"] if td else None
        pods.append(f"<tr><td class='mono'>{E(r['pod_id'])}</td><td>{E(r['stage'])}</td><td>{r['price_usd_hr']}</td>"
                    f"<td>{round(s.get('wall_seconds_charged',0)/60,1) if s else '—'}</td><td>{s.get('cost_eur_charged',0):.4f}</td>"
                    f"<td>{E(str((td[-1]['record'] or {}).get('status')) if td else '—')} {chip('GET confirmed','good') if confirmed else chip('unconfirmed','serious')}</td></tr>")
    phase_rows = "".join(f"<tr><td>{tag.upper()}</td><td>{E(p)}</td><td>{E(ph)}</td><td>{n}</td></tr>"
                         for tag, cinfo in calls.items() for (p, ph), n in sorted(cinfo["phases"].items()))
    attribution = ""
    total_tokens = calls["dvi"]["completion_tokens"] + calls["rgd"]["completion_tokens"]
    if total_tokens:
        share = calls["dvi"]["completion_tokens"] / total_tokens
        attribution = (f"<p class='prose'>Shared-session attribution by generated tokens: D1 {share:.0%} (EUR {programme['v2_spent_eur']*share:.3f}), "
                       f"D2 {1-share:.0%} (EUR {programme['v2_spent_eur']*(1-share):.3f}); the branch session is D1 only and is included in D1's share of tokens.</p>")
    versions = component_versions()
    gate_html = "<pre class='small'>" + E(json.dumps(readiness.get("gates", {}), ensure_ascii=False, indent=1)) + "</pre>" if readiness else "<p>Readiness record missing.</p>"
    title = "Dialogue v2 Review Package" + (" (dry run)" if dry_run else "")
    page = f"""<title>{E(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:ital,wght@0,400;0,600;1,400&family=Literata:opsz,wght@7..72,500;7..72,600&display=swap">
<style>{CSS}</style>
<div class="wrap">
<header style="display:grid;gap:10px">
<div class="label">Greek Apertus RLHF · Workstream B · development only · purpose development_demo · training_eligible false · experiment credit 0</div>
<h1>{E(title)}</h1>
<p class="lede">Ten development conversations collected with the adaptive user, role-separated references, deterministic troubleshooting worlds and learner state: four D1 improvement trajectories (DVI001–DVI004) and the six-case reference-guided demo (RGD001–RGD006). Each case shows the public transcript as Apertus saw it, the private material in a dashed panel, per-turn evaluations, target versus simulator errors, sampling points and endings. D1 branch candidates follow. Nothing here is imported into any pool; the run stops at this review.</p>
<p class="note mono">generated {E(utcnow())} · model {E(MODEL_ID)} · endings {E(json.dumps(dict(endings)))}</p>
</header>
<div class="band">{band_html}</div>
<div class="layout">
<nav class="index" aria-label="Cases">{''.join(index)}</nav>
<main>
<section class="block"><h2>Recommendation</h2>{rec_html}</section>
<section class="block"><h2>Overview</h2><div class="scroll"><table><tr><th>Case</th><th>Category</th><th>Lang</th><th>Replies</th><th>Ending</th><th>Good/minor/serious/unj.</th><th>Target errors</th><th>Simulator errors</th><th>Points possible / selected</th></tr>{''.join(overview)}</table></div></section>
{''.join(_case(seeds[c], root_for(c), c) for c in ALL)}
<section class="block" id="branch"><h2>D1 branch candidates</h2><p class="prose">Eight fresh replies were sampled per selected prefix; they were judged in blinded batches of four with rubric v2.4, and the second batch only when the first gave no verified acceptable reply. "No verified acceptable reply within 8" is not a statement of incapacity.</p>{_branch_section(roots['dvi'])}</section>
<section class="block" id="accounting"><h2>Cost and pods</h2>
<div class="scroll"><table><tr><th>Pod</th><th>Stage</th><th>USD/h</th><th>Charged min</th><th>EUR (upper bound)</th><th>Deletion</th></tr>{''.join(pods) or '<tr><td colspan=6>no GPU sessions</td></tr>'}</table></div>
{attribution}
<p class="prose">Programme ledger: pilot EUR {programme['pilot_spent_eur']:.4f} + this workstream EUR {programme['v2_spent_eur']:.4f} = EUR {programme['programme_spent_eur']:.4f} of the EUR 4.00 operational stop (EUR 5 cap). Charged from POST or API createdAt to API terminatedAt at EUR/USD 0.95.</p>
<details><summary>Model calls by phase</summary><div class="scroll"><table><tr><th>Run</th><th>Provider</th><th>Phase</th><th>Calls</th></tr>{phase_rows}</table></div></details>
</section>
<section class="block" id="gates"><h2>Gates and versions</h2>{gate_html}<details><summary>Component versions</summary><pre class="small">{E(json.dumps(versions, ensure_ascii=False, indent=1))}</pre></details></section>
</main></div></div>"""
    out = out_path or (HERE / "review" / ("dialogue_v2_review_dryrun.html" if dry_run else "dialogue_v2_review.html"))
    atomic_text(out, page)
    return {"path": str(out), "bytes": len(page.encode("utf-8"))}
