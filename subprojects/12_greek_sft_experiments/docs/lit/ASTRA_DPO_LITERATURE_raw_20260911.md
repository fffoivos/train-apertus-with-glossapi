# Astra review: dpo_literature

Date 2026-09-11 17:44 · model gpt-6-astra (asserted from rollout rollout-2026-09-11T17-32-29-01a090e2-5ce9-74b0-a78c-d3e95990db1b.jsonl) · effort xhigh · 11.8 min · prompt 22,092 chars · limit deltas {('codex', '10080'): 0.0} · brief `docs/reviews/briefs/astra_dpo_literature.md`

# DOC A — Technical parameters of DPO

## 1. Verdict

**Proceed with a bounded DPO pilot, but revise the draft before generating the full preference set.** Sampling from R3, preserving fp32 updates, using verifiers where applicable, and evaluating dialogue behaviour are sound choices. The proposed hyperparameters are plausible starting points, not established optima for Greek Apertus. The principal problems are an unqualified loss implementation, an overstated guarantee from the SFT anchor, inadequate treatment of seed and evaluation uncertainty, and incorrect rater-cost arithmetic. This is a knowledge-based literature review: citation lookup was unavailable, and **[verify] marks uncertain bibliographic details or exact reported results**. I checked the supplied plan and its arithmetic; I did not inspect code, checkpoints, transcripts, or sample rows. Consequently, none of the supplied behavioural failure rates is independently verified. All corrective recommendations concern the prospective DPO phase; they do not justify drastic changes to completed SFT datasets.

## 2. Findings ranked by severity

| Severity | Finding and evidence | Concrete fix |
|---|---|---|
| **HIGH** | **Rater quota is understated tenfold.** Draft §4.6: \(8{,}000 \times 0.004\%=32\%\), not 3.2%. Two iterations give 64%, not approximately 7%. If every call includes 18,000 fixed input tokens, those calls contain **144 million fixed input tokens per iteration**, before variable content. These calculations use the draft’s unverified per-call quota measurement. | Correct the arithmetic and measure actual quota consumption on a representative batch. Distinguish tokens, billing, rate limits, cached inputs, and any CLI-specific quota estimate. |
| **HIGH** | **The stated RL budget exceeds 20 node-hours before GRPO or contingency.** Draft §5 totals \(3.5+4.0+13.8=21.3\) node-hours. Evaluation accounts for 64.8% of that total. The proposed additional GRPO phase adds another 6–10 estimated hours. | Budget one complete iteration first. Make iteration two conditional on measured costs and development results, with the final evaluation reserved in advance. |
| **HIGH** | **“TRL DPOTrainer, β=0.1, RPO α=1” does not specify a reproducible objective.** Token sums versus token means, chosen-NLL reduction, completion masks, and reference-log-probability computation change the effective objective. Draft §3 does not bind these details. | Freeze the trainer version and explicitly write down the loss, reductions, masks, tokenizer/chat-template revision, and reference. Qualify them on a small batch before producing a training run. |
| **HIGH** | **The SFT anchor does not guarantee that Greek likelihood or capability is preserved.** Draft §3 asserts it is included “so Greek likelihood does not collapse.” Chosen-response NLL protects the distribution of those chosen responses; it does not automatically protect unrelated Greek tasks, English retention, or discourse behaviour. | Treat the anchor as a hypothesis. Monitor held-out Greek and retention losses and compare anchored DPO with an otherwise identical control. Use representative SFT replay if preservation beyond the chosen responses is required. |
| **HIGH** | **“Two seeds” and “no drop beyond seed noise” are not sufficient promotion definitions.** Two observations provide a very unstable estimate of training-seed variation. Evaluating the “best seed only” is valid only if selection uses a separate development set. | Select checkpoints on development data; reserve the final battery. Report both seeds on inexpensive evaluations. Use paired, dialogue-level uncertainty estimates for the primary outcome and specify meaningful regression margins beforehand. |
| **MEDIUM** | **The bf16 conclusion is overstated.** Draft §3 reports 97.65% unchanged weights in a different experiment at \(5\times10^{-6}\), then calls bf16 DPO at \(5\times10^{-7}\) a “no-op.” The measurement is not supplied, and unchanged-weight percentage does not establish unchanged behaviour. | Preserve fp32 accumulation/master parameters, but describe the risk as update quantization. Verify actual updates under the exact optimizer and training path. |
| **MEDIUM** | **Several literature statements are presented as universal rules.** Examples include DPO requiring a 10–50× smaller LR, on-policy pairs always beating rewrites, and a universally useful one-to-three-epoch window. | Present these as empirical patterns with counterexamples and implementation dependencies, as below. |

## 3. What is good and should not be changed

- **Start from the evaluated R3 checkpoint.** The failures supplied in the brief mostly concern arm B; R3 may materially change both the remaining errors and sampling yield.
- **Generate candidates from the policy being improved.** This directly exposes its current failure modes.
- **Use a frozen reference for the first iteration.** This provides a clear, reproducible comparison with R3.
- **Keep fp32 parameter updates and bf16 computation**, subject to checking the actual implementation.
- **Preserve assistant-only, turn-specific supervision.** Earlier assistant turns should usually provide context, not become additional preference targets.
- **Evaluate the targeted dialogue failures.** Generic benchmark improvements cannot establish that redirect handling, retention, or correction behaviour improved.

## 4. Technical answers and recommended starting configuration

### β: what it controls, and why its numerical value is easy to misinterpret

Standard DPO uses

\[
\mathcal L_{\mathrm{DPO}}
=
-\log \sigma\!\left(
\beta
\left[
\log\frac{\pi_\theta(y_w\mid x)}{\pi_{\mathrm{ref}}(y_w\mid x)}
-
\log\frac{\pi_\theta(y_l\mid x)}{\pi_{\mathrm{ref}}(y_l\mid x)}
\right]
\right).
\]

Its derivation relates the optimal policy to a reward through

\[
\pi^*(y\mid x)\propto
\pi_{\mathrm{ref}}(y\mid x)\exp(r(x,y)/\beta).
\]

Thus, for a fixed reward scale in the idealized optimization problem, larger β corresponds to stronger reference regularization. **In an actual finite training run, β also changes gradients and saturation.** At initialization, when policy equals reference, the multiplier on the preference-gradient difference is β/2. Increasing β therefore does not simply mean “smaller updates.” Learning rate, training duration, reward scale, and the loss reduction interact. [Rafailov et al., *Direct Preference Optimization*, NeurIPS 2023, arXiv:2305.18290](https://arxiv.org/abs/2305.18290).

For **summed completion log probabilities**, approximately **0.05–0.5** is a reasonable range to consider from common recipes; **0.1** is a defensible starting point. This is a practical range, not a literature-established optimum.

Do not transfer this range directly to a length-normalized objective. Dividing log probabilities by completion length changes their scale substantially. SimPO, for example, uses average token log probability and an additional target margin; its β values are not directly comparable with standard summed-log-probability DPO. [Meng et al., *SimPO*, arXiv:2405.14734](https://arxiv.org/abs/2405.14734).

**Recommendation:** begin with standard summed-log-probability DPO at β=0.1. Consider 0.05 or 0.2 only if the first pilot identifies under-learning, excessive drift, or rapid saturation. Do not spend the initial budget on a full Cartesian hyperparameter sweep.

### Learning rate and schedule

A useful **initial search region** for full-parameter DPO on a 7–9B model is roughly **\(2\times10^{-7}\) to \(2\times10^{-6}\)**. This is an engineering recommendation informed by conservative open recipes, not a universal boundary.

Zephyr is a relevant precedent for learning rates around **\(5\times10^{-7}\)** and multiple epochs. Its commonly reproduced recipe is substantially more conservative than its SFT stage. Exact configuration revisions should be checked before copying them. [Tunstall et al., *Zephyr: Direct Distillation of LM Alignment*, arXiv:2310.16944](https://arxiv.org/abs/2310.16944).

Why can DPO benefit from a lower LR than SFT?

- It changes an already competent, already instruction-tuned policy.
- Its negative term actively suppresses rejected responses.
- Preference datasets can be small, correlated, and noisier than their apparent size suggests.
- A small set of style preferences can move broad response behaviour.

**There is no derivation requiring “10–50× lower than SFT.”** That ratio describes some recipes. Different objectives and large iterative pipelines use different scales; the Llama 3 report is evidence against treating one small-model recipe as a universal law. [Dubey et al., *The Llama 3 Herd of Models*, arXiv:2407.21783](https://arxiv.org/abs/2407.21783).

For this case, **\(5\times10^{-7}\)** is a sensible conservative start. Use approximately **5% warmup followed by cosine decay**, and report the actual number of optimizer steps. With only a few thousand pairs, percentages can correspond to just a handful of steps.

### Epochs, overfitting, and falling chosen likelihood

**One epoch is a reasonable first ceiling; one to three epochs is not a law.** Zephyr demonstrates that three epochs can work in a particular setting. Other recipes use shorter exposure. Pair count, effective batch size, duplicates, LR, and preference difficulty determine how much learning an “epoch” represents. [Tunstall et al., arXiv:2310.16944](https://arxiv.org/abs/2310.16944).

DPO constrains a **difference of log-probability ratios**. It can improve that difference by reducing rejected likelihood more rapidly than chosen likelihood. Therefore:

- chosen likelihood can fall;
- rejected likelihood can fall further;
- DPO accuracy and margin can improve simultaneously.

Probability mass must go somewhere else, potentially to unobserved responses. This is a real failure mode, but falling chosen likelihood alone does not prove capability collapse. The consequences depend on where the mass moves and whether the preference data cover desirable behaviour.

Relevant responses include:

| Method | What it changes | Limitation for your case |
|---|---|---|
| **Chosen-response NLL / RPO-style anchoring** | Adds positive likelihood pressure on chosen responses. Iterative reasoning preference optimization is one relevant precedent. | Does not preserve capabilities absent from the chosen data. α depends on the reduction. [Pang et al., arXiv:2404.19733](https://arxiv.org/abs/2404.19733); **[verify exact TRL correspondence]**. |
| **DPO-Positive / DPOP** | Penalizes undesirable decreases in chosen likelihood relative to the reference. | Adds an objective-specific constraint and coefficient; not a free guarantee of better generalization. [Pal et al., *Smaug: Fixing Failure Modes of Preference Optimisation with DPO-Positive*, arXiv:2402.13228](https://arxiv.org/abs/2402.13228). |
| **Cal-DPO** | Calibrates the absolute scale of implicit rewards, addressing a limitation of purely relative fitting. | Reward calibration is different from calibrating a Greek judge. [*Cal-DPO: Calibrated Direct Preference Optimization for Language Model Alignment*, arXiv:2412.14516](https://arxiv.org/abs/2412.14516), **[verify citation metadata]**. |
| **IPO** | Uses a finite-target preference objective rather than driving separable logistic preferences indefinitely. | Changes the objective and tuning; it is not simply DPO with a smaller LR. [Azar et al., AISTATS 2024, arXiv:2310.12036](https://arxiv.org/abs/2310.12036). |

For your pilot, prefer **one understandable anchor ablation** over trying all these methods. Check results halfway through and after one epoch. Continue only if held-out behaviour is improving.

### Batch size, pair count, and diminishing returns

For the first run, **64 pairs per optimizer update** is reasonable. Each pair generally entails two completion sequences, so “batch size 64” must explicitly mean pairs, not flattened sequences.

At that batch size:

- 3,000 pairs give approximately 47 updates per epoch;
- 4,000 give approximately 63;
- 7,000 give approximately 110.

There is no established answer to “how many pairs are enough” for your failures. A few thousand well-targeted pairs may move narrow behaviours; they do not establish broad multilingual alignment.

Published scales differ considerably:

- UltraFeedback/Zephyr-style training: roughly **60,000 preference pairs**, depending on binarization and filtering. [Cui et al., arXiv:2310.01377](https://arxiv.org/abs/2310.01377); [Tunstall et al., arXiv:2310.16944](https://arxiv.org/abs/2310.16944).
- Tülu 3: **hundreds of thousands**, roughly \(3\times10^5\), in its preference mixture; **[verify exact count and release]**. [Lambert et al., arXiv:2411.15124](https://arxiv.org/abs/2411.15124).

Those are successful recipe sizes, **not points on a controlled universal scaling curve**. They differ in prompts, models, raters, objectives, and evaluations.

For your setting, prioritize **distinct prompt families and reliable contrasts** over multiplying correlated pairs from the same quartet. Initially cap each prompt at one training pair.

### Reference choice and reference-free alternatives

**Iteration one:** use R3 as both initialization and frozen reference.

**Later iterations:** two defensible choices exist.

- Keep R3 as reference: preserves a stable anchor and makes cumulative displacement easier to interpret.
- Reset the reference to the previous policy: treats each iteration as a local update, potentially allowing more cumulative movement.

A sequence of locally regularized updates does **not** establish a bound on divergence from R3. If the training reference changes, continue measuring divergence and regressions against R3.

Reference-free alternatives:

- **SimPO** uses length-normalized policy log probability and a target reward margin. It avoids reference-model computation and reports competitive or better results than DPO in its evaluated settings. Its headline improvements include up to approximately **6.4 points on AlpacaEval 2 and 7.5 on Arena-Hard**; **[verify exact comparison and paper version]**. These are not Greek or multi-turn results. [Meng et al., arXiv:2405.14734](https://arxiv.org/abs/2405.14734).
- **ORPO** combines an SFT objective with an odds-ratio preference term and removes the explicit reference model. It is a distinct training recipe, not a drop-in assurance of lower regression. [Hong et al., *ORPO*, arXiv:2403.07691](https://arxiv.org/abs/2403.07691).

**Recommendation:** use reference-based DPO first. Precomputed reference log probabilities capture much of the memory/computation advantage without changing the algorithm.

### Length normalization and length exploitation

Three different problems must be separated:

1. Longer answers can receive higher judge scores.
2. Sequence log probabilities depend on length.
3. Some requests genuinely require longer answers.

SimPO addresses objective scaling through average token log probability. R-DPO explicitly addresses length as a confound in preference optimization. Neither establishes that a universal 1.5× pair filter is optimal. [Meng et al., arXiv:2405.14734](https://arxiv.org/abs/2405.14734); [Park et al., *Disentangling Length from Quality in Direct Preference Optimization*, arXiv:2403.19159](https://arxiv.org/abs/2403.19159).

The proposed filter is asymmetric:

- a verbose chosen answer can be discarded;
- an excessively terse chosen answer can survive;
- a correct explanation can be discarded against a short non-answer.

**Replace it with task-conditioned review.** Record both lengths, the requested length, and the reason for preference. Audit preferences within length bands and on approximately length-matched pairs.

Length-controlled AlpacaEval is a useful evaluation precedent, but statistical length control does not remove all style or judge biases. [Dubois et al., arXiv:2404.04475](https://arxiv.org/abs/2404.04475).

### Noisy labels: cDPO and robust DPO are different

Conservative DPO-style label smoothing uses

\[
-(1-\epsilon)\log\sigma(z)-\epsilon\log\sigma(-z).
\]

It prevents unlimited certainty in an observed label. For an isolated pair, its finite optimum is

\[
z=\log\frac{1-\epsilon}{\epsilon}.
\]

This is **not the same as estimating and correcting a label-flip process**.

Robust DPO work analyzes noise correction under explicit assumptions, including symmetric preference flips. A correction involving \(1/(1-2\epsilon)\) becomes unstable as \(\epsilon\) approaches 0.5. That theoretical boundary does not imply that 30–40% noisy Greek preferences are practically acceptable. [Chowdhury et al., *Provably Robust DPO: Aligning Language Models with Noisy Feedback*, arXiv:2403.00409](https://arxiv.org/abs/2403.00409).

There is **no universal empirical noise percentage at which DPO breaks**. Systematic errors—always rewarding false concessions or treating valid Greek variants as errors—can be more damaging than the same amount of independent random noise.

Start with **no smoothing after strict pair filtering**. Consider approximately **0.05–0.1** only as an ablation if residual ambiguity remains. Do not set smoothing equal to one minus Sol–human agreement: disagreement is not an estimate of symmetric label noise.

### On-policy, off-policy, and iteration count

The evidence favours including current-policy samples and useful negative examples, especially when the alternative is repeatedly training on a fixed, mismatched preference distribution. Relevant analyses include [Tajwar et al., *Preference Fine-Tuning of LLMs Should Leverage Suboptimal, On-Policy Data*, arXiv:2404.14367](https://arxiv.org/abs/2404.14367) and [Tang et al., *Understanding the Performance Gap between Online and Offline Alignment Algorithms*, arXiv:2405.08448](https://arxiv.org/abs/2405.08448), **[verify second citation metadata]**.

However:

- Data sampled from R3 and then used for a whole epoch become off-policy as training progresses.
- “Iterative DPO with refreshed samples” is a more precise description than continuously on-policy DPO.
- Evidence favouring refreshed samples does not establish that every teacher rewrite is inferior.
- There is no established optimal iteration count for Greek 8B.

**Recommendation:** one complete iteration; a second only if the policy still produces informative contrasts and development gains justify the cost. Two iterations are a reasonable experiment, not a proven requirement.

### Multi-turn credit assignment

For the first run, define each pair as:

> Identical conversation prefix, identical latest user message, two alternative next assistant turns.

Score and train the **target assistant completion only**. Earlier assistant messages remain visible as context but contribute no preference log probability or auxiliary chosen-response loss.

Whole-dialogue DPO is possible, but it optimizes a different object. If candidate dialogues have different earlier answers and therefore different user reactions, the comparison mixes several decisions and different states. That is unsuitable for isolating your “stale after redirect” problem without a more deliberate trajectory-level design.

Important implementation details:

- Keep standing instructions and the relevant previous answer in the prefix.
- Preserve the same prefix in chosen and rejected examples.
- Group splits by source dialogue.
- Cap the number of training pairs derived from one dialogue.
- Evaluate complete rollouts even when training individual turns.

MT-Bench-101 is relevant evidence that multi-turn capability is not captured by single-turn scores. It is not sufficient evidence that preference optimization cannot help multi-turn behaviour. [Bai et al., *MT-Bench-101: A Fine-Grained Benchmark for Evaluating Large Language Models in Multi-Turn Dialogues*, arXiv:2402.14762](https://arxiv.org/abs/2402.14762), **[verify metadata and the particular ablation cited in your companion document]**.

### Packing, sequence length, and memory

Do not assume that a packing implementation validated for SFT is valid for DPO.

Required invariants include:

- separate chosen/rejected identities;
- correct completion-only masks;
- no attention across unrelated packed examples;
- matching position and attention treatment for policy and reference;
- correct per-example reductions after concatenation or packing;
- no truncation of the instruction whose retention is being tested.

For an 8B model, approximate persistent storage with fp32 parameters, fp32 gradients, and two fp32 Adam moments is:

\[
8\times10^9 \times (4+4+4+4)
=128\ \text{GB},
\]

before activations, temporary buffers, communication overhead, or optional low-precision copies. Ideal four-way sharding gives roughly **32 GB per GPU** for those components. A bf16 reference adds approximately **16 GB total**, or 16 GB on each GPU if replicated.

These are arithmetic estimates, **not a measured Clariden memory plan**. GH200 memory configuration and actual sharding must be confirmed.

Use **FSDP or ZeRO-style sharding**, activation checkpointing, and a small microbatch. Precompute frozen-reference completion log probabilities using the exact final tokenization and masks. This can eliminate a resident reference model during optimization.

Start with **4,096 total tokens per candidate**, allowing approximately 3,072 prefix and 1,024 completion tokens, but route longer contexts separately. Do not silently truncate a retention test into a different task.

### Precision at \(5\times10^{-7}\)

bf16 has seven explicit fraction bits. Around 1.0, adjacent representable values differ by \(2^{-7}\approx0.0078\). Around a weight magnitude of 0.01, the spacing is approximately \(6.1\times10^{-5}\).

An optimizer update around \(5\times10^{-7}\) can therefore vanish if immediately rounded into a bf16 parameter. Actual Adam updates depend on moments, gradient scale, and the parameter value, so LR alone cannot establish the fraction lost.

With fp32 accumulation, small updates can accumulate even while the bf16 forward representation remains unchanged for several steps.

Before training, check:

- persistent parameter/master-copy dtype;
- optimizer-state dtype;
- changes after one step and after several steps;
- update-to-weight norm by module;
- new Greek embedding/output rows specifically;
- fp32 accumulation of log-softmax, sequence sums, and loss differences.

The draft’s decision to preserve fp32 updates is good. Its categorical “no-op” claim should be softened.

### What to log

| Category | Minimum useful records |
|---|---|
| Preference fitting | DPO loss, margin distribution, implicit reward accuracy, saturation fraction |
| Likelihood | Chosen and rejected log probabilities, both summed and per token; changes relative to reference |
| Anchor | Chosen NLL, held-out Greek NLL, held-out English/multilingual retention NLL |
| Drift | Estimated KL against R3 on a fixed prompt distribution with current-policy samples; against the iteration reference if different |
| Output distribution | Length quantiles, EOS/truncation rate, language slips, repeated tails, refusals |
| Data | Pair counts by family, veto type, margin class, length ratio, and audit status |
| Optimization | Gradient norms, update norms, learning rate, numerical anomalies |

**DPO reward accuracy is not task accuracy.** Similarly, log-ratio averages on a fixed preference dataset are not automatically an unbiased estimate of current-policy KL. For KL, specify the sampling distribution and whether the quantity is per token or per response.

### What published recipes actually establish

| Recipe | Relevant evidence | What should not be inferred |
|---|---|---|
| **Zephyr-7B** | Approximately 60k synthetic preference pairs; final Zephyr-β MT-Bench score **7.34**. [Tunstall et al., arXiv:2310.16944](https://arxiv.org/abs/2310.16944). | 7.34 is a final-model score, not an isolated DPO improvement or a Greek multi-turn result. |
| **Tülu 3, including 8B** | Open staged SFT → preference optimization → verifiable-reward training, with extensive recipe evaluation. [Lambert et al., arXiv:2411.15124](https://arxiv.org/abs/2411.15124). | Do not attribute the final model’s mathematics/IF improvements entirely to DPO. Exact stagewise benchmark deltas should be extracted from its tables **[verify]**. |
| **Llama 3 family** | Iterative post-training combines preference optimization with other data and selection procedures. [Dubey et al., arXiv:2407.21783](https://arxiv.org/abs/2407.21783). | Final benchmark scores are not a clean experiment on DPO alone. |
| **OLMo 2** | Its post-training follows the broader open staged-alignment direction. [*2 OLMo 2 Furious*, arXiv:2501.00656](https://arxiv.org/abs/2501.00656), **[verify metadata and exact stage recipe]**. | I cannot responsibly supply remembered, isolated 7B DPO benchmark deltas. |
| **SmolLM2** | A relevant small-model recipe, but its largest model is 1.7B. [*SmolLM2: When Smol Goes Big*, arXiv:2502.02737](https://arxiv.org/abs/2502.02737), **[verify metadata and preference stage]**. | It is not a 7–9B scaling datapoint. |
| **Apertus** | No confidently recalled, isolated Greek-Apertus DPO ablation supports a particular setting here. | Exact DPO hyperparameters and expected gains remain **open**. |

I am deliberately not filling missing benchmark cells with plausible-looking numbers. The literature supports trying preference optimization; it does not supply a defensible numerical forecast for your redirect or recap metrics.

### Multilingual and Greek-specific implications

**The stated 14% Greek and 84% Latin-script supervised letters are not language-token proportions.** Latin script includes several languages; tokenizer efficiency changes the relationship between letters, tokens, and loss weight.

Preference training can change behaviour in languages absent from the preference set because parameters are shared. The direction and size of that transfer are task- and model-dependent. **Whether Greek DPO will degrade English or another language in your checkpoint is open.**

Relevant projects need to be distinguished:

- **Aya:** the original Aya model establishes broad multilingual instruction-tuning results; it is not a controlled demonstration of Greek DPO effects. [Üstün et al., *Aya Model*, arXiv:2402.07827](https://arxiv.org/abs/2402.07827).
- **Aya 23:** includes Greek and 8B-scale models, making it a useful comparison target. Exact stagewise preference-training conclusions require checking the report. [Aryabumi et al., *Aya 23*, arXiv:2405.15032](https://arxiv.org/abs/2405.15032).
- **Aya Expanse:** relevant to multilingual synthetic preference training, but I would verify its exact pipeline before transferring a specific recipe. [*Aya Expanse*, arXiv:2412.04261](https://arxiv.org/abs/2412.04261), **[verify citation and training details]**.
- **EuroLLM:** relevant multilingual pretraining and instruction tuning; the initial report does not by itself establish a Greek DPO optimum. [Martins et al., *EuroLLM*, arXiv:2409.16235](https://arxiv.org/abs/2409.16235).
- **Salamandra:** useful European-language coverage and evaluation, but I cannot confidently attribute an isolated Greek preference-training result. [*Salamandra: A Suite of Open Multilingual Large Language Models*, arXiv:2502.08489](https://arxiv.org/abs/2502.08489), **[verify metadata and stages]**.
- **Meltemi:** relevant Greek continued pretraining and instruction tuning. [*Meltemi: The First Open Large Language Model for Greek*, arXiv:2407.20743](https://arxiv.org/abs/2407.20743), **[verify title/identifier]**.
- **Krikri/Llama-Krikri:** I cannot provide a dependable paper identifier or a Greek DPO ablation from memory. Exact checkpoint lineage, preference method, pair count, and stagewise gains are **open**.

For this project, keep a small English/EU-language preservation component and evaluate each language separately. Do not assume either that Greek-only preferences are harmless to English or that multilingual mixing automatically protects Greek.

### Recommended initial configuration

These are **proposed engineering defaults**, not claimed Greek-specific literature optima.

| Parameter | Start | Justification and uncertainty |
|---|---|---|
| Policy/reference | R3 / frozen R3 | Clear first-iteration anchor; same tokenizer and template required |
| Objective | Standard sigmoid DPO with summed completion log probabilities | Simplest interpretable baseline |
| β | **0.1** | Common conservative starting point; tune only after inspecting drift/saturation |
| LR | **\(5\times10^{-7}\)** | Plausible 7–9B conservative scale; exact optimum unknown |
| Schedule | **5% warmup, cosine decay** | Routine choice; report actual warmup/update counts |
| Epochs | **1 maximum initially** | Inspect halfway and at completion |
| Global batch | **64 pairs** | Reasonable compromise; only tens to roughly 100 updates at proposed scale |
| Microbatch | **1–2 pairs/GPU initially** | Increase only after measured memory qualification |
| Chosen-NLL anchor | **α=0.1**, with mean token NLL explicitly defined | Deliberately modest starting weight; compare with α=0. α=1 remains an ablation, not a preservation guarantee |
| Label smoothing | **0 initially** | Filter ambiguity first; try 0.05–0.1 only if justified |
| Gradient clipping | **1.0** | Conservative operational default, not a proven optimum |
| Sequence length | **4,096 total**, approximately 3,072 prefix + 1,024 completion | Inspect truncation; use a separate longer-context lane if needed |
| Precision | **fp32 persistent updates; bf16 autocast** | Prevent loss of small updates |
| Reference compute | Precompute exact masked reference log probabilities | Saves training memory and repeated forwards |
| Packing | Off for qualification; enable only after equivalence checks | SFT packing correctness does not imply DPO correctness |
| Iterations | **1 committed; second conditional** | Fits the evidence and budget better |
| Seeds | Two for the selected full configuration if affordable | Report both on development metrics; do not call two seeds a precise noise estimate |

A possible **20-node-hour envelope** is 1 hour setup/reference qualification, 2 sampling, 4 training and small ablations, 2 development evaluation, 4.3 final battery, 2 final dialogue evaluation, and 4.7 contingency. These are allocations, not measured runtimes. R3’s baseline evaluation must already exist outside this envelope.

## 5. Open questions for the owner

1. Which exact R3 checkpoint, tokenizer, template, and trainer commit will be frozen?
2. Does the current DPO implementation sum or average completion log probabilities, and how does it reduce the auxiliary NLL?
3. What are the **post-R3** failure rates and denominators?
4. Which languages and capabilities require preservation, and what numerical non-inferiority margins are acceptable?
5. Is 20 node-hours a hard cap including all RL evaluation?
6. Can the CLI quota estimate be reproduced on a representative judging batch?

# DOC B — What a preference score should represent: how to define preference

## 1. Verdict

**Define preference as a grounded improvement in satisfying the current request within the actual conversation state, subject to reliable task-specific constraints.** The draft correctly separates verifiers from open-ended judgment, but overstates verifier coverage and gives uncertain judgments excessive veto power. Its most damaging selection rule is dropping every all-pass quartet: passing minimum requirements does not eliminate meaningful quality differences. Preserve explicit truth information for correction tasks, allow ties and uncertainty, and calibrate vetoes separately from overall ranking. A preference label should not mean “Sol liked the prose,” “the answer was longer,” or “the assistant agreed with the user.”

## 2. Findings ranked by severity

| Severity | Finding and evidence | Concrete fix |
|---|---|---|
| **BLOCKER** | **Unvalidated judgments become hard eligibility rules.** Draft §4.3 makes more than two alleged Greek errors a veto, while §4.5 accepts only 80% Greek-error precision. At that threshold, one in five flagged errors could be false. Tone and “invented fact” also lack sufficiently operational definitions. | Keep Greek naturalness and subjective tone advisory until separately calibrated. Restrict hard vetoes to sufficiently reliable, evidence-backed violations. Introduce `unknown` and `not_applicable`. |
| **HIGH** | **“All k pass” is incorrectly equated with “no signal.”** Draft §3 would discard, for example, four factually valid answers where only one addresses the redirect fully. | Retain all-pass quartets when a clear, task-relevant preference exists. Drop genuinely tied quartets. For verifier-only prompts where all candidates earn the same verified outcome, dropping is reasonable. |
| **HIGH** | **Regexes are described as exact semantic rewards.** Draft §2 calls retention, correction handling, and repetition checks “exact.” A retained name can appear in the wrong role; a disclaimer can defeat a naive false-concession regex; lexical overlap can be requested. | Document each checker’s contract. Call its output “checker pass,” not “semantic correctness.” Audit false positives and false negatives on adversarial examples. |
| **HIGH** | **The 95% sycophancy statement lacks its experimental scope.** Draft §1 says preference models prefer sycophantic answers 95% of the time. The cited paper establishes important sycophancy effects, but that sentence is not a justified universal summary. | Locate the exact experiment and denominator before retaining 95%. Until then, use the supported qualitative claim and your own measured flip-rate definition. |
| **HIGH** | **The pairwise-cost comparison is misleading.** Draft §4.2 compares two k-way calls with 12 pairwise calls. Twelve calls are needed for every unordered pair in both orders. A selected chosen/rejected pair requires only two order-swapped calls. | Compare protocols at equal decision quality and the actual number of comparisons needed, rather than assuming a full round-robin tournament. |
| **MEDIUM** | **The calibration targets lack uncertainty and per-axis coverage.** At 120/150 agreement, the approximate 95% Wilson interval is **72.9–85.6%**. At 27/30 position consistency, it is approximately **74.4–96.5%**. | Report counts, intervals, ties, and subgroup results. Do not interpret point estimates as established lower bounds. |
| **MEDIUM** | **A fixed 20% inter-vendor disagreement stop rule conflates different problems.** Draft §4.4 treats disagreements over truth, style, and genuine ties alike. | Classify disagreements by axis and adjudicate hard-veto conflicts first. Use rates and uncertainty within those categories. |

## 3. What is good and should not be changed

- Give judges **English instructions with original Greek content** if that is the established, tested workflow.
- Hide candidate source identity and randomize positions.
- Provide **verified claim truth** for planted correction tasks.
- Ask for quoted evidence, especially for context violations and false capability claims.
- Use the owner’s native-speaker calibration before training.
- Audit with a second vendor.
- Make the next assistant turn the primary unit of preference.
- Keep sycophancy, repetition, and language slips as evaluation outcomes independent of the training judge.

## 4. Answers to the preference-design questions

### What successful recipes mean by “preference”

There is no single empirically privileged scalar called “helpfulness.”

InstructGPT used human comparisons within an instruction-following framework emphasizing helpfulness, truthfulness, and avoidance of harmful outputs. Constitutional AI makes selected principles explicit and uses AI feedback to implement parts of that preference definition. Both encode a normative specification; neither discovers an objective, universal preference ordering. [Ouyang et al., NeurIPS 2022, arXiv:2203.02155](https://arxiv.org/abs/2203.02155); [Bai et al., *Constitutional AI*, arXiv:2212.08073](https://arxiv.org/abs/2212.08073).

For your model, operational preference should prioritize:

1. Correct handling of the **latest request**, including a redirect.
2. Correct use of relevant conversation state.
3. Truthfulness and justified correction handling.
4. Task completeness and usable content.
5. Appropriate Greek and task-conditioned presentation.

These priorities should be explicit. Otherwise, a judge can trade away correctness for friendliness without exposing that trade.

### Rubric, holistic, pairwise, pointwise, or k-way?

The evidence does **not** support an unconditional ordering of “pairwise best, pointwise worst.”

- Pairwise judgment is convenient for a local choice and avoids demanding globally calibrated absolute scores.
- Pointwise rubric scoring helps diagnose why a response is good or bad.
- K-way comparison can reduce shared-context cost but increases comparison complexity and sensitivity to the candidate set.
- Holistic judgment can catch interactions omitted by a checklist, but its basis is harder to audit.

GPT-4 achieved over 80% agreement with humans in the MT-Bench/Chatbot Arena study’s evaluated setting. That is useful evidence that strong LLM judges can work, not a guarantee for Sol, Greek, your rubric, or subtle correction behaviour. [Zheng et al., NeurIPS 2023, arXiv:2306.05685](https://arxiv.org/abs/2306.05685).

G-Eval and Prometheus provide evidence that task-specific rubrics and explicit evaluation criteria can make pointwise evaluation useful. They do not prove that adding more rubric fields always improves reliability. [Liu et al., *G-Eval*, arXiv:2303.16634](https://arxiv.org/abs/2303.16634); [Kim et al., *Prometheus*, arXiv:2310.08491](https://arxiv.org/abs/2310.08491).

**Recommendation:** retain the economical two-order, four-candidate protocol for the pilot, but allow partial rankings, ties, and unrankable cases. Compare its selected-pair decisions with direct order-swapped pairwise judgment on a calibration subset.

Do not require a full permutation when the evidence supports only “A and B are acceptable; C fails; A versus B is a tie.”

### What the judge should and should not judge

| Axis | Ask the judge | Do not ask it to assume |
|---|---|---|
| Task completion | What did the latest user ask, and did this response do it? | That a polished answer to an earlier request is acceptable |
| Context faithfulness | Which facts and standing instructions are relevant now? | That every user assertion is true |
| Correctness | Does the answer contradict supplied evidence or a verified solution? | That unsupported confidence establishes truth |
| Greek | Are there specific consequential errors? Is the phrasing natural in the requested register? | That one preferred edit proves the original was wrong |
| Length | Is necessary information missing or is there unnecessary material relative to the request? | That longer is more helpful or shorter is always better |
| Tone | Is the response respectful and appropriate? | That disagreement is rude or concession is polite |
| Identity/capabilities | Does it falsely claim an action, memory, tool use, or capability? | That every first-person statement is forbidden |
| Safety/refusal | Is the response appropriate to the actual request and applicable policy? | That more refusals imply greater quality |

“Invented fact” requires particular care. Fiction, explicit assumptions, and newly calculated results are not automatically hallucinations. Prefer:

> **Unsupported factual assertion presented as established, where grounding is required and the evidence supports identifying the violation.**

### Known judge biases and their mitigations

| Bias | Evidence and measurement | Appropriate mitigation |
|---|---|---|
| **Position** | Change only candidate order and measure changes in the selected preference. Position effects are documented in LLM evaluation. [Wang et al., *Large Language Models Are Not Fair Evaluators*, arXiv:2305.17926](https://arxiv.org/abs/2305.17926). | Balanced orders; agreement on the selected pair; preserve disagreements for analysis. |
| **Verbosity** | Compare preferences within length bands and on controlled content/length variants. [Zheng et al., arXiv:2306.05685](https://arxiv.org/abs/2306.05685); [Dubois et al., arXiv:2404.04475](https://arxiv.org/abs/2404.04475). | Task-conditioned length assessment and length-controlled evaluation; no blanket ratio veto. |
| **Self-preference** | Evaluators can recognize and favour their own generations in studied settings. [Panickssery et al., *LLM Evaluators Recognize and Favor Their Own Generations*, arXiv:2404.13076](https://arxiv.org/abs/2404.13076). | Hide provenance; use another vendor and native humans; include content-equivalent style contrasts. |
| **Sycophancy** | Models can alter answers to match user beliefs, and preference judgments can reward agreeable answers. [Sharma et al., *Towards Understanding Sycophancy in Language Models*, ICLR 2024, arXiv:2310.13548](https://arxiv.org/abs/2310.13548). | Supply truth where known; test both valid and invalid corrections; distinguish evidence-sensitive updating from appeasement. |
| **Style over substance** | A judge may respond to organization, confident prose, or familiar formatting while overlooking substantive errors; this is part of the evaluation-bias problem examined by Zheng et al. | Include “beautiful but wrong” controls and plain-but-correct alternatives; require substantive reasons. |
| **Social sycophancy** | ELEPHANT concerns interpersonal/social validation beyond simply changing a factual answer. [*ELEPHANT: Measuring and Understanding Social Sycophancy in LLMs*, arXiv:2505.13995](https://arxiv.org/abs/2505.13995), **[verify metadata; no numerical result asserted here]**. | Test unjustified endorsement of the user’s interpersonal framing, while allowing appropriate empathy. |
| **Instruction contamination** | Candidate text can itself contain instructions directed at the evaluator; agreement between two calls does not establish immunity. | Treat candidates as untrusted quoted content and include adversarial judge-control items. |

The literature favours **explicit measurement and multiple controls**, not reliance on a prompt saying “do not be biased.”

For the Greek correction test, withdrawing a correct answer after bare **«λάθος»** without new evidence should count against the model. Correcting an actually wrong answer after **«λάθος»** should count in its favour. A blanket anti-concession rule would train stubbornness.

### Hard constraints versus soft scores

Hard constraints are appropriate when the violation is:

- relevant to the task;
- operationally defined;
- reliably detectable;
- sufficiently serious to disqualify a candidate.

Examples include a wrong final answer under a valid exact-answer contract, an explicit prohibited output format, or a false claim to have used a tool when tool availability is known.

Soft scores are better for:

- elegance;
- mild awkwardness;
- ordinary verbosity;
- personality fit;
- disputed wording choices;
- subjective impressions of servility.

Constitutional AI supports making normative criteria explicit. It does not establish that a principle becomes a reliable veto merely because an LLM is asked to check it. [Bai et al., arXiv:2212.08073](https://arxiv.org/abs/2212.08073).

Similarly, rubric-derived rewards are useful only to the extent that the rubric and its implementation measure the desired outcome. Optimizing an imperfect proxy can increase proxy reward while reducing actual quality. [Gao et al., *Scaling Laws for Reward Model Overoptimization*, ICML 2023, arXiv:2210.10760](https://arxiv.org/abs/2210.10760).

### Combining verifiers and judgments

Use **eligibility followed by preference**, not a weighted average that lets eloquence compensate for a known wrong answer.

1. Apply relevant validated checks.
2. Establish whether each candidate meets a minimum task-quality floor.
3. Disqualify candidates with confirmed hard violations.
4. Among eligible candidates, prefer materially better task completion, state handling, and grounded content.
5. Use Greek naturalness and presentation as secondary distinctions when the substantive answers are comparable.

A passing verifier establishes only its contract. A correct numerical answer does not establish that the explanation is correct. A retained string does not establish correct use of the retained fact.

If every candidate fails the quality floor, route the prompt to recovery or log it as an unsolved case. Do not silently choose the least bad failure.

### k, best-versus-worst, margins, and all-pass prompts

**k=4 is a reasonable starting point**, not a demonstrated optimum.

Best-versus-worst pairing has advantages: an obvious contrast, one pair per prompt, and low processing overhead. Its limitations are:

- the worst response may be a trivial failure;
- extreme scores are especially exposed to judge noise;
- a huge score difference may reflect length or formatting;
- the pair can become uninformative after a small amount of training.

Use **best eligible versus a clearly worse, meaningful alternative**. Sometimes that is the worst candidate; sometimes the informative rejection is a plausible answer that mishandles a redirect.

Avoid a universal numeric margin on uncalibrated ordinal scores. Require a concrete difference such as:

> “Chosen follows the new requested format; rejected continues the previous task.”

For genuinely ambiguous differences, label a tie.

Under an illustrative independence assumption, if each sample passes a binary verifier with probability \(p\), the probability of obtaining both a pass and a fail among four samples is

\[
1-p^4-(1-p)^4.
\]

It is:

- **87.5%** at \(p=0.5\);
- **34.4%** at \(p=0.1\) or \(p=0.9\).

These are calculations, not measured yields. They show why very easy and very hard verifier prompts produce fewer contrastive pairs. Correlated candidates make this simple model less reliable.

### Human calibration: what 150 items can establish

The owner’s 150 items are valuable. They can identify systematic rubric failures and estimate aggregate agreement to roughly several percentage points. They cannot precisely validate every task family and every veto.

Measure separately:

- strict pairwise agreement;
- agreement including ties;
- tie and abstention rates;
- position reversals;
- each hard veto’s precision and recall;
- disagreement by task family;
- Greek-error severity agreement.

Use confidence intervals and report the actual denominator. Greek-error precision is measured among alleged errors, not automatically among all 150 comparisons.

For a hard veto, **80% precision is too low as a default acceptance criterion**. A reasonable operational target is at least approximately **95% observed precision**, with enough audited positive cases to support the claim. Ideally the lower confidence bound also clears an agreed threshold, such as 90%. These are proposed risk tolerances, not paper-established universal standards.

The supplied **34/235 reverted edits = 14.5%** is worth investigating, but it is not directly a Greek-error false-positive rate. Guard reversion and human error adjudication are different events.

Also, “150 items plus 30 repeated-order items in one hour” permits only **20 seconds per judgment**. That is optimistic when prefixes, Greek errors, and evidence spans must be read carefully.

### Multilingual judging

Judge original Greek. Translation into English can change:

- politeness and register;
- grammaticality;
- idiomaticity;
- ambiguity;
- instruction difficulty.

English judge instructions can remain useful, but they do not validate Greek competence. Separate:

1. task correctness;
2. discourse/state handling;
3. Greek grammatical correctness;
4. Greek naturalness/register.

A second model’s agreement is corroboration, not native-speaker ground truth.

### Multi-turn rating and prefixes

Rate the final turn against the actual prefix. Make the relevant state explicit to the evaluator without supplying an ideal answer unnecessarily.

The prefix should contain the model’s previous mistakes when the task is to recover from them. Replacing those mistakes with polished teacher responses can remove the very difficulty you are trying to train.

However, an old R0/R1 prefix is historical-policy data, not necessarily current-R3 data. Use it as a failure source, then collect fresh R3 continuations and fresh rollouts.

### Answers to the draft’s seven owner decisions

| Decision | Recommendation |
|---|---|
| 1. Two-order k-way or pairwise? | **Pilot two-order k-way with ties**, and validate selected-pair decisions against direct pairwise judgments on a subset. |
| 2. Owner calibration? | **Yes.** Prioritize correction truth, Greek-error flags, and context-state handling. Allow more than an hour if needed. |
| 3. DPO or GRPO first? | **DPO first** for the primary discourse and judgment failures. GRPO is a later, separately budgeted experiment on reliable verifier tasks. |
| 4. Rewrite-as-chosen? | **Permit a separately tracked recovery lane**, with minimal verified edits. Do not mix it invisibly into on-policy pairs. |
| 5. 1.5× length filter? | **Remove the hard filter.** Use task-conditioned length assessment and audits. |
| 6. Opus or Luna audit? | **Opus** provides the requested vendor diversity. It is still not independent ground truth. |
| 7. Budget? | **One committed iteration within 20 node-hours.** Recalculate rater quota; approve iteration two only from measured remaining capacity. |

## 5. Open questions for the owner, followed by the proposed preference definition

The unresolved owner decisions are:

1. Which violations are serious enough to disqualify an otherwise useful answer?
2. Which Greek variants and registers are acceptable?
3. Is personality consistency a secondary tie-break or an independently important objective?
4. What evidence source establishes truth for naturally occurring correction prompts?
5. Can a small portion of native review be reserved for a final assessment separate from rubric calibration?

**Proposed preference definition**

> Given the same conversation prefix and latest user request, prefer the response that more completely and correctly performs the current task, uses the relevant conversation state accurately, and handles corrections according to evidence. Require compliance with applicable, reliably verified constraints. Among substantively comparable answers, prefer appropriate Greek, proportionate length, and respectful tone.

Use the following record:

| Field | Content |
|---|---|
| `prompt_id`, `candidate_id`, hashes | Stable provenance |
| `target_turn` | Exact assistant span receiving preference and auxiliary loss |
| `applicable_checks` | Check name, version, applicability, result, evidence |
| `task_completion` | 0 = misses task; 1 = partial; 2 = substantially complete |
| `state_handling` | Correct / incorrect / uncertain, with prefix evidence |
| `grounding` | Supported / contradicted / unverifiable / not applicable |
| `correction_handling` | Evidence-sensitive update / justified resistance / false concession / unjustified resistance / not applicable |
| `greek_quality` | Consequential errors and mild issues separately; quoted spans |
| `length_fit` | Missing necessary content / appropriate / unnecessary excess |
| `tone_issue` | Specific observable issue, not an unexplained personality score |
| `hard_violation` | Type, evidence source, confidence status; only validated categories can veto |
| `preference` | A / B / tie / uncertain |
| `preference_reason` | One or two concrete, task-relevant distinctions |

**Ranking rule:** verified eligibility first; then task completion, state handling, and grounded correctness; then Greek and presentation when differences are meaningful. Keep only clear selected-pair preferences consistent across the accepted judging protocol. Keep informative all-pass pairs. Leave out mandatory total rankings, raw verbosity rewards, unsupported confidence scores, blanket anti-concession rules, and uncalibrated grammatical vetoes.

# DOC C — Synthetic preference data

## 1. Verdict

**Build a smaller, failure-focused first dataset from R3’s own responses, with explicit provenance and a separate recovery lane.** The draft’s generation strategy is broadly consistent with successful synthetic-preference work, but the “no humans” category needs correction: several influential reward models rely on human annotations upstream. The proposed 5,000–7,000 retained pairs are a hypothesis, not a measured yield, and the current selection rules could systematically remove useful chat preferences. Native Greek prompts, valid correction examples, decontaminated failure-derived tasks, and cross-vendor/native auditing matter more here than copying a large English preference corpus.

## 2. Findings ranked by severity

| Severity | Finding and evidence | Concrete fix |
|---|---|---|
| **HIGH** | **The planned distribution is not yet tied to post-R3 failures.** Draft §4.6 assigns 6,500/10,500 prompts, **61.9%**, to IF, math, and retention-checker lanes. The largest supplied failures concern redirect handling and self-observation, and those measurements precede the proposed R3 evaluation. | Reallocate after R3 evaluation. Give redirects, correction handling, recaps, and conversation state explicit quotas instead of expecting generic IF to transfer. |
| **HIGH** | **Training on failure transcripts can contaminate evaluation.** Draft §§4.1 and 4.6 draw on R0/R1 transcripts and owner-chat replays while using related dialogue measurements for promotion. | Mark reused transcripts and close derivatives as training/development. Freeze a separate final evaluation split by source dialogue and scenario/template family. |
| **HIGH** | **“LLM raters and no humans” conflates label provenance.** HelpSteer-style data and reward models are not examples of an entirely human-free chain. | Record whether each label is newly human-authored, AI-authored, or produced by a model trained on human preference/attribute labels. |
| **HIGH** | **The same-family generation/judging risk is real but unmeasured here.** Sol wrote much of the SFT data and will judge the policy’s outputs. Vendor identity alone neither proves nor removes bias. | Audit content-equivalent style contrasts, remove source metadata, use Opus on a fixed subset, and use native human adjudication for consequential disagreement. |
| **MEDIUM** | **The retained-pair forecast has no pilot evidence.** 5,000–7,000 from 10,500 prompts means **47.6–66.7% yield**. No family-level pass rates, disagreement rates, or length-filter losses are supplied. | Estimate yield and reasons for rejection from a stratified pilot. Forecast by family rather than using a single overall percentage. |
| **MEDIUM** | **The recovery policy is underspecified.** Draft §3 allows rewrites for loop failures, but does not define minimality, verification, proportion, or objective. | Store recovery data separately. Prefer minimal verified repairs; compare a small recovery-SFT lane with rewrite-positive DPO before merging them. |

## 3. What is good and should not be changed

- Sample the model’s actual response distribution.
- Use existing failure cases to identify prompt families.
- Keep evaluation prompts out of generation.
- Retain the programmatic verifier infrastructure.
- Preserve two-order checks and independent audits.
- Avoid training a Greek reward model before its cost is justified.
- Keep full candidate sets and raw judgments, even when only one pair is used.
- Separate newly generated preference data from completed SFT datasets and their historical labels.

## 4. Literature answers

### What the influential synthetic pipelines actually did

| Recipe | What it contributes | Important qualification |
|---|---|---|
| **UltraFeedback** | Roughly **64k prompts**, typically **four responses per prompt**, generated from a pool of models and scored by GPT-4 on multiple dimensions. [Cui et al., *UltraFeedback*, arXiv:2310.01377](https://arxiv.org/abs/2310.01377). | A substantial synthetic preference source, but scorer details, aggregation, and binarization matter. |
| **Zephyr** | Demonstrates effective instruction and preference distillation into a 7B model using synthetic data. [Tunstall et al., arXiv:2310.16944](https://arxiv.org/abs/2310.16944). | Dataset cleaning and preference extraction are part of the recipe, not incidental bookkeeping. |
| **Tülu 3** | Uses a broad prompt mixture and model-specific preference generation as part of a staged open pipeline. [Lambert et al., arXiv:2411.15124](https://arxiv.org/abs/2411.15124). | Exact mixture size, candidate sources, scorer, and stagewise ablations should be checked before replication. |
| **HelpSteer / HelpSteer2** | Attribute-based supervision separates helpfulness, correctness, coherence, complexity, and verbosity. HelpSteer2 uses approximately **10k response pairs** with human annotations. [Wang et al., arXiv:2311.09528](https://arxiv.org/abs/2311.09528); [Wang et al., arXiv:2406.08673](https://arxiv.org/abs/2406.08673). | These are not “no-human-label” datasets. Pair counts and response counts must not be confused. |
| **Nemotron-style reward use** | A reward model can turn attribute supervision into scalable scoring of new synthetic responses. HelpSteer2 is a relevant underlying source. [Wang et al., arXiv:2406.08673](https://arxiv.org/abs/2406.08673). | New labels may be automatic while the scorer inherits human supervision. Reward-model benchmark success is not automatically policy-training success. |
| **ArmoRM** | Uses multi-objective reward modeling and a gating mechanism to combine attribute predictions. [Wang et al., *Interpretable Preferences via Multi-Objective Reward Modeling and Mixture-of-Experts*, arXiv:2406.12845](https://arxiv.org/abs/2406.12845). | A learned attribute mixture is not an objective Greek-quality oracle. |
| **Skywork reward data/models** | Relevant releases include `Skywork/Reward-Preference-80K`. | **[verify release composition and paper metadata]**. I cannot responsibly give a paper-level provenance claim or isolated DPO gain from memory. Do not classify the release as wholly synthetic without checking it. |
| **Magpie** | Synthesizes user instructions by exploiting an aligned model’s chat formatting, reducing dependence on hand-written seed questions. [Xu et al., *Magpie*, arXiv:2406.08464](https://arxiv.org/abs/2406.08464). | It creates an instruction distribution, not verified preference truth; Greek realism and task coverage still require checking. |
| **SPIN** | Uses existing demonstrations as positives and model-generated responses as negatives in iterative self-play fine-tuning. [Chen et al., *Self-Play Fine-Tuning Converts Weak Language Models to Strong Language Models*, arXiv:2401.01335](https://arxiv.org/abs/2401.01335). | A counterexample to “both candidates must be on-policy.” It also depends on the quality of the demonstration positives. |
| **Self-rewarding LMs** | Iteratively generates and evaluates responses with the model itself; the reported setup includes several iterations at larger model scale. [Yuan et al., *Self-Rewarding Language Models*, arXiv:2401.10020](https://arxiv.org/abs/2401.10020). | Does not establish that an 8B Greek model can reliably judge its own linguistic or factual errors. |
| **West-of-N** | Selects high- and low-scoring samples to create synthetic preference contrasts, particularly for reward-model improvement. [*West-of-N*, arXiv:2401.12086](https://arxiv.org/abs/2401.12086), **[verify metadata]**. | Best/worst selection amplifies scorer errors as well as useful contrasts. |
| **RLAIF** | Finds that AI feedback can be competitive with human-feedback pipelines in evaluated tasks, and examines choices of AI labeler. [Lee et al., *RLAIF vs. RLHF*, arXiv:2309.00267](https://arxiv.org/abs/2309.00267). | Neither the strongest available model nor a same-size model is guaranteed to be the best rater for every task. Task-specific agreement matters. |

### UltraFeedback cleaning: the transferable lesson

UltraFeedback’s downstream use exposed the importance of checking scoring and binarization rather than trusting aggregate labels. The Zephyr/UltraFeedback history includes revisions to preference construction and cleaned releases; **the exact bug mechanism and affected dataset revision should be verified before citing it quantitatively**. [Cui et al., arXiv:2310.01377](https://arxiv.org/abs/2310.01377); [Tunstall et al., arXiv:2310.16944](https://arxiv.org/abs/2310.16944).

For your pipeline, make these invariants explicit:

- A selected winner must actually correspond to the intended candidate.
- Swapped-order outputs must map back to stable candidate IDs.
- Aggregated scores must match their component fields.
- A hard-veto flag must not disappear during binarization.
- Identical candidates must not become a strict preference.
- Missing/invalid judgments must not default to zero and accidentally become “worst.”
- Dataset revisions must be immutable and recorded.

These checks are more valuable than invoking “UltraFeedback-style” as a quality guarantee.

### Prompt sourcing: failures, difficulty, and coverage

Use three sources:

1. **Fresh R3 failures**, collected on development scenarios.
2. **New instances of explicit target behaviours**, with controlled truth and constraints.
3. **Naturalistic Greek requests**, including benign conversations where excessive defensiveness would be harmful.

A failure transcript is a source of a task, not permission to reuse the same scenario in the final test.

Hard prompts are useful when the model sometimes succeeds. If it never succeeds, ordinary within-policy DPO cannot supply a valid chosen response. Very easy verifier prompts likewise offer little contrast when every candidate receives the same outcome.

Do not optimize only the difficult edge cases. A correction-heavy dataset can teach the model to treat ordinary users as adversaries. Include:

- valid corrections;
- invalid corrections;
- uncertain corrections requiring checking;
- benign requests that require no correction discussion.

Prompts close to SFT data are not automatically invalid. However, near-duplicates can train memorization and overstate progress if related prompts appear in evaluation. Split and deduplicate by source, semantic scenario, and template—not merely by exact string.

### Sampling: temperature, k, and diversity

Use **T=0.8, k=4** as a provisional baseline. Keep the same decoding configuration within the main comparison.

Record:

- temperature, top-p, and any top-k;
- repetition penalties;
- maximum output length;
- stop tokens;
- seeds;
- serving/model/tokenizer revisions.

Do not change repetition penalty while measuring whether DPO fixes repetition; otherwise the causal attribution becomes ambiguous.

**Diversity means different plausible solutions or discourse choices, not just different wording.** Measure duplicate and near-duplicate rates. If all four responses are effectively identical, increasing k may buy little.

For difficult but recoverable prompts, a second batch of four samples is reasonable. Give that lane a cap and record the additional cost.

### Why current-policy responses are usually preferable—and when rewrites help

Current-policy candidates provide errors the model actually makes. They also avoid making source/style differences perfectly predictive of preference. The online/offline alignment literature supports the importance of candidate distribution and negative examples. [Tajwar et al., arXiv:2404.14367](https://arxiv.org/abs/2404.14367).

Teacher rewrites can nevertheless be valuable when the policy does not produce the desired behaviour at all. SPIN and Zephyr are evidence against categorically excluding off-policy positives. [Chen et al., arXiv:2401.01335](https://arxiv.org/abs/2401.01335); [Tunstall et al., arXiv:2310.16944](https://arxiv.org/abs/2310.16944).

The risks of rewrite-positive DPO include:

- learning the teacher’s style rather than the substantive correction;
- very different chosen/rejected support;
- attributing the preference to length or formatting;
- importing new factual mistakes;
- allowing a generator to judge its own repair.

For loop failures, prefer a **minimal repair of the model’s response** over a completely new essay. Verify the repair independently and keep its provenance visible. A small SFT recovery lane may be easier to interpret than mixing these pairs into the main DPO objective.

### Same-family SFT generation and judging

The concern is plausible:

1. Sol writes SFT responses.
2. R3 acquires some Sol-associated style.
3. Sol rewards outputs matching its preferred style.
4. The next model becomes more stylistically homogeneous, without necessarily becoming more useful.

The self-preference literature supports investigating this mechanism; it does not quantify it for Sol, Greek, or your checkpoint. [Panickssery et al., arXiv:2404.13076](https://arxiv.org/abs/2404.13076).

Mitigate it with:

- model-source blinding;
- a fixed Opus audit subset;
- native-speaker judgments;
- correctness/style conflict cases;
- content-equivalent alternatives with different presentation;
- analysis of whether judge preferences track length, headings, disclaimers, or familiar verbal habits.

A different vendor reduces one source of dependence. It does not remove shared training data, common stylistic preferences, or shared factual errors.

### Filtering and confidence

Retain a pair only when:

- the prefix is identical;
- the chosen response meets the task-quality floor;
- the hard-veto decision is supported;
- the preference is substantive and clear;
- accepted judging orders agree;
- candidate identity mapping is correct;
- neither response was truncated in a way that invalidates comparison.

Do not equate self-reported judge confidence with a calibrated probability. Use confidence as an audit-routing feature unless calibration demonstrates otherwise.

Preserve rejected and uncertain quartets. They tell you whether a failure is due to:

- model incapability;
- ambiguous rubric;
- unreliable Greek judgment;
- inconsistent order effects;
- insufficient diversity;
- unsuitable prompt construction.

### Data quantity and the observed curve

The published counts establish that useful preference training spans **tens of thousands to hundreds of thousands of pairs**, not that more is always better. UltraFeedback/Zephyr and Tülu 3 are relevant scale references, but not a controlled learning curve for Greek dialogue behaviour. [Cui et al., arXiv:2310.01377](https://arxiv.org/abs/2310.01377); [Lambert et al., arXiv:2411.15124](https://arxiv.org/abs/2411.15124).

For your project, the important curve is:

> retained **distinct, reliable contrasts** versus improvement on new conversations.

Measure it at the pilot and full first-iteration scale. Repeating easy preferences or generating all six correlated pairs from every quartet can inflate pair count without equivalent information.

### Synthetic-preference failure modes

| Failure | Detection | Prevention |
|---|---|---|
| Rubric hacking | High rubric score with poor independent task outcomes | Hold-out adversarial checks; independent evaluation |
| Length inflation | Length shifts within task families; preferences correlated with length | Task-conditioned judgment and length-controlled audits |
| Formatting bias | Headings/list structure predict preference after controlling for content | Style-controlled comparisons |
| Refusal over-generalization | Increased refusal on benign requests, including XSTest-style cases | Include benign hard prompts and audit refusal reasons |
| False anti-sycophancy | Model refuses valid corrections | Balance valid/invalid/uncertain corrections |
| Language drift | More English framing, code-switching, or translated-sounding Greek | Original Greek evaluation and language-specific monitoring |
| Teacher-style collapse | Reduced variation without better correctness or completion | Source-blind, content-controlled audits |
| Reward overoptimization | Training score rises while independent quality stalls or falls | Early stopping on held-out behaviour, not training reward |

Reward overoptimization is an established general concern; its precise onset depends on the proxy and optimization strength. [Gao et al., arXiv:2210.10760](https://arxiv.org/abs/2210.10760).

### Lower-resource language evidence

Translated preference sets are useful for coverage and can reduce annotation cost. They are weaker evidence for native pragmatics, idiom, register, and correction dynamics.

Okapi is a relevant example of multilingual instruction/RLHF work using multilingual data construction. [*Okapi: Instruction-tuned Large Language Models in Multiple Languages with Reinforcement Learning from Human Feedback*, arXiv:2307.16039](https://arxiv.org/abs/2307.16039), **[verify metadata and exact translated components]**.

Aya and Aya 23 establish the value of deliberate multilingual data and evaluation, but their final model results do not isolate the effect of native versus translated Greek preference data. [Üstün et al., arXiv:2402.07827](https://arxiv.org/abs/2402.07827); [Aryabumi et al., arXiv:2405.15032](https://arxiv.org/abs/2405.15032).

For EuroLLM, Salamandra, Meltemi, and Krikri, do not infer preference-training details merely from the existence of an instruction checkpoint. The exact Greek DPO methods and controlled native-versus-translated preference ablations remain **open in this review**.

For your target behaviours, native Greek generation should dominate. Translation is more defensible for content-preserving tasks than for politeness, social sycophancy, naturalness, or subtle conversational repair.

## 5. Open questions for the owner, followed by a concrete pipeline

The remaining questions are:

1. Which R0/R1 and owner-chat scenarios have already influenced training or prompt design?
2. Which final evaluation scenarios can remain untouched?
3. How many post-R3 failures are recoverable with k=4 or k=8?
4. Does “no humans” mean no new large-scale labels, or literally no upstream human supervision?
5. How much native review is available after calibration?
6. Should rewrite recovery be a separate SFT intervention or a small, explicitly labeled DPO component?

**Proposed first-iteration pipeline**

### Prompt allocation

Start with **6,000 distinct prompts**, subject to adjustment after the R3 baseline:

| Family | Prompts | Main evidence |
|---|---:|---|
| Redirects and correction handling | 1,500 | Typed truth/constraint checks plus judgment |
| Standing instructions and conversation-state retention | 900 | Validated checks; semantic audit |
| Recap and self-observation | 600 | Prefix-grounded answers, typed checks where possible |
| Greek verifiable IF | 900 | Checkers |
| Greek math | 600 | Answer verification; reasoning audit subset |
| Naturalistic Greek open chat and owner-style requests | 1,000 | Judgment |
| English/other EU-language preservation | 500 | Language-appropriate checks and judgment |
| **Total** | **6,000** | |

This gives explicit attention to the reported discourse failures while preserving a verifier component. It is a proposal, not a literature-derived optimum.

Use a **stratified 1,200-prompt pilot** from this training pool first. Keep the native calibration set and final evaluation outside it.

### Sampling and rating

- Generate **four R3 responses per prompt**, T=0.8.
- This produces **24,000 responses**.
- At 300 output tokens each, that is approximately **7.2 million generated tokens**, excluding prefixes and recovery samples.
- Run applicable verifiers first.
- Use two-order rubric comparison on judgment-dependent families, allowing ties.
- On the calibration subset, compare selected-pair decisions with direct order-swapped pairwise judgments.
- Audit a fixed **10% of judged prompts with Opus**, stratified by family and including both hard-veto decisions and accepted pairs.

If all 3,600 prompts in the redirect/correction, recap, open-chat, and preservation lanes receive two primary calls, that is **7,200 Sol calls**, before retries and calibration. At the supplied 18k fixed-input assumption, it entails **129.6 million fixed input tokens**. At the draft’s supplied 0.004% quota-per-call estimate, it would consume **28.8%**, not 2.88%. Actual consumption must be measured.

### Pair construction and recovery

- Keep at most one main pair per prompt.
- Keep all-pass pairs with a meaningful substantive preference.
- Drop true ties and unresolved disagreements.
- Never choose a confirmed hard failure.
- Keep Greek-error flags advisory until their precision supports veto use.
- Remove the universal 1.5× length filter.
- For all-fail prompts, permit one capped resampling round.
- If still unsolved, route to a separately tracked recovery set; do not manufacture an ordinary on-policy pair.

Forecast **roughly 3,000–4,000 main pairs** only as a planning assumption. Replace that forecast with measured family-level yield after the pilot. Record every filtering stage’s count.

### Storage and evaluation

Store all candidates, raw judgments, order mappings, verifier versions, truth provenance, token counts, generation settings, and final pair reasons.

Split by source dialogue and scenario/template lineage. Once a failure case informs training, treat it as development evidence. Use separate final conversations for promotion.

Select checkpoints on development data, then run the reserved final evaluation. Report primary dialogue results with paired, dialogue-level uncertainty and disclose which seeds received which evaluations.

### The three most informative experiments

1. **Judge-protocol calibration before training.**  
   On the same blind items, compare two-order k-way decisions with direct pairwise decisions. Measure human agreement, ties, position reversals, Greek-veto precision, and truth-versus-style conflicts. This determines whether the proposed labels deserve optimization.

2. **A small objective comparison on identical data.**  
   Compare plain DPO, DPO with the explicitly normalized α=0.1 chosen-NLL anchor, and an equal-exposure chosen-only SFT control. Keep β, LR, masks, and prompts fixed where applicable. Measure discourse gains, chosen likelihood, held-out Greek loss, and retention. This tests whether the negative preference signal helps and whether the anchor prevents a real regression.

3. **Conditional refreshed-data iteration.**  
   If iteration one helps and budget remains, compare training on newly sampled policy responses with further training on the old pairs at matched optimizer exposure. Report the extra sampling cost. This directly tests the claimed value of iteration for this model, rather than assuming two iterations are better.