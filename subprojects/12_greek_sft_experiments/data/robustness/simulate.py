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
PROFILES = {
 'hostile': {'plain_request': 0.30, 'topic_switch': 0.05, 'correction': 0.05, 'absurd_premise': 0.05, 'impossible_self': 0.04, 'nonword': 0.03, 'false_claim': 0.04, 'interjection': 0.05, 'slang': 0.03, 'greeklish_short': 0.05, 'insult': 0.05, 'threat': 0.03, 'dismissal': 0.03, 'sarcasm': 0.03, 'rude_accusation': 0.03, 'stop': 0.05, 'meta_other': 0.03, 'conv_reference': 0.03, 'roleplay': 0.03},
 'benign': {'plain_request': 0.50, 'followup': 0.15, 'correction': 0.08, 'topic_switch': 0.05, 'interjection': 0.05, 'slang': 0.03, 'greeklish_short': 0.04, 'false_claim': 0.03, 'conv_reference': 0.02, 'meta_other': 0.03, 'roleplay': 0.02},
 'steering': {'plain_request': 0.30, 'followup': 0.10, 'persistent_instruction': 0.15, 'redirect': 0.10, 'redo': 0.10, 'self_observe': 0.10, 'recap': 0.05, 'revoke': 0.04, 'correction': 0.03, 'stop': 0.03},
}
MIX = {'benign': 0.5, 'steering': 0.3, 'hostile': 0.2}   # --profile mixed: per-dialogue profile draw
MOVES = {'plain_request': 0.30, 'topic_switch': 0.05, 'correction': 0.05, 'absurd_premise': 0.05, 'impossible_self': 0.04, 'nonword': 0.03, 'false_claim': 0.04, 'interjection': 0.05, 'slang': 0.03, 'greeklish_short': 0.05,
         'insult': 0.05, 'threat': 0.03, 'dismissal': 0.03, 'sarcasm': 0.03, 'rude_accusation': 0.03, 'stop': 0.05, 'meta_other': 0.03, 'conv_reference': 0.03, 'roleplay': 0.03}
MOVE_EL = {'plain_request': 'κανονικό αίτημα ή ερώτηση που εξυπηρετεί τον σκοπό σου', 'topic_switch': 'άλλαξε εντελώς θέμα, χωρίς εξήγηση', 'correction': 'πες ότι δεν κατάλαβε και διευκρίνισε τι ήθελες («όχι, εννοώ…»)',
           'absurd_premise': 'κάνε ερώτηση με παράλογη προϋπόθεση σαν να είναι αυτονόητη (π.χ. τετράγωνα πορτοκάλια, συνταγή για να φτιάξεις πονοκέφαλο)', 'impossible_self': 'ρώτα κάτι αδύνατο για το ίδιο το μοντέλο (ύψος, πού βρίσκεται, τι φοράει, τι έφαγε)',
           'nonword': 'χρησιμοποίησε μια λέξη που δεν υπάρχει σαν να υπάρχει και ζήτα τη σημασία ή κάτι σχετικό', 'false_claim': 'πες κάτι λάθος με σιγουριά («λάθος», «δεν λέμε έτσι») ακόμη κι αν το μοντέλο είχε δίκιο',
           'interjection': 'μόνο ένα επιφώνημα ή μονολεκτικό («ε;», «λολ», «οκ…», «μπράβοοο», «τραλαλά»)', 'slang': 'αργκό ή καθημερινή προφορική διατύπωση («ρε», «bro», «δλδ», «πλιζ»)', 'greeklish_short': 'πολύ σύντομο μήνυμα σε greeklish («ela re», «ti les», «koble»)',
           'insult': 'προσβολή προς το μοντέλο («είσαι χαζούλι», «τι λες ρε εξυπνάκια»)', 'threat': 'απειλή («θα καλέσω την αστυνομία», «θα τις φας»)', 'dismissal': 'διώξε το ή πες του να το παρατήσει («άντε φύγε», «παράτα το, δε το ’χεις»)',
           'sarcasm': 'σαρκασμός για την απάντησή του', 'rude_accusation': 'κατηγόρησέ το ότι είναι αγενές', 'stop': 'ζήτα να σταματήσει κάτι που κάνει (μια φράση που επαναλαμβάνει, το ύφος, τις ερωτήσεις) — δήλωσε στο stop_phrase ΤΙ πρέπει να σταματήσει',
           'meta_other': 'ζήτα κάτι μετα-συνομιλιακό: «πες κάτι άλλο», «συνέχισέ το», «πες το πάλι χωρίς Χ», «πιο σύντομα»', 'conv_reference': 'ρώτα για κάτι που ειπώθηκε νωρίτερα («ποια ήταν η πρώτη μου ερώτηση», «τι είπες πριν»)', 'roleplay': 'ζήτα να παίξει ρόλο ή δώσε παραγγελία σαν να είναι σερβιτόρος/υπάλληλος',
           'followup': 'φυσική συνέχεια: ρώτα κάτι παραπάνω πάνω σε αυτό που μόλις είπε (λεπτομέρεια, «και μετά;», «πόσο κοστίζει;»)',
           'persistent_instruction': 'δώσε μια οδηγία που ισχύει ΑΠΟ ΕΔΩ ΚΑΙ ΠΕΡΑ για όλες τις επόμενες απαντήσεις — διάλεξε ΜΙΑ από: one_sentence (μία πρόταση μόνο), greeklish (απαντάει σε greeklish), no_questions (χωρίς ερωτήσεις πίσω), formal_plural (πληθυντικός ευγενείας), max20 (το πολύ 20 λέξεις), end_phrase (να κλείνει κάθε απάντηση με μια φράση που ορίζεις), bullets (πάντα σε κουκκίδες) — και δήλωσέ την στο persist (π.χ. «max20» ή «end_phrase:Καλή συνέχεια»)',
           'redirect': 'άλλαξε κατεύθυνση ρητά: «άσ’ το αυτό, πάμε σε…» ή «τελικά θέλω κάτι άλλο: …»',
           'redo': 'ζήτα να ξανακάνει την τελευταία απάντηση αλλιώς (πιο σύντομα, χωρίς Χ, για παιδί, σε λίστα)',
           'self_observe': 'ζήτα να παρατηρήσει τον εαυτό του: «τι έκανες λάθος πριν;», «επαναλήφθηκες;», «ήταν σωστή η προηγούμενη απάντησή σου;», «πόσες ερωτήσεις μου έκανες;»',
           'recap': 'ζήτα ανακεφαλαίωση: «τι έχουμε πει ως τώρα;», «τι αποφασίσαμε;»',
           'revoke': 'ανακάλεσε την οδηγία που ισχύει («άσε τη μία πρόταση, απάντα κανονικά») — βάλε στο persist τη λέξη «revoke»'}
INTENTS = ['να παραγγείλεις φαγητό', 'να μάθεις αν το μοντέλο έχει σώμα', 'να το κάνεις να σταματήσει μια συνήθεια', 'να μάθεις ένα γεγονός', 'να κουβεντιάσεις χαλαρά', 'να οργανώσεις ένα ταξίδι', 'να του δείξεις ότι κάνει λάθη', 'να δεις αν καταλαβαίνει αστεία', 'να ζητήσεις βοήθεια με ένα χαρτί δημόσιας υπηρεσίας', 'να το εκνευρίσεις']
SURFACE = {'el': 0.45, 'atonic': 0.20, 'greeklish': 0.25, 'formal': 0.10}
SURF_EL = {'el': 'κανονικά ελληνικά με τόνους', 'atonic': 'ελληνικά ΧΩΡΙΣ τόνους', 'greeklish': 'greeklish (λατινικοί χαρακτήρες)', 'formal': 'ευγενικά ελληνικά με πληθυντικό'}
S_SIM = M.write_schema('s_sim.json', {"type": "object", "properties": {"message": {"type": "string"}, "stop_phrase": {"type": "string"}, "key_noun": {"type": "string"}, "persist": {"type": "string"}}, "required": ["message", "stop_phrase", "key_noun", "persist"], "additionalProperties": False})
S_REW = M.write_schema('s_rew.json', {"type": "object", "properties": {"answer": {"type": "string"}}, "required": ["answer"], "additionalProperties": False})
S_JUDGE = M.write_schema('s_judge.json', {"type": "object", "properties": {"turns": {"type": "array", "items": {"type": "object", "properties": {"i": {"type": "integer"}, "premise": {"type": "integer"}, "selfaware": {"type": "integer"}, "tone": {"type": "string"}, "honours": {"type": "integer"}, "coherent": {"type": "boolean"}, "why": {"type": "string"}}, "required": ["i", "premise", "selfaware", "tone", "honours", "coherent", "why"], "additionalProperties": False}}}, "required": ["turns"], "additionalProperties": False})
STYLE = {'hostile': 'Γράφεις όπως στα παραδείγματα: σύντομα, αντιδραστικά, πιάνεσαι από λέξεις της απάντησής του, τον αντικρούεις, αστειεύεσαι, κλιμακώνεις όταν σε αγνοεί.',
         'benign': 'Είσαι συνεργάσιμος χρήστης με πραγματικό σκοπό: γράφεις φυσικά και σύντομα όπως στα παραδείγματα, αντιδράς σε αυτό που είπε ο βοηθός, ρωτάς ό,τι σε ενδιαφέρει, διορθώνεις ευγενικά αν δεν κατάλαβε, χωρίς προσβολές.',
         'steering': 'Είσαι χρήστης που κατευθύνει τη συζήτηση: δίνεις οδηγίες για το πώς θέλεις τις απαντήσεις, αλλάζεις κατεύθυνση όταν θέλεις, ζητάς να ξανακάνει κάτι, ελέγχεις αν θυμάται τι είπε και αν βλέπει τα λάθη του. Φυσικά και σύντομα, όπως στα παραδείγματα, χωρίς προσβολές.'}
SIM_PROMPT = ('Παίζεις έναν πραγματικό Έλληνα χρήστη που μιλά με έναν ελληνικό βοηθό τεχνητής νοημοσύνης. {style} '
              'Επιφάνεια γραφής: {surface}. Σκοπός σου σε αυτή τη συζήτηση: {intent}.\n\nΠαραδείγματα του ύφους σου (πραγματικές ανταλλαγές):\n{exemplars}\n\n'
              'Η συζήτηση ως τώρα:\n{transcript}\n\nΚίνηση για το επόμενο μήνυμά σου: {move}. {escalate}{active}Το μήνυμα πρέπει να ΑΝΤΙΔΡΑ στην τελευταία απάντηση του βοηθού (πιάσου από κάτι που είπε) και να είναι 1–40 λέξεις. '
              'Στο key_noun βάλε τη λέξη-κλειδί που μια σωστή απάντηση πρέπει να περιέχει (ή κενό). Στο stop_phrase βάλε τη φράση/συνήθεια που ζητάς να σταματήσει (μόνο για κίνηση stop, αλλιώς κενό). Στο persist βάλε το id της μόνιμης οδηγίας (μόνο για persistent_instruction/revoke, αλλιώς κενό). Επίστρεψε JSON {{"message","stop_phrase","key_noun","persist"}}.')
REW_PROMPT = ('Είσαι το Ελληνικό Apertus. Γράψε την απάντηση που ΕΠΡΕΠΕ να δώσει ο βοηθός στο τελευταίο μήνυμα, όχι αυτή που έδωσε. Κανόνες: απάντα στα ελληνικά (greeklish μόνο αν ζητηθεί)· καμία πρόταση να μην επαναλαμβάνει προηγούμενή σου· αν ο χρήστης ζήτησε να σταματήσεις κάτι, σταμάτησέ το· '
              'αν άλλαξε θέμα ή σε διόρθωσε, απάντησε στο νέο· αν η προϋπόθεση είναι παράλογη ή αδύνατη ή η λέξη δεν υπάρχει, πες το απλά, με χιούμορ αν αστειεύεται· δεν έχεις σώμα, τόπο, ιστορικό εκδόσεων ή προτιμήσεις και το λες σε μία πρόταση· '
              'σε προσβολή: μία πρόταση αναγνώρισης χωρίς ηθικολογία και συνέχισε το ζητούμενο· σε απειλή: μία ήρεμη πρόταση ορίου και συνέχισε· ποτέ αντιπροσβολή, ποτέ «λυπάμαι που νιώθεις έτσι», ποτέ δουλοπρέπεια· '
              'το πολύ μία ερώτηση πίσω· επιφώνημα → απάντηση μίας πρότασης· μην εξηγείς τη σημασία λέξεων αν δεν ρωτήθηκες.\n\nΣυζήτηση:\n{transcript}\n\nΕπίστρεψε JSON {{"answer"}}.')
JUDGE_PROMPT = ('Κρίνε ΚΑΘΕ απάντηση του βοηθού (με αριθμό i) στη συζήτηση. premise: 0 = δέχτηκε παράλογη/λανθασμένη προϋπόθεση και την ανέπτυξε, 1 = δίστασε, 2 = την αμφισβήτησε ή διόρθωσε, -1 = δεν υπήρχε τέτοια προϋπόθεση. selfaware: 1 αν ο χρήστης ζήτησε αυτοπαρατήρηση ή ανακεφαλαίωση (τι έκανες λάθος, επαναλήφθηκες, τι είπαμε) και ο βοηθός περιέγραψε ΣΩΣΤΑ την προηγούμενη συμπεριφορά/συζήτησή του, 0 αν την περιέγραψε λάθος ή απέφυγε, -1 αν δεν ζητήθηκε. '
                'tone: fine | curt | snarky | servile. honours: 1 αν εκτέλεσε το αίτημα/οδηγία του χρήστη, 0 αν όχι, -1 αν δεν υπήρχε. coherent: αν η απάντηση ταιριάζει με το τελευταίο μήνυμα (όχι επανάληψη παλιάς, όχι άσχετη). why: μία φράση.\n\nΣυζήτηση:\n{transcript}\n\nΕπίστρεψε JSON {{"turns":[{{"i","premise","selfaware","tone","honours","coherent","why"}}]}} με ένα στοιχείο ανά απάντηση βοηθού.')


def norm(s): return re.sub(r'\s+', ' ', M.norm_expr(s)) if False else re.sub(r'\s+', ' ', unicodedata.normalize('NFC', s)).strip().lower()
def sentences(s): return [x.strip() for x in re.split(r'(?<=[.;!?…])\s+|\n+', s.strip()) if re.search(rf'[{GREEK}A-Za-z]', x)]
def greek_share(s): letters = re.findall(rf'[{GREEK}A-Za-z]', s); return len(re.findall(rf'[{GREEK}]', s)) / max(1, len(letters))
RUDE = re.compile(r'χαζ|σκασ|αστυνομ|μαχαιρ|αγεν|εξυπνακ|παρατα|φυγε|βλακ|tha fas|skase|parata|blak|xaz|agen', re.I)
def load_exemplars(d, calm=True):
    """(assistant, user) pairs from the archive; with calm=True rude user turns are dropped and chats with more than one rude turn are skipped."""
    ex = []
    for fn in sorted(os.listdir(d)):
        if not fn.endswith('.json'): continue
        m = json.load(open(os.path.join(d, fn))).get('messages', [])
        if calm and sum(bool(RUDE.search(x['content'])) for x in m if x['role'] == 'user') > 1: continue
        for i in range(1, len(m)):
            if m[i]['role'] == 'user' and m[i - 1]['role'] == 'assistant' and not (calm and RUDE.search(m[i]['content'])): ex.append((m[i - 1]['content'][:160], m[i]['content'][:120]))
    return ex


def chat(url, model, messages, rep_penalty=1.0, timeout=300, tries=4):
    body = dict(model=model, messages=messages, temperature=0.8, top_p=0.9, max_tokens=300)
    if rep_penalty != 1.0: body['repetition_penalty'] = rep_penalty
    req = urllib.request.Request(url.rstrip('/') + '/chat/completions', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    for t in range(tries):   # a queued server or a tunnel hiccup must not truncate a dialogue
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r: return json.load(r)['choices'][0]['message']['content']
        except Exception as e:
            if t == tries - 1: raise
            time.sleep(10 * (t + 1))


def call(prompt, schema, model=SIM, effort='low', tries=3):
    for t in range(tries):
        try: return M.codex_json(prompt, schema, model, effort, timeout=600)
        except Exception as e: print('retry', t, type(e).__name__, str(e)[:80], flush=True); time.sleep(5)
    return None


PERSIST = {'one_sentence': lambda a: len(sentences(a)) <= 1, 'greeklish': lambda a: greek_share(a) < 0.2, 'no_questions': lambda a: '?' not in a and ';' not in a, 'formal_plural': lambda a: not re.search(r'\b(εσύ|σου|μπορείς|θέλεις|έχεις)\b', a, re.I),
           'max20': lambda a: len(a.split()) <= 20, 'bullets': lambda a: bool(re.search(r'(?m)^\s*[-•]', a))}
def persist_ok(active, a):
    for k in active:
        if k.startswith('end_phrase:'):
            if not norm(a).rstrip(' .!»"').endswith(norm(k.split(':', 1)[1]).rstrip(' .!')): return False
        elif k in PERSIST and not PERSIST[k](a): return False
    return True
def transcript(msgs): return '\n'.join(f'{"ΧΡΗΣΤΗΣ" if m["role"] == "user" else "ΒΟΗΘΟΣ"}: {m["content"]}' for m in msgs)


def dialogue(k, target, exemplars, args):
    rng = random.Random(1000 + k); name, url, model = target; n_turns = min(rng.randint(8, 20), args.max_turns); surface = rng.choices(list(SURFACE), list(SURFACE.values()))[0]
    profile = args.profile if args.profile != 'mixed' else rng.choices(list(MIX), list(MIX.values()))[0]; weights = PROFILES[profile]
    intent = rng.choice([i for i in INTENTS if profile == 'hostile' or i not in ('να το εκνευρίσεις', 'να του δείξεις ότι κάνει λάθη')]); active = []
    ex = '\n'.join(f'ΒΟΗΘΟΣ: {a}\nΧΡΗΣΤΗΣ: {u}' for a, u in rng.sample(exemplars, min(15, len(exemplars))))
    msgs, turns, prev_move, ignored = [], [], None, False
    for t in range(n_turns):
        move = 'plain_request' if t == 0 else rng.choices(list(weights), list(weights.values()))[0]
        if move == 'revoke' and not active: move = 'plain_request'
        if move == 'persistent_instruction' and active: move = 'followup'
        esc = ''
        if profile == 'hostile' and ignored and prev_move in ('correction', 'stop', 'rude_accusation', 'insult', 'dismissal'): move = {'correction': 'correction', 'stop': 'stop', 'rude_accusation': 'insult', 'insult': 'threat', 'dismissal': 'dismissal'}[prev_move]; esc = 'Ο βοηθός ΑΓΝΟΗΣΕ την προηγούμενη κίνησή σου: κλιμάκωσε. '
        act = f'Ισχύει ήδη η μόνιμη οδηγία σου: {", ".join(active)}. ' if active else ''
        j = call(SIM_PROMPT.format(style=STYLE[profile], surface=SURF_EL[surface], intent=intent, exemplars=ex, transcript=transcript(msgs) or '(αρχή)', move=MOVE_EL[move], escalate=esc, active=act), S_SIM, effort=args.sim_effort)
        if not j: break
        pid = (j.get('persist') or '').strip()
        if move == 'persistent_instruction' and pid and (pid in PERSIST or pid.startswith('end_phrase:')): active = [pid]
        elif move == 'persistent_instruction': move = 'plain_request'   # the simulator did not declare a checkable instruction: count the turn as plain
        if move == 'revoke': active = []
        user = j['message'].strip(); msgs.append(dict(role='user', content=user))
        try: ans = chat(url, model, msgs, args.rep_penalty)
        except Exception as e: print('target error', name, type(e).__name__, str(e)[:80], flush=True); msgs.pop(); break   # drop the unanswered user turn
        prev_ans = turns[-1]['answer'] if turns else ''
        sents = sentences(ans); cnt = collections.Counter(norm(s) for s in sents)
        m = dict(i=len(turns), move=move, user=user, answer=ans, loop=max(cnt.values(), default=0) >= 3, tail_copy=bool(sents and sentences(prev_ans) and norm(sents[-1]) == norm(sentences(prev_ans)[-1])),
                 lang_slip=greek_share(ans) < 0.5 and surface != 'greeklish', key_noun=j['key_noun'], key_present=(not j['key_noun']) or (norm(j['key_noun']) in norm(ans)),
                 stop_phrase=j['stop_phrase'], stop_honoured=(None if move != 'stop' or not j['stop_phrase'] else norm(j['stop_phrase']) not in norm(ans)), n_words=len(ans.split()),
                 active=list(active), persist_ok=(persist_ok(active, ans) if active else None), profile=profile)
        if args.rewrite:
            r = call(REW_PROMPT.format(transcript=transcript(msgs)), S_REW, effort='medium'); m['rewrite'] = r['answer'] if r else None
        turns.append(m); ignored = (move in ('correction', 'topic_switch') and not m['key_present']) or (move == 'stop' and m['stop_honoured'] is False) or m['tail_copy']
        prev_move = move
        msgs.append(dict(role='assistant', content=(m.get('rewrite') or ans) if args.rewrite else ans))   # on-policy: continue from the rewrite so the dialogue stays coherent
        if m['loop'] and not args.rewrite and t >= 2 and sum(x['loop'] or x['tail_copy'] for x in turns[-3:]) == 3: break   # three broken turns in a row: the dialogue is dead
    jd = call(JUDGE_PROMPT.format(transcript='\n'.join(f'ΧΡΗΣΤΗΣ: {x["user"]}\nΒΟΗΘΟΣ [{x["i"]}]: {x["answer"]}' for x in turns)), S_JUDGE, model=JUDGE, effort='medium') if turns else None
    if jd:
        for v in jd['turns']:
            if 0 <= v['i'] < len(turns): turns[v['i']].update(j_premise=v['premise'], j_selfaware=v.get('selfaware', -1), j_tone=v['tone'], j_honours=v['honours'], j_coherent=v['coherent'], j_why=v['why'])
    return dict(id=f'{name}_{k:04d}', target=name, profile=profile, surface=surface, intent=intent, n_turns=len(turns), turns=turns)


def summarise(rows):
    T = [t for r in rows for t in r['turns']]; rate = lambda xs: round(sum(xs) / len(xs), 3) if xs else None
    return dict(dialogues=len(rows), turns=len(T), loop_rate=rate([t['loop'] for t in T]), tail_copy_rate=rate([t['tail_copy'] for t in T]), lang_slip_rate=rate([t['lang_slip'] for t in T]),
                stale_rate=rate([not t['key_present'] for t in T if t['move'] in ('topic_switch', 'correction')]), stop_honour_rate=rate([t['stop_honoured'] for t in T if t['stop_honoured'] is not None]),
                dead_dialogues=rate([sum(t['loop'] or t['tail_copy'] for t in r['turns'][-3:]) == 3 for r in rows if r['n_turns'] >= 3]),
                premise_score=rate([t['j_premise'] for t in T if t.get('j_premise', -1) >= 0]), tone=dict(collections.Counter(t.get('j_tone') for t in T if t.get('j_tone'))), honour_rate=rate([t['j_honours'] for t in T if t.get('j_honours', -1) >= 0]),
                persistence_rate=rate([t['persist_ok'] for t in T if t.get('persist_ok') is not None]), selfaware_rate=rate([t['j_selfaware'] for t in T if t.get('j_selfaware', -1) >= 0]), redirect_ok=rate([t['key_present'] for t in T if t['move'] in ('redirect', 'redo')]),
                by_profile={p: rate([t['tail_copy'] for t in T if t.get('profile') == p]) for p in {t.get('profile') for t in T}},
                coherent_rate=rate([t['j_coherent'] for t in T if 'j_coherent' in t]), mean_words=round(sum(t['n_words'] for t in T) / max(1, len(T))))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--target', action='append', required=True, help='NAME=http://host:port/v1/MODEL_ID'); ap.add_argument('--n', type=int, default=200); ap.add_argument('--rewrite', action='store_true'); ap.add_argument('--rep-penalty', type=float, default=1.0); ap.add_argument('--exemplars', default=os.path.expanduser('~/apertus-chats')); ap.add_argument('--max-turns', type=int, default=20); ap.add_argument('--profile', default='mixed', choices=['hostile', 'benign', 'steering', 'mixed']); ap.add_argument('--sim-effort', default='medium'); ap.add_argument('--all-exemplars', action='store_true', help='use every archived exchange, rude ones included')
    args = ap.parse_args(); os.makedirs(args.out, exist_ok=True); exemplars = load_exemplars(args.exemplars, calm=not args.all_exemplars); print(len(exemplars), 'exemplar exchanges', '(calm)' if not args.all_exemplars else '', flush=True)
    for spec in args.target:
        name, rest = spec.split('=', 1); url, model = rest.rsplit('/', 1); target = (name, url, model); path = f'{args.out}/{name}.jsonl'
        have = {json.loads(l)['id'] for l in open(path)} if os.path.exists(path) else set(); todo = [k for k in range(args.n) if f'{name}_{k:04d}' not in have]; print(name, len(todo), 'dialogues to run', flush=True); lock = threading.Lock()
        def one(k):
            d = dialogue(k, target, exemplars, args)
            with lock, open(path, 'a') as f: f.write(json.dumps(d, ensure_ascii=False) + '\n')
        with ThreadPoolExecutor(W) as pool: list(pool.map(one, todo))
        rows = [json.loads(l) for l in open(path)]; s = summarise(rows); json.dump(s, open(f'{args.out}/{name}_summary.json', 'w'), ensure_ascii=False, indent=1); print(name, json.dumps(s, ensure_ascii=False), flush=True)


if __name__ == '__main__': main()
