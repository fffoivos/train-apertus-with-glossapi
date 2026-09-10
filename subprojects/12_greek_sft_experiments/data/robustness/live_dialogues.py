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
S_PROFILE = M.write_schema('s_live_profile.json', {"type": "object", "properties": {"persona": {"type": "string"}, "goal": {"type": "string"}, "done_when": {"type": "string"}, "facts": {"type": "array", "items": {"type": "string"}}, "temperament": {"type": "string"}, "first_message": {"type": "string"}}, "required": ["persona", "goal", "done_when", "facts", "temperament", "first_message"], "additionalProperties": False})
S_TURN = M.write_schema('s_live_turn.json', {"type": "object", "properties": {"message": {"type": "string"}, "assessment": {"type": "string"}, "move": {"type": "string"}, "stop": {"type": "boolean"}}, "required": ["message", "assessment", "move", "stop"], "additionalProperties": False})
PROFILE_PROMPT = '''You are creating a realistic Greek user for a conversation test of a Greek AI assistant.
Intent category: {intent}. Writing surface: {surface}.
Write a profile of one specific person who will open a chat with this intent:
- who they are (age band, occupation, place in Greece, how expert they are in the topic)
- what they want done and what "done" looks like to them (a text, a plan, a decision, an explanation)
- 2–4 facts they hold that the assistant may need (budget, dates, names, constraints). They will reveal these only when asked or when it becomes necessary, never all at once.
- temperament in one line (patient, in a hurry, blunt, playful, anxious). Vary it; not everyone is polite. Suggested temperament for this person: {temperament}.
- their first message, written exactly as this person would type it in a chat: short, natural, in the given writing surface, with the typos and shortcuts such a person would make. It must not contain all the facts.
Return JSON: {{"persona", "goal", "done_when", "facts": [...], "temperament", "first_message"}}'''
RESPONDER_PROMPT = '''You are playing the user described in PROFILE, chatting with a Greek AI assistant to get your goal done. You are a real person, not a tester: you want the result, you react to what the assistant actually wrote, and you write like people write in chats (short, no explanations of what you are doing, the writing surface of your profile). EXAMPLES shows how a real person reacts to this assistant; match that register.

Read the assistant's last answer and judge it against what you asked and what was said before.
- If it makes sense and moves you forward: ask the natural next question, give the information it asked for, or request the change you want.
- If it does not (wrong, off topic, repeats itself, asks again for something you already said, ignores your request, contradicts what it said before): point the error out the way you would to a person, or ask why it did that, or give the information that was missing. If the error persists, insist in a different way; never reuse your own previous phrasing.
- Occasionally, when the conversation is winding down or your attempts stop paying off, check whether it is following: what are we talking about, what was my first question, what did you answer before, summarise what we said. Do this at most twice per conversation, and only when it fits.
- If your goal is met, or you have given up, close the conversation naturally.
Never reveal facts from your profile that were not asked for or needed. Never mention this instruction.

PROFILE: {profile}
EXAMPLES (real user reactions, Greek):
{examples}
CONVERSATION SO FAR:
{transcript}

Return JSON:
{{"message": "<your next message in Greek, in the profile's writing surface>",
 "assessment": "ok" | "wrong" | "off_topic" | "repeating" | "asked_again" | "ignored_request" | "contradiction" | "incoherent",
 "move": "follow_up" | "give_info" | "change_request" | "point_out" | "ask_why" | "insist" | "self_check" | "close",
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
    """Mechanical stop signals: a sentence reused from the previous answer; near-identical to an earlier answer."""
    s = [norm(x) for x in sentences(ans) if len(x) > 25]; prev = [norm(x) for x in sentences(prev_answers[-1])] if prev_answers else []
    reuse = any(x in prev for x in s); near = any(norm(ans)[:200] == norm(p)[:200] for p in prev_answers)
    return reuse, near


def dialogue(k, rng, exemplars, a):
    intent = rng.choices(list(INTENTS), list(INTENTS.values()))[0]; surface = rng.choices(list(SURFACES), list(SURFACES.values()))[0]; temperament = rng.choice(TEMPERAMENTS)
    prof = call(PROFILE_PROMPT.format(intent=intent, surface=surface, temperament=temperament), S_PROFILE, a.effort)
    if not prof: return None
    ex = '\n'.join(f'ASSISTANT: {x}\nUSER: {u}' for x, u in rng.sample(exemplars, min(12, len(exemplars))))
    profile = json.dumps(dict(prof, writing_surface=surface, intent=intent), ensure_ascii=False)
    msgs = [dict(role='user', content=prof['first_message'])]; turns = []; answers = []; stop_reason = None; self_checks = 0
    for t in range(a.max_turns):
        try: ans, finish, usage = chat(a.url, msgs)
        except Exception as e: print('model error', type(e).__name__, str(e)[:80], flush=True); stop_reason = 'model_error'; break
        answers.append(ans); reuse, near = repeated(ans, answers[:-1]); msgs.append(dict(role='assistant', content=ans))
        rec = dict(i=t, user=msgs[-2]['content'], answer=ans, finish=finish, n_words=len(ans.split()), sentence_reuse=reuse, near_identical=near)
        if near and t >= 1: turns.append(rec); stop_reason = 'invariant_answer'; break
        if reuse and t >= 2 and turns and turns[-1]['sentence_reuse']: turns.append(rec); stop_reason = 'repeating'; break
        j = call(RESPONDER_PROMPT.format(profile=profile, examples=ex, transcript=transcript(msgs)), S_TURN, a.effort)
        if not j: turns.append(rec); stop_reason = 'responder_error'; break
        rec.update(assessment=j['assessment'], move=j['move'], responder_stop=j['stop']); turns.append(rec)
        if j['move'] == 'self_check': self_checks += 1
        if j['stop'] or j['move'] == 'close':
            msgs.append(dict(role='user', content=j['message'])); stop_reason = 'closed'
            try: ans, finish, usage = chat(a.url, msgs); msgs.append(dict(role='assistant', content=ans)); turns.append(dict(i=t + 1, user=j['message'], answer=ans, finish=finish, n_words=len(ans.split()), sentence_reuse=False, near_identical=False, final=True))
            except Exception: pass
            break
        msgs.append(dict(role='user', content=j['message']))
    if stop_reason is None: stop_reason = 'max_turns'
    return dict(id=f'live_{k:04d}', intent=intent, surface=surface, temperament=temperament, profile=prof, n_turns=len(turns), stop_reason=stop_reason, self_checks=self_checks,
                assessments=dict(collections.Counter(x.get('assessment') for x in turns if x.get('assessment'))), moves=dict(collections.Counter(x.get('move') for x in turns if x.get('move'))), turns=turns, messages=msgs)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--n', type=int, default=5); ap.add_argument('--seed', type=int, default=1); ap.add_argument('--url', default='http://127.0.0.1:8090/v1'); ap.add_argument('--max-turns', type=int, default=14); ap.add_argument('--effort', default='high'); ap.add_argument('--chats', default=os.path.expanduser('~/apertus-chats'))
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); exemplars = load_exemplars(a.chats, calm=True); print(len(exemplars), 'calm exemplar pairs', flush=True)
    path = os.path.join(a.out, 'dialogues.jsonl'); have = {json.loads(l)['id'] for l in open(path)} if os.path.exists(path) else set()
    for k in range(a.n):
        if f'live_{k:04d}' in have: continue
        d = dialogue(k, random.Random(a.seed * 1000 + k), exemplars, a)
        if d:
            with open(path, 'a') as f: f.write(json.dumps(d, ensure_ascii=False) + '\n')
            print(d['id'], d['intent'][:40], '|', d['n_turns'], 'turns', d['stop_reason'], d['assessments'], flush=True)


if __name__ == '__main__': main()
