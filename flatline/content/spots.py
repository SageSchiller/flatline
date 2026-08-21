"""Places to stand in, inside a district. D53.

A district is a list of services and a paragraph, and a paragraph is not a
place. These are the places: two or three per district, each somewhere a
person would actually go and stand, with who is usually there and what it
is like at night. `look` lists them, `visit` goes and stands in one, and it
costs nothing, because it is inside the district you are already in.

They are texture, and texture is the point. Nothing here is a menu: the
verbs are the same verbs, the people are the same people (`who` is where you
would expect to find them, not a cage), and a place that appears in a scene
is a place you can go and stand in afterwards, which is most of what makes
a city feel like it goes on when you are not looking.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Spot:
    key: str
    #: With the article, lowercase: `the noodle bar`. The way a person says it.
    name: str
    district: str
    #: Second person, present tense, two to four sentences.
    blurb: str
    #: The same place after dark, or '' if it is the same place after dark.
    night: str = ''
    #: NPC keys you would usually find here. Presence is still decided by the
    #: world layer; this says where in the district to look.
    who: tuple[str, ...] = ()


SPOTS: tuple[Spot, ...] = (
    # -- The Ninth Ward -------------------------------------------------------
    Spot('pumphouse', 'the pump house', 'ninth',
         'Four machines and one man, and the man has a chair, and the chair is '
         'bolted to a concrete step that sits above the highest of the tape '
         'marks on the wall by about the width of a hand. He does not look up. '
         'The pumps do not stop. That is the arrangement.',
         night='At night it is the same four machines and a different man, '
               'and the tape marks are harder to see, and the water is not.'),
    Spot('stalls', 'the stalls', 'ninth',
         'Cloth on crates on the bonnets of vans that have not moved since you '
         'got here. Everything in the Ninth that is for sale is here, and most '
         'of it works, and the people selling it know exactly which of it does '
         'not and will tell you for the price of being asked politely.',
         who=('tuck',)),
    Spot('alcove', 'the alcove', 'ninth',
         'A recess between two stairwells with a vending machine in it that '
         'has a name, a small pile of coins at its base, and a scroll of flat '
         'capitals it would like you to read. Somebody has put a stool in '
         'front of it. Somebody else has put a second stool.{{The stools face '
         'the machine.}}',
         who=('vending',)),

    # -- Marrow ---------------------------------------------------------------
    Spot('noodle_bar', 'the noodle bar', 'marrow',
         'No name over the door, three landlines behind the counter, and a '
         'woman in her sixties writing in a book. The noodles are good. Nobody '
         'comes here for the noodles and everybody eats them, because sitting '
         'at the Switchboard\'s counter without ordering is a thing you do '
         'once.',
         night='At night the landlines are quiet and the book is open and '
               'the noodles are still good, and the only other customer has '
               'been looking at the same point above the counter for some '
               'time.',
         who=('mara',)),
    Spot('exchange', 'the exchange', 'marrow',
         'The Marrow interchange: a hall of terminals under a ceiling somebody '
         'designed, the up-escalator at one end with its name and its '
         'hand-lettered sign, and a queue with a constitution. This is where '
         'runners who do not have a safehouse run from, and where the ones who '
         'do come to be seen not needing to.',
         night='At night the exchange is the people who do not sleep, one to '
               'a terminal, not looking at each other, and the escalator, '
               'not moving, with its following gone home.'),
    Spot('steps', 'the Switchboard steps', 'marrow',
         'Three concrete steps outside the noodle bar, where people waiting to '
         'see Mara wait, and where a woman with a document wallet has been '
         'waiting for what is evidently years. The steps are neutral ground '
         'inside neutral ground. Nothing has ever started on them.',
         who=('bell',)),

    # -- The Vertical ---------------------------------------------------------
    Spot('lobby', 'the lobby', 'vertical',
         'Ninety floors of Kagawa stand on a lobby that logs your gait, and '
         'the lobby knows you are not staff before you do. The chairs are for '
         'people with appointments. There is a desk with a person behind it '
         'who is very good at their job, which is saying no with their whole '
         'body.',
         night='At night the lobby goes to its night setting, which is '
               'brighter, and the desk is staffed by somebody reading a '
               'screen angled so the camera can read it too.',
         who=('auditor',)),
    Spot('walkways', 'the walkways', 'vertical',
         'Glass bridges between the towers at the twelfth floor, full of '
         'people allowed to be on them, moving at the building\'s pace. From '
         'here the Terraces are a texture and the Ninth is a colour. Nobody on '
         'the walkways has been to either.'),
    Spot('reviews', 'the review suite', 'vertical',
         'A floor of small rooms with good chairs where Kagawa review things: '
         'buyout figures, personnel files, the cost of keeping you against the '
         'cost of replacing you. The carpet is excellent. Everybody who comes '
         'out of a review says the arithmetic was correct.'),

    # -- Aoyama Green ---------------------------------------------------------
    Spot('reception', 'the clinic reception', 'green',
         'Warm, well lit, the chairs good, the magazines current. Doctor '
         'Vance\'s receptionist keeps a list and is not cross about anybody on '
         'it. Behind the desk a door opens on a schedule so regular you could '
         'set a trace by it.',
         who=('vance',)),
    Spot('lawns', 'the lawns', 'green',
         'Grass, real, cut to a length somebody signs off. People on breaks '
         'sit on it in the exact postures of people who have been told the '
         'lawn is for sitting on. There is a sign asking you not to walk on '
         'the lawn, on the lawn, and the path to the sign is a path.',
         night='At night the lawns are lit like a showroom after closing: '
               'everything visible and nothing for sale.'),
    Spot('aftercare', 'the aftercare ward', 'green',
         'The ward at the back of the campus where the clinics keep the '
         'people they have finished with, for a day or two. The aftercare is '
         'genuinely excellent. That is how the rest of it stays quiet: nobody '
         'leaves here able to say that anything went badly, because nothing '
         'did, afterwards.'),

    # -- The Glasshouse -------------------------------------------------------
    Spot('floor', 'the demonstration floor', 'glasshouse',
         'Sendai\'s shop that is not a shop: interfaces on cloth under lights '
         'that do not know what time it is, and demonstrators reading from '
         'cards to a crowd that is mostly other demonstrators. Your deck '
         'reports that something here has tried to talk to it, politely, '
         'twice.',
         night='At night the demonstrations sit under cloths and the lights '
               'stay on, and it is the quietest expensive place in the city.'),
    Spot('dark_room', 'the dark room', 'glasshouse',
         'A room with the lights off, by arrangement, where somebody sits who '
         'died for ninety seconds on a Sendai table and has not entirely '
         'agreed to be back. People come here to sit. Nothing is said for '
         'long stretches, and the stretches are the point.',
         who=('remnant',)),
    Spot('bench', 'the cold bench', 'glasshouse',
         'The Glasshouse workshop: a steel bench, a loupe on an arm, and a '
         'technician who will fix your deck and talk to it while she does, '
         'and not to you. The bench is kept cold on purpose. Things behave on '
         'a cold bench.'),

    # -- Freeport -------------------------------------------------------------
    Spot('gate', 'the west gate', 'freeport',
         'A noticeboard with actual paper on it, a table, a box, and an '
         'argument about wording. Everything Freeport decides is decided here, '
         'by the end of the shift, by the people who will have to live with '
         'it, and then it is written on the paper and read aloud to people who '
         'could have read it themselves.',
         who=('quartermaster',)),
    Spot('cranes', 'the cranes', 'freeport',
         'They have names. The newest was named by a vote, the vote was close, '
         'and the losing name is painted on the other side. An old man watches '
         'them from the same bollard most days and will tell you, if you sit, '
         'what happened to the people who used to run them.',
         night='At night the cranes keep their lights on and the water does '
               'what water does under them, and the old man has gone, and '
               'the bollard is still warm if you get there soon enough.',
         who=('pike_sr',)),
    Spot('mess', 'the dockers\' mess', 'freeport',
         'A long room over the water with a bar at one end and a bench record '
         'on the wall with a dead man\'s name still on it, by vote. The losing '
         'side of whatever got decided at the gate today is buying. That is '
         'the rule, and it is the only rule in here anybody enforces.',
         who=('broker',)),

    # -- The Precinct ---------------------------------------------------------
    Spot('counter', 'the complaints counter', 'precinct',
         'A public counter for filing complaints, a queue for it that has not '
         'moved since you arrived, and a sergeant behind it who has nineteen '
         'years and a drawer. The forms are very well designed.{{There is a '
         'form for requesting one.}}',
         who=('desk',)),
    Spot('surplus', 'the surplus counter', 'precinct',
         'Nightwatch sell what was evidence last quarter from a counter that '
         'nobody upstairs has audited in years. The prices are good. The '
         'provenance is on a sticker, and the sticker says [dim]surplus[/], '
         'and that is the whole of the provenance.'),
    Spot('cells', 'the cells', 'precinct',
         'At the back of the Precinct, behind a door that is open because '
         'nobody would try it, a row of cells with people in them being '
         'extremely reasonable at each other through the bars. Nightwatch run '
         'the cells as a line item.{{It is one of the profitable ones.}}'),

    # -- The Shambles ---------------------------------------------------------
    Spot('clinic', 'the clinic', 'shambles',
         'The room behind the Shambles clinic is clean in a way the street is '
         'not, and the Blue Surgeon works in it with the door open and does '
         'not use anaesthetic and talks the whole time. The queue outside has '
         'been there since four. It will be there at four tomorrow.',
         who=('surgeon',)),
    Spot('crate', 'the crate', 'shambles',
         'A crate outside the clinic where somebody your age sits, or sat, '
         'with six pieces of chrome and two of them load-bearing. People leave '
         'things on it. It is the nearest thing the Shambles has to a bench, '
         'and the only one anybody remembers who sat there.',
         who=('lark',)),
    Spot('cabinets', 'the cabinets', 'shambles',
         'Every shop on Carrion\'s street has a cabinet at the front with the '
         'things that came out of somebody recently, serial numbers showing, '
         'because those are the ones people check. The Blue Surgeon can tell '
         'you whose was whose. They will tell you anyway.',
         night='At night the cabinets are lit from inside and the street is '
               'not, and the chrome in them is the brightest thing on Carrion\'s '
               'ground, which is either a display or a warning and is probably '
               'both.'),

    # -- The Terraces ---------------------------------------------------------
    Spot('stairwells', 'the stairwells', 'terraces',
         'Four stairwells and eleven thousand people, twice a day, with the '
         'courtesy of people who will do it again tomorrow. The walls are wet '
         'concrete and the landings smell of growing things. Somebody has '
         'marked the floor numbers by hand where the signs gave up.',
         night='At night the stairwells are the sound of eleven thousand '
               'people being tired behind thin walls, and one child on a '
               'landing doing homework by vending-machine light.',
         who=('preacher',)),
    Spot('allotment', 'the allotment', 'terraces',
         'A landing somebody has turned into a garden, in trays, under a light '
         'borrowed from a corridor, with a man who will tell you what each '
         'thing is and what it is for and who it is for, which is nobody, '
         'which is the point.',
         who=('gardener',)),
    Spot('lifts', 'the lifts', 'terraces',
         'The service lift has preferences and the passenger lift has a '
         'committee, and the committee has no lift, the lift having been '
         'optimised, and it meets anyway, fortnightly, on the ninth landing, '
         'with minutes.{{The minutes are read aloud to the stairwell, which '
         'attends.}}'),
)

BY_KEY: dict[str, Spot] = {s.key: s for s in SPOTS}
SPOT_KEYS: tuple[str, ...] = tuple(BY_KEY)


def in_district(district: str) -> list[Spot]:
    return [s for s in SPOTS if s.district == district]


def find(district: str, query: str) -> Spot | None:
    """A place here, by key, by name, or by enough of the name to be sure."""
    q = (query or '').strip().lower()
    if not q:
        return None
    here = in_district(district)
    for s in here:
        name = s.name.lower()
        if q == s.key or q == name or q == name.removeprefix('the '):
            return s
    hits = [s for s in here if q in s.name.lower() or q in s.key]
    return hits[0] if len(hits) == 1 else None


def scene_for(spot: Spot, phase: str) -> str:
    """What it is like there now."""
    if phase == 'night' and spot.night:
        return spot.night
    return spot.blurb
