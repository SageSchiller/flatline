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
    Weapon('cleaver', 'Cleaver', 3, False, 900, 1,
           'It came off a meat bench and it has not forgotten. Quiet, cheap, '
           'and entirely without pretension: it does one thing, close up, and '
           'the one thing is not in doubt.',
           'There is no elegant way to carry a cleaver, and no way at all to '
           'carry it that the people who see you carrying it will forget.'),
    Weapon('scattergun', 'Scattergun', 4, True, 2400, 2,
           'Short, ugly, and cut down further than the law that already '
           'banned it. It does not ask which of the four of them you meant. '
           'At a doorway\'s range, which is the only range the street has, '
           'that is the whole point.',
           'Loud, and it does not care who is behind them. Every fight it is '
           'drawn in is a Nightwatch matter, and the fight after it is with '
           'whoever was standing behind the people you meant.',
           rider='spread'),
    Weapon('monowire', 'Monowire', 3, False, 4800, 3,
           'A metre of monofilament on a spool in your palm, invisible edge '
           'on, and it keeps them at the far end of the metre, which on the '
           'street is a wall nobody can cross. Quiet, in the sense that it '
           'makes almost no sound; not quiet in any sense that matters to '
           'the people who know what the sound is.',
           'It is illegal in a way that a knife is not, and the spool leaves '
           'a signature on your palm that a clinic can read. It also, '
           'occasionally, takes a fingertip that was yours.',
           rider='reach'),
    Weapon('wolvers', 'Wolvers', 3, False, 0, 2,
           'Not carried: fitted. Four ceramic blades that live in the back '
           'of the forearm until they do not, and then live in whoever is '
           'nearest. There is no drawing them and no dropping them and no '
           'walking into a room without them.',
           'They are always there, which is the point and the problem: you '
           'cannot put them down, and a scanner sees them from across a '
           'lobby.'),
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
#: Weapon keys that are fitted, not carried: granted by chrome, never on a
#: fence's shelf, never dropped. Maps the chrome that grants it -> the
#: weapon key.
CHROME_WEAPONS: dict[str, str] = {'wolvers': 'wolvers'}


def carriable() -> list:
    """What a fence can stock: everything with a price."""
    return [w for w in WEAPONS if w.price > 0]


def granted(installed) -> Weapon | None:
    """A weapon fitted rather than carried, if any is installed."""
    for ware_key, weapon_key in CHROME_WEAPONS.items():
        if ware_key in installed:
            return BY_KEY[weapon_key]
    return None


#: Riders the engine special-cases. `stun`: a landed strike halves their
#: next hit. `smartlink`: needs neural chrome or it hits for less. `spread`:
#: a hit reaches more than one while they are still bunched. `reach`: a
#: landed strike keeps them off, and they do not hit back that round.
RIDERS: frozenset[str] = frozenset({'stun', 'smartlink', 'spread', 'reach'})
