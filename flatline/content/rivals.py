"""The other runners. The city has more than one of you in it.

Rivals exist to make the world move when the player does not. A contract you
spend three shifts deliberating over is a contract somebody else takes, and the
board showing *who took it* is the cheapest possible way to make the city feel
inhabited rather than generated.

They are not a difficulty mechanic. A rival succeeding against Kagawa hardens
Kagawa, which makes the player's next Kagawa job worse, and that is a real
cost, but the point is narrative rather than numeric: over twenty shifts the
player learns that Vesper Okonkwo takes the corporate work and Hound takes
anything violent, and starts reading the board with that in mind.

**Disposition** is how a rival feels about the player specifically. It moves
when you take work they wanted, when you sell them out, and when you cover them
on an escort. At the extremes it changes what they do: a rival who likes you
will pass you work, and one who hates you will take jobs specifically to spite
you and will sell your name if asked.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: How a rival works, which decides what they take and how they fail.
STYLES = ('loud', 'quiet', 'social', 'chrome', 'careful')

STYLE_BLURB = {
    'loud': 'Fast, direct, and gone before the trace lands. Usually.',
    'quiet': 'Never seen, never in a hurry, never carrying much.',
    'social': 'Has never broken a service that would open for a phone call.',
    'chrome': 'More machine than argument. Goes where meat cannot.',
    'careful': 'Reads everything twice and takes half the work on offer.',
}


@dataclass(frozen=True, slots=True)
class RivalType:
    key: str
    name: str
    handle: str
    style: str
    #: Overall competence, 1 to 10. Drives their success roll against posture.
    skill: int
    blurb: str
    #: How they read to somebody who has met them. Shown by `who`.
    manner: str
    #: Objectives they prefer, weighted up when deciding what to take.
    prefers: tuple[str, ...]
    #: Faction standings they start with.
    standing: dict = field(default_factory=dict)
    #: Starting disposition toward the player.
    disposition: int = 0
    #: What they say when they are the escort on a job and things go wrong.
    panic: tuple[str, ...] = ()


RIVALS: tuple[RivalType, ...] = (
    RivalType(
        'vesper', 'Vesper Okonkwo', 'Vesper', 'social', 8,
        'Mara\'s niece, and better at this than Mara ever was. Takes '
        'corporate work almost exclusively, on the theory that corporations '
        'are the only clients who pay on time.',
        'Polite to the point of being unreadable. Has never once raised her '
        'voice on a job and has ended two people\'s careers in writing.',
        prefers=('exfiltrate', 'corrupt', 'surveil'),
        standing={'fixers': 55, 'kagawa': 15, 'sixes': -10},
        disposition=5,
        panic=('"I am going to need you to be somewhere useful, right now."',
               '"This was a bad brief and I took it anyway. My fault. Move."'),
    ),
    RivalType(
        'hound', 'Hound', 'Hound', 'loud', 6,
        'Nobody knows the real name and nobody has asked twice. Takes the '
        'work that involves breaking something, and charges for the noise as '
        'though it were a service.',
        'Talks constantly on a run and says nothing on the street. Genuinely '
        'seems to enjoy this, which everybody finds unsettling.',
        prefers=('wipe', 'escort', 'implant'),
        standing={'carrion': 30, 'sixes': -25, 'nightwatch': -40},
        disposition=-5,
        panic=('"There is a lot of it and it is all looking at me."',
               '"I am going to break something. Stand back or do not."'),
    ),
    RivalType(
        'quietkid', 'The Quiet Kid', 'Quiet', 'quiet', 7,
        'Turned up two years ago with no history and a deck worth more than '
        'the building it was in. Has never been caught, never been '
        'photographed, and never taken a job that pays over four thousand.',
        'Does not speak on jobs. Communicates in file drops. There is a '
        'reasonable argument that nobody has actually met them.',
        prefers=('surveil', 'exfiltrate'),
        standing={'freeport': 35, 'fixers': 20},
        disposition=0,
        panic=('A single dropped file: "leaving".',
               'No message at all. The icon is simply not there any more.'),
    ),
    RivalType(
        'saint', 'Saint Ambrose', 'Saint', 'chrome', 7,
        'Eleven visible pieces and an unknown number of the other kind. '
        'Aoyama funded the first six and has been trying to repossess them '
        'through the courts for three years.',
        'Speaks slightly too slowly, as though translating. Sometimes '
        'answers a question you have not asked yet, which he insists is a '
        'latency artefact.',
        prefers=('implant', 'exfiltrate', 'wipe'),
        standing={'aoyama': -55, 'carrion': 20, 'freeport': 10},
        disposition=0,
        panic=('"I can hold this. I have held worse. Go."',
               '"Do not wait for me. I mean that operationally."'),
    ),
    RivalType(
        'ledger', 'Ledger', 'Ledger', 'careful', 9,
        'The best in the city and takes about one job a month, always after '
        'a fortnight of legwork nobody else can be bothered with. Has never '
        'failed a contract and has declined more than everybody else '
        'combined.',
        'Asks a great many questions before agreeing to anything, and every '
        'one of them turns out to have been the question that mattered.',
        prefers=('exfiltrate', 'corrupt'),
        standing={'fixers': 40, 'freeport': 25, 'nightwatch': -15},
        disposition=0,
        panic=('"I priced this wrong. I am correcting it. Follow me out."',),
    ),
    RivalType(
        'moth', 'Moth', 'Moth', 'loud', 4,
        'Nineteen, brilliant, and going to be dead inside a year at the '
        'current rate. Takes work well above their level because nobody has '
        'ever told them not to.',
        'Enthusiastic in a way that everybody in Marrow finds difficult to '
        'be around, because they have all done the arithmetic.',
        prefers=('exfiltrate', 'wipe', 'escort'),
        standing={'sixes': 15, 'fixers': -5},
        disposition=15,
        panic=('"I do not know what that is. What is that? What IS that?"',
               '"I am fine. I am fine. Am I fine?"'),
    ),
    RivalType(
        'grieve', 'Grieve', 'Grieve', 'quiet', 8,
        'Used to run Nightwatch\'s intrusion response desk, which makes them '
        'the only person in the city who has professionally hunted every '
        'other name on this list.',
        'Watchful and extremely tired. Treats every conversation as an '
        'interview and does not appear to enjoy the habit.',
        prefers=('surveil', 'corrupt', 'wipe'),
        standing={'nightwatch': -35, 'kagawa': 20, 'carrion': -30},
        disposition=-10,
        panic=('"I know what this is. We are leaving. Now, not in a moment."',),
    ),
)

BY_KEY: dict[str, RivalType] = {r.key: r for r in RIVALS}
RIVAL_KEYS: tuple[str, ...] = tuple(BY_KEY)

#: Disposition bands, low bound inclusive. Each label covers from its own
#: bound up to the next, so the band centred on zero has to actually contain
#: zero: a rival at +15 reading as "cold" is a table that has drifted.
DISPOSITION_BANDS: tuple[tuple[int, str], ...] = (
    (-100, 'will sell you'),
    (-60, 'hostile'),
    (-25, 'cold'),
    (-8, 'neutral'),
    (25, 'friendly'),
    (60, 'owes you'),
)


def disposition_band(value: int) -> str:
    out = DISPOSITION_BANDS[0][1]
    for low, name in DISPOSITION_BANDS:
        if value >= low:
            out = name
    return out


#: What the board says when a rival has taken something off it.
TAKEN_LINES = (
    '{name} took it. The posting is gone and so is {name}.',
    '{name} got there first. Marrow knew before the board did.',
    '{name} took {title}. It was on the board and now it is not.',
    '{title} is spoken for. {name}, apparently, and at a discount.',
)

#: What the city hears afterwards.
OUTCOME_LINES = {
    'clean': (
        '{name} came out of {target} clean. Nobody is saying what with.',
        'Word is {name} finished the {target} job without anybody noticing '
        'for two days.',
    ),
    'messy': (
        '{name} got out of {target}, but not quietly. There is a lot of talk.',
        '{name} finished the {target} work and burned an identity doing it.',
    ),
    'failed': (
        '{name} did not come out of {target} with anything. {target} did '
        'come out of it with a file.',
        'The {target} job went badly for {name}. They are not taking calls.',
    ),
    'dead': (
        '{name} flatlined on the {target} job. Nobody is saying whose ICE.',
        'They are holding a wake for {name} in Marrow. {target} has not '
        'commented.',
    ),
}


# --------------------------------------------------------------------------
# the social layer
# --------------------------------------------------------------------------

#: What a rival will do for you, and what asking costs in disposition.
#: Favours are deliberately cheaper than the market rate and deliberately
#: finite: the resource being spent is a relationship, and it does not
#: regenerate on its own.
FAVOURS = {
    'intel': (
        18, 'Everything they know about your target.',
        'Free legwork on the contract you have accepted, at their quality '
        'rather than yours.'),
    'loan': (
        25, 'Money, on the understanding that it is a loan.',
        'Credits now. They will mention it later, and the mentioning is the '
        'interest.'),
    'program': (
        30, 'The loan of something off their deck.',
        'A program from their library, yours until the character dies.'),
    'cover': (
        22, 'Somebody to say you were somewhere else.',
        'Removes a chunk of heat with one faction. They are lying for you and '
        'both of you know what that is worth.'),
}

#: How a rival reacts to being asked when they do not like you enough.
REFUSALS = (
    '"No." There is no second sentence and no visible reconsidering.',
    'They look at you for slightly too long. "Ask somebody else."',
    '"I do not think we are the kind of people who do each other favours."',
    'The call ends. The number stops working about an hour later.',
)

#: Buyers pay for names. What they say when you sell one.
SALE_LINES = (
    'The handover takes six minutes in a car park and nobody uses a name.',
    'You give them the pattern: where {name} works, when, and what they '
    'render as. It is enough. It was always going to be enough.',
    'They do not thank you and they do not look at you twice. The transfer '
    'clears before you are out of the building.',
)

#: What the street says afterwards. Selling somebody is not a private act.
SALE_FALLOUT = (
    'Marrow is quiet about it, which is how you know it is not quiet at all.',
    'Nobody says anything to your face. Two contacts stop returning calls.',
    'Somebody has written a single word on the door of the place you drink. '
    'It is not clever and it is not wrong.',
)

#: What happens to the person you sold.
SALE_OUTCOMES = {
    'taken': (
        '{name} was picked up four shifts later. Nobody has seen them since.',
        '{buyer} took {name} off a street in daylight. It was very quick and '
        'very public and that was clearly the point.'),
    'killed': (
        '{name} did not survive being found. {buyer} are not commenting and '
        'do not need to.',
        'They found {name} first and there was no arrest to report.'),
    'escaped': (
        '{name} got out ahead of it. They know it was somebody. Given time '
        'they will work out it was you.',
        '{buyer} moved on {name} and came up empty. Somebody warned them. It '
        'was not you, which is going to be difficult to prove.'),
}

#: What an ally does that is worth paying for, by style.
ALLY_SPECIALTY = {
    'loud': ('breaks things', 'Adds their skill to your intrusion checks '
             'while they are standing with you, and makes a great deal of '
             'noise doing it.'),
    'quiet': ('goes unseen', 'Reduces the noise of everything you do on the '
              'node they are standing on.'),
    'social': ('talks', 'Adds their skill to pretext and forgery, and can '
               'talk a warden into a delay once per run.'),
    'chrome': ('takes the hit', 'Intercepts countermeasure strikes aimed at '
               'you, at real cost to themselves.'),
    'careful': ('sees it coming', 'ICE tells arrive a tick earlier and traps '
                'are called out before you step on them.'),
}


# --------------------------------------------------------------------------
# arcs
# --------------------------------------------------------------------------
#
# Seven named runners took work off the board for the whole life of this
# project and the entire relationship was one number between -100 and 100.
# The bands above named it, `who` printed the name, and nothing ever came of
# it: somebody at -80 competed with you in exactly the way somebody at zero
# did, and so did somebody at +80.
#
# **A bond is that number becoming a person.** It latches at either end,
# announces itself once with a scene, and then changes what that runner does
# on the shift boundary for the rest of the campaign. Latching rather than
# tracking the number is deliberate: a nemesis who stopped being one because
# you did them a favour on a Tuesday is a mood, and what makes thirty runs
# with somebody worth having is that it does not come off.

#: Where the two ends are, and how much history it takes to get there. Both
#: gates matter: crossing on disposition alone would let one betrayal on your
#: fourth shift produce a lifelong enemy, and the arc is supposed to be the
#: length of a campaign.
NEMESIS_AT = -60
PARTNER_AT = 60
BOND_AFTER_JOBS = 4

#: What a bond does on the shift boundary, per side.
BOND_KINDS = ('nemesis', 'partner')

#: The scene when somebody crosses. Printed once, ever, per runner, and it is
#: the whole reason the bond exists rather than being a modifier.
NEMESIS_DECLARED = {
    'loud': '{name} has started saying your name in rooms you are not in, '
            'and saying it the way you would name a weather event. It is not '
            'a threat and it is much worse than one: it is advertising.',
    'quiet': 'Nothing is said. You simply notice, over about a fortnight, '
             'that {name} is where you were going to be, slightly before you '
             'get there, and has been for longer than you noticed.',
    'social': '{name} is extremely warm about you in public and has stopped '
              'returning anything in private, and three people who used to '
              'take your calls now take a beat before they answer.',
    'careful': '{name} has filed you. Not with anybody: with themselves, in '
               'the way they file everything, and the difference between '
               'being filed by them and being hunted by anybody else is that '
               'the file is accurate.',
    'chrome': '{name} does not appear to have decided anything about you. '
              'What has happened is that a decision was made somewhere in '
              'the stack that runs them now, and they are carrying it out '
              'with the same evenness they carry out everything.',
}

PARTNER_DECLARED = {
    'loud': '{name} tells somebody, loudly, in front of you, that you are '
            'the only person in this city who has never once let them down. '
            'It is not true. They have decided it is true, which in this '
            'business is the same thing and lasts longer.',
    'quiet': '{name} starts leaving things where you will find them. A route '
             'that is open. A name that is worth having. Nothing is ever '
             'said about any of it and nothing ever will be.',
    'social': '{name} begins introducing you as a colleague, which from them '
              'is a technical term with a great deal of machinery behind it, '
              'and the machinery starts moving about a week later.',
    'careful': '{name} runs the numbers on you one more time, apparently, '
               'and comes back with a conclusion they are willing to act on. '
               'From Ledger that is the loudest thing that has ever '
               'happened.',
    'chrome': '{name} keeps a channel open to you. It is not a metaphor and '
              'it is not entirely comfortable, and it means that at three in '
              'the morning, when something goes wrong, somebody already '
              'knows.',
}

#: What each side does on a shift, occasionally. One thing each, kept small:
#: a bond that fired every shift would be a weather system rather than a
#: relationship.
BOND_CHANCE = 0.16

NEMESIS_ACTS = (
    '{name} has been talking to {faction} about you. Nothing actionable. '
    'Just enough that your name arrives before you do.',
    'A posting you were reading yesterday is gone, and the patron will not '
    'say to whom, and you do not have to ask, because it was {name}.',
    'Somebody describes you accurately to somebody else in a bar in the '
    'Ninth, and the description came from {name}, and it is not unkind, '
    'which is the part that will cost you.',
)

PARTNER_ACTS = (
    '{name} sends over something they did not have to. It is not much. It is '
    'the kind of not much that took them a shift to get.',
    'A door somebody was going to close stays open, and nobody explains why, '
    'and {name} is not answering their handset this evening.',
    '{name} puts your name to a patron who was not going to think of it. '
    'They mention it in passing, the way you mention weather.',
)

#: The heat a nemesis quietly adds to whoever you last worked against, and
#: the heat a partner takes off. Small per event and relentless.
NEMESIS_HEAT = 6
PARTNER_HEAT = 8


# --------------------------------------------------------------------------
# the reckoning (D119)
# --------------------------------------------------------------------------
#
# A nemesis was a weather system with no season: heat every few shifts and no
# way to make it stop that was not paying them off, which is a transaction and
# not an ending. An arc wants a place it comes to a head. So once the
# grievance has gone deeper than the declaration and stayed there, the nemesis
# stops working through the city and comes to find you in it, and it is
# settled one way or another, in the words the street already uses: you
# [fg]face[/] them, you [fg]settle[/] it, or you [fg]walk[/] and leave it for a
# night you are readier for.

#: Deeper than NEMESIS_AT, because the reckoning is the end of the arc and not
#: the middle of it: it takes a campaign of being crossed to get here.
RECKON_AT = -80
#: The base price of buying the peace, scaled by how good they are. Real money,
#: because a settlement that did not cost is not a settlement.
RECKON_COST = 3400

#: Them finding you, per style. The one flavourful beat; the outcomes below
#: are shared, because what a reckoning resolves is the same whoever it is.
RECKON_SETUP = {
    'loud': '{name} is in the doorway of wherever you were going, not '
            'pretending to be anywhere else, and loud enough that the street '
            'has stopped to watch how this goes. They have decided it goes '
            'here.',
    'quiet': '{name} is sitting where you were going to sit, and has been for '
             'a while, and does not get up. There is no message and there was '
             'never going to be one. This is the message.',
    'social': '{name} is smiling at you across a room that has gone quiet in '
              'the specific way a room goes quiet when everybody in it has '
              'already heard the story and is waiting to see which version is '
              'true.',
    'careful': '{name} has arranged to be exactly here, exactly now, with '
               'exactly you, which from them is not a coincidence and not a '
               'threat. It is a conclusion, and you are standing in it.',
    'chrome': '{name} is waiting with the stillness of something that has '
              'nowhere else it needs to be. Whatever runs them decided this '
              'was worth their time, and it does not spend their time on '
              'things it expects to lose.',
}

#: What you settle it with. Read to the player as the sum behind each answer,
#: exactly as the street reads its own.
RECKON_FACE_WIN = (
    'You stand in it and do not give them the inch. It turns out that is the '
    'whole of what they came for, and it is not there, and something goes out '
    'of {name} that does not come back tonight. The street saw. That is worth '
    'more than the fee, and it will cost {name} more than it cost you.')
RECKON_FACE_LOSE = (
    'You stand in it and {name} takes the inch anyway, in front of the people '
    'it will travel to. You are still standing when it is over. You are just '
    'standing smaller, and the city files the difference.')
RECKON_SETTLED = (
    'You pay {name} what it takes, and it takes a real number, and the thing '
    'in the air goes out of it. Bought peace is still peace. It holds for '
    'exactly as long as you keep being worth more to them alive and quiet '
    'than loud.')
RECKON_WALKED = (
    'You are not doing this tonight. You turn the way you were already going '
    'and you keep going, and {name} lets you, because a reckoning you refuse '
    'is a reckoning they get to have again, on a night that suits them '
    'better.')


# --------------------------------------------------------------------------
# the offer (D121)
# --------------------------------------------------------------------------
#
# The partner's culmination, and the mirror of the reckoning. A nemesis deep
# enough comes to settle; a partner deep enough comes to stay. Crewing has
# always been a thing you go and do to somebody willing (`crew take`); this is
# the other direction, the one that reads as a relationship rather than a
# hire: they come to you, and they waive the retainer, because past a certain
# point the money was never the thing.

#: Deeper than PARTNER_AT, because signing on for good is more than deciding
#: you are worth a job.
PARTNER_OFFER_AT = 85

#: Them coming to you, per style. Once, if you have nobody on a retainer yet.
PARTNER_OFFER = {
    'loud': '{name} finds you before you find the work, and says it the way '
            'they say everything, which is out loud and in front of people: '
            'they are done running alone, and they would rather run with you '
            'than anybody, and they are not charging you the usual to do it.',
    'quiet': '{name} is there when you turn around, which they are not, '
             'usually, and they say it once and plainly: they would run every '
             'night with you, from here, and there is no retainer in it. It '
             'is the most they have ever said at once.',
    'social': '{name} sits down across from you without being asked, which '
              'from them is a contract in itself, and lays it out warmly and '
              'exactly: a standing arrangement, no retainer, their cut and '
              'their skill and their word, because they have run the numbers '
              'on you enough times to stop running them.',
    'careful': '{name} has clearly decided this well before saying it: they '
               'will run with you, on a standing basis, and they are waiving '
               'the retainer, which from somebody who prices everything is '
               'the loudest thing they could possibly do.',
    'chrome': '{name} tells you, with the evenness they tell you everything, '
              'that whatever runs them has concluded you are worth being '
              'beside, permanently, and that the arrangement comes without a '
              'retainer, which is not a discount. It is a decision.',
}

PARTNER_OFFER_YES = (
    '{name} is your crew from tonight. No retainer, their word, and somebody '
    'standing next to you on the thirtieth run who is there because they '
    'chose to be and not because you paid for it. That is a different kind of '
    'thing to lose, later, and you both know it.')
PARTNER_OFFER_NO = (
    'You leave it where it is. {name} takes it the way they take everything, '
    'which is without a word about it, and the offer does not come again, '
    'though the door it came through does not close: `crew take {handle}` is '
    'still there, on the usual terms, whenever you are.')


# --------------------------------------------------------------------------
# a crew
# --------------------------------------------------------------------------
#
# `hire` buys one runner for one job and then forgets them. That is a
# transaction, and a transaction cannot be lost. Somebody who comes back, gets
# better at working specifically with you, and is standing next to you on the
# thirtieth run is a different kind of thing entirely, and the whole reason to
# build it is what happens when they do not come out.

#: Disposition needed before somebody will sign on permanently. Well above the
#: hire floor: taking a job with you and working with you are different asks,
#: and only one of them means they have decided you are worth it.
CREW_AT = 30

#: What a retainer costs, per point of their skill, and what they take of
#: every haul. Cheaper per run than hiring and much more expensive to start,
#: which is what makes it a commitment rather than a discount.
CREW_RETAINER = 1400
CREW_CUT = 0.18

#: Runs together per point of effective skill they gain, and the cap. They get
#: better at working with *you* specifically, which is a real thing and is not
#: the same as getting better.
CREW_RUNS_PER_STEP = 5
CREW_MAX_STEPS = 3

#: What they say when they sign on, by style.
CREW_JOINED = {
    'loud': '"Right. I am not doing the thing where we pretend this is job '
            'by job." {name} shakes your hand far too hard and appears to '
            'consider the matter closed and possibly always to have been.',
    'quiet': '{name} does not say yes. {name} turns up the next time you go '
             'in, and the time after that, and about a fortnight later you '
             'realise nobody ever actually agreed to anything.',
    'social': '"Let us be clear about what this is." {name} is clear about '
              'what this is for eleven minutes, and every word of it is '
              'accurate, and none of it is what they mean.',
    'careful': '{name} asks four questions. They are the four questions you '
               'would have asked, in the order you would have asked them, '
               'and the last one is about what happens if one of you stops '
               'being able to do this.',
    'chrome': '{name} agrees in about a tenth of a second and then sits with '
              'it for a while, which is the longest you have seen them take '
              'over anything.',
}

#: And when you end it. Nobody takes this well; they take it differently.
CREW_RELEASED = {
    'loud': '{name} says it is fine about six times, at volume, to people who '
            'did not ask.',
    'quiet': '{name} nods, and is gone before you have finished, and you '
             'find out later that they had worked it out a week ago.',
    'social': '{name} is gracious, warm, and completely finished with you, '
              'and manages all three in the same sentence.',
    'careful': '{name} agrees that it was the correct decision, and gives '
               'two reasons you had not thought of, and you feel worse rather '
               'than better.',
    'chrome': '{name} says thank you, which nobody has ever heard them say, '
              'and it is not clear to either of you why.',
}

#: What losing one is, by how long they had been with you. This is the entire
#: point of the system: a hire dying is a line of news.
CREW_LOST = (
    (0, '{name} does not come out. You had been working together for {runs} '
        'runs, which is not long, and it turns out to be long enough that '
        'you keep turning to say something to somebody who is not there.'),
    (8, 'You had {runs} runs with {name}. Long enough to have a way of doing '
        'things. Long enough that half of what you know about working with '
        'anybody, you learned from doing it with them.\n\n'
        'The Ninth puts a plate on a railing for people like this. Somebody '
        'will do it without asking you, and you will find it by accident, and '
        'that will be considerably worse than being invited.'),
    (20, '{runs} runs. There is no version of this you have a way of holding. '
         '{name} had opinions about how you work that you have been carrying '
         'around for a year without noticing whose they were, and you are '
         'going to keep having them, in their voice, for the rest of it.\n\n'
         'Nobody in this city is going to say a word about it to you. That is '
         'not coldness. It is that there is nothing to say and everybody here '
         'has already found that out.'),
)


def crew_loss(runs: int) -> str:
    """The right words for losing somebody, by how long they were there."""
    out = CREW_LOST[0][1]
    for after, text in CREW_LOST:
        if runs >= after:
            out = text
    return out
