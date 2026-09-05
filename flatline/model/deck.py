"""The assembled deck: components fitted, programs loaded, damage taken.

Kept separate from `Character` because the deck is the one part of a build that
is genuinely modular. It can be rebuilt between runs, damaged during them, and
in the Hardware rank 4 case swapped mid-run, and none of that should require
touching the character.

Heat is computed here rather than in the run layer because it is a property of
the assembly: the sum of what the components emit against what the cooling can
carry. The run layer adds transient heat from overclocking on top of it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..content import effects as fx
from ..content import hardware, mods as mod_content, programs


@dataclass(slots=True)
class Deck:
    #: slot -> component key. Every slot in `hardware.SLOTS` is always present.
    parts: dict[str, str] = field(default_factory=dict)
    #: Program keys currently loaded. Order is the player's; it is preserved
    #: because `load` listings read better when they stay where they were put.
    loaded: list[str] = field(default_factory=list)
    #: slot -> damage taken, 0 to 3. At 3 the component is destroyed and
    #: contributes nothing until repaired.
    damage: dict[str, int] = field(default_factory=dict)
    #: component key -> bench work done to that specific unit. Keyed by the
    #: component rather than by the slot, because the work was done to the
    #: metal: sell it and the tuning goes with it. See `content/mods.py`.
    mods: dict[str, list[str]] = field(default_factory=dict)
    #: What you call it (D62). Cosmetic, persisted, read by nothing but the
    #: screens that mention the deck.
    name: str = ''
    #: The digital pet riding the deck (D153), or {} for none. {key,
    #: name, charge}. It eats memory a program could have had, which is
    #: the whole cost of keeping one; it does nothing else to the run.
    familiar: dict = field(default_factory=dict)
    #: What the room is doing, for programs whose passives depend on it
    #: (D69). Set by the run; 'green' out in the city, where nothing is
    #: looking for you yet.
    alert: str = 'green'
    #: What the body adds to the budgets: memory and cooling from chrome,
    #: traits, origin, and icon. Set by `Character.refresh_deck`, never
    #: saved, because it is derived from the character and a stale copy of
    #: it is exactly the bug this field exists to end (D63: a Blacksite
    #: Stack sold three memory for two years and the deck never heard).
    extra: dict = field(default_factory=dict)

    # -- construction ------------------------------------------------------

    @classmethod
    def from_preset(cls, key: str) -> Deck:
        preset = hardware.PRESETS_BY_KEY[key]
        return cls(parts=dict(preset.parts))

    # -- components --------------------------------------------------------

    def component(self, slot: str) -> hardware.Component | None:
        key = self.parts.get(slot)
        return hardware.BY_KEY.get(key) if key else None

    def working(self, slot: str) -> bool:
        return self.damage.get(slot, 0) < 3

    def components(self, include_broken: bool = False):
        for slot in hardware.SLOTS:
            comp = self.component(slot)
            if comp and (include_broken or self.working(slot)):
                yield slot, comp

    def fit(self, component_key: str) -> str:
        """Install a component, returning the slot it went into."""
        comp = hardware.BY_KEY[component_key]
        self.parts[comp.slot] = comp.key
        self.damage.pop(comp.slot, None)
        return comp.slot

    # -- effects -----------------------------------------------------------

    def effects(self) -> dict:
        """Everything the assembly contributes, damage accounted for.

        A damaged component degrades rather than failing outright: at damage 1
        and 2 its effects are scaled down, and only at 3 does it stop counting.
        A binary would make one unlucky tick swing a run further than any
        decision the player made.
        """
        parts: list[dict] = []
        for slot, comp in self.components():
            scale = (3 - self.damage.get(slot, 0)) / 3
            worked = mod_content.effects(self.mods.get(comp.key, ()))
            if scale >= 1.0:
                parts.append(comp.effects)
                parts.append(comp.penalty)
                parts.append(worked)
                continue
            parts.append(_scaled(comp.effects, scale))
            # Penalties do not degrade. A cracked wide bank still draws power,
            # and neither does bench work: what somebody cut off it is still
            # off it.
            parts.append(comp.penalty)
            parts.append(worked)
        # Programs contribute their passive effects only while loaded, and
        # only the strongest of each category (D63 c). Before this every
        # loaded armour multiplied into every other: six of them were a
        # damage reduction of 0.07, and Mirrorbox's note about stacking
        # poorly with other masks was a wish. Now it is the rule: two masks
        # are not twice the mask, and the second slot is a second slot.
        for prog in self.passives(self.alert):
            parts.append(prog.effects)
        return fx.merge(*parts)

    def passives(self, alert: str = 'green') -> list:
        """The one program per category whose passive effects count: the
        highest rating, ties to the first loaded."""
        best: dict[str, programs.Program] = {}
        for key in self.loaded:
            prog = programs.BY_KEY.get(key)
            if prog is None or not prog.effects:
                continue
            if (prog.rider == 'understair_fails'
                    and alert not in ('green', 'amber')):
                # A backup agent is a plausible thing to be right up until
                # somebody is checking the backup schedule (D69).
                continue
            have = best.get(prog.category)
            if have is None or prog.rating > have.rating:
                best[prog.category] = prog
        return list(best.values())

    def riders(self) -> set[str]:
        """Program riders active while loaded (D63 c)."""
        return {programs.BY_KEY[k].rider for k in self.loaded
                if k in programs.BY_KEY and programs.BY_KEY[k].rider}

    # -- budgets -----------------------------------------------------------

    @property
    def memory(self) -> int:
        """Total program memory. Never below zero, because a masking layer
        that eats slots must not be able to produce a negative budget.

        Components, the bench work done to them, and what the body adds.
        Programs never count: loading one must not change how much room
        there is for programs."""
        return max(0, int(self._component_effects().get('memory', 0)
                          + self.extra.get('memory', 0)))

    @property
    def memory_used(self) -> int:
        used = sum(programs.BY_KEY[k].memory for k in self.loaded
                   if k in programs.BY_KEY)
        if self.familiar:
            from ..content import pets as pet_content
            fam = pet_content.FAMILIAR_BY_KEY.get(self.familiar.get('key', ''))
            if fam is not None:
                used += fam.memory
        return used

    @property
    def memory_free(self) -> int:
        return self.memory - self.memory_used

    @property
    def heat(self) -> int:
        """Standing thermal output of the fitted components."""
        return sum(c.heat for _, c in self.components())

    @property
    def heat_cap(self) -> int:
        return max(0, int(self._component_effects().get('heat_cap', 0)
                          + self.extra.get('heat_cap', 0)))

    @property
    def heat_headroom(self) -> int:
        """What overclocking has to spend. The Hardware skill's whole point."""
        return self.heat_cap - self.heat

    def _component_effects(self) -> dict:
        """Components and their bench work only. Memory and cooling must not
        depend on what is loaded, or loading a program could change how much
        room there is for programs, which is the kind of loop that eats an
        afternoon. Mods count: `widened` is two memory and was, until D63,
        two memory the budget never saw."""
        parts: list[dict] = []
        for slot, comp in self.components():
            scale = (3 - self.damage.get(slot, 0)) / 3
            parts.append(comp.effects if scale >= 1.0
                         else _scaled(comp.effects, scale))
            parts.append(comp.penalty)
            parts.append(mod_content.effects(self.mods.get(comp.key, ())))
        return fx.merge(*parts)

    # -- programs ----------------------------------------------------------

    def can_load(self, program_key: str) -> tuple[bool, str]:
        prog = programs.BY_KEY.get(program_key)
        if prog is None:
            return False, f'no such program: {program_key}'
        # Duplicates are deliberately legal: a Threadpuller runs the second
        # copy as a second thread, and an armour program that has taken all
        # it can is gone, so a spare is a spare. The only question here is
        # capacity.
        if prog.memory > self.memory_free:
            return False, (f'{prog.name} needs {prog.memory} memory, '
                           f'{self.memory_free} free')
        return True, ''

    def load(self, program_key: str) -> None:
        ok, why = self.can_load(program_key)
        if not ok:
            raise ValueError(why)
        self.loaded.append(program_key)

    def unload(self, program_key: str) -> bool:
        if program_key in self.loaded:
            self.loaded.remove(program_key)
            return True
        return False

    def has_category(self, category: str) -> bool:
        return any(programs.BY_KEY[k].category == category
                   for k in self.loaded if k in programs.BY_KEY)

    # -- damage ------------------------------------------------------------

    def hurt(self, slot: str, amount: int = 1) -> int:
        """Damage a component. Returns the new damage level."""
        level = min(3, self.damage.get(slot, 0) + amount)
        self.damage[slot] = level
        return level

    def repair_cost(self, mult: float = 1.0) -> int:
        """What it costs to bring everything back to zero damage.

        `mult` is the character's `repair_mult`, which is how the Salvager and
        Company Hardware passives become real rather than prose.
        """
        total = 0
        for slot in hardware.SLOTS:
            level = self.damage.get(slot, 0)
            comp = self.component(slot)
            if level and comp:
                # A destroyed component costs most of a new one; a scratched
                # one is cheap. The curve is steep so that letting damage
                # accumulate is a real mistake rather than a rounding error.
                total += int(comp.price * (0.12, 0.30, 0.65)[level - 1])
        return max(0, int(round(total * mult)))

    def repair(self, slot: str | None = None) -> None:
        if slot is None:
            self.damage.clear()
        else:
            self.damage.pop(slot, None)

    # -- persistence -------------------------------------------------------

    def to_dict(self) -> dict:
        out = {'parts': dict(self.parts), 'loaded': list(self.loaded),
               'damage': {k: v for k, v in self.damage.items() if v},
               'mods': {k: list(v) for k, v in self.mods.items() if v}}
        if self.familiar:
            out['familiar'] = dict(self.familiar)
        if self.name:
            out['name'] = self.name
        return out

    @classmethod
    def from_dict(cls, d: dict) -> Deck:
        return cls(parts=dict(d.get('parts') or {}),
                   loaded=list(d.get('loaded') or []),
                   familiar=dict(d.get('familiar') or {}),
                   damage={k: int(v) for k, v in (d.get('damage') or {}).items()},
                   mods={k: [m for m in (v or ())
                             if m in mod_content.BY_KEY]
                         for k, v in (d.get('mods') or {}).items()
                         if k in hardware.BY_KEY},
                   name=str(d.get('name') or '')[:32])


def _scaled(effects: dict, scale: float) -> dict:
    """Degrade an effects dict toward neutral.

    Additive keys scale toward zero, multiplicative keys toward 1.0. Getting
    this backwards for one key class is how a damaged component ends up better
    than an intact one.
    """
    out: dict[str, float] = {}
    for k, v in effects.items():
        if k in fx.MULTIPLICATIVE:
            out[k] = 1.0 + (v - 1.0) * scale
        else:
            out[k] = v * scale
    return out
