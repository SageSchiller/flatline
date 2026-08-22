"""Programs. What you actually carry, per D12.

Memory is the binding constraint on playstyle. You will never have enough, and
the decision about what to load, made before the run and informed by legwork,
is the most frequent interesting decision in the game.

Every program carries a **signature**: how loud it is to use. This is
deliberately not correlated with rating. The best breaker in the game is also
the loudest, and the quietest one is barely adequate, so "bring the strongest
thing" is not automatically correct and a stealth loadout is not simply a
weaker loadout.

Categories map onto verbs. A program does nothing on its own; it is what a verb
reaches for. `crack` needs a breaker, `mask` needs a mask, and a build carrying
no wiper can still run, it just cannot clean up after itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: category -> what it is for, and which verbs reach for it.
CATEGORIES: dict[str, tuple[str, tuple[str, ...]]] = {
    'breaker': ('Defeats services and access controls.', ('crack', 'chain')),
    'hunter': ('Finds things: nodes, services, ICE, data.', ('scan', 'probe', 'map')),
    'mask': ('Suppresses trace and noise.', ('mask', 'nullsig', 'connect')),
    'forger': ('Manufactures credentials and identity.', ('forge', 'pretext', 'impersonate')),
    'weapon': ('Damages countermeasures.', ('strike', 'overload', 'kill')),
    'armour': ('Absorbs what countermeasures do to you.', ('mask', 'strike')),
    'payload': ('Does the thing the contract is about.', ('deploy', 'push', 'implant')),
    'wiper': ('Removes evidence.', ('wipe', 'scrub', 'falsify')),
    'daemon': ('Acts on its own each tick.', ('daemon', 'deploy')),
}


@dataclass(frozen=True, slots=True)
class Program:
    key: str
    name: str
    category: str
    memory: int
    rating: int          # raw power, 1..6
    signature: float     # noise multiplier when used, 1.0 is baseline
    price: int
    tier: int            # 1 street, 2 professional, 3 restricted
    blurb: str
    effects: dict = field(default_factory=dict)
    #: Terse mechanical text. Shown by `load` and `inspect`.
    note: str = ''
    #: Payloads only: the objectives this one is built for (D63). Any payload
    #: will do any job, badly: one that is not built for the objective takes
    #: a penalty on the check and drags on the pull, and `jack in` says so at
    #: the door. Empty for every other category.
    jobs: tuple[str, ...] = ()


PROGRAMS: tuple[Program, ...] = (
    # -- breakers ----------------------------------------------------------
    Program('crowbar', 'Crowbar', 'breaker', 1, 2, 1.4, 300, 1,
            'Brute force with a friendly name. It works on almost everything '
            'and it tells everybody it is working.',
            note='Cheap, reliable, loud.'),
    Program('sable', 'Sable', 'breaker', 2, 3, 0.9, 1400, 1,
            'The workhorse. Quiet enough to use twice, strong enough to matter.',
            note='The default. Nobody regrets carrying Sable.'),
    Program('lattice', 'Lattice', 'breaker', 3, 4, 0.75, 4200, 2,
            'Attacks the structure of an authentication scheme rather than its '
            'implementation. Slow, elegant, nearly silent.',
            effects={'crypto_bonus': 1},
            note='Two ticks per use instead of one.'),
    Program('thunderhead', 'Thunderhead', 'breaker', 4, 6, 2.2, 9600, 3,
            'Nothing survives it. Everything hears it.',
            note='Highest rating in the game. Signature to match.'),
    Program('skeleton', 'Skeleton', 'breaker', 3, 3, 0.5, 6800, 3,
            'A key shaped like the absence of a lock. Freeport built it, and '
            'they will not say from what.',
            effects={'noise_mult': 0.9},
            note='Quietest breaker that is still worth carrying.'),

    # -- hunters -----------------------------------------------------------
    Program('blink', 'Blink', 'hunter', 1, 2, 1.0, 250, 1,
            'A scan that returns node types and nothing else. Fast and honest '
            'about its limits.',
            note='One tick, shallow.'),
    Program('cartographer', 'Cartographer', 'hunter', 3, 4, 1.3, 3100, 2,
            'Maps topology two hops out, including edges you have no business '
            'knowing about.',
            effects={'scan_depth': 1},
            note='Reveals routes, not contents.'),
    Program('auspex', 'Auspex', 'hunter', 3, 5, 0.9, 5400, 3,
            'Passive collection. It does not probe, it listens, and what it '
            'hears is everything that talks.',
            effects={'tell_lead': 1},
            note='Reveals ICE without alerting it.'),
    Program('ledgerhand', 'Ledgerhand', 'hunter', 2, 3, 0.55, 2200, 2,
            'Finds the money. Locates data assets by value rather than by '
            'location, which is how a professional decides what to steal.',
            note='Marks the highest-value asset on any mapped node.'),

    # -- masks -------------------------------------------------------------
    Program('quietcastle', 'Quietcastle', 'mask', 2, 3, 0.0, 1800, 1,
            'Wraps your traffic in something that looks like a backup job. Not '
            'convincing forever. Convincing for a while.',
            effects={'trace_mult': 0.85},
            note='Passive while loaded.'),
    Program('mirrorbox', 'Mirrorbox', 'mask', 3, 4, 0.0, 4700, 2,
            'Reflects the trace back along a path that terminates in somebody '
            'else\'s subnet.',
            effects={'trace_mult': 0.7},
            note='Passive. Stacks poorly with other masks by design.'),
    Program('nullsuit', 'Nullsuit', 'mask', 4, 6, 0.0, 11200, 3,
            'You are not there. This is expensive to be true.',
            effects={'trace_mult': 0.55, 'noise_mult': 0.8},
            note='Four memory. It costs a build, not a slot.'),

    # -- forgers -----------------------------------------------------------
    Program('handshake', 'Handshake', 'forger', 2, 3, 0.7, 1600, 1,
            'Manufactures a credential that is plausible for about ninety '
            'seconds, which is generally ninety seconds more than you need.',
            effects={'pretext_bonus': 2},
            note='Grants tier-1 access without a crack.'),
    Program('provenance', 'Provenance', 'forger', 3, 5, 0.6, 6100, 3,
            'Does not forge a credential. Forges the history that would have '
            'issued one.',
            effects={'pretext_bonus': 4},
            note='Grants tier-2 access. Survives audit.'),

    # -- weapons -----------------------------------------------------------
    Program('cudgel', 'Cudgel', 'weapon', 2, 3, 1.6, 900, 1,
            'Hits countermeasures until they stop. No subtlety, no upkeep.',
            effects={'ice_damage': 2},
            note='Reliable. Announces you to the whole segment.'),
    Program('scalpel', 'Scalpel', 'weapon', 3, 4, 0.9, 3800, 2,
            'Targets the specific routine an ICE construct uses to hold a lock, '
            'and removes only that.',
            effects={'ice_damage': 3, 'evade_bonus': 2},
            note='Breaks lock-on rather than killing. Often better.'),
    Program('banshee', 'Banshee', 'weapon', 4, 6, 2.6, 10400, 3,
            'Kills anything short of black ICE in one pass and puts the entire '
            'network into alert while it does.',
            effects={'ice_damage': 6},
            note='Escalates the alert level on use, guaranteed.'),

    # -- armour ------------------------------------------------------------
    Program('bulwark', 'Bulwark', 'armour', 2, 3, 0.0, 2100, 1,
            'Absorbs feedback before it reaches the deck. Degrades as it works.',
            effects={'ice_dr': 0.7},
            note='Passive. Good for three saves a run, then it is gone.'),
    Program('deadlight', 'Deadlight', 'armour', 3, 5, 0.0, 7300, 3,
            'Black ICE mitigation. The only reason to attempt a core without '
            'the Nerve for it.',
            effects={'ice_dr': 0.5, 'composure': 4},
            note='Passive. Specifically counters lethal countermeasures.'),

    # -- payloads ----------------------------------------------------------
    Program('siphon', 'Siphon', 'payload', 2, 3, 0.9, 1300, 1,
            'Pulls data out through the connection you already have. Slower '
            'than a bulk copy, and it does not need a bulk copy\'s privileges.',
            note='Built for exfiltration. Anything else, it does badly.',
            jobs=('exfiltrate',)),
    Program('rootcap', 'Rootcap', 'payload', 3, 4, 1.5, 4400, 2,
            'Leaves something behind that will still be there next quarter.',
            note='Built for implants. Loud, and it drags on a pull.',
            jobs=('implant',)),
    Program('revision', 'Revision', 'payload', 3, 5, 1.25, 5900, 3,
            'Edits a record so that it has always said this.',
            effects={'residue_mult': 0.8},
            note='Built for corruption. Quiet on the way out.',
            jobs=('corrupt',)),

    # -- wipers ------------------------------------------------------------
    Program('housekeeper', 'Housekeeper', 'wiper', 2, 3, 0.9, 1700, 1,
            'Removes the obvious half of what you left. The obvious half is '
            'most of it.',
            effects={'residue_mult': 0.75},
            note='One tick per node.'),
    Program('palimpsest', 'Palimpsest', 'wiper', 4, 6, 0.7, 9100, 3,
            'Does not delete logs. Rewrites them into a coherent alternative '
            'account of the evening.',
            effects={'residue_mult': 0.4},
            note='Enables `falsify` without Forensics rank 4.'),

    # -- daemons -----------------------------------------------------------
    Program('errand', 'Errand', 'daemon', 2, 2, 1.2, 2600, 2,
            'A small autonomous process that will do exactly one thing, '
            'repeatedly, until told otherwise or killed.',
            note='Holds a node or grinds a crack. Not clever.'),
    Program('choirboy', 'Choirboy', 'daemon', 4, 5, 1.8, 8700, 3,
            'Three coordinated processes that between them can run a diversion '
            'convincing enough to move a Probe off your trail.',
            effects={'evade_bonus': 3},
            note='Generates noise on a node of your choosing. Loud on purpose.'),
    # -- second wave: depth for the thin categories -----------------------
    Program('vellum', 'Vellum', 'forger', 2, 4, 0.5, 3400, 2,
            'Writes a badge that is wrong in ways only an auditor would '
            'catch, and auditors are not on shift at four in the morning.',
            effects={'pretext_bonus': 3},
            note='Quiet. Grants tier-1 access and does not survive review.'),
    Program('nom_de_guerre', 'Nom de Guerre', 'forger', 4, 6, 0.9, 9700, 3,
            'Does not forge a person. Retires one, and gives you what they '
            'left behind, which the network has no reason to question.',
            effects={'pretext_bonus': 5, 'residue_mult': 0.85},
            note='Four memory. Grants tier-2 access and holds under audit.'),
    Program('lethe', 'Lethe', 'wiper', 3, 4, 0.6, 4900, 2,
            'Does not remove the record. Removes the index, and lets the '
            'record sit there being unfindable for as long as anybody cares.',
            effects={'residue_mult': 0.6},
            note='Cheaper than Palimpsest and does not enable falsify.'),
    Program('housecall', 'Housecall', 'wiper', 1, 2, 1.3, 600, 1,
            'The free one everybody starts with. Deletes the obvious, '
            'clumsily, and leaves a deletion where the thing used to be.',
            effects={'residue_mult': 0.85},
            note='One memory. Better than nothing, and only just.'),
    Program('carapace', 'Carapace', 'armour', 4, 6, 0.0, 11800, 3,
            'A second session standing in front of the first one. Anything '
            'that reaches you has to finish with the decoy before it starts.',
            effects={'ice_dr': 0.45, 'integrity': 4},
            note='Four memory. The most expensive way to survive a core.'),
    Program('sump', 'Sump', 'armour', 1, 2, 0.0, 700, 1,
            'Bleeds feedback into the deck chassis. Cheap, and the deck is '
            'the thing that pays for it.',
            effects={'ice_dr': 0.85},
            note='One memory. Two saves a run, then it is gone.'),
    Program('understudy', 'Understudy', 'daemon', 3, 4, 1.0, 5300, 3,
            'Runs a copy of your session one node behind you, doing what you '
            'did a tick ago. Probes find it first.',
            effects={'evade_bonus': 2},
            note='Holds or makes noise. Very good at being found.'),
    Program('gleaner', 'Gleaner', 'daemon', 2, 3, 0.7, 3600, 2,
            'A patient little process that works one lock, slowly, and does '
            'not care how long you leave it there.',
            note='Grinds a service quietly. Slower than Errand, quieter.'),
    Program('drillbit', 'Drillbit', 'breaker', 2, 4, 1.8, 2900, 2,
            'Half the price of Lattice and four times the noise, because it '
            'does not attack the scheme, it attacks the machine.',
            note='Good rating, cheap, and everybody hears it.'),
    Program('tidemark', 'Tidemark', 'hunter', 2, 4, 1.1, 3300, 2,
            'Reads what a node has been doing rather than what it is. Finds '
            'the busy ones, which are the ones with something on them.',
            effects={'legwork_bonus': 1},
            note='Marks nodes by traffic, not by type.'),

    # -- third wave: gear that speaks to the newer skill lines -------------
    Program('plumbline', 'Plumbline', 'hunter', 3, 5, 0.4, 6200, 3,
            'Does not look at hosts. Looks at the gaps between them, and '
            'tells you what shape the person who built this was thinking in.',
            effects={'scan_depth': 1, 'legwork_bonus': 1},
            note='Architecture gear. Reveals structure at almost no noise.'),
    Program('dowser', 'Dowser', 'hunter', 2, 3, 0.3, 2700, 2,
            'Finds the boundary between zones without touching either side '
            'of it. Cheap, quiet, and it will not tell you what is guarding '
            'the boundary.',
            note='Marks chokepoints. Says nothing about what is on them.'),
    Program('wiretap', 'Wiretap', 'hunter', 2, 4, 0.2, 4100, 2,
            'Reads what two hosts are saying to each other. Neither of them '
            'encrypted it, because neither of them imagined you.',
            effects={'tell_lead': 1},
            note='Signal gear. The quietest reconnaissance in the game.'),
    Program('babel', 'Babel', 'forger', 3, 4, 0.4, 5100, 2,
            'Speaks whatever the node speaks, badly, with total confidence. '
            'Most authentication is a conversation and most conversations '
            'are not listening.',
            effects={'pretext_bonus': 3, 'noise_mult': 0.9},
            note='Quiet forger. Good against wardens that ask.'),
    Program('cuckoo', 'Cuckoo', 'daemon', 3, 4, 0.9, 6400, 3,
            'Sits in somebody else\'s process and answers as it. Everything '
            'that checks on that process finds it healthy and busy.',
            effects={'residue_mult': 0.8},
            note='Holds a node and makes it look normal while it does.'),
    Program('kindling', 'Kindling', 'payload', 2, 4, 1.9, 3700, 2,
            'Starts a small fault that becomes a large one somewhere nobody '
            'is watching. Sabotage gear, and it does not need you present '
            'for the interesting part.',
            note='Built for wipes. Extremely loud.',
            jobs=('wipe',)),
    Program('bellwether', 'Bellwether', 'armour', 2, 4, 0.0, 4600, 2,
            'Rings before anything reaches you. It does not stop the hit, it '
            'stops the hit being a surprise.',
            effects={'tell_lead': 1, 'ice_dr': 0.9},
            note='Passive. Trades absorption for warning.'),
    Program('anodyne', 'Anodyne', 'armour', 3, 5, 0.0, 8200, 3,
            'Sits between your nervous system and the interface and lies to '
            'both of them about how much of this is happening.',
            effects={'ice_dr': 0.6, 'composure': 5},
            note='Psyche gear. The only armour that helps against panic.'),
    Program('lodestone', 'Lodestone', 'mask', 2, 4, 0.0, 3900, 2,
            'Does not hide the signal. Moves where it appears to originate, '
            'one segment at a time, always away from you.',
            effects={'trace_mult': 0.8, 'evade_bonus': 1},
            note='Cheaper than Mirrorbox and worse at exactly one thing.'),
    Program('shrike', 'Shrike', 'weapon', 2, 4, 1.2, 4400, 2,
            'Kills small things instantly and large things not at all. '
            'Sentries and probes evaporate; a hunter does not notice.',
            effects={'ice_damage': 2},
            note='Devastating against low-rating ICE, useless above it.'),
)


BY_KEY: dict[str, Program] = {p.key: p for p in PROGRAMS}
PROGRAM_KEYS: tuple[str, ...] = tuple(BY_KEY)


def by_category(category: str) -> list[Program]:
    return [p for p in PROGRAMS if p.category == category]


def best(loaded: list[str], category: str) -> Program | None:
    """The strongest loaded program of a category, or None.

    Verbs call this rather than asking the player which program to use, because
    "which breaker" is not an interesting decision at the moment of cracking.
    The interesting decision already happened, in the loadout.
    """
    have = [BY_KEY[k] for k in loaded if k in BY_KEY and BY_KEY[k].category == category]
    return max(have, key=lambda p: p.rating) if have else None


def quietest(loaded: list[str], category: str) -> Program | None:
    """The lowest-signature loaded program of a category.

    The counterpart to `best`, used by the `--quiet` option on verbs that have
    one. Carrying both a Thunderhead and a Skeleton is a real loadout and this
    is what makes it one.
    """
    have = [BY_KEY[k] for k in loaded if k in BY_KEY and BY_KEY[k].category == category]
    return min(have, key=lambda p: (p.signature, -p.rating)) if have else None
