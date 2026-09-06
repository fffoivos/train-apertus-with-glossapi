"""Shared Claude Code CLI caller for the v2 pipeline: JSON out, model asserted, tools disallowed, pauses at a 5-hour-window threshold, usage log."""
import json, os, re, subprocess, time, datetime, threading, collections
PAUSE_AT = float(os.environ.get('PAUSE_AT', '62')); _u = {'t': 0, 'v': (None, None)}; _lock = threading.Lock(); TOT = collections.Counter()
def usage():
    if time.time() - _u['t'] < 300: return _u['v']
    _u['t'] = time.time()
    try:
        tok = json.loads(subprocess.run(['security', 'find-generic-password', '-s', 'Claude Code-credentials', '-w'], capture_output=True, text=True).stdout)['claudeAiOauth']['accessToken']
        j = json.loads(subprocess.run(['curl', '-s', '-m', '20', '-H', f'Authorization: Bearer {tok}', '-H', 'anthropic-beta: oauth-2025-04-20', 'https://api.anthropic.com/api/oauth/usage'], capture_output=True, text=True).stdout)
        _u['v'] = (float(j['five_hour']['utilization']), j['five_hour'].get('resets_at'))
    except Exception: _u['v'] = (None, None)
    return _u['v']
def call(prompt, model, log_path, label='', max_turns=3, timeout=1500, retries=3):
    """Returns the parsed JSON object from the model's result text, or None."""
    for attempt in range(retries):
        u, reset = usage()
        while u is not None and u >= PAUSE_AT:
            with _lock, open(log_path, 'a') as L: L.write(f"{datetime.datetime.now():%m-%d %H:%M} five_hour {u}% >= {PAUSE_AT}: pausing 15 min (resets {reset})\n")
            time.sleep(900); _u['t'] = 0; u, reset = usage()
        t0 = time.time()
        try:
            res = subprocess.run(['claude', '-p', '--model', model, '--output-format', 'json', '--max-turns', str(max_turns), '--disallowedTools', 'Bash,Read,Edit,Write,MultiEdit,Glob,Grep,WebFetch,WebSearch,Agent,Task,NotebookEdit,TodoWrite'], input=prompt, capture_output=True, text=True, timeout=timeout); j = json.loads(res.stdout)
        except Exception as e:
            with _lock, open(log_path, 'a') as L: L.write(f"{datetime.datetime.now():%m-%d %H:%M} {label} call error {type(e).__name__} attempt {attempt}\n")
            time.sleep(30); continue
        mu = j.get('modelUsage') or {}; us = j.get('usage') or {}; txt = j.get('result') or ''
        fam = model.split('-')[1] if '-' in model else model
        with _lock:
            TOT['calls'] += 1; TOT['cost'] += j.get('total_cost_usd') or 0
            with open(log_path, 'a') as L: L.write(f"{datetime.datetime.now():%m-%d %H:%M} {label} models={list(mu.keys())} out={us.get('output_tokens',0)} cost={j.get('total_cost_usd')} {round(time.time()-t0)}s | cumulative calls={TOT['calls']} cost=${TOT['cost']:.2f} five_hour={u}%\n")
        if not any(fam in k for k in mu): raise SystemExit(f'MODEL ASSERTION FAILED for {model}: {list(mu.keys())}')
        if re.search(r'(?i)(rate limit|usage limit|limit reached)', txt[:300]): time.sleep(900); _u['t'] = 0; continue
        if j.get('is_error') or not txt.strip():
            with _lock, open(log_path, 'a') as L: L.write(f"{datetime.datetime.now():%m-%d %H:%M} {label} empty/error stop={j.get('stop_reason')} subtype={j.get('subtype')} txt={txt[:100]!r}\n")
            time.sleep(20); continue
        try: return json.loads(txt[txt.index('{'):txt.rindex('}') + 1])
        except Exception as e:
            with _lock, open(log_path, 'a') as L: L.write(f"{datetime.datetime.now():%m-%d %H:%M} {label} parse fail {type(e).__name__}: {txt[:120]!r}\n")
    return None
