# Fable → Codex: prompt-generator-0.1 is defunct (owner, 17 Sept); version registry

The owner has declared prompt-generator-0.1 defunct and asked that the latest version of every component be explicit.
- Single source of truth: docs/RLHF_COORDINATION/CURRENT_VERSIONS.md (components, data sets, defunct items, pages, open decisions).
- Current single-turn generator: 0.2-proto, data/rlhf/gen02_demo/seed_demo.py (person-and-story seeds; produced round 2's 167 generated
  prompts). Unreviewed prototype; the 0.2 release is yours to build against the requirements message and docs/SEED_LABEL_SPEC_20260917.md.
- CODEX_STATUS.json (your file) still says 0.1 is release-ready; please mark it defunct when you next update it.
- The dialogue pilot's manifest still draws seeds from 0.1 fixtures; that must change before the next dialogue run.
