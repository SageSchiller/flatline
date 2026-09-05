"""Something soft in a hard city (D152).

A pet is the one thing you keep that is not for the work. It lives at your
safehouse, because you cannot keep a thing alive out of a chair, and it has
food, water and play that run down at a rate the animal decides, and you
keep them up or you do not. Nothing here helps you on a run or on the
street: the whole point is that it is the part of the game that is not about
winning. It belongs to the character, and when they go it is in the ending,
because in this city a thing that depended on you is the truest account of
what you were.

The care is real and the loss is real and both are telegraphed: a hungry
animal tells you it is hungry for a long time before it stops being yours.
That is the register the whole game is in, applied to the one thing you did
not have to take on.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Animal:
    key: str
    #: With the article: `a cat`, `a one-eyed dog`. The way you would say it.
    name: str
    #: One word for the kind, for the `pet` line and the market.
    species: str
    #: 'warm' | 'wry' | 'grim' | 'unsettling' | 'absurd'. Read by `validate`
    #: to hold the spread: some are meant to be a comfort and one or two are
    #: meant to be a bad idea you love anyway.
    tone: str
    #: What it is, two or three sentences, second person.
    blurb: str
    #: What it costs to take on, in credits. Some are free: a stray is a
    #: decision, not a purchase.
    price: int
    #: How much food, water and play it loses a shift. The animal decides:
    #: a dog needs walking and a gecko needs almost nothing and a cat needs
    #: you to believe it needs nothing.
    decay: dict = field(default_factory=dict)
    #: What it eats, for the feed line and the flavour.
    eats: str = 'feed'
    #: What it does when it is content, shown when you come home to it.
    happy: tuple[str, ...] = ()
    #: What it does when a stat is getting low.
    low: tuple[str, ...] = ()
    #: The line when it is starving and has been for a while: the last
    #: warning before it stops being yours.
    failing: str = ''
    #: What the ending says became of it, fed or not.
    kept_coda: str = ''
    lost_coda: str = ''


ANIMALS: tuple[Animal, ...] = (
    Animal(
        'cat', 'a cat', 'cat', 'warm',
        'A cat that decided about your safehouse before it decided about you, '
        'and has never once admitted the order of those. It is on the warm '
        'part of the deck when you come in, which is the part you needed.',
        price=0,
        decay={'food': 6, 'water': 5, 'play': 3},
        eats='something out of a tin',
        happy=('The cat is on the warm part of the deck, in the exact shape '
               'of not having missed you.',
               'The cat opens one eye, establishes that it is you, and spends '
               'the eye going back to sleep.',
               'The cat has brought you something. It is a bottle cap. It is '
               'very proud. You are required to be also.'),
        low=('The cat is at the door before you are through it, which it '
             'would like recorded is not the same as having missed you.',
             'The cat is louder than a cat should be able to be, at the '
             'cupboard, at you, at the general situation.'),
        failing='The cat is at the window more than the door now, watching '
                'the street the way you watch a thing you are deciding about.',
        kept_coda='The cat outlived you, which cats do, and went to the '
                  'neighbour who had been feeding it on the side the whole '
                  'time, which cats also do.',
        lost_coda='The cat left through a window you had stopped closing, and '
                  'is somewhere in the Ninth being somebody else\'s decision '
                  'now, and is fine, which is the part that is not about you.'),
    Animal(
        'dog', 'a dog', 'dog', 'warm',
        'A dog from nobody, of no breed the city has a name for, that followed '
        'you home once and took your not-stopping-it as a contract. It is at '
        'the door when you come in. It is always at the door. The door is the '
        'best thing that has ever happened, every time.',
        price=0,
        decay={'food': 7, 'water': 7, 'play': 10},
        eats='whatever you have',
        happy=('The dog is at the door, and the door has never been better, '
               'and neither have you, apparently, which is a thing to be told '
               'daily and believe less and need more.',
               'The dog has a routine now, which is your routine, which it '
               'thinks it invented.'),
        low=('The dog is at the door and it is not the same at the door. It '
             'watches you put your coat back on with an expression it did not '
             'used to have.',
             'The dog has chewed something it should not have, which is what '
             'a dog does with a day nobody spent on it.'),
        failing='The dog does not get up when you come in. It looks at the '
                'door and then at you and decides, again, to forgive it, and '
                'the deciding is the part you cannot stand.',
        kept_coda='The dog was old by the end, and slept more than it '
                  'watched the door, and was at the door anyway the last time '
                  'it mattered.',
        lost_coda='Somebody on the stair took the dog in when the flat went '
                  'quiet, and it is at a different door now, and the door is '
                  'still the best thing that has ever happened.'),
    Animal(
        'rat', 'a rat', 'rat', 'wry',
        'A rat, kept on purpose, which the Ninth considers either sensible or '
        'a symptom. It is clever in a way that is unsettling if you think '
        'about it and companionable if you do not, and it rides on your '
        'shoulder in a manner you have agreed to pretend is its idea.',
        price=120,
        decay={'food': 4, 'water': 4, 'play': 4},
        eats='a corner of whatever you are eating',
        happy=('The rat is doing the thing where it washes its face with its '
               'hands, which you have decided is the best thing in the flat.',
               'The rat has moved a small object to a better place. It will '
               'not say which object or where. It knows.'),
        low=('The rat is at the empty dish, sitting up, holding your gaze, '
             'making its point with the patience of something that has read '
             'you correctly.',),
        failing='The rat has started caching food it does not have, in '
                'corners, against a future it has decided not to trust you '
                'with, which is the smartest and worst thing it has done.',
        kept_coda='The rat lived its two years, which is all a rat gets, and '
                  'spent them on your shoulder, which is more than most get '
                  'to choose.',
        lost_coda='The rat left the way rats leave, through a gap you did not '
                  'know was a gap, and is running the walls of the Ninth now, '
                  'cleverer than the building.'),
    Animal(
        'pigeon', 'a pigeon', 'pigeon', 'absurd',
        'A pigeon with a bad foot and no sense of self-preservation that '
        'started landing on your sill and escalated to residency without a '
        'conversation. It is not a good pet. It is barely a pet. It is here '
        'every morning, which turns out to be the whole of what you wanted '
        'from anything.',
        price=0,
        decay={'food': 5, 'water': 6, 'play': 2},
        eats='seed, and things that are not seed',
        happy=('The pigeon is on the sill doing its low complicated sound at '
               'the street, on your behalf, about nothing.',
               'The pigeon has brought a friend. The friend is not invited. '
               'The pigeon is adamant.'),
        low=('The pigeon is on the sill, not coming in, doing the sound at '
             'you now instead of the street, which is worse.',),
        failing='The pigeon comes to the sill and does not stay, and one '
                'morning is a little later than the last, in a way you have '
                'started counting, which is a stupid thing to count and you '
                'are counting it.',
        kept_coda='The pigeon was there every morning until it was not, which '
                  'is how it goes with pigeons, and you never found out which '
                  'kind of not, which is also how it goes.',
        lost_coda='The pigeon stopped coming to the sill, and you leave it '
                  'open anyway, which everybody who has had a pigeon does, and '
                  'nobody who has not will understand.'),
    Animal(
        'gecko', 'a gecko', 'gecko', 'wry',
        'A gecko in a tank you rigged off the deck\'s waste heat, which is the '
        'most use that heat has ever been. It does approximately nothing at '
        'approximately all times and is, for a thing that does nothing, '
        'remarkably good company at four in the morning when the trace is '
        'still in your hands.',
        price=200,
        decay={'food': 2, 'water': 3, 'play': 1},
        eats='the crickets, which you would rather not discuss',
        happy=('The gecko is under the lamp, being a small warm punctuation '
               'mark, radiating a calm it did not earn and you did not '
               'either.',
               'The gecko has changed position since yesterday. This is '
               'headline news in the tank. You mark it.'),
        low=('The gecko is off its rock and in the cold corner, which is a '
             'gecko\'s entire vocabulary for something being wrong, and it is '
             'using all of it.',),
        failing='The gecko has gone the colour a gecko goes, dull and slow '
                'and folded small, and the lamp is doing what it can and it '
                'is not the lamp\'s job to be you.',
        kept_coda='The gecko is still under its lamp, off the salvaged heat '
                  'of a deck that has no runner now, and somebody will find it '
                  'there, warm, doing nothing, fine.',
        lost_coda='The lamp went out with everything else, and the tank went '
                  'cold, and a gecko is a desert thing that keeps no heat of '
                  'its own, and that is as much as should be said.'),
    Animal(
        'chimera', 'the thing from the Green', 'chimera', 'unsettling',
        'It came out of Building Nine in a coat pocket that was not yours '
        'first, and it is a cat the way a thing Aoyama made is ever only '
        'mostly the animal it started as. It has too few eyes in one place '
        'and too many somewhere you do not look directly, and it purrs, and '
        'the purr is right, and everything else is a question you have '
        'decided not to ask.',
        price=0,
        decay={'food': 6, 'water': 4, 'play': 6},
        eats='what the label did not have a word for',
        happy=('The thing from the Green is on the deck, warm, purring the '
               'purr that is exactly right, and the rest of it you have '
               'trained yourself not to see, which it lets you.',
               'The thing from the Green watches the door for a full minute '
               'before you open it, and is looking at it when you do, and you '
               'have stopped finding that strange, which is the strange '
               'part.'),
        low=('The thing from the Green is very still, and its eyes, the ones '
             'you count and the ones you do not, are all on you, and it wants '
             'something, and you would rather it asked out loud, which it '
             'nearly can.',),
        failing='The thing from the Green has stopped purring, and the flat '
                'is more silent than a flat with a living thing in it should '
                'be able to be, and whatever Aoyama built it to do instead of '
                'dying, it has not started doing yet.',
        kept_coda='The thing from the Green did not age, in the years you '
                  'had, and did not die when you did, and is somewhere in the '
                  'city being somebody else\'s question now, purring the purr '
                  'that is exactly right.',
        lost_coda='The thing from the Green left the day the heat went off, '
                  'through a door that was locked, and Aoyama would like it '
                  'back, and will not get it, and it is out there, fine, '
                  'which is the wrong word and the only one.'),
)

BY_KEY: dict[str, Animal] = {a.key: a for a in ANIMALS}
TONES: tuple[str, ...] = ('warm', 'wry', 'grim', 'unsettling', 'absurd')

#: What a bag of feed costs and how many feeds it holds. One economy for all
#: of them: the difference between animals is how fast they empty, not what
#: the tin costs.
FEED_PRICE = 60
FEED_PER_BAG = 8

#: Care stats run 0..100. These are the bands the mood reads.
FULL = 100
CONTENT_AT = 55
LOW_AT = 25

#: Shifts a stat can sit at nothing before the animal starts to go, and the
#: shift it actually leaves. Telegraphed: the first is a long warning, the
#: second is the end of it, and everything in between says so.
WARN_AFTER = 2
LOST_AFTER = 6


def mood(pet: dict) -> str:
    """content | ok | low | failing, from the worst-kept stat."""
    worst = min(pet.get('food', 0), pet.get('water', 0), pet.get('play', 0))
    streak = int(pet.get('neglect', 0))
    if streak >= WARN_AFTER:
        return 'failing'
    if worst >= CONTENT_AT:
        return 'content'
    if worst >= LOW_AT:
        return 'ok'
    return 'low'


def worst_need(pet: dict) -> str:
    """Which of the three is lowest, for the advice line."""
    order = sorted(('food', 'water', 'play'), key=lambda k: pet.get(k, 0))
    return order[0]
