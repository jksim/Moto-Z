#!/usr/bin/env python3
"""Stage 6: merge supplements, derive facets and compatibility, validate.

Captured Motorola specs win; supplement entries only add labels the capture
does not already carry.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import supplement
import taxonomy
import wayback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')

UNSAFE = re.compile(r'<script|on\w+\s*=|javascript:', re.I)

# Storefront furniture that the captured pages carry and a reference site
# should not. Matched as whole clauses so legitimate copy survives -- the
# Folio's "holds one credit card or ID" must not be touched by the credit rule.
STORE_CLAUSE = re.compile(
    r'(?i)\s*\b('
    r'free shipping'
    r'|financing available'
    r'|buy now|shop now|order now|add to cart|pre-?order now'
    r'|learn more|see details|view details'
    r'|while supplies last'
    r'|limited[- ]time offer'
    r'|in stock|out of stock'
    r'|\$\d[\d,.]*(\s*(off|/mo\.?|a month|per month))?'
    r'|save \$\d[\d,.]*'
    r'|budget pay( plan)?'
    r'|no interest if paid in full'
    r')\b[.!]?')

# Whole sentences that exist only to sell: bundled offers, stated values,
# trade-in and payment terms.
STORE_SENTENCE = re.compile(
    r'(?i)(\(\s*\$\d|you also get a free|when you (buy|trade|switch)'
    r'|trade[- ]in|device payment|apr\b|for only \$|value\s*\)|'
    r'exclusive(ly)? (from|through) \w+ for \$)')


WEIGHT = re.compile(r'(\d+(?:\.\d+)?)\s*g\b')
MAH = re.compile(r'(\d[\d,]*)\s*mAh', re.I)
DIMS = re.compile(r'(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*[x×]\s*'
                  r'(\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?)\s*mm')
INCH = re.compile(r'(\d+(?:\.\d+)?)\s*(?:"|in\b|inch)')


# Values that legitimately repeat across unrelated rows.
GENERIC_VALUES = {'yes', 'no', 'na', 'none', 'included', 'notincluded',
                  'standard', 'optional', 'builtin'}


def spec_key(value):
    return re.sub(r'[^a-z0-9]', '', (value or '').lower())


# Manufacturer and retailer names for the same fact.
LABEL_ALIASES = {
    'waterprotection': 'waterresistance',
    'speakerpower': 'audiopower',
    'batterysize': 'batterycapacity',
    'batterylife': 'batterylife',
    'lamplife': 'lamplife',
    'projectortechnology': 'displaysystem',
    'sensorresolution': 'resolution',
}


def label_key(label):
    """A label reduced so two names for one fact collide."""
    key = re.sub(r'[^a-z0-9]', '', (label or '').lower())
    key = re.sub(r'^(numberof|no)', '', key)
    key = re.sub(r'(range|rating|level|type)$', '', key)
    key = re.sub(r's$', '', key)
    key = LABEL_ALIASES.get(key, key)
    return re.sub(r's$', '', key)


def distinctive(value):
    key = spec_key(value)
    return len(key) >= 3 and key not in GENERIC_VALUES


def merge_specs(base, extra):
    """Add specs the table lacks, by label and by value.

    A retailer names the same fact differently -- "projector technology: DLP"
    and "Display System: DLP" -- so a label check alone leaves the table
    repeating itself. Generic values like "Yes" are exempt, since plenty of
    unrelated rows legitimately share them.
    """
    labels = {label_key(s['label']) for s in base}
    values = {spec_key(s['value']) for s in base if distinctive(s['value'])}
    out = list(base)
    for spec in extra:
        if label_key(spec['label']) in labels:
            continue
        key = spec_key(spec['value'])
        if distinctive(spec['value']) and any(key == v or key in v for v in values):
            continue
        out.append(spec)
        labels.add(label_key(spec['label']))
        if distinctive(spec['value']):
            values.add(key)
    return out


def facets(specs):
    out = {}
    blob = ' | '.join('{}: {}'.format(s['label'], s['value']) for s in specs)
    for spec in specs:
        label = spec['label'].lower()
        value = spec['value']
        if 'weight' in label and 'weightG' not in out:
            m = WEIGHT.search(value)
            if m:
                out['weightG'] = float(m.group(1))
        if 'dimension' in label and 'dimensionsMm' not in out:
            m = DIMS.search(value.replace(' ', ' '))
            if m:
                out['dimensionsMm'] = '{} x {} x {} mm'.format(*m.groups())
        if ('batter' in label or 'capacity' in label) and 'batteryMah' not in out:
            m = MAH.search(value)
            if m:
                out['batteryMah'] = int(m.group(1).replace(',', ''))
        if 'display' in label and 'displayIn' not in out:
            m = INCH.search(value)
            if m:
                out['displayIn'] = float(m.group(1))
    if 'batteryMah' not in out:
        m = MAH.search(blob)
        if m:
            out['batteryMah'] = int(m.group(1).replace(',', ''))
    return out


# Footnote markers Motorola and its retailers hang off claims. Superscript
# digits are included, but "moto z\u00b2" and "moto z\u00b3" are product names,
# not references, so they are protected first.
FOOTNOTE = re.compile(r'[\u2020\u2021\u00a7*\u00b9\u00b2\u00b3\u2074-\u2079\u2070]+')
MODEL_SUPER = re.compile(r'(?i)\bz([\u00b2\u00b3])')
# Private-use placeholders, so the footnote sweep cannot see the real glyphs.
GUARDS = {'\u00b2': '\uE002', '\u00b3': '\uE003'}


def strip_footnotes(value):
    out = MODEL_SUPER.sub(lambda m: 'z' + GUARDS[m.group(1)], value or '')
    out = FOOTNOTE.sub('', out)
    for glyph, guard in GUARDS.items():
        out = out.replace(guard, glyph)
    return out


def clean_text(value):
    """Strip storefront furniture and footnote markers, keeping the prose."""
    out = strip_footnotes(value or '')
    out = STORE_CLAUSE.sub(' ', out)
    out = re.sub(r'\s+', ' ', out)
    kept = [p for p in re.split(r'(?<=[.!?])\s+', out) if not STORE_SENTENCE.search(p)]
    out = ' '.join(kept)
    out = re.sub(r'\s+([.,;:])', r'\1', out)
    out = re.sub(r'([.,;:])\1+', r'\1', out)
    return out.strip(' .,;:\u2014-').strip() + ('.' if out.strip().endswith(('.', '!', '?')) else '')


def main():
    mods = wayback.load_json(os.path.join(DATA, 'mods.json'), [])
    phones = wayback.load_json(os.path.join(DATA, 'phones.json'), [])
    extras = wayback.load_json(os.path.join(DATA, 'supplement.json'), {})
    retail = wayback.load_json(os.path.join(DATA, 'bh.json'), {}) or {}

    problems = []
    edges = []

    # Motorola reused a few family slogans across unrelated products; a tagline
    # that shows up on several is boilerplate, not a description.
    counts = {}
    for rec in mods + phones:
        key = (rec.get('tagline') or '').strip().lower()
        if key:
            counts[key] = counts.get(key, 0) + 1
    boilerplate = {k for k, n in counts.items() if n >= 3}
    for rec in mods + phones:
        if (rec.get('tagline') or '').strip().lower() in boilerplate:
            rec['tagline'] = ''

    for rec in mods + phones:
        extra = extras.get(rec['slug'])
        if extra:
            rec['specs'] = merge_specs(rec['specs'], extra['specs'])
            if extra['source'] not in rec['sources']:
                rec['sources'].append(extra['source'])
        # A COPY entry is a deliberate replacement, not a fallback: it exists
        # because the captured copy is missing or not worth showing.
        copy = supplement.COPY.get(rec['slug'])
        if copy:
            rec['tagline'] = copy['tagline']
            rec['summary'] = copy['summary']
            rec['features'] = [{'title': t, 'body': b} for t, b in copy['features']]
            if copy['source'] not in rec['sources']:
                rec['sources'].append(copy['source'])
        # B&H described what each Mod actually is, where Motorola's copy sells
        # it. Keep both: Motorola's as the summary, B&H's as the detail, and
        # let B&H fill any spec the capture lacks.
        shop = retail.get(rec['slug'])
        rec['details'] = ''
        if shop:
            desc = shop.get('description') or ''
            # Some summaries already came from this same B&H copy; comparing
            # openings catches that without needing an exact match.
            def head(t):
                return re.sub(r'[^a-z0-9]', '', (t or '').lower())[:60]
            if desc and head(desc) != head(rec.get('summary')):
                rec['details'] = clean_text(desc)
            rec['specs'] = merge_specs(rec['specs'], shop.get('specs') or [])
            # B&H's titled features say something; its bare bullet lists just
            # restate the description, so only entries with a body are taken.
            have = {f['title'].strip().lower() for f in rec['features']}
            rec['features'] += [{'title': clean_text(f['title']),
                                 'body': clean_text(f['body'])}
                                for f in shop.get('features') or []
                                if f.get('body') and f['title'].strip().lower() not in have]
            if shop.get('url') and shop['url'] not in rec['sources']:
                rec['sources'].append(shop['url'])

        rec['awards'] = [dict(a) for a in supplement.AWARDS.get(rec['slug'], [])]
        for award in rec['awards']:
            if award['url'] not in rec['sources']:
                rec['sources'].append(award['url'])

        story = supplement.TIMELINE.get(rec['slug'])
        rec['timeline'] = ([{'date': d, 'event': e} for d, e in story['events']]
                           if story else [])
        if story and story['source'] not in rec['sources']:
            rec['sources'].append(story['source'])
        rec['summary'] = clean_text(rec.get('summary'))
        rec['tagline'] = clean_text(rec.get('tagline'))
        rec['features'] = [{'title': clean_text(f['title']),
                            'body': clean_text(f['body'])}
                           for f in rec.get('features', [])]
        rec['features'] = [f for f in rec['features'] if f['title']]
        rec['specs'] = [{'label': clean_text(s['label']),
                         'value': clean_text(s['value'])}
                        for s in rec['specs']]
        rec['specs'] = [s for s in rec['specs'] if s['value']]
        rec['facets'] = facets(rec['specs'])
        want = supplement.COVERS.get(rec['slug'])
        rec['coverKey'] = next(
            (i['key'] for i in rec['images']
             if want and i['key'].rsplit('/', 1)[-1].startswith(want)), '')
        rec['sources'] = [s for s in dict.fromkeys(rec['sources']) if s]

        for field in ('summary', 'tagline'):
            if UNSAFE.search(rec.get(field) or ''):
                problems.append('{}: unsafe html in {}'.format(rec['slug'], field))
        for feature in rec.get('features', []):
            if UNSAFE.search(feature.get('body', '')):
                problems.append('{}: unsafe html in feature'.format(rec['slug']))
        if not rec['specs']:
            problems.append('{}: no specs'.format(rec['slug']))
        if not rec['sources']:
            problems.append('{}: no sources'.format(rec['slug']))

    device_slugs = {p['slug'] for p in phones}
    unknown = set(taxonomy.DEVICES) - device_slugs
    if unknown:
        problems.append('taxonomy devices missing from data: {}'.format(sorted(unknown)))

    for mod in mods:
        mod['compatibleDevices'] = [d for d in taxonomy.compatible_devices(mod['slug'])
                                    if d in device_slugs]
        if not mod['compatibleDevices']:
            problems.append('{}: no compatible devices'.format(mod['slug']))
        for device in mod['compatibleDevices']:
            edges.append({'mod': mod['slug'], 'phone': device, 'fit': mod['fit']})

    by_device = {}
    for edge in edges:
        by_device.setdefault(edge['phone'], []).append(edge['mod'])
    for phone in phones:
        phone['compatibleMods'] = sorted(by_device.get(phone['slug'], []))

    wayback.save_json(os.path.join(DATA, 'mods.json'), mods)
    wayback.save_json(os.path.join(DATA, 'phones.json'), phones)
    wayback.save_json(os.path.join(DATA, 'compatibility.json'), edges)
    wayback.save_json(os.path.join(DATA, 'platform-awards.json'),
                      [dict(a) for a in supplement.PLATFORM_AWARDS])

    print('mods={} phones={} edges={}'.format(len(mods), len(phones), len(edges)))
    print('specs: min={} max={}'.format(
        min(len(r['specs']) for r in mods + phones),
        max(len(r['specs']) for r in mods + phones)))
    if problems:
        print('\nPROBLEMS')
        for p in problems:
            print('  ' + p)
        sys.exit(1)
    print('validation ok')


if __name__ == '__main__':
    main()
