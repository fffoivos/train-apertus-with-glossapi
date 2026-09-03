# Cluster protocol — how node-hours get spent on Clariden (round one)

Owner's rule, 2026-09-04: *a wrong script can lose us the allocation; prefer an interactive
allocation that Claude stays on, and be careful about resources.* This is the protocol that
follows from it. It binds Claude (the only one who touches the cluster) and shapes every brief
Sol receives.

## 1. The allocation is a workbench, not a launcher

- **Nothing new runs under `sbatch`.** Every script meets the GPU for the first time inside an
  interactive allocation that Claude is attached to and watching.
- **The allocation is a Slurm "workbench" job**, not a bare `salloc` from a login shell (the
  login-node reaper kills long shells; a workbench survives it):
  `sbatch --account a0140 --partition debug --nodes 1 --gpus-per-node 4 --time 1:30:00 --wrap "sleep 5400"`
  then attach with `srun --jobid <id> --overlap --pty bash` or run one command at a time with
  `srun --jobid <id> --overlap <cmd>`. The walltime is the hard ceiling: a runaway can burn at
  most one allocation, 1.5 nh in `debug` (~CHF 4), never more.
- **Idle time is the real waste.** An allocation is opened only when the next command is ready
  to run, and cancelled (`scancel <id>`) the moment the step is done — never parked "in case".
  A watchdog checks every 15 minutes: no GPU process for 15 minutes → `scancel`, logged.
- **One node, one allocation, one job at a time** until gate G2. Multi-node only if the smoke run
  proves throughput demands it, and then `nodes=2` at most, `--time` capped, never `--exclusive`
  across more, never array jobs.
- `sbatch` proper is used **only** for a long run whose exact command has already completed a
  20-step probe on a workbench: same container, same config, `--time` = projected × 1.5, one job.

## 2. Three stages before a real run

1. **Mac dry run** — the script runs end to end on the Mac with a small stand-in model
   (`--dry-run` prints the plan and exits 0; a real 5-step run on CPU/MPS proves the data path,
   the loss mask, the checkpoint save/reload).
2. **20-step probe on the workbench** — same script, `--max-steps 20`, real model, real data:
   measures tokens/s and memory; Claude watches the log line by line.
3. **The run** — same command without `--max-steps`, on the workbench if it fits the walltime,
   else `sbatch` per §1.

## 3. Budget guard, mechanical

- `EXECUTION_LOG.md` carries the cumulative node-hours and CHF. Before any submission Claude
  runs `cluster/preflight.sh <projected_nh>`, which refuses if cumulative + projected exceeds the
  cap (CHF 90 ≈ 33.5 nh) and prints the account's usage this month (`sreport`) for the log.
- After every job: `sacct -j <id> -o JobID,Elapsed,AllocNodes,State` → actual nh into the ledger
  the same day. First job's CHF is checked against the portal to confirm the 2.69 rate.

## 4. Resource hygiene

- Checkpoints and generations to `$SCRATCH/<run>/`, copied to `$STORE` (or the HF Hub, private)
  before the 30-day scratch purge; nothing bulky in `$HOME`.
- The container image / uenv is pulled and the HF cache populated **on the login node before**
  the allocation opens (`HF_HUB_OFFLINE=1` on the node); no `pip install` while allocated.
- Monitoring is never fire-and-forget: a Monitor on the job log with a heartbeat rule; kill on
  NaN loss, no heartbeat for 15 minutes, or a repeating OOM.

## 5. What Sol is told (the cluster clause of every brief)

Sol never touches the cluster and is never given a hostname, a job id, or a credential. Its
deliverable is a script that Claude can run under §2, so every brief that produces cluster code
contains this clause verbatim:

> **Cluster clause.** You do not run `ssh`, `sbatch`, `salloc`, `srun` or `scancel`, and you do
> not write scripts that call them. Write a single-process entrypoint. It must: (1) accept
> `--dry-run` (print the resolved config, data paths, token counts and the planned steps, then
> exit 0 without loading the model); (2) accept `--max-steps N` and `--limit N` so a 20-step
> probe is possible; (3) validate every input file and the tokenizer/template *before* loading
> the model, failing fast with a one-line reason; (4) print a heartbeat line
> `HB step=<n> loss=<x> tok/s=<y> mem=<z>` at least every 60 s; (5) make no network calls at
> runtime (HF cache is pre-populated; set `HF_HUB_OFFLINE=1` compatible); (6) write outputs only
> under the `--out-dir` given; (7) carry a header comment `RESOURCES: nodes=1 gpus=4
> walltime=<hh:mm> mem=<GB>` that states what it needs. The acceptance is: it runs on the Mac
> with the stand-in model in `--dry-run` and in a real 5-step run; Claude runs it on the cluster.

Briefs also avoid security-flavoured wording (kill/attack/exploit), which trips Sol's content
filter mid-task.

## 6. Roles restated

| who | may |
| --- | --- |
| Claude | open/attach/cancel workbenches, run probes, submit the one proven long job at a time, keep the ledger |
| Sol | write scripts that satisfy the cluster clause; nothing else |
| Owner | approve the cap; be told before any multi-node job or any job over 2 h |
