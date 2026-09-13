# GOAL for the executing agent (astra / Codex), 13–14 September 2026

Read first: docs/HANDOFF_20260913.md (state), docs/R4_PLAN_20260913.md (§0 answers, §7/§10 dispositions, §8 tables), docs/reviews/ASTRA_results_r3_20260913.md. Owner: Foivos. You continue the R3 → R4 programme until the owner returns (14 Sept morning). Claude resumes then; leave a dated log of everything you did in docs/EXECUTION_LOG.md.

## Contract
1. **Nothing launches without a one-line announcement in EXECUTION_LOG.md first**: what, how many Sol calls or node-hours, why. The owner reads that log.
2. **Owner's sequence is binding**: evaluations (DONE) → (a)/(b) (DONE, plan §0) → (c) reviews (DONE, §7/§10) → (d) datasets and experiments. Step (d) begins with the two experiments the results review named; bulk data generation is NOT authorised until the owner has read the plan and said which sets to build.
3. **Allowed without the owner**: (i) the frozen recovery panel — reuse existing generations only (results/R3_single/bench_*, results/peers_20260913, results/robustness_*), identical inputs, hidden identities, item ids, explicit denominators; no new model serving; (ii) the 300-row audit of the partial cut-2 math output (data/math/cut2/out) as an error-rate report, not a filter; (iii) reconciling the correcting-set turn taxonomy (data/robustness/correcting/scale/rows/summary.json: 3,822 category counts vs 3,692 turns); (iv) the IFBench-el `words` checker audit with hand-built Greek answers (DATA_TODO 59); (v) defining the noise bands as paired-item intervals in the status doc.
4. **Not allowed without the owner's explicit line**: any training or cluster job (cap CHF 230, ledger CHF 163.02; cluster/preflight.sh must say OK); any Sol batch over 200 calls; any use of Claude/Opus (`claude -p`) for judging or scoring — judging is Sol only; any change to completed datasets, receipts or results (annotate, never rewrite); any push to `Greekpt/*`.
5. **Safety rules**: kill processes by PID only (never `pkill -f codex`); keep concurrent Sol calls ≤ 100 (`ps -eo pid,ppid,args | grep "exec -m"`); a detached launch survives an interrupted command — check `pgrep` after any interruption; ssh/scp with `-4`; the CSCS certificate expires daily (`cscs-key sign` is the owner's); no sleeping scripts on the login node; `-c features.remote_plugin=false -c features.apps=false` on every codex call.
6. **Reporting**: every number with its protocol (judge, profile, n, decoding); report failing numbers as failing; never compare runs whose protocols differ without saying so; if a dataset or metric looks wrong, write it down, do not fix it silently.

## Definition of done for the night
- EXECUTION_LOG.md entries for each item in §3 you completed, with paths to outputs.
- docs/R4_PLAN_20260913.md updated with: the recovery-panel table (if done), the cut-2 audit error rate, the reconciled correcting counts, the IFBench words-checker verdict, defined noise bands.
- No running processes left behind except ones listed in the log with their PIDs.
- A five-line summary at the top of docs/HANDOFF_20260913.md: what changed, what is open, what the owner must decide.

## Reusable drivers (copied from the session scratchpad; read before use, paths inside are absolute)
cluster/drivers/: peers_takeover.sh (serve peers + benchmarks + dialogues on a debug workbench), judge_peers_seq.sh (Sol judging, low concurrency), bench_pass.sh (four benchmarks for two checkpoints), interviews_pass.sh (interview rounds 2–3 + scoring), score_old_sol.sh (interview rescoring on Sol), ds_reviews.sh / results_review.sh (astra review launchers), queue_r3_pass.sh (arm assembly + sbatch + eval chain), resume_test.sh, launch_r3_probe.sh, cut2_sol.sh (math batches — DO NOT run without the owner).
