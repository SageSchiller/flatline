#!/usr/bin/env python3
"""Screenshots of the real game as SVG, for the README.

Drives a seeded life through the play-test harness with a true-colour console
and the author's palette, captures what the game printed, and writes each
screen as an SVG of a terminal window: text, not pixels, so it is crisp at any
size, diffs like text, and is regenerated from the code rather than kept in
step with it by hand. Nothing here is drawn by hand except the window.

    python3 tools/shots.py            # writes docs/shot-*.svg
    python3 tools/shots.py --print    # also prints each screen to the terminal
"""
from __future__ import annotations

import html
import io
import os
import pathlib
import re
import sys
from dataclasses import replace

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools' / 'playtest'))
sys.path.insert(0, str(ROOT))

import harness  # noqa: E402  (sets XDG_DATA_HOME before flatline is imported)
from harness import Play  # noqa: E402
from flatline import anim, theme  # noqa: E402
from flatline.ui import ColorLevel  # noqa: E402
from flatline.commands import city as city_cmd  # noqa: E402

OUT = ROOT / 'docs'
SEED = 8829
COLS = 80
BG = '#0a0c16'
FG = '#dce7ff'
CH_W = 7.83      # px per column at 13px in the usual monospaces
LINE_H = 17.0    # px per row
PAD_X, PAD_TOP, PAD_BOT = 18, 44, 18
FONT = ("ui-monospace, 'SF Mono', Menlo, Consolas, 'DejaVu Sans Mono', "
        "'Liberation Mono', monospace")

_SGR = re.compile(r'\x1b\[([0-9;]*)m')
_OTHER = re.compile(r'\x1b\[[0-9;?]*[A-Za-ln-z]|\x1b[^\[]')


def _runs(line: str):
    """Split one rendered line into (text, fill, bold, ul, rev, bg) runs."""
    fill, bold, ul, rev, bg = None, False, False, False, None
    pos = 0
    out = []
    for m in _SGR.finditer(line):
        if m.start() > pos:
            out.append((line[pos:m.start()], fill, bold, ul, rev, bg))
        codes = [int(c) for c in m.group(1).split(';') if c] or [0]
        i = 0
        while i < len(codes):
            c = codes[i]
            if c == 0:
                fill, bold, ul, rev, bg = None, False, False, False, None
            elif c == 49:
                bg = None
            elif c == 48 and i + 4 < len(codes) and codes[i + 1] == 2:
                bg = '#%02x%02x%02x' % (codes[i + 2], codes[i + 3], codes[i + 4])
                i += 4
            elif c == 1:
                bold = True
            elif c == 4:
                ul = True
            elif c == 7:
                rev = True
            elif c in (22, 24, 27):
                bold, ul, rev = (bold if c != 22 else False, ul if c != 24 else False,
                                 rev if c != 27 else False)
            elif c == 39:
                fill = None
            elif c == 38 and i + 4 < len(codes) and codes[i + 1] == 2:
                fill = '#%02x%02x%02x' % (codes[i + 2], codes[i + 3], codes[i + 4])
                i += 4
            i += 1
        pos = m.end()
    if pos < len(line):
        out.append((line[pos:], fill, bold, ul, rev, bg))
    return out


def svg(screen: str, title: str, cols: int = COLS) -> str:
    lines = _OTHER.sub('', screen).replace('\r', '').split('\n')
    while lines and not _SGR.sub('', lines[-1]).strip():
        lines.pop()
    while lines and not _SGR.sub('', lines[0]).strip():
        lines.pop(0)
    rows = len(lines)
    w = int(PAD_X * 2 + cols * CH_W)
    h = int(PAD_TOP + rows * LINE_H + PAD_BOT)
    body = []
    y = PAD_TOP + 12
    for line in lines:
        spans = []
        rects = []
        x = PAD_X
        plain_len = 0
        for text, fill, bold, ul, rev, bg in _runs(line):
            if not text:
                continue
            attrs = []
            if rev:
                bg, fill = (fill or FG), BG
            if bg:
                rects.append(f'<rect x="{x:.1f}" y="{y - 13:.1f}" width="{len(text) * CH_W:.2f}" '
                             f'height="{LINE_H:.1f}" fill="{bg}"/>')
            if fill:
                attrs.append(f'fill="{fill}"')
            if bold:
                attrs.append('font-weight="bold"')
            if ul:
                attrs.append('text-decoration="underline"')
            spans.append(f'<tspan {" ".join(attrs)}>{html.escape(text, quote=False)}</tspan>'
                         if attrs else html.escape(text, quote=False))
            x += len(text) * CH_W
            plain_len += len(text)
        # Every row is forced onto the column grid: a block or box-drawing
        # glyph from a fallback font would otherwise have its own advance and
        # the map would shear.
        body.extend(rects)
        body.append(f'<text x="{PAD_X}" y="{y:.1f}" textLength="{plain_len * CH_W:.2f}" '
                    f'lengthAdjust="spacingAndGlyphs">{"".join(spans)}</text>')
        y += LINE_H
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{FONT}" font-size="13px">
<style>text{{white-space:pre;fill:{FG}}}</style>
<rect width="{w}" height="{h}" rx="9" fill="{BG}" stroke="#24345c"/>
<circle cx="19" cy="17" r="5" fill="#ff5f8f"/><circle cx="37" cy="17" r="5" fill="#ffd479"/><circle cx="55" cy="17" r="5" fill="#72f1b8"/>
<text x="{w / 2:.0f}" y="21" text-anchor="middle" fill="#5a6b94" font-size="12px">{html.escape(title, quote=False)}</text>
<line x1="0" y1="32" x2="{w}" y2="32" stroke="#24345c"/>
{chr(10).join(body)}
</svg>
'''


class Shots:
    def __init__(self):
        self.p = Play('shots', origin='gutter', seed=SEED, handle='Keeper', log=io.StringIO())
        self.p.con.caps = replace(self.p.con.caps, color=ColorLevel.TRUE,
                                  palette=theme.CYBERPUNK_NEON, width=COLS)
        self.taken: dict[str, str] = {}

    def grab(self, name: str, cmds, title: str = ''):
        con = self.p.con
        con.start_capture()
        for c in cmds:
            self.p.sess.execute(c)
        out = con.end_capture()
        self.p.settle()
        self.taken[name] = svg(out, title or f'flatline  ·  {"  ".join(cmds)}')
        if '--print' in sys.argv:
            print(out)
        return out

    def title(self):
        con = self.p.con
        con.start_capture()
        anim.boot(con, quick=True)
        out = con.end_capture()
        self.taken['title'] = svg(out, 'flatline')
        if '--print' in sys.argv:
            print(out)

    def to_run(self, cap=20):
        p = self.p
        for _ in range(cap):
            if p.sess.run is not None or p.g.over:
                return
            steps = city_cmd.city_steps(p.g)
            if not steps:
                p.do('board')
                if p.g.city.board and p.g.city.current is None:
                    soft = min(p.g.city.board, key=lambda c: c.posture)
                    p.do(f'take {soft.cid}'); p.settle(); continue
                p.do('rest'); p.settle(); continue
            p.do_step(steps[0][0]); p.settle()

    def build(self):
        p = self.p
        self.title()
        # a job on the board, so the map has somewhere to point: a breach,
        # so the network shot has doors in it, and the softest of those
        soft = None
        for _ in range(6):
            p.do('board')
            breaches = [c for c in p.g.city.board if c.objective != 'escort']
            if breaches:
                soft = min(breaches, key=lambda c: c.posture)
                break
            p.do('rest'); p.settle()
        soft = soft or min(p.g.city.board, key=lambda c: c.posture)
        p.do(f'take {soft.cid}'); p.settle()
        self.grab('city', ['map'], 'flatline  ·  map')
        self.grab('job', ['job'], 'flatline  ·  job')
        # into the network
        self.to_run()
        if p.sess.run is not None:
            # Some way in, so the map has hosts on it and the sum has a door.
            step = ''
            for _ in range(10):
                run = p.sess.run
                if run is None:
                    break
                b = run.brief()
                step = b.steps[0] if b.steps else ''
                if b.done or run.objective_met() or not step or '<' in step:
                    break
                if step.startswith(('crack', 'probe')) and _ >= 4:
                    break
                p.do(step); p.settle()
            if p.sess.run is not None:
                self.grab('run', ['map'], 'flatline  ·  map')
                if step.startswith(('crack', 'probe')):
                    self.grab('odds', [f'odds {step}'], f'flatline  ·  odds {step}')
                self.grab('brief', ['job'], 'flatline  ·  job')
            p.drive_run()
        # a few more, so somebody remembers you
        for _ in range(3):
            p.play_job()
        mem = p.g.city.memory
        if mem:
            fac = max(mem, key=lambda k: mem[k].get('runs', 0))
            self.grab('render', [f'render {fac}'], f'flatline  ·  render {fac}')
        self.grab('record', ['record'], 'flatline  ·  record')
        self.grab('char', ['char'], 'flatline  ·  char')
        return self.taken


#: Row colours for the wordmark, top to bottom: the palette's own run from
#: accent to accent2, the same one the boot animation settles on.
ROW_COLOURS = ['#00f0ff', '#3fd3ff', '#6cb6ff', '#9a9cf5', '#c792ea', '#ff5fd7']


def banner() -> str:
    """The wordmark as rectangles, not glyphs, so it needs no font at all;
    a scanline; the trace drawing in underneath and then a pulse crossing it
    and going flat, which is the name. Every animation starts from the still
    frame, so a viewer that ignores SMIL sees the finished banner."""
    rows = anim.mark()
    cell_w, cell_h, gap = 12, 20, 1
    cols = max(len(r) for r in rows)
    mark_w = cols * cell_w
    w = mark_w + 120
    ox = (w - mark_w) // 2
    oy = 46
    mark_h = len(rows) * cell_h
    parts = []
    for r, row in enumerate(rows):
        fill = ROW_COLOURS[r % len(ROW_COLOURS)]
        # one path per row, runs of cells merged, so the file stays small
        c = 0
        while c < len(row):
            if row[c] != '█':
                c += 1
                continue
            start = c
            while c < len(row) and row[c] == '█':
                c += 1
            parts.append(f'<rect x="{ox + start * cell_w}" y="{oy + r * cell_h}" '
                         f'width="{(c - start) * cell_w - gap}" height="{cell_h - gap}" fill="{fill}">'
                         f'<animate attributeName="opacity" values="1;1;0.35;1;1" keyTimes="0;{0.07 + r * 0.02:.2f};{0.1 + r * 0.02:.2f};{0.13 + r * 0.02:.2f};1" dur="9s" repeatCount="indefinite"/>'
                         f'</rect>')
    trace_y = oy + mark_h + 18
    tag_y = trace_y + 40
    h = tag_y + 36
    # the pulse: flat, one blip, flat; drawn once per loop across the trace
    blip = (f'M{ox},{trace_y} h{mark_w * 0.42:.0f} l6,-16 l6,30 l6,-22 l5,8 h{mark_w * 0.5:.0f}')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{FONT}">
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#0a0c16"/><stop offset="1" stop-color="#10142a"/>
  </linearGradient>
  <linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#00f0ff" stop-opacity="0"/><stop offset="0.5" stop-color="#00f0ff" stop-opacity="0.16"/><stop offset="1" stop-color="#00f0ff" stop-opacity="0"/>
  </linearGradient>
</defs>
<rect width="{w}" height="{h}" rx="12" fill="url(#sky)"/>
<g>{''.join(parts)}</g>
<rect x="0" y="-60" width="{w}" height="60" fill="url(#scan)">
  <animate attributeName="y" values="-60;{h}" dur="6s" repeatCount="indefinite"/>
</rect>
<line x1="{ox}" y1="{trace_y}" x2="{ox + mark_w}" y2="{trace_y}" stroke="#ff5f8f" stroke-width="2" stroke-linecap="round">
  <animate attributeName="x2" values="{ox};{ox + mark_w};{ox + mark_w}" keyTimes="0;0.3;1" dur="9s" repeatCount="indefinite"/>
</line>
<path d="{blip}" fill="none" stroke="#ff5f8f" stroke-width="2" stroke-linejoin="round" stroke-dasharray="{mark_w + 80}" stroke-dashoffset="{mark_w + 80}" opacity="0.9">
  <animate attributeName="stroke-dashoffset" values="{mark_w + 80};{mark_w + 80};0;0;{-(mark_w + 80)}" keyTimes="0;0.35;0.6;0.7;1" dur="9s" repeatCount="indefinite"/>
</path>
<text x="{w / 2:.0f}" y="{tag_y}" text-anchor="middle" fill="#7d8cb0" font-size="15px" letter-spacing="1.5">a city that does not care whether you live</text>
<text x="{w / 2:.0f}" y="{tag_y + 20}" text-anchor="middle" fill="#5a6b94" font-size="12px">python3 flatline.pyz</text>
</svg>
'''


def main() -> int:
    OUT.mkdir(exist_ok=True)
    (OUT / 'banner.svg').write_text(banner())
    print('docs/banner.svg')
    shots = Shots().build()
    for name, text in shots.items():
        (OUT / f'shot-{name}.svg').write_text(text)
        print(f'docs/shot-{name}.svg  {len(text):,} bytes')
    return 0


if __name__ == '__main__':
    sys.exit(main())
