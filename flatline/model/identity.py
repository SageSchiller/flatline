"""Aliases, per D13. The container for both heat and reputation.

The whole design is one sentence: **heat and reputation live on the same
object, and burning it dumps both.**

That is what makes the decision hard. If burning an alias only cleared heat it
would be a consumable, bought whenever things got warm and never thought about
again. Because it also erases every relationship built under that name, a
runner with four shifts of Switchboard goodwill and a Nightwatch problem has a
genuine dilemma, and the answer changes depending on what they were planning to
do next.

Faction posture deliberately does **not** live here. A corporation that has
been robbed hardens its networks whether or not it ever learns who did it, so
posture belongs to the city and survives any number of new names.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..content import factions

#: What it costs to establish a new identity that will survive scrutiny.
ALIAS_COST = 1800
#: Shifts of downtime while the new name beds in.
ALIAS_SHIFTS = 2
#: Heat on any one faction above which an alias is effectively spent. Not a
#: hard limit: the player may keep running a hunted alias, and sometimes that
#: is correct, because a new name starts at zero reputation too.
BURN_THRESHOLD = 85


@dataclass(slots=True)
class Alias:
    name: str
    #: Shift on which it was established. Age is its own kind of credibility.
    established: int = 0
    rep: dict = field(default_factory=dict)
    heat: dict = field(default_factory=dict)
    burned: bool = False
    #: Runs completed under this name. Shown on `alias`, and it is the thing a
    #: player actually feels when they consider throwing the name away.
    runs: int = 0

    # ------------------------------------------------------------------

    def reputation(self, faction: str) -> int:
        return int(self.rep.get(faction, 0))

    def attention(self, faction: str) -> int:
        return int(self.heat.get(faction, 0))

    def adjust_rep(self, faction: str, delta: float) -> int:
        """Change standing, and propagate to allies and rivals.

        Propagation is the reason the relations table exists. Helping the
        Switchboard warms the Sixes a little and cools Nightwatch a little,
        automatically, so a player who reads the table can plan a run whose
        real payload is the political side effect.
        """
        if faction not in factions.BY_KEY:
            return 0
        value = self._set_rep(faction, self.reputation(faction) + delta)
        for other in factions.FACTION_KEYS:
            if other == faction:
                continue
            rel = factions.relation(faction, other)
            if rel:
                # Knock-on is deliberately weaker than the direct change, so
                # that indirect politics never outweighs the work itself.
                self._set_rep(other, self.reputation(other) + delta * rel * 0.4)
        return value

    def _set_rep(self, faction: str, value: float) -> int:
        clamped = max(-100, min(100, int(round(value))))
        self.rep[faction] = clamped
        return clamped

    def add_heat(self, faction: str, delta: float) -> int:
        if faction not in factions.BY_KEY:
            return 0
        value = max(0, min(100, int(round(self.attention(faction) + delta))))
        self.heat[faction] = value
        return value

    def decay_heat(self, rate: float = 1.0) -> None:
        """One shift of forgetting. Corps forget faster than gangs.

        `rate` scales it, which is how the Legally Dead origin's passive
        becomes real: there is nothing to attach the heat to.
        """
        for key in list(self.heat):
            fac = factions.BY_KEY.get(key)
            if not fac:
                continue
            self.heat[key] = max(
                0, int(round(self.heat[key] - fac.heat_decay * rate)))
            if not self.heat[key]:
                del self.heat[key]

    # ------------------------------------------------------------------

    @property
    def hottest(self) -> tuple[str, int]:
        if not self.heat:
            return ('', 0)
        key = max(self.heat, key=lambda k: self.heat[k])
        return (key, self.heat[key])

    @property
    def spent(self) -> bool:
        """Whether this name has outlived its usefulness."""
        return self.hottest[1] >= BURN_THRESHOLD

    def standing(self) -> list[tuple[str, int, int]]:
        """(faction, rep, heat) for every faction the player has touched."""
        keys = sorted(set(self.rep) | set(self.heat))
        return [(k, self.reputation(k), self.attention(k)) for k in keys]

    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {'name': self.name, 'established': self.established,
                'rep': {k: v for k, v in self.rep.items() if v},
                'heat': {k: v for k, v in self.heat.items() if v},
                'burned': self.burned, 'runs': self.runs}

    @classmethod
    def from_dict(cls, d: dict) -> Alias:
        return cls(name=d.get('name', 'nobody'),
                   established=int(d.get('established', 0)),
                   rep={k: int(v) for k, v in (d.get('rep') or {}).items()},
                   heat={k: int(v) for k, v in (d.get('heat') or {}).items()},
                   burned=bool(d.get('burned', False)),
                   runs=int(d.get('runs', 0)))


# --------------------------------------------------------------------------
# name generation
# --------------------------------------------------------------------------

#: Handles read as chosen, not as generated, so they are built from concrete
#: nouns and plain adjectives rather than from syllable soup.
_FIRST = (
    'quiet', 'seventh', 'paper', 'iron', 'low', 'winter', 'half', 'grey',
    'north', 'small', 'last', 'blue', 'thin', 'hollow', 'first', 'salt',
    'clean', 'long', 'dry', 'still',
)
_SECOND = (
    'lantern', 'switch', 'harbour', 'ledger', 'window', 'signal', 'anchor',
    'kettle', 'marker', 'bishop', 'compass', 'needle', 'gantry', 'crane',
    'shutter', 'meridian', 'chapel', 'furnace', 'archive', 'pillar',
)


def generate_name(rng) -> str:
    """A plausible working name. Two words, lowercase, no numbers."""
    return f'{rng.pick(_FIRST)} {rng.pick(_SECOND)}'
