# Shared paths for the SFT round-one eval jobs (Clariden). Sourced by the job scripts.
# Every scorer is the CPT card's frozen one (see cluster/reference_sbatch/*), parameterized on MODEL/LABEL.
S=/iopsstor/scratch/cscs/fffoivos
C=/capstor/scratch/cscs/fffoivos
ROUND=$S/sft_round1
EVALS=$ROUND/evals
UENV_IMAGE=pytorch/v2.9.1:v2
PYENV=$S/python_envs/lm_eval
WHEEL=$S/evals/full8_native_greek_peak_window_20260817/vendor_probe/accelerate-1.14.0-py3-none-any.whl
B=$S/orchestration/full8b-cpt/20260807T221007Z-sanitized-v43
NATIVE_ROOT=$B/subprojects/03_apertus_extension_and_embedding_adaptation/03_4_implementation_experiments/init_bakeoff/eval
FINALIZER=$B/subprojects/07_full_8b_cpt/evaluation/finalize_hf_greekmmlu.py
CLEAN_SUBSET=$C/cpt_runs/dataset-scheduling-0p5b/20260803T064000Z-static-prelaunch-v2/greekmmlu_clean_subset_manifest.json
SUITE_CODE=$S/evals/full8_native_greek_3cp_20260812/code/036e1e2e53e13d3cd58cc8cb22b3c38a52881580
SUITE_RUNNER=$SUITE_CODE/subprojects/09_full_8b_cpt_results_analysis/evaluation/run_checkpoint_suite.py
SUITE_NATIVE_RUNNER=$SUITE_CODE/subprojects/03_apertus_extension_and_embedding_adaptation/03_4_implementation_experiments/init_bakeoff/eval/run_native_greek_mcq_eval.py
SUITE_ASSETS=$S/evals/full8_native_greek_peak_window_20260817/clean_assets_v5
RETENTION_CACHE_SRC=$S/evals/full8_retention_20260819/retention_only/cache/3124429_iter_0002384
LM_EVAL_REPAIR_SCRIPT=$S/repo/train-apertus-with-glossapi-cpt25b-a04c68a8/subprojects/05_token_distillation_cpt/03_training_experiments/scripts/repair_lm_eval_cli_install.py
RETENTION_TASKS="arc_challenge,arc_easy,hellaswag,winogrande,piqa,mmlu,global_mmlu,xnli,xcopa,arc_challenge_mt_el,xnli_el,xquad_el,belebele_ell_Grek,global_mmlu_full_el,include_base_44_greek_few_shot_en,global_piqa_completions_ell_grek"
: "${MODEL:?set MODEL=<hf model dir>}"; : "${LABEL:?set LABEL=<run label>}"
OUT=$EVALS/$LABEL; mkdir -p "$OUT/logs"
hb() { echo "HB $(date -u +%H:%M:%S) $*"; }

# Models live under the round HF_HOME on scratch (home quota is full): $ROUND/hf_home
HF_HOME_ROUND=$ROUND/hf_home
