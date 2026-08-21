"""What the seventeen people in this city will actually do for you.

`Npc.offers` has declared work, goods, intel and favours since the cast was
written, and `who is` has printed the list, and for four of those it printed a
label attached to nothing. Intel was real, through `ask`. The other twelve
declarations were decoration on people who were otherwise very well written.
That is this project's oldest bug class living in the most human part of the
game, which is the worst place for it: a character who exists to have an
opinion about what you are doing and cannot be asked for anything is a
newspaper.

**The three of them are one relationship, not three features.**

- **Work** is a contract that never reaches the board. It pays better, because
  they know you, and it is a job from a person rather than from a market, so
  dropping it costs something a board contract cannot charge.
- **A favour** is them spending their own standing on your problem. You can
  ask for one whether or not you have earned it, and the asking is recorded.
- **What you owe** is the number in the middle. Every favour puts you one
  deeper with that person; finishing a job they gave you clears one. Ask for
  more than they think you are good for and they stop taking your calls, in
  their own words, which are not always unkind.

So the loop is: they trust you enough to hand you work, the work buys favours,
and the favours are what you actually wanted. A player who only ever takes and
never delivers runs out of people, one at a time, and the city gets quieter in
a way nobody announces.

**Goods** sit outside that. A shopkeeper is not a friend and does not need to
be: what they have is theirs, it does not rotate with the market, and it is
the only route to several things in this game.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: How deep you can get with one person before they stop helping. Small, so
#: the ceiling is felt rather than theoretical.
OWED_LIMIT = 3

#: Shifts between jobs from the same person. A relationship rather than a
#: vending machine: somebody who has something for you every single shift is
#: a second contract board with a face drawn on it.
WORK_EVERY = 8


@dataclass(frozen=True, slots=True)
class Work:
    """A job from a person. Generated like any other and then bent."""

    npc: str
    #: The faction whose money it is. They are fronting for somebody.
    patron: str
    #: Who they want hit, weighted. Empty means the ordinary relations table.
    targets: tuple[str, ...] = ()
    #: Multiplier on the pay a board contract of the same shape would carry.
    pay: float = 1.0
    #: How much longer than a board posting it stays open, in shifts. They
    #: are holding it for you, which is most of what personal work is.
    patience: int = 6
    #: Requirements, in `Story.satisfied` syntax.
    requires: tuple[str, ...] = ()
    #: How they put it, before you accept.
    pitch: str = ''
    #: What they say as you take it.
    closing: str = ''
    #: What they say if you drop it. There is no board equivalent of this.
    dropped: str = ''


WORK: tuple[Work, ...] = (
    Work(
        'mara', patron='fixers',
        pay=1.15, patience=8,
        requires=('runs:1',),
        pitch='"Something came in that I am not putting on the board. Not '
              'because it is worse than what is on the board. Because the '
              'person who brought it in asked me not to, and I have known '
              'them a long time, and you are the shape of thing they '
              'described without knowing they were describing it."',
        closing='"Good. I will tell them it is handled, which is a thing I '
                'would like to keep being able to say."',
        dropped='"That is fine." It is not fine, and she does not pretend it '
                'is, and she does not raise her voice about it either. She '
                'simply writes something short in the book and turns the page.'),
    Work(
        'lark', patron='carrion', targets=('kagawa', 'aoyama', 'sendai'),
        pay=1.3, patience=4,
        requires=('runs:3', 'not:lark_dead'),
        pitch='"There is a thing I want doing and I cannot pay what it is '
              'worth, so I am paying what I have, which is more than it is '
              'worth to anybody who is not me." She does not explain the '
              'difference and does not intend to.',
        closing='"Right." She looks at you for slightly too long, the way '
                'people do when they have decided to be hopeful and are out '
                'of practice.',
        dropped='She takes it better than you expected, which is the part '
                'that stays with you. The Shambles is full of people who have '
                'learned to take things well.'),
    Work(
        'vance', patron='aoyama', targets=('sendai', 'kagawa', 'meridian'),
        pay=1.1, patience=10,
        requires=('runs:2', 'met:vance', 'not:vance_exposed'),
        pitch='"The clinic has an interest here and the clinic cannot be seen '
              'to have an interest here. I am telling you that plainly '
              'because the alternative is telling you something else and then '
              'you finding out, and I have no appetite for the version of '
              'this evening where that happens."',
        closing='"Thank you. I will have the fee routed through something '
                'that will not embarrass either of us."',
        dropped='"Understood." The word costs him nothing and he spends it '
                'like it does, which is how you know the answer is no next '
                'time as well.'),
    Work(
        'broker', patron='freeport', targets=('kagawa', 'nightwatch'),
        pay=1.25, patience=5,
        requires=('runs:4', 'not:sunday_sold'),
        pitch='"I am going to describe a job and I am going to tell you which '
              'parts of the description are true. That is not a courtesy. It '
              'is that I have watched four people take this without asking '
              'and I would like the fifth one to come back."',
        closing='"Then we understand each other, which puts us both ahead of '
                'where we were."',
        dropped='Mr Sunday nods, and it is impossible to tell whether that '
                'cost you anything at all, which is exactly the effect he has '
                'spent thirty years building.'),
)


@dataclass(frozen=True, slots=True)
class Stock:
    """What somebody keeps under their own counter.

    Fixed rather than rotated. The market's whole design is that stock turns
    over and that is a reason to travel and a reason to hurry; a person's
    stock is the opposite thing, and it is the only reliable supply of
    several items in this game.
    """

    npc: str
    #: Catalogue keys. Resolved across programs, ware, components and drugs,
    #: and `validate.py` checks every one of them exists somewhere.
    goods: tuple[str, ...]
    #: Multiplier on list price. Somebody who likes you is not a charity.
    markup: float = 1.0
    #: How they show you what they have.
    pitch: str = ''
    #: Said once, the first time, and it is the whole character.
    first: str = ''
    #: Story rules for the counter being open to you at all. D51: a cabinet
    #: is something a person decides to get out, and people remember.
    requires: tuple[str, ...] = ()
    #: What they say when it stays closed.
    refusal: str = ''


STOCK: tuple[Stock, ...] = (
    Stock(
        'quartermaster',
        goods=('cool_fan', 'mem_wide', 'io_broadwave', 'sump'),
        markup=0.82,
        pitch='The Quartermaster does not have a shop. They have a shelf, and '
              'a book, and an opinion about every single thing on the shelf.',
        first='"Community printed, most of it. Some of it fell off '
              'something, and I will tell you which, because you should know '
              'what you are putting in your head."'),
    Stock(
        'surgeon',
        goods=('grave_salt', 'ratchet', 'wick'),
        markup=0.9,
        pitch='The Blue Surgeon keeps things in a cabinet that has a lock on '
              'it and has never once been observed to be locked.',
        first='"These are for people who work. I do not sell them to people '
              'who do not work, which is not a moral position, it is that '
              'they are wasted on them."'),
    Stock(
        'vance',
        goods=('longwater', 'nightingale', 'ash_tea'),
        markup=1.15,
        pitch='Doctor Vance writes it out properly, on paper, with a heading, '
              'as though any part of this were happening in a hospital.',
        first='"Prescribed, technically. The technically is doing a great '
              'deal of work in that sentence and we will both pretend it is '
              'not."',
        requires=('not:vance_exposed',),
        refusal='Doctor Vance is perfectly pleasant, and the cabinet stays '
                'closed, and she does not refer to the Static piece, and '
                'neither of you needs her to.'),
    Stock(
        'archivist',
        goods=('quietcastle', 'ledgerhand', 'mirrorbox'),
        markup=1.05,
        pitch='The Archivist has one of everything and will not tell you '
              'where any of it came from, on principle, which they will '
              'explain at length.',
        first='"Nothing here is new. Everything here worked at least once, '
              'for somebody, which is more than you can say for what is on '
              'the shelf in Marrow."'),
    Stock(
        'vending',
        goods=('ozymandias',),
        markup=1.0,
        pitch='Ozymandias has one product. Ozymandias has always had one '
              'product. Ozymandias would like to tell you about it.',
        first='"FORMULA NUMBER ONE. ALERTNESS. CLARITY. LONGEVITY. RESISTANCE '
              'TO ELEVEN NAMED CONDITIONS." The machine is very pleased. It '
              'has been very pleased about this for nineteen years.'),
)


#: The effects a favour can have. Declared so that a favour cannot promise
#: something the engine does not do, which is the failure mode this whole
#: file exists to fix.
EFFECTS = ('heat', 'hold', 'intel', 'detox', 'debt', 'ground')


@dataclass(frozen=True, slots=True)
class Favour:
    npc: str
    key: str
    name: str
    #: One line, shown when you ask what they will do.
    blurb: str
    #: One of `EFFECTS`, and how much of it.
    effect: str
    amount: int
    requires: tuple[str, ...] = ()
    #: What it looks like when they do it.
    text: str = ''
    #: What they say when you have asked for too much already.
    refusal: str = ''


FAVOURS: tuple[Favour, ...] = (
    Favour(
        'mara', 'quiet', 'A word in the right place',
        'The Switchboard forget about the worst of your recent work.',
        effect='heat', amount=35,
        requires=('met:mara', 'not:favour_refused'),
        text='She makes two calls, neither of them long, and neither of them '
             'about you as far as anybody listening would be able to tell. '
             'The second one she makes in a language you do not have.\n\n'
             '"That is done. It is not undone, you understand. It is filed '
             'somewhere that nobody has a reason to look at."',
        refusal='"No." She says it without heat and without apology, and then '
                'she says the rest of it, which is: "You are asking me to '
                'spend something you have not put back. I will still take '
                'your calls. I will not make any."'),
    Favour(
        'mara', 'holding', 'She holds the job for you',
        'Your accepted contract stops expiring for a while.',
        effect='hold', amount=8,
        requires=('met:mara', 'not:favour_refused'),
        text='"I will tell them you are being thorough." She writes the word '
             'thorough in the book, and underlines it, and you get the '
             'distinct impression that the underlining is the part that '
             'works.',
        refusal='"I have held two things for you already and got two things '
                'back, one of which was an apology. Go and do something and '
                'then come and ask me."'),
    Favour(
        'lark', 'walked', 'She walks you out of it',
        'A district full of people looking for you forgets your face.',
        effect='heat', amount=45,
        requires=('met:lark', 'not:lark_dead'),
        text='She does not tell you what she does. You are simply in a '
             'different part of the Shambles about forty minutes later, with '
             'a different coat, and the coat is not new and does not fit and '
             'smells faintly of somebody else\'s evening.\n\n'
             '"Do not thank me in the street."',
        refusal='"I like you." She says it the way you would say a diagnosis. '
                '"I have done three things for you and you have done none for '
                'me, and I have been in this city long enough to know what '
                'that is the beginning of."'),
    Favour(
        'remnant', 'clean', 'They take the edge off the drift',
        'Some of your Dissonance, walked back, for nothing.',
        effect='ground', amount=9,
        requires=('met:remnant', 'diss:30'),
        text='Remnant does not do anything you can see. They sit with you for '
             'most of a shift in a room with the lights off, and at some '
             'point you notice that the room has stopped being somewhere you '
             'are waiting and started being somewhere you are.\n\n'
             '"It comes back. I am not fixing you. I am reminding you what '
             'the other thing was like."',
        refusal='"I will not." A pause, and then, more gently: "You are '
                'asking me to hold something for you that you keep putting '
                'back down. That is not a favour, it is a habit with two '
                'people in it."'),
    Favour(
        'remnant', 'read', 'They read the job for you',
        'Full intel on the contract you are carrying.',
        effect='intel', amount=1,
        requires=('met:remnant',),
        text='They ask for the name of the target and then stop talking for '
             'eleven minutes. What comes back is not a briefing. It is the '
             'shape of somebody else\'s network described by somebody who has '
             'stopped experiencing shapes the way you do, and it is correct '
             'in every particular.',
        refusal='"Not this time." Remnant is the only person in this city who '
                'will refuse you without any implication that you have done '
                'something wrong, and it is somehow worse.'),

    # -- D51: favours a decision opened ---------------------------------------
    #
    # None of these exist until the player decided something. They are the
    # mechanical half of a choice whose prose says somebody now owes you, or
    # trusts you, or has let you further in.

    Favour(
        'surgeon', 'clean', 'Eleven hours, no charge',
        'The Blue Surgeon walks some of the drift back. They owe you a friend.',
        effect='ground', amount=8,
        requires=('surgeon_owed',),
        text='They do it in the clean room off the Shambles, talking the '
             'whole time, about nothing, about Lark, about a technique they '
             'read about once and have never had the chance to try. No '
             'money changes hands and they are careful not to make a point '
             'of that.\n\n'
             '"That is one. I do not keep count. I want to be clear that I '
             'do not keep count, and that this is one."',
        refusal='"No." The Blue Surgeon does not look up from what they are '
                'doing to somebody else. "You are not owed a second one, and '
                'I would not be doing you a kindness by pretending you were."'),
    Favour(
        'vance', 'referral', 'A word at the right desk',
        'Aoyama forget about you for a while. She sent you something expensive '
        'once; this is the rest of it.',
        effect='heat', amount=30,
        requires=('vance_owed',),
        text='"I referred you." She says it the way she says everything, as '
             'though reading it from a form. "Not to anybody. Onward. There '
             'is a file on you in this building and it has been moved to a '
             'part of the building that nobody reads from, and that is a '
             'thing I can do once and have now done."',
        refusal='"I did say once." She smiles, and it is a real smile, and '
                'it closes the subject the way a door closes.'),
    Favour(
        'vance', 'immaculate', 'She writes it out properly',
        'A habit, taken back a step, on paper, with a heading.',
        effect='detox', amount=1,
        requires=('vance_employed',),
        text='She does not ask what it is. She looks, and writes, and tears '
             'the sheet off, and the course she has written takes four days '
             'and works, and the paperwork would survive any audit in the '
             'city.\n\n"Staff rate," she says, which is the first time either '
             'of you has used the word.',
        refusal='"Not again so soon. Dependency on the treatment is still '
                'dependency and I do not keep a second set of books for '
                'people I like."'),
    Favour(
        'archivist', 'kept', 'They read the job the way they read the dead',
        'Full intel on the contract you are carrying, from four hundred and '
        'seven logs.',
        effect='intel', amount=1,
        requires=('archive_consented',),
        text='They ask for the target and turn back to the wall. What comes '
             'back is not a briefing: it is nine people who ran this network '
             'and what each of them saw last, stitched into a shape, and the '
             'shape is correct.\n\n'
             '"Four hundred and seven. Not yet, obviously." They do not look '
             'round when they say it.',
        refusal='"Not this one." A pause. "I read a great deal for you. I '
                'would like to keep being able to, which means not now."'),
    Favour(
        'mara', 'long', 'She pays somebody again',
        'Some of what you owe, settled by a woman who has done this before.',
        effect='debt', amount=3000,
        requires=('favour_done',),
        text='She does not ask who holds the paper. She makes one call, '
             'and it is not a long call, and part of what you owe is '
             'simply not owed any more.\n\n'
             '"Nineteen years ago I paid somebody to not do something. It '
             'turns out I am quite good at it."',
        refusal='"No." She caps the pen. "That was for the room in the '
                'Terraces, and the room in the Terraces is settled. The rest '
                'is yours."'),
)


BY_NPC_WORK: dict[str, Work] = {w.npc: w for w in WORK}
BY_NPC_STOCK: dict[str, Stock] = {s.npc: s for s in STOCK}


def favours_for(npc_key: str) -> list[Favour]:
    return [f for f in FAVOURS if f.npc == npc_key]


def favour(npc_key: str, key: str) -> Favour | None:
    return next((f for f in FAVOURS if f.npc == npc_key and f.key == key),
                None)
