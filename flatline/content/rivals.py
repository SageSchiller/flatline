"""The other runners. The city has more than one of you in it.

Rivals exist to make the world move when the player does not. A contract you
spend three shifts deliberating over is a contract somebody else takes, and the
board showing *who took it* is the cheapest possible way to make the city feel
inhabited rather than generated.

They are not a difficulty mechanic. A rival succeeding against Kagawa hardens
Kagawa, which makes the player's next Kagawa job worse, and that is a real
cost, but the point is narrative rather than numeric: over twenty shifts the
player learns that Vesper Okonkwo takes the corporate work and Hound takes
anything violent, and starts reading the board with that in mind.

**Disposition** is how a rival feels about the player specifically. It moves
when you take work they wanted, when you sell them out, and when you cover them
on an escort. At the extremes it changes what they do: a rival who likes you
will pass you work, and one who hates you will take jobs specifically to spite
you and will sell your name if asked.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: How a rival works, which decides what they take and how they fail.
STYLES = ('loud', 'quiet', 'social', 'chrome', 'careful')

STYLE_BLURB = {
    'loud': 'Fast, direct, and gone before the trace lands. Usually.',
    'quiet': 'Never seen, never in a hurry, never carrying much.',
    'social': 'Has never broken a service that would open for a phone call.',
    'chrome': 'More machine than argument. Goes where meat cannot.',
    'careful': 'Reads everything twice and takes half the work on offer.',
}


@dataclass(frozen=True, slots=True)
class RivalType:
    key: str
    name: str
    handle: str
    style: str
    #: Overall competence, 1 to 10. Drives their success roll against posture.
    skill: int
    blurb: str
    #: How they read to somebody who has met them. Shown by `who`.
    manner: str
    #: Objectives they prefer, weighted up when deciding what to take.
    prefers: tuple[str, ...]
    #: Faction standings they start with.
    standing: dict = field(default_factory=dict)
    #: Starting disposition toward the player.
    disposition: int = 0
    #: What they say when they are the escort on a job and things go wrong.
    panic: tuple[str, ...] = ()


RIVALS: tuple[RivalType, ...] = (
    RivalType(
        'vesper', 'Vesper Okonkwo', 'Vesper', 'social', 8,
        'Mara\'s niece, and better at this than Mara ever was. Takes '
        'corporate work almost exclusively, on the theory that corporations '
        'are the only clients who pay on time.',
        'Polite to the point of being unreadable. Has never once raised her '
        'voice on a job and has ended two people\'s careers in writing.',
        prefers=('exfiltrate', 'corrupt', 'surveil'),
        standing={'fixers': 55, 'kagawa': 15, 'sixes': -10},
        disposition=5,
        panic=('"I am going to need you to be somewhere useful, right now."',
               '"This was a bad brief and I took it anyway. My fault. Move."'),
    ),
    RivalType(
        'hound', 'Hound', 'Hound', 'loud', 6,
        'Nobody knows the real name and nobody has asked twice. Takes the '
        'work that involves breaking something, and charges for the noise as '
        'though it were a service.',
        'Talks constantly on a run and says nothing on the street. Genuinely '
        'seems to enjoy this, which everybody finds unsettling.',
        prefers=('wipe', 'escort', 'implant'),
        standing={'carrion': 30, 'sixes': -25, 'nightwatch': -40},
        disposition=-5,
        panic=('"There is a lot of it and it is all looking at me."',
               '"I am going to break something. Stand back or do not."'),
    ),
    RivalType(
        'quietkid', 'The Quiet Kid', 'Quiet', 'quiet', 7,
        'Turned up two years ago with no history and a deck worth more than '
        'the building it was in. Has never been caught, never been '
        'photographed, and never taken a job that pays over four thousand.',
        'Does not speak on jobs. Communicates in file drops. There is a '
        'reasonable argument that nobody has actually met them.',
        prefers=('surveil', 'exfiltrate'),
        standing={'freeport': 35, 'fixers': 20},
        disposition=0,
        panic=('A single dropped file: "leaving".',
               'No message at all. The icon is simply not there any more.'),
    ),
    RivalType(
        'saint', 'Saint Ambrose', 'Saint', 'chrome', 7,
        'Eleven visible pieces and an unknown number of the other kind. '
        'Aoyama funded the first six and has been trying to repossess them '
        'through the courts for three years.',
        'Speaks slightly too slowly, as though translating. Sometimes '
        'answers a question you have not asked yet, which he insists is a '
        'latency artefact.',
        prefers=('implant', 'exfiltrate', 'wipe'),
        standing={'aoyama': -55, 'carrion': 20, 'freeport': 10},
        disposition=0,
        panic=('"I can hold this. I have held worse. Go."',
               '"Do not wait for me. I mean that operationally."'),
    ),
    RivalType(
        'ledger', 'Ledger', 'Ledger', 'careful', 9,
        'The best in the city and takes about one job a month, always after '
        'a fortnight of legwork nobody else can be bothered with. Has never '
        'failed a contract and has declined more than everybody else '
        'combined.',
        'Asks a great many questions before agreeing to anything, and every '
        'one of them turns out to have been the question that mattered.',
        prefers=('exfiltrate', 'corrupt'),
        standing={'fixers': 40, 'freeport': 25, 'nightwatch': -15},
        disposition=0,
        panic=('"I priced this wrong. I am correcting it. Follow me out."',),
    ),
    RivalType(
        'moth', 'Moth', 'Moth', 'loud', 4,
        'Nineteen, brilliant, and going to be dead inside a year at the '
        'current rate. Takes work well above their level because nobody has '
        'ever told them not to.',
        'Enthusiastic in a way that everybody in Marrow finds difficult to '
        'be around, because they have all done the arithmetic.',
        prefers=('exfiltrate', 'wipe', 'escort'),
        standing={'sixes': 15, 'fixers': -5},
        disposition=15,
        panic=('"I do not know what that is. What is that? What IS that?"',
               '"I am fine. I am fine. Am I fine?"'),
    ),
    RivalType(
        'grieve', 'Grieve', 'Grieve', 'quiet', 8,
        'Used to run Nightwatch\'s intrusion response desk, which makes them '
        'the only person in the city who has professionally hunted every '
        'other name on this list.',
        'Watchful and extremely tired. Treats every conversation as an '
        'interview and does not appear to enjoy the habit.',
        prefers=('surveil', 'corrupt', 'wipe'),
        standing={'nightwatch': -35, 'kagawa': 20, 'carrion': -30},
        disposition=-10,
        panic=('"I know what this is. We are leaving. Now, not in a moment."',),
    ),
)

BY_KEY: dict[str, RivalType] = {r.key: r for r in RIVALS}
RIVAL_KEYS: tuple[str, ...] = tuple(BY_KEY)

#: Disposition bands, low bound inclusive. Each label covers from its own
#: bound up to the next, so the band centred on zero has to actually contain
#: zero: a rival at +15 reading as "cold" is a table that has drifted.
DISPOSITION_BANDS: tuple[tuple[int, str], ...] = (
    (-100, 'will sell you'),
    (-60, 'hostile'),
    (-25, 'cold'),
    (-8, 'neutral'),
    (25, 'friendly'),
    (60, 'owes you'),
)


def disposition_band(value: int) -> str:
    out = DISPOSITION_BANDS[0][1]
    for low, name in DISPOSITION_BANDS:
        if value >= low:
            out = name
    return out


#: What the board says when a rival has taken something off it.
TAKEN_LINES = (
    '{name} took it. The posting is gone and so is {name}.',
    '{name} got there first. Marrow knew before the board did.',
    'Somebody took {title} out from under you. It was {name}.',
    '{title} is spoken for. {name}, apparently, and at a discount.',
)

#: What the city hears afterwards.
OUTCOME_LINES = {
    'clean': (
        '{name} came out of {target} clean. Nobody is saying what with.',
        'Word is {name} finished the {target} job without anybody noticing '
        'for two days.',
    ),
    'messy': (
        '{name} got out of {target}, but not quietly. There is a lot of talk.',
        '{name} finished the {target} work and burned an identity doing it.',
    ),
    'failed': (
        '{name} did not come out of {target} with anything. {target} did '
        'come out of it with a file.',
        'The {target} job went badly for {name}. They are not taking calls.',
    ),
    'dead': (
        '{name} flatlined on the {target} job. Nobody is saying whose ICE.',
        'They are holding a wake for {name} in Marrow. {target} has not '
        'commented.',
    ),
}
