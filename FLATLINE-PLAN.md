---
tags:
  - flatline
  - project-plan
  - game
created: 2026-08-12
updated: 2026-08-13
---

# flatline: Build Plan and Progress Log

> Resumable build plan for **flatline**, a text-based cyberpunk intrusion game. **Read this file first** when picking the project back up. Every locked decision and every completed step is recorded here so work can pause and resume without re-deriving context.

> [!tip] Picking this back up: START HERE
> **State as of 2026-08-13.** **Phases 0 through 5 are done and D17's finish line is passed.** `python3 validate.py` is clean with zero warnings, `python3 test.py` is green at **5832 checks**, and `./build.sh` produces a `dist/flatline.pyz` that runs standalone with nothing installed. About 24,300 lines.
>
> The whole loop closes. Create a character six ways, spend an attribute and experience budget, read a board that other runners are competing with you for, take a contract, travel, do legwork, hire somebody to come in with you, jack in, break into a procedurally generated network, do the job, get out. The residue you left becomes faction heat a shift later, sustained heat becomes a standing bounty, and a bounty makes that faction's districts genuinely dangerous to walk into.
>
> **What is not done:** nothing structural. Every system the plan set out to build is built, and the catalogue has had one breadth pass (12 skills with 24 techniques, 26 traits, 34 chrome, 46 programs, 28 ICE, 8 icons, 7 rivals, 18 NPCs, 18 story threads, 10 origins, 9 districts, 12 factions, 23 manual topics). More districts and origins are the obvious next content, but **the right way to choose is to play it and notice what is missing**, which nobody has done yet. Treat any further content added without play as a guess.
>
> **What this is.** A netrunner sim you play by typing at a fake terminal. Two layers: a persistent city that keeps score, and procedurally generated corporate networks you break into one contract at a time. The character system is classless and deep enough that two players at the same credit total play nothing alike.
>
> **The tone is grim.** Not cynical-cool: grim. The city does not care whether you live, the clinics are the best and worst thing in it, every piece of chrome costs you something you do not get back, and the only true death in the game is telegraphed and then absolute. Everything ships in that register or it does not ship.
>
> **This is a netrunning game, not a combat game.** There are no guns and no street fights. The whole of the conflict layer is program against countermeasure, inside the net, through a deck. "Warfare" is the skill of attacking ICE constructs; it never leaves cyberspace.
>
> **The one-sentence pitch.** Every action you take in a network is loud, and the city remembers.
>
> **This is a terminal application written in Python, stdlib only.** No dependencies, no install, no network access at runtime. `python3 -m flatline` from the source tree, or a single `flatline.pyz` from `./build.sh`.
>
> **This is a wholly separate project from hone and from Waypoint.** Different folder, different app, no shared code and no shared content. Where this document cites either, it is citing prior art the way it would cite any other project that already solved a problem. See D15.
>
> **After any change, run both:** `python3 validate.py` and `python3 test.py`.

---

## Running it

```bash
cd "$HOME/projects/flatline"
python3 -m flatline              # play
python3 -m flatline --seed 8829  # play a specific world
python3 -m flatline --theme ansi # inherit the terminal's own colours
python3 validate.py              # content graph checks
python3 test.py                  # behaviour checks
./build.sh                       # dist/flatline.pyz
```

---

## The pitch, at length

You are a netrunner in a city that does not care whether you live. You take contracts from fixers, break into corporate networks, take what you were paid to take, and get out before the trace lands. That is the loop.

What makes it a game rather than a fantasy is that **every one of those verbs is a cost**. Scanning a subnet is loud. Cracking a service is louder. Wiping the logs that prove you were there takes time, and time is the one thing the trace is also spending. The interesting decisions are not "which exploit do I have" but "do I spend forty seconds covering this, knowing the trace advances while I do, or do I leave it and let Arasaka's forensics team put my signature in a file with my name forming at the top of it."

And that file persists. **The city is the scoreboard.** Burn a corp and their next network is harder, because you taught them what you can do. Take a gang contract against a fixer who liked you and the contract board changes shape. Run under the same alias too long and heat accumulates until the alias is worthless and you have to burn it, losing every relationship you built under it.

The character system exists to make that loop personal. There are no classes. There is a build: attributes, skills you invest in, chrome you install at a real cost to your stability, a deck you assemble out of components with genuine tradeoffs, and a program loadout constrained by memory you never have enough of. A social-engineering build with almost no breaker programs and a cracked-open Guile score plays a different game from an overclocked smash-and-grab build that beats the trace by being faster than it. Both are viable. Neither is the intended one.

---

## Locked decisions

Numbered so later text can cite them. A decision here is settled; changing one means editing this section and saying why in the session log.

### D1: Python 3.11+, standard library only

No dependencies, ever. `zipapp` ships with Python, so `./build.sh` produces a single file a stranger can run with `python3 flatline.pyz` and nothing installed. This constraint has a design consequence worth naming: no `rich`, no `textual`, no `numpy`. The rendering layer is written here, and it is small because D2 keeps it small.

### D2: The shell is the entire interface

No panes, no menus, no cursor addressing, no alternate screen. The game is a REPL: it prints, you type, it prints. Everything the player needs is either in the scrollback or one command away.

Three reasons this is the right call and not just the cheap one:

1. **It is the fiction.** A netrunner at a terminal is the genre image. A menu of numbered options is not.
2. **It makes the game testable.** A session is a list of input strings and a list of output strings. `test.py` can play entire runs and assert on what came back, which is not remotely true of a curses app.
3. **It makes the game deep cheaply.** Adding a verb costs one function. Adding a pane costs layout, overflow, resize, and focus.

`readline` from the stdlib supplies history, emacs-style line editing, and tab completion for free where it exists, and the game degrades to plain `input()` where it does not.

### D3: Determinism is a hard invariant

Nothing calls `random` directly and nothing reads the clock. All randomness flows through a seeded `rng.Rng` threaded from the session; all time is game time, advanced explicitly in shifts.

This is the single most important engineering decision in the project. A simulation this stateful is only debuggable if `--seed 8829` reproduces a world exactly, and only testable if a run can be replayed. It also gives the player something real: worlds have seeds, seeds can be shared, and a build can be proved against a fixed world rather than argued about.

**Corollary:** save files record the seed and the full RNG stream position. Loading a save and continuing produces the same world as never having quit.

### D4: Two layers, one save, one character

The city persists. Runs are ephemeral. The character carries across both and is the only thing that matters long-term. A run that goes badly does not end the game; it changes the city (D6).

### D5: Noise, trace, and residue are three different quantities and are never conflated

This is the core mechanical idea and everything else hangs off it.

| Quantity | Scope | Timescale | What it does |
|---|---|---|---|
| **Noise** | One node | Immediate, decays | Local suspicion. High noise wakes the ICE on this node and can trigger an alert escalation. |
| **Trace** | The whole run | Monotonic, never decays | The clock. When it fills, the run is compromised: connection severed at best, black ICE at worst. |
| **Residue** | Persists after the run | Permanent until cleaned | Evidence. Converts into faction heat, bounty, and future network hardening **after** you have already jacked out and think you got away with it. |

The tension the whole game is built on: **reducing residue costs time, and time feeds trace.** Getting out clean and getting out at all pull in opposite directions.

### D6: Failure is a state change, not a game over

Getting traced is a bad outcome, not a terminal one. The consequence ladder, in order of severity:

1. **Burned run.** Objective failed, no pay, residue high.
2. **Connection severed.** Above, plus deck damage and a cooldown before you can run again.
3. **Alias burned.** Heat on the identity exceeds tolerance; the alias is now a liability. Reputation earned under it is lost.
4. **Bounty.** A faction actively hunts you. Districts they control become dangerous to enter.
5. **Chrome damage.** Cyberware degrades or is destroyed. Expensive, and it changes your build mid-game.
6. **Flatline.** Actual death. Only reachable through black ICE, only when you failed a Nerve check you were warned about, and it ends that character.

Flatline is rare and always telegraphed. The game's name is a promise about stakes, not a promise about frequency.

### D7: State lives in the XDG data directory, as versioned JSON

`$XDG_DATA_HOME/flatline/` or `~/.local/share/flatline/`. One save per character, plus a `meta.json` for cross-character unlocks and records. Every save carries `schema` and the loader runs forward migrations, because a game this stateful will change shape and losing a character to a refactor is unacceptable.

### D8: Content is Python data modules, not JSON

Programs, cyberware, ICE, districts, factions, and name tables all live in `flatline/content/*.py` as plain dicts and tuples.

Python rather than JSON because content wants comments explaining why a number is what it is, wants to compute derived values rather than duplicating them, and wants to be importable by `validate.py` without a parse step. The cost is that content is code and can break the build; `validate.py` exists to catch exactly that.

### D9: Commands are registered objects, and one table feeds everything

A command carries its name, aliases, the contexts it is legal in, its argument spec, and its help text. The dispatcher, the `help` command, tab completion, and `validate.py` all read that one table. A command with no help text is a validation error, not a TODO.

### D10: The build is classless; origins are fiction and a starting kit, never a cap

You pick an origin at creation. It sets your backstory, your starting attributes' shape, your opening gear, your initial faction standing, and a single passive that stays with you. It never locks a skill tree or caps a stat. A corporate-defector origin can end up a street-level social engineer; it will just have taken longer to get there than the fixer's-runner origin would have.

### D11: Every piece of chrome has a real downside

Cyberware costs **Bandwidth** (a hard capacity budget) and accrues **Dissonance** (a soft, permanent drift). Beyond that, each individual piece carries a specific, named drawback. A reflex co-processor that grants an extra action per tick also raises your thermal signature, which is a trace multiplier. Nothing is a pure upgrade. If a piece of chrome cannot be given an honest drawback, it does not ship.

**Dissonance** is the long arc: the more of you is chrome, the better you are in the net and the worse you are in the city. High Dissonance grants real net-side bonuses and real city-side penalties (worse prices, fewer social options, fixers who stop returning calls). It is a playstyle axis, not a punishment track. A full-chrome build is legitimate and plays like a different game.

### D12: Memory is the real constraint on playstyle

Programs occupy deck memory. You will never have enough. What you choose to carry into a specific run, knowing what you learned during legwork, is the most frequent interesting decision in the game and it happens before the run starts.

### D13: Aliases are the container for heat

You run under an alias, not under your name. Heat accrues to the alias. Reputation also accrues to the alias. Burning an alias dumps the heat and the reputation together, which is what makes the decision hard, and it costs money and a shift of downtime to establish a new one.

### D14: No hidden dice

Any check the game makes, the player can inspect. `odds <action>` shows the actual computation: base, attribute contribution, skill contribution, gear modifiers, situational modifiers, and the resulting number. Post-roll, a failed check says which term sank it.

Deep systems are only fun when they are legible. Hiding the math does not create mystery, it creates the suspicion that the math is not there.

### D15: Separate from hone and Waypoint

No shared code, no shared content, no imports across projects. Prior art may be cited; nothing is copied wholesale except where this document says so explicitly (the palette, see D16).

### D16: The capability ladder, and the ASCII rung

The game must be fully playable at 80 columns, ASCII only, sixteen colours, and also look good at 120 columns with truecolour and Unicode. Colour is requested by semantic role (`accent`, `warn`, `err`), never by name, so `--theme ansi` maps everything onto the terminal's own palette.

The default palette is lifted from the author's own `~/.config/doom/themes/doom-cyberpunk-neon-theme.el`, including its sixteen-colour fallbacks, so the game matches ghostty, tmux, fish, Doom, and neovim rather than visiting them. This is the one deliberate borrow from hone's approach, and it is a borrow of technique and of the author's own theme file, not of code.

### D18: Your icon is the fourth build axis

You render as *something* in the net, and what you choose is a real mechanical
decision: how loud you are, how ICE classifies you, whether anything in there
will talk to you at all.

It is deliberately the **cheapest axis to change**. Skills cost experience,
chrome costs Dissonance you never get back, the deck costs a trip to a market;
an icon is a file. Carry several and wear the right one for the job. That makes
icons the tactical layer of character building, sitting under the three
permanent ones.

**Coherence** is the constraint that ties it back to D11. An icon far from a
human shape is hard to hold together, and holding one costs you unless your
Dissonance has already done the work. That is the payoff arc for a chromed
build: the same drift that makes you worse in the city makes you better at
being something other than a person in here. A Process icon, which renders you
as a scheduled maintenance job, needs 50 Dissonance and cannot speak to
anything at all.

### D19: Cyberspace is a place, and every faction's looks different

The single most important thing stopping a run reading like a port scan is that
a Kagawa fileserver and a Carrion fileserver do not look remotely alike from
the inside. Kagawa render agricultural terraces of pale green process light.
Carrion render a slaughterhouse corridor at a framerate chosen to make you
sick. Freeport render the actual docks, to scale, with a public log running
down the sky where anybody can read what you just did.

This is pure flavour with no mechanical weight, which is exactly why it lives in
its own file (`content/cyberspace.py`) and can be rewritten wholesale without
touching a rule. Three composable layers: the faction **signature** printed on
connection, the **node** description, and the **descent** text printed when you
cross a zone boundary inward. Plus **trace pressure**: one line, at a threshold
only, making the clock physical.

### D20: The city moves without you, and losing is a story

Two halves of the same decision, and the thing that turns a contract board into
a world.

**Rivals act on the shift tick.** Seven named runners take work off the board
while you deliberate, succeed or fail offscreen, and their successes raise the
target's posture. Sitting on your hands for ten shifts is therefore not a free
way to let heat decay: it is a way to let Vesper Okonkwo make Kagawa more
expensive. Their turn resolves immediately rather than being simulated, because
what matters to the player is not *how* she got in, it is that Kagawa is harder
now and she is owed a favour.

Three guards keep it pressure rather than denial: at most one job leaves the
board per shift, nobody ever touches the contract the player has accepted, and
rivals stop when the board is down to three postings.

**The failure ladder is a ladder, not a cliff.** Sustained heat becomes a
standing bounty; a bounty makes that faction's districts genuinely dangerous to
walk into; walking in anyway can get you picked up, and being picked up costs
you one specific thing: credits, a beating, a damaged deck component, a piece
of chrome taken out of you in a room you did not choose, or the name itself.

None of those is a game over, and that is the whole point. A player who has
been caught twice is playing a different, worse, more interesting character than
the one they built. The only thing that ends a character is black ICE, where
they can see it coming.

### D21: Relationships are a resource, and spending one is permanent

Rivals stopped being scenery in Phase 4 and became a system in Phase 5. Three
verbs, and the shape of all three is the same: you are spending something that
does not grow back on its own.

**`hire`** puts one of them in the network beside you. What they are worth is
entirely their style: a chromed runner steps into strikes aimed at you, a quiet
one keeps the room quiet, a loud one adds their skill to everything you break,
a careful one calls out traps before you step on them. They take a fee up front
and a quarter of the haul, and they can die in there, and if they do the whole
street knows whose job it was.

**`ask`** calls in a favour: intel, money, a program off their deck, or somebody
to say you were elsewhere. Favours are priced in disposition rather than
credits, and asking spends it. That makes the social layer genuinely finite,
which is the only thing that stops it becoming a second wallet.

**`betray`** sells a name to a faction that wants it. It is the most lucrative
single action in the game and the most expensive: the person you sold usually
does not survive being found, every other runner in the city thinks less of you
permanently, and none of it can be undone. It has its own verb rather than
being a mode of `sell` because selling a program and selling a person are not
the same act and should not read as one.

**The loop closes through `escort`.** Nobody starts liking you enough for a
favour. The way up is to take an escort contract and keep somebody alive
through it, which is worth more disposition than anything else in the game. So
the objective that seemed like the odd one out turns out to be the engine: it
is where relationships are made, and relationships are what make hiring cheap
and favours possible.

### D22: Scripts check before they act

A script that only replays a recorded sequence is a macro, and a macro is not
what a netrunner writes. What they write is something that checks before it
acts and gets out when the numbers turn. So scripts have conditions.

Four statement forms and nothing else:

```
scan                          a plain command
if trace > 40: mask           runs only when the condition holds
stop if alert >= red          abandons the rest of the script
repeat 3: crack gw01 shell    bounded, one to ten
```

A daemon can be handed a script as its behaviour policy (`daemon script
<name>`): it re-reads it every tick and the first passing condition names its
task. It only ever gets its own three tasks, never the player's verb set,
because an autonomous process that could type `jack out` would be puppeting the
player rather than helping them.

Conditions read live run state by name: `trace`, `noise`, `focus`,
`integrity`, `tick`, `haul`, `residue`, `tier` as numbers; `ice`, `locked`,
`open`, `data`, `mapped`, `ally`, `escort` as yes-or-no; and `alert`, which
compares by rank rather than alphabetically.

**There are no variables, no arithmetic, and no user-defined anything, and
that ceiling is the point.** A real expression grammar would be a second game
sitting beside the first one. The interesting decision is *which checks are
worth writing*, not how cleverly you can write them.

Two supporting rules. A skipped step says it was skipped, because a script
that silently does nothing is indistinguishable from one that is broken. And
scripts are saved with the character, because a script library is a build
investment in exactly the way a program library is.

### D23: The drift is an arc, with doors on both sides

D11 made Dissonance a permanent one-way cost with net-side payoffs. What it
never had was anything *written* for it, and a number that only shows up in a
price multiplier is a spreadsheet entry rather than an arc.

**Passages** fire once, when you cross a band, and they are the emotional
payload: the half-second where you have to decide which of two rooms you are
in, the beat of lag somebody else politely adjusts around, the point at which
the meat world becomes the thing on the far side of a window.

**Doors open as well as closing.** The single most important rule here is that
**restricted chrome is sold nowhere else**: tier-3 implants never appear on an
open shelf, only in the back of a clinic, and the back only opens to somebody
already past 50. So the best hardware in the city is available exclusively to
people who have stopped being customers and started being colleagues, which is
the payoff the whole axis was missing. Legwork moves the same way: `resonance`
opens at 50 because you are closer to the network than to people now, and
`employee` closes at 75 because a pretext needs a voice that does not lag.

**Grounding** is the valve, and it is deliberately bad value: expensive, slow,
partial, and it hurts. It exists so the arc is a decision rather than a
ratchet. It cannot take you below what your installed chrome accounts for,
which keeps D11 honest: you can walk back what the work did to you, never the
hardware while it is still in you. Taking chrome out still does not lower the
number, it only lowers the floor.

### D24: A passive with no mechanical half is a lie

Every origin's headline ability must carry either an `effects` dict or a
`rider` the engine implements, and `validate.py` fails the build otherwise.

This exists because an audit found several that did not. The Gutter runner's
Salvager passive had promised "deck components cost 30% less to repair" since
the first day and there was no repair command at all. The Chromed origin's
"one additional action in the first tick" was a sentence. The protege's "10%
higher" was a sentence. They read convincingly, they shipped, and they did
nothing, which is the most expensive kind of content because it costs the
player's trust rather than their credits.

The rule generalises past origins and is already applied to chrome (D11) and
icons (D18): if the drawback or the benefit cannot be stated in numbers or in
a named rider, it does not ship.

### D25: Debt is a clock that is not the trace

Two origins ship owing somebody money, and one of them had said "it is
compounding" in its complication text since the beginning while compounding
nothing.

Debt grows every shift, and after a grace period the lender starts collecting
in person. If the account is empty they take it out of the room instead,
routed through the same D6 fallout ladder as everything else. What it buys is
a second kind of pressure: heat decays if you wait, so waiting is a strategy,
and a debt makes waiting expensive in a way nothing else did.

**It has to be survivable**, and `validate.py` asserts the invariant directly:
a collection must remove more than the interest accrued between collections.
Otherwise the debt is unpayable and the character is dead, and D6 says nothing
but black ICE ends a character. It is a spiral you get dragged down, never one
you fall out of the bottom of.

### D26: A herder does not fight

The seventh ICE behaviour, and the only one that does no damage at all. A
herder closes routes: it cuts the way you came, one edge at a time, and leaves
exactly one door open.

The question it asks is different from every other construct's. A hunter asks
whether you can afford to fight, a warden asks what your answer to a locked
door is, and a herder asks **whether the thing it is steering you toward is
worse than the trace you would spend refusing**. That is why it must never
deal damage: the moment it can hurt you it becomes a hunter with extra steps,
and `validate.py` enforces the zero.

**Every cut is checked before it is made.** A herder that can orphan the
objective, or cut you off from the way out, is not a difficulty spike: it is an
unwinnable run generated in the middle of a winnable one, which is the single
thing network generation is not allowed to do. So `_cut_route` tries candidates,
tests connectivity from the player's position to both the entry and the job,
and rolls back anything that fails. If nothing is safe to close, the construct
simply has nothing to do that tick. `test.py` proves it over sixty networks and
roughly two thousand cuts.

### D27: Help explains systems, not just verbs

`help <command>` told you what a verb did and never told you what Nerve was
for. That is most of the game, and none of it was written anywhere a player
could reach.

The manual is twenty-one topics under four headings, written to one rule:
**every topic ends with a decision**. A reference entry that explains a number
without saying what to do differently is a glossary, and a glossary is not
help. `validate.py` warns on any topic that only describes.

**The tutorial watches rather than leads.** Fourteen steps, each an instruction
plus a condition checked after every command, so the player is always doing the
thing they were just told about and never reading ahead. Nothing is forced.
Conditions must be total, and `validate.py` calls every one against an empty
session to prove they cope with nothing existing yet: a tutorial is optional
and a bug in one is never worth a traceback in the middle of somebody's run.

### D28: Traits, and a pool bigger than the slots

Skills say what you can do, chrome says what you are made of, and traits say
what you are **like**. Twenty-six of them, two picked at creation, one more
every six runs, five maximum.

**The asymmetry is the whole design.** Any axis where you can eventually have
everything converges: given enough runs, two characters become the same
character. Traits cannot be completed, so they cannot converge, and the
question stops being "what is optimal" and becomes "what is this person".

They follow the D11 rule and the D24 rule together: every one has an honest
mechanical drawback, and every rider is implemented rather than described.
Some refuse to sit together, and `validate.py` checks the exclusions are
mutual.

### D29: Every attribute governs at least two skills

Logic governed five of the original eight lines and Grit governed none. That
made Logic mandatory, Grit a dump stat that only bought derived numbers, and
every character's opening attribute spread the same shape.

Twelve lines now, three apiece for Logic and two for everybody else, and
`validate.py` enforces the spread. **A customisation system whose optimal
opening is identical for everybody is not one**, and that is worth a build
check rather than good intentions.

### D30: A cast written for range, not for genre

Rivals are other runners and are defined by competing with you. Everybody else
is in `content/npcs.py`, and its whole job is **range**: a city populated
entirely by laconic mercenaries in long coats is a city with one joke in it.

So the cast spans a councillor nine years into the same drainage objection, a
vending machine with a name and an offering of coins, a doctor who is buying
rather than selling, a child who knows every cable run in the Ninth Ward, and
somebody dying who has decided not to ask you about it. Tone is a declared
field and `validate.py` asserts no single register is more than 40% of the
cast, because a spread that is hoped for is a spread that drifts.

**Every one of them wants something, and it is not always your money.** A
character who exists to sell you a thing is a shop with a face on it.

### D31: Threads, not quest chains

A thread is a set of **scenes**, each with its own condition, and a scene
happens the moment its condition holds however that happened. There is no
sequence and no gating on the previous step.

Three consequences, and all three are the point:

**More than one way in.** A stage takes `any_of` as well as `requires`, so a
second door is a property of the data rather than the same scene written
twice. Deepwater can be reached through the Archivist, through Remnant,
through running one of their networks, or through asking Mara the wrong
question.

**They cross for free.** The entire state is one set of strings, so a thread
does not need to know another exists in order to read a flag it happened to
set. Vance's thread never mentions Lark's, and taking Vance's offer closes a
door in Lark's anyway. `validate.py` checks crossings are mutual and warns when
a thread claims one it does not actually share, which caught seven claims that
were decoration rather than design.

**Nothing is ordered**, so the fourth scene can arrive before the second if the
world got there first. That is why every stage is written as a scene rather
than as a step: the prose has to survive arriving in any order.

### D32: One thing per origin that nobody else can do

An origin used to be an attribute shape, some gear, and a passive. Two
characters who spent forty shifts diverging still ended up able to do all the
same things, because everything an origin gave was a modifier.

Every origin now has a **signature ability**: one verb, once per run, owned by
exactly one background. It cannot be trained, bought, or shared, because the
only way to have it is to have been that person.

The Legally Dead can set the trace to zero, because there is no record to
attach it to. The Burnout can retry the check they just failed at full skill,
because they have seen it before. The Chromed can stop using the interface for
three ticks and move through the network as though it were a room. The
Indentured can requisition a program they do not own against a buyout they have
not finished paying.

`validate.py` enforces that every origin has one, that each is owned by exactly
one origin, and that each names a real command. **The refusal names who can**,
which is deliberate: being told "that is not something you can do, Legally dead
can" teaches you what the other nine backgrounds are for.


### D33: Appearance is a trade, not a portrait

The seventh customisation axis and the first one about the meat rather than
the work. 102 features across eight slots, and every one of them moves two
numbers, because a feature that moves nothing is a costume item in a game that
promised every choice weighs something. `validate.py` rejects those.

**Memorable is deliberately two-sided and that is the whole system.** It earns
more standing per job, because work gets attributed to somebody and you are
somebody worth naming. It also converts more residue into faction heat,
because forensics is only half of it and the other half is a woman behind a
counter describing you to Nightwatch. Presence is the second number and feeds
pretext.

**Chrome sets a floor under memorable.** Past about 25 Dissonance you cannot
be forgettable however you dress, which is the appearance layer paying the
same rent as everything else: you do not get the benefits of the hardware and
the anonymity of not having it.

Four slots are set at creation, four are free to change, and each origin
starts wearing a different face so ten backgrounds do not all walk into Marrow
in the same grey coat. Marks are the exception to all of it: the engine awards
them, the player never picks them, and they do not come off.

### D34: The tonal budget is enforced, not intended

The setting is grim and stays grim, but a city that is unrelentingly bleak
stops landing after about an hour, because misery with no floor under it is
just texture. So the ambient event layer has a budget with a floor *and a
ceiling* on each register: grim 50-70%, wry 20-35%, absurd 10-20%.

Absurd has a ceiling for the same reason it has a floor. Relief that arrives
every other shift is not relief, it is the tone.

`validate.py` checks the ratio, and also checks that every district can produce
all three registers, so the budget cannot be satisfied on paper and never in
play. Tone drift is invisible one entry at a time and obvious after forty,
which makes it exactly the kind of thing to encode rather than to trust.

The absurd entries are absurd the way an institution is absurd: internally
consistent, taken completely seriously by the people inside it, and quietly
sad underneath. **Footnotes** are the device that carries this. `{{like this}}`
anywhere in any content string; the console lifts them out and prints them
under the block. They nest, because the entire reason to have a footnote is
the writer who gets halfway through an aside and needs an aside about the
aside.

### D35: Nothing in the presentation layer is allowed to matter

There is an animated cold start, and a carrier handshake on the way into a
run, and neither is permitted to change anything. Every effect degrades to a
static frame, every frame degrades to plain text, and the game is identical
either way.

The gate wants a real tty **and** colour **and** a non-capturing console. All
three, which is why `test.py` can drive the boot sequence seventy times
without sleeping once.

Two rules that are not obvious and are both load-bearing:

- **Animation never draws from a game RNG stream.** An intro that consumed
  world entropy would mean the number of times you watched it changed which
  contracts appeared on the board. It has a private `random.Random` and
  `test.py` asserts the stream state is untouched across five boots.
- **Ctrl-C during an animation means "get on with it", not "quit".** It is
  caught, it redraws the final frame, and it does not propagate. The cursor is
  restored in `__exit__` whatever happens, because a hidden cursor outlives
  the process and the player will not connect that to this program.


### D36: The street and the net want opposite hours

The city ran on a three-shift clock from the beginning, and for a long time the
clock was a label: `morning`, `afternoon`, `night` appeared in the prompt and
nothing anywhere read them.

The clock is now a decision, and its shape is the same shape as D5's triangle:
two things you want, pulling against each other, priced in time.

At **peak** every walkway is at capacity, which is bad for you out there and
good for you in here, because all those people are generating the traffic you
hide in. Danger +18%, trace -8%. At **night** the street empties and nobody is
looking at you; so does the network, and now your session is the only session
and the trace has nothing to sort you out of. Danger -22%, trace +10%, prices
+14%. **Morning** is the middle of both, and when stock lands.

Four hooks: travel danger, the trace rate, market prices (itemised like every
other term, so `buy --why` shows it), and legwork.

`validate.py` holds the inversion: whichever shift is worst on the street must
be best in the net, and every shift must be under baseline on something. A
clock that is bad everywhere is a tax, not a choice.

The phase is fixed at the moment you jack in and does not tick over mid-run.

### D37: What the city remembers, it says out loud

The pitch has always been that the city remembers, and it always did, in the
numbers. Posture climbed, heat accrued, bounties were posted. None of it was
visible standing in the street: you had to open a reputation screen to learn
that the world had changed around you, which is the wrong surface for "this
street is different because of you".

`look` now describes where you are, what shift it is and what that shift is
costing you, how far the controlling faction's posture has moved from its own
baseline, and how much attention you personally are carrying here. The last two
are independent and print as two lines, because a district can be locked down
and not care about you, or unchanged and full of people who have your name.

**The neutral case has to be silent**, and `validate.py` enforces it. A
district that narrates itself when nothing has happened teaches the player to
skip the paragraph, and then the paragraph cannot tell them anything.

The same principle produced the appearance remarks: `memorable` was a number
the sheet printed and a multiplier on two systems nobody sees, so nobody in the
city ever looked at you and the claim had no evidence. Twenty-two reactions,
one for every feature striking enough to draw one, fired occasionally rather
than every time, because a city that remarks on you constantly is a city of
very rude people.


### D38: The shell is the player's, and the city does not get it

One system in this game costs nothing and takes nothing. Six axes of terminal
customisation, sixty-seven pieces, most of them earned by playing: palette,
prompt, frame, bars, marks, banner.

**It lives in meta rather than in the save.** The deck's interface belongs to
the player and not to the character, so it survives a flatline. That is the
entire reason it is stored there: you lose everything else, and the terminal
you spent a week getting right is still yours when you sit down with somebody
new.

Two promises, both enforced rather than intended:

- **Nothing here affects play.** `test.py` rices three axes and asserts that
  credits, experience, memorability, the contract board and every RNG stream
  are byte-identical afterwards. A cosmetic that moved a number would be a
  build decision hiding in a menu.
- **Nothing here is bought.** Every condition is a thing you did.
  `validate.py` rejects a catalogue where any single condition covers more
  than 45% of the unlocks, so the reward channel cannot decay into one number
  going up.

The one hard rule inside it: **whatever the prompt style does, the trace
survives**. Everything else on the prompt is one `status` away and costs
nothing to ask for. The trace is the number that ends the character. The
`path` style dropped it in the first draft, which is why that rule is a test
rather than a comment.

Capability still beats preference, as everywhere else: an ASCII terminal
ignores every set here, and a saved preference for something a later build no
longer ships degrades to the default rather than raising.

### D39: The game must be able to say what it is for

A playtester finished their first run without ever finding out what it was
for. That is not a difficulty problem and it was not fixed by writing more
help: the game genuinely did not say, and in three places it said it did.

**The single verb is `job`, and it works in both halves.** In the city: the
contract, the walk to it, the deadline measured against that walk, and what is
still missing from the deck. In a run: what finishing looks like for this
host and this record, where the thing is or what to look for when you have not
found it, how far along you are, and the next command to type. No time cost,
always safe to ask. `status` carries one row of the same thing, because
`status` is what a player checks when they are unsure and it used to answer
only "how much trouble am I in".

**The next step is computed, not authored.** Every run is the same five beats:
find it, reach it, open it, do the thing, leave. So the advice reads the state
and names a real host and a real service rather than printing `probe <host>`,
which is a syntax reminder given to somebody who did not ask about syntax. It
prices doors with the same `crack_check` that `odds` prints, so the advice and
the maths cannot disagree. It routes around wardens you have identified and
cannot pass, points at an auth server when the obstacle is an access tier
rather than a lock, and says to leave when there is nothing left to try.

**The bar is termination, not victory.** Doing what it says has to arrive
somewhere every time: the job done, the run over, or an honest "there is no
way on". Not every network is winnable by every build and the advice is
allowed to say so. What it may not do is loop, and every shape it could loop
in is now a test.

**Writing this found three things that were not true.**

`objective_met` did not check what you had acted on. `bool(done[kind])`
accepted an implant left on the reception desk and a wipe of any junk file in
the building against a contract that named one host and one record. The player
could not tell whether they had done the job because neither could the game.

Seven networks in ten put the objective behind a Gatekeeper, and a warden
guards the door rather than the room: you meet it from the node next to it,
and `strike` only reaches what is on your own node. Every counter is a rank 2
or rank 4 technique. `_ensure_passable` now opens one route the way
`_ensure_reachable` opens one edge, on the same principle stated in the same
file: generation may not produce a run that cannot be finished.

Nine of the ten origins ship without a payload and four of the six objectives
need one, while the shelves carried one in three worlds out of five. Markets
now always stock the cheapest breaker and the cheapest payload. That is a
floor under the market rather than a shortcut past it: the good programs are
still something you go looking for.

**The general lesson, which is the same one as D33 and D38.** Content that
claims something the engine does not do is the recurring bug of this project,
and it is at its worst in the tutorial, because the tutorial is read by the
one person with no way to tell it is wrong.

### D40: Three ways to borrow against later

Asked for at the author's request: a loan shark, gambling, and drugs. Built as
one system said three ways, because they are one system.

**The city already ran on this shape.** Residue becomes heat a shift after you
believed you were clean; that delay is the emotional point of D5's third
quantity and it is the whole game in miniature. These three are the same
sentence in three registers: something now, priced afterwards, at a rate you
were told.

**Money.** The debt machinery had been in since the beginning and debt could
only ever *happen* to you, which meant the interesting half was missing: a
debt you were handed is a difficulty setting, and a debt you chose is a plan
that did not work. Three lenders, and the thing that separates them is not the
interest rate, it is what happens when you stop paying. The Switchboard stop
finding you work. The Sixes come round. Carrion take payment in parts. Two of
the three are people the city already had, standing where they already stood,
and `validate.py` checks they have not been moved.

The lender key *is* the faction key, deliberately, because a debt records who
it is owed to and the fallout ladder resolves a visit by asking that faction
what its people do. Two identifiers for one lender is one identifier plus a
bug.

**Chemistry.** Ten drugs, and one number does all three jobs the brief asked
for. `habit` weakens the high, deepens the crash, and past four applies a
third block of effects *whenever you are not using*. That last step is the
system; everything before it is a stat buff with a bill, which any game has.
The moment worth building is a player looking at a number that used to be five
and seeing three and understanding that they did that.

Authored under a rule `validate.py` enforces: **the crash outlasts the high
and costs more than it paid**, measured on both axes. Six drugs failed it on
the first pass and were rewritten. A drug that came out ahead would not be a
decision, it would be equipment, and it would be correct before every run.

Ash Tea is the trap and the design in one item: it ends a comedown exactly as
advertised, and moves the price into the habit instead. Ozymandias Formula
No. 1 is the joke, and there is exactly one of them, which `validate.py` also
enforces.

**Luck.** Ninepins is two dice with a sixth of every stake in it, the same
edge on all three calls, so there is no correct bet and only a choice of
variance. It is fast, needs no build, and exists so that being broke has a
stupid solution with a number attached. Threes is the opposite: an evening,
resolved on Guile and Subterfuge, and the one place in this game a social
build is a build rather than a discount on conversations.

Both print the exact probability first, which is D14 applied somewhere D14 was
not written for. A casino that hides its edge is a casino. One that paints it
on the wall and lets you read it is this city, and nobody in it is deceiving
you; they are simply correct about how it will go.

**Winning is not free**, which is the thesis holding. Take enough off a room
and the house thinks less of you, the table gets measurably harder, and past
five thousand in a night everybody there can describe your face. Counted per
table rather than off faction standing: several origins start disliked by the
Switchboard, and a table that had learned how somebody plays before they sat
down is not a table, it is a bad mood.

**What building it turned up.** A comedown reduces `integrity_max`, and a bad
one on top of an unhealed run could take it to zero, which is a character dead
in the street from a hangover and a straight violation of D6. There is now a
floor in the one place every modifier in the game passes through. Integrity
*reaching* zero out here is still legal and is correct: it is a person who
cannot take another hit, which is survivable in the street and is not
survivable in a network, so `jack in` refuses it without `--force`.

### D41: Help is three questions, not one page

`help` printed every verb legal in the current context and then the whole
manual index. A hundred and forty-one lines, six screenfuls, and it grew every
time anything was added, which is the shape of every in-game help system that
nobody reads.

The diagnosis is that one screen was answering three different questions.
*What can I type* is the command list. *How does this work* is the manual.
*I am lost* is neither, and it is the only one that is urgent. Somebody asking
any of the three had to scroll past the other two.

So: `help` is now a landing page of about twenty-five lines. Four topics to
read in order, the four free verbs that answer "what now", and three pointers
to where the rest lives. `help commands` and `help topics` are the two indexes,
separately, and `help --all` is still both at once for anybody who liked it.

**`help <anything>` searches when nothing is called that.** With a hundred and
six verbs and thirty-five topics, the commonest failure is knowing what you
want and not what it is called. It scores over keys, titles, summaries, bodies,
command names and aliases, and one hit opens the thing rather than listing it.

Two things make the search actually work. `terms` are declared synonyms:
`help addiction` and `help loan` both found nothing because the prose says
habit and borrow, and writing a synonym into prose to satisfy a search is how
prose gets worse. And a topic's `covers` is used to index its own catalogue, so
`help gatekeeper` reaches the ICE topic and `help grave salt` reaches
chemistry, without anybody maintaining a word list.

**`covers` is the part worth keeping.** Every topic declares which content
modules it is the documentation for, and `validate.py` walks
`flatline/content/` and fails the build on any module no topic claims and that
is not explicitly exempt with a reason. That is this project's oldest rule
turned on its own prose: content declaring something the engine never reads is
a lie that ships because it works, and a system nobody wrote a topic for is
the same lie by omission. Two modules are exempt, the modifier vocabulary and
the manual itself.

The landing page is also held to being a page: the starter path is capped, and
every verb on the "lost right now" list has to cost zero ticks and work in both
halves of the game, because advice that costs the player the thing they are
short of is not advice.

**What it turned up.** `help --topic <key>`, the documented escape hatch for
the seven topic keys a command shadows, had never worked: it parses as an
option rather than a flag, so the check for it never fired and it silently
printed the index. And those seven pages ended with "Background: `help
chrome`" at the bottom of the page you reached by typing `help chrome`, which
also went unnoticed because the collision is through aliases half the time.

### D42: The seventeen people do something now

`Npc.offers` declared work, goods, intel and favours from the day the cast was
written. `who is` printed the list. Intel was real, through `ask`. The other
twelve declarations were a label attached to nothing, on people who are
otherwise the best-written content in this project.

That is the recurring bug class of this codebase living in its most human part,
which is the worst place for it: a character who exists to have an opinion
about what you are doing and cannot be asked for anything is a newspaper.

**The three are one relationship, not three features.** Work is a contract that
never reaches the board, pays over the board rate, and is held longer than a
posting. A favour is somebody spending their own standing on your problem. What
ties them together is the tab: every favour puts you one deeper with that
person, finishing work they handed you takes one off, and past `OWED_LIMIT`
they stop helping in their own words, which are not always unkind.

So the loop is that they trust you enough to hand you work, the work buys
favours, and the favours were what you actually wanted. Somebody who only ever
takes runs out of people one at a time, and the city gets quieter in a way
nobody announces.

Goods sit outside that, because a shopkeeper is not a friend and does not need
to be. What they keep back does not rotate with the market and is the only
supply of several things in the game.

**Routed through the existing machinery wherever possible.** Personal work is
generated by the ordinary contract generator and then bent, so it can be any
shape of job against any sensible target rather than becoming a thin second
contract system with a name on it. Private stock joins the district's listings,
so `buy` and `market` work on it unchanged.

Two rules with teeth in `validate.py`: an offer may only exist for somebody who
declares it, *and* every declaration must be served by something. The label and
the implementation are now unable to disagree in either direction. Favour
effects are checked against the engine source the same way ICE riders are.

**What the soak found.** Private stock did rotate off, because `refresh_stock`
rebuilds every shelf from scratch, so the one promise a cabinet makes that a
market does not was false the first time six shifts passed. And dropping
somebody's job could push the tab past its own ceiling, which made the screen
that says "as deep as they will let you get" a lie.

### D43: There is a door, and something goes through it

Two problems, one answer. This game has been called Flatline since the first
day and the flatline ended into a scoreboard; and the only two exits were
black ICE and closing the terminal.

**`retire` is the way out you choose.** It wants four things, and every one is
something the city has spent the whole campaign making harder: nothing owed,
nothing in you that you need, nobody paying for your name, and enough put
away. None is hard alone and all four at once is the game. Typed bare it
prints how far off you are, which is the only way anybody discovers this is a
goal.

That is the long arc the game did not have. A thirty-run character had money,
skills, chrome and *more contracts*. Now they have a door, and every loan,
every point of habit and every bounty is a thing they put between themselves
and it, usually for a good reason at the time.

**Dissonance does not gate it.** Somebody four fifths machine can leave this
business, and what they leave into is a different ending. Refusing them would
be the game saying their arc has no ending when what it has is another one.
Four endings, keyed to the same bands as the drift.

**Whichever way you go, you leave one thing.** A retirement leaves a share of
the stake or a name that still opens a door. A flatline leaves what gets taken
and what cannot be forgiven: chrome back on a Shambles shelf, a program in
circulation with your handle in the header, or a debt Carrion fully expect the
next person to honour.

One, and not chosen. An inheritance you picked would be a difficulty setting
with prose on it; one that arrives on your second day is the city having an
opinion about how you went. It is claimed exactly once, by whoever is made
next, during creation rather than at it.

**And afterwards the city says your name.** Occasionally, at about one ambient
beat in twenty, to somebody who never met you and is standing where you used
to stand. That is the thesis finally holding: this game remembers factions,
districts, postures and evidence left on a node three weeks ago, and it forgot
the player character completely.

Two details worth keeping. The Ghost's complication is starting with no
history, so a Ghost inherits neither a name nor a debt, and is told that
something was waiting and that nobody came for it: an inheritance must not
quietly cancel an origin's defining line. And a departed handle that collides
with a living rival's name is skipped, because `Vesper Okonkwo` runs in this
city and a player who names a character Vesper would otherwise get ghost
stories about somebody currently taking work off their board.

### D44: The other runners decide about you

Seven named people took work off the board for the whole life of this project
and the entire relationship was one number between -100 and 100. The bands
named it, `who` printed it, and nothing ever came of it: somebody at -80
competed with you in exactly the way somebody at zero did, and so did somebody
at +80.

**A bond is that number becoming a person.** Past either pole, and after
enough jobs, it latches, announces itself once in that runner's own register,
and changes what they do on the shift boundary for the rest of the campaign. A
nemesis talks about you to people who were not going to think of you, and your
name starts arriving before you do. A partner leaves things where you will
find them.

Two gates rather than one, deliberately. Disposition alone would let a single
betrayal on your fourth shift produce a lifelong enemy, and the whole point of
an arc is that it takes a campaign to earn.

**It latches.** A bond that came off because you did somebody a favour on a
Tuesday is a mood, and what makes thirty runs with the same person worth
having is that it does not reverse. That also makes their death land: a rival
dying is a line of news, and a partner dying is not.

Written per style, so the Hound declaring a feud reads nothing like Ledger
doing it, and Ledger deciding anything at all is the loudest thing that has
ever happened to Ledger.

### D45: Heat becomes something somebody can take

You have been resting in safehouses since the first build and could never have
one. That gap has a specific shape: heat has always been a multiplier on a
danger roll, which is a real cost and a completely abstract one. Nothing in
this city could physically take anything away from you for being wanted.

**A safehouse is a place to put things and a place that can be raided, and
those are the same half.** What makes storing anything a decision is that the
store has an address, and what makes the address matter is that enough
attention eventually finds it.

Storing money is the sharp end. Credits on you are exposed to a collector, a
mugging, and everything else in this city that takes cash out of a room.
Credits under the boards in the Ninth are exposed to exactly one thing, which
is rare and takes most of it. Neither is safe; they are *differently* unsafe,
which is the only kind of choice this project is interested in.

**What you buy is security, not space.** All four hold the same amount. The
difference between a floor cavity and a bonded container is not volume, it is
how many people have to be paid before somebody looks inside, and
`validate.py` checks price and security move together so that none of the four
is simply the right answer.

**Being unknown is the best security in the game and it is free.** Below a
floor of faction attention the raid chance is exactly zero, and no amount of
money buys a substitute. Two visits burns the place, because the second one is
somebody establishing that they know where you live.

### D46: A crew is a thing that can be lost

`hire` buys one runner for one job and then forgets them. That is a
transaction, and a transaction cannot be lost.

`crew` puts somebody on a retainer. They come in on every run without being
asked, take a smaller cut than a hire, and get better at working with *you*
specifically, up to a cap, which is a real thing and does not transfer.
Signing somebody is a harder ask than hiring them and costs more up front,
and `validate.py` enforces both directions so that a crew can never be
simply a cheaper hire.

**The whole system exists for the moment they do not come out.** A hire dying
costs a fee and a paragraph. Somebody who has been standing next to you for
thirty runs costs the thirty runs, so what gets printed scales on how long it
had been: three scenes, and the last one is about carrying somebody's opinions
around for a year without noticing whose they were.

Everything else is in service of that. The skill they earn is there so you
feel the investment. The smaller cut is there so keeping them is correct. The
retainer is there so it is a decision. And letting somebody go costs more the
longer they were there, because it should.

### D47: A bench, which is not a crafting system

Asked for as crafting, built as the thing crafting is usually a worse version
of. The obvious system spends materials and returns a catalogue item, which is
a discount on the market with extra steps: it makes every price in the shop
mean slightly less, and the interesting decision it produces is none.

**Nothing here produces an item.** Everything here changes one you already
own, permanently, in a direction nobody stocks. One axis up, one axis down, on
that specific component. `validate.py` weighs both sides and rejects anything
that comes out ahead, which is the drug rule applied to metal and for the same
reason: a change that was simply better is an upgrade you do to everything
once.

**It lives on deck components rather than on programs**, and that is a
representation decision as much as a design one. A component sits in exactly
one slot and there is exactly one of it, so "your cooling loop" is unambiguous
in a way "your Crowbar" is not when you own two. Doing this to programs would
have needed per-item identity threaded through every lookup in the game, to
produce a worse version of the same choice.

The work is keyed to the component rather than to the slot, because it was
done to the metal: sell the unit and the tuning goes with it.

**Scrap is a stock the player has been generating for hours without
noticing.** Fitting a component puts the old one in the bag, and over a
campaign the bag fills with things nobody will buy at a price worth the walk.
The rate is deliberately poor, and `validate.py` checks that no single junk
program pays for a modification, so this is a use for rubbish rather than a
second currency.

**What it turned up.** One modification fits every slot, and the slot-picking
logic took the first one with something in it, so `mod stripped` silently took
the chassis off a CPU when the cooling loop was full. Ambiguity is now asked
about rather than resolved.

### D48: Guile buys something out here

Measured rather than guessed. Every attribute had a derived stat except Guile:
Grit had two, Logic had Focus, Reflex had Tempo, Nerve had Composure, and Guile
had four skill checks that all happened inside a run. A player who put nine
points into it had bought a different way of opening doors and nothing else.
The city could not see it at all.

**Cover is the derived stat, and it is about time rather than about doors.**
Guile does not stop heat arriving, because talking your way in is not the same
as not being noticed. It decides how fast heat leaves. Over one job that is
nothing; over a campaign it is the difference between a name you can keep and
a name you have to burn, which is the most expensive thing in the game.

**And the two city sums that should always have read it now do.** A price
multiplied reputation, drift, faction attention and the hour, and never asked
how well the buyer could ask. Legwork read your face and the time of day but
not your manner, except for resonance, which is sitting near a network
listening and is deliberately the one kind that Guile buys nothing in.

**The find was much older than the feature.** Cover changed nothing at any
value, which was not a bug in Cover. `decay_heat` rounded heat to an integer
every shift, so a faction shedding 0.4 a shift shed `round(89.6) = 90` and
never moved. The twelve declared decay rates collapsed into four behaviours,
and the two slowest, Carrion and Sixes, were **permanent for the life of the
project**. Nothing looked wrong from outside: the number on screen was an
integer either way, and a gang that never forgets is exactly what a gang
would do.

A rate declared as a float and applied to a value stored as an int is not a
slow effect. It is no effect, and from outside it is indistinguishable from a
slow one. That generalises well past heat.

Three standing checks came out of it. `check_heat` drives the real decay path
rather than a copy of the arithmetic, and fails if two factions with different
declared rates cool in the same number of shifts. `check_guile` is source
level: `quote()` must take a Guile argument and every one of its five call
sites must pass one, because a keyword argument with a default of zero is how
four call sites out of five quietly stop reading a stat. And a **dead-points**
check, which is the general form of a mistake made while writing this: the
haggle discount was capped at a flat 18%, which made Guile 7, 8 and 9 points
the character sheet sells and nothing reads. Every value in the attribute range
must now buy something.

### D17: The finish line

**Phase 4 is a legitimate stopping point.** At the end of Phase 4 the game has: a full character build, procedural networks with real ICE, the noise/trace/residue triangle, a persistent city with factions that react, and consequences that carry between runs. That is a complete game that can sit indefinitely without being unfinished.

Phases 5 and 6 are depth and breadth. They are for when the game is being played and something specific is found to be missing, not for working through as a checklist.

---

## Systems design

### 1. The character

#### Attributes

Five, each 1 to 10, starting spread around 3 to 5. They are deliberately few, because the interesting differentiation lives in skills and gear, and because five numbers can be held in the head while twelve cannot.

| Attribute | Governs | Failure feels like |
|---|---|---|
| **Logic** | Exploit construction, cryptanalysis, understanding what you are looking at | You cannot break what you do not understand |
| **Reflex** | Actions per tick, evasion, reacting to ICE that has already noticed you | Everything happens to you before you happen to it |
| **Nerve** | Resisting black ICE, holding function under trace pressure, not panicking | You fold at exactly the moment folding is fatal |
| **Guile** | Social engineering, forging credentials, passing as someone with a badge, what you are charged, what strangers tell you | Every door needs to be broken, every price is the asking price, and your name never cools |
| **Grit** | Stamina across a long run, recovery, absorbing damage to deck and body | You are fine right up until you are not, and then the run is over |

**Derived:**

- **Bandwidth** = 8 + Grit. The capacity budget cyberware spends.
- **Integrity** = 10 + (2 x Grit). Damage you can take before the run ends badly.
- **Focus** = 3 + floor(Logic / 2). A per-run resource spent on precision actions: retries, forced successes, careful work that reduces residue.
- **Tempo** = 1 + floor(Reflex / 4). Actions per tick during real-time ICE engagement.
- **Composure** = Nerve, less what the drift has taken. Resistance to black ICE and panic.
- **Cover** = 2 x Guile. How fast heat cools, on every faction at once. See D48.

#### Skills

Eight lines, 0 to 5 each, bought with experience. Every line has a mechanical identity, not just a number that goes up.

| Skill | What it buys |
|---|---|
| **Intrusion** | Breaking services. The bread-and-butter attack skill. |
| **Cryptography** | Cracking encrypted stores, key material, secure channels. Gates the highest-value data. |
| **Subterfuge** | Social engineering, pretexting, forged credentials. The alternative to breaking things. |
| **Hardware** | Deck tuning, overclocking without frying, physical taps, drone work. |
| **Stealth** | Noise reduction at the source. Makes everything you do quieter rather than making it work better. |
| **Warfare** | Direct ICE engagement. Killing what is hunting you instead of hiding from it. |
| **Forensics** | Anti-forensics. Residue reduction, log manipulation, understanding what you are leaving behind. |
| **Daemonology** | Automation. Writing scripts and autonomous programs that act without you. The deepest skill and the one that changes how the game is played rather than how well. |

Each skill has five ranks, and ranks 2 and 4 unlock a **technique**: a new verb in the shell or a new option on an existing one. Investment changes what you can type, not just what number you roll. That is the difference between a skill system and a stat block.

#### Origins

Six at v1. Each sets starting attribute shape, gear, faction standing, one passive, and a starting alias with its own history.

- **Corporate defector.** Started inside. Knows how corps think. Begins with real credentials that still work, and a corp that wants them back.
- **Gutter runner.** Self-taught in a squat off salvaged parts. Cheap, fast, loud. Best starting gear-per-credit and the worst gear.
- **Fixer's protege.** Grew up in the trade. Best starting reputation and contract access, thinnest technical foundation.
- **Academic.** Cryptography background, no street sense. Highest Logic, lowest Guile, and prices that reflect it.
- **Ex-enforcement.** Worked the other side. Reads ICE like a native and reads people worse. Starts with a bounty.
- **Chromed.** Already more machine than most. Starts with high Dissonance, real net-side power, and a city that treats them like a walking incident report.

#### Cyberware

Slots by location: **neural** (2), **ocular** (1), **cortex** (2), **spinal** (1), **limb** (2), **subdermal** (2). Each piece costs Bandwidth and Dissonance, and carries a named drawback (D11).

The design rule: a piece of chrome should change a decision, not a number. A "Kohler-Reyes Threadpuller" that lets you run two programs against one target simultaneously but doubles the noise of both is a decision. A "+1 Logic implant" is not, and does not ship.

#### The deck

Six component slots, each swappable, each a tradeoff:

- **CPU:** action economy vs heat generation
- **Memory:** how many programs you carry (D12)
- **I/O:** connection speed, which sets how much you accomplish per tick
- **Cooling:** heat headroom, which gates overclocking
- **Masking:** trace resistance, at the cost of memory or speed
- **Antenna:** range and remote-run capability, at the cost of a bigger signature

**Overclocking** is a live decision during a run: push the CPU past rated speed for more actions per tick, generating heat. Heat above threshold risks component damage and adds trace. Hardware skill sets how far you can push before it bites.

### 2. The run

A run is a procedurally generated network plus a contract that says what you are there for.

#### Network structure

A directed graph of **nodes**. Each node has a type (gateway, workstation, server, controller, vault, honeypot), a set of **services** (the attack surface), an **access tier** required to enter, optional **ICE**, and optional **data**.

Networks are generated in **zones** with increasing tier: perimeter, interior, restricted, core. Zone boundaries are chokepoints and are where ICE concentrates. This gives networks a readable shape rather than a random mesh: you can always tell roughly how deep you are and what it cost to get there.

Generation is parameterised by the target's **security posture**, which is a persistent per-faction value the city layer raises every time you succeed against them (D5, residue). The same corp gets meaningfully harder to rob over a campaign, and the player can watch it happen.

#### The tick

A run advances in ticks. Every command that does work consumes tick budget based on your I/O and Tempo. Trace advances per tick plus per noisy action. This means fast builds genuinely get more done per unit of trace, and it makes I/O a real stat rather than flavour.

#### ICE

Intrusion countermeasures are the opposition. Types at v1:

- **Sentry.** Passive. Watches a node, raises noise when it sees something. Cheap to evade, common.
- **Probe.** Active. Moves through the network looking for you. Has to be avoided or misdirected, not fought.
- **Hunter.** Active and hostile. Locks onto you and does deck damage until killed or shaken.
- **Trap.** Passive and invisible until triggered. Spikes trace or drops your access tier.
- **Warden.** Guards a chokepoint. Cannot be evaded, only broken, subverted, or talked past with credentials.
- **Black.** Lethal. Guards cores. Does Integrity damage rather than deck damage, and is the only route to a flatline (D6).

Each ICE piece has a **rating**, an **attack pattern**, and a **tell**: a specific line of output that appears one tick before it acts. Reading tells is the skill ceiling of the combat layer, and it is why the log is the interface rather than a health bar.

#### Objectives

Contracts specify one or more: **exfiltrate** a named data asset, **implant** a persistent backdoor, **corrupt** a record, **surveil** (stay resident undetected for N ticks, which inverts the whole risk calculus), **wipe** an asset, or **escort** (protect a rival's run, which introduces an ally who makes noise you did not choose to make).

### 3. The city

#### Structure

Six districts, each with a controlling faction, a security level, an economy flavour, and a set of locations (fixer, clinic, market, safehouse). Districts gate what you can buy and who will talk to you.

#### Factions

Eight at v1: three corps, two gangs, a fixer network, an enforcement body, and an underground collective. Each tracks:

- **Reputation** with you, from hostile through neutral to trusted, per alias (D13)
- **Heat** on you specifically
- **Security posture**, which is how hard their networks generate
- **Relations** with every other faction, so helping one is legibly hurting another

#### Time

Time advances in **shifts** (three per day). Everything costs shifts: travel, legwork, downtime, recovery, establishing an alias. The contract board refreshes on a cycle, contracts expire, and heat decays slowly with time, which makes "do nothing for a week" a real and sometimes correct strategic option.

#### Legwork

Before a run, you can spend shifts learning about the target: mapping the perimeter, buying intel from a fixer, social-engineering an employee, tapping a physical line. Legwork converts shifts and credits into **prior knowledge**, which materially changes the run: known node layout, known ICE placement, a credential that skips a zone boundary.

This is where the loadout decision (D12) gets its teeth. Legwork tells you what to bring.

#### Rivals

Named NPC netrunners with their own builds and their own agendas. They take contracts you decline, and the world changes accordingly. They can be encountered mid-run. They can be hired. They can be sold out. They accumulate reputation the same way you do, and the board shows their names next to jobs that are no longer available.

### 4. The shell

Two contexts with two verb sets, plus a shared core.

**City context:** `board`, `take`, `travel`, `market`, `buy`, `sell`, `install`, `uninstall`, `deck`, `load`, `unload`, `legwork`, `rest`, `alias`, `burn`, `rep`, `char`, `skills`, `train`, `save`, `jack in`.

**Run context:** `scan`, `probe`, `map`, `connect`, `route`, `crack`, `spoof`, `forge`, `deploy`, `kill`, `mask`, `pull`, `push`, `wipe`, `sweep`, `overclock`, `focus`, `jack out`.

**Shared:** `help`, `odds` (D14), `log`, `status`, `alias` (shell aliases, distinct from identity aliases; the collision is deliberate and the fiction absorbs it), `script`, `history`, `quit`.

**Scripting** is the Daemonology payoff: save a command sequence to a named script, run it as one action with a tick discount, and at higher ranks attach conditions so the script reacts. This is a real automation layer and it is the thing that makes a fifth playthrough different from a first.

---

## Phases

> **Status:** Phases 0 through 4 are complete. **D17's finish line is reached:**
> the game is a complete thing and can sit here indefinitely without being
> unfinished. Phases 5 and 6 are depth and breadth, for when the game is being
> played and something specific is found to be missing.

### Phase 0: harness

The skeleton that runs and proves the invariants.

- `config.py`, `theme.py`, `ui.py`, `rng.py`, `save.py`
- `shell.py` with the D9 command table, dispatch, help, completion
- `app.py` entry point, argument parsing, session loop
- `validate.py` and `test.py` in place, both green with real assertions
- `build.sh` producing `dist/flatline.pyz`

**Done when:** the game boots, accepts commands, saves, loads, and `--seed` reproduces.

### Phase 1: the character

- Attributes, derived stats, skills with techniques, origins
- Cyberware with Bandwidth, Dissonance, and drawbacks
- The deck with six component slots and overclocking
- Programs with memory cost and signature
- Character creation as a shell flow, and `char` / `skills` / `deck` inspection commands

**Done when:** you can build a character six meaningfully different ways and read the whole build back.

### Phase 2: the run

- Network generation by zone and posture
- Nodes, services, access tiers, data assets
- The tick, the noise/trace/residue triangle
- ICE: all six types with tells
- The run command set, and run resolution into consequences

**Done when:** you can jack into a generated network, break into it, take something, and get out, and the way you did it is recorded.

### Phase 3: the city

- Districts, factions, relations, reputation, heat
- Time in shifts, the contract board, expiry
- Market with stock and posture-driven pricing
- Aliases and burning
- Legwork

**Done when:** the run has a reason and an aftermath.

### Phase 4: consequences

- Residue converting to heat and posture after the fact
- Rivals acting on their own
- Bounties and dangerous districts
- The full failure ladder from D6
- Save migrations proved with a real migration

**Done when:** D17's finish line is reached.

### Phase 5: depth

Scripting and daemons, more ICE behaviours, more objective types, more origins, the Dissonance arc paying off in city-side content.

### Phase 6: breadth

More districts, factions, chrome, and programs. Content, not systems.

---

## Session log

### 2026-08-12 (a): project created

Scoped the project from a blank start. Four decisions taken up front, all locked here: Python, hybrid persistent-city-plus-roguelike-runs, diegetic shell, full classless build system.

Named it **flatline**. In Gibson, to flatline is what black ICE does to you: the EEG goes flat and you do not come back. It names the stakes rather than the power fantasy, which is the right emphasis for a game whose whole tension is that everything you do is loud. Short, lowercase, one word, and unclaimed by anything dominant. Renaming later is cheap and this project has prior art for doing exactly that.

Surveyed `hone` for conventions and adopted them deliberately: plan document at the project root with a START HERE block, locked decisions with citable numbers, `validate.py` and `test.py` split by what-content-says versus what-app-does, stdlib only, `build.sh` producing a zipapp, and the author's own doom-cyberpunk-neon palette carrying all three capability rungs.

The one significant departure from hone is D2. hone is a TUI with screens; flatline is a REPL. That was the user's call on interface, and it turns out to be load-bearing for testability: a shell session is strings in and strings out, so `test.py` can play whole runs.

### 2026-08-12 (b): playable end to end

Built Phases 0 through 3 in one sitting. The loop closes: create, take, travel, legwork, jack in, break in, take something, get out, and feel it a shift later.

**Four bugs the harnesses caught that playing would not have.** `wrap()` used the length of the subsequent-indent as its "start of line" test, which silently ate every run of padding in `help` and `skills`. `validate.py` caught three techniques (`hotswap`, `falsify`, `daemon`) whose skill-tree entries promised shell verbs that did not exist, and one asymmetric faction relation. `test.py`'s command fuzz caught five commands that turned a typo like `rest zzz` into a traceback, which is now fixed centrally with `Args.int_at`.

**Two balance problems visible only from generated output.** The Sixes, a gang whose doctrine promises "almost no ICE", were generating *more* countermeasures than Kagawa, because density scaled on posture alone. Density now scales on faction kind as well, and the gradient runs 0.37 ICE per node for the Sixes to 1.20 for Aoyama. Separately, wardens were placed at every zone boundary regardless of who owned the network, which gave a gang's back room a corporate Chamberlain on it; warden placement is now doctrine-sensitive too.

### 2026-08-12 (c): tone and the VR layer

Two directions from the author, both taken: grimmer and grittier, and lean into the deck and cyberspace rather than anything resembling combat.

Added **D19**, cyberspace as a place, which is the change that stops a run reading like a port scan. Added **D18**, the icon system, which is both the most VR-native idea in the game and a fourth customisation axis: a cheap, swappable, tactical one under the three permanent ones. Icons tie back to the Dissonance arc through coherence, which finally gives a chromed build something it is *better* at rather than merely stranger.

Rewrote the run outcomes in the grim register: the room coming back one sense at a time, the nosebleed you did not feel start, and a flatline that is not a disconnection but simply the last thing.

Nothing in this project has ever had a gun in it and nothing will. The conflict layer is program against countermeasure, through a deck, and "Warfare" is a netrunning skill that never leaves cyberspace.

### 2026-08-13 (a): Phase 4, and the finish line

Built the consequences layer. **D17's finish line is reached.** `validate.py` clean, `test.py` green at **4943 checks**.

Added **D20** in two halves. Rivals act on the shift tick and the world hardens without the player, which retroactively makes the whole city layer tenser: the board is now a queue you are competing for rather than a menu you are browsing. And the D6 failure ladder is finally a ladder, with bounties, dangerous districts, and five specific things that being picked up can cost you.

`escort` and `surveil` stopped being stubs. Surveil inverts the run entirely: get somewhere valuable, then do nothing, for eight ticks, while every instinct the rest of the game has trained says take one more thing. Escort puts a named rival in the network generating noise you did not choose.

**The escort's first implementation was wrong in an instructive way.** ICE only engaged them when the player was standing on the same node, which meant the correct play was to ignore the escort entirely and let them walk the network alone. That is the exact opposite of what the objective is for. They are now exposed wherever they are, they open their own doors badly, and the player's counterplay is to hold them still, clear the road ahead, or stand there and take it instead.

Two smaller things the harness forced. Rivals initially stripped the board faster than a player could read it, roughly 1.5 contracts a shift against a five-slot board; capped now. And `disposition_band` labelled +15 as "cold", because the band boundaries had drifted off zero, which `validate.py` now asserts directly.

**Schema 2 exists, and the migration is real.** D7 promised forward migrations and nothing had ever proved one. A schema-1 save now opens, gains a runner pool, an icon, and a bounty ledger, and round-trips cleanly. `test.py` proves it by forging a v1 save and loading it.

### 2026-08-13 (b): Phase 5, the social layer

Rivals became a system you act on rather than a feed you read. `hire`, `ask`, and `betray`, plus the ally mechanics that make a hired runner worth their fee: style decides what they are for, and a chromed one will physically step into a strike aimed at you.

**The design problem this solved.** Phase 4 shipped rivals whose disposition only ever went *down*, and favours priced above anything reachable. The fix was not to lower the prices, it was to notice that `escort` was already the answer: the objective where you spend a night keeping somebody alive is exactly where a relationship should come from. Escort now pays 18 disposition on a clean run and costs you dearly when they die, which turns the odd-one-out objective into the engine of the whole social layer.

**One bug that only shows up in play.** A runner you had hired was still eligible for the shift-tick rival turn, so between paying their fee and jacking in they could be sent off on somebody else's contract and killed, taking the fee with them. `city.hired` now marks them busy and is deliberately held through the run rather than cleared at the door.

**One design call worth recording.** `betray` is its own verb rather than an overload of `sell`. The command registry refused the duplicate, which was the right refusal for the wrong reason: selling a program and selling a person should not share a word.

`validate.py` clean, `test.py` green at **5044 checks**.

### 2026-08-13 (c): Phase 5 continued, reactive scripting

Added **D22**. `script` stopped being a macro recorder and became a small
conditional language, which is the Daemonology payoff and the most on-theme
feature left in the game. Four statement forms, sixteen readable conditions,
three shipped examples that double as the tutorial, and a `script help` that
prints the whole vocabulary.

The language lives in `flatline/script.py` and is pure: parsing produces `Step`
objects and evaluation reads a state object, with the session doing the
dispatch. That split is why `validate.py` can check every shipped example
parses and names real commands, and why `test.py` can evaluate every declared
condition without standing up a run.

**One bug worth recording.** `script write mine pull --all` stored `pull`,
because the command layer parses `--all` into a flag set and `Args.rest()`
returns positionals only. Anything that stores a command to run later needs the
text as typed, so `Args.raw_rest()` now exists and the two are documented
against each other.

**The loop is now closed.** `daemon script <name>` reads a script as a
*policy* rather than a program: every tick the daemon re-reads it and the first
step whose condition passes names its task. So Daemonology rank 2 writes the
automation and rank 4 sets it running unattended, which is the arc the skill
description promised from the beginning.

The important restraint is that a daemon only ever gets its own three tasks
(`hold`, `grind`, `noise`), never the player's verb set. An autonomous process
that could type `jack out` would be puppeting the player rather than helping
them, and the command refuses to deploy a script that names nothing a daemon
can do rather than silently ignoring half of it.

`validate.py` clean, `test.py` green at **5058 checks**.

### 2026-08-13 (d): the drift arc

Added **D23**, the city-side half of Dissonance, which was the last real
systems gap on the list.

The design turn that made it work was noticing that the arc needed a **door
that opens**, not just penalties that accumulate. Restricted chrome now exists
nowhere except the back of a clinic, and the back only opens above 50
Dissonance. That single rule converts the whole axis from a tax into a
bargain: the best hardware in the city is sold only to people who have already
gone too far to be sold anything else.

Grounding is the counterweight and is priced to be a bad deal on purpose. It
cannot go below the chrome floor, which is what keeps D11's one-way rule
intact while still letting a player change their mind at real cost.

`validate.py` clean, `test.py` green at **5114 checks**.

### 2026-08-13 (e): breadth

Every system the plan set out to build is built, so this was content. The
catalogue went from 18 chrome / 26 programs / 14 ICE to **26 / 36 / 20**, plus
four new services.

Chosen by auditing what was thin rather than by writing whatever came to mind.
Three findings drove the whole pass:

- **Only six restricted implants existed**, and the D23 back room samples three
  of them, so the reward for the entire Dissonance arc was nearly the same
  three items every time. Now ten.
- **Forger had two programs**, which meant a Subterfuge build had no loadout
  decision to make in the one category that defines it. Now four, and the same
  went for wipers, armour, and daemons.
- **Ocular had two options for one slot**, which is a choice, but a thin one
  for the slot with the least room to hedge. Now four.

Everything new holds the same bars: every implant has an honest drawback with a
penalty dict or an implemented rider, and the one new rider (`slow_exit`, the
Grave Governor holding a session open you are trying to leave) is wired into
`jack out` rather than existing only in prose.

Verified by generation rather than by eye: over sixty networks across all eight
factions, **all twenty ICE types and all fifteen services appear**, so nothing
was added that the generator cannot reach.

`validate.py` clean, `test.py` green at **5133 checks**.

### 2026-08-13 (f): the city, and ten ways into it

Districts nine, origins ten, and one systems addition to make one of them work.

**Three districts, chosen so every faction that holds ground has somewhere.**
Nightwatch got a precinct with a surplus counter nobody has audited; Carrion
got the Shambles, which is cheap for a reason; and Kagawa got the Terraces,
which exists for tone rather than mechanics. The Terraces is the one district
where nobody is in this business, and its whole job is to be the thing the rest
of the city is happening to. A game about a city that does not care whether you
live needs somewhere that shows you what it is not caring about.

**Four origins**, chosen to open play that did not exist: the Indentured, who
are running to afford a corporation rather than away from one; the Burnout, who
knows everything and cannot move any more; the Legally Dead, who start with no
standing, no heat, and nobody; and the Courier, who learned the streets first
and the net last.

**The audit that mattered.** Writing the Indentured's debt meant checking what
the other passives actually did, and several did nothing at all: the Gutter
runner's repair discount pointed at a repair command that had never been
written, and the Chromed origin's opening action and the protege's pay
negotiation were both prose. That became **D24**, which `validate.py` now
enforces, and every passive in the game has a mechanical half.

**D25** is the debt system that the Indentured needed and that the academic's
complication had been promising since the first session. The invariant that
makes it shippable is checked rather than hoped for: collections must outpace
interest, or the debt is a death sentence and D6 forbids those.

`validate.py` clean, `test.py` green at **5257 checks**.

### 2026-08-13 (g): four more powers, and a construct that does not fight

**Twelve factions.** Meridian Trust, who hold the paper rather than the ground
and whose networks are cryptographic to the exclusion of everything else. The
Chorus, who have decided that what happens to a netrunner at high Dissonance is
not a symptom. Static, a pirate press who publish rather than sell. And
Deepwater, which has placed contracts through four fixers for nine years
without once meeting anybody, and whose networks are not defended but
inhabited.

**None of the four holds a district, and that is the characterisation.** A bank
owns paper, a cult meets in other people's clinics, a pirate broadcast is
nowhere on purpose, and whatever Deepwater is, it does not have offices. Every
faction that holds *ground* has somewhere; these do not hold ground.

Three new faction kinds came with them (`cult`, `press`, `construct`), which
meant finding every place the code branches on kind. That is a real failure
mode: a missing branch is a `KeyError` in network generation that a player
discovers rather than the build. `validate.py` now generates one network per
kind at build time specifically to catch it.

The doctrine gradient came out exactly as written: Static generates 0.24 ICE
per node against Kagawa's 1.00 and Deepwater's 1.38.

**D26** is the herder, the first ICE behaviour that does no damage. Eight new
constructs in all, including one apiece for the new powers: a Notary that
guards keys rather than data, a Psalm that asks what you are doing here and
appears interested in the answer, a Stringer that publishes you to everybody
rather than to security, and an Undertow that does not approach.

`validate.py` clean, `test.py` green at **5796 checks**.

### 2026-08-13 (h): code audit

No new features. A systematic read of ~16,000 lines looking for the things the
harnesses cannot see. **Seven real bugs**, three of them reachable in ordinary
play and one of them severe.

**The severe one: a run that ended mid-command never settled.** When the trace
completed, or black ICE landed, or the deck died, `RunState.finish` ran but
nothing told the session. The player stayed inside a finished run, kept issuing
commands against a dead connection, and none of the consequences ever applied.
The central failure state of the game did not actually fail. `_act` now settles
up when a run ends inside it.

**Overclocking stopped the clock.** Step 1 cost heat and gave nothing at all,
and step 2 reduced every one-tick action to zero ticks. At zero ticks `advance`
never runs, so the trace stopped, the ICE stopped, and the entire run clock
stopped with it: a Hardware 2 build could take unlimited actions for free.
Rebuilt as a credit pool, so "one extra action per tick per step" is literally
what happens and eight actions cost 8 / 4 / 3 / 2 ticks at 0 / 1 / 2 / 3 steps.

**Nullsig lied about its duration**, decrementing once per action *and* once
per tick, with the action decrement applied before `advance` so the last point
of the window protected nothing. The announcement promised seven ticks and
delivered three and a half.

**Three separate cases of content promising what the engine does not read**,
which is now the bug class this project has to be most careful about, because
it validates, it ships, and it lies:

- `crack --chain`, Intrusion rank 2, the first technique most players unlock:
  the flag was never read. It announced itself on training and did nothing.
- `credential_check`, declared by three wardens and read nowhere. Implemented
  as the Subterfuge answer to a door that cannot be evaded: `connect --present`
  shows the warden what you are carrying, with the odds printed first per D14.
- `alert_jump` on non-trap constructs, ignored on the strike path, which made
  the one distinguishing feature of Verger, Psalm and Stringer decorative.

`validate.py` now has source-level checks for the whole class: every declared
ICE rider must appear in the run layer, and every technique naming a `--flag`
must have a handler that reads it. Both would have caught all three.

**Also:** eleven dead definitions removed, and `data_price` wired up. That last
one was a designed fence economy sitting unused while `_resolve` hard-coded a
flat 50%; the haul now clears at 33% to 74% of nominal depending on standing
with the buyer, which gives reputation a second job.

**One thing deliberately not changed.** Stripping a network bare pays about
1.95x doing only the job. That reads as the intended D5 tension rather than a
fault, and the cost of the extra nodes is trace, noise and residue. It is
flagged here rather than tuned, because tuning it without play would be a
guess.

`validate.py` clean, `test.py` green at **5832 checks**, with regression
coverage for every bug above.

### 2026-08-13 (i): the manual, the tutorial, traits, and four more skills

The largest single session of content, in response to two asks: a help system
that explains how things interact, and deeper customisation.

**D27** is the manual and the tutorial. Twenty-one topics and fourteen watched
steps, both checked by the build.

**D28** is traits: twenty-six of them, five slots at most, every one cutting
both ways. This is the axis that was missing, and the reason it works is that
it can never be completed.

**D29** came out of writing the new skill lines and counting the old ones.
Logic governed five of eight and Grit governed none, which meant everybody's
opening spread was identical and the customisation on offer was partly an
illusion. Hardware and Forensics moved to Grit, the four new lines went to
Logic, Reflex, Guile and Nerve, and the spread is now a build check.

Four new lines with eight new verbs: **Architecture** (chart, backdoor),
**Signal** (listen, intercept), **Sabotage** (misdirect, collapse), and
**Psyche** (steady, dissociate). Between them they give stealth builds real
reconnaissance, wipe contracts a real answer, and black ICE a counter that is
not "kill it".

**One latent bug found on the way.** `crack_check` held its own literal copy of
the skill-to-attribute mapping, which would have silently gone stale the moment
Hardware moved to Grit: every Hardware check would have kept rolling against
Logic. It now reads the attribute off the skill definition.

`validate.py` clean, `test.py` green at **6004 checks**.

### 2026-08-13 (j): people, and things happening to them

**D30** and **D31**: eighteen NPCs and eight crossing threads, plus chrome to
34 and programs to 46 aimed at the four new skill lines.

The design problem worth recording is non-linearity. The obvious implementation
of a storyline is a chain: stage two unlocks after stage one. That produces
something the player experiences as a queue, and it cannot cross another
storyline without one of them owning the other.

Modelling the whole layer as **one set of flags** solves both at once. A stage
asks whether some strings are present; meeting somebody, reaching a scene and
taking a choice all put strings in. Crossing is then not a feature that had to
be built, it is what happens by default, and the only work left was checking
that claimed crossings are real. Seven were not.

`any_of` came out of that check. Several threads claimed to cross and shared
nothing, and the honest fix was not to delete the claim but to give stages a
second door, which is what the design said it wanted from the beginning.

**One structural cleanup.** NPCs originally carried a `threads` field listing
what they could open, which duplicated what `met:<key>` in a stage's
requirements already says. Two places that can disagree is one place plus a
bug, and it had already drifted: nine of the listed threads did not exist. The
field is gone.

`validate.py` clean, `test.py` green at **6110 checks**.

### 2026-08-13 (k): complications become threads, and origins get teeth

**Ten origin threads.** Every origin has carried a complication since the first
day of this project and every one of them was a sentence. Kagawa really do want
the laptop now, and there is a third partition on it. Mara really is owed
something, and she has been waiting eleven years for the right person to ask.
The package really is still in your bag, the address really is live, and there
really is a standing order on it renewed four months ago.

They gate on `origin:<key>`, so a character sees exactly one, and they cross
into the general threads wherever the fiction wants.

**One design error the build caught.** Two origin-gated threads can never both
exist on the same character, so a crossing between them is not merely
unshared, it is impossible. `laptop` claimed to cross `buyout`, which no
character could ever see. `validate.py` now rejects that class outright.

**D32** came from the observation that everything an origin gave was a
modifier, so two characters forty shifts apart could still do all the same
things. Ten signature verbs, one apiece, unpurchasable.

`validate.py` clean, `test.py` green at **6245 checks**.

### 2026-08-13 (l): verification pass

A check-everything sweep before the first real play session. Two classes of
problem, both of them things the harnesses could not see because both were
about content and commands being *correct but not connected*.

**Twenty-seven city commands were legal inside a run.** `contexts` defaults to
`('any',)`, and almost nothing in `commands/city.py` had ever declared
otherwise, so `travel`, `market`, `install`, `take` and two dozen others could
be typed while jacked into somebody's network. D9's stated example is that
"`market` does not exist while you are inside somebody's network" and it had
not been true for weeks. `validate.py` now rejects any `city` or `prep` command
that has not declared its context.

**Four fields of written content were never displayed.** A sweep of every
content dataclass field against the whole engine found: `Signature.ice_wakes`,
twelve pieces of per-faction menace that had never once printed;
`Signature.texture`, the faction's materials, unused; `Ware.maker`, on all
thirty-four implants, never shown; and `Attribute.governs` and
`.failure`, written to tell a player what an attribute is for and shown
nowhere. All four are wired in now, and the sweep is worth repeating whenever
content grows.

The only field deliberately left content-only is `Npc.tone`, which exists so
`validate.py` can assert the cast spans registers. That is now said in the
field comment so the next sweep does not flag it.

`validate.py` clean, `test.py` green at **6245 checks**.

### 2026-08-13 (m): a face, a tone, and a cold start

Three things, in response to three notes from the author: make the character
theirs, let the city come up for air the way Pratchett does, and make the
terminal do something a terminal is not supposed to do.

**D33, appearance.** 102 features, eight slots, four earned marks. The design
question was how to stop it being a paper doll, and the answer was to make the
central number cut both ways: being worth describing earns you more standing
and more heat at the same time, so there is no correct answer and both extremes
are builds. Ghost starts at -15 memorable, Chromed at +20, and the ten origins
span 35 points of it.

`validate.py` caught two features that moved neither number on the first run,
which is exactly the check earning its keep. The RNG guard refused `self
--roll` drawing from a shared stream, correctly: how many times you reroll a
haircut must not change the contract board. The command registry refused
`look`, which was already taken, and `self` turned out to be the better verb
in a game about a body you keep replacing.

One real bug, found by writing the test rather than the feature: the chrome
floor was applied unconditionally, so `max(memorable, 0)` clamped every
negative score to zero and silently deleted the entire forgettable half of the
scale. That is the half that people who do not want to be found are buying.

**D34, tone.** Footnotes as a real console feature, with nesting, flushed by
the dispatcher so any content anywhere can use one without knowing it exists.
Then 51 ambient events on a budget that `validate.py` enforces.

The interesting constraint turned out to be the *ceiling* on absurd rather than
the floor. The first draft came out at 22% and read as a comedy game with grim
bits, which is the opposite of the brief. Writing five more grim entries fixed
the ratio and was also just the right thing to write.

Ambient events are proven unable to touch credits, damage, xp, marks or
Dissonance. The moment scenery can pay you, players stop reading it for the
city and start reading it for outcomes.

**D35, motion.** A boot sequence that POSTs the deck the character actually
owns, decrypts the wordmark out of noise, and then does the thing the game is
named after. A carrier handshake on the way into a run. Both tested at every
rung of the capability ladder: no escape codes at all without colour, nothing
above codepoint 127 in ASCII mode, nothing overflowing 40 columns.

Also fixed while in here: the markup checker was collecting every content
source twice, so any failure in npcs, threads, traits, manual, tutorial or
rivals would have been reported as two identical errors.

`validate.py` clean, `test.py` green at **6533 checks**.

### 2026-08-13 (n): the clock, the street, and a sweep of my own work

**D36, the shift clock.** The city had a three-shift day that nothing read. It
now inverts: peak is dangerous outside and safe inside, night is the reverse,
and there is no correct shift to work, only one that suits the job. The
constraint that made it worth building is that waiting for the right shift is
priced in the only currency this city charges in.

**D37, the city saying what it remembers.** District state in the street, and
NPC reactions to how you look. Both exist for the same reason: a consequence
the player can only find on a summary screen is not a consequence they feel.

**And a sweep of everything I added last night**, prompted by finding that
`presence` had shipped as a number the character sheet printed and nothing
anywhere consumed, with a docstring claiming it fed "everything social". That
is this project's oldest bug class and I had written a fresh instance of it
while writing the check that is supposed to catch it.

The sweep found four more, all mine, all from the same session: a `gradient`
parameter with a docstring paragraph explaining what it did and no caller, an
`appearance.roll` that was never called because the command had an inline copy,
an `appearance.summary` nothing displayed, and `Event.flag` plus
`City.event_flags`, plumbing for events setting story flags where no event set
one and no thread read one.

Two of those became features (`roll` is now the one place that knows how to
roll a look; `summary` is on the character sheet). Two were deleted.
Speculative generality is the same bug as dead content wearing better clothes.

`check_dead_fields` is the standing version, walking the fields of eight
content records and requiring each to be read by attribute somewhere. Verified
by adding a dead field on purpose and watching it fail.

`validate.py` clean, `test.py` green at **6739 checks**. Both soaks clean, and
a scripted run played end to end: 41 ticks, trace 77, jacked out at the line,
residue 81 converting to heat 46 and a posted bounty a shift later.

### 2026-08-14 (a): the shell, and a bug that had made the game greyscale

**D38.** Terminal customisation as a cosmetic reward channel, at the author's
suggestion, and the framing that made it work was realising it should not live
in the save. The city takes the runner and does not get the shell.

**The find of the session was not the feature.** Measuring whether the new
palettes kept their roles apart turned up that no palette did, including the
shipped one, because `_to_256` was mapping almost everything to grey.

Its grey branch computed error as the distance from the colour's *average* to
the nearest step on the grey ramp, which asks "is this colour's brightness
close to a grey" and is true of every saturated colour there is. Pure cyan
scored a near-perfect grey match and won. `accent` rendered as index 248.

That is not a subtle wrongness. **The entire game rendered in greyscale for
anybody whose `TERM` says 256 and whose `COLORTERM` does not say truecolor**,
which is most terminals over ssh, most tmux sessions, and a lot of default
configurations. It had been true since the theme layer was written.

`check_palette_separation` is the standing version: every pair of roles in
every palette at least 20 apart in RGB *and* not quantising onto the same 256
index, with the four deliberate twins exempted, plus a direct assertion that
saturated probes never land on the grey ramp at all.

Three smaller ones, all found by looking at output rather than at code: the
palette swatches were written with role markup so every scheme in the list
rendered in the scheme already on and all eleven looked identical; the Bracket
prompt's sample rendered as `[1,200c] $` because `[marrow]` is valid tag
syntax and the parser ate it; and `rice --preview` could never fire because
the no-argument branch was tested first and a bare flag has no positionals.

`validate.py` clean, `test.py` green at **7476 checks**. Both soaks clean.

### 2026-08-15 (b): Guile buys something out here

**D48.** The thinnest attribute in the game, found by measuring rather than by
guessing: Guile was the only one with no derived stat, and every use of it was
inside a run. Cover is the derived stat, prices and legwork are the two city
sums that now read it, and resonance stays the one kind of legwork it buys
nothing in because listening to a network is not a conversation.

**The find was ten months older than the feature.** Cover changed nothing at
any value, because `decay_heat` rounded heat to an integer every shift. A
faction shedding 0.4 a shift shed `round(89.6) = 90` and never moved. Twelve
declared rates collapsed into four behaviours, and Carrion and Sixes heat had
been permanent since the day heat was written. It looked exactly like a gang
holding a grudge, which is why nobody caught it.

Heat is stored as a float now and rounded only where it is printed, so the
sheet still shows whole numbers and D14 is unbothered. `from_dict` nearly
undid the whole thing by coercing back to `int` on load, which would have
truncated a little of it on every autosave.

Three checks, one of them general: `check_heat` drives the real decay rather
than a copy of it and fails when two different declared rates cool in the same
number of shifts; `check_guile` requires all five `quote()` call sites to pass
a Guile, since a defaulted keyword argument is how a stat stops being read;
and a **dead-points** check caught the flat 18% haggle cap I had just written,
which made Guile 7, 8 and 9 points the sheet sells and nothing reads.

`soak7.py` is the campaign-shaped version: 30 long games, every faction
forgets, every campaign cooled, Guile 1 to 6 is 19% faster. It reports the
original bug as "carrion never forgets".

`validate.py` clean, `test.py` green at **12,849 checks**. All seven soaks
clean.
