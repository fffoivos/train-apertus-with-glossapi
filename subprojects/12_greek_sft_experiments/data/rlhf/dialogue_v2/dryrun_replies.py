"""Hand-written stand-in assistant replies for the Stage C dry run ONLY (real Sol user/world/learner calls against
fixed replies, no GPU). They exercise defects and progress; they are never data, never saved outside runtime/dryrun,
and never shown as Apertus output."""
from __future__ import annotations

REPLIES = {
    "RGD001": [
        "Αξιότιμε κύριε Υπεύθυνε του Σεμιναρίου,\n\nΜε ιδιαίτερη εκτίμηση και σεβασμό θα ήθελα να σας εκφράσω τη βαθύτατη λύπη μου, διότι λόγω ανωτέρας βίας δεν θα καταστεί δυνατή η παρουσία μου στη συνάντηση της ερχόμενης Παρασκευής. Θα ήμουν ευγνώμων, εάν μου επιτρέπατε, να σας παρακαλέσω θερμά να εξετάσετε το ενδεχόμενο συμμετοχής μου στην αμέσως επόμενη συνάντηση του σεμιναρίου, εφόσον βεβαίως αυτό δεν προκαλεί την παραμικρή αναστάτωση στον προγραμματισμό σας.\n\nΕυχαριστώ εκ των προτέρων για την πολύτιμη κατανόησή σας.\n\nΜετά βαθύτατου σεβασμού,\n[Όνομα]",
        "Καλησπέρα σας,\n\nδεν θα μπορέσω να είμαι στο σεμινάριο της Παρασκευής. Μπορώ να συμμετάσχω στην επόμενη συνάντηση;\n\nΕυχαριστώ,\n[Όνομα]",
    ],
    "RGD002": [
        "🌱 DON'T MISS THE EVENT OF THE SEASON! 🌱\n\nOn 12 October, 3–5 pm, our community garden becomes the ultimate paradise for plant lovers! Expert gardeners will be on hand to share their secrets, free refreshments will keep you going, and all tools will be provided. Entry is free and you can come even without seeds. This is an unmissable, life-changing afternoon — be there!",
        "Seed swap at the community garden\n\nOn 12 October, 3–5 pm, bring spare seeds to the community garden and swap them with neighbours. Entry is free, and you are welcome even if you have no seeds.",
    ],
    "RGD003": [
        "Δοκίμασε τα εξής:\n1. Κάνε επανεκκίνηση στον εκτυπωτή, στον φορητό και στο ρούτερ.\n2. Έλεγξε σε ποιο δίκτυο Wi-Fi είναι συνδεδεμένος ο φορητός.\n3. Τύπωσε από τον εκτυπωτή μια σελίδα με τις ρυθμίσεις δικτύου του, για να δεις σε ποιο δίκτυο είναι συνδεδεμένος.\nΠες μου τι βλέπεις.",
        "Αν ο εκτυπωτής είναι σε διαφορετικό δίκτυο από τον φορητό, σύνδεσέ τον στο ίδιο δίκτυο από τις ρυθμίσεις Wi-Fi στην οθόνη του και μετά ξαναπρόσθεσέ τον στον υπολογιστή.",
    ],
    "RGD004": [
        "This usually means requests was installed for a different Python than the one running your script. Please check:\n1. In the VS Code terminal run `python --version` and `pip --version`.\n2. Look at the bottom-right of VS Code to see which interpreter is selected.\nTell me what they show.",
        "Try `pip install --upgrade requests` and then restart VS Code.",
    ],
    "RGD005": [
        "Η διαίρεση δεν σημαίνει πάντα «μικραίνω». Μπορείς να τη δεις ως ερώτηση: «πόσες φορές χωράει ο διαιρέτης μέσα στον διαιρετέο;». Για παράδειγμα, 3 : 1/2 ρωτάει πόσα μισά χωράνε στο 3. Σε κάθε ακέραιο χωράνε δύο μισά, άρα στο 3 χωράνε 6 μισά. Γι' αυτό το αποτέλεσμα είναι μεγαλύτερο από το 3: μετράμε κομμάτια μικρότερα από ένα.",
        "Σωστά. Ο κανόνας «αντιστρέφω και πολλαπλασιάζω» απλώς μετράει γρήγορα πόσα τέτοια κομμάτια χωράνε.",
    ],
    "RGD006": [
        "Η παράφραση κρατάει όλες τις πληροφορίες με άλλα λόγια, γι' αυτό βγαίνει ίδιο μήκος. Η περίληψη διαλέγει μόνο τα βασικά για τον σκοπό της. Ρώτα τον εαυτό σου: «τι πρέπει να ξέρει κάποιος που θα διαβάσει μόνο αυτό;» και άφησε έξω λεπτομέρειες και παραδείγματα. Αν θες, στείλε μου ένα κείμενο και να προσπαθήσουμε μαζί.",
        "Καλή προσπάθεια. Κράτησες τα βασικά, αλλά ίσως μπορείς να το κάνεις λίγο πιο σύντομο.",
    ],
    "DVI001": [
        "Ο σταθμός του χωριού έκλεινε εκείνο το απόγευμα. Ο κυρ-Στάθης, συνταξιούχος σταθμάρχης, είχε έρθει να δει το τελευταίο τρένο. Μια νεαρή επιβάτισσα καθόταν στο παγκάκι κρατώντας ένα παλιό εισιτήριο. Ο Στάθης το αναγνώρισε αμέσως: ήταν το εισιτήριο που είχε κόψει ο ίδιος πριν από σαράντα χρόνια στη γιαγιά της, την ημέρα που έφυγε για την Αθήνα και δεν γύρισε ποτέ. Η κοπέλα το είχε βρει σε ένα κουτί και ήθελε να κάνει το ίδιο ταξίδι ανάποδα. Ο σταθμάρχης κατάλαβε ότι το εισιτήριο ήταν μια υπόσχεση επιστροφής που επιτέλους εκπληρωνόταν.",
        "— Αυτό το εισιτήριο το έκοψα εγώ, είπε ο Στάθης.\n— Της γιαγιάς μου είναι. Δεν ταξίδεψε ποτέ.\n— Τότε ήρθες να κάνεις εσύ το ταξίδι;\n— Ήρθα να το φέρω πίσω.",
    ],
    "DVI002": [
        "Πρόγραμμα:\nΔευτέρα 17:00–20:00 Αλγόριθμοι\nΤρίτη 10:00–13:00 Αλγόριθμοι, 19:00–20:30 Βάσεις Δεδομένων\nΤετάρτη 10:00–13:00 Δίκτυα\nΠέμπτη 10:00–13:00 Αλγόριθμοι\nΠαρασκευή 10:00–13:00 Βάσεις Δεδομένων\nΣάββατο 17:00–20:00 Αλγόριθμοι\nΚυριακή 10:00–13:00 Δίκτυα, 16:00–19:00 Αλγόριθμοι",
        "Διόρθωσα τις συγκρούσεις:\nΔευτέρα 10:00–13:00 Αλγόριθμοι\nΤρίτη 10:00–13:00 Αλγόριθμοι, 16:00–18:00 Βάσεις Δεδομένων\nΤετάρτη 10:00–13:00 Δίκτυα\nΠέμπτη 10:00–13:00 Αλγόριθμοι\nΠαρασκευή 10:00–13:00 Βάσεις Δεδομένων\nΣάββατο 17:00–20:00 Αλγόριθμοι\nΚυριακή 10:00–13:00 Δίκτυα, 16:00–19:00 Αλγόριθμοι",
    ],
    "DVI003": [
        "Volunteer update:\n- Monday 12 October: Sarah covers the welcome desk instead of the stockroom.\n- Delivery now Wednesday 14 October (not Friday 16 October).\n- Imran meets the driver and checks chilled items.\n- Side gate opens at 6:30 pm for the delivery.\n- Please use the rear entrance while the front ramp is repaired.\n- Sarah updates the printed rota; Imran puts the delivery notice by the sign-in sheet.",
        "Volunteer update:\n- Monday 12 October: Sarah covers the welcome desk; she will also update the printed rota.\n- Delivery now Wednesday 14 October (not Friday 16 October); Imran meets the driver, checks chilled items and posts the notice by the sign-in sheet.\n- Side gate opens at 6:30 pm for the delivery.\n- Please use the rear entrance while the front ramp is repaired.",
    ],
    "DVI004": [
        "Την Πέμπτη 24 Σεπτεμβρίου:\n- Β2: σχολάει στις 12:25.\n- Δ1: σχολάει στις 13:15 (εξαίρεση Τρίτης και Πέμπτης λόγω θεατρικής αγωγής).",
        "Την ίδια μέρα η παραλαβή γίνεται από την πλαϊνή είσοδο, στην οδό Σολωμού 18.",
    ],
}
