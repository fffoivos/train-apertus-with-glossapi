# Greek math dataset: plan

Date: 2026-09-09. Status: PLAN, not started. Owner's brief (8 September, 23:40): «we should also plan for a math dataset».

## 1. Why

Greek MGSM is round two's clearest remaining gap: arm B 0.524, Apertus-8B-Instruct 0.532, Krikri 0.676. The mix has English math only (OpenMath GSM, 4.5k rows in the Greek pass, more in stage 1) and no Greek reasoning text, so the model reasons in a foreign register and slips on Greek number formatting, units and vocabulary. Math is also the cheapest skill to verify: every row has an answer that a checker can confirm, so the set can be built with no judge in the loop, like the instruction-following set.

## 2. Dimensions the literature names, and what each contributes

| dimension | source | what it covers | Greek-specific additions |
|---|---|---|---|
| grade-school word problems | GSM8K, MGSM (its test set is 250 GSM8K test problems in translation) | multi-step arithmetic in everyday stories | Greek names, places, euros, VAT 24% and 13%, ΕΝΦΙΑ, ΚΤΕΛ fares; decimal comma «3,5», thousands dot «1.000», «€» after the number |
| competition math | MATH (7 subjects × 5 levels), NuminaMath, OpenMathInstruct-2 | algebra, geometry, number theory, counting and probability, precalculus | Greek terminology (ΕΚΠ, ΜΚΔ, παρονομαστής, συνάρτηση, διακρίνουσα), Greek variable and point names, «·» for multiplication |
| school curriculum | Greek Δημοτικό to Λύκειο syllabus; Πανελλαδικές past papers (public documents of the Ministry) | the problem types a Greek pupil meets, in the form a Greek teacher writes them | Πανελλαδικές style: θέματα Α–Δ, proof steps, «Δίνεται … να δείξετε ότι» |
| robustness to surface changes | GSM-Symbolic (2024), GSM-Plus | the same problem with other numbers, names, irrelevant sentences, reordered clauses | templated variants of every generated problem, so the model learns the reasoning, not the story |
| irrelevant context | GSM-IC | a distracting sentence that must be ignored | idem, in Greek |
| error spotting | PRM-style, MathCheck | find the wrong step in a given solution; judge whether a solution is right | Greek solutions with one planted error |
| multi-turn tutoring | MathChat, Tulu 3 math personas | the pupil asks a follow-up, wants a hint, makes a mistake | Greek pupil personas by grade; the assistant gives a hint before the solution when asked |
| answer format | IFEval-style | final answer on its own line, units, exact vs rounded | «Απάντηση: 42 €», «Απάντηση: 3/4», rounding rules stated in the problem |

## 3. Sources and verification

| source | rows | licence | verification |
|---|---|---|---|
| GSM8K train, translated and localised by Sol (names, currency, formats) | 7,473 | MIT | the reference answer travels with the row; a Greek solution is generated and its final number must equal it |
| MATH train, translated | 7,500 (levels 1–4 first) | MIT | reference answer, symbolic comparison with sympy |
| OpenMathInstruct-2 or NuminaMath-CoT, translated sample | 10,000 | CC-BY-4.0 / to verify per subset | reference answer |
| native Greek problems written by Sol per curriculum cell (grade × topic × context) | 8,000 | ours | two independent solves (Sol at high effort, Luna) must agree on the final answer, and a sympy or Python check where the answer is numeric; disagreement rows go to a review pile |
| Πανελλαδικές past papers (Μαθηματικά Προσανατολισμού, ΕΠΑΛ, Γενικής) | 300–600 problems | public documents; solutions ours | Sol solution checked against published answer keys (public) |
| GSM-Symbolic-style variants of the above | 5,000 | derived | the answer is recomputed from the template |

Contamination rule: MGSM is built from GSM8K test, so only GSM8K train is used, and the Greek held-out set (§5) is checked for overlap against everything above by exact and near-duplicate match before any training.

## 4. The generator

- **Cells.** Grade (Γ΄ Δημοτικού to Γ΄ Λυκείου) × topic (arithmetic, fractions and decimals, percentages and finance, ratios, equations, functions, geometry, trigonometry, probability and statistics, number theory, sequences) × context (shop, school, travel in Greece, cooking, sport, farming, public services) × surface (plain, with irrelevant sentence, with a table).
- **Solution style.** Step-by-step in Greek, short sentences, one calculation per line, the final line «Απάντηση: …»; the style guide's level rules apply (Ε2 for school problems, Ε3 for competition).
- **Two solves per problem**: the training row keeps the agreeing solution; disagreements are not trained on.
- **Variants.** Every native problem gets two GSM-Symbolic variants (other numbers and names) with the answer recomputed by the template's formula, so the checker is exact.
- **Multi-turn**: 20% of native rows get a second and third turn (a hint request, a wrong pupil attempt to correct, a «why this step» question).

## 5. Pilot experiments (before scaling)

| # | question | design | readout |
|---|---|---|---|
| M1 | translation fidelity | 300 GSM8K and 300 MATH rows translated by Sol; Sol solves the Greek version | share whose Greek solution reaches the reference answer (fidelity ceiling); Luna spot-check of 100 for Greek quality and localisation errors |
| M2 | native problem quality | 500 native problems, two solves | agreement rate by grade and topic; sympy-check pass; review of 50 disagreements to see whether the problem or the solve is at fault |
| M3 | difficulty calibration | the 500 native problems solved by arm B (greedy, 4 samples) | arm B accuracy by grade and topic, to set the mix towards what it fails |
| M4 | format and formatting | 200 rows | share of solutions with correct decimal comma, thousands dot, «€» after the number, final answer line |
| M5 | held-out set | 300 native problems built the same way, never trained on, plus MGSM-el | the evaluation for every later run |

Cost: about 2,000 Sol calls for M1–M4, one afternoon at 24 workers.

## 6. Targets

First cut 20k rows: translated-localised 10k (GSM8K 5k, MATH 3k, OpenMath 2k), native 6k, variants 3k, multi-turn 1k; then 40k. Every row carries the answer, the verification method and the source. Failed solves become preference pairs (right vs wrong solution to the same problem).

## 7. What to measure

Greek MGSM (primary), the 300-problem Greek held-out set, a Πανελλαδικές sample, and English GSM8K to check that Greek math does not cost English math. Success is Greek MGSM above 0.60 on the 8B without losing IFEval.
