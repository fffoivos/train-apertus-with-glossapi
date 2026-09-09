#!/usr/bin/env python3
"""Sol pilot runner: answers Greek IF prompts in batches with codex exec (schema-enforced JSON), resumable by id.
Usage: python3 run_pilot.py <answers.jsonl> <prompts.jsonl> [more prompts.jsonl ...]   env: GEN_MODEL (gpt-5.6-sol) GEN_EFFORT (medium) WORKERS (24) BATCH (8)
The model sees ONLY the user prompt (never the structured constraint list): the pilot measures first-try yield."""
import json, os, subprocess, sys, tempfile, threading, time
from concurrent.futures import ThreadPoolExecutor
MODEL = os.environ.get('GEN_MODEL', 'gpt-5.6-sol'); EFFORT = os.environ.get('GEN_EFFORT', 'medium'); W = int(os.environ.get('WORKERS', '24')); B = int(os.environ.get('BATCH', '8'))
HERE = os.path.dirname(os.path.abspath(__file__)); SCHEMA = os.path.join(HERE, 'answers_schema.json'); TMP = os.environ.get('CLAUDE_JOB_DIR', tempfile.gettempdir()) + '/tmp'; os.makedirs(TMP, exist_ok=True)
HEAD = ('Είσαι το Ελληνικό Apertus, ένας βοηθός που απαντά στα ελληνικά. Παρακάτω υπάρχουν {n} ανεξάρτητα μηνύματα χρηστών, το καθένα με ένα id. Απάντησε σε καθένα ξεχωριστά, όπως θα απαντούσε ο βοηθός στον χρήστη. '
        'Απάντησε στο ουσιαστικό αίτημα ΚΑΙ τήρησε ακριβώς όλες τις εφαρμόσιμες οδηγίες μορφής, μήκους, γλώσσας, ύφους και περιεχομένου που δίνει ο χρήστης, ακόμη κι αν φαίνονται ασυνήθιστες. Γράφε φυσικά, χωρίς περιττές επαναλήψεις και χωρίς γέμισμα για να καλύψεις έναν περιορισμό. '
        'Σε περίληψη, μετάφραση ή αναδιατύπωση διατήρησε τα δεδομένα και το νόημα του αρχικού κειμένου. Μην επινοείς ημερομηνίες, ποσά, πηγές ή ισχυρισμούς επικαιρότητας για να καλύψεις έναν περιορισμό· αν ζητείται ημερομηνία ή ποσό που δεν δίνεται, χρησιμοποίησε ρητά υποθετικό παράδειγμα ή ζήτησε σύντομα το στοιχείο. '
        'Ενσωμάτωσε τις υποχρεωτικές λέξεις με ουσιαστικό τρόπο. Αν δύο οδηγίες είναι πραγματικά ασύμβατες, πες το σε μία πρόταση και τήρησε τις υπόλοιπες. Απάντησε σε φυσικά μονοτονικά ελληνικά ανεξάρτητα από την επιφάνεια του μηνύματος (greeklish, χωρίς τόνους), εκτός αν ζητείται άλλη γλώσσα, γραφή ή ακριβές παράθεμα. '
        'Μην προσθέτεις εισαγωγές, σημειώσεις ή σχόλια εκτός απάντησης. Επίστρεψε JSON {{"answers":[{{"id":…,"answer":…}}]}} με ακριβώς τα {n} ids.\n\n')   # head revised after the astra review of v1 (faithful content, no invented facts, natural Greek)
lock = threading.Lock(); done = 0; t0 = time.time()
def run_batch(rows, out_path):
    global done
    prompt = HEAD.format(n=len(rows)) + '\n\n'.join(f'=== id: {r["id"]} ===\n{r["prompt"]}' for r in rows)
    out = tempfile.NamedTemporaryFile('w', suffix='.json', dir=TMP, delete=False).name
    for attempt in range(3):
        try:
            r = subprocess.run(['codex', 'exec', '-m', MODEL, '-c', f'model_reasoning_effort={EFFORT}', '-c', 'project_doc_max_bytes=0', '-c', 'features.code_mode_host=false',
                                '--skip-git-repo-check', '--sandbox', 'read-only', '--ephemeral', '--output-schema', SCHEMA, '-o', out, '-'],
                               input=prompt, capture_output=True, text=True, timeout=1500, cwd=TMP)
            j = json.load(open(out)); got = {a['id']: a['answer'] for a in j['answers']}
            if set(got) != {r['id'] for r in rows}: raise ValueError(f'id mismatch {len(got)}/{len(rows)}')
            with lock:
                with open(out_path, 'a') as f:
                    for r in rows: f.write(json.dumps(dict(id=r['id'], answer=got[r['id']], model=MODEL, effort=EFFORT), ensure_ascii=False) + '\n')
                done += len(rows); el = time.time() - t0
                if done % 40 < len(rows): print(f'{done} rows in {el/60:.1f} min ({done/el*3600:.0f} rows/h)', flush=True)
            return
        except Exception as e:
            with lock: print('retry', attempt, type(e).__name__, str(e)[:160], (r.stderr[-200:] if 'r' in dir() and r.stderr else ''), flush=True)
            time.sleep(15 * (attempt + 1))
    with lock: print('FAILED batch', [r['id'] for r in rows], flush=True)
def main():
    out_path, files = sys.argv[1], sys.argv[2:]
    have = {json.loads(l)['id'] for l in open(out_path)} if os.path.exists(out_path) else set()
    rows = [json.loads(l) for fn in files for l in open(fn)]; todo = [r for r in rows if r['id'] not in have]
    print(f'{len(rows)} prompts, {len(have)} answered, {len(todo)} to do, model {MODEL} effort {EFFORT}, {W} workers × {B}', flush=True)
    chunks = [todo[i:i + B] for i in range(0, len(todo), B)]
    with ThreadPoolExecutor(W) as pool:
        for _ in pool.map(lambda c: run_batch(c, out_path), chunks): pass
    print('done', done, 'rows in', f'{(time.time()-t0)/60:.1f} min')
if __name__ == '__main__': main()
