"""The cold open (D115): a first job, before there is a you.

A text game asks a newcomer to make a character and read a stat sheet before
anything has happened to them, and the best thing in this game (the writing,
the tension, the story) is the last thing they meet. The cold open turns that
around. It drops the player into a short, on-rails heist as somebody else,
already mid-job, and teaches the loop by making them run it once with a voice
in their ear and the trace climbing, then hands them the question the whole
game is really asking: now, who are you?

It is a scripted scene, not a real run: it never touches the combat maths, so
it cannot stall or fail on somebody who has typed nothing at a game before. It
uses the real verbs (`scan`, `crack`, `grab`, `jack out`), so what it teaches
transfers, and it uses the picture layer (D102) so the first ninety seconds
look like nothing they have seen in a terminal. Whatever they type, it moves
forward: the word they were reaching for is shown, and the scene carries on.

Every beat is a `Question` (D50): the scene is a chain of them, each handler
drawing its beat and asking the next, the last one rolling straight into
guided character creation.
"""

from __future__ import annotations

# The verbs each beat is listening for, loosely. Anything else still advances
# the scene, with the real word shown, because a hook that punishes a wrong
# guess is not a hook.
_SCAN = ('scan', 'look', 'recon', 'map', 'see')
_CRACK = ('crack', 'break', 'hack', 'connect', 'open', 'in')
_GRAB = ('grab', 'take', 'pull', 'steal', 'exfil', 'get', 'copy')
_OUT = ('jack', 'out', 'leave', 'run', 'go', 'disconnect', 'quit')
_SKIP = ('skip', 'new', 'creation')


def _said(line: str, verbs) -> bool:
    words = line.lower().split()
    return any(v in words or any(w.startswith(v) for w in words) for v in verbs)


def _voice(c, text: str) -> None:
    """Switchboard, in your ear. Its own colour, so it reads as a person on
    the line rather than as the game narrating."""
    c.say(f'[accent]Switchboard[/][dim]:[/] [fg]{text}[/]')


def _trace(sess, pct: float) -> None:
    """The one number that matters in there, climbing. Green, amber, red."""
    c = sess.console
    width = 24
    fill = max(1, int(round(pct * width)))
    role = 'err' if pct >= 0.8 else 'warn' if pct >= 0.4 else 'ok'
    bar = sess.console.caps.g('bar_full') * fill
    rest = sess.console.caps.g('bar_empty') * (width - fill)
    c.raw(f'  [{role}]{bar}[/][dim]{rest}[/]  [dim]trace {int(pct * 100)}%[/]')


def _hosts(sess, mark_target: bool) -> None:
    """The three hosts a scan turns up, drawn with their type glyphs (D111)."""
    from .content import nodes as node_content
    from .ui import GlyphLevel
    c = sess.console
    plain = c.caps.glyphs is not GlyphLevel.UNICODE
    rows = [('gw-node00', 'gateway', 'you are here'),
            ('fs-vault07', 'fileserver', 'the ledger' if mark_target else ''),
            ('ws-desk02', 'workstation', '')]
    for uid, kind, tag in rows:
        glyph = node_content.host_glyph(kind, plain)
        note = f'  [accent2]{tag}[/]' if tag else ''
        c.raw(f'  [dim]{glyph}[/] [fg]{uid:<12}[/] [dim]{kind}[/]{note}')


def play(sess) -> None:
    """Open the scene. Everything after is one handler asking the next."""
    c = sess.console
    from . import anim, pixels
    c.blank()
    c.rule('a borrowed deck', role='accent2')
    c.say('[dim]You are not you yet. Tonight you are wearing a dead runner\'s '
          'deck and her name, because the job was hers and she is not using '
          'either any more. A voice you paid for waits on the line. It calls '
          'itself Switchboard.[/]')
    c.blank()
    if pixels.can_render(c.caps):
        # A face for the target, drawn, so the first thing a newcomer sees is
        # the thing a terminal is not supposed to do.
        pix = pixels.render('sixes', 34, 14)
        if pix:
            anim.reveal(c, pix, 'their network, from the outside', quick=True)
            c.blank()
    anim.connect(c, 'gw-node00', quick=False)
    c.blank()
    _voice(c, 'You are on their gateway. Half a minute before the log works '
              'out your shape. Look around in there. Type scan.')
    sess.ask('in the dark > ', _beat_scan, must_answer=True,
             choices=_SCAN)


def _skip_or(sess, line, nxt) -> bool:
    """A player who wants past the scene gets past it. Returns True if handled."""
    if _said(line, _SKIP):
        sess.console.blank()
        sess.console.say('[dim]Straight to it, then.[/]')
        _to_creation(sess)
        return True
    return False


def _nudge(sess, line, verbs, word) -> None:
    """Show the word they were reaching for, if they did not reach it, then
    carry on regardless."""
    if not _said(line, verbs):
        sess.console.say(f'[dim](the word was `{word}`. It carries on.)[/]')


def _beat_scan(sess, line) -> None:
    if _skip_or(sess, line, None):
        return
    c = sess.console
    _nudge(sess, line, _SCAN, 'scan')
    c.blank()
    c.say('[dim]The dark answers. Three shapes resolve out of it, close '
          'enough to touch.[/]')
    _hosts(sess, mark_target=True)
    c.blank()
    _trace(sess, 0.14)
    c.blank()
    _voice(c, 'The fileserver. That is where the ledger lives. Break into it. '
              'Type crack.')
    sess.ask('in the dark > ', _beat_crack, must_answer=True, choices=_CRACK)


def _beat_crack(sess, line) -> None:
    if _skip_or(sess, line, None):
        return
    c = sess.console
    _nudge(sess, line, _CRACK, 'crack')
    c.blank()
    c.say('[dim]You put a shoulder to fs-vault07. It holds, holds, and then '
          'it is not a wall any more, it is a door, and you are through it.[/]')
    c.blank()
    _trace(sess, 0.48)
    c.blank()
    _voice(c, 'In. The ledger is right there. Take it and nothing else, and do '
              'not read it. Type grab.')
    sess.ask('inside > ', _beat_grab, must_answer=True, choices=_GRAB)


def _beat_grab(sess, line) -> None:
    if _skip_or(sess, line, None):
        return
    c = sess.console
    from . import anim
    _nudge(sess, line, _GRAB, 'grab')
    c.blank()
    c.say('[dim]The ledger comes loose into the deck, warm and heavier than a '
          'file has any right to be. And the network stops pretending it '
          'cannot see you.[/]')
    c.blank()
    anim.disrupt(c, frames=8, height=6)
    _trace(sess, 0.92)
    c.blank()
    _voice(c, 'That woke something. It has your shape now and it is coming '
              'down the wire for it. Do not be here. Type jack out.')
    sess.ask('[err]it is coming[/] > ', _beat_out, must_answer=True,
             choices=_OUT)


def _beat_out(sess, line) -> None:
    if _skip_or(sess, line, None):
        return
    c = sess.console
    from . import anim
    _nudge(sess, line, _OUT, 'jack out')
    c.blank()
    c.say('[dim]You rip the connection out by the root. The room lunges, '
          'closes on the place you were, and finds cooling air. Then the '
          'ceiling of a rented booth, and your own hands, and the sweat cold '
          'on the back of your neck.[/]')
    c.blank()
    _voice(c, 'You are out. You are breathing. Not everyone who takes that job '
              'is, tonight.')
    c.blank()
    c.say('[dim]The ledger sits in the deck with a word in it you were not '
          'paid to read, and read anyway.[/] [accent2]Deepwater.[/]')
    c.blank()
    c.say('[dim]Switchboard is quiet for a second longer than a machine '
          'should be.[/]')
    _voice(c, '"Forget you saw that."')
    c.blank()
    c.rule('and now', role='accent2')
    c.say('[dim]That was her deck. Her name. Her job. You gave it back the '
          'moment you were clear of it, because it was never yours.[/]')
    c.blank()
    c.say('[fg]The next one is yours. Who are you?[/]')
    c.blank()
    _to_creation(sess)


def _to_creation(sess) -> None:
    from .commands import guide
    guide.start_creation(sess)
