"""Getting out, and what is left of you either way.

This game has been called Flatline since the first day and the flatline has
always ended into a scoreboard. Meta counters go up, the rice catalogue gains
a palette, and the person is gone as though they had never been in the city at
all. That is the one place the game's thesis does not hold: it remembers
factions, districts, postures and the evidence you left on a node three weeks
ago, and it forgets *you* the moment you stop breathing.

There were also only two exits, and one of them was closing the terminal.

**So: two endings, and one inheritance.**

`retire` is the way out you choose, and what it asks for is a list of exactly
the things this game spends its time making you accumulate. Clear the debt.
Come off whatever you are on. Have nobody paying for your name. Have enough
put away. None of those is hard on its own and all four at once is the whole
campaign, which is the point: the door has been there since the first shift
and every system in the city has been quietly making it further away.

**Dissonance does not gate it.** Somebody who is four fifths machine can walk
out of this business, and what they walk out into is a different ending, which
is a better answer than a refusal. See `ENDINGS`.

**Whichever way you go, you leave exactly one thing.** A retirement leaves
money, or a name people still trust. A flatline leaves the things that get
taken and the things that get remembered: chrome back on a shelf in the
Shambles, a program still in circulation with your handle in the header, or a
debt somebody fully expects the next person to honour.

One, not several, and you do not choose it. An inheritance you picked would be
a character-creation menu with a story attached; an inheritance that arrives is
the city having an opinion about how you went.
"""

from __future__ import annotations

from dataclasses import dataclass

# --------------------------------------------------------------------------
# getting out
# --------------------------------------------------------------------------

#: What you have to have put away. Priced against the board: contracts pay
#: between about 1,200 and 6,000, so this is somewhere between ten and thirty
#: successful runs of everything going right, and nothing in this city lets
#: everything go right for thirty runs in a row.
STAKE = 45000

#: The gates, in the order they are checked and reported. Each is a key the
#: command implements, a one-line description of what it wants, and the line
#: printed when you have not got there. Declared rather than written inline so
#: `retire` with nothing to do can print the whole list as a progress sheet,
#: which is the only way somebody discovers this is a goal at all.
GATES = (
    ('stake', 'enough put away to stop',
     'You have {credits:,}c. Getting out costs {stake:,}c, which is not a '
     'fee. It is what it takes to be somebody who used to do this.'),
    ('debt', 'nobody holding paper on you',
     'You owe {owed:,}c. Nobody walks away from this business owing '
     '{lender} money, and the reason nobody does is that they are not '
     'allowed to.'),
    ('clean', 'nothing in you that you need',
     'You have a habit. Whatever you are planning to be next, it is not '
     'going to be that while you still need something on a Tuesday.'),
    ('quiet', 'nobody paying for your name',
     'There is a bounty on you. A retirement with a number attached to it is '
     'a change of address, and they have your address.'),
)

#: What the city says when you have cleared all four and asked.
LEAVING = (
    'It does not take long. That is the part nobody tells you: the whole '
    'apparatus of being somebody in this city comes apart in about four '
    'hours, because almost none of it was ever real. Two accounts closed. A '
    'deck sold to somebody who asked no questions and paid accordingly. A '
    'name given back to the people who rent them out.\n\n'
    'You are on a walkway you have crossed two hundred times, and the city is '
    'doing what it always does, which is not noticing. Somewhere behind you '
    'the board has a job on it that would have been perfect.'
)

#: The ending you get, by how far into the drift you were when you stopped.
#: Keyed to `cyberware.DISSONANCE_BANDS`, and this is why Dissonance is not a
#: gate: refusing to let a chromed character retire would be the game saying
#: their arc has no ending, when what it actually has is a different one.
ENDINGS = (
    (0, 'You get to be a person about it',
     'You sleep badly for a month and then you sleep. Somebody at the market '
     'asks what you used to do and you tell them something dull, and it is '
     'nearly true, and by the third time you say it the dullness has stopped '
     'being a lie and started being the answer.'),
    (25, 'It takes a while to land',
     'The transitions keep happening for a season. You walk into a room and '
     'wait, very briefly, to find out which room it is. It gets further apart '
     'and then it stops, and the stopping is so gradual that you cannot say '
     'afterwards when it happened.'),
    (50, 'Half of you is still in there',
     'You do not go back and you do not stop being somebody who could. There '
     'is a version of every day where you sit down at something and it opens '
     'for you, and you are aware of that version the way you are aware of '
     'weather.\n\n'
     'People who knew you say you are quiet now. You were always quiet. What '
     'they mean is that you answer a beat late, and you always will.'),
    (75, 'You do not so much retire as stop being asked',
     'There is no version of this where you become a person who does '
     'something else. What happens is that the work stops and you keep '
     'running, in a flat somewhere with the lights off, doing whatever it is '
     'you do now, which nobody has a word for and which you would not call a '
     'problem.\n\n'
     'The Aoyama literature has a word for it. You have read the paper. It '
     'still does not describe anything you would call a problem.'),
)


def ending(dissonance: int) -> tuple[str, str]:
    """The ending for a given drift. Always one, never a refusal."""
    out = ENDINGS[0]
    for band, title, text in ENDINGS:
        if dissonance >= band:
            out = (band, title, text)
    return out[1], out[2]


# --------------------------------------------------------------------------
# what is left
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Bequest:
    key: str
    #: 'retired' or 'flatlined'. What kind of ending produces this.
    after: str
    #: One line, on the character sheet of whoever inherits it.
    summary: str
    #: The scene, second person, addressed to the new character.
    text: str


#: The four things that can reach the next runner, and which ending produces
#: which. A retirement leaves what somebody chose to leave; a flatline leaves
#: what could not be stopped from being taken and what could not be forgiven.
BEQUESTS: tuple[Bequest, ...] = (
    Bequest(
        'stake', 'retired',
        'A share of somebody\'s retirement, wired to a name you now use.',
        'The transfer arrives from an account that closed eleven days ago, '
        'with a reference field containing one word, which is a handle you '
        'have heard of and never met.\n\n'
        'There is no note. People who get out properly do not write notes. '
        'What they do, apparently, is leave a standing instruction with a '
        'fixer to find somebody starting, and to not tell them anything '
        'else.'),
    Bequest(
        'name', 'retired',
        'A name that still opens one door, because somebody left it open.',
        'Somebody in Marrow uses a handle that is not yours in a sentence '
        'that is about you. They do it twice more over the next week, in '
        'front of people whose opinion is worth something, and it is a full '
        'month before you work out that this was arranged.\n\n'
        'Whoever did it is not in this city any more, and did this on the way '
        'out, and you will never find out why they picked you.'),
    Bequest(
        'chrome', 'flatlined',
        'A piece of somebody, on a shelf in the Shambles, cheap.',
        'It is in the case at the front, which is where Carrion put the '
        'things that came out of somebody recently, because those are the '
        'ones that still have the serial numbers people check.\n\n'
        'The Blue Surgeon tells you whose it was, unprompted, at length, and '
        'with what you eventually understand is professional respect. Then '
        'they quote you a price that reflects the wear.'),
    Bequest(
        'program', 'flatlined',
        'Somebody else\'s tool, still with their handle in the header.',
        'It comes off a fence in a bundle of four, and three of them are junk. '
        'This one has a comment block at the top of it that somebody wrote at '
        'four in the morning, addressed to nobody, explaining why a thing that '
        'should not work does.\n\n'
        'The handle in the header belongs to a runner the Ninth still talks '
        'about, in the past tense, without ever saying what happened.'),
    Bequest(
        'debt', 'flatlined',
        'Somebody else\'s debt, and the people who held it can count.',
        'They are waiting outside on your second day, which means they knew '
        'where you would be before you did.\n\n'
        'The number is not yours. They know the number is not yours. Their '
        'position, delivered without heat and without any apparent interest '
        'in whether you agree, is that the number is not the sort of thing '
        'that stops existing because the person attached to it did.'),
)

BY_KEY: dict[str, Bequest] = {b.key: b for b in BEQUESTS}


def candidates(after: str) -> list[Bequest]:
    return [b for b in BEQUESTS if b.after == after]


#: How much of a retired runner's stake reaches the next one. Deliberately a
#: fraction: it is a gesture from somebody who has left, not a save file with
#: the difficulty turned down.
STAKE_SHARE = 0.18

#: Reputation floor a remembered name is worth with one faction.
NAME_STANDING = 22

#: What a chrome bequest knocks off the price, and what a debt bequest carries.
CHROME_DISCOUNT = 0.55
DEBT_SHARE = 0.45


#: How the city mentions somebody who is gone. `{handle}` is theirs. Used by
#: the ambient event layer, which is the whole point of the thesis holding:
#: the city remembering you has to be something a later player runs into
#: rather than a line in a menu.
REMEMBERED = (
    'Somebody at the next table is telling a story about {handle}, and it is '
    'not true, and two other people at the table know it is not true and are '
    'letting it happen because the true version is worse.',
    'A fixer uses {handle} as a unit of measurement. "Two of those, maybe '
    'three." Nobody at the table asks what the unit is.',
    'There is a handle scratched into the paint by the transit gate, which is '
    '{handle}, and under it a date, and under that somebody has written a '
    'single word that has been scratched out again by somebody else.',
    'Somebody asks whether you knew {handle}. You did not. They tell you '
    'anyway, at length, and it takes most of it to work out that they did not '
    'either.',
    'The board has a job on it that specifies, in the small print, that the '
    'patron will not work with anybody who worked with {handle}. The job has '
    'been up for nine shifts.',
)
