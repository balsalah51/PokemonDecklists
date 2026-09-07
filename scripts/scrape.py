#!/usr/bin/env python3
"""Scrape Aug–Sep 2026 Pokémon TCG lists from Limitless and Limitless Play."""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
UA = "Mozilla/5.0 (compatible; PokemonDecklists/1.0; +https://pokemondecklists.com)"
SLEEP = 0.22


def get(url: str, retries: int = 3) -> str:
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            last = e
            time.sleep(0.8 * (i + 1))
    raise last


def get_json(url: str):
    return json.loads(get(url))


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:80] or "list"


def parse_cards_html(html: str) -> dict:
    out = {"pokemon": [], "trainer": [], "energy": []}
    current = "pokemon"
    heading = re.compile(
        r'<div class="decklist-column-heading">([^<]+)</div>', re.I
    )
    card_re = re.compile(
        r'<div class="decklist-card"[^>]*data-set="([^"]*)"[^>]*data-number="([^"]*)"[^>]*>'
        r'[\s\S]*?<span class="card-count">(\d+)</span>\s*'
        r'<span class="card-name">([^<]+)</span>'
        r'[\s\S]*?(?:href="(https://partner\.tcgplayer\.com[^"]+)"[^>]*>\s*\$([0-9.]+))?',
        re.I,
    )
    # Split by headings then parse cards in each column
    parts = re.split(r'(<div class="decklist-column-heading">)', html)
    blob = html
    sections = re.findall(
        r'<div class="decklist-column-heading">([^<]+)</div>([\s\S]*?)(?=<div class="decklist-column-heading">|</div>\s*</div>\s*</div>\s*<)',
        html,
    )
    if not sections:
        # fallback: all cards
        for m in re.finditer(
            r'data-set="([^"]+)"[^>]*data-number="([^"]+)"[\s\S]*?<span class="card-count">(\d+)</span>\s*<span class="card-name">([^<]+)</span>',
            html,
        ):
            out["pokemon"].append(
                {"count": int(m.group(3)), "set": m.group(1), "number": m.group(2), "name": m.group(4).strip()}
            )
        return out
    for title, body in sections:
        t = title.lower()
        if "pok" in t:
            bucket = "pokemon"
        elif "train" in t:
            bucket = "trainer"
        elif "energ" in t:
            bucket = "energy"
        else:
            bucket = "trainer"
        for m in re.finditer(
            r'data-set="([^"]+)"[^>]*data-number="([^"]+)"[\s\S]*?<span class="card-count">(\d+)</span>\s*<span class="card-name">([^<]+)</span>[\s\S]{0,600}?card-price usd"[^>]*>\$([0-9.]+)?',
            body,
        ):
            item = {
                "count": int(m.group(3)),
                "set": m.group(1),
                "number": m.group(2),
                "name": m.group(4).strip(),
            }
            if m.group(5):
                item["price"] = float(m.group(5))
            out[bucket].append(item)
        if bucket == "energy" and not out["energy"]:
            # energy sometimes listed without set
            for m in re.finditer(
                r'<span class="card-count">(\d+)</span>\s*<span class="card-name">([^<]+)</span>',
                body,
            ):
                out["energy"].append({"count": int(m.group(1)), "name": m.group(2).strip(), "set": "", "number": ""})
    return out


def energies_of(decklist: dict) -> list[str]:
    names = []
    for e in decklist.get("energy") or []:
        if isinstance(e, str):
            names.append(e)
        elif isinstance(e, dict):
            names.append(e.get("name") or "")
    cleaned = []
    for n in names:
        n = re.sub(r"\s+(Energy|energy)$", "", n).strip()
        n = n.replace("Basic ", "")
        if n:
            cleaned.append(n)
    # unique preserve order
    seen = []
    for n in cleaned:
        key = n.lower()
        if key not in {x.lower() for x in seen}:
            seen.append(n)
    return seen


def card_img(card: dict, pocket: bool = False) -> str:
    s = (card.get("set") or "").strip()
    n = str(card.get("number") or "").strip()
    if not s or not n:
        return ""
    if pocket:
        return f"https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/pocket/{s}/{s}_{n}_EN.webp"
    return f"https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/tpci/{s}/{s}_{n}_R_EN.png"


def flatten_play_list(dl: dict, pocket: bool) -> dict:
    if not isinstance(dl, dict):
        return {"pokemon": [], "trainer": [], "energy": []}
    out = {"pokemon": [], "trainer": [], "energy": []}
    for key in ("pokemon", "trainer"):
        for c in dl.get(key) or []:
            item = {
                "count": int(c.get("count") or 1),
                "set": c.get("set") or "",
                "number": str(c.get("number") or ""),
                "name": c.get("name") or "",
            }
            item["image"] = card_img(item, pocket)
            out[key].append(item)
    energy = dl.get("energy") or []
    if energy and isinstance(energy[0], str):
        for name in energy:
            out["energy"].append({"count": 0, "name": name, "set": "", "number": "", "image": ""})
    else:
        for c in energy:
            item = {
                "count": int(c.get("count") or 1),
                "set": c.get("set") or "",
                "number": str(c.get("number") or ""),
                "name": c.get("name") or "",
            }
            item["image"] = card_img(item, pocket)
            out["energy"].append(item)
    return out


def scrape_worlds(limit: int = 24) -> list[dict]:
    html = get("https://limitlesstcg.com/tournaments/515")
    rows = []
    for m in re.finditer(
        r'<tr data-rank="(\d+)" data-name="([^"]+)" data-country="([^"]+)" data-deck="([^"]*)"[\s\S]*?href="/decks/list/(\d+)"',
        html,
    ):
        rank, name, country, deck, lid = m.groups()
        rows.append(
            {
                "rank": int(rank),
                "player": name,
                "country": country,
                "archetype": deck,
                "list_id": lid,
            }
        )
        if len(rows) >= limit:
            break
    lists = []
    for row in rows:
        time.sleep(SLEEP)
        url = f"https://limitlesstcg.com/decks/list/{row['list_id']}"
        try:
            page = get(url)
        except Exception as e:
            print("worlds fail", row, e)
            continue
        parsed = parse_cards_html(page)
        for bucket in ("pokemon", "trainer", "energy"):
            for c in parsed[bucket]:
                c["image"] = card_img(c, False)
        placing = row["rank"]
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(placing, "th")
        if 10 <= placing % 100 <= 20:
            suffix = "th"
        title = f"{placing}{suffix} {row['player']} — {row['archetype']}"
        slug = slugify(f"{placing}-{row['player']}-{row['archetype']}-worlds-2026")
        lists.append(
            {
                "id": slug,
                "format": "standard",
                "title": title,
                "player": row["player"],
                "placing": placing,
                "event": "World Championships 2026",
                "event_url": "https://limitlesstcg.com/tournaments/515",
                "source_url": url,
                "date": "2026-08-28",
                "country": row["country"],
                "archetype": row["archetype"],
                "energies": energies_of(parsed),
                "decklist": parsed,
                "players": 797,
                "notes": "Masters Division · Limitless TCG public table",
            }
        )
        print("worlds", placing, row["player"], row["archetype"], "cards",
              sum(c["count"] for c in parsed["pokemon"] + parsed["trainer"] + parsed["energy"] if c.get("count")))
    return lists


def play_tournaments(game: str, fmt: str | None, limit: int = 30) -> list[dict]:
    q = f"https://play.limitlesstcg.com/api/tournaments?game={game}&limit={limit}"
    if fmt:
        q += f"&format={fmt}"
    data = get_json(q)
    out = []
    for t in data:
        date = (t.get("date") or "")[:10]
        if not (date.startswith("2026-08") or date.startswith("2026-09")):
            continue
        out.append(t)
    return out


def scrape_play(game: str, fmt_code: str | None, site_format: str, max_events: int, top_n: int, min_players: int = 6) -> list[dict]:
    events = play_tournaments(game, fmt_code, 40)
    events = [e for e in events if int(e.get("players") or 0) >= min_players]
    events.sort(key=lambda e: (-int(e.get("players") or 0), e.get("date") or ""), reverse=False)
    events.sort(key=lambda e: e.get("date") or "", reverse=True)
    picked = events[:max_events]
    lists = []
    pocket = site_format == "pocket"
    for ev in picked:
        tid = ev["id"]
        time.sleep(SLEEP)
        try:
            standings = get_json(f"https://play.limitlesstcg.com/api/tournaments/{tid}/standings")
        except Exception as e:
            print("standings fail", tid, e)
            continue
        date = (ev.get("date") or "")[:10]
        name = ev.get("name") or "Limitless Play"
        nplayers = int(ev.get("players") or len(standings))
        taken = 0
        for row in standings:
            if taken >= top_n:
                break
            dl = row.get("decklist")
            if not dl:
                continue
            parsed = flatten_play_list(dl, pocket)
            if not parsed["pokemon"]:
                continue
            placing = int(row.get("placing") or 0) or taken + 1
            player = row.get("name") or row.get("player") or "Unknown"
            arch = ""
            deck = row.get("deck") or {}
            if isinstance(deck, dict):
                arch = deck.get("name") or ""
            elif isinstance(deck, str):
                arch = deck
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(placing, "th")
            if 10 <= placing % 100 <= 20:
                suffix = "th"
            title = f"{placing}{suffix} {player}" + (f" — {arch}" if arch else "")
            slug = slugify(f"{placing}-{player}-{arch}-{tid[:6]}")
            lists.append(
                {
                    "id": slug,
                    "format": site_format,
                    "title": title,
                    "player": player,
                    "placing": placing,
                    "event": name,
                    "event_url": f"https://play.limitlesstcg.com/tournament/{tid}",
                    "source_url": f"https://play.limitlesstcg.com/tournament/{tid}/standings",
                    "date": date,
                    "country": row.get("country") or "",
                    "archetype": arch or (parsed["pokemon"][0]["name"] if parsed["pokemon"] else "Deck"),
                    "energies": energies_of(parsed),
                    "decklist": parsed,
                    "players": nplayers,
                    "notes": f"Limitless Play · {nplayers} players",
                    "record": row.get("record") or {},
                }
            )
            taken += 1
        print("play", site_format, date, name[:40], "got", taken)
    return lists


def scrape_limited_placeholder() -> list[dict]:
    """Limited rarely posts full lists on Play; keep the format page honest."""
    return []


def unique_cards(lists: list[dict]) -> list[dict]:
    seen = {}
    for lst in lists:
        if lst["format"] == "pocket":
            continue
        dl = lst.get("decklist") or {}
        for bucket in ("pokemon", "trainer", "energy"):
            for c in dl.get(bucket) or []:
                if not c.get("set") or not c.get("number"):
                    continue
                key = f"{c['set']}|{c['number']}|{c['name']}"
                if key not in seen:
                    seen[key] = {
                        "name": c["name"],
                        "set": c["set"],
                        "number": c["number"],
                        "image": c.get("image") or "",
                        "price": c.get("price"),
                        "count": 0,
                        "formats": set(),
                    }
                seen[key]["count"] += int(c.get("count") or 1)
                seen[key]["formats"].add(lst["format"])
    out = []
    for v in seen.values():
        v["formats"] = sorted(v["formats"])
        out.append(v)
    out.sort(key=lambda x: -x["count"])
    return out


def fetch_limitless_prices(cards: list[dict], max_cards: int = 36) -> dict:
    """Pull TCGPlayer history from Limitless card IDs."""
    prices = {}
    for card in cards[:max_cards]:
        setc, num = card["set"], card["number"]
        time.sleep(SLEEP)
        url = f"https://limitlesstcg.com/cards/{urllib.parse.quote(setc)}/{urllib.parse.quote(str(num))}"
        try:
            html = get(url)
        except Exception as e:
            print("card page fail", setc, num, e)
            continue
        m = re.search(r"var cardId\s*=\s*(\d+)", html)
        usd = re.search(r'class="card-price usd"[^>]*>\$([0-9.]+)', html)
        tcg = re.search(r"tcgplayer\.com/product/(\d+)", html)
        if not m:
            print("no cardId", setc, num)
            continue
        cid = m.group(1)
        time.sleep(SLEEP)
        try:
            hist = get_json(f"https://limitlesstcg.com/api/cards/{cid}/prices")
        except Exception as e:
            print("hist fail", cid, e)
            hist = {}
        tcgplayer = hist.get("tcgplayer") or []
        # keep last ~90 points
        if len(tcgplayer) > 120:
            tcgplayer = tcgplayer[-120:]
        key = f"{setc}-{num}"
        latest = None
        if tcgplayer:
            latest = tcgplayer[-1]
        prices[key] = {
            "name": card["name"],
            "set": setc,
            "number": num,
            "image": card.get("image") or "",
            "limitless_id": cid,
            "tcgplayer_id": tcg.group(1) if tcg else None,
            "spot": float(usd.group(1)) if usd else (latest.get("market") if isinstance(latest, dict) else None),
            "history": tcgplayer,
            "url": url,
            "count": card.get("count") or 0,
        }
        print("price", card["name"], setc, num, "pts", len(tcgplayer), "spot", prices[key]["spot"])
    return prices


def main():
    lists = []
    print("=== Worlds ===")
    lists += scrape_worlds(24)

    print("=== Standard Play ===")
    lists += scrape_play("PTCG", "STANDARD", "standard", max_events=4, top_n=8, min_players=100)

    print("=== Expanded ===")
    lists += scrape_play("PTCG", "EXPANDED", "expanded", max_events=4, top_n=5, min_players=6)

    print("=== GLC ===")
    lists += scrape_play("PTCG", "GLC", "glc", max_events=5, top_n=5, min_players=8)

    print("=== Pocket ===")
    lists += scrape_play("POCKET", None, "pocket", max_events=4, top_n=8, min_players=80)

    print("=== Vintage EX ===")
    lists += scrape_play("PTCG", "EX", "unlimited", max_events=3, top_n=4, min_players=8)

    print("=== Base-Neo ===")
    lists += scrape_play("PTCG", "BASENEO", "unlimited", max_events=3, top_n=4, min_players=8)

    # de-dupe ids
    used = set()
    for lst in lists:
        base = lst["id"]
        i = 2
        while lst["id"] in used:
            lst["id"] = f"{base}-{i}"
            i += 1
        used.add(lst["id"])

    lists.sort(key=lambda x: (x.get("date") or "", -int(x.get("placing") == 1), x.get("placing") or 99), reverse=True)

    payload = {
        "scraped": "2026-09-07",
        "source": ["https://limitlesstcg.com/", "https://play.limitlesstcg.com/"],
        "lists": lists,
    }
    (DATA / "lists.json").write_text(json.dumps(payload, indent=2))
    print("wrote", len(lists), "lists")

    cards = unique_cards(lists)
    (DATA / "cards.json").write_text(json.dumps(cards, indent=2))
    print("unique constructed cards", len(cards))

    prices = fetch_limitless_prices(cards, 40)
    (DATA / "prices.json").write_text(json.dumps(prices, indent=2))
    print("prices", len(prices))


if __name__ == "__main__":
    main()
