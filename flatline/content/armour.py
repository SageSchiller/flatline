"""What you wear on the street (D131).

Armour is chrome, mostly (see `cyberware`: dermal weave, plating, bone
lacing, trauma plate), and chrome costs bandwidth and dissonance and a
clinic. This is the other kind: a jacket, a vest, a carrier, bought at a
fence or a market, worn over the skin rather than under it, and taken off
again. It adds to the chrome's number and the sum is capped, because past
a point nobody is wearing armour any more, they are wearing a room.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Armour:
    key: str
    name: str
    #: Taken off every hit that reaches you in a fight, with the chrome's.
    armour: int
    price: int
    tier: int                      # 1 street, 2 professional, 3 restricted
    blurb: str
    #: The honest downside, in the fiction.
    drawback: str


ARMOUR: tuple[Armour, ...] = (
    Armour('jacket', 'Ballistic jacket', 1, 600, 1,
           'A jacket with a lining that is not lining. It turns a blade '
           'that was not committed and takes the worst out of a boot, and '
           'it looks, to anybody who knows, like exactly what it is.',
           'It is hot, it does not breathe, and it says to every doorway '
           'you walk into that you were expecting the doorway.'),
    Armour('vest', 'Riot vest', 2, 2200, 2,
           'Nightwatch surplus, which is to say Nightwatch issue that fell '
           'off a Nightwatch. Plates front and back, and it does not '
           'pretend to be anything: you are wearing a vest, and the vest is '
           'why you are still standing.',
           'There is no hiding it. A lobby, a bar, a queue: everyone in '
           'them knows you came dressed for a fight, and some of them will '
           'want to know why.'),
    Armour('carrier', 'Plate carrier', 3, 5200, 3,
           'The military shape: a carrier and the plates that go in it, '
           'ceramic and heavy and rated for things the street does not '
           'have. What the street does have bounces.',
           'Heavy. It slows the stairs and it slows the chair, and it makes '
           'you the most interesting person on any street you are on.'),
)

BY_KEY: dict[str, Armour] = {a.key: a for a in ARMOUR}

#: The most armour a body can wear, worn and fitted together.
CAP = 4
