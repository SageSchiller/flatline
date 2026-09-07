"""Where you came from, per D10.

An origin sets attribute shape, starting gear, opening faction standing, and
one passive that never goes away. It never caps a skill and never locks a tree.
The corporate defector can end up a street social engineer; it will simply have
taken longer than the fixer's runner would have taken.

Each origin also carries a **complication**: something already true about the
world when the game starts. This is the part that makes an origin a story
rather than a stat block. The academic's debt exists whether or not the player
thinks about it, and the ex-cop's bounty is on the board on shift one.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Origin:
    key: str
    name: str
    blurb: str
    #: Prose shown at creation. Second person, present tense, no more than
    #: four sentences: this is a character sheet, not a novel.
    story: str
    #: Added to the flat starting spread of 3 across the board.
    attrs: dict[str, int]
    #: Free skill ranks, granted before creation experience is spent.
    skills: dict[str, int]
    credits: int
    #: Content ids resolved by the loader. A missing id is a validation error.
    cyberware: tuple[str, ...]
    programs: tuple[str, ...]
    deck: str
    #: The shape they already wear in the net. See content/icons.py.
    icon: str
    #: faction key -> starting reputation, on the -100..100 scale.
    standing: dict[str, int]
    passive: str
    passive_detail: str
    complication: str
    #: The numeric half of the passive, merged into the character like chrome.
    #: `validate.py` checks the keys, which is the only reason a passive
    #: cannot quietly become prose that does nothing.
    effects: dict = field(default_factory=dict)
    #: The half the engine has to special-case. Must be in `RIDERS`.
    rider: str = ''
    #: Where this character's face starts. A default rather than a cage: the
    #: player can change the four free slots immediately and buy the rest on a
    #: clinic table. It exists so that ten origins do not all walk into Marrow
    #: wearing the same grey coat and the same nothing expression.
    look: dict = field(default_factory=dict)
    #: The thing nobody else can do. A verb only this origin has, which is
    #: what makes the choice at creation weigh something: two characters with
    #: the same skills and the same chrome still cannot do each other's job.
    signature: str = ''
    signature_name: str = ''
    signature_detail: str = ''


ORIGINS: tuple[Origin, ...] = (
    Origin(
        'defector', 'Corporate defector',
        'Started inside. Knows how they think, and they know it.',
        'You wrote the access policy that you are now going to spend a career '
        'violating. Eleven years at Kagawa Vertical, most of them believing the '
        'work was neutral. You left with a laptop that was not yours and a '
        'clear idea of exactly how much they log.',
        attrs={'logic': 2, 'guile': 1, 'grit': -1},
        skills={'intrusion': 1, 'forensics': 1},
        credits=2400,
        cyberware=('corp_neural_shunt',),
        programs=('sable', 'quietcastle', 'ledgerhand'),
        deck='kagawa_issue',
        icon='corporate',
        standing={'kagawa': -45, 'aoyama': 10, 'fixers': 5},
        passive='Policy reader',
        passive_detail=(
            'You know what corporate networks log and when. Residue generated '
            'on any corporate network is reduced by 15%, and node types read '
            'correctly on a `scan` without a second probe.'),
        complication=(
            'Kagawa Vertical wants the laptop back, and they have not decided '
            'yet whether they want you with it.'),
        rider='policy_reader',
        signature='policy',
        signature_name='Policy',
        signature_detail=(
            'You wrote the access policy. Once per run, name a node and it will '
            'tell you what it is required to log and when, which means you know '
            'exactly what leaving it alone is worth. Removes all residue you '
            'have left there and reveals whether anything is watching.'),
        look=dict(build='soft', face='young', eyes='reconstructed', hair='severe', marks='corporate', dress='corporate', bearing='formal', voice='corporate')),
    Origin(
        'gutter', 'Gutter runner',
        'Self-taught off salvage. Cheap, fast, and loud.',
        'Nobody taught you this. You found a deck in a flooded substation at '
        'fourteen and spent six years finding out what the parts did by '
        'breaking them. Everything you own is held together with solder and '
        'opinion, and all of it is faster than it has any right to be.',
        attrs={'reflex': 2, 'grit': 1, 'logic': -1},
        skills={'intrusion': 1, 'hardware': 1, 'streetcraft': 1},
        credits=700,
        cyberware=('salvage_reflex_loop',),
        programs=('crowbar', 'crowbar', 'blink'),
        deck='scrapdeck',
        icon='plain',
        standing={'sixes': 20, 'kagawa': -10, 'fixers': -5},
        passive='Salvager',
        passive_detail=(
            'You can repair and improvise. Deck components cost 30% less to '
            'repair, and a destroyed component can be jury-rigged back to half '
            'function for free once per run.'),
        complication=(
            'The Sixes consider you theirs. They have not asked for anything '
            'yet. They will.'),
        effects={'repair_mult': 0.7},
        signature='jury',
        signature_name='Jury-rig',
        signature_detail=(
            'Once per run, bring a destroyed deck component back to half '
            'function out of nothing but what is already in the case. Everybody '
            'else has to leave the run.'),
        look=dict(build='wiry', face='sharp', eyes='tired', hair='cropped', marks='ports', dress='street', bearing='watchful', voice='ninth')),
    Origin(
        'protege', 'Fixer\'s protege',
        'Grew up in the trade. Best contacts, thinnest foundation.',
        'Mara Okonkwo took you off a corner at nine and put you behind a desk '
        'answering her phones. You learned who everybody is, what everybody '
        'owes, and how a deal falls apart, long before you learned what a port '
        'scan was. The technical part is still catching up.',
        attrs={'guile': 2, 'nerve': 1, 'logic': -1},
        skills={'subterfuge': 1, 'streetcraft': 1},
        credits=1800,
        cyberware=('social_lattice',),
        programs=('sable', 'handshake', 'blink'),
        deck='midline',
        icon='plain',
        standing={'fixers': 40, 'sixes': 10, 'nightwatch': -10},
        passive='Known quantity',
        passive_detail=(
            'Fixers front you work nobody else can see. One extra contract on '
            'the board at all times, and contract payouts negotiate 10% higher '
            'before reputation is applied.'),
        complication=(
            'Mara is owed something and has never once said what. She is '
            'patient in the way that people are when they are certain.'),
        effects={'pay_mult': 1.1},
        rider='known_quantity',
        signature='vouch',
        signature_name='Vouch',
        signature_detail=(
            'Once per run, spend the Switchboard\'s name instead of a '
            'credential. A warden that checks credentials accepts you outright, '
            'no roll, because somebody it trusts has said you are fine.'),
        look=dict(build='compact', face='kind', eyes='warm', hair='undercut', marks='ink', dress='expensive', bearing='amiable', voice='warm')),
    Origin(
        'academic', 'Academic',
        'Cryptography background, no street sense whatsoever.',
        'You have published. Two of the papers are still cited, one of them by '
        'people who should not have access to it. The department stopped '
        'funding the work when they understood what it implied, which was '
        'roughly eight months before you understood what it was worth.',
        attrs={'logic': 3, 'guile': -2, 'grit': -1, 'nerve': 1},
        skills={'cryptography': 2},
        credits=1200,
        cyberware=('cortex_annex',),
        programs=('lattice', 'sable', 'quietcastle'),
        deck='university_loan',
        icon='plain',
        standing={'aoyama': 25, 'freeport': 15, 'sixes': -15},
        passive='First principles',
        passive_detail=(
            'You solve what you have never seen. Cryptography checks against '
            'unfamiliar encryption schemes take no unfamiliarity penalty, and '
            'you learn a network\'s cipher family from a single observation.'),
        complication=(
            'The loan on the deck is real, it is compounding, and the lender is '
            'not a bank.'),
        rider='first_principles',
        signature='firstprinciples',
        signature_name='First principles',
        signature_detail=(
            'Once per run, derive a key rather than breaking one. Opens any '
            'single encrypted service or asset outright, at the cost of every '
            'point of Focus you have left.'),
        look=dict(build='stooped', face='worn', eyes='shielded', hair='thinning', marks='faded', dress='layered', bearing='restless', voice='rambling')),
    Origin(
        'expolice', 'Ex-enforcement',
        'Worked the other side. Reads ICE like a native.',
        'Nine years in Nightwatch cyber division, three of them running the '
        'intrusion response desk. You have sat on the other end of a trace with '
        'a coffee going cold, waiting for somebody exactly like you to make one '
        'more move. You know what they are waiting for. It has not helped as '
        'much as you expected.',
        attrs={'nerve': 2, 'reflex': 1, 'guile': -1},
        skills={'warfare': 1, 'forensics': 1, 'streetcraft': 1,
                'violence': 1},
        credits=1500,
        cyberware=('threat_overlay',),
        programs=('cudgel', 'sable', 'mirrorbox'),
        deck='decommissioned',
        icon='corporate',
        standing={'nightwatch': -60, 'sixes': -20, 'freeport': 20},
        passive='Read the room',
        passive_detail=(
            'ICE tells arrive a full tick earlier for you, and you identify '
            'countermeasure types on sight without a probe. Against Nightwatch '
            'networks specifically, you know the response playbook: alert '
            'escalation is one step slower.'),
        complication=(
            'There is a live bounty on you, filed by people who have your '
            'biometrics on record and your service history in a drawer.'),
        rider='read_the_room',
        signature='playbook',
        signature_name='Playbook',
        signature_detail=(
            'Once per run, call the response the way the desk would have. Every '
            'countermeasure on the network telegraphs a full tick early for the '
            'rest of the run, and you learn what each one is.'),
        look=dict(build='blocky', face='severe', eyes='narrow', hair='shaved', marks='surgical', dress='nightwatch', bearing='coiled', voice='clipped')),
    Origin(
        'chromed', 'Chromed',
        'Already more machine than most. The city notices.',
        'You stopped counting at eleven pieces. Somewhere in the middle of that '
        'the net started feeling less like a place you visit and more like the '
        'room you are actually standing in, with the meat world as the thing on '
        'the far side of a window. You are aware this is a symptom. It has not '
        'made you want to reverse it.',
        attrs={'reflex': 2, 'nerve': 1, 'grit': 1, 'guile': -2},
        skills={'warfare': 1, 'stealth': 1, 'violence': 1},
        credits=400,
        cyberware=('spinal_bus', 'ocular_suite', 'reflex_governor'),
        programs=('crowbar', 'cudgel'),
        deck='midline',
        icon='null',
        standing={'aoyama': -20, 'nightwatch': -15, 'sixes': 5},
        passive='Native',
        passive_detail=(
            'The net is your first language. You begin every run with one '
            'additional action in the first tick, and black ICE composure '
            'checks are made at a bonus equal to a quarter of your Dissonance.'),
        complication=(
            'You start at 35 Dissonance. Clinics charge you more, fixers meet '
            'you outdoors, and something in the ocular suite has begun '
            'reporting to a maintenance address you did not configure.'),
        rider='native',
        signature='native',
        signature_name='Native',
        signature_detail=(
            'Once per run, stop using the interface. For three ticks you move '
            'through the network as though it were a room: connections cost '
            'nothing, no noise at all, and locked-on countermeasures lose you.'),
        look=dict(build='asymmetric', face='unfinished', eyes='optics', hair='none', marks='subdermal', dress='armoured', bearing='twitchy', voice='synthetic')),
    Origin(
        'bonded', 'Indentured',
        'Corporate property with a buyout figure. Best gear, worst terms.',
        'You signed at nineteen because the alternative was the Terraces and '
        'a lifetime of somebody else\'s stairwell. Kagawa trained you, chromed '
        'you, and priced you, and the price has never once gone down. You are '
        'not running away from them. You are running to afford them.',
        attrs={'logic': 1, 'grit': 1, 'nerve': 1, 'guile': -1},
        skills={'intrusion': 1, 'cryptography': 1},
        credits=600,
        cyberware=('corp_neural_shunt', 'archivist'),
        programs=('sable', 'handshake', 'housecall'),
        deck='kagawa_issue',
        icon='corporate',
        standing={'kagawa': 20, 'freeport': -15, 'sixes': -10},
        passive='Company hardware',
        passive_detail=(
            'Everything you own is corporate issue and corporately '
            'maintained. Deck repairs cost half, and Kagawa networks read '
            'your credentials as current until somebody checks them against '
            'the buyout ledger.'),
        complication=(
            'You owe Kagawa twenty-six thousand credits and it compounds '
            'every shift. They are extremely patient and they have never once '
            'had to be anything else.'),
        effects={'repair_mult': 0.5},
        signature='requisition',
        signature_name='Requisition',
        signature_detail=(
            'Once per run, file for corporate resources against a buyout you '
            'have not finished paying. A program you do not own appears in '
            'memory for the rest of the run, and the paperwork is somebody '
            'else\'s problem.'),
        look=dict(build='slight', face='young', eyes='brown', hair='long', marks='brand', dress='workwear', bearing='apologetic', voice='quiet')),
    Origin(
        'burnout', 'Burnout',
        'Was one of the best. Eight years ago.',
        'There was a stretch where people said your name in the same sentence '
        'as Ledger\'s. Then a Sendai job went wrong in a way you still cannot '
        'describe in order, and you spent four years doing something else, and '
        'the chrome you came back with is a generation behind and the hands '
        'are not what they were. You still know more than almost anybody. '
        'Knowing is the part that got cheaper.',
        attrs={'reflex': -2, 'grit': -1, 'logic': 1, 'nerve': 2},
        skills={'intrusion': 2, 'forensics': 1, 'warfare': 1, 'stealth': 1},
        credits=900,
        cyberware=('salvage_reflex_loop', 'nictitating'),
        programs=('sable', 'cudgel', 'quietcastle', 'housecall'),
        deck='scrapdeck',
        icon='plain',
        standing={'fixers': 15, 'sendai': -30, 'sixes': 10},
        passive='Been here before',
        passive_detail=(
            'You have seen all of this. You start with every countermeasure '
            'type already identified on sight, traps included, and you take '
            'no unfamiliarity penalty against anything. What you cannot do is '
            'move like you used to.'),
        complication=(
            'Your deck starts damaged, your Reflex is gone, and somebody at '
            'Sendai still has the incident file with your working name on the '
            'cover.'),
        rider='veteran_eye',
        signature='remember',
        signature_name='Remember',
        signature_detail=(
            'Once per run, remember having done this before. Retry any check '
            'you have just failed, with your full skill and no situational '
            'penalties at all.'),
        look=dict(build='gaunt', face='burned', eyes='flickering', hair='unkempt', marks='burns', dress='nothing', bearing='exhausted', voice='rough')),
    Origin(
        'ghost', 'Legally dead',
        'No record, no history, no heat. Also no friends.',
        'The death certificate is real, filed, and eleven months old. You do '
        'not remember arranging it and you have stopped assuming you did. '
        'What you have instead of a life is a clean slate in the most literal '
        'sense: nothing in this city has an opinion about you, because as far '
        'as this city is concerned there is nobody here to have one about.',
        attrs={'guile': 1, 'reflex': 1, 'nerve': 1, 'grit': -1},
        skills={'stealth': 2, 'subterfuge': 1},
        credits=1100,
        cyberware=('ghost_layer',),
        programs=('skeleton', 'quietcastle', 'blink'),
        deck='midline',
        icon='deadname',
        standing={},
        passive='Nobody',
        passive_detail=(
            'You have no history to burn. New identities cost you half what '
            'they cost anybody else and take one shift instead of two, and '
            'all faction heat decays 40% faster, because there is nothing to '
            'attach it to.'),
        complication=(
            'You start knowing nobody and owed nothing. Every relationship in '
            'this city has to be built from zero, and somebody, somewhere, '
            'is currently using the name you had before.'),
        rider='no_history',
        signature='nobody',
        signature_name='Nobody',
        signature_detail=(
            'Once per run, stop existing for a moment. The trace resets to '
            'zero. It has nowhere to attach and it has to start again from what '
            'it can find, which is nothing.'),
        look=dict(build='unremarkable', face='plain', eyes='grey', hair='wig', marks='none_visible', dress='grey', bearing='grey_man', voice='unremarkable')),
    Origin(
        'courier', 'Courier',
        'Carried data through the streets before ever going through a wire.',
        'Nine years of moving things across this city on foot, on a bike, and '
        'twice in your own abdomen. You know which stairwells connect, which '
        'gate guards read their screens, and what time the Terraces shift '
        'changes. The net is the part you learned last and it still feels '
        'like somewhere you are visiting.',
        attrs={'reflex': 2, 'grit': 2, 'logic': -2, 'guile': 1},
        skills={'subterfuge': 1, 'hardware': 1, 'fieldcraft': 1},
        credits=1600,
        cyberware=('quiet_hands',),
        programs=('crowbar', 'blink', 'siphon'),
        deck='midline',
        icon='plain',
        standing={'fixers': 20, 'sixes': 15, 'freeport': 15, 'kagawa': -5},
        passive='Knows the streets',
        passive_detail=(
            'You move through this city the way other people move through '
            'their own flat. Travel to any district you have already visited '
            'costs no shift, and arriving anywhere is 40% less likely to go '
            'badly however much heat you are carrying.'),
        complication=(
            'There is a package you never delivered. You still have it, you '
            'have never opened it, and the person who gave it to you has been '
            'dead for two years.'),
        rider='streetwise',
        signature='backway',
        signature_name='The back way',
        signature_detail=(
            'Once per run, take a route you already knew about. Move to any '
            'node you have seen, from anywhere, in one tick and in silence. '
            'The one thing in the game that ignores reach: a courier knows '
            'a way that is not on the plan.'),
        look=dict(build='rangy', face='lopsided', eyes='mismatched', hair='braided', marks='clinic', dress='salvage', bearing='restless', voice='fast')),
    Origin(
        'printer', 'Compositor',
        'Set type in the Stacks. Reads a system the way you read a page.',
        'Eleven years on the floor under the water towers, setting other '
        'people\'s words in somebody else\'s font and correcting both. You '
        'learned networks the way compositors always have, which is by '
        'noticing that everything published is a structure somebody chose, '
        'and that people who choose structures are people, and tired.',
        attrs={'logic': 2, 'guile': 1, 'grit': 1, 'reflex': -2},
        skills={'architecture': 2, 'forensics': 1, 'streetcraft': 1},
        credits=1300,
        cyberware=('optic_lattice',),
        programs=('sable', 'blink', 'housecall'),
        deck='midline',
        icon='meter',
        standing={'static': 25, 'freeport': 10, 'kagawa': -15, 'meridian': -5},
        passive='Reads the floor',
        passive_detail=(
            'Everything published is a structure somebody chose. Legwork on '
            'the shape of a network is free for you and comes back better, '
            'and you can tell a corrected edition from an original at a '
            'glance, which in a network means a honeypot.'),
        complication=(
            'Your name is in the header of forty thousand pages, and one of '
            'them was the edition Kagawa asked the Watch to stop. Nobody has '
            'come about it. Somebody filed it.'),
        rider='reads_the_floor',
        signature='correction',
        signature_name='Correction',
        signature_detail=(
            'Once per run, publish a correction: everything a network has '
            'filed about you this evening is amended to be about a plausible '
            'other person. The alert drops a level and the trace goes back '
            'to where it was ten ticks ago.'),
        look=dict(build='slight', face='worn', eyes='grey', hair='cropped',
                  marks='ink', dress='workwear', bearing='still',
                  voice='flat')),
    Origin(
        'chorister', 'Chorister',
        'Raised in the Hall. Fed people for a living before this.',
        'The Chorus took the interchange when the trains stopped and you '
        'were four, and you grew up under a departure board showing a hymn, '
        'in a building where the answer to most questions was soup. You '
        'know every stairwell in the east of this city and everybody who '
        'sleeps in them, and you have never once been alone in a room.',
        attrs={'nerve': 2, 'guile': 1, 'grit': 1, 'logic': -2},
        skills={'psyche': 2, 'streetcraft': 1, 'subterfuge': 1},
        credits=900,
        cyberware=(),
        programs=('crowbar', 'quietcastle', 'housecall'),
        deck='scrapdeck',
        icon='plain',
        standing={'chorus': 30, 'sixes': 10, 'carrion': -10, 'meridian': -10},
        passive='Somebody will vouch',
        passive_detail=(
            'Forty people will say you were at the soup, and mean it. Heat '
            'cools half again as fast for you, and the street stops you less '
            'often, because somebody in the queue always knows your face and '
            'says so out loud.'),
        complication=(
            'The Hall fed you for twenty years and the Chorus have never '
            'asked you for anything, which is a debt with no number on it '
            'and no way to pay it down.'),
        rider='vouched_for',
        signature='hymn',
        signature_name='The hymn',
        signature_detail=(
            'Once per run, hold still and go through it, all of it, the way '
            'you were taught. Composure is restored, every lock-on breaks, '
            'and the tick costs nothing because you were not doing anything '
            'anybody could file.'),
        look=dict(build='blocky', face='kind', eyes='brown', hair='shaved',
                  marks='religious', dress='devotional', bearing='open',
                  voice='warm')),
)

ORIGIN_KEYS: tuple[str, ...] = tuple(o.key for o in ORIGINS)
BY_KEY: dict[str, Origin] = {o.key: o for o in ORIGINS}

#: The lifepath opening (D126): the first beat where the complication you
#: started under stops being a line on the sheet and starts being a thing that
#: is happening. It fires once, after your first run, because a first job is
#: what puts you back on the radar of whatever you came from.
ORIGIN_OPENING: dict[str, str] = {
    'defector':
        'A message reaches you through a channel you were sure you had '
        'closed. It is not a threat. It is worse than a threat: it is polite, '
        'it uses your first name, and it says the Vertical hopes you are '
        'keeping the laptop somewhere dry.',
    'gutter':
        'Somebody from the Sixes buys you a drink you did not order, in a bar '
        'you told nobody you would be in. They do not sit down. They just '
        'wanted you to see that they could have.',
    'protege':
        'Mara sends nothing after your first job. No note, no congratulation, '
        'no correction. From anybody else that would mean nothing. From her '
        'it means she is waiting to see what you do with the second one.',
    'academic':
        'The loan on the deck posts its first real interest, and the number '
        'is worse than the maths you did, because you did the maths as though '
        'the lender were a bank. The statement arrives by hand, which banks '
        'do not do.',
    'expolice':
        'Somebody runs your face on your way out. You feel it the way you '
        'were trained to, from the other side of it. The bounty on you is not '
        'theoretical any more. It has a shift and a place attached to it now, '
        'and the place is here.',
    'chromed':
        'The ocular suite does a thing it has not done before. It holds, for '
        'exactly one second, on a maintenance node you had no reason to look '
        'at, and then lets go as if nothing happened. Something in you is '
        'filing reports, and it is not you.',
    'bonded':
        'Kagawa\'s number ticks over, the way it does every shift, and this '
        'time a note comes with it. Not a demand. A reminder that they know '
        'you are working now, and that working is good, because working is '
        'how the number comes down, eventually, in theory.',
    'burnout':
        'Your deck drops a frame mid-thought, the way it has since you got '
        'it, and for a second you are back in the room where it happened. '
        'Somebody at Sendai still has that room on file. Your first job just '
        'put a fresh timestamp next to your working name.',
    'ghost':
        'For the first time since you died, one person in this city thinks '
        'your face belongs to somebody. It is not much. They are not even '
        'sure. But a ghost seen once is a person who can be seen twice, and '
        'somewhere the name you used to have is still walking around on '
        'somebody else.',
    'courier':
        'The package you never delivered is exactly where you left it, and '
        'after your first real job it feels heavier, though nothing about it '
        'has changed. The person who gave it to you has been dead two years. '
        'You are the only one who remembers there is a package at all. You '
        'think.',
    'printer':
        'Your name is in the header of forty thousand pages, and after your '
        'first job one of them turns up, left where you will find it, folded '
        'to the edition Kagawa asked the Watch to stop. There is no note. The '
        'fold is the note.',
    'chorister':
        'The Hall does not contact you. The Chorus never do. But a hymn you '
        'have not heard since you left plays, once, from a doorway you pass, '
        'and stops when you turn to look. It is not a message. It is a '
        'reminder that the debt with no number is still open, and still '
        'theirs.',
}

#: Every origin starts here before its `attrs` delta is applied.
BASE_ATTR = 3

#: The three the origin table puts first (D187), each with how it plays,
#: for somebody who has never chosen between twelve of anything.
FIRST_RUNNER: tuple[tuple[str, str], ...] = (
    ('gutter', 'Loud and fast'),
    ('defector', 'Quiet and clever'),
    ('protege', 'Talks their way in'),
)


def starting_attrs(origin) -> list[tuple[str, str, int, bool]]:
    """What this origin starts with, as (short, name, value, moved) in the
    order the sheet prints them (D185). The table used to show `REF +2`
    and the spend screen `Reflex 5`, and nothing said what the middle was."""
    from . import attributes as attr_content
    return [(a.short, a.name, BASE_ATTR + origin.attrs.get(a.key, 0),
             a.key in origin.attrs) for a in attr_content.ATTRIBUTES]

#: Riders the engine implements. A passive naming anything else is a
#: validation error, which is what stops an origin's headline ability from
#: being a sentence that does nothing.
#: Signature verbs, one per origin. Registered as commands like anything
#: else, and refused to anybody who is not that origin.
SIGNATURES: frozenset[str] = frozenset({
    'policy', 'jury', 'vouch', 'firstprinciples', 'playbook', 'native',
    'requisition', 'remember', 'nobody', 'backway', 'correction', 'hymn',
})

RIDERS: frozenset[str] = frozenset({
    'policy_reader', 'known_quantity', 'first_principles',
    'read_the_room', 'native', 'veteran_eye',
    'no_history', 'streetwise', 'reads_the_floor', 'vouched_for',
})

#: The Chromed origin's opening Dissonance. Named rather than inline because
#: the city layer reads it when deciding how merchants behave on shift one.
CHROMED_START_DISSONANCE = 35
