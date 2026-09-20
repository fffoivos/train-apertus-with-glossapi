# Astra review: gate1_pilots

Date 2026-09-14 18:01 · model gpt-6-astra (asserted from rollout rollout-2026-09-14T17-55-15-01a0a06a-48cc-71d1-bd5e-d872fc995f4b.jsonl) · effort xhigh · 6.0 min · prompt 98,296 chars · limit deltas {('codex', '10080'): 66.0, ('codex_bengalfox', '300'): 0.0} · brief `docs/reviews/briefs/astra_gate1_pilots.md`

**1. Verdict**

**HOLD Gate 1 for M0/M1/M2.** The supplied receipts reconcile the principal row counts, and `check_arms.log` provides substantial evidence that the intended populations and common blocks match. They do **not yet establish launch readiness**: all three trainer dry-runs are missing, the token-budget narrative contradicts the block receipts, and the supplied evidence does not bind every retained solution to a high-effort validity verdict on its final text. Two sampled Level-5 prompts also require unstated assumptions. This is an artifact review of the supplied material: local file access was unavailable, so I could not inspect §4/§8, execute the checker, recompute file hashes, or inspect `pilot_summary.py`. I distinguish those evidence gaps from demonstrated dataset defects below; I make no recommendation to regenerate completed parent datasets.

**2. Findings, ranked by severity**

**BLOCKER — Launch and decision-rule evidence is incomplete for all three arms.**

Evidence:

- **3/3 dry-run logs are missing.** The tokenizer description explicitly says its counts use “content only, +8 per turn” and that the trainer supplies the exact rendered count. Consequently, “final manifests, exact tokenizer” does **not** establish exact training-token counts.
- The effective batch implied by the config is \(1\times4\times4=16\) sequences per update. The reported ≈436/463/478 updates assume approximately full 4,096-token packing: 65,536 tokens/update. Without packing, one epoch would instead require approximately **4,483/4,483/4,568 updates**, subject to trainer batching semantics.
- No preflight budget result is supplied. Neither the full recipe table nor the readout implementation is present. “Paired one-sided 90% bootstrap,” two guardrails, and “loops M0+5” are insufficient to audit the complete decision rule.

**Fix:** Produce trainer-native dry-runs and the required preflight for all three frozen configurations. Record rendered and supervised tokens, packing/truncation statistics, actual world size, optimizer updates, schedule, runtime/cost estimate, and budget result. Bind these to dataset/config/checkpoint/tokenizer/template hashes or immutable revisions. Supply the frozen decision rule and readout-script revision, with a small fixture demonstrating pairing, missing-result handling, threshold boundaries, and winner selection. This requests evidence against the existing plan, not a revised experimental design.

**HIGH — Universal high-effort validation and post-polish coverage are not demonstrated.**

Evidence:

- **60/60 sample headers say `validity none`**, including **20/60 marked `polished edited`**. This is a provenance failure in the review material; it is **not proof that 60 solutions were unchecked**.
- The logs explicitly label repair as `HIGH`, but the `validate` entries do not expose reasoning effort or the hash of the checked text.
- The totals are internally plausible:
  - \(11,479+215+2=11,696\) validity results.
  - \(11,483+215=11,698\) polish results.
  
  These totals can include successive versions of the same problem. They do not prove distinct-problem coverage.
- `first_stage_flagged=727`, `audit_flagged=5`, and `adjudicated=727` need an ID-level reconciliation. The receipt does not establish whether the five audit flags are included; it would be unjustified to declare five adjudications missing.
- Final exclusions include **12 `no_solution`** and **2 `unpolished`**. Those are disclosed exclusions, not demonstrated failures among retained rows.

**Fix:** Generate a coverage ledger keyed by problem ID and final problem/solution hashes. Include fidelity verdict, adjudication membership, validator model and actual effort, repair lineage, polish status, and validity verdict for the exported text. Require zero retained rows with missing, stale, or insufficient-effort checks. Explain and correct the sample exporter’s `validity none`. Rerun checks only where that reconciliation finds missing coverage.

**HIGH — The stated replay token budget contradicts the arm receipts.**

The English blocks total **8,935,057 tokens** in every arm. Subtracting these and the Greek block from the reported arm totals gives:

| Arm | Reported total | Greek block | Implied replay | Implied replay share |
|---|---:|---:|---:|---:|
| M0 | ≈28.5M | 3,282,117 | ≈16.28M | ≈57.1% |
| M1 | ≈30.3M | 5,055,646 | ≈16.31M | ≈53.8% |
| M2 | ≈31.3M | 6,058,272 | ≈16.31M | ≈52.1% |

Thus **“≈19M tokens ≈65% of each arm” is incompatible with the supplied totals**. Rounding cannot explain the approximately 2.7M-token discrepancy. With 19M replay tokens, the totals would instead be approximately **31.22M/32.99M/33.99M**.

**Fix:** Reconcile all components using one counting convention and regenerate the budget/readiness summary. Report parent sampling fraction, final-arm row fraction, and final-arm token fraction separately. Preserve the authorized replay recipe; this arithmetic discrepancy does not justify changing it.

**HIGH — The contrast is strongly supported, but its exact scope is not fully attested.**

Verified from the supplied records:

- M0/M1 each contain **8,930 translated pairs**, plus **5,108 native rows** before dev removal.
- Their Greek training populations are **13,898 rows** each.
- Both English blocks have matching cross-arm content hashes.
- The checker reports identical English and replay multisets and paired Greek dev sets.
- Greek nonsupervised-token totals match exactly:
  \(3,282,117-1,607,762=5,055,646-3,381,291=1,674,355\).

Remaining gap: matching prompt multisets and matching IDs, stated separately, do not explicitly attest **byte-identical prompts for each corresponding ID**. Nor does the excerpt explicitly attest unchanged native assistant targets. The overlay flags make these useful assertions to expose. No actual pairing violation is demonstrated.

**Fix:** Attach a machine-readable comparison over `(problem_id, role, content_bytes)`, covering train and dev. Assert unchanged native targets, unchanged common M1/M2 rows, and identical common-block multiplicities. Bind the comparison to the final manifests and checker revision.

**HIGH — Two Level-5 prompts depend on unstated assumptions.**

This is **2/20 Level-5 sample prompts (10%)**, or **2/60 sampled problems (3.3%)**. These are sample findings, not estimated population rates.

- **`c2_math5_269`:** The problem asks for four-letter combinations without specifying an alphabet. The target begins **“Για το πρώτο γράμμα υπάρχουν $26$ επιλογές.”** With 26 letters the answer is 17,576; with 24 Greek letters it is 13,824. The Greek prompt does not justify choosing 26.
  
  **Fix:** Specify **“από τα 26 γράμματα του αγγλικού αλφαβήτου”** and clarify that arbitrary letter strings count, rather than only dictionary words. Recheck against the original source.

- **`c2_math5_946`:** The prompt defines the function **“για έναν ακέραιο $n$”** and asks for the smallest multiple of 15. The solution introduces **“όπου ο \(r\) είναι θετικός ακέραιος”** without that restriction appearing in the prompt. Under literal integer divisibility, negative multiples containing sufficiently large prime factors make the requested minimum nonexistent; zero also falls outside the function’s stated construction.
  
  **Fix:** Specify positive integers explicitly. The visible reasoning toward 255 then has the required domain.

These establish defects in the supplied Greek statements. Without the English originals, I cannot attribute them specifically to translation rather than source inheritance.

**MEDIUM — Drop reporting is arithmetically honest, but coverage loss needs explicit interpretation.**

| Source | Input | Retained | Dropped | Drop rate |
|---|---:|---:|---:|---:|
| GSM8K | 6,000 | 5,735 | 265 | 4.42% |
| MATH | 3,999 | 3,195 | 804 | 20.11% |
| Level-5 extension | 1,496 | 1,376 | 120 | 8.02% |
| **Total** | **11,495** | **10,306** | **1,189** | **10.34%** |

Every listed per-source drop total reconciles. However, **743/1,189 drops (62.49%) are `no_cut1_pair`**, including **647/3,999 MATH candidates (16.18%)**. These are pairing/availability exclusions, not failed mathematical validation. The contrast therefore concerns the retained paired population.

Separately, \(7,417\times3=22,251\), versus **22,211** English GSM rows retained. Seven identical-solution collapses explain only seven of the **40 unfilled slots**; **33 slots** require another explanation. This may simply reflect problems with fewer than three eligible solutions.

**Fix:** Publish an ID-level exclusion ledger with explicit reason precedence, plus below-\(k\) availability counts for English GSM. Preserve the paired exclusions; do not restore rows merely to improve retention.

**MEDIUM — Clipped review excerpts prevent complete target inspection.**

**7/100 displayed target excerpts** end before completion:

- M1: `c2_math_2469`, `c2_math_1762`.
- M0: `c2_math_672`.
- M2 extra: `c2_math5_442`, `c2_math5_1123`, `c2_math5_1152`, `c2_math5_946`.

Problem excerpts also end inside Asymptote code for `c2_math5_1181` and `c2_math5_1152`. `c2_math5_746` displays a damaged `\triangle` command.

**Fix:** Export unabridged sampled rows with hashes and explicit display-truncation metadata. Inspect the raw and trainer-rendered versions. **These are counted excerpt defects, not established training-file truncations.**

**LOW — Two localized presentation issues should be logged.**

- **`c2_gsm_1748`, M0:** **“Συνολικό κόστος των άλλων αγορών”** labels a 50-euro sum that includes hummus already discussed separately. The arithmetic and answer are correct. Change the label to total purchases.
- **`c2_math5_1462`:** Greek reasoning concludes with `\boxed{\text{Monday}}`: **1/20 Level-5 targets** has an English weekday answer. Document whether this deliberately preserves a canonical answer string; otherwise use Greek with an equivalence mapping.

**3. What is good and should not be changed**

- **The central population control is coherent.** Paired filtering, common English multiplicities, common replay, paired dev problems, and exclusion of English dev twins should remain.
- **M2’s size reconciles:** \(1,376-13-5=1,358\) additional training rows, exactly matching the checker. Its five downstream contamination exclusions are visible.
- **Decontamination is substantive:** the receipts disclose **134 Greek MATH-500 exclusions** and **172 English MATH exclusions**. The final checker reports zero 8-gram and 13-gram benchmark hits.
- **Failures and retries are disclosed.** The logs show export refusals and subsequent recovery rather than presenting an uninterrupted success narrative.
- The visible worked solutions generally explain valid mathematical steps. Examples worth preserving include domain restrictions in `c2_math_2469`, subset pairing in `c2_math5_1272`, and the reflection construction in `c2_math5_651`. I found no definite arithmetic error in those visible derivations.
- **Inherited exposure is disclosed.** Keep that disclosure; do not alter completed parents in response to this review.

**4. Answers to the brief’s specific questions**

| Question | Assessment |
|---|---|
| Do receipts prove the intended arm contrast? | **Substantial support, incomplete attestation.** Counts, English hashes, and multiset checks agree. Per-ID prompt-byte equality and unchanged native targets require explicit evidence. |
| Were all cut-2 gates applied as specified? | **Not established by the supplied material.** Counts are plausible, but universal coverage, actual high effort, and final-text bindings are missing. `validity none` is not proof of skipped checks. |
| Are drops reported honestly? | **Yes arithmetically:** all 1,189 reconcile. Distinguish pairing exclusions from quality failures and reconcile stage-event counts separately. |
| Did decontamination propagate? | **Supported by the exclusion receipts and reported final zero-hit scan**, not independently rerun here. Further English exclusions—12 GSM and 119 MATH—and M2’s five exclusions need benchmark-specific attribution. |
| Is inherited exposure disclosed correctly? | The selected R2 parent has **1 hit row / 1 distinct MATH-500 item**. R3 has **17 hit rows / 12 items**, but is not the configured parent. Do not attribute R3’s exposure to these pilots or equate overlap hits with proven memorization. |
| Are configs, updates, budget, and readout launch-ready? | **No certification possible yet:** three missing dry-runs, contradictory replay tokens, absent preflight evidence, and unavailable full recipe/readout implementation. |
| Could the pilot be misinterpreted? | Yes, if described as an isolated test of reasoning rather than the specified target-recipe change. M1 adds **1,773,529 Greek supervised tokens (+110.3%)**, changes wording/formatting, and has more updates. These are treatment properties to report, not grounds to redesign the frozen experiment. |

MATH-500 should not be described as wholly unseen. Preserve the frozen primary analysis and apply the plan’s already-dispositioned exposure/sensitivity policy; its implementation remains unverified here.

**5. Open questions for the owner**

1. Where are the final, hash-bound dry-runs, preflight result, §4/§8 text, checker implementation, and frozen `pilot_summary.py` revision?
2. Is `validity none` an exporter lookup error? Can the final-text validation ledger reconcile all retained IDs, the five audit flags, and subsequent edits?
3. Which token-count artifact is authoritative, and what produced the 19M replay claim?
4. Are the seven incomplete targets and damaged diagram text only briefing truncation? Which sampled rows are actually in training versus dev?
5. What source text supports the alphabet and integer-domain assumptions, and how does the frozen readout handle the R2 parent’s one MATH-500 overlap item?