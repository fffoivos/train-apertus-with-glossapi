# CK5 acceptance — escalating resampling
Spec: plan §30 (docs/RLHF_PLAN_20260916.md) and messages/CK5_brief.md. Blocking: (1) prefix byte-identity and sha256 equal to the
existing convention; frozen report and existing selections untouched; (2) sampling settings frozen, n=1, every completion stored with
sha256, resumable; (3) escalating batches of four judged in sampling order, stop at first reinforce, samples_needed recorded, cap 32;
(4) 4-candidate judge prompt = rubric v2.4 verbatim + randomized letters + hidden provenance; (5) export rule = first reinforce chosen,
lowest-ranked rejected, clear margin, `origin: resample`, `samples_needed`; no_reinforce_at_32 recorded; (6) Sol cap extension recorded
in forecast.json and enforced additively; (7) tests as listed pass; nothing outside the directory modified; pod runner supports
`resample` with the same trap/watchdog.
