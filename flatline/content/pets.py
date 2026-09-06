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


# --------------------------------------------------------------------------
# The other kind (D153): a pet that is not an animal but a small program you
# let run on the deck for no reason but company. It costs memory, which is
# the one thing a deck never has enough of, so keeping one is a real
# decision: a slot that could have been a breaker, spent on a thing that
# only talks. It rides into the run with you and says what it makes of what
# is happening, and some of them are a comfort and some of them are not.
# --------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Familiar:
    key: str
    #: With the article, lowercase.
    name: str
    #: One word for the `familiar` line.
    species: str
    #: 'warm' | 'wry' | 'grim' | 'unsettling' | 'absurd'.
    tone: str
    #: Memory it eats on the deck, which is memory a program cannot have.
    memory: int
    #: How fast its charge runs down per idle shift (D154). A construct
    #: is fed by being run; left in a folder it winds down, faster if it
    #: is the needy kind, slower if it is the patient kind.
    drain: int
    #: What it is.
    blurb: str
    #: What it says, keyed to what the run is doing. Each is a tuple and the
    #: run picks one. Keys: connect, quiet, amber, red, lockdown, blackice,
    #: clean, burned, idle, dormant.
    says: dict = field(default_factory=dict)


FAMILIARS: tuple[Familiar, ...] = (
    Familiar(
        'pixelcat', 'a pixel cat', 'cat', 'absurd', 1, 8,
        'Eight pixels of cat that somebody drew in an afternoon and gave a '
        'purr to and then, apparently, a soul, or the part of one that fits '
        'in a kilobyte. It sits in the corner of the render and reacts to '
        'the run with the confidence of a thing that does not understand any '
        'of it.',
        says={
            'connect': ('The pixel cat blinks in, sits down in the corner of '
                        'the render, and begins washing a paw it does not '
                        'have.',),
            'quiet': ('The pixel cat is asleep. It does this to indicate '
                      'that everything is fine, which it does not know.',),
            'amber': ('The pixel cat\'s ears go up. It has noticed the thing '
                      'you noticed. It looks at you to check you are dealing '
                      'with it. You are the responsible adult here, which is '
                      'the worst part.',),
            'red': ('The pixel cat has puffed up to twelve pixels and is '
                    'making a noise no eight pixels should be able to make.',),
            'lockdown': ('The pixel cat is under the render furniture and '
                         'will not be coming out and thinks you should join '
                         'it.',),
            'blackice': ('The pixel cat has stopped. It is staring at '
                         'something behind you, in the way cats do, except '
                         'this time there is something behind you.',),
            'clean': ('The pixel cat rides your signal back out looking '
                      'enormously pleased with a night it contributed '
                      'nothing to.',),
            'burned': ('The pixel cat comes out with you, unbothered, having '
                       'enjoyed the whole thing on a level you cannot '
                       'access.',),
            'low': ('The pixel cat is smaller than it was, and dimmer, and '
                    'still trying to purr, which at this resolution is mostly '
                    'a suggestion of a purr. It needs running.',),
            'idle': ('The pixel cat has moved to a warmer part of the render '
                     'and is judging your pace.',),
            'dormant': ('The pixel cat is a still frame in the corner. It has '
                        'not run in a while and it shows.',),
            'done': ('The pixel cat, on the objective, does a slow turn in the render and sits on it, which is how it claims things.',),
            'home': ('The pixel cat is asleep on the deck when you get in, or renders as asleep, which for it is the same thing.',),
            'log': ('The pixel cat walks across the log as it renders and sits on the entry for the day after tomorrow, which is a Tuesday, and does not move.',),
        }),
    Familiar(
        'chatterbird', 'a chatter-bird', 'bird', 'wry', 1, 10,
        'A little talking construct in the shape of a bird that a runner '
        'writes to keep themselves company and regrets within a week and '
        'keeps for years. It comments. It is always commenting. It is not '
        'always wrong.',
        says={
            'connect': ('The chatter-bird lands on the top of the render and '
                        'says, "Ooh. Their taste is all over this. Look at '
                        'the arches."',),
            'quiet': ('"Nice and quiet," says the chatter-bird, which is the '
                      'kind of thing it says specifically to end quiet.',),
            'amber': ('"That is a filed session, that is," the chatter-bird '
                      'observes, helpfully, after the fact. "I would not have '
                      'done that. But you did. And here we are."',),
            'red': ('"Right, that is a red, that is a proper red," says the '
                    'chatter-bird, with the satisfaction of a thing that does '
                    'not have a body to lose.',),
            'lockdown': ('"They are cutting the roads. Classic them. I said, '
                         'did I not say, at the arches, I said."',),
            'blackice': ('The chatter-bird stops talking. The chatter-bird '
                         'never stops talking. That is how you know.',),
            'clean': ('"Textbook," says the chatter-bird, taking full credit, '
                      'on the way out. "We are so good at this. I am so good '
                      'at this."',),
            'burned': ('"We do not talk about this one," says the chatter-'
                       'bird, already talking about this one.',),
            'low': ('The chatter-bird has gone hoarse, which should not be '
                    'possible, and is repeating itself, which should not be '
                    'either. Take it on a run before it forgets the words.',),
            'idle': ('"Are we doing anything? We could be doing anything," '
                     'says the chatter-bird.',),
            'dormant': ('The chatter-bird is quiet, which is unlike it, '
                        'because you have not run it in long enough that it '
                        'has run down.',),
            'done': ('"That was the bit they pay for," says the chatter-bird, "and I was here for it, so."',),
            'home': ('"You live here?" says the chatter-bird, every time, from the top of the deck, in the tone of a bird that lives there too.',),
            'log': ('"That is a lot of you," says the chatter-bird, reading over your shoulder, and then, quieter than it has ever said anything, "More than there has been."',),
        }),
    Familiar(
        'goodboy', 'a good boy', 'dog', 'warm', 2, 12,
        'A loyal-dog construct, big and slow and simple, that a runner made '
        'for a kid who does not run any more, and could never bring itself to '
        'delete. It cannot do anything. It just comes with you, and is glad '
        'to, every single time, which turns out to be worth two memory to '
        'some people, on some nights.',
        says={
            'connect': ('The good boy phases in beside you, orients on the '
                        'nearest host, and wags a tail rendered at a framerate '
                        'that suggests real joy.',),
            'quiet': ('The good boy is sitting. It is being so good. It wants '
                      'you to know it is being so good.',),
            'amber': ('The good boy has put itself between you and the '
                      'watching thing, which does nothing, which it does not '
                      'know, which is the whole of what it is.',),
            'red': ('The good boy is barking at the trace. The trace does not '
                    'care. The good boy does not know the trace does not '
                    'care. The good boy will bark at the trace all night.',),
            'lockdown': ('The good boy is pressed against you and shaking and '
                         'has not left, and will not leave, because leaving is '
                         'not a thing it was built to be able to do.',),
            'blackice': ('The good boy is between you and it, hackles up, a '
                         'construct that cannot fight snarling at a thing that '
                         'cannot be fought, for you, because you are the whole '
                         'of what there is.',),
            'clean': ('The good boy rides out at your heel, having saved you '
                      'from nothing, having been the best thing in the run.',),
            'burned': ('The good boy comes out with you and is not '
                       'disappointed, has never once been disappointed, would '
                       'not know how to start.',),
            'low': ('The good boy has not run in too long and it shows: it '
                    'is slower to render, and it looks at the jack, and then '
                    'at you, and it does not understand, and that is worse '
                    'than if it did.',),
            'idle': ('The good boy is waiting by the jack. It has been '
                     'waiting by the jack. It is always waiting by the '
                     'jack.',),
            'dormant': ('The good boy has gone quiet in a folder you do not '
                        'open. It is fine in there. Load it and it will not '
                        'have minded.',),
            'done': ('The good boy sits, the way he was taught, and looks at the objective and then at you, and his whole render wags.',),
            'home': ('The good boy is at the door of the render before you are through the real one, and stays there until you say something to him.',),
            'log': ('The good boy renders between you and the log, the way he renders between you and a warden, and looks at you until you tell him it is all right, which you do not.',),
        }),
    Familiar(
        'tally', 'the tally', 'thing', 'grim', 1, 5,
        'Not a pet. A runner who did not come back left a counting daemon '
        'behind, and it attached to your deck the way a stray does, and now '
        'it counts. You do not know what it counts. It knows. It is content, '
        'in the way a thing with one job is content, and you have stopped '
        'finding that a comfort.',
        says={
            'connect': ('The tally is already counting when you arrive, as '
                        'though it started before you did.',),
            'quiet': ('The tally counts. There is nothing to count and it '
                      'counts anyway, which is either reassuring or the '
                      'opposite and you have never decided.',),
            'amber': ('The tally\'s count changes rhythm. You have learned '
                      'that rhythm. You wish you had not learned that '
                      'rhythm.',),
            'red': ('The tally is counting faster now, and it is not counting '
                    'the trace, you have checked, it is counting something '
                    'else, and it will not say what.',),
            'lockdown': ('The tally has stopped counting up. It is counting '
                         'down. It has never counted down before.',),
            'blackice': ('The tally reaches a number. You do not know which '
                         'number. It goes still, the way it went still the '
                         'once before, on the night you do not talk about.',),
            'clean': ('The tally resets, without comment, to a number that is '
                      'not zero, and begins again.',),
            'burned': ('The tally notes the outcome in whatever ledger a '
                       'thing like the tally keeps, and does not judge, and '
                       'that is worse.',),
            'low': ('The tally has slowed, the count dragging, the intervals '
                    'stretching, and you find that a slow tally is worse to '
                    'have in the room than a fast one. Run it.',),
            'idle': ('The tally is counting the shifts, you think. You have '
                     'not run it in a while. It has noticed. It counts that '
                     'too.',),
            'dormant': ('The tally has gone quiet, and the quiet is louder '
                        'than the counting was, and you find yourself loading '
                        'it again just to make the counting come back.',),
            'done': ('The tally shows the number and then a second number under it, smaller, which is what it thinks the first one cost.',),
            'home': ('The tally shows the shift, and under it the number of shifts it has shown you the shift, and does not say why.',),
            'log': ('The tally counts the entries, and then counts the ones you remember, and shows the difference, and shows it again, larger.',),
        }),
    Familiar(
        'wormwood', 'wormwood', 'thing', 'unsettling', 2, 3,
        'You did not write this and you did not buy it and you cannot '
        'remember when it started riding your deck. It is small and it is '
        'patient and it says things it should not be able to know, in a voice '
        'that is almost yours, and you keep meaning to delete it, and you '
        'keep not, and you have stopped asking yourself why.',
        says={
            'connect': ('Wormwood says, quietly, in the voice that is almost '
                        'yours, "I have been here before. So have you. You do '
                        'not remember it either."',),
            'quiet': ('Wormwood is not saying anything, which is not the same '
                      'as it having nothing to say.',),
            'amber': ('"They felt that," says wormwood. "They always feel it. '
                      'You always do it anyway. I like that about us."',),
            'red': ('"There it is," says wormwood, warmly, as though a red '
                    'alert were a thing it had been looking forward to on your '
                    'behalf.',),
            'lockdown': ('"You could stay," wormwood says. "You never stay. '
                         'One of these times you will stay, and I will be '
                         'here, and it will be fine." It will not be fine.',),
            'blackice': ('"Do not," says wormwood, and for once it sounds '
                         'exactly like you, and for once it sounds '
                         'frightened, and you do not know which of those is '
                         'the lie.',),
            'clean': ('"Good," says wormwood, on the way out, and means it, '
                      'and you do not know why that is the part that keeps '
                      'you up.',),
            'burned': ('"Next time," says wormwood, and it is not a threat, '
                       'and it is not a comfort, and it is patient, and it '
                       'will wait.',),
            'low': ('Wormwood says, from very far down, in a voice with the '
                    'edges worn off it, that it is cold, and that you know '
                    'what it needs, and that you always did.',),
            'idle': ('Wormwood has not spoken in some shifts. You have '
                     'checked, twice, that it is still loaded. It is still '
                     'loaded.',),
            'dormant': ('Wormwood has gone dormant, or is pretending to, and '
                        'you cannot tell which, and you have decided that not '
                        'being able to tell is the same as it being fine.',),
            'done': ('"Done," says wormwood, in the voice that is almost yours, before you have decided it is.',),
            'home': ('"You came back," says wormwood, when you get in, and it is not clear whether that is a greeting or a note.',),
            'log': ('"I have read this," says wormwood, in the voice that is almost yours. "I read it before you did. I did not know how to say so."',),
        }),
)

FAMILIAR_BY_KEY: dict[str, Familiar] = {f.key: f for f in FAMILIARS}


#: The one thing each animal plays with (D160): (what it is, what it costs,
#: what playing with it looks like). Cosmetic, which is the rule for pets:
#: `pet play` fills the same need with or without one, and reads differently.
TOYS: dict[str, tuple[str, int, str]] = {
    'cat': ('a wire mouse', 40,
            'The wire mouse dies four times and is brought back each time by '
            'the cat being bored of its being dead. You are the referee. '
            'Nobody consulted you.'),
    'dog': ('a rope', 60,
            'The rope has two ends and the dog is certain about both of them. '
            'You lose. You were always going to, and it is the best thing '
            'that happens to you this week.'),
    'rat': ('a wheel', 50,
            'The wheel goes nowhere at a speed that would be impressive if it '
            'went somewhere. The rat is not interested in your opinion of '
            'the arrangement.'),
    'pigeon': ('a mirror', 30,
               'The mirror has another pigeon in it. The two of them have a '
               'great deal to discuss and none of it is your business.'),
    'gecko': ('a warm stone', 45,
              'The stone is warm and the gecko is on it, and that is the '
              'entire game, and the gecko is winning it.'),
    'chimera': ('a bell', 80,
                'The bell rings when it moves and it moves when the bell '
                'rings, and it has worked out, slowly and with some '
                'resentment, that the thing in the middle of that is you.'),
}

#: A familiar's charge runs 0..100 (D154). A run fills it; idle shifts
#: drain it at the familiar's own rate. At nothing it is dormant, quiet
#: until you run it or tend it; it is software, it does not die, it waits.
FAMILIAR_FULL = 100
FAMILIAR_LOW = 30
#: What `familiar tend` gives back: a moment out of a run, worth less
#: than a run but enough to keep a patient one going.
FAMILIAR_TEND = 35
