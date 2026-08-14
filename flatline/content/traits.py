"""Traits: the axis that makes two identical builds play differently.

Skills say what you can do. Chrome says what you are made of. Traits say what
you are *like*, and they are the only customisation axis where the pool is
much larger than what you can take. That asymmetry is the entire point: with
thirty on offer and five slots at most, no two characters are picking the same
five, and the interesting question stops being "what is optimal" and becomes
"what is this person".

Three rules this file is written under:

**Every trait cuts both ways.** Same rule as chrome (D11): if it cannot be
given an honest drawback it does not ship. A trait that is purely good is a
trait everybody takes, and a pick everybody makes is not a choice.

**Traits change decisions, not numbers.** `+1 Logic` is not in here. "You
cannot stop reading logs" is, because it makes you slower and better informed
and the player has to decide whether that trade suits them.

**They are permanent.** You choose two at creation and earn more as you go,
and none of them can be taken back. That is what makes a trait part of who
somebody is rather than a loadout.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: Chosen at creation. Small, because the first two should feel like a
#: definition rather than a shopping list.
CREATION_PICKS = 2
#: Runs between earned picks, and the ceiling.
EARN_EVERY = 6
MAX_TRAITS = 5

#: Grouping, purely for how the list reads.
GROUPS = ('temperament', 'habit', 'history', 'body')

GROUP_TITLES = {
    'temperament': 'Temperament',
    'habit': 'Habits',
    'history': 'History',
    'body': 'The body you are in',
}


@dataclass(frozen=True, slots=True)
class Trait:
    key: str
    name: str
    #: What it is, in the fiction. Second person.
    blurb: str
    group: str
    effects: dict = field(default_factory=dict)
    #: The honest downside, in the fiction.
    drawback: str = ''
    #: The honest downside, in numbers.
    penalty: dict = field(default_factory=dict)
    #: Engine-implemented special behaviour. Must be in `RIDERS`.
    rider: str = ''
    #: Traits that cannot be taken alongside this one.
    excludes: tuple[str, ...] = ()


TRAITS: tuple[Trait, ...] = (
    # -- temperament ------------------------------------------------------
    Trait('impatient', 'Impatient',
          'You have never in your life waited for something to finish when '
          'you could start the next thing instead.',
          'temperament',
          effects={'tick_mult': 0.88},
          drawback='You also never wait for the tell. Countermeasures get '
                   'their strike in before you have finished reacting.',
          penalty={'tell_lead': -1},
          excludes=('methodical', 'quietworker')),
    Trait('methodical', 'Methodical',
          'You do things in an order, and the order is the reason they work.',
          'temperament',
          effects={'residue_mult': 0.78, 'crack_bonus': 1},
          drawback='Order takes time. Everything you do costs more of it than '
                   'it costs anybody else.',
          penalty={'tick_mult': 1.12},
          excludes=('impatient',)),
    Trait('cold', 'Cold',
          'Whatever the thing is that makes people\'s hands shake, you were '
          'not issued one.',
          'temperament',
          effects={'composure': 5},
          drawback='People notice. Every social read you attempt starts from '
                   'somebody deciding they do not quite like you.',
          penalty={'pretext_bonus': -2}),
    Trait('twitchy', 'Twitchy',
          'You react before you decide, which is right about as often as it '
          'is wrong.',
          'temperament',
          effects={'evade_bonus': 3},
          drawback='Reacting before deciding is exactly as bad as it sounds '
                   'when the thing you reacted to was nothing.',
          penalty={'composure': -3}),
    Trait('greedy', 'Greedy',
          'You have never once left a network without checking the last node, '
          'and you know precisely what that habit has cost you.',
          'temperament',
          effects={'legwork_bonus': 1},
          drawback='You cannot leave. Jacking out while there is anything '
                   'unclaimed on a node you hold costs you an extra tick of '
                   'deciding.',
          penalty={},
          rider='cannot_leave',
          excludes=('disciplined',)),
    Trait('disciplined', 'Disciplined',
          'You take what you were paid for and you go. Everybody who works '
          'with you says the same thing about it, in the same slightly '
          'disappointed tone.',
          'temperament',
          effects={'focus': 2, 'trace_mult': 0.92},
          drawback='You are not curious, and curiosity is where the good '
                   'material is. Assets you were not sent for are worth less '
                   'to you: you do not know who to sell them to.',
          penalty={'pay_mult': 0.94},
          excludes=('greedy',)),

    # -- habits -----------------------------------------------------------
    Trait('logreader', 'Cannot stop reading logs',
          'Everybody else takes the file. You read the file, and then you '
          'read what the file was doing there.',
          'habit',
          effects={'skill_forensics': 1, 'scan_depth': 1},
          drawback='It takes as long as it takes, and it takes longer than '
                   'anybody else needs.',
          penalty={'tick_mult': 1.08}),
    Trait('overprepared', 'Overprepared',
          'You have a program for it. You have three programs for it. Two of '
          'them are for a situation that has never once occurred.',
          'habit',
          effects={'memory': 2},
          drawback='All that preparation is weight. You start every run one '
                   'tick behind, sorting through what you brought.',
          penalty={},
          rider='slow_start',
          excludes=('improviser',)),
    Trait('improviser', 'Improviser',
          'You have never packed correctly for anything and it has never '
          'stopped you.',
          'habit',
          effects={'crack_bonus': 2, 'evade_bonus': 1},
          drawback='Improvisation is loud. You are working the problem in '
                   'front of everybody.',
          penalty={'noise_mult': 1.2},
          excludes=('overprepared',)),
    Trait('quietworker', 'Works quietly',
          'You were taught by somebody who was frightened, and it took.',
          'habit',
          effects={'noise_mult': 0.8},
          drawback='Quiet is slow, and you cannot make yourself hurry even '
                   'when hurrying is obviously correct.',
          penalty={'tick_mult': 1.1},
          excludes=('impatient',)),
    Trait('hoarder', 'Hoarder',
          'You have never deleted anything, sold anything at a loss, or '
          'thrown away a component that still had one function left in it.',
          'habit',
          effects={'repair_mult': 0.65},
          drawback='Your deck is full of things that nearly work. Damaged '
                   'components degrade further between runs unless you fix '
                   'them.',
          penalty={},
          rider='rot'),
    Trait('showoff', 'Shows off',
          'The job is not the point. Doing the job in a way somebody will '
          'talk about is the point.',
          'habit',
          effects={'rep_mult': 1.25, 'pay_mult': 1.08},
          drawback='People talk about it. That is the whole problem with '
                   'people talking about it.',
          penalty={'heat_mult': 1.3}),
    Trait('ghostly', 'Leaves nothing',
          'You have a routine at the end of every run and you have never once '
          'skipped it, including the time you were bleeding.',
          'habit',
          effects={'residue_mult': 0.65},
          drawback='The routine costs what it costs, every time, whether or '
                   'not you have the seconds for it.',
          penalty={'tick_mult': 1.06, 'focus': -1}),

    # -- history ----------------------------------------------------------
    Trait('inside', 'Was inside once',
          'Two years at a desk somewhere with a badge and a parking space. '
          'You still know the shape of a corporate morning.',
          'history',
          effects={'pretext_bonus': 3},
          drawback='Somebody in that building still recognises your gait, and '
                   'corporate networks hold your details on file somewhere.',
          penalty={'heat_mult': 1.15}),
    Trait('taught', 'Somebody taught you',
          'You did not work this out alone, and whoever showed you is still '
          'out there being owed something.',
          'history',
          effects={'skill_intrusion': 1},
          drawback='They are owed something. Favours cost you more, because '
                   'the street knows you are already carrying one.',
          penalty={},
          rider='owes_a_favour',
          excludes=('selftaught',)),
    Trait('selftaught', 'Nobody taught you',
          'Everything you know, you know because you broke it first.',
          'history',
          effects={'skill_hardware': 1, 'repair_mult': 0.8},
          drawback='There are gaps, and they are in places other people do '
                   'not have gaps. Anything genuinely unfamiliar goes badly.',
          penalty={'crypto_bonus': -2},
          excludes=('taught',)),
    Trait('survivor', 'Came back from one',
          'You have flatlined once, briefly, on a table, and somebody '
          'expensive brought you back. You do not talk about it and you have '
          'not been quite the same since.',
          'history',
          effects={'composure': 6, 'integrity': 4},
          drawback='Whatever they used to restart you has never entirely '
                   'stopped. You heal slower than anybody should.',
          penalty={},
          rider='slow_healing'),
    Trait('marked', 'Somebody is looking',
          'There is a person in this city who has a photograph of you and a '
          'reason, and you do not know which person.',
          'history',
          effects={'evade_bonus': 2, 'tell_lead': 1},
          drawback='They are looking. Heat on you decays more slowly than it '
                   'does on anybody with a clean start.',
          penalty={'heat_mult': 1.2}),
    Trait('known', 'Known in Marrow',
          'You drink somewhere everybody drinks and you have never once been '
          'asked to leave.',
          'history',
          effects={'price_mult': 0.9, 'rep_mult': 1.15},
          drawback='Everybody knows where you drink, which includes everybody '
                   'you would rather did not.',
          penalty={},
          rider='findable'),

    # -- the body you are in ----------------------------------------------
    Trait('steadyhands', 'Steady hands',
          'Surgeons have said things about your hands that you have chosen '
          'not to think about too hard.',
          'body',
          effects={'crypto_bonus': 2, 'skill_cryptography': 1},
          drawback='Precision is not speed. You have never done anything '
                   'quickly in your life.',
          penalty={'tempo': -1},
          excludes=('fast',)),
    Trait('fast', 'Fast',
          'Whatever the physical component of this is, you have more of it '
          'than the people who taught you.',
          'body',
          effects={'tempo': 1},
          drawback='Fast hands and a fast temper come out of the same place. '
                   'Anything that rewards patience does not reward you.',
          penalty={'crack_bonus': -1, 'pretext_bonus': -2},
          excludes=('steadyhands',)),
    Trait('tolerant', 'High tolerance',
          'Your nervous system has been through things and has stopped '
          'complaining about most of them.',
          'body',
          effects={'ice_dr': 0.85, 'bandwidth': 2},
          drawback='Tolerance is not immunity, it is a lack of warning. You '
                   'do not notice damage until there is a lot of it.',
          penalty={'composure': -2}),
    Trait('sensitive', 'Reads the net',
          'You feel the shape of a network before you have finished '
          'connecting to it. Nobody has explained this and you have stopped '
          'asking.',
          'body',
          effects={'tell_lead': 1, 'scan_depth': 1},
          drawback='Feeling all of it means feeling all of it. Everything in '
                   'there is louder for you than it is for anybody else.',
          penalty={'ice_dr': 1.2}),
    Trait('insomniac', 'Does not sleep',
          'Three hours, most nights, for eleven years. You have made your '
          'peace with it and it has not made its peace with you.',
          'body',
          effects={'focus': 2},
          drawback='Rest does you less good than it does anybody else, and '
                   'you carry damage between runs.',
          penalty={},
          rider='poor_rest'),
    Trait('clean', 'No chrome at all',
          'You have never had anything put in you and you have opinions about '
          'people who have.',
          'body',
          effects={'pretext_bonus': 3, 'price_mult': 0.92, 'integrity': 3},
          drawback='You are running on what you were born with, against '
                   'people who are not. Nothing can be installed while you '
                   'hold this.',
          penalty={},
          rider='no_chrome',
          excludes=('wired',)),
    Trait('wired', 'Wired for it',
          'Your interface latency was measured once, for a study, and the '
          'person doing the measuring asked you to repeat it.',
          'body',
          effects={'tick_mult': 0.92, 'bandwidth': 1},
          drawback='The same coupling that makes you fast makes you '
                   'reachable. Everything that comes back up the wire arrives '
                   'a little more intact.',
          penalty={'ice_dr': 1.15},
          excludes=('clean',)),
)

BY_KEY: dict[str, Trait] = {t.key: t for t in TRAITS}
TRAIT_KEYS: tuple[str, ...] = tuple(BY_KEY)

#: Riders the engine implements. A trait naming anything else is a
#: validation error, per the same rule that governs chrome and origins.
RIDERS: frozenset[str] = frozenset({
    'cannot_leave', 'slow_start', 'rot', 'owes_a_favour', 'slow_healing',
    'findable', 'poor_rest', 'no_chrome',
})


def available(taken, char=None) -> list[Trait]:
    """Traits still open to somebody, respecting exclusions."""
    held = set(taken)
    blocked: set[str] = set()
    for key in held:
        trait = BY_KEY.get(key)
        if trait:
            blocked.update(trait.excludes)
    for trait in TRAITS:
        if held & set(trait.excludes):
            blocked.add(trait.key)
    out = []
    for trait in TRAITS:
        if trait.key in held or trait.key in blocked:
            continue
        if (trait.key == 'clean' and char is not None
                and getattr(char, 'installed', None)):
            continue  # you cannot become somebody who never had chrome
        out.append(trait)
    return out


def earned(runs: int) -> int:
    """How many traits a character has earned by now, creation excluded."""
    return min(MAX_TRAITS - CREATION_PICKS, runs // EARN_EVERY)
