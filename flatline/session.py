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
from . import theme
from .content import factions, rice
from .config import APP_TITLE, TAGLINE_PARTS, history_path
from .game import Game
from .content import tutorial
from .script import MAX_DISPATCH, ScriptError, parse
from . import anim
from . import prompt as prompt_mod
from .shell import REGISTRY, CommandError, Invocation, Quit, resolve, split_line
from .ui import Caps, Console


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
    #: Commands the player has used at least once. The tutorial reads it,
    #: because "have they looked at their own character sheet" is a real
    #: teaching goal and is not otherwise visible in game state.
    seen: set = field(default_factory=set)
    #: Index of the current tutorial step, or -1 when it is not running.
    tutorial_step: int = -1
    #: Which prompt shape the player has chosen. See `prompt.py`.
    prompt_style: str = 'classic'

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

        The *shape* is the player's, per the rice catalogue, but the content is
        not negotiable: every style shows the same facts. A prompt style that
        could hide the trace would be a cosmetic that changes the game, and
        `validate.py` checks that none of them do.
        """
        return prompt_mod.render(self, self.prompt_style)

    # ------------------------------------------------------------------
    # the shell, and what unlocks it
    # ------------------------------------------------------------------

    def record_progress(self) -> None:
        """Update the meta counters, and say so if that earned something.

        Called from the two places time actually moves: the end of a run and
        the shift tick. Everything it records is a high-water mark rather than
        a total, because these are "has this player ever" questions, and
        because writing the meta file on every single shift when nothing has
        changed is a great deal of fsync for nothing.
        """
        game = self.game
        if game is None:
            return
        best_rep = max((game.alias.reputation(k) for k in factions.FACTION_KEYS),
                       default=0)
        threads = sum(1 for stages in game.story.reached.values() if stages)
        save_mod.high_water(
            best_credits=game.char.credits,
            deepest_drift=game.char.dissonance,
            districts_seen=len(game.city.visited),
            bounties_taken=1 if game.city.bounties else 0,
            black_ice_survived=1 if 'black_ice' in game.char.marks else 0,
            threads_closed=threads,
            best_standing=best_rep,
        )
        self.announce_unlocks()

    def announce_unlocks(self) -> None:
        """Tell the player about anything they have just earned, once."""
        meta = save_mod.read_meta()
        already = set(meta.get('unlocked') or ())
        fresh = rice.newly_earned(meta, already)
        if not fresh:
            return
        for item in fresh:
            already.add(f'{item.kind}:{item.key}')
        meta['unlocked'] = sorted(already)
        save_mod.write_meta(meta)
        # Recorded, but not announced. What you started with is not a reward,
        # and eleven of these are available on the first command: a player
        # whose first ever screen is a wall of things they already had learns
        # to skip the box, and then the box cannot tell them anything.
        fresh = [item for item in fresh if item.needs[0] != 'always']
        if not fresh:
            return
        c = self.console
        c.blank()
        c.rule('unlocked', role='accent2')
        for item in fresh:
            c.raw(f'  [accent]{item.name}[/] [dim]{item.kind}[/]')
            c.say(f'[dim]{item.blurb}[/]', indent='  ', subsequent='  ')
        c.blank()
        c.say(f'[dim]`rice` to put {"them" if len(fresh) > 1 else "it"} on. '
              f'It stays yours whatever happens to this character.[/]')

    @property
    def shell(self) -> dict:
        """The saved look, filled in with defaults for anything unset."""
        meta = save_mod.read_meta()
        out = dict(rice.DEFAULTS)
        out.update({k: v for k, v in (meta.get('shell') or {}).items()
                    if (k, v) in rice.BY_KEY or k in rice.DEFAULTS})
        return out

    def apply_shell(self) -> None:
        """Rebuild the console's capabilities from the saved preferences."""
        look = self.shell
        self.prompt_style = look.get('prompt', prompt_mod.DEFAULT)
        caps = self.console.caps
        self.console.caps = Caps(
            color=caps.color, glyphs=caps.glyphs, width=caps.width,
            palette=theme.get(look.get('palette')),
            frame=look.get('frame', 'single'),
            bars=look.get('bars', 'blocks'),
            marks=look.get('marks', 'plain'))

    def splash(self, quick: bool = False) -> None:
        c = self.console
        sep = f' {c.caps.g("bullet")} '
        anim.boot(c, char=self.game.char if self.game else None,
                  quick=quick, style=self.shell.get('banner', 'block'))
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
            self.seen.add(inv.command.name)
        except CommandError as e:
            if str(e):
                self.console.err(str(e))
        except Quit as q:
            self.console.footnotes()
            self.running = False
            self.exit_code = q.code
            return
        # Asides go at the bottom of the block that raised them, the way they
        # do on a page. Flushing here rather than in each command means any
        # content anywhere can write one without knowing this exists, and an
        # error path cannot leave a note orphaned into the next command.
        self.console.footnotes()
        # The tutorial watches rather than leads: it checks after every
        # command whether the current step has been satisfied, however the
        # player got there.
        if self.tutorial_step >= 0:
            self.tutorial_advance()

    # ------------------------------------------------------------------
    # tutorial
    # ------------------------------------------------------------------

    def tutorial_show(self) -> None:
        """Print the current instruction."""
        if not 0 <= self.tutorial_step < len(tutorial.STEPS):
            return
        step = tutorial.STEPS[self.tutorial_step]
        c = self.console
        c.blank()
        c.rule(f'step {self.tutorial_step + 1} of {len(tutorial.STEPS)}',
               role='accent2')
        c.say(f'[accent]{step.instruction}[/]')
        c.blank()
        c.say(f'[dim]{step.why}[/]')
        if step.topic:
            c.say(f'[dim]More: `help {step.topic}`.[/]')

    def tutorial_advance(self) -> None:
        """Complete every satisfied step, and show the next one.

        A loop rather than a single check, because one command can satisfy
        several steps at once and stopping after the first would leave the
        player being told to do something they have already done.

        A condition that raises must never take the shell down with it: the
        tutorial is optional and a bug in it is not worth a traceback in the
        middle of somebody's run.
        """
        c = self.console
        while 0 <= self.tutorial_step < len(tutorial.STEPS):
            step = tutorial.STEPS[self.tutorial_step]
            try:
                done = bool(step.done(self))
            except Exception:
                done = False
            if not done:
                return
            if step.payoff:
                c.blank()
                c.say(f'[ok]{c.caps.g("check")}[/] [dim]{step.payoff}[/]')
            self.tutorial_step += 1
            if self.tutorial_step >= len(tutorial.STEPS):
                self.tutorial_step = -1
                c.blank()
                c.rule('done', role='accent2')
                for line in tutorial.CLOSING.split('\n\n'):
                    for part in line.split('\n'):
                        if part.startswith('  '):
                            c.raw(part)
                        else:
                            c.say(part)
                    c.blank()
                return
            self.tutorial_show()

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
