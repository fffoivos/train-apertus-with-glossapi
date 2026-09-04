#!/usr/bin/env python3
"""Correction pass on the Greek rewriting set: a second Sol call reads passage + instruction + answer with an editor's brief and
returns the corrected answer plus a list of what it changed. Resumable. Usage: python3 gen_greek_rewrite_edit.py <gen.jsonl> <out.jsonl> <workers>"""
import json, sys, os, time, subprocess, tempfile, threading, collections, concurrent.futures as cf
IN, OUT, W = sys.argv[1], sys.argv[2], int(sys.argv[3])
MODEL = os.environ.get('GEN_MODEL', 'gpt-5.6-sol'); EFFORT = os.environ.get('GEN_EFFORT', 'high'); TIER = os.environ.get('GEN_TIER', 'default')
SCHEMA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'greek_rewrite_edit_schema.json')
json.dump({"type": "object", "additionalProperties": False, "required": ["verdict", "edited_answer", "changes"],
           "properties": {"verdict": {"type": "string", "enum": ["ok", "edited", "rewrite"]}, "edited_answer": {"type": "string"},
                          "changes": {"type": "array", "items": {"type": "string"}}}}, open(SCHEMA, 'w'), ensure_ascii=False)
BRIEF = """Είσαι ο τελικός επιμελητής μιας γραμμής εκπαίδευσης για έναν ελληνικό βοηθό: ένα ελληνικό κείμενο, η οδηγία ενός Έλληνα χρήστη πάνω σε αυτό, και η απάντηση του βοηθού. Η γραμμή γράφτηκε εξαρχής στα ελληνικά, μέσα στον κόσμο ενός Έλληνα: πρόσωπα, τόποι, υπηρεσίες, ευρώ, συνήθειες είναι αυτά που ξέρει ένας Έλληνας. Πριν αγγίξεις οτιδήποτε, χτίσε την κατανόησή σου σε τρία βήματα, με αυτή τη σειρά.

**1. Το έργο.** Η οδηγία του χρήστη ορίζει το έργο: τι ζητείται, με ποια μορφή, με ποιο μήκος. Η απάντηση κρίνεται απέναντι στην οδηγία και στο κείμενο — όχι απέναντι σε ό,τι εσύ θα ζητούσες. Οι ιδιότητες της ίδιας της οδηγίας ανήκουν στο έργο, όχι σε σένα: ένα βιαστικό ύφος, μια ζητούμενη αυστηρότητα, ένα μήνυμα μέχρι 160 χαρακτήρες.

**2. Η πιστότητα.** Η απάντηση δεν προσθέτει γεγονότα, ονόματα, ποσά, ημερομηνίες που δεν υπάρχουν στο κείμενο (εκτός αν η οδηγία ζητά ανάπτυξη· και τότε οι προσθήκες είναι λογικές και όχι επινοήσεις που αλλάζουν τα γεγονότα), και δεν παραλείπει ουσιώδη σημεία που ζητούνται. Αν ζητούνται τρεις προτάσεις, είναι τρεις· αν λίστα, λίστα· αν διόρθωση λαθών, όλα τα λάθη διορθώθηκαν και τίποτα άλλο δεν άλλαξε· αν τρίτο πρόσωπο, παντού τρίτο πρόσωπο.

**3. Η ανάγνωση.** Ερμήνευσε κάθε πρόταση μέσα σε όλα τα παραπάνω. Η αμφισημία δεν είναι λάθος. Όταν μια πρόταση επιδέχεται περισσότερες από μία αναγνώσεις, πάρε την πιο χαριτωμένη: συμφωνία με την πλησιέστερη λέξη, μια πτώση που κυβερνάται από νωρίτερα στην πρόταση, ένα συμπαγές ιδίωμα. Μια πρόταση είναι ανόητη μόνο όταν κάθε λογική ανάγνωση αποτυγχάνει.

**Τα ελληνικά προτιμούν τη συμπαγή μορφή.** Αναφορική πρόταση όπου αρκεί μια φράση, «ο οποίος» όπου εξυπηρετεί το «που», περιγραφή όπου υπάρχει μία λέξη — αυτές είναι οι αναλυτικές κατασκευές, το σημάδι του μεταφρασμένου κειμένου: ποτέ μην τις εισάγεις, και ποτέ μην καταδικάσεις μια συμπαγή μορφή επειδή είναι συμπαγής.
✗ «το κατάστημα το οποίο βρίσκεται στη γωνία» → ✓ «το μαγαζί στη γωνία»
✗ «η ώρα κατά την οποία φτάνει το τρένο» → ✓ «η ώρα που φτάνει το τρένο»
✗ «τα άτομα τα οποία εργάζονται στον δήμο» → ✓ «οι υπάλληλοι του δήμου»

**Ό,τι δεν επιβιώνει αυτής της κατανόησης, το διορθώνεις — και μόνο αυτό:**
- παράβαση της οδηγίας: λάθος πλήθος προτάσεων, λάθος μορφή, μήκος εκτός ορίου, πρόσωπο ή ύφος διαφορετικό από το ζητούμενο·
- απιστία προς το κείμενο: επινοημένα ή παραλειμμένα γεγονότα, ονόματα, ποσά, ημερομηνίες·
- συμφωνία, πτώση, άρθρο: «έφτιαξα τα Φεγγαροκουλούρες» → «τις Φεγγαροκουλούρες»· τελικό ν: «στην Σάμο» → «στη Σάμο»· έγκλιση: «ώσπου να το έβρισκε» → «ώσπου να το βρει»·
- λέξεις που δεν υπάρχουν στα ελληνικά· εκφράσεις μεταφρασμένες από τα αγγλικά που κανένας Έλληνας δεν θα έλεγε: «δυνατά χρώματα» → «έντονα χρώματα»· σπασμένες συνάψεις: «κέρδισε εμπειρία» → «απέκτησε εμπειρία»· μετέωροι ή ημιτελείς σχηματισμοί· μια πρόταση ανόητη όπως είναι γραμμένη·
- μανιέρες βοηθού: εισαγωγές ή επίλογοι του τύπου «Φυσικά!», «Ορίστε», «Ελπίζω να βοήθησα», «Αν χρειαστείς κάτι άλλο…», και κάθε αναφορά του βοηθού στον εαυτό του — αφαιρούνται·
- ξένο πλαίσιο: οτιδήποτε προϋποθέτει ξένη χώρα, νόμισμα, υπηρεσία ή συνήθεια χωρίς να το ζητά η οδηγία.

**Αλλαγές που δεν κάνεις.** Όταν και οι δύο μορφές είναι έγκυρες, δεν υπάρχει λάθος· και όπου δεν υπάρχει λάθος, δεν υπάρχει διόρθωση. Άφησε «κυκλοφορεί σε τρία χρώματα» (φυσικά ελληνικά, η ομοιότητα με τα αγγλικά δεν είναι λάθος)· άφησε «τα έκανε θάλασσα» (το ιδίωμα είναι ακριβώς τα καλά ελληνικά που ζητούνται)· άφησε «Ώρα για ύπνο.» (η φυσική έλλειψη είναι πλήρη ελληνικά)· άφησε τη μεταφορά (η εικόνα είναι το νόημα). Μια διόρθωση δεν είναι ποτέ πιο ρητή, πιο αναλυτική ή πιο ομοιόμορφη από αυτό που αντικαθιστά.

Πριν απαντήσεις, έλεγξε: κάθε αλλαγή διορθώνει ένα από τα παραπάνω· καμία αλλαγή δεν είναι προτίμηση· η οδηγία εκτελείται ακριβώς· το κείμενο δεν προδίδεται.

Επίστρεψε ΜΟΝΟ JSON: verdict ("ok" αν δεν άλλαξες τίποτα, "edited" για διορθώσεις, "rewrite" αν έπρεπε να ξαναγράψεις την απάντηση), edited_answer (η τελική απάντηση, ολόκληρη, ακόμη και αν είναι ίδια), changes (λίστα, μία φράση ανά αλλαγή, κενή αν verdict=ok).

ΚΕΙΜΕΝΟ:
{passage}

ΟΔΗΓΙΑ ΧΡΗΣΤΗ:
{instruction}

ΑΠΑΝΤΗΣΗ ΒΟΗΘΟΥ:
{answer}"""
def edit(r):
    prompt = BRIEF.format(passage=r['passage'], instruction=r['instruction'], answer=r['answer'])
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, prefix='grrwe_') as tmp: tmp.write(prompt); p = tmp.name
    out = tempfile.mktemp(suffix='.json', prefix='grrwe_out_'); t0 = time.time()
    try:
        res = subprocess.run(['codex', 'exec', '-m', MODEL, '-c', f'model_reasoning_effort={EFFORT}', '-c', f'service_tier={TIER}', '--skip-git-repo-check', '-c', 'features.code_mode_host=false',
                              '--sandbox', 'read-only', '--ephemeral', '--output-schema', SCHEMA, '-o', out, '-'], stdin=open(p), capture_output=True, text=True, timeout=900)
        txt = open(out).read() if os.path.exists(out) else res.stdout
        j = json.loads(txt[txt.index('{'):txt.rindex('}') + 1])
    except Exception as e: j = dict(verdict=None, edited_answer=None, changes=[], error=f'{type(e).__name__}')
    j['id'] = r['id']; j['seconds'] = round(time.time() - t0, 1)
    for f in (p, out):
        try: os.remove(f)
        except Exception: pass
    return j
rows = [json.loads(l) for l in open(IN)]; rows = [r for r in rows if r.get('passage') and r.get('answer')]
done = set()
if os.path.exists(OUT):
    for l in open(OUT): done.add(json.loads(l)['id'])
todo = [r for r in rows if r['id'] not in done]; print(f'{len(done)} done, {len(todo)} to go, {W} workers, {MODEL}/{EFFORT}', flush=True)
lock = threading.Lock(); t0 = time.time(); n = 0; stats = collections.Counter()
with open(OUT, 'a') as fh, cf.ThreadPoolExecutor(W) as ex:
    for j in ex.map(edit, todo):
        with lock:
            fh.write(json.dumps(j, ensure_ascii=False) + '\n'); fh.flush(); n += 1; stats[j.get('verdict') or 'fail'] += 1
            if n % 50 == 0 or n == len(todo): el = time.time() - t0; print(f'{n}/{len(todo)} {round(3600*n/el)} rows/h {dict(stats)} elapsed {round(el/60)} min', flush=True)
print('ALL DONE', flush=True)
