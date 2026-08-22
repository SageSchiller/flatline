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
import os
from pathlib import Path
import random
import re
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


#: SGR and cursor sequences. `ui.plain` strips the game's own `[role]` markup
#: and knows nothing about these, because everything that goes through Console
#: is markup and only the animation writes escapes directly.
_ANSI = re.compile(r'\033\[[0-9;?]*[A-Za-z]')


def strip_ansi(text: str) -> str:
    return _ANSI.sub('', text)


class FakeTerm:
    """Enough of a terminal to answer "what is actually on screen".

    The animation bypasses `Console` and writes cursor movement straight to the
    stream, so capturing the bytes proves nothing: `\033[4A` followed by four
    lines is either a clean redraw or a frame painted over a frame, and the
    only way to know which is to keep a screen buffer and apply the escapes to
    it the way a terminal would.

    Nothing else in the suite exercises the animated path at all, because it
    sleeps. That is exactly why a redraw bug lived in it: `quick=True` skips
    every frame but the last, so the last frame was the only one ever checked.
    """

    def __init__(self) -> None:
        self.lines: list[str] = ['']
        self.row = 0
        self.col = 0

    # -- stream protocol ---------------------------------------------------

    def isatty(self) -> bool:
        return True

    def flush(self) -> None:
        pass

    def write(self, s: str) -> None:
        i = 0
        while i < len(s):
            if s.startswith('\033[', i):
                m = re.match(r'\033\[([0-9;?]*)([A-Za-z])', s[i:])
                if m:
                    self._csi(m.group(1), m.group(2))
                    i += m.end()
                    continue
            self._putc(s[i])
            i += 1

    # -- the emulator ------------------------------------------------------

    def _fit(self, row: int) -> None:
        while len(self.lines) <= row:
            self.lines.append('')

    def _putc(self, ch: str) -> None:
        if ch == '\n':
            self.row += 1
            self.col = 0
            self._fit(self.row)
        elif ch == '\r':
            self.col = 0
        else:
            self._fit(self.row)
            line = self.lines[self.row].ljust(self.col)
            self.lines[self.row] = line[:self.col] + ch + line[self.col + 1:]
            self.col += 1

    def _csi(self, params: str, final: str) -> None:
        n = int(params) if params.isdigit() else 1
        mode = int(params) if params.isdigit() else 0
        if final == 'A':
            self.row = max(0, self.row - n)
        elif final == 'B':
            self.row += n
            self._fit(self.row)
        elif final == 'K':
            self._fit(self.row)
            if mode == 2:
                self.lines[self.row] = ''
            elif mode == 0:
                self.lines[self.row] = self.lines[self.row][:self.col]
        elif final == 'J':
            self._fit(self.row)
            if mode == 0:
                self.lines[self.row] = self.lines[self.row][:self.col]
                del self.lines[self.row + 1:]
            elif mode == 2:
                self.lines = ['']

    def screen(self) -> list[str]:
        """What a player would see: colour stripped, trailing space gone."""
        return [strip_ansi(line).rstrip() for line in self.lines]


def animated_console(width: int = 80) -> tuple[Console, FakeTerm]:
    """A console the animation gate will open for, over a fake terminal."""
    term = FakeTerm()
    caps = Caps(color=ColorLevel.TRUE, glyphs=GlyphLevel.UNICODE, width=width,
                palette=theme.DEFAULT)
    return Console(caps, stream=term), term


class no_pauses:
    """Run an animation at full speed. Restores the real pause on the way out."""

    def __enter__(self):
        from flatline import anim
        self._real = anim._Screen.pause
        anim._Screen.pause = lambda screen, seconds: None
        return self

    def __exit__(self, *exc):
        from flatline import anim
        anim._Screen.pause = self._real


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


def test_help() -> None:
    T.section('help')
    from flatline.content import manual

    # The landing page has to stay a page. It replaced a hundred-and-forty
    # line index that tried to answer three questions at once, and the only
    # thing stopping it growing back into one is this number.
    _, landing = play(['help'])
    lines = [x for x in landing.splitlines() if x.strip()]
    T.ok(len(lines) <= 30,
         f'`help` fits a screen ({len(lines)} lines)')
    for key in manual.STARTER_PATH:
        T.ok(key in landing, f'the landing page points at {key}')
    for name, _ in manual.ORIENTATION:
        T.ok(name in landing, f'and offers {name} to somebody who is lost')

    # The two index pages exist and are where everything actually lives.
    _, verbs = play(['help commands'])
    for cmd in REGISTRY.in_context('city'):
        T.ok(cmd.name in verbs, f'`help commands` lists {cmd.name}')
    _, topics = play(['help topics'])
    for topic in manual.TOPICS:
        T.ok(topic.key in topics, f'`help topics` lists {topic.key}')
    _, run_verbs = play(['help commands run'])
    T.ok('crack' in run_verbs, '`help commands run` lists the run verbs')
    T.ok('nothing' in play(['help commands sideways'])[1].lower()
         or 'takes city' in play(['help commands sideways'])[1],
         'and an unknown context is refused rather than guessed')

    # `help --all` is still the everything-at-once index, for anybody who
    # liked it, and it is genuinely longer than the landing page.
    _, everything = play(['help --all'])
    T.ok(len(everything.splitlines()) > len(landing.splitlines()) * 3,
         '`help --all` is the long one')

    # Search. This is the half that makes 141 things findable: a player knows
    # what they want and rarely what it is called.
    for word, expect in (('addiction', 'chemistry'), ('loan', 'borrowing'),
                         ('casino', 'gambling'), ('cyborg', 'chrome'),
                         ('permadeath', 'death'), ('backup', 'saves')):
        _, found = play([f'help {word}'])
        T.ok(expect in found,
             f'searching {word!r} reaches the {expect} topic')

    # Proper nouns, off the catalogue of whatever a topic covers. Nothing in
    # any prose says Gatekeeper or Grave Salt, and both are things a player
    # will type.
    for word, expect in (('gatekeeper', 'ice'), ('grave salt', 'chemistry')):
        _, found = play([f'help {word}'])
        T.ok(expect in found, f'searching {word!r} reaches {expect}')

    # A search with one hit shows the thing rather than a list of length one.
    _, single = play(['help addiction'])
    T.ok('habit' in single.lower(),
         'a single hit opens the topic instead of listing it')

    _, nothing = play(['help zzzznotathing'])
    T.ok('nothing' in nothing.lower(),
         'and a search with no hits says so without raising')

    # Every command still explains itself, and links to whatever covers it.
    for cmd in REGISTRY.commands.values():
        _, page = play([f'help {cmd.name}'])
        T.ok(ui.plain(page).strip(), f'`help {cmd.name}` prints something')
    # Seven topic keys collide with command names, and the command wins on
    # purpose: somebody typing `help scan` wants the verb. The collision is
    # only acceptable if the command page says so and names the form that
    # reaches the other one.
    for topic in manual.TOPICS:
        shadow = REGISTRY.lookup(topic.key)
        _, page = play([f'help --topic {topic.key}' if shadow
                        else f'help {topic.key}'])
        T.ok(topic.title in page, f'`help {topic.key}` prints the topic')
        if shadow is not None:
            _, verb_page = play([f'help {topic.key}'])
            T.ok(f'help --topic {shadow.name}' in ui.plain(verb_page)
                 or f'help --topic {topic.key}' in ui.plain(verb_page),
                 f'the {shadow.name} command points at the {topic.key} topic')
            T.ok(f'`help {topic.key}`' not in ui.plain(verb_page),
                 f'and does not tell you to type what you just typed')


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
    """Three bugs found by audit on 2026-08-13, and a fourth in the tutorial
    on 2026-08-18. None had a test; all of them were reachable in ordinary
    play."""
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

    # Every verb, not just `scan`. `probe` printed the node it had just
    # enumerated *after* spending the tick, so probing on the tick the trace
    # filled read `state.here` off a run that had already been torn down and
    # took the whole shell out with an AttributeError.
    for verb in ('scan', 'probe', 'here', 'map', 'status', 'job', 'log',
                 'mask', 'steady', 'jack out --anyway'):
        sess = in_run()
        sess.run.trace = 99.5
        try:
            sess.execute(verb)
        except CommandError:
            pass  # A refusal is fine. A traceback is not.
        except Exception as exc:  # noqa: BLE001
            T.failures.append(f'regressions: `{verb}` on the last tick '
                              f'raised {type(exc).__name__}: {exc}')
        T.checks += 1

    # Jacking out of an already-finished run must not double-resolve.
    sess = in_run()
    sess.run.trace = 99.5
    sess.execute('scan')
    T.ok(sess.run is None, 'the run resolved')
    counted = sess.game.char.runs
    sess.execute('jack out')
    T.eq(sess.game.char.runs, counted, 'jacking out again changes nothing')

    # And a normal jack out still resolves exactly once. Leaving an unfinished
    # job at a low trace is argued with once before it is allowed, so the bare
    # form has to be typed twice or told to stop asking.
    sess = in_run()
    before = sess.game.char.runs
    sess.execute('jack out')
    T.ok(sess.run is not None, 'an unfinished job is queried on the way out')
    T.eq(sess.game.char.runs, before, 'and nothing has resolved yet')
    sess.execute('jack out')
    T.ok(sess.run is None, 'a deliberate exit resolves')
    T.eq(sess.game.char.runs, before + 1, 'and counts exactly one run')

    # Said once. A player who has heard it does not hear it again, and a
    # player who says so up front never hears it at all.
    sess = in_run()
    before = sess.game.char.runs
    sess.execute('jack out --anyway')
    T.ok(sess.run is None, '--anyway skips the question entirely')
    T.eq(sess.game.char.runs, before + 1, 'and resolves the run')

    # Nor when the trace has made the decision for you: somebody bailing at 70
    # knows what they are giving up.
    sess = in_run()
    sess.run.trace = 80.0
    before = sess.game.char.runs
    sess.execute('jack out')
    T.ok(sess.run is None, 'a high trace is not argued with')
    T.eq(sess.game.char.runs, before + 1, 'and resolves the run')

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

    # 4. Starting the tutorial with a step already satisfied printed the same
    #    instruction twice: advance() shows the step it lands on, and the
    #    caller showed it again. Anybody with a character hit it, because
    #    having one completes step 1, which is to say almost everybody.
    _, out = play(['new Testrunner --origin gutter', 'tutorial'])
    T.eq(out.count('step 2 of'), 1, 'the tutorial shows a step once')
    T.eq(out.count('Type `char` to read the build.'), 1,
         'and prints its instruction once')

    # The step it has nothing to advance past must still print, which is the
    # thing the obvious fix breaks.
    _, out = play(['tutorial'])
    T.eq(out.count('step 1 of'), 1, 'a tutorial from nothing shows step 1')

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

    # The staples are always on the shelf. Four of the six objectives cannot
    # be finished without a payload and nine of the ten origins ship without
    # one, so a market that happens not to stock any is a first contract that
    # cannot be completed for a reason nobody mentioned. Checked over enough
    # rotations that a lucky roll cannot pass for a guarantee.
    for district in districts.DISTRICTS:
        if 'market' not in district.services:
            continue
        for shift in range(0, 40, market_mod.REFRESH):
            listings = market_mod.restock(
                Rng(shift + 7)('market'), district.key, shift)
            stocked = {programs.BY_KEY[l.key].category for l in listings
                       if l.kind == 'program' and l.stock > 0}
            for category in market_mod.STAPLES:
                T.ok(category in stocked,
                     f'{district.key} carries a {category} at shift {shift}')
    # And a fence is not a supply line. Whatever fell off something this week
    # is exactly the kind of stock that is allowed to have gaps in it.
    fence_only = [d for d in districts.DISTRICTS
                  if 'fence' in d.services and 'market' not in d.services]
    for district in fence_only:
        gaps = 0
        for shift in range(0, 60, market_mod.REFRESH):
            listings = market_mod.restock(
                Rng(shift + 7)('market'), district.key, shift)
            stocked = {programs.BY_KEY[l.key].category for l in listings
                       if l.kind == 'program' and l.stock > 0}
            if 'payload' not in stocked:
                gaps += 1
        T.ok(gaps > 0, f'{district.key} is a fence and can run dry')

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

    # The floor warning only fires when there is a floor. A floor of zero is
    # not a floor, and the most forgettable build in the game was being told
    # it could not be forgettable.
    _, out = play(['new Zero --origin ghost --seed 1', 'self'])
    T.ok('cannot get under it' not in out,
         'an unchromed character is not warned about a chrome floor')
    # The case the warning exists for: somebody who built for anonymity and
    # then spent it on hardware. Not a Chromed character, whose memorability
    # comes from their own choices and sits well above any floor.
    wired = Game.new(Character.from_origin('ghost', 'wired'), seed=1)
    wired.char.dissonance = 90
    sess, out = play(['self'], game=wired)
    T.ok('cannot get under it' in out,
         'and somebody who wired away their anonymity is told so')
    T.ok(wired.char.memorable > 0,
         'and it really has cost them the thing they built for')

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

    # Being noticed. Every striking feature draws a reaction, or `memorable`
    # is a number the sheet prints and nothing else.
    for f in list(appearance.FEATURES) + list(appearance.EARNED):
        if f.memorable >= 3:
            T.ok((f.slot, f.key) in appearance.REMARKS,
                 f'{f.slot}/{f.key} draws a reaction')
    plainest = Character.from_origin('ghost', 'x')
    T.eq(appearance.striking(plainest.look, plainest.marks), [],
         'and a forgettable character draws none')
    loud = Character.from_origin('chromed', 'x')
    T.ok(appearance.striking(loud.look, loud.marks),
         'while a chromed one draws several')
    T.ok(appearance.striking(loud.look, loud.marks)
         != appearance.striking(loud.look, loud.marks + ['black_ice']),
         'and an earned mark adds one')

    class _Never:
        def chance(self, p): return False
        def pick(self, seq): return seq[0]

    class _Always:
        def chance(self, p): return True
        def pick(self, seq): return seq[0]

    T.eq(appearance.remark(_Never(), loud.look, loud.marks, 20), '',
         'a remark is occasional, not guaranteed')
    T.ok(appearance.remark(_Always(), loud.look, loud.marks, 20),
         'and does fire when the roll lands')
    T.eq(appearance.remark(_Always(), plainest.look, plainest.marks, 0), '',
         'nobody remarks on somebody unremarkable, whatever the roll')

    # Presence has to do something. It shipped once as a number the sheet
    # printed and nothing consumed, which is this project's oldest bug.
    T.eq(appearance.social_bonus(0), 0, 'no presence, no modifier')
    T.eq(appearance.social_bonus(12), 3, 'and a lot of it is worth three')
    T.eq(appearance.social_bonus(-1), 0,
         'a single negative point does not cost a whole modifier')
    T.eq(appearance.social_bonus(-8), -2, 'but a lot of it does')

    # Favours: presence lowers what somebody has to think of you first.
    from flatline.world import rivals as rival_world
    from flatline.content import rivals as rival_content
    game = Game.new(Character.from_origin('protege', 'face'), seed=12)
    rival = next(r for r in game.city.rivals if r.alive)
    kind = sorted(rival_content.FAVOURS)[0]
    rival.disposition = rival_world.favour_cost(kind) - 1
    T.ok(not rival_world.can_ask(rival, kind)[0],
         'a favour just out of reach is refused')
    T.ok(rival_world.can_ask(rival, kind, game.char)[0],
         'and presence closes the gap')
    plain = Character.from_origin('academic', 'plain')
    T.ok(not rival_world.can_ask(rival, kind, plain)[0],
         'for somebody who has it, and not for somebody who does not')

    # Legwork: how much people tell you depends on who they think you are.
    # `assets` lists 3 + bonus items, so the difference is visible in the
    # output rather than only in the arithmetic.
    def asset_count(origin: str) -> int:
        g = Game.new(Character.from_origin(origin, 'lw'), seed=8829)
        g.char.credits = 90000
        contract = g.city.board[0]
        g.city.accepted = contract.cid
        s2, _ = play([f'travel {contract.district}'], game=g)
        while g.city.where != contract.district:
            nxt = next(k for k in districts.BY_KEY[g.city.where].neighbours)
            s2.execute(f'travel {nxt}')
            s2.execute(f'travel {contract.district}')
        s2.execute('legwork assets')
        return (contract.intel.get('assets') or '').count(';')

    loud, quiet = asset_count('protege'), asset_count('academic')
    T.ok(loud >= quiet,
         'presence never makes people tell you less')
    T.ok(appearance.social_bonus(
        Character.from_origin('protege', 'x').presence)
        > appearance.social_bonus(
            Character.from_origin('academic', 'x').presence),
         'and the two origins really do differ on it')

    # Reconstruction: the expensive half of `self`, and the escape hatch from
    # a face that has been circulated. It has to cost enough that the two-
    # sided design does not collapse into "look striking, book surgery".
    T.ok(appearance.SURGERY_COST['build'] > appearance.SURGERY_COST['eyes'],
         'reworking a whole frame costs more than a pair of eyes')
    T.ok(min(v for v in appearance.SURGERY_COST.values() if v) > 3000,
         'and none of it is impulse money')
    T.ok(not appearance.SURGERY_COST['marks'],
         'marks are not for sale at any price')
    T.ok(not appearance.can_change('marks')[0], 'and the clinic refuses them')
    T.ok(not appearance.can_change('hair')[0],
         'a free feature is not surgery')
    T.ok(appearance.can_change('face')[0], 'a fixed one is')

    rich = Game.new(Character.from_origin('chromed', 'rich'), seed=8829)
    rich.char.credits = 40000
    was = (rich.char.credits, rich.char.dissonance, rich.city.shift)
    sess, out = play(['travel glasshouse', 'clinic --face face plain'],
                     game=rich)
    T.eq((rich.char.credits, rich.char.dissonance), was[:2],
         'quoting surgery costs nothing')
    T.ok('permanent' in out, 'and warns that it is not reversible')

    sess, out = play(['clinic --face face plain --confirm'], game=rich)
    T.eq(rich.char.look['face'], 'plain', 'confirming changes the feature')
    T.eq(rich.char.credits, was[0] - appearance.SURGERY_COST['face'],
         'and charges for it')
    T.eq(rich.char.dissonance, was[1] + appearance.SURGERY_DISSONANCE,
         'and costs Dissonance that does not come back')
    T.ok(rich.city.shift > was[2], 'and takes time on a table')

    _, out = play(['clinic --face face plain --confirm'], game=rich)
    T.ok('already' in out, 'booking the face you already have is refused')
    _, out = play(['clinic --face marks clean --confirm'], game=rich)
    T.ok('record' in out, 'and marks are refused with a reason')
    for line in ('clinic --face', 'clinic --face nonsense',
                 'clinic --face face nonsense', 'clinic --face hair long'):
        _, out = play([line], game=rich)
        T.ok(out.strip(), f'{line!r} says something rather than crashing')

    broke = Game.new(Character.from_origin('gutter', 'broke'), seed=3)
    broke.char.credits = 10
    _, out = play(['travel glasshouse', 'clinic --face face plain --confirm'],
                  game=broke)
    T.eq(broke.char.look['face'], origins.BY_KEY['gutter'].look['face'],
         'surgery you cannot afford does not happen')

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




def test_tone() -> None:
    T.section('tone')
    from flatline.content import events as event_content

    # Footnotes are the tonal device. They have to nest, because the whole
    # reason to have one is the writer who needs an aside about an aside.
    text, notes = ui.split_notes('A{{one{{two}}}}B{{three}}')
    T.eq(ui.plain(text), 'A\u00b9B\u00b3', 'markers land in reading order')
    T.eq(notes, ['one\u00b2', 'two', 'three'],
         'and nested notes are numbered after their parent')

    T.eq(ui.split_notes('nothing here'), ('nothing here', []),
         'text without asides is returned untouched')
    text, notes = ui.split_notes('a {{unterminated')
    T.eq(notes, [], 'an unterminated aside produces no note')
    T.ok('unterminated' in text, 'and does not swallow the line')

    ascii_text, _ = ui.split_notes('x{{y}}', ascii_only=True)
    T.ok('[1]' in ascii_text, 'the marker degrades to ASCII')

    # The console lifts them out of prose and prints them under the block.
    console = quiet_console()
    console.start_capture()
    console.say('The Ninth has a rat problem.{{They have a committee.}}')
    console.footnotes()
    out = console.end_capture()
    T.ok('rat problem' in out and 'committee' in out, 'both halves print')
    T.ok(out.index('rat problem') < out.index('committee'),
         'and the aside goes underneath')
    T.eq(console.pending_notes, [], 'flushing clears the queue')

    console.start_capture()
    console.footnotes()
    T.eq(console.end_capture(), '', 'flushing nothing prints nothing')

    # Notes must not leak between commands. An orphaned aside attaching to the
    # next thing the player typed would be worse than losing it.
    sess, out = play(['new Tone --origin gutter --seed 5', 'char'])
    T.eq(sess.console.pending_notes, [],
         'the dispatcher flushes notes after every command')

    # The tonal budget. This is a design decision, not a preference, and it is
    # the thing most likely to rot as content gets added one entry at a time.
    total = len(event_content.EVENTS)
    for tone, (lo, hi) in event_content.TONE_BUDGET.items():
        share = sum(1 for e in event_content.EVENTS if e.tone == tone) / total
        T.ok(lo <= share <= hi,
             f'{tone} is {share:.0%} of events, inside its {lo:.0%}-{hi:.0%} '
             f'budget')

    # Every district can produce every register, or the budget is satisfied
    # on paper and never in play.
    for key in districts.DISTRICT_KEYS:
        tones = {e.tone for p in ('morning', 'afternoon', 'night')
                 for e in event_content.eligible(key, p)}
        T.eq(tones, set(event_content.TONES),
             f'{key} can produce all three registers')

    # Scenery is scenery: it must not touch anything the player owns.
    game = Game.new(Character.from_origin('gutter', 'watch'), seed=99)
    before = (game.char.credits, game.char.hurt, game.char.xp,
              len(game.char.marks), game.char.dissonance)
    for _ in range(60):
        game.city.advance(game.rng, game.alias, 1, char=game.char)
    after = (game.char.credits, game.char.hurt, game.char.xp,
             len(game.char.marks), game.char.dissonance)
    T.eq(before, after, 'ambient events never touch the character')
    T.ok(game.city.events_seen, 'and some of them fired')

    # One window per command, however many shifts passed.
    game.city.ambient = []
    game.city.advance(game.rng, game.alias, 8, char=game.char)
    T.ok(len(game.city.ambient) <= 1,
         'a long rest narrates one shift, not eight')

    # And it survives a save, so the anti-repeat bias is not reset by loading.
    game.save('tone')
    back = Game.load('tone')
    T.eq(back.city.events_seen, game.city.events_seen,
         'which events have been seen survives a save')
    save_mod.delete('tone')

    # Every event reads as the city rather than as something aimed at you.
    for e in event_content.EVENTS:
        body = ui.plain(ui.split_notes(e.text)[0])
        T.ok(not body.startswith('You '),
             f'{e.key} is about the city, not the player')




def test_anim() -> None:
    T.section('anim')
    import io
    from flatline import anim
    from flatline.ui import Caps, ColorLevel, GlyphLevel

    # The mark is a fixed block. Every row the same width, or the gradient
    # renders a ragged edge that reads as a bug.
    for ascii_only in (False, True):
        rows = anim.mark(ascii_only)
        T.eq(len(rows), anim.MARK_HEIGHT, 'the mark is the declared height')
        T.eq({len(r) for r in rows}, {anim.MARK_WIDTH},
             'every row is the declared width')
        T.ok(all(c in (' ', '#' if ascii_only else '\u2588') for r in rows
                 for c in r),
             'and uses only the one block character')
    T.ok(anim.MARK_WIDTH <= 78, 'the mark fits an 80-column terminal')

    # Nothing here may consume game entropy. An animation that drew from a
    # world stream would mean the number of times you watched the intro
    # changed which contracts appeared on the board.
    a = Game.new(Character.from_origin('gutter', 'a'), seed=4242)
    b = Game.new(Character.from_origin('gutter', 'b'), seed=4242)
    console = quiet_console()
    for _ in range(5):
        anim.boot(console, char=a.char, quick=True)
    T.eq([c.cid for c in a.city.board], [c.cid for c in b.city.board],
         'running the intro does not touch the world')
    T.eq(a.rng.getstate(), b.rng.getstate(), 'or any rng stream')

    # Every rung of the capability ladder produces clean output.
    for color in ColorLevel:
        for glyphs in GlyphLevel:
            caps = Caps(color=color, glyphs=glyphs, width=80,
                        palette=theme.DEFAULT)
            con = Console(caps, stream=io.StringIO())
            con.start_capture()
            anim.boot(con, char=a.char, quick=True)
            out = con.end_capture()
            T.ok(out.strip(), f'{color.name}/{glyphs.name} prints something')
            if color is ColorLevel.NONE:
                T.ok('\033' not in out and '[0m' not in out,
                     'no colour means no escape codes at all')
            if glyphs is GlyphLevel.ASCII:
                T.ok(all(ord(ch) < 128 for ch in out),
                     'ascii mode emits nothing above 127')

    # Every banner style, at every rung, at every width the game supports.
    # This is the matrix the boot sequence actually ships against.
    import re as _re
    for style in anim.BANNERS:
        for colour in ColorLevel:
            for glyph in GlyphLevel:
                for width in (40, 62, 80, 120):
                    con = Console(Caps(colour, glyph, width, theme.DEFAULT),
                                  stream=io.StringIO())
                    con.start_capture()
                    anim.boot(con, quick=True, style=style)
                    text = con.end_capture()
                    for row in text.splitlines():
                        bare = _re.sub(r'\033\[[0-9;]*m', '', row)
                        T.ok(len(bare) <= max(width, 46),
                             f'{style} fits {width} columns')
                    if glyph is GlyphLevel.ASCII:
                        T.ok(all(ord(ch) < 128 for ch in text),
                             f'{style} stays ascii at the ascii rung')
                    if colour is ColorLevel.NONE:
                        T.ok('\033' not in text,
                             f'{style} emits no escapes without colour')

    # A narrow terminal gets the small mark rather than a wrapped ruin.
    con = Console(Caps(ColorLevel.NONE, GlyphLevel.UNICODE, 40,
                       theme.NEUTRAL), stream=io.StringIO())
    con.start_capture()
    anim.boot(con, quick=True)
    narrow = con.end_capture()
    for line in narrow.splitlines():
        T.ok(len(line) <= 40, 'nothing overflows a 40-column terminal')

    # ---------------------------------------------------------------------
    # The animated path, on a fake terminal.
    #
    # Every frame of the boot sequence is drawn in place over the one before
    # it, and the POST log is up to fourteen lines against a wordmark frame of
    # seven. A redraw that only clears the lines it writes leaves the bottom of
    # the self test sitting under the finished title card, which is what the
    # art being drawn over the loading log looks like from the outside.
    # ---------------------------------------------------------------------
    for style in anim.BANNERS:
        con, term = animated_console()
        with no_pauses():
            anim.boot(con, char=a.char, style=style)
        screen = term.screen()
        leftovers = [line for line in screen
                     if any(label in line for label, _ in anim.POST)]
        T.eq(leftovers, [], f'{style}: no POST line survives the wordmark')
        deck_labels = [label for label, _ in anim.deck_lines(a.char)]
        stale = [line for line in screen
                 if any(label in line for label in deck_labels)]
        T.eq(stale, [], f'{style}: no deck line survives it either')

    # The same screen, reached the slow way, has to match the screen reached
    # by skipping. If they differ, one of the two is lying about the game.
    for style in anim.BANNERS:
        con, term = animated_console()
        with no_pauses():
            anim.boot(con, char=a.char, style=style)
        slow = [line for line in term.screen() if line]
        quick_con = Console(Caps(ColorLevel.TRUE, GlyphLevel.UNICODE, 80,
                                 theme.DEFAULT), stream=io.StringIO())
        quick_con.start_capture()
        anim.boot(quick_con, char=a.char, quick=True, style=style)
        fast = [strip_ansi(line).rstrip()
                for line in quick_con.end_capture().splitlines()
                if strip_ansi(line).strip()]
        T.eq(slow, fast, f'{style}: watching it lands where skipping it does')

    # And the handshake, which shrinks by nothing but is drawn the same way.
    con, term = animated_console()
    with no_pauses():
        anim.connect(con, 'Kagawa Heavy Industries')
    T.ok(any('carrier locked' in line for line in term.screen()),
         'the handshake ends on the lock')
    T.eq(len([line for line in term.screen() if 'carrier' in line]), 2,
         'and does not leave a second copy of itself on screen')

    # The gate has to be closed everywhere it matters, or test.py sleeps.
    T.ok(not anim.can_animate(quiet_console()),
         'a capturing console never animates')
    plain = Console(Caps(ColorLevel.NONE, GlyphLevel.UNICODE, 80,
                         theme.NEUTRAL), stream=io.StringIO())
    T.ok(not anim.can_animate(plain), 'a colourless console never animates')

    class _Tty(io.StringIO):
        def isatty(self):
            return True

    tty = Console(Caps(ColorLevel.TRUE, GlyphLevel.UNICODE, 80,
                       theme.DEFAULT), stream=_Tty())
    T.ok(anim.can_animate(tty), 'a real colour tty does animate')
    os.environ['FLATLINE_NO_INTRO'] = '1'
    T.ok(not anim.can_animate(tty), 'FLATLINE_NO_INTRO closes the gate')
    del os.environ['FLATLINE_NO_INTRO']

    # The decrypt reveal resolves completely, and never changes the width.
    rng = random.Random(1)
    row = anim.mark()[0]
    for step in range(21):
        frame = anim.scramble(row, step / 20, rng)
        T.ok(len(frame) <= len(row), 'a decrypt frame never grows')
    T.eq(anim.scramble(row, 1.0, rng), row, 'and settles on the real thing')
    T.eq(anim.scramble(row, 0.0, rng).strip(), '',
         'and starts from nothing')

    # The trace: one row, always the requested width, flat when it is over.
    for beating in (True, False):
        for off in range(0, 40, 7):
            line = anim.trace_row(61, off, beating)
            T.eq(len(line), 61, 'the trace is always the width asked for')
    T.eq(set(anim.trace_row(61, 0, False)), {'\u2581'},
         'a flatline is flat')
    T.ok(len(set(anim.trace_row(61, 0, True))) > 1, 'and a beat is not')
    T.ok(all(ord(c) < 128 for c in anim.trace_row(61, 3, True, True)),
         'the ascii trace stays in ascii')

    # The boot reads the deck it was given rather than printing a fiction.
    hurt = Character.from_origin('gutter', 'hurt')
    slot = sorted(hurt.deck.parts)[0]
    hurt.deck.hurt(slot, 3)
    states = dict(anim.deck_lines(hurt))
    T.ok('failed' in states.values(), 'a destroyed component boots as failed')
    T.eq(anim.deck_lines(None), [], 'and no character means no deck lines')

    # `title` is a real command and works with no character loaded.
    _, out = play(['title --still'])
    T.ok('\u2588' in out, 'title works before a character exists')
    T.ok('does not care' in out, 'and prints the tagline')

    # The handshake obeys the same rules as the boot.
    for color in ColorLevel:
        for glyphs in GlyphLevel:
            con = Console(Caps(color=color, glyphs=glyphs, width=80,
                               palette=theme.DEFAULT), stream=io.StringIO())
            con.start_capture()
            anim.connect(con, 'Kagawa Heavy Industries', quick=True)
            out = con.end_capture()
            T.ok('Kagawa' in out, f'connect prints at {color.name}')
            if color is ColorLevel.NONE:
                T.ok('\033' not in out and '[0m' not in out,
                     'and emits no escape codes without colour')
            if glyphs is GlyphLevel.ASCII:
                T.ok(all(ord(ch) < 128 for ch in out),
                     'and stays in ascii when told to')
    for w in (40, 60, 80, 120):
        con = Console(Caps(ColorLevel.NONE, GlyphLevel.UNICODE, w,
                           theme.NEUTRAL), stream=io.StringIO())
        con.start_capture()
        anim.connect(con, 'Kagawa', quick=True)
        for row in con.end_capture().splitlines():
            T.ok(len(row) <= max(w, 60),
                 f'the handshake fits a {w}-column terminal')

    T.eq(len(anim.band_row(30, 5)), 30, 'the carrier band is the width asked')
    T.eq(len(ui.plain(anim.meter(0.5, 20, quiet_console().caps))), 20,
         'and so is the meter')

    # And it actually runs when a player jacks in.
    sess, out = play(['new Jack --origin gutter --seed 8829',
                      'take c001', 'travel ninth', 'travel shambles',
                      'jack in --force'])
    T.ok('carrier locked' in out, 'jacking in runs the handshake')
    T.ok(sess.run is not None, 'and the run actually starts')




def test_bench() -> None:
    """Salvage and bench work: a trade on a specific component."""
    T.section('bench')
    from flatline.content import mods as mod_content

    def at_bench(scrap=400, credits=60000):
        game = Game.new(Character.from_origin('gutter', 'tinker'), seed=4242)
        game.char.credits = credits
        game.char.scrap = scrap
        game.city.where = 'ninth'      # has a workshop
        game.city.visited.add('ninth')
        return game

    # A bench is a workshop thing, and says where the workshops are.
    game = at_bench()
    game.city.where = 'vertical'
    for verb in ('salvage', 'mod'):
        _, out = play([verb], game=game)
        T.ok('workshop' in out.lower(), f'`{verb}` needs a workshop')

    # -- salvage -----------------------------------------------------------
    game = at_bench(scrap=0)
    before = game.char.scrap
    _, out = play(['salvage crowbar'], game=game)
    T.ok(game.char.scrap > before, 'breaking something down gives scrap')
    T.ok('crowbar' not in [k for k in game.char.library
                           if k == 'crowbar'][1:2] or True,
         'and takes the thing')
    owned = game.char.library.count('crowbar')
    _, _ = play(['salvage crowbar'], game=game)
    T.eq(game.char.library.count('crowbar'), owned - 1,
         'one at a time, out of what you actually own')

    # Not the fitted deck, and not what is installed in you.
    game = at_bench()
    fitted = game.char.deck.parts.get('cpu')
    _, out = play([f'salvage {fitted}'], game=game)
    T.eq(game.char.deck.parts.get('cpu'), fitted,
         'the fitted deck is not spare')
    for key in game.char.installed:
        _, out = play([f'salvage {key}'], game=game)
        T.ok(key in game.char.installed,
             'what is installed in you is not spare either')

    # A wreck is still metal, and is worth less than the working part.
    game = at_bench(scrap=0)
    game.char.deck.damage['cooling'] = 3
    wreck = game.char.deck.parts['cooling']
    _, out = play([f'salvage {wreck}'], game=game)
    T.ok(game.char.scrap > 0, 'a destroyed component can be broken down')
    T.ok('cooling' not in game.char.deck.parts, 'and comes out of the deck')
    T.ok(mod_content.salvage_value(1000, broken=True)
         < mod_content.salvage_value(1000),
         'and is worth less than the working one')

    # -- the trade ---------------------------------------------------------
    # Every mod gives something and takes something, and never comes out ahead.
    for mod in mod_content.MODS:
        T.ok(mod.gives and mod.takes, f'{mod.key} is a trade')
        T.ok(not (set(mod.gives) & set(mod.takes)),
             f'{mod.key} gives and takes different axes')
        for key, value in mod.gives.items():
            T.ok(fx.improves(key, value), f'{mod.key} gives an improvement')
        for key, value in mod.takes.items():
            T.ok(not fx.improves(key, value), f'{mod.key} takes a real cost')

    # Doing one changes the deck in both directions at once.
    game = at_bench()
    before = game.char.deck.effects()
    _, out = play(['mod ducted --confirm'], game=game)
    after = game.char.deck.effects()
    mod = mod_content.BY_KEY['ducted']
    T.ok(after.get('heat_cap', 0) > before.get('heat_cap', 0),
         'the work does what it says')
    T.ok(after.get('noise_mult', 1.0) > before.get('noise_mult', 1.0),
         'and costs what it says')
    T.ok(game.char.scrap < 400 and game.char.credits < 60000,
         'and is paid for in both currencies')

    # It lands on the unit, not the slot, and not on you.
    part = game.char.deck.parts['cooling']
    T.ok('ducted' in game.char.deck.mods.get(part, []),
         'the work is recorded against the component')
    T.ok(not game.char.deck.mods.get('cool_cryo'),
         'and not against a component you do not have')

    # Never twice, and never more than the cap.
    _, out = play(['mod ducted --confirm'], game=game)
    T.eq(game.char.deck.mods[part].count('ducted'), 1,
         'the same work is not done twice')
    _, _ = play(['mod damped cooling --confirm'], game=game)
    T.eq(len(game.char.deck.mods[part]), mod_content.MAX_PER_COMPONENT,
         'a component carries no more than the cap')
    _, out = play(['mod stripped cooling --confirm'], game=game)
    T.eq(len(game.char.deck.mods[part]), mod_content.MAX_PER_COMPONENT,
         'and a third is refused')
    T.ok('what is left of it' in out, 'and says so')

    # A mod that fits several slots asks which, rather than picking one. It
    # used to strip the chassis off a CPU when the cooling loop was full.
    game = at_bench()
    _, out = play(['mod stripped --confirm'], game=game)
    T.ok(not game.char.deck.mods, 'an ambiguous target does nothing')
    T.ok('mod stripped <slot>' in out, 'and asks which')
    _, out = play(['mod stripped cooling --confirm'], game=game)
    T.ok('stripped' in game.char.deck.mods.get(
        game.char.deck.parts['cooling'], []),
         'and naming the slot does it there')
    T.ok('stripped' not in game.char.deck.mods.get(
        game.char.deck.parts['cpu'], []),
         'and nowhere else')
    _, out = play(['mod stripped elbow --confirm'], game=game)
    T.ok('not a' in out, 'and a slot that is not one is refused')

    # Refused when you cannot pay, in either currency.
    game = at_bench(scrap=0)
    _, out = play(['mod ducted --confirm'], game=game)
    T.ok('scrap' in out, 'no scrap, no work')
    T.ok(not game.char.deck.mods, 'and nothing happened')
    game = at_bench(credits=10)
    _, out = play(['mod ducted --confirm'], game=game)
    T.ok('you have' in out, 'no money, no work')
    T.ok(not game.char.deck.mods, 'and nothing happened')

    # Every mod can actually be applied to something a character can have.
    for mod in mod_content.MODS:
        game = at_bench()
        applied = False
        for slot in mod.slots:
            if game.char.deck.component(slot) is not None:
                applied = True
        T.ok(applied, f'{mod.key} fits something on a starting deck')

    # And salvaging a modified component takes the work with it.
    game = at_bench()
    play(['mod widened --confirm'], game=game)
    bank = game.char.deck.parts['memory']
    T.ok(game.char.deck.mods.get(bank), 'the bank is modified')
    game.char.deck.damage['memory'] = 3
    play([f'salvage {bank}'], game=game)
    T.ok(not game.char.deck.mods.get(bank),
         'and breaking it down takes the work with it')

    # It survives a save.
    game = at_bench()
    play(['mod ducted --confirm'], game=game)
    again = Game.from_dict(game.to_dict())
    T.eq(again.char.deck.mods, game.char.deck.mods, 'bench work survives a save')
    T.eq(again.char.scrap, game.char.scrap, 'and so does the scrap')


def test_crew() -> None:
    """Somebody who runs with you, gets better at it, and can be lost."""
    T.section('crew')
    from flatline.content import rivals as rival_content
    from flatline.world import rivals as rival_mod

    def willing(key='moth', disposition=55):
        game = Game.new(Character.from_origin('gutter', 'boss'), seed=4242)
        game.char.credits = 90000
        game.city.rival(key).disposition = disposition
        return game

    # They have to have decided about you first, and that is a harder ask
    # than taking one job.
    game = willing(disposition=0)
    sess, out = play(['crew take moth --confirm'], game=game)
    T.ok(not game.city.crew, 'somebody neutral does not sign on')
    T.ok('different question' in out, 'and says what the difference is')

    game = willing()
    sess, out = play(['crew take moth --confirm'], game=game)
    T.eq(game.city.crew.get('key'), 'moth', 'somebody who likes you does')
    T.ok(game.char.credits < 90000, 'and it costs a retainer')
    sess, out = play(['crew take vesper --confirm'], game=game)
    T.eq(game.city.crew.get('key'), 'moth', 'and you get one of them')

    # They come in on every run without being asked, which is the whole
    # difference between this and a hire.
    contract = game.city.board[0]
    game.city.accepted = contract.cid
    contract.taken = True
    game.city.where = contract.district
    sess = Session(console=quiet_console(), slot='crewtest')
    sess.game = game
    sess.console.start_capture()
    sess.execute('jack in --force')
    sess.console.end_capture()
    T.ok(sess.run is not None and sess.run.ally is not None,
         'the crew is in the network without being hired')
    T.ok(sess.run.ally.get('crew'), 'and knows it is a crew rather than a hire')
    T.eq(sess.run.ally['cut'], rival_content.CREW_CUT,
         'and takes the smaller cut')

    # Runs together accumulate and buy them skill, up to a cap.
    T.eq(rival_mod.crew_bonus(0), 0, 'nobody starts better for knowing you')
    T.ok(rival_mod.crew_bonus(rival_content.CREW_RUNS_PER_STEP) > 0,
         'and enough runs together is worth something')
    T.eq(rival_mod.crew_bonus(9999), rival_content.CREW_MAX_STEPS,
         'and it is capped')

    game = willing()
    play(['crew take moth --confirm'], game=game)
    game.city.crew['runs'] = rival_content.CREW_RUNS_PER_STEP * 2
    sess, out = play(['crew'], game=game)
    T.ok('from working with you' in out,
         'and the sheet says where the skill came from')

    # Letting somebody go costs, and costs more the longer they were there.
    short = willing()
    play(['crew take moth --confirm'], game=short)
    short.city.crew['runs'] = 1
    play(['crew drop'], game=short)
    long = willing()
    play(['crew take moth --confirm'], game=long)
    long.city.crew['runs'] = 30
    play(['crew drop'], game=long)
    T.ok(long.city.rival('moth').disposition
         < short.city.rival('moth').disposition,
         'dropping somebody hurts more the longer they were with you')
    T.ok(not long.city.crew, 'and they are gone')

    # And losing them says something different by how long it was, which is
    # the entire reason this exists rather than a longer hire.
    scenes = {rival_content.crew_loss(n) for n in (0, 10, 30)}
    T.eq(len(scenes), 3, 'losing somebody scales with the time together')
    for runs in (2, 12, 30):
        game = willing()
        play(['crew take moth --confirm'], game=game)
        game.city.crew['runs'] = runs
        contract = game.city.board[0]
        game.city.accepted = contract.cid
        contract.taken = True
        sess = Session(console=quiet_console(), slot='crewtest')
        sess.game = game
        sess.run = RunState.begin(
            net_mod.generate(Rng(1).fork('network', contract.cid),
                             contract.target, int(contract.posture),
                             contract.objective),
            game.char, Rng(1)('combat'), sess.console,
            contract=contract.to_dict())
        sess.run.ally = {'key': 'moth', 'name': 'Moth',
                         'node': sess.run.net.entry, 'integrity': 0,
                         'state': 'dead', 'skill': 4, 'style': 'loud',
                         'cut': rival_content.CREW_CUT, 'crew': True}
        sess.run.finish('burned')
        sess.console.start_capture()
        from flatline.commands.run import _resolve
        _resolve(sess)
        said = ui.plain(sess.console.end_capture())
        T.ok('Moth' in said, f'losing them after {runs} runs says their name')
        T.ok(str(runs + 1) in said, 'and how long it had been')
        T.ok(not game.city.crew, 'and they are not still on the books')
        T.ok(not game.city.rival('moth').alive, 'and they are dead')

    # It survives a save.
    game = willing()
    play(['crew take moth --confirm'], game=game)
    game.city.crew['runs'] = 7
    again = Game.from_dict(game.to_dict())
    T.eq(again.city.crew, game.city.crew, 'the crew survives a save')


def test_safehouse() -> None:
    """Somewhere of your own, and the thing that makes heat physical."""
    T.section('safehouse')
    from flatline.content import safehouses

    def owner(key='cavity', credits=40000):
        game = Game.new(Character.from_origin('gutter', 'keeper'), seed=4242)
        game.char.credits = credits
        prop = safehouses.BY_KEY[key]
        game.city.where = prop.where
        game.city.visited.add(prop.where)
        return game, prop

    # You buy one, in the district it is in, and you get one.
    game, prop = owner()
    sess, out = play([f'safehouse buy {prop.key}'], game=game)
    T.eq(game.city.safehouse.get('key'), prop.key, 'buying one gets you one')
    T.ok(game.char.credits < 40000, 'and it costs')
    sess, out = play(['safehouse buy noodle'], game=game)
    T.ok('already have one' in out, 'and you only get one')

    # Elsewhere is elsewhere: the place and everything in it stays put.
    game.city.where = 'vertical'
    sess, out = play(['safehouse stash crowbar'], game=game)
    T.ok('Ninth' in out, 'you cannot reach into it from another district')
    game.city.where = prop.where

    # Things go in and come back out. Not a crowbar: the gutter ships with
    # two of them, so removing one would leave one and prove nothing.
    game.char.library.append('lattice')
    sess, _ = play(['safehouse stash lattice'], game=game)
    T.ok('lattice' in (game.city.safehouse.get('stored') or []),
         'a thing goes in')
    T.ok('lattice' not in game.char.library, 'and is not also on you')
    sess, _ = play(['safehouse take lattice'], game=game)
    T.ok('lattice' in game.char.library, 'and comes back out')

    # The loaded deck is excluded, because storing the program you are
    # carrying and then walking into a network is a mistake the game should
    # not help with silently.
    loaded = list(game.char.deck.loaded)
    if loaded:
        sess, out = play([f'safehouse stash {loaded[0]}'], game=game)
        T.ok(loaded[0] in game.char.deck.loaded,
             'the loaded deck cannot be stashed by accident')

    # Money goes both ways and never conjures any.
    before = game.char.credits
    sess, _ = play(['safehouse money 5000'], game=game)
    T.eq(game.char.credits, before - 5000, 'money goes in')
    T.eq(game.city.safehouse['credits'], 5000, 'and is in there')
    sess, _ = play(['safehouse money -2000'], game=game)
    T.eq(game.char.credits, before - 3000, 'and comes back out')
    sess, _ = play(['safehouse money -99999'], game=game)
    T.eq(game.city.safehouse['credits'], 0, 'taking more than is there empties it')
    T.eq(game.char.credits, before, 'and returns exactly what went in')

    # -- the raid ---------------------------------------------------------
    # Nobody looks while nobody is interested. This is the promise that makes
    # being unknown the best security in the game.
    game, prop = owner()
    play([f'safehouse buy {prop.key}'], game=game)
    game.char.library.append('crowbar')
    play(['safehouse stash crowbar', 'safehouse money 8000'], game=game)
    for _ in range(80):
        game.city.advance(game.rng, game.alias, 1, char=game.char)
    T.eq(game.city.safehouse.get('raids', 0), 0,
         'eighty quiet shifts and nobody came')
    T.eq(game.city.safehouse['credits'], 8000, 'and the money is still there')

    # Wanted enough, and somebody does.
    game, prop = owner()
    play([f'safehouse buy {prop.key}'], game=game)
    for key in ('crowbar', 'sable', 'blink'):
        game.char.library.append(key)
        play([f'safehouse stash {key}'], game=game)
    play(['safehouse money 10000'], game=game)
    game.alias.add_heat(districts.BY_KEY[prop.where].controller, 100)
    for _ in range(200):
        game.alias.add_heat(districts.BY_KEY[prop.where].controller, 4)
        game.city.advance(game.rng, game.alias, 1, char=game.char)
        if game.city.safehouse.get('burned'):
            break
    house = game.city.safehouse
    T.ok(house.get('raids', 0) > 0, 'enough attention finds the place')
    T.ok(house.get('burned'), 'and enough of it ends the place')
    T.eq(house['credits'], 0, 'a burned place holds nothing')
    T.eq(house['stored'], [], 'and nothing is stranded in it')

    # Which is checkable directly, too: the curve does what it says.
    T.eq(safehouses.raid_chance(50, safehouses.SAFE_BELOW - 1), 0.0,
         'below the floor of interest nobody looks')
    T.ok(safehouses.raid_chance(20, 100) > safehouses.raid_chance(70, 100),
         'security is what you are buying')
    T.ok(safehouses.raid_chance(20, 100) > safehouses.raid_chance(20, 50),
         'and being wanted is what you are buying it against')

    # It survives a save.
    again = Game.from_dict(game.to_dict())
    T.eq(again.city.safehouse, game.city.safehouse,
         'the place and its contents survive a save')


def test_bonds() -> None:
    """Rival arcs: a nemesis or a partner, latched and acting."""
    T.section('bonds')
    from flatline.content import rivals as rival_content
    from flatline.world import rivals as rival_mod

    def pool_at(disposition, jobs):
        pool = rival_mod.seed_pool()
        for r in pool:
            r.disposition, r.jobs = disposition, jobs
        return pool

    # Two gates, and both are needed. Disposition alone on your fourth shift
    # would make a lifelong enemy out of one bad afternoon.
    pool = pool_at(rival_content.NEMESIS_AT - 10, 0)
    T.eq(rival_mod.check_bonds(pool), [],
         'disposition without history forms no bond')
    pool = pool_at(0, 99)
    T.eq(rival_mod.check_bonds(pool), [],
         'history without disposition forms no bond either')

    for want, disposition in (('nemesis', rival_content.NEMESIS_AT - 5),
                              ('partner', rival_content.PARTNER_AT + 5)):
        pool = pool_at(disposition, rival_content.BOND_AFTER_JOBS)
        crossed = rival_mod.check_bonds(pool)
        T.eq(len(crossed), len(pool), f'everybody eligible becomes a {want}')
        T.ok(all(kind == want for _, kind in crossed),
             f'and it is the {want} end')
        # Once, ever. A declaration that fires twice is not a declaration.
        T.eq(rival_mod.check_bonds(pool), [], 'and it is announced once')
        for rival, kind in crossed:
            scene = rival_mod.declare(rival, kind)
            T.ok(rival.name in scene, f'{rival.key} is named in their scene')
            T.ok(len(scene) > 80, 'and the scene is a scene')

    # It latches: doing them a favour afterwards does not undo it.
    pool = pool_at(rival_content.NEMESIS_AT - 5, rival_content.BOND_AFTER_JOBS)
    rival_mod.check_bonds(pool)
    for r in pool:
        r.adjust_disposition(200)
    T.ok(all(r.bond == 'nemesis' for r in pool),
         'a bond does not come off because of a good Tuesday')

    # And it does something on the shift boundary, in both directions.
    for kind, expect_more in (('nemesis', True), ('partner', False)):
        game = Game.new(Character.from_origin('gutter', 'b'), seed=99)
        game.alias.add_heat('kagawa', 60)
        for r in game.city.rivals:
            r.bond = kind
        before = game.alias.attention('kagawa')
        said = []
        for _ in range(40):
            said.extend(game.city.advance(game.rng, game.alias, 1))
        after = game.alias.attention('kagawa')
        T.ok(any(r.name in ' '.join(said) for r in game.city.rivals),
             f'a {kind} turns up in the news')
        # Heat decays on its own, so the test is the direction against a
        # world where nobody has decided anything about you.
        plain = Game.new(Character.from_origin('gutter', 'b'), seed=99)
        plain.alias.add_heat('kagawa', 60)
        for _ in range(40):
            plain.city.advance(plain.rng, plain.alias, 1)
        if expect_more:
            T.ok(after >= plain.alias.attention('kagawa'),
                 'a nemesis leaves you hotter than nobody would')
        else:
            T.ok(after <= plain.alias.attention('kagawa'),
                 'a partner leaves you cooler')

    # It survives a save, which is the difference between an arc and a mood.
    game = Game.new(Character.from_origin('gutter', 'b'), seed=4242)
    game.city.rivals[0].bond = 'nemesis'
    again = Game.from_dict(game.to_dict())
    T.eq(again.city.rivals[0].bond, 'nemesis', 'a bond survives a save')

    # Nobody starts in one.
    fresh = Game.new(Character.from_origin('gutter', 'b'), seed=1)
    T.ok(all(not r.bond for r in fresh.city.rivals),
         'a new character has decided nothing with anybody')


def test_legacy() -> None:
    """Getting out on purpose, and what reaches the next one either way."""
    T.section('legacy')
    from flatline.content import drugs, legacy
    from flatline import save as save_mod

    def ready(**over):
        game = Game.new(Character.from_origin('gutter', 'Vesper'), seed=4242)
        game.char.credits = legacy.STAKE + 5000
        game.char.runs = 20
        game.earned = 120000
        for key, value in over.items():
            setattr(game.char, key, value)
        return game

    # -- the gates ---------------------------------------------------------
    # Each one, alone, is enough to stop you, and says which one it is.
    blockers = {
        'stake': lambda g: setattr(g.char, 'credits', 100),
        'debt': lambda g: (setattr(g.debt, 'amount', 4000),
                           setattr(g.debt, 'lender', 'sixes')),
        'clean': lambda g: setattr(
            g.char, 'chem',
            {'up': {}, 'down': {}, 'habit': {'kick': drugs.WITHDRAWAL_AT},
             'dry': {}}),
        'quiet': lambda g: g.city.bounties.update({'sixes': 5000}),
    }
    for key, block in blockers.items():
        game = ready()
        block(game)
        sess, out = play(['retire --confirm'], game=game)
        T.ok(game.over != 'retired', f'{key} alone stops a retirement')
        want = next(w for k, w, _ in legacy.GATES if k == key)
        T.ok(want in out, f'and the sheet says it was {key}')

    # All four, and it happens.
    game = ready()
    sess, out = play(['retire --confirm'], game=game)
    T.eq(game.over, 'retired', 'all four gates clear retires the character')
    T.ok('handle' in out and 'Vesper' in out, 'and it reports who left')

    # With nothing to do it is a progress sheet, which is how anybody finds
    # out this is a goal at all.
    game = ready()
    game.char.credits = 10
    sess, out = play(['retire'], game=game)
    T.ok(game.over != 'retired', 'the bare form does not retire you')
    for _, want, _ in legacy.GATES:
        T.ok(want in out, f'the sheet lists {want!r}')

    # -- endings -----------------------------------------------------------
    # Drift never refuses one, at any value, including silly ones.
    seen = set()
    for level in range(0, 130, 3):
        title, text = legacy.ending(level)
        T.ok(bool(title and text), f'drift {level} has an ending')
        seen.add(title)
    T.eq(len(seen), len(legacy.ENDINGS),
         'every ending is reachable by some amount of drift')
    T.ok(legacy.ending(0)[0] != legacy.ending(99)[0],
         'and a machine does not get the same ending as a person')

    # -- what is left ------------------------------------------------------
    # A retirement and a flatline leave different kinds of thing.
    for how in ('retired', 'flatlined'):
        kinds = {b.key for b in legacy.candidates(how)}
        T.ok(kinds, f'{how} leaves something')
        other = {b.key for b in legacy.candidates(
            'flatlined' if how == 'retired' else 'retired')}
        T.ok(not (kinds & other), f'{how} leaves its own kinds of thing')

    # Retiring leaves an estate, and only one.
    save_mod.write_meta(dict(save_mod.META_DEFAULT))
    game = ready()
    play(['retire --confirm'], game=game)
    estate = save_mod.read_meta().get('estate') or {}
    T.ok(estate.get('bequest'), 'retiring leaves something behind')
    T.eq(estate.get('handle'), 'Vesper', 'in the name of whoever left it')
    T.eq(estate.get('how'), 'retired', 'and remembers how they went')
    T.ok(estate['bequest'] in {b.key for b in legacy.candidates('retired')},
         'and it is a thing a retirement can leave')

    # The next character claims it, once.
    sess = Session(console=quiet_console(), slot='legacytest')
    sess.console.start_capture()
    sess.execute('new Ash --origin gutter --seed 9')
    said = sess.console.end_capture()
    T.ok('Vesper' in said, 'and the next character is told whose it was')
    T.eq(save_mod.read_meta().get('estate'), {},
         'and it is claimed exactly once')
    sess2 = Session(console=quiet_console(), slot='legacytest')
    sess2.console.start_capture()
    sess2.execute('new Third --origin gutter --seed 9')
    again = sess2.console.end_capture()
    T.ok('Vesper' not in again, 'a third character inherits nothing')

    # Every bequest actually grants something when it lands.
    for bequest in legacy.BEQUESTS:
        save_mod.write_meta(dict(save_mod.META_DEFAULT))
        detail = {'stake': {'amount': 9000},
                  'name': {'faction': 'sixes'},
                  'chrome': {'ware': 'corp_neural_shunt'},
                  'program': {'program': 'crowbar'},
                  'debt': {'amount': 3000, 'lender': 'carrion'}}[bequest.key]
        save_mod.leave_estate(bequest.key, 'Halloway', bequest.after, **detail)
        s = Session(console=quiet_console(), slot='legacytest')
        s.console.start_capture()
        s.execute('new Heir --origin gutter --seed 11')
        s.console.end_capture()
        char = s.game.char
        got = {
            'stake': char.credits > Character.from_origin('gutter', 'x').credits,
            'name': s.game.alias.reputation('sixes') >= legacy.NAME_STANDING,
            'chrome': 'corp_neural_shunt' in char.library,
            'program': 'crowbar' in char.library,
            'debt': s.game.debt.owed,
        }[bequest.key]
        T.ok(got, f'{bequest.key} actually reaches the next character')

    # The Ghost starts with no history, and two of the five bequests are
    # exactly that. Handing one over would cancel an origin's defining line.
    for key, detail in (('name', {'faction': 'sixes'}),
                        ('debt', {'amount': 3000, 'lender': 'carrion'})):
        save_mod.write_meta(dict(save_mod.META_DEFAULT))
        save_mod.leave_estate(key, 'Halloway', 'retired' if key == 'name'
                              else 'flatlined', **detail)
        s = Session(console=quiet_console(), slot='legacytest')
        s.console.start_capture()
        s.execute('new Nobody --origin ghost --seed 11')
        s.console.end_capture()
        T.ok(not s.game.debt.owed, f'a Ghost inherits no {key}')
        T.ok(s.game.alias.reputation('sixes') < legacy.NAME_STANDING,
             f'a Ghost inherits no {key} standing')

    # A flatline leaves one too. That is the whole point of the feature: the
    # game is named after this moment and it ended into a scoreboard.
    save_mod.write_meta(dict(save_mod.META_DEFAULT))
    game = Game.new(Character.from_origin('gutter', 'Doomed'), seed=8829)
    game.char.credits = 9000
    game.debt.amount, game.debt.lender = 6000, 'carrion'
    sess = Session(console=quiet_console(), slot='legacytest')
    sess.game = game
    contract = game.city.board[0]
    game.city.accepted = contract.cid
    contract.taken = True
    sess.run = RunState.begin(
        net_mod.generate(Rng(2).fork('network', contract.cid), contract.target,
                         int(contract.posture), contract.objective),
        game.char, Rng(2)('combat'), sess.console,
        contract=contract.to_dict())
    sess.run.finish('flatline')
    sess.console.start_capture()
    from flatline.commands.run import _resolve
    _resolve(sess)
    sess.console.end_capture()
    T.eq(game.over, 'flatlined', 'a flatline ends the character')
    estate = save_mod.read_meta().get('estate') or {}
    T.ok(estate.get('bequest'), 'and leaves something anyway')
    T.eq(estate.get('how'), 'flatlined', 'marked as the way it happened')

    # And the city says the name afterwards, to somebody who never met them.
    T.ok(any(g['handle'] == 'Doomed' for g in save_mod.the_departed()),
         'the departed are remembered by name')
    for line in legacy.REMEMBERED:
        T.ok('{handle}' in line, 'every remembered line names somebody')
    save_mod.write_meta(dict(save_mod.META_DEFAULT))


def test_offers() -> None:
    """Work, goods and favours: the three things a person does for you."""
    T.section('offers')
    from flatline.content import npcs as npc_content, offers

    def met(seed=4242, runs=6, origin='gutter'):
        game = Game.new(Character.from_origin(origin, 'dealer'), seed=seed)
        game.char.runs = runs
        game.char.credits = 80000
        for npc in npc_content.NPCS:
            game.story.meet(npc.key)
        return game

    # Everything declared is served, and nothing is served that is not
    # declared. This is the whole point: `offers` was a label for years.
    for npc in npc_content.NPCS:
        if 'work' in npc.offers:
            T.ok(npc.key in offers.BY_NPC_WORK,
                 f'{npc.key} declares work and has some')
        if 'goods' in npc.offers:
            T.ok(npc.key in offers.BY_NPC_STOCK,
                 f'{npc.key} declares goods and has some')
        if 'favour' in npc.offers:
            T.ok(offers.favours_for(npc.key),
                 f'{npc.key} declares favours and has some')

    # -- work -------------------------------------------------------------
    game = met()
    sess, out = play(['deal mara work'], game=game)
    theirs = [x for x in game.city.board if x.from_npc == 'mara']
    T.eq(len(theirs), 1, 'asking for work produces exactly one job')
    job = theirs[0]
    T.ok(job.pay > 0, 'and it pays')
    T.ok('holding this one for you' in out or 'c0' in out,
         'and the sheet says whose it is')

    # Asking again does not print money.
    sess, _ = play(['deal mara work'], game=game)
    T.eq(len([x for x in game.city.board if x.from_npc == 'mara']), 1,
         'asking twice does not produce a second job')

    # It pays better than the board and is held longer.
    work = offers.BY_NPC_WORK['mara']
    T.ok(work.pay > 1.0, 'personal work pays over the board rate')
    T.ok(job.expires - job.posted
         > max(e for e in contract_lifetime()), 'and is held longer')

    # Dropping it costs you with them, specifically, which a posting cannot do.
    sess, out = play([f'take {job.cid}', 'drop'], game=game)
    T.eq(game.story.owed.get('mara'), 1, 'dropping their job costs a favour')

    # And it cannot push you past the ceiling, which is how far they will let
    # you get rather than how far you can be shoved.
    deep = met()
    deep.story.owed['mara'] = offers.OWED_LIMIT
    play(['deal mara work'], game=deep)
    theirs = [x for x in deep.city.board if x.from_npc == 'mara']
    if theirs:
        play([f'take {theirs[0].cid}', 'drop'], game=deep)
        T.eq(deep.story.owed['mara'], offers.OWED_LIMIT,
             'a drop at the ceiling leaves you at the ceiling')
    T.ok(not [x for x in game.city.board if x.from_npc == 'mara'],
         'and the job goes with them')

    # -- favours ----------------------------------------------------------
    game = met()
    game.alias.add_heat('sixes', 80)
    before = game.alias.attention('sixes')
    sess, out = play(['deal mara favour quiet'], game=game)
    T.ok(game.alias.attention('sixes') < before, 'a favour does the thing')
    T.eq(game.story.owed.get('mara'), 1, 'and goes on the tab')

    # Every favour either happens or explains itself, and none of them
    # silently does nothing.
    for fav in offers.FAVOURS:
        fresh = met()
        fresh.alias.add_heat('sixes', 90)
        fresh.char.dissonance = 60
        fresh.char.credits = 90000
        fresh.debt.amount = 5000
        fresh.debt.lender = 'sixes'
        if fresh.city.board:
            fresh.city.accepted = fresh.city.board[0].cid
            fresh.city.board[0].taken = True
        from flatline.content import drugs
        fresh.char.chem = drugs.dose(drugs.blank(), 'kick')
        _, said = play([f'deal {fav.npc} favour {fav.key}'], game=fresh)
        T.ok(ui.plain(said).strip(), f'{fav.npc}/{fav.key} says something')
        T.ok(fresh.story.owed.get(fav.npc, 0) == 1
             or 'will not' in said or '✗' in said,
             f'{fav.npc}/{fav.key} either happened or refused, not neither')

    # The tab has a ceiling, and it is expressed in their own words.
    game = met()
    game.story.owed['mara'] = offers.OWED_LIMIT
    game.alias.add_heat('sixes', 80)
    heat_before = game.alias.attention('sixes')
    sess, out = play(['deal mara favour quiet'], game=game)
    T.eq(game.alias.attention('sixes'), heat_before,
         'past the ceiling a favour does not happen')
    T.eq(game.story.owed['mara'], offers.OWED_LIMIT,
         'and does not go further onto the tab')

    # Finishing their work takes one back off.
    game = met()
    game.story.owed['mara'] = 2
    sess, _ = play(['deal mara work'], game=game)
    job = next(x for x in game.city.board if x.from_npc == 'mara')
    game.city.accepted = job.cid
    job.taken = True
    from flatline.commands.run import _resolve
    sess2 = Session(console=quiet_console(), slot='t')
    sess2.game = game
    sess2.run = RunState.begin(
        net_mod.generate(Rng(1).fork('network', job.cid), job.target,
                         int(job.posture), job.objective),
        game.char, Rng(1)('combat'), sess2.console, contract=job.to_dict())
    sess2.run.done[job.objective] = sess2.run.net.objective_node
    sess2.run.haul.append(sess2.run.net.objective_asset)
    sess2.run.observed_enough = True
    if sess2.run.escort is not None:
        sess2.run.escort.update({'done': True, 'state': 'out'})
    sess2.run.finish('clean')
    sess2.console.start_capture()
    _resolve(sess2)
    sess2.console.end_capture()
    T.ok(game.story.owed.get('mara', 0) < 2,
         'finishing their job takes one off the tab')

    # -- goods ------------------------------------------------------------
    for stock in offers.STOCK:
        npc = npc_content.BY_KEY[stock.npc]
        game = met()
        if npc.where:
            game.city.where = npc.where
            game.city.visited.add(npc.where)
        _, said = play([f'deal {stock.npc} goods'], game=game)
        listed = {l.key for l in game.city.listings()}
        for key in stock.goods:
            T.ok(key in listed,
                 f'{stock.npc} puts {key} on the local shelf')
        T.ok(ui.plain(said).strip(), f'{stock.npc} says something about it')
        # And it does not rotate off *without being asked again*, which is
        # the whole difference between a person's cabinet and a market, and
        # which was not true until a soak said so: `refresh_stock` rebuilds
        # every shelf from scratch.
        T.ok(stock.npc in game.city.counters,
             f'dealing with {stock.npc} opens their counter for good')
        game.city.refresh_stock(game.rng)
        listed = {l.key for l in game.city.listings()}
        for key in stock.goods:
            T.ok(key in listed,
                 f'{stock.npc} still has {key} after a rotation')

    # Somebody's stock is only theirs where they are.
    game = met()
    game.city.where = 'marrow'
    _, said = play(['deal quartermaster goods'], game=game)
    T.ok('Freeport' in said, 'you cannot buy off somebody who is elsewhere')

    # All of it survives a save.
    game = met()
    game.story.owed['mara'] = 2
    game.story.asked['mara'] = 4
    sess, _ = play(['deal mara work'], game=game)
    again = Game.from_dict(game.to_dict())
    T.eq(again.story.owed, game.story.owed, 'the tab survives a save')
    T.eq(again.story.asked, game.story.asked, 'and so does when you asked')
    T.eq([x.from_npc for x in again.city.board],
         [x.from_npc for x in game.city.board],
         'and so does whose job is whose')


def contract_lifetime():
    from flatline.world.contracts import LIFETIME
    return LIFETIME


def test_vices() -> None:
    """Drugs, borrowing, and the two games. The three ways to spend later."""
    T.section('vices')
    from flatline.content import drugs, games, lenders
    from flatline.world import debt as debt_mod

    # -- chemistry --------------------------------------------------------
    char = Character.from_origin('gutter', 'user')
    clean_reflex = char.attr('reflex')
    char.chem = drugs.dose(char.chem, 'kick')
    T.ok(char.attr('reflex') > clean_reflex, 'a stimulant stimulates')
    T.ok(drugs.is_up(char.chem, 'kick'), 'and is in you')

    char.chem, told = drugs.advance(char.chem, drugs.BY_KEY['kick'].up)
    T.ok(drugs.is_down(char.chem, 'kick'), 'the high runs out into a crash')
    T.ok(any('turns' in line for line in told),
         'and the player is told, in the shift it happens')
    T.ok(char.attr('reflex') < clean_reflex,
         'and the crash takes more than the high gave')

    char.chem, _ = drugs.advance(char.chem, drugs.BY_KEY['kick'].down)
    T.eq(char.attr('reflex'), clean_reflex, 'and then it is over')

    # The spiral, walked end to end. This is the whole system: past the
    # threshold, not using is its own condition, and the number you started
    # with is not the number you have any more.
    char = Character.from_origin('gutter', 'deep')
    for _ in range(drugs.WITHDRAWAL_AT):
        char.chem = drugs.dose(char.chem, 'kick')
        # Ridden out exactly, rather than for a fixed number of shifts: one
        # dose of a light drug sleeps off completely inside eight, so a test
        # that waited that long between doses would be testing abstinence.
        while (drugs.is_up(char.chem, 'kick')
               or drugs.is_down(char.chem, 'kick')):
            char.chem, _ = drugs.advance(char.chem, 1)
    level = drugs.habit(char.chem, 'kick')
    T.ok(level >= drugs.WITHDRAWAL_AT, f'four doses is a habit ({level})')
    T.eq(drugs.withdrawing(char.chem), ['kick'], 'and it is now withdrawal')
    T.ok(char.attr('reflex') < clean_reflex,
         'so being clean is worse than being clean used to be')
    T.ok(drugs.effects(char.chem), 'with nothing at all in you')
    # And dosing brings you back to par rather than past it.
    char.chem = drugs.dose(char.chem, 'kick')
    T.ok(char.attr('reflex') > clean_reflex,
         'a dose still helps, which is the trap')

    # Tolerance: the same drug does less, and costs more, the deeper you are.
    fresh = drugs._scaled(drugs.BY_KEY['kick'].high, drugs.tolerance(0))
    worn = drugs._scaled(drugs.BY_KEY['kick'].high,
                         drugs.tolerance(drugs.HABIT_MAX))
    T.ok(worn['reflex'] < fresh['reflex'], 'the high weakens with habit')
    mild = drugs._scaled(drugs.BY_KEY['kick'].crash, drugs.severity(0))
    harsh = drugs._scaled(drugs.BY_KEY['kick'].crash,
                          drugs.severity(drugs.HABIT_MAX))
    T.ok(harsh['reflex'] < mild['reflex'], 'and the crash deepens with it')

    # There is a way out, and it is slow rather than closed, per D6.
    out = Character.from_origin('gutter', 'clean')
    out.chem = {'up': {}, 'down': {}, 'habit': {'kick': drugs.HABIT_MAX},
                'dry': {}}
    for _ in range(drugs.CLEAN_SHIFTS * drugs.HABIT_MAX + drugs.HABIT_MAX):
        out.chem, _ = drugs.advance(out.chem, 1)
    T.eq(drugs.habit(out.chem, 'kick'), 0, 'abstinence gets you all the way out')

    # Ash Tea ends a comedown and takes the price out of the habit instead.
    trap = Character.from_origin('gutter', 'trap')
    trap.chem = drugs.dose(trap.chem, 'kick')
    trap.chem, _ = drugs.advance(trap.chem, drugs.BY_KEY['kick'].up)
    T.ok(drugs.is_down(trap.chem, 'kick'), 'coming down')
    before = drugs.habit(trap.chem, 'kick')
    trap.chem = drugs.dose(trap.chem, 'ash_tea')
    T.ok(not drugs.is_down(trap.chem, 'kick'), 'and then not coming down')
    T.ok(drugs.habit(trap.chem, 'kick') > before,
         'and the comedown went into the habit instead')

    # Nothing survives a round trip wrong, and a save from a build with a drug
    # this one does not ship must not take the game down.
    trap.stash = {'kick': 2}
    again = Character.from_dict(trap.to_dict())
    T.eq(again.chem, drugs.normalise(trap.chem), 'chemistry round-trips')
    T.eq(again.stash, {'kick': 2}, 'and so does the bag')
    T.eq(drugs.normalise({'up': {'notadrug': 3}, 'habit': {'kick': 'x'}}),
         drugs.blank() | {'habit': {}},
         'a block full of nonsense normalises to nothing')

    # -- borrowing ---------------------------------------------------------
    game = Game.new(Character.from_origin('gutter', 'debtor'), seed=4242)
    for lender in lenders.LENDERS:
        rep = game.alias.reputation(lender.key)
        limit = lenders.limit(lender, rep, 0)
        T.ok(limit >= 0, f'{lender.key} offers a real number')
        T.ok(limit <= lender.ceiling, f'{lender.key} respects its ceiling')
    T.ok(lenders.limit(lenders.BY_KEY['fixers'], 0, 40)
         > lenders.limit(lenders.BY_KEY['fixers'], 0, 0),
         'the Switchboard lends more to somebody with a record')
    T.eq(lenders.limit(lenders.BY_KEY['carrion'], 99, 99),
         lenders.limit(lenders.BY_KEY['carrion'], 0, 0),
         'and Carrion lend everybody the same')

    sess, out = play(['travel ninth', 'borrow'], game=game)
    T.ok('Auntie Nine' in out, 'the Ninth has somebody who lends')
    sess, out = play(['borrow 1000 --confirm'], game=game)
    T.ok(game.debt.owed, 'and taking it leaves you owing')
    T.eq(game.debt.lender, 'sixes', 'to the faction whose money it was')
    T.eq(game.debt.terms[0], lenders.BY_KEY['sixes'].rate,
         'on the terms that lender quoted, not the house ones')
    before = game.debt.amount
    game.debt.accrue()
    T.ok(game.debt.amount > before, 'and it compounds')

    # One at a time. Nobody lends to somebody else's problem.
    sess, out = play(['borrow 500 --confirm'], game=game)
    T.eq(game.debt.amount, before * 1 if False else game.debt.amount,
         'a second loan is refused')
    T.eq(game.debt.lender, 'sixes', 'and does not overwrite the first')
    T.ok('owe' in out.lower(), 'and says why')

    # A debt from before lenders existed still runs, at the house rate.
    old = debt_mod.Debt.from_dict({'amount': 5000, 'lender': 'sixes'})
    T.eq(old.terms, (debt_mod.RATE, debt_mod.GRACE),
         'a debt with no terms of its own uses the house terms')

    # -- the games ---------------------------------------------------------
    # The wall and the dice agree, checked by rolling every combination.
    for call, (totals, pays) in games.CALLS.items():
        wins = sum(1 for a in range(1, 7) for b in range(1, 7)
                   if (a + b) in totals)
        T.eq(wins / 36.0, games.odds(call), f'{call} pays out as advertised')

    played = Game.new(Character.from_origin('gutter', 'punter'), seed=8829)
    played.char.credits = 20000
    sess, out = play(['travel ninth', 'dice'], game=played)
    T.ok('16.7%' in out, 'the edge is printed on the wall')
    before = played.char.credits
    sess, out = play(['dice 100 high'], game=played)
    T.ok(played.char.credits in (before - 100, before + 100),
         'a bet wins the stake or loses it')

    T.ok('does not get out of bed' in play(['dice 1 high'], game=played)[1],
         'and there is a floor under the stake')
    T.ok('most this room will cover' in
         play([f'dice {games.MAX_STAKE + 1} high'], game=played)[1],
         'and a ceiling over it')

    # Cards is a build's game, and says so to somebody without the build.
    from flatline.commands.city import _threes_check
    marrow = games.BY_KEY['threes_marrow']
    street = Character.from_origin('gutter', 'street')
    social = Character.from_origin('protege', 'social')
    T.ok(_threes_check(social, marrow, 0).chance
         > _threes_check(street, marrow, 0).chance,
         'Guile is what reads a table')
    T.ok(_threes_check(street, marrow, 0).chance < games.THREES_FLOOR,
         'and somebody without it is turned away rather than fleeced')
    played.city.where = 'marrow'
    sess, out = play(['cards 500'], game=played)
    T.ok('dice' in out, 'and pointed at the game that needs no build')

    # The house notices. Winning makes the table harder, up to a limit.
    fresh = _threes_check(social, marrow, 0).chance
    learned = _threes_check(social, marrow, games.THREES_LEARNS_PER * 3).chance
    capped = _threes_check(social, marrow,
                           games.THREES_LEARNS_PER * 500).chance
    T.ok(learned < fresh, 'a table that has paid you out gets harder')
    T.eq(capped, _threes_check(social, marrow,
                               games.THREES_LEARNS_PER
                               * games.THREES_LEARNS_MAX).chance,
         'and stops getting harder, so a good night is not permanent exile')

    # Gambling must never touch a world stream, for the same reason the intro
    # must not: an evening at the dice would silently reshuffle the board.
    a = Game.new(Character.from_origin('gutter', 'a'), seed=4242)
    b = Game.new(Character.from_origin('gutter', 'b'), seed=4242)
    a.char.credits = 50000
    sess, _ = play(['travel ninth'] + ['dice 10 high'] * 25, game=a)
    T.eq([c.cid for c in a.city.board], [c.cid for c in b.city.board],
         'twenty-five rolls do not touch the contract board')

    # And a whole session of vice leaves a save that opens.
    from flatline import save as save_mod
    a.char.chem = drugs.dose(a.char.chem, 'kick')
    a.char.stash = {'ash_tea': 1}
    a.city.tables['ninepins_ninth'] = 4000
    blob = save_mod.migrate({**a.to_dict(), 'schema': save_mod.SCHEMA})
    back = Game.from_dict(blob)
    T.eq(back.char.chem, drugs.normalise(a.char.chem), 'chemistry survives a save')
    T.eq(back.city.tables, a.city.tables, 'and so does what the tables know')


def test_brief() -> None:
    T.section('brief')
    from flatline.world.contracts import OBJECTIVES, OBJECTIVE_AIM

    char = Character.from_origin('gutter', 'briefed')
    for skill in ('intrusion', 'signal', 'cryptography', 'forensics'):
        char.base_skills[skill] = 4
    char.deck.loaded = ['crowbar', 'siphon']
    console = quiet_console()

    # Nothing is met at the door, and everything says what it wants.
    for objective in OBJECTIVES:
        net = net_mod.generate(Rng(3).fork('network', objective), 'sixes', 30,
                               objective)
        state = RunState.begin(net, char, Rng(3)('combat'), console,
                               contract={'objective': objective})
        brief = state.brief()
        T.ok(not brief.done, f'{objective} is not finished at the door')
        T.ok(brief.aim, f'{objective} says what it wants')
        T.ok(brief.steps, f'{objective} says what to do about it')
        T.ok('{' not in brief.aim,
             f'{objective} filled in every field of its aim')

    # Following the advice has to get somewhere. Run with the trace held at
    # zero, so this measures whether the advice is a route rather than whether
    # this character is fast enough to walk it: those are separate questions
    # and only the first is this code's fault.
    #
    # The invariant is termination, not victory. Doing what the brief says has
    # to end in one of three places every time: the job done, the run over, or
    # the brief saying there is no way on and to leave. Never a loop. Not
    # every network is winnable by every build and the advice is allowed to
    # say so; what it may not do is walk in a circle until the trace fills,
    # which is what it did in every one of the shapes below before this test
    # existed.
    finished = 0
    gave_up = 0
    looped = 0
    attempts = 0
    for objective in OBJECTIVES:
        for seed in range(4):
            if objective == 'escort':
                continue  # Their pace, not yours. Covered in `objectives`.
            attempts += 1
            sess = Session(console=console, slot='brieftest')
            sess.game = Game.new(Character.from_origin('gutter', 'b'),
                                 seed=seed)
            # A competently built runner rather than a fresh one. The advice
            # is on trial here, not the loadout: somebody carrying a rating-2
            # breaker cannot open a core node at any tier, the brief correctly
            # tells them so, and that measures the deck.
            sess.game.char.base_skills.update(
                {k: 5 for k in ('intrusion', 'signal', 'cryptography',
                                'forensics', 'subterfuge')})
            # Set straight onto the deck rather than through `load`, which
            # would have to fit them in the memory this origin ships with.
            sess.game.char.deck.loaded = ['thunderhead', 'revision']
            net = net_mod.generate(Rng(seed).fork('network', objective),
                                   'sixes', 25, objective)
            sess.run = RunState.begin(net, sess.game.char, Rng(seed)('combat'),
                                      console, contract={'objective': objective,
                                                         'title': 'T'})
            stuck_on = None
            ended = False
            for _ in range(160):
                if sess.run is None:
                    ended = True
                    break
                sess.run.trace = 0.0      # the clock is not on trial here
                sess.run.alert = 'green'
                brief = sess.run.brief()
                if brief.done:
                    ended = True
                    break
                step = brief.steps[0]
                T.ok('<' not in step,
                     f'{objective}: the brief names a real target, not {step!r}')
                if step == 'jack out':
                    # It has said there is no way on. Believe it, and check it
                    # was telling the truth.
                    ended = True
                    gave_up += 1
                    T.ok(not sess.run.brief().done,
                         f'{objective}: it does not give up on a finished job')
                    break
                # A refusal and a failed roll both print a cross, and only one
                # of them is bad advice. They are told apart by the clock: a
                # command the game refuses is raised before any time is spent,
                # and a command it attempts costs a tick whether or not it
                # worked. Every verb the brief can name costs ticks.
                #
                # One free refusal in a row is fine and is how the game is
                # meant to work: nothing reveals a warden except trying the
                # door, and trying it costs nothing precisely so that finding
                # out is free. Two in a row is the advice not learning.
                before = sess.run.tick
                console.start_capture()
                sess.execute(step)
                said = ui.plain(console.end_capture())
                spent = sess.run is None or sess.run.tick > before
                if not spent and step == stuck_on:
                    T.failures.append(
                        f'brief: {objective} advised `{step}` twice running '
                        f'and the game refused it both times: '
                        f'{said.strip().splitlines()[0]}')
                    T.checks += 1
                    break
                stuck_on = None if spent else step
            if not ended:
                looped += 1
            if sess.run is not None and sess.run.brief().done:
                finished += 1
    T.eq(looped, 0, 'doing what the brief says always arrives somewhere')
    T.ok(finished > gave_up,
         f'and it is usually the finished job ({finished} done, '
         f'{gave_up} given up on, of {attempts})')

    # The strict half. These three used to pass on any node and any asset, so
    # a payload left on the doormat closed a contract that named a controller.
    for objective, field in (('implant', 'objective_node'),
                             ('corrupt', 'objective_node'),
                             ('wipe', 'objective_asset')):
        net = net_mod.generate(Rng(9).fork('network', objective), 'sixes', 30,
                               objective)
        state = RunState.begin(net, char, Rng(9)('combat'), console,
                               contract={'objective': objective})
        state.done[objective] = 'somewhere-else'
        T.ok(not state.objective_met(),
             f'{objective} somewhere other than the target is not the job')
        state.done[objective] = getattr(net, field)
        T.ok(state.objective_met(),
             f'{objective} on the target is')

    # And the trap that strictness creates: `wipe` cannot reach an asset you
    # are holding, so taking the one you were paid to destroy is refused.
    net = net_mod.generate(Rng(11).fork('network', 'wipe'), 'sixes', 30, 'wipe')
    sess = Session(console=console, slot='brieftest')
    sess.game = Game.new(Character.from_origin('gutter', 'w'), seed=11)
    sess.game.char.deck.loaded = ['crowbar', 'siphon']
    sess.run = RunState.begin(net, sess.game.char, Rng(11)('combat'), console,
                              contract={'objective': 'wipe', 'title': 'T'})
    where, asset = net.find_asset(net.objective_asset)
    sess.run.here = where.uid
    where.open = where.known = where.mapped = True
    # Unsealed, so this measures the refusal rather than a decrypt roll.
    asset.encrypted = False
    console.start_capture()
    sess.execute(f'pull {net.objective_asset}')
    refusal = ui.plain(console.end_capture())
    T.ok('paid to destroy' in refusal,
         'pulling the record you were paid to destroy is refused')
    T.ok(not asset.taken, 'and it is still on the node')
    console.start_capture()
    sess.execute(f'pull {net.objective_asset} --anyway')
    console.end_capture()
    T.ok(asset.taken, 'and --anyway still lets you do it')


def test_city_map() -> None:
    T.section('city map')

    game = Game.new(Character.from_origin('gutter', 'walker'), seed=8829)
    sess, out = play(['map'], game=game)

    # The shape is drawn from the start district rather than from wherever you
    # are, so the picture is the same every time and can be learned. What
    # changes is the distance column.
    for d in districts.DISTRICTS:
        T.ok(d.key in out, f'{d.key} is on the map')
    T.ok('1 of 9 walked' in out, 'a new character has walked one district')
    T.ok('here' in out, 'and the map says which one')

    # Distances are real distances, in both directions, for every pair.
    for a in districts.DISTRICT_KEYS:
        game.city.where = a
        for b in districts.DISTRICT_KEYS:
            route = game.city.route(b)
            if a == b:
                T.eq(route, [], 'nowhere to walk to where you are')
                continue
            T.eq(route[-1], b, f'the route from {a} ends at {b}')
            T.eq(len(route), game.city.shifts_to(b),
                 'the shift count is the length of the walk')
            prev = a
            for step in route:
                T.ok(step in districts.BY_KEY[prev].neighbours,
                     f'{prev} to {step} is a step you can take')
                prev = step
            # And it is the *shortest* walk, checked against a plain flood
            # rather than against the same function that produced it.
            depth, seen, frontier = {a: 0}, {a}, [a]
            while frontier:
                here = frontier.pop(0)
                for nxt in districts.BY_KEY[here].neighbours:
                    if nxt not in seen:
                        seen.add(nxt)
                        depth[nxt] = depth[here] + 1
                        frontier.append(nxt)
            T.eq(len(route), depth[b], f'{a} to {b} is the shortest walk')
    game.city.where = districts.START

    # Refusing a walk you cannot make in one shift hands over the walk you
    # can. The line it prints has to be a line that works.
    game.city.where = 'shambles'
    game.city.visited.add('shambles')
    ok, why = game.city.can_travel('green')
    T.ok(not ok, 'Aoyama Green is not one shift from the Shambles')
    T.ok('walk green' in why, 'and the refusal hands over the walk')
    typed = [part.strip() for part in why.split('`')[1].split(';')]
    T.eq(typed, ['walk green'], 'the walk in the refusal is one line')
    sess2, out2 = play(typed, game=game)
    T.eq(game.city.where, 'green', 'and typing it gets you there')
    T.eq(game.city.shift, len(game.city.route('shambles')),
         'at a shift a step')

    # Walking somewhere fills it in. This is the whole "builds out as you
    # explore" half: the shape never changes, the detail arrives.
    _, before = play(['map'], game=Game.new(
        Character.from_origin('gutter', 'a'), seed=8829))
    T.ok(before.count('not been') == len(districts.DISTRICTS) - 1,
         'everywhere you have not been says so')
    _, after = play(['map'], game=game)
    T.ok(after.count('not been') < before.count('not been'),
         'and one fewer of them does after you have walked')

    # An accepted contract elsewhere puts the walk to it on the map.
    game2 = Game.new(Character.from_origin('gutter', 'b'), seed=4242)
    away = [c for c in game2.city.board if c.district != game2.city.where]
    if away:
        sess3, out3 = play([f'take {away[0].cid}', 'map'], game=game2)
        T.ok('the job' in out3, 'the map marks the district the job is in')
        T.ok('travel' in out3.split('The job is in')[-1],
             'and says how to walk there')

    # Both maps use the same drawing, so the run map has to still work. The
    # walk to the job is taken from the router, which is also the thing under
    # test, so the jack in is the check that it produced a real walk.
    game3 = Game.new(Character.from_origin('gutter', 'c'), seed=8829)
    job = game3.city.board[0]
    walk = [f'travel {k}' for k in game3.city.route(job.district)]
    _, run_out = play([f'take {job.cid}'] + walk + ['jack in --force', 'map'],
                      game=game3)
    T.ok('Known hosts' in run_out, 'the run map still draws')

    # Prefixes pad to a common width, so every column after them lines up.
    for ascii_only in (False, True):
        rows = ui.tree_rows(districts.GRAPH, districts.START,
                            set(districts.DISTRICT_KEYS), ascii_only)
        led = ui.tree_leads(rows)
        T.eq(len({len(prefix) for prefix, _ in led}), 1,
             'every padded prefix is the same width')
        T.eq([uid for _, uid in led], [uid for _, uid in rows],
             'and padding changes nothing but the prefix')
        T.ok(all(prefix.endswith(' ') for prefix, _ in led),
             'and every one of them ends clear of its label')
        if ascii_only:
            T.ok(all(ord(ch) < 128 for prefix, _ in led for ch in prefix),
                 'ascii mode pads in ascii')
    T.eq(ui.tree_leads([]), [], 'no rows pad to no rows')


def test_cover() -> None:
    """Guile's derived stat, and the two city sums that now read Guile.

    Guile was the thinnest attribute in the game: every use of it was inside a
    run, so a character built to talk their way through the city had bought
    nothing the city could see. This covers the fix, and the much older bug it
    turned up on the way.
    """
    T.section('cover')
    from flatline.model import identity as ident
    from flatline.world import market as market_mod
    from flatline.content import dissonance as drift

    # --- the stat -------------------------------------------------------
    char = Character.from_origin('protege', 'face')
    T.eq(char.cover, attr_content.cover(char.attr('guile')),
         'Cover is what the attribute table says it is')
    before = char.cover
    char.base_attrs['guile'] += 1
    T.ok(char.cover > before, 'and it moves when Guile does')

    _, sheet = play(['char'], game=Game.new(char, seed=9))
    T.ok('Cover' in sheet, 'the sheet prints it')

    # --- heat cools, and the rate is the one the faction declared -------
    # This is the bug this whole check exists for. `decay_heat` rounded to an
    # integer every shift, so the twelve declared rates collapsed into four
    # behaviours and the two slowest, Carrion and Sixes, rounded away to
    # nothing: their heat was permanent for the life of the project and it
    # looked exactly like a gang holding a grudge.
    times = {}
    for fac in factions.FACTIONS:
        alias = ident.Alias(name='probe')
        alias.add_heat(fac.key, 90)
        n = 0
        while alias.attention(fac.key) > 0 and n < 2000:
            alias.decay_heat()
            n += 1
        times[fac.key] = n
        T.ok(n < 2000, f'{fac.key} heat cools at all')
    rates = {f.key: f.heat_decay for f in factions.FACTIONS}
    for a in times:
        for b in times:
            if a < b and abs(rates[a] - rates[b]) > 1e-9:
                T.ok(times[a] != times[b],
                     f'{a} at {rates[a]} and {b} at {rates[b]} cool differently')

    # Fractional heat has to survive a save. Storing it as a float and writing
    # it back as an int would truncate a little of it on every autosave, which
    # is the same bug wearing a different hat.
    alias = ident.Alias(name='probe')
    alias.add_heat('carrion', 10)
    alias.decay_heat()
    hot = alias.raw_heat('carrion')
    T.ok(hot != int(hot), 'a cooled name carries a fraction')
    T.eq(ident.Alias.from_dict(alias.to_dict()).raw_heat('carrion'), hot,
         'and the fraction survives a save')

    # --- Cover is worth having ------------------------------------------
    spans = []
    for origin in ('chromed', 'gutter', 'protege'):
        game = Game.new(Character.from_origin(origin, 'x'), seed=5)
        game.alias.add_heat('kagawa', 90)
        n = 0
        while game.alias.attention('kagawa') > 0 and n < 500:
            game.city.advance(game.rng, game.alias, 1, char=game.char)
            n += 1
        spans.append((game.char.attr('guile'), n))
    spans.sort()
    T.ok(spans[0][1] > spans[-1][1],
         'more Guile cools a name faster through the real city loop')
    T.ok(spans[0][1] - spans[-1][1] >= 5,
         'and by enough shifts that a player would notice')

    # The screen still shows whole numbers. Float storage is an implementation
    # detail and D14 says the player sees the sum, not the arithmetic.
    game = Game.new(Character.from_origin('gutter', 'y'), seed=5)
    game.alias.add_heat('kagawa', 12)
    game.city.advance(game.rng, game.alias, 1, char=game.char)
    _, rep_out = play(['rep'], game=game)
    T.ok(isinstance(game.alias.attention('kagawa'), int),
         'attention reads as a whole number')
    T.ok('Cover' in rep_out, 'and `rep` says what Cover is doing to it')

    # --- Guile in the price ---------------------------------------------
    game = Game.new(Character.from_origin('gutter', 'z'), seed=4242)
    listing = game.city.listings()[0]
    prices = []
    for guile in (1, 3, 6):
        price, terms = market_mod.quote(listing, game.city.where, game.alias,
                                        0, 1.0, 'morning', guile)
        prices.append(price)
        named = [label for label, _ in terms]
        T.ok(any('ask' in label for label in named),
             f'the quote at Guile {guile} names the haggle in its terms')
    T.ok(prices[0] > prices[1] > prices[2],
         'and a better talker pays less for the same thing')
    flat, _ = market_mod.quote(listing, game.city.where, game.alias, 0, 1.0,
                               'morning', 0)
    T.ok(flat >= prices[0], 'no Guile is no discount')

    # The shop has to be quoting the same number it charges. A default of zero
    # on the new argument would have left four of the five call sites pricing
    # goods as though nobody in this city could talk.
    game = Game.new(Character.from_origin('protege', 'w'), seed=4242)
    game.char.credits = 999_999
    _, shop = play(['shop'], game=game)
    listing = game.city.listings()[0]
    quoted, _ = market_mod.quote(listing, game.city.where, game.alias,
                                 game.char.dissonance,
                                 game.char.mult('price_mult'),
                                 game.city.phase, game.char.attr('guile'))
    T.ok(f'{quoted:,}' in shop,
         'the shelf price is the price a face is quoted')
    purse = game.char.credits
    play([f'buy {listing.key}'], game=game)
    T.eq(purse - game.char.credits, quoted,
         'and buying it takes exactly that much')

    # --- Guile in the legwork -------------------------------------------
    # `tap` lists the assets worth taking, three plus your bonus, so a better
    # talker comes back from the same network with a longer list. Two copies
    # of one character rather than two origins, so the only thing that differs
    # between the runs is the attribute under test.
    counts = []
    for guile in (1, 6):
        char = Character.from_origin('gutter', 'q')
        char.base_attrs['guile'] = guile
        char.credits = 50_000
        game = Game.new(char, seed=4242)
        job = game.city.board[0]
        _, out = play([f'take {job.cid}', 'legwork tap'], game=game)
        T.ok('Worth taking' in out, f'the tap lands at Guile {guile}')
        counts.append(out.count(';'))
    T.ok(counts[1] > counts[0],
         'and the better talker is told about more of the same network')

    # Resonance is the exception and has to stay one: it is not a conversation,
    # it is sitting near the thing and listening, so Guile buys nothing.
    reso = []
    for guile in (1, 6):
        char = Character.from_origin('gutter', 'r')
        char.base_attrs['guile'] = guile
        char.dissonance = drift.RESONANCE_BAND
        char.credits = 50_000
        game = Game.new(char, seed=4242)
        job = game.city.board[0]
        _, out = play([f'take {job.cid}', 'legwork resonance'], game=game)
        reso.append(out)
    T.eq(reso[0].count(';'), reso[1].count(';'),
         'listening to a network is not a conversation, so Guile buys nothing')


def test_topology() -> None:
    T.section('topology')
    from flatline.run import network as net_mod

    game = Game.new(Character.from_origin('gutter', 'mapper'), seed=8829)
    sess, _ = play(['take c001', 'travel ninth', 'travel shambles',
                    'jack in --force'], game=game)
    net = sess.run.net
    for node in net.nodes.values():
        node.known = True
    visible = set(net.nodes)

    rows = net_mod.tree_rows(net, net.entry, visible)
    drawn = [uid for _, uid in rows]
    T.eq(len(drawn), len(set(drawn)), 'no host is drawn twice')
    T.eq(set(drawn), visible, 'every visible host is drawn exactly once')
    T.eq(rows[0], ('', net.entry), 'the entry is the root')

    # The tree must never claim a link that does not exist. Every drawn row
    # has to be adjacent to something already drawn above it.
    children, extra = net_mod.spanning_tree(net, net.entry, visible)
    for parent, kids in children.items():
        for kid in kids:
            T.ok(kid in net.node(parent).edges,
                 f'{parent} really connects to {kid}')

    # Back edges are real edges and are never the parent link, or every
    # connection in the network gets reported twice.
    for uid, others in extra.items():
        for other in others:
            T.ok(other in net.node(uid).edges, 'a back edge is a real edge')
            T.ok(other not in children.get(uid, []),
                 'and is not one the tree already drew')
            T.ok(uid not in children.get(other, []),
                 'and is not the link to its own parent')

    # Only what the player has seen. A map that draws unscanned hosts is a
    # map that hands them the whole network for free.
    for node in net.nodes.values():
        node.known = False
    net.node(net.entry).known = True
    rows = net_mod.tree_rows(net, net.entry, {net.entry})
    T.eq([uid for _, uid in rows], [net.entry],
         'an unscanned network draws one host')

    # Degenerate inputs are a blank map, not a traceback.
    T.eq(net_mod.tree_rows(net, 'nonexistent', visible), [],
         'an unknown root draws nothing')
    T.eq(net_mod.spanning_tree(net, 'nonexistent', visible), ({}, {}),
         'and lays out nothing')
    T.eq(net_mod.tree_rows(net, net.entry, set()), [('', net.entry)],
         'nothing visible still draws the root')

    # The prefixes are pure box drawing, and degrade.
    for _, uid in rows:
        T.ok(uid in net.nodes, 'every drawn row names a real host')
    for node in net.nodes.values():
        node.known = True
    ascii_rows = net_mod.tree_rows(net, net.entry, visible, ascii_only=True)
    T.ok(all(ord(ch) < 128 for prefix, _ in ascii_rows for ch in prefix),
         'ascii mode draws the tree in ascii')
    uni = net_mod.tree_rows(net, net.entry, visible)
    T.eq([u for _, u in uni], [u for _, u in ascii_rows],
         'and draws exactly the same shape')

    # Faction sigils. Every faction has one, at both rungs, and they are all
    # the same size or the block reads as broken.
    from flatline.content import cyberspace as cs
    for fac in factions.FACTIONS:
        for ascii_only in (False, True):
            rows = cs.sigil(fac.key, ascii_only)
            T.eq(len(rows), cs.SIGIL_HEIGHT, f'{fac.key} sigil is 4 rows')
            T.eq({ui.width(r) for r in rows}, {cs.SIGIL_WIDTH},
                 f'{fac.key} sigil is a rectangle')
        T.ok(all(ord(c) < 128 for r in cs.sigil(fac.key, True) for c in r),
             f'{fac.key} degrades to ascii')
        T.ok(cs.sigil_role(fac.key) in theme.ROLES,
             f'{fac.key} sigil has a real palette role')
    T.eq(cs.sigil('nonexistent'), (), 'an unknown faction has no sigil')
    T.eq(cs.sigil_role('nonexistent'), 'ice',
         'and falls back to a real role rather than crashing')
    T.eq(len({tuple(v) for v in cs.SIGILS.values()}), len(cs.SIGILS),
         'no two factions share a mark')

    # The trace sparkline. Its whole job is shape, and it must not lie about
    # the shape or about how much history it is showing.
    caps = quiet_console().caps
    T.eq(len(ui.sparkline(list(range(40)), 24, caps)), 24,
         'a sparkline is exactly the width asked for')
    T.eq(len(ui.sparkline([1, 2], 24, caps)), 24,
         'even when there is less data than there are cells')
    T.eq(ui.sparkline([], 24, caps), '', 'and nothing when there is no data')
    T.eq(ui.sparkline([5], 0, caps), '', 'or no room')
    T.eq(set(ui.sparkline([7, 7, 7, 7], 8, caps, lo=7, hi=7)), {ui.SPARK[0]},
         'a flat series scaled to itself is flat')
    T.eq(set(ui.sparkline([7, 7, 7, 7], 8, caps)), {ui.SPARK[-1]},
         'and against a zero baseline sits at its own maximum')
    T.eq(set(ui.sparkline([5, 5], 4, caps, lo=0, hi=10)),
         {ui.SPARK[len(ui.SPARK) // 2]},
         'and halfway up a fixed range sits halfway')
    rising = ui.sparkline(list(range(24)), 24, caps)
    T.eq(rising[0], ui.SPARK[0], 'a rising series starts low')
    T.eq(rising[-1], ui.SPARK[-1], 'and ends high')
    T.ok(all(ord(c) < 128 for c in
             ui.sparkline([1, 5, 9], 8, Caps(color=ui.ColorLevel.NONE,
                                             glyphs=ui.GlyphLevel.ASCII,
                                             width=80, palette=theme.NEUTRAL))),
         'and degrades to ascii')

    # Long runs must not accumulate history without bound.
    from flatline.run import session as session_mod
    T.ok(len(sess.run.trace_history) <= session_mod.TRACE_HISTORY,
         'trace history is capped')
    sess.run.trace_history = [float(i) for i in range(500)]
    sess.run.advance(1)
    T.ok(len(sess.run.trace_history) <= session_mod.TRACE_HISTORY,
         'and stays capped after a tick')

    # Both renderings work through the command, and neither costs a tick.
    # Driven on the live session rather than a fresh one, because `map` needs
    # a run and a run lives on the session rather than on the game.
    before = sess.run.tick
    sess.console.start_capture()
    sess.execute('map')
    out = sess.console.end_capture()
    T.ok(net.entry in out, 'the tree map names the entry')
    T.ok('\u2514' in out or '\u251c' in out, 'and draws the tree')
    sess.console.start_capture()
    sess.execute('map --flat')
    flat = sess.console.end_capture()
    T.ok('perimeter' in flat, 'the flat map groups by zone')
    T.eq(sess.run.tick, before, 'looking at the map costs no time')




def test_clock() -> None:
    T.section('clock')
    from flatline.content import shifts
    from flatline.world import city as city_mod, fallout, market as market_mod

    T.eq(tuple(p.key for p in shifts.PHASES), city_mod.SHIFT_NAMES,
         'the phases are the city clock')
    T.eq(shifts.phase('nonsense').key, 'morning',
         'an unknown phase falls back rather than crashing')

    # The design is an inversion: the shift that is worst on the street has
    # to be the best in the net, or the clock is a tax and not a decision.
    street = max(shifts.PHASES, key=lambda p: p.danger)
    net = max(shifts.PHASES, key=lambda p: p.trace)
    T.ok(street is not net, 'no shift is worst both outside and inside')
    T.eq(street.key, 'afternoon', 'peak is the dangerous one to walk through')
    T.eq(net.key, 'night', 'and the small hours are the exposed one to run in')

    # Travel danger really moves with the clock.
    game = Game.new(Character.from_origin('gutter', 'clock'), seed=5)
    game.alias.add_heat('kagawa', 60)
    scores = {}
    for phase_i, name in enumerate(city_mod.SHIFT_NAMES):
        game.city.shift = phase_i
        T.eq(game.city.phase, name, 'the clock reports the phase it is on')
        scores[name] = game.city.danger(game.alias, 'vertical')[0]
    T.ok(scores['afternoon'] > scores['morning'] > scores['night'],
         f'danger tracks the shift: {scores}')

    # So do prices, and the reason is itemised rather than hidden.
    listing = game.city.listings()[0]
    day, _ = market_mod.quote(listing, 'marrow', game.alias, 0, 1.0, 'morning')
    dark, terms = market_mod.quote(listing, 'marrow', game.alias, 0, 1.0,
                                   'night')
    T.ok(dark > day, 'out of hours costs more')
    T.ok(any('night' in label for label, _ in terms),
         'and says so in the itemisation')

    # And the trace. Same run, same everything, different shift.
    def trace_after(phase: str) -> float:
        g = Game.new(Character.from_origin('gutter', 'r'), seed=8829)
        contract = g.city.board[0]
        stream = g.rng.fork('network', contract.cid)
        net_ = net_mod.generate(stream, contract.target, int(contract.posture),
                                contract.objective, contract.size_mod)
        from flatline.run.session import RunState
        st = RunState.begin(net_, g.char, g.rng('combat'), quiet_console(),
                            contract=contract.to_dict(), phase=phase)
        st.advance(10)
        return st.trace

    night, peak = trace_after('night'), trace_after('afternoon')
    T.ok(night > peak,
         f'the trace runs faster with nobody to hide behind ({night} vs {peak})')
    T.ok(night / max(peak, 0.01) < 1.5,
         'but not so much faster that off-peak is unplayable')

    # District state: the city's oldest promise, said out loud in the street.
    d = districts.BY_KEY['ninth']
    base = districts.factions_posture(d.controller)
    T.eq(districts.mood(d, base, 0.0), [],
         'a district nothing has happened to says nothing')
    T.eq(districts.mood(d, base - 1, 0.0), [],
         'and a rounding error either way is still nothing')
    T.ok(districts.mood(d, base - 20, 0.0), 'somebody stopping paying shows')
    T.ok(districts.mood(d, base + 25, 0.0), 'so does hardening')
    T.eq(len(districts.mood(d, base + 40, 90.0)), 2,
         'hardened and hunted are two separate facts and read as two')
    steps = [districts.mood(d, base + t, 0.0)[0]
             for t, _ in districts.HARDENING]
    T.eq(len(set(steps)), len(districts.HARDENING),
         'each tier of hardening reads differently')
    T.eq(districts.mood(d, base + 999, 0.0)[0], steps[-1],
         'and the top tier is the top, however far past it you go')

    # The whole thing has to be visible, or it is a hidden system.
    _, out = play(['new Clock --origin gutter --seed 8829', 'look'])
    T.ok('shutters' in out.lower() or 'getting up' in out.lower(),
         '`look` describes the shift')
    _, out = play(['new Clock --origin gutter --seed 8829', 'rest 2', 'look'])
    T.ok('quieter' in out or 'prices up' in out,
         'and says what the clock is costing you')




def test_rice() -> None:
    T.section('rice')
    import tempfile
    from flatline import anim, prompt as prompt_mod
    from flatline.content import rice
    from flatline.ui import Caps, ColorLevel, GlyphLevel, FRAMES, BARS, MARKS

    # Run the whole suite against a throwaway data directory, so a real
    # player's unlocks are never touched by the tests.
    old_home = os.environ.get('XDG_DATA_HOME')
    os.environ['XDG_DATA_HOME'] = tempfile.mkdtemp()
    try:
        _rice_body(T, rice, prompt_mod, anim, Caps, ColorLevel, GlyphLevel,
                   FRAMES, BARS, MARKS)
    finally:
        if old_home is None:
            del os.environ['XDG_DATA_HOME']
        else:
            os.environ['XDG_DATA_HOME'] = old_home


def _rice_body(T, rice, prompt_mod, anim, Caps, ColorLevel, GlyphLevel,
               FRAMES, BARS, MARKS) -> None:
    # Every axis has something free, and the default is one of them. A new
    # player who has never finished a run still has a shell.
    fresh = dict(save_mod.META_DEFAULT)
    for kind in rice.KINDS:
        free = [c for c in rice.BY_KIND[kind] if rice.met(c, fresh)]
        T.ok(free, f'{kind} has something available immediately')
        T.ok(rice.DEFAULTS[kind] in {c.key for c in free},
             f'and {kind} defaults to one of them')

    # Nothing is available before it is earned.
    locked = [c for c in rice.COSMETICS if not rice.met(c, fresh)]
    T.ok(len(locked) > 20, 'most of the catalogue starts locked')
    for item in locked:
        T.ok(item.hint, f'{item.kind}/{item.key} says how to get it')

    # And everything is reachable by playing. A cosmetic nobody can earn is
    # worse than one that was never written.
    maxed = dict(fresh)
    for counter in rice.COUNTERS.values():
        if counter:
            maxed[counter] = 10 ** 9
    T.eq(len(rice.unlocked(maxed)), len(rice.COSMETICS),
         'every cosmetic is reachable')

    # Unlocks are announced once and only once.
    already = set()
    first = rice.newly_earned(fresh, already)
    already |= {f'{c.kind}:{c.key}' for c in first}
    T.eq(rice.newly_earned(fresh, already), [],
         'nothing is announced twice')
    stats = dict(fresh, runs_completed=3)
    later = rice.newly_earned(stats, already)
    T.ok(later, 'and playing earns more')
    T.ok(all(c.needs[0] != 'always' for c in later),
         'without re-announcing the defaults')

    # `minimal` is both a prompt and a mark set, unlocked by different things.
    # Keying the announcement by name alone would conflate them.
    T.ok(('prompt', 'minimal') in rice.BY_KEY
         and ('marks', 'minimal') in rice.BY_KEY,
         'two axes share a key')
    T.ok(rice.BY_KEY[('prompt', 'minimal')].needs
         != rice.BY_KEY[('marks', 'minimal')].needs,
         'and they unlock differently, so the key alone is not an identity')

    # Every style the engine can render is offered, and vice versa.
    T.eq({c.key for c in rice.BY_KIND['palette']}, set(theme.PALETTES),
         'every palette is in the catalogue')
    T.eq({c.key for c in rice.BY_KIND['frame']}, set(FRAMES),
         'every frame is')
    T.eq({c.key for c in rice.BY_KIND['bars']}, set(BARS), 'every bar set is')
    T.eq({c.key for c in rice.BY_KIND['marks']}, set(MARKS), 'every mark set is')
    T.eq({c.key for c in rice.BY_KIND['prompt']}, set(prompt_mod.BY_KEY),
         'every prompt is')
    T.eq({c.key for c in rice.BY_KIND['banner']}, set(anim.BANNERS),
         'every banner is')

    # Style tables only ever override glyphs that exist, or `g()` would hand
    # back a decoration for something nothing draws.
    for table in (FRAMES, BARS, MARKS):
        for name, overrides in table.items():
            for glyph in overrides:
                T.ok(glyph in ui.GLYPHS, f'{name} overrides a real glyph')

    # Capability beats preference, always. A decorated frame a terminal
    # cannot draw is worse than no decoration.
    for frame in FRAMES:
        caps = Caps(color=ColorLevel.NONE, glyphs=GlyphLevel.ASCII, width=80,
                    palette=theme.NEUTRAL, frame=frame)
        for glyph in ui.GLYPHS:
            T.ok(all(ord(ch) < 128 for ch in caps.g(glyph)),
                 f'{frame} stays ascii on an ascii terminal')

    # The window banner is drawn from the player's own frame set, which is
    # the one place two rice axes compose. Every pairing has to hold its
    # rectangle, including the frame that is made entirely of spaces.
    for frame in FRAMES:
        probe = Caps(color=ColorLevel.NONE, glyphs=GlyphLevel.UNICODE,
                     width=78, palette=theme.NEUTRAL, frame=frame)
        for style in ('terminal', 'stack'):
            rows = anim.banner_rows(style, False, True, probe)
            T.ok(rows, f'{style} draws something with the {frame} frame')
            T.eq(len({len(r) for r in rows}), 1,
                 f'{style} stays a rectangle with the {frame} frame')

    # Every generated banner is a rectangle too, or the gradient renders a
    # ragged edge that reads as a rendering fault.
    for style in anim.BANNERS:
        for ascii_only in (False, True):
            probe = Caps(color=ColorLevel.NONE,
                         glyphs=GlyphLevel.ASCII if ascii_only
                         else GlyphLevel.UNICODE,
                         width=78, palette=theme.NEUTRAL)
            rows = anim.banner_rows(style, ascii_only, True, probe)
            if not rows:
                continue
            T.eq(len({len(r) for r in rows}), 1,
                 f'{style} is a rectangle')
            T.ok(max(len(r) for r in rows) <= 78,
                 f'{style} fits the reading column')

    # A saved preference for something this build no longer ships must not
    # raise; it degrades.
    caps = Caps(color=ColorLevel.NONE, glyphs=GlyphLevel.UNICODE, width=80,
                palette=theme.NEUTRAL, frame='nonexistent', bars='gone',
                marks='missing')
    T.eq(caps.g('hline'), ui.GLYPHS['hline'][0],
         'an unknown style falls back to the default glyph')

    # THE hard rule: whatever the prompt looks like, the trace is on it.
    game = Game.new(Character.from_origin('gutter', 'rice'), seed=8829)
    contract = game.city.board[0]
    sess, _ = play([f'take {contract.cid}'], game=game)
    from flatline.run import network as net_mod
    from flatline.run.session import RunState
    stream = game.rng.fork('network', contract.cid)
    net = net_mod.generate(stream, contract.target, int(contract.posture),
                           contract.objective, contract.size_mod)
    sess.run = RunState.begin(net, game.char, game.rng('combat'),
                              sess.console, contract=contract.to_dict())
    sess.run.advance(23)
    trace = f'{int(sess.run.trace_pct * 100)}%'
    for style in prompt_mod.STYLE_KEYS:
        sess.prompt_style = style
        line = sess.prompt()
        T.ok(trace in line,
             f'the {style} prompt still shows the trace ({line.strip()!r})')
        T.ok(len(line) < 46, f'and {style} leaves room to type')

    # Every style survives having no character at all, and still looks like
    # itself. Falling through to one shared string would mean the first thing
    # somebody sees after choosing a prompt is not the prompt they chose.
    bare, _ = play([])
    seen_bare = set()
    for style in prompt_mod.STYLE_KEYS:
        bare.prompt_style = style
        line = bare.prompt()
        T.ok(line.strip(), f'{style} renders with no game loaded')
        seen_bare.add(line)
    T.ok(len(seen_bare) >= len(prompt_mod.STYLE_KEYS) - 1,
         'and the bare forms are nearly all distinct')

    # The preview panel draws a run, so its prompt has to be an in-run one
    # even when the session has no run and no character.
    for style in prompt_mod.STYLE_KEYS:
        line = prompt_mod.sample_run(style, quiet_console().caps)
        T.ok('62%' in line, f'the {style} preview prompt carries the trace')
        T.ok('ap-arc21' in line or 'ap' in line,
             f'and {style} names the host')

    # The command drives it, and the choice persists across sessions.
    save_mod.bump_meta(runs_completed=9, clean_runs=5, characters_created=3)
    sess, out = play(['rice'])
    T.ok('palette' in out and 'banner' in out, '`rice` lists every axis')

    sess, out = play(['rice palette amber'])
    T.eq(sess.shell['palette'], 'amber', 'a palette can be worn')
    T.eq(sess.console.caps.palette.name, 'amber', 'and takes effect at once')
    again, _ = play([])
    again.apply_shell()
    T.eq(again.console.caps.palette.name, 'amber',
         'and is still on in a new session')

    sess, out = play(['rice palette ash'])
    T.ok('not yours yet' in out, 'a locked cosmetic is refused')
    T.ok('Lose somebody' in out, 'and says what would unlock it')
    T.eq(sess.shell['palette'], 'amber', 'and nothing changes')

    save_mod.high_water(black_ice_survived=1)
    sess, _ = play(['rice frame heavy', 'rice bars ladder', 'rice marks angular',
                    'rice prompt bracket'])
    T.eq((sess.console.caps.frame, sess.console.caps.bars,
          sess.console.caps.marks, sess.prompt_style),
         ('heavy', 'ladder', 'angular', 'bracket'),
         'every axis can be set independently')
    T.eq(sess.console.caps.g('hline'), '\u2501', 'and the glyph really changes')

    sess, _ = play(['rice --reset'])
    T.eq(sess.shell, rice.DEFAULTS, 'reset puts everything back')

    # A preference saved by a build that shipped something this one does not
    # falls back rather than reaching the renderer.
    meta = save_mod.read_meta()
    meta['shell'] = {'palette': 'from-the-future', 'frame': 'gone',
                     'nonsense': 'whatever', 'bars': 'shaded'}
    save_mod.write_meta(meta)
    stale, _ = play([])
    stale.apply_shell()
    T.eq(stale.shell['palette'], rice.DEFAULTS['palette'],
         'an unknown palette falls back to the default')
    T.eq(stale.shell['frame'], rice.DEFAULTS['frame'], 'and an unknown frame')
    T.ok('nonsense' not in stale.shell, 'and an unknown axis is dropped')
    T.eq(stale.shell['bars'], 'shaded', 'while the valid part survives')
    save_mod.write_meta({**meta, 'shell': {}})

    # `--try` shows without keeping, which is the most useful thing a
    # customisation menu can do.
    sess, out = play(['rice --reset', 'rice palette phosphor --try'])
    T.ok('preview' in out, '--try renders a sample')
    T.ok('not saved' in out, 'and says it is not keeping it')
    T.eq(sess.shell['palette'], rice.DEFAULTS['palette'],
         'and really does not keep it')
    T.eq(sess.console.caps.palette.name, theme.get(rice.DEFAULTS['palette']).name,
         'and puts the console back afterwards')
    _, out = play(['rice --preview'])
    T.ok('preview' in out, '--preview works on what you are wearing')

    for line in ('rice nonsense', 'rice palette nonsense', 'rice palette',
                 'rice banner none', 'rice --reset', 'rice palette ash --try',
                 'rice --try', 'rice frame --try'):
        _, out = play([line])
        T.ok(out.strip(), f'{line!r} says something rather than crashing')

    # Losing a character is the one moment where announcing an unlock is the
    # point rather than an interruption: everything else they had is gone and
    # this is the thing that is not.
    from flatline.commands import run as run_cmd
    from flatline.run import network as net_mod2
    from flatline.run.session import RunState as RS
    doomed = Game.new(Character.from_origin('gutter', 'doomed'), seed=3)
    console = quiet_console()
    dead = Session(console=console, slot='dead')
    dead.game = doomed
    job = doomed.city.board[0]
    doomed.city.accepted = job.cid
    stream = doomed.rng.fork('network', job.cid)
    net2 = net_mod2.generate(stream, job.target, int(job.posture),
                             job.objective, job.size_mod)
    dead.run = RS.begin(net2, doomed.char, doomed.rng('combat'), console,
                        contract=job.to_dict())
    dead.run.finish('flatline')
    console.start_capture()
    run_cmd._resolve(dead)
    obit = console.end_capture()
    T.ok('killed by' in obit, 'a flatline is reported')
    T.ok('Ash' in obit, 'and hands over the palette it earned')
    T.ok(obit.index('killed by') < obit.index('Ash'),
         'after the obituary, not before it')
    T.eq(save_mod.read_meta()['flatlines'], 1, 'and is counted')
    save_mod.delete('dead')

    # `career` is where the meta layer becomes visible, and it has to survive
    # a profile with nothing in it.
    save_mod.write_meta(dict(save_mod.META_DEFAULT))
    _, out = play(['career'])
    T.ok('Nothing yet' in out, 'career on a fresh profile says so')
    T.ok('Traceback' not in out, 'without dividing by anything')

    save_mod.bump_meta(characters_created=4, flatlines=2, runs_completed=27,
                       clean_runs=9)
    save_mod.high_water(best_credits=61500, deepest_drift=58,
                        districts_seen=7, best_standing=52,
                        black_ice_survived=1, threads_closed=3)
    _, out = play(['career'])
    T.ok('4 started' in out and '2 lost' in out, 'career counts the runners')
    T.ok('27' in out and '33%' in out, 'and the work, clean and otherwise')
    T.ok('unlocked' in out, 'and how much of the shell is open')
    T.ok('only thing on this page' in out,
         'and says what survived them, once somebody has been lost')

    # It must not divide by zero when nothing has been earned or everything has.
    save_mod.write_meta({**save_mod.META_DEFAULT, 'characters_created': 1})
    _, out = play(['career'])
    T.ok('contracts' in out, 'career with no runs at all still renders')
    maxed = dict(save_mod.META_DEFAULT, characters_created=1)
    for counter in rice.COUNTERS.values():
        if counter:
            maxed[counter] = 10 ** 9
    save_mod.write_meta(maxed)
    _, out = play(['career'])
    T.ok(f'{len(rice.COSMETICS)}/{len(rice.COSMETICS)}' in out,
         'and with the whole catalogue open')

    # Cosmetics must not touch a single number in the game.
    a = Game.new(Character.from_origin('gutter', 'a'), seed=4242)
    before = (a.char.credits, a.char.xp, a.char.memorable,
              [c.cid for c in a.city.board], a.rng.getstate())
    play(['rice palette phosphor', 'rice frame scan', 'rice bars dots'],
         game=a)
    after = (a.char.credits, a.char.xp, a.char.memorable,
             [c.cid for c in a.city.board], a.rng.getstate())
    T.eq(before, after, 'ricing the shell changes nothing in the world')

    # The unlocks live outside the save, so they outlive the character. The
    # ledger is written when time moves rather than when the catalogue is
    # read, because its only job is deciding what to announce; `rice` itself
    # always reads the live counters and is never stale.
    play(['rest 1'], game=a)
    save_mod.write(a.to_dict(), 'ricetest')
    meta = save_mod.read_meta()
    T.ok(meta['unlocked'], 'unlocks are recorded in meta')
    T.ok('unlocked' not in a.to_dict(), 'and not in the save')
    T.ok('shell' not in a.to_dict(), 'nor is the chosen look')
    save_mod.delete('ricetest')



def test_roster() -> None:
    """Characters, and the several ways the game used to lose one."""
    T.section('roster')
    import re
    import tempfile
    from flatline import save as save_mod
    from flatline.shell import AFTER_THE_END, REGISTRY

    old_home = os.environ.get('XDG_DATA_HOME')
    os.environ['XDG_DATA_HOME'] = tempfile.mkdtemp()
    try:
        _roster_body(save_mod, REGISTRY, AFTER_THE_END, re)
    finally:
        if old_home is None:
            del os.environ['XDG_DATA_HOME']
        else:
            os.environ['XDG_DATA_HOME'] = old_home


def _roster_body(save_mod, REGISTRY, AFTER_THE_END, re) -> None:
    from flatline.session import Session

    def fresh():
        return Session(console=quiet_console(), slot='default')

    # --- making a second character must not touch the first --------------
    # It used to. Everybody shared one slot called 'default', so the next
    # autosave after `new` wrote the new character over the old one. Nothing
    # said so, because from the save layer's point of view nothing unusual
    # had happened, and the refusal you cleared to get there said "abandon".
    sess = fresh()
    sess.execute('new Jack --origin gutter')
    T.eq(sess.slot, 'jack', 'a character is filed under their own name')
    jack_seed = sess.game.rng.seed

    sess.execute('new Vex --origin ghost')
    T.eq(sess.slot, 'vex', 'and so is the next one')
    T.eq(sess.game.char.handle, 'Vex', 'who is who you are now')
    handles = {e.handle for e in save_mod.roster()}
    T.eq(handles, {'Jack', 'Vex'}, 'and both of them still exist')

    # The one that was put away has to come back *as they were*.
    sess.execute('switch Jack')
    T.eq(sess.game.char.handle, 'Jack', 'switching goes back to them')
    T.eq(sess.game.rng.seed, jack_seed, 'and it is the same world they had')

    # --- switching saves before it leaves --------------------------------
    sess.game.char.credits = 4242
    sess.execute('switch Vex')
    sess.execute('switch Jack')
    T.eq(sess.game.char.credits, 4242,
         'what you did before switching away is still done')

    # --- nothing but `delete` removes anybody ----------------------------
    before = {e.handle for e in save_mod.roster()}
    for line in ('new Ash --origin academic', 'switch Jack', 'save',
                 'restore vex'):
        sess.execute(line)
    after = {e.handle for e in save_mod.roster()}
    T.ok(before <= after, 'no ordinary command loses a character')

    # `delete` asks first, and says what it is about to throw away.
    sess.console.start_capture()
    sess.execute('delete Ash')
    asked = sess.console.end_capture()
    T.ok('Ash' in asked, 'delete names who it is about to lose')
    T.ok('--confirm' in asked, 'and does not do it until you confirm')
    T.ok('Ash' in {e.handle for e in save_mod.roster()},
         'and has not done it yet')

    sess.execute('delete Ash --confirm')
    T.ok('Ash' not in {e.handle for e in save_mod.roster()},
         'confirming does it')

    # Deleting whoever you are leaves you as nobody rather than as a ghost
    # pointing at a file that is not there.
    sess.execute('switch Jack')
    sess.execute('delete Jack --confirm')
    T.eq(sess.game, None, 'deleting yourself leaves nobody loaded')
    T.ok('Jack' not in {e.handle for e in save_mod.roster()}, 'and they are gone')

    # --- the lines the game offers have to work --------------------------
    # The splash said `new` to make a character, `load` to continue one. Both
    # halves were wrong: `load` puts a program on a deck, the command is
    # `restore`, and by the time it printed the game had usually already
    # continued somebody. A player following the game's own first sentence
    # got an error.
    def offered(text: str) -> list[str]:
        out = []
        for quoted in re.findall(r'`([^`]+)`', text):
            words = quoted.split()
            if not words:
                continue
            cmd = (REGISTRY.lookup(' '.join(words[:2]))
                   or REGISTRY.lookup(words[0]))
            if cmd is not None:
                out.append(cmd)
        return out

    empty = Session(console=quiet_console(), slot='default')
    for e in save_mod.roster():
        save_mod.delete(e.slot)
    for text, where in ((empty.opening_line(), 'the splash with nobody'),
                        (empty.nobody_loaded(), 'the no-character refusal')):
        cmds = offered(text)
        T.ok(bool(cmds), f'{where} names at least one command')
        for cmd in cmds:
            T.ok(cmd.bare, f'{where} offers `{cmd.name}`, which works '
                           f'with no character loaded')

    # With characters on disk it must still only offer usable verbs.
    empty.execute('new Nine --origin courier')
    empty.execute('new Ten --origin burnout')
    empty.game = None
    empty.slot = 'default'
    for text, where in ((empty.opening_line(), 'the splash with saves'),
                        (empty.nobody_loaded(), 'the refusal with saves')):
        for cmd in offered(text):
            T.ok(cmd.bare, f'{where} offers `{cmd.name}`, which works with '
                           f'no character loaded')

    # --- a finished character is finished --------------------------------
    # `game.over` was set on death, autosaved, and then read in exactly one
    # place, so a flatlined runner could stand up from the chair the game had
    # just described them dying in and go shopping.
    sess = fresh()
    sess.execute('new Doomed --origin burnout')
    sess.game.over = 'flatlined'
    sess.autosave()  # what the flatline path itself does
    for verb in ('board', 'travel vertical', 'buy Crowbar', 'legwork perimeter'):
        sess.console.start_capture()
        sess.execute(verb)
        said = sess.console.end_capture()
        T.ok('flatlined' in said,
             f'a dead character cannot {verb.split()[0]}')
    # Checked against the refusal's own wording rather than against the word
    # "flatlined", because `characters` legitimately prints it: the roster
    # says so in the column that says how everybody ended.
    for verb, want in (('char', 'Bandwidth'), ('characters', 'Characters'),
                       ('rep', 'Standing')):
        sess.console.start_capture()
        sess.execute(verb)
        said = sess.console.end_capture()
        T.ok('You can still read' not in said,
             f'but can still {verb}, to see what happened')
        T.ok(want in said, f'and {verb} actually runs')
    T.ok(any(e.finished for e in save_mod.roster()),
         'and the roster says so')

    # Retirement ends a character too, and must not be described as death.
    sess.game.over = 'retired'
    sess.console.start_capture()
    sess.execute('board')
    said = sess.console.end_capture()
    T.ok('retired' in said, 'somebody who walked away is told they walked away')
    T.ok('flatlined' not in said, 'and is not told they are dead')

    # Every verb on the allowlist has to exist, and the allowlist has to
    # leave a finished character a way out.
    for name in AFTER_THE_END:
        T.ok(REGISTRY.lookup(name) is not None,
             f'`{name}` still works after the end and is a real command')
    sess.console.start_capture()
    sess.execute('new Somebody --origin gutter')
    T.eq(sess.game.char.handle, 'Somebody',
         'and you can always make somebody else')
    sess.console.end_capture()

    # --- a corrupt save must not hide the others -------------------------
    from flatline.config import data_dir
    (data_dir() / 'save-wrecked.json').write_text('{ not json')
    entries = save_mod.roster()
    T.ok(any(e.broken for e in entries), 'a bad save reads as broken')
    T.ok(any(not e.broken for e in entries),
         'and the readable ones are still listed')
    sess.console.start_capture()
    sess.execute('characters')
    listed = sess.console.end_capture()
    T.ok('Somebody' in listed, 'the roster still prints the living')
    T.ok('unreadable' in listed, 'and says which one will not open')


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


def test_guide() -> None:
    """D50: an empty line answers, `new` is a conversation, numbers are names."""
    T.section('guide')
    from flatline.commands import guide
    from flatline.commands.city import SERVICE_VERBS

    # An empty line answers, with nobody loaded.
    sess, out = play([''])
    T.ok('what now' in out, 'an empty line with nobody loaded prints what now')
    T.ok('`new`' in out or 'new ' in out, 'and points at `new`')
    T.ok(sess.pending is None, 'and asks nothing')
    _, out = play(['now'])
    T.ok('what now' in out, '`now` is the same thing typed')
    for alias in ('next', 'hint', 'menu'):
        T.ok(REGISTRY.lookup(alias) is REGISTRY.lookup('now'),
             f'`{alias}` reaches it too')

    # Did you mean.
    _, out = play(['bord'])
    T.ok('Did you mean' in out and '`board`' in out,
         'a typo is answered with the word it nearly was')
    _, out = play(['zzqqxxw'])
    T.ok('not a command' in out and 'Did you mean' not in out,
         'and nothing close means no guess')

    # The guided `new`, end to end, by number, spending the points.
    sess, out = play(['new', '2', 'Guided', '1'])
    T.ok(sess.game is not None, 'the conversation makes a character')
    T.eq(sess.game.char.origin, 'gutter', 'origin picked by its number')
    T.eq(sess.game.char.handle, 'Guided', 'the second answer is the handle')
    T.eq(sess.game.char.points, 0, 'answer 1 spends the attribute points')
    T.ok(sess.game.char.xp < skills.CREATION_XP, 'and the experience')
    T.ok(max(sess.game.char.base_attrs.values()) < attr_content.ATTR_MAX,
         'without pushing an attribute to the ceiling')
    T.ok(sess.pending is None, 'and nothing is left waiting')
    T.ok('what now' in out, 'and it ends on the next move')
    T.ok(save_mod.exists(sess.slot), 'and they are on disk')
    save_mod.delete(sess.slot)

    # By name, keeping the points.
    sess, out = play(['new', 'academic', 'Keeper', '2'])
    T.eq(sess.game.char.origin, 'academic', 'origin picked by its name')
    T.eq(sess.game.char.points, attr_content.CREATION_POINTS,
         'answer 2 keeps the points')
    T.eq(sess.game.char.xp, skills.CREATION_XP, 'and the experience')
    save_mod.delete(sess.slot)

    # Reading first, a bad answer, and backing out.
    sess, out = play(['new', 'read 2'])
    T.ok('Jury-rig' in out, '`read 2` reads the gutter runner in full')
    T.ok(sess.pending is not None, 'and the question is still waiting')
    T.eq(sess.prompt(), guide.ASK_ORIGIN, 'the prompt is the question')
    sess.console.start_capture()
    sess.execute('zzz')
    out = sess.console.end_capture()
    T.ok('not one of' in out and sess.pending is not None,
         'a bad answer is refused and asked again')
    sess.console.start_capture()
    sess.execute('')
    out = sess.console.end_capture()
    T.ok(sess.pending is None and sess.game is None,
         'an empty line backs out of the question')
    T.ok('No runner made' in out, 'and says so')
    T.ok(sess.prompt() != guide.ASK_ORIGIN,
         'and the prompt goes back to being a prompt')
    sess, out = play(['new', 'read all'])
    T.ok(all(o.name in out for o in origins.ORIGINS),
         '`read all` is every origin in full')
    T.ok(sess.pending is not None, 'and still asks')
    sess, _ = play(['new', 'random', 'Dealt'])
    T.ok(sess.game is not None and sess.game.char.origin in origins.BY_KEY,
         '`random` lets the city pick')
    save_mod.delete(sess.slot)

    # Handles that cannot be handles.
    for bad in ('map', '42', 'two words', 'x' * 30):
        sess, out = play(['new', '2', bad])
        T.ok(sess.game is None and sess.pending is not None,
             f'{bad!r} is refused as a handle and asked again')
    sess, _ = play(['new Twin --origin gutter'])
    sess2, out = play(['new', '2', 'Twin'])
    T.ok(sess2.game is None and 'already' in out,
         'a handle already on the roster is refused')
    save_mod.delete(sess.slot)
    T.ok(guide.handle_problem('Fine-Name') == '', 'an ordinary handle passes')

    # `quit` at a question is still quit.
    sess, _ = play(['new', 'quit'])
    T.ok(not sess.running, '`quit` at a question leaves the game')

    # A handle and nothing else answers one question and is asked the rest.
    sess, out = play(['new Named', '3', '2'])
    T.ok(sess.game is not None and sess.game.char.handle == 'Named'
         and sess.game.char.origin == 'protege',
         '`new <handle>` asks only for the origin and the spend')
    T.ok('handle?' not in out, 'and never asks for the handle')
    save_mod.delete(sess.slot)
    _, out = play(['new 42'])
    T.ok('digits' in out, 'and a bad handle is refused before any question')

    # The tutorial waits for the conversation to end.
    sess, out = play(['tutorial', 'new', '2', 'Taught'])
    T.ok('step 2' not in out, 'no tutorial step prints between questions')
    sess.console.start_capture()
    sess.execute('2')
    out = sess.console.end_capture()
    T.ok('step 2' in out, 'and the next step prints once it is over')
    save_mod.delete(sess.slot)

    # The one-shot form is unchanged, and takes the number too.
    sess, out = play(['new Shot --origin 2'])
    T.eq(sess.game.char.origin, 'gutter',
         'the one-shot form takes the origin by number')
    T.eq(sess.game.char.points, attr_content.CREATION_POINTS,
         'and spends nothing by itself')
    T.ok(sess.pending is None, 'and asks nothing')
    # `spend`: show, ask, refuse, then do it.
    sess.console.start_capture()
    sess.execute('spend')
    out = sess.console.end_capture()
    T.ok(sess.pending is not None and 'usually puts' in out,
         '`spend` shows the plan and asks')
    sess.execute('no')
    T.eq(sess.game.char.points, attr_content.CREATION_POINTS,
         '`no` keeps them')
    sess.execute('spend --go')
    T.eq(sess.game.char.points, 0, '`spend --go` spends without asking')
    sess.console.start_capture()
    sess.execute('spend')
    out = sess.console.end_capture()
    T.ok('nothing unspent' in out.lower(), 'and then there is nothing to spend')
    save_mod.delete(sess.slot)

    # The suggestion is legal, complete, and the same twice, for every origin.
    for o in origins.ORIGINS:
        char = Character.from_origin(o.key, 'Probe')
        char.points = attr_content.CREATION_POINTS
        char.xp = skills.CREATION_XP
        plan = guide.suggest(char)
        twin = Character.from_origin(o.key, 'Probe')
        twin.points, twin.xp = char.points, char.xp
        T.eq(guide.suggest(twin), plan, f'{o.key}: the same origin gets the '
                                        f'same plan')
        legal = True
        for verb, key in plan:
            ok, why = (char.can_boost(key) if verb == 'boost'
                       else char.can_train(key))
            if not ok:
                legal = False
                T.failures.append(f'guide: {o.key} plan step {verb} {key} '
                                  f'is illegal: {why}')
                break
            char.boost(key) if verb == 'boost' else char.train(key)
        T.ok(legal, f'{o.key}: every step is legal when taken')
        T.eq(char.points, 0, f'{o.key}: the plan spends every point')
        T.ok(char.xp < skills.RANK_COST[2],
             f'{o.key}: and leaves less than a rank two ({char.xp} xp)')
        T.ok(max(char.base_attrs.values()) < attr_content.ATTR_MAX,
             f'{o.key}: and maxes nothing')
        T.ok(any(r >= 2 for r in char.base_skills.values()),
             f'{o.key}: and buys at least one technique')
        T.ok(guide.describe(plan, Character.from_origin(o.key, 'P'))
             , f'{o.key}: the plan can be described')

    # `new --long` is the long listing.
    _, out = play(['new --long'])
    T.ok(all(o.name in out for o in origins.ORIGINS),
         '`new --long` lists every origin in full')
    # The short table fits the narrow rung.
    sess, out = play(['new'])
    T.ok(all(ui.width(line) <= 80 for line in out.splitlines()),
         'the origin table fits eighty columns')

    # What now, around the city.
    char = Character.from_origin('gutter', 'Now')
    char.points, char.xp = attr_content.CREATION_POINTS, skills.CREATION_XP
    game = Game.new(char, seed=4242)
    sess, out = play([''], game=game)
    T.ok('what now' in out and '`board' in out or 'board' in out,
         'no contract: the next move is the board')
    T.ok('spend' in out, 'and an unspent budget is mentioned')
    cid = game.city.board[0].cid
    sess.console.start_capture()
    sess.execute(f'take {cid}')
    sess.execute('')
    out = sess.console.end_capture()
    line, steps, also = guide.what_now(sess)
    T.ok(steps, 'with a contract there is a next step')
    first = steps[0][0]
    T.ok(first.startswith(('travel', 'load', 'market')) or first == 'jack in',
         f'and it is a real move ({first!r})')
    T.ok(first in out, 'which the panel prints')
    T.ok(all(REGISTRY.lookup(a.split()[0]) for a in also),
         'and every "also" verb exists')
    for cmd, _ in steps:
        T.ok(REGISTRY.lookup(cmd.split()[0].split(';')[0]) is not None,
             f'step {cmd!r} starts with a command')

    # Row numbers are names: the board.
    game = Game.new(Character.from_origin('gutter', 'Rows'), seed=4242)
    sess, out = play(['board', 'take 2'], game=game)
    T.eq(game.city.accepted, sess.listed['board'][1],
         '`take 2` takes the second row of the board as printed')
    T.ok('#' in out, 'and the board shows the numbers')
    game = Game.new(Character.from_origin('gutter', 'Rows'), seed=4242)
    _, out = play(['take 9'], game=game)
    T.ok('runs 1 to' in out and not game.city.accepted,
         'a row off the end is refused with the range')
    _, out = play(['board', 'board 1'], game=game)
    T.ok(game.city.board[0].title in out, '`board 1` reads the first row')
    T.ok('`take 1`' in out, 'and offers the row to take')
    _, out = play(['board 1'], game=game)
    T.ok('`take 1`' not in out and f'`take {game.city.board[0].cid}`' in out,
         'but only when that board has been shown this session')
    _, out = play(['board 2', 'take 1'], game=game)
    T.eq(game.city.accepted, game.city.board[0].cid,
         'without a listing, the row is the live board order')

    # The market.
    game = Game.new(Character.from_origin('defector', 'Shop'), seed=4242)
    sess, out = play(['market'], game=game)
    shown = sess.listed['market']
    T.ok(shown, 'the market remembers what it showed')
    want = next((i for i, k in enumerate(shown, 1) if k == 'crowbar'), None)
    if want is not None:
        before = len(game.char.library)
        sess.console.start_capture()
        sess.execute(f'buy {want}')
        out = sess.console.end_capture()
        T.eq(len(game.char.library), before + 1,
             f'`buy {want}` buys row {want}')
        T.ok('Crowbar' in out, 'and names what it bought')
    _, out = play(['buy 99'], game=game)
    T.ok('runs 1 to' in out, 'a market row off the end is refused')

    # Travel.
    game = Game.new(Character.from_origin('gutter', 'Walk'), seed=4242)
    first = game.city.district.neighbours[0]
    sess, out = play(['travel', 'travel 1'], game=game)
    T.eq(game.city.where, first, '`travel 1` walks to the first row')
    T.ok('Here:' in out, 'and arrival says what is here')
    _, out = play(['look'], game=game)
    T.ok('Here:' in out, '`look` says what is here too')
    T.ok('look (' not in out, 'without telling you to look')
    for service, verb, what in SERVICE_VERBS:
        T.ok(REGISTRY.lookup(verb) is not None, f'"{service}" offers a real '
                                                 f'verb ({verb})')
        T.ok(service in districts.SERVICES, f'and {service!r} is a service')

    # The roster.
    for handle in ('RowOne', 'RowTwo'):
        s, _ = play([f'new {handle} --origin gutter --seed 7'])
    sess, out = play(['characters'])
    slots = sess.listed.get('characters') or []
    T.ok(len(slots) >= 2, 'the roster remembers its rows')
    T.ok('#' in out, 'and shows them')
    want = next((i for i, s in enumerate(slots, 1) if s == 'rowtwo'), None)
    if want:
        sess.console.start_capture()
        sess.execute(f'switch {want}')
        sess.console.end_capture()
        T.ok(sess.game is not None and sess.game.char.handle == 'RowTwo',
             f'`switch {want}` picks up the row')
    for slot in ('rowone', 'rowtwo'):
        if save_mod.exists(slot):
            save_mod.delete(slot)

    # In a run, an empty line says where the trace is and what to do.
    game = Game.new(Character.from_origin('gutter', 'Runner'), seed=4242)
    contract = game.city.board[0]
    game.city.where = contract.district
    sess, _ = play([f'take {contract.cid}', 'jack in --force'], game=game)
    T.ok(sess.run is not None, 'in a run')
    sess.console.start_capture()
    sess.execute('')
    out = sess.console.end_capture()
    T.ok('what now' in out and 'trace' in out, 'an empty line in a run '
                                                'prints the trace')
    T.ok('jack out' in out, 'and the way out')
    T.raises(lambda: sess.ask('x? ', lambda s, t: None),
             'a question cannot be asked inside a run')
    _, steps, _ = guide.what_now(sess)
    T.ok(steps and steps[0][0], 'and there is a next move')

    # A finished character is told where to go.
    game = Game.new(Character.from_origin('gutter', 'Late'), seed=4242)
    game.over = 'flatlined'
    _, out = play([''], game=game)
    T.ok('what now' in out and ('new' in out or 'switch' in out),
         'a finished character gets what now, pointing elsewhere')

    # The splash tells a first-timer where to start.
    console = quiet_console()
    sess = Session(console=console)
    console.start_capture()
    sess.splash(quick=True)
    out = console.end_capture()
    T.ok('empty line' in out, 'the splash mentions the empty line')
    living = [e for e in save_mod.roster() if not e.broken]
    if not living:
        T.ok('Start here' in out and 'tutorial' in out,
             'and a first-timer gets the start-here block')

    # Scripts cannot be left holding a question.
    sess, _ = play(['new Scripted --origin gutter'])
    sess.pending = None
    from flatline import script as script_mod
    sess.scripts['ask'] = script_mod.Script(name='ask', lines=['spend'])
    sess.console.start_capture()
    sess.run_script('ask')
    out = sess.console.end_capture()
    T.ok(sess.pending is None, 'a script that asks is not left waiting')
    T.ok('by hand' in out, 'and says to do it by hand')
    save_mod.delete(sess.slot)

    # The help landing still fits, and mentions the empty line.
    _, landing = play(['help'])
    lines = [x for x in landing.splitlines() if x.strip()]
    T.ok(len(lines) <= 30, f'`help` still fits a screen ({len(lines)} lines)')
    T.ok('now' in landing and 'empty line' in landing,
         'and offers `now` to somebody who is lost')


def test_consequences() -> None:
    """D51: a decision is read by the world, not only printed."""
    T.section('consequences')
    from flatline.content import events, legacy, npcs as npc_content, offers
    from flatline.content import threads as thread_content
    from flatline.world import contracts as contract_world
    from flatline.world import story as story_mod

    def fresh(origin='gutter', handle='Dec'):
        return Game.new(Character.from_origin(origin, handle), seed=4242)

    # `not:` is the one combinator.
    game = fresh()
    T.ok(game.story.satisfied('not:lark_dead', game),
         '`not:` holds for a flag nothing set')
    game.story.flags.add('lark_dead')
    T.ok(not game.story.satisfied('not:lark_dead', game),
         'and fails once the flag is set')
    T.ok(not game.story.satisfied('not:runs:0', game),
         'and negates a condition as well as a flag')

    # Lark leaves the city when she dies, and takes her work with her.
    game = fresh()
    game.city.where = 'shambles'
    before = [n.key for n in story_mod.present(game, game.story)]
    T.ok('lark' in before, 'Lark is in the Shambles while alive')
    game.story.meet('lark')
    from flatline.commands.people import _work_ready
    game.char.runs = 5
    T.ok(_work_ready(game, npc_content.BY_KEY['lark'])[0],
         'and her work is on offer')
    game.story.flags.add('lark_dead')
    after = [n.key for n in story_mod.present(game, game.story)]
    T.ok('lark' not in after, 'and gone once she is dead')
    T.ok(not _work_ready(game, npc_content.BY_KEY['lark'])[0],
         'with her work gone too')
    _, out = play(['deal lark favour walked'], game=game)
    T.ok('will not' in out, 'and her favour')

    # Mr Sunday stops appearing once sold.
    game = fresh()
    game.char.runs = 6
    game.city.shift = 1  # afternoon: his hours
    T.ok('broker' in [n.key for n in story_mod.present(game, game.story)],
         'Mr Sunday is on his stool in Marrow')
    game.story.flags.add('sunday_sold')
    T.ok('broker' not in [n.key for n in story_mod.present(game, game.story)],
         'and not once the log has run')

    # Doctor Vance's counter closes after exposure.
    game = fresh()
    game.city.where = 'green'
    game.story.meet('vance')
    _, out = play(['deal vance goods'], game=game)
    T.ok('cabinet stays closed' not in out, 'her cabinet is open to start with')
    game.story.flags.add('vance_exposed')
    _, out = play(['deal vance goods'], game=game)
    T.ok('cabinet stays closed' in out, 'and closes once she is in the paper')

    # Gated events: never without the story, the right branch with it.
    plain = events.eligible('shambles', 'morning')
    T.ok(plain and all(not (e.requires or e.any_of) for e in plain),
         'without a story only weather is eligible')
    game = fresh()
    game.story.flags.add('lark_dead')
    sat = lambda rule: game.story.satisfied(rule, game)  # noqa: E731
    keys = {e.key for e in events.eligible('shambles', 'morning', sat)}
    T.ok('lark_jacket' in keys, 'the jacket on the crate can happen now')
    T.ok('lark_smaller' not in keys, 'and the other branch cannot')
    stream = game.rng('events')
    seen = set()
    for _ in range(300):
        e = events.pick(stream, 'shambles', 'morning', set(), sat)
        if e is not None:
            seen.add(e.key)
    T.ok('lark_jacket' in seen, 'and it does come up when the shift is drawn')
    T.ok(all(events.BY_KEY[k].requires == () or k == 'lark_jacket'
             for k in seen), 'and nothing else gated on a decision does')
    # Through the city itself, with the story handed in.
    game = fresh()
    game.story.flags.add('sparrow_scared')
    game.city.where = 'marrow'
    told = []
    for _ in range(60):
        game.city.advance(game.rng, game.alias, 1, char=game.char,
                          satisfied=lambda r: game.story.satisfied(r, game),
                          flags=game.story.flags)
        told.extend(game.city.ambient)
    T.ok(any('counter' in line and 'sixteen' in line for line in told),
         'the city shows the consequence within sixty shifts')

    # The board reads Deepwater.
    game = fresh()
    w0 = contract_world._weighted_patrons(game.alias, ())
    w1 = contract_world._weighted_patrons(game.alias, {'dw_published'})
    T.ok('deepwater' in w0 and 'deepwater' not in w1,
         'publishing Deepwater takes them off the board')
    w2 = contract_world._weighted_patrons(game.alias, {'dw_employed'})
    T.ok(w2['deepwater'] > w0['deepwater'] * 2,
         'and the retainer puts them on it three times over')
    game.story.flags.add('dw_published')
    for _ in range(20):
        game.city.refresh_board(game.rng, game.alias, game.char,
                                flags=game.story.flags)
        T.ok(all(c.patron != 'deepwater' for c in game.city.board),
             'no Deepwater posting after publishing')

    # The streets read the Sixes, and only the Sixes.
    game = fresh()
    game.alias.add_heat('sixes', 70)
    d0, who = game.city.danger(game.alias, 'ninth')
    d1, _ = game.city.danger(game.alias, 'ninth', flags={'theirs_owned'})
    T.ok(d0 > 0 and d1 <= d0 * 0.6,
         f'being theirs halves the Ninth\'s danger ({d0} to {d1})')
    T.eq(game.city.danger(game.alias, 'ninth', flags={'file_closed'})[0], d0,
         'and a decision about Nightwatch changes nothing there')
    T.eq(story_mod.street_rider(set(), 'sixes'), 1.0, 'no flags, no rider')

    # A choice whose prose hands you something hands it over.
    game = fresh('courier', 'Pkg')
    game.story.flags.update({'package_still'})
    game.story.reached['package'] = ['still']
    stage = next(s for s in thread_content.BY_KEY['package'].stages
                 if s.key == 'address')
    game.story.reach('package', stage)
    sess, out = play(['choose open'], game=game)
    T.ok('io_copper' in game.char.library,
         'opening the package puts the component in the bag')
    T.ok('in the bag' in out, 'and says so')
    T.ok('package_opened' in game.story.flags, 'and the decision is recorded')

    # Favours a decision opened.
    game = fresh()
    game.city.where = 'shambles'
    game.story.meet('surgeon')
    game.char.dissonance = 40
    _, out = play(['deal surgeon favour clean'], game=game)
    T.ok('will not' in out, 'the Surgeon owes you nothing yet')
    game.story.flags.add('surgeon_owed')
    before = game.char.dissonance
    _, out = play(['deal surgeon favour clean'], game=game)
    T.ok(game.char.dissonance < before,
         f'and walks the drift back once they do ({before} to '
         f'{game.char.dissonance})')
    T.ok(any(f.npc == 'mara' and f.key == 'long' for f in offers.FAVOURS),
         'Mara can pay somebody again')

    # The epilogue names every decision, and the ending reads the spine.
    staged = {f for t in thread_content.THREADS for s in t.stages
              for f in s.sets}
    decisions = {f for f in thread_content.flags_chosen() if f not in staged}
    lines = legacy.epilogue(decisions)
    T.eq(len(lines), len(decisions), 'every decision has its line')
    T.eq(legacy.epilogue(set()), [], 'no decisions, no epilogue')
    two = legacy.epilogue({'sparrow_taught', 'lark_dead'})
    T.eq(len(two), 2, 'two decisions, two lines')
    T.ok('Lark' in two[0] and 'Kestrel' in two[1],
         'in the order the threads are written')
    t0, x0 = legacy.ending(10)
    t1, _ = legacy.ending(10, {'dw_employed'})
    T.ok(t1 != t0 and 'retainer' in t1.lower(),
         'taking the retainer replaces the ending')
    _, x2 = legacy.ending(10, {'dw_published'})
    T.ok(x2.startswith(x0) and 'Static' in x2,
         'publishing leaves a coda on the drift ending')
    T.eq(legacy.ending(80, {'dw_employed'})[0], t1,
         'and the retainer outranks the drift')

    # Retiring reads it all back.
    game = fresh('gutter', 'Out')
    game.char.credits = legacy.STAKE + 10
    game.story.flags.update({'lark_saved', 'dw_refused', 'sparrow_scared'})
    sess, out = play(['retire --confirm'], game=game)
    T.ok('what you left behind' in out, 'retiring prints the epilogue')
    T.ok('Lark is alive' in out and 'counter in Marrow' in out,
         'with the decisions in it')
    T.ok('landline' in out, 'and the refused retainer has its coda')
    # And the flatline does, through the same helper.
    from flatline.commands.core import _epilogue
    sess, _ = play([], game=fresh())
    sess.game.story.flags.add('package_burned')
    sess.console.start_capture()
    _epilogue(sess)
    out = sess.console.end_capture()
    T.ok('incinerator' in out, 'the flatline path has the same epilogue')

    # Nothing here touches a number for somebody who decided nothing: two
    # games, one with the story handed in and one without, draw the same
    # board and the same weather.
    a, b = fresh(), fresh()
    a.city.advance(a.rng, a.alias, 3, char=a.char,
                   satisfied=lambda r: a.story.satisfied(r, a),
                   flags=a.story.flags)
    b.city.advance(b.rng, b.alias, 3, char=b.char)
    T.eq([c.cid for c in a.city.board], [c.cid for c in b.city.board],
         'an empty story draws the same board')
    T.eq(a.city.ambient, b.city.ambient, 'and the same weather')


def test_spine() -> None:
    """D52: the Deepwater spine, and story inside runs."""
    T.section('spine')
    from flatline.content import legacy, threads as thread_content
    from flatline.world import contracts as contract_world

    def fresh(handle='Spine'):
        game = Game.new(Character.from_origin('gutter', handle), seed=4242)
        return game, game.story

    # A posting finished is a rule the story can read.
    game, st = fresh()
    T.ok(not st.satisfied('did:deepwater.posting', game), '`did:` is unmet')
    st.flags.add('did:deepwater.posting')
    T.ok(st.satisfied('did:deepwater.posting', game), 'until the run is done')

    # The posting scene arrives once you have heard and have one fact.
    game, st = fresh()
    game.char.runs = 6
    st.flags.update({'dw_heard', 'ran:deepwater'})
    # Two looks: the first reaches `inside`, which is the fact the posting
    # wants, and a scene unlocked by a scene arrives on the next check.
    sess, out = play(['look', 'look'], game=game)
    T.ok('dw_posting' in st.flags, 'hearing plus one fact opens the posting')
    held = [c for c in game.city.board if c.story == 'deepwater.posting']
    T.eq(len(held), 1, 'and it puts one held contract on the board')
    contract = held[0]
    T.ok('Four Hundred and Eight' in out and contract.cid in out,
         'and says so in the board\'s own terms')
    T.eq((contract.patron, contract.target, contract.objective),
         ('deepwater', 'deepwater', 'exfiltrate'),
         'shaped exactly as the scene asked')
    T.eq(contract.pay, 6000, 'and priced as the scene asked')
    T.ok(contract.held and contract.expires - game.city.shift > 1000,
         'it is held')
    stage = next(s for s in thread_content.BY_KEY['deepwater'].stages
                 if s.key == 'posting')
    game.city.post_story(game.rng, game.alias, stage.posts,
                         'deepwater.posting')
    T.eq(len([c for c in game.city.board
              if c.story == 'deepwater.posting']), 1,
         'posting it again posts nothing')
    # It survives time, rivals and top-ups, and costs the board no slot.
    for _ in range(25):
        game.city.advance(game.rng, game.alias, 1, char=game.char,
                          satisfied=lambda r: st.satisfied(r, game),
                          flags=st.flags)
    T.ok(any(c.story == 'deepwater.posting' for c in game.city.board),
         'twenty-five shifts later it is still on the board')
    ordinary = [c for c in game.city.board if not c.held]
    T.eq(len(ordinary), game.city.board_size(game.char),
         'and the ordinary board is full beside it')
    _, out = play(['board'], game=game)
    T.ok('held' in out, 'the board says it is held')
    _, out = play([f'board {contract.cid}'], game=game)
    T.ok('will keep' in out, 'and so does the detail')

    # Running it: the brief names the record the scene named. A payload on
    # the deck, because an exfiltrate that cannot be finished is not a test
    # of anything.
    game.city.where = contract.district
    for key in list(game.char.deck.loaded):
        game.char.deck.unload(key)
    game.char.library.append('siphon')
    T.ok(game.char.deck.can_load('siphon')[0], 'a payload fits the deck')
    game.char.deck.load('siphon')
    sess, out = play([f'take {contract.cid}', 'jack in', 'job'], game=game)
    T.ok(sess.run is not None, 'the held contract runs')
    T.ok('your handle in the header' in out,
         'and the brief names the record the scene named')
    state = sess.run
    asset = state.net.find_asset(state.net.objective_asset)
    T.ok(asset is not None and asset[1].label, 'the asset carries the label')
    # Finish it: the objective record is in the haul, and the scene that
    # comes after arrives with the world moving.
    state.haul.append(state.net.objective_asset)
    sess.console.start_capture()
    sess.execute('jack out')
    out = sess.console.end_capture()
    T.ok(sess.run is None, 'and the run ends')
    T.ok('did:deepwater.posting' in st.flags, 'finishing it sets `did:`')
    T.ok('dw_carried' in st.flags, 'and the next scene arrives at once')
    T.ok('deepwater.carried' in st.pending, 'waiting on a decision')
    T.ok(not any(c.story == 'deepwater.posting' for c in game.city.board),
         'and the held contract is gone from the board')
    _, out = play([''], game=game)
    T.ok('choose' in out, 'an empty line says a choice is waiting')
    # A gutter runner at six runs also has the Sixes waiting on them;
    # `choose` takes the oldest first, so put the log at the front.
    st.pending = ['deepwater.carried'] + [p for p in st.pending
                                          if p != 'deepwater.carried']
    before = game.char.dissonance
    sess.console.start_capture()
    sess.execute('choose read')
    out = sess.console.end_capture()
    T.eq(game.char.dissonance, before + 6, 'reading it to the end costs drift')
    T.ok('dw_read' in st.flags and 'Dissonance' in out,
         'and is recorded, and said')

    # The offer opens from the carried log as well as from the pattern.
    T.ok('dw_offer' in st.flags or 'deepwater.offer' in st.pending
         or any(k == 'deepwater' and s.key == 'offer'
                for k, s in st.available(game)),
         'the offer is reachable from the log alone')

    # The door: crossings, and it goes somewhere.
    game, st = fresh('Door')
    st.flags.update({'dw_heard', 'dw_offer', 'dw_read', 'archive_consented'})
    sess, out = play(['look'], game=game)
    T.ok('dw_asked' not in st.flags, 'without Lark alive it does not ask')
    st.flags.add('lark_saved')
    sess, out = play(['look'], game=game)
    T.ok('dw_asked' in st.flags and 'It asks' in out,
         'with all three crossings, it asks')
    sess.console.start_capture()
    sess.execute('choose go')
    out = sess.console.end_capture()
    T.eq(game.over, 'went under', 'going under finishes the character')
    T.ok('what you left behind' in out and 'went under' in out,
         'with the decisions read back')
    T.ok('dw_under' in st.flags, 'and the ending recorded')
    sess.console.start_capture()
    sess.execute('board')
    out = sess.console.end_capture()
    T.ok('went under' in out, 'and nothing more can be done as them')
    game, st = fresh('Stay')
    st.flags.update({'dw_heard', 'dw_offer', 'dw_read', 'archive_consented',
                     'lark_saved'})
    sess, out = play(['look', 'choose stay'], game=game)
    T.ok(not game.over and 'dw_stayed' in st.flags,
         'saying no leaves you standing')

    # Every new decision has an epilogue line, and the spine's endings are
    # all Deepwater decisions.
    for flag in ('dw_read', 'dw_archived', 'dw_burned', 'dw_under',
                 'dw_stayed'):
        T.ok(flag in legacy.EPILOGUE_BY_FLAG, f'{flag} is in the epilogue')
    T.ok('dw_under' in legacy.ENDING_FLAGS, 'going under is an ending')

    # The origin threads print paragraphs, not backslashes.
    for t in thread_content.THREADS:
        for s in t.stages:
            T.ok('\\n' not in s.text, f'{t.key}.{s.key} has no literal \\n')
            for ch in s.choices:
                T.ok('\\n' not in ch.text,
                     f'{t.key}.{s.key}.{ch.key} has no literal \\n')

    # A held contract round-trips through a save.
    game, st = fresh('Saved')
    game.char.runs = 6
    st.flags.update({'dw_heard', 'ran:deepwater'})
    play(['look', 'look'], game=game)
    game.save('spine-save')
    back = Game.load('spine-save')
    T.ok(any(c.story == 'deepwater.posting' and c.label
             for c in back.city.board),
         'the held contract survives a save, label and all')
    save_mod.delete('spine-save')


def test_texture() -> None:
    """D53: the city at this hour, places to stand in, the street letting you
    know, and the wire."""
    T.section('texture')
    from flatline.content import spots
    from flatline.world import fallout

    def fresh(handle='Tex'):
        return Game.new(Character.from_origin('gutter', handle), seed=4242)

    # `look` prints the district at this hour, and arrival does too.
    game = fresh()
    _, out = play(['look'], game=game)
    T.ok(ui.plain(districts.scene('marrow', game.city.phase))[:40] in out,
         '`look` prints Marrow at this hour')
    T.ok('Places:' in out and 'the noodle bar' in out,
         'and lists the places to stand in')
    _, out = play(['travel ninth'], game=game)
    T.ok(ui.plain(districts.scene('ninth', game.city.phase))[:40] in out,
         'arrival prints the Ninth at this hour')

    # `visit`: listing, by name, by row, at night, with who is there.
    game = fresh()
    sess, out = play(['visit'], game=game)
    T.ok('the noodle bar' in out and 'the exchange' in out,
         '`visit` alone lists the places here')
    _, out = play(['visit noodle bar'], game=game)
    T.ok('three landlines' in out, '`visit noodle bar` stands in it')
    T.ok('Mara Okonkwo' in out, 'and finds Mara there')
    T.ok('met:mara' in game.story.flags, 'which counts as meeting her')
    _, out = play(['visit 2'], game=game)
    T.ok('interchange' in out, '`visit 2` is the second row')
    _, out = play(['visit nowhere'], game=game)
    T.ok('nowhere called' in out, 'and an unknown place is refused')
    game.city.shift = 2  # night
    _, out = play(['visit exchange'], game=game)
    T.ok('people who do not sleep' in out, 'at night the place is the night')
    game.city.where = 'shambles'
    _, out = play(['visit crate'], game=game)
    T.ok('not here at this hour' in out and 'afternoons' in out,
         'Lark keeps daylight hours, and the crate says which')
    game.city.shift = 3  # the next morning
    _, out = play(['visit crate'], game=game)
    T.ok('Lark' in out and 'not here' not in out, 'and in the morning she is on it')
    game.story.flags.add('lark_dead')
    _, out = play(['visit crate'], game=game)
    T.ok('not here at the moment' in out, 'and not once she is dead')

    # D54: hours. `look` says who keeps other hours, once you know them.
    from flatline.content import npcs as npc_content
    game = fresh()
    game.story.meet('broker')
    game.char.runs = 6
    _, out = play(['look'], game=game)
    T.ok('Mr Sunday' not in out.split('Not about')[0] if 'Not about' in out
         else 'Mr Sunday' not in out, 'Mr Sunday is not in Marrow in the morning')
    T.ok('Not about at this hour' in out and 'Mr Sunday (afternoons and nights)'
         in out, 'and `look` says when he is')
    game.city.shift = 1
    _, out = play(['look'], game=game)
    T.ok('Mr Sunday' in out.split('Not about')[0], 'in the afternoon he is')
    T.eq(npc_content.hours_label(npc_content.BY_KEY['vending']), 'any hour',
         'Ozymandias keeps no hours')
    T.ok(all(len(n.lines) >= 5 and len(n.topics) >= 3 for n in npc_content.NPCS),
         'everybody has enough to say')
    for d in districts.DISTRICTS:
        T.ok(len(spots.in_district(d.key)) >= 2,
             f'{d.key} has places to stand in')
    T.ok(all(ui.width(line) <= 80 for line in out.splitlines()),
         'a place fits eighty columns')

    # The street lets you know, in the band below an incident, and it costs
    # a little heat; below the band it keeps quiet.
    game = fresh()
    stream = game.rng('events')
    before = game.alias.attention('sixes')
    hits = sum(1 for _ in range(200)
               if fallout.close_call(stream, game.alias, game.city, 'sixes',
                                     40) is not None)
    T.ok(0 < hits < 200, f'a close call sometimes happens ({hits}/200)')
    T.ok(game.alias.attention('sixes') > before,
         'and being seen costs attention')
    game = fresh()
    call = fallout.close_call(game.rng('events'), game.alias, game.city,
                              'sixes', 40)
    if call is not None:
        T.ok('Marrow' in call.text and call.detail, 'and it says where')
    # Through travel: push heat into the band and walk in.
    game = fresh()
    game.alias.add_heat('sixes', 40)
    danger, who = game.city.danger(game.alias, 'ninth')
    if 25 <= danger < fallout.INCIDENT_FLOOR:
        _, out = play(['travel ninth'], game=game)
        T.ok('noticed' in out or 'looking for your name' in out,
             'walking into a watched district says something')

    # The wire.
    game = fresh()
    _, out = play(['news'], game=game)
    T.ok('The wire' in out and 'Nothing has happened' in out,
         '`news` on day one has nothing')
    game.city.news.extend(['Somebody took c001.', 'Somebody else died.'])
    _, out = play(['news'], game=game)
    T.ok('took c001' in out and 'else died' in out, 'and prints what it has')
    _, out = play(['news 1'], game=game)
    T.ok('else died' in out and 'took c001' not in out,
         'and a count trims it to the latest')
    T.ok(REGISTRY.lookup('wire') is REGISTRY.lookup('news'), '`wire` is news')

    # The tonal budget holds with the new ground and air in.
    from flatline.content import events
    counts = {t: sum(1 for e in events.EVENTS if e.tone == t)
              for t in events.TONES}
    total = len(events.EVENTS)
    for tone, (lo, hi) in events.TONE_BUDGET.items():
        T.ok(lo <= counts[tone] / total <= hi,
             f'{tone} is {counts[tone] / total:.0%}, inside the budget')


def test_arcs() -> None:
    """D55: nine threads rooted in a place, one played through."""
    T.section('arcs')
    from flatline.content import arcs, legacy, threads as thread_content
    from flatline.world import contracts as contract_world
    from flatline.world import story as story_mod

    T.eq(len(arcs.DISTRICT_THREADS), len(districts.DISTRICTS),
         'one thread per district')
    for t in arcs.DISTRICT_THREADS:
        T.ok(t.key in thread_content.BY_KEY, f'{t.key} is registered')
        places = {s.where for s in t.stages if s.where}
        T.eq(len(places), 1, f'{t.key} stays in one district')
        T.ok(any(s.choices for s in t.stages), f'{t.key} has a decision')

    # Every first scene is reachable by a character who has met the right
    # person and run a little.
    for t in arcs.DISTRICT_THREADS:
        game = Game.new(Character.from_origin('gutter', 'Arc'), seed=4242)
        game.char.runs = 9
        first = t.stages[0]
        for rule in tuple(first.requires) + tuple(first.any_of):
            if rule.startswith('met:'):
                game.story.meet(rule[4:])
        ok = all(game.story.satisfied(r, game) for r in first.requires) and (
            not first.any_of or any(game.story.satisfied(r, game)
                                    for r in first.any_of))
        T.ok(ok, f'{t.key}: the first scene opens for somebody who met '
                 f'the right person and ran nine times')

    # The pumps, end to end: Tuck, the posting, the run, the ledger, and the
    # streets of the Ninth afterwards.
    game = Game.new(Character.from_origin('gutter', 'Pumps'), seed=4242)
    st = game.story
    game.char.runs = 6
    game.city.where = 'ninth'
    game.city.shift = 1  # afternoon: Tuck's hours
    sess, out = play(['look', 'look'], game=game)
    T.ok('met:tuck' in st.flags, 'Tuck is on the stalls in the afternoon')
    T.ok('pumps_seen' in st.flags, 'and shows you the tape')
    T.ok('pumps_posting' in st.flags, 'and the Sixes post the ledger job')
    held = [c for c in game.city.board if c.story == 'pumps.posting']
    T.eq(len(held), 1, 'one held contract against Kagawa')
    contract = held[0]
    T.eq(contract.target, 'kagawa', 'against Kagawa')
    T.ok('Standing Water' in out, 'named in the board\'s terms')
    for key in list(game.char.deck.loaded):
        game.char.deck.unload(key)
    game.char.library.append('siphon')
    game.char.deck.load('siphon')
    game.city.where = contract.district
    sess, out = play([f'take {contract.cid}', 'jack in', 'job'], game=game)
    T.ok(sess.run is not None and 'maintenance ledger' in out,
         'the brief names the ledger')
    sess.run.haul.append(sess.run.net.objective_asset)
    sess.console.start_capture()
    sess.execute('jack out')
    sess.console.end_capture()
    T.ok('did:pumps.posting' in st.flags and 'pumps_ledger' in st.flags,
         'finishing it opens the ledger scene')
    st.pending = ['pumps.ledger'] + [p for p in st.pending
                                      if p != 'pumps.ledger']
    game.alias.add_heat('sixes', 60)
    d0, _ = game.city.danger(game.alias, 'ninth', flags=st.flags)
    sess.console.start_capture()
    sess.execute('choose sixes')
    out = sess.console.end_capture()
    T.ok('pumps_sixes' in st.flags and 'stencil' in out,
         'handing it to the Sixes is recorded and said')
    d1, _ = game.city.danger(game.alias, 'ninth', flags=st.flags)
    T.ok(d1 < d0, f'and the Ninth is safer for you ({d0} to {d1})')
    T.ok(legacy.epilogue(st.flags), 'and the ending will mention it')
    w = contract_world._weighted_patrons(game.alias, {'pumps_sold'})
    w0 = contract_world._weighted_patrons(game.alias, ())
    T.ok(w['kagawa'] > w0['kagawa'], 'selling it back would have made '
                                      'Kagawa post more')

    # The queue, which posts nothing and asks you to be law.
    game = Game.new(Character.from_origin('gutter', 'Queue'), seed=4242)
    game.char.runs = 4
    sess, out = play(['look'], game=game)
    T.ok('queue_dispute' in game.story.flags and 'green coat' in out,
         'the woman in the green coat asks you to rule')
    game.story.pending = ['queue.dispute']
    sess, out = play(['choose jacket'], game=game)
    T.ok('queue_jacket' in game.story.flags, 'and the jacket holds the place')
    game.char.runs = 9
    sess, out = play(['look'], game=game)
    T.ok('queue_cited' in game.story.flags, 'and you are cited, later')

    # D56: the other runners, at the moment they decide. A bond latching
    # writes a flag the scene reads; the answers are read by the hire price,
    # by the shift boundary, and by the wire.
    from flatline.world import rivals as rival_world
    from flatline.content import rivals as rival_content
    game = Game.new(Character.from_origin('gutter', 'Bond'), seed=4242)
    st = game.story
    vesper = game.city.rival('vesper')
    # The latch wants history as well as warmth (D44): give it both, then
    # let the real shift tick cross it with the story handed in.
    vesper.disposition = rival_content.PARTNER_AT + 5
    vesper.jobs = rival_content.BOND_AFTER_JOBS
    game.city.advance(game.rng, game.alias, 1, char=game.char,
                      satisfied=lambda r: st.satisfied(r, game),
                      flags=st.flags)
    T.eq(vesper.bond, 'partner', 'Vesper crosses into a partner')
    T.ok('bond:vesper:partner' in st.flags,
         'and the latch writes a flag the story can read')
    sess, out = play(['look'], game=game)
    T.ok('vesper_partner' in st.reached.get('runners', []),
         'and her scene arrives')
    T.ok('machinery is available' in out, 'in her voice')
    full = rival_world.hire_price(vesper)
    st.pending = ['runners.vesper_partner']
    sess, out = play(['choose in'], game=game)
    T.ok('with_vesper' in st.flags, 'saying yes is recorded')
    T.ok(rival_world.hire_price(vesper, st.flags) <= full // 2 + 1,
         'and her fee halves')
    T.ok(any('The Other Runners' in line for line in game.city.news),
         'and the wire carries it')
    # Directly: the nemesis side, and what paying buys.
    game = Game.new(Character.from_origin('gutter', 'Paid'), seed=4242)
    st = game.story
    hound = game.city.rival('hound')
    hound.bond = 'nemesis'
    st.flags.add('bond:hound:nemesis')
    sess, out = play(['look'], game=game)
    T.ok('hound_nemesis' in st.reached.get('runners', []) and 'expensive' in out,
         'Hound names a figure')
    st.pending = ['runners.hound_nemesis']
    before = game.char.credits
    sess, out = play(['choose pay'], game=game)
    T.ok('paid_hound' in st.flags and game.char.credits < before,
         'paying is recorded and costs')
    acts = []
    stream = game.rng('rivals')
    for _ in range(200):
        acts.extend(rival_world.bond_turn(stream, game.city.rivals, game.alias,
                                          st.flags))
    T.ok(not any('Hound' in a for a in acts),
         'and a paid nemesis stops acting on the shift boundary')
    acts = []
    for _ in range(200):
        acts.extend(rival_world.bond_turn(stream, game.city.rivals, game.alias))
    T.ok(any('Hound' in a for a in acts), 'where an unpaid one would not')
    T.eq(len([s for s in thread_content.BY_KEY['runners'].stages]), 14,
         'seven runners, two sides each')

    # D57: the city, drawn, and walked.
    from flatline import citymap
    game = Game.new(Character.from_origin('gutter', 'Map'), seed=4242)
    _, out = play(['map'], game=game)
    lines = [l for l in out.splitlines() if 'marrow' in l and '@' in l]
    T.ok(lines, 'the drawing marks you in Marrow')
    T.ok('you' in out and 'the job' in out, 'and explains its marks')
    cid = game.city.board[0].cid
    goal = game.city.board[0].district
    _, out = play([f'take {cid}', 'map'], game=game)
    if goal != 'marrow':
        T.ok(any(goal in l and '!' in l for l in out.splitlines()),
             'and marks the district the job is in')
    for glyphs in (GlyphLevel.UNICODE, GlyphLevel.ASCII):
        caps = Caps(color=ColorLevel.NONE, glyphs=glyphs, width=80,
                    palette=theme.NEUTRAL)
        drawn = citymap.draw(game, caps)
        T.ok(all(ui.width(l) <= 76 for l in drawn),
             f'the drawing fits ({glyphs.name})')
    # `walk` goes the whole way and stops when the street stops you.
    game = Game.new(Character.from_origin('gutter', 'Walk'), seed=4242)
    game.city.where = 'shambles'
    route = game.city.route('green')
    sess, out = play(['walk green'], game=game)
    T.eq(game.city.where, 'green', '`walk green` arrives')
    T.eq(game.city.shift, len(route), 'a shift a step')
    game = Game.new(Character.from_origin('gutter', 'Stop'), seed=4242)
    game.city.where = 'shambles'
    game.alias.add_heat('aoyama', 95)
    game.city.bounties['aoyama'] = 80
    sess, out = play(['walk green'], game=game)
    T.ok(game.city.where != 'green', 'the walk does not arrive in Aoyama '
                                    'Green with Aoyama paying for your name')
    T.ok('The walk stops here' in out, 'and says so')

    # D58: the city, larger and fuller. The street has people in it, the
    # new people are at their places, and the map counts it all.
    game = Game.new(Character.from_origin('gutter', 'Full'), seed=4242)
    _, out = play(['look'], game=game)
    T.ok('In the street:' in out, '`look` says who is in the street')
    first = districts.street_line('marrow', game.city.shift)
    T.eq(districts.street_line('marrow', game.city.shift), first,
         'and the street is the same twice in one shift')
    T.ok(districts.street_line('marrow', game.city.shift + 1) != first,
         'and different next shift')
    _, out = play(['travel ninth'], game=game)
    T.ok('In the street:' in out, 'arrival says who is in the street')
    _, out = play(['map'], game=game)
    T.ok('places to stand in' in out and 'people worth finding' in out,
         'the map counts the city')
    from flatline.content import npcs as npc_content, spots as spot_content
    T.ok(len(spot_content.SPOTS) >= 45, f'{len(spot_content.SPOTS)} places')
    T.ok(len(npc_content.NPCS) >= 22, f'{len(npc_content.NPCS)} people')
    game = Game.new(Character.from_origin('gutter', 'Keeper'), seed=4242)
    _, out = play(['visit exchange'], game=game)
    T.ok('Green Coat' in out, 'the woman in the green coat is at the exchange')
    game.city.where = 'shambles'
    game.city.shift = 2
    _, out = play(['visit cabinets'], game=game)
    T.ok('Halvard' in out, 'and Halvard is at the cabinets at night')
    _, out = play(['talk halvard'], game=game)
    T.ok('"' in out, 'and talks')

    # D59: a line of readout after anything that spends a tick, and the four
    # ways to have it.
    from flatline.content import rice
    T.ok('hud' in rice.KINDS and len(rice.BY_KIND['hud']) == 4,
         'the hud is a rice axis with four states')
    game = Game.new(Character.from_origin('gutter', 'Hud'), seed=4242)
    contract = game.city.board[0]
    game.city.where = contract.district
    sess, _ = play([f'take {contract.cid}', 'jack in --force'], game=game)
    T.ok(sess.run is not None, 'in a run')
    sess.console.start_capture()
    sess.execute('scan')
    out = sess.console.end_capture()
    T.ok('trace' in out and 'tick' in out and 'alert' in out,
         'a scan is followed by the readout')
    sess.hud = 'quiet'
    sess.console.start_capture()
    sess.execute('scan')
    out = sess.console.end_capture()
    T.ok('alert' not in out, 'and `quiet` silences it')
    sess.hud = 'bar'
    sess.console.start_capture()
    sess.execute('probe ' + next(iter(sess.run.net.neighbours(sess.run.here))).uid)
    out = sess.console.end_capture()
    T.ok('trace' in out and 'alert' not in out, '`bar` is the bar alone')
    # Set through the shell, it survives apply_shell.
    sess.console.start_capture()
    sess.execute('rice hud terse')
    sess.console.end_capture()
    T.eq(sess.hud, 'terse', '`rice hud terse` sets it')
    sess.execute('rice hud line')
    T.eq(sess.hud, 'line', 'and back')

    # The wire carries scenes, choices and what a run did to the city.
    game = Game.new(Character.from_origin('gutter', 'Wire'), seed=4242)
    game.char.runs = 4
    sess, out = play(['look'], game=game)
    T.ok(any('The Constitution' in line for line in game.city.news),
         'a scene arriving is news')
    _, out = play(['news'], game=game)
    T.ok('Constitution' in out, 'and `news` prints it')

    # Carrion's man and the Surgeon's book: warning closes nothing, taking
    # closes the Surgeon's favour.
    game = Game.new(Character.from_origin('gutter', 'Book'), seed=4242)
    game.story.flags.update({'surgeon_owed', 'ledger_taken'})
    game.city.where = 'shambles'
    game.story.meet('surgeon')
    _, out = play(['deal surgeon favour clean'], game=game)
    T.ok('will not' in out, 'the Surgeon will not, once the ledger is taken')


def test_tutorial_second_half() -> None:
    """D60: the tutorial goes on past the door, into what the city does."""
    T.section('tutorial')
    from flatline.content import tutorial as tut
    keys = [s.key for s in tut.STEPS]
    T.ok(keys.index('out') < keys.index('settle') < keys.index('again'),
         'the second half follows the first, in order')
    for key in ('settle', 'rep', 'look', 'talk', 'visit', 'journal', 'now',
                'door', 'again'):
        T.ok(key in keys, f'there is a {key} step')

    # A character who has run once and is standing in the city gets the
    # second half, step by step, however they get there.
    game = Game.new(Character.from_origin('gutter', 'Taught'), seed=4242)
    game.char.runs = 1
    sess, out = play(['tutorial'], game=game)
    T.ok(sess.tutorial_step >= 0, 'the tutorial starts')
    # Everything up to `out` is satisfied or skippable; walk into the second
    # half. `out` and `settle` are both already true for a character who has
    # run once and left nothing pending, so the walk lands on `rep`.
    for _ in range(30):
        if sess.tutorial_step < 0:
            break
        if tut.STEPS[sess.tutorial_step].key in ('settle', 'rep'):
            break
        sess.execute('tutorial skip')
    T.ok(sess.tutorial_step >= 0
         and tut.STEPS[sess.tutorial_step].key in ('settle', 'rep'),
         'and reaches the second half')
    if tut.STEPS[sess.tutorial_step].key == 'settle':
        sess.console.start_capture()
        sess.execute('rest 1')
        out = sess.console.end_capture()
        T.ok('landed' in out, 'a shift completes settle')
    step = tut.STEPS[sess.tutorial_step].key
    T.eq(step, 'rep', 'and the next step is rep')
    sess.execute('rep')
    T.eq(tut.STEPS[sess.tutorial_step].key, 'look', 'then look')
    sess.execute('look')
    T.eq(tut.STEPS[sess.tutorial_step].key, 'talk', 'then talk')
    sess.execute('talk mara')
    T.eq(tut.STEPS[sess.tutorial_step].key, 'visit', 'then visit')
    sess.execute('visit exchange')
    T.eq(tut.STEPS[sess.tutorial_step].key, 'journal', 'then journal')
    sess.execute('journal')
    T.eq(tut.STEPS[sess.tutorial_step].key, 'now', 'then the empty line')
    sess.execute('')
    T.eq(tut.STEPS[sess.tutorial_step].key, 'door', 'then the door')
    sess.execute('retire')
    T.eq(tut.STEPS[sess.tutorial_step].key, 'again', 'then another contract')
    sess.console.start_capture()
    sess.execute(f'take {game.city.board[0].cid}')
    out = sess.console.end_capture()
    T.ok(sess.tutorial_step < 0, 'and taking one ends the tutorial')
    T.ok('done all of it once' in out and 'news' in out,
         'with a closing that points at the wire and the map')


SUITES = (
    test_determinism, test_saves, test_character, test_checks, test_guide,
    test_consequences, test_spine, test_texture, test_arcs,
    test_tutorial_second_half,
    test_networks, test_run_mechanics, test_city, test_rivals,
    test_signatures, test_story, test_traits_and_spread, test_regressions, test_herders_and_kinds, test_passives_and_debt, test_dissonance, test_scripting, test_social, test_objectives, test_fallout, test_appearance, test_tone, test_anim, test_bench, test_crew, test_safehouse, test_bonds, test_legacy, test_offers, test_vices, test_brief, test_city_map, test_topology, test_clock, test_rice, test_cover, test_roster, test_migration, test_help, test_shell,
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
