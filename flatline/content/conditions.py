"""What the network is like tonight, which is not what it is. D61.

A network has a posture, which is how hard it is, and a shape, which is who
built it (D19). Those are fixed at generation. This is the third thing: a
condition, drawn when you jack in, announced at the door, shown on `status`
for the rest of the run, and read by the engine in every place it claims
to matter. About one run in two has one.

The rule is the same as for everything else in this game that claims to
change a number: every field here is read by attribute somewhere in the
engine, `validate.py` checks that, and a condition that touches a check
shows up in `odds` as its own term, because D14 says no hidden dice and a
modifier that is not in the sum is a hidden die wearing weather.

They are weather, not difficulty. The same network is a different run on
a different night, and that is the reason `legwork` cannot tell you
everything and the reason a fifth run against Kagawa is not the fourth.
"""

from __future__ import annotations

from dataclasses import dataclass

#: How often a run has a condition at all. Under a half, so that the plain
#: run is still the ordinary run and a condition is something that happened
#: tonight rather than the way networks are.
CHANCE = 0.45

#: The other runner: how often, per tick, they make noise somewhere you can
#: see, and how much.
GHOST_CHANCE = 0.12
GHOST_NOISE = 2


@dataclass(frozen=True, slots=True)
class Condition:
    key: str
    name: str
    #: Announced at the door. Second person, present tense.
    blurb: str
    #: One clause for `status` and for the list in the manual.
    summary: str
    #: Multipliers and offsets the engine reads. Neutral is 1.0 or 0.
    trace: float = 1.0
    noise: float = 1.0
    residue: float = 1.0
    #: Added to the noise a countermeasure needs before it wakes. Positive
    #: means they sleep longer.
    wake: int = 0
    #: Added to every crack check, as a visible term.
    crack: int = 0
    #: Multiplier on what the contract pays.
    pay: float = 1.0
    #: Verbs that cost one tick more than usual tonight.
    slow: tuple[str, ...] = ()
    #: Somebody else is in here, making noise you did not choose.
    ghost: bool = False
    #: How likely, relative to the others.
    weight: float = 1.0

    def terms(self) -> list[str]:
        """What it does, in numbers, for the door and for `status`. D14."""
        out: list[str] = []
        if self.trace != 1.0:
            out.append(f'trace x{self.trace:.2f}')
        if self.noise != 1.0:
            out.append(f'noise x{self.noise:.2f}')
        if self.residue != 1.0:
            out.append(f'residue x{self.residue:.2f}')
        if self.wake:
            out.append(f'countermeasures wake {abs(self.wake)} '
                       f'{"later" if self.wake > 0 else "sooner"}')
        if self.crack:
            out.append(f'{self.crack:+d} to every crack')
        if self.pay != 1.0:
            out.append(f'pay x{self.pay:.2f}')
        if self.slow:
            out.append('+1 tick to ' + ', '.join(self.slow))
        if self.ghost:
            out.append('somebody else making noise in here')
        return out

    @property
    def neutral(self) -> bool:
        return not self.terms()


CONDITIONS: tuple[Condition, ...] = (
    Condition(
        'maintenance', 'Maintenance window',
        'Somebody is doing maintenance. Half the countermeasures are in a '
        'reduced state, and the logging is in a heightened one, because that '
        'is what maintenance is.',
        'countermeasures slow to wake, trace fast',
        trace=1.15, wake=3, weight=1.2),
    Condition(
        'audit', 'Audit in progress',
        'Forensics are already in the building. Everything you leave will be '
        'read twice, and the patron knows it, which is why the number is what '
        'it is.',
        'residue counts half again, pay is better',
        residue=1.5, pay=1.15),
    Condition(
        'lockdown', 'Lockdown',
        'The network is on a posture it does not usually wear. Every door is '
        'a door tonight, and the things behind them are awake earlier than '
        'they should be.',
        'every crack harder, countermeasures wake sooner',
        crack=-1, wake=-1, weight=0.8),
    Condition(
        'ghost', 'Another runner inside',
        'Somebody else is in here. You will not meet them. You will meet '
        'their noise, and the desk is already awake because of it.',
        'noise you did not make, trace a little faster',
        ghost=True, trace=1.1),
    Condition(
        'dead', 'Dead hours',
        'The response desk is down to one person and they are doing '
        'something else. The trace runs slow. So, for the moment, does '
        'everything that would wake.',
        'trace slow, countermeasures slow to wake',
        trace=0.8, wake=1),
    Condition(
        'storm', 'Carrier storm',
        'The carrier is bad tonight. Everything that moves you takes longer, '
        'and the noise you make is lost in the noise that is already there.',
        'moving costs a tick more, noise counts less',
        slow=('connect', 'scan', 'probe'), noise=0.9),
    Condition(
        'exercise', 'Security exercise',
        'They are running an exercise. Everything wakes at a whisper, and '
        'everything you leave is lost in the logs of a thing that did not '
        'happen.',
        'countermeasures wake at a whisper, residue counts less',
        wake=-2, residue=0.7, weight=0.8),
    Condition(
        'skeleton', 'Skeleton crew',
        'A holiday, or the nearest thing this faction has. Half the desks are '
        'empty and half the doors are propped, and the patron has priced '
        'accordingly.',
        'every crack easier, pay is worse',
        crack=1, pay=0.9),
)

BY_KEY: dict[str, Condition] = {c.key: c for c in CONDITIONS}
CONDITION_KEYS: tuple[str, ...] = tuple(BY_KEY)


def pick(rng) -> Condition | None:
    """Tonight's condition, or None for an ordinary night.

    Drawn from its own stream, forked on the contract, so that the network a
    contract generates is the same network whether or not anybody looked at
    the weather (legwork regenerates it to read it, and must get the same
    one).
    """
    if not rng.chance(CHANCE):
        return None
    return BY_KEY[rng.weighted({c.key: c.weight for c in CONDITIONS})]
