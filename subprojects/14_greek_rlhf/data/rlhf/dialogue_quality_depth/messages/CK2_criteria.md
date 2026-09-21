# Checkpoint CK2 acceptance — forecast and admission after smoke
Spec: plan §3 (admission), §5 (forecast from measured rates, separate candidate/annotation reserve), §11 (EUR 5 cap, EUR 4 operational
stop, 120-call Sol cap, reallocation only in the recorded forecast), and messages/CK2_brief.md.
Blocking: (1) GPU rate basis = sessions with ≥1 observed completion; zero-completion sessions still deducted as spend; basis and
exclusions recorded in forecast.json; conservative margin stated; Sol-wave idle time modelled explicitly. (2) Reallocation of Sol
reservations recorded in forecast.json, honoured by budget.py, never exceeding 120 including calls already made; annotation of the full
admitted horizon funded before anything else. (3) Admission = largest predeclared size fundable on both ledgers; if none, the
smoke-only status stays. (4) No silent cap increase anywhere; no change to sampling settings, prompts, or barriers. (5) Tests exist and
pass for both defects; nothing outside this directory modified.
