#!/usr/bin/env python3
"""Cross-vendor review of a dataset or experiment with ChatGPT's astra model at xhigh (owner rule, 2026-09-09: 1–3 reviews after every build or
experimentation phase; outputs vs intent, prompt vs literature, verification design). One codex call per review; the model is asserted from the
rollout file; the weekly-limit delta is logged so we learn what astra costs.
Usage: python3 review_astra.py <name> <brief.md> <out.md> [--rows file.jsonl --n 60 --seed 1 --fields user,assistant,meta] [--model gpt-6-astra] [--effort xhigh]
The brief is written per review: what the dataset is for, how it was built (prompt text), what to judge, and the disposition (what we will do with findings)."""
import argparse, datetime, glob, json, os, random, re, subprocess, sys, tempfile, time
HOME = os.path.expanduser('~'); LOG = f'{HOME}/sft_annot/limit_probe.log'
HEAD = ("You are an independent, cross-vendor REVIEWER of a Greek SFT dataset or experiment produced by another model (Claude) with OpenAI Sol/Luna as generators. "
        "You did not build it. Be adversarial and concrete: verify claims against the sample rows, quote row ids, report failing rates you can count in the sample, distinguish what you verified from what you infer. "
        "Report in English; quote Greek verbatim where needed. Structure: (1) verdict in one paragraph; (2) findings ranked by severity, each with evidence (row ids, counts) and a concrete fix; (3) what is good and should not be changed; (4) answers to the specific questions in the brief; (5) open questions for the owner. "
        "Disposition: findings marked BLOCKER or HIGH will be applied to queued datasets before they are generated further; MEDIUM/LOW are logged. Datasets marked 'completed' in the brief receive no drastic action, only notes.\n\n")


def limits(path):
    m = re.findall(r'"limit_id":"([^"]*)","limit_name":[^,]*,"primary":\{"used_percent":([0-9.]+),"window_minutes":(\d+)', open(path, errors='ignore').read())
    return {(k, w): float(v) for k, v, w in m}


def latest_rollout(): return max(glob.glob(f'{HOME}/.codex/sessions/*/*/*/rollout-*.jsonl'), key=os.path.getmtime)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('name'); ap.add_argument('brief'); ap.add_argument('out'); ap.add_argument('--rows', default=''); ap.add_argument('--n', type=int, default=60); ap.add_argument('--seed', type=int, default=1); ap.add_argument('--fields', default=''); ap.add_argument('--model', default='gpt-6-astra'); ap.add_argument('--effort', default='xhigh'); ap.add_argument('--max-chars', type=int, default=40000); ap.add_argument('--codex-bin', default='/Users/foivoskarounos-zamparloukos/codex-new/node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex', help='the newer CLI that gpt-6-astra requires; the pipelines keep the old one')
    a = ap.parse_args(); brief = open(a.brief).read(); sample = ''
    if a.rows:
        rows = [json.loads(l) for l in open(a.rows)]; rng = random.Random(a.seed); pick = rng.sample(rows, min(a.n, len(rows))); fields = a.fields.split(',') if a.fields else None
        def show(r): return json.dumps({k: v for k, v in r.items() if not fields or k in fields}, ensure_ascii=False)[:a.max_chars]
        sample = f'\n\n=== SAMPLE: {len(pick)} of {len(rows)} rows, seed {a.seed} ===\n' + '\n'.join(show(r) for r in pick)
    prompt = HEAD + brief + sample
    before = limits(latest_rollout()); t0 = time.time(); outp = tempfile.NamedTemporaryFile('w', suffix='.md', delete=False).name
    p = subprocess.run([a.codex_bin if os.path.exists(a.codex_bin) else 'codex', 'exec', '-m', a.model, '-c', f'model_reasoning_effort={a.effort}', '-c', 'project_doc_max_bytes=0', '-c', 'features.code_mode_host=false', '--skip-git-repo-check', '--sandbox', 'read-only', '-o', outp, '-'], input=prompt, capture_output=True, text=True, timeout=7200, cwd=tempfile.gettempdir())
    roll = latest_rollout(); models = set(re.findall(r'"model":"([^"]*)"', open(roll, errors='ignore').read())); after = limits(roll); el = time.time() - t0
    text = open(outp).read() if os.path.exists(outp) else ''
    if p.returncode != 0 or not text.strip(): sys.exit(f'review failed rc={p.returncode}: {p.stderr[-400:]}')
    if a.model not in models: sys.exit(f'MODEL ASSERTION FAILED: rollout models {models}, wanted {a.model}')
    delta = {k: round(after.get(k, 0) - before.get(k, 0), 2) for k in set(before) | set(after)}
    header = (f'# Astra review: {a.name}\n\nDate {datetime.datetime.now():%Y-%m-%d %H:%M} · model {a.model} (asserted from rollout {os.path.basename(roll)}) · effort {a.effort} · {el/60:.1f} min · prompt {len(prompt):,} chars · '
              f'limit deltas {delta} · brief `{os.path.relpath(a.brief)}`' + (f' · sample {a.n} rows of `{os.path.relpath(a.rows)}` seed {a.seed}' if a.rows else '') + '\n\n')
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True); open(a.out, 'w').write(header + text)
    with open(LOG, 'a') as f: f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M} astra-review {a.name}: deltas {delta} ({el/60:.1f} min, {len(prompt)} chars)\n")
    print(header.strip()); print(text[:1500])


if __name__ == '__main__': main()
