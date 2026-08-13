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
from ..content import hardware, programs


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
            if scale >= 1.0:
                parts.append(comp.effects)
                parts.append(comp.penalty)
                continue
            parts.append(_scaled(comp.effects, scale))
            # Penalties do not degrade. A cracked wide bank still draws power.
            parts.append(comp.penalty)
        # Programs contribute their passive effects only while loaded.
        for key in self.loaded:
            prog = programs.BY_KEY.get(key)
            if prog and prog.effects:
                parts.append(prog.effects)
        return fx.merge(*parts)

    # -- budgets -----------------------------------------------------------

    @property
    def memory(self) -> int:
        """Total program memory. Never below zero, because a masking layer
        that eats slots must not be able to produce a negative budget."""
        return max(0, int(self._component_effects().get('memory', 0)))

    @property
    def memory_used(self) -> int:
        return sum(programs.BY_KEY[k].memory for k in self.loaded
                   if k in programs.BY_KEY)

    @property
    def memory_free(self) -> int:
        return self.memory - self.memory_used

    @property
    def heat(self) -> int:
        """Standing thermal output of the fitted components."""
        return sum(c.heat for _, c in self.components())

    @property
    def heat_cap(self) -> int:
        return int(self._component_effects().get('heat_cap', 0))

    @property
    def heat_headroom(self) -> int:
        """What overclocking has to spend. The Hardware skill's whole point."""
        return self.heat_cap - self.heat

    def _component_effects(self) -> dict:
        """Components only. Memory and cooling must not depend on what is
        loaded, or loading a program could change how much room there is for
        programs, which is the kind of loop that eats an afternoon."""
        parts: list[dict] = []
        for slot, comp in self.components():
            scale = (3 - self.damage.get(slot, 0)) / 3
            parts.append(comp.effects if scale >= 1.0
                         else _scaled(comp.effects, scale))
            parts.append(comp.penalty)
        return fx.merge(*parts)

    # -- programs ----------------------------------------------------------

    def can_load(self, program_key: str) -> tuple[bool, str]:
        prog = programs.BY_KEY.get(program_key)
        if prog is None:
            return False, f'no such program: {program_key}'
        # Duplicates are deliberately legal: two Crowbars means a spare when
        # one gets burned. The only question here is capacity.
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
        return {'parts': dict(self.parts), 'loaded': list(self.loaded),
                'damage': {k: v for k, v in self.damage.items() if v}}

    @classmethod
    def from_dict(cls, d: dict) -> Deck:
        return cls(parts=dict(d.get('parts') or {}),
                   loaded=list(d.get('loaded') or []),
                   damage={k: int(v) for k, v in (d.get('damage') or {}).items()})


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
