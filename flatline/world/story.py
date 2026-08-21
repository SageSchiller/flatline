"""Live story state: who you have met, what you know, what you decided.

The whole system is one set of strings. Meeting somebody sets `met:<key>`,
reaching a stage sets whatever that stage sets, and taking a choice sets
whatever that choice sets. Everything else is a query against that set.

That is deliberately the simplest thing that can work, and it is what makes
the criss-crossing free: a thread does not need to know another thread exists
in order to read a flag it happened to set. Vance's thread never mentions
Lark's, and taking Vance's offer closes a door in Lark's anyway, because they
share a string.

**Nothing here is scheduled.** Stages are checked whenever the world moves,
and any stage whose condition now holds becomes available immediately. A player
who does things in an order nobody anticipated gets the scenes in that order,
which is why every stage is written as a scene rather than as a step.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..content import npcs as npc_content
from ..content import threads as thread_content


@dataclass(slots=True)
class Story:
    #: Everything that has happened, as flags. The entire state of the layer.
    flags: set = field(default_factory=set)
    #: thread key -> stage keys reached, in the order they were reached.
    reached: dict = field(default_factory=dict)
    #: Stage keys presented and awaiting a choice, as 'thread.stage'.
    pending: list = field(default_factory=list)
    #: NPC keys met, which is also mirrored into flags as `met:<key>`.
    met: set = field(default_factory=set)
    #: NPC key -> favours you have asked for and not yet worked off. The one
    #: number that makes work and favours the same relationship instead of two
    #: features: asking costs one, finishing a job they handed you clears one,
    #: and past `offers.OWED_LIMIT` they stop taking your calls.
    owed: dict = field(default_factory=dict)
    #: NPC key -> the shift you last got a job out of them, so a person is a
    #: relationship rather than a vending machine for contracts.
    asked: dict = field(default_factory=dict)

    # ------------------------------------------------------------------

    def has(self, flag: str) -> bool:
        return flag in self.flags

    def meet(self, key: str) -> bool:
        """Record a first meeting. True if it was in fact the first."""
        if key in self.met:
            return False
        self.met.add(key)
        self.flags.add(f'met:{key}')
        return True

    def stage_done(self, thread: str, stage: str) -> bool:
        return stage in self.reached.get(thread, [])

    # ------------------------------------------------------------------

    def satisfied(self, rule: str, game) -> bool:
        """Whether one requirement holds. Unknown rules are never satisfied,
        which fails closed: a typo hides a scene rather than unlocking one.

        `not:<rule>` is the one combinator, and it exists for D51: a dead
        friend's work has to stop being on offer, and "Lark is alive" is not
        a flag anything sets, it is the absence of one.
        """
        if rule.startswith('not:'):
            return not self.satisfied(rule[4:], game)
        if ':' not in rule:
            return rule in self.flags
        kind, _, value = rule.partition(':')
        if kind == 'met':
            return f'met:{value}' in self.flags
        if kind == 'ran':
            return f'ran:{value}' in self.flags
        if kind == 'did':
            # A posting finished. The flag carries its own colon, so it is
            # matched whole rather than parsed.
            return rule in self.flags
        if kind == 'runs':
            return game.char.runs >= int(value)
        if kind == 'diss':
            return game.char.dissonance >= int(value)
        if kind == 'credits':
            return game.char.credits >= int(value)
        if kind == 'shift':
            return game.city.shift >= int(value)
        if kind == 'heat':
            return game.alias.hottest[1] >= int(value)
        if kind == 'rep':
            faction, _, amount = value.partition(':')
            return game.alias.reputation(faction) >= int(amount)
        if kind == 'origin':
            return game.char.origin == value
        if kind == 'trait':
            return value in game.char.traits
        if kind == 'debt':
            return game.debt.amount >= int(value)
        return False

    def available(self, game) -> list[tuple[str, thread_content.Stage]]:
        """Every stage that has become reachable and has not been seen.

        Returns them in thread order rather than in any narrative order,
        because there is no narrative order: this is the whole point of the
        design and the writing is built to survive it.
        """
        out = []
        for thread in thread_content.THREADS:
            done = self.reached.get(thread.key, [])
            for stage in thread.stages:
                if stage.key in done:
                    continue
                if not all(self.satisfied(r, game) for r in stage.requires):
                    continue
                if stage.any_of and not any(
                        self.satisfied(r, game) for r in stage.any_of):
                    continue
                out.append((thread.key, stage))
        return out

    def reach(self, thread_key: str, stage: thread_content.Stage) -> None:
        """Mark a stage as seen and apply its flags."""
        self.reached.setdefault(thread_key, []).append(stage.key)
        self.flags.update(stage.sets)
        if stage.choices:
            self.pending.append(f'{thread_key}.{stage.key}')

    def resolve(self, thread_key: str, stage_key: str,
                choice: thread_content.Choice) -> None:
        self.flags.update(choice.sets)
        tag = f'{thread_key}.{stage_key}'
        if tag in self.pending:
            self.pending.remove(tag)

    # ------------------------------------------------------------------

    def open_choice(self):
        """The choice currently waiting, if any, as (thread, stage)."""
        if not self.pending:
            return None
        thread_key, _, stage_key = self.pending[0].partition('.')
        thread = thread_content.BY_KEY.get(thread_key)
        if thread is None:
            self.pending.pop(0)
            return None
        stage = next((s for s in thread.stages if s.key == stage_key), None)
        if stage is None:
            self.pending.pop(0)
            return None
        return thread, stage

    def active_threads(self) -> list[thread_content.Thread]:
        return [thread_content.BY_KEY[k] for k in self.reached
                if k in thread_content.BY_KEY]

    def headline(self, thread_key: str) -> str:
        """The most recent stage headline for a thread."""
        done = self.reached.get(thread_key, [])
        if not done:
            return ''
        thread = thread_content.BY_KEY[thread_key]
        for stage in reversed(thread.stages):
            if stage.key in done:
                return stage.headline
        return ''

    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {'flags': sorted(self.flags),
                'reached': {k: list(v) for k, v in self.reached.items()},
                'pending': list(self.pending),
                'met': sorted(self.met),
                'owed': {k: v for k, v in self.owed.items() if v},
                'asked': dict(self.asked)}

    @classmethod
    def from_dict(cls, d: dict) -> Story:
        return cls(flags=set(d.get('flags') or ()),
                   reached={k: list(v)
                            for k, v in (d.get('reached') or {}).items()},
                   pending=list(d.get('pending') or []),
                   met=set(d.get('met') or ()),
                   owed={k: int(v) for k, v in (d.get('owed') or {}).items()},
                   asked={k: int(v) for k, v in (d.get('asked') or {}).items()})


# --------------------------------------------------------------------------
# running into people
# --------------------------------------------------------------------------


def present(game, story: Story) -> list[npc_content.Npc]:
    """Everybody who can be found in the district the player is standing in."""
    district = game.city.district
    out = []
    for npc in npc_content.in_district(district.key, district.services):
        if not npc_content.meets(npc, game.char, game.alias, game.char.runs):
            continue
        # The story half of `requires`: plain flags and `not:` rules, which
        # `meets` cannot see because the content layer has no story. This is
        # how somebody stops being in the city once they are dead. D51.
        if not all(story.satisfied(rule, game) for rule in npc.requires
                   if rule.partition(':')[0] not in npc_content.NUMERIC_RULES):
            continue
        out.append(npc)
    return out


# --------------------------------------------------------------------------
# D51: decisions the streets read
# --------------------------------------------------------------------------

#: What a decision does to how safe one faction's streets are for you, as
#: (flag, faction, multiplier on arrival risk). Read by
#: `fallout.arrival_risk`, so travel and legwork feel it alike. Declared as
#: data so `validate.py` can see that the flag is set by a choice and the
#: faction exists, which is the whole of D51: a choice is content that claims
#: a consequence, and a claim the engine never reads is a lie that validates.
STREET_RIDERS: tuple[tuple[str, str, float], ...] = (
    # The Sixes consider you theirs, and mean it, in the Ninth.
    ('theirs_owned', 'sixes', 0.5),
    # The file is closed, formally, with a reason that holds up. So far.
    ('file_closed', 'nightwatch', 0.5),
    # Kagawa have decided about you, and what they decided was "fine".
    ('laptop_returned', 'kagawa', 0.6),
)


def street_rider(flags, faction: str) -> float:
    """Multiplier on a faction's arrival risk, from what you have decided."""
    out = 1.0
    for flag, who, mult in STREET_RIDERS:
        if who == faction and flag in flags:
            out *= mult
    return out
