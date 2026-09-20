# Correcting/dialogue specification plan: revision 2

Revision 2 preserves the original manifest and corrects the scale denominator. The requested 200 false, 200 true, 100 partial, and 100 unresolved decisions are the **600 training decisions**. Development and final confirmation each add 60 held-out decisions, so the full program contains 720 decisions across 240 isolated families.

| Split | Four-label families | True/false-only families | Decisions |
|---|---:|---:|---:|
| Train | 100 | 100 | 600 |
| Development | 10 | 10 | 60 |
| Final confirmation | 10 | 10 | 60 |
| **Total** | **120** | **120** | **720** |

The training allocation is exactly 200 true, 200 false, 100 partial, and 100 unresolved decisions. Each holdout contains 20 true, 20 false, 10 partial, and 10 unresolved decisions.

The 48-decision pilot remains balanced at 12 decisions per label and 32/8/8 across train, development, and final confirmation. `cf05_cafe_order` moves from train to development, while `cf10_reminder_cancel` moves from development to train. This keeps all counts fixed and gives the training pilot direct coverage of version editing, state inference, and cancellation. The two final-confirmation families remain sealed and unchanged.

Specifications alone are not quality-ready for scale. The active goal authorizes later scaling after the semantic, Greek, executable-oracle, mask, and family-leakage gates pass.
