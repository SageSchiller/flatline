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
        'Type `new` to see the ten origins, then '
        '`new <a name> --origin <key>` to pick one.',
        'An origin sets where you start and never where you can go. If you '
        'have no preference, `gutter` is the straightforward one: fast, '
        'cheap, and loud.',
        done=lambda s: _has_game(s),
        payoff='That is a character. Everything from here is theirs.',
        topic='attributes'),
    Step(
        'sheet',
        'Type `char` to read the build.',
        'Five attributes, and four numbers derived from them. Bandwidth is '
        'how much chrome fits in you, Focus is precision actions per run, '
        'Tempo is actions per tick, and Integrity is how much damage you '
        'absorb before a run ends badly.',
        done=lambda s: bool(_char(s)) and 'char' in getattr(s, 'seen', set()),
        payoff='Those numbers are what every check in the game is built on.',
        topic='attributes'),
    Step(
        'spend',
        'Spend a point with `boost <attribute>`, and an experience with '
        '`train <skill>`.',
        'You start with six attribute points and twelve experience. Ranks 2 '
        'and 4 of any skill unlock a technique, which is a new verb rather '
        'than a bigger number, so `train intrusion` twice is a real change to '
        'what you can type.',
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
        'If the job is elsewhere, `travel <district>`. Then `jack in`.',
        'Travel costs a shift, and shifts are the city\'s real currency. '
        'While they pass, contracts expire and other people work.',
        done=lambda s: _run(s) is not None,
        payoff='You are inside somebody else\'s network now.',
        topic='city'),
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
        'on you carrying it. Leaving early is a skill.',
        done=lambda s: _run(s) is None and _has_game(s)
        and s.game.char.runs > 0,
        payoff='Out. Look at the residue line in that summary: it is the only '
               'number that follows you home.',
        topic='heat'),
)

STEP_KEYS: tuple[str, ...] = tuple(s.key for s in STEPS)

OPENING = (
    'A guided run, one instruction at a time. Nothing is forced: do the '
    'steps in any order you like, ignore them entirely, or `tutorial stop`. '
    'It watches what you do and moves on when you have done it.'
)

CLOSING = (
    'That is the loop, and you have now done all of it once.\n\n'
    'What the tutorial did not cover, and what to read when you want it:\n'
    '  [fg]help triangle[/]   the three numbers, properly\n'
    '  [fg]help heat[/]       what the residue you left is about to become\n'
    '  [fg]help skills[/]     where your experience should go\n'
    '  [fg]help rivals[/]     the other people doing this job\n'
    '  [fg]help money[/]      what things cost and what a run is worth\n\n'
    'The residue from that run becomes heat in a shift or so. Everything '
    'else in this city follows from that one fact.'
)

#: Commands whose mere use satisfies a step. Tracked because "did they look at
#: it" is a legitimate teaching goal and is not otherwise visible in state.
WATCHED = ('char', 'board', 'deck', 'odds', 'status')
