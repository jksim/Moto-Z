# Moto Z & Moto Mods — Product Archive Site

## Context

Motorola's Moto Z phone line (2016–2019) and its Moto Mods snap-on accessory
ecosystem are gone, and so is the consumer site that documented them. The
developer-facing half of that story is already preserved next door in
`/data/claude/workspace/motomods_docs` (published as
[MotoMods-Developer-Docs](https://jksim.github.io/MotoMods-Developer-Docs/)) —
but that archive is deliberately engineering-focused. It contains **no consumer
product information at all**: not one commercial Mod is named in it, and no Moto
Z model is distinguished beyond the bare string "Moto Z".

This project builds the missing consumer half: a GitHub Pages site that
**shows off the Moto Z device family and all 20 Moto Mods** — a product that now
has essentially no presence on the internet.

**This is a showcase, not an archive.** The goal is to present the product well
and completely. Motorola's captured pages are the richest single source, but
where they are thin the specs are filled in from elsewhere rather than left
blank. The site does not carry provenance apparatus, capture-date caveats or
"not preserved" notices — those belong to the sibling archive, not here.

`/data/claude/workspace/Moto_Z` is currently empty. This is a greenfield build.

## Findings that shape the plan

Verified directly against the Wayback Machine during planning, not assumed:

- **Source pages are server-rendered Drupal HTML**, so copy and spec tables
  extract cleanly with BeautifulSoup. (The 2019+ site moved to a JS-rendered
  VTEX store and is largely unusable — prefer 2016–17 captures.)
- **20 Moto Mods** and **~11 phone listings** (9 distinct devices) have captured
  US product pages.
- **Spec coverage is uneven.** Hasselblad True Zoom and Insta-Share Projector
  expose a full `field-specifications-full-lft/rgt` block (~25 fields). JBL
  SoundBoost, GamePad and 360 Camera do **not**, in the captures sampled. This
  is the biggest implementation risk and is why Phase 0 exists.
- **~10,000 archived product images**, under *four* path conventions
  (`library/us/products/<slug>/`, `library/us/moto-mods/`,
  `library/storage/products/`, `library/storage/moto-mods/`). Fetching needs the
  exact CDX timestamp + the `id_` modifier + following redirects; a bare-URL
  guess 404s.
- **Stated compatibility is stale.** The 2016 Hasselblad page lists three
  phones; the Mod physically works on all of them plus later generations.
  Motorola never updated the page. This must be modelled honestly, not "fixed".
- **Prices are omitted by decision.** They are partially recoverable (the Mods
  landing page carries server-rendered prices for the first seven Mods across 37
  dated captures), but the settled choice is to omit them entirely. Note
  Motorola's `$99,999.99` sentinel for unavailable items so it is never mistaken
  for data.
- **Wayback throttles hard.** 2 concurrent workers, retry with backoff, and
  validate magic bytes — it answers an unavailable capture with HTTP 200 and an
  HTML error page.

## Decisions

| Decision | Choice |
| --- | --- |
| Generator | **Astro** (static output, no adapter) |
| Prices | **Omitted entirely** |
| Scope | **Phones + Mods, US captures only** |
| Repo | **New standalone repo**, cross-linked with the developer-docs archive |

## Architecture

### The central principle

**The scrape is not part of the site build.** The pipeline is run by hand and
its outputs — captures, JSON, images — are committed. CI only runs `astro
build`, and **never contacts archive.org**. That keeps deploys fast,
deterministic, and independent of Wayback's availability.

### Repo layout

```
Moto_Z/
├── tools/                    # Python pipeline            [COMMITTED]
│   ├── wayback.py            #   shared: CDX, fetch+backoff, magic bytes
│   ├── manifest.py           #   curated slug→URL map — SINGLE SOURCE OF TRUTH
│   ├── taxonomy.py           #   categories, phone aliases, sibling-doc links
│   ├── fetch_pages.py extract.py index_images.py
│   ├── select_images.py fetch_images.py normalize.py report.py
├── archive/                  # exact capture bytes + index.json  [COMMITTED]
├── data/                     # generated JSON — the build's input [COMMITTED]
│   ├── mods.json phones.json compatibility.json images.json
├── src/
│   ├── content.config.ts     # Zod schemas
│   ├── assets/products/…     # localised images        [COMMITTED ~40 MB]
│   ├── lib/{url,images,compat}.ts
│   ├── components/ layouts/ pages/
├── .github/workflows/{deploy.yml, data-check.yml}
└── build/                    # scratch                  [GITIGNORED]
```

**Commit the raw captures** (~31 pages, ~3 MB) so every offline stage is
reproducible without re-scraping, and so a `git diff` on `data/` is meaningful
after an extractor change. Gitignored: `build/`, `node_modules/`, `dist/`,
`.astro/`.

### Data model

Astro 5 Content Layer with the `file()` loader over `data/*.json`, validated by
Zod. *Not* Markdown-per-product — 31 machine-generated files with 25 front-matter
keys each is a generated artefact wearing a hand-edited costume. *Not* a plain
JSON import either, since that loses Zod validation and `reference()`.

```jsonc
{
  "slug": "hasselblad-true-zoom",
  "name": "Hasselblad True Zoom",
  "brand": "Hasselblad",          // orthogonal to category — a second filter axis
  "category": "camera",
  "categorySecondary": [],
  "tagline": "Mobile photography x10",
  "summary": "...",
  "bodyHtml": "...",              // SANITIZED at extraction (see risks)
  "features":  [ { "title": "...", "body": "...", "imageKey": "..." } ],
  "specs":     [ { "label": "Sensor resolution", "value": "12MP" } ],
  "facets":    { "weightG": 145, "opticalZoom": 10, "sensorMp": 12 },
  "compatibility": {
    "rawText":  "Moto Z Droid, Moto Z Force Droid, Moto Z Play Droid",
    "stated":   ["moto-z-droid-edition", "..."],   // what the page said
    "inferred": ["moto-z2-play", "..."]            // mechanically compatible
  },
  "images": [ { "key": "...", "role": "hero", "alt": "..." } ],
  "relatedDocs": [ { "title": "Camera Controls protocol", "url": "..." } ],
  "status": "complete",
  "sources": [ { "url": "...", "waybackUrl": "...", "capture": "20160903014106",
                 "sha256": "...", "archivePath": "..." } ]
}
```

Three decisions worth stating outright:

- **`specs[]` stays verbatim and unnormalised.** A camera Mod and a battery Mod
  share maybe two fields; a unioned schema would be 90 nullable columns each
  product fills 12 of. Zod validates the *shape*, never the *keys*. Normalisation
  happens only in the small optional **`facets{}`** block, which powers sorting
  and comparison; a parse miss there is an absent optional field, never a wrong
  page, and unmatched labels are logged so the alias table grows deliberately.
- **Compatibility is stated plainly and correctly.** Every Mod fits every Moto Z
  generation mechanically; the real exceptions (the 5G Mod needs a Z3/Z4, the
  Gamepad and TurboPower arrived later) are recorded explicitly in
  `taxonomy.py`. Motorola's own pages list only the phones that shipped at the
  time, so they are used as a floor, not as the answer.
- **`sources` is a flat list of URLs** backing each record, surfaced once in a
  small credits line on `/about/` — not a per-page provenance footer. It is an
  array because the Z4 has two listings (`-unlocked`, `-verizon`) that are one
  phone.

Images are addressed by **key**, resolved at render through
`import.meta.glob('/src/assets/products/**/*')`, not by path and not via the
`image()` schema helper. This decouples the JSON from filenames and survives the
extension corrections that magic-byte validation performs.

### Mod taxonomy

| Category | n | Products |
| --- | --- | --- |
| Audio | 4 | JBL SoundBoost, SoundBoost 2, Moto Stereo Speaker, Smart Speaker with Alexa |
| Power | 6 | Incipio offGRID, mophie juice pack, Moto Power Pack, TurboPower, TurboPower Pack, Tumi |
| Camera | 2 | Hasselblad True Zoom, Moto 360 Camera |
| Projection & Printing | 2 | Insta-Share Projector, Polaroid Insta-Share Printer |
| Style & Protection | 3 | Style Shell, Style Shell with Wireless Charging, Moto Folio |
| Connectivity & Mounting | 2 | Moto 5G Mod, Incipio Vehicle Dock |
| Gaming & Input | 1 | Moto GamePad |

Categories are an explicit dict in `taxonomy.py`, **never inferred from slugs**
(inference breaks on the Alexa speaker and both Style Shells). Devices: Moto Z,
Z Force, Z Play, Z2 Play, Z2 Force, Z3, Z3 Play, Z4, plus the `moto-z-family`
overview as landing-page source.

### Pipeline

Seven stages, each `input dir → output dir`, no stage mutating its own input.
Network stages (1, 3, 5) are manual; pure stages (2, 4, 6, 7) are deterministic —
sorted keys, stable ordering — so identical input bytes give byte-identical JSON.
That determinism is what makes the CI data-check gate possible.

| # | Script | Net | Out |
| --- | --- | --- | --- |
| 1 | `fetch_pages.py` | ✔ | `archive/pages/**`, `archive/index.json` |
| 2 | `extract.py` | — | `data/{mods,phones}.json`, `build/image_refs.json` |
| 3 | `index_images.py` | ✔ | `archive/cdx/images.tsv.gz` |
| 4 | `select_images.py` | — | `build/image_plan.json` |
| 5 | `fetch_images.py` | ✔ | `src/assets/products/**`, `data/images.json` |
| 5b | `enrich.py` | ✔ | secondary-source specs → `data/supplement.json` |
| 6 | `normalize.py` | — | merge, compatibility edges, facets, validation |
| 7 | `report.py` | — | coverage table |

### Filling the spec gaps

Motorola's US captures carry a full spec table for some products and none for
others. Specs are sourced in this order, and `normalize.py` merges them with
earlier sources winning:

1. **Motorola US captures** — official copy, official imagery, spec tables where present.
2. **Manufacturer pages via Wayback** — JBL, Incipio, mophie, Polaroid, TUMI for their own Mods.
3. **Wikipedia** — device specs and platform context (reachable; the article covers Z, Z Force and Z Play directly).
4. **`tools/supplement.py`** — a hand-curated table for whatever remains, each entry carrying the URL it came from.

Non-`/us/` Motorola locales exist (`at`, `be`, `bg`) but no English ones, so they
are not used. GSMArena is behind Cloudflare and is not a usable source.

Capture selection picks the **largest capture** in the latest year group (bigger
= fuller server render), and validates it with a *positive* Drupal marker plus a
minimum byte size — not merely "is it HTML".

`fetch_images.py` is a direct port of the sibling's `tools/fetch_assets.py`:
`fetch()` with backoff, `MAGIC`/`sniff()`/`looks_valid()`, `try_url()`,
`on_disk()`, and the 2-worker pool all port unchanged. `load_cdx_index()` needs
new prefixes and **pagination** (10k images will exceed the sibling's flat
`limit=20000`). `apply_renames()` is dropped entirely — it rewrites Markdown,
and here nothing needs touching because images are addressed by key.
`dimensions()` from `upgrade_images.py` folds into the first pass: try up to 4
renditions, measure each, keep the largest by pixel area, cap at 2400px.

### Site

Routes: `/`, `/mods/`, `/mods/[slug]/` ×20, `/mods/category/[category]/` ×7,
`/phones/`, `/phones/[slug]/` ×9, `/compatibility/`, `/about/`, `/404`.

**One interactive island**, vanilla TS (~60 lines), `client:idle`. The server
renders all 20 cards; the island only toggles `hidden` and writes filter state to
the query string so a filtered view is shareable. Filter chips are real links to
the static category pages, which the island intercepts — progressive
enhancement, not a JS-only feature. No React/Preact for 20 checkboxes, and no
client-side search index for 31 pages.

## Phases

Each phase is a complete vertical path, not a layer. Stop at each checkpoint.

---

### Phase 0 — Capture audit *(first; it sizes everything else)*

**0.1** For all ~31 product listings, query CDX, fetch 2–3 candidate captures
each, and record: best capture timestamp, whether a spec block is present and
under which markup variant, image count and path prefix, whether copy is intact.

- *Output:* `data/coverage.json` + a readable summary table.
- *Acceptance:* every product has either a chosen capture or an explicit "no
  usable capture" verdict with a reason.

> **CHECKPOINT 1** — Review the coverage table together. If many Mods lack a spec
> block, the detail page must lean on imagery and copy instead of spec tables.
> Do not build the detail page until this is known.

---

### Phase 1 — One Mod, end to end

Build the entire path for **Hasselblad True Zoom** (richest verified data) before
generalising anything.

**1.1** Scaffold Astro (exact pinned versions, no `^`), `.gitignore`,
`public/.nojekyll`, and the LICENSE with the scope carve-out — MIT covers
`tools/` and site config only; reproduced Motorola content is not licensed.

**1.2** `manifest.py` + `taxonomy.py` + `wayback.py` + `fetch_pages.py` →
commit `archive/`. *The project is now offline-reproducible.*

**1.3** `extract.py` → `data/mods.json` for one product, with HTML
sanitisation and storefront-CTA stripping.
- *Acceptance:* ≥20 spec pairs, compatibility `rawText`, populated `sources`.

**1.4** `src/lib/url.ts` + `BaseLayout` + one product route. **Get `base` right
before building 30 templates.**

**1.5** Image stages 3–5 for this Mod into `src/assets/`.
- *Acceptance:* every referenced image exists and `file` reports a real image
  type, not HTML.

**1.6** `deploy.yml` (ported structure, setup-node) + `check-links.mjs`
base-path gate.

- *Acceptance:* live on GitHub Pages, Hasselblad page correct with real imagery,
  specs and a provenance footer.

> **CHECKPOINT 2** — Look at the live page and confirm the visual direction
> before repeating it 30 times.

---

### Phase 2 — The full Mods library

**2.1** Generalise `extract.py` with the markup strategies Phase 0 found.
**2.1b** `enrich.py` + `supplement.py` — fill every product that Phase 0 flagged
as spec-less, so each Mod ships a real spec table.
**2.2** Run for all 20 Mods; review each record by hand.
**2.3** Catalogue grid + 7 static category pages.
**2.4** The filter island.
**2.5** `data-check.yml` determinism gate.

- *Acceptance:* 20 detail pages, filtering works with and without JS, no broken
  images, `check-links.mjs` exits 0.

> **CHECKPOINT 3** — Review the library before moving to phones.

---

### Phase 3 — The device family

**3.1** Extend the pipeline to the phones (a second extractor variant — the
phone template differs), merging the Z4's two listings into one record.
**3.2** Device detail pages and index.

- *Verify:* spot-check Moto Z against the verified capture — 5.5" AMOLED QHD,
  Snapdragon 820, 4 GB RAM, 5.19 mm depth, 136 g.

---

### Phase 4 — Compatibility

**4.1** `normalize.py` resolves names to slugs (hard-fail on unmapped) and emits
the edge list from the compatibility rules in `taxonomy.py`.
**4.2** Matrix page + reciprocal "works with" on both product types.

- *Acceptance:* the matrix is generated from data, not hand-written, and the
  real exceptions (5G Mod needs Z3/Z4, later Mods predate earlier phones) are
  correct.

---

### Phase 5 — Provenance, legal and polish

**5.1** `/about/`: a short page — what the Moto Z and Moto Mods were, where the
material came from (a credits list of source URLs), and that prices are omitted.
**5.2** Footer copyright on every page, trademark notice, "not affiliated with
Motorola or Lenovo".
**5.3** Reciprocal cross-links: `relatedDocs` per product into the sibling site,
and a link back from its `docs/about.md` and nav.
**5.4** Accessibility pass (alt text on every image, matrix keyboard-scrollable)
and Lighthouse.

## Verification

- **Per product:** validates against the Zod schema; rendered specs match the
  archived capture by eye.
- **Build:** `npm run build` clean; `node tools/check-links.mjs dist` exits 0.
- **Determinism:** re-running pure stages produces no `git diff` in `data/`.
- **Deployed:** images load under the project sub-path; filtering degrades
  gracefully without JS.

## Risks

| Risk | Mitigation |
| --- | --- |
| Spec blocks missing for many Mods | Phase 0 measures it before any UI is built |
| Wayback throttling / downtime | 2 workers, backoff, response cache, captures committed, CI offline |
| 200-with-HTML-error-page | Magic bytes for binaries; positive Drupal marker + min size for HTML |
| Markup differs per product/era | Per-product strategy chosen in `manifest.py`, not one brittle selector |
| **Stored XSS from archived HTML** | Captures contain `<script>` and `onclick`. Sanitise at extraction with a tag/attribute allowlist; assert in `normalize.py` that no stored HTML matches `/<script\|on\w+=\|javascript:/i` |
| **Base-path regression** | Every internal link goes through `url.ts`; CI link-check gate. This *will* happen at least once |
| Compatibility wrong at the edges | Rules in `taxonomy.py` with explicit exceptions, not scraped from stale pages |
| Missing imagery | Source from the manufacturer's own site via Wayback before accepting a gap |
| Supplemented specs drift from fact | Every supplement entry carries its source URL and is reviewed once |
| Repo bloat | Cap at 2400px, gzip the CDX index, ~100 MB budget |
| Astro major-version churn | Pin exact versions, commit the lockfile, no auto-update |

**Explicitly rejected:** Markdown-per-product; a unioned spec schema; a JS
framework for filtering 20 items; client-side search; re-scraping in CI; images
in `public/` (loses `astro:assets`); inferring categories from slugs; hunting
other sources for the missing prices.

## Writing and commits

**Prose is kept to a minimum.** The site, the README and commit messages state
facts and stop. No narrative, no scene-setting, no explaining the significance of
the archive to the reader.

- **Site copy:** Motorola's own product copy is reproduced verbatim (that *is*
  the archive). Everything written by us — `/about/`, section intros, empty
  states — is factual and short. `/about/` is a provenance table plus a gap list,
  not an essay.
- **README:** what this is, how to build it, where the data comes from, licence.
  Roughly the length of the sibling archive's README or shorter.
- **Commit messages:** imperative subject line, no body unless a decision needs
  recording in one sentence. Matches the sibling repo's existing style.

**Commits: a single squashed commit at the end.** Nothing is committed until
the site is complete and verified; the repo is initialised at the start and the
one commit is made at the end of Phase 5.
