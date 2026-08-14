"""Prompt shapes.

The prompt is the single most riced object in the entire practice of ricing,
so it gets its own file and six of them.

**Inside a run, every style shows the trace.** That is the hard rule and the
only one. A style may abbreviate, reorder, decorate and drop almost anything
else, because everything else is one `status` away and costs nothing to ask
for. The trace is the number that ends the character, it is the reason the
prompt carries state at all, and a cosmetic that could hide it would be a
cosmetic that changes the game. `validate.py` renders every style against a
live run and checks the number survives.

The other constraint is that a prompt is printed several hundred times an
hour, so nothing here may be slow, and nothing here may be wide: the styles
are sized so that the longest of them still leaves most of an eighty-column
line for what the player is typing.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Style:
    key: str
    name: str
    blurb: str
    #: What it looks like, for the catalogue, with no session to render from.
    #: Written in console markup, so a literal `[` is `[[`: the Bracket style
    #: is made almost entirely of things the tag parser would otherwise eat,
    #: and its sample rendered as `[1,200c] $` until this was noticed. A
    #: literal `{{` is a footnote for the same reason, so the Structured
    #: style's sample uses single braces.
    sample: str


STYLES: tuple[Style, ...] = (
    Style('classic', 'Classic',
          'What the deck shipped with. Everything spelled out, separated by '
          'the bullet you chose.',
          'marrow · morning · 1,200c > '),
    Style('minimal', 'Minimal',
          'The facts and nothing else, in the fewest characters that can '
          'carry them.',
          'marrow morning 1200c > '),
    Style('bracket', 'Bracket',
          'Segmented. Reads fast once your eye knows which bracket is which.',
          '[[marrow][[morning][[1,200c] $ '),
    Style('path', 'Path',
          'The city as a filesystem, which is either a joke about netrunners '
          'or the most honest thing in this game.',
          '/city/marrow/morning $ '),
    Style('powerline', 'Powerline',
          'Segments with pointed separators. Needs a font that has the '
          'glyphs, and falls back cleanly when it does not.',
          'marrow ▶ morning ▶ 1,200c ▶ '),
    Style('terse', 'Terse',
          'For people who have played enough that the prompt is furniture.',
          'mrw» '),
    Style('json', 'Structured',
          'The state as a record. Somebody built this deck for machines to '
          'read and never got round to changing it.',
          '{where:marrow, shift:morning, c:1200} > '),
    Style('caret', 'Caret',
          'Angle brackets, one level per fact. Older than everything else in '
          'this list and it has outlasted all of them.',
          '<marrow|morning|1,200c> '),
)

BY_KEY: dict[str, Style] = {s.key: s for s in STYLES}
STYLE_KEYS: tuple[str, ...] = tuple(BY_KEY)
DEFAULT = 'classic'


def _run_parts(state) -> tuple[str, str, str]:
    """(where, tick, trace) inside a run. Every style needs all three."""
    trace = (f'{int(state.trace_pct * 100)}%' if not state.blind_trace
             else state.trace_label())
    return state.here, str(state.tick), trace


def _city_parts(game) -> tuple[str, str, str]:
    """(where, when, money) in the city."""
    return (game.city.district.name.lower(), game.city.when,
            f'{game.char.credits:,}')


def render(sess, style: str = DEFAULT) -> str:
    """Build the prompt for the session's current state."""
    caps = sess.caps
    key = style if style in BY_KEY else DEFAULT
    bullet, arrow = caps.g('bullet'), caps.g('arrow')

    if sess.run is not None:
        where, tick, trace = _run_parts(sess.run)
        return _shape(key, where=where, mid=f'tick {tick}', tail=f'trace {trace}',
                      slug=trace, short=where.split('-')[0][:6],
                      bullet=bullet, arrow=arrow, root='run')
    if sess.game is not None:
        where, when, money = _city_parts(sess.game)
        return _shape(key, where=where, mid=when, tail=f'{money}c',
                      slug=sess.game.city.phase, short=where[:3],
                      bullet=bullet, arrow=arrow, root='city')
    # No character loaded. Every style still has to look like itself, or the
    # title screen quietly reverts everybody to Classic and the first thing a
    # player sees after choosing a prompt is not the prompt they chose.
    return {
        'classic': 'flatline > ',
        'minimal': '> ',
        'bracket': '[flatline] $ ',
        'path': '/ $ ',
        'powerline': f'flatline {arrow} ',
        'terse': 'fl» ',
        'json': '{state:none} > ',
        'caret': '<flatline> ',
    }.get(key, 'flatline > ')


def _shape(key: str, where: str, mid: str, tail: str, slug: str, short: str,
           bullet: str, arrow: str, root: str) -> str:
    """The facts, arranged.

    `slug` is the one thing that must survive whatever the style does to the
    rest: the trace in a run, the shift in the city. The compact styles are
    built out of `short` and `slug` rather than by truncating the full form,
    which is how `path` used to lose the trace entirely.
    """
    if key == 'minimal':
        return f'{where} {mid} {tail.replace(",", "")} > '
    if key == 'bracket':
        return f'[{where}][{mid}][{tail}] $ '
    if key == 'path':
        return f'/{root}/{where}/{slug.replace(" ", "-")} $ '
    if key == 'powerline':
        return f'{where} {arrow} {mid} {arrow} {tail} {arrow} '
    if key == 'terse':
        return f'{short}\u00b7{slug}» '
    if key == 'json':
        # Built from the parts rather than from the formatted strings, which
        # is why it reads as a record instead of as `day:1,:morning`.
        run = root == 'run'
        fields = (f'host:{where}, tick:{mid.split()[-1]}, trace:{slug}' if run
                  else f'where:{where}, shift:{slug}, '
                       f'c:{tail.rstrip("c").replace(",", "")}')
        return '{' + fields + '} > '
    if key == 'caret':
        return f'<{where}|{mid}|{tail}> '
    return f'{where} {bullet} {mid} {bullet} {tail} > '


def sample_run(style: str, caps) -> str:
    """A representative in-run prompt, with no run to read from.

    Used by the rice preview, which draws a run screen and needs the prompt
    under it to be the one you would actually see there.
    """
    key = style if style in BY_KEY else DEFAULT
    return _shape(key, where='ap-arc21', mid='tick 14', tail='trace 62%',
                  slug='62%', short='ap', bullet=caps.g('bullet'),
                  arrow=caps.g('arrow'), root='run')
