# Six targeted adapted-core repair candidates

Status: proposed for full root technical and language review. No corpus row was modified, no model subprocess was called, and no candidate is approved for assembly.

## Candidate summary

| Candidate | Language | Narrow repair |
|---|---|---|
| `personas_if_37ae2fa7` | Greek | Natural Greek field wording, exactly three instrument fields, no invented feminine manager signature; P.S. and uppercase-emphasis constraint retained. |
| `393a7e8e…` | English | Adds the missing nonrestrictive-clause comma and restores `truck`; embedded news is byte-identical. |
| `20461` | Spanish | Replaces the statistically false input-variance account with separate treatment of predictor spread, noise, estimator variance, residual variance, and generalization. |
| `15571` | Spanish | Opens with the dying sailor in bed as requested and repairs the malformed hourglass phrase; every later paragraph is unchanged. |
| `49139` | Italian | Fixes agreement and supplies one consistent one-sided Welch test with correct hypotheses, statistic, degrees of freedom, threshold, and noncausal interpretation. |
| `euroblocks_fr_3c014d32` | French | Replaces 1580 with the source-supported approximately 1500-year speculative estimate and corrects its attribution and uncertainty. |

## Evidence boundary

The Spanish regression repair follows the conditional simple-regression slope variance and residual-noise relationships in [Duke's simple linear regression notes](https://www2.stat.duke.edu/courses/Fall18/sta210.001/slides/lectures/06_slr.html), together with the bias-variance and test-error treatment in [*An Introduction to Statistical Learning*](https://www.statlearning.com/s/ISLRSeventhPrinting.pdf). Predictor spread is not itself overfitting; noise, design, estimator sensitivity, and out-of-sample evaluation are distinct.

The Italian test uses the unequal-variance two-sample statistic and Welch-Satterthwaite degrees of freedom documented by the [NIST Engineering Statistics Handbook](https://www.itl.nist.gov/div898/handbook/eda/section3/eda353.htm). Direct arithmetic from the supplied summaries gives `t = 4.082482904639` and `df = 147.999879329070`; the proposed target rounds these transparently and uses an approximately 1.66 one-sided 5% threshold. The study description does not establish a causal design.

The French correction follows the [Cornell Chronicle report dated June 15, 2016](https://news.cornell.edu/stories/2016/06/relax-itll-be-1500-years-aliens-contact-us). It reports about 1,500 years under the probabilistic Solomonides-Terzian Fermi-paradox/mediocrity model and explicitly frames the horizon as likely rather than guaranteed. The target preserves the named scientists and topic while avoiding a claim that the number follows from the Drake equation alone or describes one signal's travel time.

## Review artifacts

`candidate_records.jsonl` contains every complete before and proposed message pair with source lineage and hashes. `delta_reasons.jsonl` states the permitted change for each row. `proposed_targets.jsonl` is the compact review envelope. `constraint_checks.jsonl` and `verification.json` cover hashes, exact field count, unchanged embedded content, preserved story tail, statistical arithmetic, and the factual guardrails.
