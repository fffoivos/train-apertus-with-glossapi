#!/usr/bin/env python3
"""Did rebuilding the scoring environment change the instrument? (poison ledger E9)

On 20 Sept a scratch cleanup gutted the scoring environment mid-job and it was reinstalled from the
surviving version pins. Twelve of those pins were ambiguous (duplicate .dist-info from layered
installs, resolved at newest; nltk and regex among them). So the rebuilt environment CANNOT be
asserted identical to the one that produced the 19 Sept baseline and wave 1.

It can be measured. `armNM44VERIFY_ep3` re-scores, under the REBUILT environment, exactly the weights
already scored as `armNM44_ep3` under the OLD one. Same weights, same tokenizer, same frozen date,
same geometry. Anything that differs is the instrument.

This compares them at the ITEM level, not on the summary accuracy: two runs can agree on a mean while
disagreeing on which items they got right, and that would still mean the instrument moved.

  verify_instrument.py <frozen_dir> [--a armNM44_ep3] [--b armNM44VERIFY_ep3]

Exit 0 only if every lane matches item-for-item.
"""
import glob, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from rlhf.evals import from_lm_eval

LANES = [("ifeval_greek", "prompt_level_strict_acc"), ("mgsm_greek", "exact_match")]

def rundir(root, label):
    ds = sorted(d for d in glob.glob(os.path.join(root, label + "__*cfg")) if os.path.isdir(d))
    if len(ds) != 1: raise SystemExit("expected one run dir for %s, found %d" % (label, len(ds)))
    return ds[0]

def main():
    root = sys.argv[1]
    a_lab = sys.argv[sys.argv.index("--a") + 1] if "--a" in sys.argv else "armNM44_ep3"
    b_lab = sys.argv[sys.argv.index("--b") + 1] if "--b" in sys.argv else "armNM44VERIFY_ep3"
    A, B = rundir(root, a_lab), rundir(root, b_lab)
    print("A (old environment): %s" % os.path.basename(A))
    print("B (rebuilt)        : %s\n" % os.path.basename(B))
    bad = 0
    for task, metric in LANES:
        ra, rb = from_lm_eval(A, task, metric), from_lm_eval(B, task, metric)
        ka, kb = set(ra.items), set(rb.items)
        if ka != kb:
            print("  %-16s ITEM SETS DIFFER: %d only in A, %d only in B" % (task, len(ka - kb), len(kb - ka))); bad += 1; continue
        diff = sorted(k for k in ka if ra.items[k] != rb.items[k])
        aa = sum(ra.items.values()) / len(ra.items); ab = sum(rb.items.values()) / len(rb.items)
        if diff:
            print("  %-16s %d of %d items DISAGREE   acc %.4f vs %.4f (%+.2f pp)"
                  % (task, len(diff), len(ka), aa, ab, (ab - aa) * 100))
            print("      first few: %s" % ", ".join(str(k) for k in diff[:8])); bad += 1
        else:
            print("  %-16s identical on all %d items   acc %.4f" % (task, len(ka), aa))
    # Global-MMLU leaves
    leaves = sorted(os.path.basename(f).split("samples_")[1].rsplit("_", 1)[0]
                    for f in glob.glob(os.path.join(A, "**", "samples_global_mmlu_*.jsonl"), recursive=True))
    gbad = gtot = 0
    for t in leaves:
        try:
            ra, rb = from_lm_eval(A, t, "acc"), from_lm_eval(B, t, "acc")
        except Exception as e:
            print("  global_mmlu leaf %s: %s" % (t, e)); gbad += 1; continue
        gtot += len(ra.items)
        if set(ra.items) != set(rb.items) or any(ra.items[k] != rb.items[k] for k in ra.items): gbad += 1
    print("  %-16s %d leaves, %d items, %d leaves disagree" % ("global_mmlu", len(leaves), gtot, gbad))
    bad += gbad

    print()
    if bad == 0:
        print("INSTRUMENT UNCHANGED: the rebuilt environment reproduces the old one item-for-item.")
        print("Every cross-day comparison in this round stands.")
        return 0
    print("INSTRUMENT CHANGED in %d lane(s). Cross-environment comparisons are NOT valid." % bad)
    print("Do not reconcile this by averaging or by widening a tolerance. Re-score the 19 Sept")
    print("baseline in the rebuilt environment and compare within it.")
    return 1

sys.exit(main())
