"""The command layer, per D9. One table feeds dispatch, help, and completion.

The registry is the single source of truth about what verbs exist. `help` reads
it, tab completion reads it, `validate.py` reads it and fails the build on a
command with no summary or an unreachable context. There is deliberately no
second list of commands anywhere, because two lists is one list plus a bug.

Commands are context-scoped. `crack` does not exist while you are in the city
and `market` does not exist while you are inside somebody's network, and the
shell says so in those words rather than "unknown command", because the
difference between "that verb is not real" and "that verb is not real *here*"
is most of what a new player needs to learn.
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from typing import Callable, Iterable, Sequence

#: Where a command is legal. `any` means both.
CONTEXTS = ('city', 'run', 'any')

#: Help groupings, in display order. A command's group must be one of these.
GROUPS = (
    'session',    # save, quit, help
    'character',  # char, skills, deck, install
    'city',       # board, travel, market
    'prep',       # legwork, load, alias
    'recon',      # scan, probe, map
    'access',     # connect, crack, forge
    'action',     # deploy, pull, wipe
    'defence',    # mask, kill, overclock
    'info',       # status, log, odds
)


class CommandError(Exception):
    """A problem the player caused and can fix. Printed, never traced."""


class Quit(Exception):
    """Leave the session cleanly. Carries an exit code."""

    def __init__(self, code: int = 0) -> None:
        super().__init__(code)
        self.code = code


# --------------------------------------------------------------------------
# arguments
# --------------------------------------------------------------------------


class Args:
    """Parsed arguments for one command invocation.

    Deliberately simple: positionals, long flags, and `--key value` options.
    A full option parser would be more capable and would also mean the game's
    verbs stop reading like shell commands and start reading like `argparse`,
    which is the wrong texture for the fiction.
    """

    __slots__ = ('positional', 'flags', 'options', 'raw')

    def __init__(self, tokens: Sequence[str]) -> None:
        self.raw = list(tokens)
        self.positional: list[str] = []
        self.flags: set[str] = set()
        self.options: dict[str, str] = {}
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok.startswith('--') and len(tok) > 2:
                key = tok[2:]
                if '=' in key:
                    k, v = key.split('=', 1)
                    self.options[k] = v
                elif i + 1 < len(tokens) and not tokens[i + 1].startswith('--'):
                    self.options[key] = tokens[i + 1]
                    i += 1
                else:
                    self.flags.add(key)
            else:
                self.positional.append(tok)
            i += 1

    def __len__(self) -> int:
        return len(self.positional)

    def __getitem__(self, i: int) -> str:
        return self.positional[i]

    def get(self, i: int, default: str | None = None) -> str | None:
        return self.positional[i] if i < len(self.positional) else default

    def require(self, i: int, what: str) -> str:
        if i >= len(self.positional):
            raise CommandError(f'expected {what}')
        return self.positional[i]

    def rest(self, i: int = 0) -> str:
        return ' '.join(self.positional[i:])

    def has(self, flag: str) -> bool:
        return flag in self.flags

    def opt(self, key: str, default: str | None = None) -> str | None:
        return self.options.get(key, default)

    def int_opt(self, key: str, default: int) -> int:
        raw = self.options.get(key)
        if raw is None:
            return default
        try:
            return int(raw)
        except ValueError:
            raise CommandError(f'--{key} wants a number, got {raw!r}') from None

    def int_at(self, i: int, default: int, what: str = 'a number') -> int:
        """A positional integer, or a `CommandError` the player can read.

        Every command that takes a count uses this rather than `int()`, because
        a bare `int()` on player input turns a typo into a traceback. The fuzz
        pass in `test.py` exists specifically to keep this honest.
        """
        raw = self.get(i)
        if raw is None:
            return default
        try:
            return int(raw)
        except ValueError:
            raise CommandError(f'expected {what}, got {raw!r}') from None


# --------------------------------------------------------------------------
# registry
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Command:
    name: str
    summary: str
    handler: Callable
    group: str = 'session'
    contexts: tuple[str, ...] = ('any',)
    aliases: tuple[str, ...] = ()
    usage: str = ''
    detail: str = ''
    #: Base tick cost inside a run. Zero means free, which is correct for
    #: anything that only reads state the player already has.
    ticks: int = 0
    #: Optional argument completer: (ctx, prefix, args) -> list[str].
    complete: Callable | None = None
    #: True for commands that must work even with no character loaded.
    bare: bool = False

    def legal_in(self, context: str) -> bool:
        return 'any' in self.contexts or context in self.contexts


class Registry:
    def __init__(self) -> None:
        self.commands: dict[str, Command] = {}
        self.by_alias: dict[str, str] = {}

    def add(self, cmd: Command) -> Command:
        if cmd.name in self.commands:
            raise RuntimeError(f'duplicate command {cmd.name!r}')
        if cmd.group not in GROUPS:
            raise RuntimeError(f'{cmd.name}: unknown group {cmd.group!r}')
        for c in cmd.contexts:
            if c not in CONTEXTS:
                raise RuntimeError(f'{cmd.name}: unknown context {c!r}')
        self.commands[cmd.name] = cmd
        for a in cmd.aliases:
            if a in self.by_alias or a in self.commands:
                raise RuntimeError(f'{cmd.name}: alias {a!r} already taken')
            self.by_alias[a] = cmd.name
        return cmd

    def command(self, name: str, summary: str, **kw):
        def deco(fn: Callable) -> Callable:
            self.add(Command(name=name, summary=summary, handler=fn, **kw))
            return fn
        return deco

    def lookup(self, word: str) -> Command | None:
        if word in self.commands:
            return self.commands[word]
        target = self.by_alias.get(word)
        return self.commands.get(target) if target else None

    def in_context(self, context: str) -> list[Command]:
        return sorted((c for c in self.commands.values() if c.legal_in(context)),
                      key=lambda c: (GROUPS.index(c.group), c.name))

    def names(self, context: str | None = None) -> list[str]:
        cmds = self.in_context(context) if context else list(self.commands.values())
        out: list[str] = []
        for c in cmds:
            out.append(c.name)
            out.extend(c.aliases)
        return sorted(out)

    def prefix_matches(self, word: str, context: str) -> list[Command]:
        """Unique-prefix resolution, so `conn` reaches `connect`.

        Worth having in a game where you type the same eight verbs a thousand
        times, and safe because ambiguity is reported rather than guessed.
        """
        seen: dict[str, Command] = {}
        for c in self.in_context(context):
            for n in (c.name, *c.aliases):
                if n.startswith(word):
                    seen[c.name] = c
        return list(seen.values())


#: The one registry. Command modules import this and decorate against it.
REGISTRY = Registry()
command = REGISTRY.command


# --------------------------------------------------------------------------
# parsing a line
# --------------------------------------------------------------------------


@dataclass(slots=True)
class Invocation:
    command: Command
    args: Args
    word: str
    line: str


def split_line(line: str) -> list[str]:
    """One input line into zero or more command strings.

    `;` separates, `#` starts a comment. Both matter more than they look:
    chained commands are how a player expresses "do these three things as one
    decision", and comments are what make a saved script readable when they
    come back to it twenty shifts later.
    """
    try:
        lexer = shlex.shlex(line, posix=True, punctuation_chars=';')
        lexer.whitespace_split = True
        lexer.commenters = '#'
        tokens = list(lexer)
    except ValueError as e:
        raise CommandError(f'could not parse that line: {e}') from None

    out: list[list[str]] = [[]]
    for tok in tokens:
        if tok == ';':
            out.append([])
        else:
            out[-1].append(tok)
    return [' '.join(shlex.quote(t) for t in part) for part in out if part]


def resolve(line: str, context: str, registry: Registry = REGISTRY) -> Invocation:
    """One command string into something dispatchable, or a helpful error."""
    try:
        tokens = shlex.split(line, comments=True)
    except ValueError as e:
        raise CommandError(f'could not parse that: {e}') from None
    if not tokens:
        raise CommandError('')

    word, rest = tokens[0].lower(), tokens[1:]

    # Two-word verbs read better in the fiction than hyphenated ones, and
    # `jack in` / `jack out` are the two most important commands in the game.
    if rest:
        joined = f'{word} {rest[0].lower()}'
        cmd = registry.lookup(joined)
        if cmd and cmd.legal_in(context):
            return Invocation(cmd, Args(rest[1:]), joined, line)

    # `lookup` ignores context on purpose: a command that exists but is illegal
    # here should reach the `legal_in` check below and get the specific error,
    # not be reported as unknown.
    cmd = registry.lookup(word)
    if cmd is None:
        matches = registry.prefix_matches(word, context)
        if len(matches) == 1:
            cmd = matches[0]
        elif len(matches) > 1:
            names = ', '.join(sorted(c.name for c in matches))
            raise CommandError(f'{word!r} is ambiguous: {names}')
        else:
            raise CommandError(
                f'{word!r} is not a command. Type `help` for what is.')

    if not cmd.legal_in(context):
        where = 'inside a run' if 'run' in cmd.contexts else 'in the city'
        raise CommandError(f'`{cmd.name}` only works {where}.')

    return Invocation(cmd, Args(rest), word, line)
