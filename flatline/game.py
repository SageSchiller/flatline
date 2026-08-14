"""The whole persistent state in one object, and its trip to and from disk.

`Game` is what a save file is. It owns the character, the city, the identity
stack, and the RNG, and it is the only thing `save.py` ever serialises.

The RNG travels with the save (D3): a loaded game continues the same world it
was in rather than a statistically similar one. That is the difference between
determinism as a testing convenience and determinism as a property the player
can rely on.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import save as save_mod
from .model.character import Character
from .model.identity import Alias, generate_name
from .rng import Rng, random_seed
from .script import Script
from .world.debt import Debt
from .world.story import Story
from .world.city import City


@dataclass(slots=True)
class Game:
    character: Character
    city: City
    rng: Rng
    #: Every identity this character has used, newest last. Burned ones are
    #: kept rather than deleted, because the history is worth reading and
    #: because a burned name still exists in the world's memory.
    aliases: list = field(default_factory=list)
    #: Saved scripts by name. Persisted because a script library is a build
    #: investment, not session scratch.
    scripts: dict = field(default_factory=dict)
    #: What you owe, and to whom. At most one at a time.
    debt: Debt = field(default_factory=Debt)
    #: Who you have met, what you know, and what you decided.
    story: Story = field(default_factory=Story)
    #: Total credits earned across the character's life, for the epitaph.
    earned: int = 0
    #: Set when the character is dead. A flatlined save is readable, not
    #: playable, so the player can look at what happened.
    over: str = ''

    # ------------------------------------------------------------------

    @property
    def alias(self) -> Alias:
        return self.aliases[-1]

    @property
    def char(self) -> Character:
        return self.character

    # ------------------------------------------------------------------

    @classmethod
    def new(cls, character: Character, seed: int | None = None) -> Game:
        rng = Rng(seed if seed is not None else random_seed())
        alias = Alias(name=generate_name(rng('names')), established=0)
        origin = character.origin_data
        for faction, value in origin.standing.items():
            alias.rep[faction] = value
        game = cls(character=character, city=City(), rng=rng, aliases=[alias])
        game.city = City.new(rng, alias, character)
        # The ex-cop starts wanted. The complication is not decorative.
        if character.origin == 'expolice':
            game.city.bounties['nightwatch'] = 25
            alias.add_heat('nightwatch', 30)
        # Nor are the debts. Both of these have said "it is compounding" in
        # their complication text since the beginning; now it does.
        if character.origin == 'academic':
            game.debt = Debt(
                amount=9400, lender='sixes', opened=0,
                note='The department did not lend you the deck. Somebody in '
                     'the Ninth did, against the department\'s name, and the '
                     'department has since stopped answering.')
        elif character.origin == 'bonded':
            game.debt = Debt(
                amount=26000, lender='kagawa', opened=0,
                note='A buyout figure, calculated by Kagawa, for a contract '
                     'Kagawa wrote. It is not a debt in any sense a court '
                     'would recognise. It is the price of the rest of your '
                     'life and they will take instalments.')
        return game

    def new_alias(self, name: str = '') -> Alias:
        """Burn the current name and take another, per D13."""
        self.alias.burned = True
        fresh = Alias(name=name or generate_name(self.rng('names')),
                      established=self.city.shift)
        self.aliases.append(fresh)
        return fresh

    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            'character': self.character.to_dict(),
            'city': self.city.to_dict(),
            'rng': self.rng.getstate(),
            'aliases': [a.to_dict() for a in self.aliases],
            'scripts': {k: v.to_dict() for k, v in self.scripts.items()},
            'debt': self.debt.to_dict(),
            'story': self.story.to_dict(),
            'earned': self.earned,
            'over': self.over,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Game:
        aliases = [Alias.from_dict(a) for a in (d.get('aliases') or [])]
        if not aliases:
            aliases = [Alias(name='nobody')]
        return cls(
            character=Character.from_dict(d.get('character') or {}),
            city=City.from_dict(d.get('city') or {}),
            rng=Rng.fromstate(d.get('rng') or {'seed': 0}),
            aliases=aliases,
            scripts={k: Script.from_dict(v)
                     for k, v in (d.get('scripts') or {}).items()},
            debt=Debt.from_dict(d.get('debt') or {}),
            story=Story.from_dict(d.get('story') or {}),
            earned=int(d.get('earned', 0)),
            over=d.get('over', ''),
        )

    # ------------------------------------------------------------------

    def save(self, slot: str = 'default'):
        return save_mod.write(self.to_dict(), slot)

    @classmethod
    def load(cls, slot: str = 'default') -> Game:
        return cls.from_dict(save_mod.read(slot))
