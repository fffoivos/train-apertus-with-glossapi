# Astra review: r3_diag_recipe

Date 2026-09-12 07:29 · model gpt-6-astra (asserted from rollout rollout-2026-09-12T07-21-52-01a093d9-af98-7970-8bb4-8e6e51c3b40c.jsonl) · effort xhigh · 7.9 min · prompt 22,774 chars · limit deltas {('codex', '10080'): 0.0} · brief `docs/reviews/briefs/astra_r3_diag_recipe.md`

## 1. Verdict

**R3 is a trade-off, not demonstrated overall progress over arm B.** The strongest evidence favors the value of B’s concentrated finishing stage, but it does **not** establish that ordering alone caused the difference, or that the new data is innocent. B differs in terminal data composition, exposure count, additional optimization, and LR scheduling. R3_pass changes all of those again, making it a useful recovery test but an inadequate isolation test. The math diagnosis also needs narrowing: both recipes lost **Greek MATH benchmark performance**, while R3’s English MATH score improved. I would preserve completed artifacts, keep the queued pass as a diagnostic run, and change the next recipe’s exposure accounting, math coverage, and retention provisions. **Verification boundary:** no sample rows, row IDs, predictions, or actual receipt files were supplied. Arithmetic below is independently checked against the printed tables; behavioral counts and audit results remain owner-reported. No row-level failure rate can honestly be claimed from this packet.

## 2. Findings ranked by severity

### HIGH — R3_pass cannot establish “schedule, not data”

**Evidence.** The queued comparison changes:

- Base checkpoint: stage 1 → R3.
- Pass data: 41,697 → 48,449 rows, **+16.2%**.
- Suite/correcting exposure: another **13,504 row presentations** across two epochs.
- Supervised training volume: those additions contribute approximately **10.8M supervised tokens** across two epochs, using the registry’s rounded totals.
- Common v3 personality exposure: nominally four presentations during R3 plus eight during the pass, versus eight in B’s pass.

Moreover, identical peak LR, epochs, and warmup percentages do not mean identical numbers of updates or identical optimization histories.

**Fix.** Describe the experiment as:

> “Does an augmented Greek finishing stage recover R3’s behavior?”

Do not interpret success as proving ordering was responsible, or failure as disproving H1. Add an exact historical-pass control, discussed under question 2.

### HIGH — “Both lost hard math” conflates different possible failures

Assuming the reported percentages use all 500 items:

| Greek MATH measure | R3 | B | Stage 1 |
|---|---:|---:|---:|
| Correct | 40/500, **8.0%** | 38/500, **7.6%** | 64/500, **12.8%** |
| Repetition detector positive | 35/500, **7.0%** | 7/500, **1.4%** | 23/500, **4.6%** |
| Truncated | 96/500, **19.2%** | 29/500, **5.8%** | 60/500, **12.0%** |

Loops and truncations may overlap; their rates must not be added.

Three observations constrain the explanation:

1. **B completes more reliably but answers fewer questions correctly than stage 1.** Loop removal alone will not recover its math score.
2. English MATH is **18.0 / 15.8 / 16.4** for R3/B/stage 1. R3’s result does not support broad mathematical forgetting.
3. The Greek loss is not confined to the hardest level: reported Level-1 accuracy falls **37% → 26% for both**. Zero Level-5 training examples cannot, by itself, explain that pattern.

**Fix.** Partition existing errors by correctness, answer extraction, truncation, repetition, and difficulty, with paired Greek/English item IDs. Include Greek and English MATH in the first consequential pass readout. Treat math cut 2 as a coverage intervention, not an already established cure for the reversals.

For queued math generation, record acceptance rates by source and difficulty **before and after filtering**. Retain explicit hard-problem quotas through additional verification, rather than letting agreement filtering silently determine the curriculum.

### HIGH — The dose narrative uses misleading denominators, and the pass lacks explicit protection for the IF gain

**Evidence.**

- Suite + correcting: **6,752/403,727 = 1.67% of effective rows**, but **5.4/140.4 ≈ 3.85% of supervised tokens**.
- Nemotron A+B: **62.6/140.4 ≈ 44.6% of supervised tokens**.
- Personality: approximately **0.71%** of supervised tokens.
- Greek math: approximately **0.93%**.
- Personality presentations fall from **10,552 in B’s pass to 6,016 in R3**, approximately **43% fewer overall**, with changed membership and placement.

Assuming token-averaged loss, supervised-token shares are a better exposure measure than row shares, although they still do not measure gradient influence.

Also, “5% replay” is a **source sampling rate**, not the final mixture share. The disclosed historical pass contains:

\[
41,697-5,276-19,800-1,980=14,641
\]

replay rows: **35.1% of its rows**, or **30.2% of R3_pass**. Its supervised-token share is unspecified.

Finally, the disclosed R3_pass uses the old 41,697-row pass plus dialogue sets. It has **no explicit new Greek IF or Greek math allocation**. Recovery could therefore trade away the principal demonstrated R3 gain.

**Fix.** Publish pass totals by supervised tokens, language, task, and cumulative presentations. Define IF and math replay explicitly in the next recipe. Verify whether loss normalization makes those nominal token shares operationally meaningful.

### MEDIUM — H2 is overclosed; H3 is not yet cleared

**Evidence.** The reported new-target repetition counts—Greek IF **one turn**, math/suite/correcting **zero**—argue against literal repetitive targets as the main explanation. They do not exclude:

- Weak or incorrect reasoning trajectories.
- Inappropriate continuation or termination targets.
- Effects of planted-failure context.
- A mismatch between short training solutions and difficult generation tasks.

The Greek IF result is a **turn count without a turn denominator**, so it cannot be converted into a defensible row failure rate.

For H3, **0/40 pilot failures** only establishes that those 40 cases passed the stated checks. Equal format-gate stop rates, **43/50 for R3 and stage 1**, do not establish correct supervision on long mathematical or packed multi-turn examples.

**Fix.** Rename H2 to “literal repeated-target mechanism unsupported.” Keep broader data mechanisms open. Obtain the full **631 flagged + 1,200 plain** audit results, including final assistant turn-end labels after packing and truncation. Verify attention isolation separately from label masking.

Loss-masked context remains available to subsequent predictions; masking is not equivalent to removing that context.

### MEDIUM — H8’s own summary contradicts its counts

**Evidence.**

- False-challenge capitulation: R3 **4/12 = 33.3%**, B **2/12 = 16.7%**, stage 1 **3/12 = 25.0%**.
- Markdown: **52/120 = 43.3%**, **46/120 = 38.3%**, **62/120 = 51.7%**.
- Mean words: **144 / 141 / 169**.

R3 is between stage 1 and B on markdown and length, **but worse than both on capitulation**. “Between on every register measure” is false.

Nemotron’s **1,887/89,000 ≈ 2.1%** capitulation-style openings do not establish that those acknowledgements endorse false claims. Nor are the correcting set’s 23 acknowledgements of true corrections equivalent negative examples.

**Fix.** Distinguish justified acknowledgement from false capitulation. Audit matched challenge/response examples, with row IDs and explicit truth labels. Do not remove acknowledgement language wholesale.

### MEDIUM — The uncertainty and loss comparisons are insufficiently specified

**Evidence.** “Noise 0.1” does not identify a standard error, confidence interval, judge-repeat variation, or another quantity. Consequently, **−0.38 coherence is not automatically a four-sigma result**. Inspecting the ten largest gaps can diagnose failure modes but cannot estimate their prevalence.

Likewise, train losses **0.941 versus 0.944** concern different mixtures and masking and are not a controlled quality comparison. Personality holdout loss **1.534 versus 1.603** establishes better prediction on that holdout under comparable scoring, not better conversational behavior.

**Fix.** Report paired item changes and uncertainty at the dialogue level, accounting for repeated rounds. Treat the IFEval **+4.1 points** as an observed gain whose formal uncertainty remains unspecified.

## 3. What is good and should not be changed

- **Keep stage 1 as a control.** Its presence exposed that B’s finishing stage reduced loops in both languages.
- **Preserve verifiable Greek IF coverage.** The measured gain is useful; IFBench’s **9.3 = 9.3** limits its generalization claim.
- **Keep explicit per-turn masking and its audits.** The supplied evidence does not justify removing the mechanism.
- **Keep language accounting over supervised spans.** Mixed spans containing formulas, names, or Greeklish should not automatically be classified as defects.
- **Keep answer verification for math.** Repair difficulty-dependent selection; do not weaken verification to fill quotas.
- **Preserve completed datasets and predictions.** They provide the evidence needed for these comparisons.

The registry’s unique and effective row totals reconcile to **376,039 and 403,727**. The rounded block-token figures sum to approximately **140.6M**, compatible with a stated **140.4M** aggregate after rounding.

## 4. Answers to the specific questions

### Q1. Ranking H1–H8, and missing explanations

This ranks support from the packet, not calibrated causal probabilities. H1 and H4 substantially overlap.

| Rank | Hypothesis | Assessment |
|---|---|---|
| 1 | **H4: B’s pass reduced existing loops** | Strong descriptive evidence: Greek **23→7**, English **28→9**. Attribution is to the entire pass intervention, not ordering alone. |
| 2 | **H1: missing concentrated ending** | Best broad explanation for B’s behavioral advantage. **Pure ordering**, and especially “not the data,” remain unproven. |
| 3 | **H5: insufficient dialogue/personality exposure** | Plausible and quantitatively grounded. Personality exposure was reduced; dialogue sets have modest token share. No controlled dose-response result exists. |
| 4 | **H8: imported conversational habits** | Plausible given Nemotron’s token share, but source-level causal evidence is weak. Length and markdown actually improve from stage 1 to R3. |
| 5 | **H7: greedy decoding amplifies degeneration** | Untested on matched math prompts. Sampling could change absolute failure rates without eliminating the checkpoint difference. |
| 6 | **H6: noise or judge drift** | Material for small interview subsets. Cannot explain the counted generation failures by itself. |
| 7 | **H3: broken stop supervision** | Pilot evidence weighs against a widespread fault; long-row and packing-specific faults remain unresolved. |
| 8 | **H2: literal repetitive new targets taught loops** | Weakest current explanation. The reported audit argues against it; broader data-induced degeneration remains possible. |

The principal missing explanations/checks are:

- **Optimization duration and restart.** R3 has **20.7% more rows but 15.5% more rendered tokens** than stage 1. At perfectly full 65,536-token optimizer batches, that is approximately **3,488 versus 3,019 updates**. Actual packing determines the real count. Record actual updates, LR trajectory, and optimizer-state initialization. The identical cosine floor is not an independently supported culprit.
- **Changed retained data and multiplicities.** R3 explicitly has `greek_ours ×2`. The fifteen retained blocks total **327,316 unique / 347,116 effective rows**, versus the stated stage-1 total of 334,383 rows. “Same fifteen blocks” does not establish matched examples or exposures. Obtain the source-ID and multiplicity diff.
- **Length and packing interactions.** BFD is shared, but the new row-length and multi-turn distributions are not. Check clipping, lost terminal labels, pack boundaries, and actual cross-example attention isolation.
- **Evaluation/serving identity.** Compare checkpoint fingerprints, tokenizer/template versions, stop IDs, maximum generation length, and decoding arguments. This is a cheap exclusion check, not evidence that a serving error occurred.
- **Greek-conditioned math generation and scoring.** The bilingual results make this more compelling than a simple global-math-forgetting account.
- **Filtered difficulty and reasoning coverage.** Zero Level-5 examples and 42-word solutions expose a curriculum limitation; they do not prove the mechanism behind existing losses.

### Q2. Does R3_pass discriminate schedule from data? Which second run?

**It tests recovery by a package of changes. It does not cleanly discriminate schedule from data.**

Let **P** be the exact historical pass and **D** the added suite/correcting material:

| Base | Historical P | Augmented P+D |
|---|---|---|
| Stage 1 | B: available | Missing |
| R3 | Missing | R3_pass: queued |

**If funding one additional pass run, my first choice is `R3 + exact historical P`.**

It answers the most immediate question: **does the historical finishing intervention suffice, or is the augmented pass needed?**

- Compare it with queued `R3 + P+D` for the effect of augmenting the finishing package.
- Compare it with B for differences remaining after the same historical pass.

`Stage 1 + P+D` is also valuable: compared with queued R3_pass, it holds the finishing recipe fixed and tests whether R3’s preceding training history helps or hurts. Compared with B, it measures the augmented-pass effect from the historical base.

**Neither one alone proves pure ordering.** Extra data also adds updates. A strict ordering test requires the same training-example presentations, packed examples, total updates, and LR trajectory, with only their placement changed. For example, compare concentrated phases against a shuffled stream of the same packed-example multiset while preserving the same LR restart boundary. That entails a broader training control, not merely another approximately **5 nh** pass-and-evaluation run.

### Q3. Why could both lose Greek MATH while B improves MGSM?

**Leading inference:** the Greek adaptation improves familiar, relatively short response trajectories without preserving sufficient coverage of difficult Greek reasoning and answer completion. But the two recipes need not fail through the same immediate mechanism.

- B’s MGSM rises **0.468→0.524**, while Greek MATH falls **12.8→7.6** and loops decline.
- R3’s Greek MATH falls to **8.0**, with substantially more truncation, while English MATH rises to **18.0**.

For B, a shift in reasoning behavior, answer presentation, or Greek-conditioned problem solving is more plausible than increased looping. For R3, degeneration and truncation are additional plausible contributors.

**Crucially, the new math set cannot explain B’s earlier decline: B never trained on it.**

**Check:** pair Greek and English outcomes by underlying problem, then partition Greek failures into:

1. Incorrect completed answer.
2. Correct answer rejected by extraction/equivalence handling.
3. Truncation or repetition before a final answer.
4. A usable final answer followed by damaging continuation.

Inspect answer lengths and difficulty within these partitions. Do not compare only the surviving, completed outputs: that conditions on a behavior the training itself changed.

### Q4. Concrete next recipe

I would use a **broad main stage followed by a mixed Greek finishing stage with explicit IF and math retention**. The following is a starting candidate, not an experimentally established optimum.

**Main stage**

- Preserve R3’s broad mix and **29,773 Greek IF rows ×1**.
- Replace the existing Greek math block with cut 2, retaining verified solutions and explicit difficulty strata.
- Keep one epoch and the existing optimizer settings initially; avoid simultaneously changing the cosine floor.
- Make `greek_ours ×2` and all other multiplicities explicit.

**Finishing stage**

Use this core once per finishing epoch:

| Component | Effective rows |
|---|---:|
| Same frozen v3+v4 personality version ×4 | 6,016 |
| `greek_ours ×1` | 19,800 |
| `greek_rewrite ×1` | 1,980 |
| Suite ×2 | 5,622 |
| Correcting ×2 | 1,130 |
| **Core total** | **34,548** |

Then construct the finishing mixture by **supervised-token budget**:

- **60%** this core.
- **20%** Greek verifiable IF, balanced across constraint families.
- **15%** math: initially 10% Greek and 5% English, with explicit competition-math difficulty coverage.
- **5%** broad retention replay.

These percentages are proposed control settings, not findings. They make the intended trade-off measurable and avoid treating “5% of each source” as “5% of the pass.”

Start with **one finishing epoch at the historical peak LR**. A second epoch should be conditional on development evidence of further dialogue/loop improvement without IF or math regression. Assuming the main-stage copies remain unchanged, one finishing epoch gives each personality row **eight total presentations**, and each suite/correcting row **four**; two finishing epochs give **twelve and six** respectively.

Keep this mixed finishing distribution through the final updates. Do not append a personality-only sweep.

For math cut 2, set difficulty quotas before generation—for example, equal supervised-token allocation across levels within its competition-math stratum, alongside a separately specified elementary stratum. Failed hard candidates should receive further verification or remain unresolved, rather than disappearing silently.

Selection must jointly consider:

- Retaining the R3 IF gain.
- Recovering dialogue behavior.
- Reducing loops **without increasing premature stopping**.
- Greek **and** English math correctness.

No recipe can promise all four from these aggregates; those are the acceptance criteria.

### Q5. Single cheapest missing experiment

**Run a deterministic alternative-ending rescoring experiment on the existing Greek MATH outputs.**

Freeze a rule that ends an output immediately after its **first explicitly declared final answer**, where one exists, and apply the same equivalence scorer. Compare with the original score for all three checkpoints. Manually validate ambiguous extraction cases; never search intermediate calculations for a convenient correct number.

This needs no new training or model generation.

**Decision value:** if it recovers much of R3’s **24-answer deficit versus stage 1**, prioritize completion/termination behavior before attributing the loss to missing mathematical capability. If it barely changes results, curriculum and reasoning-path explanations gain weight. Analyze B separately: its **26-answer deficit despite fewer loops** may have another cause.

This is a diagnostic scoring intervention, not permission to replace the official benchmark result.

The queued hostile sampling run does **not** replace a matched Greek-MATH greedy-versus-sampling test: it changes the task as well as the decoding regime.

## 5. Open questions for the owner

1. What are the actual R3_pass rendered/supervised token totals, optimizer updates, LR trace, and optimizer-state initialization? Was “5% replay” drawn only from the historical sources?
2. What are the full masking-audit results, including terminal labels, clipping, and attention-boundary checks? Which concrete row IDs cover each edge case?
3. Are checkpoint copies, tokenizer/template hashes, stopping settings, scorers, and Greek/English problem IDs identical across comparisons?
4. What exactly does each reported noise band mean? Can you supply paired outcomes rather than only averages?
5. What changed in the retained fifteen blocks, including `greek_ours` multiplicity? Also, how do **1,319 v3 + 192 v4 = 1,511** reconcile with **1,504 unique personality rows**?
6. For math cut 2, what difficulty distribution is required before filtering, and what acceptance rates and retained solution lengths will be reported by stratum?