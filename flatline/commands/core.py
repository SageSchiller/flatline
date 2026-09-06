"""Session commands: help, saving, and the shell's own furniture.

`help` is generated entirely from the registry (D9). There is no hand-written
command list anywhere in this project, which is the only way a command list
stays true.
"""

from __future__ import annotations

import pathlib
import re

from .. import save as save_mod
from ..config import APP_TITLE
from ..content import factions as fac_content
from ..content import manual, tutorial
from ..content import skills as skill_content
from .. import script as script_mod
from .. import anim
from .. import ui
from .. import theme
from .. import prompt as prompt_mod
from ..content import districts
from ..content import origins
from ..content import rice
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


@command('help', 'Where to start, what you can type, and what it all means.',
         group='session', aliases=('?', 'h'), bare=True,
         usage='help [command|topic|commands|topics|<search>] [--all]',
         detail='With no argument: one screen. What to read first, the verbs '
                'that answer "what now", and where the rest lives. '
                '`help commands` is every verb grouped, `help topics` is every '
                'explanation grouped, and `help --all` is both at once, which '
                'is what this used to be and is a hundred and forty lines. '
                '`help <anything else>` finds a verb, a system, or searches '
                'both for the word.')
def cmd_help(sess, args) -> None:
    if args.has('all'):
        _help_everything(sess)
        return

    # `--topic <key>` forces the manual entry when a command shadows it, and
    # is what the seven colliding pages tell you to type. It parses as an
    # option rather than a flag, so `args.has('topic')` never saw it and the
    # documented escape hatch quietly showed the index instead.
    forced = args.opt('topic') or (args.get(0) if args.has('topic') else None)
    if forced:
        topic = manual.BY_KEY.get(forced.lower())
        if topic is None:
            raise CommandError(f'no manual topic called {forced!r}. '
                               f'`help topics` for the list.')
        _help_topic(sess, topic)
        return

    if not len(args):
        _help_landing(sess)
        return

    want = args[0].lower()
    # The two index pages. Checked before the registry so they cannot be
    # shadowed later by a verb that happens to be called `topics`.
    if want in ('commands', 'verbs'):
        _help_commands(sess, (args.get(1) or sess.context).lower())
        return
    if want in ('topics', 'manual', 'systems'):
        _help_topics(sess)
        return

    # A topic and a command can share a name; the command wins, because
    # somebody typing `help scan` wants the verb. The command page links to
    # any topic that covers it, so the other one is one hop away.
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

    _help_search(sess, args.rest().lower())


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
    #
    # A topic whose key is this command's own name, or one of its aliases, is
    # called out separately and by the form that actually reaches it. Seven
    # collide, and listing one the ordinary way put "Background: `help
    # chrome`" at the bottom of the page somebody got by typing `help chrome`.
    names = {cmd.name, *cmd.aliases}
    same = next((manual.BY_KEY[n] for n in names if n in manual.BY_KEY), None)
    related = [t for t in manual.TOPICS
               if cmd.name in t.commands and t.key not in names]
    if related:
        c.blank()
        c.say('[dim]Background: '
              + ', '.join(f'`help {t.key}`' for t in related) + '[/]')
    if same is not None:
        if not related:
            c.blank()
        c.say(f'[dim]There is a manual topic of the same name, about the '
              f'system rather than the verb: [fg]help --topic {same.key}[/]'
              f'[dim] ({same.summary})[/]')


def _help_topic(sess, topic) -> None:
    c = sess.console
    # The header names the form that reaches this page. For the seven keys a
    # command shadows, `help <key>` is not that form and printing it is the
    # page lying about its own address.
    reached = ('help --topic' if REGISTRY.lookup(topic.key) else 'help')
    c.header(topic.title, f'{reached} {topic.key}')
    for para in topic.body.split('\n\n'):
        # A paragraph that opens by naming itself gets a rule, so a page of
        # twenty-five paragraphs is a page you can scan (D68). The marker is
        # the prose's own shape: `[warn]The decision:[/]`, `[warn]Six
        # shapes.[/]`, and so on.
        head = _sub_heading(para)
        if head:
            c.rule(head, role='muted')
            para = para[para.index('[/]') + 3:].lstrip()
            # The sentence carried on from the heading, so it starts in
            # lower case; standing on its own under a rule it should not.
            # Only plain prose gets the capital: a paragraph that opens with
            # markup opens with a command name, which is lower case on
            # purpose, and reaching into the tag for a letter to raise turns
            # `[fg]errands[/]` into a visible `[Fg]errands`.
            if para[:1].isalpha():
                para = para[0].upper() + para[1:]
        for line in para.split('\n'):
            # Lines that are already laid out as a table keep their spacing;
            # prose gets wrapped.
            if line.startswith('  '):
                c.raw(_colour_nouns(line))
            else:
                c.say(_colour_nouns(line))
        c.blank()
    if topic.commands:
        c.say('[dim]Commands: '
              + ', '.join(f'[fg]{x}[/]' for x in topic.commands) + '[/]')
    if topic.see:
        c.say('[dim]See also: ' + ', '.join(
            f'`help {"--topic " if REGISTRY.lookup(k) else ""}{k}`'
            for k in topic.see) + '[/]')


#: The nouns that have a colour everywhere else in the game and had one
#: almost nowhere in the manual (D68). Coloured at render time rather than
#: in the prose, so a page written today is consistent with one written in
#: March, and only outside existing markup, so nothing nests by accident.
NOUN_ROLES = {
    'trace': 'trace', 'noise': 'noise', 'residue': 'residue',
    'heat': 'heat', 'credits': 'credit', 'dissonance': 'accent2',
}
_NOUNS = re.compile(r'\b(' + '|'.join(NOUN_ROLES) + r')\b', re.IGNORECASE)


def _colour_nouns(text: str) -> str:
    """Wrap the game's own nouns in the game's own colours, outside tags."""
    out, depth, i = [], 0, 0
    for m in re.finditer(r'\[[^\]]*\]', text):
        chunk = text[i:m.start()]
        out.append(_NOUNS.sub(
            lambda w: f'[{NOUN_ROLES[w.group(1).lower()]}]{w.group(1)}[/]',
            chunk) if depth == 0 else chunk)
        tag = m.group(0)
        out.append(tag)
        depth += -1 if tag == '[/]' else 1
        i = m.end()
    tail = text[i:]
    out.append(_NOUNS.sub(
        lambda w: f'[{NOUN_ROLES[w.group(1).lower()]}]{w.group(1)}[/]',
        tail) if depth == 0 else tail)
    return ''.join(out)


#: The longest a leading `[warn]...[/]` can be and still be a heading
#: rather than an emphasised sentence.
SUB_HEADING_MAX = 34


def _sub_heading(para: str) -> str:
    """The heading a paragraph opens with, or '' if it does not open with
    one. A short bolded phrase ending in a colon or a full stop is a
    heading; anything longer is prose that happens to start emphasised."""
    if not para.startswith('[warn]'):
        return ''
    end = para.find('[/]')
    if end < 0:
        return ''
    text = para[len('[warn]'):end].strip()
    if len(text) > SUB_HEADING_MAX or not text.endswith((':', '.')):
        return ''
    return text.rstrip(':.').lower()


def _listing(c, rows: list[tuple[str, str]], indent: str = '  ') -> None:
    """A name-and-blurb list, aligned, wrapping under its own name column."""
    if not rows:
        return
    width = max(len(name) for name, _ in rows)
    for name, blurb in rows:
        pad = ' ' * (width - len(name))
        # The indent goes through `say`'s own parameter rather than into the
        # string: `wrap` strips leading space off what it is given, so an
        # indent written inline disappears and the continuation lines of a
        # long blurb hang under nothing.
        c.say(f'[fg]{name}[/]{pad}  [dim]{blurb}[/]', indent=indent,
              subsequent=indent + ' ' * (width + 2))


def _help_landing(sess) -> None:
    """One screen, answering the three questions separately.

    This used to print every verb in context and every topic in the manual,
    which was a hundred and forty lines and six screenfuls. It was trying to
    answer three different questions at once: what do I type, how does this
    work, and I am lost. Somebody asking any one of them had to scroll past
    the other two.
    """
    c = sess.console
    context = sess.context
    c.header(f'{APP_TITLE} help',
             'in a run' if context == 'run' else 'in the city')

    c.say('[accent]Read these four, in this order[/]')
    _listing(c, [(k, manual.BY_KEY[k].summary) for k in manual.STARTER_PATH
                 if k in manual.BY_KEY])
    if sess.game is None:
        c.say('[dim]...or `tutorial`, which walks you through a run one '
              'instruction at a time while you play it.[/]', indent='  ',
              subsequent='  ')

    c.blank()
    c.say('[accent]Lost right now[/]')
    _listing(c, [(name, blurb) for name, blurb in manual.ORIENTATION
                 if REGISTRY.lookup(name)])
    c.say('[dim]None of those cost time, and all of them are safe to ask at '
          'any point.[/]', indent='  ', subsequent='  ')

    c.blank()
    c.say('[accent]Everything else[/]')
    verbs = len(REGISTRY.in_context(context))
    _listing(c, [
        ('help commands', f'all {verbs} verbs you can use here, grouped'),
        ('help topics', f'all {len(manual.TOPICS)} explanations, grouped'),
        ('help <word>', 'a verb, a system, or a search across both'),
    ])

    c.blank()
    c.say('[dim]Prefixes work: `conn` reaches `connect`. Row numbers work '
          'wherever a list was shown: `take 2`, `buy 3`. Chain commands with '
          '`;`. `help --all` is the old everything-at-once index.[/]')


def _help_commands(sess, which: str) -> None:
    """Every verb, grouped. `which` is a context, or `all` for both."""
    c = sess.console
    if which in ('all', 'any', 'both'):
        context, label = None, 'everywhere'
    elif which in ('city', 'run'):
        context = which
        label = 'in a run' if which == 'run' else 'in the city'
    else:
        raise CommandError(f'`help commands` takes city, run or all, '
                           f'not {which!r}')
    cmds = (REGISTRY.in_context(context) if context
            else sorted(REGISTRY.commands.values(),
                        key=lambda x: (GROUPS.index(x.group), x.name)))
    c.header('Commands', label)
    for group in GROUPS:
        rows = [(x.name, x.summary) for x in cmds if x.group == group]
        if not rows:
            continue
        c.blank()
        c.raw(f'[accent]{GROUP_TITLES[group]}[/]')
        _listing(c, rows)
    c.blank()
    c.say('[dim]`help <verb>` for what one does, what it costs, and the '
          'topic that explains what it operates on. `help commands all` for '
          'the ones that only work elsewhere.[/]')


def _help_topics(sess) -> None:
    """Every explanation, grouped."""
    c = sess.console
    c.header('The manual', f'{len(manual.TOPICS)} topics')
    c.say('[dim]These explain the systems rather than the verbs.[/]')
    for group in manual.GROUPS:
        topics = [t for t in manual.TOPICS if t.group == group]
        if not topics:
            continue
        c.blank()
        c.raw(f'[accent2]{manual.GROUP_TITLES[group]}[/]')
        _listing(c, [(t.key, t.summary) for t in topics])
    c.blank()
    c.say('[dim]`help <topic>` to read one. Every topic ends with the '
          'decision it exists to inform.[/]')


def _help_everything(sess) -> None:
    """Both indexes at once. What `help` used to be, for anybody who wants it."""
    _help_commands(sess, sess.context)
    sess.console.blank()
    _help_topics(sess)


#: How many search hits are worth printing. Past this it is not a search
#: result, it is the index again.
SEARCH_LIMIT = 12


def _in_catalogue(topic, word: str) -> bool:
    """Whether a topic's own content module names something called this.

    Read off `covers`, so it stays true for free: a topic that documents the
    drugs is searchable by every drug name the moment one is added, and a
    module renamed out from under it fails `validate.py` rather than quietly
    unindexing itself.
    """
    import importlib
    for module_name in topic.covers:
        try:
            module = importlib.import_module(
                f'..content.{module_name}', __package__)
        except ImportError:
            continue
        table = getattr(module, 'BY_KEY', None)
        if not isinstance(table, dict):
            continue
        for key, value in table.items():
            if word in str(key).lower():
                return True
            name = getattr(value, 'name', '')
            if name and word in str(name).lower():
                return True
    return False


def _help_search(sess, word: str) -> None:
    """Nothing is called that. Find what does mention it.

    A hundred and thirty verbs and forty-two topics is more than anybody can
    hold the names of, and the commonest failure is knowing what you want and
    not what it is called. `help addiction` and `help loan` and `help odds of
    winning` all have to land somewhere rather than raising.
    """
    c = sess.console
    if not word:
        raise CommandError('search for what?')

    # D63 c: `help sable` is a question about a thing, and the thing has a
    # page. Exact key or name only; a topic that happens to mention a word
    # still wins the search below.
    from .city import find_item, describe_item
    hit = find_item(word)
    if hit is not None and (hit[1].key == word
                            or hit[1].name.lower() == word):
        describe_item(sess, *hit)
        module = {'program': 'programs', 'ware': 'cyberware',
                  'component': 'hardware', 'drug': 'drugs'}.get(hit[0], '')
        pointers = [t for t in manual.TOPICS if module in t.covers]
        if pointers:
            c.say('[dim]How it works: '
                  + ', '.join(f'`help {t.key}`' for t in pointers) + '.[/]')
        return

    topics: list[tuple[int, str, str]] = []
    for topic in manual.TOPICS:
        score = 0
        if word in topic.key or word in topic.terms:
            score = 3
        elif word in topic.title.lower() or word in topic.summary.lower():
            score = 2
        elif any(word in term for term in topic.terms):
            score = 2
        elif word in ui.plain(topic.body).lower():
            score = 1
        elif _in_catalogue(topic, word):
            # The proper nouns of whatever this topic documents. `help kick`
            # and `help gatekeeper` and `help carrion` are all things a player
            # will type, and none of them appear in any prose.
            score = 2
        if score:
            topics.append((score, topic.key, topic.summary))

    verbs: list[tuple[int, str, str]] = []
    for cmd in REGISTRY.in_context(sess.context):
        haystack = ' '.join((cmd.name, ' '.join(cmd.aliases))).lower()
        score = 0
        if word in haystack:
            score = 3
        elif word in cmd.summary.lower():
            score = 2
        elif word in (cmd.detail or '').lower():
            score = 1
        if score:
            verbs.append((score, cmd.name, cmd.summary))

    if not topics and not verbs:
        raise CommandError(
            f'nothing called {word!r}, and nothing mentions it. '
            f'`help topics` for the manual, `help commands` for the verbs.')

    # A word a topic *claims* is that topic's word (D68). `trace` is
    # mentioned by nineteen pages and belongs to one; handing back nineteen
    # rows was the search refusing to answer a question it knew the answer
    # to. An outright owner wins, and the rest becomes a dim footnote.
    owners = [t for t in topics if t[0] == 3]
    if len(owners) == 1 and not [v for v in verbs if v[0] == 3]:
        topic = manual.BY_KEY[owners[0][1]]
        _help_topic(sess, topic)
        rest = [t for t in topics if t[1] != topic.key][:6]
        if rest:
            c.blank()
            c.say(f'[dim]{len(topics) - 1} other page'
                  f'{"s" if len(topics) - 1 != 1 else ""} mention '
                  f'{word!r}: '
                  + ', '.join(f'`help --topic {t[1]}`' for t in rest)
                  + ('...' if len(topics) - 1 > len(rest) else '') + '[/]')
        return

    # One hit is an answer, not a result set. Making somebody read a list of
    # length one and then type the only thing on it is a search being pleased
    # with itself.
    if len(topics) + len(verbs) == 1:
        if topics:
            c.say(f'[dim]Nothing is called {word!r}. This is the one that '
                  f'covers it.[/]')
            _help_topic(sess, manual.BY_KEY[topics[0][1]])
        else:
            c.say(f'[dim]Nothing is called {word!r}. This is the one that '
                  f'mentions it.[/]')
            _help_command(sess, REGISTRY.lookup(verbs[0][1]))
        return

    c.header(f'Anything about {word!r}', f'{len(topics) + len(verbs)} found')
    for label, found in (('Explanations', topics), ('Verbs', verbs)):
        if not found:
            continue
        found.sort(key=lambda row: (-row[0], row[1]))
        c.blank()
        c.raw(f'[accent]{label}[/]')
        _listing(c, [(name, blurb) for _, name, blurb
                     in found[:SEARCH_LIMIT]])
        if len(found) > SEARCH_LIMIT:
            c.say(f'[dim]  ...and {len(found) - SEARCH_LIMIT} more.[/]')


def fac_short(key: str) -> str:
    faction = fac_content.BY_KEY.get(key)
    return faction.short if faction else key or 'somebody'


@command('retire', 'Stop. Properly, on purpose, while you still can.',
         group='session', contexts=('city',), usage='retire [--confirm]',
         detail='The only exit that is not black ICE or closing the terminal. '
                'It wants four things, all of them things the city has spent '
                'your whole career making harder: nothing owed, nothing in '
                'you that you need, nobody paying for your name, and enough '
                'put away. With no argument it prints how far off you are, '
                'which is the only way anybody finds out this is a goal. What '
                'you leave behind reaches whoever you make next.')
def cmd_retire(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    char = game.char
    from ..content import drugs, legacy
    from .. import save as save_mod

    owed = game.debt.amount if game.debt.owed else 0
    lender = (fac_short(game.debt.lender) if game.debt.owed else '')
    habit = drugs.normalise(char.chem)['habit']
    worst = max(habit.values(), default=0)
    bounty = max(game.city.bounties.values(), default=0)
    # A name that has held (D95). Four bounties came off for one alias fee
    # the shift before, and the campaign's hardest condition was its
    # cheapest. The number has to be nought and the name has to be old
    # enough that nobody is still looking for the last one.
    age = game.city.shift - int(game.alias.established)
    state = {
        'stake': char.credits >= legacy.STAKE,
        'debt': not owed,
        'clean': worst < drugs.WITHDRAWAL_AT,
        'quiet': bounty <= 0 and age >= legacy.NAME_HOLDS,
    }
    if bounty > 0:
        quiet_why = ('There is a bounty on you. A retirement with a number '
                     'attached to it is a change of address, and they have '
                     'your address')
    else:
        quiet_why = (f'The name is {age} shift{"s" if age != 1 else ""} old '
                     f'and the last one is still warm. Nobody retires under '
                     f'a name that has not held for {legacy.NAME_HOLDS}: '
                     f'that is a change of address with the old one still '
                     f'on the door')
    fill = {'credits': char.credits, 'stake': legacy.STAKE, 'owed': owed,
            'lender': lender or 'anybody', 'quiet_why': quiet_why}

    if not args.has('confirm') or not all(state.values()):
        c.header('Getting out', f'{sum(state.values())} of {len(state)}')
        for key, want, missing in legacy.GATES:
            done = state[key]
            c.raw(f'  [{"ok" if done else "err"}]'
                  f'{c.caps.g("check") if done else c.caps.g("cross")}[/] '
                  f'[{"dim" if done else "fg"}]{want}[/]')
            if not done:
                c.say(f'[dim]{missing.format(**fill)}[/]', indent='    ',
                      subsequent='    ')
        c.blank()
        if all(state.values()):
            c.say('[accent2]All four. You can stop.[/] [dim]`retire '
                  '--confirm`, and it is not reversible, and it is not '
                  'supposed to be.[/]')
        else:
            c.say('[dim]None of these is hard on its own. All four at once is '
                  'the campaign, which is the point: the door has been there '
                  'since the first shift.[/]')
        return

    title, text = legacy.ending(char.dissonance, game.story.flags)
    c.blank()
    c.rule('out', role='accent2')
    c.say(legacy.LEAVING)
    c.blank()
    c.rule(title, role='accent')
    for para in text.split('\n\n'):
        c.say(para)
        c.blank()

    c.kv([('handle', char.handle),
          ('runs', str(char.runs)),
          ('earned', f'[credit]{game.earned:,}c[/]'),
          ('walked away with', f'[credit]{char.credits:,}c[/]'),
          ('drift', f'{char.dissonance} ({char.dissonance_band[1]})')])
    _epilogue(sess)

    game.over = 'retired'
    _bequeath(sess, 'retired')
    sess.record_progress()
    save_mod.bump_meta(retirements=1)
    sess.autosave()
    c.blank()
    c.say('[dim]`new` when you want to be somebody else. Something of this '
          'one will find them.[/]')


def end_character(sess, how: str) -> None:
    """A character finished by a decision, not by ICE or the door. D52.

    `how` is the past-tense phrase the roster will use: 'went under'. The
    scene that ended them has already said what happened; this prints the
    numbers the flatline prints, reads the decisions back, leaves one thing
    to whoever is next, and files them. What is left is drawn from the
    flatline's list, because the chair is still occupied and the deck is
    still warm: nobody chose what to leave.
    """
    from .. import save as save_mod
    game, c = sess.game, sess.console
    char = game.char
    c.blank()
    c.rule(how, role='accent2')
    c.kv([('handle', char.handle),
          ('ran as', game.alias.name),
          ('runs', str(char.runs)),
          ('earned', f'[credit]{game.earned:,}c[/]'),
          ('drift', f'{char.dissonance} ({char.dissonance_band[1]})')])
    _epilogue(sess)
    game.over = how
    _bequeath(sess, 'flatlined')
    sess.record_progress()
    save_mod.bump_meta(killed=1 if how.startswith('killed') else 0,
                       went_under=0 if how.startswith('killed') else 1)
    sess.autosave()
    c.blank()
    c.say('[dim]`new` when you want to be somebody else. Something of this '
          'one will find them.[/]')


def _epilogue(sess) -> None:
    """What you left behind, in people. D51.

    Every decision the character made, read back once, in the order the
    threads are written, at whichever end they reached. Printed at retirement
    and at the flatline alike, because the flatline is the ending most
    players get and it used to forget everything but the numbers.
    """
    from ..content import legacy
    game, c = sess.game, sess.console
    lines = legacy.epilogue(game.story.flags)
    if lines:
        c.blank()
        c.rule('what you left behind, in people', role='accent2')
        c.bullets(lines, role='dim')
    # And in nights (D99). The epilogue read the decisions back and not
    # the career, and a character who had run nine times, been emptied by
    # a collection and burned a name ended as a list of other people.
    career = career_lines(game)
    if career:
        c.blank()
        c.rule('and in nights', role='accent2')
        c.bullets(career, role='dim')
    # And the one thing that was not for the work (D152).
    from ..world import pets as pet_world
    coda = pet_world.ending_coda(game.city)
    if coda:
        c.blank()
        c.rule('and in the one that was not for the work', role='accent2')
        c.say(f'[dim]{coda}[/]')


def career_lines(game) -> list[str]:
    """Two or three lines the log can say about a career, for the end."""
    history = game.history
    if not history:
        return []
    out: list[str] = []
    done = [h for h in history if h.get('done')]
    severed = [h for h in history if h.get('outcome') == 'severed']
    names = len(game.aliases)
    out.append(f'{len(history)} night{"s" if len(history) != 1 else ""} in '
               f'the chair, {len(done)} of them paid, under '
               f'{names} name{"s" if names != 1 else ""}.')
    if done:
        best = max(done, key=lambda h: int(h.get('pay', 0)))
        who = (fac_content.BY_KEY[best['faction']].short
               if best.get('faction') in fac_content.BY_KEY else 'somebody')
        out.append(f'The best of them was {best.get("title") or "a night "
                   "nobody was paying for"}, against {who}, on day '
                   f'{best.get("day", 0)}: {int(best.get("pay", 0)):,}c.')
    if severed:
        worst = max(severed, key=lambda h: int(h.get('trace', 0)))
        who = (fac_content.BY_KEY[worst['faction']].short
               if worst.get('faction') in fac_content.BY_KEY else 'somebody')
        from ..content import ice as ice_content
        held = game.city.grudges.get(worst.get('faction', ''), '')
        it = ice_content.BY_KEY.get(held)
        out.append(f'The worst was day {worst.get("day", 0)}, when {who} '
                   f'cut the line at {worst.get("alert", "red")}'
                   + (f', and a {it.name} has been running since'
                      if it is not None else '')
                   + '.')
    return out


def _bequeath(sess, how: str) -> None:
    """Leave exactly one thing to whoever gets made next.

    Not chosen by the player. An inheritance you picked is a difficulty
    setting with prose on it; an inheritance that arrives is the city having
    an opinion about how you went.
    """
    from ..content import legacy
    from .. import save as save_mod

    game, c = sess.game, sess.console
    char = game.char
    stream = game.rng('events')
    options = legacy.candidates(how)
    # Filtered to the ones this particular character can actually leave. A
    # chrome bequest from somebody who was never chromed is the game inventing
    # a life they did not have.
    viable = []
    for bequest in options:
        if bequest.key == 'stake' and char.credits < 1000:
            continue
        if bequest.key == 'chrome' and not char.installed:
            continue
        if bequest.key == 'program' and not char.library \
                and not char.deck.loaded:
            continue
        if bequest.key == 'debt' and not game.debt.owed:
            continue
        viable.append(bequest)
    if not viable:
        return
    picked = stream.pick(viable)

    detail: dict = {}
    if picked.key == 'stake':
        detail['amount'] = int(char.credits * legacy.STAKE_SHARE)
    elif picked.key == 'name':
        best = max(fac_content.FACTION_KEYS,
                   key=lambda k: game.alias.reputation(k))
        detail['faction'] = best
    elif picked.key == 'chrome':
        detail['ware'] = stream.pick(char.installed)
    elif picked.key == 'program':
        pool = list(char.library) + list(char.deck.loaded)
        detail['program'] = stream.pick(pool)
    elif picked.key == 'debt':
        detail['amount'] = int(game.debt.amount * legacy.DEBT_SHARE)
        detail['lender'] = game.debt.lender

    save_mod.leave_estate(picked.key, char.handle, how, **detail)
    c.blank()
    c.say(f'[dim]{picked.summary}[/]')


@command('quit', 'Leave. Saves first unless you say otherwise.',
         group='session', aliases=('exit',), bare=True,
         usage='quit [--no-save]',
         detail='The deck powers down on the way out: the link dropped, the '
                'city dark, the mark gone, the trace flat. Ctrl-C during it '
                'skips to the end, and `--no-intro` on the command line skips '
                'it the way it skips the boot.')
def cmd_quit(sess, args) -> None:
    if sess.run is not None and not args.has('force'):
        raise CommandError('you are still jacked in. `jack out` first, or '
                           '`quit --force` to drop the connection.')
    if sess.game is not None and not args.has('no-save'):
        sess.autosave()
        sess.console.info(f'Saved to slot {sess.slot!r}.')
    raise Quit(0)


@command('save', 'Write the current game to disk.',
         group='session', usage='save [slot] [--export <path>] [--force]',
         detail='Ordinary saves live in the XDG data directory, which is '
                'correct and is also the one place you will not think to back '
                'up. `--export <path>` writes a copy anywhere you like: same '
                'format, same migrations, so a copy made today still opens '
                'after the format moves on. `restore --import <path>` brings '
                'one back.')
def cmd_save(sess, args) -> None:
    game = sess.require_game()
    c = sess.console

    target = args.opt('export')
    if target is not None:
        sess.sync_scripts()
        path = pathlib.Path(target).expanduser()
        # Check what it is before checking whether to overwrite it, or
        # pointing at a directory reports the wrong problem.
        if path.is_dir():
            raise CommandError(f'{path} is a directory; give me a filename, '
                               f'like {path}/{game.char.handle}.json')
        if path.exists() and not args.has('force'):
            raise CommandError(f'{path} already exists. `--force` to write '
                               f'over it.')
        try:
            written = save_mod.export_to(game.to_dict(), path)
        except save_mod.SaveError as e:
            # A bad path is the player's problem to fix, not a traceback.
            raise CommandError(str(e)) from None
        c.ok(f'Exported to {written}.')
        c.say(f'[dim]{game.char.handle}, {game.city.when}, '
              f'{game.char.runs} runs. `restore --import {written}` to bring '
              f'it back, here or anywhere else.[/]')
        return

    slot = args.get(0) or sess.slot
    path = game.save(slot)
    sess.slot = slot
    c.ok(f'Saved to {path}.')


@command('restore', 'Load a saved game.',
         group='session', bare=True,
         usage='restore [slot] [--import <path>] [--as <slot>]',
         detail='Named `restore` rather than `load` because `load` puts a '
                'program on your deck, which you will type far more often. '
                '`--import <path>` opens a save exported from anywhere, on '
                'this machine or another one, and `--as <slot>` says which '
                'slot to file it under.')
def cmd_restore(sess, args) -> None:
    c = sess.console
    if sess.run is not None:
        raise CommandError('finish the run first.')

    source = args.opt('import')
    if source is not None:
        try:
            data = save_mod.import_from(pathlib.Path(source))
        except save_mod.SaveError as e:
            raise CommandError(str(e)) from None
        slot = args.opt('as') or 'imported'
        if save_mod.exists(slot) and not args.has('force'):
            raise CommandError(
                f'slot {slot!r} already has a character in it. '
                f'`--as <another slot>`, or `--force` to write over them.')
        save_mod.write(data, slot)
        sess.load_game(slot)
        game = sess.game
        c.ok(f'{game.char.handle} is here, filed under {slot!r}.')
        from .guide import previously
        previously(sess)
        c.say(f'[dim]{game.city.when}, {game.city.district.name}, '
              f'{game.char.runs} runs, running as {game.alias.name}.[/]')
        if game.over:
            c.warn(f'This character is finished: {game.over}')
        return

    slots = save_mod.slots()
    if not slots:
        raise CommandError('no saves found.')
    slot = args.get(0)
    if slot is None:
        if len(slots) == 1:
            slot = slots[0]
        else:
            raise CommandError(f'which one: {", ".join(slots)}')
    sess.load_game(slot)
    game = sess.game
    sess.console.ok(f'{game.char.handle}, running as [accent]'
                    f'{game.alias.name}[/]. {game.city.when}, '
                    f'{game.city.district.name}.')
    if game.over:
        sess.console.warn(f'This character is finished: {game.over}')
        return
    _coming_back(sess)


def _coming_back(sess) -> None:
    """What a player who has been away needs to know before `now` (D163):
    the job they are on and when it dies, the money somebody is coming
    for, the animal, the construct, the crew. `restore` used to say the
    time and the district and leave the rest to be found out the hard way."""
    from ..content import pets as pet_content
    game, c = sess.game, sess.console
    lines: list[str] = []
    cur = game.city.current
    if cur is not None:
        left = int(cur.expires) - int(game.city.shift)
        lines.append(f'On {cur.title}, in {districts.BY_KEY[cur.district].name}, '
                     + (f'{left} shift{"s" if left != 1 else ""} left on it.'
                        if left > 0 else 'and it has expired.'))
    if game.debt.owed:
        lines.append(f'{fac_short(game.debt.lender)} are owed '
                     f'{game.debt.amount:,}c, and they collect.')
    if game.city.pet:
        animal = pet_content.BY_KEY.get(game.city.pet.get('key', ''))
        name = game.city.pet.get('name', animal.name if animal else 'it')
        m = pet_content.mood(game.city.pet)
        need = pet_content.worst_need(game.city.pet)
        lines.append(f'{name} is '
                     + ('fine.' if m in ('content', 'ok')
                        else f'not fine: it needs {need}.'))
    fam = game.char.deck.familiar or {}
    if fam and int(fam.get('charge', pet_content.FAMILIAR_FULL)) <= 0:
        lines.append(f'{fam.get("name", "The familiar")} is dormant. `familiar tend`.')
    if game.city.crew:
        lines.append(f'{game.city.crew.get("name", "Somebody")} is crewed with you.')
    if lines:
        c.blank()
        for line in lines:
            c.say(f'[dim]{line}[/]', indent='  ', subsequent='  ')
    c.say('[dim]`now` for the next move, `journal` for where the stories stand.[/]')


# --------------------------------------------------------------------------
# the roster
# --------------------------------------------------------------------------


def _roster_rows(sess, entries):
    """One table of characters, marking whoever is loaded."""
    here = sess.slot if sess.game is not None else None
    rows = []
    for n, e in enumerate(entries, 1):
        if e.broken:
            rows.append((str(n), f'[err]{e.slot}[/]', '[err]unreadable[/]',
                         '', '', '[dim]-[/]'))
            continue
        mark = '[accent]you[/]' if e.slot == here else ''
        if e.finished:
            mark = f'[dim]{e.over}[/]' if not mark else f'[warn]{e.over}[/]'
        rows.append((
            str(n),
            e.handle,
            origins.BY_KEY[e.origin].name if e.origin in origins.BY_KEY
            else e.origin,
            f'day {e.day}, {e.phase}',
            f'{e.runs} run{"s" if e.runs != 1 else ""}, {e.credits:,}c',
            mark or '[dim]waiting[/]'))
    return rows


@command('characters', 'Everybody you have made.',
         aliases=('chars', 'roster'), group='session', bare=True,
         usage='characters',
         detail='Characters are filed under their own handle, so making a '
                'second one does not touch the first. `switch <handle>` to '
                'pick one up, `delete <handle>` to lose one on purpose. This '
                'is the only screen that lists them, and it lists the '
                'finished ones too, because a roster you can only see the '
                'living on quietly deletes your history the moment it stops '
                'being useful.')
def cmd_characters(sess, args) -> None:
    c = sess.console
    entries = save_mod.roster()
    if not entries:
        c.info('Nobody yet. `new` to see the origins.')
        return
    c.header('Characters', f'{len(entries)} of them')
    c.table(('#', 'handle', 'origin', 'when', 'done', ''),
            _roster_rows(sess, entries),
            roles=('accent', 'accent', 'dim', None, 'dim', None))
    # Slots rather than handles, so that two runners who share a handle are
    # still two different row numbers.
    sess.remember('characters', [e.slot for e in entries])
    c.blank()
    if any(e.broken for e in entries):
        c.say('[err]One of these will not open.[/] [dim]It is still on disk; '
              'nothing here has thrown it away.[/]')
    living = [e for e in entries if not e.finished and not e.broken]
    other = [e for e in living if sess.game is None or e.slot != sess.slot]
    if other:
        after = ('Whoever you are now is saved first.' if sess.game is not None
                 else 'Nobody is loaded at the moment.')
        c.say(f'[dim]`switch {other[0].handle}` to pick somebody up. '
              f'{after}[/]')
    else:
        c.say('[dim]`new <handle> --origin <key>` to make another. Nobody '
              'here is written over by it.[/]')


@command('switch', 'Put this character down and pick up another.',
         group='session', bare=True, usage='switch <handle>',
         detail='Saves whoever you are before loading whoever you asked for, '
                'so switching is never how you lose somebody. Refuses during '
                'a run, because there is no coherent thing to do with a '
                'connection that is still open.')
def cmd_switch(sess, args) -> None:
    c = sess.console
    if sess.run is not None:
        raise CommandError('finish the run first.')
    want = args.get(0)
    if want is None:
        raise CommandError('switch to whom? `characters` for the list.')
    want = sess.pick('characters', want,
                     fallback=[e.slot for e in save_mod.roster()],
                     what='row', again='characters')

    found = save_mod.find(want)
    if not found:
        known = ', '.join(e.handle for e in save_mod.roster()[:6])
        raise CommandError(f'no character called {want!r}'
                           + (f'. You have: {known}' if known else ''))
    if len(found) > 1:
        raise CommandError(
            f'{want!r} matches {len(found)}: '
            + ', '.join(f'{e.handle} ({e.slot})' for e in found)
            + '. Use the one in brackets.')
    target = found[0]
    if target.broken:
        raise CommandError(f'{target.slot} will not open: {target.broken}')
    if sess.game is not None and target.slot == sess.slot:
        raise CommandError(f'you are already {sess.game.char.handle}.')

    if sess.game is not None:
        leaving = sess.game.char.handle
        sess.sync_scripts()
        sess.game.save(sess.slot)
        c.info(f'{leaving} is saved.')
    sess.load_game(target.slot)
    game = sess.game
    c.ok(f'You are [accent]{game.char.handle}[/], running as '
         f'[accent]{game.alias.name}[/].')
    if game.over:
        c.warn(f'This character is finished: {game.over}')
    else:
        from .guide import previously
        previously(sess)


@command('delete', 'Lose a character on purpose.',
         group='session', bare=True, usage='delete <handle> --confirm',
         detail='The only thing in this game that removes a character. It '
                'says what it is about to throw away and then needs '
                '`--confirm`, because there is no undo and no second copy: '
                'nothing else, including `new`, touches a save that is not '
                'the one you are playing.')
def cmd_delete(sess, args) -> None:
    c = sess.console
    want = args.get(0)
    if want is None:
        raise CommandError('delete whom? `characters` for the list.')
    want = sess.pick('characters', want,
                     fallback=[e.slot for e in save_mod.roster()],
                     what='row', again='characters')
    found = save_mod.find(want)
    if not found:
        raise CommandError(f'no character called {want!r}.')
    if len(found) > 1:
        raise CommandError(
            f'{want!r} matches {len(found)}: '
            + ', '.join(f'{e.handle} ({e.slot})' for e in found)
            + '. Use the one in brackets.')
    target = found[0]

    if not args.has('confirm'):
        c.blank()
        c.say(f'[warn]This throws {target.handle} away.[/]')
        if target.broken:
            c.say('[dim]The save will not open, so this is all that is known '
                  'about it.[/]')
        else:
            c.kv([('handle', target.handle),
                  ('running as', target.alias),
                  ('when', f'day {target.day}, {target.phase}'),
                  ('runs', str(target.runs)),
                  ('credits', f'{target.credits:,}c'),
                  ('dissonance', str(target.dissonance))])
            if target.finished:
                c.say(f'[dim]Already finished: {target.over}.[/]')
        c.blank()
        c.say(f'[dim]`delete {target.handle} --confirm` to go through with '
              f'it. There is no undo.[/]')
        return

    was_current = sess.game is not None and target.slot == sess.slot
    save_mod.delete(target.slot)
    c.ok(f'{target.handle} is gone.')
    if was_current:
        sess.game = None
        sess.run = None
        sess.slot = 'default'
        left = [e for e in save_mod.roster() if not e.broken]
        if left:
            c.say(f'[dim]`switch {left[0].handle}` for somebody else, or '
                  f'`new` to start again.[/]')
        else:
            c.say('[dim]Nobody left. `new` to see the origins.[/]')


@command('reset', 'Start over: every character gone, the meta layer too.',
         group='character', bare=True,
         usage='reset --confirm [--keep-career]',
         detail='For testing, and for the rare evening you want the city to '
                'have never heard of you. Deletes every save slot and resets '
                'the meta layer (career counters, rice unlocks, what the '
                'departed left) to new. `--keep-career` deletes the '
                'characters and keeps the meta, which is the terminal you '
                'earned and the estates waiting to be claimed. Without '
                '`--confirm` it only says what would go. There is no undo: '
                '`save --export` first if any of them matter.')
def cmd_reset(sess, args) -> None:
    c = sess.console
    entries = save_mod.roster()
    meta = save_mod.read_meta()
    keep = args.has('keep-career')
    if not args.has('confirm'):
        c.header('Reset', 'what would go')
        if entries:
            c.say(f'{len(entries)} character{"s" if len(entries) != 1 else ""}: '
                  + ', '.join(e.handle for e in entries) + '.')
        else:
            c.say('[dim]No characters.[/]')
        c.say('[dim]The meta layer: '
              f'{int(meta.get("characters_created", 0))} created, '
              f'{int(meta.get("runs_completed", 0))} runs, the shell you have '
              f'earned, and anything the departed left.[/]'
              if not keep else '[dim]The meta layer stays (--keep-career).[/]')
        c.blank()
        c.say('[warn]`reset --confirm` to do it, `reset --confirm '
              '--keep-career` to keep the terminal and the estates. No undo; '
              '`save --export` first if any of them matter.[/]')
        return
    for slot in save_mod.slots():
        save_mod.delete(slot)
    if not keep:
        save_mod.write_meta(dict(save_mod.META_DEFAULT))
    sess.game = None
    sess.run = None
    sess.slot = 'default'
    sess.apply_shell()
    c.ok('Fresh. The city has never heard of you.')
    c.say('[dim]`new` to start.[/]')


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
         group='info', aliases=('tech',), usage='techniques')
def cmd_techniques(sess, args) -> None:
    game = sess.require_game()
    c = sess.console
    have = game.char.techniques()
    c.header('Techniques', f'{len(have)} of {len(skill_content.TECHNIQUES)}')
    if not have:
        c.say('[dim]None yet. Ranks 2 and 4 of every skill unlock one.[/]')
        return
    for tech in have:
        verb = tech.verb or 'no new verb: it changes what happens'
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
        before = sess.tutorial_step
        sess.tutorial_advance()
        # advance() shows whatever step it lands on, so showing here as well
        # would print the same instruction twice for anybody who already
        # satisfied a step before asking: the common case, since having a
        # character at all completes the first one. Only print when there was
        # nothing to advance past.
        if sess.tutorial_step == before:
            sess.tutorial_show()
        return

    c.info(f'Step {sess.tutorial_step + 1} of {len(tutorial.STEPS)}.')
    sess.tutorial_show()


@command('title', 'The cold start, again.',
         group='session', bare=True, usage='title [--still]',
         detail='Runs the boot sequence. `--still` prints the last frame '
                'without the animation, which is also what happens '
                'automatically when output is not a terminal, when colour is '
                'off, or when FLATLINE_NO_INTRO is set. Ctrl-C during it '
                'means "get on with it" rather than "quit".')
def cmd_title(sess, args) -> None:
    anim.boot(sess.console,
              char=sess.game.char if sess.game else None,
              quick=args.has('still'),
              style=sess.shell.get('banner', 'block'))


# --------------------------------------------------------------------------
# the shell
# --------------------------------------------------------------------------


#: Roles worth showing in a preview. Enough to tell two schemes apart at a
#: glance, few enough to fit beside a name.
SWATCH_ROLES = ('accent', 'accent2', 'ok', 'warn', 'err', 'info',
                'trace', 'residue', 'credit', 'muted')


def _swatch(c, palette) -> str:
    """One palette, as a row of its own colours.

    Emits raw sequences rather than role markup, which is the whole trick: a
    swatch written as `[accent]` renders in the palette currently in use, so
    every scheme in the list looked identical to the one already on.
    """
    block = c.caps.g('bar_full') * 2
    if c.caps.color is ui.ColorLevel.NONE:
        return ''
    out = []
    for role in SWATCH_ROLES:
        colour = getattr(palette, role)
        out.append(anim._fg(colour.rgb, c.caps, colour.ansi) + block)
    return ''.join(out) + anim.RESET


def _rice_index(sess) -> None:
    """Everything, what is on, and what is still out there."""
    c = sess.console
    meta = save_mod.read_meta()
    look = sess.shell
    c.header('The shell', 'yours, not the character\'s')
    c.say('[dim]The city takes everything else. It does not get this: what '
          'you set here survives a flatline and follows you into the next '
          'one.[/]')

    for kind in rice.KINDS:
        items = rice.BY_KIND[kind]
        have = [i for i in items if rice.met(i, meta)]
        c.blank()
        c.rule(f'{kind}  {len(have)}/{len(items)}')
        for item in items:
            earned = rice.met(item, meta)
            worn = look.get(kind) == item.key
            mark = ('[ok]' + c.caps.g('check') + '[/]' if worn
                    else ' ' if earned else '[dim]' + c.caps.g('lock') + '[/]')
            if not earned:
                left = rice.progress(item, meta)
                c.raw(f'  {mark} [dim]{item.name:<16}[/] '
                      f'[dim]({left})[/]')
                c.say(f'[dim]{item.hint}[/]', indent='     ', subsequent='     ')
                continue
            tail = ''
            if kind == 'palette':
                tail = '  ' + _swatch(c, theme.get(item.key))
            elif kind == 'prompt':
                tail = f'  [dim]{prompt_mod.BY_KEY[item.key].sample}[/]'
            elif kind in ('frame', 'bars', 'marks'):
                tail = '  [dim]' + _sample_glyphs(c, kind, item.key) + '[/]'
            elif kind == 'banner':
                tail = f'  [dim]{anim.BANNERS[item.key].blurb}[/]'
            role = 'accent' if worn else 'fg'
            c.raw(f'  {mark} [{role}]{item.name:<16}[/]{tail}')

    c.blank()
    c.say('[dim]`rice <kind> <name>` to wear one, `rice <kind>` to see just '
          'that set, `rice --reset` to go back to standard.[/]')


def _sample_glyphs(c, kind: str, key: str) -> str:
    """A one-line preview of a frame, bar or mark set."""
    caps = c.caps
    probe = ui.Caps(color=caps.color, glyphs=caps.glyphs, width=caps.width,
                    palette=caps.palette,
                    frame=key if kind == 'frame' else caps.frame,
                    bars=key if kind == 'bars' else caps.bars,
                    marks=key if kind == 'marks' else caps.marks)
    if kind == 'frame':
        # Top and bottom of a box, side by side. The first attempt ran a
        # top-left corner into a bottom-right one and read as a broken frame
        # rather than as a sample of an intact one.
        top = probe.g('corner_tl') + probe.g('hline') * 5 + probe.g('corner_tr')
        bottom = (probe.g('corner_bl') + probe.g('hline') * 5
                  + probe.g('corner_br'))
        return f'{top} {bottom}'
    if kind == 'bars':
        return probe.g('bar_full') * 7 + probe.g('bar_empty') * 5
    return ' '.join(probe.g(n) for n in
                    ('bullet', 'arrow', 'check', 'cross', 'node'))


def _rice_gallery(sess, kind: str) -> None:
    """Every palette you own, rendered live and side by side (D106).

    `rice --preview` shows the shell you are wearing. This shows the same
    handful of real lines under every scheme you have earned, because the
    only honest way to choose between colours is to see them next to each
    other rendering the actual game, not a swatch.
    """
    c = sess.console
    meta = save_mod.read_meta()
    look = sess.shell
    if kind and kind not in rice.KINDS:
        match = [k for k in rice.KINDS if k.startswith(kind)]
        kind = match[0] if len(match) == 1 else 'palette'
    kind = kind or 'palette'
    if c.caps.color is ui.ColorLevel.NONE:
        raise CommandError('a gallery of colours needs a colour terminal. '
                           '`rice` lists what you have.')
    earned = [i for i in rice.BY_KIND[kind] if rice.met(i, meta)]
    c.header('The gallery', f'{kind}, {len(earned)} yours')
    c.say('[dim]The same lines, in every one you own. `rice ' + kind
          + ' <name>` wears one.[/]')
    for item in earned:
        was = c.caps
        pal = theme.get(item.key if kind == 'palette' else look.get('palette'))
        c.caps = ui.Caps(
            color=was.color, glyphs=was.glyphs, width=was.width, palette=pal,
            frame=item.key if kind == 'frame' else look.get('frame', 'single'),
            bars=item.key if kind == 'bars' else look.get('bars', 'blocks'),
            marks=item.key if kind == 'marks' else look.get('marks', 'plain'))
        try:
            worn = look.get(kind) == item.key
            c.blank()
            c.raw(f'[accent]{item.name}[/]'
                  + (' [dim](worn)[/]' if worn else ''))
            if kind == 'prompt':
                # The one axis a status line does not show: render the
                # prompt itself, in a run, so the gallery of prompts is a
                # gallery of prompts.
                line = prompt_mod.sample_run(item.key, c.caps)
                c.raw(f'  [dim]{line}[/]scan --quiet')
            else:
                c.raw('  ' + c.bar(0.62, 'trace', 18, 'trace 62/100')
                      + '   [warn]AMBER[/]')
                c.raw('  [ok]' + c.caps.g('check') + ' ice down[/]  '
                      '[err]black ICE[/]  [accent]ap-arc21[/]  '
                      '[credit]4,200c[/]  [residue]18 residue[/]')
        finally:
            c.caps = was


def _preview(sess, look: dict) -> None:
    """Render a slice of real output under a shell the player has not worn yet.

    Done by swapping the console's capabilities for the duration rather than
    by emitting colours directly, which means the sample goes through exactly
    the same wrap, markup and glyph path as the game does. A preview drawn any
    other way is a preview of the preview.
    """
    c = sess.console
    was = c.caps
    c.caps = ui.Caps(color=was.color, glyphs=was.glyphs, width=was.width,
                     palette=theme.get(look.get('palette')),
                     frame=look.get('frame', 'single'),
                     bars=look.get('bars', 'blocks'),
                     marks=look.get('marks', 'plain'))
    try:
        c.blank()
        c.rule('preview')
        c.header('ap-arc21', 'tick 14')
        c.raw('  ' + c.bar(0.62, 'trace', 22, 'trace 62/100'))
        c.raw('  ' + c.bar(0.25, 'noise', 22, 'noise 5 here'))
        c.kv([('alert', '[warn]amber[/] [dim]something has been noticed[/]'),
              ('residue', '[residue]18 across the network[/]'),
              ('haul', '[credit]4,200c[/] nominal')])
        c.ok('Ice down. Nothing else moved.')
        c.warn('The trace is past halfway.')
        c.err('Black ICE. It has your signature and it is not in a hurry.')
        c.info('`jack out` to leave with what you have.')
        # The panel above is a run, so the prompt under it has to be one. The
        # live prompt would be whatever the session is actually in, which for
        # somebody browsing the catalogue with no character loaded is the
        # bare form: a preview of a run screen with a title-screen prompt on
        # the bottom of it.
        style = look.get('prompt', 'classic')
        line = (prompt_mod.render(sess, style) if sess.run is not None
                else prompt_mod.sample_run(style, c.caps))
        c.raw(f'  [dim]{line}scan --quiet[/]')
        c.rule()
    finally:
        c.caps = was


@command('rice', 'Customise the shell. Earned, and yours to keep.',
         group='session', bare=True, aliases=('shell',),
         usage='rice [[kind] [[name] [[gallery] [[--try] [[--preview] [[--reset]',
         detail='Eight axes: palette, prompt, frame, bars, marks, banner, '
                'hud, render. Most '
                'of them are earned by playing, and everything you earn is '
                'recorded outside the save, so it survives the character who '
                'earned it.\n\n'
                'Nothing here touches a single number in the game. That is '
                'the point of it: after four hours of a city that does not '
                'care whether you live, a colour scheme should be free.\n\n'
                '`rice <kind> <name> --try` shows you a screen of real output '
                'in it without keeping it, `rice --preview` does the same '
                'for what you are already wearing, and `rice gallery [[kind]` '
                'renders the same lines under every one you own at once.')
def cmd_rice(sess, args) -> None:
    c = sess.console
    meta = save_mod.read_meta()

    if args.has('reset'):
        meta['shell'] = {}
        save_mod.write_meta(meta)
        sess.apply_shell()
        c.ok('Back to standard.')
        return

    # Before the no-argument branch: `rice --preview` has no positionals, so
    # testing the argument count first meant the flag could never be reached.
    if args.has('preview'):
        _preview(sess, sess.shell)
        return

    if not len(args):
        _rice_index(sess)
        return

    if (args.get(0) or '').lower() in ('gallery', 'showcase', 'all'):
        _rice_gallery(sess, (args.get(1) or '').lower())
        return

    kind = (args.get(0) or '').lower()
    matches = [k for k in rice.KINDS if k.startswith(kind)]
    if len(matches) != 1:
        raise CommandError(f'no such setting: {kind!r}. '
                           f'One of: {", ".join(rice.KINDS)}.')
    kind = matches[0]

    choice = (args.get(1) or '').lower()
    if not choice:
        _rice_kind(sess, kind)
        return

    options = rice.BY_KIND[kind]
    hit = next((i for i in options
                if i.key == choice or i.name.lower().startswith(choice)), None)
    if hit is None:
        _rice_kind(sess, kind)
        raise CommandError(f'no {kind} called {choice!r}.')
    if not rice.met(hit, meta):
        raise CommandError(f'{hit.name} is not yours yet. {hit.hint} '
                           f'[dim]({rice.progress(hit, meta)})[/]')

    shell = dict(meta.get('shell') or {})
    shell[kind] = hit.key

    if args.has('try'):
        # Wear it for one screen without keeping it. The most useful thing a
        # customisation menu can do is let you look before you decide.
        c.say(f'[dim]{hit.name}, not saved. '
              f'`rice {kind} {hit.key}` to keep it.[/]')
        _preview(sess, {**sess.shell, kind: hit.key})
        return

    meta['shell'] = shell
    save_mod.write_meta(meta)
    sess.apply_shell()
    c.ok(f'{kind}: {hit.name}.')
    c.say(f'[dim]{hit.blurb}[/]')
    if kind == 'palette':
        c.blank()
        c.raw('  ' + _swatch(c, theme.get(hit.key)))
    if kind == 'banner':
        c.blank()
        anim.boot(sess.console, char=sess.game.char if sess.game else None,
                  quick=True, style=hit.key)


def _rice_kind(sess, kind: str) -> None:
    """One axis, in full, with everything it can look like."""
    c = sess.console
    meta = save_mod.read_meta()
    look = sess.shell
    items = rice.BY_KIND[kind]
    c.header(kind, f'{sum(1 for i in items if rice.met(i, meta))}/{len(items)}')
    for item in items:
        earned = rice.met(item, meta)
        worn = look.get(kind) == item.key
        c.blank()
        head = ('[ok]' + c.caps.g('check') + '[/] ' if worn
                else '[dim]' + c.caps.g('lock') + '[/] ' if not earned
                else '  ')
        role = 'accent' if earned else 'dim'
        c.raw(f'{head}[{role}][bold]{item.name}[/][/]  [dim]{item.key}[/]')
        c.say(f'[dim]{item.blurb}[/]', indent='   ', subsequent='   ')
        if not earned:
            c.say(f'[warn]{item.hint}[/] [dim]({rice.progress(item, meta)})[/]',
                  indent='   ', subsequent='   ')
            continue
        if kind == 'palette':
            c.raw('   ' + _swatch(c, theme.get(item.key)))
        elif kind == 'prompt':
            c.raw(f'   [dim]{prompt_mod.BY_KEY[item.key].sample}[/]')
        elif kind in ('frame', 'bars', 'marks'):
            c.raw('   [dim]' + _sample_glyphs(c, kind, item.key) + '[/]')
        elif kind == 'banner':
            for row in anim.banner_preview(item.key, c.caps):
                c.raw('   ' + row)
        elif kind == 'hud':
            bullet = c.caps.g('bullet')
            tail = (f' [dim]{bullet} noise 6 {bullet} tick 9 {bullet} '
                    f'alert green[/]')
            if item.key == 'line':
                c.raw('   ' + c.bar(0.23, 'trace', 12, 'trace 23/100') + tail)
            elif item.key == 'bar':
                c.raw('   ' + c.bar(0.23, 'trace', 12, 'trace 23/100'))
            elif item.key == 'terse':
                c.raw('   [trace]trace 23/100[/]' + tail)
            else:
                c.raw('   [dim](nothing; the prompt carries the trace)[/]')
    c.blank()
    c.say(f'[dim]`rice {kind} <name>` to wear one.[/]')


@command('career', 'Everything you have done, across every character.',
         group='session', bare=True, aliases=('legacy',), usage='career',
         detail='The save holds one runner. This holds all of them: how many '
                'you have started, how many you have lost, how far any of '
                'them got. It is also what the shell catalogue unlocks '
                'against, which is why the two live in the same file and why '
                'neither of them dies with a character.')
def cmd_career(sess, args) -> None:
    c = sess.console
    meta = save_mod.read_meta()
    made = int(meta.get('characters_created') or 0)
    lost = int(meta.get('flatlines') or 0)
    runs = int(meta.get('runs_completed') or 0)
    clean = int(meta.get('clean_runs') or 0)

    c.header('Career', 'across everybody')
    if not made:
        c.say('[dim]Nothing yet. `new` to make somebody.[/]')
        return

    c.kv([
        ('runners', f'{made} started'
                    + (f', [err]{lost} lost[/]' if lost else
                       ', [dim]none lost[/]')),
        ('contracts', f'{runs}'
                      + (f'  [dim]{clean} with nobody ever knowing '
                         f'({clean * 100 // max(1, runs)}%)[/]' if runs
                         else '')),
        ('richest', f'[credit]{int(meta.get("best_credits") or 0):,}c[/] '
                    f'[dim]held at once[/]'),
        ('deepest', f'{int(meta.get("deepest_drift") or 0)} Dissonance'),
        ('seen', f'{int(meta.get("districts_seen") or 0)} of '
                 f'{len(districts.DISTRICT_KEYS)} districts'),
        ('best standing', f'{int(meta.get("best_standing") or 0)} '
                          f'[dim]with anybody[/]'),
    ])

    marks = []
    if meta.get('black_ice_survived'):
        marks.append('met black ICE and walked away from it')
    if meta.get('bounties_taken'):
        marks.append('been worth money to somebody')
    if meta.get('threads_closed'):
        marks.append(f'{int(meta["threads_closed"])} storylines carried '
                     f'somewhere')
    if marks:
        c.blank()
        c.bullets(marks, role='dim')

    have = len(rice.unlocked(meta))
    c.blank()
    c.rule('the shell')
    c.raw('  ' + c.bar(have / len(rice.COSMETICS), 'accent', 24,
                       f'{have}/{len(rice.COSMETICS)} unlocked'))
    close = sorted(
        ((int(rice.progress(item, meta).split('/')[0]) / item.needs[1], item)
         for item in rice.COSMETICS if not rice.met(item, meta)
         and item.needs[1]),
        key=lambda pair: -pair[0])[:3]
    for share, item in close:
        c.raw(f'  [dim]{item.name:<16} {item.kind:<8} '
              f'{rice.progress(item, meta)}[/]')
    if close:
        c.say('[dim]`rice` for the rest of it.[/]')

    if lost:
        c.blank()
        c.say('[dim]The shell is the only thing on this page that any of them '
              'got to keep.[/]')
