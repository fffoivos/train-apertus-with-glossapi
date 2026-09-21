# Review brief R-DPO2 — the DPO objective, masking and update path

## Stage goal
A training run whose objective, masking, reference and update are exactly what the plan specifies, so that a difference between arms is a
difference in learning rate or objective rather than in plumbing. This review blocks nothing already running on frozen inputs, but a blocking
finding invalidates the affected arms and they are rerun.

## Scope
- `cluster/dpo_train.py` (entrypoint and the `AnchoredDPOTrainer` subclass), `cluster/test_dpo_local.py` (7 fixtures, all passing in the production container).
- Configs `cluster/configs/G4F6P1_DPO01_0{0,1,2,3}.yaml` and `cluster/configs/zero3_dpo01.yaml`; launcher `cluster/dpo01_run.sh`.
- Run logs `logs/dpo01_0*.out` on the cluster and `runs/G4F6P1--DPO01--0*/run_receipt.json`.
- Plans: `DPO01_EXECUTION_PLAN_20260918.md` §5-§6, `DPO_EXPERIMENT_COMPARISON_20260918.md` §2-§3.
- Installed stack: TRL 1.12.0, transformers 5.16.1, torch 2.9.1, DeepSpeed ZeRO-3, four GH200s.

## Decisions taken during implementation, to be checked rather than assumed
1. TRL's `precompute_ref_log_probs` fails here: it writes per-rank arrow caches and reloads them across ranks (FileNotFoundError in `_precompute_ref_logps`). All arms therefore use a live frozen reference model, which is the fallback the plan names. Check that the reference is the identical parent, never updated, and never the policy.
2. The anchored objective (arms 02 and 03) is implemented by overriding `compute_loss`: the chosen NLL is computed from the same forward pass that TRL already ran, as a per-example token mean then a mean over examples, added as `alpha * nll`. Check the reduction, the mask and that alpha=0 leaves plain DPO bit-for-bit.
3. Schedule is constant after two warmup steps, three epochs, checkpoints each epoch, so the one-epoch checkpoint is the prefix of the three-epoch run.

## Acceptance criteria
Blocking:
1. Only the latest assistant completion is a training target; earlier assistant turns are context. Chosen and rejected share the prompt tokens.
2. Log probabilities are completion-only and summed for the DPO term; padding and the end-of-turn token are handled as the plan states.
3. The reference is frozen and identical to the parent; at initialisation the loss is log 2 and the margins are zero.
4. Full-parameter FP32 master weights with BF16 autocast; a step changes the policy, never the reference; no LoRA or quantisation crept in.
5. No silent truncation: every example fits in 4,096 tokens intact, and the trainer refuses rather than truncates.
6. The anchored term is exactly the specified reduction and is off when alpha is 0.
Major:
7. Arms differ only in learning rate and alpha: same data, seed, batch, layout, schedule, reference and template.
8. Receipts bind each arm to its config, data and code hashes.

## Notes for the reviewer
The four arms train on data corrected after R-DPO1 (round-1 leak and collapsed groups). Report defects in the objective and update path; if a
criterion passes, say so plainly. Do not restate R-DPO1's data findings.
