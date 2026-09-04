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
    r"|ως (τεχνητή νοημοσύνη|γλωσσικό μοντέλο|μοντέλο τεχνητής)|είμαι (ένα |μια )?(τεχνητή νοημοσύνη|γλωσσικό μοντέλο))", re.I)
def identity_hit_messages(messages):
    """messages: list of {role, content}; True if any assistant or system turn carries an identity statement."""
    return any(m.get('role') in ('assistant', 'system') and IDENT.search(m.get('content') or '') for m in messages)
