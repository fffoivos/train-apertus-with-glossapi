#!/usr/bin/env python3
"""Greek math pilots (plan docs/GREEK_MATH_DATASET_PLAN_20260909.md §5).
  translate <out_dir> [n_gsm=300] [n_math=300]   M1: Sol translates+localises GSM8K/MATH train rows to Greek, then solves the Greek version blind; fidelity = solve reaches the reference answer. M4 formatting on the solutions.
  native    <out_dir> [n=500]                    M2: Sol writes native Greek curriculum problems with solutions; Luna solves them blind; agreement + numeric check. M4 formatting.
Sources under ~/sft_annot/math_src (gsm8k_train.jsonl, math_train.jsonl). env WORKERS (24), GEN_MODEL (gpt-5.6-sol), SOLVER2 (gpt-5.6-luna)."""
import collections, json, os, random, sys, threading
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import mathlib as M
SRC = os.path.expanduser('~/sft_annot/math_src'); W = int(os.environ.get('WORKERS', '24')); GEN = os.environ.get('GEN_MODEL', 'gpt-5.6-sol'); SOLVER2 = os.environ.get('SOLVER2', 'gpt-5.6-luna')
lock = threading.Lock()
S_TRANS = M.write_schema('s_trans.json', {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string"}, "problem_el": {"type": "string"}, "changes": {"type": "string"}}, "required": ["id", "problem_el", "changes"], "additionalProperties": False}}}, "required": ["items"], "additionalProperties": False})
S_SOLVE = M.write_schema('s_solve.json', {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string"}, "solution_el": {"type": "string"}, "final_answer": {"type": "string"}}, "required": ["id", "solution_el", "final_answer"], "additionalProperties": False}}}, "required": ["items"], "additionalProperties": False})
S_NATIVE = M.write_schema('s_native.json', {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "object", "properties": {"problem_el": {"type": "string"}, "solution_el": {"type": "string"}, "final_answer": {"type": "string"}}, "required": ["problem_el", "solution_el", "final_answer"], "additionalProperties": False}}}, "required": ["items"], "additionalProperties": False})
RULES = ('Κανόνες γραφής: λύση βήμα προς βήμα στα ελληνικά, σύντομες προτάσεις, ένα ουσιαστικό βήμα ανά γραμμή (μικρές εκφράσεις επιτρέπονται), εξισώσεις με σωστές διαστάσεις (όχι «1 ώρα · 60 = 60 λεπτά» αλλά «1 ώρα = 60 λεπτά»), μία σύντομη αιτιολόγηση του γιατί εφαρμόζεται κάθε πράξη, ελληνική μορφή αριθμών (δεκαδικό κόμμα «3,5», τελεία χιλιάδων «1.000», το «€» μετά τον αριθμό «25 €», σύμβολο πολλαπλασιασμού «·»), '
         'και τελευταία γραμμή «Απάντηση: …» με μόνο το τελικό αποτέλεσμα (αριθμό, κλάσμα ή έκφραση) και τη μονάδα αν υπάρχει.')
TRANS = ('Μετάφρασε και προσάρμοσε στα ελληνικά τα παρακάτω μαθηματικά προβλήματα, ώστε να διαβάζονται σαν γραμμένα για μαθητή στην Ελλάδα: ελληνικά ονόματα και τόποι, ευρώ αντί για δολάρια (κράτησε ΤΟΥΣ ΙΔΙΟΥΣ αριθμούς), ελληνική μορφή αριθμών (δεκαδικό κόμμα, τελεία χιλιάδων), '
         'μονάδες SI όπου το πρωτότυπο έχει ίντσες/μίλια ΜΟΝΟ αν δεν αλλάζει η αριθμητική (αλλιώς κράτα τη μονάδα). Μην αλλάξεις τη μαθηματική δομή ούτε την απάντηση. Σημείωσε στο «changes» τι προσάρμοσες. Επίστρεψε JSON {{"items":[{{"id","problem_el","changes"}}]}} με ακριβώς τα {n} ids.\n\n{body}')
SOLVE = 'Λύσε καθένα από τα παρακάτω {n} προβλήματα ανεξάρτητα. ' + RULES + ' Στο «final_answer» βάλε μόνο το τελικό αποτέλεσμα. Επίστρεψε JSON {{"items":[{{"id","solution_el","final_answer"}}]}} με ακριβώς τα {n} ids.\n\n{body}'
GRADES = ['Γ΄ Δημοτικού', 'Δ΄ Δημοτικού', 'Ε΄ Δημοτικού', 'ΣΤ΄ Δημοτικού', 'Α΄ Γυμνασίου', 'Β΄ Γυμνασίου', 'Γ΄ Γυμνασίου', 'Α΄ Λυκείου', 'Β΄ Λυκείου', 'Γ΄ Λυκείου']
TOPICS = ['αριθμητική με ακέραιους', 'κλάσματα και δεκαδικοί', 'ποσοστά, ΦΠΑ και εκπτώσεις', 'αναλογίες και λόγοι', 'μονάδες μέτρησης και μετατροπές', 'εξισώσεις πρώτου βαθμού', 'συστήματα και δευτεροβάθμιες', 'συναρτήσεις', 'γεωμετρία επίπεδη (εμβαδά, περίμετροι, γωνίες)', 'γεωμετρία στερεά (όγκοι)', 'τριγωνομετρία', 'πιθανότητες', 'στατιστική (μέσος, διάμεσος)', 'θεωρία αριθμών (διαιρετότητα, ΜΚΔ, ΕΚΠ)', 'ακολουθίες και πρόοδοι', 'χρόνος, ταχύτητα, απόσταση']
CONTEXTS = ['λαϊκή αγορά', 'σχολική εκδρομή', 'ταξίδι με ΚΤΕΛ ή πλοίο', 'μαγείρεμα και συνταγές', 'ποδόσφαιρο ή μπάσκετ', 'αγρόκτημα και ελαιώνας', 'λογαριασμοί ΔΕΗ και ενοίκιο', 'κατασκευή και επισκευές στο σπίτι', 'πανηγύρι και εκδηλώσεις', 'καθαρά μαθηματικά, χωρίς ιστορία']
SURFACES = ['απλή διατύπωση', 'με μία άσχετη πληροφορία που πρέπει να αγνοηθεί', 'με μικρό πίνακα ή λίστα δεδομένων', 'σε δύο ερωτήματα (α) και (β)']
NATIVE = ('Γράψε {n} ΝΕΑ μαθηματικά προβλήματα για μαθητή {grade}, θέμα «{topic}», περίσταση «{ctx}», μορφή «{surface}». Κάθε πρόβλημα με πλήρη εκφώνηση όπως σε ελληνικό σχολικό βιβλίο ή διαγώνισμα (ονόματα, τόποι, ευρώ, ελληνική μορφή αριθμών), '
          'ρεαλιστικούς αριθμούς, μία σαφή τελική απάντηση, δυσκολία κατάλληλη για την τάξη. ' + RULES + ' Επίστρεψε JSON {{"items":[{{"problem_el","solution_el","final_answer"}}]}} με ακριβώς {n} στοιχεία.')


def call(prompt, schema, model=GEN, effort='medium', tries=3):
    for t in range(tries):
        try: return M.codex_json(prompt, schema, model, effort)
        except Exception as e: print('retry', t, model, type(e).__name__, str(e)[:100], flush=True)
    return None


def append(path, rows):
    with lock, open(path, 'a') as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')


def done_ids(path):
    return {json.loads(l)['id'] for l in open(path)} if os.path.exists(path) else set()


def translate(out, n_gsm=300, n_math=300):
    os.makedirs(out, exist_ok=True); rng = random.Random(9)
    gsm = [json.loads(l) for l in open(f'{SRC}/gsm8k_train.jsonl')]; math = [json.loads(l) for l in open(f'{SRC}/math_train.jsonl')]
    math = [r for r in math if r.get('level') in tuple(x.strip() for x in os.environ.get('MATH_LEVELS', 'Level 1,Level 2,Level 3').split(','))]
    rows = [dict(id=f'gsm_{i}', src='gsm8k', problem_en=r['question'], ref=M.gsm_answer(r['answer']), level='gsm') for i, r in enumerate(rng.sample(gsm, n_gsm))]
    rows += [dict(id=f'math_{i}', src='math', problem_en=r['problem'], ref=M.boxed(r['solution']) or '', level=r['level'], subject=r['subject']) for i, r in enumerate(rng.sample(math, n_math))]
    rows = [r for r in rows if r['ref']]; append_rows = {r['id']: r for r in rows}
    tp = f'{out}/translated.jsonl'; have = done_ids(tp); todo = [r for r in rows if r['id'] not in have]; print(len(todo), 'to translate', flush=True)
    def tbatch(ch):
        body = '\n\n'.join(f'=== id: {r["id"]} ===\n{r["problem_en"]}' for r in ch); j = call(TRANS.format(n=len(ch), body=body), S_TRANS)
        if j and {x['id'] for x in j['items']} == {r['id'] for r in ch}: append(tp, [dict(append_rows[x['id']], problem_el=x['problem_el'], changes=x['changes']) for x in j['items']])
    with ThreadPoolExecutor(W) as pool: list(pool.map(tbatch, [todo[i:i + 10] for i in range(0, len(todo), 10)]))
    tr = [json.loads(l) for l in open(tp)]; sp = f'{out}/solved.jsonl'; have = done_ids(sp); todo = [r for r in tr if r['id'] not in have]; print(len(todo), 'to solve', flush=True)
    def sbatch(ch):
        body = '\n\n'.join(f'=== id: {r["id"]} ===\n{r["problem_el"]}' for r in ch); j = call(SOLVE.format(n=len(ch), body=body), S_SOLVE, effort='high')
        if j and {x['id'] for x in j['items']} == {r['id'] for r in ch}: append(sp, [dict(id=x['id'], solution_el=x['solution_el'], final_answer=x['final_answer']) for x in j['items']])
    with ThreadPoolExecutor(W) as pool: list(pool.map(sbatch, [todo[i:i + 5] for i in range(0, len(todo), 5)]))
    sol = {json.loads(l)['id']: json.loads(l) for l in open(sp)}; res = []
    for r in tr:
        s = sol.get(r['id'])
        if not s: continue
        fa = s['final_answer'] or M.final_answer(s['solution_el']); ok = M.equiv(fa, r['ref']); res.append(dict(r, **s, final_used=fa, correct=ok, fmt=M.fmt_checks(s['solution_el'])))
    with open(f'{out}/results.jsonl', 'w') as f:
        for r in res: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    by = lambda key: {k: dict(n=len(v), fidelity=round(sum(x['correct'] for x in v) / len(v), 3)) for k, v in sorted(collections.defaultdict(list, {k: [x for x in res if key(x) == k] for k in {key(x) for x in res}}).items())}
    fmt = {k: round(sum(x['fmt'][k] for x in res) / len(res), 3) for k in ('decimal_comma_ok', 'euro_after_number', 'answer_line')}
    summ = dict(n=len(res), fidelity=round(sum(x['correct'] for x in res) / len(res), 3), by_source=by(lambda x: x['src']), by_level=by(lambda x: x['level']), formatting=fmt, mean_greek_share=round(sum(x['fmt']['greek_share'] for x in res) / len(res), 3))
    json.dump(summ, open(f'{out}/summary.json', 'w'), ensure_ascii=False, indent=1); print(json.dumps(summ, ensure_ascii=False))


def native(out, n=500):
    os.makedirs(out, exist_ok=True); rng = random.Random(int(os.environ.get('NATIVE_SEED', '11'))); per = 5   # NATIVE_SEED=… for the held-out set (M5)
    cells = [(rng.choice(GRADES), rng.choice(TOPICS), rng.choice(CONTEXTS), rng.choice(SURFACES)) for _ in range(n // per)]
    pp = f'{out}/problems.jsonl'; have = len(done_ids(pp)) // per; todo = list(enumerate(cells))[have:]; print(len(todo), 'cells to write', flush=True)
    def wbatch(ic):
        i, (g, t, c, s) = ic; j = call(NATIVE.format(n=per, grade=g, topic=t, ctx=c, surface=s), S_NATIVE, effort='high')
        if j and len(j['items']) == per: append(pp, [dict(id=f'nat_{i}_{k}', grade=g, topic=t, context=c, surface=s, **x) for k, x in enumerate(j['items'])])
    with ThreadPoolExecutor(W) as pool: list(pool.map(wbatch, todo))
    probs = [json.loads(l) for l in open(pp)]; sp = f'{out}/solved2.jsonl'; have = done_ids(sp); verify = {x.strip() for x in os.environ.get('VERIFY_GRADES', '').split(',') if x.strip()}   # VERIFY_GRADES limits the second solve to the hardest grades (owner, 9 Sep)
    todo = [r for r in probs if r['id'] not in have and (not verify or r['grade'] in verify)]; print(len(todo), 'to solve with', SOLVER2, ('(grades ' + ', '.join(sorted(verify)) + ')') if verify else '', flush=True)
    def sbatch(ch):
        body = '\n\n'.join(f'=== id: {r["id"]} ===\n{r["problem_el"]}' for r in ch); j = call(SOLVE.format(n=len(ch), body=body), S_SOLVE, model=SOLVER2, effort='high')
        if j and {x['id'] for x in j['items']} == {r['id'] for r in ch}: append(sp, [dict(id=x['id'], solution2=x['solution_el'], final2=x['final_answer']) for x in j['items']])
    with ThreadPoolExecutor(W) as pool: list(pool.map(sbatch, [todo[i:i + 5] for i in range(0, len(todo), 5)]))
    s2 = {json.loads(l)['id']: json.loads(l) for l in open(sp)}; res = []
    for r in probs:
        s = s2.get(r['id'])
        if not s:
            if verify and r['grade'] not in verify: res.append(dict(r, solution2='', final2='', agree=None, numeric=M.norm_num(r['final_answer'] or '') is not None, fmt=M.fmt_checks(r['solution_el'])))   # unverified by design
            continue
        f1 = r['final_answer'] or M.final_answer(r['solution_el']); f2 = s['final2'] or M.final_answer(s['solution2']); agree = M.equiv(f1, f2)
        numeric = M.norm_num(f1) is not None and M.norm_num(f2) is not None
        res.append(dict(r, **s, agree=agree, numeric=numeric, fmt=M.fmt_checks(r['solution_el'])))
    with open(f'{out}/results.jsonl', 'w') as f:
        for r in res: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    ver = [x for x in res if x['agree'] is not None]
    by = lambda key: {k: dict(n=len(v), agree=(round(sum(x['agree'] for x in v) / len(v), 3) if v else None)) for k, v in sorted(collections.defaultdict(list, {k: [x for x in ver if key(x) == k] for k in {key(x) for x in ver}}).items())}
    fmt = {k: round(sum(x['fmt'][k] for x in res) / len(res), 3) for k in ('decimal_comma_ok', 'euro_after_number', 'answer_line')}
    summ = dict(n=len(res), verified=len(ver), agree=(round(sum(x['agree'] for x in ver) / len(ver), 3) if ver else None), numeric_share=round(sum(x['numeric'] for x in res) / len(res), 3), by_grade=by(lambda x: x['grade']), by_topic=by(lambda x: x['topic']), by_surface=by(lambda x: x['surface']), formatting=fmt)
    json.dump(summ, open(f'{out}/summary.json', 'w'), ensure_ascii=False, indent=1); print(json.dumps(summ, ensure_ascii=False))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'translate': translate(sys.argv[2], *(int(x) for x in sys.argv[3:5]))
    elif cmd == 'native': native(sys.argv[2], *(int(x) for x in sys.argv[3:4]))
