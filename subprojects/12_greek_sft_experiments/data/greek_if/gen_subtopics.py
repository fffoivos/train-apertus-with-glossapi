#!/usr/bin/env python3
"""Scale the subject tree: Sol proposes concrete subtopics per domain (default 50), merged with the hand-written ones into subtopics.json,
which gen_prompts.py loads automatically. Usage: python3 gen_subtopics.py [per_domain=50]   env: GEN_MODEL GEN_EFFORT"""
import json, os, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ['GREEK_IF_NO_SUBTOPICS'] = '1'; from gen_prompts import DOMAINS
MODEL = os.environ.get('GEN_MODEL', 'gpt-5.6-sol'); EFFORT = os.environ.get('GEN_EFFORT', 'medium'); SCHEMA = os.path.join(HERE, 'subtopics_schema.json'); TMP = os.environ.get('CLAUDE_JOB_DIR', tempfile.gettempdir()) + '/tmp'; os.makedirs(TMP, exist_ok=True)
OUT = os.path.join(HERE, 'subtopics.json'); N = int(sys.argv[1]) if len(sys.argv) > 1 else 50
BRIEF = ('Για τον τομέα «{dom}» (παραδείγματα υποθεμάτων: {ex}) γράψε {n} ΝΕΑ, συγκεκριμένα υποθέματα για τα οποία ένας χρήστης στην Ελλάδα θα ρωτούσε έναν βοηθό: πρακτικές περιστάσεις, διαδικασίες, αποφάσεις, '
         'προβλήματα, γνώσεις, τοπικές ιδιαιτερότητες (νησιά, επαρχία, Αθήνα, Θεσσαλονίκη), όλες τις ηλικίες. Κάθε υποθέμα 2–6 λέξεις, χωρίς επικάλυψη με τα παραδείγματα και μεταξύ τους, χωρίς αρίθμηση. Επίστρεψε JSON {{"subtopics":[…]}}.')
def one(dom):
    out = tempfile.NamedTemporaryFile('w', suffix='.json', dir=TMP, delete=False).name
    for attempt in range(3):
        try:
            subprocess.run(['codex', 'exec', '-m', MODEL, '-c', f'model_reasoning_effort={EFFORT}', '-c', 'project_doc_max_bytes=0', '-c', 'features.code_mode_host=false', '--skip-git-repo-check', '--sandbox', 'read-only', '--ephemeral', '--output-schema', SCHEMA, '-o', out, '-'],
                           input=BRIEF.format(dom=dom, ex=', '.join(DOMAINS[dom]), n=N), capture_output=True, text=True, timeout=900, cwd=TMP)
            subs = [s.strip(' .') for s in json.load(open(out))['subtopics'] if s.strip()]
            if len(subs) < N * 0.6: raise ValueError(f'{len(subs)} subtopics')
            return dom, subs
        except Exception as e: print('retry', attempt, dom, type(e).__name__, str(e)[:100], flush=True)
    return dom, []
def main():
    tree = json.load(open(OUT)) if os.path.exists(OUT) else {}
    todo = [d for d in DOMAINS if len(tree.get(d, [])) < len(DOMAINS[d]) + N * 0.6]
    print(len(todo), 'domains to expand with', MODEL, flush=True)
    with ThreadPoolExecutor(16) as pool:
        for dom, subs in pool.map(one, todo):
            seen = set(); merged = []
            for s in list(DOMAINS[dom]) + subs:
                k = s.lower()
                if k not in seen: seen.add(k); merged.append(s)
            tree[dom] = merged
    json.dump(tree, open(OUT, 'w'), ensure_ascii=False, indent=1)
    print({d: len(v) for d, v in tree.items()}, 'total', sum(len(v) for v in tree.values()))
if __name__ == '__main__': main()
