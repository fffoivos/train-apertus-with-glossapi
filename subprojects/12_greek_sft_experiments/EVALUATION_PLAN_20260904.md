# Greek SFT — evaluation plan after round one (2026-09-04)

Written after the owner's review of the round-one readout. Three pieces of work. Plain names throughout: no run codes.

## What the owner decided

- Run the two public Greek instruction benchmarks on four peer models, so our numbers and theirs come from one harness.
- Run GreekMMLU on a minimal batch, ours and peers.
- Change the setup of the Greek reading evaluation: Claude in this session scores the answers directly, blind, instead of the headless judge, and adds a tone evaluation. The owner reviews Claude's scores afterwards.

## Names used below

| name | what it is |
|---|---|
| base model | the averaged Greek-CPT checkpoint, before any fine-tuning |
| the pick | fine-tuned on the Greek data, learning rate 1e-5, 2 epochs |
| epoch 1 / epoch 3 at 1e-5 | the same recipe stopped earlier / later |
| the lower-rate runs | learning rate 5e-6, epochs 1, 2, 3 |
| the two seed replicates | the pick's recipe with a cosine schedule, seeds 43 and 44, epoch 2 |
| the terminal-checkpoint run | the pick's recipe started from the last CPT checkpoint instead of the averaged one |
| the paired-English run | Greek data plus the English originals of the same rows |
| the adapted-imports run | Greek data plus the skills, French and German rows adapted to a Greek point of view |
| the raw-imports run | Greek data plus the same imported rows, unadapted |
| the four peers | Llama-Krikri-8B-Instruct, Meltemi-7B-Instruct-v1.5, Apertus-8B-Instruct-2509, Gemma-3-12B-it |

Gemma 3 has no 8B size. The 12B instruct is the nearest size above ours and is reported with that caveat.

## Part A — peers on Greek IFEval and Greek MGSM

**What:** the two ILSP benchmarks, scored with our harness, on the four peers. Each peer uses its own chat template, bf16, batch 32, one model per GPU, all four in one workbench.

**Why:** Krikri's published 67.5% comes from ILSP's harness, ours from mine. Scoring Krikri on our harness shows whether the two are comparable. Apertus-8B-Instruct is the most important baseline of all: it shows what Greek CPT plus our SFT bought over the vendor's own instruct model.

**Output:** one table, ours and peers, both benchmarks, prompt-level and instruction-level strict scores plus the strict average that the Krikri card reports. If our Krikri number lands more than a few points from 67.5%, the harnesses differ and the readout says the comparison holds on our harness only.

**Cost:** about 1 node-hour, about CHF 3. One debug workbench, under 90 minutes, attended.

**Risks:** Gemma-3-12B-it is a multimodal checkpoint; the text-only loader may need a flag. Krikri, Meltemi and Gemma download inside the workbench, about 16 GB each. Access to all four was verified on 2026-09-04 with the owner's token, including the Gemma license.

## Part B — GreekMMLU, minimal batch

**What:** the CPT card's frozen fp32 scorer on four models: the pick, the adapted-imports run, Krikri-Instruct, Apertus-8B-Instruct. Same scorer, same decontaminated 16,159-question set as the CPT model card, so the fine-tuned models can sit on the card next to the CPT checkpoints.

**Why only four:** the scorer takes about 2.8 hours per model and cannot be split across GPUs, so each model costs the same. The knowledge score barely moves under SFT, so two of ours suffice. Meltemi and Gemma add little here and are left out; base-model peers already exist from the CPT analysis (our CPT 56.8%, Apertus base 52.8%, Krikri base 48.6%).

**Cost:** about 3 node-hours, about CHF 8. One normal-partition workbench of about 3 hours 15 minutes, four models in parallel, one per GPU, attended by the loop.

**Owner notice:** this is a job over two hours. The owner's "the evaluations are in" on 2026-09-04 is taken as the go. It starts only after Part A has shown the peer models load and score correctly.

## Part C — the reading evaluation, redone by Claude, with tone

**What changes from round one:**

1. **Rater.** Claude in this session reads and scores every answer directly. No headless judge, no delegated model.
2. **Blind.** Run labels are hidden and the order of the answers is shuffled separately for each prompt. Labels are revealed only after all scores are written.
3. **Coverage.** All 13 runs that have reading outputs, not 7: the base model, the six grid checkpoints, the two seed replicates, the terminal-checkpoint run, and the three data-mix runs. All 40 prompts, 31 in Greek and 9 in English, French and German. That is 520 answers.
4. **Rater noise floor.** The two seed replicates are the same recipe. Whatever difference Claude scores between them is Claude's own noise, and every other difference is read against it.
5. **Tone axis, new.** Three checks on every answer:
   - **Warmth**, 1 to 5. Good when high. A warm answer speaks to the person, not at them.
   - **Direct commands**, flagged. Bad. Second-person orders the user did not ask for: "Κάνε αυτό", "Πρέπει να", "Μην". Steps the user asked for, such as a recipe or a procedure, do not count. The owner confirms or corrects this reading of "direct command" in the review.
   - **Chatbot mannerisms**, flagged with the phrase quoted. Bad. Openers such as "Great!", "Certainly!", "Φυσικά!", "Βεβαίως!", "Τέλεια!", "Εξαιρετική ερώτηση", closers such as "Ελπίζω να βοήθησα" or "Αν χρειαστείτε κάτι άλλο", and exclamation-mark enthusiasm.

**Axes kept from round one:** answers the prompt, Greek quality, stays in the prompt's language, honours the prompt's constraints where there are any, stops cleanly.

**Also, automatically:** a mannerism lexicon count over every generated text we have per run, the 50 dev prompts, the 40 reading prompts and the 40 interviews. Deterministic string matching, reported per run as a rate. This is a cheap second signal on tone that does not depend on any rater.

**Output for the owner's review:** one page per prompt showing every answer with Claude's scores, the quoted evidence for each flag, and the run label revealed. A summary table per run: mean warmth, share of answers with a command, share with a mannerism, and the kept axes. The scores also land as JSON in the results directory.

**Cost:** no GPU. Reading time on Claude's side only.

## Order

1. Part A opens first. While it runs, Part C starts on the Mac.
2. Part B opens when Part A has scored all four peers without errors.
3. Part C's page goes to the owner as soon as scoring is done, independently of A and B.
4. The round-one readout is updated with the peer table and the GreekMMLU table when they exist.

## Budget

| part | node-hours | CHF |
|---|---|---|
| A, peers on the two benchmarks | about 1 | about 3 |
| B, GreekMMLU on four models | about 3 | about 8 |
| C, reading and tone | 0 | 0 |
| total | about 4 | about 11 |

Used so far CHF 47.81 of the 90 cap. After this plan, about CHF 59, leaving about CHF 31 for the preference round or the filtered-data arm.
