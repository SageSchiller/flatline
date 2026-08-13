"""The REPL: the whole of D2's interface.

`Session` owns everything live: the console, the loaded game, the active run if
there is one, and the shell's own state (aliases, scripts, history). Commands
receive it and are otherwise stateless, which is what makes a command a
function rather than a class.

The loop is deliberately dull. Read a line, split it on `;`, resolve each part
against the registry for the current context, call it, print whatever it says.
Errors that are the player's fault print and continue; errors that are the
game's fault are allowed to propagate, because a traceback the player can paste
is worth more than a swallowed exception that leaves the world half-updated.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

from . import save as save_mod
from .config import APP_TITLE, TAGLINE_PARTS, history_path
from .game import Game
from .script import MAX_DISPATCH, ScriptError, parse
from .shell import REGISTRY, CommandError, Invocation, Quit, resolve, split_line
from .ui import Caps, Console

#: Longest a script may be, so a runaway `script` cannot lock the session.
MAX_SCRIPT = 40


@dataclass(slots=True)
class Session:
    console: Console
    game: Game | None = None
    run: object | None = None          # RunState, typed loosely to avoid a cycle
    slot: str = 'default'
    #: Shell aliases: typed word -> replacement line.
    shell_aliases: dict = field(default_factory=dict)
    #: Saved scripts by name, unlocked by Daemonology rank 2. Held on the
    #: session but persisted with the game: a script library is a build
    #: investment and losing it on quit would make the whole feature a toy.
    scripts: dict = field(default_factory=dict)
    #: Set while a script is executing, to stop a script calling itself.
    in_script: bool = False
    running: bool = True
    exit_code: int = 0
    #: Everything typed this session, for `history` and for `script save`.
    typed: list = field(default_factory=list)

    # ------------------------------------------------------------------
    # context
    # ------------------------------------------------------------------

    @property
    def context(self) -> str:
        return 'run' if self.run is not None else 'city'

    @property
    def caps(self) -> Caps:
        return self.console.caps

    def require_game(self) -> Game:
        if self.game is None:
            raise CommandError('no character loaded. `new` to make one, '
                               '`load` to open a save.')
        return self.game

    def require_run(self):
        if self.run is None:
            raise CommandError('you are not in a run.')
        return self.run

    # ------------------------------------------------------------------
    # presentation
    # ------------------------------------------------------------------

    def prompt(self) -> str:
        """The prompt carries the two numbers that matter right now.

        In the city that is where you are and what time it is; in a run it is
        which node you are standing in and how close the trace is. Putting them
        here rather than in a status bar keeps D2 honest: there is no second
        surface, only the stream.
        """
        sep = self.caps.g('bullet')
        if self.run is not None:
            state = self.run
            pct = int(state.trace_pct * 100)
            trace = (f'trace {pct}%' if not state.blind_trace
                     else f'trace {state.trace_label()}')
            return f'{state.here} {sep} tick {state.tick} {sep} {trace} > '
        if self.game is not None:
            city = self.game.city
            return (f'{city.district.name.lower()} {sep} {city.when} {sep} '
                    f'{self.game.char.credits:,}c > ')
        return 'flatline > '

    def splash(self) -> None:
        c = self.console
        sep = f' {c.caps.g("bullet")} '
        c.blank()
        c.raw(f'[accent][bold]{APP_TITLE}[/][/]')
        c.raw(f'[dim]{sep.join(TAGLINE_PARTS)}[/]')
        c.blank()
        c.say('[dim]`help` for commands. `new` to make a character. '
              '`load` to continue one.[/]')
        c.blank()

    # ------------------------------------------------------------------
    # dispatch
    # ------------------------------------------------------------------

    def expand(self, line: str) -> str:
        """Apply shell aliases to the first word only.

        First word only, deliberately: an alias that can rewrite arguments is a
        macro system, and this game already has one of those in `script`.
        """
        stripped = line.strip()
        if not stripped:
            return stripped
        head, _, tail = stripped.partition(' ')
        target = self.shell_aliases.get(head)
        if target is None:
            return stripped
        return f'{target} {tail}'.strip()

    def execute(self, line: str) -> None:
        """One typed line, which may be several commands."""
        for part in split_line(self.expand(line)):
            if not self.running:
                return
            try:
                inv = resolve(part, self.context)
            except CommandError as e:
                if str(e):
                    self.console.err(str(e))
                continue
            self.invoke(inv)

    def invoke(self, inv: Invocation) -> None:
        if inv.command.bare is False and self.game is None:
            self.console.err('no character loaded. `new` to make one, '
                             '`load` to open a save.')
            return
        try:
            inv.command.handler(self, inv.args)
        except CommandError as e:
            if str(e):
                self.console.err(str(e))
        except Quit as q:
            self.running = False
            self.exit_code = q.code

    # ------------------------------------------------------------------
    # scripts
    # ------------------------------------------------------------------

    def run_script(self, name: str) -> None:
        """Execute a script, checking its conditions against live state.

        The conditions are the whole point (see `script.py`). A step whose
        condition is false is skipped and *said to be skipped*, because a
        script that silently does nothing is indistinguishable from a script
        that is broken, and the player has to be able to tell.
        """
        script = self.scripts.get(name)
        if script is None:
            raise CommandError(f'no script called {name!r}')
        if self.in_script:
            raise CommandError('a script cannot call another script')
        try:
            steps = script.steps
        except ScriptError as e:
            raise CommandError(f'{name}: {e}') from None

        state = self.run
        dispatched = 0
        self.in_script = True
        try:
            for step in steps:
                if not self.running:
                    break
                # Conditions read run state, so outside a run they are all
                # unanswerable and the script runs as a plain sequence.
                if step.condition is not None and state is not None:
                    if self.run is None:
                        break
                    truth = step.condition.evaluate(self.run)
                    if step.kind == 'stop':
                        if truth:
                            self.console.warn(
                                f'[dim]{name}:[/] stopped, {step.condition}.')
                            return
                        continue
                    if not truth:
                        self.console.raw(
                            f'[dim]  skipped ({step.condition}): '
                            f'{step.command}[/]')
                        continue
                elif step.kind == 'stop':
                    continue

                for _ in range(step.count):
                    if not self.running or dispatched >= MAX_DISPATCH:
                        break
                    # A run command after the run has ended is not an error,
                    # it is simply the rest of the script becoming moot.
                    if state is not None and self.run is None:
                        return
                    dispatched += 1
                    self.console.raw(f'[dim]> {step.command}[/]')
                    self.execute(step.command)
        finally:
            self.in_script = False

    # ------------------------------------------------------------------
    # readline
    # ------------------------------------------------------------------

    def setup_readline(self) -> None:
        """History and completion where the platform has them, silence where
        it does not. Never fatal: the game must work without readline."""
        try:
            import readline
        except ImportError:
            return
        path = history_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                readline.read_history_file(str(path))
            readline.set_history_length(2000)
        except OSError:
            pass
        readline.set_completer(self._completer)
        readline.parse_and_bind('tab: complete')
        readline.set_completer_delims(' \t\n')

    def save_readline(self) -> None:
        try:
            import readline
        except ImportError:
            return
        try:
            readline.write_history_file(str(history_path()))
        except OSError:
            pass

    def _completer(self, text: str, state: int):
        try:
            options = self._completions(text)
        except Exception:
            # A completer that raises kills the prompt silently. Never let it.
            return None
        return options[state] if state < len(options) else None

    def _completions(self, text: str) -> list[str]:
        import readline
        line = readline.get_line_buffer()[:readline.get_endidx()]
        words = line.split()
        first = not words or (len(words) == 1 and not line.endswith(' '))
        if first:
            names = REGISTRY.names(self.context) + list(self.shell_aliases)
            return sorted(n for n in names if n.startswith(text))
        cmd = REGISTRY.lookup(words[0])
        if cmd and cmd.complete:
            try:
                return sorted(o for o in cmd.complete(self, text)
                              if o.startswith(text))
            except Exception:
                return []
        return []

    # ------------------------------------------------------------------
    # the loop
    # ------------------------------------------------------------------

    def loop(self) -> int:
        self.setup_readline()
        try:
            while self.running:
                try:
                    line = input(self.prompt())
                except EOFError:
                    self.console.blank()
                    self.console.say('[dim]Connection closed.[/]')
                    break
                except KeyboardInterrupt:
                    self.console.blank()
                    self.console.say('[dim]Use `quit` to leave, or `jack out` '
                                     'if you are mid-run.[/]')
                    continue
                if line.strip():
                    self.typed.append(line.strip())
                self.execute(line)
        finally:
            self.save_readline()
        return self.exit_code

    # ------------------------------------------------------------------
    # persistence helpers
    # ------------------------------------------------------------------

    def autosave(self) -> None:
        """Called on shift boundaries. Silent on success, loud on failure,
        because a save that is quietly not happening is the worst outcome."""
        if self.game is None:
            return
        self.sync_scripts()
        try:
            self.game.save(self.slot)
        except OSError as e:
            self.console.err(f'autosave failed: {e}')

    def load_game(self, slot: str) -> None:
        try:
            self.game = Game.load(slot)
        except save_mod.SaveError as e:
            raise CommandError(str(e)) from None
        self.slot = slot
        self.run = None
        self.scripts = dict(self.game.scripts)

    def sync_scripts(self) -> None:
        """Push the session's script library back onto the game before a save."""
        if self.game is not None:
            self.game.scripts = dict(self.scripts)
