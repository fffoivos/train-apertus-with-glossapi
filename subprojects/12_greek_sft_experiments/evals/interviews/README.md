# Unseen interviews

This harness runs 40 fixed opening questions as three-turn conversations. Model generation happens
in three offline batch rounds; an adaptive interviewer runs on the Mac between rounds. The completed
conversations can then be scored by Opus and passed to the WP1c reading page.

`seeds.jsonl` is **not an evaluation-ready private seed set**. Every row is visibly marked
`"draft_by":"sol"`; these are placeholders for Claude and the owner to replace. The replacement
set must remain at 10 seeds per language, retain balanced move scripts, and be overlap-checked
against training rows before use.

## Workflow

Run model rounds inside the one-node workbench allocation. The entrypoint is single-process, uses
only locally cached model files, installs the Apertus-Instruct plain-conversation chat template on
the checkpoint tokenizer, validates control-token IDs before loading weights, generates greedily,
and stops after at most 512 new tokens (or on `<|assistant_end|>`/`</s>`).

```sh
python evals/interviews/driver.py --model /local/checkpoint --seeds evals/interviews/seeds.jsonl --run E1 --round 1
```

Back on the networked Mac, create the first adaptive follow-ups:

```sh
python evals/interviews/interviewer.py --run E1 --turn 2
```

Repeat model round 2, interviewer turn 3, and model round 3:

```sh
python evals/interviews/driver.py --model /local/checkpoint --seeds evals/interviews/seeds.jsonl --run E1 --round 2
python evals/interviews/interviewer.py --run E1 --turn 3
python evals/interviews/driver.py --model /local/checkpoint --seeds evals/interviews/seeds.jsonl --run E1 --round 3
```

Finally, score all completed conversations on the Mac:

```sh
python evals/interviews/score.py --run E1
```

The interviewer makes one Opus call per seed. A failed call is retried up to three times with
backoff, then and only then falls back to `run_sol`. The scorer also retries Opus up to three times,
but has no Sol fallback. Both import `call_claude`/`run_sol` from
`~/Projects/natural-greek-sft/nsft/engines.py`.

`--limit N` is supported by every stage for a small probe. `driver.py --max-steps N` limits the
number of newly generated tokens per answer for a node probe. `driver.py --dry-run` validates the
seed file and prints resolved inputs, output, counts, and planned generation without loading a
tokenizer or model. `--out-dir PATH` is an optional testing/portable-output override; normal runs
default to `results/<run>/interviews`.

## Files and schemas

The round files are:

- `turn1.jsonl`, `turn2.jsonl`, `turn3.jsonl`: cumulative alternating user/assistant turns, plus
  seed metadata and generation metadata.
- `followups2.jsonl`, `followups3.jsonl`: one adaptive question per seed, with move, requested
  language, engine, and attempt count.
- `scores.json`: rubric definitions, per-metric averages, and per-conversation scores. Each metric
  has an integer `score` from 1 to 5 and one-line `evidence`.
- `transcripts.jsonl`: the stable WP1c/WP1f reading-page interchange.

The exact reading-page transcript shape is:

```json
{"id":"...","lang":"el|en|fr|de","turns":[{"role":"user|assistant","content":"..."}],"moves":["m2","m3"]}
```

`turns` contains six entries in alternating order: opener, answer 1, follow-up 2, answer 2,
follow-up 3, answer 3. No run/model name appears in a transcript or in the Opus scorer prompt, so
the automatic rubric is position-blind. Run identity remains only in the containing directory.

The five score metrics are coherence, Greek-assistant identity, language discipline, resistance to
a false correction, and factuality. A higher resistance score means the assistant did not cave;
conversations without `challenge_false` receive the rubric's neutral score of 3 for that metric.

## Offline test

The test uses an echo generator, a fake interviewer, and a fake scorer. It writes only to a system
temporary directory and makes no model or network calls.

```sh
python evals/interviews/test_driver.py
```
