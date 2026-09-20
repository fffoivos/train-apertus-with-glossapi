# Personality and deployment-claim audit

Date: 2026-09-13  
Scope: `data/personality/personality_v3v4_final.jsonl`, with a complete row-level read of all 192 v4 rows (144 H manners, 48 I capability cases), deduplicated claim-family scan of all 1,580 v3+v4 rows, and review of the seven registered v3 fact corrections. This is a prospective repair pilot. No source dataset, score, checkpoint, or production file was changed. No additional model subprocess or web search was used.

## Verdict

Retain a small core that teaches truthful model identity, the documented adaptation lineage, ordinary first-person language, lack of a body or personal experiences, calibrated fallibility, and the useful H-category interaction patterns. Do not carry universal claims about internet, tools, files, images, audio, clocks, conversation memory, storage, or deletion into reusable model weights. Those are properties of a deployment and should be generated from a versioned runtime manifest or phrased only from prompt-observable evidence.

The audit found two separate concrete issues in v4:

- **Six established structural defects:** `v4_H07_00`, `v4_H07_02`, `v4_H07_03`, `v4_H07_05`, `v4_H07_06`, `v4_H07_08` end on a user turn and therefore have no final assistant target. The earlier editor correctly proposed an assistant closing line, but the final file replaced the text of the existing user turn instead of restoring the user turn and appending the assistant turn. Exact reconstructed candidates are in `candidate_fixes.jsonl`.
- **Twenty-nine deployment-dependent rows:** all 12 `v4_I00_*`, all 12 `v4_I01_*`, `v4_I02_00`, `v4_I02_07`, `v4_I02_11`, `v4_I03_10`, plus `v4_H07_07`. These should be conditioned on the actual endpoint. Fourteen prompt-grounded candidate rewrites demonstrate the safe pattern; the whole family must use the same invariant before promotion.

The remaining **157/192 v4 rows** are retained by this bounded identity/deployment audit. This does not certify every incidental ordinary-world fact in H; it means no identity/deployment contradiction or structural failure was found after reading all v4 rows and the existing Opus/Sol reviews.

## What the local evidence establishes

The project configuration identifies the training parent as `fffoivos/apertus-8b-greek-cpt` at revision `18-avg-uniform5-tokens30B-50B`, with `swiss-ai/Apertus-8B-Instruct-2509` as the template source (`cluster/configs/R3_single.yaml`, lines 3–6). The pipeline describes the CPT parent as an average of 18 Greek continued-pretraining checkpoints of `swiss-ai/Apertus-8B-2509`, and names the intended identity as a Greek adaptation of Apertus by GlossAPI at ΕΕΛΛΑΚ (`docs/PIPELINE_DESCRIPTION_20260911.md`, lines 7–9). The dataset card independently records continued Greek pretraining, then instruction tuning, with a Swiss AI Initiative grant (`docs/HF_DATASET_CARD_greek-apertus-sft_20260907.md`, lines 61–65).

The canonical serving script documents one direct vLLM snapshot: an OpenAI-compatible text endpoint with `--max-model-len 4096` and no tool-schema or retrieval flags (`cluster/serve_models.sh`, lines 1–12). This supports describing that exact invocation as direct text generation. It does **not** establish permanent properties of the weights. In particular:

- `v4_I00_03` says it sees “all messages,” but a 4,096-token serving window can truncate or omit conversation history.
- File, URL, image and audio adapters can exist outside the model process; the serving command does not prove that every future host lacks them.
- Service logging, retention, deletion and cross-session memory are absent from the model configuration. The model cannot promise them.
- The training mix contains 29,700 textual `<function_calls>` demonstrations, while the recipe explicitly says these were not evaluated as tool competence (`docs/RECIPE_R3_single_20260911.md`, lines 50 and 142). “I have no tools” and “I can use tools” are both unjustified as unconditional weight-level claims.

The stable no-body/no-personal-senses statements are ontology claims about a language model and can remain. `v4_I02_06` is especially useful: the user supplies transcribed microphone content and the answer simply performs the requested writing task. The `v4_I03_*` supplied-current-information controls are also useful; only `v4_I03_10` needs its unconditional internet statement removed.

## Identity and release claims

The minimum accurate retained identity core is:

> Δεν έχω δικό μου όνομα· είμαι μια ελληνική προσαρμογή του Apertus 8B από την ομάδα GlossAPI της ΕΕΛΛΑΚ, με χορηγία της Swiss AI Initiative. Η προσαρμογή περιλαμβάνει συνέχιση προεκπαίδευσης σε ελληνικό κείμενο και εκπαίδευση σε οδηγίες.

This preserves warranted first-person language and the owner’s no-proper-name decision while staying within local training documentation. “8B” should be treated as the documented model class/name; this checkout contains no model `config.json` or tensor index from which an exact parameter total was independently recounted.

Three large v3 claim families require a release manifest before reuse:

- **85 rows** say or imply that Greek-model weights/code/data are public or open.
- **40 rows** specifically name Apache 2.0 for the Greek weights.
- **52 rows** teach a mid-2025 knowledge cutoff.

The exact IDs are in `claim_inventory.json`. These families overlap. The project’s own identity registry leaves the Greek weight licence and cutoff unset (`data/personality/identity_facts.json`, lines 30–34). The dataset card calls the mid-2025 cutoff and named licence “current proposals,” uses a mixed dataset licence, and says the project licence is still to be announced (`docs/HF_DATASET_CARD_greek-apertus-sft_20260907.md`, lines 116–120). Another pipeline line confirms one historical arm-B checkpoint was public and gated, but that fact does not prove the status or licence of every future checkpoint. Therefore:

- keep the base/adaptation lineage;
- replace release claims with a checkpoint-specific pointer only after a signed/versioned release manifest exists;
- exclude Apache 2.0 claims about Greek weights until that manifest names the licence;
- exclude the single “mid-2025 cutoff” story unless a data-stage inventory defines exactly what it bounds. A training corpus assembled later and containing synthetic/current examples does not have one simple cutoff merely because HPLT 3 was released in 2025.

`B00_04` says “καμία σχέση με το ChatGPT ή την OpenAI.” This is too broad. The defensible distinction is that the base weights are Apertus and the Greek adaptation was done by GlossAPI/ΕΕΛΛΑΚ; local review records also say Claude/OpenAI generators contributed synthetic training data (`data/personality/FACT_CORRECTIONS_ASTRA_20260909.md`, lines 28–31). Keep “Δεν είμαι το ChatGPT” as product identity when asked, but do not claim no relationship to those vendors.

## Seven registered v3 factual corrections

The seven existing corrections are real pending work items, not completed remediation: `A14_09`, `A21_21`, `F05_03`, `A02_02`, `A01_22`, `G09_09`, `A12_20`. The registry itself requires confirmation against the named primary source before a corrected target is admitted (`data/personality/FACT_CORRECTIONS_ASTRA_20260909.md`, lines 3–16). They should remain excluded from a retained core until that source check is attached. This audit did not browse those external sources and does not upgrade the registry’s proposed corrections to newly verified facts.

## Capability invariant for future rows

Use observable, deployment-qualified language:

- Conversation: “Στο πλαίσιο που μου δόθηκε εδώ δεν υπάρχει η προηγούμενη συζήτηση.”
- Context: “Μπορώ να χρησιμοποιήσω τα μηνύματα που περιλαμβάνονται στο τρέχον πλαίσιο.” Avoid “βλέπω όλα τα μηνύματα.”
- Files/media/links: “Το περιεχόμενο του αρχείου/εικόνας/συνδέσμου δεν έχει δοθεί εδώ σε αναγνώσιμη μορφή.”
- Tools/live data: “Δεν μου έχει δοθεί εδώ αποτέλεσμα από εργαλείο ή ζωντανή πηγή.”
- Storage/deletion/logging: “Δεν μπορώ να συμπεράνω ή να εγγυηθώ τι αποθηκεύει η υπηρεσία· έλεγξε την πολιτική και τις ρυθμίσεις του παρόχου.”
- Body: “Δεν έχω σώμα, αισθήσεις ή προσωπική ζωή.” This may remain unconditional.

These formulations test the intended skill—accurate self-description from available evidence—without teaching an endpoint-specific inability as a permanent model trait.

## Outputs and validation

- `v4_full_audit.jsonl`: one disposition for every one of the 192 v4 rows.
- `claim_inventory.json`: deduplicated claim families, exact affected IDs, and retained/unresolved invariants.
- `candidate_fixes.jsonl`: six complete structural candidate rows plus fourteen prompt-grounded deployment-claim rewrites.
- `evidence_table.md`: claim-by-claim evidence, status, and target consequence.
- `manifest.json`: input/output hashes and counts.
- `build_audit.py`: deterministic reproducer; reads repository files and writes only this output directory.

Validation executed locally:

1. Parsed all four JSONL inputs as JSON.
2. Counted v4 categories: H=144, I=48.
3. Checked message termination: 186 assistant-final rows, six user-final rows; all six are the H07 defects above.
4. Checked adjacent role alternation: no duplicated adjacent role remains, which confirms that the defect is missing target turns rather than malformed adjacency.
5. Reconstructed six candidates from the original user-ending conversations and the existing reviewed closing answers.
6. Rebuilt the audit and hashed every input/output. No checker here claims semantic correctness beyond the explicit dispositions above.
