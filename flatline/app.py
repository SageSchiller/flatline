"""Entry point: parse the arguments, build a session, hand over to the loop.

Deliberately thin. Everything interesting is in `session.py` and the command
modules; this file exists to turn a command line into a `Session` and to make
sure the terminal is left in a sane state whatever happens.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace

from . import commands  # noqa: F401  (registers the command table)
from . import save as save_mod
from . import theme
from .config import APP_NAME, SEED_MAX
from .session import Session
from .ui import Console, detect_caps


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog=APP_NAME,
        description='A text-based cyberpunk intrusion game.')
    p.add_argument('--seed', type=int, default=None,
                   help=f'world seed, 0 to {SEED_MAX}. Worlds are '
                        f'reproducible: the same seed is the same city.')
    p.add_argument('--theme', default=None, choices=sorted(theme.PALETTES),
                   help='colour palette for this session only. Ignores what '
                        'you have unlocked, on purpose: the catalogue is a '
                        'reward channel and this is your terminal. `ansi` '
                        'inherits whatever your terminal already does.')
    p.add_argument('--ascii', action='store_true',
                   help='ASCII only, for terminals without Unicode.')
    p.add_argument('--no-color', action='store_true',
                   help='no colour at all.')
    p.add_argument('--no-intro', action='store_true',
                   help='skip the cold start. FLATLINE_NO_INTRO does the '
                        'same thing permanently. Ctrl-C skips it once.')
    # No default, so "the player named a slot" is distinguishable from "the
    # player said nothing", which is the difference between obeying an
    # instruction and inventing one.
    p.add_argument('--slot', default=None,
                   help='save slot to use. Defaults to the character you '
                        'played last.')
    p.add_argument('--continue', dest='cont', action='store_true',
                   help='open the most recently played character.')
    p.add_argument('--no-continue', dest='no_continue', action='store_true',
                   help='start at the roster and open nobody.')
    p.add_argument('-c', '--command', action='append', default=[],
                   metavar='CMD',
                   help='run a command and exit. Repeatable. Used by test.py '
                        'and useful for scripting a known opening.')
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    caps = detect_caps(theme_name=args.theme, ascii_only=args.ascii,
                       no_color=args.no_color)
    console = Console(caps)
    # Written for eighty columns (D170): narrower, the map and the tables
    # wrap rather than break, and the player should hear that once rather
    # than wonder.
    if caps.width < 80 and getattr(sys.stdout, 'isatty', lambda: False)():
        console.warn(f'flatline is written for eighty columns and this '
                     f'terminal has {caps.width}. It runs; the map and the '
                     f'tables will wrap until it is wider.')
    sess = Session(console=console, slot=args.slot or 'default')
    # The shell the player earned, before anything is printed. An explicit
    # --theme on the command line still wins: a flag you typed this second
    # beats a preference you set last week.
    sess.apply_shell()
    if args.theme:
        sess.console.caps = replace(sess.console.caps,
                                    palette=theme.get(args.theme))

    _open_a_character(sess, args, console)

    if args.command:
        # Non-interactive mode: no splash, no readline.
        for line in args.command:
            sess.execute(line)
            if not sess.running:
                break
        # And then it saves, the same as leaving the prompt does. It used
        # not to, which sounds like the safe choice and was not: a handful
        # of commands autosave on their own (anything that moves a shift,
        # anything on the street), so a `-c` run wrote *some* of what it
        # did. Spending your budget and then taking a job persisted the
        # spend and lost the job, and the next invocation said no contract
        # accepted, which reads as the game forgetting rather than as a
        # policy about non-interactive mode (D74).
        #
        # Mid-run is the one exception, because a run is not in the save
        # format at all: `quit` refuses while you are jacked in for the
        # same reason, and writing here would file the city as it was
        # before you jacked in and quietly lose the run.
        if sess.game is not None and sess.run is None:
            sess.autosave()
        return sess.exit_code

    sess.splash(quick=args.no_intro)
    if sess.game is not None:
        game = sess.game
        console.say(f'[dim]Continuing as [/][accent]{game.char.handle}[/]'
                    f'[dim], running as {game.alias.name}.[/]')
        if len(_living(sess)) > 1:
            console.say('[dim]`characters` for the others.[/]')
        # Where you left it (D62): a save is a place, and nobody remembers a
        # place they left a week ago well enough to stand back up in it.
        from .commands.guide import previously
        previously(sess)
        console.blank()
    elif len(_living(sess)) > 1:
        # Nobody open and several to choose from. Show them rather than
        # picking, because picking for the player is exactly the thing that
        # dropped somebody into a character they had not asked for.
        sess.execute('characters')
        console.blank()
    return sess.loop()


def _living(sess) -> list:
    return [e for e in save_mod.roster() if not e.broken]


def _open_a_character(sess, args, console) -> None:
    """Decide who the player is, before anything is printed.

    The old rule was: if the default slot has a save in it, become that
    person. That was fine while there could only ever be one character, and
    became a trap the moment there could be several, because it silently
    resumed one of them and the banner underneath still said `new` to make a
    character.

    The rule now: an explicit --slot or --continue is obeyed. A single
    character is continued, because that is the whole reason the game
    remembers anything. Several characters and no instruction means the
    player gets the roster and picks, since being handed the wrong one is
    worse than one extra command.
    """
    asked = args.slot
    if args.no_continue and not (asked or args.cont):
        return

    living = _living(sess)
    slot = asked
    if slot is None and (args.cont or len(living) == 1):
        # Most recently played, which for one character is that character and
        # for --continue is the one they were last in the middle of.
        slot = living[0].slot if living else None
    if slot is None:
        return
    if not save_mod.exists(slot):
        if asked is not None and not args.command:
            console.err(f'no character in slot {slot!r}.')
        return
    try:
        sess.load_game(slot)
    except Exception as e:  # a bad save must not stop the game booting
        console.err(str(e))


if __name__ == '__main__':
    sys.exit(main())
