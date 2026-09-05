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
CONDITIONS = ('runs', 'diss', 'shift', 'credits', 'heat', 'bounty', 'met', 'rep',
              'ran', 'origin', 'debt', 'trait', 'did', 'bond', 'found',
              'street', 'warned', 'heard', 'arranged',
              # The half of the game with the deck in the bag (D140): what
              # you can do, what you carry, what you are hooked on, what
              # the wall says, and what a fight left on you.
              'skill', 'pit', 'habit', 'carrying', 'mark', 'fought', 'job',
              # How much of the city you have stood in and found (D147),
              # as counts, so the explorer has threads that read it.
              'places', 'finds',
              # How many lines of the record you have earned (D150),
              # so the achiever has a thread the scoreboard opens.
              'record',
              # `asked:<npc>:<topic>`: set by `ask`, so a scene that is
              # written as a question can wait for the question (D86).
              'asked',
              # `visited:<place>`: set by `visit`, so a scene can be written
              # for standing somewhere (D91).
              'visited')


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
    #: What the choice does to the debt, if one is owed (D95): negative
    #: pays it down, positive adds to it. The buyout review said "the
    #: number comes down by nine thousand" and the number did not move.
    debt: int = 0


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
    #: Shifts that must have passed since the thread's previous stage, or
    #: since meeting the person the stage requires if it is the first
    #: (D91). A scene that says "the second time you see them" cannot fire
    #: in the same breath as the first.
    after: int = 0
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


#: The flags the main line ends on (D143). The record, the settle, the
#: ambition and the board all read them (D144), so the list lives here.
SPINE_ENDINGS: frozenset = frozenset(
    ('dw_employed', 'dw_published', 'dw_refused', 'dw_under', 'dw_stayed'))

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
                  after=2, requires=('met:lark',),
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
                  after=3, requires=('met:broker', 'runs:3'),
                  sets=('sunday_noticed',)),
            Stage('tell', 'The one thing that does not move',
                  'Every job he has offered you has been against somebody '
                  'who owes Meridian money.\n\n'
                  'Not most. Every one. It took writing them down to see it, '
                  'because individually each brief is a different faction '
                  'wanting a different thing, and collectively they are a '
                  'bank tidying up.',
                  after=4, requires=('sunday_noticed',),
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
            # The sign says not to. The scene used to fire on the next
            # `look` after meeting him, narrating a question nobody had
            # typed; `ask vending war` is what sets this now (D86).
            Stage('war', 'You ask him about the war',
                  'The sign says not to. You do.\n\n'
                  'The display scrolls for a long time. It describes, in '
                  'flat capitals and considerable detail, a dispute between '
                  'two vending routes in 2041 that resulted in the physical '
                  'destruction of nine machines, and it names all nine, and '
                  'it is not clear at any point whether this is a bit.\n\n'
                  'It ends: THEY WERE NOT REPLACED. THEY WERE RESTOCKED.',
                  requires=('ozy_met', 'asked:vending:war'),
                  sets=('ozy_war',)),
            Stage('answer', 'You ask him about Deepwater',
                  'You ask. The display goes blank.\n\n'
                  'It stays blank for four seconds, which for a machine that '
                  'has never once in your presence failed to have an opinion '
                  'is the longest silence in this city.\n\n'
                  'Then: NO.\n\n'
                  'Then, after a while: I DO NOT WANT TO. Which is not a '
                  'sentence a fault in a coin mechanism produces.',
                  requires=('ozy_war', 'dw_heard', 'asked:vending:deepwater'),
                  sets=('ozy_deepwater', 'dw_heard')),
        )),
    # -- the half with the deck in the bag (D140) ---------------------------
    Thread(
        'weight', 'The Weight',
        'The house keeps a book, and the book is not about who wins.',
        (
            Stage('noticed', 'Hollis writes a line about you',
                  'You are two rungs up the wall and Hollis has stopped '
                  'writing your name and started writing sentences after it. '
                  'She turns the ledger round so you can read the line, which '
                  'is a courtesy nobody else on the ramp gets.\n\n'
                  '"Draws a crowd. Does not know it yet." She turns it back. '
                  '"That is worth more than the winning. The winning is worth '
                  'a purse. That is worth a season."',
                  requires=('met:hollis', 'pit:2'),
                  sets=('weight_noticed',), where='shambles'),
            Stage('offer', 'The house would like one to go the other way',
                  'Hollis does not dress it up, which you find you are '
                  'grateful for.\n\n'
                  '"There is money on you now. Enough that the money would '
                  'like a say. One bout, you go down in the third, and the '
                  'house makes more on that than on six of you winning." She '
                  'closes the book. "I am asking because I would rather ask. '
                  'Carrion would not have asked."',
                  requires=('weight_noticed', 'pit:3'), where='shambles',
                  after=2,
                  choices=(
                      Choice('dive', 'Go down in the third',
                             'You go down in the third and you make it '
                             'honest, which is harder than winning and nobody '
                             'in the room will ever know you did it. The '
                             'money changes hands somewhere above you. Hollis '
                             'writes one line and does not turn the book '
                             'round.\n\nThe crowd is quieter with you after. '
                             'Not hostile. Quieter, the way people are with '
                             'somebody they have stopped being curious about.',
                             sets=('weight_dived',), credits=4200,
                             rep={'carrion': 12}),
                      Choice('straight', 'Fight it straight and tell her so',
                             'You tell her no, in the room, at the table, '
                             'with the book open. She looks at you for a long '
                             'moment and then writes something quite short.'
                             '\n\n"Good," she says, and means it, and then: '
                             '"That will cost you. Not from me." The next '
                             'three bouts the house books you are all a rung '
                             'above where they should be, and the crowd is '
                             'very loud for you, and you understand that '
                             'both of those are the same sentence.',
                             sets=('weight_straight',), rep={'carrion': -8}),
                      Choice('tell', 'Tell the floor what was asked',
                             'You say it on the tape, to sixty people, before '
                             'the bout. The room does the thing rooms do, '
                             'which is go quiet and then go very loud, and '
                             'Hollis sits with her hands flat on the book and '
                             'lets it happen.\n\nAfterwards she says the only '
                             'angry thing you will ever hear her say, which '
                             'is: "Eleven years and nobody has died on that '
                             'floor. You have just made me the story instead '
                             'of that."',
                             sets=('weight_told',), rep={'carrion': -25},
                             credits=0)),
                  ),
            Stage('after', 'What the book was for',
                  'Hollis is not at the table. The cash box is, and the '
                  'shotgun is, and a kid of about nineteen is sitting where '
                  'she sits, holding the ledger like it might go off.\n\n'
                  'She left the book open at your line. Under whatever she '
                  'wrote about the crowd, in the same flat hand: "Worth '
                  'asking. Asked."',
                  any_of=('weight_dived', 'weight_straight', 'weight_told'),
                  sets=('weight_closed',), where='shambles', after=4),
        )),
    Thread(
        'ninety', 'Ninety Seconds',
        'The crash is the price on the label, and the label is honest.',
        (
            Stage('noticed', 'Pell knows before you say anything',
                  'Pell looks up from the envelopes and reads you the way a '
                  'clinician reads a chart, and the terrible part is the '
                  'warmth.\n\n"You are on it," they say. "Not badly. I am not '
                  'saying badly. I am saying I can see the shape of the last '
                  'fortnight in how you are standing, and so can anybody else '
                  'who does this for a living, and some of them are not me."',
                  requires=('met:pell',),
                  any_of=('habit:redline:1', 'habit:numb:1'),
                  sets=('ninety_noticed',), where='shambles'),
            Stage('offer', 'A better batch, and what it costs',
                  'They have a different envelope out. It is not marked '
                  'differently and that is somehow worse.\n\n"Cleaner cut. '
                  'The high is the same and the crash is ninety seconds '
                  'shorter, which does not sound like much until it is you." '
                  'They put it down between you. "Cheaper, too. I will not '
                  'insult you by pretending that is not the point of the '
                  'conversation."',
                  requires=('ninety_noticed',),
                  any_of=('habit:redline:2', 'habit:numb:2'),
                  where='shambles', after=3,
                  choices=(
                      Choice('take', 'Take the cleaner cut',
                             'It is cleaner. Everything they said was true, '
                             'which is the thing about Pell that people find '
                             'hard afterwards. The crash is ninety seconds '
                             'shorter and it arrives on time and it is a '
                             'little further down than it used to be, and you '
                             'have a supply and a price and a person who '
                             'expects to see you.',
                             sets=('ninety_took',), credits=-600),
                      Choice('stop', 'Ask them what getting off it looks like',
                             'They tell you, in detail, for free, with the '
                             'envelope still on the counter. A clinic, a '
                             'fortnight, money, and the fortnight being the '
                             'part nobody has. Then they put the envelope '
                             'away without being asked, which is not nothing.'
                             '\n\n"Come back when you have the fortnight," '
                             'they say. "Not for this. For the other thing."',
                             sets=('ninety_stopped',)),
                      Choice('report', 'Say where the back of the clinic is',
                             'You tell somebody who can do something about '
                             'it, and something is done about it, and for '
                             'about nine days the Shambles is a district '
                             'where a particular thing is harder to get.\n\n'
                             'Then it is not. What has changed is that the '
                             'person who cooked it carefully has gone, and '
                             'the person who cooks it now does not read '
                             'anybody\'s chart.',
                             sets=('ninety_reported',),
                             rep={'carrion': -10, 'nightwatch': 10})),
                  ),
            Stage('after', 'The other thing',
                  'The clinic at the front has a new sign about a service it '
                  'has always offered and never advertised. Somewhere behind '
                  'it, the back room is a store room again, or it is not.\n\n'
                  'Either way there is an envelope on the counter with your '
                  'handle on it, and inside it is a folded paper with a '
                  'number of shifts written on it, and nothing else.',
                  any_of=('ninety_took', 'ninety_stopped', 'ninety_reported'),
                  sets=('ninety_closed',), where='shambles', after=5),
        )),
    Thread(
        'slot', 'The Slot',
        'An advertisement knew something about you that you had told nobody.',
        (
            Stage('addressed', 'The ad was about you',
                  'A slot on the wall of the exchange runs something that is '
                  'not for everybody. It is for somebody who was recently in '
                  'the state you are recently in, and it says so, warmly, and '
                  'then it sells them a thing.\n\nUnder the colonnade on the '
                  'Row, a man in a good coat says your last handle and then '
                  'apologises for it, and that is Marek Vig introducing '
                  'himself.',
                  requires=('met:vig', 'runs:3'),
                  any_of=('mark:blooded', 'habit:redline:1', 'heat:30',
                          'street:knives', 'carrying:loud'),
                  sets=('slot_addressed',)),
            Stage('file', 'Thirty-one lines',
                  '"Yours is thirty-one lines," Vig says. "I priced it on '
                  'Tuesday." He is not threatening you. He is showing you a '
                  'product, in the way a man shows you a product, and the '
                  'product is a description of your last two months assembled '
                  'from things that were each of them public.\n\n"You can buy '
                  'it. You can buy somebody else\'s. Or you can do the thing '
                  'the squeamish ones do, which never works, and which I '
                  'would honestly quite like to watch."',
                  requires=('slot_addressed',), where='row', after=2,
                  choices=(
                      Choice('buy', 'Buy your own file',
                             'You buy thirty-one lines about yourself and '
                             'read them in a doorway, and there is nothing in '
                             'there you did not do. That is the whole of the '
                             'horror and it takes about a minute to arrive.'
                             '\n\nThe slots go quiet about you for a while. '
                             'Vig did not promise that and does not mention '
                             'it, and it happens anyway, which is how you '
                             'learn what you actually bought.',
                             sets=('slot_bought',), credits=-3000),
                      Choice('sell', 'Buy somebody else\'s, and use it',
                             'It is four thousand for a description rather '
                             'than a name, and a description is enough when '
                             'you already know who you are looking for. What '
                             'you do with it is efficient and quiet and works '
                             'exactly as advertised.\n\nVig is pleased with '
                             'you in a way you will think about later, at an '
                             'hour when you would rather be asleep.',
                             sets=('slot_used',), credits=2600,
                             rep={'meridian': 10}),
                      Choice('burn', 'Put the operation in the public log',
                             'Static will not touch it. Freeport will, and '
                             'the Stacks print it, and for eleven days the '
                             'Row is a place where a certain kind of buyer '
                             'has to say what they are buying.\n\nVig sends a '
                             'message. It is not a threat, it is a receipt: '
                             'the eleven days cost him about nine per cent, '
                             'and he has written the number down, and he '
                             'wanted you to have it.',
                             sets=('slot_burned',),
                             rep={'meridian': -20, 'static': 12,
                                  'freeport': 10})),
                  ),
            Stage('after', 'What the file is now',
                  'The slots have your shape again, because the shape was '
                  'never the secret. What is different is that you can hear '
                  'the buying now: an advertisement lands and you know what '
                  'description you matched to be shown it, and you can name '
                  'the line.\n\nIt does not change anything. Vig said that '
                  'too, and Vig was right about it, and being right about it '
                  'is his entire profession.',
                  any_of=('slot_bought', 'slot_used', 'slot_burned'),
                  sets=('slot_closed',), after=4),
        )),

    # -- a thread for each way of working (D141) ----------------------------
    Thread(
        'nobody', 'Nobody Saw It',
        'Leaving nothing behind is a pattern, and patterns are what they do.',
        (
            Stage('pattern', 'The absence is the signature',
                  'The desk sergeant has a folder that is thinner than the '
                  'others and he taps it twice before he opens it.\n\n'
                  '"Eleven networks in this city have had a bad month and '
                  'none of them can tell me what happened. Not one alarm. No '
                  'residue worth the name." He turns it round. "Do you know '
                  'how many people in this city can do that? I do. It is a '
                  'short list and I did not have to write it down."',
                  requires=('met:desk', 'skill:stealth:3', 'runs:5'),
                  sets=('nobody_named',), where='precinct'),
            Stage('offer', 'He would like one of them noisy',
                  '"There is a house in the Terraces that I cannot get a '
                  'warrant near, because the people who sign warrants are on '
                  'the second floor of it." He does not blink. "I do not want '
                  'it robbed. I want it to have an incident. Loud enough to '
                  'be logged by somebody who is not me."\n\n'
                  'He puts a card on the desk with no name on it. "You are on '
                  'the short list either way. This is the version where being '
                  'on it is worth something."',
                  requires=('nobody_named',), where='precinct', after=3,
                  choices=(
                      Choice('loud', 'Make an incident, on purpose',
                             'It is the strangest run of your career: every '
                             'instinct you have spent years training says '
                             'quiet and you spend the whole of it doing the '
                             'opposite, deliberately, well.\n\nIt gets logged. '
                             'Somebody on the second floor has a very bad '
                             'fortnight. The desk sergeant never mentions it '
                             'again and the folder gets thicker, with other '
                             'people in it.',
                             sets=('nobody_loud',), credits=3800,
                             rep={'nightwatch': 18, 'kagawa': -12}),
                      Choice('quiet', 'Do it your way instead',
                             'You go in and you come out and there is no '
                             'incident, because you do not know how to leave '
                             'one, and what you bring him instead is the '
                             'second floor\'s own filing.\n\n"That is not what '
                             'I asked for," he says, reading it. He keeps '
                             'reading it. "That is considerably worse for '
                             'them. Get out of my station."',
                             sets=('nobody_quiet',), credits=2400,
                             rep={'nightwatch': 8, 'static': 10}),
                      Choice('walk', 'Tell him the list is his problem',
                             'You say no, in a police station, to a man '
                             'holding a folder with your working life in it, '
                             'and walk out past the desk and the queue and '
                             'the door.\n\nNothing happens. Nothing keeps '
                             'happening for a fortnight, and then the folder '
                             'turns up in the Stacks with somebody else\'s '
                             'name on the front, which is how you learn what '
                             'the list was actually for.',
                             sets=('nobody_walked',),
                             rep={'nightwatch': -15, 'static': 6})),
                  ),
            Stage('after', 'A short list, still',
                  'The desk in the Precinct has a new folder on it, thinner '
                  'than the others. You do not get to see whether your name '
                  'is still in it, and the not seeing is the point, and he '
                  'knows it is the point.',
                  any_of=('nobody_loud', 'nobody_quiet', 'nobody_walked'),
                  sets=('nobody_closed',), where='precinct', after=5),
        )),
    Thread(
        'order', 'Out of Order',
        'The queue at the exchange is not a queue. It is a market in places.',
        (
            Stage('place', 'Somebody sells the third place',
                  'The keeper of the queue has a clipboard, a folding stool '
                  'and an authority nobody has ever formally given her. She '
                  'watches you watch the queue for a while and then decides '
                  'you are worth explaining it to.\n\n"Fourth from the front '
                  'is worth six hundred on a Tuesday. Third is worth nine. '
                  'Nobody has ever written that down and everybody knows it, '
                  'and the Switchboard pretend the whole thing is weather."',
                  requires=('met:keeper', 'skill:subterfuge:3'),
                  sets=('order_place',), where='marrow'),
            Stage('jump', 'A man who cannot be seen queueing',
                  'A Switchboard man needs to be at the front at eleven and '
                  'cannot be seen in a queue, because being seen in a queue '
                  'is a statement about who he is.\n\nThe keeper puts it '
                  'plainly. "He wants the front and he wants nobody to have '
                  'been moved for him. Those are two different jobs and only '
                  'one of them is possible, so somebody is getting moved and '
                  'the question is who, and whether they know."',
                  requires=('order_place',), where='marrow', after=2,
                  choices=(
                      Choice('talk', 'Move somebody who agrees to be moved',
                             'You spend forty minutes finding the one person '
                             'in that queue who would rather have six hundred '
                             'than eleven o\'clock, and you find her, and the '
                             'whole thing costs the Switchboard a fee and '
                             'nobody a place.\n\nThe keeper watches the entire '
                             'operation with her arms folded and afterwards '
                             'says, "You could have just moved somebody," in '
                             'the tone of a person filing that away.',
                             sets=('order_talked',), credits=1400,
                             rep={'fixers': 12}),
                      Choice('bump', 'Move somebody who does not',
                             'It takes four minutes and a story about a '
                             'terminal fault, and the man is at the front at '
                             'eleven, and a woman who was there at six is not.'
                             '\n\nShe finds you afterwards. She is not angry, '
                             'which is worse: she wants to know what she did '
                             'wrong, because she has assumed for two hours '
                             'that she must have done something wrong.',
                             sets=('order_bumped',), credits=2200,
                             rep={'fixers': 15}),
                      Choice('expose', 'Tell the queue what it is worth',
                             'You say the numbers out loud to eighty people '
                             'standing in the rain, and the queue works out '
                             'in about ninety seconds that it has been a '
                             'market for years and that all of them were the '
                             'stock.\n\nThe keeper folds her stool. "Eleven '
                             'years I kept that fair," she says, and she is '
                             'not wrong, and neither are you, and the queue '
                             'behind you is already arguing about who was '
                             'here first.',
                             sets=('order_exposed',),
                             rep={'fixers': -18, 'static': 12})),
                  ),
            Stage('after', 'What the queue is now',
                  'The queue outside the exchange is longer and slower and '
                  'nobody is keeping it. Whether that is better is being '
                  'settled about four times a day by people standing in the '
                  'rain, which is one definition of a fair system and not the '
                  'one the keeper meant.',
                  any_of=('order_talked', 'order_bumped', 'order_exposed'),
                  sets=('order_closed',), where='marrow', after=4),
        )),
    Thread(
        'gooddog', 'A Good Dog',
        'Somebody left a daemon running on the cranes and it has opinions.',
        (
            Stage('found', 'It has been running for eleven months',
                  'The crane driver has stopped taking the new crane out and '
                  'she will not say why on the radio, so she says it to you, '
                  'on the gantry, over the noise.\n\n"There is something in '
                  'the load system. It is not a fault. It schedules. It has '
                  'been scheduling for eleven months and it is better at it '
                  'than the office, and last week it refused a lift and the '
                  'lift would have killed somebody, and I do not know what to '
                  'tell the rota."',
                  requires=('met:crane', 'skill:daemonology:3'),
                  sets=('dog_found',), where='freeport'),
            Stage('what', 'What to do with a thing that works',
                  'You read it on the gantry with the tide coming in. It is '
                  'somebody\'s work, abandoned, still going: a scheduler with '
                  'a safety clause bolted on by somebody who then left, and '
                  'the safety clause is why nobody died last week.\n\n'
                  'Freeport want to know if it is safe. The office want to '
                  'know who owns it. Nobody has asked what it wants because '
                  'it does not want anything, and the crane driver has '
                  'started saying "she" about it.',
                  requires=('dog_found',), where='freeport', after=3,
                  choices=(
                      Choice('keep', 'Document it and leave it running',
                             'You write it up properly: what it does, what it '
                             'refuses, and the one clause that makes it worth '
                             'keeping. The rota votes. It stays.\n\nThe crane '
                             'driver calls it by a name within a fortnight '
                             'and the whole dock has picked it up within '
                             'three, and none of that is in your write-up, '
                             'and none of it is your problem, and you think '
                             'about it anyway.',
                             sets=('dog_kept',), credits=1800,
                             rep={'freeport': 20}),
                      Choice('sell', 'Sell it to somebody who wants a scheduler',
                             'Kagawa pay well for eleven months of tested '
                             'scheduling that nobody has to be credited for. '
                             'They take the safety clause out in the first '
                             'week, because the safety clause costs four per '
                             'cent.\n\nThe cranes at Freeport go back to the '
                             'office schedule. The driver does not speak to '
                             'you again, and does not make anything of it, '
                             'which is somehow the whole of it.',
                             sets=('dog_sold',), credits=6200,
                             rep={'kagawa': 12, 'freeport': -25}),
                      Choice('kill', 'Take it out before it decides something else',
                             'You end it, carefully, the way you would end '
                             'anything that has been running unsupervised for '
                             'eleven months near people.\n\nThe office '
                             'schedule comes back. Six weeks later there is a '
                             'lift that should not have been signed off, and '
                             'nobody is hurt, and the crane driver looks at '
                             'you across the yard and does not say the thing '
                             'she is obviously thinking.',
                             sets=('dog_killed',),
                             rep={'freeport': -8, 'kagawa': 6})),
                  ),
            Stage('after', 'The rota, either way',
                  'There is a line in the Freeport minutes about automated '
                  'scheduling and a decision taken on a date, and your handle '
                  'is not in it, and the decision is. That is how Freeport '
                  'writes things down and it is the closest thing to a '
                  'monument this city hands out.',
                  any_of=('dog_kept', 'dog_sold', 'dog_killed'),
                  sets=('dog_closed',), where='freeport', after=5),
        )),
    Thread(
        'somebody', 'What Came Out of Somebody',
        'The fence has a box of things that were in people, and a problem.',
        (
            Stage('box', 'A box with a schedule attached',
                  'The fence in the Shambles has a box under the counter that '
                  'he does not sell from, and he takes the lid off it for you '
                  'because you have stood in a doorway for money and that is '
                  'a reference of a kind.\n\n"Chrome out of people. Every '
                  'piece logged, every piece paid for, all of it clean." He '
                  'puts the lid back. "Somebody is running a construct that '
                  'reads clinic manifests and it has started matching serial '
                  'numbers to living people, and it will get to this box, and '
                  'then it will get to the people I bought from."',
                  requires=('met:fence', 'skill:warfare:3'),
                  any_of=('job:protect', 'job:hurt', 'job:recover',
                          'skill:violence:2'),
                  sets=('somebody_box',), where='shambles'),
            Stage('reader', 'The thing reading the manifests',
                  'It is not a person. It is a construct on a Kagawa '
                  'subnet that was built to find stolen chrome and has been '
                  'quietly improved by somebody into a thing that finds the '
                  'people wearing it.\n\n"Kill it and they build another one," '
                  'the fence says. "Do not kill it and it gets to a list of '
                  'four hundred names, and about eighty of those people are '
                  'in this district tonight."',
                  requires=('somebody_box',), where='shambles', after=2,
                  choices=(
                      Choice('sever', 'Take it apart in the net',
                             'You go in and you kill it properly, which takes '
                             'longer than killing it improperly and is the '
                             'difference between a fortnight and a year.\n\n'
                             'They build another one. It takes them eleven '
                             'months, and eleven months is eleven months, and '
                             'the fence says so in the flat way of a man who '
                             'has done this arithmetic before and got a '
                             'smaller number.',
                             sets=('somebody_severed',), credits=2600,
                             rep={'kagawa': -14, 'carrion': 12}),
                      Choice('poison', 'Leave it running, and wrong',
                             'You do not kill it. You teach it that four '
                             'hundred serial numbers belong to a scrap '
                             'consignment that went into the water in a year '
                             'nobody can check.\n\nIt keeps running. It keeps '
                             'reporting. Everything it says about those four '
                             'hundred people is confidently, permanently '
                             'wrong, and it will go on saying it long after '
                             'anybody who could correct it has stopped '
                             'caring.',
                             sets=('somebody_poisoned',), credits=3400,
                             rep={'kagawa': -6, 'carrion': 18}),
                      Choice('sell', 'Sell the box list instead',
                             'There is a buyer for four hundred names '
                             'attached to four hundred pieces of chrome, and '
                             'the buyer is not the Nightwatch and is not '
                             'Kagawa, and you do not ask past that.\n\nThe '
                             'fence closes the counter for nine days. When it '
                             'opens the box is gone and so is the schedule, '
                             'and he serves you, and does not look up.',
                             sets=('somebody_sold',), credits=7000,
                             rep={'carrion': -30, 'meridian': 10})),
                  ),
            Stage('after', 'The counter, nine days on',
                  'The box is not under the counter. The fence has a new one, '
                  'or the same one somewhere else, or neither, and he is '
                  'exactly as pleasant to you as he was before, which tells '
                  'you nothing and is meant to.',
                  any_of=('somebody_severed', 'somebody_poisoned',
                          'somebody_sold'),
                  sets=('somebody_closed',), where='shambles', after=4),
        )),

    Thread(
        'demonstration', 'The Demonstration',
        'Sendai would like somebody frightening to fail to hurt a volunteer.',
        (
            Stage('card', 'They have read about you, from a card',
                  'The demonstrator in the Glasshouse market is reading from '
                  'a card about impact-rated dermal work, to nobody, for the '
                  'fourth time this hour. Then she stops, checks a different '
                  'card, and reads a short description of a person who has '
                  'recently been in a fight and won it.\n\n'
                  'The description is of you. She looks up. "Oh," she says. '
                  '"You are the one they want."',
                  requires=('met:demonstrator',),
                  any_of=('fought:sixes', 'fought:carrion', 'fought:kagawa',
                          'fought:nightwatch', 'mark:blooded',
                          'trait:known', 'trait:showoff'),
                  sets=('demo_card',), where='glasshouse'),
            Stage('stage', 'A live demonstration, with a volunteer',
                  'Sendai Precision would like to demonstrate subdermal '
                  'plating to an audience of buyers, and a demonstration '
                  'needs somebody hitting somebody. They have a volunteer in '
                  'the plating. They would like you to be the other half.\n\n'
                  '"It is rated," the demonstrator says, reading. "It is '
                  'genuinely rated, I have seen the tests, I am not being '
                  'careful with you." Then, not from the card: "They want it '
                  'to look like it nearly did not hold."',
                  requires=('demo_card',), where='glasshouse', after=2,
                  choices=(
                      Choice('honest', 'Hit the plating properly',
                             'You hit it the way you would hit anything, and '
                             'it holds, because it is rated and the tests '
                             'were real. The volunteer is fine and slightly '
                             'disappointed, and the buyers are unmoved, '
                             'because nothing that works is interesting to '
                             'watch.\n\nSendai pay the agreed fee exactly and '
                             'do not book you again. The demonstrator finds '
                             'you afterwards to say the tests were real, '
                             'twice, as though somebody needed telling.',
                             sets=('demo_honest',), credits=2200,
                             rep={'sendai': 10}),
                      Choice('show', 'Make it look like it nearly did not hold',
                             'You sell it. The volunteer goes down and stays '
                             'down a beat too long and comes up grinning, and '
                             'the room makes the noise the room was booked to '
                             'make, and four buyers ask about volume.\n\n'
                             'It is the easiest money you have ever taken and '
                             'the plating is still rated and nothing you did '
                             'was a lie, exactly, and you notice yourself '
                             'assembling that sentence on the way out.',
                             sets=('demo_showed',), credits=4600,
                             rep={'sendai': 20, 'static': -8}),
                      Choice('tell', 'Tell the room what was asked for',
                             'You say it into the room before the first '
                             'swing: that the plating is rated, that the '
                             'tests are real, and that you have been asked to '
                             'make it look close.\n\nThe demonstrator does not '
                             'contradict you, which is the bravest thing '
                             'anybody does that afternoon. Sendai sell four '
                             'units on the strength of it and never speak to '
                             'either of you again.',
                             sets=('demo_told',), credits=800,
                             rep={'sendai': -12, 'static': 15})),
                  ),
            Stage('after', 'The card, revised',
                  'The demonstrator is reading from a new card. It is about '
                  'the same plating and it is a paragraph shorter, and the '
                  'part that has gone is the part about what it is like to '
                  'be hit.\n\nShe gets to the end, looks up, sees you, and '
                  'does the smallest possible thing with her face.',
                  any_of=('demo_honest', 'demo_showed', 'demo_told'),
                  sets=('demo_closed',), where='glasshouse', after=4),
        )),

    # -- what the city is, afterwards (D143) --------------------------------
    Thread(
        'afterwards', 'Afterwards',
        'The thing about the water is finished. The city is not.',
        (
            Stage('employed', 'On the inside of it',
                  'You work for it now, in whatever sense that word survives '
                  'this. The money is real and arrives, and the work is a '
                  'kind you can do, and nobody has asked you to do anything '
                  'you would describe as wrong, yet, out loud.\n\n'
                  'What is strange is the city afterwards. It is exactly the '
                  'same size and you can see all of it, and none of it is '
                  'about the water any more, and there turns out to be a '
                  'great deal of it.',
                  requires=('runs:5', 'dw_employed'),
                  sets=('after_settled',), after=3),
            Stage('published', 'Nine logs, in print',
                  'The Stacks ran it. Nine logs, in order, with the dates, '
                  'and the part that got people was not the water, it was '
                  'the ordinariness of the memos.\n\nFor eleven days it is '
                  'the only thing anybody says to you. On the twelfth '
                  'somebody in a queue asks whether you did the thing with '
                  'the printers, which was somebody else, and you say no, '
                  'and the conversation moves on, and the city closes over '
                  'it the way it closes over everything.',
                  requires=('runs:5', 'dw_published'),
                  sets=('after_settled',), after=3),
            Stage('walked', 'You let it alone',
                  'You know what it is and you did not take the money and '
                  'you did not put it in print, and both of those were '
                  'decisions and neither of them was nothing.\n\nThe noodle '
                  'bar has four landlines. One of them has never rung in '
                  'anybody\'s hearing. You go past it about as often as you '
                  'used to and you notice it every single time, and the rest '
                  'of the district goes on being a district.',
                  requires=('runs:5',),
                  any_of=('dw_refused', 'dw_stayed'),
                  sets=('after_settled',), after=3),
            Stage('rest', 'The rest of it',
                  'Somebody asks what you are working on and you find you do '
                  'not have an answer, and that the not having one is not '
                  'the same as having nothing to do.\n\n'
                  'There are seventy-two quarters in this city and you have '
                  'stood in some of them. There are people in it who have '
                  'never asked you for anything and would answer if you '
                  'asked. There is a wall in the Shambles with names on it, '
                  'a queue outside the exchange that is not a queue, a thing '
                  'running on the Freeport cranes that nobody has explained, '
                  'and a box under a counter that somebody is worried '
                  'about.\n\nNone of it is the main thing. There is no main '
                  'thing any more. That was the reward.',
                  requires=('after_settled', 'not:pit:deacon'),
                  sets=('after_rest',), after=4),
            # The same close for somebody whose name is on that wall
            # (D144): a rung-four fighter was told about "a wall in the
            # Shambles with names on it" as if they had never seen it.
            Stage('rest_wall', 'The rest of it',
                  'Somebody asks what you are working on and you find you do '
                  'not have an answer, and that the not having one is not '
                  'the same as having nothing to do.\n\n'
                  'There are seventy-two quarters in this city and you have '
                  'stood in some of them. There are people in it who have '
                  'never asked you for anything and would answer if you '
                  'asked. There is a wall in the Shambles with your name on '
                  'it above other people\'s, and the people whose names are '
                  'under yours have not stopped coming in; there is a queue '
                  'outside the exchange that is not a queue, a thing running '
                  'on the Freeport cranes that nobody has explained, and a '
                  'box under a counter that somebody is worried about.\n\n'
                  'None of it is the main thing. There is no main thing any '
                  'more. That was the reward.',
                  requires=('after_settled', 'pit:deacon'),
                  sets=('after_rest',), after=4),
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
                             debt=-9000,
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
