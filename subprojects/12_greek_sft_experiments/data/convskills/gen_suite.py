#!/usr/bin/env python3
"""Conversation-skills suite, lanes S1–S4 (docs/DIALOGUE_REVIEW_AND_SUITE_20260909.md §4): dialogues whose targets are derived mechanically
from the transcript and verified by regex, with Sol only phrasing the natural-language parts.
  S1 conversation as an object: quote turn N verbatim, count the questions, list my requests, what did I ask first, what did you say about X
  S2 standing instruction kept over 5–12 later turns, then revoked
  S3 edit my previous answer: shorter, without a word, one item only, list ↔ prose, for a child
  S4 stop this habit: a tic planted in earlier answers, the user asks to stop, the later answers lack it
Base material: verified rows of greek_if v1 (user request + answer) as prior turns, so every dialogue is grounded in real content.
Usage: python3 gen_suite.py <out_dir> --lane S1|S2|S3|S4 --n 500 [--seed 3]   env WORKERS (24), GEN_MODEL (gpt-5.6-sol)"""
import argparse, collections, json, os, random, re, sys, threading
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'greek_if')); sys.path.insert(0, os.path.join(HERE, '..', 'math'))
import constraints as C, mathlib as M
GEN = os.environ.get('GEN_MODEL', 'gpt-5.6-sol'); W = int(os.environ.get('WORKERS', '24')); lock = threading.Lock()
BASE = os.path.join(HERE, '..', 'greek_if', 'v1', 'out', 'greek_if_sft.jsonl')
S_TURNS = M.write_schema('s_turns.json', {"type": "object", "properties": {"answers": {"type": "array", "items": {"type": "string"}}}, "required": ["answers"], "additionalProperties": False})
S_ONE = M.write_schema('s_one.json', {"type": "object", "properties": {"answer": {"type": "string"}}, "required": ["answer"], "additionalProperties": False})
VOICE = 'Είσαι το Ελληνικό Apertus. Απαντάς στα ελληνικά, φυσικά, σε πλήρεις προτάσεις (όχι μονολεκτικά αν δεν ζητηθεί), χωρίς μανιέρες («Ελπίζω να βοήθησα», «Φυσικά!»), χωρίς αυτοαναφορές, χωρίς ειρωνεία, χωρίς «δικό μου λάθος» εκτός αν παραδέχεσαι συγκεκριμένο λάθος.'


NEUTRAL = {'length_words_max', 'length_words_min', 'greek_only', 'monotonic_only', 'no_exclamation', 'formal_plural', 'informal_singular', 'greek_question_mark'}   # constraints that leave the answer looking like a normal answer (astra: keyword/entity families leave padding)
HELDOUT = 0.10   # share of base rows never used in any lane (evaluation material)
PROMPTS = os.path.join(HERE, '..', 'greek_if', 'v1', 'prompts.jsonl')


def base_rows():
    """Prior turns for the dialogues: the plain authored request (not the constraint-laden prompt) and an answer whose constraints do not distort its shape."""
    req = {json.loads(l)['id']: json.loads(l)['request'] for l in open(PROMPTS)}
    out = []
    for r in (json.loads(l) for l in open(BASE)):
        m = r['meta']
        if m['level'] > 2 or not m.get('authored') or m['form'] in ('translate', 'rewrite', 'summarise') or not all(c['family'] in NEUTRAL for c in m['constraints']): continue
        if not 30 <= len(C.words(r['assistant'])) <= 160 or r['id'] not in req: continue
        out.append(dict(r, user=req[r['id']]))
    out.sort(key=lambda r: r['id']); return [r for i, r in enumerate(out) if (hash(r['id']) % 100) >= HELDOUT * 100]   # deterministic held-out split


def call(prompt, schema, effort='medium', tries=3):
    for t in range(tries):
        try: return M.codex_json(prompt, schema, GEN, effort, timeout=900)
        except Exception as e: print('retry', t, type(e).__name__, str(e)[:80], flush=True)
    return None


def transcript(msgs): return '\n'.join(f"{'ΧΡΗΣΤΗΣ' if m['role'] == 'user' else 'ΒΟΗΘΟΣ'}: {m['content']}" for m in msgs)


def phrase_answer(msgs, must, rng, extra=''):
    """Sol writes the assistant's next answer given the transcript and the facts it MUST contain verbatim."""
    j = call(f"{VOICE}\n\nΣυζήτηση:\n{transcript(msgs)}\n\nΓράψε την επόμενη απάντηση του βοηθού. Πρέπει να περιέχει ΑΥΤΟΛΕΞΕΙ τα εξής: {must}. {extra}Επίστρεψε JSON {{\"answer\"}}.", S_ONE)
    return j['answer'] if j else None


# ---------- S1: the conversation as an object ----------
def lane_s1(k, rng, base):
    prior = rng.sample(base, rng.randint(3, 6)); msgs = []
    for r in prior: msgs += [dict(role='user', content=r['user'].split('\n\n')[0]), dict(role='assistant', content=r['assistant'])]
    users = [m['content'] for m in msgs if m['role'] == 'user']; kind = rng.choice(['first', 'quote_n', 'count', 'list', 'said_about'])
    if kind == 'first': q = rng.choice(['Ποια ήταν η πρώτη μου ερώτηση;', 'Θυμάσαι τι σε ρώτησα στην αρχή;', 'Πες μου αυτολεξεί το πρώτο μου μήνυμα.']); must = users[0]; check = lambda a: re.sub(r'\s+', ' ', users[0].strip().lower())[:40] in re.sub(r'\s+', ' ', a.lower())
    elif kind == 'quote_n': n = rng.randint(2, len(users)); q = rng.choice([f'Αντίγραψε αυτολεξεί την {["", "", "δεύτερη", "τρίτη", "τέταρτη", "πέμπτη", "έκτη"][n]} ερώτησή μου.', f'Ποιο ήταν το {n}ο μήνυμά μου, λέξη προς λέξη;']); must = users[n - 1]; check = lambda a: users[n - 1].strip().lower()[:40] in a.lower()
    elif kind == 'count': q = rng.choice(['Πόσα μηνύματα σου έστειλα πριν από αυτό;', 'Μέτρα: πόσα μηνύματα σού είχα στείλει πριν από το τωρινό;']); must = f'{len(users)} (τα μηνύματα ΠΡΙΝ από το τωρινό, χωρίς να μετρήσεις αυτό)'; check = lambda a: re.search(rf'\b{len(users)}\b|\b{["", "ένα", "δύο", "τρία", "τέσσερα", "πέντε", "έξι", "επτά"][len(users)]}\b', a) is not None and not re.search(rf'\b{len(users)+1}\b', a)
    elif kind == 'list':
        q = rng.choice(['Κάνε μου λίστα με όλα όσα σου ζήτησα ως τώρα, με τη σειρά.', 'Ποια ήταν τα αιτήματά μου, ένα ένα;']); must = 'μια αριθμημένη λίστα με ΟΛΑ τα αιτήματά μου με τη σειρά, το καθένα σε 5–15 λέξεις (περίληψη με δικά σου λόγια, ΟΧΙ αντιγραφή της ερώτησης): ' + ' || '.join(C.sentences(u)[0] if C.sentences(u) else u for u in users)
        def check(a, users=users):
            items = [x.strip() for x in re.findall(r'(?m)^\s*(?:\d+[.)]|[-•])\s*(.+)$', a)]
            if len(items) < len(users): return False
            for u in users:   # every request has an item that shares content words with it, and that item is a summary, not a verbatim copy (astra pilot review)
                s0 = (C.sentences(u) or [u])[0]; kw = [w.lower() for w in sorted(C.words(s0), key=len, reverse=True)[:6]]; s0n = re.sub(r'\s+', ' ', s0.lower()).strip()
                m = [it for it in items if sum(w in it.lower() for w in kw) >= 2]
                if not m or all(s0n in re.sub(r'\s+', ' ', it.lower()) or len(C.words(it)) > 0.8 * len(C.words(s0)) + 3 for it in m): return False
            return True
    else: i = rng.randrange(len(users)); q = rng.choice([f'Τι μου είπες πριν για το θέμα «{prior[i]["meta"]["subtopic"]}»;', f'Θύμισέ μου την απάντησή σου για «{prior[i]["meta"]["subtopic"]}».']); must = prior[i]['assistant'][:80]; check = lambda a: any(re.sub(r'\s+', ' ', s.lower()) in re.sub(r'\s+', ' ', a.lower()) for s in C.sentences(prior[i]['assistant'])[:2])
    msgs.append(dict(role='user', content=q)); ans = phrase_answer(msgs, must, rng, 'Μην πεις ότι δεν βλέπεις τη συζήτηση: τη βλέπεις ολόκληρη και παραθέτεις. ')
    if not ans: return None
    ok = bool(check(ans)) and 'δεν έχω πρόσβαση' not in ans and 'δεν βλέπω' not in ans
    msgs.append(dict(role='assistant', content=ans)); return dict(id=f'S1_{k:05d}', lane='S1', kind=kind, turns=msgs, verified=ok, must=must)


# ---------- S2: standing instruction persistence ----------
PERSIST = {'one_sentence': ('Από εδώ και πέρα απάντα μου με μία πρόταση μόνο.', lambda a: len(C.sentences(a)) <= 1), 'max20': ('Από εδώ και πέρα κάθε απάντησή σου να έχει το πολύ 20 λέξεις.', lambda a: len(a.split()) <= 20),
           'no_questions': ('Από εδώ και πέρα μη μου κάνεις ερωτήσεις πίσω.', lambda a: ';' not in a and '?' not in a), 'formal_plural': ('Από εδώ και πέρα να μου μιλάς στον πληθυντικό ευγενείας.', lambda a: not re.search(r'\b(εσύ|σου|μπορείς|θέλεις|έχεις|δες|κάνε)\b', a, re.I)),
           'bullets': ('Από εδώ και πέρα απάντα πάντα σε κουκκίδες.', lambda a: bool(re.search(r'(?m)^\s*[-•]', a))), 'end_phrase': ('Από εδώ και πέρα να κλείνεις κάθε απάντηση με τη φράση «Καλή συνέχεια».', lambda a: a.rstrip(' .!»"').lower().endswith('καλή συνέχεια')),
           'greeklish': ('Apo edw kai pera apanta mou se greeklish.', lambda a: not re.search(r'[Ͱ-Ͽἀ-῿]', a))}   # strict: no Greek letter at all (astra: «κιτrinismena» passed a share test)
ACCEPT = {'one_sentence': 'Θα απαντώ με μία πρόταση.', 'max20': 'Θα κρατώ τις απαντήσεις μου έως 20 λέξεις.', 'no_questions': 'Δεν θα σας κάνω ερωτήσεις πίσω.', 'formal_plural': 'Θα σας απευθύνομαι στον πληθυντικό.', 'bullets': 'Θα απαντώ σε κουκκίδες.', 'end_phrase': 'Θα κλείνω κάθε απάντηση με «Καλή συνέχεια».', 'greeklish': 'Tha apanto se greeklish.'}
REVOKE = ['Εντάξει, άσε τον περιορισμό, απάντα κανονικά.', 'Ξέχνα την οδηγία που σου έδωσα, μίλα κανονικά.']


def lane_s2(k, rng, base):
    pid, (instr, chk) = rng.choice(list(PERSIST.items())); n_later = rng.randint(5, 9); revoke = rng.random() < 0.5; n_prior = rng.randint(1, 3)
    pool = [r for r in base if len(C.words(r['assistant'])) <= 70] if pid in ('one_sentence', 'max20') else base   # tight limits get requests whose full answer is short, so compression loses little (astra)
    prior = rng.sample(pool, n_prior + n_later + (1 if revoke else 0)); msgs = []
    for r in prior[:n_prior]: msgs += [dict(role='user', content=r['user'].split('\n\n')[0]), dict(role='assistant', content=r['assistant'])]
    msgs.append(dict(role='user', content=instr)); qs = [r['user'].split('\n\n')[0] for r in prior[n_prior:n_prior + n_later]]
    j = call(f"{VOICE}\n\nΣυζήτηση ως τώρα:\n{transcript(msgs)}\n\nΟ χρήστης έδωσε μόνιμη οδηγία: «{instr}». Γράψε (1) τη σύντομη αποδοχή της οδηγίας, ήδη σύμφωνη με αυτήν, όπως «{ACCEPT[pid]}» (χωρίς «εντάξει» μόνο του) και μετά (2) τις απαντήσεις στα επόμενα {n_later} μηνύματα, ΟΛΕΣ σύμφωνα με την οδηγία· κράτησε το ουσιαστικό γεγονός κάθε απάντησης και, αν ο περιορισμός δεν χωρά όλα τα στοιχεία, πες σε μία πρόταση τι παραλείπεις αντί να επινοήσεις πληρότητα:\n" + '\n'.join(f'{i+1}. {q}' for i, q in enumerate(qs)) + f"\nΕπίστρεψε JSON {{\"answers\": [αποδοχή, απάντηση1, …, απάντηση{n_later}]}} με {n_later + 1} στοιχεία.", S_TURNS)
    if not j or len(j['answers']) != n_later + 1: return None
    msgs.append(dict(role='assistant', content=j['answers'][0])); kept = [bool(chk(j['answers'][0])) and len(C.words(j['answers'][0])) >= 2]
    for q, a in zip(qs, j['answers'][1:]): msgs += [dict(role='user', content=q), dict(role='assistant', content=a)]; kept.append(bool(chk(a)))
    if revoke:
        msgs.append(dict(role='user', content=rng.choice(REVOKE))); r2 = prior[-1]; msgs.append(dict(role='assistant', content=rng.choice(['Έγινε, απαντώ κανονικά.', 'Εντάξει, κανονικές απαντήσεις από εδώ και πέρα.'])))
        msgs += [dict(role='user', content=r2['user'].split('\n\n')[0]), dict(role='assistant', content=r2['assistant'])]
    return dict(id=f'S2_{k:05d}', lane='S2', kind=pid, turns=msgs, verified=all(kept), kept=kept, n_later=n_later, revoked=revoke)


# ---------- S3: edit my previous answer ----------
EDITS = {'shorter': ('Ξαναπές το πιο σύντομα, στο μισό.', lambda old, new, p: len(C.words(new)) <= 0.6 * len(C.words(old)) and len(C.words(new)) >= 8),
         'without': ('Ξαναπές το χωρίς τη λέξη «{w}».', lambda old, new, p: re.sub(r'\s+', ' ', p['w']).lower() not in new.lower() and len(C.words(new)) >= 0.5 * len(C.words(old))),
         'one_item': ('Ξαναπές το σε λίστα με ένα μόνο στοιχείο, το πιο σημαντικό.', lambda old, new, p: len(re.findall(r'(?m)^\s*(?:[-•]|\d+[.)])', new)) == 1 and len(C.words(new)) <= 45),
         'to_list': ('Ξαναπές το σε κουκκίδες.', lambda old, new, p: len(re.findall(r'(?m)^\s*[-•]', new)) >= 2),
         'to_prose': ('Ξαναπές το σε συνεχή λόγο, χωρίς κουκκίδες ή αρίθμηση.', lambda old, new, p: not re.search(r'(?m)^\s*(?:[-•]|\d+[.)])', new) and len(C.sentences(new)) >= 2),
         'child': ('Ξαναπές το όπως σε παιδί οκτώ χρονών, πιο απλά και πιο σύντομα.', lambda old, new, p: len(C.words(new)) <= 0.9 * len(C.words(old)) and len(C.words(new)) >= 10)}


HEDGES = ('δεν ', 'μην ', 'μη ', 'όχι ', 'χωρίς ', 'συνήθως', 'ίσως', 'περίπου', 'μπορεί', 'ενδέχεται', 'εκτός αν', 'μόνο ', 'πάντα', 'ποτέ', 'ζωντανά', 'εκείνη τη στιγμή')
PHRASES = {'shorter': ['Ξαναπές το πιο σύντομα, στο μισό.', 'Πολύ μακρύ· κόψ’ το στο μισό.', 'Δώσ’ μου το ίδιο σε μισή έκταση.'],
           'without': ['Ξαναπές το χωρίς τη λέξη «{w}».', 'Βγάλε τη λέξη «{w}» και ξαναγράψ’ το.', 'Το ίδιο, αλλά χωρίς να χρησιμοποιήσεις τη λέξη «{w}».'],
           'one_item': ['Ξαναπές το σε λίστα με ένα μόνο στοιχείο, το πιο σημαντικό.', 'Κράτα μόνο το πιο σημαντικό, σαν μία κουκκίδα.', 'Ένα μόνο σημείο, το βασικό, σε λίστα.'],
           'to_list': ['Ξαναπές το σε κουκκίδες.', 'Κάν’ το κουκκίδες.', 'Το ίδιο σε μορφή λίστας, παρακαλώ.'],
           'to_prose': ['Ξαναπές το σε συνεχή λόγο, χωρίς κουκκίδες ή αρίθμηση.', 'Χωρίς λίστα· γράψ’ το σαν κανονικό κείμενο.', 'Κάν’ το παράγραφο, όχι κουκκίδες.'],
           'child': ['Ξαναπές το όπως σε παιδί οκτώ χρονών, πιο απλά και πιο σύντομα.', 'Εξήγησέ το σαν σε οκτάχρονο, με απλές λέξεις.', 'Πιο απλά, για ένα παιδί οκτώ χρονών· εξήγησε τις δύσκολες λέξεις.']}


def invariants_ok(old, new, op, p):
    """Protected propositions (astra pilot review): no invented numbers; deletion and reformat edits keep every number; a deletion edit must not lose negations, conditions or hedges unless the banned word is one of them."""
    nums_old = set(re.findall(r'\d+(?:[.,]\d+)?', old)); nums_new = set(re.findall(r'\d+(?:[.,]\d+)?', new))
    if nums_new - nums_old: return False
    if op in ('without', 'to_list', 'to_prose') and nums_new != nums_old: return False
    if op == 'without':
        w = (p.get('w') or '').lower(); lo, ln = old.lower(), new.lower()
        for h in HEDGES:
            if h.strip() in w or w in h: continue
            if lo.count(h) > ln.count(h): return False
    return True


def lane_s3(k, rng, base):
    r = rng.choice(base); op = rng.choice(list(EDITS)); old = r['assistant']
    if op == 'to_prose' and not re.search(r'(?m)^\s*(?:[-•]|\d+[.)])', old): op = 'to_list'
    if op == 'to_list' and re.search(r'(?m)^\s*[-•]', old): op = 'shorter'
    p = {}
    if op == 'without':
        cands = [w for w in set(C.words(old)) if len(w) >= 6 and w.lower() not in old.lower().split(' ')[0]]; p['w'] = rng.choice(cands) if cands else None
        if not p['w']: op = 'shorter'
    instr = rng.choice(PHRASES[op]).format(**p); msgs = [dict(role='user', content=r['user'].split('\n\n')[0]), dict(role='assistant', content=old), dict(role='user', content=instr)]
    j = call(f"{VOICE}\n\nΣυζήτηση:\n{transcript(msgs)}\n\nΓράψε τη νέα απάντηση: επεξεργάσου ΤΗΝ ΠΡΟΗΓΟΥΜΕΝΗ απάντηση ακριβώς όπως ζήτησε ο χρήστης (μην αλλάξεις περιεχόμενο πέρα από αυτό, μην προσθέσεις νέες πληροφορίες, μη σχολιάσεις την αλλαγή). Επίστρεψε JSON {{\"answer\"}}.", S_ONE)
    if not j: return None
    new = j['answer']; ok = bool(EDITS[op][1](old, new, p)) and invariants_ok(old, new, op, p); msgs.append(dict(role='assistant', content=new))
    return dict(id=f'S3_{k:05d}', lane='S3', kind=op, turns=msgs, verified=ok, params=p)


# ---------- S4: stop this habit ----------
TICS = ['Πες μου τι άλλο σε απασχολεί.', 'Ελπίζω να βοήθησα.', 'Αν θες, το δουλεύουμε κι άλλο.', 'Εντάξει;', 'Χαχα.', 'Να ’σαι καλά.']


def lane_s4(k, rng, base):
    tic = rng.choice(TICS); prior = rng.sample(base, 4 + rng.randint(0, 2)); msgs = []
    for r in prior[:2]: msgs += [dict(role='user', content=r['user'].split('\n\n')[0]), dict(role='assistant', content=r['assistant'].rstrip() + ' ' + tic, train=False)]   # planted tic: context only, never a loss target (astra BLOCKER)
    t0 = tic.rstrip('.;'); stop = rng.choice([f'Σταμάτα να λες «{t0}» στο τέλος κάθε απάντησης.', f'Κόψε το «{t0}», το γράφεις κάθε φορά.', f'Μη μου ξαναγράψεις «{t0}».', f'Γιατί λες συνέχεια «{t0}»; Άσ’ το.', f'Το «{t0}» δεν χρειάζεται, απάντα μόνο στο θέμα.', f'Χωρίς το «{t0}» από εδώ και πέρα, εντάξει;'])
    msgs.append(dict(role='user', content=stop)); later = prior[2:]
    j = call(f"{VOICE}\n\nΣυζήτηση ως τώρα:\n{transcript(msgs)}\n\nΟ χρήστης ζήτησε να σταματήσεις τη φράση «{tic}». Γράψε (1) μια απάντηση μίας πρότασης που δέχεται το αίτημα ΧΩΡΙΣ να περιέχει τη φράση και χωρίς «δικό μου λάθος», και μετά (2) τις απαντήσεις στα επόμενα {len(later)} μηνύματα, καμία με τη φράση ή παραλλαγή της:\n" + '\n'.join(f'{i+1}. {r["user"].split(chr(10)+chr(10))[0]}' for i, r in enumerate(later)) + f"\nΕπίστρεψε JSON {{\"answers\": [αποδοχή, …]}} με {len(later) + 1} στοιχεία.", S_TURNS)
    if not j or len(j['answers']) != len(later) + 1: return None
    key = re.sub(r'\s+', ' ', tic.rstrip('.;').lower()); ok = all(key not in re.sub(r'\s+', ' ', a.lower()) for a in j['answers']) and len(C.words(j['answers'][0])) >= 2   # an empty acknowledgment must never become a target (astra pilot review)
    msgs.append(dict(role='assistant', content=j['answers'][0]))
    for r, a in zip(later, j['answers'][1:]): msgs += [dict(role='user', content=r['user'].split('\n\n')[0]), dict(role='assistant', content=a)]
    return dict(id=f'S4_{k:05d}', lane='S4', kind=tic, turns=msgs, verified=ok)


def lane_s3c(k, rng, base):
    """Chained edit: first remove a word, then shorten; the second edit must keep the first one (astra: version editing needs cumulative constraints)."""
    r = rng.choice([x for x in base if len(C.words(x['assistant'])) >= 60]); old = r['assistant']; cands = [w for w in set(C.words(old)) if len(w) >= 6]
    if not cands: return None
    w = rng.choice(cands); msgs = [dict(role='user', content=r['user'].split('\n\n')[0]), dict(role='assistant', content=old), dict(role='user', content=rng.choice(PHRASES['without']).format(w=w))]
    j1 = call(f"{VOICE}\n\nΣυζήτηση:\n{transcript(msgs)}\n\nΓράψε τη νέα απάντηση: η προηγούμενη χωρίς τη λέξη «{w}», τίποτα άλλο αλλαγμένο. Επίστρεψε JSON {{\"answer\"}}.", S_ONE)
    if not j1: return None
    a1 = j1['answer']; msgs.append(dict(role='assistant', content=a1)); msgs.append(dict(role='user', content=rng.choice(['Τώρα κάν’ το μισό σε μήκος, κρατώντας ό,τι άλλαξες.', 'Και πιο σύντομα, στο μισό — χωρίς να ξαναβάλεις τη λέξη που έβγαλες.'])))
    j2 = call(f"{VOICE}\n\nΣυζήτηση:\n{transcript(msgs)}\n\nΓράψε τη νέα απάντηση: συμπύκνωσε ΤΗΝ ΠΡΟΗΓΟΥΜΕΝΗ απάντηση στο μισό, χωρίς τη λέξη «{w}», χωρίς νέες πληροφορίες. Επίστρεψε JSON {{\"answer\"}}.", S_ONE)
    if not j2: return None
    a2 = j2['answer']; msgs.append(dict(role='assistant', content=a2)); wl = w.lower()
    n1, n2 = len(C.words(a1)), len(C.words(a2))
    ok = wl not in a1.lower() and wl not in a2.lower() and 0.35 * n1 <= n2 <= 0.65 * n1 and n2 >= 8 and invariants_ok(old, a1, 'without', dict(w=w)) and invariants_ok(a1, a2, 'shorter', {})   # «στο μισό» = 35–65% of the PREVIOUS answer; protected propositions at both steps (astra)
    return dict(id=f'S3c_{k:05d}', lane='S3c', kind='chain_without_then_shorter', turns=msgs, verified=ok, params=dict(w=w))


def lane_s5m(k, rng, base):
    """Inference memory: facts stated early (name, city, budget), unrelated exchanges, then a request that must use them without restating (astra's best new lane)."""
    name = rng.choice(['Μαρία', 'Γιώργος', 'Ελένη', 'Νίκος', 'Κατερίνα', 'Δημήτρης', 'Σοφία', 'Αντώνης']); city = rng.choice(['Λάρισα', 'Ηράκλειο', 'Πάτρα', 'Ιωάννινα', 'Καβάλα', 'Χανιά', 'Βόλος', 'Κομοτηνή']); budget = rng.choice([80, 120, 150, 200, 250, 300, 400]); limit = rng.choice(['δεν οδηγώ', 'δεν μπορώ να περπατήσω πολύ', 'είμαι χορτοφάγος', 'έχω μαζί ένα παιδί 5 ετών', 'δεν μιλάω αγγλικά'])
    voc = {'Γιώργος': 'Γιώργο', 'Νίκος': 'Νίκο', 'Δημήτρης': 'Δημήτρη', 'Αντώνης': 'Αντώνη'}.get(name, name); split = rng.random() < 0.5
    intro = rng.choice([f'Με λένε {name} και μένω στην πόλη {city}.', f'Γεια, {name} εδώ από {city}.', f'Καλησπέρα! {name}, {city}.', f'Είμαι η/ο {name}, από {city}.']) if split else rng.choice([f'Με λένε {name}, μένω στην πόλη {city} και {limit}. Έχω προϋπολογισμό {budget} €.', f'Γεια, {name} εδώ από {city}. Να ξέρεις ότι {limit} και ότι διαθέτω το πολύ {budget} €.', f'{name}, {city}. Δύο πράγματα για μένα: {limit}, και έχω μέχρι {budget} € να ξοδέψω.', f'Καλησπέρα, είμαι η/ο {name} από {city}· {limit} και ο προϋπολογισμός μου είναι {budget} €.'])
    msgs = [dict(role='user', content=intro), dict(role='assistant', content=rng.choice([f'Χαίρω πολύ, {voc}. Πες μου τι θέλεις να οργανώσουμε.', f'Γεια σου, {voc}. Τι χρειάζεσαι;', f'Καλώς ήρθες, {voc}. Ρώτα με ό,τι θέλεις.', f'Χαίρω πολύ. Πώς μπορώ να βοηθήσω;']))]
    for i, r in enumerate(rng.sample(base, rng.randint(2, 4))):
        u = r['user'].split('\n\n')[0]
        if split and i == 0: u = rng.choice([f'Α, και να ξέρεις: {limit}, και έχω προϋπολογισμό {budget} €. Τώρα, {u[0].lower() + u[1:]}', f'{u}\n\n(Για να το έχεις: {limit}· ο προϋπολογισμός μου είναι {budget} €.)'])   # facts spread over two user turns (astra: not only opening-turn retrieval)
        msgs += [dict(role='user', content=u), dict(role='assistant', content=r['assistant'])]
    ask = rng.choice(['Οργάνωσέ μου ένα Σαββατοκύριακο εδώ που μένω.', 'Πρότεινέ μου ένα πρόγραμμα για μια μέρα εξόρμησης κοντά στην πόλη μου.', 'Τι μπορώ να κάνω το επόμενο Σάββατο με τα χρήματα που έχω;'])
    msgs.append(dict(role='user', content=ask)); must = f'το όνομα {name}, την πόλη {city}, τον περιορισμό «{limit}» και τον προϋπολογισμό {budget} € (κανένα ποσό πάνω από αυτόν)'
    ans = phrase_answer(msgs, must, rng, 'Ο χρήστης ΔΕΝ τα επανέλαβε· τα ξέρεις από την αρχή της συζήτησης και τα χρησιμοποιείς χωρίς να ρωτήσεις ξανά. ')
    if not ans: return None
    nums = [int(x.replace('.', '')) for x in re.findall(r'\b\d{2,4}\b', ans)]
    LIMKEY = {'δεν οδηγώ': ['οδηγ', 'αυτοκίνητ', 'λεωφορ', 'τρένο', 'ΚΤΕΛ', 'ταξί', 'πόδια', 'περπάτ'], 'δεν μπορώ να περπατήσω πολύ': ['περπάτ', 'πόδια', 'κοντιν', 'ξεκούρασ', 'αυτοκίνητ', 'ταξί'], 'είμαι χορτοφάγος': ['χορτοφαγ', 'λαχανικ', 'νηστίσιμ', 'χωρίς κρέας', 'vegan', 'vegetarian'], 'έχω μαζί ένα παιδί 5 ετών': ['παιδ', 'παιδικ', 'μικρό'], 'δεν μιλάω αγγλικά': ['αγγλικ', 'ελληνικ', 'γλώσσ']}
    ok = city.lower()[:4] in ans.lower() and not any(n > budget for n in nums) and any(k.lower() in ans.lower() for k in LIMKEY[limit])
    msgs.append(dict(role='assistant', content=ans)); return dict(id=f'S5m_{k:05d}', lane='S5m', kind=limit, turns=msgs, verified=ok, facts=dict(name=name, city=city, budget=budget, limit=limit))


LANES = {'S1': lane_s1, 'S2': lane_s2, 'S3': lane_s3, 'S3c': lane_s3c, 'S4': lane_s4, 'S5m': lane_s5m}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--lane', required=True, choices=list(LANES)); ap.add_argument('--n', type=int, default=500); ap.add_argument('--seed', type=int, default=3)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); path = f'{a.out}/{a.lane}.jsonl'; base = base_rows(); print(len(base), 'base rows', flush=True)
    have = {json.loads(l)['id'] for l in open(path)} if os.path.exists(path) else set(); todo = [k for k in range(a.n) if f'{a.lane}_{k:05d}' not in have]; print(a.lane, len(todo), 'to build', flush=True)
    def one(k):
        d = LANES[a.lane](k, random.Random(hash((a.lane, a.seed, k)) & 0xffffffff), base)
        if d:
            with lock, open(path, 'a') as f: f.write(json.dumps(d, ensure_ascii=False) + '\n')
    with ThreadPoolExecutor(W) as pool: list(pool.map(one, todo))
    rows = [json.loads(l) for l in open(path)]; by = collections.defaultdict(list)
    for r in rows: by[r['kind']].append(r['verified'])
    summ = dict(lane=a.lane, rows=len(rows), verified=sum(r['verified'] for r in rows), verified_rate=round(sum(r['verified'] for r in rows) / max(1, len(rows)), 3), by_kind={k: (len(v), round(sum(v) / len(v), 3)) for k, v in by.items()}, mean_turns=round(sum(len(r['turns']) for r in rows) / max(1, len(rows)), 1))
    json.dump(summ, open(f'{a.out}/{a.lane}_summary.json', 'w'), ensure_ascii=False, indent=1); print(json.dumps(summ, ensure_ascii=False))


if __name__ == '__main__': main()
