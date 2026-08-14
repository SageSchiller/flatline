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

WORD = 'FLATLINE'
MARK_HEIGHT = 6
#: Computed rather than assumed, because the glyphs are not all one width and
#: an `I` as fat as an `N` looks like a rendering fault rather than a typeface.
MARK_WIDTH = sum(len(_GLYPHS[c][0]) for c in WORD) + len(WORD) - 1


def mark(ascii_only: bool = False) -> list[str]:
    """The wordmark as plain rows, no colour."""
    rows = []
    for r in range(MARK_HEIGHT):
        rows.append(' '.join(_GLYPHS[ch][r] for ch in WORD))
    if ascii_only:
        rows = [r.replace('█', '#') for r in rows]
    return rows


def small_mark() -> list[str]:
    """What a narrow terminal gets instead. Still a mark, just a quiet one."""
    return ['/ / F L A T L I N E / /']


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


def gradient(rows: list[str], palette: Palette, caps: Caps) -> list[str]:
    """Colour the mark top to bottom, accent into accent2."""
    top, bottom = palette.accent.rgb, palette.accent2.rgb
    out = []
    for i, row in enumerate(rows):
        t = i / max(1, len(rows) - 1)
        code = _fg(_lerp(top, bottom, t), caps,
                   palette.accent.ansi if t < 0.5 else palette.accent2.ansi)
        out.append(f'{code}{row}{RESET}' if code else row)
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
        """Replace the previous frame in place."""
        if self.drawn:
            self._w(f'\033[{self.drawn}A')
        for line in lines:
            self._w('\033[2K' + line + '\n')
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
               'failed': 'err', 'absent': 'dim'}


def _post_line(label: str, state: str, caps: Caps, width: int) -> str:
    role = _STATE_ROLE.get(state, 'dim')
    dots = '.' * max(2, width - len(label) - len(state) - 6)
    return ('  ' + paint(label, 'muted', caps)
            + paint(f' {dots} ', 'dim', caps)
            + paint(state, role, caps))


def boot(console, char=None, quick: bool = False) -> None:
    """The cold start. Prints its last frame and returns if it cannot animate.

    Roughly two and a half seconds when it runs at all, and Ctrl-C at any
    point jumps straight to the end of it.
    """
    caps = console.caps
    ascii_only = caps.glyphs is GlyphLevel.ASCII
    palette = caps.palette
    fits = caps.width >= MARK_WIDTH + 2
    rows = mark(ascii_only) if fits else small_mark()
    width = min(caps.width - 1, MARK_WIDTH)
    pad = ' ' * max(0, (min(caps.width, 80) - (MARK_WIDTH if fits else 23)) // 2)

    def final() -> list[str]:
        out = [''] + [pad + r for r in gradient(rows, palette, caps)]
        if fits:
            out.append(pad + paint(
                trace_row(MARK_WIDTH, 0, False, ascii_only), 'err', caps))
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

            # 2. It clears, and the mark decrypts into place.
            steps = 16
            for i in range(steps + 1):
                t = i / steps
                frame = [scramble(r, t, rng, ascii_only) for r in rows]
                screen.draw([''] + [pad + r for r in
                                    gradient(frame, palette, caps)])
                screen.pause(0.032)

            # 3. And then the part the game is named after.
            if fits:
                lit = gradient(rows, palette, caps)
                for i in range(26):
                    beating = i < 18
                    line = trace_row(MARK_WIDTH, i * 3, beating, ascii_only)
                    screen.draw([''] + [pad + r for r in lit]
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
