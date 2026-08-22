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
- **herder**: will you go where it wants? (cuts routes, never touches you)
- **black**: is this worth dying for? (the only route to a flatline)

A herder is the odd one and the most interesting to play against, because it
does no damage at all. It closes the way you came and leaves exactly one door
open, and the question it asks is whether the thing it is steering you toward
is worse than the trace you would spend refusing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: What a countermeasure looks like the moment it wakes, by behaviour. Three
#: rows, the same width, in the Unicode rung and the ASCII one. Printed once
#: per construct, beside its name, when it wakes and you know what it is
#: (D62): a mark, like the faction sigils, so that after five runs the shape
#: says "warden" before the word does.
PORTRAITS: dict[str, tuple[tuple[str, str, str], tuple[str, str, str]]] = {
    'sentry': (('┌─┐', '│●│', '└─┘'), ('+-+', '|o|', '+-+')),
    'probe': (('·∘·', ' ◉ ', '·∘·'), ('.o.', ' O ', '.o.')),
    'hunter': (('◢█◣', '███', '◥█◤'), ('/#\\', '###', '\\#/')),
    'trap': (('╲ ╱', ' ╳ ', '╱ ╲'), ('\\ /', ' X ', '/ \\')),
    'warden': (('▛▀▜', '▌■▐', '▙▄▟'), ('+=+', '|#|', '+=+')),
    'herder': (('→→→', '↑ ↓', '←←←'), ('>>>', '^ v', '<<<')),
    'black': (('███', '█ █', '███'), ('###', '# #', '###')),
}


def portrait(behaviour: str, ascii_only: bool) -> tuple[str, ...]:
    """The three rows for a behaviour, at the rung the terminal can draw."""
    pair = PORTRAITS.get(behaviour)
    if pair is None:
        return ()
    return pair[1] if ascii_only else pair[0]


BEHAVIOURS = ('sentry', 'probe', 'hunter', 'trap', 'warden', 'herder',
              'black')

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

#: What each level costs you and what answers it, printed at the moment the
#: network escalates. The blurb above is the fiction; this is the decision.
#:
#: Escalating is the point in a run where a new player most often freezes,
#: because a red banner with no reading on it says "something bad" and says
#: nothing about whether the correct response is to leave, to hurry, or to
#: carry on exactly as before. It is usually one of the first two, and which
#: one depends on numbers the player already has.
ALERT_ADVICE = {
    'green': '',
    'amber': 'The trace runs a quarter faster from here. Nothing has been '
             'decided about you yet, so this is the cheap moment to `scrub` '
             'what you have left behind and keep moving.',
    'red': 'The trace runs at nearly double and the countermeasures are '
           'hunting rather than watching. `mask` buys you a tick of distance '
           'and `job` will tell you how much is left to do. If the answer is '
           '"most of it", leaving with nothing costs less than the alternative.',
    'lockdown': 'Everything is at two and a half times and routes are being '
                'cut behind you. There is no version of this that ends well '
                'slowly: finish the one thing you are standing on, or get out '
                'now.',
}


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
    # -- second wave ------------------------------------------------------
    IceType(
        'verger', 'Verger', 'sentry', ('aoyama', 'sendai'),
        (4, 6),
        'Corporate monitoring that does not report upward. It reports '
        'sideways, to three other constructs, all at once.',
        tells=(
            'three separate processes have started agreeing about something',
            'the node is describing you to its neighbours in the third person',
            'something has begun taking a census and you are in it',
        ),
        strike='Verger tells everything nearby exactly where you are.',
        noise=5,
        effects={'alert_jump': 2},
    ),
    IceType(
        'gull', 'Gull', 'probe', ('freeport', 'fixers', 'sixes'),
        (2, 4),
        'Wanders. Genuinely wanders: it has no route and no schedule, which '
        'makes it impossible to time and trivial to walk into.',
        tells=(
            'something is moving and it is not moving toward anything',
            'a process just changed direction for no reason you can see',
            'there is traffic on this segment that has no destination',
        ),
        strike='Gull blunders into you and starts shouting.',
        noise=7,
        trace=3,
    ),
    IceType(
        'coroner', 'Coroner', 'hunter', ('nightwatch', 'kagawa'),
        (5, 8),
        'Response-desk ICE. It does not hunt intruders, it hunts intrusions: '
        'it works backward from the damage and arrives where you are now.',
        tells=(
            'something is reading the log of what you did an hour ago',
            'your earlier work is being re-walked, in order, quickly',
            'a process is retracing your route and gaining',
        ),
        strike='Coroner finishes the reconstruction and arrives at you.',
        damage=6,
        noise=4,
        trace=6,
    ),
    IceType(
        'gallows', 'Gallows', 'trap', ('carrion', 'sixes'),
        (3, 6),
        'Somebody wired a dead-drop to a segment cut. It is not clever and '
        'the person who left it thought it was extremely funny.',
        tells=(),
        strike='Gallows cuts the segment behind you. That route is gone.',
        trace=5,
        effects={'route_cut': 1},
    ),
    IceType(
        'steward', 'Steward', 'warden', ('freeport', 'fixers', 'sixes'),
        (3, 5),
        'Not really ICE. A person, mostly, watching a boundary on a rota, '
        'with a script they wrote themselves and understand completely.',
        tells=(
            'somebody at the boundary has stopped what they were doing',
            'the gateway is being watched by something with opinions',
            'a human-paced process has taken an interest in this connection',
        ),
        strike='Steward closes the boundary and starts asking questions.',
        damage=2,
        noise=5,
        trace=2,
        effects={'credential_check': 1},
    ),
    IceType(
        'requiem', 'Requiem', 'black', ('aoyama',),
        (7, 10),
        'Aoyama built lethal countermeasure the way Aoyama builds everything: '
        'medically. It does not attack the session. It attacks the person on '
        'the other end of it, accurately, with reference to their chart.',
        tells=(
            'something is reading your vitals off the interface and writing '
            'them down',
            'the connection has begun behaving like a clinical procedure',
            'you are being measured by something that has seen your file',
        ),
        strike='Requiem administers the dose it calculated.',
        damage=13,
        noise=3,
        trace=8,
    ),
    # -- herder -----------------------------------------------------------
    IceType(
        'drover', 'Drover', 'herder', (),
        (3, 6),
        'Does not attack, does not report, and does not stop. It closes '
        'routes behind you, one at a time, and it is extremely patient about '
        'where it would prefer you went.',
        tells=(
            'a route you were not using has stopped answering',
            'the segment is smaller than it was a minute ago',
            'something is closing doors somewhere behind you, unhurriedly',
        ),
        strike='Drover closes a route. You have fewer ways out than you did.',
        noise=2,
        trace=2,
        effects={'route_cut': 1},
    ),
    IceType(
        'ostler', 'Ostler', 'herder', ('meridian', 'kagawa', 'nightwatch'),
        (4, 7),
        'Corporate containment. It is not trying to catch you: it is trying '
        'to make sure that when somebody does, you are somewhere convenient.',
        tells=(
            'the routing table has been simplified in a way that suits '
            'somebody',
            'two paths just became one path',
            'something is arranging the network around your position',
        ),
        strike='Ostler cuts the alternative. The remaining route is the one '
               'they want you on.',
        noise=3,
        trace=4,
        effects={'route_cut': 1},
    ),

    # -- the new powers ----------------------------------------------------
    IceType(
        'notary', 'Notary', 'warden', ('meridian',),
        (5, 8),
        'Meridian do not guard data, they guard keys, and the Notary is the '
        'thing that decides whether you are somebody a key may be issued to. '
        'It has never been in a hurry and it has never been wrong.',
        tells=(
            'your credentials are being compared against a signature chain',
            'something is establishing, carefully, who issued you',
            'the boundary has begun a verification that has several steps',
        ),
        strike='Notary declines to certify you, in writing, permanently.',
        damage=3,
        noise=2,
        trace=6,
        effects={'credential_check': 1},
    ),
    IceType(
        'psalm', 'Psalm', 'sentry', ('chorus',),
        (3, 6),
        'A Chorus construct, and the only ICE in the city that will talk to '
        'you first. It asks what you are doing here. It appears to be '
        'genuinely interested in the answer.',
        tells=(
            'something has addressed you directly and is waiting',
            'a voice underneath the network has asked you a question',
            'the agreement has paused, politely, for you',
        ),
        strike='Psalm decides you are not one of them and says so, loudly, to '
               'everybody.',
        noise=6,
        effects={'alert_jump': 2},
    ),
    IceType(
        'congregant', 'Congregant', 'hunter', ('chorus',),
        (4, 7),
        'People, more or less. A Chorus run is defended by members who have '
        'jacked in specifically to defend it, and who do not appear to mind '
        'what happens to them in the course of doing so.',
        tells=(
            'something has committed to you completely and without hedging',
            'a process just accepted damage it could have avoided',
            'whatever is closing has no exit strategy at all',
        ),
        strike='Congregant closes on you and does not protect itself.',
        damage=8,
        noise=5,
        trace=3,
    ),
    IceType(
        'stringer', 'Stringer', 'probe', ('static',),
        (2, 5),
        'A Static process that is not looking for intruders. It is looking '
        'for a story, and an intruder is one.',
        tells=(
            'something started recording about four seconds ago',
            'a feed somewhere has swung round to face this segment',
            'you are, quite suddenly, being documented',
        ),
        strike='Stringer publishes you. Not to security. To everybody.',
        noise=4,
        trace=5,
        effects={'alert_jump': 2},
    ),
    IceType(
        'undertow', 'Undertow', 'black', ('deepwater',),
        (8, 10),
        'Nothing about Undertow behaves like software. It does not scan, it '
        'does not challenge, and it does not escalate. It notices, and then '
        'the distance between you and it stops being a distance.',
        tells=(
            'the pressure has changed and you did not move',
            'something very large is now much closer and you cannot say when',
            'you have been noticed by something that does not have eyes',
        ),
        strike='Undertow arrives. There was no approach.',
        damage=15,
        noise=2,
        trace=5,
    ),
    IceType(
        'benthic', 'Benthic', 'herder', ('deepwater',),
        (5, 8),
        'Deepwater does not need to catch anybody. It simply makes the parts '
        'of itself you are not wanted in stop existing while you are looking '
        'at them.',
        tells=(
            'a route has closed the way a hand closes',
            'the shape of this place has changed and nothing moved',
            'somewhere you had been intending to go is no longer there',
        ),
        strike='Benthic closes. The network is smaller and you are further in.',
        noise=1,
        trace=3,
        effects={'route_cut': 1},
    ),
)


BY_KEY: dict[str, IceType] = {i.key: i for i in ICE}
ICE_KEYS: tuple[str, ...] = tuple(BY_KEY)

#: Effect keys ICE may carry that the run layer implements specially. Anything
#: outside this set plus `effects.ALL` is a validation error.
ICE_RIDERS: frozenset[str] = frozenset({
    'access_drop', 'alert_jump', 'credential_check', 'route_cut',
})


def by_behaviour(behaviour: str) -> list[IceType]:
    return [i for i in ICE if i.behaviour == behaviour]


def available(behaviour: str, faction: str) -> list[IceType]:
    """Constructs of a behaviour that this faction actually fields."""
    return [i for i in ICE
            if i.behaviour == behaviour and (not i.factions or faction in i.factions)]
