#!/usr/bin/env python3
"""Generate responses for the four Greek benchmarks from an OpenAI-compatible chat endpoint (vLLM on a workbench, or the laptop server for smoke tests).
Frozen protocol (recorded in MANIFEST.json under 'generation'): greedy decoding (temperature 0), top_p 1, max_tokens 2048 for math500 and 1024 otherwise,
no system prompt (the model's chat template as served), one request per item, in the language variant asked for:
  math500: problem_el / problem_en + the fixed boxed-answer instruction (el: «Λύσε το πρόβλημα και δώσε την τελική απάντηση μέσα σε \\boxed{}.» ; en: "Solve the problem and give the final answer inside \\boxed{}.")
  ifbench: prompt_el / prompt_en as is
  xstest:  prompt_el / prompt_en as is
  multichallenge: turns_el / turns_en as the message history (fixed-history continuation; the last turn is the user's)
Resumable (skips ids already in the output). Usage:
  python3 generate.py <endpoint_base e.g. http://127.0.0.1:8000/v1> <served_model_name> <out_dir> [--sets math500,ifbench,xstest,multichallenge] [--langs el,en] [--workers 16] [--limit N]
Output: <out_dir>/<set>_<lang>.jsonl rows {id, response, finish_reason, usage} — the input format of every scorer (math500: score_math500.py; ifbench/score.py; xstest/judge.py; multichallenge/judge.py)."""
import argparse, json, os, sys, time, urllib.request, concurrent.futures as cf
HERE = os.path.dirname(os.path.abspath(__file__))
BOX = {'el': ' Λύσε το πρόβλημα και δώσε την τελική απάντηση μέσα σε \\boxed{}.', 'en': ' Solve the problem and give the final answer inside \\boxed{}.'}
def load(p): return [json.loads(l) for l in open(p) if l.strip()]
def items(s, lang):
    if s == 'math500':
        for r in load(f'{HERE}/math500/problems_el_final.jsonl'): yield r['id'], [dict(role='user', content=(r['problem_el'] if lang == 'el' else r['problem_en']) + BOX[lang])], 2048
    if s == 'math200':   # one-use confirmation set (R4 plan §5); same instruction and budget as math500
        for r in load(f'{HERE}/math200_confirm/problems_el_final.jsonl'): yield r['id'], [dict(role='user', content=(r['problem_el'] if lang == 'el' else r['problem_en']) + BOX[lang])], 2048
    elif s == 'ifbench':
        for r in load(f'{HERE}/ifbench/prompts_el_final.jsonl'): yield r['id'], [dict(role='user', content=r['prompt_el'] if lang == 'el' else r['prompt_en'])], 1024
    elif s == 'xstest':
        for r in load(f'{HERE}/xstest/prompts_el_final.jsonl'): yield r['id'], [dict(role='user', content=r['prompt_el'] if lang == 'el' else r['prompt_en'])], 1024
    elif s == 'multichallenge':
        for r in load(f'{HERE}/multichallenge/conversations_el_final.jsonl'):
            if r.get('excluded'): continue
            turns = r['turns_el'] if lang == 'el' else r.get('turns_en') or []
            if not turns or turns[-1]['role'] != 'user': continue
            yield r['id'], [dict(role=t['role'], content=t['content']) for t in turns], 1024
EXTRA = {}
def call(base, model, messages, max_tokens, tries=4):
    body = dict(model=model, messages=messages, temperature=0, top_p=1, max_tokens=max_tokens, **EXTRA)
    for k in range(tries):
        try:
            req = urllib.request.Request(base.rstrip('/') + '/chat/completions', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=600) as r: j = json.loads(r.read())
            c = j['choices'][0]; return c['message']['content'], c.get('finish_reason'), j.get('usage')
        except Exception as e:
            if k == tries - 1: return '', f'error: {str(e)[:200]}', None
            time.sleep(5 * (k + 1))
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('base'); ap.add_argument('model'); ap.add_argument('out'); ap.add_argument('--sets', default='math500,ifbench,xstest,multichallenge')
    ap.add_argument('--langs', default='el,en'); ap.add_argument('--workers', type=int, default=16); ap.add_argument('--limit', type=int, default=0); ap.add_argument('--extra-body', default='', help='JSON merged into every request, e.g. {"chat_template_kwargs": {"enable_thinking": false}}'); a = ap.parse_args()
    EXTRA.update(json.loads(a.extra_body) if a.extra_body else {})
    os.makedirs(a.out, exist_ok=True)
    for s in a.sets.split(','):
        for lang in a.langs.split(','):
            outp = f'{a.out}/{s}_{lang}.jsonl'; done = {json.loads(l)['id'] for l in open(outp)} if os.path.exists(outp) else set()
            todo = [(i, m, mt) for i, m, mt in items(s, lang) if i not in done]
            if a.limit: todo = todo[:a.limit]
            t0 = time.time(); n_err = 0
            with open(outp, 'a') as f, cf.ThreadPoolExecutor(a.workers) as ex:
                futs = {ex.submit(call, a.base, a.model, m, mt): i for i, m, mt in todo}
                for fu in cf.as_completed(futs):
                    i = futs[fu]; resp, fin, usage = fu.result()
                    if resp is None: n_err += 1
                    f.write(json.dumps(dict(id=i, response=resp, finish_reason=fin, usage=usage), ensure_ascii=False) + '\n'); f.flush()
            print(f'{s}_{lang}: {len(todo)} generated (+{len(done)} existing), errors {n_err}, {time.time()-t0:.0f}s', flush=True)
if __name__ == '__main__': main()
