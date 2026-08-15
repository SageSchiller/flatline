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


GROUPS = ('start', 'systems', 'character', 'city')

GROUP_TITLES = {
    'start': 'Starting out',
    'systems': 'How a run works',
    'character': 'What you are made of',
    'city': 'The city, and what it remembers',
}


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
        group='start'),

    Topic(
        'saves', 'Saves, and keeping one',
        'Where a character lives, and how to make sure they survive.',
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
        commands=('save', 'restore'),
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
        'loud, so it is fed by both the time you spend and the noise you make.\n\n'
        '[residue]RESIDUE[/] is evidence. It does not affect the run at all. '
        'It sits on the nodes you touched, you carry it out with you, and a '
        'shift later it becomes that faction\'s heat on your name.\n\n'
        '[warn]Here is the whole tension:[/] cleaning up residue costs ticks, '
        'and ticks feed the trace. Getting out [ul]clean[/] and getting out '
        '[ul]at all[/] pull in opposite directions, and you cannot have both '
        'unless you were fast enough earlier to afford the difference.',
        see=('alert', 'heat', 'basics'),
        commands=('status', 'scrub', 'mask', 'wipe')),
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
        commands=('odds',)),
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
        '  [ice]black[/]    lethal. The only thing that can actually kill you\n\n'
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
        commands=('probe', 'strike', 'mask', 'overload')),
    Topic(
        'alert', 'The alert level',
        'The network making up its mind about you.',
        'A network is at [ok]green[/], [warn]amber[/], [err]red[/], or '
        '[err]lockdown[/]. It only ever goes up, never down, inside a run.\n\n'
        'Each step multiplies how fast the trace advances: amber is 1.25x, red '
        'is 1.7x, lockdown is 2.4x. It rises when a node gets too noisy, when a '
        'sentry files on you, when a pretext fails, and when you do something '
        'spectacular like an overload.\n\n'
        '[warn]The decision:[/] alert is the reason a slow careful run beats a '
        'fast loud one over the length of a whole network. At red your trace '
        'is running at nearly double speed, so every tick you spend after that '
        'point costs you nearly twice what the same tick cost at green.',
        see=('triangle', 'ice'),
        commands=('status',)),
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
        commands=('board', 'take', 'observe', 'signal')),

    # -- what you are made of ---------------------------------------------
    Topic(
        'attributes', 'The five attributes',
        'What each one is for, and what being short on it feels like.',
        '[accent]Logic[/] builds exploits and breaks encryption. It drives '
        'Focus. Low Logic means services read as noise.\n\n'
        '[accent]Reflex[/] is speed. It drives Tempo, which is how many '
        'actions you get per tick. Low Reflex means everything happens to you '
        'before you happen to it.\n\n'
        '[accent]Nerve[/] holds you together under black ICE and drives '
        'Composure. Low Nerve means you fold at the moment folding is fatal.\n\n'
        '[accent]Guile[/] is pretexting and forged credentials: the whole '
        'argument that the cheapest exploit is a plausible voice. Low Guile '
        'means every door has to be broken.\n\n'
        '[accent]Grit[/] is capacity. It drives Bandwidth, which is how much '
        'chrome fits in you, and Integrity, which is how much damage you '
        'absorb.\n\n'
        '[warn]What they turn into:[/]\n'
        '  Bandwidth = 8 + Grit          chrome capacity\n'
        '  Integrity = 10 + 2x Grit      damage before the run ends\n'
        '  Focus     = 3 + Logic/2       precision actions per run\n'
        '  Tempo     = 1 + Reflex/4      actions per tick, capped at 3\n\n'
        '[warn]The decision:[/] attributes are broad and slow. They set your '
        'ceilings. Skills decide what you can do at all, so early points '
        'usually go to whichever attribute your intended skills check against.',
        see=('skills', 'chrome', 'checks'),
        commands=('char', 'boost'),
        group='character'),
    Topic(
        'skills', 'The twelve skill lines',
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
        '  [accent]Forensics[/]     managing what you leave behind.\n\n'
        '[warn]Every attribute governs at least two of them[/], three lines '
        'apiece for Logic and two for everybody else, so there is no '
        'attribute you can safely ignore and no single best one.\n\n'
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
        group='character'),
    Topic(
        'techniques', 'Techniques',
        'The twenty-four things ranks 2 and 4 unlock.',
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
        group='character'),
    Topic(
        'traits', 'Traits',
        'The axis where the pool is much bigger than the slots.',
        'Skills say what you can do. Chrome says what you are made of. '
        '[accent]Traits say what you are like.[/]\n\n'
        'You pick two at creation and earn one more every six runs, to a '
        'maximum of five, out of a pool of twenty-six. That asymmetry is the '
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
        group='character'),
    Topic(
        'chrome', 'Cyberware and Dissonance',
        'Nothing here is a pure upgrade, and the cost is permanent.',
        'Chrome costs two things. [accent]Bandwidth[/] is hard capacity: you '
        'have 8 + Grit and that is that. [accent2]Dissonance[/] is the long '
        'arc, and it never goes down on its own.\n\n'
        'Every single piece also carries a specific named drawback. A reflex '
        'governor removes the hesitation between deciding and acting by '
        'removing the hesitation, so your pretexts suffer. If a piece cannot '
        'be given an honest downside it does not exist.\n\n'
        '[accent2]Dissonance[/] is the interesting one. It makes you '
        '[ul]better in the net[/] and [ul]worse in the city[/]: better '
        'composure against black ICE, the coherence to wear icons no person '
        'could hold, and in exchange, worse prices, fewer social options, and '
        'a city that treats you as a walking incident report.\n\n'
        'Past 50 Dissonance the back of a clinic opens, and [warn]restricted '
        'chrome is sold nowhere else[/]. The best hardware in the city is '
        'available only to people who have gone too far to be sold anything '
        'else.\n\n'
        '[warn]The decision:[/] a full-chrome build is a real playstyle, not a '
        'punishment track. But taking chrome out does not lower your '
        'Dissonance, only the floor that grounding can reach. You are choosing '
        'who to be, not renting it.',
        see=('attributes', 'icons', 'money'),
        commands=('chrome', 'install', 'clinic', 'ground'),
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
        see=('programs', 'contracts'),
        commands=('deck', 'load', 'unload', 'buy', 'repair'),
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
        '[warn]The decision:[/] every slot spent on insurance is a slot not '
        'spent on capability. Armour and masks are invisible until the run '
        'they save, and a build that never carries them wins more often and '
        'loses harder.',
        see=('deck', 'triangle'),
        commands=('load', 'deck', 'market'),
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
        group='character'),

    # -- the city ---------------------------------------------------------
    Topic(
        'city', 'The city and time',
        'Everything costs shifts, and the board does not wait.',
        'Time moves in [accent]shifts[/], three to a day. Travelling costs '
        'one, legwork costs one, resting costs as many as you spend, and '
        'establishing a new identity costs two.\n\n'
        'Nine districts, and [accent]travel only goes to a neighbour[/], so '
        'somewhere on the far side of the city costs two or three shifts to '
        'reach and the contract expiring is counting all of them. [fg]map[/] '
        'draws the whole shape, marks where you are, and says how many shifts '
        'each district is from here. Anything that sends you somewhere hands '
        'you the walk as a line you can type.\n\n'
        'While shifts pass: contracts expire, heat decays, market stock '
        'rotates, faction posture drifts back toward baseline, and '
        '[warn]other runners take work off the board[/].\n\n'
        'That last one matters more than it sounds. Sitting still is not a '
        'free way to let heat cool. It is a way to let somebody else make the '
        'city more expensive, because when a rival succeeds against a faction, '
        'that faction hardens for you too.\n\n'
        '[warn]The decision:[/] doing nothing is a real strategy with a real '
        'price, and knowing when to pay it is most of the city layer.',
        see=('heat', 'rivals', 'contracts', 'reading', 'clock'),
        commands=('travel', 'map', 'rest', 'board'),
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
        '[warn]The decision:[/] legwork is what turns your loadout from a '
        'guess into a choice. A run you did no legwork for is a run you packed '
        'for blind.',
        see=('city', 'deck', 'objectives'),
        commands=('board', 'take', 'legwork'),
        group='city'),
    Topic(
        'heat', 'Heat, aliases, and bounties',
        'What the residue turns into, and what to do about it.',
        'A shift after a run, the residue you left becomes [heat]heat[/] on '
        'the faction you ran. Heat is attention, not hatred: a faction can '
        'like you and still be looking for whoever did that thing last week.\n\n'
        'Heat decays slowly. Corps forget faster than gangs.\n\n'
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
        see=('triangle', 'factions', 'death'),
        commands=('alias', 'burn', 'rep', 'rest'),
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
        group='city'),
    Topic(
        'rivals', 'The other runners',
        'Seven named people who are also working.',
        'Rivals take contracts off the board while you deliberate, and when '
        'they succeed the target hardens for everybody. Over twenty shifts you '
        'learn that Vesper takes the corporate work and Hound takes anything '
        'violent, and you start reading the board with that in mind.\n\n'
        '[accent]Disposition[/] is how one feels about you. It falls when you '
        'take work they wanted and rises when you keep them alive.\n\n'
        'Three things you can do with them:\n'
        '  [fg]hire[/]    one runs alongside you. What they are worth is '
        'entirely their style.\n'
        '  [fg]ask[/]     a favour, priced in disposition rather than credits.\n'
        '  [fg]betray[/]  sell a name to somebody who wants it.\n\n'
        '[warn]The way up is escort work.[/] Nobody starts liking you enough '
        'for a favour, and disposition only falls on its own. An escort '
        'contract, run so that they come out alive, is worth more standing '
        'than anything else in the game.\n\n'
        '[err]Betrayal is permanent.[/] The person usually does not survive '
        'being found, every other runner in the city thinks less of you, and '
        'none of it can be undone.\n\n'
        '[warn]The decision:[/] disposition is a resource you spend and can '
        'only earn back slowly. Selling somebody is the largest single payday '
        'available to you and it closes the whole social layer behind it.',
        see=('objectives', 'city'),
        commands=('who', 'hire', 'ask', 'betray'),
        group='city'),
    Topic(
        'people', 'The people in this city',
        'Who to find, how to find them, and why they are worth it.',
        'The city has people in it who are not competing with you. '
        '[fg]look[/] is how you find them: who you run into depends on where '
        'you are, what you can get into there, and in some cases on what you '
        'have already done.\n\n'
        'They are not shops with faces on. Every one of them wants something, '
        'and it is not always your money. Some of them are trying to help '
        'you, some are lying about who they work for, one is a vending '
        'machine with opinions about a war in 2041, and one of them is dying '
        'and has decided not to ask you about it.\n\n'
        '[fg]talk[/] gets you a line. [fg]ask <name> <topic>[/] gets you what '
        'they think about something specific, and some of those answers open '
        'things.\n\n'
        '[warn]The decision:[/] talking costs you nothing and no shift, so '
        'the only reason not to is that you do not know they are there. Walk '
        'into districts you have no job in.',
        see=('threads', 'rivals', 'city'),
        commands=('look', 'talk', 'ask', 'who is'),
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
        group='city'),
    Topic(
        'money', 'Credits and what things cost',
        'The economy, and what a run is actually worth.',
        'A contract pays between about 1,200 and 6,000 credits depending on '
        'the target\'s posture and what the patron thinks of you.\n\n'
        'On top of that you keep what you carried out, sold through the '
        'patron. [warn]What it clears depends on your standing with them[/]: a '
        'stranger gets under half of nominal, somebody trusted gets close to '
        'three quarters. Reputation is worth money, directly.\n\n'
        'For scale: a good professional program is about one and a half '
        'contracts. A piece of restricted chrome or a top deck component is '
        'four or five. A new identity is under one.\n\n'
        '[warn]The decision:[/] stripping a network bare pays roughly twice '
        'what doing only the job pays. It also means touching every node, '
        'which is trace, noise, and residue you did not have to spend. That '
        'temptation is the game asking you a question every single run.',
        see=('triangle', 'contracts', 'deck'),
        commands=('market', 'buy', 'sell', 'debt'),
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
        '  [err]FLATLINE[/]        black ICE. This one ends the character.\n\n'
        'Everything except the last is a change of circumstances, not a game '
        'over. A runner who has been caught twice is playing a different, '
        'worse, more interesting character than the one they built.\n\n'
        '[err]Only black ICE can kill you[/], it only guards cores and vaults, '
        'it always telegraphs, and it gives you a Composure check before the '
        'end. If you are somewhere a Coffin lives, you were told.\n\n'
        '[warn]The decision:[/] because failure is survivable, the correct '
        'play is often to attempt things you will probably lose. A burned run '
        'costs a night. Not trying costs the campaign.',
        see=('ice', 'heat', 'triangle'),
        commands=('status', 'jack out'),
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
        group='city'),

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
        see=('city', 'triangle', 'contracts', 'heat'),
        commands=('look', 'rest', 'travel', 'status'),
        group='city'),

    Topic(
        'shell', 'Ricing the shell',
        'Six axes of terminal, earned by playing, and yours to keep.',
        'Everything else in this game costs you something. Chrome costs '
        'Dissonance, work costs heat, a face worth remembering costs '
        'anonymity. This costs nothing and takes nothing, and it is here for '
        'exactly that reason.\n\n'
        '`rice` shows six axes: [accent]palette[/] is the colour scheme, '
        '[accent]prompt[/] is the shape of the line you type at, '
        '[accent]frame[/] is the box-drawing, [accent]bars[/] is what a meter '
        'is made of, [accent]marks[/] is bullets and ticks and crosses, and '
        '[accent]banner[/] is the wordmark on the cold start. Sixty-seven '
        'pieces across the six, most of them earned.\n\n'
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
        group='start'),
)

BY_KEY: dict[str, Topic] = {t.key: t for t in TOPICS}
TOPIC_KEYS: tuple[str, ...] = tuple(BY_KEY)

#: What `help` suggests to somebody who has just started.
STARTER = ('basics', 'firstrun', 'triangle', 'origins')
