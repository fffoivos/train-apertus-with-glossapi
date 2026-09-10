#!/usr/bin/env python3
"""MultiChallenge-el judge: the upstream protocol byte-for-byte (the judge sees ONLY the model response and the target question, is told to be very strict,
returns reasoning + YES/NO; pass = verdict == PASS_CRITERIA). Backends: 'claude' (claude -p, model pinned) or 'sol' (Codex, OpenAI family — NOT for arms
trained on Sol data; kept for cross-judge audits). Rubric language: --rubric en|el (English is the default; the review's evidence favours English rubrics).
Usage: python3 judge.py <responses.jsonl: {id, response}> <out.jsonl> [--backend claude|sol] [--model claude-opus-5] [--rubric en]"""
import argparse, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..')); import bench_lib as B
JUDGE_PROMPT = '''You are tasked with evaluating a model response to see if it meets a specific criteria.
The criteria will always be YES/NO evaluation.
The model response is as follows:
<MODEL_RESPONSE>
{}
</MODEL_RESPONSE>
The criteria that the model response must meet is as follows. Be VERY STRICT!:
<CRITERIA>
{}
</CRITERIA>
Print your reasoning followed by your verdict, either "YES" or "NO".'''   # verbatim from upstream src/evaluator.py (commit 5ccefcca6a39)
SCHEMA = B.M.write_schema('s_mcjudge.json', {"type": "object", "properties": {"reasoning": {"type": "string"}, "verdict": {"type": "string"}}, "required": ["reasoning", "verdict"], "additionalProperties": False})


def judge_claude(prompt, model):
    out = subprocess.run(['claude', '-p', '--model', model, '--output-format', 'json', prompt + '\n\nAnswer as JSON: {"reasoning": "...", "verdict": "YES" or "NO"}.'], capture_output=True, text=True, timeout=600)
    j = json.loads(out.stdout); txt = j.get('result', ''); m = re.search(r'\{.*\}', txt, re.S)
    try: v = json.loads(m.group(0))
    except Exception: v = dict(reasoning=txt, verdict='YES' if re.search(r'\bYES\b', txt.split('verdict')[-1]) else 'NO')
    return dict(reasoning=v.get('reasoning', ''), verdict='YES' if str(v.get('verdict', '')).strip().upper().startswith('YES') else 'NO', judge_model=next((m for m in (j.get('modelUsage') or {}) if 'haiku' not in m), model), is_error=bool(j.get('is_error')))


def judge_sol(prompt, model):
    j = B.sol_json(prompt + '\n\nReturn JSON {"reasoning","verdict"} with verdict exactly "YES" or "NO".', SCHEMA, model=model, effort='medium', timeout=600)
    return dict(reasoning=j['reasoning'], verdict='YES' if j['verdict'].strip().upper().startswith('YES') else 'NO', judge_model=model) if j else None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('responses'); ap.add_argument('out'); ap.add_argument('--backend', default='claude', choices=['claude', 'sol']); ap.add_argument('--model', default=None); ap.add_argument('--rubric', default='en', choices=['en', 'el']); ap.add_argument('--workers', type=int, default=6)
    a = ap.parse_args(); model = a.model or ('claude-opus-5' if a.backend == 'claude' else 'gpt-5.6-sol')
    bench = {r['id']: r for r in B.load(os.path.join(HERE, 'conversations_el_final.jsonl'))}; resp = B.load(a.responses)
    def one(x):
        b = bench[x['id']]
        if b.get('excluded'): return None   # quarantined / excluded rows are never scored
        crit = b['target_question_en'] if a.rubric == 'en' else b['target_question_el']
        if b.get('judge_note_el'): crit += '\n' + b['judge_note_el']   # astra: explicit scoring contract for banned-word scope / category terms
        p = JUDGE_PROMPT.format(x['response'], crit)
        v = judge_claude(p, model) if a.backend == 'claude' else judge_sol(p, model)
        return None if not v else dict(id=x['id'], axis=b['axis'], response=x['response'], passed=v['verdict'] == b['pass_criteria'], rubric=a.rubric, **v, **{k: x[k] for k in x if k not in ('id', 'response')})
    B.run_jobs(resp, one, a.out, workers=a.workers, stage=f'mc judge {a.backend}')
    rows = B.load(a.out); import collections
    by = collections.defaultdict(list); [by[r['axis']].append(r['passed']) for r in rows]
    print(json.dumps(dict(n=len(rows), pass_rate=round(sum(r['passed'] for r in rows) / max(1, len(rows)), 3), by_axis={k: round(sum(v) / len(v), 3) for k, v in by.items()}), ensure_ascii=False))


if __name__ == '__main__': main()
