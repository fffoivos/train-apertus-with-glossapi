#!/usr/bin/env python3
"""Cross-vendor double check of Luna's verdicts with Claude Sonnet 5 through the Claude Code CLI (owner request, Sat 5 Sep).
Samples n rows per Luna disposition (keep/adapt/drop) per block, sends them in batches under the full rubric v3 with a wider window
(12,000 chars a turn, 24,000 a row), asserts the model from modelUsage, logs tokens/cost per call and pauses when the 5-hour
subscription window passes 90%. Usage: python3 data/sonnet_check.py <out_dir> <n_per_disposition> <workers> <block1> [block2 ...]"""
import json, sys, os, re, random, subprocess, time, threading, collections, concurrent.futures as cf, datetime
OUT, N, W = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); BLOCKS = sys.argv[4:]; A = os.path.expanduser('~/sft_annot'); os.makedirs(OUT, exist_ok=True)
MODEL = os.environ.get('CHECK_MODEL', 'claude-sonnet-5'); BATCH = int(os.environ.get('CHECK_BATCH', '8')); TC, TT = 12000, 24000
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'terra_probe.py')).read()
RUBRIC = re.search(r'^RUBRIC = """(.*?)"""', src, re.S | re.M).group(1)
HEAD = ("You are an independent second judge. Apply the rubric below to EACH of the rows that follow (they are separated by ===== ROW <id> =====). "
        "Judge every row on its own. Do not use any tools. Return ONLY one JSON object: {\"rows\": [{\"id\": ..., \"vantage\": 0-3, \"frame_type\": ..., \"skill\": ..., "
        "\"quality\": 1-3, \"mannerism\": true/false, \"imperatives\": true/false, \"disposition\": \"keep\"|\"adapt\"|\"drop\", \"why\": \"...\"}, ...]} with one entry per row, same ids.\n\nRUBRIC:\n")
def usage():
    try:
        tok = json.loads(subprocess.run(['security', 'find-generic-password', '-s', 'Claude Code-credentials', '-w'], capture_output=True, text=True).stdout)['claudeAiOauth']['accessToken']
        r = subprocess.run(['curl', '-s', '-m', '20', '-H', f'Authorization: Bearer {tok}', '-H', 'anthropic-beta: oauth-2025-04-20', 'https://api.anthropic.com/api/oauth/usage'], capture_output=True, text=True)
        j = json.loads(r.stdout); return float(j['five_hour']['utilization']), j['five_hour'].get('resets_at')
    except Exception: return None, None
def render(row):
    parts = [f"[{t['role'].upper()}]\n{(t.get('content') or '')[:TC]}" for t in row['turns'] if t['role'] in ('user', 'assistant', 'system') and (t.get('content') or '').strip()]
    return '\n\n'.join(parts)[:TT]
lock = threading.Lock(); LOG = open(f'{OUT}/usage.log', 'a'); tot = collections.Counter()
def call(batch):
    prompt = HEAD + RUBRIC + '\n\n' + '\n\n'.join(f"===== ROW {r['id']} =====\n{render(r)}" for r in batch)
    for attempt in range(4):
        u, _ = usage()
        while u is not None and u >= 90:
            with lock: LOG.write(f"{datetime.datetime.now():%H:%M} five_hour {u}% >= 90: pausing 10 min\n"); LOG.flush()
            time.sleep(600); u, _ = usage()
        t0 = time.time()
        try:
            res = subprocess.run(['claude', '-p', '--model', MODEL, '--output-format', 'json', '--max-turns', '2'], input=prompt, capture_output=True, text=True, timeout=1200)
            j = json.loads(res.stdout)
        except Exception as e:
            with lock: LOG.write(f"{datetime.datetime.now():%H:%M} call error {type(e).__name__} attempt {attempt}\n"); LOG.flush()
            time.sleep(60); continue
        mu = j.get('modelUsage') or {}; us = j.get('usage') or {}
        with lock:
            for k in ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens', 'output_tokens'): tot[k] += us.get(k, 0)
            tot['cost'] += j.get('total_cost_usd') or 0; tot['calls'] += 1
            LOG.write(f"{datetime.datetime.now():%H:%M} rows={len(batch)} models={list(mu.keys())} in={us.get('input_tokens',0)} cache_new={us.get('cache_creation_input_tokens',0)} cache_read={us.get('cache_read_input_tokens',0)} out={us.get('output_tokens',0)} cost={j.get('total_cost_usd')} {round(time.time()-t0)}s | cumulative calls={tot['calls']} cost=${tot['cost']:.2f} out_tokens={tot['output_tokens']}\n"); LOG.flush()
        if not any(k.startswith('claude-sonnet-5') for k in mu): raise SystemExit(f'MODEL ASSERTION FAILED: {list(mu.keys())}')
        txt = j.get('result') or ''
        if j.get('is_error') or re.search(r'(?i)(rate limit|usage limit|limit reached)', txt[:300]):
            with lock: LOG.write(f"{datetime.datetime.now():%H:%M} limit/error result: {txt[:120]!r}; sleeping 10 min\n"); LOG.flush()
            time.sleep(600); continue
        try:
            obj = json.loads(txt[txt.index('{'):txt.rindex('}') + 1]); rows = obj['rows']; got = {str(r['id']): r for r in rows}
            out = []
            for r in batch:
                g = got.get(str(r['id']))
                out.append(dict(id=r['id'], block=r['block'], luna=r['luna'], sonnet=g.get('disposition') if g else 'PARSE_FAIL', s_frame=g.get('frame_type') if g else None, s_quality=g.get('quality') if g else None,
                                s_mannerism=g.get('mannerism') if g else None, s_vantage=g.get('vantage') if g else None, s_why=g.get('why') if g else None, judge=MODEL))
            return out
        except Exception as e:
            with lock: LOG.write(f"{datetime.datetime.now():%H:%M} parse fail {type(e).__name__} attempt {attempt}: {txt[:100]!r}\n"); LOG.flush()
    return [dict(id=r['id'], block=r['block'], luna=r['luna'], sonnet='PARSE_FAIL', judge=MODEL) for r in batch]
random.seed(17)
for b in BLOCKS:
    outp = f'{OUT}/{b}.jsonl'; done = set()
    if os.path.exists(outp):
        for l in open(outp):
            j = json.loads(l)
            if j.get('sonnet') and j['sonnet'] != 'PARSE_FAIL': done.add(j['id'])
    lab = {}
    for l in open(f'{A}/labels/{b}.labels.jsonl'):
        j = json.loads(l)
        if j.get('disposition'): lab[j['id']] = j
    by = collections.defaultdict(list)
    for i, j in lab.items(): by[j['disposition']].append(i)
    want = {}
    for d in ('keep', 'adapt', 'drop'):
        ids = sorted(by.get(d, [])); random.Random(f'{b}:{d}').shuffle(ids)
        for i in ids[:N]: want[i] = d
    todo = {i: d for i, d in want.items() if i not in done}
    rows = []
    with open(f'{A}/core_export/{b}.jsonl') as f:
        for l in f:
            if not todo: break
            r = json.loads(l)
            if r['id'] in todo: rows.append(dict(id=r['id'], block=b, luna=todo.pop(r['id']), turns=r['turns']))
    random.shuffle(rows); batches = [rows[k:k + BATCH] for k in range(0, len(rows), BATCH)]
    print(f'{b}: {len(want)} sampled ({collections.Counter(want.values())}), {len(done)} done, {len(rows)} to judge in {len(batches)} calls', flush=True)
    t0 = time.time(); n = 0
    with open(outp, 'a') as fh, cf.ThreadPoolExecutor(W) as ex:
        for res in ex.map(call, batches):
            for j in res: fh.write(json.dumps(j, ensure_ascii=False) + '\n')
            fh.flush(); n += len(res)
            print(f'{b}: {n}/{len(rows)} {round(3600*n/(time.time()-t0))} rows/h cumulative ${tot["cost"]:.2f}', flush=True)
    print(f'== {b} DONE', flush=True)
print('ALL DONE', flush=True)
