"""The shapes a storyline is made of: a thread, its stages, the choices a
stage offers and the posting a stage can put on the board. They live apart
from the threads themselves so that `arcs.py` (the later arcs) and
`threads.py` (the first) can both import them without importing each other:
either module imported first used to fail on the cycle.

The rules a stage can require live here too, in `CONDITIONS`, because a rule
is part of the shape."""

from __future__ import annotations

from dataclasses import dataclass, field

#: World conditions usable in `requires`, alongside plain flags.
#: 'runs:N', 'diss:N', 'shift:N', 'credits:N', 'heat:N', 'met:<npc>',
#: 'rep:<faction>:N', 'ran:<faction>', 'did:<thread.stage>' (a posting
#: finished, see `Posting`).
CONDITIONS = ('runs', 'diss', 'shift', 'credits', 'heat', 'bounty', 'ninth', 'pet', 'familiar', 'titles', 'met', 'rep',
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
