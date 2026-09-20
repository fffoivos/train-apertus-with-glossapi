from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1] / 'staged'
sys.path.insert(0, str(ROOT / 'data' / 'math'))
sys.path.insert(0, str(ROOT / 'data' / 'benchmarks_el'))
sys.path.insert(0, str(ROOT / 'data' / 'math' / 'cut2'))

import mathlib
import bench_lib
import run_batches


def canonical_sha(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


class CodexJsonGuardsTest(unittest.TestCase):
    def test_literal_latex_survives_json_roundtrip(self):
        expected = "Λύση: \\frac{1}{2}\nΑπάντηση: \\boxed{1/2}"

        def fake_run(argv, **kwargs):
            output_path = argv[argv.index('-o') + 1]
            with open(output_path, 'w') as f:
                json.dump({'solution_el': expected}, f, ensure_ascii=False)
            return SimpleNamespace(returncode=0, stderr='')

        with mock.patch.object(mathlib.subprocess, 'run', side_effect=fake_run):
            result = mathlib.codex_json('prompt', 'schema.json')
        self.assertEqual(result['solution_el'], expected)
        self.assertIn(r'\frac', result['solution_el'])
        self.assertNotIn('\x0c', result['solution_el'])

    def test_disallowed_c0_and_del_report_recursive_location(self):
        for bad, label in [('\x08', 'U+0008'), ('\x7f', 'U+007F')]:
            with self.subTest(label=label):
                def fake_run(argv, **kwargs):
                    output_path = argv[argv.index('-o') + 1]
                    with open(output_path, 'w') as f:
                        json.dump({'outer': [{'solution': 'ok' + bad}]}, f)
                    return SimpleNamespace(returncode=0, stderr='')

                expected = f'disallowed control {label} at $.outer[0].solution[2]'
                with mock.patch.object(mathlib.subprocess, 'run', side_effect=fake_run):
                    with self.assertRaises(ValueError) as raised:
                        mathlib.codex_json('prompt', 'schema.json')
                self.assertEqual(str(raised.exception), expected)

    def test_disallowed_control_in_object_key_fails(self):
        with self.assertRaisesRegex(ValueError, 'U\\+0001'):
            mathlib.reject_disallowed_controls({'bad\x01key': 'value'})

    def test_tab_newline_and_carriage_return_are_allowed(self):
        mathlib.reject_disallowed_controls({'text': 'a\tb\nc\rd'})

    def test_nonzero_subprocess_return_code_raises_before_json_load(self):
        failed = SimpleNamespace(returncode=7, stderr='synthetic failure')
        with mock.patch.object(mathlib.subprocess, 'run', return_value=failed):
            with self.assertRaisesRegex(RuntimeError, 'return code 7: synthetic failure'):
                mathlib.codex_json('prompt', 'schema.json')


class RunJobsGuardsTest(unittest.TestCase):
    def test_conflicting_duplicate_id_fails_before_worker_call(self):
        called = []
        items = [{'id': 'same', 'problem_en': 'one'}, {'id': 'same', 'problem_en': 'two'}]
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, "conflicting duplicate input id='same'"):
                bench_lib.run_jobs(items, lambda item: called.append(item), str(Path(td) / 'out.jsonl'), workers=1)
        self.assertEqual(called, [])

    def test_identical_duplicate_is_collapsed_in_first_seen_order(self):
        item = {'id': 'same', 'problem_en': 'one'}
        called = []
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.object(bench_lib, 'codex_limit', return_value=None), \
             mock.patch.object(bench_lib, 'log_cost'):
            done = bench_lib.run_jobs([item, dict(item)], lambda x: called.append(x['id']) or x,
                                      str(Path(td) / 'out.jsonl'), workers=1)
        self.assertEqual(called, ['same'])
        self.assertEqual(done, [item])

    def test_worker_hard_max_applies_to_argument_and_environment(self):
        for workers in (0, 101):
            with self.subTest(workers=workers), tempfile.TemporaryDirectory() as td:
                with self.assertRaisesRegex(ValueError, 'workers must be between 1 and 100'):
                    bench_lib.run_jobs([], lambda x: x, str(Path(td) / 'out.jsonl'), workers=workers)
        with mock.patch.dict(os.environ, {'WORKERS': '101'}), tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, 'workers must be between 1 and 100'):
                bench_lib.run_jobs([], lambda x: x, str(Path(td) / 'out.jsonl'))

    def test_existing_historical_output_is_skipped_and_not_rewritten(self):
        old = {'id': 'old', 'solution_el': 'historical output'}
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.object(bench_lib, 'codex_limit', return_value=None), \
             mock.patch.object(bench_lib, 'log_cost'):
            path = Path(td) / 'out.jsonl'
            original = json.dumps(old, ensure_ascii=False) + '\n'
            path.write_text(original)
            done = bench_lib.run_jobs([{'id': 'old'}], lambda x: self.fail('worker called'), str(path), workers=1)
            self.assertEqual(done, [])
            self.assertEqual(path.read_text(), original)


class ProvenanceTest(unittest.TestCase):
    def test_problem_provenance_binds_input_prompt_model_and_effort(self):
        prompts = []

        def fake_sol(prompt, schema, model, effort):
            prompts.append(prompt)
            return {'problem_el': 'Ελληνικό πρόβλημα', 'changes': 'none'}

        first = {'id': 'p', 'problem_en': 'Compute 1+1.', 'solution_en': '2', 'subject': 'Algebra'}
        second = dict(first, problem_en='Compute 1+2.')
        with mock.patch.object(run_batches.B, 'sol_json', side_effect=fake_sol):
            out1 = run_batches.problem(first, 'high', model='test-model')
            out2 = run_batches.problem(second, 'high', model='test-model')
        self.assertEqual(out1['generation']['input_sha256'], canonical_sha(first))
        self.assertEqual(out1['generation']['prompt_sha256'], hashlib.sha256(prompts[0].encode('utf-8')).hexdigest())
        self.assertEqual(out1['generation']['model'], 'test-model')
        self.assertEqual(out1['generation']['effort'], 'high')
        self.assertNotEqual(out1['generation']['input_sha256'], out2['generation']['input_sha256'])
        self.assertNotEqual(out1['generation']['prompt_sha256'], out2['generation']['prompt_sha256'])

    def test_solution_provenance_binds_actual_input_and_prompt(self):
        prompts = []

        def fake_sol(prompt, schema, model, effort):
            prompts.append(prompt)
            return {'solution_el': 'Λύση'}

        item = {'id': 's', 'problem_el': 'Πόσο κάνει 1+1;', 'solution_en': '1+1=2',
                'ref': '2', 'level': 'Level 5', 'src': 'math'}
        with mock.patch.object(run_batches.B, 'sol_json', side_effect=fake_sol):
            out = run_batches.solution(item, 'medium', model='test-model')
        self.assertEqual(out['generation']['input_sha256'], canonical_sha(item))
        self.assertEqual(out['generation']['prompt_sha256'], hashlib.sha256(prompts[0].encode('utf-8')).hexdigest())
        self.assertEqual(out['generation']['model'], 'test-model')
        self.assertEqual(out['generation']['effort'], 'medium')


if __name__ == '__main__':
    unittest.main(verbosity=2)
