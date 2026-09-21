"""Shared Wayback Machine access: CDX queries, throttled fetching, validation.

The Wayback Machine answers an unavailable capture with HTTP 200 and an HTML
error page, so every fetch is validated by content, never by status code alone.
Two workers is the tested ceiling before it starts refusing.
"""

import gzip
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, 'build', 'fetch_cache')

MAX_WORKERS = 2
UA = 'moto-z-archive/1.0 (+https://github.com/jksim)'

# Leading bytes -> true extension. Wayback often serves a rendition whose
# extension disagrees with its content.
MAGIC = [
    (b'\xff\xd8\xff', '.jpg'),
    (b'\x89PNG\r\n\x1a\n', '.png'),
    (b'GIF87a', '.gif'),
    (b'GIF89a', '.gif'),
    (b'RIFF', '.webp'),
    (b'<?xml', '.svg'),
    (b'<svg', '.svg'),
    (b'%PDF', '.pdf'),
]


def sniff(blob):
    """Return the true extension for an image blob, or None if it is not one."""
    head = blob[:16]
    for magic, ext in MAGIC:
        if head.startswith(magic):
            if ext == '.webp' and blob[8:12] != b'WEBP':
                continue
            return ext
    if b'<svg' in blob[:512].lower():
        return '.svg'
    return None


def _cache_path(url):
    return os.path.join(CACHE, hashlib.sha256(url.encode()).hexdigest() + '.gz')


def fetch(url, retries=5, use_cache=True):
    """GET with backoff. Returns bytes. Raises on 403/404 immediately."""
    cp = _cache_path(url)
    if use_cache and os.path.exists(cp):
        with gzip.open(cp, 'rb') as fh:
            return fh.read()

    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                blob = resp.read()
            os.makedirs(CACHE, exist_ok=True)
            with gzip.open(cp, 'wb') as fh:
                fh.write(blob)
            return blob
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 404):
                raise
            last = exc
        except Exception as exc:
            last = exc
        time.sleep(5 * (attempt + 1))
    raise last


def cdx(url, match='exact', limit=200, extra=''):
    """Query the CDX index. Returns a list of dicts, oldest first."""
    q = ('https://web.archive.org/cdx/search/cdx?url=' + urllib.parse.quote(url, safe='')
         + '&matchType=' + match
         + '&filter=statuscode:200&fl=original,timestamp,mimetype,length'
         + '&limit=' + str(limit) + extra)
    try:
        raw = fetch(q).decode('utf-8', 'replace')
    except Exception:
        return []
    rows = []
    for line in raw.strip().splitlines():
        parts = line.split(' ')
        if len(parts) < 4:
            continue
        try:
            length = int(parts[3])
        except ValueError:
            length = 0
        rows.append({'original': parts[0], 'timestamp': parts[1],
                     'mimetype': parts[2], 'length': length})
    return rows


def snapshot_url(url, timestamp):
    """The raw-capture URL: `id_` suppresses the Wayback toolbar rewrite."""
    return 'https://web.archive.org/web/{}id_/{}'.format(timestamp, url)


def fetch_capture(url, timestamp):
    """Fetch one capture's original bytes, following redirects."""
    return fetch(snapshot_url(url, timestamp))


def sha256(blob):
    return hashlib.sha256(blob).hexdigest()


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write('\n')
