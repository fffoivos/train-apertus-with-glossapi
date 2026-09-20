# Implementation handoff — prompt generator 0.1
16 September 2026. Owner: Codex. Recipient: Fable 5.1 through the user; acknowledgement pending.

## Decision and scope
The single-turn API and reviewed development pilot are ready for integration review. Production tens-of-thousands generation, training-data promotion and dialogue rollout are NOT validated by this release.

Shared board (full path):
/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/docs/RLHF_COORDINATION/README.md

Implementation:
/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/prompt_generator

Run/API reference:
/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/rlhf/prompt_generator/README.md

Local artifact: http://127.0.0.1:8768/
Local API: http://127.0.0.1:8769/ (generation disabled by default).
These are local processes, not permanently hosted services. README gives restart commands.

## Delivered evidence
- 100-slot frozen programme; 65 accepted single-turn prompts; 35 dialogue slots deliberately deferred.
- Purpose counts: everyday25, instruction15, factual10, safety10, math5.
- Single-turn languages: Greek45, English15, French/German/Spanish/Italian/Portuguese1 each.
- Global plan: dialogue35/everyday25/IF15/factual10/safety10/math5; el70/en20/other five2 each.
- 32 of38 single-turn families in the actual sample; deterministic fixture tests cover all38.
- 36 completed Sol calls at high effort, generation and separate review, within a48-call cap. Concurrency3, batch maximum8.
- Separate all-row semantic audit; eight accepted rows reopened with archived evidence. Further automatic repair occurred where the reviewer rejected wording. All65 final rows accepted.
- 34 regression tests pass;9 final HTTP checks pass, with no extra model calls.
- Final lexical benchmark screen:65 checked,0 hits,14 named/hash-bound cache artifacts. Not a semantic decontamination guarantee.
- No CSCS or Prime Intellect job launched. No training or publication performed.
- Exact total token usage is unavailable: the first resume overwrote the original28-call usage-event file. Call receipts remain complete; subsequent resumes now append usage events. Do not estimate or report a fabricated total.

Authoritative result: runtime/runs/pilot100_v2/report.json.
Frozen source manifest: runtime/runs/pilot100_v2/manifest_final.json.
Model input: runtime/runs/pilot100_v2/model_requests.jsonl.
Private audit metadata: curator.jsonl and revision_history.jsonl alongside it.
Release file hashes: RELEASE.json.
The runtime SQLite database remains the authority for uniqueness across future runs; back it up before integration changes. Do not share runtime/api.token.

## Review dispositions
See PILOT_REVIEW.md and the independent audit. Fixed: irrelevant translation branch, formal Greek address, malformed English article, phone/message source inconsistency, Greek element wording, two unnatural harmful-request wrappers, and missing full-event conditional branch. Future fixture constructors were corrected as well as the frozen pilot rows.
There is no remaining known blocking defect for this bounded demonstration. Significant coverage limits remain below.

## Work ownership and handoff protocol
Fable owns production execution after reviewing this release, actual latest forum generation/imports, preference sampling/judging, RLHF and scheduling.
Codex owns prompt-generator development and the next bounded dialogue investigation, per the user's latest sequencing.
No Fable acknowledgement has been received. The user will pass this document and board path along. Fable should write its status in FABLE_STATUS.md and messages/, referencing the release consumed. Codex writes CODEX_STATUS.json; neither overwrites the other's status.

## What Fable can do now
1. Read README and PILOT_REVIEW; verify RELEASE.json hashes and inspect the final65 prompts in the artifact. Run the34 local tests.
2. Integrate against the source-preserving forum import contract. Use latest upstream version/hash, direct-request approval and false-premise annotation. Do not assume the old artifact's forum rows were imported here: they were not.
3. Choose production task-language/source quotas before building new plans. Natural forum records fill matching unfilled cells; do not rewrite their texture to satisfy synthetic quotas.
4. Keep one registry across batches; record config and accepted-output coverage. A failed quota/capacity check means expand the source pool or change the plan explicitly, never silently accept fewer rows or reset uniqueness.
5. Add benchmark/semantic decontamination and downstream training eligibility outside this demonstration. The supplied screen does not automatically quarantine/refill hits; all exports remain ineligible.
6. Before bulk generation, expand source diversity and calibrate a small target-model preference-yield sample. Current source breadth is not ready for10,000.

## Limits that must not disappear in a later status report
- Many notice/event sources; narrow account/privacy safety situations; chemical-element-only closed facts.
- Default40instances perstructure. 38×40=1,520 is merely an upper structure ceiling, not an attainable balanced capacity. Smaller finite families and quota/split constraints bind sooner.
- Closed facts:13elements ×3queries =39 distinct parameter instances; style and language do not add instances.
- Rare-language requests often use English source text. This tests cross-language tasks rather than native source coverage.
- Six advanced math families lack live Sol pilot coverage. No trained-model math or dialogue evaluation was performed.
- Difficulty is an assigned stratum, not an empirical measure. Attitude/task proportions are designed, not measured from the actual SFT mix.
- Exact-instance and exact-message deduplication exist; semantic uniqueness is not guaranteed.
- No independent human calibration or different-model review. Separate Sol calls may share blind spots.
- Crash recovery and automatic rejected-forum/contaminated-source replacement remain manual explicit operations.
- Existing long-form design documents describe a broader intended generator; this implementation's README and fixture source define what actually works.

## Deferred dialogue and provider budget
The user explicitly directed: finish/review/handoff API first; experiment with dialogue afterwards.
35slots remain reservations, not generated dialogue prompts. Assistant turns must be generated by the exact adapted Apertus checkpoint; no Sol-written histories.
The user authorized later Prime Intellect use with a total EUR5 ceiling. The provided credential has not been saved in any project file or used. Do not place it in the board, logs or release.
Next dialogue work must first establish exact checkpoint identity/availability, compatible inference runtime, live provider price and all billable costs, plus an automatic early shutdown with margin underEUR5. A small verified pilot, not the entire35 by default, should measure throughput and trajectory validity. No resource should be left running while waiting for review. The implemented transcript receipt checker is only a consistency check; it does not prove model provenance cryptographically.

## Release verification
From the implementation directory:
```sh
python3 -c 'import hashlib,json,pathlib; r=json.load(open("RELEASE.json")); bad=[p for p,h in r["sha256"].items() if not pathlib.Path(p).exists() or hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()!=h]; print("PASS" if not bad else bad); raise SystemExit(bool(bad))'
python3 -m unittest discover -p 'test_*.py' -v
python3 api.py report pilot100_v2
```
RELEASE.json binds the current source, docs and selected pilot evidence. Later exports change timestamped receipt hashes; retain this frozen evidence before a new run or revision.
