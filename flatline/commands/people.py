"""Commands for the people in this city, and the threads they carry.

`look` is the discovery verb: it is the only way to find out who is standing
in the district you are in. Everything else follows from having met somebody.

Story scenes surface through `_check_story`, which runs whenever the world
moves. It never interrupts a run: being handed a scene about a dying friend
halfway through a vault would be the wrong moment for both of them.
"""

from __future__ import annotations

from ..content import factions
from ..content import npcs as npc_content
from ..content import threads as thread_content
from ..content import shifts
from ..shell import CommandError, command
from ..world import story as story_mod


@command('look', 'Look at where you are.',
         group='city', aliases=('around',), usage='look',
         detail='In the city, this is how you find the people in it: who you '
                'run into depends on where you are, what you can get into '
                'there, and in some cases on what you have already done. '
                'Inside a run it shows you the node you are standing in.')
def cmd_look(sess, args) -> None:
    if sess.run is not None:
        # One verb that always means "look at where I am".
        from .run import cmd_here
        cmd_here(sess, args)
        return
    game, c = sess.require_game(), sess.console
    here = story_mod.present(game, game.story)
    district = game.city.district
    when = shifts.phase(game.city.phase)

    c.header(district.name, game.city.when)
    # Where you are, not just who is standing in it. `travel` prints the
    # district once on arrival and then never again, so a player who has been
    # somewhere for six shifts had nothing to look at.
    c.say(f'[dim]{district.blurb}[/]')
    c.blank()
    c.say(when.scene)

    # What the clock is doing to you, in the two places it is doing it.
    parts = []
    if when.danger != 1.0:
        parts.append(f'street {"busier" if when.danger > 1 else "quieter"}')
    if when.trace != 1.0:
        parts.append(f'trace {"faster" if when.trace > 1 else "slower"} in '
                     f'there')
    if when.price != 1.0:
        parts.append(f'prices up {(when.price - 1) * 100:.0f}%')
    if parts:
        c.blank()
        c.info(f'{", ".join(parts)}. [dim]{when.why}[/]')

    c.blank()
    if not here:
        c.say('[dim]Nobody here is interested in you, which in this district '
              'is a mercy.[/]')
        return
    c.rule(f'{len(here)} worth talking to')

    for npc in here:
        first = game.story.meet(npc.key)
        c.blank()
        if first:
            c.raw(f'[accent2][bold]{npc.name}[/][/]  [dim]{npc.epithet}[/]')
            c.say(npc.first)
        else:
            c.raw(f'[accent]{npc.name}[/]  [dim]{npc.epithet}[/]')
    c.blank()
    c.say('[dim]`talk <name>` to say something. `ask <name> <topic>` if you '
          'want something specific.[/]')
    _check_story(sess)


@command('talk', 'Say something to somebody.',
         group='city', contexts=('city',), usage='talk <name>')
def cmd_talk(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    npc = _find(sess, args.rest())
    line = game.rng('events').pick(npc.lines)
    c.blank()
    c.raw(f'[accent]{npc.name}[/]  [dim]{npc.epithet}[/]')
    c.blank()
    c.say(line)
    if npc.topics:
        c.blank()
        c.say('[dim]They will talk about: '
              + ', '.join(sorted(npc.topics)) + '. `ask '
              + npc.key + ' <topic>`.[/]')
    _check_story(sess)


def ask_npc(sess, args) -> bool:
    """Try to answer `ask` as a question to one of the city's people.

    Returns False if the name is not somebody, so the caller can fall through
    to the rival-favour meaning of the verb. One word, two meanings, and the
    fiction absorbs it: you ask a person about a thing and you ask a colleague
    for a thing.
    """
    game, c = sess.require_game(), sess.console
    if len(args) < 2:
        return False
    npc = _match(args[0])
    if npc is None:
        return False
    if npc.key not in game.story.met:
        raise CommandError(f'you have not met {npc.name}. `look` around '
                           f'where they are.')

    topic = args[1].lower()
    match = next((k for k in npc.topics if k.startswith(topic)), None)
    if match is None:
        raise CommandError(f'{npc.name} will talk about: '
                           + ', '.join(sorted(npc.topics)))
    c.blank()
    c.raw(f'[accent]{npc.name}[/] [dim]on {match}[/]')
    c.blank()
    c.say(npc.topics[match])
    game.story.flags.add(f'asked:{npc.key}:{match}')
    _check_story(sess)
    return True


@command('who is', 'What you know about somebody you have met.',
         group='info', contexts=('city',), usage='who is <name>')
def cmd_who_is(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    npc = _find(sess, args.rest())
    c.header(npc.name, npc.epithet)
    c.say(npc.manner)
    where = npc.where or 'moves around'
    from ..content import districts
    if npc.where:
        where = districts.BY_KEY[npc.where].name
        if npc.at:
            where += f', where there is a {npc.at}'
    elif npc.at:
        where = f'anywhere with a {npc.at}'
    c.blank()
    c.kv([('found', where), ('offers', ', '.join(npc.offers))])


@command('journal', 'What you have got yourself into.',
         group='info', aliases=('threads',), usage='journal [name]')
def cmd_journal(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    story = game.story

    if len(args):
        query = args.rest().lower()
        thread = next((t for t in thread_content.THREADS
                       if t.key.startswith(query)
                       or query in t.name.lower()), None)
        if thread is None or thread.key not in story.reached:
            raise CommandError(f'nothing in the journal about {query!r}')
        c.header(thread.name, thread.key)
        c.say(f'[dim]{thread.blurb}[/]')
        for stage in thread.stages:
            if stage.key not in story.reached[thread.key]:
                continue
            c.blank()
            c.rule(stage.headline)
            for para in stage.text.split('\n\n'):
                c.say(para)
                c.blank()
        crossing = [k for k in thread.crosses if k in story.reached]
        if crossing:
            c.say('[dim]Touches: '
                  + ', '.join(thread_content.BY_KEY[k].name
                              for k in crossing) + '[/]')
        return

    active = story.active_threads()
    c.header('Journal', f'{len(active)} of {len(thread_content.THREADS)}')
    if not active:
        c.say('[dim]Nothing yet. Things start when you meet people: `look` '
              'around wherever you are.[/]')
        return
    for thread in active:
        c.blank()
        c.raw(f'[accent]{thread.name}[/]  [dim]{thread.key}[/]')
        headline = story.headline(thread.key)
        if headline:
            c.say(f'[dim]{headline}[/]', indent='  ', subsequent='  ')
    if story.pending:
        c.blank()
        c.warn('Something is waiting on you. `choose` to see it.')
    c.blank()
    c.say('[dim]`journal <name>` to read one in full.[/]')


@command('choose', 'Decide the thing that is waiting on you.',
         group='city', contexts=('city',), usage='choose [option]')
def cmd_choose(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    found = game.story.open_choice()
    if found is None:
        raise CommandError('nothing is waiting on a decision from you.')
    thread, stage = found

    if not len(args):
        c.header(thread.name, stage.headline)
        for para in stage.text.split('\n\n'):
            c.say(para)
            c.blank()
        c.rule('what you do')
        for choice in stage.choices:
            c.blank()
            c.raw(f'  [accent]{choice.key}[/]  {choice.label}')
        c.blank()
        c.say('[dim]`choose <option>`. There is no going back on this one.[/]')
        return

    key = args[0].lower()
    choice = next((x for x in stage.choices if x.key.startswith(key)), None)
    if choice is None:
        raise CommandError('options: '
                           + ', '.join(x.key for x in stage.choices))

    game.story.resolve(thread.key, stage.key, choice)
    c.blank()
    c.rule(choice.label, role='accent2')
    for para in choice.text.split('\n\n'):
        c.say(para)
        c.blank()

    if choice.credits:
        game.char.credits = max(0, game.char.credits + choice.credits)
        word = 'in' if choice.credits > 0 else 'gone'
        c.say(f'[credit]{abs(choice.credits):,}c[/] {word}.')
    for faction, delta in choice.rep.items():
        game.alias.adjust_rep(faction, delta)
        c.say(f'[dim]{factions.BY_KEY[faction].short} '
              f'{"warmer" if delta > 0 else "colder"}.[/]')
    for rival_key, delta in choice.disposition.items():
        rival = game.city.rival(rival_key)
        if rival is not None:
            rival.adjust_disposition(delta)
    sess.autosave()
    _check_story(sess)


# --------------------------------------------------------------------------


def _match(query: str):
    query = (query or '').lower().strip()
    if not query:
        return None
    for npc in npc_content.NPCS:
        if query == npc.key or query in npc.name.lower():
            return npc
    return None


def _find(sess, query: str):
    game = sess.require_game()
    npc = _match(query)
    if npc is None:
        raise CommandError(f'nobody called {query!r}')
    if npc.key not in game.story.met:
        raise CommandError(f'you have not met them. `look` around.')
    return npc


def _check_story(sess) -> None:
    """Surface any scene that has become available.

    Never during a run: being handed a scene about a dying friend halfway
    through a vault is the wrong moment for both of them.
    """
    game = sess.game
    if game is None or sess.run is not None:
        return
    c = sess.console
    for thread_key, stage in game.story.available(game):
        thread = thread_content.BY_KEY[thread_key]
        game.story.reach(thread_key, stage)
        c.blank()
        c.rule(thread.name, role='accent2')
        c.say(f'[dim]{stage.headline}[/]')
        c.blank()
        for para in stage.text.split('\n\n'):
            c.say(para)
            c.blank()
        if stage.choices:
            c.say('[warn]This one is waiting on you.[/] [dim]`choose`.[/]')
    sess.autosave()
