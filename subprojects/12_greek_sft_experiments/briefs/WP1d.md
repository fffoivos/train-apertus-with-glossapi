# Brief WP1d — Greek IFEval and Greek MGSM as lm-eval tasks (ILSP data)

**Goal.** Score a checkpoint on `ilsp/ifeval_greek` (541 prompts, standard IFEval schema:
`key, prompt, instruction_id_list, kwargs, prompt_en`) and `ilsp/mgsm_greek` (250 test problems,
MGSM schema) with the EleutherAI lm-evaluation-harness, using Greek-aware IFEval checkers, plus
a tiny local runner for the tests. These replace the "build ifeval_greek / gsm8k_el" packages.

**Read first:** `briefs/_COMMON.md`; `CLUSTER_PROTOCOL.md` §5; `SFT_PLAN_20260903.md` §6 and §11;
the dataset cards (`hf_hub_download('ilsp/ifeval_greek','README.md',repo_type='dataset')`, same for
`ilsp/mgsm_greek`); the harness's own `ifeval` task (install-free: read it from the lm-eval package
in the venv if present — `pip show lm_eval`; if absent, read the task from the vendored copy under
`references/evals-post-train` if it has one, else fetch the task files from
`https://github.com/EleutherAI/lm-evaluation-harness/tree/main/lm_eval/tasks/ifeval` — `utils.py`,
`instructions.py`, `instructions_registry.py`, `instructions_util.py`, `ifeval.yaml`).

**Deliverable paths (only these):** `evals/ilsp/tasks/ifeval_greek/` (task yaml + utils + Greek
checkers), `evals/ilsp/tasks/mgsm_greek/` (task yaml + utils), `evals/ilsp/run.sh`,
`evals/ilsp/README.md`, `evals/ilsp/tests/` (pytest), `briefs/WP1d.REPORT.md`.

**Spec.**
1. `ifeval_greek`: a copy of the harness's ifeval task pointed at `ilsp/ifeval_greek` (split `train`),
   with the checkers made Greek-aware where they are language-bound: **capitalisation** (upper/lower
   via `str.isupper()/islower()` on Greek letters; note tonos: Ά etc. count as uppercase), **letter
   frequency** (Greek letters), **word count** (whitespace tokens; Greek punctuation), **language
   detection** (`langdetect` → `el`; if `langdetect` is unavailable, a script-share rule: ≥ 0.6 Greek
   script), **keywords / forbidden words** (case-insensitive with Greek casefold and accent-insensitive
   matching, documented), **response language** kwargs, **end phrase / first word / postscript
   markers** taken verbatim from `kwargs` (the ILSP translation localised them — check what the
   kwargs actually contain and report), **json / title / placeholders / sections / bullets /
   highlights** unchanged (format constraints). Metrics: `prompt_level_strict_acc`,
   `inst_level_strict_acc`, `prompt_level_loose_acc`, `inst_level_loose_acc`, as in the original.
2. `mgsm_greek`: generation task, 8-shot? no — **zero-shot chat** ("Λύσε το πρόβλημα βήμα-βήμα και δώσε
   την τελική απάντηση ως αριθμό στην τελευταία γραμμή με τη μορφή `Απάντηση: <αριθμός>`"), exact match
   on the last number (strip thousands separators, accept `,` as decimal), metric `exact_match`.
   Also a 4-shot variant for base models (`mgsm_greek_4shot`) with exemplars from the train split.
3. `run.sh <model_dir> <run_name> [--limit N] [--dry-run]` → `lm_eval --model hf --model_args
   pretrained=<dir>,dtype=bfloat16 --tasks ifeval_greek,mgsm_greek --apply_chat_template
   --include_path evals/ilsp/tasks --output_path results/<run_name>/ilsp/` (vLLM optional via a flag);
   writes `results/<run_name>/ilsp.json` with the four IFEval metrics and MGSM exact match.
4. `tests/`: pytest over the Greek checkers with a Greek pass and fail case per checker type you
   touched (capitalisation, letter frequency, word count, language, keywords, forbidden words,
   end phrase, first word, postscript) and a test that the 541 prompts load and every
   `instruction_id` in the data resolves to a registered checker; MGSM answer extraction tests
   (`1.234,5`, `12`, `−3`, `Απάντηση: 42`).

**Acceptance (Claude runs):** `python -m pytest evals/ilsp/tests -q` all green; `bash evals/ilsp/run.sh x y --dry-run` exits 0 printing the lm_eval command; the report states which kwargs the ILSP data localised and any instruction ids you could not make Greek-aware.
