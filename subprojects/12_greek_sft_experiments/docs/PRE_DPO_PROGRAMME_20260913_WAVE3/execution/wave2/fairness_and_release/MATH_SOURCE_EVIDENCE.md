# Maths source and licence evidence

Checked 13 September 2026. This supplements the frozen pilot manifest; it does not change dispatched payloads.

The MATH authors explicitly identify the data and code as MIT-licensed in the paper's “Author Statement and License”. The paper separately explains their reliance on research/fair-use grounds for underlying competition problems. Record both the stated dataset licence and that underlying-source qualification; do not present the repository's software licence alone as a newly verified grant from every original problem author. [Original paper, Appendix B](https://arxiv.org/pdf/2103.03874), [author repository licence](https://github.com/hendrycks/math/blob/main/LICENSE).

The 32-problem pilot uses the existing 7,500-row MATH training cache, bound by SHA-256 in its manifest. Its fresh 16 problems are not imported NVIDIA solutions. Their Greek adaptations and independent solutions therefore retain separate authorship and generation receipts. The original cache download revision remains a distinct provenance field to resolve before release.

NVIDIA's OpenMathInstruct-2 card declares CC-BY-4.0, distinguishes original MATH/GSM8K training problems from augmented problems, and distinguishes reference answers from majority-vote answers. Preserve that distinction when selecting the proposed English competition block. Its collection licence should not overwrite source-specific provenance. [NVIDIA dataset card](https://huggingface.co/datasets/nvidia/OpenMathInstruct-2).
