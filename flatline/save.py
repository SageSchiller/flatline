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
# meta: survives character death, per D6
# --------------------------------------------------------------------------

META_DEFAULT = {
    'schema': SCHEMA,
    'characters_created': 0,
    'flatlines': 0,
    'best_credits': 0,
    'runs_completed': 0,
    'seeds_played': [],
}


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
