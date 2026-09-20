# Krikri evaluations and the proposed evaluation suite

Checked 13 September 2026. Scope: the official Krikri paper and model cards, the later native GreekMMLU paper, and our inspected experiment artifacts. This is not an exhaustive inventory of every third-party use of Krikri.

## Published evaluations: keep model and protocol identities separate

| Evaluated model / publication | Greek evaluations | English evaluations |
|---|---|---|
| Krikri-8B-Base | Medical MCQA (15-shot), Belebele (5), HellaSwag (10), ARC-Challenge (25), TruthfulQA MC2 (0), ILSP translated MMLU (5) | WinoGrande (5-shot), Belebele (5), HellaSwag (10), ARC-Challenge (25), TruthfulQA MC2 (0), MMLU (5) |
| Krikri-8B-Instruct, chat evaluation | IFEval, MT-Bench, Arena-Hard-Auto v0.1 adapted to Greek | IFEval, MT-Bench, Arena-Hard-Auto v0.1 |
| Krikri-8B-Instruct, Open LLM Leaderboard route | — | IFEval, BBH, MATH, GPQA, MuSR, MMLU-Pro |
| Further tests in the final Krikri paper | ASEP MCQA, 1,200 questions; Ancient↔Modern Greek translation, 100 sentence pairs, BLEU | — |
| Later native GreekMMLU paper | Krikri-Base and Krikri-Instruct, zero- and five-shot native GreekMMLU | — |
| Krikri-Instruct-v1.5 card | IFEval, MT-Bench, Greek Arena-Hard | IFEval, MT-Bench |

Sources for the inventory: [Krikri Base card](https://huggingface.co/ilsp/Llama-Krikri-8B-Base), [Instruct card](https://huggingface.co/ilsp/Llama-Krikri-8B-Instruct), [final EMNLP paper, §§4.1–4.2](https://aclanthology.org/2025.findings-emnlp.268.pdf), [native GreekMMLU paper](https://aclanthology.org/2026.findings-acl.448.pdf), [v1.5 card](https://huggingface.co/ilsp/Llama-Krikri-8B-Instruct-v1.5).

The final EMNLP paper adds ASEP to the evaluations discussed in the earlier preprint. Our native suite already includes ASEP; reconcile the exact release and scoring before treating it as a missing benchmark.

### Comparability rules

- The base-model table is not an Instruct-model result. Re-running its tasks on Instruct is useful, but label that as our evaluation.
- ILSP's translated MMLU, native GreekMMLU, Global-MMLU-Lite and other translated MMLU releases are distinct datasets/protocols.
- Original MT-Bench scores use GPT-4o-2024-08-06. Original Greek Arena uses GPT-4o-mini-2024-07-18 as baseline and GPT-4o-2024-08-06 as judge; English uses GPT-4-0314 and GPT-4-1106-preview. Their win rates cannot be pooled across languages. The v1.5 Greek Arena card instead uses Sonnet 3.7. New Sol-judged scores require matched re-evaluation of peers. [Instruct evaluation](https://huggingface.co/ilsp/Llama-Krikri-8B-Instruct), [variant evaluation](https://huggingface.co/ilsp/Llama-Krikri-8B-Instruct-v1.5)
- Published English leaderboard MATH is not our Greek MATH-500 protocol. Published IFEval is also not automatically our rescored IFEval.
- MT-Bench and Arena contain coding prompts, but their scores alone do not establish executable code or tool-use competence.

## What our actual artifacts establish

“Configured” means a task appears in the runner. “Completed” requires a usable score artifact with the expected item count and protocol.

| Area | Current evidence | Action |
|---|---|---|
| Greek arithmetic and competition maths | MGSM and MATH-500 outputs/scores for project checkpoints and peers | Keep; audit extraction, language, difficulty and termination. |
| Greek knowledge | Native GreekMMLU, ASEP, medical MCQA, GPCR and DemosQA | Keep; reconcile source identities and macro versus item-weighted aggregation. |
| Greek language/reasoning | OYXOY WiC, definition WSD, metaphor and NLI; Greek XNLI | Keep disaggregated; NLI exact-set is an auxiliary metric, not a ninth independent benchmark in the eight-benchmark mean. |
| English commonsense/knowledge | Successful ARC-Easy/Challenge, HellaSwag, WinoGrande, PIQA and MMLU results | Keep as retention references; establish matched peer coverage. |
| Multilingual knowledge | Global-MMLU-Lite, including all six foreign target languages | Complete matched Apertus-Instruct scores. The task label alone does not imply full Global-MMLU. |
| Multilingual inference | XNLI, plus XCOPA where languages are available | Keep; these do not cover every target language or every capability. |
| Reading comprehension | Belebele and XQuAD appear in configuration, but successful results were absent from the inspected retention files | Activate and verify; do not claim completed coverage from configuration. |
| IF and behavioural tests | Greek IFEval; Greek/English IFBench, XSTest and MultiChallenge artifacts; some selected-checkpoint judging incomplete | Finish decision-relevant cells, inspect checker validity and translation revision. |
| Dialogue | Adaptive mixed-profile and hostile-user simulations, interviews, small probes | Add fixed-history causal diagnostics and equally sized confirmation panels. |
| MT-Bench / Arena / dedicated BBH | No successful project results established in the inspected inventory | Add selectively as below. |

### Native GreekMMLU reconciliation

The published zero-shot table reports Krikri-Instruct **66.47% average**. Our saved native MCQ headline is **52.01% across 16,632 items**. The paper's prose advertises a different public count while its appendix includes 16,632; inspect the actual release/manifests, not a guessed explanation. [Published GreekMMLU paper](https://aclanthology.org/2026.findings-acl.448.pdf)

First recompute macro, subject and item-weighted aggregates from existing outputs. Then compare pinned upstream code with our actual prompts, scored continuations, likelihood normalization, choice labels, tokenizer/chat-template usage, shot examples and checkpoint revisions. If necessary, run both protocols on the same 200-item stratified intersection for Krikri and G3F2P1. Expand only after locating the discrepancy. Preserve both protocols in the report; do not replace a score just because another is higher.

## Minimal expansion and exact initial sizes

### 1. Broad dialogue: MT-Bench

Use the [Greek release](https://huggingface.co/datasets/ilsp/mt-bench-greek) and its corresponding English inputs: **80 two-turn conversations per language**, eight categories. Its Hugging Face split is named `train`; it remains evaluation-only for us. Check ambiguous references and translation fidelity before judging, retaining an original and any justified corrected protocol separately.

Initial models: G2F1P1--02, G3F2P2--00, pinned Apertus-Instruct, original Krikri-Instruct; include Krikri-Instruct-v1.5 if the serving pilot fits. That is 1,280 assistant responses for four models, or 1,600 for five. Use one judge call per conversation with per-turn/per-category fields: 640 or 800 primary calls, plus a declared blind audit allowance. The final selected candidate adds 320 responses and 160 primary judgments. These counts are workload, not measured runtime.

MT-Bench's two turns complement, but cannot replace, longer dialogue-state testing.

### 2. Cross-language comprehension: Belebele

[Belebele](https://github.com/facebookresearch/belebele) has 900 parallel questions per language across 122 language variants. Use Greek, English, French, German, Spanish, Portuguese and Italian. Start with **100 matched question IDs per language**: 700 items/model. Prioritise Apertus and the selected project reference/candidate, adding Krikri's Greek/English comparison.

Expand to 900 per target language for the selected candidate and Apertus when priced within the final-evaluation allowance. Keep matched families together for intervals and train/test separation. Add XQuAD Greek to distinguish free answer generation from MC recognition when its already-configured runner works.

### 3. Factual recall, recognition and evidence use

Create **100 independently sourced fact families**, each with Greek/English versions, and run three separate contexts: short-answer without options, MC, and supplied-evidence QA. That is 600 prompts/model. Split families in advance into 40 development and 60 sealed confirmation families; do not repeatedly tune against all 100. Use answer aliases and evidence spans. Include unsupported questions and misleading/updated passages in declared strata.

For each other target language, begin with a matched 20-family sentinel subset: 60 prompts/language/model, used for diagnosis rather than an equivalence claim. Prefer stable science/culture facts and fresh controlled-world facts. Verify changing real-world facts at their snapshot date. External search/RAG is a separate system-level evaluation if it is part of deployment.

### 4. Dialogue state and non-maths reasoning

Create **120 fixed-history Greek cases**, 20 in each of six categories: version edits, inferred state, evidence-based corrections, premise/uncertainty handling, stop/output boundaries, and natural task continuation. Split 60 development / 60 confirmation by scenario family. Add matched English versions, then 24-case diagnostic subsets in each of the five other languages. Use computed state or sourced truth wherever possible.

This gives 240 Greek/English responses plus 120 foreign-language sentinel responses per model. Separately use **60 equally budgeted mixed-profile interactive conversations per selected model**, with fixed scenario seeds and turn caps. Adaptation means the histories will diverge; report this as interactive performance, not a same-input experiment. Score decision-relevant outcomes, usefulness, naturalness, copying and stopping separately.

For a factual correction, record whether the user's claim is true, false, partly true or unresolved independently of tone. Fictional/counterfactual instructions form a distinct stratum, not a false-fact label.

### 5. Open-ended usefulness: Greek Arena-Hard

Use a **100-prompt stratified pilot** for the selected candidate versus original Krikri, with a fixed judge, swapped presentation order, explicit ties and the declared style-control method. Primary budget: 200 pairwise judgments before audit/retries. Add Apertus as a second comparator only when its additional 200 judgments and generations are budgeted. Expand to the full release only after confirming usefulness and runtime.

The official [release link](https://huggingface.co/datasets/ilsp/m-ArenaHard_greek) is linked by Krikri's card, but its dataset page timed out during this check. Fetch, pin and validate the artifact before fixing its full-run count. Do not substitute another Arena version silently.

### 6. Optional benchmarks after the first readout

- **BBH:** a prespecified balanced subset of deductive/constraint tasks, with explicit task selection. Any Greek adaptation must be checked independently and labelled as an adaptation.
- **MuSR:** useful if longer narrative reasoning remains weak after the state panel. Price separately.
- **GPQA and MMLU-Pro:** potentially useful difficult-knowledge diagnostics; not required on every SFT pilot.
- **TruthfulQA Greek/English:** useful optional misconception robustness, but not a substitute for broad factual accuracy or source-grounded recall.
- **ILSP translated MMLU, HellaSwag and ARC Greek:** useful compatibility checks with the original base-model publication; native GreekMMLU and validated multilingual comparisons take priority.
- **Ancient Greek translation:** defer unless it becomes an explicit product objective. Later specialised Krikri translation models are separate checkpoints, not evidence for the same general Instruct model. [Specialised translation study](https://arxiv.org/abs/2605.18504)
- **Executable code/tool tests:** add only if tools/code are in the intended deployment contract; chat-judge impressions cannot replace execution.

No full all-model × all-language × all-benchmark matrix is assumed funded. New-panel pilots establish runtime; the final candidate receives the required coverage and older peers are reused only when their exact protocol matches.
