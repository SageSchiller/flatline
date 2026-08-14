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
        see=('triangle', 'firstrun', 'checks'),
        commands=('board', 'take', 'jack in'),
        group='start'),
    Topic(
        'firstrun', 'Your first run, step by step',
        'The exact sequence, with the reasons.',
        '[accent]In the city:[/]\n'
        '  [fg]board[/]              see what work is on offer\n'
        '  [fg]board c001[/]         read one properly before taking it\n'
        '  [fg]take c001[/]          accept it\n'
        '  [fg]deck[/]               check what you are carrying\n'
        '  [fg]travel <district>[/]  if the job is not where you are\n'
        '  [fg]jack in[/]            go\n\n'
        '[accent]Inside:[/]\n'
        '  [fg]scan[/]               see what this node connects to\n'
        '  [fg]probe <host>[/]       see what a host runs, and what guards it\n'
        '  [fg]odds crack <host> <service>[/]   the maths, before you commit\n'
        '  [fg]crack <host> <service>[/]        break it open\n'
        '  [fg]connect <host>[/]     move there\n'
        '  [fg]status[/]             where the trace is\n'
        '  [fg]pull[/]               take what you came for\n'
        '  [fg]jack out[/]           leave\n\n'
        'Repeat the middle four until you are standing on the objective. '
        '[dim]`status` tells you which node that is.[/]\n\n'
        '[warn]The mistake everybody makes first:[/] staying too long. Every '
        'command costs time, time advances the trace, and there is no prize '
        'for the last asset you grabbed if the trace lands on you carrying it.',
        see=('triangle', 'checks', 'objectives'),
        commands=('scan', 'probe', 'odds', 'crack', 'connect', 'jack out'),
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
        'skills', 'The eight skill lines',
        'What each buys, and why ranks 2 and 4 are the ones that matter.',
        '  [accent]Intrusion[/]     breaking services. The bread and butter.\n'
        '  [accent]Cryptography[/]  encrypted stores and key material.\n'
        '  [accent]Subterfuge[/]    talking your way in instead.\n'
        '  [accent]Hardware[/]      deck tuning, overclocking, hotswaps.\n'
        '  [accent]Stealth[/]       making everything you do quieter.\n'
        '  [accent]Warfare[/]       killing countermeasures instead of '
        'avoiding them.\n'
        '  [accent]Forensics[/]     managing what you leave behind.\n'
        '  [accent]Daemonology[/]   automation that acts without you.\n\n'
        '[warn]Ranks 2 and 4 of every line unlock a technique[/], which is a '
        'new verb in the shell or a new option on an existing one. Ranks 1, 3 '
        'and 5 are numeric fill. That is the whole shape of progression here: '
        'you are buying [ul]new things to type[/], not bigger numbers.\n\n'
        'Costs rise steeply: 2, 4, 7, 11, 16 experience. Rank 5 in one line '
        'costs as much as rank 2 in six lines.\n\n'
        '[warn]The decision:[/] breadth gets you more verbs, depth gets you '
        'better odds on the ones you have. Two techniques at rank 2 in '
        'different lines will change how a run plays more than one rank 4.',
        see=('attributes', 'techniques', 'checks'),
        commands=('skills', 'train', 'techniques'),
        group='character'),
    Topic(
        'techniques', 'Techniques',
        'The sixteen things ranks 2 and 4 unlock.',
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
        see=('chrome',),
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
        'bailout` copies a working one into your library.[/]',
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
        'While shifts pass: contracts expire, heat decays, market stock '
        'rotates, faction posture drifts back toward baseline, and '
        '[warn]other runners take work off the board[/].\n\n'
        'That last one matters more than it sounds. Sitting still is not a '
        'free way to let heat cool. It is a way to let somebody else make the '
        'city more expensive, because when a rival succeeds against a faction, '
        'that faction hardens for you too.\n\n'
        '[warn]The decision:[/] doing nothing is a real strategy with a real '
        'price, and knowing when to pay it is most of the city layer.',
        see=('heat', 'rivals', 'contracts'),
        commands=('travel', 'rest', 'board'),
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
)

BY_KEY: dict[str, Topic] = {t.key: t for t in TOPICS}
TOPIC_KEYS: tuple[str, ...] = tuple(BY_KEY)

#: What `help` suggests to somebody who has just started.
STARTER = ('basics', 'firstrun', 'triangle')
