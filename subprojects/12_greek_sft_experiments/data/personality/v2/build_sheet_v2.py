#!/usr/bin/env python3
"""Build facts_greece_v2.json from v1 + sheet_data_1 (titles, rewrites, new facts) + sheet_data_2 (explain, related, events)."""
import json, os, sys, re
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H); import sheet_data_1 as d1, sheet_data_2 as d2
v1 = json.load(open(f'{H}/../facts_greece.json')); out = []
for f in v1:
    g = dict(f); g['title_el'] = d1.TITLES[f['id']]
    if f['id'] in d1.REWRITES: g['fact_el'] = d1.REWRITES[f['id']]
    if f['id'] in d2.EXPLAIN: g['explain_el'], g['related_el'] = d2.EXPLAIN[f['id']]
    if f['id'] in d2.EVENTS: g['events'] = d2.EVENTS[f['id']]
    out.append(g)
for nf in d1.NEW_FACTS:
    g = dict(nf)
    if g['id'] in d2.EVENTS: g['events'] = d2.EVENTS[g['id']]
    out.append(g)
names = [f['id'] for f in out if re.search(r'(στην Ελλάδα|της Ελλάδας|η Ελλάδα)', f['fact_el'])]
json.dump(out, open(f'{H}/facts_greece_v2.json', 'w'), ensure_ascii=False, indent=1)
print(f"{len(out)} facts; with explain {sum(1 for f in out if f.get('explain_el'))}, with events {sum(1 for f in out if f.get('events'))}, still naming the country in fact_el: {len(names)} {names}")
