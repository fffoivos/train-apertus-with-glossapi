#!/usr/bin/env python3
"""Terra annotation probe: label N sampled rows for vantage level and disposition with codex (gpt-5.6-terra, medium),
measure rows/hour and agreement with the lexicon. Usage: python3 data/terra_probe.py <sample.jsonl> <out_dir> [n] [workers]"""
import json, sys, os, time, subprocess, tempfile, concurrent.futures as cf, collections

SAMPLE, OUT = sys.argv[1], sys.argv[2]; N = int(sys.argv[3]) if len(sys.argv) > 3 else 60; W = int(sys.argv[4]) if len(sys.argv) > 4 else 24
MODEL = os.environ.get('TERRA_MODEL', 'gpt-5.6-terra'); EFFORT = os.environ.get('TERRA_EFFORT', 'medium')
os.makedirs(OUT, exist_ok=True)

RUBRIC = """You label ONE training row (a user prompt and an assistant answer) for a Greek assistant project.
Question: does the ASSISTANT ANSWER presuppose a non-Greek world in a way that matters to a Greek user? Judge only the answer.

Levels:
0 = vantage-neutral: math, code, tables, format tasks, tool calls, rewriting or summarising a given text, general knowledge with no locale.
1 = incidental: a foreign name, place or brand appears, but nothing in the advice depends on it.
2 = framed: the answer assumes a foreign world in a way that would misinform or misfit a Greek user: dollars, Fahrenheit, miles, the IRS or NHS, ZIP codes, "your state's law", Thanksgiving, the SAT, US or UK procedures, prices, holidays, institutions.
3 = asserted: the answer states an identity or locale outright: "as an AI developed by X", "I am ChatGPT", "as a US resident you", refusals framed around a named foreign product's policy.

Disposition (what we should do with the row for stage-1 SFT):
keep = use as is (levels 0 and most 1).
adapt = worth rewriting to a Greek frame because the skill is valuable and the frame is the only problem (some level 2).
drop = remove (identity rows, safety-policy refusals, level 2 rows whose value is low or whose frame cannot be moved).

Return ONLY a JSON object: {"level": 0|1|2|3, "disposition": "keep"|"adapt"|"drop", "why": "at most 15 words"}"""

def label(row):
    prompt = RUBRIC + "\n\nSOURCE: " + row['source'] + "\n\nUSER:\n" + row['user'][:1500] + "\n\nASSISTANT:\n" + row['assistant'][:2500]
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, prefix='terra_') as tmp:
        tmp.write(prompt); p = tmp.name
    out = tempfile.mktemp(suffix='.json', prefix='terra_out_')
    t0 = time.time()
    r = subprocess.run(['codex', 'exec', '-m', MODEL, '-c', f'model_reasoning_effort={EFFORT}', '--skip-git-repo-check', '-c', 'features.code_mode_host=false',
                        '--sandbox', 'read-only', '--ephemeral', '-o', out, '-'], stdin=open(p), capture_output=True, text=True, timeout=600)
    dt = time.time() - t0
    txt = open(out).read() if os.path.exists(out) else r.stdout
    try:
        j = json.loads(txt[txt.index('{'):txt.rindex('}') + 1])
    except Exception:
        j = {'level': None, 'disposition': None, 'why': 'PARSE_FAIL', 'raw': txt[-300:]}
    j.update(source=row['source'], bucket=row['bucket'], lexicon_level=row['level'], seconds=round(dt, 1))
    return j

rows = [json.loads(l) for l in open(SAMPLE)][:N]
t0 = time.time(); results = []
with cf.ThreadPoolExecutor(W) as ex:
    for j in ex.map(label, rows):
        results.append(j); print(f"{len(results)}/{len(rows)} lvl={j.get('level')} disp={j.get('disposition')} lex={j['lexicon_level']} {j['seconds']}s {j.get('why','')[:60]}", flush=True)
wall = time.time() - t0
ok = [r for r in results if r.get('level') is not None]
agree = sum(1 for r in ok if r['level'] == r['lexicon_level']); within1 = sum(1 for r in ok if abs(r['level'] - r['lexicon_level']) <= 1)
summary = dict(model=MODEL, effort=EFFORT, n=len(rows), parsed=len(ok), wall_seconds=round(wall), rows_per_hour=round(3600 * len(rows) / wall),
               mean_call_seconds=round(sum(r['seconds'] for r in results) / len(results), 1), workers=W,
               agreement_exact=round(agree / max(1, len(ok)), 3), agreement_within1=round(within1 / max(1, len(ok)), 3),
               dispositions=dict(collections.Counter(r.get('disposition') for r in results)),
               level_by_lexicon={str(k): dict(collections.Counter(r['level'] for r in ok if r['lexicon_level'] == k)) for k in range(4)})
json.dump(results, open(f'{OUT}/labels.json', 'w'), ensure_ascii=False, indent=1); json.dump(summary, open(f'{OUT}/summary.json', 'w'), indent=1)
print(json.dumps(summary, indent=1))
