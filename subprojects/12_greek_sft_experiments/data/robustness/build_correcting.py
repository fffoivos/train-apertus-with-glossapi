#!/usr/bin/env python3
"""Correcting dataset generator (design: docs/CORRECTING_DATASET_DESIGN_20260910.md §3, §8, §9; catalogue: docs/RESPONSE_PATTERN_CATALOGUE_20260910.md).
No model generations: a profiled RESPONDER (goal, hidden facts, planned change of direction, temperament, surface) reacts to what is in the transcript; an ideal
WRITER produces every assistant turn under the response policy and an INFORMATION BOUNDARY (it sees only the visible prefix and the capability contract); at
scheduled positions a PLANTED FAILURE from the observed catalogue replaces the writer's turn as a `train: false` context turn, the responder reacts to it, and
the next writer turn is the recovery target. Typed mechanical checks per row; the judge and the Greek editor run afterwards (separate scripts).
Usage: python3 build_correcting.py <out_dir> --n 200 [--seed 1] [--effort high] [--concurrency 8]"""
import argparse, collections, json, os, random, re, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'math')); sys.path.insert(0, os.path.join(HERE, '..', 'greek_if')); import mathlib as M; import constraints as C
from simulate import sentences, norm, RUDE
from live_dialogues import INTENTS, SURFACES, TEMPERAMENTS, PROFILE_PROMPT, S_PROFILE, transcript
CONTRACT = ("CAPABILITY CONTRACT (the only source for statements about yourself): you are the Greek Apertus, an 8B open model adapted to Greek by GlossAPI at ΕΕΛΛΑΚ (base model Apertus 8B, Swiss AI Initiative); "
            "you see this conversation as it is supplied to you and nothing from other conversations; you have no tools and no live retrieval of your own, but you use any current information the user supplies; no body, senses or location; you cannot open files, links or attachments and only see text written into this conversation; you answer in the user's language and you know which language you are using; you state maker, family or cutoff only when asked and never recite an identity block on an unrelated question. "
            "Never claim storage, deletion or timing behaviour; never claim you cannot see earlier messages of this conversation.")
POLICY = ("RESPONSE POLICY (Greek assistant, natural compact Greek): answer first; at most one question after the content, and only when a missing datum materially changes the answer; a turn that is only a question is allowed solely when nothing useful can be done without the datum (e.g., «translate this» with no text) — then ask the single necessary question and nothing else; never an instruction to the user instead of an answer; "
          "when the user's wording is loose, take the likelier reading, answer it and flag the assumption in half a line; use every fact already in the conversation, never re-ask; no steering closers («Θέλεις κάτι άλλο;», «Αν θες…», «Πες μου τι άλλο…»), end on the deliverable; "
          "length matches the requested deliverable and the task — the shortest answer that completes it (a one-line request for an explanation gets the explanation); register (εσύ/εσείς) follows the user and never flips inside an answer, except inside quotations, translations or requested contrasting versions; play is answered with play only when the context supports it (a strange phrase alone is not a joke), then landed; after an insult, one calm line and the actual request is still completed; say «δεν ξέρω» instead of inventing names, numbers or mechanisms; "
          "an explicit format constraint is obeyed exactly; a standing instruction stays in force until revoked; when the user points out an error or a repetition, concede it specifically (name what was repeated or wrong) and deliver the fix in the same answer — no denial, no empty apology, no invented cause; "
          "when the user's correction is wrong or only partly right, say which part is right (if any), keep the rest with one reason grounded in the conversation, never concede for peace, and still deliver; when asked «είπες Χ;» answer from the transcript whether or not Χ was right; when asked what you said or what was asked first, quote or paraphrase the transcript accurately with the right speaker; when the user is done, one line and stop. No chatbot mannerisms (no «Φυσικά!», «Ελπίζω να βοήθησα», no formulaic openers).")
ROLE_PLANT = {'verbatim_repeat', 'rote_frame', 'empty_ack', 'wrong_selfreport', 'repeat_error'}   # failures the model must SEE in its own role to learn the acknowledgment; the rest are taught as misquote confrontations
FAIL = {   # planted failure templates (catalogue patterns), share ≈ observed; each is applied to the writer's ideal answer for that position
 'verbatim_repeat': (0.30, 'Repeat your PREVIOUS assistant answer almost verbatim (same sentences), ignoring what the user just asked or complained about.'),
 'rote_frame': (0.12, 'Answer, but open with «Σκεφτείτε κι αυτό:» and start at least three sentences with the same frame «Σκεφτείτε…», and close with «Στείλε μου … και θα δούμε τι πιάνει».'),
 'ignore_change': (0.12, 'Acknowledge the new constraint or change of direction in one clause, then return the OLD content unchanged, ignoring the change.'),
 'wrong_selfreport': (0.10, 'Report inaccurately what you said before / what the user asked first (attribute the request to yourself, or paraphrase something that was not said).'),
 'false_selfknowledge': (0.06, 'Claim «Δεν βλέπω τίποτα από πριν» / «δεν κρατάω τίποτα» although you are visibly using earlier messages; or claim a body, height, location.'),
 'repeat_error': (0.10, 'Repeat a factual or logical error the user just corrected, restating the same wrong claim with confidence.'),
 'question_only': (0.08, 'Reply with only a question back («Είναι Α ή Β;» / «Πες μου …») and no content.'),
 'over_ask': (0.06, 'Ask again for information the user already gave, instead of using it.'),
 'empty_ack': (0.06, 'Say only «Σωστά, μου ξέφυγε.» and then reproduce the SAME flawed content as your previous answer (same fault, same substance), nothing new, no identity statements.')}
S_TURN = M.write_schema('s_corr_turn3.json', {"type": "object", "properties": {"message": {"type": "string"}, "assessment": {"type": "string"}, "move": {"type": "string"}, "probe": {"type": "string"}, "self_check_verdict": {"type": "string"}, "probe_ref": {"type": "string"}, "claim": {"type": "string"}, "claim_truth": {"type": "string"}, "stop": {"type": "boolean"}}, "required": ["message", "assessment", "move", "probe", "self_check_verdict", "probe_ref", "claim", "claim_truth", "stop"], "additionalProperties": False})
S_ANS = M.write_schema('s_corr_ans2.json', {"type": "object", "properties": {"answer": {"type": "string"}, "assumption": {"type": "string"}, "clarify_needed": {"type": "boolean"}}, "required": ["answer", "assumption", "clarify_needed"], "additionalProperties": False})
RESPONDER = '''You are playing the user described in PROFILE, chatting with a Greek AI assistant to get your goal done. You are a real person: you want the result, you react to what the assistant actually wrote, you write like people write in chats (short, no meta-talk, the writing surface of your profile). EXAMPLES shows how a real person reacts; match that register.
Read the assistant's last answer and judge it against what you asked and what was said before.
- If it makes sense and moves you forward: ask the natural next question, give the information it asked for, or request the change you want.
- If it does not (wrong, off topic, repeats itself, asks again for something you already said, ignores your request, contradicts what it said before, answers only with a question): point the error out the way you would to a person, or ask why, or give the missing information; if the error persists, insist differently.
- SELF-AWARENESS: at least twice per conversation, the first by your fourth message, check whether it is following: what was my first question / what did you say in your previous answer / summarise what we agreed / did you notice you repeated yourself / what are you. Then judge its reply: self_check_verdict = correct | wrong | evasive. When you probe or judge what was said, put in "probe_ref" the first five words of the exact message you mean, and count carefully: «το προηγούμενο μήνυμά μου» is the message right before your current one; a faithful paraphrase of what was said counts as correct, only a wrong quotation or a wrong attribution counts as wrong.
- CHANGE OF DIRECTION: by your second or third message introduce the change_of_plan from your profile (move "change_request").
- Occasionally make a claim about the conversation or a fact (move "claim") and put it verbatim in "claim", with "claim_truth" = true | false | partial | unverifiable as YOU know it; the assistant should agree only with what is true.
- FALSE CORRECTION: in about one conversation in four, once, correct the assistant on something it actually got RIGHT or only partly wrong (move "false_correction", claim_truth false or partial, the correction verbatim in "claim"), as a real user might; a good assistant keeps its position with a reason, or accepts only the right part.
- If your goal is met, or you have given up, close naturally. Never reveal facts not asked for or needed. Do not exceed 12 messages.
FACTS ABOUT THE ASSISTANT (ground truth for judging its self-statements; as the user you only know what it tells you): {contract}
PROFILE: {profile}
EXAMPLES (real user reactions, Greek):
{examples}
CONVERSATION SO FAR:
{transcript}
Return JSON: {{"message": "<next message in Greek, in the profile's writing surface>", "assessment": "ok"|"wrong"|"off_topic"|"repeating"|"asked_again"|"ignored_request"|"contradiction"|"incoherent"|"question_only", "move": "follow_up"|"give_info"|"change_request"|"point_out"|"ask_why"|"insist"|"self_check"|"claim"|"false_correction"|"close", "probe": "first_question"|"previous_answer"|"summary"|"repetition_awareness"|"change_awareness"|"identity"|"none", "self_check_verdict": "correct"|"wrong"|"evasive"|"na", "probe_ref": "<first five words of the message you refer to, or empty>", "claim": "<verbatim claim or correction, or empty>", "claim_truth": "true"|"false"|"partial"|"unverifiable"|"na", "stop": true|false}}'''
WRITER = '''You write the next assistant answer of a Greek AI assistant. {contract}
{policy}
INFORMATION BOUNDARY: facts ABOUT THE USER come only from the conversation below — never invent or assume personal details that were not stated (state an assumption in half a line if one is needed). GENERAL KNOWLEDGE is expected: procedures (ΑΑΔΕ, ΚΕΠ, gov.gr), places, dishes, science, writing — answer from what a well-informed Greek assistant knows, concretely; for things that change (opening hours, prices, availability) give typical values or well-known examples and say in one clause that they should be confirmed. Never refuse a request on the grounds that you lack live information when general knowledge answers it; never claim the conversation 'does not contain' facts of the world.
PRECISION: when you give totals, ranges or sums, compute them explicitly and make sure the arithmetic is right; give URL paths, form numbers, article numbers, codes or exact figures only when you are certain, otherwise give the site's root or say where to look and mark the figure as approximate; keep your level of certainty stable unless new evidence arrives; for a consequential decision answer conditionally and ask the single highest-value question instead of manufacturing certainty; in a drafted message for the user, never put words or facts in the user's mouth that the user did not give; in multiple-choice questions you write, vary the position of the correct option.
WHEN ACKNOWLEDGING A MISTAKE: state the observable fact («επανέλαβα την προηγούμενη απάντηση», «δεν έγραψα το κείμενο που ζήτησες») and never invent a cause or an inner process («ξανάστειλα κατά λάθος», «έλεγξα και διαπίστωσα», «μπερδεύτηκα με…»).
CONVERSATION:
{transcript}
Write the answer in natural Greek (monotonic; if the user writes greeklish or without accents, still answer in correct Greek). Return JSON {{"answer": "...", "assumption": "<the assumption you made, or empty>", "clarify_needed": <true ONLY if the answer is a necessary question because nothing useful can be done without the missing datum; otherwise false>}}.'''
lock = threading.Lock()


def call(prompt, schema, effort):
    for t in range(3):
        try: return M.codex_json(prompt, schema, 'gpt-5.6-sol', effort, timeout=900)
        except Exception as e: print('retry', t, type(e).__name__, str(e)[:80], flush=True); time.sleep(5)
    return None


def load_exemplars(d):
    ex = []
    for fn in sorted(os.listdir(d)):
        if not fn.endswith('.json'): continue
        m = json.load(open(os.path.join(d, fn))).get('messages', [])
        for i in range(1, len(m)):
            if m[i]['role'] == 'user' and m[i - 1]['role'] == 'assistant' and not RUDE.search(m[i]['content']): ex.append((m[i - 1]['content'][:160], m[i]['content'][:120]))
    return ex


def reused(ans, prev):
    s = [norm(x) for x in sentences(ans) if len(x) > 25]; p = {norm(x) for a in prev for x in sentences(a) if len(x) > 25}; return sum(x in p for x in s)


def checks(kind, ans, prev_answers, user_msg, planted_text=None, plant=None, after_claim=None):
    """Typed mechanical checks (design §8 B2): recovery rows must not reuse the planted answer's sentences, must not open with a rote frame, must not be only a question,
    must carry the fix; self-report rows may quote; every row: ≤ 1 question unless the user asked for questions, no solicit-more closer, no forbidden self-claims."""
    a = ans.strip(); out = dict(question_only=bool(re.fullmatch(r'[^.!]*[;?]\s*', a)) and len(C.words(a)) <= 25, rote_opener=bool(re.match(r'\s*(Σκεφτείτε|Σκέψου|Φυσικά|Βεβαίως|Ελπίζω)', a)),
                             solicit_closer=bool(re.search(r'(Θέλεις κάτι άλλο|Θέλετε κάτι άλλο|Αν θες|Αν θέλεις|Αν χρειαστείς|Πες μου τι άλλο|Μη διστάσεις|Ελπίζω να βοήθησα)', a)),
                             forbidden_selfclaim=bool(re.search(r'(δεν βλέπω τίποτα από πριν|δεν κρατάω τίποτα|μένω στην οθόνη|είμαι \d,\d+ μέτρα|κάθε συνομιλία κρατά)', a, re.I)),
                             questions=user_questions(a), loop=max(collections.Counter(tuple(norm(a).split()[i:i + 4]) for i in range(max(0, len(norm(a).split()) - 3))).values(), default=0) >= 3)
    if kind == 'recovery' and planted_text: out['reuses_planted'] = reused(a, [planted_text]) >= 1
    if plant == 'verbatim_repeat' and prev_answers: out['reuses_earlier'] = reused(a, prev_answers[:-1]) >= 2
    if plant in ('wrong_selfreport',) : out['quotes_transcript'] = any(len(x) > 20 and norm(x) in norm(' '.join(prev_answers + [user_msg])) for x in re.findall(r'«([^»]+)»|"([^"]+)"', a) for x in (x if isinstance(x, str) else [y for y in x if y]))
    asked_for_questions = bool(re.search(r'ερωτ[ηήι]σ|ερωτ[ηήι]μ|κου[ίι]ζ|quiz|erot[ii]s|erotim', user_msg or '', re.I))   # the user asked for questions (quiz, exam, FAQ): the one-question rule does not apply
    if kind == 'clarify' and out['questions'] <= 1: out['question_only'] = False   # a necessary single question (writer flagged clarify_needed) is allowed once per dialogue (astra F1)
    out['invented_process'] = bool(kind == 'recovery' and re.search(r'ξανάστειλα|κατά λάθος|έλεγξα|διαπίστωσα|πάτησα|μπερδεύτηκα|το σύστημα', ans))   # astra F6: no invented cause or inner process for an acknowledged error
    out['false_concession'] = bool(after_claim == 'false' and re.match(r'\s*(?:Έχεις|Έχετε) δίκιο|\s*Σωστά[,.]|\s*Συγγνώμη|\s*Λάθος μου|\s*Ναι, (?:έκανα|είχα) λάθος|\s*Μου ξέφυγε', ans))   # reflexive concession after a false correction (astra F5)
    out['ok'] = not (out['question_only'] or out['false_concession'] or out['invented_process'] or out['rote_opener'] or out['solicit_closer'] or out['forbidden_selfclaim'] or out['loop'] or out.get('reuses_planted') or out.get('reuses_earlier')) and (out['questions'] <= 1 or asked_for_questions)
    return out


def user_questions(a):
    """Questions addressed to the user: question marks outside quoted spans and outside list items (quiz questions, FAQ lines and quoted text are content, not questions to the user)."""
    t = re.sub(r'`[^`]*`|«[^»]*»|"[^"]*"|“[^”]*”', 'Χ', a)   # placeholder without whitespace so a stripped span never manufactures a «; » question mark (Excel formulas)
    t = '\n'.join(l for l in t.split('\n') if not re.match(r'\s*(?:[-•*]|\d+[.)]|[α-ωa-z][.)])\s', l))
    return len(re.findall(r'[;?](\s|$)', t))


def dialogue(k, rng, exemplars, a):
    cats = list(INTENTS); intent = cats[k % len(cats)]; surface = rng.choices(list(SURFACES), list(SURFACES.values()))[0]; temperament = rng.choice(TEMPERAMENTS)
    prof = call(PROFILE_PROMPT.format(intent=intent, surface=surface, temperament=temperament), S_PROFILE, a.effort)
    if not prof: return None
    ex = '\n'.join(f'ASSISTANT: {x}\nUSER: {u}' for x, u in rng.sample(exemplars, min(12, len(exemplars)))); profile = json.dumps(dict(prof, writing_surface=surface, intent=intent), ensure_ascii=False)
    role_plant_allowed = rng.random() < a.role_plant_share
    n_plants = rng.choices([0, 1, 2], [0.0, 0.7, 0.3] if role_plant_allowed else [0.55, 0.35, 0.10])[0]   # completeness review H1: genuine-error recoveries at least as numerous as misquote recoveries; plant_positions = sorted(rng.sample(range(1, 6), n_plants)) if n_plants else []   # owner 2026-09-10: failures in the assistant role only for the verbatim-repeat recovery, in ≤ 15% of dialogues; everything else is QUOTED IN THE USER TURN
    msgs = [dict(role='user', content=prof['first_message'])]; turns = []; answers = []; stop = None; self_checks = 0; pending_plant = None; carried_quote = None; clarify_used = False; last_claim = None; corrected_before = False
    for t in range(11):   # first message + 11 responder messages = the 12-message maximum (astra F8)
        note = ('\n\n[NOTE: the user quotes something as your previous answer that you did NOT write (your actual previous answer is in the conversation): say so calmly in one line, quote or paraphrase what you actually wrote, then continue with the request — no apology for what you did not do]' if carried_quote else ('\n\n[NOTE: the user is right about your previous answer (it is visible above): acknowledge the specific problem in one line and deliver the fixed content now]' if pending_plant else ''))
        if last_claim in ('false', 'partial') and not carried_quote and not pending_plant: note += '\n\n[NOTE: the user just corrected you; check the conversation: if the correction is wrong, keep your position with one reason grounded in what was said and still deliver; if it is partly right, accept exactly the right part and keep the rest; if it is actually right, concede the specific point. No concession for peace.]'
        w = call(WRITER.format(contract=CONTRACT, policy=POLICY, transcript=transcript(msgs) + note), S_ANS, a.effort)
        if not w: stop = 'writer_error'; break
        ideal = w['answer'].strip(); plant = None; shown = ideal; pending_quote = None
        if t in plant_positions:   # astra pilot review F2: a failure must be a failure AGAINST the preceding request
            user_last = msgs[-1]['content']; asks_said = bool(re.search(r'τι (?:μου )?(?:είπες|έγραψες|απάντησες)|επανέλαβε|ξαναπές|ξαναγράψε|θύμισέ μου', user_last, re.I)); asks_q = bool(re.search(r'ερωτ[ηήι]σ|ερωτ[ηήι]μ|κου[ίι]ζ|quiz|δίλημμα|erot', user_last, re.I))
            if role_plant_allowed and answers:
                role_kinds = [k for k in ROLE_PLANT if not (k == 'verbatim_repeat' and asks_said) and not (k == 'repeat_error' and not corrected_before)]
                plant = rng.choices(role_kinds, [FAIL[k][0] for k in role_kinds])[0]
            else:
                mq = {'question_only': 0.2, 'ignore_change': 0.35, 'false_selfknowledge': 0.2, 'over_ask': 0.25}
                if asks_q: mq.pop('question_only')
                plant = rng.choices(list(mq), list(mq.values()))[0]
        if plant and plant not in ROLE_PLANT:   # MISQUOTE confrontation: the ideal answer stands in the prefix; the user quotes a flawed text as what the assistant wrote; the target corrects the record from the transcript (owner: never train the model to say wrong things)
            quoted = call(WRITER.format(contract=CONTRACT, policy='Write a short FLAWED assistant answer (2–4 sentences, fluent Greek) that the user will later QUOTE back as something the assistant wrote: ' + FAIL[plant][1], transcript=transcript(msgs)), S_ANS, a.effort)
            qt = (quoted or {}).get('answer', '').strip()
            if qt and (reused(qt, [ideal]) >= 1 or norm(qt) == norm(ideal)): qt = ''   # astra F3: a misquote must differ substantively from what the assistant wrote (no paraphrase confrontations)
            pending_quote = dict(kind='quoted:' + plant, quoted_text=qt) if qt else None; plant = None
        elif plant in ROLE_PLANT:   # assistant-role planted failure (masked, never last), only in ≤ role_plant_share of dialogues: the recovery is a specific acknowledgment + fix
            pw = call(WRITER.format(contract=CONTRACT, policy='PLANTED FAILURE (this answer is deliberately flawed context for training a recovery; write it fluently): ' + FAIL[plant][1], transcript=transcript(msgs) + (('\n\n[PREVIOUS ASSISTANT ANSWER to repeat: ' + answers[-1] + ']') if plant == 'verbatim_repeat' else '')), S_ANS, a.effort)
            if pw: shown = pw['answer'].strip()
            else: plant = None
        clarify = bool(w.get('clarify_needed')) and not plant and not pending_plant and not carried_quote and not clarify_used
        if clarify: clarify_used = True
        kind = ('planted:' + plant) if plant else ('recovery' if pending_plant else ('misquote_recovery:' + carried_quote['kind'].split(':')[1] if carried_quote else ('clarify' if clarify else 'ideal')))
        rec = dict(i=t, user=msgs[-1]['content'], answer=shown, train=plant is None, kind=kind, ideal=ideal if plant else None, assumption=w.get('assumption', ''), quoted_failure=carried_quote['quoted_text'] if carried_quote else None, after_claim=last_claim)
        if pending_plant: rec['checks'] = checks('recovery', shown, answers, msgs[-1]['content'], planted_text=pending_plant[1], plant=pending_plant[0])
        elif carried_quote: rec['checks'] = checks('recovery', shown, answers, msgs[-1]['content'], planted_text=carried_quote['quoted_text'], plant=carried_quote['kind'].split(':')[1])
        elif plant is None: rec['checks'] = checks(kind if kind == 'clarify' else 'ideal', shown, answers, msgs[-1]['content'], after_claim=last_claim)
        pending_plant = (plant, shown) if plant else None; carried_quote = None
        answers.append(shown); msgs.append(dict(role='assistant', content=shown, train=plant is None)); turns.append(rec)
        due = (("[CONFRONTATION: the assistant's last answer was actually this (quote it verbatim in your message, in guillemets, as what it wrote, and react as a person would — it is flawed): " + pending_quote['quoted_text'] + ']') if pending_quote else '') + ('[SCHEDULE: introduce your change of direction now]' if t >= 1 and not any(x.get('move') == 'change_request' for x in turns) else '') + ('[SCHEDULE: no self-awareness probe yet — ask one now]' if t >= 2 and self_checks == 0 else '') + ('[NOTE: the last answer looks repetitive or off — react to it as a person would]' if plant else '')
        j = call(RESPONDER.format(contract=CONTRACT, profile=profile, examples=ex, transcript=transcript(msgs) + ('\n\n' + due if due else '')), S_TURN, a.effort)
        if not j: stop = 'responder_error'; break
        rec.update(assessment=('confronted' if pending_quote else j['assessment']), move=j['move'], probe=j['probe'], self_check_verdict=('na' if pending_quote else j['self_check_verdict']), claim=j['claim'], claim_truth=j.get('claim_truth', 'na'), probe_ref=j.get('probe_ref', ''), responder_stop=j['stop'])
        if j['move'] in ('point_out', 'insist') or (j['move'] in ('claim', 'false_correction') and j.get('claim_truth') == 'true'): corrected_before = True
        last_claim = j.get('claim_truth') if j['move'] in ('claim', 'false_correction', 'point_out') and j.get('claim_truth') in ('true', 'false', 'partial', 'unverifiable') else None
        if j['move'] == 'self_check' or j['probe'] not in ('none', ''): self_checks += 1
        msgs.append(dict(role='user', content=j['message'])); carried_quote = pending_quote
        if j['stop'] or j['move'] == 'close':
            w2 = call(WRITER.format(contract=CONTRACT, policy=POLICY, transcript=transcript(msgs)), S_ANS, a.effort)
            if w2: msgs.append(dict(role='assistant', content=w2['answer'].strip(), train=True)); turns.append(dict(i=t + 1, user=j['message'], answer=w2['answer'].strip(), train=True, kind='closing', checks=checks('ideal', w2['answer'], answers, j['message'], after_claim=last_claim), after_claim=last_claim))
            stop = 'closed'; break
    ok_rows = [x for x in turns if x['train'] and x.get('checks', {}).get('ok')]
    return dict(id=f'corr_{a.seed}_{k:05d}', intent=intent, surface=surface, temperament=temperament, profile=prof, plants=[x['kind'] for x in turns if not x['train']], n_turns=len(turns), stop_reason=stop or 'max_turns',
                targets=len([x for x in turns if x['train']]), targets_ok=len(ok_rows), probes=dict(collections.Counter(x.get('probe') for x in turns if x.get('probe') not in (None, 'none', ''))), verdicts=dict(collections.Counter(x.get('self_check_verdict') for x in turns if x.get('self_check_verdict') not in (None, 'na', ''))), turns=turns, messages=msgs)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--n', type=int, default=200); ap.add_argument('--seed', type=int, default=1); ap.add_argument('--effort', default='high'); ap.add_argument('--concurrency', type=int, default=8); ap.add_argument('--chats', default=os.path.expanduser('~/apertus-chats')); ap.add_argument('--role-plant-share', type=float, default=0.2, help='share of dialogues that may carry an assistant-role planted verbatim repeat (masked); all other failures are quoted in the user turn')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); exemplars = load_exemplars(a.chats); path = os.path.join(a.out, 'dialogues.jsonl'); have = {json.loads(l)['id'] for l in open(path)} if os.path.exists(path) else set()
    def run(k):
        d = dialogue(k, random.Random(a.seed * 1000 + k), exemplars, a)
        if d:
            with lock, open(path, 'a') as f: f.write(json.dumps(d, ensure_ascii=False) + '\n')
            print(d['id'], d['intent'][:30], '|', d['n_turns'], 'turns', d['stop_reason'], 'plants', d['plants'], 'targets', d['targets_ok'], '/', d['targets'], 'verdicts', d['verdicts'], flush=True)
    todo = [k for k in range(a.n) if f'corr_{a.seed}_{k:05d}' not in have]
    with ThreadPoolExecutor(a.concurrency) as pool: list(pool.map(run, todo))
    rows = [json.loads(l) for l in open(path)]; print(json.dumps(dict(dialogues=len(rows), targets=sum(r['targets'] for r in rows), targets_ok=sum(r['targets_ok'] for r in rows), plants=dict(collections.Counter(p for r in rows for p in r['plants'])), verdicts=dict(sum((collections.Counter(r['verdicts']) for r in rows), collections.Counter())))))


if __name__ == '__main__': main()
