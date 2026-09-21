"""The one Sol client. Every prompt generator, every judge and every reviewer goes through here.

Today the same `CodexServer` is imported and configured separately by `judge_rank4.py`, `forum_gate.py`,
`generator_v02/generate.py`, `maths_judge.py`, `dialogue_v2/clients.py` and `prompt_generator/worker.py`,
each repeating the same decisions and each free to get one of them wrong. This module makes the decisions
once, in one place, where they can be tested:

  * **Effort is a POLICY, not a parameter.** Pipeline work runs at medium; reviews at xhigh. Passing an
    effort by hand is refused: on 17 September ~1,750 pipeline calls ran at high by accident.
  * **A review is a different kind of call.** It needs a working shell, so `code_mode_host` must NOT be
    disabled for it -- that flag silently blinded two cross-vendor reviews on 19 September, producing an
    honest "UNREVIEWED" and a BLOCKER that was our own harness. `review()` therefore refuses this client
    and points at `cluster/run_review.sh`.
  * **JSON from Sol is checked before it is returned.** codex decodes LaTeX escapes such as backslash-theta
    into C0 control characters; `mathlib.reject_disallowed_controls` runs on every result.
  * **Budget is reported, not guessed.** `usage()` returns what the server actually accounted.

Concurrency: one server runs 24 concurrent turns (measured); `WORKERS` is that default and must not be
lowered or split across runs -- a restart is lossless, a smaller pool is just slower.
"""
import os, sys, threading

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "data", "math"))

MODEL = "gpt-5.6-sol"
WORKERS = 24
EFFORT = {"pipeline": "medium", "review": "xhigh", "hardest": "max"}

class EffortError(ValueError): pass
class ReviewThroughPipelineError(RuntimeError): pass

def _controls(obj):
    from mathlib import reject_disallowed_controls
    reject_disallowed_controls(obj)
    return obj

class Sol(object):
    """A pipeline Sol client: generation and judging. NOT for reviews -- see `review()`."""

    def __init__(self, cwd=None, model=MODEL, purpose="pipeline"):
        if purpose != "pipeline":
            raise EffortError("Sol() is the pipeline client; purpose=%r is not one of its jobs" % purpose)
        from codex_server import CodexServer
        self._srv = CodexServer(cwd=cwd)
        self._model, self._lock, self._calls = model, threading.Lock(), 0
        self._started = False

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.close(); return False

    def start(self):
        self._srv.start(); self._started = True; return self

    def call(self, prompt, schema, timeout=900, effort=None):
        """One schema-constrained turn at the pipeline effort. `effort` exists only to be refused."""
        if effort is not None:
            raise EffortError("effort is set by policy (%r for pipeline work), not per call. If a call "
                              "genuinely needs another effort, add it to rlhf.sol.EFFORT with a reason."
                              % EFFORT["pipeline"])
        if not self._started:
            raise RuntimeError("use `with Sol() as sol:` or call .start() -- the server is not running")
        out = self._srv.call(prompt, schema, model=self._model, effort=EFFORT["pipeline"], timeout=timeout)
        with self._lock:
            self._calls += 1
        return _controls(out)

    def usage(self):
        """What the server accounted for, not an estimate."""
        return {"calls": self._calls, "model": self._model, "effort": EFFORT["pipeline"],
                "turns": list(self._srv.usage)}

    def close(self):
        if self._started:
            self._srv.close(); self._started = False

def review(*a, **k):
    raise ReviewThroughPipelineError(
        "reviews do not run through this client. The pipeline server is started with "
        "features.code_mode_host=false, which disables the reviewer\'s shell: it can read nothing and "
        "returns an honest \'UNREVIEWED\' (this cost R-DPO6 and R-DPO7a on 19 September). Use "
        "cluster/run_review.sh <label> <brief.md> <model> <effort>, which runs a separate process with a "
        "working read-only shell, asserts the model from the session rollout, and refuses to file a "
        "review whose reviewer ran fewer than three commands.")
