"""The coach (D183): a tutorial that reads where you are standing.

The first tutorial (D27, D60) was a list of twenty-five instructions, each
with a condition, and it watched rather than led: it printed a step and
waited for the world to satisfy it. The testers found the flaw the day the
game went public. A step the player walked past, `deck` before `jack in`,
held the whole list at that step, so the tutorial sat on "type `deck`"
through the entire run while `job` said "probe coldstore", and none of the
run's teaching ever printed. A list cannot follow somebody who does not
walk in a line.

So: lessons, not steps. Each lesson says when it applies (where the player
is standing, what they hold) and when it is done, and the coach is always
the first lesson in this order that applies and is not done. Inside a
network the lesson is the brief itself: the instruction is the next thing
`job` would say, word for word and host for host, and the reason is written
once per verb. One source of truth, so the tutorial, `now`, `job` and Enter
can never disagree.

Three rules from the first tutorial survive. Nothing is forced: `tutorial
stop` is one word. Conditions are total: `validate.py` calls every one
against an empty session. And every lesson has a reason, because the
instruction is the part the player could have guessed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable


# --------------------------------------------------------------------------
# reading the session, safely
# --------------------------------------------------------------------------

def _game(sess):
    game = getattr(sess, 'game', None)
    return None if game is None or getattr(game, 'over', '') else game


def _char(sess):
    game = _game(sess)
    return game.char if game is not None else None


def _run(sess):
    return getattr(sess, 'run', None)


def _seen(sess) -> set:
    return getattr(sess, 'seen', None) or set()


def _city(sess) -> bool:
    return _game(sess) is not None and _run(sess) is None


def _contract(sess):
    game = _game(sess)
    return game.city.current if game is not None else None


def _city_steps(sess) -> list[tuple[str, str]]:
    """The city's own advice, as (command, why). Empty when nothing applies
    or anything goes wrong: the coach never takes the shell down."""
    game = _game(sess)
    if game is None:
        return []
    try:
        from ..commands.city import city_steps
        return list(city_steps(game))
    except Exception:
        return []


def _first_step(sess, verbs: tuple[str, ...]) -> str:
    for cmd, _ in _city_steps(sess):
        if cmd.split()[0] in verbs:
            return cmd
    return ''


#: A city step that must come before the job: shopping, street work, the
#: deck. When the city's advice leads with one of these, the coach says it
#: too, or a newcomer walks into a run without the program the job needs.
KIT_VERBS = ('buy', 'errands', 'borrow', 'drop', 'load', 'market', 'sell',
             'repair', 'unload', 'train', 'boost', 'spend', 'install',
             'clinic', 'rest')
GO_VERBS = ('travel', 'walk')


# --------------------------------------------------------------------------
# lessons
# --------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Lesson:
    key: str
    #: Whether this lesson is about where the player is standing right now.
    when: Callable
    #: True once the player has done it. Cached the first time it is true.
    done: Callable
    #: What to do, in one imperative sentence naming the command in
    #: backticks. A string, or a function of the session for a lesson that
    #: names a real job, district or host.
    instruction: str | Callable
    #: Why, which is the part that actually teaches.
    why: str
    #: Printed when the lesson completes. The payoff.
    payoff: str = ''
    #: A manual topic worth reading at this point.
    topic: str = ''
    #: Whether being done once is being done for good. The kit lesson is
    #: not: it applies whenever the city's advice leads with shopping,
    #: which can be before the first job and again before the second.
    sticky: bool = True


def instruction_of(lesson: Lesson, sess) -> str:
    text = lesson.instruction
    if callable(text):
        try:
            return text(sess) or ''
        except Exception:
            return ''
    return text


def command_of(instruction: str) -> str:
    """The thing to type, out of an instruction: the first backticked word
    or phrase, or `Enter` for the one lesson that is a key rather than a
    verb."""
    m = re.search(r'`([^`]+)`', instruction or '')
    if m:
        return m.group(1)
    return 'Enter' if 'Enter' in (instruction or '') else ''


LOOP = (
    'The whole game is one loop. Take a job from the `board`. Travel to the '
    'district it is in. `jack in` to their network. Inside, find the host '
    'the job is on, open it, do the thing, and `jack out` before the trace '
    'fills. Then the city reacts: what you left behind becomes heat, the '
    'board changes, people notice. Everything else is detail on that loop. '
    'Enter on an empty line always says the next step, out here and inside '
    'a run, and `now` is the same thing typed.'
)


def _take_instruction(sess) -> str:
    """A real job, always: the one the city recommends, else the softest
    on the board, else a shift for the board to refresh. A coach that says
    "pick something" to somebody who does not know how is not coaching."""
    step = _first_step(sess, ('take',))
    if step:
        return f'Type `{step}`.'
    game = _game(sess)
    board = list(getattr(game.city, 'board', ()) or ()) if game else []
    if board:
        soft = min(board, key=lambda c: getattr(c, 'posture', 0))
        return f'Type `take {soft.cid}`.'
    return 'Type `rest 1`. The board refreshes while you sleep.'


def _kit_instruction(sess) -> str:
    step = _first_step(sess, KIT_VERBS)
    return f'Type `{step}`.' if step else 'Type `deck`.'


def _go_instruction(sess) -> str:
    step = _first_step(sess, GO_VERBS)
    if step:
        return f'Type `{step}`.'
    contract = _contract(sess)
    if contract is not None:
        return f'Type `travel {contract.district}`, or `walk {contract.district}`.'
    return 'Type `map`, then `travel <district>` toward the job.'


def _unspent(sess) -> bool:
    char = _char(sess)
    return char is not None and (char.points > 0 or char.xp > 0)


def _in_job_district(sess) -> bool:
    game, contract = _game(sess), _contract(sess)
    return (game is not None and contract is not None
            and game.city.where == contract.district)


def _kit_wanted(sess) -> bool:
    steps = _city_steps(sess)
    return bool(steps) and steps[0][0].split()[0] in KIT_VERBS


def _runs(sess) -> int:
    char = _char(sess)
    return int(getattr(char, 'runs', 0) or 0) if char is not None else 0


LESSONS: tuple[Lesson, ...] = (
    Lesson(
        'make',
        when=lambda s: _game(s) is None,
        done=lambda s: _game(s) is not None,
        instruction='Type `new`. It asks which origin, what to call them, '
                    'and whether to spend the opening points the usual way.',
        why='An origin sets where you start and never where you can go. If '
            'you have no preference, `gutter` is the straightforward one: '
            'fast, cheap, and loud. Whenever you do not know what to type, '
            'Enter on an empty line says what to do next.',
        payoff='That is a character. Everything from here is theirs.',
        topic='origins'),
    Lesson(
        'loop',
        when=_city,
        done=lambda s: 'now' in _seen(s),
        instruction='Press Enter on an empty line.',
        why=LOOP,
        payoff='That is the button. Whenever you do not know what to type, '
               'that.',
        topic='basics'),
    Lesson(
        'sheet',
        when=_city,
        done=lambda s: _char(s) is not None and 'char' in _seen(s),
        instruction='Type `char` to read the build.',
        why='Read it top to bottom, because every screen in the game is '
            'built the same way. The first line is the title, with the '
            'context on the right. Under the rule, a grid: names on the '
            'left, values to the right of the bar. Then the five attributes, '
            'a bar each, with what each one is for beside the number, and '
            'under them the numbers worked out from those: Bandwidth, Focus, '
            'Tempo, Composure, Cover, and Integrity near the top. The prompt '
            'at the bottom says where you are, the time, and your money; in '
            'a run it says which node, the tick, and the trace.',
        payoff='Those numbers are what every check in the game is built on.',
        topic='attributes'),
    Lesson(
        'colours',
        when=_city,
        done=lambda s: 'legend' in _seen(s),
        instruction='Type `legend`.',
        why='Every colour here is a meaning, and one meaning is one colour '
            'everywhere: the trace is always the trace colour, money is '
            'always the money colour, and a word that changes colour in the '
            'middle of a sentence is the sentence telling you which number '
            'it means. `legend` prints the key in the colours themselves, '
            'and it is free.',
        payoff='Whenever a colour means nothing to you, that.',
        topic='colours'),
    Lesson(
        'spend',
        when=lambda s: _city(s) and _unspent(s),
        done=lambda s: _char(s) is not None and not _unspent(s),
        instruction='Type `spend`, or `boost <attribute>` and `train <skill>` '
                    'to place them yourself.',
        why='You start with attribute points and experience unspent, and '
            'every check in the game reads them. Ranks 2 and 4 of any skill '
            'unlock a technique, which is a new verb rather than a bigger '
            'number, so `train intrusion` twice is a real change to what '
            'you can type. `spend` puts the lot where your origin usually '
            'would, if you would rather play than plan.',
        payoff='Progression here is about buying new things to type.',
        topic='skills'),
    Lesson(
        'board',
        when=lambda s: _city(s) and _contract(s) is None,
        done=lambda s: 'board' in _seen(s),
        instruction='Type `board` to see what work is on offer, and '
                    '`board <id>` to read one properly.',
        why='The board is generated from the state of the city: who dislikes '
            'whom enough to pay for it. It also expires, and other runners '
            'are taking these while you read. The [accent]reads[/] column is doors '
            'and room: whether your breaker opens what the job is behind, '
            'and how hard the place runs the clock while you work.',
        payoff='Note the target and the posture. Posture is how hard their '
               'network will be.',
        topic='contracts'),
    Lesson(
        'kit',
        # Before the first job, or with a job in hand: the city's shopping
        # advice comes first. Between jobs after the first run the coach
        # teaches the city, and the shopping can wait.
        when=lambda s: _city(s) and _kit_wanted(s)
        and (_contract(s) is not None or _runs(s) == 0),
        done=lambda s: _city(s) and not _kit_wanted(s),
        instruction=_kit_instruction,
        why='The city\'s advice leads with this, and the coach follows it: '
            'the work needs something you are not carrying, or the money '
            'for it, and this is where it comes from. A run needs a breaker '
            'to open things and, for most jobs, a payload to carry the '
            'thing out or do the damage, and the loadout is fixed the '
            'moment you jack in. Enter on an empty line says the same, with '
            'the price.',
        topic='deck',
        sticky=False),
    Lesson(
        'take',
        when=lambda s: _city(s) and _contract(s) is None,
        done=lambda s: _contract(s) is not None,
        instruction=_take_instruction,
        why='That one is the softest job on the board that the deck you '
            'are carrying can actually finish, which is the same thing '
            'Enter would tell you. A first run wants a small job against a '
            'low posture; the pay is smaller and so is the room.',
        payoff='That is your job. It stays yours until you finish or dropes it.'.replace('dropes', 'drop'),
        topic='contracts'),
    Lesson(
        'deck',
        when=lambda s: _city(s) and _contract(s) is not None,
        done=lambda s: 'deck' in _seen(s),
        instruction='Type `deck` to see what you are carrying.',
        why='Memory is the constraint that decides your playstyle, and the '
            'loadout is fixed the moment you jack in. A run needs a breaker '
            'to open things and a payload to carry anything out; `load` and '
            '`unload` change it, but only out here.',
        payoff='That is what you take in with you.',
        topic='deck'),
    Lesson(
        'go',
        when=lambda s: _city(s) and _contract(s) is not None
        and not _in_job_district(s),
        done=lambda s: _in_job_district(s) or _run(s) is not None,
        instruction=_go_instruction,
        why='The job is in another district. `travel` goes one district a '
            'shift; `walk` goes the whole way, a shift a step, and stops if '
            'the street stops you. Shifts are the city\'s real currency: '
            'while they pass, contracts expire and other people work. `map` '
            'draws the city and says how far everything is.',
        payoff='You are standing where the job is.',
        topic='city'),
    Lesson(
        'jackin',
        when=lambda s: _city(s) and _contract(s) is not None
        and _in_job_district(s),
        done=lambda s: _run(s) is not None or _runs(s) > 0,
        instruction='Type `jack in`.',
        why='This is the door. Past it the loadout is fixed, every command '
            'costs time, and the trace starts. You can `jack out` at any '
            'moment, so there is nothing to lose by going in and looking.',
        payoff='You are inside somebody else\'s network now.',
        topic='firstrun'),
    Lesson(
        'run',
        when=lambda s: _run(s) is not None,
        done=lambda s: _run(s) is None and _runs(s) > 0,
        instruction='Type `job`, then do what it says, one move at a time.',
        why='Inside, the coach is the brief: the next move, word for word, '
            'and why.',
        payoff='Out. Look at the residue line in that summary: it is the '
               'only number that follows you home.',
        topic='firstrun'),
    Lesson(
        'settle',
        when=lambda s: _city(s) and _runs(s) > 0
        and bool(getattr(_game(s).city, 'pending', None)),
        done=lambda s: _city(s) and _runs(s) > 0
        and not getattr(_game(s).city, 'pending', None),
        instruction='Spend a shift: `rest 1`. The residue you left is about '
                    'to become somebody\'s attention.',
        why='Residue does not follow you out of the network as heat. It '
            'follows you out as evidence, and a shift later somebody has '
            'read it, and then it is heat. That gap is the only reason '
            'getting out quietly ever feels like getting away with it.',
        payoff='It has landed. Whatever you left behind is a number on a '
               'faction\'s side of the ledger now.',
        topic='heat'),
    Lesson(
        'rep',
        when=lambda s: _city(s) and _runs(s) > 0,
        done=lambda s: 'rep' in _seen(s),
        instruction='Type `rep` to see how the city feels about you.',
        why='Standing is what people will pay you; attention is how hard '
            'they are looking for you. They are different numbers and they '
            'move for different reasons, and past a threshold attention '
            'becomes a bounty, which is a faction paying for your name.',
        payoff='Every number on that screen came from something you did, or '
               'something you were seen doing.',
        topic='heat'),
    Lesson(
        'look',
        when=lambda s: _city(s) and _runs(s) > 0,
        done=lambda s: 'look' in _seen(s),
        instruction='Type `look` to see where you are standing, who is '
                    'about, and the places you can go and stand.',
        why='A district is more than its market. There are people here who '
            'hand out work, keep private stock, do favours on a tab, and '
            'have opinions about what you are doing, and they keep hours. '
            '`look` says who is here now and who keeps other hours.',
        payoff='That is the city in one screen: the hour, the street, the '
               'people, the places.',
        topic='city'),
    Lesson(
        'talk',
        when=lambda s: _city(s) and _runs(s) > 0,
        done=lambda s: 'talk' in _seen(s),
        instruction='Type `talk <name>` to somebody here, and `who is '
                    '<name>` for what you know about them.',
        why='Talking is how threads start. Meeting somebody sets a flag, and '
            'scenes arrive when their conditions hold, in whatever order '
            'the world produced them. Nobody here is a shop with a face on '
            'it.',
        payoff='They have an opinion about you now. So will the story.',
        topic='people'),
    Lesson(
        'visit',
        when=lambda s: _city(s) and _runs(s) > 0,
        done=lambda s: 'visit' in _seen(s),
        instruction='Type `visit <place>` to go and stand somewhere in the '
                    'district. It costs nothing.',
        why='The places are texture, and texture is most of what makes a '
            'city feel like it goes on when you are not looking. Some of the '
            'people are easier to find at their place than in the street.',
        payoff='Every place in a scene is a place you can go and stand in '
               'afterwards.',
        topic='city'),
    Lesson(
        'journal',
        when=lambda s: _city(s) and _runs(s) > 0,
        done=lambda s: 'journal' in _seen(s),
        instruction='Type `journal` to see what you have got yourself into.',
        why='Threads, not quest chains: several are running at once, none '
            'of them waits for you, and advancing one changes the shape of '
            'another. The journal is where they are, and `choose` is how '
            'you answer one that is waiting on you.',
        payoff='Every decision in there is read by the world, and every one '
               'has a line in the ending.',
        topic='threads'),
    Lesson(
        'face',
        when=lambda s: _city(s) and _runs(s) > 0,
        done=lambda s: 'self' in _seen(s),
        instruction='Type `self` to see what this person looks like, and '
                    '`self --roll` or `self --set dress <key>` to change it.',
        why='This is a build decision rather than a portrait. How memorable '
            'you are earns you more standing per job and turns more of what '
            'you leave behind into somebody hunting you, so both ends of it '
            'are real builds. Four of the eight are yours to change '
            'whenever you like; the rest need a clinic and a lot of money.',
        payoff='Chrome puts a floor under how memorable you are, so a '
               'heavily wired runner has spent their anonymity whether they '
               'wanted to or not.',
        topic='appearance'),
    Lesson(
        'door',
        when=lambda s: _city(s) and _runs(s) > 0,
        done=lambda s: 'retire' in _seen(s),
        instruction='Type `retire` to see how far off the door is.',
        why='There is a way out you choose, and it wants four things: '
            'nothing owed, nothing in you that you need, nobody paying for '
            'your name, and enough put away. None of them is hard alone. '
            'All four at once is the campaign.',
        payoff='The door has been there since the first shift. Every system '
               'in this city is quietly making it further away.',
        topic='death'),
    Lesson(
        'again',
        when=lambda s: _city(s) and _runs(s) > 0 and _contract(s) is None,
        done=lambda s: _runs(s) > 0 and _contract(s) is not None,
        instruction=_take_instruction,
        why='That is the loop. The second run is the one where the city '
            'remembers the first: the faction you hit is harder, the people '
            'who noticed you are looking, and the other runners have taken '
            'the work you did not.',
        payoff='Good. Everything from here is yours.',
        topic='firstrun'),
)

LESSON_KEYS: tuple[str, ...] = tuple(l.key for l in LESSONS)
BY_KEY: dict[str, Lesson] = {l.key: l for l in LESSONS}
#: The lesson that ends the tutorial when it completes.
LAST = 'again'


# --------------------------------------------------------------------------
# inside a network: the brief, coached
# --------------------------------------------------------------------------

#: Printed once, the first time the coach speaks inside a network.
INSIDE = (
    'You are inside their network, standing on the gateway. A network is '
    'hosts joined by links, in zones from the perimeter in to the core, '
    'and every zone deeper wants a higher access tier. The job is on one '
    'host: find it, open a service on it, stand on it, do the thing, '
    'leave.\n\n'
    'Three numbers matter. The trace is the clock: it only rises, and at '
    '100 they cut you loose. Noise is suspicion where you are standing, and '
    'it fades. Residue is what you leave behind, and it follows you home. '
    'Every command in here costs ticks, and ticks feed the trace.\n\n'
    '`job` is the whole brief. Enter is the next move, every time, and the '
    'coach says why. `jack out` leaves at any moment, and leaving early is '
    'a skill. `tutorial stop` ends the coach whenever you like.'
)

#: Why the brief says what it says, by verb. Printed the first time the
#: coach hands the player each verb, and never again.
RUN_WHY: dict[str, str] = {
    'scan': 'You can only act on hosts you have found. `scan` shows what '
            'the host you are standing on connects to, with the zone and '
            'the access tier each one wants. It is the first noise you make.',
    'probe': 'A scan says a host exists. `probe` says what it runs, what is '
             'guarding it, and whether there is anything on it worth taking. '
             'You need that before you can open anything on it.',
    'crack': 'One open service is enough to stand on a host. `crack` breaks '
             'one open, and it is the loudest ordinary thing you do: noise '
             'wakes the countermeasures on that node. `odds crack <host> '
             '<service>` prints the whole sum first, if you want to see it.',
    'connect': 'A host with an open service will take you. `connect` moves '
               'you onto it; where you stand decides what you can reach and '
               'what can reach you. Deeper zones want a higher access tier, '
               'and cracking an auth server is how you get one.',
    'pivot': '`pivot` is `connect` through a host you already hold: the '
             'route runs through it rather than straight from the gateway.',
    'wait': 'The room is loud. `wait` is the quiet move: noise cools, the '
            'alert falls back, and the trace still moves, which is the '
            'price of it. When the brief says wait, wait.',
    'observe': 'This job is watching, not taking. Sit on the host and '
               '`observe` until the clean ticks are banked. A tick banks '
               'while the alert is below red, and red empties every one you '
               'had, so the job is keeping the room calm while you do it.',
    'pull': '`pull` takes the thing you came for off this host and into '
            'the deck. It is loud, and once it is in the deck the only move '
            'left is to leave with it: nothing counts until you are out.',
    'push': '`push` plants the payload where you are standing. It is the '
            'objective verb for this job, and it is loud.',
    'wipe': '`wipe` destroys the thing where it sits. Loud, fast, and it '
            'does not need carrying out.',
    'jack out': 'You have what you came for, or the trace is close, or the '
                'brief has nothing better. `jack out` leaves. Nothing you '
                'are carrying counts until you are out, and there is no '
                'prize for the last thing you grabbed if the trace lands on '
                'you holding it.',
    'signal': 'Somebody is in here with you and they are not yours to '
              'command. `signal` is advice: hold, move, out.',
    'mask': 'A mask suppresses trace and noise for a while. The brief '
            'wants it up before the loud part.',
    'strike': 'Something awake is on this node and it will act before you '
              'can. `strike` hits it with the weapon you carry; `odds '
              'strike` prints the sum.',
    '*': 'The brief says this is the move. `job` says why, in the words of '
         'this room.',
}


def run_lesson(sess) -> tuple[str, str, str] | None:
    """Inside a network: (key, instruction, why) from the brief, or None.

    The key carries the verb, so the caller can tell a new verb from the
    same one again. Never raises: a brief that cannot be built is a
    `scan`.
    """
    run = _run(sess)
    if run is None:
        return None
    try:
        brief = run.brief()
        step = brief.steps[0] if brief.steps else ''
        done = bool(brief.done)
    except Exception:
        step, done = '', False
    if done and step != 'jack out':
        step = 'jack out'
    if not step or '<' in step:
        step = 'scan'
    verb = 'jack out' if step.startswith('jack') else step.split()[0]
    why = RUN_WHY.get(verb, RUN_WHY['*'])
    return (f'run:{verb}', f'Type `{step}`.', why)


def current(sess) -> tuple[str, str, str, str, int] | None:
    """The lesson that applies right now: (key, instruction, why, topic,
    number), or None when nothing does.

    Inside a network the lesson is the brief, unless the player skipped the
    coaching for this run. Outside, the first lesson in order that applies
    and is not done.
    """
    done = getattr(sess, 'tutorial_done', None) or set()
    if _run(sess) is not None:
        if 'run:skip' in done:
            return None
        got = run_lesson(sess)
        if got is None:
            return None
        key, instruction, why = got
        return (key, instruction, why, 'firstrun', LESSON_KEYS.index('run') + 1)
    for i, lesson in enumerate(LESSONS):
        if lesson.key == 'run' or lesson.key in done:
            continue
        try:
            applies = bool(lesson.when(sess))
            if applies and not lesson.sticky:
                applies = not bool(lesson.done(sess))
        except Exception:
            applies = False
        if not applies:
            continue
        return (lesson.key, instruction_of(lesson, sess), lesson.why,
                lesson.topic, i + 1)
    return None


OPENING = (
    'The coach is on. It reads where you are standing and says the one '
    'next thing to type, and why; Enter on an empty line repeats it. '
    'Nothing is forced: do things in any order, ignore it, `tutorial skip` '
    'a lesson, or `tutorial stop`.'
)

CLOSING = (
    'That is the loop, and you have now done all of it once, and seen what '
    'the city does with it.\n\n'
    'What the coach did not cover, and what to read when you want it:\n'
    '  [fg]legend[/]          the colours, again\n'
    '  [fg]help triangle[/]   the three numbers, properly\n'
    '  [fg]help heat[/]       what the residue you left is about to become\n'
    '  [fg]help skills[/]     where your experience should go\n'
    '  [fg]help rivals[/]     the other people doing this job\n'
    '  [fg]help money[/]      what things cost and what a run is worth\n'
    '  [fg]map[/]             the city, drawn, and `walk` to anywhere on it\n'
    '  [fg]help street[/]     the half of the danger with the deck in the bag, and the fights\n'
    '  [fg]news[/]            what the city did while you were not looking\n\n'
    'The residue from that run becomes heat in a shift or so. Everything '
    'else in this city follows from that one fact.'
)

#: Commands whose mere use satisfies a lesson. Tracked because "did they
#: look at it" is a legitimate teaching goal and is not otherwise visible
#: in state.
WATCHED = ('char', 'board', 'deck', 'odds', 'status', 'rep', 'look',
           'talk', 'visit', 'journal', 'now', 'retire', 'errands', 'legend',
           'self')
