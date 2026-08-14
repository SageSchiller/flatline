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
}


@dataclass(frozen=True, slots=True)
class Caps:
    color: ColorLevel
    glyphs: GlyphLevel
    width: int
    palette: Palette

    def g(self, name: str) -> str:
        """Glyph by name at the supported rung."""
        pair = GLYPHS[name]
        return pair[0] if self.glyphs is GlyphLevel.UNICODE else pair[1]

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

_TAG = re.compile(r'\[(/|[a-z_][a-z0-9_]*)\]')
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
    if role:
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
