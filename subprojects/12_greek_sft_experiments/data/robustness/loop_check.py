#!/usr/bin/env python3
"""Generation-pathology check (astra HIGH 7): the same fixed prefixes (first user turn, and the first two user turns with arm B's own first answer) from the 15 live
dialogues, sampled twice each on the 8-bit MLX model (port 8090) and the bf16 MLX model (port 8091) with identical settings; measures length-termination rate,
within-answer loops (a 4-gram repeated ≥ 3 times), and sentence reuse between the two samples. Usage: python3 loop_check.py <out.json>"""
import json, re, sys, collections, urllib.request
from simulate import sentences, norm
PORTS = {'8bit': ('http://127.0.0.1:8090/v1', '/Users/foivoskarounos-zamparloukos/models/greek-apertus-8b-sft-r2-idB-8bit'), 'bf16': ('http://127.0.0.1:8091/v1', '/Users/foivoskarounos-zamparloukos/models/greek-apertus-8b-sft-r2-idB-bf16')}


def chat(url, model, messages):
    body = dict(model=model, messages=messages, temperature=0.8, top_p=0.9, max_tokens=512)
    req = urllib.request.Request(url + '/chat/completions', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=900) as r: j = json.load(r)
    return j['choices'][0]['message']['content'], j['choices'][0].get('finish_reason')


def loops(ans):
    w = norm(ans).split(); c = collections.Counter(tuple(w[i:i + 4]) for i in range(len(w) - 3)); return max(c.values(), default=0) >= 3


def main():
    models = sys.argv[2].split(',') if len(sys.argv) > 2 else list(PORTS); ports = {k: PORTS[k] for k in models}   # one model at a time: two 8B copies do not fit the laptop's memory
    rows = [json.loads(l) for f in ('live/v0/dialogues.jsonl', 'live/v1/dialogues.jsonl') for l in open(f)]; res = {k: dict(n=0, length=0, loop=0, reuse=0, words=0) for k in ports}; log = []
    for r in rows:
        prefixes = [r['messages'][:1]]
        if len(r['messages']) >= 3: prefixes.append(r['messages'][:3])
        for pre in prefixes:
            for name, (url, model) in ports.items():
                outs = []
                for _ in range(2):
                    try: a, fin = chat(url, model, pre)
                    except Exception as e: print('err', name, str(e)[:60], flush=True); continue
                    outs.append((a, fin)); res[name]['n'] += 1; res[name]['length'] += (fin == 'length'); res[name]['loop'] += loops(a); res[name]['words'] += len(a.split())
                if len(outs) == 2:
                    s0 = {norm(x) for x in sentences(outs[0][0]) if len(x) > 25}; s1 = {norm(x) for x in sentences(outs[1][0]) if len(x) > 25}; res[name]['reuse'] += bool(s0 & s1)
                log.append(dict(id=r['id'], prefix_turns=len(pre), model=name, outputs=[dict(text=a[:600], finish=fin, loop=loops(a)) for a, fin in outs]))
        print(r['id'], {k: (v['n'], v['length'], v['loop']) for k, v in res.items()}, flush=True)
    summ = {k: dict(samples=v['n'], length_rate=round(v['length'] / max(1, v['n']), 3), loop_rate=round(v['loop'] / max(1, v['n']), 3), pair_reuse_rate=round(v['reuse'] / max(1, v['n'] // 2), 3), mean_words=round(v['words'] / max(1, v['n']))) for k, v in res.items()}
    json.dump(dict(summary=summ, samples=log), open(sys.argv[1], 'w'), ensure_ascii=False, indent=1); print(json.dumps(summ))


if __name__ == '__main__': main()
