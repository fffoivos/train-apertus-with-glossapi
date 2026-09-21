"""The guard against (a) the comparisons that actually went wrong on 19 September 2026, on the real
run outputs, and (b) every way R-DPO8 (two cycles) found to defeat earlier versions of it."""
import glob, json, os, re, shutil, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
import rlhf.evals
from rlhf.evals import (from_lm_eval, from_official_greekmmlu, compare, comparable,
                        ComparabilityError, Result, Store, load_receipt, stats)

LOCAL = os.path.join(ROOT, "results/G4F6P1--DPO01/full_local")
RAW, CFG, WDIR = os.path.join(LOCAL, "raw"), os.path.join(LOCAL, "model_configs.jsonl"), os.path.join(LOCAL, "weights")
ITEMS250 = os.path.join(ROOT, "results/G4F6P1--DPO01/greekmmlu_items")
OFFICIAL = os.path.join(ROOT, "..", "12_greek_sft_experiments", "results", "greekmmlu_official")   # the GreekMMLU-official instrument and its results are shared infrastructure and stayed in the SFT subproject
TOK = "acf4d5c6"   # tokenizer.json sha, byte-identical across the parent and all 68 checkpoints (R-DPO7b2)
R = "/iopsstor/scratch/cscs/fffoivos/sft_round1"
WEIGHTS_OF = {"parent": R + "/eval_copies/R4_full_ep1", "parent_ckptcfg": R + "/eval_copies/R4_full_ep1_ckptcfg",
              "arm05_ep3": R + "/runs/G4F6P1--DPO01--05/checkpoint-129", "arm01_ep3": R + "/runs/G4F6P1--DPO01--01/checkpoint-129",
              "arm05s44_ep3": R + "/runs/G4F6P1--DPO01--05s44/checkpoint-129", "arm01s44_ep3": R + "/runs/G4F6P1--DPO01--01s44/checkpoint-129"}
WEIGHTS_OF["arm05_ep3_parentcfg"] = WEIGHTS_OF["arm05_ep3"]; WEIGHTS_OF["arm01_ep3_parentcfg"] = WEIGHTS_OF["arm01_ep3"]
HAVE = os.path.exists(CFG) and os.path.isdir(WDIR)
need = unittest.skipUnless(HAVE, "real run outputs not present")

def receipt_for(label):
    for f in glob.glob(os.path.join(WDIR, "*.json")):
        with open(f) as fh: r = json.load(fh)
        if r.get("requested_dir") == WEIGHTS_OF[label]: return r
    raise unittest.SkipTest("no weights receipt for " + label)

# Rotary tables as resolved INSIDE the lm_eval environment (transformers 4.57), verified on the cluster 19 Sept:
# the parent builds 4ae228093081..., every DPO checkpoint as-is builds 082aa1f8a9e9... (E6). Padded to 64 hex.
GEO_PARENT, GEO_MISLOADED = "4ae228093081".ljust(64, "0"), "082aa1f8a9e9".ljust(64, "0")
# Effective generation settings, verified identical on the cluster for the parent, the parent_ckptcfg stage
# and the arms (digest 857c25f224c3) once lm_eval's overrides are applied: it forces use_cache and the
# tokenizer's pad id, and [2,68] / [68,2,68] stop on the same tokens. This is what run_receipt.py records.
GEN_EFFECTIVE = {"eos_token_ids": [2, 68], "bos_token_id": 1, "pad_token_id": 3, "pad_token_id_source": "tokenizer (lm_eval override)",
                 "do_sample": False, "num_beams": 1, "repetition_penalty": 1.0, "temperature": None, "top_p": None,
                 "use_cache": True, "use_cache_source": "lm_eval HFLM._model_generate forces it"}

def _sha(path):
    import hashlib
    with open(path, "rb") as fh: return hashlib.sha256(fh.read()).hexdigest()

def mint_receipt(run_dir, label, **over):
    """Historic runs predate run receipts. For the tests we write one from facts verified on the cluster
    (real weights receipt, real generation config, the rotary table that environment really built).
    Production receipts are written by cluster/eval_jobs/run_receipt.py inside the scoring job."""
    w = receipt_for(label)
    outs = sorted(glob.glob(os.path.join(run_dir, "**", "results_*.json"), recursive=True) + glob.glob(os.path.join(run_dir, "**", "samples_*.jsonl"), recursive=True))
    r = {"schema": "rlhf-run-receipt-v1", "label": label, "config_mode": "historic", "frozen_date": None,
         "weights_id": w["weights_id"], "weights_files": w["files"], "gen_config": dict(GEN_EFFECTIVE),
         "geometry": {"inv_freq_sha256": GEO_PARENT if label.startswith("parent") else GEO_MISLOADED, "max_position_embeddings": 4096,
                      "hidden_size": 4096, "num_hidden_layers": 32, "num_attention_heads": 32},
         "tokenizer_sha256": TOK.ljust(64, "0"), "outputs": {os.path.relpath(o, run_dir): _sha(o) for o in outs}}
    r.update(over)
    with open(os.path.join(run_dir, "run_receipt.json"), "w") as fh: json.dump(r, fh)

_CACHE = {}
def staged(label):
    if label not in _CACHE:
        tmp = tempfile.mkdtemp(); dst = os.path.join(tmp, label); shutil.copytree(os.path.join(RAW, label), dst); mint_receipt(dst, label); _CACHE[label] = dst
    return _CACHE[label]

def load(label, task="ifeval_greek", metric="prompt_level_strict_acc", run_dir=None):
    return from_lm_eval(run_dir or staged(label), task, metric)

def mutated_copy(case, label, samples=None, results=None, receipt=None):
    tmp = tempfile.mkdtemp(); case.addCleanup(shutil.rmtree, tmp)
    dst = os.path.join(tmp, label); shutil.copytree(os.path.join(RAW, label), dst)
    if samples:
        f = glob.glob(os.path.join(dst, "**", "samples_ifeval_greek_*.jsonl"), recursive=True)[0]
        with open(f) as fh: rows = [json.loads(l) for l in fh if l.strip()]
        samples(rows)
        with open(f, "w") as fh: fh.write("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    if results:
        f = glob.glob(os.path.join(dst, "**", "results_*.json"), recursive=True)[0]
        with open(f) as fh: d = json.load(fh)
        results(d)
        with open(f, "w") as fh: json.dump(d, fh)
    mint_receipt(dst, label, **(receipt or {}))          # an honest evaluator re-receipts what it actually produced
    return load(label, run_dir=dst)

@need
class RealFailures(unittest.TestCase):
    def test_date_confound(self):
        with self.assertRaises(ComparabilityError) as cm: compare(load("parent"), load("arm05_ep3_parentcfg"))
        self.assertIn("ONLY in the 'Current date:' line (2026-09-18 vs 2026-09-19)", str(cm.exception))
    def test_the_18_september_comparison_is_refused_for_geometry_not_generation_config(self):
        """The original published contrast. It was blamed on generation config; the effective generation
        settings are in fact identical (E2 withdrawn) and the real difference is the mis-loaded arm (E6)."""
        with self.assertRaises(ComparabilityError) as cm: compare(load("parent"), load("arm05_ep3"))
        msg = str(cm.exception)
        self.assertIn("EFFECTIVE MODEL GEOMETRY differs", msg)
        self.assertNotIn("generation config differs", msg); self.assertNotIn("Current date", msg)
    def test_E6_the_comparison_we_believed_was_controlled_is_refused(self):
        """parent_ckptcfg vs a 19-Sept arm: same date, same generation config, same prompts -- and this
        guard's own first test suite accepted it. The arm was loaded with the wrong rotary settings."""
        with self.assertRaises(ComparabilityError) as cm: compare(load("parent_ckptcfg"), load("arm05s44_ep3"))
        self.assertIn("EFFECTIVE MODEL GEOMETRY differs", str(cm.exception)); self.assertNotIn("Current date", str(cm.exception))
    def test_a_controlled_comparison_passes(self):
        """Two arms, same day, same generation config, same (mis-loaded) geometry: weights are the only difference."""
        r = compare(load("arm01s44_ep3"), load("arm05s44_ep3")); self.assertEqual((r["n"], r["control"]["unverified"]), (541, []))
        r = compare(load("arm01s44_ep3", "mgsm_greek", "exact_match"), load("arm05s44_ep3", "mgsm_greek", "exact_match"))
        self.assertEqual(r["n"], 250); self.assertTrue(comparable(load("arm01s44_ep3"), load("arm05s44_ep3")))
    def test_the_loader_artefact_has_its_own_policy(self):
        """Same weights, same everything, different effective geometry: measurable, but only under its own name."""
        tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmp); dst = os.path.join(tmp, "x"); shutil.copytree(os.path.join(RAW, "parent_ckptcfg"), dst)
        mint_receipt(dst, "parent_ckptcfg", geometry={"inv_freq_sha256": GEO_MISLOADED, "max_position_embeddings": 4096, "hidden_size": 4096, "num_hidden_layers": 32, "num_attention_heads": 32})
        a, b = load("parent_ckptcfg"), from_lm_eval(dst, "ifeval_greek", "prompt_level_strict_acc")
        with self.assertRaises(ComparabilityError): compare(a, b)                       # not a training effect
        self.assertEqual(compare(a, b, policy="geometry")["control"]["varying"], ["geometry"])
    def test_symlinked_stage_has_the_parents_identity(self):
        self.assertEqual(load("parent").manifest["weights_id"], load("parent_ckptcfg").manifest["weights_id"])
    def test_serving_effect_policy_is_still_date_guarded(self):
        with self.assertRaises(ComparabilityError) as cm: compare(load("parent"), load("parent_ckptcfg"), policy="gen_config")
        self.assertIn("Current date", str(cm.exception))

@need
class CycleOneDefeats(unittest.TestCase):
    def test_no_caller_controlled_escape_hatch(self):
        a, b = load("parent"), load("arm05_ep3")
        with self.assertRaises(TypeError): compare(a, b, varying=("weights_id", "gen_config"))
        with self.assertRaises(TypeError): compare(a, b, allow_unknown=("gen_config",))
        with self.assertRaises(ValueError): compare(a, b, policy="everything")
    def test_per_request_generation_options_are_bound(self):
        def f(rows):
            for r in rows: r["arguments"]["gen_args_0"]["arg_1"]["max_gen_toks"] = 64
        with self.assertRaises(ComparabilityError) as cm: compare(load("arm01s44_ep3"), mutated_copy(self, "arm05s44_ep3", samples=f))
        self.assertIn("requests differ", str(cm.exception))
    def test_gold_reassigned_among_ids_is_caught(self):
        def f(rows): rows[0]["target"], rows[1]["target"] = "SWAPPED-A", "SWAPPED-B"
        with self.assertRaises(ComparabilityError) as cm: compare(load("arm01s44_ep3"), mutated_copy(self, "arm05s44_ep3", samples=f))
        self.assertIn("different items or gold", str(cm.exception))
    def test_runtime_is_bound(self):
        def f(d): d["config"]["model_dtype"] = "torch.float16"
        with self.assertRaises(ComparabilityError) as cm: compare(load("arm01s44_ep3"), mutated_copy(self, "arm05s44_ep3", results=f))
        self.assertIn("runtime differs in: model_dtype", str(cm.exception))
    def test_identity_is_never_an_argument(self):
        with self.assertRaises(TypeError): from_lm_eval(staged("parent"), "ifeval_greek", "prompt_level_strict_acc", "parent", "parent")
        with self.assertRaises(TypeError): from_lm_eval(staged("arm05_ep3"), "ifeval_greek", "prompt_level_strict_acc", gen_config={"eos_token_id": 2})
    def test_a_run_without_a_receipt_has_no_identity(self):
        with self.assertRaises(ValueError) as cm: from_lm_eval(os.path.join(RAW, "parent"), "ifeval_greek", "prompt_level_strict_acc")
        self.assertIn("no run_receipt.json", str(cm.exception))
    def test_a_model_compared_with_itself_is_refused(self):
        with self.assertRaises(ComparabilityError) as cm: compare(load("arm05_ep3"), load("arm05_ep3_parentcfg"))   # one checkpoint, two labels
        self.assertIn("IDENTICAL on both sides", str(cm.exception))
    def test_unknowns_are_the_builders_to_declare_and_only_per_protocol(self):
        from rlhf.evals.compare import _check                       # private; used here only to pin the rule
        a, b = load("arm01s44_ep3").manifest, load("arm05s44_ep3").manifest
        for m in (a, b): m["gen_config"] = None; m["unrecordable"] = ["gen_config"]
        with self.assertRaises(ComparabilityError) as cm: _check(a, b)
        self.assertIn("does not permit", str(cm.exception))

class CycleTwoDefeats(unittest.TestCase):
    """R-DPO8b: each of these was still ACCEPTED after the first round of fixes."""
    @need
    def test_editing_a_manifest_changes_nothing(self):
        a, b = load("parent"), load("arm05_ep3")                    # differ in generation config: must refuse
        m = b.manifest; m["gen_config"] = a.manifest["gen_config"]  # the attack: edit, then compare
        with self.assertRaises(ComparabilityError): compare(a, b)   # the edit reached a copy, not the result
        with self.assertRaises(AttributeError): b._m = m
        with self.assertRaises(TypeError): compare(a.manifest, b.manifest)
    @need
    def test_outcomes_cannot_be_supplied_separately(self):
        a, b = load("arm01s44_ep3"), load("arm05s44_ep3")
        with self.assertRaises(TypeError): compare(a, {k: True for k in b.items})
        with self.assertRaises(TypeError): compare(a, a.items, b, b.items)
    def test_a_result_cannot_be_built_by_hand(self):
        with self.assertRaises(TypeError):
            Result({"label": "x", "n_items": 1, "protocol": "custom_full_text", "unrecordable": ["prompt_digest"]}, {"1": True})
    def test_the_manifest_level_check_is_not_public(self):
        self.assertFalse(hasattr(rlhf.evals, "check")); self.assertFalse(hasattr(rlhf.evals, "RunManifest"))
    @need
    def test_store_keeps_results_that_differ_only_in_geometry(self):
        """R-DPO10 finding 5: two sealed results differing only in geometry collapsed onto one store key."""
        tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmp); st = Store(tmp); d2 = os.path.join(tmp, "x"); shutil.copytree(os.path.join(RAW, "parent_ckptcfg"), d2)
        mint_receipt(d2, "parent_ckptcfg", geometry={"inv_freq_sha256": GEO_MISLOADED, "max_position_embeddings": 4096, "hidden_size": 4096, "num_hidden_layers": 32, "num_attention_heads": 32})
        k1 = st.put(load("parent_ckptcfg")); k2 = st.put(from_lm_eval(d2, "ifeval_greek", "prompt_level_strict_acc"))
        self.assertNotEqual(k1, k2); self.assertEqual(len(st.records(label="parent_ckptcfg")), 2)
    @need
    def test_store_takes_and_returns_only_sealed_results(self):
        tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmp); st = Store(tmp); a = load("parent_ckptcfg")
        with self.assertRaises(TypeError): st.put(a.manifest)
        key = st.put(a); self.assertEqual(st.one(label="parent_ckptcfg").seal, a.seal)
        f = os.path.join(tmp, "items", key + ".json")
        with open(f) as fh: it = json.load(fh)
        k0 = sorted(it)[0]; it[k0] = not it[k0]                     # tamper with one outcome on disk
        with open(f, "w") as fh: json.dump(it, fh)
        with self.assertRaises(ValueError) as cm: st.one(label="parent_ckptcfg")
        self.assertIn("failed its seal", str(cm.exception))
    @need
    def test_a_relabelled_weights_receipt_is_refused(self):
        r = dict(receipt_for("arm05_ep3")); r["weights_id"] = receipt_for("arm01_ep3")["weights_id"]
        with self.assertRaises(ValueError) as cm: load_receipt(r)
        self.assertIn("not self-consistent", str(cm.exception))
    @need
    def test_a_subset_is_a_different_population(self):
        a, b = load("arm01s44_ep3"), load("arm05s44_ep3"); keep = sorted(a.items)[:100]
        sa, sb = a.subset(keep, "first100"), b.subset(keep, "first100")
        self.assertEqual(compare(sa, sb)["n"], 100)
        with self.assertRaises(ComparabilityError): compare(a, sb)  # full frame vs subset never compares

@need
class AllLanesCompareAcrossProcesses(unittest.TestCase):
    """R-DPO11 finding 1: lm_eval serialises task callables with their memory address, so two scorer
    processes produced different task digests and compare() refused all 36 Global-MMLU lanes -- the
    comparison the frozen re-score exists to make. Uses the real 38-lane outputs of two models."""
    GEO = {"inv_freq_sha256": GEO_PARENT, "max_position_embeddings": 4096, "hidden_size": 4096,
           "num_hidden_layers": 32, "num_attention_heads": 32}

    def _twin(self, label, new_addr, mutate=None):
        """The run as a SEPARATE scorer process would have serialised it: only the addresses differ.
        Both sides get the parent's geometry, i.e. the repaired state the frozen re-score produces --
        these historic outputs carry the E6 mis-load, which the guard refuses for a different reason."""
        tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmp)
        dst = os.path.join(tmp, label); shutil.copytree(os.path.join(RAW, label), dst)
        f = glob.glob(os.path.join(dst, "**", "results_*.json"), recursive=True)[0]
        with open(f) as fh: raw = fh.read()
        raw = re.sub(r" at 0x[0-9a-fA-F]+>", " at 0x%s>" % new_addr, raw)
        if mutate: raw = mutate(raw)
        with open(f, "w") as fh: fh.write(raw)
        mint_receipt(dst, label, geometry=self.GEO)
        return dst

    def _lanes(self, run_dir):
        leaves = sorted(os.path.basename(f).split("samples_")[1].rsplit("_", 1)[0]
                        for f in glob.glob(os.path.join(run_dir, "**", "samples_global_mmlu_*.jsonl"), recursive=True))
        return [("ifeval_greek", "prompt_level_strict_acc"), ("mgsm_greek", "exact_match")] + [(t, "acc") for t in leaves]

    def test_all_38_lanes_compare_when_the_two_runs_were_serialised_separately(self):
        a_dir, b_dir = self._twin("parent", "aaaaaaaaaaaa"), self._twin("arm01_ep3", "bbbbbbbbbbbb")
        lanes = self._lanes(a_dir)
        self.assertEqual(len(lanes), 38)                                   # 1 IFEval + 1 MGSM + 36 Global-MMLU leaves
        ok, refused = 0, []
        for task, metric in lanes:
            try:
                compare(from_lm_eval(a_dir, task, metric), from_lm_eval(b_dir, task, metric)); ok += 1
            except ComparabilityError as e:
                refused.append("%s: %s" % (task, str(e).splitlines()[-1].strip()))
        self.assertEqual((ok, refused), (38, []))

    def test_a_genuinely_different_task_still_differs(self):
        a_dir = self._twin("parent", "aaaaaaaaaaaa")
        b_dir = self._twin("arm01_ep3", "bbbbbbbbbbbb", mutate=lambda r: r.replace("category='Business'", "category='Medical'"))
        with self.assertRaises(ComparabilityError) as cm:
            compare(from_lm_eval(a_dir, "global_mmlu_en_business", "acc"), from_lm_eval(b_dir, "global_mmlu_en_business", "acc"))
        self.assertIn("runtime differs in: task_config", str(cm.exception))
        compare(from_lm_eval(a_dir, "global_mmlu_en_stem", "acc"), from_lm_eval(b_dir, "global_mmlu_en_stem", "acc"))   # untouched lane still fine

@need
class ClosingReviewDefeats(unittest.TestCase):
    """R-DPO9 B2: accepted through the public API after two Sol cycles."""
    def test_a_false_generation_config_cannot_be_sealed_in(self):
        with self.assertRaises(TypeError): from_lm_eval(staged("arm05_ep3"), "ifeval_greek", "prompt_level_strict_acc", gen_config=load("parent").manifest["gen_config"])
        with self.assertRaises(ComparabilityError): compare(load("parent"), load("arm05_ep3"))
    def test_the_policy_table_cannot_be_widened(self):
        with self.assertRaises(TypeError): rlhf.evals.POLICIES["weights"] = ("weights_id", "gen_config")
    def test_another_models_receipt_does_not_fit_these_outputs(self):
        tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmp); dst = os.path.join(tmp, "p"); shutil.copytree(os.path.join(RAW, "parent"), dst)
        shutil.copy(os.path.join(staged("arm05_ep3"), "run_receipt.json"), os.path.join(dst, "run_receipt.json"))   # arm's receipt, parent's outputs
        with self.assertRaises(ValueError) as cm: from_lm_eval(dst, "ifeval_greek", "prompt_level_strict_acc")
        self.assertIn("does not match the files on disk", str(cm.exception))
    def test_outputs_edited_after_the_receipt_are_refused(self):
        tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmp); dst = os.path.join(tmp, "p"); shutil.copytree(staged("arm05s44_ep3"), dst)
        f = glob.glob(os.path.join(dst, "**", "samples_ifeval_greek_*.jsonl"), recursive=True)[0]
        with open(f, "a") as fh: fh.write("\n")
        with self.assertRaises(ValueError): from_lm_eval(dst, "ifeval_greek", "prompt_level_strict_acc")

@unittest.skipUnless(os.path.exists(os.path.join(OFFICIAL, "parent.json")) and HAVE, "official results not present")
class Protocols(unittest.TestCase):
    def test_official_result_reproduces_and_declares_what_it_could_not_record(self):
        a = from_official_greekmmlu(os.path.join(OFFICIAL, "parent.json")); b = from_official_greekmmlu(os.path.join(OFFICIAL, "arm05_ep3.json"))
        r = compare(a, b)
        self.assertEqual((r["n"], r["gained"], r["lost"]), (16632, 114, 186))    # independently reproduced in R-DPO8
        self.assertAlmostEqual(r["delta_pp"], -0.432900, places=5); self.assertIn("prompt_digest", r["control"]["unverified"])
        self.assertEqual(a.manifest["weights_id"], receipt_for("parent")["weights_id"])     # evaluator receipt == independent hash
        self.assertEqual(b.manifest["weights_id"], receipt_for("arm05_ep3")["weights_id"])
    def test_one_result_file_cannot_be_two_models(self):
        """R-DPO10 finding 1: the same parent.json, once with the parent's weights receipt and once with an arm's,
        was accepted as a weights comparison with 0 gained / 0 lost."""
        with self.assertRaises(TypeError): from_official_greekmmlu(os.path.join(OFFICIAL, "parent.json"), "arm05_ep3", receipt_for("arm05_ep3"))
        tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmp); f = os.path.join(tmp, "parent.json"); shutil.copy(os.path.join(OFFICIAL, "parent.json"), f)
        with self.assertRaises(ValueError) as cm: from_official_greekmmlu(f)                          # no receipt: no identity
        self.assertIn("no evaluator receipt", str(cm.exception))
        shutil.copy(os.path.join(OFFICIAL, "arm05_ep3.json.receipt.json"), f + ".receipt.json")       # an arm's receipt on the parent's result
        with self.assertRaises(ValueError) as cm: from_official_greekmmlu(f)
        self.assertIn("different result file", str(cm.exception))
        a = from_official_greekmmlu(os.path.join(OFFICIAL, "parent.json"))
        with self.assertRaises(ComparabilityError) as cm: compare(a, from_official_greekmmlu(os.path.join(OFFICIAL, "parent.json")))
        self.assertIn("IDENTICAL on both sides", str(cm.exception))
    def test_legacy_custom_protocol_results_can_be_read_but_never_compared(self):
        from rlhf.evals.manifest import _legacy_native_mcq
        self.assertFalse(hasattr(rlhf.evals, "from_native_mcq"))
        tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmp)
        shutil.copy(glob.glob(os.path.join(ITEMS250, "arm05_ep3", "*predictions.jsonl"))[0], tmp)
        with open(os.path.join(tmp, "run_metadata.json"), "w") as fh: json.dump({"schema": "x", "dataset_bindings": [{}]}, fh)
        b = _legacy_native_mcq(tmp, "arm05_ep3", receipt_for("arm05_ep3"))
        with self.assertRaises(ComparabilityError) as cm: compare(from_official_greekmmlu(os.path.join(OFFICIAL, "parent.json")), b)
        self.assertIn("asserted by a caller", str(cm.exception))

class Stats(unittest.TestCase):
    def test_mcnemar_matches_R_small_and_large(self):
        for g, l, want in ((9, 3, 0.1459961), (10, 5, 0.3017578), (9, 5, 0.4239502)):
            self.assertAlmostEqual(stats.mcnemar_exact(g, l), want, places=6)
        self.assertAlmostEqual(stats.mcnemar_exact(602, 530), 0.03479, places=4)
        self.assertAlmostEqual(stats.mcnemar_exact(131, 200), 0.0001768261, places=9)
        self.assertEqual(stats.mcnemar_exact(4, 4), 1.0); self.assertEqual(stats.mcnemar_exact(0, 0), 1.0)
    def test_published_alpha_intervals_are_pinned_numerically(self):
        a0 = [0.6173752310536045, 0.6118299445471349, 0.6173752310536045, 0.6099815157116451, 0.5988909426987061]
        a25 = [0.6210720887245841, 0.6229205175600739, 0.5970425138632163, 0.6303142329020333, 0.6192236598890942]
        u, p = stats.seed_bootstrap(a0, a25), stats.paired_seed_bootstrap(a0, a25)
        self.assertEqual((u["design"], p["design"]), ("unpaired", "paired"))
        for got, want in ((u["delta_pp"], 0.7024), (u["ci_pp"][0], -0.5176), (u["ci_pp"][1], 1.7745),
                          (p["delta_pp"], 0.7024), (p["ci_pp"][0], -0.7394), (p["ci_pp"][1], 1.8484)):
            self.assertAlmostEqual(got, want, places=3)
    def test_input_validation(self):
        for bad in (lambda: stats.paired({}, {}), lambda: stats.paired({"1": True}, {"2": True}),
                    lambda: stats.paired({"1": True}, {"1": "false"}), lambda: stats.seed_bootstrap([0.5], [0.6]),
                    lambda: stats.seed_bootstrap([0.5, 0.6], [0.6, 0.7], B=3), lambda: stats.seed_bootstrap([0.5, 0.6], [0.6, 0.7], level=1.5),
                    lambda: stats.paired_seed_bootstrap([0.5, 0.6], [0.6]), lambda: stats.holm([]),
                    lambda: stats.holm([0.2, 1.4]), lambda: stats.holm([0.2, float("nan")])):
            with self.assertRaises(ValueError): bad()
    def test_holm(self):
        adj = stats.holm([0.03479, 0.08427, 0.01231]); self.assertTrue(adj[2] < 0.05 < adj[0] and adj[1] > 0.05)

if __name__ == "__main__":
    unittest.main(verbosity=1)
