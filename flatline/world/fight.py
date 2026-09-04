"""The fight (D128): a short exchange on the street.

The street was a single check: you chose, it resolved, and what happened
next happened to you. D81 gave a bad one a second decision. This is the
third shape: a fight is rounds. Each round you pick a move, it resolves as
a printed check, and then they hit you, until they are done or you are,
or you get out. It is the net's ICE combat with the deck in the bag: a
number going down on both sides and a decision every beat.

Two routes in. Violence is hands, a blade, or a gun, and reads the skill
of that name. `jack` is the netrunner's: the deck against their chrome,
read by Warfare and whatever weapon program is loaded, and no use at all
on somebody with nothing in them to reach. `break` is always on the menu,
because starting a fight never takes away the way out; it makes it cost
more.

What it costs is the point. A gun is a Nightwatch matter every time it is
drawn; the kind that kills is the kind you have killed when you win; and
the Integrity you lose here is the same number the net spends, so a
runner who fought their way home jacks in bleeding. D6 holds: no round of
a fight kills you, and a lost fight is the encounter's worst outcome,
which at the top of the ladder warns first and then does not.

The engine owns the rounds and nothing else. Who you are fighting, and
what winning or losing means, are the caller's (`world/street.py` for an
encounter, `world/rivals.py` for a reckoning), handed in as a `Foe` and a
`then` callback: `then(sess, fight, 'won' | 'lost' | 'broke')`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..content import armour as armour_content
from ..content import drugs as drug_content
from ..content import programs as program_content
from ..content import street as street_content
from ..content import weapons as weapon_content
from ..run.checks import Check, CRIT

#: What there is to get through, by tier, and what each of their hits is
#: worth before armour. A lean is a couple of people who did not expect
#: it; the kind that kills is people who did.
FOE_POOL = {1: 4, 2: 8, 3: 12, 4: 20}
FOE_HIT = {1: (1, 2), 2: (2, 3), 3: (3, 5), 4: (6, 10)}
#: The kind that kills wears something too: what they take off every
#: strike that lands on them (D131). Nobody else does.
FOE_ARMOUR = {4: 2}
#: A crit is half again, not double: a fight should take a second round.
CRIT_MULT = 1.5
#: Who hears a gun, and what it costs them to have heard it.
LAW = 'nightwatch'
LOUD_HEAT = 6
#: What killing somebody costs on top. The mark it leaves is `blooded`.
KILL_HEAT = 4
#: A fight this long has been noticed. They break off; so should you.
LONG_FIGHT = 8
#: Non-answers before the fight stops waiting and you cover up.
PATIENCE = 3
#: `finish` is on the menu once they are at or below this share of them.
FINISH_AT = 0.5
#: What `jack` does when nothing offensive is loaded.
JACK_BASE = 1
#: What a won fight teaches, by tier (D131). A lean teaches nothing; the
#: kind that kills teaches most of what a run does.
FIGHT_XP = {1: 0, 2: 1, 3: 2, 4: 3}
#: A partner beside you: the chance a round that they put one down, and
#: what that takes off them.
ALLY_CHANCE = 0.6
ALLY_HIT = 2

ASIDES = ('help', '?', 'look', 'status', 'now', 'odds', 'what', 'again',
          'repeat', 'char', 'rep')


@dataclass
class Foe:
    """Who you are fighting, as the engine needs to know them."""
    tier: int
    #: Whether there is chrome in them for the deck to reach.
    chromed: bool
    #: Faction key, or '' for nobody's people.
    faction: str
    #: Placeholders for the lines (`fac`, `district`).
    fill: dict
    #: District danger, which stiffens their resistance when they are
    #: somebody's people.
    danger: int = 0
    #: A word for them in the state line.
    them: str = 'them'
    #: A named fighter (D134): extra on the pool and on every hit, over
    #: the tier.
    pool_bonus: int = 0
    hit_bonus: int = 0


@dataclass
class Fight:
    foe: Foe
    pool: int
    pool_max: int
    then: Callable
    round: int = 1
    #: Their hit, reduced by chrome you have turned off.
    bricked: int = 0
    #: They saw the deck: there is no second try.
    jack_burned: bool = False
    #: A guard that worked: the next strike goes in easier.
    set_up: bool = False
    #: A baton hit: their next one lands at half.
    stunned: bool = False
    #: The loud thing came out.
    drawn: bool = False
    #: A reach weapon kept them off: no return hit this round.
    kept_off: bool = False
    #: A talk-down that did not take: it does not work twice.
    talk_burned: bool = False
    #: A blunt hit put one on the floor: their next hit lands lighter.
    staggered: bool = False
    #: Somebody standing with you, by name, or ''.
    ally: str = ''
    shrugged: bool = False
    tries: int = 0

    @property
    def state(self) -> str:
        share = self.pool / self.pool_max if self.pool_max else 0
        for floor, word in street_content.FOE_STATE:
            if share >= floor:
                return word
        return street_content.FOE_STATE[-1][1]


# --------------------------------------------------------------------------
# the sums
# --------------------------------------------------------------------------


def _resist(f: Fight) -> int:
    base = street_content.RESISTANCE[f.foe.tier]
    return base + (f.foe.danger // 20 if f.foe.faction else 0)


def armour_of(char) -> int:
    """Worn and fitted together, capped (D131)."""
    worn = armour_content.BY_KEY.get(char.armour)
    return min(armour_content.CAP,
               char.bonus('armour') + (worn.armour if worn else 0))


def weapon_of(char):
    return (weapon_content.BY_KEY.get(char.weapon)
            or weapon_content.granted(char.installed))


def strike_damage(char, crit: bool = False) -> int:
    """What a landed strike takes off them."""
    dmg = 2 + char.skill('violence')
    w = weapon_of(char)
    if w is not None:
        # Holding it is not using it: untrained, a weapon does half.
        dmg += w.damage if char.skill('violence') else max(1, w.damage // 2)
        if w.rider == 'smartlink' and not any(
                k for k in char.installed
                if k in _neural_keys()):
            dmg -= 2
    dmg += char.bonus('strike_damage')
    return max(1, int(dmg * CRIT_MULT) if crit else dmg)


def _neural_keys() -> set[str]:
    from ..content import cyberware
    return {w.key for w in cyberware.WARE if w.location == 'neural'}


def jack_damage(char) -> int:
    """The deck against their chrome: the best weapon program loaded."""
    best = 0
    for key in char.deck.loaded:
        p = program_content.BY_KEY.get(key)
        if p is not None and p.category == 'weapon':
            best = max(best, p.tier)
    return JACK_BASE + best + (1 if best else 0)


def coming_down(char) -> bool:
    """Any comedown in progress (D133). The crash already lowers what it
    lowers through the attributes; this is the part a fight adds on top,
    printed so the player sees the chem in the sum."""
    return any(drug_content.is_down(char.chem, k) for k in drug_content.BY_KEY)


def strike_check(game, f: Fight) -> Check:
    char = game.char
    check = Check(name='strike', resistance=_resist(f))
    check.add('grit', char.attr('grit'))
    check.add('violence', char.skill('violence') * 2)
    check.add('nerve', char.attr('nerve'))
    if f.set_up:
        check.add('set up', 2)
    w = weapon_of(char)
    if w is not None and w.rider == 'edge':
        check.add('an edge', 1)
    if w is not None and w.rider == 'concealed' and f.round == 1:
        check.add('they did not see it', 2)
    if char.bonus('strike_bonus'):
        check.add('targeting' if 'targeting' in char.installed else 'aim',
                  char.bonus('strike_bonus'))
    if coming_down(char):
        check.add('coming down', -2)
    if (char.integrity <= char.integrity_max // 3
            and 'pain_editor' not in char.riders()):
        check.add('you are hurt', -2)
    return check


def guard_check(game, f: Fight) -> Check:
    char = game.char
    check = Check(name='guard', resistance=_resist(f) - 2)
    check.add('reflex', char.attr('reflex'))
    check.add('fieldcraft', char.skill('fieldcraft') * 2)
    check.add('violence', char.skill('violence'))
    if char.bonus('guard_bonus'):
        check.add('reflex booster' if char.bonus('guard_bonus') > 0
                  else 'you do not cover up', char.bonus('guard_bonus'))
    if coming_down(char):
        check.add('coming down', -2)
    return check


def jack_check(game, f: Fight) -> Check:
    char = game.char
    check = Check(name='jack', resistance=_resist(f))
    check.add('logic', char.attr('logic'))
    check.add('warfare', char.skill('warfare') * 2)
    check.add('intrusion', char.skill('intrusion'))
    return check


def finish_check(game, f: Fight) -> Check:
    char = game.char
    check = Check(name='finish', resistance=_resist(f) + 2)
    check.add('grit', char.attr('grit'))
    check.add('violence', char.skill('violence') * 2)
    check.add('nerve', char.attr('nerve'))
    return check


def talk_check(game, f: Fight) -> Check:
    char = game.char
    check = Check(name='talk', resistance=_resist(f) + 1)
    check.add('guile', char.attr('guile'))
    check.add('streetcraft', char.skill('streetcraft') * 2)
    check.add('a face', 2)
    # Easier once they are hurting and can take the excuse to stop.
    if f.pool <= f.pool_max * 0.5:
        check.add('they would rather stop', 2)
    return check


def break_check(game, f: Fight) -> Check:
    char = game.char
    check = Check(name='break', resistance=_resist(f) + 2)
    check.add('reflex', char.attr('reflex'))
    check.add('fieldcraft', char.skill('fieldcraft') * 2)
    check.add('streetcraft', char.skill('streetcraft'))
    if coming_down(char):
        check.add('coming down', -2)
    if (char.integrity <= char.integrity_max // 3
            and 'pain_editor' not in char.riders()):
        check.add('you are hurt', -2)
    return check


def moves(game, f: Fight) -> list[tuple[str, str, Check | None, str]]:
    """(key, label, check, note) for what you can do this round."""
    char = game.char
    w = weapon_of(char)
    out = []
    out.append(('strike', 'Hit them' + (f', with the {w.name.lower()}'
                                        if w else ''),
                strike_check(game, f), f'+{strike_damage(char)}'))
    out.append(('guard', 'Cover up and take it on the arm',
                guard_check(game, f), 'sets up the next strike'))
    if f.foe.chromed and not f.jack_burned:
        out.append(('jack', 'The deck, against their chrome',
                    jack_check(game, f), f'+{jack_damage(char)}, and it stays off'))
    if (char.has_technique('finisher')
            and f.pool <= f.pool_max * FINISH_AT):
        out.append(('finish', 'End it', finish_check(game, f),
                    'all of it, or wide open'))
    if (char.has_technique('face') and not f.talk_burned
            and 'no_talkdown' not in char.riders()):
        out.append(('talk', 'Talk them down', talk_check(game, f),
                    'ends it, clean, if it takes'))
    out.append(('break', 'Get out of it', break_check(game, f), ''))
    return out


# --------------------------------------------------------------------------
# the rounds
# --------------------------------------------------------------------------


def begin(sess, foe: Foe, then: Callable, first_hit: bool = False,
          ally: str = '') -> None:
    """Start it. `first_hit` is a fight you did not start well: they go
    first (a `menace` that did not take). `ally` is somebody standing with
    you, by name, or ''."""
    game, c = sess.game, sess.console
    char = game.char
    pool = FOE_POOL[foe.tier] + foe.pool_bonus
    f = Fight(foe=foe, pool=pool, pool_max=pool, then=then, ally=ally)
    c.blank()
    c.rule('a fight', role='err')
    c.say(f'[warn]{street_content.FIGHT_OPEN[foe.tier].format(**foe.fill)}[/]')
    if not foe.chromed:
        c.say(f'[dim]{street_content.JACK_NOTHING}[/]')
    if ally:
        c.say(f'[dim]{ally} is beside you.[/]')
    if 'adrenal' in char.riders():
        # The pump fires: the first second of it, you have already had.
        f.set_up = True
        c.say('[dim]The pump fires. The arm is up and the world is slow.[/]')
    if first_hit:
        _foe_hits(sess, f)
        if _lost(sess, f):
            return
    _menu(sess, f)
    _wait(sess, f)


def _menu(sess, f: Fight) -> None:
    game, c = sess.game, sess.console
    char = game.char
    c.blank()
    armour = armour_of(char)
    c.say(f'[dim]{f.foe.them}: {f.state}. You: Integrity '
          f'{char.integrity}/{char.integrity_max}'
          + (f', armour {armour}' if armour else '') + '.[/]')
    for key, label, check, note in moves(game, f):
        tail = f'[dim]{check.summary()}[/]' if check is not None else ''
        if note:
            tail += f'  [dim]{note}[/]'
        c.raw(f'  [accent]{key:<8}[/] {label}  {tail}')
    c.blank()
    c.say('[dim]Type one. An empty line is covering up.[/]')


def _wait(sess, f: Fight) -> None:
    keys = [m[0] for m in moves(sess.game, f)]
    sess.ask(f'round {f.round}, {f.foe.them} {f.state}: {", ".join(keys)}? ',
             lambda s, text: _answer(s, f, text),
             on_cancel='', choices=tuple(keys), must_answer=True)


def _answer(sess, f: Fight, text: str) -> None:
    game, c = sess.game, sess.console
    char = game.char
    low = (text or '').strip().lower()
    keys = [m[0] for m in moves(game, f)]
    word = low.split()[0] if low else ''
    if not word:
        move = 'guard'
        c.say('[dim]You cover up.[/]')
    elif word in ASIDES:
        _menu(sess, f)
        _wait(sess, f)
        return
    else:
        move = next((k for k in keys if k == word), None) or next(
            (k for k in keys if k.startswith(word)), None)
        if move is None:
            f.tries += 1
            if f.tries >= PATIENCE:
                move = 'guard'
                c.err(f'{text!r} is not a move, and they are not waiting: '
                      f'you cover up.')
            else:
                c.err(f'{text!r} is not a move. This is: ' + ', '.join(keys)
                      + '.')
                _wait(sess, f)
                return
    # Answering properly buys back the patience a typo spent (D139).
    f.tries = 0
    rng = game.rng('combat')
    skip_hit = False
    guard = None
    c.blank()
    if move == 'strike':
        check = strike_check(game, f).resolve(rng)
        f.set_up = False
        c.say(f'[dim]{check.explain()}[/]')
        w = weapon_of(char)
        if w is not None and w.loud:
            f.drawn = True
        if check.success:
            crit = check.critical or (w is not None and w.rider == 'edge'
                                      and check.margin >= CRIT - 2)
            dmg = max(1, strike_damage(char, crit=crit)
                      - FOE_ARMOUR.get(f.foe.tier, 0))
            spread = 0
            if w is not None and w.rider == 'spread' and f.round <= 2:
                # It does not ask which of them you meant, while they are
                # still bunched.
                spread = 1 + f.foe.tier // 2
                dmg += spread
            f.pool -= dmg
            line = (rng.pick(street_content.STRIKE_CRIT) if crit
                    else rng.pick(street_content.STRIKE_WIN))
            note = f'-{dmg}'
            if spread:
                note += ', into the ones behind'
            c.say(f'[ok]{line}[/] [dim]({note})[/]')
            if w is not None and w.rider == 'stun':
                f.stunned = True
            if w is not None and w.rider == 'stagger':
                f.staggered = True
            if w is not None and w.rider == 'reach':
                # You kept them at the far end of the metre.
                f.kept_off = True
        else:
            c.say(f'[err]{rng.pick(street_content.STRIKE_LOSE)}[/]')
    elif move == 'guard':
        check = guard_check(game, f).resolve(rng)
        c.say(f'[dim]{check.explain()}[/]')
        guard = check.success
        if guard:
            c.say(f'[ok]{rng.pick(street_content.GUARD_WIN)}[/]')
            f.set_up = True
        else:
            c.say(f'[err]{rng.pick(street_content.GUARD_LOSE)}[/]')
    elif move == 'jack':
        check = jack_check(game, f).resolve(rng)
        c.say(f'[dim]{check.explain()}[/]')
        if check.success:
            dmg = jack_damage(char)
            f.pool -= dmg
            f.bricked += 1
            c.say(f'[ok]{rng.pick(street_content.JACK_WIN)}[/] [dim](-{dmg}, '
                  f'their hits -1 from here)[/]')
        else:
            f.jack_burned = True
            c.say(f'[err]{rng.pick(street_content.JACK_LOSE)}[/]')
            _foe_hits(sess, f)
            skip_hit = True
    elif move == 'finish':
        check = finish_check(game, f).resolve(rng)
        c.say(f'[dim]{check.explain()}[/]')
        if check.success:
            f.pool = 0
            c.say(f'[ok]{rng.pick(street_content.FINISH_WIN)}[/]')
        else:
            c.say(f'[err]{rng.pick(street_content.FINISH_LOSE)}[/]')
            _foe_hits(sess, f, bonus=1)
            skip_hit = True
    elif move == 'talk':
        check = talk_check(game, f).resolve(rng)
        c.say(f'[dim]{check.explain()}[/]')
        if check.success:
            c.say(f'[ok]{rng.pick(street_content.TALKDOWN_WIN)}[/]')
            _end(sess, f, 'talked')
            return
        f.talk_burned = True
        c.say(f'[err]{rng.pick(street_content.TALKDOWN_LOSE)}[/]')
        _foe_hits(sess, f)
        skip_hit = True
    elif move == 'break':
        check = break_check(game, f).resolve(rng)
        c.say(f'[dim]{check.explain()}[/]')
        if check.success:
            c.say(f'[ok]{rng.pick(street_content.BREAK_WIN)}[/]')
            _end(sess, f, 'broke')
            return
        c.say(f'[err]{rng.pick(street_content.BREAK_LOSE)}[/]')
    if f.ally and f.pool > 0 and rng.chance(ALLY_CHANCE):
        f.pool -= ALLY_HIT
        c.say(f'[ok]{rng.pick(street_content.ALLY_HIT).format(ally=f.ally)}[/] '
              f'[dim](-{ALLY_HIT})[/]')
    if f.pool <= 0:
        _end(sess, f, 'won')
        return
    if f.kept_off:
        f.kept_off = False
        skip_hit = True
        c.say(f'[dim]{street_content.FOE_REACHED}[/]')
    if not skip_hit:
        if guard is True:
            c.say(f'[dim]{street_content.FOE_MISS}[/]')
        else:
            _foe_hits(sess, f, scale=0.5 if guard is False else 1.0)
    if _lost(sess, f):
        return
    f.round += 1
    if f.round > LONG_FIGHT:
        c.blank()
        c.say('[warn]It has gone on long enough for the street to notice, '
              'and a street that has noticed is a street with the Nightwatch '
              'on the way. They break off. So should you.[/]')
        _end(sess, f, 'broke')
        return
    _menu(sess, f)
    _wait(sess, f)


def _foe_hits(sess, f: Fight, scale: float = 1.0, bonus: int = 0) -> None:
    """Their turn. Never lethal on its own (D6): a round can leave you at
    one, and the end of a lost fight is what decides the rest."""
    game, c = sess.game, sess.console
    char = game.char
    rng = game.rng('combat')
    lo, hi = FOE_HIT[f.foe.tier]
    raw = rng.int(lo, hi) + bonus + f.foe.hit_bonus - f.bricked
    told = []
    if f.stunned:
        raw //= 2
        f.stunned = False
        told.append(f'[dim]{street_content.FOE_STUNNED}[/]')
    if f.staggered:
        raw -= 2
        f.staggered = False
        told.append(f'[dim]{street_content.FOE_STAGGERED}[/]')
    raw = int(raw * scale)
    armour = armour_of(char)
    if armour and raw > 0:
        soaked = min(armour, raw)
        raw -= soaked
        if raw <= 0:
            told.append(f'[dim]{street_content.FOE_HIT_ARMOUR}[/]')
    if raw > 0 and char.has_technique('shrug') and not f.shrugged:
        raw = max(1, raw // 2)
        f.shrugged = True
        told.append('[dim]Shrug: half of it.[/]')
    raw = min(raw, max(0, char.integrity - 1))
    if raw <= 0:
        if not told:
            told.append(f'[dim]{street_content.FOE_GLANCE if scale < 1.0 else street_content.FOE_MISS}[/]')
        for line in told:
            c.say(line)
        return
    char.hurt += raw
    c.say(f'[err]{rng.pick(street_content.FOE_HIT)}[/] '
          f'[err]Integrity -{raw}[/] '
          f'[dim]({char.integrity}/{char.integrity_max})[/]')
    for line in told:
        c.say(line)


def _lost(sess, f: Fight) -> bool:
    if sess.game.char.integrity <= 1:
        _end(sess, f, 'lost')
        return True
    return False


def _end(sess, f: Fight, result: str) -> None:
    game, c = sess.game, sess.console
    char = game.char
    tier = f.foe.tier
    c.blank()
    if result == 'won':
        game.city.fights_won += 1
        c.rule('you won it', role='ok')
        c.say(f'[ok]{street_content.FIGHT_WON[tier].format(**f.foe.fill)}[/]')
    elif result == 'lost':
        c.rule('you lost it', role='err')
        c.say(f'[err]{street_content.FIGHT_LOST[tier].format(**f.foe.fill)}[/]')
    elif result == 'talked':
        c.rule('talked down', role='ok')
    else:
        c.rule('out of it', role='warn')
    if f.drawn:
        from ..content import conditions as cond_content
        tonight = cond_content.NIGHT_BY_KEY.get(getattr(game.city, 'tonight', ''))
        heat = int(LOUD_HEAT * (tonight.loud if tonight is not None else 1.0))
        game.alias.add_heat(LAW, heat)
        district = f.foe.fill.get('district', 'the district')
        c.say(f'[heat]{street_content.FIGHT_LOUD.format(district=district)}[/] '
              f'[dim]Nightwatch heat +{heat}'
              + (f', {tonight.name.lower()}' if tonight is not None and tonight.loud != 1.0 else '')
              + '.[/]')
        game.city.news.append(f'[heat]Shots in {district}.[/]')
    if result == 'won' and FIGHT_XP.get(tier, 0):
        char.xp += FIGHT_XP[tier]
        c.say(f'[dim]{FIGHT_XP[tier]} experience.[/]')
    if result == 'won' and (tier == 4 or (tier == 3 and f.drawn)):
        got = char.mark('blooded')
        game.alias.add_heat(LAW, KILL_HEAT)
        game.story.flags.add('killer')
        c.say(f'[warn]{street_content.FIGHT_KILLED}[/]')
        if got is not None:
            c.say(f'[dim]It leaves a mark: {got.name.lower()}.[/]')
    f.then(sess, f, result)
