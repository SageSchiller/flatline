"""The street, as a place things happen to you (D65).

The net is half the game and the street is the other half, and until now
the street could shake you down, hurt you a little, take the deck apart and
burn a name, and it could not kill you. The author's direction: the idea
that nothing ends you unless you are jacked in works against the setting.
So the street is real now. It can hurt you, in Integrity, the same number
the net hurts; it can cost you money, chrome and a name; and at the top of
the ladder it can kill you, under the same contract as black ICE (D6):
telegraphed first, then absolute. Nobody dies on the street without having
been told, in so many words, that next time they would not be asking.

You do not fight. There are no guns in your hands and never will be (the
locked direction stands). You get out of it the way people who live here
get out of it: you run, you talk, you pay, or you stand there and take it,
and two skills decide how well each of those goes. The checks are printed
like every other check in the game.

An encounter is a `Question` (D50): a prompt, a handful of answers, the
next line you type. It never happens inside a run.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: Which answers are checks, and which skill and attribute each reads.
#: `pay` is money and no check; `none` is a choice with nothing to roll.
CHECKS: dict[str, tuple[str, str, str]] = {
    # answer -> (attribute, skill x2, second skill x1)
    'run': ('reflex', 'fieldcraft', 'streetcraft'),
    'talk': ('guile', 'streetcraft', 'subterfuge'),
    'stand': ('grit', 'fieldcraft', 'nerve'),
    'careful': ('reflex', 'fieldcraft', 'streetcraft'),
}

#: Base resistance by tier, before the district's danger (a point per
#: twenty, when it is somebody's people). Set so that an untrained runner
#: with an ordinary attribute has about an even chance at the bottom rung
#: and none at the top, and a runner with Streetcraft or Fieldcraft at 4
#: usually walks away from the kind that kills. The street is a skill.
RESISTANCE = {1: 3, 2: 6, 3: 9, 4: 14}

#: What paying costs, by tier.
PAY = {1: 250, 2: 500, 3: 900, 4: 1600}

TIER_NAMES = {1: 'a lean', 2: 'a press', 3: 'a taking', 4: 'the kind that kills'}


@dataclass(frozen=True, slots=True)
class Outcome:
    #: Second person, present tense. What happens.
    text: str
    #: Integrity lost, as an inclusive range.
    hurt: tuple[int, int] = (0, 0)
    #: Share of your credits lost, 0..1. Negative is money in.
    credits: float = 0.0
    #: Heat with the faction, when there is one. Negative cools.
    heat: int = 0
    #: An earned mark, or ''.
    mark: str = ''
    #: A deck component takes a level.
    deck: bool = False
    #: Can kill, if the encounter is tier 4 and you were warned. Otherwise
    #: the blow leaves you at one and *is* the warning.
    lethal: bool = False


@dataclass(frozen=True, slots=True)
class Option:
    key: str
    label: str
    #: 'run' | 'talk' | 'stand' | 'careful' | 'pay' | 'none'
    check: str
    win: Outcome
    lose: Outcome


@dataclass(frozen=True, slots=True)
class Encounter:
    key: str
    name: str
    #: 1 a lean, 2 a press, 3 a taking, 4 the kind that kills.
    tier: int
    #: 'faction' (somebody's people, `{fac}` fills) or 'street' (nobody's).
    who: str
    tone: str
    #: Second person, present tense. `{fac}` and `{district}` fill.
    setup: str
    options: tuple[Option, ...]
    #: Story rules, all of which must hold. Empty for ordinary danger.
    requires: tuple[str, ...] = ()
    #: Phases it can happen in. Empty means any.
    phases: tuple[str, ...] = ()


ENCOUNTERS: tuple[Encounter, ...] = (
    # -- somebody's people ---------------------------------------------------
    Encounter(
        'toll', 'The price of the street', 1, 'faction', 'grim',
        'Two of {fac}\'s people step off the kerb in {district} and fall in '
        'either side of you, not touching, matching your pace. "You know '
        'whose street this is." It is not a question and it is not, yet, a '
        'threat. It is a price, being named.',
        (
            Option('run', 'Take the next corner fast', 'run',
                   Outcome('You take the corner and the stairwell after it '
                           'and they do not bother. It was a price, not a '
                           'chase, and you were not worth the chase today.'),
                   Outcome('You take the corner and one of them is already '
                           'at the bottom of the stairwell, and the other '
                           'arrives behind you, and it costs more than the '
                           'price would have.', hurt=(1, 3), credits=0.2)),
            Option('talk', 'Tell them whose you are', 'talk',
                   Outcome('You say a name, not yours, in the right tone, and '
                           'the pace either side of you slackens, and they '
                           'peel off at the next junction without a word.'),
                   Outcome('You say a name and it is the wrong name, or the '
                           'right one said wrong, and they stop, and you pay '
                           'for the pause.', hurt=(1, 2), credits=0.25)),
            Option('pay', 'Pay the price', 'pay',
                   Outcome('You pay. They take it without counting it, which '
                           'is how you know the amount was never the point, '
                           'and peel off.'),
                   Outcome('', )),
            Option('stand', 'Stop walking', 'stand',
                   Outcome('You stop, and so do they, and for a moment it is '
                           'three people standing in a street, and then it is '
                           'you standing in a street. They did not want it '
                           'badly enough. You did not blink.'),
                   Outcome('You stop and they do not, and what happens next '
                           'is brief and specific and leaves you against a '
                           'wall with your pockets lighter.',
                           hurt=(2, 4), credits=0.3)),
        )),
    Encounter(
        'lean', 'Where you were last night', 2, 'faction', 'grim',
        'Three of {fac}\'s people, one of them with a tablet, in a doorway '
        'in {district} you were always going to walk past. The one with the '
        'tablet has a photograph on it. It is not a good photograph. It is '
        'good enough. "Where were you, last night?"',
        (
            Option('talk', 'Have been somewhere else', 'talk',
                   Outcome('You were somewhere else. You name the place and '
                           'the people and the thing you were doing, and the '
                           'one with the tablet writes it down, and it will '
                           'check out, because you chose it to.'),
                   Outcome('You were somewhere else and it does not hold, '
                           'and they walk you to a room and explain, with '
                           'their hands, what holding means.',
                           hurt=(2, 5), heat=-6, mark='bounty_mark')),
            Option('pay', 'Buy the photograph', 'pay',
                   Outcome('The photograph has a price. You pay it. The '
                           'tablet goes away. The photograph does not, but '
                           'tonight it is not in anybody\'s hand.', heat=-8),
                   Outcome('')),
            Option('stand', 'Say nothing at all', 'stand',
                   Outcome('You say nothing, and keep saying it, and they are '
                           'on a clock too. They let you go with a look that '
                           'says the photograph is not going anywhere.'),
                   Outcome('You say nothing and they fill the silence with '
                           'something that leaves a mark, and then you still '
                           'say nothing, and that is the only part of the '
                           'night you are proud of.',
                           hurt=(3, 6), heat=-4, mark='bounty_mark')),
            Option('run', 'Go, now', 'run',
                   Outcome('You are moving before the question finishes and '
                           'the doorway is behind you, and nobody with a '
                           'tablet runs.'),
                   Outcome('You run, and the one without the tablet was '
                           'waiting for exactly that, and it is a short run.',
                           hurt=(3, 6), credits=0.2)),
        )),
    Encounter(
        'press', 'The van', 3, 'faction', 'grim',
        'Four of {fac}\'s, and a van with the side door already open, in '
        '{district}, at an hour nobody will remember seeing anything. One of '
        'them says your alias. The name, the one you have been using, in a '
        'voice that has said it before to somebody else.',
        (
            Option('run', 'Run', 'run',
                   Outcome('You run, and they are four and you are one and '
                           'the one knows the stairwells, and the van is the '
                           'wrong way up a one-way street, and you are gone.',
                           hurt=(0, 1)),
                   Outcome('You run and they have done this before, and the '
                           'van is where you end up, and what happens in the '
                           'van happens to the deck as well as to you.',
                           hurt=(4, 8), deck=True, heat=-10)),
            Option('talk', 'Make it a conversation', 'talk',
                   Outcome('You talk, fast and specific, and somewhere in it '
                           'is a thing they did not know and want to, and '
                           'the van door closes without you in it. You owe '
                           'somebody a conversation now.', heat=-6),
                   Outcome('You talk and they let you, all the way into the '
                           'van, and then the talking is theirs.',
                           hurt=(4, 7), credits=0.4, heat=-8)),
            Option('pay', 'Pay, all of it', 'pay',
                   Outcome('You pay what they ask, which is most of what you '
                           'have, and the van door closes without you in it, '
                           'and one of them says the alias again, softer, as '
                           'a reminder that they still have it.', heat=-12),
                   Outcome('')),
            Option('stand', 'Get in', 'stand',
                   Outcome('You get in. It is a conversation with the deck on '
                           'the table between you and it is long, and at the '
                           'end of it they let you out somewhere else with '
                           'the deck, and it was filing, not finishing.',
                           hurt=(2, 4), heat=-15, mark='bounty_mark'),
                   Outcome('You get in, and the deck comes out of the bag, '
                           'and they do something specific to it while you '
                           'watch, and then to you while it watches.',
                           hurt=(5, 9), deck=True, heat=-10,
                           mark='bounty_mark')),
        )),
    Encounter(
        'finish', 'They have stopped asking', 4, 'faction', 'grim',
        'There is no price and no photograph and no van. There is a quiet '
        'stretch of {district} that is quieter than it should be, and '
        '{fac}\'s people at both ends of it, and nobody says your alias, '
        'because they are past saying it. The number attached to your name '
        'is bigger than anything you are carrying. This is what the number '
        'is for.',
        (
            Option('run', 'Run, and mean it', 'run',
                   Outcome('You run the way you have never run, through a '
                           'building you did not know had a back, and you '
                           'are hit once, going, and you keep going, and the '
                           'street behind you is shouting and you are not '
                           'in it.', hurt=(3, 6)),
                   Outcome('You run and there is nowhere, and they are not '
                           'hurried, and it is not filing.',
                           hurt=(9, 14), lethal=True)),
            Option('talk', 'Say the one thing that might matter', 'talk',
                   Outcome('You say it. A name, a place, a thing they want '
                           'more than they want you, and you watch it land, '
                           'and they have a different evening than they '
                           'planned, and you have an evening.', hurt=(1, 3),
                           heat=-20),
                   Outcome('You say it and it is not enough, and they let you '
                           'finish, which is the courtesy.',
                           hurt=(9, 14), lethal=True)),
            Option('stand', 'Stand there', 'stand',
                   Outcome('You stand. You do not run and you do not talk and '
                           'something about it, the sheer stupidity of it, '
                           'makes the nearest one laugh, and the laugh goes '
                           'down the street, and it is not tonight. It will '
                           'be another night. But it is not tonight.',
                           hurt=(2, 5)),
                   Outcome('You stand there.', hurt=(10, 16), lethal=True)),
        )),
    # -- nobody's people -----------------------------------------------------
    Encounter(
        'tail', 'Somebody behind you', 1, 'street', 'grim',
        'There is somebody behind you in {district}, and has been for three '
        'streets, and they are not good at it, which is worse than if they '
        'were, because the ones who are not good at it are usually not the '
        'ones who decided to do it.',
        (
            Option('run', 'Lose them', 'run',
                   Outcome('Two corners and a market and they are gone, or '
                           'you are, which is the same thing from where you '
                           'stand.'),
                   Outcome('Two corners and they are still there, closer, '
                           'and a second one has arrived, and this is now a '
                           'different evening.', hurt=(1, 3), credits=0.15)),
            Option('talk', 'Turn round and ask', 'talk',
                   Outcome('You turn round and ask, and they are so startled '
                           'they tell you: a name, not yours, and somebody '
                           'who paid for a description, and you thank them '
                           'and mean it and they go.'),
                   Outcome('You turn round and ask and they do not answer, '
                           'and the person behind *them* does, with a hand.',
                           hurt=(1, 3))),
            Option('stand', 'Wait for them at a corner', 'stand',
                   Outcome('You wait at a corner and they come round it and '
                           'into you, and you are bigger than they expected, '
                           'or stiller, and they go back the way they came '
                           'without finishing the sentence they started.'),
                   Outcome('You wait at a corner and they come round it with '
                           'something in their hand.', hurt=(2, 4))),
        )),
    Encounter(
        'knives', 'Kids', 2, 'street', 'grim',
        'Four of them, none over sixteen, in a covered walkway in {district} '
        'with the lights out at one end. One has a knife and is holding it '
        'wrong, and you find that is the frightening part. They want the bag. '
        'They do not know what is in the bag. That is also the frightening '
        'part.',
        (
            Option('run', 'Back the way you came', 'run',
                   Outcome('You go back the way you came, fast, and they are '
                           'kids, and kids do not follow into the light.'),
                   Outcome('You go back the way you came and the lights are '
                           'out at that end too, which was the plan, and the '
                           'knife is held wrong right into you.',
                           hurt=(3, 6), credits=0.3)),
            Option('talk', 'Talk to the one with the knife', 'talk',
                   Outcome('You talk to the one with the knife, not about the '
                           'knife, and by the end of it he is holding it '
                           'right and pointing it at the floor and one of the '
                           'others has started to laugh, and you walk out.'),
                   Outcome('You talk and the one with the knife is not the '
                           'one who decides, and the one who decides has '
                           'decided.', hurt=(2, 5), credits=0.35)),
            Option('pay', 'Give them what is in your pockets', 'pay',
                   Outcome('You give them what is in your pockets and not '
                           'what is in the bag, and they are pleased with the '
                           'pockets, and they are sixteen, and you walk out '
                           'with the deck.'),
                   Outcome('')),
            Option('stand', 'Stand your ground', 'stand',
                   Outcome('You stand and you are an adult and it turns out '
                           'that still counts for something in a covered '
                           'walkway, and the knife goes away, and so do '
                           'they, swearing.'),
                   Outcome('You stand, and they are four, and you are an '
                           'adult, and that counts for exactly as long as it '
                           'takes.', hurt=(3, 7), credits=0.25)),
        )),
    Encounter(
        'stair', 'The dark stairwell', 2, 'street', 'grim',
        'A stairwell in {district} with the lights out, which you have taken '
        'before, in the light, and there is a step missing somewhere in it, '
        'and the stairwell knows where and you do not.',
        (
            Option('careful', 'Take it slowly, by the wall', 'careful',
                   Outcome('You take it by the wall, a hand on the rail, a '
                           'foot feeling for each step, and the missing one '
                           'is the eleventh, and you step over it, and you '
                           'have lost a minute and nothing else.'),
                   Outcome('You take it by the wall and the missing step is '
                           'two steps, and the second one is the one you '
                           'were not feeling for.', hurt=(2, 4))),
            Option('run', 'Take it fast and trust your feet', 'run',
                   Outcome('You take it fast and your feet know, somehow, '
                           'and you are at the bottom before the thought '
                           'finishes.'),
                   Outcome('You take it fast and the eleventh step is not '
                           'there and the landing is, eventually.',
                           hurt=(3, 7), deck=True)),
        ),
        phases=('night',)),
    Encounter(
        'crossed', 'Somebody you crossed', 4, 'street', 'grim',
        'Not anybody\'s people. One person, in {district}, who has been '
        'waiting for you specifically, and who you would recognise if you '
        'had ever looked at them when it mattered. They have something in '
        'their hand and nothing in their face. You crossed them. You may '
        'not remember how. They do.',
        (
            Option('run', 'Run', 'run',
                   Outcome('You run, and they are one person and not young, '
                           'and you are not, tonight, and it is over in a '
                           'street and a half.', hurt=(1, 3)),
                   Outcome('You run and it turns out they knew you would, and '
                           'which way, and that is all it takes.',
                           hurt=(9, 13), lethal=True)),
            Option('talk', 'Ask them what you did', 'talk',
                   Outcome('You ask. They tell you. It takes a while and you '
                           'had, in fact, forgotten, and at the end of it '
                           'they are crying and you are still alive and you '
                           'do not think those two things are unrelated.',
                           hurt=(0, 2)),
                   Outcome('You ask, and they tell you, and then they show '
                           'you.', hurt=(9, 14), lethal=True)),
            Option('stand', 'Let them decide', 'stand',
                   Outcome('You stand there and let them, and it is a long '
                           'moment, and they decide, and it is not this, and '
                           'they go, and you do not know what you would have '
                           'done.', hurt=(2, 5)),
                   Outcome('You stand there and let them decide.',
                           hurt=(10, 16), lethal=True)),
        ),
        requires=('heat:45',)),
    Encounter(
        'soup', 'Somebody with a pot', 1, 'street', 'wry',
        'A woman with a pot on a trolley in {district}, ladling something '
        'into paper cups for anybody who stops, and she has seen you and '
        'she has seen the way you are walking, and she is holding out a '
        'cup. It is not a transaction. It is soup.',
        (
            Option('take', 'Take the cup', 'none',
                   Outcome('It is soup. It is hot and it is mostly lentils and '
                           'you drink it standing up and she refills it '
                           'without asking, and you walk on a little '
                           'straighter than you arrived.', hurt=(-2, -2)),
                   Outcome('')),
            Option('decline', 'Keep walking', 'none',
                   Outcome('You keep walking. She does not mind. The cup goes '
                           'to the next person, who does not keep walking.'),
                   Outcome('')),
        )),
    # -- the city reads back (D65): decisions that come to find you ----------
    Encounter(
        'backqueue', 'The back of the queue, closer', 2, 'street', 'grim',
        'Two of Carrion\'s, the two who stand at the back of the Hall\'s '
        'queue, in {district}, not at the back of anything now. "You carried '
        'the kettle. Then you took our money. We are not sure which one you '
        'are." They would like to find out.',
        (
            Option('talk', 'Tell them which one you are', 'talk',
                   Outcome('You tell them. It is the version they wanted, '
                           'said the way they wanted it, and they are '
                           'satisfied in the way people are satisfied by a '
                           'thing they already believed.'),
                   Outcome('You tell them and it is the wrong version, and '
                           'they show you, in a doorway, which one they have '
                           'decided you are.', hurt=(2, 5), credits=0.2)),
            Option('run', 'Go', 'run',
                   Outcome('You go, and the Hall taught you nothing about '
                           'running but the Shambles did.'),
                   Outcome('You go, and they were ready for that, because '
                           'they had decided which one you are.',
                           hurt=(3, 6))),
            Option('pay', 'Pay them to have decided', 'pay',
                   Outcome('You pay, and they decide you are the one who '
                           'pays, and that is a kind of answer.'),
                   Outcome('')),
        ),
        requires=('soup_carrion',)),
    Encounter(
        'paperboy', 'Somebody with a paper', 1, 'street', 'wry',
        'Somebody from the Stacks, ink to the elbow, in {district}, holding '
        'out a paper you did not ask for. Your handle is on the front of it. '
        'Not the real one. The one you have used. Above the fold.',
        (
            Option('talk', 'Ask what it costs to not be in the next one', 'talk',
                   Outcome('They name a price, and it is small, and it is '
                           'not really about money, and you say the right '
                           'thing about Ines, and the paper goes back under '
                           'their arm.'),
                   Outcome('They name a price and you say the wrong thing '
                           'about Ines, and the next edition is worse, and '
                           'somebody who reads it finds you.',
                           hurt=(1, 3), heat=0)),
            Option('stand', 'Take the paper and read it', 'stand',
                   Outcome('You take it and read it standing there, all of '
                           'it, and hand it back, and say it is mostly right, '
                           'and they look at you differently.'),
                   Outcome('You take it and read it and somebody behind you '
                           'reads it over your shoulder and recognises the '
                           'handle and you.', hurt=(1, 3), credits=0.15)),
        ),
        requires=('presses_sold',)),
    Encounter(
        'courier', 'A case that is not heavy enough', 2, 'street', 'grim',
        'A courier, in {district}, with a case that is not heavy enough, who '
        'does not slow down and does not look at you, and then does both. '
        '"The ledger has a line for you." The case opens. It is empty. It '
        'was always going to be empty. "The line is very long."',
        (
            Option('talk', 'State the matter', 'talk',
                   Outcome('You state the matter the way the Notary would, '
                           'and the courier listens, and closes the case, '
                           'and says, "Noted," and goes, and the line does '
                           'not end, but it does not get longer tonight.'),
                   Outcome('You state the matter badly, and the courier '
                           'writes something in the empty case, and two '
                           'people you had not seen explain the ledger to '
                           'you with their hands.', hurt=(2, 5), credits=0.25)),
            Option('run', 'Leave the courier with the case', 'run',
                   Outcome('You leave, and the courier does not follow, '
                           'because the courier never follows. The line is '
                           'longer.'),
                   Outcome('You leave, and the two you had not seen were '
                           'where you were going.', hurt=(3, 6))),
            Option('stand', 'Wait for the rest of it', 'stand',
                   Outcome('You wait, and the rest of it is a sentence, and '
                           'the sentence is that the key opens nothing of '
                           'theirs, and they know what it opens, and they '
                           'are writing it down. Then they go.'),
                   Outcome('You wait, and the rest of it is not a sentence.',
                           hurt=(3, 6), deck=True)),
        ),
        requires=('keys_kept',)),
    Encounter(
        'hounds_people', 'Hound\'s people', 2, 'street', 'grim',
        'Two people in {district} who are not anybody\'s and are, it turns '
        'out, Hound\'s, which is worse, because Hound pays by results and '
        'these two have not had a result in a while. "Hound says you will '
        'know why." You do.',
        (
            Option('talk', 'Send Hound a message', 'talk',
                   Outcome('You give them a sentence to take back, and it is '
                           'the right sentence, and they take it, because '
                           'taking a sentence back is a result.'),
                   Outcome('You give them a sentence and it is the wrong one, '
                           'and they give you the reply on Hound\'s behalf, '
                           'with interest.', hurt=(2, 5), credits=0.2)),
            Option('run', 'Go', 'run',
                   Outcome('You go, and they are paid by results, and chasing '
                           'you across {district} is not a result they are '
                           'being paid for.'),
                   Outcome('You go, and one of them is faster than paid-by-'
                           'results usually is.', hurt=(3, 6))),
            Option('pay', 'Pay what Hound is paying them', 'pay',
                   Outcome('You name a number that is a little more than Hound '
                           'is paying, and they look at each other, and take '
                           'it, and Hound will hear about it, and that is '
                           'fine: Hound will respect it.'),
                   Outcome('')),
        ),
        requires=('bond:hound:nemesis', 'not:paid_hound')),
    Encounter(
        'vespers_word', 'A word from Vesper', 1, 'street', 'wry',
        'Somebody in {district} says your name, the real one, quietly, and '
        'when you turn it is nobody, a woman with a shopping bag, and she '
        'says, "Vesper says hello," and keeps walking. It is not a threat. '
        'Vesper does not make threats. Vesper makes sure you know she knows '
        'where you stand, so that you do too.',
        (
            Option('talk', 'Send hello back', 'talk',
                   Outcome('You say hello back, to the shopping bag, with the '
                           'right amount of warmth, and the bag pauses, and '
                           'nods, and Vesper will be told you took it well.'),
                   Outcome('You say the wrong thing to the shopping bag and '
                           'Vesper will be told that too, and the telling is '
                           'the cost.', credits=0.1)),
            Option('stand', 'Say nothing', 'none',
                   Outcome('You say nothing. Vesper will be told that you '
                           'said nothing, and will read into it exactly what '
                           'you meant, which is the problem with Vesper.'),
                   Outcome('')),
        ),
        requires=('bond:vesper:nemesis', 'not:paid_vesper')),
)

BY_KEY: dict[str, Encounter] = {e.key: e for e in ENCOUNTERS}


def pool(tier: int, who: str, phase: str) -> list[Encounter]:
    """Encounters of at most this tier for this kind of trouble, now."""
    return [e for e in ENCOUNTERS
            if e.tier <= tier and e.who == who
            and (not e.phases or phase in e.phases)]
