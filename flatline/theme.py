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
    # Distance from the actual colour to that grey, not from its average to
    # the grey ramp. Measuring the average was the original and it was very
    # wrong: it asks "is this colour's brightness close to a grey", which is
    # true of every saturated colour, so pure cyan scored a near-perfect grey
    # match and lost to nothing. The entire game rendered in greyscale on any
    # 256-colour terminal, which is most terminals over ssh.
    grey_err = ((grey_level - r) ** 2 + (grey_level - g) ** 2
                + (grey_level - b) ** 2)

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
    heat=Color('#e09a5f', 'brightyellow'),
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


# --------------------------------------------------------------------------
# unlockable palettes
# --------------------------------------------------------------------------
#
# Everything below here is earned rather than shipped, and the catalogue in
# `content/rice.py` decides how. They exist because the deck's interface is
# the one thing in this game the city cannot take off you, and because a
# reward that costs the designer nothing to give and the player nothing to
# carry is the cheapest good feeling in games.
#
# Two rules held all of them:
#
# **Every role has to stay distinguishable.** A palette where `trace` and
# `dim` read the same is not a mood, it is a bug, and `validate.py` measures
# it rather than trusting the author's eye.
#
# **The monochromes differentiate by brightness, not by hue**, which is what
# an actual phosphor tube did. It is also why they are the most legible
# palettes here despite having one colour in them.

#: Amber CRT. One phosphor, eleven brightnesses, and the specific warmth of a
#: tube that has been on since before you were born.
AMBER = Palette(
    name='amber',
    fg=Color('#ffb642', 'brightyellow'),
    dim=Color('#5c3f14', 'brightblack'),
    muted=Color('#8f6a24', 'yellow'),
    border=Color('#3d2a0d', 'brightblack'),
    ok=Color('#ffd98a', 'brightyellow'),
    warn=Color('#ffc75e', 'yellow'),
    err=Color('#fff2d0', 'brightwhite'),
    info=Color('#c68f33', 'yellow'),
    accent=Color('#ffe9b8', 'brightwhite'),
    accent2=Color('#e0951f', 'brightyellow'),
    trace=Color('#fff2d0', 'brightwhite'),
    noise=Color('#ffc75e', 'yellow'),
    residue=Color('#a97a28', 'yellow'),
    ice=Color('#c68f33', 'yellow'),
    credit=Color('#ffd98a', 'brightyellow'),
    heat=Color('#ffa726', 'brightyellow'),
)

#: Green phosphor. The other tube. Colder, harsher, and what most people
#: picture when they picture this.
PHOSPHOR = Palette(
    name='phosphor',
    fg=Color('#3bff6a', 'brightgreen'),
    dim=Color('#0f4a20', 'brightblack'),
    muted=Color('#1f8a3c', 'green'),
    border=Color('#0a3316', 'brightblack'),
    ok=Color('#9fffb8', 'brightgreen'),
    warn=Color('#c9ff8a', 'brightgreen'),
    err=Color('#e8ffe8', 'brightwhite'),
    info=Color('#2fc257', 'green'),
    accent=Color('#d4ffd4', 'brightwhite'),
    accent2=Color('#5cff8f', 'brightgreen'),
    trace=Color('#e8ffe8', 'brightwhite'),
    noise=Color('#c9ff8a', 'brightgreen'),
    residue=Color('#32a050', 'green'),
    ice=Color('#2fc257', 'green'),
    credit=Color('#9fffb8', 'brightgreen'),
    heat=Color('#8fff5c', 'brightgreen'),
)

#: Kagawa house style. Cold, correct, and entirely without opinions. Wearing
#: the interface of the people whose network you are inside is a specific
#: kind of joke and it is available to anybody they trust.
KAGAWA = Palette(
    name='kagawa',
    fg=Color('#e8eef5', 'brightwhite'),
    dim=Color('#5a6a7a', 'brightblack'),
    muted=Color('#8d9dad', 'white'),
    border=Color('#2b3742', 'brightblack'),
    ok=Color('#7fd4c1', 'cyan'),
    warn=Color('#e2c48a', 'yellow'),
    err=Color('#e08b8b', 'red'),
    info=Color('#8fb4d9', 'blue'),
    accent=Color('#5fc4d9', 'brightcyan'),
    accent2=Color('#a8c4dd', 'brightblue'),
    trace=Color('#e08b8b', 'brightred'),
    noise=Color('#e2c48a', 'yellow'),
    residue=Color('#a89dc4', 'magenta'),
    ice=Color('#8fb4d9', 'blue'),
    credit=Color('#7fd4c1', 'brightcyan'),
    heat=Color('#dda87f', 'brightyellow'),
)

#: Carrion. Wet reds and the colour of bone, and no attempt at comfort.
CARRION = Palette(
    name='carrion',
    fg=Color('#e8ddd4', 'white'),
    dim=Color('#6b3a3a', 'brightblack'),
    muted=Color('#a87878', 'red'),
    border=Color('#42201f', 'brightblack'),
    ok=Color('#c4b48a', 'yellow'),
    warn=Color('#e09f5f', 'brightyellow'),
    err=Color('#ff4f4f', 'brightred'),
    info=Color('#c48f8f', 'red'),
    accent=Color('#e05252', 'brightred'),
    accent2=Color('#f0d0b0', 'brightwhite'),
    trace=Color('#ff4f4f', 'brightred'),
    noise=Color('#e09f5f', 'brightyellow'),
    residue=Color('#96538f', 'magenta'),
    ice=Color('#c48f8f', 'red'),
    credit=Color('#c4b48a', 'yellow'),
    heat=Color('#ff7a4f', 'brightred'),
)

#: Deepwater. Nobody has established what Deepwater is, and this is what the
#: inside of not knowing looks like.
DEEPWATER = Palette(
    name='deepwater',
    fg=Color('#bfe4e8', 'brightcyan'),
    dim=Color('#1d4650', 'brightblack'),
    muted=Color('#4d818c', 'cyan'),
    border=Color('#122d35', 'brightblack'),
    ok=Color('#6fd8c0', 'brightcyan'),
    warn=Color('#8fc4d0', 'cyan'),
    err=Color('#d97fa8', 'brightmagenta'),
    info=Color('#5fa8c4', 'blue'),
    accent=Color('#3fe0d4', 'brightcyan'),
    accent2=Color('#8f7fd9', 'brightmagenta'),
    trace=Color('#d97fa8', 'brightmagenta'),
    noise=Color('#8fc4d0', 'cyan'),
    residue=Color('#7060b0', 'magenta'),
    ice=Color('#5fa8c4', 'blue'),
    credit=Color('#6fd8c0', 'brightcyan'),
    heat=Color('#d9a87f', 'brightyellow'),
)

#: Static. Pirate broadcast, run by people who publish rather than sell, and
#: the harshest thing in this list by a distance.
STATIC = Palette(
    name='static',
    fg=Color('#f0f0f0', 'brightwhite'),
    dim=Color('#5a4a5a', 'brightblack'),
    muted=Color('#9a8a9a', 'white'),
    border=Color('#3a2a3a', 'brightblack'),
    ok=Color('#8fff8f', 'brightgreen'),
    warn=Color('#ffff5f', 'brightyellow'),
    err=Color('#ff2f8f', 'brightred'),
    info=Color('#5fdfff', 'brightcyan'),
    accent=Color('#ff2fdf', 'brightmagenta'),
    accent2=Color('#ffffff', 'brightwhite'),
    trace=Color('#ff2f8f', 'brightred'),
    noise=Color('#ffff5f', 'brightyellow'),
    residue=Color('#cf5fff', 'magenta'),
    ice=Color('#5fdfff', 'brightcyan'),
    credit=Color('#8fff8f', 'brightgreen'),
    heat=Color('#ff8f2f', 'brightyellow'),
)

#: Ash. Almost no colour at all, and one thin red line for the only number
#: that ever really mattered. Unlocked by losing somebody.
ASH = Palette(
    name='ash',
    fg=Color('#d0d0d0', 'brightwhite'),
    dim=Color('#4a4a4a', 'brightblack'),
    muted=Color('#8a8a8a', 'white'),
    border=Color('#333333', 'brightblack'),
    ok=Color('#b4bcb4', 'white'),
    warn=Color('#ccc4a8', 'brightwhite'),
    err=Color('#c45f5f', 'red'),
    info=Color('#98a4ac', 'white'),
    accent=Color('#ececec', 'brightwhite'),
    accent2=Color('#74748e', 'brightblack'),
    trace=Color('#c45f5f', 'brightred'),
    noise=Color('#ccc4a8', 'brightwhite'),
    residue=Color('#6a6470', 'brightblack'),
    ice=Color('#98a4ac', 'white'),
    credit=Color('#b4bcb4', 'white'),
    heat=Color('#b07a6a', 'red'),
)

#: Paper. A light theme, for the one person who runs a light terminal, and
#: genuinely useful in daylight. It is the only palette here that assumes
#: anything about the background it lands on, which is why it says so.
PAPER = Palette(
    name='paper',
    fg=Color('#1c1c22', 'black'),
    dim=Color('#8a8a92', 'brightblack'),
    muted=Color('#55555e', 'brightblack'),
    border=Color('#bdbdc7', 'white'),
    ok=Color('#1a6b3a', 'green'),
    warn=Color('#8a5a00', 'yellow'),
    err=Color('#a81f3c', 'red'),
    info=Color('#1b4f8a', 'blue'),
    accent=Color('#00756a', 'cyan'),
    accent2=Color('#7a1f7a', 'magenta'),
    trace=Color('#a81f3c', 'red'),
    noise=Color('#8a5a00', 'yellow'),
    residue=Color('#5f2f8a', 'magenta'),
    ice=Color('#1b4f8a', 'blue'),
    credit=Color('#1a6b3a', 'green'),
    heat=Color('#b03a10', 'red'),
)


PALETTES = {p.name: p for p in (
    CYBERPUNK_NEON, NEUTRAL, ANSI,
    AMBER, PHOSPHOR, KAGAWA, CARRION, DEEPWATER, STATIC, ASH, PAPER,
)}
DEFAULT = CYBERPUNK_NEON

#: Every role name, for `validate.py` to check that palettes stay in step and
#: for the `theme` command to demonstrate the whole set.
ROLES = tuple(f.name for f in Palette.__dataclass_fields__.values() if f.name != 'name')


def get(name: str | None) -> Palette:
    """Look up a palette by name, falling back to the default."""
    if not name:
        return DEFAULT
    return PALETTES.get(name, DEFAULT)
