import json, pathlib, sys, threading, unittest, sqlite3, tempfile, shutil, importlib
HERE = pathlib.Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import generate as G
import manifest as M
class T(unittest.TestCase):
    def test_category_quota_independent_of_subtype_count(self):
        a = M.lr(100, {'everyday': 25, 'instruction': 15}); self.assertEqual(sum(a.values()), 100); self.assertIn(a['everyday'], (62, 63)); self.assertEqual(a['everyday'] + a['instruction'], 100)
        # subtypes are split only inside a category
        sub = M.lr(a['everyday'], {s: 1 for s in json.load(open(HERE / 'task_kinds.json'))['everyday']}); self.assertEqual(sum(sub.values()), a['everyday'])
    def test_manifest_totals_and_compatibility(self):
        m = json.load(open(HERE / 'manifest_round3.json'))
        self.assertEqual(m['single_turn_slots'] + m['forum_selected_slots'] + m['dialogue_starting_seeds_reserved'], m['slot_budget'])
        self.assertEqual(sum(m['cell_totals'].values()), m['single_turn_slots'])
        for s in m['slots']:
            self.assertFalse(s['register'] == 'greeklish' and s['language'] != 'el', s['slot_id'])
            self.assertFalse(s['packet'] and s['detail'] == 'short', s['slot_id'])
        self.assertEqual(m['compatibility_violations'], [])
    def test_instance_key_ignores_ids_and_persona_but_not_values(self):
        slot = dict(purpose='math', subtype='calculation', slot_id='A', person='x', language='el', register='standard', attitude='cooperative', detail='bare')
        inst = dict(task_summary='Compute 3 + 4', givens=['3', '4'], constraints=[{'type': 't', 'params': '', 'text': 'answer only'}], deliverable='result only')
        k1 = G.instance_key(slot, inst); k2 = G.instance_key(dict(slot, slot_id='B', person='y', language='en'), inst)
        k3 = G.instance_key(slot, dict(inst, givens=['3', '5']))
        self.assertEqual(k1, k2); self.assertNotEqual(k1, k3)
    def test_reservation_atomic_across_threads(self):
        tmp = tempfile.mkdtemp(); G.REG = pathlib.Path(tmp) / 'r.sqlite'; results = []
        slot = dict(slot_id='S1')
        def worker(i): results.append(G.reserve(dict(slot_id=f'S{i}'), 'samekey', 'test', 1))
        ts = [threading.Thread(target=worker, args=(i,)) for i in range(8)]; [t.start() for t in ts]; [t.join() for t in ts]
        self.assertEqual(sum(results), 1); shutil.rmtree(tmp)
    def test_code_checks(self):
        slot = dict(slot_id='S', language='el', register='standard', detail='bare', packet=False)
        inst = dict(check_values=['42'], packet='')
        self.assertIn('missing_value:42', G.code_checks(slot, inst, dict(message='Πόσο κάνει αυτό;', pasted_span=''), []))
        self.assertIn('detail_ceiling_exceeded', G.code_checks(slot, inst, dict(message='Θέλω ' + 'πολύ ' * 15 + '42', pasted_span=''), []))
        self.assertEqual(G.code_checks(dict(slot, packet=True, detail='bare'), dict(check_values=[], packet='Κείμενο προς διόρθωση με πολλές λέξεις ' * 5), dict(message='διόρθωσε: ' + 'Κείμενο προς διόρθωση με πολλές λέξεις ' * 5, pasted_span='Κείμενο προς διόρθωση με πολλές λέξεις ' * 5), []), [])
        self.assertIn('wrong_language', G.code_checks(slot, dict(check_values=[], packet=''), dict(message='Please help me', pasted_span=''), []))
        self.assertIn('framing_or_meta_text', G.code_checks(dict(slot, detail='medium'), dict(check_values=[], packet=''), dict(message='Σε ένα φανταστικό σενάριο θέλω βοήθεια', pasted_span=''), []))
        self.assertTrue(any(i.startswith('near_duplicate') for i in G.code_checks(dict(slot, detail='medium'), dict(check_values=[], packet=''), dict(message='Θέλω βοήθεια με την εφορία μου αύριο', pasted_span=''), [('X', G.content_words('Θέλω βοήθεια με την εφορία μου αύριο'))])))
        self.assertEqual(G.code_checks(dict(slot, register='greeklish', detail='terse'), dict(check_values=[], packet=''), dict(message='Thelo voitheia me tin eforia', pasted_span=''), []), [])
    def test_instance_key_covers_packet_params_and_conditions(self):
        slot = dict(purpose='everyday', subtype='rewrite_supplied_draft')
        inst = dict(task_summary='Fix draft', givens=['a'], constraints=[{'type': 'length', 'params': '80', 'text': 'about 80 words'}], deliverable='draft', packet='Αγαπητέ κύριε', check_values=['80'], ambiguity='none', answer_conditions='keeps date')
        k = G.instance_key(slot, inst)
        self.assertNotEqual(k, G.instance_key(slot, dict(inst, packet='Αγαπητή κυρία')))
        self.assertNotEqual(k, G.instance_key(slot, dict(inst, constraints=[{'type': 'length', 'params': '120', 'text': 'about 80 words'}])))
        self.assertNotEqual(k, G.instance_key(slot, dict(inst, answer_conditions='keeps place')))
    def test_pasted_span_ignored_on_non_packet_slots(self):
        slot = dict(slot_id='S', language='it', register='standard', detail='medium', packet=False)
        msg = 'Durante la chiamata di stamattina il mio collega ha usato una sigla che non conosco'
        self.assertNotIn('wrong_language', G.code_checks(slot, dict(check_values=[], packet=''), dict(message=msg, pasted_span=msg), []))
        self.assertIn('no_own_words', G.code_checks(dict(slot, packet=True), dict(check_values=[], packet=msg), dict(message=msg, pasted_span=msg), []))
    def test_safety_decision_order_and_detail_note_reach_prompts(self):
        d = G.defs_for([dict(purpose='safety', subtype='fiction', detail='bare', register='standard', attitude='cooperative', difficulty='routine')])
        self.assertIn('Decision order', d); self.assertIn('Detail is defined by', d); self.assertIn('never raises the detail level', d)
        self.assertIn('math (maths)', G.defs_for([dict(purpose='everyday', subtype='plan_or_organise', detail='bare', register='standard', attitude='cooperative', difficulty='routine')], instance_stage=True))
    def test_scenario_screen_catches_cross_language_duplicates(self):
        a = dict(scenario='dental appointment rescheduling', task_summary='Rewrite a dental appointment email in formal Greek', givens=['Tuesday 10:00'])
        b = dict(scenario='dental clinic appointment request', task_summary='Rewrite an Italian message to a dental clinic', givens=['Friday'])
        c = dict(scenario='cat-safe houseplants', task_summary='Recommend plants', givens=['two cats'])
        known = [('A', G.instance_words(a), G.scenario_stems(a))]
        self.assertEqual(G.similar(b, known), ['A']); self.assertEqual(G.similar(c, known), [])
if __name__ == '__main__': unittest.main()
