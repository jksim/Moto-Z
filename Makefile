# Stages that hit the network are manual; their output is committed.
# CI only runs `site`.

PY := python3

.PHONY: all pages data images site clean

## Offline rebuild from the committed captures.
all: data site

## 1. Pick the best capture for every product (network).
audit:
	$(PY) tools/audit.py

## 2. Download those captures (network).
pages:
	$(PY) tools/fetch_pages.py

## 3. Fetch secondary specs (network).
enrich:
	$(PY) tools/enrich.py

## 4. Resolve and download product imagery (network, slow), then work out
##    where the product sits in each shot so cards crop to it.
images:
	$(PY) tools/fetch_images.py
	$(PY) tools/tidy_images.py --apply
	$(PY) tools/focus.py

## 5. Captures -> JSON, then merge, derive and validate. Offline.
data:
	$(PY) tools/extract.py
	$(PY) tools/normalize.py

site:
	npm run build
	node tools/check-links.mjs dist

clean:
	rm -rf dist .astro build/fetch_cache
