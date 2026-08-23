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
#: 'rep:<faction>:N', 'ran:<faction>', 'did:<thread.stage>' (a posting
#: finished, see `Posting`).
CONDITIONS = ('runs', 'diss', 'shift', 'credits', 'heat', 'met', 'rep',
              'ran', 'origin', 'debt', 'trait', 'did', 'bond', 'found',
              'street', 'warned', 'heard', 'arranged')


@dataclass(frozen=True, slots=True)
class Posting:
    """A contract a scene puts on the board. D52: story inside runs.

    Built by the ordinary generator and then bent: the patron, target and
    objective are fixed, the title and blurb are the scene's, and `label`
    names the objective record so the brief says what the run is actually
    for. It does not expire and nobody else takes it, because a story beat
    that a rival can walk off with is a story beat the player may never see.
    Finishing it sets `did:<thread>.<stage>`, which is how a later scene
    knows you did the thing rather than read about it.
    """

    patron: str
    target: str
    objective: str
    title: str
    blurb: str
    #: What the objective record is called, in the brief and on the node.
    label: str = ''
    #: Fixed pay, or 0 to price it like any other contract of its shape.
    pay: int = 0


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
    #: Catalogue keys that go into the bag. A choice whose prose hands you a
    #: thing has to actually hand it over, or it is the oldest bug in this
    #: project wearing a story.
    gives: tuple[str, ...] = ()
    #: Dissonance the choice costs, or restores if negative. Reading your own
    #: log to the end is the kind of thing that should leave a mark.
    drift: int = 0
    #: If set, the choice finishes the character, and this is how: the word
    #: the roster and `characters` will use, in the past tense, e.g. 'went
    #: under'. The third exit, after the door and black ICE (D52).
    ends: str = ''


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
    #: A contract this scene puts on the board when it is reached. See
    #: `Posting`. Most scenes post nothing.
    posts: Posting | None = None


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
        crosses=('archive', 'ozymandias', 'drawer', 'favour', 'package', 'lark', 'demo', 'listener',),
        stages=(
            # -- act one: hearing it -----------------------------------------
            Stage('hear', 'Somebody mentioned it and then stopped',
                  'It comes up the way weather comes up. Somebody says the '
                  'name, and then does not say the next thing, and the '
                  'conversation goes somewhere else with a small limp in it.',
                  requires=('runs:2',),
                  sets=('dw_heard',)),
            # -- act two: three facts, from three people -----------------------
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
            Stage('pattern', 'Three facts, and the shape they make',
                  'Nine logs that do not end. A name it should not know. A '
                  'network with nothing arranged around anything. You put '
                  'them next to each other the way Remnant put their two '
                  'facts next to each other, and you have what they did not '
                  'have, which is a third one, and it does not help.\n\n'
                  'Whatever Deepwater is, it is not guarding anything, '
                  'because guarding is what you do to a thing you are '
                  'outside of.',
                  requires=('dw_logs', 'dw_name', 'dw_inside'),
                  sets=('dw_pattern',)),
            # -- act three: the posting ----------------------------------------
            Stage('posting', 'A posting with your name in it',
                  'It comes through Mara, like all of them, and she holds it '
                  'a moment longer than she holds the others.\n\n'
                  '"Deepwater. Exfiltrate. Their own network, which is not a '
                  'thing anybody has asked for before, and I have placed four '
                  'hundred of these." She puts it on the counter rather than '
                  'into your hand. "The record has a name on it. It is '
                  'yours."\n\n'
                  'She does not say what she thinks that means. She goes back '
                  'to the book. The posting does not expire, which she also '
                  'does not mention, and which you find out by watching it '
                  'not expire.',
                  requires=('dw_heard', 'runs:5'),
                  any_of=('dw_logs', 'dw_name', 'dw_inside', 'ozy_deepwater'),
                  sets=('dw_posting',),
                  posts=Posting(
                      patron='deepwater', target='deepwater',
                      objective='exfiltrate',
                      title='Four Hundred and Eight',
                      blurb='Deepwater wants something taken out of a '
                            'Deepwater network. The record has your handle '
                            'on it. Nobody will say whose idea that was, and '
                            'nobody else on the board will touch it.',
                      label='a log with your handle in the header',
                      pay=6000)),
            # -- act four: what you carried out --------------------------------
            Stage('carried', 'You read it, or you do not',
                  'It is a log. Your log: the handle in the header is the one '
                  'on the roster, spelled the way you spell it. It is longer '
                  'than you have been running.\n\n'
                  'The early entries are yours. You recognise the mistakes. '
                  'Somewhere past the middle the entries stop being things '
                  'you did and carry on being things you do, in the same '
                  'voice, with the same mistakes, and the last entry is dated '
                  'the day after tomorrow.\n\n'
                  'You have it on your deck. Nobody is asking for it back.',
                  requires=('did:deepwater.posting',),
                  sets=('dw_carried',),
                  choices=(
                      Choice('read', 'Read it to the end',
                             'You read it. The entry for the day after '
                             'tomorrow is not frightening. It is a Tuesday: a '
                             'contract, a clean exit, a noodle bar. That is '
                             'the frightening part, and it does not leave, '
                             'and some of the log is in you now in the way a '
                             'tune is.\n\n'
                             'You are not sure, afterwards, which of you '
                             'wrote the next entry.',
                             sets=('dw_read',), gives=('yourlog',),
                             drift=6),
                      Choice('archive', 'Give it to the Archivist',
                             'You take it to the fence with the back room. If '
                             'you have never been, you find it anyway: the '
                             'address is in the log, a week from now.\n\n'
                             'They take it in both hands and do not turn '
                             'round. "Four hundred and eight," they say, and '
                             'then, after a while, "it is still being '
                             'written. I do not know how to file that." They '
                             'put it on its own shelf.',
                             sets=('dw_archived',)),
                      Choice('burn', 'Wipe it',
                             'You wipe it, and it takes longer than wiping a '
                             'file takes, and when it is gone your deck runs '
                             'a fraction cooler than it did, which you notice '
                             'and then decide not to have noticed.\n\n'
                             'Somewhere, presumably, the entry for the day '
                             'after tomorrow is still being written. It is '
                             'just not being written here.',
                             sets=('dw_burned',)),
                  )),
            # -- act five: the offer, and the other door ----------------------
            Stage('offer', 'It would like to hire you',
                  'The contract arrives through Mara, who does not look at '
                  'you while she hands it over, which is new.\n\n'
                  '"Nine years I have placed these. This is the first one '
                  'with a name on it." A pause. "Your name."\n\n'
                  'The brief is four words long and the payment has already '
                  'cleared.',
                  requires=('dw_heard',),
                  any_of=('dw_pattern', 'dw_carried'),
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
                             sets=('dw_published',), gives=('samizdat',),
                             rep={'static': 25, 'meridian': -10},
                             credits=3000),
                  )),
            Stage('under', 'It asks',
                  'It asks the way the Archivist asked: formally, for '
                  'something it will only ever have if you give it.\n\n'
                  'It comes through the deck, not through Mara. There is no '
                  'brief. There is depth, and pressure, and the sense of '
                  'enormous slow structure somewhere below the resolution you '
                  'are being permitted, and in the middle of it, in your '
                  'voice, with your mistakes, a question.\n\n'
                  'Lark is alive because of something you did. The Archivist '
                  'has your name in a book because you said they could. You '
                  'have read the entry for the day after tomorrow. It knows '
                  'all three of those things, and it is not using them. It is '
                  'just asking.',
                  requires=('dw_offer', 'dw_read', 'archive_consented',
                            'lark_saved'),
                  sets=('dw_asked',),
                  choices=(
                      Choice('go', 'Go under',
                             'You jack in with no contract and nothing loaded '
                             'and you do not jack out.\n\n'
                             'Somebody will find the deck warm and the chair '
                             'occupied and the trace at zero, which is not a '
                             'number a trace can be. The log on the '
                             'Archivist\'s shelf, or the one that was never '
                             'there, gets its next entry on time.\n\n'
                             'The city will say your name to somebody who '
                             'never met you. It will be wrong about most of '
                             'it, and right about the Tuesday.',
                             sets=('dw_under',),
                             ends='went under'),
                      Choice('stay', 'Say no',
                             'You say no, the way the Archivist was told no: '
                             'plainly, once.\n\n'
                             'It does not ask again. That is the whole of '
                             'what happens, and for a long time afterwards it '
                             'is the loudest thing in any network you run: '
                             'the specific quiet of something that could '
                             'have, and did not.',
                             sets=('dw_stayed',)),
                  )),
        )),

    # ------------------------------------------------------------------
    Thread(
        'lark', 'Lark',
        'Somebody your age, on the wrong side of their own chrome.',
        crosses=('vance', 'sparrow', 'deepwater'),
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
        crosses=('lark', 'archive', 'drawer', 'maintenance', 'ward',
                 'cabinets'),
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
        crosses=('sunday', 'deepwater', 'vance', 'file', 'surplus',
                 'cabinets'),
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
        crosses=('deepwater', 'vance', 'oldname'),
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
                             sets=('archive_consented',), gives=('fourohsix',)),
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


def flags_chosen() -> dict[str, tuple[str, str, str]]:
    """Every flag a *choice* sets, mapped to (thread, stage, choice).

    These are the decisions, as opposed to the stages, which are merely the
    things that happened. D51 holds every one of them to being read by
    something: a later scene, an offer, an event, the streets, the board, or
    the ending. A decision nothing reads is prose with a flag on it.
    """
    out: dict[str, tuple[str, str, str]] = {}
    for thread in THREADS:
        for stage in thread.stages:
            for choice in stage.choices:
                for flag in choice.sets:
                    out.setdefault(flag, (thread.key, stage.key, choice.key))
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


# --------------------------------------------------------------------------
# origin complications
# --------------------------------------------------------------------------
#
# Every origin has shipped with a complication since the first day of this
# project, and until now every one of them was a sentence. These are the same
# sentences with a thread behind them.
#
# They gate on `origin:<key>`, so a given character sees exactly one of them,
# and they cross into the general threads wherever the fiction wants: the
# defector's laptop and the indentured runner's buyout are both Kagawa
# problems, and the courier's package has been sitting in the same city as
# Deepwater for two years.

ORIGIN_THREADS: tuple[Thread, ...] = (
    Thread(
        'laptop', 'The Laptop',
        'Kagawa want it back and have not decided about you.',
        crosses=(),
        stages=(
            Stage('contact', 'They have found a way to ask',
                  'The message is polite, correctly addressed, and arrives on '
                  'a channel you have not used since you left.\n\n'
                  'It does not threaten you. It does not mention the laptop. '
                  'It asks, in four lines of impeccable corporate English, '
                  'whether you would be available for a conversation, and '
                  'gives a time rather than proposing one.',
                  requires=('origin:defector',),
                  any_of=('runs:3', 'heat:25'),
                  sets=('laptop_contact',)),
            Stage('meeting', 'What they actually want',
                  'The person across the table is not from legal and does not '
                  'pretend to be.\n\n'
                  '"We do not want the machine. We want to know whether you '
                  'read the third partition, and I am authorised to tell you '
                  'that we will believe your answer, because the alternative '
                  'is a process neither of us has the budget for."\n\n'
                  'You did not know there was a third partition.',
                  requires=('laptop_contact',),
                  sets=('laptop_meeting',),
                  choices=(
                      Choice('give', 'Hand it back unopened',
                             'You give them the machine and tell them the '
                             'truth, which is that you never looked, and they '
                             'believe you, which is worse than being '
                             'disbelieved because it means they knew already.'
                             '\n\nThe payment is generous and arrives '
                             'itemised.',
                             sets=('laptop_returned',),
                             credits=7000,
                             rep={'kagawa': 25}),
                      Choice('read', 'Read the third partition first',
                             'Eleven thousand personnel files, and against '
                             'four hundred of them a second assessment nobody '
                             'was ever meant to see, scoring each person on '
                             'how much they would cost to replace against how '
                             'much they would cost to keep.\n\n'
                             'Your name is in it. Your number was low.',
                             sets=('laptop_read',),
                             rep={'kagawa': -20}),
                      Choice('sell', 'Sell it to somebody who is not Kagawa',
                             'Static will not pay much and will actually run '
                             'it. Meridian will pay a great deal and will '
                             'not.\n\nYou take the money. The files do not '
                             'surface, and every so often over the next few '
                             'shifts you wonder which of the two decisions '
                             'that was.',
                             sets=('laptop_sold',),
                             credits=12000,
                             rep={'kagawa': -35, 'meridian': 15}),
                  )),
        )),
    Thread(
        'theirs', 'The Sixes Consider You Theirs',
        'They have not asked for anything yet.',
        crosses=('pumps',),
        stages=(
            Stage('ask', 'They ask',
                  'It is not a threat and it is not phrased as one. Somebody '
                  'you half know finds you in the Ninth and explains, at '
                  'length and with genuine warmth, how much the Sixes have '
                  'done for you.\n\n'
                  'Most of it is true. All of it happened before you were old '
                  'enough to decline it.\n\n'
                  'Then he tells you what they would like, and it is '
                  'nothing. A name. Somebody left a door open in the '
                  'Terraces on a Tuesday and half the Ninth knows which '
                  'somebody, and the Sixes would rather hear it from '
                  'a person they have been good to than from a person '
                  'they have not.',
                  requires=('origin:gutter',),
                  any_of=('runs:4', 'rep:sixes:30'),
                  sets=('theirs_asked',),
                  choices=(
                      Choice('yes', 'Give them the name',
                             'You do it, and it is easy, and the warmth is '
                             'real afterwards. That is the part nobody warns '
                             'you about: it is a good deal every single time '
                             'and there is never a moment where refusing '
                             'would obviously have been better.',
                             sets=('theirs_owned',),
                             credits=3000,
                             rep={'sixes': 25, 'carrion': -15}),
                      Choice('no', 'Say you do not know it',
                             'He takes it well. He takes it so well that you '
                             'spend two shifts waiting for the other thing, '
                             'and the other thing does not come, and by the '
                             'fourth shift you understand that it already '
                             'has: nobody in the Ninth is rude to you and '
                             'nobody in the Ninth is anything else either.',
                             sets=('theirs_refused',),
                             rep={'sixes': -30}),
                  )),
        )),
    Thread(
        'favour', 'What Mara Is Owed',
        'She has never once said what.',
        crosses=('deepwater',),
        stages=(
            Stage('ask', 'She says what',
                  'She waits until the bar is empty, which for Mara is a '
                  'gesture roughly equivalent to shouting.\n\n'
                  '"Nineteen years ago I paid somebody to not do something. '
                  'It has come round. I need somebody to go somewhere I '
                  'cannot be seen going, and I have been waiting for the '
                  'right person for eleven of those years."\n\n'
                  'She does not say why it is you.',
                  requires=('origin:protege', 'met:mara'),
                  any_of=('runs:5', 'rep:fixers:50'),
                  sets=('favour_asked',),
                  choices=(
                      Choice('go', 'Go',
                             'You go. What is there is a woman about Mara\'s '
                             'age in a room in the Terraces who has been '
                             'alive for nineteen years on the understanding '
                             'that nobody knows she is, and who takes one '
                             'look at your face and says the name of the bar.'
                             '\n\nMara never raises it again. She does not '
                             'have to.',
                             sets=('favour_done', 'dw_heard'), gives=('io_landline',),
                             rep={'fixers': 35},
                             disposition={'vesper': 15}),
                      Choice('ask', 'Ask what it is first',
                             '"No." A long pause. "I have thought about this '
                             'for eleven years and the version where I tell '
                             'you does not end well for either of us."\n\n'
                             'She does not ask again, and she is exactly as '
                             'warm as she was before, and something in the '
                             'noodle bar has changed shape permanently.',
                             sets=('favour_refused',),
                             rep={'fixers': -10}),
                  )),
        )),
    Thread(
        'lender', 'The Lender',
        'The loan on the deck is real and it is not a bank.',
        crosses=('collector',),
        stages=(
            Stage('visit', 'They stop sending messages',
                  'The department stopped answering. The lender did not. '
                  'Somebody is sitting on the step of wherever you are '
                  'staying, being extremely pleasant, with the numbers '
                  'written out on paper.',
                  requires=('origin:academic',),
                  any_of=('debt:12000', 'runs:5'),
                  sets=('lender_visit',),
                  choices=(
                      Choice('pay', 'Clear as much as you can, now',
                             'You put everything you have against it, and the '
                             'pleasant person writes you a receipt, and the '
                             'receipt is the first document in this whole '
                             'affair that anybody has given you.',
                             sets=('lender_paying',),
                             credits=-4000,
                             rep={'sixes': 12}),
                      Choice('work', 'Offer to work it off',
                             'They are delighted. They are so delighted that '
                             'you understand, several shifts later, that this '
                             'was always the product and the money was the '
                             'advertisement.',
                             sets=('lender_working',),
                             rep={'sixes': 20, 'nightwatch': -10}),
                      Choice('run', 'Say nothing and keep moving',
                             'Nothing happens for four shifts. On the fifth, '
                             'the deck is gone from where you left it, and '
                             'the pleasant person is on the step again with a '
                             'revised number and the same handwriting.',
                             sets=('lender_angry',),
                             rep={'sixes': -25}),
                  )),
        )),
    Thread(
        'file', 'The File With Your Name On',
        'Nightwatch have your biometrics and your service history.',
        crosses=('drawer', 'surplus'),
        stages=(
            Stage('achebe', 'Somebody on the desk still likes you',
                  'Sergeant Achebe does not look up. "There is a file. You '
                  'know there is a file."\n\n'
                  'He turns a page. "What you may not know is that it is '
                  'nineteen months out of date, because the person who was '
                  'updating it retired and nobody has been given the task, '
                  'and I have not raised it."',
                  requires=('origin:expolice',),
                  any_of=('met:desk', 'heat:40'),
                  sets=('file_known',),
                  choices=(
                      Choice('leave', 'Leave it out of date',
                             'You leave it. Nineteen months of drift is worth '
                             'more than a clean file and a fresh entry, and '
                             'Achebe is careful to have offered no opinion.',
                             sets=('file_stale',),
                             rep={'nightwatch': 5}),
                      Choice('close', 'Get it closed properly',
                             'It costs money and two shifts and a favour '
                             'Achebe will not describe. The file is closed, '
                             'formally, with a reason, and the reason is a '
                             'lie that will hold up.\n\n'
                             'Somebody, eventually, is going to check.',
                             sets=('file_closed',),
                             credits=-5000,
                             rep={'nightwatch': 20}),
                  )),
        )),
    Thread(
        'maintenance', 'The Maintenance Address',
        'Something in the ocular suite is reporting somewhere.',
        crosses=('vance',),
        stages=(
            Stage('trace', 'You look at where it goes',
                  'It takes an evening and it is not difficult, which is the '
                  'first thing that is wrong with it.\n\n'
                  'The address is inside Aoyama Green, it is live, it has '
                  'been receiving from you for as long as you have had the '
                  'suite, and the volume is very small and very regular and '
                  'has never once spiked.',
                  requires=('origin:chromed',),
                  any_of=('diss:45', 'runs:4'),
                  sets=('maint_traced',),
                  choices=(
                      Choice('cut', 'Cut it',
                             'You cut it. The suite works exactly as before '
                             'and nothing contacts you about it, and eleven '
                             'shifts later your left eye develops a '
                             'four-second lag on low light that no clinic can '
                             'find a cause for.',
                             sets=('maint_cut',),
                             rep={'aoyama': -15}),
                      Choice('feed', 'Feed it something else',
                             'You leave it running and start deciding what it '
                             'sees. It is the most enjoyable eleven minutes '
                             'of your month and you are aware that this says '
                             'something about you.',
                             sets=('maint_fed',),
                             rep={'aoyama': -5},
                             credits=1500),
                      Choice('ask', 'Ask Aoyama about it, directly',
                             'Doctor Vance answers within the hour, in person, '
                             'delighted. "Post-market surveillance. It is in '
                             'the consent form and nobody has ever read the '
                             'consent form." She is telling the truth. She '
                             'has the form.',
                             sets=('maint_asked', 'vance_file'),
                             rep={'aoyama': 10}),
                  )),
        )),
    Thread(
        'buyout', 'The Buyout Figure',
        'Kagawa priced you at nineteen and the price has never gone down.',
        crosses=('reviews',),
        stages=(
            Stage('review', 'They offer to review it',
                  'The letter is warm. It notes your recent independent '
                  'activity, expresses no opinion about it, and invites you '
                  'to a review of your buyout figure at your convenience.\n\n'
                  'The last person you knew who attended one came back with '
                  'a smaller number and a longer contract.',
                  requires=('origin:bonded',),
                  any_of=('runs:5', 'credits:15000'),
                  sets=('buyout_review',),
                  choices=(
                      Choice('attend', 'Go to the review',
                             'The number comes down by nine thousand. The '
                             'terms extend by four years. Everybody in the '
                             'room is pleased and the arithmetic is correct '
                             'and you sign it because the arithmetic is '
                             'correct.',
                             sets=('buyout_extended',),
                             rep={'kagawa': 20}),
                      Choice('ignore', 'Do not go',
                             'Nothing happens. Nothing continues to happen '
                             'for some time, and then the figure is revised '
                             'upward without explanation and the letter '
                             'accompanying it is exactly as warm as the '
                             'first one.',
                             sets=('buyout_ignored',),
                             rep={'kagawa': -10}),
                  )),
        )),
    Thread(
        'incident', 'The Incident File',
        'Somebody at Sendai still has it, with your working name on the cover.',
        crosses=(),
        stages=(
            Stage('pike', 'Somebody who was in the room',
                  'Old Pike listens to the whole thing without interrupting, '
                  'which nobody has ever done.\n\n'
                  '"I read that file." He watches the cranes. "You are not in '
                  'it as a perpetrator. You are in it as a result. There is a '
                  'difference and it is the only good news I have."',
                  requires=('origin:burnout',),
                  any_of=('met:pike_sr', 'runs:4'),
                  sets=('incident_read',),
                  choices=(
                      Choice('know', 'Ask what actually happened',
                             'He tells you. It takes forty minutes and it is '
                             'not what you remember, in the specific way that '
                             'means one of you is wrong and both of you were '
                             'there.\n\n'
                             'You sleep badly and then, for the first time in '
                             'four years, well.',
                             sets=('incident_known',),
                             disposition={'ledger': 10}),
                      Choice('leave', 'Decide you do not want it',
                             '"Good." He does not elaborate and does not '
                             'look at you differently, and it is the kindest '
                             'thing anybody has done for you in some time.',
                             sets=('incident_left',)),
                  )),
        )),
    Thread(
        'oldname', 'Somebody Is Using Your Name',
        'The one you had before the certificate.',
        crosses=('archive', 'vote'),
        stages=(
            Stage('found', 'It turns up',
                  'It is on a manifest, of all things: a name you have not '
                  'been for eleven months, attached to a shipment, in the '
                  'present tense.\n\n'
                  'Whoever they are, they are not hiding. They are filing '
                  'paperwork.',
                  requires=('origin:ghost',),
                  any_of=('runs:4', 'met:quartermaster'),
                  sets=('oldname_found',)),
            Stage('who', 'Who it is',
                  'You find them in a Freeport office doing something '
                  'entirely legitimate with a name that used to be yours, and '
                  'they look up, and they are not surprised, and the first '
                  'thing they say is your handle.\n\n'
                  '"I bought it," they say, reasonably. "Eleven months ago, '
                  'from an estate. I did not know there was anybody left to '
                  'mind."',
                  requires=('oldname_found',),
                  any_of=('runs:7', 'met:quartermaster', 'archive_met'),
                  sets=('oldname_met',),
                  choices=(
                      Choice('take', 'Take it back',
                             'You take it back, which is expensive and '
                             'legally intricate and, when it is finished, '
                             'leaves you holding a name you did not want and '
                             'somebody else without one.',
                             sets=('oldname_reclaimed',),
                             credits=-6000),
                      Choice('leave', 'Let them keep it',
                             'You let them keep it. They are doing more with '
                             'it than you were, and they file the paperwork, '
                             'and somewhere in a municipal system you are '
                             'now marginally more alive than you were last '
                             'week.',
                             sets=('oldname_left',),
                             rep={'freeport': 12})),
                  ),
        )),
    Thread(
        'package', 'The Package',
        'You never delivered it and the sender has been dead two years.',
        crosses=('deepwater',),
        stages=(
            Stage('still', 'It is still there',
                  'You have moved four times and it has come with you every '
                  'time, in the same wrapping, with the same address on it in '
                  'handwriting belonging to somebody who has been dead for '
                  'two years.',
                  requires=('origin:courier',),
                  any_of=('runs:3', 'shift:15'),
                  sets=('package_still',)),
            Stage('address', 'The address is live',
                  'You check it, finally, expecting a demolished block.\n\n'
                  'It is a live address. Somebody is at it. There is a '
                  'standing order on the account for a delivery that has '
                  'never arrived, renewed annually, most recently four months '
                  'ago.',
                  requires=('package_still',),
                  any_of=('runs:6', 'dw_heard'),
                  sets=('package_address',),
                  choices=(
                      Choice('deliver', 'Deliver it',
                             'You deliver it, two years late, to somebody who '
                             'takes it without any particular ceremony and '
                             'signs for it and thanks you.\n\n'
                             'The standing order stops the following month. '
                             'You never find out what was in it and you have '
                             'stopped minding.',
                             sets=('package_delivered',),
                             credits=4000,
                             rep={'fixers': 15}),
                      Choice('open', 'Open it',
                             'Inside is a deck component, obsolete, in its '
                             'original packaging, and a note reading: FOR '
                             'WHEN YOU ARE READY TO STOP RUNNING ABOUT.\n\n'
                             'It is addressed to you. It has always been '
                             'addressed to you. You have been carrying your '
                             'own present around for two years.',
                             sets=('package_opened',),
                             gives=('io_copper',),
                             credits=2000),
                      Choice('burn', 'Get rid of it',
                             'You put it in an incinerator in the Ninth and '
                             'watch until it is gone, and it takes '
                             'considerably longer than you expected, and you '
                             'stay for all of it.',
                             sets=('package_burned',)),
                  )),
        )),
    Thread(
        'stoplist', 'Your Name In The Header',
        'Forty thousand pages carry it, and one of them was the edition '
        'Kagawa asked the Watch to stop.',
        crosses=('presses',),
        stages=(
            Stage('filed', 'Somebody has the edition',
                  'Ines Vale finds you on the floor with a sheet she has '
                  'clearly been holding for a while, and does not hand it '
                  'over, she just turns it round.\n\n'
                  'It is a page you set. Nine years ago, a Tuesday, a '
                  'correction that ran under a story about the water board, '
                  'and your name is in the header because you set it, and '
                  'the whole page has been photographed by somebody standing '
                  'over it with the light wrong. "This came back to us," she '
                  'says. "From a person who buys things. They wanted to know '
                  'if the compositor still worked here."',
                  requires=('origin:printer',),
                  sets=('stoplist_filed',),
                  where='stacks'),
            Stage('buyer', 'The person who buys things',
                  'They are not from Kagawa and they say so before you ask, '
                  'in the way people say a thing they have practised. They '
                  'buy pages. Specifically, they buy the plates: the metal a '
                  'page was set in, which the Stacks keep, because the '
                  'Stacks keep everything.\n\n'
                  '"The plate for that correction is in the last shack on '
                  'Correction Row," they say. "You know it is. I would like '
                  'it, and I will pay a number that will surprise you, and '
                  'you should ask yourself why."',
                  requires=('stoplist_filed',),
                  any_of=('runs:2', 'presses_floor'),
                  sets=('stoplist_offer',),
                  choices=(
                      Choice('sell', 'Sell them the plate',
                             'You go down Correction Row at an hour when '
                             'nobody is on it and take a piece of metal out '
                             'of a box of every edition ever printed here, in '
                             'order, and nobody stops you because nobody in '
                             'the Stacks has ever locked that door.\n\n'
                             'The number does surprise you. A month later '
                             'the correction is quoted in a filing you will '
                             'never read, and the water board settles '
                             'something, and the Ninth does not hear about '
                             'it, and Ines does not mention the gap in the '
                             'box.',
                             sets=('stoplist_sold',),
                             credits=3400,
                             rep={'static': -20, 'meridian': 10}),
                      Choice('print', 'Print it again instead',
                             'You set it again, from the plate, on the small '
                             'press, and run four hundred, and they go out '
                             'with the morning edition folded inside it '
                             'where the shutters go up.\n\n'
                             'Ines watches you do the whole thing and says '
                             'nothing at all, which from Ines is the loudest '
                             'she gets. Kagawa\'s stop list gets one item '
                             'longer, and everybody who reads it knows the '
                             'name in the header.',
                             sets=('stoplist_reprinted',),
                             rep={'static': 25, 'kagawa': -25}),
                      Choice('melt', 'Melt the plate',
                             'The ink store has a drum and the drum has a '
                             'burner under it, and metal is metal. It takes '
                             'a while. You stand and watch it because '
                             'leaving would be worse.\n\n'
                             'Nobody can quote what does not exist, on '
                             'either side. The buyer stops answering. Ines '
                             'finds the gap in the box within a week, and '
                             'asks you once, and believes you, and that is '
                             'somehow the worst part.',
                             sets=('stoplist_melted',)),
                  ),
                  where='stacks'),
        )),
    Thread(
        'tin_debt', 'The Debt With No Number',
        'The Hall fed you for twenty years and has never asked for anything.',
        crosses=('soup',),
        stages=(
            Stage('asked', 'Somebody finally asks',
                  'Not the Cantor. A woman on the kitchen rota you have known '
                  'since you were both eight, who stirs while she talks so '
                  'that it is not a conversation you are having face to '
                  'face.\n\n'
                  '"The boiler," she says. "Not the kettle, the boiler, the '
                  'one that does the whole east wing. Kagawa will not sell '
                  'us the part. It is on a list. Everything is on a list." '
                  'She stops stirring. "You do the thing you do. Nobody has '
                  'asked you. I am asking you."',
                  requires=('origin:chorister',),
                  any_of=('runs:2', 'soup_kettle'),
                  sets=('tin_asked',),
                  posts=Posting(
                      patron='chorus', target='kagawa', objective='exfiltrate',
                      title='The Part',
                      blurb='A part number, a supplier, and the authorisation '
                            'that would let the Hall buy a boiler component '
                            'Kagawa have put on a list. The Chorus are not '
                            'offering much. They are asking.',
                      label='the supply authorisation',
                      pay=1400),
                  where='hall'),
            Stage('boiler', 'What the authorisation is worth',
                  'It is not a part number. It is an authorisation, and it '
                  'is general: it would let the Hall buy the boiler part, and '
                  'it would let anybody buy anything on that list, from any '
                  'Kagawa supplier, until somebody notices.\n\n'
                  'The woman on the rota wants a boiler. What is in your hand '
                  'is a year of anything.',
                  requires=('did:tin_debt.asked',),
                  sets=('tin_held',),
                  choices=(
                      Choice('boiler', 'Buy the boiler part and stop',
                             'One part, one supplier, one invoice that reads '
                             'exactly like nine thousand other invoices, and '
                             'the east wing is warm by the weekend.\n\n'
                             'Nobody thanks you, because nobody outside the '
                             'kitchen knows, because you asked her not to '
                             'say. She stirs. The Hall is warm. That is the '
                             'whole of it, and it turns out to be enough.',
                             sets=('tin_boiler',),
                             rep={'chorus': 25}),
                      Choice('spend', 'Spend it while it lasts',
                             'You buy the boiler part. Then you buy the '
                             'things the clinic has been going without, and '
                             'the things the kitchen has, and then, because '
                             'the authorisation is still good, a few things '
                             'that are worth money elsewhere.\n\n'
                             'It lasts eleven days. When it stops, it stops '
                             'in the middle of an order, and somebody at '
                             'Kagawa has a list of everything bought under it '
                             'with the Hall\'s name at the top.',
                             sets=('tin_spent',),
                             credits=2600,
                             rep={'chorus': -10, 'kagawa': -20}),
                      Choice('sell', 'Sell the authorisation',
                             'A man in Marrow pays for it the way you pay for '
                             'something you intend to use badly, which is '
                             'promptly and without questions.\n\n'
                             'The east wing is not warm. You tell her the '
                             'authorisation did not work, and she says, '
                             '"Right," and goes back to stirring, and does '
                             'not ask you anything else, that week or after.',
                             sets=('tin_sold',),
                             credits=3800,
                             rep={'chorus': -30, 'fixers': 10}),
                  ),
                  where='hall'),
        )),
)

#: Origin threads live in the same registry as everything else: they are just
#: threads that happen to gate on a background.
#: The nine district threads live in `arcs.py` (D55) and import the classes
#: above, which is why this import is at the bottom: by the time it runs,
#: everything they need is defined.
from .arcs import DISTRICT_THREADS, MORE_THREADS, RUNNER_THREAD  # noqa: E402

THREADS = (THREADS + ORIGIN_THREADS + DISTRICT_THREADS + MORE_THREADS
           + (RUNNER_THREAD,))
BY_KEY = {t.key: t for t in THREADS}
THREAD_KEYS = tuple(BY_KEY)
ALL_STAGES = {f'{t.key}.{s.key}': s for t in THREADS for s in t.stages}
