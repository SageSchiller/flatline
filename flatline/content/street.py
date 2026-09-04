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

You get out of it the way people who live here get out of it: you run,
you talk, you pay, or you stand there and take it, and two skills decide
how well each of those goes. The checks are printed like every other check
in the game. And since D128 you can fight, when there is somebody to
fight: `fight` is on the menu of every encounter with people in it, it is
never the only thing on the menu, and it is a short exchange rather than a
check (see `world/fight.py`). `front` is the bluff, once you have a name
worth bluffing with. The founding rule that there were no street fights
(D2) was unlocked by the author on 2026-09-03; the half of it that stays
is that combat is a way to survive the street and never a way to do a job.

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
    # `stand` read Nerve as a skill for the whole life of the layer and
    # found nothing, and the ladder was tuned around that. Streetcraft is
    # the term it was tuned with in effect: zero untrained, a little when
    # you know the street (D128).
    'stand': ('grit', 'fieldcraft', 'streetcraft'),
    'careful': ('reflex', 'fieldcraft', 'streetcraft'),
    # D128. `fight` is the opening strike's sum, shown on the menu; the
    # exchange itself prints its own. `front` is the bluff.
    'fight': ('grit', 'violence', 'nerve'),
    'front': ('guile', 'streetcraft', 'nerve'),
}

#: Encounters with nobody in them to fight: a stair, a pot of soup, a
#: crowd on a landing, somebody handing you a paper. `fight` is not
#: offered, and neither is `menace`.
NOBODY_TO_FIGHT: frozenset[str] = frozenset({
    'stair', 'soup', 'stairs_crowd', 'paperboy', 'vespers_word',
})

#: People with nothing in them for the deck to reach: four kids with one
#: knife, an amateur tail, a courier. `jack` needs chrome to hit.
UNCHROMED: frozenset[str] = frozenset({
    'knives', 'tail', 'courier', 'queue_jumper', 'walkway',
})


def fightable(enc: Encounter) -> bool:
    return enc.key not in NOBODY_TO_FIGHT


def chromed(enc: Encounter) -> bool:
    """Whether their people carry chrome. Somebody's people do, unless the
    encounter says otherwise; nobody's people mostly do not."""
    if enc.key in UNCHROMED:
        return False
    return enc.who == 'faction' or enc.key in ('crossed', 'hounds_people',
                                               'backqueue', 'colonnade_coat',
                                               'frame', 'callout', 'collectors')


# -- the fight, in words (D128) ---------------------------------------------
#: Second person, present tense, deadpan. `{fac}` fills where there is one.

#: How it starts, by tier.
FIGHT_OPEN = {
    1: 'It goes the way these go: no announcement, a half step, and then it '
       'is happening and everybody involved is slightly surprised.',
    2: 'There is a moment where it could still be a conversation, and then '
       'there is not, and the one nearest you has already moved.',
    3: 'Nobody says anything. The van door stays open. They come in '
       'together, which is how you can tell they have done this before.',
    4: 'They were not here to talk, and now neither are you. It is very '
       'quiet, and it is going to be over quickly one way or the other.',
}

#: Their condition, by the share of them left.
FOE_STATE = ((0.99, 'untouched'), (0.6, 'hurt'), (0.3, 'reeling'),
             (0.0, 'nearly done'))

STRIKE_WIN = (
    'You hit them. It is not the movies: it is a short ugly noise and a '
    'step back, and something in the arithmetic of the doorway changes.',
    'It lands. Not where you meant, somewhere better, and the one you hit '
    'stops being the one to worry about.',
    'You go first and you go somewhere that counts, and for a moment the '
    'only person in the walkway making a sound is them.',
)
STRIKE_CRIT = (
    'You hit them properly. There is a noise like a dropped bag of tools '
    'and one of them is not standing any more.',
)
STRIKE_LOSE = (
    'You swing and it is not there. They let you, which is the part that '
    'tells you what kind of night this is.',
    'It does not land. Something about the angle, something about the '
    'light, something about you.',
)
GUARD_WIN = (
    'You get an arm up and take it on the arm, and the arm will complain '
    'tomorrow and you will be there to hear it.',
    'You give ground and turn, and what was meant for your head goes past '
    'your ear, and now you know where they are.',
)
GUARD_LOSE = (
    'You cover up and it comes in under the cover, which is where these '
    'things go.',
)
JACK_WIN = (
    'You do not touch them. You reach into the chrome they paid too much '
    'for and turn something off, and they find out what their optics were '
    'doing for them by not having it.',
    'The deck is in your hand and their reflex boost is a construct with a '
    'person attached, and you have killed constructs before. The person '
    'sits down.',
    'Something under their skin stops answering. You can see them realise, '
    'and you can see them realise who did it.',
)
JACK_LOSE = (
    'They see the deck. They know what a deck is for and they close the '
    'distance before you finish, which is what a deck is not for.',
)
JACK_NOTHING = 'There is nothing in them for the deck to reach.'
FINISH_WIN = (
    'You end it. One more, where it needs to go, and the walkway is a '
    'walkway again with people lying in it.',
)
FINISH_LOSE = (
    'You go for the end of it and it is not the end of it, and you are '
    'wide open for exactly as long as it takes them to notice.',
)
BREAK_WIN = (
    'You go. Not fast, not clever: gone, through the gap that a fight '
    'opens in the people having it, and they are too busy to follow.',
)
BREAK_LOSE = (
    'You try for the gap and the gap has somebody in it.',
)
FOE_HIT = (
    'They hit you. It is exactly as bad as it sounds.',
    'One of them gets through and you hear it before you feel it.',
    'It lands on you and the street tilts a few degrees and comes back.',
    'They are not tired yet. That was to show you they are not tired yet.',
)
FOE_HIT_ARMOUR = 'Most of it stops at the plating.'
FOE_STUNNED = 'The one you hit is still finding out where their hands are.'
TALKDOWN_WIN = (
    'You find the sentence. It is not a clever sentence; it is the true one, '
    'about how this ends for everybody standing here, and one of them was '
    'waiting for a reason and you have handed it to them.',
    'You give them the out. A way to stop that is not losing, and they take '
    'it the way people take a thing they wanted and could not ask for.',
)
TALKDOWN_LOSE = (
    'You find the sentence and it is the wrong one, and the wrong one in a '
    'fight is a beat you spent not covering up.',
)
FOE_MISS = 'They come in and there is nothing there.'
FOE_GLANCE = 'Most of it goes into the arm, which is what the arm was for.'
FOE_REACHED = 'They come for you and the metre is in the way, and the metre wins.'
FOE_STAGGERED = 'The one you put on the floor is still on the floor.'
STRIKE_FIRST = 'They did not see it coming, because there was nothing to see.'
ALLY_HIT = (
    '{ally} puts one down while you are busy with another.',
    '{ally} is beside you, and the doorway is narrower for it.',
    '{ally} does something quick and ugly and somebody stops.',
)

#: What you take off the people you beat (D131): the weapon they had, by
#: encounter, half the time. It goes in the bag. A fence buys it back, or
#: you carry it.
LOOT: dict[str, str] = {
    'knives': 'switchblade', 'walkway': 'bat', 'toll': 'bat',
    'lean': 'knuckles', 'press': 'baton', 'finish': 'pistol',
    'collectors': 'pistol', 'hounds_people': 'blade', 'backqueue': 'cleaver',
    'callout': 'katana', 'crossed': 'blade', 'wet_press': 'baton',
    'checkpoint': 'baton', 'frame': '', 'tail': 'switchblade',
}

#: The end of it, by tier. `{fac}` fills.
FIGHT_WON = {
    1: 'It is over. They were not expecting anybody to do that, and they '
       'are going to have to think about the street differently, later, '
       'somewhere else.',
    2: 'It is over. Somebody is on the ground and somebody is walking away '
       'in the wrong direction, and you are the one still standing in the '
       'doorway, which is not nothing on this street.',
    3: 'It is over, and the van leaves without what it came for. You stand '
       'there for a moment with your hands doing something on their own, '
       'and then you put them in your pockets and walk.',
    4: 'It is over. Nobody is getting up, and you check, because the kind '
       'that kills is the kind that does not stop. It is very quiet. You '
       'are going to remember this one for longer than the others.',
}
FIGHT_LOST = {
    1: 'They win. It was always most likely that they would win, and the '
       'walkway agrees with them.',
    2: 'You lose. There is a moment near the end where you understand that '
       'you have lost and a moment after it where they make sure.',
    3: 'You lose, and they take their time about the rest of it, because '
       'time is the one thing the van has plenty of.',
    4: 'You lose. There is nothing to say about it that the ground is not '
       'already saying.',
}
FIGHT_KILLED = ('You did that. Whatever else the night was, it is also the '
                'night you did that, and something in how you stand has '
                'already changed to fit.')
FIGHT_LOUD = ('A gun went off in {district}. Everyone within four streets '
              'heard which kind, and one of them is the Nightwatch.')

MENACE_WIN = (
    'You do not say anything. You let them look at you, and you let them '
    'work out what a fight would cost them, and they do the sum faster '
    'than you expected and find somewhere else to be.',
)
MENACE_LOSE = (
    'You let them look. They look. One of them laughs, which is the sound '
    'of somebody who has decided, and they go first.',
)
FRONT_WIN = (
    'You tell them who you are. You tell it like it is already a story '
    'they have heard, and you watch them decide that it is.',
    'You do not slow down. You name the last thing you did to somebody '
    'like them, and the number, and you let the number do the walking.',
    '"Ask around," you say, and keep walking, and the thing about that is '
    'that they will, and what they hear will be true.',
)
FRONT_LOSE = (
    'You tell them who you are. They know. That is the problem.',
    'It is a good line and you deliver it well, and one of them explains '
    'with the flat of a hand why lines are for people who can back them.',
    'You name-drop a job. It turns out one of them was on the other end '
    'of it.',
)

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
    #: Districts it belongs to. Empty means anywhere in the city; a named
    #: one is the street of that place and nowhere else.
    districts: tuple[str, ...] = ()


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
        'walkway', 'The toll on the walkway', 2, 'street', 'grim',
        'The covered walkway in {district} has a toll now. Six of them, '
        'nobody\'s, the oldest maybe nineteen, with a shopping trolley across '
        'the narrow part and a price written on a piece of card. The price is '
        'more than the card cost and less than what is in the bag, and they '
        'have thought about that harder than you would expect.',
        (
            Option('run', 'Go over the trolley', 'run',
                   Outcome('You go over the trolley while they are still '
                           'deciding whether you would, and you are through '
                           'the narrow part with the card behind you.'),
                   Outcome('You go over the trolley and the trolley goes over '
                           'with you, and there are six of them and a lot of '
                           'boots.', hurt=(3, 6), credits=0.25)),
            Option('talk', 'Ask who set the price', 'talk',
                   Outcome('You ask who set the price and it turns out to be '
                           'the one at the back, who is pleased to be asked, '
                           'and the price comes down to nothing on the '
                           'grounds that you asked.'),
                   Outcome('You ask who set the price and they all did, '
                           'which is the problem with committees.',
                           hurt=(2, 5), credits=0.3)),
            Option('pay', 'Pay the card', 'pay',
                   Outcome('You pay the card. It is an honest price for a '
                           'walkway, considered as a walkway.'),
                   Outcome('')),
            Option('stand', 'Wait for them to get bored', 'stand',
                   Outcome('You stand there. They are nineteen and it is '
                           'cold and there is a queue forming behind you '
                           'that is more trouble than you are, and the '
                           'trolley moves.'),
                   Outcome('You stand there, and the queue behind you would '
                           'rather you paid, and says so, with help.',
                           hurt=(3, 6), credits=0.2)),
        )),
    Encounter(
        'frame', 'The man in the frame', 2, 'street', 'wry',
        'A docker in {district} in a load frame, the kind that lifts pallets, '
        'and he is drunk in it, which the frame was not built for. He has '
        'decided something about you. It is not clear what. He is wearing '
        'eleven thousand credits of crane and none of it is a brain, and '
        'the arms are coming up.',
        (
            Option('run', 'Be somewhere the frame is not', 'run',
                   Outcome('You are somewhere the frame is not, which is '
                           'easy, because the frame is slow and he is slower, '
                           'and the arms come down on nothing.'),
                   Outcome('You go and the frame does not need to be fast '
                           'when the street is narrow.', hurt=(4, 7))),
            Option('talk', 'Ask him what he is lifting', 'talk',
                   Outcome('You ask him what he is lifting. He looks at his '
                           'arms. It takes a while. By the end of it he is '
                           'lifting a wall, carefully, and you are gone.'),
                   Outcome('You ask, and he tells you, and it is you.',
                           hurt=(3, 6))),
            Option('careful', 'Wait for the arms to come down', 'careful',
                   Outcome('You wait for the arms to come down, which they '
                           'do, because they are hydraulic and he is not, '
                           'and you step round the man inside them.'),
                   Outcome('You wait for the arms to come down and one of '
                           'them does, on you.', hurt=(4, 8))),
        ),
        phases=('night',)),
    Encounter(
        'callout', 'Somebody who heard', 3, 'street', 'grim',
        'One person, in {district}, who has been waiting for you specifically, '
        'and who says your handle, and then says what you did, the thing you '
        'are known for, in a tone that has decided it is not true. Not '
        'anybody\'s. His own. He has chrome in both arms and a small crowd '
        'that has come to watch, and he wants you to know that whatever '
        'happens next, they will tell it.',
        (
            Option('run', 'Give him nothing to tell', 'run',
                   Outcome('You give him nothing. You walk, and the crowd '
                           'has nothing to tell except that you walked, and '
                           'they tell it anyway, and it costs you nothing '
                           'that you cannot afford.'),
                   Outcome('You walk and he does not let you, in front of '
                           'people, which was the point.', hurt=(5, 9),
                           credits=0.15)),
            Option('talk', 'Ask him what he heard', 'talk',
                   Outcome('You ask him what he heard, and he tells you, and '
                           'you correct one detail, quietly, and it is the '
                           'detail that matters, and the crowd goes home '
                           'with a better story than the one they came for.'),
                   Outcome('You ask, and he was not here to talk, and the '
                           'crowd came to see that.', hurt=(5, 9))),
            Option('stand', 'Let him say it', 'stand',
                   Outcome('You stand there and let him say it. It takes '
                           'longer than he planned and lands worse than he '
                           'hoped, because you are still standing there, '
                           'and the crowd knows what that means.',
                           hurt=(1, 3)),
                   Outcome('You stand there and let him say it, and then '
                           'let him show it.', hurt=(6, 10))),
        ),
        requires=('runs:4',)),
    Encounter(
        'collectors', 'Hired', 3, 'street', 'grim',
        'Three people in {district} who are not anybody\'s, which is the '
        'thing they want you to understand first: hired, by somebody who '
        'did not want their own people seen doing this, which means paid, '
        'which means they are not going to be talked out of it and they are '
        'not in a hurry. They have a van. They have a piece of paper with '
        'your handle on it, and the handle is spelt right.',
        (
            Option('run', 'Make them earn it', 'run',
                   Outcome('You make them earn it, through a market and out '
                           'the back of a laundry, and by the time they have '
                           'earned it you are three districts away and they '
                           'are being paid by the hour.'),
                   Outcome('You make them earn it and they earn it.',
                           hurt=(6, 10), deck=True)),
            Option('talk', 'Ask who is paying', 'talk',
                   Outcome('You ask who is paying. They do not know. You '
                           'tell them what it would be worth to know, and '
                           'what that is worth to them, and it turns out '
                           'they have a rate for that too.', credits=0.1),
                   Outcome('You ask who is paying, and they are '
                           'professionals, and professionals do not gossip '
                           'with the work.', hurt=(5, 9), credits=0.2)),
            Option('pay', 'Outbid whoever it is', 'pay',
                   Outcome('You outbid whoever it is. They take the money '
                           'and they take the paper, and the paper goes '
                           'back to whoever with a note about the rate.'),
                   Outcome('')),
            Option('stand', 'Get in the van', 'stand',
                   Outcome('You get in the van. It is a conversation, in '
                           'the end, with a man who wanted to be sure you '
                           'understood something, and you understood it, '
                           'and the van lets you out.', hurt=(2, 4)),
                   Outcome('You get in the van and it is not a '
                           'conversation.', hurt=(7, 11), deck=True)),
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
    # -- streets that are only one street (D65 depth) -------------------------
    Encounter(
        'lobby_gait', 'The lobby has decided about you', 2, 'faction', 'grim',
        'The Vertical\'s lobby logs your gait, and something about the way '
        'you walked in has come up as a mismatch, and two of {fac}\'s '
        'building people are already crossing the floor at the angle that '
        'means they have been told which one you are. Nobody raises a voice '
        'in this lobby. That is not the same as nobody doing anything.',
        (
            Option('talk', 'Be somebody with an appointment', 'talk',
                   Outcome('You have an appointment. You say whose, and the '
                           'floor, and the time, and one of them checks a '
                           'tablet and the other has already stopped '
                           'walking, and the lobby goes back to logging '
                           'everybody else.'),
                   Outcome('You have an appointment and it is not on the '
                           'system, and the room the conversation finishes '
                           'in is off the lobby and has no window.',
                           hurt=(2, 5), heat=-6, mark='bounty_mark')),
            Option('careful', 'Walk out the way somebody who belongs walks out',
                   'careful',
                   Outcome('You turn, unhurried, and cross the floor at the '
                           'speed of somebody who has finished, and the doors '
                           'do what doors do, and the gait model files you as '
                           'staff leaving early.'),
                   Outcome('You turn, and hurry, which is the one thing the '
                           'model is looking for, and they have you at the '
                           'doors.', hurt=(2, 4), credits=0.2)),
            Option('pay', 'Have a reason in your hand', 'pay',
                   Outcome('You have a docket, or something that passes for '
                           'one, and a note in it, and the building takes '
                           'both and loses interest in the difference.'),
                   Outcome('')),
        ),
        districts=('vertical',)),
    Encounter(
        'colonnade_coat', 'A man in a good coat', 1, 'street', 'wry',
        'One of the coats on the Row has stopped being sixty paces away and '
        'is now beside you, matching your pace under the colonnade, saying '
        'nothing, for a hundred yards, with the rain on the roof and the '
        'couriers going past. Eventually: "You are not a customer."',
        (
            Option('talk', 'Explain what you are', 'talk',
                   Outcome('You explain, mostly truthfully, and he listens the '
                           'way a man listens who is paid to have already '
                           'decided, and then peels off, and the next coat '
                           'sixty paces on does not look up.'),
                   Outcome('You explain and he is not listening, he is '
                           'timing, and at the end of the hundred yards there '
                           'are two more of them and a door.',
                           hurt=(1, 3), credits=0.2)),
            Option('careful', 'Walk to the end and out', 'careful',
                   Outcome('You walk to the end of the colonnade at exactly '
                           'the pace you were walking, and out, and he stops '
                           'at the last pillar the way a dog stops at a line '
                           'in the grass.'),
                   Outcome('You get to the end and the end is where he wanted '
                           'you.', hurt=(1, 4))),
        ),
        districts=('row',)),
    Encounter(
        'queue_jumper', 'Somebody in the queue', 1, 'street', 'grim',
        'A man in the soup queue at the Hall says your handle. Not loudly. '
        'He says it the way you say a thing to see whether it lands, and '
        'when it lands he does not look pleased, he looks tired, and he says '
        'the name of somebody who is not here any more, and waits.',
        (
            Option('talk', 'Say the name back to him', 'talk',
                   Outcome('You say it back, and the rest of what you know '
                           'about it, which is not much and is honest, and he '
                           'nods, and takes his soup, and eats it beside you '
                           'without saying anything else, and that is the '
                           'whole of it.'),
                   Outcome('You say it back wrong, or say the wrong thing '
                           'about it, and the queue is suddenly a room with '
                           'forty people in it who heard.',
                           hurt=(1, 3), heat=6)),
            Option('stand', 'Wait for him to say the rest', 'none',
                   Outcome('You wait. He waits. The queue moves. At the '
                           'counter he takes his soup and goes and sits with '
                           'his back to you, and you have learned something '
                           'about what your name is worth in this building.'),
                   Outcome('')),
        ),
        districts=('hall',)),
    Encounter(
        'checkpoint', 'A checkpoint that was not there yesterday', 2, 'faction',
        'grim',
        'Two of {fac}\'s at a folding table across the pavement in '
        '{district}, with a terminal and a queue, checking whatever it is '
        'they check today. The queue is moving. Everybody in it is being '
        'polite. That is what a checkpoint is for.',
        (
            Option('talk', 'Queue, and be ordinary', 'talk',
                   Outcome('You queue. You are ordinary. The terminal says '
                           'whatever it says about ordinary people and you '
                           'are through it in four minutes and nobody has '
                           'looked at you twice.'),
                   Outcome('You queue and the terminal does not like you, and '
                           'the four minutes become a van, briefly, and a '
                           'conversation, and a lighter pocket.',
                           hurt=(1, 4), credits=0.3, heat=-5)),
            Option('careful', 'Go round it', 'careful',
                   Outcome('You go round: a service door, a yard, a fence '
                           'that is a suggestion, and out on the far side of '
                           'the table with nothing to declare.'),
                   Outcome('You go round and there is a reason the yard was '
                           'empty, which is that they put the second pair '
                           'there.', hurt=(2, 5))),
            Option('pay', 'Have the right thing to show', 'pay',
                   Outcome('You have the right thing, or something with the '
                           'right shape and a note folded into it, and the '
                           'table takes it and waves you on.'),
                   Outcome('')),
        ),
        districts=('precinct', 'vertical', 'green', 'row')),
    Encounter(
        'stairs_crowd', 'The stairwell at shift change', 1, 'street', 'grim',
        'Six floors of people coming down while you are going up, in a '
        'stairwell built for two abreast, and every one of them has been on '
        'their feet for ten hours, and somewhere in the middle of it '
        'somebody\'s hand is going through your coat.',
        (
            Option('careful', 'Let it happen and watch which way they go',
                   'careful',
                   Outcome('You let it happen, and watch, and on the third '
                           'landing you take back what was yours and a little '
                           'that was not, and nobody in the stairwell has '
                           'broken step.'),
                   Outcome('You let it happen and lose them at the second '
                           'landing, because they do this every shift change '
                           'and you do not.', credits=0.2)),
            Option('stand', 'Take hold of the wrist', 'stand',
                   Outcome('You take the wrist and hold it up where the '
                           'stairwell can see it, and the stairwell, which '
                           'knows exactly whose wrist it is, makes a sound '
                           'that is not laughter, and the coat is returned.'),
                   Outcome('You take a wrist and it is the wrong wrist, and '
                           'six floors of tired people have an opinion about '
                           'that.', hurt=(2, 4), credits=0.15)),
        ),
        districts=('terraces', 'ninth'), phases=('afternoon',)),
    Encounter(
        'wet_press', 'Somebody wants the edition stopped', 2, 'faction', 'grim',
        'Three of {fac}\'s in the ink store, which is not their ink store, '
        'talking to a printer who has both hands where they can be seen. '
        'They are here to stop an edition. You are here, which was not the '
        'plan, and one of them has already decided you are part of it.',
        (
            Option('talk', 'Be nobody, loudly', 'talk',
                   Outcome('You are nobody, at volume, with detail, and it is '
                           'boring enough to be true, and they go back to the '
                           'printer and you go out past the drums.'),
                   Outcome('You are nobody and one of them has seen you '
                           'before, in a paper, above the fold.',
                           hurt=(2, 5), heat=-6)),
            Option('stand', 'Stand with the printer', 'stand',
                   Outcome('You stand where the printer can see you standing '
                           'and so can they, and it is three against two now '
                           'rather than three against one, and three against '
                           'two in a room with a drain in the floor is not '
                           'worth the paperwork. They go.',
                           heat=-4),
                   Outcome('You stand with the printer and they do the '
                           'printer first and you second, and the edition '
                           'does not run.', hurt=(3, 7))),
            Option('run', 'Not your edition', 'run',
                   Outcome('It is not your edition. You are out past the '
                           'drums and into the rain before anybody has '
                           'finished deciding about you.'),
                   Outcome('It is not your edition and you are out of the '
                           'door into somebody who was posted on the door.',
                           hurt=(2, 5))),
        ),
        districts=('stacks',)),
)

BY_KEY: dict[str, Encounter] = {e.key: e for e in ENCOUNTERS}


def pool(tier: int, who: str, phase: str, district: str = '') -> list[Encounter]:
    """Encounters of at most this tier for this kind of trouble, now, here."""
    return [e for e in ENCOUNTERS
            if e.tier <= tier and e.who == who
            and (not e.phases or phase in e.phases)
            and (not e.districts or district in e.districts)]


# -- a fixer's street jobs (D134) ------------------------------------------
#: Three shapes of physical work a fixer hands out, over and above muscle
#: errands: somebody needs hurting, something needs protecting, something
#: needs getting back. Each is a fight where the job is, at the tier the
#: fixer says, and it is not a run: combat is never the way to do a job,
#: and these are a second kind of work.

FIXER_JOBS = {
    'hurt': {
        'label': 'somebody needs hurting',
        'pitch': '"{who}. {district}. I do not want them dead and I do not '
                 'want them talked to. I want them to have had a bad night '
                 'that they connect, afterwards, with a decision they made."',
        'arrive': 'You find {who} in {district}, which is not hard, because '
                  'people who have made the decision the fixer meant do not '
                  'expect the consequence to have a face.',
        'won': 'They will connect it. You leave them where the fixer would '
               'want them found, which is where they are.',
        'lost': 'They had friends, or you were slower than the fixer was '
                'paying for. The fixer will hear, and the fixer does not pay '
                'for hearing.',
        'talked': '',
    },
    'protect': {
        'label': 'something needs standing in front of',
        'pitch': '"{who}, {district}, tonight. Somebody is coming to close '
                 'it, and I would like it to still be open in the morning. '
                 'I am not paying you to be reasonable."',
        'arrive': 'You find {who} in {district} and you stand where it can '
                  'be seen that you are standing, and it is not long before '
                  'the people who were coming arrive and find the doorway '
                  'has an opinion.',
        'won': 'It is still open in the morning. The fixer\'s money is where '
               'the fixer said it would be.',
        'lost': 'It is not open in the morning.',
        'talked': 'It is still open in the morning, and nobody bled on the '
                  'step, and the fixer pays half and says nothing about the '
                  'half.',
    },
    'recover': {
        'label': 'something needs getting back',
        'pitch': '"Somebody in {district} has {item}, which is not theirs, '
                 'and they are not going to hand it over, and I would rather '
                 'they were asked by somebody who is not me."',
        'arrive': 'You find them in {district}, and they have {item} on '
                  'them, which they make no attempt to hide, because they do '
                  'not think you are the kind of problem that gets it back.',
        'won': 'You have {item}. They do not, and the fixer does not want it '
               'either; it was never about the thing.',
        'lost': 'They still have {item}, and now they know what the fixer '
                'sends.',
        'talked': '',
    },
}

#: Who the hurting is for, by the fixer's tone. `{district}` fills.
FIXER_MARKS = (
    'a man who runs a stall and a side business the stall is for',
    'a woman who collects for somebody and has started collecting for '
    'herself',
    'two brothers with a van and a route that is not theirs',
    'somebody\'s cousin, which is the whole of what you are told',
    'a printer who printed the wrong thing for the wrong people',
    'a docker who has been saying things on the rota about the fixer',
)
FIXER_PLACES = (
    'a print shop that is also a betting shop', 'a clinic with a back door',
    'a bar under the arches', 'a stall that sells one thing',
    'a laundry with a queue', 'a workshop that is not open',
)
