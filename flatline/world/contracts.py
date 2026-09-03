"""The contract board: work generated from what the world currently is.

Contracts are not drawn from a list. They are produced by asking, for each
patron, who they currently dislike enough to pay for, and what they want done.
That means the board *reads* as a consequence of the world: raise the
Switchboard's opinion of you and their work appears, burn Kagawa badly enough
and their rivals start offering you money to do it again.

Expiry is what makes the board a pressure rather than a menu. Contracts run out
after a few shifts, so travelling across the city to shop for a better one has
a real cost, which is the entire point of the city layer being priced in time.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..content import districts, factions
from ..rng import Stream

OBJECTIVES = ('exfiltrate', 'implant', 'corrupt', 'surveil', 'wipe', 'escort')

OBJECTIVE_BLURB = {
    'exfiltrate': 'Get a specific asset out. The classic, and still the best paid.',
    'implant': 'Leave something behind that survives the quarter.',
    'corrupt': 'Change a record so that it has always said something else.',
    'surveil': 'Stay resident and undetected. Inverts the whole risk calculation.',
    'wipe': 'Destroy an asset. Loud, fast, and it does not need you to get it out.',
    'escort': 'Cover somebody else\'s run. Their noise is not your decision.',
}

#: What finishing looks like, in the words the player will use to do it.
#:
#: `OBJECTIVE_BLURB` above is the pitch, written for somebody reading the
#: board and deciding whether to take the work. This is the brief: written for
#: somebody already inside, who needs to know what the run is for. The fields
#: are filled from the network, so the sentence names the host and the record
#: this contract is actually about rather than describing a kind of job.
#:
#: `{node}` is the objective host, `{asset}` the record on it, `{ticks}` the
#: residency a surveil job wants, `{who}` the runner an escort is covering.
OBJECTIVE_AIM = {
    'exfiltrate': 'Take {asset} off {node}, and still be holding it when you '
                  'jack out.',
    'implant': 'Get onto {node} and `push` a payload into it. It has to be '
               'that host: the money is for a foothold somewhere that '
               'matters.',
    'corrupt': 'Get onto {node} and `push` an edit into {asset}, so that it '
               'has always said what your patron wants it to say.',
    'wipe': 'Destroy {asset} on {node} with `wipe`. Nobody is paying you to '
            'carry it out, which is the whole appeal.',
    'surveil': 'Sit on {node} and `observe` until {ticks} clean ticks are '
               'banked. A tick banks while the alert is below red, and red '
               'empties every one you had, so the job is not the '
               'sitting: it is keeping the room calm while you do it.',
    'escort': 'Keep {who} alive and moving until they are done and out. '
              'Their noise is not your decision and never will be.',
}

#: What each objective needs in the loadout. Checked before `jack in` so a
#: player is told at the door rather than three zones deep.
OBJECTIVE_PROGRAM = {
    'exfiltrate': 'payload',
    'implant': 'payload',
    'corrupt': 'payload',
    'wipe': 'payload',
    'surveil': '',
    'escort': '',
}

#: What the objective verb itself is up against, by posture (D71). The run
#: builds the full itemised check; this is the resistance half of it, kept
#: here because the city has to be able to ask the same question before it
#: recommends a job. It used to live only inside `push_check` and
#: `wipe_check`, and the city's advice therefore checked whether you owned
#: a payload and not whether the payload could do anything: a fresh build
#: was reliably sent at a corruption it could not land, walked the whole
#: network, stood on the objective, and read `impossible` for the first
#: time with the trace at forty.
def objective_resistance(kind: str, posture: int) -> int:
    if kind in ('corrupt', 'implant'):
        return posture // 5 + 6
    if kind == 'wipe':
        return posture // 6 + 3
    return 0


#: What using a payload for a job it was not built for costs. The run
#: applies it as its own term after the doubling, and so does this.
IMPROVISED = 3


def objective_power(char, kind: str) -> int:
    """What a character brings to that verb, before the die.

    Counts anything owned rather than anything loaded: the loadout is a
    shop trip and a `load`, and the advice already treats gear you own as
    gear you have.
    """
    from ..content import programs as program_content
    if kind not in ('corrupt', 'implant', 'wipe'):
        return 0
    skill = 'intrusion' if kind == 'implant' else 'sabotage'
    attr = 'logic' if kind == 'implant' else 'guile'
    power = char.skill(skill) * 2 + char.attr(attr)
    owned = [program_content.BY_KEY[k]
             for k in list(char.library) + list(char.deck.loaded)
             if k in program_content.BY_KEY]
    payloads = [p for p in owned if p.category == 'payload']
    if not payloads:
        return power - 4 if kind == 'wipe' else power
    # Mirroring `push_check` and `wipe_check` exactly: the payload term is
    # doubled and *then* the improvised penalty comes off, as its own
    # term. Taking the penalty off before doubling cost three points and
    # made the estimate say impossible about jobs the real check gives you
    # thirty per cent on, which steered the advice away from work that
    # pays (D84).
    rank = char.skill(skill)
    best = max(program_content.held(p, rank) * 2
               - (0 if (not p.jobs or kind in p.jobs) else IMPROVISED)
               for p in payloads)
    return power + int(best)


#: The difficulty of the sort of service a vault runs, which is what the
#: job is behind. See `nodes.SERVICES`: keystore 5-7, sign 5-8, cipher 4-7.
VAULT_SERVICE = 5.5
#: Below this chance of a vault door the board reads it as shut, and a
#: rung for a young runner is not a rung (D91).
DOOR_TIGHT = 0.35


def door_odds(char, posture: int, rank: int | None = None) -> float:
    """The chance of one vault-grade door, with what is loaded. The
    board's reads column, and the rung the board keeps for a young
    runner, price the same door. `rank` overrides Intrusion, for a plan
    asking what one more rank would buy (D100)."""
    from ..content import programs as program_content
    from ..run.checks import DIE, OFFSET
    difficulty = max(1, round(VAULT_SERVICE * (0.45 + 0.78 * posture / 50.0)))
    breaker = program_content.best(char.deck.loaded, 'breaker')
    rank = char.skill('intrusion') if rank is None else rank
    power = rank * 2 + char.attr('logic') + char.bonus('crack_bonus')
    if breaker:
        power += program_content.held(breaker, rank) * 2
    else:
        power -= 6
    need = difficulty * 2 + OFFSET - power
    return max(0.0, min(1.0, (DIE - need + 1) / DIE))


def objective_ready(char, kind: str, posture: int) -> bool:
    """Whether this is a job they could go and do tonight.

    Two questions, and the board has to ask both. `objective_possible` is
    whether the die could carry the verb; this adds whether the thing the
    verb needs is on the deck or in the library at all. A guaranteed first
    job that wants a nine hundred credit payload from somebody holding
    seven hundred is a guaranteed first job in name only, and it sent
    people at the harder network on the board instead (D74).
    """
    from ..content import programs as program_content
    need = OBJECTIVE_PROGRAM.get(kind, '')
    if need:
        held = {program_content.BY_KEY[k].category
                for k in list(char.library) + list(char.deck.loaded)
                if k in program_content.BY_KEY}
        if need not in held:
            return False
    return objective_possible(char, kind, posture)


def objective_odds(char, kind: str, posture: int) -> float:
    """The chance the objective verb lands, with what is owned (D101).
    The same sum `push_check` and `wipe_check` roll, read before the walk:
    a build that walked through every door typed `push` seventeen times
    at ten per cent because nothing had priced the job itself."""
    from ..run.checks import DIE, OFFSET
    if kind not in ('corrupt', 'implant', 'wipe'):
        return 1.0
    need = objective_resistance(kind, posture) + OFFSET - objective_power(char, kind)
    return max(0.0, min(1.0, (DIE - need + 1) / DIE))


def objective_skill(kind: str) -> str:
    return {'corrupt': 'Sabotage', 'wipe': 'Sabotage'}.get(kind, 'Intrusion')


def objective_possible(char, kind: str, posture: int) -> bool:
    """Whether the die could carry it at all (D14: the same sum the run
    prints). A ten-sided die offset by five is five points of reach."""
    from ..run.checks import DIE, OFFSET
    return (objective_power(char, kind) + DIE - OFFSET
            >= objective_resistance(kind, posture))


#: The fee curve against posture. `PAY_BASE` is what nothing at all is
#: worth, and the rest is how steeply difficulty is priced.
PAY_BASE = 900
PAY_PIVOT = 25.0
PAY_CURVE = 1.6

#: What a job's size is worth, against the standard one. Measured rather
#: than picked (D66): a large network is about a third more hosts at the
#: front, which is a third more of the evening and a good deal more to
#: carry out of it, and the old figure of a quarter more did not cover the
#: hours. A sprawl is the top of the range and it is a night's work.
SIZE_PAY = {0.75: 0.82, 1.0: 1.0, 1.35: 1.5, 1.7: 2.1}

#: The same in one short word, for a table column.
SIZE_SHORT = {0.75: 'small', 1.0: 'usual', 1.35: 'large', 1.7: 'sprawl'}

#: What the board calls each size, and the one-line warning under it.
SIZE_WORDS = {
    0.75: ('small', 'a handful of hosts and one way in'),
    1.0: ('ordinary', 'the usual shape of a job'),
    1.35: ('large', 'a wide front and a long evening'),
    1.7: ('a sprawl', 'somebody\'s whole operation, and a night to walk it'),
}

#: Payout multiplier per objective, applied to the base rate.
OBJECTIVE_PAY = {
    'exfiltrate': 1.0, 'implant': 1.15, 'corrupt': 1.1,
    'surveil': 0.9, 'wipe': 0.85, 'escort': 1.25,
}

#: Shifts a contract stays on the board.
LIFETIME = (4, 9)

#: How many sit on the board at once, before origin and reputation bonuses.
BOARD_SIZE = 5


@dataclass(slots=True)
class Contract:
    cid: str
    patron: str
    target: str
    objective: str
    pay: int
    posted: int
    expires: int
    #: The target's posture snapshotted at generation, so a contract taken now
    #: and run in four shifts is the network you were told about.
    posture: int
    title: str
    blurb: str
    district: str
    #: Legwork already bought, per D-Phase 3. Keys are intel types.
    intel: dict = field(default_factory=dict)
    #: Set once accepted. An accepted contract leaves the board.
    taken: bool = False
    #: The person who handed you this, if it did not come off the board.
    #: Personal work pays better and costs something a posting cannot charge,
    #: which is that somebody specific is waiting for it.
    from_npc: str = ''
    size_mod: float = 1.0
    #: `thread.stage` of the scene that posted this, or ''. A story contract
    #: is held: it does not expire, rivals do not take it, and finishing it
    #: sets `did:<story>` for the scenes that come after (D52).
    story: str = ''
    #: What the objective record is called, when the scene names it.
    label: str = ''

    @property
    def held(self) -> bool:
        return bool(self.story)

    @property
    def patron_data(self) -> factions.Faction:
        return factions.BY_KEY[self.patron]

    @property
    def target_data(self) -> factions.Faction:
        return factions.BY_KEY[self.target]

    def expired(self, shift: int) -> bool:
        return shift >= self.expires

    def to_dict(self) -> dict:
        return {
            'cid': self.cid, 'patron': self.patron, 'target': self.target,
            'objective': self.objective, 'pay': self.pay, 'posted': self.posted,
            'expires': self.expires, 'posture': self.posture,
            'title': self.title, 'blurb': self.blurb, 'district': self.district,
            'intel': dict(self.intel), 'taken': self.taken,
            'from_npc': self.from_npc, 'size_mod': self.size_mod,
            'story': self.story, 'label': self.label,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Contract:
        return cls(
            cid=d['cid'], patron=d['patron'], target=d['target'],
            objective=d['objective'], pay=int(d['pay']),
            posted=int(d['posted']), expires=int(d['expires']),
            posture=int(d['posture']), title=d['title'], blurb=d['blurb'],
            district=d.get('district', districts.START),
            intel=dict(d.get('intel') or {}), taken=bool(d.get('taken')),
            from_npc=d.get('from_npc', ''),
            size_mod=float(d.get('size_mod', 1.0)),
            story=d.get('story', ''), label=d.get('label', ''),
        )


# --------------------------------------------------------------------------
# generation
# --------------------------------------------------------------------------

#: Title fragments. Assembled rather than written out so that a board of five
#: never repeats, while still reading like something a person named.
_JOB_WORDS = (
    'Housekeeping', 'Second Opinion', 'Paper Trail', 'Quiet Word',
    'Inventory', 'Courtesy Call', 'Long Weekend', 'Cold Storage',
    'Open Secret', 'Fire Drill', 'Change of Address', 'Night Shift',
    'Clean Break', 'Loose Thread', 'Small Favour', 'Due Diligence',
    'Standing Order', 'Last Resort', 'Off Books', 'Short Notice',
)


#: D51. What a decision does to who posts work, as (flag, faction,
#: multiplier on that patron's weight). Zero means they stop posting to you
#: altogether. Declared as data so `validate.py` can hold the flag to being
#: one a choice sets, and the faction to existing.
PATRON_RIDERS: tuple[tuple[str, str, float], ...] = (
    # You are on the retainer. The work arrives, and keeps arriving.
    ('dw_employed', 'deepwater', 3.0),
    # Nobody brings it up, and that includes them.
    ('dw_published', 'deepwater', 0.0),
    # Meridian paid, and did not run it, and remember who sold it.
    ('laptop_sold', 'meridian', 1.6),
    # Meridian read the public log in Freeport too.
    ('sunday_sold', 'meridian', 0.4),
    # You wiped something of theirs. They post less, and do not say why.
    ('dw_burned', 'deepwater', 0.5),
    # D55. Static ran Kagawa's DEFERRED column; Kagawa remember the byline.
    ('pumps_public', 'kagawa', 0.7),
    # You sold the water board its own ledger, and they were grateful.
    ('pumps_sold', 'kagawa', 1.3),
    # Eleven numbers moved toward each other, and Kagawa cannot find who.
    ('reviews_fair', 'kagawa', 0.8),
    # Sendai were told what was on their floor, and were efficient about it.
    ('demo_sold', 'sendai', 1.4),
    # Freeport voted your way, and the losing side bought.
    ('vote_spoke', 'freeport', 1.4),
    # Freeport voted the other way, and the Quartermaster wrote it down.
    ('vote_quiet', 'freeport', 0.6),
)


def generate_board(rng: Stream, shift: int, alias, posture: dict,
                   count: int = BOARD_SIZE, start_id: int = 1,
                   avoid: set | None = None, flags=None) -> list[Contract]:
    """Produce a fresh board from current world state.

    `avoid` is the set of titles already posted. Two jobs called Due Diligence
    on one board is not a collision the player can be expected to hold in their
    head, and it reads as a bug even though it is not. `flags` is the story's
    flag set, which decides who still posts to you (D51).
    """
    out: list[Contract] = []
    used = set(avoid or ())
    cid = start_id
    patrons = _weighted_patrons(alias, flags or ())
    #: How many jobs on one board may point at the same faction before it is
    #: discouraged. Two is a choice; four is a theme night (D114).
    target_cap = 2
    hit: dict[str, int] = {}
    for _ in range(count):
        patron = rng.weighted(patrons)
        over = {t for t, n in hit.items() if n >= target_cap}
        target = pick_target(rng, patron, alias, over=over)
        if target is None:
            continue
        contract = make_one(rng, cid, patron, target, shift, alias,
                            posture, used)
        used.add(contract.title)
        out.append(contract)
        hit[target] = hit.get(target, 0) + 1
        cid += 1
    return out


def _weighted_patrons(alias, flags=()) -> dict[str, float]:
    """Who is offering work. Standing buys access to better patrons, and
    what you decided about somebody decides whether they still call."""
    weights: dict[str, float] = {}
    for key, fac in factions.BY_KEY.items():
        rep = alias.reputation(key)
        base = 1.0
        if fac.kind == 'broker':
            base = 2.2  # the Switchboard always has something
        elif fac.kind == 'corp':
            base = 0.7  # corps hire strangers reluctantly
        # Reputation opens doors, and hostility closes them entirely.
        if rep <= -60:
            continue
        weights[key] = max(0.05, base * (1.0 + rep / 60.0))
    for flag, faction, mult in PATRON_RIDERS:
        if flag in flags and faction in weights:
            weights[faction] *= mult
            if weights[faction] <= 0:
                del weights[faction]
    return weights


def pick_target(rng: Stream, patron: str, alias, over=()) -> str | None:
    """Who the patron wants hit. Driven by the relations table."""
    weights: dict[str, float] = {}
    for key in factions.FACTION_KEYS:
        if key == patron:
            continue
        rel = factions.relation(patron, key)
        if rel > 0.1:
            continue  # you do not hire somebody to rob your friends
        # The more they dislike the target, the likelier the job.
        weight = 0.4 + abs(min(0.0, rel)) * 2.5
        # Running somebody you are trusted by is available but discouraged.
        rep = alias.reputation(key)
        if rep >= 60:
            weight *= 0.25
        # And a target already all over the board is discouraged (D114): a
        # widely-disliked corp is every patron's default, and a night of
        # five jobs against one faction is no real choice of who to hit.
        # Softly, so a thin relations table still fills the board.
        if key in over:
            weight *= 0.12
        weights[key] = weight
    if not weights:
        return None
    return rng.weighted(weights)


def make_one(rng: Stream, cid: int, patron: str, target: str, shift: int,
          alias, posture: dict, used: set | None = None,
          objective: str | None = None,
          size_mod: float | None = None) -> Contract:
    pfac, tfac = factions.BY_KEY[patron], factions.BY_KEY[target]
    if objective is None:
        objective = rng.weighted({o: (2.5 if o in pfac.wants else 0.7)
                                  for o in OBJECTIVES})

    target_posture = int(posture.get(target, tfac.posture))
    # Pay tracks difficulty first, then the patron's opinion of you.
    #
    # The curve is measured rather than picked (D66). It used to be linear,
    # nine hundred and thirty-four a point, which made a corporate network
    # pay half again what a gang's did; running two dozen of each with the
    # same build put the completion rates at about two thirds and about one
    # in six. A job you finish once in six for half again the money is not
    # a harder job, it is a worse one, and the board was quietly telling
    # every player to stay in the Ninth for ever. This pays roughly what
    # the attempt is worth: three times a gang job at corporate posture,
    # nearly four at Deepwater's.
    base = PAY_BASE * (1.0 + (target_posture / PAY_PIVOT) ** PAY_CURVE)
    base *= OBJECTIVE_PAY[objective]
    base *= 1.0 + alias.reputation(patron) / 150.0
    pay = rng.spread(base, 0.18)

    # Size, and what size is worth (D66). A bigger network is more ways in,
    # more that is not the job, and more hours: the fee has to say so, and
    # the board has to say so before you take it. Hardened targets run
    # bigger operations, so posture leans the roll.
    heavy = 1.0 + (target_posture / 100.0)
    if size_mod is None:
        size_mod = rng.weighted({0.75: 1.2, 1.0: 2.5, 1.35: 1.0 * heavy,
                                 1.7: 0.35 * heavy})
    pay = int(pay * SIZE_PAY[size_mod])

    district = _where(rng, target)
    free = [w for w in _JOB_WORDS if w not in (used or ())]
    title = rng.pick(free or _JOB_WORDS)
    blurb = _blurb(rng, patron, target, objective, pfac, tfac)

    return Contract(
        cid=f'c{cid:03d}', patron=patron, target=target, objective=objective,
        pay=int(pay), posted=shift,
        expires=shift + rng.int(*LIFETIME), posture=target_posture,
        title=title, blurb=blurb, district=district, size_mod=size_mod,
    )


#: How long a held contract lives, in shifts. Long enough to be "does not
#: expire" for any campaign, and a number rather than a flag so that the
#: ordinary expiry code never has to know it exists.
HELD = 9999


def make_story(rng: Stream, cid: int, posting, tag: str, shift: int,
               alias, posture: dict) -> Contract:
    """A contract a scene asked for. Generated like any other, then bent.

    The generator prices it, places it and draws its network exactly as it
    would a board posting against the same target, so a story run is a real
    run; what the scene fixes is who, against whom, what for, what it is
    called, and that it waits.
    """
    contract = make_one(rng, cid, posting.patron, posting.target, shift,
                        alias, posture)
    contract.objective = posting.objective
    contract.title = posting.title
    contract.blurb = posting.blurb
    contract.label = posting.label
    contract.story = tag
    contract.expires = shift + HELD
    if posting.pay:
        contract.pay = int(posting.pay)
    return contract


def _where(rng: Stream, target: str) -> str:
    """Which district the job is physically in. Prefers the target's turf."""
    home = [d.key for d in districts.DISTRICTS if d.controller == target]
    if home and rng.chance(0.7):
        return home[0]
    present = [d.key for d in districts.DISTRICTS if target in d.presence]
    if present:
        return rng.pick(present)
    return rng.pick(districts.DISTRICT_KEYS)


_FRAMES = {
    'exfiltrate': (
        '{p} wants something {t} is holding, and would rather not be seen '
        'asking for it.',
        'There is a file on a {t} network. {p} has been offered money for it '
        'by somebody they will not name.',
    ),
    'implant': (
        '{p} would like a way back into {t} that does not depend on you being '
        'available next quarter.',
        'Leave a door open on a {t} network. {p} is not going to say what for.',
    ),
    'corrupt': (
        'A record on a {t} system says something inconvenient. {p} would like '
        'it to have always said something else.',
        '{p} needs one number changed on a {t} network, and needs it to look '
        'like it was never any other number.',
    ),
    'surveil': (
        '{p} wants to know what {t} does when nobody is watching. Get in, sit '
        'still, and do not touch anything.',
        'Residency on a {t} network, undetected, for as long as you can hold '
        'it. {p} pays by what you hear.',
    ),
    'wipe': (
        'Something on a {t} network needs to stop existing. {p} does not care '
        'how loud that is.',
        '{p} wants a {t} asset destroyed rather than stolen, which is cheaper '
        'for them and worse for you.',
    ),
    'escort': (
        '{p} has somebody else going into {t} and wants them coming out. Their '
        'noise is not your decision.',
        'Cover a runner on a {t} job. {p} is paying for the other one to '
        'survive it, not for you to be comfortable.',
    ),
}


def _blurb(rng: Stream, patron: str, target: str, objective: str,
           pfac: factions.Faction, tfac: factions.Faction) -> str:
    frame = rng.pick(_FRAMES[objective])
    return frame.format(p=pfac.short, t=tfac.short)
