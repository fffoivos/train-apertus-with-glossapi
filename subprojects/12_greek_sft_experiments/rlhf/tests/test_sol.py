"""The Sol client's policies, without calling Sol."""
import os, sys, types, unittest
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, ROOT)
from rlhf import sol

class FakeServer(object):
    def __init__(self, cwd=None, extra_flags=()): self.usage = [{"input_tokens": 10}]; self.calls = []
    def start(self): return {"ok": True}
    def call(self, prompt, schema, model=None, effort=None, timeout=None):
        self.calls.append({"model": model, "effort": effort}); return {"verdict": "fine"}
    def close(self): pass

class Policies(unittest.TestCase):
    def setUp(self):
        self._real = sys.modules.get("codex_server")
        sys.modules["codex_server"] = types.SimpleNamespace(CodexServer=FakeServer)
    def tearDown(self):
        if self._real is not None: sys.modules["codex_server"] = self._real
        else: sys.modules.pop("codex_server", None)

    def test_effort_is_policy_not_a_parameter(self):
        with sol.Sol() as s:
            with self.assertRaises(sol.EffortError): s.call("p", {}, effort="high")
            s.call("p", {})
            self.assertEqual(s._srv.calls[-1], {"model": sol.MODEL, "effort": "medium"})

    def test_reviews_refuse_the_pipeline_client(self):
        with self.assertRaises(sol.ReviewThroughPipelineError) as cm: sol.review("brief.md")
        self.assertIn("run_review.sh", str(cm.exception)); self.assertIn("code_mode_host", str(cm.exception))

    def test_latex_control_characters_are_refused(self):
        bad_text = "x = " + chr(8) + "eta + 1"          # codex decoding backslash-b-e-t-a
        class Bad(FakeServer):
            def call(self, *a, **k): return {"solution": bad_text}
        sys.modules["codex_server"] = types.SimpleNamespace(CodexServer=Bad)
        with sol.Sol() as s:
            with self.assertRaises(ValueError) as cm: s.call("p", {})
            self.assertIn("disallowed control", str(cm.exception))

    def test_server_must_be_started(self):
        with self.assertRaises(RuntimeError): sol.Sol().call("p", {})

    def test_usage_is_reported_from_the_server(self):
        with sol.Sol() as s:
            s.call("p", {}); u = s.usage()
            self.assertEqual((u["calls"], u["effort"]), (1, "medium")); self.assertTrue(u["turns"])

    def test_worker_default_is_not_lowered(self):
        self.assertEqual(sol.WORKERS, 24)

if __name__ == "__main__":
    unittest.main()
