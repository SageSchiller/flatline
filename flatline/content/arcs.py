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
        crosses=('theirs',),
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
                  requires=('met:vance',),
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


def _runner_stages() -> tuple[Stage, ...]:
    out = []
    for key, name, partner, yes, apart, nemesis, pay, stand in _RUNNER_SCENES:
        out.append(Stage(
            f'{key}_partner', f'{name} has decided',
            partner,
            requires=(f'bond:{key}:partner',),
            sets=(f'asked_{key}',),
            choices=(
                Choice('in', 'Work with them', yes, sets=(f'with_{key}',)),
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
