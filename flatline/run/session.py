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
#: Trace added per tick before any modifier. Deliberately small: most of the
#: pressure should come from what the player does, not from the clock alone.
TRACE_PER_TICK = 1.1
#: How many ticks of trace history `status` keeps for its sparkline. Sixty is
#: comfortably longer than any run has ever lasted and short enough that it is
#: never worth thinking about.
TRACE_HISTORY = 60
#: How much of a noisy action's noise converts straight into trace.
NOISE_TO_TRACE = 0.30
#: Local noise removed from every node each tick.
NOISE_DECAY = 2
#: Node noise at which dormant ICE there wakes up.
NOISE_WAKE = 8
#: Node noise at which the whole network escalates one alert level.
NOISE_ESCALATE = 18
#: Residue converted to faction heat after the run, per point.
RESIDUE_TO_HEAT = 0.55

#: Damage a component takes per ICE strike that lands on the deck.
DECK_HIT = 1

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

    # ------------------------------------------------------------------
    # construction
    # ------------------------------------------------------------------

    @classmethod
    def begin(cls, net: Network, char: Character, rng: Stream,
              console: Console, contract: dict | None = None,
              phase: str = 'morning') -> RunState:
        state = cls(net=net, char=char, rng=rng, console=console,
                    contract=contract, here=net.entry, phase=phase)
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
        # The character's own noise_mult already carries chrome riders like the
        # Threadpuller's doubling, because those are declared as penalties.
        amount *= self.char.mult('noise_mult') * node.data_type.noise_mult
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
        self.trace = min(TRACE_MAX, self.trace + max(0.0, amount))

    def leave_residue(self, amount: float, node: Node | None = None) -> int:
        node = node or self.node
        amount *= self.char.mult('residue_mult')
        if (self.char.origin == 'defector'
                and fac_content.BY_KEY[self.net.faction].kind == 'corp'):
            # Policy reader: you know what corporate networks log and when.
            amount *= 0.85
        value = max(0, int(round(amount)))
        node.residue += value
        return value

    def escalate(self, steps: int = 1, why: str = '') -> None:
        levels = ice_content.ALERT_LEVELS
        i = levels.index(self.alert)
        if self.char.origin == 'expolice' and self.net.faction == 'nightwatch':
            # Read the room: you know their escalation playbook.
            if self.rng.chance(0.5):
                return
        new = min(len(levels) - 1, i + steps)
        if new == i:
            return
        self.alert = levels[new]
        self.console.blank()
        self.console.raw(f'[err][bold]ALERT: {self.alert.upper()}[/][/]  '
                         f'[dim]{ice_content.ALERT_BLURB[self.alert]}[/]')
        if why:
            self.console.say(f'[dim]{why}[/]')
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
        real = max(1, int(round(ticks * cost)))
        for _ in range(real):
            if not self.running:
                return
            self.tick += 1
            was = self.trace_pct
            self.add_trace(TRACE_PER_TICK)
            self.trace_history.append(round(self.trace, 2))
            del self.trace_history[:-TRACE_HISTORY]
            # The clock made physical. One line at most, and only on a
            # threshold, because narrating every point of trace would turn
            # the tensest number in the game into wallpaper.
            felt = cyberspace.pressure(was, self.trace_pct)
            if felt:
                self.console.blank()
                self.console.say(f'[trace]{felt}[/]')
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
            self._ice_tick()
            self._surveil_tick()
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
            threshold = max(3, NOISE_WAKE - construct.rating)
            if node.noise < threshold:
                continue
            if construct.state == 'dormant':
                construct.state = 'awake'
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

            if construct.state == 'dormant':
                threshold = max(3, NOISE_WAKE - construct.rating)
                if self.node.noise >= threshold and construct in self.node.ice:
                    construct.state = 'awake'
                    if not self.woken:
                        self.woken = True
                        self.console.blank()
                        wakes = cyberspace.signature(
                            self.net.faction).ice_wakes
                        self.console.say(f'[ice]{wakes}[/]')
                    self._tell(construct)
                continue

            if construct.state in ('awake', 'locked'):
                if construct.telegraphed:
                    self._strike(construct)
                else:
                    self._tell(construct)

    def _tell(self, construct: IceInstance) -> None:
        """One line, the tick before it acts. Never says what it will do."""
        data = construct.data
        if not data.tells:
            return
        construct.telegraphed = True
        lead = self.char.bonus('tell_lead')
        if self.char.origin == 'expolice':
            lead += 1
        if self.playbook:
            lead += 1
        line = self.rng.pick(data.tells)
        name = data.name if (construct.known or lead > 0) else 'something'
        self.console.blank()
        self.console.say(f'[ice]{line}[/]')
        if construct.known or lead > 0:
            self.console.say(f'[dim]that reads as {name}.[/]')
            construct.known = True
        self.log(f'tell: {name}')

    def _strike(self, construct: IceInstance) -> None:
        data = construct.data
        construct.telegraphed = False
        self.console.blank()
        self.console.raw(f'[err]{data.strike}[/]')
        self.log(f'strike: {data.name}')
        construct.known = True

        # A construct that declares `alert_jump` escalates by that much
        # rather than by the generic one. Three of them declared it and were
        # being escalated generically, which made their whole distinguishing
        # feature decorative.
        jump = int(data.effects.get('alert_jump', 1))

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
            self.locked.append(construct)
            construct.state = 'locked'
        self.add_trace(data.trace)
        damage = data.damage + construct.rating // 2
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
                # Prefer cutting behind the player, which is the whole point:
                # a herder pushes you deeper rather than boxing you in place.
                if node.uid == self.here or edge == self.here:
                    continue
                candidates.append((node.uid, edge))
        if not candidates:
            return None

        for a, b in self.rng.shuffled(candidates):
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

    def _check_trace(self) -> None:
        if self.trace < TRACE_MAX:
            return
        self.console.blank()
        self.console.raw('[err][bold]TRACE COMPLETE.[/][/]')
        self.console.say('The connection is cut from the far end. Somebody now '
                         'has a file with your working habits in it.')
        self.finish('severed')

    # ------------------------------------------------------------------
    # damage
    # ------------------------------------------------------------------

    def take_damage(self, amount: int, black: bool, source: str = '') -> None:
        amount = max(0, int(round(amount * self.char.mult('ice_dr'))))
        if not amount:
            return
        # Psyche rank 4: you are not present for this. The deck is.
        if self.dissociated > 0:
            black = False
            to_body = False
            slot = self.rng.pick(list(self.char.deck.parts))
            level = self.char.deck.hurt(slot, DECK_HIT)
            self.console.warn(f'It lands on the {slot} instead of on you '
                              f'[dim](damage {level}/3)[/].')
            return
        # The Deepjack routes everything through you rather than the deck.
        to_body = black or 'deep_jack' in self.char.installed

        if not to_body:
            slot = self.rng.pick(list(self.char.deck.parts))
            level = self.char.deck.hurt(slot, DECK_HIT)
            self.console.warn(f'The {slot} takes it '
                              f'[dim](damage {level}/3)[/].')
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
            check.add(forger.name, forger.rating * 2)
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

    # ------------------------------------------------------------------
    # resolution
    # ------------------------------------------------------------------

    def finish(self, outcome: str) -> None:
        if not self.running:
            return
        self.outcome = outcome
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
        # the game telling you something you have not earned.
        asset_name = (asset[1].name if asset and asset[0].mapped
                      else 'the record they want')

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

        return Brief(aim=aim, where=self._objective_where(target, found),
                     progress=self._objective_progress(kind, asset_name),
                     done=self.objective_met(),
                     steps=self._objective_steps(kind, target, found))

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
            return (f'{self.observed} of {self.SURVEIL_TICKS} clean ticks '
                    f'banked' + (', which is enough' if self.observed_enough
                                 else ''))
        if kind == 'escort' and self.escort:
            return (f'{self.escort["name"]} is on {self.escort["node"]}, '
                    f'{self.escort["state"]}'
                    + (', carrying it' if self.escort['done'] else ''))
        if kind == 'exfiltrate':
            return ('you have it' if self.objective_met()
                    else f'{asset_name} is still theirs')
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
        if target is None:
            return ('scan',)
        if not found:
            return self._search_steps()
        if self.here != self.net.objective_node:
            return self._approach_steps()
        return self._finish_steps(kind)

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
        if unmapped:
            return (f'probe {self._deepest(unmapped).uid}',)
        shut = self._first_shut()
        if shut:
            return (f'crack {shut[0]} {shut[1]}', f'connect {shut[0]}')
        fresh = [n for n in self.net.nodes.values()
                 if n.open and n.uid not in self.scanned and n.uid != self.here]
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
        if warden is not None and self.credential_challenge(warden) is not None:
            return (f'connect {step} --present',)
        return (f'connect {step}',)

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
        return ('jack out',)

    def _tier_steps(self) -> tuple[str, ...] | None:
        """The way to hold a higher access tier, if there is one in reach.

        Cracking every service on an auth server is the standard route to a
        badge. Only ones at or below your current tier: sending somebody at a
        locked door to open a locked door behind it is not advice.
        """
        for node in self.net.nodes.values():
            if node.type != 'auth' or not node.known or node.tier > self.tier:
                continue
            if not node.mapped:
                return (f'probe {node.uid}',)
            way = self._easiest(node)
            if way:
                return (f'crack {node.uid} {way}',)
        return None

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
        for svc in node.services:
            if svc.cracked:
                continue
            _, category = node_content.FAMILIES[svc.family]
            program = programs.best(self.char.deck.loaded, category)
            chance = crack_check(self, node, svc, program).chance
            if chance > best_chance:
                best, best_chance = svc.key, chance
        return best

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
        asset = self.net.objective_asset
        return {
            'exfiltrate': (f'pull {asset}' if asset else 'pull',),
            'implant': ('push',),
            'corrupt': ('push',),
            'wipe': (f'wipe {asset}' if asset else 'wipe',),
            'surveil': ('observe',),
            'escort': ('signal move', 'signal out'),
        }.get(kind, ('pull',))

    def _first_shut(self) -> tuple[str, str] | None:
        """An adjacent host you have looked at and not opened, and its way in."""
        shut = [n for n in (self.net.node(u) for u in self.node.edges)
                if n is not None and not n.open and n.mapped
                and self._easiest(n)]
        if not shut:
            return None
        node = self._deepest(shut)
        return node.uid, self._easiest(node)

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
            # rather than one the advice makes for them.
            if challenge is None or challenge.impossible:
                return True
        return node.mapped and not node.open and not self._easiest(node)

    def objective_met(self) -> bool:
        """Whether the contract's requirement has been satisfied."""
        if not self.contract:
            return bool(self.haul)
        kind = self.contract.get('objective', 'exfiltrate')
        if kind == 'exfiltrate':
            return self.net.objective_asset in self.haul
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
            return self.done.get('implant') == self.net.objective_node
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
                total += found[1].value
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
            'faction': self.net.faction,
            'framed': self.framed,
            'observed': self.observed,
            'escort': dict(self.escort) if self.escort else None,
            'ally': dict(self.ally) if self.ally else None,
            'hurt': self.hurt,
            'events': list(self.events),
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
        check.add(program.name, program.rating * 2)
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
    return check
