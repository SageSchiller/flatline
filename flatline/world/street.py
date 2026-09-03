"""The street as an engine (D65): encounters, the checks, the warning, the
end, and the work that has nothing to do with a deck.

The content is in `content/street.py`. This is what makes it happen: which
encounter fits this much danger at this hour, the printed sums behind
`run`, `talk`, `stand` and `careful`, what an outcome does to a body, a
bag and a name, and the one rule that matters most, which is that nothing
here kills anybody who was not told first.

Errands are the other half: courier work and a shift on watch, paid in
credits, priced by how far and how dangerous, with the same street in the
way. They need no deck. They are what a runner does between runs, and what
a character who is not a runner at all might do instead.
"""

from __future__ import annotations

from ..content import districts, factions, spots
from ..content import street as street_content
from ..run.checks import Check

#: Danger to tier: below 45 a lean, below 60 a press, below 75 a taking,
#: and past that the kind that kills (once you have been warned).
TIER_AT = ((75, 4), (60, 3), (45, 2), (0, 1))

#: What an errand teaches, in experience (D91). Small, and it is what a
#: street build lives on until the first door opens.
ERRAND_XP = 1

#: How much of the incident roll at travel is an encounter rather than the
#: old ladder (shakedown, beating, deck, chrome, burn). Both are the street.
ENCOUNTER_SHARE = 0.6

#: Chance of a tier-1 street encounter in the close-call band on arrival,
#: and of a lean on a rough night's rest somewhere dangerous.
TEXTURE_CHANCE = 0.18
ROUGH_NIGHT_CHANCE = 0.3

#: Errands: courier pay per hop, and a watch's base.
COURIER_PER_HOP = 180
WATCH_BASE = 260


def tier_for(danger: int) -> int:
    for floor, tier in TIER_AT:
        if danger >= floor:
            return tier
    return 1


def choose(rng, game, who: str, tier: int, faction: str = ''):
    """An encounter of at most this tier for this kind of trouble, now.

    Prefers the tier asked for; lower ones fill in. Story rules on an
    encounter are read with the game's own `satisfied`. Returns None when
    nothing fits, which callers treat as the street having let you pass.
    """
    phase = game.city.phase
    here = game.city.where
    pool = [e for e in street_content.pool(tier, who, phase, here)
            if all(game.story.satisfied(r, game) for r in e.requires)]
    if not pool:
        return None
    # Something written for this street beats something written for any
    # street, at the same rung.
    # And not the one you just had, unless it is the only one (D87): two
    # of twenty, back to back, reads as a game with two.
    last = getattr(game.city, 'last_street', '')
    weights = {e.key: ((3.0 if e.tier == tier else 1.0)
                       * (2.5 if e.districts else 1.0)
                       * (0.1 if e.key == last and len(pool) > 1 else 1.0))
               for e in pool}
    key = rng.weighted(weights)
    return street_content.BY_KEY[key]


def check_for(game, enc, option, faction: str, danger: int) -> Check | None:
    """The printed sum behind an answer, or None for pay and none."""
    kind = option.check
    if kind not in street_content.CHECKS:
        return None
    attr, skill, second = street_content.CHECKS[kind]
    char = game.char
    check = Check(name=f'{option.key} ({enc.name.lower()})',
                  resistance=street_content.RESISTANCE[enc.tier]
                  + (danger // 20 if faction else 0))
    check.add(attr, char.attr(attr))
    check.add(skill, char.skill(skill) * 2)
    check.add(second, char.skill(second))
    if kind == 'talk' and char.has_technique('face'):
        check.add('a face', 4)
    if faction and kind == 'talk':
        hot = game.alias.attention(faction)
        if hot >= 50:
            check.add('they know exactly who you are', -(hot // 25))
    if char.integrity <= char.integrity_max // 3 and kind in ('run', 'stand'):
        check.add('you are hurt', -2)
    return check


def pay_cost(game, enc) -> int:
    cost = street_content.PAY[enc.tier]
    if game.char.has_technique('face'):
        cost //= 2
    return cost


def can_bolt(game, enc) -> bool:
    """Bolt: leave before it starts, once a day, not from tier 4."""
    return (game.char.has_technique('bolt') and enc.tier < 4
            and game.city.bolted != game.city.shift)


# --------------------------------------------------------------------------
# the encounter, as a question
# --------------------------------------------------------------------------


def _fill(game, enc, faction: str) -> dict:
    """What the setup line's placeholders stand for."""
    fac = factions.BY_KEY.get(faction)
    return {'fac': fac.short if fac else 'nobody\'s',
            'district': game.city.district.name}


def begin(sess, enc, faction: str = '', danger: int = 0,
          why: str = '') -> None:
    """Print the setup and the answers, and wait for the next line."""
    game, c = sess.game, sess.console
    game.city.last_street = enc.key
    fill = _fill(game, enc, faction)
    c.blank()
    c.rule('the street', role='warn')
    if why:
        c.say(f'[dim]{why}[/]')
    c.say(f'[warn]{enc.setup.format(**fill)}[/]')
    c.blank()
    keys = []
    for opt in enc.options:
        check = check_for(game, enc, opt, faction, danger)
        if opt.check == 'pay':
            cost = pay_cost(game, enc)
            can = game.char.credits >= cost
            tail = (f'[credit]{cost:,}c[/]' if can
                    else f'[dim]{cost:,}c, which you do not have[/]')
        elif check is None:
            tail = ''
        else:
            tail = f'[dim]{check.summary()}[/]'
        keys.append(opt.key)
        c.raw(f'  [accent]{opt.key:<8}[/] {opt.label}  {tail}')
    if can_bolt(game, enc):
        keys.append('bolt')
        c.raw(f'  [accent]{"bolt":<8}[/] Leave before it starts  '
              f'[dim]Streetcraft 2, once a day[/]')
    c.blank()
    c.say('[dim]Type one. They are not going to wait, and an empty line is '
          'standing there.[/]')
    _wait(sess, enc, faction, danger, keys)


#: Words that are somebody asking what is going on rather than somebody
#: refusing to answer. They reprint the question and cost nothing: the
#: street runs out of patience with people who will not answer, not with
#: people who want to see the odds again (D75).
ASIDES = ('help', '?', 'look', 'status', 'now', 'odds', 'what', 'again',
          'repeat', 'char', 'rep')


def _restate(sess, enc, faction: str, danger: int) -> None:
    """Print the question again, with the sums, having been asked to."""
    game, c = sess.game, sess.console
    fill = _fill(game, enc, faction)
    c.blank()
    c.say(f'[warn]{enc.setup.format(**fill)}[/]')
    c.blank()
    for opt in enc.options:
        check = check_for(game, enc, opt, faction, danger)
        if opt.check == 'pay':
            cost = pay_cost(game, enc)
            can = game.char.credits >= cost
            tail = (f'[credit]{cost:,}c[/]' if can
                    else f'[dim]{cost:,}c, which you do not have[/]')
        elif check is None:
            tail = ''
        else:
            tail = f'[dim]{check.summary()}[/]'
        c.raw(f'  [accent]{opt.key:<8}[/] {opt.label}  {tail}')
    if can_bolt(game, enc):
        c.raw(f'  [accent]{"bolt":<8}[/] Leave before it starts  '
              f'[dim]Streetcraft 2, once a day[/]')
    c.blank()
    c.say('[dim]An empty line is standing there.[/]')


def _wait(sess, enc, faction: str, danger: int, keys, tries: int = 0) -> None:
    """Ask, and keep the same prompt when the answer was not one of them."""
    tier_word = street_content.TIER_NAMES[enc.tier]
    # A colon, not a comma: "a lean, run, talk, stand?" read as four
    # options (D91).
    sess.ask(f'{tier_word}: {", ".join(keys)}? ',
             lambda s, text: _answer(s, enc, faction, danger, text, tries),
             on_cancel='', choices=tuple(keys), must_answer=True)


#: Non-answers before the street stops waiting for one. It is not a
#: conversation: standing there is an answer and eventually it is the one
#: you have given.
PATIENCE = 3


def _answer(sess, enc, faction: str, danger: int, text: str,
            tries: int = 0) -> None:
    game, c = sess.game, sess.console
    low = text.strip().lower()
    if not low:
        # Standing there is an answer, whichever word this one uses for it.
        low = ('stand' if any(o.key == 'stand' for o in enc.options)
               else enc.options[-1].key)
        c.say('[dim]You stand there.[/]')
    elif low.split()[0] in {o.key for o in enc.options}:
        # `talk vance` at a street that offers `talk` is `talk` (D91).
        low = low.split()[0]
    if low == 'bolt' and can_bolt(game, enc):
        game.city.bolted = game.city.shift
        c.say('[ok]You were never there.[/] [dim]It is not a trick. It is '
              'having already left, and it works once a day.[/]')
        sess.autosave()
        return
    keys = [o.key for o in enc.options]
    if can_bolt(game, enc):
        keys.append('bolt')
    opt = next((o for o in enc.options if o.key == low
                or o.key.startswith(low)), None)
    if opt is None and low.split()[0] in ASIDES:
        # Asking what the question was is not refusing to answer it. This
        # used to burn one of three strikes, so a player who typed `help`
        # at a knife in a doorway was two keystrokes from having stood
        # there.
        _restate(sess, enc, faction, danger)
        _wait(sess, enc, faction, danger, keys, tries)
        return
    if opt is None:
        if tries + 1 >= PATIENCE:
            c.err(f'{text!r} is not one of the answers, and they have '
                  f'stopped waiting for one.')
            opt = next((o for o in enc.options if o.key == 'stand'),
                       enc.options[-1])
        else:
            c.err(f'{text!r} can wait. This cannot: '
                  + ', '.join(keys) + '.')
            _wait(sess, enc, faction, danger, keys, tries + 1)
            return
    rng = game.rng('events')
    if opt.check == 'pay':
        cost = pay_cost(game, enc)
        if game.char.credits < cost:
            c.err(f'You do not have {cost:,}c. Something else.')
            _wait(sess, enc, faction, danger,
                  [o.key for o in enc.options if o.check != 'pay'], tries)
            return
        game.char.credits -= cost
        c.blank()
        c.say(f'[credit]{cost:,}c[/] gone.')
        _apply(sess, enc, faction, opt.win, rng, won=True)
        return
    check = check_for(game, enc, opt, faction, danger)
    if check is None:
        _apply(sess, enc, faction, opt.win, rng, won=True)
        return
    check.resolve(rng)
    c.blank()
    c.say(f'[dim]{check.explain()}[/]')
    _apply(sess, enc, faction, opt.win if check.success else opt.lose, rng,
           won=check.success)


#: Below this, a bad answer is a bad answer and the street gets on with
#: it. At or above it there is time to do one thing about it, which is
#: the physical half of D81: the same design as `brace`, out here.
FLINCH_AT = 3


def _flinch(sess, enc, faction, outcome, rng, hurt, then) -> None:
    """It has gone wrong and there is one thing you can still do.

    The street was a single check: you chose, it resolved, and what
    happened next happened to you. That is fine for the small ones and
    thin for the ones that put you in a clinic, and it left every point
    of Grit and every rank of Fieldcraft doing nothing but sitting in a
    sum you never saw twice.

    So a bad answer that is going to cost you buys one more decision.
    Nobody throws a punch here and nobody is going to: `cover` is taking
    it properly, `give` is making it not worth their time, and both are
    printed checks like everything else (D81).
    """
    game, c = sess.game, sess.console
    char = game.char
    cost = min(char.credits, 120 + 90 * enc.tier)
    # Hard at the top and never impossible: at six plus two a rung the
    # fourth rung was out of reach of every build in the game, which
    # makes the option decoration. A Grit build that has bought Fieldcraft
    # can turn with the worst of it about two nights in five.
    cover = Check(name='cover', resistance=4 + 2 * enc.tier)
    cover.add('grit', char.attr('grit'))
    cover.add('fieldcraft', char.skill('fieldcraft') * 2)
    if char.has_technique('scar'):
        cover.add('scar tissue', 2)
    c.blank()
    c.say(f'[err]It is going to land, and it is going to be about {hurt} '
          f'of you.[/]')
    c.raw(f'  [accent]cover[/]    Get an arm up and turn with it  '
          f'[dim]{cover.summary()}[/]')
    if cost >= 120:
        c.raw(f'  [accent]give[/]     Make it not worth the trouble  '
              f'[credit]{cost:,}c[/]')
    c.blank()
    # A second question, said to be one (D100): it took Integrity fourteen
    # to four when a verb was typed at it, because nothing said that
    # anything but the two words above was taking it as it comes.
    c.say('[dim]A second question, and it does not wait: `cover`'
          + (', `give`' if cost >= 120 else '')
          + ', or anything else, which is taking it as it comes.[/]')
    keys = ['cover'] + (['give'] if cost >= 120 else [])

    def answered(s, text: str) -> None:
        low = (text or '').strip().lower()
        soft = 0
        if low.startswith('c'):
            cover.resolve(game.rng('combat'))
            c.blank()
            c.say(cover.explain())
            if cover.success:
                soft = max(1, hurt // 2)
                c.say('[ok]You turn with it and most of it goes past.[/]')
            else:
                c.say('[err]You get it wrong and it goes in properly.[/]')
        elif low.startswith('g') and cost >= 120:
            char.credits -= cost
            soft = hurt
            c.blank()
            c.say(f'[credit]{cost:,}c[/] [dim]changes hands. They were '
                  f'never here for you.[/]')
        else:
            c.blank()
            c.say('[dim]You take it as it comes.[/]')
        then(max(0, hurt - soft))

    sess.ask(f'{", ".join(keys)}? ', answered, on_cancel='',
             choices=tuple(keys), must_answer=True)


def _apply(sess, enc, faction: str, outcome, rng, won: bool) -> None:
    """What an outcome does to you. The warning rule lives here."""
    game, c = sess.game, sess.console
    char = game.char
    fac = factions.BY_KEY.get(faction)
    who = faction or 'street'
    if outcome.text:
        c.blank()
        c.say(f'[{"ok" if won else "err"}]{outcome.text}[/]')
    told = []
    lo, hi = outcome.hurt
    hurt = rng.int(lo, hi) if hi >= lo else 0
    if hurt < 0:
        heal = min(-hurt, char.hurt)
        char.hurt -= heal
        if heal:
            told.append(f'[ok]Integrity +{heal}.[/]')
        hurt = 0
    if hurt > 0 and char.has_technique('shrug'):
        hurt = max(1, hurt // 2)
        told.append('[dim]Shrug: half of it.[/]')
    # One more decision before it lands, when it is going to be worth
    # deciding about (D81). Everything after this point is the same, so
    # the rest of the outcome runs as a continuation.
    if not won and hurt >= FLINCH_AT:
        _flinch(sess, enc, faction, outcome, rng, hurt,
                lambda left: _land(sess, enc, faction, outcome, rng, won,
                                   left, told))
        return
    _land(sess, enc, faction, outcome, rng, won, hurt, told)


def _land(sess, enc, faction: str, outcome, rng, won: bool, hurt: int,
          told: list) -> None:
    """What the outcome does, once it is decided how it is taken."""
    game, c = sess.game, sess.console
    char = game.char
    fac = factions.BY_KEY.get(faction)
    who = faction or 'street'
    killed = False
    if hurt > 0:
        left = char.integrity - hurt
        warned = f'warned:{who}' in game.story.flags
        if outcome.lethal and enc.tier == 4 and warned and left <= 0:
            char.hurt = char.integrity_max
            killed = True
        else:
            if outcome.lethal and enc.tier == 4 and left <= 0:
                # The warning. The blow lands and leaves you at one, and
                # the next one will not (D6: telegraphed, then absolute).
                hurt = max(0, char.integrity - 1)
                game.story.flags.add(f'warned:{who}')
                told.append(f'[err]That was the warning. Next time '
                            f'{fac.short if fac else "they"} will not be '
                            f'asking, and you will not be getting up.[/]')
            else:
                hurt = min(hurt, max(0, char.integrity - 1))
            char.hurt += hurt
            if hurt:
                told.append(f'[err]Integrity -{hurt}[/] [dim]'
                            f'({char.integrity}/{char.integrity_max})[/]')
    if outcome.credits > 0 and char.credits > 0:
        take = min(char.credits, max(50, int(char.credits * outcome.credits)))
        char.credits -= take
        told.append(f'[credit]{take:,}c[/] gone.')
    if outcome.heat and fac is not None:
        game.alias.add_heat(faction, outcome.heat)
        told.append(f'[dim]{fac.short} heat {outcome.heat:+d}.[/]')
    if outcome.mark:
        got = char.mark(outcome.mark)
        if got is not None:
            told.append(f'[dim]It leaves a mark: {got.name.lower()}.[/]')
    if outcome.deck:
        from ..content import hardware
        working = [s for s in hardware.SLOTS if char.deck.working(s)]
        if working:
            slot = rng.pick(working)
            level = char.deck.hurt(slot, 1)
            comp = char.deck.component(slot)
            told.append(f'[dim]{comp.name if comp else slot} damaged '
                        f'({level}/3).[/]')
    for line in told:
        c.say(line)
    game.city.news.append(
        f'[warn]{enc.name}[/] in {game.city.district.name}: '
        + ('you got clear.' if won else 'it cost you.'))
    game.story.flags.add(f'street:{enc.key}')
    if killed:
        _die(sess, enc, faction)
        return
    sess.record_progress()
    sess.autosave()


def _die(sess, enc, faction: str) -> None:
    """The street ends a character. Same shape as the flatline."""
    from ..commands.core import end_character
    game, c = sess.game, sess.console
    fac = factions.BY_KEY.get(faction)
    c.blank()
    c.raw('[err][bold]It does not stop.[/][/]')
    c.say(f'You were told. {fac.short if fac else "Somebody"} told you, in '
          f'{game.city.district.name}, in so many words, and you went back, '
          f'or you never left, and this is the part after the telling.')
    game.city.news.append(f'[err]{game.char.handle} died in '
                          f'{game.city.district.name}.[/]')
    end_character(sess, 'killed in the street')


# --------------------------------------------------------------------------
# hooks: where the street happens
# --------------------------------------------------------------------------


def on_arrival(sess, faction: str, danger: int) -> bool:
    """The incident roll at travel, as an encounter some of the time.
    Returns True if an encounter began (and the caller should not also run
    the old ladder)."""
    game = sess.game
    rng = game.rng('events')
    if not rng.chance(ENCOUNTER_SHARE):
        return False
    tier = tier_for(danger)
    if faction in game.city.arrangements:
        from .city import ARRANGE_TIER_CAP
        tier = min(tier, ARRANGE_TIER_CAP)
    enc = choose(rng, game, 'faction', tier, faction)
    if enc is None:
        return False
    begin(sess, enc, faction, danger,
          why=f'{factions.BY_KEY[faction].short} have people here and a '
              f'reason.')
    return True


def texture(sess, danger: int) -> bool:
    """Below the ladder: a small thing in the street, sometimes. Twice as
    often with somebody in tow or something warm in the bag."""
    game = sess.game
    rng = game.rng('events')
    chance = TEXTURE_CHANCE * (2.0 if game.city.errand.get('hot') else 1.0)
    if not rng.chance(chance):
        return False
    enc = choose(rng, game, 'street', 1)
    if enc is None:
        return False
    begin(sess, enc, '', danger)
    return True


def rough_night(sess) -> bool:
    """Sleeping somewhere dangerous without a safehouse."""
    game = sess.game
    danger, who = game.city.danger(game.alias, game.city.where,
                                   flags=game.story.flags, riders=game.char.riders())
    if danger < 40 or game.city.phase != 'night':
        return False
    rng = game.rng('events')
    if not rng.chance(ROUGH_NIGHT_CHANCE):
        return False
    if who:
        enc = choose(rng, game, 'faction', min(2, tier_for(danger)), who)
    else:
        enc = choose(rng, game, 'street', 2)
    if enc is None:
        return False
    begin(sess, enc, who or '', danger, why='You did not sleep well, and '
                                             'somebody noticed where.')
    return True


# --------------------------------------------------------------------------
# errands
# --------------------------------------------------------------------------


def errands_here(game) -> list[dict]:
    """Two pieces of street work on offer in this district this shift,
    deterministic in (district, shift) so looking twice shows the same two."""
    city = game.city
    stream = game.rng.fork('errands', f'{city.where}:{city.shift // 3}')
    here = city.district
    out = []
    # Courier: somewhere one to three shifts away.
    far = [d for d in districts.DISTRICTS
           if d.key != city.where and 1 <= city.shifts_to(d.key) <= 3]
    if far:
        target = stream.pick(far)
        hops = city.shifts_to(target.key)
        danger, _ = city.danger(game.alias, target.key, flags=game.story.flags, riders=game.char.riders())
        hot = stream.chance(0.3)
        pay = COURIER_PER_HOP * hops + danger * 3 + (200 if hot else 0)
        out.append({'kind': 'courier', 'to': target.key, 'pay': int(pay),
                    'hot': hot, 'from': city.where,
                    'what': stream.pick(COURIER_PACKAGES)})
    # The second one is local: a watch, or a debt to collect, or somebody
    # who needs walking somewhere, by the shift.
    places = spots.in_district(city.where)
    where = stream.pick(places).name if places else here.name
    local = stream.weighted({'watch': 2.0, 'collect': 1.2, 'escort': 1.0})
    if local == 'escort' and far:
        target = stream.pick(far)
        hops = city.shifts_to(target.key)
        danger, _ = city.danger(game.alias, target.key, flags=game.story.flags, riders=game.char.riders())
        out.append({'kind': 'escort', 'to': target.key,
                    'pay': int(ESCORT_PER_HOP * hops + danger * 4 + 150),
                    'hot': True, 'from': city.where,
                    'what': stream.pick(ESCORTEES)})
    elif local == 'collect':
        owed = stream.int(12, 40) * 100
        out.append({'kind': 'collect', 'at': where, 'owed': owed,
                    'pay': int(owed * COLLECT_CUT), 'from': city.where,
                    'who': stream.pick(DEBTORS)})
    else:
        pay = WATCH_BASE + here.security * 2
        out.append({'kind': 'watch', 'at': where, 'pay': int(pay),
                    'from': city.where})
    # Once each per window (D101). The offers are deterministic in the
    # district and the window so looking twice shows the same two, which
    # also meant taking twice paid twice.
    window = f'{city.where}:{city.shift // 3}'
    for i, job in enumerate(out):
        job['key'] = f'{window}:{i}'
    return [job for job in out
            if job['key'] not in getattr(city, 'errands_taken', ())]


#: Escort pay per hop, and what a collector keeps of what they collect.
ESCORT_PER_HOP = 260
COLLECT_CUT = 0.15

ESCORTEES = (
    'a clerk who has stopped looking over their shoulder, which is how you '
    'know they should',
    'a woman with a child and a suitcase that is mostly child',
    'a man who says he is nobody, twice, unprompted',
    'somebody the Hall fed for a month, walking for the first time in it',
    'a courier who has lost the case and not the habit of carrying it',
)

DEBTORS = (
    'a man behind a shutter who owes the Sixes and knows your face from '
    'somewhere',
    'a woman running a stall who pays everybody late and everybody on time',
    'two brothers who disagree about which of them owes it',
    'somebody who has moved twice since the loan and not far enough',
)


def collect(sess, job: dict) -> None:
    """A debt to collect, at a door, with your voice (D65). A talk check;
    win and you keep a cut, lose and it is a press in a doorway."""
    game, c = sess.game, sess.console
    check = Check(name='collect', resistance=7 + game.city.district.security // 15)
    check.add('guile', game.char.attr('guile'))
    check.add('streetcraft', game.char.skill('streetcraft') * 2)
    check.add('subterfuge', game.char.skill('subterfuge'))
    if game.char.has_technique('face'):
        check.add('a face', 4)
    c.say(f'You find {job["who"]}, and say the number, which is '
          f'{job["owed"]:,}c, and wait.')
    check.resolve(game.rng('events'))
    c.say(f'[dim]{check.explain()}[/]')
    if check.success:
        game.char.credits += job['pay']
        game.earned += job['pay']
        game.city.errands_done += 1
        game.char.xp += ERRAND_XP
        c.ok(f'They pay, eventually, most of it. Your cut is '
             f'[credit]{job["pay"]:,}c[/]. [dim]{ERRAND_XP} experience.[/]')
        sess.record_progress()
        return
    c.err('They do not pay. They have friends, it turns out, and a doorway.')
    enc = street_content.BY_KEY['knives']
    begin(sess, enc, '', 40, why='The debt was not the problem. You were.')


COURIER_PACKAGES = (
    'a case that is not heavy enough', 'a paper bag, stapled shut',
    'a deck bag with no deck in it', 'a box of printed things, still warm',
    'something in a cool bag that needs to stay cool',
    'an envelope you are not to bend',
)


def deliver(sess) -> None:
    """Called on arrival: if the package was for here, it is delivered."""
    game, c = sess.game, sess.console
    errand = game.city.errand
    if not errand or errand.get('kind') not in ('courier', 'escort'):
        return
    if errand.get('to') != game.city.where:
        return
    pay = int(errand.get('pay', 0))
    game.char.credits += pay
    game.earned += pay
    kind = errand.get('kind')
    game.city.errand = {}
    game.city.errands_done += 1
    # The street teaches something too (D91): a street build with every
    # door reading shut had no way to earn the rank that opens one.
    game.char.xp += ERRAND_XP
    controller = game.city.district.controller
    game.alias.adjust_rep(controller, 3)
    c.blank()
    c.rule('delivered', role='ok')
    c.say(f'[dim]{ERRAND_XP} experience.[/]')
    if kind == 'escort':
        c.say(f'You get {errand.get("what", "them")} to the agreed place, '
              f'and somebody takes them in, and they do not look back, and '
              f'you are paid by somebody who does not say thank you.')
    else:
        c.say(f'Somebody is waiting for {errand.get("what", "it")} at the '
              f'agreed place, and takes it, and does not look inside, and '
              f'pays.')
    c.say(f'[credit]{pay:,}c[/]. [dim]{factions.BY_KEY[controller].short} '
          f'warmer, a little.[/]')
    game.city.news.append(f'Delivered {errand.get("what", "a package")} to '
                          f'{game.city.district.name}: {pay:,}c.')
    sess.record_progress()
