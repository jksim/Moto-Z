"""Curated map from motorola.com product pages to catalogue records.

Everything downstream iterates these lists. Nothing is discovered at build time.

`slug` is the last path segment of the original US product URL and is also the
route slug, except where `record` overrides it -- the Moto Z4 was listed twice
(unlocked and Verizon) and is one device.
"""

BASE = 'https://www.motorola.com/us/products/'

# (slug, name, brand, year)
MODS = [
    ('hasselblad-true-zoom',                   'Hasselblad True Zoom',                 'Hasselblad', 2016),
    ('incipio-offgrid-power-pack',             'Incipio offGRID Power Pack',           'Incipio',    2016),
    ('incipio-vehicle-dock',                   'Incipio Vehicle Dock',                 'Incipio',    2016),
    ('jbl-soundboost-speaker',                 'JBL SoundBoost Speaker',               'JBL',        2016),
    ('jbl-soundboost-2-speaker',               'JBL SoundBoost 2 Speaker',             'JBL',        2017),
    ('mophie-juice-pack',                      'mophie juice pack',                    'mophie',     2016),
    ('moto-360-camera',                        'Moto 360 Camera',                      'Motorola',   2017),
    ('moto-5g',                                'Moto 5G Mod',                          'Motorola',   2019),
    ('moto-folio',                             'Moto Folio',                           'Motorola',   2017),
    ('moto-gamepad-console',                   'Moto GamePad',                         'Motorola',   2017),
    ('moto-insta-share-projector',             'Moto Insta-Share Projector',           'Motorola',   2016),
    ('moto-power-pack',                        'Moto Power Pack',                      'Motorola',   2018),
    ('moto-smart-speaker-with-amazon-alexa',   'Moto Smart Speaker with Amazon Alexa', 'Motorola',   2017),
    ('moto-stereo-speaker',                    'Moto Stereo Speaker',                  'Motorola',   2018),
    ('moto-style-shell',                       'Moto Style Shell',                     'Motorola',   2016),
    ('moto-style-shell-with-wireless-charging','Moto Style Shell with Wireless Charging','Motorola', 2017),
    ('moto-turbopower-pack-battery',           'Moto TurboPower Pack',                 'Motorola',   2017),
    ('polaroid-insta-share-printer',           'Polaroid Insta-Share Printer',         'Polaroid',   2017),
    ('tumi-power-pack',                        'TUMI Power Pack',                      'TUMI',       2017),
    # Sold to developers through element14 rather than the consumer store, so
    # there is no motorola.com product page; its record is built from the
    # developer documentation. See tools/supplement.py.
    ('moto-mods-development-kit',              'Moto Mods Development Kit',            'Motorola',   2016),
]

# (slug, record, name, family, generation, carrier, year)
# `record` groups listings that are the same device.
PHONES = [
    ('moto-z',                      'moto-z',        'Moto Z',            'Z',       1, 'unlocked', 2016),
    ('moto-z-droid-edition',        'moto-z',        'Moto Z Droid',      'Z',       1, 'droid',    2016),
    ('moto-z-force-droid-edition',  'moto-z-force',  'Moto Z Force Droid','Z Force', 1, 'droid',    2016),
    ('moto-z-play',                 'moto-z-play',   'Moto Z Play',       'Z Play',  1, 'unlocked', 2016),
    ('moto-z-play-droid',           'moto-z-play',   'Moto Z Play Droid', 'Z Play',  1, 'droid',    2016),
    ('moto-z-play-gen-2',           'moto-z2-play',  'Moto Z2 Play',      'Z Play',  2, 'unlocked', 2017),
    ('moto-z-force-edition-gen-2',  'moto-z2-force', 'Moto Z2 Force',     'Z Force', 2, 'unlocked', 2017),
    ('moto-z-gen-3',                'moto-z3',       'Moto Z3',           'Z',       3, 'verizon',  2018),
    ('moto-z-play-gen-3',           'moto-z3-play',  'Moto Z3 Play',      'Z Play',  3, 'unlocked', 2018),
    ('moto-z-gen-4-unlocked',       'moto-z4',       'Moto Z4',           'Z',       4, 'unlocked', 2019),
    ('moto-z-gen-4-verizon',        'moto-z4',       'Moto Z4',           'Z',       4, 'verizon',  2019),
]

# Landing pages, used for catalogue copy rather than as products.
LANDING = [
    ('moto-mods',      BASE + 'moto-mods'),
    ('moto-z-family',  BASE + 'moto-z-family'),
]

# Captures chosen by hand where the automatic heuristic picks a worse one.
CAPTURE_OVERRIDES = {}


def mod_url(slug):
    return BASE + 'moto-mods/' + slug


def phone_url(slug):
    return BASE + slug


def all_targets():
    """(kind, slug, url) for every page the pipeline fetches."""
    out = [('mod', s, mod_url(s)) for s, _, _, _ in MODS]
    out += [('phone', s, phone_url(s)) for s, _, _, _, _, _, _ in PHONES]
    return out
