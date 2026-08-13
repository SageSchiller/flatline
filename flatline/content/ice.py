"""Intrusion countermeasures: the opposition.

**Every construct has a tell.** One line of output, printed the tick before it
acts, describing what it is doing rather than what it is about to do. Reading
tells is the skill ceiling of the run layer, and it is the entire reason the
log is the interface instead of a health bar. A player who has learned that
`the segment's routing table is being rewritten around you` means a Hunter is
one tick from lock-on is playing a better game than one who has not, without
having spent a single point on anything.

Tells are per-archetype and there are several per construct, drawn from the
`ice` stream, so the same construct does not read identically every time.

The six behaviours, and the design question each one asks:

- **sentry**: will you pay to be quiet? (cheap, passive, everywhere)
- **probe**: will you move or will you hide? (roams, no lock-on)
- **hunter**: can you afford to fight? (locks on, damages the deck)
- **trap**: did you look before you touched it? (invisible until sprung)
- **warden**: what is your answer to a door that cannot be evaded?
- **black**: is this worth dying for? (the only route to a flatline)
"""

from __future__ import annotations

from dataclasses import dataclass, field

BEHAVIOURS = ('sentry', 'probe', 'hunter', 'trap', 'warden', 'black')

#: Alert levels. The network's collective state of mind. Escalates on noise
#: and on specific failures, and never de-escalates within a run.
ALERT_LEVELS = ('green', 'amber', 'red', 'lockdown')

ALERT_BLURB = {
    'green': 'Nothing has been noticed.',
    'amber': 'Something has been noticed. Nobody has decided what yet.',
    'red': 'You have been noticed. Active response is underway.',
    'lockdown': 'The network is closing. Routes are being cut behind you.',
}

#: Per-level multipliers applied to trace advance and ICE aggression.
ALERT_TRACE_MULT = {'green': 1.0, 'amber': 1.25, 'red': 1.7, 'lockdown': 2.4}


@dataclass(frozen=True, slots=True)
class IceType:
    key: str
    name: str
    behaviour: str
    #: Which factions field this construct. Empty means anybody.
    factions: tuple[str, ...]
    #: Rating range at posture 50. Scaled by actual posture at generation.
    rating: tuple[int, int]
    blurb: str
    #: Printed the tick before it acts. Never says what it will do.
    tells: tuple[str, ...]
    #: Printed when it acts.
    strike: str
    #: Damage per action, scaled by rating. Black ICE hits Integrity instead.
    damage: int = 0
    #: How much noise its presence adds when it is awake.
    noise: int = 0
    #: Extra trace per tick while it is locked on to you.
    trace: int = 0
    effects: dict = field(default_factory=dict)


ICE: tuple[IceType, ...] = (
    # -- sentry ------------------------------------------------------------
    IceType(
        'watchman', 'Watchman', 'sentry', (),
        (2, 4),
        'Standard passive monitor. Watches a node and reports what it sees, '
        'which is all it does and all it needs to do.',
        tells=(
            'a polling interval somewhere just shortened',
            'the node is describing itself to something upstream',
            'your session has been enumerated twice in the same second',
        ),
        strike='Watchman logs your session and escalates.',
        noise=3,
    ),
    IceType(
        'auditor', 'Auditor', 'sentry', ('kagawa', 'nightwatch', 'freeport'),
        (3, 5),
        'Compliance monitoring repurposed as security, which it turns out to '
        'be extremely good at, because it was always the same job.',
        tells=(
            'a compliance job has started early and against the wrong table',
            'something is reconciling this node against a manifest',
            'the audit log just began writing faster than events are happening',
        ),
        strike='Auditor files an exception against your access pattern.',
        noise=4,
        effects={'residue_mult': 1.4},
    ),

    # -- probe -------------------------------------------------------------
    IceType(
        'bloodhound', 'Bloodhound', 'probe', (),
        (3, 5),
        'Roams the segment looking for anything that does not belong. It does '
        'not lock on and it does not fight. It finds you and it tells.',
        tells=(
            'something is walking the segment one node at a time',
            'a scan is coming down the routing table toward you',
            'an inventory sweep just started two nodes out',
        ),
        strike='Bloodhound finds you and hands you to whatever is listening.',
        noise=6,
        trace=4,
    ),
    IceType(
        'stray', 'Stray', 'probe', ('sixes', 'carrion', 'freeport'),
        (2, 4),
        'Somebody\'s abandoned monitoring script, still running years later, '
        'still reporting to an address that still answers.',
        tells=(
            'an old cron job just woke up on an odd schedule',
            'something unmaintained is nonetheless paying attention',
            'a process with a nine-year-old timestamp has started moving',
        ),
        strike='Stray reports your presence to whoever inherited it.',
        noise=4,
        trace=2,
    ),

    # -- hunter ------------------------------------------------------------
    IceType(
        'kestrel', 'Kestrel', 'hunter', (),
        (3, 6),
        'Locks on and does not stop. Fast, light, and it will follow you '
        'across the entire network to keep doing exactly this.',
        tells=(
            'the segment\'s routing table is being rewritten around you',
            'something has matched your signature and is closing',
            'three failed connections just resolved to your position',
        ),
        strike='Kestrel is on you.',
        damage=4,
        noise=5,
        trace=5,
    ),
    IceType(
        'pike', 'Pike', 'hunter', ('sendai', 'nightwatch'),
        (4, 7),
        'Sendai\'s answer to the question of what an intrusion costs. Slower '
        'than a Kestrel and it does not need to be fast.',
        tells=(
            'something heavy has allocated itself against your session',
            'your connection is being held open from the far end',
            'the node has stopped negotiating and started measuring',
        ),
        strike='Pike drives into your session.',
        damage=7,
        noise=6,
        trace=4,
    ),
    IceType(
        'scrapper', 'Scrapper', 'hunter', ('sixes', 'carrion'),
        (2, 5),
        'Gang ICE. Improvised, badly documented, and considerably more '
        'dangerous than it looks because nobody can predict it.',
        tells=(
            'something is behaving in a way the protocol does not describe',
            'a process just did something that should not have worked',
            'the node is answering in a format nothing standard produces',
        ),
        strike='Scrapper tears into whatever it reached first.',
        damage=5,
        noise=8,
        trace=3,
    ),

    # -- trap --------------------------------------------------------------
    IceType(
        'snare', 'Snare', 'trap', (),
        (2, 5),
        'Invisible until it is not. Costs nothing to leave in place, which is '
        'why every network has them and nobody remembers where.',
        tells=(),
        strike='Snare closes. Your access tier drops.',
        trace=8,
        effects={'access_drop': 1},
    ),
    IceType(
        'tarbaby', 'Tarbaby', 'trap', ('aoyama', 'kagawa'),
        (3, 6),
        'Does not stop you. Slows you, specifically and only, while the trace '
        'does not slow at all.',
        tells=(),
        strike='Tarbaby has you. Everything is going to take longer now.',
        trace=4,
        effects={'tick_mult': 1.6},
    ),
    IceType(
        'canary', 'Canary', 'trap', ('freeport', 'fixers'),
        (2, 4),
        'Does nothing to you whatsoever. Tells everybody, immediately, in '
        'public, which is worse.',
        tells=(),
        strike='Canary publishes. The alert level jumps.',
        trace=6,
        effects={'alert_jump': 1},
    ),

    # -- warden ------------------------------------------------------------
    IceType(
        'gatekeeper', 'Gatekeeper', 'warden', (),
        (4, 6),
        'Guards a zone boundary. Cannot be evaded, cannot be ignored, and has '
        'no interest at all in what you say you are.',
        tells=(
            'the boundary is re-authenticating everything on both sides',
            'something at the chokepoint has begun refusing by default',
            'the gateway has stopped forwarding and started asking',
        ),
        strike='Gatekeeper refuses you and marks the attempt.',
        damage=3,
        noise=4,
        trace=3,
    ),
    IceType(
        'chamberlain', 'Chamberlain', 'warden', ('kagawa', 'aoyama', 'sendai'),
        (5, 8),
        'Corporate boundary ICE with a credential model deep enough to be '
        'talked past, if what you are carrying is good enough.',
        tells=(
            'your credentials are being checked against something authoritative',
            'the boundary has escalated your session for review',
            'something is comparing you to a list of people who belong here',
        ),
        strike='Chamberlain rejects your credentials and holds the record.',
        damage=4,
        noise=3,
        trace=5,
        effects={'credential_check': 1},
    ),

    # -- black -------------------------------------------------------------
    IceType(
        'coffin', 'Coffin', 'black', ('kagawa', 'aoyama', 'sendai', 'nightwatch'),
        (6, 9),
        'Lethal countermeasure. Legal in this jurisdiction for the protection '
        'of designated critical assets, a category the owner defines.',
        tells=(
            'the connection has stopped being a connection and started being a hold',
            'something is measuring your response latency against a baseline',
            'feedback is arriving before you send anything',
        ),
        strike='Coffin closes on your nervous system.',
        damage=11,
        noise=5,
        trace=7,
    ),
    IceType(
        'vespers', 'Vespers', 'black', ('sendai',),
        (7, 10),
        'Sendai builds the interface and Sendai builds the thing that comes '
        'back up it. Nobody has published a recording of one working.',
        tells=(
            'the deck is reporting input you did not provide',
            'your own commands are arriving back at you slightly wrong',
            'something has begun speaking in your session\'s voice',
        ),
        strike='Vespers reaches through the interface.',
        damage=14,
        noise=4,
        trace=6,
    ),
)

BY_KEY: dict[str, IceType] = {i.key: i for i in ICE}
ICE_KEYS: tuple[str, ...] = tuple(BY_KEY)

#: Effect keys ICE may carry that the run layer implements specially. Anything
#: outside this set plus `effects.ALL` is a validation error.
ICE_RIDERS: frozenset[str] = frozenset({
    'access_drop', 'alert_jump', 'credential_check',
})


def by_behaviour(behaviour: str) -> list[IceType]:
    return [i for i in ICE if i.behaviour == behaviour]


def available(behaviour: str, faction: str) -> list[IceType]:
    """Constructs of a behaviour that this faction actually fields."""
    return [i for i in ICE
            if i.behaviour == behaviour and (not i.factions or faction in i.factions)]
