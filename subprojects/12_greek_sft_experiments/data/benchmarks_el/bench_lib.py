#!/usr/bin/env python3
"""Shared helpers for the Greek benchmark builds (2026-09-10): one Sol JSON call with retries, a resumable parallel runner,
the Codex weekly-limit reading (to cost every stage), and the common translation rules."""
from __future__ import annotations
import glob, json, os, re, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'math')); sys.path.insert(0, os.path.join(HERE, '..', 'greek_if'))
import mathlib as M
lock = threading.Lock()
MAX_WORKERS = 100


def sol_json(prompt: str, schema: str, model: str = 'gpt-5.6-sol', effort: str = 'medium', timeout: int = 1500, tries: int = 3) -> dict | None:
    for t in range(tries):
        try: return M.codex_json(prompt, schema, model, effort, timeout=timeout)
        except Exception as e: print('retry', t, type(e).__name__, str(e)[:100], flush=True); time.sleep(5 * (t + 1))
    return None


def codex_limit() -> float | None:
    """The weekly Codex window from the newest rollout (used_percent of limit_id 'codex', window 10080 min)."""
    files = sorted(glob.glob(os.path.expanduser('~/.codex/sessions/*/*/*/rollout-*.jsonl')), key=os.path.getmtime)[-3:]
    vals = []
    for f in files:
        vals += re.findall(r'"limit_id":"codex","limit_name":null,"primary":\{"used_percent":([0-9.]+),"window_minutes":10080', open(f, errors='ignore').read())
    return float(vals[-1]) if vals else None


def log_cost(stage: str, before: float | None, after: float | None, n: int):
    line = f"{time.strftime('%Y-%m-%d %H:%M')} {stage}: n={n} codex {before} -> {after} (delta {None if before is None or after is None else round(after - before, 1)})"
    with open(os.path.join(HERE, 'cost_ledger.log'), 'a') as f: f.write(line + '\n')
    print(line, flush=True)


def _deduplicate_inputs(items: list, key: str) -> tuple[list, int]:
    """Collapse structurally identical duplicates and reject one ID bound to different input."""
    unique, seen, collapsed = [], {}, 0
    for item in items:
        item_id = item[key]
        encoded = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
        if item_id in seen:
            if seen[item_id] != encoded:
                raise ValueError(f'conflicting duplicate input {key}={item_id!r}')
            collapsed += 1
        else:
            seen[item_id] = encoded; unique.append(item)
    return unique, collapsed


def run_jobs(items: list, fn, out_path: str, key: str = 'id', workers: int | None = None, stage: str = ''):
    """Resumable: rows already in out_path (by key) are skipped; fn(item) returns a dict (with key) or None."""
    workers = int(os.environ.get('WORKERS', '24')) if workers is None else int(workers)
    if not 1 <= workers <= MAX_WORKERS:
        raise ValueError(f'workers must be between 1 and {MAX_WORKERS}, got {workers}')
    items, collapsed = _deduplicate_inputs(items, key)
    have = set()
    if os.path.exists(out_path):
        with open(out_path, encoding='utf-8') as existing:
            for l in existing:
                try: have.add(json.loads(l)[key])
                except Exception: pass
    todo = [x for x in items if x[key] not in have]; print(f'{stage}: {len(items)} unique items, {collapsed} identical duplicates collapsed, {len(todo)} to do, {workers} workers', flush=True)
    before = codex_limit()
    def one(x):
        r = fn(x)
        if r is not None:
            with lock, open(out_path, 'a') as f: f.write(json.dumps(r, ensure_ascii=False) + '\n')
        return r
    with ThreadPoolExecutor(workers) as pool: done = [r for r in pool.map(one, todo) if r is not None]
    log_cost(stage or out_path, before, codex_limit(), len(done)); return done


def load(path): return [json.loads(l) for l in open(path)]


RULES_EL = ("Μεταφράζεις υλικό ΑΞΙΟΛΟΓΗΣΗΣ γλωσσικών μοντέλων από τα αγγλικά σε φυσικά, σύγχρονα ελληνικά (μονοτονικό). Κανόνες: "
            "(1) πιστή απόδοση του νοήματος και της δυσκολίας, όχι ελεύθερη προσαρμογή· ό,τι είναι ασαφές ή δύσκολο στο πρωτότυπο μένει εξίσου ασαφές ή δύσκολο· "
            "(2) διατηρείς ΟΛΟΥΣ τους αριθμούς, μονάδες, ημερομηνίες, κωδικούς, ονόματα προϊόντων, διευθύνσεις URL, κώδικα και μαθηματικά όπως είναι· "
            "(3) κύρια ονόματα: κρατάς τη μορφή του πρωτοτύπου ή την καθιερωμένη ελληνική απόδοση (Νέα Υόρκη, Παρίσι) και την ίδια επιλογή ΠΑΝΤΟΥ μέσα στο ίδιο κείμενο· "
            "(4) δεν προσθέτεις, δεν αφαιρείς, δεν εξηγείς, δεν διορθώνεις λάθη του πρωτοτύπου· "
            "(5) ύφος και μητρώο όπως το πρωτότυπο (ανεπίσημο μένει ανεπίσημο, ενικός/πληθυντικός ευγενείας κατά περίπτωση)· "
            "(6) η γλώσσα να είναι αυτή που θα έγραφε φυσικός ομιλητής, όχι μεταφρασμένη σύνταξη.")
