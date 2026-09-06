"""The five attributes and everything derived from them.

Five rather than twelve because five numbers fit in a player's head and the
interesting differentiation is supposed to live in skills, chrome, and the
deck. An attribute here is a broad disposition; a skill is a learned trade.

The derived formulas are in this file rather than on the character class so
that there is exactly one place to look when a number seems wrong, and so
`validate.py` can check the whole set against a range of inputs.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Creation and progression bounds. Nine, not ten, because a maxed attribute
#: at creation would make the first ten hours of the game a straight line.
ATTR_MIN = 1
ATTR_MAX = 9

#: Points to distribute at creation, on top of the origin's shape.
CREATION_POINTS = 6


@dataclass(frozen=True, slots=True)
class Attribute:
    key: str
    name: str
    short: str
    governs: str
    #: What it feels like to have this one low. Shown at creation, because a
    #: player choosing between five nouns needs to know what they are buying
    #: out of, not just what they are buying.
    failure: str
    #: Three or four words beside the number on the sheet (D182). A sheet
    #: that prints five nouns and five numbers and nothing else is a form
    #: for somebody who already knows the game; this is for everybody else.
    gloss: str


ATTRIBUTES: tuple[Attribute, ...] = (
    Attribute(
        'logic', 'Logic', 'LOG',
        'Exploit construction, cryptanalysis, understanding what you are looking at.',
        'You cannot break what you do not understand. Services read as noise.',
        'breaking in, and reading what you see'),
    Attribute(
        'reflex', 'Reflex', 'REF',
        'Free actions banked as you work, slipping a lock-on, reacting to ICE '
        'that has already noticed you.',
        'Everything happens to you before you happen to it.',
        'speed, and free actions'),
    Attribute(
        'nerve', 'Nerve', 'NRV',
        'Holding function under trace pressure, and surviving black ICE.',
        'You fold at exactly the moment folding is fatal.',
        'holding on under pressure'),
    Attribute(
        'guile', 'Guile', 'GUI',
        'Pretexting, forged credentials, passing as somebody with a badge, '
        'what you get charged, and how fast your name cools.',
        'Every door has to be broken, every price is the asking price, and '
        'nobody ever forgets you.',
        'talking, prices, staying forgotten'),
    Attribute(
        'grit', 'Grit', 'GRT',
        'Stamina across a long run, recovery, absorbing damage to deck and body.',
        'You are fine right up until you are not, and then the run is over.',
        'taking damage, carrying chrome'),
)

ATTR_KEYS: tuple[str, ...] = tuple(a.key for a in ATTRIBUTES)
BY_KEY: dict[str, Attribute] = {a.key: a for a in ATTRIBUTES}

#: The derived numbers, glossed the same way (D182): what each one is for
#: and which attribute feeds it, in a clause short enough to sit beside the
#: number on `char`. The formulas below are the authority; this is the
#: caption. `validate.py` holds every key here to a formula in this file.
DERIVED_GLOSS: dict[str, str] = {
    'bandwidth': 'chrome you can carry (Grit)',
    'integrity': 'damage before a run ends badly (Grit)',
    'focus': 'careful actions a run (Logic)',
    'tempo': 'free actions banked as you work (Reflex)',
    'composure': 'against black ICE and panic (Nerve)',
    'cover': 'how fast your name cools (Guile)',
}


# --------------------------------------------------------------------------
# derived stats
# --------------------------------------------------------------------------


def bandwidth(grit: int) -> int:
    """Cyberware capacity, per D11. Grit is the body's tolerance for chrome."""
    return 8 + grit


def integrity(grit: int) -> int:
    """Damage absorbed before a run ends badly. Not hit points: losing all of
    it severs the connection, and only black ICE converts it into a flatline."""
    return 10 + 2 * grit


def focus(logic: int) -> int:
    """The per-run precision resource. Spent on retries, forced successes, and
    careful work that trades tempo for lower residue."""
    return 3 + logic // 2


def tempo(reflex: int) -> int:
    """How fast free actions bank during live engagement: at 2, one verb in
    three costs nothing; at 3, one in two (see `run.session.TEMPO_RATE`).
    Capped at 3 because a fourth action per tick outruns the ICE tell system,
    and reading tells is supposed to be the ceiling of the combat layer
    rather than something you skip."""
    return min(3, 1 + reflex // 4)


def cover(guile: int) -> int:
    """How well the story about you holds together, and for how long.

    Guile was the only attribute driving nothing. The other four each put a
    number on the sheet that the player spends or leans on: Grit gives
    Bandwidth and Integrity, Logic gives Focus, Reflex gives Tempo, Nerve
    gives Composure. Guile gave a modifier to two verbs and nothing else, so
    the sheet had four attributes that meant something and one that was an
    opinion.

    This is what it means. Heat is a story a faction is assembling about
    somebody, and Cover is how fast that story falls apart while they are not
    actively adding to it: not being missed, being confused with somebody
    else, having three plausible other people in the frame. It is the
    attribute of staying in business.
    """
    return guile * 2


def composure(nerve: int, dissonance: int) -> int:
    """Resistance to black ICE and to panic effects.

    Dissonance helps here and hurts everywhere social, which is the whole
    shape of the D11 chrome arc in one function: the more machine you are, the
    less the net can frighten you.
    """
    return nerve * 2 + dissonance // 10
