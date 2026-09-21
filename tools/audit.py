#!/usr/bin/env python3
"""Phase 0: pick the best capture for every product and report what it contains.

For each target it ranks captures (Drupal era first, then largest byte length),
fetches candidates until one yields a spec block, and records what was found.
Output: data/coverage.json plus a summary table on stdout.
"""

import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import manifest
import wayback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'coverage.json')

DRUPAL_ERA = ('2016', '2017', '2018')

# Ordered spec-block strategies. First hit wins.
SPEC_VARIANTS = [
    ('lft-rgt-h5', r'field-name-field-specifications-full-(?:lft|rgt)'),
    ('specs-full', r'id="specifications-full"'),
    ('specs-summary', r'field-name-field-specifications(?:-|")'),
]

IMAGE_PREFIX = re.compile(r'public/(library/[^/"?]+/[^/"?]+)/')
TITLE = re.compile(r'<title>(.*?)</title>', re.S | re.I)
OG_DESC = re.compile(r'<meta\s+property="og:description"\s+content="(.*?)"', re.S | re.I)


def rank(rows):
    """Drupal-era captures first, then largest byte length."""
    def key(r):
        return (0 if r['timestamp'][:4] in DRUPAL_ERA else 1, -r['length'])
    return sorted(rows, key=key)


def spec_pairs(html):
    """Count <h5>label</h5><p>value</p> pairs inside the spec columns."""
    total = 0
    labels = []
    for side in ('lft', 'rgt'):
        m = re.search(r'field-name-field-specifications-full-' + side, html)
        if not m:
            continue
        seg = html[m.start():m.start() + 12000]
        pairs = re.findall(r'<h5[^>]*>(.*?)</h5>\s*<p[^>]*>(.*?)</p>', seg, re.S)
        for label, _ in pairs:
            labels.append(re.sub(r'<[^>]+>', '', label).strip())
        total += len(pairs)
    return total, labels


def analyse(html):
    variant = None
    for name, pattern in SPEC_VARIANTS:
        if re.search(pattern, html):
            variant = name
            break
    n_pairs, labels = spec_pairs(html)
    title = TITLE.search(html)
    desc = OG_DESC.search(html)
    prefixes = sorted(set(IMAGE_PREFIX.findall(html)))
    images = len(set(re.findall(r'(?:src|srcset)="([^"]*sites/default/files/[^" ]*)', html)))
    return {
        'spec_variant': variant,
        'spec_pairs': n_pairs,
        'spec_labels': labels[:40],
        'image_prefixes': prefixes,
        'image_refs': images,
        'title': re.sub(r'\s+', ' ', title.group(1)).strip() if title else None,
        'tagline': re.sub(r'\s+', ' ', desc.group(1)).strip() if desc else None,
        'is_drupal': 'region-content' in html or 'Drupal.settings' in html,
    }


def audit(target):
    kind, slug, url = target
    rows = [r for r in wayback.cdx(url) if 'html' in (r['mimetype'] or '')]
    rec = {'kind': kind, 'slug': slug, 'url': url,
           'captures_found': len(rows), 'chosen': None, 'tried': [],
           'status': 'no-capture', 'notes': []}
    if not rows:
        return rec

    forced = manifest.CAPTURE_OVERRIDES.get(slug)
    ordered = ([r for r in rows if r['timestamp'] == forced] if forced else []) + rank(rows)

    seen = set()
    best = None
    for row in ordered:
        ts = row['timestamp']
        if ts in seen:
            continue
        seen.add(ts)
        if len(rec['tried']) >= 3:
            break
        try:
            html = wayback.fetch_capture(url, ts).decode('utf-8', 'replace')
        except Exception as exc:
            rec['tried'].append({'timestamp': ts, 'error': str(exc)[:80]})
            continue
        info = analyse(html)
        info.update({'timestamp': ts, 'bytes': len(html)})
        rec['tried'].append({k: info[k] for k in
                             ('timestamp', 'bytes', 'spec_variant', 'spec_pairs', 'is_drupal')})
        if best is None or info['spec_pairs'] > best['spec_pairs']:
            best = info
        if info['spec_pairs'] >= 5:
            break

    if best:
        rec['chosen'] = best
        if best['spec_pairs'] >= 5:
            rec['status'] = 'specs'
        elif best['is_drupal'] and best['image_refs'] > 5:
            rec['status'] = 'copy-only'
            rec['notes'].append('no spec table in any capture tried')
        else:
            rec['status'] = 'thin'
            rec['notes'].append('capture looks like a shell')
    return rec


def main():
    targets = manifest.all_targets()
    with ThreadPoolExecutor(max_workers=wayback.MAX_WORKERS) as pool:
        results = list(pool.map(audit, targets))

    by_slug = {r['slug']: r for r in results}
    wayback.save_json(OUT, by_slug)

    order = {'specs': 0, 'copy-only': 1, 'thin': 2, 'no-capture': 3}
    print('\n{:<40} {:<6} {:>5} {:>6} {:<14} {}'.format(
        'PRODUCT', 'KIND', 'PAIRS', 'CAPS', 'CAPTURE', 'STATUS'))
    print('-' * 100)
    for r in sorted(results, key=lambda r: (order[r['status']], r['slug'])):
        c = r['chosen'] or {}
        print('{:<40} {:<6} {:>5} {:>6} {:<14} {}'.format(
            r['slug'][:39], r['kind'], c.get('spec_pairs', 0),
            r['captures_found'], c.get('timestamp', '-'), r['status']))

    counts = {}
    for r in results:
        counts[r['status']] = counts.get(r['status'], 0) + 1
    print('\n' + '  '.join('{}={}'.format(k, v) for k, v in sorted(counts.items())))
    print('written: ' + OUT)


if __name__ == '__main__':
    main()
