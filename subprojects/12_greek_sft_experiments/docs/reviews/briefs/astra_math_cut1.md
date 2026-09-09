# Brief: Greek math dataset, pilots M1–M5 and the first cut (status: cut1 GENERATING now; findings apply to it and to the next cut)

## What it is for
Greek MGSM is the clearest remaining gap of our 8B model (0.524 vs Krikri 0.676); the mix has only English math. This set gives Greek step-by-step solutions in Greek conventions (decimal comma «3,5», thousands dot «1.000», «€» after the number, «·» for multiplication, a final line «Απάντηση: …»), on translated-and-localised GSM8K/MATH problems and on native Greek school problems.

## How it was built
- Translation: Sol translates and localises GSM8K train and MATH train (levels 1–4) rows with the instruction «Μετάφρασε και προσάρμοσε στα ελληνικά … ελληνικά ονόματα και τόποι, ευρώ αντί για δολάρια (κράτησε ΤΟΥΣ ΙΔΙΟΥΣ αριθμούς), ελληνική μορφή αριθμών … Μην αλλάξεις τη μαθηματική δομή ούτε την απάντηση». Then Sol solves the Greek version blind (high effort) with the writing rules «λύση βήμα προς βήμα στα ελληνικά, σύντομες προτάσεις, μία πράξη ανά γραμμή … τελευταία γραμμή «Απάντηση: …»». A row is kept only if the Greek solve reaches the reference answer (equivalence checker: numeric with Greek/English formats, units ignored, fractions, Unicode minus, multi-part answers by number sequence, rounding within half a cent or 0.1%). Pilot fidelity: 95.5% (GSM8K 98.7%, MATH 92.3%).
- Native: Sol writes 5 problems per (grade Γ΄ Δημοτικού…Γ΄ Λυκείου × topic × context × surface) cell with the same rules; in the pilot a second solver (Luna) solved blind and 97.8% agreed; the owner then ruled that only the hardest (Lykeio) problems get a second solve (Sol, high effort) in the cut; the rest are kept unverified.
- Arm B (our model) on the 500 native pilot problems: 37% greedy, 61% pass@4; primary school ~50%, Gymnasio 31–40%, Lykeio 11–26%; weakest probability 8%, systems/quadratics 12%, trigonometry 20%.
- Contamination: GSM8K train only (MGSM is GSM8K test); no pilot problem above 0.25 character-5-gram Jaccard with any Greek MGSM item.
- A Greek correction pass (editor, answer-guarded) runs after the cut.

## Sample
Rows from the pilots: translated (`problem_en`, `problem_el`, `changes`, `solution_el`, `final_used`, `ref`, `correct`) and native (`grade`, `topic`, `context`, `surface`, `problem_el`, `solution_el`, `final_answer`, and where present Luna's `solution2`, `final2`, `agree`).

## What to judge
1. Translation quality and localisation: are the Greek problems natural, are the localisations coherent (currency, names, units), do any change the arithmetic or the answer? Count in the sample.
2. Solution quality as a training target for an 8B model: step granularity, Greek mathematical register (ΕΚΠ, παρονομαστής, κλπ), formatting rules followed, brevity vs completeness. Do the solutions teach reasoning or just state results?
3. Native problems: realism for the grade, ambiguity, multi-part (α)(β) answers, whether "one clear final answer" holds; are there grades or topics that look wrong for the stated level?
4. Verification design: the reference-answer filter for translated rows, a second solve only for Lykeio, none for the rest (owner's decision): where will unverified errors concentrate, and is there a cheap check you would add (e.g. code recomputation for numeric answers)?
5. Against the literature (GSM8K, MATH, GSM-Symbolic/GSM-Plus perturbations, GSM-IC irrelevant context, MathCheck/PRM error-spotting, multi-turn tutoring data, MGSM): what would you add or reweight for a model at 37% on Greek school math? What is the risk of training on translated competition-style solutions in Greek?
6. Anything that must not be trained on.

Disposition: cut1 is generating; BLOCKER/HIGH findings will be applied to the filtering of cut1 and to the recipe of cut2.
