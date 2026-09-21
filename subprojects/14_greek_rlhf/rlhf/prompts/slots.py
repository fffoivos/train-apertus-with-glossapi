"""Seed slots: the SOURCE of a seeded or dialogue prompt, built for the cells a plan still needs.

A slot is generator 0.2's unit -- purpose x subtype x language x difficulty/attitude/register/detail x
person/situation/topic -- and generate.py turns one slot into one prompt. Registering the slot as a bank
source BEFORE any model call is what ties the eventual prompt to where it came from.

Deterministic for a given (seed, bank state). person/situation/topic are drawn LEAST-USED FIRST against every
slot the bank already holds, legacy ones included, and the same (person, situation, topic) triple is never
issued twice. Strict no-reuse was the first design and is impossible: on 2026-09-21 all 172 Greek and all 70
English personas, and 127 of 130 situations, had already been used, and the legacy manifests were themselves
reusing personas (49 more than once, one six times). exhaustion() reports this so it is a known supply limit
rather than a silent one; the fix is to extend generator_v02/axes, not to look away.
"""
import collections, json, pathlib, random
from .bank import apportion

RL = pathlib.Path(__file__).resolve().parents[2] / "data" / "rlhf"
GEN = RL / "generator_v02"
DETAIL = {"bare": 30, "terse": 20, "short": 20, "medium": 20, "detailed": 5, "rambling": 5}      # generator_v02/manifest.py, round-2 profile
NO_BARE = {"multi_constraint_composition"}
# What a dialogue opens on. collection60's allocation, as weights: correction/revision, troubleshooting, learning.
DIALOGUE_OPENS_ON = {("everyday", "write_or_rewrite_message"): 4, ("everyday", "rewrite_supplied_draft"): 4, ("everyday", "plan_or_organise"): 4,
                     ("everyday", "summarise_supplied_text"): 3, ("instruction", "edit_preserving_values"): 4, ("instruction", "multi_constraint_composition"): 4,
                     ("instruction", "strict_format"): 3, ("factual", "grounded_in_supplied_text"): 4, ("everyday", "troubleshoot"): 15,
                     ("everyday", "explain_simply"): 8, ("math", "explanation_and_learning"): 7}

def _load(name): return json.load(open(GEN / name))

def _compatible(s):
    return not ((s["register"] == "greeklish" and s["language"] != "el") or (s["packet"] and s["detail"] == "short")
                or (s["detail"] == "bare" and s["subtype"] in NO_BARE))

def _used(bank):
    """({axis: Counter of value -> times used}, {triples already issued})"""
    used = collections.defaultdict(collections.Counter); triples = set()
    for (payload,) in bank.db.execute("SELECT payload FROM sources WHERE kind IN ('seed','dialogue','template')"):
        p = json.loads(payload); slot = p.get("slot") or p
        for axis in ("person", "situation", "topic"):
            if slot.get(axis): used[axis][slot[axis]] += 1
        triples.add((slot.get("person"), slot.get("situation"), slot.get("topic")))
        triples.add(("scene", slot.get("language"), slot.get("subtype"), slot.get("situation")))
    return used, triples

def exhaustion(bank, languages=("el", "en", "fr", "de", "es", "it", "pt")):
    """Per axis: pool size, how many values are still unused, and the heaviest reuse so far."""
    used, _ = _used(bank); out = {}
    pools = dict({"person:" + l: (_load("axes/people_%s.json" % l)["items"], "person") for l in languages},
                 situation=(_load("axes/situations.json")["items"], "situation"), topic=(_load("axes/topics.json")["items"], "topic"))
    for name, (pool, axis) in pools.items():
        out[name] = {"pool": len(pool), "unused": sum(1 for x in pool if not used[axis][x]), "max_times_one_value_used": max([used[axis][x] for x in pool] or [0])}
    return out

def build(bank, needs, *, prefix, seed, target):
    """needs: [(kind, purpose, language), ...] with kind in {'seed','dialogue'}; purpose is the BANK purpose
    ('dialogue' for dialogue openings). Returns the new source ids, one per need, in order."""
    rng = random.Random(seed); kinds = {p: {s: d for s, d in v.items() if isinstance(d, dict)} for p, v in _load("task_kinds.json").items() if isinstance(v, dict)}
    defaults = target["within_seeded_defaults_percent"]; used, triples = _used(bank)
    axes = {"situation": _load("axes/situations.json")["items"], "topic": _load("axes/topics.json")["items"]}
    people = {}
    def draw(axis, pool):
        least = min(used[axis][x] for x in pool)                   # least-used first; ties broken by the seeded rng
        x = rng.choice([x for x in pool if used[axis][x] == least]); used[axis][x] += 1; return x
    def weighted(w): return rng.choices(list(w), weights=list(w.values()))[0]
    # subtypes evenly within a purpose (largest remainder), as generator_v02/manifest.py does
    per_purpose = collections.Counter(p for k, p, _ in needs if k == "seed"); queue = {}
    for p, n in per_purpose.items():
        q = [s for s, c in apportion(n, {s: 1 for s in kinds[p]}).items() for _ in range(c)]; rng.shuffle(q); queue[p] = q
    out = []
    for i, (kind, purpose, language) in enumerate(needs):
        if kind == "dialogue": under, subtype = weighted(DIALOGUE_OPENS_ON)
        elif kind == "seed": under, subtype = purpose, queue[purpose].pop()
        else: raise ValueError("slots are for seed and dialogue sources, not %r" % kind)
        people.setdefault(language, _load("axes/people_%s.json" % language)["items"])
        for _ in range(200):
            s = dict(purpose=under, language=language, subtype=subtype, packet=kinds[under][subtype]["packet"],
                     difficulty=weighted(defaults["difficulty"]), attitude=weighted(defaults["attitude"]),
                     register=weighted(defaults["register"]), detail=weighted(DETAIL))
            if _compatible(s): break
        else: raise ValueError("no compatible label combination for %s/%s/%s" % (under, subtype, language))
        # CP2 M1: E1 and E2 each got "an online application keeps rejecting a correctly formatted address" for the same
        # language and subtype, and rendered near-paraphrases with a word-5-gram Jaccard of 0.000. The topic axis cannot
        # carry uniqueness -- the generator is licensed to drop it, and did in 11 of 20 -- so the SCENE must be unique too.
        for _ in range(200):
            trip = (draw("person", people[language]), draw("situation", axes["situation"]), draw("topic", axes["topic"]))
            scene = ("scene", language, subtype, trip[1])
            if trip not in triples and scene not in triples: break
            for axis, v in zip(("person", "situation", "topic"), trip): used[axis][v] -= 1      # not issued: give the draw back
        else: raise ValueError("could not find an unissued person/situation/topic triple with a fresh scene")
        triples.add(trip); triples.add(scene)
        s.update(slot_id="%s-%s%02d" % (prefix, "D" if kind == "dialogue" else "S", i + 1), person=trip[0], situation=trip[1], topic=trip[2])
        if kind == "dialogue": s.update(opens_a_dialogue=True)
        # CP1 M5: slot_id is a run-scoped LABEL. With it inside the key, the same seed under a new experiment prefix was a
        # new source, which is exactly the duplicate the bank exists to refuse. Identity is the seed's content.
        identity = {k: v for k, v in s.items() if k != "slot_id"}
        out.append(bank.add_source(kind, json.dumps(identity, ensure_ascii=False, sort_keys=True), purpose=purpose, language=language,
                                   payload=s, origin="slots.build seed=%s" % seed))
    return out
