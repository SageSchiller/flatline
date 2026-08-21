"""The city, drawn. D57.

`map` drew a tree: true, dense, and not a picture anybody could hold in
their head, because a tree has one route into everything and the city has
two into most things. This is the other half: the nine districts laid out
the same way every time, with the joins drawn, and you marked on it.

The layout is authored, not computed. Laying out a graph is a research
problem and this graph has nine nodes and fourteen edges that have not
changed since the city was drawn; a hand layout that reads well beats a
general one that reads correctly. What `validate.py` holds is that the
edges the drawing claims (`MAP_EDGES`) are exactly the edges in
`districts.GRAPH`, so the picture cannot quietly lie about the city.

Every glyph goes through `caps.g`, so the ASCII rung gets `|`, `-`, `\\`
and `/` and the same shape.
"""

from __future__ import annotations

from .content import districts
from . import ui

#: Every join the drawing shows, as unordered pairs. Checked against
#: `districts.GRAPH` by `validate.py`: a district gaining or losing a
#: neighbour without the map changing is a build failure.
MAP_EDGES: frozenset[frozenset[str]] = frozenset(frozenset(p) for p in (
    ('terraces', 'vertical'), ('vertical', 'green'),
    ('terraces', 'ninth'), ('vertical', 'marrow'), ('green', 'glasshouse'),
    ('vertical', 'precinct'), ('precinct', 'marrow'),
    ('ninth', 'marrow'), ('marrow', 'glasshouse'),
    ('ninth', 'shambles'), ('ninth', 'freeport'), ('marrow', 'freeport'),
    ('glasshouse', 'freeport'), ('shambles', 'freeport'),
))

#: Markers after a district's name. Plain, so they survive the ASCII rung.
MARK_HERE = '@'
MARK_JOB = '!'
MARK_WANTED = 'x'

#: Left margin, so the picture sits inside the text column rather than
#: against the edge of it.
_MARGIN = 4


def draw(game, caps, flags=None) -> list[str]:
    """The city as markup lines, you on it, the job on it, danger on it."""
    city = game.city
    contract = city.current
    goal = contract.district if contract else ''
    walked = set(city.visited)
    g = caps.g
    v, h = g('vline'), g('hline')
    dn, up = g('diag_dn'), g('diag_up')

    def slot(key: str, width: int, joined: bool = False) -> str:
        """A district's name, marked and coloured, padded on visible width.

        `joined` pads with the rule rather than spaces, so a label shorter
        than its slot runs straight into the edge beside it instead of
        leaving a gap that reads as a break in the road.
        """
        here = key == city.where
        marks = ''
        if here:
            marks += MARK_HERE
        if key == goal:
            marks += MARK_JOB
        if not here:
            danger, _ = city.danger(game.alias, key, flags=flags)
            if danger >= 25:
                marks += MARK_WANTED
        role = ('accent' if here else 'accent2' if key == goal
                else 'fg' if key in walked else 'dim')
        text = f'[{role}]{key}[/]'
        if marks:
            text += f'[warn]{marks}[/]'
        pad = max(0, width - len(key) - len(marks))
        if joined:
            return text + (f'[dim]{h * pad}[/]' if pad else '')
        return text + ' ' * pad

    def at(parts: list[tuple[int, str]]) -> str:
        """A row from (column, text) pieces, padded on visible width."""
        out = ''
        col = 0
        for where, text in parts:
            out += ' ' * max(0, where - col)
            out += text
            col = max(col, where) + ui.width(text)
        return out

    m = _MARGIN
    # Column plan (0-based, margin included): terraces/ninth/shambles slots
    # start at m, vertical/marrow/freeport at m+14, green/glasshouse at m+30,
    # precinct at m+20. The bars sit two in from each slot's left edge.
    # Every connector is dimmed at construction rather than by a replace
    # afterwards: the ASCII rung's `/` is also the character in `[/]`.
    rule = f'[dim]{{}}[/]'
    v, dn, up = f'[dim]{v}[/]', f'[dim]{dn}[/]', f'[dim]{up}[/]'
    rows = [
        at([(m, slot('terraces', 10, True)), (m + 10, rule.format(h * 4)),
            (m + 14, slot('vertical', 10, True)),
            (m + 24, rule.format(h * 6)), (m + 30, slot('green', 8))]),
        at([(m + 2, v), (m + 16, v), (m + 18, dn), (m + 32, v)]),
        at([(m + 2, v), (m + 16, v), (m + 20, slot('precinct', 10)),
            (m + 32, v)]),
        at([(m + 2, v), (m + 16, v), (m + 18, up), (m + 32, v)]),
        at([(m, slot('ninth', 8, True)), (m + 8, rule.format(h * 6)),
            (m + 14, slot('marrow', 9, True)), (m + 23, rule.format(h * 7)),
            (m + 30, slot('glasshouse', 12))]),
        at([(m + 2, v), (m + 8, dn), (m + 16, v), (m + 31, up)]),
        at([(m + 2, v), (m + 9, dn), (m + 16, v), (m + 30, up)]),
        at([(m, slot('shambles', 10, True)), (m + 10, rule.format(h * 4)),
            (m + 14, slot('freeport', 10, True)),
            (m + 24, rule.format(h * 5)), (m + 29, up)]),
    ]
    return rows


def legend(caps) -> str:
    """What the marks mean, one line."""
    return (f'[dim]{MARK_HERE} you  {MARK_JOB} the job  {MARK_WANTED} '
            f'somebody there wants you  dim: not yet walked[/]')
