"""The one statistics implementation. Paired by default, and the three uncertainties kept apart.

  between-seed SD      how much the score moves if you retrain with another seed
  same-seed repeat gap ONE contrast between two identical runs; a number, not a distribution
  item sampling SE     how much the score would move on a fresh draw of items

They answer different questions and must never be substituted for one another (R-DPO6, R-DPO7a).
"""
import math, random
from fractions import Fraction

def _comb(n, k):
    try:
        return math.comb(n, k)
    except AttributeError:                      # python < 3.8 on the cluster login node
        k = min(k, n - k); c = 1
        for i in range(1, k + 1):
            c = c * (n - k + i) // i
        return c

def mcnemar_exact(gained, lost):
    """Two-sided exact binomial test over discordant pairs at q = 0.5. Certified against R's
    binom.test in R-DPO7a: 9/3 -> 0.1460, 10/5 -> 0.3018, 9/5 -> 0.4240."""
    n = gained + lost
    if n == 0:
        return 1.0
    tail = sum(_comb(n, i) for i in range(0, min(gained, lost) + 1))
    # exact rational: at full-benchmark scale (n > 1000) both terms overflow a float
    return min(1.0, float(Fraction(2 * tail, 2 ** n)))

def paired(items_a, items_b):
    """b against a on exactly the same items. `items_*` map item id -> bool.
    Refuses differing populations: a paired test over a partial overlap is a different test."""
    if not items_a or not items_b:
        raise ValueError("paired(): empty item set")
    if set(items_a) != set(items_b):
        raise ValueError("paired(): item populations differ (%d vs %d ids, %d shared)"
                         % (len(items_a), len(items_b), len(set(items_a) & set(items_b))))
    for name, it in (("a", items_a), ("b", items_b)):
        bad = [k for k, v in it.items() if not isinstance(v, bool)]
        if bad:
            raise ValueError("paired(): %s has %d non-boolean outcomes, e.g. %r" % (name, len(bad), it[bad[0]]))
    g = sum(1 for k in items_a if not items_a[k] and items_b[k])
    l = sum(1 for k in items_a if items_a[k] and not items_b[k])
    n = len(items_a)
    return {"n": n, "acc_a": sum(items_a.values()) / float(n), "acc_b": sum(items_b.values()) / float(n),
            "gained": g, "lost": l, "net": g - l, "delta_pp": 100.0 * (g - l) / n,
            "p_mcnemar": mcnemar_exact(g, l), "moving": g + l}

def item_se_pp(acc, n):
    """Binomial SE of ONE score on n items, in percentage points. Not valid for a paired contrast."""
    return 100.0 * math.sqrt(acc * (1.0 - acc) / n)

def seed_sd_pp(scores):
    if len(scores) < 2:
        return None
    m = sum(scores) / len(scores)
    return 100.0 * math.sqrt(sum((x - m) ** 2 for x in scores) / (len(scores) - 1))

def _check_boot(B, level, *groups):
    if not (isinstance(B, int) and B >= 100): raise ValueError("B must be an integer >= 100")
    if not 0.5 < level < 1.0: raise ValueError("level must be in (0.5, 1)")
    for g in groups:
        if len(g) < 2: raise ValueError("bootstrap needs at least 2 runs per group, got %d" % len(g))
        if any((not isinstance(x, (int, float))) or x != x for x in g): raise ValueError("non-finite score")

def seed_bootstrap(scores_a, scores_b, B=10000, seed=20260919, level=0.95):
    """UNPAIRED: difference of means b - a, resampling whole runs independently within each arm.
    Use only when runs in the two arms are NOT matched. For matched seeds use paired_seed_bootstrap."""
    _check_boot(B, level, scores_a, scores_b)
    rng = random.Random(seed)
    ds = []
    for _ in range(B):
        ra = [rng.choice(scores_a) for _ in scores_a]; rb = [rng.choice(scores_b) for _ in scores_b]
        ds.append(sum(rb) / len(rb) - sum(ra) / len(ra))
    ds.sort(); lo = (1.0 - level) / 2.0
    return {"delta_pp": 100.0 * (sum(scores_b) / len(scores_b) - sum(scores_a) / len(scores_a)),
            "ci_pp": [100.0 * ds[int(lo * B)], 100.0 * ds[int((1.0 - lo) * B)]],
            "unit": "training run", "design": "unpaired", "B": B, "level": level,
            "n_a": len(scores_a), "n_b": len(scores_b)}

def paired_seed_bootstrap(scores_a, scores_b, B=10000, seed=20260919, level=0.95):
    """PAIRED: scores_a[i] and scores_b[i] share a seed (and whatever else varies with it, such as
    the day they were trained and scored). Resamples the per-seed DIFFERENCES. R-DPO8 finding 6: the
    alpha interval was described as seed-paired while computed with the unpaired bootstrap."""
    if len(scores_a) != len(scores_b): raise ValueError("paired bootstrap needs equally many runs per arm")
    _check_boot(B, level, scores_a, scores_b)
    d = [y - x for x, y in zip(scores_a, scores_b)]
    rng = random.Random(seed); ds = []
    for _ in range(B):
        r = [rng.choice(d) for _ in d]; ds.append(sum(r) / len(r))
    ds.sort(); lo = (1.0 - level) / 2.0
    return {"delta_pp": 100.0 * sum(d) / len(d), "ci_pp": [100.0 * ds[int(lo * B)], 100.0 * ds[int((1.0 - lo) * B)]],
            "diffs_pp": [100.0 * x for x in d], "unit": "seed-matched pair of training runs",
            "design": "paired", "B": B, "level": level, "n_pairs": len(d)}

def holm(pvalues):
    """Holm step-down adjusted p-values, returned in the input order."""
    if not pvalues: raise ValueError("holm(): no p-values")
    if any((not isinstance(x, (int, float))) or x != x or x < 0.0 or x > 1.0 for x in pvalues):
        raise ValueError("holm(): p-values must be finite and in [0, 1]")
    order = sorted(range(len(pvalues)), key=lambda i: pvalues[i]); m = len(pvalues)
    adj = [0.0] * m; run = 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (m - rank) * pvalues[i])); adj[i] = run
    return adj
