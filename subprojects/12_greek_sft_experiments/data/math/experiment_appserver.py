#!/usr/bin/env python3
"""A/B/C experiment: per-call `codex exec` (A) vs a persistent `codex app-server` per worker (B) vs app-server with minimal base
instructions (C), on the same 20 writer prompts at the same concurrency. Measures wall time per call, success, tokens (B/C report usage;
A cannot), Wi-Fi bytes over the run (en0 deltas; the suite runs in the background, so compare arms run back to back), peak RSS of the
worker processes. Usage: python3 experiment_appserver.py <arm A|B|C> [workers=4] [n=20]   Results appended to experiment_appserver.jsonl"""
import json, sys, os, time, subprocess, threading, concurrent.futures as cf, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mathlib as M
from codex_server import CodexServer
ARM = sys.argv[1]; W = int(sys.argv[2]) if len(sys.argv) > 2 else 4; N = int(sys.argv[3]) if len(sys.argv) > 3 else 20
prompts = json.load(open('/tmp/appsrv/prompts20.json'))[:N]; schema_path = '/var/folders/5q/65_c_z89577cz_zxgkpkz36m0000gn/T/tmp/s_corr_ans2.json'; schema = json.load(open(schema_path))
MINIMAL = 'You write the next answer of a Greek AI assistant exactly as the prompt instructs. Return only JSON matching the provided schema.'
def en0():
    out = subprocess.run(['netstat', '-ib', '-I', 'en0'], capture_output=True, text=True).stdout.splitlines(); hdr = out[0].split(); row = [l for l in out[1:] if '<Link' in l][0].split()
    return int(row[hdr.index('Ibytes')]), int(row[hdr.index('Obytes')])
def rss_mb(pids):
    if not pids: return 0.0
    out = subprocess.run(['ps', '-o', 'rss=', '-p', ','.join(map(str, pids))], capture_output=True, text=True).stdout.split(); return sum(int(x) for x in out) / 1024
results = []; lock = threading.Lock(); servers = {}
def run_A(item):
    t0 = time.time()
    try: obj = M.codex_json(item['prompt'], schema_path, 'gpt-5.6-sol', 'high', timeout=900); ok = isinstance(obj, dict) and bool(obj.get('answer'))
    except Exception as e: ok = False; obj = {'error': type(e).__name__}
    return dict(id=item['id'], wall=time.time() - t0, ok=ok, tokens=None)
def run_BC(item, base=None):
    me = threading.get_ident()
    if me not in servers:
        srv = CodexServer(); 
        if base:
            orig = srv._request
            def req(method, params, timeout=900, _orig=orig): return _orig(method, dict(params, baseInstructions=base) if method == 'thread/start' else params, timeout)
            srv._request = req
        srv.start(); servers[me] = srv
    srv = servers[me]; t0 = time.time()
    try: obj = srv.call(item['prompt'], schema, model='gpt-5.6-sol', effort='high', timeout=900); ok = isinstance(obj, dict) and bool(obj.get('answer'))
    except Exception as e: ok = False; obj = {'error': type(e).__name__ + ':' + str(e)[:80]}
    u = srv.usage[-1]['tokenUsage']['last'] if srv.usage and 'tokenUsage' in srv.usage[-1] else None
    return dict(id=item['id'], wall=time.time() - t0, ok=ok, tokens=u, err=obj.get('error'))
fn = run_A if ARM == 'A' else (lambda it: run_BC(it, None)) if ARM == 'B' else (lambda it: run_BC(it, MINIMAL))
a0 = en0(); T0 = time.time(); peak = 0.0
def sampler():
    global peak
    while time.time() - T0 < 3600 and not done.is_set():
        pids = [s.p.pid for s in servers.values()] if ARM != 'A' else [int(x) for x in subprocess.run(['pgrep', '-f', 'codex exec'], capture_output=True, text=True).stdout.split()]
        peak = max(peak, rss_mb(pids)); time.sleep(5)
done = threading.Event(); threading.Thread(target=sampler, daemon=True).start()
with cf.ThreadPoolExecutor(W) as pool: results = list(pool.map(fn, prompts))
done.set(); a1 = en0(); wall = time.time() - T0
for s in servers.values(): s.close()
walls = [r['wall'] for r in results]; oks = sum(r['ok'] for r in results)
toks = [r['tokens'] for r in results if r.get('tokens')]
summ = dict(arm=ARM, workers=W, n=N, total_wall=round(wall, 1), calls_per_min=round(N / wall * 60, 2), mean_call=round(statistics.mean(walls), 1), median_call=round(statistics.median(walls), 1), ok=oks,
            in_MB=round((a1[0] - a0[0]) / 1e6, 1), out_MB=round((a1[1] - a0[1]) / 1e6, 1), peak_rss_MB=round(peak, 0), processes=(N if ARM == 'A' else W),
            mean_input_tokens=(round(statistics.mean(t['inputTokens'] for t in toks)) if toks else None), mean_cached_tokens=(round(statistics.mean(t['cachedInputTokens'] for t in toks)) if toks else None), mean_output_tokens=(round(statistics.mean(t['outputTokens'] for t in toks)) if toks else None), errors=[r.get('err') for r in results if r.get('err')][:3], at=time.strftime('%H:%M'))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'experiment_appserver.jsonl'), 'a').write(json.dumps(summ, ensure_ascii=False) + '\n'); print(json.dumps(summ, ensure_ascii=False))
