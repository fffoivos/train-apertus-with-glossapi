# RLHF prompt generator 0.1
Release scope: reviewed single-turn development pilot and local API. Not a training dataset or a claim of production-scale semantic coverage.

## Run
Python 3.11+ standard library for the planner/API/tests. Sol generation additionally uses the existing project data/math/codex_server.py client and an authenticated Codex installation. Benchmark screening uses data/mixlib.py and its local confirmed benchmark caches.

From this directory:
```sh
python3 api.py --state runtime serve --port 8769
python3 api.py --state runtime report pilot100_v2
python3 api.py --state runtime export pilot100_v2
python3 -m unittest discover -p 'test_*.py' -v
```
The default server is read/plan/export capable but generation-disabled. Start with --enable-generation to allow explicit POST generation. The CLI generate command is always explicit. Never expose the server outside loopback.

To plan a new run, copy pilot100.json and change programme, seed, size and quotas as needed. If size changes, remove or recalculate task_language_counts: its row and column margins must match the new plan.
```sh
python3 api.py --state runtime plan --config pilot100.json --run-id new_pilot
python3 api.py --state runtime generate new_pilot
python3 api.py --state runtime screen new_pilot
python3 api.py --state runtime export new_pilot
```
These commands reserve new instances; even with the same random seed the persistent registry excludes previously reserved instances. A fresh registry with the same config reproduces the initial plan. Retain one registry across production batches to preserve uniqueness and split isolation. Do not reset it to evade exhaustion.

## HTTP contract
Base URL http://127.0.0.1:8769. Public GET /health and /openapi.json.
All other routes require Authorization: Bearer TOKEN, read locally from runtime/api.token (0600). Do not paste it into tickets, command logs or handoffs. No browser CORS access is enabled.
All POST requests use application/json, including an empty {} for actions without arguments.

| Method/path | Body or query | Result |
|---|---|---|
| GET /v1/catalogue | none | design and exact-margin minimum size |
| POST /v1/runs | {"config":{...},"run_id":"example"} | atomic plan and reservations |
| GET /v1/runs/RUN | none | accepted/planned margins, call ledger, worker state |
| GET /v1/runs/RUN/seeds | offset=0&limit=50; maximum100 | private curator rows |
| POST /v1/runs/RUN/generate | {} | 202, poll run; requires enabled server |
| POST /v1/runs/RUN/export | {} | files under runtime/runs/RUN |
| POST /v1/runs/RUN/screen | {} | lexical benchmark receipt; does not promote data |
| POST /v1/runs/RUN/revise | {"slot_id":"S0001","issues":["concrete issue"],"reviewer":"name"}; optional fixture_replacement | archive prior accepted row and reopen same quota slot |
| POST /v1/runs/RUN/forum-import | {"records":[...]} | source-preserving import into matching unfilled cells |
| POST /v1/runs/RUN/dialogue | {"slot_id":"...","payload":{...}} | deferred integration contract; see core.py |

The seeds endpoint includes private references: it is a curator endpoint, not a model-input feed. model_requests.jsonl is the model feed.
GET run reports asynchronous failures. Invalid input returns400, unauthenticated401, disabled generation403, duplicate active launch409. Unexpected errors return500. No automatic recovery from abandoned worker claims or reserved/failed calls: inspect the ledger and process before any explicit recovery. This release has no process-crash recovery command.

## Pipeline
1. Largest-remainder apportionment fixes purpose and family counts. Language, register, attitude and designed difficulty receive independently allocated margins, subject to Greeklish being Greek-only. The pilot additionally fixes a task-language joint table so every language is represented before dialogue.
2. Per-family constructors choose relevant concrete parameters, construct complete source content and private references, and validate internal consistency. Sampling retries invalid/used/split-conflicting instances. Conditional IF alternates open/full branches.
3. SQLite atomically reserves meaningful instance hashes, source-family split membership and per-programme structure counts. Instance identity excludes language and attitude: cosmetic variants are not new tasks.
4. Sol receives batches of up to8, grouped by language, with concurrency3 and high effort. It receives task specification and frozen source, not private parameters or answers. It produces only the request wrapper. Software appends the unchanged source.
5. A separate Sol call reviews the request, source and private reference. Structural checks also enforce source immutability, labels, IDs and exact-message deduplication. Rejected rows are repaired in their original slots and reviewed again, within total call and attempt caps.
6. Export only accepted single turns or verified completed dialogue histories. Accepted openings have a separate export. All exports remain training_eligible=false.
7. Screen against version-hashed benchmark caches, inspect semantics, then make an explicit downstream dataset decision. A clean lexical screen is not proof of semantic decontamination.

Separate review uses a fresh call to the same model, not a different-model or human judge. The pilot also received a separate all-row semantic audit and root disposition.

## Natural forum imports
Required record:
```json
{
 "source_id":"stable-upstream-id",
 "source_version":"immutable-generation-version",
 "source_sha256":"SHA256 of exact UTF-8 user content",
 "messages":[{"role":"user","content":"Exact direct request"}],
 "labels":{"purpose":"everyday","language":"el","register":"standard","attitude":"cooperative","difficulty":"routine"},
 "review":{"accepted":true,"direct_request":true,"reviewer":"upstream-reviewer","premise_status":"not_applicable"}
}
```
Premise labels: supported, contradicted, unresolved, not_applicable. Import is atomic; no matching planned cell means rejection, not rewriting. Forum records receive separate review but are never regenerated to satisfy a quota. Rejected imports require an explicit new sourcing decision; this release does not automatically refill those cells. No actual latest forum generation was imported in this development pilot; Fable owns that integration.

## Outputs and receipts
- manifest_final.json: current config and all100 reserved seeds; manifest.json is the historical initial snapshot.
- model_requests.jsonl:65 accepted single user requests.
- curator.jsonl: accepted seed, private reference, generation, review and attempts.
- revision_history.jsonl: archived superseded accepted rows and review reasons.
- calls/:36 completed model-call receipts for this pilot.
- benchmark_screen.json: final lexical screen,65 rows,0 hits,14 cache identities.
- receipt.json: output JSONL hashes and config.
- report.json: current authoritative counters; worker_result.json is diagnostic.
- usage_events.json: partial token accounting. An early resume overwrote the first28 calls' usage events; exact all-run token totals are unavailable. The call ledger and call receipts are complete. Subsequent resumes now append usage events.
- RELEASE.json: frozen code/docs/output hash manifest; runtime DB and API token are intentionally not a portable release bundle.

Do not edit accepted rows in place. The revision API archives the previous accepted row; source replacements validate family/hash/split consistency. Editorial changes retain the same source-family lineage; substantive parameters get a new identity. Revision output is re-reviewed before export.

## Scale and limits
The API accepts requested sizes up to100,000, but that is an input limit, NOT a validated content capacity.
The release has38 narrow single-turn family constructors. The default structure cap is40 instances per programme. A theoretical38×40=1,520 structure ceiling is already an overestimate: fixed quota bottlenecks and finite factual records can stop a plan sooner. Closed-book facts contain13 elements ×3 query forms =39 distinct instances before split exclusions; languages/attitudes do not multiply these. Existing reservations also reduce available capacity.
No tens-of-thousands content run or throughput benchmark was performed. Expanding catalogue/source inventories and validating saturation is necessary before increasing caps.

The 100-slot plan is the minimum with exact agreed primary-purpose and language percentages; only65 are realised now. It covers32/38 single-turn families; all38 have deterministic fixture checks. Six advanced math families are not live-tested in this pilot.
Notice/event sources remain common (31/65 at initial audit). Safety domains are narrow. Rare-language requests often operate on English source text; they are cross-language tasks, not proof of native source coverage.
Task/attitude/register/difficulty proportions are design choices, not a measured SFT census. No empirical SFT alignment, semantic near-duplicate guarantee, target-model difficulty calibration, or preference-pair yield has been established.

## Dialogue boundary
35 slots are deferred. Do not fabricate assistant history. Future assistant turns must come from the exact trained Apertus checkpoint with sampling and text-hash receipts; recovery goals need actual verified errors, false-correction goals actual verified correct answers. Receipt consistency checks are implemented, not real-model rollout validation.
User sequencing: complete API review and handoff first; only then Codex experiments with dialogue. Later Prime Intellect experimentation has a total EUR5 cap, including all provider charges. No provider has been started and no user credential is stored in this package.
