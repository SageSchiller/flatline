"""Session commands: help, saving, and the shell's own furniture.

`help` is generated entirely from the registry (D9). There is no hand-written
command list anywhere in this project, which is the only way a command list
stays true.
"""

from __future__ import annotations

from .. import save as save_mod
from ..config import APP_TITLE
from ..content import manual, tutorial
from ..content import skills as skill_content
from .. import script as script_mod
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


@command('help', 'What you can type, and what everything means.',
         group='session', aliases=('?', 'h'), bare=True,
         usage='help [command|topic] [--all]',
         detail='With no argument, shows the commands you can use here and '
                'the manual index. `help <command>` explains a verb. '
                '`help <topic>` explains a system: try `help triangle` for '
                'the three numbers the whole game runs on, or `help firstrun` '
                'for a walkthrough of one.')
def cmd_help(sess, args) -> None:
    c = sess.console
    if len(args):
        want = args[0].lower()
        # A topic and a command can share a name; the command wins, because
        # somebody typing `help scan` wants the verb. Topics that collide are
        # reachable as `help --topic <name>`, and none currently do.
        cmd = REGISTRY.lookup(want)
        if cmd is None and not args.has('topic'):
            matches = REGISTRY.prefix_matches(want, sess.context)
            if len(matches) == 1:
                cmd = matches[0]
        if cmd is not None and not args.has('topic'):
            _help_command(sess, cmd)
            return

        topic = manual.BY_KEY.get(want)
        if topic is None:
            near = [k for k in manual.TOPIC_KEYS if k.startswith(want)]
            if len(near) == 1:
                topic = manual.BY_KEY[near[0]]
        if topic is not None:
            _help_topic(sess, topic)
            return
        raise CommandError(
            f'nothing called {want!r}. `help` for the command list and the '
            f'manual index.')

    _help_index(sess, everything=args.has('all'))


def _help_command(sess, cmd) -> None:
    c = sess.console
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
    # Point at the manual topics that explain what this verb operates on.
    related = [t for t in manual.TOPICS if cmd.name in t.commands]
    if related:
        c.blank()
        c.say('[dim]Background: '
              + ', '.join(f'`help {t.key}`' for t in related) + '[/]')


def _help_topic(sess, topic) -> None:
    c = sess.console
    c.header(topic.title, f'help {topic.key}')
    for para in topic.body.split('\n\n'):
        for line in para.split('\n'):
            # Lines that are already laid out as a table keep their spacing;
            # prose gets wrapped.
            if line.startswith('  '):
                c.raw(line)
            else:
                c.say(line)
        c.blank()
    if topic.commands:
        c.say('[dim]Commands: '
              + ', '.join(f'[fg]{x}[/]' for x in topic.commands) + '[/]')
    if topic.see:
        c.say('[dim]See also: '
              + ', '.join(f'`help {k}`' for k in topic.see) + '[/]')


def _help_index(sess, everything: bool = False) -> None:
    c = sess.console
    context = sess.context
    c.header(f'{APP_TITLE} help',
             'in a run' if context == 'run' else 'in the city')

    if sess.game is None:
        c.say('[dim]New here? `help basics` is four sentences on what this '
              'game is, and `tutorial` will walk you through one run while '
              'you play it.[/]')
        c.blank()

    for group in GROUPS:
        cmds = [x for x in REGISTRY.in_context(context) if x.group == group]
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
    c.rule('the manual')
    c.say('[dim]These explain the systems rather than the verbs. '
          '`help <topic>`.[/]')
    for group in manual.GROUPS:
        topics = [t for t in manual.TOPICS if t.group == group]
        if not topics:
            continue
        c.blank()
        c.raw(f'[accent2]{manual.GROUP_TITLES[group]}[/]')
        width = max(len(t.key) for t in topics)
        for topic in topics:
            pad = ' ' * (width - len(topic.key))
            c.say(f'  [fg]{topic.key}[/]{pad}  [dim]{topic.summary}[/]',
                  subsequent=' ' * (width + 4))

    c.blank()
    c.say('[dim]Prefixes work: `conn` reaches `connect`. Chain with `;`. '
          'Start with `help basics`.[/]')


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


@command('script', 'Write, keep, and run automation.',
         group='session',
         usage='script [list|show|write|save|run|drop|help] [name] [line]',
         detail='Needs Daemonology rank 2. A script is not a macro: it checks '
                'before it acts. `script write <name> if trace > 60: jack out` '
                'appends a line. `script help` lists everything a condition '
                'can read. Scripts are saved with the character.')
def cmd_script(sess, args) -> None:
    game = sess.require_game()
    if not game.char.has_technique('script'):
        raise CommandError('you have not learned to script. Daemonology '
                           'rank 2.')
    action = (args.get(0) or 'list').lower()
    c = sess.console

    if action == 'help':
        c.header('Script conditions', 'what a step can check')
        c.say('[dim]Four forms. A plain command runs. `if <cond>: <command>` '
              'runs only when the condition holds. `stop if <cond>` abandons '
              'the rest of the script. `repeat <n>: <command>` runs it up to '
              'ten times.[/]')
        c.blank()
        c.rule('numbers')
        c.kv([(name, blurb) for name, (_, blurb)
              in sorted(script_mod.NUMERIC.items())])
        c.say('[dim]Compare with > < >= <= = != against a whole number.[/]')
        c.blank()
        c.rule('yes or no')
        c.kv([(name, blurb) for name, (_, blurb)
              in sorted(script_mod.FLAGS.items())])
        c.say('[dim]Use bare, or negate with `not`: `if not open: crack`.[/]')
        c.blank()
        c.rule('alert')
        c.say('[dim]`alert` compares against '
              + ', '.join(script_mod.ALERT_LEVELS)
              + ': `stop if alert >= red`.[/]')
        c.blank()
        c.rule('examples you can copy')
        for name, lines in script_mod.EXAMPLES.items():
            c.blank()
            c.raw(f'  [accent]{name}[/]')
            for line in lines:
                c.raw(f'    [dim]{line}[/]')
        c.blank()
        c.say('[dim]`script example <name>` copies one into your library.[/]')
        return

    if action == 'list':
        if not sess.scripts:
            c.info('No scripts. `script help` for how to write one, or '
                   '`script example bailout` to start from a shipped one.')
            return
        c.header('Scripts', f'{len(sess.scripts)} saved')
        for name, script in sorted(sess.scripts.items()):
            try:
                count = len(script.steps)
                problem = ''
            except script_mod.ScriptError as e:
                count, problem = 0, str(e)
            tail = f'[err]{problem}[/]' if problem else f'[dim]{count} steps[/]'
            c.raw(f'  [accent]{name:<14}[/] {tail}')
        c.blank()
        c.say('[dim]`script show <name>` to read one.[/]')
        return

    name = args.get(1)
    if not name:
        raise CommandError('which script?')

    if action == 'example':
        lines = script_mod.EXAMPLES.get(name)
        if lines is None:
            raise CommandError('shipped examples: '
                               + ', '.join(script_mod.EXAMPLES))
        sess.scripts[name] = script_mod.Script(name=name, lines=list(lines))
        c.ok(f'{name} copied into your library.')
        for line in lines:
            c.raw(f'    [dim]{line}[/]')
        return

    if action == 'show':
        script = sess.scripts.get(name)
        if script is None:
            raise CommandError(f'no script called {name!r}')
        c.header(name, f'{len(script.lines)} lines')
        for i, line in enumerate(script.lines, start=1):
            c.raw(f'  [dim]{i:2}[/]  {line}')
        try:
            script.steps
        except script_mod.ScriptError as e:
            c.blank()
            c.err(str(e))
        return

    if action == 'write':
        line = args.raw_rest(2)
        if not line:
            raise CommandError('write what? `script write bail stop if '
                               'trace > 70`')
        try:
            script_mod.parse_line(line)
        except script_mod.ScriptError as e:
            raise CommandError(str(e)) from None
        script = sess.scripts.setdefault(
            name, script_mod.Script(name=name, lines=[]))
        if len(script.lines) >= script_mod.MAX_STEPS:
            raise CommandError(f'{name} is already {script_mod.MAX_STEPS} '
                               f'lines, which is the limit')
        script.lines.append(line)
        c.ok(f'{name} line {len(script.lines)}: [dim]{line}[/]')
        return

    if action == 'save':
        count = args.int_at(2, 5, 'how many commands')
        source = [l for l in sess.typed[:-1] if not l.startswith('script')]
        lines = source[-max(1, count):]
        if not lines:
            raise CommandError('nothing recent to record')
        sess.scripts[name] = script_mod.Script(name=name, lines=list(lines))
        c.ok(f'{name}: {len(lines)} steps recorded.')
        for line in lines:
            c.raw(f'    [dim]{line}[/]')
        c.say('[dim]`script write` to add conditions to it.[/]')
        return

    if action == 'run':
        sess.run_script(name)
        return

    if action == 'drop':
        if sess.scripts.pop(name, None) is None:
            raise CommandError(f'no script called {name!r}')
        c.ok(f'{name} dropped.')
        return

    raise CommandError('script list|show|write|save|run|drop|example|help')


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


@command('tutorial', 'A guided first run, one instruction at a time.',
         group='session', bare=True, usage='tutorial [stop|skip|again]',
         detail='Optional and interruptible. It watches what you do rather '
                'than leading you by the hand, so you can do the steps in any '
                'order, ignore it, or stop it. `skip` moves past a step you '
                'do not want to do.')
def cmd_tutorial(sess, args) -> None:
    c = sess.console
    action = (args.get(0) or '').lower()

    if action == 'stop':
        if sess.tutorial_step < 0:
            raise CommandError('the tutorial is not running.')
        sess.tutorial_step = -1
        c.ok('Tutorial off. `tutorial` starts it again from wherever you are.')
        return

    if action == 'skip':
        if sess.tutorial_step < 0:
            raise CommandError('the tutorial is not running.')
        sess.tutorial_step += 1
        if sess.tutorial_step >= len(tutorial.STEPS):
            sess.tutorial_step = -1
            c.ok('That was the last one.')
            return
        c.info('Skipped.')
        sess.tutorial_show()
        return

    if action == 'again':
        sess.tutorial_step = 0

    if sess.tutorial_step < 0:
        # Start at the first step the player has not already satisfied, so
        # somebody who asks for it forty shifts in is not told to make a
        # character they already have.
        sess.tutorial_step = 0
        c.blank()
        c.rule('tutorial', role='accent2')
        c.say(tutorial.OPENING)
        sess.tutorial_advance()
        if sess.tutorial_step >= 0:
            sess.tutorial_show()
        return

    c.info(f'Step {sess.tutorial_step + 1} of {len(tutorial.STEPS)}.')
    sess.tutorial_show()
