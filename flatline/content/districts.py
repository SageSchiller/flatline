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
    #: D67, the city as a place. How big it is, in the terms the place
    #: itself would use: floors, people, streets, cranes.
    scale: str = ''
    #: What it is made of, and what that does to standing in it.
    built: str = ''
    #: What people here do for money, and who takes a cut of it.
    works: str = ''
    #: Named parts of it. A district is not one street, and naming six
    #: corners of it that you will never visit is most of what makes a
    #: place feel like it goes on past the bit you are standing in.
    quarters: tuple[str, ...] = ()
    #: What is past its edge. The city does not stop at the map.
    beyond: str = ''


DISTRICTS: tuple[District, ...] = (
    District(
        'ninth', 'The Ninth Ward', 'sixes',
        'Low, wet, and cheap. Everything is for sale and most of it works.',
        'The Ninth smells like standing water and fryer oil. Somebody two '
        'floors up is testing a generator, and nobody in the street has looked '
        'at you yet, which in the Ninth is a decision rather than an accident.',
        services=('market', 'fence', 'workshop', 'safehouse'),
        security=25, price_mult=0.85, max_tier=1,
        scale=(
            'Nine blocks that were eleven before the water, and something '
            'like forty thousand people in them, most of whom have never '
            'been above the fourth floor of anything.'
        ),
        built=(
            'Concrete poured in a hurry sixty years ago, walkways bolted on '
            'ever since, and a tide mark at chest height on everything that '
            'has not been replaced. Nothing in the Ninth was designed. All '
            'of it was added, by somebody who needed it that week.'
        ),
        works=(
            'Salvage. The Ninth takes apart what the rest of the city '
            'throws out and sells it back in pieces, and the pieces are '
            'good, because the people doing it have nothing else to be good '
            'at. Under that the Sixes take their cut of everything, and '
            'under that the pumps run on parts nobody is ever invoiced for.'
        ),
        quarters=('the Tideline', 'Pump Row', 'the Stalls', 'Lower Nine', 'the Drowned Arcade', 'Kettle Street'),
        beyond=(
            'Past the Tideline the water won. Those blocks are still '
            'standing and still empty and nobody has ever counted them, and '
            'the Sixes say people live out there, and say it in the voice '
            'you use for something you would rather was a story.'
        ),
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
        scale=(
            'Four thousand people live in a quarter mile of covered street, '
            'and three times that pass through it on any given shift.'
        ),
        built=(
            'A market that grew a roof, and then floors, and then more '
            'roof. Six decks of it now, strung with cable and hung with '
            'sheeting, and nobody alive can tell you which parts are load '
            'bearing.'
        ),
        works=(
            'Marrow makes nothing. It arranges things: work, credit, '
            'silence, an introduction, and a cup of something at four in '
            'the morning for whoever has just finished doing one of them. '
            'Everybody here is somebody\'s second phone call.'
        ),
        quarters=('the Long Counter', 'Under Six', 'the Exchange', 'Landline Row', 'the Back Bar', 'the Transit Gate'),
        beyond=(
            'Every road out of Marrow goes somewhere that wants something. '
            'That is the entire geography of the place and everybody '
            'standing in it knows which road is theirs.'
        ),
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
        scale=(
            'Ninety floors, eleven thousand on shift at any hour, and a '
            'lobby that has logged every one of them walking in.'
        ),
        built=(
            'One building, and then a city arranged around it afterwards. '
            'Glass and steel and a service core you could drive a lorry '
            'down, all of it cleaned nightly by people who are bussed in at '
            'eleven and bussed out at four and never once appear on a floor '
            'plan.'
        ),
        works=(
            'Logistics. A third of the city\'s calories move through the '
            'Vertical\'s schedules, and every person in the building is a '
            'line on a spreadsheet about it, including the ones who write '
            'the spreadsheets.'
        ),
        quarters=('the Lobby', 'Forty Through Sixty', 'the Service Core', 'the Loading Deck', 'Reception Seven', 'the Roof Farm'),
        beyond=(
            'Above sixty the lifts need a reason and below the lobby there '
            'are four levels of plant that are on no public plan, and the '
            'people who work down there are Kagawa staff with Kagawa badges '
            'who have never been upstairs.'
        ),
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
        scale=(
            'A campus of nine buildings, four thousand staff, and a lawn '
            'that costs more a year to keep than the Ninth spends on its '
            'pumps.'
        ),
        built=(
            'Low, curved, and pale, with real wood in the reception areas '
            'and a filtration plant under the lawn that runs louder than '
            'anything in the Ninth. Every corridor is the same width. That '
            'is on purpose, and after an hour you can feel it.'
        ),
        works=(
            'Chrome, and the research that produces it, and the aftercare '
            'that keeps the research from being a scandal. Aoyama will put '
            'anything in you that you can pay for, and their aftercare is '
            'genuinely excellent, which is how the rest of it stays quiet.'
        ),
        quarters=('Reception', 'the Lawns', 'Aftercare', 'the Dispensary', 'Building Four', 'the Long Wing'),
        beyond=(
            'Building Nine has no reception and no signage and a car park '
            'that is full at three in the morning, and the staff in the '
            'other eight call it the Long Wing and change the subject.'
        ),
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
        scale=(
            'Two hundred metres of frontage, forty of glass, and behind it '
            'eleven floors of showroom, workshop and interface bar that '
            'never entirely closes.'
        ),
        built=(
            'Sendai built it to be looked at: a wall of glass with the '
            'interface floor behind it, lit so that from Marrow at night it '
            'reads as one enormous screen with people moving about inside. '
            'The back of the building is breeze block, like everywhere '
            'else.'
        ),
        works=(
            'Interfaces, and the people who wear them. The Glasshouse sells '
            'the fastest connection in the city and a room to use it in, '
            'and buys, quietly, the recordings of what everybody does in '
            'those rooms.'
        ),
        quarters=('the Floor', 'the Dark Room', 'the Bench', 'Interface Bar', 'the Bay', 'the Back Stair'),
        beyond=(
            'The dark room is on no plan of the building and the people who '
            'use it came out of somewhere that does not appear on plans '
            'either, and Sendai leave the lights off in there as a courtesy '
            'they have never explained.'
        ),
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
        scale=(
            'A mile and a half of working dock, six thousand people on the '
            'rota, and eleven cranes, of which nine move.'
        ),
        built=(
            'Steel, salt, and forty years of repairs made by whoever was on '
            'shift. Nothing here is branded. Everything here has been fixed '
            'at least twice, by people who wrote down how, on a board, by '
            'the gate, in pen.'
        ),
        works=(
            'Cargo, and what comes off cargo. Freeport unloads the city\'s '
            'imports and keeps a percentage in kind, and everybody agrees '
            'not to call that what it is because the alternative is Kagawa '
            'running the docks.'
        ),
        quarters=('the West Gate', 'the Crane Line', 'the Mess', 'Print Row', 'the Wall', 'Cold Store Three'),
        beyond=(
            'Past the last crane the quay keeps going for another half mile '
            'into water nobody dredges, and there are boats tied up out '
            'there that have not moved in years and are not empty.'
        ),
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
        scale=(
            'Four streets, one building that matters, and eleven hundred '
            'officers on the roster, of whom about four hundred are real.'
        ),
        built=(
            'Municipal concrete with the windows too small, a yard behind '
            'it with a wire fence, and a public counter designed by '
            'somebody who had thought hard about queues and not at all '
            'about people. The cells are older than the building and were '
            'moved into it.'
        ),
        works=(
            'Response. Nightwatch do not prevent anything: they arrive, '
            'they file, and they keep. The Precinct is mostly a warehouse '
            'for things taken off people, sorted by date, with a retention '
            'schedule that is public and that nobody has ever asked to see.'
        ),
        quarters=('the Counter', 'the Yard', 'Lost Property', 'the Cells', 'Surplus', 'the Waiting Room'),
        beyond=(
            'The yard backs onto a lot where the vans that have stopped '
            'working are parked in rows, and the rows are longer every '
            'year, and the fence around them was put up facing inward.'
        ),
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
        scale=(
            'Six streets that used to be a hospital campus, and nobody '
            'counts the people, because the people are the trade.'
        ),
        built=(
            'A ward block with the wards taken out, a chapel with the pews '
            'taken out, and a car park that has had four storeys of housing '
            'grown into it. Every surface that can carry a handwritten sign '
            'is carrying one, and about a third of them are directions to a '
            'clinic.'
        ),
        works=(
            'Bodies. Carrion buy what comes out of people and sell it to '
            'whoever will have it, and the Blue Surgeon will put it back '
            'into somebody else for a price that is always, precisely, what '
            'you have. There is more clinical skill on this street than in '
            'the Green and none of the paperwork.'
        ),
        quarters=('the Clinic', 'the Cabinets', 'the Yard', 'Chapel Row', 'the Night Counter', 'Ward Nine'),
        beyond=(
            'Ward Nine is boarded at both ends and the boards have been '
            'rehung so many times that the current ones are new, and '
            'Carrion keep it that way, and will tell you cheerfully that '
            'they do not know why.'
        ),
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
        scale=(
            'Eighteen stairwells up the hill, nine thousand flats, and two '
            'lifts, neither of which has worked in a year.'
        ),
        built=(
            'Kagawa housing from the good decade: brick and balcony, built '
            'to last and maintained until the maintenance contract was '
            'deferred. The water towers at the top feed the whole hill by '
            'gravity, and the whole hill knows exactly which step is '
            'missing on which stair.'
        ),
        works=(
            'The Terraces work everywhere else. Nine thousand flats of '
            'people who go down the hill at six and come back up it at '
            'eight, and carry their own water for the last four floors of '
            'it, and know every neighbour by the sound of their door.'
        ),
        quarters=('the Stairwells', 'the Allotment', 'the Water Point', 'the Lifts', 'Upper Terrace', 'the Roof'),
        beyond=(
            'Above the top terrace the hill keeps going into the old '
            'reservoir works, fenced, with a path worn through the fence, '
            'and the view from up there takes in the whole city and is the '
            'only free thing in it.'
        ),
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
        scale=(
            'A quarter mile of tin roofs under the Terraces\' water towers, '
            'eleven presses, and nobody will say how many relays.'
        ),
        built=(
            'Sheds. Sheds against sheds, roofed in corrugate that the '
            'towers drip on all year, with cable strung overhead in bundles '
            'thick as an arm and a gantry between the two big roofs that is '
            'the only dry place to talk.'
        ),
        works=(
            'Printing, and broadcasting, and the difference between them, '
            'which the Stacks will explain to you at length. Static run the '
            'presses and the relays and the list of names, and everybody '
            'here is either setting type, climbing a tower, or reading the '
            'floor.'
        ),
        quarters=('the Press Room', 'the Towers', 'the Relay Shacks', 'the Ink Store', 'the Gantry', 'Correction Row'),
        beyond=(
            'The last three shacks on Correction Row have no dish, no press '
            'and no lock, and what is in them is boxes of every edition '
            'ever printed here, in order, and the Stacks will let anybody '
            'in and watch them the whole time.'
        ),
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
        scale=(
            'One street, eight hundred metres, four institutions, and a '
            'silence that is maintained at considerable expense.'
        ),
        built=(
            'Stone, because stone reads as permanent, over a steel frame, '
            'because stone is not. Doors tall enough to be a statement, '
            'windows lit from inside all night, and eleven steps down to a '
            'vault door that is not a door, it is an argument about doors.'
        ),
        works=(
            'Keys. Meridian hold things: money, contracts, identities, and '
            'the cryptographic material that makes all three mean anything. '
            'Nothing on the Row is for sale. Things on the Row are held, '
            'and the holding is the business.'
        ),
        quarters=('the Counter Hall', 'the Colonnade', 'the Vault Steps', 'the Atrium', 'the Paper Archive', 'the Back Office'),
        beyond=(
            'The Row runs out at a set of gates that are always open onto a '
            'street of ordinary offices that all, if you check the '
            'registry, belong to the same four companies, and the check '
            'takes eleven days and costs money.'
        ),
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
        scale=(
            'One concourse, six platforms, no trains, and between two and '
            'four hundred people in it depending on the weather.'
        ),
        built=(
            'A transit interchange from when the city had a plan, with the '
            'tracks pulled up and the departure boards still lit. Iron '
            'roof, tile floor, pigeons in the beams, and a clock that has '
            'been four minutes wrong for six years.'
        ),
        works=(
            'Soup, and a clinic that does not ask, and the singing. The '
            'Chorus took the building when the trains stopped and have '
            'never once explained what they want, and forty people a night '
            'stand on the old platform and sing, and the queue for the soup '
            'does not stop for it.'
        ),
        quarters=('the Concourse', 'the Old Platform', 'the Kitchens', 'the Side Chapel', 'the Bell Loft', 'Platform Six'),
        beyond=(
            'Platform six is behind a hoarding and the hoarding has a door '
            'in it that the Chorus keep locked, and what is behind it is '
            'the tunnel mouth, bricked, with something written on the brick '
            'that is not in any language the Hall will name.'
        ),
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
        'a man on the Tideline steps counting something in a notebook, '
        'out loud',
        'four kids running a length of cable between two blocks at '
        'second-floor height',
        'a woman selling fried things from a pram with a car battery '
        'under it',
        'somebody\'s whole flat on a walkway while the water goes down '
        'inside it',
        'a Sixes lad who is fifteen and doing the standing-about very '
        'seriously',
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
        'a queue at the exchange that has not moved and does not mind',
        'two people doing a deal in the middle of the walkway while the '
        'crowd goes round them like water',
        'somebody carrying a deck case wrapped in a coat, badly',
        'a landline ringing somewhere on Landline Row and nobody '
        'hurrying',
        'a fixer\'s runner going through with a paper bag and no eye '
        'contact',
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
        'a bus of night cleaners unloading at the service core, all of '
        'them holding the same lanyard',
        'a man on the loading deck reading a docket he has clearly read '
        'already',
        'two floors of the tower going dark at once, on a schedule',
        'somebody being walked out through reception by two people '
        'being kind about it',
        'the lobby floor being polished by a machine with a person '
        'walking behind it',
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
        'a groundsman mowing a lawn that did not need it',
        'two people in Aoyama blue eating lunch and not talking',
        'a delivery of something refrigerated going in the back of '
        'Building Four',
        'somebody sitting on the aftercare steps holding a wrist and '
        'looking at nothing',
        'a car in the Building Nine car park with the engine running '
        'and nobody in it',
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
        'the wall of glass showing the interface floor and forty people '
        'in it not moving',
        'a demonstrator running the same three minutes for a crowd of '
        'six',
        'somebody coming out of the dark room into the light and '
        'stopping',
        'a Sendai courier at the bay with a case that is chained to '
        'them',
        'two runners on the bench comparing decks and lying about the '
        'prices',
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
        'the rota being argued about at the west gate, publicly, with '
        'numbers',
        'a crane going over with something under it that nobody will '
        'name',
        'somebody chalking a repair onto the board by the gate',
        'the mess doing a shift change: forty people out, forty in, no '
        'words',
        'a print run of the week\'s prices going up on the wall while '
        'people read it over the printer\'s shoulder',
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
        'a queue at the public counter that has learned to stand very '
        'still',
        'a van backing into the yard with the back doors already open',
        'somebody at Lost Property describing a coat, in detail, to a '
        'sergeant writing none of it down',
        'two officers walking the four streets slowly, which here is '
        'the whole of the job',
        'a lot behind the fence with eleven vans in it that have '
        'stopped working',
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
        'a handwritten sign directing you to a clinic that is two signs '
        'further on',
        'somebody outside the cabinets holding a cool bag and not going '
        'in yet',
        'two of Carrion\'s carrying something between them wrapped in '
        'sheeting',
        'a queue at the night counter of people who are all looking at '
        'the ground',
        'a chapel doorway with three mattresses in it and nobody on '
        'them',
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
        'a chain of people passing cans up a stairwell without being '
        'asked',
        'somebody on the fourth landing sitting down halfway, on '
        'purpose',
        'the allotment being watered from a can somebody carried up '
        'eight floors',
        'two lifts with the doors open and a notice on both that has '
        'faded',
        'a woman at the water point who knows what everybody on the '
        'hill is called',
    ),
    'stacks': (
        'a handcart of bundles under a dripping tower, nobody pushing it yet',
        'a kid halfway up a water tower with a coil of cable over one shoulder',
        'a shutter with a masthead on it and the date painted over',
        'a relay voice reading names in no order, and three people listening',
        'a press running behind a wall, felt more than heard',
        'two of the Sixes buying a paper they cannot read, for the pictures',
        'a dish on a shack roof pointed at the Vertical, which is rude',
        'the presses going behind a wall, felt in the feet before it is '
        'heard',
        'a bundle of the morning edition going past on a handcart, '
        'still warm',
        'somebody up a tower with a spanner and no harness',
        'a knot of people under the gantry, in the dry, arguing about a '
        'headline',
        'ink on the puddles making colours that are not in anything '
        'else here',
    ),
    'row': (
        'a man in a good coat, standing where he stood this morning',
        'a courier with a case that is not heavy enough',
        'a door that has gone from shut to open without anybody touching it',
        'a camera that does not move because it does not need to',
        'a Nightwatch pair walking slowly, which on the Row is a courtesy',
        'nobody selling anything, at all, anywhere',
        'a window lit from inside with nobody behind it',
        'a clerk crossing the street with a folder held flat against '
        'the rain',
        'the colonnade with a coat at every sixtieth pace, all of them '
        'not looking at you',
        'a car pulling up and nobody getting out of it for a long '
        'moment',
        'the only litter on the street being picked up by somebody paid '
        'to',
    ),
    'hall': (
        'the soup queue, the length of the old platform, nobody taking names',
        'a departure board showing a hymn, then the wrong time',
        'somebody singing, not well, and nobody minding',
        'two of Carrion\'s at the back of the clinic queue, not in it',
        'a kettle on the concourse that has never been off',
        'a pigeon coming down out of the roof changed by the singing',
        'a child asleep on a bench under a blanket that says SENDAI',
        'somebody sleeping under the departure boards in the warm light',
        'a pigeon coming down out of the roof and everybody ducking '
        'except the Chorus',
        'two of Carrion\'s at the back, not in the queue, being looked '
        'at',
        'a child running the length of platform six\'s hoarding, hand '
        'on it, all the way',
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


#: What is between two districts (D67). Travel prints one of these on the
#: way, keyed on the pair, so that crossing the city is a thing that
#: happens rather than a shift that passes. Unordered: the walk reads the
#: same in both directions, because the walk is the same walk.
CROSSINGS: dict[frozenset, tuple[str, ...]] = {
    frozenset(('ninth', 'marrow')): (
        'Up out of the wet on the old freight ramp, past the tide marks '
        'getting lower and then stopping, into a street with a roof on it.',
        'The walkway from Kettle Street runs above the water for a quarter '
        'mile and then joins Marrow at the third deck, and you go from '
        'seeing the sky to not.',),
    frozenset(('ninth', 'freeport')): (
        'Along the dock road with the water on your left the whole way and '
        'the cranes getting bigger ahead until they are the only thing.',
        'Past the boat yards, where four men are taking something apart that '
        'was a hull, in the rain, without hurrying.',),
    frozenset(('ninth', 'terraces')): (
        'Up the hill. The lift shaft at the bottom has been out for a year '
        'and the stair beside it is nine flights, and everybody on it is '
        'carrying something.',),
    frozenset(('ninth', 'shambles')): (
        'Through the arches where the old hospital laundry was, which smells '
        'of the old hospital laundry, and out into signage.',),
    frozenset(('ninth', 'stacks')): (
        'Under the towers, in the drip, on planks laid over the wet ground '
        'by whoever needed to cross last, and the presses get louder for '
        'twenty minutes and then you are in them.',),
    frozenset(('marrow', 'vertical')): (
        'Out from under the roof and into the shadow of the tower, which '
        'starts four streets before the tower does.',
        'The approach is a boulevard nobody walks on, with the Vertical at '
        'the end of it doing what it was built to do, which is be seen from '
        'four streets away.',),
    frozenset(('marrow', 'glasshouse')): (
        'East along the cable run, past the point where the sheeting stops '
        'and the lit wall of the Glasshouse starts being the reason you can '
        'see where you are going.',),
    frozenset(('marrow', 'freeport')): (
        'Down the ramp to the dock road, where the crowd thins and the '
        'people in it start being people who are on a rota.',),
    frozenset(('marrow', 'precinct')): (
        'Four streets that get quieter each one, and then a building with '
        'the windows too small and a queue outside it in the weather.',),
    frozenset(('vertical', 'green')): (
        'The link road, which is a private road, which nobody stops you '
        'walking down and everybody notices you walking down.',),
    frozenset(('vertical', 'terraces')): (
        'Down the back of the hill through the service estate that Kagawa '
        'built for the people who worked in the tower, when they still '
        'housed them.',),
    frozenset(('vertical', 'precinct')): (
        'Past the loading deck and the vans, over the yard wall, or round '
        'it like everybody else, and the two buildings look at each other '
        'the whole way.',),
    frozenset(('green', 'glasshouse')): (
        'Through the landscaping, which stops at a line you can see from '
        'either side, and then it is frontage and glass and people looking '
        'at their own reflections.',),
    frozenset(('glasshouse', 'freeport')): (
        'Along the cut, past the bay doors, where the difference between the '
        'two districts is that one of them polishes the glass.',),
    frozenset(('glasshouse', 'row')): (
        'Two streets, and the noise stops. That is the whole of the '
        'crossing: you notice the silence before you notice the stone.',),
    frozenset(('glasshouse', 'hall')): (
        'East past the last of the frontage and into the approach roads for '
        'a station that has not run a train in eleven years, and the '
        'singing carries further than you expect.',),
    frozenset(('freeport', 'shambles')): (
        'Through the gate the dockers use to get to the clinic, which is the '
        'shortest road between anywhere and Carrion, and is well worn.',),
    frozenset(('freeport', 'row')): (
        'Up from the water into the money, in about four hundred metres, '
        'past two sets of gates that are open and one that is not.',),
    frozenset(('terraces', 'stacks')): (
        'Down the water-tower stairs with the drip on your neck the whole '
        'way and the roofs of the Stacks coming up under you.',),
    frozenset(('row', 'hall')): (
        'Along the back of the institutions to the old concourse, where the '
        'pavement stops being swept about halfway.',),
}


def crossing(a: str, b: str, shift: int) -> str:
    """What is between two districts, or '' if nobody wrote it."""
    lines = CROSSINGS.get(frozenset((a, b)), ())
    return lines[shift % len(lines)] if lines else ''
