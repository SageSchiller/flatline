"""The network, drawn (D104).

`map` inside a run has always been a tree: breadth-first from the entry,
back edges listed underneath. A tree is honest and a terminal is good at
them, and it is not a picture of a place. This is: the zones as columns
from the perimeter on the left to the core on the right, every host you
know as a label in its column, and every edge you know as a line between
them on a character canvas, with you, the job, and what is awake marked
in colour. It knows nothing about play. It reads the same fields the tree
reads and draws them, which is the whole of D35.
"""

from __future__ import annotations

from .content import nodes as node_content
from .ui import Caps, GlyphLevel

ZONES = ('perimeter', 'interior', 'restricted', 'core')

#: The line glyphs, at both rungs: horizontal, vertical, the two diagonals,
#: a crossing.
GLYPHS = {'h': ('─', '-'), 'v': ('│', '|'), 'd': ('╲', '\\'), 'u': ('╱', '/'),
          'x': ('┼', '+')}


class Canvas:
    def __init__(self, width: int, height: int, ascii_only: bool) -> None:
        self.w, self.h = width, height
        self.rung = 1 if ascii_only else 0
        self.cells: list[list[tuple[str, str | None]]] = [
            [(' ', None) for _ in range(width)] for _ in range(height)]
        #: Cells a label owns; lines never overwrite them.
        self.fixed: set[tuple[int, int]] = set()

    def g(self, name: str) -> str:
        return GLYPHS[name][self.rung]

    def put(self, x: int, y: int, ch: str, role: str | None,
            fixed: bool = False) -> None:
        if not (0 <= x < self.w and 0 <= y < self.h):
            return
        if (x, y) in self.fixed and not fixed:
            return
        old, old_role = self.cells[y][x]
        if not fixed and old != ' ' and old != ch:
            # Two lines meeting. A horizontal across a vertical is a
            # crossing; anything else keeps the brighter of the two.
            hv = {self.g('h'), self.g('v')}
            if old in hv and ch in hv:
                ch = self.g('x')
            elif old_role == 'accent' and role != 'accent':
                return
        self.cells[y][x] = (ch, role)
        if fixed:
            self.fixed.add((x, y))

    def hline(self, x0: int, x1: int, y: int, role) -> None:
        for x in range(min(x0, x1), max(x0, x1) + 1):
            self.put(x, y, self.g('h'), role)

    def vline(self, x: int, y0: int, y1: int, role) -> None:
        for y in range(min(y0, y1), max(y0, y1) + 1):
            self.put(x, y, self.g('v'), role)

    def elbow(self, x0: int, y0: int, x1: int, y1: int, role) -> None:
        """An edge as a schematic draws one: out along the row, a corner,
        down or up the column, a corner, in along the row. Reads as wiring
        rather than as a diagonal picked out in box characters."""
        if y0 == y1:
            self.hline(x0, x1, y0, role)
            return
        if x0 == x1:
            self.vline(x0, y0, y1, role)
            return
        mid = (x0 + x1) // 2
        self.hline(x0, mid, y0, role)
        self.vline(mid, y0, y1, role)
        self.hline(mid, x1, y1, role)
        if self.rung == 0:
            right = x1 > x0
            down = y1 > y0
            first = ('┐' if right else '┌') if down else ('┘' if right else '└')
            second = ('└' if right else '┘') if down else ('┌' if right else '┐')
            self.put(mid, y0, first, role, fixed=True)
            self.put(mid, y1, second, role, fixed=True)
        else:
            self.put(mid, y0, '+', role, fixed=True)
            self.put(mid, y1, '+', role, fixed=True)

    def label(self, x: int, y: int, text: str, role: str | None) -> int:
        """Left edge at x. Returns the right edge (exclusive)."""
        left = max(0, min(self.w - len(text), x))
        for i, ch in enumerate(text):
            self.put(left + i, y, ch, role, fixed=True)
        return left + len(text)

    def rows(self) -> list[str]:
        out = []
        for row in self.cells:
            parts, last = [], None
            for ch, role in row:
                if role != last:
                    if last is not None:
                        parts.append('[/]')
                    if role is not None:
                        parts.append(f'[{role}]')
                    last = role
                parts.append('[[' if ch == '[' else ch)
            if last is not None:
                parts.append('[/]')
            out.append(''.join(parts).rstrip())
        return out


def draw(net, state, caps: Caps, tall: bool = False) -> list[str]:
    """The known network as a schematic, as markup rows."""
    ascii_only = caps.glyphs is GlyphLevel.ASCII
    known = [n for n in net.nodes.values() if n.known]
    if not known:
        return []
    width = min(caps.text_width, 78)
    columns = {z: sorted((n for n in known if n.zone == z), key=lambda n: n.uid)
               for z in ZONES}
    deepest = max((len(v) for v in columns.values()), default=1)
    height = max(7, (3 if tall else 2) * deepest + 3)
    canvas = Canvas(width, height, ascii_only)
    lanes = [z for z in ZONES if columns[z]]
    span = max(1, len(lanes) - 1)
    lane_w = max(12, (width - 4) // max(1, len(lanes)))
    x_of = {z: 2 + i * lane_w for i, z in enumerate(lanes)}
    here = state.here if state is not None else ''
    # Where each label sits, and its edges.
    pos: dict[str, tuple[int, int]] = {}
    labels: dict[str, str] = {}
    for z in lanes:
        nodes = columns[z]
        gap = (height - 2) / (len(nodes) + 1)
        for i, node in enumerate(nodes):
            marks = ''
            if node.uid == here:
                marks += '@'
            if node.uid == net.objective_node:
                marks += '!'
            live = [c for c in node.ice if c.alive and c.known]
            if live:
                marks += ('^' if ascii_only else '▲') * min(2, len(live))
            # The type glyph leads the label (D111): the map reads as a field
            # of shapes, so you can see the vault sitting in the core before
            # you read a single host id. A disguised honeypot draws the
            # workstation glyph, giving nothing the word did not.
            glyph = node_content.host_glyph(node.display_type, ascii_only)
            labels[node.uid] = f'{glyph} {marks}{node.uid}'
            pos[node.uid] = (x_of[z], 1 + int(round(gap * (i + 1))))
    # The route to the job, lit; every other edge dim.
    route = set()
    target = net.node(net.objective_node) if net.objective_node else None
    if target is not None and target.known and state is not None:
        chain = [state.here] + list(state.route_to(net.objective_node))
        route = {tuple(sorted((a, b))) for a, b in zip(chain, chain[1:])}
    drawn = set()
    for node in known:
        for other in node.edges:
            if other not in pos or node.uid not in pos:
                continue
            key = tuple(sorted((node.uid, other)))
            if key in drawn:
                continue
            drawn.add(key)
            a, b = (node.uid, other) if pos[node.uid][0] <= pos[other][0] \
                else (other, node.uid)
            (x0, y0), (x1, y1) = pos[a], pos[b]
            role = 'accent' if key in route else 'dim'
            if x0 == x1:
                # Same column: a lane down the left of the labels.
                canvas.vline(x0 - 1, y0, y1, role)
            else:
                canvas.elbow(x0 + len(labels[a]), y0, x1 - 1, y1, role)
    for node in known:
        x, y = pos[node.uid]
        live = [c for c in node.ice if c.alive and c.known]
        awake = [c for c in live if c.state != 'dormant']
        if node.uid == here:
            role = 'ok'
        elif node.uid == net.objective_node:
            role = 'accent2'
        elif awake:
            role = 'err'
        elif state is not None and not state.in_reach(node.uid):
            # Seen, not reachable from here (D184): the scan saw it and
            # nothing you type will touch it until you are next to it.
            role = 'dim'
        elif node.open:
            role = 'accent'
        else:
            role = 'dim'
        canvas.label(x, y, labels[node.uid], role)
    for z in lanes:
        canvas.label(x_of[z], 0, z, 'muted')
    rows = canvas.rows()
    legend = ('[dim]@ you  ! the job  ' + ('^' if ascii_only else '▲')
              + ' something on it  lit: the way to the job[/]')
    reach = '[dim]dim: shut, or out of reach from where you stand[/]'
    # A key for the type glyphs, but only for the types actually on the map,
    # so it names what you can see and grows as you find more (D111).
    present = {n.display_type for n in known}
    key = '  '.join(f'{node_content.host_glyph(name, ascii_only)} {name}'
                     for name in node_content.HOST_GLYPHS if name in present)
    return rows + [legend, reach, f'[dim]{key}[/]']
