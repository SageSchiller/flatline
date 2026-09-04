"""What people put in themselves to get through a shift, and what it costs.

**Everything here is a loan against your own body**, and it is written to the
same shape as the two other loans in this game. Residue becomes heat a shift
later; money borrowed becomes a collector at the door; and a dose becomes a
comedown that lasts longer than the high did and takes more than the high
gave. The city runs on getting away with things temporarily.

So the rule this file is authored under, and `validate.py` enforces it: **the
crash always outlasts the high and always costs more than the high paid.** A
drug that came out ahead would not be a decision, it would be equipment, and
the game already has equipment. What makes a dose worth taking is never the
arithmetic. It is that the arithmetic lands at a different time from the
problem.

**One number does all three jobs.** `habit` is tolerance, dependency and
withdrawal at once, and it is the only piece of state a player has to hold in
their head:

- It **weakens the high**, so the same dose does less each time.
- It **deepens the crash**, so the same dose costs more each time.
- Past `WITHDRAWAL_AT` it applies a third set of effects *whenever you are not
  using*, and those are the ones that hurt: your baseline is now below where
  you started, and a dose no longer makes you better than a person, it makes
  you a person again.

That last step is the whole system. Everything before it is a stat buff with a
bill attached, which is a thing any game has. The moment worth building is the
one where the player looks at a number that used to be five, sees three, and
understands that they did that.

**It is survivable, per D6.** Habit decays while you are clean, a clinic will
shorten it for money, and nothing in here can kill a character. It is a hole
you climb out of slowly, in the one currency this city actually charges in,
which is shifts.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: How deep a habit can get. Ten doses of the same thing, roughly, and the
#: ceiling matters: an unbounded one would make a long campaign unplayable
#: rather than difficult, and D6 says the only thing that ends a character is
#: black ICE.
HABIT_MAX = 10

#: Habit at which your body starts expecting it. Below this you are a person
#: who takes something occasionally; at it you are a person who needs to.
WITHDRAWAL_AT = 4

#: Clean shifts per point of habit shed. Deliberately slow: coming off
#: something has to cost more than the fortnight of using that put you there,
#: or the spiral has a cheap exit and stops being one.
CLEAN_SHIFTS = 5

#: How much of the high survives at maximum habit, and how much bigger the
#: crash gets. Tolerance is the part players feel first and understand last.
TOLERANCE_FLOOR = 0.35
CRASH_PER_HABIT = 0.14


@dataclass(frozen=True, slots=True)
class Drug:
    key: str
    name: str
    #: What it is, in one line, as somebody who sells it would put it.
    blurb: str
    #: Market tier, as programs and chrome. Gates which districts stock it.
    tier: int
    price: int
    #: While it is in you. Scaled down by habit.
    high: dict
    #: When it goes. Scaled *up* by habit, and always the larger of the two.
    crash: dict
    #: What you are like without it, once your body has decided it is normal.
    #: Applies only past `WITHDRAWAL_AT`, and only while you are not using.
    withdrawal: dict
    #: Shifts of each phase. `down` is never shorter than `up`.
    up: int
    down: int
    #: Habit added per dose. Zero is legal and there is exactly one of them.
    hook: int
    #: Which district services carry it.
    sold: tuple[str, ...]
    #: Second person, present tense, the moment it lands.
    onset: str
    #: The moment it turns. This is the line that teaches the system.
    turn: str
    #: A run-layer flag while it is in you.
    rider: str = ''
    #: Clears every comedown in progress. Exactly one thing does this and it
    #: is the worst idea in the catalogue.
    cures_crash: bool = False
    #: One of a kind (D63 e). Never in a market: found somewhere, given by
    #: somebody, or handed over by a decision. `lore` is its history, shown
    #: by `inspect` and when it is found.
    unique: bool = False
    lore: str = ''


DRUGS: tuple[Drug, ...] = (
    Drug(
        'kick', 'Kick',
        'Street stimulant, sold by the strip, cut with whatever was nearest.',
        tier=1, price=180,
        high={'reflex': 2, 'tempo': 1},
        crash={'reflex': -2, 'focus': -1, 'tick_mult': 1.15},
        withdrawal={'reflex': -2, 'focus': -1},
        up=2, down=3, hook=1,
        sold=('fence', 'market'),
        onset='It arrives between one breath and the next, and the room '
              'acquires edges it did not have. Your hands know what they are '
              'doing slightly before you do.',
        turn='The edges go. Everything is a half-second further away than '
             'your hands expect, and you keep reaching through where things '
             'used to be.'),

    Drug(
        'longwater', 'Longwater',
        'Prescribed to people with important jobs, and to nobody else, '
        'officially.',
        tier=2, price=900,
        high={'logic': 2, 'focus': 2, 'crypto_bonus': 2},
        crash={'logic': -2, 'tick_mult': 1.25, 'crack_bonus': -2},
        withdrawal={'logic': -2, 'focus': -1},
        up=2, down=4, hook=1,
        sold=('clinic', 'market'),
        onset='Nothing happens, and then you notice you have been reading the '
              'same wall for a while and have understood all of it. The '
              'thoughts arrive already finished.',
        turn='The thoughts stop arriving finished. You can feel the shape of '
             'the one you wanted and no way at all to get to it, which is '
             'considerably worse than never having had it.'),

    Drug(
        'ratchet', 'Ratchet',
        'For work injuries. Turns the volume down on the body rather than '
        'fixing anything.',
        tier=1, price=420,
        high={'integrity': 6, 'composure': 3},
        crash={'integrity': -6, 'grit': -2, 'reflex': -2},
        withdrawal={'integrity': -4, 'composure': -2},
        up=2, down=3, hook=2,
        sold=('clinic', 'fence'),
        onset='Everything that hurt goes quiet at once. It is not gone, it '
              'has been put in another room, and you can hear it in there.',
        turn='The other room opens. Every injury you spent the last two '
             'shifts not noticing arrives at the same time, in the order you '
             'collected them.'),

    Drug(
        'nightingale', 'Nightingale',
        'A calm you can buy. Popular with people who have to sit very still '
        'for a living.',
        tier=2, price=640,
        high={'composure': 4, 'evade_bonus': 2, 'noise_mult': 0.85},
        crash={'nerve': -3, 'guile': -2, 'noise_mult': 1.25},
        withdrawal={'composure': -3, 'nerve': -1},
        up=2, down=3, hook=1,
        sold=('clinic', 'market'),
        onset='Your pulse comes down to somewhere sensible and stays there. '
              'Things that were urgent are still urgent and no longer feel '
              'like it, which is the entire product.',
        turn='It comes back up past where it started. Everything is urgent '
             'now, including the wallpaper.'),

    Drug(
        'blue_hour', 'Blue Hour',
        'Makes you good company. Sold in Marrow to people about to ask for '
        'something.',
        tier=2, price=700,
        high={'guile': 2, 'pretext_bonus': 3, 'legwork_bonus': 2},
        crash={'guile': -3, 'pretext_bonus': -2, 'rep_mult': 0.8},
        withdrawal={'guile': -2, 'pretext_bonus': -2},
        up=3, down=3, hook=1,
        sold=('fixer', 'market'),
        onset='You become, for a few hours, the version of yourself that '
              'people agree with. It is not that you lie better. It is that '
              'you stop transmitting.',
        turn='You transmit again, and for a while you transmit more than you '
             'did before. People finish conversations with you early and are '
             'not sure why.'),

    Drug(
        'static_line', 'Static Line',
        'Dissociative. The Chorus give it away, which should tell you '
        'something.',
        tier=2, price=1100,
        high={'composure': 6, 'trace_mult': 0.9},
        crash={'nerve': -3, 'logic': -3, 'composure': -3},
        withdrawal={'nerve': -2, 'composure': -3},
        up=1, down=4, hook=3,
        sold=('fence',),
        rider='dissociated',
        onset='You stop being the thing this is happening to and become the '
              'thing watching it happen. The Chorus have a word for this and '
              'use it constantly and you can suddenly see why.',
        turn='You come back into it all at once and from slightly the wrong '
             'angle, like sitting down in a chair that has moved.'),

    Drug(
        'wick', 'Wick',
        'Everything, briefly. Named for what it does to the thing it is in.',
        tier=2, price=1800,
        high={'reflex': 2, 'logic': 2, 'nerve': 2, 'grit': 2, 'guile': 2,
              'focus': 2, 'tempo': 1},
        crash={'reflex': -3, 'logic': -3, 'nerve': -3, 'grit': -3,
               'guile': -3, 'integrity': -6, 'focus': -2},
        withdrawal={'reflex': -2, 'logic': -2, 'nerve': -2, 'grit': -2,
                    'guile': -2},
        up=1, down=5, hook=3,
        sold=('fence',),
        onset='For about ninety seconds you are the best in the city at all '
              'of it, and you know exactly how long ninety seconds is.',
        turn='You are not the best in the city at anything, including '
             'standing. The bill for the ninety seconds is itemised and it '
             'takes most of two days to read.'),

    Drug(
        'grave_salt', 'Grave Salt',
        'Carrion make it. They will not say from what, and the answer is '
        'people.',
        tier=2, price=1400,
        high={'grit': 3, 'integrity': 8, 'composure': 2},
        crash={'grit': -4, 'integrity': -8, 'reflex': -2},
        withdrawal={'grit': -3, 'integrity': -6, 'composure': -2},
        up=2, down=4, hook=4,
        sold=('fence', 'clinic'),
        onset='You stop being interested in whether things hurt. The Shambles '
              'is full of people who took this once and are still walking '
              'around inside the decision.',
        turn='Everything you are made of files a complaint at once. Carrion '
             'sell something for this, obviously.'),

    Drug(
        'ash_tea', 'Ash Tea',
        'For the morning after. Works exactly as advertised, which is the '
        'problem.',
        tier=1, price=300,
        high={'composure': 1},
        crash={'nerve': -1, 'guile': -1},
        withdrawal={'composure': -2, 'nerve': -1},
        up=1, down=2, hook=2,
        sold=('market', 'fixer', 'fence'),
        cures_crash=True,
        onset='Whatever you were coming down from stops coming down. The room '
              'reassembles, your hands are yours again, and the cost of that '
              'is a question for later.',
        turn='Later.'),

    Drug(
        'ozymandias', 'Ozymandias Formula No. 1',
        'Sold by a vending machine that believes in it completely.',
        tier=1, price=45,
        high={'composure': 1},
        crash={'composure': -1},
        withdrawal={},
        up=2, down=2, hook=0,
        sold=('market',),
        onset='The label promises alertness, clarity, longevity, and '
              'resistance to eleven named conditions. It tastes of pears. '
              'Nothing whatsoever happens to you and you feel, on balance, '
              'slightly better about the evening.',
        turn='The feeling of having been slightly better about the evening '
             'wears off. Ozymandias would like you to know this is normal and '
             'that a second can is available.'),
    # -- the street's (D133) ----------------------------------------------
    Drug(
        'redline', 'Redline',
        'A fighter\'s stimulant, sold at the back of fences to people who '
        'are about to need it. It does not make you brave. It makes the '
        'question of bravery arrive too late to matter.',
        tier=2, price=420,
        high={'strike_damage': 2, 'strike_bonus': 1, 'grit': 1},
        crash={'strike_bonus': -2, 'reflex': -2, 'integrity': -3,
               'tick_mult': 1.1},
        withdrawal={'grit': -1, 'strike_bonus': -1},
        up=2, down=4, hook=2,
        sold=('fence',),
        onset='Something in the chest opens like a valve and the street '
              'goes bright and simple, and your hands are already closed '
              'and you do not remember closing them.',
        turn='The valve shuts. Everything you hit with is heavy now, and '
             'somewhere under the heaviness is the bill for the last two '
             'shifts, itemised.'),
    Drug(
        'numb', 'Numb',
        'A clinic painkiller, in a street dose, which is to say three of '
        'them. You are not harder to hurt. You just stop being told.',
        tier=1, price=260,
        high={'armour': 1, 'integrity': 4},
        crash={'integrity': -5, 'composure': -2, 'reflex': -1},
        withdrawal={'integrity': -2},
        up=2, down=3, hook=3,
        sold=('fence', 'clinic'),
        rider='pain_editor',
        onset='The edges of you go soft and far away, and whatever was '
              'hurting is still hurting, in another room, to somebody else.',
        turn='It all comes back at once, with interest, and it has brought '
             'the things you did while it was gone.'),
)


#: The ones there is one of (D63 e). Sold nowhere.
RELICS: tuple[Drug, ...] = (
    Drug('formula_zero', 'Ozymandias Formula No. 0',
         'The one before the one that does nothing. The machine does not '
         'list it and will not dispense it to anybody who has paid.',
         1, 45,
         high={'composure': 3, 'focus': 1},
         crash={'composure': -3, 'focus': -1},
         withdrawal={'composure': -1},
         up=2, down=2, hook=1,
         sold=(),
         onset='It tastes of the machine. Something in you stops arguing '
               'with something else in you, and the argument had been going '
               'on so long you had mistaken it for weather.',
         turn='It goes the way a radio goes when you walk out of range: '
              'gradually, and then you notice it has been gone a while.',
         unique=True,
         lore='Ozymandias, the vending machine in the Ninth, sells Formula '
              'No. 1, which does nothing and is honest about it. Formula No. '
              '0 is what it was before the lawyers, and the machine has one '
              'left, and it gave it to you at night, unprompted, the way a '
              'person who has been standing at a bus stop for nine years '
              'might give a stranger the last thing in their pocket. Nobody '
              'has told the machine it is a machine. The restocking notices '
              'taped to it are in its own handwriting.'),
    Drug('surgeons_own', 'Surgeon\'s Own',
         'What the Blue Surgeon takes, in the hours when there is a table '
         'and a person on it and the person is the kind who does not get '
         'anaesthetic. A vial, no label.',
         3, 1500,
         high={'composure': 5, 'ice_dr': 0.85},
         crash={'nerve': -3, 'focus': -2, 'tick_mult': 1.2},
         withdrawal={'composure': -3, 'nerve': -2},
         up=2, down=3, hook=2,
         sold=(),
         onset='Everything is exactly as far away as it needs to be. You '
               'could do surgery. You could watch surgery. They are about '
               'the same.',
         turn='The distance comes back in all at once, with interest, and '
              'your hands are somebody else\'s for a while.',
         unique=True,
         lore='You paid for Lark\'s life, or you arranged for it to be '
              'paid for, and the Blue Surgeon, who keeps accounts on people '
              'the way other people keep them on money, gave you this the '
              'next time you were at the clinic: a vial, no label, and the '
              'words "for the next time", which at that clinic is not a '
              'pleasantry. It is what they use to do eleven hours of '
              'careful work on somebody who is screaming. Inside a run it '
              'does the same thing, which is keep you steady while '
              'something goes through you, and afterwards it does what '
              'eleven hours of that does to the Surgeon.'),
)

DRUGS = DRUGS + RELICS

BY_KEY: dict[str, Drug] = {d.key: d for d in DRUGS}
DRUG_KEYS: tuple[str, ...] = tuple(BY_KEY)


def find(query: str) -> Drug | None:
    """A drug by key or by name, however the player typed it."""
    q = (query or '').strip().lower().replace(' ', '_')
    if q in BY_KEY:
        return BY_KEY[q]
    for drug in DRUGS:
        if drug.name.lower().startswith(q.replace('_', ' ')) or \
                drug.key.startswith(q):
            return drug
    return None


# --------------------------------------------------------------------------
# state
# --------------------------------------------------------------------------
#
# Held on the character as three dicts of drug key to number: shifts of high
# left, shifts of crash left, and habit. Kept as plain data rather than as a
# class because it has to round-trip through JSON on every autosave, and
# because every question anybody asks of it is a lookup.


#: The four things a chem block holds, all of them drug key to a count of
#: shifts, except `habit` which is a count of how far in you are. Declared so
#: that `normalise` cannot be given a block with a field nobody reads.
FIELDS = ('up', 'down', 'habit', 'dry')


def blank() -> dict:
    return {name: {} for name in FIELDS}


def normalise(chem: dict | None) -> dict:
    """A chem block with every field present and nothing bogus in it.

    Every read goes through here, because this data round-trips through JSON
    on every autosave and a save written by a build that shipped a drug this
    one does not is a `KeyError` in the middle of somebody's evening.
    """
    raw = dict(chem or {})
    return {name: dict(_counts(raw.get(name))) for name in FIELDS}


def _counts(raw) -> dict[str, int]:
    """Drug key to positive integer, discarding anything that is not that.

    Defensive about the value as well as the key. Both halves have to survive
    a save this build did not write: a drug that has since been renamed is the
    expected case, and a number that is not a number is the hand-edited one,
    and neither is worth a traceback in front of somebody who just wanted to
    load their character.
    """
    out: dict[str, int] = {}
    for key, value in (raw or {}).items():
        if key not in BY_KEY:
            continue
        try:
            count = int(value)
        except (TypeError, ValueError):
            continue
        if count > 0:
            out[key] = count
    return out


def habit(chem: dict, key: str) -> int:
    return int(normalise(chem)['habit'].get(key, 0))


def is_up(chem: dict, key: str) -> bool:
    return normalise(chem)['up'].get(key, 0) > 0


def is_down(chem: dict, key: str) -> bool:
    return normalise(chem)['down'].get(key, 0) > 0


def tolerance(level: int) -> float:
    """How much of the high survives at this habit. Never nothing."""
    return max(TOLERANCE_FLOOR, 1.0 - 0.065 * max(0, level))


def severity(level: int) -> float:
    """How much bigger the crash is at this habit."""
    return 1.0 + CRASH_PER_HABIT * max(0, level)


def _scaled(effects: dict, factor: float) -> dict:
    """Scale a modifier block, keeping multiplicative keys around 1.0.

    An additive `-2` at 1.5 severity is `-3`. A multiplicative `1.2` at the
    same severity is `1.3`, not `1.8`: scaling a rate by scaling the whole
    number is how a 20% penalty quietly becomes an 80% one.
    """
    from . import effects as fx
    out: dict = {}
    for key, value in effects.items():
        if key in fx.MULTIPLICATIVE:
            out[key] = 1.0 + (value - 1.0) * factor
        else:
            out[key] = value * factor
    return out


def effects(chem: dict | None) -> dict:
    """Everything currently in the bloodstream, as one modifier block."""
    from . import effects as fx
    state = normalise(chem)
    parts: list[dict] = []
    for key, drug in BY_KEY.items():
        level = state['habit'].get(key, 0)
        if state['up'].get(key, 0) > 0:
            parts.append(_scaled(drug.high, tolerance(level)))
        elif state['down'].get(key, 0) > 0:
            parts.append(_scaled(drug.crash, severity(level)))
        elif level >= WITHDRAWAL_AT:
            # The part that matters. Not using is now its own condition, and
            # it scales with how far in you are rather than with the dose.
            parts.append(_scaled(drug.withdrawal,
                                 level / HABIT_MAX + 0.5))
    return fx.merge(*parts) if parts else {}


def riders(chem: dict | None) -> set[str]:
    state = normalise(chem)
    return {BY_KEY[k].rider for k, left in state['up'].items()
            if left > 0 and BY_KEY[k].rider}


def dose(chem: dict, key: str) -> dict:
    """Take one. Returns the new chem block; the caller narrates it."""
    state = normalise(chem)
    drug = BY_KEY[key]
    state['up'][key] = drug.up
    state['down'].pop(key, None)
    if drug.hook:
        state['habit'][key] = min(HABIT_MAX,
                                  state['habit'].get(key, 0) + drug.hook)
    if drug.cures_crash:
        # It does what it says. What it does not say is that ending a
        # comedown early does not end it, it moves it, and the thing it moves
        # it into is the habit.
        for other in list(state['down']):
            if other == key:
                continue
            state['down'].pop(other)
            state['habit'][other] = min(HABIT_MAX,
                                        state['habit'].get(other, 0) + 1)
    return state


def advance(chem: dict, shifts: int = 1) -> tuple[dict, list[str]]:
    """One or more shifts of chemistry. Returns (state, lines to print).

    The lines are the entire teaching surface of this system. A player who
    doses and reads nothing has taken a stat buff; a player who is told, in
    the shift it happens, that the thing has turned and that their hands are
    not where they think, has learned what a comedown is.
    """
    state = normalise(chem)
    told: list[str] = []
    for _ in range(max(1, shifts)):
        for key in list(state['up']):
            state['up'][key] -= 1
            if state['up'][key] <= 0:
                del state['up'][key]
                drug = BY_KEY[key]
                state['down'][key] = drug.down
                told.append(f'[warn]{drug.name} turns.[/] {drug.turn}')
        for key in list(state['down']):
            state['down'][key] -= 1
            if state['down'][key] <= 0:
                del state['down'][key]
                told.append(f'[dim]The {BY_KEY[key].name} has finished with '
                            f'you.[/]')
        # Habit sheds only on a shift where nothing is in you and nothing is
        # leaving. Using anything at all holds every habit where it is, which
        # is why a person with two of these has a much harder time than a
        # person with one.
        if not state['up'] and not state['down']:
            for key in list(state['habit']):
                run = state['dry'].get(key, 0) + 1
                if run >= CLEAN_SHIFTS:
                    run = 0
                    state['habit'][key] -= 1
                    if state['habit'][key] <= 0:
                        del state['habit'][key]
                        state['dry'].pop(key, None)
                        told.append(f'[ok]You have not wanted '
                                    f'{BY_KEY[key].name} in a while, and you '
                                    f'notice that you have not.[/]')
                        continue
                state['dry'][key] = run
        else:
            # Anything at all in you resets every clock. Two habits are much
            # worse than twice one habit, because using either holds both.
            state['dry'] = {}
    return state, told


def withdrawing(chem: dict | None) -> list[str]:
    """Drug keys whose withdrawal is currently acting on you."""
    state = normalise(chem)
    return [k for k, level in state['habit'].items()
            if level >= WITHDRAWAL_AT
            and not state['up'].get(k) and not state['down'].get(k)]


#: How far gone, in words. Read out by `chem` and by the character sheet.
def depth(level: int) -> str:
    if level <= 0:
        return 'clean'
    if level < WITHDRAWAL_AT:
        return 'occasional'
    if level < 7:
        return 'dependent'
    if level < HABIT_MAX:
        return 'in trouble'
    return 'as far in as it goes'
