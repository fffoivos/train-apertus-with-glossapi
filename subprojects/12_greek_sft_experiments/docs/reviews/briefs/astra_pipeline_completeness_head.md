# Review brief: is this a good and complete SFT training set and pipeline for the Greek Apertus-8B?

## The question the owner is asking
Before the next training run (planned for Saturday 12 September, one run from the Greek-CPT base), the owner wants an independent judgement of the whole programme as described in the document below: the foreign and Greek datasets gathered, the annotation and filtering, the adaptations and corrections, the training runs so far and their results, and the planned final training set. The verdict we need: (a) does this constitute a good and complete training dataset for a Greek instruction-following assistant at 8B; (b) what is missing, wrong or risky enough that it should be fixed BEFORE training rather than after; (c) are we ready to train, and if not, what exactly would make us ready.

## Context you should know
- The model's current state (arm B): Greek IFEval 63.7% strict average (Krikri 66.8%, Apertus-8B-Instruct 56.0%), Greek MGSM 0.524 (Krikri 0.676), GreekMMLU pending (round-one SFT 56.0%, base 56.8%, Krikri 52.0%), conversational quality weak (repetition, stale intent, self-report errors; the picky-user and live-dialogue measurements are in §7).
- Three sets are being generated tonight and tomorrow with reviewed generators (correcting set 1,500 dialogues, conversation suite ≈ 4,000 attempts, personality v4 ≈ 200 rows); their final counts are marked "to be assembled" in the document. Judge the design and the plan for them, not the counts.
- Earlier astra reviews of the individual sets exist and their dispositions were applied (listed in §5 of the document); do not re-review those sets row by row, judge whether the programme as a whole is complete and coherent.
- Constraints that stand: SFT only for this round (no preference/RL), one training run, budget about 8 node-hours, the four new Greek benchmarks are evaluation-only.

## What to judge (be adversarial and concrete; cite the document's sections)
1. Coverage: which capabilities a Greek assistant needs are absent or thin in the planned set (by task type, by language surface, by conversation shape, by domain), against the peers' recipes you know (Krikri, Meltemi, Tülu/OLMo Dolci, SmolTalk) and the failure evidence in §7.
2. Balance and weights: the proposed block weights and the Greek/English ratio; the personality set at ×4; whether 30k Greek IF rows next to 46k English ifeval-like rows and 14k math rows are the right doses; anything that will overfit or be drowned.
3. Quality and provenance: are the screens, edit passes, decontamination and verification adequate for each block; where does a judge label silently act as a filter; where is a source's licence or version unresolved; where is contamination against the evaluations plausible.
4. The Greek point of view and adaptation: is the "Greek vantage" share sufficient, and is the adaptation evidence (E3 vs E3′) strong enough to justify the choice.
5. Training recipe: one run from the base with the personality fold-in vs stage 1 plus a Greek pass (the Greek pass gave +3.8 IFEval points in round two); epochs, learning rate, packing, loss masking; what should be measured after training to know it worked (and what baseline).
6. Risks that should block training: list them with the concrete check or fix each one needs.
7. What is fine and should not be changed.

## Disposition
BLOCKER findings are fixed before the training launch; HIGH findings are fixed before launch where they concern assembly or recipe, otherwise logged with an owner decision; MEDIUM/LOW logged in docs/DATA_TODO.md. The document will be updated with final counts before the launch and the recipe will be disclosed to the owner as a parameter table.

---

