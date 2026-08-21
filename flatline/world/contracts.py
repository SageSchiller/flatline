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
    'surveil': 'Sit on {node} and `observe` until you have banked {ticks} '
               'clean ticks. Take nothing, break nothing.',
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
    for _ in range(count):
        patron = rng.weighted(patrons)
        target = pick_target(rng, patron, alias)
        if target is None:
            continue
        contract = make_one(rng, cid, patron, target, shift, alias,
                            posture, used)
        used.add(contract.title)
        out.append(contract)
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


def pick_target(rng: Stream, patron: str, alias) -> str | None:
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
        weights[key] = weight
    if not weights:
        return None
    return rng.weighted(weights)


def make_one(rng: Stream, cid: int, patron: str, target: str, shift: int,
          alias, posture: dict, used: set | None = None) -> Contract:
    pfac, tfac = factions.BY_KEY[patron], factions.BY_KEY[target]
    objective = rng.weighted({o: (2.5 if o in pfac.wants else 0.7)
                              for o in OBJECTIVES})

    target_posture = int(posture.get(target, tfac.posture))
    # Pay tracks difficulty first, then the patron's opinion of you.
    base = 900 + target_posture * 34
    base *= OBJECTIVE_PAY[objective]
    base *= 1.0 + alias.reputation(patron) / 150.0
    pay = rng.spread(base, 0.18)

    size_mod = rng.weighted({0.75: 1.0, 1.0: 2.5, 1.35: 1.0})
    if size_mod > 1.2:
        pay = int(pay * 1.25)
    elif size_mod < 0.9:
        pay = int(pay * 0.8)

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
