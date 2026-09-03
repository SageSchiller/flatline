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
    'plain': {'body': (150, 152, 160), 'edge': (92, 94, 102)},
    'corporate': {'suit': (52, 60, 82), 'skin': (202, 172, 150),
                  'badge': (232, 210, 92), 'shirt': (212, 216, 226)},
    'null': {'edge': (44, 50, 66), 'hole': (7, 8, 12)},
    'swarm': {'a': (120, 200, 232), 'b': (68, 130, 202), 'c': (204, 232, 250)},
    'predator': {'dark': (18, 20, 28), 'edge': (128, 30, 42),
                 'eye': (244, 64, 64)},
    'mirror': {'you': (146, 158, 190), 'them': (196, 160, 176),
               'split': (232, 236, 246)},
    'deadname': {'skin': (216, 188, 164), 'hair': (58, 42, 34),
                 'coat': (114, 92, 126), 'warm': (250, 226, 202)},
    'process': {'box': (34, 54, 46), 'text': (118, 210, 160),
                'done': (92, 232, 152), 'todo': (28, 46, 40)},
    'janitor': {'overall': (70, 80, 96), 'skin': (192, 168, 150),
                'cart': (112, 118, 130), 'low': (52, 58, 70)},
    'meter': {'grey': (120, 122, 130), 'dark': (68, 70, 78),
              'num': (212, 214, 222)},
    'wraith': {'body': (70, 96, 128), 'rim': (150, 224, 255)},
    'ronin': {'armour': (34, 38, 52), 'edge': (120, 150, 210),
              'blade': (224, 236, 248), 'eye': (248, 72, 72),
              'crest': (208, 70, 96)},
    'seraph': {'body': (238, 240, 250), 'glow': (255, 246, 210),
               'wing': (198, 210, 244), 'halo': (255, 214, 120)},
    'reaper': {'cloak': (16, 16, 22), 'trim': (78, 40, 96),
               'skull': (214, 210, 196), 'socket': (8, 8, 12),
               'glint': (236, 60, 60)},
}


def render_icon(key: str, width: int = ICON_WIDTH, height: int = ICON_HEIGHT):
    """The picture of a player icon, or [] for one that has none."""
    fn = _ICON_RENDERS.get(key)
    if fn is None:
        return []
    rng = random.Random(f'icon:{key}')
    return fn(width, height, rng)


def _head(w: int, h: int):
    """Where the head sits. Shared, so anything drawn on the face (skin, a
    hood, a halo) lands where the silhouette actually put the head."""
    hr = max(2, h // 6)
    return w // 2, 1 + hr, hr


def _outline(pix, colour, edge) -> None:
    """A one-pixel rim in `edge` around every `colour` pixel that borders the
    background. What reads as a lit edge rather than a flat cut-out."""
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


def _figure(pix, colour, edge=None):
    """A head-and-shoulders bust centred in the frame: a round head, a real
    neck, shoulders that are the widest point, and a chest that holds its
    width rather than flaring to a cone. The base every human icon bends.

    The old figure was a circle on a triangle and read as a traffic cone. A
    person is read at the shoulders, so the shoulders are drawn first and the
    body hangs off them."""
    h, w = len(pix), len(pix[0])
    cx, hcy, hr = _head(w, h)
    for y in range(hcy - hr, hcy + hr + 1):                     # the head
        for x in range(cx - hr, cx + hr + 1):
            if (x - cx) ** 2 + (y - hcy) ** 2 <= hr * hr + 1:
                _put(pix, x, y, colour)
    neck_top = hcy + hr
    neck_w = max(1, hr - 1)
    shoulder_top = neck_top + max(2, h // 8)
    shoulder_w = int(w * 0.34)
    chest_w = int(w * 0.29)
    ramp = max(2, h // 6)
    for y in range(neck_top, h):
        if y < shoulder_top:                                    # the neck
            half = neck_w
        elif y < shoulder_top + ramp:                           # the shoulders
            t = (y - shoulder_top) / ramp
            half = round(neck_w + (shoulder_w - neck_w) * (t ** 0.55))
        else:                                                   # the chest
            t = (y - shoulder_top - ramp) / max(1, h - (shoulder_top + ramp))
            half = round(shoulder_w - (shoulder_w - chest_w) * t)
        for x in range(cx - half, cx + half + 1):
            _put(pix, x, y, colour)
    if edge is not None:
        _outline(pix, colour, edge)


def _icon_plain(w, h, rng):
    c = ICON_RGB['plain']
    pix = _blank(w, h)
    _figure(pix, c['body'], edge=c['edge'])
    return pix


def _icon_corporate(w, h, rng):
    c = ICON_RGB['corporate']
    pix = _blank(w, h)
    _figure(pix, c['suit'])
    cx, hcy, hr = _head(w, h)
    for y in range(hcy - hr + 1, hcy + hr):                     # the face
        for x in range(cx - hr + 1, cx + hr):
            if (x - cx) ** 2 + (y - hcy) ** 2 <= hr * hr:
                _put(pix, x, y, c['skin'])
    collar = hcy + hr + 1
    for y in range(collar, min(h, collar + 3)):                 # a shirt V
        d = y - collar
        for x in range(cx - 1 - d, cx + 2 + d):
            _put(pix, x, y, c['shirt'])
    _put(pix, cx + int(w * 0.16), collar + 2, c['badge'])       # the badge
    _put(pix, cx + int(w * 0.16), collar + 3, c['badge'])
    return pix


def _icon_null(w, h, rng):
    c = ICON_RGB['null']
    pix = _blank(w, h)
    _figure(pix, c['hole'], edge=c['edge'])
    for y in range(h):
        for x in range(w):
            if pix[y][x] == c['hole'] and rng.random() < 0.86:
                pix[y][x] = None
    return pix


def _icon_swarm(w, h, rng):
    c = ICON_RGB['swarm']
    pix = _blank(w, h)
    cx, cy = w / 2, h / 2
    cols = (c['a'], c['b'], c['c'])
    for _ in range(95):
        ang = rng.random() * math.tau
        rad = rng.random() ** 0.5
        _put(pix, int(cx + math.cos(ang) * rad * w * 0.42),
             int(cy + math.sin(ang) * rad * h * 0.46), rng.choice(cols))
    return pix


def _icon_predator(w, h, rng):
    c = ICON_RGB['predator']
    pix = _blank(w, h)
    for i in range(w):
        t = i / w
        y = int(h * 0.2 + t * h * 0.6)
        thick = int(1 + (1 - abs(t - 0.5) * 2) * h * 0.30)
        for d in range(-thick, thick + 1):
            _put(pix, i, y + d, c['dark'] if abs(d) < thick else c['edge'])
    for i in range(int(w * 0.5), w, 2):
        y = int(h * 0.2 + (i / w) * h * 0.6)
        _put(pix, i, y + 3, c['edge'])
    _put(pix, int(w * 0.78), int(h * 0.5), c['eye'])
    return pix


def _icon_mirror(w, h, rng):
    c = ICON_RGB['mirror']
    pix = _blank(w, h)
    cx = w // 2
    _figure(pix, c['you'])
    for y in range(h):
        for x in range(cx, w):
            if pix[y][x] == c['you']:
                _put(pix, min(w - 1, x + 1), y, c['them'])
    for y in range(h):
        _put(pix, cx, y, c['split'])
    return pix


def _icon_deadname(w, h, rng):
    c = ICON_RGB['deadname']
    pix = _blank(w, h)
    _figure(pix, c['coat'])
    cx, hcy, hr = _head(w, h)
    for y in range(hcy - hr, hcy + hr + 1):                     # the face
        for x in range(cx - hr, cx + hr + 1):
            if (x - cx) ** 2 + (y - hcy) ** 2 <= hr * hr + 1:
                _put(pix, x, y, c['skin'])
    for x in range(cx - hr, cx + hr + 1):                       # swept hair
        _put(pix, x, hcy - hr, c['hair'])
        _put(pix, x, hcy - hr + 1, c['hair'] if x < cx else pix[hcy - hr + 1][x])
    _put(pix, cx - hr - 1, hcy, c['warm'])                      # an earring
    return pix


def _icon_process(w, h, rng):
    c = ICON_RGB['process']
    pix = _blank(w, h)
    _rect(pix, 2, 3, w - 2, h - 3, c['box'])
    for x in range(3, w - 3):
        _put(pix, x, 5, c['text'] if x % 2 else c['box'])
    for x in range(3, w - 3):
        done = x < 3 + int((w - 6) * 0.62)
        _put(pix, x, h - 6, c['done'] if done else c['todo'])
    _put(pix, w - 4, 4, c['done'])
    return pix


def _icon_janitor(w, h, rng):
    c = ICON_RGB['janitor']
    pix = _blank(w, h)
    cx = int(w * 0.4)
    _rect(pix, cx - 2, 2, cx + 2, 4, c['skin'])
    _rect(pix, cx - 3, 4, cx + 3, h - 2, c['overall'])
    _rect(pix, cx + 4, h - 6, w - 2, h - 2, c['cart'])
    _rect(pix, cx + 4, h - 7, w - 3, h - 6, c['low'])
    return pix


def _icon_meter(w, h, rng):
    c = ICON_RGB['meter']
    pix = _blank(w, h)
    _rect(pix, 3, 4, w - 3, h - 4, c['grey'])
    _rect(pix, 3, 4, w - 3, 6, c['dark'])
    for x in range(5, w - 5, 4):
        _put(pix, x, 8, c['num'])
        _put(pix, x, 9, c['num'])
        _put(pix, x + 1, 9, c['num'])
        _put(pix, x, 10, c['num'])
    return pix


def _icon_wraith(w, h, rng):
    c = ICON_RGB['wraith']
    pix = _blank(w, h)
    _figure(pix, c['body'])
    _outline(pix, c['body'], c['rim'])                          # a lit edge
    for y in range(h):                                          # then a haze
        for x in range(w):
            if pix[y][x] == c['body'] and rng.random() < 0.55:
                pix[y][x] = None
    return pix


def _icon_ronin(w, h, rng):
    c = ICON_RGB['ronin']
    pix = _blank(w, h)
    _figure(pix, c['armour'], edge=c['edge'])
    cx, hcy, hr = _head(w, h)
    _line(pix, cx - hr, hcy - hr, cx - hr - 2, hcy - hr - 3, c['crest'])
    _line(pix, cx + hr, hcy - hr, cx + hr + 2, hcy - hr - 3, c['crest'])
    _put(pix, cx - 1, hcy, c['eye'])                            # a visor glare
    _put(pix, cx + 1, hcy, c['eye'])
    _line(pix, cx + 2, h - 2, w - 2, 1, c['blade'])             # a drawn katana
    _put(pix, cx + 1, h - 2, c['crest'])                        # the tsuba
    return pix


def _icon_seraph(w, h, rng):
    c = ICON_RGB['seraph']
    pix = _blank(w, h)
    cx, hcy, hr = _head(w, h)
    sy = hcy + hr                                               # wings root here
    span = int(w * 0.40)
    for i in range(span):                                       # broad feathers
        t = i / max(1, span - 1)
        length = int((1 - t) * h * 0.42) + 1
        y0 = sy - int(t * h * 0.10)
        for dy in range(length):
            col = c['wing'] if dy < length - 1 else shade(c['wing'], 0.7)
            _put(pix, cx - hr - 2 - i, y0 - dy, col)
            _put(pix, cx + hr + 2 + i, y0 - dy, col)
    for a in range(0, 360, 12):                                 # a nimbus, behind
        x = cx + int(round(math.cos(math.radians(a)) * (hr + 2)))
        y = hcy + int(round(math.sin(math.radians(a)) * (hr + 1)))
        _put(pix, x, y, c['halo'])
    _figure(pix, c['body'], edge=c['glow'])
    return pix


def _icon_reaper(w, h, rng):
    c = ICON_RGB['reaper']
    pix = _blank(w, h)
    cx, top = w // 2, 1
    for y in range(top, h):                                     # a robe
        t = (y - top) / max(1, h - 1 - top)
        half = int(2 + t * (w * 0.36))
        for x in range(cx - half, cx + half + 1):
            _put(pix, x, y, c['cloak'])
            if x in (cx - half, cx + half):
                _put(pix, x, y, c['trim'])                      # a lit hem
    fy = 3                                                      # the hood's skull
    for y in range(fy, fy + 5):
        for x in range(cx - 2, cx + 3):
            if (x - cx) ** 2 + ((y - (fy + 2)) * 1.3) ** 2 <= 6:
                _put(pix, x, y, c['skull'])
    for dx in (-1, 1):                                          # eye sockets
        _put(pix, cx + dx, fy + 1, c['socket'])
        _put(pix, cx + dx, fy + 2, c['socket'])
    _put(pix, cx - 1, fy + 2, c['glint'])                       # a glint in one
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
