# Moto Z & Moto Mods

**[View the site →](https://jksim.github.io/Moto-Z/)**

A reference site for the Motorola Moto Z phones (2016–2019) and the 20 Moto Mods
that snapped onto them. Motorola retired the line and took its product pages
down; this collects the specifications, copy and imagery in one place.

## Build

```console
$ npm ci
$ npm run build      # -> dist/
```

## Data

`data/*.json` is generated and committed. The site builds from it and never
touches the network.

```console
$ make audit    # choose the best archived capture per product
$ make pages    # download those captures into archive/pages/
$ make enrich   # secondary specs for pages with no spec table
$ make images   # resolve and download product imagery
$ make data     # captures -> JSON, merge, validate
```

The first four stages hit the Wayback Machine and are run by hand. `make data`
is offline and deterministic.

## Sources

Product copy, specifications and imagery come from Motorola's own archived
product pages. Where a page carried no specification table, figures come from
the manufacturer's stated specs or from Wikipedia; `tools/supplement.py` records
which. Prices are not listed — Motorola loaded them from a service that no
longer exists.

Motorola's developer documentation for the Moto Mods platform is preserved
separately at [MotoMods Developer Docs](https://jksim.github.io/MotoMods-Developer-Docs/).

## Licence

The tooling in `tools/` and the site configuration are MIT licensed. Product
text and images are © Motorola Mobility LLC and are not covered by that licence.
Moto, Moto Mods and Moto Z are trademarks of their respective owners. This
project is not affiliated with, sponsored by, or endorsed by Motorola, Lenovo or
Google.
