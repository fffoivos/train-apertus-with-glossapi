#!/usr/bin/env python3
"""Do topic and person MATTER? A 3 situations x 3 topics factorial, rendered by two generators.

Everything else is held fixed (el / everyday / plan_or_organise / compositional / cooperative / standard / medium), each cell
gets its own person. Arm A is generate.py as it stands; arm B is variants/generate_roles.py. If the topic matters, prompts
that share a TOPIC should be more alike than prompts that share nothing, and prompts that share only a SITUATION should stop
looking alike. Similarity is TF-IDF cosine over accent-folded words, with IDF from the 151 legacy Greek seeded prompts, the
same measure used on the legacy data.

  python3 data/rlhf/bank/factorial_experiment.py --id F1 [--fake]        # 18 seeds, about 25-35 Sol medium calls, single-turn only
"""
import argparse, collections, itertools, json, math, pathlib, random, re, shutil, statistics as st, sys, unicodedata
HERE = pathlib.Path(__file__).resolve().parent; RL = HERE.parent; ROOT = RL.parents[1]; sys.path.insert(0, str(ROOT))
from rlhf.prompts import PromptBank
from rlhf.prompts import slots as slotlib, seeded

def fold(t): return "".join(c for c in unicodedata.normalize("NFD", t.lower()) if not unicodedata.combining(c))
def words(msgs): return re.findall(r"\w{3,}", fold(" ".join(m["content"] for m in msgs if m["role"] == "user")))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--id", required=True); ap.add_argument("--fake", action="store_true"); ap.add_argument("--seed", type=int, default=20260922)
    a = ap.parse_args(); out = HERE / "experiments" / a.id
    if out.exists(): raise SystemExit("%s exists" % out)
    out.mkdir(parents=True); rng = random.Random(a.seed)
    ref = PromptBank(HERE / "bank.sqlite"); slotlib.ingest_axes(ref)
    corpus = [words(json.loads(m)) for (m,) in ref.db.execute("SELECT messages FROM prompts WHERE kind='seed' AND status='active' AND language='el'")]
    sits = rng.sample([r["value"] for r in ref.ingredient_usage("situation")], 3); tops = rng.sample([r["value"] for r in ref.ingredient_usage("topic")], 3)
    people = rng.sample([r["value"] for r in ref.ingredient_usage("person", "el")], 9); ref.db.close()
    grid = [(i, j, sits[i], tops[j], people[3 * i + j]) for i in range(3) for j in range(3)]
    N = len(corpus); df = collections.Counter(w for d in corpus for w in set(d)); idf = lambda w: math.log((N + 1) / (df[w] + 1)) + 1
    def vec(ws):
        v = {w: (1 + math.log(n)) * idf(w) for w, n in collections.Counter(ws).items()}; z = math.sqrt(sum(x * x for x in v.values())) or 1; return {w: x / z for w, x in v.items()}
    cos = lambda p, q: sum(x * q.get(w, 0) for w, x in p.items())
    report = {"situations": sits, "topics": tops, "fixed": "el / everyday / plan_or_organise / compositional / cooperative / standard / medium", "arms": {}}
    md = ["# %s — do topic and person matter? 3 situations × 3 topics, two generators\n" % a.id, "Situations: " + " · ".join("**S%d** %s" % (i + 1, s) for i, s in enumerate(sits)),
          "\nTopics: " + " · ".join("**T%d** %s" % (j + 1, t) for j, t in enumerate(tops)) + "\n"]
    for arm, script in (("A_stock", None), ("B_roles", HERE / "variants" / "generate_roles.py")):
        d = out / arm; d.mkdir(); shutil.copy(HERE / "bank.sqlite", d / "bank.sqlite"); bank = PromptBank(d / "bank.sqlite"); cell = {}
        for i, j, sit, top, per in grid:
            s = dict(purpose="everyday", language="el", subtype="plan_or_organise", packet=False, difficulty="compositional", attitude="cooperative", register="standard",
                     detail="medium", slot_id="%s%s-S%d%d" % (a.id, arm[0], i + 1, j + 1), person=per, situation=sit, topic=top)
            cell[bank.add_slot("seed", s, purpose="everyday", language="el", origin="factorial %s" % a.id, must_be_new=True)] = (i, j)
        bank.plan(arm, 9, shares={"language": {"el": 1}})
        # only the 9 grid seeds may be drawn: every other available seed source is parked for the duration of this arm
        bank.db.execute("UPDATE sources SET state='retired', state_reason='parked for the factorial' WHERE kind='seed' AND state='available' AND source_id NOT IN (%s)" % ",".join("?" * len(cell)), list(cell))
        r = seeded.generate_into(bank, arm, "seed", 9, run="%s-%s" % (a.id, arm), workdir=d / "gen", fake=a.fake, max_rounds=3, generator_script=script,
                                 legacy_registry=RL / "dialogue_v2" / "collection60" / "registry.sqlite", prior_runs=[RL / "dialogue_v2" / "collection60" / "runs", RL / "generator_v02" / "runs"])
        got = {cell[sid]: json.loads(m) for sid, m in bank.db.execute("SELECT source_id, messages FROM prompts WHERE plan_id=? AND status='active'", (arm,))}
        V = {k: vec(words(m)) for k, m in got.items()}; groups = collections.defaultdict(list)
        for p, q in itertools.combinations(sorted(V), 2):
            groups["same situation" if p[0] == q[0] else "same topic" if p[1] == q[1] else "share nothing"].append(cos(V[p], V[q]))
        base = st.mean(groups["share nothing"]) if groups.get("share nothing") else None
        res = {g: {"pairs": len(v), "mean": round(st.mean(v), 4), "x_nothing": round(st.mean(v) / base, 2) if base else None} for g, v in groups.items() if v}
        report["arms"][arm] = {"registered": len(got), "generator": {k: r[k] for k in ("slots_issued_to_generator", "generator_held", "generator_hold_rate", "sol_calls", "skipped")}, "similarity": res}
        md += ["\n## Arm %s — %d of 9 rendered · generator held %s of %s\n" % (arm, len(got), r["generator_held"], r["slots_issued_to_generator"]), "| pairs that share | n | mean similarity | × share-nothing |", "|---|---|---|---|"]
        md += ["| %s | %d | %.4f | %s |" % (g, res[g]["pairs"], res[g]["mean"], res[g]["x_nothing"]) for g in ("same situation", "same topic", "share nothing") if g in res]
        for (i, j), m in sorted(got.items()): md += ["\n**S%d × T%d**\n\n> %s" % (i + 1, j + 1, m[0]["content"].replace("\n", "\n> "))]
        bank.db.close()
    json.dump(report, open(out / "report.json", "w"), ensure_ascii=False, indent=1); (out / "PROMPTS.md").write_text("\n".join(md) + "\n")
    for arm, v in report["arms"].items(): print(arm, "rendered", v["registered"], "|", {g: (x["mean"], x["x_nothing"]) for g, x in v["similarity"].items()}, "|", v["generator"]["sol_calls"])
    print("->", out)
main()
