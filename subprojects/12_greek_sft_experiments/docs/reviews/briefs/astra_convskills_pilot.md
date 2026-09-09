# Brief: conversation-skills suite, PILOT outputs (status: QUEUED lane set, pilot generated 2026-09-09/10; findings will change the lanes before they are scaled after the Codex reset on 15 Sep)

## What it is for
Multi-turn skills our 8B Greek model lacks (owner's stress chats, docs/CHAT_REVIEW + DIALOGUE_REVIEW): remembering and quoting the conversation (S1), keeping a standing instruction for the rest of the dialogue and revoking it (S2), editing the previous answer on request (S3) and chained edits (S3c), stopping a repeated tic when told (S4, planted tics in earlier answers are context only), using facts stated early in the dialogue without being reminded (S5m inference memory). Targets are written by Sol (gpt-5.6-sol) from authored neutral base rows and verified by regex/mechanical checks; every row then passes the Greek correction editor (Sol, language-only edits, constraint guard).

## Your earlier review of the PROMPTS (before generation) was applied
Full-sentence S1 targets + overlap check; count phrased «πριν από αυτό» and off-by-one rejected; planted tics `train: false`; neutral base pool restricted (length/no_exclamation/greek_only/monotonic_only/register/question-mark families) with a 10% held-out split; per-lane seeds; S2 instruction after 1–3 exchanges, short bases for tight limits, strict greeklish (no Greek letter at all), natural acceptances («Θα απαντώ με μία πρόταση.»); six stop phrasings in S4; new lanes S3c and S5m.

## Pilot results (mechanical verification, before the correction pass)
| lane | rows | verified | weak kinds |
|---|---|---|---|
| S1 recall | 150 | 84.7% | list 25% (5/20), said_about 68% |
| S2 standing instruction | 249 | 75.5% | greeklish 17.9% (7/39), no_questions 56.1%, one_sentence 77.8% |
| S3 edit | 250 | 92.0% | shorter 69.6% |
| S3c chained edit | 100 | 95.0% | — |
| S4 stop the tic | 75 | 100% | — |
| S5m inference memory | 150 | 95.3% | vegetarian 87% |
Known defect found while reviewing: the queue's assembly glob `S[1-4].jsonl` left S3c and S5m out of the first correction pass; they are corrected separately and merged before this review's sample is drawn (rows_all.jsonl). Unverified rows are dropped, not repaired.

## What to judge (sample rows attached: id, turns, meta, edit_changes)
1. Outputs vs intent: does each row actually teach the skill named in meta.kind, or does the mechanical check pass rows that a careful human would reject (e.g. S1 answers that list the user's requests verbatim instead of summarising; S2 answers that obey the letter of the limit but lose the substance; S3 edits that change content; S5m answers that mention the facts without using them)? Count in the sample by lane.
2. Verification design: which checks are too weak (false pass) and which too strict (the 18% greeklish and 25% list yields: real failures by the writer, or the checker rejecting good rows)? Give the rule to change.
3. The correction editor's effect on multi-turn rows: any edit that broke a standing instruction, a quote, a planted tic context, or the memory facts?
4. Dialogue naturalness and diversity: base-row reuse across dialogues, repetitive user phrasings, unnatural acceptances, anything that would teach a tic of its own.
5. Should any lane be dropped, merged, or redesigned before scaling to ~3–5k rows, and what sample sizes per lane make sense for the training arm?
Disposition: BLOCKER/HIGH are applied before scaling; MEDIUM/LOW logged.
