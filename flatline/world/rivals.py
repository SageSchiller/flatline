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
    #: '' | 'nemesis' | 'partner'. Latched: see `content/rivals.py`. A bond
    #: that came off because you did somebody a favour on a Tuesday is a
    #: mood, and the point of thirty runs with the same person is that it
    #: does not come off.
    bond: str = ''

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
                'bond': self.bond,
                'rep': {k: v for k, v in self.rep.items() if v},
                'jobs': self.jobs, 'alive': self.alive, 'died': self.died,
                'last': self.last}

    @classmethod
    def from_dict(cls, d: dict) -> Rival:
        return cls(key=d['key'], disposition=int(d.get('disposition', 0)),
                   bond=d.get('bond', ''),
                   rep={k: int(v) for k, v in (d.get('rep') or {}).items()},
                   jobs=int(d.get('jobs', 0)),
                   alive=bool(d.get('alive', True)),
                   died=int(d.get('died', -1)), last=d.get('last', ''))


def seed_pool() -> list[Rival]:
    """The city's runners at the start of a game."""
    return [Rival(key=r.key, disposition=r.disposition, rep=dict(r.standing))
            for r in rival_content.RIVALS]


# --------------------------------------------------------------------------
# arcs
# --------------------------------------------------------------------------


def check_bonds(pool: list[Rival]) -> list[tuple[Rival, str]]:
    """Anybody who has just crossed into a nemesis or a partner.

    Two gates, not one. Disposition alone would let a single betrayal on your
    fourth shift produce a lifelong enemy, and the whole point of an arc is
    that it takes the length of a campaign to get there.
    """
    crossed: list[tuple[Rival, str]] = []
    for rival in pool:
        if rival.bond or not rival.alive:
            continue
        if rival.jobs < rival_content.BOND_AFTER_JOBS:
            continue
        if rival.disposition <= rival_content.NEMESIS_AT:
            rival.bond = 'nemesis'
        elif rival.disposition >= rival_content.PARTNER_AT:
            rival.bond = 'partner'
        else:
            continue
        crossed.append((rival, rival.bond))
    return crossed


def bond_turn(rng: Stream, pool: list[Rival], alias, flags=()) -> list[str]:
    """What the people who have made up their minds about you do this shift.

    One thing each, occasionally. A bond that fired every shift would be a
    weather system; what makes this a relationship is that it turns up when
    you were thinking about something else. A nemesis you paid to stop
    (`paid_<key>`, D56) has stopped: that is what the figure bought.
    """
    told: list[str] = []
    for rival in pool:
        if not rival.alive or rival.bond not in rival_content.BOND_KINDS:
            continue
        if rival.bond == 'nemesis' and f'paid_{rival.key}' in flags:
            continue
        if not rng.chance(rival_content.BOND_CHANCE):
            continue
        hot, _ = alias.hottest
        if rival.bond == 'nemesis':
            faction = hot or rng.pick(factions.FACTION_KEYS)
            if hot:
                alias.add_heat(hot, rival_content.NEMESIS_HEAT)
            told.append('[heat]' + rng.pick(
                rival_content.NEMESIS_ACTS).format(
                    name=rival.name,
                    faction=factions.BY_KEY[faction].short) + '[/]')
        else:
            if hot:
                alias.add_heat(hot, -rival_content.PARTNER_HEAT)
            told.append('[ok]' + rng.pick(
                rival_content.PARTNER_ACTS).format(name=rival.name) + '[/]')
    return told


def declare(rival: Rival, kind: str) -> str:
    """The scene when somebody crosses. Once, ever, per runner."""
    table = (rival_content.NEMESIS_DECLARED if kind == 'nemesis'
             else rival_content.PARTNER_DECLARED)
    line = table.get(rival.data.style) or next(iter(table.values()))
    return line.format(name=rival.name)


# --------------------------------------------------------------------------
# their turn
# --------------------------------------------------------------------------


def take_turn(rng: Stream, pool: list[Rival], board: list, posture: dict,
              shift: int, protected: str = '',
              busy: set | None = None) -> tuple[list, list[str]]:
    """Let the rivals work. Returns (contracts they took, what to tell you).

    `protected` is the contract the player has accepted. Nobody takes that one
    out from under them: losing an accepted job to an NPC would be a rug-pull
    rather than a consequence, and the player cannot even see it coming.

    `busy` is anybody already working for the player. Without it a runner you
    have hired can be sent off on somebody else's contract on the same shift
    they are standing next to you in a network, and can die on it, which is
    exactly the sort of bug that only shows up in play.
    """
    told: list[str] = []
    taken: list = []

    for rival in rng.shuffled(pool):
        if len(taken) >= MAX_PER_SHIFT:
            break
        if len(board) - len(taken) <= BOARD_FLOOR:
            break
        if not rival.alive or rival.key in (busy or ()):
            continue
        if not rng.chance(ACTIVITY):
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


# --------------------------------------------------------------------------
# the social layer
# --------------------------------------------------------------------------

#: Disposition below which nobody does anything for you at any price.
HIRE_FLOOR = -25
#: Base fee, scaled by skill. They also take a cut of the haul.
HIRE_BASE = 900
#: Share of the run's haul value an ally takes.
HIRE_CUT = 0.25


def hire_price(rival: Rival, flags=()) -> int:
    """What they want up front. Liking you is a discount, not a waiver.

    Somebody who decided to work with you and was told yes (`with_<key>`,
    D56) charges half: the fee that is smaller than it should be, and
    arrives on time.
    """
    base = HIRE_BASE + rival.data.skill * 420
    price = max(300, int(base * (1.0 - rival.disposition / 300.0)))
    if f'with_{rival.key}' in flags:
        price = max(300, price // 2)
    return price


def can_hire(rival: Rival) -> tuple[bool, str]:
    if not rival.alive:
        return False, f'{rival.name} is dead.'
    if rival.disposition < HIRE_FLOOR:
        return False, (f'{rival.name} does not work with you and is not '
                       f'interested in discussing it.')
    return True, ''


def can_crew(rival: Rival) -> tuple[bool, str]:
    """Whether somebody will sign on permanently rather than job by job."""
    if not rival.alive:
        return False, f'{rival.name} is dead.'
    if rival.disposition < rival_content.CREW_AT:
        return False, (f'{rival.name} will take a job with you. Working with '
                       f'you is a different question and the answer is not '
                       f'yet.')
    return True, ''


def crew_retainer(rival: Rival) -> int:
    """What signing somebody costs up front."""
    return max(1000, rival.data.skill * rival_content.CREW_RETAINER)


def crew_bonus(runs: int) -> int:
    """Effective skill somebody has gained from working with *you*.

    Capped, and it is not the same as getting better: it is knowing how the
    other one moves, which is a real thing and does not transfer.
    """
    return min(rival_content.CREW_MAX_STEPS,
               runs // rival_content.CREW_RUNS_PER_STEP)


def bounty_buyers(rival: Rival) -> list[tuple[str, int]]:
    """Who would pay for this name, and roughly what for.

    A faction pays for a runner in proportion to how much that runner has
    cost them. That means selling somebody is only lucrative once they have
    done something, which in turn means the most valuable name to sell is
    usually the most useful person to know.
    """
    out: list[tuple[str, int]] = []
    for key, fac in factions.BY_KEY.items():
        standing = rival.reputation(key)
        if standing >= -10:
            continue
        value = int(abs(standing) * 45 + rival.data.skill * 260)
        out.append((key, value))
    return sorted(out, key=lambda pair: -pair[1])


def sell_out(rng: Stream, rival: Rival, buyer: str, pool: list[Rival],
             alias, shift: int) -> dict:
    """Sell a name. Returns what happened, for the caller to narrate.

    The consequences are deliberately wide. The rival's disposition floors,
    everybody who works with them cools on you, the buyer warms to you, and
    there is a real chance the person you sold does not survive it. None of
    that is reversible.
    """
    price = dict(bounty_buyers(rival)).get(buyer, 0)
    fac = factions.BY_KEY[buyer]

    # How it goes for them, weighted by how good they are at not being found.
    escape = 0.15 + rival.data.skill * 0.045
    if rival.data.style == 'quiet':
        escape += 0.2
    if rng.chance(min(0.75, escape)):
        outcome = 'escaped'
    elif rng.chance(0.35 if fac.kind == 'law' else 0.6):
        outcome = 'killed'
    else:
        outcome = 'taken'

    rival.adjust_disposition(-200)
    if outcome == 'killed':
        rival.alive = False
        rival.died = shift
    elif outcome == 'taken':
        rival.alive = False
        rival.died = shift

    # The street is small. Anybody who liked them likes you less.
    for other in pool:
        if other.key == rival.key or not other.alive:
            continue
        shared = sum(1 for f in factions.FACTION_KEYS
                     if other.reputation(f) > 20 and rival.reputation(f) > 20)
        other.adjust_disposition(-8 - shared * 4)

    alias.adjust_rep(buyer, 12)
    for enemy in factions.FACTION_KEYS:
        if factions.relation(buyer, enemy) < -0.4:
            alias.adjust_rep(enemy, -4)

    return {'price': price, 'outcome': outcome, 'buyer': buyer,
            'rival': rival.key}


def favour_cost(kind: str) -> int:
    from ..content.rivals import FAVOURS
    return FAVOURS[kind][0]


def can_ask(rival: Rival, kind: str, char=None) -> tuple[bool, str]:
    """Whether this runner will do this for you.

    `char` is optional because two callers only want to know what a favour
    nominally costs. When it is supplied, presence moves the bar: somebody who
    carries a room needs to be thought slightly less well of before they get
    asked a favour, which is most of what presence is for.
    """
    from ..content import appearance
    from ..content.rivals import FAVOURS
    if kind not in FAVOURS:
        return False, f'no such favour: {kind}'
    if not rival.alive:
        return False, f'{rival.name} is dead.'
    cost = favour_cost(kind)
    if char is not None:
        cost -= appearance.social_bonus(char.presence)
    if rival.disposition < cost:
        return False, (f'{rival.name} is not going to do that for you. '
                       f'That favour needs them at {cost} and they are at '
                       f'{rival.disposition}.')
    return True, ''
