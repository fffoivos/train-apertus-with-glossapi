#!/usr/bin/env python3
"""DATA_TODO 29 / launch gate: re-run every conversation-suite lane check on the FINAL rows (after the Greek editor pass and assembly), from
the rows' own fields, without any model call; write a manifest (lane, kind, attempted, verified at generation, verified now, agreement,
content hash) and a rows_final.jsonl holding only the rows that pass now.
Usage: python3 reverify_suite.py <rows.jsonl> <out_dir>      (rows: v2/rows_all.jsonl or v2/edited/rows_edited.jsonl)"""
import json, re, sys, os, hashlib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import gen_suite as G; C = G.C
NUM_WORDS = ['', 'ένα', 'δύο', 'τρία', 'τέσσερα', 'πέντε', 'έξι', 'επτά', 'οκτώ']
def norm(s): return re.sub(r'\s+', ' ', s.lower()).strip()
def turns(r): return r.get('turns') or r.get('messages')
RAW = {}
def F(r, k, d=None):
    """row field at top level (lane files), under meta (assembled/edited rows), or from the raw lane file joined by id (params, must, facts are dropped at assembly)"""
    v = r.get(k)
    if v is None: v = (r.get('meta') or {}).get(k)
    if v is None: v = (RAW.get(r['id']) or {}).get(k, d)
    return v
def s1(r):
    t = turns(r); users = [m['content'] for m in t if m['role'] == 'user'][:-1]; a = t[-1]['content']; k = F(r, 'kind'); must = F(r, 'must') or ''
    if 'δεν έχω πρόσβαση' in a or 'δεν βλέπω' in a: return False
    if k == 'first': return norm(users[0])[:40] in norm(a)
    if k == 'quote_n': return must.strip().lower()[:40] in a.lower()
    if k == 'count': n = len(users); return re.search(rf'\b{n}\b|\b{NUM_WORDS[n] if n < len(NUM_WORDS) else "@@"}\b', a) is not None and not re.search(rf'\b{n + 1}\b', a)
    if k == 'list': return bool(G.s1_list_ok(a, users))
    if k == 'said_about':
        src = next((m['content'] for m in t if m['role'] == 'assistant' and m['content'].startswith(must[:60])), None)
        return bool(src) and any(norm(s) in norm(a) for s in C.sentences(src)[:2])
    return False
def s2(r):
    t = turns(r); pid = F(r, 'kind'); instr, chk = G.PERSIST[pid]
    idx = next((i for i, m in enumerate(t) if m['role'] == 'user' and m['content'].strip() == instr.strip()), None)
    if idx is None: return False
    later = []
    for m in t[idx + 1:]:
        if m['role'] == 'user' and m['content'].strip() in {x.strip() for x in G.REVOKE}: break
        if m['role'] == 'assistant': later.append(m['content'])
    return bool(later) and len(C.words(later[0])) >= 2 and all(chk(a) for a in later)
def s3(r):
    t = turns(r); op = F(r, 'kind'); p = F(r, 'params') or {}; old = t[1]['content']; new = t[-1]['content']
    return bool(G.EDITS[op][1](old, new, p)) and bool(G.invariants_ok(old, new, op, p))
def s3c(r):
    t = turns(r); p = F(r, 'params') or {}; w = p.get('w', ''); order = p.get('order', 'without_then_shorter'); old, a1, a2 = t[1]['content'], t[3]['content'], t[5]['content']; wl = w.lower()
    n0, n1, n2 = len(C.words(old)), len(C.words(a1)), len(C.words(a2))
    if order == 'without_then_shorter': return wl not in a1.lower() and wl not in a2.lower() and 0.35 * n1 <= n2 <= 0.65 * n1 and n2 >= 8 and G.invariants_ok(old, a1, 'without', dict(w=w)) and G.invariants_ok(a1, a2, 'shorter', {})
    return 0.35 * n0 <= n1 <= 0.65 * n0 and n1 >= 8 and wl not in a2.lower() and 0.75 * n1 <= n2 <= 1.1 * n1 + 2 and G.invariants_ok(old, a1, 'shorter', {}) and G.invariants_ok(a1, a2, 'without', dict(w=w))
def s4(r):
    t = turns(r); tic = F(r, 'kind'); key = norm(tic.rstrip('.;'))
    ctx = [m for m in t[:4] if m['role'] == 'assistant']
    if len(ctx) != 2 or not all(key in norm(m['content']) and m.get('train') is False for m in ctx): return False   # planted context intact and masked
    idx = next((i for i, m in enumerate(t) if m['role'] == 'user' and key[:12] in norm(m['content']) and i >= 4), None)
    if idx is None: return False
    later = [m['content'] for m in t[idx + 1:] if m['role'] == 'assistant']
    return bool(later) and len(C.words(later[0])) >= 2 and all(key not in norm(a) for a in later)
def s5m(r):
    t = turns(r); f = F(r, 'facts') or {}; a = t[-1]['content']; nums = [int(x.replace('.', '')) for x in re.findall(r'\b\d{2,4}\b', a)]
    keys = G.LIMKEY.get(f.get('limit'), []) if hasattr(G, 'LIMKEY') else None
    if keys is None:   # LIMKEY is local to the lane: rebuild the same table from the lane source
        src = open(G.__file__).read(); m = re.search(r"LIMKEY = (\{.*?\})\n", src, re.S); keys = eval(m.group(1)).get(f.get('limit'), []) if m else []
    return f.get('city', '@@').lower()[:4] in a.lower() and not any(n > f.get('budget', 10**9) for n in nums) and any(k.lower() in a.lower() for k in keys)
CHECK = {'S1': s1, 'S2': s2, 'S3': s3, 'S3c': s3c, 'S4': s4, 'S5m': s5m}
src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
rows = [json.loads(l) for l in open(src)]
import glob as _glob
for _f in _glob.glob(os.path.join(os.path.dirname(os.path.abspath(src)).split('/edited')[0].split('/reverify')[0], 'S*.jsonl')):
    for _l in open(_f):
        _r = json.loads(_l); RAW[_r['id']] = _r
print(f'raw lane rows joined: {len(RAW)}', file=sys.stderr); man = collections.defaultdict(lambda: collections.Counter()); final = []; hashes = collections.defaultdict(hashlib.sha256); errs = {}
for r in rows:
    lane = r.get('lane') or r.get('bucket') or r['id'].split('_')[0]; r['lane'] = lane
    try: ok = bool(CHECK[lane](r))
    except Exception as e:
        ok = False; man[lane]['check_error'] += 1
        if 'first_error' not in errs.get(lane, {}): errs.setdefault(lane, {})['first_error'] = f'{type(e).__name__}: {str(e)[:160]} (row {r["id"]})'
    empty = any(m['role'] == 'assistant' and m.get('train', True) and not m['content'].strip() for m in turns(r))
    ok = ok and not empty
    m = man[lane]; m['attempted'] += 1; m['verified_at_generation'] += bool(r.get('verified')); m['verified_final'] += ok; m['agree'] += (bool(r.get('verified')) == ok); m['edited'] += bool(r.get('edited_by')); m['empty_target'] += empty
    r['verified_final'] = ok
    if ok: final.append(r); hashes[lane].update((r['id'] + json.dumps(turns(r), ensure_ascii=False, sort_keys=True)).encode())
with open(f'{out}/rows_final.jsonl', 'w') as f:
    for r in final: f.write(json.dumps(r, ensure_ascii=False) + '\n')
manifest = dict(source=src, rows=len(rows), final_rows=len(final), lanes={k: dict(v, content_sha256=hashes[k].hexdigest() if k in hashes else None, **errs.get(k, {})) for k, v in man.items()})
json.dump(manifest, open(f'{out}/manifest.json', 'w'), ensure_ascii=False, indent=1); print(json.dumps(manifest, ensure_ascii=False))
