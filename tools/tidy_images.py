#!/usr/bin/env python3
"""Stage 5d: drop imagery that adds nothing -- duplicates and stray icons.

Motorola's pages served the same photograph more than once -- a re-encode at a
different size, or the same shot cropped for another slot. Two signals catch
both, because neither does alone:

  * a difference hash over an aspect-squashed thumbnail, which matches
    re-encodes and rescales but not recrops;
  * a colour histogram, which survives recropping but cannot tell apart
    different photographs from the same shoot.

It also drops anything too small to be product photography: a few 35x34 icons
reach the gallery that no filename rule catches.

Dry run by default; --apply removes the files and the records.
"""

import itertools
import json
import math
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import wayback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
ASSETS = os.path.join(ROOT, 'src', 'assets', 'products')

HASH_SIZE = 16
HASH_MAX = 12          # near-identical structure: a re-encode or rescale
HIST_MIN = 0.975       # near-identical colour: the same shot, recropped
# Below this an image is an icon, not a photograph: too small to show, and too
# small for either duplicate signal to mean anything.
MIN_AREA = 40000
ROLE_RANK = {'hero': 0, 'feature': 1, 'gallery': 2, 'spec': 3, 'logo': 4}


def signature(path, size=HASH_SIZE):
    im = Image.open(path).convert('L').resize((size + 1, size), Image.LANCZOS)
    px = im.load()
    bits = 0
    for y in range(size):
        for x in range(size):
            bits = (bits << 1) | (1 if px[x, y] > px[x + 1, y] else 0)
    return bits


def histogram(path, bins=8):
    im = Image.open(path).convert('RGB').resize((96, 96), Image.LANCZOS)
    counts = [0] * (bins ** 3)
    px = im.load()
    for y in range(96):
        for x in range(96):
            r, g, b = px[x, y]
            counts[(r * bins // 256) * bins * bins
                   + (g * bins // 256) * bins
                   + (b * bins // 256)] += 1
    total = sum(counts) or 1
    return [c / total for c in counts]


def same_picture(a, b):
    if bin(a['sig'] ^ b['sig']).count('1') <= HASH_MAX:
        return True
    overlap = sum(math.sqrt(x * y) for x, y in zip(a['hist'], b['hist']))
    return overlap >= HIST_MIN


def keeper(group):
    """The copy worth keeping: most pixels, then the better slot.

    Area leads deliberately. Role-first would keep a small gallery thumbnail
    over the full-size shot it duplicates.
    """
    return min(group, key=lambda i: (-i['img']['width'] * i['img']['height'],
                                     ROLE_RANK.get(i['img']['role'], 9)))


def main():
    apply = '--apply' in sys.argv
    dropped = 0

    for name in ('mods', 'phones'):
        path = os.path.join(DATA, name + '.json')
        records = wayback.load_json(path, [])
        for rec in records:
            loaded, tiny = [], []
            for img in rec.get('images', []):
                file = os.path.join(ASSETS, img['key'])
                if img['key'].endswith('.svg') or not os.path.exists(file):
                    continue
                if img['width'] * img['height'] < MIN_AREA:
                    tiny.append(img)
                    continue
                loaded.append({'img': img, 'sig': signature(file),
                               'hist': histogram(file)})

            groups = []
            for item in loaded:
                for group in groups:
                    if same_picture(group[0], item):
                        group.append(item)
                        break
                else:
                    groups.append([item])

            remove = list(tiny)
            for img in tiny:
                print('{}: drop {} ({}x{}) - too small to be a photo'.format(
                    rec['slug'], img['key'].split('/')[-1], img['width'], img['height']))
            for group in groups:
                if len(group) < 2:
                    continue
                keep = keeper(group)
                for item in group:
                    if item is not keep:
                        remove.append(item['img'])
                print('{}: keep {} ({}x{}), drop {}'.format(
                    rec['slug'], keep['img']['key'].split('/')[-1],
                    keep['img']['width'], keep['img']['height'],
                    ', '.join(i['img']['key'].split('/')[-1]
                              for i in group if i is not keep)))

            dropped += len(remove)
            if apply and remove:
                keys = {i['key'] for i in remove}
                rec['images'] = [i for i in rec['images'] if i['key'] not in keys]
                if rec.get('coverKey') in keys:
                    rec['coverKey'] = ''
                for key in keys:
                    file = os.path.join(ASSETS, key)
                    if os.path.exists(file):
                        os.remove(file)
        if apply:
            wayback.save_json(path, records)

    print('\n{} image(s) removed{}'.format(dropped, '' if apply else ' - dry run'))


if __name__ == '__main__':
    main()
