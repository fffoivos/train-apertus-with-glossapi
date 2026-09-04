#!/usr/bin/env python3
"""Terra annotation probe: label N sampled rows for vantage level and disposition with codex (gpt-5.6-terra, medium),
measure rows/hour and agreement with the lexicon. Usage: python3 data/terra_probe.py <sample.jsonl> <out_dir> [n] [workers]"""
import json, sys, os, time, subprocess, tempfile, concurrent.futures as cf, collections

SAMPLE, OUT = sys.argv[1], sys.argv[2]; N = int(sys.argv[3]) if len(sys.argv) > 3 else 60; W = int(sys.argv[4]) if len(sys.argv) > 4 else 24
MODEL = os.environ.get('TERRA_MODEL', 'gpt-5.6-luna'); EFFORT = os.environ.get('TERRA_EFFORT', 'medium'); TIER = os.environ.get('TERRA_TIER', 'priority')
SCHEMA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'annotation_schema.json')
os.makedirs(OUT, exist_ok=True)

RUBRIC = """You label ONE training row (a user prompt and an assistant answer) for a Greek assistant project. Judge the ASSISTANT ANSWER.

vantage (0-3): does the answer presuppose a non-Greek world in a way that matters to a Greek user?
 0 neutral: math, code, tables, format tasks, tool calls, rewriting or summarising given text, general knowledge with no locale.
 1 incidental: a foreign name, place or brand appears, nothing in the advice depends on it.
 2 framed: the answer assumes a foreign world in a way that would misinform or misfit a Greek user: advice or procedure bound to a foreign state (the IRS or NHS, ZIP codes, "your state's law", US or UK agencies and rules), prices or budgets given as advice in dollars, imperial units in advice, holidays, school systems, foreign institutions presented as the user's own. Currency or units that merely restate a math problem's givens are level 1, not 2.
 3 asserted: the answer states an identity or locale outright ("as an AI developed by X", "I am ChatGPT", "as a US resident you"), or a refusal framed around a named foreign product's policy.
frame_type: what carries the framing, if vantage >= 2 (else "none").
skill: the main thing the row teaches.
quality: 1 wrong or useless, 2 acceptable, 3 good and complete.
mannerism: true if the answer opens or closes with chatbot phrases ("Great question!", "Certainly!", "I hope this helps", "Let me know if"), or gushes.
imperatives: true if the answer gives second-person commands the user did not ask for.
disposition: keep = use as is (levels 0-1, quality 2-3); adapt = the skill is valuable and only the frame is wrong (level 2, quality 2-3), worth rewriting to a Greek frame; drop = remove: quality 1, identity rows (level 3), refusals that cite a foreign product's policy or read as boilerplate, chatbot-mannerism-heavy answers with no other value, framed rows whose skill is low.
adapt_note: for adapt only, what to change, at most 20 words. why: at most 15 words.
Return ONLY the JSON object."""

def label(row):
    prompt = RUBRIC + "\n\nSOURCE: " + row['source'] + "\n\nUSER:\n" + row['user'][:1500] + "\n\nASSISTANT:\n" + row['assistant'][:2500]
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, prefix='terra_') as tmp:
        tmp.write(prompt); p = tmp.name
    out = tempfile.mktemp(suffix='.json', prefix='terra_out_')
    t0 = time.time()
    r = subprocess.run(['codex', 'exec', '-m', MODEL, '-c', f'model_reasoning_effort={EFFORT}', '-c', f'service_tier={TIER}', '--skip-git-repo-check', '-c', 'features.code_mode_host=false',
                        '--sandbox', 'read-only', '--ephemeral', '--output-schema', SCHEMA, '-o', out, '-'], stdin=open(p), capture_output=True, text=True, timeout=600)
    dt = time.time() - t0
    txt = open(out).read() if os.path.exists(out) else r.stdout
    try:
        j = json.loads(txt[txt.index('{'):txt.rindex('}') + 1])
    except Exception:
        j = {'vantage': None, 'disposition': None, 'why': 'PARSE_FAIL', 'raw': txt[-300:]}
    j.update(source=row['source'], bucket=row['bucket'], lexicon_level=row['level'], seconds=round(dt, 1))
    return j

rows = [json.loads(l) for l in open(SAMPLE)][:N]
t0 = time.time(); results = []
with cf.ThreadPoolExecutor(W) as ex:
    for j in ex.map(label, rows):
        results.append(j); print(f"{len(results)}/{len(rows)} v={j.get('vantage')} {str(j.get('frame_type'))[:14]:14s} {str(j.get('skill'))[:14]:14s} q={j.get('quality')} m={int(bool(j.get('mannerism')))} i={int(bool(j.get('imperatives')))} {str(j.get('disposition')):5s} lex={j['lexicon_level']} {j['seconds']:5.1f}s {j.get('why','')[:50]}", flush=True)
wall = time.time() - t0
ok = [r for r in results if r.get('vantage') is not None]
agree = sum(1 for r in ok if r['vantage'] == r['lexicon_level']); within1 = sum(1 for r in ok if abs(r['vantage'] - r['lexicon_level']) <= 1)
summary = dict(model=MODEL, effort=EFFORT, tier=TIER, n=len(rows), parsed=len(ok), wall_seconds=round(wall), rows_per_hour=round(3600 * len(rows) / wall),
               mean_call_seconds=round(sum(r['seconds'] for r in results) / len(results), 1), workers=W,
               agreement_exact=round(agree / max(1, len(ok)), 3), agreement_within1=round(within1 / max(1, len(ok)), 3),
               dispositions=dict(collections.Counter(r.get('disposition') for r in results)),
               level_by_lexicon={str(k): dict(collections.Counter(r['vantage'] for r in ok if r['lexicon_level'] == k)) for k in range(4)},
               frame_types=dict(collections.Counter(r.get('frame_type') for r in ok)), skills=dict(collections.Counter(r.get('skill') for r in ok)),
               mannerism=sum(1 for r in ok if r.get('mannerism')), imperatives=sum(1 for r in ok if r.get('imperatives')), quality=dict(collections.Counter(r.get('quality') for r in ok)))
json.dump(results, open(f'{OUT}/labels.json', 'w'), ensure_ascii=False, indent=1); json.dump(summary, open(f'{OUT}/summary.json', 'w'), indent=1)
print(json.dumps(summary, indent=1))
