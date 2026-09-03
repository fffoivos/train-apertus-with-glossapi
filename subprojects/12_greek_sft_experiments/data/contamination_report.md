# SFT contamination report

This report contains identifiers and scores only; it does not reproduce training or evaluation text.

## Method

User turns were normalized with Unicode NFKC, case-folding, punctuation removal, and whitespace collapse. Distinct word 8-grams were compared with containment `intersection / min(train_ngrams, eval_ngrams)`; texts shorter than 8 words use their complete token tuple. Near duplicate threshold: `0.5`. Exact means the complete normalized strings match.

Only rows assigned to train were scanned. If any user turn had an exact match, the complete `(config, row_id)` was removed from every arm and every adapted/raw variant before files and token statistics were written. Dev rows were not contamination-filtered because the requested gate applies to train rows.

## Evaluation prompt receipts

| suite | status | prompts | revision or identity |
| --- | --- | ---: | --- |
| ellinika_bench | available | 1788 | `80fbf436d83efbf21566e607275cc60c5a8df8cb50ada42af2c2c16567627f1a` |
| greek_mmlu | available | 16632 | `6a03aa06b68beb932fb75edff3a34e50b3674649` |
| gsm8k | available | 1319 | `740312add88f781978c0658806c59bc2815b9866` |
| ifeval | available | 541 | `966cd89545d6b6acfd7638bc708b98261ca58e84` |
| native_greek_suite | unavailable | 0 | `not accessible via HfApi at build time` |

## Result

- Exact hits before removal: **5**
- Unique train rows removed: **5**
- Exact hits in final train files: **0**
- Near-duplicate hits (not removed): **0**

## Exact hits removed

| config | row_id | variant | user turn | arms | eval suite | eval id | containment |
| --- | --- | --- | ---: | --- | --- | --- | ---: |
| everyday | everyday_443f5ebc | adapted | 2 | E1,E2,E3,E3prime | greek_mmlu | All:test:11741 | 1.000000 |
| no_robots | 5b557cf13e5386643b037ce300cc1459ca26b7766d6e41eb6ad06f2265277cb4 | adapted | 1 | E1,E2,E3,E3prime | greek_mmlu | All:test:4675 | 1.000000 |
| no_robots | cdc3138fa384db4f2a848ee35f42810a780599665de420a45d6863e1bdf00669 | adapted | 1 | E1,E2,E3,E3prime | greek_mmlu | All:test:4717 | 1.000000 |
| no_robots | da46fe95a16bed2a0f796fc92deba00adbbb0d99a1bd79339c9212bd16e8e766 | adapted | 0 | E1,E2,E3,E3prime | greek_mmlu | All:test:5299 | 1.000000 |
| no_robots | dd49e255193bc02ee4d6aeca33d3542313019d138611790895456d5b4ed25354 | adapted | 3 | E1,E2,E3,E3prime | greek_mmlu | All:test:4860 | 1.000000 |

## Near-duplicate hits retained

None.
