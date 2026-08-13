"""Resolution. One check model for the whole game, per D14.

    margin = power + d10 - resistance - 5

`power` is everything you bring, `resistance` is twice the difficulty rating,
and the d10 minus five gives a symmetric spread of -4 to +5. Success is a
margin of zero or better.

The important property is not the formula, it is that a `Check` **records its
terms**. Every contribution is kept as a labelled number, so `odds` can print
the whole sum before you commit and a failure can name the term that sank it.
A deep system that will not show its working is indistinguishable from an
unfair one, and the player has to be able to tell the difference.

Exact probabilities are computable rather than estimated, because the only
random input is a single d10. `odds` prints a real percentage, not a guess.
"""

from __future__ import annotations

from dataclasses import dataclass, field

DIE = 10
#: Subtracted so that an average roll contributes about half a point rather
#: than five and a half, which keeps `power` and `resistance` directly
#: comparable when reading the maths.
OFFSET = 5

#: Margins at or beyond these are exceptional in either direction.
CRIT = 8
FUMBLE = -8


@dataclass(slots=True)
class Term:
    label: str
    value: int
    #: Shown in explanations as the thing to fix. False for fixed costs.
    actionable: bool = True


@dataclass(slots=True)
class Check:
    """A resolvable check with a full audit trail."""

    name: str
    resistance: int
    terms: list[Term] = field(default_factory=list)
    #: Filled by `resolve`.
    roll: int = 0
    margin: int = 0
    resolved: bool = False

    def add(self, label: str, value: float, actionable: bool = True) -> Check:
        """Record a contribution. Zero-valued terms are dropped: a list of
        modifiers that are all zero teaches the player nothing and buries the
        two that matter."""
        v = int(round(value))
        if v:
            self.terms.append(Term(label, v, actionable))
        return self

    @property
    def power(self) -> int:
        return sum(t.value for t in self.terms)

    @property
    def target(self) -> int:
        """The lowest d10 that succeeds. Below 1 is automatic, above 10 is
        impossible, and both cases are worth telling the player about."""
        return self.resistance + OFFSET - self.power

    @property
    def chance(self) -> float:
        """Exact probability of success."""
        need = self.target
        if need <= 1:
            return 1.0
        if need > DIE:
            return 0.0
        return (DIE - need + 1) / DIE

    @property
    def certain(self) -> bool:
        return self.chance >= 1.0

    @property
    def impossible(self) -> bool:
        return self.chance <= 0.0

    def resolve(self, rng) -> Check:
        self.roll = rng.int(1, DIE)
        self.margin = self.power + self.roll - self.resistance - OFFSET
        self.resolved = True
        return self

    @property
    def success(self) -> bool:
        return self.margin >= 0

    @property
    def critical(self) -> bool:
        return self.margin >= CRIT

    @property
    def fumble(self) -> bool:
        return self.margin <= FUMBLE

    # -- explanation -------------------------------------------------------

    def culprit(self) -> Term | None:
        """The weakest actionable term: what the player should go and fix.

        Picks the most negative term if there is one, otherwise the smallest
        positive contribution, because "your Intrusion is doing almost nothing
        here" is more useful than "the dice were bad".
        """
        actionable = [t for t in self.terms if t.actionable]
        if not actionable:
            return None
        worst = min(actionable, key=lambda t: t.value)
        return worst

    def explain(self) -> str:
        """One line of markup: the whole sum, for `odds` and for failures."""
        parts = []
        for t in self.terms:
            sign = '+' if t.value >= 0 else ''
            role = 'ok' if t.value >= 0 else 'err'
            parts.append(f'[{role}]{sign}{t.value}[/] [dim]{t.label}[/]')
        body = ' '.join(parts) if parts else '[dim]nothing[/]'
        return (f'{body} [dim]vs[/] [warn]{self.resistance}[/] '
                f'[dim]resistance[/]')

    def summary(self) -> str:
        """The headline: what it takes and how likely it is."""
        if self.impossible:
            return ('[err]impossible[/] as configured: you need more than the '
                    'die can give')
        if self.certain:
            return '[ok]automatic[/]'
        pct = int(round(self.chance * 100))
        role = 'ok' if pct >= 70 else 'warn' if pct >= 40 else 'err'
        return f'[{role}]{pct}%[/] [dim](need {self.target} or better on d10)[/]'


def opposed(name: str, resistance: int) -> Check:
    return Check(name=name, resistance=resistance)
