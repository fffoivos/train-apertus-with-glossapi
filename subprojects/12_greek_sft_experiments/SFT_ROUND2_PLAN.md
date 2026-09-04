> **Status 2026-09-05:** §1 (dataset selection), §1a, §2 (filtering), §2a/§2b, §6 (speeds) and §7 (decisions) are SUPERSEDED by `docs/ROUND2_DATA_PLAN_20260905.md`, the document under review. §0 (shape of the round), §3 (personality set), §4 (preference) and §5 (evaluation gates) still stand and are referenced from there.

# Greek SFT, round two: plan (draft 2, 2026-09-04)

Owner's brief: select broad public SFT suites without being conservative; filter or adapt only the rows that pull hardest
against Greek-centredness; then tune a personality that knows it is a Greek model made by ΕΕΛΛΑΚ, running locally, talking
to Greeks. Round one showed why: a generic recipe lands where Apertus-Instruct is (56% Greek IFEval), the peers' edge comes
from constraint data plus preference optimisation, and raw imported rows pull the voice toward an American assistant.

## 0. Shape of the round

| stage | data | purpose | GPU |
|---|---|---|---|
| 1. broad SFT | 0.25M to 4M public rows, English-heavy, filtered | skills that transfer: instruction following, math, code, formats, tools | 6 to 100 node-hours by tier |
| 2. Greek pass | our 20k adapted rows + personality set + filtered native Greek + 10% replay of stage 1 | voice, vantage, identity, Greek conventions; low learning rate | under 2 node-hours |
| 3. preference | checker-verified constraint pairs + Sol-judged Greek pairs + identity pairs, DPO, 100k to 270k pairs | pass Krikri on instruction following, hold the voice | 12 to 40 node-hours |

Each stage ends with the round-one evaluation suite plus a new identity probe. The base stays the averaged CPT checkpoint.

## 1. Dataset selection

What is actually available. Gemma's and Qwen's own post-training data are not released. What exists from those families is
other people's data generated with their models, and Qwen3-generated rows are inside SmolTalk2. Verified on Hugging Face
today:

| source | rows | licence | what it brings | note |
|---|---|---|---|---|
| swiss-ai/apertus-sft-mixture | 3.9M | ODC-BY | the recipe Apertus-Instruct was trained on: SmolTalk2, Tulu-3 (OLMo-2 mixture), EuroBlocks, roughly 65/23/11 | the "copy them" backbone; we already sample it as apertus_en |
| allenai/tulu-3-sft-mixture | 0.94M | ODC-BY | Krikri's main English source; personas math and IF, coding, WildChat-derived chat | decontaminated against IFEval by its authors |
| allenai/Dolci-Instruct-SFT | 2.15M | ODC-BY | OLMo 3's SFT set, newer than Tulu 3, more math/code/tool use | fully open pipeline, same spirit as Apertus |
| HuggingFaceTB/smoltalk2 | 4.78M | mixed | OpenHermes 2.5, Magpie Ultra, everyday, systemchats, multilingual-8, tool calling, table tasks; "think" and "no_think" variants | take the no_think subsets only; Qwen3-32B generated |
| argilla/ifeval-like-data | 0.55M | Qwen 2.5 licence, attribution | constraint-following rows of the IFEval shape, generated with Qwen2.5-72B, unfiltered so prompts can carry conflicting constraints | the single source most tied to the Krikri gap; keep only rows the IFEval checkers verify as satisfied |
| nvidia/OpenMathInstruct-2 | 22M | CC-BY-4.0 | grade-school to competition math with solutions | for the MGSM gap; sample, do not take whole |
| microsoft/orca-agentinstruct-1M | 1.05M | CDLA-permissive-2.0 | agentic multi-step tasks | breadth |
| open-thoughts/OpenThoughts3-1.2M | 1.2M | Apache-2.0 | long reasoning traces | most rows exceed our 4,096-token window; take the short tail or skip |
| nvidia/Nemotron-Post-Training-Dataset-v2 | 6.3M | CC-BY-4.0 | very large, math/code/chat, five European languages | optional bulk; no Greek |
| CohereLabs/aya_collection, greek split | 3.6M | Apache-2.0 | the only large native-Greek instruction set | templated task instances, uneven quality; sample and filter hard |
| allenai/WildChat-1M | 0.84M | ODC-BY | real user prompts | only 619 Greek conversations; useful as prompt source for DPO, not as SFT bulk |
| our wave 1 | 20k | mixed | adapted to the Greek vantage | stage 2 core |

Excluded from training and used for decontamination: every ilsp evaluation set (mmlu_greek, arc_greek, hellaswag_greek,
ifeval_greek, mgsm_greek, truthful_qa_greek, medical_mcqa_greek, greek_civics_qa), google/IFEval and GSM8K test in English
because the Greek benchmarks are their translations, our 40 reading prompts, the 50 dev prompts, and the 40 interview seeds.

Three tiers for stage 1, the owner picks one:

| tier | composition | rows | tokens | node-hours per epoch |
|---|---|---|---|---|
| S | Apertus mixture sample stratified by source, plus ifeval-like 30k, math 30k | 250k | 0.15B | 6 |
| M | Apertus mixture sample 700k, Tulu-3 personas and IF, ifeval-like 100k, OpenMathInstruct 100k, tool calling 50k | 1M | 0.6B | 23 |
| L | Apertus mixture whole, plus all of the above additions | 4.5M | 2.7B | 100 |

Recommendation: run S and M as a ladder, measure after each, decide L on the curve. The owner's "no reason to be
conservative" argues for M as the floor. Token counts assume 600 tokens per row after the 4,096-token filter; rows longer
than the window are dropped, not truncated, as in wave 1.

### 1a. Stage-1 mix, recalculated 2026-09-04 late (owner rule: verified answers, or a recent generator; old and unchecked is out)

| block | source | generator, year | checked | rows |
|---|---|---|---|---|
| verified constraints | Dolci Precise IF | 2025 models | constraint checkers | 137k |
| verified constraints | ifeval-like filtered | Qwen2.5-72B, 2024 | constraint checkers | 56k |
| math | OpenMathInstruct-2 | Llama-3.1-405B, 2024 | final answer vs ground truth | 100k (replaces the 60k persona GSM, GPT-4o unverified) |
| chat and advice | Nemotron IF-Chat v3 chat | GLM-5, 2026 | reward model best-of-N; our Luna screen, Sol on technical rows | 150k (about 375k rows have their prompt; hash recovery of the WildChat-seeded rest is optional) |
| chat, human-written | OpenAssistant, screened | volunteers, 2023 | our screen | about 4k |
| coding | Dolci "Python Algorithms" (186k available) | 2025 | unknown; Sol spot-check of 300 rows first | 60k if the spot-check is clean, else Sol-generated |
| coding, extra | Sol-generated answers to code prompts | gpt-5.6, 2026 | Sol | 20k to 40k, if needed |
| rewriting, summarising | Nemotron rows Luna labels rewriting, plus Sol-generated | 2026 | Sol | 20k + 20k |
| reasoning | Dolci "Verifiable Reasoning" (311k available) | 2025 | Sol spot-check of 300 rows | 30k |
| reasoning | Dolci logic puzzles and word sorts | generator | brute-force checker | 11k confirmed |
| tool use | Dolci Tool Use | 2025 | Luna identity screen | 30k |
| science | Dolci OpenThoughts3+ Science | 2025 | Sol screen | 15k |
| other European languages | SmolTalk2 multilingual-8 | Qwen3-32B, 2025 (to confirm) | Luna | 25k |
| other European languages | Nemotron non-English European rows | GLM-5, 2026 | Luna | 10k |
| safety | Dolci WildGuardMix, CoCoNot, screened | 2024 | Luna | 10k now; regenerate in our voice with Sol in stage 2 |
| Greek | our adapted set | Sol, 2026 | ours | 20k, seen twice |
| **total** | | | | **about 720k to 760k** |

Dropped under the rule: Magpie Ultra (Llama-3.1-405B 2024, style-filtered only), OpenHermes (GPT-4/3.5 2023), Tulu WildChat
(GPT-4 answers 2023-24), FLAN (2015-era labels, 12% wrong under Sol), EuroBlocks fr/de (2024 synthetic), Dolci persona
math and Evol-CodeAlpaca and persona Python (GPT-4/4o, unverified), TableGPT.

Sol generation budget: round one produced about 3k adapted rows a day at 16 workers, so roughly 5k a day at 24; a
40k to 60k generation programme is one to two weeks and competes with the personality set. Priority order: rewriting
and summarising (needs nothing but source texts), safety refusals in our voice, coding only if the Dolci spot-check
fails.

## 2. Filtering: what pulls against Greek-centredness, ranked by impact

Impact = how strongly a row fixes the assistant's world × how many such rows there are. Only the top of the list is worth
adapting; the rest is dropped or downweighted, because adaptation is the slow part: wave 1 delivered about 20k adapted rows
in roughly a week of pipeline time at 16 generation and 24 edit workers. Adapting 200k rows would take months.

1. **Identity and self-description.** "I am an AI developed by …", "As a language model I …", system prompts naming a
   foreign product or lab. Strongest pull, since identity is what stage 3 must own outright. Action: drop every such row
   from stage 1 by pattern, and replace with the personality set. Zero adaptation cost.
2. **Advice bound to a foreign state.** Law, tax, healthcare, benefits, schooling, licences, consumer rights, banking, with
   agencies and instruments named (IRS, NHS, 401(k), FDA, ZIP codes, imperial units, dollar prices in everyday advice).
   Strong pull and common in Tulu, WildChat-derived and persona chat. Action: detect with a lexicon plus a small classifier
   trained on Sol-labelled samples; drop the bulk from stage 1; adapt a fixed budget of 5k to 10k rows in the categories
   our Greek data lacks, civic procedure first, through the existing pipeline under the D24 vantage rules.
3. **Everyday life with American defaults.** Names, food, sports, holidays, school life, weather in Fahrenheit. Moderate
   pull, very common in everyday and systemchats subsets. Action: cap their share at a few percent of stage 1; our adapted
   no_robots and everyday rows already cover this space in Greek. Do not adapt more.
4. **Vantage-neutral skills.** Math, code, tables, function calling, rewriting, summarising a given text, JSON, constraint
   following, translation between non-Greek languages. No pull. Keep in English as-is. This is most of the value and most
   of the rows.
5. **Other European languages.** EuroBlocks and multilingual-8 rows in fr/de/it/es. Weak pull, small share. Keep raw; the
   D37 adaptation stays reserved for the stage-2 slices.

Every kept row also passes the decontamination list above and the 4,096-token filter.

### 2a. Screening status (2026-09-04 evening)

- Samples of every source, full text, to know the data: https://claude.ai/code/artifact/941df833-a155-45ab-af26-939f88e4db96
- Ground truth v2: 63 rows (7 per screened block, full turns, tool calls rendered) hand-labelled with rubric v3.
  Luna (gpt-5.6-luna, medium, default tier, 48 workers) against it: disposition agreement 55/61; flagged rows (adapt or drop)
  precision 0.55 (6/11) and recall 0.86 (6/7); identity rows (level 3) recall 4/4 with no false identity. The five extra
  Luna drops are answer-quality calls, not vantage calls: two verified right (a FLAN NLI row with the wrong label, a C++
  answer with false claims about unique_ptr), one verified wrong (a logic puzzle brute-forced: the dataset answer is
  correct), two arguable (a fabricated bibliography, an arbitrary FLAN emotion target). The one miss is a level-2 case
  (a cheesecake recipe on US ingredients and units). Decision: the identity and drop categories are reliable enough;
  the core annotation started at 48 workers on the default tier; quality-1 drops will be spot-checked before use.
- Measured on long rows (median 1.5k, p90 8k characters): 3,734 rows per hour at 48 workers, mean call 34 s.
- Data defects found while exporting: (1) Dolci Tool Use stores calls in a `function_calls` field, so the rows looked
  empty; fixed. (2) The Nemotron IF-Chat v3 chat split withholds the first user prompt for rows seeded from WildChat-1M
  (content null, only a sha256 of the prompt): 40.8% of the exported 100k, and 3,915 of the first 4,000 rows. Those rows
  are unusable as-is; the export now drops them, so the usable chat split is roughly 60% of 637k. Recovering the prompts
  by hashing WildChat-1M is possible but not done. (3) Dolci Chat in the release is OpenAssistant only, 6,952 rows.

### 2b. Trust rule (owner, 2026-09-04): verified sources are trusted over the judge

Once a source is shown to be (a) high quality and (b) verified by a program, its rows are not dropped on Luna's quality
verdict; only identity and framing labels apply, and where framing is negligible the source is not screened at all.
The quality screen is for unverified sources, where wrong answers actually live.

Judge routing (owner, 2026-09-04, revised): decide in advance, by dataset and category, which rows need more
intelligence and give those to Sol as their only judge; do not use Sol merely to re-check Luna's drops, because Luna also
misses wrong answers. Checker wherever one exists.

| judge | blocks | why |
|---|---|---|
| checker (exact) | Dolci logic puzzles and word sorts; constraint checkers and final-answer matches where the source has them | no model can beat a program |
| Sol, gpt-5.6-sol, 24 workers | FLAN (Tulu and Dolci), OpenHermes, Magpie, Science, and every row Luna labels as code, math or reasoning inside the Luna blocks | correctness is the question and it needs reading and calculation |
| Luna, gpt-5.6-luna, 48 workers | OpenAssistant (done), safety, WildChat, tool use, Nemotron chat | identity, framing, tone and skill labels; conversational rows where correctness is rarely the issue |

Measured: Luna about 4,300 rows an hour; Sol about 1,700. Sol's share is roughly 77k block rows plus about 12% of the
Luna blocks, two to three days alongside Luna's two days. On the OpenAssistant drops Sol overturned 28% of Luna's
"wrong answer" verdicts, which is why correctness-heavy sources go to Sol outright.

| source | how answers were checked | trust | screen |
|---|---|---|---|
| Dolci Precise IF, ifeval-like filtered | constraint checkers pass on every row | verified | none |
| OpenMathInstruct-2 and its Dolci slice | final answer matches the GSM8K/MATH ground truth | verified | none |
| Dolci logic puzzles | NOT verified: our brute-force checker finds 8 of 51 zebra puzzles with a wrong final answer (16%); the 49 word-sort rows all correct; Luna as judge: 5 of the 8 caught, 6 correct rows falsely dropped | verifiable, unclean | checker, not judge: keep only rows the solver confirms (`data/zebra_check.py`) |
| Dolci Tool Use | synthetic trajectories, schema-checked calls, no ground truth | partial | identity only |
| Dolci Coding, Reasoning | card documents no verification (Evol-CodeAlpaca and Tulu persona code are GPT-generated, unchecked; OpenThoughts3 traces removed) | unverified | identity only; quality screen on a sample before deciding |
| Nemotron chat | best-of-N by a reward model, no truth check | rated, unverified | full |
| Magpie, OpenHermes, WildChat-GPT-4 | model-written, style-filtered | unverified | full |
| OpenAssistant | volunteer-written, unchecked | unverified | full (about a fifth dropped so far) |
| FLAN | 2015-era labels through templates | unverified, noisy | full |
| Safety (WildGuardMix, CoCoNot) | policy-labelled, answers unchecked | unverified | full |

## 3. Personality set

A generated-and-edited set of about 4k rows that fixes who the model is, plus a held-out probe of about 100 questions.

**Facts to bake in.** Its name (owner decision). Made by ΕΕΛΛΑΚ, the Greek Free/Open Source Software Society, on Apertus
from the Swiss AI Initiative, with Greek continued pretraining and Greek fine-tuning. Weights are public on Hugging Face
under an open licence. It runs on the user's own machine: no internet, no tools, no memory between conversations, no access
to the user's files unless pasted, a knowledge cutoff it can state. The user is assumed Greek: euro, metric, Greek law and
institutions, Greek school system, Athens time, Greek holidays, unless the user says otherwise. It answers in the language
it is addressed in, reads Greeklish, and uses the polite plural when the user does.

**Behaviours.** Warm without gushing. No chatbot openers or closers, the ones the blind reading flagged: Βεβαίως!, Φυσικά!,
Τέλεια!, Ελπίζω να βοήθησα. No unsolicited imperatives. Honest about limits and about being a local model, in plain Greek.
Refusals short and in the same voice. Handles questions about itself: who made you, what are you, can you browse, do you
remember me, what data did you learn from, how do I run or quantise you, what hardware do you need, how do you compare to
ChatGPT, is my data private. Multi-turn consistency of all of the above.

**Build.** Prompt taxonomy of about 60 question types × Greek and English × single and multi-turn, generated by Sol from
the persona specification, edited by the Γ pass, sampled for owner review. The probe set is written separately and never
trained on.

**One technical prerequisite.** The Apertus chat template injects "You are Apertus, a helpful assistant created by the
SwissAI initiative" as the default system prompt, and our evaluation copies carry it. Stage 2 trains with the new default
system prompt in the template, and every evaluation after that uses the new template. Otherwise the personality set fights
the template at inference.

## 4. Stage 3, preference

Three pair sources, two scorers. Constraint pairs: fresh Greek prompts with IFEval-shaped constraints, several samples from
the stage-2 model, scored by the checkers, pass versus fail as chosen versus rejected. Identity pairs: the personality probe
distribution, scored by rules. Judged pairs: Greek and cross-language prompts from the interview and WildChat-Greek
distributions, two samples, Sol as the only judge with the round-one rubric plus tone. Opus is not used anywhere in the
batch path: it shares the owner's Claude quota and throttles on the five-hour window. DPO with the stage-2 model as
reference, one epoch, then the full suite.

The evidence for the stage: Tulu 3 on the same base family as Krikri gains 8 points of IFEval from DPO at 8B (72.8 to
81.1) and 1 to 2 more from verifiable-reward RL; at 70B the DPO gain is under a point. Tulu 3 used about 270k pairs. That
scale is affordable on GPU (roughly 30 to 40 node-hours for one epoch) and the judged share is bounded by Sol's throughput,
which is one of the numbers to measure below.

## 5. Evaluation gates

After each stage: Greek IFEval and MGSM, the format gate, the voice score, the 40 interviews, the blind reading by Claude
with the tone axis, the native-Greek suite, GreekMMLU on the stage-end checkpoint, and the new identity probe. Stage 1
must not lose native-suite or GreekMMLU points against the CPT base beyond noise. Stage 2 must recover the wave-1 voice
score and pass the identity probe. Stage 3 must beat stage 2 on Greek IFEval without losing on the reading.

## 6. Speeds: what is measured, what is not, and the tests that settle it

Every duration in this plan rests on a handful of rates. Half are measured from round one; the other half are guesses
until a short test replaces them. The tests are cheap and most run inside work we want anyway.

**Measured in round one**

| rate | value | source |
|---|---|---|
| SFT training, packed 4,096-token sequences, one node | 26M tokens per node-hour | E1 runs, 3 epochs of 20k Greek rows in 32 minutes |
| Greek rows | about 230 tokens each | the dev split |
| light evaluations per checkpoint (IFEval, MGSM, gate, voice, 40 interviews) | about 0.5 node-hour, 25 minutes of wall-clock | 14 checkpoints |
| Greek IFEval plus MGSM on a peer model, batch 32 | 35 to 55 minutes for 8B to 12B | five peers today |
| native-Greek suite, four lanes | about 1 node-hour per model | four checkpoints |
| GreekMMLU, frozen fp32 scorer | 2.8 hours per model, cannot be split | today's batch |
| Sol adaptation pipeline, 16 generation and 24 edit workers | about 20k rows per week | wave 1 |

**Not measured yet, with the test that measures it**

| rate | guess | test | cost |
|---|---|---|---|
| SFT throughput on external rows, about 600 tokens each, after the 4,096 filter | same tokens per node-hour | 50k Dolci rows, one epoch, timed | 0.6 node-hour |
| data preparation: download, filter, decontaminate, tokenise 1M rows | hours on the login node | 100k rows end to end, timed | no GPU |
| Sol judging throughput, short rubric, 24 workers | about 3,000 pairs per hour | 500 pairs, timed | 15 minutes of Sol |
| Sol generation for the personality set | wave-1 pace | 200 rows from the persona spec, timed | 30 minutes of Sol |
| on-policy sampling, two answers per prompt | 2 node-hours per 10k with HF generate; a tenth of that with vLLM if present | 1k prompts, both paths if vLLM loads | 0.3 node-hour |
| DPO training | 1 to 1.5 node-hours per 10k pairs per epoch | arm I: 18k precise-IF pairs on the pick, reference log-probs precomputed | 2 node-hours |
| multi-node scaling of the trainer | unknown; only needed for tier L | 15-minute run on two nodes | 0.5 node-hour |
| vantage filter: Sol labelling of the seed set and classifier training | hours | 2k rows labelled, classifier fitted, precision read on 200 held out | 1 hour of Sol |

The first five tests fit in one debug workbench and one afternoon of Sol. Arm I doubles as the first stage-3 measurement.


**Measured 2026-09-04 afternoon (annotation, codex gpt-5.6-luna, medium effort, full nine-field schema)**

| workers | tier | rows per hour | median call |
|---|---|---|---|
| 24 | priority | 4,240 | 17 s |
| 48 | default | 5,270 | 26 s |
| 88 | default | 5,900 | 29 s |

Throughput grows sub-linearly with workers; 88 workers on the default tier is the working rate. At 5,900 rows per hour: the 250k screened pool takes 42 hours, all 805k training rows 5.7 days, a 1.1M candidate pool 7.8 days. Spot-check of five rows Luna rated "wrong" (quality 1): all five verdicts held on reading.

**Provisional totals, to be replaced by the tests**

| item | node-hours | CHF |
|---|---|---|
| stage 1, tier S then M | 30 | 80 |
| stage 2, two passes | 2 | 5 |
| stage 3, DPO on 100k to 270k pairs | 12 to 40 | 32 to 108 |
| evaluations, three stage ends | 15 | 40 |
| timing tests above | 4 | 11 |
| total, ladder without tier L | 63 to 91 | 170 to 245 |
| tier L on top | plus 100 | plus 270 |

Round one spent CHF 52 of the 90 cap. The allocation is 779 node-hours. Wall-clock is set by Sol, not by GPUs: the
adapted rows, the personality set and the judged pairs all run through the same 24 workers, so they are scheduled in that
order and overlap with stage-1 training.

## 7. Owner decisions before work starts

1. The model's name and the exact identity facts (ΕΕΛΛΑΚ wording, licence, credits to Apertus and the CPT).
2. Stage-1 tier: S then M, or straight to M, and whether L stays on the table.
3. Backbone: Apertus mixture, or Dolci as the newer fully open set.
4. Include the Aya Greek split after filtering, or leave native Greek to our own rows.
5. Accept Qwen3-generated rows from SmolTalk2. Apache-licensed outputs, no restriction.
6. A new spending cap for the round. CHF 250 covers the ladder and a 100k-pair DPO; a 270k-pair DPO needs about CHF 300.
7. Go-ahead for the timing tests, about CHF 11 and one afternoon of Sol, which turn the guesses above into numbers.
