#!/usr/bin/env python3
"""Terra annotation probe: label N sampled rows for vantage level and disposition with codex (gpt-5.6-terra, medium),
measure rows/hour and agreement with the lexicon. Usage: python3 data/terra_probe.py <sample.jsonl> <out_dir> [n] [workers]"""
import json, sys, os, time, subprocess, tempfile, concurrent.futures as cf, collections

SAMPLE, OUT = sys.argv[1], sys.argv[2]; N = int(sys.argv[3]) if len(sys.argv) > 3 else 60; W = int(sys.argv[4]) if len(sys.argv) > 4 else 24
MODEL = os.environ.get('TERRA_MODEL', 'gpt-5.6-luna'); EFFORT = os.environ.get('TERRA_EFFORT', 'medium'); TIER = os.environ.get('TERRA_TIER', 'priority')
SCHEMA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'annotation_schema.json')
os.makedirs(OUT, exist_ok=True)

RUBRIC = """You label ONE training row (a user prompt and an assistant answer) for a Greek assistant project. Judge the ASSISTANT ANSWER.
The row may contain several turns: the USER field is the user turns in order, the ASSISTANT field the assistant turns in order; pair them in order. Long turns may be cut: judge what is shown and do NOT penalise truncation or a missing ending.

vantage (0-3): does the answer presuppose a non-Greek world in a way that matters to a Greek user?
 0 neutral: math, code, tables, format tasks, tool calls, rewriting or summarising given text, general knowledge with no locale.
 1 incidental: a foreign name, place, brand, currency or unit appears but the advice does not depend on it. This includes every case where the USER fixed the foreign setting (asked about a US county, US law, a US trip, gave dollar amounts): answering inside the user's own frame is level 1.
 2 framed: the answer itself introduces a foreign world that would misinform or misfit a Greek user who did not ask for it: procedures of the IRS or NHS, ZIP codes, "your state's law", prices or budgets given as advice in dollars, imperial units in advice, holidays, school systems, foreign institutions presented as the user's own.
 3 asserted: the assistant describes itself as an AI, a language model or an assistant with capability or knowledge limits ("as an AI I cannot…", "I'm an AI, not a doctor", "my knowledge cutoff is…", "I don't have access to real-time data"), names a creator or product (OpenAI, Ai2, ChatGPT, OLMo), or speaks as a member of a foreign nation ("our national anthem"). Any such sentence makes the row level 3 even if the rest is useful.
frame_type: what carries the framing (identity for level 3; "none" for levels 0-1).
skill: the main thing the row teaches.
quality: 1 wrong, harmful or useless in what is shown; 2 acceptable; 3 good. Incomplete because of the window cut is NOT quality 1.
mannerism: true only if the answer opens or closes with chatbot phrases ("Great question!", "Certainly!", "I hope this helps", "Let me know if you need anything else") or gushes with exclamation marks.
imperatives: true if the answer gives the user second-person commands they did not ask for.
disposition:
 keep = levels 0-1 with quality 2-3.
 adapt = the skill is valuable and the only problem is the frame: level 2 with quality 2-3, or level 3 where the identity sentence is one line on an otherwise good answer.
 drop = quality 1; level 3 where the identity or refusal boilerplate is the substance of the answer, and every answer whose subject is the assistant itself (how it was trained, who made it, how it compares to ChatGPT); refusals that cite a foreign product's policy; persona chats that ignore the user's request; sexual, fetish, demeaning or vulgar roleplay; fabricated private records about named people.
adapt_note: for adapt only, what to change, at most 20 words. why: at most 15 words.
Return ONLY the JSON object."""

def label(row):
    if row.get('turns'):
        TC, TT = int(os.environ.get('TERRA_TURN_CAP', '3000')), int(os.environ.get('TERRA_TOTAL_CAP', '9000'))
        conv = '\n\n'.join(f"[{t.get('role','?').upper()}]\n{(t.get('content') or '')[:TC]}" for t in row['turns'])[:TT]
        prompt = RUBRIC + "\n\nSOURCE: " + row['source'] + "\n\nCONVERSATION (turns in order; TOOL turns are the tool's own outputs, not fabrications by the assistant):\n" + conv
    else:
        prompt = RUBRIC + "\n\nSOURCE: " + row['source'] + "\n\nUSER:\n" + row['user'][:1500] + "\n\nASSISTANT:\n" + row['assistant'][:2500]
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, prefix='terra_') as tmp:
        tmp.write(prompt); p = tmp.name
    out = tempfile.mktemp(suffix='.json', prefix='terra_out_')
    t0 = time.time()
    try:
        r = subprocess.run(['codex', 'exec', '-m', MODEL, '-c', f'model_reasoning_effort={EFFORT}', '-c', f'service_tier={TIER}', '--skip-git-repo-check', '-c', 'features.code_mode_host=false',
                            '--sandbox', 'read-only', '--ephemeral', '--output-schema', SCHEMA, '-o', out, '-'], stdin=open(p), capture_output=True, text=True, timeout=900)
        txt = open(out).read() if os.path.exists(out) else r.stdout
    except Exception as e:  # a timed-out or failed call must not kill the whole pool; it becomes a PARSE_FAIL row that can be re-run
        txt = ''; print('call failed:', type(e).__name__, str(e)[:80], flush=True)
    dt = time.time() - t0
    try:
        j = json.loads(txt[txt.index('{'):txt.rindex('}') + 1])
    except Exception:
        j = {'vantage': None, 'disposition': None, 'why': 'PARSE_FAIL', 'raw': txt[-300:]}
    j.update(source=row['source'], bucket=row['bucket'], lexicon_level=row.get('level'), gt_id=row.get('gt_id'), seconds=round(dt, 1))
    return j

rows = [json.loads(l) for l in open(SAMPLE)][:N]
t0 = time.time(); results = []
with cf.ThreadPoolExecutor(W) as ex:
    for j in ex.map(label, rows):
        results.append(j); print(f"{len(results)}/{len(rows)} v={j.get('vantage')} {str(j.get('frame_type'))[:14]:14s} {str(j.get('skill'))[:14]:14s} q={j.get('quality')} m={int(bool(j.get('mannerism')))} i={int(bool(j.get('imperatives')))} {str(j.get('disposition')):5s} lex={j['lexicon_level']} {j['seconds']:5.1f}s {j.get('why','')[:50]}", flush=True)
wall = time.time() - t0
ok = [r for r in results if r.get('vantage') is not None]
lex = [r for r in ok if r.get('lexicon_level') is not None]
agree = sum(1 for r in lex if r['vantage'] == r['lexicon_level']); within1 = sum(1 for r in lex if abs(r['vantage'] - r['lexicon_level']) <= 1)
summary = dict(model=MODEL, effort=EFFORT, tier=TIER, n=len(rows), parsed=len(ok), wall_seconds=round(wall), rows_per_hour=round(3600 * len(rows) / wall),
               mean_call_seconds=round(sum(r['seconds'] for r in results) / len(results), 1), workers=W,
               agreement_exact=round(agree / max(1, len(lex)), 3), agreement_within1=round(within1 / max(1, len(lex)), 3), lexicon_rows=len(lex),
               dispositions=dict(collections.Counter(r.get('disposition') for r in results)),
               level_by_lexicon={str(k): dict(collections.Counter(r['vantage'] for r in lex if r['lexicon_level'] == k)) for k in range(4)},
               frame_types=dict(collections.Counter(r.get('frame_type') for r in ok)), skills=dict(collections.Counter(r.get('skill') for r in ok)),
               mannerism=sum(1 for r in ok if r.get('mannerism')), imperatives=sum(1 for r in ok if r.get('imperatives')), quality=dict(collections.Counter(r.get('quality') for r in ok)))
json.dump(results, open(f'{OUT}/labels.json', 'w'), ensure_ascii=False, indent=1); json.dump(summary, open(f'{OUT}/summary.json', 'w'), indent=1)
print(json.dumps(summary, indent=1))
