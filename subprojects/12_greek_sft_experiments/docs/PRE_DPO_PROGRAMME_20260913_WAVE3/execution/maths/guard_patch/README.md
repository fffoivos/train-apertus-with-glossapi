# Maths pipeline guard patch

This directory contains a review-only patch and isolated tests. It does not modify project sources, repair historical data, or run a model.

The patch adds four narrow protections:

1. It rejects decoded output strings containing C0 controls other than tab, newline, and carriage return, or DEL. The exception reports the recursive value path and character index. It does not strip or reinterpret output.
2. It raises when the `codex exec` subprocess exits nonzero before attempting to load its output.
3. It rejects one input ID bound to different records before any worker dispatch. Structurally identical duplicate records are collapsed in first-seen order and counted. Worker configuration remains supported from the argument or `WORKERS`, with an explicit range of 1–100.
4. Newly generated Level 5 problem and solution rows record SHA256 bindings for the canonical UTF-8 input object and exact assembled prompt, plus model and effort. Resumed historical rows remain untouched and receive no invented provenance.

Apply from the experiment root with:

```sh
patch -p1 < /absolute/path/to/math_pipeline_guards.patch
```

Run the isolated tests from this directory with:

```sh
python3 -m unittest discover -s tests -v
```

The staged tree is an executable copy of the three patched source files used by the tests. It exists only to test the proposal without changing the project.

## Root application update — 13 September 2026

The reviewed code repair has now been applied to the project and verified against the tested candidate. See `../applied_repairs.json` (at the execution root) for file hashes and limitations. Historical corpora and scores were not recomputed. Earlier statements above describe the proposal-stage audit.
