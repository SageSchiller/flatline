"""What people play for money, and what it costs beyond the money.

The third of the three loans, and the most honest one: dice do not pretend the
bill arrives later. The bill is now, and you agreed to it, and everybody in the
room told you the odds first.

**Both games print their exact probability before you commit**, which is D14
applied somewhere D14 was not written for. A casino that hides its edge is a
casino; a casino that puts a sixth of every stake on a board on the wall and
lets you read it before you play is the Ninth Ward, and the difference between
those two things is most of the tone of this city. Nobody here is deceiving
you. They are simply correct about how it will go, on average, and you are
going to play anyway.

**They are different games on purpose.**

`Ninepins` is dice. No skill, no build, a fixed house edge, and it is over in a
second. It exists so that being broke has a fast and stupid solution, and so
that the fast and stupid solution has a number attached to it that the player
can read and ignore.

`Threes` is cards, and it is the opposite: slow, one hand an evening, and
resolved on Guile and Subterfuge against a named opponent. It is the only
place in the game where a social build gets to be a *build* rather than a
discount on conversations. Somebody with the right character can beat the
house at Threes, reliably, forever, which sounds broken and is not, because
the house notices. See `HEAT_PER_WIN`.

**Winning has consequences and they are not the money.** Every faction whose
room you take money out of thinks slightly less of you, and everybody in the
room remembers your face. The city's whole thesis is that it remembers; a
gambling system where the only thing that changed was a number in your account
would be the one place it forgot.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Reputation lost with the house's faction per thousand credits taken off
#: them. Small, and it accumulates, and it is the reason a perfect Threes
#: player is a problem rather than an exploit.
REP_PER_THOUSAND = 1.2

#: Memorability is a real stat with real consequences, and a person who wins
#: a lot in a small room becomes a person that room can describe.
MEMORABLE_AT = 5000

#: Attention drawn per thousand won, once you are past `MEMORABLE_AT` in a
#: single sitting. Winning quietly is free; winning famously is not.
HEAT_PER_WIN = 1.5


@dataclass(frozen=True, slots=True)
class Venue:
    key: str
    #: The game played here.
    game: str
    name: str
    #: District and the service that has to exist for the room to be there.
    where: str
    at: str
    #: Whose room it is. Winning takes standing off them.
    house: str
    #: Walking in.
    arrival: str
    #: Said once, before the first bet, and it contains the odds because the
    #: people who run these rooms are not embarrassed about the odds.
    pitch: str


VENUES: tuple[Venue, ...] = (
    Venue(
        'ninepins_ninth', 'dice', 'the pitch behind the noodle stalls',
        where='ninth', at='market', house='sixes',
        arrival='Somebody has chalked a rectangle on the wet concrete and '
                'four people are standing around it with the specific '
                'patience of people who have been losing money slowly for '
                'two hours and intend to continue.',
        pitch='The rules are painted on the wall, along with the edge, in a '
              'hand that has been repainted over several times and always '
              'with the same number.'),
    Venue(
        'ninepins_shambles', 'dice', 'the back of the solvent shop',
        where='shambles', at='fence', house='carrion',
        arrival='The rectangle here is cut into the floor rather than chalked '
                'on it, and the floor is somebody else\'s idea of a floor. '
                'Nobody looks up. Two of them cannot.',
        pitch='The edge is the same as everywhere. Carrion are many things '
              'and none of them is subtle enough to shave dice.'),
    Venue(
        'ninepins_freeport', 'dice', 'the crane crew game',
        where='freeport', at='workshop', house='freeport',
        arrival='The dock crews play on an upturned pallet between shifts, '
                'and the game has a treasurer, minutes, and a written '
                'constitution, because of course it does.',
        pitch='The edge goes into the crew fund, which pays for funerals and '
              'a Christmas party, and this is explained to you in full '
              'before anybody will take your money.'),
    Venue(
        'threes_marrow', 'cards', 'the long table at the back of the noodle bar',
        where='marrow', at='fixer', house='fixers',
        arrival='Six people at a table that was built for eight, playing the '
                'slowest card game in the city for money that would make you '
                'wince, and conducting four separate business negotiations '
                'over the top of it.',
        pitch='Threes is a reading game. The cards are a formality and '
              'everybody at this table knows it, which is itself the first '
              'thing you have to read.'),
    Venue(
        'threes_vertical', 'cards', 'the ninetieth floor lounge',
        where='vertical', at='market', house='kagawa',
        arrival='Kagawa middle management, unwinding, in a room with a view '
                'of weather. They are delighted to have somebody new and '
                'they are going to be extremely polite about the money.',
        pitch='They will explain the rules to you slowly and completely, in '
              'the manner of people who have decided you are a guest, which '
              'is how you know what the stakes are going to be.'),
)

BY_KEY: dict[str, Venue] = {v.key: v for v in VENUES}


def here(district: str, services: tuple[str, ...],
         game: str = '') -> list[Venue]:
    """Which rooms are open in this district, given what it has."""
    return [v for v in VENUES
            if v.where == district and v.at in services
            and (not game or v.game == game)]


# --------------------------------------------------------------------------
# Ninepins
# --------------------------------------------------------------------------
#
# Two dice. Seven belongs to the house and nothing else does, which is the
# entire edge and it is a sixth of every stake. Written out rather than
# computed so the numbers on the wall and the numbers in the resolver are the
# same numbers.

#: call -> (winning totals, payout multiple on the stake).
CALLS: dict[str, tuple[tuple[int, ...], int]] = {
    'high': ((8, 9, 10, 11, 12), 1),
    'low': ((2, 3, 4, 5, 6), 1),
    'seven': ((7,), 4),
}

#: How many of the 36 outcomes each call wins on. Checked against `CALLS`.
WAYS: dict[str, int] = {'high': 15, 'low': 15, 'seven': 6}

MAX_STAKE = 4000
MIN_STAKE = 10


def odds(call: str) -> float:
    """Exact probability of winning this call."""
    return WAYS[call] / 36.0


def edge(call: str) -> float:
    """The house's expected take, as a fraction of the stake."""
    win = odds(call)
    return 1.0 - (win * (1 + CALLS[call][1]))


def roll_total(stream) -> tuple[int, int]:
    """Two dice, as they land."""
    return stream.int(1, 6), stream.int(1, 6)


#: What the table says when it goes your way, and when it does not. Picked
#: from, so a long session does not read like a slot machine.
DICE_WIN = (
    'Somebody sighs. Money changes hands with the specific reluctance of '
    'money that was going to be spent on something.',
    'The dice are examined, briefly and without malice, and handed back.',
    'A small round of the kind of applause that is mostly about wanting to '
    'get on with the next one.',
)
DICE_LOSS = (
    'The dice stop. Nobody says anything, because there is nothing to say.',
    'It goes into the tin. The tin has been there longer than you have been '
    'in this city.',
    'Somebody who has not been paying attention asks what happened, and is '
    'told, and nods.',
)


# --------------------------------------------------------------------------
# Threes
# --------------------------------------------------------------------------
#
# One hand an evening, resolved on reading the table rather than on the cards,
# which is why it costs a shift and why it is the one game a character build
# reaches into.

THREES_SHIFTS = 1
THREES_MIN = 100
THREES_MAX = 12000

#: Base resistance of a table, before the house's own quality.
THREES_RESISTANCE = 12

#: Credits you have to have taken off a table before it gets one point
#: harder, and the most it can ever learn. **This is "the house notices", as
#: a number.**
#:
#: Without it, a specialist social build beats Threes at a positive
#: expectation forever, at a stake cap of twelve thousand, which is an income
#: rather than a game. With it, a run of good evenings ends the way it does in
#: life, which is that they start knowing how you play.
#:
#: Counted per table rather than off your reputation with the house, which is
#: the obvious shortcut and is wrong: several origins start disliked by the
#: Switchboard, and a table that had already learned how somebody plays before
#: they sat down is not a table, it is a bad mood.
THREES_LEARNS_PER = 6000
THREES_LEARNS_MAX = 6

#: Credits of stake per point of resistance (D63 d). The bigger the hand,
#: the closer they watch it: at the twelve-thousand cap the table is eight
#: points harder than at a hundred. Without this a Guile 8 build read every
#: table at a hundred percent at the cap, and the card room was an income
#: with a floor. With it, and the learning above, a specialist takes a few
#: good evenings off each table and then the table is closed to them.
THREES_PER_STAKE = 1500

#: Below this chance, the room says so and will not take your money. Threes is
#: a game for a build, and somebody without one is not being kept out, they
#: are being pointed at the dice, which is the game that needs no build.
THREES_FLOOR = 0.1

#: Profit as a multiple of the stake, by the margin of the read. A scrape
#: pays less than it cost to sit down, which is what stops a coin-flip build
#: from grinding the table: you have to read them *well*, not just win.
THREES_PAYOUT = ((6, 2.0), (3, 1.2), (0, 0.7))

THREES_WIN = (
    'You take it on the last card, and the table takes a moment to decide '
    'how to be about that. They decide to be gracious, mostly.',
    'Nobody is surprised except one person, who is very surprised, and who '
    'is the reason the rest of them were not.',
    'It is not the cards. It was never the cards. Somebody at the far end '
    'says so out loud and is ignored.',
)
THREES_LOSS = (
    'You had it read exactly right for two hours and then somebody did '
    'something stupid, correctly, and the whole shape of the table changed.',
    'They are kind about it, which is worse, and one of them explains what '
    'you did, which is worse than that.',
    'You lose it slowly, over a whole evening, in a way that never once '
    'presents a moment at which leaving would have been the obvious move.',
)
