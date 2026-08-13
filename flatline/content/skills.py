"""The eight skill lines and the techniques they unlock.

The design rule for this file: **a rank must change what you can type, not
just what you roll.** Ranks 2 and 4 of every line unlock a technique, which is
either a new verb in the run shell or a new option on an existing verb. That is
the difference between a skill system and a stat block, and it is why a
Daemonology build plays a different game rather than the same game better.

Ranks 1, 3, and 5 are the numeric fill between them. They matter, but they are
not what a player is buying toward.
"""

from __future__ import annotations

from dataclasses import dataclass

MAX_RANK = 5

#: Experience to buy the next rank, indexed by the rank being bought.
#: Steep at the top so that a fifth rank is a real commitment against breadth.
RANK_COST = {1: 2, 2: 4, 3: 7, 4: 11, 5: 16}

#: Skill points granted at creation, spent under the same cost table.
CREATION_XP = 12


@dataclass(frozen=True, slots=True)
class Technique:
    key: str
    name: str
    rank: int
    #: The shell command this unlocks, or '' when it modifies an existing one.
    verb: str
    summary: str
    detail: str


@dataclass(frozen=True, slots=True)
class Skill:
    key: str
    name: str
    attr: str          # the attribute checks in this line are made against
    summary: str
    detail: str
    techniques: tuple[Technique, ...]

    def technique_at(self, rank: int) -> Technique | None:
        return next((t for t in self.techniques if t.rank == rank), None)


SKILLS: tuple[Skill, ...] = (
    Skill(
        'intrusion', 'Intrusion', 'logic',
        'Breaking services. The bread and butter.',
        'Every network has a front door and forty windows. Intrusion is the '
        'skill of getting through whichever one is closest, quickly, and '
        'without thinking too hard about elegance.',
        (
            Technique('chain', 'Chain', 2, 'crack --chain',
                      'Crack two services on one node in a single action.',
                      'Costs one action instead of two and generates 1.6x the '
                      'noise of the louder half. The maths favours it when '
                      'the trace is your problem and the ICE is not.'),
            Technique('pivot', 'Pivot', 4, 'pivot',
                      'Enter a neighbouring node on a cracked node\'s trust.',
                      'Skips the access check entirely on any node that trusts '
                      'the one you are standing in. Silent. This is the single '
                      'largest tempo swing in the game and it is why Intrusion '
                      'rank 4 is worth the eleven experience.'),
        )),
    Skill(
        'cryptography', 'Cryptography', 'logic',
        'Encrypted stores, key material, secure channels.',
        'The highest-value data on any network is encrypted, which means the '
        'difference between a payday and a wasted run is usually this line.',
        (
            Technique('keygrind', 'Keygrind', 2, 'crack --key',
                      'Grind an encrypted store without touching the network.',
                      'Spends Focus instead of ticks and makes no noise at all, '
                      'because the work happens on your deck. The constraint is '
                      'Focus, which does not regenerate inside a run.'),
            Technique('sidechannel', 'Sidechannel', 4, 'sidechannel',
                      'Derive a key from observed traffic on a node you hold.',
                      'Free, silent, and slow: it needs three ticks of residency '
                      'on a node carrying live traffic. The pure-stealth answer '
                      'to a vault that a Warfare build would simply break.'),
        )),
    Skill(
        'subterfuge', 'Subterfuge', 'guile',
        'Pretexting, forged credentials, being somebody else.',
        'Networks are defended against intruders. They are not, on the whole, '
        'defended against employees. Subterfuge is the argument that the '
        'cheapest exploit is a plausible voice on a phone.',
        (
            Technique('pretext', 'Pretext', 2, 'pretext',
                      'Talk a service into granting access.',
                      'A Guile check against the service instead of a Logic one, '
                      'at a quarter of the noise. Fails badly: a blown pretext '
                      'raises the alert level rather than merely making noise.'),
            Technique('impersonate', 'Impersonate', 4, 'impersonate',
                      'Assume a captured credential\'s owner wholesale.',
                      'ICE ignores you for a number of ticks equal to your Guile. '
                      'Not stealth: you are extremely visible and entirely '
                      'authorised, which is a different and better thing.'),
        )),
    Skill(
        'hardware', 'Hardware', 'logic',
        'Deck tuning, overclocking, physical taps.',
        'The deck is not a fixed quantity. Hardware is the line that treats it '
        'as something you are operating rather than something you own.',
        (
            Technique('overclock', 'Overclock', 2, 'overclock',
                      'Push the CPU past rated speed for extra actions.',
                      'One extra action per tick per step, at rising heat. '
                      'Heat above the cooling budget damages components and '
                      'feeds trace. Rank sets how many steps you survive.'),
            Technique('hotswap', 'Hotswap', 4, 'hotswap',
                      'Change a deck component mid-run.',
                      'Three ticks and a spike of noise to trade masking for '
                      'memory, or cooling for speed, once you know what the '
                      'network actually is. Legwork guesses; hotswap corrects.'),
        )),
    Skill(
        'stealth', 'Stealth', 'reflex',
        'Noise reduction at the source.',
        'Stealth does not make anything work better. It makes everything you '
        'do quieter, which in a game where the clock is driven by how loud you '
        'are turns out to be the same thing as making it work better.',
        (
            Technique('ghost', 'Ghost', 2, 'connect --ghost',
                      'Move between nodes generating no noise.',
                      'Costs an extra tick per hop. The trade is explicit: you '
                      'are spending the clock to not spend the alarm.'),
            Technique('nullsig', 'Nullsig', 4, 'nullsig',
                      'Suppress your signature entirely for a few ticks.',
                      'Trace does not advance at all while it holds. Once per '
                      'run, duration scales with rank, and every action you take '
                      'inside the window shortens it. The escape hatch, and the '
                      'reason a stealth build can attempt a core it has no '
                      'business being inside.'),
        )),
    Skill(
        'warfare', 'Warfare', 'nerve',
        'Direct engagement with countermeasures.',
        'The unfashionable answer to ICE is to kill it. Loud, fast, and the '
        'only line that gets better the worse the situation is.',
        (
            Technique('strike', 'Strike', 2, 'strike',
                      'Attack ICE directly rather than evading it.',
                      'Damage scales on rank and on Nerve. Cheaper than evasion '
                      'when the thing is already locked on to you, which is the '
                      'situation every other build is trying to avoid and this '
                      'one is trying to arrive at.'),
            Technique('overload', 'Overload', 4, 'overload',
                      'Destroy a countermeasure outright.',
                      'Kills any non-black ICE regardless of rating, once per '
                      'run, for a trace spike that will be the largest single '
                      'number you see all session. Worth it exactly once.'),
        )),
    Skill(
        'forensics', 'Forensics', 'logic',
        'Anti-forensics. Managing what you leave behind.',
        'The run ends when you jack out. The consequences do not. Forensics is '
        'the only line that operates on residue, which is the only quantity in '
        'the game that outlives the session it was created in.',
        (
            Technique('scrub', 'Scrub', 2, 'scrub',
                      'Reduce residue on the node you are standing in.',
                      'Two ticks. The purest expression of D5: you are spending '
                      'trace, right now, to buy down heat you will not feel for '
                      'another two shifts.'),
            Technique('falsify', 'Falsify', 4, 'falsify',
                      'Plant residue implicating another faction.',
                      'Converts your residue into their problem. The single most '
                      'powerful city-layer verb in the game, because it does not '
                      'reduce heat, it moves it, and factions react to each other.'),
        )),
    Skill(
        'daemonology', 'Daemonology', 'logic',
        'Automation. Programs that act without you.',
        'The deepest line and the one that changes how the game is played '
        'rather than how well. A daemonologist is not faster than the trace. A '
        'daemonologist is in four places at once.',
        (
            Technique('script', 'Script', 2, 'script',
                      'Record a command sequence and replay it as one action.',
                      'A saved script costs one tick less than the sum of its '
                      'parts, to a minimum of one. Trivial-looking, and it '
                      'compounds: by rank 4 a good script library is worth more '
                      'than an attribute point.'),
            Technique('daemon', 'Daemon', 4, 'daemon',
                      'Deploy an autonomous agent that acts each tick.',
                      'A daemon holds a node, watches for ICE, or grinds a '
                      'crack while you are elsewhere. It has its own noise '
                      'signature and it is not smart. Two of them will get you '
                      'caught. Two of them will also get you out with the data.'),
        )),
)

SKILL_KEYS: tuple[str, ...] = tuple(s.key for s in SKILLS)
BY_KEY: dict[str, Skill] = {s.key: s for s in SKILLS}
TECHNIQUES: dict[str, Technique] = {
    t.key: t for s in SKILLS for t in s.techniques
}
