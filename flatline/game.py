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


#: How many runs the history keeps. A career past this is a career whose
#: first nights nobody needs by name.
HISTORY_KEEP = 200

#: What an origin's debt grows by a shift (D95). The house rate is a loan
#: taken in a back room; these are a department's and a corporation's
#: paper, slower and colder.
ORIGIN_RATE = {'academic': 0.008, 'bonded': 0.004}


def fresh_name(stream) -> str:
    """A working name nobody on this machine has run under (D95). A second
    character made in the same city was born under the first one's burned
    alias, because the name stream restarts with the seed; the meta file
    remembers every name handed out and the draw skips them."""
    try:
        meta = save_mod.read_meta()
    except Exception:  # noqa: BLE001
        meta = {}
    used = set(meta.get('names_used') or ())
    name = generate_name(stream)
    for _ in range(40):
        if name not in used:
            break
        name = generate_name(stream)
    try:
        meta['names_used'] = sorted(used | {name})[-400:]
        save_mod.write_meta(meta)
    except Exception:  # noqa: BLE001
        pass
    return name


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
    #: Every run, newest last, as the summary line the city keeps of it
    #: (D86): day, job, target, how it ended, how long it took, what it
    #: paid. A career is a story the game was not telling back; `log` in
    #: the city reads it, and so does whoever comes after.
    history: list = field(default_factory=list)
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
        # A fork, not the stream: the draw skips names the meta file has
        # seen, and a draw of variable length on the shared stream would
        # make the world depend on what other characters were called.
        alias = Alias(name=fresh_name(rng.fork('names', 'first')),
                      established=0)
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
        # Origin debts carry their own terms (D95). At the house rate a
        # buyout of twenty-six thousand grew faster than any honest income
        # and the origin's ending could not be reached: measured, a
        # follower earned about a thousand a shift against a leak of
        # fifteen hundred. These are slow, taken in instalments, and paid
        # down fastest by working for the lender (`LENDER_WORK_SHARE`).
        if character.origin == 'academic':
            game.debt = Debt(
                amount=9400, lender='sixes', opened=0,
                rate=ORIGIN_RATE['academic'], grace=12, instalment=600,
                note='The department did not lend you the deck. Somebody in '
                     'the Ninth did, against the department\'s name, and the '
                     'department has since stopped answering.')
        elif character.origin == 'bonded':
            game.debt = Debt(
                amount=26000, lender='kagawa', opened=0,
                rate=ORIGIN_RATE['bonded'], grace=18, instalment=1500,
                note='A buyout figure, calculated by Kagawa, for a contract '
                     'Kagawa wrote. It is not a debt in any sense a court '
                     'would recognise. It is the price of the rest of your '
                     'life and they will take instalments.')
        return game

    def new_alias(self, name: str = '') -> Alias:
        """Burn the current name and take another, per D13."""
        self.alias.burned = True
        fresh = Alias(name=name or fresh_name(
            self.rng.fork('names', f'burn{len(self.aliases)}')),
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
            'history': [dict(h) for h in self.history[-HISTORY_KEEP:]],
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
            history=[dict(h) for h in (d.get('history') or [])
                     if isinstance(h, dict)],
        )

    # ------------------------------------------------------------------

    def save(self, slot: str = 'default'):
        return save_mod.write(self.to_dict(), slot)

    @classmethod
    def load(cls, slot: str = 'default') -> Game:
        return cls.from_dict(save_mod.read(slot))
