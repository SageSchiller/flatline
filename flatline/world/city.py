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

#: A runner's loan: how often they mention it, and what a mention costs.
TAB_NAG = 9
TAB_NAG_COST = 3

#: The posture a first board must offer something at or below (D64 c).
SOFT_POSTURE = 30

#: A standing arrangement with a faction (D65): how often the number comes
#: round, how much danger it takes off their streets, the tier their people
#: stop at while it stands, the base of the rate, and the heat a missed
#: payment costs on top of the arrangement ending.
ARRANGE_EVERY = 6
ARRANGE_EASE = 25
#: What a contract finished after its date pays, as a share of the fee.
LATE_SHARE = 0.6
ARRANGE_TIER_CAP = 2
ARRANGE_BASE = 300
ARRANGE_BROKEN_HEAT = 12

#: How often an ambient beat is about somebody who used to do this instead of
#: about the city. Low: the departed are a ghost story the city tells
#: occasionally, and a city that talks about nobody else would be a memorial.
REMEMBERED_CHANCE = 0.06

#: Where each kind of faction sits on the power map before a campaign moves it
#: (D124). Corps and law are entrenched; gangs and cults hold less and lose it
#: faster. The neutral middle is 50.
GRIP_BASELINE = {'corp': 70, 'law': 64, 'construct': 56, 'broker': 54,
                 'press': 50, 'collective': 48, 'cult': 45, 'gang': 42}
#: How far grip has to move off its baseline before the wire says so, and how
#: much of the gap the city closes each shift on its own.
GRIP_NEWS_AT = 14
GRIP_RECOVERY = 0.4


def grip_baseline(faction: str) -> float:
    fac = factions.BY_KEY.get(faction)
    return float(GRIP_BASELINE.get(fac.kind if fac else '', 50))


#: A run that goes clean gets, sometimes, a line that lets you feel like you
#: are good at this (D125). The grimdark needs light to throw its shadow, and
#: the light this game can afford is the deadpan kind: not a hacker in
#: sunglasses, a professional enjoying, privately, being a professional.
SWAGGER = (
    'You were out before the log finished the sentence it was writing about '
    'you.',
    'Clean. The kind of clean that has somebody in a chair somewhere insisting '
    'to their supervisor that nothing happened, because the alternative is '
    'saying what did.',
    'Nobody will ever know it was you, which is the second best feeling, a '
    'long way behind the first, which is knowing it was.',
    'That went the way you said it would, out loud, to nobody, on the way in.',
    'Somewhere a very expensive system is generating a report that concludes, '
    'at length and with confidence, that everything is fine.',
)

#: How many runs before the city starts telling stories about you, and how
#: often it does once it has started.
LEGEND_AFTER = 5
LEGEND_CHANCE = 0.14

#: The city, talking about you, when you are not there. Earned cool, kept dry.
LEGEND = (
    'Somebody in Marrow described a run to somebody else. It was one of yours. '
    'They got the details wrong in your favour.',
    'A name that might be yours is being used as a verb by people who have '
    'never met you.',
    'Somebody turned down a job on the grounds that it was probably already '
    'spoken for. It was not. You are becoming a reason things do not happen.',
    'A fixer quoted a price, then quoted a higher one for the same job without '
    'you, unprompted, on the theory that anybody who is not you is a '
    'downgrade.',
    'There is an argument going in a bar in the Ninth about whether you are '
    'one person. You would not settle it if you were there, which you might '
    'be. Nobody is sure what you look like, and you intend to keep it that '
    'way.',
)


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
    #: Somebody who runs with you permanently: `{key, runs}`. See the crew
    #: section of `content/rivals.py`. A hire is a transaction and cannot be
    #: lost; somebody standing next to you on the thirtieth run is a different
    #: kind of thing, and the reason to build it is what happens when they do
    #: not come out.
    crew: dict = field(default_factory=dict)
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
    #: rival key -> [credits owed, shift it was lent]. A runner's loan is a
    #: tab, not a gift: they mention it every `TAB_NAG` shifts it stands,
    #: and the mentioning costs you their opinion. `ask <name> repay`.
    tabs: dict = field(default_factory=dict)
    #: The street (D65): the shift Bolt was last used, the errand being
    #: carried (`{kind, to, pay, hot, from, what}` or `{}`), and how many
    #: have been done.
    bolted: int = -1
    errand: dict = field(default_factory=dict)
    errands_done: int = 0
    #: Standing arrangements with factions on the street (D65): faction ->
    #: {'rate': credits every ARRANGE_EVERY shifts, 'paid': the shift it was
    #: last paid}. While one stands their people lean rather than take.
    arrangements: dict = field(default_factory=dict)
    #: The last street encounter's key, so the next is a different one.
    last_street: str = ''
    #: The shift before which `jack in` is refused: a severed connection
    #: keeps you out of the chair for a while (D6, D88).
    grounded: int = -1
    #: Titles finished recently, which the board does not post again at
    #: once: "Courtesy Call" twice running read as a copy (D88).
    done_titles: list = field(default_factory=list)
    #: faction -> the construct that cut you loose last time (D89). Their
    #: next network runs it on the route, awake.
    grudges: dict = field(default_factory=dict)
    #: faction -> the shift you left a way in on their network (D123). The
    #: next run on them starts past the wall, until they find it and it burns.
    backdoors: dict = field(default_factory=dict)
    #: faction -> its grip on the city (D124), 0 to 100, drifting from a
    #: baseline as it is robbed and preyed on and as it recovers. The power
    #: map that a campaign actually moves; `world` reads it.
    grip: dict = field(default_factory=dict)
    #: Tonight, outside (D133): a `conditions.Night` key while it is night.
    tonight: str = ''
    #: The pit's ledger (D134): rank, the night last fought, the names
    #: beaten, whether the wall is yours.
    pit: dict = field(default_factory=dict)
    #: The deck in the city (D135): mail read, things watched, and what
    #: has been said this cycle (watch pings, messages sent).
    mail_read: list = field(default_factory=list)
    watches: list = field(default_factory=list)
    messaged: dict = field(default_factory=dict)
    #: The record (D142): fights won and doorways held for somebody.
    fights_won: int = 0
    doorways: int = 0
    #: Errands already taken this window, as 'district:window:index' (D101):
    #: a collection at the same door paid nine times in one shift.
    errands_taken: set = field(default_factory=set)
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
                debt=None, char=None, satisfied=None,
                flags=None, dead=(), lender: str = '') -> list[str]:
        """Move time forward. Returns everything the player should be told.

        `satisfied` is the story's rule check bound to the game and `flags`
        its flag set: the city does not hold the story, but D51 has the
        street and the board read what the player decided, so both are
        handed in by whoever spends the shift.
        """
        told: list[str] = []
        self.ambient = []
        for _ in range(max(1, shifts)):
            self.shift += 1
            riders = char.riders() if char is not None else ()
            # Tonight, outside (D133): drawn when the night comes in,
            # cleared when it goes.
            if self.phase == 'night' and not self.tonight:
                from ..content import conditions as cond_content
                night = cond_content.pick_night(rng('nights'))
                if night is not None:
                    self.tonight = night.key
                    if flags is not None:
                        flags.add(f'night:{night.key}')
                    told.append(f'[warn]{night.name}.[/] {night.blurb}')
            elif self.phase != 'night' and self.tonight:
                self.tonight = ''
            # The water, settled (D143). Once, and the city keeps going.
            if flags is not None and 'dw_settled' not in flags:
                told.extend(self._settle_deepwater(flags))
            alias.decay_heat(
                1.4 if 'no_history' in riders
                else 1.5 if 'vouched_for' in riders
                else 1.0,
                cover=char.cover if char is not None else 0)
            self._decay_posture()
            told.extend(self._apply_pending(alias))
            told.extend(self._expire(alias))
            told.extend(self._rival_turn(rng, alias, flags))
            told.extend(fallout_mod.bounty_check(alias, self, rng('events')))
            # Arrangements come round (D65). Paid from the account; missed,
            # they end, and the ending is remembered.
            if char is not None:
                for key, deal in list(self.arrangements.items()):
                    if self.shift - int(deal.get('paid', 0)) < ARRANGE_EVERY:
                        continue
                    rate = int(deal.get('rate', 0))
                    fac = factions.BY_KEY.get(key)
                    short = fac.short if fac else key
                    if char.credits >= rate:
                        char.credits -= rate
                        deal['paid'] = self.shift
                        told.append(f'[dim]Your arrangement with {short}: '
                                    f'{rate:,}c, collected.[/]')
                    else:
                        del self.arrangements[key]
                        alias.add_heat(key, ARRANGE_BROKEN_HEAT)
                        told.append(f'[err]You could not pay {short}. The '
                                    f'arrangement is over, and they remember '
                                    f'that it was you who ended it.[/]')
            # A warning on the street stands as long as the threat does
            # (D65). When a faction has stopped paying and stopped caring,
            # the sentence "next time they will not be asking" lapses with
            # them; the next number on your name starts the ladder again.
            if flags is not None:
                for key in [f for f in flags if f.startswith('warned:')]:
                    who = key[7:]
                    if (who in factions.BY_KEY and who not in self.bounties
                            and alias.attention(who) < 25):
                        flags.discard(key)
                        told.append(f'[dim]{factions.BY_KEY[who].short} have '
                                    f'stopped looking. What they told you in '
                                    f'the street no longer stands.[/]')
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
                said = self.refresh_stock(rng)
                if char is not None and getattr(char, 'runs', 0) >= 3:
                    told.extend(said)
            self.ambient.extend(self._ambient(rng, satisfied))
            # Once you are worth a story, the city occasionally tells one
            # about you when you are not there (D125). One per window, and
            # never on top of another ambient beat, so it stays a rumour and
            # not a running commentary.
            if (not self.ambient and alias.runs >= LEGEND_AFTER
                    and rng('events').chance(LEGEND_CHANCE)):
                line = rng('events').pick(LEGEND)
                self.ambient.append(f'[dim]{line}[/]')
                told.append(f'[dim]{line}[/]')
        # Top the board back up rather than replacing it, so a contract the
        # player was saving does not vanish because a shift ticked over.
        told.extend(self.top_up_board(rng, alias, char, flags, dead, lender))
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

    def _ambient(self, rng: Rng, satisfied=None) -> list[str]:
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
                                   self.events_seen, satisfied)
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
        # Grip drifts back toward baseline the same way (D124): a hold on the
        # city that was lost is regained slowly, so a campaign leaves a mark
        # that fades rather than one that snaps back the next shift.
        for key in list(self.grip):
            base = grip_baseline(key)
            cur = self.grip[key]
            if cur < base:
                self.grip[key] = min(base, cur + GRIP_RECOVERY)
            elif cur > base:
                self.grip[key] = max(base, cur - GRIP_RECOVERY)

    def _apply_pending(self, alias: Alias) -> list[str]:
        told: list[str] = []
        still: list[PendingFallout] = []
        for item in self.pending:
            if item.due > self.shift:
                still.append(item)
                continue
            if item.heat:
                alias.add_heat(item.faction, item.heat)
            moved = ''
            if item.posture:
                base = factions.BY_KEY[item.faction].posture
                before = self.posture.get(item.faction, base)
                self.posture[item.faction] = min(100, before + item.posture)
                after = self.posture[item.faction]
                if int(after) != int(before):
                    # The number and the cause (D97): "their posture is up"
                    # said nothing a player could price.
                    moved = (f' [dim]Posture {int(before)} to {int(after)}, '
                             f'because of you.[/]')
            if item.note:
                told.append(item.note + moved)
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

        take = debt.assess()
        stream = rng('events')
        if char is not None and char.credits >= take:
            char.credits -= take
            debt.settle(take, self.shift)
            told.append(f'[heat]{stream.pick(debt_mod.COLLECT_LINES)}[/] '
                        f'[dim]{take:,}c. {debt.amount:,}c outstanding.[/]')
            self.news.append(f'[heat]{factions.BY_KEY[debt.lender].short if debt.lender in factions.BY_KEY else "The lender"} took '
                             f'{take:,}c.[/] [dim]{debt.amount:,}c '
                             f'outstanding.[/]')
        elif char is not None:
            # Nothing in the account, so they take it out of the room. This
            # routes through the same ladder as everything else, per D6.
            # What they take out of the room counts, at their rate: the
            # cash first, and the incident for half of what the cash did
            # not cover. Before this the debt dropped by the whole visit
            # whether or not a credit changed hands, which made an empty
            # account the cheapest way to pay.
            paid = max(0, min(char.credits, take))
            char.credits -= paid
            in_kind = (take - paid) // 2
            debt.settle(paid + in_kind, self.shift)
            incident = fallout_mod.pick_up(stream, char, alias,
                                           self, debt.lender)
            told.append(f'[err]{debt_mod.IN_KIND}[/]')
            told.append(f'[err]{incident.text}[/]')
            if incident.detail:
                told.append(incident.detail)
            told.append(f'[dim]They count it at {paid + in_kind:,}c against '
                        f'{take:,}c asked. {debt.amount:,}c outstanding.[/]')
        else:
            debt.settle(take, self.shift)
        return told

    def _rival_turn(self, rng: Rng, alias: Alias | None = None,
                    flags=None) -> list[str]:
        """The other runners work. This is why sitting still is not free.

        `flags` is the story's flag set when the caller has one: a bond
        latching is written into it as `bond:<runner>:<kind>`, which is how
        the runner's scene finds out (D56), and a nemesis you have paid off
        stops acting.
        """
        if not self.rivals:
            self.rivals = rival_mod.seed_pool()
        # A held contract is a story beat, and a story beat a rival can walk
        # off with is one the player may never see. They do not see it.
        taken, told = rival_mod.take_turn(
            rng('rivals'), self.rivals,
            [c for c in self.board if not c.held], self.posture, self.shift,
            protected=self.accepted,
            busy={self.hired} if self.hired else None)
        if taken:
            gone = {c.cid for c in taken}
            self.board = [c for c in self.board if c.cid not in gone]
            # The other runners move the power map too (D124): every job that
            # gets run is a bite out of somebody, whoever ran it.
            for contract in taken:
                crossed = self.bump_grip(contract.target, -2)
                if crossed:
                    told.append(crossed)
                    self.news.append(crossed)
        # Anybody who has just made up their mind about you says so, once.
        for rival, kind in rival_mod.check_bonds(self.rivals):
            told.append('')
            told.append(f'[accent2]{rival.name} has decided something about '
                        f'you.[/]')
            told.append(rival_mod.declare(rival, kind))
            if flags is not None:
                flags.add(f'bond:{rival.key}:{kind}')
        if alias is not None:
            told.extend(rival_mod.bond_turn(rng('rivals'), self.rivals, alias,
                                            flags or ()))
        # The mentioning is the interest. Every TAB_NAG shifts a tab stands,
        # the runner who lent it says something, and it costs you.
        for key, (amount, since) in list(self.tabs.items()):
            rival = self.rival(key)
            if rival is None or not rival.alive or amount <= 0:
                continue
            stood = self.shift - since
            if stood > 0 and stood % TAB_NAG == 0:
                rival.adjust_disposition(-TAB_NAG_COST)
                told.append(f'[warn]{rival.name} mentions the {amount:,}c. '
                            f'Lightly. In front of somebody.[/] [dim]`ask '
                            f'{rival.key} repay`.[/]')
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
                continue
            if contract.expired(self.shift) and contract.cid == self.accepted:
                # The one you accepted is protected from the sweep, which
                # is right: losing a job out from under somebody mid-walk
                # is not a thing the city should do quietly. It should not
                # be silent about it either. Said once, when it happens,
                # because a board reading `-68sh` is the alternative and
                # that is what it read before (D75).
                if 'late:' + contract.cid not in self.counters:
                    self.counters.add('late:' + contract.cid)
                    told.append(f'[warn]{contract.title} is past its date. '
                                f'{contract.patron_data.short} have stopped '
                                f'expecting it.[/] [dim]Still yours to '
                                f'finish or `drop`.[/]')
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
        if char is not None and 'known_quantity' in char.riders():
            size += 1  # Known quantity
        return size

    def refresh_board(self, rng: Rng, alias: Alias, char=None,
                      flags=None) -> None:
        self.board = contract_mod.generate_board(
            rng('contracts'), self.shift, alias, self.posture,
            count=self.board_size(char), start_id=self.next_cid, flags=flags)
        self.next_cid += len(self.board) + 1
        self._ensure_startable(rng, alias, char, flags)

    #: A runner with fewer than this many jobs behind them is still being
    #: taught the game, and the board keeps something they could attempt.
    #: After it, the city stops making allowances (D75).
    EARLY_RUNS = 5

    #: The hardest posture that counts as startable while they are young.
    YOUNG_POSTURE = 36

    def _ensure_lender_work(self, rng: Rng, alias: Alias, char, lender: str,
                            dead=()) -> None:
        """Somebody you owe posts work you can do (D100). The Indentured
        line is running to afford them, and in fifty-seven shifts the
        honest run saw three Kagawa jobs it could take. One held for you,
        soft, whenever the board has none."""
        if not lender or lender not in factions.BY_KEY or char is None:
            return
        posture_of = lambda k: int(self.posture.get(k, factions.BY_KEY[k].posture))
        ceiling = 30 + 5 * int(getattr(char, 'runs', 0))
        if any(c.patron == lender and c.cid not in dead
               and posture_of(c.target) <= ceiling
               for c in self.board):
            return
        spare = [i for i, c in enumerate(self.board)
                 if not c.held and c.cid != self.accepted]
        if not spare:
            return
        index = next((i for i in spare if self.board[i].cid in dead),
                     spare[-1])
        fac = factions.BY_KEY[lender]
        targets = [k for k in factions.FACTION_KEYS
                   if k != lender and fac.relations.get(k, 0) < 0
                   and posture_of(k) <= ceiling]
        if not targets:
            targets = [k for k in factions.FACTION_KEYS
                       if k != lender and posture_of(k) <= ceiling]
        if not targets:
            return
        target = min(targets, key=posture_of)
        kind = next((o for o in ('surveil', 'exfiltrate', 'corrupt', 'wipe')
                     if contract_mod.objective_ready(char, o,
                                                     posture_of(target))),
                    'surveil')
        self.board[index] = contract_mod.make_one(
            rng('contracts'), self.next_cid, lender, target,
            self.shift, alias, self.posture,
            used={c.title for i, c in enumerate(self.board) if i != index}
            | set(self.done_titles),
            objective=kind, size_mod=0.75)
        self.next_cid += 1

    def _ensure_startable(self, rng: Rng, alias: Alias, char, flags=None,
                          dead=()) -> None:
        """Keep one job on the board a young runner could actually take.

        The curated first board was a cliff rather than a ramp: the
        soft-small-ready guarantee fired at `runs == 0` and never again, so
        the second board was pure chance. One playthrough drew five `large`
        postings at postures twenty-eight to fifty-eight and the advice
        recommended Nightwatch at forty-eight to somebody with Intrusion 2
        and a Crowbar. The size distribution was fine; nothing was watching
        the *board* for whether it had a rung on it.

        Run zero keeps the stricter promise, because a first night that
        goes wrong has nothing behind it to absorb the cost. Runs one to
        four get the weaker one: something they are equipped for, at a
        posture that is not a corporation. After that the city is the city.
        """
        if char is None or not self.board:
            return
        runs = int(getattr(char, 'runs', 0))
        if runs >= self.EARLY_RUNS:
            return
        first = runs == 0
        ceiling = SOFT_POSTURE if first else self.YOUNG_POSTURE

        def startable(c) -> bool:
            if int(c.posture) > ceiling:
                return False
            # A job that has already ended on this character is not a
            # rung, and nor is one whose doors read shut for what they
            # carry (D91): a courier at Intrusion 0 had a board of five
            # rows, one of them "startable" by the old rule, and it was
            # the one that had just burned them on the chair.
            if c.cid in dead:
                return False
            if contract_mod.door_odds(char, int(c.posture)) < contract_mod.DOOR_TIGHT:
                return False
            # Size counts too. A large network at a soft posture is not a
            # hard job, but it is a long one, and a runner four contracts
            # old walking a sprawl is spending forty ticks of trace to
            # learn that. The first night wants small; the ones after it
            # want no bigger than ordinary.
            # Size steps up with the runs behind them, not the moment the
            # first one is over. Handing a one-contract runner an ordinary
            # network was the whole of the early economy: measured, run one
            # paid every time and run two paid twice in six (D82).
            if c.size_mod > (0.8 if runs < 3 else 1.0):
                return False
            return contract_mod.objective_ready(char, c.objective,
                                                int(c.posture))

        if any(startable(c) for c in self.board):
            return
        # Replace the last posting that is nobody's yet: a held one came
        # out of a scene and taking its slot would delete a story beat.
        spare = [i for i, c in enumerate(self.board)
                 if not c.held and c.cid != self.accepted]
        if not spare:
            return
        # The slot that is dead to them first, and a fresh id: the rung
        # used to inherit the id of the posting it replaced, so a job that
        # had burned somebody on the chair came back as a new job the
        # history still called dead (D91).
        index = next((i for i in spare if self.board[i].cid in dead),
                     spare[-1])
        old = self.board[index]
        # A doable rung, but not the same fingerprint every night (D114). The
        # old rule always took the single lowest-posture faction (Sixes) and
        # the first ready objective (surveil), so the soft slot read as a
        # template across every seed. Pick among the soft factions a young
        # runner can actually start against, and among the objectives they
        # can run, so the guarantee holds while the face of it rotates.
        stream = rng('contracts')

        def _post(k):
            return int(self.posture.get(k, factions.BY_KEY[k].posture))
        soft_pool = sorted(
            k for k in factions.FACTION_KEYS
            if _post(k) <= ceiling
            and contract_mod.door_odds(char, _post(k))
            >= contract_mod.DOOR_TIGHT)
        soft = stream.pick(soft_pool) if soft_pool else min(
            factions.FACTION_KEYS, key=_post)
        posture = _post(soft)
        patron = next((k for k in factions.FACTION_KEYS
                       if k != soft
                       and factions.BY_KEY[k].relations.get(soft, 0) < 0),
                      old.patron)
        ready = [o for o in ('surveil', 'exfiltrate', 'corrupt', 'wipe')
                 if contract_mod.objective_ready(char, o, posture)]
        kind = stream.pick(ready) if ready else 'surveil'
        self.board[index] = contract_mod.make_one(
            rng('contracts'), self.next_cid, patron, soft,
            self.shift, alias, self.posture,
            used={c.title for i, c in enumerate(self.board) if i != index}
            | set(self.done_titles),
            objective=kind, size_mod=0.75 if runs < 3 else 1.0)
        self.next_cid += 1

    def top_up_board(self, rng: Rng, alias: Alias, char=None,
                     flags=None, dead=(), lender: str = '') -> list[str]:
        want = self.board_size(char)
        # Held contracts sit on top of the board rather than in it, so a
        # scene that posts something does not cost the player a slot.
        have = len([c for c in self.board if not c.held])
        if have >= want:
            # Still worth asking whether there is a rung on it. A full
            # board is exactly the case where nothing new arrives to be a
            # rung, and it is the case that stranded a runner for two days
            # of play.
            self._ensure_startable(rng, alias, char, flags, dead)
            self._ensure_lender_work(rng, alias, char, lender, dead)
            return []
        fresh = contract_mod.generate_board(
            rng('contracts'), self.shift, alias, self.posture,
            count=want - have, start_id=self.next_cid,
            avoid={c.title for c in self.board} | set(self.done_titles),
            flags=flags)
        self.next_cid += len(fresh) + 1
        self.board.extend(fresh)
        self._ensure_startable(rng, alias, char, flags, dead)
        self._ensure_lender_work(rng, alias, char, lender, dead)
        return [f'[dim]{len(fresh)} new posting'
                f'{"s" if len(fresh) != 1 else ""} on the board.[/]']

    def post_story(self, rng: Rng, alias: Alias, posting, tag: str):
        """Put a scene's contract on the board, once. Returns it. D52."""
        existing = next((c for c in self.board if c.story == tag), None)
        if existing is not None:
            return existing
        contract = contract_mod.make_story(
            rng('contracts'), self.next_cid, posting, tag, self.shift, alias,
            self.posture)
        self.next_cid += 1
        self.board.append(contract)
        return contract

    def withdraw_story(self, tag: str) -> str:
        """Take a scene's contract off the board for good (D144).

        A held posting does not expire, which was the point, and it went on
        not expiring after the story it belonged to had ended: the offer
        came, was answered, and `now` still said `jack in` on a log nobody
        needed any more. Returns a line for the wire, or '' if there was
        nothing to take down.
        """
        gone = next((c for c in self.board if c.story == tag), None)
        if gone is None:
            return ''
        self.board = [c for c in self.board if c.cid != gone.cid]
        if self.accepted == gone.cid:
            self.accepted = ''
        line = (f'[dim]{gone.title} is off the board. Nobody says who took '
                f'it down, and it does not come back.[/]')
        self.news.append(line)
        return line

    def contract(self, cid: str) -> Contract | None:
        return next((c for c in self.board if c.cid == cid), None)

    @property
    def current(self) -> Contract | None:
        return self.contract(self.accepted) if self.accepted else None

    # -- market --------------------------------------------------------

    def refresh_stock(self, rng: Rng) -> list[str]:
        stream = rng('market')
        self.stock = {d.key: market_mod.restock(stream, d.key, self.shift)
                      for d in districts.DISTRICTS}
        self.stock_shift = self.shift
        # The word on the street about the two shelves that decide hard
        # work (D98). Said on the cycle, so a player who has seen the
        # corporate wall knows where to walk.
        told: list[str] = []
        parts = []
        for category in ('mask', 'forger'):
            where = market_mod.shelf_for(self.stock, category)
            if not where:
                # Seven markets turning through eight categories miss one
                # some cycles, and the two that decide hard work are not
                # allowed to be the one missed.
                shops = [d for d in districts.DISTRICTS
                         if 'market' in d.services
                         and d.max_tier >= market_mod.SHELF_TIER]
                pool = [p for p in market_mod.programs.by_category(category)
                        if not p.unique and p.tier == market_mod.SHELF_TIER]
                if shops and pool:
                    shop = shops[(self.shift // market_mod.REFRESH) % len(shops)]
                    best = max(pool, key=lambda p: (p.rating, -p.price))
                    self.stock.setdefault(shop.key, []).append(
                        market_mod.Listing(
                            kind='program', key=best.key,
                            price=max(1, int(round(best.price
                                                   * shop.price_mult))),
                            stock=1))
                    where = market_mod.shelf_for(self.stock, category)
            if where:
                key, p = where[0]
                parts.append(f'{p.name} in {districts.BY_KEY[key].name}')
        if parts:
            line = ('[dim]The word on the shelves this cycle: '
                    + ', '.join(parts) + '.[/]')
            told.append(line)
            if self.shift > 0:
                # Not on day one: the wire is empty until the city has
                # done something.
                self.news.append(line)
        # And then put back what people keep under their own counters, which
        # is not stock and does not turn over.
        from ..content import npcs as npc_content, offers
        for key in sorted(self.counters):
            stock = offers.BY_NPC_STOCK.get(key)
            npc = npc_content.BY_KEY.get(key)
            if stock is None or npc is None:
                continue
            self._shelve(stock, npc.where or self.where)
        return told

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
        to a refusal is worse than being told nothing. One shift is `travel`;
        more than one is `walk`, which is the same thing repeated and stops
        when the street stops you (D57).
        """
        route = self.route(target)
        if len(route) == 1:
            return f'travel {route[0]}'
        return f'walk {target}' if route else ''

    def danger(self, alias: Alias, target: str, rng: Rng | None = None,
               flags=None, riders=None):
        """How risky arriving in a district is, given who is looking for you.

        Lives in `world/fallout.py` so that travel, legwork, and anything else
        that puts you on a street ask exactly the same question. `flags` is
        the story's flag set, because what you decided about a faction is
        part of the answer (D51).
        """
        stream = rng('events') if rng is not None else None
        if stream is None:
            # Scoring is deterministic and needs no draws; the stream is only
            # threaded for callers that go on to resolve an incident.
            from ..rng import Rng as _Rng
            stream = _Rng(0)('events')
        return fallout_mod.arrival_risk(stream, alias, self, target,
                                        flags or (), riders=riders or ())

    def _settle_deepwater(self, flags) -> list[str]:
        """What the city does about the main line having ended (D143).

        The endings used to move a contract weight and nothing else, so a
        campaign\'s last decision changed the board and not the world. This
        is the world: who gained, who lost, and the city saying so once.
        """
        endings = {
            'dw_employed': (('deepwater', 10), ('kagawa', 6),
                            '[warn]Something in the water has been given a '
                            'budget line.[/] Nobody will say whose.'),
            'dw_published': (('static', 14), ('kagawa', -12),
                             '[warn]The Stacks ran the nine logs.[/] For '
                             'eleven days it is the only thing anybody says '
                             'to anybody.'),
            'dw_refused': (('deepwater', -4), ('kagawa', -2),
                           '[dim]Nothing happens about the water. That is '
                           'not the same as nothing having happened.[/]'),
            'dw_stayed': (('deepwater', -4), ('kagawa', -2),
                          '[dim]Nothing happens about the water. That is '
                          'not the same as nothing having happened.[/]'),
        }
        for flag, (gain, loss, line) in endings.items():
            if flag not in flags:
                continue
            flags.add('dw_settled')
            told = [line]
            # The posting with your name on it comes down with the ending
            # (D144), for a save that answered the offer before this did.
            taken = self.withdraw_story('deepwater.posting')
            if taken:
                told.append(taken)
            for key, delta in (gain, loss):
                news = self.bump_grip(key, delta)
                if news:
                    told.append(news)
            self.news.append(line)
            return told
        return []

    # -- consequences --------------------------------------------------

    def grip_of(self, faction: str) -> float:
        return self.grip.get(faction, grip_baseline(faction))

    def bump_grip(self, faction: str, delta: float) -> str:
        """Move a faction's hold on the city (D124), and say so when it
        crosses a line off its baseline. Returns a wire line, or ''."""
        base = grip_baseline(faction)
        before = self.grip.get(faction, base)
        after = max(0.0, min(100.0, before + delta))
        self.grip[faction] = after
        short = factions.BY_KEY[faction].short
        if before > base - GRIP_NEWS_AT >= after:
            return (f'[heat]{short} is losing its grip. The people who watched '
                    f'it happen are already moving into the gap.[/]')
        if before < base + GRIP_NEWS_AT <= after:
            return (f'[dim]{short} is ascendant. Doors that were shut a month '
                    f'ago are open, and the ones that were open cost more.[/]')
        return ''

    def apply_run(self, alias: Alias, summary: dict, rng: Rng,
                  memorable: int = 0, heat_mult: float = 1.0) -> list[str]:
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

        learned_clean = 0.0
        if outcome == 'clean' and summary.get('objective'):
            gain = 6 + summary.get('haul_value', 0) // 900
            learned_clean = fac.hardening
            told.append(f'[ok]Work recorded.[/] {gain} standing with your patron.')
            # A job done is a bite out of their hold on the city (D124),
            # bigger the bigger the haul. This is the campaign moving.
            crossed = self.bump_grip(target,
                                     -(4 + summary.get('haul_value', 0) // 1400))
            if crossed:
                told.append(crossed)
                self.news.append(crossed)
            # And, sometimes, a moment to enjoy being good at it (D125).
            if rng('events').chance(0.4):
                told.append(f'[dim]{rng("events").pick(SWAGGER)}[/]')

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
            heat *= heat_mult

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
                # A failed attempt teaches them something: less if you
                # never got past the front (D97). Seven failed attempts at
                # one held job took Deepwater from 72 to 96, which made the
                # job unwinnable by trying it.
                learned = fac.hardening * (0.4 if summary.get('reached')
                                           else 0.15)
                # One line per run (D101): the clean hardening and the
                # residue's were two items and two lines.
                self.pending.append(PendingFallout(
                    due=self.shift + RESIDUE_DELAY, faction=target,
                    heat=heat, posture=learned + learned_clean, note=note))
                learned_clean = 0.0

        if learned_clean:
            self.pending.append(PendingFallout(
                due=self.shift + RESIDUE_DELAY, faction=target,
                heat=0.0, posture=learned_clean,
                note=f'[dim]{fac.short} has changed something.[/]'))
        if outcome in ('severed', 'burned'):
            alias.add_heat(target, 12)
            told.append(f'[warn]{fac.short} logged the intrusion attempt.[/]')
        if outcome == 'flatline':
            told.append('[err]There is no city layer for this one.[/]')

        return told

    def pay_out(self, alias: Alias, contract: Contract, summary: dict,
                pay_mult: float = 1.0,
                memorable: int = 0,
                rep_mult: float = 1.0) -> tuple[int, list[str]]:
        """Settle a contract. Returns credits paid and what to tell the player.

        `rep_mult` is the character's own modifier (D63): the key was sold by
        chrome and traits and read by nothing. `heat_mult` is its twin and
        lives in `apply_run`, where the residue becomes heat."""
        told: list[str] = []
        if not summary.get('objective'):
            told.append(f'[err]{contract.patron_data.short} does not pay for '
                        f'attempts.[/]')
            alias.adjust_rep(contract.patron, -8)
            return 0, told

        pay = int(contract.pay * pay_mult)
        if contract.expired(self.shift) and not contract.held:
            # They had stopped expecting it. The board said so at the time,
            # and then paid in full anyway, which made every deadline on it
            # decoration (D87).
            pay = int(pay * LATE_SHARE)
            told.append(f'[warn]It was past its date. They pay '
                        f'{int(LATE_SHARE * 100)}% for late, and do not '
                        f'argue about it.[/]')
        if summary['outcome'] != 'clean':
            # You delivered, but they had to hear about it from somebody else.
            pay = int(pay * 0.7)
            told.append('[warn]The exit was messy. They withheld part of it.[/]')
        if summary.get('sealed'):
            # D63 b: they wanted it open. A sealed record is the job done
            # badly rather than not done, and paid like it.
            from ..run.session import SEALED_SHARE
            pay = int(pay * SEALED_SHARE)
            told.append('[warn]It came out sealed. They wanted it open, and '
                        'the fee says so.[/]')
        # Work gets attributed to somebody. Being a person worth naming means
        # the story that goes round afterwards has your name in it.
        alias.adjust_rep(contract.patron,
                         max(1, round(8 * appearance.rep_mult(memorable)
                                      * rep_mult)))
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
            'crew': dict(self.crew),
            'tables': dict(self.tables),
            'tabs': {k: list(v) for k, v in self.tabs.items()},
            'bolted': self.bolted, 'errand': dict(self.errand),
            'errands_done': self.errands_done,
            'arrangements': {k: dict(v) for k, v in self.arrangements.items()},
            'last_street': self.last_street,
            'grounded': self.grounded,
            'done_titles': list(self.done_titles),
            'grudges': dict(self.grudges),
            'backdoors': dict(self.backdoors),
            'grip': {k: round(v, 1) for k, v in self.grip.items()},
            'tonight': self.tonight,
            'pit': dict(self.pit),
            'mail_read': list(self.mail_read),
            'watches': list(self.watches),
            'messaged': dict(self.messaged),
            'fights_won': int(self.fights_won),
            'doorways': int(self.doorways),
            'errands_taken': sorted(self.errands_taken),
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
            crew=dict(d.get('crew') or {}),
            tables={k: int(v) for k, v in (d.get('tables') or {}).items()},
            tabs={k: [int(v[0]), int(v[1])]
                  for k, v in (d.get('tabs') or {}).items()
                  if isinstance(v, (list, tuple)) and len(v) == 2},
            bolted=int(d.get('bolted', -1)),
            errand=dict(d.get('errand') or {}),
            errands_done=int(d.get('errands_done', 0)),
            arrangements={k: {'rate': int(v.get('rate', 0)),
                              'paid': int(v.get('paid', 0))}
                          for k, v in (d.get('arrangements') or {}).items()
                          if isinstance(v, dict)},
            last_street=str(d.get('last_street', '') or ''),
            grounded=int(d.get('grounded', -1)),
            grudges={str(k): str(v) for k, v in (d.get('grudges') or {}).items()},
            backdoors={str(k): int(v) for k, v in (d.get('backdoors') or {}).items()},
            grip={str(k): float(v) for k, v in (d.get('grip') or {}).items()},
            tonight=str(d.get('tonight') or ''),
            pit=dict(d.get('pit') or {}),
            mail_read=list(d.get('mail_read') or []),
            watches=list(d.get('watches') or []),
            messaged={str(k): int(v) for k, v in (d.get('messaged') or {}).items()},
            fights_won=int(d.get('fights_won', 0)),
            doorways=int(d.get('doorways', 0)),
            errands_taken={str(k) for k in (d.get('errands_taken') or [])},
            done_titles=[str(t) for t in (d.get('done_titles') or [])],
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
