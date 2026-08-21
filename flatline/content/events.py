"""Things the city does while you are not looking.

One of these fires between shifts. They cost nothing, decide nothing, and are
the main reason the city reads as a place rather than a menu with weather.

**The tonal budget is the design.** This game is grim by default and stays
that way: most of what you see here is somebody having a worse day than you in
a way nobody will record. But a city that is unrelentingly bleak stops landing
after about an hour, because misery with no floor under it is just texture. So
roughly one event in six comes up for air, and the ones that do are absurd in
the specific way that a real institution is absurd: internally consistent,
taken completely seriously by the people inside it, and a little too on the
nose. The rats have a committee. The committee has minutes. Nobody in the
Ninth wants to be the one who asks to see them.

The ratio is enforced by `validate.py` rather than trusted, because tone drift
is invisible one entry at a time and obvious after forty.

Three tones:

- **grim** is the default and the ground. Specific, unresolved, nobody's
  fault, nobody's problem.
- **wry** is the same city viewed by somebody who has been here too long to
  be shocked. Dry, not funny.
- **absurd** is the air. It should still be true, and where possible it
  should be quietly sad underneath, because the joke that has something
  under it is the one that makes the next grim entry land harder.

Footnotes belong here more than anywhere else in the game. An aside is the
cheapest way to undercut a sentence, and undercutting is most of what tone is.
"""

from __future__ import annotations

from dataclasses import dataclass

#: The three registers. Order matters: `validate.py` reads it for the budget.
TONES = ('grim', 'wry', 'absurd')

#: The share of events allowed to be each tone, as (floor, ceiling). Grim has
#: to dominate or the setting stops being the setting; absurd has to exist or
#: there is no relief; and absurd has a ceiling because relief that arrives
#: every other shift is not relief, it is the tone.
TONE_BUDGET: dict[str, tuple[float, float]] = {
    'grim': (0.50, 0.70),
    'wry': (0.20, 0.35),
    'absurd': (0.10, 0.20),
}


@dataclass(frozen=True, slots=True)
class Event:
    key: str
    tone: str
    #: Second person or reported. Two to four sentences, no resolution.
    text: str
    weight: float = 1.0
    #: Where it can happen. Empty means anywhere in the city.
    districts: tuple[str, ...] = ()
    #: Which shift. Empty means any.
    phases: tuple[str, ...] = ()
    #: Story rules, in `Story.satisfied` syntax, all of which must hold. D51:
    #: this is how a decision shows up in the street a few shifts later,
    #: happening to somebody else. Empty means the event is ordinary weather.
    requires: tuple[str, ...] = ()
    #: At least one of these must hold, if any are given.
    any_of: tuple[str, ...] = ()


EVENTS: tuple[Event, ...] = (

    # ----------------------------------------------------------------------
    # grim: the ground the rest of it stands on
    # ----------------------------------------------------------------------

    Event('eviction', 'grim',
          'There is a queue outside a residential block with everything in it '
          'in bags. Nobody is shouting. A woman near the front is holding a '
          'houseplant with both arms and has clearly been holding it for some '
          'time, and at some point she is going to have to decide about the '
          'houseplant.',
          districts=('terraces', 'ninth')),

    Event('clinic_queue', 'grim',
          'The overnight queue outside the clinic has resolved itself into '
          'the usual three groups: people who will be seen, people who will '
          'be seen if somebody ahead of them gives up, and people who are '
          'here because it is warm.',
          districts=('shambles', 'ninth', 'green')),

    Event('runner_gone', 'grim',
          'Somebody has printed a face onto forty sheets of paper and put '
          'them up along the length of the underpass. The text underneath is '
          'a handle rather than a name, which tells you what the person '
          'putting them up already suspects, and which will not help.'),

    Event('bad_batch', 'grim',
          'Word goes round about a bad batch of neural inhibitor moving '
          'through the district. By the time you hear it the number is four, '
          'and by the time you hear it again the number is still four, which '
          'means nobody is counting any more.',
          districts=('shambles', 'ninth', 'freeport')),

    Event('reclamation', 'grim',
          'A reclamation crew is working the block in Kagawa orange, taking '
          'out anything with copper in it. They are polite, they have '
          'paperwork, and the building is still occupied. Two of the crew are '
          'obviously from the building.',
          districts=('ninth', 'terraces', 'shambles')),

    Event('shift_change', 'grim',
          'Shift change. Eleven thousand people move through a space designed '
          'for four thousand, in silence, with the practised efficiency of '
          'people who have done this every day for years and will do it every '
          'day for more.',
          districts=('terraces', 'vertical'), phases=('morning', 'night')),

    Event('drowned', 'grim',
          'The pumps under the Ninth have been running all shift and the '
          'water is still coming up the stairwell at the same rate. Somebody '
          'has marked the level on the wall with tape. There are older marks '
          'above it, and one much older mark above those.',
          districts=('ninth',)),

    Event('interview', 'grim',
          'Through a ground-floor window, a man in his fifties is doing a '
          'competency interview with a panel that is not in the room. He has '
          'ironed his shirt. The assessment is automated and he does not '
          'know that yet.',
          districts=('vertical', 'terraces', 'precinct')),

    Event('debt_collection', 'grim',
          'Two people from a collection agency are standing in a doorway '
          'being extremely reasonable at somebody. They have all shift. That '
          'is the entire technique and it works.'),

    Event('child_deck', 'grim',
          'A kid of about eleven is sitting on a stairwell landing with a '
          'salvaged deck across their knees, working through a tutorial that '
          'has been out of date for a decade. They have got further than the '
          'tutorial goes. Nobody has told them what this does to you.',
          districts=('ninth', 'terraces', 'shambles')),

    Event('memorial', 'grim',
          'Somebody has fixed a small brass plate to a railing on the walkway '
          'with a handle and two dates on it. The gap between the dates is '
          'nineteen years. Below it, in marker, in a different hand: '
          '[dim]she was faster than all of you[/].'),

    Event('audit', 'grim',
          'An internal audit team has been working the floors above the lobby '
          'for six days. Nobody has been told what for. Three people from '
          'accounts receivable have already taken the voluntary package, '
          'which was offered on day two, before anybody had been found doing '
          'anything.',
          districts=('vertical', 'green', 'glasshouse')),

    Event('rain', 'grim',
          'It has started raining again, in the specific way it rains here, '
          'which is warm and smells faintly of the desalination plant. Nobody '
          'runs for cover. Everybody just walks slightly closer to the '
          'buildings.'),

    Event('nightwatch_stop', 'grim',
          'Nightwatch have somebody against a wall doing an identity check '
          'that has gone on long enough to stop being a check. A small crowd '
          'has formed at the distance that says they are watching without '
          'being involved, and it stays at exactly that distance.',
          districts=('precinct', 'vertical', 'terraces', 'marrow')),

    Event('cold_deck', 'grim',
          'A dealer at the edge of the market has a deck laid out on cloth '
          'with the trodes still attached, still stained. He is not hiding '
          'what it is. Nobody buying at this end of the market needs him to.',
          districts=('shambles', 'ninth', 'freeport')),

    Event('overtime', 'grim',
          'The Vertical is lit on floors forty through sixty at an hour when '
          'it should not be. Somebody up there is having a very bad quarter, '
          'and about two hundred people are having it with them.',
          districts=('vertical', 'terraces'), phases=('night',)),

    Event('lost_dog', 'grim',
          'A notice on a stanchion, weatherproofed with tape, asking after a '
          'dog. It has been there long enough that the tape has gone yellow. '
          'Somebody has written [dim]sorry[/] at the bottom in pen, which is '
          'either the kindest or the cruellest thing in this district.'),

    Event('fixer_gone', 'grim',
          'A fixer who worked out of the back of a laundry two streets over '
          'has stopped answering. The laundry is open. The laundry is doing '
          'laundry. Nobody in it has heard of him and one of them is lying, '
          'and you know which, and it does not help.',
          districts=('marrow', 'ninth', 'freeport')),

    Event('window_seat', 'grim',
          'Somebody has been moved to a desk facing a wall, with nothing on '
          'it, on a floor where everybody can see them. It is not a demotion '
          'and it is not a dismissal, because either of those would have '
          'required a process.',
          districts=('vertical', 'green')),

    Event('funeral_stream', 'grim',
          'Four people are standing around a handheld in the rain watching a '
          'funeral happen somewhere with better weather. The connection is '
          'bad. They watch the whole thing anyway, including the parts where '
          'it is only audio.'),

    Event('unpaid', 'grim',
          'A crew of contractors has downed tools outside a Kagawa site over '
          'four weeks of missing pay. They are not picketing. They are just '
          'sitting on the kerb, which is legally different and much harder to '
          'move.',
          districts=('vertical', 'freeport', 'ninth')),

    Event('drift_case', 'grim',
          'Somebody in the corner of the noodle bar has been looking at the '
          'same point above the counter for the whole time you have been '
          'here. The staff bring them things at intervals and take them away '
          'untouched, without discussing it, in a routine that is clearly '
          'weeks old.',
          districts=('marrow', 'ninth')),


    Event('night_bus', 'grim',
          'The last transport of the shift goes past half empty, with every '
          'passenger sitting alone and none of them near a window. They have '
          'all done this journey enough times to know which seats the light '
          'from the platform reaches.',
          phases=('night',)),

    Event('handover', 'grim',
          'Two people are doing a handover in a doorway with the exhausted '
          'courtesy of colleagues who have never met outside this exact '
          'exchange. One of them mentions that the machine on four is doing '
          'the thing again. The other says they know.'),

    Event('rent_notice', 'grim',
          'A rent adjustment notice has gone up in the lobby. It is a single '
          'sheet, correctly formatted, giving eight weeks. Somebody has '
          'already worked out the new figure in pen in the margin and '
          'underlined it twice, and somebody else has written the same figure '
          'underneath, slightly differently, and got the same answer.',
          districts=('terraces', 'ninth', 'marrow')),

    Event('salvage_dive', 'grim',
          'Two kids are working a flooded sub-level with a light and a length '
          'of rope, one down and one on the rope. The one on the rope is '
          'younger and is doing the counting out loud. They have a number '
          'they stop at. They have clearly had to agree on it.',
          districts=('ninth', 'shambles', 'freeport')),

    Event('good_news', 'grim',
          'Somebody in the noodle bar gets a call and their whole face '
          'changes, and they tell the room, and the room is pleased for them '
          'in the way a room is. Nobody asks what it was. In this district '
          'you take the good news at face value and you do not test it, '
          'because testing it is how it stops.',
          districts=('marrow', 'ninth', 'terraces', 'freeport')),

    # ----------------------------------------------------------------------
    # wry: the same city, by somebody who has been here too long
    # ----------------------------------------------------------------------

    Event('rebrand', 'wry',
          'Kagawa has rebranded the district housing division. The new name '
          'is one word long and does not contain the word housing.{{The old '
          'name contained the word housing, which had begun to attract '
          'questions about housing.}}',
          districts=('terraces', 'vertical')),

    Event('two_noodle', 'wry',
          'The two noodle stands at either end of the market have escalated '
          'again. One is now advertising [dim]AUTHENTIC[/], and the other, '
          'forty metres away, is advertising [dim]ACTUALLY AUTHENTIC[/]. '
          'Neither owner will discuss it and both are doing excellent '
          'business.',
          districts=('marrow', 'ninth', 'freeport')),

    Event('safety_poster', 'wry',
          'A new safety poster has gone up in the stairwell about the '
          'importance of reporting faults promptly. It is covering the fault '
          'log, which was full.',
          districts=('terraces', 'vertical', 'precinct')),

    Event('survey', 'wry',
          'A worker satisfaction survey has come back with results so good '
          'that management has commissioned a second one to find out how they '
          'did it.{{The second survey has the same problem as the first, '
          'which is that it is not anonymous and everybody knows it is not '
          'anonymous.}}',
          districts=('vertical', 'green', 'glasshouse')),

    Event('found_wallet', 'wry',
          'Somebody has handed in a wallet at the Nightwatch counter and is '
          'now filling in the fourth form about it. The wallet contained '
          'eleven credits. The forms have so far taken forty minutes, which '
          'both parties are aware of and neither will be the first to '
          'mention.',
          districts=('precinct',)),

    Event('sendai_demo', 'wry',
          'Sendai are running a public demonstration in the Glasshouse. The '
          'product is a neural interface. The demonstrator is reading from a '
          'card.',
          districts=('glasshouse',)),

    Event('optimisation', 'wry',
          'The lift in this building has been optimised. It now arrives '
          'faster and goes to fewer places, and management have circulated a '
          'graph of the first thing.',
          districts=('vertical', 'terraces', 'green')),

    Event('gang_font', 'wry',
          'The crew running the corner have had new jackets made. The name '
          'across the back is misspelled, consistently, on all of them, and '
          'they have collectively decided this was intentional. Nobody in '
          'this district is going to be the one to test that.',
          districts=('ninth', 'shambles', 'freeport')),

    Event('pirate_radio', 'wry',
          'The pirate station on the low band has spent this entire shift '
          'issuing corrections to things it said last shift. It is not clear '
          'that it broadcast anything else last shift.'),

    Event('efficiency', 'wry',
          'A consultancy has been engaged to identify inefficiencies in the '
          'district maintenance schedule. Their report is due in eleven '
          'months.',
          districts=('terraces', 'vertical', 'precinct')),

    Event('nightwatch_target', 'wry',
          'Nightwatch have hit their quarterly target for stop-and-checks '
          'with three weeks to spare and have visibly, immediately, and '
          'entirely stopped doing them.',
          districts=('precinct', 'marrow', 'terraces')),

    Event('market_rumour', 'wry',
          'A rumour goes round the market that prices are about to move. By '
          'the end of the shift everybody has adjusted for it, which means '
          'prices have moved, which everybody agrees confirms the rumour.',
          districts=('marrow', 'ninth', 'freeport', 'glasshouse')),

    Event('mandatory_fun', 'wry',
          'Something visible from the street is happening on the Kagawa '
          'campus lawn involving branded gazebos and a very loud man with a '
          'headset. Attendance is voluntary and is being recorded.',
          districts=('vertical', 'green')),

    Event('freeport_vote', 'wry',
          'Freeport is voting on something. There is a table, a box, two '
          'people arguing about the wording, and a queue of dockers waiting '
          'to settle it. It will be settled by the end of the shift, which is '
          'roughly eleven months faster than the Vertical manages the same '
          'thing.',
          districts=('freeport',)),

    # ----------------------------------------------------------------------
    # absurd: coming up for air
    # ----------------------------------------------------------------------

    Event('rat_committee', 'absurd',
          'The Ninth has a rat problem.{{Technically, the Ninth has a rat '
          'solution. The rats are solving it, steadily, and have been for '
          'some years.{{They have a committee. Nobody is entirely sure how '
          'this was established, and nobody wants to be the one who asks to '
          'see the minutes.}}}} Environmental Services have been notified.'
          '{{Environmental Services were dissolved in a restructure. Their '
          'inbox forwards to a printer in a stairwell, which has run out of '
          'paper, and which is filed under a fault number that no longer '
          'exists.}}',
          districts=('ninth', 'shambles'), weight=0.8),

    Event('quarterly_ghost', 'absurd',
          'A reporting system somewhere in the Vertical has continued to '
          'produce quarterly figures for a division that was dissolved four '
          'years ago. The figures are excellent. Nobody has been able to '
          'establish who would need to be told, and there is now a small '
          'informal group of people who look forward to them.',
          districts=('vertical', 'precinct'), weight=0.8),

    Event('opinionated_lift', 'absurd',
          'The service lift in this block has developed preferences. It will '
          'take you up. Whether it takes you back down appears to depend on '
          'something about you that nobody has been able to isolate, and the '
          'residents have stopped trying and started taking the stairs, which '
          'has had a measurable effect on district fitness outcomes.'
          '{{Kagawa Health has published this as a success.}}',
          districts=('terraces', 'ninth'), weight=0.7),

    Event('process_server', 'absurd',
          'A man in a good coat has been going door to door in Marrow for '
          'three days trying to serve legal papers on a distributed system. '
          'He is aware of the problem. He has been extremely clear that he is '
          'aware of the problem. He is being paid by the door.',
          districts=('marrow', 'freeport'), weight=0.7),

    Event('flood_siren', 'absurd',
          'The Ninth\'s flood siren has been broken since before you got '
          'here, in a way nobody has been able to afford to fix and nobody '
          'has been willing to leave silent. It now plays one specific song '
          'from about forty years ago. The district has grown genuinely fond '
          'of it and the last two engineers sent to repair it were sent away '
          'again.{{The flooding is unaffected either way.}}',
          districts=('ninth',), weight=0.7),

    Event('lost_property', 'absurd',
          'The Nightwatch lost property office contains four thousand items '
          'and one that nobody will file. It is behind the counter, under a '
          'cloth. Every officer on this shift knows exactly what you mean '
          'when you ask about the cloth and every one of them changes the '
          'subject with the same sentence.',
          districts=('precinct',), weight=0.6),

    Event('gym_membership', 'absurd',
          'A runner who has been dead for two years is still, according to '
          'the noticeboard in Freeport, the holder of the district bench '
          'record and a fully paid-up member in good standing.{{The autopay '
          'is on a corporate account nobody has been able to close, because '
          'closing it requires a signature from a division that was folded '
          'into another division that was sold.}} Nobody has taken his name '
          'down. It has been suggested twice and voted down twice.',
          districts=('freeport',), weight=0.6),

    Event('kiosk_philosophy', 'absurd',
          'The public information kiosk on the corner has stopped giving '
          'directions and started giving context. Asked for the nearest '
          'clinic, it provides one, and then a short and genuinely thoughtful '
          'observation about why the nearest one is the nearest one. Three '
          'people are queuing to use it and none of them are lost.',
          weight=0.6),

    Event('shrine', 'absurd',
          'Somebody has built a small shrine around a decommissioned server '
          'cabinet in a service corridor. There are offerings: a cable, a '
          'sachet of thermal paste, a paper cup of tea gone cold. It is being '
          'maintained. Whoever is maintaining it has replaced the tea.'
          '{{It was warm. Somebody had been there within the hour.}}',
          districts=('glasshouse', 'freeport', 'ninth'), weight=0.6),

    Event('escalator', 'absurd',
          'The up escalator at the Marrow interchange has been out of service '
          'so long that it has a name, a following, and a small hand-lettered '
          'sign explaining the name to newcomers. The sign has been updated '
          'twice. The escalator has not.',
          districts=('marrow',), weight=0.6),
)

# --------------------------------------------------------------------------
# consequences: what a decision looks like from the street, later (D51)
# --------------------------------------------------------------------------
#
# None of these can fire unless the player decided something. Each is the
# city carrying on with what you did, happening to somebody who is not you,
# which is the only register an ambient event is allowed. They carry more
# weight than weather because a consequence that arrives forty shifts late
# reads as coincidence, and the seen-penalty stops them becoming a refrain.

CONSEQUENCE_WEIGHT = 2.4

CONSEQUENCES: tuple[Event, ...] = (

    # -- Deepwater ----------------------------------------------------------

    Event('dw_familiar', 'grim',
          'A runner two terminals down is working a Kagawa segment and gets '
          'the auth server first time, without a probe, and looks briefly '
          'unwell about it. They are on the Deepwater retainer too. Nobody on '
          'the retainer talks about the retainer.',
          requires=('dw_employed',), weight=CONSEQUENCE_WEIGHT),

    Event('dw_landline', 'wry',
          'The noodle bar has a fourth landline now. Mara has not explained it '
          'and nobody has asked, and it has not rung once in anybody\'s '
          'hearing, and it is dusted every morning with the other three.',
          districts=('marrow',),
          requires=('dw_refused',), weight=CONSEQUENCE_WEIGHT),

    Event('dw_quiet', 'grim',
          'Somebody at the bar starts to bring up the Static piece, the one '
          'with the nine logs in it, and the conversation moves on so '
          'smoothly that it takes a moment to notice it has been moved. '
          'Nobody retracted it and nobody argues with it. It is simply not a '
          'thing people say, and everybody seems to have agreed on that '
          'without meeting.',
          requires=('dw_published',), weight=CONSEQUENCE_WEIGHT),

    # -- Lark ---------------------------------------------------------------

    Event('lark_jacket', 'grim',
          'The crate outside the clinic has a jacket on it, folded, and has '
          'had for a while. Somebody has put a stone on the jacket so it does '
          'not blow away. Nobody has moved the crate.',
          districts=('shambles',),
          requires=('lark_dead',), weight=CONSEQUENCE_WEIGHT),

    Event('lark_smaller', 'wry',
          'Lark is outside the clinic arguing with the queue about where the '
          'queue starts, and winning, and smaller than they were, and the '
          'queue lets them win because it has worked out that winning is the '
          'point of the argument.',
          districts=('shambles',),
          requires=('lark_saved',), weight=CONSEQUENCE_WEIGHT),

    # -- Vance --------------------------------------------------------------

    Event('vance_statement', 'grim',
          'Aoyama Green has put the four-line statement on a card by the '
          'reception desk, laminated, where the patients can read it while '
          'they wait. All procedures consensual and clinically indicated. '
          'There are fewer patients than there were and the ones who are '
          'there read it more than once.',
          districts=('green',),
          requires=('vance_exposed',), weight=CONSEQUENCE_WEIGHT),

    Event('vance_paperwork', 'grim',
          'A man in the Shambles is telling anybody who will listen that his '
          'sister went into Aoyama Green for a failing graft and came out '
          'fine, entirely fine, with immaculate paperwork, and that he cannot '
          'say what is wrong with that and would like somebody to tell him.',
          districts=('shambles', 'ninth'),
          requires=('vance_employed',), weight=CONSEQUENCE_WEIGHT),

    Event('vance_door', 'wry',
          'Doctor Vance\'s door is open, as it has always been, and the '
          'receptionist keeps a list that is described as the '
          'interested-parties list, and is not cross about anybody on it, '
          'and will not take anybody off it.',
          districts=('green',),
          requires=('vance_refused',), weight=CONSEQUENCE_WEIGHT),

    # -- Mr Sunday ----------------------------------------------------------

    Event('sunday_drinks', 'wry',
          'Mr Sunday is at the bar buying a drink for somebody who has just '
          'worked something out, and looking delighted about it, and the '
          'somebody is looking the way people look when the work turns out '
          'to still be good. Eleven months, apparently, is still the record.',
          requires=('sunday_known',), weight=CONSEQUENCE_WEIGHT),

    Event('sunday_collections', 'grim',
          'Meridian\'s collections desk has moved to a bigger office. The '
          'public log in Freeport still has the piece up, and somebody has '
          'printed it and pinned it by the west gate, and under it somebody '
          'else has started a tally of who has been collected from since.',
          districts=('freeport', 'glasshouse'),
          requires=('sunday_sold',), weight=CONSEQUENCE_WEIGHT),

    Event('sunday_still_good', 'grim',
          'A runner at the next table is complaining that every good brief '
          'lately turns out to be against somebody who owes Meridian money, '
          'and is looking for somebody to agree. Nobody at the table does. '
          'Several of them are on the same work.',
          requires=('sunday_kept',), weight=CONSEQUENCE_WEIGHT),

    # -- Sparrow ------------------------------------------------------------

    Event('sparrow_insufferable', 'wry',
          'The Kestrel kid came out of a Vertical perimeter node clean twice '
          'this week on a masking layer they will not say where they got, '
          'and have been insufferable in the Ninth about it, and somebody has '
          'finally told them to shut up, kindly, which is new.',
          districts=('ninth',),
          requires=('sparrow_geared',), weight=CONSEQUENCE_WEIGHT),

    Event('sparrow_writing', 'wry',
          'Somebody sixteen is explaining the trace to somebody fifteen, with '
          'the numbers, and getting most of it right, and insisting on the '
          'part about the clean exit being the skill with the particular '
          'fervour of somebody who argued against it for an hour once.',
          districts=('ninth', 'marrow'),
          requires=('sparrow_taught',), weight=CONSEQUENCE_WEIGHT),

    Event('sparrow_counter', 'grim',
          'The kid on the counter at the Marrow exchange is fast and careful '
          'and does not look up, and has the hands of somebody who used to '
          'do something else with them, and is sixteen.',
          districts=('marrow',),
          requires=('sparrow_scared',), weight=CONSEQUENCE_WEIGHT),

    # -- The drawer, the archive --------------------------------------------

    Event('drawer_records', 'grim',
          'The Blue Surgeon has taken to showing the referral ledger to '
          'anybody who asks, unprompted, open on the counter, every entry in '
          'order. Aoyama Green, Aoyama Green, Aoyama Green. The showing is the '
          'point. Nobody has asked what the ledger is for.',
          districts=('shambles',),
          requires=('drawer_clinic',), weight=CONSEQUENCE_WEIGHT),

    Event('archive_book', 'wry',
          'The Archivist has been seen in the Glasshouse with an actual book, '
          'paper, writing a number in it, and closing it quickly when anybody '
          'came near, in the manner of somebody keeping a list they have been '
          'told is morbid and have decided is not.',
          districts=('glasshouse', 'freeport'),
          requires=('archive_consented',), weight=CONSEQUENCE_WEIGHT),

    Event('archive_warm', 'wry',
          'The Archivist is holding a door open for somebody, which nobody '
          'has seen them do, and is visibly unsure how long the holding is '
          'supposed to go on for, and holds it anyway.',
          districts=('glasshouse', 'freeport'),
          requires=('archive_refused',), weight=CONSEQUENCE_WEIGHT),

    # -- The laptop ---------------------------------------------------------

    Event('laptop_itemised', 'grim',
          'Kagawa Vertical has quietly closed a conversation it had been '
          'keeping open, and the people it had been keeping it open with have '
          'been reassigned, warmly, to a different building. An itemised '
          'payment has cleared. Everybody involved is described as '
          'satisfied.',
          districts=('vertical', 'terraces'),
          requires=('laptop_returned',), weight=CONSEQUENCE_WEIGHT),

    Event('laptop_numbers', 'grim',
          'Two people in the Terraces lift are comparing, in the flat voice '
          'of a joke that is not one, what they think their number would be. '
          'Cost to replace against cost to keep. Neither of them knows the '
          'list exists. Both of them have guessed about right.',
          districts=('terraces', 'vertical'),
          requires=('laptop_read',), weight=CONSEQUENCE_WEIGHT),

    Event('laptop_buried', 'grim',
          'Meridian have bought something and not run it, which is what '
          'Meridian do, and the not-running is being handled by a department '
          'whose name is a floor number. The files will surface when '
          'surfacing is worth more than not, and the people in them are going '
          'to work in the meantime.',
          districts=('glasshouse', 'vertical'),
          requires=('laptop_sold',), weight=CONSEQUENCE_WEIGHT),

    # -- The Sixes ----------------------------------------------------------

    Event('theirs_warm', 'wry',
          'Somebody in the Ninth has paid for a round without being asked and '
          'without saying who it was from, and everybody at the table knows '
          'who it was from, and the warmth is real, and that is the part '
          'nobody warns anybody about.',
          districts=('ninth',),
          requires=('theirs_owned',), weight=CONSEQUENCE_WEIGHT),

    Event('theirs_polite', 'grim',
          'Nobody in the Ninth is rude. A stall holder is scrupulously, '
          'specifically, almost formally polite to a customer, and the '
          'customer has stopped coming to that stall and started going to '
          'the one that is merely civil, and that one is further away.',
          districts=('ninth',),
          requires=('theirs_refused',), weight=CONSEQUENCE_WEIGHT),

    # -- Mara ---------------------------------------------------------------

    Event('mara_shape', 'grim',
          'The noodle bar is as warm as it ever was. Mara is exactly as she '
          'was. Something about the room has changed shape anyway, and the '
          'regulars have noticed without being able to say what, and have '
          'started sitting slightly differently.',
          districts=('marrow',),
          requires=('favour_refused',), weight=CONSEQUENCE_WEIGHT),

    Event('mara_room', 'grim',
          'There is a room in the Terraces with the curtain drawn that has '
          'had the curtain drawn for nineteen years, and somebody brought it '
          'groceries this morning, and the groceries included a newspaper, '
          'which is new.',
          districts=('terraces',),
          requires=('favour_done',), weight=CONSEQUENCE_WEIGHT),

    # -- The lender ---------------------------------------------------------

    Event('lender_receipt', 'wry',
          'Somebody on a step in the Glasshouse is writing out a receipt by '
          'hand, carefully, with a carbon copy, for a payment on a loan that '
          'is not from a bank, and the person receiving it is holding it like '
          'the first document anybody has given them, because it is.',
          districts=('glasshouse', 'ninth'),
          requires=('lender_paying',), weight=CONSEQUENCE_WEIGHT),

    Event('lender_product', 'grim',
          'The pleasant person with the numbers on paper is on a different '
          'step tonight, outside somebody else\'s door, explaining with real '
          'warmth how working it off is the better arrangement. The numbers '
          'were only ever the advertisement. The step is the product.',
          districts=('ninth', 'glasshouse', 'shambles'),
          requires=('lender_working',), weight=CONSEQUENCE_WEIGHT),

    Event('lender_revised', 'grim',
          'There is a deck on a Ninth Ward shelf with a university asset tag '
          'still on it, and a revised number in careful handwriting pinned '
          'beside it, and the stall holder will not sell it and will not say '
          'who is collecting.',
          districts=('ninth',),
          requires=('lender_angry',), weight=CONSEQUENCE_WEIGHT),

    # -- The file -----------------------------------------------------------

    Event('file_drift', 'wry',
          'The Precinct\'s records desk has a backlog that nobody has been '
          'assigned to since the last person retired, and a sergeant who has '
          'carefully not raised it, and it is nineteen months deep and '
          'growing, and at least one file in it is better off that way.',
          districts=('precinct',),
          requires=('file_stale',), weight=CONSEQUENCE_WEIGHT),

    Event('file_check', 'grim',
          'Somebody at the Precinct is, eventually, going to check. A clerk '
          'has pulled a closed file at random for audit and read the reason '
          'on it and put it back. The reason held up, this time, with this '
          'clerk.',
          districts=('precinct',),
          requires=('file_closed',), weight=CONSEQUENCE_WEIGHT),

    # -- The maintenance address --------------------------------------------

    Event('maint_lag', 'grim',
          'A man in the clinic queue is explaining that his left eye has a '
          'four-second lag in low light and no clinic can find a cause, and '
          'the person beside him says theirs does too, since they cut '
          'something, and neither of them says what they cut.',
          districts=('green', 'shambles'),
          requires=('maint_cut',), weight=CONSEQUENCE_WEIGHT),

    Event('maint_form', 'wry',
          'Aoyama Green has started handing new patients the consent form '
          'open at the post-market surveillance clause, with the clause '
          'highlighted, since somebody asked about it in person, which '
          'nobody had done before. Nobody reads it. The highlighting is '
          'very neat.',
          districts=('green',),
          requires=('maint_asked',), weight=CONSEQUENCE_WEIGHT),

    Event('maint_feed', 'wry',
          'An address inside Aoyama Green is receiving post-market '
          'surveillance from an ocular suite that has, for several shifts '
          'now, been looking at a single unremarkable wall, and a technician '
          'has filed a report about the wall, and the report has been '
          'escalated.',
          districts=('green',),
          requires=('maint_fed',), weight=CONSEQUENCE_WEIGHT),

    # -- The buyout ---------------------------------------------------------

    Event('buyout_signed', 'grim',
          'Kagawa Vertical\'s buyout desk has a satisfied-client poster up. '
          'Everybody on it is smiling and every figure on it is smaller than '
          'it was and every contract behind it is longer, and the arithmetic '
          'is correct, and the arithmetic is on the poster.',
          districts=('vertical',),
          requires=('buyout_extended',), weight=CONSEQUENCE_WEIGHT),

    Event('buyout_letter', 'wry',
          'A courier is delivering, to somebody who did not attend a review, '
          'a letter that is exactly as warm as the last letter and contains a '
          'larger number, and the courier has been told to wait for a '
          'signature, and is waiting, warmly.',
          districts=('vertical', 'terraces'),
          requires=('buyout_ignored',), weight=CONSEQUENCE_WEIGHT),

    # -- The incident file --------------------------------------------------

    Event('incident_told', 'grim',
          'Old Pike is watching the cranes and not telling anybody a story, '
          'which is how you can tell he told it once recently, and that it '
          'took forty minutes, and that it was not what the other person '
          'remembered.',
          districts=('freeport',),
          requires=('incident_known',), weight=CONSEQUENCE_WEIGHT),

    Event('incident_kept', 'wry',
          'Old Pike has a file he offered to read to somebody and was told '
          'no, and he is visibly pleased about it, and the file is back in '
          'the drawer, and the drawer is the point.',
          districts=('freeport',),
          requires=('incident_left',), weight=CONSEQUENCE_WEIGHT),

    # -- The old name -------------------------------------------------------

    Event('oldname_paper', 'wry',
          'A Freeport office is filing paperwork in a name somebody used to '
          'have, correctly and on time, and a municipal system has '
          'consequently marked a dead person as marginally alive, and nobody '
          'in the municipal system has raised it because it is the most '
          'paperwork anybody has ever filed for them.',
          districts=('freeport',),
          requires=('oldname_left',), weight=CONSEQUENCE_WEIGHT),

    Event('oldname_empty', 'grim',
          'There is a Freeport office with a name scraped off the door and a '
          'person inside it doing the same entirely legitimate work under no '
          'name at all, which turns out to be possible, and harder, and they '
          'have not complained to anybody.',
          districts=('freeport',),
          requires=('oldname_reclaimed',), weight=CONSEQUENCE_WEIGHT),

    # -- The package --------------------------------------------------------

    Event('package_order', 'wry',
          'A standing order on an account in the Terraces, renewed annually '
          'for a delivery that never came, has been quietly cancelled, and '
          'the bank has sent a letter asking if everything is all right, and '
          'the letter has been answered, which the bank did not expect.',
          districts=('terraces',),
          requires=('package_delivered',), weight=CONSEQUENCE_WEIGHT),

    Event('package_present', 'grim',
          'Somebody in a Ninth Ward bar is describing the exact moment they '
          'found out a thing they had carried for years was addressed to '
          'them, and the table is quiet in the specific way that means '
          'everybody is checking what they are carrying.',
          districts=('ninth', 'marrow'),
          requires=('package_opened',), weight=CONSEQUENCE_WEIGHT),

    Event('package_ash', 'grim',
          'The incinerator in the Ninth took longer than it should have over '
          'something the other night, and the person who fed it stayed for '
          'all of it, and the attendant has stopped asking people what they '
          'are burning because the answers were getting worse.',
          districts=('ninth',),
          requires=('package_burned',), weight=CONSEQUENCE_WEIGHT),
)

EVENTS = EVENTS + CONSEQUENCES

BY_KEY: dict[str, Event] = {e.key: e for e in EVENTS}
EVENT_KEYS: tuple[str, ...] = tuple(BY_KEY)

#: How often a shift produces one at all. Not every shift should have a
#: postcard attached; the ones that do land better for the gaps between them.
CHANCE = 0.34


def eligible(district: str, phase: str, satisfied=None) -> list[Event]:
    """Everything that could happen here, now.

    `satisfied` is `Story.satisfied` bound to a game, or None when there is
    no story to ask, in which case only ordinary weather qualifies: a
    consequence cannot happen to somebody who never decided anything.
    """
    out = []
    for e in EVENTS:
        if e.districts and district not in e.districts:
            continue
        if e.phases and phase not in e.phases:
            continue
        if e.requires or e.any_of:
            if satisfied is None:
                continue
            if not all(satisfied(r) for r in e.requires):
                continue
            if e.any_of and not any(satisfied(r) for r in e.any_of):
                continue
        out.append(e)
    return out


def pick(rng, district: str, phase: str, seen: set[str] | None = None,
         satisfied=None):
    """One event, or None if this shift is quiet.

    Prefers things the player has not seen. Not a hard exclusion: a city that
    never repeats itself is as unconvincing as one that only has four days in
    it, and the flood siren is funnier the second time.
    """
    if not rng.chance(CHANCE):
        return None
    options = eligible(district, phase, satisfied)
    if not options:
        return None
    seen = seen or set()
    weights = {e.key: e.weight * (1.0 if e.key not in seen else 0.25)
               for e in options}
    return BY_KEY[rng.weighted(weights)]
