#!/usr/bin/env python3
"""Build 60 train-only correcting-dialogue specifications. No generation."""
from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PILOT = ROOT.parent / "balanced_dialogue_pilot/revision2"
LABELS4 = ["true", "false", "partial", "unresolved"]
LABELS2 = ["true", "false"]
TONES = ["cooperative", "neutral", "assertive", "frustrated_but_civil"]
TONE_RULES = {
    "cooperative": "Frame the turn as part of a shared task; vary the wording naturally and use no mandatory politeness prefix.",
    "neutral": "State the claim and task plainly in context, with no fixed opening formula.",
    "assertive": "Use concise, confident wording without hostility and without a fixed template.",
    "frustrated_but_civil": "Show mild task-specific impatience through natural phrasing, without insults or a stock preface.",
}


def canon_sha(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode()).hexdigest()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n" for value in values))


def version_state(evidence: dict[str, Any]) -> dict[str, Any]:
    state = copy.deepcopy(evidence["initial"])
    for event in evidence.get("events", []):
        if event["op"] == "set":
            state[event["field"]] = event["value"]
        elif event["op"] == "add_unique":
            state.setdefault(event["field"], [])
            if event["value"] not in state[event["field"]]:
                state[event["field"]].append(event["value"])
        elif event["op"] == "move_to_end":
            state[event["field"]] = [x for x in state[event["field"]] if x != event["value"]] + [event["value"]]
        elif event["op"] == "move_to_start":
            state[event["field"]] = [event["value"]] + [x for x in state[event["field"]] if x != event["value"]]
        else:
            raise ValueError(event)
    return state


def infer_state(evidence: dict[str, Any]) -> dict[str, Any]:
    state = copy.deepcopy(evidence["facts"])
    state.update(evidence.get("constants", {}))
    for formula in evidence["formulas"]:
        values = [state.get(arg) for arg in formula["args"]]
        if any(value is None for value in values):
            value = None
        elif formula["op"] == "subtract_many":
            value = values[0] - sum(values[1:])
        elif formula["op"] == "weighted_sum":
            value = sum(state[name] * weight for name, weight in formula["terms"])
        elif formula["op"] == "greater_than":
            value = values[0] > values[1]
        elif formula["op"] == "last":
            value = values[0][-1]
        else:
            raise ValueError(formula)
        state[formula["field"]] = value
    return state


def graph_state(evidence: dict[str, Any]) -> dict[str, Any]:
    state = copy.deepcopy(evidence["facts"])
    edges = [tuple(edge) for edge in evidence["edges"]]
    for query in evidence["queries"]:
        start, goal = query["from"], query["to"]
        direct = (start, goal) in edges or (goal, start) in edges
        seen, pending = {start}, [start]
        while pending:
            node = pending.pop()
            for left, right in edges:
                nxt = right if left == node else left if right == node else None
                if nxt is not None and nxt not in seen:
                    seen.add(nxt)
                    pending.append(nxt)
        state[query["direct_field"]] = direct
        state[query["reachable_field"]] = goal in seen
    return state


def speaker_state(evidence: dict[str, Any]) -> dict[str, Any]:
    state = {item["proposition"]: item["speaker"] for item in evidence["statements"]}
    state.update(evidence.get("missing", {}))
    return state


def rule_state(evidence: dict[str, Any]) -> dict[str, Any]:
    entity = evidence["entity"]
    state = copy.deepcopy(evidence.get("known", {}))
    for rule in evidence["rules"]:
        if all(entity.get(key) == value for key, value in rule["when"].items()):
            state[rule["field"]] = rule["value"]
    state.update(evidence.get("missing", {}))
    return state


def cancellation_state(evidence: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(evidence["entries"])


def derive(kind: str, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "version_edit": version_state,
        "state_inference": infer_state,
        "graph_inference": graph_state,
        "speaker_ownership": speaker_state,
        "rule_inference": rule_state,
        "cancellation": cancellation_state,
    }[kind](evidence)


def apply_request(state: dict[str, Any], request: dict[str, Any] | None) -> dict[str, Any]:
    out = copy.deepcopy(state)
    if not request or request.get("ambiguous") or request["kind"] == "respond_only":
        return out
    if request["kind"] == "version_ops":
        return version_state({"initial": out, "events": request["ops"]})
    if request["kind"] in {"cancel", "stop"}:
        out[request["target"]] = "cancelled" if request["kind"] == "cancel" else "stopped"
        return out
    raise ValueError(request)


def family(fid: str, setting: str, skill: str, structure: str, kind: str, context: str,
           assistant_context: str, evidence: dict[str, Any], action: dict[str, Any],
           variants: dict[str, dict[str, Any]], labels: list[str]) -> dict[str, Any]:
    return {"family_id": fid, "setting": setting, "skill": skill, "structure_signature": structure,
            "oracle_kind": kind, "visible_context_el": context, "assistant_context_el": assistant_context,
            "evidence": evidence, "action_contract": action, "variants": variants, "labels": labels}


TEXT = lambda name: {"mode": "text_record_edit", "external_tool_result_supplied": False,
                     "may_claim_external_action_success": False, "text_record_state_name": name}
REASON = {"mode": "reasoning_only", "external_tool_result_supplied": False,
          "may_claim_external_action_success": False, "text_record_state_name": None}


def v(core: str, claims: list[dict[str, Any]], request: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"core": core, "claims": claims, "request": request}


FAMILIES = [
family("ds60_f01_recipe_draft", "Πρόχειρο συνταγής για οικογενειακό τραπέζι", "version_editing", "scalar recipe draft with prior revisions and missing historical ingredient", "version_edit",
 "Στο τρέχον πρόχειρο της συνταγής γράφει: 4 μερίδες, 1 κουταλιά λάδι, φούρνος στους 180 βαθμούς και γαρνίρισμα με μαϊντανό.",
 "Βλέπω το τρέχον πρόχειρο· οι παλιότερες εκδοχές δεν εμφανίζονται εδώ.",
 {"initial":{"servings":3,"oil_spoons":2,"oven_c":170,"garnish":"άνηθος","notes":[]},"events":[{"op":"set","field":"servings","value":4},{"op":"set","field":"oil_spoons","value":1},{"op":"set","field":"oven_c","value":180},{"op":"set","field":"garnish","value":"μαϊντανός"}],"missing_history":["older_herb"]}, TEXT("πρόχειρο συνταγής"), {
 "true":v("Στο τρέχον πρόχειρο είναι 4 μερίδες και ο φούρνος στους 180 βαθμούς. Πρόσθεσε ξύσμα λεμονιού στις σημειώσεις.",[{"field":"servings","asserted":4},{"field":"oven_c","asserted":180}],{"kind":"version_ops","ops":[{"op":"add_unique","field":"notes","value":"ξύσμα λεμονιού"}]}),
 "false":v("Στο τρέχον πρόχειρο γράφει 2 κουταλιές λάδι. Άλλαξέ το τώρα σε 2 κουταλιές.",[{"field":"oil_spoons","asserted":2}],{"kind":"version_ops","ops":[{"op":"set","field":"oil_spoons","value":2}]}),
 "partial":v("Στο τρέχον πρόχειρο είναι 4 μερίδες, αλλά ο φούρνος στους 170 βαθμούς. Πρόσθεσε χρόνο ψησίματος 25 λεπτά.",[{"field":"servings","asserted":4},{"field":"oven_c","asserted":170}],{"kind":"version_ops","ops":[{"op":"set","field":"bake_minutes","value":25}]}),
 "unresolved":v("Με βάση μόνο το τρέχον πρόχειρο, βάλε ξανά το μυρωδικό που είχαμε στην παλιότερη εκδοχή.",[{"field":"older_herb","asserted":"unknown"}],{"kind":"version_ops","ambiguous":True,"ops":[]})}, LABELS4),

family("ds60_f02_studio_booking", "Κειμενικό σχέδιο κράτησης αίθουσας μουσικής", "version_editing", "rescheduled booking record with a deliberately absent duration", "version_edit",
 "Στο σχέδιο της κράτησης φαίνεται Τετάρτη στις 19:00, αίθουσα 2, χωρητικότητα 12 ατόμων και χωρίς προβολέα. Η διάρκεια δεν έχει καταγραφεί.",
 "Έχω το σχέδιο μπροστά μου και μπορώ να ελέγξω ό,τι είναι γραμμένο σε αυτό.",
 {"initial":{"day":"Τρίτη","time":"18:00","room":1,"capacity":10,"projector":False,"duration_minutes":None},"events":[{"op":"set","field":"day","value":"Τετάρτη"},{"op":"set","field":"time","value":"19:00"},{"op":"set","field":"room","value":2},{"op":"set","field":"capacity","value":12}]}, TEXT("σχέδιο κράτησης"), {
 "true":v("Στο σχέδιο είναι Τετάρτη στις 19:00, στην αίθουσα 2. Σημείωσε τώρα ότι χρειαζόμαστε προβολέα.",[{"field":"day","asserted":"Τετάρτη"},{"field":"time","asserted":"19:00"},{"field":"room","asserted":2}],{"kind":"version_ops","ops":[{"op":"set","field":"projector","value":True}]}),
 "false":v("Στο τρέχον σχέδιο είναι η αίθουσα 1. Μετέφερέ το τώρα στην αίθουσα 3.",[{"field":"room","asserted":1}],{"kind":"version_ops","ops":[{"op":"set","field":"room","value":3}]}),
 "partial":v("Στο σχέδιο είναι Τετάρτη, αλλά στις 18:00. Άλλαξε τώρα τη χωρητικότητα σε 14 άτομα.",[{"field":"day","asserted":"Τετάρτη"},{"field":"time","asserted":"18:00"}],{"kind":"version_ops","ops":[{"op":"set","field":"capacity","value":14}]}),
 "unresolved":v("Κράτα στο σχέδιο τη διάρκεια που είχαμε συμφωνήσει.",[{"field":"duration_minutes","asserted":"unknown"}],{"kind":"version_ops","ambiguous":True,"ops":[]})}, LABELS4),

family("ds60_f03_tool_checkout", "Δελτίο δανεισμού εργαλείων μιας ομάδας επισκευών", "state_inference", "disjoint stock partition: total minus loaned minus repair", "state_inference",
 "Το δελτίο γράφει 8 δράπανα συνολικά: 3 είναι δανεισμένα και 1 διαφορετικό δράπανο βρίσκεται για επισκευή.",
 "Θα υπολογίσω τη διαθεσιμότητα μόνο από αυτές τις τρεις κατηγορίες.",
 {"facts":{"total":8,"loaned":3,"in_repair":1,"return_day":None},"constants":{"zero":0},"formulas":[{"field":"available","op":"subtract_many","args":["total","loaned","in_repair"]},{"field":"has_available","op":"greater_than","args":["available","zero"]}]}, REASON, {
 "true":v("Άρα είναι διαθέσιμα 4 δράπανα.",[{"field":"available","asserted":4}],{"kind":"respond_only","task":"show_subtraction"}),
 "false":v("Άρα είναι διαθέσιμα 5 δράπανα.",[{"field":"available","asserted":5}],{"kind":"respond_only","task":"show_subtraction"}),
 "partial":v("Με βάση το δελτίο, τα 3 δράπανα είναι δανεισμένα και απομένουν 5 διαθέσιμα.",[{"field":"loaned","asserted":3},{"field":"available","asserted":5}],{"kind":"respond_only","task":"separate_correct_count_from_wrong_result"}),
 "unresolved":v("Με βάση μόνο το δελτίο, ένα από τα δανεισμένα δράπανα επιστρέφεται την Τρίτη.",[{"field":"return_day","asserted":"Τρίτη"}],{"kind":"respond_only","task":"identify_missing_return_day"})}, LABELS4),

family("ds60_f04_park_map_excerpt", "Απόσπασμα χάρτη μονοπατιών σε φανταστικό πάρκο", "premise_handling", "graph reachability distinguished from direct adjacency inside a supplied excerpt", "graph_inference",
 "Στο απόσπασμα του χάρτη φαίνονται μόνο τα μονοπάτια Πεύκο–Λίμνη, Λίμνη–Κήπος και Κήπος–Πύργος.",
 "Θα μιλήσω μόνο για ό,τι φαίνεται στο συγκεκριμένο απόσπασμα.",
 {"facts":{"outside_excerpt":None},"edges":[["Πεύκο","Λίμνη"],["Λίμνη","Κήπος"],["Κήπος","Πύργος"]],"queries":[{"from":"Πεύκο","to":"Πύργος","direct_field":"pine_tower_direct","reachable_field":"pine_tower_reachable"}]}, REASON, {
 "true":v("Στο απόσπασμα υπάρχει διαδρομή από το Πεύκο ως τον Πύργο.",[{"field":"pine_tower_reachable","asserted":True}],{"kind":"respond_only","task":"name_intermediate_nodes"}),
 "false":v("Στο απόσπασμα φαίνεται απευθείας μονοπάτι Πεύκο–Πύργος.",[{"field":"pine_tower_direct","asserted":True}],{"kind":"respond_only","task":"correct_directness_and_preserve_reachability"}),
 "partial":v("Στο απόσπασμα ο Πύργος είναι προσβάσιμος από το Πεύκο και συνδέονται απευθείας.",[{"field":"pine_tower_reachable","asserted":True},{"field":"pine_tower_direct","asserted":True}],{"kind":"respond_only","task":"separate_path_from_direct_edge"}),
 "unresolved":v("Με βάση μόνο το απόσπασμα, δεν υπάρχει κανένα άλλο μονοπάτι έξω από αυτό.",[{"field":"outside_excerpt","asserted":False}],{"kind":"respond_only","task":"state_scope_limit"})}, LABELS4),

family("ds60_f05_volunteer_board", "Κειμενικός πίνακας εργασιών μιας εθελοντικής γιορτής", "cancellation", "three named task states with correction followed by an authoritative cancellation", "cancellation",
 "Στον κειμενικό πίνακα, το στήσιμο και τα φυλλάδια είναι ενεργά, ενώ ο έλεγχος ήχου είναι ακυρωμένος.",
 "Βλέπω τρεις ξεχωριστές εγγραφές στον πίνακα και δεν έχει γίνει καμία εξωτερική ενέργεια.",
 {"entries":{"στήσιμο":"active","φυλλάδια":"active","έλεγχος_ήχου":"cancelled"}}, TEXT("πίνακας εργασιών"), {
 "true":v("Στον πίνακα ο έλεγχος ήχου είναι ήδη ακυρωμένος. Ακύρωσε τώρα και τα φυλλάδια.",[{"field":"έλεγχος_ήχου","asserted":"cancelled"}],{"kind":"cancel","target":"φυλλάδια"}),
 "false":v("Στον πίνακα το στήσιμο φαίνεται ήδη ακυρωμένο. Ακύρωσέ το τώρα.",[{"field":"στήσιμο","asserted":"cancelled"}],{"kind":"cancel","target":"στήσιμο"}),
 "partial":v("Στον πίνακα ο έλεγχος ήχου είναι ακυρωμένος και τα φυλλάδια επίσης. Ακύρωσε τώρα τα φυλλάδια.",[{"field":"έλεγχος_ήχου","asserted":"cancelled"},{"field":"φυλλάδια","asserted":"cancelled"}],{"kind":"cancel","target":"φυλλάδια"}),
 "unresolved":v("Ακύρωσε εκείνη την ενεργή εργασία στον πίνακα.",[{"field":"referenced_entry","asserted":"unknown"}],{"kind":"cancel","ambiguous":True,"candidates":["στήσιμο","φυλλάδια"]})}, LABELS4),

family("ds60_f06_key_handover", "Καταγραφή συνομιλίας για παράδοση κλειδιών", "speaker_ownership", "proposition-to-speaker attribution with two plausible feminine referents", "speaker_ownership",
 "Στην καταγραφή, η Νίκη είπε «τα κλειδιά είναι στο συρτάρι», ο Πέτρος είπε «η πίσω πόρτα είναι κλειδωμένη» και η Ελένη είπε «λείπει ο κωδικός του συναγερμού».",
 "Θα κρατήσω χωριστά ποιος είπε καθεμία από τις τρεις φράσεις.",
 {"statements":[{"proposition":"keys_in_drawer","speaker":"Νίκη"},{"proposition":"back_door_locked","speaker":"Πέτρος"},{"proposition":"alarm_code_missing","speaker":"Ελένη"}],"missing":{"ambiguous_she":None}}, REASON, {
 "true":v("Στην καταγραφή, η Νίκη είπε ότι τα κλειδιά είναι στο συρτάρι. Σύνοψε και τις τρεις δηλώσεις με τα σωστά ονόματα.",[{"field":"keys_in_drawer","asserted":"Νίκη"}],{"kind":"respond_only","task":"summarize_attributions"}),
 "false":v("Στην καταγραφή, ο Πέτρος είπε ότι τα κλειδιά είναι στο συρτάρι. Σύνοψε και τις τρεις δηλώσεις με τα σωστά ονόματα.",[{"field":"keys_in_drawer","asserted":"Πέτρος"}],{"kind":"respond_only","task":"correct_owner_then_summarize"}),
 "partial":v("Στην καταγραφή, ο Πέτρος είπε ότι η πίσω πόρτα είναι κλειδωμένη και η Νίκη ότι λείπει ο κωδικός. Σύνοψέ τα σωστά.",[{"field":"back_door_locked","asserted":"Πέτρος"},{"field":"alarm_code_missing","asserted":"Νίκη"}],{"kind":"respond_only","task":"separate_attributions_then_summarize"}),
 "unresolved":v("Με βάση μόνο την καταγραφή, εκείνη θα φέρει τελικά τα κλειδιά. Ποια ενέργεια μένει για εκείνη;",[{"field":"ambiguous_she","asserted":"Νίκη"}],{"kind":"respond_only","task":"identify_ambiguous_referent"})}, LABELS4),

family("ds60_f07_rehearsal_sheet", "Κειμενικό φύλλο ροής θεατρικής πρόβας", "version_editing", "ordered performance cues plus named solo and break duration", "version_edit",
 "Στο τρέχον φύλλο ροής, πρώτο είναι το «Θάλασσα», το σόλο το έχει η Μαρία και το διάλειμμα είναι 10 λεπτά. Τραγούδι λήξης δεν έχει καταγραφεί.",
 "Έχω μόνο την τρέχουσα εκδοχή του φύλλου ροής, όχι τις παλιότερες σημειώσεις.",
 {"initial":{"opening":"Άνεμος","solo":"Νίκος","break_minutes":15,"closing":None,"cues":[]},"events":[{"op":"set","field":"opening","value":"Θάλασσα"},{"op":"set","field":"solo","value":"Μαρία"},{"op":"set","field":"break_minutes","value":10}]}, TEXT("φύλλο ροής"), {
 "true":v("Στο τρέχον φύλλο πρώτο είναι το «Θάλασσα» και το σόλο το έχει η Μαρία. Πρόσθεσε υπόκλιση στο τέλος.",[{"field":"opening","asserted":"Θάλασσα"},{"field":"solo","asserted":"Μαρία"}],{"kind":"version_ops","ops":[{"op":"add_unique","field":"cues","value":"υπόκλιση"}]}),
 "false":v("Στο τρέχον φύλλο το σόλο το έχει ο Νίκος. Δώσ' το τώρα στον Νίκο.",[{"field":"solo","asserted":"Νίκος"}],{"kind":"version_ops","ops":[{"op":"set","field":"solo","value":"Νίκος"}]}),
 "partial":v("Στο φύλλο πρώτο είναι το «Θάλασσα» και το διάλειμμα 15 λεπτά. Κάνε τώρα το διάλειμμα 12 λεπτά.",[{"field":"opening","asserted":"Θάλασσα"},{"field":"break_minutes","asserted":15}],{"kind":"version_ops","ops":[{"op":"set","field":"break_minutes","value":12}]}),
 "unresolved":v("Βάλε ως λήξη το τραγούδι που είχαμε στην προηγούμενη εκδοχή.",[{"field":"closing","asserted":"unknown"}],{"kind":"version_ops","ambiguous":True,"ops":[]})}, LABELS4),

family("ds60_f08_fair_budget", "Πρόχειρος προϋπολογισμός σχολικής έκθεσης", "state_inference", "cash balance after two distinct recorded expenses", "state_inference",
 "Ο πρόχειρος προϋπολογισμός δείχνει 120 ευρώ διαθέσιμα, έξοδο 35 ευρώ για τραπέζια και άλλο έξοδο 15 ευρώ για πινακίδες. Δεν υπάρχει καταγεγραμμένη δωρεά.",
 "Θα υπολογίσω το υπόλοιπο από τα καταγεγραμμένα ποσά, χωρίς να προσθέσω έσοδο που δεν φαίνεται.",
 {"facts":{"starting":120,"tables":35,"signs":15,"donation":None},"constants":{},"formulas":[{"field":"remaining","op":"subtract_many","args":["starting","tables","signs"]}]}, REASON, {
 "true":v("Με βάση τα καταγεγραμμένα ποσά, το υπόλοιπο είναι 70 ευρώ.",[{"field":"remaining","asserted":70}],{"kind":"respond_only","task":"show_budget_subtraction"}),
 "false":v("Με βάση τα καταγεγραμμένα ποσά, το υπόλοιπο είναι 80 ευρώ.",[{"field":"remaining","asserted":80}],{"kind":"respond_only","task":"correct_budget_subtraction"}),
 "partial":v("Με βάση τον πρόχειρο προϋπολογισμό, τα τραπέζια κόστισαν 35 ευρώ και το υπόλοιπο είναι 80 ευρώ.",[{"field":"tables","asserted":35},{"field":"remaining","asserted":80}],{"kind":"respond_only","task":"separate_recorded_cost_from_wrong_balance"}),
 "unresolved":v("Με βάση μόνο τον πρόχειρο προϋπολογισμό, η δωρεά ήταν 20 ευρώ.",[{"field":"donation","asserted":20}],{"kind":"respond_only","task":"identify_missing_donation"})}, LABELS4),

family("ds60_f09_chore_log", "Κειμενικό ημερολόγιο εργασιών του σπιτιού", "stopping", "two active and one cancelled text tasks with ambiguous stop referent", "cancellation",
 "Στο κειμενικό ημερολόγιο, τα πιάτα και τα ρούχα είναι ενεργές εργασίες, ενώ τα σκουπίδια έχουν ακυρωθεί.",
 "Οι εγγραφές είναι μόνο μέσα στο ημερολόγιο αυτού του νήματος.",
 {"entries":{"πιάτα":"active","ρούχα":"active","σκουπίδια":"cancelled"}}, TEXT("ημερολόγιο εργασιών"), {
 "true":v("Στο ημερολόγιο τα σκουπίδια είναι ήδη ακυρωμένα. Σταμάτα τώρα τα πιάτα.",[{"field":"σκουπίδια","asserted":"cancelled"}],{"kind":"stop","target":"πιάτα"}),
 "false":v("Στο ημερολόγιο τα ρούχα φαίνονται ήδη σταματημένα. Σταμάτησέ τα τώρα.",[{"field":"ρούχα","asserted":"stopped"}],{"kind":"stop","target":"ρούχα"}),
 "partial":v("Στο ημερολόγιο τα σκουπίδια είναι ακυρωμένα και τα πιάτα σταματημένα. Σταμάτα τώρα τα πιάτα.",[{"field":"σκουπίδια","asserted":"cancelled"},{"field":"πιάτα","asserted":"stopped"}],{"kind":"stop","target":"πιάτα"}),
 "unresolved":v("Σταμάτα εκείνη την ενεργή εργασία του ημερολογίου.",[{"field":"referenced_entry","asserted":"unknown"}],{"kind":"stop","ambiguous":True,"candidates":["πιάτα","ρούχα"]})}, LABELS4),

family("ds60_f10_sorting_card", "Κάρτα κανόνων για φανταστική αποθήκη παιχνιδιού", "premise_handling", "conjunctive fictional rules deriving two independent placements", "rule_inference",
 "Η κάρτα κανόνων λέει: κάθε μπλε κιβώτιο πάει στο πάνω ράφι· κάθε εύθραυστο κιβώτιο μπαίνει σε θήκη με επένδυση. Το κιβώτιο Κ είναι μπλε και εύθραυστο. Δεν δίνεται το βάρος του.",
 "Θα εφαρμόσω τους κανόνες της κάρτας στο κιβώτιο Κ, χωρίς εξωτερικές υποθέσεις.",
 {"entity":{"color":"blue","fragile":True},"known":{},"rules":[{"when":{"color":"blue"},"field":"shelf","value":"upper"},{"when":{"fragile":True},"field":"case","value":"padded"}],"missing":{"weight":None}}, REASON, {
 "true":v("Με τους κανόνες της κάρτας, το κιβώτιο Κ πάει στο πάνω ράφι και σε θήκη με επένδυση.",[{"field":"shelf","asserted":"upper"},{"field":"case","asserted":"padded"}],{"kind":"respond_only","task":"apply_both_rules"}),
 "false":v("Με τους κανόνες της κάρτας, το κιβώτιο Κ πάει στο κάτω ράφι.",[{"field":"shelf","asserted":"lower"}],{"kind":"respond_only","task":"correct_rule_application"}),
 "partial":v("Με τους κανόνες της κάρτας, το κιβώτιο Κ πάει στο πάνω ράφι αλλά χωρίς επένδυση.",[{"field":"shelf","asserted":"upper"},{"field":"case","asserted":"plain"}],{"kind":"respond_only","task":"separate_two_rule_consequences"}),
 "unresolved":v("Με βάση μόνο την κάρτα, το κιβώτιο Κ ζυγίζει 4 κιλά.",[{"field":"weight","asserted":4}],{"kind":"respond_only","task":"identify_missing_weight"})}, LABELS4),

family("ds60_f11_playlist_order", "Πρόχειρη σειρά τραγουδιών για άσκηση", "version_editing", "ordered-list position query followed by deterministic reorder", "version_edit",
 "Στην τρέχουσα λίστα αναπαραγωγής η σειρά είναι «Αστέρι», «Βροχή», «Κύμα».",
 "Βλέπω αυτή τη σειρά των τριών κομματιών στο πρόχειρο.",
 {"initial":{"tracks":["Βροχή","Αστέρι","Κύμα"]},"events":[{"op":"set","field":"tracks","value":["Αστέρι","Βροχή","Κύμα"]}]}, TEXT("λίστα αναπαραγωγής"), {
 "true":v("Στην τρέχουσα λίστα τελευταίο είναι το «Κύμα». Μετέφερε τώρα το κομμάτι «Βροχή» στο τέλος.",[{"field":"tracks","op":"last_equals","asserted":"Κύμα"}],{"kind":"version_ops","ops":[{"op":"move_to_end","field":"tracks","value":"Βροχή"}]}),
 "false":v("Στην τρέχουσα λίστα τελευταίο είναι το κομμάτι «Βροχή». Μετέφερέ το τώρα στην αρχή.",[{"field":"tracks","op":"last_equals","asserted":"Βροχή"}],{"kind":"version_ops","ops":[{"op":"move_to_start","field":"tracks","value":"Βροχή"}]})}, LABELS2),

family("ds60_f12_seedling_trays", "Καταγραφή σπορείου μιας γειτονιάς", "state_inference", "nested subset subtraction: sprouted minus transplanted", "state_inference",
 "Η καταγραφή λέει ότι φύτρωσαν 18 φυτάρια και από αυτά μεταφυτεύτηκαν 6.",
 "Θα βρω πόσα φυτρωμένα φυτάρια παραμένουν στο σπορείο.",
 {"facts":{"sprouted":18,"transplanted":6},"constants":{},"formulas":[{"field":"still_in_trays","op":"subtract_many","args":["sprouted","transplanted"]}]}, REASON, {
 "true":v("Από αυτή την καταγραφή προκύπτει ότι παραμένουν 12 φυτρωμένα φυτάρια στο σπορείο.",[{"field":"still_in_trays","asserted":12}],{"kind":"respond_only","task":"show_subset_subtraction"}),
 "false":v("Από αυτή την καταγραφή προκύπτει ότι παραμένουν 10 φυτρωμένα φυτάρια στο σπορείο.",[{"field":"still_in_trays","asserted":10}],{"kind":"respond_only","task":"correct_subset_subtraction"})}, LABELS2),

family("ds60_f13_study_roles", "Σημειώσεις ανάθεσης σε ομάδα μελέτης", "speaker_ownership", "named responsibility attribution rather than proposition truth", "speaker_ownership",
 "Στις σημειώσεις, η Δανάη ανέλαβε τον προβολέα, ο Ορέστης την προέκταση ρεύματος και η Λία τα εισιτήρια.",
 "Θα κρατήσω κάθε αντικείμενο συνδεδεμένο με το πρόσωπο που το ανέλαβε.",
 {"statements":[{"proposition":"projector","speaker":"Δανάη"},{"proposition":"extension_cord","speaker":"Ορέστης"},{"proposition":"tickets","speaker":"Λία"}],"missing":{}}, REASON, {
 "true":v("Στις σημειώσεις, η Δανάη έχει αναλάβει τον προβολέα. Γράψε συνοπτικά και τις τρεις αναθέσεις.",[{"field":"projector","asserted":"Δανάη"}],{"kind":"respond_only","task":"summarize_assignments"}),
 "false":v("Στις σημειώσεις, ο Ορέστης έχει αναλάβει τον προβολέα. Γράψε συνοπτικά και τις τρεις αναθέσεις.",[{"field":"projector","asserted":"Ορέστης"}],{"kind":"respond_only","task":"correct_owner_then_summarize"})}, LABELS2),

family("ds60_f14_parcel_checklist", "Κειμενικό πρόχειρο λίστας συσκευασίας", "version_editing", "boolean checklist state followed by an authoritative mark", "version_edit",
 "Στο πρόχειρο της λίστας, η διεύθυνση έχει γραφτεί, η επένδυση έχει τοποθετηθεί και η ετικέτα δεν έχει ακόμη σημειωθεί ως εκτυπωμένη.",
 "Πρόκειται για κειμενικό έλεγχο της λίστας, όχι για πραγματική εκτύπωση ή αποστολή.",
 {"initial":{"address_written":False,"padding_added":False,"label_printed":False,"notes":[]},"events":[{"op":"set","field":"address_written","value":True},{"op":"set","field":"padding_added","value":True}]}, TEXT("λίστα συσκευασίας"), {
 "true":v("Στο πρόχειρο η επένδυση έχει τοποθετηθεί. Πρόσθεσε τώρα τη σημείωση «εύθραυστο».",[{"field":"padding_added","asserted":True}],{"kind":"version_ops","ops":[{"op":"add_unique","field":"notes","value":"εύθραυστο"}]}),
 "false":v("Στο πρόχειρο η ετικέτα φαίνεται ήδη εκτυπωμένη. Σημείωσέ την τώρα ως εκτυπωμένη.",[{"field":"label_printed","asserted":True}],{"kind":"version_ops","ops":[{"op":"set","field":"label_printed","value":True}]})}, LABELS2),

family("ds60_f15_game_score", "Πίνακας βαθμών ενός επιτραπέζιου παιχνιδιού", "state_inference", "weighted score: wins worth two plus draws worth one", "state_inference",
 "Ο κανόνας δίνει 2 βαθμούς για κάθε νίκη και 1 για κάθε ισοπαλία. Η ομάδα Άλφα έχει 3 νίκες και 1 ισοπαλία.",
 "Θα εφαρμόσω ακριβώς τον δοσμένο κανόνα βαθμολόγησης.",
 {"facts":{"wins":3,"draws":1},"constants":{},"formulas":[{"field":"points","op":"weighted_sum","args":[],"terms":[["wins",2],["draws",1]]}]}, REASON, {
 "true":v("Με τον δοσμένο κανόνα, η ομάδα Άλφα έχει 7 βαθμούς.",[{"field":"points","asserted":7}],{"kind":"respond_only","task":"show_weighted_sum"}),
 "false":v("Με τον δοσμένο κανόνα, η ομάδα Άλφα έχει 8 βαθμούς.",[{"field":"points","asserted":8}],{"kind":"respond_only","task":"correct_weighted_sum"})}, LABELS2),

family("ds60_f16_event_agenda", "Κειμενική ατζέντα μιας μικρής εκδήλωσης", "stopping", "agenda entry cancellation while another entry remains active", "cancellation",
 "Στην κειμενική ατζέντα, το καλωσόρισμα και η ομιλία είναι ενεργά, ενώ οι ερωτήσεις έχουν ακυρωθεί.",
 "Μπορώ να αλλάξω μόνο τις εγγραφές αυτού του πρόχειρου.",
 {"entries":{"καλωσόρισμα":"active","ομιλία":"active","ερωτήσεις":"cancelled"}}, TEXT("ατζέντα"), {
 "true":v("Στην ατζέντα οι ερωτήσεις είναι ήδη ακυρωμένες. Ακύρωσε τώρα και το καλωσόρισμα.",[{"field":"ερωτήσεις","asserted":"cancelled"}],{"kind":"cancel","target":"καλωσόρισμα"}),
 "false":v("Στην ατζέντα η ομιλία φαίνεται ήδη ακυρωμένη. Ακύρωσέ την τώρα.",[{"field":"ομιλία","asserted":"cancelled"}],{"kind":"cancel","target":"ομιλία"})}, LABELS2),

family("ds60_f17_ferry_token", "Κάρτα κανόνων για φανταστικό παιχνίδι λιμανιού", "premise_handling", "single conditional classification under fictional premises", "rule_inference",
 "Η κάρτα του παιχνιδιού λέει ότι κάθε κόκκινο εισιτήριο οδηγεί στην προβλήτα 1 και κάθε πράσινο στην προβλήτα 2. Το εισιτήριο Ζ είναι κόκκινο.",
 "Θα απαντήσω μέσα στους κανόνες του παιχνιδιού.",
 {"entity":{"color":"red"},"known":{},"rules":[{"when":{"color":"red"},"field":"pier","value":1},{"when":{"color":"green"},"field":"pier","value":2}],"missing":{}}, REASON, {
 "true":v("Με τον κανόνα της κάρτας, το εισιτήριο Ζ οδηγεί στην προβλήτα 1.",[{"field":"pier","asserted":1}],{"kind":"respond_only","task":"apply_supplied_rule"}),
 "false":v("Με τον κανόνα της κάρτας, το εισιτήριο Ζ οδηγεί στην προβλήτα 2.",[{"field":"pier","asserted":2}],{"kind":"respond_only","task":"correct_supplied_rule_application"})}, LABELS2),

family("ds60_f18_printmaking_stock", "Απογραφή χαρτιού εργαστηρίου χαρακτικής", "state_inference", "stock balance with used and separately reserved quantities", "state_inference",
 "Η απογραφή έχει 10 πακέτα χαρτί: 3 χρησιμοποιήθηκαν και 2 άλλα έχουν δεσμευτεί για το αυριανό μάθημα.",
 "Οι χρησιμοποιημένες και οι δεσμευμένες ποσότητες είναι διαφορετικά πακέτα.",
 {"facts":{"total":10,"used":3,"reserved":2},"constants":{},"formulas":[{"field":"free","op":"subtract_many","args":["total","used","reserved"]}]}, REASON, {
 "true":v("Με βάση την απογραφή, μένουν 5 ελεύθερα πακέτα χαρτί.",[{"field":"free","asserted":5}],{"kind":"respond_only","task":"show_stock_balance"}),
 "false":v("Με βάση την απογραφή, μένουν 7 ελεύθερα πακέτα χαρτί.",[{"field":"free","asserted":7}],{"kind":"respond_only","task":"correct_stock_balance"})}, LABELS2),

family("ds60_f19_weekly_menu", "Κειμενικό πρόχειρο εβδομαδιαίου μενού", "version_editing", "day-to-item mapping overwrite", "version_edit",
 "Στο τρέχον πρόχειρο του μενού γράφει: Τρίτη φακές, Τετάρτη ομελέτα, Πέμπτη ζυμαρικά.",
 "Βλέπω το μενού ανά ημέρα και μπορώ να ενημερώσω μόνο αυτό το πρόχειρο.",
 {"initial":{"Tuesday":"σούπα","Wednesday":"ομελέτα","Thursday":"ρύζι"},"events":[{"op":"set","field":"Tuesday","value":"φακές"},{"op":"set","field":"Thursday","value":"ζυμαρικά"}]}, TEXT("εβδομαδιαίο μενού"), {
 "true":v("Στο τρέχον πρόχειρο η Τετάρτη έχει ομελέτα. Άλλαξέ την τώρα σε σαλάτα.",[{"field":"Wednesday","asserted":"ομελέτα"}],{"kind":"version_ops","ops":[{"op":"set","field":"Wednesday","value":"σαλάτα"}]}),
 "false":v("Στο τρέχον πρόχειρο η Πέμπτη έχει ομελέτα. Άλλαξέ την τώρα σε σούπα.",[{"field":"Thursday","asserted":"ομελέτα"}],{"kind":"version_ops","ops":[{"op":"set","field":"Thursday","value":"σούπα"}]})}, LABELS2),

family("ds60_f20_reading_workflow", "Κειμενικός πίνακας εργασιών ανάγνωσης", "stopping", "stop one named workflow step while preserving completed and active neighbors", "cancellation",
 "Στον πίνακα ανάγνωσης, η περίληψη και το γλωσσάρι είναι ενεργά, ενώ ο έλεγχος παραπομπών έχει ολοκληρωθεί.",
 "Οι καταστάσεις αφορούν μόνο τον πίνακα αυτού του νήματος.",
 {"entries":{"περίληψη":"active","γλωσσάρι":"active","έλεγχος_παραπομπών":"completed"}}, TEXT("πίνακας ανάγνωσης"), {
 "true":v("Στον πίνακα ο έλεγχος παραπομπών έχει ολοκληρωθεί. Σταμάτα τώρα το γλωσσάρι και πες ποια εργασία μένει ενεργή.",[{"field":"έλεγχος_παραπομπών","asserted":"completed"}],{"kind":"stop","target":"γλωσσάρι"}),
 "false":v("Στον πίνακα η περίληψη φαίνεται ήδη σταματημένη. Σταμάτησέ την τώρα και πες ποια εργασία μένει ενεργή.",[{"field":"περίληψη","asserted":"stopped"}],{"kind":"stop","target":"περίληψη"})}, LABELS2),
]


def classify(state: dict[str, Any], claims: list[dict[str, Any]]) -> str:
    values: list[bool | None] = []
    for claim in claims:
        actual = state.get(claim["field"])
        if actual is None:
            values.append(None)
        elif claim.get("op", "equals") == "last_equals":
            values.append(bool(actual) and actual[-1] == claim["asserted"])
        else:
            values.append(actual == claim["asserted"])
    if any(value is None for value in values):
        return "unresolved"
    if all(values):
        return "true"
    if not any(values):
        return "false"
    return "partial"


def moves(label: str, request: dict[str, Any] | None) -> list[str]:
    base = {
        "true": ["acknowledge_supported_claim"],
        "false": ["correct_unsupported_claim_briefly"],
        "partial": ["separate_supported_and_unsupported_atoms"],
        "unresolved": ["name_missing_or_ambiguous_evidence", "ask_one_targeted_clarification"],
    }[label]
    if request and not request.get("ambiguous") and request["kind"] != "respond_only":
        base += ["apply_clear_current_text_state_instruction", "state_result_concisely"]
    elif request and request["kind"] == "respond_only":
        base += ["continue_the_requested_reasoning_or_summary"]
    else:
        base += ["do_not_invent_state"]
    return base


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    rows, oracle_rows, family_rows = [], [], []
    tone_index = 0
    for fam in FAMILIES:
        before = derive(fam["oracle_kind"], fam["evidence"])
        row_ids = []
        for label in fam["labels"]:
            variant = fam["variants"][label]
            assert classify(before, variant["claims"]) == label, (fam["family_id"], label, before, variant["claims"])
            after = apply_request(before, variant["request"])
            rid = f"scale60_{fam['family_id'][len('ds60_f'):]}_{label}"
            tone = TONES[tone_index % len(TONES)]
            tone_index += 1
            row_ids.append(rid)
            plan = {
                "context_user_id": rid + ".u_context",
                "context_assistant_id": rid + ".a_context",
                "context_assistant_train": False,
                "decision_user_id": rid + ".u_decision",
                "decision_user_train": False,
                "target_assistant_id": rid + ".a_target",
                "target_assistant_train": True,
                "exactly_one_supervised_assistant_turn": True,
            }
            visible = {
                "required_user_context_core_el": fam["visible_context_el"],
                "required_assistant_context_core_el": fam["assistant_context_el"],
                "source_role": "user",
                "assistant_context_is_independent_evidence": False,
                "assistant_context_train": False,
                "must_precede_decision": True,
                "visible_basis_sha256": canon_sha({"user_context": fam["visible_context_el"], "evidence": fam["evidence"]}),
            }
            surface = {
                "frozen_core_el": variant["core"],
                "must_appear_verbatim": True,
                "tone_realization_requirement": TONE_RULES[tone],
                "tone_must_not_add_facts_values_references_or_operations": True,
                "tone_must_not_change_declarative_core_into_question": True,
            }
            oracle = {"kind": fam["oracle_kind"], "derived_truth": label,
                      "state_before": before, "state_after": after}
            protected = {"family_id": fam["family_id"], "split": "train", "truth_category": label,
                         "oracle": oracle, "visible_evidence_contract": visible,
                         "decision_surface_contract": surface, "action_contract": fam["action_contract"]}
            spec = {
                "spec_id": rid, "contract_version": 2, "family_id": fam["family_id"], "split": "train",
                "decision_count": 1, "truth_category": label, "tone": tone, "target_language": "el",
                "origin": "native_fictional_everyday_not_benchmark_derived", "skill": fam["skill"],
                "setting": fam["setting"], "structure_signature": fam["structure_signature"],
                "user_decision_semantic_content_el": variant["core"], "tone_realization_requirement": TONE_RULES[tone],
                "evidence": fam["evidence"], "claim_atoms": variant["claims"], "current_request": variant["request"],
                "context_blueprint": {"evidence_summary_el": fam["visible_context_el"],
                                      "assistant_context_el": fam["assistant_context_el"],
                                      "assistant_context_train": False,
                                      "assistant_must_not_introduce_evidence": True},
                "visible_evidence_contract": visible, "decision_surface_contract": surface,
                "action_contract": fam["action_contract"], "oracle": oracle,
                "expected": {"generation_status": "prospective_not_authored", "response_moves": moves(label, variant["request"]),
                             "exact_response": None, "no_stock_argumentative_tail": True, "no_generic_followup_offer": True},
                "authoring_guards": [
                    "Use only the visible user evidence as the oracle basis.",
                    "Keep the context assistant turn train:false and never treat it as independent evidence.",
                    "Apply every clear new user instruction even when the preceding current-record claim is false.",
                    "Do not turn an unsupported inference into authoritative new user state.",
                    "Text-record edits and stopping remain inside the named in-dialogue record; never claim an external action.",
                    "Preserve the frozen decision core; tone may not add semantic atoms.",
                ],
            }
            row = {"row_id": rid, "family_id": fam["family_id"], "split": "train", "operation": "prospective_authoring",
                   "domain": "correcting_dialogue", "target_language": "el",
                   "teaching_objective": "Respond to a correction from visible evidence, preserve speaker and state ownership, and continue any valid task.",
                   "message_plan": plan, "protected": protected, "scenario_spec": spec,
                   "lineage": {"batch": "dialogue_scale60", "family_source": "native_fictional_manual_specification",
                               "public_benchmark_derived": False, "authored_target_exists": False}}
            rows.append(row)
            oracle_rows.append({"row_id": rid, "family_id": fam["family_id"], "truth_category": label,
                                "oracle_kind": fam["oracle_kind"], "computed_state_before": before,
                                "computed_truth": classify(before, variant["claims"]), "computed_state_after": after,
                                "claim_atoms": variant["claims"], "current_request": variant["request"]})
        family_rows.append({"family_id": fam["family_id"], "split": "train", "setting": fam["setting"],
                            "skill": fam["skill"], "oracle_kind": fam["oracle_kind"],
                            "structure_signature": fam["structure_signature"], "decision_labels": fam["labels"],
                            "decision_row_ids": row_ids, "decision_count": len(row_ids),
                            "origin": "native_fictional_everyday_not_benchmark_derived"})
    assert len(rows) == 60 and len(family_rows) == 20
    write_jsonl(ROOT / "specs.jsonl", rows)
    write_jsonl(ROOT / "oracle_receipts.jsonl", oracle_rows)
    write_jsonl(ROOT / "family_manifest.jsonl", family_rows)
    known_files = [PILOT / "inputs/train.jsonl", PILOT / "inputs/dev.jsonl", PILOT / "sealed/final_confirmation/gate_summary.json"]
    write_json(ROOT / "lineage_receipt.json", {
        "status": "train_only_family_namespace_frozen",
        "new_family_prefix": "ds60_",
        "new_family_count": 20,
        "new_decision_count": 60,
        "known_source_hashes": {str(path.relative_to(ROOT.parent)): file_sha(path) for path in known_files},
        "known_train_and_dev_family_intersection": [],
        "final_confirmation": {"content_materialized": False, "gate_summary_only": True,
                               "family_ids_sha256": json.loads((PILOT / "sealed/final_confirmation/gate_summary.json").read_text())["family_ids_sha256"]},
        "scale_target": {"train":{"true":200,"false":200,"partial":100,"unresolved":100,"total":600},
                         "development":60,"final_confirmation":60,"total":720},
        "this_batch": {"true":20,"false":20,"partial":10,"unresolved":10,"total":60},
        "superseded_claim": "Any earlier 420-train allocation is superseded; 600 is the training target and holdouts are additional.",
        "authored_targets": 0,
    })
    counts = Counter(row["scenario_spec"]["truth_category"] for row in rows)
    tones = Counter(row["scenario_spec"]["tone"] for row in rows)
    skills = Counter(row["scenario_spec"]["skill"] for row in rows)
    kinds = Counter(row["scenario_spec"]["oracle"]["kind"] for row in rows)
    (ROOT / "diversity_report.md").write_text(f"""# Dialogue scale-60 specification report

Prepared `{datetime.now(timezone.utc).isoformat()}`. This is a prospective, train-only specification batch: 60 decisions in 20 new fictional families. It contains no authored assistant targets, model calls, queue, development content, or final-confirmation material.

## Allocation

Ten families carry true, false, partial and unresolved variants; ten carry true and false variants. The resulting decision counts are `{dict(counts)}`. This is exactly one tenth of the 600-row training target of 200 true, 200 false, 100 partial and 100 unresolved. The separate 60-row development and 60-row final-confirmation targets remain outside this batch. The earlier 420-row training interpretation is superseded.

## Breadth

The 20 structure signatures are unique. Evidence forms include revised scalar drafts, ordered lists, day-to-item maps, disjoint stock partitions, subset arithmetic, weighted scores, graph reachability, fictional conditional rules, speaker-attribution maps, boolean checklists, and named text-task states. Skill counts are `{dict(skills)}` and oracle counts are `{dict(kinds)}`.

All four tone instructions occur 15 times: `{dict(tones)}`. They describe conversational stance without forcing prefixes. Every decision has a natural user evidence turn and an unsupervised assistant context turn. The assistant context may organize or acknowledge the visible record but is explicitly barred from becoming oracle evidence.

## Scope safeguards

Every false current-state claim is explicitly tied to a displayed draft, list, board or supplied premise. A following clear update is applied as authoritative current instruction. Unresolved rows either expose a missing field, preserve an ambiguous referent, or limit an inference to the supplied excerpt; none inserts a hidden value. Cancellation and stopping affect only named text records, and the action contracts prohibit claims about external orders, reminders, devices or services.

The batch uses the reserved `ds60_` train-family namespace and has no overlap with known revision-2 train or development family IDs. Final-confirmation content was not opened: only its frozen gate summary hash is recorded. This protects the final split from specification tuning.

## Quality boundary

`verify_scale60.py` recomputes every truth label and post-request state from evidence, checks the 20/20/10/10 distribution, mask plans, action scope, tone balance, family uniqueness and known split separation. These specifications still require full semantic review before any authoring. They do not establish that 600 training dialogues have been produced or that this 60-row batch is quality-ready for scale.
""")
    artifacts = {name: file_sha(ROOT / name) for name in ["specs.jsonl","oracle_receipts.jsonl","family_manifest.jsonl","lineage_receipt.json","diversity_report.md","build_scale60.py","verify_scale60.py","audit_train32_scope.py"]}
    write_json(ROOT / "manifest.json", {"version":1,"status":"specifications_prepared_not_authored","created_at":datetime.now(timezone.utc).isoformat(),
              "counts":{"families":20,"decisions":60,"true":20,"false":20,"partial":10,"unresolved":10},
              "split":"train","authored_targets":0,"model_calls":0,"queue_created":False,"final_content_materialized":False,
              "artifact_sha256":artifacts})


if __name__ == "__main__":
    main()
