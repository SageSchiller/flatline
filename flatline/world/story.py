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
    #: When things happened, as shifts: `thread:<key>` for the last stage
    #: of a thread reached, `met:<npc>` for a meeting (D91). Read by
    #: `Stage.after`, so a scene that says "the second time" waits for a
    #: second time.
    when: dict = field(default_factory=dict)

    # ------------------------------------------------------------------

    def has(self, flag: str) -> bool:
        return flag in self.flags

    def meet(self, key: str, shift: int | None = None) -> bool:
        """Record a first meeting. True if it was in fact the first."""
        if key in self.met:
            return False
        self.met.add(key)
        self.flags.add(f'met:{key}')
        if shift is not None:
            self.when[f'met:{key}'] = int(shift)
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
        if kind in ('did', 'bond', 'found', 'street', 'warned', 'heard',
                    'asked', 'visited', 'fought', 'job'):
            # A posting finished, a runner decided about you, or a relic
            # found (D63 e). The flag carries its own colons, so it is
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
        if kind == 'skill':
            # A trained rank (D140), so a story can want somebody who can
            # actually do the thing it is about to ask for.
            key, _, rank = value.partition(':')
            return game.char.skill(key) >= int(rank or 1)
        if kind == 'places':
            # How many places you have stood in (D147), so the explorer,
            # who had material and no story, has a gate that reads the
            # walking. A count, not a named place: `visited:<key>` is the
            # flag, `places:<n>` is how many of them there are.
            return sum(1 for f in self.flags
                       if f.startswith('visited:')) >= int(value)
        if kind == 'finds':
            # How many one-of-a-kind things you have found (D147). The
            # finds were kept back for somebody; this is the gate on
            # having been that somebody more than once.
            return sum(1 for f in self.flags
                       if f.startswith('found:')) >= int(value)
        if kind == 'pit':
            # A name on the wall (D134): `pit:champion` is the flag the
            # house sets, and `pit:<n>` is the rung.
            if value.isdigit():
                return int(game.city.pit.get('rank', 0)) >= int(value)
            return rule in self.flags
        if kind == 'habit':
            from ..content import drugs as drug_content
            key, _, level = value.partition(':')
            return drug_content.habit(game.char.chem, key) >= int(level or 1)
        if kind == 'carrying':
            from ..content import weapons as weapon_content
            held = (weapon_content.BY_KEY.get(game.char.weapon)
                    or weapon_content.granted(game.char.installed))
            if value in ('any', ''):
                return held is not None
            if value == 'loud':
                return held is not None and held.loud
            return held is not None and held.key == value
        if kind == 'mark':
            return value in game.char.marks
        if kind == 'arranged':
            # Arrangements standing with factions (D70). World state rather
            # than a decision, so it is a rule kind and not a flag.
            return len(game.city.arrangements) >= int(value)
        return False

    def waiting_on(self, thread, game) -> str:
        """What the next scene of a thread is still short of, in words.

        The journal has always been able to say a thread is waiting on
        *you*, because a pending choice is a thing you can see. It could
        not say the other case, which is a thread waiting on the world: on
        somebody you have not met, or on a decision belonging to a
        different story. The main line ends on a scene that needs Lark
        alive, and a player who never met Lark lost the last scene of the
        game without ever learning it was there (D76).

        Names people and other threads, never flags, and never says what
        the scene is. Returns '' when there is nothing useful to say,
        which includes the common cases: the thread is finished, or the
        only thing missing is work you were going to do anyway.
        """
        done = set(self.reached.get(thread.key, ()))
        best: list[str] | None = None
        shut = False
        # A next scene the player can trigger right here and now (its only
        # unmet requirements are their own work: a topic to ask, a couple of
        # runs, the passage of a shift). When one exists, the thread is not
        # waiting on the world at all, so naming a far wall from some later
        # stage misdirects: a player reads "waiting on <other thread>" and
        # walks away from a scene that was one command off (D114).
        actionable = False
        for stage in thread.stages:
            if stage.key in done:
                continue
            here = not stage.where or stage.where == game.city.where
            unmet = [r for r in stage.requires if not self.satisfied(r, game)]
            if stage.any_of and not any(self.satisfied(r, game)
                                        for r in stage.any_of):
                # An any-of that is wholly unmet is a real wall, but it is
                # a choice of walls: naming all of them reads as a list of
                # errands. Say nothing and let the closest `requires` talk.
                unmet = unmet or []
            if not unmet:
                # Nothing missing but the place (D86). The most useful
                # thing the journal can say, because it is the one thing
                # that is only ever a walk away.
                if not here:
                    from ..content import districts
                    place = districts.BY_KEY[stage.where].name
                    named = [f'you being in {place}']
                    if best is None or len(named) < len(best):
                        best = named
                else:
                    actionable = True
                continue
            if any(_foreclosed(self, r) for r in unmet):
                shut = True
                continue
            named = _name_rules(unmet, thread.key)
            if named:
                if best is None or len(named) < len(best):
                    best = named
            elif here:
                # Unmet, but nothing a person could be named for: the work is
                # the player's and it can be done from where they stand.
                actionable = True
        if actionable:
            return ''
        if not best:
            return ('There was more of this. There is not now.'
                    if shut else '')
        if len(best) == 1:
            return f'There is more of this, and it is waiting on {best[0]}.'
        joined = ', '.join(best[:-1]) + f' and {best[-1]}'
        return f'There is more of this, and it is waiting on {joined}.'

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
                # Where it happens is where it happens (D86). Forty-two
                # scenes declare a district and, until this line, nothing
                # read it: the Notary's counter on the Row was played on a
                # Freeport dock, and a vending machine in the Ninth was
                # asked about the war from Marrow. The field was flavour
                # with a gate's name, which is this project's oldest bug.
                if stage.where and game.city.where != stage.where:
                    continue
                if not self._old_enough(thread, stage, game):
                    continue
                out.append((thread.key, stage))
        return out

    def _old_enough(self, thread, stage, game) -> bool:
        """`Stage.after` (D91): shifts since the thread's previous stage,
        or since meeting the person it requires when it is the first. A
        save from before the stamps existed has nothing to measure from
        and is not held back."""
        if not stage.after:
            return True
        if self.reached.get(thread.key):
            base = self.when.get(f'thread:{thread.key}')
        else:
            met = next((r[4:] for r in stage.requires if r.startswith('met:')),
                       None)
            base = self.when.get(f'met:{met}') if met else None
            if base is None:
                # A first stage that waits on nobody, only on something
                # another thread decided (D144): "Afterwards" opens a few
                # shifts after the offer, and it opened in the same breath,
                # because the only stamp this looked for was a meeting. The
                # stamp of the thread that set the flag is the one to
                # measure from.
                owners = _flag_owners()
                stamps = [self.when.get(f'thread:{owners[r][0]}')
                          for r in stage.requires + stage.any_of
                          if r in owners]
                stamps = [s for s in stamps if s is not None]
                base = max(stamps) if stamps else None
        if base is None:
            return True
        return game.city.shift - int(base) >= stage.after

    def waiting_elsewhere(self, game) -> list[tuple[str, str]]:
        """Scenes that would fire the moment you stood in the right
        district, as (thread key, district key). What `now` reads to say
        there is a reason to go somewhere (D86)."""
        out = []
        here = game.city.where
        for thread in thread_content.THREADS:
            done = self.reached.get(thread.key, [])
            for stage in thread.stages:
                if stage.key in done or not stage.where:
                    continue
                if stage.where == here:
                    continue
                if not all(self.satisfied(r, game) for r in stage.requires):
                    continue
                if stage.any_of and not any(
                        self.satisfied(r, game) for r in stage.any_of):
                    continue
                out.append((thread.key, stage.where))
                break
        return out

    def waiting_on_somebody_here(self, game) -> list[str]:
        """Threads whose next scene wants only a person who is standing in
        this district now, unmet. `now` turns it into `look` (D86)."""
        present = {n.key for n in present_now(game, self)}
        out = []
        for thread in thread_content.THREADS:
            done = self.reached.get(thread.key, [])
            for stage in thread.stages:
                if stage.key in done:
                    continue
                if stage.where and stage.where != game.city.where:
                    continue
                unmet = [r for r in stage.requires
                         if not self.satisfied(r, game)]
                if stage.any_of and not any(self.satisfied(r, game)
                                            for r in stage.any_of):
                    continue
                if (len(unmet) == 1 and unmet[0].startswith('met:')
                        and unmet[0][4:] in present
                        and unmet[0][4:] not in self.met):
                    out.append(thread.key)
                break
        return out

    def reach(self, thread_key: str, stage: thread_content.Stage,
              shift: int | None = None) -> None:
        """Mark a stage as seen and apply its flags."""
        self.reached.setdefault(thread_key, []).append(stage.key)
        self.flags.update(stage.sets)
        if shift is not None:
            self.when[f'thread:{thread_key}'] = int(shift)
        if stage.choices:
            self.pending.append(f'{thread_key}.{stage.key}')

    def resolve(self, thread_key: str, stage_key: str,
                choice: thread_content.Choice) -> None:
        self.flags.update(choice.sets)
        # Every decision leaves one countable mark (D142), so the record
        # can say how many times somebody put it to you and you answered.
        self.flags.add(f'chose:{thread_key}.{stage_key}')
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

    def decided(self, thread_key: str) -> list[tuple]:
        """What you chose in a thread, as (stage, choice) pairs, in order.

        Derived from the flags rather than stored, because the flags are the
        whole state of the layer (D31): the choice you took is the one whose
        flags are all set. A stage with a choice still waiting is not here;
        it is in `pending`.
        """
        out = []
        thread = thread_content.BY_KEY.get(thread_key)
        if thread is None:
            return out
        done = self.reached.get(thread_key, [])
        for stage in thread.stages:
            if stage.key not in done or not stage.choices:
                continue
            if f'{thread_key}.{stage.key}' in self.pending:
                continue
            for choice in stage.choices:
                if choice.sets and all(f in self.flags for f in choice.sets):
                    out.append((stage, choice))
                    break
        return out

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
                'asked': dict(self.asked),
                'when': {k: int(v) for k, v in self.when.items()}}

    @classmethod
    def from_dict(cls, d: dict) -> Story:
        return cls(flags=set(d.get('flags') or ()),
                   reached={k: list(v)
                            for k, v in (d.get('reached') or {}).items()},
                   pending=list(d.get('pending') or []),
                   met=set(d.get('met') or ()),
                   owed={k: int(v) for k, v in (d.get('owed') or {}).items()},
                   asked={k: int(v) for k, v in (d.get('asked') or {}).items()},
                   when={k: int(v) for k, v in (d.get('when') or {}).items()})


# --------------------------------------------------------------------------
# running into people
# --------------------------------------------------------------------------


def present_now(game, story: Story) -> list[npc_content.Npc]:
    """`present`, by another name, for the methods above that cannot
    reach a function defined below their class."""
    return present(game, story)


def present(game, story: Story,
            any_hour: bool = False) -> list[npc_content.Npc]:
    """Everybody who can be found in the district the player is standing in.

    `any_hour` ignores the clock: everybody who would be here at *some*
    hour, which is what `look` needs in order to say who is not about right
    now and when they will be (D54).
    """
    district = game.city.district
    out = []
    for npc in npc_content.in_district(district.key, district.services):
        if not npc_content.meets(npc, game.char, game.alias, game.char.runs):
            continue
        if not any_hour and not npc_content.about_now(npc, game.city.phase):
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
    # D55. The pumps run on Sixes parts, and the Ninth knows who brought the
    # ledger.
    ('pumps_sixes', 'sixes', 0.7),
    # The lobby reads your gait as furniture.
    ('reviews_self', 'kagawa', 0.7),
    # Somebody walked out of the aftercare ward, and Aoyama are well.
    ('ward_walked', 'aoyama', 1.4),
    # The evidence log is gone, and with it most of what they had on you.
    ('surplus_wiped', 'nightwatch', 0.7),
)


def street_rider(flags, faction: str) -> float:
    """Multiplier on a faction's arrival risk, from what you have decided."""
    out = 1.0
    for flag, who, mult in STREET_RIDERS:
        if who == faction and flag in flags:
            out *= mult
    return out


_OWNERS = None


def _flag_owners() -> dict:
    """Which thread and stage sets which flag, and whether a decision
    does it. Built once, from the threads."""
    global _OWNERS
    if _OWNERS is None:
        owners: dict = {}
        for thread in thread_content.THREADS:
            for stage in thread.stages:
                for flag in stage.sets:
                    owners.setdefault(flag, (thread.key, stage.key, False))
                for choice in (stage.choices or ()):
                    for flag in choice.sets:
                        owners.setdefault(flag, (thread.key, stage.key, True))
        _OWNERS = owners
    return _OWNERS


def _foreclosed(self, rule: str) -> bool:
    """Whether a flag can no longer ever be set.

    A flag that comes from a decision is gone for good once that decision
    has been made the other way: the scene does not come round again. The
    hint has to know, or a thread whose Lark is dead says it is waiting on
    Lark for the rest of the game.
    """
    owner = _flag_owners().get(rule)
    if owner is None:
        return False
    thread_key, stage_key, from_choice = owner
    if not from_choice:
        return False
    if stage_key not in self.reached.get(thread_key, ()):
        return False
    # The stage happened. If it is still waiting on the player the flag is
    # still possible; if it has been answered and the flag is not set, it
    # never will be.
    return f'{thread_key}.{stage_key}' not in self.pending


#: Rule kinds that are simply the passage of a career. A thread waiting on
#: one of these is waiting on nothing the player has to go and find.
_PATIENCE_RULES = ('runs', 'shift', 'rep', 'heat', 'diss', 'debt', 'street',
                   'arranged', 'ran')


def _name_rules(rules, own_thread: str) -> list[str]:
    """Turn unmet requirements into things a person could go and do."""
    from ..content import npcs as npc_content
    out: list[str] = []
    owners = _flag_owners()
    for rule in rules:
        kind, _, value = rule.partition(':')
        if rule.startswith('not:'):
            continue
        if kind in _PATIENCE_RULES:
            continue
        if kind == 'met':
            # Not when the person is the thread. "Lark is waiting on Lark"
            # is true and reads as a fault.
            if value == own_thread:
                continue
            who = npc_content.BY_KEY.get(value)
            if who is not None and who.name not in out:
                out.append(who.name)
            continue
        if kind == 'did':
            other, _, _stage = value.partition('.')
            if other and other != own_thread:
                other_thread = thread_content.BY_KEY.get(other)
                if other_thread is not None and other_thread.name not in out:
                    out.append(other_thread.name)
            continue
        owner = owners.get(rule)
        if owner is not None and owner[0] != own_thread:
            other_thread = thread_content.BY_KEY.get(owner[0])
            if other_thread is not None and other_thread.name not in out:
                out.append(other_thread.name)
    return out
