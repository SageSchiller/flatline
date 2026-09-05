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

from .threads import Choice, Posting, Stage, Thread

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
                  requires=('met:osei', 'skill:cryptography:3'),
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
                  requires=('record:15',),
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
                  requires=('reckoner_heard', 'record:20'),
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
