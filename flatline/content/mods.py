"""Work done to a specific unit, at a bench, that nobody sells.

The obvious crafting system is a discount on the market with extra steps:
spend materials, receive a catalogue item, and every price in the shop means
slightly less than it did. This is not that. Nothing here produces an item.
Everything here changes one you already own, permanently, in a direction the
market does not stock.

**Every modification is a trade with a named cost.** One axis goes up and
another goes down, on the same component, and `validate.py` weighs both sides
and rejects anything that comes out ahead. That is the same rule the drugs are
written under and for the same reason: a change that was simply better would
not be a decision, it would be an upgrade you do to everything once.

**It lands on the unit, not on you.** A tuned cooling loop is a tuned cooling
loop; sell it and the work goes with it, because the work was done to the
metal. That is also why this lives on deck components rather than on programs:
a component sits in exactly one slot and there is exactly one of it, so "your
cooling unit" is unambiguous in a way "your Crowbar" is not when you own two.

**Scrap comes from what you already throw away.** Fitting a component puts the
old one in the bag, and the bag fills up over a campaign with things nobody
will buy at a price worth the walk. Breaking those down is what pays for this,
which means the input is a stock the player has been generating for hours
without noticing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: Modifications one component can carry. Two, so the second choice is made
#: against the first rather than in addition to it.
MAX_PER_COMPONENT = 2

#: What breaking something down returns, as a fraction of list price, in
#: scrap. Deliberately poor: this is a use for things that are otherwise
#: worthless, not a way to convert money into a different currency.
SALVAGE_RATE = 0.22

#: A destroyed component is worth this much of its scrap value. It is still
#: metal.
BROKEN_RATE = 0.5

#: Shifts a modification takes. It is bench work.
BENCH_SHIFTS = 1


@dataclass(frozen=True, slots=True)
class Mod:
    key: str
    name: str
    #: Which component slots this can be done to.
    slots: tuple[str, ...]
    #: One line, in the fiction, as the person doing it would put it.
    blurb: str
    #: What improves. An effects block, merged into the component's own.
    gives: dict
    #: What it costs, in the same vocabulary. Never empty, and never lighter
    #: than `gives`.
    takes: dict
    scrap: int
    price: int
    #: What the work looks like, printed once when it is done.
    bench: str


MODS: tuple[Mod, ...] = (
    Mod(
        'honed', 'Honed timings',
        ('cpu',),
        'Clocks pushed past where the documentation stops, and a fan that '
        'now has an opinion about it.',
        gives={'tick_mult': 0.9},
        takes={'heat_cap': -2, 'noise_mult': 1.12},
        scrap=100, price=1800,
        bench='Two shifts of somebody with a probe and a strong view about '
              'what the manufacturer was frightened of. It comes back warmer '
              'than it went in and it will stay warmer.'),
    Mod(
        'padded', 'Padded rails',
        ('cpu', 'io'),
        'Signal conditioning on the bus, at the cost of everything having '
        'slightly further to go.',
        gives={'noise_mult': 0.85},
        takes={'tick_mult': 1.12, 'memory': -1},
        scrap=90, price=1400,
        bench='They line the rails with something they will not name and '
              'will not stop talking about. It is quieter. It is also, '
              'measurably, slower.'),
    Mod(
        'widened', 'Widened bank',
        ('memory',),
        'More room for programs, taken out of the part of the assembly that '
        'was keeping it cool.',
        gives={'memory': 2},
        takes={'heat_cap': -3},
        scrap=110, price=2100,
        bench='The bank comes out, gets more of itself, and goes back in with '
              'nowhere for the heat to go. The bench engineer says the word '
              '"fine" in a way that does not mean it.'),
    Mod(
        'shielded', 'Shielded housing',
        ('memory', 'masking', 'antenna'),
        'Wrapped against what a forensics team can read off the outside of '
        'it, which is more than anybody is comfortable with.',
        gives={'residue_mult': 0.85},
        takes={'heat_cap': -2, 'tick_mult': 1.08},
        scrap=130, price=2600,
        bench='It goes into a jacket that weighs more than the component '
              'does. Everything about the deck now takes a moment longer, '
              'and everything about the deck now says less afterwards.'),
    Mod(
        'ducted', 'Ducted loop',
        ('cooling',),
        'Real airflow, at the cost of a housing that now announces itself to '
        'anybody within about four metres.',
        gives={'heat_cap': 3},
        takes={'noise_mult': 1.15, 'residue_mult': 1.12},
        scrap=100, price=1900,
        bench='They cut a duct in it. The deck runs cold and sounds like a '
              'small industrial process, which in a quiet building is the '
              'entire problem with it.'),
    Mod(
        'damped', 'Damped mounts',
        ('cooling', 'masking'),
        'Everything mounted on rubber. Quiet, warm, and slightly out of true '
        'for the rest of its life.',
        gives={'noise_mult': 0.82},
        takes={'heat_cap': -3, 'trace_mult': 1.06},
        scrap=110, price=2300,
        bench='Every mount is replaced with something softer. The deck stops '
              'transmitting through the desk it is on, and stops shedding '
              'heat into it as well.'),
    Mod(
        'burned', 'Burned identifiers',
        ('masking', 'antenna'),
        'Every serial, watermark and firmware signature taken off, which is '
        'illegal, effective, and irreversible.',
        gives={'trace_mult': 0.9},
        takes={'repair_mult': 1.4, 'heat_mult': 1.1},
        scrap=140, price=3100,
        bench='They take the identifiers off with a tool that was not made '
              'for it. Nothing legitimate will ever service this component '
              'again, which they mention afterwards.'),
    Mod(
        'tuned', 'Tuned aerial',
        ('antenna',),
        'Reach, bought from the part of the budget that was paying for '
        'discretion.',
        gives={'legwork_bonus': 1, 'trace_mult': 0.94},
        takes={'noise_mult': 1.18, 'heat_cap': -1},
        scrap=90, price=1600,
        bench='The aerial comes back longer, in a way that is obvious from '
              'across a room, and hears a great deal more than it did.'),
    Mod(
        'stripped', 'Stripped chassis',
        ('cpu', 'memory', 'io', 'cooling', 'masking', 'antenna'),
        'Everything not load-bearing removed. Faster, lighter, and with '
        'nothing left between the working parts and the world.',
        gives={'tick_mult': 0.94, 'heat_cap': 1},
        takes={'repair_mult': 1.5, 'residue_mult': 1.12},
        scrap=80, price=900,
        bench='They take off the case, the brackets, two of the three fans '
              'and a plate that turns out to have been doing something. It '
              'is lighter. It is also, now, permanently open.'),
)

BY_KEY: dict[str, Mod] = {m.key: m for m in MODS}
MOD_KEYS: tuple[str, ...] = tuple(BY_KEY)


def for_slot(slot: str) -> list[Mod]:
    return [m for m in MODS if slot in m.slots]


def effects(applied) -> dict:
    """Everything a list of mod keys contributes, as one block."""
    from . import effects as fx
    parts = [BY_KEY[k].gives for k in applied if k in BY_KEY]
    parts += [BY_KEY[k].takes for k in applied if k in BY_KEY]
    return fx.merge(*parts) if parts else {}


def salvage_value(price: int, broken: bool = False) -> int:
    """Scrap from breaking something down. Poor on purpose."""
    value = int(price * SALVAGE_RATE)
    if broken:
        value = int(value * BROKEN_RATE)
    return max(1, value)


#: Said when there is nothing worth taking apart. The bench is not sentimental
#: and neither is the line.
NOTHING_TO_SALVAGE = (
    'You have nothing spare. Everything you own is either in the deck, in '
    'you, or worth more than what a bench would give you for the pieces.'
)
