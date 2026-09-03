"""Output. The whole of the D16 capability ladder lives here.

Everything the game prints goes through `Console`. Nothing else emits escape
codes, and nothing else decides whether a box-drawing character is safe.

Content is written with inline markup, `[accent]like this[/]`, because the
alternative is that every line of flavour text in the game becomes a list of
tuples and stops being readable in the source. The markup parses to spans
before anything measures or wraps it, so widths are always computed on the
text a human will see rather than on the text plus its escape codes. That is
the bug this design exists to prevent, and it is worth the parser.

Roles are the semantic names from `theme.Palette`. An unknown role is a
validation error rather than a silent fallback, so a typo in content is caught
by `validate.py` instead of quietly rendering unstyled.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import unicodedata
from dataclasses import dataclass
from enum import IntEnum

from . import theme
from .config import MIN_COLS, TEXT_WIDTH
from .theme import Palette

# --------------------------------------------------------------------------
# capability detection
# --------------------------------------------------------------------------


class ColorLevel(IntEnum):
    NONE = 0
    ANSI16 = 1
    ANSI256 = 2
    TRUE = 3


class GlyphLevel(IntEnum):
    ASCII = 0
    UNICODE = 1


def detect_color(stream=None) -> ColorLevel:
    """What the terminal can actually do, respecting the usual overrides.

    NO_COLOR wins over everything because that is the point of NO_COLOR. A
    non-tty gets nothing, which is what makes piped output and `test.py`
    capture clean text without special-casing.
    """
    stream = stream or sys.stdout
    if os.environ.get('NO_COLOR'):
        return ColorLevel.NONE
    force = os.environ.get('FORCE_COLOR')
    if force:
        return {'0': ColorLevel.NONE, '1': ColorLevel.ANSI16,
                '2': ColorLevel.ANSI256}.get(force, ColorLevel.TRUE)
    if not hasattr(stream, 'isatty') or not stream.isatty():
        return ColorLevel.NONE
    if os.environ.get('TERM') == 'dumb':
        return ColorLevel.NONE
    if os.environ.get('COLORTERM') in ('truecolor', '24bit'):
        return ColorLevel.TRUE
    term = os.environ.get('TERM', '')
    if '256' in term:
        return ColorLevel.ANSI256
    if term:
        return ColorLevel.ANSI16
    return ColorLevel.NONE


def detect_glyphs(stream=None) -> GlyphLevel:
    """Unicode is only safe when the output encoding can actually carry it."""
    stream = stream or sys.stdout
    enc = (getattr(stream, 'encoding', None) or '').lower()
    if 'utf' not in enc:
        return GlyphLevel.ASCII
    lang = (os.environ.get('LC_ALL') or os.environ.get('LC_CTYPE')
            or os.environ.get('LANG') or '')
    if lang and 'utf' not in lang.lower() and lang.lower() not in ('c', 'posix'):
        return GlyphLevel.ASCII
    return GlyphLevel.UNICODE


#: name -> (unicode, ascii). Content never writes a raw box character; it asks
#: for a glyph by name, which is the only reason the ASCII rung stays honest.
GLYPHS = {
    'bullet': ('·', '.'),
    'arrow': ('→', '->'),
    'dash': ('—', '--'),
    'hline': ('─', '-'),
    'vline': ('│', '|'),
    'corner_tl': ('┌', '+'),
    'corner_tr': ('┐', '+'),
    'corner_bl': ('└', '+'),
    'corner_br': ('┘', '+'),
    'tee_l': ('├', '+'),
    'tee_r': ('┤', '+'),
    'bar_full': ('█', '#'),
    'bar_empty': ('░', '.'),
    'check': ('✓', 'y'),
    'cross': ('✗', 'x'),
    'lock': ('■', '#'),
    'open': ('□', 'o'),
    'node': ('●', '*'),
    'ellipsis': ('…', '...'),
    'degree': ('°', 'o'),
    # The two diagonals the drawn city map needs (D57).
    'diag_dn': ('╲', '\\'),
    'diag_up': ('╱', '/'),
}


#: Box-drawing sets. The player picks one; nothing in the game asks for a
#: specific character. Overrides land on top of `GLYPHS`, so a set only has to
#: name what it changes, and anything it does not name keeps the default.
#:
#: All of these collapse to the ASCII rung untouched, because `g()` checks the
#: capability before it checks the preference: a decorated frame that a
#: terminal cannot draw is worse than no decoration.
FRAMES: dict[str, dict[str, str]] = {
    'single': {},
    'double': {'hline': '═', 'vline': '║', 'corner_tl': '╔', 'corner_tr': '╗',
               'corner_bl': '╚', 'corner_br': '╝', 'tee_l': '╠', 'tee_r': '╣'},
    'heavy': {'hline': '━', 'vline': '┃', 'corner_tl': '┏', 'corner_tr': '┓',
              'corner_bl': '┗', 'corner_br': '┛', 'tee_l': '┣', 'tee_r': '┫'},
    'rounded': {'corner_tl': '╭', 'corner_tr': '╮',
                'corner_bl': '╰', 'corner_br': '╯'},
    'dotted': {'hline': '┄', 'vline': '┆', 'corner_tl': '┌', 'corner_tr': '┐',
               'corner_bl': '└', 'corner_br': '┘'},
    'wire': {'hline': '─', 'vline': '│', 'corner_tl': '┼', 'corner_tr': '┼',
             'corner_bl': '┼', 'corner_br': '┼', 'tee_l': '┼', 'tee_r': '┼'},
    'rule': {'hline': '━', 'corner_tl': ' ', 'corner_tr': ' ',
             'corner_bl': ' ', 'corner_br': ' ', 'tee_l': ' ', 'tee_r': ' '},
    'scan': {'hline': '╌', 'vline': '╎', 'corner_tl': '·', 'corner_tr': '·',
             'corner_bl': '·', 'corner_br': '·', 'tee_l': '·', 'tee_r': '·'},
    'bracket': {'hline': '─', 'vline': '│', 'corner_tl': '⌜', 'corner_tr': '⌝',
                'corner_bl': '⌞', 'corner_br': '⌟', 'tee_l': '├', 'tee_r': '┤'},
    'slab': {'hline': '▄', 'vline': '█', 'corner_tl': '▗', 'corner_tr': '▖',
             'corner_bl': '▝', 'corner_br': '▘', 'tee_l': '▐', 'tee_r': '▌'},
    'rail': {'hline': '═', 'vline': '│', 'corner_tl': '╒', 'corner_tr': '╕',
             'corner_bl': '╘', 'corner_br': '╛', 'tee_l': '╞', 'tee_r': '╡'},
    'quiet': {'hline': ' ', 'corner_tl': ' ', 'corner_tr': ' ',
              'corner_bl': ' ', 'corner_br': ' ', 'tee_l': ' ', 'tee_r': ' '},
}

#: Meter fills. Same override mechanism, kept separate because a player who
#: wants a heavy frame does not necessarily want a heavy bar.
BARS: dict[str, dict[str, str]] = {
    'blocks': {},
    'shaded': {'bar_full': '▓', 'bar_empty': '░'},
    'solid': {'bar_full': '█', 'bar_empty': ' '},
    'dots': {'bar_full': '●', 'bar_empty': '○'},
    'line': {'bar_full': '━', 'bar_empty': '╌'},
    'ladder': {'bar_full': '▮', 'bar_empty': '▯'},
    'wave': {'bar_full': '▰', 'bar_empty': '▱'},
    'ascii': {'bar_full': '#', 'bar_empty': '.'},
    'braille': {'bar_full': '⣿', 'bar_empty': '⣀'},
    'arrows': {'bar_full': '▶', 'bar_empty': '▷'},
    'sharp': {'bar_full': '◼', 'bar_empty': '◻'},
    'pipe': {'bar_full': '┃', 'bar_empty': '┊'},
}

#: Bullets and pointers, which are the other thing people change.
MARKS: dict[str, dict[str, str]] = {
    'plain': {},
    'angular': {'bullet': '▸', 'arrow': '»', 'check': '✔', 'cross': '✘'},
    'minimal': {'bullet': '-', 'arrow': '>', 'check': '+', 'cross': '-'},
    'geometric': {'bullet': '◆', 'arrow': '▶', 'check': '◉', 'cross': '◌',
                  'node': '◆', 'lock': '◼', 'open': '◻'},
    'runic': {'bullet': '·', 'arrow': '→', 'check': '√', 'cross': '×',
              'node': '◇', 'lock': '▪', 'open': '▫'},
    'stars': {'bullet': '✦', 'arrow': '➜', 'check': '★', 'cross': '✧',
              'node': '✦', 'lock': '✥', 'open': '✧'},
    'ticks': {'bullet': '›', 'arrow': '⟶', 'check': '✓', 'cross': '✕',
              'node': '•', 'lock': '▰', 'open': '▱'},
    'medical': {'bullet': '▁', 'arrow': '⟩', 'check': '♥', 'cross': '⚕',
                'node': '◉', 'lock': '▮', 'open': '▯'},
    # What a courier chalks on a wall for the next courier (D65).
    'kerbside': {'bullet': '⌐', 'arrow': '↳', 'check': '✓', 'cross': '⌗',
                 'node': '⌂', 'lock': '⌷', 'open': '⌸'},
}


@dataclass(frozen=True, slots=True)
class Caps:
    color: ColorLevel
    glyphs: GlyphLevel
    width: int
    palette: Palette
    #: The player's shell, per the rice catalogue. Names rather than tables so
    #: that a saved preference for a set this build no longer ships degrades
    #: to the default instead of raising.
    frame: str = 'single'
    bars: str = 'blocks'
    marks: str = 'plain'

    def g(self, name: str) -> str:
        """Glyph by name at the supported rung, then at the chosen style.

        Capability first, preference second, and never the other way round. A
        decorated frame a terminal cannot draw is worse than no decoration,
        so the ASCII rung ignores every set here.
        """
        pair = GLYPHS[name]
        if self.glyphs is not GlyphLevel.UNICODE:
            return pair[1]
        for table, key in ((FRAMES, self.frame), (BARS, self.bars),
                           (MARKS, self.marks)):
            override = table.get(key, {}).get(name)
            if override is not None:
                return override
        return pair[0]

    @property
    def text_width(self) -> int:
        return min(TEXT_WIDTH, self.width)


def detect_caps(theme_name: str | None = None, ascii_only: bool = False,
                no_color: bool = False, stream=None) -> Caps:
    color = ColorLevel.NONE if no_color else detect_color(stream)
    glyphs = GlyphLevel.ASCII if ascii_only else detect_glyphs(stream)
    pal = theme.get(theme_name)
    if pal.name == 'ansi' and color > ColorLevel.ANSI16:
        color = ColorLevel.ANSI16
    width = shutil.get_terminal_size((MIN_COLS, 24)).columns
    return Caps(color=color, glyphs=glyphs, width=max(40, width), palette=pal)


# --------------------------------------------------------------------------
# markup
# --------------------------------------------------------------------------

#: A role, or a colour: `[#ff1744]` is a twenty-four-bit colour in the
#: markup (D103), for the gradients, which no palette role can express.
#: It degrades like a role: the cube at 256, the nearest of sixteen below.
_TAG = re.compile(r'\[(/|#[0-9a-fA-F]{6}|[a-z_][a-z0-9_]*)\]')
#: Control sequences, for stripping already-rendered output back to text.
_ANSI = re.compile(r'\033\[[0-9;?]*[a-zA-Z]')

#: Styles that are not palette roles. Kept separate so `validate.py` can tell a
#: typo'd role from a legitimate attribute.
ATTRS = frozenset({'bold', 'ul', 'rev'})


# --------------------------------------------------------------------------
# footnotes
# --------------------------------------------------------------------------

#: Superscript markers. Ten is a hard ceiling on notes in one block and that
#: is a feature: the eleventh footnote is a sign the writing has lost the
#: thread, not a sign the numbering needs extending.
_SUPER = '⁰¹²³⁴⁵⁶⁷⁸⁹'
MAX_NOTES = 9


def note_marker(n: int, ascii_only: bool = False) -> str:
    """The little raised number. `[n]` where Unicode is not safe."""
    if ascii_only or not 0 < n < 10:
        return f'[{n}]'
    return _SUPER[n]


def split_notes(s: str, start: int = 1,
                ascii_only: bool = False) -> tuple[str, list[str]]:
    """Pull `{{footnotes}}` out of a markup string, leaving numbered markers.

    Footnotes nest, because the whole reason to have them is the writer who
    gets halfway through an aside and needs an aside about the aside. An
    inner note is numbered after its parent and printed as its own line, so
    the reader can follow it or not.

    Returns the text with markers substituted, and the notes in printing
    order. Deliberately operates on the markup string before `parse`, so a
    footnote can carry styling and a styled span can carry a footnote.
    """
    out: list[str] = []
    notes: list[str] = []
    counter = start
    i = 0
    while i < len(s):
        if s.startswith('{{', i):
            depth, j = 1, i + 2
            while j < len(s) and depth:
                if s.startswith('{{', j):
                    depth += 1
                    j += 2
                elif s.startswith('}}', j):
                    depth -= 1
                    j += 2
                else:
                    j += 1
            if depth:
                # Unterminated. Same policy as an unclosed tag: print the text
                # rather than lose a line of flavour to a missing brace.
                out.append(s[i:])
                break
            n = counter
            counter += 1
            slot = len(notes)
            notes.append('')
            inner, deeper = split_notes(s[i + 2:j - 2], counter, ascii_only)
            counter += len(deeper)
            notes[slot] = inner
            notes.extend(deeper)
            out.append(note_marker(n, ascii_only))
            i = j
            continue
        out.append(s[i])
        i += 1
    return ''.join(out), notes


@dataclass(frozen=True, slots=True)
class Span:
    text: str
    role: str | None = None
    attrs: frozenset[str] = frozenset()


def parse(s: str) -> list[Span]:
    """Split markup into styled spans.

    `[[` is a literal `[`, which is the only escape and is needed because the
    game prints things like `[[ SEVERED ]]` as banner text. Unclosed tags are
    closed implicitly at the end of the string rather than raising, because a
    missing `[/]` in one line of flavour text should not crash a run; the
    checker in `validate.py` is where that gets caught.
    """
    out: list[Span] = []
    stack: list[str] = []
    buf: list[str] = []
    i = 0

    def flush() -> None:
        if buf:
            role = next((t for t in reversed(stack) if t not in ATTRS), None)
            attrs = frozenset(t for t in stack if t in ATTRS)
            out.append(Span(''.join(buf), role, attrs))
            buf.clear()

    while i < len(s):
        if s.startswith('[[', i):
            buf.append('[')
            i += 2
            continue
        m = _TAG.match(s, i)
        if m:
            flush()
            tag = m.group(1)
            if tag == '/':
                if stack:
                    stack.pop()
            else:
                stack.append(tag)
            i = m.end()
            continue
        buf.append(s[i])
        i += 1
    flush()
    return out


def plain(s: str) -> str:
    """The text a human sees, with all markup removed."""
    return ''.join(sp.text for sp in parse(s))


def char_width(ch: str) -> int:
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1


def width(s: str) -> int:
    """Display columns of a markup string."""
    return sum(char_width(c) for c in plain(s))


def _sgr(caps: Caps, role: str | None, attrs: frozenset[str]) -> str:
    if caps.color is ColorLevel.NONE:
        return ''
    parts: list[str] = []
    if 'bold' in attrs:
        parts.append('1')
    if 'ul' in attrs:
        parts.append('4')
    if 'rev' in attrs:
        parts.append('7')
    if role and role.startswith('#'):
        r, g, b = theme._hex_rgb(role)
        if caps.color is ColorLevel.TRUE:
            parts.append(f'38;2;{r};{g};{b}')
        elif caps.color is ColorLevel.ANSI256:
            parts.append(f'38;5;{theme._to_256(role)}')
        else:
            parts.append(str(theme.ANSI16[nearest_ansi(r, g, b)]))
    elif role:
        col = getattr(caps.palette, role, None)
        if col is not None:
            if caps.color is ColorLevel.TRUE:
                r, g, b = col.rgb
                parts.append(f'38;2;{r};{g};{b}')
            elif caps.color is ColorLevel.ANSI256:
                parts.append(f'38;5;{col.c256}')
            else:
                parts.append(str(theme.ANSI16[col.ansi]))
    return f'\033[{";".join(parts)}m' if parts else ''


#: The sixteen, as points, for the rung that has nothing else.
_ANSI_POINTS = {
    'black': (0, 0, 0), 'red': (170, 0, 0), 'green': (0, 170, 0),
    'yellow': (170, 140, 0), 'blue': (0, 0, 170), 'magenta': (170, 0, 170),
    'cyan': (0, 170, 170), 'white': (190, 190, 190),
    'brightblack': (100, 100, 100), 'brightred': (255, 80, 80),
    'brightgreen': (80, 255, 80), 'brightyellow': (255, 255, 80),
    'brightblue': (90, 90, 255), 'brightmagenta': (255, 80, 255),
    'brightcyan': (80, 255, 255), 'brightwhite': (255, 255, 255),
}


def nearest_ansi(r: int, g: int, b: int) -> str:
    """The closest of the sixteen to a colour, by distance."""
    return min(_ANSI_POINTS, key=lambda k: sum(
        (a - c) ** 2 for a, c in zip(_ANSI_POINTS[k], (r, g, b))))


def blend(stops, t: float) -> str:
    """A colour along a list of hex stops, as hex, at t in [0, 1]."""
    t = max(0.0, min(1.0, t))
    if len(stops) == 1:
        return stops[0]
    pos = t * (len(stops) - 1)
    i = min(len(stops) - 2, int(pos))
    f = pos - i
    a, b = theme._hex_rgb(stops[i]), theme._hex_rgb(stops[i + 1])
    return '#%02x%02x%02x' % tuple(int(round(x + (y - x) * f))
                                   for x, y in zip(a, b))


#: Cool to hot: what a rising number looks like (D103).
HEAT_STOPS = ('#00c853', '#c6ff00', '#ffab00', '#ff6d00', '#ff1744')


def gradient_bar(pct: float, cells: int, caps: Caps, stops=HEAT_STOPS,
                 label: str | None = None, label_role: str = 'trace') -> str:
    """A meter whose fill is coloured by how far along it is, as markup.

    Where the terminal has no colour it is the plain bar: the number is
    the same, which is the whole of D35.
    """
    pct = max(0.0, min(1.0, pct))
    filled = int(round(pct * cells))
    full, empty = caps.g('bar_full'), caps.g('bar_empty')
    parts, last = [], None
    for i in range(filled):
        colour = blend(stops, i / max(1, cells - 1))
        if colour != last:
            if last is not None:
                parts.append('[/]')
            parts.append(f'[{colour}]')
            last = colour
        parts.append(full)
    if last is not None:
        parts.append('[/]')
    parts.append(f'[dim]{empty * (cells - filled)}[/]')
    if label is not None:
        parts.append(f' [{label_role}]{label}[/]')
    return ''.join(parts)


def sparkline_coloured(values, cells: int, caps: Caps, lo: float = 0.0,
                       hi: float | None = None, stops=HEAT_STOPS) -> str:
    """`sparkline`, with every column coloured by its own level."""
    line = sparkline(values, cells, caps, lo, hi)
    if not line:
        return ''
    chars = SPARK if caps.glyphs is GlyphLevel.UNICODE else SPARK_ASCII
    parts, last = [], None
    for ch in line:
        level = chars.index(ch) / max(1, len(chars) - 1) if ch in chars else 0.0
        colour = blend(stops, level)
        if colour != last:
            if last is not None:
                parts.append('[/]')
            parts.append(f'[{colour}]')
            last = colour
        parts.append(ch)
    if last is not None:
        parts.append('[/]')
    return ''.join(parts)


def render(s: str, caps: Caps) -> str:
    """Markup to a printable string at the terminal's actual rung."""
    spans = parse(s)
    if caps.color is ColorLevel.NONE:
        return ''.join(sp.text for sp in spans)
    out: list[str] = []
    for sp in spans:
        code = _sgr(caps, sp.role, sp.attrs)
        out.append(f'{code}{sp.text}\033[0m' if code else sp.text)
    return ''.join(out)


def wrap(s: str, cols: int, indent: str = '', subsequent: str | None = None) -> list[str]:
    """Word-wrap a markup string, preserving styling across line breaks.

    Wrapping happens on the plain text and the markup is re-emitted per line,
    because a naive wrap that counts escape codes as characters produces
    ragged output that looks like a rendering bug and is maddening to chase.
    """
    sub = indent if subsequent is None else subsequent
    spans = parse(s)
    lines: list[list[Span]] = [[]]
    col = len(indent)
    limit = max(20, cols)

    for sp in spans:
        # Split on whitespace but keep it, so runs of spaces survive. Padding
        # is meaningful in this game's output: `help` and `skills` both align
        # columns by emitting explicit runs of spaces, and collapsing them to
        # one turns every aligned listing into ragged prose.
        for word in re.split(r'(\s+)', sp.text):
            if not word:
                continue
            if word.isspace():
                if '\n' in word:
                    for _ in range(word.count('\n')):
                        lines.append([])
                        col = len(sub)
                    continue
                # Only meaningful once the line has something on it; leading
                # whitespace is what `indent` is for.
                if lines[-1]:
                    lines[-1].append(Span(word, sp.role, sp.attrs))
                    col += len(word)
                continue
            w = sum(char_width(c) for c in word)
            if col + w > limit and lines[-1]:
                # Drop trailing whitespace before breaking.
                while lines[-1] and lines[-1][-1].text.isspace():
                    lines[-1].pop()
                lines.append([])
                col = len(sub)
            lines[-1].append(Span(word, sp.role, sp.attrs))
            col += w

    out: list[str] = []
    for n, line in enumerate(lines):
        pre = indent if n == 0 else sub
        body = ''.join(_remark(sp) for sp in line)
        out.append(pre + body if body else pre.rstrip())
    return out


def _remark(sp: Span) -> str:
    """A span back to markup, so wrapped lines can be re-parsed downstream."""
    text = sp.text.replace('[', '[[')
    tags = list(sp.attrs) + ([sp.role] if sp.role else [])
    if not tags:
        return text
    return ''.join(f'[{t}]' for t in tags) + text + '[/]' * len(tags)


# --------------------------------------------------------------------------
# console
# --------------------------------------------------------------------------


class Console:
    """Everything the game prints goes through one of these.

    Holds a capture buffer rather than writing straight to the stream when
    `capture` is set, which is how `test.py` plays a session and asserts on
    what came back without a pty.
    """

    def __init__(self, caps: Caps, stream=None) -> None:
        self.caps = caps
        self.stream = stream or sys.stdout
        self.captured: list[str] | None = None
        #: Everything printed this session, plain, for the `log` command.
        self.transcript: list[str] = []
        #: Footnotes collected from this block, flushed at the end of the
        #: command. Held on the console rather than passed around because a
        #: paragraph is usually several `say` calls and the notes belong at the
        #: bottom of all of them, the way they do on a page.
        self.pending_notes: list[str] = []

    # -- primitives --------------------------------------------------------

    def raw(self, s: str = '') -> None:
        """One already-wrapped markup line.

        Collects footnotes too, so a `raw` call is not a hole in the feature.
        `say` has already stripped them by the time it gets here, so this only
        fires for content that reached the console directly.
        """
        s = self.collect_notes(s)
        self.transcript.append(plain(s))
        text = render(s, self.caps)
        if self.captured is not None:
            self.captured.append(text)
            return
        print(text, file=self.stream)

    def emit(self, s: str = '') -> None:
        """A line that is already rendered. No markup parsing, no wrapping.

        The one hole in "everything goes through Console", and it exists for
        `anim.py`, which composes raw SGR gradients per character and would
        otherwise have to escape every escape it writes. The transcript gets
        the text with the control codes stripped, so `log` stays readable.
        """
        self.transcript.append(_ANSI.sub('', s))
        if self.captured is not None:
            self.captured.append(s)
            return
        print(s, file=self.stream)

    def blank(self) -> None:
        self.raw('')

    def say(self, s: str = '', indent: str = '', subsequent: str | None = None) -> None:
        """Wrapped prose. The default for anything sentence-shaped.

        Any `{{aside}}` in the text is lifted out here, replaced with a raised
        number, and printed under the block by `footnotes()`.
        """
        s = self.collect_notes(s)
        for line in wrap(s, self.caps.text_width, indent, subsequent):
            self.raw(line)

    # -- footnotes ---------------------------------------------------------

    def collect_notes(self, s: str) -> str:
        """Strip footnotes from a string and queue them. Returns the text."""
        if '{{' not in s:
            return s
        ascii_only = self.caps.glyphs is GlyphLevel.ASCII
        text, notes = split_notes(s, len(self.pending_notes) + 1, ascii_only)
        self.pending_notes.extend(notes)
        return text

    def footnotes(self) -> None:
        """Print and clear whatever asides this block accumulated."""
        if not self.pending_notes:
            return
        notes, self.pending_notes = self.pending_notes[:MAX_NOTES], []
        ascii_only = self.caps.glyphs is GlyphLevel.ASCII
        self.blank()
        for i, text in enumerate(notes, 1):
            mark = note_marker(i, ascii_only)
            for line in wrap(f'[dim]{mark} {text}[/]', self.caps.text_width,
                             indent=' ', subsequent='   '):
                self.raw(line)

    # -- semantic shorthands ----------------------------------------------

    def ok(self, s: str) -> None:
        self.say(f"[ok]{self.caps.g('check')}[/] {s}")

    def warn(self, s: str) -> None:
        self.say(f"[warn]![/] {s}", subsequent='  ')

    def err(self, s: str) -> None:
        self.say(f"[err]{self.caps.g('cross')}[/] {s}", subsequent='  ')

    def info(self, s: str) -> None:
        self.say(f"[dim]{self.caps.g('bullet')}[/] {s}", subsequent='  ')

    # -- structure ---------------------------------------------------------

    def rule(self, title: str = '', role: str = 'border') -> None:
        w = self.caps.text_width
        h = self.caps.g('hline')
        if not title:
            self.raw(f'[{role}]{h * w}[/]')
            return
        label = f' {title} '
        left = 3
        right = max(0, w - left - width(label))
        self.raw(f'[{role}]{h * left}[/][accent]{label}[/][{role}]{h * right}[/]')

    def header(self, title: str, right: str = '') -> None:
        """A section heading. Deliberately plain: this is a shell, not a GUI."""
        self.blank()
        pad = self.caps.text_width - width(title) - width(right)
        line = f'[accent][bold]{title}[/][/]'
        if right:
            line += ' ' * max(1, pad) + f'[dim]{right}[/]'
        self.raw(line)
        self.rule()

    def kv(self, pairs, key_width: int | None = None, role: str = 'muted') -> None:
        """Aligned label/value rows. The workhorse of every inspection command."""
        pairs = [(k, v) for k, v in pairs]
        if not pairs:
            return
        kw = key_width or max(width(k) for k, _ in pairs)
        hang = ' ' * (kw + 2)
        for k, v in pairs:
            pad = ' ' * max(0, kw - width(k))
            # Values wrap under themselves rather than off the edge: several
            # of these carry a whole sentence of faction doctrine.
            for line in wrap(f'[{role}]{k}[/]{pad}  {v}',
                             self.caps.text_width, subsequent=hang):
                self.raw(line)

    def table(self, headers, rows, roles=None) -> None:
        """Left-aligned columns sized to content, truncated to fit the width.

        No borders. Borders in a scrollback-heavy game turn the log into a
        wall, and this output has to be readable when fifty lines of it are
        stacked above the prompt.
        """
        if not rows:
            return
        cols = len(headers)
        widths = [width(h) for h in headers]
        for row in rows:
            for i in range(cols):
                widths[i] = max(widths[i], width(str(row[i])))
        avail = self.caps.text_width - 2 * (cols - 1)
        while sum(widths) > avail:
            widths[widths.index(max(widths))] -= 1

        head = '  '.join(f'[dim][ul]{h}[/][/]' + ' ' * max(0, widths[i] - width(h))
                         for i, h in enumerate(headers))
        self.raw(head.rstrip())
        for row in rows:
            cells = []
            for i, cell in enumerate(row):
                s = truncate(str(cell), widths[i], self.caps)
                role = roles[i] if roles else None
                s = f'[{role}]{s}[/]' if role else s
                cells.append(s + ' ' * max(0, widths[i] - width(s)))
            self.raw('  '.join(cells).rstrip())

    def box(self, lines, title: str = '', role: str = 'border') -> None:
        """A framed block. Rare, on purpose: borders in a scrollback game turn
        the log into a wall, so this is for the one card at the end of a run
        (D62) and nothing that prints every tick. Lines are markup and are
        wrapped to fit; the frame glyphs come from the player's chosen set."""
        g = self.caps.g
        w = self.caps.text_width
        h, v = g('hline'), g('vline')
        tl, tr, bl, br = (g('corner_tl'), g('corner_tr'), g('corner_bl'),
                          g('corner_br'))
        inner = w - 4
        if title:
            label = f' {title} '
            top = (f'[{role}]{tl}{h}[/][accent]{label}[/][{role}]'
                   f'{h * max(0, w - 3 - width(label))}{tr}[/]')
        else:
            top = f'[{role}]{tl}{h * (w - 2)}{tr}[/]'
        self.raw(top)
        for line in lines:
            for piece in wrap(line, inner):
                pad = ' ' * max(0, inner - width(piece))
                self.raw(f'[{role}]{v}[/] {piece}{pad} [{role}]{v}[/]')
        self.raw(f'[{role}]{bl}{h * (w - 2)}{br}[/]')

    def bar(self, pct: float, role: str = 'accent', cells: int = 20,
            label: str | None = None) -> str:
        """A meter as a markup string, for embedding in a status line.

        Returns rather than prints, because meters almost always want to sit
        beside something else.
        """
        pct = max(0.0, min(1.0, pct))
        filled = int(round(pct * cells))
        full, empty = self.caps.g('bar_full'), self.caps.g('bar_empty')
        text = f'[{role}]{full * filled}[/][dim]{empty * (cells - filled)}[/]'
        if label is not None:
            text += f' [{role}]{label}[/]'
        return text

    def columns(self, items, role: str | None = None,
                gap: int = 2, indent: str = '  ') -> None:
        """A long list of short things, down the page in columns (D68).

        Forty verbs in one column is a scroll; forty verbs in four is a
        list you can read. Sized to the widest item and the terminal, and
        it degrades to one column on a narrow one without special-casing.
        """
        items = [str(i) for i in items]
        if not items:
            return
        widest = max(width(i) for i in items)
        avail = self.caps.text_width - len(indent)
        cols = max(1, min(len(items), (avail + gap) // (widest + gap)))
        rows = (len(items) + cols - 1) // cols
        for r in range(rows):
            cells = []
            for col in range(cols):
                i = col * rows + r
                if i >= len(items):
                    continue
                text = items[i]
                pad = ' ' * max(0, widest - width(text))
                shown = f'[{role}]{text}[/]' if role else text
                cells.append(shown + pad)
            self.raw(indent + (' ' * gap).join(cells).rstrip())

    def chip(self, text: str, role: str = 'accent') -> str:
        """A small inline tag: `[ held ]`. Returns markup for embedding."""
        return f'[dim][[/][{role}]{text}[/][dim]][/]'

    def bullets(self, items, role: str | None = None) -> None:
        b = self.caps.g('bullet')
        for it in items:
            s = f'[{role}]{it}[/]' if role else it
            self.say(f'[dim]{b}[/] {s}', subsequent='  ')

    # -- capture -----------------------------------------------------------

    def start_capture(self) -> None:
        self.captured = []

    def end_capture(self) -> str:
        out = '\n'.join(self.captured or [])
        self.captured = None
        return out


#: Eight levels of block, for inline history. The whole point of a sparkline
#: is that it costs one row: a game whose central tension is one number rising
#: should be able to show you the shape of that rise without spending a chart
#: on it.
SPARK = '▁▂▃▄▅▆▇█'
SPARK_ASCII = '_.-~=+*#'


def sparkline(values, cells: int, caps: Caps,
              lo: float = 0.0, hi: float | None = None) -> str:
    """A series as one row of blocks, resampled to `cells` columns.

    Scaled against a caller-supplied range rather than against the data, so
    successive readings are comparable. Auto-scaling would make a trace that
    crept from 2% to 4% look identical to one that went from 10% to 90%, which
    is the exact misreading this is meant to prevent.
    """
    chars = SPARK if caps.glyphs is GlyphLevel.UNICODE else SPARK_ASCII
    series = list(values)
    if not series or cells < 1:
        return ''
    top = max(series) if hi is None else hi
    span = max(1e-9, top - lo)
    out = []
    for i in range(cells):
        # Resample by bucket rather than by index, so a long run does not
        # simply drop most of its own history on the floor.
        start = int(i * len(series) / cells)
        end = max(start + 1, int((i + 1) * len(series) / cells))
        chunk = series[start:end]
        if not chunk:
            out.append(chars[0])
            continue
        level = (sum(chunk) / len(chunk) - lo) / span
        out.append(chars[max(0, min(len(chars) - 1,
                                    int(level * (len(chars) - 1) + 0.5)))])
    return ''.join(out)


# --------------------------------------------------------------------------
# graphs, drawn as trees
# --------------------------------------------------------------------------
#
# A graph is not a tree and a terminal is good at trees, so both maps in this
# game do the same thing: walk breadth-first from a root, draw what the walk
# covers, and report the edges it could not use underneath. Breadth-first
# rather than depth-first on purpose, because it puts every node at its true
# distance from the root, and that distance is the number the player is
# actually reasoning about: hops to open in a network, shifts to walk in a
# city.
#
# This lives here rather than with either map because it knows nothing about
# hosts or districts. It takes an adjacency dict and returns strings.


def spanning_tree(edges: dict[str, list[str]], root: str,
                  visible: set[str]) -> tuple[dict[str, list[str]],
                                              dict[str, list[str]]]:
    """Lay the visible part of a graph out as a tree from `root`.

    Returns (children, extra), where `extra` maps a node to the visible nodes
    it also touches that the tree could not show.
    """
    children: dict[str, list[str]] = {}
    extra: dict[str, list[str]] = {}
    if root not in edges:
        return children, extra
    seen = {root}
    parent: dict[str, str] = {}
    queue = [root]
    while queue:
        uid = queue.pop(0)
        kids, others = [], []
        for edge in edges.get(uid, ()):
            if edge not in visible or edge not in edges:
                continue
            if edge in seen:
                # An edge back into the tree. Real, and worth telling the
                # player about, because a second route to a place is a second
                # route out of one. The edge back to this node's own parent is
                # not one of those: the tree already draws it, and reporting it
                # would list every single link twice.
                if edge != uid and parent.get(uid) != edge:
                    others.append(edge)
                continue
            seen.add(edge)
            parent[edge] = uid
            kids.append(edge)
            queue.append(edge)
        children[uid] = kids
        if others:
            extra[uid] = others
    return children, extra


def tree_rows(edges: dict[str, list[str]], root: str, visible: set[str],
              ascii_only: bool = False) -> list[tuple[str, str]]:
    """(prefix, node) for every visible node, in drawing order.

    The prefix carries the box-drawing. Split from the labelling so a caller
    can style each node however it likes without this function knowing
    anything about markup or colour.
    """
    if root not in edges:
        return []
    children, _ = spanning_tree(edges, root, visible)
    tee, elbow = ('+- ', '\\- ') if ascii_only else ('├─ ', '└─ ')
    pipe, gap = ('|  ', '   ') if ascii_only else ('│  ', '   ')
    rows: list[tuple[str, str]] = []

    def walk(uid: str, prefix: str) -> None:
        for i, kid in enumerate(children.get(uid, [])):
            last = i == len(children[uid]) - 1
            rows.append((prefix + (elbow if last else tee), kid))
            walk(kid, prefix + (gap if last else pipe))

    rows.append(('', root))
    walk(root, '')
    return rows


def tree_leads(rows: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """The same rows, with every prefix padded to a common width.

    A tree prefix is as wide as the node is deep, so anything a caller prints
    after it starts in a different column on every row and the whole thing
    reads as a table somebody has knocked askew.

    Padded with the horizontal rule rather than with spaces, because a branch
    that stops three characters short of the thing it points at is a branch
    pointing at nothing. The root gets spaces: it is not on a branch.

    Which rule to pad with is read off the rows rather than passed in. It is
    the one thing about these prefixes a caller could get wrong, `tree_rows`
    has already made the decision, and a mismatched flag would draw a unicode
    tree with hyphens through it.
    """
    lead = max((len(prefix) for prefix, _ in rows), default=0)
    rule = '─' if any('─' in prefix for prefix, _ in rows) else '-'
    out = []
    for prefix, uid in rows:
        if not prefix:
            out.append((' ' * lead, uid))
            continue
        # Every prefix from `tree_rows` ends in the one space that separates
        # its connector from the label, so stripping takes that and nothing
        # structural, and the space is put back on the end of the run.
        body = prefix.rstrip()
        out.append((body + rule * max(0, lead - len(body) - 1) + ' ', uid))
    return out


def shortest_path(edges: dict[str, list[str]], start: str,
                  goal: str) -> list[str]:
    """The fewest hops from `start` to `goal`, `start` excluded.

    Empty when there is no route, and empty when you are already there, which
    are the same answer to the only question a caller asks: what do I still
    have to walk.
    """
    if start == goal or start not in edges or goal not in edges:
        return []
    parent: dict[str, str] = {start: ''}
    queue = [start]
    while queue:
        here = queue.pop(0)
        for step in edges.get(here, ()):
            if step in parent or step not in edges:
                continue
            parent[step] = here
            if step == goal:
                path = [goal]
                while parent[path[-1]]:
                    path.append(parent[path[-1]])
                return list(reversed(path[:-1]))
            queue.append(step)
    return []


def truncate(s: str, cols: int, caps: Caps) -> str:
    """Cut a markup string to fit, appending an ellipsis glyph if it had to."""
    if width(s) <= cols:
        return s
    ell = caps.g('ellipsis')
    budget = cols - len(ell)
    out: list[str] = []
    used = 0
    for sp in parse(s):
        for ch in sp.text:
            w = char_width(ch)
            if used + w > budget:
                out.append(f'[dim]{ell}[/]')
                return ''.join(out)
            out.append(_remark(Span(ch, sp.role, sp.attrs)))
            used += w
    return ''.join(out)
