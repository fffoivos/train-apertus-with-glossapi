"""rlhf.prompts -- where prompts come from, and the proof that each one came from somewhere.

    from rlhf.prompts import PromptBank
    bank = PromptBank("data/rlhf/bank/bank.sqlite")

    bank.add_source("forum", url, forum="lexilogia", purpose="factual", language="el", payload=row, origin="forum-gate-v3")
    bank.plan("round4", 500, shares={"purpose": {...}, "language": {...}}, caps={"forum": {"astrovox": 4}})

    src = bank.claim("round4", "forum", worker="me")          # an UNUSED source whose cell still has room, or None
    pid = bank.submit(src["source_id"], messages, plan_id="round4", run="R4-main", generator="forum-gate-v3")
    bank.supersede(pid, better_messages, run="R4-fix", generator="forum-gate-v3")   # a retry, atomically

    bank.coverage("round4")     # target / filled / claimed / remaining, per quota
    bank.lineage(pid)           # the prompt, its source verbatim, every earlier attempt on that source
    bank.audit()                # every invariant, counted; all zeros or something bypassed the schema

submit() raises SourceError, DuplicateError, NearDuplicateError or QuotaError. It never degrades quietly.
"""
from .bank import (PromptBank, BankError, SourceError, QuotaError, DuplicateError, NearDuplicateError,
                   content_sha, shingle_set, source_id_for, apportion, KINDS, DIMENSIONS, NEAR_DUPLICATE_JACCARD)
from .flows import ingest_forum_gate, ingest_seeds, fill, forum_prompt
