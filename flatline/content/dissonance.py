"""The drift, city-side. What being mostly machine costs and what it opens.

D11 made Dissonance a permanent one-way cost and gave it net-side payoffs:
composure against black ICE, and the coherence to wear icons no person could
hold. What it never had was anything *written* for it. A number that only
appears in a price multiplier is a spreadsheet entry, not an arc.

So this file is the city half. Three kinds of thing:

**Passages** fire once, when you cross a band, and they are the whole emotional
payload. They are written in the second person and they are not reassuring.

**Doors** open and close by band. Some content requires you to be far enough
gone, which is the payoff: the deepest chrome in the city is sold by people who
will only deal with somebody who has already stopped being a customer and
started being a colleague. Other content closes, because a person who lags when
they speak cannot talk their way into a building.

**Grounding** is the valve. It exists so the arc is a decision rather than a
ratchet, and it is deliberately bad value: expensive, slow, partial, and it
hurts. You can come back. You cannot come back all the way, and D11's rule that
the mark stays holds even here: grounding lowers Dissonance without ever
returning what you sold to get it.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Band floors, matching cyberware.DISSONANCE_BANDS. Repeated here as an
#: explicit contract rather than imported, because `validate.py` asserts the
#: two agree and a silent divergence would put a passage on the wrong band.
BANDS = (0, 25, 50, 75)


@dataclass(frozen=True, slots=True)
class Passage:
    """One crossing. Printed once, the first time you go past."""

    band: int
    title: str
    text: str


PASSAGES: tuple[Passage, ...] = (
    Passage(
        25, 'Drifting',
        'It starts with transitions. You jack out and there is a half-second '
        'where you are still deciding which of the two rooms is the one you '
        'are in, and the decision feels arbitrary rather than obvious. It '
        'passes. You notice that it passed, and you notice that you had to '
        'wait for it to.'),
    Passage(
        50, 'Submerged',
        'Somebody in Marrow asks you a question and you answer it a beat '
        'late, because the answer had to come up from somewhere. They do not '
        'say anything. They do adjust, very slightly, the way people adjust '
        'around a man with a limp.\n\n'
        'Clinics have started quoting you differently. Not more, exactly. '
        'Differently, the way a garage quotes a fleet.'),
    Passage(
        75, 'Dissolved',
        'You have stopped thinking of the net as somewhere you go. It is the '
        'room. The other place, with the weather and the noodle bar and the '
        'people who need eight hours a night, is the thing on the far side of '
        'a window you are increasingly not looking through.\n\n'
        'This is a recognised condition and there is a word for it in the '
        'Aoyama literature. You have read the paper. It did not describe '
        'anything you would call a problem.'),
)

BY_BAND: dict[int, Passage] = {p.band: p for p in PASSAGES}


# --------------------------------------------------------------------------
# doors
# --------------------------------------------------------------------------

#: The black clinic. Not a district service: a thing that exists in districts
#: with a clinic, for people the ordinary clinic has stopped being able to
#: help. It carries what nobody licensed will fit.
DEEP_CLINIC_BAND = 50
DEEP_CLINIC_DISCOUNT = 0.82

DEEP_CLINIC_ARRIVAL = (
    'The address is a loading bay behind the clinic proper, and the person '
    'who answers does not ask what you want. They look at your eyes for '
    'slightly too long, decide something, and stand aside.'
)

DEEP_CLINIC_REFUSED = (
    'The woman on the desk is polite about it. "This is for patients with '
    'ongoing integration needs." She looks at you the way you would look at '
    'somebody who had wandered into the wrong funeral. You are, by her '
    'standards, fine.'
)

#: Legwork that only works if you are far enough into it. Costs nothing and
#: takes a shift, like the rest, but the mechanism is that you are closer to
#: the network than you are to people now.
RESONANCE_BAND = 50
RESONANCE_TEXT = (
    'You do not go and look. You sit in a room a few hundred metres from the '
    'building and let the shape of it arrive. It takes most of a shift and it '
    'is not something you could explain to anybody who would want it '
    'explained.'
)

#: Social legwork stops being available: a pretext needs a voice that does not
#: lag, and yours does.
SOCIAL_FLOOR_BAND = 75
SOCIAL_REFUSED = (
    'You get as far as the front desk. Whatever happens in the four seconds '
    'after that, it ends with somebody quietly pressing a button under the '
    'counter, and you leaving before you find out which button.'
)


# --------------------------------------------------------------------------
# grounding
# --------------------------------------------------------------------------

#: What one course costs, and what it gives back. Priced so that a chromed
#: build cannot casually undo the arc: this is a decision about who you want
#: to be, taken at real expense.
GROUND_COST = 6800
GROUND_SHIFTS = 3
GROUND_POINTS = (8, 14)
#: Integrity damage the course does. It is neurological work and it is not
#: gentle.
GROUND_HURT = (3, 7)

GROUND_TEXT = (
    'Three shifts in a reclining chair in a room with no screens, while '
    'somebody who will not give you their surname walks your interface layer '
    'back through a sequence it has been running away from. It is not '
    'painful in the way a burn is painful. It is painful in the way that '
    'having a decision reversed is painful.\n\n'
    'You come out of it slower, and more here, and less than you were.'
)

GROUND_FLOOR_TEXT = (
    'They will not take you any lower than this. Past a certain point what '
    'is left is not drift, it is architecture, and the only way to reverse '
    'architecture is to remove it.'
)

#: Grounding cannot take you below the Dissonance your installed chrome
#: implies. You can walk back what the work did to you. You cannot walk back
#: the hardware while it is still in you.
GROUND_FLOOR_RULE = 'sum of installed cyberware dissonance'


def band_of(value: int) -> int:
    """The band floor a Dissonance value sits in."""
    out = BANDS[0]
    for floor in BANDS:
        if value >= floor:
            out = floor
    return out


def crossed(before: int, after: int) -> list[Passage]:
    """Every passage between two Dissonance values, in order.

    Returns a list rather than one, because a single expensive implant can
    take somebody through two bands at once and skipping the first would lose
    the only writing that band ever gets.
    """
    return [p for p in PASSAGES if before < p.band <= after]
