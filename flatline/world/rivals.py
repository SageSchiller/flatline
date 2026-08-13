"""Rival runners as live state: what they took, how it went, who died.

Their turn happens on the shift boundary, entirely offscreen, and resolves
immediately. That is deliberate. Simulating a rival's run tick by tick would
cost a great deal of code to produce a number the player never sees, and the
part that matters to the player is not *how* Vesper got into Kagawa, it is that
Kagawa is harder now and Vesper is owed a favour by somebody.

The important systemic consequence: **posture rises when rivals succeed.** The
world hardens whether or not the player does anything, which means sitting on
your hands for ten shifts is not a free way to let heat decay. It is a way to
let somebody else make the city more expensive.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..content import factions, rivals as rival_content
from ..rng import Stream

#: Chance per shift that any given rival goes looking for work.
ACTIVITY = 0.11
#: At most this many jobs leave the board to rivals per shift, across all of
#: them. Without a cap, seven rivals at any meaningful activity rate strip a
#: five-slot board faster than the player can read it, and the feature stops
#: being pressure and becomes denial.
MAX_PER_SHIFT = 1
#: Rivals leave the player this many postings alone. A board picked down to
#: nothing is not a living city, it is a broken one.
BOARD_FLOOR = 3
#: A rival will not touch a patron who dislikes them this much.
ACCESS_FLOOR = -55
#: Chance a failed run kills them outright. Deliberately small: a city that
#: loses a named runner every week stops having named runners.
DEATH_ON_FAILURE = 0.08


@dataclass(slots=True)
class Rival:
    key: str
    disposition: int = 0
    rep: dict = field(default_factory=dict)
    jobs: int = 0
    alive: bool = True
    #: Shift they died on, for the memorial in `who`.
    died: int = -1
    #: One line of what they were last seen doing.
    last: str = ''

    @property
    def data(self) -> rival_content.RivalType:
        return rival_content.BY_KEY[self.key]

    @property
    def name(self) -> str:
        return self.data.name

    def reputation(self, faction: str) -> int:
        return int(self.rep.get(faction, 0))

    def adjust_rep(self, faction: str, delta: float) -> None:
        self.rep[faction] = max(-100, min(100, int(round(
            self.reputation(faction) + delta))))

    def adjust_disposition(self, delta: int) -> int:
        self.disposition = max(-100, min(100, self.disposition + delta))
        return self.disposition

    @property
    def band(self) -> str:
        return rival_content.disposition_band(self.disposition)

    def to_dict(self) -> dict:
        return {'key': self.key, 'disposition': self.disposition,
                'rep': {k: v for k, v in self.rep.items() if v},
                'jobs': self.jobs, 'alive': self.alive, 'died': self.died,
                'last': self.last}

    @classmethod
    def from_dict(cls, d: dict) -> Rival:
        return cls(key=d['key'], disposition=int(d.get('disposition', 0)),
                   rep={k: int(v) for k, v in (d.get('rep') or {}).items()},
                   jobs=int(d.get('jobs', 0)),
                   alive=bool(d.get('alive', True)),
                   died=int(d.get('died', -1)), last=d.get('last', ''))


def seed_pool() -> list[Rival]:
    """The city's runners at the start of a game."""
    return [Rival(key=r.key, disposition=r.disposition, rep=dict(r.standing))
            for r in rival_content.RIVALS]


# --------------------------------------------------------------------------
# their turn
# --------------------------------------------------------------------------


def take_turn(rng: Stream, pool: list[Rival], board: list, posture: dict,
              shift: int, protected: str = '') -> tuple[list, list[str]]:
    """Let the rivals work. Returns (contracts they took, what to tell you).

    `protected` is the contract the player has accepted. Nobody takes that one
    out from under them: losing an accepted job to an NPC would be a rug-pull
    rather than a consequence, and the player cannot even see it coming.
    """
    told: list[str] = []
    taken: list = []

    for rival in rng.shuffled(pool):
        if len(taken) >= MAX_PER_SHIFT:
            break
        if len(board) - len(taken) <= BOARD_FLOOR:
            break
        if not rival.alive or not rng.chance(ACTIVITY):
            continue
        options = [c for c in board
                   if c.cid != protected
                   and c.cid not in {t.cid for t in taken}
                   and rival.reputation(c.patron) >= ACCESS_FLOOR]
        if not options:
            continue

        weights = {}
        for contract in options:
            weight = 1.0
            if contract.objective in rival.data.prefers:
                weight *= 2.6
            # Standing with the patron buys access to their better work.
            weight *= 1.0 + rival.reputation(contract.patron) / 90.0
            # Ledger declines almost everything, which is the whole character.
            if rival.data.style == 'careful':
                weight *= 0.35
            weights[contract.cid] = max(0.05, weight)

        cid = rng.weighted(weights)
        contract = next(c for c in options if c.cid == cid)
        taken.append(contract)
        rival.jobs += 1

        told.append('[dim]' + rng.pick(rival_content.TAKEN_LINES).format(
            name=rival.name, title=contract.title) + '[/]')
        told.extend(_resolve(rng, rival, contract, posture, shift))

    return taken, told


def _resolve(rng: Stream, rival: Rival, contract, posture: dict,
             shift: int) -> list[str]:
    """Run the job offscreen and apply what it did to the world."""
    told: list[str] = []
    target = contract.target
    fac = factions.BY_KEY[target]
    current = posture.get(target, fac.posture)

    # Competence against hardness, on the same d10 the player uses, so a rival
    # is legible in the same terms the player already understands.
    margin = rival.data.skill * 2 + rng.int(1, 10) - int(current / 5) - 8
    if rival.data.style == 'careful':
        margin += 3
    if rival.data.style == 'loud':
        margin -= 1

    if margin >= 6:
        outcome = 'clean'
    elif margin >= 0:
        outcome = 'messy'
    elif margin >= -6:
        outcome = 'failed'
    else:
        outcome = 'dead' if rng.chance(DEATH_ON_FAILURE) else 'failed'

    if outcome in ('clean', 'messy'):
        gain = fac.hardening * (1.0 if outcome == 'clean' else 0.6)
        posture[target] = min(100, current + gain)
        rival.adjust_rep(contract.patron, 6 if outcome == 'clean' else 3)
        rival.adjust_rep(target, -8)
    elif outcome == 'failed':
        posture[target] = min(100, current + fac.hardening * 0.25)
        rival.adjust_rep(contract.patron, -5)
    else:
        rival.alive = False
        rival.died = shift

    line = rng.pick(rival_content.OUTCOME_LINES[outcome]).format(
        name=rival.name, target=fac.short)
    rival.last = line
    role = {'clean': 'dim', 'messy': 'warn',
            'failed': 'warn', 'dead': 'err'}[outcome]
    told.append(f'[{role}]{line}[/]')
    return told


def on_player_took(rng: Stream, pool: list[Rival], contract) -> list[str]:
    """A rival notices when you take work they wanted.

    Small, and it accumulates. Over a campaign the player discovers they have
    made an enemy of somebody purely by being faster to the board, which is a
    better story than any single scripted grudge.
    """
    told: list[str] = []
    for rival in pool:
        if not rival.alive:
            continue
        if contract.objective not in rival.data.prefers:
            continue
        if rival.reputation(contract.patron) < 25:
            continue
        rival.adjust_disposition(-3)
        if rival.disposition <= -50 and rng.chance(0.3):
            told.append(f'[warn]{rival.name} wanted that one, and has started '
                        f'saying so where people can hear.[/]')
    return told


def hireable(pool: list[Rival]) -> list[Rival]:
    """Who would run alongside you if asked. Escort contracts draw from here."""
    return [r for r in pool if r.alive and r.disposition > -50]


def pick_escort(rng: Stream, pool: list[Rival], patron: str) -> Rival | None:
    """Who the patron has already put on the job you are covering."""
    options = [r for r in hireable(pool)
               if r.reputation(patron) >= ACCESS_FLOOR]
    if not options:
        return None
    weights = {r.key: 1.0 + max(0, r.reputation(patron)) / 50.0
               + (1.5 if 'escort' in r.data.prefers else 0.0)
               for r in options}
    key = rng.weighted(weights)
    return next(r for r in options if r.key == key)
