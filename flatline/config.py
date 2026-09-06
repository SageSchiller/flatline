"""App-wide constants and the on-disk layout.

Small on purpose. Anything that grows a policy belongs with that policy, not
here. Balance numbers in particular live with the system they balance, because
a constant named `TRACE_PER_TICK` sitting next to `APP_NAME` is a number nobody
can justify six months later.
"""

from __future__ import annotations

import os
from pathlib import Path

APP_NAME = 'flatline'
APP_TITLE = 'FLATLINE'

#: Shown under the title on the splash. Joined with a separator at render time
#: rather than baked in, because a literal '·' here would survive into the
#: ASCII rung of D16.
TAGLINE_PARTS = ('everything you do is loud', 'the city remembers')

#: Save format version. Bumped whenever the shape of a save changes; `save.py`
#: owns the migration chain from 1 up to this number. Never reuse a number.
SCHEMA = 4

#: D16: content is authored to fit here and `test.py` asserts nothing overflows.
MIN_COLS = 80
MIN_ROWS = 24

#: Wrap width for prose output. Narrower than MIN_COLS because text set to the
#: full terminal width is unreadable, and because the prompt and status lines
#: need to sit visually inside the same column that paragraphs do.
TEXT_WIDTH = 76

#: The widest a table may grow on a terminal that has the room (D182). Prose
#: stays at TEXT_WIDTH, because sixty to eighty characters a line is the
#: readable range and a wider paragraph reads worse, not better. A table is
#: columns, columns truncate at eighty, and they get whatever the terminal
#: has, up to this.
TABLE_WIDTH = 120

#: D3: the world seed is user-facing. Sixteen bits keeps it typeable and
#: shareable; the RNG stretches it internally so the small space costs nothing.
SEED_MAX = 65535


def data_dir() -> Path:
    """Where state lives, per D7. Honours XDG, falls back to the spec default."""
    base = os.environ.get('XDG_DATA_HOME') or (Path.home() / '.local' / 'share')
    return Path(base) / APP_NAME


def save_path(slot: str = 'default') -> Path:
    return data_dir() / f'save-{slot}.json'


def meta_path() -> Path:
    """Cross-character records and unlocks. Survives character death (D6)."""
    return data_dir() / 'meta.json'


def history_path() -> Path:
    """Readline history. Kept beside the saves so one uninstall gets it all."""
    return data_dir() / 'history'
