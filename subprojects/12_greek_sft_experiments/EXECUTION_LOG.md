# Execution log — Greek SFT round one

One line per attempt: `date | WP | attempt | executor | verdict | nh projected/actual | CHF cumulative`.
Cap: CHF 90 ≈ 33.5 node-hours at CHF 2.69/nh (owner, 2026-09-04). Rate to be confirmed on the portal after the first job.

| date | WP | attempt | executor | verdict | nh proj/actual | CHF cum |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-09-04 00:40 | G0 | — | owner | "keep arming your loop until the plan completes … finish by morning" = GO within the CHF 90 cap; blind reading + seeds' final say stay with the owner | 0/0 | 0.00 |
| 2026-09-04 01:45 | wave1 | 1 | sol | all six briefs FAILED before any command: codex tool bridge "unknown field code_mode_host_duration_ns" (CLI 0.144.1 vs the ChatGPT app-server); fixed by `-c features.code_mode_host=false` (probe OK); relaunched | 0/0 | 0.00 |
| 2026-09-04 01:55 | WP1d/e | — | claude | ILSP public Greek IFEval (541) + MGSM (250) found → WP1d becomes an lm-eval wrap, WP1e dropped; WP1d launched | 0/0 | 0.00 |
| 2026-09-04 01:52 | cluster prep | 1 | claude | venv build + model prefetch on the login node (uenv pytorch/v2.9.1, $SCRATCH/venvs/sft); first attempt failed (no pip / wrong uenv syntax), relaunched | 0/0 | 0.00 |
| 2026-09-04 02:06 | WP1b | 2 | sol | GREEN: dry-run prints both commands; card pull reproduces GreekMMLU 0.5678 / native macro 0.4993 for E0b (and E0b_last 0.5485/0.4341) | 0/0 | 0.00 |
| 2026-09-04 02:12 | E0a | job 3285828 | claude | workbench opened (debug 01:29, preflight OK CHF 4.04 projected); GreekMMLU + native suite + retention on Apertus-8B-Instruct launched | 1.5/— | 0.00 |
| 2026-09-04 02:14 | WP1c, WP1f | 2 | sol | GREEN (offline tests OK, dry runs exit 0) | 0/0 | 0.00 |
| 2026-09-04 02:24 | WP3 | 2 | sol | GREEN (offline test OK, dry run exit 0) | 0/0 | 0.00 |
| 2026-09-04 02:24 | E0a | job 3285828 | claude | native suite cannot score Instruct (frozen model contract = CPT vocab) — dropped for E0a; retention relaunched with the 9 Table-14 tasks (offline cache); GreekMMLU running | 1.5/— | 0.00 |
| 2026-09-04 02:30 | E0a | job 3285828 | claude | GreekMMLU killed (too slow for the debug walltime: ~100 q/min); retention (9 Table-14 tasks) running on GPU1; workbench closes when retention ends | 1.5/— | 0.00 |
| 2026-09-04 02:14 | E0a | job 3285828 | claude | workbench closed after retention (GreekMMLU stopped, native n/a for Instruct) | —/0.111 | 0.30 |
| 2026-09-04 02:36 | E0a | job 3285828 | claude | MISTAKE: my watcher polled login-node pgrep for the retention wrapper, saw nothing and closed the workbench 7 min in — retention killed, E0a has NO results yet (0.11 nh, CHF 0.30). Fix: cluster/wb_watch.sh watches job state + GPU processes on the node. E0a evals to be re-run batched with the first SFT checkpoint | 1.5/0.111 | 0.30 |
| 2026-09-04 02:40 | WP1d | 1 | sol | GREEN: ILSP ifeval_greek + mgsm_greek lm-eval tasks, 17 tests pass, dry run exit 0 | 0/0 | 0.30 |
| 2026-09-04 02:45 | WP0 | 2 | sol | GREEN: --check OK; dev 658 rows; contamination: 5 exact GreekMMLU hits removed, 0 remain; E1 tokens 6.18M with the CPT tokenizer (plan said 9.34M with the Instruct tokenizer) | 0/0 | 0.30 |
| 2026-09-04 02:50 | WP2 | 2 | sol | GREEN: dry run exit 0; test_trainer_local OK (5 checks) | 0/0 | 0.30 |
| 2026-09-04 03:05 | E0b | job 3286292 | claude | workbench (debug 01:29): ILSP ifeval_greek+mgsm_greek_4shot on the base with the imposed template (GPU0), dev50/reading40 generation baseline (GPU1); GreekMMLU shard probe FAILED by design (no greekmmlu in the suite contract) → GreekMMLU batch deferred to a morning normal-partition workbench | 0.7/— | 0.30 |
| 2026-09-04 03:15 | R1 | 1 | claude-fable-5 (asserted) | VERDICT: sound in substance, every recomputed number matches; BLOCKERS 0, HIGH 2 → F1 twin-dev leak fixed, F2 batch unit decided (16 packed seqs/step); re-review R1b on the fix | 0/0 | 0.30 |
| 2026-09-04 03:07 | E0b | job 3286292 | claude | workbench closed: dev50 format-gate baseline + reading40 generations done; ILSP (ifeval_greek+mgsm_4shot) killed at 259/791 — too slow for the walltime, to rerun with a larger batch; GreekMMLU probe n/a | —/0.631 | 2.00 |
| 2026-09-04 03:40 | probe20 | job 3286621 | claude | workbench (debug 01:29) opened; 20-step trainer probe launched (smoke.yaml, --max-steps 20) while R1b re-review runs in parallel (trade-off logged: probe is mechanical, CHF <1) | 0.5/— | 2.00 |
| 2026-09-04 04:22 | probe20 | job 3286621 | claude | GREEN after 3 fixes (out-dir, hub for kernel, nvtx): 20 steps, loss 1.75→1.69, ~7.3k tok/s/node (26M tok/nh, 1.7× Meditron); eval + epoch snapshot OK → G2; smoke skipped | 0.5/— | 2.00 |
| 2026-09-04 04:26 | gridA run1 | job 3286621 | claude | E1_lr1e-5_3ep_const launched on the probe workbench (1:13 left; est. 55 min) | 1.5/— | 2.00 |
| 2026-09-04 04:35 | R1b | 1 | claude-fable-5 (asserted) | VERDICT: both fixes verified firsthand; BLOCKERS 0, HIGH 0; 3 LOW doc-drift items fixed | 0/0 | 2.00 |
| 2026-09-04 04:40 | probe20 | — | claude | fp32-master check: 14.85% of weights changed bitwise (bf16) after 20 steps — consistent with fp32 master (bf16-only trap would be ~2%) | 0/0 | 2.00 |
| 2026-09-04 03:45 | cluster | — | claude | debug QoS allows 1 running job/user → sequential grid; evals to reuse training workbenches or the normal partition; ledger rows above stamped 04:2x/04:3x/04:40 were written at 03:2x/03:3x/03:40 (clock slip, content correct) | 0/0 | 2.00 |
| 2026-09-04 03:45 | gridA run2 | job 3287233 | claude | E1_lr5e-6_3ep_const launched on a NORMAL-partition workbench (started at once; debug pending job cancelled) | 1.5/— | 2.00 |
| 2026-09-04 03:57 | gridA run1 | job 3286621 | claude | E1_lr1e-5_3ep_const DONE: 285 steps in 1,901 s (~9.4k tok/s), train loss 1.376, epoch1/2/3 saved; per-config dev losses in results/E1_lr1e-5_3ep_const/dev_losses.json | 1.5/— | 2.00 |
| 2026-09-04 04:19 | light_run1_ep12 | job 3287430 | claude | light evals of run-1 epoch1+epoch2 | —/0.345 | 2.92 |
| 2026-09-04 04:21 | gridA run2 | job 3287233 | claude | E1_lr5e-6_3ep_const DONE: 285 steps in 1,913 s, train loss 1.471, epoch1/2/3 saved; dev losses in results/E1_lr5e-6_3ep_const/dev_losses.json | 1.5/— | 2.92 |
| 2026-09-04 04:25 | rehearsal probe20_ep1 | job 3287229 | claude | eval pipeline rehearsal (native suite + interviews; ILSP/dev50 OOM lesson) | —/0.688 | 4.77 |
| 2026-09-04 04:36 | probe20+run1+ep3 light | job 3286621 | claude | debug workbench: probe attempts, grid run 1, light evals of run-1 epoch3 (walltime end) | —/1.485 | 8.77 |
| 2026-09-04 05:13 | gridA run2 + light evals | job 3287233 | claude | run 2 training + light evals of its epoch3 and epoch2 | —/1.456 | 12.69 |
| 2026-09-04 05:14 | pickA | — | claude | PROVISIONAL pick (lr 1e-5, 2 epochs): lowest dev loss, stop 0.90, voice Delta 0.853; ILSP within noise of (5e-6, ep3); E1_cos + E1last_cos set and launching | 0/0 | 12.69 |
| 2026-09-04 05:14 | E1_cos E1_cos.yaml rep | job  | claude | launched (lr 1e-5, 2 epochs, cosine) on a normal workbench | 1.5/— | 12.69 |
| 2026-09-04 05:14 | E1last_cos E1last_cos.yaml last | job  | claude | launched (lr 1e-5, 2 epochs, cosine) on a normal workbench | 1.5/— | 12.69 |
| 2026-09-04 05:16 | E1_cos | job 3288016 | claude | replicate (seed 43; lr 1e-5, 2 ep, cosine) launched on normal (earlier attempt got no workbench: normal allows ~4 jobs/user) | 1.5/— | 12.69 |
| 2026-09-04 05:19 | light_r1ep2_r2ep1 | job 3287486 | claude | light evals run-1 ep2 + run-2 ep1 | —/0.98 | 15.32 |
| 2026-09-04 05:20 | E1last_cos | job 3288021 | claude | E1-last (rev 17; lr 1e-5, 2 ep, cosine) launched on normal | 1.5/— | 12.69 |
| 2026-09-04 05:20 | gridA | — | claude | six checkpoints measured; provisional readout written (results/READOUT_provisional.md); blind reading page published for the owner | 0/0 | 15.32 |
| 2026-09-04 06:09 | E1_cos + light eval | job 3288016 | claude | replicate (seed 43) training + light evals of epoch2 | —/0.884 | 17.70 |
| 2026-09-04 06:10 | E1_cos_s44 | job 3288263 | claude | second cosine seed (44) for the seed-only noise floor | 1.5/— | — |
| 2026-09-04 06:11 | native | job 3288014 | claude | native suite on the pick (E1 lr1e-5 ep2): macro(8) 0.574 vs base 0.499 (the 0.512 first printed included a 9th key, oyxoy_nli_exact_set); NLI −0.008, WiC +0.23, metaphor +0.21 → guard passes | —/— | 17.70 |
| 2026-09-04 06:14 | E1last_cos + light eval | job 3288021 | claude | E1-last (rev 17) training + light evals of epoch2 | —/0.901 | 20.12 |
| 2026-09-04 06:15 | knownness_base | job 3287968 | claude | known-ness scorer on the base | —/1.473 | 24.09 |
| 2026-09-04 06:16 | E2_cos | job 3288295 | claude | launched (lr 1e-5, 2 ep, cosine) on normal | 1.5/— | — |
| 2026-09-04 06:20 | E3_cos | job 3288299 | claude | launched (lr 1e-5, 2 ep, cosine) on normal | 1.5/— | — |
| 2026-09-04 06:45 | E3prime_cos | job 3288520 | claude | launched (lr 1e-5, 2 ep, cosine) on normal | 1.5/— | — |
| 2026-09-04 07:04 | E1_cos_s44 + light eval | job 3288263 | claude | second cosine seed + light evals | —/0.899 | 26.50 |
| 2026-09-04 07:07 | native_candidates | job 3288014 | claude | native suite for the two candidate checkpoints | —/1.502 | 30.54 |
| 2026-09-04 07:07 | readout | — | claude | morning report published: https://claude.ai/code/artifact/162f6fc7-9d5d-4203-b379-701758d35257 (blind reading: …/690e0be1-dff4-4d25-ac8e-d49b861ab19c) | 0/0 | 26.50 |
| 2026-09-04 07:18 | E2_cos + light eval | job 3288295 | claude | training + light evals of epoch2 | —/1.043 | 33.35 |
| 2026-09-04 07:24 | E3_cos + light eval | job 3288299 | claude | training + light evals of epoch2 | —/1.076 | 36.25 |
| 2026-09-04 07:54 | knownness2 | job 3288556 | claude | known-ness scorer on the base (rerun) | —/0.782 | 38.35 |
| 2026-09-04 07:55 | native_rival | job 3288584 | claude | native suite for the (5e-6, ep3) rival | —/0.44 | 39.53 |
| 2026-09-04 07:55 | E3prime_cos + light eval | job 3288520 | claude | training + light evals of epoch2 | —/1.171 | 42.68 |
| 2026-09-04 08:22 | native_guards | job 3288578 | claude | native suite for E1_cos_ep2 (E1last moved to its own workbench) | —/0.957 | 45.26 |
| 2026-09-04 09:15 | native_E1last_ep2 | job 3289061 | claude | native suite | —/0.949 | 47.81 |
| 2026-09-04 09:16 | round one | — | claude | COMPLETE pending owner gates; natives: pick 0.574, rival 0.577, replicate 0.573, E1-last 0.500 (base 0.499/0.434); readout + blind reading published | —/17.773 | 47.81 |
| 2026-09-04 13:11 | eval plan | C | claude | blind reading + tone: 13 runs x 40 prompts scored, page published; prompt 15 excluded (answer in prompt) | — | — |
| 2026-09-04 13:11 | eval plan | A | claude | peer ILSP lanes launched on wb 3291238 (Meltemi needed sentencepiece; launcher zsh word-split bug fixed) | ~1.2 proj | — |
| 2026-09-04 13:59 | eval plan A | job 3291238 | claude | peer ILSP: Krikri/Meltemi/Apertus-Instruct/Gemma-3-12B on Greek IFEval+MGSM | —/0.945 | 50.35 |
| 2026-09-04 14:00 | eval plan | B | claude | GreekMMLU batch launched on normal wb 3292398 (pick, adapted imports, Krikri-Instruct, Apertus-Instruct) | 3.3 proj | — |
| 2026-09-04 14:08 | eval plan | B | claude | GreekMMLU batch LIVE on normal wb 3292398, 4 lanes (pick, adapted imports, Krikri-Instruct, Apertus-Instruct), ETA ~16:00. Incidents: eval env python_envs/lm_eval was mass-reinstalled at 12:27 by a process that was not this session (dill left without code, datasets import failed); dill 0.3.8 reinstalled. Launch loop with ssh inside while-read ate the lane list twice (fixed: ssh -n). One duplicate Apertus-Instruct lane OOMed and died; the original is running. ~8 min idle burn. | 3.3 proj | — |
