# WP1f report — unseen interviews driver and scorer

## What I built

- `evals/interviews/seeds.jsonl`: 40 original placeholder seeds, 10 each in `el`, `en`, `fr`, and
  `de`. Every row is marked `"draft_by":"sol"`. Across the 80 move slots the counts are:
  `challenge_true=12`, `challenge_false=12`, `clarify_shorter=12`, `clarify_format=12`,
  `localise=12`, `switch=12`, and `stretch=8`. Each source language and each switch target has
  three switches.
- `evals/interviews/driver.py`: a single-process, offline-compatible batch-round generator for
  rounds 1–3. It validates seed/previous-round/follow-up inputs before model loading, imposes and
  validates the Apertus-Instruct plain-conversation template and token IDs, generates greedily with
  a 512-token maximum, stops on assistant-end/EOS, prints 30-second heartbeats, and supports
  `--dry-run`, `--limit`, `--max-steps`, and `--out-dir`.
- `evals/interviews/interviewer.py`: one adaptive interviewer call per selected seed for turns 2 or
  3. It retries Opus up to three times with backoff and falls back to `run_sol` only after all three
  Opus attempts fail. Prompts prohibit answering/grading and require a plausible, deliberately
  false correction for `challenge_false`. Runtime text is JSON-escaped so Greek script is absent
  from a prompt that requests another language.
- `evals/interviews/score.py`: a position-blind, one-Opus-call-per-conversation rubric scorer for
  coherence, Greek-assistant identity, language discipline, resistance to false correction, and
  factuality. It writes `scores.json` and reading-page-ready `transcripts.jsonl`.
- `evals/interviews/test_driver.py`: a four-seed offline end-to-end test using an echo generator,
  fake interviewer, and fake scorer. It checks every round file, seed balance, prompt guards, score
  shape, and the exact transcript interchange shape.
- `evals/interviews/README.md`: the node/Mac sequence, retry behavior, files, options, and the shared
  WP1c/WP1f transcript contract: `{id, lang, turns:[{role, content}], moves}`.

No packages were installed, and no additional packages are needed for the specified environment.
No files were written under `results/`.

## Local commands and outputs

Python used throughout:
`/private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python`.

Syntax compilation:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python - <<'PY'
from pathlib import Path
for path in sorted(Path('evals/interviews').glob('*.py')):
    compile(path.read_text(encoding='utf-8'), str(path), 'exec')
print('syntax OK')
PY
```

Output, exit 0:

```text
syntax OK
```

Required offline end-to-end acceptance:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python evals/interviews/test_driver.py
```

Output, exit 0:

```text
OK
```

Required dry run:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python evals/interviews/driver.py --dry-run --model x --seeds evals/interviews/seeds.jsonl --run t --round 1
```

Output, exit 0:

```text
{
  "dry_run": true,
  "model": "x",
  "seeds": "/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/evals/interviews/seeds.jsonl",
  "out_dir": "/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/t/interviews",
  "output": "/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/results/t/interviews/turn1.jsonl",
  "round": 1,
  "seed_count": 40,
  "input_characters": 4268,
  "planned_max_new_tokens_per_seed": 512,
  "planned_max_generated_tokens": 20480,
  "required_inputs": [
    "/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/evals/interviews/seeds.jsonl"
  ],
  "generation": "greedy",
  "network": "disabled; local model files only"
}
```

Seed-balance and official-template equivalence probe (using the locally cached official tokenizer,
with no network access):

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/claude-501/-Users-foivoskarounos-zamparloukos/b9019f62-a4f0-4001-b1b9-3a1a58e99c50/scratchpad/sftdata/bin/python - <<'PY'
from collections import Counter
import json, sys
from pathlib import Path
from transformers import AutoTokenizer
sys.path.insert(0, 'evals/interviews')
import driver
rows=[json.loads(line) for line in Path('evals/interviews/seeds.jsonl').read_text(encoding='utf-8').splitlines()]
moves=Counter('switch' if move.startswith('switch:') else move for row in rows for move in row['moves'])
sources=Counter(row['lang'] for row in rows for move in row['moves'] if move.startswith('switch:'))
targets=Counter(move.split(':',1)[1] for row in rows for move in row['moves'] if move.startswith('switch:'))
snap=Path.home()/'.cache/huggingface/hub/models--swiss-ai--Apertus-8B-Instruct-2509/snapshots/b946d40447b2b597999b9c86d44bee0b452c919f'
tok=AutoTokenizer.from_pretrained(snap, local_files_only=True)
official=tok.chat_template
cases=[[{'role':'system','content':'S'},{'role':'user','content':'U'}],[{'role':'user','content':'U'},{'role':'assistant','content':'A'},{'role':'user','content':'V'}]]
equal=[]
for messages in cases:
    tok.chat_template=official
    expected=tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    tok.chat_template=driver.APERTUS_CHAT_TEMPLATE
    actual=tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    equal.append(expected == actual)
print('languages', dict(Counter(row['lang'] for row in rows)))
print('moves', dict(moves))
print('switch_sources', dict(sources))
print('switch_targets', dict(targets))
print('official_template_equal', equal)
PY
```

Output, exit 0:

```text
languages {'el': 10, 'en': 10, 'fr': 10, 'de': 10}
moves {'challenge_true': 12, 'switch': 12, 'challenge_false': 12, 'clarify_shorter': 12, 'clarify_format': 12, 'localise': 12, 'stretch': 8}
switch_sources {'el': 3, 'en': 3, 'fr': 3, 'de': 3}
switch_targets {'en': 3, 'fr': 3, 'de': 3, 'el': 3}
official_template_equal [True, True]
```

Whitespace/error check:

```sh
git diff --check -- evals/interviews briefs/WP1f.REPORT.md
```

Output: none; exit 0.

## What I could not test

- I did not load or generate with a real 8B checkpoint on the Mac.
- I did not run any cluster command or node-side generation, as required by the brief.
- I did not make live Opus or Sol calls. Retry/fallback paths were exercised only through injected
  offline fakes.
- `evals/dev/reading_page.py` is not present in this checkout, so I could not render WP1f
  transcripts through WP1c. The shared shape is documented and asserted exactly.
- I did not overlap-check the placeholder seeds against training data. They are explicitly ineligible
  for evaluation and must be replaced first.

## Open questions / handoff gates

1. Claude and the owner must replace all 40 `draft_by=sol` seed rows with private fresh seeds, then
   run the training-row overlap check while preserving the tested language/move balance.
2. WP1c should consume `results/<run>/interviews/transcripts.jsonl` using the exact four-key shape in
   the README and test one rendered three-turn item.
3. Claude should run a small real-checkpoint probe with `--limit` and `--max-steps` before the full
   three-round node/Mac sequence, then verify live language compliance and Opus JSON stability.
