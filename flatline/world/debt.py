"""Owing somebody money, and what happens when you keep owing it.

Two origins ship with a debt. The academic's has been in their complication
text since the first day of the project and did nothing, which is exactly the
kind of promise a game should not make: a line that says "it is compounding"
had better compound.

The design is deliberately simple and deliberately nasty. It grows every shift,
it grows faster the longer you ignore it, and the lender is not a bank. What it
buys the player is a clock that is not the trace: something that makes sitting
still expensive in a way heat decay does not, and that turns "take the safe
contract" into a decision rather than a default.

**It is survivable.** A debt you cannot clear is a dead character, and D6 says
nothing but black ICE ends a character. So the lender escalates through the
same fallout ladder everything else uses: they take a payment out of you in
kind, and the debt drops when they do. It is a spiral you can be dragged down,
not one you fall out of the bottom of.
"""

from __future__ import annotations

from dataclasses import dataclass

#: The house terms, used by any debt that does not carry its own: the two
#: origins that ship owing somebody, and every save written before lenders
#: existed. A debt taken deliberately records the terms it was taken on,
#: because the terms are the decision.
RATE = 0.035
#: Shifts of grace before the lender starts taking an interest in person.
GRACE = 12
#: Once they are collecting, how often they come round.
COLLECT_EVERY = 6
#: What a visit takes, as a fraction of the outstanding debt, and the floor.
COLLECT_FRACTION = 0.25
COLLECT_MIN = 400


@dataclass(slots=True)
class Debt:
    """One outstanding obligation. Characters have at most one."""

    amount: int = 0
    lender: str = ''
    #: Shift on which the lender last took something, or -1 for never.
    last_collected: int = -1
    #: Shift the debt was taken on, which is what GRACE counts from.
    opened: int = 0
    #: Flavour: what they will say they are, when they finally say something.
    note: str = ''
    #: The terms this particular debt was taken on. Zero means the house
    #: rate, which is what every debt handed to you rather than chosen runs
    #: at, and what every save older than lenders has.
    rate: float = 0.0
    grace: int = 0

    @property
    def terms(self) -> tuple[float, int]:
        return (self.rate or RATE, self.grace or GRACE)

    @property
    def owed(self) -> bool:
        return self.amount > 0

    def accrue(self) -> int:
        """One shift of interest. Returns what it grew by."""
        if not self.owed:
            return 0
        before = self.amount
        self.amount = int(round(self.amount * (1.0 + self.terms[0])))
        return self.amount - before

    def due(self, shift: int) -> bool:
        """Whether the lender is coming round this shift."""
        grace = self.terms[1]
        if not self.owed or shift - self.opened < grace:
            return False
        since = shift - (self.last_collected if self.last_collected >= 0
                         else self.opened + grace)
        return since >= COLLECT_EVERY

    def collect(self, shift: int) -> int:
        """What they are taking. The debt drops by it either way."""
        take = max(COLLECT_MIN, int(self.amount * COLLECT_FRACTION))
        take = min(take, self.amount)
        self.amount -= take
        self.last_collected = shift
        return take

    def pay(self, amount: int) -> int:
        """Put money against it. Returns what was actually applied."""
        applied = max(0, min(amount, self.amount))
        self.amount -= applied
        return applied

    def to_dict(self) -> dict:
        return {'amount': self.amount, 'lender': self.lender,
                'last_collected': self.last_collected, 'opened': self.opened,
                'note': self.note, 'rate': self.rate, 'grace': self.grace}

    @classmethod
    def from_dict(cls, d: dict) -> Debt:
        return cls(amount=int(d.get('amount', 0)), lender=d.get('lender', ''),
                   last_collected=int(d.get('last_collected', -1)),
                   opened=int(d.get('opened', 0)), note=d.get('note', ''),
                   rate=float(d.get('rate', 0.0)),
                   grace=int(d.get('grace', 0)))


#: What the lender says when the grace period ends and they turn up.
FIRST_VISIT = (
    'Somebody is waiting outside your door who is not in a hurry and does not '
    'introduce themselves. They mention the number. They do not mention what '
    'happens if the number stops moving in the right direction, because they '
    'do not have to.'
)

COLLECT_LINES = (
    'They take it out of your account in front of you, on a handset, and then '
    'stand there a moment longer than the transaction needed.',
    'The collection is polite, itemised, and receipted. Somebody has thought '
    'about how to make this feel like admin.',
    'They do not knock. The money is gone by the time you have finished '
    'deciding whether to say anything.',
)

#: When there is nothing to take, they take something else.
IN_KIND = (
    'There is nothing in the account, so they look around the room and price '
    'it instead.'
)


def tick(debt: Debt, shift: int) -> tuple[int, str]:
    """One shift of debt. Returns (interest, note) for the caller to print."""
    if not debt.owed:
        return 0, ''
    interest = debt.accrue()
    if shift - debt.opened == debt.terms[1]:
        return interest, f'[err]{FIRST_VISIT}[/]'
    return interest, ''
