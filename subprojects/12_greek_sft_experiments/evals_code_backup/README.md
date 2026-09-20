# Archived copy of the Greek eval task code

This is the **scorer** for `ifeval_greek` and `mgsm_greek` — the two generated-lane benchmarks every
DPO01 number is measured on. It is archived here because on 2026-09-20 it partially vanished from
scratch *in the middle of a scoring job* (poison ledger E8), and nothing in the repo held a copy.

Taken from `clariden:/iopsstor/scratch/cscs/fffoivos/sft_round1/evals_code/ilsp` after the
restoration described below. 136 KB.

## Why some modules are `.pyc` with no `.py`

That is how this environment ships them, and it is not a corruption: lm_eval's own bundled `ifeval`
task directory is sourceless in exactly the same way (`instructions.pyc`, `instructions_registry.pyc`,
`instructions_util.pyc`, `utils.pyc`, no `.py`). Python imports these as sourceless modules.

`ifeval_greek/{__init__,instructions,instructions_registry}.pyc` at the top level were **restored by
copying the matching `__pycache__/*.cpython-312.pyc`** after the `.py` sources disappeared. That is
exactness-preserving rather than a reconstruction: during the wave that succeeded, CPython was
executing precisely those cached bytecode files, so the restored scorer is the same code object that
produced every earlier result — not a re-derivation that might differ.

Empirically checked, not merely argued: the retry job re-scored an already-scored model
(`armNM44VERIFY_ep3`, same weights as `armNM44_ep3`) under the restored scorer. Those two rows must
agree exactly; if they ever do not, the restoration changed the instrument and every number scored
after it is suspect.

## Caveat

`instructions.pyc` and `instructions_registry.pyc` are bytecode. They are byte-identical to what ran
before, but they are **not human-auditable**. If the Greek IFEval instruction set ever needs to be
read or changed, the sources have to be recovered upstream from ILSP rather than from here.
