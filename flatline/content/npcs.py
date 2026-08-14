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
OFFERS = ('work', 'goods', 'intel', 'favour', 'nothing')


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
    #: Conditions for running into them at all, checked by the world layer.
    #: 'runs:N' at least N runs, 'diss:N' at least N Dissonance,
    #: 'heat:N' at least N heat with anybody, 'rep:<faction>:N'.
    #:
    #: There is deliberately no `threads` field. Meeting somebody sets
    #: `met:<key>`, and a thread stage requires that flag like any other, so
    #: the connection lives in one place instead of two that can disagree.
    requires: tuple[str, ...] = ()


NPCS: tuple[Npc, ...] = (
    # -- Marrow -----------------------------------------------------------
    Npc('mara', 'Mara Okonkwo', 'who answers for the Switchboard',
        'marrow', 'fixer', 'grim', ('work', 'intel', 'favour'),
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
        ),
        topics={
            'city': '"Twelve powers, and eleven of them think they are the '
                    'one holding the leash. Do not correct anybody."',
            'work': '"Take the small ones until somebody who is not me says '
                    'your name. Then take the small ones for a while longer."',
            'deepwater': 'She stops writing. "I place four contracts a month '
                         'for that and I have never met anybody who works '
                         'there. Draw your own conclusions and keep them."',
        }),
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
        ),
        topics={
            'city': '"Everything in this city is built on a document somebody '
                    'lost. I have most of the documents."',
            'terraces': '"Eleven thousand people and one stairwell rated for '
                        'four hundred. I have said so. Repeatedly."',
        }),

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
        ),
        topics={
            'city': '"Nothing down here connects the way the map says. The '
                    'map is from before the flood."',
            'work': '"You want the one nobody else took. There is always one '
                    'nobody took and there is always a reason."',
        }),
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
        ),
        topics={
            'city': 'DISPLAY: THE CITY IS A MACHINE FOR SORTING PEOPLE. I AM '
                    'ALSO A MACHINE FOR SORTING PEOPLE. WE ARE NOT THE SAME.',
            'deepwater': 'The display goes blank for four seconds. Then: NO.',
        }),

    # -- the Shambles -----------------------------------------------------
    Npc('surgeon', 'The Blue Surgeon', 'who does not use anaesthetic',
        'shambles', 'clinic', 'unsettling', ('goods',),
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
        ),
        topics={
            'chrome': '"Everything I fit, I would fit in myself. Some of it I '
                      'have. That is the only assurance worth anything and '
                      'nobody ever believes it."',
            'chorus': '"They send me people. The people arrive calm and leave '
                      'calmer. I do not ask and they do not volunteer."',
        }),
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
        ),
        topics={
            'chrome': '"Everybody tells you it has a cost. Nobody tells you '
                      'the cost arrives all at once, eleven years later, on '
                      'a Tuesday."',
            'work': '"Take the jobs that pay. I took the jobs that were '
                    'interesting and here I am being interesting."',
        }),

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
        ),
        topics={
            'freeport': '"Nine years, no boss, and the accounts balance. '
                        'People come to sneer and then they read the '
                        'accounts."',
            'city': '"Every other district in this town runs on somebody not '
                    'writing something down."',
        }),
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
        ),
        topics={
            'ice': '"It telegraphs because I made it telegraph. I had an '
                   'argument about that and I won it, and I have been paid '
                   'for it in ways I did not expect."',
            'sendai': '"They are not evil. That would be easier. They are '
                      'nineteen people in a room optimising a number."',
        }),

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
        ),
        topics={
            'kagawa': '"We log everything. Everything. I have raised concerns '
                      'about the volume and been thanked for my input."',
            'work': '"If you must, and I am not saying you must, the '
                    'nine-to-eleven window has fewer of us in it."',
        }),
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
        ),
        topics={
            'death': '"It is not dark and it is not light. It is a room you '
                     'have already been in and cannot place."',
            'deepwater': 'They are quiet for a long moment. "It knows my '
                         'name. I have never told anybody that."',
        },
        requires=('runs:3',)),

    # -- Aoyama Green -----------------------------------------------------
    Npc('vance', 'Doctor Vance', 'who is buying, not selling',
        'green', 'clinic', 'deceitful', ('work', 'goods'),
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
        ),
        topics={
            'chrome': '"Aoyama chrome is the best in this city and I will '
                      'not pretend otherwise out of modesty."',
            'aoyama': '"We fund the clinics that treat what the clinics '
                      'cause. I am aware of how that sounds."',
        }),

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
        ),
        topics={
            'nightwatch': '"We are a vendor. Vendors have targets. Work out '
                          'what a target does to an arrest rate."',
            'heat': '"A bounty is a line item. If you are on one, somebody '
                    'costed you, and costs come down."',
        },
        requires=('heat:20',)),

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
        ),
        topics={
            'city': '"They keep telling us the Terraces are being reviewed. '
                    'Thirty-one years of review."',
            'kagawa': '"They grow the food and they own the wall I grow mine '
                      'on. I have made my peace and it is a small peace."',
        }),
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
        ),
        topics={
            'chorus': '"They are the worst of it. They have made a religion '
                      'out of a metaphor and they are FITTING it to people."',
            'city': '"Everybody in this city is somewhere. That is the whole '
                    'of my position and it is unanswerable."',
        }),

    # -- found rather than located ----------------------------------------
    Npc('broker', 'Mr Sunday', 'who works for whoever you think',
        '', 'fixer', 'deceitful', ('work', 'intel'),
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
        ),
        topics={
            'city': '"Twelve powers and about nine hundred of me. Guess which '
                    'of those actually moves anything."',
            'work': '"I can get you work above your standing. There is '
                    'always a reason work is available above your standing."',
        },
        requires=('runs:2',)),
    Npc('archivist', 'The Archivist', 'who is not selling the archive',
        '', 'fence', 'unsettling', ('goods', 'intel'),
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
        ),
        topics={
            'death': '"Everybody leaves a log. It is the only part of this '
                     'that is reliably permanent."',
            'deepwater': '"Nine of my four hundred and six were running '
                         'Deepwater. All nine logs end the same way and it '
                         'is not the way a log ends."',
        },
        requires=('runs:5',)),
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
        ),
        topics={
            'work': '"Where do you start? Everybody says start small. Small '
                    'does not pay for the thing that makes you not-small."',
            'death': 'They laugh. It is not a good laugh. "I know. I do '
                     'actually know."',
        },
        requires=('runs:4',)),
)

BY_KEY: dict[str, Npc] = {n.key: n for n in NPCS}
NPC_KEYS: tuple[str, ...] = tuple(BY_KEY)


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
