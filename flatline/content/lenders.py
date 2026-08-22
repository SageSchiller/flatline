"""Who will lend you money, and what they are like about being owed it.

Debt has been in this game since the beginning and it has only ever been
something that *happened* to you: two origins ship with one, and a clinic bill
you cannot cover becomes one. Nobody could ever decide to owe somebody, which
means the most interesting half of the mechanic was missing. A debt you were
handed is a difficulty setting. A debt you chose is a plan that did not work.

**Three lenders, and the difference between them is not the interest rate.**
It is what happens when you stop paying:

- The **Switchboard** are a business. They lend against your reputation and
  they collect against it: fall behind and the work dries up, which in a game
  where the board is the only income is worse than it sounds and slower than
  it sounds, which is exactly how a business hurts you.
- The **Sixes** are a neighbourhood. They lend more than they should to people
  they know, at a rate that reflects that, and they come round in person.
- **Carrion** will lend to anybody, for anything, immediately. They are the
  only ones who never ask what it is for. They are also the only ones who take
  payment in parts, and the Shambles is full of people who found that out one
  instalment at a time.

**The limit is the interesting number, not the rate.** What somebody will lend
you is what they think they can get back, so it scales on your standing with
them and on your record: a runner nobody has heard of gets street money from a
gang and nothing from a broker, and the same runner forty runs later can put a
deck on the Switchboard's tab. Carrion's limit does not scale on anything at
all, which is its own kind of statement.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Lender:
    #: **The faction key.** Deliberately the same identifier: a debt records
    #: who it is owed to, the fallout ladder resolves a visit by asking that
    #: faction what its people do, and two identifiers for one lender is one
    #: identifier plus a bug waiting for the first person who owes the Sixes.
    key: str
    #: Who you actually talk to. Two of the three are people the city already
    #: had, standing where they already stood.
    name: str
    #: District where the conversation can happen, and the service you need.
    where: str
    at: str
    #: Interest per shift, compounding. The house rate is 0.035.
    rate: float
    #: Shifts before they start taking an interest in person.
    grace: int
    #: What they will lend somebody they have never met.
    floor: int
    #: Credits of limit per point of reputation with their faction.
    per_rep: int
    #: Credits of limit per completed run.
    per_run: int
    #: Hard ceiling, however well you are doing.
    ceiling: int
    #: The pitch, printed by `borrow` with no arguments.
    offer: str
    #: What handing the money over looks like.
    handover: str
    #: What they said about what happens if you do not pay, in their words.
    warning: str


LENDERS: tuple[Lender, ...] = (
    Lender(
        'fixers', 'Mara Okonkwo',
        where='marrow', at='fixer',
        rate=0.022, grace=18,
        floor=1200, per_rep=90, per_run=400, ceiling=25000,
        offer='The Switchboard will advance against work. Not against you, '
              'against work: what they will lend is what they think you are '
              'going to earn, and if they have not seen you earn anything '
              'that number is what a payload costs and not a credit more. '
              'Somebody who has burned them is offered less than that, and '
              'at some point a conversation instead.',
        handover='She writes it in a book, turns the book round so you can '
                 'read your own name in it, and waits until you have. Then '
                 'the money is in your account and the book goes back in the '
                 'drawer.',
        warning='"If it stops moving, I stop finding you work. That is the '
                'whole of it. People expect something else and are '
                'disappointed, and then about a month later they are not."'),

    Lender(
        'sixes', 'Auntie Nine',
        where='ninth', at='fence',
        rate=0.038, grace=12,
        floor=1500, per_rep=40, per_run=250, ceiling=12000,
        offer='The Sixes lend on the Ninth the way the Ninth does everything: '
              'more than is sensible, to people they have decided are local, '
              'at a number that reflects how sensible it is not.',
        handover='It comes out of a tin, in cash, counted twice, the second '
                 'time by somebody else who has been sent over specifically '
                 'to count it twice.',
        warning='"We know where you drink. That is not a threat, it is just '
                'true, and the reason it is not a threat is that everybody '
                'here knows where everybody drinks."'),

    Lender(
        'carrion', 'The Blue Surgeon',
        where='shambles', at='clinic',
        rate=0.062, grace=6,
        floor=8000, per_rep=0, per_run=0, ceiling=8000,
        offer='Carrion do not ask what it is for, what you do, or whether you '
              'can pay it back. There is one number and everybody gets the '
              'same one, which they will tell you is fair, and which is.',
        handover='Nobody writes anything down. Somebody takes your picture, '
                 'from three angles, on a device that is doing more than '
                 'taking your picture.',
        warning='"We do not do collections. We do procedures. If you would '
                'rather it were money, and everybody would, then it should '
                'be money."'),
)

BY_KEY: dict[str, Lender] = {x.key: x for x in LENDERS}
LENDER_KEYS: tuple[str, ...] = tuple(BY_KEY)


def here(district: str, services: tuple[str, ...]) -> list[Lender]:
    """Who is lending in this district, given what it has."""
    return [x for x in LENDERS if x.where == district and x.at in services]


def limit(lender: Lender, reputation: int, runs: int, owed: int = 0) -> int:
    """What this lender will put in front of you right now.

    Reputation below zero counts: somebody who has burned this faction is not
    offered the floor, they are offered less than the floor, and at some point
    they are offered a conversation instead.
    """
    total = (lender.floor
             + lender.per_rep * reputation
             + lender.per_run * max(0, runs))
    total = min(lender.ceiling, total)
    # Rounded to something a person would say out loud.
    total = int(total // 100 * 100)
    return max(0, total - max(0, owed))


#: What they say when you ask for more than they will give.
REFUSALS = {
    'fixers': 'She does not say no. She says a number, and the number '
                   'is {limit:,}c, and the difference between those two '
                   'things is the entire Switchboard.',
    'sixes': 'A pause, and then a laugh that is not unkind. {limit:,}c, and '
             'they would like it noted that they are being generous.',
    'carrion': 'The number is {limit:,}c. The number is always {limit:,}c. '
               'Asking for a different one is how they know you are new.',
}

#: What they say when the limit has reached zero, which is a different and
#: worse conversation than being offered less than you asked for.
NOTHING = {
    'fixers': 'She turns the book round again. There is nothing written '
                   'under your name, and she lets you look at the nothing '
                   'for a while before she says anything.',
    'sixes': 'They are sorry. They are actually sorry, which is somehow '
             'worse, and one of them offers you a cigarette on the way out.',
    'carrion': 'Even Carrion have a line, and you have found it by owing '
               'them everything they were ever going to lend you.',
}
