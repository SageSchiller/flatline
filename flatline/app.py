"""Entry point: parse the arguments, build a session, hand over to the loop.

Deliberately thin. Everything interesting is in `session.py` and the command
modules; this file exists to turn a command line into a `Session` and to make
sure the terminal is left in a sane state whatever happens.
"""

from __future__ import annotations

import argparse
import sys

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
                   help='colour palette. `ansi` inherits your terminal.')
    p.add_argument('--ascii', action='store_true',
                   help='ASCII only, for terminals without Unicode.')
    p.add_argument('--no-color', action='store_true',
                   help='no colour at all.')
    p.add_argument('--slot', default='default', help='save slot to use.')
    p.add_argument('--continue', dest='cont', action='store_true',
                   help='load the save slot immediately.')
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
    sess = Session(console=console, slot=args.slot)

    if args.cont or (not args.command and save_mod.exists(args.slot)):
        try:
            sess.load_game(args.slot)
        except Exception as e:  # a bad save must not stop the game booting
            console.err(str(e))

    if args.command:
        # Non-interactive mode: no splash, no readline, no autosave surprises.
        for line in args.command:
            sess.execute(line)
            if not sess.running:
                break
        return sess.exit_code

    sess.splash()
    if sess.game is not None:
        game = sess.game
        console.say(f'[dim]Continuing as [/][accent]{game.char.handle}[/]'
                    f'[dim], running as {game.alias.name}. '
                    f'{game.city.when}, {game.city.district.name}.[/]')
        console.blank()
    return sess.loop()


if __name__ == '__main__':
    sys.exit(main())
