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

from ..content import cyberware, districts, factions, hardware, programs
from ..rng import Stream

#: Shifts between stock rotations.
REFRESH = 6

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

    def to_dict(self) -> dict:
        return {'kind': self.kind, 'key': self.key,
                'price': self.price, 'stock': self.stock}

    @classmethod
    def from_dict(cls, d: dict) -> Listing:
        return cls(kind=d['kind'], key=d['key'], price=int(d['price']),
                   stock=int(d.get('stock', 1)))


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
            pool = [(k, t, p) for k, t, p in _catalogue(kind)
                    if t <= district.max_tier]
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
    return out


def quote(listing: Listing, district_key: str, alias, dissonance: int,
          price_mult: float = 1.0) -> tuple[int, list[tuple[str, float]]]:
    """What this costs *you*, itemised.

    Returns the final price and the list of multipliers that produced it, so
    the shop can show its working the same way a check does under D14.
    """
    district = districts.BY_KEY[district_key]
    terms: list[tuple[str, float]] = []
    total = float(listing.price)

    rep = alias.reputation(district.controller)
    if rep:
        # Warm standing is a discount, hostility is a surcharge.
        mult = 1.0 - (rep / 100.0) * 0.22
        terms.append((f'{factions.BY_KEY[district.controller].short} standing', mult))
        total *= mult

    band = cyberware.band(dissonance)[0]
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


def data_price(rng: Stream, kind: str, value: int, alias,
               buyer: str) -> tuple[int, str]:
    """What a fixer pays for stolen data, and who is buying.

    Not the asset's nominal value: that is what it is worth, and what you get
    is what somebody will pay today, which is less and depends on who you are.
    """
    rep = alias.reputation(buyer)
    mult = 0.55 + (rep / 100.0) * 0.25
    mult *= rng.spread(100, 0.12) / 100.0
    return max(1, int(round(value * mult))), buyer
