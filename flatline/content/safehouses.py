"""Somewhere of your own, and what it means that somebody could find it.

You have been resting in safehouses since the first build and you have never
been able to have one. That is a gap with a specific shape: heat has always
been a multiplier on a danger roll, which is a real cost and an entirely
abstract one. There has been nothing in this city that being wanted could
physically take away from you.

**So a safehouse is a place to put things and a place that can be raided.**
The two halves are the same half. What makes storing anything a decision is
that the store has an address, and what makes the address matter is that
enough attention eventually finds it.

**Storing money is the interesting one.** Credits on you are exposed to a
collector, a mugging and every other thing in this city that takes cash out of
a room; credits in a floor cavity in the Ninth are exposed to precisely one
thing, and it does not happen often, and when it does it takes everything.
Neither is safe. They are different unsafe, which is the only kind of choice
this game is interested in.

**Security is what you are buying**, not space. The cheap ones hold as much as
the expensive ones and are found much sooner, because the difference between a
floor cavity and a bonded unit is not volume, it is how many people have to be
paid before somebody looks in it.
"""

from __future__ import annotations

from dataclasses import dataclass

#: How many separate things fit in one, whatever it costs. Deliberately flat:
#: what you pay for is not being found, and a capacity ladder on top of a
#: security ladder is two numbers doing one job.
CAPACITY = 8

#: Attention with the district's controller below which nobody comes looking,
#: however cheap the room is. Being unknown is the best security in the game
#: and it is free.
SAFE_BELOW = 30

#: Chance per shift of a raid, at maximum attention and zero security. Scaled
#: down by the property's own security and by how far past `SAFE_BELOW` you
#: actually are.
RAID_AT_WORST = 0.09

#: What a raid takes, as a fraction of what is stored, and the floor. A raid
#: that took one item would be a tax; a raid that took everything every time
#: would make storage pointless. It takes a lot, and it can take all of it.
RAID_TAKES = 0.6

#: Raids past this many burn the place. You do not get to keep a safehouse
#: that has been turned over twice: the second visit is somebody establishing
#: that they know where you live.
BURN_AFTER = 2


@dataclass(frozen=True, slots=True)
class Property:
    key: str
    name: str
    #: District, which must have a safehouse service. A place to hide in a
    #: district with nowhere to hide is a contradiction the map would notice.
    where: str
    price: int
    #: 0..100. Divides the raid chance. What you are actually buying.
    security: int
    blurb: str
    #: Second person, the first time you let yourself in.
    arrival: str


PROPERTIES: tuple[Property, ...] = (
    Property(
        'cavity', 'The floor cavity', 'ninth',
        price=3200, security=20,
        blurb='A room above a fryer, and a cavity under the boards that the '
              'landlord knows about and has decided not to.',
        arrival='It is warm, because of the fryer, and it smells of the '
                'fryer, and after about a week you stop noticing both and '
                'start finding the smell somewhere reassuring, which is when '
                'you understand you live here now.'),
    Property(
        'noodle', 'The room over the noodle bar', 'marrow',
        price=9800, security=55,
        blurb='Marrow keeps its own. Nobody has ever been found in this '
              'building, and several people have been looked for.',
        arrival='Somebody has left a key, a list of four rules, and a kettle. '
                'The rules are about the stairwell rather than about you, and '
                'the fourth one has been added recently in a different hand.'),
    Property(
        'container', 'The bonded container', 'freeport',
        price=14500, security=70,
        blurb='A unit on the dock with a docket, a serial number, and a crew '
              'who have collectively decided that the paperwork is correct.',
        arrival='The crew do not ask what is in it. They ask whether you want '
                'it on the manifest as machine parts or as personal effects, '
                'and they wait, and they are clearly hoping for the funnier '
                'of the two.'),
    Property(
        'flat', 'The flat in the stack', 'terraces',
        price=7400, security=45,
        blurb='Eleven thousand people come home through this stairwell every '
              'evening and not one of them has ever heard of you.',
        arrival='The neighbours establish, over about three days and entirely '
                'without asking, that you work shifts, that you are quiet, '
                'and that you are not to be involved in the thing about the '
                'parking. You are then left completely alone, for years, if '
                'you want it.'),
)

BY_KEY: dict[str, Property] = {p.key: p for p in PROPERTIES}


def here(district: str) -> list[Property]:
    return [p for p in PROPERTIES if p.where == district]


def raid_chance(security: int, attention: float) -> float:
    """How likely somebody turns the place over this shift.

    Zero below `SAFE_BELOW`, because being unknown is the best security there
    is and nothing should be able to sell you a substitute for it.
    """
    if attention < SAFE_BELOW:
        return 0.0
    heat = (attention - SAFE_BELOW) / max(1.0, 100.0 - SAFE_BELOW)
    return RAID_AT_WORST * heat * (1.0 - min(0.9, security / 100.0))


#: What it looks like when they come. Picked from, and the first one is not
#: about violence, because the ordinary version of this is administrative.
RAIDS = (
    'The door is not broken. It is open, and it was opened with a key, and '
    'the landlord is not answering and will not be answering again.',
    'They have been thorough and they have been tidy, which is the part that '
    'tells you it was not opportunists. Somebody had a list.',
    'A neighbour tells you about it before you get to the door. They are '
    'apologetic in the specific way of somebody who watched and did nothing '
    'and has decided you would rather hear it from them.',
)

#: The second visit, which is the one that ends it.
BURNED = (
    'They come back, which is the entire message. There is nothing left to '
    'take and they take the time to establish that. Whatever this place was, '
    'it is now an address that somebody keeps in a file.'
)

#: Said when nothing was in it. Still not free: they know where it is now.
EMPTY_RAID = (
    'They find nothing, because there was nothing, and they are not '
    'disappointed. Knowing where it is was most of what they came for.'
)
