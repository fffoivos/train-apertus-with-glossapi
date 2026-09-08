#!/usr/bin/env python3
"""Request bank: Sol writes natural Greek user requests per (domain, subtopic) × 12 forms × personas, WITHOUT constraints (added later by gen_prompts.py --requests).
This is the "authored" arm of the request-variability experiment (E0): templates vs model-written requests, same cells.
Usage: python3 gen_requests.py <bank.jsonl> [per_form=2]   env: GEN_MODEL GEN_EFFORT WORKERS(24)"""
import json, os, random, subprocess, sys, tempfile, threading, time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from gen_prompts import DOMAINS, FORMS, PERSONAS
MODEL = os.environ.get('GEN_MODEL', 'gpt-5.6-sol'); EFFORT = os.environ.get('GEN_EFFORT', 'medium'); W = int(os.environ.get('WORKERS', '24'))
HERE = os.path.dirname(os.path.abspath(__file__)); SCHEMA = os.path.join(HERE, 'requests_schema.json'); TMP = os.environ.get('CLAUDE_JOB_DIR', tempfile.gettempdir()) + '/tmp'; os.makedirs(TMP, exist_ok=True)
FORM_EL = {'quick_fact': 'σύντομη ερώτηση για ένα γεγονός ή έναν αριθμό', 'explanation': 'ζητά εξήγηση του πώς ή του γιατί', 'howto': 'ζητά οδηγίες βήμα προς βήμα', 'comparison': 'ζητά σύγκριση δύο συγκεκριμένων επιλογών που κατονομάζει',
           'opinion': 'ζητά γνώμη με επιχειρήματα', 'creative': 'ζητά δημιουργικό κείμενο (ποίημα, ιστορία, διαφήμιση, ευχή, στίχοι)', 'rewrite': 'δίνει ένα δικό του κείμενο 50–120 λέξεων ΜΕΣΑ στο μήνυμα και ζητά να ξαναγραφτεί ή να διορθωθεί',
           'summarise': 'δίνει ένα κείμενο 80–150 λέξεων ΜΕΣΑ στο μήνυμα και ζητά περίληψη', 'translate': 'δίνει ένα ελληνικό κείμενο 40–100 λέξεων ΜΕΣΑ στο μήνυμα και ζητά μετάφραση στα αγγλικά',
           'list': 'ζητά λίστα ή κατηγοριοποίηση', 'planning': 'ζητά πλάνο ή πρόγραμμα με συγκεκριμένες παραμέτρους (ημέρες, προϋπολογισμό, άτομα)', 'correction': 'διατυπώνει μια λανθασμένη πεποίθηση και ρωτά αν ισχύει'}
BRIEF = ('Γράψε {n} ρεαλιστικά μηνύματα χρηστών προς έναν ελληνικό βοηθό τεχνητής νοημοσύνης. Θέμα: «{sub}» (τομέας: {dom}). Κάθε μήνυμα αντιστοιχεί σε μία γραμμή του παρακάτω πίνακα (μορφή + πρόσωπο που γράφει) και πρέπει:\n'
         '- να είναι αυτόνομο και συγκεκριμένο (πραγματική περίσταση, λεπτομέρειες, ονόματα τόπων ή ποσά όπου ταιριάζει), όχι γενικό·\n- να ακολουθεί τη ΜΟΡΦΗ που δίνεται και να γράφεται όπως θα το έγραφε το ΠΡΟΣΩΠΟ (ύφος, γνώσεις, ορθογραφικές συνήθειες: ο μαθητής χωρίς τόνους γράφει χωρίς τόνους, ο ομογενής σε greeklish γράφει greeklish, ο συνταξιούχος με πληθυντικό ευγενείας)·\n'
         '- να ΜΗΝ περιέχει καμία οδηγία μορφοποίησης, μήκους ή ύφους της απάντησης (αυτές προστίθενται αργότερα)·\n- να διαφέρει από τα υπόλοιπα σε περίσταση και διατύπωση· κανένα κοινό αρχικό μοτίβο.\n'
         'Για τις μορφές rewrite/summarise/translate το κείμενο του χρήστη μπαίνει μέσα στο μήνυμα, γραμμένο από σένα, αληθοφανές.\nΕπίστρεψε JSON {{"requests":[{{"form":…,"persona":…,"text":…}}]}} με ακριβώς {n} στοιχεία, ίδια σειρά με τον πίνακα.\n\nΠίνακας:\n{table}')
lock = threading.Lock()
def cell(dom, sub, per_form, seed, out_path):
    rng = random.Random(seed); spec = [(f, rng.choice(PERSONAS)) for f in FORMS for _ in range(per_form)]; rng.shuffle(spec)
    table = '\n'.join(f'{i+1}. μορφή: {f} ({FORM_EL[f]}) | πρόσωπο: {p[0]}' for i, (f, p) in enumerate(spec))
    prompt = BRIEF.format(n=len(spec), sub=sub, dom=dom, table=table); out = tempfile.NamedTemporaryFile('w', suffix='.json', dir=TMP, delete=False).name
    for attempt in range(3):
        try:
            r = subprocess.run(['codex', 'exec', '-m', MODEL, '-c', f'model_reasoning_effort={EFFORT}', '-c', 'project_doc_max_bytes=0', '-c', 'features.code_mode_host=false', '--skip-git-repo-check', '--sandbox', 'read-only', '--ephemeral', '--output-schema', SCHEMA, '-o', out, '-'],
                               input=prompt, capture_output=True, text=True, timeout=1500, cwd=TMP)
            got = json.load(open(out))['requests']
            if len(got) != len(spec): raise ValueError(f'{len(got)} != {len(spec)}')
            with lock, open(out_path, 'a') as f:
                for (fm, p), g in zip(spec, got): f.write(json.dumps(dict(domain=dom, subtopic=sub, form=fm, persona=p[0], persona_style=p[1], text=g['text'], model=MODEL), ensure_ascii=False) + '\n')
            return len(got)
        except Exception as e:
            with lock: print('retry', attempt, dom, sub, type(e).__name__, str(e)[:120], flush=True)
            time.sleep(15 * (attempt + 1))
    print('FAILED', dom, sub, flush=True); return 0
def main():
    out_path = sys.argv[1]; per_form = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    have = {(json.loads(l)['domain'], json.loads(l)['subtopic']) for l in open(out_path)} if os.path.exists(out_path) else set()
    cells = [(d, s) for d, subs in DOMAINS.items() for s in subs if (d, s) not in have]; print(len(cells), 'cells to author,', len(have), 'done,', MODEL, EFFORT, W, 'workers', flush=True); t0 = time.time()
    with ThreadPoolExecutor(W) as pool: n = sum(pool.map(lambda c: cell(c[0], c[1], per_form, sum(map(ord, c[0] + c[1])), out_path), cells))
    print(n, 'requests in', f'{(time.time()-t0)/60:.1f} min')
if __name__ == '__main__': main()
