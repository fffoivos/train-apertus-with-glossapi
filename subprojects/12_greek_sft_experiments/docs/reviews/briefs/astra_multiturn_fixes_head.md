# Review brief: multi-turn conversation quality — what to fix in SFT and where

## The goal the owner set
Round two's model (arm B, Greek Apertus-8B SFT) scores well on Greek IFEval (63.7% strict) and holds its identity, but in real conversations it is not yet helpful, coherent, self-aware and pleasant to talk to: in the owner's 17 laptop chats 16 ended in a repetition or a stale copy; in 15 live dialogues with a profiled responder the model repeated itself, ignored changes of direction, misreported what it had said, answered with only a question, re-asked for given facts, and used steering closers («Θέλεις κάτι άλλο;», «Πες μου…»). The owner's instruction: park preference/RL; research what SFT data buys for multi-turn quality; apply it to the specific errors observed (docs/RESPONSE_PATTERN_CATALOGUE_20260910.md, 24 patterns over 196 answers); fold the response-pattern fixes (choice-offers instead of answers, «say this» prompts, closers, length mismatch) into the personality set; then review, then write the full pipeline description, then train.

## What you are reviewing
The document below (docs/MULTITURN_FIXES_20260910.md) with: §1 a literature digest from two of four research reports (the reports themselves are in docs/lit/; two more, on repetition mechanics and context-copying bias, are still pending), §2 the evidence, §3 the personality-set additions (v4 brief rules), §4 the conversation-set additions (dimensions D14–D16 on top of the correcting set's D1–D13, plus four rules derived from the literature), §5 generation hygiene. Also relevant and already reviewed by you: the correcting-set design (docs/CORRECTING_DATASET_DESIGN_20260910.md) and its pilot.

## What to judge (be adversarial and concrete)
1. Are the proposed fixes the right ones for the observed failures, and are they SFT-teachable at 8B? Name any fix that the literature says SFT cannot deliver, or that would need preference/RL, and any observed failure that has no fix in the plan.
2. Over-correction risk: the personality rules push toward brevity, no questions and no closers; the R0 picky-user benchmark already scores arm B as curt 27% of turns. Which rules risk making the model curt, evasive or unwilling to ask a needed grounding question? Propose the guard (e.g., the two-label scheme in §1.6, a length-match rule, minimum content rules).
3. Where each fix belongs: personality set (the model's story about itself and its manners, ×4 in the mix) vs conversation sets (suite, correcting set) vs the broad mix. Any fix placed where it will not take (too small a dose, wrong context length, single-turn where the failure is multi-turn)?
4. Dose and mixing: the plan is ~250 new personality rows, a scaled suite (≈3.5k rows) and a 1,500-dialogue correcting set (≈5k target rows) inside a ≈380k-row mix trained once from the base. Against the literature's numbers (§1.9), is this enough, too much, or wrongly balanced? What would you change?
5. Data hazards: any proposed row type that would teach a wrong behaviour (denial, over-apology, invented causes, unverifiable self-claims, refusing for lack of live info), or that contradicts the capability contract? Any way the judges/editors used to select rows import the biases §1.7 warns about?
6. Missing failure classes: from your knowledge of multi-turn failure taxonomies (MultiChallenge, MT-Bench-101, Lost-in-conversation causes), what is absent from D1–D16 and the personality rules?
7. Evaluation: how will we know it worked? Judge the proposed measurement (MultiChallenge-el 262 items internal, IFBench-el, the picky-user R1 metrics, live dialogues) and name what is missing (e.g., an Instruction Forgetting Ratio on our own rows, a held-out live-dialogue set, a curtness/tone floor metric).
8. The literature digest itself: flag any claim in §1 that is wrong, overstated or misapplied to our case.

## Disposition
BLOCKER/HIGH findings are applied to the personality v4 brief and to the suite/correcting generators before their scale runs (tonight and tomorrow); MEDIUM/LOW are logged in docs/DATA_TODO.md. Findings on §1 are corrected in the doc.

---

