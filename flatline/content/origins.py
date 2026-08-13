"""Where you came from, per D10.

An origin sets attribute shape, starting gear, opening faction standing, and
one passive that never goes away. It never caps a skill and never locks a tree.
The corporate defector can end up a street social engineer; it will simply have
taken longer than the fixer's runner would have taken.

Each origin also carries a **complication**: something already true about the
world when the game starts. This is the part that makes an origin a story
rather than a stat block. The academic's debt exists whether or not the player
thinks about it, and the ex-cop's bounty is on the board on shift one.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Origin:
    key: str
    name: str
    blurb: str
    #: Prose shown at creation. Second person, present tense, no more than
    #: four sentences: this is a character sheet, not a novel.
    story: str
    #: Added to the flat starting spread of 3 across the board.
    attrs: dict[str, int]
    #: Free skill ranks, granted before creation experience is spent.
    skills: dict[str, int]
    credits: int
    #: Content ids resolved by the loader. A missing id is a validation error.
    cyberware: tuple[str, ...]
    programs: tuple[str, ...]
    deck: str
    #: The shape they already wear in the net. See content/icons.py.
    icon: str
    #: faction key -> starting reputation, on the -100..100 scale.
    standing: dict[str, int]
    passive: str
    passive_detail: str
    complication: str


ORIGINS: tuple[Origin, ...] = (
    Origin(
        'defector', 'Corporate defector',
        'Started inside. Knows how they think, and they know it.',
        'You wrote the access policy that you are now going to spend a career '
        'violating. Eleven years at Kagawa Vertical, most of them believing the '
        'work was neutral. You left with a laptop that was not yours and a '
        'clear idea of exactly how much they log.',
        attrs={'logic': 2, 'guile': 1, 'grit': -1},
        skills={'intrusion': 1, 'forensics': 1},
        credits=2400,
        cyberware=('corp_neural_shunt',),
        programs=('sable', 'quietcastle', 'ledgerhand'),
        deck='kagawa_issue',
        icon='corporate',
        standing={'kagawa': -45, 'aoyama': 10, 'fixers': 5},
        passive='Policy reader',
        passive_detail=(
            'You know what corporate networks log and when. Residue generated '
            'on any corporate network is reduced by 15%, and node types read '
            'correctly on a `scan` without a second probe.'),
        complication=(
            'Kagawa Vertical wants the laptop back, and they have not decided '
            'yet whether they want you with it.'),
    ),
    Origin(
        'gutter', 'Gutter runner',
        'Self-taught off salvage. Cheap, fast, and loud.',
        'Nobody taught you this. You found a deck in a flooded substation at '
        'fourteen and spent six years finding out what the parts did by '
        'breaking them. Everything you own is held together with solder and '
        'opinion, and all of it is faster than it has any right to be.',
        attrs={'reflex': 2, 'grit': 1, 'logic': -1},
        skills={'intrusion': 1, 'hardware': 1},
        credits=700,
        cyberware=('salvage_reflex_loop',),
        programs=('crowbar', 'crowbar', 'blink'),
        deck='scrapdeck',
        icon='plain',
        standing={'sixes': 20, 'kagawa': -10, 'fixers': -5},
        passive='Salvager',
        passive_detail=(
            'You can repair and improvise. Deck components cost 30% less to '
            'repair, and a destroyed component can be jury-rigged back to half '
            'function for free once per run.'),
        complication=(
            'The Sixes consider you theirs. They have not asked for anything '
            'yet. They will.'),
    ),
    Origin(
        'protege', 'Fixer\'s protege',
        'Grew up in the trade. Best contacts, thinnest foundation.',
        'Mara Okonkwo took you off a corner at nine and put you behind a desk '
        'answering her phones. You learned who everybody is, what everybody '
        'owes, and how a deal falls apart, long before you learned what a port '
        'scan was. The technical part is still catching up.',
        attrs={'guile': 2, 'nerve': 1, 'logic': -1},
        skills={'subterfuge': 1},
        credits=1800,
        cyberware=('social_lattice',),
        programs=('sable', 'handshake', 'blink'),
        deck='midline',
        icon='plain',
        standing={'fixers': 40, 'sixes': 10, 'nightwatch': -10},
        passive='Known quantity',
        passive_detail=(
            'Fixers front you work nobody else can see. One extra contract on '
            'the board at all times, and contract payouts negotiate 10% higher '
            'before reputation is applied.'),
        complication=(
            'Mara is owed something and has never once said what. She is '
            'patient in the way that people are when they are certain.'),
    ),
    Origin(
        'academic', 'Academic',
        'Cryptography background, no street sense whatsoever.',
        'You have published. Two of the papers are still cited, one of them by '
        'people who should not have access to it. The department stopped '
        'funding the work when they understood what it implied, which was '
        'roughly eight months before you understood what it was worth.',
        attrs={'logic': 3, 'guile': -2, 'grit': -1, 'nerve': 1},
        skills={'cryptography': 2},
        credits=1200,
        cyberware=('cortex_annex',),
        programs=('lattice', 'sable', 'quietcastle'),
        deck='university_loan',
        icon='plain',
        standing={'aoyama': 25, 'freeport': 15, 'sixes': -15},
        passive='First principles',
        passive_detail=(
            'You solve what you have never seen. Cryptography checks against '
            'unfamiliar encryption schemes take no unfamiliarity penalty, and '
            'you learn a network\'s cipher family from a single observation.'),
        complication=(
            'The loan on the deck is real, it is compounding, and the lender is '
            'not a bank.'),
    ),
    Origin(
        'expolice', 'Ex-enforcement',
        'Worked the other side. Reads ICE like a native.',
        'Nine years in Nightwatch cyber division, three of them running the '
        'intrusion response desk. You have sat on the other end of a trace with '
        'a coffee going cold, waiting for somebody exactly like you to make one '
        'more move. You know what they are waiting for. It has not helped as '
        'much as you expected.',
        attrs={'nerve': 2, 'reflex': 1, 'guile': -1},
        skills={'warfare': 1, 'forensics': 1},
        credits=1500,
        cyberware=('threat_overlay',),
        programs=('cudgel', 'sable', 'mirrorbox'),
        deck='decommissioned',
        icon='corporate',
        standing={'nightwatch': -60, 'sixes': -20, 'freeport': 20},
        passive='Read the room',
        passive_detail=(
            'ICE tells arrive a full tick earlier for you, and you identify '
            'countermeasure types on sight without a probe. Against Nightwatch '
            'networks specifically, you know the response playbook: alert '
            'escalation is one step slower.'),
        complication=(
            'There is a live bounty on you, filed by people who have your '
            'biometrics on record and your service history in a drawer.'),
    ),
    Origin(
        'chromed', 'Chromed',
        'Already more machine than most. The city notices.',
        'You stopped counting at eleven pieces. Somewhere in the middle of that '
        'the net started feeling less like a place you visit and more like the '
        'room you are actually standing in, with the meat world as the thing on '
        'the far side of a window. You are aware this is a symptom. It has not '
        'made you want to reverse it.',
        attrs={'reflex': 2, 'nerve': 1, 'grit': 1, 'guile': -2},
        skills={'warfare': 1, 'stealth': 1},
        credits=400,
        cyberware=('spinal_bus', 'ocular_suite', 'reflex_governor'),
        programs=('crowbar', 'cudgel'),
        deck='midline',
        icon='null',
        standing={'aoyama': -20, 'nightwatch': -15, 'sixes': 5},
        passive='Native',
        passive_detail=(
            'The net is your first language. You begin every run with one '
            'additional action in the first tick, and black ICE composure '
            'checks are made at a bonus equal to a quarter of your Dissonance.'),
        complication=(
            'You start at 35 Dissonance. Clinics charge you more, fixers meet '
            'you outdoors, and something in the ocular suite has begun '
            'reporting to a maintenance address you did not configure.'),
    ),
)

ORIGIN_KEYS: tuple[str, ...] = tuple(o.key for o in ORIGINS)
BY_KEY: dict[str, Origin] = {o.key: o for o in ORIGINS}

#: Every origin starts here before its `attrs` delta is applied.
BASE_ATTR = 3

#: The Chromed origin's opening Dissonance. Named rather than inline because
#: the city layer reads it when deciding how merchants behave on shift one.
CHROMED_START_DISSONANCE = 35
