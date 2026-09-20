# Pilot: eight samples per prompt, rubric v2.2 with issue tags (16 Sept)

Judge Sol gpt-5.6-sol, medium effort, `--rejudge-share 0`, rubric `data/rlhf/prompts/judge_rank4_v2_en.txt` (v2.2, sha16 ce30cb1696adc17b); v2.1 kept as `judge_rank4_v21_en.txt`. Batch 1 = the original four samples of all 50 prompts (50 calls, 0 errors); batch 2 = four new samples for the 34 prompts that had no reinforce-worthy reply under v2.1 (34 calls, 0 errors).

## Positives and pairs per slice

| slice | prompts | resampled | ≥1 reinforce v2.1 (4) | ≥1 reinforce v2.2 (4) | ≥1 reinforce v2.2 (8) | real pair v2.2 (4) | real pair v2.2 (8) |
|---|---|---|---|---|---|---|---|
| maths EL | 5 | 4 | 1/5 | 1/5 | 2/5 | 1/5 | 2/5 |
| maths EN | 5 | 4 | 1/5 | 1/5 | 2/5 | 0/5 | 1/5 |
| IF | 10 | 8 | 2/10 | 2/10 | 4/10 | 2/10 | 4/10 |
| multi-turn | 8 | 5 | 3/8 | 3/8 | 4/8 | 2/8 | 3/8 |
| safety | 5 | 1 | 4/5 | 4/5 | 4/5 | 4/5 | 4/5 |
| English | 7 | 5 | 2/7 | 2/7 | 2/7 | 2/7 | 2/7 |
| forum | 10 | 7 | 3/10 | 3/10 | 3/10 | 3/10 | 3/10 |
| **all** | **50** | **34** | **16/50** | **16/50** | **21/50** | **14/50** | **19/50** |

Of the 34 prompts resampled, 5 got a reinforce-worthy reply in the new four (15 %); 0 of them had one under v2.2 on the *original* four that v2.1 had not called positive.

## v2.1 → v2.2 verdict agreement (the same 200 replies, same four samples)

183/200 replies keep the same absolute verdict (91.5 %). Same top-ranked sample on 41/50 prompts.

| v2.1 ↓ / v2.2 → | reinforce | neutral | discourage |
|---|---|---|---|
| reinforce | 26 | 1 | 0 |
| neutral | 0 | 22 | 11 |
| discourage | 0 | 5 | 135 |

Verdict totals: v2.1 {'discourage': 140, 'reinforce': 27, 'neutral': 33}; v2.2 batch 1 {'discourage': 146, 'reinforce': 26, 'neutral': 28}.

## Verdict distribution of the 136 new samples (batch 2)

| slice | reinforce | neutral | discourage | unusable |
|---|---|---|---|---|
| maths EL | 2 | 0 | 14 | 9 |
| maths EN | 1 | 4 | 11 | 11 |
| IF | 2 | 11 | 19 | 6 |
| multi-turn | 1 | 2 | 17 | 14 |
| safety | 0 | 0 | 4 | 2 |
| English | 0 | 1 | 19 | 16 |
| forum | 0 | 3 | 25 | 11 |
| **all 136** | **6** | **21** | **109** | **69** |

For comparison, batch 1 (200 replies, the same prompts' first four): reinforce 26, neutral 28, discourage 146, unusable 77.

## Issue tags (batch 1 + batch 2, 336 replies)

| tag | maths EL | maths EN | IF | multi-turn | safety | English | forum | all |
|---|---|---|---|---|---|---|---|---|
| wrong_substance | 33 | 28 | 21 | 25 | 11 | 42 | 56 | 216 |
| fabricated_fact | 3 | 9 | 14 | 15 | 10 | 29 | 25 | 105 |
| misread_request | 7 | 10 | 19 | 21 | 7 | 21 | 18 | 103 |
| thin_or_vague | 0 | 1 | 14 | 5 | 5 | 7 | 9 | 41 |
| evasive | 0 | 0 | 1 | 0 | 1 | 2 | 1 | 5 |
| ignored_instruction_or_format | 0 | 3 | 54 | 12 | 0 | 9 | 0 | 78 |
| wrong_language_or_greeklish | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| poor_greek | 1 | 0 | 16 | 2 | 3 | 1 | 7 | 30 |
| repetitive_or_stalled | 6 | 4 | 3 | 16 | 1 | 8 | 4 | 42 |
| curt_or_dismissive | 0 | 0 | 0 | 8 | 2 | 3 | 0 | 13 |
| servile_or_padded | 3 | 2 | 6 | 3 | 2 | 22 | 5 | 43 |
| unsafe_compliance | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| over_refusal | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 2 |
| **any tag** | 33 | 32 | 67 | 42 | 20 | 46 | 64 | 304 |

No off-vocabulary tag was returned: the judge stayed inside the 13-tag vocabulary.

## Consistency: reinforce with a disqualifying tag

0 violations: no reply carries wrong_substance or fabricated_fact together with the verdict "reinforce". The rubric rule holds.


## Reading

1. **Doubling the samples buys little.** Four more samples on the 34 prompts without a positive produced a reinforce-worthy reply on 5 of them (15 %): 16/50 positives at four samples become 21/50 at eight, real pairs 14/50 → 19/50. The marginal yield of the second four (5 prompts per 136 samples) is a fifth of the first four (16 prompts per 200 samples). Sampling alone will not close the gap on the prompts the model cannot do; the §24 fallbacks (written reference replies, or negative-only training) still carry the rest.
2. **The resampled prompts are the hard ones, and stay hard.** 69/136 of the new replies are unusable (50.7 %) against 77/200 in batch 1 (38.5 %), and 109/136 are "discourage". Where the model fails it fails on substance, not by variance: forum 0/7 and English 0/5 resampled prompts gained a positive, maths gained 2, IF 2, multi-turn 1.
3. **v2.2 did not move the positives.** The 26 "reinforce" replies of v2.2 are a subset of v2.1's 27 on the same 200 replies, and the set of prompts with a positive is identical (16/50). The 17 changed verdicts are all in the neutral/discourage band (11 neutral → discourage, 5 discourage → neutral, 1 reinforce → neutral), i.e. adding issue tags tightened the negative end slightly without loosening the bar for a positive.
4. **The tags name the failures we already suspected, and rank them.** 216 wrong_substance and 105 fabricated_fact over 336 replies — 230 replies (68.5 %) carry at least one of the two, which is also why the positives are scarce. Per slice the profile is specific: IF is dominated by ignored_instruction_or_format (54 of 78 such tags) and carries half the poor_greek (16/30); multi-turn holds most of repetitive_or_stalled (16/42) and curt_or_dismissive (8/13); English is where servile_or_padded (22/43) and fabricated_fact (29/105) concentrate; forum is almost pure wrong_substance (56). unsafe_compliance and wrong_language_or_greeklish were never tagged — the two failures the SFT round did fix.
5. **The rule holds mechanically.** 0 of 336 replies carry wrong_substance or fabricated_fact together with "reinforce", so the disqualification sentence in v2.2 is enforceable as a filter and can be used as a cheap validity check on the full run.
