"""The deck, in the city (D135): mail, search, watch, message, ads.

Five things a runner does with a deck that are not a run. Each has a
mechanical hook: search finds real stock, mail points at real work and
real debts, a watch saves a shift, a message moves a disposition, an ad
reads your state and says so.
"""

from __future__ import annotations

from ..content import districts
from ..content import feed
from ..shell import CommandError, command
from ..world import deck as deck_world


def _needs_deck(sess):
    """Every city verb on the deck reads its condition (D136)."""
    game = sess.require_game()
    if not deck_world.working(game.char):
        raise CommandError(deck_world.IN_PIECES)
    return game


@command('mail', 'What the deck has for you: the people who would message you.',
         group='info', contexts=('city',), usage='mail [all]',
         aliases=('inbox',),
         blocked='The deck is busy. Everything else can wait.',
         detail=(
                'The deck, in the city (D135). A partner checking in, a '
                'nemesis making a promise, a fixer with something physical, a '
                'lender with a reminder, a thread waiting on somebody, the pit '
                'asking after you, a number against your name, a thing you '
                'watch landing on a shelf, and an advertisement that has read '
                'you. New ones are marked; `mail` marks them read. Each line '
                'ends with the command that acts on it.'))
def cmd_mail(sess, args) -> None:
    game, c = _needs_deck(sess), sess.console
    every = deck_world.messages(game)
    new = {m.id for m in deck_world.unread(game)}
    show = every if (args.get(0) or '').lower() == 'all' or not new else \
        [m for m in every if m.id in new]
    c.header('The deck', f'{len(new)} new' if new else 'nothing new')
    if not every:
        c.say('[dim]Nobody has anything to say to you. Give it a shift.[/]')
        return
    if not new and (args.get(0) or '').lower() != 'all':
        c.say('[dim]Nothing new. `mail all` for everything the deck has.[/]')
        return
    bullet = c.caps.g('bullet')
    static = deck_world.damaged(game.char)
    for m in show:
        tag = '[warn]new[/] ' if m.id in new else ''
        if static:
            m.text = deck_world.garble(game, m.text)
        role = {'ad': 'dim', 'nemesis': 'err', 'partner': 'ok', 'lender': 'heat',
                'bounty': 'heat'}.get(m.kind, 'accent')
        c.say(f'[dim]{bullet}[/] {tag}[{role}]{m.sender}[/]: {m.text}'
              + (f' [dim]`{m.do}`[/]' if m.do else ''), subsequent='  ')
    deck_world.mark_read(game, [m.id for m in show])
    if static:
        c.say('[dim]The cpu has a level of damage and it shows. `repair`.[/]')


@command('search', 'Ask the net where a thing is sold this cycle.',
         group='info', contexts=('city',), usage='search <thing>',
         aliases=('locate', 'find'),
         blocked='Not in here. In here the net is the thing being searched.',
         detail=(
                'The net knows where things are sold. Name a program, a piece '
                'of chrome, a component, a drug, a weapon or armour and it says '
                'which shelves in the city have it this cycle and at what '
                'price, cheapest first; `walk` there. A one-of-a-kind thing is '
                'not sold, and the net says where people stop asking about it. '
                'A search for a gun is a record: Nightwatch attention, a '
                'point.'))
def cmd_search(sess, args) -> None:
    game, c = _needs_deck(sess), sess.console
    if not len(args):
        raise CommandError('search for what? A name. `search katana`, '
                           '`search plating`.')
    lines, note = deck_world.search(game, args.rest())
    for line in lines:
        c.say(line)
    if note:
        c.say(f'[heat]{note}[/]')


@command('watch', 'Have the deck tell you when a thing lands on a shelf.',
         group='info', contexts=('city',), usage='watch [<thing>|drop <thing>]',
         blocked='Later.',
         detail=(
                'A watch on a thing: whenever time moves and it is on a shelf '
                'somewhere in the city, the deck says where and for how much, '
                'once a cycle, and it is in `mail`. `watch` alone lists them; '
                '`watch drop <thing>` stops one. It is how a runner waiting for '
                'a smartgun to turn up does not walk to Freeport every day to '
                'look.'))
def cmd_watch(sess, args) -> None:
    game, c = _needs_deck(sess), sess.console
    watches = game.city.watches
    if not len(args):
        c.header('Watching', f'{len(watches)} thing{"s" if len(watches) != 1 else ""}')
        if not watches:
            c.say('[dim]Nothing. `watch <thing>` to start.[/]')
            return
        for key in watches:
            hit = deck_world._find_on_shelves(game, key)
            where = (f'on a shelf in {hit[0][0]}, [credit]{hit[0][1]:,}c[/]'
                     if hit else '[dim]nowhere this cycle[/]')
            c.say(f'  [accent]{deck_world._name(key)}[/]  {where}')
        return
    first = (args.get(0) or '').lower()
    if first in ('drop', 'stop', 'forget'):
        rest = ' '.join(args.rest().split()[1:])
        hit = deck_world.lookup(rest)
        if hit is None:
            hit = next(((k, i) for k, i in deck_world.matches(rest)
                        if i.key in watches), None)
        if hit is None or hit[1].key not in watches:
            raise CommandError('you are not watching that. `watch` lists them.')
        watches.remove(hit[1].key)
        c.ok(f'The deck stops watching for {hit[1].name}.')
        return
    hit = deck_world.lookup(args.rest())
    if hit is None:
        several = deck_world.ambiguous(args.rest())
        if several:
            raise CommandError(f'{args.rest()!r} could be: '
                               + ', '.join(i.name for _, i in several[:8])
                               + '. Watch for one of them.')
        raise CommandError(f'the net has no catalogue entry called {args.rest()!r}.')
    kind, item = hit
    if getattr(item, 'unique', False):
        # A watch that can never fire is a slot spent on nothing (D138).
        raise CommandError(f'{item.name} is one of a kind. It is not sold '
                           f'anywhere and no shelf will ever have it: '
                           f'`search {item.key}` for where people stop '
                           f'asking about it.')
    if item.key in watches:
        raise CommandError(f'already watching for {item.name}.')
    cap = deck_world.watch_capacity(game.char)
    if len(watches) >= cap:
        raise CommandError(f'{cap} is as many as this deck\'s memory will watch '
                           f'for. `watch drop <thing>` first, or more memory.')
    watches.append(item.key)
    c.ok(f'The deck watches for {item.name}. It says when it lands, once a '
         f'cycle, and it is in `mail`.')
    sess.autosave()


@command('message', 'Send a line to another runner, and see what comes back.',
         group='info', contexts=('city',), usage='message <runner> [<anything>]',
         aliases=('msg', 'ping'),
         blocked='Not from in here.',
         detail=(
                'A line to one of the other runners. What comes back is what '
                'they think of you: a partner answers "here, where?", somebody '
                'who owes you tells you something true about where they are, a '
                'stranger says "sure", somebody cold says "busy", somebody '
                'hostile tells you not to, and a nemesis lets you watch it show '
                'as read. Warm answers warm them a little; hostile ones cool. '
                'Once a shift each. `who` lists them.'))
def cmd_message(sess, args) -> None:
    game, c = _needs_deck(sess), sess.console
    if not len(args):
        raise CommandError('message who? `who` lists the other runners.')
    name = (args.get(0) or '').lower()
    rival = next((r for r in game.city.rivals
                  if r.key == name or r.name.lower().startswith(name)), None)
    if rival is None:
        raise CommandError(f'no runner called {name!r}. `who` lists them.')
    line, delta = deck_world.reply(game, rival)
    c.blank()
    c.say(f'[dim]to {rival.name}:[/] {args.rest()[len(args.get(0) or ""):].strip() or "..."}')
    c.say(f'[accent]{rival.name}[/]: {line}')
    if delta:
        c.say(f'[dim]{rival.name} {"+" if delta > 0 else ""}{delta}, {rival.band}.[/]')
    sess.autosave()


@command('ads', 'The advertising. It has read you.',
         group='info', contexts=('city',), usage='ads',
         blocked='The ads cannot reach you in here. Nothing else can either.',
         detail=(
                'Everything you do is loud and the city remembers, and so the '
                'ads know. They are targeted by what you actually did: shot at, '
                'hurt, drifting, a habit, a loud weapon, a debt, a name on the '
                'wall. One of them is in every `mail`. This shows three. They '
                'change nothing, which is the one thing on the deck that does '
                'not, and they would like you to know they are aware of that. They '
                'arrive whatever state the deck is in.'))
def cmd_ads(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    c.header('Sponsored', game.city.when)
    if not deck_world.working(game.char):
        # Deliberate (D138): every other verb on the deck is gated on the
        # hardware and this one is not, because the joke is the system.
        c.say('[dim]The deck is in pieces and the advertising is still '
              'arriving. Nobody has ever worked out how.[/]')
        c.blank()
    seen = set()
    for salt in ('', 'b', 'c'):
        ad = deck_world.ad_for(game, salt)
        if ad.key in seen:
            # Fillers are the ads for everybody: an ad that has read you
            # and got you wrong is worse than no ad.
            pool = [a for a in feed.ADS if a.when == 'any' and a.key not in seen]
            if not pool:
                break
            ad = deck_world._pick(game, pool, 'ad' + salt)
        seen.add(ad.key)
        c.say(f'[dim]{ad.sponsor}:[/] {ad.text}')
        c.blank()


@command('sweep', 'Read the street off the air: how rough, who is looking, what is here.',
         group='info', contexts=('city',), usage='sweep [<district>]',
         blocked='In here the network is the thing you are reading.',
         detail=(
                'The deck listens to the district (D136): how rough the street '
                'is at this hour and what tonight is, which factions here have '
                'your name near the top of a list, whether their people carry '
                'chrome (whether `jack` has anything to reach in a fight), '
                'whether the Nightwatch is on the street, which postings on '
                'the board are for networks here, and who keeps hours here. '
                'With an antenna above the first tier it reads districts a '
                'shift or two away as well. Listening is not a record.'))
def cmd_sweep(sess, args) -> None:
    from ..content import districts
    game, c = _needs_deck(sess), sess.console
    key = game.city.where
    if len(args):
        key = districts.resolve(args.rest()) if hasattr(districts, 'resolve') else None
        if key is None:
            q = args.rest().lower()
            key = next((d.key for d in districts.DISTRICTS
                        if d.key.startswith(q) or d.name.lower().startswith(q)
                        or q in d.name.lower()), None)
        if key is None:
            raise CommandError('no district by that name. `map` lists them.')
        if not deck_world.in_reach(game, key):
            r = deck_world.reach(game.char)
            raise CommandError(f'{districts.BY_KEY[key].name} is past the antenna\'s '
                               f'reach ({r} shift{"s" if r != 1 else ""}). A '
                               f'longer antenna, or walk.')
    c.header('Sweep', game.city.when)
    for line in deck_world.sweep(game, key):
        c.say(line)


@command('route', 'Plan the walk: each hop, the hour you reach it, and the street then.',
         group='info', contexts=('city',), usage='route <district>',
         blocked='Later.',
         detail=(
                'The deck plans a walk (D136): the districts in order, the hour '
                'you will arrive in each, how rough its street will be at that '
                'hour, and who there is looking for your name. It is `walk` '
                'previewed, so the runner who would rather cross the Shambles '
                'in the morning can see that they will not.'))
def cmd_route(sess, args) -> None:
    from ..content import districts
    game, c = _needs_deck(sess), sess.console
    if not len(args):
        raise CommandError('route where? `map` lists the districts.')
    q = args.rest().lower()
    key = next((d.key for d in districts.DISTRICTS
                if d.key.startswith(q) or d.name.lower().startswith(q)
                or q in d.name.lower()), None)
    if key is None:
        raise CommandError('no district by that name. `map` lists them.')
    if key == game.city.where:
        raise CommandError('you are there.')
    rows = deck_world.route(game, key)
    c.header('Route', f'{districts.BY_KEY[key].name}, {len(rows)} shift'
                      f'{"s" if len(rows) != 1 else ""}')
    c.table(('hop', 'arrive', 'the street then', 'looking for you'),
            [(name, phase, word, who or '[dim]nobody[/]') for name, phase, word, who in rows],
            roles=('accent', 'dim', 'warn', 'heat'))
    c.blank()
    c.say(f'[dim]`walk {key}` to go.[/]')


@command('tune', 'Tune into a district: the scene at this hour, and what is going round.',
         group='info', contexts=('city',), usage='tune [<district>]',
         blocked='In here you are the thing being listened to.',
         detail=(
                'The deck tunes into a district (D136): the scene at this hour, '
                'the street\'s line, and any rumour going round it, which is '
                'how one-of-a-kind things are found, because the rumour is the '
                'only breadcrumb there is. With an antenna above the first '
                'tier it hears districts a shift or two away.'))
def cmd_tune(sess, args) -> None:
    from ..content import districts
    game, c = _needs_deck(sess), sess.console
    key = game.city.where
    if len(args):
        q = args.rest().lower()
        key = next((d.key for d in districts.DISTRICTS
                    if d.key.startswith(q) or d.name.lower().startswith(q)
                    or q in d.name.lower()), None)
        if key is None:
            raise CommandError('no district by that name. `map` lists them.')
        if not deck_world.in_reach(game, key):
            r = deck_world.reach(game.char)
            raise CommandError(f'{districts.BY_KEY[key].name} is past the antenna\'s '
                               f'reach ({r} shift{"s" if r != 1 else ""}).')
    c.header('Listening', districts.BY_KEY[key].name)
    for line in deck_world.listen(game, key):
        c.say(line)


@command('record', 'What the city can say about you: the work, the city, the people, the floor.',
         group='info', contexts=('any',), usage='record [work|city|people|floor]',
         aliases=('records',),
         detail=(
                'The record (D142). Four sections, because there are four '
                'reasons to play: what you have done with a deck, where you '
                'have been and what you found there, who knows you and how, '
                'and what you have done without a deck. Each line is a count '
                'against a target, and crossing one earns a name the city '
                'starts using, kept in the profile so it survives the '
                'character the way the terminal does. It is the screen that '
                'answers what is left.'))
def cmd_record(sess, args) -> None:
    from ..content import record as record_content
    from ..world import record as record_world
    from .. import save as save_mod
    c = sess.console
    game = sess.game
    meta = save_mod.read_meta()
    counts = record_world.counts(game, meta)
    done = {e.key for e in record_world.earned(counts)}
    want = (args.get(0) or '').lower()
    shown = [k for k in record_content.SECTION_KEYS
             if not want or k.startswith(want)]
    if not shown:
        raise CommandError('the sections are: '
                           + ', '.join(record_content.SECTION_KEYS))
    title = record_world.title_of(counts, meta.get('recorded'))
    c.header('The record', f'{len(done)} of {len(record_content.ENTRIES)}'
                           + (f'  {title}' if title else ''))
    for key, name, blurb in record_content.SECTIONS:
        if key not in shown:
            continue
        c.blank()
        c.rule(name.lower())
        c.say(f'[dim]{blurb}[/]')
        for e in record_content.BY_SECTION[key]:
            have = counts.get(e.counter, 0)
            got = e.key in done
            bar = c.bar(min(1.0, have / e.target), 'ok' if got else 'accent',
                        cells=8)
            num = (f'{have:,}/{e.target:,}' if e.target > 1
                   else ('yes' if have else 'not yet'))
            line = f'  {bar} [{"ok" if got else "fg"}]{e.name:<32}[/] [dim]{num}[/]'
            c.raw(line + (f'  [accent2]{e.title}[/]' if got and e.title else ''))
    c.blank()
    left = len(record_content.ENTRIES) - len(done)
    if left:
        c.say(f'[dim]{left} line{"s" if left != 1 else ""} to go. It keeps '
              f'counting across characters, like the terminal does.[/]')
    else:
        c.say(f'[accent2]{record_content.COMPLETE_LINE}[/]')
