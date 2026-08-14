"""The character: attributes, skills, chrome, and the deck they drive.

Everything the rest of the game asks about a build comes through here, and
every one of those questions is answered as `base + modifiers` computed on
demand rather than cached. Caching was tempting and would have been wrong: a
build changes when chrome is installed, when a component is damaged mid-run,
and when a program is loaded, and a stale cached Tempo is the kind of bug that
presents as "the game feels wrong" rather than as a traceback.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..content import appearance, attributes as attrs
from ..content import cyberware, dissonance as drift
from ..content import effects as fx, icons, origins, programs, skills
from ..content import traits as trait_content
from .deck import Deck


@dataclass(slots=True)
class Character:
    #: The name on nothing official. Aliases (D13) are separate and live in
    #: `model/identity.py`; this is what the player calls themselves.
    handle: str = 'unnamed'
    origin: str = 'gutter'

    base_attrs: dict[str, int] = field(default_factory=dict)
    base_skills: dict[str, int] = field(default_factory=dict)

    installed: list[str] = field(default_factory=list)
    deck: Deck = field(default_factory=Deck)
    #: Programs owned but not necessarily loaded. The loadout decision of D12
    #: only exists because these two lists are different.
    library: list[str] = field(default_factory=list)

    #: The shape you wear in cyberspace. The cheapest customisation axis to
    #: change, and therefore the tactical one: carry several, wear the right
    #: one for the job.
    icon: str = icons.DEFAULT
    icons: list[str] = field(default_factory=lambda: [icons.DEFAULT])

    #: What you are like. Permanent, chosen from a pool much larger than the
    #: number of slots, which is what stops two characters converging.
    traits: list[str] = field(default_factory=list)

    #: What you look like: slot -> feature key. Four of these are set at
    #: creation and only a clinic changes them; four are yours to change.
    look: dict[str, str] = field(default_factory=appearance.default)
    #: Marks the work has left on you. You do not choose these and they do not
    #: come off, which is the point of them.
    marks: list[str] = field(default_factory=list)

    credits: int = 0
    xp: int = 0
    #: Unspent attribute points. Creation grants a budget and spends it through
    #: the same `boost` command used later, so there is no separate creation
    #: minigame to learn and then never use again.
    points: int = 0
    dissonance: int = 0

    #: Highest Dissonance band whose passage has already been printed. The
    #: drift only gets told to you once per band, however you got there.
    drift_seen: int = 0
    #: Damage carried out of a run. Heals with rest, never spontaneously.
    hurt: int = 0
    runs: int = 0

    # ------------------------------------------------------------------
    # creation
    # ------------------------------------------------------------------

    @classmethod
    def from_origin(cls, origin_key: str, handle: str) -> Character:
        origin = origins.BY_KEY[origin_key]
        base = {k: origins.BASE_ATTR + origin.attrs.get(k, 0)
                for k in attrs.ATTR_KEYS}
        char = cls(
            handle=handle,
            origin=origin_key,
            base_attrs=base,
            base_skills={k: origin.skills.get(k, 0) for k in skills.SKILL_KEYS},
            installed=list(origin.cyberware),
            deck=Deck.from_preset(origin.deck),
            library=list(origin.programs),
            icon=origin.icon,
            icons=sorted({icons.DEFAULT, origin.icon}),
            credits=origin.credits,
            look={**appearance.default(), **origin.look},
        )
        char.dissonance = sum(cyberware.BY_KEY[w].dissonance
                              for w in char.installed if w in cyberware.BY_KEY)
        if origin_key == 'chromed':
            char.dissonance = max(char.dissonance,
                                  origins.CHROMED_START_DISSONANCE)
        # Load what fits, strongest first, so a new character can run at once
        # rather than having to discover the `load` command to do anything.
        for key in sorted(char.library,
                          key=lambda k: -programs.BY_KEY[k].rating
                          if k in programs.BY_KEY else 0):
            ok, _ = char.deck.can_load(key)
            if ok:
                char.deck.load(key)
        return char

    # ------------------------------------------------------------------
    # effects
    # ------------------------------------------------------------------

    def effects(self) -> dict:
        """Everything modifying this character right now.

        Order does not matter: additive keys sum and multiplicative keys
        multiply, both commutatively, which is exactly why `fx` splits them.
        """
        parts = [self.deck.effects()]
        for key in self.installed:
            ware = cyberware.BY_KEY.get(key)
            if ware:
                parts.append(ware.effects)
                parts.append(ware.penalty)
        origin = origins.BY_KEY.get(self.origin)
        if origin and origin.effects:
            parts.append(origin.effects)
        for key in self.traits:
            trait = trait_content.BY_KEY.get(key)
            if trait:
                parts.append(trait.effects)
                parts.append(trait.penalty)
        icon = icons.BY_KEY.get(self.icon)
        if icon:
            parts.append(icon.effects)
            parts.append(icon.penalty)
            # An icon further from a human shape than your drift can carry
            # fights you the whole time you wear it.
            parts.append(icons.coherence_penalty(self.icon, self.dissonance))
        parts.append(appearance.effects(self.look, self.marks))
        return fx.merge(*parts)

    def mult(self, key: str) -> float:
        """A multiplicative modifier, defaulting to 1.0."""
        return float(self.effects().get(key, 1.0))

    def bonus(self, key: str) -> int:
        """An additive modifier, defaulting to 0."""
        return int(round(self.effects().get(key, 0)))

    # ------------------------------------------------------------------
    # attributes and skills
    # ------------------------------------------------------------------

    def attr(self, key: str) -> int:
        """Effective attribute, clamped to the legal range."""
        raw = self.base_attrs.get(key, attrs.ATTR_MIN)
        raw += int(round(self.effects().get(key, 0)))
        return max(attrs.ATTR_MIN, min(attrs.ATTR_MAX + 3, raw))

    def skill(self, key: str) -> int:
        """Effective skill rank. Chrome can push a rank past 5; techniques
        cannot be granted that way, which is checked by `has_technique`."""
        raw = self.base_skills.get(key, 0)
        raw += int(round(self.effects().get(f'skill_{key}', 0)))
        return max(0, min(skills.MAX_RANK + 2, raw))

    def has_technique(self, technique_key: str) -> bool:
        """Techniques come from trained rank only.

        Deliberate: an implant that grants `+1 Intrusion` should make you
        better at cracking, not teach you to Pivot. Otherwise the technique
        system, which is the whole point of D10's skill design, becomes
        purchasable with money.
        """
        tech = skills.TECHNIQUES.get(technique_key)
        if tech is None:
            return False
        owner = next((s for s in skills.SKILLS
                      if any(t.key == technique_key for t in s.techniques)), None)
        if owner is None:
            return False
        return self.base_skills.get(owner.key, 0) >= tech.rank

    def techniques(self) -> list[skills.Technique]:
        return [t for s in skills.SKILLS for t in s.techniques
                if self.base_skills.get(s.key, 0) >= t.rank]

    # ------------------------------------------------------------------
    # derived
    # ------------------------------------------------------------------

    @property
    def bandwidth(self) -> int:
        return attrs.bandwidth(self.attr('grit')) + self.bonus('bandwidth')

    @property
    def bandwidth_used(self) -> int:
        return sum(cyberware.BY_KEY[k].bandwidth for k in self.installed
                   if k in cyberware.BY_KEY)

    @property
    def bandwidth_free(self) -> int:
        return self.bandwidth - self.bandwidth_used

    @property
    def integrity_max(self) -> int:
        return attrs.integrity(self.attr('grit')) + self.bonus('integrity')

    @property
    def integrity(self) -> int:
        return max(0, self.integrity_max - self.hurt)

    @property
    def focus(self) -> int:
        return attrs.focus(self.attr('logic')) + self.bonus('focus')

    @property
    def tempo(self) -> int:
        return min(4, attrs.tempo(self.attr('reflex')) + self.bonus('tempo'))

    @property
    def composure(self) -> int:
        return (attrs.composure(self.attr('nerve'), self.dissonance)
                + self.bonus('composure'))

    @property
    def dissonance_band(self) -> tuple[int, str, str]:
        return cyberware.band(self.dissonance)

    @property
    def memorable(self) -> int:
        """How easily somebody could describe you afterwards.

        Two-sided on purpose: it earns reputation and it earns heat. Chrome
        puts a floor under it that no amount of dressing down gets below.
        """
        return appearance.score(self.look, self.marks, self.dissonance)[0]

    @property
    def presence(self) -> int:
        """How much room you take up in a conversation."""
        return appearance.score(self.look, self.marks, self.dissonance)[1]

    @property
    def memorable_band(self) -> tuple[str, str]:
        return appearance.band(self.memorable)

    def mark(self, key: str) -> appearance.Feature | None:
        """Take an earned mark. Returns it if it is new, None if already worn.

        Called by the engine when the thing that causes a mark happens, so the
        list is a record of what has actually been done to this character
        rather than anything they picked.
        """
        feature = appearance.EARNED_BY_KEY.get(key)
        if feature is None or key in self.marks:
            return None
        self.marks.append(key)
        return feature

    def new_passages(self) -> list:
        """Drift passages not yet shown, and mark them shown.

        Called after anything that moves Dissonance. Returning a list rather
        than one handles the case where a single expensive implant carries
        somebody through two bands at once, which would otherwise silently
        lose the only writing a band ever gets.
        """
        due = [p for p in drift.PASSAGES
               if self.drift_seen < p.band <= self.dissonance]
        if due:
            self.drift_seen = max(p.band for p in due)
        # Submerged is the point at which it stops being something you feel
        # and starts being something other people can see.
        if self.dissonance >= drift.PASSAGES[1].band:
            self.mark('drift_pallor')
        return due

    @property
    def chrome_dissonance(self) -> int:
        """Dissonance the installed hardware alone accounts for.

        Grounding cannot take you below this: you can walk back what the work
        did to you, not the hardware while it is still in you.
        """
        return sum(cyberware.BY_KEY[k].dissonance for k in self.installed
                   if k in cyberware.BY_KEY)

    # ------------------------------------------------------------------
    # chrome
    # ------------------------------------------------------------------

    def can_install(self, ware_key: str) -> tuple[bool, str]:
        ware = cyberware.BY_KEY.get(ware_key)
        if ware is None:
            return False, f'no such cyberware: {ware_key}'
        if ware_key in self.installed:
            return False, f'{ware.name} is already installed'
        if ware.bandwidth > self.bandwidth_free:
            return False, (f'{ware.name} needs {ware.bandwidth} bandwidth, '
                           f'{self.bandwidth_free} free')
        used = sum(1 for k in self.installed
                   if k in cyberware.BY_KEY
                   and cyberware.BY_KEY[k].location == ware.location)
        if used >= cyberware.SLOTS[ware.location]:
            return False, (f'no {ware.location} slot free '
                           f'({used}/{cyberware.SLOTS[ware.location]} used)')
        return True, ''

    def install(self, ware_key: str) -> None:
        ok, why = self.can_install(ware_key)
        if not ok:
            raise ValueError(why)
        self.installed.append(ware_key)
        self.dissonance += cyberware.BY_KEY[ware_key].dissonance

    def uninstall(self, ware_key: str) -> None:
        """Chrome comes out. Dissonance does not.

        This is the sharp edge of D11 and it is intentional: the drift is a
        record of what you have done to yourself, not a status effect keyed to
        current equipment. Removing the hardware removes the benefit and leaves
        the mark, which is what makes a chrome-heavy build a commitment rather
        than a rental.
        """
        if ware_key not in self.installed:
            raise ValueError(f'{ware_key} is not installed')
        self.installed.remove(ware_key)

    def slots_used(self, location: str) -> int:
        return sum(1 for k in self.installed
                   if k in cyberware.BY_KEY
                   and cyberware.BY_KEY[k].location == location)

    def riders(self) -> set[str]:
        """Rider keys currently active. The run layer special-cases these."""
        out = {cyberware.BY_KEY[k].rider for k in self.installed
               if k in cyberware.BY_KEY and cyberware.BY_KEY[k].rider}
        icon = icons.BY_KEY.get(self.icon)
        if icon and icon.rider:
            out.add(icon.rider)
        origin = origins.BY_KEY.get(self.origin)
        if origin and origin.rider:
            out.add(origin.rider)
        for key in self.traits:
            trait = trait_content.BY_KEY.get(key)
            if trait and trait.rider:
                out.add(trait.rider)
        return out

    # ------------------------------------------------------------------
    # traits
    # ------------------------------------------------------------------

    @property
    def trait_slots(self) -> int:
        """How many traits this character is entitled to right now."""
        return (trait_content.CREATION_PICKS
                + trait_content.earned(self.runs))

    @property
    def trait_picks(self) -> int:
        """Unspent trait slots."""
        return max(0, self.trait_slots - len(self.traits))

    def can_take_trait(self, key: str) -> tuple[bool, str]:
        trait = trait_content.BY_KEY.get(key)
        if trait is None:
            return False, f'no such trait: {key}'
        if key in self.traits:
            return False, f'you are already {trait.name.lower()}'
        if not self.trait_picks:
            return False, (f'no slots left. The next one comes at '
                           f'{(trait_content.earned(self.runs) + 1) * trait_content.EARN_EVERY} '
                           f'runs.')
        if trait not in trait_content.available(self.traits, self):
            clash = next((self.traits[i] for i, k in enumerate(self.traits)
                          if k in trait.excludes
                          or key in trait_content.BY_KEY[k].excludes), None)
            if clash:
                return False, (f'{trait.name} does not go with '
                               f'{trait_content.BY_KEY[clash].name}.')
            return False, f'{trait.name} is not open to you.'
        return True, ''

    def take_trait(self, key: str) -> trait_content.Trait:
        ok, why = self.can_take_trait(key)
        if not ok:
            raise ValueError(why)
        self.traits.append(key)
        return trait_content.BY_KEY[key]

    @property
    def icon_data(self) -> icons.Icon:
        return icons.BY_KEY.get(self.icon) or icons.BY_KEY[icons.DEFAULT]

    @property
    def coherence_gap(self) -> int:
        """How far short of holding the current icon you are. Zero is a fit."""
        return icons.coherence_gap(self.icon, self.dissonance)

    # ------------------------------------------------------------------
    # progression
    # ------------------------------------------------------------------

    def can_boost(self, attr_key: str) -> tuple[bool, str]:
        if attr_key not in attrs.ATTR_KEYS:
            return False, f'no such attribute: {attr_key}'
        if not self.points:
            return False, 'no attribute points left'
        if self.base_attrs.get(attr_key, 0) >= attrs.ATTR_MAX:
            return False, f'{attr_key} is already at {attrs.ATTR_MAX}'
        return True, ''

    def boost(self, attr_key: str) -> int:
        ok, why = self.can_boost(attr_key)
        if not ok:
            raise ValueError(why)
        self.points -= 1
        self.base_attrs[attr_key] = self.base_attrs.get(attr_key, 0) + 1
        return self.base_attrs[attr_key]

    def can_train(self, skill_key: str) -> tuple[bool, str]:
        if skill_key not in skills.BY_KEY:
            return False, f'no such skill: {skill_key}'
        rank = self.base_skills.get(skill_key, 0)
        if rank >= skills.MAX_RANK:
            return False, f'{skills.BY_KEY[skill_key].name} is already at rank 5'
        cost = skills.RANK_COST[rank + 1]
        if cost > self.xp:
            return False, (f'rank {rank + 1} costs {cost} experience, '
                           f'you have {self.xp}')
        return True, ''

    def train(self, skill_key: str) -> skills.Technique | None:
        """Buy the next rank. Returns the technique unlocked, if any."""
        ok, why = self.can_train(skill_key)
        if not ok:
            raise ValueError(why)
        rank = self.base_skills.get(skill_key, 0) + 1
        self.xp -= skills.RANK_COST[rank]
        self.base_skills[skill_key] = rank
        return skills.BY_KEY[skill_key].technique_at(rank)

    @property
    def origin_data(self) -> origins.Origin:
        return origins.BY_KEY[self.origin]

    # ------------------------------------------------------------------
    # persistence
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            'handle': self.handle,
            'origin': self.origin,
            'base_attrs': dict(self.base_attrs),
            'base_skills': {k: v for k, v in self.base_skills.items() if v},
            'installed': list(self.installed),
            'deck': self.deck.to_dict(),
            'library': list(self.library),
            'icon': self.icon,
            'icons': list(self.icons),
            'traits': list(self.traits),
            'look': dict(self.look),
            'marks': list(self.marks),
            'credits': self.credits,
            'xp': self.xp,
            'points': self.points,
            'dissonance': self.dissonance,
            'drift_seen': self.drift_seen,
            'hurt': self.hurt,
            'runs': self.runs,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Character:
        return cls(
            handle=d.get('handle', 'unnamed'),
            origin=d.get('origin', 'gutter'),
            base_attrs={k: int(d.get('base_attrs', {}).get(k, origins.BASE_ATTR))
                        for k in attrs.ATTR_KEYS},
            base_skills={k: int(d.get('base_skills', {}).get(k, 0))
                         for k in skills.SKILL_KEYS},
            installed=list(d.get('installed') or []),
            deck=Deck.from_dict(d.get('deck') or {}),
            library=list(d.get('library') or []),
            icon=d.get('icon') or icons.DEFAULT,
            icons=list(d.get('icons') or [icons.DEFAULT]),
            traits=list(d.get('traits') or []),
            look={**appearance.default(), **(d.get('look') or {})},
            marks=list(d.get('marks') or []),
            credits=int(d.get('credits', 0)),
            xp=int(d.get('xp', 0)),
            points=int(d.get('points', 0)),
            dissonance=int(d.get('dissonance', 0)),
            drift_seen=int(d.get('drift_seen', 0)),
            hurt=int(d.get('hurt', 0)),
            runs=int(d.get('runs', 0)),
        )
