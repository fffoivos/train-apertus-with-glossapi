# Competition-maths scale source inventory

Built at `2026-09-13T16:58:18+03:00` by a local, read-only metadata/text scan. No model subprocess, production transform, source edit, GPU job, or remote job was run.

## What the complete lineage scan establishes

The cached MATH training split has **7,500 rows and 7,492 normalized source families**. Eight rows repeat an existing normalized problem. The current Greek maths source has 14,215 rows: 5,823 translated GSM8K, 3,284 translated MATH, and 5,108 native rows. In the actual assembled split, the MATH portion contributes **3,241 rows / 3,240 families to gradient training**, 40 rows / 40 families to development, and three rows / three families excluded during assembly. One normalized family accounts for two gradient-training rows.

The English `openmath_gsm_raw.jsonl` import was exhaustively scanned: all **100,000** rows declare `problem_source=gsm8k`, and none exactly matches a normalized MATH-train family. Its assembly receipt records 99,971 available after its prior keep-list stage, 29 contamination exclusions, 99,942 taken, 98,943 train, and 999 development rows. This supports a zero exact MATH-family contribution from that named import; it is not a claim about unrelated blocks without MATH lineage metadata.

The 32-row generation pilot contains 29 MATH-family rows and three GSM8K rows. Its 16 `fresh_level5` items are new to that pilot's audited sample selection. None maps to the current Greek MATH train/dev rows, but that does **not** establish that the problems were unseen in pretraining, earlier checkpoints, evaluator development, or any source outside the enumerated assembly lineage.

## Old Greek Level-5 material

Cut 2 names 1,500 Level-5 source candidates. Append-only output files contain 1,457 problem IDs and 1,168 solution IDs, giving 1,168 paired IDs. Only **104 paired IDs** have no decoded disallowed control character and no conflicting saved problem or solution text across attempts. The other 1,064 pairs need attempt reconciliation or control repair; 289 have only a problem output and 43 have no problem output. “Mechanically clean and nonconflicting” is an inventory gate, not semantic or mathematical acceptance.

The proposed training options reuse 21 of the 104 mechanically clean pairs: seven in stage 1 and 14 in stage 2. Every reused pair still requires a full source-fidelity, derivation, answer, Greek, and provenance review before promotion.

## Identity and benchmark gates

Family identity uses the exact normalization already used by the pilot: NFD, lowercase, combining-mark removal, non-word replacement, and whitespace collapse, followed by SHA-256. Candidate source families are rejected for the MATH-500 test when any of these holds:

- complete normalized equality;
- any shared normalized word 13-gram;
- more than 50% of the **candidate MATH-train problem's distinct 8-grams** occur in one test item.

The denominator in the current pilot code is candidate 8-grams. Prose that calls these “test 8-grams” is inaccurate. Across the complete source, 180 normalized families trigger at least one of the MATH-500 gates. The family inventory records the exact result and maximum share for every family.

Assembly decontamination is a separate implementation. It uses NFKC + casefold + word extraction, then drops a training user turn when at least 50% of that candidate turn's distinct 8-grams occur anywhere in the loaded evaluation-gram index. The receipt reports zero matches in final train for the specifically loaded inventories: English originals, Greek MMLU, GSM8K, IFBench-el, IFEval, math500-el, MGSM-el, MultiChallenge-el, four named native sets, XSTest-el, and Ellinika Bench. This audit makes no decontamination claim for omitted datasets, pretraining, selection exposure, or unrecorded sources.

## Frozen family options

The content-free split manifest freezes **133 disjoint family identities** after excluding current train, current development, assembly-excluded rows, all pilot families, ambiguous metadata, and the MATH-500 gates.

| Lane | Families | Coverage | Existing Greek candidates |
|---|---:|---|---:|
| Train stage 1 | 35 | one per 7 subjects × 5 levels | 7 clean Level-5 pairs |
| Train stage 2 | 70 | two additional per subject × level cell | 14 clean Level-5 pairs |
| Development | 14 | two per subject, with levels rotated | 0 |
| Final confirmation | 14 | two per subject, with levels rotated | 0 |

Final-confirmation entries contain identity hash, source line, subject, and level, but no source problem text. Future authoring, reviewer, prompt-development, retry, and selection payloads must exclude those 14 identities and their content. They should be materialized only after prompts and gates are frozen, and their outcomes must not drive another prompt revision.

## Modest execution sequence

The last supplied account observation was **49% weekly quota remaining**; this scan did not refresh it. Given that shared and possibly stale limit, the next scale should stay staged:

1. Fully review the seven existing Greek pairs in phase A without generation. Any semantic or mathematical defect becomes a separately tracked repair; conflicting historical attempts are not silently selected.
2. Run only the 14-family source-generation probe in phase B. Under the prior fresh-row shape—adaptation, high solve, blind verification, and xhigh on half—this is about **49 primary calls**, before separately capped correction or retry work.
3. If that gate passes and the current usage check supports it, complete the remaining 14 stage-1 training families and the 14 development families. The 42 source-only train/development families in the complete stage-1 envelope correspond to about **147 primary calls** under the same shape. Freeze conditional correction and retry caps before dispatch.
4. Defer stage 2, which adds 70 families, until stage-1 quality and a fresh quota check justify it. It includes 14 old Greek pairs and 56 source-only families.
5. Generate and review the 14 final-confirmation families only after prompt freeze. Their approximately 49 primary calls are outside development and selection.

All local inventory work is appropriate on the Mac. Any bulk materialization, corpus-wide transformation, or larger batch assembly should be routed to CSCS with its own source hashes and receipts. This report prepares options only; it does not launch or authorize generation.

## Artifacts

- `math7500_family_inventory.jsonl`: all 7,492 normalized families, content-free identity and lineage flags.
- `proposed_family_splits.jsonl`: the 133 disjoint options and execution phases, without problem text.
- `source_manifest.json`: exact input hashes, sizes, and JSONL row counts.
- `inventory_summary.json`: checkable aggregate counts and source receipts.
- `verification.json`: executable gate and split invariants.
- `build_inventory.py`: deterministic builder.
