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
from typing import Callable

from . import save as save_mod
from .content import threads as thread_content
from . import theme
from .content import factions, rice
from .config import APP_TITLE, TAGLINE_PARTS, history_path
from .game import Game
from .content import tutorial
from .script import MAX_DISPATCH, ScriptError, parse
from . import anim
from . import prompt as prompt_mod
from .shell import (AFTER_THE_END, REGISTRY, Args, CommandError, Invocation,
                    Quit, resolve, split_line)
from .ui import Caps, Console, prompt_render


@dataclass(slots=True)
class Question:
    """Something the game has asked, and is waiting on the next line for.

    D50. The shell is still the whole interface: a question is a prompt that
    says what it wants, and the answer is the next line typed, exactly as a
    command would be. What it adds is that a flow with three decisions in it
    can be three short answers rather than one line of flag syntax, which is
    the difference between `new` being a form and being a conversation.

    An empty line always backs out. A handler that does not like an answer
    says so and asks again; one that is happy does its work and either asks
    the next thing or leaves `pending` empty, which is how a conversation
    ends. Nothing here is allowed inside a run: every prompt style has to show
    the trace, and a question cannot.
    """

    #: What the prompt line shows while this is waiting. Short, ends in `? `.
    prompt: str
    #: Called with (session, answer). Raises CommandError for a bad answer
    #: after re-asking, or returns having done its work.
    handler: Callable
    #: What to say when the player backs out with an empty line.
    on_cancel: str = ''
    #: Tab-completion candidates while waiting, where readline exists.
    choices: tuple[str, ...] = ()
    #: The street does not wait (D65). An empty line or a back-out word is
    #: handed to the handler as '' rather than cancelling, so standing
    #: there is an answer. `quit` still quits.
    must_answer: bool = False


#: Words that back out of a question, besides an empty line.
BACK_OUT = frozenset({'cancel', 'stop', 'back', 'never mind', 'nevermind'})
#: What a yes-or-no question accepts as an answer. Anything else that is a
#: command is a command.
YES_NO_WORDS = frozenset({'yes', 'y', '1', 'go', 'do it', 'no', 'n', '2',
                          'keep'})


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
    #: Whether a command handler is running, and what it earned that is
    #: said once it has finished (D144).
    _in_command: bool = False
    _announce_queue: list = field(default_factory=list)
    #: The coach (D183): whether it is on, the lessons done (and the
    #: reasons already given, as `why:<key>`), the lessons ever shown, and
    #: the key of the one last printed in full, so a new lesson always
    #: prints and the same one never prints twice.
    tutorial_on: bool = False
    tutorial_done: set = field(default_factory=set)
    tutorial_told: set = field(default_factory=set)
    tutorial_shown: str = ''
    #: Set while a command has already printed the current lesson this turn
    #: (`now`, `tutorial`), so the coach line under the command stays quiet.
    _coach_said: bool = False
    #: Commands executed this session, and the one on which the current
    #: lesson was last printed in full: Enter right after a lesson repeats
    #: its instruction and not its paragraph.
    _turns: int = 0
    tutorial_shown_turn: int = -99
    #: Set while the first runner on this profile is being made (D182), so
    #: creation ends by turning the tutorial on. Nothing else reads it.
    teach: bool = False
    #: The cold open while it runs (D186): the scene's own state, spoken
    #: to after every command; and what it left for the runner made next.
    prologue: object | None = None
    prologue_result: dict = field(default_factory=dict)
    #: How many times the blank-prompt lifeline has been shown (D118). It
    #: fades after a few, and stops the moment `now` is used.
    lifelines: int = 0
    #: Which prompt shape the player has chosen. See `prompt.py`.
    prompt_style: str = 'classic'
    #: A question waiting on the next line, or None. See `Question`.
    pending: Question | None = None
    #: Which readout follows every tick-costing run action (D59): one of
    #: `rice.HUD_MODES`. Read from the shell (`rice hud`), cached here so an
    #: action does not read the meta file.
    hud: str = 'line'
    #: How a faction's cyberspace is shown on connect (D102): one of
    #: `rice.RENDER_MODES`.
    render_mode: str = 'mark'
    #: How a picture arrives on screen (D109): one of `rice.REVEAL_STYLES`.
    reveal_style: str = 'dissolve'
    #: The last list of each kind the player was shown, as the keys that were
    #: printed, in printed order. `take 2` means the second row of the board
    #: you last read, which is the only thing a row number can honestly
    #: mean: the board moves between shifts, and a number that silently
    #: re-pointed at whatever is there now would accept jobs the player never
    #: saw. See `pick`.
    listed: dict = field(default_factory=dict)

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
            raise CommandError(self.nobody_loaded())
        return self.game

    def after_the_end(self) -> str:
        """Why a finished character cannot do that.

        Named for what it is rather than for death, because retirement ends a
        character too and telling somebody who walked away that they are dead
        would be worse than saying nothing.
        """
        game = self.game
        handle = game.char.handle if game else 'this character'
        how = game.over if game else 'finished'
        others = [e for e in save_mod.roster()
                  if not e.broken and not e.finished and e.slot != self.slot]
        tail = (f'`switch {others[0].handle}`' if others else '`new`')
        return (f'{handle} {how}. You can still read the sheet and the log. '
                f'{tail} to carry on somewhere else.')

    def nobody_loaded(self) -> str:
        """What to say when a command needs a character and there is none.

        Adaptive, because the fixed version of this line told the player to
        type `load`, which is the command that puts a program on a deck. Being
        sent to the wrong command by the game's own error message is worse
        than no advice, and it named a character they might not have while
        saying nothing about the four they did.
        """
        living = [e for e in save_mod.roster() if not e.broken]
        if not living:
            return 'no character loaded. `new` to make one.'
        if len(living) == 1:
            return (f'no character loaded. `switch {living[0].handle}` for '
                    f'the one you have, or `new` to make another.')
        names = ', '.join(e.handle for e in living[:4])
        return (f'no character loaded. `characters` to see all {len(living)} '
                f'({names}), `switch <handle>` to pick one up.')

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

        While a question is waiting, the prompt is the question. That is the
        one case where the prompt carries no state, and it is allowed because
        a question is never asked inside a run.
        """
        if self.pending is not None:
            # Rendered like anything else (D182): a question's prompt is the
            # one prompt that may carry markup, and it used to print it raw.
            return prompt_render(self.pending.prompt, self.console.caps)
        # The prompt is markup too now (D187): the trace and the money lit.
        # Without a character the shapes are plain text with their own
        # brackets, which the renderer must not read as tags.
        text = prompt_mod.render(self, self.prompt_style)
        if self.game is None:
            text = text.replace('[', '[[')
        return prompt_render(text, self.console.caps)

    # ------------------------------------------------------------------
    # questions, and lists you can answer by number
    # ------------------------------------------------------------------

    def ask(self, prompt: str, handler: Callable, on_cancel: str = '',
            choices: tuple[str, ...] = (), must_answer: bool = False) -> None:
        """Wait for the next line and hand it to `handler`. See `Question`."""
        if self.run is not None:
            raise CommandError('not while you are in a run.')
        self.pending = Question(prompt=prompt, handler=handler,
                                on_cancel=on_cancel, choices=choices,
                                must_answer=must_answer)

    def cancel_question(self, say: bool = True) -> None:
        q, self.pending = self.pending, None
        if q is not None and say:
            self.console.say(f'[dim]{q.on_cancel or "Left it there."}[/]')

    def answer(self, line: str) -> None:
        """The next line typed while a question was waiting."""
        q, self.pending = self.pending, None
        text = line.strip()
        if (not text or text.lower() in BACK_OUT) and not q.must_answer:
            self.console.say(f'[dim]{q.on_cancel or "Left it there."}[/]')
            return
        if q.must_answer and text.lower() in BACK_OUT:
            text = ''
        # Somebody who types `quit` at a question wants out of the game, not
        # out of the question, and keeping them in a conversation they have
        # asked to leave is the thing every wizard ever built gets wrong.
        if text.lower() in ('quit', 'exit'):
            if q.must_answer:
                # The street does not wait for a session either (D101):
                # leaving the terminal at a knife in a doorway is standing
                # there, and it is settled before the game closes.
                try:
                    q.handler(self, '')
                except CommandError as e:
                    if str(e):
                        self.console.err(str(e))
                self.console.footnotes()
                if self.pending is not None:
                    self.pending = None
            else:
                self.console.say(f'[dim]{q.on_cancel or "Left it there."}[/]')
            self.execute(text)
            return
        # A verb typed at a yes-or-no question is somebody moving on, not
        # somebody answering it: `board 3` at "spend it this way?" used to
        # get "yes or no." three times running (D87). Only yes-or-no
        # questions, because a handle or an origin can be any word at all.
        if (q.choices == ('yes', 'no') and text.lower() not in YES_NO_WORDS
                and not q.must_answer):
            try:
                resolve(text.split(';')[0].strip(), self.context)
            except CommandError:
                pass
            else:
                self.console.say(f'[dim]{q.on_cancel or "Left it there."}[/]')
                self.execute(text)
                return
        try:
            q.handler(self, text)
        except CommandError as e:
            if str(e):
                self.console.err(str(e))
        except Quit as quit_:
            self.running = False
            self.exit_code = quit_.code
        self.console.footnotes()
        # The tutorial waits for the conversation to finish. An instruction
        # printed between one question and the next reads as the answer to
        # the question, and the tutorial is the one reader with no way to
        # tell that it was not.
        if self.tutorial_on and self.pending is None:
            self.tutorial_advance()

    def remember(self, kind: str, keys) -> None:
        """Record the list the player was just shown, for `pick`."""
        self.listed[kind] = list(keys)

    def pick(self, kind: str, token: str, fallback=None, what: str = 'row',
             again: str = '') -> str:
        """A row number into the key it stood for, or the token unchanged.

        `1` is the first row of the last `kind` list printed. When nothing of
        that kind has been printed this session, the live list is used, so
        `take 1` before `board` still means the first contract, which is what
        the player would have seen had they looked.
        """
        if not token.isdigit():
            return token
        shown = self.listed.get(kind)
        if shown is None:
            shown = list(fallback or ())
        n = int(token)
        if not 1 <= n <= len(shown):
            hint = f' `{again}` to see the list.' if again else ''
            if not shown:
                raise CommandError(f'there is nothing numbered here yet.{hint}')
            raise CommandError(
                f'there is no {what} {n}: the list runs 1 to {len(shown)}.'
                f'{hint}')
        return shown[n - 1]

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
        story = game.story
        flags = story.flags
        save_mod.high_water(
            # The record (D142): where you have been, who knows you, what
            # you have decided, and what you have put down.
            places_stood=sum(1 for f in flags if f.startswith('visited:')),
            relics_found=sum(1 for f in flags if f.startswith('found:')),
            nights_seen=sum(1 for f in flags if f.startswith('night:')),
            watch_hits=int(game.city.messaged.get('watch_hits', 0)),
            people_met=len(story.met),
            topics_asked=sum(1 for f in flags if f.startswith('asked:')),
            bonds_formed=sum(1 for r in game.city.rivals if getattr(r, 'bond', '')),
            decisions_made=sum(1 for f in flags if f.startswith('chose:')),
            fights_won=int(getattr(game.city, 'fights_won', 0)),
            pit_rank=int(game.city.pit.get('rank', 0)),
            pit_champion=1 if 'pit:champion' in flags else 0,
            factions_fought=sum(1 for f in flags if f.startswith('fought:')),
            doorways_held=sum(1 for f in flags if f.startswith('job:'))
                          + int(getattr(game.city, 'doorways', 0)),
            kills_done=1 if 'killer' in flags else 0,
            # The main line, carried to one of its ends (D143).
            spine_finished=1 if flags & thread_content.SPINE_ENDINGS else 0,
            best_credits=game.char.credits,
            deepest_drift=game.char.dissonance,
            districts_seen=len(game.city.visited),
            errands_done=int(getattr(game.city, 'errands_done', 0)),
            bounties_taken=1 if game.city.bounties else 0,
            black_ice_survived=1 if 'black_ice' in game.char.marks else 0,
            threads_closed=threads,
            best_standing=best_rep,
        )
        self.announce_unlocks()
        self.announce_record()

    def announce(self, fn) -> None:
        """Print now, or at the bottom of the current command's block."""
        if self._in_command:
            self._announce_queue.append(fn)
        else:
            fn()

    def flush_announcements(self) -> None:
        queue, self._announce_queue = self._announce_queue, []
        for fn in queue:
            fn()

    def announce_record(self) -> None:
        """Say a line of the record once, when it lands (D142)."""
        from .content import record as record_content
        from .world import record as record_world
        meta = save_mod.read_meta()
        counts = record_world.counts(self.game, meta)
        fresh = record_world.newly_earned(counts, meta.get('recorded'))
        if not fresh:
            return
        said = list(meta.get('recorded') or [])
        for entry in fresh:
            said.append(entry.key)
        meta['recorded'] = said
        save_mod.write_meta(meta)
        sections = []
        for key in record_world.sections_done(counts):
            flag = f'section:{key}'
            if flag in said:
                continue
            said.append(flag)
            sections.append(key)
            meta['recorded'] = said
            save_mod.write_meta(meta)

        def say(c=self.console, fresh=fresh, sections=sections):
            for entry in fresh:
                c.blank()
                c.rule('the record', role='accent2')
                c.say(f'[accent]{entry.name}.[/] {entry.earned}')
                if entry.title:
                    c.say(f'[dim]They have started saying it: [accent2]'
                          f'{entry.title}[/][dim].[/]')
            for key in sections:
                c.blank()
                c.say(f'[accent2]Every line of '
                      f'{record_content.BY_SECTION[key][0].section}. '
                      f'{record_content.SECTION_TITLE[key].capitalize()}.[/]')
        self.announce(say)
        self.announce_titles()

    def announce_titles(self) -> None:
        """Earn and say a flavoured title once, when the deed is done
        (D151). Recorded to the profile so a dead runner's title is
        still one the next can wear."""
        from .world import record as record_world
        meta = save_mod.read_meta()
        have = set(meta.get('titles') or ())
        fresh = [t for t in record_world.extra_earned(self.game)
                 if t.key not in have]
        if not fresh:
            return
        meta['titles'] = sorted(have | {t.key for t in fresh})
        save_mod.write_meta(meta)
        register = {'heroic': 'a name to keep', 'vile': 'a name to carry',
                    'amusing': 'a name, anyway'}

        def say(c=self.console, fresh=fresh, register=register):
            for t in fresh:
                c.blank()
                c.rule(register.get(t.register, 'a name'), role='accent2')
                c.say(t.earned)
                c.say(f'[dim]The city has a name for you now: [accent2]'
                      f'{t.name}[/][dim]. `called` to wear it, or one of '
                      f'the others.[/]')
        self.announce(say)

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

        def say(c=self.console, fresh=fresh):
            c.blank()
            c.rule('unlocked', role='accent2')
            for item in fresh:
                c.raw(f'  [accent]{item.name}[/] [dim]{item.kind}[/]')
                c.say(f'[dim]{item.blurb}[/]', indent='  ', subsequent='  ')
            c.blank()
            c.say(f'[dim]`rice` to put {"them" if len(fresh) > 1 else "it"} on. '
                  f'It stays yours whatever happens to this character.[/]')
        self.announce(say)

    @property
    def shell(self) -> dict:
        """The saved look, filled in with defaults for anything unset.

        Anything the catalogue does not recognise is dropped rather than
        carried, so a preference saved under a build that shipped a set this
        one does not falls back to the default instead of reaching the
        renderer. The `(kind, key)` pair is the test: checking the kind alone
        would let `palette: nonsense` through, which happens to degrade safely
        and would still be a saved preference nothing can honour.
        """
        meta = save_mod.read_meta()
        out = dict(rice.DEFAULTS)
        out.update({k: v for k, v in (meta.get('shell') or {}).items()
                    if (k, v) in rice.BY_KEY})
        return out

    def apply_shell(self) -> None:
        """Rebuild the console's capabilities from the saved preferences."""
        look = self.shell
        self.prompt_style = look.get('prompt', prompt_mod.DEFAULT)
        self.hud = look.get('hud', 'line')
        self.render_mode = look.get('render', 'mark')
        self.reveal_style = look.get('reveal', 'dissolve')
        caps = self.console.caps
        self.console.caps = Caps(
            color=caps.color, glyphs=caps.glyphs, width=caps.width,
            palette=theme.get(look.get('palette')),
            frame=look.get('frame', 'single'),
            bars=look.get('bars', 'blocks'),
            marks=look.get('marks', 'plain'))

    def outro(self, quick: bool = False) -> None:
        """The power-down on the way out (D181). Only after a clean quit:
        never on a crash, and `--no-intro` skips it the way it skips the
        boot."""
        anim.shutdown(self.console,
                      char=self.game.char if self.game else None,
                      quick=quick, style=self.shell.get('banner', 'block'))

    def splash(self, quick: bool = False) -> None:
        c = self.console
        sep = f' {c.caps.g("bullet")} '
        anim.boot(c, char=self.game.char if self.game else None,
                  quick=quick, style=self.shell.get('banner', 'block'))
        c.raw(f'[dim]{sep.join(TAGLINE_PARTS)}[/]')
        c.blank()
        living = [e for e in save_mod.roster() if not e.broken]
        if self.game is None and not living:
            # Nobody has ever sat down here. Three things to type, each with
            # what it does, rather than one sentence that assumes the reader
            # already knows what a command is. D50.
            c.say('[dim]This is a text game: you type a word and press '
                  'Enter. Enter on its own, at any point, says what to do '
                  'next.[/]')
            c.blank()
            c.say('[accent]Start here[/]')
            for name, blurb in (
                    ('begin', 'a first job, right now. The fastest way in, '
                              'and it teaches itself.'),
                    ('new', 'skip that and make a runner yourself.'),
                    ('tutorial', 'the coach: the next thing to type, and '
                                 'why, wherever you are.'),
                    ('legend', 'what the colours mean.'),
                    ('help', 'what to read first, and what it all means.')):
                c.say(f'[fg]{name}[/]{" " * (10 - len(name))}[dim]{blurb}[/]',
                      indent='  ', subsequent='            ')
        else:
            c.say(f'[dim]{self.opening_line()}[/]')
            c.say('[dim]Enter on an empty line says what to do next.[/]')
        c.blank()

    def opening_line(self) -> str:
        """The one line under the banner, which has to be true.

        It used to be fixed, and it read `new` to make a character, `load` to
        continue one. Both halves were wrong at once: `load` puts a program on
        a deck, the command is `restore`, and by the time this printed the
        game had usually already continued somebody, so the player was being
        told to start when they had in fact been handed a character they did
        not ask for.
        """
        living = [e for e in save_mod.roster() if not e.broken]
        if self.game is not None:
            return ('`help` for commands. `characters` for everybody you '
                    'have, `switch <handle>` to become one of them.')
        if not living:
            return '`help` for commands. `new` to make a character.'
        if len(living) == 1:
            return (f'`help` for commands. `switch {living[0].handle}` to '
                    f'carry on, `new` to make somebody else.')
        return ('`help` for commands. `characters` to see who you have, '
                '`new` to make somebody else.')

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
        """One typed line, which may be several commands.

        Or the answer to a question, if one is waiting: the whole line, not
        split on `;`, because an answer is not a command. Or nothing at all,
        which is the other thing D50 gives a meaning to: an empty line asks
        "what now", because that is what a player who does not know what to
        type does with the keyboard, and it used to be the one input the game
        had no answer to.
        """
        self._coach_said = False
        self._turns += 1
        if self.prologue is not None:
            from . import prologue as prologue_mod
            if prologue_mod.intercept(self, line):
                return
        if self.pending is not None:
            was_done = self._objective_state()
            self.answer(line)
            self._objective_turned(was_done)
            return
        if not line.strip():
            self.what_now()
            return
        for part in split_line(self.expand(line)):
            if not self.running:
                return
            try:
                inv = resolve(part, self.context)
            except CommandError as e:
                if str(e):
                    self.console.err(str(e))
                if self.prologue is not None:
                    # A wrong word in the cold open is answered by her
                    # repeating the right one (D186).
                    from . import prologue as prologue_mod
                    prologue_mod.after(self)
                continue
            was_done = self._objective_state()
            self.invoke(inv)
            self._objective_turned(was_done)

    def _objective_state(self):
        """Whether the run's objective is met, or None outside a run."""
        run = self.run
        if run is None:
            return None
        try:
            return bool(run.objective_met())
        except Exception:  # noqa: BLE001
            return None

    def _objective_turned(self, was_done) -> None:
        """The one moment the job gets done (D164): whichever verb did it,
        the familiar riding the deck has a line for it. Cosmetic; it reads
        the flip and nothing else."""
        if was_done is not False or self.run is None:
            return
        if self._objective_state():
            self.run.familiar_say('done')

    def what_now(self) -> None:
        """What an empty line means: the next move, and the verbs that matter.

        Goes through `invoke` like anything typed, so the tutorial sees it,
        footnotes flush, and a finished character gets the same answer they
        would get from typing `now`.
        """
        cmd = REGISTRY.lookup('now')
        if cmd is not None:
            self.invoke(Invocation(cmd, Args([]), 'now', ''))

    def invoke(self, inv: Invocation) -> None:
        if inv.command.bare is False and self.game is None:
            self.console.err(self.nobody_loaded())
            return
        if (self.game is not None and self.game.over
                and inv.command.name not in AFTER_THE_END):
            self.console.err(self.after_the_end())
            return
        self._in_command = True
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
        finally:
            self._in_command = False
        # What the shift earned is said after what the shift did (D144):
        # a line of the record landed between "1 shift pass" and "you did
        # not sleep well", and a palette between the walk and the street.
        self.flush_announcements()
        # Asides go at the bottom of the block that raised them, the way they
        # do on a page. Flushing here rather than in each command means any
        # content anywhere can write one without knowing this exists, and an
        # error path cannot leave a note orphaned into the next command.
        self.console.footnotes()
        # The tutorial watches rather than leads: it checks after every
        # command whether the current step has been satisfied, however the
        # player got there.
        if self.tutorial_on:
            self.tutorial_advance()
        if self.prologue is not None:
            from . import prologue as prologue_mod
            prologue_mod.after(self)

    # ------------------------------------------------------------------
    # tutorial
    # ------------------------------------------------------------------

    def tutorial_show(self, full: bool = True) -> None:
        """Print the current lesson (D183): in full, with the reason and the
        topic, or as the one-line coach line under a command."""
        cur = tutorial.current(self)
        if cur is None:
            return
        key, instruction, why, topic, number = cur
        c = self.console
        if not full:
            cmd = tutorial.command_of(instruction)
            if cmd == 'Enter':
                c.say(f'[dim]{c.caps.g("arrow")} next[/]  [accent]press '
                      f'Enter[/]')
            elif cmd:
                c.say(f'[dim]{c.caps.g("arrow")} next[/]  [accent]{cmd}[/]  '
                      f'[dim]Enter says why[/]')
            return
        c.blank()
        if key.startswith('run:'):
            # Inside a network the coach is the brief. The room is explained
            # once, ever; each verb's reason once, ever.
            if 'inside' not in self.tutorial_done:
                self.tutorial_done.add('inside')
                c.rule('inside', role='accent2')
                for para in tutorial.INSIDE.split('\n\n'):
                    c.say(f'[dim]{para}[/]')
                    c.blank()
            c.say(f'[accent2]coach[/]  [accent]{instruction}[/]',
                  subsequent='       ')
            if f'why:{key}' not in self.tutorial_done:
                self.tutorial_done.add(f'why:{key}')
                c.say(f'[dim]{why}[/]', indent='       ', subsequent='       ')
            self.tutorial_told.add('run')
        else:
            c.rule(f'lesson {number} of {len(tutorial.LESSONS)}',
                   role='accent2')
            c.say(f'[accent]{instruction}[/]')
            if why:
                c.blank()
                c.say(f'[dim]{why}[/]')
            if topic:
                c.say(f'[dim]More: `help {topic}`.[/]')
            c.say('[dim]`tutorial skip` passes this one; `tutorial stop` '
                  'ends the coach.[/]')
            self.tutorial_told.add(key)
        self.tutorial_shown = key
        self.tutorial_shown_turn = self._turns
        self._coach_said = True

    def tutorial_advance(self) -> None:
        """After every command while the coach is on: complete what is done
        and say so, end when the last lesson is done, and show the lesson
        that applies now, in full when it is new and as one line when it is
        not.

        A condition that raises must never take the shell down with it: the
        tutorial is optional and a bug in it is not worth a traceback in the
        middle of somebody's run.
        """
        if not self.tutorial_on:
            return
        c = self.console
        if self.run is None:
            self.tutorial_done.discard('run:skip')
        for lesson in tutorial.LESSONS:
            if lesson.key in self.tutorial_done:
                continue
            try:
                done = bool(lesson.done(self))
            except Exception:
                done = False
            if not done:
                continue
            if lesson.sticky:
                self.tutorial_done.add(lesson.key)
            elif lesson.key not in self.tutorial_told:
                continue
            else:
                self.tutorial_told.discard(lesson.key)
            if lesson.payoff and lesson.key in self.tutorial_told:
                c.blank()
                c.say(f'[ok]{c.caps.g("check")}[/] [dim]{lesson.payoff}[/]')
        if tutorial.LAST in self.tutorial_done:
            self.tutorial_on = False
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
        cur = tutorial.current(self)
        if cur is None:
            return
        if cur[0] != self.tutorial_shown:
            self.tutorial_show(full=True)
        elif not self._coach_said:
            self.tutorial_show(full=False)

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
        if state is not None and state.running and len(steps) > 1:
            # Script (D63, as the technique always said): one tick less
            # than the sum of its parts. Banked, so the first one-tick step
            # the script takes is the one that costs nothing.
            state.tick_bank += 1.0
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
                    # A script cannot answer a question, and letting its next
                    # step be the answer would be a script doing something
                    # nobody wrote. Drop it and say so.
                    if self.pending is not None:
                        self.cancel_question(say=False)
                        self.console.warn(f'[dim]{name}:[/] `{step.command}` '
                                          f'wanted an answer, which a script '
                                          f'cannot give. Run it by hand.')
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
        if self.pending is not None:
            return sorted(c for c in self.pending.choices if c.startswith(text))
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
                    if self.pending is not None:
                        self.cancel_question()
                        continue
                    self.console.say('[dim]Use `quit` to leave, or `jack out` '
                                     'if you are mid-run.[/]')
                    continue
                if line.strip():
                    self.typed.append(line.strip())
                self.execute(line)
                self._lifeline()
        finally:
            self.save_readline()
        return self.exit_code

    def _lifeline(self) -> None:
        """A fading reminder, for a brand-new runner who has not yet found
        that an empty line asks the game what to do (D118). The one thing a
        person who has never played a text game needs is to know the blank
        prompt is not a test they can fail. It stops the moment they use it,
        and fades after a few turns regardless, so it never becomes nag: not
        during a run, not mid-question, not while the tutorial is already
        holding their hand, and never once a run is behind them.
        """
        if (self.game is None or self.run is not None or self.pending is not None
                or self.tutorial_on):
            return
        if 'now' in self.seen or getattr(self.game.char, 'runs', 0) > 0:
            return
        if self.lifelines >= 4:
            return
        self.lifelines += 1
        self.console.say('[dim]Lost? Press Enter, or type `now`, for what to '
                         'do next.[/]')

    # ------------------------------------------------------------------
    # persistence helpers
    # ------------------------------------------------------------------

    def autosave(self) -> None:
        """Called on shift boundaries. Silent on success, loud on failure,
        because a save that is quietly not happening is the worst outcome."""
        if self.prologue is not None:
            return
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
