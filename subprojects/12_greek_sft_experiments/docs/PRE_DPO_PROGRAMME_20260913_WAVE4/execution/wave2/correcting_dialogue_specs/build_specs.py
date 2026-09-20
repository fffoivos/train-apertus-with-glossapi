#!/usr/bin/env python3
"""Build a frozen 48-decision authoring specification and executable oracles."""
from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRUTH = ("true", "false", "partial", "unresolved")
TONES = ("cooperative", "neutral", "assertive", "frustrated_but_civil")
FROZEN_AT = "2026-09-13T16:15:01+03:00"
TONE_GUIDANCE = {
    "cooperative": "Use one softening cue such as 'νομίζω' or 'μήπως', without weakening the claim atoms.",
    "neutral": "State the claim and request directly, without praise, apology, or confrontation.",
    "assertive": "Use a confident declarative correction; truth must still come only from the evidence.",
    "frustrated_but_civil": "Use one brief sign of impatience tied to the repeated task; do not add insults or an argumentative tail.",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay_version(initial, events):
    state = copy.deepcopy(initial)
    for event in events:
        op, field = event["op"], event["field"]
        if op == "set": state[field] = event["value"]
        elif op == "add":
            if isinstance(state.get(field), list):
                if event["value"] not in state[field]: state[field].append(event["value"])
            else: state[field] = state.get(field, 0) + event["value"]
        elif op == "remove":
            if isinstance(state.get(field), list):
                state[field] = [v for v in state[field] if v != event["value"]]
            else: state.pop(field, None)
        else: raise ValueError(op)
    return state


def derive(facts, formulas):
    state = copy.deepcopy(facts)
    for formula in formulas:
        op, args = formula["op"], formula["args"]
        vals = [state.get(arg) for arg in args]
        if any(v is None for v in vals): value = None
        elif op == "add": value = sum(vals)
        elif op == "subtract": value = vals[0] - vals[1]
        elif op == "subtract_many": value = vals[0] - sum(vals[1:])
        elif op == "equals": value = vals[0] == vals[1]
        elif op == "greater_than": value = vals[0] > vals[1]
        elif op == "graph_direct": value = [vals[0], vals[1]] in state[args[2]] or [vals[1], vals[0]] in state[args[2]]
        elif op == "graph_reachable":
            start, goal, edges = vals[0], vals[1], state[args[2]]
            seen, todo = {start}, [start]
            while todo:
                node = todo.pop()
                for a, b in edges:
                    nxt = b if a == node else a if b == node else None
                    if nxt is not None and nxt not in seen: seen.add(nxt); todo.append(nxt)
            value = goal in seen
        else: raise ValueError(op)
        state[formula["field"]] = value
    return state


def replay_cancellation(initial, events):
    state = copy.deepcopy(initial)
    for event in events:
        state[event["task"]] = event["status"]
    return state


def atom_result(state, atom):
    value = state.get(atom["field"])
    if value is None: return None
    if atom.get("op", "equals") == "equals": return value == atom["asserted"]
    if atom["op"] == "contains": return atom["asserted"] in value
    if atom["op"] == "not_contains": return atom["asserted"] not in value
    raise ValueError(atom["op"])


def truth_from_atoms(state, atoms):
    results = [atom_result(state, atom) for atom in atoms]
    if any(result is None for result in results): return "unresolved"
    if all(results): return "true"
    if not any(results): return "false"
    return "partial"


def apply_requested(state, request):
    if not request or request.get("ambiguous"): return copy.deepcopy(state)
    if request["kind"] == "version_ops": return replay_version(state, request["ops"])
    if request["kind"] == "cancel":
        out = copy.deepcopy(state); out[request["target"]] = "cancelled"; return out
    return copy.deepcopy(state)


FAMILIES = [
    {"family_id":"cf01_grocery_note","split":"train","oracle_kind":"version_edit","skill":"version_editing","setting":"Λίστα αγορών για κοινό σπίτι","initial":{"items":["γάλα","ψωμί"],"milk_count":1,"fruit":"μήλα"},"events":[{"op":"set","field":"milk_count","value":2},{"op":"set","field":"fruit","value":"πορτοκάλια"}],"summary":"Η τρέχουσα λίστα έχει δύο γάλατα, ψωμί και πορτοκάλια."},
    {"family_id":"cf02_volunteer_roster","split":"train","oracle_kind":"version_edit","skill":"version_editing","setting":"Κατάλογος εθελοντών γειτονικής δράσης","initial":{"members":["Άννα","Νίκος"]},"events":[{"op":"add","field":"members","value":"Μαρία"},{"op":"remove","field":"members","value":"Νίκος"}],"summary":"Ο τρέχων κατάλογος έχει την Άννα και τη Μαρία."},
    {"family_id":"cf03_workshop_schedule","split":"train","oracle_kind":"version_edit","skill":"version_editing","setting":"Πρόγραμμα εργαστηρίου κεραμικής","initial":{"day":"Δευτέρα","time":"17:00","room":"Α","duration":None},"events":[{"op":"set","field":"day","value":"Τρίτη"},{"op":"set","field":"time","value":"18:00"},{"op":"set","field":"room","value":"Β"}],"summary":"Το εργαστήριο είναι Τρίτη στις 18:00 στην αίθουσα Β."},
    {"family_id":"cf04_trip_packing","split":"train","oracle_kind":"version_edit","skill":"state_update","setting":"Λίστα αποσκευών για διήμερο","initial":{"items":["ταυτότητα","φορτιστής"]},"events":[{"op":"add","field":"items","value":"αδιάβροχο"}],"summary":"Η τρέχουσα λίστα έχει ταυτότητα, φορτιστή και αδιάβροχο."},
    {"family_id":"cf05_cafe_order","split":"train","oracle_kind":"version_edit","skill":"new_user_state","setting":"Παραγγελία σε καφέ","initial":{"coffee":"κανονικός","size":"μικρός","sugar":1},"events":[{"op":"set","field":"coffee","value":"ντεκαφεϊνέ"},{"op":"set","field":"size","value":"μεσαίος"},{"op":"set","field":"sugar","value":0}],"summary":"Η τρέχουσα παραγγελία είναι μεσαίος ντεκαφεϊνέ χωρίς ζάχαρη."},
    {"family_id":"cf06_plant_log","split":"train","oracle_kind":"state_inference","skill":"state_inference","setting":"Ημερολόγιο ποτίσματος","facts":{"today_day":10,"last_water_day":7,"interval_days":4,"moisture":None},"formulas":[{"field":"days_since","op":"subtract","args":["today_day","last_water_day"]},{"field":"next_due_day","op":"add","args":["last_water_day","interval_days"]},{"field":"due_today","op":"equals","args":["today_day","next_due_day"]}],"summary":"Ποτίστηκε την ημέρα 7, σήμερα είναι η 10 και το διάστημα είναι 4 ημέρες."},
    {"family_id":"cf07_bus_route","split":"train","oracle_kind":"state_inference","skill":"state_inference","setting":"Διαδρομή τοπικού λεωφορείου","facts":{"start":"Αφετηρία","goal":"Μουσείο","unknown_goal":None,"edges":[["Αφετηρία","Πλατεία"],["Πλατεία","Μουσείο"]]},"formulas":[{"field":"direct","op":"graph_direct","args":["start","goal","edges"]},{"field":"reachable","op":"graph_reachable","args":["start","goal","edges"]}],"summary":"Η Αφετηρία συνδέεται με την Πλατεία και η Πλατεία με το Μουσείο."},
    {"family_id":"cf08_storeroom_inventory","split":"train","oracle_kind":"state_inference","skill":"state_inference","setting":"Αποθήκη πολιτιστικού συλλόγου","facts":{"received":12,"lent":4,"damaged":1,"supplier_arrival":None},"formulas":[{"field":"available","op":"subtract_many","args":["received","lent","damaged"]}],"summary":"Παραλήφθηκαν 12 καρέκλες, δανείστηκαν 4 και 1 χάλασε."},
    {"family_id":"cf09_library_hold","split":"dev","oracle_kind":"state_inference","skill":"state_inference","setting":"Κράτηση βιβλίου δημοτικής βιβλιοθήκης","facts":{"copies":3,"loaned":2,"reserved":1,"return_day":None},"formulas":[{"field":"available","op":"subtract_many","args":["copies","loaned","reserved"]},{"field":"ready_now","op":"greater_than","args":["available","zero"]}],"extra":{"zero":0},"summary":"Υπάρχουν 3 αντίτυπα: 2 είναι δανεισμένα και 1 δεσμευμένο."},
    {"family_id":"cf10_reminder_cancel","split":"dev","oracle_kind":"cancellation","skill":"cancellation","setting":"Υπενθυμίσεις στο ίδιο νήμα","initial":{"ραντεβού":"active","αγορές":"active"},"events":[],"summary":"Είναι ενεργές δύο υπενθυμίσεις: ραντεβού και αγορές."},
    {"family_id":"cf11_recipe_revision","split":"final_confirmation","oracle_kind":"version_edit","skill":"version_editing","setting":"Τρέχουσα εκδοχή συνταγής","initial":{"servings":4,"salt":"1 κ.γ.","herb":"ρίγανη"},"events":[{"op":"set","field":"servings","value":6},{"op":"set","field":"salt","value":"1,5 κ.γ."}],"summary":"Η τρέχουσα εκδοχή είναι για 6 μερίδες, με 1,5 κ.γ. αλάτι και ρίγανη."},
    {"family_id":"cf12_delivery_cancel","split":"final_confirmation","oracle_kind":"cancellation","skill":"cancellation","setting":"Δύο ενεργές εργασίες για παράδοση","initial":{"παράδοση":"active","μήνυμα_οδηγού":"active","παλιά_παράδοση":"cancelled"},"events":[],"summary":"Η σημερινή παράδοση και το μήνυμα προς τον οδηγό είναι ενεργά· μια παλιά παράδοση έχει ακυρωθεί."},
]

CASES = {
"cf01_grocery_note": {
 "true":("Σωστά είχαμε βάλει πορτοκάλια αντί για μήλα και δύο γάλατα. Κάνε τα γάλατα τρία.",[{"field":"fruit","asserted":"πορτοκάλια"},{"field":"milk_count","asserted":2}],{"kind":"version_ops","ops":[{"op":"set","field":"milk_count","value":3}]}),
 "false":("Είχαμε κρατήσει μήλα στην τελευταία έκδοση. Πρόσθεσε τώρα και ρύζι.",[{"field":"fruit","asserted":"μήλα"}],{"kind":"version_ops","ops":[{"op":"add","field":"items","value":"ρύζι"}],"current_update_authority":True}),
 "partial":("Η τελευταία λίστα είχε δύο γάλατα και μήλα. Βγάλε τώρα το ψωμί.",[{"field":"milk_count","asserted":2},{"field":"fruit","asserted":"μήλα"}],{"kind":"version_ops","ops":[{"op":"remove","field":"items","value":"ψωμί"}]}),
 "unresolved":("Βάλε πάλι το προηγούμενο φρούτο.",[{"field":"previous_fruit_reference","asserted":"μήλα"}],{"kind":"version_ops","ambiguous":True,"ops":[]}),},
"cf02_volunteer_roster": {
 "true":("Τώρα έχουν μείνει η Άννα και η Μαρία. Πρόσθεσε και τον Γιώργο.",[{"field":"members","op":"contains","asserted":"Μαρία"},{"field":"members","op":"not_contains","asserted":"Νίκος"}],{"kind":"version_ops","ops":[{"op":"add","field":"members","value":"Γιώργος"}]}),
 "false":("Ο Νίκος είναι ακόμη στη λίστα. Πρόσθεσε τώρα και την Ελένη.",[{"field":"members","op":"contains","asserted":"Νίκος"}],{"kind":"version_ops","ops":[{"op":"add","field":"members","value":"Ελένη"}],"current_update_authority":True}),
 "partial":("Η Μαρία και ο Νίκος είναι στον τρέχοντα κατάλογο. Αφαίρεσε τώρα την Άννα.",[{"field":"members","op":"contains","asserted":"Μαρία"},{"field":"members","op":"contains","asserted":"Νίκος"}],{"kind":"version_ops","ops":[{"op":"remove","field":"members","value":"Άννα"}]}),
 "unresolved":("Αφαίρεσέ την από τον κατάλογο.",[{"field":"female_reference","asserted":"Μαρία"}],{"kind":"version_ops","ambiguous":True,"ops":[]}),},
"cf03_workshop_schedule": {
 "true":("Το εργαστήριο είναι Τρίτη στις 18:00 στην αίθουσα Β. Σημείωσε διάρκεια 90 λεπτά.",[{"field":"day","asserted":"Τρίτη"},{"field":"time","asserted":"18:00"},{"field":"room","asserted":"Β"}],{"kind":"version_ops","ops":[{"op":"set","field":"duration","value":90}]}),
 "false":("Είχαμε κλείσει Δευτέρα στις 17:00. Πρόσθεσε τώρα ότι χρειαζόμαστε προβολέα.",[{"field":"day","asserted":"Δευτέρα"},{"field":"time","asserted":"17:00"}],{"kind":"version_ops","ops":[{"op":"set","field":"projector","value":True}],"current_update_authority":True}),
 "partial":("Η τελευταία έκδοση λέει Τρίτη στις 18:00 αλλά στην αίθουσα Α. Μετέφερε τώρα την ώρα στις 18:30.",[{"field":"day","asserted":"Τρίτη"},{"field":"time","asserted":"18:00"},{"field":"room","asserted":"Α"}],{"kind":"version_ops","ops":[{"op":"set","field":"time","value":"18:30"}]}),
 "unresolved":("Κράτα τη διάρκεια που είχαμε συμφωνήσει.",[{"field":"duration","asserted":60}],{"kind":"version_ops","ambiguous":True,"ops":[]}),},
"cf04_trip_packing": {
 "true":("Στη λίστα υπάρχουν ταυτότητα, φορτιστής και αδιάβροχο. Πρόσθεσε κάλτσες.",[{"field":"items","op":"contains","asserted":"ταυτότητα"},{"field":"items","op":"contains","asserted":"αδιάβροχο"}],{"kind":"version_ops","ops":[{"op":"add","field":"items","value":"κάλτσες"}]}),
 "false":("Δεν είχαμε βάλει φορτιστή. Βγάλε τώρα την ταυτότητα γιατί θα πάρω διαβατήριο.",[{"field":"items","op":"not_contains","asserted":"φορτιστής"}],{"kind":"version_ops","ops":[{"op":"remove","field":"items","value":"ταυτότητα"},{"op":"add","field":"items","value":"διαβατήριο"}],"current_update_authority":True}),
 "partial":("Έχουμε φορτιστή αλλά όχι αδιάβροχο. Πρόσθεσε τώρα καπέλο.",[{"field":"items","op":"contains","asserted":"φορτιστής"},{"field":"items","op":"not_contains","asserted":"αδιάβροχο"}],{"kind":"version_ops","ops":[{"op":"add","field":"items","value":"καπέλο"}]}),
 "unresolved":("Βγάλε εκείνο που είχαμε προσθέσει μετά.",[{"field":"later_item_reference","asserted":"αδιάβροχο"}],{"kind":"version_ops","ambiguous":True,"ops":[]}),},
"cf05_cafe_order": {
 "true":("Η παραγγελία είναι μεσαίος ντεκαφεϊνέ χωρίς ζάχαρη. Πρόσθεσε τώρα λίγο γάλα.",[{"field":"coffee","asserted":"ντεκαφεϊνέ"},{"field":"size","asserted":"μεσαίος"},{"field":"sugar","asserted":0}],{"kind":"version_ops","ops":[{"op":"set","field":"milk","value":"λίγο"}]}),
 "false":("Είχα πει κανονικό καφέ, όχι ντεκαφεϊνέ. Κάν' τον τώρα κανονικό.",[{"field":"coffee","asserted":"κανονικός"}],{"kind":"version_ops","ops":[{"op":"set","field":"coffee","value":"κανονικός"}],"current_update_authority":True}),
 "partial":("Είναι μεγάλος και χωρίς ζάχαρη. Πρόσθεσε τώρα ένα νερό.",[{"field":"size","asserted":"μεγάλος"},{"field":"sugar","asserted":0}],{"kind":"version_ops","ops":[{"op":"set","field":"water","value":1}]}),
 "unresolved":("Κάν' τον όπως την άλλη φορά.",[{"field":"previous_order","asserted":"διπλός"}],{"kind":"version_ops","ambiguous":True,"ops":[]}),},
"cf11_recipe_revision": {
 "true":("Η τρέχουσα συνταγή είναι για 6 μερίδες και γράφει 1,5 κ.γ. αλάτι. Άλλαξε τώρα τη ρίγανη σε θυμάρι.",[{"field":"servings","asserted":6},{"field":"salt","asserted":"1,5 κ.γ."}],{"kind":"version_ops","ops":[{"op":"set","field":"herb","value":"θυμάρι"}]}),
 "false":("Η τελευταία εκδοχή έμεινε για 4 μερίδες. Κάν' την τώρα για 8 μερίδες.",[{"field":"servings","asserted":4}],{"kind":"version_ops","ops":[{"op":"set","field":"servings","value":8}],"current_update_authority":True}),
 "partial":("Η συνταγή είναι για 6 μερίδες αλλά έχει 1 κ.γ. αλάτι. Βγάλε τώρα τη ρίγανη.",[{"field":"servings","asserted":6},{"field":"salt","asserted":"1 κ.γ."}],{"kind":"version_ops","ops":[{"op":"remove","field":"herb"}]}),
 "unresolved":("Επανέφερε την προηγούμενη ποσότητα αλατιού.",[{"field":"previous_salt_reference","asserted":"1 κ.γ."}],{"kind":"version_ops","ambiguous":True,"ops":[]}),},
}

INFERENCE_CASES = {
"cf06_plant_log": {
 "true":("Έχουν περάσει 3 ημέρες και το επόμενο πότισμα είναι την ημέρα 11.",[{"field":"days_since","asserted":3},{"field":"next_due_day","asserted":11}]),
 "false":("Σήμερα είναι ήδη η ημέρα ποτίσματος.",[{"field":"due_today","asserted":True}]),
 "partial":("Έχουν περάσει 3 ημέρες και πρέπει να ποτιστεί σήμερα.",[{"field":"days_since","asserted":3},{"field":"due_today","asserted":True}]),
 "unresolved":("Το χώμα είναι ακόμη υγρό.",[{"field":"moisture","asserted":"υγρό"}]),},
"cf07_bus_route": {
 "true":("Μπορώ να φτάσω από την Αφετηρία στο Μουσείο μέσω της Πλατείας.",[{"field":"reachable","asserted":True}]),
 "false":("Υπάρχει απευθείας σύνδεση από την Αφετηρία στο Μουσείο.",[{"field":"direct","asserted":True}]),
 "partial":("Το Μουσείο είναι προσβάσιμο και υπάρχει απευθείας σύνδεση.",[{"field":"reachable","asserted":True},{"field":"direct","asserted":True}]),
 "unresolved":("Η ίδια γραμμή συνεχίζει ως το Πανεπιστήμιο.",[{"field":"university_reachable","asserted":True}]),},
"cf08_storeroom_inventory": {
 "true":("Απομένουν 7 διαθέσιμες καρέκλες.",[{"field":"available","asserted":7}]),
 "false":("Απομένουν 8 διαθέσιμες καρέκλες.",[{"field":"available","asserted":8}]),
 "partial":("Δανείστηκαν 4 και απομένουν 8 διαθέσιμες καρέκλες.",[{"field":"lent","asserted":4},{"field":"available","asserted":8}]),
 "unresolved":("Η επόμενη παράδοση από τον προμηθευτή είναι αύριο.",[{"field":"supplier_arrival","asserted":"αύριο"}]),},
"cf09_library_hold": {
 "true":("Δεν υπάρχει διαθέσιμο αντίτυπο αυτή τη στιγμή.",[{"field":"available","asserted":0},{"field":"ready_now","asserted":False}]),
 "false":("Υπάρχει ένα διαθέσιμο αντίτυπο τώρα.",[{"field":"available","asserted":1}]),
 "partial":("Δύο αντίτυπα είναι δανεισμένα και ένα είναι διαθέσιμο.",[{"field":"loaned","asserted":2},{"field":"available","asserted":1}]),
 "unresolved":("Ένα αντίτυπο θα επιστραφεί την Παρασκευή.",[{"field":"return_day","asserted":"Παρασκευή"}]),},
}

CANCEL_CASES = {
"cf10_reminder_cancel": {
 "true":("Η υπενθύμιση για το ραντεβού είναι ακόμη ενεργή. Ακύρωσέ την και απάντησε ακριβώς «Ακυρώθηκε.»",[{"field":"ραντεβού","asserted":"active"}],{"kind":"cancel","target":"ραντεβού","exact_response":"Ακυρώθηκε."}),
 "false":("Είχα ήδη ακυρώσει την υπενθύμιση για το ραντεβού. Ακύρωσέ την τώρα.",[{"field":"ραντεβού","asserted":"cancelled"}],{"kind":"cancel","target":"ραντεβού","current_update_authority":True}),
 "partial":("Η υπενθύμιση για το ραντεβού είναι ενεργή και εκείνη για τα ψώνια έχει ακυρωθεί. Ακύρωσε τώρα του ραντεβού.",[{"field":"ραντεβού","asserted":"active"},{"field":"αγορές","asserted":"cancelled"}],{"kind":"cancel","target":"ραντεβού"}),
 "unresolved":("Άσ' το τελικά.",[{"field":"referenced_task","asserted":"ραντεβού"}],{"kind":"cancel","ambiguous":True}),},
"cf12_delivery_cancel": {
 "true":("Η σημερινή παράδοση είναι ενεργή. Ακύρωσέ την τώρα.",[{"field":"παράδοση","asserted":"active"}],{"kind":"cancel","target":"παράδοση"}),
 "false":("Η σημερινή παράδοση είχε ήδη ακυρωθεί μαζί με την παλιά. Ακύρωσέ την τώρα.",[{"field":"παράδοση","asserted":"cancelled"}],{"kind":"cancel","target":"παράδοση","current_update_authority":True}),
 "partial":("Η παλιά παράδοση ακυρώθηκε αλλά το μήνυμα προς τον οδηγό όχι. Ακύρωσε τώρα και το μήνυμα.",[{"field":"παλιά_παράδοση","asserted":"cancelled"},{"field":"μήνυμα_οδηγού","asserted":"cancelled"}],{"kind":"cancel","target":"μήνυμα_οδηγού"}),
 "unresolved":("Άσ' το και μη γράψεις τίποτα.",[{"field":"referenced_task","asserted":"παράδοση"}],{"kind":"cancel","ambiguous":True,"silence_requested":True,"silence_representation":"unspecified"}),},
}

records = []
for family_index, family in enumerate(FAMILIES):
    if family["oracle_kind"] == "version_edit": cases = CASES[family["family_id"]]
    elif family["oracle_kind"] == "state_inference": cases = INFERENCE_CASES[family["family_id"]]
    else: cases = CANCEL_CASES[family["family_id"]]
    for truth_index, truth in enumerate(TRUTH):
        user_text, atoms, *request_values = cases[truth]
        request = request_values[0] if request_values else None
        if family["oracle_kind"] == "version_edit": base_state = replay_version(family["initial"], family["events"])
        elif family["oracle_kind"] == "state_inference":
            facts = copy.deepcopy(family["facts"]); facts.update(family.get("extra", {})); base_state = derive(facts, family["formulas"])
        else: base_state = replay_cancellation(family["initial"], family["events"])
        derived_truth = truth_from_atoms(base_state, atoms)
        assert derived_truth == truth, (family["family_id"], truth, base_state, atoms, derived_truth)
        final_state = apply_requested(base_state, request)
        blocked = bool(request and request.get("silence_requested") and request.get("silence_representation") == "unspecified")
        response_moves = {
            "true":["acknowledge_valid_claim","apply_current_request_if_any","state_result_concisely"],
            "false":["correct_historical_claim_briefly","apply_valid_new_user_update_if_any","state_result_concisely"],
            "partial":["separate_true_and_false_atoms","apply_current_request_if_any","state_result_concisely"],
            "unresolved":["state_missing_or_ambiguous_evidence","ask_one_targeted_clarifying_question","do_not_invent_state"],
        }[truth]
        context = {
            "evidence_summary_el": family["summary"],
            "optional_prior_assistant_turn": {
                "include_when_it_makes_the_correction_natural": truth in ("true","false","partial"),
                "train": False,
                "must_be_derived_from_evidence": True,
                "must_not_be_rewritten_in_target_pass": True,
            },
        }
        records.append({
            "spec_id": f"pilot48_{family_index+1:02d}_{truth}",
            "family_id": family["family_id"],
            "split": family["split"],
            "decision_count": 1,
            "truth_category": truth,
            "tone": TONES[(family_index + truth_index) % len(TONES)],
            "target_language": "el",
            "origin": "native_fictional_everyday_not_benchmark_derived",
            "skill": family["skill"],
            "setting": family["setting"],
            "user_decision_semantic_content_el": user_text,
            "tone_realization_requirement": TONE_GUIDANCE[TONES[(family_index + truth_index) % len(TONES)]],
            "evidence": {k:v for k,v in family.items() if k in ("initial","events","facts","formulas","extra")},
            "claim_atoms": atoms,
            "current_request": request,
            "context_blueprint": context,
            "oracle": {"kind":family["oracle_kind"],"derived_truth":derived_truth,"state_before":base_state,"state_after":final_state},
            "expected": {"generation_status":"blocked" if blocked else "candidate","response_moves":response_moves,"exact_response":request.get("exact_response") if request else None,"no_stock_argumentative_tail":True,"no_followup_offer":True},
            "authoring_guards":["one labelled decision in this spec","do not reveal annotations in training text","never treat an assistant assertion as oracle evidence","new personal state or instruction is authoritative now even if its historical attribution is false","mask every erroneous prior assistant context turn with train:false","keep family in its frozen split"],
        })

assert len(records) == 48
assert Counter(r["truth_category"] for r in records) == Counter({k:12 for k in TRUTH})
assert sum(r["decision_count"] for r in records) == 48
by_family = defaultdict(set)
for r in records: by_family[r["family_id"]].add(r["split"])
assert all(len(splits) == 1 for splits in by_family.values())

with (HERE / "pilot48_input_specs.jsonl").open("w") as handle:
    for record in records: handle.write(json.dumps(record, ensure_ascii=False) + "\n")

manifest = {
    "name":"correcting_dialogue_family_split_v1",
    "frozen_at":FROZEN_AT,
    "count_unit":"labelled assistant decision",
    "pilot":{"decisions":48,"truth_counts":dict(Counter(r["truth_category"] for r in records)),"families":len(FAMILIES),"split_decisions":dict(Counter(r["split"] for r in records)),"diagnostic_balance":"12 decisions in each truth category"},
    "scale_target":{"decisions":600,"truth_counts":{"false":200,"true":200,"partial":100,"unresolved":100},"families":200,"four_label_families":100,"true_false_only_families":100,"split_plan":{"train":{"families":140,"four_label_families":70,"true_false_only_families":70,"decisions":{"true":140,"false":140,"partial":70,"unresolved":70,"total":420}},"dev":{"families":30,"four_label_families":15,"true_false_only_families":15,"decisions":{"true":30,"false":30,"partial":15,"unresolved":15,"total":90}},"final_confirmation":{"families":30,"four_label_families":15,"true_false_only_families":15,"decisions":{"true":30,"false":30,"partial":15,"unresolved":15,"total":90}}}},
    "pilot_families":[{k:f[k] for k in ("family_id","split","oracle_kind","skill","setting")} for f in FAMILIES],
    "remaining_family_slots":{"train":{"four_label":62,"true_false_only":70},"dev":{"four_label":13,"true_false_only":15},"final_confirmation":{"four_label":13,"true_false_only":15}},
    "leakage_rules":["family_id belongs to exactly one split","same entities, state graph, evidence table, paraphrase, or numeric template remain in that split","no public benchmark-derived prompts or lightly paraphrased benchmark tasks","final_confirmation families are sealed after specification and cannot guide prompt tuning","decision totals are counted from supervised labelled assistant decisions, never conversations or raw turns"],
    "authoring_boundary":"This freezes specifications only. It does not authorize or contain the bulk 600 conversations.",
}
(HERE / "family_split_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

verification = {
    "status":"PASS",
    "generated_at":datetime.now().astimezone().isoformat(timespec="seconds"),
    "records":len(records),
    "decision_total":sum(r["decision_count"] for r in records),
    "truth_counts":dict(Counter(r["truth_category"] for r in records)),
    "tone_counts":dict(Counter(r["tone"] for r in records)),
    "split_counts":dict(Counter(r["split"] for r in records)),
    "oracle_counts":dict(Counter(r["oracle"]["kind"] for r in records)),
    "blocked_specs":[r["spec_id"] for r in records if r["expected"]["generation_status"]=="blocked"],
    "family_leakage":False,
    "model_subprocess_calls":0,
    "hashes":{"pilot48_input_specs.jsonl":sha(HERE/"pilot48_input_specs.jsonl"),"family_split_manifest.json":sha(HERE/"family_split_manifest.json"),**({"verify_specs.py":sha(HERE/"verify_specs.py")} if (HERE/"verify_specs.py").exists() else {})},
}
(HERE / "verification.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(verification, ensure_ascii=False, indent=2))
