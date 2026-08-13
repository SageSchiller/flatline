"""In-game scripting: the Daemonology payoff.

A script that only replays a recorded sequence is a macro, and a macro is not
what a netrunner writes. What they write is something that *checks* before it
acts and gets out when the numbers turn. So scripts here have conditions.

The language is deliberately tiny and deliberately looks like the shell it is
embedded in, because the player is a person at a prompt and not a programmer at
an IDE. Four statement forms and one comparison operator each:

    scan                          plain command
    if trace > 40: mask           conditional
    stop if alert red             abort the whole script
    repeat 3: crack gw01 shell    bounded loop

Conditions read live run state by name. There are no variables, no arithmetic,
no user-defined anything: this is a language for expressing "get out if it goes
wrong", not for computing. That ceiling is the point. A scripting system with a
real expression grammar would be a second game sitting next to the first one,
and the interesting decision is *which checks are worth writing*, not how
cleverly you can write them.

Everything here is pure: parsing produces `Step` objects and evaluation reads a
state object. The session executes. That split is what lets `validate.py` check
every shipped example and `test.py` evaluate every condition without a run.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

#: Longest a script may be. A runaway script cannot lock the session, and a
#: script this long is not a script, it is a plan.
MAX_STEPS = 24
#: Total commands one `script run` may dispatch, loops included.
MAX_DISPATCH = 60


class ScriptError(Exception):
    """A problem in the script text. Always shown to the player."""


# --------------------------------------------------------------------------
# conditions
# --------------------------------------------------------------------------

#: name -> (reader, kind). `kind` decides how it is compared and printed.
#: Numeric readers return an int; flag readers return a bool.
NUMERIC = {
    'trace': (lambda s: int(s.trace), 'the trace, 0 to 100'),
    'noise': (lambda s: int(s.node.noise), 'noise on the node you are in'),
    'focus': (lambda s: int(s.focus), 'Focus remaining'),
    'integrity': (lambda s: int(s.char.integrity_max - s.char.hurt - s.hurt),
                  'your remaining Integrity'),
    'tick': (lambda s: int(s.tick), 'ticks elapsed this run'),
    'haul': (lambda s: len(s.haul), 'assets taken so far'),
    'residue': (lambda s: int(s.residue_total), 'evidence left behind'),
    'tier': (lambda s: int(s.tier), 'the access tier you hold'),
}

FLAGS = {
    'ice': (lambda s: bool(s.node.live_ice),
            'anything alive is running on this node'),
    'locked': (lambda s: bool(s.locked),
               'something has locked on to you'),
    'open': (lambda s: bool(s.node.open),
             'you hold the node you are standing in'),
    'data': (lambda s: any(not a.taken for a in s.node.data),
             'there is something here worth taking'),
    'mapped': (lambda s: bool(s.node.mapped),
               'this node has been probed'),
    'ally': (lambda s: bool(s.ally and s.ally['state'] == 'with you'),
             'the runner you hired is still with you'),
    'escort': (lambda s: bool(s.escort and s.escort['state'] not in
                              ('out', 'dead')),
               'the runner you are covering is still in'),
}

#: Alert is neither: it compares against a named level, in order.
ALERT_LEVELS = ('green', 'amber', 'red', 'lockdown')

OPS = {
    '>': lambda a, b: a > b,
    '<': lambda a, b: a < b,
    '>=': lambda a, b: a >= b,
    '<=': lambda a, b: a <= b,
    '=': lambda a, b: a == b,
    '==': lambda a, b: a == b,
    '!=': lambda a, b: a != b,
}

_COND = re.compile(
    r'^(?P<not>not\s+)?(?P<name>[a-z]+)\s*'
    r'(?:(?P<op>>=|<=|==|!=|>|<|=)\s*(?P<value>\w+))?$')


@dataclass(frozen=True, slots=True)
class Condition:
    name: str
    op: str = ''
    value: str = ''
    negated: bool = False

    def evaluate(self, state) -> bool:
        result = self._raw(state)
        return (not result) if self.negated else result

    def _raw(self, state) -> bool:
        if self.name == 'alert':
            here = ALERT_LEVELS.index(state.alert)
            if not self.op:
                return here > 0
            if self.value not in ALERT_LEVELS:
                return False
            return OPS[self.op](here, ALERT_LEVELS.index(self.value))
        if self.name in NUMERIC:
            reader = NUMERIC[self.name][0]
            if not self.op:
                return bool(reader(state))
            try:
                target = int(self.value)
            except ValueError:
                return False
            return OPS[self.op](reader(state), target)
        if self.name in FLAGS:
            return bool(FLAGS[self.name][0](state))
        return False

    def __str__(self) -> str:
        head = 'not ' if self.negated else ''
        if self.op:
            return f'{head}{self.name} {self.op} {self.value}'
        return f'{head}{self.name}'


def parse_condition(text: str) -> Condition:
    text = text.strip().lower()
    if not text:
        raise ScriptError('a condition cannot be empty')
    match = _COND.match(text)
    if not match:
        raise ScriptError(f'{text!r} is not a condition I understand')
    name = match.group('name')
    if name not in NUMERIC and name not in FLAGS and name != 'alert':
        raise ScriptError(
            f'{name!r} is not something a script can check. Try: '
            + ', '.join(sorted({*NUMERIC, *FLAGS, 'alert'})))
    op, value = match.group('op') or '', match.group('value') or ''
    if name in FLAGS and op:
        raise ScriptError(f'{name!r} is a yes-or-no check and takes no '
                          f'comparison')
    if name in NUMERIC and op and not value.lstrip('-').isdigit():
        raise ScriptError(f'{name} compares against a number, not {value!r}')
    if name == 'alert' and op and value not in ALERT_LEVELS:
        raise ScriptError('alert compares against: '
                          + ', '.join(ALERT_LEVELS))
    return Condition(name=name, op=op, value=value,
                     negated=bool(match.group('not')))


# --------------------------------------------------------------------------
# statements
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Step:
    #: 'cmd' | 'if' | 'stop' | 'repeat'
    kind: str
    #: The command to run, for every kind except `stop`.
    command: str = ''
    condition: Condition | None = None
    count: int = 1
    #: The original text, for `script show`.
    source: str = ''


def parse_line(text: str) -> Step | None:
    """One line of script into a Step, or None for blanks and comments."""
    raw = text.strip()
    if not raw or raw.startswith('#'):
        return None
    low = raw.lower()

    if low.startswith('stop if '):
        return Step(kind='stop', condition=parse_condition(raw[8:]),
                    source=raw)
    if low == 'stop':
        raise ScriptError('`stop` needs a condition: `stop if trace > 60`')

    if low.startswith('if '):
        body = raw[3:]
        if ':' not in body:
            raise ScriptError('an `if` needs a colon: `if ice: strike`')
        cond, _, command = body.partition(':')
        command = command.strip()
        if not command:
            raise ScriptError('an `if` needs something to do')
        return Step(kind='if', command=command,
                    condition=parse_condition(cond), source=raw)

    if low.startswith('repeat '):
        body = raw[7:]
        if ':' not in body:
            raise ScriptError('a `repeat` needs a colon: `repeat 3: scan`')
        count, _, command = body.partition(':')
        count, command = count.strip(), command.strip()
        if not count.isdigit() or not 1 <= int(count) <= 10:
            raise ScriptError('`repeat` takes a count from 1 to 10')
        if not command:
            raise ScriptError('a `repeat` needs something to do')
        return Step(kind='repeat', command=command, count=int(count),
                    source=raw)

    return Step(kind='cmd', command=raw, source=raw)


def parse(lines) -> list[Step]:
    """A whole script. Raises on the first line that does not make sense."""
    steps: list[Step] = []
    for number, text in enumerate(lines, start=1):
        try:
            step = parse_line(text)
        except ScriptError as e:
            raise ScriptError(f'line {number}: {e}') from None
        if step is not None:
            steps.append(step)
    if len(steps) > MAX_STEPS:
        raise ScriptError(f'a script may be at most {MAX_STEPS} steps; '
                          f'this one is {len(steps)}')
    return steps


# --------------------------------------------------------------------------
# the library
# --------------------------------------------------------------------------


@dataclass(slots=True)
class Script:
    name: str
    lines: list = field(default_factory=list)

    @property
    def steps(self) -> list[Step]:
        return parse(self.lines)

    def to_dict(self) -> dict:
        return {'name': self.name, 'lines': list(self.lines)}

    @classmethod
    def from_dict(cls, d: dict) -> Script:
        return cls(name=d.get('name', 'unnamed'),
                   lines=list(d.get('lines') or []))


#: Shipped examples. These are teaching material as much as tools: a player who
#: reads `bailout` learns the whole conditional form in four lines, and one who
#: reads `sweep` learns that a script is where you put the checks you keep
#: forgetting to make by hand.
EXAMPLES: dict[str, tuple[str, ...]] = {
    'bailout': (
        '# Leave before it is too late to leave.',
        'stop if trace > 75',
        'if locked: mask',
        'jack out',
    ),
    'sweep': (
        '# Look around, carefully.',
        'scan',
        'if ice: probe',
        'stop if alert >= red',
    ),
    'grab': (
        '# Take what is here and clean up after.',
        'stop if alert >= red',
        'if data: pull --all',
        'if residue > 12: scrub',
    ),
}
