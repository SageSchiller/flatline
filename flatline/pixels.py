"""Pictures, in a terminal (D102).

Everything the game draws is text: one glyph, one colour, per cell. That is
the D16 ladder and it is right, but it means the most a faction's cyberspace
ever got was an eleven-by-four mark. A terminal that can do twenty-four-bit
colour can also do two pixels per cell, because the upper-half block `▀`
takes a foreground and a background and they need not agree. Forty cells
wide and eight rows tall is a forty-by-sixteen picture, and that is enough
to make a Kagawa network look like terraces and a Sendai one look like a
black room with something in it.

Nothing here is allowed to matter (D35). A picture is composed from a
faction key, a size and a seed, deterministically, and it is drawn or it
is not: at 256 colours it is drawn in the cube, at sixteen or in ASCII it
is not drawn at all and the text mark stands in for it. `blit` is the only
thing that emits escapes, and it coalesces runs so a picture is a few
hundred bytes rather than a few thousand.
"""

from __future__ import annotations

import math
import random

from .theme import Color
from .ui import Caps, ColorLevel, GlyphLevel

RGB = tuple[int, int, int]
RESET = '\033[0m'

#: Default picture size in pixels: forty cells by eight rows of text.
WIDTH = 40
HEIGHT = 16


def can_render(caps: Caps) -> bool:
    """Whether this terminal gets pictures at all."""
    return (caps.color >= ColorLevel.ANSI256
            and caps.glyphs is GlyphLevel.UNICODE)


def _sgr(rgb: RGB, caps: Caps, background: bool) -> str:
    if caps.color is ColorLevel.TRUE:
        return f'\033[{48 if background else 38};2;{rgb[0]};{rgb[1]};{rgb[2]}m'
    if caps.color is ColorLevel.ANSI256:
        index = Color('#%02x%02x%02x' % rgb, 'white').c256
        return f'\033[{48 if background else 38};5;{index}m'
    return ''


def blit(pix: list[list[RGB | None]], caps: Caps) -> list[str]:
    """Rows of pixels to rows of text, two pixels per cell.

    A `None` pixel is transparent: the terminal's own background shows.
    Runs of identical cells share one escape, which matters at forty cells
    a row: a picture is a handful of sequences per row, not one per cell.
    """
    if not can_render(caps) or not pix:
        return []
    out: list[str] = []
    for y in range(0, len(pix), 2):
        top = pix[y]
        bottom = pix[y + 1] if y + 1 < len(pix) else [None] * len(top)
        cells = []
        for x in range(len(top)):
            t = top[x]
            b = bottom[x] if x < len(bottom) else None
            if t is None and b is None:
                cells.append(('', ' '))
            elif t is None:
                cells.append((_sgr(b, caps, False), '▄'))
            elif b is None:
                cells.append((_sgr(t, caps, False), '▀'))
            else:
                cells.append((_sgr(t, caps, False) + _sgr(b, caps, True), '▀'))
        line, last = [], None
        for code, glyph in cells:
            if code != last:
                line.append(RESET if not code else code)
                last = code
            line.append(glyph)
        out.append(''.join(line) + RESET)
    return out


# --------------------------------------------------------------------------
# a little maths
# --------------------------------------------------------------------------


def lerp(a: RGB, b: RGB, t: float) -> RGB:
    t = max(0.0, min(1.0, t))
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))  # type: ignore


def shade(rgb: RGB, k: float) -> RGB:
    return tuple(max(0, min(255, int(round(c * k)))) for c in rgb)  # type: ignore


def _blank(w: int, h: int, fill: RGB | None = None):
    return [[fill for _ in range(w)] for _ in range(h)]


def _rect(pix, x0: int, y0: int, x1: int, y1: int, rgb: RGB) -> None:
    for y in range(max(0, y0), min(len(pix), y1)):
        row = pix[y]
        for x in range(max(0, x0), min(len(row), x1)):
            row[x] = rgb


def _put(pix, x: int, y: int, rgb: RGB) -> None:
    if 0 <= y < len(pix) and 0 <= x < len(pix[y]):
        pix[y][x] = rgb


def _line(pix, x0: float, y0: float, x1: float, y1: float, rgb: RGB) -> None:
    steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(steps + 1):
        t = i / max(1, steps)
        _put(pix, int(round(x0 + (x1 - x0) * t)),
             int(round(y0 + (y1 - y0) * t)), rgb)


# --------------------------------------------------------------------------
# the renders
# --------------------------------------------------------------------------

#: What each faction's cyberspace is made of, in its own colours. These are
#: the faction's and not the palette's: a Kagawa terrace is pale green on
#: an amber terminal too, the way their sigil is their sigil.
FACTION_RGB: dict[str, dict[str, RGB]] = {
    'kagawa': {'sky': (8, 20, 14), 'near': (60, 160, 90), 'far': (170, 230, 190),
               'crop': (20, 70, 40)},
    'aoyama': {'wall': (246, 242, 236), 'vessel': (214, 96, 118),
               'deep': (160, 40, 70), 'glow': (255, 228, 220)},
    'sendai': {'void': (2, 2, 4), 'edge': (28, 28, 34), 'you': (120, 120, 130),
               'eye': (255, 255, 255)},
    'sixes': {'blue': (30, 48, 110), 'wire': (90, 130, 220),
              'missing': (220, 40, 200), 'tag': (240, 210, 60)},
    'carrion': {'dark': (36, 4, 6), 'wet': (150, 12, 24), 'drip': (90, 6, 14),
                'bone': (220, 200, 180)},
    'fixers': {'warm': (70, 42, 18), 'brass': (214, 168, 78),
               'lit': (255, 230, 150), 'cable': (40, 24, 10)},
    'nightwatch': {'grey': (22, 28, 36), 'line': (70, 90, 110),
                   'lamp': (220, 230, 240), 'beat': (140, 170, 200)},
    'freeport': {'sea': (18, 26, 34), 'rust': (150, 70, 30),
                 'ochre': (190, 140, 50), 'steel': (90, 110, 120),
                 'edge': (10, 12, 14)},
    'meridian': {'ink': (6, 6, 10), 'gold': (200, 160, 60),
                 'pale': (120, 100, 50), 'point': (255, 240, 180)},
    'chorus': {'dark': (14, 10, 18), 'beam': (120, 100, 140),
               'voice': (230, 210, 240), 'centre': (255, 255, 250)},
    'static': {'snow0': (30, 30, 30), 'snow1': (200, 200, 200),
               'band': (240, 240, 240), 'rec': (230, 40, 40)},
    'deepwater': {'surface': (10, 30, 50), 'deep': (0, 2, 8),
                  'band': (14, 40, 64), 'shape': (0, 6, 14)},
}


def render(faction: str, width: int = WIDTH, height: int = HEIGHT,
           seed: int = 0):
    """A picture of what this faction's cyberspace is made of."""
    fn = _RENDERS.get(faction)
    if fn is None:
        return []
    rng = random.Random(f'{faction}:{seed}')
    return fn(width, height, rng)


def _kagawa(w, h, rng):
    c = FACTION_RGB['kagawa']
    pix = _blank(w, h, c['sky'])
    shelves = 5
    for i in range(shelves):
        depth = i / max(1, shelves - 1)
        top = int(h * (0.28 + 0.16 * i))
        left = int(w * 0.06 * i)
        right = w - int(w * 0.03 * i)
        colour = lerp(c['near'], c['far'], 1 - depth)
        _rect(pix, left, top, right, h, colour)
        # The crop rows, on the flat of each shelf.
        for x in range(left + 2, right - 1, 3):
            _put(pix, x, top + 1, c['crop'])
    return pix


def _aoyama(w, h, rng):
    c = FACTION_RGB['aoyama']
    pix = _blank(w, h, c['wall'])
    for k in range(3):
        phase = rng.random() * math.pi * 2
        amp = h * (0.12 + 0.1 * k)
        mid = h * (0.35 + 0.2 * k)
        thick = 2 - (k == 2)
        for x in range(w):
            y = mid + amp * math.sin(x / w * math.pi * 2 + phase)
            for d in range(thick):
                _put(pix, x, int(y) + d, lerp(c['vessel'], c['deep'], k / 2))
    # The glow of a room kept warm.
    for y in range(h):
        for x in range(w):
            if pix[y][x] == c['wall'] and (x + y) % 7 == 0:
                pix[y][x] = c['glow']
    return pix


def _sendai(w, h, rng):
    c = FACTION_RGB['sendai']
    pix = _blank(w, h, c['void'])
    # A figure, at very high resolution, with no floor under it.
    cx = w // 2
    for y in range(int(h * 0.2), h):
        half = int(2 + 3 * math.sin((y - h * 0.2) / (h * 0.8) * math.pi))
        t = (y - h * 0.2) / (h * 0.8)
        for x in range(cx - half, cx + half + 1):
            _put(pix, x, y, lerp(c['edge'], c['you'], t * 0.6))
    _put(pix, cx, int(h * 0.12), c['eye'])
    return pix


def _sixes(w, h, rng):
    c = FACTION_RGB['sixes']
    pix = _blank(w, h, c['blue'])
    for x in range(0, w, 5):
        _line(pix, x, 0, x, h - 1, c['wire'])
    for y in range(0, h, 4):
        _line(pix, 0, y, w - 1, y, c['wire'])
    # The texture that never loaded.
    mx, my = int(w * 0.6), int(h * 0.3)
    for y in range(my, my + 6):
        for x in range(mx, mx + 10):
            _put(pix, x, y, c['missing'] if (x + y) % 2 else (0, 0, 0))
    # Somebody's tag, eight metres high.
    _line(pix, 3, h - 3, 14, h - 9, c['tag'])
    _line(pix, 14, h - 9, 20, h - 4, c['tag'])
    return pix


def _carrion(w, h, rng):
    c = FACTION_RGB['carrion']
    pix = _blank(w, h)
    for y in range(h):
        row = lerp(c['dark'], c['wet'], y / max(1, h - 1))
        for x in range(w):
            pix[y][x] = row
    for _ in range(7):
        x = rng.randrange(w)
        length = rng.randrange(h // 3, h)
        for y in range(length):
            _put(pix, x, y, c['drip'])
    # The hook, and the thing on it.
    hx = int(w * 0.72)
    _line(pix, hx, 0, hx, 4, c['bone'])
    _line(pix, hx, 4, hx - 3, 6, c['bone'])
    _rect(pix, hx - 2, 6, hx + 3, 12, c['drip'])
    return pix


def _fixers(w, h, rng):
    c = FACTION_RGB['fixers']
    pix = _blank(w, h, c['warm'])
    for y in range(2, h, 3):
        for x in range(1, w, 3):
            _put(pix, x, y, c['brass'])
            if rng.random() < 0.18:
                _put(pix, x, y, c['lit'])
    for _ in range(4):
        x0, x1 = rng.randrange(w), rng.randrange(w)
        _line(pix, x0, 2 + 3 * rng.randrange(h // 3), x1,
              2 + 3 * rng.randrange(h // 3), c['cable'])
    return pix


def _nightwatch(w, h, rng):
    c = FACTION_RGB['nightwatch']
    pix = _blank(w, h, c['grey'])
    for x in range(0, w, 8):
        _line(pix, x, 0, x, h - 1, c['line'])
    for y in range(0, h, 5):
        _line(pix, 0, y, w - 1, y, c['line'])
    lx = int(w * 0.3)
    for y in range(h):
        spread = int(y * 0.6)
        for x in range(lx - spread, lx + spread + 1):
            _put(pix, x, y, lerp(c['beat'], c['grey'], 0.15 + y / h * 0.6))
    for x in range(0, w, 8):
        for y in range(0, h, 5):
            if rng.random() < 0.35:
                _put(pix, x, y, c['lamp'])
    return pix


def _freeport(w, h, rng):
    c = FACTION_RGB['freeport']
    pix = _blank(w, h, c['sea'])
    colours = (c['rust'], c['ochre'], c['steel'])
    for row in range(4):
        y1 = h - row * 4
        y0 = y1 - 4
        offset = (row % 2) * 4
        x = -offset
        while x < w:
            width = 7 + rng.randrange(3)
            _rect(pix, x, y0, x + width, y1, rng.choice(colours))
            _line(pix, x, y0, x, y1 - 1, c['edge'])
            _line(pix, x, y0, x + width - 1, y0, c['edge'])
            x += width
    return pix


def _meridian(w, h, rng):
    c = FACTION_RGB['meridian']
    pix = _blank(w, h, c['ink'])
    for y in range(3, h, 3):
        _line(pix, 0, y, w - 1, y, c['pale'])
    for x in range(w):
        y = h - 2 - int((x / w) ** 2.2 * (h - 3))
        _put(pix, x, y, c['gold'])
        _put(pix, x, y + 1, shade(c['gold'], 0.5))
    _put(pix, w - 1, 1, c['point'])
    return pix


def _chorus(w, h, rng):
    c = FACTION_RGB['chorus']
    pix = _blank(w, h, c['dark'])
    cx, cy = w // 2, int(h * 0.55)
    for i in range(9):
        x0 = int(w * i / 8)
        y0 = 0 if i % 2 == 0 else h - 1
        _line(pix, x0, y0, cx, cy, lerp(c['beam'], c['voice'], (i % 3) / 2))
    _rect(pix, cx - 1, cy - 1, cx + 2, cy + 1, c['centre'])
    return pix


def _static(w, h, rng):
    c = FACTION_RGB['static']
    pix = _blank(w, h)
    for y in range(h):
        for x in range(w):
            pix[y][x] = lerp(c['snow0'], c['snow1'], rng.random() ** 2)
    for x in range(w):
        y = int(h * 0.7 - x * 0.35)
        for d in range(2):
            _put(pix, x, y + d, c['band'])
    _put(pix, w - 3, 1, c['rec'])
    return pix


def _deepwater(w, h, rng):
    c = FACTION_RGB['deepwater']
    pix = _blank(w, h)
    for y in range(h):
        row = lerp(c['surface'], c['deep'], (y / max(1, h - 1)) ** 0.7)
        for x in range(w):
            pix[y][x] = row
        if y % 3 == 1:
            for x in range(w):
                pix[y][x] = lerp(pix[y][x], c['band'], 0.5)
    cx, cy = w // 2, int(h * 0.8)
    rx, ry = int(w * 0.28), int(h * 0.22)
    for y in range(h):
        for x in range(w):
            if ((x - cx) / max(1, rx)) ** 2 + ((y - cy) / max(1, ry)) ** 2 <= 1:
                pix[y][x] = c['shape']
    return pix


_RENDERS = {
    'kagawa': _kagawa, 'aoyama': _aoyama, 'sendai': _sendai, 'sixes': _sixes,
    'carrion': _carrion, 'fixers': _fixers, 'nightwatch': _nightwatch,
    'freeport': _freeport, 'meridian': _meridian, 'chorus': _chorus,
    'static': _static, 'deepwater': _deepwater,
}

#: How a picture arrives (D102): rows of noise that settle top to bottom.
SETTLE_FRAMES = 10


def scrambled(pix, settled: float, rng: random.Random):
    """The picture with every row below the settle line replaced by noise
    in its own colours, for the reveal."""
    h = len(pix)
    line = int(h * settled)
    out = []
    for y, row in enumerate(pix):
        if y < line:
            out.append(list(row))
            continue
        palette = [p for p in row if p is not None] or [(0, 0, 0)]
        out.append([rng.choice(palette) if rng.random() < 0.7 else None
                    for _ in row])
    return out
