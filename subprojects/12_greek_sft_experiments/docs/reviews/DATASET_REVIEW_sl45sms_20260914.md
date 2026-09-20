# Review of sl45sms/reviewed-qa-keep-discard-pairs (+ -tpriftis-pairs), 14 Sept 2026

Pipeline as described by the owner: a ~400B Qwen generates QA pairs from our CPT data; humans review in Argilla (keep/discard).

## What is there
- Two public Hub datasets, cards are YAML only (no prose, no generation prompt, no reviewer guidelines).
- `reviewed-qa-keep-discard-pairs`: 21,027 rows, every row `review_action=accept`; discarded rows are not published, so the discard rate and reviewer behaviour are unknown.
- `reviewed-qa-keep-discard-tpriftis-pairs`: 603 rows, all contained (exact pair) in the large set; it adds nothing.
- Format: single-turn chat. User = `Κείμενο:\n"""\n<CPT passage, median 600 words>\n"""\n\n<instruction>`; assistant = a JSON string `{"question": …, "answer": …}`. This is the generation task the reviewers saw, not a QA training format. Two instruction variants: 19,606 rows "Δημιούργησε ένα ζεύγος ερώτησης-απάντησης…", 1,421 rows "Απάντησε ΜΟΝΟ με JSON…". Only the 1,421 carry source provenance (Wikisource 1,276, school books 123, folk literature 22); the other 19,606 have none.
- Content: passages are CPT chunks; many are thesis/dissertation front matter (title pages, committees, abstracts) with `<!-- image -->` and `##` artefacts; 2,896 passages (14%) are polytonic literature. Questions: median 25 words, 78% start with Ποια/Ποιος/Ποιο/Ποιοι/Ποιες (factoid), 13% refer to "the text/poem/author". Answers: median 28 words, abstractive (median longest verbatim span 13% of the answer; 9% of answers are half copied). JSON valid 21,027/21,027. 32 exact duplicate pairs; 696 passages reused for several pairs. 477 answers (2.3%) have Latin share > 20% (names, terms).
- Benchmark contamination: 3 rows share a 13-gram with our evaluation caches (exclude); no overlap with our current training prompts.
- Cost if used as is: ~25–30M tokens of passages in user turns (unsupervised) for ~1.5M supervised answer tokens; comparable to a whole pass in tokens.

## Quality (spot read of 8 random pairs + statistics)
Greek is correct and natural; questions are answerable from the passage; several are document-metadata questions of low value (the title of a thesis, which professor a volume honours, the thematic area of a bachelor thesis). "Accept" tells us a human did not reject them; it does not tell us how strict the reviewers were.

## Recommendation
- Do not pause the pilots (maths question, unrelated) and do not add this data to tomorrow's Phase C pass: a new untested block at launch time breaks the plan's rule that every block is piloted and attested.
- Intake as a candidate block for the next round: (1) ask the colleague for the discard counts, reviewer guidelines, the Qwen prompt/settings and the provenance of the 19,606 unlabelled rows; (2) Sol judge on a 300-row sample: faithfulness to the passage, answerability, triviality (metadata questions), Greek quality; (3) reformat into the task we want (user = passage + question, assistant = answer; optionally a small JSON-generation share), drop metadata questions and `<!-- image -->` junk, cap per source, decontaminate; (4) pilot +block vs without on reading-comprehension measures (Belebele-el, native reading QA) before it earns an F number.

## The pipeline (github.com/sl45sms/GSDG, read 14 Sept)
- Generator: Qwen3.5-397B-A17B (FP8) served with vLLM on Clariden (Ray, multi-node). Sources: GlossAPI Hub datasets (Sxolika_vivlia, Wikisource, dimodis_logotexnia, ...) and parquet shards of `fffoivos/glossapi-greek-nanochat-pretraining-dataset` (HPLT clean60 shards), i.e. our CPT corpus.
- Text extraction (`text_extraction.py`): the document text is whitespace-collapsed and truncated to a character budget (2k-6k chars recommended). Every passage is therefore the HEAD of a document, which is why so many rows are thesis title pages and front matter.
- Prompt (`prompting.py`): one comprehension question in Greek that "must stand alone without reference to the text"; JSON output. In the published rows 19,606 carry a different, shorter instruction ("Δημιούργησε ένα ζεύγος ερώτησης-απάντησης που να βασίζεται στο παραπάνω κείμενο") and 13% of questions still refer to the text/poem/author, so the standalone requirement was not enforced.
- Curation (`curate_jsonl.py`, `async_curation.py`): deterministic filters (answer >= 4 words, context window, question/answer length ratio <= 10, garbage, question-answer overlap <= 0.8, AI refusals, Greek ratio), MinHash near-duplicates at 0.85, then an LLM review at temperature 0 (ACCEPT / REJECT_LANGUAGE / REJECT_TEMPORAL / REJECT_LOW_QUALITY) with topic classification into 18 categories. None of the category or reject fields survive in the Hub export.
- The Argilla keep/discard step is not in the repository; `review_action=accept` in the Hub metadata is that step's label. A sibling repo (glossApi-trainer) fine-tunes Apertus (LoRA/full) on this data with a side-by-side UI; no evaluation numbers are published.

Refinements to the recommendation: ask for the curated JSONL with categories and the reject log (they exist in the pipeline), and for chunking by section/paragraph instead of document heads before any regeneration; treat the standalone (closed-book) questions and the passage-grounded ones as two different tasks when reformatting.

## Deterministic triage (14 Sept, 22:15) — `data/intake/sl45sms/{features.py, judge_sample.py, calibrate.py}`
Flags per row (no model): non-prose passage (few function words / many capitals / markdown artefacts), metadata question (regex), title copied into the answer, text-referencing question, low answer grounding (< 50% of answer content words in the passage), unanchored question, short answer. Flag counts on 21,027 rows: non-prose 10,380; metadata question 6,548; text-referencing 4,670; low grounding 4,523; unanchored 4,908; title copy 579; short 504; no flag 5,713.
Calibration: Sol (medium) judged 300 rows, 150 flagged + 150 unflagged, for content (good / trivial metadata / not a question), standalone, faithfulness, Greek. Judged-bad = trivial metadata, not a question, not standalone, contradicts the passage, or flawed Greek.
- Non-prose passages carry 30% metadata questions vs 5% for prose passages: the head-only sampling is the cause of the metadata questions, as suspected.
- Rule "drop if metadata question OR text-referencing question OR low grounding": precision 0.63, recall 0.74 of the judged-bad rows, keeps 8,863 rows with about 14% residual defects (7% Greek flaws, 5% metadata the regex misses); the passage flag itself is too coarse to use alone (53% bad among flagged).
- Population estimate: about 42% of the published rows are defective by these criteria, plus 14% whose answers the passage cannot verify (the generator answered from its own knowledge).
Conclusion: the deterministic rule is a good pre-filter (halves the judge cost) but not a substitute for the judge on the kept rows.
