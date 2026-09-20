# Draft issue: support revision-bound standalone checkpoint evaluation

## Problem

The canonical runner at `origin/main` revision `22c4561050cba36f34b8480e1373788e139aaf3c` cannot express a standalone evaluation of a public Hugging Face checkpoint without inventing a training campaign.

Campaign v3 requires at least one training segment and gate, plus training-specific science fields including a training data manifest and `train_argv`. Evaluation profiles and milestones live inside that compiled campaign. `probe --role evaluation` therefore needs a compiled campaign and a declared milestone, while `run-evaluation-in-allocation` needs a claimed evaluation attempt in an existing campaign allocation. Neither surface accepts an external checkpoint plus evaluation plan as a complete standalone contract.

This matters for fair peer evaluation. A public checkpoint should be bound by repository revision, weight/config/tokenizer/template hashes, benchmark/task hashes, generation settings, runtime identities, and a new output root without pretending that the canonical runner trained it.

## Proposed reusable surface

Add an evaluation-only contract and lifecycle that:

- binds an external checkpoint and its tokenizer/template files;
- binds an opaque science-owned benchmark adapter and data/task files;
- declares evaluator runtime, Slurm geometry, expected item counts, and output gates;
- supports allocation-free input/runtime preflight and `sbatch --test-only`;
- creates immutable attempt-local receipts and refuses existing output roots;
- supports debug execution and retry without any training segment or training-data fields.

One possible CLI shape is `apertus-campaign compile-evaluation` followed by the existing `probe --role evaluation` and an evaluation-only apply/execute command. The exact CLI is less important than retaining the canonical claim, receipt, retry, and scheduler-test invariants.

## Current bounded workaround

The experiment owns a frozen science adapter and manifest, uses the canonical `preflight_evaluator.py` for byte bindings and runtime imports, and runs the exact Slurm script through raw `sbatch --test-only`. This proves readiness but does not claim canonical lifecycle coverage. The draft is local only and has not been posted.

## Measured closure failures in the first debug attempt

Job `3390957` completed all model inference but exited `FAILED` while lm-eval formatted its terminal table. `make_table` dynamically imported `pytablewriter`, whose `mbstrdecoder` dependency called a `chardet` module without `detect`. The canonical import preflight passed for `lm_eval`, `transformers`, `datasets`, `accelerate`, and `torch` because it did not exercise this late rendering path. A reusable evaluation preflight should invoke the result-rendering path or accept an evaluator-owned zero-data probe that does so.

The frozen IFBench scorer also imported `mathlib` through `bench_lib.py`, but that dependency was absent from the bundle manifest. It was caught during allocation-free recovery after generation. Science-adapter closure should either enumerate recursive Python imports or run each scorer against a tiny synthetic fixture before scheduler submission. Both failures are evidence for canonical preflight/closure improvements; neither justifies changing the scientific protocol or rerunning completed inference.
