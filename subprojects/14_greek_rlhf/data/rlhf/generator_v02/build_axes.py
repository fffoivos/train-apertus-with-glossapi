#!/usr/bin/env python3
"""Generator 0.2: build frozen value pools (people per language, situations, topics) with Sol, once. Resumable per pool.
Usage: python3 data/rlhf/generator_v02/build_axes.py"""
import concurrent.futures, json, pathlib, sys, hashlib
HERE = pathlib.Path(__file__).resolve().parent; AX = HERE / 'axes'; sys.path.insert(0, str(HERE.parents[1] / 'math'))
from codex_server import CodexServer
LANG = {'el': ('Greek', 'people living in Greece or Cyprus, or Greeks abroad', 160), 'en': ('English', 'people in the UK, Ireland, the US, Australia and elsewhere who write in English, including non-native speakers', 70),
        'fr': ('French', 'people in France, Belgium, Switzerland, Québec and francophone Africa', 30), 'de': ('German', 'people in Germany, Austria and Switzerland', 30),
        'es': ('Spanish', 'people in Spain and Latin America', 30), 'it': ('Italian', 'people in Italy and Italian-speaking Switzerland', 30), 'pt': ('Portuguese', 'people in Portugal, Brazil and lusophone Africa', 30)}
PEOPLE = """Write {n} distinct, realistic people who would type requests to an AI assistant in {lang}: {who}. Vary age (16–85), occupation (including manual work, care work, farming, unemployment, retirement, students, small business, public sector, professionals), region (cities, towns, villages, islands), education, family situation, digital skill and interests. Avoid clichés and famous people; no two entries alike. Each entry: a one-line English description with age, occupation, place and one characteristic detail. Return JSON {{"items": ["...", ...]}}."""
SITUATIONS = """Write 120 distinct everyday situations that make a person turn to an AI assistant at that moment. Cover work, study, family, health admin (not medical diagnosis), money, housing, travel, hobbies, bureaucracy, relationships, technology problems, community life, deadlines, curiosity, and moments of worry or boredom. Each entry: one short English line describing the moment, without naming a task type. No two alike. Return JSON {"items": ["...", ...]}."""
TOPICS = """Write 250 distinct concrete topics a person might ask an AI assistant about. Mix domains evenly: daily life and household, food, money and bills, work and careers, education, health administration and fitness (no diagnosis), law and bureaucracy (general), technology and devices, travel and transport, culture, history, language, science and nature, sport, arts, local community, environment, animals, crafts and DIY, gaming, parenting, ageing. About one fifth should be specific to Greece or Cyprus; the rest international. Each entry: 2–6 English words. No duplicates. Return JSON {"items": ["...", ...]}."""
SCHEMA = {'type': 'object', 'properties': {'items': {'type': 'array', 'items': {'type': 'string'}}}, 'required': ['items'], 'additionalProperties': False}
jobs = [(f'people_{l}', PEOPLE.format(n=n, lang=name, who=who)) for l, (name, who, n) in LANG.items()] + [('situations', SITUATIONS), ('topics', TOPICS)]
jobs = [(name, p) for name, p in jobs if not (AX / f'{name}.json').exists()]
srv = CodexServer(); srv.start()
def run(job):
    name, prompt = job
    for _ in range(3):
        try:
            v = srv.call(prompt, SCHEMA, model='gpt-5.6-sol', effort='medium', timeout=900); items = list(dict.fromkeys(x.strip() for x in v['items'] if x.strip()))
            json.dump({'name': name, 'prompt_sha16': hashlib.sha256(prompt.encode()).hexdigest()[:16], 'count': len(items), 'items': items}, open(AX / f'{name}.json', 'w'), ensure_ascii=False, indent=1)
            return name, len(items)
        except Exception as e: err = str(e)[:200]
    return name, 'ERROR ' + err
with concurrent.futures.ThreadPoolExecutor(9) as ex:
    for name, n in ex.map(run, jobs): print(name, n, flush=True)
srv.close(); print('AXES_DONE')
