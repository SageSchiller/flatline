"""City commands: the build, the board, the market, and the door to a run.

Everything here costs either credits or shifts, and the ones that cost shifts
say so before they take them. Time is the city's real currency and a command
that quietly spends three of it is a command that has lied.
"""

from __future__ import annotations

from ..content import attributes as attr_content
from ..content import cyberware, districts, effects as fx, factions
from ..content import hardware, origins, programs
from ..content import skills as skill_content
from ..game import Game
from ..model.character import Character
from ..model.identity import ALIAS_COST, ALIAS_SHIFTS
from ..rng import random_seed
from ..shell import CommandError, command
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
          '`train <skill>` to spend, `board` when you are ready to work.[/]')


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

    listings = game.city.listings(kind)
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
    listings = game.city.listings()
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

    danger, who = game.city.danger(game.alias, target)
    game.city.where = target
    district = districts.BY_KEY[target]
    _advance(sess, 1)
    c.blank()
    c.rule(district.name)
    c.say(district.arrival)
    if danger >= 45:
        c.blank()
        c.warn(f'{factions.BY_KEY[who].short} have people here and they are '
               f'looking for your name. Do not linger.')


@command('rest', 'Lie low. Heals, cools heat, and passes time.',
         group='city', usage='rest [shifts]')
def cmd_rest(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    shifts = max(1, min(12, args.int_at(0, 1, 'a number of shifts')))
    safe = 'safehouse' in game.city.district.services
    before = game.char.hurt
    heal = (2 if safe else 1) * shifts
    game.char.hurt = max(0, game.char.hurt - heal)
    _advance(sess, shifts)
    healed = before - game.char.hurt
    c.ok(f'{shifts} shift{"s" if shifts != 1 else ""} pass.'
         + (f' [ok]Integrity +{healed}.[/]' if healed else ''))
    if not safe:
        c.info('No safehouse here. You did not sleep well.')


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
    c.say(f'[dim]`burn` to take a new name: {ALIAS_COST:,}c and '
          f'{ALIAS_SHIFTS} shifts, and everything above goes with it.[/]')


@command('burn', 'Abandon this identity and establish another.',
         group='prep', usage='burn [name] [--confirm]')
def cmd_burn(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    alias = game.alias
    if game.char.credits < ALIAS_COST:
        raise CommandError(f'a new name costs {ALIAS_COST:,}c and you have '
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
    game.char.credits -= ALIAS_COST
    fresh = game.new_alias(name)
    _advance(sess, ALIAS_SHIFTS)
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
            have = '[ok]done[/]' if key in contract.intel else ''
            rows.append((key, f'{cost:,}c' if cost else 'free', blurb, have))
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
    contract.intel[gives] = _legwork_result(net, gives, bonus, game)
    c.ok(f'{key.title()} done.')
    c.say(contract.intel[gives])
    _advance(sess, 1)


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
    told = game.city.advance(game.rng, game.alias, shifts)
    for line in told:
        sess.console.say(line)
    sess.autosave()


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
