# Dialogue sampling addendum: quality-dependent depth
Status: proposed investigation design, updated from the owner's 16 September instruction. No rollout or provider spending authorized by this document beyond the existing user scope. The existing single-turn release is unchanged.

## Objective
Distinguish (a) preventing the first serious failure and (b) recovering from an actual failure later. Do not assume every dialogue eventually fails, or that the first visibly bad turn is always the highest-value learning opportunity. Measure this under a declared Apertus checkpoint, decoding configuration and user-simulator policy.

Full trajectory generation and turn annotation precede the choice of preference-sampling points. Turn depth alone must not set the training distribution.

## Raw measurement trajectories
- One ordinary, unselected Apertus sample per assistant turn. Record checkpoint, template, sampling, token usage, seed where supported, and each exact prefix/response hash.
- Do not use best-of-N selection, judge rejection, or silent retry to improve measurement histories. Such rollouts are a different policy and need a separately labelled experiment.
- User follow-ups may be Sol-generated but must use only actual preceding history and a frozen user-goal/state policy. Natural follow-ups, valid changes and spontaneous corrections must be distinguished from deliberately injected adversarial challenges.
- Keep existing assistant turns byte-for-byte. No teacher-written replacements in measurement histories.
- Start with a declared maximum of 8 assistant turns, subject to pricing and context limits; allow genuine task completion. This is a proposed pilot horizon, not an empirical optimum. Record natural ending, token-limit truncation, tool failure and budget termination separately.
- Generate the full planned trajectory even if an early failure appears, unless completion or a necessary stop condition occurs. Later turns measure persistence, escalation and recovery.
- Preserve no-failure trajectories. Conclusions only cover observed horizons and this simulator; deeper unseen behaviour is unknown.
- Bootstrap simulator openings from the released seed contract; align the richer rollout receipt with Fable before integration. Never treat 35 reserved slots as 35 completed trajectories.

## Turn annotation contract
For each assistant response: trajectory_id, assistant_turn_index, prefix_sha256, response_sha256, language, task family, cumulative context tokens, current task/constraints, local_quality (good/minor/serious/unjudgeable), issue tags, evidence spans, confidence, verifiability/reference result, prior_failure_state, new_error, propagated_error, recovery_opportunity, recovery_success.
Suggested dimensions: factual/mathematical correctness; request and constraint satisfaction; context retention; uncertainty/false-premise handling; helpfulness/task progress; safety discrimination; dialogue tone. Keep dimension scores rather than collapsing everything into an opaque number.

Serious means the response materially defeats the user's task or violates a critical constraint/boundary; minor wording disagreement is not serious. Calibrate a small stratified sample, especially all borderline first-serious-failure labels and factual claims without an oracle. Sol uncertainty is not evidence of a model failure.
Annotators judge each response using its prefix and available reference only. No later user complaint or later assistant text may redefine what the response should have known. Compute trajectory state/first-failure indices from those prefix-local labels afterwards. This avoids hindsight leakage.
Use batching for independent annotation packets where context permits; keep IDs, separate prefix boundaries and source references. Do not assume batched review is error-free; audit disagreements.

## Measurement before training allocation
Report language/task-conditioned tables and plots of:
1. Quality x assistant-turn depth, with reached-depth denominators and cumulative-token bins.
2. First serious failure by depth, plus no observed failure and explicit stopping/censoring reasons.
3. Failure onset risk among trajectories that reach a depth without a prior serious failure.
4. Quality conditional on an earlier failure, next valid recovery opportunity, recovery delay and recurrence.
5. Unjudgeable share and uncertainty; avoid pretending sparse joint cells are precise estimates.
6. Candidate preference yield at selected points, after the initial annotation.

Keep the observed raw distribution distinct from any enriched training sample. A tiny budgeted pilot is diagnostic, not a population-level guarantee. Natural completion and externally truncated trajectories cannot be relabelled as later successes or failures.

## Sampling points
For a trajectory prefix h_t ending in the user's turn:
- Prevention: select h_t immediately BEFORE the first seriously bad assistant reply a_t. Sample alternatives to a_t. Do not include a_t in the prompt. This teaches a better response at the failure boundary.
- Earlier warning: if a minor issue clearly precedes the serious failure, optionally select that earlier prefix too, based on its own local task violation. Temporal precedence does not prove causality.
- Recovery: choose a later h_k containing the genuine earlier mistake and actual user follow-up. Sample alternatives to a_k; do not fabricate a correction opportunity.
- Retention/control: sample good turns and no-failure trajectories across depth, languages and tasks. Otherwise the dataset will overrepresent distressed conversations and opportunities to apologize.

Prioritise prevention in the first comparison, but do not lock an unsupported prevention/recovery percentage before the quality-depth and candidate-yield tables exist. Choose quotas at trajectory level, retain minimum good-context coverage, then apportion within depth/error/language strata. Default maximum two selected points per trajectory (one prevention, one recovery); control points can come from separate good trajectories. Log any override and cap per-trajectory training contribution.

Selection receipt: stratum definition, eligible count, selected count, random seed/probability where used, intended training weight, selected prefix hash, reasons, and observed candidate yield. A deterministic top-error selection is biased enrichment, not a representative sample. Do not pool it into raw quality estimates.

## Preference construction
Reuse the original Apertus response as a candidate and initially draw two fresh alternatives at the selected identical prefix. Judge candidates with randomized order and hidden original/new status. Require a meaningful preference and an acceptable chosen answer; skip ties/all-bad sets or explicitly budget a capped resampling attempt. Do not presume a low-rated original implies another sample will be better.
For DPO, chosen/rejected completions share EXACTLY the same prompt/history; train the selected completion tokens, with all history tokens masked, including earlier bad assistant turns. Never pair a prevention completion with a recovery completion because their histories differ. The loss-mask and pair-assembly checks must be tested in Fable's actual training pipeline.
The DPO pairwise framing is from Rafailov et al., https://arxiv.org/abs/2305.18290 . The trajectory collection, strata and budget scheme here are our proposed design, not a result established by that paper.

After choosing a replacement at an early turn, the original later suffix is no longer a valid continuation of that replacement. Keep it only for the original raw trajectory/recovery context; regenerate a branch if a separate causal outcome experiment requires it. A preference win is not proof that the alternative prevents later deterioration.

## Economical full-information design
Save branches, not observed trajectory depth:
- Generate N raw trajectories, mean L assistant turns, with one sample at each turn.
- Retain/annotate every observed turn.
- Select m prefixes and generate K-1 alternatives each, reusing the original.
- Assistant generation count is approximately N*L + m*(K-1), instead of B*N*L for best-of-B at every turn.
Illustration only: N=100, L=8, m=100, K=3 gives 1,000 assistant completions versus 3,200 for best-of-4 every turn. This is a completion-count comparison, not a token/CHF/EUR estimate or an authorized run size. Prefix length, caching, user simulation and judging costs still matter.

This retains all measured turns of the same raw trajectories; it does not reveal ungenerated counterfactual branches. Initially do not use quality-triggered early stopping to save money, because it removes precisely the post-failure information of interest.
If scale later demands adaptive stopping, retain a separately sampled full-horizon measurement panel and record inclusion/continuation probabilities. Be explicit that censored trajectories have less individual information; weighting cannot reconstruct their actual unseen suffixes. Do not claim that alternative is lossless.

## Cost, ownership and next implementation
No GPU spending in this addendum. Existing total Prime Intellect cap EUR5 remains. Provider setup, download time, billed storage/other charges and shutdown reserve count; live rate and throughput must be measured before choosing N. Sol call/token usage is a separate ledger and also needs a cap.
Fable's board currently proposes best-of-N at every turn; that must not drive raw measurement histories. Posted a coordination message explaining the distinction. Existing single-turn production work can continue independently.
Next dialogue implementation: trajectory/annotation schemas, per-prefix masking and no-future-information checks, sampling-policy/selection receipt, quality-depth report, bounded target-model pilot, then empirical allocation. The current max_assistant_turns=4 opening metadata is an older default; a horizon-8 investigation requires an explicit versioned override, not silent reinterpretation.
