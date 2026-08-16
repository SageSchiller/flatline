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

from ..content import appearance, districts, drugs as drug_content
from ..content import events as event_content
from ..content import factions
from ..model.identity import Alias
from ..rng import Rng
from .. import ui
from . import contracts as contract_mod
from . import debt as debt_mod
from . import fallout as fallout_mod
from . import rivals as rival_mod
from . import market as market_mod
from .contracts import Contract
from .market import Listing

SHIFTS_PER_DAY = 3
SHIFT_NAMES = ('morning', 'afternoon', 'night')

#: Residue-to-heat conversion happens once, on the shift after a run, so the
#: player gets out believing they were clean and finds out later. That delay is
#: deliberate and is the whole emotional point of D5's third quantity.
RESIDUE_DELAY = 1

#: How much of the world's news is kept. A scrollback rather than a record.
NEWS_KEPT = 40

#: How often an ambient beat is about somebody who used to do this instead of
#: about the city. Low: the departed are a ghost story the city tells
#: occasionally, and a city that talks about nobody else would be a memorial.
REMEMBERED_CHANCE = 0.06


def _shifts(n: int) -> str:
    """A shift count, in the words the rest of the game uses for time."""
    return '1 shift' if n == 1 else f'{n} shifts'


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
    #: A rival paid to run alongside you on the next job.
    hired: str = ''
    #: Districts you have set foot in. Read by the Courier's passive, and a
    #: reasonable thing for a city to remember about somebody in any case.
    visited: set = field(default_factory=set)
    #: Somewhere of your own, or empty. `{key, stored: [...], credits: n,
    #: raids: n}`. See `content/safehouses.py`: it is a place to put things
    #: and a place that can be found, and those are the same half.
    safehouse: dict = field(default_factory=dict)
    #: NPC keys whose private counter you have opened. Re-applied after every
    #: restock: a person's cabinet not rotating is the one promise it makes
    #: that a market does not, and `refresh_stock` rebuilds the shelves from
    #: scratch, so without this the promise was false the first time six
    #: shifts went by.
    counters: set = field(default_factory=set)
    #: venue key -> credits taken off that table, ever. The card game reads it
    #: and gets harder; it is the city remembering a specific room rather than
    #: a faction, which is the right grain for somebody who has been winning
    #: at the same table for a month.
    tables: dict = field(default_factory=dict)
    next_cid: int = 1
    #: district -> listings, and the shift they were rolled.
    stock: dict = field(default_factory=dict)
    stock_shift: int = -999
    pending: list = field(default_factory=list)
    #: The other runners. They take work off the board while you deliberate.
    rivals: list = field(default_factory=list)
    #: Free-text log of what the world did while you were not looking. Kept
    #: to NEWS_KEPT: it is a scrollback, not a record, and it is appended to
    #: on every single shift.
    news: list = field(default_factory=list)
    #: Ambient events already shown. Used to bias away from repeats rather
    #: than to forbid them: a city that never repeats itself is as
    #: unconvincing as one with four days in it.
    events_seen: set = field(default_factory=set)
    #: Scenery from the most recent `advance`, kept apart from the news it
    #: returns. Mechanical news is a consequence and an ambient event is a
    #: window, and printing them in one block turns both into a wall of grey.
    #: Not persisted: it is what the player was just shown, not world state.
    ambient: list = field(default_factory=list, compare=False)

    # ------------------------------------------------------------------

    @classmethod
    def new(cls, rng: Rng, alias: Alias, char=None) -> City:
        city = cls()
        city.posture = {k: f.posture for k, f in factions.BY_KEY.items()}
        city.rivals = rival_mod.seed_pool()
        city.visited = {city.where}
        city.refresh_board(rng, alias, char)
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

    def advance(self, rng: Rng, alias: Alias, shifts: int = 1,
                debt=None, char=None) -> list[str]:
        """Move time forward. Returns everything the player should be told."""
        told: list[str] = []
        self.ambient = []
        for _ in range(max(1, shifts)):
            self.shift += 1
            alias.decay_heat(
                1.4 if (char is not None and 'no_history' in char.riders())
                else 1.0)
            self._decay_posture()
            told.extend(self._apply_pending(alias))
            told.extend(self._expire(alias))
            told.extend(self._rival_turn(rng, alias))
            told.extend(fallout_mod.bounty_check(alias, self, rng('events')))
            if debt is not None:
                told.extend(self._debt_turn(rng, alias, debt, char))
            if char is not None and alias is not None:
                told.extend(self._raid_turn(rng, alias, char))
            if char is not None:
                # Chemistry, one shift of it. Told here rather than by the
                # command that spent the shift, because a comedown arriving
                # while you `rest` and a comedown arriving while you `travel`
                # are the same event and it is not the travelling's fault.
                char.chem, said = drug_content.advance(char.chem, 1)
                told.extend(said)
            if self.shift % market_mod.REFRESH == 0:
                self.refresh_stock(rng)
            self.ambient.extend(self._ambient(rng))
        # Top the board back up rather than replacing it, so a contract the
        # player was saving does not vanish because a shift ticked over.
        told.extend(self.top_up_board(rng, alias, char))
        return told

    def _raid_turn(self, rng: Rng, alias: Alias, char) -> list[str]:
        """Whether somebody found the place you keep things.

        This is the only thing in the game that makes heat physical. Attention
        has always been a multiplier on a danger roll, which is real and
        entirely abstract; being wanted has never been able to take anything
        away from you that you could point at.
        """
        from ..content import cyberware, drugs, programs, safehouses
        house = self.safehouse
        if not house or house.get('burned'):
            return []
        prop = safehouses.BY_KEY.get(house.get('key', ''))
        if prop is None:
            return []
        attention = alias.attention(districts.BY_KEY[prop.where].controller)
        stream = rng('events')
        if not stream.chance(safehouses.raid_chance(prop.security, attention)):
            return []

        house['raids'] = int(house.get('raids', 0)) + 1
        told = [f'[err]{stream.pick(safehouses.RAIDS)}[/]']
        stored = list(house.get('stored') or [])
        credits = int(house.get('credits', 0))
        if not stored and not credits:
            told.append(f'[dim]{safehouses.EMPTY_RAID}[/]')
        else:
            take = max(1, int(len(stored) * safehouses.RAID_TAKES))
            gone = stream.sample(stored, min(take, len(stored)))
            for key in gone:
                stored.remove(key)
            lost_cash = int(credits * safehouses.RAID_TAKES)
            house['stored'] = stored
            house['credits'] = credits - lost_cash
            names = []
            for key in gone:
                for table in (programs.BY_KEY, cyberware.BY_KEY,
                              drugs.BY_KEY):
                    if key in table:
                        names.append(table[key].name)
                        break
            if names:
                told.append(f'[err]Gone: {", ".join(sorted(names))}.[/]')
            if lost_cash:
                told.append(f'[err]And {lost_cash:,}c.[/]')
        if house['raids'] >= safehouses.BURN_AFTER:
            # "There is nothing left to take" has to be true when it is
            # printed. Leaving the remainder of the cash in a place nobody can
            # go back to would strand it somewhere the player can see it and
            # not reach it, which is worse than losing it.
            house['burned'] = True
            house['stored'] = []
            house['credits'] = 0
            told.append(f'[err]{safehouses.BURNED}[/]')
        return told

    def _ambient(self, rng: Rng) -> list[str]:
        """One thing the city did this shift that has nothing to do with you.

        Deliberately consequence-free. The moment an ambient event can cost
        credits it stops being scenery and becomes a slot machine attached to
        the rest command, and the player starts reading these for outcomes
        instead of for the city.
        """
        # A long rest passes several shifts and should not narrate all of
        # them: one window per command is a glance out of it, six is a
        # travelogue nobody asked for.
        if self.ambient:
            return []
        stream = rng('events')
        # Occasionally, somebody who used to do this. The city remembering you
        # is the thesis of the whole project and it forgot every character the
        # moment they stopped breathing, so this is where a later runner walks
        # into the last one.
        remembered = self._remembered(stream)
        if remembered:
            return [f'[dim]{remembered}[/]']
        event = event_content.pick(stream, self.where, self.phase,
                                   self.events_seen)
        if event is None:
            return []
        self.events_seen.add(event.key)
        return [f'[dim]{event.text}[/]']

    def _remembered(self, stream) -> str:
        """Somebody who is gone, mentioned by somebody who is not."""
        from .. import save as save_mod
        from ..content import legacy
        if not stream.chance(REMEMBERED_CHANCE):
            return ''
        # Not somebody a living rival is also called. `Vesper Okonkwo` is a
        # runner in this city, and a player who names a character Vesper would
        # otherwise get scenes about the departed that read as being about
        # somebody currently taking work off their board.
        living = {r.data.name.lower() for r in self.rivals if r.alive}
        gone = [g['handle'] for g in save_mod.the_departed()
                if g.get('handle')
                and not any(g['handle'].lower() in name for name in living)]
        if not gone:
            return ''
        return stream.pick(legacy.REMEMBERED).format(
            handle=stream.pick(gone))

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

    def _debt_turn(self, rng: Rng, alias: Alias, debt, char) -> list[str]:
        """Interest, and the lender turning up when it has been long enough."""
        told: list[str] = []
        interest, note = debt_mod.tick(debt, self.shift)
        if note:
            told.append(note)
        if not debt.due(self.shift):
            return told

        take = debt.collect(self.shift)
        stream = rng('events')
        if char is not None and char.credits >= take:
            char.credits -= take
            told.append(f'[heat]{stream.pick(debt_mod.COLLECT_LINES)}[/] '
                        f'[dim]{take:,}c. {debt.amount:,}c outstanding.[/]')
        elif char is not None:
            # Nothing in the account, so they take it out of the room. This
            # routes through the same ladder as everything else, per D6.
            paid = max(0, char.credits)
            char.credits -= paid
            incident = fallout_mod.pick_up(stream, char, alias,
                                           self, debt.lender)
            told.append(f'[err]{debt_mod.IN_KIND}[/]')
            told.append(f'[err]{incident.text}[/]')
            if incident.detail:
                told.append(incident.detail)
            told.append(f'[dim]{debt.amount:,}c outstanding.[/]')
        return told

    def _rival_turn(self, rng: Rng, alias: Alias | None = None) -> list[str]:
        """The other runners work. This is why sitting still is not free."""
        if not self.rivals:
            self.rivals = rival_mod.seed_pool()
        taken, told = rival_mod.take_turn(
            rng('rivals'), self.rivals, self.board, self.posture, self.shift,
            protected=self.accepted,
            busy={self.hired} if self.hired else None)
        if taken:
            gone = {c.cid for c in taken}
            self.board = [c for c in self.board if c.cid not in gone]
        # Anybody who has just made up their mind about you says so, once.
        for rival, kind in rival_mod.check_bonds(self.rivals):
            told.append('')
            told.append(f'[accent2]{rival.name} has decided something about '
                        f'you.[/]')
            told.append(rival_mod.declare(rival, kind))
        if alias is not None:
            told.extend(rival_mod.bond_turn(rng('rivals'), self.rivals, alias))
        self.news.extend(told)
        del self.news[:-NEWS_KEPT]
        return told

    def rival(self, key: str):
        return next((r for r in self.rivals if r.key == key), None)

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

    def board_size(self, char=None) -> int:
        """How many postings the board holds.

        `char` is threaded all the way through rather than defaulted, because
        the protege's Known Quantity passive says "one extra contract on the
        board at all times" and for a long time it only applied to the board
        generated at creation: every top-up afterwards silently dropped back
        to the standard size, so the passive was true for about one shift.
        """
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
            count=want - have, start_id=self.next_cid,
            avoid={c.title for c in self.board})
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
        # And then put back what people keep under their own counters, which
        # is not stock and does not turn over.
        from ..content import npcs as npc_content, offers
        for key in sorted(self.counters):
            stock = offers.BY_NPC_STOCK.get(key)
            npc = npc_content.BY_KEY.get(key)
            if stock is None or npc is None:
                continue
            self._shelve(stock, npc.where or self.where)

    def listings(self, kind: str | None = None,
                 deep: bool | None = None) -> list[Listing]:
        """What is for sale here. `deep` filters the back-room stock: None is
        everything, False is the shop floor, True is only what the back
        room carries."""
        here = self.stock.get(self.where, [])
        return [l for l in here
                if (kind is None or l.kind == kind)
                and (deep is None or bool(l.deep) is deep)
                and l.stock > 0]

    # -- what people keep back -----------------------------------------

    def offer_work(self, rng: Rng, alias: Alias, work) -> Contract:
        """A contract from a person, generated like any other and then bent.

        Deliberately routed through the same generator: personal work has to
        be able to be any shape of job, against any target that makes sense
        for whoever is fronting it, or it becomes a second and much thinner
        contract system that happens to have a name attached.
        """
        stream = rng('contracts')
        target = (stream.pick(work.targets) if work.targets
                  else contract_mod.pick_target(stream, work.patron, alias))
        if target is None:
            target = stream.pick([k for k in factions.FACTION_KEYS
                                  if k != work.patron])
        contract = contract_mod.make_one(
            stream, self.next_cid, work.patron, target, self.shift, alias,
            self.posture, {c.title for c in self.board})
        contract.pay = int(contract.pay * work.pay)
        contract.expires += work.patience
        contract.from_npc = work.npc
        self.next_cid += 1
        self.board.append(contract)
        return contract

    def open_counter(self, stock) -> bool:
        """Put somebody's private stock on the local shelf. True if it is new.

        Added to the district's listings rather than kept in a second
        inventory, so `buy` and `market` work on it unchanged, and recorded in
        `counters` so that `refresh_stock` puts it back: the market turning
        over is a reason to travel and a reason to hurry, and a person's own
        cabinet is the opposite thing.
        """
        self.counters.add(stock.npc)
        return self._shelve(stock, self.where)

    def _shelve(self, stock, where: str) -> bool:
        from ..content import cyberware, drugs, hardware, programs
        here = self.stock.setdefault(where, [])
        have = {(l.kind, l.key) for l in here}
        added = False
        tables = (('program', programs.BY_KEY), ('ware', cyberware.BY_KEY),
                  ('component', hardware.BY_KEY), ('drug', drugs.BY_KEY))
        for key in stock.goods:
            for kind, table in tables:
                item = table.get(key)
                if item is None or (kind, key) in have:
                    continue
                here.append(Listing(
                    kind=kind, key=key,
                    price=max(1, int(round(item.price * stock.markup))),
                    stock=1))
                added = True
                break
        return added

    # -- travel --------------------------------------------------------

    def can_travel(self, target: str) -> tuple[bool, str]:
        if target not in districts.BY_KEY:
            return False, f'no district called {target!r}'
        if target == self.where:
            return False, 'you are already there'
        if target not in self.district.neighbours:
            # Not "no", but "not in one go". Somebody who lives in this city
            # knows how to walk across it, and the refusal that only listed
            # the neighbours left the player to solve a maze they were never
            # shown. The route is handed over as the line to type, which also
            # teaches `;` to anybody who has not found it yet.
            steps = self.walk_to(target)
            if not steps:
                return False, (f'there is no way from {self.district.name} to '
                               f'{districts.BY_KEY[target].name}')
            return False, (f'{districts.BY_KEY[target].name} is '
                           f'{_shifts(self.shifts_to(target))} from here, '
                           f'not one. `{steps}`')
        return True, ''

    # -- the shape of the city -----------------------------------------

    def route(self, target: str) -> list[str]:
        """The districts to walk through to reach `target`, in order.

        Empty when you are already there or there is no way, which are the
        same answer to the only question the caller has.
        """
        return ui.shortest_path(districts.GRAPH, self.where, target)

    def shifts_to(self, target: str) -> int:
        """How many shifts of walking. Zero means you are standing in it."""
        return len(self.route(target))

    def walk_to(self, target: str) -> str:
        """The route as the line to type. Empty when you are already there.

        Every place that tells the player where to go hands them this rather
        than the destination, because `travel <somewhere three districts
        away>` is a command the travel command itself refuses, and being sent
        to a refusal is worse than being told nothing.
        """
        return '; '.join(f'travel {k}' for k in self.route(target))

    def danger(self, alias: Alias, target: str, rng: Rng | None = None):
        """How risky arriving in a district is, given who is looking for you.

        Lives in `world/fallout.py` so that travel, legwork, and anything else
        that puts you on a street ask exactly the same question.
        """
        stream = rng('events') if rng is not None else None
        if stream is None:
            # Scoring is deterministic and needs no draws; the stream is only
            # threaded for callers that go on to resolve an incident.
            from ..rng import Rng as _Rng
            stream = _Rng(0)('events')
        return fallout_mod.arrival_risk(stream, alias, self, target)

    # -- consequences --------------------------------------------------

    def apply_run(self, alias: Alias, summary: dict, rng: Rng,
                  memorable: int = 0) -> list[str]:
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
            # Forensics is only half of it. The other half is somebody
            # describing you to somebody who is writing it down, and a face
            # that fits nine thousand people is worth real protection here.
            heat *= appearance.heat_mult(memorable)

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
                pay_mult: float = 1.0,
                memorable: int = 0) -> tuple[int, list[str]]:
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
        # Work gets attributed to somebody. Being a person worth naming means
        # the story that goes round afterwards has your name in it.
        alias.adjust_rep(contract.patron,
                         max(1, round(8 * appearance.rep_mult(memorable))))
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
            'accepted': self.accepted, 'hired': self.hired,
            'visited': sorted(self.visited),
            'counters': sorted(self.counters),
            'safehouse': dict(self.safehouse),
            'tables': dict(self.tables),
            'next_cid': self.next_cid,
            'stock': {k: [l.to_dict() for l in v] for k, v in self.stock.items()},
            'stock_shift': self.stock_shift,
            'pending': [p.to_dict() for p in self.pending],
            'rivals': [r.to_dict() for r in self.rivals],
            'news': list(self.news[-NEWS_KEPT:]),
            'events_seen': sorted(self.events_seen),
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
            hired=d.get('hired', ''),
            visited=set(d.get('visited') or ()),
            counters=set(d.get('counters') or ()),
            safehouse=dict(d.get('safehouse') or {}),
            tables={k: int(v) for k, v in (d.get('tables') or {}).items()},
            next_cid=int(d.get('next_cid', 1)),
            stock={k: [Listing.from_dict(l) for l in v]
                   for k, v in (d.get('stock') or {}).items()},
            stock_shift=int(d.get('stock_shift', -999)),
            pending=[PendingFallout.from_dict(p) for p in (d.get('pending') or [])],
            rivals=[rival_mod.Rival.from_dict(r)
                    for r in (d.get('rivals') or [])] or rival_mod.seed_pool(),
            news=list(d.get('news') or []),
            events_seen=set(d.get('events_seen') or ()),
        )
