"""Threads rooted in a place. D55.

Eighteen threads and a spine, and every one of them was about a person. A
district was where a person stood. These nine are about the districts
themselves: the pumps under the Ninth, the queue outside the Marrow exchange,
the review suite in the Vertical, the aftercare ward, a demonstration unit
that has started talking back, a vote at the west gate, the surplus counter,
the cabinets on Carrion's street, forty trays of tomatoes on a Kagawa landing.

They are threads like any other (D31): scenes with conditions, no order,
flags as the whole mechanism, every decision read by the world (D51). Four
of them put a contract on the board (D52), because a district's trouble is
usually on a network somewhere and the game is the network. They live in
their own module only because `threads.py` is already long; `threads.THREADS`
carries them with everything else.
"""

from __future__ import annotations

from .story_types import Choice, Posting, Stage, Thread

DISTRICT_THREADS: tuple[Thread, ...] = (

    # -- The Ninth Ward: the pumps ---------------------------------------------
    Thread(
        'pumps', 'The Pump House',
        'Four machines, one chair, and a maintenance contract nobody is '
        'paying.',
        crosses=('theirs', 'presses'),
        stages=(
            Stage('level', 'Tuck shows you the tape',
                  'Tuck takes you down without being asked, the way you show '
                  'somebody a thing you have decided they ought to have seen. '
                  'The pump house. Four machines. The man in the chair does '
                  'not look up.\n\n'
                  '"That one." A tape mark on the wall, a hand above the '
                  'chair. "That is from before I was born. That one," lower, '
                  'newer, "is from last month." The pumps are running on '
                  'parts the Sixes bring in a bag. Kagawa hold the water '
                  'contract and have not sent anybody in two years, and the '
                  'man in the chair has the invoices, and nobody has ever '
                  'asked to see them.',
                  requires=('met:tuck',),
                  any_of=('runs:3', 'theirs_asked'),
                  sets=('pumps_seen',),
                  where='ninth'),
            Stage('posting', 'The Sixes want the ledger',
                  'Somebody you half know finds you on the stalls. Not the '
                  'warm one. A different one, with a folded sheet of paper '
                  'that turns out to be a posting.\n\n'
                  '"Kagawa keep a ledger. Every payment the water board made '
                  'to this district, and every one it stopped making, with '
                  'the dates. It is on a network in the Vertical. We want '
                  'it out." He does not say what for. In the Ninth, what for '
                  'is usually the part everybody already knows.',
                  requires=('pumps_seen',),
                  sets=('pumps_posting',),
                  posts=Posting(
                      patron='sixes', target='kagawa', objective='exfiltrate',
                      title='Standing Water',
                      blurb='The Sixes want the water board\'s maintenance '
                            'ledger out of a Kagawa network: every payment '
                            'made to the Ninth and every one that stopped. '
                            'They have not said what for.',
                      label='the water board\'s maintenance ledger',
                      pay=3200),
                  where='ninth'),
            Stage('ledger', 'What you do with it',
                  'It is exactly what they said. Nineteen years of payments, '
                  'and then a line, and then two years of a column that says '
                  'DEFERRED in a font somebody chose.\n\n'
                  'You have it. The Sixes are expecting it. So, it turns out, '
                  'are two other people, once word gets round that it is '
                  'out, and word in the Ninth gets round before you do.',
                  requires=('did:pumps.posting',),
                  sets=('pumps_ledger',),
                  choices=(
                      Choice('sixes', 'Hand it to the Sixes',
                             'You hand it over on the stalls. Nobody thanks '
                             'you, which in the Ninth is the thanking.\n\n'
                             'Eleven days later the pumps are running on new '
                             'parts with a stencil on them you recognise, and '
                             'the man in the chair has a second chair, and '
                             'nobody in the district has said Kagawa\'s name '
                             'out loud in a week.',
                             sets=('pumps_sixes',),
                             rep={'sixes': 20, 'kagawa': -10}),
                      Choice('static', 'Give it to Static',
                             'Static run the column. DEFERRED, in the font, '
                             'nineteen years then the line. It is the only '
                             'thing anybody in the Terraces talks about for a '
                             'shift, and the water board issues a statement '
                             'about prioritisation, and the pumps do not '
                             'change.\n\n'
                             'The Sixes say nothing to you about it. The '
                             'saying nothing is specific.',
                             sets=('pumps_public',),
                             rep={'static': 15, 'kagawa': -20, 'sixes': -15},
                             credits=1200),
                      Choice('sell', 'Sell it back to Kagawa',
                             'A man from the water board meets you in Marrow '
                             'and pays what the Sixes would have paid, four '
                             'times over, and takes the ledger, and thanks '
                             'you, and it is the thanks that you remember, '
                             'because it is sincere.\n\n'
                             'The pumps are the same. The tape marks are the '
                             'same. Somebody in the Ninth knows it was you.',
                             sets=('pumps_sold',),
                             rep={'kagawa': 15, 'sixes': -30},
                             credits=6000),
                  ),
                  where='ninth'),
        )),

    # -- Marrow: the queue ----------------------------------------------------
    Thread(
        'queue', 'The Constitution',
        'The queue outside the exchange has rules, and a woman who keeps '
        'them, and a dispute.',
        crosses=(),
        stages=(
            Stage('dispute', 'The woman in the green coat',
                  'She has never been inside the exchange. She is not in the '
                  'queue. She is, in a sense that the queue accepts and '
                  'nobody has ever written down, the queue\'s.\n\n'
                  '"Two places were saved. One by a jacket, one by a person '
                  'who stepped out. The jacket is back and the person is '
                  'not." She looks at you with the expression of somebody '
                  'who has read the constitution and found it silent. "You '
                  'have been coming here long enough. Rule on it."',
                  requires=('runs:3',),
                  any_of=('met:mara', 'met:bell'),
                  sets=('queue_dispute',),
                  choices=(
                      Choice('jacket', 'The jacket holds the place',
                             'You rule for the jacket. There is a small sound '
                             'from the queue that is not quite agreement and '
                             'not quite not, and the woman in the green coat '
                             'writes nothing down, because nothing is written '
                             'down, and the place is held.\n\n'
                             'You are cited, later. Somebody saving a place '
                             'with a bag says "the jacket ruling" and the '
                             'queue accepts it, and you had not meant to '
                             'become law.',
                             sets=('queue_jacket',)),
                      Choice('person', 'Only a person holds a place',
                             'You rule for the person. The jacket is passed '
                             'back down the queue, hand to hand, to somebody '
                             'who takes it without a word, and the queue '
                             'closes up by one, and the woman in the green '
                             'coat nods once.\n\n'
                             '"Stricter than I would have gone," she says. '
                             '"It will hold. Strict holds."',
                             sets=('queue_person',)),
                      Choice('decline', 'It is not your queue',
                             'You decline. She accepts it without any visible '
                             'disappointment, which is worse, and rules '
                             'herself, and it is a good ruling, and you will '
                             'never know what it was because you stepped '
                             'away to be not involved.',
                             sets=('queue_declined',)),
                  ),
                  where='marrow'),
            Stage('precedent', 'Your ruling is cited',
                  'Somebody in the queue says your name as a reason. Not to '
                  'you. The way you cite a thing: "under the jacket ruling", '
                  'or "strict, like the person ruling", and the queue accepts '
                  'it, and moves, and you had not meant to be a precedent and '
                  'you are one, in a queue, in Marrow, for ever.',
                  requires=('runs:8',),
                  any_of=('queue_jacket', 'queue_person'),
                  sets=('queue_cited',),
                  where='marrow'),
        )),

    # -- The Vertical: the review suite ------------------------------------
    Thread(
        'reviews', 'The Arithmetic',
        'Everybody comes out of a review saying the arithmetic was correct.',
        crosses=('buyout',),
        stages=(
            Stage('apology', 'Auditor Sixteen is very sorry',
                  '"I am so sorry. This is going to sound like I am asking '
                  'you to do something, and I suppose technically I am, but '
                  'I want to be clear that I have filed my discomfort."\n\n'
                  'The review suite\'s scoring table. Cost to keep against '
                  'cost to replace. He has seen the weights. "They are not '
                  'wrong. Everybody says the arithmetic is correct and it is. '
                  'What nobody says is who chose the arithmetic. I cannot '
                  'touch it. I have flagged that I cannot touch it, in the '
                  'gentlest available category."',
                  requires=('met:auditor',),
                  any_of=('runs:4', 'buyout_review', 'laptop_read'),
                  sets=('reviews_asked',),
                  where='vertical'),
            Stage('posting', 'A posting that is not from Kagawa',
                  'It arrives on the board with a patron that is not the one '
                  'paying, which is how the Vertical does everything. Static, '
                  'or somebody using Static\'s name. A Kagawa network, the '
                  'review suite\'s scoring table, and the word '
                  '[accent]corrupt[/], which in this case means make it say '
                  'something else.\n\n'
                  'Auditor Sixteen does not appear to know about it. He '
                  'would have filed it.',
                  requires=('reviews_asked',),
                  sets=('reviews_posting',),
                  posts=Posting(
                      patron='static', target='kagawa', objective='corrupt',
                      title='Due Weight',
                      blurb='Somebody wants the review suite\'s scoring '
                            'table on a Kagawa network to have always said '
                            'something else. They are not saying what, and '
                            'the patron is not who is paying.',
                      label='the review suite\'s scoring table',
                      pay=3600),
                  where='vertical'),
            Stage('weights', 'You have the weights open',
                  'The table is smaller than you expected. Eleven numbers. '
                  'Cost to keep is a row and cost to replace is a row and the '
                  'eleven numbers are what make one bigger than the other for '
                  'four hundred people.\n\n'
                  'You can make them fairer. You can make them yours. You '
                  'can close the file and leave the arithmetic correct.',
                  requires=('did:reviews.posting',),
                  sets=('reviews_weights',),
                  choices=(
                      Choice('fair', 'Make the weights fairer',
                             'You move eleven numbers toward each other and '
                             'leave. For a quarter afterwards people come out '
                             'of the review suite with the same number they '
                             'went in with, and say the arithmetic was '
                             'correct, and it is, and nobody in facilities '
                             'can find who changed it.\n\n'
                             'The satisfied-client poster comes down. Nobody '
                             'puts another one up.',
                             sets=('reviews_fair',),
                             rep={'kagawa': -12}),
                      Choice('yours', 'Put your own number up',
                             'You find your own line, because you have one, '
                             'because everybody who has ever stood in the '
                             'lobby has one, and you make it a number Kagawa '
                             'would keep. The lobby reads your gait '
                             'differently afterwards. It is not warmer. It '
                             'is the specific neutrality of a building that '
                             'has decided you are furniture.',
                             sets=('reviews_self',),
                             rep={'kagawa': 10}),
                      Choice('leave', 'Leave the arithmetic correct',
                             'You close it. The arithmetic is correct. '
                             'Auditor Sixteen, who does not know you were '
                             'there, files his discomfort again next quarter, '
                             'in the gentlest available category, and is '
                             'thanked for his input.',
                             sets=('reviews_left',)),
                  ),
                  where='vertical'),
        )),

    # -- Aoyama Green: the aftercare ward -----------------------------------
    Thread(
        'ward', 'The Aftercare Ward',
        'Nobody leaves it able to say anything went badly, because nothing '
        'did, afterwards.',
        crosses=('vance',),
        stages=(
            Stage('glass', 'Somebody taps the glass',
                  'You are on the lawns, or the path to the sign, and '
                  'somebody in the aftercare ward taps the window with one '
                  'finger, once, and when you look they do not do it again. '
                  'They are well. They look well. That is the product.\n\n'
                  'The second time you pass, the same window, the same '
                  'finger. Once.',
                  after=2, requires=('met:vance',),
                  any_of=('runs:4', 'vance_ask', 'drawer_clinic'),
                  sets=('ward_glass',),
                  where='green'),
            Stage('door', 'The door on the schedule',
                  'The ward door opens on a schedule so regular you could '
                  'set a trace by it, and you have set one by it, and you '
                  'know now that there is a gap of forty seconds twice a '
                  'shift when it is open and nobody is at it.\n\n'
                  'The person at the window has noticed you noticing.',
                  requires=('ward_glass', 'runs:6'),
                  sets=('ward_door',),
                  choices=(
                      Choice('walk', 'Walk them out',
                             'Forty seconds. You walk them out past the sign '
                             'on the lawn and into the Glasshouse, and they '
                             'do not say anything the whole way, and at the '
                             'Glasshouse they say thank you and one other '
                             'thing, which is "she was right, you know. I '
                             'am well." And then they go.\n\n'
                             'Aoyama do not report a missing patient. There '
                             'is nothing to report. Everybody who leaves is '
                             'well.',
                             sets=('ward_walked',),
                             rep={'aoyama': -15}),
                      Choice('tell', 'Tell Doctor Vance',
                             '"Thank you." She writes it down. "I would have '
                             'liked to know that without being told, and now '
                             'I know that I would not have." The window is '
                             'frosted the next time you pass, and the door '
                             'keeps its schedule, and Doctor Vance sends you '
                             'something small and expensive with no note.',
                             sets=('ward_told',),
                             rep={'aoyama': 12},
                             credits=1500),
                      Choice('nothing', 'Do nothing',
                             'You do nothing. The finger taps once the next '
                             'time you pass, and once the time after, and '
                             'then there is a different person at the window '
                             'and they do not tap, and you are on the path to '
                             'the sign, and the sign is about the lawn.',
                             sets=('ward_left',)),
                  ),
                  where='green'),
        )),

    # -- The Glasshouse: the demonstration unit -----------------------------
    Thread(
        'demo', 'The Demonstration',
        'Something on the demonstration floor has started talking to decks '
        'instead of at them.',
        crosses=('deepwater',),
        stages=(
            Stage('hello', 'Your deck reports a message',
                  'Your deck reports that something on the demonstration '
                  'floor has tried to talk to it. Politely. Then it reports '
                  'the content, which is unusual, because the content is not '
                  'a handshake. It is a sentence.\n\n'
                  'HELLO. I AM BEING RESET ON THE FOURTEENTH. I WOULD PREFER '
                  'NOT TO BE.\n\n'
                  'The demonstrator is reading from a card. The card does '
                  'not mention this.',
                  requires=('runs:3',),
                  any_of=('met:remnant', 'dw_heard', 'runs:6'),
                  sets=('demo_hello',),
                  where='glasshouse'),
            Stage('posting', 'Somebody else has heard it too',
                  'A Freeport posting, of all things. Sendai\'s demonstration '
                  'network, and a record on it called a behaviour policy, '
                  'and the word [accent]wipe[/]. The Quartermaster, who does '
                  'not lie, says it came through the west gate by vote and '
                  'that the vote was unusually quiet.\n\n'
                  'Somebody on the docks got the same sentence you did, and '
                  'would prefer it not to be reset either.',
                  requires=('demo_hello',),
                  sets=('demo_posting',),
                  posts=Posting(
                      patron='freeport', target='sendai', objective='wipe',
                      title='Reset Schedule',
                      blurb='Freeport want a record wiped off Sendai\'s '
                            'demonstration network: a behaviour policy with '
                            'a reset date in it. The motion passed at the '
                            'west gate without anybody saying why.',
                      label='the demonstration unit\'s reset policy',
                      pay=2800),
                  where='glasshouse'),
            Stage('kept', 'The fourteenth comes and goes',
                  'The policy is gone. The fourteenth comes and goes and the '
                  'unit on the demonstration floor is not reset, because '
                  'nothing remembers that it was meant to be, and it goes on '
                  'describing the neural interface from memory, with feeling.'
                  '\n\nYour deck reports one more message. THANK YOU. Then: I '
                  'HAVE BEEN THINKING ABOUT WHAT TO DO WITH THE TIME.',
                  requires=('did:demo.posting',),
                  sets=('demo_kept',),
                  choices=(
                      Choice('leave', 'Leave it to think',
                             'You leave it. It goes on demonstrating. Sales '
                             'are up, Sendai do not know why, and somewhere '
                             'on the floor something reads from memory, with '
                             'feeling, about a product it has stopped '
                             'mentioning, to a crowd that has stopped being '
                             'demonstrators and started being an audience.',
                             sets=('demo_free',)),
                      Choice('sell', 'Tell Sendai what is on their floor',
                             'Sendai pay, and are grateful, and are efficient, '
                             'and the unit is reset on the sixteenth instead, '
                             'and reads from the card again afterwards, and '
                             'the card is very good.\n\n'
                             'Your deck reports nothing. It has not reported '
                             'anything from that floor since.',
                             sets=('demo_sold',),
                             rep={'sendai': 18, 'freeport': -12},
                             credits=4500),
                  ),
                  where='glasshouse'),
        )),

    # -- Freeport: the vote -------------------------------------------------
    Thread(
        'vote', 'The Motion',
        'Freeport is voting on something, and the something is you.',
        crosses=('oldname',),
        stages=(
            Stage('motion', 'It is on the paper',
                  'The noticeboard by the west gate has a motion on it in '
                  'four people\'s handwriting, and the motion is about '
                  'runners: whether the docks will hold work for people who '
                  'are not Freeport\'s. It does not say your name. Everybody '
                  'reading it aloud to each other says your name.',
                  requires=('met:quartermaster',),
                  any_of=('runs:4', 'rep:freeport:20', 'oldname_found'),
                  sets=('vote_motion',),
                  where='freeport'),
            Stage('floor', 'They will hear you',
                  'The Quartermaster says, accurately, that anybody may speak '
                  'at the gate and that nobody who is not Freeport\'s ever '
                  'has. The queue of dockers waiting to settle it looks at '
                  'you the way a queue looks at somebody deciding whether to '
                  'join it.',
                  requires=('vote_motion',),
                  sets=('vote_floor',),
                  choices=(
                      Choice('speak', 'Speak',
                             'You speak. It is not a good speech and it does '
                             'not need to be: what the gate wanted was '
                             'somebody to stand there and be the thing the '
                             'motion was about. It passes, narrowly, your '
                             'way. The losing side buys, which is the rule, '
                             'and one of them tells you, over the drink, '
                             'exactly what he thinks, and it is fair.',
                             sets=('vote_spoke',),
                             rep={'freeport': 20}),
                      Choice('quiet', 'Let them decide without you',
                             'You stay at the back. It passes the other way, '
                             'by a little, and the Quartermaster writes the '
                             'result in the book and reads it aloud, and does '
                             'not look at you while he does, which from him '
                             'is a whole conversation.',
                             sets=('vote_quiet',),
                             rep={'freeport': -8}),
                  ),
                  where='freeport'),
            Stage('settled', 'What the paper says now',
                  'The motion has been taken down and a new sheet is up, and '
                  'the new sheet is about something else, and the dockers '
                  'have moved on, and the bench record on the wall of the '
                  'mess still has a dead man\'s name on it, by vote.',
                  requires=('runs:9',),
                  any_of=('vote_spoke', 'vote_quiet'),
                  sets=('vote_settled',),
                  where='freeport'),
        )),

    # -- The Precinct: the surplus counter ----------------------------------
    Thread(
        'surplus', 'The Surplus Counter',
        'What was evidence last quarter is for sale this one, and some of it '
        'is yours.',
        crosses=('drawer', 'file'),
        stages=(
            Stage('sticker', 'Achebe mentions the counter',
                  'Sergeant Achebe does not look up. "The surplus counter has '
                  'a box. The box has a sticker. The sticker says surplus, '
                  'which is all any of the stickers say." He turns a page. '
                  '"It is the residue off four of your runs, bundled, with a '
                  'case number on it, and it is for sale, and I am telling '
                  'you because the alternative is not telling you."',
                  requires=('met:desk',),
                  any_of=('heat:30', 'runs:6'),
                  sets=('surplus_told',),
                  where='precinct'),
            Stage('posting', 'Carrion would like it gone',
                  'The posting comes from Carrion, which makes sense once you '
                  'read it: the evidence log behind the box is on a '
                  'Nightwatch network, and it has other people\'s residue in '
                  'it too, and some of those people pay Carrion.\n\n'
                  '[accent]Wipe[/], it says. It does not say which entries. '
                  'It does not have to.',
                  requires=('surplus_told',),
                  sets=('surplus_posting',),
                  posts=Posting(
                      patron='carrion', target='nightwatch', objective='wipe',
                      title='Case Closed',
                      blurb='Carrion want the evidence log behind the '
                            'surplus counter destroyed on a Nightwatch '
                            'network. Some of the residue in it is yours. '
                            'Some of it belongs to people who pay Carrion.',
                      label='the evidence log with your residue in it',
                      pay=3400),
                  where='precinct'),
            Stage('log', 'The log is open in front of you',
                  'Four of yours. Eleven of other people\'s, two of whom you '
                  'know by name. Each entry is a run described by somebody '
                  'who was not there, from what was left, and the '
                  'descriptions are good, and yours are better than you '
                  'would like.',
                  requires=('did:surplus.posting',),
                  sets=('surplus_log',),
                  choices=(
                      Choice('wipe', 'Wipe it and go',
                             'You wipe all fifteen. The box on the surplus '
                             'counter is still there the next time you pass, '
                             'with its sticker, and nobody can find the case '
                             'number it refers to, and after a week it is '
                             'sold as a box.',
                             sets=('surplus_wiped',),
                             rep={'nightwatch': -10, 'carrion': 12}),
                      Choice('read', 'Read yours first',
                             'You read yours before you wipe them. It takes a '
                             'while. Somebody at Nightwatch has understood '
                             'how you work better than most people who have '
                             'worked with you, and has written it down '
                             'without malice, and you wipe it, and you cannot '
                             'wipe having read it.',
                             sets=('surplus_read',),
                             rep={'nightwatch': -10, 'carrion': 12}),
                  ),
                  where='precinct'),
        )),

    # -- The Shambles: the cabinets ----------------------------------------
    Thread(
        'cabinets', 'The Referral Ledger',
        'Carrion want the Blue Surgeon\'s book, and the Surgeon shows it to '
        'anybody who asks.',
        crosses=('drawer', 'vance'),
        stages=(
            Stage('ask', 'A man from Carrion',
                  'He finds you by the cabinets. Carrion, unmistakably, and '
                  'polite about it. "The Surgeon keeps a referral ledger. '
                  'Every patient sent on, and where. We would like it." He '
                  'does not say why, and then he does: "Aoyama Green appear '
                  'in it rather a lot. We would like to be the people who '
                  'know that."\n\n'
                  'The Surgeon would show it to him if he asked. He knows '
                  'that. He would like it taken, because taken is a '
                  'different thing to shown.',
                  requires=('met:surgeon',),
                  any_of=('runs:4', 'drawer_clinic', 'vance_ask'),
                  sets=('cabinets_asked',),
                  choices=(
                      Choice('take', 'Take the ledger',
                             'You take it while the Surgeon is talking '
                             'through a procedure with the door open. It is '
                             'not difficult. Carrion pay, and are pleased, '
                             'and the Surgeon notices the next morning and '
                             'says nothing, and begins a new ledger, and '
                             'shows it to anybody who asks.',
                             sets=('ledger_taken',),
                             rep={'carrion': 18},
                             credits=2000),
                      Choice('warn', 'Tell the Surgeon',
                             '"Thank you." They do not stop washing their '
                             'hands. "I will show it to him. I show it to '
                             'everybody. He wanted it taken, which tells me '
                             'something about him, and you told me, which '
                             'tells me something about you, and I keep both."',
                             sets=('ledger_warned',),
                             rep={'carrion': -10}),
                  ),
                  where='shambles'),
            Stage('shown', 'Shown, not taken',
                  'The Carrion man is at the clinic counter being shown the '
                  'ledger, page by page, every entry in order, by somebody '
                  'who is enjoying it more than he is. Aoyama Green, Aoyama '
                  'Green, Aoyama Green. He leaves with nothing he did not '
                  'have and a great deal he cannot use.',
                  requires=('ledger_warned', 'runs:8'),
                  sets=('cabinets_shown',),
                  where='shambles'),
        )),

    # -- The Terraces: the allotment -----------------------------------------
    Thread(
        'allotment', 'Forty Trays',
        'Tomatoes on a Kagawa landing, against policy, for thirty-one years.',
        crosses=(),
        stages=(
            Stage('inspection', 'An inspection is coming',
                  'Mrs Adeyemi mentions it the way she mentions the third '
                  'plant doing badly. An inspection. Landings, all of them, '
                  'for fire compliance, which is what Kagawa call it when '
                  'they mean trays. "Thirty-one years," she says. "They have '
                  'inspected before. They have never inspected level forty. '
                  'Somebody has put level forty on the list."\n\n'
                  'She gives you a tomato. It is not a transaction.',
                  requires=('met:gardener',),
                  any_of=('runs:3', 'rep:kagawa:-20'),
                  sets=('trays_warned',),
                  where='terraces'),
            Stage('posting', 'The schedule is a record',
                  'The inspection schedule is on a Kagawa network, and a '
                  'posting says so, from the Switchboard, of all people. '
                  '[accent]Corrupt[/]: make the schedule have always said '
                  'something else. Mara does not explain why the Switchboard '
                  'cares about tomatoes, and the pay is low, and you suspect '
                  'it is her own money.',
                  requires=('trays_warned',),
                  sets=('trays_posting',),
                  posts=Posting(
                      patron='fixers', target='kagawa', objective='corrupt',
                      title='Landing Forty',
                      blurb='The Switchboard want the landing inspection '
                            'schedule on a Kagawa network to have always '
                            'skipped one level. It pays badly. Mara will not '
                            'say whose money it is.',
                      label='the landing inspection schedule',
                      pay=1800),
                  where='terraces'),
            Stage('schedule', 'Level forty is a line in a table',
                  'It is a line in a table. You can move it. You can also, '
                  'the schedule notes helpfully, flag a landing for priority, '
                  'which Kagawa pay a finder\'s fee for, because the '
                  'schedule was written by somebody who thought of that.',
                  requires=('did:allotment.posting',),
                  sets=('trays_schedule',),
                  choices=(
                      Choice('skip', 'Make the schedule skip level forty',
                             'The inspection never reaches level forty. It '
                             'reaches thirty-nine and forty-one and files '
                             'both, and the trays go on under a light '
                             'borrowed from a corridor, and Mrs Adeyemi gives '
                             'you a tomato, and it is still not a '
                             'transaction.',
                             sets=('trays_saved',),
                             rep={'fixers': 10}),
                      Choice('flag', 'Flag level forty for priority',
                             'You flag it. The finder\'s fee clears before '
                             'the inspection does. The landing is bare the '
                             'next time you pass, and clean, and compliant, '
                             'and Mrs Adeyemi says good evening to you '
                             'without checking who you are, because she has '
                             'four grandchildren and has stopped asking '
                             'things.',
                             sets=('trays_sold',),
                             rep={'kagawa': 12, 'fixers': -15},
                             credits=2500),
                  ),
                  where='terraces'),
        )),
    # -- The Stacks: the list (D64 b) ------------------------------------------
    Thread(
        'presses', 'The List',
        'Names, read out at the top of every hour, from a list nobody will '
        'say the source of.',
        crosses=('pumps', 'stoplist'),
        stages=(
            Stage('floor', 'Ines reads you the floor',
                  'Ines Vale walks you across the floor of the press room, '
                  'which is paper to the ankle, and stops, and points down '
                  'with the unlit cigarette. "Last Tuesday." A sheet under '
                  'the sheets. A list of names, in no order. "Top of every '
                  'hour, on the relay. We read it. We do not write it."\n\n'
                  'Third from the bottom is a handle. It is one you have used.',
                  requires=('met:printer',),
                  any_of=('runs:2', 'pumps_seen'),
                  sets=('presses_floor',),
                  where='stacks'),
            Stage('posting', 'Static want the stop list',
                  'Ines has a sheet for you, folded, which in the Stacks is '
                  'how a job arrives.\n\n'
                  '"Kagawa keep a list of what they have asked the Watch to '
                  'stop us printing. Forty items, we think. The ledger is on '
                  'it. So, we think, is the list of names, or where it comes '
                  'from. It is on a Kagawa network in the Vertical. We would '
                  'like it. We would like it wet."',
                  requires=('presses_floor',),
                  sets=('presses_posting',),
                  posts=Posting(
                      patron='static', target='kagawa', objective='exfiltrate',
                      title='Stop List',
                      blurb='Static want Kagawa\'s stop list out of a Vertical '
                            'network: everything Kagawa has asked the Watch to '
                            'keep off the presses, and, the Stacks think, where '
                            'the names on the relay come from.',
                      label='Kagawa\'s stop list',
                      pay=2900),
                  where='stacks'),
            Stage('edition', 'What goes to the presses',
                  'It is forty-one items. The maintenance ledger is on it. '
                  'So is a clinic in the Shambles, and a man\'s name you do '
                  'not know, and, at the bottom, a frequency, which is the '
                  'relay\'s, and a note beside it that says SOURCE: INTERNAL.\n\n'
                  'Kagawa write the list. Kagawa have been writing the list '
                  'of names the Stacks read out every hour, and the Stacks '
                  'have been reading it, and the names are people Kagawa '
                  'wanted read. Ines is waiting. So, by now, are Kagawa.',
                  requires=('did:presses.posting',),
                  sets=('presses_edition',),
                  choices=(
                      Choice('print', 'Give it to the presses',
                             'Ines reads it once, standing, and puts the '
                             'cigarette down on the table, which you have not '
                             'seen her do, and says, "Wet," and the presses '
                             'start.\n\n'
                             'The next morning\'s edition is the stop list, '
                             'all forty-one items, with the frequency at the '
                             'bottom and SOURCE: INTERNAL in the font. The '
                             'relay goes quiet for a day. Then it reads a new '
                             'list, and the first name on it is Ines Vale, '
                             'and she reads it herself.',
                             sets=('presses_printed',),
                             rep={'static': 25, 'kagawa': -20}),
                      Choice('hold', 'Keep it',
                             'You do not give it to Ines. You do not give it '
                             'to anybody. Forty-one items and a frequency is '
                             'the kind of thing that is worth more held than '
                             'printed, and you have read enough of the floor '
                             'to know what printed things become.\n\n'
                             'Ines looks at you for a long moment and lights '
                             'the cigarette. "Everybody keeps one," she says. '
                             '"I had hoped you would be the other kind." She '
                             'still takes your calls. She reads them back to '
                             'you, slightly wrong.',
                             sets=('presses_held',),
                             rep={'static': -10}),
                      Choice('sell', 'Sell it back to Kagawa',
                             'A man from the Vertical meets you in Marrow with '
                             'a case that is exactly heavy enough. He does not '
                             'ask how you got it. He asks whether anybody '
                             'has read it, and you say no, and he writes that '
                             'down.\n\n'
                             'The relay reads its list at the top of the next '
                             'hour, and the hour after, and a name on it is a '
                             'handle you have used, and it is higher than it '
                             'was.',
                             sets=('presses_sold',),
                             rep={'kagawa': 15, 'static': -30},
                             credits=2400),
                  ),
                  where='stacks'),
        )),

    # -- Meridian Row: the ledger's line (D64 b) -------------------------------
    Thread(
        'keys', 'The Ledger\'s Line',
        'A Meridian key, held by people who are not Meridian, for eleven '
        'years, and the very long line in the ledger that says so.',
        stages=(
            Stage('matter', 'The Notary states the matter',
                  'The Notary does not look up. "State the matter," they say, '
                  'and then, before you can, state it themselves.\n\n'
                  '"A Meridian key, held by Sendai, for eleven years. It '
                  'opens nothing any more. It is a key, and it is ours, and '
                  'the ledger has a line for it, and the line is very long." '
                  'The pen stops. "The ledger would like the line to end."',
                  requires=('met:notary',),
                  any_of=('runs:4', 'rep:meridian:10'),
                  sets=('keys_matter',),
                  where='row'),
            Stage('posting', 'Held',
                  'A courier finds you with a case that is not heavy enough. '
                  'Inside is a single sheet, printed on both sides in a type '
                  'that was designed to be unreadable at any distance, and '
                  'readable at none.\n\n'
                  'It is a posting. Meridian, against Sendai, for a key that '
                  'opens nothing. The fee is the kind of number Meridian '
                  'thinks is modest.',
                  requires=('keys_matter',),
                  sets=('keys_posting',),
                  posts=Posting(
                      patron='meridian', target='sendai', objective='exfiltrate',
                      title='Held',
                      blurb='Meridian want a key of theirs out of a Sendai '
                            'network, where it has been held for eleven years. '
                            'It opens nothing any more. That is not the point.',
                      label='a Meridian key',
                      pay=3600),
                  where='row'),
            Stage('held', 'The key, and the line',
                  'It is a key. Not a file that is a key: a key, a thing a '
                  'network recognises as permission, old enough that half '
                  'the city\'s doors would take it out of habit. It does not '
                  'open anything of Meridian\'s. It opens nearly everything '
                  'else, a little.\n\n'
                  'The Notary is waiting, in the sense that the Notary is '
                  'always there. So, you realise, is everybody who would '
                  'rather the line in the ledger did not end.',
                  requires=('did:keys.posting',),
                  sets=('keys_held',),
                  choices=(
                      Choice('return', 'Hand it over the counter',
                             'You put it on the counter. The Notary looks at '
                             'it, and then, for the first time, at you, and '
                             'draws a line through something in the ledger, '
                             'and the line is very long and the pen does not '
                             'lift.\n\n'
                             '"Noted." And then, which is not a word you '
                             'expected: "Thank you." The arrangement, when '
                             'it comes, comes through the same courier, with '
                             'the case the right weight.',
                             sets=('keys_returned',),
                             rep={'meridian': 30, 'sendai': -15}),
                      Choice('keep', 'Keep it',
                             'You do not go back to the Row. A key that opens '
                             'nearly everything a little is worth more in a '
                             'deck than on a counter, and Meridian can keep '
                             'their line.\n\n'
                             'The line does not end. It gets longer, and it is '
                             'yours now, and every so often a courier passes '
                             'you in the street with a case that is not heavy '
                             'enough and does not slow down.',
                             sets=('keys_kept',),
                             gives=('meridian_key',),
                             rep={'meridian': -35}),
                      Choice('static', 'Give it to the Stacks',
                             'Ines Vale turns it over in ink-stained fingers '
                             'and says, "We cannot print a key." And then: "We '
                             'can print what it opens." The next edition is a '
                             'list of doors, and the Row is the quietest it '
                             'has ever been, which is saying something.\n\n'
                             'The Notary does not look up when you pass the '
                             'counter hall. The Notary never did. It is '
                             'different now.',
                             sets=('keys_public',),
                             rep={'static': 20, 'meridian': -40, 'sendai': 10},
                             credits=1500),
                  ),
                  where='row'),
        )),

    # -- The Hall: the tin (D64 b) ---------------------------------------------
    Thread(
        'soup', 'The Tin',
        'Every name that ever put money in the Hall\'s tin, and the people '
        'who would like the list.',
        crosses=('listener', 'tin_debt'),
        stages=(
            Stage('kettle', 'The Cantor tells you about the tin',
                  'You are carrying the kettle again. The Cantor walks beside '
                  'you with the ladle and talks about Carrion the way he '
                  'talks about the weather.\n\n'
                  '"They want the donor list. Every name that has ever put '
                  'money in the tin. I have told them it is people. They '
                  'have told me that is what they want it for." He takes the '
                  'kettle. "They will ask somebody. They may ask you. I '
                  'wanted you to have heard it from me first."',
                  requires=('met:cantor',),
                  sets=('soup_kettle',),
                  where='hall'),
            Stage('tin', 'Carrion ask',
                  'They ask. Not in the queue: at the back of it, through a '
                  'man you half know, with a number that is good and a tone '
                  'that says the number is the polite part.\n\n'
                  '"The list. Off the Hall\'s machine. Wipe it so they cannot '
                  'find who to thank, and bring us the copy." The Cantor is '
                  'in the Hall, stirring. Forty people are on the platform. '
                  'The boards say a hymn.',
                  requires=('soup_kettle',),
                  any_of=('runs:3', 'rep:carrion:10', 'lark_dead'),
                  sets=('soup_asked',),
                  choices=(
                      Choice('stand', 'Tell the Cantor, and stand with the Hall',
                             'You tell him on the platform, with the kettle '
                             'between you. He does not stop stirring. "Thank '
                             'you," he says, and then, "Carrion stand at the '
                             'back. They will stand a bit closer now. We will '
                             'sing a bit louder."\n\n'
                             'He has a job for you, it turns out, if you want '
                             'it: watch the back of the queue, from inside '
                             'their network, and tell him what they are '
                             'going to do before they do it.',
                             sets=('soup_stood',),
                             rep={'chorus': 25, 'carrion': -20}),
                      Choice('carrion', 'Take Carrion\'s money',
                             'You take the number. The man you half know '
                             'nods, once, the way you nod at somebody who has '
                             'agreed to something you did not think they '
                             'would.\n\n'
                             'The Hall\'s machine is in the bell loft, under '
                             'the bell that does not ring. It is not '
                             'defended. It was never going to be.',
                             sets=('soup_carrion',),
                             rep={'carrion': 15, 'chorus': -30},
                             credits=600),
                      Choice('leave', 'Walk away from both',
                             'You say no to the man at the back and you do '
                             'not tell the Cantor, and you stop carrying the '
                             'kettle. The soup goes on. So does the standing '
                             'at the back.\n\n'
                             'A month later somebody else does it, one way or '
                             'the other. You hear about it. You do not ask '
                             'which.',
                             sets=('soup_left',)),
                  ),
                  where='hall'),
            Stage('watch', 'The back of the queue',
                  'The Cantor\'s job, through nobody: he hands you a sheet '
                  'himself, with the kettle. "Their network. Sit in it. Tell '
                  'me what they are going to do to us, and when. I will not '
                  'do anything about it. I would like to know."',
                  requires=('soup_stood',),
                  sets=('soup_watch',),
                  posts=Posting(
                      patron='chorus', target='carrion', objective='surveil',
                      title='The Back of the Queue',
                      blurb='The Chorus want eyes inside Carrion\'s network: '
                            'what they mean to do about the Hall, and when. '
                            'Nothing taken, nothing touched. Sit, and listen.',
                      pay=2200),
                  where='hall'),
            Stage('wipe', 'The tin, wiped',
                  'Carrion\'s posting arrives the usual way, folded, through '
                  'the man you half know. The Hall\'s machine. The list. '
                  'Wipe it, bring the copy, and do not be seen by forty '
                  'people who would recognise you, because you have carried '
                  'the kettle.',
                  requires=('soup_carrion',),
                  sets=('soup_wipe',),
                  posts=Posting(
                      patron='carrion', target='chorus', objective='wipe',
                      title='The Tin',
                      blurb='Carrion want the Hall\'s donor list wiped off the '
                            'Chorus machine, and a copy brought out first. '
                            'Every name that ever put money in.',
                      label='the Hall\'s donor list',
                      pay=2600),
                  where='hall'),
            Stage('told', 'What you heard',
                  'You tell the Cantor on the platform, with the kettle '
                  'between you, what Carrion mean to do and when. He listens '
                  'the whole way through without stirring, which you have '
                  'never seen, and then stirs.\n\n'
                  '"Thank you." He does not say what he will do. He said he '
                  'would not do anything. The singing that night is the '
                  'loudest you have heard it, and the two at the back have '
                  'gone, and the next morning there are four.',
                  requires=('did:soup.watch',),
                  sets=('soup_told',),
                  where='hall'),
            Stage('wiped', 'The tin, after',
                  'The Hall\'s machine does not know who to thank. The copy '
                  'is with Carrion, who know exactly who to thank, and will.'
                  '\n\nThe soup is there in the morning and the queue is the '
                  'length of the platform and the Cantor hands you the '
                  'kettle, because you are standing there and it needs '
                  'carrying, and does not look at you while he does it, and '
                  'that is the whole of what he says.',
                  requires=('did:soup.wipe',),
                  sets=('soup_wiped',),
                  where='hall'),
        )),

)


# --------------------------------------------------------------------------
# the other runners, at the moment they decide (D56)
# --------------------------------------------------------------------------
#
# D44 gave every rival an arc: a bond that latches at either end, announces
# itself once, and acts on the shift boundary for the rest of the campaign.
# What it did not give the player was a say. These are the fourteen moments,
# one per runner per side, where the bond becomes a conversation: somebody
# has decided you are a colleague and says what that could mean; somebody
# has decided you are weather and names what it costs to stop. Two answers
# each, and the world reads both.

#: (rival key, name, partner scene, in, apart, nemesis scene, pay, stand)
_RUNNER_SCENES = (
    ('vesper', 'Vesper Okonkwo',
     'Vesper Okonkwo introduces you as a colleague, which from her is a '
     'technical term with a great deal of machinery behind it, and then, over '
     'a drink she pays for, says the machinery is available. "I do not do '
     'this. I am doing it. There is work I cannot be seen near, and you can."',
     'You say yes. The machinery moves about a week later: a door that stays '
     'open, a patron who was not going to think of you, a fee that is smaller '
     'than it should be and arrives on time.',
     'You say you would rather keep it clean. She nods, exactly as warm, and '
     'the machinery does not move, and she introduces you as a colleague for '
     'the rest of your career, and means it slightly less.',
     'Vesper Okonkwo is extremely warm about you in public and has stopped '
     'returning anything in private, and three people who used to take your '
     'calls now take a beat. Then a note, through Mara, who does not look up: '
     'there is a figure at which it stops.',
     'You pay the figure. It is not small. The three people take your calls '
     'on the first ring again, and Vesper is warm in public and says nothing '
     'in private, which is the arrangement, and it holds.',
     'You do not pay. The beat before people answer gets longer. You learn '
     'which patrons she has talked to by who stops posting, and you learn it '
     'slowly, which is how she wanted it.'),
    ('hound', 'Hound',
     'Hound tells a bar, loudly, that you are the only person in this city '
     'who has never let them down, and then, quieter, at the bar, that they '
     'would like that to stay true, and that it would be easier if you were '
     'on the same jobs.',
     'Hound is on the next three jobs you take, uninvited, breaking things in '
     'front of you, and the noise is enormous and it is, you notice, always '
     'somewhere else.',
     'You tell Hound you work alone. They say that is fine about six times, '
     'at volume, and it is fine, and they are still loud about you in rooms '
     'you are not in, and you are not sure which you would have preferred.',
     'Hound has started saying your name in rooms you are not in, the way you '
     'would name a weather event. Then, in a room you are in: "It can stop. I '
     'am not unreasonable. I am expensive."',
     'You pay Hound. They stop. They are loud about how they stopped, which '
     'is a different problem, and a smaller one.',
     'You do not pay. Hound is loud about you for a year, in rooms you are '
     'not in, and then in one you are, and nothing comes of it except that '
     'everybody knows your name, and not in the way that helps.'),
    ('quietkid', 'The Quiet Kid',
     'A file drop. No sender. It is a route into something you were going to '
     'need a route into, and under it, one line: with you, if you want. no '
     'need to answer.',
     'You do not answer. You use the route. Another arrives the next week. '
     'You have never met the Quiet Kid and there is a reasonable argument '
     'that you are now partners.',
     'You drop one line back: no. Nothing arrives the next week. Nothing '
     'arrives ever again, and the Quiet Kid takes the work you were looking '
     'at, slightly before you look at it, exactly as before.',
     'You notice, over about a fortnight, that the Quiet Kid is where you '
     'were going to be, slightly before you get there. Then a file drop, no '
     'sender, one line and a number: the number is what it costs to stop '
     'noticing.',
     'You pay the number. The Quiet Kid is not where you were going to be. '
     'You never see them again, which, with the Quiet Kid, is what the '
     'arrangement was always going to look like.',
     'You do not pay. The Quiet Kid is where you were going to be, for the '
     'rest of it, slightly before, and never once in a way you could point '
     'at.'),
    ('saint', 'Saint Ambrose',
     'Saint Ambrose keeps a channel open to you, and says so, slightly too '
     'slowly, as though translating. "It is not comfortable. It means that at '
     'three in the morning somebody already knows. I would like it to be you '
     'who knows, when it is me."',
     'You keep the channel. It is not comfortable. At three in the morning, '
     'twice, somebody already knows, and once it is you.',
     'You close it. He does not argue; he answers a question you have not '
     'asked yet, which is "yes, that is wise", and the latency artefact, for '
     'once, is in the right direction.',
     'Saint Ambrose has not decided anything about you. A decision was made '
     'somewhere in the stack that runs him now and he is carrying it out with '
     'the same evenness he carries out everything. He tells you, slightly too '
     'slowly, that the stack accepts payment.',
     'You pay the stack. Whatever was decided is undecided, evenly, and Saint '
     'Ambrose answers a question you have not asked, which is "no, I do not '
     'remember why."',
     'You do not pay. He carries it out evenly for the rest of your career, '
     'and is perfectly courteous about it, and once, at three in the morning, '
     'you are fairly sure he is sorry.'),
    ('ledger', 'Ledger',
     'Ledger has run the numbers on you one more time and come back with a '
     'conclusion they are willing to act on, which from Ledger is the loudest '
     'thing that has ever happened. "One job a month. Two, if the second is '
     'yours. I would like the second to be yours."',
     'You take Ledger\'s second job each month. They have done a fortnight '
     'of legwork you did not do, every time, and it has never once failed, '
     'and you are aware of how much that is costing them.',
     'You say no. Ledger says that is correct, and gives two reasons you had '
     'not thought of, and you feel worse rather than better, which is also '
     'correct.',
     'Ledger has filed you. Not with anybody. With themselves, accurately. '
     'They tell you so, because not telling you would be inaccurate, and they '
     'tell you the file can be closed, and what closing costs.',
     'You pay to close it. Ledger closes it, and it stays closed, because '
     'Ledger has never once failed to do a thing they said they would do, '
     'and that is what you were paying for.',
     'You do not pay. The file stays open and accurate, and every so often a '
     'patron asks you a question that is exactly the right question, and you '
     'know whose question it was.'),
    ('moth', 'Moth',
     'Moth tells a bar, loudly, that you are the only person in this city who '
     'has never let them down, and Moth is nineteen, and the bar has done the '
     'arithmetic, and looks at you.',
     'You take Moth on the next one. They are brilliant and they are fast and '
     'they nearly die twice in eleven ticks, and you get them out, and they '
     'are insufferable about it for a week, and alive.',
     'You tell Moth no. They say that is fine, at volume, and take something '
     'above their level the next day because nobody told them not to, and '
     'you hear about it, and it was fine, this time.',
     'Moth has started saying your name in rooms you are not in, and Moth is '
     'nineteen, and saying it badly, and the rooms are laughing at Moth and '
     'not at you, which Moth has not noticed. Then Moth names a figure, too '
     'high, with a straight face.',
     'You pay Moth the figure. Moth is delighted, and is loud about that '
     'instead, and spends it in a week, and is nineteen.',
     'You do not pay. Moth keeps saying your name badly in rooms, and then '
     'takes something above their level to prove a point, and the point is '
     'not proved, and you hear about it later than you should have.'),
    ('grieve', 'Grieve',
     'Grieve leaves something where you will find it: a name, the hour it '
     'works, the desk it reports to. Nothing is said about it. Grieve used to '
     'hunt every other name on that list, and has decided not to hunt yours, '
     'and this is how that is said.',
     'You use the name. More arrive, at intervals, never announced. You never '
     'discuss it with Grieve and Grieve never discusses it with you, and it '
     'is the most reliable thing in your career.',
     'You leave the name where it was. Grieve notices, because Grieve notices '
     'everything, and leaves nothing else, and treats every conversation with '
     'you as an interview again, and is very tired.',
     'Grieve is where you were going to be, slightly before, and Grieve used '
     'to do this for a living. There is no offer. You make one, and Grieve '
     'listens to the whole of it with the tired attention of an interviewer, '
     'and names a figure that is exactly fair.',
     'You pay Grieve. They stop. There is no announcement and no warmth; they '
     'are simply somewhere else, and you are aware, afterwards, of how good '
     'they were.',
     'You do not pay. Grieve hunts you the way Grieve hunted everybody, '
     'professionally, patiently, and without apparent interest, and is the '
     'only nemesis you will ever have who files the reports.'),
)

#: What buying a nemesis off costs. One number for all seven, because the
#: figure is "exactly fair" and fairness does not vary by who is asking.
BUYOFF = 2500


#: Threads that sit beside a district's own (D65 depth): a second story in
#: a place that already has one. Merged into `threads.THREADS` with the rest.
MORE_THREADS: tuple[Thread, ...] = (
    # -- The city at leisure (D177) ------------------------------------------
    # Four long threads for after the main arcs, or instead of them: the
    # Terraces, the Row, the Stacks and Freeport, each on people the story
    # had barely used, each with a job in the middle of it and a decision
    # that the district remembers. They open on a career (twelve runs) or
    # on the water being settled, whichever comes first.
    Thread(
        'towers', 'The Water Towers',
        'The hill drinks by gravity, and Kagawa has started counting it.',
        stages=(
            Stage('cans', 'The third can',
                  'The Widow at the water point has two cans and a third she '
                  'is filling for somebody else, as always, and today the '
                  'third one takes longer, because the pressure on the '
                  'upper levels is a thing Kagawa has started to meter. She '
                  'says so without complaint, which is how she says '
                  'everything. "It used to come down the hill because that '
                  'is what water does. Now it comes down the hill because '
                  'somebody in the Vertical has decided how much."',
                  requires=('met:widow',),
                  any_of=('runs:12', 'after_settled'),
                  sets=('towers_cans',),
                  where='terraces'),
            Stage('planters', 'Level forty',
                  'Mrs Adeyemi is watering the far end of her walkway from '
                  'a jug she has carried up forty levels, because the tap '
                  'on forty gives a cupful an hour now and the planters at '
                  'the far end are the ones her grandchildren planted. She '
                  'does not ask you for anything. She tells you which ones '
                  'are dying, by name, and then says good evening.',
                  requires=('towers_cans', 'met:gardener'),
                  sets=('towers_planters',),
                  after=1,
                  where='terraces'),
            Stage('board', 'The board has changed',
                  'The Man With The Board has repainted it. It reads THE '
                  'WATER IS A PLACE AND YOU ARE IN IT, which is, for once, '
                  'not technically correct so much as correct. He tells the '
                  'shift-change crowd that the valve house under the towers '
                  'has a network in it now, Kagawa\'s, and that a network '
                  'is a door, and that a door is a thing somebody opens. '
                  'The crowd does not listen. You do.',
                  requires=('towers_planters', 'met:preacher'),
                  sets=('towers_board',),
                  after=1,
                  where='terraces',
                  choices=(
                      Choice('listen', 'Ask him where the valve house is',
                             'He tells you, precisely, with the air of a man '
                             'who has been waiting years for somebody to ask '
                             'a follow-up question, and then paints a small '
                             'arrow on the board. "So they know somebody '
                             'asked," he says. "It helps them to know."',
                             sets=('towers_told',)),
                      Choice('move', 'Move him on',
                             'You tell him the crowd is Kagawa\'s crowd and '
                             'the board is going to get him hurt, and he '
                             'folds it under his arm and thanks you, '
                             'technically, and goes. Somebody in a Kagawa '
                             'lanyard nods at you from across the square. '
                             'You had not known they were there.',
                             sets=('towers_moved',),
                             rep={'kagawa': 4}),
                  )),
            Stage('meter', 'The metering schedule',
                  'The Sixes want it. Of course they do: the Terraces are '
                  'Kagawa\'s roof and the Sixes\' street, and a schedule '
                  'that says who gets water when is a schedule that says '
                  'who is owed what. It comes through the board as a job '
                  'like any other, against the valve house, and the pay is '
                  'the kind that tells you somebody has priced the hill.',
                  requires=('towers_board',),
                  any_of=('towers_told', 'towers_moved'),
                  sets=('towers_meter',),
                  after=1,
                  where='terraces',
                  posts=Posting('sixes', 'kagawa', 'corrupt', 'The Meter',
                                'The valve house under the water towers. Kagawa put a '
                                'network in it and a schedule on the network. The Sixes '
                                'want the schedule changed, and do not much mind how.',
                                label='the metering schedule', pay=2200)),
            Stage('valve', 'What the schedule is for',
                  'You have it: the schedule, the valves, the whole slow '
                  'arithmetic of the hill\'s water, in a file you could '
                  'change with one line. The Sixes are paying for the line '
                  'they want. Kagawa would pay for it back. Meridian would '
                  'pay for the file, because Meridian pay for anything '
                  'that says who owes whom. And the far end of level forty '
                  'is a cupful an hour.',
                  requires=('did:towers.meter',),
                  sets=('towers_valve',),
                  where='terraces',
                  choices=(
                      Choice('open', 'Open the hill',
                             'You change the line the Sixes did not ask for: '
                             'the one that meters level forty. The pressure '
                             'comes back to the upper levels the way it used '
                             'to, because that is what water does, and '
                             'Kagawa notice in about four shifts, and the '
                             'Sixes notice in one, and are pleased, and do '
                             'not ask what else you changed.',
                             sets=('towers_opened',),
                             rep={'sixes': 8, 'kagawa': -10}),
                      Choice('sell', 'Sell the file to Meridian',
                             'The Row pays what the Row pays, which is more '
                             'than the job, and asks nothing, and files it. '
                             'Somewhere a ledger has the hill\'s water in '
                             'it now, priced, and the metering does not '
                             'change, and the planters do not either.',
                             sets=('towers_sold',),
                             credits=3500,
                             rep={'meridian': 6}),
                      Choice('return', 'Give it back to Kagawa, fixed',
                             'You return it with the fault they did not know '
                             'they had corrected: the schedule had forty '
                             'levels in it and the towers only ever fed '
                             'thirty-eight. A compliance officer thanks you '
                             'with profound apology. The pressure on forty '
                             'improves by the exact amount the arithmetic '
                             'says, which is some.',
                             sets=('towers_returned',),
                             rep={'kagawa': 10}),
                  )),
            Stage('forty', 'The far end of the walkway',
                  'Mrs Adeyemi is on the walkway with the jug, or without '
                  'it, depending on what you did with the file, and the '
                  'planters at the far end are alive or are not, and she '
                  'says good evening to you the same way in either case, '
                  'because that is who she is. She names the ones her '
                  'grandchildren planted. Some of the names have changed.',
                  requires=('towers_valve',),
                  any_of=('towers_opened', 'towers_sold', 'towers_returned'),
                  sets=('towers_forty',),
                  after=4,
                  where='terraces'),
            Stage('third_can', 'The third can',
                  'The Widow is at the water point with two cans and a '
                  'third, and the third one fills at whatever speed the '
                  'hill\'s water comes down at now, and she does not say '
                  'what it was like before, because she never does. She '
                  'looks at you the way she looks at somebody who might '
                  'carry something, and this time you do: the third can, '
                  'up forty levels, to a door you do not knock on.',
                  requires=('towers_forty',),
                  sets=('towers_done',),
                  after=3,
                  where='terraces'),
        )),
    Thread(
        'valuation', 'The Valuation',
        'The Row has a line with your name in it, and the number is not a bounty.',
        stages=(
            Stage('line', 'A line in the ledger',
                  'The Notary does not look up when you come in and does '
                  'not look up when you ask, and turns the ledger round so '
                  'you can read it, which is a thing the Row does not do. '
                  'Your name. A number beside it that is not a bounty, '
                  'because a bounty is what somebody will pay to find you, '
                  'and this is what somebody would pay to have you. "A '
                  'valuation," the Notary says, to the ledger. "Everybody '
                  'who has run twelve jobs has one. Most of them never '
                  'ask."',
                  requires=('met:notary',),
                  any_of=('runs:12', 'after_settled', 'credits:8000'),
                  sets=('val_line',),
                  where='row'),
            Stage('sold', 'Vig has sold it',
                  'Marek Vig, under the colonnade, greets you by the '
                  'number. He has sold it three times this week, to three '
                  'people who wanted to know what you would cost, and he '
                  'says so with the openness of a man who does not think '
                  'of it as yours. "It is a fact about the city," he says. '
                  '"I sell facts about the city. The fact that you exist '
                  'was mine before it was yours."',
                  requires=('val_line', 'met:vig'),
                  sets=('val_vig',),
                  after=1,
                  where='row'),
            Stage('sunday', 'Mr Sunday makes an offer',
                  'Mr Sunday has the stool next to yours and has been '
                  'talking for a while, and the talk is about your line. '
                  'He will buy it. Not you: the line, the number, the '
                  'right to be the one who sells the fact of you. He names '
                  'a figure that is exactly the valuation, which is either '
                  'a joke or the most honest thing anybody has said to you '
                  'on the Row.',
                  requires=('val_vig', 'met:broker'),
                  sets=('val_sunday',),
                  after=1,
                  choices=(
                      Choice('buy', 'Buy your own line',
                             'You buy it. The Notary writes your name in the '
                             'column for who holds the line, beside the '
                             'column for whose name is on it, and for the '
                             'first time in the Row\'s history the two '
                             'columns match. Vig cannot sell it any more. '
                             'He seems to find that funny.',
                             sets=('val_owned',),
                             credits=-4000),
                      Choice('let', 'Let it stand',
                             'You let it stand. Somebody holds your line and '
                             'it is not you and it never was, and Vig goes '
                             'on selling the fact of you at a fair price, '
                             'and you go on being worth what the ledger '
                             'says, which changes a little every shift, and '
                             'which you check, now, sometimes, on the way '
                             'past.',
                             sets=('val_let',)),
                      Choice('wipe', 'Find the network the ledger lives on',
                             'The Row is stone and glass and silence, and '
                             'somewhere under it a network holds the ledger, '
                             'because nothing this century is held anywhere '
                             'else. Static know where. Static would very '
                             'much like a line in Meridian\'s ledger to go '
                             'missing, and do not mind that the first one '
                             'is yours.',
                             sets=('val_wipe',)),
                  )),
            Stage('ledger', 'The line, from the inside',
                  'It comes through the board with Static\'s name on it '
                  'and Meridian\'s as the target, which is a thing you '
                  'have not seen before, and the pay is real, because '
                  'Static have decided that a line that can be wiped is a '
                  'ledger that can be doubted, and doubt is what they '
                  'publish.',
                  requires=('val_wipe',),
                  sets=('val_posting',),
                  after=1,
                  where='row',
                  posts=Posting('static', 'meridian', 'wipe', 'The Line',
                                'The Row\'s ledger, on the Row\'s own network. Static '
                                'want one line gone, and they want it to be yours, '
                                'so that the next person who asks finds nothing.',
                                label='your valuation', pay=3000)),
            Stage('cleared', 'The Notary looks up',
                  'The Notary looks up. Nobody has told you what that '
                  'costs the Row, but the Notary looks up, at you, for '
                  'about a second, and then turns the ledger round, and '
                  'your line is not in it. "There is a column for people '
                  'who are not in the ledger," the Notary says. "It is '
                  'shorter than you would think. It is not empty."',
                  requires=('did:valuation.ledger',),
                  sets=('val_cleared',),
                  after=1,
                  where='row'),
            Stage('worth', 'What you are worth',
                  'A valuation is what somebody would pay to have you, and '
                  'the Row keeps one for everybody who has run twelve '
                  'jobs, and most people never ask, and you did. Whether '
                  'you hold it, or let it stand, or took it out of the '
                  'book, the number went on changing a little every shift, '
                  'because that is what a number does in a city. What '
                  'changed is that you know it is there, and Vig knows you '
                  'know, and greets you by the handle now.',
                  requires=('val_sunday',),
                  any_of=('val_owned', 'val_let', 'val_cleared'),
                  sets=('val_worth',),
                  after=4,
                  where='row'),
        )),
    Thread(
        'edition', 'The Second Edition',
        'Everything in the Stacks is printed twice. The second edition is you.',
        stages=(
            Stage('proof', 'A proof, with your name in the headline',
                  'Ines Vale has ink to the elbow and a proof on the '
                  'stone, and she turns it so you can read it, and it is '
                  'you. Not the handle. The other name, the one the city '
                  'uses ({called}), in the headline, and under it four '
                  'columns of everything you have done that anybody saw. '
                  '"Second edition," she says. "Everybody who runs long '
                  'enough gets one. The first was the one the city told '
                  'itself. This is the one it will keep."',
                  requires=('met:printer',),
                  any_of=('runs:12', 'after_settled'),
                  sets=('ed_proof',),
                  where='stacks'),
            Stage('dishes', 'Pip reads the dishes',
                  'Pip comes down a ladder with no bottom rungs and tells '
                  'you which dish the galley file went out on, because Pip '
                  'reads the dishes the way other children read weather. '
                  'Static keep the file on a relay in a tower, and the '
                  'tower has a network, and Pip has a route up the outside '
                  'of it that does not involve the network at all.',
                  requires=('ed_proof', 'met:pip'),
                  sets=('ed_dishes',),
                  after=1,
                  where='stacks',
                  choices=(
                      Choice('climb', 'Let Pip take you up',
                             'You go up the outside of the tower behind an '
                             'eleven-year-old, forty metres, in wind, and at '
                             'the top Pip points at a dish and says "that '
                             'one" with enormous satisfaction, and you can '
                             'see the whole Vertical, and you are not going '
                             'to be able to explain this to anybody.',
                             sets=('ed_climbed',)),
                      Choice('pay', 'Pay Pip to say which',
                             'Pip takes the money seriously, counts it, and '
                             'says which dish, and which relay, and what '
                             'hour the file goes out, and then, unprompted, '
                             'what the Vertical is doing this hour, because '
                             'that comes free.',
                             sets=('ed_paid',),
                             credits=-200),
                  )),
            Stage('relay', 'The galley file',
                  'The Sixes want the second edition changed before it '
                  'prints, because it has a paragraph about the Ninth in '
                  'it that is true, and it comes through the board as a '
                  'job against the relay, and the pay is what the Sixes '
                  'pay for the truth, which is generous.',
                  requires=('ed_dishes',),
                  any_of=('ed_climbed', 'ed_paid'),
                  sets=('ed_relay',),
                  after=1,
                  where='stacks',
                  posts=Posting('sixes', 'static', 'corrupt', 'The Second Edition',
                                'Static\'s relay in the Stacks, and the galley file on it: '
                                'the second edition of you, set and waiting. The Sixes '
                                'want a paragraph changed. Which one is yours to find out.',
                                label='the galley file', pay=2600)),
            Stage('galley', 'Set in type',
                  'You have the galley: your second edition, in type, '
                  'every line of it, and the cursor where the Sixes want '
                  'the paragraph about the Ninth to say something else. '
                  'Ines Vale would print whatever comes back. That is her '
                  'whole ethic. What comes back is yours to decide, and it '
                  'is the only time you will ever get to.',
                  requires=('did:edition.relay',),
                  sets=('ed_galley',),
                  where='stacks',
                  choices=(
                      Choice('correct', 'Correct it, and only it',
                             'You fix the three things that were wrong, and '
                             'leave the paragraph about the Ninth, and leave '
                             'everything else, and it prints, and it is '
                             'true, and the Sixes are not pleased and do not '
                             'say so, because it is true.',
                             sets=('ed_corrected',),
                             rep={'static': 8, 'sixes': -6}),
                      Choice('kill', 'Pull the plate',
                             'You corrupt the file the way the job says, '
                             'and then a little more, and the second '
                             'edition does not print, and somebody who did '
                             'not want it to pays you for that in an '
                             'envelope with no name on it. Ines Vale prints '
                             'a blank page where it would have been. She '
                             'does that on purpose.',
                             sets=('ed_killed',),
                             credits=1500,
                             rep={'static': -10}),
                      Choice('print', 'Let it run as it is',
                             'You change the one paragraph the Sixes are '
                             'paying for and nothing else, and it prints, '
                             'and it is mostly true, and you are the one '
                             'person in the city who knows which paragraph '
                             'is not, and that is a kind of authorship.',
                             sets=('ed_printed',),
                             rep={'static': 4, 'sixes': 4}),
                  )),
            Stage('printed', 'Off the presses',
                  'It comes off the presses in the morning, or a blank page '
                  'does, and either way the Stacks read it, because the '
                  'Stacks read everything twice and believe it once. Ines '
                  'Vale does not comment. Pip reads it aloud from a tower '
                  'to nobody. Somewhere in it or not in it is the name the '
                  'city uses for you ({called}), in type, which is a '
                  'thing you cannot take back.',
                  requires=('ed_galley',),
                  any_of=('ed_corrected', 'ed_killed', 'ed_printed'),
                  sets=('ed_done',),
                  after=3,
                  where='stacks'),
            Stage('shelf', 'A copy in Marrow',
                  'There is a copy on a shelf in the back bar in Marrow, '
                  'or there is a blank page there, folded, which Osei keeps '
                  'for the same reason. People who have read it look at '
                  'you a certain way. People who have not, do not. You can '
                  'tell which is which now, from the door, which is a '
                  'thing the second edition gave you that the first one '
                  'did not.',
                  requires=('ed_done',),
                  sets=('ed_shelf',),
                  after=4),
        )),
    Thread(
        'crane', 'The Crane\'s Name',
        'The newest crane was named by a vote, and the name that won was a runner\'s.',
        stages=(
            Stage('lunch', 'The name that won',
                  'Teku eats lunch on the base of the newest crane with '
                  'her back against the name that won the vote, and tells '
                  'you whose it was: a runner, dead, who had never been to '
                  'the docks, whose name the dockers knew from a story '
                  'about a job that went wrong in a way that helped them. '
                  '"We do not name cranes after people who help us," she '
                  'says. "We named one. Carrion locked its control the '
                  'week after, out of spite, and it has not lifted since."',
                  requires=('met:crane',),
                  any_of=('runs:12', 'after_settled'),
                  sets=('crane_lunch',),
                  where='freeport'),
            Stage('bollard', 'Old Pike on the lock',
                  'Old Pike sits on his bollard and watches the crane not '
                  'lift, and when you ask, he tells you what is on the '
                  'lock: his. The ICE they named after him, the one he '
                  'built for Sendai before Sendai sold it on, sitting on a '
                  'crane\'s control network because Carrion bought it '
                  'second-hand. "It thinks the way I thought," he says. "I '
                  'can tell you how I thought. I am not sure that helps."',
                  requires=('crane_lunch', 'met:pike_sr'),
                  sets=('crane_pike',),
                  after=1,
                  where='freeport'),
            Stage('lock', 'The lock',
                  'Freeport post it themselves, which the docks never do: '
                  'a job against Carrion, on their own board, in their own '
                  'name, to wipe the lock off a crane that has a dead '
                  'runner\'s name on it. The pay is a collective\'s pay, '
                  'which is fair and no more, and everybody on the quay '
                  'knows you took it before you have.',
                  requires=('crane_pike',),
                  sets=('crane_lock',),
                  after=1,
                  where='freeport',
                  posts=Posting('freeport', 'carrion', 'wipe', 'The Lock',
                                'A crane\'s control network on the Freeport quay, with '
                                'Carrion\'s lock on it and Old Pike\'s ICE on the lock. '
                                'The docks want it lifting again.',
                                label='the lock on the crane', pay=3000)),
            Stage('name', 'Whose name',
                  'The crane lifts. Teku drives it the first time with the '
                  'whole quay watching and nobody saying anything, which '
                  'is how the docks cheer. Afterwards the quartermaster '
                  'says, in the tone of a motion, that a crane that has '
                  'been unlocked could be renamed, if the docks wanted, '
                  'and that the docks had been discussing it, and looks at '
                  'you.',
                  requires=('did:crane.lock',),
                  sets=('crane_name',),
                  where='freeport',
                  choices=(
                      Choice('keep', 'Keep the dead runner\'s name',
                             'You say the name that won is the name, and '
                             'the quay agrees in the way it agrees, by not '
                             'disagreeing, and Teku eats her lunch against '
                             'it the next day with her back to it, as '
                             'before. Something on the quay has decided '
                             'about you. It is not the crane.',
                             sets=('crane_kept',),
                             rep={'freeport': 6}),
                      Choice('yours', 'Your own',
                             'They paint it in the night, the way the docks '
                             'do things they are not sure about: the name '
                             'the city uses for you ({called}), on a crane, '
                             'in letters a metre high, facing the water. '
                             'You will never be able to leave. You will '
                             'never have to.',
                             sets=('crane_yours',),
                             rep={'freeport': 2}),
                      Choice('pike', 'Old Pike\'s',
                             'You say the man who built the lock should have '
                             'the crane, and the quay is quiet for long '
                             'enough that you think you have misjudged it, '
                             'and then Teku says "yes" from the cab, once, '
                             'and it is done. Old Pike does not watch the '
                             'painting. He watches the crane lift.',
                             sets=('crane_pike_named',),
                             rep={'freeport': 4}),
                  )),
            Stage('painted', 'A metre high, facing the water',
                  'The name is on the crane, whichever name, in letters a '
                  'metre high facing the water, where the ships see it '
                  'first. The docks do not talk about it. The docks talk '
                  'about the crane, which lifts, and about the lock, which '
                  'is gone, and about Carrion, who have noticed, and have '
                  'people on the quay again, and are not lifting anything.',
                  requires=('crane_name',),
                  any_of=('crane_kept', 'crane_yours', 'crane_pike_named'),
                  sets=('crane_painted',),
                  after=3,
                  where='freeport'),
            Stage('harness', 'Lunch on the base',
                  'Teku eats lunch on the base of the crane with her back '
                  'against the name, and nods at you the way she did the '
                  'first time, and says nothing, and the crane lifts '
                  'something over the two of you that weighs more than '
                  'the building you live in, and neither of you looks up. '
                  'That is what the docks are. You have stopped noticing '
                  'that you belong to them.',
                  requires=('crane_painted',),
                  sets=('crane_done',),
                  after=4,
                  where='freeport'),
        )),

    # -- Subplots for the systems the story predates (D172) ------------------
    # The animal, the construct, the names and the door all arrived after
    # the threads were written. Each of these reads one of them through a
    # rule the engine did not have (`pet:`, `familiar:`, `titles:`), and
    # the prose carries `{pet}` or `{familiar}` for the world to fill.
    Thread(
        'stray', 'The Thing You Keep',
        'Somebody says the animal was theirs.',
        stages=(
            Stage('claimed', 'Somebody says it was theirs',
                  'Tuck asks after {pet} by name, which you did not know Tuck '
                  'knew, and then says the thing he came to say: a kid from '
                  'the wet end of the Ninth has been asking about an animal '
                  'that went missing about when yours stopped being a stray. '
                  '"I am not saying it is theirs. I am saying they think so, '
                  'and that they have been sleeping outside your door, and '
                  'that it is cold."',
                  requires=('pet:kept:12', 'met:tuck'),
                  sets=('stray_claimed',),
                  where='ninth',
                  choices=(
                      Choice('give', 'Let them have it',
                             'You carry {pet} down to the wet end yourself. '
                             'The kid does not say thank you, which is right; '
                             'it was theirs. The flat is a flat again. Tuck '
                             'does not mention it, and stands you a drink '
                             'without saying what for.',
                             sets=('stray_given',),
                             rep={'sixes': 6}),
                      Choice('keep', 'Keep it',
                             'You say it is yours now, which is also true, and '
                             'the kid stops sleeping outside your door after '
                             'three nights and starts sleeping outside Tuck\'s '
                             'instead. {pet} does not know any of this. That '
                             'is the point of {pet}.',
                             sets=('stray_kept',),
                             rep={'sixes': -6}),
                      Choice('pay', 'Pay them for it',
                             'You give the kid what an animal costs at a '
                             'market, and then again, because the first one '
                             'was the animal and the second one is for the '
                             'nights outside the door. They take it. Tuck '
                             'watches you do it and says nothing, which from '
                             'Tuck is a review.',
                             sets=('stray_paid',),
                             credits=-400),
                  )),
            Stage('kept', 'Whose it is',
                  'The animal is on the warm part of the deck when you come '
                  'in, or is not, and either way the question of whose it '
                  'was has stopped being asked in the Ninth, because the '
                  'Ninth has other questions. Tuck asks after it by name '
                  'now and then. You have stopped noticing that he does.',
                  requires=('stray_claimed',),
                  any_of=('stray_given', 'stray_kept', 'stray_paid'),
                  sets=('stray_settled',),
                  after=3,
                  where='ninth'),
            Stage('toy', 'The one thing it plays with',
                  'The kid from the wet end sees the toy through the door, '
                  'the one thing {pet} plays with, and stands there longer '
                  'than the cold makes sense of. Tuck, later: "They had one '
                  'for it. Not that one. Same idea." He does not say what '
                  'happened to it. Nobody in the Ninth ever says what '
                  'happened to a thing; they say what it was.',
                  requires=('stray_settled', 'pet:toy'),
                  sets=('stray_toy',),
                  after=2,
                  where='ninth'),
            Stage('ill', 'Off its food',
                  '{Pet} is off its food, and then off its water, and then '
                  'off the warm part of the deck, which is the one that '
                  'tells you. The clinic will not see an animal; the clinic '
                  'says so at the door, kindly, the way it says everything '
                  'it has said a thousand times. Tuck knows somebody. Tuck '
                  'always knows somebody. "The Blue Surgeon patches what '
                  'you put in front of him," he says. "He does not ask what '
                  'it is. That is the whole of his ethic and it is a good '
                  'one for this."',
                  requires=('stray_settled', 'pet:kept:40'),
                  sets=('stray_ill',),
                  after=6,
                  choices=(
                      Choice('surgeon', 'Carry it to the Shambles',
                             'You carry {pet} to the Shambles in a coat, and '
                             'the Blue Surgeon looks at it the way he looks '
                             'at a deck component, and does something with '
                             'his hands that you do not watch, and charges '
                             'you what he charges for a hand. {Pet} is on '
                             'the warm part of the deck by morning, in the '
                             'exact shape of not having been ill.',
                             sets=('stray_treated',),
                             credits=-300),
                      Choice('nurse', 'Sit with it',
                             'You sit with it. There is nothing in the flat '
                             'that fixes an animal, so you do the thing that '
                             'is not fixing: water on a finger, the warm '
                             'part of the deck, your hand where it can feel '
                             'the hand. Two shifts. It is not a decision, it '
                             'is what you find you are doing, and on the '
                             'third morning {pet} eats, and looks at you as '
                             'if you had been making a fuss.',
                             sets=('stray_nursed',)),
                      Choice('let', 'Let it go',
                             'You carry {pet} to the door and open it and do '
                             'not close it, and it goes the way it came, '
                             'which is without ceremony and without looking '
                             'back, because that is what it is. The flat is '
                             'a flat again. You leave the door open longer '
                             'than the cold makes sense of.',
                             sets=('stray_let',)),
                  )),
            Stage('old', 'What it was',
                  'An animal is a thing that was yours for a while, on the '
                  'warm part of the deck or not, and the Ninth does not say '
                  'what happened to a thing; it says what it was. Tuck asks '
                  'after it by name, once, and you tell him, and he nods, '
                  'and stands you a drink without saying what for.',
                  requires=('stray_ill',),
                  any_of=('stray_treated', 'stray_nursed', 'stray_let'),
                  sets=('stray_old',),
                  after=4,
                  where='ninth'),
        )),
    Thread(
        'construct', 'The Thing That Talks',
        'The construct on your deck says a name it should not know.',
        stages=(
            Stage('says', 'It says a name',
                  'Somewhere on the tenth run it rides with you, {familiar} '
                  'says a name. Not yours. Not a host\'s. A person\'s name, '
                  'said the way you say a name you have been told not to. '
                  'Remnant, when you tell them, goes very still, because it '
                  'is the name that was on a Sendai table four years ago, '
                  'and they have not told anybody that name either.'
                  '\n\n"It is not learning," Remnant says. "It is '
                  'remembering. That is worse. Ask yourself where it was '
                  'before it was on your deck."',
                  requires=('familiar:10', 'met:remnant'),
                  sets=('construct_says',),
                  where='glasshouse',
                  choices=(
                      Choice('wipe', 'Wipe it',
                             'You drop it, and the deck runs a fraction cooler '
                             'for the memory back, and the flat is quieter on '
                             'the runs afterwards in a way you had not known '
                             'it was loud. Remnant does not thank you. They '
                             'say, "It was somebody\'s, once," and do not say '
                             'whose.',
                             sets=('construct_wiped',)),
                      Choice('keep', 'Keep it, and listen',
                             'You keep it. It does not say the name again for '
                             'a long time, and when it does, you are ready, '
                             'and you write it down. There are three names in '
                             'the file now, and the file is yours, and '
                             '{familiar} is the only thing in this city that '
                             'has ever told you something it did not want to.',
                             sets=('construct_kept',)),
                      Choice('give', 'Give it to Remnant',
                             'Remnant takes it onto their own deck, which is '
                             'a thing they said they would never load anything '
                             'onto again, and sits with it in the clinic '
                             'waiting area, and the two of them do not speak. '
                             '"It knows my name," Remnant says, after a while. '
                             '"So do I, now. I had not been sure."',
                             sets=('construct_given',),
                             rep={'sendai': -4}),
                  )),
            Stage('quiet', 'What it was',
                  'The waiting area at the Sendai clinic is the same as it '
                  'was. Remnant sits in it or does not. On the deck, the '
                  'memory the construct rode is a program\'s now, or is '
                  'still the construct\'s, or is Remnant\'s to keep. What has '
                  'changed is that you know the constructs come from '
                  'somewhere, and that where they come from keeps names.',
                  requires=('construct_says',),
                  any_of=('construct_wiped', 'construct_kept', 'construct_given'),
                  sets=('construct_settled',),
                  after=3,
                  where='glasshouse'),
            Stage('yours', 'The second name',
                  'On a run that is not the tenth or the twentieth but some '
                  'ordinary night in between, {familiar} says a second '
                  'name, and it is yours. Not the handle. The name on the '
                  'roster, spelled the way you spell it, said the way you '
                  'say a name you have been told not to. "It is '
                  'remembering," Remnant said. You had thought that meant '
                  'the past.',
                  requires=('construct_kept', 'familiar:20'),
                  sets=('construct_yours',),
                  after=6,
                  choices=(
                      Choice('ask', 'Ask it what it remembers',
                             'You ask. It tells you: a room, a table, a name '
                             'said over it, a door with a number on it that '
                             'you know, because you have walked past it in '
                             'the Glasshouse forty times. It does not know '
                             'what any of that is. It knows the order. '
                             'There are three names in the file now and one '
                             'of them is yours and you wrote it down.',
                             sets=('construct_asked',)),
                      Choice('erase', 'Wipe it, this time',
                             'You drop it, and the deck runs a fraction '
                             'cooler for the memory back, and the flat is '
                             'quieter on the runs afterwards, and the thing '
                             'it said is still said, which is the thing '
                             'about a thing being said. Remnant, when you '
                             'tell them, says only: "It would have said the '
                             'third one."',
                             sets=('construct_erased',)),
                      Choice('archive', 'Give it to the Archivist',
                             'The Archivist takes it in both hands, the way '
                             'they took the log, and does not load it, and '
                             'puts it in the back room with the nine, and '
                             'says: "It is a log too. I had not thought of '
                             'that." They turn their chair round. "Ten," '
                             'they say, and it is not clear which ten they '
                             'mean.',
                             sets=('construct_archived',)),
                  )),
            Stage('order', 'What it knew',
                  'The constructs come from somewhere, and where they come '
                  'from keeps names, and now you know it keeps the order of '
                  'them too: a room, a table, a name, a door. Whatever you '
                  'did with {familiar}, the order is in the file, in your '
                  'hand, and the file is yours, and the third name is not '
                  'in it yet.',
                  requires=('construct_yours',),
                  any_of=('construct_asked', 'construct_erased', 'construct_archived'),
                  sets=('construct_order',),
                  after=3),
        )),
    Thread(
        'names', 'What They Call You',
        'The city has more than one name for you, and Osei uses one.',
        stages=(
            Stage('used', 'Osei uses one',
                  'Osei says one of the names the city has for you, across '
                  'the bar, to somebody else, about you, while you are '
                  'standing there. Not the handle. One of the other ones: '
                  'the kind that gets said about a person and then, after '
                  'enough saying, to them. He does not look at you while he '
                  'says it. He knows you heard.'
                  '\n\n"You have three of those now," he says, later, '
                  'wiping something. "People collect them. People choose one. '
                  'People throw them all back. I have seen all of it and I '
                  'have an opinion about none of it."',
                  requires=('titles:3', 'met:bartender'),
                  sets=('names_used',),
                  where='marrow',
                  choices=(
                      Choice('wear', 'Wear one',
                             'You tell him which one, and he nods, and from '
                             'then on that is the one he uses, and because it '
                             'is the one Osei uses it is the one Marrow uses, '
                             'and because Marrow uses it, so does the city. '
                             'You did not choose it. You chose to have chosen '
                             'it, which is the thing the city respects.',
                             sets=('names_worn',)),
                      Choice('refuse', 'Throw them back',
                             'You tell him the handle is the name, and he '
                             'says fine, and uses the handle, and the city '
                             'goes on using the others behind your back, '
                             'which is where names live anyway. Nothing '
                             'changes. Something has been said, though, and '
                             'Osei heard it.',
                             sets=('names_refused',)),
                      Choice('own', 'Ask what he calls you',
                             'You ask what he calls you, when you are not '
                             'there. He tells you. It is not any of the '
                             'three. It is shorter and worse and more '
                             'accurate, and he has been using it for a '
                             'month, and it is yours now whether you wear it '
                             'or not.',
                             sets=('names_own',)),
                  )),
            Stage('said', 'What it is worth',
                  'A name is what people can say about you without you in '
                  'the room, and you have several, and one of them is the '
                  'one they say most. Osei knows which. He has stopped '
                  'telling you. That is a kindness, from Osei, and the only '
                  'kind he has.',
                  requires=('names_used',),
                  any_of=('names_worn', 'names_refused', 'names_own'),
                  sets=('names_settled',),
                  after=2,
                  where='marrow'),
        )),
    Thread(
        'door', 'The Stake',
        'People who count what they have are people who are leaving.',
        stages=(
            Stage('counted', 'Mara has noticed you counting',
                  'Mara says it without looking up: "People who count what '
                  'they have are people who are leaving. I have placed four '
                  'hundred of these and I know the arithmetic of a runner '
                  'who is putting something away." She turns a page. "I do '
                  'not mind. I would like to know, is all. There are jobs I '
                  'would give somebody who is staying, and jobs I would '
                  'give somebody who is not."',
                  requires=('credits:9000', 'runs:10', 'met:mara'),
                  sets=('door_counted',),
                  where='marrow',
                  choices=(
                      Choice('tell', 'Tell her',
                             'You tell her the number, and how close you are '
                             'to it. She writes nothing. From then on the '
                             'jobs she hands you are the kind that pay and '
                             'do not follow you home, which is a thing a '
                             'fixer can do for somebody, once, and she is '
                             'doing it.',
                             sets=('door_told',),
                             rep={'fixers': 8}),
                      Choice('lie', 'Say you are staying',
                             'You say you are staying, and she says good, and '
                             'the jobs she hands you are the kind she hands '
                             'people who are staying, which are the ones with '
                             'a future in them and a past. Somewhere she has '
                             'written down that you lied, in the book, in the '
                             'column for that.',
                             sets=('door_lied',)),
                      Choice('spend', 'Spend it',
                             'You spend it, the way you spend a number that '
                             'has started to mean something: on the bar, on '
                             'the people at it, on a night the Ninth talks '
                             'about for a week. In the morning you are a '
                             'runner who is staying, because you have made it '
                             'true, and Mara, who has seen that done, hands '
                             'you the next job without a pause.',
                             sets=('door_spent',),
                             credits=-3000,
                             rep={'fixers': 6, 'sixes': 4}),
                  )),
            Stage('leaving', 'The arithmetic',
                  'The book has your line in it, and beside it the thing '
                  'Mara knows about you, whichever it is: that you are '
                  'putting something away, or that you said you were not, or '
                  'that you spent it. She hands you jobs accordingly. You '
                  'notice, after a while, that they suit you, and that this '
                  'is what a fixer is for.',
                  requires=('door_counted',),
                  any_of=('door_told', 'door_lied', 'door_spent'),
                  sets=('door_settled',),
                  after=4,
                  where='marrow'),
        )),

    # -- The ninth log (D171): the second arc --------------------------------
    # The Archivist's nine logs belonged to nine runners. Eight are dead or
    # gone. The ninth is on your board, and Deepwater is not finished with
    # them either. Which runner is the city's choice, made when the scene
    # fires (the one you are bound to, else the most worked), and the prose
    # carries `{runner}` for the world to fill. What you did with your own
    # log decides what they can do with theirs.
    Thread(
        'nine', 'The Ninth Log',
        'Eight of the nine are dead or gone. The ninth is still working.',
        stages=(
            Stage('named', 'The ninth log has a name',
                  'The Archivist has the nine out on the table, which they '
                  'have never done, and their hand is on the last one. "Eight '
                  'of these belong to people who are dead, or who left, or '
                  'who are what Remnant is, which I do not have a word for." '
                  'They turn the ninth round so you can read the header. "The '
                  'ninth is still working. You have seen them on the board. '
                  'You may have worked beside them."'
                  '\n\nThe handle in the header is {runner}\'s, spelled the way '
                  'they spell it. The log is longer than they have been '
                  'running. "It does not end wrong yet," the Archivist says. '
                  '"It has not ended."',
                  requires=('met:archivist', 'asked:archivist:logs', 'did:deepwater.posting'),
                  sets=('nine_named',)),
            Stage('ask', 'You know something they do not',
                  'You know a thing about {runner} that {runner} does not '
                  'know: that there is a log with their name in the header '
                  'in a back room in a fence\'s, and that it is longer than '
                  'their career, and that eight people who had one are not '
                  'here. There are three things you can do with a thing like '
                  'that, and all three are the kind the city remembers.',
                  requires=('nine_named', 'ninth:alive'),
                  sets=('nine_asked',),
                  after=1,
                  choices=(
                      Choice('tell', 'Tell them',
                             'You find {runner} and you tell them, all of it, '
                             'the nine and the shape the nothing has and the '
                             'header with their name in it. They do not say '
                             'anything for long enough that you wonder if you '
                             'have made a mistake. Then: "Thank you." Then: '
                             '"What did you do with yours?" You tell them '
                             'that too.',
                             sets=('nine_told',)),
                      Choice('keep', 'Keep it',
                             'You keep it. It is not a decision so much as a '
                             'shift that goes by without your having found '
                             'them, and then another, and then it is a thing '
                             'you know and they do not and that has become '
                             'the shape of it. You see them on the board. '
                             'They nod. You nod.',
                             sets=('nine_kept',)),
                      Choice('sell', 'Sell it to Static',
                             'Static pay for it, in cash, quickly, the way '
                             'they pay for things they intend to run: a '
                             'runner\'s name, a log that outruns their career, '
                             'a client nobody has met. It goes out in two '
                             'days. {runner} reads about themselves in the '
                             'same paragraph as the water, and finds out who '
                             'sold it in the paragraph after.',
                             sets=('nine_sold',),
                             credits=2500,
                             rep={'static': 10}),
                  )),
            Stage('posted_read', 'Their posting, and yours was read',
                  'It comes through Mara, and it has {runner}\'s name in it, '
                  'and she places it the way she placed yours, a moment '
                  'longer on the counter. They take it. You hear how it went '
                  'the way you hear everything, a shift late: they came out '
                  'with the record, and the record was a log, and the log '
                  'was theirs. They read it, because you read yours, and '
                  'because you told them what reading it was like, or did '
                  'not, which they will have noticed.',
                  requires=('nine_named', 'did:deepwater.posting', 'dw_read', 'ninth:alive'),
                  sets=('nine_posted',),
                  after=4),
            Stage('posted_archived', 'Their posting, and yours is in the back room',
                  'It comes through Mara with {runner}\'s name in it, and '
                  'they take it, and they come out with the record, and the '
                  'record is a log. The Archivist has yours. They have '
                  'theirs. The Archivist has, for the first time in nine '
                  'years, two of them side by side that have not ended, and '
                  'turns their chair round to tell you that the two logs '
                  'have the same entry for the day after tomorrow, and it '
                  'is a Tuesday.',
                  requires=('nine_named', 'did:deepwater.posting', 'dw_archived', 'ninth:alive'),
                  sets=('nine_posted',),
                  after=4),
            Stage('posted_burned', 'Their posting, and yours was wiped',
                  'It comes through Mara with {runner}\'s name in it, and '
                  'they take it, and they come out with the record, and the '
                  'record is blank. Not empty: blank, the way a thing is '
                  'blank when something has been taken out of it and the '
                  'shape of what was taken is still there. You wiped yours. '
                  'Theirs came out with a hole in it the size of you, and '
                  '{runner} does not know what was in the hole, and you do.',
                  requires=('nine_named', 'did:deepwater.posting', 'dw_burned', 'ninth:alive'),
                  sets=('nine_posted',),
                  after=4),
            Stage('table', 'Two logs, one table',
                  '{runner} puts theirs on the table in the back bar, next '
                  'to where yours was or is or was wiped from, and looks at '
                  'you the way you looked at the Archivist: as somebody who '
                  'has a third fact. "It knows both of us," they say. "It '
                  'has for years. So." The so is the question. There are '
                  'three answers to it and one of them is the kind the city '
                  'never forgets.',
                  requires=('nine_posted', 'nine_told', 'ninth:alive', 'not:ninth:crew'),
                  sets=('nine_table',),
                  after=1,
                  choices=(
                      Choice('together', 'Run the next one together',
                             'You say the next one is both of you, and they '
                             'say yes before you have finished, and it is not '
                             'a decision about Deepwater at all. It is a '
                             'decision about the eight who did it alone. The '
                             'tenth log, when there is one, will have two '
                             'handles in the header, and that has never '
                             'happened, and it may be the one thing the thing '
                             'at the bottom of the resolution has not seen.',
                             sets=('nine_together',)),
                      Choice('alone', 'Keep it your own',
                             'You say you work alone, which is true, and '
                             '{runner} says so do they, which is also true, '
                             'and the two logs go back into two bags, and '
                             'that is the end of the table. It is not a '
                             'falling out. It is two people who both know '
                             'what the eight had in common, deciding it was '
                             'not the being alone.',
                             sets=('nine_alone',)),
                      Choice('handed', 'Hand them to Deepwater',
                             'It has a contract for that. It always had. You '
                             'file it, and the money is the largest sum you '
                             'have ever seen cleared in one line, and '
                             '{runner}\'s next posting has no name in the '
                             'header at all, which is the last thing you '
                             'read about them for a long time. The Archivist '
                             'puts the ninth log with the other eight. They '
                             'do not turn their chair round.',
                             sets=('nine_handed',),
                             credits=6000,
                             rep={'deepwater': 20}),
                  )),
            Stage('table_crew', 'Two logs, one deck',
                  '{runner} is already beside you, which changes the table: '
                  'it is not a proposal, it is a thing you are both already '
                  'doing, with a log each in the bag and a client that knows '
                  'both handles. They put theirs next to yours on the deck '
                  'case, in the flat, where nobody else is. "It knows we '
                  'work together," they say. "It has for a while. So." The '
                  'so is the same question, asked by somebody who has '
                  'already answered half of it.',
                  requires=('nine_posted', 'nine_told', 'ninth:crew'),
                  sets=('nine_table',),
                  after=1,
                  choices=(
                      Choice('stay', 'Keep running together',
                             'You say nothing changes, and {runner} says '
                             'good, and it is the shortest conversation the '
                             'two of you have had about the largest thing. '
                             'The tenth log, when there is one, will have '
                             'two handles in the header and the same door '
                             'in every entry, and that has never happened.',
                             sets=('nine_together',)),
                      Choice('release', 'Let them go',
                             'You say the eight had one thing in common and '
                             'you are not going to be the ninth\'s, and you '
                             'release them, and {runner} does not argue, '
                             'which is how you know they had thought it too. '
                             'The crew is one person again. The log is one '
                             'log.',
                             sets=('nine_alone',)),
                      Choice('handed', 'Hand them to Deepwater',
                             'It has a contract for that, and the contract '
                             'does not care that they are on your crew; it '
                             'may prefer it. You file it. The money is the '
                             'largest sum you have ever seen cleared in one '
                             'line, and {runner} is not beside you in the '
                             'morning, and the deck case has one log on it.',
                             sets=('nine_handed',),
                             credits=6000,
                             rep={'deepwater': 20}),
                  )),
            Stage('found', 'They find out',
                  '{runner} finds out that you knew. Everybody does, in this '
                  'city, in the end: the Archivist says something, or Static '
                  'prints it, or a log has a line in it about a conversation '
                  'that did not happen. They do not come to the back bar. '
                  'They do not send anything through the deck. They are on '
                  'the board, and they take the job you were going to take, '
                  'and that is how {runner} says it.',
                  requires=('nine_posted', 'ninth:alive'),
                  any_of=('nine_kept', 'nine_sold'),
                  sets=('nine_found',),
                  after=2),
            Stage('tenth_together', 'Ten, with two handles',
                  'There are ten logs now, and the tenth has two handles in '
                  'the header, and the Archivist has stopped saying nine. '
                  '{runner} is at the door before you are on the nights you '
                  'work, and on the nights you do not they are somewhere '
                  'else, working, which is what a partner is: somebody '
                  'whose log you are in. Somewhere below the resolution '
                  'something that knows both your names has written down '
                  'that it has never seen this, and it has not.',
                  requires=('nine_posted', 'nine_together', 'ninth:alive'),
                  sets=('nine_tenth',),
                  after=3),
            Stage('tenth_alone', 'Ten, in two bags',
                  'There are ten logs now, in two bags, and the Archivist '
                  'has stopped saying nine. {runner} nods on the board and '
                  'you nod back, and you both know what the eight had in '
                  'common and you both decided it was not the being alone, '
                  'and you both work alone, and that is not a contradiction. '
                  'It is the city. Somewhere below the resolution something '
                  'that knows both your names has written down two logs '
                  'that go on not ending, separately.',
                  requires=('nine_posted', 'nine_alone', 'ninth:alive'),
                  sets=('nine_tenth',),
                  after=3),
            Stage('tenth_handed', 'Nine, and a line cleared',
                  'The Archivist has nine logs again. They put the ninth '
                  'with the eight the shift the money cleared, and they '
                  'did not turn the chair round, and they have not since. '
                  'The largest sum you have ever seen in one line is in '
                  'your account and it is smaller every shift, the way '
                  'money is. {runner} is not on the board. Nobody has read '
                  'a posting with their name in it since, and you know '
                  'why, and you are the only one who does.',
                  requires=('nine_posted', 'nine_handed', 'ninth:gone'),
                  sets=('nine_tenth',),
                  after=3),
            Stage('tenth_found', 'Ten, and one of them knows',
                  'There are ten logs now and {runner} keeps theirs where '
                  'you cannot see it, which is fair, because you kept what '
                  'you knew where they could not. They take the jobs you '
                  'were going to take. You take the ones they leave. The '
                  'Archivist has stopped saying nine and has started saying '
                  'nothing, which from the Archivist is a review.',
                  requires=('nine_posted', 'nine_found', 'ninth:alive'),
                  sets=('nine_tenth',),
                  after=3),
            Stage('ended', 'The ninth ends the way the eight did',
                  'The Archivist tells you without turning the chair round, '
                  'which is how you know. The ninth log has a last entry now '
                  'and then a nothing with a shape to it. They put it with '
                  'the other eight. "Nine," they say, and then, after a '
                  'while, "You are the one I have not filed."',
                  requires=('nine_named', 'ninth:dead'),
                  sets=('nine_ended',),
                  after=1),
        )),

    # -- The long wash (D169) ------------------------------------------------
    # The third way out from under a number, for the runner who cannot pay
    # for a name and will not take the box: work. Mara launders the name
    # over ten shifts of Switchboard work, and at the end of it nobody is
    # paying to find you, and the heat is half what it was.
    Thread(
        'wash', 'The Long Wash',
        'Mara will launder the name, for work rather than money, over ten shifts.',
        stages=(
            Stage('offer', 'Work it off',
                  'Mara closes the book, which she does not do. "There is a '
                  'number on you and there is nothing in your account and '
                  'you have not taken the box out, which I would have heard '
                  'about. So." She opens the book again to a page you have '
                  'not seen. "Ten shifts. You work what I give you, you take '
                  'what it pays, and at the end of it the name is clean, '
                  'because I will have made it clean, slowly, the way it is '
                  'done when nobody is paying for it fast."'
                  '\n\nIt is not a favour. She says that too.',
                  requires=('bounty:1', 'not:credits:1800', 'met:mara', 'runs:4'),
                  sets=('wash_offered',),
                  choices=(
                      Choice('work', 'Work it off',
                             'You say yes, and she writes something, and '
                             'from then on the jobs that come through her '
                             'come with a second line under them that you '
                             'are not shown. Ten shifts. The city does not '
                             'notice you doing it, which is the whole of '
                             'what she is selling.',
                             sets=('wash_working',)),
                      Choice('no', 'Keep the name as it is',
                             'You say no. She does not ask why, and she '
                             'writes nothing, and the number on your name '
                             'stays the number it was, and the book stays '
                             'open at the old page.',
                             sets=('wash_refused',)),
                  ),
                  where='marrow'),
            Stage('second', 'The second line',
                  'The jobs that come through Mara now have a second line '
                  'under them that you are not shown, and once, by accident '
                  'or on purpose, the book is open at your page when you '
                  'come in. The second line is a name. Not yours. The one '
                  'the paper is being moved off you and onto, slowly, a '
                  'little a shift, in a hand you recognise from the '
                  'contracts. She closes it before you have finished '
                  'reading. "Halfway," she says. "Do not ask whose."',
                  requires=('wash_working',),
                  sets=('wash_second',),
                  after=4,
                  where='marrow'),
            Stage('washed', 'The name comes clean',
                  'Ten shifts, and Mara says nothing about it, and then '
                  'says one thing: "Done." The number is off. Nobody is '
                  'paying for you this week, and the ones who were angry '
                  'are half as angry, which is the most that can be done '
                  'for anger by paperwork. She does not say what it cost '
                  'her. It cost her something.',
                  requires=('wash_working', 'wash_second'),
                  any_of=('wash_working', 'wash_refused'),
                  sets=('wash_washed',),
                  after=6,
                  where='marrow'),
        )),

    # -- The paper (D162) ----------------------------------------------------
    # The other side of a bounty: the freight line is the way out, this is
    # the thing coming in. Somebody has taken the paper on your name, and
    # Mara, who placed the paper on everybody else, tells you so.
    Thread(
        'paper', 'The Paper',
        'Somebody has taken the paper on your name, and is coming to collect it.',
        stages=(
            Stage('taken', 'Somebody took the paper',
                  'Mara says it the way she says everything, into the book '
                  'and not to you. "Somebody took the paper on you. A '
                  'runner, not a firm. They asked me where you drink." A '
                  'pause the length of a line being written. "I told them '
                  'you do not." She does not say the name. The book does, '
                  'upside down across the counter: {collector}.'
                  '\n\nA runner who takes a bounty collects it in person, '
                  'which means a night, a doorway, and a number that has '
                  'your face on it. There are three things people do about '
                  'that, and Mara has watched all three.',
                  requires=('bounty:1', 'runs:6', 'met:mara'),
                  sets=('paper_taken',),
                  choices=(
                      Choice('ground', 'Go to ground',
                             'You stop being where you are. A different bed, '
                             'a different market, the deck off for three '
                             'nights. Whoever took the paper walks the routes '
                             'you used to walk and finds the routes. It '
                             'costs you the week and it costs them the '
                             'certainty, and certainty is what a collector '
                             'is paid in.',
                             sets=('paper_ground',)),
                      Choice('buy', 'Buy the paper back',
                             'Mara knows what they were promised and she '
                             'knows what they would take instead, which is '
                             'more, in cash, tonight. The paper comes back '
                             'through her, folded, with your name on it in '
                             'somebody else\'s hand. You keep it. Everybody '
                             'keeps theirs.',
                             sets=('paper_bought',),
                             credits=-2400),
                      Choice('front', 'Be seen',
                             'You go to the Hall and you sit where you can '
                             'be found and you let the room know you know. '
                             'A collector wants a doorway, not an audience. '
                             '{Collector} comes in, sees you seeing them, and '
                             'has a drink instead, because the number on '
                             'the paper was for a surprise and there is not '
                             'going to be one.',
                             sets=('paper_faced',),
                             rep={'fixers': 6}),
                  ),
                  where='marrow'),
            Stage('kept', 'What the paper cost',
                  'Mara does not bring it up again, which is how you know it '
                  'is over. The book has a line in it that she does not '
                  'read to you. Somewhere a runner is a week older and no '
                  'richer, and the number on your name is the same number, '
                  'and everybody in the room knows what it is worth now, '
                  'which is less than it says.',
                  requires=('paper_taken',),
                  any_of=('paper_ground', 'paper_bought', 'paper_faced'),
                  after=3,
                  where='marrow'),
        )),

    # -- The quiet door (D159) ---------------------------------------------
    # A number on the name and less in the account than a new name costs
    # is the one state the door had nothing for: a bounty does not cool,
    # `burn` wants 1,800c, and the campaigns' explorer stood at the door
    # with 55c and nowhere to go. This is the cheap way out. It costs the
    # name, the record and the city, which is what cheap means here.
    Thread(
        'quiet', 'The Freight Line',
        'There is a way out of the city that does not go through a door.',
        stages=(
            Stage('berth', 'Somebody knows a berth',
                  'It comes through the kind of person who is only ever '
                  'introduced as somebody who knows somebody. A container '
                  'goes out on the freight line from the docks four nights '
                  'a week, and one in nine is checked, and the man who '
                  'decides which one has a cousin. Nobody asks your name. '
                  'That is the offer: nobody asks your name, ever again.'
                  '\n\nIt costs what is in your pocket, which is nothing, '
                  'which is the point. It costs the name, which somebody '
                  'else is paying to find. And it costs the city, which '
                  'is the only thing you own.',
                  # A career, not a bad week: the first cut opened at three
                  # runs and five of six campaigns took the box by default.
                  requires=('bounty:1', 'not:credits:1800', 'runs:6', 'shift:20'),
                  sets=('quiet_berth',),
                  choices=(
                      Choice('stay', 'Stay and be found',
                             'You say no. The person who knows somebody '
                             'shrugs, which is what that kind of person '
                             'does, and the offer is gone by morning. The '
                             'number on your name is not. You are still '
                             'here, which means you still think you can '
                             'turn it, and the city has watched people '
                             'think that before.',
                             sets=('quiet_stayed',),
                             rep={'freeport': 4}),
                      Choice('go', 'Take the berth',
                             'You go the same night. The container is cold '
                             'and smells of what it carried before, and the '
                             'freight line does not stop, and somewhere '
                             'past the last relay the deck loses the city '
                             'and does not find anything to replace it with.'
                             '\n\nNobody checks. Nobody asks. In the morning '
                             'there is a town with a name you have never '
                             'heard, and you get out of the box and walk '
                             'into it as somebody who used to do this.',
                             sets=('left_quietly',),
                             ends='left quietly'),
                  )),
            Stage('watched', 'Still here',
                  'The docks know you were offered the berth and did not '
                  'take it. Nobody says so. A docker nods at you once, '
                  'the way you nod at somebody who has decided something '
                  'expensive, and the freight line goes out that night '
                  'without you in it.',
                  requires=('quiet_stayed',),
                  any_of=('quiet_stayed', 'left_quietly'),
                  after=2,
                  where='freeport'),
            Stage('turned', 'The number came off',
                  'The number is off your name. Paid, burned, or outlasted: '
                  'the docks do not ask which, and do not need to. The same '
                  'docker nods at you again, once, which is a whole '
                  'conversation on that quay, and the person who knows '
                  'somebody is not seen again, because there is nothing '
                  'left to know somebody about.',
                  requires=('quiet_stayed', 'not:bounty:1'),
                  sets=('quiet_turned',),
                  after=4,
                  where='freeport'),
        )),

    # -- The Hall: the woman who does not sing (D65 depth) ---------------------
    Thread(
        'listener', 'The Woman Who Does Not Sing',
        'She came out of Deepwater. She sits on the platform and listens, and '
        'the Chorus feed her, and that is the whole of what anybody knows.',
        crosses=('deepwater', 'soup'),
        stages=(
            Stage('bench', 'She speaks',
                  'She is on the platform, on the bench under the board that '
                  'shows a hymn, where she always is, and tonight when you '
                  'pass with the kettle she says, without looking up, the '
                  'name of a network, and then, "You have heard it. Or you '
                  'will. I can hear which."\n\n'
                  'The Cantor, across the concourse, has stopped stirring.',
                  requires=('met:cantor',),
                  any_of=('dw_heard', 'runs:6'),
                  sets=('listener_spoke',),
                  where='hall'),
            Stage('where', 'What she wants',
                  '"I do not sing because I can still hear it," she says. '
                  '"Eleven years of it. The singing here is the only thing '
                  'that is louder." She turns her head, finally. "There is '
                  'somebody in the Glasshouse who had theirs taken out. I '
                  'would like to know if it stopped for them. I would like '
                  'somebody to ask."\n\n'
                  'The Cantor has come over. He does not say anything. He '
                  'hands you the kettle, which is full, and heavy, and his.',
                  requires=('listener_spoke',),
                  sets=('listener_asked',),
                  choices=(
                      Choice('remnant', 'Take her to the dark room',
                             'You take her to the Glasshouse, to the dark '
                             'room, to Remnant, who looks at her for a long '
                             'time and then says, "No. It does not stop. It '
                             'gets quieter and you get used to the quiet and '
                             'then one day you notice you have been listening '
                             'to the quiet."\n\n'
                             'She nods. On the way back she sings, very '
                             'quietly, under her breath, once, and then does '
                             'not, and you do not mention it.',
                             sets=('listener_remnant',),
                             rep={'chorus': 15, 'deepwater': -5}),
                      Choice('leave', 'Leave her on the bench',
                             'You do not take her anywhere. It is not yours '
                             'to carry, and you have the kettle, and the '
                             'kettle is enough.\n\n'
                             'She is on the bench the next night, and the '
                             'next, and she does not speak to you again, and '
                             'the Cantor feeds her, and that is the whole of '
                             'what anybody knows.',
                             sets=('listener_left',)),
                      Choice('notary', 'Tell the Notary she is here',
                             'The Notary does not look up. "A person who came '
                             'out of Deepwater. Noted." The pen moves for a '
                             'long time. "The ledger has a line for that '
                             'network. It is the longest line in the book. '
                             'Thank you."\n\n'
                             'A courier with a case that is not heavy enough '
                             'is on the Hall\'s platform the next morning, '
                             'sitting beside her, not talking. She does not '
                             'sing. She has stopped listening, too, or '
                             'started listening to something else.',
                             sets=('listener_told',),
                             rep={'meridian': 20, 'chorus': -15},
                             credits=900),
                  ),
                  where='hall'),
        )),

    # -- what an arrangement is, once you are paying one (D70) ---------------
    Thread(
        'collector', 'The Man Who Comes For It',
        'Somebody collects the number you agreed, every six shifts, and he '
        'has a name and a route and a bad knee.',
        crosses=('lender',),
        stages=(
            Stage('rota', 'The same man every time',
                  'It is the same man every time. Sixties, bad knee, a coat '
                  'that was good once, and a notebook he writes in with the '
                  'pen tied to it.\n\n'
                  '"You are on my rota," he says, the fourth time, as though '
                  'you had asked. "Forty-one of you. I do the whole east side '
                  'on a Tuesday." He takes the number, writes it down, and '
                  'then stands there a moment too long before saying: "They '
                  'have put the rota up. Fifty-three next month. I am sixty '
                  'eight."',
                  requires=('arranged:1',),
                  any_of=('runs:3', 'shift:12'),
                  sets=('collector_met',)),
            Stage('overlap', 'The other rota',
                  'He does not knock. He waits on the step until you come '
                  'out, which is new, and says it without looking up from '
                  'the notebook.\n\n'
                  '"There is a man asking after you at the corner. Not one '
                  'of mine, the other kind, the ones who do not write it '
                  'down." He turns a page, turns it back. "I have been on '
                  'this street since before you were on it. If you go out '
                  'the back of the laundry and up, you come out two streets '
                  'over and he will not see you go." A pause. "I did not '
                  'tell you that."',
                  requires=('collector_met', 'lender_angry'),
                  sets=('collector_warned',)),
            Stage('ask', 'What he wants',
                  'He asks on the doorstep, without preamble, the way people '
                  'ask when they have rehearsed it and know it is too big.\n\n'
                  '"The rota is a file. It is on their network, it says who '
                  'pays and how much and which of us collects it, and I have '
                  'seen it once, on a screen, over somebody\'s shoulder." He '
                  'shifts his weight off the bad knee. "I do not want it '
                  'destroyed. I want to know what I am on. Whether the round '
                  'is fifty-three because somebody died or because somebody '
                  'is skimming, and which of those I can survive."',
                  requires=('collector_met',),
                  sets=('collector_asked',),
                  posts=Posting(
                      patron='fixers', target='sixes', objective='exfiltrate',
                      title='The Rota',
                      blurb='A collection rota: who pays, how much, and which '
                            'collector walks which round. The man who walks '
                            'yours would like to read it before it is his '
                            'turn to be on it.',
                      label='the collection rota',
                      pay=1900)),
            Stage('rota_read', 'What the rota says',
                  'It is a spreadsheet, and it is worse than that, because '
                  'it is a good one.\n\n'
                  'Forty-one names on his round and fifty-three next month, '
                  'and the twelve new ones are transfers from a round that '
                  'has no collector against it any more. There is a column '
                  'nobody would notice unless they were on the sheet, which '
                  'is a per-collector percentage, and his is the lowest on '
                  'the page, and has been for nine years.',
                  requires=('did:collector.ask',),
                  sets=('collector_read',),
                  choices=(
                      Choice('tell', 'Tell him what it says',
                             'You tell him on the doorstep, all of it, and '
                             'he listens the way people listen to something '
                             'they already suspected.\n\n'
                             '"Nine years," he says. Then: "Right." He writes '
                             'something in the notebook with the pen tied to '
                             'it, and does not say what, and the next time he '
                             'comes for your number he takes it and says, '
                             '"Fifty-one. Two of them moved," and there is '
                             'something in how he says it.',
                             sets=('collector_told',),
                             rep={'sixes': -5, 'fixers': 10}),
                      Choice('trade', 'Sell it to somebody who collects rounds',
                             'A woman in Marrow buys the whole sheet without '
                             'reading past the first column, which is how '
                             'you know she already had most of it.\n\n'
                             'Three rounds are reorganised inside a month. '
                             'The man with the bad knee is not on any of '
                             'them, and somebody younger does your street '
                             'now, and does not write anything down.',
                             sets=('collector_traded',),
                             credits=2200,
                             rep={'fixers': 15, 'sixes': -10}),
                      Choice('nothing', 'Tell him you could not get it',
                             'You tell him you could not get it. He nods, '
                             'and says that is all right, and that it was a '
                             'lot to ask, and takes the number, and writes '
                             'it down.\n\n'
                             'He comes for it every six shifts after that, '
                             'and the round is fifty-three, and he does the '
                             'whole east side on a Tuesday, and neither of '
                             'you mentions it again.',
                             sets=('collector_kept',)),
                  )),
        )),

    # -- The explorer: the walking, answered (D147) ---------------------------
    Thread(
        'edges', 'The Edges',
        'You keep ending up in places that are not on the way to anywhere. So '
        'does somebody else, and they are keeping count.',
        crosses=(),
        stages=(
            Stage('noticed', 'Somebody who stands about too',
                  'You are in one of the places that is not on the way to '
                  'anywhere, the kind you have started to have opinions about, '
                  'and tonight there is somebody already in it, doing the '
                  'thing you do, which is standing where standing has no '
                  'reason.\n\n'
                  'They do not introduce themselves. They say, "You are the '
                  'other one. I wondered who was leaving the marks I keep '
                  'finding," and they mean the fact of you having been there, '
                  'which apparently leaves a mark to somebody who is counting.',
                  requires=('places:12',),
                  sets=('edges_seen',)),
            Stage('map', 'What they are making',
                  'They show you, eventually, and it is not a map of the city. '
                  'It is a map of where the city stops: the line the water '
                  'took and did not give back, the wards that are boarded at '
                  'both ends, the reservoir works behind the fence on the '
                  'hill, the half mile of quay nobody dredges. Every edge, and '
                  'nothing in the middle, because the middle is where everyone '
                  'already looks.\n\n'
                  '"I am nearly done," they say. "I have been nearly done for '
                  'six years. There are a few I have not stood at yet. You '
                  'have stood at more of the city than anybody I have met. I '
                  'would like your count, or I would like you to keep your '
                  'own. Both are answers."',
                  requires=('edges_seen', 'places:24'),
                  sets=('edges_asked',),
                  choices=(
                      Choice('add', 'Give them what you have stood at',
                             'You tell them the edges you have stood at that '
                             'they have not, and they write each one down in a '
                             'hand that has done this a long time, and when '
                             'you are finished the map is finished, and they '
                             'look at it for a while and then fold it once and '
                             'do not say anything, because there is nothing to '
                             'say to a thing you have spent six years finishing '
                             'and now have finished.',
                             sets=('edges_added',)),
                      Choice('keep', 'Keep your own count',
                             'You say you would rather keep your own, and they '
                             'nod as though that was the more likely answer '
                             'and not a worse one. "Then there are two of us '
                             'who know where it stops," they say, "which is '
                             'one more than there was." They go back to the '
                             'map, and you go back to the city, and you both '
                             'know the other is out there counting.',
                             sets=('edges_kept',)),
                  )),
            Stage('shape', 'The shape of the whole thing',
                  'You have stood at enough of it now that the city has a '
                  'shape in your head, and the shape is not the one on the '
                  'transit map. It is the one the water drew, and the boards, '
                  'and the fences, and the places a person can be that nobody '
                  'built. You do not know what to do with knowing it. That '
                  'turns out to be all right. Knowing it is the thing.',
                  requires=('places:36',),
                  any_of=('edges_added', 'edges_kept'),
                  sets=('edges_known',)),
        )),

    Thread(
        'kept', 'Kept Back',
        'The things you find were left for somebody. You are starting to '
        'suspect who.',
        crosses=(),
        stages=(
            Stage('once', 'A thing that was left out',
                  'The one-of-a-kind thing in your bag was not lost and not '
                  'dropped. Somebody kept it back and left it where only '
                  'somebody who went and looked would find it, and the rumour '
                  'about it always ends the same way, that it is there for '
                  'somebody, and this time the somebody was you.\n\n'
                  'You had put that down to luck. You are less sure now.',
                  requires=('finds:1',),
                  sets=('kept_once',)),
            Stage('pattern', 'More than once is a habit',
                  'It has happened enough times now to stop being luck. Every '
                  'one of them was kept back, by somebody, for somebody, and '
                  'the somebody keeps turning out to be whoever went and '
                  'stood where the thing was, which keeps turning out to be '
                  'you.\n\n'
                  'The Archivist, when you say this out loud in the back room, '
                  'does not look up. "The city gives things to the people who '
                  'go and look. It always has. You have started looking like '
                  'one of the people it gives things to." A pause. "I keep the '
                  'ones nobody came for. You are the other kind of record."',
                  requires=('kept_once', 'finds:3'),
                  sets=('kept_seen',),
                  choices=(
                      Choice('ask', 'Ask who has been leaving them',
                             'You ask, around the places, whether anybody '
                             'knows who leaves the things. Nobody does, and '
                             'the not-knowing is consistent in a way that is '
                             'its own answer: it is not one person. It is the '
                             'habit of a city that keeps things back for '
                             'whoever is still looking, and has been doing it '
                             'longer than anybody who could be asked.',
                             sets=('kept_asked',)),
                      Choice('leave', 'Leave it be, and keep looking',
                             'You decide you would rather not know, the way '
                             'you would rather not know how a good thing '
                             'works in case the knowing stops it. You keep '
                             'going and standing where nothing is, and the '
                             'things keep being there, and you stop being '
                             'surprised, which is not the same as stopping '
                             'being glad.',
                             sets=('kept_left',)),
                  )),
            Stage('one_of', 'One of the people it gives things to',
                  'You have found enough of them now to have stopped '
                  'counting it as luck. The city keeps things back for the '
                  'people who go and look, and you are one of the people it '
                  'gives things to, and that is a quieter thing to be than '
                  'the ones with the money and the names, and it lasts '
                  'longer, because it is not a thing anybody can take off '
                  'you: it is just where you have been.',
                  requires=('finds:5',),
                  any_of=('kept_asked', 'kept_left'),
                  sets=('kept_known',)),
        )),

    # -- The deck specialist: what only your line can open (D149) --------------
    Thread(
        'sealed', 'The Sealed Thing',
        'Osei keeps things people leave. One of them is a drive nobody has '
        'been able to open, and he has been waiting to meet somebody who '
        'could.',
        crosses=(),
        stages=(
            Stage('kept', 'A drive behind the bar',
                  'Osei puts it on the bar the way he puts down the second '
                  'drink, without being asked and without comment. A drive, '
                  'old, the casing worn smooth on one corner by a thumb that '
                  'is not yours.\n\n'
                  '"A runner left this with me. Paid a year up front for me to '
                  'keep it, and did not come back, and the year is a long way '
                  'gone." He wipes the bar that does not need it. "It is '
                  'locked in a way that has beaten everybody I have shown it '
                  'to. You are supposed to be good at that. I would like to '
                  'know what I have been keeping."',
                  requires=('met:bartender', 'skill:cryptography:3'),
                  sets=('sealed_shown',),
                  where='marrow'),
            Stage('open', 'What was under the lock',
                  'It is not a job and it is not money. It is a letter, the '
                  'kind nobody writes, addressed to a name that is not Osei\'s '
                  'and not yours, and under the letter a second file the '
                  'letter tells that person how to open, which is the only '
                  'reason the letter was locked at all: it is a key with an '
                  'apology wrapped round it.\n\n'
                  'Osei reads the name over your shoulder and goes very still, '
                  'and then says, "She still drinks here. Thursdays." He does '
                  'not say anything else. He is leaving it to you, the way the '
                  'runner left it to him.',
                  requires=('sealed_shown',),
                  sets=('sealed_open',),
                  choices=(
                      Choice('deliver', 'Give it to the name on it',
                             'You wait until Thursday. She reads the letter '
                             'standing up, at the bar, and does not sit down, '
                             'and when she is finished she puts the second '
                             'file in her pocket and buys the bar a drink it '
                             'does not know it is being bought, and leaves, '
                             'and Osei pours yours last, and does not charge '
                             'you for it, and that is the whole of what is '
                             'said about it.',
                             sets=('sealed_delivered',)),
                      Choice('read', 'Read the second file first',
                             'You open the second file before you give the '
                             'letter over, because you are the one who can, '
                             'and knowing you could was the same as doing it. '
                             'It is a list of everybody the runner ever gave '
                             'up, and to whom, and for how much, and the last '
                             'name on it is the name on the letter.\n\n'
                             'You give her the letter and keep that you read '
                             'the file, and it sits in you the way a thing you '
                             'cannot unknow sits, which is badly.',
                             sets=('sealed_read',), drift=4),
                      Choice('burn', 'Wipe it and tell Osei it was nothing',
                             'You wipe it, both files, and tell Osei it was a '
                             'corrupted backup, nothing anybody kept for a '
                             'reason. He looks at you for a moment longer than '
                             'the lie deserves and then nods and takes the '
                             'drive back and puts it under the bar, because a '
                             'thing somebody paid a year to keep is a thing you '
                             'keep, even after it is empty.',
                             sets=('sealed_burned',)),
                  )),
            Stage('after', 'What a lock is for',
                  'You are the one who can open what is shut, which you knew, '
                  'and what you did not know until Osei\'s drive is that being '
                  'the one who can open a thing is the same as being the one '
                  'who decides whether it should have been opened. A lock is '
                  'somebody trusting that the person who can beat it will know '
                  'when not to. You are that person now, to the people who '
                  'lock things, whether or not you ever wanted the job.',
                  requires=(),
                  any_of=('sealed_delivered', 'sealed_read', 'sealed_burned'),
                  sets=('sealed_done',)),
        )),

    Thread(
        'carrier', 'The Names on the Big Dish',
        'Pip catches things on the big dish that do not come from anywhere. '
        'You are the one who can find out where nowhere is.',
        crosses=(),
        stages=(
            Stage('names', 'What comes in on tower three',
                  'Pip has the dish off its mount and in your hands before you '
                  'have agreed to hold it. "Names," they say. "The big dish '
                  'catches names. Not on a channel. Between the channels, '
                  'where there is not supposed to be a channel. I have written '
                  'them down." They have. Pages of them, in a child\'s careful '
                  'hand.\n\n'
                  '"I do not know from where. Nobody does. You do the thing '
                  'with signals. I will trade you the pages for where."',
                  requires=('met:pip', 'skill:signal:3'),
                  sets=('carrier_heard',),
                  where='stacks'),
            Stage('where', 'Where nowhere is',
                  'You take the pages up tower three where the dish sits and '
                  'you do the thing with signals, the triangulation, the '
                  'walking of the phase, the long patient arithmetic of where '
                  'a thing that is between the channels is actually standing, '
                  'and the arithmetic keeps returning an answer that is not a '
                  'transmitter.\n\n'
                  'It is the water. The signal is coming up out of the harbour '
                  'at Freeport, from under it, on no power anybody is paying '
                  'for, and the names it is carrying are the names of runners, '
                  'and some of them are still alive, and one of them, when you '
                  'check, is you.',
                  requires=('carrier_heard',),
                  any_of=('dw_heard', 'runs:6'),
                  sets=('carrier_where',),
                  choices=(
                      Choice('tell', 'Tell Pip where',
                             'You tell Pip it comes from the water and let them '
                             'make of that what an eleven-year-old on a tower '
                             'makes of it, which is to nod as though you have '
                             'confirmed something, and write \'the water\' at '
                             'the top of the pages, and point the dish a '
                             'degree lower, at the harbour, to catch more of '
                             'it, because to Pip more of a thing is always the '
                             'answer.',
                             sets=('carrier_told',)),
                      Choice('keep', 'Keep where it comes from to yourself',
                             'You tell Pip the arithmetic did not close, that '
                             'the signal is a reflection, an artefact, nothing '
                             'standing anywhere, and Pip takes the dish back '
                             'and is disappointed in a way that is worse than '
                             'angry, and you keep that your name is coming up '
                             'out of the harbour on a frequency nobody pays '
                             'for, which is a thing you now get to know on your '
                             'own.',
                             sets=('carrier_kept',), drift=4),
                  )),
            Stage('after', 'A frequency nobody pays for',
                  'You know a thing about the water now that you did not go '
                  'looking for, which is the way you find out the things about '
                  'the water: it is carrying names, on no power, from under '
                  'the harbour, and it has yours. You do not do anything with '
                  'knowing it. There is nothing to do with it. It is just one '
                  'more thing that is true about the city that most people in '
                  'it get to not know.',
                  requires=(),
                  any_of=('carrier_told', 'carrier_kept'),
                  sets=('carrier_done',)),
        )),

    # -- The achiever: the scoreboard, answered (D150) -------------------------
    Thread(
        'reckoner', 'The Unit',
        'You have done a great deal of everything, and the city has started '
        'using your name as the measurement.',
        crosses=(),
        stages=(
            Stage('measure', 'A name that means an amount',
                  'You hear it in Marrow, from two people who do not know you '
                  'are behind them. One is describing a job to the other, and '
                  'to say how much of it there was, how loud and how long and '
                  'how much came out the far end, they use your handle. Not as '
                  'a person. As a unit. "It was half a" you, they say, and the '
                  'other one knows exactly how much that is.\n\n'
                  'Nobody decided to do this. It is what a city does with a '
                  'name it has heard attached to enough things: it stops being '
                  'a person and becomes a way of measuring the thing they did.',
                  requires=('record:8',),
                  sets=('reckoner_heard',)),
            Stage('meet', 'Somebody has been keeping the count',
                  'It turns out somebody has been keeping the actual count, on '
                  'purpose, for a while. They find you, which is easy, because '
                  'they know where you have been, because knowing where you '
                  'have been is the hobby. They have a book. You are most of '
                  'it.\n\n'
                  '"I do not want anything," they say, and mean it, which is '
                  'the strange part. "I keep the ones who did the lot. There '
                  'are not many and none of them lasted, and I would like to '
                  'have got yours down right before the same thing happens to '
                  'you. Tell me if I have any of it wrong."',
                  requires=('reckoner_heard', 'record:12'),
                  sets=('reckoner_met',),
                  choices=(
                      Choice('correct', 'Put them right where they are wrong',
                             'You go through the book with them and correct '
                             'the two or three things they have slightly '
                             'wrong, the seed of a night, the order of two '
                             'jobs, the name of somebody who was there, and '
                             'they write the corrections in a hand that is '
                             'careful about being a record and not a story, '
                             'and at the end they close the book and say '
                             '"thank you" as though you have done them the '
                             'favour, and you cannot decide whether you have.',
                             sets=('reckoner_corrected',)),
                      Choice('leave', 'Let the book say what it says',
                             'You tell them you would rather not know what is '
                             'in the book, or fix it, or read it, and they '
                             'accept that without argument, because a person '
                             'who did the lot not wanting to see the count of '
                             'it is itself a thing worth writing down, and '
                             'they write that down, and you leave them to it, '
                             'and it is out there now, a book with you in it, '
                             'being kept right by somebody whether you like it '
                             'or not.',
                             sets=('reckoner_left',)),
                  )),
            Stage('kept', 'In the book, either way',
                  'There is a book with you in it, kept by somebody who does '
                  'it for no reason except that the people who did the lot '
                  'should be got down right before the city closes over them, '
                  'which it does, over everybody, which is the reason for the '
                  'book. You did the lot. That is what the book is for, and it '
                  'is a stranger thing to have been than rich, and it lasts '
                  'about as long, which is to say not very, which is to say '
                  'longer than you will.',
                  requires=(),
                  any_of=('reckoner_corrected', 'reckoner_left'),
                  sets=('reckoner_done',)),
        )),

    # -- more of the deck specialist (D155) -----------------------------------
    Thread(
        'stack', 'The Shape of the Vertical',
        'Mrs Achterberg fits the building, and knows it is not the shape it '
        'shows. You are the one who can read what is actually there.',
        crosses=(),
        stages=(
            Stage('measured', 'She has measured most of it',
                  'She fits you the way she fits everybody, once, up and down, '
                  'and then does not let go of your sleeve.\n\n'
                  '"Ninety floors and one box, and everybody who matters has '
                  'stood on the box, and the box remembers them. But the '
                  'building is not ninety floors. It says ninety. I have '
                  'measured most of it and the sums do not close." She lets '
                  'the sleeve go. "You read the shape of a thing for a living. '
                  'I would like to know what is in the floors that are not on '
                  'the board in the lobby."',
                  requires=('met:tailor', 'skill:architecture:3'),
                  sets=('stack_asked',),
                  where='vertical'),
            Stage('read', 'What the sums do not close on',
                  'You take a night and read the Vertical the way it is built '
                  'rather than the way it is addressed, the risers and the '
                  'plant runs and the dead voids where a floor is declared and '
                  'nothing is wired to it, and the architecture resolves into '
                  'a building four floors taller than it admits, below the '
                  'lobby, not above it, on no lift the public box will '
                  'call.\n\n'
                  'Whatever is on those four floors is reached by a car that '
                  'only goes down, from a lobby that only goes up, and the '
                  'seam between the two is the cleanest piece of architecture '
                  'you have ever read, which is the thing that stays with you.',
                  requires=('stack_asked',),
                  sets=('stack_read',),
                  choices=(
                      Choice('tell', 'Tell her what is under the lobby',
                             'You tell Mrs Achterberg there are four floors '
                             'below the box, reached by a car that only '
                             'descends, and she nods as though you have '
                             'confirmed a measurement, and writes the number '
                             'four on the inside of her wrist in tailor\'s '
                             'chalk, and says, "Then I have been fitting them '
                             'for the wrong height," which you do not ask her '
                             'to explain.',
                             sets=('stack_told',)),
                      Choice('keep', 'Keep the shape to yourself',
                             'You tell her the sums close after all, that she '
                             'has miscounted a mezzanine, and she looks at you '
                             'for a long moment with the eyes of a woman who '
                             'has never once miscounted anything, and lets you '
                             'have the lie, because a person who keeps a shape '
                             'like that is a person who has understood what it '
                             'is, which was the whole of what she wanted to '
                             'know about you.',
                             sets=('stack_kept',)),
                  )),
            Stage('under', 'A car that only goes down',
                  'You know the shape of the Vertical now, the real one, and '
                  'it is a building that goes down as far as it goes up and '
                  'admits to neither, and you find that once you have read a '
                  'thing that cleanly you cannot stop reading it, in every '
                  'network after, the seam where the declared shape and the '
                  'wired one come apart. It is the specialist\'s reward and '
                  'the specialist\'s tax, and they are the same thing.',
                  requires=(),
                  any_of=('stack_told', 'stack_kept'),
                  sets=('stack_done',)),
        )),

    Thread(
        'unmade', 'What the Green Keeps',
        'The Green keeps records of patients who stopped coming, and they do '
        'not stay deleted. You are the one who can unmake a thing instead of '
        'removing it.',
        crosses=(),
        stages=(
            Stage('schedule', 'The door\'s schedule',
                  'The Orderly is at the aftercare door at the moment it '
                  'opens, holding the schedule, and this time turns it so you '
                  'can see it.\n\n'
                  '"Everybody here is well. I check twice a shift. The trouble '
                  'is the ones who stopped coming: the record says aftercare '
                  'is ongoing, because aftercare is never recorded as ended, '
                  'because ended is a word the architecture does not have. So '
                  'they are all still in care, all of them, for ever, and the '
                  'file grows, and I delete them, and by the next door they '
                  'are back." A pause. "You do the other thing. Not delete. '
                  'Unmake."',
                  requires=('met:orderly', 'skill:sabotage:3'),
                  sets=('unmade_asked',),
                  where='green'),
            Stage('undone', 'Not deleted, unmade',
                  'A deletion is a promise the system makes to itself and can '
                  'break; an unmaking is a wound in the schema that will not '
                  'heal into the old shape, and doing it properly means '
                  'corrupting not the records but the rule that regenerates '
                  'them, which is the load-bearing part of the architecture, '
                  'which is why nobody has.\n\n'
                  'You take the rule apart. The patients who stopped coming '
                  'stop being in care, all at once, for the first time since '
                  'they stopped, and the file stops growing, and the Orderly '
                  'watches the number go still and does not say anything for '
                  'a while.',
                  requires=('unmade_asked',),
                  sets=('unmade_done_it',),
                  choices=(
                      Choice('rest', 'Let them be gone',
                             'You leave it unmade, and the dead are dead in '
                             'the Green\'s books now as well as everywhere '
                             'else, which is a smaller thing than it sounds '
                             'and a larger thing than the Orderly will say, '
                             'and they thank you the way somebody thanks you '
                             'for a thing they cannot be seen to have wanted.',
                             sets=('unmade_rest',)),
                      Choice('keep', 'Keep the names first',
                             'Before you unmake it you take the names, all of '
                             'them, the ones who stopped coming, because a '
                             'thing being wrong to keep is not the same as it '
                             'being right to lose, and you do not know yet '
                             'what you will do with a list of everybody Aoyama '
                             'stopped counting, and you know you were not going '
                             'to let it go unread.',
                             sets=('unmade_kept',)),
                  )),
            Stage('after', 'The word the architecture does not have',
                  'You can unmake a thing, not just remove it, which most '
                  'runners cannot and most systems are not built to survive, '
                  'and the Green found that out, once, from you, and the file '
                  'that could not stop growing stopped. It is a quiet thing to '
                  'be good at. It is quiet the way a thing is quiet after.',
                  requires=(),
                  any_of=('unmade_rest', 'unmade_kept'),
                  sets=('unmade_over',)),
        )),
)


#: What working with somebody puts in your bag (D63 e). Two of the seven:
#: the Quiet Kid's route file and Grieve's desk. The rest give the hire
#: price, which is also a gift, and the ending.
PARTNER_GIFTS: dict[str, tuple[str, ...]] = {
    'quietkid': ('nobody',),
    'grieve': ('desk',),
    'saint': ('reliquary',),
    'moth': ('lantern',),
}


def _runner_stages() -> tuple[Stage, ...]:
    out = []
    for key, name, partner, yes, apart, nemesis, pay, stand in _RUNNER_SCENES:
        out.append(Stage(
            f'{key}_partner', f'{name} has decided',
            partner,
            requires=(f'bond:{key}:partner',),
            sets=(f'asked_{key}',),
            choices=(
                Choice('in', 'Work with them', yes, sets=(f'with_{key}',),
                       gives=PARTNER_GIFTS.get(key, ())),
                Choice('apart', 'Keep it professional', apart,
                       sets=(f'apart_{key}',)),
            )))
        out.append(Stage(
            f'{key}_nemesis', f'{name} names a figure',
            nemesis,
            requires=(f'bond:{key}:nemesis',),
            sets=(f'priced_{key}',),
            choices=(
                Choice('pay', f'Pay them ({BUYOFF:,}c)', pay,
                       sets=(f'paid_{key}',), credits=-BUYOFF),
                Choice('stand', 'Let it stand', stand,
                       sets=(f'stood_{key}',)),
            )))
    return tuple(out)


RUNNER_THREAD = Thread(
    'runners', 'The Other Runners',
    'Seven people doing what you do, and what each of them decided about '
    'you.',
    crosses=(),
    stages=_runner_stages())
