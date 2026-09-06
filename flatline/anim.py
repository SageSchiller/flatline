"""Motion, and the title card.

Nothing in this file is allowed to matter. Every effect here degrades to a
static frame, every static frame degrades to plain text, and the game is
identical either way. That is the rule that makes it safe to have at all: a
terminal game that needs its animation to be playable is a terminal game that
breaks over ssh, in a pipe, in a CI log, and in `test.py`.

The gate is `can_animate`. It wants a real tty, colour, and a console that is
not capturing, and all three have to be true. In every other case the boot
sequence prints its last frame and returns immediately, which is why the test
harness can drive `boot` a thousand times without sleeping once.

**Cursor state is restored in a `finally`.** An animation that exits through
Ctrl-C with the cursor still hidden leaves the player's shell broken after the
process is gone, and they will not connect that to this program.

Skipping is Ctrl-C. It is caught, it jumps to the final frame, and it does not
propagate: interrupting the intro means "get on with it", not "quit", and a
player who has seen this forty times should not have to be told how to escape
it. `--no-intro` and `FLATLINE_NO_INTRO` skip it before it starts.

The randomness here is a private `random.Random`. It must never touch the
game's streams: D3 says a world is reproducible from its seed, and an
animation that consumed entropy would mean the number of times you watched the
intro changed which contracts appeared on the board.
"""

from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass

from .theme import Palette
from .ui import Caps, ColorLevel, GlyphLevel

# --------------------------------------------------------------------------
# the mark
# --------------------------------------------------------------------------

#: Seven columns per letter, six rows, two-cell strokes. Sized so the whole
#: word lands in 63 columns and still fits a standard 80-column terminal with
#: room to breathe.
_GLYPHS: dict[str, tuple[str, ...]] = {
    'F': ('███████', '██     ', '██████ ', '██     ', '██     ', '██     '),
    'L': ('██     ', '██     ', '██     ', '██     ', '██     ', '███████'),
    'A': ('  ███  ', ' ██ ██ ', '██   ██', '███████', '██   ██', '██   ██'),
    'T': ('███████', '   ██  ', '   ██  ', '   ██  ', '   ██  ', '   ██  '),
    'I': ('█████', ' ███ ', ' ███ ', ' ███ ', ' ███ ', '█████'),
    'N': ('██   ██', '███  ██', '████ ██', '██ ████', '██  ███', '██   ██'),
    'E': ('███████', '██     ', '██████ ', '██     ', '██     ', '███████'),
}

#: The same letters, hollow. Lighter on the eye, and it holds a gradient
#: better than the solid one because the colour lands on an edge rather than
#: on a field.
_OUTLINE: dict[str, tuple[str, ...]] = {
    'F': ('▛▀▀▀▀▀▀', '▌      ', '▛▀▀▀▀▘ ', '▌      ', '▌      ', '▙      '),
    'L': ('▛      ', '▌      ', '▌      ', '▌      ', '▌      ', '▙▄▄▄▄▄▄'),
    'A': ('  ▄▀▀▄ ', ' ▞    ▚', '▌      ', '▛▀▀▀▀▀▜', '▌     ▐', '▙     ▟'),
    'T': ('▀▀▀▀▀▀▀', '   ▐▌  ', '   ▐▌  ', '   ▐▌  ', '   ▐▌  ', '   ▐▌  '),
    'I': ('▀▀▀▀▀', ' ▐▌  ', ' ▐▌  ', ' ▐▌  ', ' ▐▌  ', '▄▄▄▄▄'),
    'N': ('▛▖    ▐', '▌▚    ▐', '▌ ▚   ▐', '▌  ▚  ▐', '▌   ▚ ▐', '▙    ▚▟'),
    'E': ('▛▀▀▀▀▀▀', '▌      ', '▛▀▀▀▀▘ ', '▌      ', '▌      ', '▙▄▄▄▄▄▄'),
}


#: One-cell strokes rather than two. Narrower than the block by a third,
#: which is the whole reason it exists: the block mark is 61 columns and
#: there are terminals and moods that want less than that.
_THIN: dict[str, tuple[str, ...]] = {
    'F': ('█████', '█    ', '████ ', '█    ', '█    ', '█    '),
    'L': ('█    ', '█    ', '█    ', '█    ', '█    ', '█████'),
    'A': (' ███ ', '█   █', '█   █', '█████', '█   █', '█   █'),
    'T': ('█████', '  █  ', '  █  ', '  █  ', '  █  ', '  █  '),
    'I': ('███', ' █ ', ' █ ', ' █ ', ' █ ', '███'),
    'N': ('█   █', '██  █', '█ █ █', '█  ██', '█   █', '█   █'),
    'E': ('█████', '█    ', '████ ', '█    ', '█    ', '█████'),
}

#: Drawn with rules rather than filled. Reads as a schematic of the word.
_WIRE: dict[str, tuple[str, ...]] = {
    'F': ('┌────', '│    ', '├─── ', '│    ', '│    ', '╵    '),
    'L': ('╷    ', '│    ', '│    ', '│    ', '│    ', '└────'),
    'A': ('┌───┐', '│   │', '│   │', '├───┤', '│   │', '╵   ╵'),
    'T': ('──┬──', '  │  ', '  │  ', '  │  ', '  │  ', '  ╵  '),
    'I': ('─┬─', ' │ ', ' │ ', ' │ ', ' │ ', '─┴─'),
    'N': ('┌╮  ╷', '│╰╮ │', '│ ╰╮│', '│  ╰┤', '│   │', '╵   ╵'),
    'E': ('┌────', '│    ', '├─── ', '│    ', '│    ', '└────'),
}

#: The word, one letter per line, down the left with a rule off each end.
#: The only banner here that is taller than it is wide.
def _stacked(caps) -> list[str]:
    """The word down the left, on a rule. The only banner taller than wide."""
    v, h = caps.g('vline'), caps.g('hline')
    top, bottom = caps.g('corner_tl'), caps.g('corner_bl')
    span = max(4, min(caps.width, 60) - 8)
    rows = []
    for i, ch in enumerate(WORD):
        if i == 0:
            rows.append(f'{top}{h} {ch}  {h * span}')
        elif i == len(WORD) - 1:
            rows.append(f'{bottom}{h} {ch}  {h * span}')
        else:
            rows.append(f'{v}  {ch}')
    return _pad(rows)


def _pad(rows: list[str]) -> list[str]:
    """Right-pad to a rectangle. Every check downstream assumes one."""
    if not rows:
        return rows
    wide = max(len(r) for r in rows)
    return [r.ljust(wide) for r in rows]


def _slanted(rows: list[str]) -> list[str]:
    """Lean the mark over, by shifting each row against the one below it.

    Generated rather than drawn: a hand-cut italic of a 61-column wordmark is
    a lot of careful work to produce something a two-line transform gets
    exactly right.
    """
    depth = len(rows) - 1
    return _pad([' ' * (depth - i) + row for i, row in enumerate(rows)])


def _shadowed(rows: list[str], ascii_only: bool = False) -> list[str]:
    """The mark with a lighter copy of itself behind it, down and right.

    Drawn in a second character rather than a second colour, so it survives
    `--no-color` intact. A shadow that only exists in the palette is a shadow
    that vanishes in a pipe.
    """
    solid = '#' if ascii_only else '█'
    ghost = '+' if ascii_only else '░'
    height = len(rows) + 1
    width = (max(len(r) for r in rows) if rows else 0) + 1
    grid = [[' '] * width for _ in range(height)]
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ' ':
                grid[y + 1][x + 1] = ghost
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ' ':
                grid[y][x] = solid
    return [''.join(line) for line in grid]


#: Braille dot numbering, as (column, row) -> bit. The 2x4 cell is why this
#: is here at all: it packs the same bitmap into a quarter of the columns and
#: half the rows, at four times the resolution per character.
_DOTS = {(0, 0): 0x01, (0, 1): 0x02, (0, 2): 0x04, (0, 3): 0x40,
         (1, 0): 0x08, (1, 1): 0x10, (1, 2): 0x20, (1, 3): 0x80}


def _braille(rows: list[str]) -> list[str]:
    """Repack the mark into braille cells.

    Not an accessibility feature and not pretending to be one: this is the
    bitmap, at 2x4 dots per character, because a terminal that can draw
    braille can draw the wordmark at a third of the width without losing a
    stroke of it.

    The source is doubled vertically first. Packing six rows straight in fills
    one and a half cell rows, which throws away most of the vertical detail
    and comes out as mush; twelve rows fill three cleanly.
    """
    if not rows:
        return []
    width = max(len(r) for r in rows)
    grid = [row.ljust(width) for row in rows for _ in range(2)]
    out = []
    for top in range(0, len(grid), 4):
        line = []
        for left in range(0, width, 2):
            bits = 0
            for (dx, dy), bit in _DOTS.items():
                y, x = top + dy, left + dx
                if y < len(grid) and x < width and grid[y][x] != ' ':
                    bits |= bit
            line.append(chr(0x2800 + bits))
        out.append(''.join(line))
    return _pad(out)


#: How far each row of the glitch banner slips, and what it slips into.
#: Fixed rather than random: the intro is not allowed to touch a game stream,
#: and a wordmark that came out differently every boot would read as a fault
#: rather than as a style.
_SLIP = (0, 3, -2, 5, -1, 2)
_ARTEFACT = '▚▞▓▒░'


def _glitched(rows: list[str], ascii_only: bool = False) -> list[str]:
    """The mark, torn. Rows slip sideways and the tear fills with noise."""
    noise = '#%=-.' if ascii_only else _ARTEFACT
    width = max(len(r) for r in rows) if rows else 0
    out = []
    for i, row in enumerate(rows):
        slip = _SLIP[i % len(_SLIP)]
        if slip > 0:
            shifted = noise[i % len(noise)] * slip + row[:-slip or None]
        elif slip < 0:
            shifted = row[-slip:] + noise[i % len(noise)] * -slip
        else:
            shifted = row
        out.append(shifted.ljust(width))
    return _pad(out)


def _framed(rows: list[str], caps) -> list[str]:
    """The word inside a drawn window, titled like a device node.

    Uses the player's own frame set, so this banner is the one place two rice
    axes visibly compose.
    """
    title = ' deck://cold-start '
    body = ['', '  ' + '  '.join(WORD) + '  ', '',
            '  a city that does not care whether you live  ']
    inner = max(len(title) + 4, max(len(b) for b in body))
    h, v = caps.g('hline'), caps.g('vline')
    top = (caps.g('corner_tl') + h + title
           + h * (inner - len(title) - 1) + caps.g('corner_tr'))
    bottom = caps.g('corner_bl') + h * inner + caps.g('corner_br')
    return _pad([top] + [f'{v}{b.ljust(inner)}{v}' for b in body] + [bottom])


WORD = 'FLATLINE'
MARK_HEIGHT = 6
#: Computed rather than assumed, because the glyphs are not all one width and
#: an `I` as fat as an `N` looks like a rendering fault rather than a typeface.
MARK_WIDTH = sum(len(_GLYPHS[c][0]) for c in WORD) + len(WORD) - 1


#: Letterform sets, and whether each survives the ASCII rung. `outline` and
#: `wire` are made of box-drawing and have no honest ASCII form, so they fall
#: back to the block rather than to a field of hashes.
_FONTS: dict[str, dict[str, tuple[str, ...]]] = {
    'block': _GLYPHS, 'outline': _OUTLINE, 'thin': _THIN, 'wire': _WIRE,
}
_ASCII_SAFE = frozenset({'block', 'thin'})


def mark(ascii_only: bool = False, style: str = 'block') -> list[str]:
    """The wordmark as plain rows, no colour."""
    font = style if style in _FONTS else 'block'
    if ascii_only and font not in _ASCII_SAFE:
        font = 'block'
    table = _FONTS[font]
    rows = [' '.join(table[ch][r] for ch in WORD) for r in range(MARK_HEIGHT)]
    if ascii_only:
        rows = [r.replace('█', '#') for r in rows]
    return _pad(rows)


#: What the small mark measures, so the width guard can compare against it.
SMALL_WIDTH = 23


def small_mark() -> list[str]:
    """What a narrow terminal gets instead. Still a mark, just a quiet one."""
    return ['/ / F L A T L I N E / /']


@dataclass(frozen=True, slots=True)
class Banner:
    key: str
    blurb: str


#: Wordmark styles. The catalogue in `content/rice.py` decides which are
#: earned; this decides what they are.
BANNERS: dict[str, Banner] = {
    'block': Banner('block', 'six rows, solid, with the trace under it'),
    'outline': Banner('outline', 'the same letters, hollow'),
    'thin': Banner('thin', 'one-cell strokes, a third narrower'),
    'wire': Banner('wire', 'drawn in rules, like a schematic of the word'),
    'slant': Banner('slant', 'the block mark, leaning'),
    'shadow': Banner('shadow', 'solid, with a lighter copy behind it'),
    'braille': Banner('braille', 'the same bitmap at 2x4 dots per character'),
    'glitch': Banner('glitch', 'torn sideways, with noise in the tears'),
    'terminal': Banner('terminal', 'inside a drawn window, titled'),
    'stack': Banner('stack', 'one letter per line, down the left'),
    'small': Banner('small', 'one line'),
    'none': Banner('none', 'no wordmark at all'),
}

#: Banners that need more than 40 columns to be worth drawing. Anything else
#: falls back to the small mark on a narrow terminal.
_WIDE_ONLY = frozenset({'block', 'outline', 'thin', 'wire', 'slant',
                        'shadow', 'glitch', 'terminal'})
#: Banners the trace line goes under. The tall and the framed ones already
#: have a bottom edge and a second rule under them reads as a mistake.
_TRACED = frozenset({'block', 'outline', 'thin', 'wire', 'slant', 'shadow'})


def banner_rows(style: str, ascii_only: bool, wide: bool,
                caps: Caps | None = None) -> list[str]:
    """The rows for a banner style, honouring what the terminal can do.

    Capability first, taste second, as everywhere else in here. A narrow
    terminal gets the small mark whatever the preference says, and a style
    made of characters this terminal cannot draw falls back to the block
    rather than to a field of hashes that used to be a typeface.
    """
    if style == 'none':
        return []
    if style == 'small':
        return small_mark()
    # Braille, the drawn window and the stack are all made of codepoints an
    # ASCII terminal has no answer for.
    if ascii_only and style in ('braille', 'terminal', 'stack'):
        return _fit(mark(True, 'block'), wide)
    if style == 'braille':
        return _fit(_braille(mark(False, 'block')), wide)
    if style == 'stack':
        return _fit(_stacked(caps), wide) if caps is not None else small_mark()
    if style == 'terminal':
        return (_fit(_framed(mark(ascii_only), caps), wide)
                if caps is not None else small_mark())
    if style == 'slant':
        return _fit(_slanted(mark(ascii_only, 'block')), wide)
    if style == 'shadow':
        return _fit(_shadowed(mark(ascii_only, 'block'), ascii_only), wide)
    if style == 'glitch':
        return _fit(_glitched(mark(ascii_only, 'block'), ascii_only), wide)
    return _fit(mark(ascii_only, style), wide)


def _fit(rows: list[str], wide: bool) -> list[str]:
    """The small mark instead, if these rows will not fit.

    The guard is last rather than first on purpose. Several styles fall back
    to a different style before they are measured, and checking the width
    before that happened let a 61-column ASCII fallback through on a
    40-column terminal.
    """
    if wide or not rows:
        return rows
    return small_mark() if max(len(r) for r in rows) > SMALL_WIDTH else rows


def banner_preview(style: str, caps: Caps) -> list[str]:
    """The banner, coloured, for the catalogue."""
    rows = banner_rows(style, caps.glyphs is GlyphLevel.ASCII, True, caps)
    if not rows:
        return [paint('(nothing)', 'dim', caps)]
    return gradient(rows, caps.palette, caps)


# --------------------------------------------------------------------------
# colour
# --------------------------------------------------------------------------


def _lerp(a: tuple[int, int, int], b: tuple[int, int, int],
          t: float) -> tuple[int, int, int]:
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))  # type: ignore


def _fg(rgb: tuple[int, int, int], caps: Caps, fallback: str) -> str:
    """An SGR sequence at the best rung this terminal actually supports."""
    if caps.color is ColorLevel.NONE:
        return ''
    if caps.color is ColorLevel.TRUE:
        return f'\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m'
    if caps.color is ColorLevel.ANSI256:
        from .theme import Color
        return f'\033[38;5;{Color(_hex(rgb), fallback).c256}m'
    from .theme import ANSI16
    return f'\033[{ANSI16.get(fallback, 37)}m'


def _hex(rgb: tuple[int, int, int]) -> str:
    return '#%02x%02x%02x' % rgb


RESET = '\033[0m'


def paint(text: str, role: str, caps: Caps) -> str:
    """Text in a palette role, or text, if this terminal has no colour.

    The `or text` half is the part that matters. Emitting a reset after an
    empty colour code leaves a bare `[0m` in the output, which is invisible on
    a terminal and extremely visible in a pipe, a log, or a screenshot from
    somebody reporting a bug.
    """
    colour = getattr(caps.palette, role)
    code = _fg(colour.rgb, caps, colour.ansi)
    return f'{code}{text}{RESET}' if code else text


#: Characters the shadow is drawn in. They get the dim role rather than the
#: gradient, because a drop shadow in the same colour as the thing dropping it
#: is not a shadow, it is a smear.
SHADOW_CHARS = frozenset('░+')


def gradient(rows: list[str], palette: Palette, caps: Caps) -> list[str]:
    """Colour the mark top to bottom, accent into accent2."""
    top, bottom = palette.accent.rgb, palette.accent2.rgb
    dim = _fg(palette.dim.rgb, caps, palette.dim.ansi)
    out = []
    for i, row in enumerate(rows):
        t = i / max(1, len(rows) - 1)
        code = _fg(_lerp(top, bottom, t), caps,
                   palette.accent.ansi if t < 0.5 else palette.accent2.ansi)
        if not code:
            out.append(row)
            continue
        if not any(ch in SHADOW_CHARS for ch in row):
            out.append(f'{code}{row}{RESET}')
            continue
        # Split into runs so the shadow can take a different colour without
        # emitting a sequence per character.
        parts, run, shadowed = [], [], row[0] in SHADOW_CHARS
        for ch in row:
            here = ch in SHADOW_CHARS
            if here != shadowed:
                parts.append((shadowed, ''.join(run)))
                run, shadowed = [], here
            run.append(ch)
        parts.append((shadowed, ''.join(run)))
        out.append(''.join(f'{dim if s else code}{text}' for s, text in parts)
                   + RESET)
    return out


# --------------------------------------------------------------------------
# the trace
# --------------------------------------------------------------------------

#: One beat, in eighth-blocks. Read left to right as a rising edge, a spike,
#: and the drop after it.
_BEAT = '▁▁▁▂▃▅███▅▃▂▁▁▁'
_FLAT = '▁'
_BEAT_ASCII = '___..-^^^-.___'


def trace_row(width: int, offset: int, beating: bool,
              ascii_only: bool = False) -> str:
    """One frame of the heart trace, scrolling right to left."""
    flat = '_' if ascii_only else _FLAT
    if not beating:
        return flat * width
    beat = _BEAT_ASCII if ascii_only else _BEAT
    gap = flat * 22
    pattern = (beat + gap) * (width // (len(beat) + len(gap)) + 2)
    start = offset % (len(beat) + len(gap))
    return pattern[start:start + width]


# --------------------------------------------------------------------------
# the gate
# --------------------------------------------------------------------------


def can_animate(console) -> bool:
    """Whether motion is safe here. All three conditions, no exceptions."""
    if os.environ.get('FLATLINE_NO_INTRO'):
        return False
    if getattr(console, 'captured', None) is not None:
        return False
    if console.caps.color is ColorLevel.NONE:
        return False
    stream = getattr(console, 'stream', None)
    return bool(stream and hasattr(stream, 'isatty') and stream.isatty())


class _Screen:
    """Direct terminal writes for the duration of one animation.

    Bypasses `Console` on purpose. Everything here is cursor movement and
    partial lines, which is exactly what `Console` exists to not do, and
    routing it through the markup parser would mean escaping every escape.
    """

    def __init__(self, console) -> None:
        self.console = console
        self.stream = console.stream
        self.caps = console.caps
        self.drawn = 0

    def __enter__(self) -> _Screen:
        self._w('\033[?25l')
        return self

    def __exit__(self, *exc) -> None:
        # Unconditionally, however we leave. A hidden cursor outlives the
        # process and the player will not connect that to this program.
        self._w('\033[?25h' + RESET)
        self.stream.flush()

    def _w(self, s: str) -> None:
        self.stream.write(s)

    def draw(self, lines: list[str]) -> None:
        """Replace the previous frame in place.

        **A frame shorter than the one before it has to erase what it does not
        cover.** Clearing each line as it is written handles a frame that grows
        and a frame that stays the same size, and does nothing at all about a
        frame that shrinks: the tail of the old one is below the last line
        written and nothing ever touches it again. The boot sequence shrinks by
        seven lines when the POST log gives way to the wordmark, so the bottom
        of the self test sat under the finished title card, which reads exactly
        like the art being drawn on top of the log.
        """
        if self.drawn:
            self._w(f'\033[{self.drawn}A')
        for line in lines:
            self._w('\033[2K' + line + '\n')
        if len(lines) < self.drawn:
            # The cursor is on the first uncovered line. Erase from here down.
            self._w('\033[J')
        self.drawn = len(lines)
        self.stream.flush()

    def pause(self, seconds: float) -> None:
        time.sleep(seconds)


# --------------------------------------------------------------------------
# effects
# --------------------------------------------------------------------------

#: What unresolved cells look like mid-decrypt. Deliberately noisy and
#: deliberately not the alphabet: it should read as signal, not as letters.
_NOISE = '▚▞▓▒░╱╲│┤├┼╳█▛▜▟▙◣◤◥◢!@#%&*<>/\\|=+-'
_NOISE_ASCII = '#%&*<>/\\|=+-:;.'


def scramble(target: str, settled: float, rng: random.Random,
             ascii_only: bool = False) -> str:
    """One frame of a decrypt reveal.

    `settled` is 0..1. Cells resolve left to right with a soft edge, so the
    wavefront reads as something arriving rather than as a wipe.
    """
    noise = _NOISE_ASCII if ascii_only else _NOISE
    width = len(target)
    edge = settled * (width + 8) - 4
    out = []
    for i, ch in enumerate(target):
        if ch == ' ' or i < edge - 4:
            out.append(ch)
        elif i >= edge + 4:
            out.append(' ')
        else:
            out.append(ch if rng.random() < 0.35 else rng.choice(noise))
    return ''.join(out)


# --------------------------------------------------------------------------
# the boot
# --------------------------------------------------------------------------

#: Power-on self test. Written to look like a machine talking to itself rather
#: than to you, because the moment a boot sequence addresses the player it
#: stops being a machine and starts being a cutscene.
POST: tuple[tuple[str, str], ...] = (
    ('cold start', 'ok'),
    ('trode net', 'ok'),
    ('nerve interface', 'ok'),
    ('substrate clock', 'ok'),
    ('cortical buffer', 'ok'),
    ('bloodflow compensation', 'ok'),
    ('dead man handler', 'armed'),
)


def deck_lines(char) -> list[tuple[str, str]]:
    """POST entries for the deck this character actually owns.

    Reading the real build matters more than it sounds: a boot screen that
    prints the same six fictional components for everybody is decoration, and
    one that names the cracked cooling unit you have been meaning to replace
    is the game telling you something before you have typed anything.
    """
    from .content import hardware
    out: list[tuple[str, str]] = []
    if char is None:
        return out
    for slot in hardware.SLOTS:
        comp = char.deck.component(slot)
        if comp is None:
            out.append((f'{slot}', 'absent'))
            continue
        damage = char.deck.damage.get(slot, 0)
        state = ('ok' if not damage
                 else 'degraded' if damage < 3 else 'failed')
        out.append((comp.name.lower(), state))
    return out


_STATE_ROLE = {'ok': 'ok', 'armed': 'warn', 'degraded': 'warn',
               'failed': 'err', 'absent': 'dim',
               # the shutdown's states (D181)
               'closed': 'warn', 'dropped': 'warn', 'flushed': 'ok',
               'stood down': 'ok', 'cold': 'dim', 'off': 'dim'}


def _post_line(label: str, state: str, caps: Caps, width: int) -> str:
    role = _STATE_ROLE.get(state, 'dim')
    dots = '.' * max(2, width - len(label) - len(state) - 6)
    return ('  ' + paint(label, 'muted', caps)
            + paint(f' {dots} ', 'dim', caps)
            + paint(state, role, caps))


# --------------------------------------------------------------------------
# the skyline (D112): the boot's one full-colour picture
# --------------------------------------------------------------------------

#: Fixed. The boot is not allowed to touch a game stream (D35), and a city
#: that came out different every launch would read as a fault rather than a
#: place. The day the netrunning layer first drew a picture.
SKYLINE_SEED = 20260901
#: Pixels tall. Even, because a half-block cell is two pixels and the blit
#: pairs rows. Ten text rows.
_SCENE_H = 20


def scene(caps, palette, lit: float = 1.0, sweep=None):
    """The neon waterfront as a pixel grid, or None where pictures are off.

    A night sky over a synthwave sun, a skyline whose windows come on as
    `lit` climbs from nothing to one, and dark water under it that holds the
    horizon glow and a scatter of the same lights thrown back. Drawn in the
    player's own accent, so the palette they earned themes the title. It is
    the one place the boot uses the picture layer the rest of the game earned
    (D102), and like everything in the layer it is drawn or it is not: at
    sixteen colours or in ASCII the terminal gets the wordmark alone.
    """
    from . import pixels
    if not pixels.can_render(caps):
        return None
    w = min(76, caps.width - 2) & ~1
    if w < 40:
        return None
    h = _SCENE_H
    horizon = int(h * 0.60)
    accent, accent2 = palette.accent.rgb, palette.accent2.rgb
    sky_top = (9, 7, 26)
    hor = pixels.lerp(accent2, (255, 130, 120), 0.40)
    scn = pixels._blank(w, h, sky_top)
    rng = random.Random(SKYLINE_SEED)
    for y in range(horizon):                                    # the sky
        c = pixels.lerp(sky_top, hor, (y / max(1, horizon)) ** 1.6)
        for x in range(w):
            scn[y][x] = c
    for _ in range(int(w * 0.22)):                              # stars
        sx, sy = rng.randrange(w), rng.randrange(max(1, horizon // 2))
        b = rng.randint(120, 210)
        scn[sy][sx] = (b, b, min(255, b + 25))
    cx, cy, radius = w // 2, horizon, int(h * 0.50)             # the sun
    for y in range(max(0, cy - radius), cy):
        for x in range(cx - radius, cx + radius + 1):
            if not 0 <= x < w:
                continue
            dx, dy = (x - cx) / radius, (y - cy) / radius
            if dx * dx + dy * dy <= 1.0:
                vt = (y - (cy - radius)) / max(1, radius)
                if vt > 0.45 and (cy - y) % 2 == 0:             # scanline gaps
                    continue
                scn[y][x] = pixels.lerp((255, 246, 205), (255, 54, 150),
                                        vt ** 1.2)
    silhouette, wins = (12, 10, 24), []                         # the skyline
    x = 0
    while x < w:
        bw = rng.randint(3, 7)
        top = horizon - rng.randint(int(h * 0.14), int(h * 0.40))
        pixels._rect(scn, x, top, min(w, x + bw), horizon, silhouette)
        rim = pixels.shade(accent if rng.random() < 0.6 else accent2, 0.95)
        for xx in range(x, min(w, x + bw)):                     # neon rim light
            pixels._put(scn, xx, top, rim)
        for wy in range(top + 2, horizon, 2):                   # lit windows
            for wx in range(x + 1, min(w, x + bw), 2):
                if rng.random() < 0.5 * lit:
                    wc = rng.choice([accent, accent2, (255, 200, 110)])
                    pixels._put(scn, wx, wy, wc)
                    wins.append((wx, wy, wc))
        x += bw + rng.randint(1, 2)
    base_top, base_bot = (16, 6, 24), (3, 2, 8)                 # the water
    for y in range(horizon, h):
        c = pixels.lerp(base_top, base_bot, (y - horizon) / max(1, h - horizon))
        for xx in range(w):
            scn[y][xx] = c
    for d in range(h - horizon):                               # horizon glow
        fade = max(0.0, 0.55 - d * 0.16)
        for xx in range(w):
            scn[horizon + d][xx] = pixels.lerp(scn[horizon + d][xx], hor, fade)
    for (wx, wy, wc) in wins:                                   # reflections
        ry = horizon + (horizon - wy)
        if horizon <= ry < h:
            scn[ry][wx] = pixels.lerp(scn[ry][wx], wc, 0.35)
    if sweep is not None:                                       # a light sweep
        for y in range(h):
            row = scn[y]
            for x in range(w):
                near = abs(x - sweep)
                if near < 3 and row[x] is not None:
                    row[x] = pixels.lerp(row[x], (255, 255, 255),
                                         (3 - near) / 7)
    return scn


def scene_rows(caps, palette, lit: float = 1.0, sweep=None) -> list[str]:
    """The skyline blitted to centred text rows, or [] where pictures are off."""
    from . import pixels
    grid = scene(caps, palette, lit, sweep)
    if grid is None:
        return []
    pad = ' ' * max(0, (min(caps.width, 80) - len(grid[0])) // 2)
    return [pad + r for r in pixels.blit(grid, caps)]


def boot(console, char=None, quick: bool = False,
         style: str = 'block') -> None:
    """The cold start. Prints its last frame and returns if it cannot animate.

    Roughly two and a half seconds when it runs at all, and Ctrl-C at any
    point jumps straight to the end of it.
    """
    caps = console.caps
    ascii_only = caps.glyphs is GlyphLevel.ASCII
    palette = caps.palette
    fits = caps.width >= MARK_WIDTH + 2
    rows = banner_rows(style, ascii_only, fits, caps)
    # Measured rather than assumed. The banners are not all the same width:
    # braille is 31 columns and slant is 66, and centring every one of them
    # against the block mark's 61 put half of them off-centre and pushed the
    # widest one past the edge.
    span = max((len(r) for r in rows), default=0)
    traced = fits and style in _TRACED and span <= caps.width - 2
    width = min(caps.width - 1, MARK_WIDTH)
    pad = ' ' * max(0, (min(caps.width, 80) - span) // 2)

    # The skyline sits above the wordmark, on the terminals that can draw it
    # and at the wide styles that leave room for it. A minimal banner (none,
    # small) reads as a request for a quiet start, so it gets one. `head` is
    # everything above the wordmark, shared by the animation and the final
    # frame so the title does not jump when the motion ends.
    show_scene = fits and style not in ('none', 'small')
    scene_full = scene_rows(caps, palette, 1.0) if show_scene else []
    head = [''] + (scene_full + [''] if scene_full else [])

    def final() -> list[str]:
        out = list(head) + [pad + r for r in gradient(rows, palette, caps)]
        if traced:
            out.append(pad + paint(
                trace_row(span, 0, False, ascii_only), 'err', caps))
        # The long tagline is 42 columns. Anything narrower gets the short
        # one rather than a centred line that runs off the edge.
        tag = ('a city that does not care whether you live'
               if caps.width >= 44 else 'it does not care')
        out.append('')
        out.append(' ' * max(0, (min(caps.width, 80) - len(tag)) // 2)
                   + paint(tag, 'dim', caps))
        out.append('')
        return out

    if quick or not can_animate(console):
        for line in final():
            console.emit(line)
        return

    rng = random.Random(20260813)
    posts = list(POST) + deck_lines(char)

    try:
        with _Screen(console) as screen:
            # 1. The machine wakes up and checks itself.
            shown: list[str] = ['']
            for label, state in posts:
                shown.append(_post_line(label, state, caps, width))
                screen.draw(shown)
                screen.pause(0.055 if state == 'ok' else 0.16)
            screen.pause(0.22)

            # 2. It clears, and the city comes up: the sky, then the windows
            #    lighting a bank at a time, then a sweep of light off the
            #    water. Only where the terminal can draw it.
            if scene_full:
                power = 8
                for i in range(1, power + 1):
                    screen.draw([''] + scene_rows(caps, palette, i / power))
                    screen.pause(0.05)
                grid = scene(caps, palette, 1.0)
                span_px = len(grid[0]) if grid else 0
                for sx in range(-2, span_px + 3, 5):
                    screen.draw([''] + scene_rows(caps, palette, 1.0, sweep=sx))
                    screen.pause(0.025)

            # 3. And the mark decrypts into place beneath it.
            if not rows:
                screen.draw(final())
                return
            steps = 16
            for i in range(steps + 1):
                t = i / steps
                frame = [scramble(r, t, rng, ascii_only) for r in rows]
                screen.draw(head + [pad + r for r in
                                    gradient(frame, palette, caps)])
                screen.pause(0.032)

            # 4. And then the part the game is named after.
            if traced:
                lit = gradient(rows, palette, caps)
                for i in range(26):
                    beating = i < 18
                    line = trace_row(span, i * 3, beating, ascii_only)
                    screen.draw(head + [pad + r for r in lit]
                                + [pad + paint(line, 'ok' if beating else 'err',
                                               caps)])
                    screen.pause(0.045 if beating else 0.07)
            screen.draw(final())
    except KeyboardInterrupt:
        # "Get on with it", not "quit". Redraw the end state and carry on.
        console.raw()
        for line in final():
            console.emit(line)


# --------------------------------------------------------------------------
# jacking in
# --------------------------------------------------------------------------

#: The handshake, in the order a deck would actually do it. Each entry is
#: (label, weight), where weight is roughly how long that stage takes relative
#: to the others. Written as a machine reporting to itself.
HANDSHAKE: tuple[tuple[str, float], ...] = (
    ('carrier', 0.6),
    ('key exchange', 1.0),
    ('session', 0.7),
    ('icon render', 1.2),
    ('nerve sync', 0.9),
)

#: The glyphs the data band is made of. Not hex: a wall of hex reads as a
#: screensaver from 1998, and the point of this band is that you cannot read
#: it, only see that it is moving.
_BAND = '▁▂▃▄▅▆▇█▇▆▅▄▃▂'
_BAND_ASCII = '.:-=+*#%#*+=-:'


def band_row(width: int, offset: int, ascii_only: bool = False) -> str:
    """One frame of the carrier band, scrolling."""
    chars = _BAND_ASCII if ascii_only else _BAND
    return ''.join(chars[(i + offset) % len(chars)] for i in range(width))


def meter(pct: float, width: int, caps: Caps, ascii_only: bool = False) -> str:
    """A progress bar in the palette's accent, at whatever rung is available."""
    full = caps.g('bar_full') if not ascii_only else '#'
    empty = caps.g('bar_empty') if not ascii_only else '.'
    filled = int(round(max(0.0, min(1.0, pct)) * width))
    return (paint(full * filled, 'accent', caps)
            + paint(empty * (width - filled), 'border', caps))


def connect(console, target_name: str, quick: bool = False) -> None:
    """The handshake. Called once, on the way into a run.

    The threshold moment of the whole game: the point where the city stops and
    the other place starts. It gets an animation for the same reason the boot
    does, and it obeys the same rule, which is that skipping it changes
    nothing at all.
    """
    caps = console.caps
    ascii_only = caps.glyphs is GlyphLevel.ASCII
    width = min(52, max(20, caps.width - 24))

    def line(label: str, pct: float) -> str:
        return (f'  {paint(label.ljust(14), "muted", caps)}'
                f'{meter(pct, width, caps, ascii_only)} '
                f'{paint(f"{int(pct * 100):3d}%", "dim", caps)}')

    def final() -> list[str]:
        return ([''] + [line(label, 1.0) for label, _ in HANDSHAKE]
                + ['', '  ' + paint(f'carrier locked: {target_name}',
                                    'accent', caps), ''])

    if quick or not can_animate(console):
        for row in final():
            console.emit(row)
        return

    try:
        with _Screen(console) as screen:
            progress = [0.0] * len(HANDSHAKE)
            frame = 0
            for i, (_, weight) in enumerate(HANDSHAKE):
                steps = max(3, int(weight * 9))
                for step in range(steps + 1):
                    progress[i] = step / steps
                    rows = ['']
                    rows += [line(HANDSHAKE[j][0], progress[j])
                             for j in range(len(HANDSHAKE))]
                    rows += ['', '  ' + paint(
                        band_row(width + 14, frame, ascii_only), 'ice', caps),
                        '']
                    screen.draw(rows)
                    screen.pause(0.028)
                    frame += 2
            screen.draw(final())
    except KeyboardInterrupt:
        console.raw()
        for row in final():
            console.emit(row)



# --------------------------------------------------------------------------
# pictures (D102)
# --------------------------------------------------------------------------


#: The ways a picture can arrive (D109). Each is a function from the whole
#: picture, a frame index and a total, to the pixels shown that frame.
REVEAL_STYLES = ('dissolve', 'scan', 'wipe', 'flash', 'instant')


def _reveal_frame(style: str, pix, i: int, total: int, rng):
    """The picture as it looks on frame `i` of `total`, for a reveal style.

    None-valued pixels are transparent, so an unrevealed row is simply the
    terminal's own ground. Everything is composed from the finished picture,
    which is why no style can show a pixel the picture does not have.
    """
    from . import pixels
    h = len(pix)
    t = i / max(1, total)
    if style == 'wipe':
        cut = int(round(h * t))
        return [list(row) if y < cut else [None] * len(row)
                for y, row in enumerate(pix)]
    if style == 'scan':
        cut = int(round(h * t))
        if cut >= h:
            return [list(row) for row in pix]
        out = []
        for y, row in enumerate(pix):
            if y < cut - 1:
                out.append(list(row))
            elif y == cut - 1 or y == cut:
                # the bright leading edge, in each cell's own colour lifted
                out.append([pixels.shade(c, 1.6) if c else None for c in row])
            else:
                out.append([None] * len(row))
        return out
    if style == 'flash':
        if t < 0.5:
            k = 0.25 + t
            return [[pixels.shade(c, k) if c else None for c in row] for row in pix]
        return [list(row) for row in pix]
    # dissolve
    return pixels.scrambled(pix, t, rng)


def reveal(console, pix, caption: str, quick: bool = False,
           style: str = 'dissolve') -> None:
    """A picture arriving, in one of a handful of styles (D109). Prints the
    finished picture and returns when it cannot animate."""
    from . import pixels
    caps = console.caps
    rows = pixels.blit(pix, caps)
    if not rows:
        return
    lines = ['  ' + r for r in rows]
    if caption:
        lines[min(1, len(lines) - 1)] += '   ' + paint(caption, 'dim', caps)
    if quick or style == 'instant' or not can_animate(console):
        for line in lines:
            console.emit(line)
        console.blank()
        return
    frames = 4 if style == 'flash' else pixels.SETTLE_FRAMES
    pause = 0.09 if style == 'flash' else 0.04
    rng = random.Random(len(caption) + len(pix))
    try:
        with _Screen(console) as screen:
            for i in range(frames + 1):
                frame = _reveal_frame(style, pix, i, frames, rng)
                drawn = ['  ' + r for r in pixels.blit(frame, caps)]
                if caption and drawn:
                    drawn[min(1, len(drawn) - 1)] += '   ' + paint(caption, 'dim', caps)
                screen.draw(drawn)
                screen.pause(pause)
            screen.draw(lines)
    except KeyboardInterrupt:
        console.raw()
        for line in lines:
            console.emit(line)
    console.blank()


def flatline(console, quick: bool = False, style: str = 'block') -> None:
    """The game's name, done properly (D102).

    The heart trace runs, the beats come further apart, and then it is a
    line, and the word above it is the only word this game has ever been
    about. Nothing here matters (D35): the character is already dead.
    """
    caps = console.caps
    ascii_only = caps.glyphs is GlyphLevel.ASCII
    fits = caps.width >= MARK_WIDTH + 2
    rows = banner_rows(style, ascii_only, fits, caps)
    span = max((len(r) for r in rows), default=SMALL_WIDTH)
    pad = ' ' * max(0, (min(caps.width, 80) - span) // 2)
    lit = [pad + paint(r, 'err', caps) for r in rows]

    def final() -> list[str]:
        return ([''] + lit
                + [pad + paint(trace_row(span, 0, False, ascii_only), 'err', caps)]
                + [''])

    if quick or not can_animate(console):
        for line in final():
            console.emit(line)
        return
    try:
        with _Screen(console) as screen:
            # The beats, slowing: the gap between them grows each pass.
            offset = 0
            for gap in (22, 22, 30, 38, 50, 70):
                beat = _BEAT_ASCII if ascii_only else _BEAT
                flat = '_' if ascii_only else _FLAT
                pattern = (beat + flat * gap) * 4
                for step in range(0, len(beat) + gap, 3):
                    line = pattern[step:step + span]
                    screen.draw([''] + lit + [pad + paint(line, 'ok' if gap < 40 else 'warn', caps)])
                    screen.pause(0.045)
                    offset += 3
            for _ in range(10):
                screen.draw([''] + lit + [pad + paint(trace_row(span, 0, False, ascii_only), 'err', caps)])
                screen.pause(0.09)
            screen.draw(final())
    except KeyboardInterrupt:
        console.raw()
        for line in final():
            console.emit(line)


def sever(console, last_line: str, quick: bool = False) -> None:
    """The connection cut from the far end: the last thing on the screen
    tears sideways for a moment (D102). Prints nothing when it cannot
    animate, because a torn line on a page is a typo."""
    caps = console.caps
    if quick or not can_animate(console) or not last_line:
        return
    ascii_only = caps.glyphs is GlyphLevel.ASCII
    try:
        with _Screen(console) as screen:
            for i in range(6):
                torn = _glitched([last_line], ascii_only)
                screen.draw([paint(torn[0], 'err' if i % 2 else 'dim', caps)])
                screen.pause(0.05)
            screen.draw([''])
    except KeyboardInterrupt:
        console.raw()


# --------------------------------------------------------------------------
# disruption (D110)
# --------------------------------------------------------------------------
#
# When the connection is being cut from the far end, or something lethal has
# hold of you, the display itself should not be calm about it. `disrupt`
# fills the space where the cursor is with a burst of static in the alarm
# colours, shuddering side to side, and then clears it, so it reads as the
# terminal being interfered with rather than as one more paragraph. It obeys
# the same rule as everything else here: on anything that is not a live
# colour tty it does nothing at all, and the words that follow it are the
# whole of the content (D35).


def disrupt(console, frames: int = 7, height: int = 6,
            roles: tuple[str, ...] = ('err', 'ice', 'warn'),
            shake: bool = True) -> None:
    """A burst of static where the cursor is, then gone. Silent unless the
    terminal can actually animate."""
    if not can_animate(console):
        return
    caps = console.caps
    ascii_only = caps.glyphs is GlyphLevel.ASCII
    chars = _NOISE_ASCII if ascii_only else _NOISE
    width = min(max(20, caps.width - 2), 78)
    rng = random.Random()
    try:
        with _Screen(console) as screen:
            for f in range(frames):
                off = rng.randint(-3, 3) if shake else 0
                fade = 1.0 - f / max(1, frames)
                lines = []
                for _ in range(height):
                    if rng.random() > fade + 0.15:
                        lines.append('')
                        continue
                    n = max(4, int(width * (0.4 + 0.6 * fade)))
                    row = ''.join(rng.choice(chars) for _ in range(n))
                    lines.append(' ' * max(0, off) + paint(row, rng.choice(roles), caps))
                screen.draw(lines)
                screen.pause(0.05 if f < frames - 1 else 0.03)
            screen.draw([''])
    except KeyboardInterrupt:
        console.raw()


# --------------------------------------------------------------------------
# the shutdown (D181)
# --------------------------------------------------------------------------

#: The deck powering down, in the order it would actually do it: the link
#: first, because a session left open is a session somebody reads; the
#: nerve last, because that is the part of it that is you.
SHUTDOWN: tuple[tuple[str, str], ...] = (
    ('session', 'closed'),
    ('link', 'dropped'),
    ('cortical buffer', 'flushed'),
    ('dead man handler', 'stood down'),
    ('nerve interface', 'cold'),
    ('trode net', 'cold'),
)


def shutdown(console, char=None, quick: bool = False,
             style: str = 'block') -> None:
    """The power-down: the reverse of `boot`. The deck reports itself off
    a line at a time, the city's windows go out a bank at a time, the mark
    decays the way it arrived, and the trace beats slower until it does
    not, which is the name. About three seconds; prints its last frame
    and returns where it cannot animate, and Ctrl-C at any point jumps
    to the end of it, the same as the boot.
    """
    caps = console.caps
    ascii_only = caps.glyphs is GlyphLevel.ASCII
    palette = caps.palette
    fits = caps.width >= MARK_WIDTH + 2
    rows = banner_rows(style, ascii_only, fits, caps)
    span = max((len(r) for r in rows), default=0)
    width = min(caps.width - 1, MARK_WIDTH)
    pad = ' ' * max(0, (min(caps.width, 80) - span) // 2)
    traced = fits and 0 < span <= caps.width - 2
    show_scene = fits and style not in ('none', 'small')

    def final() -> list[str]:
        out = ['']
        if traced:
            out.append(pad + paint(trace_row(span, 0, False, ascii_only),
                                   'err', caps))
        tag = ('connection closed. the city is still there.'
               if caps.width >= 48 else 'connection closed.')
        out.append(' ' * max(0, (min(caps.width, 80) - len(tag)) // 2)
                   + paint(tag, 'dim', caps))
        out.append('')
        return out

    if quick or not can_animate(console):
        for line in final():
            console.emit(line)
        return

    rng = random.Random(20260905)
    report = list(SHUTDOWN) + [(label, 'off')
                               for label, _ in reversed(deck_lines(char))]
    try:
        with _Screen(console) as screen:
            # 1. The deck reports itself off, top to bottom.
            shown: list[str] = ['']
            for label, state in report:
                shown.append(_post_line(label, state, caps, width))
                screen.draw(shown)
                screen.pause(0.05 if state in ('off', 'cold') else 0.12)
            screen.pause(0.2)

            # 2. The city and the mark, once more, whole.
            scene_full = scene_rows(caps, palette, 1.0) if show_scene else []
            lit = gradient(rows, palette, caps)
            screen.draw([''] + (scene_full + [''] if scene_full else [])
                        + [pad + r for r in lit])
            screen.pause(0.25)

            # 3. The windows go out a bank at a time.
            if scene_full:
                power = 8
                for i in range(power - 1, -1, -1):
                    screen.draw([''] + scene_rows(caps, palette, i / power)
                                + [''] + [pad + r for r in lit])
                    screen.pause(0.06)

            # 4. The mark decays the way it arrived, from the right.
            steps = 14
            for i in range(steps + 1):
                t = 1.0 - i / steps
                frame = [scramble(r, t, rng, ascii_only) for r in rows]
                screen.draw([''] + [pad + r for r in
                                    gradient(frame, palette, caps)])
                screen.pause(0.03)

            # 5. And the trace beats, slower each time, until it does not.
            if traced:
                for i in range(22):
                    beating = i < 12
                    line = trace_row(span, i * 3, beating, ascii_only)
                    screen.draw([''] + [pad + paint(
                        line, 'ok' if beating else 'err', caps)])
                    screen.pause((0.06 + 0.02 * (i // 4)) if beating else 0.08)
            screen.draw(final())
    except KeyboardInterrupt:
        console.raw()
        for line in final():
            console.emit(line)
