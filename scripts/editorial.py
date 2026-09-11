"""Long-form copy for Pokémon Decklists. Imported by build.py."""

# Featured homepage essays: href, kicker, title, dek, image
ESSAYS = [
    (
        "/desk.html",
        "The Desk",
        "What this window actually says",
        "1,172 lists from 1 August to 9 September 2026. Dragapult still leads Standard. Pocket is a Mega Evolution cup.",
        "/img/art/art-binder.jpg",
    ),
    (
        "/guides/worlds-2026.html",
        "Worlds 2026",
        "San Francisco, then the weeks after",
        "Andrew Hedrick won Masters on Dragapult. The public table is on this site, not behind a paywall.",
        "/img/art/art-gallery.jpg",
    ),
    (
        "/guides/how-to-read-a-list.html",
        "Field notes",
        "How to read a posted list",
        "Count, set, number, name. What a 4-of means, what a 1-of is doing, and when Pocket is a different game.",
        "/img/art/art-sleeved-spread.jpg",
    ),
    (
        "/methodology.html",
        "Sourcing",
        "How lists and prices get here",
        "Limitless tables, public TCGPlayer snapshots, fair-use card images. No invented partner IDs.",
        "/img/art/art-shop-wall.jpg",
    ),
]

TYPE_BLURB = {
    "grass": "Grass in this window is often the Teal Mask / Ogerpon / Meganium line in Standard, or a GLC singleton pile that wants to stall and spread. Energy attachments are slower than Fire; the lists that work usually have a draw engine that does not care.",
    "fire": "Fire is the aggressive paper pile — Ethan’s Typhlosion, Mega Blaziken, Entei lines. Prize races are short. If a list posts four of a Stage 2, look at the draw and the rare candy count before you copy it.",
    "water": "Water is still the control and spread seat: Greninja, Starmie, Gyarados, Suicune in Pocket. Paper lists that look “just Water” are often a second type in the energy row.",
    "lightning": "Lightning is Miraidon, Magnezone, and the rush piles. Prize maps are front-loaded. Check the energy count twice — these lists brick if the math is tourist.",
    "psychic": "Psychic is Alakazam, Munkidori, and a lot of GLC. Status and disruption over raw numbers. A Psychic GLC list with twenty-two copies of the type is doing the format correctly.",
    "fighting": "Fighting is Lucario, Mega Lucario, Excadrill, and the Bench-snipe seats. Three-prize Megas change the math. Do not copy a Worlds Fighting list into a locals cup without counting prizes.",
    "darkness": "Darkness is N’s Zoroark, Honchkrow, and the mill / disruption cousins. The 4-of supporters matter more than the attackers. Read the trainer row first.",
    "metal": "Metal is still the awkward paper type — boxes, Magnezone hybrids, and the old Energy cards that spike on the tracker. A Metal list that posts in Unlimited is not a Standard list.",
    "fairy": "Fairy is thin in this window. If a list shows Fairy energy it is usually a splash or a Pocket experiment. Do not force a paper identity that the table is not playing.",
    "dragon": "Dragon is Dragapult, and then Dragapult with a friend (Dusknoir, Blaziken). One hundred Standard lists in this window are just “Dragapult.” Open three of them. The 1-ofs are the real list.",
    "colorless": "Colorless is Basic Box, Dudunsparce, and the GLC Colorless gym. Energy is easy; the constraint is the attacker suite. Colorless GLC is one of the few community piles that still looks like a gym leader’s box.",
}

GUIDE_BODY = {
    "pokemon-tcg": """
<p>The Pokémon Trading Card Game is a 60-card constructed game in paper and on Pokémon TCG Live. You take six Prize cards. You attach one Energy a turn unless a card says otherwise. The Pokémon in play have HP, attacks, and retreat costs. Knocking out a Mega Evolution Pokémon ex is usually three prizes, not two.</p>
<p>This site is organized by <strong>format</strong>, not by a leader name. That is the difference from One Piece Deck Base, whose hubs sit under a character. Open Standard if you want the championship pile. Open Pocket if you want the 20-card phone game. Open Gym Leader Challenge if you want singleton, one type, no rule boxes.</p>
<p>Lists here are public tournament tables from August and September 2026. They are not a substitute for the official rulebook. Official text lives on <a href="https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources/" target="_blank" rel="noopener">Play! Pokémon</a>.</p>
""",
    "standard": """
<p>Standard in 2026 is regulation marks <strong>H, I, and J</strong>. G-mark cards left the format on 26 March 2026 for Pokémon TCG Live and 10 April 2026 for paper Play! Pokémon events. Mega Evolution Pokémon ex are in the pool and follow ordinary evolution rules.</p>
<p>In this window the Standard table is not mysterious. Dragapult is the plurality — about a hundred lists under that name alone, plus Dusknoir and Blaziken variants. Alakazam / Dudunsparce, Basic Box, N’s Zoroark, and Slowking fill the next seats. The Worlds 2026 Masters winner was Andrew Hedrick on Dragapult.</p>
<p>When you copy a Standard list off this site, check the date. A 30 August Worlds list and a 8 September online cup are the same format, not the same metagame. Open the <a href="/tier-list.html">tier list</a> for the weighted view, then open three actual lists in the same archetype and diff the 1-ofs.</p>
""",
    "expanded": """
<p>Expanded is Black &amp; White forward, with its own ban list. It is still an official Play! Pokémon format at some events, but it is not the Worlds constructed seat. Lists on this site are the ones that actually posted in August–September 2026 — a small table compared with Standard.</p>
<p>Do not take an Expanded list into a Standard cup. The card pool is a decade wider. Ban lists change. Read the official Expanded legality page before you sleeve it for paper.</p>
""",
    "gym-leader-challenge": """
<p>Gym Leader Challenge is the community format that still feels like a gym: <strong>one type</strong>, <strong>one of each card name</strong>, no rule-box Pokémon (no ex / V / GX / Radiant / ACE SPEC as the format defines them). Sixty cards. The ban list lives at <a href="https://gymleaderchallenge.com/" target="_blank" rel="noopener">gymleaderchallenge.com</a>, not on this site.</p>
<p>In this window Psychic and Colorless post the most. A GLC list that looks “off-meta” is often just a gym identity — that is the point. Copy the type, not a Standard Dragapult core.</p>
<p>If you are building from scratch, start with the type page, then the GLC hub, then a singleton constraint. Four of a card name is a Standard habit. It is illegal here.</p>
""",
    "pokemon-tcg-pocket": """
<p>Pokémon TCG Pocket is a different product. Twenty-card lists, different energy rules, huge online cups. It is not paper Standard with fewer cards. A Mega Lucario ex / Lucario pile that is drowning Pocket cups in this window will not sleeve into a 60-card paper list.</p>
<p>This site tags Pocket as its own format. Filter there. The card images may look familiar; the counts will not. Energy is not “attach one per turn” the way paper players mean it.</p>
<p>Official client and rules: <a href="https://tcgpocket.pokemon.com/" target="_blank" rel="noopener">tcgpocket.pokemon.com</a>.</p>
""",
    "regulation-marks": """
<p>The letter in the corner of a Pokémon TCG card is the <strong>regulation mark</strong>. It is legality, not the set symbol. Standard 2026 is H, I, and J. G rotated out in spring 2026.</p>
<p>A card can be reprinted with a new mark. The old print with a rotated letter is not Standard-legal even if the name matches. When you buy singles for a paper list, match the mark, not just the name.</p>
<p>Pocket and Unlimited do not use the same letter as a Standard gate. Do not mix the systems.</p>
""",
    "mega-evolution": """
<p>Mega Evolution Pokémon ex in the 2026 paper game are not the 2014 Mega ruleset. They evolve normally (Basic, Stage 1, or Stage 2 as printed). Knocking one out is typically <strong>three Prize cards</strong>.</p>
<p>That prize map is why Mega Lucario, Mega Excadrill, Mega Starmie, and the Pocket Mega seats show up so often after Worlds. A two-prize attacker into a three-prize Mega is a different race. Count prizes before you copy the attacker suite.</p>
""",
    "worlds-2026": """
<p>The 2026 Pokémon World Championships were at the Moscone Center in San Francisco, 28–30 August 2026, with TCG finals at Chase Center on the 30th. Masters TCG: 797 players. Winner: Andrew Hedrick, Dragapult.</p>
<p>This site carries public Worlds lists from the Limitless table, plus the online cups that filled the two weeks after. That is why the homepage window is August–September 2026, not “all time.”</p>
<p>If you want the championship pile, start with <a href="/formats/standard.html">Standard</a>, then the <a href="/tier-list.html">tier list</a>, then a Worlds list with a placing next to the name. A 16th-place list from San Francisco is still a Worlds list.</p>
""",
    "play-pokemon": """
<p>Play! Pokémon is the official organized-play program: League Challenges, League Cups, Regionals, Internationals, Worlds, Championship Points. Registration and store locators are on Pokémon’s site, not here.</p>
<p>This site is a fan table of lists that already posted. It will not sign you up for a cup. Use the <a href="/events.html">events page</a> for official links, then come back here to see what the room actually played.</p>
""",
    "starter-decks": """
<p>A paper Standard list is 60 cards. You may play four copies of a card name, except Basic Energy, which is unlimited. Pocket is 20. GLC is singleton.</p>
<p>What to buy first is not a secret: a playable Standard pile from a recent cup, 100 standard-size (63×88 mm) sleeves, and a box. The <a href="/shop/">shop</a> is Amazon affiliate table gear — sleeves, dice, mats, boxes — not a substitute for the singles in the list.</p>
<p>Do not buy four of every Pokémon on a Worlds list if you are going to locals tomorrow. Buy the 4-ofs that show up in three lists of the same archetype. The 1-ofs are the room’s opinion, not a law.</p>
""",
    "locals": """
<p>League Challenges and store cups are where most paper lists actually get played. This site posts a locals list the same way it posts Worlds: if a full public table exists, it can sit next to San Francisco.</p>
<p>A locals Dragapult list from 8 September is often more useful than a 32nd-place Worlds list if you are playing Tuesday night. Filter by date. Read the event name. “Pudding Weekly” is not Moscone.</p>
""",
    "limitless": """
<p>Almost every row on this site starts as a public table on <a href="https://limitlesstcg.com/" target="_blank" rel="noopener">Limitless TCG</a> or <a href="https://play.limitlesstcg.com/" target="_blank" rel="noopener">Limitless Play</a>. Worlds 2026 is the big paper table. Online cups are Limitless Play standings.</p>
<p>We are not Limitless. We are not Pokémon. We rehost public lists, with format tags and a price desk, so you can read them without hopping ten URLs. If a list is wrong, the source URL on the list page is the authority.</p>
""",
    "constructed": """
<p>Constructed, in Play! Pokémon language, means you bring a 60-card deck. Four-of per name. Unlimited Basic Energy. Best-of-three at most premier events, with some cups as single games — check the organizer.</p>
<p>Pocket is constructed in the loose sense (you built the list) and not in the paper sense (20 cards, different energy). This site keeps them in different hubs on purpose.</p>
""",
    "collectibles": """
<p>The collectibles half of the site is the singles that showed up in this window’s lists, with public TCGPlayer market snapshots (via Limitless), a 7-day and 30-day change, and an affiliate buy link.</p>
<p>The <a href="/market/">market desk</a> adds a watchlist, a binder with qty and paid price, print compare, and below/above checks. Those tools live in your browser. They are not a brokerage and not a live feed from TCGPlayer’s API.</p>
<p>Prices move. A $135 Electrode ex from an old set is not a Standard staple. Read the set code.</p>
""",
    "championship-series": """
<p>The 2026 Championship Series is the Play! Pokémon season around rotation: League Cups, Regionals, Internationals, then Worlds in San Francisco at the end of August. Championship Points gate the invitation, not this site.</p>
<p>After Worlds the online cups keep posting. That is why September lists sit next to the Moscone table. The format did not rotate again on 1 September.</p>
""",
    "rotation-2026": """
<p>G-mark cards left Standard on <strong>26 March 2026</strong> (Pokémon TCG Live) and <strong>10 April 2026</strong> (paper Play! Pokémon). The legal pool is H, I, and J.</p>
<p>If a YouTube list still has a G-mark 4-of, it is either Expanded, Unlimited, or out of date. Check the letter. Then check this site’s date stamp.</p>
""",
    "how-to-read-a-list": """
<p>Every list on this site is a table: Pokémon, Trainer, Energy. Each row is a count, a set code, a number, and a name. “4 DRI 34 Ethan’s Typhlosion” means four copies of that print.</p>
<p>Read Pokémon first for the attacker, then Trainer for the engine, then Energy last. A Dragapult list with 4 Buddy-Buddy Poffin and a Dragapult list with 2 are not the same list. The 1-ofs (a single Boss’s Orders, a single counter Pokémon) are the player’s opinion of the room.</p>
<p>Placing is the number on the left of the title. 1st is the winner. 16th at Worlds is still a Worlds list. 16th at a 16-player weekly is the whole room. Open the event name.</p>
<p>Pocket lists will look short. They are supposed to. Do not “fix” them up to 60.</p>
""",
    "buying-singles": """
<p>Buy the print that matches the list: name, set, number, regulation mark. A reprint with a rotated letter is a different card for Standard.</p>
<p>TCGPlayer buttons on this site are affiliate links (Impact partner 7670706 / 1780961). The shop is Amazon Associates for sleeves and table gear. Neither is a price guarantee. Check condition (NM vs LP) before you click through a $100 vintage print.</p>
<p>Use <a href="/market/compare.html">compare</a> if two prints of a similar name are on the tracker. Use the <a href="/market/staples.html">staples</a> table to see which Pokémon lines were actually copied in this window — that is demand from lists, not from Twitter.</p>
""",
    "event-prep": """
<p>Paper: 60-card list, sleeves, dice, a playmat if the store wants one, and a way to track prizes. The <a href="/shop/">shop</a> is the same Amazon kit as the sister One Piece site. 63×88 mm sleeves fit Pokémon cards.</p>
<p>Registration is on the Play! Pokémon locator or the store’s page. This site will not check you in. Read the format on the event posting. A GLC night is not Standard.</p>
<p>Bring the list printed or on your phone. Judges want a list, not a vibe. Copy from a page on this site the morning of — lists do not update themselves after you screenshot them in July.</p>
""",
    "pocket-vs-paper": """
<p>Pocket is 20 cards. Paper Standard is 60. Energy, prizes, and the set pool are different. A Mega Lucario ex pile that is 10% of Pocket cups in this window is a Pocket pile.</p>
<p>If you are learning the game on your phone, stay in the Pocket hub. If you are driving to a League Challenge, stay in Standard. Cross-pollinating “this attacker is good” is fine. Cross-pollinating the counts is how you show up illegal.</p>
""",
    "glc-building": """
<p>Pick a type. Play one of each card name. No rule-box Pokémon as the GLC document defines them. Check the live ban list on gymleaderchallenge.com before you sleeve a reprint that looks innocent.</p>
<p>A good GLC list looks like a gym leader’s box: 15–20 Pokémon, a trainer suite that does not repeat names, and enough energy that the singleton attackers can actually fire. Psychic and Colorless posted the most in this window. That is a hint, not a requirement.</p>
""",
}

GUIDE_SECTIONS = {
    "how-to-read-a-list": [
        ("Count", "The number on the left is copies in the 60 (or 20). Four is the constructed cap for named cards in Standard."),
        ("Set + number", "The print. DRI 34 is not DRI 32. The image on the row is that print."),
        ("Placing + event", "1st at a weekly and 16th at Worlds are not the same achievement. Read both."),
    ],
}


def type_body(key: str, lab: str) -> str:
    blurb = TYPE_BLURB.get(key, f"Lists that posted {lab} energy in this window.")
    return f"<p>{blurb}</p><p>These rows are lists whose posted energy includes {lab}. A dual-type Standard list will appear on more than one type page. That is intentional.</p>"
