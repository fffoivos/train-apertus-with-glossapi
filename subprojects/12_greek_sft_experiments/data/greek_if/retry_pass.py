#!/usr/bin/env python3
"""Retry pass: rows whose first answer failed a checkable constraint are asked again, with the failed constraints named as a hint
(the hint is generation-only; the stored prompt stays the original). Usage: python3 retry_pass.py <prompts.jsonl> <scores.jsonl> <retry_answers.jsonl>"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import run_pilot
from concurrent.futures import ThreadPoolExecutor
def main():
    prompts_path, scores_path, out_path = sys.argv[1:4]
    rows = {json.loads(l)['id']: json.loads(l) for l in open(prompts_path)}
    have = {json.loads(l)['id'] for l in open(out_path)} if os.path.exists(out_path) else set()
    todo = []
    for l in open(scores_path):
        s = json.loads(l)
        if s['all_pass'] is False and s['id'] not in have:
            r = rows[s['id']]; failed = [x['family'] for x in s['results'] if x['ok'] is False]
            texts = [c['text'] for c in r['constraints'] if c['family'] in failed]
            todo.append(dict(id=r['id'], prompt=r['prompt'] + '\n\n[Σημείωση για σένα, όχι μέρος του μηνύματος: σε προηγούμενη προσπάθεια ΔΕΝ τηρήθηκαν οι εξής οδηγίες, τήρησέ τες αυτή τη φορά με ακρίβεια: ' + ' | '.join(texts) + ']'))
    print(len(todo), 'rows to retry', flush=True)
    chunks = [todo[i:i + run_pilot.B] for i in range(0, len(todo), run_pilot.B)]
    with ThreadPoolExecutor(run_pilot.W) as pool:
        for _ in pool.map(lambda c: run_pilot.run_batch(c, out_path), chunks): pass
    print('retry done')
if __name__ == '__main__': main()
