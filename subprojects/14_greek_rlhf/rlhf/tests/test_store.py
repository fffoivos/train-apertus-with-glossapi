import os, sys, tempfile, unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
from rlhf.evals.manifest import RunManifest
from rlhf.evals.result import Result, _BUILDER     # tests may mint results; callers may not
from rlhf.evals.store import Store
from rlhf.evals.compare import ComparabilityError

def man(label, protocol="official_label", digest="d1", prompts="p1", n=4):
    return RunManifest(label=label, weights_id=label, benchmark="greekmmlu", protocol=protocol, metric="correct",
                       n_items=n, item_digest=digest, prompt_digest=prompts, gen_config={"eos": 2},
                       gen_kwargs={}, runtime={"dtype": "bf16"}, geometry={"inv_freq_sha256": "g"}, tokenizer_sha="t", harness={"h": 1}, unrecordable=[])
def res(label, items=None, **kw):
    it = items or ITEMS; m = man(label, **kw); m['n_items'] = len(it); return Result(m, it, _token=_BUILDER)

ITEMS = {"1": True, "2": False, "3": True, "4": True}

class StoreTests(unittest.TestCase):
    def setUp(self): self.s = Store(tempfile.mkdtemp())
    def test_no_identity_no_entry(self):
        m = man("a"); m["protocol"] = None
        with self.assertRaises(ValueError): self.s.put(Result(m, ITEMS, _token=_BUILDER))
    def test_protocols_never_share_a_slot(self):
        self.s.put(res("a")); self.s.put(res("a", protocol="custom_full_text"))
        self.assertEqual(len(self.s.records(label="a")), 2)
        with self.assertRaises(LookupError): self.s.one(label="a")            # ambiguous on purpose
        self.assertEqual(self.s.one(label="a", protocol="official_label").manifest["protocol"], "official_label")
    def test_group_refuses_mixed_populations(self):
        self.s.put(res("a")); self.s.put(res("b", digest="d2"))
        with self.assertRaises(ComparabilityError): self.s.group(["a", "b"], protocol="official_label")
    def test_group_refuses_mixed_dates(self):
        self.s.put(res("a")); self.s.put(res("b", prompts="p2"))
        with self.assertRaises(ComparabilityError): self.s.group(["a", "b"], protocol="official_label")
    def test_group_ok(self):
        self.s.put(res("a")); self.s.put(res("b", items=dict(ITEMS, **{"2": True})))
        g = self.s.group(["a", "b"], protocol="official_label")
        self.assertEqual(g["n_runs"], 2); self.assertAlmostEqual(g["mean"], 0.875)
    def test_outcomes_must_be_boolean_and_complete(self):
        with self.assertRaises(ValueError): res("a", items=dict(ITEMS, **{"1": "false"}))
        with self.assertRaises(ValueError): Result(man("a", n=5), ITEMS, _token=_BUILDER)
        with self.assertRaises(TypeError): self.s.put(man("a"))

if __name__ == "__main__":
    unittest.main()
