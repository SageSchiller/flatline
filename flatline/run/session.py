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
from ..content import factions as fac_content
from ..content import ice as ice_content
from ..content import nodes as node_content
from ..content import programs
from ..model.character import Character
from ..rng import Stream
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
    trace: float = 0.0
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
    #: Consecutive ticks of clean residency, for a surveil job. Reset by the
    #: alert going red, because being watched is the opposite of watching.
    observed: int = 0
    #: Set once a surveil job has banked enough. Latches: having held it, you
    #: have held it, and the walk back out cannot take it away.
    observed_enough: bool = False

    outcome: str = 'running'
    #: Human-readable record, shown by `log` and after the run.
    events: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # construction
    # ------------------------------------------------------------------

    @classmethod
    def begin(cls, net: Network, char: Character, rng: Stream,
              console: Console, contract: dict | None = None) -> RunState:
        state = cls(net=net, char=char, rng=rng, console=console,
                    contract=contract, here=net.entry)
        state.focus = char.focus
        node = net.node(net.entry)
        if node:
            node.known = node.open = node.mapped = True
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

            if daemon['task'] == 'hold':
                # Keeps a node quiet by absorbing the traffic you generated.
                node.noise = max(0, node.noise - (1 + rating // 2))
            elif daemon['task'] == 'grind':
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
            elif daemon['task'] == 'noise':
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
        for construct in node.live_ice:
            if construct.behaviour == 'trap':
                continue
            threshold = max(3, NOISE_WAKE - construct.rating)
            if node.noise < threshold:
                continue
            if construct.state == 'dormant':
                construct.state = 'awake'
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

        if data.behaviour == 'probe':
            self.add_trace(data.trace + construct.rating)
            self.escalate(1, f'{data.name} reported your position.')
            construct.state = 'dormant'
            return

        if data.behaviour == 'sentry':
            self.add_trace(data.trace + construct.rating * 0.5)
            self.escalate(1, f'{data.name} filed on your session.')
            if 'null_escalation' in self.char.riders():
                self.escalate(1, 'There was nothing there to file, which is '
                                 'considerably worse than something.')
            construct.state = 'dormant'
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
                self.finish('severed')
            else:
                self.finish('flatline')
            return
        self.finish('severed')

    # ------------------------------------------------------------------
    # traps
    # ------------------------------------------------------------------

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
        if kind in ('corrupt', 'wipe', 'implant'):
            return bool(self.done.get(kind))
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
    attr = {'intrusion': 'logic', 'cryptography': 'logic',
            'subterfuge': 'guile', 'hardware': 'logic'}[skill_key]
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
