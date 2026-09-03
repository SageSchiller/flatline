"""City commands: the build, the board, the market, and the door to a run.

Everything here costs either credits or shifts, and the ones that cost shifts
say so before they take them. Time is the city's real currency and a command
that quietly spends three of it is a command that has lied.
"""

from __future__ import annotations

from ..content import appearance
from ..content import attributes as attr_content
from ..content import cyberware, dissonance as drift, districts
from ..content import drugs as drug_content
from ..content import effects as fx, factions, games
from ..content import hardware, icons, lenders, offers, origins, programs
from ..content import rivals as rival_content
from ..content import shifts
from ..content import skills as skill_content
from ..content import traits as trait_content
from ..game import Game
from ..model.character import Character
from ..model import identity
from ..model.identity import ALIAS_COST, ALIAS_SHIFTS
from ..rng import random_seed
from .. import save as save_mod
from .. import ui
from ..shell import Args, CommandError, command
from ..world import city as city_mod
from ..world import contracts as contract_mod
from ..world import debt as debt_mod
from ..world import fallout
from ..world import street as street_world
from ..world import rivals as rival_world
from ..world import market as market_mod


# --------------------------------------------------------------------------
# creation
# --------------------------------------------------------------------------


@command('new', 'Make a character.',
         contexts=('city',), group='character', bare=True,
         usage='new [handle --origin <key|number> [--seed n]] [--long]',
         detail='With nothing after it, it asks: which origin, what to call '
                'them, and whether to spend the opening points the usual way '
                'for that origin. `new <handle> --origin <key>` does the '
                'same in one line, for anybody who has picked already; the '
                'origin can be its number from the list. `new --long` is '
                'every origin in full. Creation gives you an attribute budget '
                'and an experience budget, which you spend with `boost` and '
                '`train`: the same commands you will use for the rest of the '
                'character\'s life.')
def cmd_new(sess, args) -> None:
    c = sess.console
    if not len(args) and not args.opt('origin'):
        if args.has('long') or args.has('list') or args.has('all'):
            list_origins(sess)
            return
        from . import guide
        guide.start_creation(sess)
        return

    if sess.run is not None:
        raise CommandError('finish the run first.')

    if not args.opt('origin'):
        # A name and nothing else is one of the three answers. Ask the other
        # two rather than refusing over a flag nobody was told about.
        from . import guide
        guide.start_creation(sess, handle=args[0])
        return
    origin = resolve_origin(args.opt('origin') or '')
    if origin is None:
        raise CommandError('pick an origin: '
                           + ', '.join(origins.ORIGIN_KEYS)
                           + ', or its number. Or `new` with nothing after '
                           'it, to be asked.')
    handle = args.get(0) or 'nobody'
    seed = args.int_opt('seed', random_seed())
    create_character(sess, handle, origin.key, seed)
    c.blank()
    c.say('[dim]`char` to see the build, `spend` to put the opening points '
          'where this origin usually does, or `boost <attribute>` and '
          '`train <skill>` to spend them yourself. `trait` to decide what '
          'kind of person this is, `self` to decide what they look like, '
          'which is a real decision here and not a portrait. `board` when '
          'you are ready to work. `load` lists what you carry and `inspect '
          '<name>` says what each thing does. Enter on an empty line says what to do '
          'next.[/]')


#: The two words a build comes down to (D62). Cosmetic: it reads the build
#: and nothing reads it back. The noun is the skill you have most of, the
#: adjective the attribute, and "wired" arrives with the drift.
_BUILD_NOUN = {
    'intrusion': 'breaker', 'cryptography': 'cryptographer',
    'subterfuge': 'talker', 'hardware': 'tinker', 'stealth': 'ghost',
    'warfare': 'brawler', 'forensics': 'cleaner', 'daemonology': 'summoner',
    'architecture': 'mapper', 'signal': 'listener', 'sabotage': 'wrecker',
    'psyche': 'nerve',
}
_BUILD_ADJ = {'logic': 'careful', 'reflex': 'fast', 'nerve': 'steady',
              'guile': 'smooth', 'grit': 'hard'}


def build_label(char) -> str:
    """'a fast breaker', 'a wired careful summoner', or 'a runner' for a
    sheet with nothing on it yet."""
    best_skill = max(skill_content.SKILL_KEYS,
                     key=lambda k: (char.skill(k),
                                    -skill_content.SKILL_KEYS.index(k)))
    best_attr = max(attr_content.ATTR_KEYS,
                    key=lambda k: (char.attr(k),
                                   -attr_content.ATTR_KEYS.index(k)))
    noun = (_BUILD_NOUN.get(best_skill, 'runner') if char.skill(best_skill)
            else 'runner')
    adj = _BUILD_ADJ.get(best_attr, '')
    wired = 'wired' if char.dissonance >= 50 else ''
    words = ' '.join(w for w in (wired, adj, noun) if w)
    article = 'an' if words[:1] in 'aeiou' else 'a'
    return f'{article} {words}'


def resolve_origin(token: str):
    """An origin from its number in the list, its key, or its name. Or None.

    Numbers are the list order in `new` and `new --long`, which is the order
    of `origins.ORIGINS` and does not change between screens.
    """
    t = (token or '').strip().lower()
    if not t:
        return None
    if t.isdigit():
        n = int(t)
        return (origins.ORIGINS[n - 1]
                if 1 <= n <= len(origins.ORIGINS) else None)
    if t in origins.BY_KEY:
        return origins.BY_KEY[t]
    hits = [o for o in origins.ORIGINS
            if o.key.startswith(t) or o.name.lower().startswith(t)]
    return hits[0] if len(hits) == 1 else None


def show_origin(sess, origin, number: int | None = None) -> None:
    """One origin in full: shape, money, passive and signature."""
    c = sess.console
    c.blank()
    num = f'[dim]{number:>2}[/]  ' if number is not None else ''
    c.raw(f'{num}[accent][bold]{origin.name}[/][/]  [dim]{origin.key}[/]')
    c.say(origin.blurb, indent='  ')
    shape = '  '.join(
        f'{attr_content.BY_KEY[k].short} {v:+d}'
        for k, v in origin.attrs.items())
    c.say(f'[dim]{shape}  {origin.credits:,}c[/]', indent='  ')
    c.say(f'[warn]{origin.passive}:[/] [dim]{origin.passive_detail}[/]',
          indent='  ', subsequent='  ')
    c.say(f'[accent2]{origin.signature_name}[/] '
          f'[dim](`{origin.signature}`, once a run, nobody else '
          f'can):[/] [dim]{origin.signature_detail}[/]',
          indent='  ', subsequent='  ')


def list_origins(sess) -> None:
    """Every origin in full. The long form; `new` alone is the short one."""
    c = sess.console
    c.header('Origins', f'{len(origins.ORIGINS)} of them')
    c.say('[dim]An origin sets where you start, never where you can go.[/]')
    for i, origin in enumerate(origins.ORIGINS, 1):
        show_origin(sess, origin, i)
    c.blank()
    c.say('[dim]`new` to be asked which, or `new <handle> --origin <key>` '
          'when you have picked. The number works in place of the key.[/]')


def create_character(sess, handle: str, origin_key: str, seed: int) -> None:
    """Make them, file them, and say who they are. Both forms of `new` end here."""
    c = sess.console

    # Put the character who is already here away before making another one.
    # This used to be a refusal you cleared with `--force`, and `--force` did
    # not abandon them, it destroyed them: everybody shared one slot, so the
    # next autosave wrote the new character over the old one and nothing in
    # the game said so. Saving first is the whole fix. Nothing but `delete`
    # removes a character now.
    leaving = None
    if sess.game is not None:
        leaving = sess.game.char.handle
        sess.sync_scripts()
        sess.game.save(sess.slot)

    char = Character.from_origin(origin_key, handle)
    char.points = attr_content.CREATION_POINTS
    char.xp = skill_content.CREATION_XP
    sess.game = Game.new(char, seed=seed)
    sess.run = None
    # Filed under their own name, so having two characters is possible.
    sess.slot = save_mod.slot_for(handle)
    sess.autosave()
    if leaving is not None:
        c.blank()
        c.info(f'{leaving} is saved and waiting. `characters` to see '
               f'everybody, `switch {leaving}` to go back.')

    origin = char.origin_data
    c.blank()
    c.rule(origin.name)
    c.say(origin.story)
    c.blank()
    c.say(f'[warn]{origin.passive}.[/] {origin.passive_detail}')
    c.blank()
    c.say(f'[accent2]{origin.signature_name}.[/] {origin.signature_detail}')
    c.say(f'[dim]`{origin.signature}`, once a run. Nobody else in this city '
          f'can do it.[/]')
    c.blank()
    c.say(f'[err]{origin.complication}[/]')
    c.blank()
    c.kv([('handle', f'[accent]{handle}[/]'),
          ('running as', f'[accent]{sess.game.alias.name}[/]'),
          ('world seed', f'[dim]{seed}[/]'),
          ('to spend', f'{char.points} attribute points, '
                       f'{char.xp} experience')])
    save_mod.bump_meta(characters_created=1)
    _inherit(sess)
    sess.record_progress()


def _inherit(sess) -> None:
    """Take whatever the last character left, if anything is waiting.

    Arrives during creation rather than being offered at it. An inheritance
    you picked from a list is a difficulty setting with prose attached; one
    that turns up on your second day is the city having an opinion about
    somebody who is no longer in it.
    """
    from ..content import legacy

    game, c = sess.game, sess.console
    estate = save_mod.claim_estate()
    bequest = legacy.BY_KEY.get(estate.get('bequest', ''))
    if bequest is None:
        return
    handle = estate.get('handle') or 'somebody'

    # The Ghost's whole complication is starting with no history: no name
    # anybody knows and nothing owed. Two of the five bequests are exactly
    # those things, and handing one over would be the inheritance quietly
    # cancelling an origin's defining line.
    if 'no_history' in game.char.riders() and bequest.key in ('name', 'debt'):
        c.blank()
        c.say(f'[dim]There was something waiting, left by {handle}. It was a '
              f'name, or a number attached to one, and either way it needed '
              f'somebody the city could find. Nobody came to collect it and '
              f'nobody will.[/]')
        return

    told = ''
    if bequest.key == 'stake':
        amount = int(estate.get('amount') or 0)
        game.char.credits += amount
        told = f'[credit]{amount:,}c[/], from an account that no longer exists.'
    elif bequest.key == 'name':
        faction = estate.get('faction') or 'fixers'
        if faction in factions.BY_KEY:
            current = game.alias.reputation(faction)
            if current < legacy.NAME_STANDING:
                game.alias.adjust_rep(faction, legacy.NAME_STANDING - current)
            told = (f'{factions.BY_KEY[faction].short} will take your call, '
                    f'and neither of you will mention why.')
    elif bequest.key == 'chrome':
        ware = estate.get('ware')
        if ware in cyberware.BY_KEY:
            game.char.library.append(ware)
            told = (f'{cyberware.BY_KEY[ware].name}, in the bag, not in you. '
                    f'`install` it at a clinic when you have decided.')
    elif bequest.key == 'program':
        key = estate.get('program')
        if key in programs.BY_KEY:
            game.char.library.append(key)
            told = f'{programs.BY_KEY[key].name}, and it still runs.'
    elif bequest.key == 'debt':
        amount = int(estate.get('amount') or 0)
        lender = estate.get('lender') or 'carrion'
        if amount > 0 and lender in factions.BY_KEY:
            game.debt = debt_mod.Debt(
                amount=amount, lender=lender, opened=game.city.shift,
                note=f'inherited from {handle}')
            told = (f'[err]{amount:,}c[/] to '
                    f'{factions.BY_KEY[lender].short}, which was not yours '
                    f'and is now.')
    if not told:
        return

    c.blank()
    c.rule(f'what {handle} left', role='accent2')
    for para in bequest.text.split('\n\n'):
        c.say(para)
        c.blank()
    c.say(told)


# --------------------------------------------------------------------------
# inspection
# --------------------------------------------------------------------------


@command('char', 'Your build, in full.',
         group='character', aliases=('sheet', 'me'),
         usage='char [--effects] [--attributes]',
         detail=(
                'The whole sheet: attributes and what they derive, the skills '
                'you have ranks in, your chrome and drift, what you look like '
                'and how memorable that makes you, and what is unspent. '
                '`spend` puts an unspent budget where your origin usually '
                'would.'))
def cmd_char(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    char = game.char
    origin = char.origin_data

    c.header(char.handle, origin.name + (f', {game.over}' if game.over else ''))
    c.kv([
        (('ran as', f'[dim]{game.alias.name}[/] [dim]({game.alias.runs} run'
                    f'{"s" if game.alias.runs != 1 else ""}), and does not '
                    f'any more[/]') if game.over else
         ('running as', f'[accent]{game.alias.name}[/] '
                        f'[dim]({game.alias.runs} run'
                        f'{"s" if game.alias.runs != 1 else ""})[/]')),
        ('credits', f'[credit]{char.credits:,}c[/]'),
        ('integrity', f'{char.integrity}/{char.integrity_max}'
                      + _warned_line(game)),
        ('dissonance', f'{char.dissonance} [dim]({char.dissonance_band[1]})[/]'),
        ('looks', f'[dim]{appearance.summary(char.look)}[/]'),
        ('read as', f'{char.memorable_band[0]} '
                    f'[dim]({char.memorable} memorable, '
                    f'{char.presence:+d} presence, `self` for detail)[/]'),
        ('plays as', f'[accent2]{build_label(char)}[/] [dim](the shape of '
                     f'the build, in two words; it reads nothing back)[/]'),
    ])

    c.blank()
    if args.has('attributes'):
        for a in attr_content.ATTRIBUTES:
            c.blank()
            c.raw(f'[accent]{a.name}[/] [dim]{a.short}, '
                  f'{char.attr(a.key)}[/]')
            c.say(a.governs, indent='  ', subsequent='  ')
            c.say(f'[dim]Short on it: {a.failure}[/]',
                  indent='  ', subsequent='  ')
        return

    rows = []
    arrow = c.caps.g('arrow')
    # What is doing it, not just how much. "+3 from gear" on a number that is
    # up because of what you took an hour ago is the sheet telling you the one
    # thing you already knew and hiding the one you needed.
    chem_now = drug_content.effects(char.chem)
    for a in attr_content.ATTRIBUTES:
        base = char.base_attrs.get(a.key, 0)
        eff = char.attr(a.key)
        if eff == base:
            rows.append((a.name, str(base)))
            continue
        shift = eff - base
        from_chem = int(round(chem_now.get(a.key, 0)))
        from_gear = shift - from_chem
        if from_chem and from_gear:
            why = f'{from_gear:+d} gear, {from_chem:+d} what is in you'
        elif from_chem:
            why = f'{from_chem:+d} from what is in you'
        else:
            why = f'{shift:+d} from gear'
        role = 'accent' if shift >= 0 else 'err'
        rows.append((a.name, f'{base} {arrow} [{role}]{eff}[/] '
                             f'[dim]({why})[/]'))
    # A bar beside each number (D62), scaled to the ceiling, the way the
    # skills screen has always done it: five numbers read faster as five
    # lengths.
    rows = [(name, c.bar(char.base_attrs.get(a.key, 0) / attr_content.ATTR_MAX,
                         'accent', 9) + f' {value}')
            for (name, value), a in zip(rows, attr_content.ATTRIBUTES)]
    c.kv(rows)

    c.blank()
    c.say(f'[accent2]{origin.signature_name}[/] '
          f'[dim]`{origin.signature}`, once a run.[/]')

    c.blank()
    c.kv([('Bandwidth', f'{char.bandwidth_used}/{char.bandwidth}'),
          ('Focus', str(char.focus)),
          ('Tempo', str(char.tempo)),
          ('Composure', str(char.composure)),
          ('Cover', str(char.cover))])

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
         contexts=('city',), group='character', usage='boost <attribute>',
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
    attribute = attr_content.BY_KEY[match[0]]
    value = game.char.boost(match[0])
    c.ok(f'{attribute.name} is now {value}. '
         f'[dim]{game.char.points} point'
         f'{"s" if game.char.points != 1 else ""} left.[/]')
    c.say(f'[dim]{attribute.governs}[/]')


def _train_index(sess) -> None:
    """Every skill, what the next rank costs, and what it buys.

    Advancement was a number that went up and a command that errored with
    a list of fourteen words. Twenty-eight techniques hang off these
    ranks and nothing said so anywhere a player would look, which is why
    somebody with eleven experience in the bank had no idea what to do
    with it (D79).
    """
    game, c = sess.require_game(), sess.console
    char = game.char
    c.header('To train', f'{char.xp} experience')
    rows = []
    for key in skill_content.SKILL_KEYS:
        skill = skill_content.BY_KEY[key]
        rank = char.skill(key)
        cost = skill_content.RANK_COST.get(rank + 1)
        nxt = next((t for t in skill.techniques if t.rank == rank + 1), None)
        if cost is None:
            rows.append((skill.name, f'{rank}', '[dim]done[/]', ''))
            continue
        afford = char.xp >= cost
        price = (f'[ok]{cost}[/]' if afford else f'[dim]{cost}[/]')
        if nxt is not None:
            gain = f'[accent]{nxt.name}[/] [dim]{nxt.summary}[/]'
        else:
            # No verb at the very next rank, so name the one it is on the
            # way to. A player planning a build needs the goal, not the
            # step, and "a better number" is not a goal.
            later = next((t for t in skill.techniques if t.rank > rank), None)
            gain = (f'[dim]a better number, and[/] [accent]{later.name}[/] '
                    f'[dim]at rank {later.rank}[/]' if later
                    else '[dim]a better number on every check it governs[/]')
        rows.append((skill.name, f'{rank}', price, gain))
    width = max(len(r[0]) for r in rows)
    for name, rank, price, gain in rows:
        pad = ' ' * (width - len(name))
        c.say(f'[fg]{name}[/]{pad}  [dim]rank[/] {rank}  [dim]next[/] {price}'
              f'  {gain}', indent='  ',
              subsequent=' ' * (width + 20))
    c.blank()
    c.say('[dim]`train <skill>` buys the next rank. Ranks cost '
          + ', '.join(str(skill_content.RANK_COST[r])
                      for r in sorted(skill_content.RANK_COST))
          + ' experience, so the fifth costs eight times the first. Two '
            'ranks in every skill open a technique, at two and at four, '
            'and a technique is a verb rather than a number.[/]',
          indent='  ', subsequent='  ')
    ready = [skill_content.BY_KEY[k] for k in skill_content.SKILL_KEYS
             if (t := next((x for x in skill_content.BY_KEY[k].techniques
                            if x.rank == char.skill(k) + 1), None)) is not None
             and char.xp >= skill_content.RANK_COST.get(char.skill(k) + 1, 999)]
    if ready:
        c.blank()
        c.say('[ok]Affordable now, and each of them a verb you do not have: '
              + ', '.join(f'`train {s.key}`' for s in ready) + '.[/]',
              indent='  ', subsequent='  ')


@command('train', 'Buy the next rank in a skill.',
         contexts=('city',), group='character', usage='train [skill]',
         bare=True,
         detail='With no argument: every skill, the rank you hold, what the '
                'next one costs, and what it buys. Two ranks in every skill '
                'open a technique, at two and at four, and a technique is a '
                'verb you did not have rather than a number that got '
                'bigger.',
         complete=lambda sess, prefix: list(skill_content.SKILL_KEYS))
def cmd_train(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    key = (args.get(0) or '').lower()
    if not key:
        _train_index(sess)
        return
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
         group='character', usage='deck [name <what you call it>]',
         detail=(
                'The six components fitted, the memory they give you, the '
                'thermal headroom overclocking spends, and what is loaded '
                'with what each program is for. `fit` changes a component, '
                '`mod` does bench work on one, `repair` fixes what a '
                'countermeasure broke.'))
def cmd_deck(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    deck = game.char.deck
    if (args.get(0) or '').lower() == 'name':
        # Naming it (D62). Cosmetic, persisted, and the only thing about
        # the deck that the deck does not read.
        name = args.rest(1).strip()
        if args.has('clear'):
            deck.name = ''
            c.ok('It is a deck again.')
        elif not name:
            raise CommandError('deck name <what you call it>. `deck name '
                               '--clear` to stop calling it anything.')
        else:
            deck.name = name[:32]
            c.ok(f'The deck is [accent]{deck.name}[/] now. It does not care, '
                 f'and it will be on every screen that mentions it.')
        sess.autosave()
        return
    c.header(deck.name or 'Deck', f'memory {deck.memory_used}/{deck.memory}  '
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
            what, _verbs = programs.CATEGORIES.get(p.category, ('', ()))
            c.say(f'[dim]{what} {p.note}[/]', indent='      ',
                  subsequent='      ')
    spare = [k for k in game.char.library if k not in deck.loaded]
    if spare:
        c.blank()
        c.say(f'[dim]In storage: '
              f'{", ".join(programs.BY_KEY[k].name for k in spare if k in programs.BY_KEY)}[/]')
    if deck.heat_headroom <= 0:
        c.blank()
        c.warn('No thermal headroom. Overclocking is not available until the '
               'cooling outpaces the components.')


def _icon_picture(sess, key: str) -> None:
    """The icon as a picture (D105), on the sheet and when you put one on,
    where the terminal can draw one. `render` mode decides; a text terminal
    reads the render string that follows either way."""
    from .. import anim, pixels
    c = sess.console
    if sess.render_mode in ('picture', 'wide') and pixels.can_render(c.caps):
        pix = pixels.render_icon(key)
        if pix:
            c.blank()
            anim.reveal(c, pix, '', quick=True)


@command('icon', 'The shape you wear in the net.',
         contexts=('city',), group='character', usage='icon [wear <key>] [buy <key>]',
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
                        * char.mult('price_mult')
                        * shifts.phase(game.city.phase).price)
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
        _icon_picture(sess, key)
        c.say(f'[dim]{icon.render}[/]')
        gap = char.coherence_gap
        if gap:
            c.warn(f'It does not fit. You are {gap} short of the Dissonance '
                   f'this shape needs, and holding it will cost you.')
        return

    icon = char.icon_data
    c.header('Icon', icon.name)
    _icon_picture(sess, char.icon)
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
         contexts=('city',), group='prep', usage='load <program>',
         blocked='The loadout is fixed the moment you jack in: what you are '
                 'carrying is what you have. `hotswap` is the only thing that '
                 'changes a deck mid-run, and it changes hardware rather than '
                 'programs.',
         complete=lambda sess, prefix: _library_names(sess),
         detail=(
                'Puts a program on the deck, out here only: the loadout is '
                'fixed from the moment you jack in. With nothing after it, '
                'lists the bag with what each thing is for. Memory is the '
                'constraint that decides your playstyle, and a program above '
                'your skill rank runs held to that rank plus two, so the '
                'strongest thing you own is not always the strongest thing '
                'you can drive.'))
def cmd_load(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if sess.run is not None:
        raise CommandError('the loadout is fixed once you are inside.')
    owned = [k for k in game.char.library if k in programs.BY_KEY]
    if not len(args):
        # D63 c: the bag, numbered, with what each thing is. `load` with
        # nothing after it used to be an error, and the only other place the
        # bag was listed was nowhere.
        deck = game.char.deck
        c.header('The bag', f'memory {deck.memory_used}/{deck.memory}')
        if not owned:
            c.say('[dim]Nothing. `market program` to buy one.[/]')
            return
        keys = []
        rows = []
        for key in owned:
            p = programs.BY_KEY[key]
            keys.append(key)
            loaded = key in deck.loaded and keys.count(key) <= deck.loaded.count(key)
            rows.append((str(len(keys)), p.name, p.category, f'{p.memory}',
                         f'{p.rating}', f'{p.signature:g}',
                         ('loaded' if loaded else
                          'fits' if p.memory <= deck.memory_free else 'no room')))
        c.table(('#', 'program', 'kind', 'mem', 'r', 'sig', 'deck'), rows,
                roles=('accent', 'accent', 'dim', 'dim', 'dim', 'dim', 'info'))
        sess.remember('load', keys)
        sess.remember('unload', [k for k in keys if k in deck.loaded])
        c.blank()
        for key in dict.fromkeys(owned):
            p = programs.BY_KEY[key]
            what, _verbs = programs.CATEGORIES.get(p.category, ('', ()))
            c.say(f'[accent]{p.name}[/][dim]: {what} {p.note}[/]',
                  indent='  ', subsequent='    ')
        c.blank()
        c.say('[dim]`load <name>` or `load <row number>`. `inspect <name>` '
              'for the whole of what one does. `unload <name|row>` to make '
              'room. `help programs` for how they work.[/]')
        return
    token = sess.pick('load', args.get(0), fallback=owned, what='program',
                      again='load')
    key = _find_program(token, game.char.library)
    ok, why = game.char.deck.can_load(key)
    if not ok:
        raise CommandError(why)
    game.char.deck.load(key)
    p = programs.BY_KEY[key]
    c.ok(f'{p.name} loaded. [dim]{game.char.deck.memory_free} memory free.[/]')


@command('unload', 'Take a program off the deck.',
         contexts=('city',), group='prep', usage='unload <program>',
         blocked='The loadout is fixed from the moment you jack in, in both '
                 'directions.',
         complete=lambda sess, prefix: _loaded_names(sess),
         detail=(
                'Takes a program off the deck to make room. With nothing '
                'after it, lists what is loaded, numbered. Only out here: '
                'what you are carrying when you jack in is what you have.'))
def cmd_unload(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if sess.run is not None:
        raise CommandError('the loadout is fixed once you are inside.')
    loaded = list(game.char.deck.loaded)
    if not len(args):
        if not loaded:
            raise CommandError('nothing is loaded.')
        c.header('Loaded', f'memory {game.char.deck.memory_used}/'
                           f'{game.char.deck.memory}')
        for n, key in enumerate(loaded, 1):
            p = programs.BY_KEY.get(key)
            if p:
                c.raw(f'  [accent]{n}[/]  [fg]{p.name}[/]  [dim]{p.category}, '
                      f'{p.memory}mem[/]')
        sess.remember('unload', loaded)
        c.blank()
        c.say('[dim]`unload <name>` or `unload <row number>`.[/]')
        return
    token = sess.pick('unload', args.get(0), fallback=loaded, what='program',
                      again='unload')
    key = _find_program(token, game.char.deck.loaded)
    game.char.deck.unload(key)
    c.ok(f'{programs.BY_KEY[key].name} unloaded. '
         f'[dim]{game.char.deck.memory_free} memory free.[/]')


@command('install', 'Have cyberware fitted. Needs a clinic.',
         contexts=('city',), group='character', usage='install <ware>',
         blocked='Surgery is a clinic, a table, and a shift of your life. It '
                 'is not something you do to yourself in a chair with a deck '
                 'in your head.',
         detail=(
                'Fits chrome at a clinic: a shift, a fee, and Dissonance you '
                'do not get back. Bandwidth is the hard limit and slots are '
                'the tight one. `uninstall` takes it out again and the drift '
                'stays, which is the whole of D11 in one sentence.'))
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
         contexts=('city',), group='character', usage='uninstall <ware>')
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
            c.raw(f'  [accent]{w.name}[/] [dim]{w.maker}, {w.bandwidth}bw '
                  f'{w.dissonance}dis[/]')
            c.say(f'[dim]{w.drawback}[/]', indent='    ', subsequent='    ')


# --------------------------------------------------------------------------
# the market
# --------------------------------------------------------------------------


@command('market', 'What is for sale here.',
         contexts=('city',), group='city', aliases=('shop',),
         usage='market [programs|ware|components]',
         detail=(
                'What is for sale here, priced for you specifically: the '
                'district\'s markup, what the controlling faction thinks of '
                'you, your Guile, your drift, and the hour. `buy <name> '
                '--why` breaks the number down. Stock rotates every six '
                'shifts, which is a reason to travel and a reason to hurry.'))
def cmd_market(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    district = game.city.district
    sellers = [s for s in district.services if s in market_mod.STOCK_KINDS]
    if not sellers:
        raise CommandError(f'nothing is sold in {district.name}.')

    want = (args.get(0) or '').rstrip('s').lower()
    kind = {'program': 'program', 'ware': 'ware', 'cyberware': 'ware',
            'component': 'component', 'part': 'component',
            'drug': 'drug', 'chem': 'drug'}.get(want)

    qualifies = game.char.dissonance >= drift.DEEP_CLINIC_BAND
    listings = game.city.listings(kind, deep=None if qualifies else False)
    if not listings:
        raise CommandError('nothing of that kind here.')

    c.header(f'{district.name} market',
             f'tier {district.max_tier} and below')
    rows = []
    shown = []
    for listing in listings:
        item = _item(listing)
        if item is None:
            continue
        price, _ = market_mod.quote(listing, game.city.where, game.alias,
                                    game.char.dissonance,
                                    game.char.mult('price_mult'),
                                    game.city.phase,
                                    game.char.attr('guile'))
        detail = _listing_detail(listing, item)
        shown.append(listing.key)
        rows.append((str(len(shown)), item.name, listing.kind, detail,
                     f'{price:,}c'))
    c.table(('#', 'item', 'kind', 'what it does', 'price'), rows,
            roles=('accent', 'accent', 'dim', 'dim', 'credit'))
    sess.remember('market', shown)
    c.blank()
    c.say('[dim]`buy <name>` or `buy <row number>` to take one. '
          '`buy <name> --why` to see the price broken down.[/]')


@command('buy', 'Buy something from the local market.',
         blocked='Nobody in here is selling, and your credits are out there '
                 'with the rest of you.',
         contexts=('city',), group='city', usage='buy <name> [--why]',
         detail=(
                'Takes one off the shelf. Programs and chrome go in the bag, '
                'drugs in the stash, and a component is fitted immediately '
                'with the old one going into the bag. `inspect <name>` first: '
                'it prints what a thing does, what it costs you, and whether '
                'you can drive it.'))
def cmd_buy(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if not len(args):
        raise CommandError('buy what? `market` lists it, with a row number '
                           'against each thing.')
    query = args.rest().lower()
    qualifies = game.char.dissonance >= drift.DEEP_CLINIC_BAND
    listings = game.city.listings(deep=None if qualifies else False)
    by_number = query.isdigit()
    if by_number:
        query = sess.pick('market', query,
                          fallback=[x.key for x in listings if _item(x)],
                          what='row', again='market')
    matches = []
    for listing in listings:
        item = _item(listing)
        if item and (query == listing.key if by_number
                     else (query in item.name.lower() or query == listing.key)):
            matches.append((listing, item))
            if by_number:
                break
    if not matches:
        raise CommandError(f'nothing here matches {query!r}')
    if len(matches) > 1:
        names = ', '.join(i.name for _, i in matches)
        raise CommandError(f'which one: {names}')
    listing, item = matches[0]

    price, terms = market_mod.quote(listing, game.city.where, game.alias,
                                    game.char.dissonance,
                                    game.char.mult('price_mult'),
                                    game.city.phase,
                                    game.char.attr('guile'))
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
    elif listing.kind == 'drug':
        game.char.stash[listing.key] = game.char.stash.get(listing.key, 0) + 1
        c.info(f'In the bag. `dose {listing.key}` when you want it, '
               f'`chem` for what it will do to you.')
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


@command('fit', 'Fit a component you own. The old one goes in the bag.',
         contexts=('city',), group='prep', usage='fit <component>',
         detail='D63 c. Buying a part fits it; this fits one you already '
                'have, which until now only Hotswap could do and only at '
                'Hardware 4, mid-run. A spare in the bag is a loadout '
                'decision, not a souvenir.',
         complete=lambda sess, prefix: [
             hardware.BY_KEY[k].name.lower() for k in sess.game.char.library
             if k in hardware.BY_KEY] if sess.game else [])
def cmd_fit(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if not len(args):
        spares = [hardware.BY_KEY[k] for k in game.char.library
                  if k in hardware.BY_KEY]
        if not spares:
            raise CommandError('nothing in the bag fits a deck. `market '
                               'component` where there is a workshop.')
        c.header('Spare parts', f'{len(spares)} in the bag')
        for comp in spares:
            c.raw(f'  [accent]{comp.name}[/]  [dim]{comp.slot}[/]')
        c.blank()
        c.say('[dim]`fit <name>`. `inspect <name>` for what one does.[/]')
        return
    query = args.rest().lower()
    key = next((k for k in game.char.library if k in hardware.BY_KEY
                and (query == k or query in hardware.BY_KEY[k].name.lower())),
               None)
    if key is None:
        raise CommandError(f'nothing in the bag is called {query!r}.')
    comp = hardware.BY_KEY[key]
    old = game.char.deck.parts.get(comp.slot)
    if old == key:
        raise CommandError(f'{comp.name} is already fitted.')
    game.char.deck.fit(key)
    game.char.library.remove(key)
    if old:
        game.char.library.append(old)
    c.ok(f'{comp.name} is in'
         + (f'. [dim]{hardware.BY_KEY[old].name} came out and went in the '
            f'bag.[/]' if old else '.'))
    deck = game.char.deck
    c.info(f'Memory {deck.memory_used}/{deck.memory}, heat {deck.heat}/'
           f'{deck.heat_cap}.')
    if deck.memory_used > deck.memory:
        c.warn('The deck is over memory now. `unload` something before you '
               'jack in.')


@command('sell', 'Sell something. Needs a fence or a market.',
         contexts=('city',), group='city', usage='sell <name>',
         detail=(
                'Sells a program, a piece of chrome or a spare component out '
                'of your bag, at a punishing rate. Gear is for using, not for '
                'arbitrage. What you carried out of a network is different: '
                'that sells automatically through whoever hired you.'))
def cmd_sell(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if not any(s in game.city.district.services for s in ('fence', 'market')):
        raise CommandError('nobody here is buying.')
    if not len(args):
        rows = []
        for key in game.char.library:
            item = (programs.BY_KEY.get(key) or cyberware.BY_KEY.get(key)
                    or hardware.BY_KEY.get(key))
            if item is None:
                continue
            kind = ('program' if key in programs.BY_KEY
                    else 'ware' if key in cyberware.BY_KEY else 'component')
            rows.append((item.name, kind,
                         f'[credit]{market_mod.sale_value(kind, key):,}c[/]'))
        if not rows:
            raise CommandError('nothing in the bag to sell. What is on the '
                               'deck and in you does not count.')
        c.header('For sale', 'what the bag would fetch')
        c.table(('item', 'kind', 'they pay'), rows,
                roles=('accent', 'dim', None))
        c.blank()
        c.say('[dim]`sell <name>`. The rate is punishing on purpose: gear '
              'is for using.[/]')
        return
    query = args.rest().lower()

    for key in list(game.char.library):
        item = (programs.BY_KEY.get(key) or cyberware.BY_KEY.get(key)
                or hardware.BY_KEY.get(key))
        if not item or query not in item.name.lower():
            continue
        kind = ('program' if key in programs.BY_KEY
                else 'ware' if key in cyberware.BY_KEY else 'component')
        value = market_mod.sale_value(kind, key)
        if kind == 'program' and game.char.library.count(key) <= \
                game.char.deck.loaded.count(key):
            # Sold off the deck, it stayed on the deck (D100).
            game.char.deck.unload(key)
        game.char.library.remove(key)
        game.char.credits += value
        c.ok(f'{item.name} sold for [credit]{value:,}c[/].')
        return
    if query == 'out':
        raise CommandError('to sell somebody out: `betray <runner>`. `who` '
                           'lists them and what they would fetch.')
    raise CommandError(f'you do not have anything called {query!r} in storage')


# --------------------------------------------------------------------------
# the board
# --------------------------------------------------------------------------


@command('board', 'Work currently on offer.',
         contexts=('city',), group='city', aliases=('jobs',), usage='board [id]',
         detail=(
                'Everything currently on offer, generated from the state of '
                'the city: who dislikes whom enough to pay for it, and what '
                'they think of you. `reads` is the column that matters: doors '
                'is whether your breaker opens what the job is behind, room '
                'is how hard the place runs the clock while you do it. '
                'Contracts expire, and other runners are taking these while '
                'you read.'))
def cmd_board(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    city = game.city

    if len(args):
        _show_contract(sess, _contract_arg(sess, args[0]))
        return

    if not city.board:
        c.info('The board is empty. Come back after a shift or two.')
        return
    c.header('The board', f'{city.when}')
    rows = []
    for n, contract in enumerate(city.board, 1):
        left = contract.expires - city.shift
        mark = '*' if contract.cid == city.accepted else ''
        # How it reads against what you carry, as one word, in the colour
        # of the answer (D68). The whole point of a board is choosing, and
        # choosing needs the difficulty where the pay is.
        word, role = reads_short(game.char, int(contract.posture))
        # Whether they can kill you, which posture does not say and which
        # is the one fact a player would want before the fee (D79).
        lethal = ('[err]!' if factions.runs_lethal(contract.target) else '')
        rows.append((f'{mark}{n}', contract.title,
                     contract.target_data.short + (lethal + '[/]' if lethal
                                                   else ''),
                     SHORT_OBJECTIVE.get(contract.objective,
                                         contract.objective),
                     contract_mod.SIZE_SHORT[contract.size_mod],
                     f'[{role}]{word}[/]',
                     f'{contract.pay:,}c',
                     'held' if contract.held
                     else (f'{left}sh' if left > 0 else 'late')))
    c.table(('#', 'job', 'against', 'what', 'size', 'reads', 'pay', 'left'),
            rows, roles=('accent', 'accent', 'err', 'dim',
                         'dim', None, 'credit', 'warn'))
    if any(factions.runs_lethal(x.target) for x in city.board):
        c.say('[dim]An [err]![/][dim] after a name means they run lethal '
              'countermeasures. Posture is how hard the doors are; that is '
              'whether the room can kill you, and the two are not the same '
              'number.[/]')
    # The row numbers mean this board, as printed. See `Session.pick`.
    sess.remember('board', [contract.cid for contract in city.board])
    c.blank()
    c.say('[dim]`board 1` reads the first one properly: who is paying, how '
          'their networks are built, and the walk. `take 1` accepts it.[/]')
    c.say('[dim][fg]reads[/] is doors and room. Doors is whether your '
          'breaker opens what the job is behind; room is how hard the place '
          'runs the clock while you do it. Most runs are lost to the '
          'second.[/]')


def _contract_arg(sess, token: str):
    """A contract from a row number or an id, or a readable refusal."""
    game = sess.game
    cid = sess.pick('board', token,
                    fallback=[x.cid for x in game.city.board],
                    what='contract', again='board')
    contract = game.city.contract(cid)
    if contract is None:
        if token.isdigit():
            raise CommandError(f'row {token} was {cid}, and it has gone from '
                               f'the board since you looked. `board` again.')
        if token in drug_content.BY_KEY:
            raise CommandError(f'{drug_content.BY_KEY[token].name} is a '
                               f'drug: `dose {token}` takes it.')
        raise CommandError(f'no contract {token!r} on the board')
    return contract


def way_in(game, contract) -> str:
    """How deep the job is, in badges, before the walk (D93).

    The mid-game tester's third idea: corporate work was a tier ladder the
    build could not climb in the ticks the room allowed, and nothing said
    so until the brief announced the zone at the door, three shifts after
    the job was taken. The network is deterministic from the contract, so
    the zone and the tier are readable now for nothing. Who guards the
    desk is legwork (`legwork intel`), and stays so.
    """
    from ..run import network as net_mod
    net = net_mod.generate(game.rng.fork('network', contract.cid),
                           contract.target, int(contract.posture),
                           contract.objective, contract.size_mod,
                           grudge=game.city.grudges.get(contract.target, ''))
    target = net.node(net.objective_node)
    if target is None:
        return ''
    walls = {uid for uid, node in net.nodes.items() if net_mod._is_wall(node)}
    route = (net_mod._route(net, net.objective_node, avoid=walls)
             or net_mod._route(net, net.objective_node))
    deepest = max((net.nodes[u].tier for u in route if u in net.nodes),
                  default=target.tier)
    desks = sum(1 for u in route if u in net.nodes
                and net.nodes[u].type == 'auth')
    hops = max(0, len(route) - 1)
    if deepest <= 0:
        depth = 'no badge needed'
    else:
        depth = (f'{deepest} badge{"s" if deepest != 1 else ""} deep'
                 + (f', and the desk{"s" if desks != 1 else ""} that '
                    f'issue{"" if desks != 1 else "s"} them '
                    f'{"are" if desks != 1 else "is"} on the way'
                    if desks else ', and no desk on the way: a forger, '
                                  'a lucky crack, or another route'))
    from ..run.session import NOISE_TO_TRACE, TRACE_MAX, TRACE_PER_TICK
    from ..content import ice as ice_content
    rate = (TRACE_PER_TICK + 2.0 * NOISE_TO_TRACE) * net.crowd
    rate *= shifts.phase(game.city.phase).trace
    clocks = []
    for alert in ('green', 'amber', 'red'):
        mult = ice_content.ALERT_TRACE_MULT.get(alert, 1.0)
        clocks.append(f'{int(TRACE_MAX / max(0.05, rate * mult))} at {alert}')
    return (f'their {target.zone}, about {hops} host{"s" if hops != 1 else ""} '
            f'in, {depth}. The clock has about {", ".join(clocks)}, in '
            f'working ticks, this shift')


def job_read(char, contract) -> str:
    """The objective verb's own odds, beside the doors (D101)."""
    kind = contract.objective
    if kind not in ('corrupt', 'implant', 'wipe'):
        return ''
    odds = contract_mod.objective_odds(char, kind, int(contract.posture))
    verb = {'corrupt': 'the edit', 'implant': 'the implant',
            'wipe': 'the wipe'}[kind]
    skill = contract_mod.objective_skill(kind)
    role = ('ok' if odds >= 0.7 else 'warn' if odds >= contract_mod.DOOR_TIGHT
            else 'err')
    return (f'[{role}]{verb} lands at {odds:.0%}[/] [dim]with what you '
            f'carry: {skill} and the payload are the numbers[/]')


def _show_contract(sess, contract) -> None:
    game, c = sess.game, sess.console
    from ..world.contracts import OBJECTIVE_BLURB, OBJECTIVE_PROGRAM
    c.header(contract.title, contract.cid)
    c.say(contract.blurb)
    if contract.from_npc:
        from ..content import npcs as npc_content
        who = npc_content.BY_KEY.get(contract.from_npc)
        if who is not None:
            c.blank()
            c.say(f'[accent2]{who.name} is holding this one for you.[/] '
                  f'[dim]Personal work. It pays better and somebody '
                  f'specific is waiting for it.[/]')
    c.blank()
    c.kv([
        ('patron', f'[info]{contract.patron_data.name}[/]'),
        ('target', f'[err]{contract.target_data.name}[/]'),
        ('objective', f'{contract.objective} [dim]'
                      f'{OBJECTIVE_BLURB[contract.objective]}[/]'),
        ('pay', f'[credit]{contract.pay:,}c[/]'),
        ('district', districts.BY_KEY[contract.district].name
         + (f' [dim]({game.city.shifts_to(contract.district)} shift'
            f'{"s" if game.city.shifts_to(contract.district) != 1 else ""} '
            f'from here)[/]'
            if contract.district != game.city.where
            else ' [dim](you are here)[/]')),
        ('expires', 'held for you, and it will keep' if contract.held
                    else f'in {contract.expires - game.city.shift} shifts'),
        ('size', f'{contract_mod.SIZE_WORDS[contract.size_mod][0]} [dim]'
                 f'{contract_mod.SIZE_WORDS[contract.size_mod][1]}[/]'),
        ('the way in', way_in(game, contract)),
        ('reads as', readiness(game.char, int(contract.posture))),
        *([('the job', job_read(game.char, contract))]
          if job_read(game.char, contract) else []),
        *([('their way', _net_signature(contract.target))]
          if _net_signature(contract.target) else []),
        ('posture', f'{int(contract.posture)} [dim]'
                    f'{contract.target_data.doctrine}[/]'
                    + (f' [accent2]({factions.style_line(contract.target_data)})[/]'
                       if contract.target_data.style else '')),
    ])
    if factions.runs_lethal(contract.target):
        c.blank()
        c.warn(f'{contract.target_data.short} run lethal countermeasures. '
               f'Black ICE tells you once, the tick before it acts, and '
               f'after that it is the only thing in this game that kills '
               f'you outright.')
    need = OBJECTIVE_PROGRAM.get(contract.objective)
    if need and not game.char.deck.has_category(need):
        c.blank()
        c.warn(f'You have no {need} loaded. This objective needs one.')
    held_ice = game.city.grudges.get(contract.target, '')
    if held_ice:
        from ..content import ice as ice_content
        it = ice_content.BY_KEY.get(held_ice)
        if it is not None:
            hunts = it.behaviour in ('hunter', 'black')
            c.blank()
            c.say(f'[ice]Last time in a {contract.target_data.short} network, '
                  f'a {it.name} {"put" if hunts else "filed"} you out. They '
                  f'still run it, and it will be awake'
                  + (': a weapon program and the Warfare to drive it, or a '
                     'route round it.' if hunts else
                     ': it files rather than hunts, so quiet past it, or a '
                     'route round it.') + '[/]')
    desk = badge_read(game.char)
    if (desk.impossible and not game.char.has_technique('pivot')
            and 'native' not in game.char.riders()):
        c.blank()
        c.warn('A badge desk would stop you. Some routes have a warden that '
               'takes credentials rather than a door that breaks, and you '
               'have nothing it would take:')
        c.say(f'[dim]{desk.explain()}[/]', indent='  ')
        c.say('[dim]A forger program and the Subterfuge to drive it, or '
              '`pivot` at Intrusion 4, is the difference. `map` inside '
              'shows whether there is another way round.[/]')
    if contract.intel:
        c.blank()
        c.rule('intel')
        for key, value in contract.intel.items():
            c.say(f'[ok]{key}:[/] {value}')
    # How to say yes, in the terms the board used. The row number is only
    # offered when this contract is on the board the player last read, so
    # the advice cannot name a row that means something else now.
    if contract.cid != game.city.accepted and not game.city.accepted:
        shown = sess.listed.get('board') or []
        by_row = (f'`take {shown.index(contract.cid) + 1}` or '
                  if contract.cid in shown else '')
        c.blank()
        c.say(f'[dim]{by_row}`take {contract.cid}` to accept it.[/]')


def city_job(sess) -> None:
    """What you have agreed to do, and the next thing standing between you.

    The city half of `job`. The run half is in `run.py` and reads the network;
    this one reads the calendar, the walk, and the deck, because out here the
    thing between you and the job is nearly always one of those three.
    """
    game, c = sess.require_game(), sess.console
    from ..world.contracts import OBJECTIVE_BLURB, OBJECTIVE_PROGRAM
    contract = game.city.current
    if contract is None:
        c.header('No job', 'nothing accepted')
        c.say('[dim]Nothing accepted. `board` for what is on offer, '
              '`board 1` to read the first one properly, then `take 1`. '
              'The id works in place of the number.[/]')
        return

    c.header(contract.title, contract.cid)
    c.say(f'[dim]{OBJECTIVE_BLURB[contract.objective]}[/]')
    c.blank()
    where = districts.BY_KEY[contract.district]
    hops = game.city.shifts_to(contract.district)
    left = contract.expires - game.city.shift
    c.kv([
        ('for', f'[info]{contract.patron_data.name}[/]'),
        ('against', f'[err]{contract.target_data.name}[/]'),
        ('pay', f'[credit]{contract.pay:,}c[/]'),
        ('where', f'{where.name} [dim]'
                  + ('you are here' if not hops
                     else f'{hops} shift{"s" if hops != 1 else ""} away')
                  + '[/]'),
        ('expires', 'held for you, and it will keep' if contract.held
                    else f'in {left} shift{"s" if left != 1 else ""}'
                    if left > 0 else
                    f'{-left} shift{"s" if left != -1 else ""} past its '
                    f'date: they pay {int(city_mod.LATE_SHARE * 100)}% for '
                    f'late' if left < 0 else 'today, and not after'),
    ])

    # The walk is priced in the same currency as the deadline, and a job you
    # cannot reach in time is worth knowing about before you spend two shifts
    # walking toward it. Standing on it, the walk is nothing and the late
    # fee is the only arithmetic (D97).
    if hops and hops >= left and not contract.held:
        c.blank()
        c.err(f'The walk is {hops} shift{"s" if hops != 1 else ""} and it '
              f'expires in {max(0, left)}. You will not make it in time: '
              f'`drop` it, or go anyway for {int(city_mod.LATE_SHARE * 100)}% '
              f'of the fee.')

    need = OBJECTIVE_PROGRAM.get(contract.objective)
    if need and not game.char.deck.has_category(need):
        c.blank()
        c.warn(f'No {need} loaded, and this objective cannot be finished '
               f'without one. The loadout is fixed the moment you jack in.')
        # Naming one you own, or saying plainly that you own none. Telling
        # somebody to `load <program>` when their library is empty of the
        # category is an instruction they cannot follow and cannot diagnose.
        owned = [programs.BY_KEY[k] for k in game.char.library
                 if k in programs.BY_KEY
                 and programs.BY_KEY[k].category == need]
        if not owned:
            cheapest = min(programs.by_category(need),
                           key=lambda p: (p.tier, p.price))
            c.say(f'[dim]You do not own one either. Every market carries a '
                  f'{cheapest.name} at around {cheapest.price:,}c, which is '
                  f'the cheap end of {need}: `market program`.[/]')
            if game.char.credits < cheapest.price:
                # The opening squeeze, said out loud. A broke runner is not
                # stuck, they are on the wrong contract: two of the six
                # objectives need nothing in the payload slot at all.
                c.say('[dim]That is more than you are carrying. Surveil and '
                      'escort work needs no payload, and a run with no '
                      'contract on it pays for whatever you can carry out. '
                      '`board` shows which is which.[/]')
    c.blank()
    c.say('[dim]Next:[/]')
    for step, _ in city_steps(game):
        c.raw(f'  [fg]{step}[/]')


#: What a posture reads as against a build, by the chance its middling
#: services give you. Said before you take the job, because posture is the
#: difficulty and a number between twenty and seventy-two tells a new
#: player nothing at all.
#: The difficulty of the sort of service a vault runs, which is what the
#: job is behind. See `nodes.SERVICES`: keystore 5-7, sign 5-8, cipher 4-7.
#: Above this posture the trace is what ends runs, and a mask is the
#: difference between a hard job and an impossible one: measured over
#: twenty four runs it roughly doubles what a top build finishes against
#: a corporation, three in twenty four to nine (D85).
MASK_POSTURE = 40

#: Heat at or above this is not waited out (D87): it cools about a point a
#: shift, so the advice to rest is advice to lose the week. Below it, a
#: few shifts is a real answer.
HEAT_WAITS_OUT = 40

#: The recommender's posture ceiling: this, plus this much per finished
#: run (D91). Six clean runs reach the corporate band.
POSTURE_FLOOR = 30
POSTURE_PER_CLEAN = 5
#: What ending an arrangement on your own terms costs in standing (D96):
#: the line always said they would not forget it.
ARRANGE_STOP_REP = 4
#: How many collections' worth the account holds before an arrangement is
#: advised (D100).
ARRANGE_CYCLES_AHEAD = 3

VAULT_SERVICE = contract_mod.VAULT_SERVICE

#: How many of those doors stand between the front of a network and the
#: thing you came for.
DOORS = 3

#: The objective, short enough for a column.
SHORT_OBJECTIVE = {'exfiltrate': 'exfil', 'surveil': 'watch',
                   'implant': 'implant', 'corrupt': 'corrupt',
                   'wipe': 'wipe', 'escort': 'escort'}

#: Two things kill runs and they are not the same thing (D68). The doors
#: are whether your breaker opens what the job is behind; the room is how
#: hard the place runs the clock while you do it. Measuring a hundred runs
#: made the difference plain: at corporate posture a mid build opens nearly
#: every door and still loses four runs in five, because the trace fills.
#: A line that priced only the doors told those players a bank was
#: comfortable.
DOOR_WORDS = ((0.70, 'ok', 'open'), (0.35, 'warn', 'tight'),
              (0.0, 'err', 'shut'))
ROOM_WORDS = ((60, 'err', 'hostile'), (42, 'warn', 'hard'),
              (28, 'warn', 'busy'), (0, 'ok', 'quiet'))


def _door_odds(char, posture: int) -> float:
    """The chance of one vault-grade door, with what is loaded. Lives
    with the contracts now (D91), so the board's rung can read it."""
    return contract_mod.door_odds(char, posture)


def reads_short(char, posture: int) -> tuple[str, str]:
    """The two-word judgement for a table: doors and room."""
    door = _door_odds(char, posture)
    for floor, drole, dword in DOOR_WORDS:
        if door >= floor:
            break
    for floor, rrole, rword in ROOM_WORDS:
        if posture >= floor:
            break
    worst = 'err' if 'err' in (drole, rrole) else (
        'warn' if 'warn' in (drole, rrole) else 'ok')
    return f'{dword}/{rword}', worst


def readiness(char, posture: int) -> str:
    """How this target reads against this build, in the two ways that
    decide a run: whether the doors open, and how hard the room is."""
    door = _door_odds(char, posture)
    for floor, drole, dword in DOOR_WORDS:
        if door >= floor:
            break
    for floor, rrole, rword in ROOM_WORDS:
        if posture >= floor:
            break
    breaker = programs.best(char.deck.loaded, 'breaker')
    tail = breaker.name if breaker else 'nothing loaded'
    if breaker is not None and breaker.key == 'lattice':
        # The price the board never mentioned (D97).
        tail += ', two ticks a door'
    doors = {'open': 'Their doors open for what you carry',
             'tight': 'Their doors are tight for what you carry',
             'shut': 'Their doors are shut to what you carry'}[dword]
    room = {'quiet': 'The room is quiet: little is watching it, and the '
                     'clock is yours to spend',
            'busy': 'The room is busy: enough is watching to make the clock '
                    'a real question',
            'hard': 'The room is hard: it will find you, and the trace runs '
                    'on their terms once it has',
            'hostile': 'The room is hostile: assume it finds you, and plan '
                       'the evening around that'}[rword]
    return (f'[{drole}]{doors}[/] [dim]({door:.0%} a door with {tail}, and '
            f'the job is behind about {DOORS})[/]\n[{rrole}]{room}[/]')


def _net_signature(faction: str) -> str:
    """What this lot's networks do that nobody else's do (D67), or ''."""
    from ..run import network as net_mod
    return net_mod.SIGNATURES.get(faction, '')


def _suggest_contract(game):
    """The job to take next: the lowest posture whose program you carry or
    own, ties to the better pay. None when the board is empty."""
    from ..world.contracts import OBJECTIVE_PROGRAM
    board = [c for c in game.city.board if not c.expired(game.city.shift)]
    if not board:
        return None
    have = {programs.BY_KEY[k].category for k in
            list(game.char.library) + list(game.char.deck.loaded)
            if k in programs.BY_KEY}

    from ..world.contracts import objective_possible

    def equipped(c) -> bool:
        need = OBJECTIVE_PROGRAM.get(c.objective)
        return not need or need in have

    def possible(c) -> bool:
        # Not "do you own the program" but "could the die carry it": the
        # verb at the end of the walk is a check like any other and the
        # advice reads it before it sends anybody (D71).
        return objective_possible(game.char, c.objective, int(c.posture))

    # Posture is the difficulty, and gear you do not have yet is a shop
    # trip rather than a wall: a soft job that wants a nine-hundred-credit
    # payload beats a hard one that wants nothing.
    #
    # Size is the second axis and it used to be read the wrong way round:
    # ties went to the better fee, the better fee is the bigger job, and
    # depth scales with the fee, so the advice reliably pointed a fresh
    # build at the deepest thing on the softest network. Somebody who is
    # asking what to do next is asking for a job they can finish. Once
    # there are a few runs behind them the fee is the right tiebreak
    # again, because by then the answer to a big network is gear.
    # Both gaps are priced rather than sorted on, and in the same currency
    # as the difficulty they are weighed against: gear you have not bought
    # is a shop trip, a verb the die cannot carry is a wasted night, and
    # neither is worth walking into a corporate network to avoid.
    # Tenure is not capability. Five contracts in, a runner who has spent
    # nothing is exactly as able as they were on night one, and the advice
    # used to start recommending the biggest job on the softest network to
    # them the moment the counter ticked over. Ranks bought is the honest
    # measure: about double what an origin ships with is the point where
    # size stops being the thing most likely to end the night (D82).
    # And finished runs, not only ranks bought (D87): a player who has
    # trained past the threshold on the strength of three clean nights
    # and five severed ones is not ready for a sprawl.
    green = (sum(game.char.base_skills.values()) < 12
             or _clean_runs(game) < 4)

    def history_cost(c) -> float:
        # A contract that has already cut you loose is not the softest
        # thing on the board, whatever its posture says. Twice and it is
        # off the list: the advice recommended the same severed run five
        # nights running, and the drop it suggested in between was undone
        # by the next `now` (D87).
        if _dead_to_you(game, c.cid):
            return float('inf')
        return 12.0 * len(_attempts(game, c.cid))

    def calendar_cost(c) -> float:
        # A job that expires before the walk gets there.
        hops = game.city.shifts_to(c.district)
        left = c.expires - game.city.shift
        if not c.held and hops >= left:
            return float('inf')
        return 0.0

    def street_cost(c) -> float:
        # A walk through somebody who is paying to find you: a lean when
        # it is heat, a wall when it is a bounty (D100).
        hunted, _ = _hunted_on_route(game, c.district)
        if not hunted:
            return 0.0
        who = next((k for k in factions.FACTION_KEYS
                    if factions.BY_KEY[k].short == hunted), '')
        if who and int(game.city.bounties.get(who, 0)) > 0:
            return float('inf')
        return 25.0

    # A badge desk on the route is not certain, so this is a lean and not
    # a wall: the wall is in the run, and the board says so (D88).
    desk = (8.0 if badge_read(game.char).impossible
            and not game.char.has_technique('pivot')
            and 'native' not in game.char.riders() else 0.0)

    # Variety (D90). The softest job on a gang board is a watch, always,
    # so a first-timer was sent on three surveils running while the
    # Siphon they were told to buy sat unused. Two of a kind in a row is
    # a lean against a third, and the job the payload you own was built
    # for is a lean toward it.
    recent = [h.get('objective') for h in game.history[-2:]]
    built_for = set()
    for key in list(game.char.library) + list(game.char.deck.loaded):
        p = programs.BY_KEY.get(key)
        if p is not None and p.category == 'payload':
            built_for.update(p.jobs)

    def variety_cost(c) -> float:
        out = 0.0
        if len(recent) == 2 and recent[0] == recent[1] == c.objective:
            out += 4.0
        if c.objective in built_for and equipped(c):
            out -= 3.0
        return out

    # A ceiling that rises with finished runs (D91). "The softest thing
    # on the board you have the gear for" was said about Sendai at
    # fifty-eight to a five-run academic, because everything softer had
    # been excluded and softest is a comparison, not a judgement.
    ceiling = ceiling_for(game)

    def door_cost(c) -> float:
        # A shut read is not "the gear for" (D100): the ceiling had risen
        # five a clean night past the door read, and a lethal corporate
        # job at thirty per cent a door was called the softest thing.
        odds = _door_odds(game.char, int(c.posture))
        if odds < contract_mod.DOOR_TIGHT:
            return float('inf')
        if int(c.posture) > ceiling:
            return float('inf')
        return 0.0

    def verb_cost(c) -> float:
        # The job itself, priced like a door (D101): tight is a lean,
        # shut is a wall.
        odds = contract_mod.objective_odds(game.char, c.objective,
                                           int(c.posture))
        if odds < contract_mod.DOOR_TIGHT:
            return float('inf') if odds <= 0.1 else 15.0
        return 0.0

    def cost(c):
        return (int(c.posture)
                + (0 if equipped(c) else 12)
                + (0 if possible(c) else 20)
                + verb_cost(c)
                + history_cost(c) + calendar_cost(c) + street_cost(c) + desk
                + variety_cost(c) + door_cost(c),
                c.size_mod if green else 0.0,
                -c.pay)

    pick = min(board, key=cost)
    if cost(pick)[0] == float('inf'):
        return None
    return pick


def _warned_line(game) -> str:
    """Who has told you, in so many words, that next time they will not
    be asking (D65). On the sheet beside Integrity, because it is the one
    number on the sheet that the warning is about."""
    warned = sorted(f[7:] for f in game.story.flags if f.startswith('warned:'))
    if not warned:
        return ''
    names = [factions.BY_KEY[w].short if w in factions.BY_KEY else 'somebody'
             for w in warned]
    return (f'  [err]warned by {", ".join(names)}: next time they will not '
            f'be asking[/]')


def _hunted_on_route(game, target: str) -> tuple[str, str]:
    """Who is hunting you on the way to `target`, and where.

    `walk` is one command and several streets and it stops at the first
    hop where somebody is paying to find you, so the whole route has to be
    read, not the first step of it. Returns ('', '') when the road is
    clear.
    """
    from ..world import fallout
    riders = game.char.riders()
    for hop in game.city.route(target):
        danger, who = game.city.danger(game.alias, hop,
                                       flags=game.story.flags, riders=riders)
        if 'streetwise' in riders:
            danger = int(danger * 0.6)
        if 'findable' in riders:
            danger = int(danger * 1.3)
        if (danger >= fallout.INCIDENT_FLOOR and who
                and who not in game.city.arrangements):
            fac = factions.BY_KEY.get(who)
            return ((fac.short if fac else 'somebody'),
                    districts.BY_KEY[hop].name)
    return '', ''


def nearest_workshop(game) -> str:
    """The district key of the closest workshop, or ''."""
    shops = [d for d in districts.DISTRICTS if 'workshop' in d.services]
    if not shops:
        return ''
    return min(shops, key=lambda d: game.city.shifts_to(d.key)).key


def badge_read(char):
    """What this build could show a badge desk, as the run's own check,
    against the softest warden the generator ever puts in front of the
    desk (D88). The board's reads column priced doors and the room and
    never the third thing that ends runs: a warden that takes credentials
    from a build that has none to give. A Chromed origin ships with ten
    points against it and a Steward on the first route was a wall the
    advice called the softest job on the board."""
    from ..run.checks import Check
    from ..run.network import SOFT_DOORMAN
    check = Check(name='credentials', resistance=SOFT_DOORMAN * 2 + 2)
    check.add('subterfuge', char.skill('subterfuge') * 2)
    check.add('guile', char.attr('guile'))
    check.add('gear', char.bonus('pretext_bonus'))
    forger = programs.best(list(char.deck.loaded) + list(char.library),
                           'forger')
    if forger:
        rank = char.skill('subterfuge')
        check.add(programs.held_label(forger, rank, 'subterfuge'),
                  programs.held(forger, rank) * 2)
    if 'no_social' in char.riders():
        check.add('a process cannot present a badge', -10)
    return check


def _shelf_price(game, key: str) -> int | None:
    """What a program on the local shelf would actually cost this
    character, or None if it is not stocked here. The advice used to quote
    the catalogue price times the district: `buy siphon ... about 900c`
    against a shop that then asked 563c, because standing, the hour and
    the asking all move the number and the shop reads every one (D87)."""
    listing = next((l for l in game.city.listings('program') if l.key == key),
                   None)
    if listing is None:
        return None
    price, _ = market_mod.quote(listing, game.city.where, game.alias,
                                game.char.dissonance,
                                game.char.mult('price_mult'),
                                game.city.phase, game.char.attr('guile'))
    return price


def _attempts(game, cid: str) -> list[dict]:
    """Every run against one contract that did not finish it."""
    return [h for h in game.history
            if h.get('cid') == cid and not h.get('done')]


def _clean_runs(game) -> int:
    return sum(1 for h in game.history if h.get('done'))


def ceiling_for(game) -> int:
    """The recommender's posture ceiling for this record (D91)."""
    return POSTURE_FLOOR + POSTURE_PER_CLEAN * _clean_runs(game)


def _dead_cids(game) -> set:
    """Every contract on the board the history says is not this
    character's, for the board's rung to skip."""
    return {c.cid for c in game.city.board if _dead_to_you(game, c.cid)}


def _dead_to_you(game, cid: str) -> bool:
    """Whether the history says this contract is not tonight's, in one
    place, read by the drop advice and the recommender alike (D91). The
    two used to disagree: one burn on the chair was enough for `drop` and
    not enough to stop the recommender naming the same job, so a follower
    dropped and re-took it for ever."""
    tries = _attempts(game, cid)
    severed = sum(1 for h in tries if h.get('outcome') == 'severed')
    return (severed >= 2 or len(tries) >= 3
            or any(h.get('chair') for h in tries))


#: The order in which program categories earn their memory, once the job's
#: own need and the breaker are in. Read by `_loadout_plan`.
LOADOUT_ORDER = ('breaker', 'payload', 'mask', 'forger', 'hunter', 'armour',
                 'weapon', 'wiper', 'daemon')


def _loadout_plan(game) -> list:
    """The programs this deck should be carrying, best first, that fit.

    Three separate pieces of advice used to each ask for the last two
    memory on a four-memory deck: the breaker step said load Sable, the
    payload step then said unload Sable to fit Siphon, and the mask step
    said unload Siphon to fit Quietcastle, for ever (D87). One plan, so
    every fit step is a move toward the same deck: the breaker, then what
    the job in hand needs, then a payload, then a mask, then the rest in
    the order they matter, each the best owned of its kind at the rank
    that drives it, and each only if there is room left after the ones
    before it.
    """
    from ..world.contracts import OBJECTIVE_PROGRAM
    char = game.char
    deck = char.deck
    owned = [programs.BY_KEY[k] for k in list(char.library) + list(deck.loaded)
             if k in programs.BY_KEY]
    contract = game.city.current

    def strength(p) -> tuple:
        rank = char.skill('intrusion') if p.category == 'breaker' else 99
        return (programs.held(p, rank), -p.memory, p.rating)

    def best_of(category):
        have = [p for p in owned if p.category == category]
        return max(have, key=strength) if have else None

    order = ['breaker']
    if contract is not None:
        need = OBJECTIVE_PROGRAM.get(contract.objective, '')
        if need and need not in order:
            order.append(need)
    # A build that strikes carries what it strikes with (D91): the plan
    # told a Warfare build to unload the Cudgel that later killed the
    # construct with its name on it.
    if char.has_technique('strike') and 'weapon' not in order:
        order.append('weapon')
    for cat in LOADOUT_ORDER:
        if cat not in order:
            order.append(cat)
    # A mask earns its slot on hard work. Below that posture it is memory
    # a payload or a forger would use better, and on a fresh deck it is
    # the whole of the bank. The work is the job in hand, or failing that
    # the softest thing on the board, which is what the advice will send
    # you at next.
    if contract is not None:
        posture = int(contract.posture)
    else:
        board = [c for c in game.city.board
                 if not c.expired(game.city.shift)]
        posture = min((int(c.posture) for c in board), default=0)
    if posture < MASK_POSTURE and 'mask' in order:
        order.remove('mask')
        order.append('mask')
    plan, room = [], deck.memory
    # Room for the payload the advice is about to say buy: two steps were
    # undone across a purchase because the plan filled the bank first and
    # then had to empty it (D91).
    if best_of('payload') is None:
        cheapest = min((p for p in programs.by_category('payload')
                        if not p.unique), key=lambda p: p.price, default=None)
        if cheapest is not None and char.credits >= cheapest.price:
            room -= cheapest.memory
    for cat in order:
        p = best_of(cat)
        if p is not None and p.memory <= room:
            plan.append(p)
            room -= p.memory
    return plan


LOADOUT_WHY = {
    'breaker': 'every door in the game reads its rating',
    'payload': 'four of the six objectives need one',
    'mask': 'it is what makes hard work possible',
    'forger': 'it is what opens a badge desk',
}


def _loadout_step(game):
    """One move toward the deck `_loadout_plan` describes, or None."""
    deck = game.char.deck
    plan = _loadout_plan(game)
    keys = {p.key for p in plan}
    missing = [p for p in plan if p.key not in deck.loaded]
    if not missing:
        return None
    want = missing[0]
    why = LOADOUT_WHY.get(want.category,
                          'it is the best of what you own for the slot')
    if deck.memory_free >= want.memory:
        return (f'load {want.name.lower()}',
                f'{want.name} is in the bag and the deck has room: {why}')
    loaded = [programs.BY_KEY[k] for k in deck.loaded if k in programs.BY_KEY]
    spare = [p for p in loaded if p.key not in keys]
    if spare:
        drop = max(spare, key=lambda p: (p.memory, -p.rating))
        return (f'unload {drop.name.lower()}',
                f'{want.name} needs {want.memory} memory with '
                f'{deck.memory_free} free, and {drop.name} is not part of '
                f'the deck you should be carrying: {why}')
    return ('deck', f'{want.name} needs {want.memory} memory and the deck '
                    f'has {deck.memory_free}. A bigger bank, or carry less')


def _fit_step(game, category: str, why: str):
    """Advice for a program that is owned and not on the deck.

    Buying is one step and carrying is another, and the advice used to
    only ever know the first. Told to buy a payload, you bought it and
    were left holding it; told to buy a better breaker, you bought it,
    could not fit it, and were told to buy the next one up (D83). One
    helper, used by both, so the recommendation always carries through to
    the thing being usable.
    """
    deck = game.char.deck
    owned = [programs.BY_KEY[k] for k in game.char.library
             if k in programs.BY_KEY
             and programs.BY_KEY[k].category == category]
    loaded = [programs.BY_KEY[k] for k in deck.loaded
              if k in programs.BY_KEY
              and programs.BY_KEY[k].category == category]
    if not owned:
        return None
    best_owned = max(owned, key=lambda p: p.rating)
    best_loaded = max(loaded, key=lambda p: p.rating, default=None)
    if best_loaded is not None and best_loaded.rating >= best_owned.rating:
        return None
    if deck.memory_free >= best_owned.memory:
        return (f'load {best_owned.name.lower()}',
                f'{best_owned.name} is in the bag and the deck has room: '
                f'{why}')
    spare = best_owned.memory - deck.memory_free
    drop = next((p for p in sorted(
        (programs.BY_KEY[k] for k in deck.loaded if k in programs.BY_KEY),
        key=lambda p: (p.category == category and p.rating >= best_owned.rating,
                       p.rating, -p.memory))
        if p.memory >= spare), None)
    if drop is None:
        return ('deck', f'{best_owned.name} needs {best_owned.memory} memory '
                        f'and the deck has {deck.memory_free}. A bigger bank, '
                        f'or carry less')
    return (f'unload {drop.name.lower()}',
            f'{best_owned.name} is in the bag and needs {best_owned.memory} '
            f'memory with {deck.memory_free} free: {drop.name} is the least '
            f'of what is on the deck')


def city_steps(game) -> list[tuple[str, str]]:
    """What stands between you and the job, as (command, why), in order.

    The computed half of the city `job`, kept separate so that `now` can
    print the first of them without the rest of the brief. The same list
    feeds both, so the one-line answer and the full one cannot disagree.
    """
    from ..world.contracts import OBJECTIVE_PROGRAM
    contract = game.city.current
    steps: list[tuple[str, str]] = []
    # An unspent budget is a step before anything else. `now` said so while
    # the board was empty and then stopped the moment a job was taken,
    # which is the moment it matters: a fresh runner who never spent their
    # twelve experience fails every check in the network they just walked
    # to, and nothing tells them why.
    if game.char.points or game.char.xp >= 4:
        from .guide import softest_posture, suggest
        if suggest(game.char, softest_posture(game)):
            steps.append(('spend',
                          f'{game.char.points} attribute point'
                          f'{"s" if game.char.points != 1 else ""} and '
                          f'{game.char.xp} experience unspent: every check in '
                          f'there reads them'))
        elif game.char.xp >= 2:
            steps.append(('train',
                          f'{game.char.xp} experience unspent, and nothing '
                          f'the origin\'s shape suggests: `train` lists what '
                          f'a rank costs'))
    # The rank that holds the breaker (D87). A protege ships with a
    # rating-three Sable and Intrusion 0, so every door for eight runs
    # printed "held to 2 by Intrusion 0", and the advice named five other
    # skills before it named that one. Every door reads this number.
    char = game.char
    breaker = programs.best(char.deck.loaded, 'breaker')
    if breaker is not None:
        rank = char.skill('intrusion')
        running = programs.held(breaker, rank)
        cost = skill_content.RANK_COST.get(rank + 1)
        if (running < breaker.rating and cost is not None
                and char.xp >= cost
                and not any(cmd == 'spend' for cmd, _ in steps)):
            steps.append(('train intrusion',
                          f'{breaker.name} is rating {breaker.rating} and '
                          f'runs at {running} because Intrusion is {rank}: '
                          f'every door reads that number. Rank {rank + 1} '
                          f'costs {cost} experience and you have {char.xp}'))
        elif (cost is not None and char.xp >= cost
              and not any(cmd == 'spend' for cmd, _ in steps)
              and game.city.board
              and _door_odds(char, min(int(c.posture)
                                       for c in game.city.board)) < 0.35):
            # Every row reads shut and the nudge pointed at Signal (D91).
            steps.append(('train intrusion',
                          f'every row on the board reads tight or shut for '
                          f'what you carry, and Intrusion is the number '
                          f'every door reads. Rank {rank + 1} costs {cost} '
                          f'experience and you have {char.xp}'))
    # A severed connection keeps you out of the chair (D6, D88).
    if game.city.grounded > game.city.shift:
        left = game.city.grounded - game.city.shift
        steps.append((f'rest {left}',
                      f'you came back badly: {left} shift'
                      f'{"s" if left != 1 else ""} before your hands stop '
                      f'shaking enough to jack in'))
    # A collection due within a shift that the account cannot meet (D100):
    # they price the room instead, and nothing said it was coming.
    debt = game.debt
    if debt.owed and game.city.shift - debt.opened >= debt.terms[1]:
        since = game.city.shift - (debt.last_collected if debt.last_collected >= 0
                                   else debt.opened + debt.terms[1])
        take = debt.assess()
        if since >= debt_mod.COLLECT_EVERY - 1 and char.credits < take:
            offers = street_world.errands_here(game)
            if offers and not game.city.errand:
                best = max(range(len(offers)), key=lambda i: offers[i]['pay'])
                steps.append((f'errands take {best + 1}',
                              f'{fac_short(debt.lender)} collect {take:,}c '
                              f'within a shift and you have '
                              f'{char.credits:,}c: short, they price the '
                              f'room. This one pays {offers[best]["pay"]:,}c'))
            else:
                steps.append(('debt',
                              f'{fac_short(debt.lender)} collect {take:,}c '
                              f'within a shift and you have '
                              f'{char.credits:,}c: short, they price the '
                              f'room'))
    # Hurt is a step before any job (D65): the street hits harder when you
    # are, and a run starts with what you carry in.
    if char.integrity <= max(4, char.integrity_max // 3):
        steps.append(('rest', f'you are hurt ({char.integrity}/'
                              f'{char.integrity_max}); the street and the net '
                              f'both hit harder when you are'))
    # A package in the bag is a step wherever the job is (D65).
    errand = game.city.errand
    # Anything being carried somewhere: a package or a person (D100). The
    # escort kind fell through this branch and the fallback below said
    # `rest 1` for ever with somebody waiting to be walked to the Row.
    if errand and errand.get('to'):
        to = errand.get('to', '')
        if to in districts.BY_KEY and to != game.city.where:
            # The same refusal the contract walk checks for, on the same
            # terms. `walk` stops at the first hop where somebody is paying
            # to find you, and this branch named the walk anyway: the
            # advice said `walk hall`, the street said no, and it said it
            # every time you asked (D75).
            hunted, hop_name = _hunted_on_route(game, to)
            if hunted:
                # The same ways out as the contract walk (D100): `rest 3`
                # at heat a hundred was a loop with a friendly voice, and
                # the fallback then named the same walk `walk` refuses.
                who = next((k for k in factions.FACTION_KEYS
                            if factions.BY_KEY[k].short == hunted), '')
                hot = int(game.alias.attention(who)) if who else 0
                cost = (ALIAS_COST // 2 if 'no_history' in game.char.riders()
                        else ALIAS_COST)
                route = game.city.walk_to(to)
                if hot >= HEAT_WAITS_OUT or int(game.city.bounties.get(who, 0)):
                    steps.append((f'{route} --anyway',
                                  f'{hunted} are hunting you in {hop_name} '
                                  f'and the delivery goes through it. Heat '
                                  f'is {hot}, which does not cool this '
                                  f'week: walk into them and the street '
                                  f'prices it, or `burn` the name for '
                                  f'{cost:,}c'))
                else:
                    steps.append((f'rest {max(1, hot - HEAT_WAITS_OUT + 8)}',
                                  f'{hunted} are hunting you in {hop_name} '
                                  f'and the delivery goes through it. Heat '
                                  f'is {hot} and cools about a point a '
                                  f'shift; `{route} --anyway` walks into '
                                  f'them'))
            else:
                steps.append((game.city.walk_to(to),
                              f'deliver {errand.get("what", "the package")} '
                              f'to {districts.BY_KEY[to].name} for '
                              f'{int(errand.get("pay", 0)):,}c'))
    # A payload is the difference between two objectives and six. Four of
    # the six need one; the two that do not are the two hardest to finish;
    # and a runner without one is steered round every job that wants one,
    # for ever. The loop that comes out of that is: no payload, so watch
    # work, so no money, so no payload. Measured over six careers, income
    # after the third contract was nought (D82). So it is a standing step
    # the moment it is affordable, rather than advice that waits for a
    # contract to demand it.
    owned = {programs.BY_KEY[k].category for k in
             list(game.char.library) + list(game.char.deck.loaded)
             if k in programs.BY_KEY}
    loaded_cats = {programs.BY_KEY[k].category
                   for k in game.char.deck.loaded if k in programs.BY_KEY}
    # The breaker is the biggest single term in every door in the game and
    # nothing ever said so: seventeen contracts and five thousand credits
    # into a playthrough the deck was still the two rating-two Crowbars it
    # started with, because the advice only spoke about programs a
    # contract demanded and no contract demands a *better* one (D83).
    fit = _loadout_step(game)
    if fit is not None:
        steps.append(fit)
    breaker_fit = fit
    if breaker_fit is None:
        on_deck = max((programs.BY_KEY[k] for k in game.char.deck.loaded
                       if k in programs.BY_KEY
                       and programs.BY_KEY[k].category == 'breaker'),
                      key=lambda p: p.rating, default=None)
        here_now = game.city.district
        if on_deck is not None and 'market' in here_now.services:
            # Only what is actually on the shelf here. Affordability and a
            # market in the district are not the same as stock, and the
            # advice looped on `buy drillbit` against a shop that said
            # "nothing here matches 'drillbit'" (D83).
            for_sale = {l.key for l in game.city.listings('program')}
            rank = game.char.skill('intrusion')
            better = min((p for p in programs.by_category('breaker')
                          if not p.unique
                          and programs.held(p, rank) > programs.held(on_deck,
                                                                     rank)
                          and p.key in for_sale
                          and p.memory <= game.char.deck.memory
                          and game.char.credits >= (_shelf_price(game, p.key)
                                                    or 10 ** 9)),
                         key=lambda p: p.price, default=None)
            if better is not None:
                steps.append((f'buy {better.name.lower()}',
                              f'every door you fail is your breaker: '
                              f'{on_deck.name} is rating {on_deck.rating} and '
                              f'{better.name} is {better.rating}, here for '
                              f'{_shelf_price(game, better.key):,}c'))
    # A payload built for the job (D100): an improvised Siphon rooting an
    # implant under an amber room cost the whole clock and the deck.
    if contract is not None and 'market' in game.city.district.services:
        loaded_payload = programs.best(game.char.deck.loaded, 'payload')
        if (loaded_payload is not None and loaded_payload.jobs
                and contract.objective not in loaded_payload.jobs):
            for_sale = {l.key for l in game.city.listings('program')}
            built = min((p for p in programs.by_category('payload')
                         if not p.unique and contract.objective in p.jobs
                         and p.key in for_sale
                         and game.char.credits >= (_shelf_price(game, p.key)
                                                   or 10 ** 9)),
                        key=lambda p: p.price, default=None)
            if built is not None:
                steps.append((f'buy {built.name.lower()}',
                              f'{loaded_payload.name} is not built for '
                              f'{"an" if contract.objective[0] in "aeiou" else "a"} '
                              f'{contract.objective}: it does it badly and '
                              f'loudly. {built.name} is, and it is '
                              f'{_shelf_price(game, built.key):,}c here'))
    # A mask is what makes hard work possible and nothing said so: the
    # same failure as the payload and the breaker, one tier up (D85).
    owned_mask = any(p.category == 'mask' for p in
                     (programs.BY_KEY[k] for k in
                      list(game.char.library) + list(game.char.deck.loaded)
                      if k in programs.BY_KEY))
    if (not owned_mask and contract is not None
            and int(contract.posture) >= MASK_POSTURE):
        held_mask = any(programs.BY_KEY[k].category == 'mask'
                        for k in game.char.deck.loaded
                        if k in programs.BY_KEY)
        if not held_mask:
            here_m = game.city.district
            for_sale = {l.key for l in game.city.listings('program')}
            pick = min((p for p in programs.by_category('mask')
                        if not p.unique and p.key in for_sale
                        and p.memory <= game.char.deck.memory
                        and game.char.credits >= (_shelf_price(game, p.key)
                                                  or 10 ** 9)),
                       key=lambda p: p.price, default=None)
            if pick is not None:
                steps.append((f'buy {pick.name.lower()}',
                              f'{contract.target_data.short} run at posture '
                              f'{int(contract.posture)} and you carry no '
                              f'mask. The trace is what ends runs up here; '
                              f'{pick.name} is '
                              f'{_shelf_price(game, pick.key):,}c here'))
            else:
                # Not here: the named shelf (D98) says where.
                shelf = market_mod.shelf_for(game.city.stock, 'mask', tier=1)
                shelf = [(k, p) for k, p in shelf if k != game.city.where]
                if shelf:
                    key, p = shelf[0]
                    steps.append((game.city.walk_to(key),
                                  f'{contract.target_data.short} run at '
                                  f'posture {int(contract.posture)} and you '
                                  f'carry no mask. {p.name} is on a shelf in '
                                  f'{districts.BY_KEY[key].name} this cycle'))
    # A deck nobody repairs is not the deck you built: armour and masks
    # degrade as they work, and nothing tells you except the runs getting
    # worse.
    deck = game.char.deck
    wrecked = ([s for s, level in deck.damage.items() if level >= 2]
               or deck.memory_used > deck.memory)
    if deck.damage and 'workshop' in game.city.district.services:
        # `repair` alone prints an estimate and waits (D95): the step is
        # the one that does it, with the price. Only when the price can be
        # paid (D100): advised at nought credits, it was refused for free
        # forty times running.
        bill = deck.repair_cost(game.char.mult('repair_mult'))
        if game.char.credits >= bill:
            steps.append(('repair --confirm',
                          f'the deck is carrying damage, which degrades what '
                          f'it does rather than stopping it. {bill:,}c here'))
        else:
            short = bill - game.char.credits
            offers = street_world.errands_here(game)
            if offers and not game.city.errand:
                best = max(range(len(offers)), key=lambda i: offers[i]['pay'])
                steps.append((f'errands take {best + 1}',
                              f'the deck needs {bill:,}c of work and you are '
                              f'{short:,}c short: street work pays '
                              f'({offers[best]["pay"]:,}c for this one)'))
            else:
                steps.append(('sell',
                              f'the deck needs {bill:,}c of work and you are '
                              f'{short:,}c short: the bag, or `borrow`'))
    elif wrecked:
        # Serious damage with no workshop here: the walk, named. The
        # nudge only ever fired where a workshop was, so a deck with a
        # destroyed CPU two shifts from one jacked in silently at nothing
        # (D88).
        shop = nearest_workshop(game)
        if shop:
            steps.append((game.city.walk_to(shop),
                          f'the deck is badly hurt ('
                          + ', '.join(f'{s} {deck.damage[s]}/3'
                                      for s in deck.damage if deck.damage[s])
                          + (f', memory {deck.memory_used}/{deck.memory}'
                             if deck.memory_used > deck.memory else '')
                          + f') and the nearest workshop is in '
                          f'{districts.BY_KEY[shop].name}'))
    if 'payload' not in owned:
        cheapest = min((p for p in programs.by_category('payload')
                        if not p.unique), key=lambda p: p.price, default=None)
        if cheapest is not None:
            here = game.city.district
            shops = [d for d in districts.DISTRICTS if 'market' in d.services]
            shop = here if 'market' in here.services else (
                min(shops, key=lambda d: game.city.shifts_to(d.key))
                if shops else here)
            price = int(round(cheapest.price * shop.price_mult))
            if game.char.credits >= price:
                why = (f'you own no payload, and four of the six objectives '
                       f'need one. The two that do not are the hardest work '
                       f'on the board')
                on_shelf = {l.key for l in game.city.listings('program')}
                if shop.key == game.city.where and cheapest.key in on_shelf:
                    real = _shelf_price(game, cheapest.key) or price
                    steps.append((f'buy {cheapest.name.lower()}',
                                  f'{why}. {cheapest.name} is {real:,}c '
                                  f'here'))
                elif shop.key == game.city.where:
                    # A market here, and not this on the shelf. Naming the
                    # buy anyway is advice the shop refuses (D83).
                    steps.append(('market program',
                                  f'{why}. Something here will do it'))
                else:
                    steps.append((game.city.walk_to(shop.key),
                                  f'{why}. {cheapest.name} is about '
                                  f'{price:,}c at the {shop.name} market'))
    if contract is None:
        # Which job, not just "the board" (D64 c). A new runner takes the
        # first row, which is as likely as not a corporate network they
        # cannot open, and the run ends in a jack out with nothing. The
        # recommendation is the softest thing they have the gear for, and
        # it says the posture out loud, because posture is the difficulty
        # and nothing on the board says so in those words.
        pick = _suggest_contract(game)
        if pick is not None:
            shown = ', '.join(f'{p.title}' for p in [pick])
            words = contract_mod.SIZE_WORDS[pick.size_mod][0]
            steps.append((f'take {pick.cid}',
                          f'{shown}: {pick.target_data.short} at posture '
                          f'{int(pick.posture)}, {words}, '
                          f'{pick.pay:,}c. The softest thing on the board '
                          f'you have the gear for'))
            return steps
        if any(not c.expired(game.city.shift) for c in game.city.board):
            # Everything on it has cut you loose, expires before you could
            # get there, or walks through somebody hunting you. Saying
            # `board` here sends a player back to the row that just
            # severed them; the street pays, and the board turns over.
            # Named, not listed (D91): `errands` alone costs no shift and
            # a follower typed it seven times at the same board.
            causes = []
            live = [c for c in game.city.board if not c.expired(game.city.shift)]
            if any(_dead_to_you(game, c.cid) for c in live):
                causes.append('has already cut you loose')
            if any(_door_odds(game.char, int(c.posture)) < contract_mod.DOOR_TIGHT
                   for c in live):
                causes.append('reads shut for what you carry')
            if any(int(c.posture) > ceiling_for(game) for c in live):
                causes.append('is above what your record says you are ready '
                              'for')
            if any(_hunted_on_route(game, c.district)[0] for c in live):
                causes.append('goes through people who are looking for you')
            if any(not c.held and game.city.shifts_to(c.district)
                   >= c.expires - game.city.shift for c in live):
                causes.append('expires before the walk')
            softest = min(live, key=lambda c: int(c.posture)) if live else None
            one = ''
            if softest is not None:
                if _dead_to_you(game, softest.cid):
                    one = 'has already cut you loose'
                elif _door_odds(game.char, int(softest.posture)) < contract_mod.DOOR_TIGHT:
                    one = 'reads shut for what you carry'
                elif _hunted_on_route(game, softest.district)[0]:
                    one = 'goes through people who are looking for you'
                elif int(softest.posture) > ceiling_for(game):
                    one = 'is above what your record says you are ready for'
                elif (not softest.held and game.city.shifts_to(softest.district)
                      >= softest.expires - game.city.shift):
                    one = 'expires before the walk'
            why = ('nothing on the board is yours tonight: the softest of it, '
                   + (f'{softest.title}, {one}' if softest is not None and one
                      else ', or '.join(causes) if causes else 'is not for you'))
            # A bounty walls the board and the fee is in the account: the
            # name is the problem, and `burn` is the answer (D101).
            walled = [k for k, v in game.city.bounties.items() if v]
            burn_cost = (ALIAS_COST // 2 if 'no_history' in game.char.riders()
                         else ALIAS_COST)
            if (walled and game.char.credits >= burn_cost
                    and any(_hunted_on_route(game, c.district)[0] for c in live)):
                return steps + [('burn --confirm',
                                 f'{why}. A bounty is on this name and every '
                                 f'walk goes through it: a new name costs '
                                 f'{burn_cost:,}c and every relationship this '
                                 f'one has, and the board opens')]
            offers = street_world.errands_here(game)
            if offers and not game.city.errand:
                best = max(range(len(offers)), key=lambda i: offers[i]['pay'])
                return steps + [(f'errands take {best + 1}',
                                 f'{why}. Street work pays '
                                 f'({offers[best]["pay"]:,}c for this one) '
                                 f'and the board changes every shift')]
            if game.city.errand:
                to = game.city.errand.get('to', '')
                if (to in districts.BY_KEY and to != game.city.where
                        and not _hunted_on_route(game, to)[0]):
                    return steps + [(game.city.walk_to(to),
                                     f'{why}. The package you are carrying '
                                     f'pays in {districts.BY_KEY[to].name}')]
                if any(cmd.endswith('--anyway') or cmd.startswith('rest')
                       for cmd, _ in steps):
                    return steps
            return steps + [('rest 1',
                             f'{why}. A shift passes and the board turns; '
                             f'`train intrusion` is the number every door '
                             f'reads')]
        return steps + [('board', 'work on offer')]
    # A contract that has already cut you loose, twice (D87). The advice
    # said `jack in` after every sever, five nights running, on the same
    # network; the honest line is why, and the door out.
    tries = _attempts(game, contract.cid)
    chair = any(h.get('chair') for h in tries)
    if _dead_to_you(game, contract.cid):
        last = tries[-1]
        verb_odds = contract_mod.objective_odds(game.char, contract.objective,
                                                int(contract.posture))
        if any(h.get('refused', 0) >= 3 for h in tries):
            reason = (f'the {contract.objective} itself refused, over and '
                      f'over, at {verb_odds:.0%} with what you carry: '
                      f'{contract_mod.objective_skill(contract.objective)} '
                      f'is the number')
        elif chair:
            reason = ('you reached the chair and the room would not let '
                      'you use it: something awake on it, or a room that '
                      'went red and stayed there. The same network is the '
                      'same chair')
        elif any(h.get('short', 0) > 0 and not h.get('reached') for h in tries):
            gap = max(h.get('short', 0) for h in tries
                      if not h.get('reached'))
            reason = (f'each time you held a badge {gap} tier'
                      f'{"s" if gap != 1 else ""} short of the zone the job '
                      f'is in, and every door up there is a penalty until '
                      f'you have one. A forger opens a badge desk')
        elif any(h.get('held', 0) > 0 for h in tries):
            reason = ('each time your breaker ran below its rating for '
                      'want of Intrusion, and every door reads that number')
        else:
            reason = (f'the room found you at {last.get("alert", "red")} '
                      f'each time, which is the trace and not the doors')
        steps.append(('drop',
                      f'{contract.title} has cut you loose {len(tries)} '
                      f'times now: {reason}. Drop it and take something '
                      f'softer, or come back with more than you carry'))
    need = OBJECTIVE_PROGRAM.get(contract.objective)
    if need and not game.char.deck.has_category(need):
        owned = [programs.BY_KEY[k] for k in game.char.library
                 if k in programs.BY_KEY
                 and programs.BY_KEY[k].category == need]
        if owned:
            want = min(owned, key=lambda p: (p.memory, -p.rating))
            ok, _why = game.char.deck.can_load(want.key)
            if ok:
                steps.append((f'load {want.name.lower()}',
                              f'the job needs a {need} loaded, and you own '
                              f'one'))
            else:
                # Owned, and no room for it: the step is making room, and
                # it names what to take off. Without this `now` said `load`
                # for ever and the deck quietly refused every time.
                deck = game.char.deck
                loaded = [programs.BY_KEY[k] for k in deck.loaded
                          if k in programs.BY_KEY]
                spare = want.memory - deck.memory_free
                drop = None
                for p in sorted(loaded, key=lambda p: (p.category == need,
                                                       p.rating, -p.memory)):
                    if p.memory >= spare:
                        drop = p
                        break
                if drop is not None:
                    steps.append((f'unload {drop.name.lower()}',
                                  f'{want.name} needs {want.memory} memory '
                                  f'and the deck has {deck.memory_free}: '
                                  f'{drop.name} is the least of what is on '
                                  f'it'))
                else:
                    steps.append(('deck',
                                  f'{want.name} needs {want.memory} memory '
                                  f'and the deck has {deck.memory_free}. '
                                  f'A bigger bank, or carry less'))
        else:
            cheapest = min((p for p in programs.by_category(need)
                            if not p.unique), key=lambda p: p.price, default=None)
            shops = [d for d in districts.DISTRICTS if 'market' in d.services]
            here = game.city.district
            shop = here if 'market' in here.services else (
                min(shops, key=lambda d: game.city.shifts_to(d.key))
                if shops else here)
            price = (int(round(cheapest.price * shop.price_mult))
                     if cheapest is not None else 0)
            short = price - game.char.credits
            if cheapest is None:
                steps.append(('market program',
                              f'the job needs a {need} loaded, and you own none'))
            elif short > 0:
                # The dead end the first play test found: no payload, no
                # money, and `now` saying `market program` forever. Money
                # first, and the street pays without a deck.
                doable = [c for c in game.city.board
                          if not OBJECTIVE_PROGRAM.get(c.objective)
                          and c.cid != contract.cid]
                if game.city.errand:
                    steps.append((game.city.walk_to(game.city.errand['to']),
                                  f'{cheapest.name} is {price:,}c at the '
                                  f'{shop.name} market and you are {short:,}c '
                                  f'short: the package you are carrying pays '
                                  f'{int(game.city.errand["pay"]):,}c'))
                else:
                    # Named, not listed: advice a player can type once.
                    offers = street_world.errands_here(game)
                    best = max(range(len(offers)),
                               key=lambda i: offers[i]['pay']) if offers else -1
                    take = (f'errands take {best + 1}' if best >= 0
                            else 'errands')
                    pays = (f' It pays {offers[best]["pay"]:,}c.'
                            if best >= 0 else '')
                    steps.append((take,
                                  f'{cheapest.name} is {price:,}c at the '
                                  f'{shop.name} market and you are {short:,}c '
                                  f'short. Street work pays and needs no '
                                  f'deck.{pays} `borrow` is the other way'))
                if doable:
                    steps.append((f'drop; take {doable[0].cid}',
                                  f'or drop this one for {doable[0].title}, '
                                  f'which needs no program you do not have'))
            elif 'market' in here.services and any(
                    l.kind == 'program' and l.key == cheapest.key
                    for l in game.city.listings('program')):
                # It is on the shelf here and you can pay for it: name the
                # buy, not the shop. Advice you can type once.
                steps.append((f'buy {cheapest.name.lower()}',
                              f'the job needs a {need}, and {cheapest.name} '
                              f'is here for about {price:,}c'))
            elif 'market' in here.services:
                steps.append(('market program',
                              f'the job needs a {need} loaded, and you own '
                              f'none. Something here will do it'))
            else:
                steps.append((game.city.walk_to(shop.key),
                              f'the job needs a {need} and you own none. '
                              f'{cheapest.name} is about {price:,}c at the '
                              f'{shop.name} market, which is the nearest'))
    where = districts.BY_KEY[contract.district]
    hops = game.city.shifts_to(contract.district)
    if hops:
        # The walk, unless the walk is a refusal. `travel` will not take you
        # somewhere a faction is paying to find you, and advice that names a
        # command the game is about to refuse is the one thing advice must
        # never do: `now` said `travel` and the street said no, for ever.
        route = game.city.walk_to(contract.district)
        # Every hop, not the first: `walk` is one command and several
        # streets, and it stops at the first one that is hunting you.
        blocked, first = '', ''
        riders = game.char.riders()
        for hop in game.city.route(contract.district):
            danger, who = game.city.danger(game.alias, hop,
                                           flags=game.story.flags, riders=game.char.riders())
            if 'streetwise' in riders:
                danger = int(danger * 0.6)
            if 'findable' in riders:
                danger = int(danger * 1.3)
            # An arrangement is the walk being theirs: `travel` no longer
            # refuses it, so the advice does not either (D87).
            if (danger >= fallout.INCIDENT_FLOOR
                    and who not in game.city.arrangements):
                blocked, first = who, hop
                break
        if blocked:
            fac = factions.BY_KEY[blocked]
            hot = int(game.alias.attention(blocked))
            bounty = int(game.city.bounties.get(blocked, 0))
            here_d = game.city.district
            rate = _arrange_rate(game, blocked)
            # Only where it can be made, which is where they hold or are
            # (D100: `arrange kagawa` was advised in the Ninth seven times
            # and refused seven times), and only when three cycles of it
            # are in the account, because one advised arrangement bled an
            # account to nothing.
            if (game.char.credits >= rate * ARRANGE_CYCLES_AHEAD
                    and blocked in (here_d.controller, *here_d.presence)):
                steps.append((f'arrange {blocked}',
                              f'{fac.short} are paying to find you in '
                              f'{districts.BY_KEY[first].name} and the walk '
                              f'goes through it: an arrangement makes their '
                              f'streets passable, {rate:,}c every '
                              f'{city_mod.ARRANGE_EVERY} shifts'))
            cost = (ALIAS_COST // 2 if 'no_history' in game.char.riders()
                    else ALIAS_COST)
            if bounty or hot >= HEAT_WAITS_OUT:
                # Not `rest`. Heat cools about a point a shift and a
                # bounty does not cool at all: `rest 3` was said twenty
                # four times in a row to somebody with a bounty, while an
                # arrangement collected every six shifts (D87). The ways
                # out are to walk into it, to end the name, or to work
                # somewhere they are not.
                why = (f'{fac.short} have a bounty on this name'
                       if bounty else
                       f'{fac.short} are hunting you at heat {hot}, which '
                       f'cools about a point a shift')
                steps.append(('drop',
                              f'{why}, and the job walks through '
                              f'{districts.BY_KEY[first].name}. Drop it and '
                              f'take work that does not, or `{route} '
                              f'--anyway` walks into them and the street '
                              f'prices it'))
                if game.char.credits >= cost:
                    steps.append(('burn --confirm',
                                  f'{why}, and the job walks through them. '
                                  f'A new name costs {cost:,}c and every '
                                  f'relationship this one has'))
            else:
                steps.append((f'rest {max(1, hot - HEAT_WAITS_OUT + 8)}',
                              f'{fac.short} are hunting you on the way '
                              f'there. Heat is {hot} and cools about a '
                              f'point a shift: `burn` ends the name for '
                              f'{cost:,}c, and `{route} --anyway` walks '
                              f'into them'))
            return steps
        steps.append((route,
                      f'the job is in {where.name}, {hops} shift'
                      f'{"s" if hops != 1 else ""} away'))
        steps.append(('jack in', 'once you are there'))
    else:
        steps.append(('jack in', 'you are in the right district'))
    return steps


@command('take', 'Accept a contract.',
         contexts=('city',), group='city', usage='take <id|row number>',
         detail=(
                'Accepts a contract and makes it yours until you finish it, '
                'drop it, or it expires. One at a time. Rival runners take '
                'what you leave on the board, so reading all five before '
                'choosing has a price. `board <id>` first: it prints the '
                'walk, the size, how the target\'s doors read against your '
                'breaker, and how their networks are built.'))
def cmd_take(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if game.city.accepted:
        raise CommandError(f'you are already on {game.city.accepted}. '
                           f'`drop` it first.')
    contract = _contract_arg(
        sess, args.require(0, 'a contract id, or its row on the board'))
    contract.taken = True
    game.city.accepted = contract.cid
    c.ok(f'Taken: [accent]{contract.title}[/] against '
         f'{contract.target_data.short}, {contract.pay:,}c.')
    # The same warning `board <id>` gives, on the screen people actually
    # reach. `now` says `take c005`, so the advice routes straight past
    # the reading screen, and the first anybody heard about a missing
    # payload was the job sheet afterwards or the objective host itself
    # (D75).
    from ..world.contracts import OBJECTIVE_PROGRAM
    need = OBJECTIVE_PROGRAM.get(contract.objective)
    if need and not game.char.deck.has_category(need):
        owned = any(k in programs.BY_KEY
                    and programs.BY_KEY[k].category == need
                    for k in game.char.library)
        c.blank()
        if owned:
            c.warn(f'You have no {need} loaded, and this objective needs '
                   f'one. You own one: `load` it before you jack in.')
        else:
            c.warn(f'You have no {need}, and this objective needs one. '
                   f'The loadout is fixed the moment you jack in.')
    if contract.from_npc:
        from ..content import npcs as npc_content, offers
        work = offers.BY_NPC_WORK.get(contract.from_npc)
        who = npc_content.BY_KEY.get(contract.from_npc)
        if work is not None and who is not None:
            c.blank()
            c.say(f'[accent]{who.name}:[/] {work.closing}')
    from ..world import rivals as rival_world
    for line in rival_world.on_player_took(game.rng('rivals'),
                                           game.city.rivals, contract):
        c.say(line)
    where = districts.BY_KEY[contract.district]
    if game.city.where != contract.district:
        hops = game.city.shifts_to(contract.district)
        c.info(f'The job is in {where.name}, {hops} shift'
               f'{"s" if hops != 1 else ""} from here.')
        c.raw(f'  [fg]{game.city.walk_to(contract.district)}[/]')
    else:
        c.info('You are in the right district. `jack in` when ready.')


@command('drop', 'Abandon the accepted contract.',
         contexts=('city',), group='city', usage='drop',
         detail=(
                'Gives back the contract you accepted. The patron notices. '
                'Better than carrying a job you cannot do into a network that '
                'will kill you for trying.'))
def cmd_drop(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    contract = game.city.current
    if contract is None:
        raise CommandError('you have not taken anything')
    game.city.accepted = ''
    contract.taken = False
    game.alias.adjust_rep(contract.patron, -4)
    c.warn(f'Dropped {contract.title}. {contract.patron_data.short} noticed.')
    # A board posting is a market and does not care. A job somebody was
    # holding for you is a person, and dropping it is the one thing a posting
    # cannot charge you for.
    if contract.from_npc:
        from ..content import npcs as npc_content, offers
        work = offers.BY_NPC_WORK.get(contract.from_npc)
        who = npc_content.BY_KEY.get(contract.from_npc)
        if work is not None and who is not None:
            # Clamped, because the limit is how far they will let you get
            # and not how far you can be pushed. Past it they are already
            # refusing you; going to four changes nothing except making the
            # screen that says "as deep as they will let you get" a lie.
            game.story.owed[who.key] = min(
                offers.OWED_LIMIT, game.story.owed.get(who.key, 0) + 1)
            game.city.board = [x for x in game.city.board
                               if x.cid != contract.cid]
            c.blank()
            c.say(f'[err]{work.dropped}[/]')


# --------------------------------------------------------------------------
# movement and time
# --------------------------------------------------------------------------
#
# The city is a graph of nine places and it was, for a long time, a graph the
# player could only ever see one node of. `travel` with no arguments listed the
# neighbours of wherever you were standing, and that was the entire published
# map. Somebody with a contract two districts away had no way to find out which
# way to walk except to walk somewhere and look again.
#
# So: the shape is known from the start, and the detail is not. A runner who
# lives in this city knows that Marrow touches the Vertical, in the way anybody
# knows their own city; what they do not know is what is actually on a street
# they have never worked. Hiding the road layout from a local would be the less
# believable option, and it is also the one that leaves a player stuck.


def city_map(sess) -> None:
    """The whole city, as a shape, dim where you have not been."""
    game, c = sess.require_game(), sess.console
    city = game.city
    walked = set(city.visited)
    c.header('The city',
             f'{len(walked)} of {len(districts.DISTRICTS)} walked')

    # The picture first (D57): the same shape every time, you marked on it.
    # The tree underneath carries what a picture cannot, which is distance
    # and what each place has.
    from .. import citymap
    c.blank()
    for line in citymap.draw(game, c.caps, flags=game.story.flags):
        c.raw(line)
    c.blank()
    c.say(citymap.legend(c.caps), indent='  ')
    c.blank()
    # Why it is that shape. Twelve names in a grid is a menu; a city has a
    # reason for each of them being where it is (D67).
    c.say(f'[dim]{citymap.LAYOUT}[/]', indent='  ', subsequent='  ')
    # How much city there is. Counted, not claimed.
    from ..content import npcs as npc_content, spots as spot_content
    c.say(f'[dim]{len(districts.DISTRICTS)} districts, '
          f'{len(spot_content.SPOTS)} places to stand in, '
          f'{len(npc_content.NPCS)} people worth finding.[/]', indent='  ')

    # Drawn from the district everybody starts in rather than from wherever
    # you happen to be standing. A tree rooted at you is a compass: it points
    # the right way and it reshuffles every time you move, so it never becomes
    # a picture anybody can hold in their head. Rooted at one fixed place the
    # shape is the same every time, and the distance from *you* goes in a
    # column, where it can be read without being memorised.
    ascii_only = c.caps.glyphs is ui.GlyphLevel.ASCII
    everywhere = set(districts.DISTRICT_KEYS)
    rows = ui.tree_rows(districts.GRAPH, districts.START, everywhere,
                        ascii_only)
    _, extra = ui.spanning_tree(districts.GRAPH, districts.START, everywhere)

    contract = city.current
    goal = contract.district if contract else ''
    c.blank()
    for prefix, key in ui.tree_leads(rows):
        c.raw(f'[dim]{prefix}[/]'
              f'{_district_label(sess, key, walked, goal)}')

    # The tree can only draw one route into each district and the city has
    # more than one into most of them. Saying so matters here more than it
    # does in a network: a second way in is a second way to be somewhere the
    # people looking for you are not.
    pairs = sorted({tuple(sorted((a, b)))
                    for a, others in extra.items() for b in others})
    if pairs:
        # Grouped by the left district rather than listed as pairs. Six
        # "x and y" clauses in one sentence wraps into a paragraph of place
        # names that nobody reads; four short rows can be scanned.
        joins: dict[str, list[str]] = {}
        for a, b in pairs:
            joins.setdefault(a, []).append(b)
        c.blank()
        c.say('[dim]Also joined, which the shape above cannot show:[/]')
        for a in sorted(joins):
            c.raw(f'  [fg]{a:<11}[/] [dim]{", ".join(sorted(joins[a]))}[/]')

    if goal and goal != city.where:
        route = city.route(goal)
        c.blank()
        c.say(f'[accent2]The job is in {districts.BY_KEY[goal].name}[/][dim], '
              f'{len(route)} shift{"s" if len(route) != 1 else ""} from '
              f'here.[/]')
        # On its own line, because prose wraps and a command chain broken
        # across two lines is a command chain somebody has to reassemble
        # before they can use it.
        c.raw(f'  [fg]{city.walk_to(goal)}[/]')
    c.blank()
    c.say('[dim]`travel <district>` is one shift to a neighbour. '
          '`walk <district>` goes the whole way, a shift a step, and stops '
          'if the street stops you.[/]')


def _district_label(sess, key: str, walked: set, goal: str) -> str:
    """One district: where it is in your week, and what is on it."""
    game = sess.game
    d = districts.BY_KEY[key]
    here = key == game.city.where
    hops = game.city.shifts_to(key)
    name = f'[{"accent" if here else "fg" if key in walked else "dim"}]' \
           f'{key:<11}[/]'
    # Padded on the visible text rather than on the marked-up string. A role
    # tag is four characters nobody can see and every column downstream of it
    # would be four characters out.
    said = 'here' if here else f'{hops} shift{"s" if hops != 1 else ""}'
    when = (f'[accent]{said}[/]' if here else f'[dim]{said}[/]') \
        + ' ' * max(1, 10 - len(said))
    marks = []
    if key == goal:
        marks.append('[accent2]the job[/]')
    if key not in walked:
        marks.append('[dim]not been[/]')
    elif not here:
        # Only for somewhere you might go. What the people in this district
        # think of you is not news when you are already standing in it, and
        # it costs the row the width that the useful half needs.
        danger, who = game.city.danger(game.alias, key,
                                       flags=game.story.flags, riders=game.char.riders())
        if danger >= fallout.INCIDENT_FLOOR:
            marks.append(f'[err]{factions.BY_KEY[who].short} want you[/]')
        elif danger >= 25:
            marks.append(f'[warn]{factions.BY_KEY[who].short} looking[/]')
    role = 'info' if key in walked else 'dim'
    tail = f'[{role}]{" ".join(d.services)}[/]'
    line = (f'{name} [dim]{factions.BY_KEY[d.controller].short:<11}[/] '
            f'{when}' + '  '.join(marks + [tail]))
    # The full terminal, less a column. These rows are drawn rather than
    # wrapped, so the only thing a narrow budget buys is an ellipsis on a line
    # that had room.
    return ui.truncate(line, max(40, sess.console.caps.width - 2),
                       sess.console.caps)


@command('travel', 'Move to another district. Costs a shift.',
         contexts=('city',), group='city', aliases=('go',),
         usage='travel <district>',
         blocked='Your body is in a chair in the district you jacked in from, '
                 'and it is going to stay there until you are back in it.',
         complete=lambda sess, prefix: list(districts.DISTRICT_KEYS),
         detail=(
                'One shift to a neighbouring district, and prints what you '
                'went through to get there. It refuses to walk you into a '
                'district where somebody is paying to find you: `--anyway` '
                'overrides that and means it. `walk <district>` crosses the '
                'whole city a shift at a time and stops if the street stops '
                'you.'))
def cmd_travel(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if not len(args):
        c.header('From here', game.city.district.name)
        rows = []
        for n, key in enumerate(game.city.district.neighbours, 1):
            d = districts.BY_KEY[key]
            danger, who = game.city.danger(game.alias, key,
                                           flags=game.story.flags, riders=game.char.riders())
            risk = ('[ok]quiet[/]' if danger < 20
                    else '[warn]watched[/]' if danger < 45
                    else f'[err]dangerous ({factions.BY_KEY[who].short})[/]')
            rows.append((str(n), key, d.name,
                         factions.BY_KEY[d.controller].short,
                         ', '.join(d.services), risk))
        c.table(('#', 'key', 'district', 'runs it', 'has', 'for you'), rows,
                roles=('accent', 'dim', 'accent', 'info', 'dim', None))
        sess.remember('travel', list(game.city.district.neighbours))
        c.blank()
        c.say('[dim]`travel <key>` or `travel <row number>`. Each one is a '
              'shift. `map` for the whole city and the walk to anywhere.[/]')
        return

    target = sess.pick('travel', args[0].lower(),
                       fallback=list(game.city.district.neighbours),
                       what='row', again='travel')
    matches = [k for k in districts.DISTRICT_KEYS if k.startswith(target)]
    if len(matches) == 1:
        target = matches[0]
    ok, why = game.city.can_travel(target)
    if not ok:
        if args.has('anyway') and why.endswith('`'):
            why = why[:-1] + ' --anyway`'
        raise CommandError(why)

    danger, who = game.city.danger(game.alias, target, game.rng,
                                   flags=game.story.flags, riders=game.char.riders())
    riders = game.char.riders()
    if 'streetwise' in riders:
        # Knows the streets: you move through this city like your own flat.
        danger = int(danger * 0.6)
    if 'findable' in riders:
        # Everybody knows where you drink, including everybody you would
        # rather did not.
        danger = int(danger * 1.3)
    # A standing arrangement is the walk being theirs (D87): their people
    # have been told, the tier is capped, and refusing the street the
    # player paid for made the arrangement a number with nothing behind it.
    if (danger >= fallout.INCIDENT_FLOOR and not args.has('anyway')
            and who not in game.city.arrangements):
        fac = factions.BY_KEY[who]
        hot = int(game.alias.attention(who))
        slow = (hot >= HEAT_WAITS_OUT
                or int(game.city.bounties.get(who, 0)) > 0)
        raise CommandError(
            f'{fac.name} have people in '
            f'{districts.BY_KEY[target].name} and a number attached to your '
            f'name. Going anyway is a real risk: `travel {target} --anyway`. '
            + ('Otherwise `rest` until it cools, or `burn` the name.'
               if not slow else
               f'Heat is {hot} and cools about a point a shift, so resting '
               f'is not the answer: `arrange {who}` if they will take your '
               f'money, `burn` the name, or work somewhere they are not.'))

    known = target in game.city.visited
    # What is between here and there (D67). The city is only as big as the
    # distance you can feel, and a shift passing in silence feels like no
    # distance at all.
    between = districts.crossing(game.city.where, target, game.city.shift)
    game.city.where = target
    game.city.visited.add(target)
    district = districts.BY_KEY[target]
    if between:
        c.blank()
        c.say(f'[dim]{between}[/]')
    free = known and 'streetwise' in game.char.riders()
    if free:
        # You have walked this one before. You know which stairwells connect.
        _drift(sess)
        sess.autosave()
    else:
        _advance(sess, 1, story=False)
    c.blank()
    c.rule(district.name)
    c.say(district.arrival)
    if district.scale:
        c.say(f'[dim]{district.scale}[/]')
    # What the place is doing at this hour, which is not the same thing as
    # what it is (D53).
    now = districts.scene(district.key, game.city.phase)
    if now:
        c.blank()
        c.say(now)
    street = districts.street_line(district.key, game.city.shift)
    if street:
        c.say(f'[dim]{street}[/]')
    if free:
        c.info('You know the way. It does not cost you a shift.')

    # What is here, before the street has its say: a question pending
    # used to print the market line between the options and the prompt
    # (D91).
    here_you_can(sess, district)
    people_here(sess)
    # A package for here is delivered before anything else happens (D65).
    street_world.deliver(sess)
    if danger >= fallout.INCIDENT_FLOOR:
        _resolve_incident(sess, who, danger)
    elif danger >= 25:
        c.blank()
        # The band below an incident is not a warning line any more. The
        # street may let you know, and the letting-know costs a little.
        call = fallout.close_call(game.rng('events'), game.alias, game.city,
                                  who, danger)
        if call is not None:
            c.rule('noticed', role='warn')
            c.say(f'[warn]{call.text}[/]')
            c.say(f'[dim]{call.detail}[/]')
        else:
            c.warn(f'{factions.BY_KEY[who].short} have people here and they '
                   f'are looking for your name. Do not linger.')
    elif sess.pending is None:
        # Below that: the street as texture (D65). Somebody behind you,
        # somebody with a pot. Small, and not every time.
        street_world.texture(sess, danger)
    # A scene set here fires on arrival, after the district and not before
    # it: "waiting for you to be there" means there (D91).
    if sess.pending is None:
        from .people import _check_story
        _check_story(sess)


#: What each thing a district has is called at the prompt. A district that
#: "has a workshop" means nothing to somebody who does not know that the
#: verb for a workshop is `repair`; this is the line that says so.
SERVICE_VERBS = (
    ('market', 'market', 'buy and sell'),
    ('clinic', 'clinic', 'chrome, grounding, detox'),
    ('workshop', 'repair', 'the deck, and `mod` for bench work'),
    ('fence', 'sell', 'what you carried out'),
    ('safehouse', 'safehouse', 'somewhere of your own'),
    ('fixer', 'look', 'somebody worth talking to'),
)


def here_you_can(sess, district, looking: bool = False) -> None:
    """One line naming the verbs this district makes possible.

    Printed on arrival and by `look`, because the map and the travel table
    both list what a district *has*, and a new player reading "workshop"
    has no way to get from that noun to the word they need to type. From
    inside `look` the advice to look is left out: the people are printed
    directly underneath.
    """
    c = sess.console
    parts = [f'[fg]{verb}[/] [dim]({what})[/]'
             for service, verb, what in SERVICE_VERBS
             if service in district.services
             and not (looking and verb == 'look')]
    if not parts:
        return
    c.blank()
    bullet = c.caps.g('bullet')
    c.say('[dim]Here:[/] ' + f' [dim]{bullet}[/] '.join(parts)
          + f' [dim]{bullet}[/] [fg]travel[/] [dim](to move on)[/]',
          subsequent='  ')


def people_here(sess) -> None:
    """Who is standing here, on arrival, in one line.

    The story layer is gated almost entirely on meeting people, and
    arriving somewhere used to list the market, the workshop and the
    places to stand without once mentioning that there were people in the
    street. `look` names them, but `look` is one of the verbs the advice
    only ever lists under "also", and a player following `now` from job to
    job could play a whole career without meeting anybody (D86). The met
    are named; the rest are a count, because meeting somebody is `look`'s
    moment and this line should send you there rather than replace it.
    """
    game, c = sess.game, sess.console
    if game is None or sess.pending is not None:
        return
    from ..world import story as story_mod
    here = story_mod.present(game, game.story)
    if not here:
        return
    met = [n.name for n in here if n.key in game.story.met]
    new = len(here) - len(met)
    parts = []
    if met:
        parts.append(', '.join(met))
    if new:
        parts.append(('somebody' if new == 1 else f'{new} people')
                     + ' you have not met')
    c.say('[dim]People:[/] ' + (' and ' if len(parts) == 2 else '').join(parts)
          + ' [dim](`look` to see who, `talk <name>` to talk)[/]'
          if new else
          '[dim]People:[/] ' + parts[0]
          + ' [dim](`talk <name>`)[/]',
          subsequent='  ')


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
    # D65: more often than not it is people, not a ladder. The ladder stays
    # for the rest: shakedown, beating, deck, chrome, burn.
    if street_world.on_arrival(sess, faction, danger):
        return
    incident = fallout.pick_up(stream, game.char, game.alias, game.city,
                               faction)
    c.blank()
    c.rule('picked up', role='err')
    c.say(f'[err]{incident.text}[/]')
    if incident.detail:
        c.blank()
        c.say(incident.detail)
    # The wire remembers, and `walk` reads it to know to stop (D57).
    game.city.news.append(f'[err]Picked up in {game.city.district.name}.[/] '
                          f'{incident.detail}')
    sess.autosave()


@command('walk', 'Go the whole way to a district, a shift a step.',
         contexts=('city',), group='city', usage='walk <district> [--anyway]',
         blocked='Your body is in a chair in the district you jacked in from, '
                 'and it is going to stay there until you are back in it.',
         detail='`travel` is one shift to a neighbour. `walk` is the same '
                'thing repeated until you arrive: each step costs a shift, '
                'each step is a street you are walking into, and it stops '
                'the moment a street stops you, whether that is somebody '
                'picking you up or a district you would have to `--anyway` '
                'your way into. `map` shows the walk to anywhere.',
         complete=lambda sess, prefix: list(districts.DISTRICT_KEYS))
def cmd_walk(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    want = (args.get(0) or '').lower()
    if not want:
        raise CommandError('walk where? `map` for the city.')
    matches = [k for k in districts.DISTRICT_KEYS if k.startswith(want)]
    if len(matches) != 1:
        raise CommandError(f'{want!r} is not a district. `map` for the '
                           f'twelve.')
    target = matches[0]
    if target == game.city.where:
        raise CommandError(f'you are in {districts.BY_KEY[target].name}.')
    route = game.city.route(target)
    if not route:
        raise CommandError(f'there is no way to {target} from here.')
    c.info(f'{len(route)} shift{"s" if len(route) != 1 else ""}: '
           + ', then '.join(route) + '.')
    for step in route:
        before = len(game.city.news)
        seen = sum(len(v) for v in game.story.reached.values())
        try:
            cmd_travel(sess, Args([step] + (['--anyway'] if args.has('anyway')
                                            else [])))
        except CommandError as e:
            c.err(str(e))
            c.say('[dim]The walk stops here.[/]')
            return
        if game.city.where != step:
            return
        if (sum(len(v) for v in game.story.reached.values()) > seen
                and step != route[-1]):
            # Something happened here (D100): five scenes and two
            # decisions arrived in one `walk`. A scene is a reason to stop.
            c.blank()
            c.say(f'[dim]The walk stops here: something happened. `walk '
                  f'{target}` again when you are ready.[/]')
            return
        if sess.pending is not None:
            # The street has stopped you and is waiting on an answer. The
            # walk carried on through two more districts with the question
            # still open, and the encounter re-printed itself wherever it
            # ended up (D87). README always said it stops; now it does.
            if step != route[-1]:
                c.say(f'[dim]The walk stops here. `walk {target}` again '
                      f'once this is settled.[/]')
            return
        picked = any('Picked up' in line
                     for line in game.city.news[before:])
        if picked and step != route[-1]:
            c.blank()
            c.say('[dim]The walk stops here. `walk {0}` again when you are '
                  'ready.[/]'.format(target))
            return


@command('rest', 'Lie low. Heals, cools heat, and passes time.',
         contexts=('city',), group='city', usage='rest [shifts]',
         blocked='Time in here is measured in ticks and the trace is spending '
                 'them. `steady` is the closest thing to a breath you get.',
         detail=(
                'Spends shifts doing nothing, which heals Integrity and cools '
                'heat. A safehouse of your own doubles the healing; '
                'Fieldcraft rank 2 adds to it again. Sleeping rough somewhere '
                'a faction wants you is how people get found, and the street '
                'knows where you sleep.'))
def cmd_rest(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    shifts = max(1, min(12, args.int_at(0, 1, 'a number of shifts')))
    safe = 'safehouse' in game.city.district.services
    before = game.char.hurt
    heal = (2 if safe else 1) * shifts
    if game.char.has_technique('scar'):
        # Scar Tissue (D65): a point more per shift, two more somewhere safe.
        heal += (2 if safe else 1) * shifts
    riders = game.char.riders()
    # Whatever they used to restart you has never entirely stopped, and three
    # hours a night for eleven years is not rest.
    if 'slow_healing' in riders:
        heal = heal // 2
    if 'poor_rest' in riders:
        heal = int(heal * 0.6)
    game.char.hurt = max(0, game.char.hurt - heal)
    healed = before - game.char.hurt
    # Said before the world reports itself, not after. What happened while you
    # were lying low reads as consequence; the same lines printed above the
    # confirmation read as a preamble to nothing.
    c.ok(f'{shifts} shift{"s" if shifts != 1 else ""} pass.'
         + (f' [ok]Integrity +{healed}.[/]' if healed else ''))
    _advance(sess, shifts)
    if not safe:
        c.info('No safehouse here. You did not sleep well.')
        if sess.pending is None and sess.game is not None:
            street_world.rough_night(sess)
    if 'slow_healing' in game.char.riders():
        c.info('You heal the way you have healed since the table.')
    elif 'poor_rest' in game.char.riders():
        c.info('Three hours, like every night.')


# --------------------------------------------------------------------------
# identity
# --------------------------------------------------------------------------


@command('arrange', 'A standing arrangement with a faction, on the street.',
         contexts=('city',), group='city', usage='arrange [faction|stop <faction>]',
         detail='D65. Pay a faction to have their people told. While it '
                'stands, their streets are safer for you (danger down by '
                'twenty-five) and the people who stop you lean rather than '
                'take; the number comes round every six shifts and is '
                'collected from the account, and a payment you cannot make '
                'ends it, with heat, because they remember who ended it. It '
                'is made with somebody who works for them, so it needs a '
                'district they hold or have a presence in, and it is refused '
                'to anybody with a big enough number on their name: past a '
                'point they want the number, not your money. `arrange` alone '
                'lists what stands and what one would cost here.')
def cmd_arrange(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    city = game.city
    district = city.district
    reachable = [district.controller, *district.presence]
    verb = (args.get(0) or '').lower()
    if verb == 'stop':
        key = _faction_arg(args.get(1) or '')
        if key not in city.arrangements:
            raise CommandError('no arrangement with them stands.')
        del city.arrangements[key]
        game.alias.adjust_rep(key, -ARRANGE_STOP_REP)
        c.ok(f'The arrangement with {factions.BY_KEY[key].short} is over, '
             f'on your terms. [dim]They will not forget it was yours to '
             f'end: {-ARRANGE_STOP_REP} standing.[/]')
        return
    if not verb:
        c.header('Arrangements', district.name)
        if city.arrangements:
            for key, deal in city.arrangements.items():
                due = city_mod.ARRANGE_EVERY - (city.shift - int(deal['paid']))
                c.raw(f'  [accent]{factions.BY_KEY[key].short:<12}[/] '
                      f'[credit]{int(deal["rate"]):,}c[/] [dim]every '
                      f'{city_mod.ARRANGE_EVERY} shifts, next in {max(0, due)}[/]')
        else:
            c.say('[dim]None stand.[/]')
        c.blank()
        c.say('[dim]Within reach here: '
              + ', '.join(f'{factions.BY_KEY[k].short} '
                          f'({_arrange_rate(game, k):,}c)'
                          for k in reachable if k not in city.arrangements)
              + '. `arrange <faction>` to make one, `arrange stop <faction>` '
                'to end one.[/]')
        return
    key = _faction_arg(verb)
    if key not in reachable:
        raise CommandError(f'{factions.BY_KEY[key].short} have nobody here to '
                           f'arrange it with. Somewhere they hold, or are.')
    if key in city.arrangements:
        raise CommandError(f'it already stands with {factions.BY_KEY[key].short}.')
    if int(city.bounties.get(key, 0)) >= 60:
        raise CommandError(f'{factions.BY_KEY[key].short} want the number on '
                           f'your name, not your money. Past this point there '
                           f'is no arrangement.')
    rate = _arrange_rate(game, key)
    if game.char.credits < rate:
        raise CommandError(f'the first payment is {rate:,}c, up front, and '
                           f'you have {game.char.credits:,}c.')
    game.char.credits -= rate
    city.arrangements[key] = {'rate': rate, 'paid': city.shift}
    c.ok(f'Somebody who works for {factions.BY_KEY[key].short} takes '
         f'[credit]{rate:,}c[/] and makes a note, and the note goes where '
         f'notes go.')
    c.say(f'[dim]Their people will lean rather than take, and their streets '
          f'are easier for you, while the number comes round every '
          f'{city_mod.ARRANGE_EVERY} shifts and you can pay it.[/]')
    game.city.news.append(f'An arrangement with {factions.BY_KEY[key].short}: '
                          f'{rate:,}c every {city_mod.ARRANGE_EVERY} shifts.')
    sess.autosave()


def _faction_arg(token: str) -> str:
    q = token.lower().strip()
    for key, fac in factions.BY_KEY.items():
        if q in (key, fac.short.lower(), fac.name.lower()) or fac.short.lower().startswith(q) and q:
            return key
    raise CommandError(f'no faction called {token!r}.')


def _arrange_rate(game, key: str) -> int:
    heat = game.alias.attention(key)
    bounty = int(game.city.bounties.get(key, 0))
    return int(city_mod.ARRANGE_BASE + heat * 6 + bounty * 10)


@command('errands', 'Street work: carry something, or stand somewhere.',
         contexts=('city',), group='city', aliases=('errand', 'odd'),
         usage='errands [take <n>|drop]',
         detail='D65. The half of the game that is not a deck. Two pieces of '
                'work on offer in every district every shift: carry a '
                'package to a district one to three shifts away and get paid '
                'on arrival; or something local: a shift on watch at a place '
                'here, a debt to collect with your voice, or somebody who '
                'needs walking across the city at your pace. Paid '
                'in credits, priced by how far and how dangerous, with the '
                'street in the way: a courier with a hot package is somebody '
                'worth stopping. No program, no deck, no trace. `errands '
                'take <n>` to take one, `errands drop` to put a package down '
                'unpaid. Only one package at a time; a watch is done on the '
                'spot.')
def cmd_errands(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    verb = (args.get(0) or '').lower()
    if verb == 'drop':
        if not game.city.errand:
            raise CommandError('you are not carrying anything.')
        what = game.city.errand.get('what', 'the package')
        game.city.errand = {}
        c.ok(f'You put {what} down somewhere it will be found, unpaid.')
        return
    offers = street_world.errands_here(game)
    if verb in ('take', 'accept'):
        if game.city.errand:
            raise CommandError(f'you are already carrying '
                               f'{game.city.errand.get("what", "something")} '
                               f'to {districts.BY_KEY[game.city.errand["to"]].name}. '
                               f'`errands drop` to put it down.')
        token = sess.pick('errands', args.get(1) or '', fallback=['1', '2'],
                          what='errand', again='errands')
        n = int(token) if str(token).isdigit() else 0
        if not 1 <= n <= len(offers):
            raise CommandError(f'which one? 1 to {len(offers)}.')
        job = offers[n - 1]
        if job['kind'] in ('courier', 'escort'):
            game.city.errand = dict(job)
            game.city.errands_taken.add(job.get('key', ''))
            to = districts.BY_KEY[job['to']]
            c.ok(f'You take {job["what"]}. {to.name}, '
                 f'{game.city.shifts_to(to.key)} shift'
                 f'{"s" if game.city.shifts_to(to.key) != 1 else ""} away, '
                 f'[credit]{job["pay"]:,}c[/] on arrival.')
            if job['kind'] == 'escort':
                c.warn('They walk at your pace and they are worth stopping. '
                       'Anybody who stops you stops them.')
            elif job.get('hot'):
                c.warn('It is warm. Whoever wants it wants it badly enough '
                       'that somebody else might too.')
            c.say(f'[dim]`{game.city.walk_to(to.key)}`. The wire remembers '
                  f'what you are carrying.[/]')
            game.city.news.append(f'Carrying {job["what"]} to {to.name}.')
            sess.autosave()
            return
        if job['kind'] == 'collect':
            game.city.errands_taken.add(job.get('key', ''))
            street_world.collect(sess, job)
            # A door, a conversation and the walk there is a shift, like
            # the watch (D101).
            if sess.game is not None and sess.pending is None:
                _advance(sess, 1)
            sess.autosave()
            return
        game.city.errands_taken.add(job.get('key', ''))
        # watch: a shift, here, now
        pay = job['pay']
        c.say(f'You stand a shift at {job["at"]}. Nothing is asked of you '
              f'but to be there and to notice.')
        _advance(sess, 1)
        if sess.game is None or not game.char.integrity:
            return
        game.char.credits += pay
        game.earned += pay
        game.city.errands_done += 1
        game.char.xp += street_world.ERRAND_XP
        c.say(f'[dim]{street_world.ERRAND_XP} experience.[/]')
        c.ok(f'[credit]{pay:,}c[/] for the shift.')
        danger, who = game.city.danger(game.alias, game.city.where,
                                       flags=game.story.flags, riders=game.char.riders())
        if sess.pending is None:
            if not street_world.texture(sess, danger) and who \
                    and danger >= 30:
                street_world.on_arrival(sess, who, danger)
        sess.autosave()
        return
    c.header('Errands', game.city.district.name)
    rows = []
    for n, job in enumerate(offers, 1):
        if job['kind'] in ('courier', 'escort'):
            to = districts.BY_KEY[job['to']]
            hops = game.city.shifts_to(to.key)
            rows.append((str(n), job['kind'],
                         f'{job["what"]} to {to.name} '
                         f'({hops} shift{"s" if hops != 1 else ""})'
                         + (' [warn]warm[/]' if job.get('hot')
                            and job['kind'] == 'courier' else ''),
                         f'{job["pay"]:,}c'))
        elif job['kind'] == 'collect':
            rows.append((str(n), 'collect',
                         f'{job["owed"]:,}c from {job["who"]}, your cut',
                         f'{job["pay"]:,}c'))
        else:
            rows.append((str(n), 'watch', f'a shift at {job["at"]}',
                         f'{job["pay"]:,}c'))
    c.table(('#', 'kind', 'what', 'pay'), rows,
            roles=('accent', 'dim', 'fg', 'credit'))
    sess.remember('errands', ['1', '2'][:len(offers)])
    if game.city.errand:
        e = game.city.errand
        c.blank()
        c.say(f'[dim]Carrying {e.get("what", "something")} to '
              f'{districts.BY_KEY[e["to"]].name} for {int(e["pay"]):,}c.[/]')
    c.blank()
    c.say('[dim]`errands take <n>`. No deck needed. The street is still the '
          'street.[/]')


@command('alias', 'The name you are running under, and what it carries.',
         contexts=('city',), group='prep', usage='alias')
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
         contexts=('city',), group='prep', usage='burn [name] [--confirm]',
         detail=(
                'Abandons this identity and starts another. Heat and standing '
                'both go with it: everything you built under the name and '
                'everything anybody is holding against it. The last resort, '
                'and sometimes the cheapest thing in the game.'))
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
    # A bounty is a number attached to a name, so it goes when the name
    # does. It did not: `city.bounties` is keyed by faction and nothing
    # cleared it, so burning cost eighteen hundred credits and every
    # relationship built under the old name and left the streets exactly
    # as dangerous. The manual has always said "sometimes that is cheaper
    # than the bounty", and it was not true of any bounty (D75).
    retired = sorted(game.city.bounties)
    game.city.bounties.clear()
    # And the warnings that came with them: "next time they will not be
    # asking" was said to somebody who no longer exists.
    for flag in [f for f in game.story.flags if f.startswith('warned:')]:
        game.story.flags.discard(flag)
    lost = sorted(((k, v) for k, v in alias.rep.items() if v > 0),
                  key=lambda kv: -kv[1])[:3]
    fresh = game.new_alias(name)
    _advance(sess, shifts)
    c.ok(f'{alias.name} is gone. You are [accent]{fresh.name}[/] now.')
    # What it cost, said (D96): the fee went silently and the standing
    # with it was never named.
    c.say(f'[dim]{cost:,}c for the name'
          + (', and the standing that was theirs: '
             + ', '.join(f'{factions.BY_KEY[k].short} {v:+d}'
                         for k, v in lost if k in factions.BY_KEY)
             if lost else '') + '.[/]')
    if retired:
        names = ', '.join(factions.BY_KEY[k].short for k in retired
                          if k in factions.BY_KEY)
        c.say(f'[ok]The number came off with it.[/] [dim]{names} were '
              f'paying to find somebody who does not exist any more.[/]')


@command('rep', 'How the city feels about you, in full.',
         group='info', usage='rep',
         detail=(
                'How the whole city feels about you: standing with each '
                'faction, the heat on your current name, their security '
                'posture, any arrangements you are paying for, and who has '
                'warned you in the street. Standing buys prices, work and '
                'back rooms; heat buys trouble.'))
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
    if game.city.arrangements:
        c.blank()
        c.say('[dim]Arrangements: '
              + ', '.join(f'{factions.BY_KEY[k].short} '
                          f'({int(v["rate"]):,}c every '
                          f'{city_mod.ARRANGE_EVERY})'
                          for k, v in game.city.arrangements.items())
              + '.[/]')
    warned = sorted(f[7:] for f in game.story.flags if f.startswith('warned:'))
    if warned:
        c.say('[err]Warned you, in so many words: '
              + ', '.join(factions.BY_KEY[w].short for w in warned
                          if w in factions.BY_KEY) + '.[/]')
    c.blank()
    c.say('[dim]Posture is how hard their networks generate. It rises when '
          'you succeed against them and falls slowly.[/]')
    cover = game.char.cover
    if cover:
        c.say(f'[dim]Heat cools on its own, at a rate each faction sets for '
              f'itself. Your Cover of {cover} makes it cool '
              f'{cover / identity.COVER_DIVISOR * 100:.0f}% faster, because a '
              f'story that holds together is a file that stops growing.[/]')
    else:
        c.say('[dim]Heat cools on its own, at a rate each faction sets for '
              'itself. Guile would make it cool faster. You have none, so it '
              'cools at exactly the speed they are willing to forget.[/]')


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

#: Points of legwork quality per point of Guile, on the four kinds of legwork
#: that are a conversation. Presence decides what they see when you walk up;
#: this decides what happens after you open your mouth.
LEGWORK_PER_GUILE = 0.5

#: Legwork gated on how far into the drift you are. `floor` needs at least
#: that much Dissonance; `ceiling` stops working at or above it.
LEGWORK_DRIFT = {
    'resonance': ('floor', drift.RESONANCE_BAND),
    'employee': ('ceiling', drift.SOCIAL_FLOOR_BAND),
}


@command('legwork', 'Learn about the target before you go in.',
         contexts=('city',), group='prep', usage='legwork [perimeter|intel|employee|tap]',
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
    if gives == 'topology' and 'reads_the_floor' in game.char.riders():
        # A compositor reads a structure somebody chose for a living, and
        # a network is one. The shape costs them nothing to work out.
        cost = 0
    if cost > game.char.credits:
        raise CommandError(f'that costs {cost:,}c and you have '
                           f'{game.char.credits:,}c')
    game.char.credits -= cost

    stream = game.rng.fork('network', contract.cid)
    from ..run import network as net_mod
    net = net_mod.generate(stream, contract.target, int(contract.posture),
                           contract.objective, contract.size_mod)

    bonus = game.char.bonus('legwork_bonus')
    if gives == 'topology' and 'reads_the_floor' in game.char.riders():
        bonus += 2
    if key == 'resonance':
        bonus += 1  # you are not looking at it, you are listening to it
        c.blank()
        c.say(f'[accent2]{drift.RESONANCE_TEXT}[/]')
        c.blank()
    else:
        # Everything else here is asking people things, and how much people
        # tell you depends on who they think they are talking to, and on
        # whether there is anybody about to ask.
        bonus += appearance.social_bonus(game.char.presence)
        bonus += int(game.char.attr('guile') * LEGWORK_PER_GUILE)
        bonus += shifts.phase(game.city.phase).legwork
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
        from ..run import network as net_mod
        form = net_mod.SHAPES.get(net.shape, net.shape)
        return (f'{len(net.nodes)} hosts: {shape}. The shape of it: {form}. '
                f'Entry at [accent]{net.entry}[/].')
    if gives == 'ice':
        seen = {}
        for node in net.nodes.values():
            for construct in node.ice:
                seen[construct.data.name] = seen.get(construct.data.name, 0) + 1
        if not seen:
            return 'Their fixer laughs. There is almost nothing on it.'
        listed = ', '.join(f'{v}x {k}' for k, v in sorted(seen.items()))
        detail = f' Deepest sits on [accent]{net.objective_node}[/].' if bonus else ''
        # Who holds the doors on the way, and whether they would take
        # what you carry (D93): the thing corporate work turned on and
        # the one thing no read said.
        from ..run import network as net_mod
        walls = {uid for uid, node in net.nodes.items()
                 if net_mod._is_wall(node)}
        route = (net_mod._route(net, net.objective_node, avoid=walls)
                 or net_mod._route(net, net.objective_node))
        wardens = [(net.nodes[u], c) for u in route if u in net.nodes
                   for c in net.nodes[u].ice
                   if c.behaviour == 'warden' and c.alive]
        if wardens:
            desk = badge_read(game.char)
            parts = []
            for node, construct in wardens:
                takes = construct.data.effects.get('credential_check')
                parts.append(f'{construct.data.name} on [accent]{node.uid}[/]'
                             + (' takes credentials' if takes
                                else ' takes nothing'))
            answer = ('' if not any(c.data.effects.get('credential_check')
                                    for _, c in wardens)
                      else (' You have nothing they would take.'
                            if desk.impossible else
                            f' Yours read at {desk.chance:.0%} against the '
                            f'softest of them.'))
            detail += f' On the way in: {"; ".join(parts)}.{answer}'
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


def _advance(sess, shifts: int, story: bool = True) -> None:
    """Move time and report what the world did. Every shift-spending command
    routes through here so nothing can silently skip fallout."""
    game = sess.require_game()
    told = game.city.advance(
        game.rng, game.alias, shifts, debt=game.debt, char=game.char,
        satisfied=lambda rule: game.story.satisfied(rule, game),
        flags=game.story.flags, dead=_dead_cids(game),
        lender=game.debt.lender if game.debt.owed else '')
    for line in told:
        sess.console.say(line)
    # Scenery goes last and gets its own air. It is the one thing printed here
    # that is not about the player, and it only reads that way with a gap in
    # front of it.
    for line in game.city.ambient:
        sess.console.blank()
        sess.console.say(line)
    _rot(sess, shifts)
    _drift(sess)
    # The world moved, so any scene whose moment has come arrives now rather
    # than the next time you happen to look at somebody (D52). Travel asks
    # for it after the arrival instead (D91).
    if story:
        from .people import _check_story
        _check_story(sess)
    sess.record_progress()
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
             'component': hardware.BY_KEY, 'drug': drug_content.BY_KEY}
    return table[listing.kind].get(listing.key)


def _listing_detail(listing, item) -> str:
    if listing.kind == 'program':
        return (f'{item.category}, {item.memory}mem, r{item.rating}, '
                f'sig {item.signature:g}')
    if listing.kind == 'ware':
        return f'{item.location}, {item.bandwidth}bw, {item.dissonance}dis'
    if listing.kind == 'drug':
        return (f'{item.up} up, {item.down} down, '
                + ('no hook' if not item.hook else f'hook {item.hook}'))
    first = next(iter(item.effects.items()), None)
    return (f'{item.slot}: {SHORT_KEY.get(first[0], first[0])} '
            f'{_brief_value(*first)}' if first else f'{item.slot}')


#: Effect keys as the two or three words a table column has room for.
SHORT_KEY = {
    'memory': 'memory', 'heat_cap': 'heat cap', 'tick_mult': 'tick cost',
    'trace_mult': 'trace', 'noise_mult': 'noise', 'residue_mult': 'residue',
    'legwork_bonus': 'legwork', 'tempo': 'tempo', 'heat_mult': 'heat',
    'repair_mult': 'repairs', 'pretext_bonus': 'pretext',
}


def _brief_value(key: str, value) -> str:
    if key in fx.MULTIPLICATIVE:
        pct = (value - 1.0) * 100
        return f'{pct:+.0f}%'
    return f'{value:+g}'


def signature_word(sig: float) -> str:
    """Signature as a word (D63 c): the number is a multiplier on the noise
    a verb makes, and nobody new can feel a multiplier."""
    if sig <= 0:
        return 'silent, passive'
    if sig < 0.5:
        return 'near silent'
    if sig < 0.9:
        return 'quiet'
    if sig <= 1.1:
        return 'ordinary'
    if sig < 1.6:
        return 'loud'
    return 'deafening'


def find_item(query: str):
    """A catalogue item by key or name, any kind (D63 c). Returns
    (kind, item) or None; prefers an exact key, then an exact name, then a
    prefix, then a substring."""
    q = query.strip().lower()
    if not q:
        return None
    tables = (('program', programs.BY_KEY), ('ware', cyberware.BY_KEY),
              ('component', hardware.BY_KEY), ('drug', drug_content.BY_KEY))
    for kind, table in tables:
        if q in table:
            return kind, table[q]
    for kind, table in tables:
        for item in table.values():
            if item.name.lower() == q:
                return kind, item
    for kind, table in tables:
        for item in table.values():
            if item.name.lower().startswith(q) or item.key.startswith(q):
                return kind, item
    for kind, table in tables:
        for item in table.values():
            if q in item.name.lower():
                return kind, item
    return None


def describe_item(sess, kind: str, item) -> None:
    """Everything a player can know about a thing before they pay for it,
    load it, or have it put in them (D63 c). The market used to print a
    category and a rating beside a four-figure price; the blurb, the note,
    the numbers and the drawback were shown nowhere."""
    c = sess.console
    game = sess.game
    tier = f'tier {item.tier}' if hasattr(item, 'tier') else ''
    c.header(item.name, f'{kind}{", " + tier if tier else ""}')
    c.say(item.blurb)
    c.blank()
    rows = []
    if kind == 'program':
        what, verbs = programs.CATEGORIES.get(item.category, ('', ()))
        rows.append(('kind', f'{item.category} [dim]{what} '
                             f'({", ".join(verbs)})[/]'))
        rows.append(('memory', str(item.memory)))
        skill = programs.HELD_BY.get(item.category, '')
        held_note = ''
        if skill and game is not None:
            rank = game.char.skill(skill)
            eff = programs.held(item, rank)
            held_note = (f'; runs at {eff} for you ({skill.title()} {rank})'
                         if eff < item.rating else
                         f'; your {skill.title()} {rank} drives it in full')
        rows.append(('rating', f'{item.rating} [dim]counts double on a check, '
                               f'held to your skill + {programs.HELD_ABOVE}'
                               f'{held_note}[/]'))
        rows.append(('signature', f'{item.signature:g} [dim]'
                                  f'{signature_word(item.signature)}[/]'))
        if item.jobs:
            rows.append(('built for', ', '.join(item.jobs)))
    elif kind == 'ware':
        rows.append(('maker', item.maker))
        rows.append(('where', item.location))
        rows.append(('bandwidth', str(item.bandwidth)))
        rows.append(('dissonance', f'+{item.dissonance} [dim]and it stays[/]'))
    elif kind == 'component':
        rows.append(('slot', item.slot))
        rows.append(('heat', str(item.heat)))
    elif kind == 'drug':
        rows.append(('up', f'{item.up} shift{"s" if item.up != 1 else ""}'))
        rows.append(('down', f'{item.down} shift{"s" if item.down != 1 else ""}'))
        rows.append(('hook', 'none' if not item.hook else str(item.hook)))
    if getattr(item, 'unique', False):
        rows.append(('one of a kind', '[accent2]not sold anywhere[/]'))
    c.kv(rows)
    # the numbers, good and bad, under two headings
    good = getattr(item, 'effects', {}) or {}
    bad = getattr(item, 'penalty', {}) or {}
    if kind == 'drug':
        good, bad = item.high, item.crash
    if good:
        c.blank()
        c.raw('[ok]gives[/]' if kind != 'drug' else '[ok]while it is in you[/]')
        for key, value in good.items():
            c.say(f'  {fx.describe(key, value)}')
    if bad:
        c.raw('[err]costs[/]' if kind != 'drug' else '[err]when it turns[/]')
        for key, value in bad.items():
            c.say(f'  {fx.describe(key, value)}')
    if kind == 'drug' and item.withdrawal:
        c.raw('[err]without it, once your body expects it[/]')
        for key, value in item.withdrawal.items():
            c.say(f'  {fx.describe(key, value)}')
    note = getattr(item, 'note', '') or getattr(item, 'drawback', '')
    if note:
        c.blank()
        c.say(f'[warn]{note}[/]')
    lore = getattr(item, 'lore', '')
    if lore:
        c.blank()
        for para in lore.split('\n\n'):
            c.say(f'[accent2]{para}[/]')
            c.blank()
    # where it is, for you
    if game is not None:
        where = []
        char = game.char
        if kind == 'program':
            if item.key in char.deck.loaded:
                where.append('loaded')
            spare = char.library.count(item.key) - (1 if item.key in char.deck.loaded else 0)
            if spare > 0:
                where.append(f'in the bag{" x" + str(spare) if spare > 1 else ""}')
        elif kind == 'ware':
            if item.key in char.installed:
                where.append('fitted in you')
            if item.key in char.library:
                where.append('in the bag, not fitted')
        elif kind == 'component':
            if char.deck.parts.get(item.slot) == item.key:
                where.append('fitted in the deck')
            if item.key in char.library:
                where.append('in the bag')
        elif kind == 'drug':
            n = char.stash.get(item.key, 0)
            if n:
                where.append(f'{n} in the bag')
        for listing in game.city.listings():
            if listing.kind == kind and listing.key == item.key:
                price, _ = market_mod.quote(listing, game.city.where, game.alias,
                                            char.dissonance,
                                            char.mult('price_mult'),
                                            game.city.phase, char.attr('guile'))
                where.append(f'for sale here at [credit]{price:,}c[/]')
                break
        c.blank()
        c.say('[dim]' + ('; '.join(where) if where else 'not yours, and not '
                                                      'for sale here') + '.[/]')


@command('inspect', 'Everything about a thing: what it does, what it costs you.',
         group='info', aliases=('examine', 'what'), bare=True,
         usage='inspect <name|row number>',
         detail='Any program, chrome, component or drug, by name, by key, or '
                'by the row number of the last market, load or chrome list. '
                'The blurb, the numbers it gives and the numbers it takes, '
                'the note, and whether it is in your bag, on your deck, in '
                'you, or for sale here and at what. Before you buy, before '
                'you load, before you have it put in you.',
         complete=lambda sess, prefix: [
             i.key for table in (programs.BY_KEY, cyberware.BY_KEY,
                                 hardware.BY_KEY, drug_content.BY_KEY)
             for i in table.values()])
def cmd_inspect(sess, args) -> None:
    if not len(args):
        raise CommandError('inspect what? A name, a key, or a row number '
                           'from the last list.')
    token = args.rest().strip()
    if token.isdigit() and sess.game is not None:
        for kind in ('market', 'load', 'chrome', 'bag'):
            shown = sess.listed.get(kind)
            if shown and 1 <= int(token) <= len(shown):
                token = shown[int(token) - 1]
                break
    hit = find_item(token)
    if hit is None:
        raise CommandError(f'nothing in any catalogue is called {token!r}. '
                           f'`market`, `load`, `chrome` list what is around.')
    kind, item = hit
    describe_item(sess, kind, item)



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
            ('thinks of you', f'{rival.disposition:+d} [dim]{rival.band}[/]'
             + ({'nemesis': '  [err]your nemesis[/]',
                 'partner': '  [ok]your partner[/]'}.get(rival.bond, ''))),
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
         contexts=('city',), group='prep', usage='hire [name] [--confirm]',
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
            price = rival_world.hire_price(rival, game.story.flags)
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
    price = rival_world.hire_price(rival, game.story.flags)
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
         contexts=('city',), group='prep', usage='ask <name> <topic|favour>',
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

    if not len(args) or (len(args) == 1 and args[0].lower() != 'favours'):
        # Bare, or one word that is not a runner: who is here to ask and
        # what about. The favour table used to print for `ask` alone,
        # which is a different system answering a question about the
        # street (D86).
        from ..world import story as story_mod
        here = [n for n in story_mod.present(game, game.story)
                if n.key in game.story.met]
        if len(args) == 1:
            query = args[0].lower()
            if not any(query in r.name.lower() or query == r.key
                       or query == r.data.handle.lower() for r in pool):
                raise CommandError(f'nobody called {query!r}. `ask <name> '
                                   f'<topic>` for the people here, `ask '
                                   f'<runner> <favour>` for a colleague.')
        if here:
            c.header('Ask', game.city.district.name)
            c.kv([(n.key, f'[accent]{n.name}[/] [dim]on '
                          + ', '.join(sorted(n.topics)) + '[/]')
                  for n in here])
            c.blank()
        c.say('[dim]`ask <name> <topic>` asks one of them. `ask <runner> '
              '<favour>` calls in a favour from another runner: `who` lists '
              'them and `ask favours` prices it.[/]')
        if not here:
            c.say('[dim]Nobody you have met is here. `look`.[/]')
        return

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
        rows = [(r.data.handle, f'{r.disposition:+d}', r.band,
                 (f'{game.city.tabs[r.key][0]:,}c'
                  if r.key in game.city.tabs else ''))
                for r in pool if r.alive]
        c.table(('who', 'disposition', '', 'you owe'), rows,
                roles=('accent', None, 'dim', 'credit'))
        return

    query = args[0].lower()
    rival = next((r for r in pool
                  if query in r.name.lower() or query == r.key
                  or query == r.data.handle.lower()), None)
    if rival is None:
        raise CommandError(f'nobody called {query!r}')

    kind = args[1].lower()
    if 'repay'.startswith(kind) and len(kind) >= 3:
        _repay(sess, rival, args)
        return
    matches = [k for k in rival_content.FAVOURS if k.startswith(kind)]
    if len(matches) != 1:
        raise CommandError('which favour: '
                           + ', '.join(rival_content.FAVOURS) + ', repay')
    kind = matches[0]

    ok, why = rival_world.can_ask(rival, kind, game.char)
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


def _repay(sess, rival, args) -> None:
    """Pay a runner's tab down. Clearing it gives back half of what the
    favour cost in their opinion of you: they remember that you paid."""
    game, c = sess.game, sess.console
    owed, since = game.city.tabs.get(rival.key, [0, 0])
    if owed <= 0:
        raise CommandError(f'you do not owe {rival.name} anything.')
    amount = args.int_at(2, owed, 'an amount') if len(args) > 2 else owed
    amount = max(0, min(amount, owed, game.char.credits))
    if amount <= 0:
        raise CommandError(f'you owe {rival.name} {owed:,}c and have '
                           f'{game.char.credits:,}c.')
    game.char.credits -= amount
    left = owed - amount
    if left > 0:
        game.city.tabs[rival.key] = [left, since]
        c.ok(f'{amount:,}c to {rival.name}. [dim]{left:,}c still on the '
             f'tab.[/]')
        return
    del game.city.tabs[rival.key]
    back = rival_world.favour_cost('loan') // 2
    rival.adjust_disposition(back)
    c.ok(f'{amount:,}c to {rival.name}, and that is the tab cleared.')
    c.say(f'[dim]They remember that you paid. Disposition {rival.disposition:+d}.[/]')
    game.city.news.append(f'You cleared your tab with {rival.name}.')


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
        owed, since = game.city.tabs.get(rival.key, [0, game.city.shift])
        game.city.tabs[rival.key] = [owed + amount, game.city.shift]
        c.ok(f'[credit]{amount:,}c[/] from {rival.name}, on the '
             f'understanding that it is a loan.')
        c.say(f'[dim]They will mention it, every {city_mod.TAB_NAG} shifts '
              f'it stands, in front of people, and the mentioning is the '
              f'interest. `ask {rival.key} repay` when you can.[/]')
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


@command('crew', 'Somebody who runs with you, not somebody you rent.',
         contexts=('city',), group='prep',
         usage='crew [take <name>|drop]',
         detail='A hire is one job and cannot be lost. Somebody on a retainer '
                'comes in on every run, gets better at working specifically '
                'with you, takes a smaller cut than a hire does, and is '
                'standing next to you on the thirtieth run. They have to have '
                'decided you are worth it first, and they can die, and that '
                'is the entire reason this exists.')
def cmd_crew(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    verb = (args.get(0) or '').lower()
    crew = game.city.crew
    current = game.city.rival(crew.get('key', '')) if crew else None

    if verb in ('take', 'sign', 'hire'):
        _crew_take(sess, args)
        return
    if verb in ('drop', 'release', 'let'):
        _crew_drop(sess)
        return

    if current is not None and current.alive:
        runs = int(crew.get('runs', 0))
        bonus = rival_world.crew_bonus(runs)
        style, detail = rival_content.ALLY_SPECIALTY[current.data.style]
        c.header(current.name, 'yours')
        c.say(f'[dim]{current.data.manner}[/]')
        c.blank()
        c.kv([('style', f'{current.data.style}, {style}'),
              ('what that means', detail),
              ('runs together', str(runs)),
              ('skill', f'{current.data.skill}'
                        + (f' [ok]+{bonus} from working with you[/]'
                           if bonus else
                           f' [dim](+1 every '
                           f'{rival_content.CREW_RUNS_PER_STEP})[/]')),
              ('their cut', f'{int(rival_content.CREW_CUT * 100)}% of the '
                            f'haul'),
              ('how they feel', f'{current.disposition:+d} {current.band}')])
        c.blank()
        c.say('[dim]They come in on every run. `crew drop` to end it, which '
              'nobody takes well.[/]')
        return

    c.header('A crew', f'{game.char.credits:,}c')
    c.say('[dim]Somebody who works with you rather than for you, once. They '
          'have to have decided you are worth it.[/]')
    c.blank()
    rows = []
    for rival in game.city.rivals:
        ok, _ = rival_world.can_crew(rival)
        rows.append((rival.data.handle, rival.data.style,
                     f'{rival.disposition:+d} {rival.band}',
                     f'{rival_world.crew_retainer(rival):,}c' if ok
                     else '[err]not yet[/]'))
    c.table(('who', 'style', 'how they feel', 'retainer'), rows,
            roles=('accent', 'dim', 'dim', 'credit'))
    c.blank()
    c.say(f'[dim]They need {rival_content.CREW_AT:+d} disposition or better. '
          f'Work with them, cover them on an escort, and do not take jobs out '
          f'from under them. `crew take <name>`.[/]')


def _crew_take(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if game.city.crew:
        raise CommandError('you already have somebody. `crew drop` first, '
                           'and think about it.')
    query = args.rest(1).replace('--confirm', '').strip().lower()
    if not query:
        raise CommandError('take who on?')
    rival = next((r for r in game.city.rivals
                  if query in r.name.lower() or query == r.key
                  or query == r.data.handle.lower()), None)
    if rival is None:
        raise CommandError(f'nobody called {query!r}')
    ok, why = rival_world.can_crew(rival)
    if not ok:
        raise CommandError(why)
    price = rival_world.crew_retainer(rival)
    if not args.has('confirm'):
        c.header(rival.name, f'{price:,}c retainer')
        c.say(f'[dim]{rival.data.manner}[/]')
        c.blank()
        c.kv([('their cut', f'{int(rival_content.CREW_CUT * 100)}% of every '
                            f'haul, against {int(rival_world.HIRE_CUT * 100)}%'
                            f' for a hire'),
              ('they get better', f'+1 skill every '
                                  f'{rival_content.CREW_RUNS_PER_STEP} runs '
                                  f'together, to +'
                                  f'{rival_content.CREW_MAX_STEPS}'),
              ('they can die', 'yes, and it is permanent')])
        c.blank()
        c.say(f'[dim]`crew take {rival.data.handle.lower()} --confirm`.[/]')
        return
    if game.char.credits < price:
        raise CommandError(f'that is {price:,}c and you have '
                           f'{game.char.credits:,}c')
    game.char.credits -= price
    game.city.crew = {'key': rival.key, 'runs': 0}
    game.city.hired = ''
    line = rival_content.CREW_JOINED.get(rival.data.style, '{name} agrees.')
    c.blank()
    c.rule(rival.name, role='accent2')
    c.say(line.format(name=rival.name))
    c.blank()
    c.ok(f'{price:,}c. [dim]They are in on every run from here.[/]')
    sess.autosave()


def _crew_drop(sess) -> None:
    game, c = sess.require_game(), sess.console
    crew = game.city.crew
    rival = game.city.rival(crew.get('key', '')) if crew else None
    if rival is None:
        raise CommandError('there is nobody to let go.')
    runs = int(crew.get('runs', 0))
    game.city.crew = {}
    rival.adjust_disposition(-12 - min(20, runs))
    line = rival_content.CREW_RELEASED.get(rival.data.style,
                                           '{name} takes it.')
    c.blank()
    c.say(line.format(name=rival.name))
    c.say(f'[dim]{runs} run{"s" if runs != 1 else ""} together. '
          f'{rival.disposition:+d} with them now.[/]')
    sess.autosave()


@command('betray', 'Sell a runner\'s name to somebody who wants it.',
         contexts=('city',), group='prep', usage='betray <name> [buyer] [--confirm]',
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
         contexts=('city',), group='character', usage='clinic',
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
    word = (args.get(0) or '').lower()
    if word in ('ground', 'grounding', 'detox', 'habit'):
        # `clinic ground` reprinted the menu and said nothing (D96).
        raise CommandError('those are their own verbs here: `ground` walks '
                           'Dissonance back, `detox <drug>` takes a habit '
                           'off. `help ground`, `help detox`.')

    if args.opt('face') or args.has('face'):
        _reconstruct(sess, (args.opt('face') or '').lower(),
                     (args.get(0) or '').lower(), args.has('confirm'))
        return

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
                                        char.mult('price_mult'),
                                        game.city.phase,
                                        char.attr('guile'))
            rows.append((ware.name, ware.maker, ware.location,
                         f'{ware.bandwidth}bw {ware.dissonance}dis',
                         f'{price:,}c'))
        c.table(('chrome', 'made by', 'slot', 'costs you', 'price'), rows,
                roles=('accent', 'dim', 'dim', 'dim', 'credit'))

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
                                        char.mult('price_mult'),
                                        game.city.phase,
                                        char.attr('guile'))
            rows.append((ware.name, ware.maker, ware.location,
                         f'{ware.bandwidth}bw {ware.dissonance}dis',
                         f'{price:,}c'))
        c.table(('chrome', 'made by', 'slot', 'costs you', 'price'), rows,
                roles=('accent2', 'dim', 'dim', 'dim', 'credit'))
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
    c.rule('reconstruction')
    c.say('[dim]They will change what you were born with, for money and for '
          'time on a table. It does not come off your Dissonance; the body '
          'does not distinguish between chrome and a new jaw.[/]')
    c.blank()
    c.table(('feature', 'now', 'price', 'takes'),
            [(appearance.SLOT_BY_KEY[k].name,
              appearance.ALL_BY_KEY[(k, char.look[k])].name,
              f'{cost:,}c', f'{appearance.SURGERY_SHIFTS} shifts')
             for k, cost in appearance.SURGERY_COST.items() if cost],
            roles=('accent', 'dim', 'credit', 'dim'))
    c.say('[dim]`clinic --face <feature>` to see the options, '
          '`clinic --face <feature> <key> --confirm` to book it.[/]')

    c.blank()
    c.say('[dim]`buy <name>` here, `install <name>` to have it fitted, '
          '`uninstall <name>` to have it taken out.[/]')


def _reconstruct(sess, slot_key: str, choice: str,
                 confirmed: bool) -> None:
    """Change a feature you were born with. The expensive half of `self`.

    Deliberately costly in credits, in shifts, and in Dissonance. This is the
    escape hatch from a face somebody has circulated, and if it were cheap the
    two-sided design of memorability would collapse into "look striking, book
    surgery before anything goes wrong".
    """
    game, c = sess.game, sess.console
    char = game.char
    slot = appearance.SLOT_BY_KEY.get(slot_key)
    if slot is None:
        raise CommandError(
            f'no such feature: {slot_key!r}. They will work on: '
            f'{", ".join(k for k, v in appearance.SURGERY_COST.items() if v)}.')
    ok, why = appearance.can_change(slot_key)
    if not ok:
        raise CommandError(why)
    cost = appearance.SURGERY_COST[slot_key]

    if not choice:
        _look_options(sess, slot_key)
        c.blank()
        c.kv([('price', f'[credit]{cost:,}c[/]'),
              ('you have', f'[credit]{char.credits:,}c[/]'),
              ('takes', f'{appearance.SURGERY_SHIFTS} shifts'),
              ('costs you', f'{appearance.SURGERY_DISSONANCE} Dissonance')])
        c.say(f'[dim]`clinic --face {slot_key} <key> --confirm` to book it.[/]')
        return

    feature = appearance.BY_KEY.get((slot_key, choice))
    if feature is None:
        _look_options(sess, slot_key)
        raise CommandError(f'no {slot.name.lower()} called {choice!r}.')
    if char.look.get(slot_key) == feature.key:
        raise CommandError(f'that is already your {slot.name.lower()}.')
    if char.credits < cost:
        raise CommandError(f'{cost:,}c, and you have {char.credits:,}c.')

    if not confirmed:
        c.blank()
        c.rule(f'{slot.name}: {feature.name}', role='accent2')
        c.say(f'[dim]{slot.stem} {feature.look}.[/]')
        c.blank()
        after = dict(char.look)
        after[slot.key] = feature.key
        now = char.memorable
        then = appearance.score(after, char.marks,
                                char.dissonance
                                + appearance.SURGERY_DISSONANCE)[0]
        c.kv([('price', f'[credit]{cost:,}c[/]'),
              ('takes', f'{appearance.SURGERY_SHIFTS} shifts'),
              ('costs you', f'{appearance.SURGERY_DISSONANCE} Dissonance, '
                            f'permanently'),
              ('memorable', f'{now} [dim]to[/] {then} '
                            f'[accent]{appearance.band(then)[0]}[/]')])
        c.blank()
        c.warn('This is permanent and the Dissonance does not come back. '
               f'[dim]`clinic --face {slot.key} {feature.key} --confirm`[/]')
        return

    before = char.memorable
    char.credits -= cost
    char.look[slot.key] = feature.key
    char.dissonance += appearance.SURGERY_DISSONANCE
    c.blank()
    c.rule('reconstruction')
    c.say('[dim]Three shifts of somebody else deciding what you look like, '
          'and a week of not recognising the transition between rooms.[/]')
    c.blank()
    c.ok(f'{slot.name}: {feature.name}. [credit]{cost:,}c[/] gone.')
    after = char.memorable
    if after != before:
        c.info(f'Memorable {before} to {after}, '
               f'[accent]{char.memorable_band[0]}[/].')
    for passage in char.new_passages():
        c.blank()
        c.say(f'[residue]{passage.text}[/]')
    _advance(sess, appearance.SURGERY_SHIFTS)


@command('ground', 'Have your Dissonance walked back. Expensive and partial.',
         contexts=('city',), group='character', usage='ground [--confirm]',
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
         contexts=('city',), group='city', aliases=('owe',), usage='debt [pay <amount>|pay all]',
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
    # The debt's own terms, not the house ones. A Carrion loan runs at nearly
    # three times a Switchboard advance and the screen that tells you where
    # you stand has to be telling you about the one you actually took.
    rate, grace = owed.terms
    per_shift = int(owed.amount * rate)
    if shifts_in < grace:
        left = grace - shifts_in
        when = f'{left} shift{"s" if left != 1 else ""} before they call'
    elif owed.last_collected < 0:
        when = 'they are collecting'
    else:
        due = owed.last_collected + debt_mod.COLLECT_EVERY - game.city.shift
        when = (f'{max(0, due)} shifts to the next collection')
    rows = [('amount', f'[err]{owed.amount:,}c[/]'),
            ('to', f'{fac_short(owed.lender)}'),
            ('rate', f'{rate * 100:.1f}% a shift, compounding'
                     + (f'; collected in instalments of '
                        f'{owed.instalment:,}c' if owed.instalment else '')),
            ('growing by', f'[warn]{per_shift:,}c[/] a shift'),
            ('status', when),
            ('you have', f'[credit]{game.char.credits:,}c[/]')]
    c.kv(rows)
    c.blank()
    c.say('[dim]`debt pay <amount>` or `debt pay all`.[/]')


def fac_short(key: str) -> str:
    faction = factions.BY_KEY.get(key)
    return faction.short if faction else key or 'somebody'


@command('repair', 'Have the deck put back together. Needs a workshop.',
         contexts=('city',), group='character', usage='repair [--confirm]',
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

    if (args.get(0) or '').lower() == 'all' and not args.has('confirm'):
        # `repair all` reads as intent, not a question (D97).
        c.say('[dim]`repair all` is `repair --confirm`. Doing it.[/]')
    if not args.has('confirm') and (args.get(0) or '').lower() != 'all':
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


# --------------------------------------------------------------------------
# the bench
# --------------------------------------------------------------------------
#
# Not a crafting system. Nothing here produces an item, because a system that
# produced catalogue items for materials would be a discount on the market
# with extra steps and would make every price in the shop mean less. What it
# does is change a component you already own, permanently, in a direction
# nobody stocks, and charge for it in an axis you were relying on.


def _spare(game) -> list[tuple[str, str, int]]:
    """Everything you could break down: (key, kind, scrap it would give).

    The fitted deck and installed chrome are excluded. So is anything in the
    safehouse, which is somewhere else by definition.
    """
    from ..content import mods as mod_content
    out: list[tuple[str, str, int]] = []
    on_deck: dict[str, int] = {}
    for key in game.char.library:
        if key in programs.BY_KEY:
            # As the refusal text always said (D96): what is loaded is not
            # spare, copy for copy, so a second Crowbar in the bag is.
            if on_deck.get(key, 0) < game.char.deck.loaded.count(key):
                on_deck[key] = on_deck.get(key, 0) + 1
                continue
            item = programs.BY_KEY[key]
            out.append((key, 'program', mod_content.salvage_value(item.price)))
        elif key in hardware.BY_KEY:
            item = hardware.BY_KEY[key]
            out.append((key, 'component',
                        mod_content.salvage_value(item.price)))
        elif key in cyberware.BY_KEY:
            item = cyberware.BY_KEY[key]
            out.append((key, 'ware', mod_content.salvage_value(item.price)))
    # A destroyed component in the deck is still metal, and is otherwise a
    # repair bill you may not want to pay.
    for slot, key in game.char.deck.parts.items():
        if game.char.deck.damage.get(slot, 0) >= 3 and key in hardware.BY_KEY:
            out.append((key, 'wreck', mod_content.salvage_value(
                hardware.BY_KEY[key].price, broken=True)))
    return out


@command('salvage', 'Break something down for parts.',
         contexts=('city',), group='prep', usage='salvage [thing]',
         detail='Needs a workshop. Turns anything spare into scrap, which is '
                'what bench work is paid for besides money. The rate is bad '
                'on purpose: this is a use for things nobody will buy at a '
                'price worth the walk, not a way to turn money into a '
                'different currency. A destroyed component counts, and is '
                'often worth more in pieces than the repair costs.')
def cmd_salvage(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    from ..content import mods as mod_content
    if 'workshop' not in game.city.district.services:
        shops = ', '.join(d.name for d in districts.with_service('workshop'))
        raise CommandError(f'a bench is a workshop thing. Try: {shops}')
    spare = _spare(game)

    if not len(args):
        c.header('The bench', f'{game.char.scrap} scrap')
        if not spare:
            c.say(f'[dim]{mod_content.NOTHING_TO_SALVAGE}[/]')
            return
        c.table(('thing', 'what it is', 'scrap'),
                [(_thing_name(k), kind, str(v)) for k, kind, v in spare],
                roles=('accent', 'dim', 'credit'))
        c.blank()
        c.say('[dim]`salvage <thing>`. It does not come back. `mod` for what '
              'the scrap is for.[/]')
        return

    query = args.rest().lower()
    match = next(((k, kind, v) for k, kind, v in spare
                  if query in _thing_name(k).lower() or query == k), None)
    if match is None:
        raise CommandError(f'nothing spare like {query!r}. The fitted deck '
                           f'and what is installed in you do not count.')
    key, kind, value = match
    if kind == 'wreck':
        slot = hardware.BY_KEY[key].slot
        game.char.deck.parts.pop(slot, None)
        game.char.deck.damage.pop(slot, None)
    else:
        game.char.library.remove(key)
    game.char.deck.mods.pop(key, None)
    game.char.scrap += value
    c.ok(f'{_thing_name(key)} comes apart. [credit]+{value} scrap[/], '
         f'[dim]{game.char.scrap} in the bag.[/]')
    sess.autosave()


@command('mod', 'Bench work on a component you own.',
         contexts=('city',), group='prep', usage='mod [name] [--confirm]',
         detail='Needs a workshop. Every modification trades one axis for '
                'another on a specific component, permanently, and nothing '
                'here comes out ahead. The work is done to the metal, so '
                'selling the component sells the work with it, and no '
                'component carries more than two.')
def cmd_mod(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    from ..content import mods as mod_content
    char = game.char
    if 'workshop' not in game.city.district.services:
        shops = ', '.join(d.name for d in districts.with_service('workshop'))
        raise CommandError(f'bench work needs a workshop. Try: {shops}')

    if not len(args):
        c.header('Bench work', f'{char.scrap} scrap, {char.credits:,}c')
        if not char.scrap:
            # Said here because nothing else ever did (D90). Indented
            # wrong once, which hid the whole bench from anybody holding
            # scrap (D96).
            c.say('[dim]Scrap comes from `salvage <thing>`: a spare program, '
                  'a piece of chrome or a component in the bag comes apart '
                  'into it.[/]')
        for slot, comp in char.deck.components(include_broken=True):
            done = char.deck.mods.get(comp.key, [])
            head = f'  [accent]{comp.name}[/] [dim]{slot}[/]'
            if done:
                head += ('  [ok]'
                         + ', '.join(mod_content.BY_KEY[m].name
                                     for m in done) + '[/]')
            c.raw(head)
            room = mod_content.MAX_PER_COMPONENT - len(done)
            if room <= 0:
                c.say('[dim]There is nothing left of it to change.[/]',
                      indent='    ', subsequent='    ')
                continue
            for mod in mod_content.for_slot(slot):
                if mod.key in done:
                    continue
                c.say(f'[fg]{mod.key}[/] [dim]{mod.name}: '
                      f'{_effect_line(mod.gives)} [/][dim]for[/] '
                      f'{_effect_line(mod.takes)}[dim], {mod.scrap} scrap and '
                      f'{mod.price:,}c[/]',
                      indent='    ', subsequent='      ')
        c.blank()
        c.say(f'[dim]`mod <name>`. Two per component, and none of it comes '
              f'off.[/]')
        return

    words = [w for w in args.rest().split() if w != '--confirm']
    mod = mod_content.BY_KEY.get(words[0].lower()) if words else None
    if mod is None:
        raise CommandError('no bench work called that: '
                           + ', '.join(mod_content.MOD_KEYS))
    asked = words[1].lower() if len(words) > 1 else ''

    # Which component. One piece of work here fits every slot, so picking the
    # first one with something in it silently stripped the chassis off a CPU
    # when the player meant the cooling loop. Ambiguity is asked about.
    fits = [s for s in mod.slots if char.deck.component(s) is not None]
    if not fits:
        raise CommandError(f'{mod.name} is done to a '
                           f'{" or ".join(mod.slots)}, and you have nothing '
                           f'in there.')
    if asked:
        if asked not in fits:
            raise CommandError(f'{mod.name} goes on a '
                               f'{" or ".join(fits)}, not a {asked!r}.')
        fits = [asked]
    room = [s for s in fits
            if mod.key not in char.deck.mods.get(char.deck.parts[s], [])
            and len(char.deck.mods.get(char.deck.parts[s], []))
            < mod_content.MAX_PER_COMPONENT]
    if not room:
        full = ', '.join(char.deck.component(s).name for s in fits)
        raise CommandError(f'{full} has already had that done, or carries '
                           f'{mod_content.MAX_PER_COMPONENT} pieces of work '
                           f'and that is what is left of it.')
    if len(room) > 1:
        raise CommandError(
            f'{mod.name} fits your '
            + ', '.join(f'{s} ({char.deck.component(s).name})' for s in room)
            + f'. `mod {mod.key} <slot>`.')
    slot = room[0]
    comp = char.deck.component(slot)
    done = list(char.deck.mods.get(comp.key, []))
    if char.scrap < mod.scrap:
        raise CommandError(f'{mod.name} wants {mod.scrap} scrap and you have '
                           f'{char.scrap}. `salvage` something.')
    if char.credits < mod.price:
        raise CommandError(f'that is {mod.price:,}c and you have '
                           f'{char.credits:,}c')

    if not args.has('confirm'):
        c.header(mod.name, comp.name)
        c.say(f'[dim]{mod.blurb}[/]')
        c.blank()
        c.kv([('you get', _effect_line(mod.gives)),
              ('it costs', _effect_line(mod.takes)),
              ('and', f'{mod.scrap} scrap, [credit]{mod.price:,}c[/], '
                      f'{mod_content.BENCH_SHIFTS} shift')])
        c.blank()
        c.say(f'[warn]It does not come off, and it stays with the component '
              f'if you sell it.[/] [dim]`mod {mod.key} --confirm`.[/]')
        return

    char.scrap -= mod.scrap
    char.credits -= mod.price
    char.deck.mods.setdefault(comp.key, []).append(mod.key)
    c.blank()
    c.rule(mod.name)
    c.say(mod.bench)
    c.blank()
    c.ok(f'{comp.name} is not what it was.')
    c.say(f'[dim]{_effect_line(mod_content.effects(char.deck.mods[comp.key]))}'
          f'[/]')
    _advance(sess, mod_content.BENCH_SHIFTS)


# --------------------------------------------------------------------------
# somewhere of your own
# --------------------------------------------------------------------------


def _stashable(game) -> dict[str, str]:
    """Everything you could put in a safehouse, key to what kind it is.

    The loaded deck is deliberately excluded. Storing the program you are
    carrying and then walking into a network without it is a mistake the game
    should not be able to help you make silently.
    """
    out: dict[str, str] = {}
    for key in game.char.library:
        if key in programs.BY_KEY:
            out[key] = 'program'
        elif key in cyberware.BY_KEY:
            out[key] = 'ware'
    for key in game.char.stash:
        out[key] = 'drug'
    return out


def _thing_name(key: str) -> str:
    for table in (programs.BY_KEY, cyberware.BY_KEY, drug_content.BY_KEY):
        if key in table:
            return table[key].name
    return key


@command('safehouse', 'Somewhere of your own to keep things.',
         contexts=('city',), group='city', aliases=('house',),
         usage='safehouse [buy <key>|stash <thing>|take <thing>|money <n>]',
         detail='A place to put things and a place that can be found, which '
                'are the same half. What you pay for is security, not space: '
                'the cheap ones hold as much and are turned over much sooner. '
                'Nobody comes looking at all while the faction whose ground '
                'it is on has no interest in you, so being unknown is the '
                'best security in this game and it is free.')
def cmd_safehouse(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    from ..content import safehouses
    house = game.city.safehouse
    prop = safehouses.BY_KEY.get(house.get('key', '')) if house else None
    verb = (args.get(0) or '').lower()

    if verb == 'buy':
        _safehouse_buy(sess, args)
        return
    if prop is None or house.get('burned'):
        _safehouse_offers(sess)
        return
    if verb in ('stash', 'put'):
        _safehouse_move(sess, args, prop, into=True)
        return
    if verb in ('take', 'get'):
        _safehouse_move(sess, args, prop, into=False)
        return
    if verb == 'name':
        # Naming it (D62). A place you own is a place you call something.
        if prop is None or house.get('burned'):
            raise CommandError('you have nowhere of your own to name.')
        name = args.rest(1).strip()
        if not name:
            raise CommandError('safehouse name <what you call it>.')
        house['name'] = name[:32]
        c.ok(f'It is [accent]{house["name"]}[/] now, to you. To the city it '
             f'is still {prop.name}.')
        sess.autosave()
        return
    if verb == 'money':
        _safehouse_money(sess, args, prop)
        return

    attention = game.alias.attention(
        districts.BY_KEY[prop.where].controller)
    risk = safehouses.raid_chance(prop.security, attention)
    stored = list(house.get('stored') or [])
    c.header(house.get('name') or prop.name,
             (f'{prop.name}, ' if house.get('name') else '')
             + districts.BY_KEY[prop.where].name)
    c.say(f'[dim]{prop.blurb}[/]')
    c.blank()
    c.kv([
        ('security', f'{prop.security}/100'),
        ('their interest in you', f'{int(attention)}'),
        ('turned over', 'never' if not house.get('raids')
         else f'{house["raids"]} time'
              f'{"s" if house["raids"] != 1 else ""}'),
        ('risk a shift', 'none, nobody is looking' if risk <= 0
         else f'[warn]{risk * 100:.1f}%[/]'),
        ('holding', f'{len(stored)}/{safehouses.CAPACITY} things'),
        ('money in the floor', f'[credit]{int(house.get("credits", 0)):,}c[/]'),
    ])
    if stored:
        c.blank()
        for key in sorted(stored):
            c.raw(f'  [fg]{_thing_name(key)}[/]')
    c.blank()
    c.say('[dim]`safehouse stash <thing>`, `safehouse take <thing>`, '
          '`safehouse money <amount>` to put cash in or a negative amount to '
          'take it out.[/]')


def _safehouse_offers(sess) -> None:
    game, c = sess.require_game(), sess.console
    from ..content import safehouses
    burned = game.city.safehouse.get('burned')
    available = safehouses.here(game.city.where)
    c.header('Somewhere to keep things',
             districts.BY_KEY[game.city.where].name)
    if burned:
        c.say('[err]The last one is an address in somebody\'s file. You will '
              'not be going back to it.[/]')
        c.blank()
    if not available:
        somewhere = ', '.join(districts.BY_KEY[p.where].name
                              for p in safehouses.PROPERTIES)
        c.say(f'[dim]Nothing here. There is something in {somewhere}.[/]')
        return
    for prop in available:
        c.blank()
        c.raw(f'[accent]{prop.name}[/]  [credit]{prop.price:,}c[/]  '
              f'[dim]security {prop.security}[/]')
        c.say(f'[dim]{prop.blurb}[/]', indent='  ', subsequent='  ')
    c.blank()
    c.say(f'[dim]`safehouse buy {available[0].key}`. You get one.[/]')
    # The rest of the ladder, because a player in Marrow saw one room at
    # nine thousand eight hundred and concluded there was no home base
    # for the whole first week, with a floor cavity for a third of that
    # two districts away (D90). Price is security and nothing else.
    elsewhere = sorted((p for p in safehouses.PROPERTIES
                        if p.where != game.city.where),
                       key=lambda p: p.price)
    if elsewhere:
        c.blank()
        c.say('[dim]Elsewhere: ' + ', '.join(
            f'{p.name.lower()} in {districts.BY_KEY[p.where].name} at '
            f'{p.price:,}c (security {p.security})' for p in elsewhere)
            + '. They all hold the same; the price is how long before '
              'somebody looks in it.[/]', subsequent='  ')


def _safehouse_buy(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    from ..content import safehouses
    if game.city.safehouse and not game.city.safehouse.get('burned'):
        raise CommandError('you already have one. Somewhere of your own is '
                           'somewhere of your own.')
    key = (args.get(1) or '').lower()
    prop = safehouses.BY_KEY.get(key)
    if prop is None:
        raise CommandError('which one: '
                           + ', '.join(p.key for p in
                                       safehouses.here(game.city.where))
                           or 'nothing is for sale here')
    if prop.where != game.city.where:
        raise CommandError(f'{prop.name} is in '
                           f'{districts.BY_KEY[prop.where].name}.')
    if game.char.credits < prop.price:
        raise CommandError(f'{prop.name} is {prop.price:,}c and you have '
                           f'{game.char.credits:,}c')
    game.char.credits -= prop.price
    game.city.safehouse = {'key': prop.key, 'stored': [], 'credits': 0,
                           'raids': 0}
    c.blank()
    c.rule(prop.name)
    c.say(prop.arrival)
    c.blank()
    c.ok(f'{prop.price:,}c. [dim]`safehouse` for what it holds and what the '
         f'risk is.[/]')
    _advance(sess, 1)


def _safehouse_move(sess, args, prop, into: bool) -> None:
    game, c = sess.require_game(), sess.console
    from ..content import safehouses
    house = game.city.safehouse
    if prop.where != game.city.where:
        raise CommandError(f'{prop.name} is in '
                           f'{districts.BY_KEY[prop.where].name}, and so is '
                           f'everything in it.')
    query = args.rest(1).lower()
    if not query:
        raise CommandError('stash what?' if into else 'take what?')
    stored = list(house.get('stored') or [])

    if into:
        pool = _stashable(game)
        match = next((k for k in pool
                      if query in _thing_name(k).lower() or query == k), None)
        if match is None:
            raise CommandError(f'you are not carrying anything like '
                               f'{query!r}. The loaded deck does not count: '
                               f'take it off first.')
        if len(stored) >= safehouses.CAPACITY:
            raise CommandError(f'{prop.name} holds {safehouses.CAPACITY} '
                               f'things and it is holding them.')
        kind = pool[match]
        if kind == 'drug':
            game.char.stash[match] -= 1
            if game.char.stash[match] <= 0:
                del game.char.stash[match]
        else:
            game.char.library.remove(match)
        stored.append(match)
        house['stored'] = stored
        c.ok(f'{_thing_name(match)} is in the floor.')
    else:
        match = next((k for k in stored
                      if query in _thing_name(k).lower() or query == k), None)
        if match is None:
            raise CommandError(f'there is nothing like {query!r} in there.')
        stored.remove(match)
        house['stored'] = stored
        if match in drug_content.BY_KEY:
            game.char.stash[match] = game.char.stash.get(match, 0) + 1
        else:
            game.char.library.append(match)
        c.ok(f'{_thing_name(match)} is back in the bag.')
    sess.autosave()


def _safehouse_money(sess, args, prop) -> None:
    game, c = sess.require_game(), sess.console
    house = game.city.safehouse
    if prop.where != game.city.where:
        raise CommandError(f'the money is in '
                           f'{districts.BY_KEY[prop.where].name}.')
    amount = args.int_at(1, 0, 'an amount, or a negative one to take it out')
    held = int(house.get('credits', 0))
    if amount > 0:
        if amount > game.char.credits:
            raise CommandError(f'you have {game.char.credits:,}c')
        game.char.credits -= amount
        house['credits'] = held + amount
        c.ok(f'{amount:,}c under the boards. '
             f'[dim]{house["credits"]:,}c in there now.[/]')
    elif amount < 0:
        out = min(-amount, held)
        if not out:
            raise CommandError('there is nothing in there')
        house['credits'] = held - out
        game.char.credits += out
        c.ok(f'{out:,}c out. [dim]{house["credits"]:,}c left in there.[/]')
    else:
        raise CommandError('how much?')
    sess.autosave()


# --------------------------------------------------------------------------
# games of chance, and one of skill
# --------------------------------------------------------------------------


def _winnings(sess, venue, amount: int) -> None:
    """What taking money out of somebody's room does besides the money.

    The city remembers, which is the thesis, so a gambling system where the
    only thing that moved was a number in the account would be the one place
    it did not. Winning costs standing with whoever's room it was, and winning
    a *lot* costs anonymity, which is a real stat with real consequences.
    """
    game, c = sess.game, sess.console
    if amount <= 0:
        return
    lost_rep = games.REP_PER_THOUSAND * amount / 1000.0
    if lost_rep >= 0.5:
        game.alias.adjust_rep(venue.house, -lost_rep)
        c.say(f'[dim]{factions.BY_KEY[venue.house].short} think slightly '
              f'less of you than they did, in the way of people who have '
              f'just paid out.[/]')
    if amount >= games.MEMORABLE_AT:
        heat = games.HEAT_PER_WIN * amount / 1000.0
        game.alias.add_heat(venue.house, heat)
        c.blank()
        c.warn('That was enough money that everybody in the room now knows '
               'your face, and one of them is already describing it to '
               'somebody who was not here.')


@command('dice', 'Ninepins. Two dice, a sixth of every stake, no secrets.',
         contexts=('city',), group='city', usage='dice [stake] [high|low|seven]',
         detail='Two dice. High is 8 to 12, low is 2 to 6, and seven belongs '
                'to the house, which is the whole edge and it is painted on '
                'the wall. Costs no time. With no arguments it prints the '
                'odds, which are the same odds it will still be printing '
                'after you have lost.')
def cmd_dice(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    rooms = games.here(game.city.where, game.city.district.services, 'dice')
    if not rooms:
        where = ', '.join(sorted({districts.BY_KEY[v.where].name
                                  for v in games.VENUES if v.game == 'dice'}))
        raise CommandError(f'nobody is playing dice in '
                           f'{game.city.district.name}. Try {where}.')
    venue = rooms[0]

    if not len(args):
        c.header('Ninepins', venue.name)
        c.say(f'[dim]{venue.arrival}[/]')
        c.blank()
        c.say(f'[dim]{venue.pitch}[/]')
        c.blank()
        c.table(('call', 'wins on', 'pays', 'chance', 'the house keeps'),
                [(call, _spread(totals), f'{pays}:1',
                  f'{games.odds(call) * 100:.1f}%',
                  f'{games.edge(call) * 100:.1f}%')
                 for call, (totals, pays) in games.CALLS.items()],
                roles=('accent', 'dim', 'credit', 'info', 'err'))
        c.blank()
        c.say(f'[dim]`dice <stake> <call>`, between {games.MIN_STAKE} and '
              f'{games.MAX_STAKE:,}c. You have '
              f'[credit]{game.char.credits:,}c[/][dim].[/]')
        return

    stake = args.int_at(0, 0, 'a stake')
    call = (args.get(1) or '').lower()
    if call not in games.CALLS:
        raise CommandError('call it: ' + ', '.join(games.CALLS))
    if stake < games.MIN_STAKE:
        raise CommandError(f'the table does not get out of bed for less than '
                           f'{games.MIN_STAKE}c')
    if stake > games.MAX_STAKE:
        raise CommandError(f'{games.MAX_STAKE:,}c is the most this room will '
                           f'cover')
    if stake > game.char.credits:
        raise CommandError(f'you have {game.char.credits:,}c')

    stream = game.rng('games')
    a, b = games.roll_total(stream)
    total = a + b
    won = total in games.CALLS[call][0]
    payout = stake * games.CALLS[call][1]

    c.blank()
    c.raw(f'  [accent]{a}[/] [dim]and[/] [accent]{b}[/] '
          f'[dim]{c.caps.g("arrow")} {total}[/]')
    c.blank()
    if won:
        game.char.credits += payout
        c.ok(f'{call.title()}. [credit]+{payout:,}c[/].')
        c.say(f'[dim]{stream.pick(games.DICE_WIN)}[/]')
        _winnings(sess, venue, payout)
    else:
        game.char.credits -= stake
        c.err(f'Not {call}. [err]-{stake:,}c[/].')
        c.say(f'[dim]{stream.pick(games.DICE_LOSS)}[/]')
        _broke_hint(sess)


def _spread(totals: tuple[int, ...]) -> str:
    if len(totals) == 1:
        return str(totals[0])
    return f'{min(totals)} to {max(totals)}'


def _broke_hint(sess) -> None:
    """Said once you have nothing, by the room, which knows what comes next."""
    game, c = sess.game, sess.console
    if game.char.credits > 200 or game.debt.owed:
        return
    available = lenders.here(game.city.where, game.city.district.services)
    c.blank()
    if available:
        c.say(f'[heat]Somebody at the back has been watching you lose and '
              f'would like you to know that {available[0].name} is here and '
              f'is not busy.[/] [dim]`borrow`.[/]')
    else:
        c.say('[dim]That is most of what you had. `borrow` where somebody '
              'lends, which is Marrow, the Ninth, or the Shambles.[/]')


@command('cards', 'Threes. One hand an evening, and it is not about the cards.',
         contexts=('city',), group='city', usage='cards [stake]',
         detail='Resolved on Guile and Subterfuge against the table rather '
                'than on what you were dealt, and it is the one game in the '
                'city a social build can genuinely beat. Costs a shift, '
                'because it is an evening. Prints the exact odds before you '
                'commit, and how well you read them decides the payout.')
def cmd_cards(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    char = game.char
    rooms = games.here(game.city.where, game.city.district.services, 'cards')
    if not rooms:
        where = ', '.join(sorted({districts.BY_KEY[v.where].name
                                  for v in games.VENUES if v.game == 'cards'}))
        raise CommandError(f'there is no game in {game.city.district.name}. '
                           f'Try {where}.')
    venue = rooms[0]
    check = _threes_check(char, venue, game.city.tables.get(venue.key, 0))
    if not len(args):
        c.header('Threes', venue.name)
        c.say(f'[dim]{venue.arrival}[/]')
        c.blank()
        c.say(f'[dim]{venue.pitch}[/]')
        c.blank()
        c.say(f'Reading this table: {check.summary()}')
        c.say(check.explain(), indent='  ')
        c.blank()
        c.say(f'[dim]`cards <stake>`, between {games.THREES_MIN} and '
              f'{games.THREES_MAX:,}c. It costs a shift. Pays up to '
              f'{games.THREES_PAYOUT[0][1]:.0f} times the stake if you read '
              f'them completely.[/]')
        return

    if check.chance < games.THREES_FLOOR:
        raise CommandError(
            f'they will not take your money. Threes is a reading game and '
            f'you cannot read this table: {check.summary()}. `dice` is the '
            f'one that needs nothing but a stake.')
    stake = args.int_at(0, 0, 'a stake')
    if stake < games.THREES_MIN:
        raise CommandError(f'the table plays for {games.THREES_MIN}c or more')
    if stake > games.THREES_MAX:
        raise CommandError(f'{games.THREES_MAX:,}c is more than this table '
                           f'will see in a night')
    if stake > char.credits:
        raise CommandError(f'you have {char.credits:,}c')

    # D63 d: the table watches a big hand more closely. Rebuilt with the
    # stake now that there is one; the odds printed above were for sitting
    # down, and `cards <stake>` prints these.
    check = _threes_check(char, venue, game.city.tables.get(venue.key, 0), stake)
    stream = game.rng('games')
    check.resolve(stream)
    c.blank()
    c.rule('threes')
    if check.success:
        multiple = next(m for margin, m in games.THREES_PAYOUT
                        if check.margin >= margin)
        payout = int(stake * multiple)
        char.credits += payout
        game.city.tables[venue.key] = (
            game.city.tables.get(venue.key, 0) + payout)
        c.ok(f'You take it. [credit]+{payout:,}c[/] '
             f'[dim]({multiple:.0f}x, margin {check.margin})[/]')
        c.say(f'[dim]{stream.pick(games.THREES_WIN)}[/]')
        _winnings(sess, venue, payout)
    else:
        char.credits -= stake
        # Losing buys some of your anonymity back. They have not learned how
        # you play; they have learned that they were wrong about you.
        game.city.tables[venue.key] = max(
            0, game.city.tables.get(venue.key, 0) - stake)
        c.err(f'They had you. [err]-{stake:,}c[/]')
        c.say(f'[dim]{stream.pick(games.THREES_LOSS)}[/]')
        c.say(check.explain())
        _broke_hint(sess)
    _advance(sess, games.THREES_SHIFTS)


def _threes_check(char, venue, taken: int, stake: int = 0):
    """Reading a table, itemised, per D14. The same shape as every other check.

    Deliberately built from the social half of a character sheet and nothing
    else. Threes is the one place Guile is the point rather than a discount,
    and a table you can beat with Intrusion would make it a second lockpick.
    """
    from ..run.checks import Check
    table = int(factions.BY_KEY[venue.house].posture)
    check = Check(name='read the table',
                  resistance=games.THREES_RESISTANCE + table // 8)
    check.add('guile', char.attr('guile') * 2)
    check.add('subterfuge', char.skill('subterfuge') * 2)
    check.add('gear', char.bonus('pretext_bonus'))
    # The house notices. Winning costs standing with them, and standing below
    # zero is the table having worked out how you play, itemised here so a
    # player watching their odds fall can see exactly what is doing it.
    learned = min(games.THREES_LEARNS_MAX,
                  int(taken // games.THREES_LEARNS_PER))
    if learned:
        check.add('they have learned how you play', -learned)
    if stake >= games.THREES_PER_STAKE:
        check.add('the size of the stake', -(stake // games.THREES_PER_STAKE))
    if 'no_social' in char.riders():
        check.add('a process cannot read a room', -8)
    return check


# --------------------------------------------------------------------------
# borrowing
# --------------------------------------------------------------------------


@command('borrow', 'Take money off somebody who will want it back.',
         contexts=('city',), group='city', usage='borrow [amount] [--confirm]',
         detail='With no argument: who lends here, how much they will give '
                'you, on what terms, and what they said about not being '
                'repaid. You can owe exactly one person at a time. The rate '
                'compounds every shift and the grace period is counted from '
                'the day you took it, not from the day you stopped paying.')
def cmd_borrow(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    char, city = game.char, game.city
    available = lenders.here(city.where, city.district.services)

    if not available:
        somewhere = ', '.join(
            f'{districts.BY_KEY[x.where].name} ({x.name})'
            for x in lenders.LENDERS)
        raise CommandError(f'nobody lends money in {city.district.name}. '
                           f'{somewhere}.')
    lender = available[0]
    rep = game.alias.reputation(lender.key)
    ceiling = lenders.limit(lender, rep, char.runs,
                            game.debt.amount if game.debt.owed else 0)

    if not len(args):
        c.header(lender.name, f'{factions.BY_KEY[lender.key].short}')
        c.say(f'[dim]{lender.offer}[/]')
        c.blank()
        c.kv([
            ('will lend', f'[credit]{ceiling:,}c[/]' if ceiling
                          else '[err]nothing[/]'),
            ('rate', f'{lender.rate * 100:.1f}% a shift, compounding'),
            ('grace', f'{lender.grace} shifts before they come round'),
            ('standing', f'{rep:+d} with {factions.BY_KEY[lender.key].short}'),
        ])
        c.blank()
        c.say(f'[warn]{lender.warning}[/]')
        if game.debt.owed:
            c.blank()
            c.warn(f'You already owe {game.debt.amount:,}c to '
                   f'{factions.BY_KEY[game.debt.lender].short}. Nobody here '
                   f'lends to somebody else\'s problem.')
        elif ceiling:
            c.blank()
            c.say(f'[dim]`borrow <amount>` to take some. It compounds from '
                  f'the shift you take it.[/]')
        return

    if game.debt.owed:
        raise CommandError(
            f'you owe {factions.BY_KEY[game.debt.lender].short} '
            f'{game.debt.amount:,}c. Clear it before anybody else will talk '
            f'to you: `debt pay all`.')
    if not ceiling:
        c.blank()
        c.say(f'[err]{lenders.NOTHING[lender.key]}[/]')
        return

    amount = args.int_at(0, 0, 'an amount to borrow')
    if amount <= 0:
        raise CommandError('borrow how much?')
    if amount > ceiling:
        c.blank()
        c.say('[warn]'
              + lenders.REFUSALS[lender.key].format(limit=ceiling) + '[/]')
        return
    if not args.has('confirm'):
        # What it becomes, not what it is. The number people agree to is the
        # one they are handed, and the number that ruins them is the one
        # eighteen shifts later, and printing only the first is how a debt
        # mechanic becomes a surprise instead of a decision.
        later = amount
        for _ in range(lender.grace):
            later = int(round(later * (1.0 + lender.rate)))
        c.warn(f'{amount:,}c now. By the time the grace period is up, in '
               f'{lender.grace} shifts, it is {later:,}c.')
        c.say(f'[dim]{lender.warning}[/]')
        c.say(f'[dim]`borrow {amount} --confirm` to take it.[/]')
        return

    char.credits += amount
    game.debt = debt_mod.Debt(
        amount=amount, lender=lender.key, opened=city.shift,
        note=lender.name, rate=lender.rate, grace=lender.grace)
    c.blank()
    c.rule('borrowed')
    c.say(lender.handover)
    c.blank()
    c.kv([('taken', f'[credit]{amount:,}c[/]'),
          ('from', f'{lender.name}, {factions.BY_KEY[lender.key].short}'),
          ('rate', f'{lender.rate * 100:.1f}% a shift'),
          ('grace', f'{lender.grace} shifts')])
    c.blank()
    c.say('[dim]`debt` for where it stands. It grows every shift, including '
          'the ones you spend asleep.[/]')


# --------------------------------------------------------------------------
# chemistry
# --------------------------------------------------------------------------


def _effect_line(effects: dict) -> str:
    """A modifier block as something readable, signed, in the game's roles."""
    if not effects:
        return '[dim]nothing[/]'
    out = []
    for key, value in sorted(effects.items()):
        if key in fx.MULTIPLICATIVE:
            pct = int(round((value - 1.0) * 100))
            if not pct:
                continue
            role = 'ok' if fx.improves(key, value) else 'err'
            out.append(f'[{role}]{key} {pct:+d}%[/]')
        else:
            n = int(round(value))
            if not n:
                continue
            out.append(f'[{"ok" if n > 0 else "err"}]{key} {n:+d}[/]')
    return '  '.join(out) or '[dim]nothing[/]'


@command('chem', 'What is in you, what is leaving, and what you now need.',
         contexts=('any',), group='character', aliases=('drugs',),
         usage='chem [drug]',
         detail='With no argument: what you are carrying, what is active, and '
                'how deep any habit has got. With one: everything that drug '
                'does to you, both halves, at your current tolerance. Costs '
                'nothing and is safe to ask at any point.')
def cmd_chem(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    char = game.char
    state = drug_content.normalise(char.chem)

    if len(args):
        drug = drug_content.find(args.rest())
        if drug is None:
            raise CommandError(f'nothing called {args.rest()!r}')
        level = state['habit'].get(drug.key, 0)
        c.header(drug.name, f'{drug.price:,}c list')
        c.say(f'[dim]{drug.blurb}[/]')
        c.blank()
        c.kv([
            ('up', f'{drug.up} shift{"s" if drug.up != 1 else ""}  '
                   + _effect_line(drug_content._scaled(
                       drug.high, drug_content.tolerance(level)))),
            ('down', f'{drug.down} shift{"s" if drug.down != 1 else ""}  '
                     + _effect_line(drug_content._scaled(
                         drug.crash, drug_content.severity(level)))),
            ('hook', 'none' if not drug.hook else f'+{drug.hook} a dose'),
            ('habit', f'{level} [dim]({drug_content.depth(level)})[/]'),
        ])
        if drug.withdrawal:
            c.blank()
            c.say(f'[dim]Once your body expects it, which is habit '
                  f'{drug_content.WITHDRAWAL_AT}, not having it costs you: [/]'
                  + _effect_line(drug.withdrawal))
        if drug.cures_crash:
            c.blank()
            c.say('[warn]It clears every comedown in progress, and every '
                  'drug it clears gains a habit point. On something already '
                  'at three, the cure is the habit.[/]')
        return

    carrying = {k: v for k, v in char.stash.items() if v > 0}
    c.header('Chemistry', 'clean' if not (state['up'] or state['down']
                                          or state['habit']) else '')
    if state['up']:
        for key, left in sorted(state['up'].items()):
            c.raw(f'  [ok]{drug_content.BY_KEY[key].name}[/] [dim]up, {left} '
                  f'shift{"s" if left != 1 else ""} left[/]')
    if state['down']:
        for key, left in sorted(state['down'].items()):
            c.raw(f'  [err]{drug_content.BY_KEY[key].name}[/] [dim]coming '
                  f'down, {left} shift{"s" if left != 1 else ""} left[/]')
    for key in drug_content.withdrawing(char.chem):
        c.raw(f'  [heat]{drug_content.BY_KEY[key].name}[/] '
              f'[dim]not in you, and your body has noticed[/]')

    if state['habit']:
        c.blank()
        c.say('[dim]Habit:[/]')
        for key, level in sorted(state['habit'].items(),
                                 key=lambda kv: -kv[1]):
            role = ('err' if level >= 7 else 'warn'
                    if level >= drug_content.WITHDRAWAL_AT else 'dim')
            c.raw(f'  [{role}]{drug_content.BY_KEY[key].name:<24}[/] '
                  f'[dim]{level}/{drug_content.HABIT_MAX}, '
                  f'{drug_content.depth(level)}[/]')

    net = drug_content.effects(char.chem)
    if net:
        c.blank()
        c.say('[dim]Right now, all of it together:[/] ' + _effect_line(net))

    c.blank()
    if carrying:
        c.say('[dim]In the bag:[/] ' + ', '.join(
            f'[fg]{drug_content.BY_KEY[k].name}[/] x{v}'
            for k, v in sorted(carrying.items())))
    else:
        c.say('[dim]Nothing in the bag. Clinics, fences and markets deal, and '
              'not in the same things.[/]')
    c.say('[dim]`chem <drug>` for what one of them does. `dose <drug>` to '
          'take it.[/]')


@command('dose', 'Take something. It works, and then it stops working.',
         contexts=('any',), group='character', usage='dose <drug>',
         complete=lambda sess, prefix: [
             k for k in (sess.game.char.stash if sess.game else {})],
         detail='Works out here and inside a run alike, and inside a run it '
                'costs a tick. The high is shorter than the comedown and the '
                'comedown is worse than the high was good, every time, for '
                'everything. What you are buying is when the bill arrives, '
                'not whether.')
def cmd_dose(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    char = game.char
    if not len(args):
        carrying = {k: v for k, v in char.stash.items() if v > 0}
        if not carrying:
            raise CommandError('you are not carrying anything. `market drug` '
                               'where somebody deals.')
        raise CommandError('dose what: ' + ', '.join(sorted(carrying)))
    drug = drug_content.find(args.rest())
    if drug is None:
        raise CommandError(f'nothing called {args.rest()!r}')
    if char.stash.get(drug.key, 0) <= 0:
        raise CommandError(f'you have no {drug.name}.')
    if drug_content.is_up(char.chem, drug.key):
        raise CommandError(f'{drug.name} is already in you. A second one on '
                           f'top of the first does nothing the first is not '
                           f'already doing.')

    before = drug_content.habit(char.chem, drug.key)
    if (drug.hook >= drug_content.WITHDRAWAL_AT and before == 0
            and not args.has('sure')):
        # D63 d: said before the dose, not after. One dose of this is a
        # habit, and the only warning used to come with the habit.
        raise CommandError(
            f'one dose of {drug.name} is a habit: hook {drug.hook}, and '
            f'{drug_content.WITHDRAWAL_AT} is where your body starts keeping '
            f'its own accounts. `dose {drug.key} --sure` if you mean it.')
    was_down = set(drug_content.normalise(char.chem)['down'])
    char.stash[drug.key] -= 1
    if char.stash[drug.key] <= 0:
        del char.stash[drug.key]
    char.chem = drug_content.dose(char.chem, drug.key)
    after = drug_content.habit(char.chem, drug.key)
    if drug.cures_crash and was_down:
        # What the cure cost the other habits, named, because the one it
        # tips over into withdrawal is the one you will not see coming.
        now = drug_content.normalise(char.chem)
        for other in sorted(was_down):
            level = now['habit'].get(other, 0)
            name = drug_content.BY_KEY[other].name if other in drug_content.BY_KEY else other
            role = 'err' if level >= drug_content.WITHDRAWAL_AT else 'dim'
            c.say(f'[{role}]{name}: comedown cleared, habit now {level}'
                  + (' and that is withdrawal territory'
                     if level >= drug_content.WITHDRAWAL_AT else '') + '.[/]')

    c.blank()
    c.say(f'[accent]{drug.onset}[/]')
    c.blank()
    c.kv([('for', f'{drug.up} shift{"s" if drug.up != 1 else ""}'),
          ('then', f'{drug.down} shift{"s" if drug.down != 1 else ""} of '
                   'coming down')])
    if after > before:
        # Said at the moment it changes, every time, because the number going
        # up one at a time is the only warning this system gives.
        role = 'err' if after >= drug_content.WITHDRAWAL_AT else 'dim'
        c.say(f'[{role}]Habit {before} to {after}. '
              f'{drug_content.depth(after)}.[/]')
    if after == drug_content.WITHDRAWAL_AT and before < after:
        c.blank()
        c.warn('That is the one where your body starts keeping its own '
               'accounts. From here, not having it is its own condition.')
    if sess.run is not None:
        from .run import _act
        _act(sess, 'mask', noise_scale=0.0, ticks=1)


@command('detox', 'Have a habit taken off you. Expensive, slow, and partial.',
         contexts=('city',), group='character', usage='detox [drug] [--confirm]',
         detail='Needs a clinic. Buys back habit points for money and shifts, '
                'the same shape as `ground`, and like `ground` it does not '
                'undo what the using already cost. Time and abstinence do the '
                'same job for free, which is the point of the price.')
def cmd_detox(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    char = game.char
    if 'clinic' not in game.city.district.services:
        raise CommandError('a detox needs a clinic.')
    state = drug_content.normalise(char.chem)
    if not state['habit']:
        raise CommandError('there is nothing on you to take off.')

    if len(args) and not args.has('confirm'):
        drug = drug_content.find(args.get(0))
        if drug is None:
            raise CommandError(f'nothing called {args.get(0)!r}')
        target = drug.key
    else:
        target = max(state['habit'], key=lambda k: state['habit'][k])
    level = state['habit'].get(target, 0)
    if level <= 0:
        raise CommandError(f'you have no habit for '
                           f'{drug_content.BY_KEY[target].name}.')

    cost = DETOX_COST + DETOX_PER_POINT * level
    if not args.has('confirm'):
        c.warn(f'{cost:,}c and {DETOX_SHIFTS} shifts, for '
               f'{DETOX_POINTS} points off your '
               f'{drug_content.BY_KEY[target].name} habit.')
        c.say('[dim]Five clean shifts does one point for nothing at all. You '
              'are paying for the ones you would have spent wanting it. '
              '`detox --confirm`.[/]')
        return
    if char.credits < cost:
        raise CommandError(f'that is {cost:,}c and you have '
                           f'{char.credits:,}c')

    char.credits -= cost
    state['habit'][target] = max(0, level - DETOX_POINTS)
    if not state['habit'][target]:
        del state['habit'][target]
    # Nothing is in you afterwards, which means the comedown is also gone,
    # which is most of what the money bought.
    state['down'].pop(target, None)
    state['up'].pop(target, None)
    char.chem = state
    hurt = game.rng('events').int(*DETOX_HURT)
    char.hurt = min(char.integrity_max - 1, char.hurt + hurt)

    c.blank()
    c.rule('detox')
    c.say(DETOX_TEXT)
    c.blank()
    c.kv([('habit', f'{level} -> [accent]'
                    f'{drug_content.habit(char.chem, target)}[/]'),
          ('cost', f'[credit]{cost:,}c[/]'),
          ('damage', f'[err]{hurt}[/] integrity')])
    _advance(sess, DETOX_SHIFTS)


#: What a clinic charges to take a habit off you, and what it costs in the
#: other two currencies. Priced against `ground`: a habit is cheaper to walk
#: back than Dissonance because it is not permanent, and it still costs more
#: than most contracts pay, because the free version is five shifts of wanting
#: it and the price is the price of skipping those.
DETOX_COST = 1800
DETOX_PER_POINT = 450
DETOX_POINTS = 3
DETOX_SHIFTS = 3
DETOX_HURT = (1, 3)
DETOX_TEXT = (
    'It is four rooms with a nurse walking between them and a chair with arm '
    'straps that nobody mentions and nobody removes. They are kind about it '
    'in the specific way of people who are kind about this eleven times a '
    'week. Somewhere around the second shift you stop negotiating.'
)


@command('trait', 'What you are like. Permanent, and there are never enough '
                  'slots.',
         contexts=('city',), group='character', aliases=('traits',),
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


# --------------------------------------------------------------------------
# appearance
# --------------------------------------------------------------------------


def _look_options(sess, slot_key: str) -> None:
    """Every feature in one slot, with what it costs you socially."""
    game, c = sess.game, sess.console
    slot = appearance.SLOT_BY_KEY[slot_key]
    worn = game.char.look.get(slot_key)
    c.header(slot.name, 'set at creation' if slot.fixed else 'change freely')
    c.say(f'[dim]{slot.blurb}[/]')
    c.blank()
    rows = []
    for feature in appearance.BY_SLOT[slot_key]:
        rows.append((
            ('[ok]*[/]' if feature.key == worn else ''),
            feature.key, feature.name,
            _signed(feature.memorable), _signed(feature.presence)))
    c.table(('', 'key', 'name', 'memorable', 'presence'), rows,
            roles=(None, 'dim', 'accent', None, None))
    c.blank()
    if slot.fixed:
        c.say('[dim]Changing this one is surgery. A clinic will quote you.[/]')
    else:
        c.say(f'[dim]`self --set {slot_key} <key>` to change it.[/]')


def _signed(n: int) -> str:
    if not n:
        return '[dim]0[/]'
    role = 'warn' if n > 0 else 'ok'
    return f'[{role}]{n:+d}[/]'


@command('self', 'What you look like, and what it costs you.',
         contexts=('city',), group='character',
         aliases=('appearance',),
         usage='self [slot] [--set <slot> <key>] [--roll]',
         detail='Appearance is the seventh way to build a character and the '
                'only one about the meat. Every feature moves two numbers. '
                'Memorable is how easily somebody could describe you '
                'afterwards: it earns more reputation per job and converts '
                'more of what you leave behind into faction heat, so it is a '
                'real trade rather than a slider. Presence is how much weight '
                'you carry in a conversation, and feeds every social check in '
                'the city.\n\n'
                'Four features are set at creation and only a clinic changes '
                'them. Four are yours to change whenever you like. Marks are '
                'neither: you do not choose those, they accumulate.')
def cmd_self(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    char = game.char

    if args.has('roll'):
        char.look.update(appearance.roll(game.rng('appearance'),
                                         appearance.FREE_SLOTS))
        c.ok('You have changed what you can change.')
        c.blank()
        sess.autosave()
    elif args.opt('set') or (args.get(0) == 'set'):
        # Both `self --set dress corporate` and `self set dress corporate`
        # reach here; the option parser splits them differently.
        if args.opt('set'):
            slot_key, value = args.opt('set').lower(), args.get(0) or ''
        else:
            slot_key, value = (args.get(1) or '').lower(), args.get(2) or ''
        slot = appearance.SLOT_BY_KEY.get(slot_key)
        if slot is None:
            raise CommandError(
                f'no such feature: {slot_key!r}. '
                f'One of: {", ".join(appearance.SLOT_KEYS)}.')
        if slot.fixed:
            raise CommandError(
                f'{slot.name} is not something you change with a decision. '
                f'A clinic can do it for money: `clinic --face {slot_key}`.')
        feature = appearance.BY_KEY.get((slot_key, value.lower()))
        if feature is None:
            _look_options(sess, slot_key)
            raise CommandError(f'no {slot.name.lower()} called {value!r}.')
        char.look[slot_key] = feature.key
        c.ok(f'{slot.name}: {feature.name}.')
        c.blank()
        sess.autosave()
    elif len(args):
        target = (args.get(0) or '').lower()
        matches = [k for k in appearance.SLOT_KEYS if k.startswith(target)]
        if len(matches) != 1:
            raise CommandError(
                f'no such feature: {target!r}. '
                f'One of: {", ".join(appearance.SLOT_KEYS)}.')
        _look_options(sess, matches[0])
        return

    memorable, presence = char.memorable, char.presence
    label, why = char.memorable_band

    c.header(char.handle, f'running as {game.alias.name}')
    c.blank()
    for line in appearance.describe(char.look, char.marks):
        c.say(line)

    c.blank()
    c.rule('how the city reads you')
    c.kv([
        ('memorable', f'{memorable}  [accent]{label}[/]'),
        ('presence', f'{presence:+d}  [dim]legwork and favours '
                     f'{appearance.social_bonus(presence):+d}[/]'),
        ('heat from work',
         f'{(appearance.heat_mult(memorable) - 1) * 100:+.0f}%'),
        ('standing from work',
         f'{(appearance.rep_mult(memorable) - 1) * 100:+.0f}%'),
    ])
    c.blank()
    c.say(f'[dim]{why}[/]')

    floor = appearance.floor_from_chrome(char.dissonance)
    chosen = appearance.score(char.look, char.marks, 0)[0]
    # `floor > chosen` alone is not enough: a floor of zero is no floor, and
    # a character with no chrome at all scores below it, so the most
    # deliberately forgettable build in the game was being told it could not
    # be forgettable.
    if floor > 0 and floor > chosen:
        c.blank()
        c.warn('You cannot get under it any more. Whatever you have had done '
               'shows in how you hold still, and no haircut fixes that.')
        c.say(f'[dim]Chrome floor {floor}, and the choices you made come to '
              f'{chosen}.[/]')

    c.blank()
    c.say('[dim]`self <slot>` for the options in one. '
          '`self --set <slot> <key>` to change one. '
          '`self --roll` to reroll everything you can change.[/]')
