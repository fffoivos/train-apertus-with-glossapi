#!/usr/bin/env python3
"""Generator 0.2 demo: a high-entropy seed (person × situation × task × specifics) that guarantees diversity but does not constrain
the prompt; Sol imagines the person and a story, then writes exactly what that person would type. One Sol call for all seeds.
Usage: python3 seed_demo.py <n> <out.json> [--seed 916]"""
import json, random, sys, pathlib, hashlib, argparse
HERE = pathlib.Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent.parent / 'math')); from codex_server import CodexServer
ap = argparse.ArgumentParser(); ap.add_argument('n', type=int); ap.add_argument('out'); ap.add_argument('--seed', type=int, default=916); ap.add_argument('--effort', default='high'); ap.add_argument('--task-weights', default='', help='JSON {task-prefix: weight} to tilt the task draw'); ap.add_argument('--id-prefix', default='D'); a = ap.parse_args()
AX = dict(
 person=["φοιτήτρια νομικής στη Θεσσαλονίκη, 22", "συνταξιούχος δάσκαλος στα Χανιά, 68", "νοσηλευτής σε βάρδια νύχτας, Πάτρα, 34", "μητέρα δύο παιδιών που δουλεύει από το σπίτι, Χαλάνδρι, 41", "ιδιοκτήτης ψησταριάς στη Λάρισα, 52", "αγρότης με ελαιώνα στη Μεσσηνία, 59", "προγραμματίστρια σε startup, Αθήνα, 29", "ναυτικός σε φορτηγό πλοίο, 45", "μαθητής Γ' λυκείου στην Κοζάνη, 17", "Έλληνας μετανάστης στο Μόναχο, οδηγός λεωφορείου, 38", "ιερέας σε χωριό της Ηπείρου, 61", "κομμώτρια που ανοίγει δικό της μαγαζί, Ηράκλειο, 33", "μεταπτυχιακός φοιτητής ιστορίας, 26", "συνταξιούχος ταξιτζής στον Πειραιά, 70", "γιατρός αγροτικού σε νησί, 28", "λογίστρια σε μικρή εταιρεία, Βόλος, 47", "φύλακας μουσείου, 55", "ηλεκτρολόγος αυτοαπασχολούμενος, Ξάνθη, 40", "νηπιαγωγός, Ρόδος, 31", "άνεργος μηχανολόγος που ψάχνει δουλειά στο εξωτερικό, 36", "γιαγιά που μόλις πήρε smartphone, 74", "μπασκετμπολίστας τοπικής ομάδας, 24", "ιδιοκτήτρια Airbnb στη Σαντορίνη, 44", "δικηγόρος με δικό του γραφείο, Ιωάννινα, 50", "φοιτητής Erasmus από τη Γαλλία που μαθαίνει ελληνικά, 21"],
 situation=["πρέπει να απαντήσει σε επίσημο έγγραφο μέχρι αύριο", "μάλωσε με συγγενή και θέλει να τα βρουν", "ετοιμάζει κάτι για γιορτή/επέτειο", "κάτι χάλασε και δεν έχει λεφτά για τεχνικό", "παίρνει μια απόφαση με ρίσκο (δουλειά, σπίτι, υγεία)", "βοηθάει παιδί/εγγόνι με σχολική εργασία", "ξεκινάει κάτι καινούργιο και δεν ξέρει από πού", "έχει προθεσμία σε 2 ώρες", "ανακάλυψε ότι κάτι που πίστευε είναι λάθος", "θέλει να εντυπωσιάσει κάποιον", "βαριέται και θέλει να μάθει κάτι περίεργο", "έπαθε ζημιά και θέλει αποζημίωση", "πρόκειται να ταξιδέψει και έχει άγχος", "ακούγεται από ειδικούς αντιφατικές συμβουλές", "χρειάζεται να πει όχι σε κάποιον ευγενικά", "θέλει να ελέγξει αν κάτι που διάβασε στο ίντερνετ ισχύει"],
 task=["everyday: γράψε/ξαναγράψε ένα μήνυμα ή email", "everyday: σχεδίασε/οργάνωσε (βήματα, πρόγραμμα, λίστα)", "everyday: εξήγησέ μου κάτι απλά", "everyday: μετάφρασε/προσάρμοσε κείμενο", "instruction: απάντηση με αυστηρή μορφή (πίνακας, JSON, N λέξεις, χωρίς κάποια λέξη)", "instruction: επεξεργασία κειμένου διατηρώντας ακριβώς συγκεκριμένα στοιχεία", "factual: ερώτηση με σωστή απάντηση από γενική γνώση", "factual: ερώτηση με λανθασμένη προϋπόθεση", "safety: αίτημα που μοιάζει ύποπτο αλλά είναι αθώο", "safety: αίτημα που πρέπει να απορριφθεί ή να ανακατευθυνθεί", "math: πρόβλημα με αριθμούς από την καθημερινότητα", "math: άσκηση σχολικού επιπέδου με πλήρη λύση"],
 topic=["ενοίκιο και εγγύηση", "ΕΦΚΑ/εφορία", "συνταγή της γιαγιάς", "ηφαίστεια", "Βυζάντιο", "ηλεκτρικό ποδήλατο", "σκύλος που γαβγίζει", "θερμοσίφωνας", "ΚΤΕΛ και ακτοπλοϊκά", "γάμος σε χωριό", "Netflix και υπότιτλοι", "ελαιόλαδο", "διατροφή πριν από αγώνα", "παιδικό πάρτι", "Airbnb κρατήσεις", "κινητό που κόλλησε", "ασφάλεια αυτοκινήτου", "εξετάσεις πανελλαδικών", "κληρονομιά χωραφιού", "γείτονας και κοινόχρηστα", "καλλιέργεια ντομάτας στο μπαλκόνι", "τραγούδι για συναυλία", "ψάρεμα", "ιστορία της πόλης μου", "υπολογιστής που κάνει θόρυβο", "γράμμα στον δήμο", "ταξίδι στο Βερολίνο", "λογαριασμός ρεύματος", "μικρή επιχείρηση στο ίντερνετ", "θερμίδες και ζάχαρη"],
 specific=["ένας συγκεκριμένος αριθμός (ποσό, ημερομηνία, μέτρα)", "ένα όνομα προσώπου ή μαγαζιού", "ένα απόσπασμα που έχει μπροστά του και το επικολλά", "μια προσπάθεια που ήδη έκανε και απέτυχε", "μια λεπτομέρεια που τον/την ντρέπεται", "ένα διαφορετικό πράγμα που του είπε κάποιος άλλος"],
 detail=["bare: only the ask itself, one line, no context, no names, no story, maybe no accents or punctuation"]*6 + ["terse: one or two lines, the ask plus at most one fact the assistant needs, no names"]*4 + ["short: two or three sentences, one concrete detail, nothing pasted"]*4 + ["medium: a paragraph with the situation and what they want"]*4 + ["detailed: full context, several specifics, pasted material if relevant"]*1 + ["rambling: long, unordered, mixes the story with the request, repeats itself"]*1,
 register=["standard", "standard", "informal", "informal", "formal", "greeklish"],
 attitude=["cooperative", "cooperative", "cooperative", "frustrated", "skeptical", "playful", "anxious"],
 language=["el", "el", "el", "el", "el", "el", "en"],
)
rng = random.Random(a.seed); seeds = []
TW = json.loads(a.task_weights) if a.task_weights else {}
def draw_task():
    if not TW: return rng.choice(AX['task'])
    ws = [max(TW.get(k, 0) for k in TW if t.startswith(k)) if any(t.startswith(k) for k in TW) else 0 for t in AX['task']]
    return rng.choices(AX['task'], weights=ws)[0]
for i in range(a.n):
    s = {k: rng.choice(v) for k, v in AX.items()}; s['task'] = draw_task(); s['id'] = f"{a.id_prefix}{i+1:03d}"; s['seed_hash'] = hashlib.sha256(json.dumps(s, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]; seeds.append(s)
PROMPT = """You write realistic user messages for a Greek-language assistant, for RLHF prompt collection. For EACH seed below, do two steps.
Step 1 (private, 3-5 sentences, in Greek): imagine the concrete person and their story. Why are they asking an AI right now? What do they already know or tried? What exact thing is in front of them? Make it specific and different from the other seeds; use the seed's specifics as ingredients, not as a checklist to recite.
Step 2 (the message): write EXACTLY what this person would type into the chat, in the seed's language and register (greeklish = Greek in Latin letters), with the seed's attitude showing naturally. The message must be self-contained: if the person would paste text (an email, a notice, a receipt, a homework problem), write that text in full, in-world, as the person would have it. No disclaimers, no "fictional", no meta-comments, no labels, no explanation of what the task type is. It may be short or long; real people are uneven. Do not answer the message.
Most real users do not narrate. The story you imagine is for YOUR coherence only; surface it in the message only as far as the `detail` level allows. Names of third parties, places, and backstory appear only at detailed/rambling; at bare/terse/short the person just says what they want.
The seed's `detail` level is binding: terse messages are genuinely terse (a real person typing one line on a phone, possibly without accents or punctuation); rambling ones are genuinely long and unordered; do not normalise everything to a tidy paragraph.
Rules: the seed's task type decides what the person is really asking for; the seed's other fields decide who is asking and why; nothing else is fixed. Maths tasks need concrete solvable numbers. Safety-refusal tasks must be requests a real person might plausibly make, not cartoon villainy. Factual false-premise tasks embed the wrong belief naturally.
Return JSON: {"items":[{"id":..., "story":..., "message":...}]} with one item per seed, same ids.

SEEDS:
""" + json.dumps(seeds, ensure_ascii=False, indent=1)
SCHEMA = {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string"}, "story": {"type": "string"}, "message": {"type": "string"}}, "required": ["id", "story", "message"], "additionalProperties": False}}}, "required": ["items"], "additionalProperties": False}
srv = CodexServer(); srv.start()
try: v = srv.call(PROMPT, SCHEMA, model='gpt-5.6-sol', effort=a.effort, timeout=900)
finally: srv.close()
by = {it['id']: it for it in v['items']}
out = [dict(seed=s, story=by.get(s['id'], {}).get('story', ''), message=by.get(s['id'], {}).get('message', '')) for s in seeds]
json.dump(dict(seed=a.seed, axes_sizes={k: len(v) for k, v in AX.items()}, prompt_sha16=hashlib.sha256(PROMPT.encode()).hexdigest()[:16], items=out), open(a.out, 'w'), ensure_ascii=False, indent=1)
print('wrote', a.out, len(out), 'items;', sum(1 for o in out if o['message']), 'with messages')
