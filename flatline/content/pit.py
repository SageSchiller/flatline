"""The pit (D134): a room in the Shambles where people hit each other for
money, and the wall with the names on it.

Built the way the gambling rooms are built (`games.Venue`): a place in a
district, a house that runs it, an arrival line and a pitch that does not
pretend about the odds. What it adds is a ladder of named regulars, each
a rung, each with a style, and at the top the one who has held the wall
for years and holds a blade you can only get by taking it.

The pit's rules are its own. It opens at night. Hands, blades and sticks:
the house holds the gun. Nobody dies in it, whatever rung: you walk out
with the Integrity you have left, and the Nightwatch never hears, and no
faction remembers. One bout a night. A rank that decays if you stop.
"""

from __future__ import annotations

from dataclasses import dataclass

WHERE = 'shambles'
AT = 'fence'
HOUSE = 'carrion'
NAME = 'the pit under the fence'

ARRIVAL = ('Down a ramp behind the fence\'s shutter, into a room that was a '
           'loading bay and is now a floor with tape on it and a wall with '
           'names. Sixty people on their feet around the tape. Nobody sits. '
           'The house has a table, a ledger, and a shotgun on the table, '
           'which is the house\'s way of saying that the shotgun is the '
           'house\'s.')
PITCH = ('The house takes a tenth of every stake and the whole of the '
         'floor. You fight the next name up the wall, or any name above '
         'it, and the further up you reach the better the house pays you '
         'for reaching: even money for the next rung, two to one for the '
         'one after, three to one past that. Win and your name goes above '
         'theirs. Lose and it does not come off. Nobody has died on this '
         'floor. The house is proud of that and would like it to stay '
         'true, and that is the only rule it enforces with the shotgun.')
CLOSED = ('The pit is a floor being mopped and a man counting last night '
          'into a ledger. It opens at night. Everything in the Shambles '
          'does.')
NO_GUNS = ('The house looks at what you are carrying and puts a hand flat '
           'on the shotgun, kindly. Hands, blades and sticks. It will hold '
           'the gun for you, and it will give it back.')
ONE_A_NIGHT = ('You fought tonight. The house does not put anybody on the '
               'floor twice in a night, because the second time is how the '
               'first death happens.')
#: Rungs idle before the rank drops one. The wall remembers; the crowd
#: does not.
RANK_DECAY_SHIFTS = 18
MAX_STAKE = 2500
HOUSE_CUT = 0.1
#: What reaching pays, by rungs above yours.
ODDS = {1: 1, 2: 2, 3: 3}
#: What the house pays for a bout the crowd has already seen (D139). A
#: fighter who has climbed to the rung below somebody they cannot beat
#: used to have exactly one thing to do with their nights, and it was
#: lose. The house will book a rematch. It will not pay full for one.
REMATCH_CUT = 0.5
REMATCH = ('The house books it, and says what it always says about a bout '
           'the crowd has already seen, which is that the crowd has already '
           'seen it, and pays accordingly.')


@dataclass(frozen=True, slots=True)
class Fighter:
    key: str
    name: str
    #: One line, on the card.
    epithet: str
    #: The rung, 1 at the bottom.
    rung: int
    #: The street's tier the bout is fought at.
    tier: int
    chromed: bool
    #: What they fight with, as a word for the card.
    style: str
    #: Extra on their pool and on every hit, over the tier.
    pool_bonus: int
    hit_bonus: int
    #: The purse for beating them, before the night's multiplier.
    purse: int
    #: Before it starts. `{handle}` fills.
    intro: str
    #: After you have won.
    beaten: str


FIGHTERS: tuple[Fighter, ...] = (
    Fighter('bottle', 'Bottle',
            'fights like a man who has been told he is not allowed to any more',
            1, 1, False, 'hands', 3, 0, 250,
            'Bottle looks at you the way he looks at everybody, which is as '
            'a problem the size of a bottle, and rolls his shoulders, and '
            'somebody in the crowd says "go on, Bottle," without much hope.',
            'Bottle sits down on the tape and laughs, which nobody expected, '
            'and says that is the best he has been hit in a year and he '
            'would like to buy you a drink, and he means it.'),
    Fighter('hinge', 'Hinge',
            'a docker with a bat and a grievance that predates you',
            2, 2, False, 'a bat', 4, 0, 500,
            'Hinge is already on the floor, bat on his shoulder, and he does '
            'not look at you at all; he looks at the wall, at the name above '
            'his, and you understand that you are not the point.',
            'Hinge stays down a while, and when he gets up he taps the tape '
            'twice with the bat, which is what he does, and goes to look at '
            'the wall, where your name is now, above his.'),
    Fighter('deacon', 'The Deacon',
            'quiet, chromed, and has read the book on you',
            3, 3, True, 'a blade', 5, 1, 900,
            'The Deacon takes the blade out slowly so that you can see what '
            'it is, which is a courtesy, and says your handle, correctly, '
            'and what you did last month, correctly, and then nothing.',
            'The Deacon bows, exactly, and picks up the blade with the arm '
            'that still works, and says the book on you was out of date, '
            'and that he will correct it.'),
    Fighter('salt', 'Salt',
            'a metre of wire and a smile, and the smile is the warning',
            4, 3, True, 'a monowire', 8, 1, 1600,
            'Salt is smiling before she is on the floor and she does not '
            'stop, and the crowd goes quiet in a way it did not for the '
            'others, and the spool in her palm hums once.',
            'Salt stops smiling, and looks at the wire, and looks at you, '
            'and says that was very good, and means something else by it '
            'that you will find out about later.'),
    Fighter('mother', 'Mother',
            'has held the wall for nine years, and holds the blade',
            5, 4, True, 'the eightfold blade', 10, 2, 3000,
            'Mother comes down the ramp last, and the room makes the space '
            'for her without being asked, and the blade she carries is the '
            'one the wall is about, folded eight times by somebody who is '
            'dead, and she has never once needed all of it.',
            'Mother is on the floor, which the room has never seen, and she '
            'looks up at you and then at the blade, and she says, "It is '
            'yours. It was always going to be somebody\'s." The room does '
            'not make a sound, and then it makes all of them.'),
)

BY_KEY: dict[str, Fighter] = {f.key: f for f in FIGHTERS}
BY_RUNG: dict[int, Fighter] = {f.rung: f for f in FIGHTERS}
TOP = max(f.rung for f in FIGHTERS)
#: What the champion holds, and hands over.
RELIC = 'eightfold'
