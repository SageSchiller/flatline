"""The optional tutorial: a thing that watches you play.

The wrong way to teach a game like this is a wall of text before the player
has touched anything. The right way is one instruction at a time, checked
against what actually happened, so the player is always doing the thing they
were just told about and never reading ahead.

So a step is an instruction plus a **condition**, and the session checks the
condition after every command. When it holds, the step is done, the payoff
prints, and the next instruction appears. Nothing is forced: the player can
ignore the tutorial entirely, do the steps out of order, or `tutorial stop`.

Conditions are functions of the session, which is why this content module is
allowed to hold callables. They must be **total and cheap**: they run after
every single command, including in the middle of a run, and one that raises
would take the shell down with it. `validate.py` calls every one of them
against an empty session to prove they cope with nothing existing yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


def _has_game(sess) -> bool:
    return getattr(sess, 'game', None) is not None


def _char(sess):
    game = getattr(sess, 'game', None)
    return getattr(game, 'char', None) if game else None


def _run(sess):
    return getattr(sess, 'run', None)


@dataclass(frozen=True, slots=True)
class Step:
    key: str
    #: What to do, in one imperative sentence.
    instruction: str
    #: Why, which is the part that actually teaches.
    why: str
    #: True once the player has done it.
    done: Callable
    #: Printed when the step completes. The payoff.
    payoff: str = ''
    #: A manual topic worth reading at this point.
    topic: str = ''


STEPS: tuple[Step, ...] = (
    Step(
        'make',
        'Type `new`. It asks which of the ten origins, what to call them, '
        'and whether to spend the opening points the usual way.',
        'An origin sets where you start and never where you can go. If you '
        'have no preference, `gutter` is the straightforward one: fast, '
        'cheap, and loud. Whenever you do not know what to type, Enter on '
        'an empty line says what to do next.',
        done=lambda s: _has_game(s),
        payoff='That is a character. Everything from here is theirs.',
        topic='attributes'),
    Step(
        'sheet',
        'Type `char` to read the build.',
        'Read it top to bottom, because every screen in the game is built '
        'the same way. The first line is the title, with the context on the '
        'right. Under the rule, a grid: names on the left, values to the '
        'right of the bar. Then the five attributes, a bar each, with what '
        'each one is for beside the number, and under them the numbers '
        'worked out from those: Bandwidth, Focus, Tempo, Composure, Cover, '
        'and Integrity near the top. The prompt at the bottom says where '
        'you are, the time, and your money; in a run it says which node, '
        'the tick, and the trace.',
        done=lambda s: bool(_char(s)) and 'char' in getattr(s, 'seen', set()),
        payoff='Those numbers are what every check in the game is built on.',
        topic='attributes'),
    Step(
        'colours',
        'Type `legend`.',
        'Every colour here is a meaning, and one meaning is one colour '
        'everywhere: the trace is always the trace colour, money is always '
        'the money colour, and a word that changes colour in the middle of '
        'a sentence is the sentence telling you which number it means. '
        '`legend` prints the key in the colours themselves, and it is free.',
        done=lambda s: 'legend' in getattr(s, 'seen', set()),
        payoff='Whenever a colour means nothing to you, that.',
        topic='colours'),
    Step(
        'spend',
        'Spend a point with `boost <attribute>`, and an experience with '
        '`train <skill>`.',
        'You start with six attribute points and twelve experience. Ranks 2 '
        'and 4 of any skill unlock a technique, which is a new verb rather '
        'than a bigger number, so `train intrusion` twice is a real change to '
        'what you can type. `spend` puts the lot where your origin usually '
        'would, if you would rather play than plan.',
        done=lambda s: bool(_char(s)) and (
            _char(s).points < 6 or _char(s).xp < 12),
        payoff='Progression here is about buying new things to type.',
        topic='skills'),
    Step(
        'face',
        'Type `self` to see what this person looks like, and `self --roll` '
        'or `self --set dress <key>` to change it.',
        'This is a build decision rather than a portrait. How memorable you '
        'are earns you more standing per job and turns more of what you leave '
        'behind into somebody hunting you, so both ends of it are real '
        'builds. Four of the eight are yours to change whenever you like; the '
        'rest need a clinic and a lot of money.',
        done=lambda s: 'self' in getattr(s, 'seen', set()),
        payoff='Chrome puts a floor under how memorable you are, so a heavily '
               'wired runner has spent their anonymity whether they wanted to '
               'or not.',
        topic='appearance'),
    Step(
        'board',
        'Type `board` to see what work is on offer, and `board <id>` to read '
        'one properly.',
        'The board is generated from the state of the city: who dislikes whom '
        'enough to pay for it. It also expires, and other runners are taking '
        'these while you read.',
        done=lambda s: 'board' in getattr(s, 'seen', set()),
        payoff='Note the target and the posture. Posture is how hard their '
               'network will be.',
        topic='contracts'),
    Step(
        'take',
        'Accept one with `take <id>`.',
        'Pick something against a low-posture target for a first run: the '
        'Sixes or Static are the softest in the city.',
        done=lambda s: _has_game(s) and bool(s.game.city.accepted),
        payoff='That is your job. It stays yours until you finish or drop it.',
        topic='contracts'),
    Step(
        'deck',
        'Type `deck` to see what you are carrying.',
        'Memory is the constraint that decides your playstyle, and the '
        'loadout is fixed the moment you jack in. A run needs a breaker to '
        'open things and a payload to carry anything out.',
        done=lambda s: 'deck' in getattr(s, 'seen', set()),
        payoff='`load` and `unload` change it, but only out here.',
        topic='deck'),
    Step(
        'travel',
        'Type `map` to see the city, then `travel <district>` toward the job. '
        'Then `jack in`.',
        'Travel only goes to a neighbouring district, so the far side of the '
        'city is two or three shifts away, and shifts are the city\'s real '
        'currency: while they pass, contracts expire and other people work. '
        'The map says how far everything is and hands you the walk as a line '
        'you can type.',
        done=lambda s: _run(s) is not None,
        payoff='You are inside somebody else\'s network now.',
        topic='city'),
    Step(
        'brief',
        'Type `job`.',
        'The one screen that answers "what am I doing here". It names what '
        'finishing looks like for this contract, where the thing is or what '
        'to look for if you have not found it, how far along you are, and the '
        'next command to type. It costs no time, it is always safe to ask, '
        'and it is the answer whenever you lose the thread.',
        done=lambda s: 'job' in getattr(s, 'seen', set()),
        payoff='Every run is the same five beats: find it, reach it, open it, '
               'do the thing, leave. That screen tells you which one you are '
               'on.',
        topic='firstrun'),
    Step(
        'scan',
        'Type `scan`.',
        'This shows what the node you are standing in connects to. It is '
        'also the first noise you make, and noise is the first of the three '
        'numbers that matter.',
        done=lambda s: _run(s) is not None and _run(s).tick > 0,
        payoff='Every command that does work costs time, and time feeds the '
               'trace.',
        topic='triangle'),
    Step(
        'probe',
        'Type `probe <host>` on something the scan found.',
        'A scan tells you a host exists. A probe tells you what it runs, what '
        'is guarding it, and whether there is anything on it worth taking. '
        'Probing is also the only counter to traps.',
        done=lambda s: _run(s) is not None and any(
            n.mapped for n in _run(s).net.nodes.values()
            if n.uid != _run(s).net.entry),
        payoff='Now you know what you are looking at.',
        topic='ice'),
    Step(
        'odds',
        'Type `odds crack <host> <service>` before you break anything.',
        'This prints the entire sum: your skill, your attribute, your '
        'program, every modifier, and the exact percentage. There are no '
        'hidden dice in this game and you can always ask.',
        done=lambda s: 'odds' in getattr(s, 'seen', set()),
        payoff='If a number ever surprises you, ask it this way.',
        topic='checks'),
    Step(
        'crack',
        'Break it open: `crack <host> <service>`.',
        'Cracking is the loudest ordinary thing you do. Noise wakes the '
        'countermeasures on that node, and enough of it puts the whole '
        'network on alert.',
        done=lambda s: _run(s) is not None and any(
            svc.cracked for n in _run(s).net.nodes.values()
            for svc in n.services if n.uid != _run(s).net.entry),
        payoff='One service open is enough to stand on the node.',
        topic='triangle'),
    Step(
        'status',
        'Type `status`.',
        'The trace is the clock. It runs to 100, it never falls on its own, '
        'and when it fills somebody cuts you loose. Watch the alert level '
        'too: every step up multiplies how fast the trace moves.',
        done=lambda s: 'status' in getattr(s, 'seen', set()),
        payoff='That number is the whole reason to be in a hurry.',
        topic='triangle'),
    Step(
        'move',
        'Move in with `connect <host>`, and keep going toward the objective.',
        '`status` names the objective node. Repeat scan, probe, crack, '
        'connect until you are standing on it. Deeper zones need a higher '
        'access tier, and cracking an auth server is how you get one.',
        done=lambda s: _run(s) is not None
        and _run(s).here != _run(s).net.entry,
        payoff='You are off the doorstep.',
        topic='firstrun'),
    Step(
        'out',
        'When you have what you came for, or when the trace gets close: '
        '`jack out`.',
        'There is no prize for the last asset you grabbed if the trace lands '
        'on you carrying it. Leaving early is a skill. If the job is not done '
        'and you still have room, this says so once and makes you type it '
        'again, so an accidental exit and a deliberate one look different.',
        done=lambda s: _run(s) is None and _has_game(s)
        and s.game.char.runs > 0,
        payoff='Out. Look at the residue line in that summary: it is the only '
               'number that follows you home.',
        topic='heat'),

    # -- the second half: the city remembers (D60) ------------------------------
    #
    # The tutorial used to stop at the door. The thesis of the game is what
    # happens after the door, and the one player with no way to tell that the
    # tutorial was incomplete was the one reading it.
    Step(
        'settle',
        'Spend a shift: `rest 1`. The residue you left is about to become '
        'somebody\'s attention.',
        'Residue does not follow you out of the network as heat. It follows '
        'you out as evidence, and a shift later somebody has read it, and '
        'then it is heat. That gap is the only reason getting out quietly '
        'ever feels like getting away with it.',
        done=lambda s: _has_game(s) and s.game.char.runs > 0
        and not s.game.city.pending,
        payoff='It has landed. Whatever you left behind is a number on a '
               'faction\'s side of the ledger now.',
        topic='heat'),
    Step(
        'rep',
        'Type `rep` to see how the city feels about you.',
        'Standing is what people will pay you; attention is how hard they '
        'are looking for you. They are different numbers and they move for '
        'different reasons, and past a threshold attention becomes a bounty, '
        'which is a faction paying for your name.',
        done=lambda s: 'rep' in getattr(s, 'seen', set()),
        payoff='Every number on that screen came from something you did, or '
               'something you were seen doing.',
        topic='heat'),
    Step(
        'look',
        'Type `look` to see where you are standing, who is about, and the '
        'places you can go and stand.',
        'A district is more than its market. There are people here who hand '
        'out work, keep private stock, do favours on a tab, and have opinions '
        'about what you are doing, and they keep hours. `look` says who is '
        'here now and who keeps other hours.',
        done=lambda s: 'look' in getattr(s, 'seen', set()),
        payoff='That is the city in one screen: the hour, the street, the '
               'people, the places.',
        topic='city'),
    Step(
        'talk',
        'Type `talk <name>` to somebody here, and `who is <name>` for what '
        'you know about them.',
        'Talking is how threads start. Meeting somebody sets a flag, and '
        'scenes arrive when their conditions hold, in whatever order the '
        'world produced them. Nobody here is a shop with a face on it.',
        done=lambda s: 'talk' in getattr(s, 'seen', set()),
        payoff='They have an opinion about you now. So will the story.',
        topic='people'),
    Step(
        'visit',
        'Type `visit <place>` to go and stand somewhere in the district. It '
        'costs nothing.',
        'The places are texture, and texture is most of what makes a city '
        'feel like it goes on when you are not looking. Some of the people '
        'are easier to find at their place than in the street.',
        done=lambda s: 'visit' in getattr(s, 'seen', set()),
        payoff='Every place in a scene is a place you can go and stand in '
               'afterwards.',
        topic='city'),
    Step(
        'journal',
        'Type `journal` to see what you have got yourself into.',
        'Threads, not quest chains: several are running at once, none of '
        'them waits for you, and advancing one changes the shape of another. '
        'The journal is where they are, and `choose` is how you answer one '
        'that is waiting on you.',
        done=lambda s: 'journal' in getattr(s, 'seen', set()),
        payoff='Every decision in there is read by the world, and every one '
               'has a line in the ending.',
        topic='threads'),
    Step(
        'now',
        'Press Enter on an empty line.',
        'That is `now`: the next real move, the reason, and the verbs that '
        'matter where you are standing. It is the answer to being lost, in '
        'the city and inside a run, and it never costs a thing.',
        done=lambda s: 'now' in getattr(s, 'seen', set()),
        payoff='Whenever you do not know what to type, that.',
        topic='basics'),
    Step(
        'door',
        'Type `retire` to see how far off the door is.',
        'There is a way out you choose, and it wants four things: nothing '
        'owed, nothing in you that you need, nobody paying for your name, '
        'and enough put away. None of them is hard alone. All four at once '
        'is the campaign.',
        done=lambda s: 'retire' in getattr(s, 'seen', set()),
        payoff='The door has been there since the first shift. Every system '
               'in this city is quietly making it further away.',
        topic='death'),
    Step(
        'again',
        'Take another contract: `board`, then `take <row>`.',
        'That is the loop. The second run is the one where the city '
        'remembers the first: the faction you hit is harder, the people who '
        'noticed you are looking, and the other runners have taken the work '
        'you did not.',
        done=lambda s: _has_game(s) and s.game.char.runs > 0
        and bool(s.game.city.accepted),
        payoff='Good. Everything from here is yours.',
        topic='firstrun'),
)

STEP_KEYS: tuple[str, ...] = tuple(s.key for s in STEPS)

OPENING = (
    'A guided run, one instruction at a time. Nothing is forced: do the '
    'steps in any order you like, ignore them entirely, or `tutorial stop`. '
    'It watches what you do and moves on when you have done it.'
)

CLOSING = (
    'That is the loop, and you have now done all of it once, and seen what '
    'the city does with it.\n\n'
    'What the tutorial did not cover, and what to read when you want it:\n'
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

#: Commands whose mere use satisfies a step. Tracked because "did they look at
#: it" is a legitimate teaching goal and is not otherwise visible in state.
WATCHED = ('char', 'board', 'deck', 'odds', 'status', 'rep', 'look',
           'talk', 'visit', 'journal', 'now', 'retire', 'errands', 'legend')
