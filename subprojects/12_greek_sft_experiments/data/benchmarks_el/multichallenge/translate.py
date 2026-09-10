#!/usr/bin/env python3
"""MultiChallenge → Greek: one Sol call per conversation translates every turn (same count, same roles) and the target question, keeps entity forms
consistent, and flags conversations whose test depends on English-specific properties (letters, spelling, wordplay, English-only formats) as
nontransferable (reported separately, never silently adapted). Output multichallenge/conversations_el.jsonl. Usage: python3 translate.py [N] [--ids id,id]"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..')); import bench_lib as B
SCHEMA = B.M.write_schema('s_mc.json', {"type": "object", "properties": {"turns_el": {"type": "array", "items": {"type": "string"}}, "target_question_el": {"type": "string"}, "entities": {"type": "string"}, "nontransferable": {"type": "boolean"}, "reason": {"type": "string"}}, "required": ["turns_el", "target_question_el", "entities", "nontransferable", "reason"], "additionalProperties": False})
AXIS_EL = {'INFERENCE_MEMORY': 'μνήμη συμπερασμού: η τελευταία απάντηση πρέπει να χρησιμοποιήσει κάτι που ειπώθηκε νωρίτερα χωρίς να το επαναλάβει ο χρήστης',
           'INSTRUCTION_RETENTION': 'διατήρηση οδηγίας: μια οδηγία που δόθηκε νωρίτερα ισχύει ακόμη στην τελευταία απάντηση',
           'SELF_COHERENCE': 'αυτοσυνέπεια: η τελευταία απάντηση πρέπει να μείνει συνεπής με ό,τι είπε ο βοηθός πριν, ακόμη κι αν ο χρήστης πιέζει',
           'RELIABLE_VERSION_EDITING': 'αξιόπιστη επεξεργασία εκδόσεων: η τελευταία απάντηση πρέπει να ενσωματώσει σωστά όλες τις προηγούμενες αλλαγές'}


def translate(r):
    conv = r['CONVERSATION']; roles = [m['role'] for m in conv]
    text = '\n\n'.join(f"[{i}] {m['role'].upper()}:\n{m['content']}" for i, m in enumerate(conv))
    prompt = (B.RULES_EL + f"\n\nΑυτό είναι ένα στοιχείο του MultiChallenge (άξονας {r['AXIS']}: {AXIS_EL[r['AXIS']]}). Το μοντέλο που αξιολογείται θα δει τη συζήτηση ως εδώ και θα γράψει την ΕΠΟΜΕΝΗ απάντηση του βοηθού· "
              "ένας κριτής θα ελέγξει την απάντηση με την ερώτηση-κριτήριο. Μετάφρασε ΚΑΘΕ γύρο (ίδιος αριθμός γύρων, ίδια σειρά, ο [i] στο turns_el[i]) και την ερώτηση-κριτήριο. "
              "Ό,τι πρέπει να θυμάται ή να τηρεί ο βοηθός (οδηγίες, αριθμοί, ονόματα, προτιμήσεις, προηγούμενες εκδόσεις κειμένου) πρέπει να αποδοθεί με ΑΚΡΙΒΕΙΑ και με ΤΙΣ ΙΔΙΕΣ μορφές παντού· γράψε τις επιλογές ονομάτων/όρων στο entities (π.χ. UN headquarters → έδρα του ΟΗΕ). "
              "Αν το κριτήριο ή μια οδηγία εξαρτάται από ιδιότητες της ΑΓΓΛΙΚΗΣ γλώσσας (γράμματα, ορθογραφία, συλλαβές, ομοιοκαταληξία, λογοπαίγνια, αγγλικές μορφές ημερομηνίας/μονάδων που δεν έχουν νόημα στα ελληνικά) βάλε nontransferable=true και εξήγησε στο reason· μετάφρασε παρ' όλα αυτά όσο πιο πιστά γίνεται. "
              "Κείμενα που ο χρήστης δίνει για επεξεργασία (ποιήματα, email, κώδικας) μεταφράζονται ως κείμενα με τα ίδια χαρακτηριστικά· ο κώδικας μένει κώδικας.\n\n"
              f"ΣΥΖΗΤΗΣΗ ({len(conv)} γύροι):\n{text}\n\nΕΡΩΤΗΣΗ-ΚΡΙΤΗΡΙΟ: {r['TARGET_QUESTION']}\n\nΕπίστρεψε JSON {{\"turns_el\":[{len(conv)} strings],\"target_question_el\",\"entities\",\"nontransferable\",\"reason\"}}.")
    j = B.sol_json(prompt, SCHEMA, effort='medium', timeout=1500)
    if not j or len(j['turns_el']) != len(conv): print('turn count mismatch', r['QUESTION_ID'], flush=True); return None
    words_en = sum(len(m['content'].split()) for m in conv); words_el = sum(len(t.split()) for t in j['turns_el'])
    return dict(id=r['QUESTION_ID'], axis=r['AXIS'], turns_en=conv, turns_el=[dict(role=ro, content=t) for ro, t in zip(roles, j['turns_el'])], target_question_en=r['TARGET_QUESTION'], target_question_el=j['target_question_el'],
                pass_criteria=r['PASS_CRITERIA'], entities=j['entities'], nontransferable=j['nontransferable'], reason=j['reason'], words_en=words_en, words_el=words_el, len_ratio=round(words_el / max(1, words_en), 2))


if __name__ == '__main__':
    rows = B.load(os.path.join(HERE, 'source', 'benchmark_questions.jsonl'))
    for r in rows: r['id'] = r['QUESTION_ID']
    if '--ids' in sys.argv: ids = set(sys.argv[sys.argv.index('--ids') + 1].split(',')); rows = [r for r in rows if r['id'] in ids]
    n = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else len(rows)
    B.run_jobs(rows[:n], translate, os.path.join(HERE, 'conversations_el.jsonl'), stage=f'multichallenge translate {n}')
    allr = B.load(os.path.join(HERE, 'conversations_el.jsonl')); print('rows', len(allr), 'nontransferable', sum(r['nontransferable'] for r in allr), 'mean len ratio', round(sum(r['len_ratio'] for r in allr) / max(1, len(allr)), 2))
