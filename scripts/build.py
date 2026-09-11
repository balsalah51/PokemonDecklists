#!/usr/bin/env python3
"""Generate the Pokémon Decklists static site from scraped JSON."""
from __future__ import annotations

import html as htmlmod
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from editorial import ESSAYS, GUIDE_BODY, type_body

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data" / "lists.json").read_text())
PRICES = json.loads((ROOT / "data" / "prices.json").read_text())
CARDS = json.loads((ROOT / "data" / "cards.json").read_text()) if (ROOT / "data" / "cards.json").exists() else []
LISTS = DATA["lists"]
SITE = "Pokémon Decklists"
SHORT = "PKMN"
CANON = "https://pokemondecklists.com"
PARTNER = "https://partner.tcgplayer.com/c/7670706/1780961/21018"
ADS = "ca-pub-1074015774205047"
NOW = "2026-09-11"
CSS_V = "pkdl-8"

TYPES = [
    ("grass", "Grass", "#4c9a2a"),
    ("fire", "Fire", "#e85d04"),
    ("water", "Water", "#1d7fc4"),
    ("lightning", "Lightning", "#d4a017"),
    ("psychic", "Psychic", "#c44b9f"),
    ("fighting", "Fighting", "#c45c2a"),
    ("darkness", "Darkness", "#5c4d7a"),
    ("metal", "Metal", "#6d7c8a"),
    ("fairy", "Fairy", "#e89bb8"),
    ("dragon", "Dragon", "#6b4c9a"),
    ("colorless", "Colorless", "#9aa0a6"),
]
TYPE_HEX = {k: h for k, _, h in TYPES}
TYPE_LABEL = {k: lab for k, lab, _ in TYPES}

FORMATS = [
    {
        "id": "standard",
        "name": "Standard",
        "kicker": "Championship format",
        "blurb": "H, I, and J regulation marks. The 2026 World Championships and Play! Pokémon circuit.",
        "legal": "Cards with H, I, or J regulation marks (G rotated April 2026).",
        "official": "https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources/",
        "img": "/img/formats/standard.jpg",
        "size": "60 cards",
    },
    {
        "id": "expanded",
        "name": "Expanded",
        "kicker": "Black & White onward",
        "blurb": "The wide constructed pool from Black & White to now, with its own ban list.",
        "legal": "Black & White (2011) through current sets, minus the Expanded ban list.",
        "official": "https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources/",
        "img": "/img/formats/expanded.jpg",
        "size": "60 cards",
    },
    {
        "id": "glc",
        "name": "Gym Leader Challenge",
        "kicker": "Singleton community format",
        "blurb": "One type, one of each card name, no rule-box Pokémon. The locals format people actually brew.",
        "legal": "Singleton, single type, no ex/V/GX/Radiant/ACE SPEC. Community ban list at gymleaderchallenge.com.",
        "official": "https://gymleaderchallenge.com/",
        "img": "/img/formats/glc.jpg",
        "size": "60 cards",
    },
    {
        "id": "pocket",
        "name": "Pokémon TCG Pocket",
        "kicker": "Mobile constructed",
        "blurb": "Twenty-card lists for the phone game. Different energy rules, huge online cups.",
        "legal": "Pocket sets and energy rules as published in Pokémon TCG Pocket.",
        "official": "https://tcgpocket.pokemon.com/",
        "img": "/img/formats/pocket.jpg",
        "size": "20 cards",
    },
    {
        "id": "unlimited",
        "name": "Unlimited",
        "kicker": "Vintage & EX era",
        "blurb": "Old paper. Base–Neo cups and EX-on-2 community events keep the pre-rotation piles alive.",
        "legal": "All Pokémon TCG cards unless a cup posts its own era (Base–Neo, EX, etc.).",
        "official": "https://www.pokemon.com/us/pokemon-tcg/",
        "img": "/img/formats/unlimited.jpg",
        "size": "60 cards",
    },
]
FMT = {f["id"]: f for f in FORMATS}

SHOP = {
    "sleeves": [
        ("Dragon Shield Matte Jet", "100 standard-size sleeves (63×88 mm). Black matte. Fits a 60-card Pokémon list plus extras.", "sleeve-jet.jpg", "https://amzn.to/4qFzNrw"),
        ("Dragon Shield Dual Matte Red / Gold", "100 standard-size Dual Matte sleeves. Red face, gold back (ART15065).", "sleeve-red-gold.jpg", "https://amzn.to/46s2YVu"),
        ("Dragon Shield Dual Matte Soul", "100 standard-size Dual Matte sleeves. Metallic purple Dual Soul (ART15062).", "sleeve-soul.jpg", "https://amzn.to/4wMuTKw"),
        ("Dragon Shield Matte Midnight Blue", "100 standard-size matte sleeves. Midnight Blue finish.", "sleeve-midnight.jpg", "https://amzn.to/4hSoJoD"),
        ("Dragon Shield Dual Matte Cobalt / Silver", "100 standard-size Dual Matte sleeves. Cobalt face, silver back.", "sleeve-cobalt-silver.jpg", "https://amzn.to/4wNVOFR"),
        ("Dragon Shield Matte Amethyst", "100 standard-size matte sleeves. Amethyst purple finish.", "sleeve-amethyst.jpg", "https://amzn.to/3SSyuZM"),
        ("Hard plastic toploaders (3×4, 200-pack)", "Rigid 3×4 in. holders for singles, trades, and binder extras. Not for in-game play.", "sleeve-toploaders.jpg", "https://amzn.to/4ixZmZn"),
    ],
    "dice": [
        ("Power counter dice (+1000 / −1000)", "32-piece set of +1000 to +6000 and −1000 to −6000 counters. Built for damage tracking.", "dice-power.jpg", "https://amzn.to/46pbKUi"),
        ("Official One Piece Premium Dice Set", "Licensed dice in a collectible tin. Same shop SKU as OPDB — works as a table set for any TCG.", "dice-luffy.jpg", "https://amzn.to/4xEOaiF"),
        ("Yiotfandoll 16 mm D6 (blue / black)", "10 acrylic 16 mm six-siders. Cheap table set for prize markers or kitchen-table counters.", "dice-acrylic.jpg", "https://amzn.to/4gQtpdA"),
    ],
    "playmats": [
        ("Custom TCG playmat with bag", "Personalized playmat with play-zone options and a non-slip surface. Ships with a mat bag.", "playmat-custom.jpg", "https://amzn.to/4hWBnD9"),
        ("Skeleton playmat set", "14×24 in. TCG playmat with two skull dice and a storage bag. Same OPDB shop link.", "playmat-skeleton.jpg", "https://amzn.to/4ypjUbx"),
    ],
    "deck-boxes": [
        ("Wanted poster deck box", "Themed box with commander display. Holds about 120 singles or 100 double-sleeved cards.", "deckbox-wanted.jpg", "https://amzn.to/4xuKTlW"),
        ("4-pack magnetic deck boxes", "Four magnetic boxes. Each holds 100+ double-sleeved cards — enough for several 60-card lists.", "deckbox-4pack.jpg", "https://amzn.to/3SSyyJ0"),
        ("MAKHISTORY Commander deck box", "Magnetic deck case with dice tray, 35pt holder, and two dividers. Fits 100+ double-sleeved cards.", "deckbox-makhistory.jpg", "https://amzn.to/4gVNBuw"),
        ("UAONO Commander deck box", "Magnetic commander box. Fits 100 double-sleeved cards and a toploader.", "deckbox-uaono.jpg", "https://amzn.to/4zVuIzE"),
    ],
    "extras": [
        ("Koonie USB desk fan", "Small quiet USB fan for long events. Strong airflow, adjustable, folds for the bag.", "extra-desk-fan.jpg", "https://amzn.to/4cc2lD5"),
    ],
}
SHOP_TITLES = {
    "sleeves": "Sleeves",
    "dice": "Dice",
    "playmats": "Playmats",
    "deck-boxes": "Deck boxes",
    "extras": "Table extras",
}


def e(s) -> str:
    return htmlmod.escape("" if s is None else htmlmod.unescape(str(s)))


def ld_script(obj) -> str:
    return (
        '  <script type="application/ld+json">'
        + json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        + "</script>\n"
    )


def short_title(title: str) -> str:
    return re.split(r"\s+\|\s+", title or "")[0].strip() or SITE


def site_graph() -> dict:
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": CANON + "/#org",
                "name": SITE,
                "alternateName": ["PKMN", "Pokemon Decklists"],
                "url": CANON + "/",
                "logo": {
                    "@type": "ImageObject",
                    "url": CANON + "/img/pkdl-logo-192.png",
                    "width": 192,
                    "height": 192,
                },
                "description": "Fan site for Pokémon TCG decklists, format hubs, and card prices. Not affiliated with Nintendo or The Pokémon Company.",
            },
            {
                "@type": "WebSite",
                "@id": CANON + "/#site",
                "name": SITE,
                "url": CANON + "/",
                "inLanguage": "en-US",
                "publisher": {"@id": CANON + "/#org"},
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": CANON + "/search.html?q={search_term_string}",
                    "query-input": "required name=search_term_string",
                },
            },
        ],
    }


def crumbs_for(path: str, title: str) -> list[tuple[str, str]]:
    path = path or "/"
    if path == "/":
        return []
    out = [("Home", "/")]
    parts = [p for p in path.strip("/").split("/") if p]
    if not parts:
        return out
    leaf = parts[-1].replace(".html", "")
    page = short_title(title)

    if parts[0] == "formats":
        out.append(("Formats", "/formats/"))
        if len(parts) > 1:
            out.append((FMT.get(leaf, {}).get("name") or page, path))
        return out
    if parts[0] == "decklists" and len(parts) >= 2:
        fmt_id = parts[1]
        out.append(("Formats", "/formats/"))
        out.append((FMT.get(fmt_id, {}).get("name") or fmt_id, f"/formats/{fmt_id}.html"))
        out.append((page, path))
        return out
    if parts[0] == "collectibles":
        out.append(("Collectibles", "/collectibles/"))
        if len(parts) == 1:
            return out
        if parts[1].startswith("movers"):
            out.append(("Price movers", "/collectibles/movers.html"))
            return out
        if parts[1] == "cards":
            out.append(("Card catalog", "/collectibles/cards/"))
            if len(parts) > 2:
                out.append((page, path))
            return out
        if parts[1] == "sets":
            out.append(("Sets", "/collectibles/sets/"))
            if len(parts) > 2:
                out.append((leaf, path))
            return out
        return out
    if parts[0] == "shop":
        out.append(("Shop", "/shop/"))
        if len(parts) > 1:
            out.append((SHOP_TITLES.get(leaf, page), path))
        return out
    if parts[0] == "guides":
        out.append(("Guides", "/guides/"))
        if len(parts) == 1:
            return out
        if parts[1] == "types" and len(parts) > 2:
            out.append((TYPE_LABEL.get(leaf, page) + " type", path))
            return out
        out.append((page, path))
        return out

    if parts[0] == "market":
        out.append(("Market", "/market/"))
        if len(parts) > 1:
            labels = {
                "watchlist.html": "Watchlist",
                "binder.html": "Binder",
                "compare.html": "Compare",
                "alerts.html": "Alerts",
                "staples.html": "Staples",
            }
            out.append((labels.get(parts[1], page), path))
        return out

    singles = {
        "tier-list.html": ("Tier list", "/tier-list.html"),
        "price-tracker.html": ("Price tracker", "/price-tracker.html"),
        "events.html": ("Events", "/events.html"),
        "privacy.html": ("Privacy", "/privacy.html"),
        "search.html": ("Search", "/search.html"),
        "format.html": ("Format rules", "/format.html"),
        "404.html": ("Page not found", "/404.html"),
        "partners.html": ("Partners", "/partners.html"),
        "gallery.html": ("Artwork gallery", "/gallery.html"),
        "desk.html": ("The Desk", "/desk.html"),
        "about.html": ("About", "/about.html"),
        "methodology.html": ("Methodology", "/methodology.html"),
        "faq.html": ("FAQ", "/faq.html"),
    }
    if parts[0] in singles:
        out.append(singles[parts[0]])
    return out


def crumb_ld(items: list[tuple[str, str]]) -> str:
    if not items:
        return ""
    return ld_script(
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": i,
                    "name": name,
                    "item": CANON + href,
                }
                for i, (name, href) in enumerate(items, 1)
            ],
        }
    )


def aff(url: str) -> str:
    if "partner.tcgplayer.com" in url or "amzn.to" in url:
        return url
    return PARTNER + "?u=" + quote(url, safe="")


def tcg_search(name: str, setc: str = "", num: str = "") -> str:
    q = " ".join(x for x in [name, setc, num] if x)
    return aff("https://www.tcgplayer.com/search/pokemon/product?q=" + quote(q) + "&productLineName=pokemon")


def clean(s: str) -> str:
    return htmlmod.unescape(s or "")


def basic_type(name: str) -> str | None:
    n = (name or "").lower()
    n = re.sub(r"\s+energy$", "", n)
    mapping = [
        ("lightning", "lightning"),
        ("electric", "lightning"),
        ("darkness", "darkness"),
        ("dark", "darkness"),
        ("psychic", "psychic"),
        ("fighting", "fighting"),
        ("metal", "metal"),
        ("steel", "metal"),
        ("grass", "grass"),
        ("fire", "fire"),
        ("water", "water"),
        ("fairy", "fairy"),
        ("dragon", "dragon"),
        ("colorless", "colorless"),
        ("magnetic metal", "metal"),
        ("telepathic psychic", "psychic"),
        ("growing grass", "grass"),
        ("spiky", "grass"),
        ("mist", "water"),
    ]
    for needle, key in mapping:
        if needle in n:
            return key
    return None


def list_types(lst: dict) -> list[str]:
    counts = Counter()
    for card in (lst.get("decklist") or {}).get("energy") or []:
        t = basic_type(card.get("name") if isinstance(card, dict) else str(card))
        if t:
            counts[t] += int(card.get("count") or 1) if isinstance(card, dict) else 1
    if counts:
        return [t for t, _ in counts.most_common()]
    # pocket often stores energy as names only
    for name in lst.get("energies") or []:
        t = basic_type(name)
        if t and t not in counts:
            counts[t] += 1
    return [t for t, _ in counts.most_common()]


def color_class(types: list[str]) -> str:
    if not types:
        return "color-colorless"
    if len(types) == 1:
        return "color-" + types[0]
    return "color-" + types[0] + "-" + types[1]


def combo_key(types: list[str]) -> tuple:
    pair = tuple(sorted(types[:2])) if types else ("colorless",)
    return pair


def href_list(lst: dict) -> str:
    return f"/decklists/{lst['format']}/{lst['id']}.html"


def nav(current: str = "") -> str:
    def a(href, label, key):
        cur = ' aria-current="page"' if current == key else ""
        return f'<a href="{href}"{cur}>{label}</a>'
    return f"""      <nav id="site-nav" class="site-nav" aria-label="Primary">
        {a("/formats/", "Formats", "formats")}
        {a("/tier-list.html", "Tier list", "tier")}
        {a("/collectibles/", "Collectibles", "collect")}
        {a("/market/", "Market", "market")}
        {a("/events.html", "Events", "events")}
        {a("/guides/", "Guides", "guides")}
        {a("/desk.html", "Desk", "desk")}
        {a("/shop/", "Shop", "shop")}
        {a("/partners.html", "Partners", "partners")}
      </nav>"""


def header(current: str = "") -> str:
    return f"""  <header class="site-header">
    <div class="header-inner">
      <a class="brand" href="/" aria-label="Pokémon Decklists home">
        <img class="logo" src="/img/pkdl-avatar.png" width="48" height="48" alt="" />
        <div>
          <p class="site-name">Pokémon Decklists</p>
          <p class="subtitle">Tournament lists · Market desk · Fan journal</p>
        </div>
      </a>
      <form class="header-search" method="get" action="/search.html" role="search">
        <label class="visually-hidden" for="nav-q">Search decklists</label>
        <input id="nav-q" type="search" name="q" placeholder="Search lists, cards, events" />
        <button type="submit">Search</button>
      </form>
      <button type="button" class="nav-toggle" aria-expanded="false" aria-controls="site-nav">Menu</button>
{nav(current)}
    </div>
  </header>
  <div class="wrap">
"""


def footer(current: str = "") -> str:
    return """    <footer class="site-footer">
      <div class="footer-grid">
        <div>
          <p class="footer-brand">Pokémon Decklists</p>
          <p>Fan-made Pokémon TCG decklists, format hubs, and card prices. Not affiliated with Nintendo, The Pokémon Company, Creatures Inc., GAME FREAK, or Wizards of the Coast.</p>
        </div>
        <nav aria-label="Compete">
          <p class="footer-head">Compete</p>
          <a href="/formats/">Formats</a>
          <a href="/tier-list.html">Tier list</a>
          <a href="/events.html">Events</a>
          <a href="/guides/">Guides</a>
          <a href="/desk.html">The Desk</a>
        </nav>
        <nav aria-label="Market">
          <p class="footer-head">Market</p>
          <a href="/market/">Price community</a>
          <a href="/market/watchlist.html">Watchlist</a>
          <a href="/market/binder.html">Binder P&amp;L</a>
          <a href="/market/compare.html">Compare prints</a>
          <a href="/price-tracker.html">Full tracker</a>
        </nav>
        <nav aria-label="Collect">
          <p class="footer-head">Collect</p>
          <a href="/collectibles/">Collectibles</a>
          <a href="/gallery.html">Artwork gallery</a>
          <a href="/shop/">Shop</a>
          <a href="/partners.html">Partner programs</a>
          <a href="/about.html">About</a>
          <a href="/methodology.html">Methodology</a>
          <a href="/faq.html">FAQ</a>
          <a href="/search.html">Search</a>
          <a href="/privacy.html">Privacy</a>
          <span class="discord-nav" title="Discord coming soon">Discord — invite soon</span>
        </nav>
      </div>
      <p class="footer-legal">© <span id="year"></span> Pokémon Decklists. As an Amazon Associate I earn from qualifying purchases. TCGplayer links are affiliate links.</p>
    </footer>
  </div>
  <script src="/js/tcgplayer-config.js" defer></script>
  <script src="/js/tcgplayer.js" defer></script>
  <script src="/js/site.js" defer></script>
  <script src="/js/market.js" defer></script>
</body>
</html>"""


def head(
    title: str,
    desc: str,
    path: str,
    image: str = "/img/pkdl-hero.jpg",
    extra: str = "",
    og_type: str = "website",
    image_alt: str = "Pokémon Decklists — Pokémon TCG decklists by format",
    published: str | None = None,
    robots: str = "index, follow, max-image-preview:large",
) -> str:
    url = CANON + path
    img = image if image.startswith("http") else CANON + image
    hero = str(image).endswith("pkdl-hero.jpg")
    img_w, img_h = ("1920", "1080") if hero else ("367", "512")
    crumbs = crumbs_for(path, title)
    dates = ""
    if published:
        dates = (
            f'  <meta property="article:published_time" content="{e(published)}" />\n'
            f'  <meta property="og:updated_time" content="{e(published)}" />\n'
        )
    return f"""<!doctype html>
<html lang="en-US">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover" />
  <title>{e(title)}</title>
  <meta name="description" content="{e(desc)}" />
  <meta name="author" content="Pokémon Decklists" />
  <meta name="color-scheme" content="light" />
  <link rel="stylesheet" href="/css/site.css?v={CSS_V}" />
  <link rel="canonical" href="{url}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link rel="preconnect" href="https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com" />
  <link rel="dns-prefetch" href="https://images.pokemontcg.io" />
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&amp;family=Source+Serif+4:opsz,wght@8..60,600;700&amp;display=swap" />
  <meta name="robots" content="{e(robots)}" />
  <meta name="theme-color" content="#c62828" />
  <meta name="application-name" content="Pokémon Decklists" />
  <meta name="apple-mobile-web-app-title" content="PKMN Decklists" />
  <meta name="format-detection" content="telephone=no" />
  <link rel="icon" href="/img/pkdl-logo-192.png" type="image/png" sizes="192x192" />
  <link rel="apple-touch-icon" href="/img/pkdl-logo-192.png" sizes="192x192" />
  <link rel="manifest" href="/site.webmanifest" />
  <link rel="search" type="application/opensearchdescription+xml" title="Pokémon Decklists" href="/opensearch.xml" />
  <meta name="google-adsense-account" content="{ADS}" />
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADS}"
     crossorigin="anonymous"></script>
  <meta property="og:locale" content="en_US" />
  <meta property="og:site_name" content="Pokémon Decklists" />
  <meta property="og:type" content="{e(og_type)}" />
  <meta property="og:title" content="{e(title)}" />
  <meta property="og:description" content="{e(desc)}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:image" content="{img}" />
  <meta property="og:image:alt" content="{e(image_alt)}" />
  <meta property="og:image:width" content="{img_w}" />
  <meta property="og:image:height" content="{img_h}" />
{dates}  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{e(title)}" />
  <meta name="twitter:description" content="{e(desc)}" />
  <meta name="twitter:image" content="{img}" />
  <meta name="twitter:image:alt" content="{e(image_alt)}" />
{ld_script(site_graph())}{crumb_ld(crumbs)}  {extra}
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
"""


def recent_item(lst: dict) -> str:
    types = list_types(lst)
    cls = color_class(types)
    img = ""
    mons = (lst.get("decklist") or {}).get("pokemon") or []
    if mons:
        img = mons[0].get("image") or ""
    who = clean(lst.get("title") or lst.get("archetype") or "List")
    meta = f"{clean(lst.get('event') or '')} · {clean(lst.get('notes') or '')}"
    return f"""            <li>
              <a class="recent-item {cls}" href="{href_list(lst)}">
                <img class="recent-leader" src="{e(img)}" alt="" width="40" height="56" loading="lazy" />
                <div class="recent-copy">
                  <div class="who">{e(who)}</div>
                  <div class="muted meta">{e(meta)}</div>
                </div>
                <div class="when">{e(lst.get('date'))}</div>
              </a>
            </li>"""


def type_pills(counter: Counter, fmt_id: str) -> str:
    bits = []
    total = sum(counter.values()) or 1
    for key, lab, hx in TYPES:
        n = counter.get(key, 0)
        if not n:
            continue
        pct = round(100 * n / total)
        bits.append(
            f'<a class="color-pill color-{key}" href="/formats/{fmt_id}.html#{key}"><span class="dot" style="background:{hx}"></span>{lab} · {n} lists · {pct}%</a>'
        )
    return "\n".join(bits) or '<p class="muted">No energy types parsed yet.</p>'


def combo_cards(pairs: Counter, fmt_id: str) -> str:
    bits = []
    for pair, n in pairs.most_common(8):
        labels = [TYPE_LABEL.get(t, t.title()) for t in pair]
        dots = "".join(f'<span class="dot" style="background:{TYPE_HEX.get(t, "#999")}"></span>' for t in pair)
        name = " / ".join(labels)
        bits.append(
            f"""          <a class="combo-card" href="/formats/{fmt_id}.html#recent">
            <div class="combo-dots">{dots}</div>
            <div>
              <div style="font-weight:800">{e(name)}</div>
              <div class="muted" style="font-size:13px">{n} recent lists</div>
            </div>
          </a>"""
        )
    return "\n".join(bits) or '<p class="muted">Combos appear once lists are tagged with energy.</p>'


def format_stats(fmt_id: str):
    rows = [x for x in LISTS if x["format"] == fmt_id]
    type_c = Counter()
    pair_c = Counter()
    arch = Counter()
    for lst in rows:
        types = list_types(lst)
        for t in types:
            type_c[t] += 1
        pair_c[combo_key(types)] += 1
        arch[clean(lst.get("archetype") or "Unknown")] += 1
    return rows, type_c, pair_c, arch


def write(path: str, content: str):
    p = ROOT / path.lstrip("/")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    print("write", path)


def page_index():
    recent = sorted(LISTS, key=lambda x: (x.get("date") or "", -int(x.get("placing") or 99)), reverse=True)[:56]
    teasers = collect_teaser_html()
    extra = ld_script(
        {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": "Pokémon TCG Decklists",
            "url": CANON + "/",
            "isPartOf": {"@id": CANON + "/#site"},
            "about": "Pokémon Trading Card Game",
            "mainEntity": {
                "@type": "ItemList",
                "name": "Pokémon TCG formats",
                "numberOfItems": len(FORMATS),
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": i,
                        "url": CANON + f"/formats/{f['id']}.html",
                        "name": f["name"],
                    }
                    for i, f in enumerate(FORMATS, 1)
                ],
            },
        }
    )
    cards = "\n".join(
        f"""            <a class="format-card" href="/formats/{f['id']}.html">
              <img src="{f['img']}" alt="{e(f['name'])} Pokémon TCG format" width="640" height="360" loading="lazy" />
              <div class="caption"><strong>{e(f['name'])}</strong><div class="muted">{e(f['kicker'])} · {e(f['size'])}</div></div>
            </a>"""
        for f in FORMATS
    )
    n_cards = len(price_records())
    n_art = len(ORIG_ART)
    fan = card_fan_html()
    rail = art_rail()
    tick = movers_ticker()
    wall = card_wall_html()
    return head(
        "Pokémon TCG Decklists | Standard, Pocket & GLC",
        "Tournament Pokémon TCG decklists by format — Standard, Pocket, Gym Leader Challenge, Expanded, and Unlimited. August–September 2026 lists, card prices, and shop.",
        "/",
        extra=extra,
        image_alt="Vintage-style fire dragon banner for Pokémon Decklists",
    ) + header() + f"""
    <main id="main" class="single home">
      <section class="home-splash">
        <img class="home-splash-bg" src="/img/pkdl-hero.jpg" alt="" width="1920" height="1080" fetchpriority="high" decoding="async">
{fan}
        <div class="home-splash-copy">
          <p class="splash-kicker">Fan journal · August–September 2026</p>
          <h1>Pokémon Decklists</h1>
          <p class="splash-lead">Tournament lists, a price desk, and original writing — Standard, Pocket, and Gym Leader Challenge first.</p>
          <div class="formats">
            <span>Standard</span>
            <span>Pocket</span>
            <span>Gym Leader Challenge</span>
          </div>
          <div class="splash-cta">
            <a class="btn-primary" href="#window">This window</a>
            <a class="btn-ghost-light" href="/market/">Price desk</a>
            <a class="btn-ghost-light" href="/desk.html">The Desk</a>
          </div>
        </div>
      </section>

      <ul class="home-stats" aria-label="Site snapshot">
        <li><strong>{len(LISTS):,}</strong><span>tournament lists</span></li>
        <li><strong>5</strong><span>formats</span></li>
        <li><strong>{n_cards}</strong><span>priced singles</span></li>
        <li><strong>{n_art}</strong><span>original paintings</span></li>
      </ul>

      <p class="trust-strip">
        <span>Public Limitless tables</span>
        <span>TCGPlayer market snapshots</span>
        <span>Fan site · not Nintendo / TPC</span>
        <span>Updated {NOW}</span>
      </p>

{digest_html()}

      <section class="home-essays" aria-label="From the Desk">
        <div class="section-title">
          <h3>From the Desk</h3>
          <a href="/guides/">All guides →</a>
        </div>
        <p class="muted">Original writing on top of the tables — how to read a list, how prices get here, what Worlds actually changed.</p>
{essay_grid_html()}
      </section>

{tick}

      <section class="home-gallery-band" aria-label="Original artwork">
        <div class="section-title">
          <h3>Original gallery</h3>
          <a href="/gallery.html">All paintings →</a>
        </div>
        <p class="muted">Fan paintings in a Pokémon-card style — original creatures, not licensed prints. Card photos below are real singles from the tracker.</p>
{rail}
        <div class="home-wide-art">
          <a href="/gallery.html"><img src="/img/art/art-sleeved-spread.jpg" alt="Sleeved cards spread across a hobby desk" width="1280" height="720" loading="lazy"></a>
          <a href="/market/"><img src="/img/art/art-market-desk.jpg" alt="A trading-card market desk" width="1280" height="720" loading="lazy"></a>
        </div>
      </section>

      <div class="home-thirds">
        <section class="home-third home-third-play" id="competitive">
          <div class="home-third-head">
            <p class="kicker">Compete</p>
            <h2>Decklists</h2>
            <p>{len(LISTS):,} August–September 2026 lists by format.</p>
          </div>
          <div class="home-third-body">
            <a class="half-link" href="#formats"><strong>Formats</strong><span>Types, color combos, recent lists</span></a>
            <a class="half-link" href="#recent"><strong>Recent lists</strong><span>Worlds and Limitless Play cups</span></a>
            <a class="half-link" href="/tier-list.html"><strong>Tier list</strong><span>Standard after Worlds 2026</span></a>
            <a class="half-link" href="/events.html"><strong>Events</strong><span>Official locator and championship dates</span></a>
          </div>
        </section>
        <section class="home-third home-third-market" id="market-home">
          <div class="home-third-head">
            <p class="kicker">Market</p>
            <h2>Price community</h2>
            <p>Watchlist, binder P&amp;L, alerts, and print compare — stored in this browser.</p>
          </div>
          <div class="home-third-body">
            <a class="half-link" href="/market/"><strong>Market hub</strong><span>Desk, staples, and tools</span></a>
            <a class="half-link" href="/market/watchlist.html"><strong>Watchlist</strong><span>Pin prints and check 7-day moves</span></a>
            <a class="half-link" href="/market/binder.html"><strong>Binder</strong><span>Qty, paid price, paper P&amp;L</span></a>
            <a class="half-link" href="/price-tracker.html"><strong>Full tracker</strong><span>Charts for {n_cards} singles</span></a>
            {teasers}
          </div>
        </section>
        <section class="home-third home-third-shop" id="collectibles-home">
          <div class="home-third-head">
            <p class="kicker">Shop</p>
            <h2>Buy &amp; partners</h2>
            <p>Live TCGplayer and Amazon links. More programs to apply next.</p>
          </div>
          <div class="home-third-body">
            <a class="half-link" href="/collectibles/"><strong>Collectibles</strong><span>Catalog, sets, card pages</span></a>
            <a class="half-link" href="/shop/"><strong>Amazon shop</strong><span>Sleeves, dice, mats, boxes</span></a>
            <a class="half-link" href="/partners.html"><strong>Partner programs</strong><span>Live IDs plus official sign-up pages</span></a>
            <a class="half-link" href="/gallery.html"><strong>Artwork</strong><span>{n_art} original paintings</span></a>
          </div>
        </section>
      </div>

      <section class="card home-panel" id="prints">
        <div class="section-title">
          <h3>Highest market prints</h3>
          <a href="/collectibles/cards/">Full catalog →</a>
        </div>
        <p class="muted">Real card photos from the August–September 2026 tracker. Open any print for history, Watch, Compare, and a TCGplayer affiliate buy.</p>
{wall}
      </section>

      <a class="events-banner" id="events" href="/events.html">
        <div>
          <div class="kicker">Official Play! Pokémon</div>
          <div class="title">Events and championship schedule</div>
          <div class="muted" style="color:rgba(255,255,255,0.82);margin-top:4px">Worlds 2026, Regionals, League Cups, and the event locator</div>
        </div>
        <div class="go">Official events →</div>
      </a>

      <form class="site-search home-search" method="get" action="/search.html" role="search">
        <label class="site-search-label" for="home-q">Search PKMN decklists</label>
        <div class="site-search-row">
          <input id="home-q" type="search" name="q" placeholder="Format, player, archetype, or event" aria-label="Search PKMN decklists" />
          <button type="submit">Search</button>
        </div>
      </form>

      <section class="home-leaders-flow" id="formats">
        <div class="home-leaders-intro">
          <p class="home-leaders-kicker">The circuit</p>
          <div class="home-leaders-intro-row">
            <div>
              <h3>Formats</h3>
              <p>Pick a format. Each page opens with types and popular color combos, then the recent lists. Names live in the <a href="/guides/">guides</a>.</p>
            </div>
            <a href="/formats/">All format pages →</a>
          </div>
        </div>
        <div class="card home-panel home-leaders-grid">
          <div class="format-cards" aria-label="Pokémon TCG formats">
{cards}
          </div>
        </div>
      </section>

      <section class="card home-panel" id="recent">
        <div class="section-title">
          <h3>Recent lists</h3>
          <div class="muted">{len(LISTS)} lists</div>
        </div>
        <p class="muted">Newest first from August and September 2026. Worlds 2026 plus Limitless Play cups in Standard, Pocket, GLC, Expanded, and vintage Unlimited.</p>
        <ul class="recent-list" aria-label="Recent decklists">
{chr(10).join(recent_item(x) for x in recent)}
        </ul>
      </section>

      <section class="home-partners card home-panel">
        <div class="section-title">
          <h3>Partners</h3>
          <a href="/partners.html">Programs &amp; apply links →</a>
        </div>
        <p class="muted">Already live: Google AdSense <code>ca-pub-1074015774205047</code>, TCGplayer Impact 7670706 / 1780961, and Amazon Associates on the shop. Discord stays a placeholder with no invite yet.</p>
        <div class="partner-strip">
          <span class="partner-pill live">AdSense live</span>
          <span class="partner-pill live">TCGplayer live</span>
          <span class="partner-pill live">Amazon live</span>
          <span class="partner-pill apply">Impact · eBay · Whatnot · TikTok Shop — apply next</span>
        </div>
      </section>
    </main>
""" + footer()


def list_index_items(rows: list[dict]) -> str:
    bits = []
    for lst in rows:
        types = list_types(lst)
        cls = color_class(types)
        bits.append(
            f"""            <li data-date="{e(lst.get('date'))}" data-placing="{lst.get('placing') or 99}">
              <a class="item {cls}" href="{href_list(lst)}">
                <div>
                  <div style="font-weight:700">{e(clean(lst.get('title')))}</div>
                  <div class="muted" style="font-size:13px">{e(lst.get('date'))} · {e(clean(lst.get('event')))} · {e(clean(lst.get('archetype')))}</div>
                </div>
                <div class="link">Open →</div>
              </a>
            </li>"""
        )
    return "\n".join(bits)


def page_formats_index():
    cards = "\n".join(
        f"""          <a class="format-card" href="/formats/{f['id']}.html">
            <img src="{f['img']}" alt="{e(f['name'])}" />
            <div class="caption"><strong>{e(f['name'])}</strong><div class="muted">{e(f['blurb'])}</div></div>
          </a>"""
        for f in FORMATS
    )
    return head("Pokémon TCG formats | Pokémon Decklists", "Standard, Expanded, Gym Leader Challenge, Pocket, and Unlimited.", "/formats/") + header("formats") + f"""
    <main id="main" class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Formats</div>
        <h1 class="page-title">Formats</h1>
        <p>Pokémon TCG is organized by format, not by a leader. Each page shows the types posting, the popular color combos, then the August–September 2026 lists.</p>
        <div class="format-cards">{cards}</div>
      </div>
    </main>
""" + footer()


def page_format(fmt: dict) -> str:
    rows, type_c, pair_c, arch = format_stats(fmt["id"])
    rows = sorted(rows, key=lambda x: x.get("date") or "", reverse=True)
    type_section = "\n".join(
        f'<div class="combo-card" id="{key}"><span class="dot" style="background:{hx}"></span><div><div style="font-weight:800">{lab}</div><div class="muted">{type_c.get(key,0)} lists using {lab} energy</div></div></div>'
        for key, lab, hx in TYPES if type_c.get(key)
    ) or '<p class="muted">Type breakdown fills in from posted energy.</p>'
    return head(
        f"{fmt['name']} Pokémon TCG Decklists (2026)",
        f"{fmt['blurb']} {len(rows)} recent {fmt['name']} lists from August and September 2026, grouped by type and color combo.",
        f"/formats/{fmt['id']}.html",
        fmt["img"],
        extra=ld_script(
            {
                "@context": "https://schema.org",
                "@type": "CollectionPage",
                "name": f"{fmt['name']} Pokémon TCG decklists",
                "url": CANON + f"/formats/{fmt['id']}.html",
                "about": fmt["name"],
                "numberOfItems": len(rows),
            }
        ),
        image_alt=f"{fmt['name']} Pokémon TCG format",
    ) + header("formats") + f"""
    <main id="main" class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/formats/">Formats</a> / {e(fmt['name'])}</div>
        <div class="leader-hero">
          <img src="{fmt['img']}" alt="{e(fmt['name'])} original artwork" />
          <div>
            <h1 class="page-title">{e(fmt['name'])}</h1>
            <p>{e(fmt['blurb'])}</p>
            <div class="stat-row">
              <span class="pill">{e(fmt['size'])}</span>
              <span class="pill">{len(rows)} lists</span>
              <span class="pill">{e(fmt['kicker'])}</span>
            </div>
            <p class="muted">{e(fmt['legal'])} Official: <a href="{fmt['official']}" target="_blank" rel="noopener">rules / info</a>.</p>
          </div>
        </div>

        <section style="margin-top:22px">
          <div class="section-title"><h3>Types in this format</h3><div class="muted">From posted lists</div></div>
          <p class="muted">Same idea as OPDB color tiles — Pokémon types instead of leader colors.</p>
          <div class="color-pills">{type_pills(type_c, fmt['id'])}</div>
          <div class="combo-grid" style="margin-top:14px">{type_section}</div>
        </section>

        <section style="margin-top:22px">
          <div class="section-title"><h3>Most popular color combos</h3><div class="muted">Energy pairs</div></div>
          <div class="combo-grid">
{combo_cards(pair_c, fmt['id'])}
          </div>
        </section>

        <section class="deck-index" id="recent" style="margin-top:22px">
          <div class="section-title"><h3>Recent lists</h3><div class="muted">{len(rows)} lists</div></div>
          <div class="list-filters" data-hub-filters>
            <input data-filter="q" placeholder="Player, archetype, event" aria-label="Filter lists" />
            <select data-filter="when">
              <option value="">Any date</option>
              <option value="sep">September 2026</option>
              <option value="aug">August 2026</option>
            </select>
            <select data-filter="place">
              <option value="">Any finish</option>
              <option value="win">Winners</option>
              <option value="top8">Top 8</option>
            </select>
          </div>
          <ul class="list">
{list_index_items(rows)}
          </ul>
        </section>
      </div>
    </main>
""" + footer()


def curve_html(lst: dict) -> str:
    dl = lst.get("decklist") or {}
    mons = dl.get("pokemon") or []
    # fake a count bar by card counts in pokemon/trainer
    total = sum(int(c.get("count") or 0) for c in mons + (dl.get("trainer") or []) + (dl.get("energy") or []))
    return f'<div class="muted">Main deck {total} cards · {len(mons)} Pokémon lines</div>'


def cards_block(title: str, cards: list, pocket: bool):
    if not cards:
        return "", ""
    lines = []
    pics = []
    for c in cards:
        name = clean(c.get("name") or "")
        setc = c.get("set") or ""
        num = str(c.get("number") or "")
        cid = f"{setc}-{num}" if setc and num else ""
        qty = int(c.get("count") or 0) or 1
        img = c.get("image") or ""
        buy = tcg_search(name, setc, num)
        lines.append(
            f"""            <li class="text-line" tabindex="0">
              <span class="qty">{qty}x</span>
              <span class="card-title">{e(name)}</span>
              <span class="muted card-id">{e(cid)}</span>
              <img class="card-pop" src="{e(img)}" alt="{e(name)}" />
            </li>"""
        )
        pics.append(
            f"""        <article class="card-entry">
          <img src="{e(img)}" alt="{e(name)}" loading="lazy" />
          <div>
            <div class="id"><span class="qty">{qty}x</span>{e(cid)} · {e(title[:-1] if title.endswith('s') else title)}</div>
            <h4>{e(name)}</h4>
            <a class="buy-tcg-inline" href="{buy}" target="_blank" rel="noopener nofollow sponsored">Buy on TCGplayer</a>
          </div>
        </article>"""
        )
    return f"""
        <div>
          <h4>{e(title)}</h4>
          <ul class="text-lines">
{chr(10).join(lines)}
          </ul>
        </div>""", "\n".join(pics)


def page_list(lst: dict) -> str:
    types = list_types(lst)
    cls = color_class(types)
    dl = lst.get("decklist") or {}
    pocket = lst["format"] == "pocket"
    p_txt, p_pic = cards_block("Pokémon", dl.get("pokemon") or [], pocket)
    t_txt, t_pic = cards_block("Trainers", dl.get("trainer") or [], pocket)
    e_txt, e_pic = cards_block("Energy", dl.get("energy") or [], pocket)
    fmt = FMT[lst["format"]]
    first = (dl.get("pokemon") or [{}])[0]
    img = first.get("image") or fmt["img"]
    arch = clean(lst.get("archetype") or "")
    buy_list = aff("https://www.tcgplayer.com/search/pokemon/product?q=" + quote(arch or "pokemon") + "&productLineName=pokemon")
    list_ld = ld_script(
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": clean(lst.get("title") or arch),
            "datePublished": lst.get("date") or NOW,
            "inLanguage": "en-US",
            "about": arch or fmt["name"],
            "articleSection": fmt["name"],
            "author": {"@type": "Person", "name": clean(lst.get("player") or lst.get("title") or "Player")},
            "publisher": {"@id": CANON + "/#org"},
            "mainEntityOfPage": CANON + href_list(lst),
            "image": img if str(img).startswith("http") else CANON + str(img),
            "description": f"{fmt['name']} Pokémon TCG decklist from {clean(lst.get('event') or 'tournament')} on {lst.get('date') or NOW}.",
        }
    )
    return head(
        f"{clean(lst.get('title'))} | {fmt['name']} Decklist",
        f"{fmt['name']} Pokémon TCG decklist: {clean(lst.get('title'))}. {clean(lst.get('event'))} · {lst.get('date')}. Full 60-card list with pictures.",
        href_list(lst),
        img,
        extra=list_ld,
        og_type="article",
        image_alt=arch or clean(lst.get("title") or "Pokémon TCG decklist"),
        published=lst.get("date") or NOW,
    ).replace("<body>", f'<body class="{cls}">') + header() + f"""
    <main id="main" class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/formats/">Formats</a> / <a href="/formats/{lst['format']}.html">{e(fmt['name'])}</a> / Decklist</div>
        <h1 class="page-title">{e(clean(lst.get('title')))}</h1>
        <p>{e(clean(lst.get('event')))} · {e(lst.get('date'))} · {e(lst.get('country') or '')} · {e(clean(lst.get('notes') or ''))}</p>
        <p class="muted">Source: <a href="{e(lst.get('source_url'))}" target="_blank" rel="noopener">{e(lst.get('source_url'))}</a>. Card pictures hosted by Limitless. Fair use of publicly posted tournament lists. Not affiliated with Nintendo or The Pokémon Company.</p>
        {curve_html(lst)}
        <p class="color-pills">{''.join(f'<span class="color-pill color-{t}"><span class="dot" style="background:{TYPE_HEX[t]}"></span>{TYPE_LABEL[t]}</span>' for t in types)}</p>
        <section class="text-deck">
          <div class="section-title">
            <h3>Text list</h3>
            <a class="buy-tcg" data-buy-list="{buy_list}" href="{buy_list}" target="_blank" rel="noopener nofollow sponsored">Buy this list on TCGplayer</a>
          </div>
          <div class="text-deck-cols">
            {p_txt}{t_txt}{e_txt}
          </div>
        </section>
        <div class="picture-summary">
          <div class="section-title"><h3>Card pictures</h3><div class="muted">Hover the text list for pops</div></div>
          {p_pic}
          {t_pic}
          {e_pic}
        </div>
        <p class="amazon-disclosure-line">As an Amazon Associate I earn from qualifying purchases. TCGplayer links are affiliate links.</p>
      </div>
    </main>
""" + footer()


def page_tier():
    worlds = [x for x in LISTS if x.get("event") == "World Championships 2026"]
    arch = Counter(clean(x.get("archetype") or "") for x in worlds)
    sept = [x for x in LISTS if x["format"] == "standard" and (x.get("date") or "") >= "2026-09-01"]
    sept_arch = Counter(clean(x.get("archetype") or "") for x in sept)
    # merge
    scores = Counter()
    for k, v in arch.items():
        scores[k] += v * 3
    for k, v in sept_arch.items():
        scores[k] += v
    ranked = [a for a, _ in scores.most_common() if a]
    tiers = {"S": ranked[:3], "A": ranked[3:7], "B": ranked[7:12], "C": ranked[12:16], "D": ranked[16:20]}
    def tile(name):
        sample = next((x for x in worlds + sept if clean(x.get("archetype")) == name), None)
        img = ""
        href = "/formats/standard.html"
        if sample:
            mons = (sample.get("decklist") or {}).get("pokemon") or []
            img = mons[0].get("image") if mons else ""
            href = href_list(sample)
        types = list_types(sample) if sample else []
        cls = color_class(types)
        meta = f"{arch.get(name,0)} Worlds · {sept_arch.get(name,0)} Sept"
        return f"""            <a class="tier-leader {cls}" href="{href}">
              <img src="{e(img)}" alt="" width="86" height="120" loading="lazy" />
              <div class="name">{e(name)}</div>
              <div class="meta">{e(meta)}</div>
            </a>"""
    rows_html = []
    for letter, names in tiers.items():
        if not names:
            continue
        rows_html.append(
            f"""        <div class="tier-row tier-{letter.lower()}">
          <div class="tier-label">{letter}</div>
          <div class="tier-leaders">
{chr(10).join(tile(n) for n in names)}
          </div>
        </div>"""
        )
    return head(
        "Standard Pokémon TCG tier list after Worlds 2026",
        "Standard tier list after the 2026 World Championships in San Francisco, cross-checked with September Limitless Play cups.",
        "/tier-list.html",
    ) + header("tier") + f"""
    <main id="main" class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Tier List</div>
        <h1 class="page-title">Standard tier list</h1>
        <p>Built from the 2026 World Championships Masters table (797 players, 28–30 Aug, San Francisco) plus September Limitless Play Standard cups. Pictures are from public lists, not a greatest-hits poster of popular cards.</p>
        <p class="muted">Updated {NOW}. Click a tile for a real list.</p>
        <div class="tier-board">
{chr(10).join(rows_html)}
        </div>
        <section class="faq" id="faq">
          <div class="section-title"><h3>Tier list FAQ</h3></div>
          <details open>
            <summary>How is this Pokémon TCG tier list built?</summary>
            <p>Worlds 2026 top 24 counts three times. September Play cups count once. That keeps the San Francisco table in front without ignoring the weeks after.</p>
          </details>
          <details>
            <summary>What format is the tier list?</summary>
            <p>2026 Standard: regulation marks H, I, and J. Mega Evolution–era cards are in the pool.</p>
          </details>
        </section>
      </div>
    </main>
""" + footer()


def hist_series(hist: list) -> list[float]:
    vals = []
    for pt in hist or []:
        if isinstance(pt, (list, tuple)) and len(pt) >= 2:
            vals.append(float(pt[1]) / 100.0)
        elif isinstance(pt, dict) and "market" in pt:
            vals.append(float(pt["market"]))
    return vals


def change_since(hist: list, days: int, spot: float | None) -> float | None:
    series_pts = []
    for pt in hist or []:
        if isinstance(pt, (list, tuple)) and len(pt) >= 2:
            series_pts.append((int(pt[0]), float(pt[1]) / 100.0))
    if not series_pts:
        return None
    last_ts, last = series_pts[-1]
    target = last_ts - days * 86400000
    prev = series_pts[0][1]
    for ts, v in series_pts:
        if ts >= target:
            prev = v
            break
        prev = v
    if not prev:
        return None
    now = spot if spot else last
    if prev < 0.75:
        return None
    pct = (now - prev) / prev * 100.0
    if abs(pct) > 250:
        return None
    return pct


def card_file(setc, num) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", f"{setc}-{num}").strip("-")
    return safe or "card"


def card_href(setc, num) -> str:
    return f"/collectibles/cards/{card_file(setc, num)}.html"


EX_IMG = {
    "RG": "ex6",
    "TRR": "ex7",
    "DS": "ex11",
    "LM": "ex12",
    "HP": "ex13",
    "CG": "ex14",
    "DF": "ex15",
    "PK": "ex16",
}


def fix_card_image(image, setc, num) -> str:
    setc, num = str(setc or ""), str(num or "")
    if setc in EX_IMG and num.isdigit():
        return f"https://images.pokemontcg.io/{EX_IMG[setc]}/{num}_hires.png"
    img = image or ""
    if num.isdigit() and len(num) < 3:
        pad = num.zfill(3)
        img = img.replace(f"_{num}_R_EN", f"_{pad}_R_EN").replace(f"_{num}_EN.", f"_{pad}_EN.")
    if not img and setc and num.isdigit():
        img = f"https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/tpci/{setc}/{setc}_{num.zfill(3)}_R_EN.png"
    return img


def spark_svg(values, w=640, h=160) -> str:
    if not values or len(values) < 2:
        return '<p class="muted">No public history yet.</p>'
    mn, mx = min(values), max(values)
    if mx == mn:
        mx = mn + 1
    pts = []
    for i, v in enumerate(values):
        x = (i / (len(values) - 1)) * (w - 4) + 2
        y = h - 3 - ((v - mn) / (mx - mn)) * (h - 8)
        pts.append(f"{x:.1f},{y:.1f}")
    color = "#2e7d32" if values[-1] >= values[0] else "#c62828"
    return (
        f'<svg class="spark spark-lg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" aria-hidden="true">'
        f'<polyline fill="none" stroke="{color}" stroke-width="2.4" points="{" ".join(pts)}"/></svg>'
    )


_PRICE_ROWS: list[dict] | None = None


def price_records() -> list[dict]:
    global _PRICE_ROWS
    if _PRICE_ROWS is not None:
        return _PRICE_ROWS
    rows = []
    for key, card in PRICES.items():
        series = hist_series(card.get("history") or [])
        spot = card.get("spot")
        if spot is None and series:
            spot = series[-1]
        pid = card.get("tcgplayer_id")
        buy = aff(f"https://www.tcgplayer.com/product/{pid}") if pid else tcg_search(card["name"], card["set"], card["number"])
        rows.append({
            "key": key,
            "name": card["name"],
            "set": card["set"],
            "number": str(card["number"]),
            "image": fix_card_image(card.get("image") or "", card["set"], card["number"]),
            "spot": spot,
            "change7": change_since(card.get("history") or [], 7, spot),
            "change30": change_since(card.get("history") or [], 30, spot),
            "series": series[-90:] if series else [],
            "buy": buy,
            "count": card.get("count") or 0,
            "artist": card.get("artist") or "",
            "ptype": card.get("ptype") or "",
            "hp": card.get("hp"),
            "kind": card.get("kind") or "",
            "stage": card.get("stage") or "",
            "regulation": card.get("regulation") or "",
            "text": card.get("text") or "",
            "href": card_href(card["set"], card["number"]),
            "url": card.get("url") or "",
        })
    rows.sort(key=lambda r: -(r["spot"] or 0))
    _PRICE_ROWS = rows
    return rows


ORIG_ART = [
    ("/img/art/art-fire-dragon.jpg", "Original fire-dragon painting", "wide"),
    ("/img/art/art-water-serpent.jpg", "Original water-serpent painting", "portrait"),
    ("/img/art/art-forest-guardian.jpg", "Original forest-guardian painting", "portrait"),
    ("/img/art/art-storm-beast.jpg", "Original storm-beast painting", "portrait"),
    ("/img/art/art-crystal-fox.jpg", "Original crystal-fox painting", "portrait"),
    ("/img/art/art-steel-beetle.jpg", "Original steel-beetle painting", "portrait"),
    ("/img/art/art-stone-ram.jpg", "Original stone-ram painting", "portrait"),
    ("/img/art/art-mist-panther.jpg", "Original mist-panther painting", "portrait"),
    ("/img/art/art-glow-moth.jpg", "Original glow-moth painting", "portrait"),
    ("/img/art/art-spark-sparrow.jpg", "Original lightning-sparrow painting", "portrait"),
    ("/img/art/art-night-wolf.jpg", "Original night-wolf painting", "portrait"),
    ("/img/art/art-blossom-sprite.jpg", "Original blossom-sprite painting", "portrait"),
    ("/img/art/art-summit-bear.jpg", "Original summit-bear painting", "portrait"),
    ("/img/art/art-star-owl.jpg", "Original star-owl painting", "portrait"),
    ("/img/art/art-ice-crane.jpg", "Original ice-crane painting", "portrait"),
    ("/img/art/art-venom-bloom.jpg", "Original venom-bloom painting", "portrait"),
    ("/img/art/art-sky-wyvern.jpg", "Original sky-wyvern painting", "portrait"),
    ("/img/art/art-market-desk.jpg", "Original painting of a trading-card market desk", "wide"),
    ("/img/art/art-binder.jpg", "Original painting of a collector’s binder", "wide"),
    ("/img/art/art-gallery.jpg", "Original painting of a card-art gallery", "wide"),
    ("/img/art/art-sleeved-spread.jpg", "Original painting of sleeved cards on a desk", "wide"),
    ("/img/art/art-shop-wall.jpg", "Original painting of a card-shop gallery wall", "wide"),
]


def art_rail(n: int = 12) -> str:
    portraits = [a for a in ORIG_ART if a[2] == "portrait"][:n]
    tiles = []
    for src, alt, _ in portraits:
        tiles.append(
            f'<a href="/gallery.html"><img src="{e(src)}" alt="{e(alt)}" width="245" height="342" loading="lazy" decoding="async"></a>'
        )
    return f'<div class="art-rail" aria-label="Original Pokémon-style artwork">{"".join(tiles)}</div>'


def card_fan_html(n: int = 7) -> str:
    recs = price_records()[:n]
    tiles = []
    for r in recs:
        tiles.append(
            f'<a class="fan-card" href="{e(r["href"])}">'
            f'<img src="{e(r["image"])}" alt="{e(r["name"])} {e(r["set"])} {e(r["number"])}" width="92" height="128"></a>'
        )
    return f'<div class="hero-fan" aria-hidden="true">{"".join(tiles)}</div>'


def movers_ticker() -> str:
    recs = [r for r in sorted(price_records(), key=lambda r: abs(r["change7"] or 0), reverse=True) if r["change7"] is not None][:16]
    if not recs:
        return ""
    chips = []
    for r in recs:
        sign = "+" if (r["change7"] or 0) >= 0 else ""
        chips.append(
            f'<a href="{e(r["href"])}"><img src="{e(r["image"])}" alt="">'
            f'<strong>{e(r["name"])}</strong>'
            f'<span>${(r["spot"] or 0):.2f} {sign}{r["change7"]:.1f}%</span></a>'
        )
    inner = "".join(chips)
    return (
        '<div class="ticker" aria-label="Seven-day price movers">'
        f'<div class="ticker-track">{inner}</div></div>'
    )


def card_wall_html(n: int = 24) -> str:
    tiles = []
    for r in price_records()[:n]:
        tiles.append(
            f'<a class="wall-card" href="{e(r["href"])}">'
            f'<img src="{e(r["image"])}" alt="{e(r["name"])} — {e(r["set"])} {e(r["number"])}" width="245" height="342" loading="lazy">'
            f'<span class="cap">{e(r["name"])}<br>${(r["spot"] or 0):.2f}</span></a>'
        )
    return f'<div class="card-wall">{"".join(tiles)}</div>'


def market_payload(row: dict) -> str:
    return (
        f'data-href="{e(row["href"])}" data-name="{e(row["name"])}" '
        f'data-image="{e(row.get("image") or "")}" data-set="{e(row.get("set") or "")}" '
        f'data-number="{e(row.get("number") or "")}" data-spot="{row.get("spot") or 0}" '
        f'data-buy="{e(row.get("buy") or "")}"'
    )


def market_actions(row: dict) -> str:
    p = market_payload(row)
    cmp_href = f'/market/compare.html?a={quote(row["href"], safe="")}'
    return (
        f'<div class="market-actions" {p}>'
        f'<button type="button" class="home-ghost" data-watch>Watch</button>'
        f'<button type="button" class="home-ghost" data-binder-add>Add to binder</button>'
        f'<a class="home-ghost" href="{e(cmp_href)}">Compare</a>'
        f'<a class="home-ghost" href="/market/alerts.html">Alert</a>'
        f"</div>"
    )


def market_data_script() -> str:
    slim = [
        {k: r[k] for k in ("key", "name", "set", "number", "image", "spot", "change7", "buy", "href")}
        for r in price_records()
    ]
    return f'<script type="application/json" id="market-data">{json.dumps(slim, ensure_ascii=False)}</script>'


def market_subnav(current: str = "") -> str:
    links = [
        ("/market/", "Hub", "hub"),
        ("/market/watchlist.html", "Watchlist", "watch"),
        ("/market/binder.html", "Binder", "binder"),
        ("/market/compare.html", "Compare", "compare"),
        ("/market/alerts.html", "Alerts", "alerts"),
        ("/market/staples.html", "Staples", "staples"),
        ("/price-tracker.html", "Full tracker", "tracker"),
        ("/collectibles/movers.html", "Movers", "movers"),
    ]
    bits = []
    for href, label, key in links:
        cur = ' aria-current="page"' if current == key else ""
        bits.append(f'<a class="home-ghost" href="{href}"{cur}>{label}</a>')
    return f'<nav class="market-subnav" aria-label="Market tools">{"".join(bits)}</nav>'


def staple_rows() -> list[tuple[str, int, dict | None, str]]:
    counts: Counter = Counter()
    images: dict[str, str] = {}
    for lst in LISTS:
        for c in (lst.get("decklist") or {}).get("pokemon") or []:
            name = c.get("name") or ""
            if not name:
                continue
            counts[name] += int(c.get("count") or 0)
            if name not in images:
                images[name] = c.get("image") or ""
    priced = {}
    for r in price_records():
        priced.setdefault(r["name"], r)
    out = []
    for name, qty in counts.most_common(48):
        out.append((name, qty, priced.get(name), images.get(name, "")))
    return out


def format_census() -> Counter:
    return Counter(x["format"] for x in LISTS)


def top_archetypes(fmt: str, n: int = 6) -> list[tuple[str, int]]:
    return Counter(clean(x.get("archetype") or "Unknown") for x in LISTS if x["format"] == fmt).most_common(n)


def essay_grid_html() -> str:
    bits = []
    for href, kicker, title, dek, img in ESSAYS:
        bits.append(
            f'<a class="essay-card" href="{e(href)}">'
            f'<img src="{e(img)}" alt="" width="640" height="360" loading="lazy">'
            f'<div class="essay-copy"><p class="kicker">{e(kicker)}</p>'
            f"<h3>{e(title)}</h3><p>{e(dek)}</p></div></a>"
        )
    return f'<div class="essay-grid">{"".join(bits)}</div>'


def market_brief_html() -> str:
    movers = [
        r
        for r in sorted(price_records(), key=lambda r: abs(r["change7"] or 0), reverse=True)
        if r["change7"] is not None
    ]
    staples = staple_rows()[:3]
    bits = []
    if movers:
        m = movers[0]
        bits.append(
            f'Biggest 7-day swing in the tracker: <a href="{e(m["href"])}">{e(m["name"])}</a> '
            f'{(m["change7"] or 0):+.1f}% at ${(m["spot"] or 0):.2f}.'
        )
    if staples:
        name, qty, match, _ = staples[0]
        bits.append(f"Most-copied Pokémon line in this window: {e(name)} ({qty} copies).")
    if not bits:
        return ""
    return "<p class=\"market-brief\">" + " ".join(bits) + "</p>"


def digest_html() -> str:
    counts = format_census()
    std = top_archetypes("standard", 5)
    worlds_n = sum(1 for x in LISTS if "World Championship" in (x.get("event") or ""))
    census = []
    for f in FORMATS:
        n = counts.get(f["id"], 0)
        census.append(
            f'<a href="/formats/{f["id"]}.html"><span>{e(f["name"])}</span><strong>{n}</strong></a>'
        )
    arch = "".join(f"<li><span>{e(name)}</span><strong>{n}</strong></li>" for name, n in std)
    return f"""
      <section class="digest" id="window">
        <div>
          <p class="kicker">This window · 1 Aug – 9 Sep 2026</p>
          <h2 class="desk-title">The room after Worlds</h2>
          <p>A fan table of <strong>{len(LISTS):,}</strong> public lists. Standard is {counts.get("standard", 0)} of them. Pocket is {counts.get("pocket", 0)} — a Mega Evolution cup, not paper with fewer cards. GLC {counts.get("glc", 0)}, Unlimited {counts.get("unlimited", 0)}, Expanded {counts.get("expanded", 0)}. Worlds 2026 accounts for {worlds_n} rows. Andrew Hedrick won Masters on Dragapult; the weeks of online cups after San Francisco are here too.</p>
          {market_brief_html()}
          <p class="digest-cta"><a class="home-ghost" href="/desk.html">Open the Desk report</a> <a class="home-ghost" href="/methodology.html">How we source this</a></p>
        </div>
        <div class="digest-side">
          <p class="kicker">Lists by format</p>
          <div class="census">{"".join(census)}</div>
          <p class="kicker" style="margin-top:16px">Standard names</p>
          <ul class="arch-lead">{arch}</ul>
        </div>
      </section>
"""


def decks_with_card(setc, num, limit=8) -> list[dict]:
    out = []
    setc, num = str(setc), str(num)
    for lst in LISTS:
        dl = lst.get("decklist") or {}
        hit = False
        for bucket in ("pokemon", "trainer", "energy"):
            for c in dl.get(bucket) or []:
                if str(c.get("set") or "") == setc and str(c.get("number") or "") == num:
                    hit = True
                    break
            if hit:
                break
        if hit:
            out.append(lst)
        if len(out) >= limit:
            break
    return out


def collect_teaser_html() -> str:
    rows = price_records()
    if not rows:
        return ""
    movers = sorted(rows, key=lambda r: abs(r["change7"] or 0), reverse=True)[:4]
    bits = ['<div class="collect-teasers">']
    for m in movers:
        ch = m["change7"]
        cls = "up" if (ch or 0) >= 0 else "down"
        label = "—" if ch is None else f"{ch:+.1f}%"
        bits.append(
            f'<a class="collect-teaser" href="{m["href"]}"><img src="{e(m["image"])}" alt="{e(m["name"])}" width="36" height="50" loading="lazy">'
            f'<span><strong>{e(m["name"])}</strong><span class="{cls}">{label} 7d</span></span></a>'
        )
    bits.append("</div>")
    return "\n".join(bits)


def page_collectibles_hub():
    rows = price_records()
    movers = sorted(rows, key=lambda r: abs(r["change7"] or 0), reverse=True)[:8]
    costly = sorted(rows, key=lambda r: -(r["spot"] or 0))[:8]
    sets = Counter(r["set"] for r in rows)
    mover_html = "\n".join(
        f'<li><a class="item" href="{m["href"]}"><div><div style="font-weight:700">{e(m["name"])}</div>'
        f'<div class="muted">{e(m["set"])} {e(m["number"])}' + (f' · {e(m["artist"])}' if m["artist"] else "") +
        f'</div></div><div class="{"up" if (m["change7"] or 0)>=0 else "down"}">'
        + ("—" if m["change7"] is None else f"{m['change7']:+.1f}%")
        + "</div></a></li>"
        for m in movers
    )
    cost_html = "\n".join(
        f'<a class="collect-card" href="{c["href"]}"><img src="{e(c["image"])}" alt="{e(c["name"])}" width="245" height="342" loading="lazy">'
        f'<div class="collect-card-copy"><strong>{e(c["name"])}</strong>'
        f'<div class="muted">{e(c["set"])} · {e(c["number"])}</div>'
        f'<div class="collect-price">${(c["spot"] or 0):.2f}</div></div></a>'
        for c in costly
    )
    set_html = "\n".join(
        f'<a class="item" href="/collectibles/sets/{e(s)}.html"><div style="font-weight:700">{e(s)}</div>'
        f'<div class="link">{n} cards →</div></a>'
        for s, n in sets.most_common(12)
    )
    return head(
        "Collectibles, prices, and card info | Pokémon Decklists",
        "Pokémon TCG collectibles: price history, trends, set pages, and card info with TCGPlayer affiliate buy links.",
        "/collectibles/",
    ) + header("collect") + f"""
    <main id="main" class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Collectibles</div>
        <h1 class="page-title">Collectibles</h1>
        <p>The other half of the site. Singles that posted in August–September 2026 lists, with public TCGPlayer market history via Limitless, card facts, and affiliate buy links.</p>
        <div class="collect-jump">
          <a class="home-ghost" href="/market/">Market hub</a>
          <a class="home-ghost" href="/price-tracker.html">Price tracker</a>
          <a class="home-ghost" href="/collectibles/cards/">Card catalog</a>
          <a class="home-ghost" href="/collectibles/sets/">Sets</a>
          <a class="home-ghost" href="/collectibles/movers.html">Movers</a>
          <a class="home-ghost" href="/gallery.html">Artwork</a>
        </div>
        <section style="margin-top:22px">
          <div class="section-title"><h3>Highest market</h3><div class="muted">{len(rows)} tracked singles</div></div>
          <div class="collect-grid">{cost_html}</div>
        </section>
        <section style="margin-top:22px">
          <div class="section-title"><h3>Biggest 7-day moves</h3><a href="/collectibles/movers.html">All movers →</a></div>
          <ul class="list">{mover_html}</ul>
        </section>
        <section style="margin-top:22px">
          <div class="section-title"><h3>Sets</h3><a href="/collectibles/sets/">All sets →</a></div>
          <ul class="list">{set_html}</ul>
        </section>
        <p class="amazon-disclosure-line">TCGplayer links use partner ID 7670706 / 1780961. As an Amazon Associate I earn from qualifying purchases on shop pages.</p>
      </div>
    </main>
""" + footer()


def page_catalog():
    rows = price_records()
    sets = sorted({r["set"] for r in rows})
    opts = "\n".join(f'<option value="{e(s)}">{e(s)}</option>' for s in sets)
    payload = json.dumps(
        [{k: r[k] for k in ("name", "set", "number", "image", "spot", "change7", "href", "artist", "kind")} for r in rows],
        ensure_ascii=False,
    )
    return head(
        "Pokémon card catalog | Collectibles",
        "Browse Pokémon TCG singles with market prices, 7-day trends, and TCGPlayer affiliate links.",
        "/collectibles/cards/",
        extra='<script src="/js/collectibles.js" defer></script>',
    ) + header("collect") + f"""
    <main id="main" class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/collectibles/">Collectibles</a> / Cards</div>
        <h1 class="page-title">Card catalog</h1>
        <p>Filter the tracked singles. Open a card for history, artist, type line, and the lists it posted in.</p>
        <form class="site-search" role="search" onsubmit="return false">
          <label class="site-search-label" for="collect-q">Filter collectibles</label>
          <div class="site-search-row">
            <input id="collect-q" type="search" placeholder="Iono, MEG, 5ban, Dragapult…" />
            <select id="collect-set" aria-label="Set">
              <option value="">All sets</option>
              {opts}
            </select>
          </div>
        </form>
        <p id="collect-status" class="muted">{len(rows)} cards</p>
        <div id="collect-grid" class="collect-grid"></div>
        <script type="application/json" id="collect-data">{payload}</script>
        <p class="amazon-disclosure-line">Every card page includes a TCGPlayer affiliate buy link (partner 7670706 / 1780961).</p>
      </div>
    </main>
""" + footer()


def page_movers():
    rows = price_records()
    up = [r for r in rows if (r["change7"] or 0) > 0]
    down = [r for r in rows if (r["change7"] or 0) < 0]
    up.sort(key=lambda r: -(r["change7"] or 0))
    down.sort(key=lambda r: (r["change7"] or 0))
    def block(title, items):
        lis = "\n".join(
            f'<li><a class="item" href="{m["href"]}"><div><div style="font-weight:700">{e(m["name"])}</div>'
            f'<div class="muted">{e(m["set"])} {e(m["number"])} · ${(m["spot"] or 0):.2f}</div></div>'
            f'<div class="{"up" if (m["change7"] or 0)>=0 else "down"}">{m["change7"]:+.1f}%</div></a></li>'
            for m in items[:16]
        )
        return f'<section style="margin-top:22px"><div class="section-title"><h3>{title}</h3></div><ul class="list">{lis}</ul></section>'
    return head(
        "Card price movers | Collectibles",
        "Biggest 7-day Pokémon TCG price moves from public TCGPlayer snapshots.",
        "/collectibles/movers.html",
    ) + header("collect") + f"""
    <main id="main" class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/collectibles/">Collectibles</a> / Movers</div>
        <h1 class="page-title">Price movers</h1>
        <p>7-day percent change on tracked singles. Tiny spots under a nickel are skipped so a $0.02 print does not look like a 4,000% spike.</p>
        {block("On the way up", up)}
        {block("On the way down", down)}
      </div>
    </main>
""" + footer()


def page_sets_index():
    rows = price_records()
    grouped = defaultdict(list)
    for r in rows:
        grouped[r["set"]].append(r)
    items = []
    for s, cards in sorted(grouped.items(), key=lambda kv: -len(kv[1])):
        top = max((c.get("spot") or 0) for c in cards)
        items.append(
            f'<li><a class="item" href="/collectibles/sets/{e(s)}.html"><div>'
            f'<div style="font-weight:700">{e(s)}</div>'
            f'<div class="muted">{len(cards)} tracked singles · top ${top:.2f}</div></div>'
            f'<div class="link">Open →</div></a></li>'
        )
    return head(
        "Pokémon TCG sets | Collectibles",
        "Pokémon TCG set pages with market prices and affiliate buy links.",
        "/collectibles/sets/",
    ) + header("collect") + f"""
    <main id="main" class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/collectibles/">Collectibles</a> / Sets</div>
        <h1 class="page-title">Sets</h1>
        <p>Set codes from the August–September 2026 lists. Open a set for the singles we track.</p>
        <ul class="list">{"".join(items)}</ul>
      </div>
    </main>
""" + footer()


def page_set(setc: str, cards: list[dict]) -> str:
    grid = "\n".join(
        f'<a class="collect-card" href="{c["href"]}"><img src="{e(c["image"])}" alt="{e(c["name"])}" width="245" height="342" loading="lazy">'
        f'<div class="collect-card-copy"><strong>{e(c["name"])}</strong>'
        f'<div class="muted">#{e(c["number"])}' + (f' · {e(c["artist"])}' if c.get("artist") else "") +
        f'</div><div class="collect-price">${(c["spot"] or 0):.2f}</div></div></a>'
        for c in sorted(cards, key=lambda x: -(x["spot"] or 0))
    )
    return head(
        f"{setc} prices and card info | Collectibles",
        f"Pokémon TCG {setc} singles with market prices and TCGPlayer affiliate links.",
        f"/collectibles/sets/{setc}.html",
    ) + header("collect") + f"""
    <main id="main" class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/collectibles/">Collectibles</a> / <a href="/collectibles/sets/">Sets</a> / {e(setc)}</div>
        <h1 class="page-title">{e(setc)}</h1>
        <p>{len(cards)} tracked singles from this set that posted in recent lists.</p>
        <div class="collect-grid">{grid}</div>
      </div>
    </main>
""" + footer()


def page_card(row: dict) -> str:
    lists = decks_with_card(row["set"], row["number"], 10)
    used = "\n".join(
        f'<li><a class="item" href="{href_list(lst)}"><div style="font-weight:700">{e(clean(lst.get("title")))}</div>'
        f'<div class="muted">{e(lst.get("date"))} · {e(clean(lst.get("event")))}</div></a></li>'
        for lst in lists
    ) or '<p class="muted">No posted lists tagged this print yet.</p>'
    facts = []
    if row.get("kind"):
        facts.append(row["kind"])
    if row.get("stage"):
        facts.append(row["stage"])
    if row.get("ptype"):
        facts.append(row["ptype"])
    if row.get("hp"):
        facts.append(f'{row["hp"]} HP')
    if row.get("regulation"):
        facts.append(f'{row["regulation"]} mark')
    meta_line = " · ".join(facts)
    artist = f'<p class="muted">Illustrated by {e(row["artist"])}.</p>' if row.get("artist") else ""
    ch7 = "—" if row["change7"] is None else f'{row["change7"]:+.1f}%'
    ch30 = "—" if row["change30"] is None else f'{row["change30"]:+.1f}%'
    chart = spark_svg(row.get("series") or [])
    src = f'<p class="muted">Public TCGPlayer snapshots via <a href="{e(row.get("url") or "#")}" target="_blank" rel="noopener">Limitless</a>. Fair use for commentary and research.</p>' if row.get("url") else ""
    offer = {
        "@type": "Offer",
        "url": row["buy"],
        "priceCurrency": "USD",
        "availability": "https://schema.org/InStock",
    }
    if row.get("spot") is not None:
        offer["price"] = f"{row['spot']:.2f}"
    card_ld = ld_script(
        {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": f'{row["name"]} ({row["set"]} {row["number"]})',
            "image": row.get("image") or (CANON + "/img/pkdl-hero.jpg"),
            "description": f'{row["name"]} Pokémon TCG card from {row["set"]}. Market price and tournament lists.',
            "brand": {"@type": "Brand", "name": "Pokémon TCG"},
            "sku": f'{row["set"]}-{row["number"]}',
            "offers": offer,
        }
    )
    return head(
        f'{row["name"]} ({row["set"]} {row["number"]}) Price & Card Info',
        f'{row["name"]} {row["set"]} {row["number"]} market price, history, and TCGPlayer affiliate buy link. Pokémon TCG collectible.',
        row["href"],
        row["image"] if row.get("image") else "/img/pkdl-hero.jpg",
        extra=card_ld,
        og_type="product",
        image_alt=row["name"],
    ) + header("collect") + f"""
    <main id="main" class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/collectibles/">Collectibles</a> / <a href="/collectibles/cards/">Cards</a> / {e(row["name"])}</div>
        <div class="price-hero collect-hero">
          <img src="{e(row["image"])}" alt="{e(row["name"])}" />
          <div>
            <div class="muted">{e(row["set"])} · {e(row["number"])}</div>
            <h1 class="page-title">{e(row["name"])}</h1>
            <p class="muted">{e(meta_line)}</p>
            {artist}
            <div class="big-price">${(row["spot"] or 0):.2f}</div>
            <p class="muted">7-day {ch7} · 30-day {ch30}</p>
            {market_actions(row)}
            <p style="margin-top:10px"><a class="shop-buy" href="{row["buy"]}" target="_blank" rel="noopener nofollow sponsored">Buy on TCGplayer</a></p>
          </div>
        </div>
        <section style="margin-top:22px">
          <div class="section-title"><h3>Price history</h3><div class="muted">Market snapshots</div></div>
          {chart}
          {src}
        </section>
        <section style="margin-top:22px">
          <div class="section-title"><h3>Posted in these lists</h3></div>
          <ul class="list">{used}</ul>
        </section>
        <p class="amazon-disclosure-line">TCGplayer affiliate partner 7670706 / 1780961. As an Amazon Associate I earn from qualifying purchases on shop pages.</p>
      </div>
    </main>
""" + footer()



def page_prices():
    rows = price_records()
    slim = [{k: r[k] for k in ("name", "set", "number", "image", "spot", "change7", "change30", "series", "buy", "href")} for r in rows]
    payload = json.dumps(slim, ensure_ascii=False)
    movers = [m for m in sorted(rows, key=lambda r: abs(r["change7"] or 0), reverse=True) if m["change7"] is not None][:6]
    mover_html = "\n".join(
        f'<li><a class="item" href="{m["href"]}"><div><div style="font-weight:700">{e(m["name"])}</div><div class="muted">{e(m["set"])} {e(m["number"])}</div></div><div class="{"up" if (m["change7"] or 0)>=0 else "down"}">{m["change7"]:+.1f}%</div></a></li>'
        for m in movers
    )
    return head(
        "Pokémon card price tracker | Pokémon Decklists",
        "Pokémon TCG card price history and trends from public TCGPlayer market snapshots. Affiliate buy links on every card.",
        "/price-tracker.html",
        extra='<script src="/js/prices.js" defer></script>',
    ) + header("market") + f"""
    <main id="main" class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/collectibles/">Collectibles</a> / Price tracker</div>
        <h1 class="page-title">Card price tracker</h1>
        <p>Market history for singles that posted in August–September 2026 lists. Charts are public TCGPlayer snapshots via Limitless. Open a name for the collectible card page. Every buy button is an affiliate link.</p>
        {market_subnav("tracker")}
        <p><a class="home-ghost" href="/collectibles/">Collectibles hub</a> · <a class="home-ghost" href="/collectibles/cards/">Catalog</a> · <a class="home-ghost" href="/collectibles/movers.html">Movers</a></p>
        <div class="section-title"><h3>Biggest 7-day moves</h3><div class="muted">From this tracker set</div></div>
        <ul class="list">{mover_html}</ul>
        <div id="price-focus"></div>
        <form class="site-search" role="search" onsubmit="return false">
          <label class="site-search-label" for="price-q">Filter cards</label>
          <div class="site-search-row">
            <input id="price-q" type="search" placeholder="Dragapult, Night Stretcher, MEG…" />
          </div>
        </form>
        <div id="tracker" style="overflow:auto">
          <table class="price-table">
            <thead><tr><th></th><th>Card</th><th>Market</th><th>7d</th><th>30d</th><th>Trend</th><th></th></tr></thead>
            <tbody id="price-body"></tbody>
          </table>
        </div>
        <script type="application/json" id="price-data">{payload}</script>
        <p class="amazon-disclosure-line">TCGplayer links use partner ID 7670706 / 1780961. As an Amazon Associate I earn from qualifying purchases on shop pages.</p>
      </div>
    </main>
""" + footer()


def shop_cards(items) -> str:
    bits = []
    for name, note, photo, url in items:
        bits.append(
            f"""          <article class="shop-card">
            <a class="shop-photo-link" href="{url}" target="_blank" rel="sponsored noopener noreferrer">
              <img class="shop-photo" src="/img/shop/{photo}" alt="{e(name)}" />
            </a>
            <div style="font-weight:800">{e(name)}</div>
            <p class="shop-note">{e(note)}</p>
            <a class="shop-buy" href="{url}" target="_blank" rel="sponsored noopener noreferrer">View on Amazon</a>
          </article>"""
        )
    return "\n".join(bits)


def page_shop_index():
    sections = []
    for key, title in SHOP_TITLES.items():
        sections.append(
            f"""        <div class="section-title" style="margin-top:28px">
          <h3>{title}</h3>
          <a href="/shop/{key}.html">All {title.lower()} →</a>
        </div>
        <div class="shop-grid">
{shop_cards(SHOP[key][:4] if key=="sleeves" else SHOP[key])}
        </div>"""
        )
    return head("Shop | Sleeves, dice, playmats, deck boxes | Pokémon Decklists", "Pokémon TCG sleeves, dice, playmats, and deck boxes via Amazon. Same affiliate shop as One Piece Deck Base.", "/shop/") + header("shop") + f"""
    <main id="main" class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Shop</div>
        <h1 class="page-title">Shop</h1>
        <p>Same table gear and the same Amazon affiliate links as One Piece Deck Base. Open Amazon for live price and stock. 63×88 mm sleeves fit Pokémon cards.</p>
        {''.join(sections)}
        <p class="amazon-disclosure-line">As an Amazon Associate I earn from qualifying purchases.</p>
      </div>
    </main>
""" + footer()


def page_shop_cat(key: str):
    title = SHOP_TITLES[key]
    return head(f"{title} | Shop | Pokémon Decklists", f"{title} for Pokémon TCG via Amazon affiliate links.", f"/shop/{key}.html") + header("shop") + f"""
    <main id="main" class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/shop/">Shop</a> / {title}</div>
        <h1 class="page-title">{title}</h1>
        <p>Same SKUs and amzn.to links as the OPDB shop.</p>
        <div class="shop-grid">{shop_cards(SHOP[key])}</div>
        <p class="amazon-disclosure-line">As an Amazon Associate I earn from qualifying purchases.</p>
      </div>
    </main>
""" + footer()


GUIDES = [
    ("pokemon-tcg", "Pokémon TCG", "The Pokémon Trading Card Game: 60-card constructed, six prizes, energy attachments."),
    ("standard", "Standard format", "H, I, and J regulation marks after the 2026 rotation. Used at Worlds, Internationals, and Regionals."),
    ("expanded", "Expanded format", "Black & White forward. Official Play! Pokémon format with a separate ban list."),
    ("gym-leader-challenge", "Gym Leader Challenge", "Singleton, one type, no rule boxes. The community format that still feels like a gym."),
    ("pokemon-tcg-pocket", "Pokémon TCG Pocket", "Twenty-card mobile lists. Different energy, huge online cups in August and September 2026."),
    ("regulation-marks", "Regulation marks", "The letter on the card is legality, not the set symbol. G rotated in 2026."),
    ("mega-evolution", "Mega Evolution", "Mega Evolution Pokémon ex are Basic, Stage 1, or Stage 2 and give three prizes."),
    ("worlds-2026", "World Championships 2026", "Moscone Center, San Francisco, 28–30 August 2026. Andrew Hedrick on Dragapult."),
    ("play-pokemon", "Play! Pokémon", "Championship Points, League Cups, Regionals, Internationals, Worlds."),
    ("starter-decks", "Starter decks", "How a 60-card list is built, what to buy first, and where the shop sleeves go."),
    ("locals", "Locals", "League Challenges and store cups. Post a list the same way OPDB posts locals."),
    ("limitless", "Limitless", "Where these tables come from: Limitless TCG and Limitless Play."),
    ("constructed", "Constructed", "60 cards, 4-of, Basic Energy unlimited. Pocket is the 20-card cousin."),
    ("collectibles", "Collectibles and prices", "How the price tracker, card pages, and TCGPlayer market history work."),
    ("championship-series", "Championship Series", "2026 Play! Pokémon circuit after rotation."),
    ("rotation-2026", "2026 rotation", "G-mark cards left Standard on 26 March (Live) / 10 April (paper)."),
    ("how-to-read-a-list", "How to read a list", "Count, set, number, placing, and why Pocket lists look short."),
    ("buying-singles", "Buying singles", "Match the print, the mark, and the format. Affiliate buy links explained."),
    ("event-prep", "Event prep", "What to sleeve, what to print, and which official page actually registers you."),
    ("pocket-vs-paper", "Pocket vs paper", "Twenty cards is a different game. Do not cross the counts."),
    ("glc-building", "Building for GLC", "One type, one of each name, no rule boxes. How to start a gym pile."),
]


def page_guides_index():
    cards = []
    for slug, title, blurb in GUIDES:
        cards.append(
            f'<a class="guide-tile" href="/guides/{slug}.html"><strong>{e(title)}</strong><span>{e(blurb)}</span></a>'
        )
    types = "\n".join(
        f'<a class="guide-tile type" href="/guides/types/{key}.html"><span class="dot" style="background:{hx}"></span><strong>{lab}</strong><span>{lab} energy lists in this window</span></a>'
        for key, lab, hx in TYPES
    )
    return head(
        "Pokémon TCG guides | Pokémon Decklists",
        "Guides for Pokémon TCG formats, regulation marks, Worlds 2026, how to read a list, and types — with real decklists attached.",
        "/guides/",
    ) + header("guides") + f"""
    <main id="main" class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Guides</div>
        <p class="kicker">Field notes</p>
        <h1 class="page-title">Guides</h1>
        <p class="lede">Writing that sits on top of the tables. Each topic page is a short brief plus lists from this window — not a wiki dump, not a scraped FAQ.</p>
        {essay_grid_html()}
        <section style="margin-top:28px">
          <div class="section-title"><h3>Topics</h3><div class="muted">{len(GUIDES)} briefs</div></div>
          <div class="guide-tiles">{"".join(cards)}</div>
        </section>
        <section style="margin-top:28px">
          <div class="section-title"><h3>Types</h3><div class="muted">Energy identity</div></div>
          <div class="guide-tiles">{types}</div>
        </section>
      </div>
    </main>
""" + footer()


def page_guide(slug, title, blurb):
    related = [x for x in LISTS if slug.replace("-", " ") in (clean(x.get("archetype") or "") + " " + x["format"]).lower()][:8]
    if slug == "worlds-2026":
        related = [x for x in LISTS if x.get("event") == "World Championships 2026"][:10]
    if slug == "pokemon-tcg-pocket" or slug == "pocket-vs-paper":
        related = [x for x in LISTS if x["format"] == "pocket"][:10]
    if slug == "gym-leader-challenge" or slug == "glc-building":
        related = [x for x in LISTS if x["format"] == "glc"][:10]
    if slug == "standard":
        related = [x for x in LISTS if x["format"] == "standard"][:10]
    if slug == "expanded":
        related = [x for x in LISTS if x["format"] == "expanded"][:10]
    body = GUIDE_BODY.get(slug) or f"<p>{e(blurb)}</p>"
    extra = ld_script(
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": blurb,
            "datePublished": NOW,
            "author": {"@type": "Organization", "name": SITE},
            "publisher": {"@id": CANON + "/#org"},
            "mainEntityOfPage": CANON + f"/guides/{slug}.html",
        }
    )
    return head(
        f"{title} | Guides | Pokémon Decklists",
        blurb,
        f"/guides/{slug}.html",
        extra=extra,
        og_type="article",
    ) + header("guides") + f"""
    <main id="main" class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/guides/">Guides</a> / {e(title)}</div>
        <p class="kicker">Guide · {NOW}</p>
        <h1 class="page-title">{e(title)}</h1>
        <p class="lede">{e(blurb)}</p>
        <div class="prose">{body}</div>
        <p class="muted" style="margin-top:18px">Pokémon Decklists is a fan site. Lists are public tournament tables. Not affiliated with Nintendo, The Pokémon Company, Creatures Inc., GAME FREAK, or Wizards of the Coast.</p>
        <div class="section-title"><h3>Lists to open</h3></div>
        <ul class="list">{list_index_items(related) or '<li class="muted">See the format hubs.</li>'}</ul>
      </div>
    </main>
""" + footer()


def page_type_guide(key, lab, hx):
    related = [x for x in LISTS if key in list_types(x)][:12]
    return head(f"{lab} type Pokémon TCG | Guides", f"{lab} energy lists on Pokémon Decklists.", f"/guides/types/{key}.html") + header("guides") + f"""
    <main id="main" class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/guides/">Guides</a> / {lab}</div>
        <p class="kicker">Type identity</p>
        <h1 class="page-title">{lab} type</h1>
        <span class="color-pill color-{key}"><span class="dot" style="background:{hx}"></span>{lab}</span>
        <div class="prose">{type_body(key, lab)}</div>
        <ul class="list" style="margin-top:16px">{list_index_items(related)}</ul>
      </div>
    </main>
""" + footer()


def page_events():
    return head(
        "Pokémon TCG events and schedule | Pokémon Decklists",
        "Official Play! Pokémon events, Worlds 2026, and where to find League Cups and Regionals.",
        "/events.html",
    ) + header("events") + """
    <main id="main" class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Events</div>
        <h1 class="page-title">Events and schedule</h1>
        <p>Official calendars first. Cup lists on this site are public tables from Limitless, not a substitute for Play! Pokémon registration. For what the room actually played in this window, read <a href="/desk.html">the Desk report</a>.</p>
        <a class="events-banner" href="https://events.pokemon.com/EventLocator" target="_blank" rel="noopener">
          <div>
            <div class="kicker">Official</div>
            <div class="title">Play! Pokémon event locator</div>
            <div class="muted" style="color:rgba(255,255,255,.82);margin-top:4px">League Challenges, League Cups, prereleases, Regionals</div>
          </div>
          <div class="go">Locator →</div>
        </a>
        <section style="margin-top:22px">
          <div class="section-title"><h3>Championship dates</h3><div class="muted">2026 circuit</div></div>
          <ul class="text-leader-list">
            <li><span>World Championships 2026</span><span class="muted">28–30 Aug · Moscone Center, San Francisco</span></li>
            <li><span>Worlds TCG finals</span><span class="muted">30 Aug · Chase Center</span></li>
            <li><span>Standard rotation (paper)</span><span class="muted">10 Apr 2026 · G-mark out</span></li>
            <li><span>ME: 30th Celebration</span><span class="muted">English street date 16 Sep 2026</span></li>
          </ul>
          <p>Worlds 2026 Masters: 797 players, winner Andrew Hedrick on Dragapult. Full table on <a href="https://limitlesstcg.com/tournaments/515" target="_blank" rel="noopener">Limitless</a> and lists on this site.</p>
        </section>
        <section style="margin-top:22px">
          <div class="section-title"><h3>Official links</h3></div>
          <ul class="list">
            <li><a class="item" href="https://championships.pokemon.com/en-us/about/world-championships" target="_blank" rel="noopener"><div style="font-weight:700">Pokémon World Championships</div><div class="link">Open →</div></a></li>
            <li><a class="item" href="https://www.pokemon.com/us/play-pokemon/" target="_blank" rel="noopener"><div style="font-weight:700">Play! Pokémon hub</div><div class="link">Open →</div></a></li>
            <li><a class="item" href="https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources/" target="_blank" rel="noopener"><div style="font-weight:700">Tournament rules and resources</div><div class="link">Open →</div></a></li>
            <li><a class="item" href="https://www.pokemon.com/us/pokemon-tcg/" target="_blank" rel="noopener"><div style="font-weight:700">Official Pokémon TCG</div><div class="link">Open →</div></a></li>
            <li><a class="item" href="https://tcgpocket.pokemon.com/" target="_blank" rel="noopener"><div style="font-weight:700">Pokémon TCG Pocket</div><div class="link">Open →</div></a></li>
            <li><a class="item" href="https://play.limitlesstcg.com/" target="_blank" rel="noopener"><div style="font-weight:700">Limitless Play (online cups)</div><div class="link">Open →</div></a></li>
          </ul>
        </section>
      </div>
    </main>
""" + footer()


def page_rules():
    return head(
        "Pokémon TCG formats and banlist | Pokémon Decklists",
        "Standard rotation, Expanded, Gym Leader Challenge, Pocket, and Unlimited in one place.",
        "/format.html",
    ) + header("rules") + """
    <main id="main" class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Format</div>
        <h1 class="page-title">Format rules</h1>
        <p>Lists on this site are tagged by format. Standard is the championship pile. Pocket, GLC, Expanded, and vintage Unlimited sit next to it instead of under a leader name.</p>
        <section style="margin-top:22px">
          <div class="section-title"><h3>Standard 2026</h3><div class="muted">H / I / J</div></div>
          <p>G-mark cards left Standard on 26 March 2026 for Pokémon TCG Live and 10 April 2026 for paper Play! Pokémon events. Mega Evolution Pokémon ex follow normal evolution rules and award three Prize cards.</p>
          <p class="muted">Official: <a href="https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources/" target="_blank" rel="noopener">Play! Pokémon rules</a>.</p>
        </section>
        <section style="margin-top:22px">
          <div class="section-title"><h3>Other formats</h3></div>
          <ul class="meta-blurbs">
            <li><a href="/formats/expanded.html">Expanded</a><span class="muted">BW+</span><p>Wider constructed pool. Still an official Play! Pokémon format at some events.</p></li>
            <li><a href="/formats/glc.html">Gym Leader Challenge</a><span class="muted">Community</span><p>Singleton, one type, no rule-box Pokémon. Ban list at gymleaderchallenge.com.</p></li>
            <li><a href="/formats/pocket.html">Pokémon TCG Pocket</a><span class="muted">Mobile</span><p>20-card lists. Separate product line, separate cups.</p></li>
            <li><a href="/formats/unlimited.html">Unlimited</a><span class="muted">Vintage</span><p>Base–Neo and EX-era community cups in August 2026.</p></li>
          </ul>
        </section>
        <section class="faq">
          <div class="section-title"><h3>FAQ</h3></div>
          <details><summary>Where do the decklists come from?</summary><p>Worlds 2026 from the public Limitless TCG table. Online cups from Limitless Play standings. Community rows only if a full list is posted.</p></details>
          <details><summary>Are you affiliated with Pokémon?</summary><p>No. Fan site. Not affiliated with Nintendo, The Pokémon Company, Creatures Inc., GAME FREAK, or Wizards of the Coast.</p></details>
        </section>
      </div>
    </main>
""" + footer()


def page_privacy():
    return head(
        "Privacy Policy | Pokémon Decklists",
        "Privacy Policy for Pokémon Decklists: cookies, analytics, advertising, and affiliate links.",
        "/privacy.html",
    ) + header() + """
    <main id="main" class="single">
      <div class="card hero policy">
        <div class="crumb"><a href="/">Home</a> / Privacy Policy</div>
        <h1 class="page-title">Privacy Policy</h1>
        <p class="muted">Last updated: September 7, 2026</p>
        <p>Pokémon Decklists ("we," "us," or "this site") respects your privacy. This Privacy Policy explains what information we collect when you visit pokemondecklists.com, how we use it, and the choices you have.</p>
        <section>
          <h3>Information We Collect</h3>
          <p><strong>Automatically collected information:</strong> Like most websites, we automatically collect certain information when you visit, including your IP address, browser type, device type, pages viewed, and time spent on the site. This is collected through cookies, log files, and similar technologies.</p>
          <p><strong>Information you provide:</strong> If you join a Discord we later announce, or contact us directly, any information you share there is subject to that platform's own privacy policy, not this one.</p>
          <p>We do not require account creation or collect personal information such as your name, email address, or payment details through this site.</p>
        </section>
        <section>
          <h3>Cookies</h3>
          <p>We use cookies and similar tracking technologies to understand how visitors use the site (analytics), remember basic preferences, and support advertising.</p>
          <p>You can disable cookies through your browser settings. Doing so may affect some site functionality.</p>
        </section>
        <section>
          <h3>Advertising</h3>
          <p>This site displays advertisements through Google AdSense (publisher <code>ca-pub-1074015774205047</code>). Google and its partners may use cookies to serve ads based on your prior visits. You can opt out of personalized advertising at <a href="https://adssettings.google.com/" target="_blank" rel="noopener">Google's Ads Settings</a> and review <a href="https://policies.google.com/technologies/partner-sites" target="_blank" rel="noopener">How Google uses information from sites or apps that use our services</a>.</p>
        </section>
        <section>
          <h3>Affiliate partnerships</h3>
          <p>Some links on this site are affiliate links. If you buy through them, we may earn a commission. That does not change the price you pay.</p>
          <p><strong>Amazon.</strong> We are an Amazon Associate. The <a href="/shop/">Shop</a> links to Amazon for sleeves, dice, playmats, deck boxes, and table extras, and we earn from qualifying purchases.</p>
          <p><strong>TCGplayer.</strong> We are a TCGplayer affiliate (Impact partner 7670706 / 1780961). Buy links on decklists, the price tracker, and collectibles card pages go to TCGplayer, and we may earn a commission if you purchase after clicking them.</p>
          <p>Other retailer programs listed on <a href="/partners.html">Partners</a> are application links only until an account is approved. We do not invent tracking IDs for programs we have not joined.</p>
        </section>
        <section>
          <h3>Price tools stored on your device</h3>
          <p>Watchlist, binder quantities, paid prices, and alert thresholds are saved in your browser with localStorage under <code>pkdl-market-v1</code>. They are not sent to our servers. Clearing site data removes them.</p>
        </section>
        <section>
          <h3>Analytics</h3>
          <p>We may use third-party analytics services (such as Google Analytics) to understand site traffic. This data is used in aggregate and is not used to personally identify you.</p>
        </section>
        <section>
          <h3>Children's Privacy</h3>
          <p>This site is not directed at children under 13, and we do not knowingly collect personal information from children under 13.</p>
        </section>
        <section>
          <h3>Fair use and trademarks</h3>
          <p>Pokémon Decklists is a fan site. Pokémon and Pokémon character names are trademarks of Nintendo / Creatures Inc. / GAME FREAK. The Pokémon TCG is published by The Pokémon Company International. This site is not affiliated with, endorsed by, or sponsored by Nintendo, The Pokémon Company, Creatures Inc., GAME FREAK, or Wizards of the Coast. Card images and tournament lists are used under fair use for commentary, reporting, and research from publicly posted sources.</p>
        </section>
        <section>
          <h3>Third-Party Links</h3>
          <p>Our site links to third-party content, including tournament results and retailers. We are not responsible for the privacy practices of these external sites.</p>
        </section>
        <section>
          <h3>Changes to This Policy</h3>
          <p>We may update this Privacy Policy from time to time. Changes will be posted on this page with an updated "Last updated" date.</p>
        </section>
        <section>
          <h3>Contact Us</h3>
          <p>Discord is a placeholder without a link for now. Pokémon Decklists is a fan site and is not affiliated with Nintendo, The Pokémon Company, Creatures Inc., GAME FREAK, or Wizards of the Coast.</p>
        </section>
      </div>
    </main>
""" + footer()


def page_search():
    groups = []
    for f in FORMATS:
        rows = [x for x in LISTS if x["format"] == f["id"]][:30]
        items = "\n".join(
            f'<li data-q="{e(clean(x.get("title"))+" "+clean(x.get("archetype"))+" "+clean(x.get("event"))+" "+x["format"])}"><a class="item" href="{href_list(x)}"><div style="font-weight:700">{e(clean(x.get("title")))}</div><div class="link">Open →</div></a></li>'
            for x in rows
        )
        groups.append(f'<section class="search-group" data-search-group><div class="section-title"><h3>{e(f["name"])}</h3></div><ul class="list">{items}</ul></section>')
    priced = price_records()[:40]
    card_items = "\n".join(
        f'<li data-q="{e(r["name"]+" "+r["set"]+" "+r["number"]+" collectible price")}"><a class="item" href="{r["href"]}"><div style="font-weight:700">{e(r["name"])}</div><div class="muted">{e(r["set"])} {e(r["number"])}</div></a></li>'
        for r in priced
    )
    groups.append(f'<section class="search-group" data-search-group><div class="section-title"><h3>Collectibles</h3></div><ul class="list">{card_items}</ul></section>')
    return head("Search PKMN decklists | Pokémon Decklists", "Search Pokémon TCG decklists by format, player, archetype, or event.", "/search.html") + header("search") + f"""
    <main id="main" class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Search</div>
        <h1 class="page-title">Search</h1>
        <form class="site-search" method="get" action="/search.html" role="search">
          <label class="site-search-label" for="q">Search PKMN decklists</label>
          <div class="site-search-row">
            <input id="q" type="search" name="q" placeholder="Dragapult, Hedrick, Pocket, GLC…" />
            <button type="submit">Search</button>
          </div>
        </form>
        <p id="search-status" class="muted" hidden></p>
        {''.join(groups)}
      </div>
    </main>
""" + footer()


def page_market_shell(
    title: str,
    desc: str,
    path: str,
    current: str,
    heading: str,
    intro: str,
    body: str,
    banner: str = "/img/art/art-market-desk.jpg",
    image_alt: str = "Original painting of a trading-card market desk",
) -> str:
    return head(
        title,
        desc,
        path,
        banner,
        extra=market_data_script(),
        image_alt=image_alt,
    ) + header("market") + f"""
    <main id="main" class="single">
      <img class="market-banner" src="{e(banner)}" alt="{e(image_alt)}" width="1600" height="900">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/market/">Market</a>{" / " + e(heading) if path != "/market/" else ""}</div>
        <p class="kicker">Price community</p>
        <h1 class="page-title">{e(heading)}</h1>
        <p>{intro}</p>
        {market_subnav(current)}
        {body}
        <p class="amazon-disclosure-line">TCGplayer affiliate partner 7670706 / 1780961. As an Amazon Associate I earn from qualifying purchases on shop pages. Watchlist, binder, and alerts stay in this browser.</p>
      </div>
    </main>
""" + footer()


def page_market_hub():
    tools = [
        ("/market/watchlist.html", "Watchlist", "Pin prints. Spot and 7-day change refresh from this site’s catalog."),
        ("/market/binder.html", "Binder P&amp;L", "Quantity and what you paid, versus live market."),
        ("/market/compare.html", "Compare prints", "Two card photos, two spots, two 7-day moves."),
        ("/market/alerts.html", "Price alerts", "Below / above checks when you open the alerts page."),
        ("/market/staples.html", "Staples", "Most-copied Pokémon in the current list window, with price if we track it."),
        ("/price-tracker.html", "Full tracker", "Charts, 7-day and 30-day trends, filter the whole set."),
        ("/collectibles/movers.html", "Movers", "Biggest percentage swings in the last week."),
        ("/collectibles/cards/", "Catalog", "Every priced single with a card page."),
    ]
    tool_html = "".join(
        f'<a class="market-tool" href="{href}"><strong>{label}</strong><span class="muted">{blurb}</span></a>'
        for href, label, blurb in tools
    )
    body = f"""
        <p class="muted" id="market-desk-note">Watchlist, binder, and alerts stay in this browser. No account.</p>
        {market_brief_html()}
        <div class="market-tools">{tool_html}</div>
        <section style="margin-top:22px">
          <div class="section-title"><h3>Highest market right now</h3><a href="/collectibles/cards/">Catalog →</a></div>
          {card_wall_html(16)}
        </section>
        <section style="margin-top:22px">
          <div class="section-title"><h3>Artwork at the desk</h3><a href="/gallery.html">Gallery →</a></div>
          <div class="art-inline">
            <img src="/img/art/art-binder.jpg" alt="Collector binder painting">
            <img src="/img/art/art-gallery.jpg" alt="Card-art gallery painting">
            <img src="/img/art/art-shop-wall.jpg" alt="Card-shop wall painting">
          </div>
        </section>
"""
    return page_market_shell(
        "Pokémon TCG price community | Pokémon Decklists",
        "Watchlist, binder profit and loss, print compare, and price alerts for Pokémon TCG singles. Public TCGPlayer market snapshots plus affiliate buy links.",
        "/market/",
        "hub",
        "Market desk",
        "A price community on top of the tracker: watch prints, log a binder, compare two cards, and set below/above checks. Live TCGplayer and Amazon links stay on. Nothing here requires a login.",
        body,
    )


def page_watchlist():
    return page_market_shell(
        "Card watchlist | Pokémon Decklists",
        "Save Pokémon TCG prints in this browser and check live spot prices from the site catalog.",
        "/market/watchlist.html",
        "watch",
        "Watchlist",
        "Tap Watch on any collectible card page. The list lives in this browser only.",
        '<div id="watch-list" class="collect-grid"></div>',
    )


def page_binder():
    return page_market_shell(
        "Binder profit and loss | Pokémon Decklists",
        "Track Pokémon TCG binder quantity and paid price versus live market, in this browser.",
        "/market/binder.html",
        "binder",
        "Binder P&L",
        "Add a print from a card page. Edit qty and what you paid. Totals use the latest spot we published — not a live brokerage.",
        '<p id="binder-sum" hidden></p><div id="binder-list"></div>',
        "/img/art/art-binder.jpg",
        "Original painting of a collector’s binder",
    )


def page_compare():
    return page_market_shell(
        "Compare Pokémon TCG prints | Pokémon Decklists",
        "Compare two Pokémon TCG prints: photos, market spot, and 7-day change.",
        "/market/compare.html",
        "compare",
        "Compare prints",
        "Pick two singles from the tracker. Share the URL — the pair is in the query string.",
        """<div class="compare-pick">
          <label>Print A <select id="compare-a"></select></label>
          <label>Print B <select id="compare-b"></select></label>
        </div>
        <div id="compare-out"></div>""",
    )


def page_alerts():
    return page_market_shell(
        "Pokémon TCG price alerts | Pokémon Decklists",
        "Set below and above price checks for watched Pokémon TCG prints. Checks run when you open this page.",
        "/market/alerts.html",
        "alerts",
        "Price alerts",
        "Watch a card first. Then set a floor or ceiling. This is a page-load check, not a push notification.",
        '<div id="alert-hits" hidden></div><div id="alert-list"></div>',
    )


def page_staples():
    rows = staple_rows()
    bits = [
        "<table class=\"price-table staples-table\"><thead><tr>"
        "<th></th><th>Pokémon</th><th>Copies in window</th><th>Spot</th><th>7d</th><th></th>"
        "</tr></thead><tbody>"
    ]
    for name, qty, match, img in rows:
        thumb = (match or {}).get("image") or img
        if match:
            ch = match["change7"]
            chs = "—" if ch is None else f"{ch:+.1f}%"
            cls = "" if ch is None else ("up" if ch >= 0 else "down")
            spot = f'${(match["spot"] or 0):.2f}'
            open_ = f'<a class="home-ghost" href="{e(match["href"])}">Open</a>'
            pic = f'<a href="{e(match["href"])}"><img src="{e(thumb)}" alt="{e(name)}" width="40" height="56"></a>'
        else:
            chs, cls, spot, open_ = "—", "", "—", ""
            pic = f'<img src="{e(thumb)}" alt="{e(name)}" width="40" height="56">' if thumb else ""
        bits.append(
            f'<tr><td>{pic}</td><td style="font-weight:700">{e(name)}</td>'
            f"<td>{qty}</td><td>{spot}</td><td class=\"{cls}\">{chs}</td><td>{open_}</td></tr>"
        )
    bits.append("</tbody></table>")
    return page_market_shell(
        "Most-played Pokémon staples | Pokémon Decklists",
        "Pokémon lines copied most in August–September 2026 lists, with market price when the print is in the tracker.",
        "/market/staples.html",
        "staples",
        "Staples",
        "Counted from Pokémon rows in the current list window. If we track a print with the same name, you get spot, trend, and the card page.",
        "".join(bits),
    )


def page_gallery():
    portraits = "".join(
        f'<a href="{e(src)}"><img src="{e(src)}" alt="{e(alt)}" width="367" height="512" loading="lazy"><span>{e(alt)}</span></a>'
        for src, alt, kind in ORIG_ART
        if kind == "portrait"
    )
    wides = "".join(
        f'<a href="{e(src)}"><img src="{e(src)}" alt="{e(alt)}" width="1280" height="720" loading="lazy"><span>{e(alt)}</span></a>'
        for src, alt, kind in ORIG_ART
        if kind == "wide"
    )
    return head(
        "Original Pokémon-style artwork | Pokémon Decklists",
        "Original fan paintings in a Pokémon trading-card style. Not official Pokémon art and not affiliated with Nintendo or The Pokémon Company.",
        "/gallery.html",
        "/img/art/art-gallery.jpg",
        image_alt="Original painting of a card-art gallery",
    ) + header() + f"""
    <main id="main" class="single">
      <img class="market-banner" src="/img/art/art-gallery.jpg" alt="Original painting of a card-art gallery" width="1600" height="900">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Artwork gallery</div>
        <h1 class="page-title">Artwork gallery</h1>
        <p>Original paintings made for this site. Creature designs are invented. They are not official Pokémon, not set art, and not a substitute for licensed cards. Real card photos live on <a href="/collectibles/">collectibles</a>.</p>
        <div class="section-title"><h3>Creatures</h3><div class="muted">{sum(1 for a in ORIG_ART if a[2]=="portrait")} portraits</div></div>
        <div class="gallery-grid">{portraits}</div>
        <div class="section-title" style="margin-top:22px"><h3>Desk and shop</h3></div>
        <div class="gallery-grid gallery-wide">{wides}</div>
      </div>
    </main>
""" + footer()


def partner_card(tag: str, tag_class: str, name: str, blurb: str, href: str, cta: str) -> str:
    return (
        f'<article class="partner-card"><span class="tag {tag_class}">{e(tag)}</span>'
        f"<h3>{name}</h3><p class=\"muted\">{blurb}</p>"
        f'<p><a class="home-ghost" href="{e(href)}" target="_blank" rel="noopener">{e(cta)}</a></p></article>'
    )


def page_partners():
    live = [
        partner_card(
            "Live",
            "live",
            "Google AdSense",
            f"Auto ads on every page. Publisher {ADS}. Listed in ads.txt as DIRECT.",
            "https://www.google.com/adsense/",
            "AdSense publisher center",
        ),
        partner_card(
            "Live",
            "live",
            "TCGplayer via Impact",
            "Impact partner 7670706 / 1780961. Buy buttons on lists, the tracker, and card pages wrap this live link.",
            PARTNER,
            "Open the live TCGplayer partner link",
        ),
        partner_card(
            "Live",
            "live",
            "Amazon Associates",
            "Shop sleeves, dice, playmats, deck boxes, and table extras. Same amzn.to SKUs as the shop — no extra tracking IDs invented.",
            "/shop/",
            "Open the Amazon shop",
        ),
    ]
    apply = [
        ("Impact.com", "Network that already powers the live TCGplayer link. Apply as a publisher to add more advertisers (GameStop, Whatnot, others on Impact).", "https://impact.com/publishers/", "Apply on Impact"),
        ("TCGplayer program notes", "Official write-up of the TCGplayer affiliate program and the Impact campaign form.", "https://docs.tcgplayer.com/docs/tcgplayer-affiliate-program", "Read TCGplayer docs"),
        ("eBay Partner Network", "Auction and Buy It Now listings. Official publisher signup.", "https://partnernetwork.ebay.com/", "Apply to EPN"),
        ("ShareASale", "Marketplace with hobby and collectibles merchants. Publisher application.", "https://www.shareasale.com/info/affiliates/", "Apply to ShareASale"),
        ("CJ Affiliate", "Commission Junction publisher enrollment for retail programs.", "https://www.cj.com/publisher", "Apply to CJ"),
        ("Rakuten Advertising", "Publisher signup for retail and collectible advertisers on Rakuten.", "https://rakutenadvertising.com/publishers/", "Apply to Rakuten"),
        ("Awin", "Publisher network with US and EU retail programs.", "https://www.awin.com/us/publishers", "Apply to Awin"),
        ("Whatnot Affiliates", "Live selling and TCG lots. Official Impact-powered application.", "https://www.whatnotaffiliates.com/", "Apply to Whatnot"),
        ("TikTok Shop Affiliate", "Creator/affiliate center for TikTok Shop US.", "https://affiliate-us.tiktok.com/", "Open TikTok Shop Affiliate"),
        ("YouTube Shopping", "YouTube’s shopping affiliate program for product shelves and tagged videos.", "https://support.google.com/youtube/answer/13360964", "YouTube Shopping help"),
        ("Cardmarket", "EU singles marketplace. Start from their affiliate help article, then apply if the region fits.", "https://help.cardmarket.com/en/AffiliateProgram", "Cardmarket affiliate help"),
        ("Partnerize", "Publisher network used by several entertainment and retail brands.", "https://partnerize.com/en-us/publishers", "Apply to Partnerize"),
        ("Walmart Creator", "Creator affiliate program for general retail, including toys and games aisles.", "https://www.walmart.com/creator", "Walmart Creator"),
    ]
    apply_html = "".join(
        partner_card("Apply next", "apply", name, blurb, href, cta) for name, blurb, href, cta in apply
    )
    return head(
        "Affiliate and partner programs | Pokémon Decklists",
        "Live AdSense, TCGplayer, and Amazon partnerships, plus official signup pages for more affiliate networks. Fan site — not affiliated with Nintendo.",
        "/partners.html",
        "/img/art/art-shop-wall.jpg",
        image_alt="Original painting of a card-shop gallery wall",
    ) + header("partners") + f"""
    <main id="main" class="single">
      <img class="market-banner" src="/img/art/art-shop-wall.jpg" alt="Original painting of a card-shop gallery wall" width="1600" height="900">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Partners</div>
        <h1 class="page-title">Partners</h1>
        <p>Three programs are already wired on this site. Everything under <strong>Apply next</strong> is an official public signup page — use them to enroll. We will not paste fake partner IDs. Discord remains a placeholder with no invite link.</p>
        <div class="section-title"><h3>Already live</h3></div>
        <div class="partner-grid">{''.join(live)}</div>
        <div class="section-title" style="margin-top:22px"><h3>Apply next</h3><div class="muted">{len(apply)} official programs</div></div>
        <p class="muted">These are opportunities to sign up. Approval is on their side. After you are in, we can hang the real tracking links next to the live TCGplayer and Amazon ones.</p>
        <div class="partner-grid">{apply_html}</div>
        <p class="amazon-disclosure-line">As an Amazon Associate I earn from qualifying purchases. TCGplayer links are affiliate links. Not affiliated with Nintendo, The Pokémon Company, Creatures Inc., GAME FREAK, or Wizards of the Coast.</p>
      </div>
    </main>
""" + footer()


def page_desk():
    counts = format_census()
    pocket = top_archetypes("pocket", 4)
    glc = top_archetypes("glc", 4)
    pocket_html = "".join(f"<li><span>{e(n)}</span><strong>{c}</strong></li>" for n, c in pocket)
    glc_html = "".join(f"<li><span>{e(n)}</span><strong>{c}</strong></li>" for n, c in glc)
    extra = ld_script(
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "The Desk — Pokémon TCG window report",
            "datePublished": NOW,
            "author": {"@type": "Organization", "name": SITE},
            "publisher": {"@id": CANON + "/#org"},
        }
    )
    return head(
        "The Desk | Pokémon TCG window report",
        "Editorial report on August–September 2026 Pokémon TCG lists: Standard after Worlds, Pocket cups, GLC, and the price desk.",
        "/desk.html",
        "/img/art/art-binder.jpg",
        extra=extra,
        og_type="article",
        image_alt="Original painting of a collector’s binder",
    ) + header("desk") + f"""
    <main id="main" class="single">
      <img class="market-banner" src="/img/art/art-binder.jpg" alt="" width="1600" height="900">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / The Desk</div>
        <p class="kicker">Window report · {NOW}</p>
        <h1 class="page-title">The Desk</h1>
        <p class="lede">A fan journal sitting on {len(LISTS):,} public lists. Not a rumor mill. Not a shopfront wearing a magazine costume. The tables first, then the sentences.</p>
        <div class="prose">
          <p>Worlds 2026 is over. The paper is still Standard: H, I, and J. Hedrick’s Dragapult is the headline and, in this window, also the plurality — one hundred Standard lists under that name, plus Dusknoir and Blaziken cousins. Alakazam / Dudunsparce, Basic Box, N’s Zoroark, and Slowking are the next seats, not a surprise “dead format.”</p>
          <p>Pocket is a different sport. {counts.get("pocket", 0)} lists, Mega Lucario and Mega Altaria at the front. If you drive to a League Challenge with a 20-card screenshot, you will be illegal. Read <a href="/guides/pocket-vs-paper.html">Pocket vs paper</a> before you sleeve either.</p>
          <p>GLC remains the gym: singleton, one type. Psychic and Colorless posted the most. Expanded is a small table ({counts.get("expanded", 0)} lists). Unlimited is the vintage cups ({counts.get("unlimited", 0)}). They belong here because they posted, not because they are Standard.</p>
        </div>
{digest_html()}
        <div class="desk-split">
          <div>
            <p class="kicker">Pocket names</p>
            <ul class="arch-lead">{pocket_html}</ul>
          </div>
          <div>
            <p class="kicker">GLC identities</p>
            <ul class="arch-lead">{glc_html}</ul>
          </div>
        </div>
        <div class="section-title" style="margin-top:28px"><h3>Keep reading</h3></div>
        {essay_grid_html()}
        <p class="muted" style="margin-top:18px">Numbers on this page are counted from the current JSON, not from memory. Methodology is public.</p>
      </div>
    </main>
""" + footer()


def page_about():
    return head(
        "About Pokémon Decklists",
        "Fan site for Pokémon TCG decklists, format hubs, and card prices. Not affiliated with Nintendo or The Pokémon Company.",
        "/about.html",
    ) + header() + f"""
    <main id="main" class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / About</div>
        <p class="kicker">The site</p>
        <h1 class="page-title">About</h1>
        <p class="lede">Pokémon Decklists is a fan journal for tournament lists, a price desk for the singles in those lists, and original writing about how to read both.</p>
        <div class="prose">
          <p>It is modeled on the same idea as One Piece Deck Base: format hubs, public tables, sleeves in a shop, prices with affiliate buy links. The Pokémon version is organized by <strong>format</strong> — Standard, Pocket, Gym Leader Challenge, Expanded, Unlimited — because Pokémon does not sit under a leader portrait.</p>
          <p>We are not Nintendo, The Pokémon Company, Creatures Inc., GAME FREAK, or Wizards of the Coast. We are not Limitless. Card images and tournament lists are used under fair use for commentary, reporting, and research from publicly posted sources.</p>
          <p>Advertising is Google AdSense (publisher <code>{ADS}</code>). Singles buy buttons are TCGplayer via Impact (7670706 / 1780961). The shop is Amazon Associates. Other networks on the <a href="/partners.html">partners</a> page are application links until an account is approved.</p>
          <p>Watchlist, binder, and alerts store in your browser. Discord is a placeholder with no invite. There is no account system.</p>
        </div>
        <p><a class="home-ghost" href="/methodology.html">Methodology</a> <a class="home-ghost" href="/faq.html">FAQ</a> <a class="home-ghost" href="/privacy.html">Privacy</a></p>
      </div>
    </main>
""" + footer()


def page_methodology():
    return head(
        "Methodology | Pokémon Decklists",
        "How Pokémon Decklists sources tournament lists, prices, staples, and the Standard tier list.",
        "/methodology.html",
        og_type="article",
    ) + header() + f"""
    <main id="main" class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Methodology</div>
        <p class="kicker">Sourcing · {NOW}</p>
        <h1 class="page-title">How we build this</h1>
        <div class="prose">
          <h3>Lists</h3>
          <p>Rows come from public Limitless TCG tables (Worlds 2026) and Limitless Play standings (online cups). A list is on this site if a full public table posted in the 1 August–9 September 2026 window. We do not invent placings. The source URL on a list page is the authority if we disagree with it.</p>
          <h3>Formats</h3>
          <p>Tags are Standard, Expanded, Gym Leader Challenge, Pocket, and Unlimited. Pocket is not paper. GLC is not Standard with a type filter. Mixing those on purpose is how you show up illegal — see the guides.</p>
          <h3>Prices</h3>
          <p>Spot, 7-day, and 30-day figures are public TCGPlayer market snapshots carried via Limitless for singles that appeared in this window. Charts are not a live brokerage. Buy buttons wrap the live TCGplayer Impact partner link.</p>
          <h3>Staples</h3>
          <p>The staples table sums Pokémon row counts across every list in the window. A name with 795 copies was copied a lot. It is not a price prediction.</p>
          <h3>Tier list</h3>
          <p>Standard only. Worlds 2026 top-table archetypes count three times; September Play cups count once. That keeps San Francisco in front without ignoring the weeks after. Pictures are from posted lists, not a licensed poster.</p>
          <h3>What we will not do</h3>
          <p>We will not paste fake affiliate IDs. We will not put a Discord URL on the site until there is a real invite. We will not claim Nintendo affiliation.</p>
        </div>
      </div>
    </main>
""" + footer()


def page_faq():
    qas = [
        ("Where do the decklists come from?", "Public Limitless TCG and Limitless Play tables. Worlds 2026 from the posted Masters table. Online cups from standings that include a full list."),
        ("Are you affiliated with Pokémon?", "No. Fan site. Not affiliated with Nintendo, The Pokémon Company, Creatures Inc., GAME FREAK, or Wizards of the Coast."),
        ("What formats do you cover?", "Standard, Expanded, Gym Leader Challenge, Pokémon TCG Pocket, and Unlimited. No Limited hub."),
        ("Why is Dragapult everywhere?", "Because the room played it. About a hundred Standard lists in this window are named Dragapult, plus variants. That is a table, not a recommendation."),
        ("Can I use a Pocket list at a League Challenge?", "Not if the challenge is paper Standard. Pocket is 20 cards and a different product. Read Pocket vs paper."),
        ("How do prices work?", "Public TCGPlayer market snapshots for singles that posted in this window. 7-day and 30-day change on the tracker. Not a live API tick."),
        ("Do you make money from buy links?", "Yes, if you click them. TCGplayer Impact 7670706 / 1780961. Amazon Associates on the shop. AdSense Auto ads. See Partners and Privacy."),
        ("Where is Discord?", "Placeholder. No invite link until there is a real server to join."),
        ("Is the watchlist an account?", "No. localStorage in this browser, key pkdl-market-v1. Clearing site data deletes it."),
        ("How often does the window update?", "This build is August–September 2026 (through 9 Sep). The date is on the Desk and in the footer of the methodology."),
    ]
    items = "".join(
        f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in qas
    )
    extra = ld_script(
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in qas
            ],
        }
    )
    return head(
        "FAQ | Pokémon Decklists",
        "Frequently asked questions about Pokémon Decklists: lists, formats, prices, affiliates, and Discord.",
        "/faq.html",
        extra=extra,
    ) + header() + f"""
    <main id="main" class="single">
      <div class="card hero policy">
        <div class="crumb"><a href="/">Home</a> / FAQ</div>
        <p class="kicker">Questions</p>
        <h1 class="page-title">FAQ</h1>
        <p class="lede">Short answers. The long ones live in the <a href="/guides/">guides</a> and <a href="/methodology.html">methodology</a>.</p>
        <section class="faq">{items}</section>
      </div>
    </main>
""" + footer()


def extras():
    (ROOT / "ads.txt").write_text("google.com, pub-1074015774205047, DIRECT, f08c47fec0942fa0\n")
    (ROOT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\n"
        "User-agent: Mediapartners-Google\nAllow: /\n\n"
        "Sitemap: https://pokemondecklists.com/sitemap.xml\n"
    )
    (ROOT / "site.webmanifest").write_text(json.dumps({
        "name": "Pokémon Decklists",
        "short_name": "PKMN Decklists",
        "description": "Pokémon TCG decklists by format, card prices, and tournament results.",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#f4f1ec",
        "theme_color": "#c62828",
        "lang": "en-US",
        "icons": [
            {"src": "/img/pkdl-logo-48.png", "sizes": "48x48", "type": "image/png"},
            {"src": "/img/pkdl-logo-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/img/pkdl-avatar.png", "sizes": "256x256", "type": "image/png"},
        ],
    }, indent=2))
    (ROOT / "opensearch.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
  <ShortName>Pokémon Decklists</ShortName>
  <Description>Search Pokémon TCG decklists and cards</Description>
  <InputEncoding>UTF-8</InputEncoding>
  <Image width="16" height="16" type="image/png">https://pokemondecklists.com/img/pkdl-logo-48.png</Image>
  <Url type="text/html" method="get" template="https://pokemondecklists.com/search.html?q={searchTerms}"/>
</OpenSearchDescription>
"""
    )
    hubs = {
        "/": ("daily", "1.0"),
        "/formats/": ("weekly", "0.9"),
        "/tier-list.html": ("weekly", "0.9"),
        "/collectibles/": ("daily", "0.9"),
        "/price-tracker.html": ("daily", "0.8"),
        "/market/": ("daily", "0.9"),
        "/market/watchlist.html": ("weekly", "0.7"),
        "/market/binder.html": ("weekly", "0.7"),
        "/market/compare.html": ("weekly", "0.7"),
        "/market/alerts.html": ("weekly", "0.7"),
        "/market/staples.html": ("daily", "0.8"),
        "/partners.html": ("monthly", "0.7"),
        "/gallery.html": ("monthly", "0.6"),
        "/events.html": ("weekly", "0.8"),
        "/guides/": ("monthly", "0.7"),
        "/desk.html": ("daily", "0.85"),
        "/about.html": ("yearly", "0.4"),
        "/methodology.html": ("monthly", "0.5"),
        "/faq.html": ("monthly", "0.5"),
        "/shop/": ("monthly", "0.6"),
        "/search.html": ("monthly", "0.4"),
        "/privacy.html": ("yearly", "0.2"),
    }
    urls = [
        "/", "/formats/", "/format.html", "/events.html", "/tier-list.html",
        "/price-tracker.html", "/collectibles/", "/collectibles/cards/", "/collectibles/sets/",
        "/collectibles/movers.html", "/shop/", "/guides/", "/privacy.html", "/search.html",
        "/market/", "/market/watchlist.html", "/market/binder.html", "/market/compare.html",
        "/market/alerts.html", "/market/staples.html", "/partners.html", "/gallery.html",
        "/desk.html", "/about.html", "/methodology.html", "/faq.html",
    ]
    urls += [f"/formats/{f['id']}.html" for f in FORMATS]
    urls += [f"/shop/{k}.html" for k in SHOP]
    urls += [f"/guides/{s}.html" for s, _, _ in GUIDES]
    urls += [f"/guides/types/{k}.html" for k, _, _ in TYPES]
    urls += [href_list(x) for x in LISTS]
    set_urls = set()
    for row in price_records():
        urls.append(row["href"])
        set_urls.add(f"/collectibles/sets/{row['set']}.html")
    urls.extend(sorted(set_urls))
    seen = []
    for u in urls:
        if u not in seen:
            seen.append(u)
    bits = []
    for u in seen:
        freq, pri = hubs.get(u, ("weekly", "0.6"))
        if u.startswith("/decklists/"):
            freq, pri = "monthly", "0.55"
        elif u.startswith("/collectibles/cards/") and u != "/collectibles/cards/":
            freq, pri = "weekly", "0.5"
        bits.append(
            f"  <url><loc>{CANON}{u}</loc><lastmod>{NOW}</lastmod>"
            f"<changefreq>{freq}</changefreq><priority>{pri}</priority></url>"
        )
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(bits)
        + "\n</urlset>\n"
    )
    write(
        "404.html",
        head(
            "Page not found | Pokémon Decklists",
            "That page is missing. Browse Pokémon TCG decklists by format or search the catalog.",
            "/404.html",
            robots="noindex, follow",
        )
        + header()
        + """
    <main id="main" class="single">
      <div class="card hero">
        <p class="kicker">404</p>
        <h1 class="page-title">This page is missing</h1>
        <p>The list or card you wanted is not here. Try search, or jump back to a format hub.</p>
        <p class="home-actions">
          <a class="btn-primary" href="/">Home</a>
          <a class="home-ghost" href="/formats/">Formats</a>
          <a class="home-ghost" href="/market/">Market</a>
          <a class="home-ghost" href="/search.html">Search</a>
        </p>
      </div>
    </main>
"""
        + footer(),
    )
    stale = ROOT / "formats" / "limited.html"
    if stale.exists():
        stale.unlink()
        print("removed", stale)
    (ROOT / ".nojekyll").write_text("")


def main():
    write("index.html", page_index())
    write("formats/index.html", page_formats_index())
    for f in FORMATS:
        write(f"formats/{f['id']}.html", page_format(f))
    for lst in LISTS:
        write(f"decklists/{lst['format']}/{lst['id']}.html", page_list(lst))
    write("tier-list.html", page_tier())
    write("price-tracker.html", page_prices())
    write("collectibles/index.html", page_collectibles_hub())
    write("collectibles/cards/index.html", page_catalog())
    write("collectibles/sets/index.html", page_sets_index())
    write("collectibles/movers.html", page_movers())
    priced = price_records()
    by_set = defaultdict(list)
    for row in priced:
        write(f"collectibles/cards/{card_file(row['set'], row['number'])}.html", page_card(row))
        by_set[row["set"]].append(row)
    for setc, cards in by_set.items():
        write(f"collectibles/sets/{setc}.html", page_set(setc, cards))
    write("shop/index.html", page_shop_index())
    for key in SHOP:
        write(f"shop/{key}.html", page_shop_cat(key))
    write("guides/index.html", page_guides_index())
    for slug, title, blurb in GUIDES:
        write(f"guides/{slug}.html", page_guide(slug, title, blurb))
    for key, lab, hx in TYPES:
        write(f"guides/types/{key}.html", page_type_guide(key, lab, hx))
    write("events.html", page_events())
    write("format.html", page_rules())
    write("privacy.html", page_privacy())
    write("search.html", page_search())
    write("market/index.html", page_market_hub())
    write("market/watchlist.html", page_watchlist())
    write("market/binder.html", page_binder())
    write("market/compare.html", page_compare())
    write("market/alerts.html", page_alerts())
    write("market/staples.html", page_staples())
    write("gallery.html", page_gallery())
    write("partners.html", page_partners())
    write("desk.html", page_desk())
    write("about.html", page_about())
    write("methodology.html", page_methodology())
    write("faq.html", page_faq())
    extras()
    print("lists", len(LISTS))


if __name__ == "__main__":
    main()
