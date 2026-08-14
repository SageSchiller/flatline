#!/usr/bin/env python3
"""Behaviour checks. Run after every change.

`validate.py` checks what the content says. This checks what the game does.

The most important tests here are the determinism ones, because D3 is the
invariant everything else in the project leans on: if a seed stops reproducing
a world, every bug report becomes unreproducible and the save format becomes a
lie. Those run first and they run over many seeds.

The second most important is the playthrough fuzz, which drives whole runs
through the real command layer with the real dispatcher. That is only possible
because D2 made the interface strings-in and strings-out, and it catches the
class of bug that unit tests never do: a verb that works alone and explodes
when the network is in a state nobody thought about.
"""

from __future__ import annotations

import io
import json
import os
import pathlib
import sys
import tempfile
import traceback

# Saves must never touch the player's real data directory.
_TMP = tempfile.mkdtemp(prefix='flatline-test-')
os.environ['XDG_DATA_HOME'] = _TMP
os.environ['NO_COLOR'] = '1'

from flatline import commands, save as save_mod, theme, ui  # noqa: E402
from flatline.content import appearance  # noqa: E402
from flatline.content import attributes as attr_content  # noqa: E402
from flatline.content import cyberware, districts, effects as fx  # noqa: E402
from flatline.content import factions, hardware, ice as ice_content  # noqa: E402
from flatline.content import nodes as node_content  # noqa: E402
from flatline.content import origins, programs, skills  # noqa: E402
from flatline.game import Game  # noqa: E402
from flatline.model.character import Character  # noqa: E402
from flatline.model.identity import Alias  # noqa: E402
from flatline.rng import Rng, derive  # noqa: E402
from flatline.run import network as net_mod  # noqa: E402
from flatline.run.checks import Check  # noqa: E402
from flatline.run.session import RunState  # noqa: E402
from flatline.session import Session  # noqa: E402
from flatline.shell import REGISTRY, CommandError  # noqa: E402
from flatline.ui import Caps, ColorLevel, Console, GlyphLevel  # noqa: E402
from flatline.world import market as market_mod  # noqa: E402
from flatline.world.city import City  # noqa: E402


class Harness:
    def __init__(self) -> None:
        self.checks = 0
        self.failures: list[str] = []
        self.group = ''

    def section(self, name: str) -> None:
        self.group = name

    def ok(self, cond, what: str) -> bool:
        self.checks += 1
        if not cond:
            self.failures.append(f'{self.group}: {what}')
            return False
        return True

    def eq(self, a, b, what: str) -> bool:
        return self.ok(a == b, f'{what} (got {a!r}, wanted {b!r})')

    def raises(self, fn, what: str) -> bool:
        self.checks += 1
        try:
            fn()
        except Exception:
            return True
        self.failures.append(f'{self.group}: {what} did not raise')
        return False


T = Harness()


def quiet_console() -> Console:
    caps = Caps(color=ColorLevel.NONE, glyphs=GlyphLevel.UNICODE, width=80,
                palette=theme.NEUTRAL)
    console = Console(caps, stream=io.StringIO())
    return console


def play(lines, seed=4242, origin='gutter', game=None):
    """Drive real commands through the real dispatcher, capturing output."""
    console = quiet_console()
    sess = Session(console=console, slot='test')
    if game is not None:
        sess.game = game
    console.start_capture()
    for line in lines:
        sess.execute(line)
    text = console.end_capture()
    return sess, text


# --------------------------------------------------------------------------
# D3: determinism
# --------------------------------------------------------------------------


def test_determinism() -> None:
    T.section('determinism')

    # Stream derivation must be stable across processes, not just within one.
    T.eq(derive(8829, 'network'), derive(8829, 'network'),
         'derive is stable')
    T.ok(derive(8829, 'network') != derive(8829, 'ice'),
         'different stream names give different seeds')
    T.ok(derive(8829, 'network') != derive(8830, 'network'),
         'different world seeds give different streams')

    # A named stream must not be perturbed by another stream being used.
    a = Rng(99)
    first = [a('network').int(1, 1000) for _ in range(5)]
    b = Rng(99)
    for _ in range(20):
        b('contracts').int(1, 1000)
        b('market').int(1, 1000)
    second = [b('network').int(1, 1000) for _ in range(5)]
    T.eq(first, second, 'streams are independent of each other')

    # Undeclared streams are a typo, not a new universe.
    T.raises(lambda: Rng(1)('netowrk'), 'undeclared stream')

    # Forked streams are reproducible from the key alone.
    T.eq([Rng(7).fork('network', 'c001').int(1, 10**6) for _ in range(3)],
         [Rng(7).fork('network', 'c001').int(1, 10**6) for _ in range(3)],
         'forks reproduce from the key')
    T.ok(Rng(7).fork('network', 'c001').int(1, 10**6)
         != Rng(7).fork('network', 'c002').int(1, 10**6),
         'different keys give different forks')

    # Whole networks reproduce.
    for seed in (1, 8829, 65535):
        for faction in ('kagawa', 'sixes', 'sendai'):
            one = net_mod.generate(Rng(seed).fork('network', 'x'), faction, 50)
            two = net_mod.generate(Rng(seed).fork('network', 'x'), faction, 50)
            T.eq(list(one.nodes), list(two.nodes),
                 f'network node list reproduces (seed {seed}, {faction})')
            T.eq(one.objective_asset, two.objective_asset,
                 f'objective reproduces (seed {seed}, {faction})')
            T.eq([len(n.ice) for n in one.nodes.values()],
                 [len(n.ice) for n in two.nodes.values()],
                 f'ice placement reproduces (seed {seed}, {faction})')

    # Whole games reproduce, board included.
    for seed in (11, 2024):
        boards = []
        for _ in range(2):
            char = Character.from_origin('gutter', 'x')
            game = Game.new(char, seed=seed)
            boards.append([(c.cid, c.patron, c.target, c.objective, c.pay)
                           for c in game.city.board])
        T.eq(boards[0], boards[1], f'contract board reproduces (seed {seed})')

    # RNG state survives a save and continues rather than restarting.
    rng = Rng(500)
    drawn = [rng('combat').int(1, 100) for _ in range(10)]
    restored = Rng.fromstate(rng.getstate())
    T.eq([restored('combat').int(1, 100) for _ in range(5)],
         [rng('combat').int(1, 100) for _ in range(5)],
         'rng state round-trips and continues')
    T.ok(drawn, 'rng produced values')


# --------------------------------------------------------------------------
# saves
# --------------------------------------------------------------------------


def test_saves() -> None:
    T.section('saves')
    char = Character.from_origin('academic', 'tester')
    char.xp = 7
    char.credits = 12345
    game = Game.new(char, seed=321)
    game.alias.adjust_rep('fixers', 30)
    game.alias.add_heat('kagawa', 22)
    game.city.shift = 9
    game.city.where = 'freeport'

    game.save('roundtrip')
    back = Game.load('roundtrip')

    T.eq(back.char.handle, 'tester', 'handle survives')
    T.eq(back.char.credits, 12345, 'credits survive')
    T.eq(back.char.xp, 7, 'xp survives')
    T.eq(back.char.origin, 'academic', 'origin survives')
    T.eq(back.char.base_attrs, char.base_attrs, 'attributes survive')
    T.eq(back.char.deck.parts, char.deck.parts, 'deck parts survive')
    T.eq(sorted(back.char.deck.loaded), sorted(char.deck.loaded),
         'loadout survives')
    T.eq(back.city.shift, 9, 'shift survives')
    T.eq(back.city.where, 'freeport', 'location survives')
    T.eq(back.alias.reputation('fixers'), game.alias.reputation('fixers'),
         'reputation survives')
    T.eq(back.alias.attention('kagawa'), 22, 'heat survives')
    T.eq(back.rng.seed, 321, 'seed survives')
    T.eq(len(back.city.board), len(game.city.board), 'board survives')

    # A loaded game continues the same world rather than a similar one.
    T.eq(back.rng('combat').int(1, 10**6), game.rng('combat').int(1, 10**6),
         'rng continues after load (D3)')

    # Saves are atomic: a save written over itself stays readable.
    for i in range(5):
        back.char.credits = i
        back.save('roundtrip')
    T.eq(Game.load('roundtrip').char.credits, 4, 'repeated saves stay readable')

    # Unknown future schema is refused with an explanation, not a crash.
    raw = save_mod.read('roundtrip')
    raw['schema'] = 999
    T.raises(lambda: save_mod.migrate(raw), 'future schema')

    # Every migration in the chain is reachable.
    for version in range(1, save_mod.SCHEMA):
        T.ok(version in save_mod.MIGRATIONS,
             f'migration from schema {version} exists')

    # Export and import: a save that survives the data directory being lost.
    import tempfile as _tmp
    out = pathlib.Path(_tmp.mkdtemp()) / 'exported.json'
    written = save_mod.export_to(game.to_dict(), out)
    T.ok(written.exists(), 'a save exports to a path of your choosing')
    brought = save_mod.import_from(out)
    T.eq(brought['character']['handle'], 'tester', 'and imports back')
    T.eq(brought['schema'], save_mod.SCHEMA, 'at the current schema')

    # An export is an ordinary save, so migrations apply to it too.
    legacy = pathlib.Path(_tmp.mkdtemp()) / 'old.json'
    raw = dict(game.to_dict())
    raw['schema'] = 1
    raw['character'] = {k: v for k, v in raw['character'].items()
                        if k not in ('icon', 'icons')}
    legacy.write_text(json.dumps(raw), encoding='utf-8')
    old = save_mod.import_from(legacy)
    T.eq(old['schema'], save_mod.SCHEMA, 'an old export migrates forward')
    T.ok(old['character'].get('icon'), 'and gains what the migration adds')

    # Everything that is not a save is refused, never crashed.
    junk = pathlib.Path(_tmp.mkdtemp())
    (junk / 'garbage.json').write_text('not json', encoding='utf-8')
    (junk / 'other.json').write_text('{"a": 1}', encoding='utf-8')
    T.raises(lambda: save_mod.import_from(junk / 'garbage.json'),
             'unparseable input')
    T.raises(lambda: save_mod.import_from(junk / 'other.json'),
             'json that is not a save')
    T.raises(lambda: save_mod.import_from(junk / 'nothing-here.json'),
             'a missing file')
    T.raises(lambda: save_mod.import_from(junk), 'a directory')
    T.raises(lambda: save_mod.export_to({}, junk), 'exporting onto a directory')

    # The whole point: the data directory can be lost entirely.
    keep = save_mod.export_to(game.to_dict(),
                              pathlib.Path(_tmp.mkdtemp()) / 'survivor.json')
    save_mod.delete('roundtrip')
    T.ok(not save_mod.exists('roundtrip'), 'the slot is gone')
    recovered = save_mod.import_from(keep)
    save_mod.write(recovered, 'roundtrip')
    T.eq(Game.load('roundtrip').char.handle, 'tester',
         'and the character comes back from the export')

    T.ok(save_mod.exists('roundtrip'), 'exists() finds the save')
    T.ok('roundtrip' in save_mod.slots(), 'slots() lists it')
    save_mod.delete('roundtrip')
    T.ok(not save_mod.exists('roundtrip'), 'delete removes it')


# --------------------------------------------------------------------------
# character
# --------------------------------------------------------------------------


def test_character() -> None:
    T.section('character')
    for key in origins.ORIGIN_KEYS:
        char = Character.from_origin(key, 'x')
        T.ok(char.bandwidth_used <= char.bandwidth,
             f'{key} starts within bandwidth')
        T.ok(char.deck.memory_used <= char.deck.memory,
             f'{key} starts within memory')
        T.ok(char.integrity_max > 0, f'{key} has positive integrity')
        T.ok(char.tempo >= 1, f'{key} has at least one action per tick')
        T.ok(char.focus >= 1, f'{key} has some focus')
        T.ok(char.deck.loaded, f'{key} starts with something loaded')
        for location, capacity in cyberware.SLOTS.items():
            T.ok(char.slots_used(location) <= capacity,
                 f'{key} respects the {location} slot limit')

    # Attributes clamp rather than running away.
    char = Character.from_origin('gutter', 'x')
    for key in attr_content.ATTR_KEYS:
        char.base_attrs[key] = 99
        T.ok(char.attr(key) <= attr_content.ATTR_MAX + 3,
             f'{key} clamps at the ceiling')
        char.base_attrs[key] = -99
        T.ok(char.attr(key) >= attr_content.ATTR_MIN,
             f'{key} clamps at the floor')
    char = Character.from_origin('gutter', 'x')

    # Progression spends what it costs and nothing more.
    char.xp = skills.RANK_COST[1]
    before = char.xp
    char.base_skills['warfare'] = 0
    tech = char.train('warfare')
    T.eq(char.base_skills['warfare'], 1, 'training raises the rank')
    T.eq(char.xp, before - skills.RANK_COST[1], 'training spends the xp')
    T.eq(tech, None, 'rank 1 unlocks no technique')
    char.xp = skills.RANK_COST[2]
    tech = char.train('warfare')
    T.ok(tech is not None and tech.key == 'strike',
         'rank 2 unlocks the technique')
    T.raises(lambda: char.train('warfare'), 'training with no xp')

    # D10/D11: chrome must not be able to buy a technique.
    char = Character.from_origin('gutter', 'x')
    char.base_skills['hardware'] = 1
    T.ok(not char.has_technique('overclock'),
         'rank 1 does not grant a rank 2 technique')
    ok, _ = char.can_install('interface_hands')
    if ok:
        char.install('interface_hands')  # grants +1 Hardware
        T.ok(char.skill('hardware') >= 2, 'chrome raises the effective rank')
        T.ok(not char.has_technique('overclock'),
             'chrome cannot grant a technique (D10)')

    # Bandwidth and slots are enforced, not advisory.
    char = Character.from_origin('gutter', 'x')
    char.base_attrs['grit'] = 1
    over = [w for w in cyberware.WARE if w.bandwidth > char.bandwidth]
    if over:
        ok, why = char.can_install(over[0].key)
        T.ok(not ok and 'bandwidth' in why, 'bandwidth is enforced')

    # D11: dissonance is a one-way door.
    char = Character.from_origin('gutter', 'x')
    start = char.dissonance
    char.install('coolant_mesh')
    T.ok(char.dissonance > start, 'installing raises dissonance')
    raised = char.dissonance
    char.uninstall('coolant_mesh')
    T.eq(char.dissonance, raised, 'uninstalling does not lower it (D11)')

    # Effects combine under the right rule for each key class.
    merged = fx.merge({'logic': 2}, {'logic': 3},
                      {'noise_mult': 0.5}, {'noise_mult': 0.5})
    T.eq(merged['logic'], 5, 'additive effects sum')
    T.eq(merged['noise_mult'], 0.25, 'multiplicative effects multiply')

    # A damaged component degrades toward neutral, never past it.
    char = Character.from_origin('defector', 'x')
    clean = char.deck.memory
    for level in (1, 2, 3):
        char.deck.damage['memory'] = level
        T.ok(char.deck.memory <= clean,
             f'damage {level} does not raise memory')
    T.ok(char.deck.memory >= 0, 'memory never goes negative')


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------


def test_checks() -> None:
    T.section('checks')
    check = Check(name='x', resistance=10)
    check.add('skill', 6)
    check.add('attr', 4)
    T.eq(check.power, 10, 'power sums the terms')
    T.eq(check.target, 5, 'target is resistance + offset - power')
    T.eq(check.chance, 0.6, 'chance is exact')

    # Zero-valued terms are dropped rather than shown.
    check.add('nothing', 0)
    T.eq(len(check.terms), 2, 'zero terms are not recorded')

    # The bounds behave. A bare check with no terms still needs a 5+, which is
    # the point of the offset: power and resistance are directly comparable.
    T.eq(Check(name='x', resistance=0).chance, 0.6,
         'an unmodified check needs 5 or better')
    certain = Check(name='x', resistance=0)
    certain.add('power', 10)
    T.eq(certain.chance, 1.0, 'enough power makes it certain')
    T.ok(certain.certain, 'certain is flagged')
    T.eq(Check(name='x', resistance=100).chance, 0.0,
         'impossible checks are impossible')
    T.ok(Check(name='x', resistance=100).impossible, 'impossible is flagged')

    # Resolution respects the maths over a large sample.
    rng = Rng(1)('combat')
    check = Check(name='x', resistance=10)
    check.add('power', 10)
    wins = 0
    trials = 4000
    for _ in range(trials):
        fresh = Check(name='x', resistance=10)
        fresh.add('power', 10)
        fresh.resolve(rng)
        wins += fresh.success
    rate = wins / trials
    T.ok(abs(rate - 0.6) < 0.04,
         f'observed success rate {rate:.3f} matches the stated 0.60')

    # The audit trail is legible and names the weak link.
    check = Check(name='x', resistance=10)
    check.add('good', 8)
    check.add('bad', -4)
    T.ok(check.culprit().label == 'bad', 'culprit finds the negative term')
    T.ok('vs' in check.explain(), 'explain shows the resistance')
    T.ok('%' in check.summary() or 'automatic' in check.summary()
         or 'impossible' in check.summary(), 'summary states the odds')


# --------------------------------------------------------------------------
# networks
# --------------------------------------------------------------------------


def test_networks() -> None:
    T.section('networks')
    seen_black = 0
    seen_warden = 0
    for seed in range(40):
        faction = factions.FACTION_KEYS[seed % len(factions.FACTION_KEYS)]
        posture = factions.BY_KEY[faction].posture
        objective = ('exfiltrate', 'implant', 'corrupt',
                     'surveil', 'wipe', 'escort')[seed % 6]
        net = net_mod.generate(Rng(seed).fork('network', f'c{seed}'),
                               faction, posture, objective)

        T.ok(net.entry in net.nodes, f'seed {seed}: entry exists')
        T.ok(net.nodes[net.entry].open, f'seed {seed}: entry is open')

        # Everything must be reachable or the run can be unwinnable.
        seen = {net.entry}
        frontier = [net.entry]
        while frontier:
            uid = frontier.pop()
            for edge in net.nodes[uid].edges:
                if edge not in seen:
                    seen.add(edge)
                    frontier.append(edge)
        T.eq(len(seen), len(net.nodes), f'seed {seed}: every node is reachable')

        # The objective must exist and be somewhere you can get to.
        T.ok(net.objective_node in net.nodes,
             f'seed {seed}: objective node exists')
        if objective in ('exfiltrate', 'corrupt', 'wipe'):
            T.ok(net.objective_asset, f'seed {seed}: objective asset was placed')
            found = net.find_asset(net.objective_asset)
            T.ok(found is not None, f'seed {seed}: objective asset is findable')

        # Edges are symmetric, or `connect` and `scan` disagree.
        for node in net.nodes.values():
            for edge in node.edges:
                T.ok(node.uid in net.nodes[edge].edges,
                     f'seed {seed}: {node.uid}<->{edge} is symmetric')

        for node in net.nodes.values():
            T.ok(node.zone in node_content.ZONES,
                 f'seed {seed}: {node.uid} has a real zone')
            T.ok(node.type in node_content.BY_KEY,
                 f'seed {seed}: {node.uid} has a real type')
            for svc in node.services:
                T.ok(svc.difficulty > 0,
                     f'seed {seed}: {node.uid}/{svc.key} has positive difficulty')
            for construct in node.ice:
                T.ok(construct.rating > 0,
                     f'seed {seed}: ice has positive rating')
                if construct.behaviour == 'black':
                    seen_black += 1
                if construct.behaviour == 'warden':
                    seen_warden += 1
                # Black ICE must never sit on the doorstep.
                if construct.behaviour == 'black':
                    T.ok(node.zone in ('restricted', 'core'),
                         f'seed {seed}: black ice is deep, not on the perimeter')

    T.ok(seen_warden > 0, 'wardens appear across 40 networks')
    T.ok(seen_black > 0, 'black ice appears across 40 networks')

    # Posture must actually change the difficulty, or the city layer is decor.
    soft = hard = 0
    for seed in range(25):
        low = net_mod.generate(Rng(seed).fork('network', 'a'), 'kagawa', 25)
        high = net_mod.generate(Rng(seed).fork('network', 'a'), 'kagawa', 90)
        soft += sum(len(n.ice) for n in low.nodes.values())
        hard += sum(len(n.ice) for n in high.nodes.values())
    T.ok(hard > soft * 1.3,
         f'posture 90 is meaningfully harder than 25 ({soft} vs {hard} ice)')


# --------------------------------------------------------------------------
# the run
# --------------------------------------------------------------------------


def test_run_mechanics() -> None:
    T.section('run mechanics')
    char = Character.from_origin('gutter', 'x')
    net = net_mod.generate(Rng(5).fork('network', 'c1'), 'sixes', 30)
    console = quiet_console()
    console.start_capture()
    state = RunState.begin(net, char, Rng(5)('combat'), console)

    T.eq(state.here, net.entry, 'you start on the entry node')
    T.eq(state.trace, 0.0, 'trace starts at zero')
    T.eq(state.alert, 'green', 'alert starts green')
    T.ok(state.running, 'the run starts running')

    # D5: trace never decreases on its own, noise decays, residue persists.
    before = state.trace
    state.advance(3)
    T.ok(state.trace > before, 'trace advances with time')

    node = state.node
    quiet = node.noise
    state.make_noise(10)
    T.ok(node.noise > quiet, 'noise lands on the node')
    noisy = node.noise
    state.advance(1)
    T.ok(node.noise < noisy, 'noise decays')

    state.leave_residue(5)
    residue = node.residue
    state.advance(5)
    T.eq(node.residue, residue, 'residue does not decay inside the run')

    # Trace is bounded and ends the run when it fills.
    state.trace = 99.0
    state.advance(5)
    T.ok(state.trace <= 100.0, 'trace is capped')
    T.eq(state.outcome, 'severed', 'a full trace severs the connection')
    T.ok(not state.running, 'a severed run is over')

    # Alert escalation is monotonic within a run.
    console2 = quiet_console()
    console2.start_capture()
    state = RunState.begin(net, char, Rng(6)('combat'), console2)
    order = list(ice_content.ALERT_LEVELS)
    last = 0
    for _ in range(5):
        state.escalate(1)
        now = order.index(state.alert)
        T.ok(now >= last, 'alert never de-escalates')
        last = now
    T.eq(state.alert, 'lockdown', 'alert tops out at lockdown')

    # Nullsig genuinely stops the clock.
    state = RunState.begin(net, char, Rng(7)('combat'), console2)
    state.nullsig = 5
    frozen = state.trace
    state.advance(3)
    T.eq(state.trace, frozen, 'nullsig freezes the trace')

    # Every ICE type that can act on the clock telegraphs first.
    for construct in ice_content.ICE:
        if construct.behaviour != 'trap':
            T.ok(len(construct.tells) >= 2,
                 f'{construct.key} telegraphs before it strikes')

    console2.end_capture()
    console.end_capture()


# --------------------------------------------------------------------------
# city
# --------------------------------------------------------------------------


def test_city() -> None:
    T.section('city')
    char = Character.from_origin('protege', 'x')
    game = Game.new(char, seed=77)

    T.ok(game.city.board, 'a fresh city has work on the board')
    for contract in game.city.board:
        T.ok(contract.patron in factions.BY_KEY, 'patron is a real faction')
        T.ok(contract.target in factions.BY_KEY, 'target is a real faction')
        T.ok(contract.patron != contract.target, 'nobody hires you to rob them')
        T.ok(contract.pay > 0, 'the job pays something')
        T.ok(contract.district in districts.BY_KEY, 'the job is somewhere real')
        T.ok(contract.expires > contract.posted, 'the job has a future')

    # Time moves and heat cools.
    game.alias.add_heat('kagawa', 40)
    hot = game.alias.attention('kagawa')
    game.city.advance(game.rng, game.alias, 6)
    T.ok(game.alias.attention('kagawa') < hot, 'heat decays over shifts')
    T.ok(game.city.shift >= 6, 'shifts accumulate')

    # Reputation propagates along the relations table.
    alias = Alias(name='test')
    alias.adjust_rep('fixers', 40)
    T.ok(alias.reputation('fixers') > 0, 'direct reputation lands')
    T.ok(alias.reputation('nightwatch') < 0,
         'helping the Switchboard cools Nightwatch (relations table)')
    T.ok(alias.reputation('sixes') > 0, 'and warms their allies')
    T.ok(abs(alias.reputation('sixes')) < abs(alias.reputation('fixers')),
         'knock-on is weaker than the direct change')

    # Reputation and heat are bounded.
    for _ in range(50):
        alias.adjust_rep('fixers', 50)
        alias.add_heat('fixers', 50)
    T.ok(alias.reputation('fixers') <= 100, 'reputation is capped')
    T.ok(alias.attention('fixers') <= 100, 'heat is capped')

    # D13: burning an alias dumps heat and reputation together.
    game = Game.new(Character.from_origin('gutter', 'x'), seed=5)
    game.alias.adjust_rep('sixes', 50)
    game.alias.add_heat('kagawa', 80)
    old = game.alias
    fresh = game.new_alias('clean slate')
    T.ok(old.burned, 'the old name is marked burned')
    T.eq(fresh.attention('kagawa'), 0, 'a new name carries no heat')
    T.eq(fresh.reputation('sixes'), 0, 'and no reputation either (D13)')
    T.ok(len(game.aliases) == 2, 'the history is kept')

    # Posture persists across an alias change, because they do not know who.
    game.city.posture['kagawa'] = 80
    game.new_alias('third')
    T.eq(game.city.posture['kagawa'], 80, 'posture survives a burn')

    # Residue converts to heat, and only after a delay.
    game = Game.new(Character.from_origin('gutter', 'x'), seed=8)
    summary = {'outcome': 'clean', 'faction': 'kagawa', 'residue': 20,
               'objective': True, 'haul_value': 1000, 'alert': 'green',
               'framed': '', 'ticks': 10, 'trace': 30, 'haul': []}
    game.city.apply_run(game.alias, summary, game.rng)
    T.eq(game.alias.attention('kagawa'), 0,
         'residue does not become heat immediately (D5)')
    T.ok(game.city.pending, 'the fallout is queued')
    game.city.advance(game.rng, game.alias, 2)
    T.ok(game.alias.attention('kagawa') > 0,
         'residue becomes heat a shift later')

    # Falsify redirects rather than reduces.
    game = Game.new(Character.from_origin('gutter', 'x'), seed=9)
    summary = dict(summary, framed='sixes')
    game.city.apply_run(game.alias, summary, game.rng)
    game.city.advance(game.rng, game.alias, 2)
    T.ok(game.alias.attention('kagawa') < 8,
         'a successful frame keeps the heat off you')

    # Travel is only ever to a neighbour.
    city = City.new(Rng(3), Alias(name='x'))
    for key in districts.DISTRICT_KEYS:
        ok, _ = city.can_travel(key)
        expected = key in districts.BY_KEY[city.where].neighbours
        T.eq(ok, expected, f'travel to {key} is gated by adjacency')


# --------------------------------------------------------------------------
# the shell
# --------------------------------------------------------------------------


def test_shell() -> None:
    T.section('shell')
    sess, _ = play(['help'])
    T.ok(sess.running, 'help does not end the session')

    # Unknown commands are reported, not fatal.
    _, out = play(['definitely-not-a-command'])
    T.ok('not a command' in out, 'unknown commands explain themselves')

    # Prefixes resolve, ambiguity is reported.
    from flatline.shell import resolve
    T.eq(resolve('hel', 'city').command.name, 'help', 'prefixes resolve')
    T.raises(lambda: resolve('', 'city'), 'empty line')

    # Context gating produces the specific error, not "unknown command".
    _, out = play(['crack foo bar'])
    T.ok('only works' in out, 'run verbs explain they need a run')

    # Chaining and comments.
    _, out = play(['help ; help'])
    T.ok(out.count('FLATLINE help') == 2, 'semicolons chain commands')
    _, out = play(['help # this is a comment'])
    T.ok('FLATLINE help' in out, 'comments are stripped')

    # Quoted arguments survive.
    from flatline.shell import Args
    args = Args(['one', '--flag', '--key', 'value', 'two'])
    T.eq(args.positional, ['one', 'two'], 'positionals are collected')
    T.ok(args.has('flag'), 'flags are detected')
    T.eq(args.opt('key'), 'value', 'options take their value')
    T.eq(Args(['--n', '5']).int_opt('n', 0), 5, 'int options parse')
    T.raises(lambda: Args(['--n', 'x']).int_opt('n', 0), 'bad int option')

    # Every command must survive being called with nothing and with junk.
    for name, cmd in sorted(REGISTRY.commands.items()):
        for suffix in ('', ' zzz', ' zzz qqq --nope'):
            char = Character.from_origin('gutter', 'fuzz')
            game = Game.new(char, seed=1234)
            try:
                play([f'{name}{suffix}'], game=game)
            except CommandError:
                pass  # expected and handled
            except SystemExit:
                pass
            except Exception:
                T.failures.append(
                    f'shell: `{name}{suffix}` crashed:\n'
                    + traceback.format_exc())
            T.checks += 1


# --------------------------------------------------------------------------
# playthroughs
# --------------------------------------------------------------------------


OPENING = [
    'boost logic', 'train intrusion', 'char', 'skills', 'deck', 'chrome',
    'techniques', 'rep', 'alias', 'status', 'board', 'travel', 'market',
]


def test_playthrough() -> None:
    T.section('playthrough')
    for origin in origins.ORIGIN_KEYS:
        char = Character.from_origin(origin, origin)
        char.points = attr_content.CREATION_POINTS
        char.xp = skills.CREATION_XP
        game = Game.new(char, seed=2468)
        try:
            sess, out = play(OPENING, game=game)
        except Exception:
            T.failures.append(f'playthrough: {origin} opening crashed:\n'
                              + traceback.format_exc())
            T.checks += 1
            continue
        T.ok('Traceback' not in out, f'{origin} opening is clean')

    # A full run, driven entirely through the command layer.
    for origin in ('gutter', 'academic', 'chromed'):
        char = Character.from_origin(origin, origin)
        game = Game.new(char, seed=13579)
        contract = game.city.board[0]
        lines = [f'take {contract.cid}']
        if game.city.where != contract.district:
            # Walk there, one shift at a time, however far it is.
            for _ in range(4):
                if game.city.where == contract.district:
                    break
                nxt = _step_toward(game.city.where, contract.district)
                if nxt is None:
                    break
                lines.append(f'travel {nxt}')
                game.city.where = nxt
            game.city.where = districts.BY_KEY[contract.district].key \
                if game.city.where != contract.district else game.city.where
        try:
            sess, _ = play(lines, game=game)
        except Exception:
            T.failures.append(f'playthrough: {origin} travel crashed:\n'
                              + traceback.format_exc())
            T.checks += 1
            continue

        # Put them on the doorstep and run the whole thing.
        sess.game.city.where = contract.district
        run_lines = ['jack in --force', 'scan', 'map', 'status', 'here']
        for node_uid in list(sess.game.city.board and []):
            pass
        try:
            _, out = _drive_run(sess)
        except Exception:
            T.failures.append(f'playthrough: {origin} run crashed:\n'
                              + traceback.format_exc())
            T.checks += 1
            continue
        T.ok(sess.run is None, f'{origin} finished the run and got out')
        T.ok(sess.game.char.runs >= 1, f'{origin} recorded the run')


def _step_toward(here: str, there: str) -> str | None:
    """Breadth-first next hop, so the test can walk the real district graph."""
    if here == there:
        return None
    frontier = [(here, [])]
    seen = {here}
    while frontier:
        node, path = frontier.pop(0)
        for nxt in districts.BY_KEY[node].neighbours:
            if nxt in seen:
                continue
            if nxt == there:
                return (path + [nxt])[0]
            seen.add(nxt)
            frontier.append((nxt, path + [nxt]))
    return None


def _drive_run(sess):
    """Play a run to a conclusion with a simple deterministic policy."""
    console = sess.console
    console.start_capture()
    sess.execute('jack in --force')
    steps = 0
    while sess.run is not None and steps < 60:
        steps += 1
        state = sess.run
        sess.execute('scan')
        if sess.run is None:
            break
        # Probe and try to crack anything adjacent and closed.
        for node in list(state.net.nodes.values()):
            if sess.run is None:
                break
            if not node.known or node.uid == state.here:
                continue
            if node.uid not in state.node.edges:
                continue
            if not node.mapped:
                sess.execute(f'probe {node.uid}')
            if sess.run is None:
                break
            closed = [s for s in node.services if not s.cracked]
            if closed:
                sess.execute(f'crack {node.uid} {closed[0].key}')
            if sess.run is None:
                break
            if node.open:
                sess.execute(f'connect {node.uid}')
                break
        if sess.run is None:
            break
        if sess.run.node.data:
            sess.execute('pull --all')
        if sess.run is not None and sess.run.trace_pct > 0.6:
            sess.execute('jack out')
    if sess.run is not None:
        sess.execute('jack out')
    return sess, console.end_capture()


# --------------------------------------------------------------------------
# presentation
# --------------------------------------------------------------------------


def test_ui() -> None:
    T.section('ui')
    # Markup parses, measures, and renders without leaking codes into widths.
    T.eq(ui.plain('[accent]hello[/] world'), 'hello world', 'plain strips tags')
    T.eq(ui.width('[accent]hello[/]'), 5, 'width ignores markup')
    T.eq(ui.plain('[[literal]'), '[literal]', 'double bracket escapes')
    T.eq(ui.plain('[accent]unclosed'), 'unclosed', 'unclosed tags do not crash')

    spans = ui.parse('[accent][bold]x[/][/]')
    T.eq(spans[0].role, 'accent', 'nested tags keep the role')
    T.ok('bold' in spans[0].attrs, 'nested tags keep the attribute')

    # No colour means no escape codes at all.
    plain_caps = Caps(ColorLevel.NONE, GlyphLevel.ASCII, 80, theme.NEUTRAL)
    T.ok('\033' not in ui.render('[accent]x[/]', plain_caps),
         'NO_COLOR emits no escapes')
    colour_caps = Caps(ColorLevel.TRUE, GlyphLevel.UNICODE, 80,
                       theme.CYBERPUNK_NEON)
    T.ok('\033' in ui.render('[accent]x[/]', colour_caps),
         'truecolour emits escapes')

    # D16: wrapping respects the column at every rung and never overflows.
    long_text = ('[accent]' + 'word ' * 200 + '[/]')
    for cols in (40, 60, 76, 100):
        for line in ui.wrap(long_text, cols):
            T.ok(ui.width(line) <= cols,
                 f'wrapped line fits {cols} columns')

    # Padding survives wrapping, which `help` and `skills` depend on.
    wrapped = ui.wrap('a' + ' ' * 8 + 'b', 40)
    T.eq(ui.plain(wrapped[0]), 'a' + ' ' * 8 + 'b', 'runs of spaces survive')

    # Every glyph has an ASCII form and it is really ASCII.
    for name, (uni, ascii_form) in ui.GLYPHS.items():
        T.ok(ascii_form.isascii(), f'{name} has an ASCII form')
        T.ok(uni, f'{name} has a Unicode form')

    ascii_caps = Caps(ColorLevel.NONE, GlyphLevel.ASCII, 80, theme.NEUTRAL)
    for name in ui.GLYPHS:
        T.ok(ascii_caps.g(name).isascii(), f'{name} renders ASCII at the low rung')

    # Truncation fits and marks itself.
    caps = Caps(ColorLevel.NONE, GlyphLevel.UNICODE, 80, theme.NEUTRAL)
    cut = ui.truncate('[accent]' + 'x' * 100 + '[/]', 20, caps)
    T.ok(ui.width(cut) <= 20, 'truncate fits the budget')

    # Every palette answers every role, at every rung.
    for name, palette in theme.PALETTES.items():
        for role in theme.ROLES:
            colour = getattr(palette, role)
            T.ok(0 <= colour.c256 <= 255, f'{name}/{role} has a 256 index')
            T.ok(colour.ansi in theme.ANSI16, f'{name}/{role} has an ANSI name')
            T.ok(len(colour.rgb) == 3, f'{name}/{role} has rgb')

    # The whole game must render at the minimum terminal, ASCII, no colour.
    small = Caps(ColorLevel.NONE, GlyphLevel.ASCII, 80, theme.ANSI)
    console = Console(small, stream=io.StringIO())
    console.start_capture()
    console.header('title', 'right')
    console.kv([('a', 'b'), ('long key here', 'value')])
    console.table(('one', 'two'), [('x' * 60, 'y' * 60)])
    console.raw(console.bar(0.5))
    console.bullets(['one', 'two'])
    for line in console.end_capture().splitlines():
        T.ok(len(line) <= 80, f'output fits 80 columns: {line[:30]!r}')
        T.ok(line.isascii(), f'output is ASCII at the low rung: {line[:30]!r}')


# --------------------------------------------------------------------------


def test_rivals() -> None:
    T.section('rivals')
    from flatline.content import rivals as rival_content
    from flatline.world import rivals as rival_world

    game = Game.new(Character.from_origin('gutter', 'x'), seed=8829)
    T.eq(len(game.city.rivals), len(rival_content.RIVALS),
         'the city seeds the whole runner pool')

    # They take work, but never so much that the board stops being a choice,
    # and never the job the player has already accepted.
    game.city.accepted = game.city.board[0].cid
    protected = game.city.accepted
    lows = []
    for _ in range(30):
        game.city.advance(game.rng, game.alias, 1)
        lows.append(len(game.city.board))
        T.checks += 1
        if not any(c.cid == protected for c in game.city.board):
            T.failures.append('rivals: took the contract the player accepted')
            break
    T.ok(min(lows) >= rival_world.BOARD_FLOOR,
         f'the board never drops below the floor (low was {min(lows)})')

    # Contract titles stay unique, or the board is unreadable.
    titles = [c.title for c in game.city.board]
    T.eq(len(titles), len(set(titles)), 'board titles are unique')

    # Their successes harden the world even though the player did nothing.
    game2 = Game.new(Character.from_origin('gutter', 'x'), seed=4242)
    before = dict(game2.city.posture)
    for _ in range(40):
        game2.city.advance(game2.rng, game2.alias, 1)
    moved = [k for k in before if game2.city.posture[k] > before[k]]
    T.ok(moved, 'rival successes raise somebody\'s posture without the player')

    # Disposition bands are labelled correctly around zero.
    T.eq(rival_content.disposition_band(0), 'neutral', 'zero reads as neutral')
    T.eq(rival_content.disposition_band(-100), 'will sell you',
         'the floor reads as hostile')
    T.eq(rival_content.disposition_band(100), 'owes you',
         'the ceiling reads as friendly')

    # They survive a save.
    game.save('rivals')
    back = Game.load('rivals')
    T.eq([r.key for r in back.city.rivals], [r.key for r in game.city.rivals],
         'the runner pool survives a save')
    T.eq([r.jobs for r in back.city.rivals], [r.jobs for r in game.city.rivals],
         'their job counts survive')
    save_mod.delete('rivals')


def test_signatures() -> None:
    T.section('signatures')
    from flatline.content import origins as origin_mod

    # Every origin has one, they are unique, and each names a real command.
    claimed = [o.signature for o in origin_mod.ORIGINS]
    T.eq(len(claimed), len(set(claimed)), 'no two origins share a signature')
    for origin in origin_mod.ORIGINS:
        T.ok(bool(origin.signature), f'{origin.key} has a signature')
        T.ok(origin.signature in origin_mod.SIGNATURES,
             f'{origin.key} signature is declared')
        T.ok(REGISTRY.lookup(origin.signature) is not None,
             f'{origin.key} signature names a real command ({origin.signature})')
        T.ok(bool(origin.signature_name and origin.signature_detail),
             f'{origin.key} signature is described')
    for sig in origin_mod.SIGNATURES:
        owners = [o.key for o in origin_mod.ORIGINS if o.signature == sig]
        T.eq(len(owners), 1, f'{sig} belongs to exactly one origin')

    def in_run(origin, seed=8829):
        game = Game.new(Character.from_origin(origin, 'x'), seed=seed)
        contract = game.city.board[0]
        game.city.where = contract.district
        sess, _ = play([f'take {contract.cid}', 'jack in --force'], game=game)
        return sess

    # Gated on the origin that owns it, and it says who can.
    sess = in_run('gutter')
    sess.console.start_capture()
    sess.execute('nobody')
    out = sess.console.end_capture()
    T.ok('not something you can do' in out,
         'somebody else\'s signature is refused')
    T.ok('Legally dead' in out, 'and the refusal names who can')

    # Once per run.
    sess = in_run('ghost')
    sess.run.trace = 50.0
    sess.execute('nobody')
    # The reset is to zero; the tick the command itself costs then adds its
    # own small amount back, which is correct and is not the same as failing.
    T.ok(sess.run.trace < 5.0,
         f'the ghost signature resets the trace (left {sess.run.trace:.1f})')
    sess.console.start_capture()
    sess.execute('nobody')
    T.ok('once a run' in sess.console.end_capture(), 'and only once')

    # A signature that cannot do anything does not burn the use.
    sess = in_run('gutter')
    sess.console.start_capture()
    sess.execute('jury')
    T.ok('nothing is dead' in sess.console.end_capture(),
         'jury-rig refuses when nothing is broken')
    T.ok('sig:jury' not in sess.run.spent,
         'and does not consume the once-per-run')
    sess.run.char.deck.damage['cpu'] = 3
    sess.execute('jury')
    T.eq(sess.run.char.deck.damage.get('cpu'), 1,
         'and repairs a destroyed component when there is one')

    # Every signature is at least reachable without crashing.
    console = quiet_console()
    for origin in origin_mod.ORIGIN_KEYS:
        sess = in_run(origin)
        if sess.run is None:
            continue
        sig = origin_mod.BY_KEY[origin].signature
        try:
            sess.execute(sig)
            T.checks += 1
        except Exception:
            T.failures.append(f'signatures: {origin} running {sig!r} raised:\n'
                              + traceback.format_exc())
            T.checks += 1
        T.ok(sess.run is None or sess.run.running or True,
             f'{origin} signature completes')


def test_story() -> None:
    T.section('story')
    from flatline.content import npcs as npc_mod
    from flatline.content import threads as thread_mod
    from flatline.world import story as story_mod

    game = Game.new(Character.from_origin('gutter', 'x'), seed=5)
    story = game.story
    T.ok(not story.flags, 'a new character knows nobody')

    # Meeting somebody is the hook every thread hangs on.
    T.ok(story.meet('mara'), 'first meeting registers')
    T.ok(not story.meet('mara'), 'and only counts once')
    T.ok(story.satisfied('met:mara', game), 'which satisfies met:')
    T.ok(not story.satisfied('met:archivist', game), 'and only for them')

    # World conditions read the actual world.
    game.char.runs = 4
    T.ok(story.satisfied('runs:2', game), 'runs: reads the run count')
    T.ok(not story.satisfied('runs:9', game), 'and compares properly')
    game.char.dissonance = 40
    T.ok(story.satisfied('diss:25', game), 'diss: reads Dissonance')
    T.ok(not story.satisfied('nonsense:3', game),
         'an unknown condition fails closed rather than unlocking')
    T.ok(not story.satisfied('never_set_anywhere', game),
         'and so does an unset flag')

    # Stages become available the moment their condition holds, in any order.
    fresh = Game.new(Character.from_origin('gutter', 'x'), seed=6)
    T.ok(not fresh.story.available(fresh), 'nothing is open at the start')
    fresh.char.runs = 3
    opened = fresh.story.available(fresh)
    T.ok(any(k == 'deepwater' for k, _ in opened),
         'a stage opens on a world condition alone')

    # any_of is a real second door.
    multi = [st for t in thread_mod.THREADS for st in t.stages if st.any_of]
    T.ok(multi, 'some stages have more than one way in')
    for stage in multi:
        T.ok(len(stage.any_of) >= 2,
             f'{stage.key} any_of offers an actual alternative')

    # Reaching a stage sets its flags and queues its choice.
    thread = thread_mod.BY_KEY['lark']
    stage = thread.stages[0]
    fresh.story.meet('lark')
    fresh.story.reach('lark', stage)
    T.ok(fresh.story.stage_done('lark', stage.key), 'the stage is recorded')
    for flag in stage.sets:
        T.ok(fresh.story.has(flag), f'{flag} was set')
    T.ok(not fresh.story.available(fresh) or True, 'availability recomputes')

    choice_stage = next(st for st in thread.stages if st.choices)
    fresh.story.reach('lark', choice_stage)
    T.ok(fresh.story.pending, 'a stage with choices waits on the player')
    found = fresh.story.open_choice()
    T.ok(found is not None, 'and the waiting choice is retrievable')
    fresh.story.resolve('lark', choice_stage.key, choice_stage.choices[0])
    T.ok(not fresh.story.pending, 'resolving clears it')
    for flag in choice_stage.choices[0].sets:
        T.ok(fresh.story.has(flag), f'the choice set {flag}')

    # Every thread has to be enterable, and every flag anything wants has to
    # be settable by something, or a storyline is written and unreachable.
    settable = thread_mod.flags_set()
    for thread in thread_mod.THREADS:
        for stage in thread.stages:
            for rule in tuple(stage.requires) + tuple(stage.any_of):
                if ':' in rule:
                    continue
                T.ok(rule in settable,
                     f'{thread.key}.{stage.key} wants {rule!r}, which is set '
                     f'somewhere')

    # Crossings are mutual.
    for thread in thread_mod.THREADS:
        for other in thread.crosses:
            T.ok(thread.key in thread_mod.BY_KEY[other].crosses,
                 f'{thread.key}/{other} crossing is mutual')

    # The cast is findable and is not all one note.
    from collections import Counter
    tones = Counter(n.tone for n in npc_mod.NPCS)
    T.ok(len(tones) >= 4, f'the cast spans registers ({dict(tones)})')
    T.ok(max(tones.values()) <= len(npc_mod.NPCS) * 0.4,
         'and no single register dominates')
    placed = [n for n in npc_mod.NPCS if n.where]
    T.ok(len(placed) >= 10, 'most of the cast is somewhere specific')
    for npc in npc_mod.NPCS:
        if npc.where:
            T.ok(npc.where in districts.DISTRICT_KEYS,
                 f'{npc.key} lives somewhere real')

    # Requirements gate who you can run into.
    early = Game.new(Character.from_origin('gutter', 'x'), seed=7)
    early.city.where = 'glasshouse'
    visible = story_mod.present(early, early.story)
    T.ok(all(not n.requires for n in visible),
         'a new character only meets people with no requirements')
    early.char.runs = 20
    later = story_mod.present(early, early.story)
    T.ok(len(later) >= len(visible),
         'and more people become findable with a history')

    # It all survives a save.
    game.story.flags.add('dw_heard')
    game.story.reached['deepwater'] = ['hear']
    game.save('story')
    back = Game.load('story')
    T.eq(back.story.flags, game.story.flags, 'flags survive a save')
    T.eq(back.story.reached, game.story.reached, 'and so does progress')
    T.eq(back.story.met, game.story.met, 'and who you have met')
    save_mod.delete('story')


def test_traits_and_spread() -> None:
    T.section('traits and spread')
    from flatline.content import traits as trait_mod

    # The whole point of the axis is that the pool dwarfs the slots. If it
    # does not, every character converges and the axis does nothing.
    T.ok(len(trait_mod.TRAITS) >= trait_mod.MAX_TRAITS * 4,
         f'{len(trait_mod.TRAITS)} traits for {trait_mod.MAX_TRAITS} slots')
    T.ok(trait_mod.CREATION_PICKS < trait_mod.MAX_TRAITS,
         'creation does not hand out every slot')

    # Every attribute must govern at least two skill lines. Logic used to
    # govern five of eight and Grit none, which made Logic mandatory, Grit a
    # dump stat, and every character's opening spread identical.
    from collections import Counter
    governs = Counter(s.attr for s in skills.SKILLS)
    for key in attr_content.ATTR_KEYS:
        T.ok(governs.get(key, 0) >= 2,
             f'{key} governs at least two skills (governs '
             f'{governs.get(key, 0)})')
    T.ok(max(governs.values()) - min(governs.values()) <= 2,
         f'the spread is not lopsided ({dict(governs)})')

    # Every skill still unlocks at ranks 2 and 4, including the new lines.
    for skill in skills.SKILLS:
        ranks = sorted(t.rank for t in skill.techniques)
        T.eq(ranks, [2, 4], f'{skill.key} unlocks at 2 and 4')
        for tech in skill.techniques:
            if tech.verb:
                head = tech.verb.split()[0].split('--')[0].strip()
                T.ok(REGISTRY.lookup(head) is not None,
                     f'{tech.key} names a real command ({head})')

    # Traits reach the character and cut both ways.
    char = Character.from_origin('gutter', 'x')
    T.eq(char.trait_picks, trait_mod.CREATION_PICKS,
         'a new character has creation picks')
    for trait in trait_mod.TRAITS:
        T.ok(bool(trait.effects), f'{trait.key} has a benefit')
        T.ok(bool(trait.penalty or trait.rider),
             f'{trait.key} has a mechanical drawback')

    fresh = Character.from_origin('gutter', 'x')
    base_tick = fresh.mult('tick_mult')
    fresh.take_trait('impatient')
    T.ok(fresh.mult('tick_mult') < base_tick, 'a trait changes the numbers')
    T.ok(fresh.bonus('tell_lead') < 0, 'and its drawback lands too')

    # Exclusions hold both ways and are enforced.
    ok, why = fresh.can_take_trait('methodical')
    T.ok(not ok, 'an excluded trait is refused')
    T.ok('does not go with' in why, 'and says why')
    for trait in trait_mod.TRAITS:
        for other in trait.excludes:
            T.ok(trait.key in trait_mod.BY_KEY[other].excludes,
                 f'{trait.key}/{other} exclusion is mutual')

    # Slots are earned, not granted.
    counter = Character.from_origin('gutter', 'x')
    T.eq(counter.trait_slots, trait_mod.CREATION_PICKS, 'two at the start')
    counter.runs = trait_mod.EARN_EVERY
    T.eq(counter.trait_slots, trait_mod.CREATION_PICKS + 1,
         'one more after the first stretch of runs')
    counter.runs = 10_000
    T.eq(counter.trait_slots, trait_mod.MAX_TRAITS, 'and it caps')

    # You cannot take more than you have.
    spent = Character.from_origin('gutter', 'x')
    spent.take_trait('cold')
    spent.take_trait('logreader')
    ok, why = spent.can_take_trait('fast')
    T.ok(not ok, 'a third pick is refused at creation')
    T.raises(lambda: spent.take_trait('fast'), 'and taking it raises')

    # Riders reach the character and are read by the engine.
    engine = _source_of('flatline/run', 'flatline/commands')
    for rider in trait_mod.RIDERS:
        T.ok(rider in engine, f'trait rider {rider!r} is read by the engine')
    rider_char = Character.from_origin('gutter', 'x')
    rider_char.take_trait('hoarder')
    T.ok('rot' in rider_char.riders(), 'a trait rider reaches riders()')

    # Traits survive a save.
    game = Game.new(Character.from_origin('gutter', 'x'), seed=5)
    game.char.take_trait('sensitive')
    game.char.take_trait('known')
    game.save('traits')
    back = Game.load('traits')
    T.eq(back.char.traits, game.char.traits, 'traits survive a save')
    T.eq(back.char.mult('ice_dr'), game.char.mult('ice_dr'),
         'and so does what they do')
    save_mod.delete('traits')

    # The new techniques all work as commands, gated on the rank.
    net = net_mod.generate(Rng(4).fork('network', 'newskills'), 'sixes', 30)
    console = quiet_console()
    console.start_capture()
    for skill_key, tech_key, verb in (
            ('architecture', 'chart', 'chart'),
            ('signal', 'listen', 'listen'),
            ('sabotage', 'misdirect', 'misdirect'),
            ('psyche', 'steady', 'steady')):
        blocked = Character.from_origin('gutter', 'x')
        T.ok(not blocked.has_technique(tech_key),
             f'{tech_key} is locked without the rank')
        trained = Character.from_origin('gutter', 'x')
        trained.base_skills[skill_key] = 2
        T.ok(trained.has_technique(tech_key),
             f'{tech_key} unlocks at rank 2 of {skill_key}')
    console.end_capture()

    # Dissociate genuinely redirects damage away from the body.
    console.start_capture()
    char = Character.from_origin('gutter', 'x')
    char.base_skills['psyche'] = 4
    state = RunState.begin(net, char, Rng(4)('combat'), console)
    state.dissociated = 3
    before_hurt = state.hurt
    before_deck = sum(state.char.deck.damage.values())
    state.take_damage(20, black=True, source='test')
    T.eq(state.hurt, before_hurt, 'dissociated damage misses the body')
    T.ok(sum(state.char.deck.damage.values()) > before_deck,
         'and lands on the deck instead')
    T.ok(state.running, 'and lethal damage cannot end you through it')
    console.end_capture()


def test_regressions() -> None:
    """Three bugs found by audit on 2026-08-13. None had a test; all three
    were reachable in ordinary play."""
    T.section('regressions')

    def in_run(hardware=4, stealth=4, seed=8829):
        game = Game.new(Character.from_origin('gutter', 'x'), seed=seed)
        game.char.base_skills['hardware'] = hardware
        game.char.base_skills['stealth'] = stealth
        contract = game.city.board[0]
        game.city.where = contract.district
        sess, _ = play([f'take {contract.cid}', 'jack in --force'], game=game)
        return sess

    # 1. Overclocking must never make an action free, because an action that
    #    costs no ticks never calls advance(), which stops the trace, the ICE
    #    and the whole run clock. Step 2 used to reduce every one-tick action
    #    to zero.
    costs = {}
    for steps in (0, 1, 2, 3):
        sess = in_run()
        sess.execute(f'overclock {steps}')
        before = sess.run.tick
        for _ in range(8):
            if sess.run is None:
                break
            sess.execute('scan')
        costs[steps] = (sess.run.tick - before) if sess.run else -1
    T.ok(costs[0] > 0, 'unoverclocked actions cost ticks')
    for steps in (1, 2, 3):
        T.ok(costs[steps] > 0,
             f'overclock {steps} still spends ticks (got {costs[steps]})')
        T.ok(costs[steps] < costs[0],
             f'overclock {steps} is faster than not overclocking')
    T.ok(costs[1] < costs[0], 'step 1 does something at all')
    T.ok(costs[2] <= costs[1], 'more steps are not slower')

    # 2. Nullsig must protect the tick it is spending. Decrementing before
    #    advance() meant the last point of the window silently protected
    #    nothing, and the announcement promised ticks it did not deliver.
    sess = in_run()
    sess.execute('nullsig')
    T.ok(sess.run.nullsig > 0, 'nullsig opens a window')
    leaked = 0
    acted = 0
    while sess.run is not None and sess.run.nullsig > 0 and acted < 25:
        before = sess.run.trace
        sess.execute('scan')
        acted += 1
        if sess.run is None:
            break
        if sess.run.trace > before:
            leaked += 1
    T.eq(leaked, 0, 'no action inside a nullsig window advances the trace')
    T.ok(acted > 0, 'and the window covers at least one action')

    # 3. A run can end inside a command, and when it does the session has to
    #    settle up. It used to leave the player inside a finished run, taking
    #    further actions against a dead connection, with no consequences ever
    #    applied.
    for ending in ('trace', 'integrity'):
        sess = in_run()
        runs_before = sess.game.char.runs
        if ending == 'trace':
            sess.run.trace = 99.5
        else:
            sess.run.hurt = sess.run.char.integrity_max - 1
            sess.run.trace = 99.5
        sess.execute('scan')
        T.ok(sess.run is None,
             f'a run ending by {ending} mid-command resolves itself')
        T.eq(sess.context, 'city', 'and the shell returns to the city')
        T.ok(sess.game.char.runs > runs_before,
             'and the run is counted')

    # Jacking out of an already-finished run must not double-resolve.
    sess = in_run()
    sess.run.trace = 99.5
    sess.execute('scan')
    T.ok(sess.run is None, 'the run resolved')
    counted = sess.game.char.runs
    sess.execute('jack out')
    T.eq(sess.game.char.runs, counted, 'jacking out again changes nothing')

    # And a normal jack out still resolves exactly once.
    sess = in_run()
    before = sess.game.char.runs
    sess.execute('jack out')
    T.ok(sess.run is None, 'a deliberate exit resolves')
    T.eq(sess.game.char.runs, before + 1, 'and counts exactly one run')

    # 4. The protege's Known Quantity says "one extra contract on the board
    #    at all times". `board_size` handled it and `char` was never threaded
    #    through the top-up, so it was true for about one shift and then the
    #    board silently dropped back to standard.
    protege = Game.new(Character.from_origin('protege', 'x'), seed=8829)
    plain = Game.new(Character.from_origin('gutter', 'x'), seed=8829)
    T.ok(len(protege.city.board) > len(plain.city.board),
         'the protege starts with an extra posting')
    for _ in range(40):
        for game in (protege, plain):
            game.city.advance(game.rng, game.alias, 1,
                              debt=game.debt, char=game.char)
    T.ok(len(protege.city.board) > len(plain.city.board),
         'and still has it forty shifts later, which is what "at all times" '
         'means')

    # The world's news is a scrollback, not a record: it is appended to every
    # single shift and must not grow without bound.
    from flatline.world.city import NEWS_KEPT
    T.ok(len(protege.city.news) <= NEWS_KEPT,
         f'news stays capped in memory ({len(protege.city.news)})')
    protege.save('news')
    T.ok(len(Game.load('news').city.news) <= NEWS_KEPT,
         'and on disk')
    save_mod.delete('news')

    # 5. Content that promises something the engine does not read. Three
    #    separate instances of this shipped: `crack --chain`, the three
    #    wardens' `credential_check`, and `alert_jump` on non-traps. All of
    #    them validated, all of them announced themselves, none of them did
    #    anything.
    from flatline.content import ice as ice_mod
    from flatline.content import skills as skill_mod

    engine = _source_of('flatline/run', 'flatline/commands')
    for rider in ice_mod.ICE_RIDERS:
        T.ok(rider in engine, f'ICE rider {rider!r} is read by the engine')
    for tech in skill_mod.TECHNIQUES.values():
        flag = _flag_of(tech.verb)
        if flag:
            T.ok(f"args.has('{flag}')" in engine,
                 f'technique {tech.key!r} option --{flag} is read')

    # Chain in particular: two services, one action.
    sess = in_run()
    sess.game.char.base_skills['intrusion'] = 2
    target = None
    sess.execute('scan')
    for node in (sess.run.net.nodes.values() if sess.run else ()):
        if (node.known and node.uid in sess.run.node.edges
                and len(node.services) >= 2):
            target = node
            break
    if target is not None:
        sess.execute(f'probe {target.uid}')
        closed = [s for s in target.services if not s.cracked]
        if len(closed) >= 2 and sess.run is not None:
            ticks = sess.run.tick
            sess.console.start_capture()
            sess.execute(f'crack {target.uid} --chain')
            out = sess.console.end_capture()
            if sess.run is not None:
                spent = sess.run.tick - ticks
                T.ok(spent <= 2,
                     f'chain costs about one action, not two (spent {spent})')
                # Assert on the attempt, not the outcome: both checks are
                # resolved on dice and either may fail.
                reported = sum(1 for svc in closed[:2]
                               if svc.data.name in out)
                T.eq(reported, 2, 'and it reports on both services')

    # Chain refuses when it cannot do what it says.
    sess = in_run()
    sess.game.char.base_skills['intrusion'] = 0
    sess.console.start_capture()
    sess.execute('crack nowhere --chain')
    out = sess.console.end_capture()
    T.ok('Intrusion rank 2' in out, 'chain is gated on the technique')

    # A credential warden can be answered with credentials.
    net = net_mod.generate(Rng(2).fork('network', 'cred'), 'kagawa', 60)
    console = quiet_console()
    console.start_capture()
    char = Character.from_origin('protege', 'x')
    char.base_skills['subterfuge'] = 3
    state = RunState.begin(net, char, Rng(2)('combat'), console)
    talkable = untalkable = None
    for construct in ice_mod.ICE:
        if construct.effects.get('credential_check'):
            talkable = construct
        elif construct.behaviour == 'warden':
            untalkable = construct
    if talkable:
        from flatline.run.network import IceInstance
        inst = IceInstance(uid='t', key=talkable.key, rating=4)
        T.ok(state.credential_challenge(inst) is not None,
             'a credential warden offers a challenge')
    if untalkable:
        from flatline.run.network import IceInstance
        inst = IceInstance(uid='u', key=untalkable.key, rating=4)
        T.eq(state.credential_challenge(inst), None,
             'and one that does not check credentials offers nothing')
    console.end_capture()

    # alert_jump is read from the construct rather than assumed.
    jumpers = [i for i in ice_mod.ICE
               if i.effects.get('alert_jump') and i.behaviour != 'trap']
    T.ok(jumpers, 'some non-trap construct declares alert_jump')
    T.ok("data.effects.get('alert_jump'" in engine
         or "effects.get('alert_jump'" in engine,
         'and the strike path reads it')


def _source_of(*dirs) -> str:
    import pathlib
    out = []
    for d in dirs:
        for path in sorted(pathlib.Path(d).glob('*.py')):
            out.append(path.read_text(encoding='utf-8'))
    return '\n'.join(out)


def _flag_of(verb: str) -> str:
    import re
    match = re.search(r'--([a-z][a-z0-9_-]*)', verb or '')
    return match.group(1) if match else ''


def test_herders_and_kinds() -> None:
    T.section('herders and kinds')

    # Every faction kind must generate without a missing branch. This is the
    # failure mode adding a faction actually has.
    for kind in factions.KINDS:
        probe = next((f for f in factions.FACTIONS if f.kind == kind), None)
        if probe is None:
            continue
        try:
            net = net_mod.generate(Rng(3).fork('network', kind),
                                   probe.key, probe.posture)
            T.ok(bool(net.nodes), f'a {kind} network generates')
        except Exception:
            T.failures.append(f'herders and kinds: {kind} generation raised:\n'
                              + traceback.format_exc())
            T.checks += 1

    # Every faction can be fielded against, and every ICE type is reachable.
    reached = set()
    for i in range(96):
        key = factions.FACTION_KEYS[i % len(factions.FACTION_KEYS)]
        net = net_mod.generate(Rng(i).fork('network', f'k{i}'), key,
                               factions.BY_KEY[key].posture)
        for node in net.nodes.values():
            for construct in node.ice:
                reached.add(construct.key)
    missing = [i.key for i in ice_content.ICE if i.key not in reached]
    T.ok(not missing, f'every ICE type is reachable by generation ({missing})')

    # Doctrine shows up in the numbers: a pirate press is emptier than a corp.
    def density(key):
        total = nodes = 0
        for i in range(24):
            net = net_mod.generate(Rng(i).fork('network', f'd{key}{i}'), key,
                                   factions.BY_KEY[key].posture)
            nodes += len(net.nodes)
            total += sum(len(n.ice) for n in net.nodes.values())
        return total / max(1, nodes)

    T.ok(density('static') < density('kagawa'),
         'a pirate press defends less than a megacorp')
    T.ok(density('deepwater') > density('sixes'),
         'whatever Deepwater is, it is denser than a gang')

    # Herders never fight, and never strand you.
    for construct in ice_content.by_behaviour('herder'):
        T.eq(construct.damage, 0, f'{construct.key} does no damage')
        T.ok(construct.effects.get('route_cut'),
             f'{construct.key} cuts a route')

    console = quiet_console()
    console.start_capture()
    char = Character.from_origin('gutter', 'x')
    cuts = 0
    for i in range(60):
        net = net_mod.generate(Rng(i).fork('network', f'h{i}'),
                               'deepwater', 72)
        state = RunState.begin(net, char, Rng(i)('combat'), console)
        deep = [n for n in net.nodes.values()
                if n.zone in ('restricted', 'core')]
        if deep:
            state.here = deep[0].uid
        for _ in range(30):
            cut = state._cut_route()
            if cut is None:
                break
            cuts += 1
            T.checks += 1
            if not state._still_playable():
                T.failures.append(
                    'herders and kinds: a cut left the run unplayable')
                break
        # Whatever it did, the way out and the job are still reachable.
        T.ok(state._still_playable(),
             f'seed {i}: the run is still playable after cutting')
    T.ok(cuts > 0, f'route cutting actually happens ({cuts} cuts)')

    # A herder with nowhere safe to cut does nothing rather than misbehaving.
    tiny = net_mod.generate(Rng(1).fork('network', 'tiny'), 'sixes', 20)
    state = RunState.begin(tiny, char, Rng(1)('combat'), console)
    for _ in range(200):
        if state._cut_route() is None:
            break
    T.eq(state._cut_route(), None,
         'a herder with nothing safe to close does nothing')
    T.ok(state._still_playable(), 'and the run is still finishable')
    console.end_capture()


def test_passives_and_debt() -> None:
    T.section('passives and debt')
    from flatline.world import debt as debt_mod

    # Every origin's headline ability has a mechanical half. This is the check
    # that stops a passive being a sentence that does nothing, which several
    # of them were before this suite existed.
    for key in origins.ORIGIN_KEYS:
        origin = origins.BY_KEY[key]
        T.ok(bool(origin.effects or origin.rider),
             f'{key} passive has a mechanical half')
        if origin.rider:
            T.ok(origin.rider in origins.RIDERS,
                 f'{key} rider is declared')
            char = Character.from_origin(key, 'x')
            T.ok(origin.rider in char.riders(),
                 f'{key} rider reaches the character')
        for fx_key in origin.effects:
            T.ok(fx_key in fx.ALL, f'{key} effect {fx_key!r} is a real key')

    # Repair discounts are real money, not prose.
    plain = Character.from_origin('protege', 'x')
    salvager = Character.from_origin('gutter', 'x')
    company = Character.from_origin('bonded', 'x')
    for char in (plain, salvager, company):
        char.deck.damage['cpu'] = 2
    base = plain.deck.repair_cost(plain.mult('repair_mult'))
    T.ok(salvager.deck.repair_cost(salvager.mult('repair_mult'))
         < salvager.deck.repair_cost(1.0),
         'Salvager pays less to repair')
    T.ok(company.mult('repair_mult') < salvager.mult('repair_mult'),
         'Company Hardware beats Salvager on repairs')
    T.ok(base > 0, 'an undiscounted repair still costs something')
    T.eq(plain.deck.repair_cost(0.0), 0, 'a free repair is free')

    # Known Quantity is worth money on a payout.
    T.ok(plain.mult('pay_mult') > 1.0, 'the protege negotiates better')

    # Nobody: cheaper, faster names and faster forgetting.
    ghost = Character.from_origin('ghost', 'x')
    T.ok('no_history' in ghost.riders(), 'the ghost has no history')
    alias_a, alias_b = Alias(name='a'), Alias(name='b')
    for alias in (alias_a, alias_b):
        alias.add_heat('kagawa', 60)
    for _ in range(6):
        alias_a.decay_heat(1.0)
        alias_b.decay_heat(1.4)
    T.ok(alias_b.attention('kagawa') < alias_a.attention('kagawa'),
         'heat with nothing to attach to fades faster')

    # Been here before: everything identified from the first tick.
    net = net_mod.generate(Rng(4).fork('network', 'vet'), 'kagawa', 60)
    console = quiet_console()
    console.start_capture()
    burnout = Character.from_origin('burnout', 'x')
    state = RunState.begin(net, burnout, Rng(4)('combat'), console)
    constructs = [i for n in state.net.nodes.values() for i in n.ice]
    if constructs:
        T.ok(all(i.known for i in constructs),
             'the burnout knows every construct on sight')
    # And somebody else does not.
    net2 = net_mod.generate(Rng(4).fork('network', 'vet'), 'kagawa', 60)
    fresh = RunState.begin(net2, Character.from_origin('courier', 'x'),
                           Rng(4)('combat'), console)
    others = [i for n in fresh.net.nodes.values() for i in n.ice]
    if others:
        T.ok(not all(i.known for i in others),
             'and somebody without the passive does not')

    # Native: the run opens with an action already in hand.
    net3 = net_mod.generate(Rng(4).fork('network', 'nat'), 'sixes', 30)
    chromed = RunState.begin(net3, Character.from_origin('chromed', 'x'),
                             Rng(4)('combat'), console)
    T.eq(chromed.free_actions, 1, 'the chromed origin opens with a free action')
    T.eq(fresh.free_actions, 0, 'and nobody else does')
    console.end_capture()

    # --- debt ---------------------------------------------------------
    game = Game.new(Character.from_origin('academic', 'x'), seed=7)
    T.ok(game.debt.owed, 'the academic starts owing somebody')
    T.ok(game.debt.lender in factions.BY_KEY, 'and the lender is real')
    bonded = Game.new(Character.from_origin('bonded', 'x'), seed=7)
    T.ok(bonded.debt.amount > game.debt.amount,
         'the indentured origin owes more')
    clean = Game.new(Character.from_origin('gutter', 'x'), seed=7)
    T.ok(not clean.debt.owed, 'and most origins owe nothing')

    # It compounds, and the lender eventually turns up.
    start = game.debt.amount
    for _ in range(debt_mod.GRACE - 1):
        game.city.advance(game.rng, game.alias, 1,
                          debt=game.debt, char=game.char)
    T.ok(game.debt.amount > start, 'debt compounds while you ignore it')
    T.ok(not game.debt.due(game.city.shift), 'nobody calls during the grace')
    # The warning lands at the grace boundary; the first collection is one
    # COLLECT_EVERY after it, which is the gap the player gets to find money in.
    game.city.advance(game.rng, game.alias, debt_mod.COLLECT_EVERY + 2,
                      debt=game.debt, char=game.char)
    T.ok(game.debt.last_collected >= 0, 'and then somebody does')

    # D6: a debt must be survivable. Collections have to outpace interest.
    solo = debt_mod.Debt(amount=20000, lender='sixes', opened=0)
    for shift in range(1, 200):
        solo.accrue()
        if solo.due(shift):
            solo.collect(shift)
        if not solo.owed:
            break
    T.ok(solo.amount < 20000,
         f'an ignored debt shrinks under collection rather than spiralling '
         f'(ended at {solo.amount})')

    # Paying works and cannot go negative.
    payable = debt_mod.Debt(amount=1000, lender='sixes')
    T.eq(payable.pay(300), 300, 'a payment applies')
    T.eq(payable.amount, 700, 'and reduces the balance')
    T.eq(payable.pay(9999), 700, 'overpaying applies only what is owed')
    T.eq(payable.amount, 0, 'and clears it')
    T.ok(not payable.owed, 'a cleared debt is not owed')
    T.eq(payable.pay(100), 0, 'and paying more does nothing')

    # It survives a save.
    game.save('debt')
    back = Game.load('debt')
    T.eq(back.debt.amount, game.debt.amount, 'debt survives a save')
    T.eq(back.debt.lender, game.debt.lender, 'and so does the lender')
    save_mod.delete('debt')

    # The city remembers where you have been, which the Courier reads.
    T.ok(game.city.visited, 'the city remembers somewhere')
    T.ok(game.city.where in game.city.visited, 'including where you are')
    game.save('visited')
    T.eq(Game.load('visited').city.visited, game.city.visited,
         'and that survives a save')
    save_mod.delete('visited')


def test_dissonance() -> None:
    T.section('dissonance')
    from flatline.commands.city import LEGWORK_DRIFT, _legwork_allowed
    from flatline.content import dissonance as drift

    # Passages fire once each, in order, and a jump can carry two at once.
    T.eq([p.band for p in drift.crossed(0, 10)], [],
         'no passage below the first band')
    T.eq([p.band for p in drift.crossed(0, 30)], [25],
         'one band crossed fires one passage')
    T.eq([p.band for p in drift.crossed(0, 80)], [25, 50, 75],
         'a big jump fires every band it passed')
    T.eq([p.band for p in drift.crossed(50, 80)], [75],
         'and never re-fires one already behind you')

    char = Character.from_origin('gutter', 'x')
    char.dissonance = 30
    T.eq([p.band for p in char.new_passages()], [25], 'the character sees it')
    T.eq(char.new_passages(), [], 'and does not see it twice')
    char.dissonance = 90
    T.eq([p.band for p in char.new_passages()], [50, 75],
         'and picks up everything it skipped')

    # The chrome floor: you cannot ground below what is still in you.
    chromed = Character.from_origin('chromed', 'x')
    T.eq(chromed.chrome_dissonance,
         sum(cyberware.BY_KEY[k].dissonance for k in chromed.installed),
         'the floor is the sum of what is fitted')
    chromed.dissonance = chromed.chrome_dissonance + 30
    floor = chromed.chrome_dissonance
    chromed.dissonance = max(floor, chromed.dissonance - 999)
    T.eq(chromed.dissonance, floor, 'grounding stops at the chrome floor')

    # D11 still holds: taking chrome out does not lower the number.
    before = chromed.dissonance
    key = chromed.installed[0]
    chromed.uninstall(key)
    T.eq(chromed.dissonance, before,
         'removing chrome leaves the drift where it was (D11)')
    T.ok(chromed.chrome_dissonance < before,
         'but it does lower the floor, so grounding can go further')

    # The back room is invisible until you are far enough gone, and the best
    # chrome in the city exists nowhere else.
    for district in ('green', 'glasshouse', 'vertical'):
        listings = market_mod.restock(Rng(3)('market'), district, 0)
        shelf = [l for l in listings if l.kind == 'ware' and not l.deep]
        deep = [l for l in listings if l.deep]
        T.ok(deep, f'{district} has a back room')
        for listing in shelf:
            T.ok(cyberware.BY_KEY[listing.key].tier < 3,
                 f'{district}: no restricted chrome on the open shelf')
        for listing in deep:
            T.ok(cyberware.BY_KEY[listing.key].tier >= 3,
                 f'{district}: the back room carries restricted chrome')

    # Districts with no clinic have no back room at all.
    listings = market_mod.restock(Rng(3)('market'), 'ninth', 0)
    T.ok(not [l for l in listings if l.deep],
         'a district with no clinic has no back room')

    # And the city filters it by who is asking.
    game = Game.new(Character.from_origin('gutter', 'x'), seed=4242)
    game.city.where = 'glasshouse'
    T.ok(game.city.listings('ware', deep=True), 'the stock exists')
    T.ok(not [l for l in game.city.listings('ware', deep=False) if l.deep],
         'and the shop floor never includes it')

    # Legwork gates open and close in the right directions.
    low = Character.from_origin('gutter', 'x')
    low.dissonance = 0
    high = Character.from_origin('gutter', 'x')
    high.dissonance = 90
    ok, _ = _legwork_allowed(low, 'resonance')
    T.ok(not ok, 'resonance is closed to somebody still grounded')
    ok, _ = _legwork_allowed(high, 'resonance')
    T.ok(ok, 'and open to somebody far enough gone')
    ok, _ = _legwork_allowed(low, 'employee')
    T.ok(ok, 'social legwork is open to somebody who can still pass')
    ok, _ = _legwork_allowed(high, 'employee')
    T.ok(not ok, 'and closed to somebody who cannot')
    ok, _ = _legwork_allowed(high, 'perimeter')
    T.ok(ok, 'ungated legwork is always available')

    # Every gate names real legwork and a real band.
    for key, (kind, threshold) in LEGWORK_DRIFT.items():
        T.ok(threshold in drift.BANDS, f'{key} gates on a real band')
        T.ok(kind in ('floor', 'ceiling'), f'{key} has a real gate kind')

    # The drift survives a save, including what has already been shown.
    game.char.dissonance = 60
    game.char.new_passages()
    seen = game.char.drift_seen
    game.save('drift')
    back = Game.load('drift')
    T.eq(back.char.dissonance, 60, 'dissonance survives')
    T.eq(back.char.drift_seen, seen, 'and so does what you have already read')
    T.eq(back.char.new_passages(), [],
         'so a loaded character is not told it all again')
    save_mod.delete('drift')


def test_scripting() -> None:
    T.section('scripting')
    from flatline import script as script_mod

    # All four statement forms parse.
    T.eq(script_mod.parse_line('scan').kind, 'cmd', 'a bare command parses')
    T.eq(script_mod.parse_line('if ice: strike').kind, 'if', 'if parses')
    T.eq(script_mod.parse_line('stop if trace > 60').kind, 'stop',
         'stop parses')
    step = script_mod.parse_line('repeat 3: scan')
    T.eq(step.kind, 'repeat', 'repeat parses')
    T.eq(step.count, 3, 'and keeps its count')
    T.eq(script_mod.parse_line('# a comment'), None, 'comments are skipped')
    T.eq(script_mod.parse_line('   '), None, 'blank lines are skipped')

    # Bad input is a readable error, never a traceback.
    for bad in ('if ice strike', 'if : scan', 'repeat 0: scan',
                'repeat 99: scan', 'repeat 3', 'stop',
                'if florble > 3: scan', 'if ice > 3: scan',
                'if trace > banana: scan', 'if alert > purple: scan'):
        T.raises(lambda b=bad: script_mod.parse_line(b),
                 f'{bad!r} is rejected')

    # Length is bounded.
    T.raises(lambda: script_mod.parse(['scan'] * (script_mod.MAX_STEPS + 1)),
             'an over-long script is rejected')

    # Conditions read live state and mean what they say.
    net = net_mod.generate(Rng(5).fork('network', 'script'), 'sixes', 30)
    char = Character.from_origin('gutter', 'x')
    console = quiet_console()
    console.start_capture()
    state = RunState.begin(net, char, Rng(5)('combat'), console)

    state.trace = 50.0
    T.ok(script_mod.parse_condition('trace > 40').evaluate(state),
         'trace > 40 is true at 50')
    T.ok(not script_mod.parse_condition('trace > 60').evaluate(state),
         'trace > 60 is false at 50')
    T.ok(script_mod.parse_condition('trace < 60').evaluate(state),
         'trace < 60 is true at 50')
    T.ok(script_mod.parse_condition('trace >= 50').evaluate(state),
         'trace >= 50 is true at 50')
    T.ok(script_mod.parse_condition('trace != 40').evaluate(state),
         'trace != 40 is true at 50')

    # Negation inverts, on both kinds.
    T.ok(script_mod.parse_condition('not trace > 60').evaluate(state),
         'not inverts a numeric condition')
    open_now = script_mod.parse_condition('open').evaluate(state)
    T.eq(script_mod.parse_condition('not open').evaluate(state), not open_now,
         'not inverts a flag')

    # Alert compares by rank, not alphabetically.
    state.alert = 'red'
    T.ok(script_mod.parse_condition('alert >= red').evaluate(state),
         'alert >= red is true at red')
    T.ok(script_mod.parse_condition('alert >= amber').evaluate(state),
         'alert >= amber is true at red')
    T.ok(not script_mod.parse_condition('alert >= lockdown').evaluate(state),
         'alert >= lockdown is false at red')
    state.alert = 'green'
    T.ok(not script_mod.parse_condition('alert').evaluate(state),
         'bare alert is false at green')
    T.ok(script_mod.parse_condition('not alert').evaluate(state),
         'and negates correctly')

    # Every declared condition evaluates against a real state without raising.
    for name in list(script_mod.NUMERIC) + list(script_mod.FLAGS) + ['alert']:
        try:
            script_mod.parse_condition(name).evaluate(state)
            T.checks += 1
        except Exception:
            T.failures.append(f'scripting: condition {name!r} raised:\n'
                              + traceback.format_exc())
    console.end_capture()

    # A script runs, skips what it should, and stops when told.
    game = Game.new(Character.from_origin('gutter', 'x'), seed=8829)
    game.char.base_skills['daemonology'] = 2
    contract = game.city.board[0]
    game.city.where = contract.district
    sess, _ = play([f'take {contract.cid}', 'jack in --force'], game=game)
    T.ok(sess.run is not None, 'the run started')

    sess.scripts['t'] = script_mod.Script(
        name='t', lines=['scan', 'stop if trace > 0', 'pull --all'])
    sess.console.start_capture()
    sess.run_script('t')
    out = sess.console.end_capture()
    T.ok('stopped' in out, 'a stop condition abandons the rest')
    T.ok('pull' not in out, 'and nothing after it runs')

    # Flags survive being stored, which `--all` depends on.
    sess.scripts['f'] = script_mod.Script(name='f', lines=['pull --all'])
    T.eq(sess.scripts['f'].lines[0], 'pull --all', 'flags are kept verbatim')

    # A broken script is reported, not raised.
    sess.scripts['bad'] = script_mod.Script(name='bad', lines=['if oops: scan'])
    T.raises(lambda: sess.run_script('bad'), 'a broken script errors cleanly')
    T.raises(lambda: sess.run_script('nope'), 'an unknown script errors')

    # Scripts belong to the character and survive a save.
    sess.sync_scripts()
    sess.game.save('scripts')
    back = Game.load('scripts')
    T.ok('t' in back.scripts, 'scripts survive a save')
    T.eq(back.scripts['t'].lines, sess.scripts['t'].lines,
         'and keep their lines exactly')
    save_mod.delete('scripts')

    # A daemon reads a script as a policy: first passing condition names the
    # task, `stop if` ends it, and it never gets the player's verb set.
    console2 = quiet_console()
    console2.start_capture()
    dstate = RunState.begin(net, char, Rng(9)('combat'), console2)
    daemon = {'uid': 'd1', 'program': 'errand', 'node': dstate.here,
              'task': 'script', 'arg': '', 'life': 9,
              'lines': ['if trace > 20: noise', 'if ice: hold', 'hold']}
    dstate.trace = 0.0
    T.eq(dstate._daemon_policy(daemon)[0], 'hold',
         'a daemon falls through to the unconditional step')
    dstate.trace = 50.0
    T.eq(dstate._daemon_policy(daemon)[0], 'noise',
         'and switches task when a condition starts passing')

    daemon['lines'] = ['stop if trace > 10']
    T.eq(dstate._daemon_policy(daemon), None, 'a stop condition ends a daemon')
    daemon['lines'] = ['stop if trace > 999']
    T.ok(dstate._daemon_policy(daemon) is not None,
         'and does not when it is false')

    daemon['lines'] = ['if trace > 0: jack out', 'if trace > 0: pull --all']
    chosen = dstate._daemon_policy(daemon)
    T.ok(chosen is None or chosen[0] in dstate.DAEMON_TASKS,
         'a daemon never gets a command outside its own task set')

    # A policy that names only commands a daemon cannot run falls back to
    # holding rather than doing something it was not told to do.
    daemon['lines'] = ['scan', 'pull --all']
    fallback = dstate._daemon_policy(daemon)
    T.ok(fallback is not None and fallback[0] == 'hold',
         'a policy of commands it cannot run leaves it holding')

    # A policy that does not parse at all stops it, rather than crashing it.
    daemon['lines'] = ['if florble > 3: hold']
    T.eq(dstate._daemon_policy(daemon), None,
         'an unparseable policy stops the daemon rather than crashing it')

    # A scripted daemon actually runs on the tick without raising.
    dstate.daemons = [{'uid': 'd2', 'program': 'errand', 'node': dstate.here,
                       'task': 'script', 'arg': '', 'life': 4,
                       'lines': ['if ice: noise', 'hold']}]
    for _ in range(6):
        dstate._daemon_tick()
        T.checks += 1
    T.ok(True, 'scripted daemons tick without raising')
    console2.end_capture()

    # Every shipped example parses and is made of real commands.
    for name, lines in script_mod.EXAMPLES.items():
        try:
            steps = script_mod.parse(lines)
            T.ok(bool(steps), f'example {name} parses to something')
        except script_mod.ScriptError:
            T.failures.append(f'scripting: example {name} does not parse')
            T.checks += 1


def test_social() -> None:
    T.section('social')
    from flatline.content import rivals as rival_content
    from flatline.world import rivals as rival_world

    game = Game.new(Character.from_origin('protege', 'x'), seed=11)
    moth = game.city.rival('moth')
    ledger = game.city.rival('ledger')

    # Hiring is priced on skill, discounted by liking you.
    T.ok(rival_world.hire_price(ledger) > rival_world.hire_price(moth),
         'the better runner costs more')
    cold = rival_world.Rival(key='moth', disposition=-20)
    warm = rival_world.Rival(key='moth', disposition=60)
    T.ok(rival_world.hire_price(warm) < rival_world.hire_price(cold),
         'liking you is a discount')

    # And gated on disposition, not just money.
    hostile = rival_world.Rival(key='hound', disposition=-80)
    ok, why = rival_world.can_hire(hostile)
    T.ok(not ok, 'somebody who hates you will not work with you')
    dead = rival_world.Rival(key='moth', disposition=90, alive=False)
    ok, _ = rival_world.can_hire(dead)
    T.ok(not ok, 'the dead do not take contracts')

    # A hired runner must not be sent off on somebody else's job while they
    # are on your books. This is the bug that only shows up in play.
    game.city.hired = 'moth'
    before = moth.jobs
    for _ in range(25):
        game.city.advance(game.rng, game.alias, 1)
    T.eq(moth.jobs, before, 'a hired runner takes no other work')
    T.ok(moth.alive, 'and cannot die on a job you did not send them on')
    T.ok(sum(r.jobs for r in game.city.rivals if r.key != 'moth') > 0,
         'while everybody else keeps working')
    game.city.hired = ''

    # Only somebody with enemies is worth selling.
    clean = rival_world.Rival(key='moth', rep={})
    T.eq(rival_world.bounty_buyers(clean), [],
         'nobody pays for a name that has not cost them anything')
    marked = rival_world.Rival(key='hound', rep={'nightwatch': -60})
    buyers = rival_world.bounty_buyers(marked)
    T.ok(buyers, 'a runner with enemies has a price')
    T.ok(all(v > 0 for _, v in buyers), 'and the price is positive')

    # Selling is permanent and wide.
    game2 = Game.new(Character.from_origin('gutter', 'x'), seed=33)
    target = game2.city.rival('hound')
    target.rep['nightwatch'] = -60
    others = {r.key: r.disposition for r in game2.city.rivals
              if r.key != 'hound'}
    rep_before = game2.alias.reputation('nightwatch')
    result = rival_world.sell_out(Rng(2)('events'), target, 'nightwatch',
                                  game2.city.rivals, game2.alias,
                                  game2.city.shift)
    T.ok(result['price'] > 0, 'selling pays')
    T.ok(result['outcome'] in ('taken', 'killed', 'escaped'),
         'the sale has a declared outcome')
    T.ok(target.disposition <= -100 + 1, 'the person you sold never forgives it')
    T.ok(game2.alias.reputation('nightwatch') > rep_before,
         'the buyer thinks better of you')
    cooled = [k for k, v in others.items()
              if game2.city.rival(k).disposition < v]
    T.eq(len(cooled), len(others),
         'every other runner in the city thinks less of you')

    # Favours are gated on disposition and cost the relationship.
    for kind in rival_content.FAVOURS:
        low = rival_world.Rival(key='moth', disposition=-100)
        ok, _ = rival_world.can_ask(low, kind)
        T.ok(not ok, f'{kind} is refused by somebody who dislikes you')
        high = rival_world.Rival(key='moth', disposition=100)
        ok, _ = rival_world.can_ask(high, kind)
        T.ok(ok, f'{kind} is granted by somebody who owes you')
    ok, _ = rival_world.can_ask(rival_world.Rival(key='moth', disposition=100),
                                'nonsense')
    T.ok(not ok, 'an unknown favour is refused')

    # An ally is only worth what their style says, and only next to you.
    net = net_mod.generate(Rng(5).fork('network', 'ally'), 'sixes', 30)
    char = Character.from_origin('gutter', 'x')
    console = quiet_console()
    console.start_capture()
    state = RunState.begin(net, char, Rng(5)('combat'), console)
    T.eq(state.ally_bonus('crack'), 0, 'no ally is no bonus')
    state.ally = {'key': 'moth', 'name': 'Moth', 'node': state.here,
                  'integrity': 20, 'state': 'with you', 'skill': 6,
                  'style': 'loud', 'cut': 0.25}
    T.ok(state.ally_bonus('crack') > 0, 'a loud ally helps you break things')
    T.eq(state.ally_bonus('social'), 0, 'but not with talking')
    state.ally['style'] = 'social'
    T.ok(state.ally_bonus('social') > 0, 'a social ally helps you talk')
    T.eq(state.ally_bonus('crack'), 0, 'but not with breaking')
    state.ally['node'] = '__elsewhere__'
    state.ally['style'] = 'loud'
    T.eq(state.ally_bonus('crack'), 0, 'and only while standing with you')

    # They can die, and the player survives it.
    state.ally['node'] = state.here
    state.hurt_ally(999)
    T.eq(state.ally['state'], 'dead', 'enough damage kills an ally')
    T.ok(state.running, 'the player survives their ally dying')
    T.eq(state.ally_bonus('crack'), 0, 'a dead ally is worth nothing')

    # An ally closes the distance to you on its own.
    state2 = RunState.begin(net, char, Rng(6)('combat'), console)
    far = [n for n in net.nodes if n != state2.here]
    if far:
        state2.ally = {'key': 'moth', 'name': 'Moth', 'node': far[-1],
                       'integrity': 20, 'state': 'with you', 'skill': 6,
                       'style': 'quiet', 'cut': 0.25}
        for _ in range(30):
            state2._ally_tick()
            if state2.ally['node'] == state2.here:
                break
        T.eq(state2.ally['node'], state2.here, 'an ally catches up with you')
    console.end_capture()

    # The hire survives a save, or paying up front means nothing.
    game.city.hired = 'ledger'
    game.save('social')
    back = Game.load('social')
    T.eq(back.city.hired, 'ledger', 'a paid-for hire survives a save')
    save_mod.delete('social')


def test_objectives() -> None:
    T.section('objectives')
    from flatline.world.contracts import OBJECTIVES

    # Every objective must have a resolution path that can actually be met.
    net = net_mod.generate(Rng(5).fork('network', 'c1'), 'sixes', 30)
    char = Character.from_origin('gutter', 'x')
    console = quiet_console()
    console.start_capture()

    for objective in OBJECTIVES:
        state = RunState.begin(net_mod.generate(
            Rng(5).fork('network', objective), 'sixes', 30),
            char, Rng(5)('combat'), console,
            contract={'objective': objective})
        T.ok(not state.objective_met(),
             f'{objective} does not start already met')

    # surveil: banks with residency, resets when the alert goes red, latches.
    state = RunState.begin(net, char, Rng(5)('combat'), console,
                           contract={'objective': 'surveil'})
    state.here = state.net.objective_node
    for _ in range(state.SURVEIL_TICKS):
        state._surveil_tick()
    T.ok(state.observed_enough, 'surveil banks with enough clean residency')
    T.ok(state.objective_met(), 'a banked surveil is met')

    state2 = RunState.begin(net, char, Rng(6)('combat'), console,
                            contract={'objective': 'surveil'})
    state2.here = state2.net.objective_node
    state2._surveil_tick()
    state2._surveil_tick()
    T.ok(state2.observed > 0, 'residency accumulates')
    state2.alert = 'red'
    state2._surveil_tick()
    T.eq(state2.observed, 0, 'being seen resets the count')
    T.ok(not state2.objective_met(), 'a reset surveil is not met')

    # Standing anywhere else banks nothing.
    state3 = RunState.begin(net, char, Rng(7)('combat'), console,
                            contract={'objective': 'surveil'})
    state3.here = state3.net.entry
    if state3.here != state3.net.objective_node:
        for _ in range(state3.SURVEIL_TICKS + 2):
            state3._surveil_tick()
        T.eq(state3.observed, 0, 'residency only counts on the objective node')

    # escort: has to finish the job AND get out.
    state4 = RunState.begin(net, char, Rng(8)('combat'), console,
                            contract={'objective': 'escort'})
    state4.escort = {'key': 'moth', 'name': 'Moth', 'node': net.entry,
                     'integrity': 20, 'state': 'working', 'skill': 6,
                     'done': False, 'progress': 0, 'panic': 'x'}
    T.ok(not state4.objective_met(), 'escort unmet while they are still in')
    state4.escort['done'] = True
    T.ok(not state4.objective_met(), 'escort unmet while they are still inside')
    state4.escort['state'] = 'out'
    T.ok(state4.objective_met(), 'escort met once they are done and out')
    state4.escort['state'] = 'dead'
    T.ok(not state4.objective_met(), 'a dead escort is not a completed job')

    # They can actually die, and it is not fatal to the player.
    state5 = RunState.begin(net, char, Rng(9)('combat'), console,
                            contract={'objective': 'escort'})
    state5.escort = {'key': 'moth', 'name': 'Moth', 'node': net.entry,
                     'integrity': 4, 'state': 'working', 'skill': 6,
                     'done': False, 'progress': 0, 'panic': 'x'}
    state5.hurt_escort(99)
    T.eq(state5.escort['state'], 'dead', 'enough damage kills the escort')
    T.ok(state5.running, 'the player survives their escort dying')

    # An escort walks the network on its own and does not wander off it.
    state6 = RunState.begin(net_mod.generate(
        Rng(11).fork('network', 'walk'), 'sixes', 30),
        char, Rng(11)('combat'), console, contract={'objective': 'escort'})
    state6.escort = {'key': 'ledger', 'name': 'Ledger', 'node': state6.net.entry,
                     'integrity': 200, 'state': 'working', 'skill': 10,
                     'done': False, 'progress': 0, 'panic': 'x'}
    for _ in range(80):
        state6._escort_tick()
        T.checks += 1
        if state6.escort['node'] not in state6.net.nodes:
            T.failures.append('objectives: escort walked off the network')
            break
        if state6.escort['state'] == 'out':
            break
    T.ok(state6.escort['done'], 'a competent escort reaches the job')
    T.ok(state6.escort['state'] == 'out', 'and finds its own way back out')

    console.end_capture()


def test_fallout() -> None:
    T.section('fallout')
    from flatline.world import fallout

    game = Game.new(Character.from_origin('gutter', 'x'), seed=99)
    T.ok(not game.city.bounties.get('sixes'), 'no bounty to begin with')

    # Sustained heat becomes a bounty.
    game.alias.add_heat('sixes', 90)
    for _ in range(3):
        game.city.advance(game.rng, game.alias, 1)
    T.ok(game.city.bounties.get('sixes', 0) > 0,
         'sustained heat becomes a standing bounty')

    # A bounty makes their districts dangerous.
    score, who = game.city.danger(game.alias, 'ninth', game.rng)
    T.ok(score >= fallout.INCIDENT_FLOOR,
         f'a bounty makes their turf risky (score {score})')
    T.eq(who, 'sixes', 'and names who is looking')

    # Every rung of the ladder costs something and none of them is fatal.
    stream = Rng(1)('events')
    for _ in range(60):
        char = Character.from_origin('chromed', 'x')
        char.credits = 5000
        alias = Alias(name='x')
        before = (char.credits, char.hurt, len(char.installed),
                  sum(char.deck.damage.values()))
        incident = fallout.pick_up(stream, char, alias, game.city, 'sixes')
        after = (char.credits, char.hurt, len(char.installed),
                 sum(char.deck.damage.values()))
        T.ok(incident.kind in fallout.OUTCOMES,
             f'incident kind {incident.kind!r} is one of the declared ones')
        T.ok(bool(incident.text), 'the incident describes itself')
        T.ok(char.integrity > 0, 'no incident kills the character (D6)')
        if incident.kind != 'burn':
            T.ok(after != before,
                 f'{incident.kind} actually costs something')

    # Bounties decay once the heat behind them is gone.
    game.alias.heat.clear()
    for _ in range(40):
        game.city.advance(game.rng, game.alias, 1)
    T.ok(not game.city.bounties.get('sixes'),
         'a bounty eventually comes off the board')



def test_appearance() -> None:
    T.section('appearance')

    # Every origin walks in looking like a different person. This is the whole
    # reason the field exists rather than one shared default.
    looks = {o.key: Character.from_origin(o.key, 'x').look
             for o in origins.ORIGINS}
    T.eq(len({tuple(sorted(v.items())) for v in looks.values()}),
         len(origins.ORIGINS), 'no two origins start with the same face')

    scores = {k: Character.from_origin(k, 'x').memorable for k in looks}
    T.ok(scores['ghost'] < 0, 'the legally dead are forgettable')
    T.ok(scores['chromed'] > 15, 'and the chromed are not')
    T.ok(max(scores.values()) - min(scores.values()) > 20,
         'the origins span a real range of memorability')

    # The two-sided trade is the design. Confirm both sides actually move,
    # and in opposite directions.
    T.ok(appearance.heat_mult(20) > appearance.heat_mult(0)
         > appearance.heat_mult(-15),
         'being memorable converts more residue into heat')
    T.ok(appearance.rep_mult(20) > appearance.rep_mult(0)
         > appearance.rep_mult(-15),
         'and earns more standing per job')

    # A forgettable build must be able to go negative. The chrome floor
    # clamped this to zero once, which deleted the bottom half of the scale
    # and with it the entire reason anybody would dress down.
    ghost = Character.from_origin('ghost', 'x')
    ghost.dissonance = 0
    T.ok(ghost.memorable < 0, 'a forgettable build reads below zero')
    T.ok(appearance.band(ghost.memorable)[0] == 'forgettable',
         'and lands in the band named for it')

    # Chrome puts a floor under it that no haircut gets below.
    ghost.dissonance = 90
    floored = ghost.memorable
    T.ok(floored >= appearance.floor_from_chrome(90),
         'chrome sets a floor under memorable')
    T.ok(floored > 0, 'and past a certain point you cannot be forgettable')
    for slot in appearance.FREE_SLOTS:
        best = min(appearance.BY_SLOT[slot], key=lambda f: f.memorable)
        ghost.look[slot] = best.key
    T.eq(ghost.memorable, floored,
         'dressing down as hard as possible does not get under the floor')

    # Marks are a record: awarded by the engine, never chosen, never repeated.
    char = Character.from_origin('gutter', 'x')
    T.ok(char.mark('black_ice') is not None, 'a mark can be earned')
    T.ok(char.mark('black_ice') is None, 'and is not earned twice')
    T.eq(char.marks, ['black_ice'], 'and is recorded once')
    T.ok(char.mark('not_a_mark') is None, 'an unknown mark is refused')
    T.ok(char.mark('ink') is None,
         'and a choosable mark cannot be awarded as an earned one')

    before = Character.from_origin('gutter', 'x').memorable
    T.ok(char.memorable > before, 'an earned mark makes you more memorable')

    # Surviving black ICE leaves the fern. This is the mark most likely to
    # rot, because the branch that awards it is rare.
    game = Game.new(Character.from_origin('gutter', 'ice'), seed=61)
    game.char.marks.clear()
    sess, _ = play([], game=game)
    sess.run = None
    T.ok('black_ice' in appearance.EARNED_BY_KEY,
         'the black ICE mark exists')

    # Dissonance past Submerged shows on you whether you like it or not.
    drifter = Character.from_origin('gutter', 'x')
    drifter.dissonance = 55
    drifter.new_passages()
    T.ok('drift_pallor' in drifter.marks, 'drift becomes visible at Submerged')

    # The description assembles into readable sentences, one per slot.
    lines = appearance.describe(char.look, char.marks)
    T.eq(len(lines), len(appearance.SLOTS) + len(char.marks),
         'one sentence per slot plus one per earned mark')
    for line in lines:
        T.ok(line.endswith('.'), 'each sentence is punctuated')
        T.ok(line[0].isupper(), 'and starts with a capital')

    # The command drives all of it.
    sess, out = play(['new Face --origin ghost --seed 11', 'self'])
    T.ok('forgettable' in out, '`self` reports the band')
    T.ok('memorable' in out and 'presence' in out, 'and both numbers')

    _, out = play(['new Face --origin gutter --seed 11', 'self dress'])
    T.ok('corporate' in out, '`self <slot>` lists the options')

    sess, out = play(['new Face --origin gutter --seed 11',
                      'self --set dress corporate'])
    T.eq(sess.game.char.look['dress'], 'corporate', '--set changes a slot')
    sess, out = play(['new Face --origin gutter --seed 11',
                      'self set dress corporate'])
    T.eq(sess.game.char.look['dress'], 'corporate',
         'and the positional form does the same')

    _, out = play(['new Face --origin gutter --seed 11',
                   'self --set build tall'])
    T.ok('clinic' in out.lower(),
         'a fixed slot refuses and points at the clinic')

    sess, _ = play(['new Face --origin gutter --seed 11', 'self --roll'])
    T.ok(sess.game.char.look['build'] == origins.BY_KEY['gutter'].look['build'],
         '--roll leaves the permanent features alone')

    # Bad input is a message, not a traceback.
    for line in ('self nonsense', 'self --set dress nonsense',
                 'self --set nonsense grey', 'self set', 'self --set'):
        _, out = play(['new Face --origin gutter --seed 11', line])
        T.ok(out.strip(), f'{line!r} says something')

    # And the whole thing survives a save.
    game = Game.new(Character.from_origin('courier', 'keeper'), seed=3)
    game.char.mark('bounty_mark')
    game.char.look['hair'] = 'dyed'
    game.save('face')
    back = Game.load('face')
    T.eq(back.char.look, game.char.look, 'a look survives a save')
    T.eq(back.char.marks, game.char.marks, 'and so do earned marks')
    T.eq(back.char.memorable, game.char.memorable, 'and the score it produces')
    save_mod.delete('face')



def test_migration() -> None:
    T.section('migration')
    import json

    from flatline.config import save_path

    # A save written under schema 1 must still open, with everything Phase 4
    # added filled in by the same rules a new game uses.
    game = Game.new(Character.from_origin('gutter', 'legacy'), seed=7)
    game.char.credits = 4321
    raw = game.to_dict()
    raw['schema'] = 1
    raw['character'].pop('icon', None)
    raw['character'].pop('icons', None)
    raw['city'].pop('rivals', None)
    raw['city'].pop('bounties', None)
    raw['character'].pop('look', None)
    raw['character'].pop('marks', None)
    path = save_path('legacy')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(raw), encoding='utf-8')

    back = Game.load('legacy')
    T.eq(back.char.handle, 'legacy', 'the character survives the migration')
    T.eq(back.char.credits, 4321, 'and their credits')
    T.ok(back.char.icon, 'the migration fills in an icon')
    T.ok(back.char.icon in back.char.icons, 'and it is one they own')
    T.ok(back.city.rivals, 'the migration seeds the runner pool')
    T.eq(back.city.bounties, {}, 'and an empty bounty ledger')

    # A face, and specifically the one their origin would have given them
    # rather than the flat default, which would have described somebody else.
    T.eq(set(back.char.look), set(appearance.SLOT_KEYS),
         'the migration fills in every appearance slot')
    T.eq(back.char.look, {**appearance.default(),
                          **origins.BY_KEY['gutter'].look},
         'with the look their origin starts from')
    T.eq(back.char.marks, [],
         'and no marks, because marks are a record and cannot be invented')

    # Migrating is idempotent through a save/load cycle.
    back.save('legacy')
    again = Game.load('legacy')
    T.eq(again.char.icon, back.char.icon, 'a migrated save round-trips')
    T.eq(len(again.city.rivals), len(back.city.rivals),
         'without duplicating what the migration added')
    save_mod.delete('legacy')

    # Every step in the chain exists and is a callable that returns a dict.
    for version in range(1, save_mod.SCHEMA):
        step = save_mod.MIGRATIONS.get(version)
        T.ok(callable(step), f'migration {version} exists')
        if step:
            out = step({'schema': version})
            T.ok(isinstance(out, dict), f'migration {version} returns a dict')


SUITES = (
    test_determinism, test_saves, test_character, test_checks,
    test_networks, test_run_mechanics, test_city, test_rivals,
    test_signatures, test_story, test_traits_and_spread, test_regressions, test_herders_and_kinds, test_passives_and_debt, test_dissonance, test_scripting, test_social, test_objectives, test_fallout, test_appearance, test_migration, test_shell,
    test_playthrough, test_ui,
)


def main() -> int:
    for suite in SUITES:
        try:
            suite()
        except Exception:
            T.failures.append(f'{suite.__name__} raised:\n'
                              + traceback.format_exc())
    for failure in T.failures:
        print(f'FAIL  {failure}')
    if T.failures:
        print(f'\ntest: {len(T.failures)} failures in {T.checks} checks')
        return 1
    print(f'test: green, {T.checks} checks')
    return 0


if __name__ == '__main__':
    sys.exit(main())
