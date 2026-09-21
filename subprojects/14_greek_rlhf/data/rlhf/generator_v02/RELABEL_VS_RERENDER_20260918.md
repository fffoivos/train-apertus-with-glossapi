# Relabel vs re-render: what the review repair cycle costs, and what of it is recoverable

Measured on `runs/R3-main/` (round 3, generator 0.2). No model calls were made for this analysis;
everything comes from the run's own instances / renderings / reviews / prompts files.
Author: fork session 200fc6, 18 September 2026.

## The cycle, in numbers

| | count |
|---|---|
| instances (slots with a spec) | 418 |
| renderings (a model writing the prompt from that spec) | 614 |
| reviews (one per rendering) | 614 |
| accepted prompts | 403 |
| **total generation calls** | **1,646** (4.1 per accepted prompt) |

169 of 614 renderings (27.5%) failed review.

## The failures are two different things

**Hard — 57 hard-only plus 13 mixed.** `missing_given` 38, `dropped_constraint` 14,
`changed_value` 13, `task_changed` 6, `unnatural` 6, `wrong_language` 2,
`added_fact_changes_answerability` 1. A required fact is absent or a value was silently altered.
The prompt is broken. Re-render is correct.

**Soft — 99 slots.** `attitude_not_realised` 47, `register_not_realised` 30,
`detail_not_realised` 28. The text may be perfectly good; it simply is not the *cell* the manifest
ordered. All 99 eventually produced an accepted prompt, at a cost of **184 renderings** — about 85
beyond the first, each of which also pays for a review.

## "Soft" is not uniformly soft

Reading the reviewer notes on all 99 soft-only failures:

- **88 are tone or length only** — "it is direct rather than skeptical", "does not convey the
  impatience or situational frustration required by the frustrated label", "orderly and concise
  rather than rambling". The prompt works; the label is wrong. Safely relabellable.
- **11 are script or orthography** — "written in standard Greek script rather than the required
  Greeklish register", "mixes Greeklish with Greek script". Here the register **is** the testable
  property of the prompt, not a description of its tone. Relabelling these hollows out the slot.
  **Not relabellable.**

## What relabelling saves

Keeping the first rendering for the 88 tone/length cases avoids roughly 76 re-renders and their
76 reviews: **~152 of 1,646 calls, about 9% of the generation budget.**

An earlier estimate of ~20% was wrong: it counted renderings rather than slots and did not separate
the script cases.

## The condition, which is not optional

Relabelling accepts whatever the writer produced instead of what the manifest ordered. Over many
slots that biases the corpus toward the writer's defaults — plausibly neutral, polite and
mid-length. That is the same direction as the brevity skew already found in the pair data, where
chosen replies are shorter in 58% of training pairs and a "pick the shorter reply" rule scores .611
on the 54-pair dev set against the best arm's .643. Relabelling must therefore not be allowed to
quietly amplify it.

1. **Keep re-render** for every hard reason, and for the script/orthography subset of
   `register_not_realised`. Detect that subset by whether the ordered register names a script or
   orthography rather than a tone.
2. **Relabel rather than re-render** for tone and length, recording BOTH the ordered value and the
   realised value on every affected slot.
3. **Report the realised distribution alongside the ordered one as a standing artefact of every
   round**, not as a one-off check. If the realised values collapse toward a single default, the
   saving is buying a less diverse corpus and the policy reverts.

## Window-cost instrumentation (adopted 18 September, applies to all runs from the next round)

`used_percent` on the Codex weekly window is integer-granular, so a synthetic probe would need
~150 judging batches to move it one tick — the whole 1% measurement cap for one significant figure.
Deriving the rate from rollout history also fails: tokens per 1% across the window's 45 observed
steps range from 94k to 20.5M, a 200x spread, because concurrent sessions draw on the same window
unobserved. No probe was run; consumption for this analysis was 0.0%.

Instead, every real generation and judging run records, in a durable append-only log:
timestamp and observed `used_percent` BEFORE, timestamp and observed `used_percent` AFTER, the
batch or call count, and the effort. Raw readings at both ends, never only the delta — four
sessions share this window, so a delta alone cannot be distinguished from someone else's draw.
The cost per batch and per accepted prompt then accumulates across runs instead of resting on a
single measurement.
