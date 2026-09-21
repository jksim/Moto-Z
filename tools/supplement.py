"""Hand-curated specs for products whose captured pages carry no spec table.

Each entry records the URL the figures came from. Values are quoted from the
source, not estimated.
"""

MOTOROLA = 'https://www.motorola.com/us/products/moto-mods/'
DOCS = 'https://jksim.github.io/MotoMods-Developer-Docs/'
VZ_LAUNCH = 'https://www.verizon.com/about/news/verizon-5g-mobility-service-and-motorola-5g-smartphone-are-here'
VZ_ANNOUNCE = 'https://www.verizon.com/about/news/verizon-and-motorola-unveil-worlds-first-5g-upgradable-smartphone--moto-z3'
VZ_FAQ = 'https://www.verizon.com/support/5g-moto-mod-faqs/'
BH = 'https://www.bhphotovideo.com/c/product/1593586-REG/moto_89878n_tumi_power_pack_moto.html'

SPECS = {
    # The page states the figures in prose under "full specifications" rather
    # than in a spec table. Two materials were sold.
    'moto-style-shell': {
        'source': MOTOROLA + 'moto-style-shell',
        'specs': [
            ('Compatibility', 'Cut for a specific Moto Z model'),
            ('Dimensions', '154 x 74 x 2 mm'),
            ('Materials', 'Nylon; Corning Gorilla Glass'),
            ('Weight', 'Nylon: 25g to 32g; Gorilla Glass: 53g'),
            ('Nylon styles', 'Herringbone Nylon, Crimson Ballistic Nylon'),
            ('Gorilla Glass styles', 'Colored leaves, Expressive curves, '
                                     'Graphic flowers, Overlapping triangles, Retro stripe'),
        ],
    },
    # Verizon sold this one exclusively and documented it far better than
    # Motorola did; the figures below come from Verizon's support FAQ and
    # newsroom, with the battery from Motorola's own page.
    'moto-5g': {
        'source': VZ_FAQ,
        'specs': [
            ('Network', 'Verizon 5G Ultra Wideband, millimetre wave'),
            ('Outside 5G coverage', 'Switches automatically to Verizon 4G LTE'),
            ('Data', 'Unlimited on 5G Ultra Wideband, with no de-prioritisation'),
            ('Battery size', '2000 mAh'),
            ('Sharing', 'Shares the 5G connection as a Wi-Fi hotspot, or by tethering'),
            ('Compatible phones', 'Moto Z3 and Moto Z4 sold by Verizon'),
            ('Plan requirement', 'A Verizon Unlimited plan with 5G Ultra Wideband '
                                 'service added to the line'),
            ('Availability', 'United States, exclusive to Verizon'),
            ('Purchase limit', 'One per eligible line'),
        ],
    },
    # The MDK was sold to developers, not through the consumer store, so its
    # record comes from Motorola's own developer documentation rather than a
    # product page.
    'moto-mods-development-kit': {
        'source': DOCS + 'hardware/mdk/',
        'specs': [
            ('In the box', 'Reference Moto Mod, Perforated Board, example cover'),
            ('Microcontroller', 'STM32L476ME (MuC), ARM Cortex-M4F with FPU'),
            ('MuC memory', '128 KB RAM, 1 MB flash'),
            ('High-speed path', 'Moto High Speed Bridge (MHB) for camera and display traffic'),
            ('Developer connector', '80-pin, exposing GPIO, power and the standard buses'),
            ('Ports', 'USB-C (USB C DRP), micro USB-B, MyDP'),
            ('Power rail', 'Regulated 3.3 V, 500 mA'),
            ('Perforated board', '26 rows of solder points at 2.54 mm pitch, power bus each side'),
            ('Component height limit', '2.3 mm on top, 1.3 mm underneath, with the in-box cover'),
            ('Firmware', 'NuttX, speaking Greybus over the Mod interface'),
            ('Compatibility', 'Any phone in the Moto Z family'),
            ('Sold through', 'element14, to developers'),
        ],
    },
    # Motorola's own page for the designer edition was captured late and
    # carries no spec table; these are B&H's published figures for the retail
    # unit (MPN 89878N).
    'tumi-power-pack': {
        'source': BH,
        # B&H lists compatibility as the two phones on sale when it was
        # listed; the Works with section covers the full family, so that row is
        # left out rather than contradicting it.
        'specs': [
            ('Capacity', '2220 mAh'),
            ('Battery life', 'Adds up to 22 hours'),
            ('Dimensions', '7.4 x 15.2 x 0.8 cm (2.9 x 6.0 x 0.3")'),
            ('Thickness', '0.27 inch'),
            ('Efficiency Mode', 'Charging starts at peak efficiency, preserving '
                                'battery life by up to 20%'),
            ('Finish', 'TUMI premium designer edition'),
            ('In the box', 'Moto TUMI Power Pack Moto Mod'),
            ('Warranty', 'Limited 1-year'),
            ('Manufacturer part number', '89878N'),
        ],
    },
}


# Imagery the captured page does not carry. The TUMI edition's own page was
# captured late, after the product shots had moved to client-side loading.
IMAGES = {
    # The Z3 Play page's own hero is the Moto Z3's shot, which would make the
    # two cards near-identical. This one is from the Z3 Play page and is a
    # clearer, distinct product photo.
    'moto-z3-play': [
        {'url': 'https://www.motorola.com/sites/default/files/styles/'
                '12_cols_desktop_1x/public/library/uk/products/moto-z-play-gen-3/'
                'moto-z3-assets_waterresistance-d.jpg',
         'role': 'hero'},
    ],
    'tumi-power-pack': [
        {'url': 'https://static.bhphoto.com/images/images1000x1000/1601390734_1593586.jpg',
         'role': 'hero', 'direct': True},
    ],
}


# Copy for products whose captured page carries none, or too little.
COPY = {
    'moto-mods-development-kit': {
        'source': DOCS + 'hardware/mdk/',
        'tagline': 'The Mod you built your own Mod on',
        'summary': 'The Moto Mods Development Kit was how anyone outside '
                   'Motorola made a Mod. It pairs a Reference Moto Mod \u2014 a '
                   'working Mod with the microcontroller, the high-speed bridge '
                   'and the phone-side interface already on it \u2014 with a '
                   'perforated board to solder your own circuit onto, and a cover '
                   'to put round the result. With a Moto Z, that was the whole '
                   'starting point for a prototype.',
        'features': [
            ('A working Mod to build on',
             'The Reference Moto Mod carries the mechanical and electrical '
             'interface to the phone, the Moto Mod Microcontroller and the Moto '
             'High Speed Bridge, so the hard part of talking to a Moto Z was '
             'already done.'),
            ('80 pins, brought to the surface',
             'The Perforated Board exposes the 80-pin developer connector as 26 '
             'rows of solder points at 2.54 mm pitch, with a power bus down each '
             'side \u2014 room to get an idea working without making a board first.'),
            ('Personality Cards as worked examples',
             'Motorola shipped audio, battery, display and temperature-sensor '
             'cards, each with open-source firmware and an Android app, as '
             'end-to-end examples of a finished Mod.'),
            ('Open firmware',
             'Mods ran NuttX and spoke Greybus, the protocol from Project Ara, '
             'over the same interface every shipping Mod used.'),
        ],
    },
    'moto-5g': {
        'source': VZ_ANNOUNCE,
        'tagline': 'The first phone you could upgrade to 5G',
        'summary': 'Verizon called the Moto Z3 with the 5G moto mod "the world\u2019s '
                   'first 5G-upgradeable smartphone". Rather than wait for a new '
                   'handset, Motorola put the millimetre-wave radio in a Mod: snap '
                   'it on and a phone that shipped in 2018 joined the 5G network '
                   'that went live in 2019. When Verizon switched on 5G Ultra '
                   'Wideband mobility in Chicago and Minneapolis on 11 April 2019, '
                   'this was the device it launched with.',
        'features': [
            ('A modem you could add later',
             'The Mod architecture put the 5G radio and its antennas outside the '
             'phone, so the network upgrade did not need a new handset. It is the '
             'clearest demonstration of what modular hardware was for.'),
            ('Verizon 5G Ultra Wideband',
             'Millimetre-wave spectrum, for what Verizon described as massive '
             'bandwidth, ultra-high speeds and single-digit millisecond latency.'),
            ('Falls back on its own',
             'Outside a 5G Ultra Wideband area the phone switches to Verizon 4G '
             'LTE without the user doing anything.'),
            ('Unlimited, and shareable',
             'Data over 5G Ultra Wideband was unlimited with no de-prioritisation, '
             'and the connection could be shared as a Wi-Fi hotspot or by tethering.'),
            ('Its own battery',
             'A 2000 mAh cell inside the Mod, so driving the 5G radio did not drain '
             'the phone.'),
        ],
    },
    'tumi-power-pack': {
        'source': BH,
        'tagline': 'Battery life, with a TUMI finish',
        'summary': 'Add additional battery life to your phone, without adding '
                   'bulk, using the sleek TUMI Power Pack Moto Mod. A slim '
                   '2220mAh battery pack that gives your phone up to 22 hours '
                   'of additional battery power. It snaps onto the back of your '
                   'phone quickly, and is only 0.27" thin.',
        'features': [
            ('Efficiency Mode',
             'Charging starts automatically when efficiency is at its peak, '
             'preserving battery life by up to 20%.'),
            ('Snap on when you need it',
             'Snap it on when your battery is running low, or always keep it on '
             'to extend normal battery life.'),
        ],
    },
}


# Products whose best shot is not the one the automatic rule picks -- usually
# because Motorola's hero image was never archived and the fallback is a video
# poster rather than the product.
COVERS = {
    'incipio-offgrid-power-pack': 'gallery-3',
    'moto-z3-play': 'hero',
}


# Dated milestones, for products whose story is the point. Each entry is
# (date, what happened), stated in the source rather than inferred.
TIMELINE = {
    'moto-5g': {
        'source': VZ_LAUNCH,
        'events': [
            ('2018',
             'Verizon and Motorola unveil the Moto Z3 as the first 5G-upgradeable '
             'smartphone, with the 5G moto mod to follow.'),
            ('October 2018',
             'Verizon launches what it calls the world\u2019s first commercial 5G '
             'Ultra Wideband network, as 5G Home broadband in Houston, Los Angeles, '
             'Sacramento and Indianapolis.'),
            ('14 March 2019', 'Preorders open for the 5G moto mod.'),
            ('11 April 2019',
             'Verizon switches on 5G Ultra Wideband mobility in Chicago and '
             'Minneapolis. The Moto Z3 with the 5G moto mod is the launch device.'),
            ('Through 2019',
             'Verizon says more than 30 markets are set to launch.'),
        ],
    },
}


# B&H listings for Mods already in the manifest. Hand-verified: B&H's own
# search no longer surfaces these discontinued products, and the entries that
# could not be confirmed as the right product are simply absent.
B = 'https://www.bhphotovideo.com/c/product/'

BH_URLS = {
    'incipio-offgrid-power-pack':   B + '1274412-REG/incipio_mt_381_blk_offgrid_moto_mod.html',
    'moto-power-pack':              B + '1344087-REG/motorola_89912n_power_pack.html',
    'moto-turbopower-pack-battery': B + '1344088-REG/motorola_89929n_turbo_power_pack.html',
    'jbl-soundboost-2-speaker':     B + '1349421-REG/moto_pg38c01816_jbl_soundboost_speaker.html',
    'moto-style-shell':             B + '1274450-REG/motorola_89887n_moto_style_shell_black.html',
    'hasselblad-true-zoom': B + '1274335-REG/hasselblad_89867n_true_zoom_camera_for.html',
    'moto-smart-speaker-with-amazon-alexa': B + '1366963-REG/moto_pg38c02060_alexa_moto_mod.html',
    'moto-insta-share-projector':   B + '1274448-REG/motorola_89866n_moto_insta_share_projector.html',
    'polaroid-insta-share-printer': B + '1409624-REG/ventev_innovations_201460_motorola_mobility_llc.html',
    'moto-gamepad-console':   B + '1344102-REG/motorola_pg38c01911_gamepad.html',
    'moto-360-camera':        'https://www.bhphotovideo.com/c/product/1344089-REG/'
                              'motorola_89596n_360_camera.html',
    'tumi-power-pack':        'https://www.bhphotovideo.com/c/product/1593586-REG/'
                              'moto_89878n_tumi_power_pack_moto.html',
    'jbl-soundboost-speaker': 'https://www.bhphotovideo.com/c/product/1316888-REG/'
                              'jbl_89869n_soundboost_speaker_mods_white.html',
}


# Imagery held locally rather than fetched: the developer documentation archive
# next door has the only photographs of the MDK.
LOCAL_IMAGES = {
    'moto-mods-development-kit': [
        ('/data/claude/workspace/motomods_docs/docs/assets/img/MDK-w-perf-top.jpg', 'hero'),
        ('/data/claude/workspace/motomods_docs/docs/assets/img/Insitu_NoCover_DROID.png', 'gallery'),
        ('/data/claude/workspace/motomods_docs/docs/assets/img/Exploded+View.png', 'gallery'),
        ('/data/claude/workspace/motomods_docs/docs/assets/img/1E9A0366-Edit.jpg', 'gallery'),
        ('/data/claude/workspace/motomods_docs/docs/assets/img/PerforatedCard.png', 'gallery'),
    ],
}


RED_DOT = 'https://www.red-dot.org/project/'
IF_DESIGN = 'https://ifdesign.com/en/winner-ranking/project/'

# Awards won by individual products. `tier` is the distinction or category
# within the award; `jury` quotes the published citation (Red Dot) or project
# statement (iF).
AWARDS = {
    'moto-gamepad-console': [
        {'award': 'Red Dot Design Award', 'year': 2018, 'tier': 'Winner',
         'jury': 'With the Moto Gamepad, control of a video game by smartphone '
                 'is significantly easier to accomplish. Its dynamic design is '
                 'also convincing.',
         'url': RED_DOT + 'moto-gamepad-24946-24945'},
        {'award': 'iF Design Award', 'year': 2019, 'tier': 'Product Design, Gaming/VR/AR',
         'jury': "In collaboration with Lenovo's Legion gaming division, Gamepad "
                 'Mod designed for Moto Z series phones offers the best analog '
                 'gaming experience on mobile. The Mod platform connector helps '
                 'to avoid controller lag and troublesome Bluetooth connections '
                 'relied upon by competitors.',
         'url': IF_DESIGN + 'moto-gamepad-mod/259912'},
    ],
    'moto-360-camera': [
        {'award': 'Red Dot Design Award', 'year': 2018, 'tier': 'Winner',
         'jury': 'The Moto 360 Camera produces impressively sharp photos and '
                 'videos which can be shared remarkably easily. Furthermore, '
                 'the solution is very elegant.',
         'url': RED_DOT + 'moto-360-camera-24968-24967'},
    ],
    'moto-stereo-speaker': [
        {'award': 'Red Dot Design Award', 'year': 2018, 'tier': 'Winner',
         'jury': 'With its sporty design and cleverly integrated stand, the '
                 'speaker folio convinces right down the line.',
         'url': RED_DOT + 'moto-stereo-speaker-mod-24718-24717'},
        {'award': 'iF Design Award', 'year': 2019, 'tier': 'Product Design, Audio',
         'jury': 'The Stereo Speaker Mod design is playful yet highly refined, '
                 'sporting a colourful and durable exterior. The radial speaker '
                 'pattern and circular full-metal kickstand (50\u00b0) provide '
                 'superior product performance.',
         'url': IF_DESIGN + 'moto-speaker-mod/259104'},
    ],
    'moto-z4': [
        {'award': 'Red Dot Design Award', 'year': 2019, 'tier': 'Winner',
         'jury': '', 'url': RED_DOT + 'motoz4moto-mods-39689'},
    ],
}

# Awards given to the platform rather than to one product.
PLATFORM_AWARDS = [
    {'name': 'Moto Z Family with Moto Mods', 'award': 'Red Dot Design Award',
     'year': 2017, 'tier': 'Best of the Best',
     'jury': 'Thanks to a modular design, the innovative design of the Moto Z '
             'smartphone series offers the comfort of individual choice whether '
             'a loudspeaker or a video projector should be integrated into the '
             'mobile phone.',
     'url': RED_DOT + 'moto-z-family-with-moto-modstm-12418'},
    {'name': 'Moto Mods', 'award': 'CES Innovation Awards', 'year': 2017,
     'tier': 'Best of Innovation', 'jury': '',
     'url': 'https://bgr.com/tech/ces-2017-innovation-awards/'},
]
