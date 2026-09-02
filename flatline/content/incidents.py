"""Things that happen while you are in there. D77.

A network has a posture (how hard), a shape (who built it), and a
condition (what tonight is like). Those are all decided before you jack
in and none of them changes while you are inside, which meant a run was a
sequence of your own decisions against a board that never moved on its
own. It was legible and it was quiet, and quiet is the thing a player
called boring.

An incident is the fourth thing: something the network does, mid-run, on
its own clock. Most are bad, some are good, and a few are neither until
you answer them.

Three rules hold this together and validate enforces all three.

**They are answered with the verbs you already have.** Nothing here opens
a menu. An incident changes the board and the next thing you type is the
answer to it: `wait`, `mask`, `scrub`, `connect`, `strike`, `jack out`.
That keeps a run one continuous stream of your own decisions instead of a
run interrupted by questionnaires.

**Nothing here is a hidden die.** Every number an incident moves is
printed on the line that moves it, and anything that changes a check
shows up in `odds` as its own term, because D14 does not stop being true
because the modifier arrived at tick nine.

**The bad ones outnumber the good ones and the good ones are real.** A
network that only ever helps you is a network with no teeth; one that
only ever hurts is a tax with prose on it. The ratio is a budget, checked
by validate, and a good incident is worth having rather than a smaller
punishment.

`hook` is the one field with any subtlety: an incident that sets one is
not finished when it prints. It has attached something to the run that
the *next* action resolves, which is where the puzzles live. The player
can always see what it is, on `status` and in the line itself, and the
answer is always a verb they already know.
"""

from __future__ import annotations

from dataclasses import dataclass


#: Chance per tick that anything happens at all, before the modifiers
#: below. Deliberately low: an incident every other tick is weather, and
#: weather is wallpaper.
CHANCE = 0.055

#: No two incidents within this many ticks of each other. A run that
#: coughs twice in three ticks reads as broken rather than as busy.
COOLDOWN = 4

#: Nothing happens before this tick. The first few ticks of a run are the
#: player working out where they are, and interrupting that is rude.
GRACE = 3

#: The alert multiplies it. A red room is a room where things happen.
BY_ALERT = {'green': 1.0, 'amber': 1.5, 'red': 2.2, 'lockdown': 2.8}


@dataclass(frozen=True, slots=True)
class Incident:
    key: str
    #: Shown on `status` while a hook is attached, and in the log.
    name: str
    #: What happens. Second person, present tense, one or two sentences.
    text: str
    #: 'bad', 'good', or 'turn' for the ones that are a decision.
    kind: str = 'bad'
    weight: float = 1.0

    # -- when it can happen ------------------------------------------
    #: Zones it belongs to. Empty means anywhere.
    zones: tuple[str, ...] = ()
    #: Faction kinds it belongs to. Empty means anybody's network.
    kinds: tuple[str, ...] = ()
    #: Alert levels it can fire at. Empty means any.
    alert: tuple[str, ...] = ()
    #: Only where there is something alive on this host.
    needs_ice: bool = False
    #: Only once the trace is at least this far along.
    min_trace: float = 0.0
    #: Only while carrying something.
    needs_haul: bool = False

    # -- what it does, all printed on the line that does it -----------
    trace: float = 0.0
    noise: int = 0
    residue: int = 0
    focus: int = 0
    integrity: int = 0
    #: Steps the alert. Negative cools it.
    alert_step: int = 0
    #: Wakes whatever is asleep on this host.
    wakes: bool = False
    #: Free ticks, given back.
    tempo: int = 0
    #: Reveals part of the network: 'hosts', 'ice', or 'objective'.
    reveals: str = ''
    #: Opens a service on this host, or one hop out.
    opens: bool = False

    # -- the ones that are not finished when they print ---------------
    #: A named state the next action resolves. See `HOOKS`.
    hook: str = ''


#: What a hook does, in one clause each, for `status` and the manual. The
#: engine reads these keys by name and validate holds every one of them to
#: being implemented.
HOOKS: dict[str, str] = {
    'echo': 'the next thing you do, it does too, and both of them are '
            'yours: double noise and double residue',
    'tail': 'something is following your traffic: the next host you open '
            'wakes with you in it',
    'lean': 'the next noise you make here costs a point of Integrity; '
            'being still costs nothing',
    'grace': 'the next thing you do is free, once',
    'quiet': 'the next noise you make does not register',
}


INCIDENTS: tuple[Incident, ...] = (
    # -- the ordinary bad ------------------------------------------------
    Incident(
        'shift_change', 'Shift change',
        'Somewhere above you a shift ends. For about a minute the traffic '
        'doubles and everybody is saying goodnight to everybody, and you '
        'are in the middle of it being nobody.',
        noise=4, trace=1.5),
    Incident(
        'backup', 'Backup window',
        'A backup job starts on a schedule somebody set nine years ago. It '
        'walks every file on this host, politely, one at a time, and it '
        'will notice a gap where a file used to be.',
        residue=4, trace=2.0, zones=('interior', 'restricted')),
    Incident(
        'renegotiate', 'Session renegotiation',
        'Your session times out and comes back. It is the same session and '
        'it is a new one, and for one tick you are two people to this '
        'network, both of them you.',
        noise=5, wakes=True),
    Incident(
        'rotation', 'Log rotation',
        'The logs roll over. Everything you have done tonight is now in a '
        'file with a date on it rather than a file being written to, which '
        'is worse: a file with a date on it is a thing people go and read.',
        residue=6),
    Incident(
        'ticket', 'Somebody opens a ticket',
        'Somebody upstairs opens a ticket. It says the word "intermittent" '
        'in it, which is the most dangerous word in this building, because '
        'it is the one that makes people look properly.',
        alert_step=1),
    Incident(
        'shaping', 'Traffic shaping',
        'The carrier decides you are a bulk transfer and shapes you '
        'accordingly. Everything you do arrives late and arrives obvious.',
        trace=4.0, min_trace=0.2),
    Incident(
        'reboot', 'A service comes back',
        'Something you opened closes. Not because anybody noticed: because '
        'a watchdog somewhere counted to sixty and did the only thing it '
        'knows how to do.',
        noise=2, zones=('interior', 'restricted', 'core')),
    Incident(
        'hot', 'The deck runs hot',
        'The deck is hotter than the room. You can hear it, out there, on '
        'the desk, in the body you are not currently using.',
        focus=-2),
    Incident(
        'sweep', 'Automated sweep',
        'A sweep runs. It is not looking for you specifically. It is '
        'looking for anything, on a timer, and being unlucky is a way of '
        'being specific.',
        wakes=True, needs_ice=True),
    Incident(
        'coolant', 'Cooling fault',
        'Something in the deck stops moving air and the feedback comes up '
        'the line and into your hands, which are not in here.',
        integrity=-1, focus=-1, min_trace=0.35),
    Incident(
        'floor_lights', 'The lights come on',
        'Two floors up, in a building you have never seen, the lights come '
        'on. Somebody is walking a corridor with a torch and a clipboard '
        'because a light on a panel is amber.',
        alert_step=1, min_trace=0.45),
    Incident(
        'mirror_traffic', 'Your traffic is mirrored',
        'A tap you did not know about starts copying everything you send '
        'to somewhere you cannot see.',
        residue=3, trace=2.0),
    Incident(
        'gossip', 'Somebody says your name',
        'Two people in a channel you can see are discussing whether the '
        'thing on the third floor is a fault or a person. One of them has '
        'already decided.',
        alert_step=1, kinds=('corp', 'law')),
    Incident(
        'devotion', 'The singing changes',
        'The traffic here has a rhythm and the rhythm changes, the way a '
        'room changes when everybody in it stops doing one thing and '
        'starts doing another, and none of them had to be told.',
        wakes=True, alert_step=1, kinds=('cult',)),
    Incident(
        'stock_check', 'Somebody counts the stock',
        'Somebody starts a stock check on the very thing you are standing '
        'in. Not a security measure. An inventory, done badly, by a person '
        'who will notice a number that is wrong.',
        residue=5, kinds=('gang', 'collective')),
    Incident(
        'pressure', 'The pressure changes',
        'Whatever this is, it notices the shape of the space you are '
        'taking up in it, and closes around it a little, the way water '
        'does around a hand.',
        trace=3.0, focus=-1, kinds=('construct',)),

    # -- the good ones, and they are worth having ------------------------
    Incident(
        'maintenance_door', 'A maintenance session',
        'An engineer opens a session on this host, does something for '
        'ninety seconds, and leaves it open behind them the way people '
        'always do.',
        kind='good', opens=True, weight=0.8),
    Incident(
        'handover', 'A bad handover',
        'The desk changes hands and the new one is reading the notes of '
        'the old one, which are three lines long and one of them is about '
        'a kettle. Nobody is watching anything for a moment.',
        kind='good', alert_step=-1, weight=0.8),
    Incident(
        'backup_ends', 'The load drops',
        'The backup finishes. The whole segment breathes out, and for a '
        'while everything on it, including you, is one more quiet process '
        'among many.',
        kind='good', trace=-5.0, weight=0.7, min_trace=0.15),
    Incident(
        'cache_spill', 'A topology cache spills',
        'Something asks a router a question it has been asked a thousand '
        'times, and the router answers it out loud, to everybody, '
        'including you.',
        kind='good', reveals='hosts', weight=0.7),
    Incident(
        'engineer_notes', "Somebody's notes",
        'There is a text file on this host with a name like a swear word '
        'and it is nine years of somebody working out what is actually '
        'running here, because nobody would tell them.',
        kind='good', reveals='ice', weight=0.6),
    Incident(
        'stale_key', 'A stale credential',
        'A process authenticates with something that expired four years '
        'ago and is still accepted, because turning it off is somebody\'s '
        'job and that somebody left.',
        kind='good', opens=True, weight=0.6,
        zones=('interior', 'restricted')),

    # -- the ones that are not finished when they print ------------------
    Incident(
        'echo', 'Something is copying you',
        'A process attaches itself to your icon and begins repeating what '
        'you do, a half-second behind, like a child in a corridor.',
        kind='turn', hook='echo', weight=0.9),
    Incident(
        'tail', 'A crawler tags your route',
        'A crawler puts a mark on the path you came in by. It is not '
        'following you. It is making it easy for the next thing to.',
        kind='turn', hook='tail', weight=0.9),
    Incident(
        'lean', 'The floor gives',
        'Something under this host is not carrying what it used to. It '
        'holds while you are still and it does not hold when you push.',
        kind='turn', hook='lean', weight=0.8, min_trace=0.25),
    Incident(
        'window', 'A gap opens',
        'For no reason you will ever learn, the segment goes quiet for a '
        'moment, the way a road does.',
        kind='turn', hook='grace', weight=0.6),
    Incident(
        'cover_noise', 'Somebody else is loud',
        'Somebody, somewhere on this segment, does something considerably '
        'louder than anything you have done tonight, and every log in the '
        'building turns to look at them.',
        kind='turn', hook='quiet', weight=0.7),
    # The other runners, in the one place they never were (D89). Who and
    # what it means is decided in `RunState._company` from the city's
    # roster, because it depends on somebody's opinion of you.
    Incident(
        'company', 'Somebody else is in here',
        'Another session, not theirs, moving the way you move: somebody '
        'who is in this network for their own reasons tonight.',
        kind='turn', weight=0.9, alert=('green', 'amber')),
)

BY_KEY: dict[str, Incident] = {i.key: i for i in INCIDENTS}
INCIDENT_KEYS: tuple[str, ...] = tuple(i.key for i in INCIDENTS)
