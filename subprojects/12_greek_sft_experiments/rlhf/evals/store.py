"""The results store. One record per (run, benchmark, protocol, population) -- never one scalar per
benchmark. R-DPO7b2: "replacing that scalar only for the seven full-scored arms would mix
16,632-item scores with 250-item scores inside the same means". Here that cannot be expressed:
a group statistic is refused unless every member shares one measurement identity.
"""
import hashlib, json, os
from .result import Result, _BUILDER
from .compare import _check, ComparabilityError
from . import stats

REQUIRED = ("label", "weights_id", "benchmark", "protocol", "metric", "n_items", "item_digest")

class Store(object):
    def __init__(self, root):
        self.root = root
        os.makedirs(os.path.join(root, "items"), exist_ok=True)

    def _key(self, m):
        ident = json.dumps([m.get(k) for k in ("label", "benchmark", "protocol", "population", "item_digest", "prompt_digest",
                                               "gen_config", "geometry", "weights_id", "runtime")], sort_keys=True, default=str)
        return hashlib.sha256(ident.encode()).hexdigest()[:20]

    def put(self, result):
        if not isinstance(result, Result):
            raise TypeError("the store takes sealed Results only")
        result.verify(); manifest, items = result.manifest, result.items
        missing = [k for k in REQUIRED if manifest.get(k) is None]
        if missing:
            raise ValueError("refusing a result without an identity; missing: %s" % ", ".join(missing))
        key = self._key(manifest)
        rec = {"key": key, "seal": result.seal, "manifest": manifest, "accuracy": sum(items.values()) / float(len(items))}
        for path, obj in ((os.path.join(self.root, "items", key + ".json"), items),
                          (os.path.join(self.root, key + ".json"), rec)):
            with open(path + ".tmp", "w") as fh:
                json.dump(obj, fh, sort_keys=True)
            os.replace(path + ".tmp", path)
        return key

    def records(self, **where):
        out = []
        for f in sorted(os.listdir(self.root)):
            if not f.endswith(".json"):
                continue
            with open(os.path.join(self.root, f)) as fh:
                r = json.load(fh)
            if all(r["manifest"].get(k) == v for k, v in where.items()):
                out.append(r)
        return out

    def one(self, **where):
        rs = self.records(**where)
        if len(rs) != 1:
            raise LookupError("%d results match %r; a lookup must be unambiguous" % (len(rs), where))
        # the seal is re-verified: a record edited on disk does not come back as a Result
        return Result(rs[0]["manifest"], self.items(rs[0]["key"]), _token=_BUILDER, _expect_seal=rs[0]["seal"])

    def items(self, key):
        with open(os.path.join(self.root, "items", key + ".json")) as fh:
            return json.load(fh)

    def group(self, labels, policy="weights", **where):
        """Mean and between-run SD over `labels` -- refused unless all members are one measurement."""
        rs = [self.one(label=l, **where) for l in labels]
        for r in rs[1:]:
            _check(rs[0].manifest, r.manifest, policy)
        accs = [sum(r.items.values()) / float(len(r.items)) for r in rs]; m0 = rs[0].manifest
        return {"n_runs": len(accs), "mean": sum(accs) / len(accs), "seed_sd_pp": stats.seed_sd_pp(accs),
                "scores": dict(zip(labels, accs)), "benchmark": m0["benchmark"],
                "protocol": m0["protocol"], "n_items": m0["n_items"]}
