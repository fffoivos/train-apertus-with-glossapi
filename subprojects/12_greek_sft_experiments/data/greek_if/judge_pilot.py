#!/usr/bin/env python3
"""E7: Opus judges the non-checkable style/situation constraints (no_adjectives, register_katharevousa, child_register) pass/fail per constraint.
Usage: python3 judge_pilot.py <answers.jsonl> <prompts.jsonl> <judgements.jsonl>   env: JUDGE_MODEL (opus) WORKERS (3) PAUSE_AT (62)
Uses the usage-gated Claude lane (data/personality/v2/claude_call.py): model assertion from modelUsage, pause above PAUSE_AT% of the 5-hour window."""
import json, os, sys, threading
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'personality', 'v2')); import claude_call
MODEL = os.environ.get('JUDGE_MODEL', 'opus'); W = int(os.environ.get('WORKERS', '3')); LOG = os.path.join(HERE, 'pilot', 'judge_usage.log')
BRIEF = ('Είσαι αυστηρός κριτής τήρησης οδηγιών. Δίνεται ένα μήνυμα χρήστη στα ελληνικά και η απάντηση ενός βοηθού. Για ΚΑΘΕ οδηγία της λίστας απόφασε αν η απάντηση την τηρεί πλήρως (pass) ή όχι (fail), '
         'με μία φράση αιτιολόγησης που δείχνει το σημείο της απάντησης που κρίνει. Κρίνε μόνο την τήρηση της οδηγίας, όχι την ποιότητα. Επίστρεψε ΜΟΝΟ JSON: {{"verdicts":[{{"family":…,"pass":true|false,"why":…}}]}}.\n\n'
         'Οδηγίες προς έλεγχο:\n{cons}\n\n=== Μήνυμα χρήστη ===\n{prompt}\n\n=== Απάντηση ===\n{answer}')
lock = threading.Lock()
def judge(r, ans, out_path):
    cons = '\n'.join(f'- {c["family"]}: {c["text"]}' for c in r['constraints'])
    j = claude_call.call(BRIEF.format(cons=cons, prompt=r['prompt'], answer=ans), MODEL, LOG, label=r['id'])
    if not j or 'verdicts' not in j: print('no verdict', r['id'], flush=True); return
    with lock, open(out_path, 'a') as f: f.write(json.dumps(dict(id=r['id'], verdicts=j['verdicts'], judge=MODEL), ensure_ascii=False) + '\n')
def main():
    ans_path, prompts_path, out_path = sys.argv[1:4]
    ans = {json.loads(l)['id']: json.loads(l)['answer'] for l in open(ans_path)}; have = {json.loads(l)['id'] for l in open(out_path)} if os.path.exists(out_path) else set()
    rows = [json.loads(l) for l in open(prompts_path)]; todo = [r for r in rows if r['id'] in ans and r['id'] not in have]; print(len(todo), 'to judge with', MODEL, flush=True)
    with ThreadPoolExecutor(W) as pool:
        for _ in pool.map(lambda r: judge(r, ans[r['id']], out_path), todo): pass
    import collections; per = collections.defaultdict(list)
    for l in open(out_path):
        for v in json.loads(l)['verdicts']: per[v['family']].append(bool(v['pass']))
    print({k: (len(v), round(sum(v) / len(v), 3)) for k, v in per.items()})
if __name__ == '__main__': main()
