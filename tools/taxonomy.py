"""Categories, compatibility rules and cross-links to the developer docs.

Categories are explicit per product -- inferring them from slugs breaks on the
Alexa speaker and on both Style Shells.
"""

CATEGORIES = [
    ('audio',        'Audio'),
    ('power',        'Power'),
    ('camera',       'Camera'),
    ('projection',   'Projection & Printing'),
    ('style',        'Style & Protection'),
    ('connectivity', 'Connectivity & Mounting'),
    ('input',        'Gaming & Input'),
    ('development',  'Development'),
]

# slug -> (primary, [secondary])
CATEGORY_OF = {
    'jbl-soundboost-speaker':                  ('audio', []),
    'jbl-soundboost-2-speaker':                ('audio', []),
    'moto-stereo-speaker':                     ('audio', []),
    'moto-smart-speaker-with-amazon-alexa':    ('audio', []),
    'hasselblad-true-zoom':                    ('camera', []),
    'moto-360-camera':                         ('camera', []),
    'incipio-offgrid-power-pack':              ('power', []),
    'mophie-juice-pack':                       ('power', []),
    'moto-power-pack':                         ('power', []),
    'moto-turbopower-pack-battery':            ('power', []),
    'tumi-power-pack':                         ('power', []),
    'moto-insta-share-projector':              ('projection', []),
    'polaroid-insta-share-printer':            ('projection', ['camera']),
    'moto-gamepad-console':                    ('input', []),
    'moto-style-shell':                        ('style', []),
    'moto-style-shell-with-wireless-charging': ('style', ['power']),
    'moto-folio':                              ('style', []),
    'moto-5g':                                 ('connectivity', []),
    'incipio-vehicle-dock':                    ('connectivity', []),
    'moto-mods-development-kit':               ('development', []),
}

# Every device record, oldest first. Mirrors manifest.PHONES `record` values.
DEVICES = ['moto-z', 'moto-z-force', 'moto-z-play', 'moto-z2-play',
           'moto-z2-force', 'moto-z3', 'moto-z3-play', 'moto-z4']

# Motorola committed to one Mod connector across every Moto Z generation, so a
# Mod works with every device unless it is listed here.
#   'devices'  -- the only devices it works with
#   'fit'      -- 'universal' | 'per-model' (shells are cut for one chassis)
COMPATIBILITY_EXCEPTIONS = {
    # The page states z3 first, then z2; the Z4 shipped with support too.
    'moto-5g':                                 {'devices': ['moto-z2-force', 'moto-z3', 'moto-z4']},
    'moto-style-shell':                        {'fit': 'per-model'},
    'moto-style-shell-with-wireless-charging': {'fit': 'per-model'},
    'moto-folio':                              {'fit': 'per-model'},
    'incipio-vehicle-dock':                    {'fit': 'per-model'},
}


def compatible_devices(slug):
    rule = COMPATIBILITY_EXCEPTIONS.get(slug, {})
    return list(rule.get('devices', DEVICES))


def fit(slug):
    return COMPATIBILITY_EXCEPTIONS.get(slug, {}).get('fit', 'universal')


DOCS = 'https://jksim.github.io/MotoMods-Developer-Docs/'

# Which firmware protocol each category of Mod used, for a "how it worked" link.
RELATED_DOCS = {
    'audio':        [('Audio protocol',        DOCS + 'explore/firmware/audio/')],
    'power':        [('Power Transfer protocol', DOCS + 'explore/firmware/power-transfer/'),
                     ('Battery protocol',      DOCS + 'explore/firmware/battery/')],
    'camera':       [('Camera Controls',       DOCS + 'explore/firmware/camera-controls/')],
    'projection':   [('Display protocol',      DOCS + 'explore/firmware/display/')],
    'input':        [('HID protocol',          DOCS + 'explore/firmware/hid/')],
    'connectivity': [('USB-Ext protocol',      DOCS + 'explore/firmware/usb-ext/')],
    'style':        [('Mod Management',        DOCS + 'explore/firmware/mod-management/')],
    'development':  [('Moto Mods Development Kit', DOCS + 'hardware/mdk/'),
                     ('Reference Moto Mod',     DOCS + 'build/mdk-user-guide/reference-moto-mod/'),
                     ('Perforated Board',       DOCS + 'build/mdk-user-guide/perforated-board/'),
                     ('System Architecture',    DOCS + 'explore/system-architecture/')],
}

# Manufacturer pages worth mining for specs the Motorola captures lack.
VENDOR_SOURCES = {
    'jbl-soundboost-speaker':       'https://www.jbl.com/',
    'jbl-soundboost-2-speaker':     'https://www.jbl.com/',
    'incipio-offgrid-power-pack':   'https://www.incipio.com/',
    'incipio-vehicle-dock':         'https://www.incipio.com/',
    'mophie-juice-pack':            'https://www.mophie.com/',
    'polaroid-insta-share-printer': 'https://www.polaroid.com/',
    'tumi-power-pack':              'https://www.tumi.com/',
}


def label(cat):
    return dict(CATEGORIES).get(cat, cat)
