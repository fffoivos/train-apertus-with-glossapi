#!/usr/bin/env python3
"""Second judge for E7 (cross-vendor): Sol judges the non-checkable constraints in batches of 8, same brief as judge_pilot.py. Agreement with Opus stands in for the human read.
Usage: python3 judge_sol.py <answers.jsonl> <prompts.jsonl> <judgements.jsonl>"""
import json, os, subprocess, sys, tempfile, threading
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); SCHEMA = os.path.join(HERE, 'verdicts_schema.json'); TMP = os.environ.get('CLAUDE_JOB_DIR', tempfile.gettempdir()) + '/tmp'; MODEL = os.environ.get('GEN_MODEL', 'gpt-5.6-sol')
HEAD = ('Είσαι αυστηρός κριτής τήρησης οδηγιών. Για καθένα από τα παρακάτω {n} ζεύγη (μήνυμα χρήστη, απάντηση βοηθού) και για ΚΑΘΕ οδηγία της λίστας του, απόφασε αν η απάντηση την τηρεί πλήρως (pass) ή όχι (fail), με μία φράση αιτιολόγησης. '
        'Κρίνε μόνο την τήρηση της οδηγίας, όχι την ποιότητα. Επίστρεψε JSON {{"items":[{{"id":…,"verdicts":[{{"family":…,"pass":…,"why":…}}]}}]}} με ακριβώς τα {n} ids.\n\n')
lock = threading.Lock()
def batch(rows, ans, out_path):
    body = '\n\n'.join(f'=== id: {r["id"]} ===\nΟδηγίες:\n' + '\n'.join(f'- {c["family"]}: {c["text"]}' for c in r['constraints']) + f'\n--- Μήνυμα χρήστη ---\n{r["prompt"]}\n--- Απάντηση ---\n{ans[r["id"]]}' for r in rows)
    out = tempfile.NamedTemporaryFile('w', suffix='.json', dir=TMP, delete=False).name
    for attempt in range(3):
        try:
            subprocess.run(['codex', 'exec', '-m', MODEL, '-c', 'model_reasoning_effort=medium', '-c', 'project_doc_max_bytes=0', '-c', 'features.code_mode_host=false', '--skip-git-repo-check', '--sandbox', 'read-only', '--ephemeral', '--output-schema', SCHEMA, '-o', out, '-'],
                           input=HEAD.format(n=len(rows)) + body, capture_output=True, text=True, timeout=1500, cwd=TMP)
            items = {it['id']: it['verdicts'] for it in json.load(open(out))['items']}
            if set(items) != {r['id'] for r in rows}: raise ValueError('id mismatch')
            with lock, open(out_path, 'a') as f:
                for r in rows: f.write(json.dumps(dict(id=r['id'], verdicts=items[r['id']], judge=MODEL), ensure_ascii=False) + '\n')
            return
        except Exception as e: print('retry', attempt, type(e).__name__, str(e)[:100], flush=True)
def main():
    ans_path, prompts_path, out_path = sys.argv[1:4]
    ans = {json.loads(l)['id']: json.loads(l)['answer'] for l in open(ans_path)}; have = {json.loads(l)['id'] for l in open(out_path)} if os.path.exists(out_path) else set()
    todo = [r for r in (json.loads(l) for l in open(prompts_path)) if r['id'] in ans and r['id'] not in have]; chunks = [todo[i:i + 8] for i in range(0, len(todo), 8)]
    with ThreadPoolExecutor(24) as pool:
        for _ in pool.map(lambda c: batch(c, ans, out_path), chunks): pass
    print('judged', len(todo))
if __name__ == '__main__': main()
