"""The persistent city: time, posture, the board, and consequences.

The city's job is to make a run mean something before it happens and after it
finishes. Before: the board is generated from current standing, and the target's
posture decides how hard the network will be. After: residue becomes heat,
success becomes posture, and both outlive the session.

**Time is the currency.** Everything costs shifts, the board expires, and heat
decays only with time. That makes "do nothing for a week" a real strategy with
a real cost, which is the shape a city layer needs if it is not going to be a
menu between runs.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..content import districts, factions
from ..model.identity import Alias
from ..rng import Rng
from . import contracts as contract_mod
from . import market as market_mod
from .contracts import Contract
from .market import Listing

SHIFTS_PER_DAY = 3
SHIFT_NAMES = ('morning', 'afternoon', 'night')

#: Residue-to-heat conversion happens once, on the shift after a run, so the
#: player gets out believing they were clean and finds out later. That delay is
#: deliberate and is the whole emotional point of D5's third quantity.
RESIDUE_DELAY = 1


@dataclass(slots=True)
class PendingFallout:
    """Consequences in flight. Applied when the shift comes around."""

    due: int
    faction: str
    heat: float
    posture: float
    note: str

    def to_dict(self) -> dict:
        return {'due': self.due, 'faction': self.faction, 'heat': self.heat,
                'posture': self.posture, 'note': self.note}

    @classmethod
    def from_dict(cls, d: dict) -> PendingFallout:
        return cls(due=int(d['due']), faction=d['faction'],
                   heat=float(d['heat']), posture=float(d['posture']),
                   note=d.get('note', ''))


@dataclass(slots=True)
class City:
    shift: int = 0
    where: str = districts.START
    #: faction -> current security posture. Persists across aliases, because a
    #: robbed corporation hardens whether or not it knows who robbed it.
    posture: dict = field(default_factory=dict)
    #: faction -> active bounty value. A bounty makes their districts dangerous.
    bounties: dict = field(default_factory=dict)
    board: list = field(default_factory=list)
    #: The contract currently accepted, if any.
    accepted: str = ''
    next_cid: int = 1
    #: district -> listings, and the shift they were rolled.
    stock: dict = field(default_factory=dict)
    stock_shift: int = -999
    pending: list = field(default_factory=list)
    #: Free-text log of what the world did while you were not looking.
    news: list = field(default_factory=list)

    # ------------------------------------------------------------------

    @classmethod
    def new(cls, rng: Rng, alias: Alias) -> City:
        city = cls()
        city.posture = {k: f.posture for k, f in factions.BY_KEY.items()}
        city.refresh_board(rng, alias)
        city.refresh_stock(rng)
        return city

    # -- time ----------------------------------------------------------

    @property
    def day(self) -> int:
        return self.shift // SHIFTS_PER_DAY + 1

    @property
    def phase(self) -> str:
        return SHIFT_NAMES[self.shift % SHIFTS_PER_DAY]

    @property
    def when(self) -> str:
        return f'day {self.day}, {self.phase}'

    @property
    def district(self) -> districts.District:
        return districts.BY_KEY[self.where]

    def advance(self, rng: Rng, alias: Alias, shifts: int = 1) -> list[str]:
        """Move time forward. Returns everything the player should be told."""
        told: list[str] = []
        for _ in range(max(1, shifts)):
            self.shift += 1
            alias.decay_heat()
            self._decay_posture()
            told.extend(self._apply_pending(alias))
            told.extend(self._expire(alias))
            if self.shift % market_mod.REFRESH == 0:
                self.refresh_stock(rng)
        # Top the board back up rather than replacing it, so a contract the
        # player was saving does not vanish because a shift ticked over.
        told.extend(self.top_up_board(rng, alias))
        return told

    def _decay_posture(self) -> None:
        """Posture drifts back toward baseline. Slowly: a robbed corporation
        does not un-harden quickly, and the player should feel that a campaign
        against one target has a cost that compounds."""
        for key, fac in factions.BY_KEY.items():
            current = self.posture.get(key, fac.posture)
            if current > fac.posture:
                self.posture[key] = max(fac.posture, current - 0.4)

    def _apply_pending(self, alias: Alias) -> list[str]:
        told: list[str] = []
        still: list[PendingFallout] = []
        for item in self.pending:
            if item.due > self.shift:
                still.append(item)
                continue
            if item.heat:
                alias.add_heat(item.faction, item.heat)
            if item.posture:
                base = factions.BY_KEY[item.faction].posture
                self.posture[item.faction] = min(
                    100, self.posture.get(item.faction, base) + item.posture)
            if item.note:
                told.append(item.note)
        self.pending = still
        return told

    def _expire(self, alias: Alias) -> list[str]:
        told: list[str] = []
        keep: list[Contract] = []
        for contract in self.board:
            if contract.expired(self.shift) and contract.cid != self.accepted:
                told.append(f'[dim]{contract.title} '
                            f'({contract.patron_data.short}) expired.[/]')
            else:
                keep.append(contract)
        self.board = keep
        return told

    # -- the board -----------------------------------------------------

    def board_size(self, char) -> int:
        size = contract_mod.BOARD_SIZE
        if char is not None and char.origin == 'protege':
            size += 1  # Known quantity
        return size

    def refresh_board(self, rng: Rng, alias: Alias, char=None) -> None:
        self.board = contract_mod.generate_board(
            rng('contracts'), self.shift, alias, self.posture,
            count=self.board_size(char), start_id=self.next_cid)
        self.next_cid += len(self.board) + 1

    def top_up_board(self, rng: Rng, alias: Alias, char=None) -> list[str]:
        want = self.board_size(char)
        have = len(self.board)
        if have >= want:
            return []
        fresh = contract_mod.generate_board(
            rng('contracts'), self.shift, alias, self.posture,
            count=want - have, start_id=self.next_cid)
        self.next_cid += len(fresh) + 1
        self.board.extend(fresh)
        return [f'[dim]{len(fresh)} new posting'
                f'{"s" if len(fresh) != 1 else ""} on the board.[/]']

    def contract(self, cid: str) -> Contract | None:
        return next((c for c in self.board if c.cid == cid), None)

    @property
    def current(self) -> Contract | None:
        return self.contract(self.accepted) if self.accepted else None

    # -- market --------------------------------------------------------

    def refresh_stock(self, rng: Rng) -> None:
        stream = rng('market')
        self.stock = {d.key: market_mod.restock(stream, d.key, self.shift)
                      for d in districts.DISTRICTS}
        self.stock_shift = self.shift

    def listings(self, kind: str | None = None) -> list[Listing]:
        here = self.stock.get(self.where, [])
        return [l for l in here if (kind is None or l.kind == kind) and l.stock > 0]

    # -- travel --------------------------------------------------------

    def can_travel(self, target: str) -> tuple[bool, str]:
        if target not in districts.BY_KEY:
            return False, f'no district called {target!r}'
        if target == self.where:
            return False, 'you are already there'
        if target not in self.district.neighbours:
            route = ', '.join(districts.BY_KEY[n].name
                              for n in self.district.neighbours)
            return False, (f'{districts.BY_KEY[target].name} is not one shift '
                           f'from here. From {self.district.name} you can '
                           f'reach: {route}')
        return True, ''

    def danger(self, alias: Alias, target: str) -> tuple[int, str]:
        """How risky arriving in a district is, given who is looking for you."""
        district = districts.BY_KEY[target]
        watchers = (district.controller, *district.presence)
        worst, who = 0, ''
        for key in watchers:
            score = alias.attention(key) + self.bounties.get(key, 0)
            score = int(score * (0.5 + district.security / 100.0))
            if score > worst:
                worst, who = score, key
        return worst, who

    # -- consequences --------------------------------------------------

    def apply_run(self, alias: Alias, summary: dict, rng: Rng) -> list[str]:
        """Turn a finished run into city state. The D5 payoff.

        Immediate effects land now. Residue is queued and lands a shift later,
        which is what makes getting away with it provisional.
        """
        told: list[str] = []
        target = summary['faction']
        fac = factions.BY_KEY[target]
        outcome = summary['outcome']
        residue = int(summary.get('residue', 0))

        alias.runs += 1

        if outcome == 'clean' and summary.get('objective'):
            gain = 6 + summary.get('haul_value', 0) // 900
            self.pending.append(PendingFallout(
                due=self.shift + RESIDUE_DELAY, faction=target,
                heat=0.0, posture=fac.hardening,
                note=f'[dim]{fac.short} has changed something. Their posture '
                     f'is up.[/]'))
            told.append(f'[ok]Work recorded.[/] {gain} standing with your patron.')

        if residue:
            from ..run.session import RESIDUE_TO_HEAT
            heat = residue * RESIDUE_TO_HEAT
            # A run that was noticed at the time converts worse.
            if summary.get('alert') in ('red', 'lockdown'):
                heat *= 1.4

            # Forensics rank 4: the heat is real, it just lands on somebody
            # else. This does not reduce the consequence, it redirects it, and
            # the redirected faction reacts to the accusation.
            framed = summary.get('framed') or ''
            if framed and framed in factions.BY_KEY:
                other = factions.BY_KEY[framed]
                note = (f'[heat]{fac.short} finished their forensics and came '
                        f'up with {other.short}.[/] [dim]Their problem now.[/]')
                self.pending.append(PendingFallout(
                    due=self.shift + RESIDUE_DELAY, faction=target,
                    heat=heat * 0.15, posture=fac.hardening * 0.4, note=note))
                # The framed faction does not enjoy being framed, and the
                # accuser now likes them considerably less.
                alias.adjust_rep(framed, -6)
                self.posture[framed] = min(
                    100, self.posture.get(framed, other.posture) + 2.0)
            else:
                note = (f'[heat]{fac.short} forensics finished with what you '
                        f'left behind.[/] [dim]Heat +{int(heat)}.[/]')
                self.pending.append(PendingFallout(
                    due=self.shift + RESIDUE_DELAY, faction=target,
                    heat=heat, posture=fac.hardening * 0.4, note=note))

        if outcome in ('severed', 'burned'):
            alias.add_heat(target, 12)
            told.append(f'[warn]{fac.short} logged the intrusion attempt.[/]')
        if outcome == 'flatline':
            told.append('[err]There is no city layer for this one.[/]')

        return told

    def pay_out(self, alias: Alias, contract: Contract, summary: dict,
                pay_mult: float = 1.0) -> tuple[int, list[str]]:
        """Settle a contract. Returns credits paid and what to tell the player."""
        told: list[str] = []
        if not summary.get('objective'):
            told.append(f'[err]{contract.patron_data.short} does not pay for '
                        f'attempts.[/]')
            alias.adjust_rep(contract.patron, -8)
            return 0, told

        pay = int(contract.pay * pay_mult)
        if summary['outcome'] != 'clean':
            # You delivered, but they had to hear about it from somebody else.
            pay = int(pay * 0.7)
            told.append('[warn]The exit was messy. They withheld part of it.[/]')
        alias.adjust_rep(contract.patron, 8)
        alias.adjust_rep(contract.target, -10)
        told.append(f'[credit]{pay:,}c[/] from {contract.patron_data.short}.')
        return pay, told

    # -- persistence ---------------------------------------------------

    def to_dict(self) -> dict:
        return {
            'shift': self.shift, 'where': self.where,
            'posture': {k: round(v, 2) for k, v in self.posture.items()},
            'bounties': dict(self.bounties),
            'board': [c.to_dict() for c in self.board],
            'accepted': self.accepted, 'next_cid': self.next_cid,
            'stock': {k: [l.to_dict() for l in v] for k, v in self.stock.items()},
            'stock_shift': self.stock_shift,
            'pending': [p.to_dict() for p in self.pending],
            'news': list(self.news[-40:]),
        }

    @classmethod
    def from_dict(cls, d: dict) -> City:
        return cls(
            shift=int(d.get('shift', 0)),
            where=d.get('where', districts.START),
            posture={k: float(v) for k, v in (d.get('posture') or {}).items()},
            bounties={k: int(v) for k, v in (d.get('bounties') or {}).items()},
            board=[Contract.from_dict(c) for c in (d.get('board') or [])],
            accepted=d.get('accepted', ''),
            next_cid=int(d.get('next_cid', 1)),
            stock={k: [Listing.from_dict(l) for l in v]
                   for k, v in (d.get('stock') or {}).items()},
            stock_shift=int(d.get('stock_shift', -999)),
            pending=[PendingFallout.from_dict(p) for p in (d.get('pending') or [])],
            news=list(d.get('news') or []),
        )
