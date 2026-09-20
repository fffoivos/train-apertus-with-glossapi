# Pre-DPO execution: first audit and repair wave

13 September 2026. Work has started under the owner's adaptation/correction contract. No CSCS allocation or corpus-scale generation has been made in this wave.

## Completed audit work

| Work | Actual coverage | What it established |
|---|---|---|
| Unfinished worked maths | 300 full source/problem/solution records: 150 GSM, 100 Level-5 stable inputs, 50 Level-5 with multiple stored problem versions | 100 Sol/high calls, no retries or schema failures. Raw flags: 35/150, 26/100 and 18/50 respectively. These are reviewer flags, not confirmed error rates. |
| Targeted maths adjudication | 19 complete cases, selected for substantive or doubtful findings | Nine substantive candidate defects, including correct final answers with wrong derivations; one unresolved alphabet choice; a correct challenge to a bad reference; several reviewer false positives or overstated classroom ambiguities. |
| Dialogue and correcting | 24 complete dialogues plus whole-file assembly, label and mask tracing | Three certain errors survive into training: an invented move date, an unanchored calendar date, and an invented diner count. Correcting-category totals mixed two overlapping axes and need a turn-level truth sidecar. |
| Greek IF and benchmark words | 20 stratified plus 10 targeted IF rows; 35 hand-built checker probes | Some checker-passing examples conflict with their task or acquire unsupported content. Empty-response handling differs from upstream; Greek POS/word-count cases need versioned protocol decisions. |
| Imported data | 24 full records plus 11 targeted follow-ups; full structural scan of the tool block and token/weight inventory | 12,257 of 29,700 tool rows have schema text clipped at exactly 1,500 characters and unparseable. The current English OpenMath import contains GSM, with no competition-MATH coverage. |

The targeted samples cannot estimate whole-corpus defect rates. The tool-clipping count is a whole-file structural result. The maths sample represents completed partial outputs; it does not describe missing generations or the already trained Greek maths set.

## Concrete findings affecting the next dataset version

**Maths needs content checks as well as language correction.** The targeted review confirmed six examples with correct final numbers but faulty proof steps: angle relations, permutation-cycle logic, a trigonometric branch, area normalization, geometric point-order coverage, and coin orientation. Another Greek target answers only the outward leg although its question explicitly asks for the return trip. See [maths adjudication](maths/ADJUDICATION.md).

The whole-file decoded-text scan also found disallowed control characters in 194/2,146 saved Level-5 problem records and 97/3,010 solution records. Those contain duplicates and correspond to 149 and 75 IDs respectively; they are not counts of selected training rows. Two ordinary problem records and three ordinary solution records are also affected. Valid JSON alone is insufficient. Repair must recover the intended notation from evidence, and new solutions must bind to the actual input version. See [scan evidence](maths/control_character_scan.json).

**Correction must preserve good Greek.** The second maths review rejected a mechanical singular/plural complaint against a valid Greek ellipsis and rejected treating retained imperial units as automatically failed adaptation. A candidate that correctly challenges a defective reference is not an incorrect solution. The updated audit prompt and acceptance checks make those distinctions explicit.

**Dialogue needs better labels and current-state handling.** A 12-dialogue native-authoring pilot was created with three decisions in each of the true/false/partial/unresolved categories. Arithmetic/state/role/mask checks passed, but an independent semantic review still found two faulty unresolved specifications. That exposes a limit in the first verifier: it checked annotated facts without fully establishing that those annotations matched the visible user claim. Those examples were repaired in a separate semantic version, preserving the original pilot and the correction output. All 12 revised rows pass the declared verifier; a root review checked all four changed rows, while the independent review covered the unchanged rows. A negative fixture shows that an unsupported assertion plus an incidental question can still fool the substring checker, so full semantic review remains a gate. The Greek correction pass correctly made no unsupported language edits. See [independent pilot review](dialogue/pilot12_independent_report.md).

**The tool block needs a new export before reuse.** The repair preserves full payloads, source revisions, source IDs and row locators, and checks what survives the actual assembler. Existing training data remains historical. The next candidate must use a validated new export or explicitly omit that block; blanket removal of all imported chat is not justified by this audit. See [import audit](imports/IMPORTS_AUDIT_INITIAL_20260913.md).

## Applied code repairs and validation

- Maths pipeline: reject disallowed decoded control characters and failed model processes; reject conflicting duplicate input IDs before dispatch; collapse identical duplicates deterministically; bind new problem/solution outputs to input/prompt hashes, model and effort. All 11 isolated tests passed, and applied files exactly match the tested versions. These guards do not resolve historical pairing or replace the legacy generation prompts. The 100-worker code bound is per process; the active task policy controls the smaller global concurrency.

- Tool exporter: removed the payload cuts, preserved mixed text/calls/results and IDs, required immutable source revisions, and refused nonempty output destinations. Ten isolated checks passed, including an actual assembler roundtrip. Final training input remains a text protocol; native-field preservation in export is not a claim of structured-tool support by the trainer. A 200-row upstream pilot and token-window checks remain necessary before re-exporting the full block.
- IFBench scorer: restored only upstream empty/whitespace-response rejection for strict and loose checks. The applied scorer matches upstream-parity expectations on all 35 probes. Broad Greek lexical blacklists and an alphanumeric gate were withdrawn because they change semantics. Historical scores were not recomputed; Greek words aggregates remain under protocol review.

The code application receipt is [applied repairs](applied_repairs.json). Candidate corpora and completed scores were not overwritten.

## Parallelism, cost and ETA

The maths probe used four workers alongside three Sol agents, followed by eight maths workers alongside the agents: at most eleven simultaneous task-level Sol calls. The full 100-call wave took **11.3 minutes** from first probe to final response; the 96-call continuation took **7.6 minutes**. Mean call duration was **37.5 seconds**. Targeted adjudication, code review and pilot preparation ran in parallel and take additional time.

Recorded maths usage: 1,559,149 input tokens, including 761,344 cached tokens; 152,320 output tokens, including 95,952 reasoning tokens. Do not add the cached or reasoning subsets again. Agent turns consume additional account quota. The observed weekly usage changed from 31% to 35% during the wave; it is a shared-account reading, not a bill attributable solely to this task.

Use **8–12 sustainable Sol workers** for the next bounded queue after checking quota and latency. Keep three independent task owners for pipeline/checker work, semantic review and data preparation when useful. For similar three-row audits, 100 calls at eight workers currently suggest about 8 minutes plus startup/tail; budget **15–30 minutes before adjudication**, and do not extrapolate that rate to full worked-solution generation. Run CSCS only when its frozen inputs are ready, while Sol prepares the following dataset work.

This wave used **0 CSCS node-hours / CHF 0**. The CHF 2,095.08 balance remains the last owner screenshot, not a live portal reading. The cumulative CHF 230 SFT cap and estimated CHF 65.46 headroom remain unchanged. The full proposed programme still exceeds that headroom; the first measurements and screening pairs fit the prior estimate, subject to launch-time accounting.

## Next work, in dependency order

1. The small dialogue semantic repair, notation/provenance guards and 19-row maths disposition list are complete. Finish adjudicating the remaining minor maths flags and pilot the revised generation prompts before scaling.
2. Audit 120 already-trained Greek maths rows, comparing before/after language correction. The unfinished candidates audited here cannot explain the earlier training decline by themselves.
3. In parallel, audit 60 adapted-core and 60 paired foreign-language examples against the developed no_robots prompts; audit personality capability claims against the deployment facts; resolve the remaining IF protocol choices.
4. Prepare the lossless 200-row tool pilot on a CPU worker; build a small reference-backed competition-maths variant; expand the balanced dialogue pilot only after its truth/evidence checks survive independent review.
5. Freeze matched measurement inputs and the two competition-coverage variants. Price and qualify the first CSCS measurement/screening allocation through the canonical runner. While it runs, continue correcting/dialogue and source-grounded knowledge preparation.

The [main plan](../PLAN.md), [audit matrix](AUDIT_AND_PARALLELISM.md) and [prompt pack](../prompts/README.md) specify the remaining stages and gates. A first-wave completion does not mean the entire pre-DPO programme is complete.
