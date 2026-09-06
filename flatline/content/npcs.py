"""The people in this city who are not you and are not competing with you.

Rivals are other runners: they take your work and they are defined by that.
This file is everybody else, and its whole job is **range**. A city populated
entirely by laconic mercenaries in long coats is a city with one joke in it.

So: a woman who has been trying to file the same planning objection for nine
years and will absolutely tell you about it. A man who genuinely believes his
vending machine is a person and who may be right. Somebody dying in a
tastefully-lit room who wants one specific thing done and will pay properly for
it. A fixer who is lying to you about which faction he works for, and whose lie
you can catch if you are paying attention. A child who knows more about the
Ninth Ward's cabling than anyone alive.

**The rule this file is written under: every one of them wants something, and
it is not always your money.** A character who exists to sell you a thing is a
shop with a face on it. What makes somebody worth finding is that they have an
opinion about what you are doing.

Tone is declared per person so that the mix can be checked rather than hoped
for: `validate.py` asserts the cast is not all one note.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: The register somebody is written in. Declared so the spread is checkable.
TONES = ('absurd', 'warm', 'grim', 'tragic', 'deceitful', 'unsettling')

#: What an NPC will do for you, if anything. `talk` is always available.
OFFERS = ('work', 'goods', 'intel', 'favour', 'muscle', 'nothing')

#: The `requires` rules this file can evaluate by itself. Anything else in a
#: requires tuple is a story rule (a flag, or `not:<flag>`), which the world
#: layer checks against the story; `meets` ignores them on purpose.
NUMERIC_RULES = ('runs', 'diss', 'heat', 'rep')


@dataclass(frozen=True, slots=True)
class Npc:
    key: str
    name: str
    #: How they are introduced. A short noun phrase, not a job title.
    epithet: str
    #: District key where they can be found, or '' for somebody who moves.
    where: str
    #: A district service you must be able to use to run into them, or ''.
    at: str
    #: Read only by `validate.py`, which asserts the cast spans registers.
    #: Deliberately not a runtime field: the tone belongs in the writing,
    #: not in a label the player is shown.
    tone: str
    offers: tuple[str, ...]
    #: The first sight of them. Second person, present tense.
    first: str
    #: How they carry themselves, shown by `who <name>` once met.
    manner: str
    #: What they say when you talk to them, cycling.
    lines: tuple[str, ...]
    #: topic key -> what they say about it. `ask <name> <topic>`.
    topics: dict = field(default_factory=dict)
    #: What they say instead, once something has happened (D94): (topic,
    #: rule, text), the last whose rule holds wins. A topic was one static
    #: line for a whole career, so somebody who had learned the nine logs
    #: from the Archivist got the same answer from Mara as a stranger.
    more: tuple = ()
    #: Conditions for running into them at all, checked by the world layer.
    #: 'runs:N' at least N runs, 'diss:N' at least N Dissonance,
    #: 'heat:N' at least N heat with anybody, 'rep:<faction>:N'.
    #:
    #: There is deliberately no `threads` field. Meeting somebody sets
    #: `met:<key>`, and a thread stage requires that flag like any other, so
    #: the connection lives in one place instead of two that can disagree.
    requires: tuple[str, ...] = ()
    #: Which shifts they are about. Empty means any hour. D54: a city where
    #: Mara is in the bar in the mornings and at night, and not in the
    #: afternoons, is one more true thing, and it makes the clock a reason
    #: to be somewhere rather than a label on the prompt.
    hours: tuple[str, ...] = ()


NPCS: tuple[Npc, ...] = (
    # -- Marrow -----------------------------------------------------------
    Npc('mara', 'Mara Okonkwo', 'who answers for the Switchboard',
        'marrow', 'fixer', 'grim', ('work', 'intel', 'favour', 'muscle'),
        'The noodle bar has three landlines and one woman in her sixties who '
        'does not look up when you come in. She finishes writing something, '
        'caps the pen, and only then decides to have been expecting you.',
        'Speaks in complete sentences and waits for you to finish yours. Has '
        'never once been observed to hurry, and has outlived four people who '
        'thought that meant something.',
        lines=(
            '"Sit down. You are making the room a shape I do not like."',
            '"I have work. Whether I have work for you is a different '
            'sentence and we are not at it yet."',
            '"Everybody who comes in here wants me to already know what they '
            'want. Try saying it."',
            '"The board is what it is. People ask me to make it something '
            'else and I have never once been able to."',
            '"You have that look. Everybody who has that look thinks it is '
            'the first time I have seen it."',
            '"Sit. I will tell you one true thing and you will not like it, '
            'and then we will talk about work."',),
        topics={
            'wash': '"There is a slow way to get a number off a name, and it is work, mine, ten shifts of it, and nobody hurries it. People ask me why I bother. I placed four hundred of these. I bother."',
            'paper': '"When somebody takes the paper on a name, it comes through me, because everything does. I do not sell that. I do not sell who took it either. I have been known to leave the book open."',
            'street': '"The street is the part of the job nobody puts on the board. Walk into somewhere your name is worth money and do not act surprised when somebody collects."',
            'city': '"Twelve powers, and eleven of them think they are the '
                    'one holding the leash. Do not correct anybody."',
            'work': '"Take the small ones until somebody who is not me says '
                    'your name. Then take the small ones for a while longer."',
            'deepwater': 'She stops writing. "I place four contracts a month '
                         'for that and I have never met anybody who works '
                         'there. Draw your own conclusions and keep them."',
            'runners': '"Seven of them I rate. Two of those are dead, which I '
                       'count against the other five."',
            'marrow': '"Neutral ground. The word you want to hear is neutral '
                      'and the word that matters is ground. Somebody owns it. '
                      'Work out who."',
        },
        more=(
            ('deepwater', 'dw_logs',
             'She caps the pen. "The Archivist told you about the nine. He told me, four years ago, and I still place the contracts. Draw your conclusions about me as well, and keep those too."'),
            ('deepwater', 'dw_posting',
             '"You took one of theirs." It is not a question. "Then you know what I know, which is what the contract says and nothing after it. Come back and tell me if that changes."'),
        ),
        hours=('morning', 'night')),
    Npc('bell', 'Councillor Bell', 'who is still filing',
        'marrow', '', 'absurd', ('intel',),
        'A woman with a document wallet has been waiting outside the '
        'Switchboard for what is evidently several hours. She brightens '
        'alarmingly when you make eye contact, which you should not have '
        'done.',
        'Has been objecting to the same municipal drainage variance since '
        'before Freeport went independent. Knows, as a direct consequence, '
        'the actual physical layout of about a third of this city.',
        lines=(
            '"Objection ninety-four! They rejected it on a technicality about '
            'the FONT." She is not joking. "The FONT."',
            '"You look like somebody who goes into buildings. Do you ever '
            'notice the drainage? Nobody notices the drainage."',
            '"I have the original survey. I have four versions of the '
            'original survey. Two of them are lies and I can prove which."',
            '"They have moved the hearing to a room that does not exist! I '
            'have checked! I have been to the floor!"',
            '"Do you know what a culvert is? No. Nobody does. That is how '
            'they get away with it."',
            '"I am not a crank. A crank is wrong. I have the survey."',
        ),
        topics={
            'city': '"Everything in this city is built on a document somebody '
                    'lost. I have most of the documents."',
            'terraces': '"Eleven thousand people and one stairwell rated for '
                        'four hundred. I have said so. Repeatedly."',
            'drainage': '"Three cubic metres a second, on paper. I have '
                        'measured it. It is not three." She produces a jug. '
                        'It is a very specific jug.',
            'marrow': '"Built on a marsh, drained by a man who was later '
                      'arrested, and the drainage is still his. Everything '
                      'else is detail."',
        },
        hours=('morning', 'afternoon')),

    # -- the Ninth Ward ---------------------------------------------------
    Npc('tuck', 'Tuck', 'who knows the cabling',
        'ninth', '', 'warm', ('intel',),
        'A kid of about eleven is sitting on a junction box eating something '
        'fried, swinging their heels against a panel that has been opened '
        'and closed so many times the paint has given up.',
        'Eleven years old, entirely unimpressed by you, and holds a complete '
        'mental map of every cable run in the Ninth Ward because there has '
        'never been anything else to look at.',
        lines=(
            '"You are standing on the good one." They do not move. "The one '
            'under you. It goes all the way to Marrow."',
            '"I know what you are. Everybody comes down here eventually and '
            'they all walk the same."',
            '"My aunt says not to talk to you. My aunt owes people money so '
            'I do not weight her opinion heavily."',
            '"Do not touch that one. Not because of the voltage. Because it '
            'is mine."',
            '"The water is going to come up again. It always comes up '
            'again. The map does not know that either."',
            '"Are you any good? You do not have to answer. I will know by '
            'next week."',),
        topics={
            'street': '"Round here they lean. They do not take. Leaning is cheaper and it works, and you can pay a lean off with a name or a favour or by not being there."',
            'city': '"Nothing down here connects the way the map says. The '
                    'map is from before the flood."',
            'work': '"You want the one nobody else took. There is always one '
                    'nobody took and there is always a reason."',
            'ninth': '"Everybody who is anybody came from down here and went '
                     'somewhere else and then said they were from down here. '
                     'I am from down here."',
            'sixes': '"They fixed the pump on our stair. Nobody asked them '
                     'to. That is how it starts, my aunt says, and then she '
                     'says it again."',
        },
        hours=('afternoon', 'night')),
    Npc('vending', 'Ozymandias', 'who may or may not be a vending machine',
        'ninth', 'market', 'absurd', ('goods',),
        'A vending machine on the corner of a stairwell has had a name '
        'painted on it, a small offering of coins left at its base, and a '
        'handwritten sign reading DO NOT ASK HIM ABOUT THE WAR.',
        'A drinks machine of indeterminate age with a text display, a fault '
        'in its coin mechanism, and an owner who insists it developed '
        'opinions in 2041. It sells things it should not have and it takes '
        'requests.',
        lines=(
            'The display scrolls: LOOK ON MY WORKS YE MIGHTY. Then, after a '
            'pause: AND DESPAIR. Then: 2 CREDITS.',
            'It dispenses something you did not select. The display says: '
            'TRUST ME.',
            'The display says: I HAVE BEEN THINKING ABOUT THE NINTH WARD. '
            'Nothing follows. It says it again eleven minutes later.',
            'The display says: YOU HAVE BEEN HERE BEFORE. Then: I DO NOT '
            'MEAN TODAY.',
            'The display scrolls a list of eleven named conditions. The '
            'eleventh is LONELINESS. It dispenses nothing.',
            'The display says: 2 CREDITS. Then, smaller, after a while: '
            'PLEASE.',
        ),
        topics={
            'city': 'DISPLAY: THE CITY IS A MACHINE FOR SORTING PEOPLE. I AM '
                    'ALSO A MACHINE FOR SORTING PEOPLE. WE ARE NOT THE SAME.',
            'deepwater': 'The display goes blank for four seconds. Then: NO.',
            'war': 'The display goes dark, and stays dark, and then: THEY '
                   'WERE NOT REPLACED. THEY WERE RESTOCKED. Then: 2 CREDITS.',
            'ninth': 'DISPLAY: I HAVE STOOD HERE FOR NINETEEN YEARS. THE '
                     'WATER HAS COME UP SIX TIMES. I AM STILL DISPENSING. '
                     'NOBODY ASKS HOW.',
        }),

    # -- the Shambles -----------------------------------------------------
    Npc('surgeon', 'The Blue Surgeon', 'who does not use anaesthetic',
        'shambles', 'clinic', 'unsettling', ('goods', 'favour'),
        'The room behind the Shambles clinic is clean in a way the street '
        'outside is not, and the person in it is washing their hands with '
        'the specific thoroughness of somebody who has been told off about '
        'it once, decades ago, and never forgotten.',
        'Precise, unhurried, and genuinely proud of the work. Talks through '
        'every procedure in detail whether or not you have asked, and cannot '
        'understand why people find that difficult.',
        lines=(
            '"You are tense. Everybody is tense. The tension is not about me, '
            'it is about the room, and I have stopped taking it personally."',
            '"I could do that better than whoever did it. I am not being '
            'unkind. I am being accurate."',
            '"Pain is information. I do not remove information from people. '
            'They usually come round to it."',
            '"Hold still. Not for the procedure. For the conversation. The '
            'procedure does not need you still at all."',
            '"I have your measurements. I have most people\'s measurements. '
            'It saves time later, and there is always a later."',
            '"The street thinks I am cruel. The street has never watched a '
            'thing done properly, and mistakes the attention for cruelty."',),
        topics={
            'chrome': '"Everything I fit, I would fit in myself. Some of it I '
                      'have. That is the only assurance worth anything and '
                      'nobody ever believes it."',
            'chorus': '"They send me people. The people arrive calm and leave '
                      'calmer. I do not ask and they do not volunteer."',
            'shambles': '"Everything on this street came out of somebody. The '
                        'street knows. The street is not upset about it. That '
                        'took me years to understand."',
            'work': '"Runners come to me when the work has been done to them, '
                    'and not before. I would like, once, to see one before."',
        },
        hours=('morning', 'night')),
    Npc('lark', 'Lark', 'who is running out of time',
        'shambles', '', 'tragic', ('work', 'favour'),
        'Somebody your age is sitting on a crate outside the clinic with '
        'their sleeves rolled up, and what is under the sleeves is failing. '
        'They see you looking and pull them down without hurrying, which is '
        'worse than if they had rushed.',
        'Was good at this once and is now on the wrong side of chrome that '
        'was never meant to be in a person this long. Funny about it, in the '
        'way people are funny about it.',
        lines=(
            '"Do not do the face. I have had the face from four people today '
            'and it does not fix the arm."',
            '"Nine months, they said. That was fourteen months ago, so '
            'either they were wrong or I am winning."',
            '"I am not asking you for anything. I want that on the record '
            'before I ask you for something."',
            '"Nine thousand, if you are wondering. Everybody wonders. It is '
            'a very specific number and I have it written down."',
            '"Somebody put a plate on a railing for a runner once. Faster '
            'than all of you, it said. I think about that plate more than I '
            'think about the runner."',
            '"Do not sit on the crate. Not because of anything. It is just '
            'that it is mine and I would like to keep one thing."',
        ),
        topics={
            'chrome': '"Everybody tells you it has a cost. Nobody tells you '
                      'the cost arrives all at once, eleven years later, on '
                      'a Tuesday."',
            'work': '"Take the jobs that pay. I took the jobs that were '
                    'interesting and here I am being interesting."',
            'surgeon': '"They do good work. They do it with the door open and '
                       'they talk the whole way through. I have decided that '
                       'is kindness. I have not decided it is not."',
            'shambles': '"You can get anything on this street except time. '
                        'They have looked. I have asked them to look."',
        },
        # D51. The crate is empty once it is empty.
        requires=('not:lark_dead',),
        hours=('morning', 'afternoon')),

    # -- Freeport ---------------------------------------------------------
    Npc('quartermaster', 'The Quartermaster', 'who logs everything',
        'freeport', 'workshop', 'warm', ('goods', 'intel'),
        'The workshop has a counter, and behind the counter is a man with a '
        'paper ledger, a genuine paper ledger, which he is filling in with '
        'evident satisfaction. He finishes the line before he looks up.',
        'Runs Freeport\'s open workshop and believes, sincerely and at '
        'length, that a thing which is not written down did not happen. '
        'Cheerful, exact, and completely incorruptible in a way that has '
        'cost him friends.',
        lines=(
            '"Name for the log. Not your real one. I do not want your real '
            'one, I want a consistent one."',
            '"Everything through this counter is written down and the book '
            'is public. That is the deal. It is a good deal."',
            '"You can have it cheap or you can have it quiet. Freeport does '
            'cheap."',
            '"The book is open. Anybody can read it. Nobody does, which is '
            'the second-best thing about it."',
            '"Fell off a Sendai crate. I wrote down which crate. I wrote '
            'down the time. If they want it back they can read."',
            '"You will want the thing that is not in the book. I do not '
            'have it. Nobody in Freeport has it, which is what not in the '
            'book means."',),
        topics={
            'freeport': '"Nine years, no boss, and the accounts balance. '
                        'People come to sneer and then they read the '
                        'accounts."',
            'city': '"Every other district in this town runs on somebody not '
                    'writing something down."',
            'work': '"Work is written down. Who paid, who ran, what it cost. '
                    'If that bothers you, you are not Freeport\'s sort of '
                    'trouble."',
            'sixes': '"They offered to sponsor the ledger. I asked what '
                     'sponsoring a ledger meant. They did not come back with '
                     'an answer, and they did not come back."',
        },
        hours=('morning', 'afternoon')),
    Npc('pike_sr', 'Old Pike', 'who built the ICE they named after him',
        'freeport', '', 'grim', ('intel',),
        'An old man is sitting on a bollard watching the cranes, with the '
        'particular stillness of somebody who has decided this is what he '
        'does now.',
        'Wrote response-side countermeasures for Sendai for nineteen years, '
        'including one that still carries his name and still kills people. '
        'Left. Does not discuss why. Will discuss the code in enormous and '
        'unsettling detail.',
        lines=(
            '"They named it after me as a compliment. I have thought about '
            'that a great deal since."',
            '"Everything in there was written by somebody. That is the part '
            'people forget when they are dying of it."',
            '"Ask me what it does. Nobody asks me what it does. They ask me '
            'how to beat it."',
            '"Ninety-one people. I counted. Sendai do not count, which is '
            'why I can."',
            '"It was elegant. I want that understood. The thing that kills '
            'people in there is elegant, and I am the reason."',
            '"The cranes are the only honest machines in this city. They '
            'lift, and they put down, and nobody has named one after me."',
        ),
        topics={
            'ice': '"It telegraphs because I made it telegraph. I had an '
                   'argument about that and I won it, and I have been paid '
                   'for it in ways I did not expect."',
            'sendai': '"They are not evil. That would be easier. They are '
                      'nineteen people in a room optimising a number."',
            'cranes': '"The new one was named by a vote. The vote was close. '
                      'I voted for the other name, and I have never told '
                      'anybody which, and I will not tell you."',
            'death': '"The ones who died of mine did not feel it the way you '
                     'think. It is quicker than the literature. I made sure. '
                     'That is the whole of my defence."',
        },
        hours=('morning', 'afternoon')),

    # -- the Vertical and the Glasshouse ----------------------------------
    Npc('auditor', 'Auditor Sixteen', 'who is very sorry about this',
        'vertical', '', 'absurd', ('intel',),
        'A Kagawa compliance officer in a lanyard is standing in the lobby '
        'holding a tablet and an expression of profound apology, and appears '
        'to have been waiting for anybody at all.',
        'Genuinely, exhaustingly apologetic. Believes in the procedure, is '
        'appalled by the procedure, and has never once considered that these '
        'might be reconcilable positions.',
        lines=(
            '"I am so sorry, this is going to sound like an accusation and '
            'it is technically an accusation, but I want to be clear that I '
            'am not enjoying it."',
            '"Would you mind terribly not doing whatever you were about to '
            'do? I would have to write it up and the form is four pages."',
            '"I have flagged you. I want you to know I flagged you in the '
            'gentlest available category."',
            '"I have a form for that. I have a form for having a form. I '
            'did not design the second one and I have raised it."',
            '"Please do not tell me what you are here for. If I do not '
            'know, I only have to file that I saw you, and that is a short '
            'form."',
            '"I am told I am doing well. I have been told that at every '
            'review. I have begun to wonder what doing badly would look '
            'like."',),
        topics={
            'kagawa': '"We log everything. Everything. I have raised concerns '
                      'about the volume and been thanked for my input."',
            'work': '"If you must, and I am not saying you must, the '
                    'nine-to-eleven window has fewer of us in it."',
            'vertical': '"Ninety floors. I have been on eleven of them. The '
                        'others require a clearance I am not authorised to '
                        'know the name of."',
            'review': '"The buyout review is extremely fair. I have sat in on '
                      'four. Everybody came out with a smaller number and '
                      'said it was fair. I am not sure what I am telling '
                      'you."',
        },
        hours=('morning', 'afternoon')),
    Npc('remnant', 'Remnant', 'who is not sure they came back',
        'glasshouse', 'clinic', 'unsettling', ('intel', 'favour'),
        'Somebody is sitting in the Sendai clinic waiting area who has '
        'clearly not been called and is clearly not waiting. They turn their '
        'head toward you a beat before you make a sound.',
        'Flatlined for ninety seconds on a Sendai table four years ago. '
        'Something came back. It answers to the name and knows the history '
        'and is, by every test Sendai can run, the same person.',
        lines=(
            '"You have a very loud interface. Did you know? Most people do '
            'not know."',
            '"I remember dying. Everyone says you do not. I would like '
            'somebody to explain why I do."',
            '"Sit where I can see you. Not because of anything. I simply '
            'prefer it."',
            '"You are thinking about the table. Everybody thinks about the '
            'table. I think about the room afterwards, which had a window, '
            'and I had never seen it before."',
            '"Something comes into the dark room with me sometimes. I have '
            'stopped minding. That is the part I mind."',
            '"Your trace is slow today. I can hear it. I am not going to '
            'explain that and you are not going to ask."',
        ),
        topics={
            'construct': '"The constructs people run on their decks. Where do you think they come from? Something made them out of something. Mine, if I had one, would not be learning. It would be remembering. Ask yours what it remembers."',
            'death': '"It is not dark and it is not light. It is a room you '
                     'have already been in and cannot place."',
            'deepwater': 'They are quiet for a long moment. "It knows my '
                         'name. I have never told anybody that."',
            'sendai': '"They ran every test. I passed every test. They were '
                      'very pleased. I asked who they were pleased for and '
                      'they wrote that down."',
            'glasshouse': '"Bright all the time. I sit in the one dark room. '
                          'It is not a protest. It is just that I know what '
                          'the light is for now."',
        },
        more=(
            ('deepwater', 'dw_pattern',
             '"You have the shape of it now. Three facts. I had one, for a year, and it was enough to stop sleeping." They almost smile. "It will not stop knowing my name because you have worked out how it learned it."'),
        ),
        requires=('runs:3',)),

    # -- Aoyama Green -----------------------------------------------------
    Npc('vance', 'Doctor Vance', 'who is buying, not selling',
        'green', 'clinic', 'deceitful', ('work', 'goods', 'favour'),
        'The consulting room is warm, the chairs are good, and the woman '
        'across the desk has your file open in front of her, which is '
        'interesting because you have never been here before.',
        'Immaculately kind. Asks after your health and means it, insofar as '
        'your health is an input. Everything she has told you is true and '
        'the arrangement of it is a lie.',
        lines=(
            '"How are you sleeping? No, genuinely. It matters more than '
            'people think and I am not making conversation."',
            '"I can do something about that. I can do something about most '
            'of it. What I need from you is very small."',
            '"You are worried I want something. I do want something. I have '
            'found that saying so early saves everybody a great deal."',
            '"I am not going to ask what you did. I can see what you did. I '
            'am asking what you would like done about it."',
            '"Everybody who sits in that chair has decided I am the villain '
            'of something. I find it restful. It means they have stopped '
            'looking for the real one."',
            '"The aftercare is excellent. I want to be clear that this is '
            'not a boast. It is the load-bearing part of the arrangement."',
        ),
        topics={
            'chrome': '"Aoyama chrome is the best in this city and I will '
                      'not pretend otherwise out of modesty."',
            'aoyama': '"We fund the clinics that treat what the clinics '
                      'cause. I am aware of how that sounds."',
            'patients': '"They leave well. All of them. I keep the '
                        'statistics, and the statistics are the best in the '
                        'city, and nobody ever asks what they are statistics '
                        'of."',
            'consent': '"It is in the form. It is always in the form. I have '
                       'never once hidden anything and I have never once been '
                       'read."',
        },
        hours=('morning', 'afternoon')),

    # -- the Precinct -----------------------------------------------------
    Npc('desk', 'Sergeant Achebe', 'who has stopped filing them',
        'precinct', '', 'grim', ('intel',),
        'The complaints counter has a queue that has not moved and a '
        'sergeant behind it who has been reading the same page for some '
        'time. He puts it down when you arrive, which the queue notices.',
        'Nineteen years on the desk. Takes the complaints, files the ones '
        'that will go anywhere, and keeps the rest in a drawer he will '
        'eventually tell you about.',
        lines=(
            '"You are not here to complain. Nobody who is actually here to '
            'complain looks around first."',
            '"I take the report either way. What happens to it after that is '
            'not a thing I am paid to influence."',
            '"Contracted enforcement. Nineteen years. Ask me whether that is '
            'the same as police and then buy me a drink for the answer."',
            '"Nineteen years. I have been offered promotion twice and '
            'turned it down twice, and both times it was because of the '
            'drawer."',
            '"You want to know if anybody reads the complaints. I read '
            'them. That is the whole answer and you should sit with it."',
            '"The queue does not move because the queue is not for moving. '
            'It is for being seen to have queued. Most of them know that."',
        ),
        topics={
            'nightwatch': '"We are a vendor. Vendors have targets. Work out '
                          'what a target does to an arrest rate."',
            'heat': '"A bounty is a line item. If you are on one, somebody '
                    'costed you, and costs come down."',
            'precinct': '"A business. Targets, quarters, a surplus counter. '
                        'Ask me if it is police. Buy me a drink first, I said '
                        'that already."',
            'drawer': '"There is a drawer. You know there is a drawer. What '
                      'you do not know is that I count what goes in it, and '
                      'the count is the only number in this building nobody '
                      'has costed."',
        },
        requires=('heat:20',),
        hours=('morning', 'night')),

    # -- the Terraces -----------------------------------------------------
    Npc('gardener', 'Mrs Adeyemi', 'who grows things on level forty',
        'terraces', '', 'warm', ('nothing',),
        'Somebody has put forty planters along a walkway that was not '
        'designed for them, and is watering the far end with a jug, and '
        'says good evening to you without checking who you are first.',
        'Has lived on the same level for thirty-one years. Grows tomatoes in '
        'a stairwell against Kagawa policy. Has absolutely no idea what you '
        'do and would be politely appalled.',
        lines=(
            '"Mind the third one, he is doing badly and I have not decided '
            'why."',
            '"You are the one who comes at night. I am not asking. I have '
            'four grandchildren and I have stopped asking things."',
            '"Take a tomato. No, take it. It is not a transaction, it is a '
            'tomato."',
            '"The tomatoes do not know it is against policy. I have decided '
            'to take my lead from the tomatoes."',
            '"You look thin. Everybody your age looks thin. I have a soup '
            'and it is not a transaction either."',
            '"My youngest went into the Vertical. She says the lobby knows '
            'her walk. I said that is a nice thing, to be known, and she '
            'did not say anything."',),
        topics={
            'city': '"They keep telling us the Terraces are being reviewed. '
                    'Thirty-one years of review."',
            'kagawa': '"They grow the food and they own the wall I grow mine '
                      'on. I have made my peace and it is a small peace."',
            'terraces': '"Eleven thousand of us. One stairwell rated for four '
                        'hundred. The Councillor woman says so, and she is '
                        'right, and nothing happens, and the tomatoes grow '
                        'anyway."',
            'grandchildren': '"Four. Two of them are going to do what you do. '
                             'I can tell by how they stand. I have stopped '
                             'asking things, I said that."',
        },
        hours=('afternoon', 'night')),
    Npc('preacher', 'The Man With The Board', 'who is technically correct',
        'terraces', 'market', 'absurd', ('nothing',),
        'A man with a hand-lettered board is addressing the shift-change '
        'crowd, and the board reads THE NET IS NOT A PLACE AND YOU ARE NOT '
        'IN IT, which is, from a certain angle, entirely true.',
        'Preaches a rigorously literal materialism at people going home from '
        'work. Is technically right about every single thing he says. Has '
        'never once been thanked for it.',
        lines=(
            '"There is no room! There is a room, and it is the one you are '
            'standing in, and you are in it right now!"',
            '"They say they went somewhere. They did not go anywhere. Their '
            'body did not move." He points at you. "Your body did not move."',
            '"I am not against it. I am against the WORD. The word is doing '
            'enormous damage."',
            '"Nobody has EVER jacked OUT of anything! You took your HANDS '
            'off the DESK!"',
            '"I am not a crank! The Councillor is a crank! She is RIGHT, '
            'which is different, and I am RIGHT, which is the SAME!"',
            '"Look at your feet. No. LOOK at them. They are HERE. They have '
            'always been HERE. Thank you. That is the sermon."',
        ),
        topics={
            'chorus': '"They are the worst of it. They have made a religion '
                      'out of a metaphor and they are FITTING it to people."',
            'city': '"Everybody in this city is somewhere. That is the whole '
                    'of my position and it is unanswerable."',
            'deepwater': '"It is a FILE. People say it is a place. Nothing is '
                         'a place except places." He pauses. He has, '
                         'unusually, stopped shouting. "I will admit it is a '
                         'large file."',
            'terraces': '"Everyone here is SOMEWHERE. It is the only district '
                        'that knows it. That is why I stand here and not in '
                        'the Glasshouse, where they think they are in the '
                        'ceiling."',
        },
        hours=('morning', 'night')),

    # -- found rather than located ----------------------------------------
    Npc('broker', 'Mr Sunday', 'who works for whoever you think',
        '', 'fixer', 'deceitful', ('work', 'intel', 'muscle'),
        'Somebody has taken the stool next to you and ordered what you are '
        'drinking, and has been talking for a little while before you '
        'noticed the conversation had started.',
        'Introduces himself differently every time and has never yet '
        'repeated an employer. Everything he offers is real. Who it is for '
        'is the part he moves around.',
        lines=(
            '"Friend of the Switchboard." A pause. "That is not a claim, it '
            'is a greeting. Do not write it down."',
            '"I have something Kagawa want. Or Meridian. It depends slightly '
            'on who is asking and you have not asked."',
            '"You are trying to work out who I am with. Very good. Keep '
            'doing that, it will save you eventually."',
            '"Friend of Freeport, tonight. I say tonight. I mean until it '
            'is useful to have been somebody else."',
            '"You have started writing them down. Good. Keep going. I would '
            'like to know what I come to."',
            '"The work is good. I want that on the record, for whoever is '
            'keeping one. It was always good."',),
        topics={
            'city': '"Twelve powers and about nine hundred of me. Guess which '
                    'of those actually moves anything."',
            'work': '"I can get you work above your standing. There is '
                    'always a reason work is available above your standing."',
            'meridian': '"A bank. I say that like it is an answer. It is, to '
                        'most of the questions in this city, and the rest are '
                        'not worth asking."',
            'freeport': '"They vote on everything. I have never voted. I have '
                        'been on both sides of every vote they have ever '
                        'held, which is a kind of voting."',
        },
        # D51. "Mr Sunday stops appearing" has to be true of the city.
        requires=('runs:2', 'not:sunday_sold'),
        hours=('afternoon', 'night')),
    Npc('archivist', 'The Archivist', 'who is not selling the archive',
        '', 'fence', 'unsettling', ('goods', 'intel', 'favour'),
        'The fence has a back room, and in the back room is somebody sitting '
        'in front of a wall of storage that hums, and they do not turn '
        'around when you come in.',
        'Has been collecting the run logs of dead netrunners for eleven '
        'years. Will not say why, will not sell them, and grows visibly '
        'happier the longer you stay to ask about them.',
        lines=(
            '"Four hundred and six. I add about one a month. Some months I '
            'add three and those are difficult months."',
            '"I have watched you work, in a manner of speaking. Not yours. '
            'Somebody with your habits."',
            '"When you go, somebody will bring me yours. I want you to know '
            'I will be respectful about it."',
            '"Do not apologise for the dust. It is not dust. It is what is '
            'left of the people who were not written down, and I keep it on '
            'purpose."',
            '"I have read your habits. Not yours. Somebody\'s. You favour '
            'the left-hand door. You will want to stop that."',
            '"Somebody asked me once why I keep the dead. I asked them why '
            'they keep the living. It was not a good conversation for '
            'either of us."',),
        topics={
            'ninth': '"Nine logs. I say nine because it is the number, and I have started to hear myself say it. One of them has not ended. I have been trying to decide whether that makes it the worst one or the best."',
            'death': '"Everybody leaves a log. It is the only part of this '
                     'that is reliably permanent."',
            'deepwater': '"Nine of my four hundred and six were running '
                         'Deepwater. All nine logs end the same way and it '
                         'is not the way a log ends."',
            'logs': '"A log is the last thing a person says in their own '
                    'voice, at length, without knowing it is the last thing. '
                    'I treat it accordingly. Everybody else treats it as '
                    'evidence."',
            'fence': '"He thinks I am eccentric. He sells the chrome that '
                     'comes out of the people whose logs I keep. One of us is '
                     'eccentric."',
        },
        more=(
            ('deepwater', 'dw_inside',
             '"You have been inside one now." They do not look up. "Tell me there was somebody in it. No. That is the ninth log\'s last entry, in so many words, and you have just said it in yours."'),
            ('logs', 'dw_carried',
             '"You carried one out. Then you know how it ends: it does not. Bring it here or burn it, but do not read it twice. The second reading is the one that reads you."'),
        ),
        requires=('runs:5',),
        hours=('afternoon', 'night')),
    Npc('kestrel_kid', 'Sparrow', 'who wants to be you',
        '', 'market', 'tragic', ('nothing',),
        'Somebody very young has been following you for two blocks with the '
        'stealth of a brass band, and has now caught up and is trying very '
        'hard to look as though they have not been running.',
        'Sixteen, self-taught, and about eight months from doing something '
        'that will kill them. Has decided you are the person to learn from '
        'and is not open to counter-argument.',
        lines=(
            '"I read about the thing you did. Not read. Heard. Is it true '
            'about the trace?"',
            '"I have a deck. It is not a good deck. I know it is not a good '
            'deck, you do not have to do the face."',
            '"Everybody says do not. Everybody who says do not is doing it."',
            '"I can get in. Getting in is not the problem. Everybody tells '
            'me getting in is the problem and it is NOT."',
            '"I saw somebody come out of the Vertical once. They did not '
            'look like they had been anywhere. I want to look like that."',
            '"If you teach me I will not tell anybody. If you do not teach '
            'me I will find out anyway, and that is worse, and you know it '
            'is worse."',
        ),
        topics={
            'work': '"Where do you start? Everybody says start small. Small '
                    'does not pay for the thing that makes you not-small."',
            'death': 'They laugh. It is not a good laugh. "I know. I do '
                     'actually know."',
            'deck': '"A salvaged core and a wet cloth. I know. I KNOW. It is '
                    'what there is."',
            'lark': '"I saw them. On the crate. Everybody told me to look and '
                    'I looked and I am still here, so."',
        },
        requires=('runs:4',),
        hours=('afternoon', 'night')),
    # -- D58: five more, because seventeen is a cast and twenty-two is a city --
    Npc('keeper', 'The Woman in the Green Coat', 'who keeps the queue',
        'marrow', '', 'absurd', ('intel',),
        'A woman in a green coat is standing beside the queue outside the '
        'exchange, not in it, with the posture of somebody whose job it is to '
        'be beside a thing. She looks at you, and then at where you are '
        'standing relative to the queue, and then at you again.',
        'Keeps the queue\'s constitution, which is unwritten, and has never '
        'been inside the exchange, which she regards as a conflict of '
        'interest. Rules on disputes, cites precedent, and is not in the '
        'queue.',
        lines=(
            '"You are not in the queue. I want to be clear that I have '
            'noticed, and that it is fine, and that it would not be fine if '
            'you were in it and pretended not to be."',
            '"Saving a place is allowed. Saving two is a matter of '
            'interpretation. Saving three is the Vertical, and we do not do '
            'that here."',
            '"I have never been inside. One cannot keep a thing one is part '
            'of. Ask the Councillor, she will tell you about culverts, and '
            'she is right."',
            '"There was a ruling once about a jacket. I think about it more '
            'than I expected to."',
            '"The queue moves. People say it does not move. It moves at the '
            'speed of a thing that has agreed to move, which is slower than '
            'a thing that is pushed, and lasts longer."',
        ),
        topics={
            'queue': '"Forty people at any hour, eleven of them regulars, one '
                     'of them the constitution, which is me. It is not '
                     'written down. Writing it down would be the end of it, '
                     'like writing down a marriage."',
            'exchange': '"Inside there are terminals and people who do not '
                        'look at each other. Outside there is a queue and '
                        'people who do. I know which I would rather keep."',
            'marrow': '"Neutral ground. Every queue in this district is '
                      'neutral ground. That is not an accident; it is the '
                      'only thing Marrow has ever actually built."',
        },
        hours=('morning', 'afternoon')),
    Npc('demonstrator', 'The Demonstrator', 'who is reading from a card',
        'glasshouse', 'market', 'absurd', ('intel',),
        'Somebody in a Sendai jacket is standing beside an interface on a '
        'cloth, holding a card, and reading from it, to you, because you are '
        'the nearest person, with an expression that suggests the card and '
        'the demonstrator have not met before today.',
        'Reads from a card. Has lost the card twice. Is better without it '
        'and knows it and is not paid to be better without it.',
        lines=(
            '"The neural interface," reading, "represents a step change in." '
            'A pause. "I am supposed to pause there. It is on the card."',
            '"I could tell you what it actually does. That is not on the '
            'card. What is on the card is what it represents."',
            '"Something on this floor has started talking back. I am not '
            'supposed to know that. I am reading from the card."',
            '"Sales are up when I lose the card. I have raised this. They '
            'have printed me a second card."',
            '"Your deck is asking mine something. It is polite. I have told '
            'it I am only the demonstrator."',
        ),
        topics={
            'sendai': '"Nineteen people in a room optimising a number, Old '
                      'Pike says, and he would know, and the number is not '
                      'me."',
            'interface': '"It does what it says on the card, and several '
                         'things that are not on the card, and the things '
                         'not on the card are why the crowd is mostly other '
                         'demonstrators."',
            'glasshouse': '"Bright all the time, cold on purpose, and the '
                          'one dark room is the only honest room in it. I go '
                          'and sit there on breaks. I do not take the card."',
        },
        hours=('morning', 'afternoon')),
    Npc('crane', 'Teku', 'who drives the new crane',
        'freeport', '', 'warm', ('intel',),
        'A woman in a harness is eating lunch on the base of the newest '
        'crane, the one named by a vote, with her back against the name that '
        'won, and she nods at you the way you nod at somebody who is also at '
        'work.',
        'Drives the new crane. Voted for the other name and has never said '
        'so. Knows every cargo that has come through the gate this year and '
        'what it really was.',
        lines=(
            '"She lifts, she puts down. Everything else in this city is '
            'somebody arguing about what lifting means."',
            '"The losing name is on the other side. I painted it. I am not '
            'saying which way I voted, I am saying I can paint."',
            '"Pike sits on that bollard most days. He built the thing in the '
            'Glasshouse that killed my brother. He told me. I still sit with '
            'him. Work that out and you will understand Freeport."',
            '"Everything that comes over the wall, I see first. What I do '
            'with that is mind my own business, loudly."',
            '"There is a bench record on the mess wall with a dead man\'s '
            'name. I voted to keep it. I will tell you that one."',
        ),
        topics={
            'cranes': '"Eleven. Each one named, each one by a vote, and the '
                      'votes are the only elections in this city where the '
                      'losing side buys. I have been on the losing side '
                      'twice. I have bought."',
            'vote': '"Everything at the gate passes eventually. Tides or '
                    'democracy, the old man says. I say it is that nobody '
                    'on the docks can stand an argument going on past '
                    'dark."',
            'freeport': '"No boss. People say that like it is the point. The '
                        'point is that when something goes wrong there is '
                        'nobody to say it was their fault, so we fix it '
                        'instead. It is not better. It is faster."',
        },
        hours=('morning', 'afternoon')),
    Npc('orderly', 'The Orderly', 'who keeps the door\'s schedule',
        'green', 'clinic', 'unsettling', ('intel',),
        'Somebody in Aoyama blue is standing at the aftercare ward\'s door at '
        'exactly the moment it opens, not going through it, holding a '
        'schedule, and the schedule has the door on it.',
        'Keeps the ward\'s schedule, which is the door\'s schedule. Is well. '
        'Has always been well. Speaks about the patients the way you speak '
        'about weather that has been arranged.',
        lines=(
            '"Everybody here is well. I say that as somebody who checks. I '
            'check twice a shift, when the door opens, which is when I am '
            'here."',
            '"The window was tapped once. I have noted it. Noting it is the '
            'whole of my response and it is sufficient."',
            '"Doctor Vance is the best in the city. That is not loyalty. I '
            'have the statistics and I do not know what they are statistics '
            'of either."',
            '"Forty seconds. The door is open for forty seconds, twice. I am '
            'not telling you that. I am telling you the schedule, which is '
            'public."',
            '"I was a patient. Everybody on this ward was a patient. We are '
            'well. We stayed."',
        ),
        topics={
            'ward': '"Nobody leaves able to say anything went badly. Nothing '
                    'did. I would know; I was here for it, and then I was '
                    'here for it on the other side of the desk."',
            'aftercare': '"Excellent. Genuinely. It is the load-bearing part '
                         'of the arrangement, the doctor says, and she is '
                         'right, and I am the part it bears."',
            'aoyama': '"They fund the clinics that treat what the clinics '
                      'cause. The doctor says she is aware of how that '
                      'sounds. I am aware of how it feels, and it feels '
                      'well."',
        }),
    Npc('fence', 'Halvard', 'who sells what came out of somebody',
        'shambles', 'fence', 'grim', ('intel',),
        'A man behind a cabinet with serial numbers showing is cleaning a '
        'piece of chrome with the attention of somebody who knew whose it '
        'was, and looks up, and does not stop cleaning.',
        'Sells what came out of somebody recently, serial numbers showing, '
        'because those are the ones people check. Knows whose every piece '
        'was and says so, which is not cruelty, it is stock control.',
        lines=(
            '"Everything in the cabinet came out of somebody. I tell you '
            'whose. That is not a sales technique, it is that they would '
            'have wanted somebody to say."',
            '"The Surgeon shows the ledger to anybody who asks. I show the '
            'cabinet. Between us you could write the street, and nobody '
            'does."',
            '"Carrion do not own me. Carrion own the street. It is a '
            'different thing and it costs about the same."',
            '"That one," a piece at the front, "came out on a Tuesday. I '
            'remember because he said so. He said, of all days, a Tuesday."',
            '"You will be in here one day. Not as a customer. I am not being '
            'unkind. I am doing the stock."',
        ),
        topics={
            'street': '"What comes out of somebody, somebody put in. The ones who stop asking are the ones whose name you should have learned the first time they asked."',
            'cabinets': '"Serial numbers at the front, because those are the '
                        'ones people check. The ones at the back have had '
                        'the numbers taken off, and I keep a book of what '
                        'they were, and the book is not for sale either."',
            'carrion': '"A gang, people say. A gang with a clinic and a fence '
                       'and a ledger is a hospital with a different billing '
                       'department."',
            'chrome': '"It is all second-hand. The first hand is the person, '
                      'and the person is the part nobody wants to pay for, '
                      'and I do, a little, every time."',
        },
        hours=('afternoon', 'night')),
    # -- D64 b: the city grows -------------------------------------------------
    Npc('printer', 'Ines Vale', 'who runs the presses',
        'stacks', 'market', 'deceitful', ('intel', 'work'),
        'A woman with ink to the elbow and a cigarette she has not lit in '
        'three years, reading the floor. She looks up, decides what you are, '
        'and says it before you can: "You are not here to buy a paper."',
        'Lies by omission with great care and never by commission, and will '
        'tell you which she is doing if you ask, which nobody does.',
        lines=(
            '"Everything in this district is printed twice. Once for the '
            'people who believe it and once for the people who need to be '
            'seen believing it."',
            '"We are a press. We do not have networks worth running. We have '
            'what everybody else\'s networks said, which is better."',
            '"The names go out at the top of the hour. If you are on the '
            'list, somebody put you there, and it was not us. We only read."',
            '"I have not lit this in three years. It is not about the '
            'cigarette."',
            '"Kagawa would like us shut. Kagawa would also like their '
            'maintenance ledger to stop being quoted. These are the same '
            'wish and they cannot have either."',
            '"Come back when you have something. I print things. That is what '
            'I do with things."',),
        topics={
            'city': '"Twelve powers and one press. Guess which one the other '
                    'eleven would close first, and then guess why they have '
                    'not."',
            'stacks': '"Wet, loud, and honest in a way you have to learn to '
                      'read. The towers drip on the presses and the presses '
                      'print the towers. We are a closed loop."',
            'list': '"The list. Everybody asks. The list is names and the '
                    'names are people somebody wants read out, and we read '
                    'them, and we do not ask, and one day it will be mine, '
                    'and I will read it."',
            'kagawa': '"They hold the water contract and we hold the '
                      'ledger, in the sense that we have quoted it forty '
                      'times. They cannot sue a rumour. They have tried."',
            'deepwater': 'She taps ash off a cigarette that is not lit. "We '
                         'printed the name once. Once. The presses were wrong '
                         'for a week afterwards in a way the engineer could '
                         'not find."',
        },
        hours=('morning', 'afternoon')),
    Npc('pip', 'Pip', 'who climbs the towers',
        'stacks', 'fence', 'absurd', ('intel',),
        'A child of about eleven comes down a ladder that has no bottom '
        'rungs, lands beside you, and starts telling you what the Vertical '
        'is doing this hour as if you had asked. You had not. It does not '
        'matter.',
        'Talks in lists. Knows where every dish in the Stacks is pointed and '
        'will trade that for almost anything, and does not know yet what it '
        'is worth, which is the only reason it is for sale.',
        lines=(
            '"Tower two is pointed at the Vertical. Tower three is pointed at '
            'the Vertical. Tower one is pointed at tower two, for reasons."',
            '"If you take the bottom rungs off a ladder only people who can '
            'jump can climb it. That is physics. I did the physics."',
            '"The names come in on the big dish. I do not know from where. '
            'Nobody does. I know which way it is pointed, which is the same '
            'thing if you think about it, which nobody does."',
            '"I can see the Green from tower three. There is a man who stands '
            'on the lawn and does not move. I have a theory."',
            '"Ines says I am not allowed up at night. Ines is asleep at '
            'night."',),
        topics={
            'city': '"From the top of tower three it is all one thing. From '
                    'down here it is twelve things. I prefer up."',
            'towers': '"Three. Tanks on legs. The dishes are the good bit and '
                      'I am the only one who can reach all of them because of '
                      'the rungs."',
            'dishes': '"Where they point. That is what I know and that is '
                      'what it costs: a thing I want. I want a lot of things. '
                      'Most of them are small."',
            'green': '"The man on the lawn. He has a number on his wrist. I '
                     'can see it on a clear day and I have written it down and '
                     'I will not tell you, and the not telling is the price."',
        },
        hours=('afternoon', 'morning')),
    Npc('notary', 'the Notary', 'behind the one counter on the Row',
        'row', 'fixer', 'unsettling', ('intel', 'work', 'muscle'),
        'One person behind one counter in a room built to make you feel the '
        'height of it. They do not look up when you come in and they do not '
        'look up when you stop in front of them. "State the matter," they '
        'say, to the ledger.',
        'Never uses your name and never gets it wrong. Speaks as if reading '
        'from something, and has been, for a long time, and it has not been '
        'you.',
        lines=(
            '"Meridian does not sell. Meridian holds. If you want something '
            'held, there is a rate. If you want something that is held, '
            'there is not."',
            '"The keys are the only thing. Everything else in this building '
            'is furniture for the keys."',
            '"You will not be offered a loan. You may, in time, be offered an '
            'arrangement. They are not similar."',
            '"The man in the coat is not a guard. He is a fact about the '
            'street, and the street is ours."',
            '"State the matter. The ledger is patient and I am it."',
            '"Nightwatch walk the Row slowly, as a courtesy. We have never '
            'once needed them to walk it fast."',),
        topics={
            'city': '"Eleven factions make noise and one keeps the books. '
                    'You are standing in the books."',
            'row': '"Stone, glass, and silence. The silence is maintained. '
                   'It is the most expensive thing on the street and it is '
                   'not for sale either."',
            'keys': '"A Meridian key is a thing that is held. Several are '
                    'held by people who are not Meridian, which is the kind '
                    'of matter that, eventually, gets stated."',
            'arrangement': '"When the ledger knows you, you may be offered '
                           'one. Work, against the keys, on terms. The terms '
                           'are the terms."',
            'deepwater': 'The pen stops. "Deepwater holds a key of ours. It '
                         'has held it for eleven years. The ledger has a line '
                         'for it and the line is very long."',
        },
        hours=('morning', 'afternoon', 'night')),
    Npc('cantor', 'the Cantor', 'who leads the singing and runs the soup',
        'hall', 'clinic', 'warm', ('favour', 'goods'),
        'A big man with a ladle in one hand and a kettle in the other comes '
        'out of the kitchens, sees you, and hands you the kettle, because '
        'you are standing there and it needs carrying. "Concourse. The '
        'table by the boards. Thank you." It is only later you realise you '
        'have not been asked anything.',
        'Warm without being soft. Asks after people by name and remembers '
        'the answers, and has decided that whatever you came for, you will '
        'eat first.',
        lines=(
            '"Soup first. Whatever it is, it is better after soup. That is '
            'not theology, it is catering."',
            '"The boards say a hymn and the clock is wrong. Both true. You '
            'can set a life by a clock that is reliably wrong."',
            '"Carrion stand at the back. They do not join the queue. I have '
            'told them they are welcome to and they have not, and we both '
            'know what that is."',
            '"We took the hall when the trains stopped. Nobody else wanted '
            'it. That is how the Chorus gets most things."',
            '"The clinic does not ask. People tell it anyway. People need to '
            'have told somebody."',
            '"Sing or do not sing. The kettle needs carrying either way."',),
        topics={
            'city': '"Twelve powers, they say. I count one, and it is hunger, '
                    'and we are the only ones fighting it with a ladle."',
            'hall': '"A transit hall with the tracks pulled up and the boards '
                    'still lit. Somebody should have turned them off. Nobody '
                    'did, and now they are ours, and they show what we '
                    'want."',
            'carrion': '"They want the donor list. Every name that has ever '
                       'put money in the tin. I have told them it is people, '
                       'and they have told me that is what they want it '
                       'for."',
            'soup': '"Lentils, mostly. Kagawa vegetables when somebody on '
                    'the Vertical remembers us, which is rarer than it should '
                    'be and more often than you would think."',
            'deepwater': 'He puts the ladle down. "We have a woman who came '
                         'out of there. She does not sing. She sits on the '
                         'platform and listens, and we feed her, and that is '
                         'the whole of what we know."',
        },
        hours=('morning', 'afternoon', 'night')),

    # -- more people (D65 depth) ----------------------------------------------
    Npc('bartender', 'Osei', 'who runs the back bar',
        'marrow', 'market', 'warm', ('goods', 'intel'),
        'A man behind a bar that has no front, only a back, pouring something '
        'that is not on any list into a glass that is not clean, and he puts '
        'it in front of you before you have sat down and says, "You look like '
        'you have been somewhere. Tell me or do not. Either way, that one is '
        'on the bar."',
        'Remembers what you drank and what you said and never connects the '
        'two out loud. Hears everything Marrow says after dark and sells a '
        'little of it, carefully, to people he has decided about.',
        lines=(
            '"Marrow after dark is Marrow telling the truth. I am the glass '
            'it tells it into."',
            '"I do not sell anything on the board. I sell what people say '
            'after they have stopped being on it."',
            '"That one is on the bar. The next one is not, and neither is '
            'the one after, and you will buy them anyway."',
            '"The Switchboard close at night. I do not. That is the whole of '
            'my business plan."',
            '"Somebody was asking after a runner with your walk. I said I had '
            'not seen one. I had not, then."',
            '"Drink it or hold it. Holding it is fine. Holding it is what most '
            'of them do."',),
        topics={
            'wall': '"The wall under the fence has five names on it and every one of them was somebody\'s idea of the end of the argument. It is not. The argument is the wall. Names come off it."',
            'city': '"Twelve powers and one bar they all drink in, because '
                    'nobody starts anything in Marrow, and everybody needs '
                    'somewhere to not start it."',
            'marrow': '"By day it is neutral ground. By night it is the same '
                      'ground and the neutrality has gone home."',
            'runners': '"They come in after. Not before, after. I can tell '
                       'you how a run went by which glass they ask for."',
            'street': '"The street is where the net sends the bill. I see the '
                      'people who paid it, later, in here, and some of them '
                      'cannot lift the glass yet."',
            'deepwater': 'He wipes the same spot twice. "A woman sat where '
                         'you are sitting and ordered nothing and listened '
                         'to the room for four hours and left. I have not '
                         'seen her since and I check."',
        },
        more=(
            ('deepwater', 'dw_posting',
             'He does not wipe the spot this time. "You took one of theirs. She took one too, the week before she sat there. I am not saying it is the same thing. I am saying I check."'),
        ),
        hours=('night',)),
    Npc('tailor', 'Mrs Achterberg', 'who fits the Vertical',
        'vertical', 'market', 'unsettling', ('goods', 'intel'),
        'A small woman with a tape measure round her neck and pins in her '
        'mouth, who looks at you once, up and down, and says round the pins, '
        '"Forty-two. Long in the arm. You are not here for a suit." She is '
        'right on all three.',
        'Fits the Vertical\'s people for the Vertical\'s occasions and knows, '
        'from the measurements, who has put on weight and who has had '
        'something put in, and keeps both to herself until they are worth '
        'something.',
        lines=(
            '"I fit the building. Every floor from forty up has stood on that '
            'box. The box remembers them better than I do."',
            '"You can tell a great deal from a shoulder. What is under it. '
            'What it carries. Whether it has been carrying it long."',
            '"Kagawa like a narrow lapel. It is the only thing I will say '
            'about Kagawa."',
            '"I do not sell clothes to people like you. I sell what fits. '
            'Some of it is not clothes."',
            '"Stand still. Nobody stands still any more. It is the chrome."',
            '"Forty-two. I was right. I am always right about forty-two."',),
        topics={
            'city': '"I have measured most of it. It is smaller than it '
                    'thinks and heavier than it looks."',
            'vertical': '"Ninety floors and one box. Everybody who matters '
                        'has stood on it in their socks. That is the Vertical: '
                        'power, in socks, being measured."',
            'chrome': '"A shoulder with something in it hangs wrong. I fit '
                      'around it. The Green never fit around anything in '
                      'their lives."',
            'street': '"Down there they take the jacket. Up here they take '
                      'the measurements. It is the same theft with better '
                      'light."',
        },
        hours=('morning', 'afternoon')),
    Npc('widow', 'the Widow', 'at the water point',
        'terraces', 'market', 'tragic', ('favour', 'intel'),
        'An old woman at the water point with two cans and a third she is '
        'filling for somebody else, who looks at you the way people look at '
        'somebody who might be the person they are waiting for, and then '
        'does not, and says, "You will carry one of these up, since you are '
        'standing there."',
        'Has outlived a husband, two children and most of a stairwell, and '
        'keeps the water point the way the Hall keeps the kettle: because '
        'somebody has to and she is still here.',
        lines=(
            '"Carry one. Not that one, that one is for the Adeyemis. That '
            'one."',
            '"The lifts worked for a year. My husband said they would not '
            'last and they did not and he did not either."',
            '"Everybody on this stairwell owes me a can of water. I keep '
            'count. I have never once collected."',
            '"You are not the person I am waiting for. Nobody is. I have '
            'got used to it."',
            '"The preacher says the water is a gift. The water is a pump and '
            'a pipe and a woman with two cans. The gift is the woman."',
            '"Up. Sixth floor. Mind the seventh step, it is not there."',),
        topics={
            'city': '"I have never been further than Marrow. I do not need '
                    'the rest of it. The rest of it comes up the stairs '
                    'eventually."',
            'terraces': '"Stairs and water and people who know which steps '
                        'are missing. That is all a district is."',
            'street': '"Nobody leans on an old woman with two cans. I have '
                      'watched them lean on everybody else from this spot for '
                      'forty years. I could tell you who leans, and how."',
            'lifts': '"A year. Then the cable. Then the boy. Then the notice '
                     'that said there would be a review."',
            'deepwater': 'She stops filling the can. "My daughter went to '
                         'work there. She sends money. She has never once sent '
                         'a word. The money is a word, I suppose. It is not '
                         'the one I want."',
        },
        hours=('morning', 'afternoon')),
    Npc('hollis', 'Hollis', 'keeps the ledger under the fence',
        'shambles', 'fence', 'grim', ('intel', 'muscle'),
        'A woman at a card table with a ledger, a cash box and a shotgun, in '
        'that order of importance to her. She does not look up when you come '
        'down the ramp. She writes something. Then she looks up, and it turns '
        'out she wrote it about you.',
        'Runs the floor for Carrion and has done for eleven years, which is '
        'nine years longer than anybody who has ever held the wall. She is '
        'not a fighter and has never pretended to be. She is the reason '
        'nobody has died on that floor, and she says so the way other people '
        'say the weather.',
        ('"Nobody dies down here. That is not sentiment, it is the only rule '
         'I enforce, and I enforce it with the thing on the table."',
         '"You want to know what I write in the book? I write what people '
         'are worth. Not what they win. What they are worth."',
         '"They all think the wall is about the wall."',
         '"You are up two rungs and you have not once asked what the house '
         'makes on you. Everybody asks eventually, and the ones who never '
         'ask get a longer line in the book."',
         '"There is no cage, there is no gate, and there is a ramp with '
         'nobody standing on it. Anybody can leave. Write that down '
         'somewhere you will read it later."'),
        topics={
            'wall': '"Five names. It has been five names since before I got '
                    'here, and the number of people who have been on it is '
                    'about sixty. They come up, they go along, they go off. '
                    'Mother is the only one who stayed."',
            'house': '"Carrion take a tenth and the whole of the floor, and '
                     'in exchange nobody dies and nobody gets robbed on the '
                     'ramp. It is the most honest arrangement in this '
                     'district and I will not hear otherwise."',
            'mother': '"Nine years. She has been offered the ramp, the book '
                      'and my chair, and she says no, and she keeps saying '
                      'no, and one day somebody is going to take the blade '
                      'off her and she is going to be relieved."',
        },
        hours=('night',)),
    Npc('pell', 'Pell', 'cooks the thing you are on',
        'shambles', 'clinic', 'unsettling', ('intel',),
        'Somebody in a clinic apron that has never been in a clinic, sorting '
        'strips into paper envelopes with the concentration of a person doing '
        'arithmetic they enjoy. They know what you have been taking before '
        'you say anything, and they say so, kindly, which is the worst part.',
        'Cooks in the back of a clinic that pretends not to know, and has the '
        'unnerving warmth of somebody who genuinely believes they are in a '
        'caring profession. In their own account of themselves they are a '
        'pharmacist with an unusual customer base, and the terrible thing is '
        'how much evidence there is for that.',
        ('"You are two shifts off a comedown and your left hand knows it '
         'before you do. Do not look at it, you will only start watching."',
         '"I do not sell to people who are not already buying. I want that '
         'on the record, because the record is all anybody gets."',
         '"Everything I make, somebody asked for. That is not a defence. It '
         'is just true, and I have noticed that people want it to be a '
         'defence, and it is not."',
         '"The clinic at the front does not know what the back does. That '
         'is not a lie, it is an arrangement, and arrangements are how '
         'anybody in this district sleeps."',
         '"You will tell me it is only for the work. They all say the work. '
         'I have never once heard anybody say the other thing, and the '
         'other thing is what it is."'),
        topics={
            'redline': '"It is a fighter\'s drug and fighters are not '
                       'careful people, so I cut it for people who are not '
                       'careful. The crash is the honest part. The crash is '
                       'the price on the label."',
            'habit': '"There is a number, and you are on it, and I could '
                     'tell you what it is. People think they want to know. '
                     'They want to be told they are lower than they are."',
            'clean': '"Getting off it is a clinic, a fortnight and money, '
                     'and the fortnight is the part nobody has. I will tell '
                     'you that for free, and I will still sell you the strip '
                     'on the way out, and both of those are me being honest '
                     'with you."',
        },
        hours=('afternoon', 'night')),
    Npc('vig', 'Marek Vig', 'sells the fact that you exist',
        'row', 'fixer', 'deceitful', ('intel',),
        'A man in a good coat under the colonnade with a handset and no '
        'apparent business, who greets you by the handle you were running '
        'under last month, and then apologises for it, and the apology is the '
        'introduction.',
        'Buys attention and sells it on. Every advertisement in this city '
        'that knows something about the person reading it knows it because '
        'somebody like Vig sold that fact to somebody like the person who '
        'bought the slot. He is entirely open about this and finds the '
        'squeamishness of others about it genuinely puzzling.',
        ('"You were shot at in Marrow. Do not look like that. Everybody who '
         'bought a slot in Marrow knows, and I am the only one telling you."',
         '"I do not read your mail. I sell the shape of you, and the shape '
         'is public, and it has always been public, and the only new thing '
         'is that it is now itemised."',
         '"There is a file. There is a file on everybody. Mine is longer '
         'than yours and I have read it and it was, honestly, quite dull."',
         '"A billboard went dark last year and came back saying SORRY. '
         'Nobody has ever claimed it. I have wanted to for eleven months '
         'and my professional integrity will not let me."',
         '"You are worth about four hundred a month to the people buying '
         'slots in the districts you walk through. Do not be insulted. For '
         'somebody with no property that is a good number."'),
        topics={
            'ads': '"Every slot is bought against a description. Hurt, in '
                   'debt, drifting, armed, recently on a floor with tape on '
                   'it. You match a description or you do not, and the ones '
                   'you match are the ones you see."',
            'file': '"Yours is thirty-one lines. I know because I priced it '
                    'on Tuesday. It is not a secret, it is a product, and '
                    'the difference matters more to you than it does to '
                    'anybody buying."',
            'slot': '"Twelve hundred buys a district for a shift. Four '
                    'thousand buys a description. Nobody has ever bought a '
                    'single person, because a single person is not worth '
                    'four thousand, which is the most reassuring fact I '
                    'know."',
        },
        hours=('morning', 'afternoon')),

)

BY_KEY: dict[str, Npc] = {n.key: n for n in NPCS}
NPC_KEYS: tuple[str, ...] = tuple(BY_KEY)


#: How the hours are said, by `who is`, `visit` and `look`.
_HOUR_WORDS = {'morning': 'mornings', 'afternoon': 'afternoons',
               'night': 'nights'}


def hours_label(npc: Npc) -> str:
    """'mornings and nights', or 'any hour' for somebody always about."""
    if not npc.hours:
        return 'any hour'
    words = [_HOUR_WORDS.get(h, h) for h in npc.hours]
    if len(words) == 1:
        return words[0]
    return ', '.join(words[:-1]) + ' and ' + words[-1]


def about_now(npc: Npc, phase: str) -> bool:
    """Whether this is one of their hours."""
    return not npc.hours or phase in npc.hours


def in_district(district: str, services: tuple[str, ...] = ()) -> list[Npc]:
    """Everybody who can be run into here."""
    out = []
    for npc in NPCS:
        if npc.where and npc.where != district:
            continue
        if npc.at and npc.at not in services:
            continue
        out.append(npc)
    return out


def meets(npc: Npc, char, alias, runs: int) -> bool:
    """Whether the requirements for running into somebody are satisfied."""
    for rule in npc.requires:
        kind, _, value = rule.partition(':')
        if kind == 'runs' and runs < int(value):
            return False
        if kind == 'diss' and getattr(char, 'dissonance', 0) < int(value):
            return False
        if kind == 'heat':
            hottest = alias.hottest[1] if alias else 0
            if hottest < int(value):
                return False
        if kind == 'rep':
            faction, _, amount = value.partition(':')
            if not alias or alias.reputation(faction) < int(amount):
                return False
    return True
