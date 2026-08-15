"""Markets: what is in stock where, and what it costs you specifically.

Stock is per district and rotates on a cycle, so "the Glasshouse has a Nullsuit
this week" is a reason to travel and a reason to hurry. A district's `max_tier`
gates what can ever appear there, which is what makes the Ninth Ward cheap and
useless for anything serious.

Price is never a single number. It is the list price times the district, times
what the controlling faction thinks of you, times what your Dissonance does to
a shopkeeper's willingness to round down. Two players can stand in the same
shop and be quoted different figures, and the game will show them why.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..content import cyberware, dissonance, districts, factions
from ..content import hardware, programs
from ..content import shifts
from ..rng import Stream

#: Shifts between stock rotations.
REFRESH = 6

#: Categories a market always carries at least one of, at the cheapest tier it
#: stocks. Rotation is a reason to travel and a reason to hurry, which is what
#: makes it good, and it is only good for things a player can do without.
#:
#: A payload is not one of those. Four of the six objectives cannot be
#: finished without one, nine of the ten origins ship without one, and the
#: shelves carried one in about three worlds in five. The rest of the time a
#: new character's first contract was unfinishable for a reason nobody had
#: mentioned, findable only by walking to another district and looking again.
#: A breaker is on the list for the same reason at one remove: without one you
#: cannot open the door the payload was for.
STAPLES = ('payload', 'breaker')

#: What each service sells.
STOCK_KINDS = {
    'market': ('program', 'component'),
    'clinic': ('ware',),
    'workshop': ('component',),
    'fence': ('program', 'ware'),
}


@dataclass(slots=True)
class Listing:
    kind: str        # 'program' | 'ware' | 'component'
    key: str
    price: int       # list price before the buyer's own modifiers
    stock: int = 1
    #: Sold out of the back of a clinic to people the front of the clinic can
    #: no longer help. Only visible above `dissonance.DEEP_CLINIC_BAND`.
    deep: bool = False

    def to_dict(self) -> dict:
        out = {'kind': self.kind, 'key': self.key,
               'price': self.price, 'stock': self.stock}
        if self.deep:
            out['deep'] = True
        return out

    @classmethod
    def from_dict(cls, d: dict) -> Listing:
        return cls(kind=d['kind'], key=d['key'], price=int(d['price']),
                   stock=int(d.get('stock', 1)), deep=bool(d.get('deep')))


def _catalogue(kind: str):
    if kind == 'program':
        return [(p.key, p.tier, p.price) for p in programs.PROGRAMS]
    if kind == 'ware':
        return [(w.key, w.tier, w.price) for w in cyberware.WARE]
    # Components priced at zero are the "nothing fitted" options and must
    # never appear as merchandise.
    return [(c.key, c.tier, c.price) for c in hardware.COMPONENTS if c.price > 0]


def restock(rng: Stream, district_key: str, shift: int) -> list[Listing]:
    """Roll this district's inventory for the current cycle."""
    district = districts.BY_KEY[district_key]
    out: list[Listing] = []
    seen: set[tuple[str, str]] = set()

    for service in district.services:
        for kind in STOCK_KINDS.get(service, ()):
            ceiling = district.max_tier
            if kind == 'ware':
                # Restricted chrome is never sold over a counter. The only
                # route to a tier-3 implant is the back room, and the back
                # room only opens to somebody already far enough gone: that
                # is the payoff for the whole Dissonance arc, and it stops
                # working the moment the same pieces appear on the shelf.
                ceiling = min(ceiling, 2)
            pool = [(k, t, p) for k, t, p in _catalogue(kind)
                    if t <= ceiling]
            if not pool:
                continue
            # A fence carries less and stranger stock than a shop.
            count = rng.int(2, 4) if service == 'fence' else rng.int(3, 6)
            for _ in range(count):
                key, tier, price = rng.pick(pool)
                if (kind, key) in seen:
                    continue
                seen.add((kind, key))
                markup = district.price_mult
                if service == 'fence':
                    # Stolen goods are cheaper and sometimes only one of them.
                    markup *= 0.72
                out.append(Listing(kind=kind, key=key,
                                   price=max(1, int(round(price * markup))),
                                   stock=1 if service == 'fence' else rng.int(1, 3)))

    # The staples, if the roll above did not happen to produce them. Only in a
    # market: a fence deals in what fell off something, and what fell off
    # something is not a reliable supply of anything.
    if 'market' in district.services:
        for category in STAPLES:
            pool = [p for p in programs.by_category(category)
                    if p.tier <= district.max_tier]
            if not pool:
                continue
            # The cheapest thing that does the job, and specifically that one
            # rather than whatever payload the roll happened to produce. A
            # guaranteed line of stock should be the floor of the market
            # rather than a shortcut past it, so the good programs stay
            # something you go looking for; and a four thousand credit payload
            # on the shelf is not stock as far as somebody holding seven
            # hundred is concerned.
            basic = min(pool, key=lambda p: (p.tier, p.price))
            if ('program', basic.key) in seen:
                continue
            seen.add(('program', basic.key))
            out.append(Listing(
                kind='program', key=basic.key,
                price=max(1, int(round(basic.price * district.price_mult))),
                stock=1))

    # The back of the clinic. Restricted chrome, at a discount, sold to people
    # the front of the clinic has stopped being able to help. Generated for
    # every clinic district regardless of the buyer, because stock is a
    # property of the world; whether it is *visible* is a property of you.
    if 'clinic' in district.services:
        deep_pool = [(w.key, w.price) for w in cyberware.WARE if w.tier >= 3]
        for key, price in rng.sample(deep_pool, min(3, len(deep_pool))):
            out.append(Listing(
                kind='ware', key=key,
                price=max(1, int(round(price * district.price_mult
                                       * dissonance.DEEP_CLINIC_DISCOUNT))),
                stock=1, deep=True))
    return out


def quote(listing: Listing, district_key: str, alias, drift: int,
          price_mult: float = 1.0,
          phase: str = 'morning') -> tuple[int, list[tuple[str, float]]]:
    """What this costs *you*, itemised.

    Returns the final price and the list of multipliers that produced it, so
    the shop can show its working the same way a check does under D14.
    """
    district = districts.BY_KEY[district_key]
    terms: list[tuple[str, float]] = []
    total = float(listing.price)

    when = shifts.phase(phase)
    if when.price != 1.0:
        terms.append((f'{when.name.lower()} rates', when.price))
        total *= when.price

    rep = alias.reputation(district.controller)
    if rep:
        # Warm standing is a discount, hostility is a surcharge.
        mult = 1.0 - (rep / 100.0) * 0.22
        terms.append((f'{factions.BY_KEY[district.controller].short} standing', mult))
        total *= mult

    band = cyberware.band(drift)[0]
    if band >= 50:
        mult = 1.0 + (band / 100.0) * 0.35
        terms.append(('what you look like', mult))
        total *= mult

    if price_mult != 1.0:
        terms.append(('your gear', price_mult))
        total *= price_mult

    heat = alias.attention(district.controller)
    if heat >= 45:
        mult = 1.0 + (heat / 100.0) * 0.4
        terms.append(('their attention on you', mult))
        total *= mult

    return max(1, int(round(total))), terms


def sale_value(kind: str, key: str) -> int:
    """What a fence gives you for something. Deliberately punishing: gear is
    for using, not for arbitrage."""
    table = {'program': programs.BY_KEY, 'ware': cyberware.BY_KEY,
             'component': hardware.BY_KEY}
    item = table[kind].get(key)
    return int(getattr(item, 'price', 0) * 0.35) if item else 0


def data_price(rng: Stream, value: int, alias, buyer: str) -> tuple[int, float]:
    """What somebody pays for stolen data, and the rate they paid at.

    Not the asset's nominal value: that is what it is worth, and what you get
    is what somebody will pay today, which is less and depends on who you are.
    A trusted runner clears close to three quarters; a stranger clears under
    half, and finds out that the difference between the two is the entire
    argument for having a reputation.
    """
    rep = alias.reputation(buyer)
    mult = 0.45 + (rep / 100.0) * 0.28
    mult *= rng.spread(100, 0.12) / 100.0
    return max(1, int(round(value * mult))), mult
