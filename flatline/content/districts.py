"""The city. Where you are changes what you can buy and who will meet you.

Districts are deliberately few and strongly characterised. Nine places a player
can hold in their head, each with one clear reason to go there and one clear
reason not to, beats twenty interchangeable ones.

Every faction that holds ground has somewhere, which matters more than it
sounds: a Nightwatch precinct and a Carrion street are places the player can
choose to walk into, and choosing to walk into them is a different act from
reading about them on a reputation screen.

**The Terraces exist for tone rather than mechanics.** It is the one district
where nobody is in this business, and its whole job is to be the place the rest
of the city is happening to. A game about a city that does not care whether you
live needs somewhere that shows you what it is not caring about.

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
        neighbours=('marrow', 'freeport', 'terraces', 'shambles'),
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
        neighbours=('ninth', 'vertical', 'glasshouse', 'freeport', 'precinct'),
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
        neighbours=('marrow', 'green', 'terraces', 'precinct'),
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
        neighbours=('ninth', 'marrow', 'glasshouse', 'shambles'),
        presence=('carrion', 'fixers', 'sixes'),
    ),

    District(
        'precinct', 'The Precinct', 'nightwatch',
        'Contracted enforcement, run as a business, with a surplus counter '
        'nobody upstairs has audited in years.',
        'The Precinct is open-plan and lit at a level somebody costed. There '
        'is a public counter for filing complaints and a queue for it that '
        'has not moved since you arrived. Everybody here is on shift and '
        'nobody here is in a hurry.',
        services=('market', 'fence'),
        security=85, price_mult=0.9, max_tier=2,
        neighbours=('marrow', 'vertical'),
        presence=('kagawa',),
    ),
    District(
        'shambles', 'The Shambles', 'carrion',
        'Carrion territory. Cheap chrome, cheaper surgery, and nobody asks '
        'where anything came from because everybody already knows.',
        'The Shambles smells of solvent and something underneath the solvent. '
        'There are people on this street with more hardware than skin and '
        'they watch you the way a butcher watches a queue. Nothing here is '
        'expensive, and there is a reason for that.',
        services=('clinic', 'fence', 'workshop'),
        security=15, price_mult=0.7, max_tier=2,
        neighbours=('ninth', 'freeport'),
        presence=('sixes',),
    ),
    District(
        'terraces', 'The Terraces', 'kagawa',
        'Where the people who are not in this business live. Kagawa housing '
        'stacked over Kagawa farms, and about a third of the city in it.',
        'The Terraces at shift change is eleven thousand people coming home '
        'through a stairwell that smells of wet concrete and growing things. '
        'Somebody is arguing about a parking allocation. A child on the '
        'landing above is doing homework by the light of a vending machine. '
        'None of these people have ever heard of you and that is the nicest '
        'thing about the place.',
        services=('market', 'safehouse'),
        security=35, price_mult=0.95, max_tier=1,
        neighbours=('vertical', 'ninth'),
        presence=('nightwatch', 'sixes'),
    ),
)

BY_KEY: dict[str, District] = {d.key: d for d in DISTRICTS}
DISTRICT_KEYS: tuple[str, ...] = tuple(BY_KEY)

#: The city as a plain graph. Derived rather than authored, so it cannot drift
#: from the districts themselves, and shaped for `ui.spanning_tree` and
#: `ui.shortest_path` which are the two things that ever ask.
GRAPH: dict[str, list[str]] = {d.key: list(d.neighbours) for d in DISTRICTS}

#: Where a new character wakes up. Marrow because it is neutral, has a fixer,
#: and touches more of the city than anywhere else.
START = 'marrow'


def with_service(service: str) -> list[District]:
    return [d for d in DISTRICTS if service in d.services]


# --------------------------------------------------------------------------
# how a district is doing
# --------------------------------------------------------------------------

#: The game's pitch is that the city remembers. It has always been true in the
#: numbers: posture climbs when you rob somebody, heat accrues, bounties get
#: posted. None of it was ever visible standing in the street, which meant the
#: player had to read a reputation screen to find out that the world had
#: changed around them.
#:
#: These are that state, in the street, where it happened. Keyed to how far
#: the controlling faction's posture has moved from its own baseline, which is
#: the number that actually tracks "have you been hitting these people".
#: Below this much *under* baseline, somebody has stopped paying for security
#: here. Handled separately from the table below rather than as its lowest
#: band, because `_band` picks the highest threshold at or under the value and
#: a negative entry in an otherwise-positive table silently swallows the
#: entire neutral zone: at exactly baseline posture the district would report
#: itself as falling apart.
RELAXED_AT = -6.0
RELAXED = ('Something has gone out of this place since you were last here. '
           'Half the checkpoints are unstaffed and nobody has replaced the '
           'camera on the corner. Whoever was paying for all that has '
           'stopped.')

HARDENING: tuple[tuple[float, str], ...] = (
    (10.0,
     'There are more people in the doorways than there were, and they are '
     'wearing the same jacket as each other. Nobody is doing anything. That '
     'is the point of them.'),
    (20.0,
     'The district has tightened. Two of the through-routes you used to take '
     'are gated now, there is a scanner arch at the transit entrance that '
     'nobody is queueing for because everybody has learned the other way '
     'round, and the whole place has the atmosphere of somewhere that has '
     'recently had a meeting about you.'),
    (32.0,
     'This is not the district you started working in. There is a permanent '
     'presence on the walkways now, in numbers that cost real money, and the '
     'people who live here have adjusted their routes and their hours and '
     'their conversation. Nobody here knows it was you. That does not make it '
     'not you.'),
)

#: What being wanted here feels like from the pavement. Keyed to your own
#: attention score with whoever is watching this ground.
WANTED: tuple[tuple[float, str], ...] = (
    (20.0, ''),
    (35.0,
     'You get looked at twice on the way in. Once by somebody who was not '
     'sure, and once by the same person making sure.'),
    (55.0,
     'Somebody makes a call while you are still in the street, holding the '
     'handset the way you hold a handset when the person you are describing '
     'can see you.'),
    (75.0,
     'Two separate people have decided not to be near you, which they '
     'accomplish without once looking in your direction, and which is the '
     'single most professional thing you will see today.'),
)


def _band(table: tuple[tuple[float, str], ...], value: float) -> str:
    line = ''
    for threshold, text in table:
        if value >= threshold:
            line = text
    return line


def mood(district: District, posture: float, attention: float) -> list[str]:
    """How this district is right now, in one or two lines.

    Returns a list because the two halves are independent: a district can be
    hardened and not care about you, or unchanged and full of people who have
    your name. Both at once is a bad afternoon and reads as one.
    """
    out = []
    drift = posture - factions_posture(district.controller)
    if drift <= RELAXED_AT:
        out.append(RELAXED)
    else:
        hardening = _band(HARDENING, drift)
        if hardening:
            out.append(hardening)
    wanted = _band(WANTED, attention)
    if wanted:
        out.append(wanted)
    return out


def factions_posture(key: str) -> float:
    """The controlling faction's baseline, imported late to avoid a cycle."""
    from . import factions
    fac = factions.BY_KEY.get(key)
    return float(fac.posture) if fac else 0.0
