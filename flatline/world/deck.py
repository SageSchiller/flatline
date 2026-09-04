"""The deck, in the city (D135): what it knows when you are not jacked in.

Mail composed from the state of the world each time you read it (with
stable ids per day, so unread is a real thing), a search over every shelf
in the city, a watch that pings when a thing lands, a line to the other
runners that they answer according to what they think of you, and the
ads, which read you.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..content import feed
from ..content import districts, factions, npcs, offers, spots
from ..content import cyberware, drugs, hardware, programs, weapons
from ..content import armour as armour_content
from ..content import pit as pit_content


@dataclass
class Message:
    id: str
    sender: str
    kind: str
    text: str
    #: A command that acts on it, or ''.
    do: str = ''


#: The catalogues a search reads, by kind.
CATALOGUES = (('program', programs.BY_KEY), ('ware', cyberware.BY_KEY),
              ('component', hardware.BY_KEY), ('drug', drugs.BY_KEY),
              ('weapon', weapons.BY_KEY), ('armour', armour_content.BY_KEY))
#: A day, in shifts: the window mail is composed over.
DAY = 3
MAIL_READ_CAP = 200


def _day(game) -> int:
    return game.city.shift // DAY


def _pick(game, pool, salt: str):
    stream = game.rng.fork('events', f'feed:{salt}:{_day(game)}')
    return stream.pick(pool)


# --------------------------------------------------------------------------
# the ads
# --------------------------------------------------------------------------


def when(game, key: str) -> bool:
    """Whether a predicate from `feed.WHEN` holds."""
    char, city, alias, flags = game.char, game.city, game.alias, game.story.flags
    if key == 'any':
        return True
    if key == 'shot_at':
        return any('Shots in' in line for line in city.news[-12:])
    if key == 'hurt':
        return char.hurt >= max(3, char.integrity_max // 3)
    if key == 'drift':
        return char.dissonance >= 30
    if key == 'habit':
        return any(drugs.habit(char.chem, k) >= 2 for k in drugs.BY_KEY)
    if key == 'loud':
        w = weapons.BY_KEY.get(char.weapon)
        return bool(w and w.loud)
    if key == 'killer':
        return 'killer' in flags
    if key == 'veteran':
        return alias.runs >= 5
    if key == 'debt':
        return bool(game.debt.owed)
    if key == 'champion':
        return 'pit:champion' in flags
    if key == 'blooded':
        return 'blooded' in char.marks
    if key == 'hot':
        return alias.hottest[1] >= 40 or any(v for v in city.bounties.values())
    if key == 'broke':
        return char.credits < 200
    if key == 'rich':
        return char.credits >= 12000
    if key == 'chromed':
        return len(char.installed) >= 5
    if key == 'clean':
        return not char.installed
    return False


def ad_for(game, salt: str = '') -> feed.Ad:
    """The ad that has read you: the most specific that holds, or one of
    the ones for everybody."""
    live = [a for a in feed.ADS if a.when != 'any' and when(game, a.when)]
    if live:
        return _pick(game, live, 'ad' + salt)
    return _pick(game, [a for a in feed.ADS if a.when == 'any'], 'ad' + salt)


# --------------------------------------------------------------------------
# mail
# --------------------------------------------------------------------------


def messages(game) -> list[Message]:
    from . import rivals as rival_world
    from . import street as street_world
    city, char, alias, story = game.city, game.char, game.alias, game.story
    day = _day(game)
    out: list[Message] = []
    here = city.district.name
    partner = rival_world.active_partner(city.rivals)
    if partner is not None:
        out.append(Message(f'partner:{partner.key}:{day}', partner.name, 'partner',
                           _pick(game, feed.PARTNER_MAIL, 'partner').format(district=here),
                           do=f'who {partner.name.lower()}'))
    for r in city.rivals:
        if r.alive and r.bond == 'nemesis':
            out.append(Message(f'nemesis:{r.key}:{day}', r.name, 'nemesis',
                               _pick(game, feed.NEMESIS_MAIL, 'nemesis')))
    for npc in npcs.NPCS:
        if not story.satisfied(f'met:{npc.key}', game):
            continue
        if 'muscle' in npc.offers and street_world.fixer_jobs(game, npc):
            out.append(Message(f'muscle:{npc.key}:{day // 2}', npc.name, 'fixer',
                               _pick(game, feed.FIXER_MAIL, 'fixer' + npc.key),
                               do=f'deal {npc.key} muscle'))
        if 'work' in npc.offers and offers.BY_NPC_WORK.get(npc.key) \
                and not any(x.from_npc == npc.key for x in city.board):
            out.append(Message(f'work:{npc.key}:{day // 3}', npc.name, 'fixer',
                               feed.WORK_MAIL[0], do=f'deal {npc.key} work'))
    if game.debt.owed:
        out.append(Message(f'lender:{day}', game.debt.lender or 'a lender', 'lender',
                           _pick(game, feed.LENDER_MAIL, 'lender').format(amount=f'{game.debt.amount:,}'),
                           do='debt'))
    for thread in story.active_threads():
        short = story.waiting_on(thread, game)
        if short:
            out.append(Message(f'story:{thread.key}:{day}', thread.name, 'story',
                               feed.STORY_MAIL.format(short=short), do='story'))
    rank = int(city.pit.get('rank', 0))
    if 0 < rank < pit_content.TOP:
        nxt = pit_content.BY_RUNG[rank + 1].name
        out.append(Message(f'pit:{rank}:{day // 2}', 'the pit', 'pit',
                           feed.PIT_MAIL[0].format(rank=rank, next=nxt), do='pit'))
    for fac, amount in city.bounties.items():
        if amount and fac in factions.BY_KEY:
            out.append(Message(f'bounty:{fac}:{day}', 'unsigned', 'bounty',
                               feed.BOUNTY_MAIL[0].format(faction=factions.BY_KEY[fac].short),
                               do='rep'))
    for key in city.watches:
        hit = _find_on_shelves(game, key)
        if hit:
            district, price, kind = hit[0]
            out.append(Message(f'watch:{key}:{day}', 'your deck', 'watch',
                               feed.WATCH_MAIL.format(item=_name(key), district=district, price=f'{price:,}'),
                               do=f'walk {_district_key(district)}'))
    ad = ad_for(game)
    out.append(Message(f'ad:{ad.key}:{day}', f'sponsored, by {ad.sponsor}', 'ad', ad.text))
    return out


def unread(game) -> list[Message]:
    seen = set(game.city.mail_read)
    return [m for m in messages(game) if m.id not in seen]


def mark_read(game, ids) -> None:
    read = list(game.city.mail_read)
    for i in ids:
        if i not in read:
            read.append(i)
    game.city.mail_read = read[-MAIL_READ_CAP:]


# --------------------------------------------------------------------------
# search and watch
# --------------------------------------------------------------------------


def lookup(query: str):
    """(kind, item) from any catalogue by key, name, prefix or substring."""
    q = query.strip().lower()
    if not q:
        return None
    for kind, table in CATALOGUES:
        if q in table:
            return kind, table[q]
    for kind, table in CATALOGUES:
        for item in table.values():
            if item.name.lower() == q:
                return kind, item
    for kind, table in CATALOGUES:
        for item in table.values():
            if item.name.lower().startswith(q) or item.key.startswith(q):
                return kind, item
    for kind, table in CATALOGUES:
        for item in table.values():
            if q in item.name.lower():
                return kind, item
    return None


def _name(key: str) -> str:
    for _, table in CATALOGUES:
        if key in table:
            return table[key].name
    return key


def _district_key(name: str) -> str:
    return next((d.key for d in districts.DISTRICTS if d.name == name), name)


def _find_on_shelves(game, key: str) -> list[tuple[str, int, str]]:
    """Every shelf in the city that has it this cycle: (district, price, kind)."""
    out = []
    for dkey, listings in game.city.stock.items():
        for l in listings:
            if l.key == key and l.stock > 0 and not l.deep:
                out.append((districts.BY_KEY[dkey].name, int(l.price), l.kind))
    return out


def search(game, query: str) -> tuple[list[str], str]:
    """Lines to print, and a note about what the search cost."""
    hit = lookup(query)
    if hit is None:
        return [f'The net has no catalogue entry called {query!r}.'], ''
    kind, item = hit
    note = ''
    if kind == 'weapon' and item.loud:
        game.alias.add_heat('nightwatch', 1)
        note = feed.SEARCH_LOUD
    if getattr(item, 'unique', False):
        where = [s.district for s in spots.SPOTS
                 if any(f.item == item.key for f in getattr(s, 'finds', ()))]
        if where:
            return [feed.SEARCH_RELIC.format(district=districts.BY_KEY[where[0]].name)], note
        return [feed.SEARCH_RELIC_FAR], note
    shelves = _find_on_shelves(game, item.key)
    if not shelves:
        return [f'[accent]{item.name}[/]: ' + feed.SEARCH_NONE], note
    lines = [f'[accent]{item.name}[/], this cycle:']
    for district, price, k in sorted(shelves, key=lambda t: t[1]):
        lines.append(f'  {district}: [credit]{price:,}c[/] [dim]({k})[/]')
    return lines, note


def pings(game) -> list[str]:
    """Watch hits not yet said this cycle. Called after time moves."""
    out = []
    cycle = game.city.shift // DAY
    said = game.city.messaged
    for key in list(game.city.watches):
        hit = _find_on_shelves(game, key)
        if hit and said.get(f'watch:{key}') != cycle:
            said[f'watch:{key}'] = cycle
            district, price, _ = hit[0]
            out.append(f'[dim]Your deck:[/] {_name(key)} is on a shelf in '
                       f'{district}, [credit]{price:,}c[/].')
    return out


# --------------------------------------------------------------------------
# a line to the other runners
# --------------------------------------------------------------------------


def reply(game, rival) -> tuple[str, int]:
    """What they say back, and what it did to their opinion. Once a shift."""
    said = game.city.messaged
    if not rival.alive:
        return feed.NO_LINE.format(name=rival.name), 0
    if said.get(f'msg:{rival.key}') == game.city.shift:
        return feed.NO_REPLY_YET.format(name=rival.name), 0
    said[f'msg:{rival.key}'] = game.city.shift
    band = rival.bond if rival.bond in ('partner', 'nemesis') else rival.band
    pool = feed.REPLIES.get(band) or feed.REPLIES['neutral']
    stream = game.rng.fork('rivals', f'msg:{rival.key}:{game.city.shift}')
    line = stream.pick(pool)
    far = stream.pick([d.name for d in districts.DISTRICTS if d.key != game.city.where])
    line = line.format(district=far)
    delta = {'partner': 2, 'owes you': 1, 'friendly': 1, 'neutral': 0,
             'cold': 0, 'hostile': -1, 'will sell you': -1, 'nemesis': 0}[band]
    if delta:
        rival.adjust_disposition(delta)
    return line, delta
