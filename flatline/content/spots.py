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
    #: Things to be found here (D63 e): one of a kind, at the right hour,
    #: after the right thing. See `Find`.
    finds: tuple = ()


@dataclass(frozen=True, slots=True)
class Find:
    """Something one of a kind, where it is, and what has to be true.

    D63 e. A relic is found rather than bought: at a place (`visit`), at an
    hour, once the story rules hold, once per character ever. The rumour is
    an ambient event, localised to the district, that stops the moment the
    thing is found; it is the breadcrumb, and it is the only one.
    """

    #: Catalogue key: a program, chrome, component or drug with `unique=True`.
    item: str
    #: Story rules, `Story.satisfied` syntax, all of which must hold.
    requires: tuple[str, ...] = ()
    #: Phases it can be found in. Empty means any hour.
    hours: tuple[str, ...] = ()
    #: Second person, present tense: the moment you find it.
    text: str = ''
    #: What the district says about it, before you do. An ambient event.
    rumour: str = ''
    #: The rumour's tone, for the budget.
    tone: str = 'wry'


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
         who=('tuck',),
         finds=(Find('cool_cloth', requires=('sparrow_taught',),
                     text='Sparrow finds you between two vans and hands you a '
                          'cloth, folded, damp, with the air of somebody passing '
                          'on a trade secret. "For the case. It works." It does, '
                          'a bit. She waits until you have put it in the bag.',
                     rumour='Sparrow is said to have solved thermal load with a '
                            'wet cloth, and to have been right about how often '
                            'that works, which is most of the time, which is '
                            'the problem.',
                     tone='absurd'),)),
    Spot('alcove', 'the alcove', 'ninth',
         'A recess between two stairwells with a vending machine in it that '
         'has a name, a small pile of coins at its base, and a scroll of flat '
         'capitals it would like you to read. Somebody has put a stool in '
         'front of it. Somebody else has put a second stool.{{The stools face '
         'the machine.}}',
         who=('vending',),
         finds=(Find('formula_zero', requires=('met:vending', 'runs:4'),
                     hours=('night',),
                     text='The machine hums, and something drops into the tray '
                          'that is not on the front of the machine, and you '
                          'have not paid. The display says RESTOCKED. It did not '
                          'say that a moment ago.',
                     rumour='The vending machine in the Ninth is said to have '
                            'dispensed something it does not list, once, at '
                            'night, to somebody who had not paid, and to have '
                            'been restocked since.',
                     tone='absurd'),)),

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
               'not moving, with its following gone home.',
         who=('keeper',)),
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
         'did, afterwards.',
         who=('orderly',)),

    # -- The Glasshouse -------------------------------------------------------
    Spot('floor', 'the demonstration floor', 'glasshouse',
         'Sendai\'s shop that is not a shop: interfaces on cloth under lights '
         'that do not know what time it is, and demonstrators reading from '
         'cards to a crowd that is mostly other demonstrators. Your deck '
         'reports that something here has tried to talk to it, politely, '
         'twice.',
         night='At night the demonstrations sit under cloths and the lights '
               'stay on, and it is the quietest expensive place in the city.',
         who=('demonstrator',)),
    Spot('dark_room', 'the dark room', 'glasshouse',
         'A room with the lights off, by arrangement, where somebody sits who '
         'died for ninety seconds on a Sendai table and has not entirely '
         'agreed to be back. People come here to sit. Nothing is said for '
         'long stretches, and the stretches are the point.',
         who=('remnant',),
         finds=(Find('remnant_graft', requires=('dw_name', 'diss:30'),
                     hours=('night',),
                     text='The room is empty and you are far enough gone to '
                          'think of opening the drawer. It is not locked. There '
                          'is one piece in it, the one that came out last, and '
                          'it is warm, which it should not be.',
                     rumour='Somebody says Remnant kept one piece back, the '
                            'one that came out last, and that it is in the dark '
                            'room in a drawer that is not locked because nobody '
                            'who goes in there opens drawers.',
                     tone='grim'),)),
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
         who=('pike_sr', 'crane'),
         finds=(Find('pike', requires=('met:pike_sr', 'runs:8'),
                     hours=('morning',),
                     text='Old Pike does not look away from the cranes. He '
                          'holds out a chip between two fingers until you take '
                          'it, and says that he wrote it the year they named '
                          'the thing after him, and never ran it, and that '
                          'eight runs is enough to be going on with.',
                     rumour='Old Pike, at the cranes, is said to have written '
                            'something once and never run it, and to hand it '
                            'to people he has watched for long enough. The '
                            'people who say so have not been handed it.',
                     tone='wry'),)),
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
         who=('surgeon',),
         finds=(Find('surgeons_own', requires=('lark_saved', 'surgeon_owed'),
                     text='The Blue Surgeon puts a vial on the counter between '
                          'you without looking up from the ledger. No label. '
                          '"For the next time." At this clinic it is not a '
                          'pleasantry.',
                     rumour='The Blue Surgeon is said to give something to '
                            'people who have paid for somebody else\'s life, in '
                            'a vial, without a label, for the next time.',
                     tone='grim'),)),
    Spot('crate', 'the crate', 'shambles',
         'A crate outside the clinic where somebody your age sits, or sat, '
         'with six pieces of chrome and two of them load-bearing. People leave '
         'things on it. It is the nearest thing the Shambles has to a bench, '
         'and the only one anybody remembers who sat there.',
         who=('lark',),
         finds=(Find('lark_piece', requires=('lark_dead',),
                     text='Somebody has been through the crate. They took the '
                          'charger and the tin. They missed the thing taped '
                          'inside the lid, because it was not worth money, and '
                          'it comes away in your hand still warm from the sun '
                          'on the lid.',
                     rumour='Somebody went through Lark\'s crate afterwards, '
                            'looking for things worth money. Somebody else says '
                            'they missed something, and will not say what, and '
                            'has not gone back for it.',
                     tone='grim'),)),
    Spot('cabinets', 'the cabinets', 'shambles',
         'Every shop on Carrion\'s street has a cabinet at the front with the '
         'things that came out of somebody recently, serial numbers showing, '
         'because those are the ones people check. The Blue Surgeon can tell '
         'you whose was whose. They will tell you anyway.',
         night='At night the cabinets are lit from inside and the street is '
               'not, and the chrome in them is the brightest thing on Carrion\'s '
               'ground, which is either a display or a warning and is probably '
               'both.',
         who=('fence',)),

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
    # -- D58: more ground -------------------------------------------------------
    Spot('tap', 'the tap', 'ninth',
         'A standpipe off the pump house with a queue for it that has the '
         'courtesy of people who have queued here before and will again. The '
         'water is clean. Nobody asks how, because the answer is the four '
         'machines and the man in the chair, and everybody knows.',
         night='At night the queue is shorter and quieter and the tap runs '
               'the same, and somebody has left a cup on the pipe for the '
               'next person, which is the constitution here.'),
    Spot('generator', 'the generator', 'ninth',
         'Two floors up, on a landing, a man is testing a generator for a '
         'landlord who is not paying for the diesel, and has been testing it '
         'since before you got here. It runs. He tests it anyway. Below him '
         'the stairwell has a line of tape on it from last month.',
         finds=(Find('survey', requires=('met:tuck', 'runs:2'),
                     text='Behind the fuel drum, in a plastic sleeve, on '
                          'something that is not paper: a map of every cable in '
                          'the Ninth, in Tuck\'s hand, with the pumps circled. '
                          'It is not hidden. It is where Tuck put it.',
                     rumour='Tuck is said to keep a map of every cable in the '
                            'Ninth on something that is not paper, and to have '
                            'lost it, in the sense of having put it somewhere.',
                     tone='wry'),)),
    Spot('transit', 'the transit gate', 'marrow',
         'The gate to the interchange, with a handle scratched into the paint '
         'by it, and a date, and under that a word that has been scratched '
         'out again by somebody else. People touch the handle going through. '
         'Nobody will tell you whose it was and two of them know.',
         finds=(Find('thessaly', requires=('runs:6',), hours=('night',),
                     text='Under the rail, where the handle is scratched into '
                          'the paint, somebody has taped a drive. It has been '
                          'there long enough for the tape to go brown. Nobody '
                          'has taken it because nobody who stands here at '
                          'night reads the paint, and you did.',
                     rumour='There is a handle scratched into the paint by '
                            'the transit gate, and a date under it, and '
                            'somebody says there is something taped under the '
                            'rail that nobody has taken, and then changes the '
                            'subject.',
                     tone='grim'),)),
    Spot('back_bar', 'the back bar', 'marrow',
         'The bar behind the noodle bar, reached through the kitchen, where '
         'the runners who have a safehouse drink with the ones who do not and '
         'nobody mentions which is which. There is a chair in the corner that '
         'nobody sits in. Nobody has said why.',
         night='At night the back bar is the only lit room in Marrow that is '
               'not the noodle bar, and the chair in the corner is still '
               'empty, and a new face has just been moved out of it, gently.'),
    Spot('dock', 'the loading dock', 'vertical',
         'The one part of the Vertical that is not climate-controlled: a '
         'dock where things arrive and are logged and go up, and where the '
         'contractors who are owed four weeks of pay sit on the kerb, which '
         'is legally different from picketing and much harder to move.'),
    Spot('canteen', 'the canteen', 'vertical',
         'Floor eleven, staff only, and the lobby has already told the '
         'canteen you are not staff. The food is good and subsidised and '
         'eaten quickly by people who can see the clock. Somebody at a '
         'corner table has been moved to face the wall.'),
    Spot('edge', 'the campus edge', 'green',
         'Where the landscaping stops. There is a line, a real line, where '
         'the grass somebody signs off becomes the grass nobody does, and '
         'people from the Glasshouse side stand on their side of it to '
         'smoke, and people from the Green side do not smoke.'),
    Spot('dispensary', 'the dispensary', 'green',
         'A counter with a queue and a window and somebody behind it who '
         'writes everything out properly, on paper, with a heading. The '
         'prescriptions are technically prescriptions. The technically is '
         'doing a great deal of work.',
         finds=(Find('aftercare_bead', requires=('met:orderly', 'rep:aoyama:10'),
                     hours=('afternoon',),
                     text='The orderly looks at you for a while and then takes '
                          'a bead off a tray that is not for you and puts it '
                          'in your hand and closes your hand on it. "Under the '
                          'skin. Wrist. It reports, but it also works."',
                     rumour='The Green dispensary is said to keep a tray of '
                            'beads for patients who have stopped coming. They '
                            'go in under the skin of the wrist. Nobody has asked '
                            'what they are for.',
                     tone='wry'),)),
    Spot('interface_bar', 'the interface bar', 'glasshouse',
         'A bar where the chairs talk to your deck and the drinks are priced '
         'by what your deck says back. Runners with good masking drink cheap '
         'here. Runners with bad masking are bought drinks, by people who '
         'wanted to know what they were running.',
         night='At night the interface bar is the loudest room in the '
               'Glasshouse, in a frequency nobody can hear, and your deck '
               'reports that four things have asked it the time.'),
    Spot('bay', 'the loading bay', 'glasshouse',
         'Sendai\'s bay, where the demonstration units arrive in crates with '
         'the behaviour policy printed on the side, and leave in the same '
         'crates, reset, and the technician who signs them out has started '
         'reading the policy, which is not in her job.'),
    Spot('wall', 'the tide wall', 'freeport',
         'A wall along the water with the tide marks painted on it by hand, '
         'one a year, by a vote, and the highest mark is from the year '
         'before Freeport went independent, and somebody has painted a '
         'small crown on it, and the crown is also by vote.'),
    Spot('print', 'the print shop', 'freeport',
         'Community printed. Three machines in a container doing deck '
         'components, cheap, out of plans that are on the noticeboard for '
         'anybody to read, and a queue of people who could not read the '
         'plans and want the parts anyway, which is most people.'),
    Spot('lost', 'the lost property office', 'precinct',
         'Four thousand items behind a counter and one under a cloth. Every '
         'officer on the shift knows what you mean when you ask about the '
         'cloth and every one of them changes the subject with the same '
         'sentence, which is very well designed.'),
    Spot('waiting', 'the waiting room', 'precinct',
         'A room for waiting in, lit at the level somebody costed, with '
         'chairs bolted down and a screen showing the queue number, which '
         'has not changed, and a poster about the importance of reporting '
         'faults promptly, covering the fault log.'),
    Spot('yard', 'the solvent yard', 'shambles',
         'Behind the clinics, a yard where the solvent is kept in drums and '
         'the thing the solvent is for is kept in bins, and the bins are '
         'emptied at night by people who do not work for the clinics and are '
         'not asked who they work for.'),
    Spot('night_counter', 'the night counter', 'shambles',
         'A counter that opens when the clinics close, for the work that '
         'comes in late, with a woman behind it who can tell from the way you '
         'stand what you have come about and will tell you the price before '
         'you say it.',
         night='At night the night counter is the brightest thing on '
               'Carrion\'s street, and the queue at it is the people on '
               'shift, and they watch you the way a butcher watches a queue.'),
    Spot('roof', 'the roof', 'terraces',
         'Above the top landing, where the air is. Kagawa\'s farms hum under '
         'every floor and the roof is the one place the hum stops, and '
         'people come up here to stand in the stopping, and say nothing to '
         'each other, and go back down.'),
    Spot('water_point', 'the water point', 'terraces',
         'A tap on the fourth landing with a rota beside it, handwritten, '
         'with eleven thousand people on it in principle and forty in '
         'practice, and the forty keep the rota, and the rota is the nearest '
         'thing the Terraces has to a government.'),
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


#: Every find, in catalogue order of the places (D63 e).
FINDS: tuple[Find, ...] = tuple(f for sp in SPOTS for f in sp.finds)
FIND_BY_ITEM: dict[str, Find] = {f.item: f for f in FINDS}


def spot_of(find: Find) -> Spot:
    return next(sp for sp in SPOTS if find in sp.finds)


def available(spot: Spot, phase: str, satisfied, flags) -> list[Find]:
    """What can be found here now: the hour is right, the rules hold, and it
    has not been found. `satisfied(rule)` is the story's rule check bound to
    the game."""
    out = []
    for find in spot.finds:
        if f'found:{find.item}' in flags:
            continue
        if find.hours and phase not in find.hours:
            continue
        if all(satisfied(rule) for rule in find.requires):
            out.append(find)
    return out
