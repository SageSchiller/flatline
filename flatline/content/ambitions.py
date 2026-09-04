"""Ambitions (D117): the ladder between one job and the whole story.

A run is a night. The thirty-five story threads are the years. Between them
there was nothing telling a player what they were building toward, so a
newcomer who had learned the loop had no next mountain to point at, and the
game's honest answer to "why keep playing" was buried in scenes they had not
found yet.

An ambition is a small, visible goal a runner would actually hold: get on
your feet, make a name, carry the kit the real jobs need, find out what
Deepwater is. Each is a predicate over state the game already tracks, so
nothing new has to be stored except which ones have been met, and that lives
in the story's own flag set (`won:<key>`), which already saves and loads.

When one is met it prints a beat and, where it fits, a small recognition
bounty. The point is not the money. The point is that there is always a next
thing worth wanting, and the game says so.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from . import factions, programs


@dataclass(frozen=True, slots=True)
class Ambition:
    key: str
    title: str
    #: What it is, and why a runner would want it.
    blurb: str
    #: What to do about it, shown while it is still open.
    hint: str
    #: done(game) -> bool. Total and cheap: it runs after every command.
    done: Callable
    #: A small recognition payout, or zero where the thing itself is the
    #: reward (the kit, the skill, the answer).
    reward: int = 0
    #: The line printed when it lands.
    line: str = ''


def _owns_payload(char) -> bool:
    return any(programs.BY_KEY[k].category == 'payload'
               for k in char.library if k in programs.BY_KEY)


def _best_rep(game) -> int:
    return max((game.alias.reputation(k) for k in factions.FACTION_KEYS),
               default=0)


def _best_skill(char) -> int:
    from . import skills
    return max((char.skill(k) for k in skills.SKILL_KEYS), default=0)



def _endings() -> frozenset:
    from . import threads as thread_content
    return thread_content.SPINE_ENDINGS

AMBITIONS: tuple[Ambition, ...] = (
    Ambition('feet', 'On your feet',
             'Finish a job. One clean pull and you are a runner, not a '
             'tourist standing at a prompt.',
             'Take the softest thing on the `board` and see it through.',
             lambda g: g.char.runs >= 1, reward=250,
             line='One job behind you. Nobody knows your name yet. The deck '
                  'does.'),
    Ambition('kit', 'Properly equipped',
             'Carry a payload of your own. It is the difference between '
             'watching a network and taking something out of one.',
             'Buy one at a `market`: exfiltrate, wipe and implant all need '
             'it.',
             lambda g: _owns_payload(g.char),
             line='You have a payload on the deck now. The real jobs were '
                  'always the ones that needed it.'),
    Ambition('name', 'A name on the street',
             'Get one faction to think of you as somebody, for good or for '
             'ill. Reputation is the whole economy underneath the money.',
             'Work for the same people, or against them, until it shows in '
             '`rep`.',
             lambda g: _best_rep(g) >= 40, reward=600,
             line='Somebody said your handle tonight without being asked who '
                  'you were. That is worth more than the fee.'),
    Ambition('somebody', 'Somebody in particular',
             'Take one skill to rank three: the point a runner stops being '
             'general and starts being a specific kind of dangerous.',
             'Spend experience with `train` on the line you play the most.',
             lambda g: _best_skill(g.char) >= 3, reward=400,
             line='Three ranks deep in one thing. You are not a runner in '
                  'general any more. You are this one.'),
    Ambition('deepwater', 'What Deepwater is',
             'Nine years of contracts and nobody ever met anybody. Chase the '
             'thing the whole city talks around.',
             'It finds you as you run. Follow it in the `journal`, and ask '
             'the people it names.',
             # Hearing the name was enough for this once (D144). Finding
             # out is the three facts, or having gone all the way.
             lambda g: ('dw_pattern' in g.story.flags
                        or bool(g.story.flags & _endings())),
             line='Three facts and the shape they make. You know what it is '
                  'now, which is more than the people who placed the '
                  'contracts ever did.'),
    Ambition('stash', 'A stake worth keeping',
             'Sit on ten thousand credits at once. Enough to walk away from a '
             'bad night, which is the only real freedom in here.',
             'Take the jobs that pay and do not spend it all at the '
             '`market`.',
             lambda g: g.char.credits >= 10000,
             line='Ten thousand clear. Enough to say no to a job for the '
                  'first time.'),
    Ambition('survive', 'Still breathing',
             'Reach your seventh night. Most runners this city makes do not, '
             'and the ones who do are the ones it starts to fear.',
             'Keep taking work, and keep getting out of it.',
             lambda g: g.city.day >= 7, reward=1000,
             line='Seven nights. The city has started keeping track of you, '
                  'and that cuts both ways.'),
)

BY_KEY: dict[str, Ambition] = {a.key: a for a in AMBITIONS}


def _won(game, key: str) -> bool:
    return f'won:{key}' in game.story.flags


def newly_met(game) -> list[Ambition]:
    """Ambitions true now that have not yet been marked. Cheap: predicates
    over live state, no side effects."""
    return [a for a in AMBITIONS if not _won(game, a.key) and a.done(game)]


def claim(game, ambition: Ambition) -> None:
    game.story.flags.add(f'won:{ambition.key}')


def status(game) -> list[tuple[Ambition, bool]]:
    """Every ambition with whether it is met, in ladder order."""
    return [(a, _won(game, a.key) or a.done(game)) for a in AMBITIONS]


def next_open(game) -> Ambition | None:
    """The first ambition still open: the next mountain to point at."""
    for a in AMBITIONS:
        if not (_won(game, a.key) or a.done(game)):
            return a
    return None
