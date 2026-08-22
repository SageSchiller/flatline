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
    #: Engine-implemented special behaviour while loaded (D63 c). Must be in
    #: `RIDERS`, and `validate.check_reads` holds the engine to reading it.
    rider: str = ''
    #: One of a kind (D63 e). Never in a market: found somewhere, given by
    #: somebody, or handed over by a decision. `lore` is its history, shown
    #: by `inspect` and when it is found.
    unique: bool = False
    lore: str = ''


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
    Program('skeleton', 'Skeleton', 'breaker', 3, 3, 0.5, 5200, 3,
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
            note='`scan` shows what each host is worth. Finds the money before you walk to it.',
            rider='ledger_eye'),

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
            note='Passive. Only the strongest mask loaded counts: two are not twice the mask.'),
    Program('nullsuit', 'Nullsuit', 'mask', 4, 6, 0.0, 11200, 3,
            'You are not there. This is expensive to be true.',
            effects={'trace_mult': 0.55, 'noise_mult': 0.8},
            note='Four memory. It costs a build, not a slot.'),

    # -- forgers -----------------------------------------------------------
    Program('handshake', 'Handshake', 'forger', 2, 3, 0.7, 1600, 1,
            'Manufactures a credential that is plausible for about ninety '
            'seconds, which is generally ninety seconds more than you need.',
            effects={'pretext_bonus': 2},
            note='Opens a door by talking: `pretext` with it loaded. Forges the argument, not the key.'),
    Program('provenance', 'Provenance', 'forger', 3, 5, 0.6, 6100, 3,
            'Does not forge a credential. Forges the history that would have '
            'issued one.',
            effects={'pretext_bonus': 4},
            note='Forges the history behind a credential. Holds up to a warden\'s check.'),

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
            note='Every strike with it escalates the alert a level. Guaranteed.',
            rider='banshee_alarm'),

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
    Program('siphon', 'Siphon', 'payload', 2, 3, 0.9, 900, 1,
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
            note='Quiet. Opens a door by talking and leaves no paper.'),
    Program('nom_de_guerre', 'Nom de Guerre', 'forger', 4, 6, 0.9, 9700, 3,
            'Does not forge a person. Retires one, and gives you what they '
            'left behind, which the network has no reason to question.',
            effects={'pretext_bonus': 5, 'residue_mult': 0.85},
            note='Four memory. The best argument in the catalogue, and it tidies after itself.'),
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
            note='`scan` shows how busy each host is: services and data, not type.',
            rider='tide_eye'),

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
            note='`scan` marks the chokepoints: hosts on a boundary, where wardens stand.',
            rider='dowse_eye'),
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
    Program('anodyne', 'Anodyne', 'armour', 2, 5, 0.0, 6900, 3,
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
            note='Twice the bite against rating 3 and under. Nothing at all against 6 and up.',
            rider='shrike_edge'),
)


#: How far above your skill a program will run at full rating (D63 f). A
#: rating-6 breaker in the hands of Intrusion 0 runs as a rating 2: you do
#: not know how to drive it yet. This is what makes training compete with
#: buying without making the cheap programs worse: every check that reads a
#: rating reads it through `held`, and prints the term as "held to N by
#: <skill> <rank>" when it bites.
HELD_ABOVE = 2

#: Which skill holds a category, for `inspect` and for the checks that do
#: not already know (breakers are held by the service's own family skill).
HELD_BY: dict[str, str] = {
    'breaker': 'intrusion', 'forger': 'subterfuge', 'weapon': 'warfare',
    'wiper': 'forensics', 'mask': 'stealth', 'payload': 'intrusion',
}


def held(prog: Program, rank: int) -> int:
    """The rating a program runs at for somebody of this rank."""
    return max(1, min(prog.rating, rank + HELD_ABOVE))


def held_label(prog: Program, rank: int, skill: str) -> str:
    eff = held(prog, rank)
    if eff >= prog.rating:
        return prog.name
    return f'{prog.name}, held to {eff} by {skill.title()} {rank}'


#: The ones there is one of (D63 e). Not sold. Found, given, or decided.
RELICS: tuple[Program, ...] = (
    Program('thessaly', 'Thessaly', 'breaker', 3, 5, 0.65, 7400, 3,
            'A breaker with a dead runner\'s handle in the header and a '
            'comment block at the top that somebody wrote at four in the '
            'morning, addressed to nobody, explaining why a thing that should '
            'not work does. It still does.',
            effects={'residue_mult': 1.2},
            note='Strong and nearly quiet. It signs its work; she always did.',
            unique=True,
            lore='The Ninth still talks about her in the past tense without '
                 'ever saying what happened, and the handle is scratched into '
                 'the paint by the transit gate with a date under it. She was '
                 'faster than all of them and she never once cleaned up, on '
                 'the grounds that anybody good enough to read the logs was '
                 'good enough to know it was her anyway. The breaker keeps the '
                 'habit. Every crack it makes leaves a little more behind than '
                 'it should, and somewhere in that little more is her name.'),
    Program('fourohsix', 'Four-Oh-Six', 'hunter', 2, 5, 0.5, 5600, 3,
            'An index of four hundred and six runs that ended, sorted by what '
            'ended them. Point it at a host and it tells you which of the '
            'four hundred and six this one looks like.',
            effects={'scan_depth': 1, 'tell_lead': 1},
            note='Reads what killed the last four hundred and six people who '
                 'tried.',
            unique=True,
            lore='The Archivist gives it to people who agree to be in it. '
                 'That is the whole of the arrangement: your log joins the '
                 'others when it ends, and until then you carry everybody '
                 'else\'s. It is not sentimental. It is the single most '
                 'useful piece of reconnaissance in the city, because a '
                 'construct that has killed somebody has a way of doing it, '
                 'and the way is in here, four hundred and six times over.'),
    Program('nobody', 'Nobody', 'mask', 2, 5, 0.0, 6900, 3,
            'The Quiet Kid\'s route file. It does not hide you. It arranges '
            'for there to have been nobody to hide.',
            effects={'trace_mult': 0.72, 'rep_mult': 0.85},
            note='Passive. Nobody gets the credit either.',
            unique=True,
            lore='Nobody knows the Quiet Kid\'s handle, which is the point of '
                 'the Quiet Kid, and nobody knows how many jobs the Kid has '
                 'done because the jobs do not read as having been done by '
                 'anyone. This is how. It arrived in your deck without a '
                 'message attached, after you said yes to working together, '
                 'which is the most the Kid has ever said to anybody. It '
                 'works exactly as well for you as it does for them, with '
                 'the same cost: the work is nobody\'s, and so is the name '
                 'it would have made you.'),
    Program('desk', 'The Desk', 'forger', 3, 5, 0.4, 6200, 3,
            'Grieve\'s names. Every pretext it writes belongs to a person '
            'who exists, with a file that checks out, because it is their '
            'file.',
            effects={'pretext_bonus': 4, 'heat_mult': 1.1},
            note='Somebody real answers for every name on it.',
            unique=True,
            lore='Grieve keeps a desk, and what is on the desk is people: '
                 'clerks and auditors and night-shift supervisors, real ones, '
                 'with real credentials, who do not know they are on it. '
                 'Working with Grieve means working from the desk. A door '
                 'that asks who you are gets an answer that survives being '
                 'checked, and somewhere in the city a clerk gets a question '
                 'they cannot answer about a night they were at home. Grieve '
                 'says they are never hurt. Grieve says a lot of things in '
                 'that voice.'),
    Program('yourlog', 'The Log', 'wiper', 3, 5, 0.5, 7000, 3,
            'Eleven years of a network\'s own record of itself, which you '
            'read, and which has been reading you back since. It knows where '
            'logs are kept because it is one.',
            effects={'residue_mult': 0.55, 'composure': -2},
            note='The best wiper you will carry, and it is heavy.',
            unique=True,
            lore='You carried it out of Deepwater and you read it, which was '
                 'the one thing the people who wanted it had asked you not '
                 'to do. It is not a program in the usual sense. It is a '
                 'record of everything a network did for eleven years, '
                 'including the part where it noticed you, and it is '
                 'extremely good at finding where a network keeps its record '
                 'of you because it is that kind of thing itself. Carrying '
                 'it costs something you cannot put a number on, so the game '
                 'puts one on it, and the number is two.'),
    Program('samizdat', 'Samizdat', 'daemon', 2, 4, 0.7, 4800, 3,
            'The log, published, became a thing that keeps publishing. Set '
            'it loose on a host and it holds the host by telling everybody '
            'about it.',
            effects={'residue_mult': 0.9},
            note='A daemon that is also a rumour.',
            unique=True,
            lore='You published Deepwater\'s log and it did what published '
                 'things do in this city, which is get copied by people who '
                 'do not want to be the only ones holding it. One of the '
                 'copies came back to you as this: a daemon built out of the '
                 'log\'s own habits, which are to sit somewhere, watch, and '
                 'tell. It holds a node the way a crowd holds a street. '
                 'Nobody wrote it, exactly. It happened to the log.'),
    Program('pike', 'Pike', 'weapon', 2, 5, 1.0, 5800, 3,
            'Old Pike wrote the counter to the thing that bears his name, '
            'tested it once against a copy, and never ran it in anger. It is '
            'the cleanest piece of warfare code in the city and nobody has '
            'improved on it.',
            effects={'ice_damage': 4},
            note='Hits like a rating-six weapon at a third of the memory.',
            unique=True,
            lore='Pike is a hunter construct, Sendai and Nightwatch issue, and '
                 'it is called that because the man at the cranes designed '
                 'the first one and the people who bought it thought naming '
                 'it after him was a kindness. He wrote this the same year, '
                 'because a man who builds a thing should know how to stop '
                 'it, and then he put it in a drawer and went back to the '
                 'cranes. He hands it over without looking away from them. '
                 'He has watched you for eight runs and that is apparently '
                 'enough.'),
    Program('meridian_key', 'A Meridian Key', 'forger', 2, 5, 0.3, 8000, 3,
            'Not a file that is a key: a key. A thing half the city\'s doors '
            'recognise as permission out of habit, because it is older than '
            'the habit. It opens nothing of Meridian\'s. It opens nearly '
            'everything else, a little.',
            effects={'pretext_bonus': 5, 'heat_mult': 1.15},
            note='Quiet, strong, and Meridian notice what it opens.',
            unique=True,
            lore='Meridian held it for the first thirty years, Sendai for '
                 'the next eleven, and the ledger on the Row kept a line for '
                 'it the whole time that got longer every shift it was '
                 'away. You carried it out of a Sendai network for the '
                 'ledger and did not put it on the counter. It is the best '
                 'argument a forger can make, because it is not an '
                 'argument: it is the thing the argument is about. Doors '
                 'that were built when the key was issued open for it the '
                 'way old men stand up for a tune. Meridian know exactly '
                 'which doors those are, and they write down every one.'),
    Program('bell', 'The Bell That Does Not Ring', 'mask', 2, 4, 0.0, 5200, 3,
            'A mask built out of a recording of a bell that was never rung: '
            'the shape of a sound with no sound in it. A network looking for '
            'you finds the shape and nothing inside it.',
            effects={'trace_mult': 0.8, 'noise_mult': 0.92},
            note='Passive. Quiet the way an empty church is quiet.',
            unique=True,
            lore='The bell in the Hall\'s loft has never rung. The Chorus '
                 'recorded it anyway, the whole of what it would have sounded '
                 'like worked out from the metal and the room, and somebody '
                 'who came out of Deepwater and does not sing turned the '
                 'recording into this, and left it in the loft, under the '
                 'bell, for whoever stood with the Hall when it counted. It is '
                 'the quietest thing the Chorus own and they gave it to you '
                 'without a word, which is how they give things.'),
    Program('reliquary', 'Reliquary', 'armour', 2, 5, 0.0, 6400, 3,
            'Saint\'s armour, which is not armour: it is a list of the names '
            'of everybody who has died doing this, kept between you and the '
            'feedback, and it holds the way a thing holds that has already '
            'been through the worst of it.',
            effects={'ice_dr': 0.7, 'composure': 4},
            note='Passive. Five saves, and it remembers each one.',
            unique=True,
            lore='Saint keeps the names. Everybody who ever ran with Saint and '
                 'did not come out is in the header, and the header is most '
                 'of the program, and the program is what sits between '
                 'Saint and the feedback, and Saint has never once explained '
                 'how a list of the dead absorbs a strike except to say that '
                 'it has been through worse. You worked with Saint and Saint '
                 'gave you a copy, which means your name is in it too, at the '
                 'bottom, with no date, and Saint would like to keep it that '
                 'way.'),
    Program('lantern', 'Lantern', 'hunter', 2, 4, 0.45, 4400, 3,
            'Moth\'s hunter. It goes towards the light, which in a network is '
            'wherever the most is happening, and it gets there first, and it '
            'does not burn.',
            effects={'tell_lead': 1, 'scan_depth': 1},
            note='Reaches a hop further and hears a tick sooner. Moth\'s way.',
            unique=True,
            lore='Moth is called that because Moth goes towards the light, '
                 'and has done for eleven years, and has not burned, which '
                 'nobody who watched the first year would have bet on. This '
                 'is how. A hunter that reads a network for where the most is '
                 'happening and gets you there a hop sooner and a tick '
                 'earlier than anything on a shelf, because Moth could not '
                 'afford the shelf and wrote it in a stairwell. Moth gave it '
                 'to you the way Moth gives anything, which is by leaving it '
                 'where you would find it and denying it later.'),
    Program('boxstep', 'Boxstep', 'daemon', 2, 4, 0.55, 5100, 3,
            'The gait model the Vertical\'s lobby runs, taken out of the '
            'lobby. It knows what a person walking somewhere they are '
            'allowed to be looks like, and it walks like that, all night, '
            'wherever you put it.',
            effects={'trace_mult': 0.9},
            note='A daemon that holds a node by belonging there.',
            unique=True,
            lore='Ninety floors and a lobby that logs your gait, and every '
                 'one of the people who matter has stood in their socks on '
                 'Mrs Achterberg\'s box while she read their shoulders. She '
                 'has been fitting the building for thirty years and she has '
                 'never once been logged, because the lobby learned its idea '
                 'of a person who belongs there from the people it watches '
                 'most, and the person it watches most is a small woman with '
                 'pins in her mouth. She gave you the model. She did not say '
                 'how she got it and you did not ask, and neither of you has '
                 'mentioned it since.'),
    Program('lostproperty', 'Lost Property', 'wiper', 1, 4, 0.5, 4300, 3,
            'The Watch\'s own retention schedule, which says what gets '
            'destroyed and when. Run it over what you left behind and the '
            'network files it as due for disposal.',
            effects={'residue_mult': 0.6},
            note='One memory. It does not delete anything. It reclassifies.',
            unique=True,
            lore='Nightwatch keep a lost property office because the Watch '
                 'keeps everything, and everything includes the things they '
                 'took off people who did not come back for them, and the '
                 'schedule that says when the shelf gets cleared. The desk '
                 'sergeant has worked that counter for eleven years and has '
                 'watched the shelf clear twice, and both times it was '
                 'people, not property. What they gave you is not a program '
                 'anybody wrote: it is the schedule, and a network that '
                 'reads it agrees that what you left is due for disposal, '
                 'because the network has no opinion about a form that is '
                 'correctly filled in.'),
    Program('survey', 'The Survey', 'hunter', 1, 3, 0.6, 1900, 1,
            'Tuck\'s map of every cable in the Ninth, on something that is '
            'not paper. It is a map of a district, and it turns out a '
            'district and a network are the same shape.',
            effects={'scan_depth': 1},
            note='One memory. Reaches a hop further, for nothing.',
            unique=True,
            lore='Tuck mapped the Ward\'s cabling over nine years because '
                 'nobody else was going to and because the pumps depend on '
                 'it. The map is kept in the generator shed, in the sense '
                 'that Tuck put it somewhere and it is there. What a hunter '
                 'program does is read how somebody decided to arrange '
                 'things, and Tuck\'s map is the purest example of that in '
                 'the city, so loaded into a deck it does the same job, '
                 'modestly, forever. It is the first thing worth having that '
                 'the Ninth ever gave anybody for free.'),
)

PROGRAMS = PROGRAMS + RELICS

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



#: Program riders (D63 c). Each is read by the run layer while the program
#: is loaded; see `Deck.riders`.
RIDERS: frozenset[str] = frozenset({
    'shrike_edge', 'banshee_alarm', 'ledger_eye', 'tide_eye', 'dowse_eye',
})
