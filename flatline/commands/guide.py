"""The verbs that lead somebody in: `now`, the guided `new`, and `spend`.

D50. Three things a player who has never typed at a game needs and the shell
did not give them: an answer to an empty line, a way to make a character
without knowing flag syntax, and a sensible place to put the opening points
if they would rather play than plan.

None of it touches a number the ordinary verbs do not. `now` reads state and
prints the move the player was about to ask `job` for. The guided `new` ends
up calling exactly what `new <handle> --origin <key>` calls. `spend` spends
through `boost` and `train`, one point at a time, and shows the plan before
it does. A player who never types any of the three is playing the same game.
"""

from __future__ import annotations

from .. import save as save_mod
from ..content import attributes as attr_content
from ..content import districts
from ..content import origins
from ..content import threads as thread_content
from ..content import skills as skill_content
from ..rng import random_seed
from ..shell import REGISTRY, CommandError, command
from . import city as city_cmds


# --------------------------------------------------------------------------
# what now
# --------------------------------------------------------------------------


@command('now', 'What now: the next move, and the verbs that matter here.',
         group='info', aliases=('next', 'hint', 'menu'), bare=True,
         usage='now',
         detail='Enter on an empty line does the same thing. It reads the '
                'state and names one real thing to type next, with the '
                'reason, then the handful of verbs worth knowing where you '
                'are standing. While the coach is on it leads with the '
                'lesson (D183). It costs nothing and is always safe to ask. '
                '`job` is the whole brief; this is the line of it you were '
                'about to ask for.')
def cmd_now(sess, args) -> None:
    c = sess.console
    line, steps, also = what_now(sess)
    c.blank()
    c.rule('what now', role='accent2')
    # The tutorial's current step, first, while it is on (D182): the step
    # prints once when reached, and a screenful of scrollback later the one
    # place a newcomer looks for it is here.
    from ..content import tutorial
    cur = tutorial.current(sess) if sess.tutorial_on else None
    if cur is not None:
        key, instruction, why, topic, number = cur
        c.say(f'[accent2]coach[/]  [accent]{instruction}[/]',
              indent='  ', subsequent='         ')
        in_run = key.startswith('run:')
        # The reason, unless it was printed in full a moment ago: Enter
        # straight after a lesson repeats the instruction, not the paragraph.
        fresh = (key == sess.tutorial_shown
                 and sess._turns - sess.tutorial_shown_turn <= 2)
        if why and not fresh and not (in_run and f'why:{key}' in sess.tutorial_done):
            if in_run:
                sess.tutorial_done.add(f'why:{key}')
            c.say(f'[dim]{why}[/]', indent='         ', subsequent='         ')
        sess.tutorial_told.add('run' if in_run else key)
        sess.tutorial_shown = key
        sess._coach_said = True
    if line:
        c.say(f'[dim]{line}[/]', indent='  ', subsequent='  ')
    width = max((len(cmd) for cmd, _ in steps), default=0)
    for i, (cmd, why) in enumerate(steps):
        label = 'next' if i == 0 else 'then'
        pad = ' ' * (width - len(cmd))
        tail = f'  [dim]{why}[/]' if why else ''
        c.say(f'[dim]{label}[/]  [fg]{cmd}[/]{pad}{tail}', indent='  ',
              subsequent=' ' * (10 + width))
    if also:
        bullet = c.caps.g('bullet')
        c.say('[dim]also[/]  ' + f' [dim]{bullet}[/] '.join(
            f'[fg]{a}[/]' for a in also), indent='  ', subsequent='        ')
    # The words a newcomer meets here before anything explained them
    # (D187): once, on the first job, and where the rest of them live.
    if (sess.game is not None and sess.run is None
            and getattr(sess.game.char, 'runs', 0) == 0
            and 'words-hint' not in sess.seen):
        sess.seen.add('words-hint')
        c.say('[dim]words[/]  [dim]posture is how hard their doors are, a '
              'shift is the city\'s clock, and `help words` has the rest.[/]',
              indent='  ', subsequent='         ')
    # The record line you are closest to crossing (D163): one line, only
    # in the city, only when it is close. An achiever reads `record` for
    # this; everybody else finds out here that the city keeps count.
    if sess.game is not None and sess.run is None and not sess.game.over:
        near = _record_near(sess)
        if near:
            c.say(f'[dim]record[/]  [dim]{near}[/]', indent='  ', subsequent='  ')


@command('ambitions', 'The next things worth wanting.',
         group='info', aliases=('aims', 'goals'), contexts=('city',),
         usage='ambitions',
         detail='The ladder between one job and the whole story (D117): a '
                'handful of goals a runner would actually hold, from getting '
                'on your feet to finding out what Deepwater is. Each is met '
                'by playing, and the game says when. `now` points at the '
                'next one still open.')
def cmd_ambitions(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    from ..content import ambitions
    rows = ambitions.status(game)
    done = sum(1 for _, met in rows if met)
    c.header('Ambitions', f'{done} of {len(rows)}')
    for amb, met in rows:
        mark = '[ok]done[/]' if met else '[dim]open[/]'
        c.say(f'[{"ok" if met else "accent"}]{amb.title}[/]  {mark}',
              indent='  ')
        c.say(f'[dim]{amb.blurb}[/]', indent='    ', subsequent='    ')
        if not met:
            c.say(f'[dim]{c.caps.g("arrow")} {amb.hint}[/]', indent='    ',
                  subsequent='    ')
        c.blank()
    nxt = ambitions.next_open(game)
    if nxt is None:
        c.say('[dim]All of them. The city is out of names for what you are.'
              '[/]', indent='  ')


def _record_near(sess, meta: dict | None = None) -> str:
    """The unearned record line with the least left to cross, when that is
    a quarter of the target or less, as one dim line. Empty otherwise. The
    record is the profile's (D142), so the profile is what is read."""
    from .. import save as save_mod
    from ..content import record as record_content
    from ..world import record as record_world
    if meta is None:
        try:
            meta = save_mod.read_meta()
        except Exception:  # noqa: BLE001
            meta = dict(save_mod.META_DEFAULT)
    try:
        counts = record_world.counts(sess.game, meta)
    except Exception:  # noqa: BLE001
        return ''
    best = None
    for e in record_content.ENTRIES:
        have = int(counts.get(e.counter, 0))
        if have >= e.target or have <= 0:
            continue
        left = e.target - have
        if left > max(1, e.target // 4):
            continue
        if best is None or left < best[0]:
            best = (left, e)
    if best is None:
        return ''
    left, e = best
    return (f'{e.name}: {int(counts.get(e.counter, 0))} of {e.target}, {left} to go'
            + (f', and the city will call you {e.title}.' if e.title else '.'))



def what_now(sess) -> tuple[str, list[tuple[str, str]], list[str]]:
    """(situation, [(command, why)], [other verbs]) for the current state.

    Data rather than printed lines so the tutorial, the tests and anything
    else that wants "the next move" can read it without parsing a screen.
    The first step is always a real thing to type that moves the state; the
    rest is one move further, never a walkthrough.
    """
    game = sess.game
    if game is None:
        return _now_nobody(sess)
    if game.over:
        return _now_finished(sess)
    if sess.run is not None:
        return _now_run(sess)
    return _now_city(sess)


def _now_nobody(sess):
    living = [e for e in save_mod.roster() if not e.broken and not e.finished]
    if not living:
        return ('Nobody is loaded, and nobody has been made yet.',
                [('new', 'make a runner. It asks you three questions.'),
                 ('tutorial', 'a guided first run, once there is somebody '
                              'to run it')],
                ['help', 'career'])
    if len(living) == 1:
        e = living[0]
        who = (origins.BY_KEY[e.origin].name.lower()
               if e.origin in origins.BY_KEY else e.origin)
        return ('Nobody is loaded.',
                [(f'switch {e.handle}', f'carry on as {e.handle}, the '
                                        f'{who}, day {e.day}'),
                 ('new', 'or make somebody else; nobody is written over')],
                ['characters', 'help'])
    return ('Nobody is loaded.',
            [('characters', f'{len(living)} runners waiting; '
                            f'`switch <handle>` picks one up'),
             ('new', 'or make somebody else')],
            ['help', 'career'])


def _now_finished(sess):
    game = sess.game
    others = [e for e in save_mod.roster()
              if not e.broken and not e.finished and e.slot != sess.slot]
    if others:
        steps = [(f'switch {others[0].handle}',
                  f'carry on as {others[0].handle}'),
                 ('new', 'or make somebody else')]
    else:
        steps = [('new', 'make somebody else. The city has things to say '
                         'about the last one.')]
    return (f'{game.char.handle} {game.over}. The sheet and the log still '
            f'open; nothing else does.',
            steps, ['char', 'log', 'career', 'characters'])


def _now_run(sess):
    state = sess.run
    node = state.node
    brief = state.brief()
    line = (f'trace {state.trace_label()} {sess.console.caps.g("bullet")} '
            f'alert {state.alert} {sess.console.caps.g("bullet")} '
            f'tick {state.tick} {sess.console.caps.g("bullet")} '
            f'noise {node.noise} here')
    if brief.done:
        steps = [('jack out', 'the job is done. Everything from here is '
                              'spending time you have already been paid for')]
    elif brief.steps:
        steps = [(brief.steps[0], brief.progress)]
        steps += [(s, '') for s in brief.steps[1:2]]
    else:
        steps = [('job', 'nothing obvious from here; the brief says why')]
    return line, steps, ['scan', 'probe <host>', 'status', 'map', 'jack out']


def _now_city(sess):
    game = sess.game
    char = game.char
    city = game.city
    contract = city.current
    line = (f'{city.district.name}, {city.when}. '
            + (f'On the job: {contract.title}.' if contract
               else 'No contract accepted.'))
    steps = []
    if game.story.open_choice() is not None:
        # A scene is waiting on a decision. It outranks everything, because
        # it is the one thing in the city that does not move without you.
        steps.append(('choose', 'something is waiting on a decision from '
                                'you'))
    if contract is None:
        # Which job, not just the board (D64 c): the softest thing on it
        # that this kit can do, with the posture said out loud.
        all_steps = city_cmds.city_steps(game)
        steps.extend(all_steps[:2])
        # The job itself is never cut. `city_steps` puts shopping and
        # training in front of it, correctly, and two of those pushed the
        # one line that names a job off the end of this list. The
        # fallback then said "`board 1` reads the first one, `take 1`
        # accepts it" about a board whose first row was a corporate
        # network, which is exactly the run the recommendation exists to
        # keep a new player out of (D86).
        take = next(((cmd, why) for cmd, why in all_steps
                     if cmd.startswith('take ')), None)
        if take is not None and take not in steps:
            steps.append(take)
        if take is None:
            steps.append(('board', 'work on offer. `board <row>` reads one, '
                                   '`take <row>` accepts it'))
        else:
            cid = take[0].split()[1]
            steps.append(('board', f'or read the rest of it: `board {cid}` '
                                   f'reads the one above'))
        also = ['look', 'journal', 'world', 'errands', 'market', 'map', 'char',
                'help']
        if save_mod.read_meta().get('recorded'):
            # Once a line has landed, the screen that answers what is left
            # is worth a word here (D144): nothing but `char` pointed at it.
            also.insert(-1, 'record')
    else:
        all_steps = city_cmds.city_steps(game)
        steps.extend(all_steps[:2])
        # The step that actually goes (the walk, `jack in`, or the rest a
        # sever imposes) is never cut, for the same reason the job itself
        # is not (D91): `choose`, `unload` and `train` filled the two
        # lines and `now` stopped saying `jack in` on a job you held.
        goes = [(cmd, why) for cmd, why in all_steps
                if cmd.split()[0] in ('jack', 'walk', 'travel', 'rest',
                                      'drop')]
        # Not the jack in after the drop it contradicts (D101).
        if any(cmd == 'drop' for cmd, _ in steps):
            goes = [g for g in goes if g[0].split()[0] in ('rest',)]
        for go in goes[:2]:
            if go not in steps:
                steps.append(go)
        # The way in is a choice before it is a run (D122): a job held with no
        # approach set yet is a job you have only thought about one way.
        if not contract.approach and not any(cmd == 'approach'
                                             for cmd, _ in steps):
            steps.append(('approach', 'how you get in: breach it, talk your '
                                      'way in, or buy in'))
        also = ['job', 'approach', 'map', 'deck', 'market', 'errands', 'look',
                'journal', 'help']
    # `city_steps` opens with the same advice when the budget is unspent,
    # and a list that says `spend` twice reads as two different things to
    # do rather than one said twice.
    if (char.runs == 0 and (char.points or char.xp)
            and suggest(char, softest_posture(game))
            and not any(cmd == 'spend' for cmd, _ in steps)):
        steps.append(('spend', f'{char.points} attribute point'
                               f'{"s" if char.points != 1 else ""} and '
                               f'{char.xp} experience are unspent. This '
                               f'suggests a way; `boost` and `train` are '
                               f'yours'))
    # Daemonology's payoff is a whole automation layer that nobody finds
    # (D62): say so, once the rank that opens it is bought and until the
    # library has something in it.
    if char.skill('daemonology') >= 2 and not sess.scripts:
        steps.append(('script help', 'Daemonology 2 opened the script '
                                     'library and it is empty. `script '
                                     'example bailout` copies a working one'))
    # Systems the player owns and has never been pointed at (D79). One
    # nudge, when it first becomes true and actionable, on the pattern the
    # Daemonology one already proved: a whole layer of this game can go
    # unplayed for a career because nothing ever said it was there.
    # `spend` and `train <skill>` are the same four experience said twice.
    # At creation the plan is the better line, because it is the whole
    # budget in one word; afterwards the verb it would buy is, because it
    # is the reason to spend at all.
    nudges = _system_nudges(sess, char)
    train = any(n[0].startswith('train ') for n in nudges)
    if train and char.runs:
        steps = [s for s in steps if s[0] != 'spend']
    elif any(cmd == 'spend' for cmd, _ in steps):
        nudges = [n for n in nudges if not n[0].startswith('train ')]
    steps.extend(nudges)
    steps.extend(_story_nudge(sess))
    # The next rung on the ladder (D117), once they are actually climbing:
    # a runner with a job behind them always has a next thing worth wanting,
    # and `now` is where they should be able to see it.
    from ..content import ambitions
    nxt = ambitions.next_open(game)
    if nxt is not None and char.runs >= 1 and not any(
            cmd == 'aims' for cmd, _ in steps):
        steps.append(('aims', f'{nxt.title}: {nxt.hint}'))
    return line, steps, also


def _story_nudge(sess) -> list[tuple[str, str]]:
    """A reason to go somewhere, or to look round where you are (D86).

    Thirty-five threads and a hundred scenes, gated almost entirely on
    meeting people, and the advice never once said a person's name or a
    district's: a player following `now` from job to job could play a
    career without a single scene. One line, at most, after the work.
    Names the thread and the place, never the scene, like the journal.
    """
    game = sess.game
    story = game.story
    here = story.waiting_on_somebody_here(game)
    if here:
        thread = thread_content.BY_KEY[here[0]]
        return [('look', f'{thread.name} is waiting on somebody who is '
                         f'in this street at this hour')]
    away = [(t, w) for t, w in story.waiting_elsewhere(game)
            if not city_cmds._hunted_on_route(game, w)[0]]
    if away:
        thread_key, where = away[0]
        thread = thread_content.BY_KEY[thread_key]
        place = districts.BY_KEY[where]
        hops = game.city.shifts_to(where)
        return [(game.city.walk_to(where),
                 f'{thread.name} has more of it in {place.name}, '
                 f'{hops} shift{"s" if hops != 1 else ""} away, and it is '
                 f'waiting for you to be there')]
    # The first couple of runs, before the spine has found the player,
    # nothing above fires and `now` never hinted a story exists at all: a
    # player who lives in `now` could run a career and never learn the best
    # thing in the game is there (D114). One quiet line until it starts.
    if game.char.runs < 2 and not story.active_threads():
        return [('journal', 'the city has a story, and it starts to find you '
                            'once you have a couple of runs behind you')]
    return []


def _system_nudges(sess, char) -> list[tuple[str, str]]:
    """At most one, and only when it is both true and worth doing now."""
    game = sess.game
    out: list[tuple[str, str]] = []

    # Experience sitting in the bank that would buy a verb.
    ready = [k for k in skill_content.SKILL_KEYS
             if any(t.rank == char.skill(k) + 1
                    for t in skill_content.BY_KEY[k].techniques)
             and char.xp >= skill_content.RANK_COST.get(char.skill(k) + 1, 999)]
    if ready and char.runs:
        name = skill_content.BY_KEY[ready[0]]
        tech = next(t for t in name.techniques if t.rank == char.skill(ready[0]) + 1)
        out.append((f'train {ready[0]}',
                    f'{char.xp} experience will buy {tech.name}, which is a '
                    f'verb you do not have: {tech.summary.lower().rstrip(".")}'
                    f'. `train` lists all fifteen'))
        return out

    # A fighter's living (D131): somebody with a rank in Violence or a
    # weapon in hand, somewhere rough enough that muscle work is on offer,
    # and nothing being carried.
    from ..world import street as street_world
    from ..world import fight as fight_mod
    fighter = char.skill('violence') >= 1 or bool(fight_mod.weapon_of(char))
    if (fighter and not game.city.errand
            and street_world.rough(game) >= street_world.MUSCLE_AT
            and any(j['kind'] == 'muscle' for j in street_world.errands_here(game))):
        out.append(('errands',
                    'muscle work is on offer here: stand in a doorway for '
                    'somebody and be paid if you are the one still standing. '
                    'It is how a fighter eats between runs'))
        return out
    if (fighter and fight_mod.armour_of(char) == 0 and char.credits >= 600
            and any(s in game.city.district.services for s in ('market', 'fence'))):
        out.append(('market armour',
                    'you fight with nothing between you and the hit. A '
                    'ballistic jacket is six hundred and takes a point off '
                    'every one that reaches you'))
        return out
    # The pit, where the pit is, to somebody who could stand in it (D137).
    from ..content import pit as pit_content
    if (fighter and game.city.where == pit_content.WHERE
            and pit_content.AT in game.city.district.services
            and game.city.phase == 'night'
            and not game.city.pit.get('rank')):
        out.append(('pit',
                    'there is a floor with tape on it under the fence here, '
                    'and a wall with names, and the house pays. Nobody dies '
                    'in the pit, whatever rung: it is the one fight in the '
                    'city that is only ever a fight'))
        return out
    # The other half of the game, to somebody the street keeps stopping who
    # has never once had anything in their hand (D137). The fighter nudges
    # above only ever fire for a player who has already committed, so a
    # runner could be stopped in a doorway five nights running and never be
    # told that any of this existed.
    stopped = sum(1 for f in game.story.flags if f.startswith('street:'))
    if (not fighter and fight_mod.armour_of(char) == 0 and stopped >= 2
            and char.credits >= 400):
        word = 'twice' if stopped == 2 else f'{stopped} times'
        out.append(('help street',
                    f'the street has stopped you {word} and you have never '
                    f'had anything in your hand or anything between you and '
                    f'the hit. It can be fought, and it never has to be: a '
                    f'jacket is a few hundred, a blade is less'))
        return out
    # Chrome, once there is money for it and nothing in you yet. The game
    # is half about this trade and a career can pass without meeting it.
    # Eleven of the twelve origins ship with a piece already in, so "has
    # no chrome" is a condition that never fires. Still carrying only what
    # the origin gave them, with money in hand, is the real signal.
    if (len(char.installed) <= 1 and char.credits >= 1600 and char.runs >= 2
            and 'clinic' in game.city.district.services):
        out.append(('clinic',
                    'you are still running on what you started with. '
                    'Chrome is the other half of a build and it is bought '
                    'with Dissonance, which never comes back down: the '
                    'clinic prices both before it takes anything'))
        return out

    # A rival who has made their mind up, and a player who has never used
    # any of the three verbs that exist for them.
    decided = [r for r in game.city.rivals if getattr(r, 'bond', '')]
    if decided and not game.city.hired and char.runs >= 3:
        who = decided[0]
        out.append((f'who {who.name.lower()}',
                    f'{who.name} has decided something about you. They can '
                    f'be hired for a cut, asked for a favour, or sold out'))
    return out



# --------------------------------------------------------------------------
# previously (D62)
# --------------------------------------------------------------------------


def previously(sess) -> None:
    """Five lines for somebody sitting back down with a character.

    Where and when, the job, who is hottest on you, what is open and what
    is waiting, and the last thing the wire said. Printed when a character
    is continued, switched to or restored, because a save is a place you
    left and nobody remembers a place they left a week ago well enough to
    stand back up in it.
    """
    game, c = sess.game, sess.console
    if game is None:
        return
    from ..content import factions as fac_content
    city, char = game.city, game.char
    rows = [('where', f'{city.district.name}, {city.when}')]
    contract = city.current
    if contract is not None:
        hops = city.shifts_to(contract.district)
        rows.append(('job', f'[accent]{contract.title}[/] [dim]against '
                            f'{contract.target_data.short}, '
                            + ('here' if not hops else
                               f'{hops} shift{"s" if hops != 1 else ""} away')
                            + '[/]'))
    else:
        rows.append(('job', '[dim]nothing accepted[/]'))
    hot, heat = game.alias.hottest
    if hot and heat > 0:
        rows.append(('heat', f'[heat]{fac_content.BY_KEY[hot].short} '
                             f'{int(heat)}[/]'))
    open_threads = len(game.story.reached)
    waiting = len(game.story.pending)
    story_line = f'{open_threads} thread{"s" if open_threads != 1 else ""} open'
    if waiting:
        story_line += (f', [warn]{waiting} waiting on a decision[/] '
                       f'[dim](`choose`)[/]')
    rows.append(('story', story_line))
    if game.history:
        from .run import run_ending
        h = game.history[-1]
        against = (fac_content.BY_KEY[h['faction']].short
                   if h.get('faction') in fac_content.BY_KEY else 'somebody')
        rows.append(('last run', f'[accent]{h.get("title") or "no contract"}'
                                 f'[/] [dim]against {against},[/] '
                                 f'{run_ending(h)}'))
    if city.news:
        last = city.news[-1]
        rows.append(('last', last))
    rows.append(('money', f'[credit]{char.credits:,}c[/] [dim]'
                          f'{char.runs} run{"s" if char.runs != 1 else ""} '
                          f'so far[/]'))
    c.blank()
    c.rule('previously', role='accent2')
    c.kv(rows)


# --------------------------------------------------------------------------
# the guided `new`
# --------------------------------------------------------------------------

#: What the prompt says while each question waits.
ASK_ORIGIN = f'origin (1-{len(origins.ORIGINS)}, or a name)? '
ASK_HANDLE = 'handle? '
ASK_SPEND = 'spend (1 or 2)? '
#: What backing out of any of them says.
NOT_MADE = 'No runner made. `new` when you are ready.'


@command('begin', 'Your first job, right now. The way in.',
         group='character', bare=True, contexts=('city',), usage='begin',
         detail='The cold open (D115, a real run since D186): a short '
                'first heist on a borrowed deck, with a voice in your ear '
                'saying the next thing to type, played with the game\'s own '
                'verbs, dice and countermeasures before it asks you to build '
                'anybody. The crack can fail and the trace can fill, and '
                'being cut loose is a scene rather than an ending; what '
                'happens reaches the runner you make afterwards. `skip` '
                'inside it goes straight to `new`; `tutorial` is the coach, '
                'which turns itself on for your first runner anyway.')
def cmd_begin(sess, args) -> None:
    if sess.game is not None:
        raise CommandError('you already have somebody. `new` makes another, '
                           '`tutorial` walks a run.')
    from .. import prologue
    prologue.play(sess)


def start_creation(sess, handle: str | None = None) -> None:
    """`new` with nothing after it: a conversation rather than a form.

    `new <handle>` with no origin lands here too, with the handle already
    decided, because somebody who typed a name and nothing else has answered
    one of the three questions and should only be asked the other two.
    """
    if sess.run is not None:
        raise CommandError('finish the run first.')
    if handle is not None:
        problem = handle_problem(handle)
        if problem:
            raise CommandError(problem)
    # The first runner on this profile gets the tutorial without asking
    # (D182). Testers who were told `begin` teaches itself found that it
    # taught the prologue and then stopped; nothing explained the sheet,
    # the screen, or the colours, and the tutorial that does was one word
    # nobody knew to type.
    sess.teach = not [e for e in save_mod.roster() if not e.broken]
    origin_table(sess)
    _ask_origin(sess, handle)


def article(name: str) -> str:
    """`a` or `an`, for the one sentence that says what the origin is."""
    return 'an' if name[:1].lower() in 'aeiou' else 'a'


def origin_table(sess) -> None:
    """The twelve origins, two lines each, which is the whole list on one screen.

    The long form, with passive, signature and story, is `read <n>` from the
    question or `new --long` from the prompt. Somebody choosing between ten
    things needs the ten things side by side first and one of them in full
    second; the old order gave them eleven screens and then a flag.
    """
    c = sess.console
    c.header('A new runner', f'{len(origins.ORIGINS)} origins')
    c.say(f'[dim]An origin sets where you start, never where you can go. '
          f'Pick one by number or by name. Every attribute starts at '
          f'{origins.BASE_ATTR}, and an origin moves a few; the numbers on '
          f'each row are what you start with, and they are the same numbers '
          f'the sheet shows. The five attributes:[/]')
    for a in attr_content.ATTRIBUTES:
        c.say(f'[warn]{a.short}[/] [accent]{a.name}[/]'
              f'{" " * (7 - len(a.name))} [dim]{a.gloss}[/]',
              indent='  ', subsequent='              ')
    c.blank()
    name_w = max(len(o.name) for o in origins.ORIGINS)
    key_w = max(len(o.key) for o in origins.ORIGINS)

    def row(i, o, tag=''):
        # The moved ones lit, the rest dim: the shape of the origin reads
        # at a glance and the numbers are the sheet's own (D185).
        shape = ' '.join(f'[accent]{short} {v}[/]' if moved
                         else f'[dim]{short} {v}[/]'
                         for short, _, v, moved in origins.starting_attrs(o))
        c.raw(f'  [accent]{i:>2}[/]  [accent][bold]{o.name}[/][/]'
              f'{" " * (name_w - len(o.name))}  [dim]{o.key}[/]'
              f'{" " * (key_w - len(o.key))}  [credit]{o.credits:>6,}c[/]'
              f'  {shape}')
        blurb = f'[accent2]{tag}.[/] [dim]{o.blurb}[/]' if tag else f'[dim]{o.blurb}[/]'
        c.say(blurb, indent='      ', subsequent='      ')

    # Twelve rows is a wall on a first screen (D187): three first, framed
    # by how they play, and the numbers stay the numbers of the full list.
    numbered = {o.key: i for i, o in enumerate(origins.ORIGINS, 1)}
    c.say('[accent]Three for a first runner[/]')
    for key, tag in origins.FIRST_RUNNER:
        row(numbered[key], origins.BY_KEY[key], tag)
    c.blank()
    c.say('[dim]And nine more, each with something nobody else can do:[/]')
    first_keys = {k for k, _ in origins.FIRST_RUNNER}
    for i, o in enumerate(origins.ORIGINS, 1):
        if o.key not in first_keys:
            row(i, o)
    c.blank()
    c.say('[dim]`read 2` reads one in full before you choose, `read all` '
          'reads every one, `random` lets the city pick. Enter alone '
          'stops.[/]')


def _ask_origin(sess, handle: str | None = None) -> None:
    sess.ask(ASK_ORIGIN, lambda s, t: _on_origin(s, t, handle),
             on_cancel=NOT_MADE,
             choices=tuple(origins.ORIGIN_KEYS) + ('read', 'random'))


def _on_origin(sess, text: str, handle: str | None = None) -> None:
    c = sess.console
    low = text.lower().strip()
    words = low.split()
    if words and words[0] in ('read', 'more', 'about', 'show', 'tell'):
        what = ' '.join(words[1:])
        if what in ('all', 'everything', ''):
            city_cmds.list_origins(sess)
        else:
            origin = city_cmds.resolve_origin(what)
            if origin is None:
                c.err(f'{what!r} is not one of the {len(origins.ORIGINS)}. '
                      f'A number, or a name.')
            else:
                city_cmds.show_origin(sess, origin)
        _ask_origin(sess, handle)
        return
    if low in ('help', '?', 'list', 'again'):
        origin_table(sess)
        _ask_origin(sess, handle)
        return
    if low in ('random', 'any', 'surprise me', 'you pick', 'dealer'):
        # Not a game stream: nothing about the world has been decided yet,
        # and the creation seed is already drawn from the same place.
        origin = origins.ORIGINS[random_seed() % len(origins.ORIGINS)]
    else:
        origin = city_cmds.resolve_origin(low)
    if origin is None:
        c.err(f'{text!r} is not one of the {len(origins.ORIGINS)}. A number '
              f'from 1 to {len(origins.ORIGINS)}, or a name. `read 3` to '
              f'read one first, Enter alone to stop.')
        _ask_origin(sess, handle)
        return
    c.blank()
    c.say(f'[accent]{origin.name}.[/] [dim]{origin.blurb}[/]')
    if handle is not None:
        city_cmds.create_character(sess, handle, origin.key, random_seed())
        offer_spend(sess)
        return
    c.say('[dim]What does the city call them? One word is best: it is how '
          'you pick them up again.[/]')
    _ask_handle(sess, origin.key)


def _ask_handle(sess, origin_key: str) -> None:
    sess.ask(ASK_HANDLE, lambda s, t: _on_handle(s, t, origin_key),
             on_cancel=NOT_MADE)


def handle_problem(handle: str) -> str:
    """Why this cannot be a handle, or '' when it can.

    The rules exist because a handle is an address: `switch <handle>` has to
    find exactly one person by it, a row number must never be mistaken for
    one, and the shell must never have to guess whether `map` meant the verb
    or the runner.
    """
    h = handle.strip()
    if not h:
        return 'a handle needs at least one letter in it.'
    if len(h) > 24:
        return 'too long to be a handle. Twenty-four characters at most.'
    if len(h.split()) > 1:
        return 'one word. Join it with a dash if it wants two.'
    if h.isdigit():
        return ('all digits would be read as a row number by `switch`. Put '
                'a letter in it.')
    if REGISTRY.lookup(h.lower()) is not None:
        return (f'`{h.lower()}` is a command, and the shell would never know '
                f'which you meant. Another name.')
    if save_mod.find(h):
        return (f'there is already a {h} on the roster. Another name, or '
                f'`delete {h}` first.')
    return ''


def _on_handle(sess, text: str, origin_key: str) -> None:
    c = sess.console
    if text.lower() in ('help', '?'):
        c.say('[dim]A handle is the name the roster files them under: one '
              'word, no spaces, not a command. What the city calls them is '
              'separate and is drawn for you.[/]')
        _ask_handle(sess, origin_key)
        return
    problem = handle_problem(text)
    if problem:
        c.err(problem)
        _ask_handle(sess, origin_key)
        return
    city_cmds.create_character(sess, text.strip(), origin_key, random_seed())
    offer_spend(sess)


def offer_spend(sess) -> None:
    """The third question: where the opening points go."""
    c = sess.console
    char = sess.game.char
    plan = suggest(char, softest_posture(sess.game))
    if not plan:
        _close(sess)
        return
    c.blank()
    c.rule('to spend', role='accent2')
    who = char.origin_data.name.lower()
    c.say(f'{char.points} attribute point{"s" if char.points != 1 else ""} '
          f'and {char.xp} experience. {article(who).capitalize()} {who} '
          f'usually puts them here:')
    print_plan(c, plan, char)
    c.blank()
    c.say('[fg]1[/]  [dim]spend them this way now[/]', indent='  ')
    c.say('[fg]2[/]  [dim]keep them. `boost <attribute>` and `train <skill>` '
          'spend them whenever you like, and `spend` suggests this again.[/]',
          indent='  ', subsequent='     ')
    sess.ask(ASK_SPEND, _on_spend,
             on_cancel='Kept. `char` shows what is unspent, `spend` suggests '
                       'this again.',
             choices=('1', '2', 'yes', 'no'))


def _on_spend(sess, text: str) -> None:
    c = sess.console
    low = text.lower().strip()
    if low in ('1', 'yes', 'y', 'spend', 'do it', 'go'):
        apply_plan(sess, suggest(sess.game.char, softest_posture(sess.game)))
    elif low in ('2', 'no', 'n', 'keep', 'later', 'myself'):
        c.say('[dim]Kept. `char` shows what is unspent; `boost` and `train` '
              'spend it one point at a time, and `spend` suggests this '
              'again.[/]')
    else:
        c.err('1 to spend them this way, 2 to keep them. Enter alone keeps '
              'them.')
        sess.ask(ASK_SPEND, _on_spend,
                 on_cancel='Kept. `char` shows what is unspent.',
                 choices=('1', '2', 'yes', 'no'))
        return
    _close(sess)


def _close(sess) -> None:
    c = sess.console
    # What last night left (D186): said once, here, where the runner it
    # happened to now exists.
    from .. import prologue as prologue_mod
    carried = prologue_mod.carry(sess)
    if carried:
        c.blank()
        c.rule('from last night', role='accent2')
        for line in carried:
            c.say(f'[dim]{line}[/]')
    c.blank()
    c.say('[dim]That is a runner. `char` is the sheet, `self` is the face, '
          '`trait` is who they are. Enter on an empty line, at any point, '
          'says what to do next:[/]')
    if sess.teach and not sess.tutorial_on:
        sess.teach = False
        c.blank()
        c.say('[accent]The coach is on[/][dim], because this is your first '
              'runner here. It reads where you are standing and says the '
              'next thing to type, and why. Enter on an empty line repeats '
              'it; `tutorial stop` turns it off, `tutorial` brings it '
              'back.[/]')
        sess.tutorial_on = True
        # The first lesson is the loop, and its instruction is to press
        # Enter; printing the advice under it would answer the lesson for
        # them.
        sess.tutorial_advance()
        return
    sess.what_now()


# --------------------------------------------------------------------------
# spend
# --------------------------------------------------------------------------


@command('spend', 'Spend what is unspent the way your origin usually would.',
         contexts=('city',), group='character', usage='spend [--go]',
         detail='Reads the origin\'s shape and proposes where the unspent '
                'attribute points and experience would usually go: the '
                'attributes the origin is built on, depth in the skills it '
                'starts with, then breadth across the ones those attributes '
                'govern. It shows the plan and asks before spending; `--go` '
                'skips the asking. It is never better than choosing '
                'yourself, and `boost` and `train` spend the same points one '
                'at a time.')
def cmd_spend(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    char = game.char
    if not (char.points or char.xp):
        raise CommandError('nothing unspent. Experience arrives at the end '
                           'of a run.')
    plan = suggest(char, softest_posture(sess.game))
    if not plan:
        raise CommandError('nothing the shape suggests. `boost` and `train` '
                           'take it from here.')
    c.header('To spend', f'{char.points} points, {char.xp} experience')
    who = char.origin_data.name.lower()
    c.say(f'[dim]{article(who).capitalize()} {who} usually puts them '
          f'here:[/]')
    print_plan(c, plan, char)
    if args.has('go'):
        c.blank()
        apply_plan(sess, plan)
        return
    c.blank()
    sess.ask('spend it this way (yes or no)? ', _on_spend_verb,
             on_cancel='Kept.', choices=('yes', 'no'))


def _on_spend_verb(sess, text: str) -> None:
    low = text.lower().strip()
    if low in ('yes', 'y', '1', 'go', 'do it'):
        apply_plan(sess, suggest(sess.game.char, softest_posture(sess.game)))
    elif low in ('no', 'n', '2', 'keep'):
        sess.console.say('[dim]Kept.[/]')
    else:
        sess.console.err('yes or no.')
        sess.ask('spend it this way (yes or no)? ', _on_spend_verb,
                 on_cancel='Kept.', choices=('yes', 'no'))


#: How many skills beyond the origin's own the suggestion will open. Breadth
#: past this buys rank ones that unlock nothing; the points go deeper instead.
BREADTH = 3


def softest_posture(game) -> int | None:
    """The softest live posture on the board, for the plan to read."""
    if game is None:
        return None
    live = [int(c.posture) for c in game.city.board
            if not c.expired(game.city.shift)]
    return min(live) if live else None


def _weights(origin) -> dict[str, int]:
    """How much the origin is about each attribute.

    A positive delta counts for itself plus one, a zero counts for one, a
    negative counts for nothing: the suggestion leans into the shape rather
    than sanding it flat, because the shape is the reason the origin was
    picked.
    """
    out = {}
    for k in attr_content.ATTR_KEYS:
        d = origin.attrs.get(k, 0)
        out[k] = d + 1 if d > 0 else (1 if d == 0 else 0)
    return out


def suggest(char, board_posture: int | None = None) -> list[tuple[str, str]]:
    """Where the unspent points would usually go, as (verb, key) steps.

    Pure: the same character gets the same plan, and nothing is changed by
    asking. Every step is legal at the moment it would be taken, which
    `test.py` checks for every origin, and no attribute is pushed to its
    ceiling: a maxed attribute on day one makes the first ten hours a
    straight line, and that is a choice a player should make on purpose.
    """
    origin = char.origin_data
    weights = _weights(origin)
    plan: list[tuple[str, str]] = []

    # Attributes, proportionally to the shape, highest averages first.
    attrs = dict(char.base_attrs)
    given = {k: 0 for k in weights}
    for _ in range(char.points):
        cands = [k for k in attr_content.ATTR_KEYS
                 if weights[k] > 0 and attrs[k] < attr_content.ATTR_MAX - 1]
        if not cands:
            break
        key = max(cands, key=lambda k: (weights[k] / (given[k] + 1),
                                        weights[k],
                                        -attr_content.ATTR_KEYS.index(k)))
        given[key] += 1
        attrs[key] += 1
        plan.append(('boost', key))

    # Experience. Depth first in the skills the origin starts with, to the
    # rank that changes what you can type; then breadth across what the
    # strong attributes govern; then whatever is left goes deeper, cheapest
    # rank first.
    xp = char.xp
    ranks = dict(char.base_skills)

    def price(key: str) -> int | None:
        nxt = ranks[key] + 1
        return skill_content.RANK_COST.get(nxt) if nxt <= skill_content.MAX_RANK else None

    def train(key: str) -> None:
        nonlocal xp
        xp -= price(key)
        ranks[key] += 1
        plan.append(('train', key))

    # The rank that drives the breaker in the kit (D87). A program runs at
    # its rating only up to the skill plus two, so a protege's rating-three
    # Sable on Intrusion 0 is a rating-two program that costs twice the
    # memory, and the plan put seventeen experience into five other skills
    # before anybody said so. Every door in the game reads this number.
    from ..content import programs as program_content
    breaker = program_content.best(list(char.deck.loaded) + list(char.library),
                                   'breaker')
    if breaker is not None:
        # And at least one rank of it whatever the breaker (D91): a
        # courier at Intrusion 0 and Logic 1 read every row of the board
        # as shut, and the plan had put the twelve experience into three
        # street skills.
        want = max(1, breaker.rating - program_content.HELD_ABOVE)
        while (ranks['intrusion'] < want and price('intrusion') is not None
               and price('intrusion') <= xp):
            train('intrusion')
        # And while the softest thing on the board reads shut (D100): the
        # plan bought Warfare, Signal, Psyche, Sabotage, Streetcraft,
        # Cryptography and Daemonology across thirteen nights whose every
        # failure printed "1 tier short" or a shut door, and `now` said
        # Intrusion after each one.
        if board_posture is not None:
            from ..world import contracts as contract_world
            while (price('intrusion') is not None and price('intrusion') <= xp
                   and contract_world.door_odds(char, board_posture,
                                                rank=ranks['intrusion'])
                   < contract_world.DOOR_TIGHT):
                train('intrusion')


    for key in origin.skills:
        while ranks[key] < 2 and price(key) is not None and price(key) <= xp:
            train(key)

    governed = [s for s in skill_content.SKILLS
                if s.key in origin.skills or weights.get(s.attr, 0) > 1]
    opened = {k for k, r in ranks.items() if r > 0}
    room = len(origin.skills) + BREADTH
    for s in sorted((s for s in governed if ranks[s.key] == 0),
                    key=lambda s: (-weights.get(s.attr, 0),
                                   skill_content.SKILLS.index(s))):
        if len(opened) >= room:
            break
        if price(s.key) is not None and price(s.key) <= xp:
            train(s.key)
            opened.add(s.key)

    while True:
        options = [s for s in governed
                   if ranks[s.key] > 0 and price(s.key) is not None
                   and price(s.key) <= xp]
        if not options:
            break
        best = min(options, key=lambda s: (ranks[s.key],
                                           -weights.get(s.attr, 0),
                                           skill_content.SKILLS.index(s)))
        train(best.key)

    # And whatever is still affordable anywhere, cheapest first. Without
    # this a character with four experience and nothing cheap inside the
    # origin's shape got an empty plan, `spend` refused it, and `now` went
    # on recommending `spend`: an advice loop with a refusal at the end of
    # it. A plan that reaches outside the shape is worse advice than one
    # inside it and better advice than none.
    while True:
        options = [s for s in skill_content.SKILLS
                   if price(s.key) is not None and price(s.key) <= xp]
        if not options:
            break
        best = min(options, key=lambda s: (price(s.key), ranks[s.key],
                                           -weights.get(s.attr, 0),
                                           skill_content.SKILLS.index(s)))
        train(best.key)
    return plan


def describe(plan, char, arrow: str = '->') -> tuple[list, list]:
    """The plan as two grids of (name, change and reason) rows (D185):
    every attribute, moved or not, and then the skills, each with the
    attribute it checks against. One grid mixed three attributes and four
    skills and the author read Warfare as a stat and asked where Logic
    had gone."""
    attrs: list[tuple[str, str]] = []
    skills_out: list[tuple[str, str]] = []
    boosts: dict[str, int] = {}
    for verb, key in plan:
        if verb == 'boost':
            boosts[key] = boosts.get(key, 0) + 1
    ranks = dict(char.base_skills)
    trained: dict[str, tuple[int, int, list]] = {}
    for verb, key in plan:
        if verb != 'train':
            continue
        start = trained.get(key, (ranks[key], ranks[key], []))[0]
        ranks[key] += 1
        techs = trained.get(key, (0, 0, []))[2]
        tech = skill_content.BY_KEY[key].technique_at(ranks[key])
        if tech:
            techs.append(tech)
        trained[key] = (start, ranks[key], techs)
    for a in attr_content.ATTRIBUTES:
        have = char.base_attrs[a.key]
        n = boosts.get(a.key, 0)
        # Padded on the plain text so the glosses line up whether or not
        # the number moved.
        plain_len = len(f'{have}{arrow}{have + n}') if n else len(str(have))
        pad = ' ' * max(0, 5 - plain_len)
        change = (f'{have}[dim]{arrow}[/][accent]{have + n}[/]' if n
                  else f'{have}')
        attrs.append((a.name, f'{change}{pad}  [dim]{a.gloss}[/]'))
    for key, (start, end, techs) in trained.items():
        s = skill_content.BY_KEY[key]
        why = s.summary.rstrip('.')
        if techs:
            why += '. ' + '; '.join(
                f'{t.name} at rank {t.rank}: {t.summary.rstrip(".").lower()}'
                for t in techs)
        governs = attr_content.BY_KEY[s.attr].name
        pad = ' ' * max(0, 5 - len(f'{start}{arrow}{end}'))
        skills_out.append((s.name, f'{start}[dim]{arrow}[/][accent]{end}[/]'
                                   f'{pad}  [dim]{why}. Checks against '
                                   f'{governs}.[/]'))
    return attrs, skills_out


def print_plan(c, plan, char) -> None:
    """The two grids, with the line between them that says what a skill
    is, because the spend screen is the first place a new player meets
    one."""
    attrs, skills_out = describe(plan, char, c.caps.g('arrow'))
    points = sum(1 for verb, _ in plan if verb == 'boost')
    c.blank()
    c.say(f'[accent]Attributes[/] [dim]({points} of {char.points} point'
          f'{"s" if char.points != 1 else ""}): the five numbers every '
          f'check reads. Unmoved ones stay as they are.[/]')
    c.kv(attrs, role='accent')
    if skills_out:
        c.blank()
        c.say(f'[accent]Skills[/] [dim]({char.xp} experience): a skill is '
              f'a trade, checked against one attribute. Ranks 2 and 4 each '
              f'unlock a technique, which is a new thing to type.[/]')
        c.kv(skills_out, role='accent')


def apply_plan(sess, plan) -> None:
    """Spend it, through the same calls `boost` and `train` make."""
    c = sess.console
    char = sess.game.char
    boosted: dict[str, tuple[int, int]] = {}
    trained: dict[str, tuple[int, int]] = {}
    unlocked: list = []
    for verb, key in plan:
        if verb == 'boost':
            before = char.base_attrs[key]
            after = char.boost(key)
            boosted[key] = (boosted.get(key, (before, after))[0], after)
        else:
            before = char.base_skills[key]
            tech = char.train(key)
            trained[key] = (trained.get(key, (before, 0))[0],
                            char.base_skills[key])
            if tech:
                unlocked.append(tech)
    arrow = c.caps.g('arrow')
    if boosted:
        c.ok('Attributes: ' + ', '.join(f'{attr_content.BY_KEY[k].name} {a}[dim]{arrow}[/]{b}'
                       for k, (a, b) in boosted.items())
             + f'. [dim]{char.points} point'
               f'{"s" if char.points != 1 else ""} left.[/]')
    if trained:
        c.ok('Skills: ' + ', '.join(f'{skill_content.BY_KEY[k].name} {b}'
                       for k, (a, b) in trained.items())
             + f'. [dim]{char.xp} experience left.[/]')
    for tech in unlocked:
        c.say(f'[accent]{tech.name} unlocked.[/] '
              f'[dim]{tech.verb or "no new verb: it changes what happens"}: '
              f'{tech.summary}[/]', indent='  ', subsequent='  ')
    sess.autosave()
