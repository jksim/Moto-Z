#!/usr/bin/env python3
"""Stage 2: archived Drupal HTML -> data/mods.json + data/phones.json.

Offline and deterministic: the same input bytes always produce the same JSON.
All retained copy is sanitised here, not at render time.
"""

import os
import re
import sys

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import manifest
import taxonomy
import wayback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = os.path.join(ROOT, 'archive', 'pages')
DATA = os.path.join(ROOT, 'data')

DROP = ['script', 'style', 'noscript', 'iframe', 'form', 'svg']
ALLOWED_TAGS = {'p', 'br', 'strong', 'em', 'ul', 'ol', 'li'}
CTA = re.compile(r'^(buy now|learn more|add to cart|pre-?order|watch video|'
                 r'view full specifications|shop now|see details|compare)\.?$', re.I)
# The cross-sell block repeated on every product page.
BOILERPLATE = re.compile(r'^moto mods|movie projector, a boombox', re.I)
# Drupal's sentinel for an unavailable item; never a real number.
PRICE_SENTINEL = '99,999'


def text(node):
    if node is None:
        return ''
    return re.sub(r'\s+', ' ', node.get_text(' ', strip=True)).strip()


def clean_html(node):
    """Whitelist-sanitise a copy block. Returns a safe HTML string."""
    if node is None:
        return ''
    frag = BeautifulSoup(str(node), 'lxml')
    for tag in frag.find_all(True):
        if tag.name in DROP:
            tag.decompose()
    for tag in frag.find_all(True):
        if tag.name not in ALLOWED_TAGS:
            tag.unwrap()
        else:
            tag.attrs = {}
    out = re.sub(r'\s+', ' ', str(frag)).strip()
    out = re.sub(r'</?(html|body)>', '', out)
    return out.strip()


def field(soup, name, all_=False):
    sel = 'div.field-name-field-' + name
    return soup.select(sel) if all_ else soup.select_one(sel)


def spec_pairs(soup, kind):
    """Flatten the two visual spec columns into one ordered list."""
    out = []
    for side in ('lft', 'rgt'):
        block = field(soup, 'specifications-{}-{}'.format(kind, side))
        if not block:
            continue
        item = block.select_one('.field-item') or block
        label = None
        for child in item.find_all(['h5', 'h4', 'p', 'li'], recursive=True):
            value = text(child)
            if not value:
                continue
            if child.name in ('h5', 'h4'):
                label = value
            elif label:
                out.append({'label': label, 'value': value})
                label = None
    return out


def spec_views(soup):
    """The 2018/2019 templates: a values div paired with a nearby label div.

    Both eras use field-ps-display-label / field-ps-values but nest them
    differently, so pair each values block with the closest ancestor that also
    holds a label.
    """
    out = []
    for values in soup.select('.field-name-field-ps-values, .views-field-field-ps-values'):
        label = None
        node = values
        for _ in range(4):
            node = node.parent
            if node is None or node.name is None:
                break
            found = node.select_one('.field-name-field-ps-display-label,'
                                    ' .views-field-field-ps-display-label')
            if found is not None:
                label = text(found)
                break
        if not label:
            continue
        parts = [text(p) for p in values.find_all(['p', 'li'])] or [text(values)]
        value = '; '.join(p for p in parts if p)
        if value and not CTA.match(value):
            out.append({'label': label, 'value': value})

    seen, deduped = set(), []
    for pair in out:
        key = (pair['label'].lower(), pair['value'][:60].lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(pair)
    return deduped


GENERIC = {'moto', 'mods', 'mod', 'with', 'the', 'and', 'pack', 'edition',
           'gen', 'droid', 'unlocked', 'verizon', 'console', 'battery'}
CHROME = re.compile(r'/(logos|social-icons|quotes-logos|reviews|tech-specs-card|'
                    r'call_to_action|moto-maker|footer|icons)/|playbutton|'
                    r'chapter_icons|[-_]icon[-_]|mmlanding|-overlay\.|_quotes|'
                    r'swatch', re.I)
ROLES = [('hero', r'hero'), ('spec', r'spec'), ('feature', r'featgrid|feature|collage'),
         ('logo', r'logo|lockup')]

# Publication mastheads from the review-quote blocks. Matched on the filename
# only: the Moto Z4's shots live under an `awards/` directory but are real
# product photography.
PRESS = re.compile(r'(?i)^(cnet|mashable|forbes|engadget|wired|techradar|pcmag|'
                   r'gizmodo|networkworld|digitaltrends|androidcentral|tomsguide|'
                   r'theverge|verge)[-_.]|[-_](verge|cnet|engadget)_?logo')


def image_tail(url):
    m = re.search(r'(?:public|files)/(library/[^?]*)', url)
    return m.group(1) if m else ''


def tokens_for(slug):
    parts = [p for p in re.split(r'[-_]', slug) if len(p) > 2 and p not in GENERIC]
    return parts or [p for p in re.split(r'[-_]', slug) if p]


def images(soup, slug):
    """Product imagery only, de-duplicated per logical image, desktop preferred."""
    found = []
    for tag in soup.select('picture source[srcset], picture img[src], img[src]'):
        for raw in (tag.get('srcset') or tag.get('src') or '').split(','):
            url = raw.strip().split(' ')[0]
            if not url or 'sites/default/files' not in url or url.startswith('data:'):
                continue
            if '/advagg_' in url:
                continue
            if not url.startswith('http'):
                url = 'http://www.motorola.com' + url
            found.append(url.replace('&amp;', '&'))

    toks = tokens_for(slug)
    keep = {}
    for url in found:
        tail = image_tail(url)
        if not tail or CHROME.search(tail):
            continue
        low = tail.lower()
        if ('/' + slug + '/') not in low and not any(t in low for t in toks):
            continue
        name = low.rsplit('/', 1)[-1]
        if PRESS.search(name):
            continue
        # Collapse -d / -m / -t and -vzw variants of the same logical image.
        key = re.sub(r'[-_](d|m|t)((?:-[a-z]{2,4})*)(\.[a-z0-9]+)$', r'\3', name)
        key = re.sub(r'[-_]\dx(\.[a-z0-9]+)$', r'\1', key)
        # Vector assets on these pages are wordmarks and icons, never product
        # photography, so they never compete to represent a product.
        if name.endswith('.svg'):
            role = 'logo'
        else:
            role = 'gallery'
            for label, pattern in ROLES:
                if re.search(pattern, name):
                    role = label
                    break
        desktop = bool(re.search(r'[-_]d((?:-[a-z]{2,4})*)\.[a-z0-9]+$', name))
        entry = {'url': url, 'role': role, 'desktop': desktop}
        if key not in keep or (desktop and not keep[key]['desktop']):
            keep[key] = entry

    order = {'hero': 0, 'feature': 1, 'gallery': 2, 'spec': 3, 'logo': 4}
    out = sorted(keep.values(), key=lambda e: (order[e['role']], e['url']))
    return [{'url': e['url'], 'role': e['role']} for e in out]


def features(soup):
    out = []
    titles = field(soup, 'collage-title', all_=True)
    teasers = field(soup, 'collage-teaser', all_=True)
    for i, title_node in enumerate(titles):
        title = text(title_node)
        body = text(teasers[i]) if i < len(teasers) else ''
        if not title or CTA.match(title):
            continue
        if BOILERPLATE.match(title) or BOILERPLATE.search(body):
            continue
        out.append({'title': title, 'body': body})
    bullets = field(soup, 'bullet-features')
    if bullets:
        for li in bullets.select('li'):
            value = text(li)
            if value and not CTA.match(value):
                out.append({'title': value, 'body': ''})
    return out


def meta(soup, name):
    tag = soup.find('meta', attrs={'name': name})
    return re.sub(r'\s+', ' ', (tag.get('content') or '')).strip() if tag else ''


def parse(path, slug):
    html = open(path, encoding='utf-8', errors='replace').read()
    soup = BeautifulSoup(html, 'lxml')
    for tag in soup(DROP):
        tag.decompose()

    title = text(soup.title)
    name = re.split(r'\s*[|–-]\s*', title)[0].strip() if title else ''
    specs = (spec_pairs(soup, 'full') or spec_views(soup)
             or spec_pairs(soup, 'summary'))

    compat = ''
    for pair in specs:
        if re.match(r'compatib', pair['label'], re.I):
            compat = pair['value']

    return {
        'name_raw': name,
        'tagline': text(field(soup, 'feature-title')) or text(field(soup, 'slogan')),
        'summary': meta(soup, 'description'),
        'features': features(soup),
        'specs': [p for p in specs if PRICE_SENTINEL not in p['value']],
        'compatibility_raw': compat,
        'image_urls': images(soup, slug),
    }


def existing_images():
    out = {}
    for name in ('mods', 'phones'):
        for rec in wayback.load_json(os.path.join(DATA, name + '.json'), []) or []:
            if rec.get('images'):
                out[rec['slug']] = rec['images']
    return out


def main():
    index = wayback.load_json(os.path.join(ROOT, 'archive', 'index.json'), {})
    kept = existing_images()
    mods, phones = [], []

    for slug, name, brand, year in manifest.MODS:
        path = os.path.join(PAGES, 'mods', slug + '.html')
        # Products with no captured page are built from supplement alone;
        # normalize.py fails the build if nothing fills them in.
        rec = parse(path, slug) if os.path.exists(path) else {
            'name_raw': name, 'tagline': '', 'summary': '', 'features': [],
            'specs': [], 'compatibility_raw': '', 'image_urls': [],
        }
        cat, secondary = taxonomy.CATEGORY_OF[slug]
        mods.append({
            'id': slug, 'slug': slug, 'name': name, 'brand': brand, 'year': year,
            'category': cat, 'categorySecondary': secondary,
            'tagline': rec['tagline'], 'summary': rec['summary'],
            'features': rec['features'], 'specs': rec['specs'],
            'compatibilityRaw': rec['compatibility_raw'],
            'compatibleDevices': taxonomy.compatible_devices(slug),
            'fit': taxonomy.fit(slug),
            'relatedDocs': [{'title': t, 'url': u}
                            for t, u in taxonomy.RELATED_DOCS.get(cat, [])],
            'imageUrls': rec['image_urls'],
            'images': kept.get(slug, []),
            'sources': [index.get(slug, {}).get('url', '')],
        })

    grouped = {}
    for slug, record, name, family, gen, carrier, year in manifest.PHONES:
        path = os.path.join(PAGES, 'phones', slug + '.html')
        if not os.path.exists(path):
            continue
        rec = parse(path, slug)
        entry = grouped.setdefault(record, {
            'id': record, 'slug': record, 'name': name, 'family': family,
            'generation': gen, 'year': year, 'variants': [],
            'tagline': '', 'summary': '', 'features': [], 'specs': [],
            'imageUrls': [], 'images': kept.get(record, []), 'sources': [],
        })
        entry['variants'].append({'slug': slug, 'name': name, 'carrier': carrier})
        entry['sources'].append(index.get(slug, {}).get('url', ''))
        seen = {i['url'] for i in entry['imageUrls']}
        entry['imageUrls'] += [i for i in rec['image_urls'] if i['url'] not in seen]
        if len(rec['specs']) > len(entry['specs']):
            entry['specs'] = rec['specs']
        if len(rec['features']) > len(entry['features']):
            entry['features'] = rec['features']
        entry['tagline'] = entry['tagline'] or rec['tagline']
        entry['summary'] = entry['summary'] or rec['summary']

    phones = sorted(grouped.values(), key=lambda p: (p['year'], p['slug']))

    wayback.save_json(os.path.join(DATA, 'mods.json'), mods)
    wayback.save_json(os.path.join(DATA, 'phones.json'), phones)

    print('{:<40} {:>5} {:>5} {:>6}'.format('PRODUCT', 'SPECS', 'FEAT', 'IMGS'))
    print('-' * 62)
    for r in mods + phones:
        print('{:<40} {:>5} {:>5} {:>6}'.format(
            r['slug'][:39], len(r['specs']), len(r['features']), len(r['imageUrls'])))
    print('\nmods={} phones={}'.format(len(mods), len(phones)))


if __name__ == '__main__':
    main()
