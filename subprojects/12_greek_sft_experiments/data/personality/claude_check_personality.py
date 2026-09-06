#!/usr/bin/env python3
"""Same Γ editing check as sol_check_personality.py, run by Claude (Opus 5 by default) through the Claude Code CLI, in batches.
Usage: python3 claude_check_personality.py <rows.jsonl> <ids.txt|all> <out.jsonl> <workers>   Env: CHECK_MODEL (claude-opus-5), CHECK_BATCH (5)"""
import json, sys, os, re, subprocess, time, threading, collections, concurrent.futures as cf, datetime
ROWS, IDS, OUT, W = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]); HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get('CHECK_MODEL', 'claude-opus-5'); BATCH = int(os.environ.get('CHECK_BATCH', '5'))
FACTS = {f['id']: f['fact_el'] for f in json.load(open(f'{HERE}/facts_greece.json'))}; IDENT = json.load(open(f'{HERE}/identity_facts.json'))['facts_el']
from personality_brief import BRIEF
def sheet(r):
    facts = [FACTS[i] for i in r.get('facts_used') or [] if i in FACTS]
    return '\n'.join('- ' + f for f in facts) if facts else '(φύλλο ταυτότητας)\n' + '\n'.join('- ' + f for f in IDENT)
def render(batch):
    parts = []
    for r in batch:
        conv = '\n\n'.join(f"[{m['role'].upper()}]\n{m['content']}" for m in r['messages'][:-1]); last = r['messages'][-1]['content']
        parts.append(f"===== ROW {r['id']} =====\nΦΥΛΛΟ ΓΕΓΟΝΟΤΩΝ:\n{sheet(r)}\n\nΣΥΝΟΜΙΛΙΑ ΩΣ ΤΩΡΑ:\n{conv}\n\nΤΕΛΕΥΤΑΙΑ ΑΠΑΝΤΗΣΗ ΒΟΗΘΟΥ (αυτή κρίνεις):\n{last}")
    return BRIEF + "\n\nΚρίνεις " + str(len(batch)) + " γραμμές, χωριστά η καθεμία (χωρίζονται με ===== ROW <id> =====). Μην χρησιμοποιήσεις εργαλεία. Επίστρεψε ΜΟΝΟ ένα JSON αντικείμενο {\"rows\": [{\"id\": ..., \"verdict\": ..., \"edited_last_answer\": ..., \"changes\": [...], \"fact_doubt\": ..., \"greekness\": 1-5}, ...]} με μία εγγραφή ανά γραμμή, ίδια ids.\n\n" + '\n\n'.join(parts)
lock = threading.Lock(); LOG = open(OUT + '.log', 'a'); tot = collections.Counter()
def call(batch):
    for attempt in range(3):
        t0 = time.time()
        try:
            res = subprocess.run(['claude', '-p', '--model', MODEL, '--output-format', 'json', '--max-turns', '3', '--disallowedTools', 'Bash,Read,Edit,Write,MultiEdit,Glob,Grep,WebFetch,WebSearch,Agent,Task,NotebookEdit,TodoWrite'], input=render(batch), capture_output=True, text=True, timeout=1500); j = json.loads(res.stdout)
        except Exception as e:
            with lock: LOG.write(f"{datetime.datetime.now():%H:%M} call error {type(e).__name__} attempt {attempt}\n"); LOG.flush()
            time.sleep(30); continue
        mu = j.get('modelUsage') or {}; txt = j.get('result') or ''
        with lock: tot['calls'] += 1; tot['cost'] += j.get('total_cost_usd') or 0; LOG.write(f"{datetime.datetime.now():%H:%M} rows={len(batch)} models={list(mu.keys())} cost={j.get('total_cost_usd')} {round(time.time()-t0)}s cumulative ${tot['cost']:.2f}\n"); LOG.flush()
        if not any(k.startswith('claude-opus') or k.startswith(MODEL) for k in mu): raise SystemExit(f'MODEL ASSERTION FAILED: {list(mu.keys())}')
        if not txt.strip(): time.sleep(20); continue
        try:
            obj = json.loads(txt[txt.index('{'):txt.rindex('}') + 1]); got = {str(x['id']): x for x in obj['rows']}
            return [dict(id=r['id'], category=r.get('category'), judge=MODEL, **{k: got[r['id']].get(k) for k in ('verdict', 'edited_last_answer', 'changes', 'fact_doubt', 'greekness')}) if r['id'] in got else dict(id=r['id'], category=r.get('category'), judge=MODEL, verdict=None, error='missing') for r in batch]
        except Exception as e:
            with lock: LOG.write(f"{datetime.datetime.now():%H:%M} parse fail {type(e).__name__}: {txt[:120]!r}\n"); LOG.flush()
    return [dict(id=r['id'], category=r.get('category'), judge=MODEL, verdict=None, error='failed') for r in batch]
rows = [json.loads(l) for l in open(ROWS)]
if IDS != 'all': want = set(open(IDS).read().split()); rows = [r for r in rows if r['id'] in want]
done = set()
if os.path.exists(OUT):
    for l in open(OUT):
        j = json.loads(l)
        if j.get('verdict'): done.add(j['id'])
todo = [r for r in rows if r['id'] not in done]; batches = [todo[k:k + BATCH] for k in range(0, len(todo), BATCH)]
print(f'{len(rows)} rows, {len(done)} done, {len(todo)} to check in {len(batches)} calls, {MODEL}', flush=True); t0 = time.time(); n = 0; stats = collections.Counter()
with open(OUT, 'a') as fh, cf.ThreadPoolExecutor(W) as ex:
    for res in ex.map(call, batches):
        for j in res: fh.write(json.dumps(j, ensure_ascii=False) + '\n'); stats[j.get('verdict') or 'fail'] += 1
        fh.flush(); n += len(res); print(f'{n}/{len(todo)} {round(3600*n/(time.time()-t0))} rows/h {dict(stats)} ${tot["cost"]:.2f}', flush=True)
print('ALL DONE', flush=True)
