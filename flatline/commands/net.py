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
    game, c = sess.require_game(), sess.console
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
    for m in show:
        tag = '[warn]new[/] ' if m.id in new else ''
        role = {'ad': 'dim', 'nemesis': 'err', 'partner': 'ok', 'lender': 'heat',
                'bounty': 'heat'}.get(m.kind, 'accent')
        c.say(f'[dim]{bullet}[/] {tag}[{role}]{m.sender}[/]: {m.text}'
              + (f' [dim]`{m.do}`[/]' if m.do else ''), subsequent='  ')
    deck_world.mark_read(game, [m.id for m in show])


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
    game, c = sess.require_game(), sess.console
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
    game, c = sess.require_game(), sess.console
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
        hit = deck_world.lookup(' '.join(args.rest().split()[1:]))
        if hit is None or hit[1].key not in watches:
            raise CommandError('you are not watching that. `watch` lists them.')
        watches.remove(hit[1].key)
        c.ok(f'The deck stops watching for {hit[1].name}.')
        return
    hit = deck_world.lookup(args.rest())
    if hit is None:
        raise CommandError(f'the net has no catalogue entry called {args.rest()!r}.')
    kind, item = hit
    if item.key in watches:
        raise CommandError(f'already watching for {item.name}.')
    if len(watches) >= 6:
        raise CommandError('six is as many as the deck will watch for. '
                           '`watch drop <thing>` first.')
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
    game, c = sess.require_game(), sess.console
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
                'not, and they would like you to know they are aware of that.'))
def cmd_ads(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    c.header('Sponsored', game.city.when)
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
