#!/usr/bin/env python3
"""Stage 5b: fill spec gaps from secondary sources.

Motorola's captures carry no spec table for a few products. Device specs come
from Wikipedia infoboxes; the remaining Mods come from tools/supplement.py.
Output: data/supplement.json, merged by normalize.py with captures winning.
"""

import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import supplement
import wayback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'supplement.json')
API = 'https://en.wikipedia.org/w/api.php'

# Device record slug -> Wikipedia article.
WIKI_PAGES = {
    'moto-z3': 'Moto Z3',
    'moto-z3-play': 'Moto Z3 Play',
    'moto-z4': 'Moto Z4',
}

# Infobox key -> display label, in the order the spec table should read.
INFOBOX_FIELDS = [
    ('released', 'Released'), ('os', 'Operating system'),
    ('soc', 'Chipset'), ('cpu', 'Processor'), ('gpu', 'GPU'),
    ('memory', 'Memory (RAM)'), ('storage', 'Storage'),
    ('memory_card', 'Expandable storage'), ('display', 'Display'),
    ('rear_camera', 'Rear camera'), ('front_camera', 'Front camera'),
    ('battery', 'Battery'), ('dimensions', 'Dimensions'), ('weight', 'Weight'),
    ('connectivity', 'Connectivity'), ('model_number', 'Model number'),
]

MONTHS = ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']


def clean_wikitext(value):
    """Reduce an infobox value to readable plain text."""
    value = re.sub(r'<ref[^>]*?/>|<ref.*?</ref>', '', value, flags=re.S)

    def start_date(m):
        parts = [p for p in m.group(1).split('|') if p.strip().isdigit()]
        if len(parts) >= 2:
            return '{} {}'.format(MONTHS[int(parts[1])], parts[0])
        return parts[0] if parts else ''

    value = re.sub(r'\{\{\s*Start date\s*\|([^}]*)\}\}', start_date, value, flags=re.I)
    # {{convert|6.01|in|mm}} / {{cvt|156|g|oz}} -> "6.01 in"
    value = re.sub(r'\{\{\s*(?:convert|cvt)\s*\|([\d.]+)\|([a-zA-Z]+)[^}]*\}\}',
                   r'\1 \2', value, flags=re.I)
    value = re.sub(r'\{\{\s*resx\s*\|([^}]*)\}\}', r'\1', value, flags=re.I)
    value = re.sub(r'\{\{\s*Collapsible list\s*\|\s*title\s*=[^|]*', '', value, flags=re.I)
    value = re.sub(r'\{\{[^}|]*\|([^}]*)\}\}', r'\1', value)
    value = re.sub(r'\{\{|\}\}', '', value)
    value = re.sub(r'\[\[[^|\]]*\|([^\]]*)\]\]', r'\1', value)
    value = re.sub(r'\[\[|\]\]', '', value)
    value = re.sub(r"'''|''", '', value)
    value = re.sub(r'<br\s*/?>', ', ', value, flags=re.I)
    value = re.sub(r'<[^>]+>', '', value)
    value = value.replace('&nbsp;', ' ').replace('nbsp', ' ')
    value = value.replace('&times;', '×').replace('|', ', ')
    value = re.sub(r'\s*,\s*(,\s*)+', ', ', value)
    value = re.sub(r'\s+', ' ', value).strip(' ,')
    return value


def infobox(wikitext):
    m = re.search(r'\{\{Infobox(.*?)\n\}\}', wikitext, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).split('\n|')[1:]:
        key, _, value = line.partition('=')
        key = key.strip().lower()
        value = clean_wikitext(value)
        if key and value:
            out[key] = value
    return out


def wikipedia(title):
    url = (API + '?action=parse&prop=wikitext&format=json&redirects=1&page='
           + urllib.parse.quote(title))
    raw = wayback.fetch(url).decode('utf-8', 'replace')
    data = json.loads(raw)
    if 'error' in data:
        return None, None
    page = data['parse']
    return page['title'], page['wikitext']['*']


def main():
    out = {}

    for slug, title in WIKI_PAGES.items():
        name, wikitext = wikipedia(title)
        if not wikitext:
            print('FAIL  {:<16} {}'.format(slug, title))
            continue
        box = infobox(wikitext)
        specs = [{'label': label, 'value': box[key]}
                 for key, label in INFOBOX_FIELDS if box.get(key)]
        out[slug] = {
            'specs': specs,
            'source': 'https://en.wikipedia.org/wiki/' + name.replace(' ', '_'),
        }
        print('ok    {:<16} {:>2} specs  <- {}'.format(slug, len(specs), name))

    for slug, entry in supplement.SPECS.items():
        out[slug] = {
            'specs': [{'label': k, 'value': v} for k, v in entry['specs']],
            'source': entry['source'],
        }
        print('ok    {:<16} {:>2} specs  <- curated'.format(slug, len(entry['specs'])))

    wayback.save_json(OUT, out)
    print('\nwritten: ' + OUT)


if __name__ == '__main__':
    main()
