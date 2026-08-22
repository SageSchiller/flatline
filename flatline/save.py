"""Persistence, per D7. Versioned JSON in the XDG data directory.

Two things here are load-bearing.

**Atomic writes.** Saves go to a temp file in the same directory and are then
renamed over the target. A game that autosaves on shift boundaries will
eventually be killed mid-write, and a truncated JSON file is a dead character.
`os.replace` is atomic on POSIX and on Windows, so the worst case becomes
"lost the last save" rather than "lost everything".

**Forward migrations.** Every save records the schema it was written under, and
loading runs it forward through every migration since. The chain is append-only
and each step is a pure dict-to-dict function, which keeps them testable and
keeps `test.py` able to prove that a save written under version 1 still opens.
The alternative, refusing to load old saves, means a refactor can cost somebody
a forty-hour character, and that is not an acceptable trade for a game.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .config import SCHEMA, data_dir, meta_path, save_path


class SaveError(Exception):
    """Anything that stops a save being read. Always shown to the player."""


# --------------------------------------------------------------------------
# migrations
# --------------------------------------------------------------------------

#: version -> function taking a save at that version and returning one at
#: version + 1. Append only; never renumber, never edit a shipped step.
MIGRATIONS: dict[int, Callable[[dict], dict]] = {}


def migration(from_version: int):
    def deco(fn: Callable[[dict], dict]):
        if from_version in MIGRATIONS:
            raise RuntimeError(f'duplicate migration from v{from_version}')
        MIGRATIONS[from_version] = fn
        return fn
    return deco


@migration(1)
def _v1_to_v2(data: dict) -> dict:
    """Phase 4 added rivals, icons, and bounties.

    A schema-1 save predates all three. The rules for filling them in are the
    same rules a new game uses, so a character opened after the upgrade finds a
    city with the standard runner pool in it and themselves wearing the icon
    their deck shipped with. Nothing is invented that the player would notice
    as wrong; they simply arrive in a slightly larger world.
    """
    from .content import icons as icon_content
    from .world import rivals as rival_mod

    char = dict(data.get('character') or {})
    char.setdefault('icon', icon_content.DEFAULT)
    char.setdefault('icons', [icon_content.DEFAULT])
    data['character'] = char

    city = dict(data.get('city') or {})
    if not city.get('rivals'):
        city['rivals'] = [r.to_dict() for r in rival_mod.seed_pool()]
    city.setdefault('bounties', {})
    data['city'] = city
    return data


@migration(2)
def _v2_to_v3(data: dict) -> dict:
    """Phase 6 gave characters a face.

    A schema-2 character has no `look` at all. Filling in the flat default
    would technically work and would be wrong: it would hand a Chromed
    survivor the same unremarkable build and plain face as a Ghost, and the
    first thing they would see on upgrading is a description of somebody
    else. Their origin's starting look is the honest answer, because it is
    exactly what the character would have been created with.

    Marks are left empty on purpose. They are a record of what has been done
    to this character, and inventing that record retroactively would be a
    lie in the one part of the system whose whole job is not to be chosen.
    """
    from .content import appearance, origins

    char = dict(data.get('character') or {})
    if not char.get('look'):
        origin = origins.BY_KEY.get(char.get('origin') or '')
        char['look'] = {**appearance.default(),
                        **(origin.look if origin else {})}
    char.setdefault('marks', [])
    data['character'] = char
    return data


@migration(3)
def _v3_to_v4(data: dict) -> dict:
    """Phase 7 gave the city three ways to borrow against your future.

    A schema-3 character has never taken anything and owes nobody, which is
    also what an empty chem block and an empty stash mean, so this is one of
    the rare migrations where the honest answer is the default one. It exists
    anyway rather than leaning on `from_dict` defaults, because the chain is
    what says which builds a save has been through, and a version that quietly
    changed shape without a step in it is a version nobody can reason about
    later.
    """
    from .content import drugs

    char = dict(data.get('character') or {})
    char.setdefault('chem', drugs.blank())
    char.setdefault('stash', {})
    data['character'] = char
    debt = dict(data.get('debt') or {})
    # Debts written before lenders had terms all ran at the house rate, which
    # is what the constants still are, so leaving these unset is correct.
    debt.setdefault('rate', 0.0)
    debt.setdefault('grace', 0)
    data['debt'] = debt
    return data


def migrate(data: dict) -> dict:
    """Bring a save up to the current schema, or explain why it cannot be."""
    version = int(data.get('schema', 0))
    if version > SCHEMA:
        raise SaveError(
            f'this save was written by a newer version of the game '
            f'(schema {version}, this build understands {SCHEMA})')
    while version < SCHEMA:
        step = MIGRATIONS.get(version)
        if step is None:
            raise SaveError(f'no migration path from schema {version} to {SCHEMA}')
        data = step(dict(data))
        version += 1
        data['schema'] = version
    return data


# --------------------------------------------------------------------------
# io
# --------------------------------------------------------------------------


def _write_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix='.tmp-', suffix='.json')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def write(data: dict, slot: str = 'default') -> Path:
    payload = dict(data)
    payload['schema'] = SCHEMA
    path = save_path(slot)
    _write_atomic(path, payload)
    return path


def read(slot: str = 'default') -> dict:
    path = save_path(slot)
    if not path.exists():
        raise SaveError(f'no save at {path}')
    try:
        raw = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        raise SaveError(f'{path} could not be read: {e}') from e
    if not isinstance(raw, dict):
        raise SaveError(f'{path} is not a save file')
    return migrate(raw)


def export_to(data: dict, target: Path) -> Path:
    """Write a save to a path of the player's choosing.

    Saves live in the XDG data directory, which is correct and is also the one
    place a player will not think to back up. An exported file is an ordinary
    save: same schema, same migrations, so a copy made today still opens after
    the format moves on.
    """
    target = Path(target).expanduser()
    if target.is_dir():
        raise SaveError(f'{target} is a directory; give me a filename')
    payload = dict(data)
    payload['schema'] = SCHEMA
    try:
        _write_atomic(target, payload)
    except OSError as e:
        raise SaveError(f'could not write {target}: {e}') from e
    return target


def import_from(source: Path) -> dict:
    """Read a save from anywhere, migrating it forward like any other."""
    source = Path(source).expanduser()
    if not source.exists():
        raise SaveError(f'no file at {source}')
    if source.is_dir():
        raise SaveError(f'{source} is a directory, not a save')
    try:
        raw = json.loads(source.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        raise SaveError(f'{source} could not be read: {e}') from e
    if not isinstance(raw, dict) or 'character' not in raw:
        raise SaveError(f'{source} is not a flatline save')
    return migrate(raw)


def exists(slot: str = 'default') -> bool:
    return save_path(slot).exists()


def delete(slot: str = 'default') -> None:
    try:
        save_path(slot).unlink()
    except FileNotFoundError:
        pass


def slots() -> list[str]:
    d = data_dir()
    if not d.exists():
        return []
    return sorted(p.stem[len('save-'):] for p in d.glob('save-*.json'))


# --------------------------------------------------------------------------
# the roster: characters, addressed by who they are
# --------------------------------------------------------------------------

#: Characters the game will list. A cap, not a limit on how many can exist:
#: it stops a directory somebody has been scripting against from printing two
#: hundred lines when they ask who they have.
ROSTER_MAX = 40


def slot_for(handle: str, taken: list[str] | None = None) -> str:
    """A slot name derived from a handle, unique against what already exists.

    Everybody used to share one slot called 'default', which meant making a
    second character wrote over the first one at the next autosave. Nothing
    warned, because from the save layer's point of view nothing unusual had
    happened. Filing a character under their own name is what makes having two
    of them possible at all.
    """
    keep = '-_'
    base = ''.join(ch if (ch.isalnum() or ch in keep) else '-'
                   for ch in handle.strip().lower()).strip('-')
    base = base or 'runner'
    existing = set(taken if taken is not None else slots())
    if base not in existing:
        return base
    n = 2
    while f'{base}-{n}' in existing:
        n += 1
    return f'{base}-{n}'


@dataclass(frozen=True, slots=True)
class Entry:
    """One line of the roster, cheap enough to build for every save at once."""
    slot: str
    handle: str
    #: Empty when the save is unreadable, which is the whole reason this is a
    #: summary rather than a loaded Game: one corrupt file must not be able to
    #: stop the player seeing the other five characters they have.
    broken: str = ''
    alias: str = ''
    origin: str = ''
    day: int = 0
    phase: str = ''
    where: str = ''
    runs: int = 0
    credits: int = 0
    dissonance: int = 0
    #: Non-empty when this character is finished. They stay on the roster:
    #: a list you can only see the living on is a list that quietly deletes
    #: your history the moment it stops being useful.
    over: str = ''
    #: Seconds since the epoch, for ordering. Most recently played first.
    played: float = 0.0

    @property
    def finished(self) -> bool:
        return bool(self.over)


def peek(slot: str) -> Entry:
    """Summarise one save, for a roster line.

    Builds the real Game rather than reading fields out of the JSON. A
    summary that picks its own way through the save format is a second,
    undeclared copy of the schema, and it goes wrong silently the first time
    a field moves: the roster would keep printing, with the wrong day on it.

    Anything that goes wrong is caught and reported on the entry instead of
    raised, because the roster is exactly the screen a player goes to when
    something has gone wrong, and one bad file must not be able to hide the
    other five characters they have.
    """
    from .game import Game

    try:
        mtime = save_path(slot).stat().st_mtime
    except OSError:
        mtime = 0.0
    try:
        game = Game.load(slot)
    except Exception as e:  # noqa: BLE001
        return Entry(slot=slot, handle=slot, broken=str(e) or type(e).__name__,
                     played=mtime)
    char, city = game.char, game.city
    return Entry(
        slot=slot,
        handle=char.handle,
        alias=game.alias.name,
        origin=char.origin,
        day=city.day,
        phase=city.phase,
        where=city.district.name,
        runs=char.runs,
        credits=char.credits,
        dissonance=char.dissonance,
        over=game.over,
        played=mtime)


def roster() -> list[Entry]:
    """Every character on this machine, most recently played first."""
    entries = [peek(slot) for slot in slots()]
    entries.sort(key=lambda e: e.played, reverse=True)
    return entries[:ROSTER_MAX]


def find(handle: str) -> list[Entry]:
    """Roster entries matching a handle or a slot name, case-insensitively.

    Returns every match rather than the best one, so the caller can tell the
    player about an ambiguity instead of guessing which of their two
    characters called Vex they meant.
    """
    want = handle.strip().lower()
    if not want:
        return []
    exact = [e for e in roster()
             if want in (e.handle.lower(), e.slot.lower())]
    if exact:
        return exact
    return [e for e in roster()
            if e.handle.lower().startswith(want) or e.slot.startswith(want)]


# --------------------------------------------------------------------------
# meta: survives character death, per D6
# --------------------------------------------------------------------------

META_DEFAULT = {
    'schema': SCHEMA,
    'characters_created': 0,
    'flatlines': 0,
    'best_credits': 0,
    'runs_completed': 0,
    'seeds_played': [],
    # Counters the rice catalogue unlocks against. All of them are here rather
    # than in the save on purpose: the deck's interface belongs to the player
    # and not to the character, and it has to survive a flatline. You lose
    # everything else; the terminal you spent a week getting right is still
    # yours when you sit down with somebody new.
    'clean_runs': 0,
    'black_ice_survived': 0,
    'deepest_drift': 0,
    'districts_seen': 0,
    'bounties_taken': 0,
    'threads_closed': 0,
    'best_standing': 0,
    'errands_done': 0,
    #: `kind:key` for everything earned, so a new unlock can be announced once.
    'unlocked': [],
    #: What the shell currently looks like. See `content/rice.py`.
    'shell': {},
    #: The one thing the last character left, waiting for the next one to be
    #: made. See `content/legacy.py`. Cleared when it is claimed, so an
    #: inheritance arrives once and belongs to whoever was next.
    'estate': {},
    #: Handles of everybody who has ended here, and how. The city remembering
    #: you is the game's whole thesis, and it forgot every character the
    #: moment they stopped breathing; this is what a later runner runs into.
    'gone': [],
}

#: How many of the departed the city keeps talking about. A scrollback rather
#: than a graveyard: forty handles is a list, six is a reputation.
GONE_KEPT = 6


def high_water(**values) -> dict:
    """Record counters that only ever go up, and persist if any moved.

    Separate from `bump_meta` because these are maxima rather than totals:
    reaching 60 Dissonance twice is not 120 Dissonance, and writing the file
    on every shift when nothing changed is a lot of fsync for nothing.
    """
    meta = read_meta()
    changed = False
    for key, value in values.items():
        if value > (meta.get(key) or 0):
            meta[key] = value
            changed = True
    if changed:
        write_meta(meta)
    return meta


def read_meta() -> dict:
    path = meta_path()
    if not path.exists():
        return dict(META_DEFAULT)
    try:
        raw = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        # Meta is a nicety, not a character. A corrupt one is reset silently
        # rather than blocking play, which is the opposite of the save policy
        # above and deliberately so.
        return dict(META_DEFAULT)
    out = dict(META_DEFAULT)
    out.update(raw if isinstance(raw, dict) else {})
    return out


def write_meta(data: dict) -> None:
    _write_atomic(meta_path(), data)


def leave_estate(bequest: str, handle: str, how: str, **detail) -> dict:
    """Record what a character left behind, for whoever is made next.

    One estate at a time on purpose. Two characters in a row going badly
    should not stack two inheritances onto the third; what is waiting is what
    the *last* person left, which is also how it works when it happens to
    people.
    """
    meta = read_meta()
    meta['estate'] = {'bequest': bequest, 'handle': handle, 'how': how,
                      **detail}
    gone = [g for g in (meta.get('gone') or []) if g.get('handle') != handle]
    gone.append({'handle': handle, 'how': how})
    meta['gone'] = gone[-GONE_KEPT:]
    write_meta(meta)
    return meta


def claim_estate() -> dict:
    """Take whatever is waiting, and clear it. Empty when there is nothing."""
    meta = read_meta()
    estate = dict(meta.get('estate') or {})
    if estate:
        meta['estate'] = {}
        write_meta(meta)
    return estate


def the_departed() -> list[dict]:
    """Everybody who has ended here, most recent last."""
    meta = read_meta()
    return [g for g in (meta.get('gone') or [])
            if isinstance(g, dict) and g.get('handle')]


def bump_meta(**deltas) -> dict:
    """Increment counters and persist. Values that are not numbers are set."""
    meta = read_meta()
    for k, v in deltas.items():
        if isinstance(v, (int, float)) and isinstance(meta.get(k), (int, float)):
            meta[k] = meta[k] + v
        else:
            meta[k] = v
    write_meta(meta)
    return meta
