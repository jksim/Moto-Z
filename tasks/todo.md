# Moto Z & Moto Mods Archive — Task List

Full plan and rationale: [plan.md](plan.md)

Each phase is a complete vertical path. **Stop at each checkpoint for review.**

---

## Phase 0 — Capture audit

- [x] 0.1 Write `tools/wayback.py` (CDX query, fetch with backoff, magic-byte validation)
- [x] 0.2 Write `tools/manifest.py` — curated list of 20 Mods + 11 phone listings
- [x] 0.3 Write `tools/taxonomy.py` — 7 categories, phone aliases, sibling-doc cross-links
- [x] 0.4 Audit all ~31 listings: for each, fetch 2–3 candidate captures and record
      best timestamp, spec-block presence + markup variant, image count + path prefix
- [x] 0.5 Emit `data/coverage.json` and a readable summary table

**Acceptance:** every product has a chosen capture or an explicit "no usable
capture" verdict with a reason.

> ### ✅ CHECKPOINT 1 — review the coverage table
> If many Mods lack a spec block, the detail page must lean on imagery and copy.
> Do not build the detail page until this is known.

---

## Phase 1 — One Mod end to end (Hasselblad True Zoom)

- [x] 1.1 Scaffold Astro with **exact pinned versions** (no `^`), `.gitignore`, `public/.nojekyll`
- [x] 1.2 LICENSE with the scope carve-out (MIT covers `tools/` + config only)
- [x] 1.3 `tools/fetch_pages.py` → commit `archive/` *(project becomes offline-reproducible)*
- [x] 1.4 `tools/extract.py` for one product, with HTML sanitisation + storefront-CTA stripping
- [x] 1.5 `src/content.config.ts` — Zod schemas for mods and phones
- [x] 1.6 `src/lib/url.ts` + `BaseLayout` + one product route — **get `base` right first**
- [x] 1.7 Image stages: `index_images.py` → `select_images.py` → `fetch_images.py` into `src/assets/`
- [x] 1.8 `.github/workflows/deploy.yml` (ported structure, setup-node)
- [x] 1.9 `tools/check-links.mjs` base-path gate

**Acceptance:** live on GitHub Pages; Hasselblad page renders with real imagery,
≥20 spec pairs, and a provenance footer. Every image passes `file` as a real
image type, not HTML.

> ### ✅ CHECKPOINT 2 — review the live page
> Confirm the visual direction before repeating it 30 times.

---

## Phase 2 — The full Mods library

- [x] 2.1 Generalise `extract.py` with the markup strategies Phase 0 identified
- [x] 2.2 `tools/enrich.py` + `tools/supplement.py` — fill spec gaps from
      manufacturer sites, Wikipedia and a curated table so every Mod has specs
- [x] 2.3 Run the pipeline for all 20 Mods; review each record by hand
- [x] 2.4 Catalogue grid + 7 static category pages
- [x] 2.5 Filter island (vanilla TS, `client:idle`, query-string state)
- [x] 2.6 `.github/workflows/data-check.yml` determinism gate

**Acceptance:** 20 detail pages; filtering works with *and* without JS; no broken
images; `check-links.mjs` exits 0.

> ### ✅ CHECKPOINT 3 — review the library before moving to phones

---

## Phase 3 — The device family

- [x] 3.1 Second extractor variant for the phone template
- [x] 3.2 Merge the Z4's two listings (`-unlocked`, `-verizon`) into one record
- [x] 3.3 Device detail pages + device index

**Verify:** spot-check Moto Z against the capture — 5.5" AMOLED QHD, Snapdragon
820, 4 GB RAM, 5.19 mm depth, 136 g.

---

## Phase 4 — Compatibility

- [x] 4.1 `normalize.py` resolves phone names to slugs — **hard-fail on unmapped**
- [x] 4.2 Compatibility rules in `taxonomy.py` with explicit exceptions
      (5G Mod needs Z3/Z4; later Mods predate earlier phones)
- [x] 4.3 Compatibility matrix page (keyboard-scrollable)
- [x] 4.4 Reciprocal "works with" sections on both product types

**Acceptance:** the matrix is generated from data, not hand-written; every cell
traces to a source field.

---

## Phase 5 — Provenance, legal and polish

- [x] 5.1 `/about/` — what the product was, credits list of sources, prices omitted. Short
- [x] 5.2 Footer copyright, trademark notice, takedown offer, non-affiliation disclaimer
- [x] 5.3 `relatedDocs` cross-links into the developer-docs archive, and a link back from it
- [x] 5.4 Accessibility pass — alt text on every image, matrix keyboard-scrollable
- [x] 5.5 Responsive check at 390px and 1280px

---

## Standing constraints

- Prices are **omitted entirely** — settled decision, do not reintroduce
- CI **never contacts archive.org**; the scrape is manual and its outputs committed
- Wayback: **2 concurrent workers max**, retry with backoff
- Every internal link goes through `url.ts` — never a hand-written leading-slash href
- **Showcase, not an archive** — no provenance footers, capture dates or
  "not preserved" notices. Fill gaps from other sources rather than leaving them
- **Minimal prose.** Motorola's product copy is reproduced verbatim; everything
  we write (site copy, README, commit messages) states facts and stops
- **A single squashed commit at the end.** Nothing is committed until the site
  is complete and verified. Imperative subject, no body
