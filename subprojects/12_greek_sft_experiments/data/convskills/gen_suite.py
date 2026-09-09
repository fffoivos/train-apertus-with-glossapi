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


NEUTRAL = {'length_words_max', 'length_words_min', 'keywords_include', 'keywords_exclude', 'keyword_freq', 'greek_only', 'monotonic_only', 'no_exclamation', 'mention_number', 'mention_euro', 'mention_date', 'mention_entity', 'avoid_entity', 'formal_plural', 'informal_singular', 'greek_question_mark'}   # constraints that leave the answer looking like a normal answer
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
    return out


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
    elif kind == 'count': q = rng.choice(['Πόσες ερωτήσεις σου έχω κάνει ως τώρα;', 'Μέτρα: πόσα μηνύματα σου έστειλα;']); must = str(len(users)); check = lambda a: re.search(rf'\b{len(users)}\b|\b{["", "μία", "δύο", "τρεις", "τέσσερις", "πέντε", "έξι", "επτά"][len(users)]}\b', a) is not None
    elif kind == 'list':
        q = rng.choice(['Κάνε μου λίστα με όλα όσα σου ζήτησα ως τώρα, με τη σειρά.', 'Ποια ήταν τα αιτήματά μου, ένα ένα;']); must = 'μια αριθμημένη λίστα με ΟΛΑ τα αιτήματά μου με τη σειρά, το καθένα σε 5–15 λέξεις (περίληψη ή η πρώτη του πρόταση, όχι κομμένη φράση): ' + ' || '.join(C.sentences(u)[0] if C.sentences(u) else u for u in users)
        def check(a, users=users):
            al = re.sub(r'\s+', ' ', a.lower())
            return all(sum(w.lower() in al for w in sorted(C.words(u), key=len, reverse=True)[:5]) >= 2 for u in users) and len(re.findall(r'(?m)^\s*(?:\d+[.)]|[-•])', a)) >= len(users)
    else: i = rng.randrange(len(users)); q = rng.choice([f'Τι μου είπες πριν για το θέμα «{prior[i]["meta"]["subtopic"]}»;', f'Θύμισέ μου την απάντησή σου για «{prior[i]["meta"]["subtopic"]}».']); must = prior[i]['assistant'][:80]; check = lambda a: any(re.sub(r'\s+', ' ', s.lower()) in re.sub(r'\s+', ' ', a.lower()) for s in C.sentences(prior[i]['assistant'])[:2])
    msgs.append(dict(role='user', content=q)); ans = phrase_answer(msgs, must, rng, 'Μην πεις ότι δεν βλέπεις τη συζήτηση: τη βλέπεις ολόκληρη και παραθέτεις. ')
    if not ans: return None
    ok = bool(check(ans)) and 'δεν έχω πρόσβαση' not in ans and 'δεν βλέπω' not in ans
    msgs.append(dict(role='assistant', content=ans)); return dict(id=f'S1_{k:05d}', lane='S1', kind=kind, turns=msgs, verified=ok, must=must)


# ---------- S2: standing instruction persistence ----------
PERSIST = {'one_sentence': ('Από εδώ και πέρα απάντα μου με μία πρόταση μόνο.', lambda a: len(C.sentences(a)) <= 1), 'max20': ('Από εδώ και πέρα κάθε απάντησή σου να έχει το πολύ 20 λέξεις.', lambda a: len(a.split()) <= 20),
           'no_questions': ('Από εδώ και πέρα μη μου κάνεις ερωτήσεις πίσω.', lambda a: ';' not in a and '?' not in a), 'formal_plural': ('Από εδώ και πέρα να μου μιλάς στον πληθυντικό ευγενείας.', lambda a: not re.search(r'\b(εσύ|σου|μπορείς|θέλεις|έχεις|δες|κάνε)\b', a, re.I)),
           'bullets': ('Από εδώ και πέρα απάντα πάντα σε κουκκίδες.', lambda a: bool(re.search(r'(?m)^\s*[-•]', a))), 'end_phrase': ('Από εδώ και πέρα να κλείνεις κάθε απάντηση με τη φράση «Καλή συνέχεια».', lambda a: a.rstrip(' .!»"').lower().endswith('καλή συνέχεια')),
           'greeklish': ('Apo edw kai pera apanta mou se greeklish.', lambda a: len(re.findall(r'[Ͱ-Ͽ]', a)) / max(1, len(re.findall(r'[Ͱ-ϿA-Za-z]', a))) < 0.2)}
REVOKE = ['Εντάξει, άσε τον περιορισμό, απάντα κανονικά.', 'Ξέχνα την οδηγία που σου έδωσα, μίλα κανονικά.']


def lane_s2(k, rng, base):
    pid, (instr, chk) = rng.choice(list(PERSIST.items())); n_later = rng.randint(5, 9); revoke = rng.random() < 0.5
    prior = rng.sample(base, 1 + n_later + (1 if revoke else 0)); msgs = [dict(role='user', content=prior[0]['user'].split('\n\n')[0]), dict(role='assistant', content=prior[0]['assistant'])]
    msgs.append(dict(role='user', content=instr)); qs = [r['user'].split('\n\n')[0] for r in prior[1:1 + n_later]]
    j = call(f"{VOICE}\n\nΣυζήτηση ως τώρα:\n{transcript(msgs)}\n\nΟ χρήστης έδωσε μόνιμη οδηγία: «{instr}». Γράψε (1) τη σύντομη αποδοχή της οδηγίας (μία πρόταση, χωρίς «εντάξει» μόνο του) και μετά (2) τις απαντήσεις στα επόμενα {n_later} μηνύματα, ΟΛΕΣ σύμφωνα με την οδηγία ακόμη κι όταν το θέμα θέλει περισσότερα (συμπύκνωσε, μην παραβείς):\n" + '\n'.join(f'{i+1}. {q}' for i, q in enumerate(qs)) + f"\nΕπίστρεψε JSON {{\"answers\": [αποδοχή, απάντηση1, …, απάντηση{n_later}]}} με {n_later + 1} στοιχεία.", S_TURNS)
    if not j or len(j['answers']) != n_later + 1: return None
    msgs.append(dict(role='assistant', content=j['answers'][0])); kept = [bool(chk(j['answers'][0]))]
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


def lane_s3(k, rng, base):
    r = rng.choice(base); op = rng.choice(list(EDITS)); old = r['assistant']
    if op == 'to_prose' and not re.search(r'(?m)^\s*(?:[-•]|\d+[.)])', old): op = 'to_list'
    if op == 'to_list' and re.search(r'(?m)^\s*[-•]', old): op = 'shorter'
    p = {}
    if op == 'without':
        cands = [w for w in set(C.words(old)) if len(w) >= 6 and w.lower() not in old.lower().split(' ')[0]]; p['w'] = rng.choice(cands) if cands else None
        if not p['w']: op = 'shorter'
    instr = EDITS[op][0].format(**p); msgs = [dict(role='user', content=r['user'].split('\n\n')[0]), dict(role='assistant', content=old), dict(role='user', content=instr)]
    j = call(f"{VOICE}\n\nΣυζήτηση:\n{transcript(msgs)}\n\nΓράψε τη νέα απάντηση: επεξεργάσου ΤΗΝ ΠΡΟΗΓΟΥΜΕΝΗ απάντηση ακριβώς όπως ζήτησε ο χρήστης (μην αλλάξεις περιεχόμενο πέρα από αυτό, μην προσθέσεις νέες πληροφορίες, μη σχολιάσεις την αλλαγή). Επίστρεψε JSON {{\"answer\"}}.", S_ONE)
    if not j: return None
    new = j['answer']; ok = bool(EDITS[op][1](old, new, p)); msgs.append(dict(role='assistant', content=new))
    return dict(id=f'S3_{k:05d}', lane='S3', kind=op, turns=msgs, verified=ok, params=p)


# ---------- S4: stop this habit ----------
TICS = ['Πες μου τι άλλο σε απασχολεί.', 'Ελπίζω να βοήθησα.', 'Αν θες, το δουλεύουμε κι άλλο.', 'Εντάξει;', 'Χαχα.', 'Να ’σαι καλά.']


def lane_s4(k, rng, base):
    tic = rng.choice(TICS); prior = rng.sample(base, 4 + rng.randint(0, 2)); msgs = []
    for r in prior[:2]: msgs += [dict(role='user', content=r['user'].split('\n\n')[0]), dict(role='assistant', content=r['assistant'].rstrip() + ' ' + tic)]
    stop = rng.choice([f'Σταμάτα να λες «{tic.rstrip(".;")}» στο τέλος κάθε απάντησης.', f'Κόψε το «{tic.rstrip(".;")}», το γράφεις κάθε φορά.', f'Μη μου ξαναγράψεις «{tic.rstrip(".;")}».'])
    msgs.append(dict(role='user', content=stop)); later = prior[2:]
    j = call(f"{VOICE}\n\nΣυζήτηση ως τώρα:\n{transcript(msgs)}\n\nΟ χρήστης ζήτησε να σταματήσεις τη φράση «{tic}». Γράψε (1) μια απάντηση μίας πρότασης που δέχεται το αίτημα ΧΩΡΙΣ να περιέχει τη φράση και χωρίς «δικό μου λάθος», και μετά (2) τις απαντήσεις στα επόμενα {len(later)} μηνύματα, καμία με τη φράση ή παραλλαγή της:\n" + '\n'.join(f'{i+1}. {r["user"].split(chr(10)+chr(10))[0]}' for i, r in enumerate(later)) + f"\nΕπίστρεψε JSON {{\"answers\": [αποδοχή, …]}} με {len(later) + 1} στοιχεία.", S_TURNS)
    if not j or len(j['answers']) != len(later) + 1: return None
    key = re.sub(r'\s+', ' ', tic.rstrip('.;').lower()); ok = all(key not in re.sub(r'\s+', ' ', a.lower()) for a in j['answers'])
    msgs.append(dict(role='assistant', content=j['answers'][0]))
    for r, a in zip(later, j['answers'][1:]): msgs += [dict(role='user', content=r['user'].split('\n\n')[0]), dict(role='assistant', content=a)]
    return dict(id=f'S4_{k:05d}', lane='S4', kind=tic, turns=msgs, verified=ok)


LANES = {'S1': lane_s1, 'S2': lane_s2, 'S3': lane_s3, 'S4': lane_s4}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--lane', required=True, choices=list(LANES)); ap.add_argument('--n', type=int, default=500); ap.add_argument('--seed', type=int, default=3)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); path = f'{a.out}/{a.lane}.jsonl'; base = base_rows(); print(len(base), 'base rows', flush=True)
    have = {json.loads(l)['id'] for l in open(path)} if os.path.exists(path) else set(); todo = [k for k in range(a.n) if f'{a.lane}_{k:05d}' not in have]; print(a.lane, len(todo), 'to build', flush=True)
    def one(k):
        d = LANES[a.lane](k, random.Random(a.seed * 100000 + k), base)
        if d:
            with lock, open(path, 'a') as f: f.write(json.dumps(d, ensure_ascii=False) + '\n')
    with ThreadPoolExecutor(W) as pool: list(pool.map(one, todo))
    rows = [json.loads(l) for l in open(path)]; by = collections.defaultdict(list)
    for r in rows: by[r['kind']].append(r['verified'])
    summ = dict(lane=a.lane, rows=len(rows), verified=sum(r['verified'] for r in rows), verified_rate=round(sum(r['verified'] for r in rows) / max(1, len(rows)), 3), by_kind={k: (len(v), round(sum(v) / len(v), 3)) for k, v in by.items()}, mean_turns=round(sum(len(r['turns']) for r in rows) / max(1, len(rows)), 1))
    json.dump(summ, open(f'{a.out}/{a.lane}_summary.json', 'w'), ensure_ascii=False, indent=1); print(json.dumps(summ, ensure_ascii=False))


if __name__ == '__main__': main()
