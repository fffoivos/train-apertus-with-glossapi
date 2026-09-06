#!/usr/bin/env python3
"""Stage 1: questions only. The writer sees a topic TITLE, never the fact, so it cannot lean on hidden context.
Usage: python3 gen_questions.py <sheet_v2.json> <out.jsonl> <fact_ids|all> <seed> [per_fact=6] [model=claude-opus-5]"""
import json, sys, os, random, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from claude_call import call, TOT
SHEET, OUT, IDS, SEED = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]); PER = int(sys.argv[5]) if len(sys.argv) > 5 else 6; MODEL = sys.argv[6] if len(sys.argv) > 6 else 'claude-opus-5'
LOG = OUT + '.log'; facts = json.load(open(SHEET)); want = None if IDS == 'all' else set(IDS.split(','))
facts = [f for f in facts if want is None or f['id'] in want]; rnd = random.Random(SEED); rnd.shuffle(facts)
USERS = ['μαθητής γυμνασίου', 'φοιτήτρια', 'γιαγιά που ρωτά το εγγόνι της', 'τουρίστας που γράφει ελληνικά', 'δημοσιογράφος', 'ομογενής από την Αμερική', 'κάποιος με λάθος υπόθεση', 'νεαρός σε greeklish', 'κάποιος που γράφει χωρίς τόνους', 'δημόσιος υπάλληλος', 'μικρός επιχειρηματίας', 'μετανάστης που έμαθε ελληνικά', 'δάσκαλος που ετοιμάζει μάθημα', 'κάποιος που έβαλε στοίχημα', 'παιδί δημοτικού', 'ξένος ανταποκριτής']
FORMS = ['what', 'when_or_howmuch', 'why', 'comparative_or_which_is_right', 'wrong_assumption', 'wide_scope']
FORM_EL = {'what': 'τι/ποιος/πού (γεγονός)', 'when_or_howmuch': 'πότε/πόσο (αριθμός ή ημερομηνία)', 'why': 'γιατί/πώς γίνεται (ζητά εξήγηση)', 'comparative_or_which_is_right': 'σύγκριση ή «ποιο είναι το σωστό» (δύο εκδοχές που είδε ο χρήστης)', 'wrong_assumption': 'ερώτηση με λάθος υπόθεση που πρέπει να διορθωθεί', 'wide_scope': 'ευρύ αίτημα (π.χ. «γράψε μου μια παράγραφο για…», «πες μου τα βασικά για…»)'}
BRIEF = """Γράφεις ΜΟΝΟ ερωτήσεις χρηστών (όχι απαντήσεις) για έναν ελληνικό βοηθό. Οι χρήστες είναι Έλληνες (ή ξένοι που γράφουν ελληνικά) και ρωτούν όπως ρωτούν στην πράξη: σύντομα, με το δικό τους ύφος, καμιά φορά σε greeklish ή χωρίς τόνους, καμιά φορά με λάθος υπόθεση, καμιά φορά με πλαίσιο («ετοιμάζω…», «διάβασα ότι…»). «Εμείς», «η χώρα μας», «εδώ» = η Ελλάδα.
ΚΑΝΟΝΑΣ 1: κάθε ερώτηση πρέπει να είναι ΑΥΤΟΤΕΛΗΣ: όποιος τη διαβάσει χωρίς να ξέρει τίποτα άλλο πρέπει να καταλαβαίνει ακριβώς τι ρωτιέται. Καμία αναφορά σε «τη φωτογραφία», «το βιβλίο», «αυτό» χωρίς να λέγεται τι είναι. Αν η ερώτηση θέλει πλαίσιο, το πλαίσιο μπαίνει μέσα στην ερώτηση.
ΚΑΝΟΝΑΣ 2: για κάθε ερώτηση γράψε needs_el: τι πρέπει να περιέχει μια ΠΛΗΡΗΣ απάντηση (μία πρόταση). Αν το θέμα είναι ευρύ, το needs_el το λέει («όλη η χρονολογία από… ως…»).
ΚΑΝΟΝΑΣ 3: οι μορφές ζητούνται ρητά ανά ερώτηση (form). Στη μορφή why ο χρήστης ζητά εξήγηση· στη σύγκριση ο χρήστης έχει δει δύο εκδοχές και ρωτά ποια ισχύει· στην ευρεία μορφή ζητά παράγραφο ή περίληψη.
Για μία στις τέσσερις ερωτήσεις γράψε και followup_el: μια φυσική δεύτερη ερώτηση του ίδιου χρήστη μετά την απάντηση (συχνά «γιατί;», «και τι σημαίνει αυτό;», «δηλαδή;»)· αλλιώς κενό.
Επίστρεψε ΜΟΝΟ JSON: {"questions": [{"topic": id, "form": form, "user_type": ..., "user_el": ερώτηση, "needs_el": ..., "followup_el": ...}, ...]}."""
def task(chunk, k):
    lines = []
    for f in chunk:
        forms = rnd.sample(FORMS, min(PER, len(FORMS))) if PER <= len(FORMS) else FORMS + rnd.choices(FORMS, k=PER - len(FORMS)); users = rnd.sample(USERS, PER)
        lines.append(f"ΘΕΜΑ [{f['id']}]: {f['title_el']}\n  ερωτήσεις: " + '; '.join(f"{i+1}) form={fo} ({FORM_EL[fo]}), χρήστης: {u}" for i, (fo, u) in enumerate(zip(forms, users))))
    return f"Γράψε {PER} ερωτήσεις για ΚΑΘΕ θέμα (μόνο ο τίτλος του θέματος σού δίνεται, σκόπιμα), με τις μορφές και τους χρήστες που ορίζονται:\n\n" + '\n'.join(lines)
chunks = [facts[i:i + 5] for i in range(0, len(facts), 5)]; done = set()
if os.path.exists(OUT):
    for l in open(OUT): done.add(json.loads(l)['topic'])
todo = [(k, c) for k, c in enumerate(chunks) if not all(f['id'] in done for f in c)]; print(f'{len(facts)} topics, {len(todo)} chunks to run, seed {SEED}, {MODEL}', flush=True)
def run(kc):
    k, c = kc; obj = call(BRIEF + '\n\n' + task(c, k), MODEL, LOG, f'Q{k}')
    if not obj: return []
    out = []
    for i, q in enumerate(obj.get('questions', [])):
        if isinstance(q, dict) and q.get('user_el') and q.get('topic'): out.append(dict(id=f"s{SEED}_{q['topic']}_{i:02d}", topic=q['topic'], form=q.get('form'), user_type=q.get('user_type'), user_el=q['user_el'], needs_el=q.get('needs_el'), followup_el=q.get('followup_el') or '', seed=SEED))
    return out
with open(OUT, 'a') as fh, cf.ThreadPoolExecutor(3) as ex:
    for out in ex.map(run, todo):
        for q in out: fh.write(json.dumps(q, ensure_ascii=False) + '\n')
        fh.flush(); print(f'+{len(out)} questions | ${TOT["cost"]:.2f}', flush=True)
print('ALL DONE', flush=True)
