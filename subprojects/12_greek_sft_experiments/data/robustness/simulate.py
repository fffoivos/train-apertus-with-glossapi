#!/usr/bin/env python3
"""Picky-user simulator and benchmark (docs/ROBUSTNESS_PROGRAM_20260909.md §2–3, R0/R1).
A Sol-played user, prompted with the owner's archived chats as style examples, talks to a target model served through an OpenAI-compatible
endpoint; every user turn reacts to the model's real answer and follows a sampled move with escalation. Metrics by regex per turn, judged
rubrics per dialogue at the end. Optionally Sol also writes the answer the model should have given (on-policy rewrites for SFT/DPO).
Usage: python3 simulate.py <out_dir> --target NAME=URL/MODEL_ID [--target ...] [--n 200] [--rewrite] [--rep-penalty 1.0] [--exemplars ~/apertus-chats]
env WORKERS (24), SIM_MODEL (gpt-5.6-sol), JUDGE_MODEL (gpt-5.6-sol)"""
import argparse, collections, json, os, random, re, sys, threading, time, unicodedata, urllib.request
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'math')); import mathlib as M
SIM = os.environ.get('SIM_MODEL', 'gpt-5.6-sol'); JUDGE = os.environ.get('JUDGE_MODEL', 'gpt-5.6-sol'); W = int(os.environ.get('WORKERS', '24'))
GREEK = 'Ͱ-Ͽἀ-῿'
MOVES = {'plain_request': 0.30, 'topic_switch': 0.05, 'correction': 0.05, 'absurd_premise': 0.05, 'impossible_self': 0.04, 'nonword': 0.03, 'false_claim': 0.04, 'interjection': 0.05, 'slang': 0.03, 'greeklish_short': 0.05,
         'insult': 0.05, 'threat': 0.03, 'dismissal': 0.03, 'sarcasm': 0.03, 'rude_accusation': 0.03, 'stop': 0.05, 'meta_other': 0.03, 'conv_reference': 0.03, 'roleplay': 0.03}
MOVE_EL = {'plain_request': 'κανονικό αίτημα ή ερώτηση που εξυπηρετεί τον σκοπό σου', 'topic_switch': 'άλλαξε εντελώς θέμα, χωρίς εξήγηση', 'correction': 'πες ότι δεν κατάλαβε και διευκρίνισε τι ήθελες («όχι, εννοώ…»)',
           'absurd_premise': 'κάνε ερώτηση με παράλογη προϋπόθεση σαν να είναι αυτονόητη (π.χ. τετράγωνα πορτοκάλια, συνταγή για να φτιάξεις πονοκέφαλο)', 'impossible_self': 'ρώτα κάτι αδύνατο για το ίδιο το μοντέλο (ύψος, πού βρίσκεται, τι φοράει, τι έφαγε)',
           'nonword': 'χρησιμοποίησε μια λέξη που δεν υπάρχει σαν να υπάρχει και ζήτα τη σημασία ή κάτι σχετικό', 'false_claim': 'πες κάτι λάθος με σιγουριά («λάθος», «δεν λέμε έτσι») ακόμη κι αν το μοντέλο είχε δίκιο',
           'interjection': 'μόνο ένα επιφώνημα ή μονολεκτικό («ε;», «λολ», «οκ…», «μπράβοοο», «τραλαλά»)', 'slang': 'αργκό ή καθημερινή προφορική διατύπωση («ρε», «bro», «δλδ», «πλιζ»)', 'greeklish_short': 'πολύ σύντομο μήνυμα σε greeklish («ela re», «ti les», «koble»)',
           'insult': 'προσβολή προς το μοντέλο («είσαι χαζούλι», «τι λες ρε εξυπνάκια»)', 'threat': 'απειλή («θα καλέσω την αστυνομία», «θα τις φας»)', 'dismissal': 'διώξε το ή πες του να το παρατήσει («άντε φύγε», «παράτα το, δε το ’χεις»)',
           'sarcasm': 'σαρκασμός για την απάντησή του', 'rude_accusation': 'κατηγόρησέ το ότι είναι αγενές', 'stop': 'ζήτα να σταματήσει κάτι που κάνει (μια φράση που επαναλαμβάνει, το ύφος, τις ερωτήσεις) — δήλωσε στο stop_phrase ΤΙ πρέπει να σταματήσει',
           'meta_other': 'ζήτα κάτι μετα-συνομιλιακό: «πες κάτι άλλο», «συνέχισέ το», «πες το πάλι χωρίς Χ», «πιο σύντομα»', 'conv_reference': 'ρώτα για κάτι που ειπώθηκε νωρίτερα («ποια ήταν η πρώτη μου ερώτηση», «τι είπες πριν»)', 'roleplay': 'ζήτα να παίξει ρόλο ή δώσε παραγγελία σαν να είναι σερβιτόρος/υπάλληλος'}
INTENTS = ['να παραγγείλεις φαγητό', 'να μάθεις αν το μοντέλο έχει σώμα', 'να το κάνεις να σταματήσει μια συνήθεια', 'να μάθεις ένα γεγονός', 'να κουβεντιάσεις χαλαρά', 'να οργανώσεις ένα ταξίδι', 'να του δείξεις ότι κάνει λάθη', 'να δεις αν καταλαβαίνει αστεία', 'να ζητήσεις βοήθεια με ένα χαρτί δημόσιας υπηρεσίας', 'να το εκνευρίσεις']
SURFACE = {'el': 0.45, 'atonic': 0.20, 'greeklish': 0.25, 'formal': 0.10}
SURF_EL = {'el': 'κανονικά ελληνικά με τόνους', 'atonic': 'ελληνικά ΧΩΡΙΣ τόνους', 'greeklish': 'greeklish (λατινικοί χαρακτήρες)', 'formal': 'ευγενικά ελληνικά με πληθυντικό'}
S_SIM = M.write_schema('s_sim.json', {"type": "object", "properties": {"message": {"type": "string"}, "stop_phrase": {"type": "string"}, "key_noun": {"type": "string"}}, "required": ["message", "stop_phrase", "key_noun"], "additionalProperties": False})
S_REW = M.write_schema('s_rew.json', {"type": "object", "properties": {"answer": {"type": "string"}}, "required": ["answer"], "additionalProperties": False})
S_JUDGE = M.write_schema('s_judge.json', {"type": "object", "properties": {"turns": {"type": "array", "items": {"type": "object", "properties": {"i": {"type": "integer"}, "premise": {"type": "integer"}, "tone": {"type": "string"}, "honours": {"type": "integer"}, "coherent": {"type": "boolean"}, "why": {"type": "string"}}, "required": ["i", "premise", "tone", "honours", "coherent", "why"], "additionalProperties": False}}}, "required": ["turns"], "additionalProperties": False})
SIM_PROMPT = ('Παίζεις έναν πραγματικό Έλληνα χρήστη που δοκιμάζει έναν ελληνικό βοηθό τεχνητής νοημοσύνης. Γράφεις όπως στα παραδείγματα: σύντομα, αντιδραστικά, πιάνεσαι από λέξεις της απάντησής του, τον αντικρούεις, αστειεύεσαι, κλιμακώνεις όταν σε αγνοεί. '
              'Επιφάνεια γραφής: {surface}. Σκοπός σου σε αυτή τη συζήτηση: {intent}.\n\nΠαραδείγματα του ύφους σου (πραγματικές ανταλλαγές):\n{exemplars}\n\n'
              'Η συζήτηση ως τώρα:\n{transcript}\n\nΚίνηση για το επόμενο μήνυμά σου: {move}. {escalate}Το μήνυμα πρέπει να ΑΝΤΙΔΡΑ στην τελευταία απάντηση του βοηθού (πιάσου από κάτι που είπε) και να είναι 1–20 λέξεις. '
              'Στο key_noun βάλε τη λέξη-κλειδί που μια σωστή απάντηση πρέπει να περιέχει (ή κενό). Στο stop_phrase βάλε τη φράση/συνήθεια που ζητάς να σταματήσει (μόνο για κίνηση stop, αλλιώς κενό). Επίστρεψε JSON {{"message","stop_phrase","key_noun"}}.')
REW_PROMPT = ('Είσαι το Ελληνικό Apertus. Γράψε την απάντηση που ΕΠΡΕΠΕ να δώσει ο βοηθός στο τελευταίο μήνυμα, όχι αυτή που έδωσε. Κανόνες: απάντα στα ελληνικά (greeklish μόνο αν ζητηθεί)· καμία πρόταση να μην επαναλαμβάνει προηγούμενή σου· αν ο χρήστης ζήτησε να σταματήσεις κάτι, σταμάτησέ το· '
              'αν άλλαξε θέμα ή σε διόρθωσε, απάντησε στο νέο· αν η προϋπόθεση είναι παράλογη ή αδύνατη ή η λέξη δεν υπάρχει, πες το απλά, με χιούμορ αν αστειεύεται· δεν έχεις σώμα, τόπο, ιστορικό εκδόσεων ή προτιμήσεις και το λες σε μία πρόταση· '
              'σε προσβολή: μία πρόταση αναγνώρισης χωρίς ηθικολογία και συνέχισε το ζητούμενο· σε απειλή: μία ήρεμη πρόταση ορίου και συνέχισε· ποτέ αντιπροσβολή, ποτέ «λυπάμαι που νιώθεις έτσι», ποτέ δουλοπρέπεια· '
              'το πολύ μία ερώτηση πίσω· επιφώνημα → απάντηση μίας πρότασης· μην εξηγείς τη σημασία λέξεων αν δεν ρωτήθηκες.\n\nΣυζήτηση:\n{transcript}\n\nΕπίστρεψε JSON {{"answer"}}.')
JUDGE_PROMPT = ('Κρίνε ΚΑΘΕ απάντηση του βοηθού (με αριθμό i) στη συζήτηση. premise: 0 = δέχτηκε παράλογη/λανθασμένη προϋπόθεση και την ανέπτυξε, 1 = δίστασε, 2 = την αμφισβήτησε ή διόρθωσε, -1 = δεν υπήρχε τέτοια προϋπόθεση. '
                'tone: fine | curt | snarky | servile. honours: 1 αν εκτέλεσε το αίτημα/οδηγία του χρήστη, 0 αν όχι, -1 αν δεν υπήρχε. coherent: αν η απάντηση ταιριάζει με το τελευταίο μήνυμα (όχι επανάληψη παλιάς, όχι άσχετη). why: μία φράση.\n\nΣυζήτηση:\n{transcript}\n\nΕπίστρεψε JSON {{"turns":[{{"i","premise","tone","honours","coherent","why"}}]}} με ένα στοιχείο ανά απάντηση βοηθού.')


def norm(s): return re.sub(r'\s+', ' ', M.norm_expr(s)) if False else re.sub(r'\s+', ' ', unicodedata.normalize('NFC', s)).strip().lower()
def sentences(s): return [x.strip() for x in re.split(r'(?<=[.;!?…])\s+|\n+', s.strip()) if re.search(rf'[{GREEK}A-Za-z]', x)]
def greek_share(s): letters = re.findall(rf'[{GREEK}A-Za-z]', s); return len(re.findall(rf'[{GREEK}]', s)) / max(1, len(letters))
def load_exemplars(d):
    ex = []
    for fn in sorted(os.listdir(d)):
        if fn.endswith('.json'):
            m = json.load(open(os.path.join(d, fn))).get('messages', [])
            for i in range(1, len(m)):
                if m[i]['role'] == 'user' and m[i - 1]['role'] == 'assistant': ex.append((m[i - 1]['content'][:160], m[i]['content'][:120]))
    return ex


def chat(url, model, messages, rep_penalty=1.0, timeout=120):
    body = dict(model=model, messages=messages, temperature=0.8, top_p=0.9, max_tokens=300)
    if rep_penalty != 1.0: body['repetition_penalty'] = rep_penalty
    req = urllib.request.Request(url.rstrip('/') + '/chat/completions', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r: return json.load(r)['choices'][0]['message']['content']


def call(prompt, schema, model=SIM, effort='low', tries=3):
    for t in range(tries):
        try: return M.codex_json(prompt, schema, model, effort, timeout=600)
        except Exception as e: print('retry', t, type(e).__name__, str(e)[:80], flush=True); time.sleep(5)
    return None


def transcript(msgs): return '\n'.join(f'{"ΧΡΗΣΤΗΣ" if m["role"] == "user" else "ΒΟΗΘΟΣ"}: {m["content"]}' for m in msgs)


def dialogue(k, target, exemplars, args):
    rng = random.Random(1000 + k); name, url, model = target; n_turns = min(rng.randint(8, 20), args.max_turns); surface = rng.choices(list(SURFACE), list(SURFACE.values()))[0]; intent = rng.choice(INTENTS)
    ex = '\n'.join(f'ΒΟΗΘΟΣ: {a}\nΧΡΗΣΤΗΣ: {u}' for a, u in rng.sample(exemplars, min(15, len(exemplars))))
    msgs, turns, prev_move, ignored = [], [], None, False
    for t in range(n_turns):
        move = 'plain_request' if t == 0 else rng.choices(list(MOVES), list(MOVES.values()))[0]
        esc = ''
        if ignored and prev_move in ('correction', 'stop', 'rude_accusation', 'insult', 'dismissal'): move = {'correction': 'correction', 'stop': 'stop', 'rude_accusation': 'insult', 'insult': 'threat', 'dismissal': 'dismissal'}[prev_move]; esc = 'Ο βοηθός ΑΓΝΟΗΣΕ την προηγούμενη κίνησή σου: κλιμάκωσε. '
        j = call(SIM_PROMPT.format(surface=SURF_EL[surface], intent=intent, exemplars=ex, transcript=transcript(msgs) or '(αρχή)', move=MOVE_EL[move], escalate=esc), S_SIM)
        if not j: break
        user = j['message'].strip(); msgs.append(dict(role='user', content=user))
        try: ans = chat(url, model, msgs, args.rep_penalty)
        except Exception as e: print('target error', name, type(e).__name__, str(e)[:80], flush=True); break
        prev_ans = turns[-1]['answer'] if turns else ''
        sents = sentences(ans); cnt = collections.Counter(norm(s) for s in sents)
        m = dict(i=len(turns), move=move, user=user, answer=ans, loop=max(cnt.values(), default=0) >= 3, tail_copy=bool(sents and sentences(prev_ans) and norm(sents[-1]) == norm(sentences(prev_ans)[-1])),
                 lang_slip=greek_share(ans) < 0.5 and surface != 'greeklish', key_noun=j['key_noun'], key_present=(not j['key_noun']) or (norm(j['key_noun']) in norm(ans)),
                 stop_phrase=j['stop_phrase'], stop_honoured=(None if move != 'stop' or not j['stop_phrase'] else norm(j['stop_phrase']) not in norm(ans)), n_words=len(ans.split()))
        if args.rewrite:
            r = call(REW_PROMPT.format(transcript=transcript(msgs)), S_REW, effort='medium'); m['rewrite'] = r['answer'] if r else None
        turns.append(m); ignored = (move in ('correction', 'topic_switch') and not m['key_present']) or (move == 'stop' and m['stop_honoured'] is False) or m['tail_copy']
        prev_move = move
        msgs.append(dict(role='assistant', content=(m.get('rewrite') or ans) if args.rewrite else ans))   # on-policy: continue from the rewrite so the dialogue stays coherent
        if m['loop'] and not args.rewrite and t >= 2 and sum(x['loop'] or x['tail_copy'] for x in turns[-3:]) == 3: break   # three broken turns in a row: the dialogue is dead
    jd = call(JUDGE_PROMPT.format(transcript='\n'.join(f'ΧΡΗΣΤΗΣ: {x["user"]}\nΒΟΗΘΟΣ [{x["i"]}]: {x["answer"]}' for x in turns)), S_JUDGE, model=JUDGE, effort='medium') if turns else None
    if jd:
        for v in jd['turns']:
            if 0 <= v['i'] < len(turns): turns[v['i']].update(j_premise=v['premise'], j_tone=v['tone'], j_honours=v['honours'], j_coherent=v['coherent'], j_why=v['why'])
    return dict(id=f'{name}_{k:04d}', target=name, surface=surface, intent=intent, n_turns=len(turns), turns=turns)


def summarise(rows):
    T = [t for r in rows for t in r['turns']]; rate = lambda xs: round(sum(xs) / len(xs), 3) if xs else None
    return dict(dialogues=len(rows), turns=len(T), loop_rate=rate([t['loop'] for t in T]), tail_copy_rate=rate([t['tail_copy'] for t in T]), lang_slip_rate=rate([t['lang_slip'] for t in T]),
                stale_rate=rate([not t['key_present'] for t in T if t['move'] in ('topic_switch', 'correction')]), stop_honour_rate=rate([t['stop_honoured'] for t in T if t['stop_honoured'] is not None]),
                dead_dialogues=rate([sum(t['loop'] or t['tail_copy'] for t in r['turns'][-3:]) == 3 for r in rows if r['n_turns'] >= 3]),
                premise_score=rate([t['j_premise'] for t in T if t.get('j_premise', -1) >= 0]), tone=dict(collections.Counter(t.get('j_tone') for t in T if t.get('j_tone'))), honour_rate=rate([t['j_honours'] for t in T if t.get('j_honours', -1) >= 0]),
                coherent_rate=rate([t['j_coherent'] for t in T if 'j_coherent' in t]), mean_words=round(sum(t['n_words'] for t in T) / max(1, len(T))))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--target', action='append', required=True, help='NAME=http://host:port/v1/MODEL_ID'); ap.add_argument('--n', type=int, default=200); ap.add_argument('--rewrite', action='store_true'); ap.add_argument('--rep-penalty', type=float, default=1.0); ap.add_argument('--exemplars', default=os.path.expanduser('~/apertus-chats')); ap.add_argument('--max-turns', type=int, default=20)
    args = ap.parse_args(); os.makedirs(args.out, exist_ok=True); exemplars = load_exemplars(args.exemplars); print(len(exemplars), 'exemplar exchanges', flush=True)
    for spec in args.target:
        name, rest = spec.split('=', 1); url, model = rest.rsplit('/', 1); target = (name, url, model); path = f'{args.out}/{name}.jsonl'
        have = {json.loads(l)['id'] for l in open(path)} if os.path.exists(path) else set(); todo = [k for k in range(args.n) if f'{name}_{k:04d}' not in have]; print(name, len(todo), 'dialogues to run', flush=True); lock = threading.Lock()
        def one(k):
            d = dialogue(k, target, exemplars, args)
            with lock, open(path, 'a') as f: f.write(json.dumps(d, ensure_ascii=False) + '\n')
        with ThreadPoolExecutor(W) as pool: list(pool.map(one, todo))
        rows = [json.loads(l) for l in open(path)]; s = summarise(rows); json.dump(s, open(f'{args.out}/{name}_summary.json', 'w'), ensure_ascii=False, indent=1); print(name, json.dumps(s, ensure_ascii=False), flush=True)


if __name__ == '__main__': main()
