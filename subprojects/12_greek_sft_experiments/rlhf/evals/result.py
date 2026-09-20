"""One validated result: a manifest and the item outcomes it describes, sealed together.

R-DPO8b finding 1 (BLOCKER): with a mutable manifest dict and a separately passed item map, a caller
could edit an identity field after building, pair a genuine manifest with fabricated outcomes, or
hand-build a manifest and declare its own unknowns. A Result can only be made by this package's
builders (or re-loaded by the Store, which re-verifies the seal); it exposes read-only copies; and
compare() accepts nothing else. Editing library source or reaching for the private token is out of
scope -- that is no longer using the API.
"""
import copy, hashlib, json

_BUILDER = object()          # private capability: only rlhf.evals builders and the Store hold it

def _seal(manifest, items):
    blob = json.dumps([manifest, sorted(items.items())], sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()

class Result(object):
    __slots__ = ("_m", "_items", "_sealed")
    def __init__(self, manifest, items, _token=None, _expect_seal=None):
        if _token is not _BUILDER:
            raise TypeError("a Result is produced by an rlhf.evals builder (from_lm_eval, from_native_mcq, "
                            "from_official_greekmmlu) or loaded from a Store; it cannot be constructed by hand")
        if not items or not all(isinstance(v, bool) for v in items.values()):
            raise ValueError("outcomes must be a non-empty map of item id -> bool")
        if manifest.get("n_items") != len(items):
            raise ValueError("manifest says %r items, %d outcomes supplied" % (manifest.get("n_items"), len(items)))
        object.__setattr__(self, "_m", copy.deepcopy(dict(manifest)))
        object.__setattr__(self, "_items", dict(items))
        object.__setattr__(self, "_sealed", _seal(self._m, self._items))
        if _expect_seal is not None and _expect_seal != self._sealed:
            raise ValueError("stored result failed its seal: the record was altered after it was written")
    def __setattr__(self, *a): raise AttributeError("a Result is immutable")
    @property
    def manifest(self): return copy.deepcopy(self._m)      # a copy: editing it changes nothing
    @property
    def items(self): return dict(self._items)
    @property
    def seal(self): return self._sealed
    @property
    def label(self): return self._m.get("label")
    def verify(self):
        if _seal(self._m, self._items) != self._sealed:
            raise ValueError("%s: result no longer matches its seal" % self.label)
        return self
    def subset(self, keep_ids, population):
        """The same run restricted to a pinned item subset (held-out, clean): a NEW sealed result whose
        population and item digest say so, so it can never be compared with the full frame."""
        keep = set(keep_ids); it = {k: v for k, v in self._items.items() if k in keep}
        if len(it) != len(keep): raise ValueError("%s: %d of %d subset ids absent" % (self.label, len(keep) - len(it), len(keep)))
        m = copy.deepcopy(self._m); m["n_items"] = len(it); m["population"] = population
        m["item_digest"] = hashlib.sha256(("%s|%s|%s" % (self._m.get("item_digest"), population, ",".join(sorted(it)))).encode()).hexdigest()[:16]
        return Result(m, it, _token=_BUILDER)
