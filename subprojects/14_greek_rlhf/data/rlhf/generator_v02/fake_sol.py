"""Deterministic fake Sol for offline tests of generate.py (no network)."""
import json, re
class FakeSol:
    def call(self, prompt, schema, model=None, effort=None, timeout=None):
        props = schema['properties']['items']['items']['properties']
        m = re.search(r'(SLOTS|ITEMS):\n(.*)$', prompt, re.S); items = json.loads(m.group(2))
        out = []
        for it in items:
            sid = it['slot_id']
            if 'task_summary' in props and 'givens' in props:
                w = ''.join(chr(97 + (ord(ch) * 7 + i * 3) % 26) for i, ch in enumerate(sid * 2)); out.append(dict(slot_id=sid, scenario=f'{w[:6]} {w[6:12]}', task_summary=f'{w[:8]} {w[4:12]} {w[8:14]}', givens=[f'{w[2:9]} 42'], constraints=[{'type': 'count', 'params': '3', 'text': 'exactly 3 items'}], packet='', deliverable='result only', ambiguity='none', maths_content='none', check_values=['42'], answer_conditions='mentions 42'))
            elif 'story' in props:
                lang = it['language']; words = {'Greek': 'Χρειάζομαι βοήθεια με το 42 γρήγορα', 'English': 'I need help with 42 quickly', 'French': 'J’ai besoin d’aide avec 42', 'German': 'Ich brauche Hilfe mit 42', 'Spanish': 'Necesito ayuda con 42', 'Italian': 'Ho bisogno di aiuto con 42', 'Portuguese': 'Preciso de ajuda com 42'}[lang]
                if it['register'] == 'greeklish': words = 'Xreiazomai voitheia me to 42 grigora'
                out.append(dict(slot_id=sid, story='A person.', message=words + ' ' + sid[-2:], pasted_span=''))
            else:
                out.append({'slot_id': sid, 'pass': True, 'reasons': [], 'note': 'ok'})
        return {'items': out}
    def close(self): pass
