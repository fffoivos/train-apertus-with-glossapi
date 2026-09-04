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
BRIEF = """Είσαι επιμελητής δεδομένων εκπαίδευσης για έναν ελληνικό βοηθό. Σου δίνεται ένα κείμενο, η οδηγία ενός Έλληνα χρήστη πάνω στο κείμενο, και η απάντηση του βοηθού. Έλεγξε την απάντηση και διόρθωσε ΜΟΝΟ ό,τι χρειάζεται:

1. Πιστότητα: η απάντηση δεν προσθέτει γεγονότα, ονόματα, ποσά ή ημερομηνίες που δεν υπάρχουν στο κείμενο (εκτός αν η οδηγία ζητά ανάπτυξη), και δεν παραλείπει ουσιώδη σημεία που ζητούνται.
2. Ακρίβεια εκτέλεσης: αν ζητούνται 3 προτάσεις, είναι 3· αν ζητείται λίστα, είναι λίστα· αν ζητείται SMS μέχρι 160 χαρακτήρες, τηρείται· αν ζητείται διόρθωση λαθών, όλα τα λάθη διορθώθηκαν και τίποτα άλλο δεν άλλαξε.
3. Γλώσσα: φυσικά, σωστά ελληνικά, με σωστό τονισμό και στίξη· ύφος που ταιριάζει στο ζητούμενο· χωρίς αγγλισμούς και χωρίς λέξεις που δεν χρησιμοποιεί ένας Έλληνας.
4. Χωρίς μανιέρες: καμία εισαγωγή ή επίλογος του τύπου «Φυσικά!», «Ορίστε», «Ελπίζω να βοήθησα», καμία αναφορά του βοηθού στον εαυτό του.
5. Ελληνικό πλαίσιο: τίποτα που να προϋποθέτει ξένη χώρα, νόμισμα ή υπηρεσία.

Επίστρεψε ΜΟΝΟ JSON: verdict ("ok" αν δεν άλλαξες τίποτα, "edited" για μικρές διορθώσεις, "rewrite" αν έπρεπε να ξαναγράψεις), edited_answer (η τελική απάντηση, ολόκληρη, ακόμη και αν είναι ίδια), changes (λίστα με τις αλλαγές, μία φράση η καθεμία, κενή αν verdict=ok).

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
