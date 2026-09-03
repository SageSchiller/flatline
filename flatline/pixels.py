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


# --------------------------------------------------------------------------
# the player's icon (D105)
# --------------------------------------------------------------------------
#
# The fourth build axis (D18) is the shape you wear in cyberspace, and it was
# a line of prose. It is a small picture now: your mark, arriving in the net,
# drawn the same way the faction pictures are but smaller and centred so it
# reads as a figure rather than a scene. Nothing here matters (D35): it is
# drawn or it is not, and the coherence cost the icon carries is unchanged.

#: A player icon is smaller than a faction render: a figure, not a place.
ICON_WIDTH = 22
ICON_HEIGHT = 16

#: Each icon's own colours. Not the palette's: your mark is your mark, the
#: way a faction's sigil is theirs.
ICON_RGB: dict[str, dict[str, RGB]] = {
    'plain': {'body': (150, 152, 160)},
    'corporate': {'suit': (46, 56, 82), 'skin': (202, 172, 150),
                  'shirt': (210, 214, 224), 'tie': (210, 80, 80),
                  'case': (40, 44, 54)},
    'null': {'void': (8, 9, 13), 'edge': (60, 66, 84)},
    'swarm': {'a': (120, 200, 232), 'b': (60, 122, 200), 'c': (206, 234, 250)},
    'predator': {'fur': (66, 70, 82), 'eye': (248, 64, 64)},
    'mirror': {'you': (138, 154, 196), 'them': (204, 162, 182),
               'split': (240, 242, 250)},
    'deadname': {'ghost': (70, 60, 74), 'skin': (196, 170, 144),
                 'face': (216, 188, 164), 'strike': (230, 82, 82)},
    'process': {'dark': (40, 54, 50), 'body': (52, 66, 60),
                'screen': (118, 210, 160), 'joint': (90, 96, 104)},
    'janitor': {'overall': (70, 80, 96), 'skin': (192, 168, 150),
                'cap': (60, 68, 84), 'handle': (156, 120, 74),
                'bristle': (116, 126, 140)},
    'meter': {'plate': (120, 122, 130), 'body': (58, 60, 70),
              'face': (212, 214, 222), 'tick': (70, 72, 82),
              'needle': (234, 120, 88), 'pivot': (40, 42, 50)},
    'wraith': {'body': (76, 104, 140), 'rim': (150, 224, 255),
               'void': (10, 14, 22)},
    'ronin': {'armour': (40, 44, 58), 'helm': (30, 34, 46),
              'horn': (208, 70, 96), 'eye': (248, 72, 72),
              'blade': (234, 240, 248)},
    'seraph': {'body': (238, 240, 250), 'wing': (200, 214, 246),
               'halo': (255, 214, 120)},
    'reaper': {'cloak': (16, 16, 22), 'bone': (216, 212, 198),
               'socket': (12, 12, 18), 'glint': (238, 62, 62),
               'pole': (120, 90, 60), 'blade': (220, 224, 230)},
}

def render_icon(key: str, width: int = ICON_WIDTH, height: int = ICON_HEIGHT):
    """The picture of a player icon, or [] for one that has none."""
    fn = _ICON_RENDERS.get(key)
    if fn is None:
        return []
    rng = random.Random(f'icon:{key}')
    return fn(width, height, rng)


def _disc(pix, cx, cy, r, rgb) -> None:
    """A filled circle."""
    r2 = r * r + r * 0.5
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r2:
                _put(pix, x, y, rgb)


def _ring(pix, cx, cy, r, rgb, width: float = 1.0) -> None:
    """A circle outline `width` pixels thick."""
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if r - width <= d <= r + 0.35:
                _put(pix, x, y, rgb)


def _outline(pix, colour, edge) -> None:
    """A one-pixel rim in `edge` around every `colour` pixel bordering the
    background: a lit edge rather than a flat cut-out."""
    h, w = len(pix), len(pix[0])
    marks = []
    for y in range(h):
        for x in range(w):
            if pix[y][x] == colour:
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1),
                               (-1, -1), (1, -1), (-1, 1), (1, 1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= ny < h and 0 <= nx < w and pix[ny][nx] is None:
                        marks.append((nx, ny))
    for x, y in marks:
        _put(pix, x, y, edge)


def _biped(pix, cx, colour, top: int = 1, foot: int = 14, hr: int = 2):
    """A standing figure: head, torso, two arms, two legs. The base the human
    characters bend. Returns the neck and hip rows for hanging detail off."""
    _disc(pix, cx, top + hr, hr, colour)
    neck = top + 2 * hr + 1
    hip = neck + 4
    _rect(pix, cx - 2, neck, cx + 3, hip, colour)
    _line(pix, cx - 2, neck + 1, cx - 4, neck + 4, colour)
    _line(pix, cx + 2, neck + 1, cx + 4, neck + 4, colour)
    _rect(pix, cx - 2, hip, cx - 1, foot, colour)
    _rect(pix, cx + 1, hip, cx + 2, foot, colour)
    return neck, hip


# Player icons are a bestiary (D114): each is its own creature or character,
# read by silhouette. Plain is a person; the rest are what a runner chooses to
# be in the net instead of one.


def _icon_plain(w, h, rng):
    c = ICON_RGB['plain']
    pix = _blank(w, h)
    _biped(pix, w // 2, c['body'])
    return pix


def _icon_corporate(w, h, rng):
    c = ICON_RGB['corporate']
    pix = _blank(w, h)
    cx = w // 2
    neck, hip = _biped(pix, cx, c['suit'])
    _disc(pix, cx, 3, 2, c['skin'])                           # a face
    _rect(pix, cx - 1, neck, cx + 2, neck + 2, c['shirt'])    # a collar
    _put(pix, cx, neck + 1, c['tie'])                         # a tie
    _rect(pix, cx + 4, hip - 1, cx + 7, hip + 3, c['case'])   # a briefcase
    return pix


def _icon_null(w, h, rng):
    c = ICON_RGB['null']
    pix = _blank(w, h)
    _biped(pix, w // 2, c['void'])
    _outline(pix, c['void'], c['edge'])
    for y in range(h):                                        # a figure of holes
        for x in range(w):
            if pix[y][x] == c['void'] and rng.random() < 0.3:
                pix[y][x] = None
    return pix


def _icon_swarm(w, h, rng):
    c = ICON_RGB['swarm']
    pix = _blank(w, h)
    cx, cy = w / 2, h / 2
    cols = (c['a'], c['b'], c['c'])
    for _ in range(22):                                       # a cloud of bats
        ang = rng.random() * math.tau
        rad = rng.random() ** 0.6
        bx = int(cx + math.cos(ang) * rad * 8)
        by = int(cy + math.sin(ang) * rad * 5)
        col = rng.choice(cols)
        _put(pix, bx, by, col)
        _put(pix, bx - 1, by - 1, col)
        _put(pix, bx + 1, by - 1, col)
    return pix


def _icon_predator(w, h, rng):
    c = ICON_RGB['predator']
    pix = _blank(w, h)
    fur = c['fur']
    _rect(pix, 7, 7, 16, 11, fur)                             # a wolf, in profile
    _line(pix, 7, 7, 9, 5, fur)
    _line(pix, 16, 7, 14, 5, fur)                             # an arched back
    _rect(pix, 2, 6, 7, 10, fur)                              # the head
    _rect(pix, 0, 8, 3, 10, fur)                              # a snout
    _line(pix, 3, 6, 2, 3, fur); _put(pix, 2, 4, fur)         # ears
    _line(pix, 6, 6, 7, 3, fur); _put(pix, 7, 4, fur)
    for lx in (7, 9, 13, 15):                                 # four legs
        _rect(pix, lx, 11, lx + 1, 15, fur)
    _line(pix, 16, 8, 20, 5, fur)                             # a tail
    _line(pix, 16, 9, 20, 7, fur)
    _put(pix, 3, 7, c['eye'])                                 # an eye
    return pix


def _icon_mirror(w, h, rng):
    c = ICON_RGB['mirror']
    pix = _blank(w, h)
    _biped(pix, 6, c['you'])                                  # you
    _biped(pix, w - 7, c['them'])                             # and the reflection
    for y in range(h):
        _put(pix, w // 2, y, c['split'])                      # the seam
    return pix


def _icon_deadname(w, h, rng):
    c = ICON_RGB['deadname']
    pix = _blank(w, h)
    _biped(pix, 10, c['ghost'])                               # a ghost behind
    _biped(pix, 12, c['skin'])                                # the stranger worn
    _disc(pix, 12, 3, 2, c['face'])
    _line(pix, 6, 13, 17, 4, c['strike'])                     # struck through
    return pix


def _icon_process(w, h, rng):
    c = ICON_RGB['process']
    pix = _blank(w, h)
    _rect(pix, 7, 2, 15, 6, c['dark'])                        # a daemon, boxed
    _put(pix, 9, 4, c['screen']); _put(pix, 12, 4, c['screen'])   # eyes
    _line(pix, 11, 6, 11, 7, c['joint'])
    _rect(pix, 6, 7, 16, 12, c['body'])
    for x in range(7, 15, 2):                                 # a readout
        _put(pix, x, 9, c['screen'])
    _rect(pix, 7, 12, 9, 15, c['body']); _rect(pix, 13, 12, 15, 15, c['body'])
    _put(pix, 11, 0, c['screen']); _line(pix, 11, 0, 11, 2, c['joint'])  # antenna
    return pix


def _icon_janitor(w, h, rng):
    c = ICON_RGB['janitor']
    pix = _blank(w, h)
    _biped(pix, 8, c['overall'])
    _disc(pix, 8, 3, 2, c['skin'])                            # a face
    _rect(pix, 6, 1, 11, 3, c['cap'])                         # a cap
    _line(pix, 12, 4, 14, 15, c['handle'])                    # a broom
    _rect(pix, 12, 14, 16, 15, c['bristle'])
    return pix


def _icon_meter(w, h, rng):
    c = ICON_RGB['meter']
    pix = _blank(w, h)
    _rect(pix, 5, 3, 17, 13, c['body'])                       # a meter drone
    _outline(pix, c['body'], c['plate'])
    _disc(pix, 11, 8, 4, c['face'])                           # a big dial
    for a in range(210, 331, 30):
        _put(pix, 11 + int(math.cos(math.radians(a)) * 3),
             8 + int(math.sin(math.radians(a)) * 3), c['tick'])
    _line(pix, 11, 8, 13, 5, c['needle'])                     # a needle
    _put(pix, 11, 8, c['pivot'])
    _rect(pix, 6, 13, 8, 15, c['plate']); _rect(pix, 14, 13, 16, 15, c['plate'])
    _put(pix, 11, 1, c['needle']); _line(pix, 11, 1, 11, 3, c['plate'])
    return pix


def _icon_wraith(w, h, rng):
    c = ICON_RGB['wraith']
    pix = _blank(w, h)
    cx = w // 2
    for y in range(2, 13):                                    # a ghost
        half = min(5, 1 + (y - 2))
        for x in range(cx - half, cx + half + 1):
            if y >= 11 and (x - cx) % 3 == 1:                 # a wavy hem
                continue
            _put(pix, x, y, c['body'])
    _line(pix, 7, 7, 4, 10, c['body']); _line(pix, 15, 7, 18, 10, c['body'])  # arms
    _outline(pix, c['body'], c['rim'])
    _put(pix, cx - 2, 6, c['void']); _put(pix, cx + 2, 6, c['void'])          # eyes
    return pix


def _icon_ronin(w, h, rng):
    c = ICON_RGB['ronin']
    pix = _blank(w, h)
    cx = w // 2 - 2
    _biped(pix, cx, c['armour'])
    _line(pix, cx - 2, 1, cx - 3, -1, c['horn'])              # a horned kabuto
    _line(pix, cx + 2, 1, cx + 3, -1, c['horn'])
    _rect(pix, cx - 2, 0, cx + 3, 2, c['helm'])
    _put(pix, cx - 1, 3, c['eye']); _put(pix, cx + 1, 3, c['eye'])
    _line(pix, cx + 4, 13, w - 3, 2, c['blade'])              # a drawn katana
    return pix


def _icon_seraph(w, h, rng):
    c = ICON_RGB['seraph']
    pix = _blank(w, h)
    cx = w // 2
    for i in range(7):                                        # wings, spread
        _line(pix, cx - 4 - i, 9 - i, cx - 4 - i, 12, c['wing'])
        _line(pix, cx + 4 + i, 9 - i, cx + 4 + i, 12, c['wing'])
    _biped(pix, cx, c['body'])
    _ring(pix, cx, 1, 2, c['halo'], 1.0)                      # a halo
    return pix


def _icon_reaper(w, h, rng):
    c = ICON_RGB['reaper']
    pix = _blank(w, h)
    cx = w // 2
    for y in range(3, 15):                                    # a robe
        half = int(2 + (y - 3) * 0.4)
        for x in range(cx - half, cx + half + 1):
            _put(pix, x, y, c['cloak'])
    _disc(pix, cx, 5, 2, c['bone'])                           # a skull in the hood
    _put(pix, cx - 1, 5, c['socket']); _put(pix, cx + 1, 5, c['socket'])
    _put(pix, cx - 1, 5, c['glint'])                          # a glint
    _line(pix, cx - 7, 15, cx - 5, 1, c['pole'])              # a scythe
    _line(pix, cx - 5, 1, cx - 1, 3, c['blade'])
    return pix


_ICON_RENDERS = {
    'plain': _icon_plain, 'corporate': _icon_corporate, 'null': _icon_null,
    'swarm': _icon_swarm, 'predator': _icon_predator, 'mirror': _icon_mirror,
    'deadname': _icon_deadname, 'process': _icon_process,
    'janitor': _icon_janitor, 'meter': _icon_meter,
    'wraith': _icon_wraith, 'ronin': _icon_ronin, 'seraph': _icon_seraph,
    'reaper': _icon_reaper,
}


# --------------------------------------------------------------------------
# a portrait (D108)
# --------------------------------------------------------------------------
#
# Appearance is a build axis with 102 features (D33) and it was a sentence.
# This composes a head-and-shoulders bust from the ones that can be drawn:
# the build sets the shoulders, the dress the collar, the face the head, the
# eyes and hair and marks the rest. It is not a likeness of anybody; it is a
# reading of the feature keys, deterministic from them, so the same look
# always draws the same bust. Skin is a neutral tone chosen from the whole
# look's hash rather than from any one feature, because none of the features
# name it and the picture should not invent one. Nothing here matters (D35).

PORTRAIT_WIDTH = 28
PORTRAIT_HEIGHT = 34

_SKIN = ((222, 184, 152), (198, 160, 130), (170, 132, 104), (140, 106, 82),
         (110, 84, 66), (232, 204, 180), (186, 150, 128))
_HAIR_COL = {
    'cropped': (60, 52, 46), 'shaved': (70, 62, 56), 'long': (52, 44, 40),
    'bleached': (226, 214, 180), 'dyed': (200, 60, 140), 'greying': (150, 150, 156),
    'locked': (40, 34, 30), 'undercut': (50, 44, 40), 'thinning': (110, 104, 98),
    'braided': (60, 46, 38), 'wig': (90, 60, 120), 'unkempt': (66, 56, 48),
    'severe': (30, 28, 30), 'none': None,
}
_DRESS_COL = {
    'grey': (86, 90, 98), 'workwear': (74, 82, 96), 'corporate': (44, 52, 74),
    'armoured': (54, 58, 66), 'street': (96, 72, 60), 'clinical': (214, 218, 224),
    'expensive': (30, 32, 44), 'layered': (80, 68, 60), 'devotional': (72, 56, 92),
    'salvage': (92, 84, 66), 'immaculate': (236, 236, 240), 'nothing': None,
    'nightwatch': (36, 44, 58), 'bright': (210, 90, 70),
}
_EYE_COL = {
    'brown': (90, 60, 40), 'grey': (130, 138, 148), 'tired': (110, 90, 78),
    'mismatched': (90, 140, 200), 'optics': (60, 240, 255), 'blackout': (10, 10, 14),
    'pale': (170, 190, 200), 'shielded': (40, 46, 54), 'flickering': (120, 230, 200),
    'warm': (140, 90, 50), 'narrow': (80, 66, 54), 'reconstructed': (200, 210, 220),
}


def render_portrait(look: dict, width: int = PORTRAIT_WIDTH,
                    height: int = PORTRAIT_HEIGHT):
    """A head-and-shoulders bust composed from an appearance dict."""
    look = look or {}
    key = ':'.join(f'{k}={look.get(k, "")}' for k in sorted(look))
    rng = random.Random('portrait:' + key)
    pix = _blank(width, height)
    cx = width // 2
    skin = _SKIN[rng.randrange(len(_SKIN))]
    shadow = shade(skin, 0.78)

    # -- shoulders and collar, from build and dress --------------------
    build = look.get('build', 'unremarkable')
    span = {'slight': 0.30, 'wiry': 0.32, 'tall': 0.34, 'heavy': 0.46,
            'soft': 0.42, 'compact': 0.40, 'stooped': 0.34, 'rangy': 0.34,
            'gaunt': 0.30, 'blocky': 0.46, 'asymmetric': 0.40}.get(build, 0.38)
    dress = look.get('dress', 'grey')
    coat = _DRESS_COL.get(dress, (86, 90, 98))
    sh_top = int(height * 0.66)
    if coat is not None:
        for y in range(sh_top, height):
            t = (y - sh_top) / max(1, height - sh_top)
            half = int((0.22 + span * (0.5 + 0.5 * t)) * width)
            off = 1 if (build == 'asymmetric' and y % 2) else 0
            for x in range(cx - half, cx + half + 1):
                _put(pix, x + off, y, coat if (x + y) % 9 else shade(coat, 1.12))
        # a collar notch
        for y in range(sh_top, sh_top + 3):
            for x in range(cx - 2, cx + 3):
                _put(pix, x, y, shade(coat, 0.7))

    # -- head, from face ----------------------------------------------
    face = look.get('face', 'plain')
    hw = {'sharp': 6, 'broad': 8, 'young': 6, 'severe': 6, 'gaunt': 5,
          'still': 7}.get(face, 7)
    hh = int(height * 0.42)
    hcy = int(height * 0.30)
    for y in range(hcy - hh // 2, hcy + hh // 2 + 1):
        ny = (y - hcy) / (hh / 2)
        w_at = hw * (1 - 0.35 * ny * ny) ** 0.5 if abs(ny) <= 1 else 0
        w_at = int(round(w_at))
        for x in range(cx - w_at, cx + w_at + 1):
            _put(pix, x, y, skin)
        # a cheek shadow on the far side
        if w_at:
            _put(pix, cx + w_at, y, shadow)
            if face == 'lopsided':
                _put(pix, cx - w_at, y, shade(skin, 0.9))
    jaw = hcy + hh // 2
    # -- neck: from the jaw down to the collar, so the head is attached --
    for y in range(jaw - 1, sh_top + 1):
        for x in range(cx - 2, cx + 3):
            _put(pix, x, y, shadow if x in (cx - 2, cx + 2) else shade(skin, 0.9))
    # face-specific marks
    if face in ('scarred', 'worn'):
        for y in range(hcy - 2, hcy + 3):
            _put(pix, cx - hw + 2, y, shade(skin, 0.6))
    if face == 'burned':
        for y in range(hcy - 3, jaw):
            for x in range(cx + 1, cx + hw):
                if rng.random() < 0.4:
                    _put(pix, x, y, shade(skin, 0.7))

    # -- eyes, from eyes ----------------------------------------------
    eyes = look.get('eyes', 'tired')
    ec = _EYE_COL.get(eyes, (110, 90, 78))
    ey = hcy - 1
    for ex in (cx - hw // 2 - 1, cx + hw // 2):
        _put(pix, ex, ey, ec)
        if eyes in ('optics', 'flickering', 'reconstructed'):
            _put(pix, ex, ey, ec)
            _put(pix, ex - 1, ey, shade(ec, 0.6))
            _put(pix, ex + 1, ey, shade(ec, 0.6))
        elif eyes == 'blackout':
            _put(pix, ex - 1, ey, ec)
            _put(pix, ex, ey, ec)
    if eyes == 'mismatched':
        _put(pix, cx + hw // 2, ey, (200, 120, 60))
    # a brow line
    for x in range(cx - hw + 1, cx + hw):
        if (x - cx) % 2 == 0:
            _put(pix, x, ey - 2, shade(skin, 0.72))
    # nose and mouth, minimal
    _put(pix, cx, hcy + 1, shadow)
    for x in range(cx - 1, cx + 2):
        _put(pix, x, hcy + hh // 2 - 1,
             shade(skin, 0.62) if eyes != 'blackout' else shade(skin, 0.7))

    # -- hair, from hair ----------------------------------------------
    hair = look.get('hair', 'cropped')
    hc = _HAIR_COL.get(hair, (60, 52, 46))
    if hc is not None and hair not in ('shaved', 'none'):
        top = hcy - hh // 2
        length = {'long': int(height * 0.22), 'braided': int(height * 0.20),
                  'locked': int(height * 0.18), 'thinning': 1,
                  'undercut': 2, 'severe': 2}.get(hair, 3)
        for y in range(top - 2, top + 2):
            for x in range(cx - hw - 1, cx + hw + 2):
                if 0 <= y and abs(x - cx) <= hw + 1:
                    _put(pix, x, y, hc)
        for y in range(top, top + length):
            for x in (cx - hw - 1, cx + hw + 1):
                _put(pix, x, y, hc)
        if hair == 'bleached' or hair == 'dyed':
            _put(pix, cx - 1, top - 1, shade(hc, 1.2))
    if hair == 'shaved':
        for x in range(cx - hw, cx + hw + 1):
            _put(pix, x, hcy - hh // 2, shade(skin, 0.85))

    # -- marks, from marks --------------------------------------------
    marks = look.get('marks', 'ports')
    if marks == 'ports':
        _put(pix, cx - hw, hcy - 1, (120, 200, 220))
        _put(pix, cx - hw, hcy, (90, 160, 190))
    elif marks in ('ink', 'gang', 'religious', 'tally'):
        col = {'ink': (40, 60, 120), 'gang': (180, 40, 60),
               'religious': (200, 180, 90), 'tally': (60, 60, 66)}[marks]
        for y in range(hcy, jaw - 1):
            _put(pix, cx - hw + 1, y, col)
    elif marks in ('subdermal', 'corporate', 'clinic', 'surgical'):
        col = (150, 160, 172)
        for x in range(cx + 1, cx + hw):
            _put(pix, x, hcy - hh // 2 + 1, col)
    elif marks in ('burns', 'brand'):
        for y in range(hcy, jaw):
            if rng.random() < 0.5:
                _put(pix, cx + hw - 1, y, shade(skin, 0.6))
    return pix


# --------------------------------------------------------------------------
# ICE, when it wakes (D110)
# --------------------------------------------------------------------------
#
# A construct winding up to act is the tensest beat in a run, and it was a
# line of text. This draws the thing: a small picture per behaviour, in its
# own menace, shown at the tell where the terminal can. Seven behaviours,
# one shape each, so a player learns to read a Hunter from a Warden at a
# glance the way they already learn a faction's cyberspace. Nothing here
# matters (D35): the tell, the strike and the odds are unchanged.

ICE_WIDTH = 20
ICE_HEIGHT = 16

ICE_RGB: dict[str, dict[str, RGB]] = {
    'sentry': {'dark': (20, 30, 46), 'ring': (90, 150, 210),
               'iris': (120, 200, 240), 'pupil': (10, 14, 22)},
    'probe': {'dark': (18, 34, 30), 'ping': (90, 220, 180),
              'core': (200, 250, 230)},
    'hunter': {'dark': (34, 14, 16), 'lock': (240, 70, 60),
               'edge': (150, 30, 34), 'core': (255, 150, 120)},
    'trap': {'dark': (30, 26, 16), 'web': (200, 180, 90),
             'bait': (240, 220, 120)},
    'warden': {'dark': (26, 28, 36), 'bar': (150, 160, 176),
               'lock': (210, 216, 226)},
    'herder': {'dark': (28, 20, 34), 'arm': (170, 130, 200),
               'core': (220, 200, 240)},
    'black': {'dark': (8, 8, 10), 'bone': (220, 220, 226),
              'shadow': (40, 40, 46), 'eye': (255, 60, 60)},
}


def render_ice(behaviour: str, width: int = ICE_WIDTH, height: int = ICE_HEIGHT,
               seed: int = 0):
    """A picture of a construct of this behaviour, or [] for an unknown one."""
    fn = _ICE_RENDERS.get(behaviour)
    if fn is None:
        return []
    return fn(width, height, random.Random(f'ice:{behaviour}:{seed}'))


def _ice_sentry(w, h, rng):
    c = ICE_RGB['sentry']
    pix = _blank(w, h, c['dark'])
    cx, cy = w // 2, h // 2
    # an eye: an almond of rings around an iris
    for y in range(h):
        for x in range(w):
            ex = (x - cx) / (w * 0.42)
            ey = (y - cy) / (h * 0.34)
            r = ex * ex + ey * ey
            if r <= 1:
                pix[y][x] = c['ring'] if r > 0.55 else c['iris']
    for y in range(cy - 2, cy + 2):
        for x in range(cx - 2, cx + 2):
            if (x - cx) ** 2 + (y - cy) ** 2 <= 3:
                _put(pix, x, y, c['pupil'])
    return pix


def _ice_probe(w, h, rng):
    c = ICE_RGB['probe']
    pix = _blank(w, h, c['dark'])
    cx, cy = w // 2, h // 2
    # concentric pings, a sensor sweeping
    for rad in (3, 5, 7):
        for a in range(0, 360, 12):
            x = int(cx + math.cos(math.radians(a)) * rad)
            y = int(cy + math.sin(math.radians(a)) * rad * 0.8)
            _put(pix, x, y, c['ping'])
    _rect(pix, cx - 1, cy - 1, cx + 2, cy + 2, c['core'])
    return pix


def _ice_hunter(w, h, rng):
    c = ICE_RGB['hunter']
    pix = _blank(w, h, c['dark'])
    cx, cy = w // 2, h // 2
    # a reticle locked on: crosshair, corners, a hot centre
    for x in range(2, w - 2):
        _put(pix, x, cy, c['edge'])
    for y in range(2, h - 2):
        _put(pix, cx, y, c['edge'])
    for dx in (-1, 1):
        for dy in (-1, 1):
            ox, oy = cx + dx * (w // 2 - 3), cy + dy * (h // 2 - 2)
            for k in range(3):
                _put(pix, ox, oy + dy * k, c['lock'])
                _put(pix, ox + dx * k, oy, c['lock'])
    for y in range(cy - 1, cy + 2):
        for x in range(cx - 1, cx + 2):
            _put(pix, x, y, c['core'])
    return pix


def _ice_trap(w, h, rng):
    c = ICE_RGB['trap']
    pix = _blank(w, h, c['dark'])
    cx, cy = w // 2, h // 2
    # a web: radial threads and two rings
    for a in range(0, 360, 30):
        for r in range(2, min(w, h) // 2):
            x = int(cx + math.cos(math.radians(a)) * r)
            y = int(cy + math.sin(math.radians(a)) * r * 0.8)
            _put(pix, x, y, c['web'])
    for rad in (3, 6):
        for a in range(0, 360, 10):
            x = int(cx + math.cos(math.radians(a)) * rad)
            y = int(cy + math.sin(math.radians(a)) * rad * 0.8)
            _put(pix, x, y, c['web'])
    _put(pix, cx, cy, c['bait'])
    return pix


def _ice_warden(w, h, rng):
    c = ICE_RGB['warden']
    pix = _blank(w, h, c['dark'])
    # a portcullis: uprights and crossbars, a lock in the middle
    for x in range(3, w - 2, 3):
        for y in range(2, h - 2):
            _put(pix, x, y, c['bar'])
    for y in range(3, h - 2, 4):
        for x in range(3, w - 2):
            _put(pix, x, y, c['bar'])
    cx, cy = w // 2, h // 2
    for y in range(cy - 1, cy + 3):
        for x in range(cx - 2, cx + 2):
            _put(pix, x, y, c['lock'])
    _put(pix, cx - 1, cy, c['dark'])
    return pix


def _ice_herder(w, h, rng):
    c = ICE_RGB['herder']
    pix = _blank(w, h, c['dark'])
    cx, cy = w // 2, h // 2
    # arrows converging: routes being cut and funnelled
    for sy in (2, h - 3):
        for x in range(2, cx):
            y = int(sy + (cy - sy) * (x - 2) / (cx - 2))
            _put(pix, x, y, c['arm'])
            _put(pix, w - 1 - x, y, c['arm'])
    _rect(pix, cx - 2, cy - 1, cx + 3, cy + 2, c['core'])
    return pix


def _ice_black(w, h, rng):
    c = ICE_RGB['black']
    pix = _blank(w, h, c['dark'])
    cx, cy = w // 2, h // 2
    # a skull: a pale dome, two black sockets, a hot glint in one
    for y in range(2, h - 2):
        for x in range(w):
            ex = (x - cx) / (w * 0.34)
            ey = (y - (cy - 1)) / (h * 0.4)
            if ex * ex + ey * ey <= 1:
                pix[y][x] = c['bone']
    # jaw
    for x in range(cx - 3, cx + 4):
        _put(pix, x, h - 3, c['bone'])
        _put(pix, x, h - 2, c['bone'] if x % 2 else c['dark'])
    # sockets
    for ox in (cx - 3, cx + 2):
        for y in range(cy - 1, cy + 2):
            for x in range(ox, ox + 2):
                _put(pix, x, y, c['shadow'])
    _put(pix, cx - 3, cy, c['eye'])
    _put(pix, cx - 2, cy, c['eye'])
    return pix


_ICE_RENDERS = {
    'sentry': _ice_sentry, 'probe': _ice_probe, 'hunter': _ice_hunter,
    'trap': _ice_trap, 'warden': _ice_warden, 'herder': _ice_herder,
    'black': _ice_black,
}
