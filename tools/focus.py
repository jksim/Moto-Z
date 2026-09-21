#!/usr/bin/env python3
"""Measure each image so cards present it well.

Two things come out of this: a focal point, and the backdrop.

Motorola's banners put the product to one side and leave the rest as flat
colour for headline text. A centred crop therefore pushes the product to the
edge of a card. Edge energy separates product from backdrop cleanly, so the
centroid of that energy is a good focal point.

Offline, but kept out of `make data` because it needs Pillow and the result is
stored alongside the imagery it describes.
"""

import os
import sys

from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import wayback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
ASSETS = os.path.join(ROOT, 'src', 'assets', 'products')

THRESHOLD = 18
SAMPLE = 240


def centroid(values):
    total = sum(values)
    if not total or len(values) < 2:
        return 0.5
    weighted = sum(i * v for i, v in enumerate(values))
    return weighted / total / (len(values) - 1)


def backdrop(path):
    """Average border colour, used as the card's frame so a crop never shows a
    grey gap against the product's own background."""
    try:
        im = Image.open(path).convert('RGB')
    except Exception:
        return None, 999.0
    im.thumbnail((160, 160))
    width, height = im.size
    px = im.load()
    points = []
    for x in range(width):
        points += [px[x, 0], px[x, height - 1]]
    for y in range(height):
        points += [px[0, y], px[width - 1, y]]
    # Median, not mean: the product and its shadow intrude on the border of
    # many shots, and an average of that shifts a pure-white backdrop to grey,
    # which shows as a seam where the frame meets the image.
    return tuple(sorted(p[i] for p in points)[len(points) // 2] for i in range(3))


def focal_point(path):
    try:
        im = Image.open(path).convert('L')
    except Exception:
        return 0.5, 0.5
    im.thumbnail((SAMPLE, SAMPLE))
    edges = im.filter(ImageFilter.FIND_EDGES)
    width, height = edges.size
    px = edges.load()
    cols = [0] * width
    rows = [0] * height
    for y in range(height):
        for x in range(width):
            v = px[x, y]
            if v > THRESHOLD:
                cols[x] += v
                rows[y] += v
    return centroid(cols), centroid(rows)


def main():
    changed = 0
    for name in ('mods', 'phones'):
        path = os.path.join(DATA, name + '.json')
        records = wayback.load_json(path, [])
        for rec in records:
            for image in rec.get('images', []):
                image.pop('flat', None)   # dropped: see git history
                if image['key'].endswith('.svg'):
                    image['focusX'], image['focusY'] = 0.5, 0.5
                    image['bg'] = ''
                    continue
                img_path = os.path.join(ASSETS, image['key'])
                x, y = focal_point(img_path)
                # Keep the crop from clinging to an edge.
                x = min(0.85, max(0.15, round(x, 2)))
                y = min(0.85, max(0.15, round(y, 2)))
                rgb = backdrop(img_path)
                before = (image.get('focusX'), image.get('focusY'), image.get('bg'))
                image['focusX'], image['focusY'] = x, y
                image['bg'] = ('#%02x%02x%02x' % rgb) if rgb else ''
                if before != (x, y, image['bg']):
                    changed += 1
        wayback.save_json(path, records)
    print('measured {} images'.format(changed))


if __name__ == '__main__':
    main()
