"""Storylines, and the reason they cross.

A linear quest is a list. What makes a story feel like a *place* is that
several of them are running at once, none of them is waiting for you, and
advancing one changes the shape of another.

So there are no quest chains here. A thread is a set of **stages**, each with
its own unlock condition, and a stage becomes available the moment its
condition holds however that happened. That means:

- A thread can be entered at more than one point. You can meet Deepwater
  through the Archivist, through Remnant, through running one of their
  networks, or through asking Mara the wrong question.
- Two threads can share a condition, so an act in one shows up in the other.
  Taking Vance's offer closes a door in Lark's thread without either of them
  mentioning the other.
- Nothing is ordered. Stage four can happen before stage two if the world got
  there first, and the writing has to survive that, which is why every stage
  reads as a scene rather than as a step.

**Flags are the whole mechanism.** A stage requires flags and sets flags, and
`validate.py` checks that every flag anything requires is set by something,
so a thread can never quietly become unreachable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: World conditions usable in `requires`, alongside plain flags.
#: 'runs:N', 'diss:N', 'shift:N', 'credits:N', 'heat:N', 'met:<npc>',
#: 'rep:<faction>:N', 'ran:<faction>'.
CONDITIONS = ('runs', 'diss', 'shift', 'credits', 'heat', 'met', 'rep', 'ran')


@dataclass(frozen=True, slots=True)
class Choice:
    key: str
    #: What the player is choosing, in their words.
    label: str
    #: What happens. Second person.
    text: str
    sets: tuple[str, ...] = ()
    #: Immediate consequences the story layer applies.
    credits: int = 0
    rep: dict = field(default_factory=dict)
    #: Disposition changes with named rivals.
    disposition: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Stage:
    key: str
    #: Shown in the journal as the current state of this thread.
    headline: str
    text: str
    #: Everything that must hold for this stage to become available.
    requires: tuple[str, ...] = ()
    #: At least one of these must hold, if any are given. This is what makes
    #: a second way into a thread a property of the data rather than a thing
    #: achieved by writing the same scene twice.
    any_of: tuple[str, ...] = ()
    sets: tuple[str, ...] = ()
    choices: tuple[Choice, ...] = ()
    #: Where this scene happens, for flavour and gating. '' means anywhere.
    where: str = ''


@dataclass(frozen=True, slots=True)
class Thread:
    key: str
    name: str
    #: One line in the journal.
    blurb: str
    stages: tuple[Stage, ...]
    #: Threads this one touches. Checked by `validate.py` for symmetry, so a
    #: crossing is never one-way by accident.
    crosses: tuple[str, ...] = ()


THREADS: tuple[Thread, ...] = (
    # ------------------------------------------------------------------
    Thread(
        'deepwater', 'What Deepwater Is',
        'Nine years of contracts and nobody has ever met anybody.',
        crosses=('archive', 'ozymandias', 'drawer'),
        stages=(
            Stage('hear', 'Somebody mentioned it and then stopped',
                  'It comes up the way weather comes up. Somebody says the '
                  'name, and then does not say the next thing, and the '
                  'conversation goes somewhere else with a small limp in it.',
                  requires=('runs:2',),
                  sets=('dw_heard',)),
            Stage('logs', 'Nine logs that end wrong',
                  'The Archivist turns their chair round for this, which they '
                  'have not done before.\n\n'
                  '"Four hundred and six logs. Nine of them were running '
                  'Deepwater. A log ends when the connection ends: there is a '
                  'last entry and then nothing, and the nothing has a shape '
                  'to it."\n\n'
                  'They pull one up. "These nine do not end. They stop being '
                  'a log and carry on being a file. There is more data after '
                  'the death than before it, and it is not in any format I '
                  'have a name for."',
                  requires=('dw_heard', 'met:archivist'),
                  sets=('dw_logs',)),
            Stage('name', 'It knows a name it should not',
                  'Remnant says it without preamble, in the middle of '
                  'something else, the way you mention a thing you have '
                  'decided not to be frightened of any more.\n\n'
                  '"It knows my name. Deepwater. I have never told anybody '
                  'and it has never been in a file."\n\n'
                  'They watch you take that. "I died for ninety seconds on a '
                  'Sendai table. I am not saying those two facts are '
                  'connected. I am saying nobody has offered me a third '
                  'fact."',
                  requires=('dw_heard', 'met:remnant'),
                  sets=('dw_name',)),
            Stage('inside', 'You have been inside it',
                  'You have run a Deepwater network now, and the thing you '
                  'cannot make sit still afterwards is that there was no '
                  'perimeter. Not a weak one. Not a clever one. There was '
                  'nothing arranged around anything, because arrangement is '
                  'what a person does to a space they do not personally '
                  'occupy.',
                  requires=('ran:deepwater',),
                  sets=('dw_inside',)),
            Stage('offer', 'It would like to hire you',
                  'The contract arrives through Mara, who does not look at '
                  'you while she hands it over, which is new.\n\n'
                  '"Nine years I have placed these. This is the first one '
                  'with a name on it." A pause. "Your name."\n\n'
                  'The brief is four words long and the payment has already '
                  'cleared.',
                  requires=('dw_inside', 'dw_logs', 'dw_name'),
                  sets=('dw_offer',),
                  choices=(
                      Choice('take', 'Take it',
                             'You take it. Nothing dramatic happens. The '
                             'money is real, the work is real, and for '
                             'several shifts afterwards you notice that '
                             'networks you have never run feel slightly '
                             'familiar, in the way a word does when somebody '
                             'has just said it.',
                             sets=('dw_employed',),
                             credits=9000),
                      Choice('refuse', 'Hand it back',
                             'Mara takes it back and does not comment. Three '
                             'shifts later the noodle bar has a new landline '
                             'and she has not explained it.\n\n'
                             'Nothing pursues you. That is somehow the part '
                             'that stays.',
                             sets=('dw_refused',),
                             rep={'fixers': 6}),
                      Choice('publish', 'Give the whole thing to Static',
                             'Static run it in full: the nine logs, the '
                             'contracts, the name. For about a day it is the '
                             'only thing anybody in Marrow is talking '
                             'about.\n\n'
                             'Then it is not. Nobody retracts it and nobody '
                             'disputes it and within a week it is simply not '
                             'a thing people bring up, and you cannot find '
                             'anybody who will tell you why.',
                             sets=('dw_published',),
                             rep={'static': 25, 'meridian': -10},
                             credits=3000),
                  )),
        )),

    # ------------------------------------------------------------------
    Thread(
        'lark', 'Lark',
        'Somebody your age, on the wrong side of their own chrome.',
        crosses=('vance', 'sparrow'),
        stages=(
            Stage('meet', 'They asked you for nothing, twice',
                  'The second time you see Lark they are worse, and they '
                  'make a joke about it that is genuinely good, and the joke '
                  'is the ask.',
                  requires=('met:lark',),
                  sets=('lark_met',)),
            Stage('problem', 'What is actually wrong',
                  '"Six pieces. Two of them are load-bearing and one of those '
                  'two is failing." Lark says it like a weather report. '
                  '"Taking it out kills me. Leaving it in kills me slower. '
                  'The interesting bit is that there is a third option and it '
                  'costs about nine thousand credits."\n\n'
                  'They look at you. "I am telling you because you asked. I '
                  'want to be extremely clear that I am not asking."',
                  requires=('lark_met',),
                  sets=('lark_problem',)),
            Stage('vance', 'Somebody else has made them an offer',
                  'Doctor Vance has been to see Lark. Lark tells you this '
                  'flatly, in the way people report things they have already '
                  'decided about.\n\n'
                  '"She will do it for free. All of it. She wants the failing '
                  'piece afterwards, and the data off it, and a waiver about '
                  'what she does with either." A shrug that costs them '
                  'something. "It is a good offer. It is a genuinely good '
                  'offer and I have not slept."',
                  requires=('lark_problem', 'met:vance'),
                  sets=('lark_vance',)),
            Stage('resolve', 'It comes down to what you do',
                  'Lark is out of time in the specific way that means this '
                  'week rather than this year.',
                  requires=('lark_problem', 'runs:5'),
                  sets=('lark_resolved',),
                  choices=(
                      Choice('pay', 'Pay for the third option yourself',
                             'Nine thousand credits, and the Blue Surgeon '
                             'does it in a clean room off the Shambles over '
                             'eleven hours, talking the whole time.\n\n'
                             'Lark comes out of it smaller and alive. They do '
                             'not thank you, at length, in a way that is '
                             'clearly the thanking.',
                             sets=('lark_saved', 'surgeon_owed'),
                             credits=-9000,
                             disposition={'moth': 12}),
                      Choice('vance', 'Tell them to take Vance\'s offer',
                             'They take it. It works. Aoyama keep the piece '
                             'and the data and the waiver, and Lark is alive '
                             'and slightly quieter than they were.\n\n'
                             'Four shifts later Vance sends you something '
                             'unasked-for and expensive, with no note, which '
                             'is how you find out what your part in that was '
                             'worth to her.',
                             sets=('lark_saved', 'vance_owed'),
                             credits=2500,
                             rep={'aoyama': 8}),
                      Choice('nothing', 'Do nothing',
                             'You do nothing, which is a thing you are '
                             'allowed to do and which nobody will ever raise '
                             'with you.\n\n'
                             'The crate outside the clinic is empty the next '
                             'time you are in the Shambles. Somebody has left '
                             'a jacket on it. It is still there four shifts '
                             'later and then it is not.',
                             sets=('lark_dead',),
                             disposition={'moth': -8}),
                  )),
        )),

    # ------------------------------------------------------------------
    Thread(
        'vance', 'Doctor Vance Is Buying',
        'Everything she has told you is true. The arrangement of it is not.',
        crosses=('lark', 'archive', 'drawer'),
        stages=(
            Stage('file', 'She had your file first',
                  'You have never been to Aoyama Green as a patient and she '
                  'had your file open before you sat down. When you say so, '
                  'she does not deny it, apologise, or explain. She turns the '
                  'page.',
                  requires=('met:vance',),
                  sets=('vance_file',)),
            Stage('warned', 'Lark told you what she offered them',
                  'You already knew she wanted something. What you did not '
                  'have until Lark said it out loud was the shape: free '
                  'work, total competence, and a waiver about the part '
                  'afterwards.\n\n'
                  'It is a good offer. That is what makes it difficult to '
                  'describe what is wrong with it.',
                  requires=('vance_file',),
                  any_of=('lark_vance', 'vance_suspect'),
                  sets=('vance_warned',)),
            Stage('ask', 'What she actually wants',
                  '"Failing chrome. Specifically: chrome that has been in a '
                  'person long enough to have been changed by them." She says '
                  'it the way you would say a shopping list.\n\n'
                  '"I am not asking you to hurt anybody. I am asking you to '
                  'tell me when you meet somebody who is already in that '
                  'position, and to be persuasive about the fact that I am '
                  'the best outcome available to them."\n\n'
                  'The worst part is that she is.',
                  requires=('vance_file',),
                  any_of=('runs:3', 'vance_warned'),
                  sets=('vance_ask',)),
            Stage('paid', 'She pays for people',
                  'The transfer arrives before you have agreed to anything, '
                  'which is not carelessness.',
                  requires=('vance_ask',),
                  sets=('vance_done',),
                  choices=(
                      Choice('work', 'Work for her',
                             'You find her people. They are people who were '
                             'going to die and now will not, and the '
                             'paperwork is immaculate, and you have not been '
                             'able to describe what is wrong with it to '
                             'anybody including yourself.',
                             sets=('vance_employed',),
                             credits=6000,
                             rep={'aoyama': 15, 'freeport': -10}),
                      Choice('refuse', 'Say no',
                             '"Of course." She closes the file. "Do come '
                             'back if the position changes. It does, for most '
                             'people, and I have never once held it against '
                             'anybody."',
                             sets=('vance_refused',),
                             rep={'aoyama': -6}),
                      Choice('expose', 'Take it to Static',
                             'Static publish, and Aoyama\'s response is a '
                             'four-line statement noting that all procedures '
                             'were consensual and clinically indicated, which '
                             'is true.\n\n'
                             'Nothing happens to her. Two of her patients '
                             'stop being her patients and one of them dies.',
                             sets=('vance_exposed',),
                             rep={'static': 20, 'aoyama': -30}),
                  )),
        )),

    # ------------------------------------------------------------------
    Thread(
        'sunday', 'Who Mr Sunday Works For',
        'Everything he offers is real. Who it is for is the moving part.',
        crosses=('drawer',),
        stages=(
            Stage('meet', 'A different employer every time',
                  'Third time you meet him he is a friend of Freeport. First '
                  'time he was a friend of the Switchboard. You have started '
                  'writing them down.',
                  requires=('met:broker', 'runs:3'),
                  sets=('sunday_noticed',)),
            Stage('tell', 'The one thing that does not move',
                  'Every job he has offered you has been against somebody '
                  'who owes Meridian money.\n\n'
                  'Not most. Every one. It took writing them down to see it, '
                  'because individually each brief is a different faction '
                  'wanting a different thing, and collectively they are a '
                  'bank tidying up.',
                  requires=('sunday_noticed',),
                  any_of=('runs:6', 'drawer_accounts'),
                  sets=('sunday_tell',),
                  choices=(
                      Choice('confront', 'Say so, to his face',
                             'He is delighted. Genuinely, unmistakably '
                             'delighted, in a way that makes the whole thing '
                             'worse.\n\n'
                             '"Eleven months. That is the fastest anybody has '
                             'done it." He buys you a drink. "The work is '
                             'still good. It was always still good."',
                             sets=('sunday_known',),
                             credits=1500),
                      Choice('sell', 'Sell what you worked out',
                             'Static will not touch it without a second '
                             'source. Freeport will, and they pay, and they '
                             'put it in the public log where Meridian will '
                             'certainly read it.\n\n'
                             'Mr Sunday stops appearing. You do not know '
                             'whether that means anything.',
                             sets=('sunday_sold',),
                             credits=4000,
                             rep={'freeport': 15, 'meridian': -20}),
                      Choice('keep', 'Say nothing and keep taking the work',
                             'The work is still good. That is the whole of '
                             'your reasoning and it holds up for a '
                             'surprisingly long time.',
                             sets=('sunday_kept',),
                             credits=2500,
                             rep={'meridian': 8}),
                  )),
        )),

    # ------------------------------------------------------------------
    Thread(
        'sparrow', 'Sparrow',
        'Sixteen, self-taught, and about eight months from something fatal.',
        crosses=('lark',),
        stages=(
            Stage('follow', 'They have been following you',
                  'Badly, for two blocks, and they are now pretending they '
                  'have not been.',
                  requires=('met:kestrel_kid',),
                  sets=('sparrow_met',)),
            Stage('deck', 'The deck is going to kill them',
                  'They show you it, eventually, with the defensiveness of '
                  'somebody who already knows.\n\n'
                  'No masking layer at all. A salvaged core with a cooling '
                  'solution that is, on inspection, a wet cloth. It will run '
                  'a perimeter node and it will not survive a warden, and '
                  'they are talking about the Vertical.',
                  requires=('sparrow_met',),
                  any_of=('runs:5', 'lark_dead', 'lark_saved'),
                  sets=('sparrow_deck',),
                  choices=(
                      Choice('gear', 'Give them something that works',
                             'You hand over a masking layer and a breaker '
                             'that will not get them killed on a Tuesday. '
                             'They are insufferable about it for eleven '
                             'minutes and then very quiet.',
                             sets=('sparrow_geared',),
                             credits=-2000),
                      Choice('teach', 'Tell them the thing nobody told you',
                             'You explain the trace. Properly, with the '
                             'numbers, including the part where the clean '
                             'exit is the skill and the entry is not.\n\n'
                             'They argue with you for an hour. Somewhere in '
                             'the middle of the argument they stop arguing '
                             'and start writing it down.',
                             sets=('sparrow_taught',)),
                      Choice('scare', 'Frighten them out of it',
                             'You tell them about Lark. You are specific, and '
                             'you are unkind, and it works: they go white and '
                             'they leave and they do not follow you again.\n\n'
                             'You see them eleven shifts later working a '
                             'counter in Marrow. They do not look up.',
                             sets=('sparrow_scared',)),
                  )),
            Stage('after', 'What happened to them',
                  'How this went is now a thing about you rather than a thing '
                  'about them.',
                  requires=('sparrow_deck', 'runs:12'),
                  sets=('sparrow_resolved',)),
        )),

    # ------------------------------------------------------------------
    Thread(
        'drawer', 'The Drawer',
        'Nineteen years of complaints that were never going to go anywhere.',
        crosses=('sunday', 'deepwater', 'vance'),
        stages=(
            Stage('open', 'He tells you about the drawer',
                  'Sergeant Achebe waits until the queue has given up for the '
                  'day.\n\n'
                  '"Nineteen years. The ones that would go somewhere, I '
                  'filed. The rest are in here." He does not open it. "I am '
                  'not a whistleblower. I am a man with a drawer and a '
                  'pension I would like to receive."',
                  requires=('met:desk',),
                  sets=('drawer_told',)),
            Stage('read', 'What is in it',
                  'He lets you read, in the room, with the door open, which '
                  'he is careful to point out is not a favour.\n\n'
                  'Most of it is nothing: neighbours, noise, a man convinced '
                  'the Terraces lifts are watching him. Two of them are not '
                  'nothing. One is a pattern of missing-persons reports from '
                  'the Shambles that all name the same clinic. The other is '
                  'four separate people, over nine years, reporting that '
                  'something is using a relative\'s account.',
                  requires=('drawer_told', 'runs:7'),
                  sets=('drawer_read',),
                  choices=(
                      Choice('shambles', 'Follow the clinic reports',
                             'They lead to the Blue Surgeon, who is '
                             'genuinely, visibly baffled by the accusation, '
                             'and whose records are immaculate, and who '
                             'offers to show you all of them.\n\n'
                             'The missing people were referred on. To Aoyama '
                             'Green. Every one.',
                             sets=('drawer_clinic', 'vance_suspect')),
                      Choice('accounts', 'Follow the account reports',
                             'Four families, nine years, and one thing in '
                             'common: every account belonged to somebody who '
                             'died with an interface still connected.\n\n'
                             'The activity is not fraud. Nothing is taken. '
                             'Something logs in, does very little, and logs '
                             'out again, and has been doing so patiently for '
                             'the better part of a decade.',
                             sets=('drawer_accounts', 'dw_heard')),
                  )),
        )),

    # ------------------------------------------------------------------
    Thread(
        'archive', 'Four Hundred and Six',
        'Somebody is collecting the last logs of dead netrunners.',
        crosses=('deepwater', 'vance'),
        stages=(
            Stage('meet', 'The wall that hums',
                  'They do not turn round for the first four minutes of the '
                  'conversation, and when they do it is worse, because they '
                  'are perfectly ordinary.',
                  requires=('met:archivist',),
                  sets=('archive_met',)),
            Stage('why', 'Why they collect',
                  '"Because somebody should." They say it without any of the '
                  'weight you were expecting.\n\n'
                  '"Four hundred and six people did a difficult thing badly '
                  'once. The log is the only part of them that is reliably '
                  'permanent, and everybody else in this city treats it as '
                  'evidence." A small shrug. "I treat it as a person. That '
                  'is the entire difference and it is not a small one."',
                  requires=('archive_met',),
                  any_of=('runs:6', 'dw_logs', 'vance_exposed'),
                  sets=('archive_why',)),
            Stage('yours', 'They would like yours, eventually',
                  'They ask permission. That is the thing that takes you '
                  'apart slightly: they ask, formally, for something they '
                  'will only ever receive if you are dead.',
                  requires=('archive_why',),
                  sets=('archive_asked',),
                  choices=(
                      Choice('yes', 'Say yes',
                             'They write it down in a book. An actual book. '
                             '"Four hundred and seven," they say, and then '
                             'immediately, "not yet, obviously," and are '
                             'embarrassed for the only time you will ever '
                             'see.',
                             sets=('archive_consented',)),
                      Choice('no', 'Say no',
                             '"Of course." They mean it. "It is the only '
                             'thing anybody gets to decide about this and it '
                             'would be obscene to argue."\n\n'
                             'They are noticeably warmer to you afterwards, '
                             'which you did not expect.',
                             sets=('archive_refused',)),
                  )),
        )),

    # ------------------------------------------------------------------
    Thread(
        'ozymandias', 'Ozymandias',
        'A vending machine with a name, an offering, and opinions.',
        crosses=('deepwater',),
        stages=(
            Stage('coins', 'Somebody leaves coins',
                  'There is a small pile at the base of it, and it is not a '
                  'joke, or it is a joke that several people are maintaining '
                  'with unusual commitment.',
                  requires=('met:vending',),
                  sets=('ozy_met',)),
            Stage('war', 'You ask him about the war',
                  'The sign says not to. You do.\n\n'
                  'The display scrolls for a long time. It describes, in '
                  'flat capitals and considerable detail, a dispute between '
                  'two vending routes in 2041 that resulted in the physical '
                  'destruction of nine machines, and it names all nine, and '
                  'it is not clear at any point whether this is a bit.\n\n'
                  'It ends: THEY WERE NOT REPLACED. THEY WERE RESTOCKED.',
                  requires=('ozy_met',),
                  sets=('ozy_war',)),
            Stage('answer', 'You ask him about Deepwater',
                  'You ask. The display goes blank.\n\n'
                  'It stays blank for four seconds, which for a machine that '
                  'has never once in your presence failed to have an opinion '
                  'is the longest silence in this city.\n\n'
                  'Then: NO.\n\n'
                  'Then, after a while: I DO NOT WANT TO. Which is not a '
                  'sentence a fault in a coin mechanism produces.',
                  requires=('ozy_war', 'dw_heard'),
                  sets=('ozy_deepwater', 'dw_heard')),
        )),
)

BY_KEY: dict[str, Thread] = {t.key: t for t in THREADS}
THREAD_KEYS: tuple[str, ...] = tuple(BY_KEY)

#: Every stage key, for the journal and for validation.
ALL_STAGES: dict[str, Stage] = {
    f'{t.key}.{s.key}': s for t in THREADS for s in t.stages
}


def flags_set() -> set[str]:
    """Every flag anything in this file can set."""
    out: set[str] = set()
    for thread in THREADS:
        for stage in thread.stages:
            out.update(stage.sets)
            for choice in stage.choices:
                out.update(choice.sets)
    return out


def flags_required() -> set[str]:
    """Every plain flag anything requires, conditions excluded."""
    out: set[str] = set()
    for thread in THREADS:
        for stage in thread.stages:
            for rule in tuple(stage.requires) + tuple(stage.any_of):
                if ':' not in rule:
                    out.add(rule)
    return out
