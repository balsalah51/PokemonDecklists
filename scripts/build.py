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
NOW = "2026-09-09"

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
    return f"""      <nav aria-label="Primary">
        {a("/tier-list.html", "Tier List", "tier")}
        {a("/#recent", "Recent lists", "recent")}
        {a("/formats/", "Formats", "formats")}
        {a("/collectibles/", "Collectibles", "collect")}
        {a("/price-tracker.html", "Prices", "prices")}
        {a("/events.html", "Events", "events")}
        {a("/guides/", "Guides", "guides")}
        {a("/shop/", "Shop", "shop")}
        {a("/search.html", "Search", "search")}
        <span class="discord-nav" title="Discord coming soon">Discord</span>
      </nav>"""


def header(current: str = "") -> str:
    return f"""    <header>
      <a class="brand" href="/">
        <img class="logo" src="/img/pkdl-avatar.png" width="56" height="56" alt="Pokémon Decklists" />
        <div>
          <h1>Pokémon Decklists</h1>
          <div class="subtitle">PKMN decklists · Standard · Pocket · Gym Leader Challenge</div>
        </div>
      </a>
{nav(current)}
    </header>"""


def footer(current: str = "") -> str:
    return f"""    <footer>
      © <span id="year"></span> Pokémon Decklists — Fan site, not affiliated with Nintendo, The Pokémon Company, Creatures Inc., GAME FREAK, or Wizards of the Coast.
      As an Amazon Associate I earn from qualifying purchases.
      <a href="/tier-list.html">Tier List</a> · <a href="/formats/">Formats</a> · <a href="/collectibles/">Collectibles</a> · <a href="/price-tracker.html">Prices</a> · <a href="/guides/">Guides</a> · <a href="/shop/">Shop</a> · <a href="/privacy.html">Privacy</a>
    </footer>
  </div>
  <script>document.getElementById('year').textContent = new Date().getFullYear();</script>
  <script src="/js/tcgplayer-config.js"></script>
  <script src="/js/tcgplayer.js"></script>
  <script src="/js/site.js"></script>
</body>
</html>"""


def head(title: str, desc: str, path: str, image: str = "/img/pkdl-hero.jpg", extra: str = "") -> str:
    url = CANON + path
    img = image if image.startswith("http") else CANON + image
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{e(title)}</title>
  <meta name="description" content="{e(desc)}" />
  <link rel="stylesheet" href="/css/site.css?v=pkdl-3" />
  <link rel="canonical" href="{url}" />
  <meta name="robots" content="index, follow, max-image-preview:large" />
  <meta name="theme-color" content="#c62828" />
  <link rel="icon" href="/img/pkdl-logo-192.png" type="image/png" sizes="192x192" />
  <link rel="apple-touch-icon" href="/img/pkdl-logo-192.png" sizes="192x192" />
  <link rel="manifest" href="/site.webmanifest" />
  <link rel="search" type="application/opensearchdescription+xml" title="Pokémon Decklists" href="/opensearch.xml" />
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADS}" crossorigin="anonymous"></script>
  <meta property="og:site_name" content="Pokémon Decklists" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="{e(title)}" />
  <meta property="og:description" content="{e(desc)}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:image" content="{img}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{e(title)}" />
  <meta name="twitter:description" content="{e(desc)}" />
  <meta name="twitter:image" content="{img}" />
  {extra}
</head>
<body>
  <div class="wrap">
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
                <img class="recent-leader" src="{e(img)}" alt="" />
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
    extra = """  <script type="application/ld+json">{"@context":"https://schema.org","@type":"WebSite","name":"Pokémon Decklists","alternateName":["PKMN","Pokemon Decklists"],"url":"https://pokemondecklists.com/","potentialAction":{"@type":"SearchAction","target":"https://pokemondecklists.com/search.html?q={search_term_string}","query-input":"required name=search_term_string"}}</script>"""
    cards = "\n".join(
        f"""            <a class="format-card" href="/formats/{f['id']}.html">
              <img src="{f['img']}" alt="{e(f['name'])} format" />
              <div class="caption"><strong>{e(f['name'])}</strong><div class="muted">{e(f['kicker'])}</div></div>
            </a>"""
        for f in FORMATS
    )
    return head(
        "Pokémon TCG Decklists (PKMN) | Pokémon Decklists",
        "Pokémon TCG decklists by format: Standard, Pocket, Gym Leader Challenge, Expanded, and Unlimited. August and September 2026 lists, price tracker, and shop.",
        "/",
        extra=extra,
    ) + header() + f"""
    <main class="single home" role="main">
      <section class="home-splash" aria-label="Pokémon Decklists">
        <img class="home-splash-bg" src="/img/pkdl-hero.jpg" alt="Orange fire dragon in vintage Pokémon TCG style, Pokémon Decklists banner" width="1920" height="1080" fetchpriority="high" decoding="async">
        <div class="home-splash-copy">
          <h2>Pokémon Decklists</h2>
          <div class="formats">
            <span>Standard</span>
            <span>Pocket</span>
            <span>Gym Leader Challenge</span>
          </div>
        </div>
      </section>

      <a class="events-banner" id="events" href="/events.html">
        <div>
          <div class="kicker">Official Play! Pokémon</div>
          <div class="title">Events and championship schedule</div>
          <div class="muted" style="color:rgba(255,255,255,0.82);margin-top:4px">Worlds 2026, Regionals, League Cups, and the event locator</div>
        </div>
        <div class="go">Official events →</div>
      </a>

      <div class="home-halves">
        <section class="home-half home-half-play" id="competitive">
          <div class="home-half-head">
            <p class="kicker">Competitive</p>
            <h3>Decklists</h3>
            <p>{len(LISTS)} August–September 2026 lists, organized by format.</p>
          </div>
          <div class="home-half-body">
            <a class="half-link" href="#formats"><strong>Formats</strong><span>Types, color combos, recent lists</span></a>
            <a class="half-link" href="#recent"><strong>Recent lists</strong><span>Newest Worlds and Limitless Play cups</span></a>
            <a class="half-link" href="/tier-list.html"><strong>Tier list</strong><span>Standard after Worlds 2026</span></a>
            <a class="half-link" href="/events.html"><strong>Events</strong><span>Official locator and championship dates</span></a>
          </div>
        </section>
        <section class="home-half home-half-collect" id="collectibles-home">
          <div class="home-half-head">
            <p class="kicker">Collectibles</p>
            <h3>Prices &amp; card info</h3>
            <p>Market history, set pages, and TCGPlayer affiliate buys for singles.</p>
          </div>
          <div class="home-half-body">
            <a class="half-link" href="/collectibles/"><strong>Collectibles hub</strong><span>Catalog, movers, and card pages</span></a>
            <a class="half-link" href="/price-tracker.html"><strong>Price tracker</strong><span>Charts, 7-day / 30-day trends</span></a>
            <a class="half-link" href="/collectibles/sets/"><strong>Sets</strong><span>Singles grouped by set code</span></a>
            <a class="half-link" href="/shop/"><strong>Shop</strong><span>Sleeves and table gear on Amazon</span></a>
            {teasers}
          </div>
        </section>
      </div>

      <nav class="home-big3" aria-label="Main sections">
        <a class="home-big home-big-tier" href="/tier-list.html">
          <span class="home-big-title">Tier List</span>
          <span class="home-big-note">Standard after Worlds 2026</span>
        </a>
        <a class="home-big home-big-recent" href="#recent">
          <span class="home-big-title">Recent Lists</span>
          <span class="home-big-note">{len(LISTS)} lists this window</span>
        </a>
        <a class="home-big home-big-formats" href="#formats">
          <span class="home-big-title">Formats</span>
          <span class="home-big-note">Standard, Pocket, GLC, Expanded…</span>
        </a>
        <a class="home-big home-big-prices" href="/collectibles/">
          <span class="home-big-title">Collectibles</span>
          <span class="home-big-note">Prices, card info, set pages</span>
        </a>
        <a class="home-big home-big-shop" href="/shop/">
          <span class="home-big-title">Shop</span>
          <span class="home-big-note">Sleeves, dice, playmats, deck boxes</span>
        </a>
        <div class="home-big home-big-discord discord-placeholder">
          <div>
            <div class="home-big-title">Discord</div>
            <div class="note">Placeholder — invite coming soon. No link yet.</div>
          </div>
        </div>
      </nav>

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
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Formats</div>
        <h2>Formats</h2>
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
        f"{fmt['name']} decklists | Pokémon Decklists",
        f"{fmt['blurb']} Recent {fmt['name']} lists from August and September 2026.",
        f"/formats/{fmt['id']}.html",
        fmt["img"],
    ) + header("formats") + f"""
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/formats/">Formats</a> / {e(fmt['name'])}</div>
        <div class="leader-hero">
          <img src="{fmt['img']}" alt="{e(fmt['name'])} original artwork" />
          <div>
            <h2>{e(fmt['name'])}</h2>
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
            <input data-filter="q" placeholder="Player, archetype, event" />
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
    return head(
        f"{clean(lst.get('title'))} | {fmt['name']} | PKMN",
        f"{fmt['name']} decklist — {clean(lst.get('event'))} · {lst.get('date')}",
        href_list(lst),
        img,
    ).replace("<body>", f'<body class="{cls}">') + header() + f"""
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/formats/">Formats</a> / <a href="/formats/{lst['format']}.html">{e(fmt['name'])}</a> / Decklist</div>
        <h2>{e(clean(lst.get('title')))}</h2>
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
        "Standard Pokémon TCG tier list | Pokémon Decklists",
        "Standard tier list after the 2026 World Championships in San Francisco, cross-checked with September Limitless Play cups.",
        "/tier-list.html",
    ) + header("tier") + f"""
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Tier List</div>
        <h2>Standard tier list</h2>
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


def price_records() -> list[dict]:
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
    return rows


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
            f'<a class="collect-teaser" href="{m["href"]}"><img src="{e(m["image"])}" alt="">'
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
        f'<a class="collect-card" href="{c["href"]}"><img src="{e(c["image"])}" alt="">'
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
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Collectibles</div>
        <h2>Collectibles</h2>
        <p>The other half of the site. Singles that posted in August–September 2026 lists, with public TCGPlayer market history via Limitless, card facts, and affiliate buy links.</p>
        <div class="collect-jump">
          <a class="home-ghost" href="/price-tracker.html">Price tracker</a>
          <a class="home-ghost" href="/collectibles/cards/">Card catalog</a>
          <a class="home-ghost" href="/collectibles/sets/">Sets</a>
          <a class="home-ghost" href="/collectibles/movers.html">Movers</a>
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
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/collectibles/">Collectibles</a> / Cards</div>
        <h2>Card catalog</h2>
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
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/collectibles/">Collectibles</a> / Movers</div>
        <h2>Price movers</h2>
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
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/collectibles/">Collectibles</a> / Sets</div>
        <h2>Sets</h2>
        <p>Set codes from the August–September 2026 lists. Open a set for the singles we track.</p>
        <ul class="list">{"".join(items)}</ul>
      </div>
    </main>
""" + footer()


def page_set(setc: str, cards: list[dict]) -> str:
    grid = "\n".join(
        f'<a class="collect-card" href="{c["href"]}"><img src="{e(c["image"])}" alt="">'
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
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/collectibles/">Collectibles</a> / <a href="/collectibles/sets/">Sets</a> / {e(setc)}</div>
        <h2>{e(setc)}</h2>
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
    return head(
        f'{row["name"]} ({row["set"]} {row["number"]}) price and info | Collectibles',
        f'{row["name"]} {row["set"]} {row["number"]} market price, history, and TCGPlayer affiliate buy link.',
        row["href"],
        row["image"] if row.get("image") else "/img/pkdl-hero.jpg",
    ) + header("collect") + f"""
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/collectibles/">Collectibles</a> / <a href="/collectibles/cards/">Cards</a> / {e(row["name"])}</div>
        <div class="price-hero collect-hero">
          <img src="{e(row["image"])}" alt="{e(row["name"])}" />
          <div>
            <div class="muted">{e(row["set"])} · {e(row["number"])}</div>
            <h2 style="margin:4px 0 8px">{e(row["name"])}</h2>
            <p class="muted">{e(meta_line)}</p>
            {artist}
            <div class="big-price">${(row["spot"] or 0):.2f}</div>
            <p class="muted">7-day {ch7} · 30-day {ch30}</p>
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
    ) + header("prices") + f"""
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/collectibles/">Collectibles</a> / Price tracker</div>
        <h2>Card price tracker</h2>
        <p>Market history for singles that posted in August–September 2026 lists. Charts are public TCGPlayer snapshots via Limitless. Open a name for the collectible card page. Every buy button is an affiliate link.</p>
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
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Shop</div>
        <h2>Shop</h2>
        <p>Same table gear and the same Amazon affiliate links as One Piece Deck Base. Open Amazon for live price and stock. 63×88 mm sleeves fit Pokémon cards.</p>
        {''.join(sections)}
        <p class="amazon-disclosure-line">As an Amazon Associate I earn from qualifying purchases.</p>
      </div>
    </main>
""" + footer()


def page_shop_cat(key: str):
    title = SHOP_TITLES[key]
    return head(f"{title} | Shop | Pokémon Decklists", f"{title} for Pokémon TCG via Amazon affiliate links.", f"/shop/{key}.html") + header("shop") + f"""
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/shop/">Shop</a> / {title}</div>
        <h2>{title}</h2>
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
]


def page_guides_index():
    topics = "\n".join(
        f'<li><a class="item" href="/guides/{slug}.html"><div style="font-weight:700">{e(title)}</div><div class="link">Open →</div></a></li>'
        for slug, title, _ in GUIDES
    )
    types = "\n".join(
        f'<li><a class="item" href="/guides/types/{key}.html"><div style="font-weight:700">{lab} type</div><div class="link">Open →</div></a></li>'
        for key, lab, _ in TYPES
    )
    return head("Pokémon TCG guides | PKMN", "Guides for Pokémon TCG formats, regulation marks, Worlds 2026, and types, linking to real decklists.", "/guides/") + header("guides") + f"""
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Guides</div>
        <h2>Pokémon TCG guides</h2>
        <p>Topic and type pages that link to the lists on this site. Same job as the OPDB guides, rewritten for Pokémon.</p>
        <section><div class="section-title"><h3>Topics</h3><div class="muted">Play! Pokémon / PKMN</div></div>
        <ul class="list">{topics}</ul></section>
        <section style="margin-top:18px"><div class="section-title"><h3>Types</h3><div class="muted">Energy colors</div></div>
        <ul class="list">{types}</ul></section>
      </div>
    </main>
""" + footer()


def page_guide(slug, title, blurb):
    related = [x for x in LISTS if slug.replace("-", " ") in (clean(x.get("archetype") or "") + " " + x["format"]).lower()][:8]
    if slug == "worlds-2026":
        related = [x for x in LISTS if x.get("event") == "World Championships 2026"][:10]
    if slug == "pokemon-tcg-pocket":
        related = [x for x in LISTS if x["format"] == "pocket"][:10]
    if slug == "gym-leader-challenge":
        related = [x for x in LISTS if x["format"] == "glc"][:10]
    if slug == "standard":
        related = [x for x in LISTS if x["format"] == "standard"][:10]
    if slug == "expanded":
        related = [x for x in LISTS if x["format"] == "expanded"][:10]
    return head(f"{title} | Guides | Pokémon Decklists", blurb, f"/guides/{slug}.html") + header("guides") + f"""
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/guides/">Guides</a> / {e(title)}</div>
        <h2>{e(title)}</h2>
        <p>{e(blurb)}</p>
        <p>Pokémon Decklists is a fan site. Lists are public tournament tables. Not affiliated with Nintendo, The Pokémon Company, Creatures Inc., GAME FREAK, or Wizards of the Coast (the original English TCG publisher).</p>
        <div class="section-title"><h3>Lists to open</h3></div>
        <ul class="list">{list_index_items(related) or '<li class="muted">See the format hubs.</li>'}</ul>
      </div>
    </main>
""" + footer()


def page_type_guide(key, lab, hx):
    related = [x for x in LISTS if key in list_types(x)][:12]
    return head(f"{lab} type Pokémon TCG | Guides", f"{lab} energy lists on Pokémon Decklists.", f"/guides/types/{key}.html") + header("guides") + f"""
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / <a href="/guides/">Guides</a> / {lab}</div>
        <h2>{lab} type</h2>
        <p>Lists that posted {lab} energy in August–September 2026. Color identity for Pokémon, the same way OPDB tags leader colors.</p>
        <span class="color-pill color-{key}"><span class="dot" style="background:{hx}"></span>{lab}</span>
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
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Events</div>
        <h2>Events and schedule</h2>
        <p>Official calendars first. Cup lists on this site are public tables from Limitless, not a substitute for Play! Pokémon registration.</p>
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
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Format</div>
        <h2>Format rules</h2>
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
    <main class="single">
      <div class="card hero policy">
        <div class="crumb"><a href="/">Home</a> / Privacy Policy</div>
        <h2>Privacy Policy</h2>
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
          <p>We use cookies and similar tracking technologies to understand how visitors use the site (analytics), remember basic preferences, and support advertising if ads are enabled.</p>
          <p>You can disable cookies through your browser settings. Doing so may affect some site functionality.</p>
        </section>
        <section>
          <h3>Advertising</h3>
          <p>This site may display advertisements served by third-party providers, including Google AdSense. Google and its partners may use cookies to serve ads based on your prior visits. You can opt out of personalized advertising at <a href="https://adssettings.google.com/" target="_blank" rel="noopener">Google's Ads Settings</a> and review <a href="https://policies.google.com/technologies/partner-sites" target="_blank" rel="noopener">How Google uses information from sites or apps that use our services</a>.</p>
        </section>
        <section>
          <h3>Affiliate partnerships</h3>
          <p>Some links on this site are affiliate links. If you buy through them, we may earn a commission. That does not change the price you pay.</p>
          <p><strong>Amazon.</strong> We are an Amazon Associate. The <a href="/shop/">Shop</a> links to Amazon for sleeves, dice, playmats, deck boxes, and table extras, and we earn from qualifying purchases.</p>
          <p><strong>TCGplayer.</strong> We are a TCGplayer affiliate (Impact partner 7670706 / 1780961). Buy links on decklists, the price tracker, and collectibles card pages go to TCGplayer, and we may earn a commission if you purchase after clicking them.</p>
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
    <main class="single">
      <div class="card hero">
        <div class="crumb"><a href="/">Home</a> / Search</div>
        <h2>Search</h2>
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


def extras():
    (ROOT / "ads.txt").write_text("google.com, pub-1074015774205047, DIRECT, f08c47fec0942fa0\n")
    (ROOT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\nSitemap: https://pokemondecklists.com/sitemap.xml\n"
    )
    (ROOT / "site.webmanifest").write_text(json.dumps({
        "name": "Pokémon Decklists",
        "short_name": "PKMN",
        "description": "Pokémon TCG decklists by format.",
        "start_url": "/",
        "display": "browser",
        "background_color": "#f7f5f3",
        "theme_color": "#c62828",
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
  <Description>Search PKMN decklists</Description>
  <Url type="text/html" template="https://pokemondecklists.com/search.html?q={searchTerms}"/>
</OpenSearchDescription>
"""
    )
    urls = [
        "/", "/formats/", "/format.html", "/events.html", "/tier-list.html",
        "/price-tracker.html", "/collectibles/", "/collectibles/cards/", "/collectibles/sets/",
        "/collectibles/movers.html", "/shop/", "/guides/", "/privacy.html", "/search.html",
    ]
    urls += [f"/formats/{f['id']}.html" for f in FORMATS]
    urls += [f"/shop/{k}.html" for k in SHOP]
    urls += [f"/guides/{s}.html" for s, _, _ in GUIDES]
    urls += [f"/guides/types/{k}.html" for k, _, _ in TYPES]
    urls += [href_list(x) for x in LISTS]
    for row in price_records():
        urls.append(row["href"])
        urls.append(f"/collectibles/sets/{row['set']}.html")
    body = "\n".join(f"  <url><loc>{CANON}{u}</loc><lastmod>{NOW}</lastmod></url>" for u in urls)
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n'
    )
    css = (ROOT / "css" / "site.css").read_text()
    if ".discord-nav" not in css:
        (ROOT / "css" / "site.css").write_text(css + """
.discord-nav{color:var(--muted);font-weight:600;cursor:default}
header > nav[aria-label="Primary"] a:first-of-type{color:var(--accent);font-weight:800}
""")
    stale = ROOT / "formats" / "limited.html"
    if stale.exists():
        stale.unlink()
        print("removed", stale)


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
    extras()
    print("lists", len(LISTS))


if __name__ == "__main__":
    main()
