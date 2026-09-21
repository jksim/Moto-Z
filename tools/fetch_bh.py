#!/usr/bin/env python3
"""Stage 5c: pull retailer product detail from B&H for Mods we already list.

B&H has run two page templates over the years, so both are handled: the older
one keys on class names (ov-desc-paragraph, specTopic), the current one on
data-selenium attributes and JSON-LD.

Motorola's captured copy sells the Mod; B&H described what it is, wrote a
titled feature list, and published a real spec table.

Pages come from the Wayback Machine rather than bhphotovideo.com: B&H is
behind a bot check that blocks scripted fetches, and the archived copies carry
the same markup.

This only enriches Mods already in the manifest, from hand-verified URLs in
supplement.BH_URLS. It does not search B&H or discover products.

Output: data/bh.json, merged by normalize.py.
"""

import html
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import supplement
import wayback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'bh.json')

SKIP_SECTIONS = {'packaging info'}
SKIP_LABELS = {'package weight', 'box dimensions (lxwxh)', 'upc'}


def text(fragment):
    out = re.sub(r'<[^>]+>', ' ', fragment or '')
    out = html.unescape(out).replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', out).strip()


UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')


def render(url):
    """Live page via headless Chrome, for products with no archived copy."""
    try:
        out = subprocess.run(
            ['google-chrome', '--headless', '--disable-gpu', '--no-sandbox',
             '--virtual-time-budget=25000', '--user-agent=' + UA, '--dump-dom', url],
            capture_output=True, timeout=200).stdout.decode('utf-8', 'replace')
    except Exception:
        return ''
    # The bot-check interstitial is small and titled "Just a moment...".
    return '' if len(out) < 60000 else out


def captures(url):
    rows = wayback.cdx(url, limit=40)
    return sorted(rows, key=lambda r: -r['length'])


def parse(page):
    """Name, description, titled features and specs from a B&H product page."""
    rec = {'name': '', 'description': '', 'features': [], 'specs': []}

    title = re.search(r'<title>(.*?)</title>', page, re.S)
    if title:
        rec['name'] = re.sub(r'\s*B&H Photo Video\s*$', '',
                             text(title.group(1))).strip()

    # The overview paragraph. `productDescription` is deliberately not used:
    # on some templates that class is the caption under the main image
    # ("Smartphone not included").
    para = re.search(r'(?is)<p[^>]*class="[^"]*ov-desc-paragraph[^"]*"[^>]*>(.*?)</p>', page)
    if not para:
        body = re.search(r'(?is)<div[^>]+class="[^"]*ov-desc[^"]*"[^>]*>(.*?)</div>', page)
        if body:
            para = re.search(r'(?is)<p[^>]*>(.*?)</p>', body.group(1))
    if para:
        rec['description'] = text(para.group(1))
    if not rec['description']:
        # Current template: the long description sits in the Product JSON-LD.
        for m in re.finditer(r'(?is)<script[^>]*application/ld\+json[^>]*>(.*?)</script>',
                             page):
            try:
                data = json.loads(m.group(1))
            except Exception:
                continue
            for item in (data if isinstance(data, list) else [data]):
                if isinstance(item, dict) and item.get('@type') == 'Product':
                    rec['name'] = rec['name'] or item.get('name') or ''
                    rec['description'] = text(item.get('description') or '')

    for m in re.finditer(r'(?is)<dt class="featureTitle">(.*?)</dt>\s*'
                         r'<dd[^>]*>(.*?)</dd>', page):
        title_, body_ = text(m.group(1)), text(m.group(2))
        if title_ and body_:
            rec['features'].append({'title': title_, 'body': body_})

    section = ''
    for m in re.finditer(r'(?is)<th[^>]*class="specHeader[^"]*"[^>]*>(.*?)</th>'
                         r'|<td[^>]*class="specTopic[^"]*"[^>]*>(.*?)</td>\s*'
                         r'<td[^>]*class="specDetail[^"]*"[^>]*>(.*?)</td>', page):
        if m.group(1) is not None:
            section = text(m.group(1)).lower()
            continue
        label, value = text(m.group(2)), text(m.group(3))
        if (section in SKIP_SECTIONS or label.lower() in SKIP_LABELS
                or not label or not value):
            continue
        rec['specs'].append({'label': label, 'value': value})

    if not rec['specs']:
        # Current template: hashed class names, but stable data-selenium hooks.
        for m in re.finditer(
                r'(?is)<td[^>]*data-selenium="specsItemGroupTableColumnLabel"[^>]*>(.*?)</td>'
                r'\s*<td[^>]*data-selenium="specsItemGroupTableColumnValue"[^>]*>(.*?)</td>',
                page):
            label, value = text(m.group(1)), text(m.group(2))
            if label and value and label.lower() not in SKIP_LABELS:
                rec['specs'].append({'label': label, 'value': value})
    return rec


def main():
    out = wayback.load_json(OUT, {}) or {}
    for slug, url in supplement.BH_URLS.items():
        have = out.get(slug, {})
        if have.get('description') and (have.get('specs') or have.get('features')):
            print('skip  {:<40} cached'.format(slug))
            continue
        rec = None
        pages = []
        for row in captures(url)[:3]:
            try:
                pages.append(wayback.fetch_capture(url, row['timestamp'])
                             .decode('utf-8', 'replace'))
            except Exception:
                continue
        for page in pages:
            rec = parse(page)
            if rec['description'] and rec['specs']:
                break
        if not (rec and rec['description'] and rec['specs']):
            live = render(url)
            if live:
                rec = parse(live)
        # A thin parse is worse than what may already be on file.
        if not rec or not rec['description'] or not (rec['specs'] or rec['features']):
            print('MISS  {:<40} no usable capture'.format(slug))
            continue
        rec['url'] = url
        out[slug] = rec
        print('ok    {:<40} {:>2} feat {:>2} specs  {}'.format(
            slug, len(rec['features']), len(rec['specs']), rec['name'][:38]))

    wayback.save_json(OUT, out)
    print('\nwritten: ' + OUT)


if __name__ == '__main__':
    main()
