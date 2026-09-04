"""Things you can carry on the street (D128).

Five of them, and one axis that matters: quiet or loud. A blade is quiet
and a gun is not, and the difference is who hears. `damage` is what a
landed strike adds on top of the skill; the skill is what lands it. None
of this is a technique and none of it comes into the net: a pistol in the
bag is a pistol in the bag, and the deck does not know it is there.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Weapon:
    key: str
    name: str
    #: Added to a landed strike.
    damage: int
    #: The law hears it. Every fight it is drawn in is a Nightwatch matter,
    #: whichever way the fight went.
    loud: bool
    price: int
    tier: int                      # 1 street, 2 professional, 3 restricted
    blurb: str
    #: The honest downside, in the fiction.
    drawback: str
    #: Engine special case by key, or ''.
    rider: str = ''


WEAPONS: tuple[Weapon, ...] = (
    Weapon('knuckles', 'Knuckledusters', 1, False, 240, 1,
           'Four rings and a bar, machined out of something that used to be '
           'a bearing race. They do not make you a fighter. They make the '
           'argument shorter.',
           'Nobody who sees them on your hand believes anything else you say '
           'that night.'),
    Weapon('blade', 'Blade', 2, False, 700, 1,
           'Twenty centimetres of something that holds an edge, in a sheath '
           'that does not print. Quiet, which on this street is most of what '
           'a weapon is for.',
           'It is a knife. Everything it can do to them it can do to you, and '
           'it does not care who is holding it.'),
    Weapon('baton', 'Shock baton', 2, False, 1500, 2,
           'Corporate crowd kit that fell off a corporate crowd. A hit puts '
           'their whole nervous system on hold for a breath, and a breath is '
           'a breath they are not hitting you in.',
           'It has a charge, and the charge has a light, and the light says '
           'exactly what you are carrying to anybody who looks.',
           rider='stun'),
    Weapon('pistol', 'Pistol', 4, True, 2800, 2,
           'Old, honest, and printed. It does what it does at any range you '
           'will ever be at. It is also the loudest thing that will happen on '
           'that street tonight, and the street has ears that report to the '
           'Nightwatch.',
           'Loud. Every fight it is drawn in is a Nightwatch matter, whichever '
           'way it went.'),
    Weapon('smartgun', 'Smartgun', 5, True, 6500, 3,
           'A pistol that knows where you are looking, through a neural link '
           'that it will also remember. Without something in the neural slot '
           'it is a heavy, expensive pistol that does not know you.',
           'Loud, and it logs. Every round it fires is a record, and the link '
           'that makes it accurate makes you legible.',
           rider='smartlink'),
)

BY_KEY: dict[str, Weapon] = {w.key: w for w in WEAPONS}

#: Riders the engine special-cases. `stun`: a landed strike halves their
#: next hit. `smartlink`: needs neural chrome fitted, or hits for less.
RIDERS: frozenset[str] = frozenset({'stun', 'smartlink'})
