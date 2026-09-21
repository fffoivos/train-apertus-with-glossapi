"""Seed slots: the SOURCE of a seeded or dialogue prompt, built for the cells a plan still needs.

A seed is the COMBINATION of all its elements -- purpose x subtype x language x difficulty/attitude/register/detail x
person/situation/topic -- and generate.py turns one seed into one prompt. Registering the seed as a bank source BEFORE
any model call is what ties the eventual prompt to where it came from, and the bank refuses the same combination twice.
That is the whole uniqueness rule. Elements are reused freely: the space is ~52 billion seeds for Greek alone.

Elements are drawn least-used-first purely for SPREAD, so a round does not lean on a handful of personas when it need
not. It is a preference, never a refusal. Deterministic for a given (seed, bank state). The pools live in the bank
(`ingredients`); ingest_axes() loads the pool files and is idempotent, so extending a pool is: edit the file, re-run.
"""
import collections, json, pathlib, random
from .bank import apportion, SlotError

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

LANGUAGES = ("el", "en", "fr", "de", "es", "it", "pt")

def ingest_axes(bank, languages=LANGUAGES):
    """Load generator_v02/axes/*.json into the bank's ingredient pool. Idempotent. Returns {pool: newly added}."""
    out = {"person:" + l: bank.add_ingredients("person", _load("axes/people_%s.json" % l)["items"], language=l, origin="axes/people_%s.json" % l) for l in languages}
    out["situation"] = bank.add_ingredients("situation", _load("axes/situations.json")["items"], origin="axes/situations.json")
    out["topic"] = bank.add_ingredients("topic", _load("axes/topics.json")["items"], origin="axes/topics.json")
    return out

def label_combinations(target):
    d = target["within_seeded_defaults_percent"]; return len(d["difficulty"]) * len(d["attitude"]) * len(d["register"]) * len(DETAIL)

def seed_space(bank, target):
    kinds = _load("task_kinds.json"); n = sum(len([1 for d in v.values() if isinstance(d, dict)]) for v in kinds.values() if isinstance(v, dict))
    ingest_axes(bank); return bank.seed_space(n, label_combinations(target))

def backfill(bank):
    """Give every slot-shaped source that predates the `slots` table its row."""
    ingest_axes(bank); n = 0
    from .bank import ingredient_id_for
    rows = bank.db.execute("SELECT source_id, payload, language FROM sources s WHERE kind IN ('seed','dialogue','template') "
                           "AND NOT EXISTS(SELECT 1 FROM slots x WHERE x.source_id=s.source_id)").fetchall()
    for sid, payload, lang in rows:
        p = json.loads(payload); sl = p.get("slot") or p
        if not all(sl.get(a) for a in ("person", "situation", "topic")): continue
        for axis in ("person", "situation", "topic"): bank.add_ingredients(axis, [sl[axis]], origin="legacy-slot", language=sl.get("language") or lang)
        with bank._tx() as db:
            db.execute("INSERT OR IGNORE INTO slots VALUES (?,?,?,?,?,?)", (sid, sl.get("language") or lang, sl.get("subtype") or "?",
                       ingredient_id_for("person", sl["person"]), ingredient_id_for("situation", sl["situation"]), ingredient_id_for("topic", sl["topic"]))); n += 1
    return n

def build(bank, needs, *, prefix, seed, target):
    """needs: [(kind, purpose, language), ...] with kind in {'seed','dialogue'}; purpose is the BANK purpose
    ('dialogue' for dialogue openings). Returns the new source ids, one per need, in order."""
    ingest_axes(bank)
    rng = random.Random(seed); kinds = {p: {s: d for s, d in v.items() if isinstance(d, dict)} for p, v in _load("task_kinds.json").items() if isinstance(v, dict)}
    defaults = target["within_seeded_defaults_percent"]
    # usage comes from the bank in one join per axis; `bump` tracks what THIS call has issued so far
    usage = {("person", l): {r["value"]: r["used"] for r in bank.ingredient_usage("person", l)} for l in {l for _, _, l in needs}}
    usage[("situation", None)] = {r["value"]: r["used"] for r in bank.ingredient_usage("situation")}
    usage[("topic", None)] = {r["value"]: r["used"] for r in bank.ingredient_usage("topic")}
    def draw(axis, lang=None, skip=()):
        pool = {v: n for v, n in usage[(axis, lang)].items() if v not in skip}
        if not pool: raise ValueError("the %s pool%s has nothing left to offer here: extend generator_v02/axes" % (axis, " for %s" % lang if lang else ""))
        least = min(pool.values()); return rng.choice(sorted(v for v, n in pool.items() if n == least))     # least-used first; ties by the seeded rng
    def weighted(w): return rng.choices(list(w), weights=list(w.values()))[0]
    per_purpose = collections.Counter(p for k, p, _ in needs if k == "seed"); queue = {}
    for p, n in per_purpose.items():                       # subtypes evenly within a purpose, as generator_v02/manifest.py does
        q = [s for s, c in apportion(n, {s: 1 for s in kinds[p]}).items() for _ in range(c)]; rng.shuffle(q); queue[p] = q
    out = []
    for i, (kind, purpose, language) in enumerate(needs):
        if kind == "dialogue": under, subtype = weighted(DIALOGUE_OPENS_ON)
        elif kind == "seed": under, subtype = purpose, queue[purpose].pop()
        else: raise ValueError("slots are for seed and dialogue sources, not %r" % kind)
        for _ in range(200):
            s_ = dict(purpose=under, language=language, subtype=subtype, packet=kinds[under][subtype]["packet"],
                     difficulty=weighted(defaults["difficulty"]), attitude=weighted(defaults["attitude"]),
                     register=weighted(defaults["register"]), detail=weighted(DETAIL))
            if _compatible(s_): break
        else: raise ValueError("no compatible label combination for %s/%s/%s" % (under, subtype, language))
        if kind == "dialogue": s_.update(opens_a_dialogue=True)
        s_.update(slot_id="%s-%s%02d" % (prefix, "D" if kind == "dialogue" else "S", i + 1))
        for _ in range(50):
            pick = {"person": draw("person", language), "situation": draw("situation"), "topic": draw("topic")}
            try: sid = bank.add_slot(kind, dict(s_, **pick), purpose=purpose, language=language, origin="slots.build seed=%s" % seed, must_be_new=True)
            except SlotError: continue                      # this exact combination exists already (vanishingly rare): draw again
            usage[("person", language)][pick["person"]] += 1; usage[("situation", None)][pick["situation"]] += 1; usage[("topic", None)][pick["topic"]] += 1
            out.append(sid); break
        else: raise ValueError("could not draw a seed that does not already exist for %s/%s" % (language, subtype))
    return out
