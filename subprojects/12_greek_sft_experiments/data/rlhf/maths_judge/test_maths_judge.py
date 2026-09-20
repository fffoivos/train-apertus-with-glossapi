#!/usr/bin/env python3
"""Regression tests for deterministic maths eligibility (R-RL2 finding 1)."""
import pathlib, sys, unittest
HERE = pathlib.Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import maths_judge as M
def ref(status='verified', agree=True): return dict(status=status, comparison=dict(agree=agree))
def cand(**kw):
    c = dict(outcome='correct', reasoning='valid', task_completion='complete', requested_explanation=True, errors=[], handled_ambiguity='not_applicable', verdict='reinforce', eligible_positive=True, note='')
    c.update(kw); return c
class T(unittest.TestCase):
    def test_correct_and_valid_is_positive(self):
        self.assertTrue(M.eligible(cand(), ref()))
    def test_correct_answer_with_invalid_derivation_is_not_positive(self):
        c = cand(reasoning='invalid'); self.assertFalse(M.eligible(c, ref()))
        c['eligible_positive'] = M.eligible(c, ref()); self.assertEqual(M.sync_verdict(c), 'neutral')
    def test_short_correct_answer_without_requested_explanation_is_positive(self):
        self.assertTrue(M.eligible(cand(reasoning='not_provided', requested_explanation=False), ref()))
    def test_requested_explanation_missing_is_not_positive(self):
        self.assertFalse(M.eligible(cand(reasoning='not_provided', requested_explanation=True), ref()))
    def test_incomplete_or_incorrect_is_not_positive(self):
        self.assertFalse(M.eligible(cand(task_completion='partial'), ref()))
        self.assertFalse(M.eligible(cand(outcome='partial'), ref()))
        self.assertFalse(M.eligible(cand(outcome='incorrect'), ref()))
    def test_ambiguous_reference_needs_handled_ambiguity(self):
        self.assertTrue(M.eligible(cand(handled_ambiguity='yes'), ref('ambiguous')))
        self.assertFalse(M.eligible(cand(handled_ambiguity='no'), ref('ambiguous')))
        self.assertFalse(M.eligible(cand(handled_ambiguity='not_applicable'), ref('ambiguous')))
    def test_unresolved_or_disagreement_is_never_positive(self):
        self.assertFalse(M.eligible(cand(handled_ambiguity='yes'), ref('unresolved')))
        self.assertFalse(M.eligible(cand(), ref('verified', agree=False)))
    def test_model_flag_alone_cannot_create_a_positive(self):
        c = cand(outcome='incorrect', eligible_positive=True, verdict='reinforce')
        c['eligible_positive'] = M.eligible(c, ref()); self.assertFalse(c['eligible_positive']); self.assertEqual(M.sync_verdict(c), 'neutral')
class V2(unittest.TestCase):
    """maths-v2: the judge does the mathematics itself; eligibility is computed from its own question status."""
    def c(self, **kw):
        d = dict(outcome='correct', reasoning='valid', task_completion='complete', requested_explanation=True,
                 handled_ambiguity='not_applicable', question_status='determinate', verdict='reinforce', eligible_positive=True)
        d.update(kw); return d
    def test_correct_and_complete_is_positive(self): self.assertTrue(M.eligible_v2(self.c()))
    def test_invalid_derivation_is_not_positive(self): self.assertFalse(M.eligible_v2(self.c(reasoning='invalid')))
    def test_short_correct_answer_is_positive_when_no_explanation_requested(self): self.assertTrue(M.eligible_v2(self.c(reasoning='not_provided', requested_explanation=False)))
    def test_ambiguous_question_needs_handling(self):
        self.assertFalse(M.eligible_v2(self.c(question_status='ambiguous', handled_ambiguity='no')))
        self.assertTrue(M.eligible_v2(self.c(question_status='ambiguous', handled_ambiguity='yes')))
    def test_unresolvable_question_gives_no_positive(self): self.assertFalse(M.eligible_v2(self.c(question_status='unresolvable')))
    def test_model_flag_alone_cannot_create_a_positive(self):
        c = self.c(outcome='incorrect'); c['eligible_positive'] = M.eligible_v2(c)
        self.assertFalse(c['eligible_positive']); self.assertEqual(M.sync_verdict(c), 'neutral')
class Reconcile(unittest.TestCase):
    def test_strictest_status_applies_to_every_batch(self):
        import tempfile, json, os
        c = lambda **kw: dict(dict(outcome='correct', reasoning='valid', task_completion='complete', requested_explanation=True, handled_ambiguity='no',
                                   question_status='determinate', verdict='reinforce', eligible_positive=True, verdict_model='reinforce'), **kw)
        rows = [dict(id='P', batch=0, rubric='maths-v2', question_status='determinate', by_k={'0': c(), '1': c()}),
                dict(id='P', batch=1, rubric='maths-v2', question_status='ambiguous', by_k={'4': c(), '5': c(handled_ambiguity='yes')})]
        d = tempfile.mkdtemp(); f = os.path.join(d, 'j.jsonl')
        with open(f, 'w') as h:
            for r in rows: h.write(json.dumps(r) + '\n')
        M.reconcile([f]); out = [json.loads(l) for l in open(f)]
        self.assertTrue(all(r['question_status'] == 'ambiguous' for r in out))
        pos = {k for r in out for k, v in r['by_k'].items() if v['eligible_positive']}
        self.assertEqual(pos, {'5'})
if __name__ == '__main__': unittest.main()
