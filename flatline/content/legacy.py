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


#: D51. The spine reads back into the ending. Taking Deepwater's retainer
#: replaces the drift ending outright, because there is no version of that
#: arc that ends in being a person about it; the other two outcomes leave a
#: coda on whatever the drift had to say. Declared so `validate.py` can see
#: these flags are decisions a choice makes.
ENDING_FLAGS = ('dw_employed', 'dw_published', 'dw_refused', 'dw_under')

RETAINED = (
    'The retainer does not lapse',
    'You stop taking contracts, and the retainer keeps clearing, on the '
    'first of the month, itemised, from an account that has been paying nine '
    'years of runners and has never met one. Nothing is asked of you. The '
    'money is real. Networks you have never run still feel, when somebody '
    'describes them, like a word somebody has just said.\n\n'
    'You do not know whether you retired. You know that you stopped, and that '
    'something did not, and that the difference is the kind of thing Remnant '
    'would have wanted a third fact about.')

CODAS = {
    'dw_published':
        'Years later somebody at the market mentions the Static piece, the '
        'one with the nine logs in it, and you watch the conversation move on '
        'without anybody moving it, and you understand that you are never '
        'going to find out, and that it was the last thing you did in the '
        'city that anybody noticed not noticing.',
    'dw_refused':
        'The noodle bar has four landlines. One of them has never rung in '
        'anybody\'s hearing. You think about it more than you expected to, '
        'and less every year, and never not at all.',
}


def ending(dissonance: int, flags=()) -> tuple[str, str]:
    """The ending for a given drift, and what the spine did to it.

    Always one, never a refusal. Drift picks the body; the decisions you made
    about Deepwater either replace it or leave a coda on it.
    """
    if 'dw_employed' in flags:
        return RETAINED
    out = ENDINGS[0]
    for band, title, text in ENDINGS:
        if dissonance >= band:
            out = (band, title, text)
    title, text = out[1], out[2]
    for flag, coda in CODAS.items():
        if flag in flags:
            text = f'{text}\n\n{coda}'
    return title, text


# --------------------------------------------------------------------------
# what you left behind, in people (D51)
# --------------------------------------------------------------------------

#: One line per decision, read back at the end, whichever end it is. Every
#: flag a choice sets and nothing else sets has a line here, and `validate.py`
#: fails the build on a decision this forgets, because an ending that does
#: not mention what you did to Lark is an ending to somebody else's game.
EPILOGUE: tuple[tuple[str, str], ...] = (
    # Deepwater
    ('dw_employed',
     'Deepwater hired you, and you took it, and the money was real, and you '
     'never again ran a network that felt entirely unfamiliar.'),
    ('dw_refused',
     'Deepwater hired you and you handed it back. Nothing pursued you. Mara '
     'has four landlines now and one of them has never rung.'),
    ('dw_published',
     'You gave Deepwater to Static, the nine logs and the name, and for a day '
     'it was the only thing in Marrow, and then it was not a thing anybody '
     'said, and nobody will tell you why.'),
    ('dw_read',
     'You read your own log to the end, including the entry for the day '
     'after tomorrow, which was a Tuesday, and some of it is in you now the '
     'way a tune is.'),
    ('dw_archived',
     'You gave your log to the Archivist, who put it on its own shelf '
     'because it was still being written, and did not know how to file '
     'that.'),
    ('dw_burned',
     'You wiped your own log, and it took longer than a file takes, and your '
     'deck ran a fraction cooler afterwards, which you decided not to have '
     'noticed.'),
    ('dw_under',
     'It asked, and you went under, with nothing loaded and no contract, and '
     'the chair was found occupied and the trace at zero.'),
    ('dw_stayed',
     'It asked, and you said no, plainly, once, and it did not ask again, '
     'and the quiet of that was the loudest thing in every network you ran '
     'afterwards.'),
    # Lark
    ('lark_saved',
     'Lark is alive. Smaller, quieter, arguing with a queue outside the '
     'clinic, alive.'),
    ('surgeon_owed',
     'The Blue Surgeon owed you eleven hours, and did not keep count, and '
     'said so.'),
    ('vance_owed',
     'Doctor Vance owed you something and paid it without a note, which is '
     'how she pays.'),
    ('lark_dead',
     'Lark died on a crate outside the Shambles clinic, and somebody left a '
     'jacket on it, and you did nothing, which you were allowed to do.'),
    # Vance
    ('vance_employed',
     'You found people for Doctor Vance. They were going to die and did not, '
     'and the paperwork was immaculate, and you never managed to say what '
     'was wrong with it.'),
    ('vance_refused',
     'You told Doctor Vance no. She closed the file and did not hold it '
     'against you, and the door stayed open, and you never went back '
     'through it.'),
    ('vance_exposed',
     'You took Doctor Vance to Static. Nothing happened to her. Two of her '
     'patients stopped being her patients and one of them died.'),
    # Mr Sunday
    ('sunday_known',
     'You worked out who Mr Sunday works for and told him so, and he bought '
     'you a drink, and the work was still good.'),
    ('sunday_sold',
     'You sold what you worked out about Mr Sunday to Freeport, and Meridian '
     'read it, and he stopped appearing, and you never found out whether '
     'that meant anything.'),
    ('sunday_kept',
     'You worked out who Mr Sunday works for and kept taking the work, '
     'because the work was good, and it was, for a long time.'),
    # Sparrow
    ('sparrow_geared',
     'You gave the Kestrel kid a masking layer and a breaker that would not '
     'kill them on a Tuesday. They are still running. They are insufferable '
     'about it.'),
    ('sparrow_taught',
     'You taught the Kestrel kid the trace, properly, with the numbers. They '
     'argued for an hour and then wrote it down. They are still running, and '
     'they leave clean.'),
    ('sparrow_scared',
     'You frightened the Kestrel kid out of it with Lark\'s name. It worked. '
     'They work a counter in Marrow and do not look up.'),
    # The drawer
    ('drawer_clinic',
     'You followed the clinic reports in Achebe\'s drawer to the Blue '
     'Surgeon, whose records were immaculate, and every referral went to '
     'Aoyama Green.'),
    ('vance_suspect',
     'You knew about Doctor Vance before she told you, which did not make '
     'her easier to refuse.'),
    ('drawer_accounts',
     'You followed the account reports in Achebe\'s drawer: four families, '
     'nine years, and something logging in as patiently as the dead.'),
    # The archive
    ('archive_consented',
     'You told the Archivist they could have your log, when it came to it. '
     'They wrote it in a book.'),
    ('archive_refused',
     'You told the Archivist no. They said of course, and meant it, and were '
     'warmer to you afterwards.'),
    # The laptop
    ('laptop_returned',
     'You gave Kagawa the laptop back unopened and told them the truth, and '
     'they believed you, which meant they had known already.'),
    ('laptop_read',
     'You read the third partition. Eleven thousand files, four hundred '
     'assessments, and your own number, which was low.'),
    ('laptop_sold',
     'You sold Kagawa\'s laptop to Meridian, who paid a great deal and did '
     'not run it, and the files have not surfaced, and you still wonder '
     'which decision that was.'),
    # The Sixes
    ('theirs_owned',
     'The Sixes asked and you did it, and it was easy, and the warmth was '
     'real, and there was never a moment where refusing would obviously '
     'have been better.'),
    ('theirs_refused',
     'The Sixes asked and you said no, and nobody in the Ninth was ever rude '
     'to you again, and nobody in the Ninth was anything else either.'),
    # Mara
    ('favour_done',
     'You went where Mara could not be seen going, and found a woman who has '
     'been alive for nineteen years on the understanding that nobody knows '
     'she is, and Mara never raised it again.'),
    ('favour_refused',
     'You asked Mara what the favour was before you would do it, and she '
     'said no, and the noodle bar changed shape permanently.'),
    # The lender
    ('lender_paying',
     'You paid the lender what you had and got a receipt, the first document '
     'anybody gave you in the whole affair.'),
    ('lender_working',
     'You offered to work the loan off, and they were delighted, and you '
     'understood later that this had always been the product.'),
    ('lender_angry',
     'You kept moving and said nothing to the lender, and on the fifth shift '
     'the deck was gone and the number had been revised.'),
    # The file
    ('file_stale',
     'You left the Nightwatch file nineteen months out of date, and Achebe '
     'was careful to have offered no opinion.'),
    ('file_closed',
     'You had the Nightwatch file closed properly, with a reason that was a '
     'lie that held up. Somebody, eventually, is going to check.'),
    # The maintenance address
    ('maint_cut',
     'You cut the maintenance address. The suite worked as before, and '
     'eleven shifts later your left eye developed a lag on low light that no '
     'clinic can find a cause for.'),
    ('maint_fed',
     'You left the maintenance address running and decided what it saw. It '
     'was the most enjoyable eleven minutes of your month.'),
    ('maint_asked',
     'You asked Aoyama about the maintenance address, and Doctor Vance '
     'answered in person, delighted, with the consent form.'),
    # The buyout
    ('buyout_extended',
     'You went to the buyout review. The number came down by nine thousand '
     'and the terms went out by four years, and you signed because the '
     'arithmetic was correct.'),
    ('buyout_ignored',
     'You did not go to the buyout review. The figure was revised upward '
     'without explanation, and the letter was exactly as warm.'),
    # The incident file
    ('incident_known',
     'You asked Old Pike what actually happened, and he told you, and it was '
     'not what you remembered, and you slept badly and then, for the first '
     'time in four years, well.'),
    ('incident_left',
     'You decided you did not want to know what was in the incident file, '
     'and Old Pike said good, and did not look at you differently.'),
    # The old name
    ('oldname_reclaimed',
     'You took your old name back, which left you holding a name you did not '
     'want and somebody else without one.'),
    ('oldname_left',
     'You let somebody else keep your old name. They filed the paperwork, '
     'and somewhere in a municipal system you are marginally more alive than '
     'you were.'),
    # The package
    ('package_delivered',
     'You delivered the package, two years late, to somebody who signed for '
     'it and thanked you, and the standing order stopped the following '
     'month.'),
    ('package_opened',
     'You opened the package. It was addressed to you. It had always been '
     'addressed to you.'),
    ('package_burned',
     'You put the package in an incinerator in the Ninth and stayed for all '
     'of it.'),
    # The districts (D55)
    ('pumps_sixes',
     'You took the water board\'s ledger out of Kagawa and handed it to the '
     'Sixes, and the pumps under the Ninth run on parts with a stencil on '
     'them.'),
    ('pumps_public',
     'You gave Static the DEFERRED column, nineteen years then a line, and '
     'the water board issued a statement, and the pumps did not change.'),
    ('pumps_sold',
     'You sold the water board its own ledger back, and the thanks was '
     'sincere, and somebody in the Ninth stopped selling you fried things.'),
    ('queue_jacket',
     'You ruled that a jacket holds a place in the Marrow queue, and became '
     'law, and had not meant to.'),
    ('queue_person',
     'You ruled that only a person holds a place in the Marrow queue, and '
     'the woman in the green coat said strict holds, and it held.'),
    ('queue_declined',
     'You declined to rule on the queue, and she ruled herself, and you '
     'never knew what she decided.'),
    ('reviews_fair',
     'You moved eleven numbers toward each other in Kagawa\'s review suite, '
     'and the satisfied-client poster came down, and nobody put another up.'),
    ('reviews_self',
     'You put your own number up in Kagawa\'s review suite, and the lobby '
     'has read you as furniture ever since.'),
    ('reviews_left',
     'You had the review suite\'s weights open and left the arithmetic '
     'correct.'),
    ('ward_walked',
     'You walked somebody out of the aftercare ward in forty seconds, and '
     'they said she was right, they were well, and went.'),
    ('ward_told',
     'You told Doctor Vance about the finger on the glass, and the window '
     'was frosted, and she sent you something small and expensive.'),
    ('ward_left',
     'You saw the finger on the glass twice and did nothing, and the third '
     'time it was somebody else.'),
    ('demo_free',
     'You wiped the reset policy off Sendai\'s floor and left the unit to '
     'think, and it reads from memory, with feeling, to an audience.'),
    ('demo_sold',
     'You wiped the reset policy and then told Sendai what was on their '
     'floor, and they reset it on the sixteenth instead.'),
    ('vote_spoke',
     'You stood at the west gate and spoke, badly, and Freeport voted your '
     'way, and the losing side bought.'),
    ('vote_quiet',
     'You stayed at the back while Freeport voted on you, and it went the '
     'other way, by a little.'),
    ('surplus_wiped',
     'You wiped fifteen entries from Nightwatch\'s evidence log, four of '
     'them yours, and the box on the surplus counter was sold as a box.'),
    ('surplus_read',
     'You read what Nightwatch had written about you before you wiped it, '
     'and it was good, and you could not wipe having read it.'),
    ('ledger_taken',
     'You took the Blue Surgeon\'s referral ledger for Carrion while the '
     'door was open, and the Surgeon said nothing and started another.'),
    ('ledger_warned',
     'You told the Blue Surgeon that Carrion wanted the ledger taken, and '
     'they showed it to him instead, page by page.'),
    ('trays_saved',
     'You made the landing inspection skip level forty, and the tomatoes '
     'went on under a borrowed light, and it was not a transaction.'),
    ('trays_sold',
     'You flagged level forty for priority and took the finder\'s fee, and '
     'the landing was bare the next time you passed.'),
    # The other runners (D56)
    ('with_vesper',
     'Vesper Okonkwo called you a colleague, and you let the machinery move, '
     'and it moved.'),
    ('apart_vesper',
     'Vesper Okonkwo called you a colleague, and you kept it clean, and she '
     'meant it slightly less for the rest of your career.'),
    ('paid_vesper',
     'Vesper Okonkwo named a figure at which it would stop, through Mara, '
     'and you paid it, and it held.'),
    ('stood_vesper',
     'Vesper Okonkwo named a figure and you did not pay it, and you learned '
     'which patrons she had talked to by who stopped posting.'),
    ('with_hound',
     'Hound wanted to be on the same jobs, and was, uninvited, and the '
     'noise was always somewhere else.'),
    ('apart_hound',
     'You told Hound you work alone, and they said that was fine six times, '
     'at volume.'),
    ('paid_hound',
     'You paid Hound to stop saying your name in rooms, and they stopped, '
     'loudly.'),
    ('stood_hound',
     'You did not pay Hound, and everybody in the city knew your name for a '
     'year, and not in the way that helps.'),
    ('with_quietkid',
     'A route arrived with no sender and you used it, and another came the '
     'next week, and you never met the Quiet Kid, and you were partners.'),
    ('apart_quietkid',
     'You dropped one line back to the Quiet Kid, which was no, and nothing '
     'ever arrived again.'),
    ('paid_quietkid',
     'You paid the Quiet Kid\'s number and they were never where you were '
     'going to be again, or anywhere.'),
    ('stood_quietkid',
     'You did not pay the Quiet Kid, and they were where you were going to '
     'be, slightly before, for the rest of it.'),
    ('with_saint',
     'You kept Saint Ambrose\'s channel open, and at three in the morning, '
     'twice, somebody already knew.'),
    ('apart_saint',
     'You closed Saint Ambrose\'s channel, and he said yes, that is wise, '
     'before you had asked.'),
    ('paid_saint',
     'You paid the stack that runs Saint Ambrose, and whatever it had '
     'decided was undecided, evenly.'),
    ('stood_saint',
     'You did not pay the stack, and Saint Ambrose carried it out evenly '
     'and courteously for the rest of your career, and was once, you think, '
     'sorry.'),
    ('with_ledger',
     'You took Ledger\'s second job each month, and it never once failed, '
     'and you knew what it was costing them.'),
    ('apart_ledger',
     'You said no to Ledger, and Ledger gave two reasons you had not '
     'thought of, and you felt worse.'),
    ('paid_ledger',
     'You paid Ledger to close the file, and it stayed closed, because '
     'Ledger said it would.'),
    ('stood_ledger',
     'You left Ledger\'s file open and accurate, and patrons asked you the '
     'right question every so often, and you knew whose it was.'),
    ('with_moth',
     'You took Moth on the next one, and they nearly died twice in eleven '
     'ticks, and you got them out.'),
    ('apart_moth',
     'You told Moth no, and they took something above their level the next '
     'day, and it was fine, that time.'),
    ('paid_moth',
     'You paid Moth a figure that was too high, and Moth spent it in a '
     'week, and was nineteen.'),
    ('stood_moth',
     'You did not pay Moth, and they said your name badly in rooms and then '
     'tried to prove a point, and you heard later than you should have.'),
    ('with_grieve',
     'Grieve left names where you would find them and you used them, and '
     'neither of you ever mentioned it, and it was the most reliable thing '
     'in your career.'),
    ('apart_grieve',
     'You left Grieve\'s name where it was, and Grieve noticed, and every '
     'conversation was an interview again.'),
    ('paid_grieve',
     'You paid Grieve a figure that was exactly fair, and they were simply '
     'somewhere else afterwards.'),
    ('stood_grieve',
     'You did not pay Grieve, and Grieve hunted you professionally, '
     'patiently, and filed the reports.'),
)

EPILOGUE_BY_FLAG: dict[str, str] = {flag: line for flag, line in EPILOGUE}


def epilogue(flags) -> list[str]:
    """The lines for what this character decided, in the order written."""
    return [line for flag, line in EPILOGUE if flag in flags]


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
