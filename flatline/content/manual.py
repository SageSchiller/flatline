"""The manual: what everything does, and how the pieces push on each other.

`help <command>` has always told you what a verb does. It has never told you
what Nerve is for, or why cleaning up after yourself is expensive, or what
happens to the residue you left once you have jacked out. That is most of the
game, and none of it was written down anywhere a player could reach.

**The rule this file is written under: every topic ends with a decision.** A
reference entry that explains a number without saying what the player should do
differently is a glossary, and a glossary is not help. Each topic here closes
on the tradeoff it exists to inform.

Topics cross-reference each other by key, and `validate.py` checks that every
link resolves, that every topic is reachable from the index, and that anything
naming a command names a real one.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Topic:
    key: str
    title: str
    #: One line, shown in the index.
    summary: str
    #: The body. Markup is allowed; `[[key]]` is not, links are explicit.
    body: str
    #: Other topics worth reading next.
    see: tuple[str, ...] = ()
    #: Commands that act on what this topic describes.
    commands: tuple[str, ...] = ()
    #: Grouping in the index.
    group: str = 'systems'
    #: Content modules this topic is the documentation for.
    #:
    #: `validate.py` walks `flatline/content/` and fails the build on any
    #: module that no topic claims and that is not explicitly exempt. That is
    #: this project's oldest rule turned on its own prose: content declaring
    #: something the engine never reads is a lie that ships because it works,
    #: and a system nobody wrote a topic for is the same lie by omission.
    covers: tuple[str, ...] = ()
    #: Words a player will search for that the prose does not happen to use.
    #:
    #: `help addiction` and `help loan` both found nothing, because the text
    #: says habit and borrow. Writing a synonym into the prose to satisfy a
    #: search is how prose gets worse, so it is declared instead, and anything
    #: already in the body is rejected as a duplicate that will drift.
    terms: tuple[str, ...] = ()


GROUPS = ('start', 'systems', 'character', 'city')

GROUP_TITLES = {
    'start': 'Starting out',
    'systems': 'How a run works',
    'character': 'What you are made of',
    'city': 'The city, and what it remembers',
}

#: What `help` puts in front of somebody who has just arrived, in order.
#: Deliberately four: a landing page listing everything is the index it was
#: supposed to replace.
STARTER_PATH = ('basics', 'firstrun', 'triangle', 'origins')

#: The verbs that answer "what now", listed on the landing page under their
#: own heading. Every one costs no time and is safe to ask at any point, which
#: is what qualifies them: somebody who is lost should never have to spend a
#: resource to stop being lost. `validate.py` holds them to that.
ORIENTATION = (
    ('now', 'the next move and the verbs that matter; an empty line does '
            'the same'),
    ('job', 'what you are trying to do, and the next move'),
    ('map', 'the shape of where you are, city or network'),
    ('status', 'where you stand, and how fast'),
    ('chem', 'what is in you and what it is about to do'),
)


TOPICS: tuple[Topic, ...] = (
    # -- starting out -----------------------------------------------------
    Topic(
        'basics', 'The shape of the game',
        'What you actually do, in four sentences.',
        'You take a contract from somebody who wants a corporate network '
        'interfered with. You travel to the district it is in, choose what to '
        'carry, and jack in. Inside, you break your way toward whatever the '
        'job is about while a trace runs against you, and you leave before it '
        'finishes.\n\n'
        'Then the part most games do not have: [accent]the city remembers[/]. '
        'The evidence you left behind becomes that faction\'s attention on '
        'you a shift later, their networks get harder every time you succeed '
        'against them, and the other runners in this city are taking the work '
        'you did not.\n\n'
        '[warn]The decision the whole game is built around[/] is not which '
        'exploit to use. It is whether to spend time covering your tracks, '
        'knowing the trace advances while you do it.',
        see=('triangle', 'firstrun', 'checks', 'saves', 'reading', 'shell'),
        commands=('board', 'take', 'jack in'),
        terms=('what is this', 'premise', 'overview',),
        group='start'),
    Topic(
        'firstrun', 'Your first run, step by step',
        'The exact sequence, with the reasons.',
        '[accent2]If you remember one command, remember [fg]job[/][accent2]. '
        'It says what this run is for, where the thing is, how far along you '
        'are, and the next command to type. It costs no time.[/]\n\n'
        '[accent]In the city:[/]\n'
        '  [fg]board[/]              see what work is on offer\n'
        '  [fg]board c001[/]         read one properly before taking it\n'
        '  [fg]take c001[/]          accept it\n'
        '  [fg]job[/]                what you agreed to, and what is missing\n'
        '  [fg]deck[/]               check what you are carrying\n'
        '  [fg]map[/]                the city, and the walk to the job\n'
        '  [fg]travel <district>[/]  toward it, one district a shift\n'
        '  [fg]jack in[/]            go\n\n'
        '[accent]Inside:[/]\n'
        '  [fg]job[/]                what finishing looks like, and the next move\n'
        '  [fg]scan[/]               see what this node connects to\n'
        '  [fg]probe <host>[/]       see what a host runs, and what guards it\n'
        '  [fg]odds crack <host> <service>[/]   the maths, before you commit\n'
        '  [fg]crack <host> <service>[/]        break it open\n'
        '  [fg]connect <host>[/]     move there\n'
        '  [fg]status[/]             where the trace is\n'
        '  [fg]pull[/]               take what you came for\n'
        '  [fg]jack out[/]           leave\n\n'
        'Every run is the same five beats: find it, reach it, open it, do the '
        'thing, leave. Repeat scan, probe, crack, connect until you are '
        'standing on the objective, and ask [fg]job[/] whenever you lose the '
        'thread.\n\n'
        '[warn]What you cannot do once you are inside:[/] change the loadout. '
        'The programs on the deck at the moment you jack in are the programs '
        'you have, so [fg]deck[/] and [fg]load[/] happen out in the city, '
        'before the door shuts.\n\n'
        '[warn]The mistake everybody makes first:[/] staying too long. Every '
        'command costs time, time advances the trace, and there is no prize '
        'for the last asset you grabbed if the trace lands on you carrying it.',
        see=('triangle', 'checks', 'objectives'),
        commands=('job', 'scan', 'probe', 'odds', 'crack', 'connect',
                  'jack out'),
        covers=('tutorial',),
        terms=('how to play', 'getting started', 'walkthrough',),
        group='start'),

    Topic(
        'saves', 'Saves, and keeping one',
        'Where a character lives, and how to make sure they survive.',
        'You can have as many characters as you like and they do not '
        'interact. Each one is filed under their own handle, so making a '
        'second never touches the first.\n\n'
        '  [fg]characters[/]              everybody you have, living or not\n'
        '  [fg]switch <handle>[/]         put this one down, pick that one '
        'up\n'
        '  [fg]new <handle> --origin[/]   somebody else entirely\n'
        '  [fg]delete <handle>[/]         the only thing that loses '
        'anybody\n\n'
        'Switching saves whoever you are first, so it is never how you lose '
        'somebody. [warn]Nothing except `delete` removes a character[/], and '
        '`delete` tells you what it is about to throw away before it will do '
        'it.\n\n'
        'Starting the game with one character opens them. With several it '
        'shows you the list and waits, because being handed the wrong runner '
        'is worse than typing one more word.\n\n'
        'A finished character stays on the list. You can read their sheet, '
        'their standing and their log; you cannot work with them, because '
        'they are finished. That is most of what finished means.\n\n'
        'The game autosaves on every shift boundary and on quitting. Saves '
        'live in your XDG data directory, usually '
        '[dim]~/.local/share/flatline[/], not beside the code, so moving or '
        'reinstalling the game does not touch a character.\n\n'
        'That location is correct and it is also the one place nobody thinks '
        'to back up. So:\n\n'
        '  [fg]save --export <path>[/]      a copy anywhere you like\n'
        '  [fg]restore --import <path>[/]   bring one back, here or elsewhere\n\n'
        'An export is an ordinary save: same format, same forward migrations. '
        'A copy made today still opens after the format has moved on, which '
        'is the entire reason saves carry a schema number.\n\n'
        'Both refuse to write over something without `--force`, and '
        '`restore --import` takes `--as <slot>` if you want it filed '
        'somewhere other than `imported`.\n\n'
        '[warn]The decision:[/] a character you have put forty shifts into is '
        'one disk failure from gone, and the only thing standing between '
        'those two states is you having typed `save --export` once.',
        see=('death', 'basics', 'shell'),
        commands=('save', 'restore', 'characters', 'switch', 'delete', 'reset'),
        terms=('backup', 'savegame', 'load game', 'roster', 'start over',
               'fresh', 'wipe',
               'multiple characters', 'slots', 'another character'),
        group='start'),
    # -- how a run works --------------------------------------------------
    Topic(
        'triangle', 'Noise, trace, and residue',
        'The three numbers, and why they are three and not one.',
        'These are the game. They are deliberately separate and they behave '
        'nothing alike.\n\n'
        '[noise]NOISE[/] is local and it fades. It sits on the node you are '
        'standing in, it wakes the countermeasures on that node, and enough '
        'of it escalates the whole network\'s alert level. It drops by 2 every '
        'tick, so a moment of standing still genuinely helps.\n\n'
        '[trace]TRACE[/] is the clock. It runs from 0 to 100, it never goes '
        'down on its own, and when it fills, somebody at the other end cuts '
        'you loose. It advances a little every tick and a lot when you are '
        'loud, so it is fed by both the time you spend and the noise you '
        'make, and the two are not equal: [warn]a tick in which you made no '
        'noise costs 0.45 and a tick in which you did costs 1.1[/], before '
        'the alert level multiplies either. That is what makes [fg]wait[/], '
        '[fg]--quiet[/], Ghost and Sidechannel worth the time they take, and '
        'why a big network works for you: twenty hosts is more traffic to be '
        'lost in, and runs the clock about a fifth slower than eight.\n\n'
        '[residue]RESIDUE[/] is evidence. It does not affect the run at all. '
        'It sits on the nodes you touched, you carry it out with you, and a '
        'shift later it becomes that faction\'s heat on your name.\n\n'
        '[warn]Here is the whole tension:[/] cleaning up residue costs ticks, '
        'and ticks feed the trace. Getting out [ul]clean[/] and getting out '
        '[ul]at all[/] pull in opposite directions, and you cannot have both '
        'unless you were fast enough earlier to afford the difference.',
        see=('alert', 'heat', 'basics'),
        commands=('status', 'scrub', 'mask', 'wipe'),
        terms=('trace', 'noise', 'residue', 'timer',
               'countdown', 'evidence', 'stealth meter'),
        group='systems'),
    Topic(
        'checks', 'How anything is decided',
        'The one formula, and why you can always see it.',
        'Everything rolls the same way:\n\n'
        '  [accent]margin = what you bring + d10 - what resists you - 5[/]\n\n'
        'Zero or better succeeds. A margin of 8 or more is a critical, minus '
        'eight or worse is a fumble.\n\n'
        '"What you bring" is your skill doubled, plus the governing attribute, '
        'plus the rating of the program doing the work, plus gear bonuses, '
        'plus or minus the situation. Every one of those is itemised.\n\n'
        '[warn]There are no hidden dice in this game.[/] Type [fg]odds[/] '
        'before any crack and it prints the whole sum and the exact '
        'percentage. When something fails, it prints the sum again and names '
        'the term that sank it. If a number surprises you, the game is '
        'obliged to show its working, and it will.',
        see=('attributes', 'skills', 'programs'),
        commands=('odds',),
        terms=('dice roll', 'random', 'probability', 'rng',)),
    Topic(
        'ice', 'Countermeasures, and reading them',
        'Seven behaviours, and the tell that always comes first.',
        'ICE is what defends a network. There are seven kinds and they ask '
        'seven different questions:\n\n'
        '  [ice]sentry[/]   watches, reports. Will you pay to be quiet?\n'
        '  [ice]probe[/]    roams looking for you. Move, or hide?\n'
        '  [ice]hunter[/]   locks on and damages your deck. Fight or run?\n'
        '  [ice]trap[/]     invisible until sprung. Did you look first?\n'
        '  [ice]warden[/]   holds a boundary. Break it, or satisfy it?\n'
        '  [ice]herder[/]   never touches you, closes your routes instead\n'
        '  [ice]black[/]    lethal. One of the two things that can kill '
        'you; the street is the other\n\n'
        '[warn]Everything that can act telegraphs first.[/] One tick before a '
        'construct strikes, it prints a line describing what is happening: '
        '[dim]"the segment\'s routing table is being rewritten around you"[/] '
        'means a hunter is one tick from locking on. Learning to read tells is '
        'the highest skill ceiling in the game and it costs nothing to '
        'acquire.\n\n'
        'Traps are the deliberate exception: they never telegraph, because the '
        'counter to a trap is [fg]probe[/], not reflexes.\n\n'
        '[warn]The decision:[/] a tell is one free tick. Spend it moving, '
        'masking, striking, or leaving, but spend it.',
        see=('alert', 'triangle', 'death'),
        commands=('probe', 'strike', 'mask', 'overload'),
        covers=('ice',),
        terms=('countermeasure', 'security', 'defences',)),
    Topic(
        'alert', 'The alert level',
        'The network making up its mind about you.',
        'A network is at [ok]green[/], [warn]amber[/], [err]red[/], or '
        '[err]lockdown[/]. Each step multiplies how fast the [trace]trace[/] '
        'advances: amber is 1.25x, red is 1.7x, lockdown is 2.4x. It rises '
        'when a node gets too [noise]noisy[/], when a sentry files on you, '
        'when a pretext fails, and when you do something spectacular like an '
        'overload.\n\n'
        '[ok]It can come back down.[/] A response desk that has found '
        'nothing for a while stands down: nine ticks with nothing new filed '
        'against you, or six consecutive ticks in which you made no noise '
        'anywhere, takes it down one level. Every fresh escalation resets '
        'both counters. [fg]wait[/] is the verb for buying that on purpose, '
        'and it is the only thing in the run that makes no noise at all.\n\n'
        '[warn]The decision:[/] alert is the reason a slow careful run beats '
        'a fast loud one over the length of a whole network. At red your '
        'trace runs at nearly double speed, so every tick after that costs '
        'nearly twice what it cost at green, and nine quiet ticks to buy the '
        'multiplier back is a trade worth doing arithmetic on: it is usually '
        'right early in a long run and usually wrong near the end of a short '
        'one.',
        see=('triangle', 'ice'),
        commands=('status', 'wait', 'mask', 'jack out'),

        terms=('alarm',)),
    Topic(
        'objectives', 'The six kinds of job',
        'What contracts actually ask for.',
        '  [accent]exfiltrate[/]  take a named asset out. Needs a payload '
        'program.\n'
        '  [accent]implant[/]     leave something behind that survives the '
        'quarter.\n'
        '  [accent]corrupt[/]     edit a record so it has always said '
        'something else.\n'
        '  [accent]wipe[/]        destroy an asset. Loud, and it does not need '
        'carrying out.\n'
        '  [accent]surveil[/]     sit on the objective node and [fg]observe[/] '
        'for eight clean ticks.\n'
        '  [accent]escort[/]      another runner is in there. They have to '
        'come out alive.\n\n'
        '[warn]Two of these invert the game.[/] Surveil asks you to get '
        'somewhere valuable and then do nothing, while every instinct the rest '
        'of the game has trained says take one more thing. Escort puts '
        'somebody else in the network generating noise you did not choose, and '
        '[fg]signal[/] is advice rather than an order.\n\n'
        'The contract tells you what it needs before you go in, and '
        '[fg]jack in[/] will refuse if you are missing the program for it.\n\n'
        '[warn]The decision:[/] objectives reward different builds. A stealth '
        'character should be reading the board for surveil work, and a loud '
        'one should be taking wipes. Taking the wrong shape of job for your '
        'build is the most common reason a run goes badly.',
        see=('basics', 'rivals'),
        commands=('board', 'take', 'observe', 'signal'),
        covers=('nodes',),
        terms=('mission', 'goal', 'quest',)),

    # -- what you are made of ---------------------------------------------
    Topic(
        'attributes', 'The five attributes',
        'What each one is for, and what being short on it feels like.',
        '[accent]Logic[/] builds exploits and breaks encryption. It drives '
        'Focus. Low Logic means services read as noise.\n\n'
        '[accent]Reflex[/] is speed. It drives Tempo, which banks free '
        'actions as you work: at Tempo 2 every third tick hands you a verb '
        'that costs nothing, at 3 every second. It also decides whether a '
        'construct that lunges at you gets you. Low Reflex means everything '
        'happens to you before you happen to it.\n\n'
        '[accent]Nerve[/] holds you together under black ICE and drives '
        'Composure. Low Nerve means you fold at the moment folding is fatal.\n\n'
        '[accent]Guile[/] is pretexting and forged credentials: the whole '
        'argument that the cheapest exploit is a plausible voice. It drives '
        'Cover, and the city reads it directly: what a shop charges you, and '
        'how much a stranger tells you when you do legwork. Low Guile means '
        'every door has to be broken and every price is the asking price.\n\n'
        '[accent]Grit[/] is capacity. It drives Bandwidth, which is how much '
        'chrome fits in you, and Integrity, which is how much damage you '
        'absorb.\n\n'
        '[warn]What they turn into:[/]\n'
        '  Bandwidth = 8 + Grit          chrome capacity\n'
        '  Integrity = 10 + 2x Grit      damage before the run ends\n'
        '  Focus     = 3 + Logic/2       precision actions per run\n'
        '  Tempo     = 1 + Reflex/4      free actions banked, capped at 3\n'
        '  Composure = 2x Nerve + Drift/10   holding under black ICE\n'
        '  Cover     = 2x Guile          how fast heat cools\n\n'
        '[warn]The decision:[/] attributes are broad and slow. They set your '
        'ceilings. Skills decide what you can do at all, so early points '
        'usually go to whichever attribute your intended skills check against.',
        see=('skills', 'chrome', 'checks'),
        commands=('char', 'boost'),
        covers=('attributes',),
        terms=('stats',),
        group='character'),
    Topic(
        'skills', 'The fourteen skill lines',
        'What each buys, and why ranks 2 and 4 are the ones that matter.',
        '  [accent]Intrusion[/]     breaking services. The bread and butter.\n'
        '  [accent]Cryptography[/]  encrypted stores and key material.\n'
        '  [accent]Architecture[/]  reading a network as a structure.\n'
        '  [accent]Daemonology[/]   automation that acts without you.\n'
        '  [accent]Subterfuge[/]    talking your way in instead.\n'
        '  [accent]Sabotage[/]      breaking things so it looks like they '
        'broke.\n'
        '  [accent]Stealth[/]       making everything you do quieter.\n'
        '  [accent]Signal[/]        traffic rather than machines.\n'
        '  [accent]Warfare[/]       killing countermeasures instead of '
        'avoiding them.\n'
        '  [accent]Psyche[/]        the part of you that is actually in '
        'there.\n'
        '  [accent]Hardware[/]      deck tuning, overclocking, hotswaps.\n'
        '  [accent]Forensics[/]     managing what you leave behind.\n'
        '  [accent]Streetcraft[/]   reading a street, and being read by it '
        'the way you meant.\n'
        '  [accent]Fieldcraft[/]    the body on the street: carrying hurt, '
        'walking far, staying up.\n\n'
        'The last two are the half of the game that happens with the deck in '
        'the bag. See `help street`.\n\n'
        '[warn]Every attribute governs at least two of them[/], four for '
        'Logic and two or three for everybody else, so there is no attribute '
        'you can safely ignore and no single best one.\n\n'
        '[warn]Ranks 2 and 4 of every line unlock a technique[/], which is a '
        'new verb in the shell or a new option on an existing one. Ranks 1, 3 '
        'and 5 are numeric fill. That is the whole shape of progression here: '
        'you are buying [ul]new things to type[/], not bigger numbers.\n\n'
        'Costs rise steeply: 2, 4, 7, 11, 16 experience. Rank 5 in one line '
        'costs as much as rank 2 in six lines.\n\n'
        '[warn]The decision:[/] breadth gets you more verbs, depth gets you '
        'better odds on the ones you have. Two techniques at rank 2 in '
        'different lines will change how a run plays more than one rank 4.',
        see=('attributes', 'techniques', 'traits', 'origins', 'checks'),
        commands=('skills', 'train', 'techniques'),
        covers=('skills',),
        terms=('levelling', 'leveling', 'training',),
        group='character'),
    Topic(
        'techniques', 'Techniques',
        'The twenty-eight things ranks 2 and 4 unlock.',
        'Every skill unlocks one technique at rank 2 and another at rank 4. '
        '[fg]techniques[/] lists the ones you have; [fg]skills[/] shows the '
        'next one coming.\n\n'
        'They are the reason a Daemonology build plays a different game rather '
        'than the same game better. A few worth knowing about before you '
        'spend:\n\n'
        '  [accent]Chain[/] (Intrusion 2)     two services, one action\n'
        '  [accent]Pivot[/] (Intrusion 4)     enter a neighbour on trust, '
        'silently\n'
        '  [accent]Overclock[/] (Hardware 2)  extra actions, at real heat\n'
        '  [accent]Ghost[/] (Stealth 2)       move making no noise at all\n'
        '  [accent]Nullsig[/] (Stealth 4)     stop the trace outright, briefly\n'
        '  [accent]Scrub[/] (Forensics 2)     the only way to reduce residue\n'
        '  [accent]Script[/] (Daemonology 2)  automation that checks before it '
        'acts\n\n'
        '[warn]Chrome cannot buy a technique.[/] An implant that grants +1 '
        'Intrusion makes you better at cracking; it does not teach you to '
        'Pivot. Techniques come from trained rank only.\n\n'
        '[warn]The decision:[/] read the rank 2 techniques before you spend '
        'anything. Four experience for a new verb is the best value in the '
        'game, and which four verbs you own is most of what makes your '
        'character yours.',
        see=('skills', 'scripting'),
        commands=('techniques', 'train'),
        terms=('abilities',),
        group='character'),
    Topic(
        'origins', 'Origins and signature abilities',
        'Ten backgrounds, and the one thing each of them can do that nobody '
        'else can.',
        'An origin sets where you start and never where you can go. It gives '
        'you an attribute shape, opening gear, faction standing, a passive, '
        'and a complication that is already true about the world on shift '
        'one.\n\n'
        'It also gives you a [accent2]signature ability[/]: one verb, once '
        'per run, that no other character in this city has access to. It '
        'cannot be trained, bought, or shared, because the only way to have '
        'it is to have been that person.\n\n'
        '  [accent]policy[/]           read what a node logs, and erase '
        'yourself from it\n'
        '  [accent]jury[/]             bring a destroyed component back from '
        'nothing\n'
        '  [accent]vouch[/]            spend the Switchboard\'s name instead '
        'of a credential\n'
        '  [accent]firstprinciples[/]  derive a key instead of breaking one\n'
        '  [accent]playbook[/]         every construct telegraphs early, for '
        'the whole run\n'
        '  [accent]native[/]           stop using the interface; move as '
        'though it were a room\n'
        '  [accent]requisition[/]      a program you do not own, on '
        'somebody else\'s paperwork\n'
        '  [accent]remember[/]         retry the check you just failed, at '
        'full skill\n'
        '  [accent]nobody[/]           the trace resets to zero; there is '
        'nothing to attach it to\n'
        '  [accent]backway[/]          move to any node you have seen, from '
        'anywhere, silently\n\n'
        'Your complication is also a storyline. Kagawa really do want the '
        'laptop, Mara really is owed something, and the package really is '
        'still in your bag. See `help threads`.\n\n'
        '[warn]The decision:[/] the signature is the reason to choose one '
        'origin over another, and it is the part that will still be shaping '
        'your runs forty shifts in. Read all ten before you pick.',
        see=('attributes', 'traits', 'threads', 'appearance'),
        commands=('new', 'char'),
        covers=('origins',),
        terms=('background', 'class', 'starting character',),
        group='character'),
    Topic(
        'traits', 'Traits',
        'The axis where the pool is much bigger than the slots.',
        'Skills say what you can do. Chrome says what you are made of. '
        '[accent]Traits say what you are like.[/]\n\n'
        'You pick two at creation and earn one more every six runs, to a '
        'maximum of five, out of a pool of twenty-nine. That asymmetry is the '
        'entire point: no two characters are taking the same five, so the '
        'question stops being "what is optimal" and becomes "what is this '
        'person".\n\n'
        'Every one of them cuts both ways. Impatient makes everything you do '
        'faster and takes away a tick of warning before ICE strikes. Greedy '
        'gives you better legwork and means you physically cannot leave a '
        'node with anything still on it. Nobody Taught You makes you better '
        'with hardware and worse with anything genuinely unfamiliar.\n\n'
        'Some of them refuse to sit together. You cannot be both Impatient '
        'and Methodical, and you cannot have never had chrome and also be '
        'Wired For It.\n\n'
        '[warn]The decision:[/] traits are permanent and there are never '
        'enough slots, so take the two that make the character a person '
        'rather than the two that look strongest. The optimisation is not '
        'where the value is.',
        see=('skills', 'chrome', 'attributes', 'origins'),
        commands=('trait',),
        covers=('traits',),
        terms=('perks', 'flaws',),
        group='character'),
    Topic(
        'chrome', 'Cyberware and Dissonance',
        'Nothing here is a pure upgrade, and the cost is permanent.',
        'Chrome charges you twice, and the two costs are nothing like each '
        'other.\n\n'
        '[accent]Bandwidth[/] is hard capacity: 8 + Grit, and pieces cost 1 to '
        '4. That is a wall. [accent2]Dissonance[/] is the long arc, 3 to 22 a '
        'piece, and it never goes down on its own.\n\n'
        'There are ten slots and thirty-four pieces competing for them:\n\n'
        '  neural 2     the deck interface, and what sits beside it\n'
        '  cortex 2     processing, memory, the parts that change how you think\n'
        '  limb 2       hands and arms\n'
        '  subdermal 2  power, cooling, storage\n'
        '  ocular 1     you get one set of eyes\n'
        '  spinal 1     the bandwidth trunk, the expensive one\n\n'
        'So the question is never whether you can afford it. It is '
        '[warn]what you are taking out to fit it[/].\n\n'
        'Every piece carries a specific named drawback, in the fiction and in '
        'the numbers. A reflex governor removes the hesitation between '
        'deciding and acting by removing the hesitation, so your pretexts '
        'suffer. If a piece cannot be given an honest downside it does not '
        'exist. You buy it at a clinic or a fence and [fg]install[/] it at a '
        'clinic, which costs a shift.\n\n'
        '[accent2]Dissonance is the interesting one.[/] It makes you better in '
        'the net and worse in the city. Composure against black ICE is Nerve '
        'x2 + Dissonance/10, and it buys the coherence to wear icons no person '
        'could hold. In exchange, past 50 the shops quote you differently, and '
        'past 75 social legwork closes entirely, because a pretext needs a '
        'voice that does not lag and yours does.\n\n'
        'The bands sit at 0, 25, 50 and 75, and each has something written for '
        'the crossing that you see exactly once. Past 50 the back of a clinic '
        'opens, and [warn]restricted chrome is sold nowhere else[/]: the best '
        'hardware in the city is available only to people who have gone too '
        'far to be sold anything else.\n\n'
        '[err]Taking chrome out does not lower your Dissonance.[/] The piece '
        'comes out, the benefit goes, the drift stays. [fg]ground[/] at a '
        'clinic buys some back, at real money, three shifts and real damage, '
        'and it can never take you below what your installed hardware itself '
        'accounts for. You can walk back what the work did to you. You cannot '
        'walk back architecture while it is still in you.\n\n'
        '[warn]The decision:[/] a full-chrome build is a real playstyle, not a '
        'punishment track. But you are choosing who to be rather than renting '
        'it, and the one trait that opts out of this system entirely is worth '
        'reading before you fit anything.',
        see=('attributes', 'icons', 'money', 'traits', 'chemistry'),
        commands=('chrome', 'install', 'uninstall', 'clinic', 'ground'),
        covers=('cyberware', 'dissonance'),
        terms=('cyborg', 'implant', 'augmentation', 'surgery', 'prosthetic',),
        group='character'),
    Topic(
        'deck', 'The deck and memory',
        'Six slots, and the constraint that decides your playstyle.',
        'Your deck has six component slots and every one is a trade: '
        '[accent]cpu[/] buys actions and pays in heat, [accent]memory[/] buys '
        'programs, [accent]io[/] buys throughput, [accent]cooling[/] buys the '
        'headroom that makes overclocking survivable, [accent]masking[/] buys '
        'trace resistance at the cost of memory, and [accent]antenna[/] buys '
        'reach at the cost of signature.\n\n'
        '[warn]Memory is the real constraint on playstyle.[/] Programs occupy '
        'it, you will never have enough, and what you choose to carry into a '
        'specific run is the most frequent interesting decision in the game. '
        'It happens before you jack in, and the loadout is fixed once you are '
        'inside.\n\n'
        'A deck that is good at everything does not exist at any price.\n\n'
        '[warn]The decision:[/] do legwork first. Knowing what is in there is '
        'what turns the loadout from a guess into a choice.',
        see=('bench', 'programs', 'contracts'),
        commands=('deck', 'load', 'unload', 'fit', 'buy', 'repair', 'inspect'),
        covers=('hardware',),
        terms=('rig', 'computer',),
        group='character'),
    Topic(
        'bench', 'Salvage and bench work',
        'Changing a component you own, in a direction nobody sells.',
        'There is no crafting in this city and there is a bench. The '
        'difference matters: nothing here produces an item, because a system '
        'that made catalogue goods out of materials would be a discount on '
        'the market with extra steps, and every price in the shop would mean '
        'less. What a bench does is change something you already own.\n\n'
        '[accent]Scrap[/] comes from what you were throwing away anyway. '
        'Fitting a component puts the old one in the bag, and over a campaign '
        'the bag fills with things nobody will buy at a price worth the walk. '
        '[fg]salvage[/] at a workshop turns any of it into scrap, badly, on '
        'purpose. A destroyed component counts, and is often worth more in '
        'pieces than the repair costs.\n\n'
        '[accent]Bench work[/] spends the scrap. [fg]mod[/] lists what can be '
        'done to each thing in your deck, and [warn]every one of them is a '
        'trade[/]: one axis up, another down, on that specific component, '
        'permanently. Airflow bought with noise. Quiet bought with heat. A '
        'stripped chassis that is faster and will never be cheap to repair '
        'again. Nothing here comes out ahead, and the build fails if anything '
        'does.\n\n'
        'Two things carry no more than two pieces of work each, so the second '
        'choice is made against the first rather than in addition to it. And '
        'the work is done to the metal rather than to you: sell the '
        'component and the tuning goes with it.\n\n'
        '[warn]The decision:[/] the shop sells you a better component. The '
        'bench sells you a stranger one. A deck nobody else could have bought '
        'is worth having precisely because every part of it is worse at '
        'something, and you chose which.',
        see=('deck', 'programs', 'money', 'triangle'),
        commands=('salvage', 'mod', 'repair', 'deck'),
        covers=('mods',),
        terms=('upgrade', 'modding', 'workbench', 'recycle',
               'customise a deck', 'make things'),
        group='character'),
    Topic(
        'programs', 'Programs',
        'What a verb reaches for, and why the best one is the loudest.',
        'Programs do nothing on their own. They are what a verb picks up: '
        '[fg]crack[/] needs a breaker, [fg]mask[/] needs a mask, '
        '[fg]pull[/] needs a payload. A build carrying no wiper can still run, '
        'it simply cannot clean up after itself.\n\n'
        'Every program has a [accent]rating[/] and a [accent]signature[/], and '
        '[warn]they are deliberately not correlated[/]. The strongest breaker '
        'in the game is also the loudest thing on the market; the quietest one '
        'is barely adequate. So "bring the strongest thing" is not '
        'automatically correct, and a stealth loadout is not simply a weaker '
        'loadout.\n\n'
        'Verbs take your best loaded program of the right kind by default. '
        '[fg]--quiet[/] swaps to your lowest-signature one and takes a '
        'penalty, which is exactly why carrying both is a real loadout.\n\n'
        'A program runs at full rating only for somebody who can drive it: '
        'on a check its rating is [warn]held to your skill rank plus two[/], '
        'and the sum says so when it bites. A rating-six breaker in the '
        'hands of Intrusion 0 is a rating two, and training is the way up.\n\n'
        'Passive effects, the numbers a mask or an armour gives while it is '
        'merely loaded, count for [warn]the strongest program of each kind '
        'only[/]. Two masks are not twice the mask. An armour program is '
        'good for as many saves as its rating, and then it is [err]gone for '
        'good[/]: not spent for the night, destroyed, off the deck and out '
        'of the bag. '
        '[fg]inspect <name>[/] reads any program before you pay for it.\n\n'
        '[warn]The decision:[/] every slot spent on insurance is a slot not '
        'spent on capability. Armour and masks are invisible until the run '
        'they save, and a build that never carries them wins more often and '
        'loses harder.',
        see=('deck', 'triangle'),
        commands=('load', 'deck', 'market', 'inspect'),
        covers=('programs',),
        terms=('software', 'tools',),
        group='character'),
    Topic(
        'icons', 'Your icon',
        'What cyberspace renders you as, and why it is mechanical.',
        'Every netrunner renders as something. The deck has to put a body on '
        'you before the net will talk to you, and what you choose to be in '
        'there changes how loud you are, how ICE classifies you, and whether '
        'anything will talk to you at all.\n\n'
        'It is the [ul]cheapest[/] customisation axis to change: skills cost '
        'experience, chrome costs Dissonance you never get back, an icon is a '
        'file. Carry several and wear the right one for the job.\n\n'
        '[accent2]Coherence[/] is the constraint. An icon far from a human '
        'shape is hard to hold together, and holding one costs you unless your '
        'Dissonance has already done the work. A Process icon renders you as a '
        'scheduled maintenance job, needs 50 Dissonance, and cannot speak to '
        'anything at all.\n\n'
        '[warn]The decision:[/] because it is cheap to change, an icon is '
        'where to experiment. Buy a strange one and wear it for a run you can '
        'afford to lose.',
        see=('chrome', 'appearance'),
        commands=('icon',),
        covers=('icons',),
        terms=('avatar',),
        group='character'),
    Topic(
        'scripting', 'Scripts and daemons',
        'Automation that checks before it acts.',
        'Daemonology rank 2 unlocks [fg]script[/], and a script here is not a '
        'macro: it has conditions.\n\n'
        '  [fg]scan[/]                        a plain command\n'
        '  [fg]if trace > 40: mask[/]         runs only when the check holds\n'
        '  [fg]stop if alert >= red[/]        abandons the rest\n'
        '  [fg]repeat 3: crack gw01 shell[/]  bounded, one to ten\n\n'
        'Conditions read live state by name: trace, noise, focus, integrity, '
        'tick, haul, residue, tier as numbers; ice, locked, open, data, '
        'mapped, ally, escort as yes-or-no; and alert, which compares by rank.\n\n'
        'Rank 4 unlocks [fg]daemon[/], and a daemon can be handed a script as '
        'its behaviour policy: it re-reads it every tick and does whatever the '
        'first passing condition says.\n\n'
        '[dim]`script help` prints the whole vocabulary, and `script example '
        'bailout` copies a working one into your library.[/]\n\n'
        '[warn]The decision:[/] a script is where you put the check you keep '
        'forgetting to make by hand. Write the bailout first and the clever '
        'ones later.',
        see=('techniques',),
        commands=('script', 'daemon'),
        terms=('automation', 'batch',),
        group='character'),

    # -- the city ---------------------------------------------------------
    Topic(
        'city', 'The city and time',
        'Everything costs shifts, and the board does not wait.',
        'Time moves in [accent]shifts[/], three to a day. Travelling costs '
        'one, legwork costs one, resting costs as many as you spend, and '
        'establishing a new identity costs two.\n\n'
        'Twelve districts, and [accent]travel only goes to a neighbour[/], so '
        'somewhere on the far side of the city costs two or three shifts to '
        'reach and the contract expiring is counting all of them. [fg]map[/] '
        'draws the city, marks where you are and where the job is, and says '
        'how many shifts each district is from here. [fg]walk <district>[/] '
        'goes the whole way, a shift a step, and stops if the street stops '
        'you. Anything that sends you somewhere hands you the walk as a line '
        'you can type.\n\n'
        'While shifts pass: contracts expire, heat decays, market stock '
        'rotates, faction posture drifts back toward baseline, and '
        '[warn]other runners take work off the board[/].\n\n'
        'That last one matters more than it sounds. Sitting still is not a '
        'free way to let heat cool. It is a way to let somebody else make the '
        'city more expensive, because when a rival succeeds against a faction, '
        'that faction hardens for you too.\n\n'
        'A district is also somewhere to stand. [fg]look[/] shows what it is '
        'doing at this hour, who is about, and the two or three places a '
        'person would actually go: [fg]visit <place>[/] goes and stands in '
        'one, for nothing. [fg]news[/] is the wire: what the city did while '
        'you were not looking, most of which printed once and scrolled away.'
        '\n\n'
        '[warn]The decision:[/] doing nothing is a real strategy with a real '
        'price, and knowing when to pay it is most of the city layer.'
        '\n\n'
        'The city is bigger than the twelve names on the map. Every '
        'district is built of something, works at something, and is '
        'made of quarters, and [fg]district[/] reads the whole of one '
        'from anywhere: how many people, what it is made of, what they '
        'do for money, what its corners are called, who holds it, who '
        'else has people in it, and what is past its edge. [fg]look[/] '
        'is what is in front of you this hour; district is the place '
        'itself. Crossing between two of them takes a shift, and says '
        'what you went through to get there.',
        see=('heat', 'rivals', 'contracts', 'reading', 'clock', 'relics'),
        commands=('travel', 'walk', 'map', 'district', 'rest', 'board',
                  'look', 'visit', 'news'),
        covers=('districts', 'shifts', 'spots'),
        terms=('moving around', 'getting about',),
        group='city'),
    Topic(
        'contracts', 'The board and legwork',
        'Where work comes from, and what to do before taking it.',
        'The board is generated from the state of the world: who currently '
        'dislikes whom enough to pay, and what they want done. Raise the '
        'Switchboard\'s opinion of you and their work appears. Burn Kagawa '
        'badly enough and their rivals start offering money to do it again.\n\n'
        'Contracts expire after four to nine shifts, so shopping around has a '
        'real cost.\n\n'
        '[accent]Legwork[/] is what you do between taking a job and running '
        'it. Each approach costs a shift and most cost money, and what you '
        'learn is real: known topology, known countermeasure placement, a '
        'credential that skips a boundary, or where the valuable assets '
        'actually are.\n\n'
        'All of it except resonance is asking people things, so what you come '
        'back with depends on more than the money: your [accent]Guile[/], what '
        'you are read as when you walk up, and whether there is anybody about '
        'at that hour. Resonance is the exception, because you are not asking '
        'anybody anything.\n\n'
        '[warn]The decision:[/] legwork is what turns your loadout from a '
        'guess into a choice. A run you did no legwork for is a run you packed '
        'for blind.',
        see=('city', 'deck', 'objectives'),
        commands=('board', 'take', 'legwork'),
        terms=('jobs', 'gigs',),
        group='city'),
    Topic(
        'heat', 'Heat, aliases, and bounties',
        'What the residue turns into, and what to do about it.',
        'A shift after a run, the residue you left becomes [heat]heat[/] on '
        'the faction you ran. Heat is attention, not hatred: a faction can '
        'like you and still be looking for whoever did that thing last week.\n\n'
        'Heat decays slowly, at a rate each faction sets for itself. Corps '
        'forget faster than gangs, and the two gangs barely forget at all: '
        'Carrion heat outlasts most characters.\n\n'
        '[accent]Cover[/] is what you can do about that. It comes from Guile, '
        'it is on your sheet, and it makes every faction cool faster by 2.5% '
        'per point. At the top of the range that is heat gone in about seven '
        'shifts out of ten, forever, on every faction at once. `rep` shows '
        'what yours is doing.\n\n'
        'Sustained heat becomes a [err]bounty[/], and a bounty makes that '
        'faction\'s districts genuinely dangerous to walk into. Going anyway '
        'can get you picked up, and being picked up costs you one specific '
        'thing: credits, a beating, a damaged component, a piece of chrome '
        'taken out of you in a room you did not choose, or the name itself.\n\n'
        '[accent]Aliases[/] are the container. Heat accrues to the name you '
        'run under, and so does reputation. [warn]Burning an alias dumps both '
        'together[/], which is what makes it a hard decision rather than a '
        'consumable.\n\n'
        '[warn]The decision:[/] a new name costs money, two shifts, and every '
        'relationship you built under the old one. Sometimes that is cheaper '
        'than the bounty. Usually it is not.',
        see=('triangle', 'factions', 'death', 'safehouse', 'networks'),
        commands=('alias', 'burn', 'rep', 'rest'),
        terms=('wanted', 'police', 'arrest', 'hiding',),
        group='city'),
    Topic(
        'factions', 'The twelve powers',
        'Who is who, and why helping one hurts another.',
        'Twelve factions hold this city between them: three megacorps, a bank, '
        'two gangs, a fixer network, contracted enforcement, a dock '
        'collective, a chrome cult, a pirate press, and whatever Deepwater '
        'is.\n\n'
        'Every pair has an opinion about every other pair, and '
        '[warn]reputation propagates[/]. Helping the Switchboard warms the '
        'Sixes a little and cools Nightwatch a little, automatically. A player '
        'who reads the table can plan a run whose real payload is the '
        'political side effect.\n\n'
        '[accent]Posture[/] is the number that reaches into a run: it is how '
        'hard their networks generate, it rises every time you succeed against '
        'them, and it falls very slowly. A faction you have robbed four times '
        'generates a visibly meaner network, and you can watch it happen.\n\n'
        'Each faction\'s networks also [ul]look[/] different from inside, and '
        'their doctrine tells you what to expect before you go.\n\n'
        '[warn]The decision:[/] pick enemies deliberately. Working one side '
        'of the table consistently buys you cheaper contracts, better fence '
        'rates and softer targets on the other side, and there is no way to '
        'be liked by everybody.',
        see=('heat', 'contracts', 'rivals'),
        commands=('rep', 'board'),
        covers=('factions',),
        terms=('corporations', 'who is who',),
        group='city'),
    Topic(
        'rivals', 'The other runners',
        'Seven named people who are also working, and two of them will decide.',
        'Seven runners work this city and they are not scenery. They take '
        'contracts off the board while you deliberate, they harden the '
        'factions they succeed against, and they occasionally die doing it. '
        'That is why sitting still is not a free way to let heat cool: it is '
        'a way to let somebody else make the city more expensive.\n\n'
        'You can [fg]hire[/] one to come in with you for a cut, [fg]ask[/] '
        'one for a favour, and [fg]betray[/] one, which is the most lucrative '
        'thing in this game and the most expensive.\n\n'
        '[accent2]Past enough history, somebody makes up their mind.[/] What '
        'they think of you has always been a number between -100 and 100. '
        'Far enough either way, and after enough jobs, it stops being a '
        'number and becomes a person:\n\n'
        '  [err]a nemesis[/] talks about you to people who were not going to '
        'think of you, and your name starts arriving before you do\n'
        '  [ok]a partner[/] leaves things where you will find them, and a '
        'door somebody was going to close stays open\n\n'
        'Each announces itself once, in their own register, and then changes '
        'what they do for the rest of the campaign. [warn]It does not come '
        'off[/]: a bond that reversed because you did somebody a favour on a '
        'Tuesday would be a mood, and the point of thirty runs with the same '
        'person is that it lasts.\n\n'
        '[accent2]And one of them can stop being somebody you rent.[/] '
        '[fg]hire[/] buys a runner for one job, which is a transaction and '
        'cannot be lost. [fg]crew[/] puts somebody on a retainer: they come '
        'in on every run without being asked, take a smaller cut than a hire '
        'does, and get better at working with [ul]you[/] specifically, up to '
        'a point. They have to like you well enough first, which is a higher '
        'bar than taking a job.\n\n'
        'They can also die, and that is the reason the whole thing exists. A '
        'hire dying costs a fee and a paragraph. Somebody who has been '
        'standing next to you for thirty runs costs the thirty runs.\n\n'
        '[warn]The decision:[/] every one of them is worth being on good '
        'terms with and you cannot afford all seven, because the work you '
        'take is work somebody else wanted. Choosing who to disappoint is the '
        'whole of it, and it is much easier before anybody has decided.',
        see=('contracts', 'people', 'heat', 'factions'),
        commands=('who', 'hire', 'crew', 'ask', 'betray'),
        covers=('rivals',),
        terms=('competition', 'other runners', 'enemy', 'friend', 'team'),
        group='city'),
    Topic(
        'people', 'The people in this city',
        'Who to find, how to find them, and what they will do for you.',
        'The city has people in it who are not competing with you. [fg]look[/] '
        'is how you find them: who you run into depends on where you are, what '
        'you can get into there, and in some cases on what you have already '
        'done.\n\n'
        'They are not shops with faces on. Every one of them wants something, '
        'and it is not always your money. Some are trying to help you, some '
        'are lying about who they work for, one is a vending machine with '
        'opinions about a war in 2041, and one of them is dying and has '
        'decided not to ask you about it.\n\n'
        '[fg]talk[/] gets you a line. [fg]ask <name> <topic>[/] gets you what '
        'they think about something specific, and some of those answers open '
        'things. [fg]who is <name>[/] lists what somebody deals in, and '
        '[fg]deal <name>[/] is how you do it.\n\n'
        '[accent2]Work, goods and a favour are one relationship, not three '
        'features.[/]\n\n'
        '  [accent]work[/]    a contract that never reaches the board. It '
        'pays better, because they know you, and they hold it longer than a '
        'posting.\n'
        '  [accent]goods[/]   what they keep under their own counter. It does '
        'not rotate with the market, and it is the only supply of several '
        'things in this city.\n'
        '  [accent]favour[/]  them spending their own standing on your '
        'problem: heat gone, a job held open, a network read, some of the '
        'drift walked back.\n\n'
        'What ties them together is the tab. Every favour puts you one deeper '
        'with that person, and [warn]finishing work they handed you is how it '
        'comes off again[/]. Get too far down and they stop helping, in their '
        'own words, which are not always unkind. Drop a job somebody was '
        'holding for you and you go a favour further down rather than level.\n\n'
        '[warn]The decision:[/] talking costs nothing and no shift, so the '
        'only reason not to is not knowing they are there. Walk into districts '
        'you have no job in. And take the work before you need the favour, '
        'because the order those two happen in is the whole system.',
        see=('threads', 'rivals', 'city', 'contracts'),
        commands=('look', 'talk', 'ask', 'who is', 'deal'),
        covers=('npcs', 'offers'),
        terms=('npc', 'conversation', 'friends', 'contacts', 'relationships'),
        group='city'),
    Topic(
        'threads', 'Storylines',
        'Several at once, none of them waiting for you.',
        'There are no quest chains here. A thread is a set of scenes, each '
        'with its own condition, and a scene happens the moment its condition '
        'holds however that happened.\n\n'
        'Which means three things. **A thread can be entered more than one '
        'way**: you can come at Deepwater through the Archivist, through '
        'Remnant, through running one of their networks, or through asking '
        'Mara the wrong question. **Threads cross**: taking Doctor Vance\'s '
        'offer closes a door in Lark\'s story without either of them '
        'mentioning the other. And **nothing is ordered**, so you can get the '
        'fourth scene before the second if the world got there first.\n\n'
        '[fg]journal[/] lists what you have got yourself into. '
        '[fg]choose[/] handles anything waiting on a decision from you, and '
        'those do not come back round.\n\n'
        '[warn]The decision:[/] threads advance on what you were doing '
        'anyway, so the real choice is who you spend time near. Nothing here '
        'will chase you, and a thread you ignore simply resolves without you '
        'in it.',
        see=('people', 'city'),
        commands=('journal', 'choose', 'look'),
        covers=('threads', 'arcs'),
        terms=('storyline', 'plot', 'quests',),
        group='city'),
    Topic(
        'money', 'Credits and what things cost',
        'The economy, and what a run is actually worth.',
        'A contract pays on a curve against the target\'s posture and a '
        'multiplier for its size. A gang job is about [credit]1,600c[/], a '
        'corporate one about [credit]3,200c[/], and a Meridian sprawl about '
        '[credit]10,000c[/]. Size alone moves it a long way: a small job is '
        'worth four fifths of the standard one and a sprawl is worth more '
        'than twice it, because a sprawl is a night\'s work and there is '
        'more in it to carry out.\n\n'
        'On top of that you keep what you carried out, sold through the '
        'patron. [warn]What it clears depends on your standing with them[/]: a '
        'stranger gets under half of nominal, somebody trusted gets close to '
        'three quarters. Reputation is worth money, directly.\n\n'
        '[accent]Guile[/] takes 3% off every price you are quoted, per point, '
        'and it shows up in the terms when you look at something in a shop. It '
        'is small on one purchase, it never stops applying, and at the top of '
        'the range it is most of a quarter off everything you will ever '
        'buy.\n\n'
        'For scale: a good professional program is about one and a half '
        'contracts. A piece of restricted chrome or a top deck component is '
        'four or five. A new identity is under one.\n\n'
        '[warn]The decision:[/] stripping a network bare pays roughly twice '
        'what doing only the job pays. It also means touching every node, '
        'which is trace, noise, and residue you did not have to spend. That '
        'temptation is the game asking you a question every single run.',
        see=('triangle', 'contracts', 'deck', 'vices', 'legacy'),
        commands=('market', 'buy', 'sell', 'debt'),
        terms=('economy', 'income', 'earning', 'broke', 'poor',),
        group='city'),
    Topic(
        'vices', 'Borrowing against later',
        'Three ways to have something now and pay for it afterwards.',
        'The city runs on getting away with things temporarily. Residue '
        'becomes heat a shift after you thought you were clean, and the three '
        'vices are that same sentence in three registers: something now, '
        'priced afterwards, at a rate you were told first.\n\n'
        '  [fg]help borrowing[/]   money, and three people who lend it\n'
        '  [fg]help chemistry[/]   what you can put in yourself, and the bill\n'
        '  [fg]help gambling[/]    two games, both of which print the odds\n\n'
        'They are worth reading as one thing because they compound. A payload '
        'you cannot afford is a contract you cannot finish; two thousand '
        'credits at thirty-eight percent a shift is cheaper than a fortnight '
        'of not working; a stimulant makes the run that repays it go better; '
        'and the comedown lands on the shift the collector calls.\n\n'
        '[warn]The decision:[/] each of the three is correct sometimes. The '
        'trap is never the first one. It is taking the second to pay for the '
        'first.',
        see=('borrowing', 'chemistry', 'gambling', 'money', 'heat'),
        commands=('borrow', 'dose', 'dice'),
        terms=('temptation',),
        group='city'),
    Topic(
        'borrowing', 'Debt, and who lends',
        'Three lenders, and the difference is not the interest rate.',
        'You can owe exactly one person at a time. [fg]borrow[/] where '
        'somebody lends, which is Marrow, the Ninth Ward and the Shambles, and '
        'what they will put in front of you scales on your standing with them '
        'and on your record. It compounds every shift, including the ones you '
        'spend asleep, and the grace period counts from the day you took it '
        'rather than the day you stopped paying.\n\n'
        '  [accent]Switchboard[/]  Marrow, at the fixer. Lowest rate, longest '
        'grace, and they lend against work rather than against you.\n'
        '  [accent]The Sixes[/]    the Ninth, at the fence. More than is '
        'sensible, to people they have decided are local.\n'
        '  [accent]Carrion[/]      the Shambles, at the clinic. Eight '
        'thousand, to anybody, immediately, without asking what it is for.\n\n'
        'The rate is the least of it. What separates them is what happens when '
        'you stop paying. The Switchboard stop finding you work, which in a '
        'game where the board is the only income is slower and worse than it '
        'sounds. The Sixes come round in person. Carrion do not do collections '
        'at all, they do procedures, and they are the only ones whose limit '
        'does not scale on anything you have ever done.\n\n'
        'When the grace runs out they take a quarter of the outstanding '
        'balance every few shifts. [warn]If the account is empty they take it '
        'out of the room[/], which routes through the same fallout ladder as '
        'everything else: chrome, damage, or your name in somebody\'s file.\n\n'
        '[warn]The decision:[/] a debt is a clock that is not the trace, and '
        'it is the only one you can start yourself. Borrowing to buy the '
        'program that finishes the contract is usually right. Borrowing to '
        'cover the last loan is how people end up in the Shambles.',
        see=('vices', 'money', 'factions', 'death'),
        commands=('borrow', 'debt'),
        covers=('lenders',),
        terms=('loanshark', 'shark', 'interest', 'creditor', 'repay'),
        group='city'),
    Topic(
        'street', 'The street is real',
        'The half of the danger that happens with the deck in the bag.',
        'The net is half the game and the street is the other half, and the '
        'street has people in it. Walk into a district where a faction has a '
        'number on your name and some of them will be waiting: two on a '
        'kerb naming a price, three in a doorway with a photograph, four and '
        'a van, and, at the top of the ladder, people who have stopped '
        'asking. Nobody\'s people are out there too: somebody behind you for '
        'three streets, four kids in a walkway with one knife held wrong, a '
        'stairwell in the dark with a step missing.\n\n'
        'You do not fight. You [accent]run[/], you [accent]talk[/], you '
        '[accent]pay[/], or you [accent]stand[/] there, and each is a printed '
        'check like every other check in the game: Reflex and Fieldcraft to '
        'run, Guile and Streetcraft to talk, Grit and Fieldcraft to stand. '
        'Two skills are the street\'s: [fg]streetcraft[/] (Bolt at rank 2 '
        'leaves before it starts, once a day; A Face at rank 4 makes talking '
        'easier and paying cheaper) and [fg]fieldcraft[/] (Scar Tissue at 2 '
        'heals a point more per rest; Shrug at 4 halves the first hit).\n\n'
        'What it costs is Integrity, the same number the net spends, and '
        'credits, and heat, and sometimes the deck or a mark. At the top of '
        'the ladder it can cost everything: [err]the street can kill you[/], '
        'and it warns first, every time, in so many words. A night that ends '
        'with you at one Integrity and the sentence "next time they will not '
        'be asking" is the telegraph. Go back with the number still on your '
        'name and it is the strike.\n\n'
        'The street has work, too: [fg]errands[/]. Carry a package a few '
        'shifts across the city and get paid on arrival, or stand a shift on '
        'watch somewhere. No deck, no trace, the same street in the way. It '
        'is how a runner eats between runs, and how somebody who is not a '
        'runner at all might eat instead.\n\n'
        'And the street can be paid. [fg]arrange[/] a standing arrangement '
        'with a faction whose streets you need: their people are told, their '
        'streets are easier for you, the ones who stop you lean rather than '
        'take, and the number comes round every six shifts. Miss it and it '
        'ends, and they remember who ended it.\n\n'
        '[warn]The decision:[/] the city remembers, and the street is where '
        'it collects. `rep` and the map\'s x marks say where your name is '
        'worth money. Going anyway is a choice; so is `rest`, and so is '
        '`burn`, and so is paying.',
        see=('death', 'heat', 'skills', 'city'),
        commands=('errands', 'arrange', 'travel', 'rest', 'rep'),
        covers=('street',),
        terms=('mugging', 'ambush', 'encounter', 'beating', 'physical',
               'courier', 'odd jobs', 'violence'),
        group='city'),
    Topic(
        'relics', 'Things there is one of',
        'What is not for sale, where it might be, and why it is worth having.',
        'Most of what you will ever carry came off a shelf, and the shelf '
        'will have another one next week. A few things did not. They are one '
        'of a kind, they are never in any market, and each of them has a '
        'history: a dead runner\'s breaker with her handle in the header, a '
        'map of a district that turns out to be a map of networks, the piece '
        'somebody had taken out last and kept, a vial without a label.\n\n'
        'People know. Somebody standing in a district where something can '
        'be found will say what they have heard, once, when you [fg]talk[/] '
        'to them, which is the payoff for meeting people and the reason a '
        'district with somebody in it is worth the walk.\n\n'
        'They are found rather than bought. A place, at an hour, after '
        'something has happened: [fg]visit[/] somewhere at night that you have '
        'only stood in by day, go back to a place after a thing you did, '
        'listen to what a district keeps saying about itself. A few are '
        'given, by people you decided to work with, or by a decision in a '
        'story that was never about the item. None of it is announced. The '
        'city talks about them the way it talks about anything, which is '
        'sideways and once, and the talk stops when the thing is found.\n\n'
        'Every one of them does something nothing on a shelf does, and every '
        'one of them costs something, because that is the rule for '
        'everything in this game. [fg]inspect[/] one and it tells you its '
        'history as well as its numbers.\n\n'
        '[warn]The decision:[/] whether to go and look. Standing somewhere at '
        'the wrong hour costs nothing but the hour.',
        see=('city', 'threads', 'programs'),
        commands=('visit', 'inspect', 'look'),
        terms=('unique', 'rare', 'special', 'artifact', 'artefact', 'legendary'),
        group='city'),
    Topic(
        'chemistry', 'Drugs, tolerance, and habit',
        'What you can put in yourself, and what it takes back.',
        'Ten things, sold by clinics, fences, markets and one fixer, and not '
        'the same things at each counter. [fg]chem[/] is what is in you, '
        '[fg]chem <drug>[/] is what one will do at your current tolerance, and '
        '[fg]dose[/] takes it. It works out here and inside a run alike, and '
        'inside a run it costs a tick.\n\n'
        'Everything is up for a while and down for longer, and [warn]the crash '
        'always costs more than the high paid[/]. That is not balance, it is '
        'the rule the catalogue is written under, and the build fails if a '
        'drug breaks it. What you are buying is never the arithmetic. It is '
        'that the arithmetic lands at a different time from the problem.\n\n'
        '[accent2]Habit is the part worth understanding.[/] One number per '
        'drug does three jobs at once:\n\n'
        '  it weakens the high, so the same dose does less each time\n'
        '  it deepens the crash, so the same dose costs more\n'
        '  and past four it applies a third set of effects whenever you are '
        'not using\n\n'
        'That last one is the turn. Below it you are somebody who takes '
        'something occasionally. At it, your baseline is lower than the one '
        'you started with, and a dose stops making you better than a person '
        'and starts making you a person again. The number on your sheet that '
        'used to be five is four, and nothing did that except you.\n\n'
        'Five clean shifts sheds one point, and using anything at all resets '
        'that clock for every habit you have, which is why two are much worse '
        'than twice one. A clinic will [fg]detox[/] several points for money '
        'and a few shifts. Neither undoes what the using already cost.\n\n'
        'One thing in the catalogue ends a comedown early, exactly as '
        'advertised, and moves the price into the habit instead. One does '
        'nothing at all and is sold by a vending machine that believes in it '
        'completely.\n\n'
        'Timing matters twice. A high that adds Focus has to be in you '
        'before you jack in, because Focus is counted at the door; and a dose '
        'taken in the city covers the whole of a run, because the run is '
        'inside one shift.\n\n'
        '[warn]The decision:[/] a dose before a hard run is often correct, '
        'because the crash lands on a shift you were going to spend resting '
        'anyway. A dose to get through a crash is the moment the system starts '
        'happening to you rather than the other way round.',
        see=('vices', 'chrome', 'death', 'clock'),
        commands=('chem', 'dose', 'detox', 'clinic'),
        covers=('drugs',),
        terms=('addiction', 'addicted', 'dependency', 'withdrawal', 'overdose',
               'stim', 'narcotic'),
        group='city'),
    Topic(
        'gambling', 'Ninepins and Threes',
        'Two games, and both of them tell you the odds first.',
        'Nobody in these rooms is deceiving you. They are simply correct about '
        'how it will go on average, and you are going to play anyway, and that '
        'difference is most of the tone of this city.\n\n'
        '[accent]Ninepins[/] is [fg]dice[/], in the Ninth, the Shambles and '
        'Freeport. Two dice: high is 8 to 12, low is 2 to 6, and seven belongs '
        'to the house. That is a sixth of everything you put down, it is '
        'painted on the wall, and [warn]it is the same sixth on all three '
        'calls[/], so there is no correct bet and only a choice of how hard to '
        'breathe. Costs no time and needs nothing but money.\n\n'
        '[accent]Threes[/] is [fg]cards[/], in Marrow and the Vertical. An '
        'evening, so it costs a shift, and it is resolved on Guile and '
        'Subterfuge against the table rather than on what you were dealt. It '
        'is the one place in this game where a social build is a build rather '
        'than a discount on conversations, and how well you read them decides '
        'the payout. Most characters are turned away and pointed at the dice, '
        'which is the room being honest rather than the game being shut.\n\n'
        '[warn]Winning costs something that is not money.[/] Take enough off a '
        'room and the house thinks less of you, the table measurably learns '
        'how you play, and past five thousand in a single night everybody '
        'there can describe your face to somebody who was not.\n\n'
        '[warn]The decision:[/] the dice are a fast, stupid answer to being '
        'broke and they are honest about being one. The cards are an income '
        'for the right character, right up until the table works out what kind '
        'of character that is.',
        see=('vices', 'money', 'attributes', 'heat'),
        commands=('dice', 'cards'),
        covers=('games',),
        terms=('casino', 'betting', 'wager', 'luck'),
        group='city'),
    Topic(
        'safehouse', 'Somewhere of your own',
        'A place to put things, and a place that can be found.',
        'You have been resting in safehouses since the first shift and you '
        'could never have one. [fg]safehouse[/] buys you one, in a district '
        'that has them, and you get one at a time.\n\n'
        'It holds things and it holds money. [accent2]Both halves of that are '
        'the same half[/]: what makes storing anything a decision is that the '
        'store has an address, and what makes the address matter is that '
        'enough attention eventually finds it.\n\n'
        'Money under the boards is the interesting one. Credits on you are '
        'exposed to a collector, a mugging, and everything else in this city '
        'that takes cash out of a room. Credits in a floor cavity in the '
        'Ninth are exposed to exactly one thing, which does not happen often, '
        'and which takes most of it when it does. Neither is safe. They are '
        '[ul]differently[/] unsafe.\n\n'
        '[accent]What you pay for is security, not space.[/] The cheap ones '
        'hold as much as the expensive ones and are turned over much sooner, '
        'because the difference between a floor cavity and a bonded container '
        'is not volume, it is how many people have to be paid before somebody '
        'looks inside.\n\n'
        '[warn]Nobody comes looking at all[/] while the faction whose ground '
        'it is on has no interest in you. Being unknown is the best security '
        'in this game and it costs nothing, and no amount of money buys a '
        'substitute for it. Get turned over twice and the place is finished: '
        'the second visit is somebody establishing that they know where you '
        'live.\n\n'
        '[warn]The decision:[/] this is the only thing in the city that makes '
        'heat physical. Everywhere else, being wanted is a multiplier on a '
        'roll. Here it is somebody in your room.',
        see=('heat', 'money', 'city', 'legacy'),
        commands=('safehouse', 'rest'),
        covers=('safehouses',),
        terms=('storage', 'stash', 'hideout', 'home', 'base', 'raid'),
        group='city'),
    Topic(
        'legacy', 'Getting out, and what is left',
        'The two endings, and the one thing each of them leaves behind.',
        'This game has been called Flatline since the first day and the '
        'flatline ended into a scoreboard. It remembers factions, districts, '
        'postures and the evidence you left on a node three weeks ago, and it '
        'forgot [ul]you[/] the moment you stopped breathing. There were also '
        'only two exits, and one of them was closing the terminal.\n\n'
        '[accent2]There is a door.[/] [fg]retire[/] wants four things, and '
        'every one of them is something the city has spent your whole career '
        'making harder:\n\n'
        '  nothing owed to anybody\n'
        '  nothing in you that you need\n'
        '  nobody paying for your name\n'
        '  enough put away, which is a lot\n\n'
        'None is hard on its own. All four at once is the campaign. Type '
        '[fg]retire[/] any time to see how far off you are.\n\n'
        'Dissonance does not gate it. Somebody four fifths machine can walk '
        'out of this business, and what they walk out into is a different '
        'ending, which is a better answer than a refusal. There are four, and '
        'the drift you carry decides which one you get.\n\n'
        '[accent2]Whichever way you go, you leave exactly one thing[/], and '
        'it reaches whoever you make next. A retirement leaves what somebody '
        'chose to leave: a share of the stake, or a name that still opens one '
        'door. A flatline leaves what could not be stopped from being taken '
        'and what could not be forgiven: a piece of you on a shelf in the '
        'Shambles, a program still in circulation with your handle in the '
        'header, or [warn]a debt somebody fully expects the next person to '
        'honour[/].\n\n'
        'You do not choose which. An inheritance you picked would be a '
        'difficulty setting with prose on it; one that turns up on your '
        'second day is the city having an opinion about how you went. And '
        'afterwards it talks about you, occasionally, to somebody who never '
        'met you and is standing where you used to stand.\n\n'
        '[warn]The decision:[/] the door has been open since your first '
        'shift. Every loan, every habit and every bounty is a thing you put '
        'between yourself and it, usually for a good reason at the time. '
        'Knowing when to stop taking those reasons is the only long game this '
        'city has.',
        see=('death', 'vices', 'chrome', 'money'),
        commands=('retire', 'career'),
        covers=('legacy',),
        terms=('quit the game', 'successor', 'endgame', 'winning',
               'estate', 'bequest', 'heir'),
        group='city'),
    Topic(
        'death', 'How it goes wrong',
        'The failure ladder, and the one rung that is final.',
        'Failing is not losing. In order of how much it hurts:\n\n'
        '  [warn]burned run[/]      no pay, and the residue still lands\n'
        '  [warn]severed[/]         the trace filled; deck damage and a bad '
        'night\n'
        '  [warn]alias burned[/]    the name is spent; heat and reputation '
        'both\n'
        '  [err]bounty[/]          a faction is paying for you now\n'
        '  [err]chrome damage[/]   something comes out of you in a room you '
        'did not choose\n'
        '  [err]the street[/]      somebody\'s people, or nobody\'s, and a '
        'choice: run, talk, pay, stand\n'
        '  [err]FLATLINE[/]        black ICE. This one ends the character.\n'
        '  [err]KILLED[/]          the street, after it warned you. So does '
        'this.\n\n'
        'Everything except the last two is a change of circumstances, not a '
        'game over. A runner who has been caught twice is playing a '
        'different, worse, more interesting character than the one they '
        'built.\n\n'
        '[err]Two things can kill you[/], and both tell you first. Black ICE '
        'only guards cores and vaults, it always telegraphs, and it gives you '
        'a Composure check before the end: if you are somewhere a Coffin '
        'lives, you were told. The street kills only at the top of its '
        'ladder, only people with a number on their name, and only after a '
        'night that ends with you at one Integrity and a sentence you will '
        'remember: next time they will not be asking. `help street`.\n\n'
        '[warn]The decision:[/] because failure is survivable, the correct '
        'play is often to attempt things you will probably lose. A burned run '
        'costs a night. Not trying costs the campaign.',
        see=('ice', 'heat', 'triangle', 'legacy', 'street'),
        commands=('status', 'jack out'),
        terms=('dying', 'permadeath',),
        group='city'),

    Topic(
        'appearance', 'What you look like',
        'Eight features, two numbers, and one genuine trade.',
        'Appearance is the seventh way to build a character and the only one '
        'about the meat rather than the work. It is not decoration: every '
        'feature you pick moves two numbers, and one of them cuts both ways.\n\n'
        '[accent]Memorable[/] is how easily a stranger could describe you '
        'afterwards. High memorable earns more standing per job, because work '
        'gets attributed to somebody and you are somebody worth naming. It '
        'also converts more of the evidence you leave behind into faction '
        'heat, because forensics is only half of it and the other half is a '
        'woman behind a counter telling Nightwatch exactly who came in. Low '
        'memorable is the reverse: safe, and forgettable, and forgettable '
        'people get offered forgettable work.\n\n'
        '[accent]Presence[/] is how much room you take up in a conversation. It '
        'applies out here and nowhere else, which is the right reading rather '
        'than a limit: inside a run you are an icon and not a body, and what '
        'talks in there is the shape you are wearing. Out here it improves '
        'what legwork gets you and it lowers what somebody has to think of '
        'you before they will do you a favour.\n\n'
        '[warn]Chrome puts a floor under memorable that you cannot get back '
        'under.[/] Past about twenty-five Dissonance there is no such thing '
        'as an unremarkable netrunner: whatever you have had done shows, in '
        'the way you hold still and the way you do not, and no haircut fixes '
        'it. You do not get the benefits of the hardware and the anonymity of '
        'not having it.\n\n'
        'Build, face, eyes and marks are set at creation. The other four are '
        'yours to change whenever you like, which makes changing your look '
        'the cheap half of going to ground: it will not clear a bounty, but '
        'it buys back a little of what the bounty is worth.\n\n'
        '[err]Marks are neither.[/] You do not choose those. Surviving black '
        'ICE leaves the fern pattern it makes going through a nervous system. '
        'A beating leaves a record on you as well as in their system. Past '
        'Submerged, the drift is something other people can see. They '
        'accumulate, they never come off, and they are the only part of this '
        'that is a record rather than a decision.',
        see=('chrome', 'heat', 'people', 'origins'),
        commands=('self', 'clinic'),
        covers=('appearance',),
        terms=('looks', 'disguise',),
        group='character'),

    Topic(
        'reading', 'Reading the city',
        'Ambient events, asides, and what the output is telling you.',
        'Every command that spends a shift may print one thing the city did '
        'while you were not looking. It is set apart from the news above it '
        'and it is always scenery: an ambient event cannot take your credits, '
        'damage your deck, or move a single number on your sheet. That is '
        'deliberate. The moment scenery can pay you, players stop reading it '
        'for the city and start reading it for outcomes.\n\n'
        'What it is for is tone. Most of it is somebody having a worse day '
        'than you in a way nobody will record, because that is the setting. '
        'Some of it is the same city seen by somebody who has been here too '
        'long to be shocked. And about one in six comes up for air, because a '
        'city that is unrelentingly bleak stops landing after an hour, and '
        'the joke that has something sad under it is the one that makes the '
        'next bad thing land harder.\n\n'
        '[dim]Small raised numbers in the text are asides.[/] They print '
        'under the block that raised them. They are never load-bearing: you '
        'can read every one of them or none of them and the game is the same '
        'game.{{They do occasionally nest. This is not a bug and it is not an '
        'accident either.}}\n\n'
        'The rest of the output is colour-coded by meaning rather than by '
        'severity. Trace is always the same colour everywhere trace is '
        'mentioned, which matters more than it sounds in a game whose whole '
        'tension is one rising number that you need to find at a glance in a '
        'wall of scrollback.',
        see=('triangle', 'city', 'basics', 'clock'),
        commands=('look', 'rest', 'log'),
        covers=('events', 'cyberspace',),
        terms=('footnotes', 'flavour',),
        group='city'),

    Topic(
        'networks', 'What you are breaking into',
        'Shape, size, and how one lot\'s networks differ from another\'s.',
        'Every network is generated, and every one is generated the same '
        'way: four concentric [accent]zones[/] (perimeter, interior, '
        'restricted, core), an authored [accent]shape[/] the hosts are wired '
        'into, and random fill inside that. Nothing is hand-drawn, and '
        'nothing is arbitrary either.\n\n'
        '[warn]Six shapes.[/] [accent]Layered[/] is the standard four rings. '
        'A [accent]spine[/] is one long corridor in. A [accent]ring[/] gives '
        'every zone two ways round. A [accent]hub[/] hangs each zone off one '
        'host, which is where the wardens stand. A [accent]mesh[/] is joined '
        'every way it could be. A [accent]split[/] forks the deep zones into '
        'two wings, and the job is in one of them. Which shapes a faction '
        'builds is doctrine: a gang runs a phone tree, so it is a hub; a '
        'bank is a spine; Deepwater is a mesh nobody drew. [fg]map[/] names '
        'the shape once you have seen enough of it, and topology legwork '
        'names it before you go in.\n\n'
        '[warn]Size is breadth, not depth.[/] Contracts come small, usual, '
        'large, or a [accent]sprawl[/], and the board says which. A bigger '
        'job widens the front: more ways in, more hosts that are not the '
        'job, more to carry out. It barely deepens the back, because depth '
        'is hops and hops are [trace]trace[/]. And the size itself is cover: '
        'a twenty-host network runs the clock about a fifth slower than an '
        'eight-host one, because there is more traffic to be lost in. Size '
        'pays: a sprawl is worth more than twice a standard job.\n\n'
        '[warn]Posture is the difficulty.[/] It sets how well the place is '
        'actually built: service difficulty, how much ICE there is, how '
        'often a boundary is guarded. A gang at 22 is a phone tree with '
        'delusions and a bank at 62 is a bank. The board prints it, and '
        'prints [fg]reads[/] beside it: whether their doors open for the '
        'breaker you carry, and how hard the room runs the clock while you '
        'work. Most runs are lost to the second one.\n\n'
        '[warn]And each lot builds differently.[/] Deepwater has no '
        'perimeter and you arrive already inside it. Freeport is audited in '
        'public, so you can see the whole topology from the first tick and '
        'seeing it is not walking it. Static mirror everything, so the thing '
        'you came for exists twice. Meridian always seal the objective. A '
        'Chorus construct that has woken does not go back to sleep. '
        'Nightwatch send somebody when the room turns red. The contract '
        'screen says which of these you are walking into, under '
        '[fg]their way[/].\n\n'
        '[warn]The decision:[/] posture decides whether you can open it, '
        'size decides how long you will be in there, and shape decides '
        'whether there is a second way round. Legwork buys all three before '
        'you commit, and it is cheaper than finding out.',
        see=('objectives', 'contracts', 'triangle', 'factions'),
        commands=('map', 'legwork', 'board', 'scan'),
        terms=('shape', 'sprawl', 'zones', 'topology', 'layout',
               'how big', 'signature', 'network', 'networks'),
        group='systems'),
    Topic(
        'conditions', 'Tonight, inside',
        'What the network is like tonight, which is not what it is.',
        'A network has a posture, which is how hard it is, and a shape, which '
        'is who built it. It also has a [accent]tonight[/]: a condition, '
        'drawn when you jack in, announced at the door, and shown on `status` '
        'for the rest of the run. About one run in two has one.\n\n'
        '  [fg]maintenance window[/]  countermeasures slow to wake, trace fast\n'
        '  [fg]audit in progress[/]   residue counts half again, pay is better\n'
        '  [fg]lockdown[/]            every crack harder, countermeasures wake sooner\n'
        '  [fg]another runner[/]      noise you did not make, trace a little faster\n'
        '  [fg]dead hours[/]          trace slow, countermeasures slow to wake\n'
        '  [fg]carrier storm[/]       moving costs a tick more, noise counts less\n'
        '  [fg]security exercise[/]   countermeasures wake at a whisper, residue less\n'
        '  [fg]skeleton crew[/]       every crack easier, pay is worse\n\n'
        'Every number it moves is printed at the door and on `status`, and a '
        'condition that touches a check shows up in `odds` as its own term. '
        'It is weather, not a modifier hiding in a menu: the reason the same '
        'network is a different run on a different night, and the reason '
        '`legwork` cannot tell you everything.\n\n'
        '[warn]The decision:[/] the condition is fixed the moment you jack in '
        'and does not change under you. Read it. A maintenance window rewards '
        'a fast loud run; an audit rewards a clean one; a skeleton crew '
        'rewards going deep; a storm rewards going straight there.',
        see=('triangle', 'ice', 'clock', 'checks'),
        commands=('jack in', 'status', 'odds'),
        covers=('conditions',),
        terms=('buff', 'debuff', 'mutator', 'hazard'),
        group='systems'),
    Topic(
        'clock', 'The shift clock',
        'When you do something matters as much as where.',
        'The city runs on three shifts a day and every one of them is a '
        'different city.\n\n'
        '[accent]The street and the net want opposite hours.[/] That is the '
        'whole system and it is worth holding in your head.\n\n'
        'At [accent]peak[/], the afternoon, every walkway is at capacity. '
        'That is bad for you out here: more people, and a worse chance that '
        'one of them is somebody with your name on a list. It is good for you '
        'in there, because all of those people are also generating traffic, '
        'and ten thousand legitimate sessions is the best mask money cannot '
        'buy. The trace runs slower.\n\n'
        'At [accent]night[/] the street empties and nobody is looking at you. '
        'So does the network. Your session is the only session, the trace has '
        'nothing to sort you out of, and it runs faster. Half the market is '
        'shuttered and the other half has adjusted its prices.\n\n'
        '[accent]Morning[/] is the middle of both, and it is when stock '
        'lands.\n\n'
        '[warn]The decision:[/] there is no correct shift to work, only a '
        'shift that suits the run you are about to do. Peak for a long '
        'careful job on a network you need time inside. Night for crossing a '
        'district that wants you. Morning for buying. The tension is that '
        'waiting for the right one is priced in the only currency this city '
        'actually charges in, which is time, and the contract board does not '
        'wait for you.\n\n'
        '`look` tells you what the current shift is doing, in the two places '
        'it is doing it. Inside a run, `status` shows the rate you are on: '
        'that is fixed at the moment you jacked in and does not change '
        'under you.',
        see=('city', 'triangle', 'contracts', 'heat', 'conditions'),
        commands=('look', 'rest', 'travel', 'status'),
        terms=('time of day', 'schedule',),
        group='city'),

    Topic(
        'shell', 'Ricing the shell',
        'Seven axes of terminal, earned by playing, and yours to keep.',
        'Everything else in this game costs you something. Chrome costs '
        'Dissonance, work costs heat, a face worth remembering costs '
        'anonymity. This costs nothing and takes nothing, and it is here for '
        'exactly that reason.\n\n'
        '`rice` shows seven axes: [accent]palette[/] is the colour scheme, '
        '[accent]prompt[/] is the shape of the line you type at, '
        '[accent]frame[/] is the box-drawing, [accent]bars[/] is what a meter '
        'is made of, [accent]marks[/] is bullets and ticks and crosses, and '
        '[accent]banner[/] is the wordmark on the cold start, and '
        '[accent]hud[/] is the line of readout that follows every tick '
        'you spend in a run, which you can have as a bar, as numbers, '
        'or not at all. Seventy-one pieces across the seven, most of '
        'them earned.\n\n'
        '[warn]It lives outside the save.[/] The deck\'s interface belongs to '
        'you and not to the character, so it survives a flatline. You lose '
        'everything else and the terminal you spent a week getting right is '
        'still yours when you sit down with somebody new. The city takes the '
        'runner. It does not get the shell.\n\n'
        'The unlocks are spread across very different kinds of playing on '
        'purpose: finishing contracts, finishing them without anybody ever '
        'knowing, getting somewhere with a faction, seeing the city, going '
        'too deep into the drift, meeting black ICE and being in a condition '
        'to remember it. Nobody should be able to open the whole catalogue by '
        'doing one thing forty times.\n\n'
        '[warn]The rule:[/] none of it touches a single number. A cosmetic '
        'that changed the game would be a build decision hiding in a menu, '
        'and there is one thing no prompt style is allowed to drop, which is '
        'the trace. Everything else on the prompt is one `status` away. The '
        'trace is the number that ends the character.\n\n'
        '`rice <kind> <name> --try` wears something for one screen without '
        'keeping it.',
        see=('saves', 'basics', 'death'),
        commands=('rice', 'title', 'career'),
        covers=('rice',),
        terms=('ricing', 'theme', 'colours', 'colors', 'customise', 'customize',),
        group='start'),
)

BY_KEY: dict[str, Topic] = {t.key: t for t in TOPICS}
TOPIC_KEYS: tuple[str, ...] = tuple(BY_KEY)

#: What `help` suggests to somebody who has just started.
STARTER = ('basics', 'firstrun', 'triangle', 'origins')
