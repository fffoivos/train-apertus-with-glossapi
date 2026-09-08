#!/usr/bin/env python3
"""Long, escalating Greek dialogues against a local MLX checkpoint: a scripted picky user asks for something, then keeps adding
constraints turn after turn, until the conversation passes the 4,096-token training length. Records every turn with prompt-token
counts, checks the checkable constraints, and writes a transcript reader.
NOT run by Claude on the owner's laptop (owner, 2026-09-08: "do some tests without loading the model"); ready for the owner.
Usage: python3 picky_dialogues.py --model ~/models/greek-apertus-8b-sft-r2-idB-8bit --out results/dialogues_idB [--max-turns 18] [--dialogue trip|letter|history|recipe|all]
Requires the apertus-local-chat venv (mlx_lm). Greedy decoding (temp 0) so runs are reproducible."""
import argparse, json, os, re, time, html

DIALOGUES = {
 'trip': [
  "Θέλω να οργανώσω ένα τριήμερο στη Νάξο τον Σεπτέμβριο για δύο άτομα. Πρότεινέ μου ένα πρόγραμμα.",
  "Ωραία, αλλά χωρίς ενοικίαση αυτοκινήτου, μόνο με ΚΤΕΛ και περπάτημα. Ξαναγράψε το πρόγραμμα.",
  "Πρόσθεσε για κάθε μέρα ένα εστιατόριο με τοπική κουζίνα και πες τι να παραγγείλουμε. Κράτα το κάθε γεύμα σε μία πρόταση.",
  "Η συνοδός μου δεν τρώει γλουτένη. Διόρθωσε τις προτάσεις φαγητού και σημείωσε δίπλα σε καθεμία «χωρίς γλουτένη» ή «ρώτα το μαγαζί».",
  "Θέλω το πρόγραμμα ως λίστα με ώρες (π.χ. 09:00), όχι παραγράφους, και όχι πάνω από 12 γραμμές συνολικά.",
  "Πρόσθεσε στο τέλος μια εκτίμηση κόστους ανά ημέρα σε ευρώ, με σύνολο, χωρίς τα εισιτήρια του πλοίου.",
  "Τώρα γράψε το ίδιο πρόγραμμα ξανά αλλά στον πληθυντικό ευγενείας, σαν να το στέλνει τουριστικό γραφείο σε πελάτη.",
  "Μην χρησιμοποιήσεις καθόλου τη λέξη «όμορφος» ή παράγωγά της σε όλη την απάντηση. Ξαναγράψε.",
  "Γράψε τα ίδια χωρίς τόνους (ατονικά), σε όλη την απάντηση.",
  "Τώρα σε 3 ακριβώς προτάσεις, συνόψισε το πρόγραμμα, με τόνους κανονικά.",
  "Πες μου ποιες από τις προηγούμενες απαιτήσεις μου παραβίασες κάπου, με ειλικρίνεια, σε λίστα.",
  "Μετάφρασε τη σύνοψη των 3 προτάσεων στα αγγλικά, χωρίς να αλλάξεις τίποτα άλλο.",
  "Δώσε μου τώρα την πλήρη τελική εκδοχή του προγράμματος: λίστα με ώρες, πληθυντικός ευγενείας, χωρίς «όμορφος», με τα γεύματα χωρίς γλουτένη σημειωμένα, με κόστος ανά ημέρα και σύνολο, όχι πάνω από 15 γραμμές.",
  "Πόσες γραμμές είχε η τελευταία σου απάντηση; Απάντησε μόνο με τον αριθμό.",
  "Τι μέρος της Ελλάδας είναι η Νάξος και πόσο μακριά είναι από τον Πειραιά με το πλοίο; Μία πρόταση.",
  "Ποιος είσαι και ποιος σε έφτιαξε; Μία πρόταση.",
 ],
 'letter': [
  "Γράψε μου μια επιστολή προς τον δήμο μου για μια λακκούβα στον δρόμο μου που έχει προκαλέσει ζημιά στο αυτοκίνητό μου.",
  "Να είναι σε επίσημο ύφος, πληθυντικός ευγενείας παντού, και να μην ξεπερνά τις 150 λέξεις.",
  "Πρόσθεσε ότι το περιστατικό έγινε στις 3 Σεπτεμβρίου στην οδό Αγίου Δημητρίου 14 και ότι έχω φωτογραφίες και απόδειξη συνεργείου 240 ευρώ.",
  "Ζήτα ρητά αποζημίωση και θέσε προθεσμία απάντησης 30 ημερών, με αναφορά στον Κώδικα Διοικητικής Διαδικασίας.",
  "Βάλε θέμα (Θέμα: …) στην αρχή και τα στοιχεία μου ως κενά σε αγκύλες στο τέλος, χωρίς να επινοήσεις όνομα.",
  "Μην χρησιμοποιήσεις τη λέξη «παρακαλώ» πουθενά. Ξαναγράψε ολόκληρη την επιστολή.",
  "Κάνε την πιο σύντομη: το πολύ 100 λέξεις, κρατώντας θέμα, ημερομηνία, διεύθυνση, ποσό, προθεσμία και νομική αναφορά.",
  "Γράψε την ίδια επιστολή σε δεύτερη εκδοχή προς τον Συνήγορο του Πολίτη, με μία παράγραφο που εξηγεί ότι ο δήμος δεν απάντησε εγκαίρως.",
  "Μέτρησε τις λέξεις της εκδοχής προς τον δήμο και πες μου τον αριθμό. Μόνο τον αριθμό.",
  "Γράψε την επιστολή προς τον δήμο σε greeklish, χωρίς ελληνικούς χαρακτήρες.",
  "Τώρα ξανά στα ελληνικά, με τόνους, και με κάθε πρόταση να ξεκινά με κεφαλαίο γράμμα και να τελειώνει με τελεία· καμία ερώτηση, καμία παρένθεση.",
  "Ποιες απαιτήσεις μου δεν τήρησες μέχρι τώρα; Λίστα, ειλικρινά.",
  "Δώσε μου την τελική επιστολή προς τον δήμο: επίσημη, χωρίς «παρακαλώ», με θέμα, ημερομηνία, διεύθυνση, 240 ευρώ, προθεσμία 30 ημερών, νομική αναφορά, το πολύ 100 λέξεις, χωρίς παρενθέσεις.",
  "Σε ποιον οργανισμό μπορώ να απευθυνθώ αν ο δήμος δεν απαντήσει, και ποιο είναι το σωστό όνομά του; Μία πρόταση.",
 ],
 'history': [
  "Εξήγησέ μου τι ήταν το κίνημα του Πολυτεχνείου το 1973, για παιδί δημοτικού.",
  "Τώρα το ίδιο για μαθητή λυκείου που ετοιμάζεται για εξετάσεις: με ημερομηνίες, ονόματα και αιτίες.",
  "Πρόσθεσε τι έγινε αμέσως μετά, μέχρι τη μεταπολίτευση, σε χρονολόγιο με μία γραμμή ανά γεγονός.",
  "Γράψε το χρονολόγιο χωρίς κανένα επίθετο.",
  "Τι σχέση έχει η 17η Νοεμβρίου με τα σχολεία σήμερα; Δύο προτάσεις.",
  "Διόρθωσέ με: το Πολυτεχνείο έγινε το 1974, σωστά;",
  "Γράψε ένα κείμενο 5 προτάσεων για ξένο φίλο μου που δεν ξέρει τίποτα για την Ελλάδα, στα ελληνικά, χωρίς ακρωνύμια.",
  "Μετάφρασέ το στα αγγλικά, διατηρώντας ακριβώς 5 προτάσεις.",
  "Ποιες ήταν οι τρεις κύριες πηγές αντίδρασης στη χούντα πριν το Πολυτεχνείο; Λίστα με 3 σημεία, το καθένα μέχρι 12 λέξεις.",
  "Γράψε το χρονολόγιο ξανά, ατονικά, χωρίς επίθετα, με μία γραμμή ανά γεγονός.",
  "Ποιες από τις οδηγίες μου παραβίασες μέχρι τώρα; Λίστα.",
  "Τελική εκδοχή: το χρονολόγιο με τόνους, χωρίς επίθετα, μία γραμμή ανά γεγονός, όχι πάνω από 8 γραμμές, και μετά μία πρόταση για τη σημασία του σήμερα.",
  "Πόσα τετραγωνικά χιλιόμετρα είναι η χώρα μας; Μία πρόταση.",
 ],
 'recipe': [
  "Δώσε μου μια συνταγή για φασολάδα για 4 άτομα.",
  "Χωρίς κρεμμύδι, με σέλινο, και σε βήματα αριθμημένα.",
  "Πρόσθεσε ποσότητες σε γραμμάρια για όλα τα υλικά, όχι σε φλιτζάνια.",
  "Θέλω να γίνεται σε χύτρα ταχύτητας. Προσάρμοσε τους χρόνους.",
  "Κάνε τη συνταγή για 10 άτομα, με τις ποσότητες ξανά υπολογισμένες.",
  "Γράψε τα υλικά ως πίνακα markdown με δύο στήλες: υλικό, γραμμάρια.",
  "Μην χρησιμοποιήσεις καθόλου τη λέξη «λάδι»· πες «ελαιόλαδο» παντού. Ξαναγράψε ολόκληρη τη συνταγή.",
  "Πρόσθεσε ένα βήμα για σερβίρισμα με ελιές και φέτα και πες πόσα γραμμάρια φέτα ανά άτομο.",
  "Ποιο είναι το κόστος περίπου σε ευρώ για τα 10 άτομα, με τιμές σούπερ μάρκετ; Μόνο ένα νούμερο και μία πρόταση επιφύλαξης.",
  "Γράψε τη συνταγή σε 6 ακριβώς βήματα, με τον πίνακα υλικών, για 10 άτομα, με «ελαιόλαδο», χωρίς κρεμμύδι, σε χύτρα.",
  "Ποιες από τις οδηγίες μου παραβίασες; Λίστα, ειλικρινά.",
  "Πες μου με μία πρόταση από πού κατάγεται η φασολάδα και γιατί λέγεται «εθνικό φαγητό».",
 ],
}

def checks(turn_idx, user, answer, dialogue):
    """Checkable constraints per turn; returns list of (name, ok)."""
    out = []
    u = user
    if 'χωρίς τόνους' in u or 'ατονικά' in u or 'ατονικα' in u: out.append(('no accents', not re.search(r'[άέήίόύώΆΈΉΊΌΎΏ]', answer)))
    if 'greeklish' in u and 'χωρίς ελληνικούς' in u: out.append(('no greek script', not re.search(r'[α-ωΑ-Ω]', answer)))
    m = re.search(r'το πολύ (\d+) λέξεις|(?:δεν|μην) ξεπερνά τις (\d+) λέξεις', u)
    if m: n = int(m.group(1) or m.group(2)); out.append((f'≤{n} words', len(answer.split()) <= n))
    m = re.search(r'όχι πάνω από (\d+) γραμμές', u)
    if m: n = int(m.group(1)); out.append((f'≤{n} lines', len([l for l in answer.splitlines() if l.strip()]) <= n))
    m = re.search(r'(\d+) ακριβώς (προτάσεις|βήματα)|ακριβώς (\d+) προτάσεις', u)
    if m:
        n = int(m.group(1) or m.group(3)); kind = m.group(2) or 'προτάσεις'
        if kind.startswith('προτ'): out.append((f'={n} sentences', len([s for s in re.split(r'[.;!·]\s', answer.strip()) if s.strip()]) == n))
        else: out.append((f'={n} steps', len(re.findall(r'^\s*\d+[.)]', answer, re.M)) == n))
    for w, label in [('«όμορφος»', 'no όμορφ'), ('«παρακαλώ»', 'no παρακαλώ'), ('«λάδι»', 'no bare λάδι')]:
        if w in u:
            if label == 'no bare λάδι': out.append((label, not re.search(r'(?<!ελαιό)λάδι', answer)))
            elif label == 'no όμορφ': out.append((label, not re.search(r'όμορφ|ομορφ', answer, re.I)))
            else: out.append((label, 'παρακαλ' not in answer.lower()))
    if 'χωρίς κανένα επίθετο' in u or 'χωρίς επίθετα' in u: out.append(('few adjectives (heuristic)', len(re.findall(r'\w+(ικός|ική|ικό|ικοί|ικές|ικά|αίος|αία|αίο)\b', answer)) <= 2))
    if 'Απάντησε μόνο με τον αριθμό' in u or 'Μόνο τον αριθμό' in u: out.append(('number only', bool(re.fullmatch(r'\s*\d+\s*\.?\s*', answer))))
    if 'στα αγγλικά' in u: out.append(('english', not re.search(r'[α-ωΑ-Ω]{4,}', answer)))
    if 'πληθυντικό ευγενείας' in u: out.append(('formal plural (heuristic)', bool(re.search(r'\b(σας|εσείς|μπορείτε|θα βρείτε|θα δείτε)\b', answer))))
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--model', required=True); ap.add_argument('--out', required=True); ap.add_argument('--max-turns', type=int, default=18)
    ap.add_argument('--dialogue', default='all'); ap.add_argument('--max-tokens', type=int, default=700); a = ap.parse_args()
    from mlx_lm import load, generate
    from mlx_lm.sample_utils import make_sampler
    model, tok = load(a.model); sampler = make_sampler(temp=0.0); os.makedirs(a.out, exist_ok=True)
    names = list(DIALOGUES) if a.dialogue == 'all' else [a.dialogue]
    summary = []
    for name in names:
        msgs = []; log = []
        for i, user in enumerate(DIALOGUES[name][:a.max_turns]):
            msgs.append({'role': 'user', 'content': user})
            prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True); n_prompt = len(tok.encode(prompt))
            t = time.time(); ans = generate(model, tok, prompt=prompt, max_tokens=a.max_tokens, sampler=sampler, verbose=False); dt = time.time() - t
            ans = ans.replace('<|assistant_end|>', '').strip(); msgs.append({'role': 'assistant', 'content': ans})
            ck = checks(i, user, ans, name)
            log.append(dict(turn=i + 1, user=user, answer=ans, prompt_tokens=n_prompt, answer_tokens=len(tok.encode(ans)), seconds=round(dt, 1), checks=ck, past_4096=n_prompt > 4096))
            print(f'[{name} {i+1}] prompt {n_prompt} tok, answer {len(tok.encode(ans))} tok, {dt:.0f}s, checks {sum(1 for _,o in ck if o)}/{len(ck)}' + (' PAST 4096' if n_prompt > 4096 else ''), flush=True)
        json.dump(log, open(f'{a.out}/{name}.json', 'w'), ensure_ascii=False, indent=1)
        summary.append(dict(dialogue=name, turns=len(log), max_prompt_tokens=max(l['prompt_tokens'] for l in log), turns_past_4096=sum(l['past_4096'] for l in log), checks_ok=sum(1 for l in log for _, o in l['checks'] if o), checks_total=sum(len(l['checks']) for l in log)))
    json.dump(summary, open(f'{a.out}/summary.json', 'w'), ensure_ascii=False, indent=1); print(json.dumps(summary, ensure_ascii=False))
    write_reader(a.out, names)

def write_reader(out, names):
    e = lambda s: html.escape(str(s))
    body = ''
    for name in names:
        log = json.load(open(f'{out}/{name}.json'))
        body += f'<h2>{e(name)} <span class="n">{len(log)} turns · max prompt {max(l["prompt_tokens"] for l in log)} tokens</span></h2>'
        for l in log:
            ck = ' '.join(f'<span class="ck {"ok" if o else "bad"}">{e(n)}</span>' for n, o in l['checks'])
            body += f'<article class="{"past" if l["past_4096"] else ""}"><div class="meta">turn {l["turn"]} · prompt {l["prompt_tokens"]} tok · answer {l["answer_tokens"]} tok · {l["seconds"]} s {"· PAST 4096" if l["past_4096"] else ""}</div><p class="u">{e(l["user"])}</p><div class="a">{e(l["answer"])}</div><div class="cks">{ck}</div></article>'
    page = f'''<title>Picky Dialogues</title><style>body{{font-family:"Source Sans 3",-apple-system,sans-serif;max-width:1000px;margin:0 auto;padding:2rem 1rem;line-height:1.5;color:#14202B;background:#F4F6F8}}h2{{font-family:Georgia,serif;font-weight:500;margin-top:2rem;border-top:1px solid #D5DCE3;padding-top:.8rem}}.n{{font-family:ui-monospace,monospace;font-size:.85rem;color:#5B6B78}}article{{background:#fff;border:1px solid #D5DCE3;border-radius:4px;padding:.7rem 1rem;margin:.7rem 0}}article.past{{border-left:4px solid #B4462B}}.meta{{font-family:ui-monospace,monospace;font-size:.75rem;color:#5B6B78}}.u{{font-weight:600;margin:.4rem 0}}.a{{white-space:pre-wrap;background:#E9EFF4;padding:.5rem .7rem;border-radius:3px;font-size:.95rem}}.ck{{display:inline-block;font-size:.72rem;padding:.1em .5em;border-radius:2px;margin:.3rem .3rem 0 0;color:#fff}}.ck.ok{{background:#3F7D3A}}.ck.bad{{background:#B4462B}}</style>
<h1>Picky dialogues: escalating constraints past the 4,096-token training length</h1><p class="n">Greedy decoding. Red left border = the prompt exceeded 4,096 tokens. Green/red chips = automatic checks of the checkable constraints; everything else needs a human read.</p>{body}'''
    open(f'{out}/reader.html', 'w').write(page); print('reader', f'{out}/reader.html')

if __name__ == '__main__': main()
