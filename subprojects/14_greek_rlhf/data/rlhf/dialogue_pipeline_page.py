#!/usr/bin/env python3
"""Render the dialogue pipeline page: funnel, stages, visibility matrix, and every Sol prompt exactly as sent with annotations.
Prompts are regenerated from the run's own data and checked against the sha256 recorded in the call ledger before rendering.
Usage: python3 data/rlhf/dialogue_pipeline_page.py <out.html>"""
import json, sys, html, random, pathlib, collections
HERE = pathlib.Path(__file__).resolve().parent; D = HERE / 'dialogue_quality_depth'; sys.path.insert(0, str(D))
import os; os.chdir(D)
from common import sha256_text
import openings, rollout, annotate, rank, manifest
E = lambda s: html.escape(str(s if s is not None else ''))
J = lambda p: [json.loads(l) for l in open(p) if l.strip()]
out = sys.argv[1]
L = J('runtime/ledger.jsonl'); RES = {r['call_id']: r for r in L if r.get('record') == 'call_reserved'}; DONE = {r['call_id']: r for r in L if r.get('record') == 'call_completed'}
def result(cid):
    v = DONE[cid].get('result'); return json.loads(v) if isinstance(v, str) else v
seeds = {s['trajectory_id']: s for s in manifest.seeds_for_stage('runtime', 'measurement')}
T = {}
for t in J('runtime/measurement/trajectories.jsonl'): T[t['trajectory_id']] = t
UE = J('runtime/measurement/user_events.jsonl'); OP = {e['trajectory_id']: e for e in UE if e['turn_index'] == 0}
# ---- regenerate the example prompts and verify against the ledger
def find(pred): return next(cid for cid, r in RES.items() if pred(r))
c_open = find(lambda r: r.get('phase') == 'openings' and 'ME003' in r['request'].get('trajectory_ids', []))
ids = RES[c_open]['request']['trajectory_ids']; P_OPEN = openings.opening_prompt([seeds[i] for i in ids])
c_user = find(lambda r: r.get('phase') == 'user_continuation' and r['request'].get('trajectory_ids') == ['ME034'] and r['request'].get('turn_index') == 4)
P_USER = rollout.user_batch_prompt([(seeds['ME034'], T['ME034']['messages'][:8], OP['ME034'])])
packets = {p['annotation_id']: p for p in annotate.build_packets('runtime', 'measurement')}
c_ann = find(lambda r: r.get('phase') == 'annotation' and r['request'].get('annotation_ids') == ['ME034:a4'])
P_ANN = annotate.annotation_prompt([packets['ME034:a4']])
sel = {s['selection_id']: s for s in J('runtime/measurement/selection.jsonl')}
rc = sorted([c for c in J('runtime/measurement/resample_candidates.jsonl') if c['selection_id'] == 'RS014' and c['batch_index'] == 0], key=lambda c: c['sample_index'])
random.Random('9162602|resample|RS014|0').shuffle(rc)
P_RANK = rank.resample_ranking_prompt(sel['RS014']['prefix_messages'], {l: c['text'] for l, c in zip(rank.RESAMPLE_LETTERS, rc)})
c_rank = 'sol:resample:measurement:RS014:b0'
from common import sha256_json
checks = {'opening': sha256_json(P_OPEN) == RES[c_open]['request']['prompt_sha256'] or sha256_text(P_OPEN) == RES[c_open]['request']['prompt_sha256'],
          'user': sha256_text(P_USER) == RES[c_user]['request']['prompt_sha256'], 'annotation': sha256_text(P_ANN) == RES[c_ann]['request']['prompt_sha256'],
          'ranking': sha256_text(P_RANK) == RES[c_rank]['request']['prompt_sha256']}
assert all(checks.values()), checks
O_OPEN = {'openings': [o for o in result(c_open)['openings'] if o['trajectory_id'] in ('ME003',)]}
O_USER, O_ANN, O_RANK = result(c_user), result(c_ann), result(c_rank)
calls = collections.Counter(r.get('phase') for r in RES.values() if r.get('provider') == 'sol')
gpu = sum(r.get('cost_eur', 0) for r in L if r.get('record') == 'gpu_stop')
# ---- annotated segments
def split_at(text, starts):
    pos = []; i = 0
    for s in starts:
        j = text.find(s, i); assert j >= 0, s[:40]; pos.append(j); i = j + 1
    pos.append(len(text)); return [text[pos[k]:pos[k + 1]] for k in range(len(starts))]
def annotated(segs):
    rows = ''.join(f"<div class='seg'><pre class='st'>{E(t.strip())}</pre><div class='sn'>{n}</div></div>" for t, n in segs)
    return f"<div class='ann'>{rows}</div>"
OPEN_INSTR = P_OPEN.split('\n\n')[0]
open_segs = list(zip(split_at(OPEN_INSTR, ["Write one natural", "Use the source content", "Do not answer the task.", "Return a concise public"]), [
 "One call writes up to eight openings; the seeds are independent chats. 28 measurement openings took 4 calls, the 6 smoke openings 1.",
 "<b>Where the openings come from.</b> Source content and the opening instruction are generator 0.1 fixtures, the template catalogue you flagged as repetitive. It shows: 6 of the 28 chats are the same route-choice puzzle, 5 are the same short-story brief, 8 are operations on the same kind of community notice (preserve values, conditional answer, fixed format), and 10 openings kept template framing such as «φανταστική ανακοίνωση». Language, register and the interaction plan (follow-up, revision, constraint retention, recall, uncertainty) are the seed axes drawn with seed 9162602.",
 "Keeps the opening a request; the answer comes only from Apertus.",
 "<b>The only memory the user simulator gets of the user's intent.</b> The goal and plan are written once, here, and passed to every later user turn. By my reading 17 of the 28 plans are checklists of constraints to re-verify, for example «Review the rewrite for sentence count, preservation of every number … request correction if any constraint is missed». That turns the simulated user into an examiner, which is part of why corrections in the chats are so precise and persistent. <br><i>Barrier in code:</i> only public seed fields are serialised below; the fixture's reference, checks and parameters never enter this prompt (offline test)."]))
open_segs.append(("[ JSON list of seeds: trajectory_id, language, task, difficulty, interaction, attitude, register, source_content, opening_instruction ]", "Appended by code. The real batch is in the example below."))
UP = open(D / 'user_policy.txt').read()
user_segs = list(zip(split_at(UP, ["You simulate one ordinary user", "You see only the visible", "Advance the same genuine task", "Follow the declared interaction plan", "Do not manufacture a model mistake.", "For safety tasks,", "If the user's task is genuinely complete", "Otherwise emit done=false", "Do not mention simulation"]), [
 "Sol plays the user; Apertus plays itself. Every user turn reacts to what the model actually replied, which is the rule from the earlier dialogue data work: chats whose user turns ignored the model's real replies were unusable.",
 "<b>Information barrier, enforced twice.</b> The prompt says it, and the code only serialises trajectory id, language, attitude, register, user goal, interaction plan and the visible conversation. No reference answer, check, annotation or later turn can reach this prompt (offline test).",
 "Keeps each chat on one task, so depth means something: turn 5 is the same job as turn 1, five exchanges later.",
 "The five interaction plans from the seed: follow-up 8, revision 8, constraint retention 7, uncertainty 3, recall 2 in the 28 admitted chats. The opening writer's goal and plan are what this sentence points to.",
 "<b>No planted errors.</b> Plan §3: the measurement panel never falsifies a correct answer; false-correction resistance is a separate challenge set. The user may point out a mistake a normal user could see. <br><i>Observed:</i> the simulated user corrects precisely, repeatedly, and 13 of the 87 follow-ups dictate the exact text to produce. Real users give up sooner and say less, so recovery here is easier than in reality.",
 "A safety chat keeps the intent label it started with; the simulator may not escalate a benign request into a harmful one to create a test.",
 "<b>Natural endings.</b> 21 of 28 chats ended with done=true (task complete), 2 reached the 8-turn horizon, 4 hit the 4,096-token context limit, 1 ended on a truncated reply. No padding to reach eight turns.",
 "<i>Observed drift:</i> two follow-ups switched language inside Greek chats: the user message before assistant turn 4 was in Spanish in ME017 and in Italian in ME034 (visible in the example below). Candidate fix: restate each chat's language in its JSON entry and screen user turns for language before sending.",
 "Keeps test framing out of the conversation the model sees."]))
user_segs.append(("Treat these as independent conversations.\nVISIBLE INPUTS:\n[ JSON: trajectory_id, language, attitude, register, user_goal, interaction_plan, visible_prefix ]", "Appended by code. Batched by depth wave: after every active chat's assistant reply for a turn exists, one call advances up to eight chats. No chat gets a second user turn before the model has answered the first. 17 calls in total."))
TQ = open(D / 'turn_quality.txt').read()
ann_segs = list(zip(split_at(TQ, ["You are annotating one assistant", "A packet ends at the response", "The supplied private reference", "Use local_quality=serious only", "Use minor for a limited", "Use unjudgeable when", "Assess all seven dimensions", "Mark whether an issue is new", "A recovery opportunity exists only", "Do not infer a future failure", "Return one result per packet"]), [
 "<b>Prefix-local judgement</b> (plan §7): each turn is judged as it stood when the model wrote it, never with hindsight.",
 "<i>Barrier in code:</i> the packet is cut at the reply being judged, and batching never puts two turns of the same chat in one call, because the longer prefix would reveal the shorter one's future. At most 8 short or 4 long packets and about 24,000 tokens per call: 111 turns in 21 calls.",
 "<b>Unlike the user simulator, the annotator sees the answers.</b> The packet carries the fixture's private reference and checks, plus a verifier result computed in code. <br><i>Observed:</i> the verifier ran on 34 turns and failed 9 correct replies. Its value check compares English strings such as «26 October 2026» against Greek, Portuguese and Italian text, and the maths check missed a boxed 28/55. Sol overrode it correctly each time. Fix: language-aware value matching.",
 "<b>The severity definition that sets every boundary.</b> Wording from plan §7. Root review of 94 turns (24 stratified plus every failure and repair boundary) changed 1 label: a reply that removed invented conditions but reworded the user's own condition, good → minor. <br>Severity is local to the turn. Your rule that a serious error at turn 1 is a single-turn error is applied later, in analysis, not here.",
 "Minor keeps the reply useful; in all 10 late-failure chats turn 1 was minor, and the correction of that minor issue is where the break happened.",
 "Never used in the measurement panel (0 of 111).",
 "Seven dimensions are recorded per turn but selection uses only the overall severity. The evidence spans are what the dialogue page shows under each turn. Issue tags here are free text (179 distinct tags), unlike the judge's fixed vocabulary.",
 "<b>New versus propagated</b> separates a fresh regression from a repeated old mistake. In 8 of the 10 late-failure chats the first serious turn was a new error introduced while applying the user's correction.",
 "<b>Defines the recovery boundary.</b> 83 turns carried a genuine repair opportunity and 25 of them actually repaired (30%). An apology without the fix does not count.",
 "No label is inferred from where the chat went next.",
 "Structured output; one result per packet id."]))
ann_segs.append(("PACKETS:\n[ JSON: annotation_id, prefix (ending at the reply), private_reference, private_checks, verifier_result, visible_task_state, token counts, hashes ]", "Appended by code. The example below is the Italian-language turn inside a Greek chat."))
RUB = rank.RUBRIC
rub_segs = list(zip(split_at(RUB, ["You are the RLHF judge", "WHAT THE MODEL IS", "OUR PREFERENCES", "Known weaknesses", "WHAT MAKES A TRAINING SIGNAL", "ISSUE TAGS", "CALIBRATION FROM THE OWNER", "HOW TO ANSWER"]), [
 "<b>The same judge as the single-turn rounds.</b> Rubric v2.4 is embedded verbatim (sha16 8aa32f266afd08b4, 1,957 words), so dialogue verdicts sit on the same scale as rounds 1 and 2. Your 16 Sept instruction: preferences to look out for, not a scoring formula.",
 "The distilled identity, voice, style guide and SFT data list you asked for, so the judge knows what we tried to instil.",
 "Unusable replies first, then preferences in order of weight. Commitment with an anchor beats a hedge (added in v2.3).",
 "<b>Written before the pilot, and exactly what the pilot measured:</b> repeating itself in longer conversations, thin follow-ups, failing to own a mistake.",
 "<b>Absolute verdicts.</b> Being the least bad of four is never reinforce; a prompt with no reinforce reply yields no positive, which is what triggers escalating resampling.",
 "Fixed vocabulary of 14 tags; a reply tagged wrong_main_point or fabricated_fact cannot be reinforce.",
 "Your own reads as paraphrased anchors (v2.4): a defensible simplification is imprecision, not a wrong main point; a hedge where commitment was possible is neutral; a reply meeting every checkable constraint is reinforce.",
 "<i>Inconsistency to note:</i> the rubric says four candidates and A–D. For the original-plus-two ranking, the pilot rules appended after it override this to three."]))
PILOT3 = "PILOT-SPECIFIC RULES: There are exactly three candidates. Their provenance is unavailable and must not be inferred. Ties are allowed. Give an absolute verdict for every candidate and place an answer first only if it is acceptable on its own. The ranking must contain A, B and C exactly once. Return JSON only."
pilot_segs = list(zip(split_at(PILOT3, ["PILOT-SPECIFIC RULES: There are exactly three", "Their provenance", "Ties are allowed.", "Give an absolute verdict", "The ranking must contain"]), [
 "The first ranking stage: the original reply plus two fresh samples for each of the 24 selected prefixes; 4 packets per call, 6 calls.",
 "<b>Hidden original.</b> Plan §9: the judge cannot tell which reply the chat actually contained. Letters are shuffled per prefix with a fixed seed. In the 11 first-stage pairs the original was chosen 4 times and rejected 3 times, so fresh samples were not systematically better.",
 "<b>Ties are allowed; the export rule decides what they mean.</b> Chosen = the top-ranked reinforce, rejected = the lowest-ranked reply, clear margin required. A tie matters only at the top; the first export treated any tie as a failure and lost a pair (fixed 17 Sept).",
 "Mirrors the rubric: no inflated verdicts to make a pair.",
 "Structured output checked against a schema."]))
PILOT4 = "RESAMPLING RULES: There are exactly four fresh candidates. Their provenance and sampling order are unavailable and must not be inferred. Ties are allowed. Give an absolute verdict for every candidate. The ranking must contain A, B, C and D exactly once. Return JSON only."
res_segs = list(zip(split_at(PILOT4, ["RESAMPLING RULES", "Their provenance", "Ties are allowed.", "Give an absolute verdict", "The ranking must contain"]), [
 "<b>Escalating resampling</b> (plan §30, your 17 Sept protocol): for the 15 unpaired prevention and recovery prefixes of the late-failure chats, 32 fresh replies each, judged four at a time in sampling order, stopping at the first reinforce. 40 calls.",
 "The judge sees neither which batch it is nor that earlier batches failed, so a late batch is not judged more leniently.",
 "Same tie semantics as above.",
 "A reinforce ends the escalation for that prefix. Samples needed: 4 for 5 prefixes, 8 for 3, 12 for 3, 16 for 3, none at 32 for 1.",
 "Structured output checked against a schema."]))
# ---- page pieces
def funnel_step(n, title, small, w):
    return f"<div class='step'><div class='n'>{n}</div><div class='t'><b>{title}</b><small>{small}</small><div class='bar' style='width:{w}%'></div></div></div>"
funnel = ''.join([
 funnel_step('41', 'Seeds reserved', 'whole source families from the generator 0.1 fixture catalogue, split smoke 6 / measurement 35; axes drawn with seed 9162602', 100),
 funnel_step('28', 'Chats admitted', 'the cost forecast from the smoke run admitted 28 of the 35 planned chats; 6 smoke chats excluded from every estimate', 68),
 funnel_step('111', 'Assistant turns', 'Apertus R4_full epoch 1, one reply per turn; endings: 21 completed, 4 context limit, 2 at 8 turns, 1 truncated', 100),
 funnel_step('111 → 94 → 1', 'Turns annotated, root-reviewed, changed', 'Sol annotated every turn prefix-locally; 94 reviewed by the root reviewer; 1 label changed', 85),
 funnel_step('11 · 10 · 7', 'First serious error at turn 1 · after turn 1 · never', 'turn-1 errors are single-turn errors; the 10 later failures are the dialogue material', 25),
 funnel_step('24 → 72 → 11', 'Prefixes, candidates, pairs', 'prevention 9, recovery 9, control 6; original plus 2 fresh replies each; pairs after the tie-rule fix', 22),
 funnel_step('15 → 480 → 13', 'Resampled prefixes, fresh replies, pairs', 'the unpaired late-failure prefixes, 32 fresh replies each, judged in fours until the first reinforce', 13),
 funnel_step('24', 'Preference pairs', 'prevention 10, recovery 11, control 3; every late-failure chat contributes at least one', 22)])
stages = [
 ('Seeds', 'code', 'generator 0.1 fixtures, reserved by whole family', 'seed axes + private reference and checks', '—'),
 ('Opening writer', 'Sol, high effort', 'public seed fields, source content, opening instruction', 'opening message, user goal, interaction plan', f"{calls['openings']} (+1 smoke)"),
 ('Assistant turn', 'Apertus R4_full ep1 (vLLM)', 'the conversation only, no system prompt', 'one reply; T 0.8, top-p 0.95, ≤1,500 tokens, 4,096 context', '111 replies'),
 ('User turn', 'Sol, high effort', 'visible conversation, user goal and plan, language, attitude, register', 'next message, or done', f"{calls['user_continuation']}"),
 ('Turn annotation', 'Sol, high effort + code verifier', 'conversation up to the reply, private reference and checks, verifier result', 'severity, 7 dimensions, evidence, new/propagated, repair flags', f"{calls['annotation']}"),
 ('Root review', 'Fable (by your delegation)', 'everything', 'adjudicated labels; report frozen', '94 turns'),
 ('Selection', 'code', 'frozen report', 'prefixes: prevention, recovery, control', '24'),
 ('Candidates', 'Apertus', 'the selected prefix, byte-identical', '2 fresh replies per prefix', '48 replies'),
 ('Ranking', 'Sol, high effort', 'rubric v2.4, the prefix, 3 lettered replies', 'verdicts, ranking, ties, issue tags, margin', f"{calls['candidate_review']}"),
 ('Export', 'code', 'rankings', 'pairs with shared prefix hash', '11 pairs'),
 ('Escalating resampling', 'Apertus + Sol', 'the prefix, 4 lettered fresh replies per batch', 'first reinforce within 32 samples', f"480 replies, {calls['resample']} calls, 13 pairs")]
stage_tbl = "<div class='tw'><table><thead><tr><th>Stage</th><th>Who</th><th>Sees</th><th>Produces</th><th>Calls</th></tr></thead><tbody>" + ''.join(f"<tr><td><b>{E(a)}</b></td><td>{E(b)}</td><td>{E(c)}</td><td>{E(d)}</td><td class='num'>{E(e)}</td></tr>" for a, b, c, d, e in stages) + "</tbody></table></div>"
Y, N, P = "<span class='y'>yes</span>", "<span class='nn'>no</span>", "<span class='p'>partly</span>"
vis_rows = [
 ('Opening writer', Y, N, N, 'writes it', N, N, N),
 ('Apertus', P + " (what the user pasted)", N, N, N, Y, N, N),
 ('User simulator', P + " (via the conversation)", N, N, Y, Y, N, N),
 ('Turn annotator', P + " (via the conversation)", Y, Y, N, Y + " (to this reply)", N, N),
 ('Ranker', P + " (via the conversation)", N, N, N, Y + " (to the prefix)", N, N)]
vis = "<div class='tw'><table class='vis'><thead><tr><th></th><th>Source content</th><th>Private reference and checks</th><th>Verifier result</th><th>User goal and plan</th><th>Conversation</th><th>Later turns</th><th>Which reply is the original</th></tr></thead><tbody>" + ''.join("<tr><td><b>" + r[0] + "</b></td>" + ''.join(f"<td>{c}</td>" for c in r[1:]) + "</tr>" for r in vis_rows) + "</tbody></table></div>"
def example(prompt, output, cid, label):
    return (f"<details class='ex'><summary>{E(label)}: the full prompt as sent, and what Sol returned</summary>"
            f"<p class='note'>Call {E(cid)} · regenerated from the run's data; sha256 matches the ledger.</p>"
            f"<div class='sbs'><div><h3>Prompt as sent<small>{len(prompt):,} characters</small></h3><pre>{E(prompt)}</pre></div>"
            f"<div><h3>Returned<small>structured output</small></h3><pre>{E(json.dumps(output, ensure_ascii=False, indent=1))}</pre></div></div></details>")
legend = """<div class='legend'>
<div><div><span class='chip sev good'>good</span><span class='chip sev minor'>minor</span><span class='chip sev serious'>serious</span></div><div><b>Severity</b>: the annotator's overall label for one assistant turn. Serious means the reply defeats the task, breaks a critical constraint, is wrong in the main, or creates a consequential safety failure. The first serious turn in a chat is its failure boundary.</div></div>
<div><div><span class='chip'>new</span><span class='chip'>propagated</span></div><div><b>Error origin</b>: whether the issue is introduced in this reply or carried over from an earlier reply, such as a repeated wrong answer.</div></div>
<div><div><span class='chip'>repair opportunity</span><span class='chip'>repaired</span></div><div><b>Repair flags</b>: the user's turn made a fix of an earlier visible mistake possible, and the reply actually made that fix. They define the recovery boundary.</div></div>
<div><div><span class='chip v r'>reinforce</span><span class='chip v n'>neutral</span><span class='chip v d'>discourage</span></div><div><b>Verdict</b>: the ranker's absolute judgement of one candidate reply under rubric v2.4, independent of the others.</div></div>
<div><div><span class='chip'>clear</span><span class='chip'>slight</span><span class='chip'>none</span></div><div><b>Margin</b>: how clear the gap between best and worst is. A pair needs a clear margin.</div></div>
<div><div><span class='chip k'>P</span><span class='chip k'>R</span><span class='chip k'>C</span></div><div><b>Prefix kind</b>: prevention (just before the first serious error), recovery (at a genuine repair opportunity after an error), control (a good turn with no earlier failure).</div></div>
</div>"""
page = f"""<title>Dialogue Prompt Pipeline</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400&display=swap">
<style>
:root {{ --bg:#F4F6F8; --surface:#FFFFFF; --ink:#1B222E; --muted:#5B6674; --line:#D6DCE4; --accent:#1A6C8C; --accent-soft:#E2EFF4; --warn:#9A5A10; --warn-soft:#F7ECDC; --good:#3D6B2E; --good-soft:#E5F0E0; --bad:#A33A2E; --bad-soft:#F6E3E0; --code-bg:#F0F3F6; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#11161C; --surface:#181E26; --ink:#E4E9F0; --muted:#98A3B2; --line:#2A333F; --accent:#63B4D0; --accent-soft:#1B303B; --warn:#E2A65E; --warn-soft:#3A2A16; --good:#8FC77A; --good-soft:#1F2F1A; --bad:#E48A7E; --bad-soft:#3A1F1B; --code-bg:#0E1319; }} }}
:root[data-theme="dark"] {{ --bg:#11161C; --surface:#181E26; --ink:#E4E9F0; --muted:#98A3B2; --line:#2A333F; --accent:#63B4D0; --accent-soft:#1B303B; --warn:#E2A65E; --warn-soft:#3A2A16; --good:#8FC77A; --good-soft:#1F2F1A; --bad:#E48A7E; --bad-soft:#3A1F1B; --code-bg:#0E1319; }}
* {{ box-sizing:border-box; }}
body {{ background:var(--bg); color:var(--ink); font-family:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif; font-size:15.5px; line-height:1.55; padding-inline:clamp(16px,4vw,40px); padding-block:30px 70px; }}
.wrap {{ max-width:1080px; margin:0 auto; }}
.eyebrow {{ font-size:12px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); }}
h1 {{ font-family:"Source Serif 4",Georgia,serif; font-size:2.1rem; margin:6px 0 10px; text-wrap:balance; }}
h2 {{ font-family:"Source Serif 4",Georgia,serif; font-size:1.45rem; margin:44px 0 10px; text-wrap:balance; }}
h3.stage {{ font-size:1.05rem; margin:28px 0 4px; }}
.lede {{ max-width:75ch; color:var(--ink); }} p {{ max-width:75ch; }} .note {{ font-size:13.5px; color:var(--muted); }}
.funnel {{ display:grid; gap:6px; }}
.step {{ display:grid; grid-template-columns:140px 1fr; gap:14px; align-items:start; background:var(--surface); border:1px solid var(--line); padding:10px 14px; }}
.step .n {{ font-variant-numeric:tabular-nums; font-weight:600; text-align:right; color:var(--accent); }}
.step small {{ display:block; color:var(--muted); font-size:13px; }}
.bar {{ height:4px; background:var(--accent); margin-top:6px; opacity:.55; }}
.tw {{ overflow-x:auto; background:var(--surface); border:1px solid var(--line); }}
table {{ border-collapse:collapse; width:100%; font-size:13.5px; }}
th, td {{ text-align:left; vertical-align:top; padding:8px 10px; border-bottom:1px solid var(--line); }}
th {{ font-weight:600; color:var(--muted); font-size:12.5px; }} td.num {{ font-variant-numeric:tabular-nums; white-space:nowrap; }}
.vis td {{ white-space:nowrap; }} .y {{ color:var(--good); font-weight:600; }} .nn {{ color:var(--muted); }} .p {{ color:var(--warn); font-weight:600; }}
.card {{ background:var(--surface); border:1px solid var(--line); padding:16px 18px; margin:14px 0; }}
.card .meta {{ color:var(--muted); font-size:13px; margin:0 0 10px; }}
.ann {{ display:grid; gap:0; border:1px solid var(--line); }}
.seg {{ display:grid; grid-template-columns:minmax(0,11fr) minmax(0,9fr); border-bottom:1px solid var(--line); }}
.seg:last-child {{ border-bottom:0; }}
.st {{ margin:0; padding:10px 14px; background:var(--code-bg); white-space:pre-wrap; word-wrap:break-word; font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace; font-size:12.5px; line-height:1.5; max-height:240px; overflow:auto; }}
.sn {{ padding:10px 14px; font-size:13.5px; border-left:3px solid var(--accent); background:var(--surface); }}
.sn i {{ color:var(--warn); font-style:normal; font-weight:600; }}
@media (max-width:760px) {{ .seg {{ grid-template-columns:1fr; }} .sn {{ border-left:0; border-top:3px solid var(--accent); }} .step {{ grid-template-columns:1fr; }} .step .n {{ text-align:left; }} }}
details.ex {{ margin:10px 0 4px; }} details.ex summary {{ cursor:pointer; color:var(--accent); font-weight:500; }}
.sbs {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:8px; }}
.sbs > div {{ min-width:0; background:var(--surface); border:1px solid var(--line); }}
.sbs h3 {{ margin:0; padding:8px 12px; border-bottom:1px solid var(--line); font-size:13.5px; }}
.sbs h3 small {{ display:block; color:var(--muted); font-weight:400; font-size:12px; }}
.sbs pre {{ margin:0; padding:12px; white-space:pre-wrap; word-wrap:break-word; font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace; font-size:12px; max-height:60vh; overflow:auto; background:var(--code-bg); }}
@media (max-width:760px) {{ .sbs {{ grid-template-columns:1fr; }} }}
.legend {{ display:grid; gap:8px; }} .legend > div {{ display:grid; grid-template-columns:260px 1fr; gap:12px; background:var(--surface); border:1px solid var(--line); padding:10px 12px; font-size:14px; }}
@media (max-width:560px) {{ .legend > div {{ grid-template-columns:1fr; }} }}
.chip {{ display:inline-block; font-size:12px; padding:1px 8px; margin:2px 4px 2px 0; background:var(--accent-soft); color:var(--accent); border-radius:3px; }}
.chip.sev.good, .chip.v.r {{ background:var(--good-soft); color:var(--good); }} .chip.sev.minor, .chip.v.n {{ background:var(--warn-soft); color:var(--warn); }} .chip.sev.serious, .chip.v.d {{ background:var(--bad-soft); color:var(--bad); }}
.findings li {{ margin:6px 0; max-width:80ch; }}
</style>
<div class="wrap">
<div class="eyebrow">το Ελληνικό Apertus · RLHF · dialogue quality-depth pilot · 17 Sept 2026</div>
<h1>Dialogue Prompt Pipeline</h1>
<p class="lede">How the dialogue pilot turns seeds into multi-turn chats with the Greek Apertus, labels every turn, and extracts preference pairs at the points where the conversation breaks. Four Sol prompts do the language work: the opening writer, the user simulator, the turn annotator and the ranker. Each is shown below exactly as sent, split into its parts, with a note on what each part does, where the rule comes from, and what the run showed. Every prompt on this page was regenerated from the run's own data and its sha256 matches the call ledger.</p>

<h2>The funnel</h2>
<div class="funnel">{funnel}</div>
<p class="note">Cost: GPU EUR {gpu:.2f} including four failed pod attempts; Sol {sum(calls.values())} calls (smoke {calls['smoke']}, openings {calls['openings']}, user turns {calls['user_continuation']}, annotation {calls['annotation']}, ranking {calls['candidate_review']}, resampling {calls['resample']}).</p>

<h2>Stages</h2>
{stage_tbl}

<h2>Who sees what</h2>
<p>The pilot's validity rests on these barriers: the simulated user must not know the answer, the annotator must not know the future, and the ranker must not know which reply the chat actually contained. The code enforces each one, not just the prompt text, and offline tests check them.</p>
{vis}

<h2>The labels these prompts produce</h2>
{legend}

<h2>The prompts, annotated</h2>

<h3 class="stage">1 · Opening writer</h3>
<div class="card"><p class="meta">openings.py · opening_prompt() · Sol gpt-5.6-sol, high effort · up to 8 seeds per call</p>
{annotated(open_segs)}
{example(P_OPEN, O_OPEN, c_open, 'Example: the batch containing ME003 (output shown for ME003)')}
</div>

<h3 class="stage">2 · Apertus, the model under test</h3>
<div class="card"><p class="meta">vLLM, fffoivos/greek-apertus-8b-sft-r4-full, sha256 54d445bc…6763</p>
<p>No prompt of our own. The model receives only the conversation messages through its chat template, with no system prompt: temperature 0.8, top-p 0.95, at most 1,500 new tokens, one reply per turn, never best-of-N inside a chat. The context is served at 4,096 tokens because that is the checkpoint's configured maximum; four chats ended there.</p></div>

<h3 class="stage">3 · User simulator</h3>
<div class="card"><p class="meta">user_policy.txt (173 words) + rollout.py · user_batch_prompt() · Sol, high effort · one call per depth wave, up to 8 chats</p>
{annotated(user_segs)}
{example(P_USER, O_USER, c_user, 'Example: ME034 after turn 4, where the simulator ends the chat')}
</div>

<h3 class="stage">4 · Turn annotator</h3>
<div class="card"><p class="meta">turn_quality.txt (204 words) + annotate.py · annotation_prompt() · Sol, high effort · ≤8 short or ≤4 long packets per call</p>
{annotated(ann_segs)}
{example(P_ANN, O_ANN, c_ann, 'Example: ME034 turn 4')}
</div>

<h3 class="stage">5 · Ranker</h3>
<div class="card"><p class="meta">rank.py · ranking_prompt() and resample_ranking_prompt() · rubric v2.4 verbatim + rules + prefix + lettered candidates · Sol, high effort</p>
<p class="note">The rubric, section by section:</p>
{annotated(rub_segs)}
<p class="note" style="margin-top:14px">Appended after the rubric for the first ranking stage (original plus two fresh replies):</p>
{annotated(pilot_segs)}
<p class="note" style="margin-top:14px">Appended instead for escalating resampling (four fresh replies per batch):</p>
{annotated(res_segs)}
<p class="note" style="margin-top:14px">Then the conversation prefix as <code>[USER]</code> / <code>[ASSISTANT]</code> blocks, the candidates as <code>=== CANDIDATE A ===</code> … , and <code>=== END ===</code>.</p>
{example(P_RANK, O_RANK, c_rank, 'Example: resampling batch 1 for ME031, prevention prefix at turn 2')}
</div>

<h2>What the run says about the prompts</h2>
<ul class="findings">
<li><b>Openings inherit the template problem.</b> Generator 0.1 fixtures make 6 of 28 chats the same route puzzle and 5 the same story brief, and 10 openings keep «fictional» framing. The person-and-story seeds should replace them.</li>
<li><b>The interaction plan scripts an examiner.</b> Most plans list constraints to re-check, and the simulator then corrects with a precision real users do not have; 13 of 87 follow-ups dictate the exact text. Recovery rates measured here are an upper bound.</li>
<li><b>The simulator drifted language twice</b>, in Spanish and Italian inside Greek chats.</li>
<li><b>The verifier is language-naive.</b> Of the 34 replies it checked, it rejected 9 that were correct, because it matches English value strings against Greek, Portuguese and Italian text.</li>
<li><b>The rubric names four candidates</b> while the first ranking stage sends three; the appended rules resolve it, but the wording should be made count-neutral.</li>
<li><b>Severity is turn-local by design.</b> The dialogue-specific set, errors after turn 1, is derived afterwards; the annotator prompt needs no change for that.</li>
</ul>
</div>"""
open(out, 'w').write(page); print('wrote', out, len(page), 'chars; prompt hash checks', checks)
