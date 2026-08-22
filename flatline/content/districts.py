"""The city. Where you are changes what you can buy and who will meet you.

Districts are deliberately few and strongly characterised. Nine places a player
can hold in their head, each with one clear reason to go there and one clear
reason not to, beats twenty interchangeable ones.

Every faction that holds ground has somewhere, which matters more than it
sounds: a Nightwatch precinct and a Carrion street are places the player can
choose to walk into, and choosing to walk into them is a different act from
reading about them on a reputation screen.

**The Terraces exist for tone rather than mechanics.** It is the one district
where nobody is in this business, and its whole job is to be the place the rest
of the city is happening to. A game about a city that does not care whether you
live needs somewhere that shows you what it is not caring about.

Travel costs a shift, which is the whole economy of the city layer: everything
you do is priced in time, and the contract board does not wait.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: What a location lets you do. The `travel` and `market` commands read these.
SERVICES = ('market', 'clinic', 'fixer', 'safehouse', 'workshop', 'fence')


@dataclass(frozen=True, slots=True)
class District:
    key: str
    name: str
    controller: str            # faction key
    blurb: str
    #: Second-person scene-setting, printed on arrival. Two sentences.
    arrival: str
    services: tuple[str, ...]
    #: 0..100. High security means Nightwatch presence and worse outcomes if
    #: you are carrying heat when you arrive.
    security: int
    #: Multiplies market prices here.
    price_mult: float
    #: Stock quality: the highest item tier this district's market carries.
    max_tier: int
    #: Districts reachable in one shift. Symmetric, checked by `validate.py`.
    neighbours: tuple[str, ...] = ()
    #: Factions with a presence beyond the controller. Affects who notices you.
    presence: tuple[str, ...] = ()


DISTRICTS: tuple[District, ...] = (
    District(
        'ninth', 'The Ninth Ward', 'sixes',
        'Low, wet, and cheap. Everything is for sale and most of it works.',
        'The Ninth smells like standing water and fryer oil. Somebody two '
        'floors up is testing a generator, and nobody in the street has looked '
        'at you yet, which in the Ninth is a decision rather than an accident.',
        services=('market', 'fence', 'workshop', 'safehouse'),
        security=25, price_mult=0.85, max_tier=1,
        neighbours=('marrow', 'freeport', 'terraces', 'shambles', 'stacks'),
        presence=('carrion', 'fixers'),
    ),
    District(
        'marrow', 'Marrow', 'fixers',
        'Neutral ground by long agreement. Everybody works here and nobody '
        'starts anything here.',
        'Marrow at shift change is a single continuous conversation held by '
        'four thousand people who all know better than to raise their voices. '
        'The Switchboard runs out of a noodle bar with no name and three '
        'landlines.',
        services=('market', 'fixer', 'safehouse', 'fence'),
        security=40, price_mult=1.0, max_tier=2,
        neighbours=('ninth', 'vertical', 'glasshouse', 'freeport', 'precinct'),
        presence=('sixes', 'freeport', 'nightwatch'),
    ),
    District(
        'vertical', 'The Vertical', 'kagawa',
        'Kagawa\'s spine. Ninety floors of logistics, and a lobby that logs '
        'your gait.',
        'The Vertical is climate-controlled to a degree that reads as an '
        'accusation. Every surface is clean, every door is on a schedule, and '
        'the building has already decided how long you are allowed to stand '
        'still.',
        services=('market', 'clinic'),
        security=80, price_mult=1.35, max_tier=3,
        neighbours=('marrow', 'green', 'terraces', 'precinct'),
        presence=('nightwatch',),
    ),
    District(
        'green', 'Aoyama Green', 'aoyama',
        'Campus, clinics, and the best chrome in the city at the worst prices.',
        'Aoyama Green is landscaped within an inch of its life and staffed by '
        'people who all look like they slept well. The clinics here will put '
        'anything in you that you can pay for, and their aftercare is genuinely '
        'excellent, which is how they keep the rest of it quiet.',
        services=('clinic', 'market'),
        security=70, price_mult=1.25, max_tier=3,
        neighbours=('vertical', 'glasshouse'),
        presence=('nightwatch',),
    ),
    District(
        'glasshouse', 'The Glasshouse', 'sendai',
        'Sendai\'s district. Decks, interfaces, and everything between a '
        'nervous system and a network.',
        'The Glasshouse is lit like an operating theatre and about as warm. '
        'Sendai does not have shops here so much as demonstrations, and the '
        'staff talk to your deck rather than to you.',
        services=('market', 'workshop', 'clinic'),
        security=65, price_mult=1.15, max_tier=3,
        neighbours=('marrow', 'green', 'freeport', 'row', 'hall',),
        presence=('nightwatch', 'freeport'),
    ),
    District(
        'freeport', 'Freeport', 'freeport',
        'The docks, run by the people who work them. Open hardware, grey '
        'market, no questions and no cover either.',
        'Freeport does not have a skyline, it has cranes. There is a noticeboard '
        'by the west gate with actual paper on it, and everything sold past it '
        'is either community-printed or fell off something.',
        services=('market', 'workshop', 'fence', 'safehouse', 'fixer'),
        security=30, price_mult=0.92, max_tier=2,
        neighbours=('ninth', 'marrow', 'glasshouse', 'shambles', 'row',),
        presence=('carrion', 'fixers', 'sixes'),
    ),

    District(
        'precinct', 'The Precinct', 'nightwatch',
        'Contracted enforcement, run as a business, with a surplus counter '
        'nobody upstairs has audited in years.',
        'The Precinct is open-plan and lit at a level somebody costed. There '
        'is a public counter for filing complaints and a queue for it that '
        'has not moved since you arrived. Everybody here is on shift and '
        'nobody here is in a hurry.',
        services=('market', 'fence'),
        security=85, price_mult=0.9, max_tier=2,
        neighbours=('marrow', 'vertical'),
        presence=('kagawa',),
    ),
    District(
        'shambles', 'The Shambles', 'carrion',
        'Carrion territory. Cheap chrome, cheaper surgery, and nobody asks '
        'where anything came from because everybody already knows.',
        'The Shambles smells of solvent and something underneath the solvent. '
        'There are people on this street with more hardware than skin and '
        'they watch you the way a butcher watches a queue. Nothing here is '
        'expensive, and there is a reason for that.',
        services=('clinic', 'fence', 'workshop'),
        security=15, price_mult=0.7, max_tier=2,
        neighbours=('ninth', 'freeport'),
        presence=('sixes',),
    ),
    District(
        'terraces', 'The Terraces', 'kagawa',
        'Where the people who are not in this business live. Kagawa housing '
        'stacked over Kagawa farms, and about a third of the city in it.',
        'The Terraces at shift change is eleven thousand people coming home '
        'through a stairwell that smells of wet concrete and growing things. '
        'Somebody is arguing about a parking allocation. A child on the '
        'landing above is doing homework by the light of a vending machine. '
        'None of these people have ever heard of you and that is the nicest '
        'thing about the place.',
        services=('market', 'safehouse'),
        security=35, price_mult=0.95, max_tier=1,
        neighbours=('vertical', 'ninth', 'stacks',),
        presence=('nightwatch', 'sixes'),
    ),
    District(
        'stacks', 'The Stacks', 'static',
        'Presses, relay shacks, and the water towers they hide under. '
        'Everything here is printed twice and believed once.',
        'The Stacks are wet underfoot and loud overhead: the Terraces\' water '
        'towers drip on a quarter-mile of tin roofs and under the roofs the '
        'presses run all night. Somebody has painted a masthead on a '
        'shutter and somebody else has painted over the date.',
        services=('market', 'fence'),
        security=20, price_mult=0.8, max_tier=1,
        neighbours=('terraces', 'ninth'),
        presence=('sixes', 'chorus'),
    ),
    District(
        'row', 'Meridian Row', 'meridian',
        'The banks. Stone, glass, and a silence you could set a watch by. '
        'Nothing here is for sale except the keys, and the keys are not.',
        'Meridian Row is the cleanest street in the city and the only one '
        'where nobody is selling anything. The doors are tall, the cameras '
        'are discreet to the point of courtesy, and a man in a good coat has '
        'already decided you are not a customer.',
        services=('fixer', 'market'),
        security=85, price_mult=1.4, max_tier=3,
        neighbours=('glasshouse', 'freeport', 'hall'),
        presence=('nightwatch', 'kagawa'),
    ),
    District(
        'hall', 'The Hall', 'chorus',
        'A transit hall the Chorus took over when the trains stopped. Soup, '
        'singing, and a clinic that does not ask.',
        'The Hall is the old interchange with the tracks pulled up and the '
        'departure boards still lit, every one of them showing a hymn. It '
        'smells of soup and floor polish. Somebody is singing, not well, and '
        'nobody minds.',
        services=('clinic', 'fence'),
        security=35, price_mult=0.9, max_tier=1,
        neighbours=('glasshouse', 'row'),
        presence=('sixes', 'carrion'),
    ),

)

BY_KEY: dict[str, District] = {d.key: d for d in DISTRICTS}
DISTRICT_KEYS: tuple[str, ...] = tuple(BY_KEY)


# --------------------------------------------------------------------------
# what each district is doing, by shift (D53)
# --------------------------------------------------------------------------

#: district -> phase -> two or three sentences. `look` and arrival print
#: these in place of the city-wide shift scene, because Marrow at night and
#: the Shambles at night are not the same night, and the one paragraph a
#: district used to have was the same paragraph every time you stood in it.
#: Second person where a person is there to be second; the city otherwise.
SCENES: dict[str, dict[str, str]] = {
    'ninth': {
        'morning':
            'The pumps have been going all night and the water in the '
            'stairwells has gone down a hand\'s width, which is what the '
            'Ninth calls morning. Shutters go up on the stalls that have '
            'shutters. The rest were never shut.',
        'afternoon':
            'Everything in the Ninth that is for sale is out on the street '
            'now, on cloth, on crates, on the bonnets of vans that do not '
            'move. The Sixes\' people are not visible, which is how you know '
            'they are here.',
        'night':
            'The Ninth does not go dark so much as go orange: sodium lamps '
            'over standing water, and the generator two floors up still being '
            'tested. Somebody is frying something. Somebody is always frying '
            'something.{{It is the one reliable public service.}}',
    },
    'marrow': {
        'morning':
            'Marrow opens the way a throat clears. The noodle bar\'s '
            'landlines have been ringing since before the shutters, and the '
            'queue at the exchange is the people who did not sleep standing '
            'behind the people who did.',
        'afternoon':
            'Every walkway in Marrow is at capacity and every conversation is '
            'being held at the volume of somebody who assumes the next table '
            'is listening, which it is. Nobody starts anything. That is what '
            'the district is for.',
        'night':
            'Marrow at night is four thousand people pretending to be four '
            'hundred. The noodle bar is open, because it is always open, and '
            'the landlines are quiet, and Mara is writing in the book.',
    },
    'vertical': {
        'morning':
            'The Vertical takes its first shift in through the lobby at a rate '
            'the lobby has decided on. The gait logger does not need to look '
            'up. Ninety floors of lights come on in an order somebody in '
            'facilities is proud of.',
        'afternoon':
            'The Vertical does not have an afternoon so much as a sustained '
            'peak, climate-controlled, with the walkways between the towers '
            'full of people who are allowed to be on them. You are not, yet, '
            'one of those people, and the building has noticed.',
        'night':
            'Floors forty through sixty are still lit. Down here the lobby '
            'has gone to its night setting, which is brighter, and the guard '
            'at the desk is reading something on a screen angled so that the '
            'camera can read it too.',
    },
    'green': {
        'morning':
            'Aoyama Green wakes up already landscaped. Sprinklers, the hum of '
            'the clinics\' plant, and the first of the day\'s patients '
            'arriving in good coats to have something done that their '
            'families have been told is routine.',
        'afternoon':
            'The campus lawns are being used as lawns, by people on breaks, '
            'and the clinic doors open and close on a schedule so regular you '
            'could set a trace by it. Everybody looks well. That is a '
            'product.',
        'night':
            'At night the Green is lit the way a showroom is lit when the '
            'showroom is closed: everything visible and nothing for sale. The '
            'clinics keep a skeleton staff and very good locks, and the '
            'aftercare ward glows at the back of the campus like a pilot '
            'light.',
    },
    'glasshouse': {
        'morning':
            'The Glasshouse is already bright when you arrive, because it is '
            'always bright; the lighting does not know what time it is and '
            'would not care. Sendai\'s demonstrators are setting out the '
            'day\'s interfaces on cloth, like a market, if a market talked to '
            'your deck.',
        'afternoon':
            'Sendai are demonstrating something to a crowd that is mostly '
            'other demonstrators. Every surface reflects every other surface. '
            'Your deck reports that three different things have tried to talk '
            'to it since you walked in, politely.',
        'night':
            'At night the Glasshouse is an operating theatre after the '
            'operation. The lights stay on and the staff go home and the '
            'demonstrations sit under cloths, and it is the quietest '
            'expensive place in the city.',
    },
    'freeport': {
        'morning':
            'Freeport starts before it is light because the tide does not '
            'care. The cranes are moving, the west gate has a new sheet of '
            'paper on it, and somebody is reading it aloud to somebody who '
            'could read it themselves, which is how news works here.',
        'afternoon':
            'The docks are at full stretch: containers, shouting, the market '
            'doing business out of the backs of things, and the noticeboard by '
            'the west gate with a small argument going on in front of it about '
            'the wording of something that will be voted on by dark.',
        'night':
            'Freeport at night is the cranes with their lights on and the '
            'water doing what water does under them. The bars are open. The '
            'fences are open. The vote got settled, and the losing side is '
            'buying, which is the rule.',
    },
    'precinct': {
        'morning':
            'The Precinct changes shift without anybody\'s heart rate moving. '
            'The complaints counter opens. The queue at it is already there, '
            'because it was there last night; it is not clear anybody in it '
            'went home.',
        'afternoon':
            'The Precinct is busy in the way a business is busy: forms, '
            'stamps, a surplus counter doing a brisk trade in things that were '
            'evidence last quarter. Everybody is on shift and nobody is in a '
            'hurry and the queue has moved one place.',
        'night':
            'At night the Precinct is lit at the level somebody costed, and '
            'the counter is staffed by somebody who would rather not be, and '
            'the cells at the back are full of people being extremely '
            'reasonable at each other through the bars.{{Nightwatch run the '
            'cells as a line item. It is an unusually profitable one.}}',
    },
    'shambles': {
        'morning':
            'The Shambles clinic has had a queue since four. The Blue '
            'Surgeon\'s light has been on since three. The street smells of '
            'solvent and, under the solvent, the thing the solvent is for.',
        'afternoon':
            'Carrion\'s street is doing its day\'s business, which is chrome '
            'going in, chrome coming out, and a cabinet at the front of every '
            'shop with the things that came out recently, serial numbers '
            'showing. Nobody asks. Everybody already knows.',
        'night':
            'The Shambles at night is the one district that gets louder. The '
            'clinics work late because the work comes in late, and the people '
            'on the street with more hardware than skin are the ones on shift, '
            'and they watch you the way a butcher watches a queue.',
    },
    'terraces': {
        'morning':
            'Eleven thousand people leave the Terraces in the morning through '
            'four stairwells, quietly, with the practised courtesy of people '
            'who will do this again tomorrow. Something is growing on every '
            'landing. Nobody here knows your name.',
        'afternoon':
            'The Terraces in the afternoon belong to the people who do not '
            'leave: the old, the very young, a man on the ninth landing who '
            'has opinions about parking. Kagawa\'s farms hum under the floor. '
            'It is the nearest thing to peace this city sells, and it is '
            'rented.',
        'night':
            'The stairwells fill again at night, slower, and then empty, and '
            'the Terraces settle into the sound of eleven thousand people '
            'being tired behind thin walls. A child is doing homework by '
            'vending-machine light. The homework is about Kagawa.',
    },
    'stacks': {
        'morning':
            'The presses stop for an hour at dawn, which is when the Stacks '
            'find out what they printed. Bundles go out on handcarts under '
            'the dripping towers, and the first edition of the day is already '
            'wrong about something, and somebody is already setting the '
            'correction, and the correction will be wrong too, on purpose.',
        'afternoon':
            'The afternoon is for the relays. Kids go up the water towers '
            'with coils of cable and come down with opinions, and every '
            'shack has a dish pointed at something it should not be able to '
            'see. Static\'s people do not look like anything. That is the '
            'whole craft.',
        'night':
            'At night the Stacks are a sound: the presses, the drip, and a '
            'voice on a relay reading out a list of names in no order anybody '
            'can find. Half the district is listening. The other half is '
            'being read.',
    },
    'row': {
        'morning':
            'Meridian Row opens at an hour that has been agreed rather than '
            'announced. The doors go from shut to open without anybody '
            'appearing to touch them, and the first people through are '
            'already inside by the time you notice the doors are open.',
        'afternoon':
            'Nothing happens on the Row in the afternoon, visibly, and a great '
            'deal happens. Couriers come and go with cases that are not heavy '
            'enough. A man in a good coat stands where he stood this '
            'morning. The cameras do not move, because they do not need to.',
        'night':
            'At night the Row is lit from inside, every window, and empty, '
            'every street, and the silence has the quality of a held note. '
            'Nobody is selling anything. Nobody ever was. The keys are in '
            'there, and the keys are the only thing.',
    },
    'hall': {
        'morning':
            'Soup at the Hall starts at first light and the queue is already '
            'the length of the old platform. Nobody takes names. The '
            'departure boards show a hymn, then a different hymn, then the '
            'time, which is wrong, and which nobody has fixed in six years '
            'on the grounds that it is the only clock in the building and '
            'you can set anything by a clock that is reliably wrong.',
        'afternoon':
            'Afternoons the Hall is a clinic. Two rooms off the concourse, '
            'one Cantor, one kettle, a queue that does not ask what the '
            'person in front is in for. Carrion\'s people come and stand at '
            'the back sometimes, not in the queue, and the singing does not '
            'stop for them, which is a statement.',
        'night':
            'At night the Hall sings. Not a performance: there is nobody to '
            'perform for. Forty people on the old platform doing the thing '
            'they do, and the sound goes up into the roof where the pigeons '
            'are, and comes back down changed, and the boards say a hymn, '
            'and the wrong clock says the wrong time.',
    },
}


# --------------------------------------------------------------------------
# who is in the street (D58)
# --------------------------------------------------------------------------

#: district -> fragments. `street_line` picks three by the shift, so the
#: street is different each time you look and the same each time you look
#: at the same shift, without drawing from any game stream: texture must not
#: move the world (D35).
STREET: dict[str, tuple[str, ...]] = {
    'ninth': (
        'two of the Sixes on the corner, not doing anything, which is the point '
        'of them',
        'a queue for the pump-house tap with a cup left on the pipe',
        'somebody selling batteries out of a pram',
        'a child on a junction box eating something fried',
        'the generator two floors up being tested again',
        'a van that has not moved in a year with a shop in the back of it',
        'water coming up the stairwell at the usual rate',
        'a man carrying a door, for reasons, with great care',
    ),
    'marrow': (
        'four thousand people keeping their voices down',
        'the queue outside the exchange, under constitution',
        'somebody on the Switchboard steps who has been there since yesterday',
        'a fixer you do not know pretending not to know you back',
        'a courier going the long way round the noodle bar out of respect',
        'a handset held the way you hold a handset when describing somebody',
        'the up escalator not moving, with its following',
        'two people agreeing about a price at the volume of people who know the next table is listening',
    ),
    'vertical': (
        'a lobby that has already decided about you',
        'people on the walkways who are allowed to be on the walkways',
        'a courier with a lanyard being walked somewhere by a second lanyard',
        'contractors on the kerb by the loading dock, legally not picketing',
        'an auditor apologising to nobody in particular',
        'a gait being logged',
        'a cleaner with clearance you do not have',
        'somebody coming out of a review saying the arithmetic was correct',
    ),
    'green': (
        'sprinklers',
        'people on breaks sitting on the lawn in the posture the lawn is for',
        'a patient in a good coat being told something is routine',
        'the clinic door opening on its schedule',
        'a path to the sign about the path',
        'somebody well, leaving, saying so',
        'a receptionist with a list, not cross',
        'the aftercare ward glowing at the back like a pilot light',
    ),
    'glasshouse': (
        'a demonstrator reading from a card',
        'a crowd of other demonstrators',
        'something trying to talk to your deck, politely',
        'surfaces reflecting surfaces',
        'a technician on a cold bench talking to somebody else\'s deck',
        'Sendai security not looking at you in a way that is logged',
        'the one dark room, with its door shut by arrangement',
        'a crate arriving with a behaviour policy printed on the side',
    ),
    'freeport': (
        'the cranes, moving, with names',
        'an argument about wording at the west gate',
        'somebody reading the noticeboard aloud to somebody who can read',
        'dockers settling something by the end of the shift',
        'an old man on a bollard watching the cranes',
        'the print shop queue, which cannot read the plans',
        'the tide doing what the tide does',
        'the losing side buying',
    ),
    'precinct': (
        'a queue that has not moved',
        'a form being requested, using the other form',
        'a sergeant reading the same page',
        'the surplus counter doing brisk business in last quarter',
        'somebody against a wall for a check that has stopped being one',
        'a clerk pulling a closed file at random',
        'the cloth, behind the counter, not being mentioned',
        'Nightwatch hitting a target and visibly stopping',
    ),
    'shambles': (
        'the clinic queue, since four',
        'cabinets with serial numbers showing',
        'somebody with more hardware than skin watching you the way a butcher watches a queue',
        'solvent, and under it the thing the solvent is for',
        'the Blue Surgeon\'s light on, since three',
        'a crate outside the clinic with something left on it',
        'bins being emptied by people nobody asks about',
        'chrome going in, chrome coming out',
    ),
    'terraces': (
        'eleven thousand people on four stairwells',
        'something growing on every landing',
        'a man on the ninth landing with opinions about parking',
        'a child doing homework by vending-machine light',
        'a rota by the water point with forty names on it',
        'the farms humming under the floor',
        'a lift with preferences',
        'somebody saying good evening without checking who you are',
    ),
    'stacks': (
        'a handcart of bundles under a dripping tower, nobody pushing it yet',
        'a kid halfway up a water tower with a coil of cable over one shoulder',
        'a shutter with a masthead on it and the date painted over',
        'a relay voice reading names in no order, and three people listening',
        'a press running behind a wall, felt more than heard',
        'two of the Sixes buying a paper they cannot read, for the pictures',
        'a dish on a shack roof pointed at the Vertical, which is rude',
    ),
    'row': (
        'a man in a good coat, standing where he stood this morning',
        'a courier with a case that is not heavy enough',
        'a door that has gone from shut to open without anybody touching it',
        'a camera that does not move because it does not need to',
        'a Nightwatch pair walking slowly, which on the Row is a courtesy',
        'nobody selling anything, at all, anywhere',
        'a window lit from inside with nobody behind it',
    ),
    'hall': (
        'the soup queue, the length of the old platform, nobody taking names',
        'a departure board showing a hymn, then the wrong time',
        'somebody singing, not well, and nobody minding',
        'two of Carrion\'s at the back of the clinic queue, not in it',
        'a kettle on the concourse that has never been off',
        'a pigeon coming down out of the roof changed by the singing',
        'a child asleep on a bench under a blanket that says SENDAI',
    ),
}


def street_line(district: str, shift: int) -> str:
    """Three things in the street right now, picked by the shift.

    Deterministic and stream-free on purpose: looking twice in one shift
    shows the same street, and looking never moves the world.
    """
    pool = STREET.get(district, ())
    if len(pool) < 3:
        return ''
    n = len(pool)
    picks = [pool[(shift * 3 + i * 5 + shift // n) % n] for i in range(3)]
    # Three distinct ones, stepping on if the arithmetic doubled up.
    seen: list[str] = []
    for i, item in enumerate(picks):
        k = 0
        while item in seen:
            k += 1
            item = pool[(shift * 3 + i * 5 + k) % n]
        seen.append(item)
    return f'In the street: {seen[0]}, {seen[1]}, and {seen[2]}.'


def scene(district: str, phase: str) -> str:
    """What this district is doing at this hour, or '' if nobody wrote it."""
    return SCENES.get(district, {}).get(phase, '')

#: The city as a plain graph. Derived rather than authored, so it cannot drift
#: from the districts themselves, and shaped for `ui.spanning_tree` and
#: `ui.shortest_path` which are the two things that ever ask.
GRAPH: dict[str, list[str]] = {d.key: list(d.neighbours) for d in DISTRICTS}

#: Where a new character wakes up. Marrow because it is neutral, has a fixer,
#: and touches more of the city than anywhere else.
START = 'marrow'


def with_service(service: str) -> list[District]:
    return [d for d in DISTRICTS if service in d.services]


# --------------------------------------------------------------------------
# how a district is doing
# --------------------------------------------------------------------------

#: The game's pitch is that the city remembers. It has always been true in the
#: numbers: posture climbs when you rob somebody, heat accrues, bounties get
#: posted. None of it was ever visible standing in the street, which meant the
#: player had to read a reputation screen to find out that the world had
#: changed around them.
#:
#: These are that state, in the street, where it happened. Keyed to how far
#: the controlling faction's posture has moved from its own baseline, which is
#: the number that actually tracks "have you been hitting these people".
#: Below this much *under* baseline, somebody has stopped paying for security
#: here. Handled separately from the table below rather than as its lowest
#: band, because `_band` picks the highest threshold at or under the value and
#: a negative entry in an otherwise-positive table silently swallows the
#: entire neutral zone: at exactly baseline posture the district would report
#: itself as falling apart.
RELAXED_AT = -6.0
RELAXED = ('Something has gone out of this place since you were last here. '
           'Half the checkpoints are unstaffed and nobody has replaced the '
           'camera on the corner. Whoever was paying for all that has '
           'stopped.')

HARDENING: tuple[tuple[float, str], ...] = (
    (10.0,
     'There are more people in the doorways than there were, and they are '
     'wearing the same jacket as each other. Nobody is doing anything. That '
     'is the point of them.'),
    (20.0,
     'The district has tightened. Two of the through-routes you used to take '
     'are gated now, there is a scanner arch at the transit entrance that '
     'nobody is queueing for because everybody has learned the other way '
     'round, and the whole place has the atmosphere of somewhere that has '
     'recently had a meeting about you.'),
    (32.0,
     'This is not the district you started working in. There is a permanent '
     'presence on the walkways now, in numbers that cost real money, and the '
     'people who live here have adjusted their routes and their hours and '
     'their conversation. Nobody here knows it was you. That does not make it '
     'not you.'),
)

#: What being wanted here feels like from the pavement. Keyed to your own
#: attention score with whoever is watching this ground.
WANTED: tuple[tuple[float, str], ...] = (
    (20.0, ''),
    (35.0,
     'You get looked at twice on the way in. Once by somebody who was not '
     'sure, and once by the same person making sure.'),
    (55.0,
     'Somebody makes a call while you are still in the street, holding the '
     'handset the way you hold a handset when the person you are describing '
     'can see you.'),
    (75.0,
     'Two separate people have decided not to be near you, which they '
     'accomplish without once looking in your direction, and which is the '
     'single most professional thing you will see today.'),
)


def _band(table: tuple[tuple[float, str], ...], value: float) -> str:
    line = ''
    for threshold, text in table:
        if value >= threshold:
            line = text
    return line


def mood(district: District, posture: float, attention: float) -> list[str]:
    """How this district is right now, in one or two lines.

    Returns a list because the two halves are independent: a district can be
    hardened and not care about you, or unchanged and full of people who have
    your name. Both at once is a bad afternoon and reads as one.
    """
    out = []
    drift = posture - factions_posture(district.controller)
    if drift <= RELAXED_AT:
        out.append(RELAXED)
    else:
        hardening = _band(HARDENING, drift)
        if hardening:
            out.append(hardening)
    wanted = _band(WANTED, attention)
    if wanted:
        out.append(wanted)
    return out


def factions_posture(key: str) -> float:
    """The controlling faction's baseline, imported late to avoid a cycle."""
    from . import factions
    fac = factions.BY_KEY.get(key)
    return float(fac.posture) if fac else 0.0
