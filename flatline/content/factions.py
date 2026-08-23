"""The twelve powers, and how they feel about each other.

Relations are the reason reputation is interesting. Helping one faction is
legibly hurting another, and the player can read the table before deciding,
which turns "who do I work for" into a strategic question rather than a
flavour one.

**Posture** is the number the run layer reads. It starts at each faction's
baseline and rises every time you succeed against them, because a corporation
that has been robbed hardens the thing that was robbed. Watching a target's
posture climb over a campaign, and feeling their networks get genuinely harder,
is the main way the city layer makes itself felt inside a run.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: kind -> how the city layer treats them. Every place the code branches on
#: kind must handle all of these, which `validate.py` checks: a missing branch
#: is a KeyError in network generation, discovered by a player rather than by
#: the build.
KINDS = ('corp', 'gang', 'broker', 'law', 'collective', 'cult', 'press',
         'construct')

#: Reputation bands, low bound inclusive. Read by contract access and pricing.
REP_BANDS: tuple[tuple[int, str], ...] = (
    (-100, 'hunted'),
    (-60, 'hostile'),
    (-25, 'cold'),
    (-10, 'wary'),
    (10, 'neutral'),
    (25, 'warm'),
    (60, 'trusted'),
    (85, 'inner'),
)

#: Heat bands. Heat is attention, not hatred: a faction can like you and still
#: be looking for whoever did that thing last week.
HEAT_BANDS: tuple[tuple[int, str], ...] = (
    (0, 'clean'),
    (20, 'noticed'),
    (45, 'flagged'),
    (70, 'pursued'),
    (90, 'hunted'),
)


@dataclass(frozen=True, slots=True)
class Faction:
    key: str
    name: str
    short: str
    kind: str
    blurb: str
    #: What their networks are like, in the player's words.
    doctrine: str
    #: Starting security posture, 0..100. The run layer scales everything off
    #: this, so it is the single most load-bearing number per faction.
    posture: int
    #: How fast posture climbs when robbed, per successful run against them.
    hardening: float
    #: How fast heat decays per shift. Corps forget slowly; gangs never.
    heat_decay: float
    #: faction key -> -1.0 hostile .. 1.0 allied. Sparse; missing is 0.
    relations: dict = field(default_factory=dict)
    #: What they pay for, which shapes the contract board.
    wants: tuple[str, ...] = ()
    #: How their networks differ from the standard (D63 b): multipliers the
    #: generator and the run read, keyed by `STYLE_KEYS`, default 1.0. The
    #: doctrine above is prose; this is the same sentence as numbers, and
    #: `validate.py` holds the two to agreeing by requiring every key here
    #: to be one the engine reads.
    style: dict = field(default_factory=dict)


FACTIONS: tuple[Faction, ...] = (
    Faction(
        'kagawa', 'Kagawa Vertical', 'Kagawa', 'corp',
        'Vertical farming, logistics, and about a third of the city\'s '
        'calories. The most boring megacorp in the city and the one with the '
        'most to lose.',
        'Deep, layered, and well documented. Kagawa networks are built by '
        'people following a standard, which means they are predictable, which '
        'means they are survivable if you have read the standard.',
        posture=45, hardening=6.0, heat_decay=1.8,
        relations={'aoyama': -0.3, 'sendai': -0.5, 'nightwatch': 0.6,
                   'sixes': -0.4, 'freeport': -0.6, 'meridian': 0.4,
                   'chorus': -0.3, 'static': -0.5, 'deepwater': -0.4},
        wants=('exfiltrate', 'corrupt', 'surveil'),
    ),
    Faction(
        'aoyama', 'Aoyama Biotech', 'Aoyama', 'corp',
        'Clinics, chrome, and the research that produces both. They own the '
        'best cyberware in the city and the worst of what it costs.',
        'Segmented to the point of paranoia, with a lot of small vaults rather '
        'than one large one. You will crack four things for a quarter of a '
        'payday each.',
        posture=52, hardening=7.0, heat_decay=1.4,
        relations={'kagawa': -0.3, 'sendai': 0.2, 'nightwatch': 0.4,
                   'freeport': -0.7, 'carrion': -0.5, 'meridian': 0.3,
                   'chorus': 0.3, 'static': -0.5},
        style={'vaults': 1.8, 'density': 0.9, 'traps': 1.3, 'black': 0.8},
        wants=('exfiltrate', 'implant', 'wipe'),
    ),
    Faction(
        'sendai', 'Sendai Interface', 'Sendai', 'corp',
        'Neural hardware. Everything between a human nervous system and a '
        'network passes through something they patented.',
        'Fast, modern, and aggressive. Sendai networks have less ICE than '
        'their peers and what they have hits considerably harder.',
        posture=58, hardening=8.0, heat_decay=1.2,
        relations={'kagawa': -0.5, 'aoyama': 0.2, 'nightwatch': 0.3,
                   'freeport': -0.4, 'meridian': 0.3, 'static': -0.4,
                   'deepwater': -0.6},
        style={'density': 0.7, 'damage': 1.4, 'hunters': 1.6, 'black': 1.3},
        wants=('exfiltrate', 'corrupt', 'implant'),
    ),
    Faction(
        'sixes', 'The Sixes', 'Sixes', 'gang',
        'Six blocks, once. Considerably more now, and still called that. They '
        'run the Ninth Ward and they run it as a business.',
        'Almost no ICE and almost no logging, because a gang network is a '
        'phone tree with delusions. The danger is entirely physical and '
        'entirely afterwards.',
        posture=22, hardening=3.0, heat_decay=0.5,
        relations={'carrion': -0.9, 'kagawa': -0.4, 'nightwatch': -0.7,
                   'fixers': 0.3, 'meridian': -0.3},
        style={'residue': 0.8},
        wants=('corrupt', 'wipe', 'escort'),
    ),
    Faction(
        'carrion', 'Carrion Column', 'Carrion', 'gang',
        'Newer, meaner, and organised around chrome the way a cult is '
        'organised around a text. They buy bodies and they are not fussy.',
        'Improvised, unpredictable, and studded with traps that exist because '
        'somebody thought they were funny rather than because they work.',
        posture=30, hardening=4.0, heat_decay=0.4,
        relations={'sixes': -0.9, 'aoyama': -0.5, 'nightwatch': -0.8,
                   'freeport': -0.3, 'meridian': -0.4, 'chorus': 0.2},
        style={'traps': 2.2, 'density': 0.9},
        wants=('exfiltrate', 'wipe', 'escort'),
    ),
    Faction(
        'fixers', 'The Switchboard', 'Switchboard', 'broker',
        'Not an organisation so much as an agreement between forty people who '
        'each know a hundred others. Mara Okonkwo answers for it when somebody '
        'has to.',
        'They do not have networks worth running. They have information, and '
        'they sell it, and running them is a way to never work again.',
        posture=35, hardening=5.0, heat_decay=1.0,
        relations={'sixes': 0.3, 'freeport': 0.4, 'nightwatch': -0.3,
                   'chorus': -0.2, 'static': 0.2},
        style={'density': 0.8, 'residue': 1.15},
        wants=('exfiltrate', 'surveil', 'escort'),
    ),
    Faction(
        'nightwatch', 'Nightwatch', 'Nightwatch', 'law',
        'Contracted municipal enforcement. They are not police, they are a '
        'vendor with arrest powers, and the distinction shows in the billing.',
        'Response-oriented rather than prevention-oriented. Their networks are '
        'lightly defended and extremely well watched, and the ICE arrives '
        'rather than waiting.',
        posture=48, hardening=6.5, heat_decay=0.8,
        relations={'kagawa': 0.6, 'aoyama': 0.4, 'sendai': 0.3,
                   'sixes': -0.7, 'carrion': -0.8, 'freeport': -0.5,
                   'fixers': -0.3, 'meridian': 0.5, 'chorus': -0.6,
                   'static': -0.7, 'deepwater': -0.5},
        style={'density': 0.75, 'probes': 1.8, 'hunters': 1.4, 'wardens': 0.8},
        wants=('surveil', 'wipe', 'corrupt'),
    ),
    Faction(
        'freeport', 'Freeport Collective', 'Freeport', 'collective',
        'The docks, run by the people who work them, for going on nine years '
        'now. Open hardware, open networks, and an absolute refusal to '
        'explain themselves to anybody.',
        'Genuinely open, genuinely audited, and consequently very hard to '
        'break in a way nobody notices. Everything is logged in public.',
        posture=40, hardening=4.5, heat_decay=1.6,
        relations={'fixers': 0.4, 'kagawa': -0.6, 'aoyama': -0.7,
                   'nightwatch': -0.5, 'sendai': -0.4, 'carrion': -0.3,
                   'meridian': -0.6, 'static': 0.6, 'deepwater': 0.2},
        style={'residue': 1.35, 'black': 0.5, 'wardens': 1.3},
        wants=('exfiltrate', 'implant', 'escort'),
    ),
    Faction(
        'meridian', 'Meridian Trust', 'Meridian', 'corp',
        'The bank. Not a bank in the sense of a building you can walk into: '
        'Meridian holds the paper on about a third of the debt in this city, '
        'including, in all likelihood, some of yours.',
        'Cryptographic to the exclusion of everything else. There is almost '
        'no ICE on a Meridian network because there is almost nothing on a '
        'Meridian network you can read without a key, and the keys are the '
        'only thing they guard.',
        posture=62, hardening=7.5, heat_decay=2.0,
        relations={'kagawa': 0.4, 'aoyama': 0.3, 'sendai': 0.3,
                   'nightwatch': 0.5, 'freeport': -0.6, 'sixes': -0.3,
                   'carrion': -0.4, 'chorus': -0.5, 'static': -0.7,
                   'deepwater': -0.3},
        style={'density': 0.5, 'crypto': 1.3, 'black': 0.7, 'traps': 0.6},
        wants=('exfiltrate', 'corrupt', 'surveil'),
    ),
    Faction(
        'chorus', 'The Chorus', 'Chorus', 'cult',
        'People who have decided that what happens to a netrunner at high '
        'Dissonance is not a symptom. They meet in clinics, they pay for '
        'other people\'s chrome, and they are extremely polite about all of '
        'it.',
        'Devotional rather than defensive. A Chorus network is somebody\'s '
        'sincere attempt to build a place worth being, and it is defended by '
        'people who genuinely do not mind dying in it.',
        posture=38, hardening=5.0, heat_decay=0.9,
        relations={'aoyama': 0.3, 'carrion': 0.2, 'nightwatch': -0.6,
                   'meridian': -0.5, 'fixers': -0.2, 'kagawa': -0.3,
                   'static': 0.1, 'deepwater': 0.4},
        style={'density': 0.8, 'hunters': 1.2, 'wardens': 0.7},
        wants=('implant', 'surveil', 'escort'),
    ),
    Faction(
        'static', 'Static', 'Static', 'press',
        'Pirate broadcast, run out of nowhere by people who publish rather '
        'than sell. They will pay less than a fixer for the same file and '
        'they will actually put it out, which for some jobs is the point.',
        'Almost nothing, almost nowhere, and mirrored eleven times. Breaking '
        'Static is easy and pointless: the thing you took was already public '
        'and the thing you wanted is on a machine in a country you cannot '
        'name.',
        posture=28, hardening=3.5, heat_decay=1.5,
        relations={'freeport': 0.6, 'fixers': 0.2, 'nightwatch': -0.7,
                   'kagawa': -0.5, 'aoyama': -0.5, 'sendai': -0.4,
                   'meridian': -0.7, 'chorus': 0.1},
        style={'density': 0.5, 'vaults': 0.6, 'residue': 0.7},
        wants=('exfiltrate', 'surveil', 'wipe'),
    ),
    Faction(
        'deepwater', 'Deepwater', 'Deepwater', 'construct',
        'Nobody has established what Deepwater is. It has no offices, no '
        'staff, and no street presence, and it has been placing contracts '
        'through four separate fixers for nine years without once meeting '
        'anybody. The prevailing theory is the obvious one and nobody enjoys '
        'saying it out loud.',
        'Its networks are not defended, they are inhabited. There is no '
        'perimeter to speak of and no shape you will recognise, and the '
        'countermeasures do not behave like software because there is a '
        'reasonable argument they are not.',
        posture=72, hardening=9.0, heat_decay=0.6,
        relations={'sendai': -0.6, 'freeport': 0.2, 'chorus': 0.4,
                   'nightwatch': -0.5, 'meridian': -0.3, 'kagawa': -0.4},
        style={'herders': 1.7, 'black': 1.3, 'wardens': 0.5, 'damage': 1.15},
        wants=('implant', 'surveil', 'escort'),
    ),
)

#: The style knobs (D63 b), and what each one scales. Every one is read by
#: the generator or the run; `validate.check_factions` holds `style` dicts to
#: these keys and `check_reads` holds the engine to reading them.
STYLE_KEYS: dict[str, str] = {
    'density': 'how much ICE there is at all',
    'probes': 'how much of it watches and reports',
    'hunters': 'how much of it hunts',
    'traps': 'how much of it is traps',
    'herders': 'how much of it closes routes',
    'black': 'how often a vault is lethal',
    'wardens': 'how often a boundary is guarded',
    'vaults': 'how many vaults there are',
    'crypto': 'how hard the encryption is',
    'damage': 'how hard a construct hits',
    'residue': 'how much of what you do is logged',
}


def style_line(fac: Faction) -> str:
    """The style as a phrase: `fewer constructs, harder hits, lethal
    vaults likelier`. Empty for the standard."""
    words = {
        'density': ('fewer constructs', 'more constructs'),
        'probes': ('less watched', 'closely watched'),
        'hunters': ('fewer hunters', 'more hunters'),
        'traps': ('fewer traps', 'studded with traps'),
        'herders': ('routes stay open', 'routes close behind you'),
        'black': ('lethal vaults rarer', 'lethal vaults likelier'),
        'wardens': ('boundaries softer', 'boundaries guarded'),
        'vaults': ('fewer vaults', 'many small vaults'),
        'crypto': ('weaker keys', 'harder keys'),
        'damage': ('softer hits', 'harder hits'),
        'residue': ('logs less', 'logs everything'),
    }
    out = []
    for key, value in fac.style.items():
        low, high = words.get(key, (f'less {key}', f'more {key}'))
        out.append(high if value > 1.0 else low)
    return ', '.join(out)


BY_KEY: dict[str, Faction] = {f.key: f for f in FACTIONS}
FACTION_KEYS: tuple[str, ...] = tuple(BY_KEY)


def rep_band(value: int) -> str:
    out = REP_BANDS[0][1]
    for low, name in REP_BANDS:
        if value >= low:
            out = name
    return out


def heat_band(value: int) -> str:
    out = HEAT_BANDS[0][1]
    for low, name in HEAT_BANDS:
        if value >= low:
            out = name
    return out


def relation(a: str, b: str) -> float:
    """How `a` feels about `b`. Symmetric by construction, checked by
    `validate.py`, because a one-sided grudge in a table this small is always
    a typo rather than a design intent."""
    if a == b:
        return 1.0
    fa = BY_KEY.get(a)
    return float(fa.relations.get(b, 0.0)) if fa else 0.0

def runs_lethal(key: str) -> bool:
    """Whether this lot have a lethal countermeasure to put on a network.

    Posture is advertised as the difficulty and this is the fact posture
    does not carry: Kagawa at forty-five can kill you and Meridian at
    sixty-two cannot, because lethal ICE is doctrine rather than budget.
    Seven of the twelve have none at all, and a player choosing a job by
    the number on the board had no way to know which seven (D79).
    """
    from . import ice as ice_content
    return bool(ice_content.available('black', key))
