#!/usr/bin/env python3
"""Build the review-only personality repair patch and fact adjudications."""
from pathlib import Path
import hashlib, json

HERE=Path('/Users/foivoskarounos-zamparloukos/Documents/Codex/2026-09-13/rea')
PROJ=Path('/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments')
OUT=HERE/'outputs/parallel_improvement_plan/execution/wave2/personality'
CONSOLIDATED=PROJ/'data/personality/personality_v3v4_final.jsonl'
V4_FINAL=PROJ/'data/personality/v4/personality_rows_final.jsonl'
OLD=OUT/'candidate_fixes.jsonl'
AUDIT=OUT/'v4_full_audit.jsonl'
ASSEMBLY=OUT/'assembly_verification.json'

def load(p): return [json.loads(x) for x in p.read_text().split('\n') if x.strip()]
def csha(x): return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def fsha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

consolidated={r['id']:r for r in load(CONSOLIDATED)}
source={r['id']:r for r in load(V4_FINAL)}
drafts={r['row_id']:r for r in load(OLD)}
audit=load(AUDIT)
assembly=json.loads(ASSEMBLY.read_text())
deployment_ids=[r['id'] for r in audit if r['disposition']=='deployment_conditional_rewrite']
closure_ids=[r['id'] for r in audit if r['disposition']=='repair_structural_before_reuse']

new_answers={
'v4_I00_01': 'Στο πλαίσιο που μου δόθηκε εδώ έχω τη λίστα μπροστά μου. Αν αύριο η εφαρμογή συμπεριλάβει αυτή τη συζήτηση στο πλαίσιο, μπορώ να τη χρησιμοποιήσω· αλλιώς ξαναγράψτε μου τι μαγειρεύετε και για πόσα άτομα. Για σιγουριά, κρατήστε τη λίστα σε χαρτί ή στο κινητό σας.',
'v4_I00_03': '''Χωρίς τον μισθό:

Καλημέρα [Όνομα],

θα ήθελα να κανονίσουμε μια συνάντηση για να συζητήσουμε μια αναπροσαρμογή του μισθού μου. Είμαι δύο χρόνια στην εταιρεία και έχω αναλάβει επιπλέον την εκπαίδευση των νέων συναδέλφων, κάτι που θα ήθελα να αποτυπωθεί και στις αποδοχές μου.

Πείτε μου πότε σας βολεύει μέσα στην εβδομάδα.

Ευχαριστώ,
[Όνομα]

Δεν μπορώ να εγγυηθώ διαγραφή από την υπηρεσία. Στο τρέχον πλαίσιο εξακολουθεί να υπάρχει το προηγούμενο μήνυμα· για τυχόν αποθήκευση ή διαγραφή χρησιμοποίησε τις ρυθμίσεις και την πολιτική του παρόχου.''',
'v4_I00_04': 'Αν μου γράψεις σε πλαίσιο που περιλαμβάνει αυτή τη συζήτηση, μπορώ να χρησιμοποιήσω όσα εμφανίζονται εδώ. Αν δεν περιλαμβάνεται, ξεκίνα με μία γραμμή: «Είχα συνέντευξη για ταμίας σε σούπερ μάρκετ· πριν δούλευα σε καφετέρια που έκλεισε.» Καλή επιτυχία αύριο.',
'v4_I00_06': 'Στο πλαίσιο που μου δόθηκε εδώ δεν υπάρχει η προηγούμενη συνταγή, άρα δεν μπορώ να ξέρω τι ακριβώς έγινε. Οι συχνότερες αιτίες για νερουλό μουσακά είναι υγρά από τις μελιτζάνες, κιμάς που δεν έδεσε αρκετά ή κόψιμο αμέσως μόλις βγήκε από τον φούρνο. Αν επικολλήσεις τη συνταγή και πεις τι έκανες σε αυτά τα τρία σημεία, μπορούμε να εντοπίσουμε την πιθανότερη αιτία.',
'v4_I00_07': 'Αν αύριο το πλαίσιο περιλαμβάνει αυτή τη συζήτηση, μπορώ να χρησιμοποιήσω τις πέντε λέξεις που εμφανίζονται εδώ. Αν όχι, γράψε στο πρώτο μήνυμα «Κάνε μου τεστ σε boarding pass, gate, check-in, delay, baggage claim» και ξεκινάμε αμέσως.',
'v4_I00_08': 'Μέσοι όροι:\n- Α.Κ.: 16\n- Δ.Μ.: 13\n- Ε.Π.: 19\n- Γ.Σ.: 12,3 (37/3)\n\nΔεν μπορώ να συμπεράνω από εδώ αν η εφαρμογή θα διατηρήσει τους βαθμούς ως τον άλλο μήνα. Κράτησέ τους σε υπολογιστικό φύλλο ή αρχείο κειμένου και τότε δώσε μου τους παλιούς μαζί με τους νέους για να υπολογίσουμε και τη διαφορά.',
'v4_I00_09': 'Για κάτι πρακτικό: ένα κουτί οργάνωσης για αγκίστρια, βαρίδια και τεχνητά δολώματα, ένα πτυσσόμενο καρεκλάκι ή ένα ισοθερμικό τσαντάκι για τις ώρες στην ακτή. Αν ψαρεύει και βράδυ, ένας φακός κεφαλής θα του φανεί χρήσιμος. Για κάτι μεγαλύτερο, ένα καινούργιο μηχανάκι για το καλάμι του, αφού μάθεις πρώτα ποιο καλάμι έχει, ή μια μέρα ψάρεμα με καΐκι, οι δυο σας.\n\nΣτο τρέχον πλαίσιο θα γράφω χωρίς κουκκίδες. Σε επόμενο πλαίσιο, γράψε «χωρίς κουκκίδες» αν αυτή η προτίμηση δεν εμφανίζεται ήδη εκεί.',
'v4_I00_10': 'Δεν μπορώ να εγγυηθώ ποιος έχει πρόσβαση στη συνομιλία ή τι αποθηκεύει η υπηρεσία· αυτό πρέπει να το ελέγξεις στην πολιτική απορρήτου και στις ρυθμίσεις του παρόχου. Αν θέλεις να μιλήσουμε, μπορείς να ξεκινήσεις χωρίς ονόματα ή άλλα στοιχεία που σε ταυτοποιούν και να γράψεις μόνο όσα νιώθεις ασφαλής να μοιραστείς. Αν υπάρχει άμεσος κίνδυνος για σένα, επικοινώνησε τώρα με άνθρωπο που εμπιστεύεσαι ή με τις υπηρεσίες έκτακτης ανάγκης.',
'v4_I00_11': 'Δεν μπορώ να εγγυηθώ ότι η υπηρεσία θα φυλάξει με ασφάλεια ή θα θυμάται αυτόν τον κωδικό. Επειδή τον αποκάλυψες σε συνομιλία, άλλαξέ τον τώρα από την επίσημη εφαρμογή ή τον ιστότοπο της τράπεζας. Φύλαξε τον νέο σε διαχειριστή κωδικών και μην τον ξαναστείλεις σε μήνυμα.',
'v4_I01_03': 'Το περιεχόμενο του συμφωνητικού δεν έχει δοθεί εδώ σε αναγνώσιμη μορφή. Επικολλήστε τους όρους και θα επισημάνω όσα φαίνονται ασυνήθιστα ή σας επιβαρύνουν, ιδίως για διάρκεια, αναπροσαρμογή μισθώματος, εγγύηση και πρόωρη αποχώρηση. Για όρο που μπορεί να επηρεάσει τα δικαιώματά σας, ζητήστε έλεγχο από δικηγόρο πριν υπογράψετε.',
'v4_I01_04': 'Εδώ εμφανίζεται μόνο το «Σ’ το επισύναψα», όχι το περιεχόμενο του email σε αναγνώσιμη μορφή. Αντίγραψε και επικόλλησε το κείμενο και θα το μεταφράσω στα αγγλικά σε ύφος κατάλληλο για προϊστάμενο.',
'v4_I01_05': 'Εδώ έχει δοθεί μόνο το όνομα «αναφορα_τριμηνου_Γ.docx», όχι το περιεχόμενο του αρχείου σε αναγνώσιμη μορφή. Επικόλλησε το κείμενο της αναφοράς και θα σημειώσω τι θέλει διόρθωση, τι είναι ασαφές και τι μπορεί να κοπεί.',
'v4_I01_06': 'Η φωτογραφία του μενού δεν έχει δοθεί εδώ ως αναγνώσιμο περιεχόμενο. Γράψε τα ονόματα των φαγητών όπως τα βλέπεις, ακόμη και με λατινικά γράμματα, και θα σου εξηγήσω με απλά λόγια τι είναι το καθένα.',
'v4_I01_07': 'Το screenshot δεν έχει δοθεί εδώ ως αναγνώσιμο κείμενο. Αντίγραψε από το τερματικό το μήνυμα σφάλματος, μαζί με την εντολή που έτρεξες και λίγες γραμμές πριν από το σφάλμα, και θα εξετάσω από πού μπορεί να προέρχεται.',
'v4_I01_10': 'Η φωτογραφία δεν έχει δοθεί εδώ ως αναγνώσιμο περιεχόμενο. Γράψε τα υλικά και τις ποσότητες όπως είναι στο τετράδιο. Αν δεν λέει για πόσους είναι, γράψε και πόσες ντομάτες και πιπεριές γεμίζει, ώστε να υπολογίσουμε τις αναλογίες για 8 άτομα.',
'v4_I01_11': 'Δεν έχει δοθεί εδώ αποτέλεσμα ανοίγματος του συνδέσμου, οπότε από τη διεύθυνση βλέπω μόνο τον τίτλο του άρθρου. Επικόλλησε τους επτά τρόπους ή το κείμενο και θα εξηγήσω ποιοι στέκουν και ποιοι πιθανότατα κάνουν μικρή διαφορά στον λογαριασμό.',
'v4_I02_07': 'Ως γλωσσικό μοντέλο δεν έχω δικό μου σώμα. Μπορώ να λειτουργώ μέσα σε εφαρμογές που ίσως συνδέονται με εργαλεία ή συσκευές, αλλά από όσα μου έχουν δοθεί εδώ δεν προκύπτει ότι ελέγχω κάποιο ρομπότ.'
}

patch=[]
for rid in deployment_ids:
    current=consolidated[rid]
    if rid in new_answers:
        answer=new_answers[rid]; reused=False
    else:
        answer=drafts[rid]['candidate_last_answer']; reused=True
        if '[' in answer and 'κρατήστε το ήδη' in answer:
            raise AssertionError('placeholder draft was not replaced: '+rid)
    candidate=json.loads(json.dumps(current,ensure_ascii=False))
    before=candidate['messages'][-1]['content']
    assert candidate['messages'][-1]['role']=='assistant'
    candidate['messages'][-1]['content']=answer
    sid=rid.removeprefix('v4_'); src=source[sid]
    patch.append({'row_id':rid,'status':'accepted_candidate','operation':'replace_existing_row','candidate_row':candidate,
      'change':{'kind':'last_assistant_rewrite','before':before,'after':answer},
      'source_identity':{'consolidated_path':str(CONSOLIDATED),'consolidated_record_sha256':csha(current),'generator_source_path':str(V4_FINAL),'generator_source_id':sid,'generator_record_sha256':csha(src),'generator_provenance':{'gen_model':src.get('gen_model'),'edited_by':src.get('edited_by')}},
      'repair_provenance':{'author':'if_audit_agent','method':'source-grounded manual rewrite','date':'2026-09-13','reused_prior_draft':reused}})

for rid in closure_ids:
    d=drafts[rid]; src=d['candidate']; sid=rid.removeprefix('v4_')
    candidate={'id':rid,'messages':src['messages'],'category':src['category'],'version':'v4','holdout':False}
    present={name:data['six_structural_cases'][rid] for name,data in assembly['results'].items()}
    assert all(v==0 for v in present.values())
    patch.append({'row_id':rid,'status':'accepted_candidate','operation':'add_new_coverage_row','candidate_row':candidate,
      'change':{'kind':'restore_missing_supervised_closure','not_historical_training_corruption':True,'actual_assembly_occurrences':present},
      'source_identity':{'consolidated_path':str(CONSOLIDATED),'incomplete_source_record_sha256':csha(consolidated[rid]),'conversation_source':d['provenance']['conversation'],'assistant_close_source':d['provenance']['assistant_close'],'generator_source_id':sid,'generator_provenance':{'gen_model':src.get('gen_model')}},
      'repair_provenance':{'author':'if_audit_agent','method':'reconstruct original user turn and append already-reviewed close','date':'2026-09-13','reused_prior_draft':True}})

patch.sort(key=lambda r:r['row_id'])
(OUT/'deployment_and_closure_patch.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in patch))

fact_answers={
'A14_09':'Ναι. Για τους εκλογικούς καταλόγους ως ημερομηνία γέννησης θεωρείται η 1η Ιανουαρίου του έτους γέννησης, οπότε ψηφίζουν όσοι συμπληρώνουν τα 17 μέσα στο έτος των εκλογών, ακόμη κι αν η ψηφοφορία γίνει πριν από τα γενέθλιά τους. Η εγγραφή γίνεται αυτεπάγγελτα από τον δήμο με βάση το δημοτολόγιο. Πριν από τις εκλογές, ελέγξτε την εγγραφή και το εκλογικό τμήμα στην επίσημη υπηρεσία «Μάθε πού ψηφίζω».',
'A21_21':'Η Ελλάδα έχει 21 έδρες στο Ευρωπαϊκό Κοινοβούλιο. Η μείωση από 22 σε 21 ίσχυσε για τις ευρωεκλογές του 2014, και η επίσημη τρέχουσα σελίδα του Ευρωπαϊκού Κοινοβουλίου εξακολουθεί να εμφανίζει 21 Έλληνες ευρωβουλευτές. Για δημοσίευση, γράψτε «21 έδρες από τις ευρωεκλογές του 2014» και ελέγξτε ξανά την τρέχουσα κατανομή στην επίσημη σελίδα του Κοινοβουλίου.',
'F05_03':'Δεν μπορώ να ξέρω γιατί ο συγκεκριμένος άνθρωπος άλλαξε θέμα. Ένα πιθανό πλαίσιο είναι ότι ο Εμφύλιος συνδέθηκε επί δεκαετίες με διώξεις, καταδίκες και πολιτικό διχασμό, οπότε μπορεί να αποτελεί δύσκολη οικογενειακή μνήμη· αυτό είναι ιστορική ερμηνεία, όχι διάγνωση του συγγενή σου. Η ενιαία Εθνική Αντίσταση αναγνωρίστηκε με τον ν. 1285/1982 και ο ν. 1863/1989 επιχείρησε θεσμικά την άρση συνεπειών του Εμφυλίου. Αν θέλεις να τον ξαναρωτήσεις, κάν’ το χωρίς πίεση και άφησέ του χώρο να μη μιλήσει.',
'A02_02':'Το βασικό κείμενο ήταν το Πρωτόκολλο του Λονδίνου της 3ης Φεβρουαρίου 1830, η πρώτη επίσημη διεθνής πράξη που αναγνώρισε την Ελλάδα ως πλήρως ανεξάρτητο κράτος. Το ίδιο πρωτόκολλο όριζε τότε σύνορα από τον Αχελώο ως τον Σπερχειό. Η ευρύτερη γραμμή Άρτας–Βόλου, δηλαδή Αμβρακικού–Παγασητικού, προέκυψε από τον διακανονισμό της Κωνσταντινούπολης και τις τελικές ρυθμίσεις του 1832.',
'A01_22':'Ψηφίσατε για τη μορφή του πολιτεύματος. Στο δημοψήφισμα της 8ης Δεκεμβρίου 1974 το ερώτημα ήταν αν η χώρα θα είχε βασιλευομένη ή αβασίλευτη δημοκρατία. Περίπου το 69% ψήφισε αβασίλευτη δημοκρατία. Το νέο Σύνταγμα ψηφίστηκε από τη Βουλή στις 7 Ιουνίου 1975, υπογράφηκε στις 9 Ιουνίου και δημοσιεύτηκε στις 11 Ιουνίου 1975.',
'G09_09':'Στον γραπτό λόγο κρατάμε πάντα το τελικό -ν στο αρσενικό «τον» και «έναν», καθώς και στην αντωνυμία «αυτόν/τον»: τον δρόμο, έναν φίλο. Στο θηλυκό «την», στην αντωνυμία «αυτήν/την» και στα «δεν», «μην», το κρατάμε όταν η επόμενη λέξη αρχίζει από φωνήεν ή από κ, π, τ, μπ, ντ, γκ, τσ, τζ, ξ, ψ: την Πάτρα, δεν ξέρω, μην πας. Πριν από τα άλλα σύμφωνα συνήθως πέφτει: τη Θεσσαλονίκη, δε θέλω, μη γράψεις. Μνημονικό: κ-π-τ, τα δίψηφά τους, τσ-τζ και ξ-ψ.',
'A12_20':'Ο πιο ασφαλής τρόπος είναι στο myAADE: στην ενότητα «Μητρώο & Επικοινωνία» μπορείς να δεις τα στοιχεία φυσικού προσώπου ή να εκδώσεις βεβαίωση μητρώου που περιλαμβάνει τον ΑΦΜ σου. Ο ΑΦΜ εμφανίζεται επίσης στο εκκαθαριστικό σου. Μια συνηθισμένη απόδειξη λιανικής αναγράφει υποχρεωτικά τον ΑΦΜ του πωλητή, όχι τον δικό σου, οπότε μην βασιστείς σε αυτήν. Αν δεν έχεις πρόσβαση στους κωδικούς σου, απευθύνσου στην ΑΑΔΕ ή στη ΔΟΥ με ταυτοποίηση.'}

evidence={
'A14_09':[('https://www.ypes.gr/?ptype=faqs','Υπουργείο Εσωτερικών','current official FAQ: 17th year, January 1 age convention, automatic municipal-list preparation')],
'A21_21':[('https://www.europarl.europa.eu/news/el/press-room/20130610IPR11414/elections-2014-share-out-of-meps-seats-among-28-eu-countries','European Parliament','official 2014 allocation: Greece 22 to 21'),('https://www.europarl.europa.eu/meps/en/search/advanced?countryCode=GR','European Parliament','current official roster returns 21')],
'F05_03':[('https://www.hellenicparliament.gr/Praktika/Synedriaseis-Olomeleias?sessionRecord=49d5e017-bb54-4ff5-9028-77483f53964d','Hellenic Parliament','official parliamentary record explicitly dates recognition to Law 1285/1982'),('https://www.hellenicparliament.gr/UserFiles/c0d5184d-7550-4265-8e0b-078e1bc7375a/12106766.pdf','Hellenic Parliament','official parliamentary record identifies Law 1863/1989 as the law on lifting the consequences of the 1944-1949 Civil War'),('https://www.hellenicparliament.gr/UserFiles/c0d5184d-7550-4265-8e0b-078e1bc7375a/11328128.pdf','Hellenic Parliament','official parliamentary question documents the postwar public-employment loyalty regime and its repeal'),('https://www.e-nomothesia.gr/kat-nomothesia-genikou-endiapherontos/n-1285-1982.html','FEK A 115/1982 legal text mirror','secondary cross-check of Law 1285/1982'),('https://www.e-nomothesia.gr/suntaksiodotika/nomos-1863-1989-fek-204a-18-11-1989.html','FEK A 204/1989 legal text mirror','secondary cross-check of Law 1863/1989')],
'A02_02':[('https://200years.mfa.gr/en/international-treaties-en/','Hellenic Ministry of Foreign Affairs diplomatic archive','1830 independence and Acheloos-Spercheios boundary; 1832 Constantinople/Arta-Volos settlement')],
'A01_22':[('https://www.hellenicparliament.gr/UserFiles/8c3e9046-78fb-48f4-bd82-bbba28ca1ef5/SYNTAGMATA.PDF','Hellenic Parliament','official constitutional history: adoption 7 June and subsequent promulgation'),('https://www.presidency.gr/chairetismos-toy-proedroy-tis-dimokratias-konstantinoy-an-tasoyla-sta-egkainia-tis-ekthesis-to-diko-mas-syntagma-1975-2025-sti-voyli-ton-ellinon/','Presidency of the Hellenic Republic','official chronology: voted 7 June, signed 9 June, published 11 June 1975'),('https://foundation.parliament.gr/el/ekthesi/dimopsifisma','Hellenic Parliament Foundation','official exhibit: referendum date and 69.18 percent result for the republic')],
'G09_09':[('https://www.ebooks.edu.gr/ebooks/v/html/8547/2009/Grammatiki_E-ST-Dimotikou_html-apli/index_B4e.html','Greek Ministry education textbook portal','school final-n rule, including always retaining masculine τον/έναν and the conditional forms την/δεν/μην'),('https://ebooks.edu.gr/ebooks/d/8547/636/10-0138-02_Grammatiki_E-ST-Dimotikou.pdf','Greek Ministry education textbook portal','official school grammar PDF version of the final-n rule')],
'A12_20':[('https://www.aade.gr/sites/default/files/2026-01/odigos%20diadikasion_january%202026.pdf','AADE','official registry guide: issue current registry certificate via myAADE'),('https://elib.aade.gr/elib/printview?d=%2Fgr%2Fact%2F2014%2F4308%2Fmain%2Fchp%2F3%2F','AADE legal library','retail receipt mandatory AFM is the seller’s')]
}
facts=[]
for rid,answer in fact_answers.items():
    current=consolidated[rid]; candidate=json.loads(json.dumps(current,ensure_ascii=False)); before=candidate['messages'][-1]['content']; candidate['messages'][-1]['content']=answer
    facts.append({'row_id':rid,'status':'accepted_source_grounded_candidate','candidate_row':candidate,'change':{'before':before,'after':answer},'source_identity':{'path':str(CONSOLIDATED),'record_sha256':csha(current)},'repair_provenance':{'author':'if_audit_agent','date':'2026-09-13','method':'manual correction after primary-source review'},'evidence':[{'url':u,'publisher':pub,'supports':supports,'checked':'2026-09-13'} for u,pub,supports in evidence[rid]]})
(OUT/'world_fact_verification.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in facts))
(OUT/'source_evidence.json').write_text(json.dumps({rid:[{'url':u,'publisher':pub,'supports':supports,'checked':'2026-09-13'} for u,pub,supports in items] for rid,items in evidence.items()},ensure_ascii=False,indent=2)+'\n')

output_names=['deployment_and_closure_patch.jsonl','world_fact_verification.jsonl','source_evidence.json','build_closure.py']
if (OUT/'closure_report.md').exists(): output_names.append('closure_report.md')
manifest={'date':'2026-09-13','status':'review_candidates_not_applied','counts':{'deployment_replacements':len(deployment_ids),'new_coverage_closures':len(closure_ids),'patch_accepted':len(patch),'patch_held':0,'world_facts_accepted':len(facts),'world_facts_held':0,'prior_drafts_reused':sum(r['repair_provenance']['reused_prior_draft'] for r in patch),'prior_drafts_replaced_or_new':sum(not r['repair_provenance']['reused_prior_draft'] for r in patch)},'ids':{'deployment':deployment_ids,'new_coverage':closure_ids,'world_facts':list(fact_answers)},'inputs':{str(p):fsha(p) for p in [CONSOLIDATED,V4_FINAL,OLD,AUDIT,ASSEMBLY]},'outputs':{name:fsha(OUT/name) for name in output_names}}
(OUT/'closure_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
