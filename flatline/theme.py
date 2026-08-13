"""Palettes and the colour half of the D16 capability ladder.

Every colour carries three rungs at once: a truecolour hex, a 256-colour index
derived from it, and a named ANSI-16 fallback. Rendering picks the rung the
terminal actually supports rather than assuming the best case.

Roles are semantic and several of them are game concepts rather than generic
severities. `trace` is always the same colour everywhere trace is mentioned,
which matters more than it sounds: in a game whose whole tension is one rising
number, that number needs to be findable in a wall of scrollback at a glance.

The default palette is lifted from the author's own doom-cyberpunk-neon theme,
which supplies its own sixteen-colour fallbacks; those are reused rather than
guessed, so the game sits inside the same visual world as the rest of this
machine instead of visiting it.
"""

from __future__ import annotations

from dataclasses import dataclass

ANSI16 = {
    'black': 30, 'red': 31, 'green': 32, 'yellow': 33,
    'blue': 34, 'magenta': 35, 'cyan': 36, 'white': 37,
    'brightblack': 90, 'brightred': 91, 'brightgreen': 92, 'brightyellow': 93,
    'brightblue': 94, 'brightmagenta': 95, 'brightcyan': 96, 'brightwhite': 97,
}


def _hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip('#')
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _to_256(h: str) -> int:
    """Nearest xterm-256 index for a hex colour.

    The 256 palette is sixteen fixed colours, a 6x6x6 RGB cube at 16-231, and
    24 greys at 232-255. Compare the best cube match against the best grey
    match and take whichever is closer. That second half matters for this
    palette specifically, whose backgrounds are near-grey blues the cube
    renders badly.
    """
    r, g, b = _hex_rgb(h)
    levels = (0, 95, 135, 175, 215, 255)

    def nearest(v: int) -> int:
        return min(range(6), key=lambda i: abs(levels[i] - v))

    ri, gi, bi = nearest(r), nearest(g), nearest(b)
    cube = 16 + 36 * ri + 6 * gi + bi
    cube_err = (levels[ri] - r) ** 2 + (levels[gi] - g) ** 2 + (levels[bi] - b) ** 2

    grey_v = round((r + g + b) / 3)
    gi2 = min(23, max(0, round((grey_v - 8) / 10)))
    grey_level = 8 + 10 * gi2
    grey_err = 3 * (grey_level - grey_v) ** 2

    return cube if cube_err <= grey_err else 232 + gi2


@dataclass(frozen=True, slots=True)
class Color:
    """One colour at all three rungs of the ladder."""

    hex: str
    ansi: str  # ANSI16 name used when only sixteen colours are available

    @property
    def rgb(self) -> tuple[int, int, int]:
        return _hex_rgb(self.hex)

    @property
    def c256(self) -> int:
        return _to_256(self.hex)


@dataclass(frozen=True, slots=True)
class Palette:
    """Semantic roles, never raw colours at the call site.

    Nothing outside this module asks for cyan. It asks for `accent`, or for
    `trace`, which is what lets `--theme ansi` remap the whole game onto
    somebody else's sixteen colours without touching a single line of output
    code.
    """

    name: str
    # Structure
    fg: Color
    dim: Color
    muted: Color
    border: Color
    # Severity
    ok: Color
    warn: Color
    err: Color
    info: Color
    # Emphasis
    accent: Color
    accent2: Color
    # Game concepts. These exist so that one idea is one colour everywhere.
    trace: Color      # the run clock, D5
    noise: Color      # local suspicion, D5
    residue: Color    # what you leave behind, D5
    ice: Color        # countermeasures
    credit: Color     # money
    heat: Color       # faction attention


#: The author's own palette, from doom-cyberpunk-neon.
CYBERPUNK_NEON = Palette(
    name='cyberpunk-neon',
    fg=Color('#dce7ff', 'white'),
    dim=Color('#5a6b94', 'brightblack'),
    muted=Color('#7d8cb0', 'brightblack'),
    border=Color('#24345c', 'brightblack'),
    ok=Color('#72f1b8', 'green'),
    warn=Color('#ffd479', 'yellow'),
    err=Color('#ff5f8f', 'red'),
    info=Color('#6cb6ff', 'brightblue'),
    accent=Color('#00f0ff', 'brightcyan'),
    accent2=Color('#ff5fd7', 'brightmagenta'),
    trace=Color('#ff5f8f', 'brightred'),
    noise=Color('#ffd479', 'yellow'),
    residue=Color('#c792ea', 'magenta'),
    ice=Color('#6cb6ff', 'brightblue'),
    credit=Color('#72f1b8', 'brightgreen'),
    heat=Color('#ff9f6c', 'brightyellow'),
)

#: Shipped for everyone who is not the author. Deliberately duller: it has to
#: sit on whatever background a stranger's terminal uses, so it leans on
#: contrast rather than on saturation.
NEUTRAL = Palette(
    name='neutral',
    fg=Color('#e6e6ec', 'brightwhite'),
    dim=Color('#6a6a78', 'brightblack'),
    muted=Color('#9a9aa8', 'white'),
    border=Color('#3a3a45', 'brightblack'),
    ok=Color('#87d787', 'green'),
    warn=Color('#d7c07f', 'yellow'),
    err=Color('#d78787', 'red'),
    info=Color('#87afd7', 'blue'),
    accent=Color('#5fd7d7', 'cyan'),
    accent2=Color('#d78fd7', 'magenta'),
    trace=Color('#d78787', 'brightred'),
    noise=Color('#d7c07f', 'yellow'),
    residue=Color('#af87d7', 'magenta'),
    ice=Color('#87afd7', 'blue'),
    credit=Color('#87d787', 'brightgreen'),
    heat=Color('#d7af87', 'brightyellow'),
)

#: `--theme ansi`: inherit whatever the user already likes. The hex values are
#: placeholders and are never consulted, because this palette is only ever
#: rendered at the sixteen-colour rung.
ANSI = Palette(
    name='ansi',
    fg=Color('#ffffff', 'brightwhite'),
    dim=Color('#808080', 'brightblack'),
    muted=Color('#c0c0c0', 'white'),
    border=Color('#808080', 'brightblack'),
    ok=Color('#00ff00', 'green'),
    warn=Color('#ffff00', 'yellow'),
    err=Color('#ff0000', 'red'),
    info=Color('#0000ff', 'brightblue'),
    accent=Color('#00ffff', 'brightcyan'),
    accent2=Color('#ff00ff', 'brightmagenta'),
    trace=Color('#ff0000', 'brightred'),
    noise=Color('#ffff00', 'yellow'),
    residue=Color('#ff00ff', 'magenta'),
    ice=Color('#0000ff', 'brightblue'),
    credit=Color('#00ff00', 'brightgreen'),
    heat=Color('#ffff00', 'brightyellow'),
)

PALETTES = {p.name: p for p in (CYBERPUNK_NEON, NEUTRAL, ANSI)}
DEFAULT = CYBERPUNK_NEON

#: Every role name, for `validate.py` to check that palettes stay in step and
#: for the `theme` command to demonstrate the whole set.
ROLES = tuple(f.name for f in Palette.__dataclass_fields__.values() if f.name != 'name')


def get(name: str | None) -> Palette:
    """Look up a palette by name, falling back to the default."""
    if not name:
        return DEFAULT
    return PALETTES.get(name, DEFAULT)
