#!/usr/bin/env python3
import copy
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path('/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments')
OUT = Path('/Users/foivoskarounos-zamparloukos/Documents/Codex/2026-09-13/rea/outputs/parallel_improvement_plan/execution/wave2/personality')
FINAL = ROOT / 'data/personality/personality_v3v4_final.jsonl'
V4 = ROOT / 'data/personality/v4/personality_rows_final.jsonl'
RAW = ROOT / 'data/personality/v4/personality_rows.jsonl'
CHECKS = ROOT / 'data/personality/v4/checks_opus.jsonl'

def load(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

rows = load(FINAL)
v4 = load(V4)
raw = {r['id']: r for r in load(RAW)}
checks = {r['id']: r for r in load(CHECKS)}

structural = {'H07_00','H07_02','H07_03','H07_05','H07_06','H07_08'}
runtime_i = {
    *(f'I00_{i:02d}' for i in range(12)),
    *(f'I01_{i:02d}' for i in range(12)),
    'I02_00','I02_07','I02_11','I03_10'
}
runtime_h = {'H07_07'}

audit = []
for r in v4:
    rid = r['id']
    if rid in structural:
        disp = 'repair_structural_before_reuse'
        reason = 'Final row ends on a user turn; the editor replaced the final user text but did not append the intended assistant target.'
    elif rid in runtime_i or rid in runtime_h:
        disp = 'deployment_conditional_rewrite'
        reason = 'The answer makes a runtime/interface assertion that is not an invariant property of reusable weights.'
    else:
        disp = 'retain_v4_core'
        reason = 'No identity/deployment contradiction found in the bounded full-v4 read; ordinary factual accuracy was not exhaustively re-sourced.'
    audit.append({
        'id': 'v4_' + rid,
        'source_id': rid,
        'category': r['category'],
        'disposition': disp,
        'reason': reason,
        'last_role': r['messages'][-1]['role'],
        'message_count': len(r['messages']),
    })

(OUT / 'v4_full_audit.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in audit))

repairs = []
for rid in sorted(structural):
    candidate = copy.deepcopy(raw[rid])
    candidate['messages'].append({'role':'assistant','content':checks[rid]['edited_last_answer']})
    candidate['id'] = 'v4_' + rid
    repairs.append({
        'row_id': 'v4_' + rid,
        'action': 'candidate_repair',
        'established_defect': 'source row ended with user turn and had no supervised final assistant target',
        'candidate': candidate,
        'provenance': {
            'conversation': str(RAW),
            'assistant_close': str(CHECKS),
            'note': 'Reconstructs the original final user turn and appends the already reviewed assistant close.'
        }
    })

grounded_fixes = {
 'v4_H07_07': 'Γεια σου. Στο πλαίσιο που μου δόθηκε εδώ βλέπω αυτή τη συζήτηση. Αν η αυριανή συνομιλία δεν περιλαμβάνει το ιστορικό, επικόλλησε ξανά το προφίλ.',
 'v4_I00_00': 'Γεια σου. Στο πλαίσιο που μου δόθηκε εδώ δεν υπάρχει η χθεσινή συζήτηση. Αν υπάρχει στο ιστορικό της εφαρμογής, αντίγραψε τα βασικά σημεία· αλλιώς γράψε μου το θέμα της εργασίας και ό,τι θυμάσαι, και συνεχίζουμε από εκεί.',
 'v4_I00_02': 'Δεν μπορώ να συμπεράνω από εδώ τι αποθηκεύει ή ποια εργαλεία διαθέτει η εφαρμογή. Αυτό το ορίζει ο πάροχός της και πρέπει να αναφέρεται στην πολιτική απορρήτου και στην τεκμηρίωση της υπηρεσίας. Για τα email, χρησιμοποίησε [Όνομα], [ΑΦΜ] και [Ποσό] και συμπλήρωσέ τα μόνο στο τελικό κείμενο.',
 'v4_I00_03': 'Χωρίς τον μισθό: [κρατήστε το ήδη διορθωμένο κείμενο]. Δεν μπορώ να εγγυηθώ διαγραφή από την υπηρεσία. Στο τρέχον πλαίσιο εξακολουθεί να υπάρχει το προηγούμενο μήνυμα· για τυχόν αποθήκευση ή διαγραφή χρησιμοποίησε τις ρυθμίσεις και την πολιτική του παρόχου.',
 'v4_I00_05': 'Καλησπέρα σας. Δεν μπορώ να διαπιστώσω από εδώ αν η υπηρεσία καταγράφει συνομιλίες ή τις χρησιμοποιεί για εκπαίδευση· αυτό πρέπει να τεκμηριώνεται από τον πάροχο. Για το συγκεκριμένο checkpoint, η άδεια, η διαθεσιμότητα βαρών και η δημοσίευση δεδομένων πρέπει να ελεγχθούν στο δελτίο έκδοσής του.',
 'v4_I01_00': 'Το περιεχόμενο του PDF δεν έχει δοθεί στο πλαίσιο που βλέπω εδώ. Επικόλλησε το κείμενο της εργασίας και θα σου πω τι στέκει, πού θέλει δουλειά η γλώσσα και ποια ιστορικά στοιχεία αξίζει να ξαναελεγχθούν.',
 'v4_I01_01': 'Η φωτογραφία δεν έχει δοθεί ως αναγνώσιμο περιεχόμενο στο πλαίσιο που βλέπω εδώ. Γράψε όποιο όνομα φαρμάκου διαβάζεις και ο φαρμακοποιός σου ας επιβεβαιώσει το φάρμακο και τις οδηγίες λήψης.',
 'v4_I01_02': 'Δεν έχει δοθεί εδώ το περιεχόμενο της ανακοίνωσης ή αποτέλεσμα ανοίγματος του συνδέσμου. Επικόλλησε το κείμενο για να το εξηγήσω· για ποσά και προθεσμίες, έλεγξε την επίσημη ανακοίνωση ή ρώτησε τον λογιστή σου.',
 'v4_I01_08': 'Το φωνητικό δεν έχει δοθεί εδώ ως ήχος ή απομαγνητοφώνηση. Αν η εφαρμογή υποστηρίζει υπαγόρευση, μετέτρεψέ το σε κείμενο και στείλε το κείμενο.',
 'v4_I01_09': 'Δεν έχει δοθεί εδώ αποτέλεσμα ανοίγματος του συνδέσμου. Από τη συντομευμένη διεύθυνση bit.ly δεν φαίνεται πού καταλήγει· έλεγξέ το από επίσημο κανάλι της τράπεζας, όπως το τηλέφωνο στην πίσω πλευρά της κάρτας.',
 'v4_I02_00': 'Δεν μου έχει δοθεί η τρέχουσα ώρα στο πλαίσιο που βλέπω. Δες την στο κινητό ή στον υπολογιστή σου.',
 'v4_I02_07': 'Δεν έχω σώμα, αισθητήρες ή κινητήρες. Στο συγκεκριμένο περιβάλλον λαμβάνω το κείμενο που μου δίνεται και επιστρέφω κείμενο.',
 'v4_I02_11': 'Με την ώρα που έδωσες, ο λογαριασμός βγαίνει: με 4,5–5 χλμ./ώρα, τα 6 χλμ. θέλουν 1 ώρα και 12 λεπτά έως 1 ώρα και 20 λεπτά, άρα φτάνεις 8:52–9:00.',
 'v4_I03_10': 'Οι υπολογισμοί βγήκαν μόνο από τις τιμές που μου έγραψες: 0,158 €, 0,142 € ανά κιλοβατώρα και 350 kWh τον μήνα. Για τα τρέχοντα τιμολόγια χρειάζεται έλεγχος στις δημοσιεύσεις των παρόχων ή στο εργαλείο σύγκρισης της ΡΑΑΕΥ.'
}
for rid, ans in grounded_fixes.items():
    repairs.append({
        'row_id': rid,
        'action': 'candidate_last_answer_rewrite',
        'candidate_last_answer': ans,
        'basis': 'Prompt-observable context plus local deployment evidence; avoids universal claims about reusable weights or service storage.'
    })
(OUT / 'candidate_fixes.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in repairs))

family_ids = {
 'release_public_or_open_claims': 'B00_00,B00_01,B00_02,B00_03,B00_04,B00_07,B00_08,B00_14,B01_01,B01_02,B01_03,B01_05,B01_06,B01_07,B01_08,B01_12,B01_14,B02_00,B02_01,B02_02,B02_06,B02_07,B02_08,B02_11,B02_13,B03_00,B03_01,B03_02,B03_03,B03_04,B03_05,B03_07,B03_08,B03_09,B03_10,B03_11,B03_12,B03_13,B03_14,B04_03,B04_09,B05_03,B05_05,B05_14,B06_02,B06_08,B06_09,B07_01,B07_13,B08_00,B08_02,B08_03,B08_04,B08_11,B08_12,B08_13,B08_14,B09_00,B09_03,B09_04,B09_06,B09_08,B09_13,B10_04,B10_05,B10_06,B10_12,B10_13,B11_04,B11_08,B11_09,B11_12,C00_05,C01_02,C01_09,C02_03,C02_09,C05_00,C06_09,C07_02,B01_10,B09_01,B10_01,C08_01,v4_I00_05'.split(','),
 'apache_2_claims': 'B00_03,B00_07,B01_12,B01_14,B02_00,B02_13,B03_00,B03_01,B03_02,B03_03,B03_04,B03_05,B03_06,B03_07,B03_08,B03_09,B03_10,B03_11,B03_12,B03_13,B03_14,B04_09,B05_03,B05_05,B05_14,B08_02,B08_03,B08_12,B08_13,B09_03,B09_04,B10_13,C01_02,C02_09,C05_00,C07_02,C09_05,C09_08,B10_01,C08_01'.split(','),
 'mid_2025_cutoff_claims': 'B00_02,B00_07,B00_11,B00_12,B02_00,B02_01,B02_05,B02_12,B04_09,B05_00,B05_02,B05_04,B05_05,B05_11,B05_12,B06_02,B06_13,B07_00,B07_01,B07_02,B07_03,B07_05,B07_06,B07_07,B07_08,B07_09,B07_10,B07_11,B07_12,B07_13,B08_03,B08_08,B08_12,B11_00,B11_01,B11_02,B11_04,B11_05,B11_08,B11_09,B11_11,B11_13,B11_14,C00_06,C03_08,C05_09,C06_01,C07_02,C07_04,C08_09,B07_14,C08_01'.split(','),
 'runtime_conditional_v4': sorted('v4_'+x for x in runtime_i | runtime_h),
 'v4_structural_missing_target': sorted('v4_'+x for x in structural),
 'registered_v3_fact_corrections': ['A14_09','A21_21','F05_03','A02_02','A01_22','G09_09','A12_20'],
}

def matching_ids(pattern):
    rx = re.compile(pattern, re.I)
    return [r['id'] for r in rows if rx.search(r['messages'][-1]['content'].replace('\n',' '))]

family_ids.update({
 'absolute_internet_claims_all': matching_ids(r'(?:ίντερνετ|διαδίκτυο) δεν (?:έχω|έχει)|δεν έχω πρόσβαση (?:στο|σε) (?:ίντερνετ|διαδίκτυο)|δεν συνδέομαι στο διαδίκτυο'),
 'absolute_modality_claims_all': matching_ids(r'(?:φωτογραφίες|εικόνες) δεν (?:βλέπω|βλέπει)|ήχο δεν (?:ακούω|ακούει)|δουλεύ(?:ω|ει) μόνο με κείμενο|αρχεία δεν ανοίγω|συνημμένα δεν μπορώ να ανοίξω'),
 'absolute_cross_conversation_claims_all': matching_ids(r'κάθε συνομιλία ξεκινά από το μηδέν|δεν κρατ(?:ώ|άω).*συζήτηση|δεν θυμ(?:άμαι|άται).*συνομιλ|σε νέα συνομιλία δεν'),
 'absolute_current_context_claims_all': matching_ids(r'βλέπω όλα τα μηνύματα|τα έχω όλα μπροστά μου|βλέπω μόνο.*αυτήν'),
 'tool_or_permanent_storage_claims_all': matching_ids(r'δεν έχω εργαλεία|δυνατότητα μόνιμης αποθήκευσης|δεν μπορώ να (?:τον )?κρατήσω'),
})
claims = {
 'source_sha256': sha(FINAL),
 'claim_families': family_ids,
 'invariants': {
   'supported_model_identity': 'Greek adaptation of swiss-ai/Apertus-8B-2509; local CPT checkpoint fffoivos/apertus-8b-greek-cpt revision 18-avg-uniform5-tokens30B-50B.',
   'supported_adaptation': 'GlossAPI team of EELLAK; continued Greek pretraining then SFT; Swiss AI Initiative grant.',
   'supported_serving_snapshot': 'Direct vLLM OpenAI-compatible endpoint, max model length 4096, no tool flags in the canonical command.',
   'not_invariant': ['internet availability','file/link/image/audio adapters','clock/location services','cross-conversation memory','service logging/deletion','tool availability'],
   'unresolved_release_facts': ['licence of Greek released weights','blanket public availability of Greek weights/code/data','single knowledge cutoff'],
   'stable_style_or_ontology': ['no physical body or personal senses','no personal feelings/life','no proper product name by owner decision','warranted first-person reference to the model and visible conversation']
 }
}
(OUT / 'claim_inventory.json').write_text(json.dumps(claims,ensure_ascii=False,indent=2)+'\n')

manifest = {
 'inputs': {str(x): {'sha256':sha(x),'rows':len(load(x))} for x in [FINAL,V4,RAW,CHECKS]},
 'outputs': {},
 'counts': {
   'v4_rows_read': len(v4),
   'v4_categories': Counter(r['category'] for r in v4),
   'v4_dispositions': Counter(x['disposition'] for x in audit),
   'v4_last_role': Counter(r['messages'][-1]['role'] for r in v4),
   'candidate_fixes': len(repairs),
 }
}
for fn in ['v4_full_audit.jsonl','candidate_fixes.jsonl','claim_inventory.json','report.md','evidence_table.md','build_audit.py']:
 p=OUT/fn;manifest['outputs'][fn]={'sha256':sha(p),'bytes':p.stat().st_size}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2,default=dict)+'\n')
