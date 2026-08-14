"""City commands: the build, the board, the market, and the door to a run.

Everything here costs either credits or shifts, and the ones that cost shifts
say so before they take them. Time is the city's real currency and a command
that quietly spends three of it is a command that has lied.
"""

from __future__ import annotations

from ..content import attributes as attr_content
from ..content import cyberware, dissonance as drift, districts
from ..content import effects as fx, factions
from ..content import hardware, icons, origins, programs
from ..content import rivals as rival_content
from ..content import skills as skill_content
from ..content import traits as trait_content
from ..game import Game
from ..model.character import Character
from ..model.identity import ALIAS_COST, ALIAS_SHIFTS
from ..rng import random_seed
from ..shell import CommandError, command
from ..world import debt as debt_mod
from ..world import fallout
from ..world import rivals as rival_world
from ..world import market as market_mod


# --------------------------------------------------------------------------
# creation
# --------------------------------------------------------------------------


@command('new', 'Make a character.',
         group='character', bare=True,
         usage='new [handle] --origin <key> [--seed n]',
         detail='With no arguments, lists the origins. Creation gives you an '
                'attribute budget and an experience budget, which you spend '
                'with `boost` and `train`: the same commands you will use for '
                'the rest of the character\'s life.')
def cmd_new(sess, args) -> None:
    c = sess.console
    if not len(args) and not args.opt('origin'):
        c.header('Origins', f'{len(origins.ORIGINS)} of them')
        c.say('[dim]An origin sets where you start, never where you can go.[/]')
        for origin in origins.ORIGINS:
            c.blank()
            c.raw(f'[accent][bold]{origin.name}[/][/]  [dim]{origin.key}[/]')
            c.say(origin.blurb, indent='  ')
            shape = '  '.join(
                f'{attr_content.BY_KEY[k].short} {v:+d}'
                for k, v in origin.attrs.items())
            c.say(f'[dim]{shape}  {origin.credits:,}c[/]', indent='  ')
            c.say(f'[warn]{origin.passive}:[/] [dim]{origin.passive_detail}[/]',
                  indent='  ', subsequent='  ')
        c.blank()
        c.say('[dim]`new <handle> --origin <key>` when you have picked.[/]')
        return

    if sess.game is not None and not args.has('force'):
        raise CommandError('a character is already loaded. `new ... --force` '
                           'to abandon them.')

    origin_key = (args.opt('origin') or '').lower()
    if origin_key not in origins.BY_KEY:
        raise CommandError('pick an origin: '
                           + ', '.join(origins.ORIGIN_KEYS))
    handle = args.get(0) or 'nobody'
    seed = args.int_opt('seed', random_seed())

    char = Character.from_origin(origin_key, handle)
    char.points = attr_content.CREATION_POINTS
    char.xp = skill_content.CREATION_XP
    sess.game = Game.new(char, seed=seed)
    sess.run = None

    origin = char.origin_data
    c.blank()
    c.rule(origin.name)
    c.say(origin.story)
    c.blank()
    c.say(f'[warn]{origin.passive}.[/] {origin.passive_detail}')
    c.blank()
    c.say(f'[err]{origin.complication}[/]')
    c.blank()
    c.kv([('handle', f'[accent]{handle}[/]'),
          ('running as', f'[accent]{sess.game.alias.name}[/]'),
          ('world seed', f'[dim]{seed}[/]'),
          ('to spend', f'{char.points} attribute points, '
                       f'{char.xp} experience')])
    c.blank()
    c.say('[dim]`char` to see the build, `boost <attribute>` and '
          '`train <skill>` to spend, and `trait` to decide what kind of '
          'person this is. `board` when you are ready to work.[/]')


# --------------------------------------------------------------------------
# inspection
# --------------------------------------------------------------------------


@command('char', 'Your build, in full.',
         group='character', aliases=('sheet', 'me'), usage='char [--effects]')
def cmd_char(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    char = game.char
    origin = char.origin_data

    c.header(char.handle, origin.name)
    c.kv([
        ('running as', f'[accent]{game.alias.name}[/] '
                       f'[dim]({game.alias.runs} runs)[/]'),
        ('credits', f'[credit]{char.credits:,}c[/]'),
        ('integrity', f'{char.integrity}/{char.integrity_max}'),
        ('dissonance', f'{char.dissonance} [dim]({char.dissonance_band[1]})[/]'),
    ])

    c.blank()
    rows = []
    arrow = c.caps.g('arrow')
    for a in attr_content.ATTRIBUTES:
        base = char.base_attrs.get(a.key, 0)
        eff = char.attr(a.key)
        if eff == base:
            rows.append((a.name, str(base)))
        else:
            rows.append((a.name, f'{base} {arrow} [accent]{eff}[/] '
                                 f'[dim]({eff - base:+d} from gear)[/]'))
    c.kv(rows)

    c.blank()
    c.kv([('Bandwidth', f'{char.bandwidth_used}/{char.bandwidth}'),
          ('Focus', str(char.focus)),
          ('Tempo', str(char.tempo)),
          ('Composure', str(char.composure))])

    if char.points or char.xp:
        c.blank()
        bits = []
        if char.points:
            bits.append(f'{char.points} attribute point'
                        f'{"s" if char.points != 1 else ""}')
        if char.xp:
            bits.append(f'{char.xp} experience')
        c.say(f'[warn]Unspent:[/] {", ".join(bits)}. '
              f'[dim]`boost`, `train`.[/]')

    if args.has('effects'):
        c.blank()
        c.rule('modifiers')
        eff = char.effects()
        if not eff:
            c.say('[dim]Nothing.[/]')
        for key in sorted(eff):
            c.raw(f'  [dim]{fx.describe(key, eff[key])}[/]')


@command('skills', 'Your training, and what the next rank costs.',
         group='character', usage='skills')
def cmd_skills(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    char = game.char
    c.header('Skills', f'{char.xp} experience unspent')
    for skill in skill_content.SKILLS:
        rank = char.base_skills.get(skill.key, 0)
        eff = char.skill(skill.key)
        dots = c.bar(rank / skill_content.MAX_RANK, 'accent', cells=5)
        cost = (skill_content.RANK_COST[rank + 1]
                if rank < skill_content.MAX_RANK else 0)
        tail = (f'[dim]next {cost}xp[/]' if cost
                else '[ok]maxed[/]')
        if eff > rank:
            tail = f'[accent]+{eff - rank} from gear[/]  ' + tail
        c.raw(f'  {dots} [fg]{skill.name:<14}[/] {tail}')
        nxt = skill.technique_at(rank + 1)
        if nxt:
            c.say(f'[dim]{nxt.name}: {nxt.summary}[/]', indent='        ',
                  subsequent='        ')


@command('boost', 'Spend an attribute point.',
         group='character', usage='boost <attribute>',
         complete=lambda sess, prefix: list(attr_content.ATTR_KEYS))
def cmd_boost(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    key = (args.get(0) or '').lower()
    if not key:
        raise CommandError('which attribute: '
                           + ', '.join(attr_content.ATTR_KEYS))
    match = [k for k in attr_content.ATTR_KEYS if k.startswith(key)]
    if len(match) != 1:
        raise CommandError(f'{key!r} is not one of: '
                           + ', '.join(attr_content.ATTR_KEYS))
    ok, why = game.char.can_boost(match[0])
    if not ok:
        raise CommandError(why)
    value = game.char.boost(match[0])
    c.ok(f'{attr_content.BY_KEY[match[0]].name} is now {value}. '
         f'[dim]{game.char.points} point'
         f'{"s" if game.char.points != 1 else ""} left.[/]')


@command('train', 'Buy the next rank in a skill.',
         group='character', usage='train <skill>',
         complete=lambda sess, prefix: list(skill_content.SKILL_KEYS))
def cmd_train(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    key = (args.get(0) or '').lower()
    if not key:
        raise CommandError('which skill: ' + ', '.join(skill_content.SKILL_KEYS))
    match = [k for k in skill_content.SKILL_KEYS if k.startswith(key)]
    if len(match) != 1:
        raise CommandError(f'{key!r} is not one of: '
                           + ', '.join(skill_content.SKILL_KEYS))
    ok, why = game.char.can_train(match[0])
    if not ok:
        raise CommandError(why)
    tech = game.char.train(match[0])
    rank = game.char.base_skills[match[0]]
    c.ok(f'{skill_content.BY_KEY[match[0]].name} rank {rank}. '
         f'[dim]{game.char.xp} experience left.[/]')
    if tech:
        c.blank()
        c.raw(f'[accent][bold]{tech.name} unlocked.[/][/]  '
              f'[dim]{tech.verb or "modifies an existing command"}[/]')
        c.say(tech.summary)
        c.say(f'[dim]{tech.detail}[/]')


# --------------------------------------------------------------------------
# the deck
# --------------------------------------------------------------------------


@command('deck', 'What your deck is made of, and what it can carry.',
         group='character', usage='deck')
def cmd_deck(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    deck = game.char.deck
    c.header('Deck', f'memory {deck.memory_used}/{deck.memory}  '
                     f'heat {deck.heat}/{deck.heat_cap}')
    rows = []
    for slot in hardware.SLOTS:
        comp = deck.component(slot)
        dmg = deck.damage.get(slot, 0)
        if comp is None:
            rows.append((slot, '[dim]empty[/]'))
            continue
        label = comp.name
        if dmg >= 3:
            label = f'[err]{label} (destroyed)[/]'
        elif dmg:
            label = f'[warn]{label} (damage {dmg}/3)[/]'
        rows.append((slot, label))
    c.kv(rows)

    c.blank()
    c.rule('loaded')
    if not deck.loaded:
        c.say('[dim]Nothing loaded. `load <program>`.[/]')
    else:
        for key in deck.loaded:
            p = programs.BY_KEY.get(key)
            if not p:
                continue
            c.raw(f'  [accent]{p.name:<14}[/] [dim]{p.category:<8} '
                  f'{p.memory}mem  rating {p.rating}  '
                  f'sig {p.signature:.1f}[/]')
    spare = [k for k in game.char.library if k not in deck.loaded]
    if spare:
        c.blank()
        c.say(f'[dim]In storage: '
              f'{", ".join(programs.BY_KEY[k].name for k in spare if k in programs.BY_KEY)}[/]')
    if deck.heat_headroom <= 0:
        c.blank()
        c.warn('No thermal headroom. Overclocking is not available until the '
               'cooling outpaces the components.')


@command('icon', 'The shape you wear in the net.',
         group='character', usage='icon [wear <key>] [buy <key>]',
         detail='Your icon is what cyberspace renders you as, and it is a real '
                'build axis: it changes how loud you are, how ICE reads you, '
                'and whether anything in there will talk to you. It is also '
                'the cheapest axis to change, so carry several and wear the '
                'right one for the job. Icons far from a human shape need '
                'Dissonance to hold: below that, they fight you.')
def cmd_icon(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    char = game.char
    action = (args.get(0) or '').lower()

    if action in ('wear', 'buy'):
        query = (args.get(1) or '').lower()
        key = next((k for k in icons.ICON_KEYS
                    if k == query or query in icons.BY_KEY[k].name.lower()), None)
        if not key:
            raise CommandError('no icon called that: '
                               + ', '.join(icons.ICON_KEYS))
        icon = icons.BY_KEY[key]

        if action == 'buy':
            if key in char.icons:
                raise CommandError(f'you already own {icon.name}')
            if 'workshop' not in game.city.district.services:
                shops = ', '.join(d.name
                                  for d in districts.with_service('workshop'))
                raise CommandError(f'icons are cut at a workshop. Try: {shops}')
            price = int(icon.price * game.city.district.price_mult
                        * char.mult('price_mult'))
            if price > char.credits:
                raise CommandError(f'{icon.name} is {price:,}c and you have '
                                   f'{char.credits:,}c')
            char.credits -= price
            char.icons.append(key)
            c.ok(f'{icon.name} cut and keyed to your deck for '
                 f'[credit]{price:,}c[/].')
            return

        if key not in char.icons:
            raise CommandError(f'you do not own {icon.name}. `icon buy {key}` '
                               f'at a workshop.')
        if sess.run is not None:
            raise CommandError('you cannot change what you are while you are '
                               'wearing it.')
        char.icon = key
        c.ok(f'You are {icon.name} now.')
        c.say(f'[dim]{icon.render}[/]')
        gap = char.coherence_gap
        if gap:
            c.warn(f'It does not fit. You are {gap} short of the Dissonance '
                   f'this shape needs, and holding it will cost you.')
        return

    icon = char.icon_data
    c.header('Icon', icon.name)
    c.say(icon.render)
    c.blank()
    c.say(f'[dim]{icon.blurb}[/]')
    c.blank()
    c.say(f'[warn]Drawback.[/] {icon.drawback}')
    gap = char.coherence_gap
    if gap:
        c.blank()
        c.err(f'Coherence gap {gap}. This shape needs {icon.coherence} '
              f'Dissonance and you have {char.dissonance}.')
        for key, value in icons.coherence_penalty(char.icon,
                                                  char.dissonance).items():
            if value and abs(value - (1.0 if 'mult' in key else 0)) > 1e-9:
                c.raw(f'    [err]{fx.describe(key, value)}[/]')

    c.blank()
    c.rule('what you own')
    rows = []
    for key in icons.ICON_KEYS:
        other = icons.BY_KEY[key]
        owned = key in char.icons
        fit = icons.coherence_gap(key, char.dissonance)
        state = ('[accent]worn[/]' if key == char.icon
                 else '[ok]owned[/]' if owned
                 else f'[credit]{other.price:,}c[/]')
        rows.append((key, other.name, str(other.coherence),
                     '[err]too strange[/]' if fit else '[ok]fits[/]', state))
    c.table(('key', 'icon', 'needs', 'for you', ''), rows,
            roles=('dim', 'accent', 'dim', None, None))
    c.blank()
    c.say('[dim]`icon wear <key>` to change. `icon buy <key>` at a '
          'workshop.[/]')


@command('load', 'Put a program on the deck.',
         group='prep', usage='load <program>',
         complete=lambda sess, prefix: _library_names(sess))
def cmd_load(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if sess.run is not None:
        raise CommandError('the loadout is fixed once you are inside.')
    key = _find_program(args.get(0), game.char.library)
    ok, why = game.char.deck.can_load(key)
    if not ok:
        raise CommandError(why)
    game.char.deck.load(key)
    p = programs.BY_KEY[key]
    c.ok(f'{p.name} loaded. [dim]{game.char.deck.memory_free} memory free.[/]')


@command('unload', 'Take a program off the deck.',
         group='prep', usage='unload <program>',
         complete=lambda sess, prefix: _loaded_names(sess))
def cmd_unload(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if sess.run is not None:
        raise CommandError('the loadout is fixed once you are inside.')
    key = _find_program(args.get(0), game.char.deck.loaded)
    game.char.deck.unload(key)
    c.ok(f'{programs.BY_KEY[key].name} unloaded. '
         f'[dim]{game.char.deck.memory_free} memory free.[/]')


@command('install', 'Have cyberware fitted. Needs a clinic.',
         group='character', usage='install <ware>')
def cmd_install(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if 'clinic' not in game.city.district.services:
        clinics = ', '.join(d.name for d in districts.with_service('clinic'))
        raise CommandError(f'no clinic here. Try: {clinics}')
    key = _find_ware(args.get(0), [w.key for w in cyberware.WARE])
    ware = cyberware.BY_KEY[key]
    if key not in game.char.library and key not in game.char.installed:
        raise CommandError(f'you do not own a {ware.name}. Buy one first.')
    if 'no_chrome' in game.char.riders():
        raise CommandError('you have never had anything put in you and you '
                           'have opinions about people who have. Nothing is '
                           'going in now.')
    ok, why = game.char.can_install(key)
    if not ok:
        raise CommandError(why)
    game.char.install(key)
    if key in game.char.library:
        game.char.library.remove(key)
    c.ok(f'{ware.name} fitted.')
    c.say(f'[dim]{ware.drawback}[/]')
    c.info(f'Dissonance {game.char.dissonance} '
           f'({game.char.dissonance_band[1]}). '
           f'Bandwidth {game.char.bandwidth_used}/{game.char.bandwidth}.')
    gap = game.char.coherence_gap
    if gap:
        c.info(f'{game.char.icon_data.name} fits you better now.'
               if gap == 0 else
               f'{game.char.icon_data.name} is still {gap} short of fitting.')
    _advance(sess, 1)


@command('uninstall', 'Have cyberware removed. The Dissonance stays.',
         group='character', usage='uninstall <ware>')
def cmd_uninstall(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if 'clinic' not in game.city.district.services:
        raise CommandError('no clinic here.')
    key = _find_ware(args.get(0), game.char.installed)
    game.char.uninstall(key)
    game.char.library.append(key)
    c.ok(f'{cyberware.BY_KEY[key].name} removed.')
    c.say('[dim]The Dissonance does not come out with it.[/]')
    _advance(sess, 1)


@command('chrome', 'What is fitted, and what is free.',
         group='character', usage='chrome')
def cmd_chrome(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    char = game.char
    band = char.dissonance_band
    c.header('Chrome', f'bandwidth {char.bandwidth_used}/{char.bandwidth}')
    c.say(f'[accent2]Dissonance {char.dissonance}[/] '
          f'[dim]({band[1]})[/]  {band[2]}')
    for location, capacity in cyberware.SLOTS.items():
        used = char.slots_used(location)
        c.blank()
        c.raw(f'[dim]{location}[/] [dim]{used}/{capacity}[/]')
        fitted = [k for k in char.installed
                  if k in cyberware.BY_KEY
                  and cyberware.BY_KEY[k].location == location]
        if not fitted:
            c.raw('  [dim]nothing[/]')
        for key in fitted:
            w = cyberware.BY_KEY[key]
            c.raw(f'  [accent]{w.name}[/] [dim]{w.bandwidth}bw '
                  f'{w.dissonance}dis[/]')
            c.say(f'[dim]{w.drawback}[/]', indent='    ', subsequent='    ')


# --------------------------------------------------------------------------
# the market
# --------------------------------------------------------------------------


@command('market', 'What is for sale here.',
         group='city', aliases=('shop',),
         usage='market [programs|ware|components]')
def cmd_market(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    district = game.city.district
    sellers = [s for s in district.services if s in market_mod.STOCK_KINDS]
    if not sellers:
        raise CommandError(f'nothing is sold in {district.name}.')

    want = (args.get(0) or '').rstrip('s').lower()
    kind = {'program': 'program', 'ware': 'ware', 'cyberware': 'ware',
            'component': 'component', 'part': 'component'}.get(want)

    qualifies = game.char.dissonance >= drift.DEEP_CLINIC_BAND
    listings = game.city.listings(kind, deep=None if qualifies else False)
    if not listings:
        raise CommandError('nothing of that kind here.')

    c.header(f'{district.name} market',
             f'tier {district.max_tier} and below')
    rows = []
    for listing in listings:
        item = _item(listing)
        if item is None:
            continue
        price, _ = market_mod.quote(listing, game.city.where, game.alias,
                                    game.char.dissonance,
                                    game.char.mult('price_mult'))
        detail = _listing_detail(listing, item)
        rows.append((item.name, listing.kind, detail, f'{price:,}c'))
    c.table(('item', 'kind', 'what it does', 'price'), rows,
            roles=('accent', 'dim', 'dim', 'credit'))
    c.blank()
    c.say('[dim]`buy <name>` to take one. `buy <name> --why` to see the '
          'price broken down.[/]')


@command('buy', 'Buy something from the local market.',
         group='city', usage='buy <name> [--why]')
def cmd_buy(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if not len(args):
        raise CommandError('buy what?')
    query = args.rest().lower()
    qualifies = game.char.dissonance >= drift.DEEP_CLINIC_BAND
    listings = game.city.listings(deep=None if qualifies else False)
    matches = []
    for listing in listings:
        item = _item(listing)
        if item and (query in item.name.lower() or query == listing.key):
            matches.append((listing, item))
    if not matches:
        raise CommandError(f'nothing here matches {query!r}')
    if len(matches) > 1:
        names = ', '.join(i.name for _, i in matches)
        raise CommandError(f'which one: {names}')
    listing, item = matches[0]

    price, terms = market_mod.quote(listing, game.city.where, game.alias,
                                    game.char.dissonance,
                                    game.char.mult('price_mult'))
    if args.has('why'):
        c.header(item.name, f'{price:,}c')
        c.kv([('list', f'{listing.price:,}c')]
             + [(label, f'x{mult:.2f}') for label, mult in terms])
        return
    if price > game.char.credits:
        raise CommandError(f'{item.name} is {price:,}c and you have '
                           f'{game.char.credits:,}c')

    game.char.credits -= price
    listing.stock -= 1
    if listing.kind == 'program':
        game.char.library.append(listing.key)
    elif listing.kind == 'ware':
        game.char.library.append(listing.key)
        c.info('Bought, not fitted. `install` it at a clinic.')
    else:
        old = game.char.deck.parts.get(hardware.BY_KEY[listing.key].slot)
        game.char.deck.fit(listing.key)
        if old:
            # The old part goes in the bag rather than the bin: Hardware rank 4
            # swaps mid-run, and it needs something to swap to.
            game.char.library.append(old)
            c.info(f'{hardware.BY_KEY[old].name} came out and went in the bag.')
    c.ok(f'{item.name} for [credit]{price:,}c[/]. '
         f'[dim]{game.char.credits:,}c left.[/]')


@command('sell', 'Sell something. Needs a fence or a market.',
         group='city', usage='sell <name>')
def cmd_sell(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if not any(s in game.city.district.services for s in ('fence', 'market')):
        raise CommandError('nobody here is buying.')
    if not len(args):
        raise CommandError('sell what?')
    query = args.rest().lower()

    for key in list(game.char.library):
        item = programs.BY_KEY.get(key) or cyberware.BY_KEY.get(key)
        if not item or query not in item.name.lower():
            continue
        kind = 'program' if key in programs.BY_KEY else 'ware'
        value = market_mod.sale_value(kind, key)
        game.char.library.remove(key)
        game.char.credits += value
        c.ok(f'{item.name} sold for [credit]{value:,}c[/].')
        return
    raise CommandError(f'you do not have anything called {query!r} in storage')


# --------------------------------------------------------------------------
# the board
# --------------------------------------------------------------------------


@command('board', 'Work currently on offer.',
         group='city', aliases=('jobs',), usage='board [id]')
def cmd_board(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    city = game.city

    if len(args):
        contract = city.contract(args[0])
        if contract is None:
            raise CommandError(f'no contract {args[0]!r} on the board')
        _show_contract(sess, contract)
        return

    if not city.board:
        c.info('The board is empty. Come back after a shift or two.')
        return
    c.header('The board', f'{city.when}')
    rows = []
    for contract in city.board:
        left = contract.expires - city.shift
        mark = '*' if contract.cid == city.accepted else ''
        rows.append((f'{mark}{contract.cid}', contract.title,
                     contract.patron_data.short, contract.target_data.short,
                     contract.objective, f'{contract.pay:,}c',
                     f'{left}sh'))
    c.table(('id', 'job', 'patron', 'target', 'what', 'pay', 'left'), rows,
            roles=('dim', 'accent', 'info', 'err', 'dim', 'credit', 'warn'))
    c.blank()
    c.say('[dim]`board <id>` for detail. `take <id>` to accept.[/]')


def _show_contract(sess, contract) -> None:
    game, c = sess.game, sess.console
    from ..world.contracts import OBJECTIVE_BLURB, OBJECTIVE_PROGRAM
    c.header(contract.title, contract.cid)
    c.say(contract.blurb)
    c.blank()
    c.kv([
        ('patron', f'[info]{contract.patron_data.name}[/]'),
        ('target', f'[err]{contract.target_data.name}[/]'),
        ('objective', f'{contract.objective} [dim]'
                      f'{OBJECTIVE_BLURB[contract.objective]}[/]'),
        ('pay', f'[credit]{contract.pay:,}c[/]'),
        ('district', districts.BY_KEY[contract.district].name),
        ('expires', f'in {contract.expires - game.city.shift} shifts'),
        ('posture', f'{int(contract.posture)} [dim]'
                    f'{contract.target_data.doctrine}[/]'),
    ])
    need = OBJECTIVE_PROGRAM.get(contract.objective)
    if need and not game.char.deck.has_category(need):
        c.blank()
        c.warn(f'You have no {need} loaded. This objective needs one.')
    if contract.intel:
        c.blank()
        c.rule('intel')
        for key, value in contract.intel.items():
            c.say(f'[ok]{key}:[/] {value}')


@command('take', 'Accept a contract.',
         group='city', usage='take <id>')
def cmd_take(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if game.city.accepted:
        raise CommandError(f'you are already on {game.city.accepted}. '
                           f'`drop` it first.')
    contract = game.city.contract(args.require(0, 'a contract id'))
    if contract is None:
        raise CommandError('no contract by that id')
    contract.taken = True
    game.city.accepted = contract.cid
    c.ok(f'Taken: [accent]{contract.title}[/] against '
         f'{contract.target_data.short}, {contract.pay:,}c.')
    from ..world import rivals as rival_world
    for line in rival_world.on_player_took(game.rng('rivals'),
                                           game.city.rivals, contract):
        c.say(line)
    where = districts.BY_KEY[contract.district]
    if game.city.where != contract.district:
        c.info(f'The job is in {where.name}. `travel {where.key}`.')
    else:
        c.info('You are in the right district. `jack in` when ready.')


@command('drop', 'Abandon the accepted contract.',
         group='city', usage='drop')
def cmd_drop(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    contract = game.city.current
    if contract is None:
        raise CommandError('you have not taken anything')
    game.city.accepted = ''
    contract.taken = False
    game.alias.adjust_rep(contract.patron, -4)
    c.warn(f'Dropped {contract.title}. {contract.patron_data.short} noticed.')


# --------------------------------------------------------------------------
# movement and time
# --------------------------------------------------------------------------


@command('travel', 'Move to another district. Costs a shift.',
         group='city', aliases=('go',), usage='travel <district>',
         complete=lambda sess, prefix: list(districts.DISTRICT_KEYS))
def cmd_travel(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if not len(args):
        c.header('From here', game.city.district.name)
        rows = []
        for key in game.city.district.neighbours:
            d = districts.BY_KEY[key]
            danger, who = game.city.danger(game.alias, key)
            risk = ('[ok]quiet[/]' if danger < 20
                    else '[warn]watched[/]' if danger < 45
                    else f'[err]dangerous ({factions.BY_KEY[who].short})[/]')
            rows.append((key, d.name, factions.BY_KEY[d.controller].short,
                         ', '.join(d.services), risk))
        c.table(('key', 'district', 'runs it', 'has', 'for you'), rows,
                roles=('dim', 'accent', 'info', 'dim', None))
        return

    target = args[0].lower()
    matches = [k for k in districts.DISTRICT_KEYS if k.startswith(target)]
    if len(matches) == 1:
        target = matches[0]
    ok, why = game.city.can_travel(target)
    if not ok:
        raise CommandError(why)

    danger, who = game.city.danger(game.alias, target, game.rng)
    riders = game.char.riders()
    if 'streetwise' in riders:
        # Knows the streets: you move through this city like your own flat.
        danger = int(danger * 0.6)
    if 'findable' in riders:
        # Everybody knows where you drink, including everybody you would
        # rather did not.
        danger = int(danger * 1.3)
    if danger >= fallout.INCIDENT_FLOOR and not args.has('anyway'):
        fac = factions.BY_KEY[who]
        raise CommandError(
            f'{fac.name} have people in '
            f'{districts.BY_KEY[target].name} and a number attached to your '
            f'name. Going anyway is a real risk: `travel {target} --anyway`. '
            f'Otherwise `rest` until it cools, or `burn` the name.')

    known = target in game.city.visited
    game.city.where = target
    game.city.visited.add(target)
    district = districts.BY_KEY[target]
    free = known and 'streetwise' in game.char.riders()
    if free:
        # You have walked this one before. You know which stairwells connect.
        _drift(sess)
        sess.autosave()
    else:
        _advance(sess, 1)
    c.blank()
    c.rule(district.name)
    c.say(district.arrival)
    if free:
        c.info('You know the way. It does not cost you a shift.')

    if danger >= fallout.INCIDENT_FLOOR:
        _resolve_incident(sess, who, danger)
    elif danger >= 25:
        c.blank()
        c.warn(f'{factions.BY_KEY[who].short} have people here and they are '
               f'looking for your name. Do not linger.')


def _resolve_incident(sess, faction: str, danger: int) -> None:
    """You walked in somewhere they are paid to find you. Roll for it."""
    game, c = sess.game, sess.console
    stream = game.rng('events')
    # The score is a percentage chance, capped so that even a hunted runner
    # can sometimes cross a district. A guaranteed incident would make a high
    # bounty a hard wall rather than a cost.
    if not stream.chance(min(0.75, danger / 140)):
        c.blank()
        c.warn('You get most of the way across before somebody looks twice, '
               'and you are around a corner before they finish looking.')
        return
    incident = fallout.pick_up(stream, game.char, game.alias, game.city,
                               faction)
    c.blank()
    c.rule('picked up', role='err')
    c.say(f'[err]{incident.text}[/]')
    if incident.detail:
        c.blank()
        c.say(incident.detail)
    sess.autosave()


@command('rest', 'Lie low. Heals, cools heat, and passes time.',
         group='city', usage='rest [shifts]')
def cmd_rest(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    shifts = max(1, min(12, args.int_at(0, 1, 'a number of shifts')))
    safe = 'safehouse' in game.city.district.services
    before = game.char.hurt
    heal = (2 if safe else 1) * shifts
    riders = game.char.riders()
    # Whatever they used to restart you has never entirely stopped, and three
    # hours a night for eleven years is not rest.
    if 'slow_healing' in riders:
        heal = heal // 2
    if 'poor_rest' in riders:
        heal = int(heal * 0.6)
    game.char.hurt = max(0, game.char.hurt - heal)
    _advance(sess, shifts)
    healed = before - game.char.hurt
    c.ok(f'{shifts} shift{"s" if shifts != 1 else ""} pass.'
         + (f' [ok]Integrity +{healed}.[/]' if healed else ''))
    if not safe:
        c.info('No safehouse here. You did not sleep well.')
    if 'slow_healing' in game.char.riders():
        c.info('You heal the way you have healed since the table.')
    elif 'poor_rest' in game.char.riders():
        c.info('Three hours, like every night.')


# --------------------------------------------------------------------------
# identity
# --------------------------------------------------------------------------


@command('alias', 'The name you are running under, and what it carries.',
         group='prep', usage='alias')
def cmd_alias(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    alias = game.alias
    hottest, heat = alias.hottest
    c.header(alias.name,
             f'established shift {alias.established}, {alias.runs} runs')
    if alias.spent:
        c.warn('This name is spent. Everything it touches is going to be '
               'harder until you burn it.')
    standing = alias.standing()
    if not standing:
        c.say('[dim]Nobody has an opinion yet.[/]')
    else:
        rows = []
        for key, rep, hot in standing:
            fac = factions.BY_KEY[key]
            rows.append((fac.short,
                         f'{rep:+d} {factions.rep_band(rep)}',
                         f'{hot} {factions.heat_band(hot)}' if hot else '-'))
        c.table(('faction', 'standing', 'heat'), rows,
                roles=('accent', None, 'heat'))
    if len(game.aliases) > 1:
        c.blank()
        c.say('[dim]Burned: '
              + ', '.join(a.name for a in game.aliases[:-1]) + '[/]')
    c.blank()
    ghost = 'no_history' in game.char.riders()
    cost = ALIAS_COST // 2 if ghost else ALIAS_COST
    shifts = 1 if ghost else ALIAS_SHIFTS
    c.say(f'[dim]`burn` to take a new name: {cost:,}c and '
          f'{shifts} shift{"s" if shifts != 1 else ""}, and everything above '
          f'goes with it.[/]')


@command('burn', 'Abandon this identity and establish another.',
         group='prep', usage='burn [name] [--confirm]')
def cmd_burn(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    alias = game.alias
    # Nobody: you have no history to burn, so a new name is cheap and quick.
    ghost = 'no_history' in game.char.riders()
    cost = ALIAS_COST // 2 if ghost else ALIAS_COST
    shifts = 1 if ghost else ALIAS_SHIFTS
    if game.char.credits < cost:
        raise CommandError(f'a new name costs {cost:,}c and you have '
                           f'{game.char.credits:,}c')
    if not args.has('confirm'):
        c.warn(f'Burning [accent]{alias.name}[/] destroys '
               f'{len(alias.standing())} relationships along with the heat.')
        for key, rep, hot in alias.standing():
            if rep >= 25:
                c.raw(f'  [ok]losing {factions.BY_KEY[key].short} '
                      f'{rep:+d}[/]')
        c.say(f'[dim]`burn --confirm` to go through with it.[/]')
        return
    name = args.get(0) or ''
    game.char.credits -= cost
    fresh = game.new_alias(name)
    _advance(sess, shifts)
    c.ok(f'{alias.name} is gone. You are [accent]{fresh.name}[/] now.')


@command('rep', 'How the city feels about you, in full.',
         group='info', usage='rep')
def cmd_rep(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    c.header('Standing', game.alias.name)
    rows = []
    for key in factions.FACTION_KEYS:
        fac = factions.BY_KEY[key]
        rep = game.alias.reputation(key)
        heat = game.alias.attention(key)
        posture = int(game.city.posture.get(key, fac.posture))
        rows.append((fac.short, fac.kind,
                     f'{rep:+d} {factions.rep_band(rep)}',
                     f'{heat}' if heat else '-',
                     str(posture)))
    c.table(('faction', 'kind', 'standing', 'heat', 'posture'), rows,
            roles=('accent', 'dim', None, 'heat', 'warn'))
    c.blank()
    c.say('[dim]Posture is how hard their networks generate. It rises when '
          'you succeed against them and falls slowly.[/]')


# --------------------------------------------------------------------------
# legwork
# --------------------------------------------------------------------------

LEGWORK = {
    'perimeter': (0, 'Map the outside of the network yourself.', 'topology'),
    'intel': (900, 'Buy what a fixer already knows.', 'ice'),
    'employee': (350, 'Find somebody who works there and be charming.', 'credential'),
    'tap': (600, 'Put something physical on a line.', 'assets'),
    # Only available once you are far enough gone to do it, per the drift arc.
    'resonance': (0, 'Sit near it and let the shape arrive.', 'ice'),
}

#: Legwork gated on how far into the drift you are. `floor` needs at least
#: that much Dissonance; `ceiling` stops working at or above it.
LEGWORK_DRIFT = {
    'resonance': ('floor', drift.RESONANCE_BAND),
    'employee': ('ceiling', drift.SOCIAL_FLOOR_BAND),
}


@command('legwork', 'Learn about the target before you go in.',
         group='prep', usage='legwork [perimeter|intel|employee|tap]',
         detail='Each costs a shift and most cost money. What you learn is '
                'real: known topology, known ICE placement, a credential that '
                'skips a boundary, or where the valuable assets actually are. '
                'This is what turns the loadout decision into a real one.')
def cmd_legwork(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    contract = game.city.current
    if contract is None:
        raise CommandError('take a contract first: legwork is about a target.')

    if not len(args):
        c.header('Legwork', contract.title)
        rows = []
        for key, (cost, blurb, gives) in LEGWORK.items():
            ok, why = _legwork_allowed(game.char, key)
            if not ok:
                state = f'[err]{why}[/]'
            elif key in contract.intel:
                state = '[ok]done[/]'
            elif gives in contract.intel:
                state = '[dim]covered[/]'
            else:
                state = ''
            rows.append((key, f'{cost:,}c' if cost else 'free', blurb, state))
        c.table(('approach', 'cost', 'what it is', ''), rows,
                roles=('accent', 'credit', 'dim', None))
        c.say('[dim]Each also costs one shift.[/]')
        return

    key = args[0].lower()
    matches = [k for k in LEGWORK if k.startswith(key)]
    if len(matches) != 1:
        raise CommandError('legwork: ' + ', '.join(LEGWORK))
    key = matches[0]
    if key in contract.intel:
        raise CommandError(f'you have already done the {key} work')
    ok, why = _legwork_allowed(game.char, key)
    if not ok:
        c.blank()
        c.say(f'[err]{_legwork_refusal(key)}[/]')
        raise CommandError(why)

    cost, _, gives = LEGWORK[key]
    if cost > game.char.credits:
        raise CommandError(f'that costs {cost:,}c and you have '
                           f'{game.char.credits:,}c')
    game.char.credits -= cost

    stream = game.rng.fork('network', contract.cid)
    from ..run import network as net_mod
    net = net_mod.generate(stream, contract.target, int(contract.posture),
                           contract.objective, contract.size_mod)

    bonus = game.char.bonus('legwork_bonus')
    if key == 'resonance':
        bonus += 1  # you are not looking at it, you are listening to it
        c.blank()
        c.say(f'[accent2]{drift.RESONANCE_TEXT}[/]')
        c.blank()
    contract.intel[gives] = _legwork_result(net, gives, bonus, game)
    contract.intel.setdefault(key, contract.intel[gives])
    c.ok(f'{key.title()} done.')
    c.say(contract.intel[gives])
    _advance(sess, 1)


def _legwork_allowed(char, key: str) -> tuple[bool, str]:
    """Whether the drift lets you do this kind of legwork."""
    rule = LEGWORK_DRIFT.get(key)
    if rule is None:
        return True, ''
    kind, threshold = rule
    if kind == 'floor' and char.dissonance < threshold:
        return False, (f'that is not something you can do yet. It needs '
                       f'{threshold} Dissonance and you have '
                       f'{char.dissonance}.')
    if kind == 'ceiling' and char.dissonance >= threshold:
        return False, ('nobody is going to have that conversation with you '
                       'any more.')
    return True, ''


def _legwork_refusal(key: str) -> str:
    if key == 'employee':
        return drift.SOCIAL_REFUSED
    return ('You try. Whatever the trick is, it is not one you have yet, and '
            'you spend an hour listening to traffic that stays traffic.')


def _legwork_result(net, gives: str, bonus: int, game) -> str:
    """Turn a generated network into something a player can act on."""
    if gives == 'topology':
        counts = {}
        for node in net.nodes.values():
            counts[node.zone] = counts.get(node.zone, 0) + 1
        shape = ', '.join(f'{v} in {k}' for k, v in counts.items())
        return (f'{len(net.nodes)} hosts: {shape}. Entry at '
                f'[accent]{net.entry}[/].')
    if gives == 'ice':
        seen = {}
        for node in net.nodes.values():
            for construct in node.ice:
                seen[construct.data.name] = seen.get(construct.data.name, 0) + 1
        if not seen:
            return 'Their fixer laughs. There is almost nothing on it.'
        listed = ', '.join(f'{v}x {k}' for k, v in sorted(seen.items()))
        detail = f' Deepest sits on [accent]{net.objective_node}[/].' if bonus else ''
        return f'Countermeasures: {listed}.{detail}'
    if gives == 'credential':
        return ('You have a working badge. Access tier 1 from the moment you '
                'jack in.')
    if gives == 'assets':
        best = []
        for node in net.nodes.values():
            for asset in node.data:
                best.append((asset.value, asset.name, node.uid))
        best.sort(reverse=True)
        top = best[:3 + bonus]
        listed = '; '.join(f'{name} on [accent]{host}[/] ({value:,}c)'
                           for value, name, host in top)
        return f'Worth taking: {listed}.'
    return 'Nothing useful.'


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _advance(sess, shifts: int) -> None:
    """Move time and report what the world did. Every shift-spending command
    routes through here so nothing can silently skip fallout."""
    game = sess.require_game()
    told = game.city.advance(game.rng, game.alias, shifts,
                             debt=game.debt, char=game.char)
    for line in told:
        sess.console.say(line)
    _rot(sess, shifts)
    _drift(sess)
    sess.autosave()


def _rot(sess, shifts: int) -> None:
    """Hoarder: a deck full of things that nearly work gets worse on its own.

    Only touches components that are already damaged, so it is a tax on
    neglect rather than on owning a deck.
    """
    game = sess.game
    if game is None or 'rot' not in game.char.riders():
        return
    deck = game.char.deck
    hurt = [slot for slot, level in deck.damage.items() if 0 < level < 3]
    if not hurt:
        return
    stream = game.rng('events')
    for _ in range(shifts):
        if hurt and stream.chance(0.12):
            slot = stream.pick(hurt)
            level = deck.hurt(slot, 1)
            comp = deck.component(slot)
            sess.console.warn(
                f'{comp.name if comp else slot} has got worse sitting there '
                f'[dim](damage {level}/3)[/].')
            hurt = [s for s, l in deck.damage.items() if 0 < l < 3]


def _drift(sess) -> None:
    """Print any Dissonance passage the player has newly earned.

    Called from `_advance` and from anything that moves Dissonance directly,
    so a band is never crossed silently however it happened: chrome fitted, a
    creeping-dissonance rider ticking over after a run, or grounding walking
    it back and then forward again later.
    """
    game, c = sess.game, sess.console
    if game is None:
        return
    for passage in game.char.new_passages():
        c.blank()
        c.rule(passage.title, role='accent2')
        c.say(f'[accent2]{passage.text}[/]')


def _item(listing):
    table = {'program': programs.BY_KEY, 'ware': cyberware.BY_KEY,
             'component': hardware.BY_KEY}
    return table[listing.kind].get(listing.key)


def _listing_detail(listing, item) -> str:
    if listing.kind == 'program':
        return f'{item.category}, {item.memory}mem, rating {item.rating}'
    if listing.kind == 'ware':
        return f'{item.location}, {item.bandwidth}bw, {item.dissonance}dis'
    return f'{item.slot}'


def _find_program(query: str | None, pool: list[str]) -> str:
    if not query:
        raise CommandError('which program?')
    q = query.lower()
    for key in pool:
        p = programs.BY_KEY.get(key)
        if p and (q == key or q in p.name.lower()):
            return key
    raise CommandError(f'nothing called {query!r} available')


def _find_ware(query: str | None, pool: list[str]) -> str:
    if not query:
        raise CommandError('which cyberware?')
    q = query.lower()
    for key in pool:
        w = cyberware.BY_KEY.get(key)
        if w and (q == key or q in w.name.lower()):
            return key
    raise CommandError(f'nothing called {query!r} available')


def _library_names(sess) -> list[str]:
    if sess.game is None:
        return []
    return [programs.BY_KEY[k].name.lower() for k in sess.game.char.library
            if k in programs.BY_KEY]


def _loaded_names(sess) -> list[str]:
    if sess.game is None:
        return []
    return [programs.BY_KEY[k].name.lower()
            for k in sess.game.char.deck.loaded if k in programs.BY_KEY]


# --------------------------------------------------------------------------
# the other runners
# --------------------------------------------------------------------------


@command('who', 'The other runners, and what they think of you.',
         group='info', aliases=('rivals',), usage='who [name]',
         detail='Rivals take work off the board while you deliberate, and '
                'when they succeed the target hardens. Sitting still is not a '
                'free way to let heat cool: it is a way to let somebody else '
                'make the city more expensive.')
def cmd_who(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    pool = game.city.rivals

    if len(args):
        query = args.rest().lower()
        rival = next((r for r in pool
                      if query in r.name.lower() or query == r.key), None)
        if rival is None:
            raise CommandError(f'nobody called {query!r}')
        data = rival.data
        c.header(data.name, data.handle)
        c.say(data.blurb)
        c.blank()
        c.say(f'[dim]{data.manner}[/]')
        c.blank()
        c.kv([
            ('style', f'{data.style} [dim]'
                      f'{rival_content.STYLE_BLURB[data.style]}[/]'),
            ('takes', ', '.join(data.prefers)),
            ('jobs run', str(rival.jobs)),
            ('thinks of you', f'{rival.disposition:+d} [dim]{rival.band}[/]'),
        ])
        if not rival.alive:
            c.blank()
            c.err(f'Dead. Shift {rival.died}.')
        if rival.last:
            c.blank()
            c.say(f'[dim]Last heard: {rival.last}[/]')
        standing = [(k, v) for k, v in sorted(rival.rep.items()) if v]
        if standing:
            c.blank()
            c.rule('their standing')
            c.kv([(factions.BY_KEY[k].short, f'{v:+d}') for k, v in standing])
        return

    living = [r for r in pool if r.alive]
    c.header('Runners', f'{len(living)} still working')
    rows = []
    for rival in pool:
        data = rival.data
        rows.append((
            data.handle,
            data.style,
            str(rival.jobs),
            f'{rival.disposition:+d} {rival.band}' if rival.alive
            else f'[err]dead, shift {rival.died}[/]',
        ))
    c.table(('who', 'style', 'jobs', 'about you'), rows,
            roles=('accent', 'dim', 'dim', None))
    c.blank()
    c.say('[dim]`who <name>` for detail.[/]')


@command('hire', 'Pay a runner to come in with you.',
         group='prep', usage='hire [name] [--confirm]',
         detail='An ally runs alongside you on your next job. What they are '
                'worth depends entirely on their style: a chromed one steps '
                'into strikes aimed at you, a quiet one keeps the room quiet, '
                'a loud one adds their skill to everything you break. They '
                'take a fee up front and a quarter of the haul, and they can '
                'die in there.')
def cmd_hire(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if sess.run is not None:
        raise CommandError('you are already inside.')
    pool = game.city.rivals

    if not len(args):
        if game.city.hired:
            who = game.city.rival(game.city.hired)
            c.ok(f'{who.name} is already on the next job.')
            c.say('[dim]`hire --cancel` to call it off. The fee does not '
                  'come back.[/]')
            return
        c.header('For hire', f'{game.char.credits:,}c')
        rows = []
        for rival in pool:
            ok, why = rival_world.can_hire(rival)
            style, _ = rival_content.ALLY_SPECIALTY[rival.data.style]
            price = rival_world.hire_price(rival)
            rows.append((rival.data.handle, rival.data.style, style,
                         f'{price:,}c' if ok else '[err]no[/]'))
        c.table(('who', 'style', 'what you get', 'fee'), rows,
                roles=('accent', 'dim', 'dim', 'credit'))
        c.blank()
        c.say(f'[dim]They also take {int(rival_world.HIRE_CUT * 100)}% of the '
              f'haul. `hire <name> --confirm`.[/]')
        return

    if args.has('cancel'):
        game.city.hired = ''
        c.ok('Called off.')
        return

    query = args.rest().replace('--confirm', '').strip().lower()
    rival = next((r for r in pool
                  if query in r.name.lower() or query == r.key
                  or query == r.data.handle.lower()), None)
    if rival is None:
        raise CommandError(f'nobody called {query!r}')

    ok, why = rival_world.can_hire(rival)
    if not ok:
        raise CommandError(why)
    price = rival_world.hire_price(rival)
    style, detail = rival_content.ALLY_SPECIALTY[rival.data.style]

    if not args.has('confirm'):
        c.header(rival.name, f'{price:,}c up front')
        c.say(f'[dim]{rival.data.manner}[/]')
        c.blank()
        c.kv([('style', f'{rival.data.style}, {style}'),
              ('what that means', detail),
              ('their cut', f'{int(rival_world.HIRE_CUT * 100)}% of the haul'),
              ('how they feel', f'{rival.disposition:+d} {rival.band}')])
        c.blank()
        c.say(f'[dim]`hire {rival.data.handle.lower()} --confirm`.[/]')
        return

    if price > game.char.credits:
        raise CommandError(f'{rival.name} wants {price:,}c and you have '
                           f'{game.char.credits:,}c')
    game.char.credits -= price
    game.city.hired = rival.key
    rival.adjust_disposition(4)
    c.ok(f'{rival.name} is in. [credit]{price:,}c[/] gone, and a '
         f'{int(rival_world.HIRE_CUT * 100)}% cut of whatever you carry out.')


@command('ask', 'Ask somebody about something, or a runner for a favour.',
         group='prep', usage='ask <name> <topic|favour>',
         detail='With one of the city\'s people, asks about a subject they '
                'have an opinion on: `look` around to find them first. With a '
                'rival runner, calls in a favour, which is priced in '
                'disposition rather than credits and does not grow back.')
def cmd_ask(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    # One verb, two meanings. People get asked about things; colleagues get
    # asked for things.
    from .people import ask_npc
    if ask_npc(sess, args):
        return
    pool = game.city.rivals

    if len(args) < 2:
        c.header('Favours', 'what people will do, and what it costs them')
        rows = []
        for kind, (cost, blurb, detail) in rival_content.FAVOURS.items():
            rows.append((kind, str(cost), blurb))
        c.table(('favour', 'needs', 'what it is'), rows,
                roles=('accent', 'warn', 'dim'))
        c.blank()
        c.say('[dim]`needs` is the disposition they have to be at. '
              '`ask <name> <favour>`.[/]')
        c.blank()
        rows = [(r.data.handle, f'{r.disposition:+d}', r.band)
                for r in pool if r.alive]
        c.table(('who', 'disposition', ''), rows,
                roles=('accent', None, 'dim'))
        return

    query = args[0].lower()
    rival = next((r for r in pool
                  if query in r.name.lower() or query == r.key
                  or query == r.data.handle.lower()), None)
    if rival is None:
        raise CommandError(f'nobody called {query!r}')

    kind = args[1].lower()
    matches = [k for k in rival_content.FAVOURS if k.startswith(kind)]
    if len(matches) != 1:
        raise CommandError('which favour: '
                           + ', '.join(rival_content.FAVOURS))
    kind = matches[0]

    ok, why = rival_world.can_ask(rival, kind)
    if not ok:
        c.blank()
        c.say(f'[err]{game.rng("events").pick(rival_content.REFUSALS)}[/]')
        c.blank()
        c.say(f'[dim]{why}[/]')
        return

    cost = rival_world.favour_cost(kind)
    if 'owes_a_favour' in game.char.riders():
        # The street knows you are already carrying one.
        cost = int(cost * 1.4)
        c.say('[dim]They mention, without mentioning it, that you already owe '
              'somebody.[/]')
    rival.adjust_disposition(-cost)
    _grant_favour(sess, rival, kind)


def _grant_favour(sess, rival, kind: str) -> None:
    game, c = sess.game, sess.console
    stream = game.rng('events')

    if kind == 'intel':
        contract = game.city.current
        if contract is None:
            raise CommandError('take a contract first: intel is about a target.')
        net_stream = game.rng.fork('network', contract.cid)
        from ..run import network as net_mod
        net = net_mod.generate(net_stream, contract.target,
                               int(contract.posture), contract.objective,
                               contract.size_mod)
        for gives in ('topology', 'ice'):
            if gives not in contract.intel:
                contract.intel[gives] = _legwork_result(
                    net, gives, rival.data.skill // 3, game)
        c.ok(f'{rival.name} sends over everything they have on '
             f'{contract.target_data.short}.')
        for value in contract.intel.values():
            c.say(f'[dim]{value}[/]')
        return

    if kind == 'loan':
        amount = 800 + rival.data.skill * 350
        game.char.credits += amount
        c.ok(f'[credit]{amount:,}c[/] from {rival.name}, on the '
             f'understanding that it is a loan.')
        c.say('[dim]They will mention it later. The mentioning is the '
              'interest.[/]')
        return

    if kind == 'program':
        owned = set(game.char.library) | set(game.char.deck.loaded)
        pool = [p for p in programs.PROGRAMS
                if p.tier <= 2 and p.key not in owned]
        if not pool:
            raise CommandError(f'{rival.name} has nothing you do not.')
        pick = stream.pick(pool)
        game.char.library.append(pick.key)
        c.ok(f'{rival.name} drops you a copy of {pick.name}.')
        c.say(f'[dim]{pick.blurb}[/]')
        return

    if kind == 'cover':
        hot, heat = game.alias.hottest
        if not hot:
            raise CommandError('nobody is looking for you. Save it.')
        game.alias.add_heat(hot, -min(30, heat))
        c.ok(f'{rival.name} puts you somewhere else on the night in '
             f'question. [dim]{factions.BY_KEY[hot].short} heat down to '
             f'{game.alias.attention(hot)}.[/]')
        c.say('[dim]They are lying for you and you both know what that is '
              'worth.[/]')
        return


@command('betray', 'Sell a runner\'s name to somebody who wants it.',
         group='prep', usage='betray <name> [buyer] [--confirm]',
         aliases=('sellout',),
         detail='The most lucrative thing in the game and the most expensive. '
                'Everybody who worked with them cools on you, permanently, and '
                'there is a real chance the person you sold does not survive '
                'being found. Nothing about this is reversible.')
def cmd_sell_out(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if not len(args):
        raise CommandError('betray whom? `who` for the list.')

    query = args[0].lower()
    rival = next((r for r in game.city.rivals
                  if query in r.name.lower() or query == r.key
                  or query == r.data.handle.lower()), None)
    if rival is None:
        raise CommandError(f'nobody called {query!r}. `who` for the list, '
                           f'and `sell` if you meant a program.')
    if not rival.alive:
        raise CommandError(f'{rival.name} is already dead. Nobody is paying.')

    buyers = rival_world.bounty_buyers(rival)
    if not buyers:
        raise CommandError(f'nobody wants {rival.name} badly enough to pay '
                           f'for them. They have not annoyed the right people '
                           f'yet.')

    buyer_key = args.get(1, '').lower() if len(args) > 1 else ''
    buyer_key = '' if buyer_key.startswith('--') else buyer_key
    if not buyer_key:
        c.header(f'Buyers for {rival.name}', f'{len(buyers)} interested')
        c.table(('buyer', 'pays'),
                [(factions.BY_KEY[k].name, f'{v:,}c') for k, v in buyers],
                roles=('accent', 'credit'))
        c.blank()
        c.say(f'[dim]`betray {rival.data.handle.lower()} <buyer> '
              f'--confirm`.[/]')
        return

    match = next((k for k, _ in buyers if k.startswith(buyer_key)), None)
    if match is None:
        raise CommandError(f'{buyer_key!r} is not buying. Interested: '
                           + ', '.join(k for k, _ in buyers))
    price = dict(buyers)[match]

    if not args.has('confirm'):
        c.blank()
        c.warn(f'Selling {rival.name} to {factions.BY_KEY[match].name} for '
               f'{price:,}c.')
        c.say('[dim]This is permanent. Every runner who works with them will '
              'think less of you, and there is a good chance they do not '
              'survive it.[/]')
        c.blank()
        c.say(f'[dim]`betray {rival.data.handle.lower()} {match} '
              f'--confirm`.[/]')
        return

    result = rival_world.sell_out(game.rng('events'), rival, match,
                                  game.city.rivals, game.alias,
                                  game.city.shift)
    game.char.credits += result['price']
    game.earned += result['price']

    stream = game.rng('events')
    c.blank()
    c.rule('sold', role='err')
    c.say(f'[dim]{stream.pick(rival_content.SALE_LINES).format(name=rival.name)}[/]')
    c.blank()
    c.say(f'[credit]{result["price"]:,}c[/].')
    c.blank()
    line = stream.pick(rival_content.SALE_OUTCOMES[result['outcome']])
    c.say(f'[err]{line.format(name=rival.name, buyer=factions.BY_KEY[match].short)}[/]')
    c.blank()
    c.say(f'[dim]{stream.pick(rival_content.SALE_FALLOUT)}[/]')
    game.city.news.append(f'You sold {rival.name} to '
                          f'{factions.BY_KEY[match].short}.')
    sess.autosave()


# --------------------------------------------------------------------------
# the clinic, and the drift
# --------------------------------------------------------------------------


@command('clinic', 'What a clinic will do to you, and for you.',
         group='character', usage='clinic',
         detail='Clinics fit chrome, take it out again, and past a certain '
                'point sell you things the front desk does not list. They are '
                'also the only place that will try to walk your Dissonance '
                'back, which is expensive, slow, and does not undo what the '
                'chrome already cost.')
def cmd_clinic(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    char = game.char
    if 'clinic' not in game.city.district.services:
        where = ', '.join(d.name for d in districts.with_service('clinic'))
        raise CommandError(f'no clinic here. Try: {where}')

    band = char.dissonance_band
    c.header(f'{game.city.district.name} clinic',
             f'Dissonance {char.dissonance}, {band[1]}')
    c.say(f'[dim]{band[2]}[/]')

    listings = game.city.listings('ware', deep=False)
    if listings:
        c.blank()
        c.rule('on the shelf')
        rows = []
        for listing in listings:
            ware = cyberware.BY_KEY.get(listing.key)
            if ware is None:
                continue
            price, _ = market_mod.quote(listing, game.city.where, game.alias,
                                        char.dissonance,
                                        char.mult('price_mult'))
            rows.append((ware.name, ware.location,
                         f'{ware.bandwidth}bw {ware.dissonance}dis',
                         f'{price:,}c'))
        c.table(('chrome', 'slot', 'costs you', 'price'), rows,
                roles=('accent', 'dim', 'dim', 'credit'))

    # The back room, per the drift arc.
    deep = game.city.listings('ware', deep=True)
    if char.dissonance >= drift.DEEP_CLINIC_BAND and deep:
        c.blank()
        c.rule('the back of the clinic', role='accent2')
        c.say(f'[dim]{drift.DEEP_CLINIC_ARRIVAL}[/]')
        c.blank()
        rows = []
        for listing in deep:
            ware = cyberware.BY_KEY.get(listing.key)
            if ware is None:
                continue
            price, _ = market_mod.quote(listing, game.city.where, game.alias,
                                        char.dissonance,
                                        char.mult('price_mult'))
            rows.append((ware.name, ware.location,
                         f'{ware.bandwidth}bw {ware.dissonance}dis',
                         f'{price:,}c'))
        c.table(('chrome', 'slot', 'costs you', 'price'), rows,
                roles=('accent2', 'dim', 'dim', 'credit'))
    elif deep:
        c.blank()
        c.say(f'[dim]{drift.DEEP_CLINIC_REFUSED}[/]')

    c.blank()
    c.rule('grounding')
    floor = char.chrome_dissonance
    if char.dissonance <= floor:
        c.say(f'[dim]{drift.GROUND_FLOOR_TEXT}[/]')
        c.info(f'Your chrome accounts for all {floor} of it. Take something '
               f'out first.')
    else:
        c.kv([('cost', f'[credit]{drift.GROUND_COST:,}c[/]'),
              ('takes', f'{drift.GROUND_SHIFTS} shifts'),
              ('returns', f'{drift.GROUND_POINTS[0]} to '
                          f'{drift.GROUND_POINTS[1]} Dissonance'),
              ('floor', f'{floor}, which is what your chrome accounts for')])
        c.say('[dim]`ground --confirm` to book it.[/]')

    c.blank()
    c.say('[dim]`buy <name>` here, `install <name>` to have it fitted, '
          '`uninstall <name>` to have it taken out.[/]')


@command('ground', 'Have your Dissonance walked back. Expensive and partial.',
         group='character', usage='ground [--confirm]',
         detail='Three shifts of neurological work that hurts and does not '
                'finish the job. It cannot take you below what your installed '
                'chrome accounts for, because you can walk back what the work '
                'did to you and not the hardware while it is still in you.')
def cmd_ground(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    char = game.char
    if 'clinic' not in game.city.district.services:
        raise CommandError('grounding needs a clinic.')

    floor = char.chrome_dissonance
    if char.dissonance <= floor:
        raise CommandError(
            f'they will not take you below {floor}, which is what your chrome '
            f'accounts for. Take something out first.')
    if char.credits < drift.GROUND_COST:
        raise CommandError(f'the course is {drift.GROUND_COST:,}c and you have '
                           f'{char.credits:,}c')

    if not args.has('confirm'):
        c.warn(f'{drift.GROUND_COST:,}c and {drift.GROUND_SHIFTS} shifts, for '
               f'{drift.GROUND_POINTS[0]} to {drift.GROUND_POINTS[1]} '
               f'Dissonance back and a real amount of damage.')
        c.say('[dim]It does not return anything the chrome already cost you. '
              '`ground --confirm`.[/]')
        return

    stream = game.rng('events')
    before = char.dissonance
    given = stream.int(*drift.GROUND_POINTS)
    char.dissonance = max(floor, char.dissonance - given)
    hurt = stream.int(*drift.GROUND_HURT)
    char.hurt = min(char.integrity_max - 1, char.hurt + hurt)
    char.credits -= drift.GROUND_COST

    c.blank()
    c.rule('grounding')
    c.say(drift.GROUND_TEXT)
    c.blank()
    c.kv([('Dissonance', f'{before} -> [accent]{char.dissonance}[/] '
                         f'[dim]({char.dissonance_band[1]})[/]'),
          ('cost', f'[credit]{drift.GROUND_COST:,}c[/]'),
          ('damage', f'[err]{hurt}[/] integrity')])

    gap = char.coherence_gap
    if gap:
        c.blank()
        c.warn(f'{char.icon_data.name} does not fit you any more. You are '
               f'{gap} short of the drift it needs.')
    _advance(sess, drift.GROUND_SHIFTS)


@command('debt', 'What you owe, to whom, and what it is doing.',
         group='city', aliases=('owe',), usage='debt [pay <amount>|pay all]',
         detail='Debt compounds every shift and the lender is not a bank. '
                'After a grace period they start collecting in person, and if '
                'the account is empty they take it out of the room instead. '
                'It is survivable: collections reduce it faster than interest '
                'grows it, so it is a spiral you get dragged down rather than '
                'one you fall out of the bottom of.')
def cmd_debt(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    owed = game.debt

    if not owed.owed:
        c.info('You do not owe anybody anything. Enjoy it.')
        return

    if args.get(0, '').lower() == 'pay':
        target = args.get(1, '')
        if target.lower() == 'all':
            amount = min(game.char.credits, owed.amount)
        else:
            amount = args.int_at(1, 0, 'an amount, or `all`')
        if amount <= 0:
            raise CommandError('pay how much? `debt pay 2000` or `debt pay all`')
        if amount > game.char.credits:
            raise CommandError(f'you have {game.char.credits:,}c')
        applied = owed.pay(amount)
        game.char.credits -= applied
        c.ok(f'[credit]{applied:,}c[/] against it. '
             f'[dim]{owed.amount:,}c outstanding.[/]')
        if not owed.owed:
            c.blank()
            c.say('[ok]That is the last of it.[/] [dim]Nobody sends a letter. '
                  'The number simply stops being a thing you carry.[/]')
        return

    lender = factions.BY_KEY.get(owed.lender)
    shifts_in = game.city.shift - owed.opened
    c.header('Outstanding', lender.name if lender else owed.lender)
    if owed.note:
        c.say(f'[dim]{owed.note}[/]')
        c.blank()
    per_shift = int(owed.amount * debt_mod.RATE)
    if shifts_in < debt_mod.GRACE:
        when = f'{debt_mod.GRACE - shifts_in} shifts before they call'
    elif owed.last_collected < 0:
        when = 'they are collecting'
    else:
        due = owed.last_collected + debt_mod.COLLECT_EVERY - game.city.shift
        when = (f'{max(0, due)} shifts to the next collection')
    c.kv([('amount', f'[err]{owed.amount:,}c[/]'),
          ('growing by', f'[warn]{per_shift:,}c[/] a shift'),
          ('status', when),
          ('you have', f'[credit]{game.char.credits:,}c[/]')])
    c.blank()
    c.say('[dim]`debt pay <amount>` or `debt pay all`.[/]')


@command('repair', 'Have the deck put back together. Needs a workshop.',
         group='character', usage='repair [--confirm]',
         detail='Damage degrades a component rather than killing it outright, '
                'so a scratched deck still works and a neglected one quietly '
                'stops being the deck you built. The curve is steep on '
                'purpose: letting damage accumulate is a real mistake.')
def cmd_repair(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    char = game.char
    if 'workshop' not in game.city.district.services:
        where = ', '.join(d.name for d in districts.with_service('workshop'))
        raise CommandError(f'no workshop here. Try: {where}')

    damaged = [(slot, level) for slot, level in sorted(char.deck.damage.items())
               if level]
    if not damaged:
        c.info('Nothing on the deck needs work.')
        return

    mult = char.mult('repair_mult')
    cost = char.deck.repair_cost(mult)
    c.header('Repairs', f'{cost:,}c')
    rows = []
    for slot, level in damaged:
        comp = char.deck.component(slot)
        state = 'destroyed' if level >= 3 else f'damage {level}/3'
        rows.append((slot, comp.name if comp else '-', state))
    c.table(('slot', 'component', 'state'), rows,
            roles=('dim', 'accent', 'warn'))
    if mult != 1.0:
        c.blank()
        c.say(f'[dim]{char.origin_data.passive}: '
              f'{fx.describe("repair_mult", mult)}.[/]')

    if not args.has('confirm'):
        c.blank()
        c.say(f'[dim]`repair --confirm` for {cost:,}c.[/]')
        return
    if cost > char.credits:
        raise CommandError(f'that is {cost:,}c and you have '
                           f'{char.credits:,}c')
    char.credits -= cost
    char.deck.repair()
    c.ok(f'Deck rebuilt for [credit]{cost:,}c[/].')
    _advance(sess, 1)


@command('trait', 'What you are like. Permanent, and there are never enough '
                  'slots.',
         group='character', aliases=('traits',),
         usage='trait [<key>] [--confirm]',
         detail='Skills say what you can do; traits say what you are like. '
                'You pick two at creation and earn one more every six runs, '
                'to a maximum of five, out of a pool of twenty-six. Nothing '
                'here is purely good and nothing here can be taken back.')
def cmd_trait(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    char = game.char

    key = (args.get(0) or '').lower()
    if key:
        match = next((k for k in trait_content.TRAIT_KEYS
                      if k == key
                      or key in trait_content.BY_KEY[k].name.lower()), None)
        if match is None:
            raise CommandError(f'no trait called {key!r}')
        trait = trait_content.BY_KEY[match]

        if match in char.traits:
            _show_trait(c, trait, held=True)
            return
        ok, why = char.can_take_trait(match)
        if not args.has('confirm'):
            _show_trait(c, trait, held=False)
            c.blank()
            if ok:
                c.say(f'[warn]This is permanent.[/] '
                      f'[dim]`trait {match} --confirm` to take it.[/]')
            else:
                c.err(why)
            return
        if not ok:
            raise CommandError(why)
        char.take_trait(match)
        c.blank()
        c.ok(f'You are {trait.name.lower()} now.')
        c.say(f'[dim]{trait.blurb}[/]')
        c.blank()
        c.say(f'[warn]{trait.drawback}[/]')
        sess.autosave()
        return

    c.header('Traits', f'{len(char.traits)}/{char.trait_slots} taken')
    if char.traits:
        for held in char.traits:
            trait = trait_content.BY_KEY[held]
            c.blank()
            c.raw(f'[accent][bold]{trait.name}[/][/]  [dim]{trait.key}[/]')
            c.say(f'[dim]{trait.blurb}[/]', indent='  ', subsequent='  ')
            c.say(f'[warn]{trait.drawback}[/]', indent='  ', subsequent='  ')
    else:
        c.say('[dim]None yet.[/]')

    if not char.trait_picks:
        c.blank()
        nxt = ((trait_content.earned(char.runs) + 1)
               * trait_content.EARN_EVERY)
        if len(char.traits) >= trait_content.MAX_TRAITS:
            c.say('[dim]That is all of them. Five is the ceiling.[/]')
        else:
            c.say(f'[dim]Next slot at {nxt} runs. You have {char.runs}.[/]')
        return

    c.blank()
    c.rule(f'{char.trait_picks} to spend')
    open_now = trait_content.available(char.traits, char)
    for group in trait_content.GROUPS:
        pool = [t for t in open_now if t.group == group]
        if not pool:
            continue
        c.blank()
        c.raw(f'[accent2]{trait_content.GROUP_TITLES[group]}[/]')
        width = max(len(t.key) for t in pool)
        for trait in pool:
            pad = ' ' * (width - len(trait.key))
            c.say(f'  [fg]{trait.key}[/]{pad}  [dim]{trait.name}[/]',
                  subsequent=' ' * (width + 4))
    c.blank()
    c.say('[dim]`trait <key>` to read one properly. Nothing here is purely '
          'good, and nothing here comes back off.[/]')


def _show_trait(c, trait, held: bool) -> None:
    c.header(trait.name, 'held' if held else trait.key)
    c.say(trait.blurb)
    c.blank()
    c.say(f'[warn]{trait.drawback}[/]')
    rows = []
    for key, value in sorted(trait.effects.items()):
        rows.append((fx.describe(key, value), '[ok]for you[/]'))
    for key, value in sorted(trait.penalty.items()):
        rows.append((fx.describe(key, value), '[err]against you[/]'))
    if trait.rider:
        rows.append((f'{trait.rider.replace("_", " ")}', '[warn]a rule[/]'))
    if rows:
        c.blank()
        c.kv(rows)
    if trait.excludes:
        c.blank()
        c.say('[dim]Does not go with: '
              + ', '.join(trait_content.BY_KEY[k].name
                          for k in trait.excludes) + '[/]')
