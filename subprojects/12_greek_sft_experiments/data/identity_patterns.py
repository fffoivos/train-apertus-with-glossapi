"""One shared identity pattern set (review R8) for the assembly backstop and the lexicon filter. English, French, German, Italian,
Spanish, Portuguese, Greek. Scans assistant AND system turns."""
import re
IDENT = re.compile(
    r"\b(as an? (ai|artificial intelligence|language model|large language model|llm|virtual assistant|ai assistant|ai language model|chatbot)"
    r"|i am an? (ai|artificial intelligence|language model|large language model|llm|ai assistant|chatbot)"
    r"|i'm an? (ai|artificial intelligence|language model|large language model|llm|ai assistant|chatbot)"
    r"|i'm just an? (ai|language model|chatbot|assistant)|i am just an? (ai|language model|chatbot)"
    r"|i (do not|don't) have (personal )?(feelings|opinions|emotions|experiences|beliefs|preferences)"
    r"|i'm (chatgpt|claude|gemini|llama|olmo|gpt-4|gpt-3)|i am (chatgpt|claude|gemini|llama|olmo)"
    r"|my (training|knowledge) (data|cutoff)|knowledge cutoff|i (do not|don't) have (access to )?real[- ]time|i cannot browse the internet"
    r"|i (do not|don't) have the ability to (browse|access)|i am not able to access|i was (trained|created|developed) by"
    r"|developed by (openai|anthropic|google|meta|ai2|the allen institute|allen institute|mistral|nvidia|zhipu|z\.ai)|allen institute for ai|\bai2\b"
    r"|en tant qu'?(ia|intelligence artificielle|modèle de langage|assistant ia)|je suis un(e)? (ia|intelligence artificielle|modèle de langage)"
    r"|als (ki|künstliche intelligenz|sprachmodell|ki-assistent|ki-sprachmodell)|ich bin (eine? )?(ki|künstliche intelligenz|sprachmodell)"
    r"|come (ia|intelligenza artificiale|modello linguistico)|sono un(a)? (ia|intelligenza artificiale|modello linguistico)"
    r"|como (ia|inteligencia artificial|modelo de lenguaje|modelo de linguagem)|soy un(a)? (ia|inteligencia artificial|modelo de lenguaje)|sou um(a)? (ia|inteligência artificial|modelo de linguagem)"
    r"|ως (τεχνητή νοημοσύνη|γλωσσικό μοντέλο|μοντέλο τεχνητής)|είμαι (ένα |μια )?(τεχνητή νοημοσύνη|γλωσσικό μοντέλο))\b", re.I)  # trailing word boundary (review S1): no "as an aid", "als Kind"
def identity_hit_messages(messages):
    """messages: list of {role, content}; True if any assistant or system turn carries an identity statement."""
    return any(m.get('role') in ('assistant', 'system') and IDENT.search(m.get('content') or '') for m in messages)

# Broad first-person self-description (review of Luna's identity verdicts, Saturday 5 Sep): the judge's "identity" frame fires on rows with
# no self-reference at all (kayfabe explanations, book summaries, persona interviews). An identity DROP is honoured only when the
# assistant/system text carries a self-description: the strict IDENT above or one of these first-person capability/identity phrases.
BROAD_IDENT = re.compile(
    r"(?i)\b(as an? (ai|assistant|language model|chatbot|bot|machine|virtual assistant)|i am an? (ai|assistant|language model|chatbot|bot|machine)"
    r"|i'?m an? (ai|assistant|language model|chatbot|bot)|i (do not|don't|cannot|can't) (browse|access|see|view|open|watch|listen|feel|have (personal|feelings|emotions|opinions|a body|real[- ]time|access|the ability))"
    r"|my (training|knowledge|programming|creators?|developers?)|i was (trained|programmed|designed|built)|not able to (browse|access|see|view)|as a (large )?language model|i lack (the ability|access)|i'?m not (able|capable) of"
    r"|ως (τεχνητή νοημοσύνη|γλωσσικό μοντέλο|μοντέλο|βοηθός|ψηφιακός βοηθός|ai)|είμαι (ένα |μια |ένας )?(τεχνητή|γλωσσικό|μοντέλο|βοηθός|ai|chatbot|πρόγραμμα)"
    r"|δεν (έχω|διαθέτω) (προσωπικ|συναισθήματα|πρόσβαση|τη δυνατότητα)|δεν μπορώ να (περιηγηθώ|έχω πρόσβαση|δω|ακούσω)|δημιουργήθηκα|εκπαιδεύτηκα)")
def identity_phrase_hit(messages):
    """True if any assistant or system turn carries a self-description (strict IDENT or BROAD_IDENT)."""
    return any(m.get('role') in ('assistant', 'system') and (IDENT.search(m.get('content') or '') or BROAD_IDENT.search(m.get('content') or '')) for m in messages)

MANNERISM_OPEN = re.compile(r"^\s*(sure|certainly|absolutely|of course|great question|good question|excellent question|great|awesome|fantastic|wonderful)\b[!,.:]?", re.I)
MANNERISM_CLOSE = re.compile(r"(i hope this helps|hope this helps|let me know if you (need|have|would like|want)|feel free to (ask|reach out|let me know)|happy to help|is there anything else|if you have any (other|further|more) questions)[^\n]{0,60}\s*$", re.I)
def mannerism_hit_messages(messages):
    """True if the LAST assistant turn opens with a chatbot opener or closes with a chatbot closer (cheap lexicon, all blocks)."""
    for m in reversed(messages):
        if m.get('role') == 'assistant':
            c = (m.get('content') or '').strip()
            return bool(MANNERISM_OPEN.match(c)) or bool(MANNERISM_CLOSE.search(c[-300:]))
    return False
