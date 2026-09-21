#!/usr/bin/env python3
"""Stage 1: download the chosen capture for every product into archive/pages/."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import manifest
import wayback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = os.path.join(ROOT, 'archive', 'pages')
INDEX = os.path.join(ROOT, 'archive', 'index.json')
COVERAGE = os.path.join(ROOT, 'data', 'coverage.json')


def main():
    coverage = wayback.load_json(COVERAGE, {})
    index = wayback.load_json(INDEX, {}) or {}
    ok = miss = 0

    for kind, slug, url in manifest.all_targets():
        rec = coverage.get(slug) or {}
        chosen = rec.get('chosen') or {}
        ts = manifest.CAPTURE_OVERRIDES.get(slug) or chosen.get('timestamp')
        if not ts:
            print('SKIP  {:<40} no capture'.format(slug))
            miss += 1
            continue

        out = os.path.join(PAGES, kind + 's', slug + '.html')
        try:
            blob = wayback.fetch_capture(url, ts)
        except Exception as exc:
            print('FAIL  {:<40} {}'.format(slug, str(exc)[:50]))
            miss += 1
            continue

        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, 'wb') as fh:
            fh.write(blob)
        index[slug] = {'kind': kind, 'url': url, 'timestamp': ts,
                       'bytes': len(blob), 'path': os.path.relpath(out, ROOT)}
        print('ok    {:<40} {:>8} bytes  {}'.format(slug, len(blob), ts))
        ok += 1

    wayback.save_json(INDEX, index)
    print('\nsaved {} pages, {} missing'.format(ok, miss))


if __name__ == '__main__':
    main()
