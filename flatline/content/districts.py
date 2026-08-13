"""Six districts. Where you are changes what you can buy and who will meet you.

Districts are deliberately few and strongly characterised. Six places a player
can hold in their head, each with one clear reason to go there and one clear
reason not to, beats twenty interchangeable ones.

Travel costs a shift, which is the whole economy of the city layer: everything
you do is priced in time, and the contract board does not wait.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: What a location lets you do. The `travel` and `market` commands read these.
SERVICES = ('market', 'clinic', 'fixer', 'safehouse', 'workshop', 'fence')


@dataclass(frozen=True, slots=True)
class District:
    key: str
    name: str
    controller: str            # faction key
    blurb: str
    #: Second-person scene-setting, printed on arrival. Two sentences.
    arrival: str
    services: tuple[str, ...]
    #: 0..100. High security means Nightwatch presence and worse outcomes if
    #: you are carrying heat when you arrive.
    security: int
    #: Multiplies market prices here.
    price_mult: float
    #: Stock quality: the highest item tier this district's market carries.
    max_tier: int
    #: Districts reachable in one shift. Symmetric, checked by `validate.py`.
    neighbours: tuple[str, ...] = ()
    #: Factions with a presence beyond the controller. Affects who notices you.
    presence: tuple[str, ...] = ()


DISTRICTS: tuple[District, ...] = (
    District(
        'ninth', 'The Ninth Ward', 'sixes',
        'Low, wet, and cheap. Everything is for sale and most of it works.',
        'The Ninth smells like standing water and fryer oil. Somebody two '
        'floors up is testing a generator, and nobody in the street has looked '
        'at you yet, which in the Ninth is a decision rather than an accident.',
        services=('market', 'fence', 'workshop', 'safehouse'),
        security=25, price_mult=0.85, max_tier=1,
        neighbours=('marrow', 'freeport'),
        presence=('carrion', 'fixers'),
    ),
    District(
        'marrow', 'Marrow', 'fixers',
        'Neutral ground by long agreement. Everybody works here and nobody '
        'starts anything here.',
        'Marrow at shift change is a single continuous conversation held by '
        'four thousand people who all know better than to raise their voices. '
        'The Switchboard runs out of a noodle bar with no name and three '
        'landlines.',
        services=('market', 'fixer', 'safehouse', 'fence'),
        security=40, price_mult=1.0, max_tier=2,
        neighbours=('ninth', 'vertical', 'glasshouse', 'freeport'),
        presence=('sixes', 'freeport', 'nightwatch'),
    ),
    District(
        'vertical', 'The Vertical', 'kagawa',
        'Kagawa\'s spine. Ninety floors of logistics, and a lobby that logs '
        'your gait.',
        'The Vertical is climate-controlled to a degree that reads as an '
        'accusation. Every surface is clean, every door is on a schedule, and '
        'the building has already decided how long you are allowed to stand '
        'still.',
        services=('market', 'clinic'),
        security=80, price_mult=1.35, max_tier=3,
        neighbours=('marrow', 'green'),
        presence=('nightwatch',),
    ),
    District(
        'green', 'Aoyama Green', 'aoyama',
        'Campus, clinics, and the best chrome in the city at the worst prices.',
        'Aoyama Green is landscaped within an inch of its life and staffed by '
        'people who all look like they slept well. The clinics here will put '
        'anything in you that you can pay for, and their aftercare is genuinely '
        'excellent, which is how they keep the rest of it quiet.',
        services=('clinic', 'market'),
        security=70, price_mult=1.25, max_tier=3,
        neighbours=('vertical', 'glasshouse'),
        presence=('nightwatch',),
    ),
    District(
        'glasshouse', 'The Glasshouse', 'sendai',
        'Sendai\'s district. Decks, interfaces, and everything between a '
        'nervous system and a network.',
        'The Glasshouse is lit like an operating theatre and about as warm. '
        'Sendai does not have shops here so much as demonstrations, and the '
        'staff talk to your deck rather than to you.',
        services=('market', 'workshop', 'clinic'),
        security=65, price_mult=1.15, max_tier=3,
        neighbours=('marrow', 'green', 'freeport'),
        presence=('nightwatch', 'freeport'),
    ),
    District(
        'freeport', 'Freeport', 'freeport',
        'The docks, run by the people who work them. Open hardware, grey '
        'market, no questions and no cover either.',
        'Freeport does not have a skyline, it has cranes. There is a noticeboard '
        'by the west gate with actual paper on it, and everything sold past it '
        'is either community-printed or fell off something.',
        services=('market', 'workshop', 'fence', 'safehouse', 'fixer'),
        security=30, price_mult=0.92, max_tier=2,
        neighbours=('ninth', 'marrow', 'glasshouse'),
        presence=('carrion', 'fixers', 'sixes'),
    ),
)

BY_KEY: dict[str, District] = {d.key: d for d in DISTRICTS}
DISTRICT_KEYS: tuple[str, ...] = tuple(BY_KEY)

#: Where a new character wakes up. Marrow because it is neutral, has a fixer,
#: and touches four of the six other districts.
START = 'marrow'


def with_service(service: str) -> list[District]:
    return [d for d in DISTRICTS if service in d.services]
