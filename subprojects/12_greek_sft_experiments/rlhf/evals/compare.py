"""Comparisons declare their variable from a CLOSED list. Everything else must be identical.

R-DPO8 finding 1 (BLOCKER): the first version took `varying=` and `allow_unknown=` from the caller, so
`varying=IDENTITY_KEYS` switched the guard off entirely. There is no such parameter now. A comparison
names one POLICY; what may be unknown is declared by the manifest's builder for its protocol, checked
against a closed table, and always reported back as unverified.
"""
from . import stats
from .manifest import IDENTITY_KEYS, UNRECORDABLE_BY_PROTOCOL
from .result import Result

from types import MappingProxyType
# Read-only (R-DPO9 B2: the exported dict could be widened at run time to make any key "the variable").
POLICIES = MappingProxyType({
    "weights":    ("weights_id",),   # same measurement, different model: the training effect
    "gen_config": ("gen_config",),   # same model, different generation config: the serving effect
    "geometry":   ("geometry",),     # same weights, different effective rotary geometry: the loader artefact
})

class ComparabilityError(Exception):
    def __init__(self, message, diffs):
        Exception.__init__(self, message); self.diffs = diffs

def differences(a, b):
    return {k: (a.get(k), b.get(k)) for k in IDENTITY_KEYS if a.get(k) != b.get(k)}

def _explain(a, b, key):
    if key == "prompt_digest" and a.get("prompt_digest_dateless") and \
       a.get("prompt_digest_dateless") == b.get("prompt_digest_dateless"):
        return ("the requests differ ONLY in the 'Current date:' line (%s vs %s) -- the two runs were "
                "rendered on different days and the date is part of the prompt"
                % (",".join(a.get("prompt_dates") or ["?"]), ",".join(b.get("prompt_dates") or ["?"])))
    if key == "prompt_digest":
        return "the requests differ (prompt text, continuations or per-request generation options)"
    if key == "gen_config":
        return "generation config differs: %r vs %r" % (a.get(key), b.get(key))
    if key == "item_digest":
        return "different items or gold answers (%s vs %s items)" % (a.get("n_items"), b.get("n_items"))
    if key == "protocol":
        return "different scoring protocols: %r vs %r" % (a.get(key), b.get(key))
    if key == "geometry":
        return ("EFFECTIVE MODEL GEOMETRY differs (rotary table %s vs %s): one side was loaded with different "
                "RoPE settings, so this is not a weights-only comparison"
                % ((a.get(key) or {}).get("inv_freq_sha256", "?")[:12], (b.get(key) or {}).get("inv_freq_sha256", "?")[:12]))
    if key == "runtime":
        ra, rb = a.get(key) or {}, b.get(key) or {}
        return "runtime differs in: %s" % ", ".join(sorted(k for k in set(ra) | set(rb) if ra.get(k) != rb.get(k)))
    return "%s differs: %r vs %r" % (key, a.get(key), b.get(key))

def _unrecordable(m):
    declared = tuple(m.get("unrecordable") or ())
    allowed = UNRECORDABLE_BY_PROTOCOL.get(m.get("protocol"), ())
    extra = [k for k in declared if k not in allowed]
    if extra:
        raise ComparabilityError("%s declares %s unrecordable, which protocol %r does not permit"
                                 % (m.get("label"), extra, m.get("protocol")), {})
    return set(declared)

def _check(a, b, policy="weights"):
    """Raise unless `a` and `b` differ in exactly the policy's variable and nothing else."""
    if policy not in POLICIES:
        raise ValueError("unknown comparison policy %r; choose one of %s" % (policy, sorted(POLICIES)))
    varying = set(POLICIES[policy])
    for m in (a, b):
        if m.get("provenance_class") == "caller-asserted":
            raise ComparabilityError("%s: identity was asserted by a caller, not recorded by the evaluator (legacy "
                                     "custom-protocol run); it can be reported but never compared" % m.get("label"), {})
    may_be_unknown = _unrecordable(a) & _unrecordable(b)
    problems, unverified = [], []
    for k in IDENTITY_KEYS:
        va, vb = a.get(k), b.get(k)
        if k in varying:
            if va is None or vb is None:
                problems.append("%s, the variable under test, is unrecorded" % k)
            elif va == vb:
                problems.append("%s is IDENTICAL on both sides -- this is the same %s compared with itself"
                                % (k, "model" if k == "weights_id" else k))
            continue
        if va is None or vb is None:
            if k in may_be_unknown and va is None and vb is None:
                unverified.append(k)
            else:
                problems.append("%s is unrecorded for %s -- unknown is not equal" % (k, a["label"] if va is None else b["label"]))
        elif va != vb:
            problems.append(_explain(a, b, k))
    if problems:
        raise ComparabilityError("%s vs %s is not a controlled comparison (policy: %s):\n  - %s"
                                 % (a["label"], b["label"], policy, "\n  - ".join(problems)), differences(a, b))
    return {"policy": policy, "varying": sorted(varying), "unverified": sorted(unverified)}

def _results(*rs):
    for r in rs:
        if not isinstance(r, Result):
            raise TypeError("compare() takes sealed rlhf.evals Results, not %s -- a manifest dict and an item map "
                            "passed separately can be edited or swapped" % type(r).__name__)
        r.verify()

def compare(a, b, policy="weights"):
    """The only sanctioned way to turn two results into a delta."""
    _results(a, b)
    ma, mb = a.manifest, b.manifest
    ctl = _check(ma, mb, policy)
    out = stats.paired(a.items, b.items)
    out.update({"a": ma["label"], "b": mb["label"], "benchmark": ma["benchmark"], "protocol": ma["protocol"],
                "population": ma.get("population"), "control": ctl, "seals": [a.seal, b.seal]})
    return out

def comparable(a, b, policy="weights"):
    """True/raises, for sealed Results only. (The manifest-level check is private on purpose.)"""
    _results(a, b); _check(a.manifest, b.manifest, policy); return True
