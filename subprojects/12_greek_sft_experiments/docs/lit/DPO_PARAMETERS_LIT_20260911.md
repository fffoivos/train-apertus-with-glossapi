_Provenance: literature review written by the cross-vendor reviewer (gpt-6-astra, xhigh, 2026-09-11, one call for the three documents, no web access: written from the model's knowledge; brief docs/reviews/briefs/astra_dpo_literature.md; raw output docs/lit/ASTRA_DPO_LITERATURE_raw_20260911.md). Citations marked [verify] by the reviewer and the key numbers were checked by Claude on 2026-09-11; see the VERIFICATION section at the end. Owner discussion doc: docs/RLHF_PLAN_20260911.md._

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

## VERIFICATION (Claude, 2026-09-11 18:05)

Every arXiv identifier in the three documents (44 distinct) was resolved to its title on arxiv.org (docs/lit/citation_check_20260911.json). 41 resolve to the paper the reviewer names. Three identifiers were wrong and are corrected in place: West-of-N is arXiv:2401.12086 (the reviewer wrote 2402.05392, an astronomy paper); Meltemi is arXiv:2407.20743 (not 2407.20773); the Salamandra technical report is arXiv:2502.08489 (not 2502.08486). Not yet verified: the Tülu 3 preference-pair count the reviewer marked [verify], and the exact experimental scope of the "preference models prefer sycophantic answers 95% of the time" figure from Sharma et al. 2023, which the reviewer challenged in DOC B; both stay marked. Numbers quoted from papers (β ranges, pair counts, benchmark deltas) were NOT independently checked against the papers' text; treat them as the reviewer's reading until the owner discussion picks the ones we will rely on.
