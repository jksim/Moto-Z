#!/usr/bin/env python3
"""Stage 5: resolve product imagery against the Wayback CDX index and save it.

The tokenised Drupal style URLs on the page are not archived at the page's own
timestamp, so each logical image is matched by filename across every archived
locale and rendition, and the largest valid capture wins.
"""

import gzip
import os
import shutil
import re
import struct
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import manifest
import supplement
import wayback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
ASSETS = os.path.join(ROOT, 'src', 'assets', 'products')
CDX_DIR = os.path.join(ROOT, 'archive', 'cdx')

PER_ROLE = {'hero': 1, 'feature': 4, 'gallery': 4, 'spec': 1, 'logo': 1}
MAX_CANDIDATES = 3
FILES = 'www.motorola.com/sites/default/files'


def dimensions(blob):
    """Pixel size from a PNG/JPEG/GIF header, without decoding the image."""
    try:
        if blob[:8] == b'\x89PNG\r\n\x1a\n':
            w, h = struct.unpack('>II', blob[16:24])
            return int(w), int(h)
        if blob[:6] in (b'GIF87a', b'GIF89a'):
            w, h = struct.unpack('<HH', blob[6:10])
            return int(w), int(h)
        if blob[:3] == b'\xff\xd8\xff':
            i = 2
            while i < len(blob) - 9:
                if blob[i] != 0xFF:
                    i += 1
                    continue
                marker = blob[i + 1]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                              0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    h, w = struct.unpack('>HH', blob[i + 5:i + 9])
                    return int(w), int(h)
                i += 2 + struct.unpack('>H', blob[i + 2:i + 4])[0]
    except Exception:
        pass
    return 0, 0


def cdx_rows(token):
    """Archived file URLs whose path contains `token`, cached on disk."""
    safe = re.sub(r'[^a-z0-9]+', '-', token.lower())
    cache = os.path.join(CDX_DIR, safe + '.tsv.gz')
    if os.path.exists(cache):
        with gzip.open(cache, 'rt', encoding='utf-8') as fh:
            return [line.rstrip('\n').split('\t') for line in fh if line.strip()]

    rows = wayback.cdx(FILES, match='prefix', limit=4000,
                       extra='&filter=original:.*' + token + '.*&collapse=urlkey')
    out = []
    for row in rows:
        # Some captures are whole srcset strings; split them back into URLs.
        for part in re.split(r'[,\s]+', row['original']):
            if part.startswith('http') and 'sites/default/files' in part:
                out.append([part, row['timestamp'], str(row['length'])])
    os.makedirs(CDX_DIR, exist_ok=True)
    with gzip.open(cache, 'wt', encoding='utf-8') as fh:
        for r in out:
            fh.write('\t'.join(r) + '\n')
    return out


def dir_tokens(images):
    """Distinctive CDX filter tokens taken from the images' own directories.

    A slug like `moto-z` is too generic to filter on; the directory the images
    actually live in (`moto-z/new-vis-id`, `moto-z-gen-4`) is not.
    """
    generic = {'library', 'products', 'sites', 'default', 'files', 'public',
               'styles', 'desktop', 'mobile', 'us', 'storage'}
    tokens = []
    for image in images:
        url = re.sub(r'\?.*$', '', image['url'])
        m = re.search(r'(?:public|files)/(library/.*)/[^/]+$', url)
        if not m:
            continue
        parts = [p for p in m.group(1).split('/') if p and p not in generic]
        if not parts:
            continue
        token = '/'.join(parts[-2:]) if len(parts) > 1 else parts[-1]
        if token not in tokens:
            tokens.append(token)
    return tokens


def basename(url):
    return re.sub(r'\?.*$', '', url).rsplit('/', 1)[-1].lower()


def stem(name):
    """Basename reduced for comparison, without extension or punctuation."""
    return re.sub(r'[^a-z0-9]', '', name.rsplit('.', 1)[0].lower())


def same_image(wanted, archived):
    """Whether two filenames name the same asset.

    Drupal appends a cache-busting hash that differs between the captured page
    and the archived file itself (`...featgrid-1x1-dnl72sgum.jpg` on the page,
    `...featgrid-1x1-d.jpg` in the archive), so compare on the shared stem.
    """
    a, b = stem(wanted), stem(archived)
    if a == b:
        return True
    short, long = (a, b) if len(a) <= len(b) else (b, a)
    return len(short) >= 18 and long.startswith(short) and len(long) - len(short) <= 12


def pick(records, kind):
    """Trim to the images worth publishing, in display order."""
    counts = {}
    out = []
    for image in records:
        role = image['role']
        if counts.get(role, 0) >= PER_ROLE.get(role, 0):
            continue
        counts[role] = counts.get(role, 0) + 1
        out.append(image)
    return out


_GLOBAL = None


def global_index():
    """Every CDX row cached so far.

    Some pages reuse another product's imagery (the Z3 Play page serves the
    Z3's shots), so a basename missing from one product's index may be sitting
    in another's.
    """
    global _GLOBAL
    if _GLOBAL is None:
        rows = []
        for name in sorted(os.listdir(CDX_DIR)) if os.path.isdir(CDX_DIR) else []:
            if not name.endswith('.tsv.gz'):
                continue
            with gzip.open(os.path.join(CDX_DIR, name), 'rt', encoding='utf-8') as fh:
                rows += [line.rstrip('\n').split('\t') for line in fh if line.strip()]
        _GLOBAL = rows
    return _GLOBAL


def save(out_dir, role, n, blob, ext):
    os.makedirs(out_dir, exist_ok=True)
    fname = '{}-{}{}'.format(role, n, ext)
    with open(os.path.join(out_dir, fname), 'wb') as fh:
        fh.write(blob)
    return fname


def resolve(slug, kind, wanted, index):
    saved = []
    out_dir = os.path.join(ASSETS, kind, slug)
    for want in wanted:
        # Supplement images from sources other than the archive are fetched as
        # given, with no CDX lookup.
        if want.get('direct'):
            try:
                blob = wayback.fetch(want['url'])
            except Exception:
                continue
            ext = wayback.sniff(blob)
            if not ext:
                continue
            w, h = dimensions(blob)
            fname = save(out_dir, want['role'], len(saved) + 1, blob, ext)
            saved.append({'key': '{}/{}/{}'.format(kind, slug, fname),
                          'role': want['role'], 'width': w, 'height': h})
            continue
        name = basename(want['url'])
        cands = [r for r in index if basename(r[0]) == name]
        if not cands:
            cands = [r for r in index if same_image(name, basename(r[0]))]
        if not cands:
            cands = [r for r in global_index() if basename(r[0]) == name]
        cands.sort(key=lambda r: -int(r[2] or 0))

        best = None
        for url, ts, _ in cands[:MAX_CANDIDATES]:
            try:
                blob = wayback.fetch(wayback.snapshot_url(url, ts))
            except Exception:
                continue
            ext = wayback.sniff(blob)
            if not ext:
                continue
            w, h = dimensions(blob)
            if best is None or w * h > best[1] * best[2]:
                best = (blob, w, h, ext, url, ts)
            if ext == '.svg':
                break
        if best is None:
            continue

        blob, w, h, ext, url, ts = best
        fname = save(out_dir, want['role'], len(saved) + 1, blob, ext)
        saved.append({'key': '{}/{}/{}'.format(kind, slug, fname),
                      'role': want['role'], 'width': w, 'height': h})
    return saved


def local_images(slug, kind):
    """Copy imagery held on disk rather than fetched from an archive."""
    saved = []
    out_dir = os.path.join(ASSETS, kind, slug)
    for source, role in supplement.LOCAL_IMAGES.get(slug, []):
        if not os.path.exists(source):
            continue
        ext = os.path.splitext(source)[1].lower()
        fname = '{}-{}{}'.format(role, len(saved) + 1, ext)
        os.makedirs(out_dir, exist_ok=True)
        shutil.copyfile(source, os.path.join(out_dir, fname))
        with open(source, 'rb') as fh:
            w, h = dimensions(fh.read())
        saved.append({'key': '{}/{}/{}'.format(kind, slug, fname),
                      'role': role, 'width': w, 'height': h})
    return saved


def main():
    mods = wayback.load_json(os.path.join(DATA, 'mods.json'), [])
    phones = wayback.load_json(os.path.join(DATA, 'phones.json'), [])

    jobs = [('mods', r) for r in mods] + [('phones', r) for r in phones]

    def run(job):
        kind, rec = job
        # Supplement entries are added here, never written back into the
        # record, so re-running the stage stays idempotent.
        # Supplement entries come first so a hand-picked shot wins its slot
        # over whatever the page happened to use.
        wanted = pick(supplement.IMAGES.get(rec['slug'], []) + rec['imageUrls'], kind)
        if rec.get('images'):
            return rec
        if supplement.LOCAL_IMAGES.get(rec['slug']):
            rec['images'] = local_images(rec['slug'], kind)
            print('{:<42} {:>2} local images'.format(rec['slug'], len(rec['images'])))
            return rec
        index = []
        for token in dir_tokens(wanted)[:3]:
            index += cdx_rows(token)
        rec['images'] = resolve(rec['slug'], kind, wanted, index)
        print('{:<42} {:>2}/{:<2} images'.format(
            rec['slug'], len(rec['images']), len(wanted)))
        return rec

    with ThreadPoolExecutor(max_workers=wayback.MAX_WORKERS) as pool:
        list(pool.map(run, jobs))

    wayback.save_json(os.path.join(DATA, 'mods.json'), mods)
    wayback.save_json(os.path.join(DATA, 'phones.json'), phones)
    total = sum(len(r['images']) for r in mods + phones)
    print('\nsaved {} images'.format(total))


if __name__ == '__main__':
    main()
