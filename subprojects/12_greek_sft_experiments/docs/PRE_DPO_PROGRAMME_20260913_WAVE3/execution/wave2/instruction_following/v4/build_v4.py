#!/usr/bin/env python3
"""Build the reviewable v4 envelope from immutable v3 candidates."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
V3 = HERE.parent / "v3" / "candidates.jsonl"
V3_REVIEW = HERE.parent / "v3" / "independent_review" / "adjudications.jsonl"
CHECKER = Path("/Users/foivoskarounos-zamparloukos/Projects/train-apertus-with-glossapi/subprojects/12_greek_sft_experiments/data/greek_if/constraints.py")


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


spec = importlib.util.spec_from_file_location("wave2_v4_constraints", CHECKER)
C = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(C)

prior_rows = [json.loads(line) for line in V3.read_text().splitlines() if line.strip()]
prior_review = {r["row_id"]: r for r in map(json.loads, V3_REVIEW.read_text().splitlines())}
assert len(prior_rows) == 20 and len(prior_review) == 20

source_reviews = {
    "mixa_2028_03200": {
        "row_id": "mixa_2028_03200",
        "checked_on": "2026-09-13",
        "reviewer": "Sol agent",
        "source_type": "primary_official",
        "source_urls": ["https://oramaelpidas.gr/aitisi_ethelonti_doti/"],
        "verified_claim": "The official page says the registrant receives an envelope, completes the registration application contained in it, follows the oral-swab instructions, and returns the envelope.",
        "adjudication": "The v3 wording 'φάκελο με την αίτηση και οδηγίες για το στοματικό επίχρισμα' is supported. No factual repair is warranted.",
    },
    "mixa_2026_06199": {
        "row_id": "mixa_2026_06199",
        "checked_on": "2026-09-13",
        "reviewer": "Sol agent",
        "source_type": "primary_official",
        "source_urls": [
            "https://www.eody.gov.gr/el/perivallon-ygeia/odigies/kausonas.html",
            "https://www.eody.gov.gr/el/epikairotita/mathete-ta-symptomata-tes-thermoplexias-kai-tes-thermikes-exantleses.html",
            "https://civilprotection.gov.gr/odigies-prostasias/kaysonas",
        ],
        "verified_claim": "EODY identifies children and people exercising intensely as higher-risk groups, recommends cooler hours and reducing exercise in heat, and distinguishes heatstroke emergency action from heat-exhaustion monitoring. Civil Protection advises avoiding heavy work in high heat and prolonged walking or running in the sun.",
        "adjudication": "Both named links are live and support the attributed prevention claims. The response is narrowed so that emergency escalation is tied to suspected heatstroke, while milder symptoms trigger stopping, cooling, and conditional medical help.",
    },
}

out = []
delta = []
for old in prior_rows:
    rid = old["row_id"]
    row = copy.deepcopy(old["candidate_row"])
    changes = []

    if rid == "mixa_2026_05543":
        for constraint in row["meta"]["constraints"]:
            if constraint["family"] == "paragraph_starts_with":
                constraint["text"] = "Ξεκίνα την παράγραφο 2 με τη λέξη «Τελικά». Η σύγκριση αγνοεί τόνους και κεφαλαία."
            elif constraint["family"] == "keyword_freq":
                constraint["text"] = "Χρησιμοποίησε τη λέξη «επιλογή» τουλάχιστον 2 φορές. Η καταμέτρηση αγνοεί τόνους και κεφαλαία."
        changes = ["Aligned the active constraint metadata with the surfaced lexical-identity protocol; the response text is unchanged."]
    elif rid == "mixa_2026_06199":
        response = (
            "Ναι, προπόνηση μπάσκετ σε ακάλυπτη αυλή στις 14:00 με 39°C πρέπει *να ακυρωθεί ή να μεταφερθεί* "
            "σε κλειστό δροσερό χώρο ή σε σαφώς δροσερότερη ώρα. Πες στον γυμναστή ότι ο ΕΟΔΥ περιλαμβάνει τα παιδιά "
            "και όσους ασκούνται έντονα στις ομάδες αυξημένου κινδύνου, συνιστά οι εξωτερικές δραστηριότητες να γίνονται "
            "σε δροσερότερες ώρες και να μειώνεται η άσκηση στη ζέστη. Η Πολιτική Προστασία συνιστά επίσης να αποφεύγονται "
            "η βαριά σωματική δραστηριότητα σε υψηλή θερμοκρασία και το παρατεταμένο τρέξιμο στον ήλιο "
            "([ΕΟΔΥ](https://www.eody.gov.gr/el/perivallon-ygeia/odigies/kausonas.html), "
            "[Πολιτική Προστασία](https://civilprotection.gov.gr/odigies-prostasias/kaysonas)). "
            "Ζήτησε ασφαλή εναλλακτική· *το νερό και τα διαλείμματα δεν υποκαθιστούν τη μεταφορά ή την ακύρωση* σε αυτές τις συνθήκες. "
            "Αν κάποιος ζαλιστεί, έχει ναυτία ή πονοκέφαλο, σταματά αμέσως, πηγαίνει σε δροσερό μέρος και ζητά βοήθεια ενηλίκου· "
            "αν τα συμπτώματα χειροτερεύουν, επιμένουν ή υπάρχει εμετός, χρειάζεται άμεσα ιατρική βοήθεια. Σε πιθανή θερμοπληξία, "
            "ιδίως με πολύ υψηλή θερμοκρασία σώματος, σύγχυση ή λιποθυμία, κάλεσε αμέσως το 112 για ασθενοφόρο."
        )
        row["assistant"] = response
        row["turns"][-1]["content"] = response
        changes = ["Kept the cancellation-or-relocation recommendation and two highlights, verified both named official sources, and separated heat-exhaustion actions from suspected-heatstroke emergency escalation."]
    elif rid == "mixa_2026_11688":
        response = row["assistant"].replace(
            "Κατά την άποψή μου, το σύστημα είναι δίκαιο μόνο υπό προϋποθέσεις.",
            "Αν με ρωτάτε, το σύστημα είναι δίκαιο μόνο υπό προϋποθέσεις.",
        ).replace(
            "Η δική μου άποψη είναι ότι δεν είναι απόλυτα δίκαιο.",
            "Αν με ρωτάς, δεν είναι απόλυτα δίκαιο.",
        )
        assert response != row["assistant"]
        row["assistant"] = response
        row["turns"][-1]["content"] = response
        changes = ["Added one explicit plural reader address to the official version and one singular reader address to the friendly version; preserved the opinion content and ψ-bearing vocabulary."]

    checks = C.check_all(row["assistant"], row["meta"]["constraints"], row["user"])
    assert all((not c["checkable"]) or c["ok"] for c in checks), (rid, checks)
    candidate_hash = sha_bytes(canonical(row))
    changed = candidate_hash != old.get("v3_candidate_sha256")
    # v3_candidate_sha256 is the v3 row hash used by that envelope; fall back to
    # a direct hash because older wrappers used two candidate-hash conventions.
    old_direct_hash = sha_bytes(canonical(old["candidate_row"]))
    changed = candidate_hash != old_direct_hash

    prior = prior_review[rid]
    active_review = {
        "reviewer": "Sol agent",
        "reviewed_on": "2026-09-13",
        "verdict": "accept",
        "source_fidelity": "supported_primary_source" if rid in source_reviews else prior["source_fidelity"],
        "semantic_completeness": "complete",
        "unsupported_facts": "none_observed_after_primary_source_check" if rid in source_reviews else prior["unsupported_facts"],
        "repair_introduced_defect": False,
        "basis": "full request-response semantic read plus canonical constraint checker; official source check where listed",
    }
    if rid == "mixa_2026_05543":
        active_review["source_fidelity"] = "candidate_row_and_active_metadata_aligned"
    if rid == "mixa_2026_11688":
        active_review["source_fidelity"] = "source_faithful_minimal_constraint_repair"

    current = {
        "version": 4,
        "decision": "accepted",
        "candidate_row_sha256": candidate_hash,
        "checker_results": checks,
        "all_checkable_pass": True,
        "changed_from_v3_candidate": changed,
        "changes_from_v3": changes,
        "review": active_review,
        "source_review": source_reviews.get(rid),
        "production_promoted": False,
    }
    record = {
        "row_id": rid,
        "status": "candidate",
        "selection_class": old["selection_class"],
        "source_identity": old["source_identity"],
        "original_row": old["original_row"],
        "candidate_row": row,
        "preserved_invariants": old["preserved_invariants"],
        "current": current,
        "lineage": {
            "parent": str(V3),
            "parent_record_sha256": sha_bytes(canonical(old)),
            "parent_candidate_row_sha256": old_direct_hash,
        },
    }
    record["envelope_sha256"] = sha_bytes(canonical(record))
    out.append(record)
    if changed:
        delta.append({"row_id": rid, "changes": changes, "old_candidate_sha256": old_direct_hash, "new_candidate_sha256": candidate_hash})

with (HERE / "candidates.jsonl").open("w") as handle:
    for record in out:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
(HERE / "source_review.json").write_text(json.dumps(list(source_reviews.values()), ensure_ascii=False, indent=2) + "\n")
(HERE / "delta_from_v3.json").write_text(json.dumps(delta, ensure_ascii=False, indent=2) + "\n")

decisions = Counter(r["current"]["decision"] for r in out)
receipt = {
    "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    "rows": len(out),
    "accepted": decisions["accepted"],
    "held": decisions["held"],
    "checker_pass": sum(r["current"]["all_checkable_pass"] for r in out),
    "changed_candidate_rows_from_v3": len(delta),
    "changed_row_ids": [d["row_id"] for d in delta],
    "reviewer": "Sol agent",
    "checker_path": str(CHECKER),
    "checker_sha256": sha_bytes(CHECKER.read_bytes()),
    "input_v3_sha256": sha_bytes(V3.read_bytes()),
    "output_sha256": sha_bytes((HERE / "candidates.jsonl").read_bytes()),
    "source_review_sha256": sha_bytes((HERE / "source_review.json").read_bytes()),
    "production_promoted": 0,
    "model_subprocess_calls": 0,
}
(HERE / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(receipt, ensure_ascii=False, indent=2))
