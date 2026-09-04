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
from ..content import events, hardware
from ..content import street as street_content


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
#: How often each kind writes, in days (D138). Mail is news, not a status
#: board: a partner who writes every morning is somebody you stop reading,
#: and a pit that says your rank every morning is a rank you stop caring
#: about. The ad is the exception, because junk mail is daily by nature.
EVERY = {'partner': 3, 'nemesis': 3, 'fixer': 2, 'lender': 2, 'story': 2,
         'pit': 3, 'bounty': 2, 'ad': 1}
#: At most this many from the fixers at once, and this many in total: an
#: inbox with thirteen things in it is an inbox nobody reads.
FIXER_CAP = 2
MAIL_CAP = 8
#: Which kinds survive the cap, most important first.
PRIORITY = ('story', 'partner', 'nemesis', 'bounty', 'lender', 'pit',
            'fixer', 'watch', 'ad')
#: Shelves a search prints before it starts summarising: a common
#: program is on eleven of them, and eleven lines is not an answer.
SEARCH_SHOWN = 4


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
    general = [a for a in feed.ADS if a.when == 'any']
    # Even when something has read you, one morning in three is somebody
    # who has not (D138): a targeted ad every day is a targeted ad nobody
    # reads.
    if live and _pick(game, (True, True, False), 'ads' + salt):
        return _pick(game, live, 'ad' + salt)
    return _pick(game, general, 'ad' + salt)


# --------------------------------------------------------------------------
# mail
# --------------------------------------------------------------------------


def messages(game) -> list[Message]:
    from . import rivals as rival_world
    from . import street as street_world
    city, char, alias, story = game.city, game.char, game.alias, game.story
    day = _day(game)

    def every(kind: str) -> int:
        return day // EVERY.get(kind, 1)

    out: list[Message] = []
    here = city.district.name
    partner = rival_world.active_partner(city.rivals)
    if partner is not None:
        out.append(Message(f'partner:{partner.key}:{every("partner")}', partner.name, 'partner',
                           _pick(game, feed.PARTNER_MAIL, 'partner').format(district=here),
                           do=f'who {partner.name.lower()}'))
    for r in city.rivals:
        if r.alive and r.bond == 'nemesis':
            out.append(Message(f'nemesis:{r.key}:{every("nemesis")}', r.name, 'nemesis',
                               _pick(game, feed.NEMESIS_MAIL, 'nemesis')))
    # The fixers, two at most, and the same two until one of them has
    # nothing (D138): every fixer in the city writing every other day is
    # seven messages nobody reads.
    fixers: list[Message] = []
    for npc in npcs.NPCS:
        if not story.satisfied(f'met:{npc.key}', game):
            continue
        if 'muscle' in npc.offers and street_world.fixer_jobs(game, npc):
            fixers.append(Message(f'muscle:{npc.key}:{every("fixer")}', npc.name,
                                  'fixer',
                                  _pick(game, feed.FIXER_MAIL, 'fixer' + npc.key),
                                  do=f'deal {npc.key} muscle'))
        if 'work' in npc.offers and offers.BY_NPC_WORK.get(npc.key) \
                and not any(x.from_npc == npc.key for x in city.board):
            fixers.append(Message(f'work:{npc.key}:{every("fixer")}', npc.name,
                                  'fixer', feed.WORK_MAIL[0],
                                  do=f'deal {npc.key} work'))
    if fixers:
        # The rotation turns on the fixers' own cadence, not daily: a
        # different two every morning is two new messages every morning.
        start = every('fixer') % len(fixers)
        out.extend((fixers + fixers)[start:start + FIXER_CAP])
    if game.debt.owed:
        lender = factions.BY_KEY.get(game.debt.lender)
        out.append(Message(f'lender:{every("lender")}', lender.short if lender else 'a lender', 'lender',
                           _pick(game, feed.LENDER_MAIL, 'lender').format(amount=f'{game.debt.amount:,}'),
                           do='debt'))
    for thread in story.active_threads():
        short = story.waiting_on(thread, game)
        if short:
            out.append(Message(f'story:{thread.key}:{every("story")}', thread.name, 'story',
                               feed.STORY_MAIL.format(short=short), do='story'))
    rank = int(city.pit.get('rank', 0))
    if 0 < rank < pit_content.TOP:
        nxt = pit_content.BY_RUNG[rank + 1].name
        out.append(Message(f'pit:{rank}:{every("pit")}', 'the pit', 'pit',
                           feed.PIT_MAIL[0].format(rank=rank, next=nxt), do='pit'))
    for fac, amount in city.bounties.items():
        if amount and fac in factions.BY_KEY:
            out.append(Message(f'bounty:{fac}:{every("bounty")}', 'unsigned', 'bounty',
                               feed.BOUNTY_MAIL[0].format(faction=factions.BY_KEY[fac].short),
                               do='rep'))
    for key in city.watches:
        best = _best_shelf(game, key)
        if best:
            district, price, kind = best
            # The id carries the price the deck last called news, not the
            # day and not the current price (D138), so mail and the ping
            # agree about what is new: a watch on a thing that is always
            # in stock said the same thing every morning for sixty
            # mornings, and the inbox was never empty.
            told = int(city.messaged.get(f'watch:{key}', 0)) or price
            out.append(Message(f'watch:{key}:{told}', 'your deck', 'watch',
                               feed.WATCH_MAIL.format(item=_name(key), district=district, price=f'{price:,}'),
                               do=f'walk {_district_key(district)}'))
    ad = ad_for(game)
    out.append(Message(f'ad:{ad.key}:{day}', f'sponsored, by {ad.sponsor}', 'ad', ad.text))
    if len(out) > MAIL_CAP:
        out.sort(key=lambda m: PRIORITY.index(m.kind) if m.kind in PRIORITY
                 else len(PRIORITY))
        out = out[:MAIL_CAP]
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


#: Below this, a substring is not a search, it is a shrug: `search a`
#: used to answer confidently about Auspex (D138).
VAGUE = 3


def matches(query: str) -> list:
    """Everything a query could mean, best first: exact key, exact name,
    prefix, then substring. Empty when it means nothing."""
    q = query.strip().lower()
    if not q:
        return []
    exact, prefix, loose = [], [], []
    for kind, table in CATALOGUES:
        for item in table.values():
            name = item.name.lower()
            if q == item.key or q == name:
                exact.append((kind, item))
            elif name.startswith(q) or item.key.startswith(q):
                prefix.append((kind, item))
            elif len(q) >= VAGUE and q in name:
                loose.append((kind, item))
    return exact or prefix or loose


def lookup(query: str):
    """(kind, item) when a query means one thing, else None."""
    hits = matches(query)
    return hits[0] if len(hits) == 1 else None


def ambiguous(query: str) -> list:
    """The candidates when a query means more than one thing."""
    hits = matches(query)
    return hits if len(hits) > 1 else []


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
        several = ambiguous(query)
        if several:
            names = ', '.join(i.name for _, i in several[:8])
            more = f', and {len(several) - 8} more' if len(several) > 8 else ''
            return [f'{query!r} could be: {names}{more}. Ask for one of them.'], ''
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
    ordered = sorted(shelves, key=lambda t: t[1])
    for district, price, k in ordered[:SEARCH_SHOWN]:
        lines.append(f'  {district}: [credit]{price:,}c[/] [dim]({k})[/]')
    if len(ordered) > SEARCH_SHOWN:
        rest = len(ordered) - SEARCH_SHOWN
        lines.append(f'  [dim]and {rest} more shel{"f" if rest == 1 else "ves"}, '
                     f'dearer, up to {ordered[-1][1]:,}c in {ordered[-1][0]}.[/]')
    return lines, note


def _best_shelf(game, key: str):
    """The cheapest shelf holding it, or None."""
    hits = _find_on_shelves(game, key)
    return min(hits, key=lambda t: t[1]) if hits else None


def pings(game) -> list[str]:
    """What a watch has to say, which is only ever news (D138): a thing
    landing where it was not, or landing cheaper than it was. A watch on
    something permanently in stock used to say so every single cycle."""
    out = []
    said = game.city.messaged
    for key in list(game.city.watches):
        best = _best_shelf(game, key)
        mark = f'watch:{key}'
        was = int(said.get(mark, 0))
        if best is None:
            # Gone. The next time it lands is news again.
            if was:
                said[mark] = 0
            continue
        district, price, _ = best
        if was and price >= was:
            continue
        said[mark] = price
        said['watch_hits'] = int(said.get('watch_hits', 0)) + 1
        out.append(f'[dim]Your deck:[/] {_name(key)} '
                   + ('is on a shelf in' if not was else 'is cheaper in')
                   + f' {district}, [credit]{price:,}c[/].')
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


# --------------------------------------------------------------------------
# the deck as a thing (D136): condition, reach, and what it can hear
# --------------------------------------------------------------------------

#: Slots the city uses. A deck with either destroyed is in pieces out here
#: too: no mail, no search, nothing to listen with.
CITY_SLOTS = ('cpu', 'io')
IN_PIECES = 'The deck is in pieces. `repair` at a workshop, then ask it things.'
#: Not `[static]`: a bracketed word is markup to the console.
STATIC = '[dim]<static>[/]'


def working(char) -> bool:
    return all(char.deck.working(slot) for slot in CITY_SLOTS)


def damaged(char) -> bool:
    """Working, but hurt: a cpu with a level of damage garbles a line."""
    return working(char) and char.deck.damage.get('cpu', 0) > 0


def reach(char) -> int:
    """How far the deck hears, in shifts of walking: the antenna\'s tier
    less one. A hardline-only deck hears the district it is in."""
    comp = char.deck.component('antenna')
    if comp is None or not char.deck.working('antenna'):
        return 0
    return max(0, comp.tier - 1)


def watch_capacity(char) -> int:
    """How many things the deck will watch for: memory, halved, two at least."""
    return max(2, char.deck.memory // 2)


def garble(game, text: str) -> str:
    """A damaged cpu loses words. Deterministic in the shift, so reading
    twice loses the same ones."""
    words = text.split()
    if len(words) < 6:
        return text
    stream = game.rng.fork('events', f'static:{game.city.shift}')
    n = max(1, len(words) // 6)
    for _ in range(n):
        i = stream.int(0, len(words) - 1)
        words[i] = STATIC
    return ' '.join(words)


def in_reach(game, district_key: str) -> bool:
    if district_key == game.city.where:
        return True
    return game.city.shifts_to(district_key) <= reach(game.char)


def sweep(game, district_key: str) -> list[str]:
    """What the deck reads off a district\'s air: how rough, who is
    watching, whether there is chrome to reach, and what is here to run."""
    from . import street as street_world
    city, alias, char = game.city, game.alias, game.char
    district = districts.BY_KEY[district_key]
    here = district_key == city.where
    out = []
    base = 100 - district.security
    mult = street_world.ROUGH_BY_PHASE.get(city.phase, 1.0)
    tonight = street_world.night(game)
    if tonight is not None:
        mult *= tonight.rough
    rough = max(0, min(100, int(base * mult)))
    word = next(w for floor, w in street_world.ROUGH_WORDS if rough >= floor)
    out.append(f'[accent]{district.name}[/], {city.phase}: the street is '
               f'[warn]{word}[/] [dim]({rough})[/]'
               + (f', and tonight: {tonight.name.lower()}' if tonight else '') + '.')
    controller = factions.BY_KEY.get(district.controller)
    watchers = [k for k in (district.controller, *district.presence)
                if k in factions.BY_KEY]
    looking = [(factions.BY_KEY[k].short, alias.attention(k))
               for k in watchers if alias.attention(k) >= 25]
    if looking:
        out.append('Looking for your name: '
                   + ', '.join(f'{name} [heat]({att})[/]' for name, att in looking) + '.')
    else:
        out.append('[dim]Nobody here has your name at the top of a list.[/]')
    kind = controller.kind if controller else ''
    chromed = kind in ('corp', 'law', 'broker')
    who = controller.short if controller else 'The people here'
    out.append(f'{who} carry chrome: [fg]jack[/] has something to reach in a '
               f'fight here.' if chromed else
               f'{who} mostly do not carry chrome: a fight here is hands '
               f'and steel, and [fg]jack[/] has nothing to reach.')
    if district.controller == 'nightwatch' or (tonight and tonight.key == 'sweep'):
        out.append('[heat]The Nightwatch is on the street. A gun here is heard '
                   'twice.[/]')
    local = [x for x in city.board if x.district == district_key and not x.taken]
    if local:
        out.append('Networks here, on the board: '
                   + ', '.join(f'[fg]{x.cid}[/] [dim]({factions.BY_KEY[x.target].short if x.target in factions.BY_KEY else x.target})[/]'
                               for x in local[:4]) + '.')
    else:
        out.append('[dim]Nothing on the board is here.[/]')
    people = [n.name for n in npcs.NPCS if n.where == district_key]
    if people:
        out.append('[dim]Keeps hours here: ' + ', '.join(people[:5]) + '.[/]')
    if not here:
        out.append(f'[dim]Read at {city.shifts_to(district_key)} shift'
                   f'{"s" if city.shifts_to(district_key) != 1 else ""}\' remove, '
                   f'on the antenna.[/]')
    return out


def route(game, target_key: str) -> list[tuple[str, str, str, str]]:
    """The walk, planned: (district, phase on arrival, the street then, who
    is looking). One row per hop."""
    from . import street as street_world
    from .city import SHIFT_NAMES, SHIFTS_PER_DAY
    city, alias = game.city, game.alias
    path = city.route(target_key)
    rows = []
    for i, key in enumerate(path, 1):
        shift = city.shift + i
        phase = SHIFT_NAMES[shift % SHIFTS_PER_DAY]
        district = districts.BY_KEY[key]
        base = 100 - district.security
        mult = street_world.ROUGH_BY_PHASE.get(phase, 1.0)
        rough = max(0, min(100, int(base * mult)))
        word = next(w for floor, w in street_world.ROUGH_WORDS if rough >= floor)
        danger, who = city.danger(alias, key, flags=game.story.flags, riders=game.char.riders())
        looking = (f'{factions.BY_KEY[who].short} ({danger})' if who and danger >= 25 else '')
        rows.append((district.name, phase, word, looking))
    return rows


def listen(game, district_key: str) -> list[str]:
    """What the district is saying: the scene at this hour, the street\'s
    line, and any rumour going round it (the relics\' breadcrumbs)."""
    city = game.city
    out = []
    scene = districts.scene(district_key, city.phase)
    if scene:
        out.append(scene)
    line = districts.street_line(district_key, city.shift)
    if line:
        out.append(f'[dim]{line}[/]')
    sat = lambda rule: game.story.satisfied(rule, game)  # noqa: E731
    rumours = [e for e in events.eligible(district_key, city.phase, sat)
               if e.key.startswith('rumour_')]
    for e in rumours[:2]:
        out.append(f'[accent2]Going round:[/] {e.text}')
    if not out:
        out.append('[dim]Nothing but carrier.[/]')
    return out


def cheapest(game, kind: str):
    """The cheapest thing of a kind on any shelf: (name, price, district).

    What the deck is for, asked by the commands that would otherwise say
    "a fence sells them" while you are standing at a fence (D137).
    """
    best = None
    for dkey, listings in game.city.stock.items():
        for l in listings:
            if l.kind != kind or l.stock <= 0 or l.deep:
                continue
            if best is None or l.price < best[1]:
                best = (_name(l.key), int(l.price), districts.BY_KEY[dkey].name)
    return best
