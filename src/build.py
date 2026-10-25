#!/usr/bin/env python3
"""Builds the static site: one page per language, plus sitemap.xml, robots.txt and llms.txt.

    python3 src/build.py                 # GitHub Pages preview: noindex, robots blocks everything
    python3 src/build.py --production    # cafe1981.nl: indexable, sitemap announced in robots.txt
"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from strings import LANGS, S  # noqa: E402

PRODUCTION = '--production' in sys.argv
BASE = 'https://cafe1981.nl/' if PRODUCTION else 'https://januslikt.github.io/cafe1981/'
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
MAPS = 'https://maps.google.com/?cid=8676354678998687309'
LUNCH_PDF = 'https://cafe1981.nl/wp-content/uploads/2026/09/cafe1981_lunch_sep_2026.pdf'
DINNER_PDF = 'https://cafe1981.nl/wp-content/uploads/2026/09/cafe1981_diner_sep_2026.pdf'

# Prices from the September 2026 lunch and dinner menus
PRICES = dict(florentine=17, pancakes=13.5, omelette=16.5, fish=22.5, lamb=24.5, sate=21.5, bitter=10.5)
WEEKDAYS = {
    'en': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
    'nl': ['Maandag', 'Dinsdag', 'Woensdag', 'Donderdag', 'Vrijdag', 'Zaterdag', 'Zondag'],
    'de': ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'],
    'fr': ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'],
    'es': ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'],
}
STAR = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.5l2.9 6.1 6.6.8-4.9 4.6 1.3 6.6L12 17.3l-5.9 3.3 1.3-6.6-4.9-4.6 6.6-.8z"/></svg>'
STARS_5 = STAR * 5
STARS_47 = STAR * 4 + f'<span class="part">{STAR}{STAR}</span>'

MENU = {
    'Breakfast & lunch (from 08:00)': [
        ('Eggs Royale', 17.5, 'Poached eggs, smoked salmon and creamy hollandaise sauce over a toasted English muffin.', False),
        ('Eggs Benedict', 16.5, 'Poached eggs, ham and creamy hollandaise over a toasted English muffin.', False),
        ('Eggs Florentine', 17, 'Poached eggs, avocado, sautéed spinach and creamy hollandaise over a toasted English muffin.', True),
        ('The Green Omelette', 16.5, 'Fluffy omelette with Gouda cheese, spinach, onions, crispy bacon and sourdough toast.', False),
        ('Scrambled Egg', 16.5, 'Creamy scrambled eggs with avocado and smoked salmon on sourdough bread.', False),
        ('"French" Toast', 14.5, 'Sweet toast with eggs, vanilla and cinnamon, strawberries, blueberries and clotted cream.', True),
        ('Stacked American Pancakes', 13.5, 'Thick, fluffy pancakes with maple syrup, strawberries and blueberries.', True),
        ('Smashed Avocado', 16.5, 'Avocado, cherry tomatoes, radishes, rucola and parmesan on a flatbread with balsamic glaze.', True),
        ('Hummus & Falafel', 15.5, 'Crispy falafel with hummus, cucumber, rucola and onion on a warm flatbread.', True),
        ('Fish & Chips', 22.5, 'Crispy battered white fish with golden fries and garlic sauce.', False),
        ('Veggie Burger', 17, 'Plant-based vegetable patty with tomatoes and cucumber, served with fries.', True),
    ],
    'Dinner (from 16:30)': [
        ('Vegetable Bitterballen', 10.5, 'Crunchy Dutch bitterballen with a creamy vegetable filling.', True),
        ('Chicken Sate', 21.5, 'Seasoned chicken skewers with peanut sauce and golden fries.', False),
        ('Hutspot with Rookworst', 20.5, 'Traditional Dutch mash of potatoes, carrots and onions with smoked rookworst sausage.', False),
        ('Lamb Chops', 24.5, 'Rosemary and garlic grilled lamb chops with fries.', False),
        ('Fish & Chips', 24.5, 'Crispy battered white fish with golden fries and garlic sauce.', False),
        ('Butter Chicken', 25.5, 'Tandoori chicken in a mild sauce of tomatoes, cream, butter and spices, with naan.', False),
        ('Saag Paneer', 22.5, 'Fresh cottage cheese in a delicately spiced spinach purée, with naan.', True),
        ('Dal', 22.5, 'Black lentils tempered with cumin, with naan.', True),
    ],
}

REVIEWS = [
    ('Brian', 'Great little find for a classic breakfast feast. Welcomed on arrival with a smile and positive vibe. Great service throught our visit. Eggs Benedict a great classic, well seasoned and silky hollandaise.'),
    ('Kirsty Fitzsimons', 'Great little cafe. Food was excellent and very well presented. Coffee was also very good. Service was fantastic and the right balance between attentive and leaving us to enjoy our meal. The location is great too. Central but slightly tucked away - great for people watching.'),
]


def page_path(l):
    return '' if l == 'en' else l + '/'


def rel(frm, to):
    """Relative link from the page of language `frm` to the page of language `to`."""
    up = '' if frm == 'en' else '../'
    return (up + page_path(to)) or './'


def price(v, l):
    s = f'{v:.2f}' if v % 1 else f'{v:.0f}'
    if l == 'en':
        return '€' + s
    s = s.replace('.', ',')
    return f'€ {s}' if l == 'nl' else f'{s} €'


def statement(text):
    out = []
    for w in text.split(' '):
        if w.startswith('*'):
            out.append(f'<span class="w b">{w.replace("*", "")}</span>')
        else:
            out.append(f'<span class="w">{w}</span>')
    return ' '.join(out)


def strip_tags(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s))


def head(l, t):
    url = BASE + page_path(l)
    lines = []
    if not PRODUCTION:
        lines.append('<meta name="robots" content="noindex, nofollow">')
    lines += [
        f'<title>{html.escape(t["title"])}</title>',
        f'<meta name="description" content="{html.escape(t["desc"])}">',
        f'<link rel="canonical" href="{url}">',
    ]
    for o in LANGS:
        lines.append(f'<link rel="alternate" hreflang="{o}" href="{BASE + page_path(o)}">')
    lines.append(f'<link rel="alternate" hreflang="x-default" href="{BASE}">')
    lines += [
        '<meta name="theme-color" content="#0b101c">',
        '<meta name="format-detection" content="telephone=no">',
        f'<link rel="icon" href="{BASE}img/pauw.svg" type="image/svg+xml">',
        '<meta property="og:type" content="restaurant">',
        '<meta property="og:site_name" content="Café1981">',
        f'<meta property="og:title" content="{html.escape(t["title"])}">',
        f'<meta property="og:description" content="{html.escape(t["desc"])}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{BASE}img/terrace.jpg">',
        '<meta property="og:image:width" content="1800">',
        '<meta property="og:image:height" content="1200">',
        f'<meta property="og:image:alt" content="{html.escape(t["alt_terrace"])}">',
        f'<meta property="og:locale" content="{t["locale"]}">',
    ]
    for o in LANGS:
        if o != l:
            lines.append(f'<meta property="og:locale:alternate" content="{S[o]["locale"]}">')
    lines += [
        '<meta name="twitter:card" content="summary_large_image">',
        '<meta name="geo.region" content="NL-NH">',
        '<meta name="geo.placename" content="Amsterdam">',
        '<meta name="geo.position" content="52.3623932;4.8862299">',
        '<meta name="ICBM" content="52.3623932, 4.8862299">',
    ]
    return '\n'.join(lines)


def jsonld(l, t):
    url = BASE + page_path(l)
    cafe = {
        '@type': ['Restaurant', 'CafeOrCoffeeShop'],
        '@id': BASE + '#cafe',
        'name': 'Café1981',
        'alternateName': ['Cafe1981', 'Café 1981', 'Cafe 1981'],
        'description': t['desc'],
        'url': BASE,
        'image': [BASE + 'img/terrace.jpg', BASE + 'img/interior.jpg'],
        'logo': BASE + 'img/logo.png',
        'email': 'Reservations@cafe1981.nl',
        'address': {'@type': 'PostalAddress', 'streetAddress': 'Korte Leidsedwarsstraat 203', 'postalCode': '1017 RB',
                    'addressLocality': 'Amsterdam', 'addressRegion': 'Noord-Holland', 'addressCountry': 'NL'},
        'geo': {'@type': 'GeoCoordinates', 'latitude': 52.3623932, 'longitude': 4.8862299},
        'hasMap': MAPS,
        'sameAs': [MAPS],
        'openingHoursSpecification': [{
            '@type': 'OpeningHoursSpecification',
            'dayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
            'opens': '08:00', 'closes': '21:00'}],
        'servesCuisine': ['Breakfast', 'Brunch', 'International', 'Dutch', 'Indian', 'Cocktails'],
        'priceRange': '€€',
        'currenciesAccepted': 'EUR',
        'acceptsReservations': True,
        'amenityFeature': [{'@type': 'LocationFeatureSpecification', 'name': 'Outdoor seating (terrace)', 'value': True}],
        'containedInPlace': {'@type': 'Place', 'name': 'Leidseplein, Amsterdam'},
        'hasMenu': {
            '@type': 'Menu', 'name': 'Café1981 menu', 'inLanguage': 'en', 'url': LUNCH_PDF,
            'hasMenuSection': [{
                '@type': 'MenuSection', 'name': sec,
                'hasMenuItem': [dict({
                    '@type': 'MenuItem', 'name': n, 'description': d,
                    'offers': {'@type': 'Offer', 'price': f'{p:.2f}', 'priceCurrency': 'EUR'}},
                    **({'suitableForDiet': 'https://schema.org/VegetarianDiet'} if veg else {})) for n, p, d, veg in items]}
                for sec, items in MENU.items()]},
        'aggregateRating': {'@type': 'AggregateRating', 'ratingValue': 4.7, 'bestRating': 5, 'worstRating': 1, 'reviewCount': 355},
        'review': [{'@type': 'Review', 'author': {'@type': 'Person', 'name': n}, 'inLanguage': 'en',
                    'reviewRating': {'@type': 'Rating', 'ratingValue': 5, 'bestRating': 5},
                    'reviewBody': b, 'publisher': {'@type': 'Organization', 'name': 'Google'}} for n, b in REVIEWS],
    }
    graph = [
        cafe,
        {'@type': 'WebSite', '@id': BASE + '#website', 'url': BASE, 'name': 'Café1981', 'inLanguage': LANGS,
         'publisher': {'@id': BASE + '#cafe'}},
        {'@type': 'WebPage', '@id': url + '#page', 'url': url, 'name': t['title'], 'description': t['desc'],
         'inLanguage': l, 'isPartOf': {'@id': BASE + '#website'}, 'about': {'@id': BASE + '#cafe'},
         'primaryImageOfPage': BASE + 'img/terrace.jpg'},
        {'@type': 'FAQPage', '@id': url + '#faq', 'inLanguage': l, 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': strip_tags(a)}} for q, a in t['faq']]},
    ]
    data = json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, indent=1)
    return '<script type="application/ld+json">\n' + data.replace('</', '<\\/') + '\n</script>'


def langmenu(l, t):
    items = ''.join(
        f'<li><a href="{rel(l, o)}" hreflang="{o}" lang="{o}"{" aria-current=\"true\"" if o == l else ""}>{S[o]["name"]}<span>{o.upper()}</span></a></li>'
        for o in LANGS)
    return (f'<details class="langsel"><summary aria-label="{t["lang_label"]}: {t["name"]}">{l.upper()}</summary>'
            f'<ul>{items}</ul></details>')


def footlangs(l):
    return '<span class="foot-langs">' + ''.join(
        f'<a href="{rel(l, o)}" hreflang="{o}" lang="{o}"{" aria-current=\"true\"" if o == l else ""}>{o.upper()}</a>'
        for o in LANGS) + '</span>'


def faq(t):
    return '\n'.join(
        f'        <details{" open" if i == 0 else ""}><summary><h3>{q}</h3><i aria-hidden="true"></i></summary><p>{a}</p></details>'
        for i, (q, a) in enumerate(t['faq']))


def hours(l, t):
    return ''.join(f'<div><span>{d}</span><span>{t["hours_short"]}</span></div>' for d in WEEKDAYS[l])


def build():
    tpl = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
    css = open(os.path.join(HERE, 'style.css'), encoding='utf-8').read()
    for l in LANGS:
        t = S[l]
        v = {k: x for k, x in t.items() if isinstance(x, str)}
        v.update({
            'lang': l, 'R': '' if l == 'en' else '../', 'CSS': css, 'MAPS': MAPS,
            'HEAD': head(l, t), 'JSONLD': jsonld(l, t), 'LANGMENU': langmenu(l, t), 'FOOTLANGS': footlangs(l),
            'STATEMENT': statement(t['s-p']), 'FAQ': faq(t), 'HOURS': hours(l, t),
            'STARS_5': STARS_5, 'STARS_47': STARS_47,
            'JS_L': json.dumps({'lang': l, 'open': t['open'], 'closed': t['closed'], 'today': t['today'],
                                'langs': {o: {'ask': S[o]['ask'], 'cta': S[o]['cta'], 'href': rel(l, o)} for o in LANGS}},
                               ensure_ascii=False),
        })
        v.update({'p_' + k: price(p, l) for k, p in PRICES.items()})

        def sub(m):
            k = m.group(1)
            if k not in v:
                raise KeyError(f'{l}: missing {k}')
            return v[k]
        out = re.sub(r'\{\{([\w-]+)\}\}', sub, tpl)
        path = os.path.join(OUT, page_path(l), 'index.html')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, 'w', encoding='utf-8').write(out)

    # sitemap with language alternates
    alts = ''.join(f'\n    <xhtml:link rel="alternate" hreflang="{o}" href="{BASE + page_path(o)}"/>' for o in LANGS)
    alts += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{BASE}"/>'
    urls = ''.join(f'\n  <url>\n    <loc>{BASE + page_path(l)}</loc>{alts}\n  </url>' for l in LANGS)
    open(os.path.join(OUT, 'sitemap.xml'), 'w').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        f'xmlns:xhtml="http://www.w3.org/1999/xhtml">{urls}\n</urlset>\n')

    if PRODUCTION:
        robots = ('# Search engines and AI assistants are welcome\nUser-agent: *\nAllow: /\n\n'
                  'User-agent: GPTBot\nAllow: /\n\nUser-agent: OAI-SearchBot\nAllow: /\n\n'
                  'User-agent: ClaudeBot\nAllow: /\n\nUser-agent: PerplexityBot\nAllow: /\n\n'
                  'User-agent: Google-Extended\nAllow: /\n\n'
                  f'Sitemap: {BASE}sitemap.xml\n')
    else:
        robots = '# Design preview: keep out of search engines. Run build.py --production for the live site.\nUser-agent: *\nDisallow: /\n'
    open(os.path.join(OUT, 'robots.txt'), 'w').write(robots)

    en = S['en']
    menu_md = '\n'.join(f'\n### {sec}\n' + '\n'.join(f'- {n} (€{p:.2f}){" · vegetarian" if veg else ""}: {d}' for n, p, d, veg in items)
                        for sec, items in MENU.items())
    faq_md = '\n'.join(f'\n### {q}\n{strip_tags(a)}' for q, a in en['faq'])
    langs_md = '\n'.join(f'- [{S[o]["name"]}]({BASE + page_path(o)})' for o in LANGS)
    open(os.path.join(OUT, 'llms.txt'), 'w', encoding='utf-8').write(f'''# Café1981

> Café-brasserie in Amsterdam at Korte Leidsedwarsstraat 203, on a quiet street between Leidseplein (2 min walk) and the Rijksmuseum (5 min walk). Open every day 08:00–21:00: breakfast and lunch from 08:00 (Eggs Royale, Eggs Benedict, omelettes, pancakes), cocktails and dinner from 16:30 (international, Dutch and Indian dishes). Terrace out front. Walk-ins welcome. Rated 4.7 out of 5 from 355 Google reviews (October 2026).

## Key facts

- Name: Café1981 (also written Cafe1981, Café 1981)
- Address: Korte Leidsedwarsstraat 203, 1017 RB Amsterdam, Netherlands
- Coordinates: 52.3623932, 4.8862299
- Opening hours: Monday to Sunday, 08:00–21:00
- Breakfast and lunch: from 08:00. Evening menu, dinner and cocktails: from 16:30
- Reservations: not needed; groups can email Reservations@cafe1981.nl
- Getting there: tram 1, 2, 5, 7 or 19 to Leidseplein. Walking: Leidseplein 2 min, Rijksmuseum 5 min, Vondelpark 8 min
- Price range: €€ (breakfast dishes €13.50–€17.50, dinner mains €20.50–€25.50)
- Vegetarian dishes every day
- Google rating: 4.7/5 from 355 reviews; guests most often mention the Eggs Benedict, the terrace, the Green Omelette and the French toast
- Google Maps: {MAPS}

## Menu highlights (September 2026)
{menu_md}

Full menus: [Lunch (PDF)]({LUNCH_PDF}) · [Dinner (PDF)]({DINNER_PDF})

## Frequently asked questions
{faq_md}

## Pages

{langs_md}
''')
    print('built', 'production' if PRODUCTION else 'preview', BASE)


if __name__ == '__main__':
    build()
