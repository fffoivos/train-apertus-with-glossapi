# Astra review: convskills_pilot

Date 2026-09-10 01:44 · model gpt-6-astra (asserted from rollout rollout-2026-09-10T01-36-26-01a08850-b731-79c2-b80b-cd75c4137e19.jsonl) · effort xhigh · 7.6 min · prompt 139,933 chars · limit deltas {('codex_bengalfox', '300'): 0.0} · brief `../docs/reviews/briefs/astra_convskills_pilot.md` · sample 60 rows of `convskills/v1/rows_all.jsonl` seed 1

## 1. Verdict

**Do not scale the queued suite yet; retain the pilot and repair the specific gates below.** The strongest inspectable material is S3: all 16 complete rows perform the requested surface transformation, although one loses information. S4 has a more serious setup defect: in **4/4 excerpts where the stop instruction identifies the tic, neither preceding assistant answer contains it**. The review package itself also prevents approval: **41/60 records are truncated**, including every S1 target and every complete S5m target. These are defects in the supplied evidence, not proof that `rows_all.jsonl` is corrupt. I reviewed the pasted text, visible metadata and edit logs; I did not inspect the underlying files, checker implementation, rejected rows, training masks, or external factual sources.

## 2. Findings ranked by severity

The denominators matter:

| Lane | Sample rows | Inspectable evidence | Observed result |
|---|---:|---|---|
| S1 | 11 | No recall target visible | Cannot assess recall accuracy, summarisation or counting. |
| S2 | 11 | 8 acknowledgments and 10 complete subsequent constrained answers; no complete dialogue | No clear format violation in those 10 substantive answers. Revocation is unassessable. |
| S3 | 16 | 16 complete dialogues | 16/16 perform the requested surface edit; **1/16 loses an explicit qualifier**, under the semantic-preservation rubric below. |
| S3c | 7 | 4 complete turn sequences; 3 partial | **1/4 complete sequences loses an epistemic qualifier**; 2/4 exceed a proposed 60% ceiling for “half length,” overlapping that failure. |
| S4 | 5 | 4 identifiable stop requests; 3 complete acknowledgments | **4/4 lack the named tic in preceding answers**; **1/3 acknowledgments is empty**. |
| S5m | 10 | Initial facts in all 10; two partial final answers | No complete memory-use target can be graded. |

These are sample observations, not estimates of population failure rates. Missing endings are not passes.

### BLOCKER — The export prevents the requested audit

**Evidence:** Only **19/60 records reach a complete JSON ending**. `S3c_00078` additionally exposes its complete conversation and metadata but cuts off inside `edit_changes`, giving **20/60 complete turn sequences**.

All **11 S1** excerpts end before the recall target. All **10 S5m** excerpts lack a complete final answer. For example, `S5m_00080` stops during the proposed outing; `S5m_00032` stops during its language accommodation. None of the 11 S2 excerpts exposes a revocation sequence.

**Fix:** Re-export the same 60 IDs without per-record clipping, preferably as an attached JSONL artifact. Include complete turns, `meta.kind`, base IDs, supervision information and correction provenance. Validate record completeness before constructing review packets. Do not repair this by sampling only shorter dialogues: that would conceal precisely the long-context skills under review.

### HIGH — S4 does not show the established behaviour it claims to teach stopping

**Evidence:**

| Row | User identifies | Occurrences in the two preceding assistant answers |
|---|---|---:|
| `S4_00048` | «Χαχα» | 0 |
| `S4_00074` | «Εντάξει» | 0 |
| `S4_00014` | «Αν θες, το δουλεύουμε κι άλλο» | 0 |
| `S4_00030` | «Εντάξει» | 0 |

That is **4/4 assessable setups**, or at least **4/5 sampled S4 rows**. `S4_00023` cuts off before identifying the prohibited expression.

A user may legitimately prohibit an expression prospectively. But these examples do not demonstrate stopping an established repeated tic; they largely reduce to another standing prohibition.

Additionally, `S4_00030` has:

> `"role": "assistant", "content": ""`

That is **1/3 visible acknowledgments**. An empty acknowledgment can make conversational sense here, but whether it trains immediate end-of-turn emission depends on the actual loss mask.

All **10 visible pre-stop assistant objects** across the five S4 rows lack an explicit `train: false` field. A separate mask may exist; its absence from this export does **not** prove those tokens are supervised.

**Fix:**

- For the established-tic subtype, require the planted expression in the intended position in at least two preceding answers.
- Preserve those context turns through editing and verify their actual training-token masks.
- Check every subsequent applicable answer for recurrence.
- Handle “no acknowledgment needed” by explicitly masking/omitting the empty target or combining the instruction with a substantive request. Do not accidentally supervise an empty answer.
- Retain prospective prohibitions as a separately labelled subtype, not evidence that repeated-tic recovery works.

### HIGH — Edit verification needs semantic invariants, not just successful deletion or shortening

**Evidence:**

- **`S3_00117`:**  
  «Έλεγξε **ζωντανά** διαθεσιμότητα, ισχύ και πρόσφατες αξιολογήσεις κάθε φορτιστή.»  
  becomes:  
  «Έλεγξε διαθεσιμότητα, ισχύ και πρόσφατες αξιολογήσεις κάθε φορτιστή.»

  The banned word disappears, but so does the explicit requirement for current availability. A faithful replacement is:

  > «Έλεγξε τη διαθεσιμότητα εκείνη τη στιγμή, την ισχύ και τις πρόσφατες αξιολογήσεις κάθε φορτιστή.»

  This is **1/16 complete S3 rows**, and **1/3 `without` rows**, with observable information loss under a preservation rubric.

- **`S3c_00078`:**  
  «Οι βάσεις **συνήθως** ενημερώνονται … **χωρίς ενιαίο ρυθμό**.»  
  becomes:  
  «Οι βάσεις ενημερώνονται σε διαστήματα από μία εβδομάδα έως τρεις μήνες.»

  The shortened version presents the interval without either qualification. This is **1/4 fully visible chains** with a clear change in certainty. I am assessing the transformation, not endorsing the underlying interval claim.

- **`S3c_00048`, complete first revision:** The original day-three checklist includes «εξουσιοδότηση». The revision deletes that document from the checklist instead of replacing its name. The earlier requirement for «νόμιμη άδεια» survives, so this is a narrower loss of the explicit bring-along instruction—not total removal of the prerequisite.

- **`S3c_00094`, partial final revision:**  
  «ακολουθεί απλή οδηγία **χωρίς χειρονομία**»  
  becomes:  
  «ακολουθεί απλή οδηγία».

  The visible milestone bullet loses a condition. Because the answer is truncated, I cannot rule out a later qualification elsewhere.

**Fix:** For each edit, retain a small set of protected propositions: quantities, actors, conditions, negation, uncertainty, prerequisites and relevant safety instructions. Require equivalence for formatting/deletion edits; allow selective omission for summaries, but preserve the qualifications attached to retained claims. Validate each chain against the immediately preceding answer **and** the accumulated constraints.

### HIGH — Final acceptance must be demonstrated after correction and assembly

**Evidence:** The brief explicitly reports mechanical verification **before correction**. It also reports that `S[1-4].jsonl` excluded S3c and S5m from the first correction pass.

The supplied numbers are internally consistent: the rounded percentages imply accepted counts of **127, 188, 230, 95, 75 and 143**, totalling **858/974 attempts**. That reconciliation supports the arithmetic; it does not establish that every final row was corrected, remained valid, or reached training.

Visible correction evidence also shows why a final replay matters:

- `S3_00005` corrects «τα πιάτα θα πλυθεί» to «τα πιάτα θα πλύνει».
- The same base poem in `S1_00114` still contains «τα πιάτα θα πλυθεί».
- `S3_00163` explicitly logs removing assistant self-reference: «Εγώ πάντως θα σου πρότεινα» becomes «Παρ’ όλα αυτά, είναι προτιμότερο». That is a stylistic intervention beyond a narrowly grammatical correction.

These observations do not prove that an entire lane skipped correction. They demonstrate inconsistent final treatment and editor scope drift.

**Fix:** Produce a final manifest with explicit lane names, accepted counts, correction status and content hashes. Rerun all applicable checks on the exact assembled training representation. Lock user messages, planted contexts and quoted source spans; if an assistant source is corrected, revalidate any recall target that refers to it. Keep grammatical correction separate from stylistic rewriting.

### MEDIUM — “Half length” currently admits substantially longer answers

Using whitespace-separated word counts on the immediately preceding revision:

| Row | Before → after | Remaining length |
|---|---:|---:|
| `S3c_00053` | 79 → 52 | 65.8% |
| `S3c_00078` | 76 → 47 | 61.8% |
| `S3c_00002` | 87 → 35 | 40.2% |
| `S3c_00091` | 67 → 33 | 49.3% |

Thus **2/4 complete chains** fall outside a proposed **40–60%** acceptance band. That band is my recommendation, not a claim about the existing checker.

**Fix:** Define the tolerance explicitly and measure against the previous answer, not the original base. Preserve semantic invariants before optimising length. Do not demand exactly 50%, especially for short text or poetry.

### MEDIUM — Diversity is mostly in topics, less in the conversational operation

**Evidence:**

- All **16/16 S3** edit requests begin «Ξαναπές το».
- All **7/7 S3c** excerpts use the same operation order: remove a word, then shorten.
- All **10/10 S5m** profiles package name, city, limitation and budget into the first turn using just two introductory templates.
- **8/10 S5m** acknowledgments begin «Εντάξει».
- `S5m_00117` retains the incorrect vocative «Εντάξει, Δημήτρης.»
- The Mycenae prompt recurs in `S1_00114`, `S1_00028` and `S2_00205`; the Android prompt recurs in `S2_00135` and `S1_00123`; the Naxos prompt recurs in `S5m_00072` and `S1_00019`.

Reuse is expected from a base pool. These examples establish reuse, **not train/test leakage**.

Some distractors also introduce competing personal context: `S5m_00096` starts with Heraklion and subsequently says «Δουλεύω για καλοκαίρι σε ξενοδοχείο στη Ρόδο». Residence and current location can coexist, but the eventual request must distinguish them.

**Fix:** Split by base identity before expansion; cap repeated base exposure; vary edit phrasing and operation order. Distribute memory facts across turns and include explicit updates, third-party facts and irrelevant facts. Use coherent distractors when the task does not intentionally test ambiguity.

### MEDIUM — Some “child” edits simplify length more than vocabulary

**Evidence:** Of the **3 child rows**, two retain appreciable unexplained terminology:

- `S3_00191`: «TDS», «διαλυμένα άλατα», «μόλυβδο».
- `S3_00081`: «κατάστρωμα», «ακρωτήριο», «φορτία και προμήθειες».

These are **2/3 qualitative concerns**, not two objective format failures. Technical words are not automatically unsuitable for children, but the answer should explain unfamiliar words that carry the explanation.

**Fix:** Evaluate accessibility separately from shortening. For `S3_00191`, for example:

> «Ο μικρός αριθμός δεν σημαίνει ότι το νερό πίνεται. Ο μετρητής δεν ελέγχει όλους τους κινδύνους, όπως τα μικρόβια.»

## 3. What is good and should not be changed

- **Keep S3’s restrained transformations.** The six `to_list` rows generally preserve the source well. `S3_00212`, `S3_00206` and `S3_00135` are useful examples; the latter also handles nested lists.
- **Keep constrained answers substantive.** `S2_00135` gives three complete one-sentence answers with useful qualifications. The visible 20-word answers in `S2_00117` address the actual requests.
- **Keep natural, instruction-compliant acceptances:** «Θα απαντώ με μία πρόταση.» and «Θα σας απευθύνομαι στον πληθυντικό.» are appropriate.
- **Keep chained edits as a distinct evaluation category.** All four fully visible chains retain the word prohibition through the final answer.
- **Keep the intended S5m distinction between remembering and using facts.** The visible part of `S5m_00032` actually adapts the plan through «προτίμησε ελληνόφωνο οδηγό». That is stronger than merely repeating “you do not speak English”; its budget handling remains unreviewable.
- **Keep per-lane seeds, base-level holdout separation and exclusion of unverified targets.** Improve the diagnosis of rejected rows rather than admitting them merely to raise yield.

## 4. Answers to the specific questions

**1. Do outputs teach the named skills?**

S3 largely does; S3c demonstrates cumulative lexical constraints but needs stronger preservation checks. S4 currently lacks evidence of the behaviour being stopped. S1 and complete S5m behaviour cannot be judged from this export. S2’s visible constrained answers are encouraging, but there is no evidence here for successful revocation or complete-dialogue persistence.

**2. Which verification rules should change?**

| Lane/check | Recommended rule |
|---|---|
| S1 recall/list | Compare against source-turn IDs and required propositions. For summary requests, require faithful summaries rather than copied imperative prompts. Lexical overlap should be a warning signal, not the acceptance criterion. |
| S1 exact quote/count | Use the final corrected history; distinguish speaker, turn and scope. Count prior user messages according to the explicit wording «πριν από αυτό». |
| S2 Greeklish | Keep “no Greek letters” if that is the instruction. Use Unicode-aware detection; separately verify that the answer is intelligible transliterated Greek. Do not require one canonical transliteration. |
| S2 no questions | Specify whether the rule bans questions addressed to the user or every interrogative sentence, including quoted dialogue. Check speech acts as well as `;`, `;` and `?`. |
| S2 one sentence | Handle URLs, abbreviations and Greek punctuation without counting them as ordinary sentence boundaries. Reject run-ons that merely evade punctuation checks. |
| S2 persistence/revocation | Track activation and revocation explicitly; evaluate every applicable assistant turn, including acknowledgment. Revocation should permit normal behaviour, not force the opposite format unnecessarily. |
| S3/S3c | Combine transformation checks with proposition preservation, cumulative constraints and explicit length tolerances. |
| S4 | Check the pre-stop setup, loss mask and post-stop behaviour. Absence after the instruction alone is insufficient. |
| S5m | Require the relevant facts to affect the recommendation. Test paired profiles: changing diet, budget or transport ability should change the appropriate decisions, not just the introduction. |

**The 17.9% Greeklish and 25% S1-list yields cannot be diagnosed from accepted excerpts.** No rejected examples or checker reasons are supplied, and no relevant accepted targets are visible. Audit **all 32 rejected Greeklish rows and all 15 rejected list rows**, alongside the 7 and 5 accepted rows. This is small enough to classify each rejection as writer failure, checker false rejection, or ambiguous specification.

For S2 suffix acknowledgments, `S2_00152` merely promises the phrase inside quotation marks; `S2_00132` actually ends with it. Define whether the former is acceptable rather than letting incidental string matching decide.

**3. Did the correction editor break constraints?**

No supplied before/after evidence conclusively attributes a broken standing instruction, quote, tic or memory fact to the editor. The relevant records and logs are largely missing.

What is verified: inconsistent correction of a repeated poem, a surviving vocative error, and logged stylistic changes beyond grammar. What remains inference: that the editor removed planted tics or caused the semantic losses. Preserve raw and corrected versions to establish causality.

**4. Is the dialogue natural and diverse?**

The topics are varied; the operation templates and profile construction are repetitive. Base reuse needs exposure controls and split provenance. Topic switching is legitimate, but accidentally changing the user’s apparent circumstances makes memory labels ambiguous.

**5. Drop, merge or redesign lanes—and how many rows?**

Drop **no entire skill** on this evidence. Redesign S4 before scaling. Broaden S3c beyond one operation order, and S5m beyond opening-turn profile retrieval. S3 and S3c may share implementation, while retaining distinct sampling and evaluation.

A provisional allocation of **accepted training rows**, after the gates pass:

| Lane | 3,000-row arm | 4,000-row arm | 5,000-row arm |
|---|---:|---:|---:|
| S1 | 600 | 800 | 1,000 |
| S2 | 750 | 1,000 | 1,250 |
| S3 | 375 | 500 | 625 |
| S3c | 375 | 500 | 625 |
| S4 | 300 | 400 | 500 |
| S5m | 600 | 800 | 1,000 |

These are experimental allocations, not evidence of an optimum. Balance S2 by subtype **after filtering**, put revocation in at least half its dialogues, and limit easy formatting conversions within S3. Track supervised tokens as well as rows: long context answers can otherwise dominate the intended skill targets.

Before scaling, review at least **60 complete accepted rows per lane**, stratified by subtype, plus the rejected-row audits above. Evaluate against held-out base families and the owner’s stress chats.

## 5. Open questions for the owner

1. Can you supply the same 60 records untruncated, plus the 47 rejected Greeklish/list examples and their checker reasons?
2. Where are the planted S4 tics and their supervision masks represented in the final training artifact?
3. Were all constraints rerun after correction and final assembly? What manifest proves coverage of all six lanes?
4. Which assistant turns contribute loss: generated skill targets, acknowledgments, neutral context answers, or some combination?
5. Is the 10% holdout grouped by original base identity across every lane and correction variant?
6. What are the exact semantics of `no_questions`, suffix acceptance, “half length” and S5m location updates?
7. Are model/version, generation parameters and editor provenance recorded per row, and what held-out improvement will determine whether the training arm succeeds?