"""Session commands: help, saving, and the shell's own furniture.

`help` is generated entirely from the registry (D9). There is no hand-written
command list anywhere in this project, which is the only way a command list
stays true.
"""

from __future__ import annotations

from .. import save as save_mod
from ..config import APP_TITLE
from ..content import skills as skill_content
from ..shell import GROUPS, REGISTRY, CommandError, Quit, command

GROUP_TITLES = {
    'session': 'Session',
    'character': 'Character',
    'city': 'The city',
    'prep': 'Preparation',
    'recon': 'Reconnaissance',
    'access': 'Access',
    'action': 'Action',
    'defence': 'Defence and escape',
    'info': 'Information',
}


@command('help', 'What you can type, and what it does.',
         group='session', aliases=('?', 'h'), bare=True,
         usage='help [command]',
         detail='With no argument, lists every command legal in the current '
                'context, grouped. With a command name, prints that command\'s '
                'full description, including its cost in ticks.')
def cmd_help(sess, args) -> None:
    c = sess.console
    if len(args):
        name = args[0].lower()
        cmd = REGISTRY.lookup(name)
        if cmd is None:
            matches = REGISTRY.prefix_matches(name, sess.context)
            if len(matches) != 1:
                raise CommandError(f'no command called {name!r}')
            cmd = matches[0]
        c.header(cmd.name, cmd.usage or '')
        c.say(cmd.summary)
        if cmd.detail:
            c.blank()
            c.say(cmd.detail)
        rows = []
        if cmd.aliases:
            rows.append(('also', ', '.join(cmd.aliases)))
        rows.append(('where', 'anywhere' if 'any' in cmd.contexts
                     else ', '.join(cmd.contexts)))
        if cmd.ticks:
            rows.append(('costs', f'{cmd.ticks} tick'
                                  f'{"s" if cmd.ticks != 1 else ""}'))
        c.blank()
        c.kv(rows)
        return

    c.header(f'{APP_TITLE} commands',
             'in a run' if sess.context == 'run' else 'in the city')
    for group in GROUPS:
        cmds = [x for x in REGISTRY.in_context(sess.context) if x.group == group]
        if not cmds:
            continue
        c.blank()
        c.raw(f'[accent]{GROUP_TITLES[group]}[/]')
        width = max(len(x.name) for x in cmds)
        for cmd in cmds:
            pad = ' ' * (width - len(cmd.name))
            c.say(f'  [fg]{cmd.name}[/]{pad}  [dim]{cmd.summary}[/]',
                  subsequent=' ' * (width + 4))
    c.blank()
    c.say('[dim]Prefixes work: `conn` reaches `connect`. Chain with `;`. '
          '`help <command>` for detail.[/]')


@command('quit', 'Leave. Saves first unless you say otherwise.',
         group='session', aliases=('exit',), bare=True,
         usage='quit [--no-save]')
def cmd_quit(sess, args) -> None:
    if sess.run is not None and not args.has('force'):
        raise CommandError('you are still jacked in. `jack out` first, or '
                           '`quit --force` to drop the connection.')
    if sess.game is not None and not args.has('no-save'):
        sess.autosave()
        sess.console.info(f'Saved to slot {sess.slot!r}.')
    raise Quit(0)


@command('save', 'Write the current game to disk.',
         group='session', usage='save [slot]')
def cmd_save(sess, args) -> None:
    game = sess.require_game()
    slot = args.get(0) or sess.slot
    path = game.save(slot)
    sess.slot = slot
    sess.console.ok(f'Saved to {path}.')


@command('restore', 'Load a saved game.',
         group='session', bare=True, usage='restore [slot]',
         detail='Named `restore` rather than `load` because `load` puts a '
                'program on your deck, which you will type far more often.')
def cmd_restore(sess, args) -> None:
    slots = save_mod.slots()
    if not slots:
        raise CommandError('no saves found.')
    slot = args.get(0)
    if slot is None:
        if len(slots) == 1:
            slot = slots[0]
        else:
            raise CommandError(f'which one: {", ".join(slots)}')
    if sess.run is not None:
        raise CommandError('finish the run first.')
    sess.load_game(slot)
    game = sess.game
    sess.console.ok(f'{game.char.handle}, running as [accent]'
                    f'{game.alias.name}[/]. {game.city.when}, '
                    f'{game.city.district.name}.')
    if game.over:
        sess.console.warn(f'This character is finished: {game.over}')


@command('history', 'What you have typed this session.',
         group='session', bare=True, usage='history [count]')
def cmd_history(sess, args) -> None:
    count = args.int_at(0, 20, 'how many lines')
    lines = sess.typed[-max(1, count):]
    if not lines:
        sess.console.info('Nothing yet.')
        return
    for i, line in enumerate(lines, start=len(sess.typed) - len(lines) + 1):
        sess.console.raw(f'[dim]{i:4}[/]  {line}')


@command('bind', 'Make one word stand for another.',
         group='session', bare=True, usage='bind [word] [line]',
         detail='Shell shorthand, distinct from `alias`, which is the name you '
                'run under. With no arguments, lists what is bound. Only the '
                'first word is replaced, so `bind s scan` makes `s 2` mean '
                '`scan 2`.')
def cmd_bind(sess, args) -> None:
    if not len(args):
        if not sess.shell_aliases:
            sess.console.info('Nothing bound.')
            return
        sess.console.kv(sorted(sess.shell_aliases.items()))
        return
    word = args[0]
    if not args.get(1):
        if sess.shell_aliases.pop(word, None) is not None:
            sess.console.ok(f'{word} unbound.')
        else:
            raise CommandError(f'{word!r} is not bound')
        return
    if REGISTRY.lookup(word):
        raise CommandError(f'{word!r} is already a command')
    sess.shell_aliases[word] = args.rest(1)
    sess.console.ok(f'{word} -> {args.rest(1)}')


@command('script', 'Record and replay a sequence of commands.',
         group='session', usage='script [save|run|list|drop] [name]',
         detail='Needs Daemonology rank 2. `script save <name> <n>` takes the '
                'last n commands you typed. `script run <name>` replays them, '
                'and inside a run costs one tick less than the sum of its '
                'parts, to a minimum of one.')
def cmd_script(sess, args) -> None:
    game = sess.require_game()
    if not game.char.has_technique('script'):
        raise CommandError('you have not learned to script. Daemonology '
                           'rank 2.')
    action = (args.get(0) or 'list').lower()
    c = sess.console

    if action == 'list':
        if not sess.scripts:
            c.info('No scripts.')
            return
        for name, lines in sorted(sess.scripts.items()):
            c.raw(f'[accent]{name}[/] [dim]({len(lines)} steps)[/]')
            for line in lines:
                c.raw(f'    [dim]{line}[/]')
        return

    name = args.get(1)
    if not name:
        raise CommandError('which script?')

    if action == 'save':
        count = args.int_at(2, 5, 'how many commands')
        # The `script save` line is itself in the history; drop it.
        source = [l for l in sess.typed[:-1] if not l.startswith('script')]
        lines = source[-max(1, count):]
        if not lines:
            raise CommandError('nothing recent to record')
        sess.scripts[name] = lines
        c.ok(f'{name}: {len(lines)} steps recorded.')
        for line in lines:
            c.raw(f'    [dim]{line}[/]')
        return

    if action == 'run':
        sess.run_script(name)
        return

    if action == 'drop':
        if sess.scripts.pop(name, None) is None:
            raise CommandError(f'no script called {name!r}')
        c.ok(f'{name} dropped.')
        return

    raise CommandError('script save|run|list|drop')


@command('techniques', 'What your training lets you do.',
         group='info', aliases=('tech',))
def cmd_techniques(sess, args) -> None:
    game = sess.require_game()
    c = sess.console
    have = game.char.techniques()
    c.header('Techniques', f'{len(have)} of {len(skill_content.TECHNIQUES)}')
    if not have:
        c.say('[dim]None yet. Ranks 2 and 4 of every skill unlock one.[/]')
        return
    for tech in have:
        verb = tech.verb or 'modifies an existing command'
        c.blank()
        c.raw(f'[accent]{tech.name}[/]  [dim]{verb}[/]')
        c.say(tech.summary, indent='  ')
        c.say(f'[dim]{tech.detail}[/]', indent='  ')
