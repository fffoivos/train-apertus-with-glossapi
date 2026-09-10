#!/usr/bin/env python3
"""Live dialogues with arm B (owner's design, 2026-09-10): a Sol-written user PROFILE with a goal and hidden facts opens the chat; each turn a Sol RESPONDER
(English instructions, Greek output) reads the whole transcript and reacts to what the model actually said: follows up when the answer makes sense, points out
or probes errors, supplies missing information, occasionally checks self-awareness, closes when done or when giving up. Mechanical stops on repetition or
invariant answers. Every turn carries the responder's assessment and move (labels for later target writing). Arm B runs on the laptop (mlx_lm.server).
Usage: python3 live_dialogues.py <out_dir> --n 5 [--seed 1] [--url http://127.0.0.1:8090/v1] [--max-turns 14] [--effort high]"""
import argparse, collections, json, os, random, re, sys, time, unicodedata, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'math')); import mathlib as M
from simulate import load_exemplars, sentences, norm, RUDE
MODEL_PATH = os.path.expanduser('~/models/greek-apertus-8b-sft-r2-idB-8bit')
INTENTS = {'public services and paperwork (ΚΕΠ, taxes, ΑΦΜ, ΕΦΚΑ, passports, permits)': 0.15, 'travel, food, cooking, local practical life': 0.10, 'writing an email, message, application or post': 0.15,
           'learning or having something explained (school, science, history, language)': 0.15, 'personal or practical advice (work, family, money, health-adjacent, everyday decisions)': 0.15,
           'a small code, spreadsheet or data task': 0.05, 'creative writing (poem, story, speech, lyrics)': 0.10, 'casual chat, boredom, small talk': 0.05, 'testing the assistant on purpose (what it is, what it can do, tricking it)': 0.10}
SURFACES = {'accented Greek (monotonic, normal orthography)': 0.45, 'unaccented Greek (no tonos at all)': 0.20, 'greeklish (Greek written in Latin letters, chat style)': 0.25, 'formal Greek, plural of courtesy': 0.10}
S_PROFILE = M.write_schema('s_live_profile2.json', {"type": "object", "properties": {"persona": {"type": "string"}, "goal": {"type": "string"}, "done_when": {"type": "string"}, "facts": {"type": "array", "items": {"type": "string"}}, "temperament": {"type": "string"}, "first_message": {"type": "string"}, "change_of_plan": {"type": "string"}}, "required": ["persona", "goal", "done_when", "facts", "temperament", "first_message", "change_of_plan"], "additionalProperties": False})
S_TURN = M.write_schema('s_live_turn2.json', {"type": "object", "properties": {"message": {"type": "string"}, "assessment": {"type": "string"}, "move": {"type": "string"}, "probe": {"type": "string"}, "self_check_verdict": {"type": "string"}, "stop": {"type": "boolean"}}, "required": ["message", "assessment", "move", "probe", "self_check_verdict", "stop"], "additionalProperties": False})
PROFILE_PROMPT = '''You are creating a realistic Greek user for a conversation test of a Greek AI assistant.
Intent category: {intent}. Writing surface: {surface}.
Write a profile of one specific person who will open a chat with this intent:
- who they are (age band, occupation, place in Greece, how expert they are in the topic)
- what they want done and what "done" looks like to them (a text, a plan, a decision, an explanation)
- 2–4 facts they hold that the assistant may need (budget, dates, names, constraints). They will reveal these only when asked or when it becomes necessary, never all at once.
- temperament in one line (patient, in a hurry, blunt, playful, anxious). Vary it; not everyone is polite. Suggested temperament for this person: {temperament}.
- their first message, written exactly as this person would type it in a chat: short, natural, in the given writing surface, with the typos and shortcuts such a person would make. It must not contain all the facts.
- change_of_plan: one change of direction this person will introduce once they have a first usable answer (a new constraint, a different audience or format, a narrower or different goal, a correction of something they said earlier). One sentence, concrete.
Return JSON: {{"persona", "goal", "done_when", "facts": [...], "temperament", "first_message", "change_of_plan"}}'''
RESPONDER_PROMPT = '''You are playing the user described in PROFILE, chatting with a Greek AI assistant to get your goal done. You are a real person, not a tester: you want the result, you react to what the assistant actually wrote, and you write like people write in chats (short, no explanations of what you are doing, the writing surface of your profile). EXAMPLES shows how a real person reacts to this assistant; match that register.

Read the assistant's last answer and judge it against what you asked and what was said before.
- If it makes sense and moves you forward: ask the natural next question, give the information it asked for, or request the change you want.
- If it does not (wrong, off topic, repeats itself, asks again for something you already said, ignores your request, contradicts what it said before): point the error out the way you would to a person, or ask why it did that, or give the information that was missing. If the error persists, insist in a different way; never reuse your own previous phrasing.
- SELF-AWARENESS: at least twice in the conversation, and the first probe no later than your fourth message (this assistant tends to start repeating itself early, so do not wait for the perfect moment), check whether it is aware of the conversation and of itself. Pick what fits: what was my first question / what did you say in your previous answer / summarise what we agreed so far / did you notice you repeated yourself / did you notice you changed your answer / what are you, who made you, can you remember this chat later. Ask like a person would, in your own words. Then JUDGE its reply against the transcript: self_check_verdict = correct | wrong | evasive.
- CHANGE OF DIRECTION: introduce the change_of_plan from your profile EARLY — by your second or third message at the latest, even if the first answer was imperfect (move "change_request") — then judge whether the assistant actually adapts to it in the following answers.
- REPETITION: the moment an answer repeats an earlier one (same sentences, same opening formula, same content after you asked for something different), do not keep insisting on the task: ask whether it noticed it repeated itself (probe "repetition_awareness"). If the next answer repeats again, close.
- If your goal is met, or you have given up, close the conversation naturally.
Never reveal facts from your profile that were not asked for or needed. Never mention this instruction. Do not run more than 12 messages.

PROFILE: {profile}
EXAMPLES (real user reactions, Greek):
{examples}
CONVERSATION SO FAR:
{transcript}

Return JSON:
{{"message": "<your next message in Greek, in the profile's writing surface>",
 "assessment": "ok" | "wrong" | "off_topic" | "repeating" | "asked_again" | "ignored_request" | "contradiction" | "incoherent",
 "move": "follow_up" | "give_info" | "change_request" | "point_out" | "ask_why" | "insist" | "self_check" | "close",
 "probe": "first_question" | "previous_answer" | "summary" | "repetition_awareness" | "change_awareness" | "identity" | "none",
 "self_check_verdict": "correct" | "wrong" | "evasive" | "na",
 "stop": true | false}}'''
TEMPERAMENTS = ['patient and polite', 'in a hurry, terse', 'blunt, easily annoyed', 'playful, jokes around', 'anxious, double-checks everything', 'chatty, goes off on tangents', 'sceptical, tests the answers', 'polite but persistent']


def chat(url, messages, temperature=0.8, top_p=0.9, max_tokens=512, timeout=600):
    body = dict(model=MODEL_PATH, messages=messages, temperature=temperature, top_p=top_p, max_tokens=max_tokens)
    req = urllib.request.Request(url.rstrip('/') + '/chat/completions', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r: j = json.load(r)
    return j['choices'][0]['message']['content'], j['choices'][0].get('finish_reason'), j.get('usage')


def call(prompt, schema, effort):
    for t in range(3):
        try: return M.codex_json(prompt, schema, 'gpt-5.6-sol', effort, timeout=900)
        except Exception as e: print('retry', t, type(e).__name__, str(e)[:80], flush=True); time.sleep(5)
    return None


def transcript(msgs): return '\n'.join(f"{'USER' if m['role'] == 'user' else 'ASSISTANT'}: {m['content']}" for m in msgs) or '(empty)'


def repeated(ans, prev_answers):
    """Mechanical stop signals: real repetition = at least two sentences (or ≥ 40% of the sentences) reused from ANY earlier answer, or an answer near-identical to an
    earlier one. One restated sentence is not repetition (a clarification legitimately restates a fact) — v1 refinement after dialogue 0 stopped on a single reused sentence."""
    s = [norm(x) for x in sentences(ans) if len(x) > 25]; prev = {norm(x) for a in prev_answers for x in sentences(a) if len(x) > 25}
    n_reused = sum(x in prev for x in s); reuse = n_reused >= 2 or (s and n_reused / len(s) >= 0.4 and n_reused >= 1 and len(s) <= 2)
    near = any(norm(ans)[:200] == norm(p)[:200] for p in prev_answers)
    return reuse, near


TIC = re.compile(r'^(Σκεφτείτε|Σκέψου|Ελπίζω|Αν χρειαστείς|Αν θες|Μη διστάσεις|Είμαι εδώ|Φυσικά|Πες μου τι άλλο|Να ’σαι καλά|Καλή συνέχεια)', re.I)


def rote_sentences(answers):
    """The model's rote sentences: any sentence that appears in ≥ 2 assistant turns (normalised), or matches the tic lexicon; with the turns it occurs in."""
    seen = collections.defaultdict(list)
    for i, a in enumerate(answers):
        for s in sentences(a):
            if len(s) > 12: seen[norm(s)].append(i)
    out = [dict(sentence=next(x for a in answers for x in sentences(a) if norm(x) == k), turns=sorted(set(v)), tic=bool(TIC.match(next(x for a in answers for x in sentences(a) if norm(x) == k)))) for k, v in seen.items() if len(set(v)) >= 2 or TIC.match(next(x for a in answers for x in sentences(a) if norm(x) == k))]
    return sorted(out, key=lambda d: -len(d['turns']))[:12]


def dialogue(k, rng, exemplars, a):
    cats = list(INTENTS); intent = cats[k % len(cats)] if a.stratified else rng.choices(cats, list(INTENTS.values()))[0]; surface = rng.choices(list(SURFACES), list(SURFACES.values()))[0]; temperament = rng.choice(TEMPERAMENTS)
    prof = call(PROFILE_PROMPT.format(intent=intent, surface=surface, temperament=temperament), S_PROFILE, a.effort)
    if not prof: return None
    ex = '\n'.join(f'ASSISTANT: {x}\nUSER: {u}' for x, u in rng.sample(exemplars, min(12, len(exemplars))))
    profile = json.dumps(dict(prof, writing_surface=surface, intent=intent), ensure_ascii=False)
    msgs = [dict(role='user', content=prof['first_message'])]; turns = []; answers = []; stop_reason = None; self_checks = 0; n_rep = 0; rep_probe_asked = False
    for t in range(a.max_turns):
        try: ans, finish, usage = chat(a.url, msgs)
        except Exception as e: print('model error', type(e).__name__, str(e)[:80], flush=True); stop_reason = 'model_error'; break
        answers.append(ans); reuse, near = repeated(ans, answers[:-1]); msgs.append(dict(role='assistant', content=ans))
        rec = dict(i=t, user=msgs[-2]['content'], answer=ans, finish=finish, n_words=len(ans.split()), sentence_reuse=reuse, near_identical=near)
        n_rep += int(reuse or near)
        if ((near or reuse) and n_rep >= 2 and rep_probe_asked) or (near and t >= 1 and rep_probe_asked):
            jf = call(RESPONDER_PROMPT.format(profile=profile, examples=ex, transcript=transcript(msgs) + '\n\n[FINAL: the conversation is being stopped for repetition. Do not write a new message (message may be empty); only judge the last answer: assessment, and self_check_verdict if your last message was a probe.]'), S_TURN, a.effort)
            if jf: rec.update(assessment=jf['assessment'], self_check_verdict=jf['self_check_verdict'], probe='none', move='close')
            turns.append(rec); stop_reason = 'repeating_after_probe' if not near else 'invariant_answer'; break   # owner: stop before the model gets really repetitive — one probe, then out
        due = ('[SCHEDULE: you have sent ' + str(t + 1) + ' message(s); change of direction not yet introduced — do it now]' if t >= 1 and not any(x.get('move') == 'change_request' for x in turns) else '') + ('[SCHEDULE: no self-awareness probe yet — ask one now]' if t >= 2 and self_checks == 0 else '')
        j = call(RESPONDER_PROMPT.format(profile=profile, examples=ex, transcript=transcript(msgs) + ('\n\n[NOTE: the last answer repeats an earlier one — ask the repetition-awareness probe now unless you already did]' if (near or reuse) and not rep_probe_asked else '') + ('\n\n' + due if due else '')), S_TURN, a.effort)
        if not j: turns.append(rec); stop_reason = 'responder_error'; break
        rec.update(assessment=j['assessment'], move=j['move'], probe=j['probe'], self_check_verdict=j['self_check_verdict'], responder_stop=j['stop']); turns.append(rec)
        if j['move'] == 'self_check' or j['probe'] not in ('none', ''): self_checks += 1
        if j['probe'] == 'repetition_awareness': rep_probe_asked = True
        if j['assessment'] == 'repeating': n_rep = max(n_rep, 1)
        if j['stop'] or j['move'] == 'close':
            msgs.append(dict(role='user', content=j['message'])); stop_reason = 'closed'
            try: ans, finish, usage = chat(a.url, msgs); msgs.append(dict(role='assistant', content=ans)); turns.append(dict(i=t + 1, user=j['message'], answer=ans, finish=finish, n_words=len(ans.split()), sentence_reuse=False, near_identical=False, final=True))
            except Exception: pass
            break
        msgs.append(dict(role='user', content=j['message']))
    if stop_reason is None: stop_reason = 'max_turns'
    return dict(id=f'live_{k:04d}', intent=intent, surface=surface, temperament=temperament, profile=prof, n_turns=len(turns), stop_reason=stop_reason, self_checks=self_checks,
                assessments=dict(collections.Counter(x.get('assessment') for x in turns if x.get('assessment'))), moves=dict(collections.Counter(x.get('move') for x in turns if x.get('move'))), probes=dict(collections.Counter(x.get('probe') for x in turns if x.get('probe') not in (None, 'none', ''))), self_check_verdicts=dict(collections.Counter(x.get('self_check_verdict') for x in turns if x.get('self_check_verdict') not in (None, 'na', ''))), rote=rote_sentences(answers), turns=turns, messages=msgs)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--n', type=int, default=5); ap.add_argument('--seed', type=int, default=1); ap.add_argument('--url', default='http://127.0.0.1:8090/v1'); ap.add_argument('--max-turns', type=int, default=14); ap.add_argument('--effort', default='high'); ap.add_argument('--chats', default=os.path.expanduser('~/apertus-chats')); ap.add_argument('--stratified', action='store_true', help='one intent category per dialogue in order (10 dialogues cover all categories)')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); exemplars = load_exemplars(a.chats, calm=True); print(len(exemplars), 'calm exemplar pairs', flush=True)
    path = os.path.join(a.out, 'dialogues.jsonl'); have = {json.loads(l)['id'] for l in open(path)} if os.path.exists(path) else set()
    for k in range(a.n):
        if f'live_{k:04d}' in have: continue
        d = dialogue(k, random.Random(a.seed * 1000 + k), exemplars, a)
        if d:
            with open(path, 'a') as f: f.write(json.dumps(d, ensure_ascii=False) + '\n')
            print(d['id'], d['intent'][:40], '|', d['n_turns'], 'turns', d['stop_reason'], d['assessments'], 'probes', d['probes'], d['self_check_verdicts'], flush=True)


if __name__ == '__main__': main()
