"""What time it is, and why it matters.

The city ran on a three-shift clock from the beginning and for a long time the
clock was a label. `morning`, `afternoon`, `night` appeared in the prompt, and
nothing anywhere read them. This file is that clock becoming a decision.

**The central inversion is that the street and the net want opposite hours.**

At the peak of the afternoon the district is full of people, which is bad for
you: more eyes, more chance that somebody with your name on a list is one of
them. But the network is also full of people, and their traffic is your cover.
Ten thousand legitimate sessions is the best mask money cannot buy.

At night the street empties out and nobody is looking at you. So does the
network, and now your session is the only session, and the trace has nothing
to sort you out of.

So there is no correct shift to work. There is a shift that suits the run you
are about to do, and the cost of waiting for it is that the contract board does
not wait for you. That is the whole design, and it is the same shape as the
noise/trace/residue triangle: two things you want, pulling against each other,
priced in the one currency the city actually charges in, which is time.

The numbers are deliberately small. This is a thumb on the scale that rewards
a player who notices, not a multiplier that makes off-peak runs unplayable.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Phase:
    key: str
    name: str
    #: One line, printed by `look` and `status`. What the city is doing.
    scene: str
    #: How dangerous the street is: eyes on you, in a district that has your
    #: name. Multiplies the danger score `travel` already computes.
    danger: float = 1.0
    #: How fast the trace runs in here, because a trace is a search through
    #: everybody's traffic and the size of that haystack changes.
    trace: float = 1.0
    #: What the market charges. Out of hours costs more, everywhere.
    price: float = 1.0
    #: Added to legwork quality. Asking people things works better when there
    #: are people to ask.
    legwork: int = 0
    #: The one-line reason, shown next to the numbers so the player can plan
    #: rather than memorise.
    why: str = ''


PHASES: tuple[Phase, ...] = (
    Phase(
        'morning', 'Morning',
        'The district is getting up. Shutters going back, the first shift '
        'already gone, and the queue outside the clinic resolving itself into '
        'the people who will be seen and the people who will not.',
        danger=1.0, trace=1.0, price=1.0, legwork=0,
        why='Everything is what it is. Stock lands this shift.'),
    Phase(
        'afternoon', 'Afternoon',
        'Peak. Every walkway is at capacity and the market is doing the '
        'business it does, which is most of the business it does all day.',
        danger=1.18, trace=0.92, price=1.0, legwork=1,
        why='More eyes on the street, and more traffic in the net to hide in.'),
    Phase(
        'night', 'Night',
        'The district has gone quiet in the way it goes quiet, which is not '
        'silent, just down to the people who have a reason. Half the market '
        'is shuttered and the half that is not has adjusted its prices.',
        danger=0.78, trace=1.10, price=1.14, legwork=-1,
        why='Nobody is looking at you out here. In there, you are the only '
            'thing to look at.'),
)

BY_KEY: dict[str, Phase] = {p.key: p for p in PHASES}
PHASE_KEYS: tuple[str, ...] = tuple(BY_KEY)


def phase(key: str) -> Phase:
    return BY_KEY.get(key) or PHASES[0]


def modifier(key: str, field_name: str) -> float:
    """One number from the current shift, for a caller that wants only one."""
    return getattr(phase(key), field_name)
