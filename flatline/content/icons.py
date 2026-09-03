"""Your icon: the shape you wear in cyberspace.

Every netrunner renders as *something*. The deck has to put a body on you
before the net will talk to you, and what you choose to be in there is a real
decision with real mechanics, not a portrait.

This is the fourth customisation axis, alongside skills, chrome, and the deck,
and it is deliberately the cheapest one to change: an icon is a file. You can
carry several and wear the right one for the job, which makes it the tactical
layer of character building rather than the permanent one.

**Coherence** is the constraint. An icon that is very far from a human shape is
harder to hold together, and holding it costs you unless your Dissonance has
already done the work. That is the payoff arc for a chromed build: the things
that make you worse in the city make you better at being something other than
a person in here.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Icon:
    key: str
    name: str
    blurb: str
    #: What somebody watching the render actually sees.
    render: str
    price: int
    #: Dissonance needed to wear it without penalty. Below this, the coherence
    #: cost applies: the icon fights you.
    coherence: int
    effects: dict = field(default_factory=dict)
    drawback: str = ''
    penalty: dict = field(default_factory=dict)
    #: Engine-implemented special behaviour.
    rider: str = ''


ICONS: tuple[Icon, ...] = (
    Icon('plain', 'Unmarked',
         'The default the deck ships with. A person-shaped absence of '
         'personality, in the same grey as ten thousand others.',
         'A human outline at working resolution. Nothing about it is '
         'memorable, which on reflection is the entire feature.',
         price=0, coherence=0,
         effects={},
         drawback='It is what everybody who has never thought about this looks '
                  'like, and the net treats you accordingly.',
         penalty={'pretext_bonus': -1}),

    Icon('corporate', 'Compliance Shell',
         'A licensed corporate avatar, the kind an auditor wears. Wearing one '
         'you have no right to is a specific criminal offence.',
         'Mid-forties, mid-level, holding a clipboard object that does '
         'nothing. It renders with a badge you cannot quite read.',
         price=3200, coherence=0,
         effects={'pretext_bonus': 3, 'crack_bonus': 1},
         drawback='It is registered hardware wearing a registered face. '
                  'Corporate ICE checks the registry, and when it comes back '
                  'wrong it comes back very wrong.',
         penalty={'heat_mult': 1.25},
         rider='registry_check'),

    Icon('null', 'Null',
         'No icon. A hole in the render where a person should be. Most decks '
         'will not hold it and most people cannot stand being it.',
         'Nothing. The environment simply fails to draw across a '
         'person-shaped volume, and the eye keeps sliding off.',
         price=7400, coherence=40,
         effects={'noise_mult': 0.72, 'trace_mult': 0.88},
         drawback='There is nothing there to reassure anybody. Any construct '
                  'that does notice you escalates immediately: you are '
                  'obviously not staff, not a process, and not confused.',
         penalty={'pretext_bonus': -6},
         rider='null_escalation'),

    Icon('swarm', 'Swarm',
         'You render as many small things rather than one large one. Lock-on '
         'has to pick which, and picking wrong costs it a tick.',
         'Somewhere between four hundred and nine hundred separate objects, '
         'moving as one and not quite managing it at the edges.',
         price=6100, coherence=25,
         effects={'evade_bonus': 4},
         drawback='Distributed attention is still attention. You cannot '
                  'concentrate the way a single shape can, and precision work '
                  'suffers for it.',
         penalty={'crypto_bonus': -2, 'focus': -1},
         rider='swarm_lock'),

    Icon('predator', 'Predator',
         'Something with teeth, rendered at a size the protocol was never '
         'meant to allow. Gang runners wear these. It works on people.',
         'Four metres of articulated dark, moving at a framerate the rest of '
         'the environment cannot match.',
         price=4800, coherence=20,
         effects={'ice_damage': 3, 'composure': 2},
         drawback='Nothing about it is subtle and nothing about it is '
                  'deniable. Everything in the segment reacts to it.',
         penalty={'noise_mult': 1.35}),

    Icon('mirror', 'Mirror',
         'Reflects whatever is looking at it. ICE that tries to classify you '
         'gets its own signature back and has to think about it.',
         'Your own shape, until something else looks, at which point it is '
         'that thing\'s shape, a half-second out of step.',
         price=8900, coherence=30,
         effects={'evade_bonus': 2, 'tell_lead': 1},
         drawback='It reflects allies too. Anything working alongside you, '
                  'including your own daemons, has trouble telling which of '
                  'you is you.',
         penalty={},
         rider='mirror_confusion'),

    Icon('deadname', 'Deadname',
         'Somebody else\'s icon, salvaged off a runner who did not need it '
         'any more. Their credentials are still faintly attached to it.',
         'A stranger, rendered with more care than you would spend on '
         'yourself. Whoever built it, built it to be liked.',
         price=5600, coherence=15,
         effects={'pretext_bonus': 4, 'rep_mult': 1.1},
         drawback='It is a dead person and some networks remember them. '
                  'Wearing it accrues Dissonance the way chrome does: +1 every '
                  'time you complete a run in it.',
         penalty={},
         rider='creeping_dissonance'),

    Icon('process', 'Process',
         'Not a person at all. You render as a scheduled job, which is what '
         'most of a network expects to see and almost never inspects.',
         'A maintenance task with a plausible name and a plausible owner, '
         'doing plausible work at three in the morning.',
         price=9800, coherence=50,
         effects={'noise_mult': 0.6, 'residue_mult': 0.8},
         drawback='A process has no standing and no voice. You cannot talk to '
                  'anything, because processes do not talk, and any attempt to '
                  'drops the disguise entirely.',
         penalty={'pretext_bonus': -10},
         rider='no_social'),
    Icon('janitor', 'Night Cleaner',
         'The shape of somebody who is in the building because the building '
         'is dirty. Nobody has ever asked one of them a question.',
         'A person in overalls pushing something. The render is deliberately '
         'low: whoever built it understood that the trick is not being worth '
         'the resolution.',
         price=2400, coherence=0,
         effects={'residue_mult': 0.75, 'trace_mult': 0.94},
         drawback='Cleaners are on a schedule and the schedule is public. '
                  'You are somewhere you can account for and nowhere you '
                  'cannot, which means the tells arrive late.',
         penalty={'tell_lead': -1}),
    Icon('meter', 'Meter Reader',
         'A utility process with a work order and a route. It belongs on '
         'every network in the city and on none of them in particular.',
         'A flat grey shape with a number on it that goes up. It is the '
         'least interesting thing in any room it is in, which took '
         'considerable work.',
         price=1800, coherence=0,
         effects={'heat_mult': 0.85, 'skill_hardware': 1},
         drawback='A meter reader reads meters. Anything you do that is not '
                  'plausibly reading a meter looks worse for the disguise '
                  'having been there.',
         penalty={'pretext_bonus': -2}),

    Icon('wraith', 'Wraith',
         'A person-shaped smear of interference, there and not there. Cheap '
         'to hold and hard to lock, which is the whole of the pitch.',
         'A dim outline with a bright edge and not much inside it. Lock-on '
         'keeps resolving and losing you, half a metre from where you were.',
         price=5000, coherence=20,
         effects={'evade_bonus': 3, 'noise_mult': 0.85},
         drawback='There is not enough of you to read the room. A tell a solid '
                  'shape would feel coming arrives a beat late in this.',
         penalty={'tell_lead': -1}),

    Icon('ronin', 'Ronin',
         'A masterless blade, rendered the old way: armour, a crest, and a '
         'weapon the protocol keeps trying and failing to file as a person.',
         'A helmed figure the environment draws a frame sharper than '
         'everything around it, blade already out. The crest is somebody '
         'else\'s colours, worn without their leave.',
         price=4400, coherence=12,
         effects={'ice_damage': 2, 'evade_bonus': 1},
         drawback='A drawn blade is a statement and statements carry. '
                  'Everything you do in it is louder than the same thing done '
                  'in something quiet.',
         penalty={'noise_mult': 1.2}),

    Icon('seraph', 'Seraph',
         'Something luminous and winged, rendered at a fidelity that costs '
         'real money and reads as real standing. People simply believe it.',
         'A bright haloed figure, wings half-spread, a full stop brighter than '
         'the room. Nobody who renders like this has ever had to explain '
         'themselves, and the net has learned to assume as much.',
         price=8600, coherence=28,
         effects={'pretext_bonus': 3, 'rep_mult': 1.15},
         drawback='It is the opposite of forgettable. Every system it passes '
                  'through remembers that it did, and the heat finds you '
                  'faster for the glow.',
         penalty={'heat_mult': 1.2}),

    Icon('reaper', 'Reaper',
         'A hood, a robe, and a face that is mostly skull. A threat rendered '
         'as a person, and the things that watch you flinch first.',
         'A cowled shape with a pale skull where a face should be and one '
         'socket lit red. It moves like it has already decided how this ends.',
         price=6800, coherence=24,
         effects={'composure': 3, 'ice_damage': 1},
         drawback='Nothing about it says staff, or process, or harmless. It '
                  'arrives loud and everything that can raise an alarm raises '
                  'one about it.',
         penalty={'noise_mult': 1.3, 'pretext_bonus': -3}),
)

BY_KEY: dict[str, Icon] = {i.key: i for i in ICONS}
ICON_KEYS: tuple[str, ...] = tuple(BY_KEY)

DEFAULT = 'plain'

#: Riders the engine implements. Anything outside this set is a content bug.
RIDERS: frozenset[str] = frozenset({
    'registry_check', 'null_escalation', 'swarm_lock', 'mirror_confusion',
    'creeping_dissonance', 'no_social',
})


def coherence_gap(icon_key: str, dissonance: int) -> int:
    """How far short of holding this shape you are. Zero means it fits."""
    icon = BY_KEY.get(icon_key)
    if icon is None:
        return 0
    return max(0, icon.coherence - dissonance)


def coherence_penalty(icon_key: str, dissonance: int) -> dict:
    """What an ill-fitting icon costs.

    Scales with the gap rather than being a cliff, so wearing something
    slightly beyond you is a real option with a real price, and wearing
    something far beyond you is obviously a mistake before you try it.
    """
    gap = coherence_gap(icon_key, dissonance)
    if not gap:
        return {}
    return {
        'focus': -(1 + gap // 20),
        'tick_mult': 1.0 + gap * 0.006,
        'composure': -(gap // 10),
    }
