"""The run: the tick, the D5 triangle, and everything ICE does.

This is the heart of the game and the file to read first when something feels
wrong during a run.

**The triangle.** Noise is local and decays. Trace is global and never decays.
Residue persists past the run entirely. Actions feed all three at different
rates, and the whole tactical layer is the player choosing which of the three
to spend. Cleaning up costs ticks, ticks cost trace, and trace is the thing
that ends you: that loop is the game.

**The tick.** Actions cost ticks. Each tick advances trace, lets awake ICE act,
and decays local noise. Nothing else moves time, so a player who stops issuing
commands is genuinely safe, which is correct: the pressure should come from
needing to act, not from a wall clock.

**Tells.** Awake ICE telegraphs one tick before it strikes. Every strike in the
game is preceded by a line of output that described what was happening. This is
the fairness contract with the player and nothing may violate it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..content import cyberspace
from ..content import shifts
from ..content import factions as fac_content
from ..content import ice as ice_content
from ..content import incidents as incident_content
from ..content import nodes as node_content
from ..content import programs
from ..content import skills as skill_content
from ..model.character import Character
from ..rng import Stream
from .. import ui
from ..ui import Console
from . import network as net_mod
from .checks import Check
from .network import IceInstance, Network, Node

# --------------------------------------------------------------------------
# balance constants
# --------------------------------------------------------------------------

TRACE_MAX = 100.0
#: Attempts at one door before the brief prefers another on the same
#: host, if there is one (D91).
DOOR_PATIENCE = 3
#: And at one host, across its doors, before the brief prefers another
#: host, if there is one (D100).
HOST_PATIENCE = 5
#: Loud ticks at red before the response arrives (D92), and at lockdown
#: (D101).
RESPONSE_AFTER = 6
RESPONSE_AFTER_LOCKDOWN = 3
#: Trace added per tick before any modifier. Deliberately small: most of the
#: pressure should come from what the player does, not from the clock alone.
TRACE_PER_TICK = 1.1

#: What carrying the thing they want does to everything else you do (D80).
#: The exit is the job on an exfiltration, and this is the number that
#: makes that true rather than a thing the prose asserts.
HAUL_NOISE = 1.5
#: What a tick costs when you made no noise in it (D66). The comment above
#: has always said the pressure should come from what the player does
#: rather than from the clock alone, and the clock was flat, which made it
#: exactly the opposite: a run was a countdown you could not affect except
#: by finishing early. Now a working tick is dear and a quiet one is cheap,
#: which is what makes `wait`, `ghost`, `sidechannel` and every `--quiet`
#: in the game worth the time they cost.
IDLE_TRACE = 0.45
#: How many ticks of trace history `status` keeps for its sparkline. Sixty is
#: comfortably longer than any run has ever lasted and short enough that it is
#: never worth thinking about.
TRACE_HISTORY = 60
#: How much of a noisy action's noise converts straight into trace.
NOISE_TO_TRACE = 0.30
#: Local noise removed from every node each tick.
NOISE_DECAY = 2
#: The nemesis race (D120): a nemesis in the run is after the same thing you
#: are. How many of your ticks before they warn you they are ahead, before
#: they reach it first, and how much of the haul they take if they do.
RIVAL_RACE_WARN = 4
RIVAL_RACE_STEAL = 9
RIVAL_SKIM = 0.6
#: Node noise at which dormant ICE there wakes up.
NOISE_WAKE = 8
#: Node noise at which the whole network escalates one alert level.
NOISE_ESCALATE = 18
#: Residue converted to faction heat after the run, per point.
RESIDUE_TO_HEAT = 0.55

#: Damage a component takes per ICE strike that lands on the deck, and the
#: strike size at which a hit does two levels rather than one (D63). Before
#: this every non-lethal construct did exactly one level, so a Coroner at
#: damage 6 and a Kestrel at 4 were the same construct with different prose.
DECK_HIT = 1
DECK_HIT_HEAVY = 6

#: Fraction of a free action each real tick banks, by Tempo (D63). Tempo 2
#: is a free verb every third tick; Tempo 3 every second. Capped there
#: because a fourth action per tick outruns the tell system, and reading
#: tells is supposed to be the ceiling of the combat layer.
TEMPO_RATE = {1: 0.0, 2: 1 / 3, 3: 0.5}

#: Chance a Salvaged Reflex Loop drops the third or later action in a tick.
MISFIRE_CHANCE = 0.35

#: Below this fraction of Integrity a Deadman Grip cuts the connection.
DEADMAN_FRACTION = 0.35

#: Chance per tick that a daemon under a Mirror icon does nothing.
MIRROR_HESITATION = 0.25

#: `mask` (D63 b). Each use in a run is worth this much of the last, and no
#: mask can take the trace below this fraction of what the clock alone has
#: put there. Before this a rating-3 mask on a quiet host was a loop that
#: reset the only clock in the game indefinitely.
MASK_DECAY = 0.75
MASK_FLOOR = 0.5

#: What a sealed record is worth (D63 b): the share of nominal it sells for
#: and the share of the fee a patron pays for the thing they wanted open.
SEALED_HAUL = 0.4
SEALED_SHARE = 0.55

OUTCOMES = ('running', 'clean', 'burned', 'severed', 'flatline')


@dataclass(frozen=True, slots=True)
class Brief:
    """What the run is for, in four parts, filled from the run itself.

    Kept as data rather than as printed lines because three different places
    want different amounts of it: `status` takes one row of it, `job` prints
    all of it, and `jack out` reads `done` to decide whether to argue.
    """

    #: What finishing looks like. One sentence, naming real hosts and records.
    aim: str
    #: Where it is, or what to look for when you have not found it yet.
    where: str
    #: How far along. Deliberately short: it goes on one line beside a bar.
    progress: str
    #: Whether the contract is satisfied right now.
    done: bool
    #: What to type next. One move ahead, never a walkthrough.
    steps: tuple[str, ...] = ()


@dataclass(slots=True)
class RunState:
    net: Network
    char: Character
    rng: Stream
    console: Console
    #: The contract being served, as a plain dict from the city layer. None
    #: for a speculative run, which is legal and pays worse.
    contract: dict | None = None

    here: str = ''
    tick: int = 0
    #: Which shift you jacked in on. A trace is a search through everybody's
    #: traffic, so how much traffic there is decides how long you have. Fixed
    #: at connection: the shift does not tick over mid-run, and a run that
    #: straddled a shift boundary would need the whole clock in here.
    phase: str = 'morning'
    trace: float = 0.0
    #: Trace at the end of every tick, for the sparkline in `status`. Bounded
    #: because a run that somehow reached ten thousand ticks should not also
    #: be carrying ten thousand floats through every save.
    trace_history: list = field(default_factory=list)
    alert: str = 'green'
    #: Access tier from credentials, 0..3. Distinct from where you are: a tier
    #: 2 credential does not put you in the restricted zone, it stops that zone
    #: treating you as a stranger.
    tier: int = 0
    focus: int = 0
    overclock: int = 0
    hurt: int = 0

    haul: list[str] = field(default_factory=list)
    #: Objective progress, keyed by objective type.
    done: dict = field(default_factory=dict)

    #: Countermeasures currently locked on, wherever they physically sit.
    locked: list[IceInstance] = field(default_factory=list)
    #: The construct that hit you last, this tick, and the one that cut
    #: you loose, if one did (D89). The city keeps the second.
    last_hit_by: str = ''
    #: And the last one that struck you at any point tonight: when the
    #: trace fills, that is what had you (D91). Four severs in five were
    #: the trace and recorded nobody.
    last_struck_by: str = ''
    #: Ticks the room has been red or worse, and whether the response has
    #: arrived yet (D92).
    red_ticks: int = 0
    responded: bool = False
    severed_by: str = ''
    #: Whether the construct with your name on it died tonight.
    grudge_killed: bool = False
    #: The other runners in the city, as plain dicts, for the night one
    #: of them turns out to be in here too (D89).
    rivals: list = field(default_factory=list)
    company: dict = field(default_factory=dict)
    #: A nemesis racing you for the objective in this run (D120): the dict
    #: from `rivals`, or empty. `rival_lead` is how far ahead they have got,
    #: and `rival_won` records who reached it first once it is settled.
    rival_race: dict = field(default_factory=dict)
    rival_lead: int = 0
    rival_won: str = ''
    #: How the run draws its pictures (D105/D110), copied off the session so
    #: the engine can draw a construct at the tell without reaching for the
    #: shell. 'none' turns off both the pictures and the screen effects.
    render_mode: str = 'picture'
    #: Ticks remaining on Nullsig and Impersonate.
    nullsig: int = 0
    impersonating: int = 0
    #: Once-per-run techniques already spent.
    spent: set = field(default_factory=set)
    #: Transient tick-cost multiplier from traps.
    drag: float = 1.0
    #: Autonomous processes, per Daemonology rank 4. Each is
    #: {uid, program, node, task, arg, life}. They act on the tick, before ICE,
    #: which is what lets a daemon draw a Probe off you rather than after.
    daemons: list = field(default_factory=list)
    #: Faction the residue will be blamed on, per Forensics rank 4.
    framed: str = ''

    #: The runner you are covering on an escort job, as
    #: {key, name, node, integrity, state, done}. Their noise is not your
    #: decision, which is the entire design of the objective.
    escort: dict | None = None
    #: A rival you paid to run alongside you, as
    #: {key, name, node, integrity, state, skill, style, cut}. The mirror of
    #: `escort`: this one is here to help, and takes a share of the haul.
    ally: dict | None = None
    #: Set once the network's own wake-up line has been used. It is written
    #: per faction and it is strong, so it fires once rather than every time.
    woken: bool = False
    #: Ex-enforcement Playbook: every construct telegraphs a tick early.
    playbook: bool = False
    #: Chromed Native: ticks of moving through the net as a room.
    native: int = 0
    #: Indentured Requisition: a program borrowed for this run only.
    requisitioned: str = ''
    #: The last crack that failed, as (node, service), for Burnout Remember.
    last_failure: tuple | None = None
    #: Ticks of Dissociate remaining: damage lands on the deck, and black ICE
    #: cannot reach you at all.
    dissociated: int = 0
    #: Overclock credits: each real tick spent at N steps earns N of them,
    #: and each pays for one tick of a later action. See `_act`.
    oc_credit: float = 0.0
    #: Actions that cost no ticks, spent before ordinary ones. The Chromed
    #: origin opens a run with one.
    free_actions: int = 0
    #: Consecutive ticks of clean residency, for a surveil job. Reset by the
    #: alert going red, because being watched is the opposite of watching.
    observed: int = 0
    #: Set once a surveil job has banked enough. Latches: having held it, you
    #: have held it, and the walk back out cannot take it away.
    observed_enough: bool = False
    #: Whether `jack out` has already pointed out that the job is unfinished.
    #: Once per run: the second time you type it, you mean it.
    warned_incomplete: bool = False
    #: Hosts you have scanned *from*. A scan reveals the neighbourhood of
    #: wherever you are standing, so scanning twice from one host is the same
    #: answer twice, and knowing that is the difference between advice that
    #: searches a network and advice that walks between two hosts forever.
    scanned: set = field(default_factory=set)

    outcome: str = 'running'
    #: Human-readable record, shown by `log` and after the run.
    events: list[str] = field(default_factory=list)
    #: Tonight's condition (D61), or None for an ordinary night. Typed
    #: loosely: it is a `conditions.Condition` and this module does not need
    #: to know more than its fields.
    condition: object = None
    #: Constructs whose portrait has been shown (D62). Once each.
    portrayed: set = field(default_factory=set)
    #: Fractions of a tick owed or owing (D63). A `tick_mult` of 0.95 used
    #: to round away on every one-, two- and three-tick verb, which made the
    #: two cheapest upgrades in the catalogue cosmetic; now the five percent
    #: is banked and the twentieth tick is free. Negative is drag owed.
    tick_bank: float = 0.0
    #: Free actions banked by Tempo (D63). Tempo was printed on the sheet and
    #: read by nothing; now every real tick spent banks a fraction of an
    #: action, and a whole one pays for the next verb. See `TEMPO_RATE`.
    tempo_bank: float = 0.0
    #: Actions taken since the clock last moved, for the Salvaged Reflex
    #: Loop's misfire; and every action taken tonight, which only ever goes
    #: up. A free action moves the second and not the clock, so anything
    #: asking "did the game attempt that" reads `actions`, not `tick`.
    acted_this_tick: int = 0
    actions: int = 0
    #: The Nightwatch serial has been checked against the list. Once.
    serial_checked: bool = False
    #: Hits the loaded armour has absorbed tonight (D63). An armour program
    #: is good for as many saves as its rating, and then it is gone.
    armour_wear: int = 0
    #: Constructs that have tried to lock on and missed, so that the same
    #: evade line is not printed every tick they retry.
    evaded: set = field(default_factory=set)
    #: The host you came from (D63 b). A herder that knows it cuts the way
    #: back rather than a random edge, which is what herding is.
    previous: str = ''
    #: Times `mask` has been used tonight. See `MASK_DECAY`.
    masked: int = 0
    #: Consecutive ticks in which you have made no noise anywhere. At
    #: `QUIET_TO_COOL` the network stands down a level (D66).
    quiet_ticks: int = 0
    #: Ticks since anything new was filed against you. At `COOL_AFTER` the
    #: ticket ages out and the room stands down a level.
    since_filed: int = 0
    #: Set by `make_noise` and cleared each tick, so the tick knows.
    noisy_tick: bool = False
    #: Tick the last incident fired on, and what is attached to the run
    #: right now because of one (D77).
    incident_at: int = -99
    hook: str = ''
    seen_incidents: set = field(default_factory=set)
    #: Hosts already scrubbed once, so the brief advises it once and does
    #: not stand there advising it against a check that keeps missing.
    scrubbed: set = field(default_factory=set)
    #: (host, service) -> how many times a crack on it has held. Three
    #: and the brief looks at another door first (D91): eight identical
    #: attempts at amber were a long shot become a way of life.
    failed: dict = field(default_factory=dict)
    #: (verb, host) pairs a technique has already been tried on. The brief
    #: offers a technique as an opening move, once; if the check misses,
    #: the ordinary advice takes over rather than standing there repeating
    #: an expensive verb at a door that is not opening (D78).
    tried: set = field(default_factory=set)
    #: Ticks an implant still needs before it has taken (D80). An implant
    #: that is pushed and abandoned is a thing left on a desk.
    rooting: int = 0
    #: Ticks of `brace` left, and what is holding the line (D81). The one
    #: answer to a countermeasure that needs no rank.
    braced: int = 0
    bracing_with: str = ''
    #: Guard against `_salvage_step` and `_nothing_left` calling each
    #: other for ever (D82).
    _salvaging: bool = False
    #: Assets pulled shut, without the decrypt (D63 b). Worth less, and the
    #: patron pays less for the one they wanted open.
    sealed: set = field(default_factory=set)

    # ------------------------------------------------------------------
    # construction
    # ------------------------------------------------------------------

    @classmethod
    def begin(cls, net: Network, char: Character, rng: Stream,
              console: Console, contract: dict | None = None,
              phase: str = 'morning', condition=None) -> RunState:
        state = cls(net=net, char=char, rng=rng, console=console,
                    contract=contract, here=net.entry, phase=phase,
                    condition=condition)
        state.focus = char.focus
        node = net.node(net.entry)
        if node:
            node.known = node.open = node.mapped = True
        riders = char.riders()
        if 'slow_start' in riders:
            # Overprepared: you begin every run sorting through what you
            # brought, and it costs you the first tick.
            state.tick = 1
            state.trace = TRACE_PER_TICK * char.mult('trace_mult')
        if 'veteran_eye' in riders:
            # Been here before: you have seen all of this, traps included.
            for other in net.nodes.values():
                for construct in other.ice:
                    construct.known = True
        if 'native' in riders:
            # The net is your first language. One action already spent before
            # anybody else has finished arriving.
            state.free_actions = 1
        # The one with your name on it has been waiting (D89).
        for other in net.nodes.values():
            for construct in other.ice:
                if construct.grudge and construct.state == 'dormant':
                    construct.state = 'awake'
        if 'nightwatch_serial' in riders and net.faction == 'nightwatch':
            # Issue hardware with an issue serial (D63). Their network reads
            # it as one of their own and opens a tier to it, right up until
            # the first construct that files on you checks the number.
            state.tier += 1
            console.say('[info]Something in you answers to a Nightwatch '
                        'serial, and the perimeter reads you as staff. '
                        'Until somebody checks the list.[/]')
        return state

    # ------------------------------------------------------------------
    # convenience
    # ------------------------------------------------------------------

    @property
    def node(self) -> Node:
        return self.net.nodes[self.here]

    @property
    def running(self) -> bool:
        return self.outcome == 'running'

    @property
    def trace_pct(self) -> float:
        return min(1.0, self.trace / TRACE_MAX)

    @property
    def blind_trace(self) -> bool:
        """The Ghost Layer rider: you cannot read your own exact trace."""
        return 'blind_trace' in self.char.riders()

    def trace_label(self) -> str:
        if not self.blind_trace:
            return f'{int(self.trace)}/{int(TRACE_MAX)}'
        pct = self.trace_pct
        band = ('faint', 'building', 'close', 'imminent')[
            min(3, int(pct * 4))]
        return band

    @property
    def residue_total(self) -> int:
        return sum(n.residue for n in self.net.nodes.values())

    def log(self, text: str) -> None:
        self.events.append(text)

    # ------------------------------------------------------------------
    # the three quantities
    # ------------------------------------------------------------------

    def make_noise(self, amount: float, node: Node | None = None) -> int:
        """Local suspicion, and the slice of it that becomes trace."""
        node = node or self.node
        if amount > 0:
            self.noisy_tick = True
        # The character's own noise_mult already carries chrome riders like the
        # Threadpuller's doubling, because those are declared as penalties.
        amount *= self.char.mult('noise_mult') * node.data_type.noise_mult
        if self.condition is not None:
            amount *= self.condition.noise
        # What you are carrying is not free to carry (D80). An exfiltration
        # used to be over the moment you had it in hand, and the walk back
        # out was the same walk in with a different destination. The record
        # they want is the loudest thing on this network and it is now in
        # your traffic: everything you do on the way out says so.
        if self.net.objective_asset in self.haul:
            amount *= HAUL_NOISE
        value = max(0, int(round(amount)))
        node.noise += value
        if value:
            self.add_trace(value * NOISE_TO_TRACE)
        return value

    def add_trace(self, amount: float) -> None:
        if self.nullsig > 0:
            return
        amount *= self.char.mult('trace_mult')
        amount *= ice_content.ALERT_TRACE_MULT[self.alert]
        # Cover traffic. At peak there are ten thousand legitimate sessions to
        # sort you out of, and at three in the morning there is one.
        amount *= shifts.phase(self.phase).trace
        # And the size of the place is itself cover (D66): a session in a
        # network of twenty hosts is one of a great many more.
        amount *= self.net.crowd
        # Tonight (D61): a maintenance window logs more, dead hours less.
        if self.condition is not None:
            amount *= self.condition.trace
        self.trace = min(TRACE_MAX, self.trace + max(0.0, amount))

    def leave_residue(self, amount: float, node: Node | None = None) -> int:
        node = node or self.node
        amount *= self.char.mult('residue_mult')
        if ('policy_reader' in self.char.riders()
                and fac_content.BY_KEY[self.net.faction].kind == 'corp'):
            # Policy reader: you know what corporate networks log and when.
            amount *= 0.85
        if self.condition is not None:
            amount *= self.condition.residue
        # Freeport logs in public (D63 b): the faction's style.
        amount *= self.style('residue')
        # D63: a construct that declares `residue_mult` is one that files.
        # While an Auditor is awake on a host, everything done there leaves
        # more behind; the rider was declared on the type and read nowhere.
        for construct in node.ice:
            if construct.state in ('awake', 'locked'):
                amount *= float(construct.data.effects.get('residue_mult', 1.0))
        value = max(0, int(round(amount)))
        node.residue += value
        return value

    def style(self, key: str) -> float:
        """One of the target faction's style knobs (D63 b), default 1.0."""
        fac = fac_content.BY_KEY.get(self.net.faction)
        return float(fac.style.get(key, 1.0)) if fac else 1.0

    def _portrait(self, construct) -> None:
        """Its mark, beside its name, the first time it wakes and you know
        what it is (D62). Once per construct; a portrait that printed on every
        wake would be wallpaper."""
        if not construct.known or construct.uid in self.portrayed:
            return
        rows = ice_content.portrait(
            construct.behaviour,
            self.console.caps.glyphs is ui.GlyphLevel.ASCII)
        if not rows:
            return
        self.portrayed.add(construct.uid)
        role = 'err' if construct.behaviour == 'black' else 'ice'
        self.console.blank()
        for i, row in enumerate(rows):
            tail = (f'   [dim]{construct.data.name}, {construct.behaviour}, '
                    f'rating {construct.rating}[/]' if i == 1 else '')
            self.console.raw(f'  [{role}]{row}[/]{tail}')

    def _ghost_tick(self) -> None:
        """The other runner (D61). Noise on a node you can see, not yours."""
        from ..content import conditions as cond_content
        if not self.rng.chance(cond_content.GHOST_CHANCE):
            return
        others = [n for n in self.net.nodes.values()
                  if n.known and n.uid != self.here]
        if not others:
            return
        node = self.rng.pick(others)
        node.noise += cond_content.GHOST_NOISE
        self.log(f'something else moved on {node.uid}')
        self.console.say(f'[dim]Something else moves, on {node.uid}. '
                         f'Not you.[/]')

    def wake_threshold(self, construct) -> int:
        """Noise a countermeasure needs on its node before it wakes.

        The rating makes the good ones light sleepers; tonight's condition
        (D61) moves the whole table, and never below two, so that nothing
        ever wakes at nothing.
        """
        base = max(3, NOISE_WAKE - construct.rating)
        if self.condition is not None and self.condition.wake:
            base = max(2, base + self.condition.wake)
        return base

    def _response(self) -> None:
        """Nightwatch send somebody (D67).

        Their doctrine has always said their networks are lightly defended
        and extremely well watched and that the ICE arrives rather than
        waiting, and nothing in the generator did any of that. Once a run,
        when the room turns red, something turns up on the host you are
        standing on, awake, and it did not come up through the network.
        """
        if (self.net.faction != 'nightwatch' or self.alert != 'red'
                or 'arrived' in self.spent):
            return
        self.spent.add('arrived')
        pool = ice_content.available('hunter', 'nightwatch')
        if not pool:
            return
        data = self.rng.pick(pool)
        lo, hi = data.rating
        self.node.ice.append(IceInstance(
            uid=f'{data.key}-call', key=data.key,
            rating=max(1, self.rng.int(lo, hi)), state='awake', known=True))
        self.console.blank()
        self.console.raw(f'[err]Something has been sent. {data.name} is on '
                         f'{self.here}, awake, and it did not come up '
                         f'through the network.[/]')
        self.familiar_say('blackice')
        self.log(f'nightwatch sent {data.name}')

    def cool(self) -> None:
        """The network stands down one level. Never below green, and the
        quiet has to be earned again for the next one."""
        levels = ice_content.ALERT_LEVELS
        i = levels.index(self.alert)
        if i <= 0:
            return
        self.alert = levels[i - 1]
        self.char.deck.alert = self.alert
        self.quiet_ticks = 0
        self.since_filed = 0
        self.console.blank()
        self.console.say(f'[ok]{self.rng.pick(ice_content.COOLING)}[/]')
        self.console.raw(f'[ok]Alert: {self.alert}.[/] '
                         f'[dim]{ice_content.ALERT_BLURB[self.alert]}[/]')
        self.log(f'alert cooled -> {self.alert}')

    def familiar_say(self, event: str) -> None:
        """A digital pet riding the deck says what it makes of the run (D153).
        Cosmetic to the bone: it reads nothing, changes nothing, and only
        ever prints a line. On connect it wakes, which is the one bit of
        state it has."""
        from ..content import pets as pet_content
        fam_state = self.char.deck.familiar
        if not fam_state:
            return
        fam = pet_content.FAMILIAR_BY_KEY.get(fam_state.get('key', ''))
        if fam is None:
            return
        if event == 'connect':
            dormant = int(fam_state.get('idle', 0)) >= pet_content.FAMILIAR_DORMANT_AFTER
            fam_state['idle'] = 0
            key = 'dormant' if dormant else 'connect'
        else:
            key = event
        lines = fam.says.get(key)
        if not lines:
            return
        self.console.blank()
        self.console.say(f'[dim]{self.rng.pick(lines)}[/]')

    def escalate(self, steps: int = 1, why: str = '') -> None:
        levels = ice_content.ALERT_LEVELS
        i = levels.index(self.alert)
        if ('read_the_room' in self.char.riders()
                and self.net.faction == 'nightwatch'):
            # Read the room: you know their escalation playbook.
            if self.rng.chance(0.5):
                return
        new = min(len(levels) - 1, i + steps)
        if new == i:
            return
        self.alert = levels[new]
        self.char.deck.alert = self.alert
        self.since_filed = 0
        self._response()
        # The room turning red is the tensest beat in a run, so the screen
        # takes it (D116). Only on the crossing into red, so a run that is
        # already red does not stutter on every further step.
        if (self.alert in ('red', 'lockdown')
                and levels[i] not in ('red', 'lockdown')):
            self._disrupt(frames=5, height=4)
        self.console.blank()
        self.console.raw(f'[err][bold]ALERT: {self.alert.upper()}[/][/]  '
                         f'[dim]{ice_content.ALERT_BLURB[self.alert]}[/]')
        self.familiar_say(self.alert)
        if why:
            self.console.say(f'[dim]{why}[/]')
        if self.alert in ('red', 'lockdown') and self.tick > 0:
            # D63: Composure was read once, at the moment of dying. Now it
            # is read when the room turns. A printed check; a failure is a
            # tick lost to standing still, which is what panic costs.
            steady = Check(name='keep your head', resistance=12)
            steady.add('composure', self.char.composure)
            steady.add('nerve', self.char.attr('nerve'))
            steady.resolve(self.rng)
            if not steady.success:
                self.console.say(f'[warn]You freeze.[/] [dim]{steady.summary()}'
                                 f' A tick goes by before your hands '
                                 f'remember what they are for.[/]')
                self.log('froze at the alert')
                self.advance(1)
        # What it costs and what answers it, once per level. A banner that
        # only says something bad has happened leaves the player to guess
        # whether the move is to leave, to hurry, or to carry on, and the
        # commonest guess is to leave immediately with nothing.
        advice = ice_content.ALERT_ADVICE.get(self.alert, '')
        if advice:
            self.console.say(f'[warn]{advice}[/]')
        self.log(f'alert -> {self.alert}' + (f' ({why})' if why else ''))

    # ------------------------------------------------------------------
    # the tick
    # ------------------------------------------------------------------

    def advance(self, ticks: int = 1) -> None:
        """Spend time. Everything that is not the player's decision happens here."""
        cost = self.char.mult('tick_mult') * self.drag
        # D63: the fraction is banked rather than rounded. A multiplier of
        # 0.9 is a tick back every tenth tick, exactly; 1.15 is a tick owed
        # every seventh. Nothing is free until the bank says so, and drag is
        # paid the moment a whole tick of it is owed.
        real = ticks
        if ticks and cost != 1.0:
            self.tick_bank += ticks * (1.0 - cost)
            # A hair of tolerance: 0.95 times its own reciprocal is not 1.0
            # in floating point, and a bank that owes 0.9999 forever is a
            # multiplier that never quite counts.
            while self.tick_bank >= 1.0 - 1e-9 and real > 0:
                self.tick_bank -= 1.0
                real -= 1
            while self.tick_bank <= -1.0 + 1e-9:
                self.tick_bank += 1.0
                real += 1
        if real <= 0:
            # Two free-action lines read as one mechanism with two moods
            # (D90). This one is the clock running slow for you: chrome or
            # a condition that makes your ticks cheaper, banked until a
            # whole one is owed. Tempo's line is the other.
            self.console.say('[dim]Quick. That one cost nothing: your ticks '
                             'run short of the clock, and the bank just '
                             'paid one.[/]')
            return
        self.acted_this_tick = 0
        for _ in range(real):
            if not self.running:
                return
            self.tick += 1
            self.last_hit_by = ''
            was = self.trace_pct
            self.add_trace(TRACE_PER_TICK if self.noisy_tick else IDLE_TRACE)
            self.trace_history.append(round(self.trace, 2))
            del self.trace_history[:-TRACE_HISTORY]
            # The clock made physical. One line at most, and only on a
            # threshold, because narrating every point of trace would turn
            # the tensest number in the game into wallpaper.
            # Quiet buys the room back (D66). A tick in which you made no
            # noise anywhere counts; enough of them in a row and whatever
            # was watching this hard stands down a level.
            if self.noisy_tick:
                self.quiet_ticks = 0
                self.noisy_tick = False
            else:
                self.quiet_ticks += 1
            self.since_filed += 1
            if self.alert != ice_content.ALERT_LEVELS[0] and (
                    self.quiet_ticks >= ice_content.QUIET_TO_COOL
                    or self.since_filed >= ice_content.COOL_AFTER):
                self.cool()
            felt = cyberspace.pressure(was, self.trace_pct)
            if felt:
                self.console.blank()
                self.console.say(f'[trace]{felt}[/]')
            if self.condition is not None and self.condition.ghost:
                self._ghost_tick()
            if self.nullsig > 0:
                self.nullsig -= 1
                if self.nullsig == 0:
                    self.console.info('Nullsig window closes. You are visible again.')
            if self.native > 0:
                self.native -= 1
                if self.native == 0:
                    self.console.info('You are using the interface again.')
            if self.dissociated > 0:
                self.dissociated -= 1
                if self.dissociated == 0:
                    self.console.info('You come back into it. Everything that '
                                      'was waiting is still waiting.')
            if self.impersonating > 0:
                self.impersonating -= 1
                if self.impersonating == 0:
                    self.console.info('The credential stops holding. You are '
                                      'yourself again.')
            self._heat_tick()
            self._daemon_tick()
            self._escort_tick()
            self._ally_tick()
            if self.braced > 0:
                self.braced -= 1
                if self.braced == 0:
                    self.bracing_with = ''
            self._ice_tick()
            self._incident_tick()
            self._response_tick()
            self._rival_race_tick()
            self._surveil_tick()
            self._root_tick()
            self._decay_noise()
            self._check_trace()

    def _daemon_tick(self) -> None:
        """Autonomous processes act before ICE does.

        Order matters: a diversion daemon has to make its noise *before* the
        Probe decides where to look, or it is decoration rather than a tactic.
        """
        for daemon in list(self.daemons):
            node = self.net.node(daemon['node'])
            if node is None:
                self.daemons.remove(daemon)
                continue
            daemon['life'] -= 1
            prog = programs.BY_KEY.get(daemon['program'])
            if 'choir_noise' in self.char.riders():
                # A Choirmaster runs them together, which means their noise
                # is filed against your session rather than the node's
                # (D69). You own what they do.
                self.make_noise(1, self.node)
            if prog is not None and prog.rider == 'handbill_tick':
                # The cheapest daemon on the market answers for the node out
                # loud, on a timer, whether or not that is convenient (D69).
                daemon['beat'] = daemon.get('beat', 0) + 1
                if daemon['beat'] % 2 == 0:
                    self.make_noise(4, node)
                    self.console.say(f'[dim]{daemon["uid"]} answers for '
                                     f'{node.uid}, at volume, on its own '
                                     f'schedule.[/]')
            rating = prog.rating if prog else 2

            # A scripted daemon re-decides what it is doing every tick by
            # running its script as a policy: the first step whose condition
            # holds names the task. This is the top of the Daemonology arc,
            # where rank 2 writes the automation and rank 4 sets it loose.
            if daemon['task'] == 'script':
                chosen = self._daemon_policy(daemon)
                if chosen is None:
                    daemon['life'] = 0
                    self.console.info(f'{daemon["uid"]} stops itself.')
                    self.daemons.remove(daemon)
                    continue
                effective, arg = chosen
                daemon['acting'] = effective
                daemon['arg'] = arg or daemon.get('arg', '')
            else:
                effective = daemon['task']

            if ('mirror_confusion' in self.char.riders()
                    and self.rng.chance(MIRROR_HESITATION)):
                # The Mirror icon reflects allies too (D63): a daemon that
                # cannot tell which of you is you does nothing this tick.
                self.console.say(f'[dim]{daemon["uid"]} hesitates. It cannot '
                                 f'tell which of you is you.[/]')
                continue

            if effective == 'hold':
                # Keeps a node quiet by absorbing the traffic you generated.
                node.noise = max(0, node.noise - (1 + rating // 2))
            elif effective == 'grind':
                svc = node.service(daemon.get('arg', ''))
                if svc and not svc.cracked:
                    daemon['progress'] = daemon.get('progress', 0) + rating
                    if daemon['progress'] >= svc.difficulty * 3:
                        svc.cracked = True
                        node.open = True
                        self.console.blank()
                        self.console.ok(f'[dim]{daemon["uid"]}:[/] '
                                        f'{svc.data.name} on {node.uid} gave way.')
                        daemon['life'] = 0
                elif svc is None or svc.cracked:
                    daemon['life'] = 0
            elif effective == 'noise':
                # A diversion: loud somewhere you are not.
                node.noise += 2 + rating
                for construct in node.live_ice:
                    if construct.behaviour == 'probe' and construct.state == 'dormant':
                        construct.state = 'awake'
                        self._portrait(construct)
            # Daemons are not free. They announce themselves where they sit.
            if prog:
                self.add_trace(prog.signature * 0.4)

            if daemon['life'] <= 0:
                self.daemons.remove(daemon)
                self.console.info(f'{daemon["uid"]} has finished and gone.')

    def _decay_noise(self) -> None:
        for node in self.net.nodes.values():
            if node.noise:
                node.noise = max(0, node.noise - NOISE_DECAY)

    def _heat_tick(self) -> None:
        if self.overclock <= 0:
            return
        headroom = self.char.deck.heat_headroom
        load = self.overclock * 4
        if load <= headroom:
            return
        over = load - headroom
        self.add_trace(over * 0.4)
        if self.rng.chance(min(0.6, over * 0.08)):
            slot = self.rng.pick(list(self.char.deck.parts))
            level = self.char.deck.hurt(slot, 1)
            self.console.warn(f'Thermal damage to the {slot} '
                              f'[dim](damage {level}/3)[/].')
            self.log(f'thermal damage: {slot}')
        if 'thermal_load' in self.char.riders():
            # The coolant mesh routes heat through you. That has a price.
            self.take_damage(1, black=False, source='thermal load')

    #: How many ticks of clean residency a surveil contract wants.
    SURVEIL_TICKS = 8

    #: Ticks an implant needs on the network before it has taken (D80).
    #: You do not have to stand over it. You do have to still be in here.
    ROOT_TICKS = 5

    def _escort_tick(self) -> None:
        """The runner you are covering acts, and you did not choose how.

        This is the whole point of the objective. An escort moves toward the
        job on their own schedule, works loudly when they get there, and
        panics when hurt. The player's problem is not "get to the vault", it is
        "somebody else is generating your noise budget and will not stop".
        """
        escort = self.escort
        if not escort or escort['state'] in ('out', 'dead'):
            return
        node = self.net.node(escort['node'])
        if node is None:
            return

        if escort['state'] == 'hold':
            # Held in place. Still breathing, still faintly audible.
            node.noise += 1
            return

        target = self.net.objective_node
        if escort['done'] or escort['state'] == 'leaving':
            self._escort_walk(escort, self.net.entry, leaving=True)
            return

        self._escort_exposure(escort)
        if escort['state'] in ('out', 'dead', 'hold'):
            return
        node = self.net.node(escort['node']) or node

        if escort['node'] == target:
            escort['progress'] = escort.get('progress', 0) + 1
            # Working is loud, and they are not being careful about it.
            node.noise += 4
            self.leave_residue(3, node)
            if escort['progress'] == 1:
                self.console.blank()
                self.console.say(f'[info]{escort["name"]} starts working on '
                                 f'{node.uid}. They are not being quiet '
                                 f'about it.[/]')
            if escort['progress'] >= 4:
                escort['done'] = True
                escort['state'] = 'leaving'
                self.console.blank()
                self.console.ok(f'{escort["name"]} has what they came for. '
                                f'They are heading out.')
        else:
            self._escort_walk(escort, target)

    #: What a daemon is allowed to be told to do. Deliberately the same three
    #: tasks it has always had: a script sets the *policy*, it does not hand a
    #: daemon the player's whole verb set.
    DAEMON_TASKS = ('hold', 'grind', 'noise')

    def _daemon_policy(self, daemon: dict):
        """Which task this daemon should perform this tick, or None to stop.

        The script is read as a policy rather than a program: the first step
        whose condition holds names the task, and a `stop if` that fires ends
        the daemon. That keeps an autonomous process autonomous instead of
        letting it puppet the player around the network.
        """
        from ..script import ScriptError, parse

        try:
            steps = parse(daemon.get('lines') or [])
        except ScriptError:
            return None
        for step in steps:
            if step.condition is not None:
                truth = step.condition.evaluate(self)
                if step.kind == 'stop':
                    if truth:
                        return None
                    continue
                if not truth:
                    continue
            elif step.kind == 'stop':
                continue
            head, _, rest = step.command.strip().partition(' ')
            head = head.lower()
            if head in self.DAEMON_TASKS:
                return head, rest.strip()
        return 'hold', ''

    def _ally_tick(self) -> None:
        """The runner you hired keeps up, and earns their fee passively.

        An ally is deliberately low-maintenance. You are paying for a standing
        bonus and a body between you and the ICE, not for a second character to
        micromanage: the game already has one companion that needs managing and
        it is the escort, which is a whole objective.
        """
        ally = self.ally
        if not ally or ally['state'] in ('out', 'dead'):
            return
        if ally['node'] == self.here:
            if ally['style'] == 'quiet':
                # They keep the room quiet around you.
                self.node.noise = max(0, self.node.noise - 2)
            return
        # Otherwise close the distance. They are competent and they know where
        # you are, so they do not open doors or make noise doing this.
        path = self._path(ally['node'], self.here)
        if path:
            ally['node'] = path[0]

    def ally_bonus(self, kind: str) -> int:
        """What a co-located ally adds to a check of this kind."""
        ally = self.ally
        if not ally or ally['state'] != 'with you' or ally['node'] != self.here:
            return 0
        style = ally['style']
        if kind == 'crack' and style == 'loud':
            return ally['skill']
        if kind == 'social' and style == 'social':
            return ally['skill']
        if kind == 'trap' and style == 'careful':
            return ally['skill'] // 2
        return 0

    def hurt_ally(self, amount: int, source: str = '') -> None:
        ally = self.ally
        if not ally or ally['state'] in ('out', 'dead'):
            return
        ally['integrity'] -= amount
        if ally['integrity'] > 0:
            self.console.warn(f'{ally["name"]} takes it for you. '
                              f'[dim]{ally["integrity"]} left.[/]')
            return
        ally['state'] = 'dead'
        self.console.blank()
        self.console.raw(f'[err][bold]{ally["name"]} does not come back up.[/][/]')
        self.console.say('[dim]You paid them a fee this morning and they are '
                         'still holding the receipt.[/]')
        self.log(f'ally dead: {ally["name"]}')

    def _escort_exposure(self, escort: dict) -> None:
        """Countermeasures where *they* are standing, not where you are.

        Without this the correct play on an escort job is to ignore the escort
        entirely and let them walk the network alone, which is the exact
        opposite of what the objective is for. They are in danger wherever they
        are; the player's counterplay is to hold them still, clear the road
        ahead, or be standing there to take it instead.
        """
        node = self.net.node(escort['node'])
        if node is None:
            return
        # Two constructs waking on the same node in the same tick is one
        # event to the player, not two identical lines.
        announced = False
        for construct in node.live_ice:
            if construct.behaviour == 'trap':
                continue
            threshold = self.wake_threshold(construct)
            if node.noise < threshold:
                continue
            if construct.state == 'dormant':
                construct.state = 'awake'
                self._portrait(construct)
                if not announced:
                    announced = True
                    self.console.blank()
                    self.console.say(
                        f'[ice]Something on {node.uid} has noticed '
                        f'{escort["name"]}.[/]')
                continue
            # If you are standing with them, you can take it instead.
            if self.here == escort['node'] and self.rng.chance(0.5):
                return
            data = construct.data
            if data.behaviour in ('hunter', 'warden', 'black'):
                self.hurt_escort(data.damage + construct.rating // 2, data.name)
            else:
                self.add_trace(data.trace)
                self.escalate(1, f'{data.name} reported {escort["name"]}.')
            return

    def _escort_walk(self, escort: dict, target: str, leaving: bool = False) -> None:
        """One hop along the shortest path, opening what they have to."""
        path = self._path(escort['node'], target)
        if not path:
            return
        nxt = self.net.nodes[path[0]]
        # They open their own doors, badly. A failure costs them a tick and
        # makes a great deal of noise on a node they are standing on, which is
        # the mechanism by which an unmanaged escort walks into trouble.
        if not nxt.open:
            skill = escort.get('skill', 6)
            if self.rng.int(1, 10) + skill >= 11:
                nxt.open = True
                for svc in nxt.services[:1]:
                    svc.cracked = True
                nxt.noise += 5
                self.leave_residue(2, nxt)
            else:
                node = self.net.node(escort['node'])
                if node:
                    node.noise += 7
                    self.leave_residue(2, node)
                return
        escort['node'] = nxt.uid
        nxt.noise += 2
        if leaving and nxt.uid == self.net.entry:
            escort['state'] = 'out'
            self.console.blank()
            self.console.ok(f'{escort["name"]} is out.')

    def _path(self, start: str, goal: str) -> list[str]:
        """Shortest hop list from start to goal, excluding start."""
        if start == goal:
            return []
        frontier = [(start, [])]
        seen = {start}
        while frontier:
            uid, path = frontier.pop(0)
            for edge in self.net.nodes[uid].edges:
                if edge in seen:
                    continue
                if edge == goal:
                    return path + [edge]
                seen.add(edge)
                frontier.append((edge, path + [edge]))
        return []

    def hurt_escort(self, amount: int, source: str = '') -> None:
        """ICE found the person you are covering instead of you."""
        escort = self.escort
        if not escort or escort['state'] in ('out', 'dead'):
            return
        escort['integrity'] -= amount
        if escort['integrity'] > 0:
            self.console.blank()
            self.console.warn(f'{escort["name"]} takes it. '
                              f'[dim]{escort["integrity"]} left.[/]')
            if escort['integrity'] <= 6 and escort.get('panic'):
                self.console.say(f'[err]{escort["panic"]}[/]')
                escort['state'] = 'leaving'
            return
        escort['state'] = 'dead'
        self.console.blank()
        self.console.raw(f'[err][bold]{escort["name"]} flatlines on the far '
                         f'end of the connection.[/][/]')
        self.console.say('[dim]There is a sound over the shared channel that '
                         'you will be able to describe for years.[/]')
        self.log(f'escort dead: {escort["name"]}')

    def _surveil_tick(self) -> None:
        """Bank a tick of clean residency, or lose the lot.

        Deliberately fragile at the top end: a surveil job asks you to be
        somewhere valuable and do nothing, and the temptation to take one more
        thing while you are there is the whole tension.
        """
        if not self.contract or self.contract.get('objective') != 'surveil':
            return
        if self.here != self.net.objective_node:
            return
        if self.alert in ('red', 'lockdown'):
            if self.observed:
                self.console.warn('They are looking. Whatever you were '
                                  'listening to has stopped being said.')
            self.observed = 0
            return
        self.observed += 1
        if self.observed >= self.SURVEIL_TICKS and not self.observed_enough:
            self.observed_enough = True
            self.console.blank()
            self.console.ok('You have enough. Every minute past this is a '
                            'minute you are spending for free.')

    def opened(self, node) -> None:
        """A host just opened. The one place that fact is announced to the
        rest of the run, so an incident can wait for it (D77)."""
        if self.hook == 'tail':
            self.hook = ''
            woke = [c for c in node.ice if c.alive and c.state == 'dormant']
            self.console.say('[err]The mark on your route arrives with '
                             'you.[/]')
            for construct in woke:
                construct.state = 'awake'
                self._tell(construct)
            if not woke:
                self.console.say('[dim]There was nothing in here to find '
                                 'you. This time.[/]')

    def _response_tick(self) -> None:
        """Something is dispatched (D92).

        Escalation was a trace multiplier and nothing else: three runs sat
        at red for sixteen ticks on a route whose only live constructs
        were sentries, and the only thing that ever ended a night was the
        clock. So a room that stays red long enough gets a hunter, from
        the faction's own pool, on the host you are standing on, awake,
        with a tell. Once a run. Only from factions that field hunters,
        which is doctrine (D63 b): a gang phone tree has nobody to send.
        Counts loud ticks: a watch that goes quiet at red and waits it
        out is doing the right thing and is not punished for it.
        """
        if self.alert not in ('red', 'lockdown'):
            self.red_ticks = 0
            return
        # Loud ticks only at red: going quiet is the answer the brief
        # gives, and the response is for people who keep working under
        # it, not for people waiting it out. At lockdown every tick
        # counts, loud or not: lockdown is the response, and a rule
        # nobody ever met is not a rule (D97: zero dispatches in seventeen
        # corporate runs).
        # Loud ticks only, at both levels (D101: counting quiet ticks at
        # lockdown summoned the hunter the tick after the brief said
        # wait). Lockdown is quicker about it.
        if self.noisy_tick:
            self.red_ticks += 1
        after = (RESPONSE_AFTER_LOCKDOWN if self.alert == 'lockdown'
                 else RESPONSE_AFTER)
        if self.responded or self.red_ticks < after:
            return
        pool = ice_content.available('hunter', self.net.faction)
        if not pool:
            return
        self.responded = True
        it = self.rng.pick(pool)
        lo, hi = it.rating
        scale = self.net.posture / 50.0
        fac = fac_content.BY_KEY.get(self.net.faction)
        density = fac.style.get('density', 1.0) if fac else 1.0
        rating = max(2, int(round(self.rng.int(lo, hi) * (0.75 + 0.5 * scale)
                                  * density)))
        construct = IceInstance(uid=f'{it.key}-sent', key=it.key,
                                rating=rating, state='awake', known=True)
        self.node.ice.append(construct)
        self.console.blank()
        self.console.say(f'[ice]Something has been dispatched. It is not '
                         f'looking for the noise any more; it is looking '
                         f'for you.[/]')
        self.console.say(f'[dim]{it.name}, {it.behaviour}, rating {rating}, '
                         f'on {self.here}. `connect` off this host, `strike` '
                         f'it, or `mask`: it acts the tick after it '
                         f'tells.[/]')
        self.log(f'response: {it.name}')

    def _incident_tick(self) -> None:
        """Something the network does on its own clock (D77).

        Rolled once a tick, after the countermeasures have had theirs, so
        an incident lands on the room as it actually is rather than on the
        room as it was at the top of the tick.
        """
        if self.tick < incident_content.GRACE or not self.running:
            return
        if self.tick - self.incident_at < incident_content.COOLDOWN:
            return
        chance = (incident_content.CHANCE
                  * incident_content.BY_ALERT.get(self.alert, 1.0))
        if not self.rng.chance(min(0.5, chance)):
            return
        pick = self._incident_pool()
        if not pick:
            return
        weights = {i.key: i.weight for i in pick}
        it = incident_content.BY_KEY[self.rng.weighted(weights)]
        self.incident_at = self.tick
        self._apply_incident(it)

    def _incident_pool(self) -> list:
        """Which incidents belong in this room, at this moment."""
        fac = fac_content.BY_KEY.get(self.net.faction)
        kind = fac.kind if fac else ''
        node = self.node
        out = []
        for it in incident_content.INCIDENTS:
            if it.zones and node.zone not in it.zones:
                continue
            if it.kinds and kind not in it.kinds:
                continue
            if it.alert and self.alert not in it.alert:
                continue
            if it.needs_ice and not [c for c in node.ice if c.alive]:
                continue
            if it.needs_haul and not self.haul:
                continue
            if self.trace_pct < it.min_trace:
                continue
            if it.hook and self.hook:
                continue  # one attached thing at a time
            if it.key in self.seen_incidents and it.kind == 'good':
                continue  # a gift twice in one run is a discount
            if it.key == 'company' and (not self.rivals or self.company):
                continue  # one other session a night, and only if there is one
            out.append(it)
        return out

    def _company(self) -> None:
        """Somebody else is in here (D89).

        The other runners exist on the board and in the wire and never,
        until now, in the one place the game happens. Who it is comes
        from the city's roster; what it means comes from how they feel
        about you, which is the number `who` has always shown. Warm and
        their noise is your cover; cold and they tip the room; anything
        else and you read each other's scans and say nothing.
        """
        # Whoever has decided the most about you is who turns up: a nemesis
        # came for you (D120), a partner came for you too, the other way
        # (D121), and anybody else is the old roll of the dice.
        nem = next((r for r in self.rivals if r.get('bond') == 'nemesis'), None)
        par = next((r for r in self.rivals if r.get('bond') == 'partner'), None)
        who = dict(nem or par or self.rng.pick(self.rivals))
        name = who['name']
        disposition = int(who.get('disposition', 0))
        self.console.blank()
        if who.get('bond') == 'nemesis' or disposition <= -70:
            # In the one place it can actually cost you, and after the same
            # thing. Now it is a race, and the clock is the other half of it.
            who['kind'] = 'rival'
            self.console.rule('company', role='err')
            self.console.say(f'[ice]{name}. In here, on this, the same night '
                             f'you are, and not by accident. They are after '
                             f'what you are after, and they did not come '
                             f'second on purpose.[/]')
            self.escalate(1, f'{name} is working the room too')
            self.rival_race = who
            self.rival_lead = 0
        elif who.get('bond') == 'partner' or disposition >= 50:
            # The mirror of the race: they came to help, and they hand you
            # what the state you are in most needs.
            who['kind'] = 'boon'
            self._partner_boon(who)
        elif disposition >= 30:
            who['kind'] = 'cover'
            self.console.say(f'[ok]{name}. Their traffic is louder than '
                             f'yours, and it is on purpose.[/]')
            if not self.hook:
                self.hook = 'quiet'
                self.console.say(f'[warn]{incident_content.HOOKS["quiet"]}.[/]')
        elif disposition <= -30:
            who['kind'] = 'tip'
            self.console.say(f'[ice]{name}. They have seen you, and somebody '
                             f'upstairs is about to hear about it.[/]')
            self.escalate(1, f'{name} tipped them')
        else:
            who['kind'] = 'shared'
            self.console.say(f'[dim]{name}. Neither of you says anything. '
                             f'What they scanned, you can read.[/]')
            self._incident_reveal('hosts')
        self.company = who
        self.log(f'company: {name}')

    def _partner_boon(self, who: dict) -> None:
        """A partner turning up uninvited is the mirror of the nemesis race
        (D121): they came to help, and they hand you the thing the state you
        are actually in needs most. High trace, they pull the room's eye onto
        their own noise; a room already turning, they walk it the wrong way;
        otherwise they leave you what they found. A partner you have not signed
        is one `crew` away from being in every run, not the ones they wander
        into.
        """
        name = who['name']
        self.console.blank()
        self.console.rule('company', role='ok')
        if self.trace_pct >= 0.4:
            relief = min(self.trace, 14.0)
            self.trace = max(0.0, self.trace - relief)
            self.console.say(f'[ok]{name}. They make themselves the loudest '
                             f'thing in here on purpose, and the room turns to '
                             f'look at them instead of you.[/] '
                             f'[dim]trace -{relief:.0f}[/]')
        elif self.alert != ice_content.ALERT_LEVELS[0]:
            self.console.say(f'[ok]{name}. They walk something loud the wrong '
                             f'way down the hall, and whatever was deciding '
                             f'about you loses the thread.[/]')
            self.cool()
        else:
            self.console.say(f'[ok]{name}. They have been through here '
                             f'already, and they leave you what they found.'
                             f'[/]')
            self._incident_reveal('hosts')
        if who.get('bond') == 'partner':
            self.console.say(f'[dim]{name} would run every night with you, '
                             f'not just the ones they walk into. `crew` them, '
                             f'in the city.[/]')

    def _rival_race_tick(self) -> None:
        """A nemesis racing you gets closer to the objective every tick you
        spend not securing it (D120). Beat them to it and it is a win they
        will remember; be too slow and they take the part that mattered and
        leave the alarm behind them. Either way it is settled, and the run
        stops being a solo problem the moment they are in it.
        """
        race = self.rival_race
        if not race or self.rival_won:
            return
        if self.objective_met():
            self._rival_beaten(race)
            return
        self.rival_lead += 1
        if self.rival_lead == RIVAL_RACE_WARN:
            self.console.blank()
            self.console.say(f'[warn]{race["name"]} is moving fast in here. '
                             f'Whatever it is, they are closer to it than you '
                             f'are.[/]')
        elif self.rival_lead >= RIVAL_RACE_STEAL:
            self._rival_snatch(race)

    def _rival_beaten(self, race: dict) -> None:
        self.rival_race = {}
        self.rival_won = 'you'
        self.company['race'] = 'you'
        self.console.blank()
        self.console.rule('first', role='ok')
        self.console.say(f'[ok]You took it out from under {race["name"]}. They '
                         f'were fast. You were faster, tonight, and they '
                         f'watched you do it. They will not forget that you '
                         f'can.[/]')

    def _rival_snatch(self, race: dict) -> None:
        self.rival_race = {}
        self.rival_won = 'them'
        self.company['race'] = 'them'
        name = race['name']
        self.console.blank()
        self.console.rule('second', role='err')
        found = self.net.find_asset(self.net.objective_asset)
        asset = found[1] if found else None
        if asset is not None and not asset.taken:
            gone = int(asset.value * RIVAL_SKIM)
            asset.value = max(1, asset.value - gone)
            self.console.say(f'[ice]{name} got to it first. It is still there, '
                             f'and it is worth {RIVAL_SKIM:.0%} less, because '
                             f'they already took the part that was worth '
                             f'coming for.[/]')
        else:
            self.console.say(f'[ice]{name} got what they came for and is out. '
                             f'You are standing in what they left.[/]')
        self.escalate(1, f'{name} tripped it on the way past')

    def _apply_incident(self, it) -> None:
        """Print it and do it, with every number on the line that does it."""
        role = {'good': 'ok', 'turn': 'accent2'}.get(it.kind, 'ice')
        self.console.blank()
        self.console.rule(it.name.lower(), role='muted')
        self.console.say(f'[{role}]{it.text}[/]')
        self.seen_incidents.add(it.key)
        self.log(f'incident: {it.key}')
        told: list[str] = []

        if it.trace:
            self.add_trace(it.trace)
            told.append(f'[trace]trace {it.trace:+.0f}[/]')
        if it.noise:
            self.make_noise(it.noise)
            told.append(f'[noise]noise {it.noise:+d} here[/]')
        if it.residue:
            self.leave_residue(it.residue)
            told.append(f'[residue]residue {it.residue:+d}[/]')
        if it.focus:
            self.focus = max(0, self.focus + it.focus)
            told.append(f'[warn]focus {it.focus:+d}[/]')
        if it.integrity:
            told.append(f'[err]integrity {it.integrity:+d}[/]')
        if it.tempo:
            self.free_actions += it.tempo
            told.append(f'[ok]{it.tempo} free action'
                        f'{"s" if it.tempo != 1 else ""}[/]')
        if told:
            self.console.raw('  ' + ' · '.join(told))
        # The ones that need a sentence rather than a number.
        if it.alert_step:
            if it.alert_step > 0:
                self.escalate(it.alert_step, it.name)
            else:
                for _ in range(-it.alert_step):
                    self.cool()
        if it.wakes:
            woke = [c for c in self.node.ice
                    if c.alive and c.state == 'dormant']
            for construct in woke:
                construct.state = 'awake'
                self._tell(construct)
        if it.reveals:
            self._incident_reveal(it.reveals)
        if it.opens:
            self._incident_open()
        if it.integrity:
            self.take_damage(-it.integrity, black=False,
                             source=it.name.lower())
        if it.hook:
            self.hook = it.hook
            self.console.say(f'[warn]{incident_content.HOOKS[it.hook]}.[/]')
        if it.key == 'company':
            self._company()

    def _incident_reveal(self, what: str) -> None:
        """A gift of information, which is the cheapest thing a network can
        give you and often the most useful."""
        if what == 'hosts':
            fresh = [n for n in self.net.nodes.values() if not n.known]
            fresh.sort(key=lambda n: n.uid)
            for node in fresh[:3]:
                node.known = True
            if fresh[:3]:
                self.console.raw('  [ok]' + ', '.join(n.uid for n in fresh[:3])
                                 + '[/] [dim]are on the map now.[/]')
            return
        if what == 'ice':
            hidden = [c for n in self.net.nodes.values() if n.known
                      for c in n.ice if c.alive and not c.known]
            for construct in hidden[:3]:
                construct.known = True
            if hidden[:3]:
                self.console.raw('  [ok]' + ', '.join(
                    c.data.name for c in hidden[:3])
                    + '[/] [dim]are named now, and where.[/]')

    def _incident_open(self) -> None:
        """Somebody left a door open. The nearest shut service, on this host
        or one hop out, is open now."""
        here = [self.node] + [self.net.node(u) for u in self.node.edges]
        for node in here:
            if node is None or not node.known:
                continue
            shut = [s for s in node.services if not s.cracked]
            if not shut:
                continue
            svc = min(shut, key=lambda s: s.difficulty)
            svc.cracked = True
            if node.cracked_all or node is self.node:
                node.open = True
            self.console.raw(f'  [ok]{svc.data.name} on {node.uid} is open.[/]')
            return

    def _answer_back(self, stopped: int, source: str) -> None:
        """What an armour program does with the part it stopped (D81).

        Armour was seven programs that made a number smaller and nothing
        else, which is the least interesting thing a piece of kit can do.
        Braced, it is a counter: what it holds goes back into whatever
        sent it, which gives a build with no Warfare in it a way to hurt
        a countermeasure and a reason to carry armour on purpose.
        """
        target = next((c for c in self.locked if c.alive), None)
        if target is None:
            target = next((c for c in self.node.ice
                           if c.alive and c.state in ('awake', 'locked')),
                          None)
        if target is None:
            return
        target.damage_taken += stopped
        if target.damage_taken >= target.hp:
            target.state = 'dead'
            if target in self.locked:
                self.locked.remove(target)
            self.console.ok(f'It went back down the line and {target.data.name} '
                            f'stops.')
        else:
            self.console.say(f'[ok]{stopped} of it goes back the way it came. '
                             f'{target.data.name} felt that.[/]')

    def _root_tick(self) -> None:
        """An implant takes a while to become part of the thing it is in.

        The shape of an implant job is not "reach it and push", it is
        "push it and still be here afterwards", which is a different run:
        the middle is the dangerous part and the exit is on somebody
        else's clock rather than yours (D80).
        """
        if self.rooting <= 0:
            return
        self.rooting -= 1
        if self.rooting > 0:
            return
        self.console.blank()
        self.console.ok('It has taken. Whatever you left is part of the '
                        'furniture now, and you can go.')

    def _ice_tick(self) -> None:
        """Wake, telegraph, and strike. The fairness contract lives here."""
        candidates = list(self.locked)
        for i in self.node.live_ice:
            if i not in candidates:
                candidates.append(i)

        for construct in candidates:
            if not construct.alive or not self.running:
                continue
            data = construct.data
            if data.behaviour == 'trap':
                continue  # traps spring on contact, not on the clock
            if (self.net.faction == 'chorus' and construct.known
                    and construct.state == 'dormant'):
                # Devotional rather than defensive (D67): what wakes in a
                # Chorus network does not go back to sleep. A construct you
                # have seen wake is awake for the rest of the evening.
                construct.state = 'awake'
            if self.impersonating > 0 and data.behaviour != 'black':
                # Impersonate (D63, as the technique always said): you are
                # somebody with a reason to be here, and everything that
                # checks reasons lets you be. Black ICE does not check
                # anything. It is not a guard; it is a fact about the vault.
                continue

            if construct.state == 'dormant':
                threshold = self.wake_threshold(construct)
                if self.node.noise >= threshold and construct in self.node.ice:
                    construct.state = 'awake'
                    self._portrait(construct)
                    if not self.woken:
                        self.woken = True
                        self.console.blank()
                        wakes = cyberspace.signature(
                            self.net.faction).ice_wakes
                        self.console.say(f'[ice]{wakes}[/]')
                    self._tell(construct)
                continue

            if construct.state in ('awake', 'locked'):
                if not construct.telegraphed:
                    self._tell(construct)
                elif construct.warned < self._lead():
                    # Ticks of advance warning (D63). The key has always been
                    # described as ticks of warning and it only ever decided
                    # whether the tell was named; now each point holds the
                    # strike back a tick, which is what warning is for.
                    construct.warned += 1
                    self.console.say(f'[dim]{construct.data.name} is still '
                                     f'lining up. You have a tick.[/]')
                else:
                    self._strike(construct)

    def _lead(self) -> int:
        lead = self.char.bonus('tell_lead')
        if 'read_the_room' in self.char.riders():
            lead += 1  # ex-enforcement: you have read their manual
        if self.playbook:
            lead += 1
        return max(0, lead)

    def _draw_ice(self, construct: IceInstance) -> None:
        """The construct, as a picture (D110), where the render mode and the
        terminal both allow. Once per construct a run: a second drawing of a
        Hunter you already met is noise, not tension."""
        if self.render_mode not in ('picture', 'wide'):
            return
        from .. import anim, pixels
        if not pixels.can_render(self.console.caps):
            return
        if f'drew:{construct.uid}' in self.spent:
            return
        self.spent.add(f'drew:{construct.uid}')
        pix = pixels.render_ice(construct.behaviour,
                                seed=sum(ord(ch) for ch in construct.uid))
        if pix:
            anim.reveal(self.console, pix, construct.data.name, quick=True)

    def _tell(self, construct: IceInstance) -> None:
        """One line, the tick before it acts. Never says what it will do."""
        data = construct.data
        if not data.tells:
            return
        construct.telegraphed = True
        construct.warned = 0
        lead = self._lead()
        line = self.rng.pick(data.tells)
        if construct.grudge:
            # You would know it anywhere (D89).
            construct.known = True
        name = data.name if (construct.known or lead > 0) else 'something'
        self.console.blank()
        self.console.say(f'[ice]{line}[/]')
        if construct.known or lead > 0:
            self.console.say(f'[dim]that reads as {name}.[/]')
            construct.known = True
            # And you see it (D110): the construct drawn, where the terminal
            # can, once per construct a run.
            self._draw_ice(construct)
        if construct.grudge and f'grudge:{construct.uid}' not in self.spent:
            self.spent.add(f'grudge:{construct.uid}')
            fac = fac_content.BY_KEY.get(self.net.faction)
            did = ('put you out of' if data.behaviour in ('hunter', 'black',
                                                          'herder', 'trap')
                   else 'filed you out of')
            self.console.say(f'[err]You know this one. It {did} a '
                             f'{fac.short if fac else "their"} network, and '
                             f'it has been running since.[/]')
        if 'first_tell' not in self.spent and data.behaviour != 'black':
            # Said once a run, the first time anything winds up at all. The
            # tell buys you a tick, and a tick is only worth something to
            # somebody who knows what can be done with one. The black
            # warning below has always existed; ordinary countermeasures
            # had the same fairness contract and nothing that explained it
            # (D72).
            self.spent.add('first_tell')
            self.console.say('[warn]It moves next tick. A tell is a tick to '
                             'answer it in: `connect` to another host and it '
                             'is somebody else\'s problem, `strike` it if you '
                             'brought something that hits, or `mask` and go '
                             'quiet and hope it settles.[/]')
            self.console.say('[dim]`here` says what is on this host. Standing '
                             'still is also an answer, and sometimes the '
                             'right one.[/]')
        if data.behaviour == 'black':
            # The display does not stay calm about a thing that kills (D110):
            # a short shudder of static every time it winds up.
            self._disrupt(frames=4, height=3)
        if data.behaviour == 'black' and 'black_tell' not in self.spent:
            # Said once a run, the first time something lethal winds up. The
            # tell system is fair in the letter only if the correct response
            # is something a player can know, and nothing used to say it.
            self.spent.add('black_tell')
            self.console.say('[warn]That is the kind that kills. It has you '
                             'the tick after the tell: `connect` off this '
                             'host now, or be somewhere it cannot follow.[/]')
        self.log(f'tell: {name}')

    def _strike(self, construct: IceInstance) -> None:
        data = construct.data
        construct.telegraphed = False
        self.console.blank()
        self.console.raw(f'[err]{data.strike}[/]')
        self.log(f'strike: {data.name}')
        construct.known = True
        self.last_hit_by = construct.key
        self.last_struck_by = construct.key

        # A construct that declares `alert_jump` escalates by that much
        # rather than by the generic one. Three of them declared it and were
        # being escalated generically, which made their whole distinguishing
        # feature decorative.
        jump = int(data.effects.get('alert_jump', 1))
        # D63: a construct acting is itself a noise on the host, which is
        # how one awake Scrapper becomes three. `IceType.noise` was declared
        # for every type and read by nothing.
        if data.noise:
            self.node.noise += max(1, int(round(data.noise * 0.4)))

        if data.behaviour in ('probe', 'sentry'):
            if ('nightwatch_serial' in self.char.riders()
                    and self.net.faction == 'nightwatch'
                    and not self.serial_checked):
                # The number gets checked against the list of returned
                # equipment, and it is on it.
                self.serial_checked = True
                self.tier = max(0, self.tier - 1)
                self.console.say('[warn]It runs your serial against the '
                                 'returned-equipment list. You are on it.[/]')
                jump += 1

        if data.behaviour == 'probe':
            self.add_trace(data.trace + construct.rating)
            self.escalate(jump, f'{data.name} reported your position.')
            construct.state = 'dormant'
            return

        if data.behaviour == 'sentry':
            self.add_trace(data.trace + construct.rating * 0.5)
            self.escalate(jump, f'{data.name} filed on your session.')
            if 'null_escalation' in self.char.riders():
                self.escalate(1, 'There was nothing there to file, which is '
                                 'considerably worse than something.')
            construct.state = 'dormant'
            return

        if data.effects.get('route_cut'):
            # It never touches you. It closes the way you came. Keyed off the
            # declared effect rather than the behaviour so that the content
            # and the engine agree about what this construct does.
            self.add_trace(data.trace)
            cut = self._cut_route()
            if cut:
                self.console.say(f'[dim]{cut[0]} no longer reaches '
                                 f'{cut[1]}.[/]')
            else:
                self.console.say('[dim]There is nothing left it can safely '
                                 'close.[/]')
            construct.state = 'awake'
            self._portrait(construct)
            return

        if data.behaviour == 'warden':
            self.add_trace(data.trace)
            if ('registry_check' in self.char.riders()
                    and fac_content.BY_KEY[self.net.faction].kind == 'corp'):
                # A licensed face on an unlicensed body. The registry answers.
                self.console.say('[err]It queries the registry for your face '
                                 'and the registry answers honestly.[/]')
                self.add_trace(data.trace * 1.5)
                self.escalate(1, 'A compliance shell failed audit.')
            self.take_damage(max(1, data.damage), black=False,
                             source=data.name)
            return

        # A chromed ally standing with you will step into it. That is the
        # entire reason anybody hires one.
        ally = self.ally
        if (ally and ally['state'] == 'with you' and ally['node'] == self.here
                and ally['style'] == 'chrome'
                and data.behaviour in ('hunter', 'warden')
                and self.rng.chance(0.55)):
            self.hurt_ally(data.damage + construct.rating // 2, data.name)
            return

        # If the person you are covering is standing here and making the
        # noise that woke this thing up, it may well find them first.
        escort = self.escort
        if (escort and escort['state'] not in ('out', 'dead')
                and escort['node'] == self.here
                and data.behaviour in ('hunter', 'warden')
                and self.rng.chance(0.4)):
            self.hurt_escort(data.damage + construct.rating // 2, data.name)
            return

        # hunter and black: lock on and keep hitting.
        if construct not in self.locked:
            if ('swarm_lock' in self.char.riders()
                    and data.behaviour == 'hunter'
                    and self.rng.chance(0.45)):
                # It picked one of you, and it picked wrong.
                self.console.say('[ok]It commits to one of you and closes on '
                                 'a copy.[/]')
                construct.telegraphed = False
                return
            # D63: the lock-on is a check, printed like every other check.
            # `evade_bonus` was a key five implants, four programs, and two
            # traits sold and nothing read. Resistance sits above what a
            # fresh runner can beat, so it is a chance and not a defence,
            # and it goes up with the construct.
            evade = Check(name='slip the lock-on',
                          resistance=construct.rating * 2 + 4)
            evade.add('reflex', self.char.attr('reflex'))
            evade.add('stealth', self.char.skill('stealth'))
            evade.add('evade gear', self.char.bonus('evade_bonus'))
            evade.resolve(self.rng)
            if evade.success:
                self.console.say(f'[ok]It closes on where you were.[/] '
                                 f'[dim]its cover: {evade.summary()}[/]')
                construct.telegraphed = False
                self.log(f'evaded: {data.name}')
                return
            if construct.uid not in self.evaded:
                self.evaded.add(construct.uid)
                self.console.say(f'[dim]its cover: {evade.summary()}[/]')
            self.locked.append(construct)
            construct.state = 'locked'
        self.add_trace(data.trace)
        damage = data.damage + construct.rating // 2
        # D63 b: a faction's style. Sendai's doctrine has always said its
        # constructs hit harder; now the generator and the strike agree.
        damage = int(round(damage * self.style('damage')))
        self.take_damage(damage, black=(data.behaviour == 'black'),
                         source=data.name)

    def _cut_route(self) -> tuple[str, str] | None:
        """Close one edge, without ever stranding the player or the job.

        A herder that can orphan the objective, or cut you off from the way
        out, is not a difficulty spike: it is an unwinnable run generated
        mid-run, which is the one thing network generation is not allowed to
        do (see `_ensure_reachable`). So every candidate cut is tested before
        it is made, and if none is safe the construct simply has nothing to do.
        """
        candidates: list[tuple[str, str]] = []
        for node in self.net.nodes.values():
            for edge in node.edges:
                # Never the edges touching the player: a herder pushes you
                # deeper rather than boxing you in place.
                if node.uid == self.here or edge == self.here:
                    continue
                candidates.append((node.uid, edge))
        if not candidates:
            return None

        # D63 b: behind you first. The edges on the host you just left are
        # the way back, and a herder that closes the way back is herding;
        # one that closes a random edge across the network was a die roll
        # with a name. Shuffled within each group, so which edge behind you
        # goes is still the network's decision.
        behind = [e for e in candidates if self.previous in e]
        rest = [e for e in candidates if self.previous not in e]
        ordered = list(self.rng.shuffled(behind)) + list(self.rng.shuffled(rest))
        for a, b in ordered:
            node_a, node_b = self.net.nodes[a], self.net.nodes[b]
            node_a.edges.remove(b)
            node_b.edges.remove(a)
            if self._still_playable():
                return (a, b)
            # Put it back and try another.
            node_a.edges.append(b)
            node_b.edges.append(a)
        return None

    def _still_playable(self) -> bool:
        """Can the player still reach the way out and the job from here."""
        seen = {self.here}
        frontier = [self.here]
        while frontier:
            uid = frontier.pop()
            for edge in self.net.nodes[uid].edges:
                if edge not in seen:
                    seen.add(edge)
                    frontier.append(edge)
        if self.net.entry not in seen:
            return False
        if self.net.objective_node and self.net.objective_node not in seen:
            return False
        return True

    def _disrupt(self, frames: int = 7, height: int = 6) -> None:
        """A burst of static across the display (D110), where the terminal
        can. Off when the render mode is off, like the pictures."""
        if self.render_mode == 'none':
            return
        from .. import anim
        anim.disrupt(self.console, frames=frames, height=height)

    def _check_trace(self) -> None:
        if self.trace < TRACE_MAX:
            return
        self._disrupt()
        self.console.blank()
        self.console.raw('[err][bold]TRACE COMPLETE.[/][/]')
        self.console.say('The connection is cut from the far end. Somebody now '
                         'has a file with your working habits in it.')
        self.finish('severed')

    # ------------------------------------------------------------------
    # damage
    # ------------------------------------------------------------------

    def _wear_armour(self) -> None:
        """Armour is good for as many saves as its rating (D63 b). Bulwark's
        note has always said it loses a point each time it saves you, and
        until now it did not; now every hit it softens is a point, and at
        the rating it is gone from the deck and the bag."""
        armour = programs.best(self.char.deck.loaded, 'armour')
        if armour is None:
            return
        self.armour_wear += 1
        left = armour.rating - self.armour_wear
        if left > 0:
            self.console.say(f'[dim]{armour.name} took the edge off. '
                             f'{left} more like that in it.[/]')
            return
        if armour.key in self.char.deck.loaded:
            self.char.deck.loaded.remove(armour.key)
        if armour.key in self.char.library:
            self.char.library.remove(armour.key)
        self.armour_wear = 0
        self.console.warn(f'{armour.name} has taken all it can. It is gone.')
        self.log(f'armour burned: {armour.name}')

    def take_damage(self, amount: int, black: bool, source: str = '') -> None:
        amount = max(0, int(round(amount * self.char.mult('ice_dr'))))
        if self.braced > 0 and amount:
            # D81: the tick a tell buys you, spent on the hit. Halved, and
            # an armour program sends some of it back the way it came.
            stopped = amount - amount // 2
            amount = amount // 2
            self.console.say(f'[ok]Braced. {stopped} of it does not reach '
                             f'you.[/]')
            if self.bracing_with and stopped:
                self._answer_back(stopped, source)
        if not amount:
            return
        # Psyche rank 4, or a Static Line high (D63: the drug declared the
        # rider and nothing read it): you are not present for this. The deck
        # is.
        if self.dissociated > 0 or 'dissociated' in self.char.riders():
            black = False
            to_body = False
            slot = self.rng.pick(list(self.char.deck.parts))
            level = self.char.deck.hurt(slot, DECK_HIT)
            self.console.warn(f'It lands on the {slot} instead of on you '
                              f'[dim](damage {level}/3)[/].')
            return
        # The Deepjack routes everything through you rather than the deck.
        to_body = black or 'deep_jack' in self.char.installed

        self._wear_armour()
        if not to_body:
            slot = self.rng.pick(list(self.char.deck.parts))
            # D63: a big construct hits harder. Two levels at and above
            # `DECK_HIT_HEAVY`, after armour, so armour is the difference
            # between a Coroner scratching a part and breaking it.
            levels = DECK_HIT + (1 if amount >= DECK_HIT_HEAVY else 0)
            level = self.char.deck.hurt(slot, levels)
            self.console.warn(f'The {slot} takes it '
                              f'[dim](damage {level}/3'
                              + (', hard' if levels > 1 else '') + ')[/].')
            self.log(f'deck damage: {slot} from {source}')
            if all(self.char.deck.damage.get(s, 0) >= 3
                   for s in self.char.deck.parts):
                self.console.err('The deck is finished. Nothing is answering.')
                self.finish('severed')
            return

        if black:
            # It went through your nervous system and stopped. That leaves the
            # fern pattern whether or not the rest of the night goes badly.
            got = self.char.mark('black_ice')
            if got is not None:
                self.console.raw(f'[dim]It leaves something behind: '
                                 f'{got.name.lower()}.[/]')

        self.hurt += amount
        remaining = self.char.integrity_max - self.char.hurt - self.hurt
        self.console.raw(f'[err]Feedback. Integrity {max(0, remaining)}/'
                         f'{self.char.integrity_max}.[/]')
        self.log(f'integrity -{amount} from {source}')
        if remaining > 0:
            if ('deadman' in self.char.riders()
                    and remaining <= self.char.integrity_max * DEADMAN_FRACTION):
                # D63: the grip does what its drawback always said. It is
                # not clever and it does not ask: the run ends, you do not.
                self.console.blank()
                self.console.raw('[warn][bold]The grip cuts you out.[/][/]')
                self.console.say('Your pulse did something the relay did not '
                                 'like, and the relay did not ask. You are on '
                                 'the floor with the cable in your hand and '
                                 'the job unfinished, which was the deal.')
                self.log('deadman grip severed the connection')
                self.finish('severed')
            return

        if black:
            check = Check(name='composure', resistance=12)
            check.add('composure', self.char.composure)
            check.add('nerve', self.char.attr('nerve'))
            if 'native' in self.char.riders():
                check.add('the net is your first language',
                          self.char.dissonance // 4)
            if 'deadlight' in self.char.deck.loaded:
                check.add('Deadlight', 4)
            check.resolve(self.rng)
            self.console.blank()
            self.console.raw('[err][bold]The construct has you.[/][/]')
            self.console.say(check.explain())
            if check.success:
                self.console.say('[warn]You come out of it on the floor, with '
                                 'the deck smoking and your heart doing '
                                 'something arrhythmic. You are alive.[/]')
                self.char.mark('flatline_scar')
                self.finish('severed')
            else:
                self.finish('flatline')
            return
        self.finish('severed')

    # ------------------------------------------------------------------
    # traps
    # ------------------------------------------------------------------

    def credential_challenge(self, construct: IceInstance) -> Check | None:
        """A warden that checks credentials can be answered with credentials.

        This is the Subterfuge build's answer to "what do you do about a door
        that cannot be evaded": you do not break it, you satisfy it. Only
        wardens declaring `credential_check` can be passed this way, and only
        if you are actually carrying something worth showing.

        Returns the check to resolve, or None if the construct is not the kind
        that can be talked to.
        """
        if not construct.data.effects.get('credential_check'):
            return None
        check = Check(name='credentials', resistance=construct.rating * 2 + 2)
        check.add('access tier held', self.tier * 3)
        check.add('subterfuge', self.char.skill('subterfuge') * 2)
        check.add('guile', self.char.attr('guile'))
        check.add('gear', self.char.bonus('pretext_bonus'))
        forger = programs.best(self.char.deck.loaded, 'forger')
        if forger:
            rank = self.char.skill('subterfuge')
            check.add(programs.held_label(forger, rank, 'subterfuge'),
                      programs.held(forger, rank) * 2)
        if self.impersonating > 0:
            check.add('wearing somebody else\'s name', 5)
        if 'no_social' in self.char.riders():
            check.add('a process cannot present a badge', -10)
        return check

    def check_traps(self, node: Node | None = None) -> None:
        """Traps spring on contact. Nothing telegraphs them, by design: the
        counterplay is `probe`, not reflexes."""
        node = node or self.node
        for construct in node.live_ice:
            if construct.behaviour != 'trap' or construct.state == 'sprung':
                continue
            avoid = Check(name='trap', resistance=construct.rating * 2)
            avoid.add('stealth', self.char.skill('stealth') * 2)
            avoid.add('reflex', self.char.attr('reflex'))
            avoid.add('forensics', self.char.skill('forensics'))
            if construct.known:
                avoid.add('you knew it was there', 6)
            spotter = self.ally_bonus('trap')
            if spotter:
                avoid.add(f'{self.ally["name"]} saw it', spotter)
            avoid.resolve(self.rng)
            if avoid.success:
                if construct.known:
                    self.console.info(f'You step around the '
                                      f'{construct.data.name}.')
                continue
            construct.state = 'sprung'
            construct.known = True
            self.console.blank()
            self.console.raw(f'[err]{construct.data.strike}[/]')
            self.log(f'trap sprung: {construct.data.name}')
            self.add_trace(construct.data.trace + construct.rating)
            eff = construct.data.effects
            if eff.get('access_drop'):
                self.tier = max(0, self.tier - int(eff['access_drop']))
                self.console.warn(f'Access tier drops to {self.tier}.')
            if eff.get('alert_jump'):
                self.escalate(int(eff['alert_jump']), 'A tripwire published.')
            if eff.get('tick_mult'):
                self.drag *= float(eff['tick_mult'])
                self.console.warn('Everything is going to take longer now.')
            if eff.get('route_cut'):
                # Gallows (D63 b): its strike line always said it cut the
                # segment behind you, and it dropped your tier instead.
                cut = self._cut_route()
                if cut:
                    self.console.warn(f'The route between {cut[0]} and '
                                      f'{cut[1]} is gone.')
                    self.log(f'route cut: {cut[0]}-{cut[1]}')

    # ------------------------------------------------------------------
    # resolution
    # ------------------------------------------------------------------

    def finish(self, outcome: str) -> None:
        if not self.running:
            return
        self.outcome = outcome
        if outcome == 'severed':
            self.severed_by = self.last_hit_by or self.last_struck_by
        self.char.hurt = min(self.char.integrity_max - 1,
                             self.char.hurt + self.hurt)

    # ------------------------------------------------------------------
    # what you are here to do
    # ------------------------------------------------------------------

    def brief(self) -> Brief:
        """The job, where it is, how far along it is, and what to type next.

        The last of those is the part that matters. A player who knows the
        objective and cannot see the move is in the same position as one who
        knows neither, and inside a run the move is nearly always mechanical:
        find it, reach it, open it, do the thing, leave. This works that out
        from the state rather than describing it in general, because the
        general description is what the manual is for.
        """
        from ..world.contracts import OBJECTIVE_AIM, OBJECTIVE_PROGRAM

        kind = (self.contract or {}).get('objective', '')
        target = self.net.node(self.net.objective_node)
        found = bool(target and target.known)
        asset = self.net.find_asset(self.net.objective_asset)
        # Named once you have enumerated the host it sits on. Before that it
        # is a shape in somebody's filesystem and calling it by name would be
        # the game telling you something you have not earned. A record a
        # scene named is the exception: somebody told you what it is at the
        # door, and the brief saying "the record they want" about your own
        # log would be coy (D52).
        asset_name = (asset[1].name
                      if asset and (asset[0].mapped or asset[1].label)
                      else 'the record they want').rstrip('.')

        if not self.contract:
            return Brief(
                aim='Nobody is paying for this one. Take what is worth '
                    'taking and get out with it.',
                where='', progress=f'{len(self.haul)} assets in hand',
                done=bool(self.haul),
                steps=('scan', 'probe <host>', 'pull') if not self.haul
                      else ('jack out',))

        aim = OBJECTIVE_AIM.get(kind, 'Take something worth taking.').format(
            node=(self.net.objective_node if found else 'a host you have not '
                  'found yet'),
            asset=asset_name,
            ticks=self.SURVEIL_TICKS,
            who=(self.escort or {}).get('name', 'them'))
        # The one network with no perimeter (D146). The posting is a
        # posture-72 exfiltrate handed to a runs-five character, and two
        # of three who took it came out with nothing the first time
        # because they breached it like anything else. The whole point
        # of the story is that there is nothing arranged around it: the
        # way in is to be expected, not to force. Said once, in the aim.
        if (self.contract or {}).get('target') == 'deepwater':
            aim = (aim + ' There is no perimeter here to break: nothing '
                   'is arranged around anything. `approach` it as an '
                   'inside job or talk your way in, and you come up past '
                   'the wall instead of through it.')

        # Nothing else in the brief matters if the thing that does the job is
        # not on the deck. The loadout is fixed at the door and `jack in` says
        # so, but `--force` exists and people use it, and the run that follows
        # is one where every step of the advice is correct right up to the
        # last one, which cannot be taken at all.
        if self._missing_program():
            need = OBJECTIVE_PROGRAM.get(kind, '')
            return Brief(
                aim=aim,
                where=f'You came in without a {need}, and the loadout is '
                      f'fixed from the moment you jack in. There is no way to '
                      f'finish this one tonight.',
                progress=f'no {need} on the deck',
                done=False, steps=('jack out',))

        where = self._objective_where(target, found)
        if kind == 'escort' and self.escort:
            where = (f'{self.escort["name"]} is on {self.escort["node"]}, '
                     f'{self.escort["state"]}'
                     + (', carrying it' if self.escort.get('done') else '')
                     + '. Their pace, not yours: stay in until they are out.')
        steps = self._better_step(self._objective_steps(kind, target, found))
        # The objective verb has its own patience (D101): a build that
        # could walk through every door typed `push` seventeen times at
        # ten per cent, green throughout, until the trace filled.
        refused = self.failed.get(('verb', kind), 0)
        if (refused >= DOOR_PATIENCE and steps
                and steps[0].split()[0] in ('push', 'wipe', 'pull')
                and self.here == self.net.objective_node):
            from ..commands.run import push_check, wipe_check
            payload = programs.best(self.char.deck.loaded, 'payload')
            check = None
            if kind == 'wipe' and payload is not None:
                check = wipe_check(self, payload)
            elif kind in ('implant', 'corrupt') and payload is not None:
                check = push_check(self, kind, payload)
            if check is not None and check.chance < 0.5:
                skill = 'Sabotage' if kind == 'corrupt' else 'Intrusion'
                if kind == 'wipe':
                    skill = 'Sabotage'
                where = (f'{where} The {kind} has refused {refused} times '
                         f'at {check.chance:.0%}: {skill} is the number, and '
                         f'this one is not tonight.').strip()
                steps = ('jack out',)
        # The night that is over (D88). The brief prices each door against
        # the clock and never the whole job: at lockdown with the trace at
        # ninety it went on saying `wait` and `crack`, one long shot at a
        # time, until the connection was cut. This reads the clock once,
        # for the whole of what is left to do.
        over = ''
        if steps and steps[0] != 'jack out' and not self.objective_met():
            over = self.night_over(kind, target, found)
            if over:
                where = f'{where} {over}'.strip()
                steps = ('jack out',)
        # Something is winding up and this build has nothing that hurts
        # it: brace is the answer every build has (D81). Only on a run
        # that is carrying on, though: it was advising a tick of bracing
        # and then leaving on the next one, which is a tick spent on a
        # night already over (D83).
        # Only when it is actually going to reach you wherever you go.
        # A construct merely awake on this host is answered by leaving it,
        # and advising the brace instead made a corporate run into a
        # runner standing still being hit: `brace` was typed a hundred and
        # twenty four times across thirty severed runs and was the most
        # repeated command in nine of them, which is the whole of what the
        # corporate wall turned out to be (D85). Once per lock, too: the
        # tick a tell buys you is spent once, not adopted as a way of life.
        locked_on = [c for c in self.locked if c.alive]
        if (locked_on and self.braced <= 0
                and not self._huntable()
                and 'braced' not in self.spent
                and steps and steps[0] != 'jack out'):
            self.spent.add('braced')
            steps = ('brace',) + steps
        # Why there is nothing to try, when there is nothing to try (D67).
        # Not when the clock has already said why (D91).
        if steps == ('jack out',) and not self.objective_met() and not over:
            why = self._hopeless_where()
            if why:
                where = f'{where} {why}'.strip()
        # The brief reads the same sums the verbs do (D64 a). Advice that
        # says `wipe` forever against a check that cannot land tonight is
        # a loop with a friendly voice; if the thing cannot be done with
        # what you carry, the brief says so and the next move is out. A
        # sealed record it cannot open is the one exception: there is a
        # second way to carry that out.
        if steps and self.here == self.net.objective_node:
            from ..commands.run import (decrypt_check, push_check,
                                        wipe_check)
            payload = programs.best(self.char.deck.loaded, 'payload')
            blocked = None
            verb = steps[0].split(' ')[0]
            if verb == 'wipe' and payload is not None:
                check = wipe_check(self, payload)
                if check.impossible:
                    blocked = f'the wipe cannot land: {check.summary()}'
            elif verb == 'push' and payload is not None:
                check = push_check(self, kind, payload)
                if check.impossible:
                    blocked = f'the {kind} will not take: {check.summary()}'
            elif (verb == 'pull' and asset and asset[1].encrypted
                    and not asset[1].taken
                    and (decrypt_check(self).impossible
                         or ('pull', asset[1].uid) in self.tried)):
                steps = (f'pull {asset[1].uid} --sealed',)
                where = (where + ' You cannot open it tonight; take it '
                         'shut for part of the fee.').strip()
            if blocked:
                where = (where + f' {blocked[0].upper()}{blocked[1:]}. Nothing '
                         f'you carry changes that tonight.').strip()
                steps = ('jack out',)
        return Brief(aim=aim, where=where,
                     progress=self._objective_progress(kind, asset_name),
                     done=self.objective_met(), steps=steps)

    def _missing_program(self) -> str:
        """The program category this contract needs and the deck has not got."""
        from ..world.contracts import OBJECTIVE_PROGRAM
        kind = (self.contract or {}).get('objective', '')
        need = OBJECTIVE_PROGRAM.get(kind, '')
        if need and not self.char.deck.has_category(need):
            return need
        return ''

    def _objective_where(self, target, found: bool) -> str:
        """Where the job is, or what to look for if you have not found it."""
        if target is None:
            return ''
        if not found:
            # The zone is a real hint and not a giveaway: it says how deep to
            # go, which is the decision, without naming the host.
            return (f'It is in their {target.zone}, which you have not '
                    f'reached. Everything between here and there is in the '
                    f'way on purpose.')
        if self.here == self.net.objective_node:
            return 'You are standing on it.'
        route = self.route_to(self.net.objective_node)
        if not route:
            return (f'{self.net.objective_node} is on the map and nothing you '
                    f'have opened reaches it yet.')
        line = (f'{self.net.objective_node} is {len(route)} hop'
                f'{"s" if len(route) != 1 else ""} from here, through '
                f'{", ".join(route[:-1]) or "nothing in the way"}.')
        # The one obstacle in a run that is invisible from the thing blocking
        # you. A door you cannot open looks the same whether you are short a
        # program or short a credential, and only one of those is fixed by
        # trying again.
        deepest = max((n.tier for n in (self.net.node(u) for u in route)
                       if n is not None), default=0)
        if deepest > self.tier:
            line += (f' You hold tier {self.tier} and the way in goes through '
                     f'tier {deepest}, which is a penalty on every attempt '
                     f'until you have the badge for it.')
        return line

    def _objective_progress(self, kind: str, asset_name: str) -> str:
        if kind == 'surveil':
            if self.observed_enough:
                return (f'{self.observed} of {self.SURVEIL_TICKS} clean ticks '
                        f'banked, which is enough')
            # What to do about it, not just where it stands. A bar that
            # counts to eight without ever saying what banks one, or what
            # empties the lot, is a number somebody watches and does not
            # understand.
            if self.here != self.net.objective_node:
                # Named only once it has been found, like everything else
                # about it: the aim one line above says the host has not
                # been reached yet, and naming it here hands over the
                # answer the run is asking for.
                target = self.net.node(self.net.objective_node)
                where = ('nothing banks until you are on '
                         + (self.net.objective_node
                            if target is not None and target.known
                            else 'it'))
            elif self.alert in ('red', 'lockdown'):
                where = ('nothing banks while the room is red; go quiet and '
                         'let it stand down')
            else:
                where = '`observe` banks one, and red empties the lot'
            return (f'{self.observed} of {self.SURVEIL_TICKS} clean ticks '
                    f'banked: {where}')
        if kind == 'implant':
            if self.rooting > 0:
                return (f'it is in and taking: {self.rooting} tick'
                        f'{"s" if self.rooting != 1 else ""} before it is '
                        f'part of the furniture, and you have to be in here '
                        f'when it is')
            if self.done.get('implant') == self.net.objective_node:
                return 'it has taken, and you can go'
        if kind == 'corrupt' and self.alert in ('red', 'lockdown'):
            return ('the room is red, and an edit made now reads as an edit '
                    'rather than as a fault')
        if kind == 'escort' and self.escort:
            return (f'{self.escort["name"]} is on {self.escort["node"]}, '
                    f'{self.escort["state"]}'
                    + (', carrying it' if self.escort['done'] else ''))
        if kind == 'exfiltrate':
            if self.objective_met():
                return ('you have it, shut: they pay part for a sealed one'
                        if self.net.objective_asset in self.sealed
                        else 'you have it')
            found = self.net.find_asset(self.net.objective_asset)
            shut = ''
            if found and found[1].encrypted and found[0].mapped:
                shut = (' It is sealed: Cryptography opens it, or `pull '
                        '--sealed` takes it shut for part of the fee.')
            return f'{asset_name} is still theirs.{shut}'
        if self.objective_met():
            return 'done'
        return 'not yet'

    def _objective_steps(self, kind, target, found: bool) -> tuple[str, ...]:
        """The next thing to type. One move ahead, never a walkthrough.

        Written to name real hosts and real services rather than to print the
        shape of the command. `probe fl-db12` is a move; `probe <host>` is a
        syntax reminder, and somebody who had to ask what to do next did not
        need reminding of the syntax.

        Every run is the same five beats, which is why this can be worked out
        rather than authored: find it, reach it, open it, do the thing, leave.
        """
        if self.objective_met():
            return ('jack out',)
        if kind == 'escort':
            return self._escort_steps()
        if target is None:
            return ('scan',)
        if not found:
            return self._search_steps()
        if self.here != self.net.objective_node:
            return self._approach_steps()
        return self._finish_steps(kind)

    def _escort_steps(self) -> tuple[str, ...]:
        """An escort is their pace, not yours (D101). The brief treated it
        as a place to reach, said the zone had not been reached, and left
        with the escort still inside three nights running."""
        escort = self.escort
        if not escort or escort['state'] in ('out', 'dead'):
            return ('jack out',)
        if escort['state'] == 'hold':
            return ('signal move',)
        if escort.get('done') or escort['state'] == 'leaving':
            return ('wait',)
        return ('wait',)

    def _search_steps(self) -> tuple[str, ...]:
        """You have not found it. Search, in the order a person would.

        Look out from where you are standing, look properly at whatever that
        turned up, open the way onward, and then go and stand somewhere you
        have not looked out from. Without that last condition the advice walks
        between the same two open hosts forever, because both of them are
        always somewhere you could go.
        """
        if self.here not in self.scanned:
            return ('scan',)
        # Deepest first, everywhere below. The objective is always in the core
        # or the restricted zone, the brief has already said so, and the trace
        # is a clock: an even-handed sweep of the perimeter is a thorough way
        # to run out of time in the part of the network the job is not in.
        unmapped = [n for n in self.net.nodes.values()
                    if n.known and not n.mapped]
        # With Intrusion 4 the search is a walk (D100): pivot to the
        # deepest unopened host next to this one and look from there.
        if self.char.has_technique('pivot') and self.node.open:
            doors = [self.net.node(u) for u in self.node.edges]
            doors = [n for n in doors if n is not None and n.known
                     and not n.open]
            if doors:
                return (f'pivot {self._deepest(doors, penalise_tier=False).uid}',)
        shut = self._first_shut()
        # A probe budget (D88). Deepest-first read every label on a
        # hostile segment before opening anything: five probes in a row
        # at amber, and the trace spent on reading rather than on doors.
        # Two hosts mapped and one of them shut is enough to go through.
        mapped = sum(1 for n in self.net.nodes.values() if n.mapped)
        if unmapped and not (shut and mapped >= 2):
            return (f'probe {self._deepest(unmapped).uid}',)
        if shut:
            return (f'crack {shut[0]} {shut[1]}', f'connect {shut[0]}')
        # An open host a warden holds is not somewhere to stand (D100):
        # the search picked the deepest one, `_steps_toward` saw it
        # blocked and gave up, and a soft network with a plain open host
        # one hop from the objective burned three nights running.
        fresh = [n for n in self.net.nodes.values()
                 if n.open and n.uid not in self.scanned and n.uid != self.here
                 and not self._blocked(n)]
        while fresh:
            node = self._deepest(fresh, penalise_tier=False)
            if self.route_to(node.uid):
                return self._steps_toward(node.uid)
            fresh.remove(node)
        return self._nothing_left()

    def _deepest(self, nodes, penalise_tier: bool = True):
        """The one furthest in. Deeper is where the job is, always.

        `penalise_tier` puts anything above your access last, which is right
        for picking a door to break, because a zone above your tier is a
        three-point penalty on every attempt at it. It is wrong for picking
        somewhere to walk: a tier only ever costs you the *opening* of a node,
        so a host that is already open is free to stand on however deep it is.
        """
        return min(nodes, key=lambda n: ((n.tier > self.tier) if penalise_tier
                                         else False, -n.tier, n.uid))

    def _approach_steps(self) -> tuple[str, ...]:
        """You know where it is. Open the next hop and take it."""
        return self._steps_toward(self.net.objective_node)

    def _steps_toward(self, uid: str) -> tuple[str, ...]:
        """The next move toward a host you can see and are not standing on."""
        route = self.route_to(uid)
        if not route:
            shut = self._first_shut()
            if shut:
                return (f'crack {shut[0]} {shut[1]}', f'connect {shut[0]}')
            return self._nothing_left()
        step = route[0]
        hop = self.net.node(step)
        if hop is None:
            return ('scan',)
        # Intrusion 4 walks through doors (D100). `pivot` costs a tick and
        # no noise and needs no probe, no crack and no badge, and the brief
        # offered it only against a warden it could not present to: on the
        # same fifteen corporate networks a hand that pivoted every hop
        # paid nine nights and the brief paid one.
        if (self.char.has_technique('pivot') and self.node.open
                and step in self.node.edges and not hop.open):
            return (f'pivot {step}',)
        if not hop.mapped:
            return (f'probe {step}',)
        if hop.open and self._blocked(hop):
            # Open and still impassable, which only a warden does. Route
            # around it if the map allows, and otherwise say so rather than
            # advising a command the game is about to refuse.
            return self._nothing_left()
        if not hop.open:
            # A zone above your access is a three-point penalty on every
            # attempt, and grinding at it is the commonest way to spend a
            # whole run getting nowhere loudly. The answer is somewhere else
            # on the network, which is exactly why it needs pointing at.
            if hop.tier > self.tier:
                badge = self._tier_steps()
                if badge:
                    return badge
            way = self._easiest(hop)
            if way:
                return (f'crack {step} {way}', f'connect {step}')
        if not hop.open:
            # Nothing on it worth an attempt, and nowhere else to be. Saying
            # `connect` here produces a refusal, which is the one thing advice
            # must never do.
            return self._nothing_left()
        # A warden guards the door rather than the room, so an open node can
        # still refuse you, and the answer is a different command rather than
        # more of the same one.
        warden = next((i for i in hop.live_ice
                       if i.behaviour == 'warden' and i.known), None)
        if warden is not None:
            challenge = self.credential_challenge(warden)
            if challenge is None:
                return self._nothing_left()
            # Once, and only at odds worth the escalation a refusal costs
            # (D90). A story player's follower typed `connect tooth
            # --present` twelve times running, each refusal stepping the
            # alert, because nothing remembered the last one.
            if (('present', hop.uid) in self.tried
                    or challenge.chance < self.hopeless):
                return self._nothing_left()
            return (f'connect {step} --present',)
        return (f'connect {step}',)

    def _hopeless_where(self) -> str:
        """Why there is nothing to try, in the terms of the loadout."""
        # Standing on the chair with something awake keeping the room red
        # (D88): a watch banks nothing under it and an edit reads as an
        # edit, and the old reason printed here was about doors that were
        # all open.
        kind = (self.contract or {}).get('objective', '')
        if (self.here == self.net.objective_node
                and kind in ('surveil', 'corrupt')
                and self.alert in ('red', 'lockdown')
                and self._something_hunting()):
            loud = next((c for c in self.node.live_ice
                         if c.alive and c.state != 'dormant'), None)
            name = loud.data.name if loud is not None and loud.known \
                else 'something awake'
            what = ('nothing banks' if kind == 'surveil'
                    else 'an edit reads as an edit')
            return (f'{name} is keeping this room red and {what} while it '
                    f'is. Nothing you carry hits it: a weapon program and '
                    f'the Warfare to drive it is the difference. This one '
                    f'is not tonight.')
        blocked, hop = self._blocked_by_warden()
        if blocked is None:
            # A warden that has already refused you is routed around, so
            # the route no longer names it; the refusal is still the
            # reason there is nothing to try (D90).
            for uid in self.node.edges:
                near = self.net.node(uid)
                if near is None or ('present', uid) not in self.tried:
                    continue
                warden = next((c for c in near.ice if c.behaviour == 'warden'
                               and c.alive), None)
                if warden is not None:
                    blocked, hop = warden, near
                    break
        if blocked is not None and hop is not None:
            # It said "nothing opens for what you are carrying: the best
            # of it is 100% on badge reader" about a door that was open
            # and a warden that was the problem (D88).
            challenge = self.credential_challenge(blocked)
            ways = ['`pivot` past it at Intrusion 4']
            if 'native' in self.char.riders():
                ways.append('`native`, once a run')
            if challenge is None:
                return (f'{blocked.data.name} holds {hop.uid} and takes no '
                        f'credentials at all. {", or ".join(ways)}, or '
                        f'another way in: `map` shows whether there is one.')
            if ('present', hop.uid) in self.tried:
                return (f'{blocked.data.name} refused what you showed it, '
                        f'and showing it again steps the alert every time. '
                        f'{", or ".join(ways)}, or another way in: `map` '
                        f'shows whether there is one.')
            if challenge.impossible:
                return (f'{blocked.data.name} holds {hop.uid} and would not '
                        f'take anything you carry: {challenge.explain()}. A '
                        f'forger and the Subterfuge to drive it, '
                        f'{", or ".join(ways)}, or another way in. This one '
                        f'is not tonight.')
        node = self.node
        shut = [s for s in node.services if not s.cracked]
        if not shut:
            return ''
        best = 0.0
        for svc in shut:
            _, category = node_content.FAMILIES[svc.family]
            program = programs.best(self.char.deck.loaded, category)
            best = max(best, crack_check(self, node, svc, program).chance)
        if best >= self.hopeless:
            # The doors are not the problem, so do not say they are.
            return ''
        hardest = min(shut, key=lambda s: s.difficulty)
        _, category = node_content.FAMILIES[hardest.family]
        return (f'Nothing on {node.uid} opens for what you are carrying: the '
                f'best of it is {best:.0%} on {hardest.data.name}. A better '
                f'{category}, or the rank to drive one, is the difference. '
                f'This one is not tonight.')

    def _salvage_step(self) -> tuple[str, ...]:
        """Something worth carrying out of a run that is already lost.

        A contract pays nothing for an attempt, which is right, and the
        job sheet has always said that a run with nothing on it pays for
        whatever you can carry. The advice never once said it: a run whose
        objective had gone out of reach was told to leave empty handed,
        and measured over six careers that made every contract after the
        third pay exactly nothing. A lost night should be a bad night, not
        a zero (D82).
        """
        # `_steps_toward` falls back to `_nothing_left`, which is what
        # called this, so without a guard a network with an unreachable
        # asset on it recurses until Python gives up.
        if self._salvaging or programs.best(self.char.deck.loaded,
                                            'payload') is None:
            return ()
        best, value = None, 0
        for node in self.net.nodes.values():
            if not node.known or not node.open:
                continue
            if node.uid != self.here and not self.route_to(node.uid):
                continue
            for asset in node.data:
                if asset.taken or asset.uid in self.haul:
                    continue
                if asset.value > value:
                    best, value = (node, asset), asset.value
        if best is None or value < 200:
            return ()
        node, asset = best
        if node.uid != self.here:
            self._salvaging = True
            try:
                toward = self._steps_toward(node.uid)
            finally:
                self._salvaging = False
            return () if toward == ('jack out',) else toward
        if asset.encrypted:
            # Thirty `pull`s at a sealed record, each a tick, each "stays
            # sealed" (D91). Take it shut once it has refused, or when it
            # never could open.
            from ..commands.run import decrypt_check
            if (('pull', asset.uid) in self.tried
                    or decrypt_check(self).impossible):
                return (f'pull {asset.uid} --sealed',)
        return (f'pull {asset.uid}',)

    def _nothing_left(self) -> tuple[str, ...]:
        """No way on that you can see. Look once more, then go.

        The least popular advice in the game and the most important, because
        the alternative to hearing it is finding out at a hundred trace. A run
        you cannot finish is still a run you can walk out of.
        """
        # Only if standing here has not already been tried. A scan reveals the
        # neighbourhood of wherever you are, so a second one from the same
        # host is the same answer, and "scan" as a fallback for "I have run
        # out of ideas" is a hundred and fifty identical ticks.
        if self.here not in self.scanned:
            return ('scan',)
        # A tier you have not taken yet is worth three points on every locked
        # door and on every warden between you and the job, and it is the one
        # thing left that can make a wall stop being one. Somebody with no
        # Subterfuge cannot talk their way past a Steward at tier zero and can
        # at tier two, and the difference is an auth server they walked past.
        badge = self._tier_steps()
        if badge:
            return badge
        # Not empty handed, if there is anything within reach worth the
        # ticks. The contract is gone; the night does not have to be.
        salvage = self._salvage_step()
        if salvage:
            return salvage
        return ('jack out',)

    def _tier_steps(self) -> tuple[str, ...] | None:
        """The way to hold a higher access tier, if there is one in reach.

        Cracking every service on an auth server is the standard route to a
        badge. Only ones at or below your current tier: sending somebody at a
        locked door to open a locked door behind it is not advice.
        """
        # At or below your tier first; then one above, which is three
        # points and the only rung there is. Two above is a wall, and
        # sending somebody at it is not advice.
        for reach in (0, 1):
            for node in self.net.nodes.values():
                if (node.type != 'auth' or not node.known
                        or node.tier > self.tier + reach):
                    continue
                if not node.mapped:
                    return (f'probe {node.uid}',)
                way = self._easiest(node)
                if way:
                    return (f'crack {node.uid} {way}',)
        return None

    #: Below this chance the brief stops calling something a way in. A long
    #: shot is a decision and the player can price it with `odds`; a one in
    #: ten is a hundred and fifty identical ticks with a countdown running.
    #:
    #: It is a fraction of the clock rather than a fixed number, because
    #: what makes a long shot bad is the countdown and not the odds. At
    #: three trace out of a hundred a one in seven door is worth knocking
    #: on seven times; at eighty it is a way of spending the rest of the
    #: night. A flat sixteen per cent told the weakest builds to leave on
    #: the second tick of a run they had barely started (D71).
    HOPELESS = 0.05
    HOPELESS_LATE = 0.34

    @property
    def hopeless(self) -> float:
        """The odds below which the brief stops naming a door, here and
        now. Rises with the trace: the same chance is worth taking early
        and worth walking away from late."""
        return self.HOPELESS + (self.HOPELESS_LATE - self.HOPELESS) * min(
            1.0, max(0.0, self.trace_pct))

    def _easiest(self, node) -> str:
        """The best way into a host: the shut service with the best odds.

        Priced with `crack_check`, which is the same sum `odds` prints, so the
        advice and the maths can never disagree. Sorting on the declared
        difficulty instead recommended a difficulty-3 badge reader over a
        difficulty-8 process controller without noticing that the reader is a
        physical service resolved on Hardware and Grit, which this character
        does not have, and the controller was the one they could actually
        open.

        The bar is *possible*, not *likely*. A long shot is a decision and the
        player can price it with `odds`; a service this build cannot pass at
        all is not a decision, and naming one produced a hundred and fifty
        identical attempts and a filled trace.
        """
        best, best_chance = '', 0.0
        tired = {s.key for s in node.services
                 if self.failed.get((node.uid, s.key), 0) >= DOOR_PATIENCE}
        shut = [s for s in node.services if not s.cracked]
        if len(tired) < len(shut):
            shut = [s for s in shut if s.key not in tired]
        for svc in shut:
            _, category = node_content.FAMILIES[svc.family]
            program = programs.best(self.char.deck.loaded, category)
            chance = crack_check(self, node, svc, program).chance
            if chance > best_chance:
                best, best_chance = svc.key, chance
        # And a one in ten is not a way in. Naming it produced runs that
        # were forty identical attempts at the same locked door with a
        # countdown running, which is the game wasting somebody's evening
        # politely. Say nothing instead, and let the caller say leave.
        return best if best_chance >= self.hopeless else ''

    def _finish_steps(self, kind: str) -> tuple[str, ...]:
        """You are standing on it. Do the thing you came to do."""
        if not self.node.mapped:
            return (f'probe {self.here}',)
        if not self.node.open:
            way = self._easiest(self.node)
            if way:
                return (f'crack {self.here} {way}',)
        # Named, because both `pull` and `wipe` default to the first asset on
        # the node and the first asset on the node is frequently not the one
        # the contract is about.
        # A watch banks nothing while the room is red: `_surveil_tick`
        # throws the lot away every tick the alert is up, so `observe` at
        # red is the friendly-voiced loop this file refuses to print
        # anywhere else. Measured: a fresh build banked one tick, went
        # red, and was advised to observe for thirty more while the trace
        # ran from eighteen to a hundred. Quiet is the answer and there is
        # a verb for it; if quiet cannot come because something alive is
        # making the noise, that is what to say instead.
        # An implant that is in and taking wants you alive and inside, not
        # standing over it (D80).
        if kind == 'implant' and self.rooting > 0:
            return ('wait',)
        # An edit made while they are looking reads as an edit. The room
        # has to settle before this is worth trying.
        if kind == 'corrupt' and self.alert in ('red', 'lockdown'):
            if not self._something_hunting():
                return ('wait',)
            hunter = self._huntable()
            return (f'strike {hunter}',) if hunter else ('jack out',)
        if kind == 'surveil' and self.alert == 'lockdown':
            # Twelve quiet ticks at two and a half times to bank one, and
            # the response on the way (D101): a watch under lockdown is
            # over.
            return ('jack out',)
        if kind == 'surveil' and self.alert in ('red', 'lockdown'):
            if not self._something_hunting():
                return ('wait',)
            hunter = self._huntable()
            if hunter:
                return (f'strike {hunter}',)
            return ('jack out',)
        asset = self.net.objective_asset
        # Something awake on the chair, and a verb that takes ticks (D100):
        # a pull woke the black ICE and the strike landed inside it. Hit
        # it if you can, mask if you can, and then do the thing.
        awake = [c for c in self.node.ice if c.alive and c.state != 'dormant'
                 and c.behaviour in ('hunter', 'black', 'sentry')]
        if awake and kind in ('exfiltrate', 'wipe', 'implant', 'corrupt'):
            hunter = self._huntable()
            if hunter:
                return (f'strike {hunter}',)
            if (programs.best(self.char.deck.loaded, 'mask') is not None
                    and self.masked <= 0 and 'masked_here' not in self.spent):
                self.spent.add('masked_here')
                return ('mask',)
        return {
            'exfiltrate': (f'pull {asset}' if asset else 'pull',),
            'implant': ('push',),
            'corrupt': ('push',),
            'wipe': (f'wipe {asset}' if asset else 'wipe',),
            'surveil': ('observe',),
            # Only when there is somebody to signal. `jack in` always puts
            # one in, but the brief is asked in states `jack in` did not
            # build, and advising a verb at nobody is the one thing it must
            # not do.
            # And out, once they have what they came for (D100): `signal
            # move` was typed fifty-eight times at somebody holding it.
            'escort': ((('signal out',) if self.escort['done']
                        else ('signal move', 'signal out')) if self.escort
                       else ('jack out',)),
        }.get(kind, ('pull',))

    def _something_hunting(self) -> bool:
        """Whether anything is keeping *this room* loud.

        Quiet ticks cool an alert, so waiting is the answer to a room that
        went red on its own. It is not the answer to something awake on
        the host you are standing on, or something locked on to you, which
        acts every tick wherever you go. Anything dormant, or awake three
        hosts away, is not a reason to give up on standing still.
        """
        here = [c for c in self.node.ice if c.alive
                and c.state in ('awake', 'locked')]
        return bool(here or [c for c in self.locked if c.alive])

    def _huntable(self) -> str:
        """The name of something worth striking, if striking is a thing
        this build can do at all."""
        if programs.best(self.char.deck.loaded, 'weapon') is None:
            return ''
        for node in (self.node, *(self.net.node(u) for u in self.node.edges)):
            if node is None or not node.known:
                continue
            for construct in node.ice:
                if construct.alive and construct.behaviour in ('hunter',
                                                               'sentry'):
                    return construct.uid
        return ''

    def _first_shut(self) -> tuple[str, str] | None:
        """An adjacent host you have looked at and not opened, and its way in."""
        shut = [n for n in (self.net.node(u) for u in self.node.edges)
                if n is not None and not n.open and n.mapped
                and self._easiest(n)]
        if not shut:
            return None
        # A host that has held nine cracks between two doors is not the
        # first choice while there is another (D100): the per-door cap
        # ping-ponged.
        tired = [n for n in shut if self._attempts_at(n) >= HOST_PATIENCE]
        if tired and len(tired) < len(shut):
            shut = [n for n in shut if n not in tired]
        node = self._deepest(shut)
        return node.uid, self._easiest(node)

    def _attempts_at(self, node) -> int:
        return sum(v for (uid, _), v in self.failed.items() if uid == node.uid)

    def route_to(self, uid: str) -> list[str]:
        """The hops from here to a host, over what you have actually found.

        Over `known` rather than over the whole network, so this can never
        route you through a host you have not seen: the answer a player gets
        is one they could have worked out themselves from the map.

        Doors you have seen and know you cannot open are routed around, when
        there is a way round. Only ones you have actually identified: routing
        around a warden nobody has looked at yet would be the game quietly
        using what it knows instead of what you know.
        """
        known = {n.uid for n in self.net.nodes.values() if n.known}
        edges = {uid_: [e for e in node.edges if e in known]
                 for uid_, node in self.net.nodes.items() if uid_ in known}
        walls = {u for u in known if u != uid and u != self.here
                 and self._blocked(self.net.node(u))}
        if walls:
            around = {u: [e for e in es if e not in walls]
                      for u, es in edges.items() if u not in walls}
            path = ui.shortest_path(around, self.here, uid)
            if path:
                return path
        return ui.shortest_path(edges, self.here, uid)

    def trace_rates(self) -> tuple[float, float]:
        """What a working tick and a quiet tick cost in trace, here and
        now: the same multipliers `add_trace` applies, read forward. Quiet
        ticks are cheap by design (D66), so a watch and a wait are not
        priced like a crack."""
        mult = self.char.mult('trace_mult')
        mult *= ice_content.ALERT_TRACE_MULT[self.alert]
        mult *= shifts.phase(self.phase).trace
        mult *= self.net.crowd
        if self.condition is not None:
            mult *= self.condition.trace
        noisy = (TRACE_PER_TICK + 2.0 * NOISE_TO_TRACE) * mult
        quiet = IDLE_TRACE * mult
        return max(0.05, noisy), max(0.02, quiet)

    def ticks_needed(self, kind: str, target, found: bool) -> tuple[int, int]:
        """About how the rest of the job splits into (working, quiet)
        ticks, if every door opens first time. A floor, which is what
        makes it honest."""
        if found and target is not None and self.here != target.uid:
            route = self.route_to(target.uid)
            hops = 0.0
            for uid in route:
                hop = self.net.node(uid)
                if hop is not None and hop.open:
                    hops += 1
                    continue
                # A probe, the crack at its own odds (so a one-in-three
                # door is three attempts, not one), and the connect. The
                # first version assumed every door opened first time and
                # pressed on to trace ninety on corporate work (D91).
                odds = 0.5
                if hop is not None and hop.mapped:
                    way = self._easiest(hop)
                    if way:
                        svc = next(s for s in hop.services if s.key == way)
                        odds = max(0.1, self._odds_for(hop, svc))
                # A Lattice is two ticks a door, and the clock read every
                # crack as one (D97).
                breaker = programs.best(self.char.deck.loaded, 'breaker')
                per = 2 if (breaker is not None and breaker.key == 'lattice') else 1
                hops += 1 + per / odds + 1
            hops = int(round(hops))
        elif found and target is not None:
            hops = 0
        else:
            hops = 3 * 2
        finish = {'exfiltrate': 2, 'wipe': 2, 'corrupt': 2, 'implant': 2,
                  'escort': 4}.get(kind, 2)
        quiet = 0
        if kind == 'surveil':
            finish = 0
            quiet = 2 * max(0, self.SURVEIL_TICKS - self.observed)
            if self.alert in ('red', 'lockdown'):
                # Nothing banks until it stands down, and standing down is
                # quiet ticks too.
                quiet += ice_content.QUIET_TO_COOL - self.quiet_ticks
        if kind == 'implant':
            quiet += 5
        return hops + finish, quiet

    def night_over(self, kind: str, target, found: bool) -> str:
        """Why the rest of the job does not fit in the clock, or ''.

        Only once the room has turned or the clock is half spent: early,
        a slow start is a slow start and the brief should not be telling
        anybody to leave a green room at trace twelve.
        """
        if self.alert not in ('red', 'lockdown') and self.trace_pct < 0.5:
            return ''
        noisy_rate, quiet_rate = self.trace_rates()
        working, quiet = self.ticks_needed(kind, target, found)
        need = working * noisy_rate + quiet * quiet_rate
        left = max(0.0, TRACE_MAX - self.trace)
        if self.alert in ('red', 'lockdown'):
            # Two working ticks of margin: one because at two and a half
            # times the exit fired a tick before the sever (D91), and one
            # for the exit itself, which costs a tick the first version
            # forgot and the trace filled during it (D97).
            left = max(0.0, left - 2 * noisy_rate)
        if need <= left * 1.15:
            return ''
        ticks = int(left / noisy_rate)
        return (f'The trace has about {ticks} working tick'
                f'{"s" if ticks != 1 else ""} in it at {self.alert}, and what '
                f'is left of the job is about {working + quiet} even if every '
                f'door opens first time. That is not tonight: leave with '
                f'what you are carrying.')

    def _better_step(self, steps: tuple[str, ...]) -> tuple[str, ...]:
        """The plain move, improved by something this character can do.

        The brief taught the loop every runner starts with and never
        taught any other: scan, probe, crack, connect, do the thing,
        leave. Twenty-eight techniques hang off the skills and the advice
        named two of them, so somebody who spent eleven experience on
        Intrusion 4 was never once told to `pivot`, and their build read
        as a slightly better number on the same six verbs (D78).

        This is the one place that asks "is there something you hold that
        beats this?" and it only ever answers with a verb the character
        has actually bought.
        """
        if not steps or not self.contract and not self.haul:
            pass
        first = steps[0] if steps else ''
        char = self.char
        node = self.node

        # A grudge awake on the route and a mask in the deck: the mask
        # goes on at the door (D101), before the pivot wakes the room.
        if (self.tick <= 1 and steps and steps[0] != 'jack out'
                and self.masked <= 0 and 'masked_door' not in self.spent
                and programs.best(char.deck.loaded, 'mask') is not None
                and any(c.grudge and c.alive for n in self.net.nodes.values()
                        for c in n.ice)):
            self.spent.add('masked_door')
            return ('mask',) + steps
        # Something dispatched onto this host (D92) is answered before
        # anything else is typed (D100): the brief went on probing under a
        # Kestrel until the masking took it. Hit it if you carry something
        # that hits, else leave the host, else mask.
        sent = next((c for c in node.ice if c.alive and c.uid.endswith('-sent')
                     and c.state != 'dead'), None)
        if sent is not None and first != 'jack out':
            weapon = programs.best(char.deck.loaded, 'weapon')
            if char.has_technique('strike') and weapon is not None:
                return (f'strike {sent.data.name.lower()}',) + steps
            away = [self.net.node(u) for u in node.edges]
            away = [n for n in away if n is not None and n.open
                    and not self._blocked(n)]
            if away:
                route = self.route_to(self.net.objective_node) if \
                    self.net.objective_node else []
                pick = next((n for n in away if route and n.uid == route[0]),
                            away[0])
                return (f'connect {pick.uid}',) + steps
            if (programs.best(char.deck.loaded, 'mask') is not None
                    and self.masked <= 0):
                return ('mask',) + steps
            if self.here == self.net.entry:
                # Nothing to hit it with, nowhere to go, and this is the
                # door: leave by it.
                return ('jack out',)
        # Leaving with a mess on the floor. Forensics 2 is the difference
        # between a clean run and a run their forensics finish for them.
        if first == 'jack out' and self.objective_met():
            if (char.has_technique('scrub') and self.residue_here() >= 4
                    and self.here not in self.scrubbed):
                return ('scrub',) + steps
        # A door that wants a badge, and a face that can present one. The
        # target is the host the warden is standing on, not the one you are
        # standing on, and both verbs want it probed first: advice the game
        # refuses is the one thing advice must never be.
        blocked, hop = self._blocked_by_warden()
        if blocked is not None and hop is not None:
            # An open host a warden still holds is exactly what `pivot`
            # walks past, and the brief used to require the hop shut, so
            # it said `jack out` at trace three about a door the verb
            # would have opened (D88).
            if (char.has_technique('pivot') and node.open
                    and hop.known and hop.uid in node.edges):
                return (f'pivot {hop.uid}',) + steps
            challenge = self.credential_challenge(blocked)
            # The chromed answer: the network is a room, and a room does
            # not have a desk (D88). Once a run, and only against a
            # warden nothing else you carry would satisfy.
            if ('native' in char.riders() and self.native <= 0
                    and 'sig:native' not in self.spent
                    and hop.uid in node.edges
                    and (challenge is None or challenge.impossible)):
                return ('native', f'connect {hop.uid}') + steps
            if (char.has_technique('pretext') and hop.mapped
                    and ('pretext', hop.uid) not in self.tried
                    and challenge is not None and not challenge.impossible):
                shut = [s for s in hop.services if not s.cracked]
                if shut:
                    return (f'pretext {hop.uid} {shut[0].key}',) + steps
        # Two doors on one host and one action that opens both. Only while
        # the room is quiet: chaining is two cracks' worth of noise in one
        # action, which is a bargain when nothing is listening and a way
        # of putting a network into lockdown by tick ten when something
        # is. Speed is worth noise early and never worth it late (D80).
        if (first.startswith('crack ') and char.has_technique('chain')
                and self.alert == 'green' and self.trace_pct < 0.5):
            parts = first.split()
            if len(parts) >= 3 and '--chain' not in first:
                target = self.net.node(parts[1])
                if target is not None:
                    shut = [s for s in target.services if not s.cracked
                            and self._odds_for(target, s) >= self.hopeless]
                    if (len(shut) >= 2
                            and ('chain', target.uid) not in self.tried):
                        # No service named: `--chain` takes two, and given
                        # one name it refuses rather than guessing.
                        return (f'crack {target.uid} --chain',) + steps[1:]
        # A host whose only way in is cryptography, and the ranks to derive
        # a key from traffic instead of breaking a door.
        if first.startswith('crack ') and char.has_technique('sidechannel'):
            parts = first.split()
            target = self.net.node(parts[1]) if len(parts) >= 2 else None
            if target is not None and target.uid == self.here:
                shut = [s for s in target.services if not s.cracked]
                if shut and all(node_content.SERVICE_BY_KEY[s.key].family
                                == 'crypto' for s in shut):
                    return ('sidechannel',) + steps
        return steps

    def _blocked_by_warden(self):
        """The warden on the next hop that will not let you past, and the
        host it is standing on. (None, None) when the way is clear."""
        route = self.route_to(self.net.objective_node)
        for uid in (route[:1] or []):
            hop = self.net.node(uid)
            if hop is None:
                continue
            for construct in hop.ice:
                if (construct.behaviour == 'warden' and construct.alive
                        and construct.known):
                    return construct, hop
        return None, None

    def residue_here(self) -> int:
        return int(getattr(self.node, 'residue', 0))

    def _odds_for(self, node, svc) -> float:
        """The chance of the best programme against one service."""
        skill_key, category = node_content.FAMILIES[svc.family]
        program = programs.best(self.char.deck.loaded, category)
        return crack_check(self, node, svc, program, quiet=True).chance

    def _blocked(self, node) -> bool:
        """A host you have looked at and cannot get through.

        Two ways that happens, and they look identical from outside: a warden
        that does not take credentials, and a host whose every service is out
        of reach of this build. Both are only counted once you have actually
        seen them, so the route offered is one the player could have worked
        out from the same information.
        """
        if node is None:
            return False
        for construct in node.ice:
            if construct.behaviour != 'warden' or not construct.alive:
                continue
            if not construct.known:
                continue
            challenge = self.credential_challenge(construct)
            # No challenge means it does not take credentials at all. A
            # challenge nobody could pass is the same wall with a politer sign
            # on it. Anything in between is a long shot, and a long shot is a
            # decision the player gets to make with the odds in front of them
            # rather than one the advice makes for them. One it has already
            # refused is a wall too, for the route's purposes (D90).
            if (challenge is None or challenge.impossible
                    or ('present', node.uid) in self.tried):
                return True
        return node.mapped and not node.open and not self._easiest(node)

    def objective_met(self) -> bool:
        """Whether the contract's requirement has been satisfied."""
        if not self.contract:
            return bool(self.haul)
        kind = self.contract.get('objective', 'exfiltrate')
        if kind == 'exfiltrate':
            # A mirror counts (D67): Static keep everything eleven times,
            # and the copy is the same file.
            want = self.net.objective_asset
            return any(uid in (want, f'{want}-mirror') for uid in self.haul)
        if kind == 'surveil':
            return self.observed_enough
        if kind == 'escort':
            # They have to have done the job and got out of it alive.
            escort = self.escort
            return bool(escort and escort['done'] and escort['state'] == 'out')
        # These three record what they acted on, and the check has to read it.
        # Taking `bool(done[kind])` accepted an implant left on the reception
        # desk, an edit pushed into whatever host you happened to be holding,
        # and a wipe of any junk file in the building, all paid in full against
        # a contract that named one host and one record. That is the game
        # failing to check the thing it is about, and it is also why a player
        # could not tell whether they had done the job: neither could it.
        if kind == 'implant':
            # And it has to have taken. Pushing it is the middle of the
            # job, not the end of it (D80).
            return (self.done.get('implant') == self.net.objective_node
                    and self.rooting <= 0)
        if kind == 'corrupt':
            return self.done.get('corrupt') == self.net.objective_node
        if kind == 'wipe':
            return self.done.get('wipe') == self.net.objective_asset
        return bool(self.haul)

    def haul_value(self) -> int:
        total = 0
        for uid in self.haul:
            found = self.net.find_asset(uid)
            if found:
                value = found[1].value
                if uid in self.sealed:
                    value = int(value * SEALED_HAUL)
                total += value
        return total

    def summary(self) -> dict:
        """Everything the city layer needs to apply consequences."""
        return {
            'outcome': self.outcome,
            'ticks': self.tick,
            'trace': int(self.trace),
            'alert': self.alert,
            'residue': self.residue_total,
            'haul': list(self.haul),
            'haul_value': self.haul_value(),
            'objective': self.objective_met(),
            'sealed': self.net.objective_asset in self.sealed,
            'faction': self.net.faction,
            'framed': self.framed,
            'observed': self.observed,
            'escort': dict(self.escort) if self.escort else None,
            'ally': dict(self.ally) if self.ally else None,
            'hurt': self.hurt,
            'events': list(self.events),
            'condition': self.condition.key if self.condition else '',
            'severed_by': self.severed_by,
            'grudge_killed': self.grudge_killed,
            'company': dict(self.company) if self.company else None,
            'reached': bool(self.net.objective_node
                            and (self.here == self.net.objective_node
                                 or (self.net.node(self.net.objective_node)
                                     or self.node).open)),
        }


# --------------------------------------------------------------------------
# helpers used by the run commands
# --------------------------------------------------------------------------


def crack_check(state: RunState, node: Node, svc: net_mod.ServiceInstance,
                program: programs.Program | None, quiet: bool = False) -> Check:
    """The standard service-intrusion check, fully itemised for D14."""
    skill_key, category = node_content.FAMILIES[svc.family]

    check = Check(name=f'crack {svc.key}', resistance=svc.difficulty * 2)
    check.add(f'{skill_key}', state.char.skill(skill_key) * 2)
    # Read the governing attribute from the skill itself rather than a second
    # copy of the mapping: the literal that used to live here went stale the
    # moment Hardware moved from Logic to Grit.
    attr = skill_content.BY_KEY[skill_key].attr
    check.add(attr, state.char.attr(attr))
    if program:
        rank = state.char.skill(skill_key)
        check.add(programs.held_label(program, rank, skill_key),
                  programs.held(program, rank) * 2)
        if 'dual_thread' in state.char.riders():
            # Threadpuller (D63): two programs against one target. The
            # second-best of the category rides along at its full rating,
            # and the implant's noise penalty is already paying for it.
            # One copy of the chosen program steps aside; a second copy of
            # the same thing is exactly what a spare is for.
            keys = list(state.char.deck.loaded)
            if program.key in keys:
                keys.remove(program.key)
            others = [programs.BY_KEY[k] for k in keys
                      if k in programs.BY_KEY
                      and programs.BY_KEY[k].category == program.category]
            if others:
                second = max(others, key=lambda p: p.rating)
                check.add(f'second thread: {second.name}',
                          programs.held(second, rank))
    else:
        check.add(f'no {category} loaded', -6)
    if svc.family == 'crypto':
        check.add('crypto gear', state.char.bonus('crypto_bonus'))
    else:
        check.add('gear', state.char.bonus('crack_bonus'))

    short = node.tier - state.tier
    if short > 0:
        check.add(f'{short} tier short of this zone', -3 * short, actionable=True)
    if state.impersonating > 0:
        check.add('impersonating a credential', 4)
    helper = state.ally_bonus('crack')
    if helper:
        check.add(f'{state.ally["name"]} working with you', helper)
    if quiet:
        check.add('working quietly', -2)
    if state.alert in ('red', 'lockdown'):
        check.add(f'network at {state.alert}', -2)
    # Tonight (D61). In the sum, by name, because a modifier that is not
    # in the sum is a hidden die.
    if state.condition is not None and state.condition.crack:
        check.add(state.condition.name.lower(), state.condition.crack)
    return check
