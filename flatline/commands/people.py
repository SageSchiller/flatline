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
from ..content import offers
from ..content import threads as thread_content
from ..content import appearance
from ..content import districts
from ..content import shifts
from ..content import spots
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
    # This district at this hour, when somebody wrote it; the city-wide
    # shift scene otherwise (D53).
    c.say(districts.scene(district.key, game.city.phase) or when.scene)

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

    # What you have done to this place, standing in it. The city has always
    # remembered in the numbers; this is the first time it says so out here.
    posture = game.city.posture.get(district.controller, 0.0)
    watchers = (district.controller, *district.presence)
    attention = max((game.alias.attention(k) for k in watchers), default=0)
    for line in districts.mood(district, posture, attention):
        c.blank()
        c.say(f'[dim]{line}[/]')

    from .city import here_you_can
    here_you_can(sess, district, looking=True)
    _places_line(sess, district)

    # Who keeps other hours. Only people you have met, because "somebody you
    # have never seen is not here" is not information, and only the ones who
    # are away because of the clock rather than because of anything else.
    away = [n for n in story_mod.present(game, game.story, any_hour=True)
            if n not in here and n.key in game.story.met]

    c.blank()
    if not here:
        c.say('[dim]Nobody here is interested in you, which in this district '
              'is a mercy.[/]')
        _away_line(sess, away)
        return
    c.rule(f'{len(here)} worth talking to')

    for npc in here:
        first = game.story.meet(npc.key)
        c.blank()
        if first:
            c.raw(f'[accent2][bold]{npc.name}[/][/]  [dim]{npc.epithet}[/]')
            c.say(npc.first)
            _noticed(sess)
        else:
            c.raw(f'[accent]{npc.name}[/]  [dim]{npc.epithet}[/]')
    c.blank()
    c.say('[dim]`talk <name>` to say something. `ask <name> <topic>` if you '
          'want something specific.[/]')
    _away_line(sess, away)
    _check_story(sess)


def _away_line(sess, away) -> None:
    """Who keeps other hours, and which. One line, so the clock is a reason
    to come back rather than a door that was shut without saying so."""
    if not away:
        return
    c = sess.console
    c.blank()
    c.say('[dim]Not about at this hour: ' + ', '.join(
        f'{n.name} ({npc_content.hours_label(n)})' for n in away) + '.[/]',
          subsequent='  ')


def _noticed(sess) -> None:
    """What the person in front of you does about how you look.

    Occasional rather than every time, and only for the genuinely striking,
    because a city that remarks on you constantly is a city of very rude
    people. This is what stops `memorable` being a number the sheet prints
    and nothing else: a stranger's eyes going to the same place every time is
    the evidence for the claim.
    """
    game = sess.game
    said = appearance.remark(game.rng('events'), game.char.look,
                             game.char.marks, game.char.memorable)
    if said:
        sess.console.blank()
        sess.console.say(f'[dim]{said}[/]')


def _places_line(sess, district) -> None:
    """The places you can go and stand in, one line, typeable."""
    c = sess.console
    places = spots.in_district(district.key)
    if not places:
        return
    sess.remember('spots', [s.key for s in places])
    bullet = c.caps.g('bullet')
    c.say('[dim]Places:[/] ' + f' [dim]{bullet}[/] '.join(
        f'[fg]{s.name}[/]' for s in places)
          + ' [dim](`visit <place>`, which costs nothing)[/]', subsequent='  ')


@command('visit', 'Go and stand somewhere in this district.',
         group='city', contexts=('city',), aliases=('enter', 'goto'),
         usage='visit [place|row number]',
         blocked='The places are out there, and so, for the moment, is the '
                 'rest of you.',
         detail='A district has two or three places in it that a person '
                'would actually go and stand: the noodle bar, the west gate, '
                'the crate outside the clinic. `look` lists them. Visiting '
                'one costs nothing, because it is inside the district you are '
                'already in; it shows you the place as it is at this hour, '
                'and whoever is usually there if they are there now. The '
                'people are the same people and the verbs are the same verbs: '
                'this is texture, and texture is most of what makes somewhere '
                'feel like it goes on when you are not looking.',
         complete=lambda sess, prefix: [
             s.key for s in spots.in_district(sess.game.city.where)
         ] if sess.game else [])
def cmd_visit(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    district = game.city.district
    places = spots.in_district(district.key)
    if not places:
        raise CommandError('nowhere in particular to stand here. `look` for '
                           'who is about.')
    if not len(args):
        c.header(district.name, f'{len(places)} places')
        sess.remember('spots', [s.key for s in places])
        here = {n.key for n in story_mod.present(game, game.story)}
        for n, spot in enumerate(places, 1):
            who = [npc_content.BY_KEY[k].name for k in spot.who
                   if k in npc_content.BY_KEY and k in here]
            tail = f'  [dim]{", ".join(who)}[/]' if who else ''
            c.raw(f'  [accent]{n}[/]  [fg]{spot.name}[/]{tail}')
        c.blank()
        c.say('[dim]`visit <place>` or `visit <row number>`. It costs '
              'nothing.[/]')
        return

    token = sess.pick('spots', args.rest().lower(),
                      fallback=[s.key for s in places], what='place',
                      again='visit')
    spot = spots.find(district.key, token)
    if spot is None:
        raise CommandError(f'nowhere called {args.rest()!r} here. `visit` '
                           f'lists the places.')
    c.header(spot.name, district.name)
    c.say(spots.scene_for(spot, game.city.phase))
    here = {n.key for n in story_mod.present(game, game.story)}
    for key in spot.who:
        npc = npc_content.BY_KEY.get(key)
        if npc is None:
            continue
        c.blank()
        if key in here:
            first = game.story.meet(key)
            if first:
                c.raw(f'[accent2][bold]{npc.name}[/][/]  [dim]{npc.epithet}[/]')
                c.say(npc.first)
                _noticed(sess)
            else:
                c.raw(f'[accent]{npc.name}[/]  [dim]{npc.epithet}[/]')
                c.say(f'[dim]Here, as usual. `talk {npc.key}`.[/]')
        elif not npc_content.about_now(npc, game.city.phase):
            c.say(f'[dim]{npc.name} is not here at this hour. '
                  f'{npc_content.hours_label(npc).capitalize()}.[/]')
        else:
            c.say(f'[dim]{npc.name} is not here at the moment.[/]')
    _check_story(sess)


@command('news', 'What the city did while you were not looking.',
         group='info', contexts=('city',), aliases=('wire',),
         usage='news [count]',
         blocked='The wire is out there. In here there is only the trace.',
         detail='The city keeps a scrollback of what it did: who took what '
                'off the board, who posted a number against your name, who '
                'died on whose job, what expired, what you sold. Most of it '
                'printed once as it happened and scrolled away. This is where '
                'it went. It costs nothing.')
def cmd_news(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    count = args.int_at(0, 12, 'how many lines')
    lines = game.city.news[-max(1, count):]
    c.header('The wire', game.city.when)
    if not lines:
        c.say('[dim]Nothing has happened that anybody wrote down. Give it a '
              'shift.[/]')
        return
    bullet = c.caps.g('bullet')
    for line in lines:
        c.say(f'[dim]{bullet}[/] {line}', subsequent='  ')
    if len(game.city.news) > len(lines):
        c.blank()
        c.say(f'[dim]`news {len(game.city.news)}` for all of it.[/]')


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
    _noticed(sess)
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
    c.kv([('found', where),
          ('about', npc_content.hours_label(npc)),
          ('offers', ', '.join(npc.offers))])
    live = [o for o in npc.offers if o != 'nothing']
    if live:
        c.blank()
        bits = []
        if [o for o in live if o != 'intel']:
            bits.append(f'`deal {npc.key}` for the business')
        if 'intel' in live and npc.topics:
            bits.append(f'`ask {npc.key} <topic>` for what they know')
        c.say('[dim]' + ', and '.join(bits) + '.[/]')


# --------------------------------------------------------------------------
# business
# --------------------------------------------------------------------------
#
# `Npc.offers` declared work, goods and favours for the whole life of the cast
# and `who is` printed the list, and none of the three did anything. This is
# where they became real. See `content/offers.py` for why they are one system
# and not three.


def _owed(game, key: str) -> int:
    return int(game.story.owed.get(key, 0))


def _standing(game, npc) -> str:
    """Where you are with somebody, in a phrase rather than a number."""
    owed = _owed(game, npc.key)
    if owed <= 0:
        return 'square'
    if owed >= offers.OWED_LIMIT:
        return 'as deep as they will let you get'
    return f'{owed} favour{"s" if owed != 1 else ""} down'


@command('deal', 'Do business with somebody you have met.',
         group='city', contexts=('city',), usage='deal [name] [work|goods|favour]',
         detail='The three things a person will do for you that a shop will '
                'not. `who is <name>` lists which of them they offer. Work is '
                'a contract that never reaches the board and pays better for '
                'it. Goods are what they keep under their own counter, which '
                'does not rotate with the market. A favour is them spending '
                'their own standing on your problem, and it goes on a tab: '
                'finishing work they gave you is how it comes off again.')
def cmd_deal(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if not len(args):
        _deal_index(sess)
        return
    npc = _find(sess, args[0])
    kind = (args.get(1) or '').lower()
    if not kind:
        _deal_person(sess, npc)
        return
    if kind.startswith('w'):
        _deal_work(sess, npc, args)
    elif kind.startswith('g'):
        _deal_goods(sess, npc)
    elif kind.startswith('f'):
        _deal_favour(sess, npc, args)
    else:
        raise CommandError(f'{npc.name} deals in work, goods and favours, '
                           f'not {kind!r}')


def _deal_index(sess) -> None:
    """Who in this district will do business, and what kind."""
    game, c = sess.require_game(), sess.console
    here = [n for n in npc_content.NPCS
            if n.key in game.story.met
            and (not n.where or n.where == game.city.where)
            and (not n.at or n.at in game.city.district.services)
            and [o for o in n.offers if o != 'nothing']]
    c.header('Business', game.city.district.name)
    if not here:
        c.say('[dim]Nobody you know is doing business in '
              f'{game.city.district.name}. `look` to find people, and '
              '`who is <name>` for what somebody offers.[/]')
        return
    for npc in here:
        trades = ', '.join(o for o in npc.offers if o != 'nothing')
        c.raw(f'  [accent]{npc.key:<14}[/] [fg]{npc.name:<24}[/] '
              f'[dim]{trades}[/]')
    c.blank()
    c.say('[dim]`deal <name>` for the detail.[/]')


def _deal_person(sess, npc) -> None:
    game, c = sess.require_game(), sess.console
    c.header(npc.name, npc.epithet)
    c.kv([('offers', ', '.join(o for o in npc.offers if o != 'nothing')
                     or 'nothing'),
          ('between you', _standing(game, npc))])
    live = [o for o in npc.offers if o != 'nothing']
    c.blank()
    if 'work' in live:
        work = offers.BY_NPC_WORK.get(npc.key)
        ready, why = _work_ready(game, npc)
        c.say(f'[fg]deal {npc.key} work[/] [dim]'
              + ('a job they are holding for you' if ready else why) + '[/]')
    if 'goods' in live:
        c.say(f'[fg]deal {npc.key} goods[/] [dim]what is under their own '
              f'counter[/]')
    if 'intel' in live and npc.topics:
        c.say(f'[fg]ask {npc.key} <topic>[/] [dim]'
              + ', '.join(sorted(npc.topics)) + '[/]')
    if 'favour' in live:
        for fav in offers.favours_for(npc.key):
            c.say(f'[fg]deal {npc.key} favour {fav.key}[/] [dim]{fav.blurb}[/]')


def _work_ready(game, npc) -> tuple[bool, str]:
    """Whether they have something for you, and why not if they do not."""
    work = offers.BY_NPC_WORK.get(npc.key)
    if work is None:
        return False, 'they do not hand out work'
    if game.city.accepted:
        return False, 'you are already carrying something'
    for rule in work.requires:
        if not game.story.satisfied(rule, game):
            return False, 'they do not know you well enough yet'
    since = game.city.shift - int(game.story.asked.get(npc.key, -99))
    if since < offers.WORK_EVERY:
        return False, (f'nothing new for {offers.WORK_EVERY - since} more '
                       f'shifts')
    if _owed(game, npc.key) >= offers.OWED_LIMIT:
        return False, 'you are too far into them already'
    return True, ''


def _deal_work(sess, npc, args) -> None:
    game, c = sess.require_game(), sess.console
    work = offers.BY_NPC_WORK.get(npc.key)
    if work is None:
        raise CommandError(f'{npc.name} does not hand out work.')
    ready, why = _work_ready(game, npc)
    if not ready:
        raise CommandError(f'{npc.name}: {why}.')

    existing = next((x for x in game.city.board if x.from_npc == npc.key),
                    None)
    if existing is None:
        existing = game.city.offer_work(game.rng, game.alias, work)
        game.story.asked[npc.key] = game.city.shift
    c.blank()
    c.rule(npc.name)
    c.say(work.pitch)
    c.blank()
    from .city import _show_contract
    _show_contract(sess, existing)
    c.blank()
    c.say(f'[dim]It is on the board as [fg]{existing.cid}[/][dim], held for '
          f'{work.patience} shifts longer than a posting. `take '
          f'{existing.cid}` to agree to it.[/]')
    sess.autosave()


def _deal_goods(sess, npc) -> None:
    game, c = sess.require_game(), sess.console
    stock = offers.BY_NPC_STOCK.get(npc.key)
    if stock is None:
        raise CommandError(f'{npc.name} does not sell anything.')
    if npc.where and npc.where != game.city.where:
        raise CommandError(f'{npc.name} keeps their stock in '
                           f'{districts.BY_KEY[npc.where].name}.')
    # A counter can close on you. D51: what you did to somebody is part of
    # whether they still get the cabinet out.
    for rule in stock.requires:
        if not game.story.satisfied(rule, game):
            raise CommandError(stock.refusal or f'{npc.name} has nothing '
                               f'under the counter for you.')
    game.city.open_counter(stock)
    c.header(npc.name, 'what they keep back')
    c.say(f'[dim]{stock.pitch}[/]')
    # First time you deal with *them*, rather than the first time a line of
    # stock is new. Ozymandias sells one thing that the Ninth's market also
    # carries, so his entire character never printed.
    flag = f'counter:{npc.key}'
    if flag not in game.story.flags:
        game.story.flags.add(flag)
        c.blank()
        c.say(stock.first)

    # Theirs, specifically. The goods join the district's shelf so that `buy`
    # and `market` work on them unchanged, and that also means the market
    # screen mixes them into thirty other lines with nothing saying which four
    # are the ones this person got out for you.
    from ..world import market as market_mod
    from .city import _item, _listing_detail
    rows = []
    for listing in game.city.listings():
        if listing.key not in stock.goods:
            continue
        item = _item(listing)
        if item is None:
            continue
        price, _ = market_mod.quote(listing, game.city.where, game.alias,
                                    game.char.dissonance,
                                    game.char.mult('price_mult'),
                                    game.city.phase,
                                    game.char.attr('guile'))
        rows.append((item.name, listing.kind,
                     _listing_detail(listing, item), f'{price:,}c'))
    c.blank()
    if rows:
        c.table(('item', 'kind', 'what it does', 'price'), rows,
                roles=('accent', 'dim', 'dim', 'credit'))
        c.blank()
        c.say('[dim]`buy <name>` as anywhere else. It is on the local shelf '
              'now and it does not rotate off it.[/]')
    else:
        c.say('[dim]The shelf is empty. They are not apologetic about it.[/]')
    sess.autosave()


def _deal_favour(sess, npc, args) -> None:
    game, c = sess.require_game(), sess.console
    available = offers.favours_for(npc.key)
    if not available:
        raise CommandError(f'{npc.name} is not somebody you ask for things.')
    want = (args.get(2) or '').lower()
    if not want:
        c.header(npc.name, _standing(game, npc))
        for fav in available:
            c.raw(f'  [accent]{fav.key:<10}[/] [dim]{fav.blurb}[/]')
        c.blank()
        c.say(f'[dim]`deal {npc.key} favour <name>`. Each one puts you a '
              f'favour down, and finishing work they gave you is how it '
              f'comes off.[/]')
        return
    fav = next((f for f in available if f.key.startswith(want)), None)
    if fav is None:
        raise CommandError(f'{npc.name} does: '
                           + ', '.join(f.key for f in available))
    if _owed(game, npc.key) >= offers.OWED_LIMIT:
        c.blank()
        c.say(f'[err]{fav.refusal}[/]')
        return
    for rule in fav.requires:
        if not game.story.satisfied(rule, game):
            raise CommandError(f'{npc.name} will not, and does not explain '
                               f'why, which is its own answer.')

    done, note = _do_favour(sess, fav)
    if not done:
        raise CommandError(note)
    game.story.owed[npc.key] = _owed(game, npc.key) + 1
    c.blank()
    c.rule(fav.name, role='accent2')
    for para in fav.text.split('\n\n'):
        c.say(para)
        c.blank()
    c.say(f'[dim]{note}[/]')
    c.say(f'[dim]You are {_standing(game, npc)} with {npc.name}.[/]')
    sess.autosave()


def _do_favour(sess, fav) -> tuple[bool, str]:
    """Apply one favour. Returns (happened, what to say about it).

    Every effect key here is in `offers.EFFECTS` and `validate.py` checks the
    other direction, so a favour cannot promise something nothing implements,
    which is the exact failure this whole feature exists to correct.
    """
    game = sess.game
    if fav.effect == 'heat':
        hot, heat = game.alias.hottest
        if not hot:
            return False, 'nobody is looking for you. Save it.'
        shed = min(fav.amount, heat)
        game.alias.add_heat(hot, -shed)
        return True, (f'{factions.BY_KEY[hot].short} attention down '
                      f'{int(shed)}.')
    if fav.effect == 'hold':
        contract = game.city.current
        if contract is None:
            return False, 'you are not carrying anything to hold.'
        contract.expires += fav.amount
        return True, (f'{contract.title} now runs to shift '
                      f'{contract.expires}.')
    if fav.effect == 'intel':
        contract = game.city.current
        if contract is None:
            return False, 'there is no job to read.'
        # The same network the run will generate, read the same way legwork
        # reads it, so a favour cannot know something a shift of asking
        # around could not have found out.
        from ..run import network as net_mod
        from .city import _legwork_result
        net = net_mod.generate(game.rng.fork('network', contract.cid),
                               contract.target, int(contract.posture),
                               contract.objective, contract.size_mod)
        for gives in ('topology', 'ice', 'assets'):
            contract.intel[gives] = _legwork_result(net, gives, 1, game)
        return True, 'Everything they can see about it is yours.'
    if fav.effect == 'detox':
        from ..content import drugs
        state = drugs.normalise(game.char.chem)
        if not state['habit']:
            return False, 'there is nothing on you to take off.'
        worst = max(state['habit'], key=lambda k: state['habit'][k])
        state['habit'][worst] = max(0, state['habit'][worst] - fav.amount)
        if not state['habit'][worst]:
            del state['habit'][worst]
        game.char.chem = state
        return True, f'{drugs.BY_KEY[worst].name} has less of you than it did.'
    if fav.effect == 'debt':
        if not game.debt.owed:
            return False, 'you do not owe anybody anything.'
        game.debt.pay(fav.amount)
        return True, f'{game.debt.amount:,}c outstanding.'
    if fav.effect == 'ground':
        floor = game.char.chrome_dissonance
        if game.char.dissonance <= floor:
            return False, ('there is nothing to walk back that is not '
                           'hardware.')
        before = game.char.dissonance
        game.char.dissonance = max(floor, before - fav.amount)
        return True, (f'Dissonance {before} to {game.char.dissonance}.')
    return False, 'nothing happens, which should be impossible.'


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
    game.city.news.append(f'[accent2]{thread.name}:[/] you chose '
                          f'{choice.label.lower()}.')
    c.blank()
    c.rule(choice.label, role='accent2')
    for para in choice.text.split('\n\n'):
        c.say(para)
        c.blank()

    if choice.credits:
        game.char.credits = max(0, game.char.credits + choice.credits)
        word = 'in' if choice.credits > 0 else 'gone'
        c.say(f'[credit]{abs(choice.credits):,}c[/] {word}.')
    if choice.gives:
        from ..content import cyberware, hardware, programs
        for key in choice.gives:
            game.char.library.append(key)
            name = next((table.BY_KEY[key].name
                         for table in (hardware, programs, cyberware)
                         if key in table.BY_KEY), key)
            c.say(f'[dim]{name} is in the bag.[/]')
    for faction, delta in choice.rep.items():
        game.alias.adjust_rep(faction, delta)
        c.say(f'[dim]{factions.BY_KEY[faction].short} '
              f'{"warmer" if delta > 0 else "colder"}.[/]')
    for rival_key, delta in choice.disposition.items():
        rival = game.city.rival(rival_key)
        if rival is not None:
            rival.adjust_disposition(delta)
    if choice.drift:
        before = game.char.dissonance
        game.char.dissonance = max(0, min(100, before + choice.drift))
        c.say(f'[accent2]Dissonance {before} to {game.char.dissonance}.[/]')
    sess.autosave()
    if choice.ends:
        # The third exit. The choice has already said what happened; this
        # is the numbers, the decisions read back, and what is left.
        from .core import end_character
        end_character(sess, choice.ends)
        return
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
        # The wire carries the story too (D56): a scene is something the
        # city did, and `news` is where what the city did goes.
        game.city.news.append(f'[dim]{thread.name}:[/] {stage.headline}.')
        c.blank()
        c.rule(thread.name, role='accent2')
        c.say(f'[dim]{stage.headline}[/]')
        c.blank()
        for para in stage.text.split('\n\n'):
            c.say(para)
            c.blank()
        if stage.posts is not None:
            # The scene put something on the board. Said in the board's own
            # terms, because the next thing the player types is `board`.
            contract = game.city.post_story(game.rng, game.alias, stage.posts,
                                            f'{thread_key}.{stage.key}')
            c.say(f'[dim]On the board: [/][accent]{contract.title}[/]'
                  f'[dim], {contract.cid}, against '
                  f'{contract.target_data.short}. It does not expire and '
                  f'nobody else will take it. `board {contract.cid}` to read '
                  f'it, `take {contract.cid}` when you are ready.[/]')
            c.blank()
        if stage.choices:
            c.say('[warn]This one is waiting on you.[/] [dim]`choose`.[/]')
    sess.autosave()
