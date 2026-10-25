# Café1981 homepage preview

Static design preview of a new homepage for cafe1981.nl, published with GitHub Pages. Not indexed by search engines.

Live preview: https://januslikt.github.io/cafe1981/ (also `/nl/`, `/de/`, `/fr/`, `/es/`)

## How it is built

The pages are generated; edit the sources in `src/` and rebuild:

- `src/template.html`: page markup
- `src/style.css`: styles (inlined into each page)
- `src/strings.py`: all copy per language (EN, NL, DE, FR, ES), including the FAQ
- `src/build.py`: writes `index.html`, `nl/`, `de/`, `fr/`, `es/`, `sitemap.xml`, `robots.txt` and `llms.txt`

```
python3 src/build.py                # preview (noindex, robots.txt blocks crawlers)
python3 src/build.py --production   # for cafe1981.nl: indexable, canonical + hreflang on cafe1981.nl, sitemap in robots.txt
```

Each page carries its own title and description, canonical and hreflang links, Open Graph tags, and schema.org JSON-LD
(Restaurant/CafeOrCoffeeShop with address, geo, opening hours, menu with prices, Google rating, and a FAQPage).
`llms.txt` gives AI assistants a plain-text summary of the key facts.

Review quotes, rating and menu prices are copied from Google Maps and the September 2026 menus; update them in
`src/template.html`, `src/build.py` and `src/strings.py` when they change.
