---
tags:
  - flatline
  - project-plan
  - game
created: 2026-08-12
updated: 2026-09-06
---

# flatline: Build Plan and Progress Log

> Resumable build plan for **flatline**, a text-based cyberpunk intrusion game. **Read this file first** when picking the project back up. Every locked decision and every completed step is recorded here so work can pause and resume without re-deriving context.

> [!tip] Picking this back up: START HERE
> **State as of 2026-09-06: D182, the testers' first hour.** The first strangers played 1.0.1 and could not read it: nothing explained the sheet, the screen or the colours, the key/value lists read as wrapped prose, the prologue's last prompt printed its own markup, and the pixel pictures were ugly. D182 answers all of it on the release build: `legend` and `help colours`, a rule down every key/value grid, a gloss beside every number on `char`, question prompts rendered and fenced for readline, the tutorial turning itself on for the first runner on a profile with the step repeated under `now`, the words in place of the pictures (`rice render picture` brings them back), and tables allowed a hundred and twenty columns while prose stays at seventy-six. `validate.py` clean, `test.py` green at **20,356 checks** (`test_the_first_hour`, forty-five of them), the six campaigns clean. Counts that moved: 48 manual topics, 157 commands, 26 tutorial steps. **What is next:** the rest of the testers' notes as they come; the two follow-ups below are unchanged. The paragraph below is the state this was built on.
>
> **State as of 2026-09-05: version 1.0, tagged `v1.0` and public at github.com/SageSchiller/flatline under MIT, with `dist/flatline.pyz` on the release.** D1 to D181 are locked and the plan is current through all of them. `validate.py` clean, `test.py` green at **20,120 checks**, six campaigns and the two-hundred-shift life clean, every ending and both arcs reached by play. Counts (read off the code on 2026-09-05): 15 skills / 30 techniques, 33 traits, 12 origins, 14 icons, 58 implants, 13 weapons and 3 things to wear, 70 programs, 34 components, 14 drugs, 25 one of a kind, 28 ICE, 63 threads / 215 scenes / 208 decisions, 32 named people, 7 rivals, 204 events, 12 factions, 12 districts / 72 quarters / 60 places, 6 animals and 5 familiars, 28 record lines and 18 titles, 7 ambitions, 47 manual topics, 156 commands, 91 pieces of terminal across 9 axes. **What is next:** the author's own read-through of the prose, and the testers' notes; those become a fix pass and a `v1.0.1`. Two follow-ups are known and unbuilt: techniques that decide outcomes (a technique a network has not seen worth more than one it has), and the brief letting go of the verb after the tenth run against a target that remembers you. The paragraph below is the long day that got here.
>
> **State as of 2026-09-04, the long session (D133 to D179).** D133 to D143 landed first on top of the combat layer, all from the author's briefs and three rounds of play-testing, and the plan is current through all of them. First, the rest of the game met the fight (D133 to D136): street conditions, chem and traits that read a fighter, a clinic that patches a cut, the pit at Carrion's with a wall of names and a fixer's muscle work, and then the deck as a thing you live with in the city (mail, search, watch, message, ads) and a thing with a body (condition, reach, sweep, route, tune). Then the same method as D86 to D89 turned on all of it (D137 to D139): three play-tests of everything since D128 (a brawler, a netrunner who never throws a punch, a first-timer who does what `now` says), then three aimed at the deck and four at the fight and the pit, no crashes anywhere, nineteen fixes, and a balance simulation across the fighting routes with the measured take per shift written into `test_the_fight_under_pressure`. Then the story caught up with the street (D140, D141): rules that can read a skill, a rank in the pit, a habit, what you carry and what you have fought, eight new threads and three new people so that every gate in the game has fiction behind it, and `test_a_thread_for_every_way_of_working`, which fails the build if a system ships without a story. Last, against the Bartle axes, the two kinds of player the game had nothing for (D142, D143): `record`, twenty-four lines across the work, the city, the people and the floor that count things the engine actually writes, each crossing earning a name shown on `char`; and the main line paying off, the Deepwater palette gated behind finishing it, the city settling the water once and differently per ending, and *Afterwards*, the thread that hands the city back. Then the same method again (D144): an achiever playing for the record, the ending played three ways, and a fighter who ends on the main line; five campaigns, no crashes, every ending reached by play, and seven fixes, the largest being the posting that outlived its own ending and an afterwards that opened in the same breath as the offer. `validate.py` clean, `test.py` green at **18,991 checks**. Counts (read off the code on 2026-09-04): 15 skills / 30 techniques, 33 traits, 12 origins, 14 icons, 58 implants, 13 weapons and 3 things to wear, 70 programs, 34 components, 14 drugs, 25 one of a kind, 28 ICE, 63 threads / 215 scenes / 208 decisions, 32 named people with 129 topics, 7 rivals, 204 events, 12 factions, 12 districts / 72 quarters / 60 places, 24 street encounters, 5 names on the wall, 8 run conditions and 6 street nights, 28 record lines, 7 ambitions, 47 manual topics, 156 commands, 91 pieces of terminal across 9 axes. **The next thing worth doing is unchanged:** play it three ways with fresh briefs and fix what the players say. Nobody has yet played the under ending (read the log, consent to the archive, keep Lark alive), a chem habit through *Ninety*, or a campaign that lives on the deck's search and watches; and every play-test harness from here must set `XDG_DATA_HOME`. Then two more rounds the same day (D145, D146): six personas on the three corners nobody had reached by play (the fourth ending, retirement, a bond with another runner), no crashes, three fixes (a loadout dead-end that looped on a duplicate program, a partner bond that could not form, `market chrome`) and two confirmations (the under ending is complete, a death carried by the epilogue; retirement is sound); then four additions the round pointed at, a non-chrome path to the drift line, the posting's brief naming the route a network with no perimeter wants, the fence and the demonstrator introducing themselves through the work, and the README's counts held to the modules by `validate` so they cannot drift silently again. A regression of all nine personas on the fixed build is clean, and the partner bond and the hunted advice both visibly work now. Then the day kept going (D147 to D157): the walking answered (places and the district log), the hunt made visible (`rumours`, finds that sense), threads for the deck specialist and the reckoner, eighteen flavoured titles the player can pin with `called`, both kinds of pet (an animal kept at the safehouse that can be lost, a familiar that rides the deck and talks in runs, neither touching the work), `home`, and one more honest sweep that fixed five spine-shaped walls, the largest being `now` advising `drop` on the posting; and then five whole lives played through `campaign.py` (D158), which found the advice wrong in eight places, every one a loop a follower could not leave, and left four endings and a partner bond reached by play; then the five suggestions that round ended with, all built (D159): the street takes the money first, a quiet door out for a hunted runner with nothing, a follower fuzz in the suite that found its first stall on its first run, a run-craft persona that typed every technique and every origin verb, and three small text things; then (D160) the fuzz over every origin, each origin's verb held by state, toys for the animals, record lines for what you keep, and the quiet door caught by the regression opening too early and fixed; and (D161) the title for staying earned by turning the number, and four replies a band when you message a runner; then (D162) an ending never a stage's first answer, held by `validate`, *The Paper* on the other side of a bounty, and the six-campaign regression as one line; and (D163) `restore` recapping what matters and `now` naming the record line you are nearest; and (D164) the paper's collector named, the familiar's `done` and `home`, a `--long` follower, and the explorer's and socialiser's lists saying what is left; and (D165) the long follower's first two findings fixed and `who` with you on it; then the five design calls built (D166): told where to look, runners deciding about each other, the usurper on the wall, this life beside the profile, and a two-hundred-shift persona, which found (D167) the breaker advice buying what could never fit, fixed, and then lived to two hundred with the late game still deciding; then (D168) the stake brought down to fifteen thousand, a runner who asks you in, a watch `now` sets, and two scenes for the rivals' triangle; then (D169) the long wash, a bounty worked off, and the audit that holds every one of fifty-four threads open for the life it asks for; then (D170) the release checks a script can do: the 3.11 floor held, the pyz through a pty at three widths, every closing stage held, the door a distance on `home`; then the second arc (D171), *The Ninth Log*, about whichever runner the city chooses, with the first arc read back through the systems that came after it, and (D172) four subplots for the animal, the construct, the names and the door on three new rule kinds; then (D173) the retrofit the other way, three old threads closing on the partner and the name, a crew branch for the ninth log, the toy's scene and the wash's middle; and (D174) the partner as a clause the sentence can take either way; then (D175) the collector named inside the paper's scene, the record marking the profile's own line, and the origin threads played by play; then the second arc finishing clean on every branch (D176) and four long threads for the city at leisure (D177); and (D178) second scenes for the animal and the construct; then the one thing (D179): networks with memory, doors that stay cracked until patched, trails that teach them your techniques, routes and planted ways that persist and age, and a dossier on `render`. Tagged **v1.0** and made public on 2026-09-05. `test.py` green at **20,120**.
>
> **State as of 2026-09-01.** D86 to D89 landed in one session, from three play-tests run in parallel with three different briefs (a first-timer who does what `now` says, an explorer who ignores it, and a run specialist who types every verb by hand). What they found, in order of size: the story layer was gated on meeting people and nothing ever said to meet anyone, and forty-two scenes declared a district that nothing read; the advice could recommend the same severed run five nights running and never once name Intrusion; a credential warden was an unanswerable wall for the Chromed origin and the board could not see it; and D6's severed-connection cooldown had never been implemented. All fixed, with `test_people_are_the_story`, `test_night_before`, `test_wall_and_clock` and `test_remembered_inside` holding them. Two things were added rather than fixed: the construct that cut you loose is on the route next time, awake and named, and the other runners can turn up inside a network with consequences that read their opinion of you. `validate.py` clean, `test.py` green at **18,941 checks** (D90 to D114 followed on 2026-09-02 and 2026-09-03: the visual layer, from pictures and the drawn instrument through the schematic map, player icons, more palettes and prompts, the portrait, reveal styles, seen ICE with screen disruption, a glyph per host type across the scan, the map, and the node header, a full-colour city that the boot now comes up on, and the player icons redrawn as a bestiary of creatures and characters with four more to buy, and a story/quest play-test that fixed the first-runs signposting, and a cold-open first job, sharper run beats, an ambitions ladder, a blank-prompt lifeline for newcomers, a nemesis reckoning that gives the rival arc a payoff, the nemesis as a felt in-run obstacle racing you for the objective, and its mirror the partner who helps in the run offers to crew for good, and three ways into every job that make a build matter for the run itself, and a plantable backdoor that turns an in-run choice into an easier run later, and a faction-power layer with a `world` dashboard so a campaign visibly reshapes the city, and a swagger/legend layer that lets the player be good at it, and origin lifepath openings so who you started as reaches into your story, and two tactic tools, Shroud and Sledge, that each buy a verb the deck could not do before, and, unlocking the founding no-combat rule at the author's call, a street that can be fought (D128 to D132, 2026-09-03 and 2026-09-04): a fifteenth skill, an exchange in rounds with a netrunner's route through their chrome, a play-test that found the overworld safe by construction and gave districts danger of their own, twelve weapons in four styles, armour worn and fitted, chrome that fights, loot, a fighter's living in muscle work and fights that teach, a balance simulation across eight builds, and every help topic brought up to date with all of it). The next thing worth doing is another round of the same method: play it three ways and fix what the players say, because every one of the fourteen decisions since D75 came out of somebody playing rather than somebody guessing.
>
> **State as of 2026-08-21, end of the long session.** **Phases 0 through 5 are done, D17's finish line is passed, Phase 7 is closed, and D63 to D65 are the deep work.** `python3 validate.py` is clean with zero warnings, `python3 test.py` is green at **15,311 checks**, and `./build.sh` produces a `dist/flatline.pyz` that runs standalone. **D63, the mechanics deep dive** in six parts: every declared number and rider has a reader (`check_reads`); the intrusion layer's holes closed (`mask` decays, sealed records, armour wears, faction style knobs, soft wardens); the catalogue readable (`inspect`, a bare `load`, `fit`, passives once per kind, program riders, six mid-tier parts); the vices capped (Threes, collections, hook-4 warnings); twenty-four relics with histories; and programs held to skill rank plus two. **D64, the play test**: networks in six shapes by doctrine with the brief reading the sums; the city grown to twelve districts (the Stacks, Meridian Row, the Hall) with people, places, threads, events and relics; and the advice made into a chain that ends in a run, with seven dead ends closed and `test_advice` to keep them closed. **D65, the street is real**: encounters in four tiers answered by run, talk, pay or stand with printed checks; warning-then-lethal under the black-ICE contract; two street skills; `errands` (courier, watch, collect, escort); `arrange` to pay a faction for their streets; and the whole of it hooked into travel, rest and the close-call band. Before those, on the same day: D50 to D62, the onboarding layer, decisions that are read, the Deepwater spine, the city deeper, voices and hours, district arcs, the rival bond, the drawn map, the HUD, the tutorial's second half, run conditions, and the rest of the Phase 7 list.
>
> The whole loop closes. Create a character six ways, spend an attribute and experience budget, read a board that other runners are competing with you for, take a contract, travel, do legwork, hire somebody to come in with you, jack in, break into a procedurally generated network, do the job, get out. The residue you left becomes faction heat a shift later, sustained heat becomes a standing bounty, and a bounty makes that faction's districts genuinely dangerous to walk into.
>
> **What is not done:** nothing structural. Every system the plan set out to build is built, and the catalogue has had three passes (14 skills with 28 techniques, 29 traits, 38 chrome, 60 programs, 34 components, 12 drugs, 24 of all of those one of a kind, 14 street encounters, 28 ICE, 8 icons, 7 rivals, 18 NPCs, 18 story threads, 10 origins, 9 districts, 12 factions, 23 manual topics). More districts and origins are the obvious next content, but **the right way to choose is to play it and notice what is missing**, which nobody has done yet. Treat any further content added without play as a guess.
>
> **What this is.** A netrunner sim you play by typing at a fake terminal. Two layers: a persistent city that keeps score, and procedurally generated corporate networks you break into one contract at a time. The character system is classless and deep enough that two players at the same credit total play nothing alike.
>
> **The tone is grim.** Not cynical-cool: grim. The city does not care whether you live, the clinics are the best and worst thing in it, every piece of chrome costs you something you do not get back, and the only true death in the game is telegraphed and then absolute. Everything ships in that register or it does not ship.
>
> **This is a netrunning game with a street you can fight.** The whole of the *contract* layer is program against countermeasure, inside the net, through a deck: combat is a way to survive the street and never a way to do a job. From D2 to D127 there were no guns and no street fights at all; D128 (2026-09-03, the author's call) unlocked that half, and the rule that survives is the half above. Every encounter still offers the ways out that are not a fight, and nobody is ever made to fight. "Warfare" is the skill of attacking constructs, and a man's chrome is a construct with a person attached (`jack`).
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

### D49: The character is the address, not the slot

Reported as "I am loaded automatically into Jack", which was one symptom of
six problems sharing a cause: characters were addressed by *slot*, everybody
shared a slot called `default`, and nothing in the game ever showed the
player a list of who they had.

**The destructive one.** `new` refused while a character was loaded and told
you to pass `--force` to "abandon" them. `--force` did not abandon them. The
new character was made in the same slot and the next autosave wrote over the
old one, permanently, with no warning, because from the save layer's point of
view nothing unusual had happened. The word "abandon" reads as leaving
somebody behind. It meant deleting them.

Filing each character under a slot derived from their own handle is the whole
fix. `new` now saves whoever is loaded before making anybody, and nothing in
the game removes a character except `delete`, which prints what it is about
to throw away and then wants `--confirm`. `validate.py` walks the AST for
calls to `save.delete` outside `cmd_delete` and fails the build on any.

**The one that was wrong from the first line the player ever read.** The
splash said: `new` to make a character, `load` to continue one. `load` puts a
program on a deck. The command is `restore`, and it is called `restore`
*specifically* because of that collision, which is written down in its own
help text. So the game's opening sentence sent every new player to the wrong
verb, and by the time it printed, the game had usually already continued
somebody, which made the other half wrong as well.

That is a class, not an incident: **a verb the game offers has to work at the
moment it is offered.** The test drives `opening_line()` and
`nobody_loaded()`, pulls every backticked command out of what they return,
and asserts each one is `bare`, meaning usable with no character loaded. `load` is a
real command, so a check that only asked "does this resolve" would have
passed it.

**Boot behaviour.** One character is opened, because that is what remembering
is for. Several and no instruction means the roster is printed and nobody is
picked, because being handed the wrong runner is worse than one more word.
`--continue` takes the most recent, `--no-continue` opens nobody.

**And a character who is finished is finished.** `game.over` was set on
death, autosaved, and then read in exactly one place, so a flatlined runner
could stand up from the chair the game had just finished describing them
dying in and go shopping. D6 says only black ICE ends a character; it is not
much of an ending if it ends nothing. `AFTER_THE_END` is an allowlist rather
than a blocklist, because the failure modes are not symmetrical: a missing
entry means a dead character cannot read their own sheet, and a missing
blocklist entry means they can go back to work.

### D50: The shell answers an empty line, and creation is a conversation

The game was hard to start for anybody who had not played a command-line
game before, and the reasons were not depth, they were three small silences.
The splash ended at a bare prompt. `new` printed a hundred lines of origins
and then wanted `--origin <key>`, which is flag syntax shown to somebody who
has never seen a flag. And the shell had no answer to the one thing a lost
player actually does with a keyboard, which is press Enter.

D2 still holds and nothing here bends it: no panes, no cursor addressing, no
alternate screen. Strings in, strings out. What changed is that the stream
learned to ask and to answer.

**An empty line asks "what now".** `now` (also `next`, `hint`, `menu`) reads
the state and prints the one real thing to type next, with the reason, then
the handful of verbs that matter where you are standing. It is computed, not
authored: in the city it is the same `city_steps` the full `job` prints, in
a run it is `brief().steps`, so the one-line answer and the whole brief
cannot disagree. It costs nothing, works in both halves and before a
character exists, and a finished character gets it too, pointing elsewhere.
It is on the `help` landing page's "lost right now" list, and `validate.py`
holds it to the same rules as the rest of that list.

**`new` is three questions.** Which origin, from a table of ten that fits one
screen (`read 4` opens one in full, `read all` opens every one, `random`
lets the city pick); what to call them; and whether to spend the opening
points the way that origin usually would. Each answer is the next line
typed, the prompt is the question while it waits, an empty line backs out,
and `quit` is still quit. `new <handle> --origin <key|number>` does the same
in one line for anybody who has picked, `new <handle>` alone asks only the
other two, and `new --long` is the old full listing. The mechanism is
`Session.ask`: a pending `Question` whose handler gets the next line whole,
never split on `;`. It refuses to exist inside a run, because every prompt
style has to show the trace and a question cannot; scripts that trip one
have it dropped and are told to run the thing by hand; the tutorial waits
for a conversation to end before it advances, so no instruction ever prints
between a question and its answer.

**`spend` is a suggestion, not a build.** It reads the origin's attribute
shape, leans into it rather than sanding it flat, puts depth into the
skills the origin starts with up to the rank that changes what you can type,
then breadth across what the strong attributes govern, capped at three new
lines so it never buys six rank ones that unlock nothing. It shows the plan
and asks; `--go` skips the asking. It spends through the same `boost` and
`train` calls, caps every attribute below the ceiling because a maxed
attribute on day one is a choice somebody should make on purpose, and
`validate.py` proves for all ten origins that every step is legal when
taken, every attribute point goes, less than a rank two is left over, and at
least one technique is bought. It is never better than choosing yourself,
and the panel says so.

**Row numbers are names.** Every list the player is asked to pick from now
carries a `#` column, and the number works wherever the name did: `board 2`,
`take 2`, `buy 3`, `travel 1`, `switch 2`, `delete 2`, `--origin 4`. The
number means *the list as last printed*, remembered per kind on the session
(`Session.pick`), because the board moves between shifts and a number that
silently re-pointed at whatever was there now would accept jobs the player
never read. A row that has gone since says so and says to look again;
before any list was shown, the live order is used, which is what the player
would have seen had they looked.

**Smaller things that were silences.** A typo gets "did you mean" from
`difflib` over the verbs legal in context. Arriving anywhere, and `look`,
end with a `Here:` line that maps what the district *has* to the verb you
*type* for it, which is the gap between reading "workshop" on the map and
knowing the word is `repair`; `validate.py` requires every service in
`districts.SERVICES` to have one and every verb on it to exist. The splash
gives a first-timer three lines to start from instead of one sentence. The
board's footer, `job` with nothing accepted, the `jack in` closing line and
the tutorial's first step all say the same two things: the row number
works, and Enter says what to do next.

**What it does not do.** Nothing here touches a number. `test.py` plays the
conversation and the one-line form and gets the same character; the
suggestion is pure and the same origin gets the same plan twice; `now` is
read-only. There is no pager, no numbered menu that replaces a verb, and no
verb that acts on the player's behalf: `now` says `travel precinct`, it does
not travel. The depth is the point, and the point of this decision is only
that somebody can find it.

### D51: A decision must be read

Eighteen threads, thirty-nine scenes, forty-five decisions, and a grep that
found **none of the forty-five was read by anything outside
`threads.py`**. Offers, events, the board, the streets, the endings: nothing
looked. A choice printed good prose, set a string, and the world was
identical afterwards. That is this project's oldest bug class, content that
claims something the engine never does, living in the most human part of the
game, where the one reader with no way to tell is the player who just chose.

**The rule.** Every flag a choice sets, and nothing else sets (so it is a
decision and not merely a thing that happened), must be read by something
other than the ending, and must have a line in the ending. `check_consequences`
enforces both, and holds every story rule anywhere, in threads, events, NPC
presence, work, favours and counters, to naming a flag something sets.

**The readers**, all small, all data the validator can see:

- **Presence.** `Npc.requires` takes story rules now, evaluated by the world
  layer; `not:<flag>` is the one combinator, and it exists so that "Lark is
  alive" can be written. Lark leaves the Shambles when she dies. Mr Sunday
  stops appearing when the log runs.
- **Offers.** Work, favours and counters take `not:` too, so her work goes
  with her, Vance's cabinet closes once she is in the paper, and Mara's
  favours close when you asked what the favour was before you would do it.
  Five favours exist only because of a decision: the Blue Surgeon's eleven
  hours, Vance's referral and her staff rate, the Archivist reading the job
  from four hundred and seven logs, Mara paying somebody again.
- **Events.** `Event.requires`; forty-one consequences, each the city
  carrying on with what you did, happening to somebody else, weighted above
  weather so they arrive while the decision is still warm and penalised once
  seen so they never become a refrain. The tone budget (D34) still holds at
  55/34/11 with them in.
- **The streets.** `story.STREET_RIDERS`: being the Sixes' halves the
  Ninth's danger, a closed Nightwatch file halves the Precinct's, a returned
  laptop cuts Kagawa's. Read by `arrival_risk`, so travel and legwork feel it
  alike.
- **The board.** `contracts.PATRON_RIDERS`: the retainer triples Deepwater's
  postings, publishing removes them, Meridian remember who sold them the
  laptop and who sold Freeport the log.
- **The ending.** `legacy.ending` reads the spine: the retainer replaces the
  drift ending outright (there is no version of that arc that ends in being a
  person about it); refusing and publishing leave codas. And `EPILOGUE`: one
  line per decision, printed at retirement and at the flatline, under "what
  you left behind, in people". The flatline is the ending most players get
  and it used to forget everything but the numbers.
- **The bag.** `Choice.gives`: a choice whose prose hands you a component
  now hands it over. The courier had been carrying a present that did not
  exist.

**What it does not do.** Nothing here moves for somebody who decided
nothing: `test.py` advances two cities, one with the story handed in and
one without, and they draw the same board and the same weather. No thread
gained a scene; this is the layer underneath the scenes, and the reason the
scenes in Phase 7 will be worth writing.

### D52: The spine, and story inside runs

The game had eighteen storylines and no main one. The nearest thing was
Deepwater: five scenes, four ways in, an offer at the end, and the retire
door keyed to drift alone. This makes Deepwater the spine and gives the
story a way to happen where the game actually happens, which is inside a
network.

**The arc, in five acts, each with more than one way in.** *Hearing it*
(two runs, or the drawer, or Mara's favour, or the package). *Three facts*
(the Archivist's nine logs that do not end, Remnant's name, a Deepwater
network with no perimeter; Ozymandias will not say). *The posting*: a
contract through Mara with your handle on the record, against Deepwater's
own network, which does not expire and which nobody else will take. *What
you carried out*: your own log, longer than you have been running, with the
last entry dated the day after tomorrow; read it, give it to the Archivist,
or wipe it. *The offer*: take, refuse, publish, as before, reachable now
from the log alone or from the three facts together. And *the door*: it
asks, the way the Archivist asked, and it only asks somebody who saved
Lark, said yes to the archive, and read the entry for the day after
tomorrow. Go under, or say no. Four endings, and the fourth is reached only
through two other threads, which is what D31 was for.

**Story inside runs.** `Stage.posts` is a `Posting`: patron, target,
objective, title, blurb, the name of the record. Reaching the scene puts a
contract on the board through the ordinary generator and then bends it:
held (no expiry, rivals do not see it, it costs the board no slot), with
`label` on the objective asset so the brief, the node and the haul all call
it what the scene called it. Finishing it sets `did:<thread>.<stage>`, and
a later scene requires that, which is the difference between having done
the thing and having heard about it. `validate.check_spine` draws every
posting's network and requires something to read every `did:`, so a story
run nobody comes back from cannot ship. `_check_story` now also runs after
every shift spent, so a scene whose moment has come arrives when the world
moves rather than the next time you happen to look at somebody.

**The third exit.** `Choice.ends` finishes a character by a decision:
`end_character` prints the numbers the flatline prints, reads the decisions
back, leaves one thing from the flatline's list (the chair is still
occupied; nobody chose), and files them as `went under`. `Choice.drift`
exists because reading your own log to the end should leave a mark.

**What it turned up.** The ten origin threads were written with `\\n\\n`
and had been printing literal backslashes in every paragraph break since
the day they shipped; nobody had read one in the terminal. `test.py` now
refuses a backslash in any scene.

**What it does not do.** Deepwater is not explained, on purpose, and the
door is not a reward: it is a fourth ending and it goes under. Scenes still
surface only in the city; a run is still a run. Act four's choices have
their own readers (events, the board, the epilogue) under D51, and the
spine's four ending flags are the four Deepwater decisions, which
`validate.py` checks.

### D53: The city, deeper

Asked for a city that feels deep, dangerous and alive: gritty dark cyberpunk
with Pratchett-shaped, self-aware moments. The voice was already there (the
weather events, the footnotes, the rats' committee). What was thin was the
*ground*: a district was one fixed paragraph and a list of services, the
same paragraph at every hour, and nowhere inside it to stand. Danger below
an incident was one warning line. And `city.news` was written by the shift
tick, kept to forty lines, serialised, and read by nothing.

**Each district has a scene for each hour.** `districts.SCENES`: nine
districts by three shifts, two or three sentences each, printed by `look`
and on arrival in place of the city-wide shift scene. Marrow at night and
the Shambles at night are not the same night, and now they are not the same
paragraph.

**Places to stand in.** `content/spots.py`: twenty-seven places, two or
three a district, each with a scene, a night variant where the night is
different, and who you would usually find there. `look` lists them,
`visit <place>` (or its row) goes and stands in one for nothing, shows it at
this hour, and introduces whoever is there, which counts as meeting them,
so a scene that was waiting on `met:` arrives from the place. Texture, not
a menu: the verbs are the same verbs and the people are the same people.

**The street lets you know.** `fallout.close_call`: in the band below an
incident (danger 25 to 44), on a chance that climbs with the danger, the
street does something instead of printing a warning: somebody walks beside
you for eleven paces, a shutter comes down, your name is said to check how
it sounds. It costs three attention with that faction, which is the honest
cost of having been seen, and it is printed under a `noticed` rule so it
reads as an event and not as advice.

**`news`** (`wire`) reads the scrollback the city was already keeping and
nobody could see: who took what off the board, who posted a number against
your name, who died on whose job, what expired, what you sold.

**Fourteen more events**, in the same proportions: three grim, three wry,
eight absurd (the lift committee with no lift, the form for requesting a
form, the crane named by a vote with the losing name on the other side, the
queue with a constitution). Budget after: 52 / 31 / 17 against 50-70 /
20-35 / 10-20. Absurd was at the floor; it is now in the middle.

**What it does not do.** No NPC gained lines (seventeen people at three
lines each is the next place the city is thin, and it wants a pass of its
own, in seventeen voices). No scene happens inside a run. Nothing here
costs the player anything except a close call, and a close call is priced
like what it is. `validate.check_city_texture` requires every district to
have every hour, two to four places each, every place findable by its own
name with and without the article, and every close call to say where.

### D54: Seventeen voices, and hours

**The voice pass.** Every one of the seventeen people had three lines and
two topics, which is enough to be a character and not enough to be company:
`talk` repeated itself inside a shift. Each now has six lines and four or
five topics, written one person at a time in their own register, and
`validate.py` holds the floor at five and three. Ozymandias has found
loneliness among the eleven named conditions; the Man With The Board has
conceded, unusually quietly, that Deepwater is at least a large file.

**Hours.** `Npc.hours`: which shifts somebody is about, empty for always.
Mara is in the bar mornings and nights; Mr Sunday takes the stool
afternoons and nights; the Archivist, Sparrow and Tuck keep afternoons and
nights; the clinics and counters keep office hours; the machine and the
dark room keep none. The world layer filters presence by the clock; `look`
says who keeps other hours and which, once you have met them; `visit` says
when the person who is usually here will be; `who is` shows the hours. The
clock was a label on the prompt and a number in three formulas; it is now a
reason to be somewhere.

### D55: Nine threads rooted in a place

Every thread was about a person, and a district was where a person stood.
`content/arcs.py`: nine threads about the districts themselves, one each,
three scenes or so, a decision in every one, four of them putting a
contract on the board (D52): the pumps under the Ninth and the water
board's ledger; the queue outside the Marrow exchange asking you to be law;
the Vertical's review suite and eleven numbers; the aftercare ward and a
finger on the glass; a demonstration unit that would prefer not to be
reset; a vote at the west gate about you; the surplus counter selling your
own residue; Carrion wanting the Blue Surgeon's book taken rather than
shown; forty trays of tomatoes on a Kagawa landing and a schedule that is
a line in a table.

Twenty-two decisions, every one read (D51): the streets (the Ninth safer
once the pumps run on Sixes parts; Aoyama's ground worse once somebody
walked out of the ward), the board (Kagawa post less after Static ran the
DEFERRED column, Sendai post more once told what was on their floor,
Freeport either way), the Surgeon's favour closing if you took the ledger,
twenty-one events, and a line each in the epilogue. `validate` holds the
crossings symmetric, the postings generable, and each `did:` read. 27
threads, 67 scenes, 72 decisions; 132 events at 52/32/16.

**What it does not do.** The rivals. The plan said seven rival threads and
the rivals turned out to have an arc already (D44: bonds that latch,
declare themselves once, and act on the shift boundary). What they do not
have is a decision at the moment of latching, which is the next pass.

### D56: The other runners decide, and you answer; and the wire

**A say at the latch.** D44's bond latches and declares itself, and then
acts on you for the rest of the campaign, and you never got a word in. The
shift tick now writes `bond:<runner>:<kind>` into the story when a bond
crosses, and `arcs.RUNNER_THREAD` has fourteen scenes that read it: each of
the seven, on each side, in their own register. A partner says what the
machinery could mean and you work with them or keep it professional. A
nemesis names a figure, exactly fair, and you pay it or let it stand.
Twenty-eight decisions, every one read: a partner you said yes to charges
half to come in with you (`hire_price` reads `with_<key>`); a nemesis you
paid stops acting on the shift boundary (`bond_turn` reads `paid_<key>`);
four events, one per answer, gated on any of the seven; and a line each in
the epilogue, in the runner's name.

**The wire carries the story.** `city.news` was only ever what the shift
tick happened to say. A scene arriving is news now, a decision is news in
your own words, and what a run did to the city (heat arriving, posture
moving) is news, so `news` reads as a wire with more than one
correspondent.

### D57: The city, drawn, and walked

`map` drew a tree: true, dense, rooted at Marrow so it was the same shape
every time, and still not a picture anybody could hold in their head,
because a tree has one route into everything and the city has two into
most things. `citymap.draw` is the other half: nine districts laid out the
same way every time, the fourteen joins drawn, you marked `@`, the job `!`,
anywhere somebody wants you `x`, unwalked districts dim. The layout is
authored, because laying out a graph is a research problem and this one
has nine nodes that have not moved since the city was drawn; what
`validate.py` holds is that `MAP_EDGES` equals `districts.GRAPH` exactly,
so the picture cannot lie about the joins, and that it fits the column on
both rungs. The ASCII rung's `/` is also the character in `[/]`, which is
why every connector is dimmed at construction and not by a replace
afterwards.

**`walk <district>`** is `travel` repeated until you arrive: a shift a
step, each step a street you are walking into, stopping the moment a
street stops you, whether that is being picked up or a district you would
have to `--anyway` your way into. `City.walk_to`, which everything that
sends you somewhere hands over, now says `walk green` for more than one
shift and `travel green` for one, so the line the game gives you is one
line.

### D58: Large, and full of stuff

Asked for the city to feel large and full. The numbers, honestly counted
and printed under the map: nine districts, forty-five places to stand in,
twenty-two people worth finding, a hundred and fifty-four things the city
does when you are not looking.

**Eighteen more places** (the tap with a cup left on it, the generator
being tested for a landlord who is not paying for the diesel, the transit
gate with the scratched handle, the back bar with the chair nobody sits
in, the canteen on eleven, the campus edge where the landscaping stops,
the interface bar where the chairs talk to your deck, the tide wall with
the crown on the highest mark, the lost property office with the cloth,
the solvent yard, the night counter, the roof where the hum stops, the
water point with forty names on a rota for eleven thousand).

**The street.** `districts.STREET` and `street_line`: eight things per
district that might be in the street, three of them picked by the shift
and printed by `look` and on arrival. Deterministic and stream-free on
purpose, because looking must not move the world (D35): the same street
twice in one shift, a different one next shift.

**Five more people**, in full (six lines, three topics, hours, a place):
the woman in the green coat who keeps the queue and has never been inside;
the demonstrator who is better without the card and not paid to be; Teku,
who drives the crane named by the vote and painted the losing name on the
other side; the orderly who keeps the door's schedule and was a patient and
stayed; Halvard, who sells what came out of somebody and tells you whose.

**Eighteen more weather events**, two a district, and the budget holds at
52 / 33 / 15.

### D59: The readout

The prompt has carried the trace since D2, and D38 made that the one thing
no prompt style may drop. A new player does not read the prompt. They read
the last thing printed. So after anything that spends a tick inside a run,
the last thing printed is now one dim line: the trace as a bar, the noise
on this node, the tick, the alert. It is a readout and not advice: it says
where you are, `job` says what to do about it, and it costs nothing.

It is a seventh rice axis, `hud`, with four states all available from the
start (`line`, `bar`, `terse`, `quiet`), because it is a preference about
how much the stream tells you and not a reward, and because the catalogue's
own rule is that an axis with fewer than four options is not a choice. It
lives in meta with the rest of the shell, so it survives a flatline like
everything else that is the player's. `Session.hud` caches it so an action
does not read the meta file. Nothing here touches a number: the prompt
carries the trace whichever state you choose, and `validate.py` still
holds every prompt style to that.

### D60: The tutorial goes past the door

Sixteen steps took a new player from `new` to `jack out`, and stopped. The
thesis of the game is what happens after the door, and the one reader with
no way to tell the tutorial was incomplete was the person reading it.

Nine more steps, on the same mechanism (an instruction, a reason, a
condition checked after every command, a payoff): spend a shift and watch
the residue land; `rep`; `look`, and the hour, the street, the people and
the places it shows; `talk` and `who is`, because talking is how threads
start; `visit`; `journal`, and `choose`; Enter on an empty line, which is
the answer to being lost; `retire`, so the door is discovered at the start
of the campaign and not by accident at the end; and a second contract,
because the second run is the one where the city remembers the first. The
closing points at `map`, `walk` and `news` as well as the manual.

The conditions stay total and cheap, `validate.py` still runs every one
against an empty session, and the second half arrives for anybody who
asks for the tutorial late: the first half is satisfied by having played,
and the tutorial starts at the first step that is not.

### D61: Tonight, inside

A network has a posture, which is how hard it is, and a shape, which is who
built it (D19). It now has a third thing: a **condition**, drawn when you
jack in, announced at the door with its numbers, shown on `status` for the
rest of the run. About one night in two. Eight of them: a maintenance
window, an audit in progress, lockdown, another runner inside, dead hours,
a carrier storm, a security exercise, a skeleton crew.

**Every field is read.** `content/conditions.py` declares multipliers on
trace, noise, residue and pay, an offset on the noise a countermeasure
needs to wake, an offset on every crack check, the verbs that cost a tick
more tonight, and whether somebody else is in here making noise; `RunState`
reads each of them in the one place it applies (`add_trace`, `make_noise`,
`leave_residue`, `wake_threshold`, `_ghost_tick`, `_act`, `crack_check`,
the fee); `check_dead_fields` walks the record like the others, and
`check_conditions` refuses a condition that changes nothing, a multiplier
outside 0.5 to 2, an offset that is a cliff, or a slowed verb that is not a
run verb that costs ticks.

**No hidden dice.** The condition that touches a check is a named term in
the sum, so `odds` prints it. The numbers are printed at the door and on
`status`. It is weather, not difficulty: the same network is a different
run on a different night, which is the reason a fifth run against Kagawa is
not the fourth, and the reason legwork cannot tell you everything.

**Its own stream.** `Rng.fork('condition', cid)`, declared like the others
(D3), and never the network stream: legwork regenerates a network to read
it, and a draw taken from that stream would have made the network it read
a different network from the one you ran. `help conditions` is the page.

### D62: The rest of the list

The remaining Phase 7 items, each small, each a surface the game already
had that was not saying what it knew.

- **The journal is a log.** What is waiting on you comes first; under each
  thread, what you decided; in the full read, each decision under its scene
  with what it cost, derived from the flags (`Story.decided`) rather than
  stored, because the flags are the layer.
- **Previously.** Five rows when a character is continued, switched to or
  restored: where and when, the job, who is hottest, what is open and what
  is waiting, the last thing the wire said. A save is a place, and nobody
  remembers a place they left a week ago well enough to stand back up in
  it.
- **`odds` for more.** `odds strike <ice>` prints the strike sum and what a
  hit takes off (the sum is one function now, `strike_check`, used by both
  the verb and the question). `odds <any verb>` prints what that verb costs
  tonight: ticks, noise here, residue here, with chrome and the condition in
  the numbers, the same sums `_act` does, before it does them.
- **ICE portraits.** `ice.PORTRAITS`: a three-row mark per behaviour, both
  rungs, printed once beside a construct's name the first time it wakes and
  you know what it is. After five runs the shape says "warden" before the
  word does. `check_portraits` holds every behaviour to having one.
- **Attribute bars and a build label.** Five lengths beside five numbers on
  `char`, and `plays as`: the skill you have most of and the attribute,
  "wired" with the drift. It reads the build and nothing reads it back.
- **The card.** `Console.box`, the one framed thing in the game, for the
  one moment that is a result rather than a stream: the end-of-run numbers
  with the trace sparkline, titled with the outcome.
- **Scripts discoverable.** `now` names the empty library once Daemonology
  2 opens it.
- **Naming things.** `deck name <what you call it>` and `safehouse name
  <what you call it>`. Cosmetic, persisted, on every screen that mentions
  them.

### D63: The mechanics read back

A deep dive on the numbers themselves, asked for on 2026-08-21: stats,
hacking, gear, drugs, all of it, made to make sense, with nothing thin or
unread, and balance corrected where it was off. Four audits were run over
the source first (gear and market; stats, skills, checks and chrome; vices
and money; ICE, generation and the verb economy), and the same finding came
back from all four in different clothes: **the game was declaring numbers
the engine never read.** Tempo was printed on the sheet, sold by three
implants, two traits and a drug, and consumed by nothing; `evade_bonus` was
sold eleven times and read zero; `heat_mult` and `rep_mult` the same; a
Blacksite Stack's three memory and a Coolant Mesh's four heat cap never
reached the deck, nor did any bench mod's; four chrome riders (misfire,
the Nightwatch serial, dual thread, the deadman) were names with no code
under them; a Static Line high declared a rider only the Psyche technique
set; Architecture and Sabotage had no reads outside their techniques;
Impersonate said ICE would ignore you and ICE did not; Sidechannel was
three silent ticks that opened everything; Script's "one tick less" was
not there; `tell_lead` only decided whether the tell was named; and a
`tick_mult` of 0.95, the two cheapest upgrades in the catalogue, rounded
away on every one-, two- and three-tick verb, so the Standard Core and the
Standard Bus were cosmetic.

**(a) Every number reads.** Landed as one pass with one rule: a declared
number or rider gets a reader, and the reader does what the declaration
says.

- **The deck budget hears the body.** `Deck.extra`, set by
  `Character.refresh_deck` from chrome, traits, origin and icon (never
  programs, never chemistry), and `_component_effects` now merges bench
  work. Memory and cooling from anywhere count.
- **Tempo banks free actions.** `TEMPO_RATE`: at 2, a third of a verb per
  real tick; at 3, half. A whole one pays for the next verb. `status` has a
  `banked` row that sums tempo, the tick bank, overclock credit and free
  actions.
- **The tick bank.** `advance` banks the fraction a multiplier is worth
  instead of rounding it; a whole tick saved is a free verb, a whole tick
  owed is charged. 0.95 is now a tick back every twentieth tick, exactly.
- **Evade is a printed check.** A hunter or black construct lunges:
  `reflex + stealth + evade gear` against `rating x 2 + 4`, itemised like
  every other check (D14). Succeed and it closes on where you were.
- **`heat_mult` and `rep_mult`** read where the residue becomes heat
  (`City.apply_run`) and where the patron pays standing (`pay_out`).
- **Riders.** Misfire: the third action in a tick has a one-in-three chance
  of costing the tick anyway. Nightwatch serial: a tier opened at the door
  of a Nightwatch network and taken back, with an extra alert level, the
  first time something files on you. Dual thread: the second-best breaker
  rides every crack at its rating (a second copy of the same breaker
  counts, which is what a spare is for). Deadman: below 35% Integrity the
  grip severs the run and you live. Dissociated (Static Line): feedback
  lands on the deck. Mirror: a daemon under a Mirror icon hesitates one
  tick in four. The six origin passives that were keyed on the origin name
  now read their riders; two riders that only duplicated an effect
  (`salvager`, `company_hardware`) are gone.
- **Skills.** Architecture adds a hop of scan reach per two ranks.
  Sabotage is the skill for `corrupt` and for `wipe`, both of which are
  checks now (`push_check`, `wipe_check`); wipe spends the payload the door
  demanded and fails loudly. Sidechannel is a Cryptography check against
  the hardest thing on the host. Impersonate is enforced in `_ice_tick`
  for everything that checks reasons; black ICE checks nothing. Script
  banks one tick. `tell_lead` holds the strike back a tick per point.
- **The room turning is a Composure check.** At red and lockdown,
  `composure + nerve` against 12; fail and you freeze for a tick. Nerve
  was read once, at the moment of dying.
- **Small honesties.** A construct acting is a noise on its host
  (`IceType.noise` was read by nothing); an awake Auditor multiplies the
  residue left there; the first black tell of a run says what it is and
  what to do; `scan --quiet` reaches for the quietest hunter; payloads
  carry `jobs` and one not built for the objective is `-3` and louder, said
  at the door; the resonance line prints for resonance and not for
  everything else.
- **The guard.** `validate.check_reads`: every key in the effects
  vocabulary and every rider any catalogue can set must appear, quoted,
  somewhere that is not content; and no attribute may govern fewer than
  two skills. One dead vocabulary key (`actions_first_tick`) went.
  `test_reads` drives each of the above.

**(b) The intrusion layer.** The audit's findings, closed one by one.

- **`mask` wears thin.** Each use tonight is worth three quarters of the
  last (`MASK_DECAY`), and nothing a mask does takes the trace below half
  of what the clock alone has put there (`MASK_FLOOR`). It was a loop: a
  rating-3 mask on a quiet host reset the only clock in the game forever.
- **Sealed records.** The decrypt is a fifth of posture plus five (it was a
  quarter plus six: a Kagawa vault was impossible without Cryptography and
  nothing said so). `pull --sealed` takes a record shut for 40% of nominal
  and 55% of the fee; the door says the record is sealed and what opens it;
  the brief says it on the host; the patron says why the fee is short.
- **Armour wears.** An armour program is good for as many saves a run as
  its rating, and then it is gone from the deck and the bag. Bulwark's note
  said this for two years; now Sump's does too.
- **No borrowed black ICE.** Seven factions have no lethal construct; the
  generator used to hand them everybody else's. A Sixes vault gets a hunter.
- **Riders that do something.** Verger, Psalm and Stringer escalate by two
  (one was the default, so the declared effect changed nothing; `check_ice`
  holds the rule). Gallows cuts a route, as its strike line always said.
- **The herder herds.** `RunState.previous` is the host you came from, and
  `_cut_route` closes the edges behind you first.
- **Doctrine is numbers.** `Faction.style`, eleven knobs (`STYLE_KEYS`:
  density, probes, hunters, traps, herders, black, wardens, vaults, crypto,
  damage, residue), read by the generator and by the run: Meridian is
  empty and hard-keyed, Carrion is studded with traps, Aoyama has many
  small vaults, Sendai hits harder and is sparse, Nightwatch is watched
  rather than defended, Freeport logs everything, Deepwater closes routes
  and has no boundaries. `style_line` puts the phrase beside the doctrine
  on the contract. `check_factions` holds keys to the vocabulary and the
  vocabulary to being used.
- **The open route is soft.** `_soften_route`: on the one route
  `_ensure_passable` guarantees, credential wardens are capped at rating 4,
  so a Handshake answers them; off that route they keep their rating.
- **An escort job always has an escort.** When nobody on the roster works
  for the patron, the patron sends somebody you have never heard of.
- **Non-lethal hits scale.** Two deck levels at and above damage 6, after
  armour, so a Coroner and a Kestrel are different constructs. (Landed in
  (a).)

**(c) The catalogue, and what a player can learn about it.**

- **`inspect <thing>`** (also `examine`, `what`, a row number from the last
  market or bag list, and `help <exact name>` falls through to it): the
  blurb, the numbers it gives and the numbers it takes under two headings,
  the signature as a word (silent, near silent, quiet, ordinary, loud,
  deafening), the note or the drawback, and where it is for you: loaded,
  in the bag, fitted, in you, for sale here and at what. The market used
  to print a category and a rating beside a four-figure price and the
  blurb was shown nowhere. The market column now carries the signature.
- **A bare `load` lists the bag**, numbered, with memory, rating, signature
  and whether it is loaded, fits, or will not; `load 2` works. It used to
  be an error.
- **`fit <component>`** in the city: a spare in the bag goes in and the
  old part comes out. Until now only `hotswap` at Hardware 4 could, and
  only mid-run. `sell` takes components.
- **Passives count once per kind.** `Deck.passives`: the strongest loaded
  program of each category contributes its passive effects and the rest
  do not. Six armours were a damage reduction of 0.07; Mirrorbox's note
  about stacking poorly was a wish and is now the rule.
- **Program riders** (`Program.rider`, `RIDERS`, `Deck.riders` folded into
  `Character.riders`): Shrike bites double against rating 3 and under and
  not at all against 6 and up; Banshee escalates the alert on every
  strike; Ledgerhand, Tidemark and Dowser each add a column to `scan`
  (worth, traffic, boundary). Their notes always said so.
- **Honest notes.** Forgers say what `pretext` does rather than "grants
  tier-1 access"; Glacier no longer refuses daemons it never refused;
  Needle and Copper say what they are; payload notes say what they are
  built for.
- **The hardware catalogue.** A mid-tier part in every slot (Refitted
  Core, Stacked Bank, Coax Trunk, Cold Block, Foil Wrap, Window Dish) in
  the 1,500c to 3,600c gap nothing sat in; Hardline Only costs a legwork
  point (you hear nothing of the city on the wire), so the free antenna
  is a trade and the Short Whip is not a strict downgrade; Longwire is two
  legwork. Anodyne is two memory at 6,900c; Skeleton is 5,200c.

**(d) The vices and the money.**

- **Threes has a ceiling.** The stake is a term (`THREES_PER_STAKE`: a
  point of resistance per 1,500c, eight at the cap) and the table learns
  faster (a point per 6,000c taken, to six). A Guile 8 specialist used to
  read every table at a hundred percent at the cap, which was an income
  with a floor; now they take a few good evenings off each table and then
  that table is closed to them.
- **Collections outpace interest for every lender.** `Debt.collect` takes
  the larger of a quarter and `rate x 6 x 1.2`: Carrion at 6.2% a shift
  outgrew a quarter every six shifts, which made the help text's promise
  that debt is survivable false for exactly the lender a desperate
  character ends up with.
- **A first dose of a hook-4 drug asks.** `dose grave_salt` says one dose
  is a habit and wants `--sure`; the only warning used to arrive with the
  habit. Ash Tea names each comedown it cleared and the habit it moved,
  and `chem` says the cure is the habit. `help chemistry` says Focus is
  counted at the door.
- **The Switchboard has a floor.** 1,200c, what a payload costs: the one
  person who needed an advance was the one they offered nothing, and the
  offer text now says what the number is and why.

**(e) The relics: things there is one of.** Asked for in the same breath:
special items, unique, with their own backstories, hard to get or found in
an unexpected way, to reward exploration.

- **`unique` and `lore`** on every catalogue dataclass. A relic is never
  merchandise (`market._catalogue` and the back room both skip it), and
  `inspect` prints its history under its numbers with "one of a kind".
- **`spots.Find`**: a relic at a place, at an hour, once the story rules
  hold, once per character ever (`found:<item>` flag, a rule kind). `visit`
  hands it over with a moment of text and a wire line; `give_item` puts a
  drug in the stash and everything else in the bag, for finds and for
  `Choice.gives` alike. Nine finds: the Survey in the generator shed (met
  Tuck, two runs), Thessaly under the transit rail at night (six runs),
  Pike at the cranes in the morning (met Old Pike, eight runs), Remnant's
  Graft in the dark room at night (Deepwater's name, Dissonance 30), What
  Came Out of Lark in the crate (Lark dead), the Aftercare Bead at the
  dispensary (met the orderly, Aoyama standing), A Wet Cloth at the stalls
  (you taught Sparrow), Formula No. 0 from the machine at night (met it,
  four runs), Surgeon's Own at the clinic (Lark saved, the Surgeon owed).
- **Six given by decisions**: Four-Oh-Six for consenting to the archive,
  The Log for reading it, Samizdat for publishing it, Mara's Landline for
  the favour, Nobody for working with the Quiet Kid, The Desk for working
  with Grieve (`arcs.PARTNER_GIFTS`).
- **Rumours.** One ambient event per find (`events.RUMOURS`, built from the
  finds), in the district the thing is in, that stops the moment it is
  found; it is weather until then, so a character who decided nothing still
  hears it. The tone budget holds (five grim, four wry and absurd).
- **Each one does something nothing on a shelf does and costs something:**
  Thessaly signs its work (residue x1.2); Nobody takes the credit with the
  trace (rep x0.85); The Desk is somebody real answering (heat x1.1); The
  Log is heavy (composure -2); Remnant's Graft does not drift (Dissonance
  1) and costs a point of Focus; Lark's piece takes two Integrity; the
  bead reports; the cloth is a wet cloth; the landline rings.
- **`check_relics`**: at least twelve; each given by exactly one route;
  two hundred characters of history; never rolled by any market or any
  counter; every find names a unique thing, an hour that exists, rules the
  story can evaluate, a moment, a rumour in a tone; `found:` read only
  through a rumour's `not:`. `check_consequences` counts a find as a reader
  of the decisions it waits on. `help relics`.


### D64: The play test

The author's first session, 2026-08-21, and what it turned up. Each part is
small and each is a thing a new player ran into.

**(a) Networks have shapes.** `Network.shape`, one of six (`SHAPES`:
layered, spine, ring, hub, mesh, split), drawn by doctrine
(`SHAPE_WEIGHTS` by faction kind, `SHAPE_BY_FACTION` overrides: a Sixes
phone tree is a hub, Aoyama splits into wings, Meridian is a spine,
Deepwater a mesh), built into the edges by `_wire`. Named on `map` once
three hosts are known and in topology legwork. Two things the shapes
shook loose: the brief now reads the same sums the verbs do and says when
a wipe or a push cannot land tonight (and points a sealed record at
`--sealed`) instead of advising the same verb forever; and the wipe sum
is a sixth of posture plus three, which a Kindling at a gang's posture
can meet.

**(b) The city grows.** Three districts, because the map felt small and
because three factions had networks and no street: **The Stacks**
(Static's presses and relay shacks under the Terraces' water towers; a
list of names read out at the top of every hour that nobody will say the
source of), **Meridian Row** (the banks: stone, glass, silence, a counter
hall with one Notary and a ledger with a very long line in it) and **The
Hall** (the old interchange the Chorus took when the trains stopped: soup,
singing, a clinic that does not ask, Carrion standing at the back of the
queue). Each has three scenes, seven street lines, three places, and a
thread with a decision the world reads back: the stop list (print, hold,
sell), the Meridian key (return, keep, give to the Stacks: keeping it is a
relic, a forger that is not an argument but the thing the argument is
about), the tin (stand with the Hall, take Carrion's money, walk away; both
of the first two post a run). Four people (Ines Vale who runs the presses,
Pip who climbs the towers, the Notary, the Cantor), with work, stock and a
favour between them. Fifteen events: six weather, nine consequences. The
map is redrawn for twelve and the walk rule is four shifts corner to
corner, because a bigger city takes longer to cross.

### D65: The street is real

The author's direction, 2026-08-21: the game should be split evenly between
the danger of being jacked in and the danger of the physical world, with
real harm and real skill out there; the idea that nothing can end you
unless you are jacked in works against the setting. So the street is real.

**What stays.** No guns in your hands, no street fights, no combat verbs:
the locked direction holds. You do not fight the street. You survive it the
way people who live here do: you run, you talk, you pay, or you stand there
and take it.

**Encounters** (`content/street.py`, `world/street.py`). A ladder of four
tiers: a lean (two on a kerb naming a price; somebody behind you), a press
(three in a doorway with a photograph; kids with a knife; a dark
stairwell), a taking (four and a van), and the kind that kills (people who
have stopped asking; somebody you crossed). Somebody's people, filled with
the faction, or nobody's. Each is a `Question` (D50) with `must_answer`:
the answers are printed with their odds, an empty line is standing there,
and each checked answer is a printed sum like every other check in the
game (Reflex, Fieldcraft x2, Streetcraft to run; Guile, Streetcraft x2,
Subterfuge to talk; Grit, Fieldcraft x2, Nerve to stand; money to pay).
Outcomes land on Integrity (the same number the net spends), credits,
heat, the deck, and the marks.

**The warning rule.** Only tier 4 can kill, and only after a warning: the
first time a lethal blow would land it leaves you at one Integrity and
sets `warned:<faction>` with the sentence "next time they will not be
asking"; with the flag set, the next one can end the character (`killed in
the street`, the flatline's epilogue and bequests, a roster line). Same
contract as black ICE (D6): telegraphed, then absolute. Non-lethal
outcomes cannot kill, whatever the dice.

**Where it happens.** The incident roll at travel is an encounter three
times in five (the old ladder stays for the rest); the close-call band
below it gets a small thing in the street sometimes (the tail, the woman
with a pot, who heals you two); a rough night's rest somewhere dangerous
without a safehouse; a watch errand. Never inside a run.

**Two skills** (fourteen lines now): Streetcraft (Guile: Bolt at 2 leaves
before it starts, once a day, not from the top rung; A Face at 4 makes
talking four easier and paying half) and Fieldcraft (Grit: Scar Tissue at
2 heals a point more per shift of rest, two somewhere safe; Shrug at 4
halves the first hit). `check_street` holds every technique key to a
`has_technique` reader and every encounter to the ladder's rules.

**Errands.** `errands`: two pieces of street work per district per shift,
deterministic in (district, shift): carry a package one to three shifts
away and get paid on arrival (a warm one is worth stopping you for), or
stand a shift on watch somewhere here. No deck, no trace, the street in the
way. `now` carries the package; the wire remembers it.

`help street`; the death topic's ladder has the street on it.

**Arrangements.** `arrange <faction>`: pay a faction to have their people
told. While it stands their streets are twenty-five easier, the people who
stop you lean rather than take (tier capped at two), and the number (base
300c plus six per point of heat and ten per point of bounty) comes round
every six shifts from the account; a payment you cannot make ends it with
heat, because they remember who ended it; past a bounty of sixty there is
no arrangement, because they want the number. `rep` lists what stands and
who has warned you.

**(c) The advice is a chain that ends in a run.** An economy soak (a
character that does exactly what `now` says, forty seeds, four hundred
commands) found the loop the author hit and three more behind it: `now`
said `market program` to somebody who could not afford one, for ever; then
`buy` was not named, so the shop was the answer and never the purchase;
then `load` was named with no memory free, and the deck refused it every
time in silence; then a fresh runner with twelve unspent experience took
whatever was first on the board and lost every run. So: the unspent budget
is the first step there is, and it stays a step after a job is taken;
short of money, the step is the best-paying errand, named, and `borrow`;
with money, the step is `buy <name>` when it is on the shelf here and the
walk to the nearest market when it is not; with no room, the step is
`unload <the least of what is on the deck>`, named; and with nothing
accepted, the step is `take <cid>` for the softest thing on the board the
kit can do, posture said out loud, a shop trip counted as twelve posture
rather than as a wall. And `_ensure_ladder`: a network whose objective is
tier two or deeper always has an auth server at tier one, because the only
route up is a full crack of one and a network whose only auth sat at tier
two had no ladder at all; `_tier_steps` will now name an auth one rung
above you, which is three points and a decision, rather than none.

Three more dead ends, found by running a whole campaign the same way: a
`spend` that refuses ("nothing the shape suggests") while `now` goes on
recommending it, which is now impossible in both directions (the planner
falls back to any affordable rank anywhere, and the advice checks the plan
exists before naming `spend`); a `travel` the street refuses because
somebody is paying to find you there, where the advice now says `arrange`
if you can pay for the streets and `rest 3` if you cannot, and names
`--anyway` as the third way; and the same check reading only the first
token of a `walk`, so a two-hop route through a district that wanted you
was recommended for ever. `test_advice` holds all of it: every step the
advice names is a command the shell knows, says why, and is not a walk
into a district above the incident floor.

### D66: Size, the clock, and the fee

The author asked whether networks should be authored or random, unique to
the group, and larger and more complicated as the money goes up. The answer
to the first is that they already are both, and should stay both: authored
zones and shapes, random fill. The rest was measured rather than argued,
by running two dozen networks per band with the same build and counting.

**What the measurement said.** A large job at corporate posture finished
nought times in twenty-four. Successful runs finished at trace 67 to 90 out
of a hundred, so there was no margin anywhere, and 17 to 21 of every 24
failures were the trace filling. Size was doing one thing only: adding a
fifth of the run to the walk. And a corporate job paid half again what a
gang job paid while finishing about a third as often, which meant the board
was quietly telling every player to stay in the Ninth for ever.

**Size is breadth** (`SIZE_REACH`). A bigger contract widens the front
(perimeter and interior scale fully with it) and barely deepens the back
(restricted at two fifths, core not at all). More ways in, more hosts that
are not the job, more to carry out; the same number of hops to the thing
you came for. Depth is a countdown; breadth is choices. A fourth size,
`1.7`, is a sprawl.

**The size is cover** (`Network.crowd`). Trace per tick scales with how
much traffic there is to be lost in: a twenty-host network runs the clock
about a fifth slower than an eight-host one. The manual has said for
months that ten thousand legitimate sessions is the best mask money cannot
buy; this is the number under it.

**The clock reads what you do** (`IDLE_TRACE`). `TRACE_PER_TICK` has always
carried a comment saying the pressure should come from what the player does
rather than from the clock alone, and the clock was flat, which made it
exactly the opposite. A working tick costs 1.1 and a quiet one 0.45, which
is what makes `ghost`, `sidechannel`, `--quiet` and the new `wait` worth
the time they cost.

**The room can be won back** (`COOL_AFTER`, `QUIET_TO_COOL`, `cool()`).
Alert only ever went up, so one bad break in the first five ticks decided
the other thirty at one and seven tenths. Now a ticket nobody adds to ages
out after nine ticks, and six consecutive silent ticks do it too; every
escalation resets both. `wait` is the verb that buys silence with the only
currency a run has.

**The fee reads the difficulty** (`PAY_BASE`, `PAY_PIVOT`, `PAY_CURVE`,
`SIZE_PAY`). The old linear rate is a curve now: a gang job is about 1,600c,
a corporate one about 3,200c, a Meridian sprawl about 10,000c. Size pays
0.82 / 1.0 / 1.5 / 2.1 rather than 0.8 / 1.0 / 1.25.

**And the board says so before you take it.** `board <id>` carries the size
in words, and a `reads as` line pricing the target's middling services
against the breaker you are carrying with the same sum `crack_check` uses:
comfortable, workable, even money, long odds, out of your league.

### D67: The city is a place, and the difficulty is a ladder

Two things the author asked for on 2026-08-22: the city should feel
overwhelming and sprawling rather than thin, and the districts should each
be somewhere, from the flooded blocks the gangs run to the glass the banks
sit behind.

**Every district is a place now.** Four new fields on `District`, written
for all twelve: `scale` (how big it is, in the terms the place itself uses:
forty thousand people, ninety floors, eleven cranes of which nine move),
`built` (what it is made of and what that does to standing in it),
`works` (what the people here do for money and who takes a cut), and
`beyond` (what is past its edge, because the city does not stop at the
map). Plus `quarters`: six named corners each, seventy-two in all, most of
which you will never visit, which is most of what makes a place feel like
it goes on.

**`look` says how big it is and what its parts are called.** **`district`**
(also `here`, `place`) is the long read, from anywhere: the scale, what it
is made of, what it does, the quarters, what is past the edge, who holds
it, who else has people in it, what it sells and at what tier, and the
walk. Sixty more things in the street, to thirteen a district, with a
validate rule against two lines being the same thing twice.

**Twenty written crossings.** Every road between two districts has what is
on it: the freight ramp out of the Ninth, the boulevard nobody walks down
that the Vertical is at the end of, the two streets where the noise stops
and the Row starts. Travel prints one. A shift of walking is somewhere you
went through rather than a number going up.

**The map says why the city is that shape** (`citymap.LAYOUT`): water west
and south, the hill north with the towers on it, Marrow in the middle
because a market goes where the roads cross, the new money east.

**And the difficulty is a ladder rather than a wall.** Measuring the first
job in the game found the early-game trap the author had been feeling: a
gang's vault ran the same signing service as a bank's, because the service
scale was 0.7 + 0.6 x posture/50, which comes out at 0.96 for the Sixes.
A starting deck could not open the thing it had been sent for, anywhere,
at any posture, and the brief kept telling it to try. Now the curve is
0.45 + 0.78 x scale, so a phone tree with delusions is one, and a bank is
a bank. The brief will not name a door under `HOPELESS` (one in six), and
when there is nothing to try it says what would change that: a better
program, or the rank to drive one.

Measured after, twenty-four networks a band: a mid build takes 17 to 21 of
24 gang jobs and 3 to 9 corporate ones; an end-game build takes 21 of 24 at
Kagawa, 24 of 24 at Meridian and 20 of 24 at Deepwater. That is a ladder.

**And each lot builds differently, structurally** (`network.SIGNATURES`,
six of them, named on the contract screen under `their way`). Deepwater has
no perimeter: the front of the network is not there and you arrive already
inside it. Freeport is audited in public, so the whole topology is known
from the first tick and seeing it is not the same as walking it. Static
mirror everything, so the thing you came for exists twice and the copy
counts. Meridian seal the objective, always, because the keys are the only
thing they guard. A Chorus construct you have seen wake never goes back to
sleep. Nightwatch send somebody: once a run, when the room turns red,
something arrives on the host you are standing on that did not come up
through the network. `check_factions` holds every declared signature to
being acted on somewhere outside content.

### D69: Breadth, so experimenting is worth it

A catalogue audit against the playstyles found the holes, and they were not
where the eye would have guessed. **Daemonology had no tier-one program at
all**, which meant the four districts that stock only tier one could never
sell one and the whole automation arc was unreachable from the Ninth.
**Streetcraft and fieldcraft had no gear whatsoever**, one trait apiece.
Four declared effect keys (`skill_subterfuge`, `skill_stealth`,
`skill_warfare`, `skill_daemonology`) were granted by nothing. Cortex and
spinal had no tier-one chrome; ocular and limb had no endgame. Signal had
two items in the game and sabotage two. Only four programs in sixty cost
one memory, so a wide light loadout was impossible. And three of the most
expensive components in the game were pure upgrades with an empty penalty.

**Eight programs**: Handbill (the one-memory daemon a street market will
sell, which answers for its node out loud on a timer), Bellhop (one-memory
signal gear: traffic only, never contents), Understair (a one-memory mask
that stops working the moment the room goes red), Bottlecap (a one-memory
weapon that does nothing above rating three and escalates when it misses),
Cipherwright (a forger of keys that spends Focus, which never comes back
in a run), Slowfuse (a fault that goes off after you leave: quiet now,
loud in the record), Secondhand (framing without the rank: somebody real
gets the heat), Last Word (the best wiper in the game and the loudest
thing in its category).

**Nine chrome**: Doorman and Longhaul Frame for the street skills, the
Choirmaster for daemonology (their noise is filed against you), Second
Voice for subterfuge (nobody remembers the person you were not, so
standing does not accrue), Gutter Loop and Cold Spine for overclockers,
Long Eye and Breaker Hand for the two locations that had no endgame, and
Quiet Step for stealth.

**Two icons wearable at zero drift**, because six of the eight needed
coherence 15 or more and a new character had one real choice: the Night
Cleaner (quiet, and the tells arrive late) and the Meter Reader (cold on
heat, and useless the moment you do anything a meter reader would not).

**And the pure upgrades are gone.** Closed Loop has a pump that is the
first thing to fail; the Sendai Glacier is signed firmware nobody else can
work on, at Sendai repair prices; Needlecast is deaf to everything it is
not pointed at. Cold Block stopped being strictly worse than Closed Loop
and became a different trade: no moving parts, and the weight of a brick.
`test_breadth` holds every category to a tier-one option, every skill that
gear could train to gear that trains it, every chrome location to an early
pair and an endgame piece, and every tier-two-and-up component to costing
something.

### D70: Two more ways to be somebody

The city grew three districts in D67 and nobody could be from them. Two
origins, each with the full apparatus: a shape, a passive the engine reads,
a complication, a signature verb nobody else can type, and a story of its
own that crosses the district thread it came out of.

**The Compositor** set type in the Stacks for eleven years and reads a
network the way a compositor reads a page, which is as a structure somebody
chose. Topology legwork is free for them and comes back better, and a
corrected edition does not look like an original to somebody who has set
both, which in a network is a honeypot. Their verb is **`correction`**:
once a run, everything the network has filed about you this evening is
amended to be about a plausible other person, the alert drops a level and
the trace goes back about ten ticks. Their thread is the plate of a nine
year old correction with their name in the header, and somebody who buys
pages: sell it, print it again, or melt it.

**The Chorister** was raised in the Hall, under a departure board showing a
hymn, in a building where the answer to most questions was soup. Forty
people will say they were at the soup and mean it: heat cools half again as
fast and the street stops them a third less often. Their verb is
**`hymn`**: hold still and go through all of it, which restores Composure,
breaks every lock-on, and costs a tick that files as nothing, because
standing still and singing is not an action anybody can log. Their thread
is the debt with no number on it: the Hall fed them for twenty years and
has never asked for anything, and then somebody on the kitchen rota asks.

Six decisions between them, each with an epilogue line and an ambient
consequence, because D51 still holds.

D65 gave the street arrangements and nobody a face, so D70 also adds **the
collector**: the man who comes for the number you agreed is sixty eight,
has a bad knee, does the whole east side on a Tuesday, and writes it in a
notebook with the pen tied to it. The rota he walks is a file on somebody's
network, and he wants to read it before he is on it rather than walking it.
Three answers: tell him what it says about him, sell the sheet to a woman
in Marrow who reorganises three rounds inside a month, or tell him you
could not get it and let him keep coming. It waits on `arranged:1`, which
is world state rather than a decision, so it is a rule kind in
`world/story.py` and not a flag anything sets: an arrangement standing on
the street is a fact about the world, and the man is the face D65 was
missing.

### D71: The first night is winnable

The measurement that started this: twenty four fresh characters, each
taking the contract the game itself recommended and following the brief's
own advice tick by tick. **None of them finished.** Zero of twenty four,
and the game never said anything was wrong. Every individual piece was
behaving as designed; the design had four walls in it that only appear
when somebody with a starting deck walks into them in sequence.

**The rung nobody could climb.** An access tier is worth three points on
every attempt, and the only way up is a full crack of an auth server.
`_ensure_ladder` already guaranteed a tier-one auth behind any deep job,
which is a ladder. It did not guarantee that anybody could climb it: five
of the six services an auth server can expose want a forger or a
cryptography breaker, a badge needs *all* of them cracked, and no origin
starts with a forger. The lowest rung now runs no identity service at all
and always exposes the endpoint the things that call it would use.

**The door with no handle.** The same fact one level out: a host whose
services all rolled identity is not a hard door, it is a zero, and it
reads as one in the odds. `_soften_route` already capped wardens on the
one route a player would walk; `_openable_route` now makes the same
promise about the other half of a host. Off that route, whatever rolled
stands, which is what keeps a forger worth owning.

**The doorman past the desk.** A warden that does not take credentials
cannot be answered without an attack program, and no origin starts with
one either. On the walked route, at the tiers in front of the desk that
issues badges, those are removed and credential wardens come down to a
rating a fresh face can argue with. Deeper in, and anywhere off the route,
they stand where they were put.

**The vault with the errand in it.** Every objective sat in the core or
the restricted zone regardless of what the job paid, so a four hundred
credit errand for a gang was behind the same two access tiers as a bank's
ledger. Depth now scales with the fee: a small job against a soft target
sits one zone in from the front door, and that is the whole of the
discount. Against a hardened network the size buys a shorter walk, not a
shorter climb, or every posture in the game collapses into one.

Two more, found on the way down:

**The advice that could not read its own sums.** `_suggest_contract`
asked whether you owned a payload. The run asks whether the payload can
land: a corruption is resisted by posture over five plus six, a fresh
build brings about three, and the cheapest payload built for the job
costs four thousand one hundred credits against a starting seven hundred.
So the city walked people to the objective and printed `impossible` there
for the first time with the trace at forty. The resistance formulas now
live in `world/contracts.py` where both halves read them, and both the
board guarantee and the advice ask the real question.

**The friendly-voiced loop.** A watch banks nothing while the alert is
red, and the brief said `observe` anyway, once a tick, for thirty ticks,
while the trace went from eighteen to a hundred. It now says `wait`,
because quiet is what cools a room, or names the thing that is keeping
the room loud, or says to leave.

Measured after, on the same twenty four: **nineteen finish**, and the
five that do not are told the truth (something alive holds the room and
this build carries nothing that answers it). A fresh runner following the
advice through five contracts now earns about twelve hundred credits and
ends with more than they started with, against two hundred and seventy
across forty runs before.

Then the same harness was pointed at the other eleven origins, which is
where it found the flatly broken one. **Ex-enforcement finished 0 of 12**,
for a reason that had nothing to do with networks: the starting loadout is
filled "strongest first" by rating, their kit is a truncheon, a mask and a
breaker, and the first two filled the deck. They jacked in holding nothing
that opens a host, and the brief correctly told all twelve of them to
leave on the second tick. A breaker now loads first, always, because it is
not the strongest program in a kit, it is the one that makes a deck a
deck. Ex-enforcement finishes 11 of 12.

And the threshold under which the brief stops naming a door is now a
fraction of the clock rather than a flat number. What makes a long shot
bad is the countdown, not the odds: at three trace out of a hundred a one
in seven door is worth knocking on seven times, and at eighty it is a way
of spending the rest of the night.

All twelve origins now finish between 9 and 11 of 12 first contracts,
which is the spread a first night should have.

The ladder above the first night is unchanged and was re-measured to
prove it: a mid build still finishes 18-24 of 24 against a gang, 4-9
against Kagawa, 4-10 against Meridian and 2-4 against Deepwater. Posture
is still the difficulty. It is the first hour that was lying.

### D72: Something in the room, and a word about what it means

Play-test report, unprompted and exactly right: *"There doesn't seem to be
anything tricky or dangerous going on. It's rather boring really."*

Measured, and it was true. **The median number of live countermeasures on
the hosts a player actually walks through was zero.** A first-night
network had about three constructs on it and all of them were somewhere
else. ICE is rolled per host, deeper zones are meaner and the entry never
gets any, which are three reasonable rules that together empty the one
path anybody takes. D71 had made it worse by stripping the unanswerable
wardens out of the front of the route without putting anything answerable
back.

D6 is telegraphed-then-absolute: everything gets a tell and a tick to
answer it. That contract is worth nothing on a route with nothing on it.
So `_populate_route` puts a floor of live constructs on the walk, scaled
by posture, and at a gang that floor is one. A floor, not a quota: a
corporate route already runs seven and this does not touch it. In front
of the desk it draws only from the behaviours a fresh build can answer by
going quiet, moving, or leaving, which is the D71 promise and the reason
this cannot quietly undo it.

One exception, and it is the interesting one: **the chair is left clear on
a residency job.** Eight clean ticks on a host with something awake on it
is not a hard job, it is an arithmetic impossibility, so the danger goes
on the way in rather than on the thing you have to sit on.

Then the half that was not about density at all.

**The surveil brief was wrong.** It said "Take nothing, break nothing",
and the code has never read either: a tick banks if the alert is below red
when it ends, and red empties every one you had. A player watching a
counter go to eight without being told what fills it or what empties it is
watching a number, not playing a game. Both the aim and the progress line
now say the rule, and the progress line says what to do about it from
where you are standing.

**A tell explained itself only if it was lethal.** Black ICE has always
printed a line saying what the tick of warning is for. Everything else
printed atmosphere and struck. The first time anything winds up in a run,
once, the game now names the three answers: go to another host, hit it if
you brought something that hits, or go quiet and hope.

**A host said something was running and stopped there.** Now it says
whether it is asleep and what wakes it, or awake and looking, which is the
whole decision on that host: be quiet here, go round, or accept it.
Traps are exempt and stay invisible, because a trap is not running, it is
sitting there, and that is the one thing you cannot scout.

Measured after: something wakes on 10 of 24 first nights against 0, with
16 tells, and the alert leaves green on 14 of 24. Completion is 20 of 24,
which is up from D71's 19 rather than down: the danger costs a run
sometimes, and the advice being honest about red rooms saves more than it
costs. All twelve origins still finish 9 to 12 of 12, and the mid-game
ladder is unchanged again.

### D73: Who names the machines

Play-test report, and it is hard to argue with: *"They sound weird, like
I'm hacking furniture."*

They did. Gang and collective hosts were drawn from one pool of twenty
words and the pool was a canal boat inventory: kettle, ashtray, thimble,
pallet, tarp, winch, bollard, gantry, sump, lantern. Three of them were
already the names of programs, so a player could be standing on `lantern`
holding a Lantern.

Worse than the words: **only two of the eight faction kinds used them at
all.** Everybody else fell through to the corporate scheme, so Nightwatch,
the Chorus, Static, Switchboard and whatever Deepwater is all ran networks
that looked like a logistics company's asset register. D67 says every
faction's net should read as its own from the inside, and the first thing
anybody reads is the name at the top of the host.

So: one naming vocabulary per faction kind, because who names a machine
says what they are.

- **A gang** uses the names it shouts across a room: tommy, vic, knuckle,
  muggins, tallboy, nutmeg.
- **The docks** use the language of the rota: berth, muster, tally,
  bosun, dunnage, nightgang.
- **The Chorus** use the hours of the office: matins, lauds, compline,
  censer, thurible, precentor.
- **Static** use the print floor: masthead, byline, deadline, spike,
  standfirst, deadair.
- **Nightwatch** use the register: docket, warrant, custody, casefile,
  chargesheet, holdingroom.
- **Switchboard** is a telephone exchange and has never pretended to be
  anything else: trunk, tieline, ringdown, crossbar, subscriber, tandem.
- **Deepwater** is not made of offices: fathom, trench, hadal, nekton,
  thermocline, scattering, marianas.
- **A corporation** keeps the asset register, which is what the old
  scheme was and it was right about corporations.

And where a faction is sharper than its kind, it gets its own: Carrion
and the Sixes are both gangs and do not sound alike, so Carrion names its
machines the way it thinks about people, which is as parts. Gristle,
donor, graft, harvest, rejection, coldstore.

A family also numbers from two now. The old code rolled a suffix at
random, which put a `vic` and a `vic3` on the same network with no `vic2`,
and a missing host is a thing a player goes looking for.

`HOST_SITE` went in the same pass: declared at the top of the file,
read by nothing, since the first commit. The usual bug in this project,
one more time.

Two tests broke on this and neither was about naming, which is the useful
part. Both were measuring the seed rather than the game: the ladder
asserted that a starting build finishes four of twelve gang jobs when the
true rate is one in four, so twelve samples was a number between nought
and seven and it had been lucky; and a held-program check picked "any
service that is not crypto", matched a physical one, and read a Hardware
rank where it meant to read Intrusion. Renaming the hosts shifted the
stream and both fell over. The rates are now measured over thirty seeds
and the fixture asks for the family it means.

### D74: What a test run found

Three things, all found by sitting down and playing one first night from
`new` to the summary card rather than by running a harness at it.

**The game forgot the job.** `-c` mode did not save when it finished, on
the reasoning that a non-interactive invocation should not surprise
anybody by writing to disk. That sounds like the careful choice and was
not, because a handful of commands autosave on their own: anything that
moves a shift, anything on the street. So a `-c` run wrote *some* of what
it had done. Spending a budget and then taking a job kept the spend and
lost the job, and the next invocation said `no contract accepted`, which
does not read as a policy about non-interactive mode. It reads as the
game forgetting. It saves at the end now, the same as leaving the prompt
does, with one exception: not mid-run, because a run is not in the save
format and `quit` refuses for the same reason.

**The first board offered a job nobody could afford.** The guarantee
already asked whether the objective's *check* could land, which was D71's
fix and a real one. It never asked whether the thing the verb needs was
on the deck. A Carrion exfiltration at posture 30 counted as the soft,
small, doable job the board promises, and it wants a payload, and the
cheapest payload in the game is nine hundred credits against a starting
seven hundred. So the guarantee did not fire, and the advice priced the
unaffordable soft job above a posture thirty-five network and sent
everybody there. That run is in the log: a core objective, a Drover
closing routes behind, two Bloodhounds, severed at a hundred trace on
tick twenty-two with a bounty attached to the name. `objective_ready`
asks both questions and the board and the advice both read it. All twelve
origins moved up: nine to twelve of twelve first contracts, from nine to
eleven.

**The brief named a host it had just said you had not found.** The
surveil progress line was rewritten in D72 to say what to do from where
you are standing, and it did that by naming the objective host, one line
under an aim that says the host has not been reached yet. Everything else
in the run holds to earning a name before printing it. Now this does too.

### D75: A full playthrough, and the ten things it found

One character, `new` to the last scene of the main line: twenty-three
contracts, a burned name, and the Deepwater spine carried to `under`.
Nothing here was found by a harness. All of it was found by playing.

**The curated first board was a cliff, not a ramp.** The soft-small-ready
guarantee fired at `runs == 0` and never again. The second board of this
playthrough rolled five `large` postings at postures twenty-eight to
fifty-eight and the advice recommended Nightwatch at forty-eight to
somebody holding a Crowbar. The size distribution turned out to be fine
(twenty-two per cent small over two hundred boards), so nothing was broken
except that nothing was watching. `_ensure_startable` now runs on every
refresh and every top-up, including when the board is full, which was the
stranding case. Runs one to four keep a weaker promise than night one:
something they are equipped for, at a soft posture, no bigger than
ordinary.

**Burning your name did not clear the bounty on it.** `help heat` has
always said heat accrues to the name, that burning dumps it, and that
"sometimes that is cheaper than the bounty". It was not true of any
bounty: `city.bounties` is keyed by faction and nothing cleared it. I paid
eighteen hundred credits and every relationship built under the old name,
and the streets were exactly as dangerous, which is how I found it.
Burning now retires the numbers and the "next time they will not be
asking" warnings that came with them. Arrival danger in the Ninth, on the
fixture: sixty-three to nought.

**The "you cannot do this job" warning was on the screen nobody reads.**
`board <id>` warns when an objective needs a program you have not got.
`take <id>` did not, and `now` says `take c005`, so following the game's
own advice routed straight past the only warning in the game about it.

**The advice named a walk the street was refusing.** The contract branch
of `city_steps` knew about bounties on the route. The errand branch did
not, so with the Sixes hunting me in Marrow it said `walk hall`, the
street said no, and it said it every time I asked.

**"Heat cools while you lie low" was true and useless.** At ninety-seven
with a bounty standing, that is a thirty-shift suggestion printed as the
next thing to type. It now says the heat, the rate, what a new name costs,
and that `--anyway` walks into them: three doors with prices instead of
one that sounds free.

**An accepted contract that expired read as `-68sh`.** The sweep protects
the accepted contract, which is right. Printing `expires - shift` raw for
it was not, and nothing ever said the job had gone cold.

**A story decision never said what was being asked.** `theirs/ask` ended
on "Then he tells you what they would like" and offered `yes: Do it`
against `no: Say no`. Both outcomes are written; the decision was blind.
Named the ask and sharpened the labels.

**Asking a question at a street prompt burned a strike.** Three
non-answers and the street stops waiting and stands you there. Any input
counted, so typing `help` at a knife in a doorway put you two keystrokes
from having answered. Asides reprint the setup with every option's odds
and cost nothing now.

**The Hall's street line stuttered.** Two near-identical entries about
Carrion in one sentence, because the picker deduped on whole strings.
Rewrote both pairs; validate now refuses two street lines in a district
that open with the same four words.

**And one left open, because it is a design call rather than a bug.** The
last scene of the main line requires `lark_saved` along with `dw_read` and
`archive_consented`, and the scene is explicitly *about* those three
things, which is the best argument for keeping the gate. But a player who
never meets Lark, or who chooses `nothing`, loses the ending permanently
with no indication it was there. The recommendation in the issue log is to
let the journal admit, in voice, that a thread is waiting on the world
rather than on the player.

### D76: The journal admits when a thread is waiting on the world

The one thing D75 left open. The journal could always say a thread was
waiting on *you*, because a pending choice is visible. It could not say
the other case, which is a thread waiting on the world: on somebody you
have not met, or on a decision belonging to a different story. The main
line ends on a scene that needs Lark alive, and a player who never met
Lark lost the last scene of the game without ever learning it was there.

`Story.waiting_on` reads the first unreached stage whose requirements are
closest to met, and says what it is short of in words. It names people
and other threads and never flags, never says what the scene is, and says
nothing at all when the only thing missing is work the player was going
to do anyway. Reading the spine mid-way it says the Archivist, because
that is the nearest lead; reading it near the end, once the Archivist has
been found, it says Lark. That is the useful order: the next step, not
the final gate.

It also knows when a door has shut. A flag that comes from a decision is
gone for good once the decision has been made the other way, so a thread
whose Lark is dead does not send anybody looking for Lark. It says: *There
was more of this. There is not now.* Which is the honest sentence, and
the one the game should be willing to say about itself.

Four threads say anything at all on the stage they open at, and each is a
true lead. The rest are quiet, which is right: they are waiting on work
rather than on people.

### D77: Things that happen while you are in there

A network had a posture, a shape and a condition, and all three were
decided before the player jacked in. Nothing moved on its own once they
were inside, so a run was the player's decisions against a board that sat
still, and the word for that turned out to be boring.

An incident is the fourth thing: something the network does mid-run, on
its own clock, about once in a dozen ticks and more often when the room
is up. Twenty-seven of them. Sixteen are bad, six are good and worth
having rather than smaller punishments, and five are not finished when
they print.

Those last five are where the thinking is, and they exist because the
alternative was a menu. **Nothing here opens a prompt.** An incident
changes the board and the next thing you type is the answer to it:

- something copies you, so the next action is twice as loud and leaves
  twice as much: do the cheap thing now, not the expensive one
- the floor gives, so the next *noise* you make here costs Integrity and
  being still costs nothing: `wait` a tick
- a crawler marks your route, so the next host you open wakes with you in
  it: open the one you were going to fight anyway
- a gap opens and the next thing is free: spend it on the dearest thing
  you have
- somebody else is loud, and the next noise you make does not register

`status` always says what is attached and what answers it. Every number an
incident moves is printed on the line that moves it, because D14 does not
stop being true because the modifier arrived at tick nine.

### D78: The brief teaches the loop you start with and no other

Twenty-eight techniques hang off the fourteen skills, two per skill at
ranks two and four. The brief's entire vocabulary was `scan`, `probe`,
`crack`, `connect`, the objective verb, and `jack out`. It named exactly
two techniques, and one of those was added in D72.

So a player who spent eleven experience on Intrusion 4 was never once
told to `pivot`. Their build was a slightly better number on the same six
verbs, which is why the measured ladder was flat: a starting build and a
maxed build finished within a couple of runs of each other against
anything hard, and the ranks nobody was told to use were the reason.

`_better_step` is the one place that asks whether the character holds
something that beats the plain move, and it only ever answers with a verb
they have actually bought: `crack --chain` when two doors on one host are
both worth trying, `pivot` when a warden holds the next hop and a
neighbour is open, `pretext` when the warden takes credentials and the
face can present them, `sidechannel` when the only way in is cryptography,
`scrub` before leaving a host with a mess on it.

Measured, thirty seeds a cell, against a gang: **6, 11 and 19 completions
for a starting, mid and top build**, where before it was flat. Against
Kagawa the top build now finishes four times what the middle one does.

Two rules keep it honest. A technique is an *opening* move, offered once
per host: if the check misses, the ordinary advice takes over rather than
standing there repeating an expensive verb at a door that is not opening.
And the target is the host the warden is on, probed, not the host you are
standing on, because `test_brief` exists precisely to catch advice the
game then refuses, and it caught both of those.

### D79: How a character gets better, said out loud

Three things a player could not see, all of them systems that already
existed and worked.

**`train` was an error message.** With no argument it raised "which
skill:" and listed fourteen words. Twenty-eight techniques hang off those
ranks and nothing anywhere said so, so somebody sitting on twelve
experience had no way to find out what it was for. It is a screen now:
every skill, the rank held, what the next one costs, and what it buys,
named. Where the next rank buys no verb it names the one the skill is on
the way to and at what rank, because a player planning a build needs the
goal rather than the step, and "a better number" is not a goal. It ends
with what is affordable right now.

**The advice never mentioned any system but its own.** One nudge existed,
for the script library at Daemonology 2, and it worked: it was the only
optional layer I reliably noticed while playing. It has siblings now.
Experience that would buy a verb says so and names the verb. A runner
still carrying only the chrome their origin gave them, with money in
hand and a clinic in the district, gets told that chrome is the other
half of a build and what it costs. A rival who has made their mind up
about you gets mentioned once, because `hire`, `ask` and `bet` are three
verbs a career can pass without meeting.

**Lethality is doctrine, and the board sold it as posture.** Kagawa at
posture forty-five can kill you. Meridian at sixty-two cannot: seven of
the twelve factions have no lethal construct available to them at all,
and the board's difficulty column is derived from posture alone, so the
number it prints is not the number that matters most. A name on the board
now carries `!` when that lot run black ICE, the board explains the mark,
and the contract reading says it in a sentence. Nothing about it is a
spoiler: which corporations use lethal countermeasures is the sort of
thing everybody in this city knows.

### D80: Six objectives, six shapes

Six objectives and four of them were the same run: reach the host, type
one word, leave. Only a surveil was structurally different, and that is
the one that reliably produced a story, which was the clue.

**An exfiltration is about the exit.** It used to be over the moment you
had the record in hand and the walk out was the walk in with a different
destination. What they want is the loudest thing on the network and it is
in your traffic now: everything you do carrying it counts for half again.
The grab is the middle of the job.

**An implant has to take.** Pushing it is not finishing it. It needs five
ticks on the network to become part of the furniture, and you have to
still be in here when it does, anywhere in here. Standing over it is the
worst place to wait, which makes the end of an implant job a question
about where to spend five ticks rather than a walk to the door.

**A corruption has to read as a fault.** It cannot be done while the room
is red, because an edit made while the whole floor is looking at the disk
is not a disk fault, it is you. The room has to settle first, and the
verb says so rather than failing a check quietly.

**A wipe is loud and cannot be anything else.** Destroying a record wakes
everything on the host and puts the desk up a level, guaranteed, no roll.
A deletion cannot be dressed as an accident: the shape of a wipe job is
smash and run, and now it is.

**A surveil is not a vault job.** It was placed in the core like
everything else, which meant reaching it made exactly the amount of noise
that puts the room red, and red empties the bank: nought completions in
twenty four, measured with incidents on and off, so this one predated
them. You surveil where the traffic is. Restricted or interior, and six
in twenty four.

Two things found on the way. The brief advised `signal` on an escort with
nobody to signal, which is the one thing advice must never do. And
`crack --chain` is two cracks' worth of noise in one action: the brief now
offers it while the room is green and the trace is under half, and stops
offering it after that, because speed is worth noise early and never
worth it late. That alone took a network from lockdown at tick ten to
finishing.

### D81: Something to do when it is winding up

D2 says netrunning, never combat: no guns, no street fights, all conflict
program against countermeasure. That rule is not the problem. The problem
was that the conflict it does allow was locked behind one skill and
invisible to everybody else.

`strike` is Warfare 2 and `overload` is Warfare 4. Every other build's
answer to a construct winding up was to leave, and the seven armour
programs made a number smaller and did nothing else, which is the least
interesting thing a piece of kit can do.

**`brace` needs no rank.** It is the tick a tell buys you, spent on the
hit instead of on running from it: the next thing that reaches you does
half, and it lasts this tick and the next. That is the whole verb. It is
deliberately available to a first-night gutter with a Crowbar, because
"get out or get hit" is not a decision and "take it properly, or run, or
hit it if you can" is three.

**And armour answers back.** Braced, what a loaded armour program stops
goes back down the line into whatever sent it, which can kill it. A build
with no Warfare in it now has a way to hurt a countermeasure, and a
reason to carry armour on purpose rather than as a smaller number.

The brief offers `brace` when something is telegraphed and the build has
nothing that hits, which is exactly the case that used to end in `jack
out`.

**The same shape, outside.** The street was one check: you answered, it
resolved, and the rest happened to you. A bad answer that is going to
cost you three Integrity or more now buys one more decision, and nobody
throws a punch in it. `cover` is taking it properly, on Grit and
Fieldcraft, and halves it. `give` is making yourself not worth the
trouble, priced by the rung. An empty line is taking it as it comes.

Cover was written at six plus two a rung, which put the fourth rung out
of reach of every build in the game and made the option decoration. At
four plus two a rung it reads: nothing for a fresh gutter, three nights
in five for a Grit build that bought Fieldcraft, and reliable for
somebody who specialised. Which is the first time in this game that Grit
and Fieldcraft have bought anything a player can watch happen.

### D82: The stake was right. The second contract was not.

The question was whether 45,000 credits is too far. Measured against the
board it is exactly what the comment beside it has always claimed: at a
median gang fee of 1,322 credits it is thirty-four completed gang
contracts, at mid posture fourteen, at corporate nine. "Somewhere between
ten and thirty successful runs." The target is honest and it has not
moved.

What was not honest was everything between the first contract and the
thirty-fourth. Six careers driven end to end, measuring what each run
actually paid:

```
run #     1     2     3     4     5     6     7    8+
paid   1139     0     0     0     0     0     0     0
```

**The first contract pays every time and nothing else pays at all.** Not
a slow economy: a cliff with one step on it.

Three things made that, and none of them was the number.

**Depth stepped from shallowest to deepest with nothing in between.** A
small job sat one zone in from the door; an *ordinary* job went straight
to the core. So the second contract of a career was two access tiers
deeper than the first, and a realistic second-contract runner finished
one job in twenty four against twenty in twenty four for their first.
Depth tracks size across the whole range now. Measured at gang posture,
the size ladder reads 24, 24, 17 and 12 of 24 across small, ordinary,
large and sprawl, which is a gradient rather than a wall.

**The advice read tenure where it meant capability.** It preferred
smaller jobs for the first five contracts and then stopped, so a runner
five contracts in who had spent nothing was recommended the biggest job
on the softest network. It reads ranks bought now: about double what an
origin ships with is where size stops being the thing most likely to end
the night.

**And nothing ever said to buy a payload.** Four of the six objectives
need one. The two that do not are the two hardest to finish. A runner
without one was steered around every job that wanted one, for ever, and
the loop is: no payload, so watch work, so no money, so no payload. It is
a standing step now, the moment it is affordable, rather than advice that
waits for a contract to demand it. Careers that ended holding a payload
went from none in eight to five in eight.

One more, which pays for the nights that go wrong: a run whose objective
has gone out of reach is told to carry something out rather than leave
empty handed. The job sheet has always said a run with nothing on it pays
for whatever you can carry. The advice never once said it.

### D83: Playing it again, with everything in

Seven things, all from a fresh character on the current build. Five are
about the same mistake made in three places: the advice knew how to
recommend buying a thing and did not know what happened next.

**Told to buy a payload, then left holding it.** The standing nudge from
D82 says buy one, you buy it, the load fails for memory, and the advice
moves on to the next contract without mentioning it. The unload step
existed, inside the branch that fires when an accepted contract needs a
program, so buying one *before* taking a job fell straight through it.

**Seventeen contracts in, still on the starting breaker.** Five thousand
credits banked and the deck was the two rating-two Crowbars it started
with. A breaker's rating is the biggest single term in every door check
in the game and nothing had ever mentioned that a better one exists,
because the advice only ever spoke about programs a contract demanded,
and no contract demands a *better* one.

Both of those are now one helper, `_fit_step`, used by both: it knows
that owning is not carrying, and it says `load` or names the thing to
unload for it.

**And then it recommended buying the shop's whole stock.** With an
unloaded Sable in the bag the nudge compared against the best breaker
*owned* rather than the best one on the deck, so it recommended the next
one up, and would have gone on doing that for as long as the money
lasted. It reads the deck now.

**And a shop that had not got it.** `buy drillbit` against a market whose
answer is "nothing here matches 'drillbit'" is a loop, and it ran until
the turn budget stopped it. Affordability and a market in the district
are not the same as stock. Both nudges read the actual listings now.

**Gear was advised after the walk.** The loadout is fixed the moment you
jack in, so anything that changes the deck has to be said before anything
that moves you toward a network. `now` shows two steps, so an unloaded
Sable sat behind `jack in` where nobody would ever see it.

Two from the run itself.

**A gift spent on nothing.** The `quiet` hook waits for the next *noise*
now rather than the next action: `brace`, `wait` and `observe` were
eating it and announcing that something had gone out under somebody
else's noise, about an action that made none. Same for `echo`, which was
doubling a zero.

**Braced, then left.** The brief advised `brace` and then `jack out` on
consecutive ticks, which is a tick spent taking a hit on a night it had
already decided to abandon. It only offers it on a run that is carrying
on.

One left open on purpose. For this playthrough's build against a
posture-26 network, exfiltrate and wipe finish ten in twenty four,
implant eight, and **surveil two and corrupt none**. I guessed the cause
was the alert rules those two got in D80 and measured it: cooling faster
changed nothing at all, so the alert is not the constraint. Tracing a
failure shows the run ending because it runs out of openable doors, which
is the same capability wall as the corporate one. It wants an honest look
at door difficulty against breaker rating rather than a number nudged
until one objective looks better.

### D84: Measuring the wall instead of guessing at it

The open question from D83 was why a residency job finished two runs in
twenty four where its neighbours finished ten, and whether the corporate
end of the game is a wall or a bad harness. Both answers came out of
measurement, and both corrected something I had previously asserted.

**The city's estimate and the run's sum were three apart.** D71 put the
objective resistance in one place so the board and the run could not
drift. The *power* half still had two copies, and they disagreed: the run
doubles the payload term and then takes the improvised penalty off as its
own term, and the estimate took the penalty off before doubling. Three
points, every time, in the pessimistic direction. So the city told people
a wipe was impossible when the run gives them thirty per cent on it, and
steered the advice away from work that pays. `test_early` now asserts the
two agree for every payload at every rank.

**And my own conclusion in D83 was wrong.** I reported corrupt at nought
in twenty four as a game problem. It was a harness problem: I was forcing
a corruption on a character with Sabotage 0 holding an exfiltration
payload, which `objective_ready` correctly refuses to recommend. Measured
only against the objectives the game would actually let that build take,
corrupt does not belong in the table at all.

**A watch was systematically deeper than everything else.** The real
outlier was surveil, and it was placement. Every other objective lands
wherever the thing it is about happens to be; a place-objective was
narrowed to the deepest zone it was allowed in and then explicitly
preferred that zone, so a residency job sat two rooms further in than the
exfiltration on the same network, reached its own objective nine times in
twenty four against sixteen, and then still needed eight clean ticks
after arriving. It picks by traffic now, with no zone preference at all.
Three wrong hypotheses died on the way: the alert rules from D80 (cooling
faster changes nothing at all), the host-selection key, and the residency
rule itself. The numbers now read 10, 10, 8 and 7 of 24 for exfiltrate,
wipe, implant and surveil, and `test_objective_parity` holds them within
three times each other.

**The corporate wall is real.** This is the one I most expected to be my
own bad measurement, and it is not. A policy that overclocks, masks when
loud, and strikes what locks on rather than walking away from it changes
almost nothing: a top build goes 4 to 5 of 30 against Kagawa and 5 to 9
against Meridian, and a mid build does not move.

What it is, precisely: at gang posture a top build reaches the objective
**thirty times out of thirty, arriving with forty trace spent**. At
Kagawa it reaches the objective **seven times out of thirty, arriving
with eighty-four**. Twenty-four of thirty runs are severed before they
get there. The doors are not the problem, and the table says so: a rank
five build opens a difficulty seven door at a hundred per cent on its own
tier and eighty per cent three tiers above it. Nor is it the families,
which are fifty-three per cent access on a corporate route, nor a missing
forger, which makes it worse by displacing the mask.

It is the approach. At corporate posture the trace budget is spent
getting there, and nothing a player carries or does changes that enough
to matter. Whether that is correct is a design decision rather than a
bug, and it is left open deliberately: the options are a longer clock at
high posture, shorter approaches, or the position that corporate work is
meant to be something you survive rather than something you complete.

### D85: The call on the corporate wall, and two reversals getting there

I was asked to make the judgement. The judgement is: **leave the
difficulty numbers alone and ship the legibility.** Getting there took two
reversals of my own claims, and both belong in the record.

**Reversal one: it was a harness artifact, then it wasn't, then it partly
was.** I reported the wall as real on the grounds that a competent policy
did not rescue it, which was true. What I had not noticed is that the
measurement reused one character across thirty runs, and armour and masks
*degrade as they work*. So the "top build" was, by run ten, a build with
no working mask. With a clean deck for every run, corporate completion is
roughly three times what I reported. It is still low. It is not what I
said it was.

**Reversal two: I added a constant and took it back out.** Posture is
counted three times against a player (harder doors, denser ICE, longer
walk) and never once for them, and the fiction for the fix was already
written: ten thousand legitimate sessions is the best mask money cannot
buy, and a corporation has ten thousand where a gang has forty. So I put
posture into the crowd term. Measured: a top build finished four
corporate runs in thirty before and four after. A constant that buys
nothing does not belong in the game, so it came out again, and the
reasoning is in the docstring where the next person will find it.

**What the measurement actually found, in order of size.**

A mask is the difference between a hard job and an impossible one. Clean
deck, twenty four runs: no mask gives 20, 2, 1, 3 and 2 completions at
postures 22, 45, 48, 62 and 72; a mask gives 24, 6, 4, 5 and 3. It
roughly triples corporate work, and nothing anywhere told a player to
carry one. That is the third instance of the same failure this session,
after the payload and the breaker, and it is now fixed the same way.

A deck nobody repairs stops being the deck they built, silently, because
degradation makes things worse rather than stopping them. Also now
advised.

And `brace` was the corporate wall's loudest single contributor, which is
mortifying because I added it two commits earlier. Offered whenever
anything was telegraphed and the build carried no weapon, at corporate
posture where something is winding up nearly every tick, it produced a
runner standing still being hit: typed a hundred and twenty four times
across thirty severed runs, and the most repeated command in nine of
them. It is now offered only against something locked on to you, once,
because the tick a tell buys you is spent once and not adopted as a way
of life.

**Why the numbers stay.** Every difficulty lever I tested moved
completion by nought to three runs in twenty four. None was decisive; the
only decisive thing was player knowledge. A game whose stated position is
that the city does not care whether you live is allowed to make corporate
work a one-in-four proposition, *provided the player can see the price
before they pay it*: and between the lethality marks, the door and room
reads on the board, and now the mask and repair advice, they can. Moving
those numbers further would be me guessing, and this session has already
produced three measurement-driven reversals of things I was confident
about. The disciplined answer is to ship what is evidenced and leave the
rest visible.

### D86: The people are the story

Three play-tests, run in parallel with three different briefs, and the
largest thing all three agreed on was not a bug in any system: it was that
the story never started. Thirty-five threads and a hundred and three scenes,
gated almost entirely on `met:<somebody>`, and the one piece of advice a new
player follows never said a person's name. Arriving in a district listed the
market, the workshop and the places to stand, and not the people; `look` was
under "also"; the journal said "things start when you meet people" and
nothing said who or where. The first-timer reached seven threads in ten
contracts and touched none of them on purpose. The explorer, who walked all
twelve districts and talked to twenty-two people, said the same thing from
the other side: nothing ever gave them a reason to go anywhere.

And underneath it, the project's oldest bug wearing a story. `Stage.where`
is set on forty-two of the hundred and three scenes, its comment says "for
flavour and gating", and nothing read it. The Notary's counter on the Row
was played on a Freeport dock. A vending machine in the Ninth was asked
about the war from Marrow. `check_dead_fields` did not catch it because
`npc.where` is read everywhere, and the field's name is the same.

**What changed.**

- A scene fires where it is set. `Story.available` reads `where`, and the
  journal's D76 line says so when the place is the only thing missing:
  "waiting on you being in Marrow". `validate.py` holds every `where` to a
  real district.
- `now` has a reason to go somewhere. One line at most, after the work:
  somebody unmet standing in this street whose thread is waiting on them
  ("`look`: Ozymandias is waiting on somebody who is standing in this
  street"), or, failing that, a district where a scene is ready ("`travel
  marrow`: The Queue has more of it in Marrow, one shift away, and it is
  waiting for you to be there"). Names the thread and the place, never the
  scene.
- Arriving somewhere names the people: the ones you have met by name, the
  rest as a count, and `look` stays the moment of meeting.
- Talking to somebody standing here is meeting them. `talk` and `ask` used
  to refuse anybody `look` had not introduced, every arrival and every
  shift.
- `asked:<npc>:<topic>` is a rule kind. `ask` always set the flag and
  nothing could read it, so the Ozymandias scenes narrated questions nobody
  had typed. Now the sign that says DO NOT ASK HIM ABOUT THE WAR is a
  gate, and asking is the scene.
- Three scenes at most on one command. Five back to back on one `look` was
  a wall of prose; the ones written for this street go first, and the rest
  keep for the next thing you do.
- Bare verbs answer the question asked: `talk` lists who is here, `ask`
  lists who is here and what they will talk about (the favour table is
  `ask favours`), `sell` lists what the bag would fetch.

### D87: The advice reads the night before

The first-timer's transcript, condensed: contract four was severed at trace
one hundred five times in a row on the identical network, and after every
one `now` said `jack in`. They typed `drop` themselves; `now` immediately
recommended the same contract as the softest thing on the board, so they
took it back. Every crack for eight runs printed "held to 2 by Intrusion 0"
and the plan, the training screen and the nudges named five other skills
before anybody said Intrusion. With a Sixes bounty, the advice said `rest
3` twenty-four times over seventy-two shifts while an arrangement collected
every six. And the explorer found the fit advice arguing with itself over
the last two memory on a four-memory deck: load Sable, unload Sable for
Siphon, unload Siphon for Quietcastle, for ever.

None of these was a difficulty problem. All of them were the advice having
no memory and no budget.

**A run is written down.** `Game.history` keeps every run: day, job,
target, how it ended, how long it took, what it paid, and two numbers the
advice can read back, how many tiers short of the objective's zone the
badge was and how far below its rating the breaker ran. `log` in the city
prints the career one line per run; `previously` shows the last one.

**The recommender reads it.** A contract that has cut you loose is not
the softest thing on the board whatever its posture says; twice, and it is
off the list, and holding it the advice is `drop`, with the reason in the
history's own terms ("each time you held a badge two tiers short of the
zone the job is in"). It also declines jobs that expire before the walk
gets there, prices a route through somebody hunting you, and counts
finished runs and not only ranks bought before it stops calling you green.
If nothing on the board survives that, it says so and points at `errands`
rather than at row one.

**The breaker's rank first.** A program runs at its rating only up to the
skill plus two, so a protege's rating-three Sable on Intrusion 0 is a
rating-two program that costs twice the memory. The spend plan buys that
rank before breadth, and the advice names it whenever it is affordable.

**One loadout plan.** `_loadout_plan` decides the deck once, in order: the
breaker, what the job in hand needs, a payload, a mask on hard work, then
the rest, each the best owned at the rank that drives it, each only if
there is room after the ones before it. Every fit step is a move toward
that deck, so it cannot loop, and the test walks it to a fixed point.

**Not `rest` against a bounty.** Heat cools about a point a shift and a
bounty does not cool at all. Below forty, `rest N` with the number; above
it, or with a bounty, the ways out are named as steps (`drop`, `burn
--confirm`, or `walk --anyway`), and an arrangement is the walk being
theirs: `travel` no longer refuses a street you have paid for.

Smaller, from the same reports: the advice quotes the shop's real price
rather than the catalogue's; `walk` stops when the street stops you (it
carried on through two districts with the question still open); a verb
typed at a yes-or-no question is a verb; a contract finished after its
date pays sixty per cent; the street does not repeat the encounter it
just had; a job you never held is not taken "out from under you"; and the
rice hints stopped saying nine districts.

### D88: The wall you can see, and the night that is over

The run specialist played the Chromed origin, whose chrome adds up to ten
points against presenting a credential, and found that a Steward on the
one guaranteed route reads "impossible as configured" against them: nine
burned runs across gang and mid posture, on jobs the board called the
softest thing on it. The game prompted `connect --present` on the sum it
had just called impossible, and presenting escalated. The brief never
offered `pivot` against an open host a warden still held, because it
required the hop to be shut. And at lockdown with the trace at ninety, the
brief went on saying `wait` and `crack`, one long shot at a time, because
the give-up rule priced each door and never the whole night. Separately:
a severed connection had no cooldown, though D6 has promised one since the
first day, and a deck with a destroyed CPU jacked in silently and ran at
nothing.

**The wall, made visible and answerable.**

- `native` walks through a warden. The origin's own text says the network
  becomes a room; a room does not have a desk. Once a run, the warden is
  neither answered nor killed, and the brief offers it when nothing else
  you carry would satisfy the check. The Chromed wall is now the Chromed
  verb.
- The impossible is refused, for free. `connect` at a warden that would
  take nothing you carry says so once, with the sum and the ways round it,
  and prompts nothing; `--present` against it is a refusal, not an
  escalation. `strike` with the odds at nought is the same.
- `pivot` is offered on an open hop. The condition that required it shut
  is gone.
- The board reads a badge desk against the build. `board <id>` says "a
  badge desk would stop you" with the run's own sum when it would, and
  the recommender leans away from it for a build with neither a forger,
  `pivot`, nor `native`.
- `_hopeless_where` names the warden when the warden is the problem,
  and the sentry when a watch or an edit is standing under something awake
  at red, instead of "nothing opens for what you are carrying: the best of
  it is 100% on badge reader" about doors that were all open. The door
  reason is only given when the doors are in fact hopeless. The history's
  `short` is read only for runs that never reached the objective, for the
  same reason.

**The night that is over.** `night_over` reads the clock once, for the
whole of what is left: working ticks at the working rate and quiet ticks
at the quiet one (quiet ticks are cheap by design, D66, and pricing a
watch like a crack made the first version tell surveil jobs to leave at
trace fifty), against what the trace has in it at this alert. Only once
the room has turned or the clock is half spent, and only when the sum does
not fit with fifteen per cent to spare. The brief then says leave, in so
many words, with both numbers.

**The cooldown, kept.** A severed connection grounds you for two shifts,
`jack in` refuses meanwhile and says why, and the advice is `rest`. A
deck with a destroyed part or more loaded than it can hold is refused too,
with the nearest workshop named; the repair nudge walks you there when
the damage is serious and no workshop is here.

Also from the same session: a probe budget in the brief (two hosts mapped
and one of them shut is enough to go through, rather than reading every
label on a hostile segment first); `odds crack <host> --chain` prices both
halves instead of reading the host as a service on the node you stand on;
`wait` says what it buys; an `observe` that banked nothing does not print
a tick mark; a copy hook does not resolve on `jack out`; a finished title
is not re-posted at once.

### D89: What the city remembers inside the net

Two things added rather than fixed, both from the same observation: the
city remembers in numbers (posture, heat, a bounty) and never in a face,
and the other runners exist on the board and in the wire and never in the
one place the game happens.

**The construct that put you out.** A run that ends severed records which
construct did it, and the city keeps that against the faction. Their next
network runs it on the route you walk, a point harder and already awake,
and the tell names it: "You know this one. It put you out of a Sixes
network, and it has been running since." The board says so before you
take the job, the connected screen says so at the door, and killing it
ends the habit: "The Sixes will build another. They will not build that
one." It is placed without a random draw, so a network with no grudge on
it is the network it always was, and the test holds every host name
equal with and without one.

**Somebody else is in here.** A `turn` incident, weighted like the others,
that only fires when the city has a runner to spare: one of them is in
this network tonight for their own reasons. Who is the city's roster; what
it means is the number `who` has always shown. Warm, and their traffic is
your cover (the next thing you do goes out under their noise). Cold, and
they have seen you and somebody upstairs is about to hear about it (the
room steps up). Anything else, and you read each other's scans and say
nothing (their hosts are on your map). Afterwards the wire says they were
in there the same night you were, and they remember: covering for you
warms them, tipping the room cools them.

Both live entirely in systems that already existed. Neither adds a number
a player cannot read.

### D90: The second look

The first three play-tests left a list of things that were not bugs so
much as questions nobody had answered, and the second wave (the same
method, on the committed build) found one more loop before the session
limit cut all three of them off mid-career. In order of size:

**The present loop.** The brief advised `connect <host> --present` at a
warden whenever the warden took credentials, with no memory of having
been refused and no floor on the odds, and every refusal steps the alert.
A story player's follower typed it twelve times on one host. Now it is
advised once per warden, only at odds above the brief's own long-shot
line, a refusal is remembered (`tried`), a refused warden is routed
around like an impossible one, and `_hopeless_where` names the refusal
as the reason when it is.

**A list of people.** The map said twenty-nine people were worth finding
and nothing listed them. `people` is the ones you have met, with the
district they keep to and their hours, and the rest counted by district
and never named, because meeting somebody is `look`'s moment and a name
in a table is not a meeting.

**Places that told the truth about who was not there.** A spot said "not
here at this hour, afternoons and nights" and then, in the afternoon,
"not here at the moment", which read as the place lying. The second case
was somebody who has not heard of you yet, and now it says so.

**Variety in the recommender.** The softest job on a gang board is a
watch, always, so a first-timer was sent on three surveils running while
the Siphon the advice told them to buy sat unused for ten runs. Two of a
kind in a row is now a lean against a third, and a job the payload you
own was built for is a lean toward it.

**Smaller.** The bench says where scrap comes from (`salvage`), which
nothing did. The safehouse screen shows the whole ladder from anywhere,
so a player in Marrow no longer concludes the cheapest room in the city
is nine thousand eight hundred when a floor cavity two districts away is
a third of that. The second free-action line says what it is (your ticks
running short of the clock, banked) so it stops reading as Tempo in a
different mood. The README's counts caught up.

### D91: The second wave

The three second-wave testers, resumed after the limit: a first-timer
(courier), a mid-game runner (burnout, cheated to a mid build), and a
story hunter (academic). Between them, twenty-eight more findings on the
D86-D89 build. The crash first: the rival incident printed the hook line
for a hook it does not have and fell over on every stranger and enemy,
because the line had ended up under the wrong `if`. My own test called
the branch directly and missed the path; it now goes through
`_apply_incident` for all three moods.

**Loops the first wave did not reach.** `pull` at a sealed record, thirty
times in one run, from the salvage advice, which never read the seal; now
a refused seal is remembered and taken shut. `crack` at one door eight
times at amber; three failures and the brief prefers another door on the
host (`DOOR_PATIENCE`). `connect --present` twelve times (D90). The
"softest thing on the board" said about Sendai at fifty-eight to a
five-run academic, because softest is a comparison: the recommender has a
ceiling now, thirty plus five per finished run, and a door that reads
nought is off the list. Every row reading shut with the nudge pointing at
Signal: the advice names Intrusion when the board reads shut, and the
plan buys at least one rank of it.

**The window that cut the wrong line, again.** `now` shows two city steps
and `jack in` was the third when a job was held, as `take` had been
before D86 and `drop` was behind `burn`. The step that goes (the walk,
`jack in`, `rest`, `drop`) is never cut, and `drop` comes before `burn`.

**Scenes that narrated a history you did not have.** Three stages of Lark
in one visit; "third time you meet him" on the first. One stage per thread
per command now, and `Stage.after`: shifts since the thread's previous
stage, or since meeting the person it requires if it is the first, read
from stamps the story keeps (`when`). Four stages carry it. Scenes also
fire after the district on arrival rather than above it, and arriving
where a scene waits is enough (the nudge said "waiting for you to be
there" and then needed a `look`).

**Honest text.** A choice that costs money you do not have shows the
price and is refused rather than clamping to nought. The street's prompt
reads "a lean: run, talk, stand?" rather than as four options, a verb
with an argument at a street that offers that verb is that verb, and an
empty line stands there whatever the option is called. A topic that opens
a scene prints the scene rather than both. `look` in somebody's off hours
counts the strangers who keep hours here. The talk hint stopped leaking
`kestrel_kid`. The evade sum on a construct closing on you is labelled as
its cover and not left to read as your strike failing. The night-over
exit and the door reason no longer print together, and at red the exit
keeps one working tick of margin, because five times it fired the tick
before the sever.

**Grudges that form.** Four severs in five were the trace filling with no
construct recorded. The last thing that struck you at any point tonight
is what the trace remembers, and the tell says "filed you out" for
something that files and "put you out" for something that hunts. Killing
one is worth standing with the patron.

**The courier trap.** A street build spends its opening experience on
street skills, reads every row of the board as shut at Intrusion 0, and
had no way to earn the rank that opens a door: errands taught nothing,
and the rung the board keeps for a young runner did not read the doors,
so the one "startable" job was the one that had just burned them on the
chair, re-recommended the moment it was dropped. Now the plan buys one
rank of Intrusion whatever the origin, `door_odds` lives with the
contracts and the rung reads it and the history (one definition of "dead
to you", shared by the drop advice and the recommender), an errand pays
a point of experience, and the fallback when nothing on the board is
yours names an errand or a rest rather than listing errands for ever.
Measured on the courier that found it: errand, one rank, a bought Sable,
then three clean nights.

**The chair is clear.** D72 kept the route's added constructs off a
watch's chair and left the ones rolled per host where they fell, and
three first-timers across two waves burned the same watch three nights
running on a Watchman that woke on the chair. A rolled construct on a
surveil objective now moves one hop out, to the emptiest neighbour, so
the danger is on the way in, where D72 put it. No random draws, so every
other network is the network it was; surveil parity holds at nine of
sixteen.

**The loadout plan reads the build.** A Warfare build carries its
weapon; a mask earns its slot against the softest thing on the board when
no job is held, not against nothing; and memory is reserved for the
payload the advice is about to say buy, so two steps are not undone
across a purchase.

### D92: The response arrives

Escalation was a trace multiplier and nothing else. The mid-game tester
sat at red for sixteen ticks on a route whose only live constructs were
sentries and a snare, and the only thing that ever ended a night was the
clock; and because nothing ever struck, nothing was remembered.

Now a room that stays red long enough gets a hunter: after six loud ticks
at red or worse, one from the faction's own pool arrives on the host you
are standing on, awake, named, with a tell, once a run. Loud ticks only,
so a watch that goes quiet at red and waits it out (the brief's own
advice) is not punished for it; the response is for people who keep
working under a red room, which is the loop every tester called dull.
Only from factions that field hunters, which is doctrine (D63 b): a gang
phone tree has nobody to send. The first version counted quiet ticks too
and took surveil parity from nine to one in sixteen, which is the
measurement that produced the rule.

### D93: The way in

The mid-game tester's third idea, and the cheapest of the three. Corporate
work was a tier ladder the build could not climb in the ticks the room
allowed, and nothing said so until the brief announced the zone at the
door, three shifts after the job was taken. The network is deterministic
from the contract, so `board <id>` now reads it and says how deep the job
is before the walk: "their core, about 10 hosts in, 3 badges deep, and the
desk that issues them is on the way". Who holds the desk stays legwork,
because paying for what a fixer knows is a system worth keeping: `legwork
intel` now names the wardens on the route, whether they take credentials,
and what yours would read at against the softest of them.

### D94: More to say

The story hunter's proposal, taken as written: a topic was one static
line for a whole career, so somebody who had learned about the nine logs
from the Archivist got the same answer from Mara as a stranger. `Npc.more`
is (topic, rule, text): the last variant whose rule holds replaces the
line, through the same `satisfied` the scenes use, and `validate.py`
holds every variant to a topic they talk about and a rule something can
evaluate. Six variants on the Deepwater spine to begin with (Mara, the
Archivist, Remnant, Osei), because that is the thread whose facts arrive
in pieces from different people, and the people should know which
pieces you have.

### D95: The door, and the debt

The third wave's endgame tester played the Indentured origin to the door
and could not get there honestly. The buyout of twenty-six thousand ran
at the house rate, three and a half per cent a shift compounding, which
is fifteen hundred a shift by the second week against an income of about
a thousand; a collection every six shifts took the whole account and the
figure never fell. The one decision in the game that is about the debt
("the number comes down by nine thousand") changed no number: the flag
was read by an ambient event and an epilogue line that repeated the
claim. And the hardest of the four retirement conditions was the
cheapest: four bounties came off for one alias fee the shift before.

**Origin debts have their own terms.** A department's paper and a
corporation's are slower and colder than a back room's: 0.8 and 0.4 per
cent a shift, a longer grace, and a fixed instalment per visit rather
than a quarter of the balance, because a buyout is a buyout and not a
loan. **Work for the people you owe moves the figure.** A clean run for
the lender lets them keep a quarter of the fee against it and count it
double, because the work is worth more to them than the money; the
Indentured story is running to afford them, and now it is. **The review
is real.** `Choice.debt` is a thing a choice can do; attending takes nine
thousand off and halves the instalments, which is what "the terms extend"
means. **The name has to have held.** Retiring under a name younger than
ten shifts is a change of address with the old one still on the door,
and the gate says so with the age.

Smaller, from the same report: the collection is on the wire; the debt
screen says the instalment and stops printing the note twice; `repair
--confirm` with the price is the advised step, because `repair` alone
waits; a retired character's sheet says so instead of "running as"; the
help pointer names the topic that exists; and a second character is not
born under the first one's burned alias, because the meta file remembers
every name handed out and the draw skips them.

### D96: The systems say what they cost

The systems tester tried every city verb once, properly, and found the
bench I had broken myself two decisions earlier: the scrap hint had been
indented under the wrong `if`, so `mod` listed nothing to anybody holding
scrap. Fixed, with a test that holds scrap. And the rest: a script's
`jack out` is no longer argued with (the script's own `stop if` is the
argument, and the library's example bailout could not bail out); `burn`
says the fee and the standing that went with the name; `clinic ground`
points at `ground` and `detox`, which exist; `arrange stop` costs the
standing the line always promised; `salvage` does not offer what is on
the deck; `take kick` points at `dose` and `sell out` at `betray`; the
`self` hint names the verb that works; the nudge about a decided rival
no longer offers a bet there is no verb for; and a verb typed at a street
question is told it can wait.

### D97: The corporate night

The corporate tester built the best runner the shops on their seed
allowed (a rating-three forger and mask against posture fifty-eight to
ninety, because no market stocked the tier above), ran sixteen corporate
jobs, and finished none; the control at posture thirty-eight was clean at
tick thirty. Fourteen of the sixteen ended on the clock rule, whose
numbers read true every time. Two of the rest were burns turned into
severs because the rule fired with one tick left and `jack out` costs a
tick: the exit was priced one tick short. And the shape D85 named held:
doors at a hundred per cent and the trace spent on a six-host approach
with a two-tick breaker the clock counted as one.

Nothing here moves a difficulty number. What moves is what the player
can see and what a failure costs the next attempt.

- The exit keeps two working ticks of margin at red, one for the exit.
- The clock reads the breaker's own price: a Lattice is two ticks a
  door, and the board says so beside its odds.
- Lockdown counts every tick toward the response, loud or not: lockdown
  is the response, and a rule met in none of seventeen corporate runs
  was not a rule.
- A failed attempt that never got past the front teaches the target less
  than one that reached the objective (0.15 against 0.4 of their
  hardening), and the wire says the number when it lands: "Posture 72 to
  75, because of you". Seven attempts at one held story job had taken
  Deepwater from 72 to 96 silently, which made the job unwinnable by
  trying it.
- The board's way in carries the clock: "about 30 working ticks in it at
  green, this shift", against "about 10 hosts in, 3 badges deep".
- A grudge that hunts says what answers it (a weapon program, or a route
  round it); one that files says quiet past it.
- `scan` has a hops column, because with Architecture it reaches two
  hops and the table read as adjacency.
- Standing on a late job reads the late fee rather than "you will not
  make it" about a walk of nought; `travel <far> --anyway` names the walk
  with the flag; `repair all` repairs; the deck's heat over its cooling
  is said at the door.

The open question D85 left is still open, and the tester's tally makes
it sharper: at corporate posture a top build's problem is not the doors,
it is the approach, and the shops on a given seed may not sell the mask
that would make it a one-in-four. A named shelf ("Vellum is in Freeport
this week") is the next thing worth building, and it is content.

### D98: The named shelf

The corporate tester's last finding, and the one D85 could not see:
whether a top build can be built at all depends on what the markets
happen to roll. Three to six programs from a pool of sixty-odd, per
district, per cycle, and on that seed no market carried a tier-two mask
or forger in the whole game, so "top build" meant a rating-three mask
against posture ninety. Every market that can carry tier two now carries
one line of it each cycle, the category turning with the cycle
(`SHELF_ROTATION`), so somewhere in the city there is always a real mask,
a real forger, a real weapon. The wire says where the two that decide hard
work are ("The word on the shelves this cycle: Lodestone in Marrow, Vellum
in Freeport"), once you have three runs behind you, and the mask advice
names the walk when the local shelf has none. It is one line of stock, at
the district's own price: the good programs stay something you go looking
for, and now there is somewhere to look.

### D99: And in nights

The endgame tester's second proposal. The epilogue read every decision
back and not one night: a character who had run nine times, been emptied
by a collection and burned a name ended as a list of other people. The
ending now adds two or three lines from the log after the people: how
many nights in the chair, how many paid, under how many names; the best
of them by name and fee; the worst, who cut the line and at what alert,
and whether the construct that did it is still running. Printed at
retirement and at the flatline alike, because the flatline is the ending
most players get.

### D100: The fourth wave

Three testers on the D86-D99 tree: a first-timer regression pass, an
honest Indentured career (no cheats), and a corporate specialist with the
named shelf. The corporate one answered the question D85 left open. On
fifteen identical corporate networks, a hand that pivoted every hop paid
nine nights and reached the core at trace sixteen; the brief, which
offered `pivot` only against a warden it could not present to, paid one.
The wall was the brief. `pivot` costs a tick and no noise and needs no
probe, no crack and no badge, and the brief now walks through every
unopened hop with it once Intrusion 4 is held, searching by pivoting to
the deepest door next to it. Knowledge, not a number: the difficulty is
unchanged and corporate work is now better than one in four for a build
that has earned the rank.

**The first-timer's dead ends.** An open host a warden holds was picked
as the deepest fresh place to look from, seen to be blocked, and the
search gave up on a soft network with a plain open host one hop from the
objective; the search skips them now. A lethal corporate job at thirty
per cent a door was called the softest thing on the board because the
ceiling had risen five a clean night past the door read; a shut read is
a wall, and a bounty on the route is a wall. `arrange` was advised seven
times in a district the faction is not in; it is advised only where they
hold or are, and only with three collections in the account, because an
advised arrangement bled an honest career to nothing. The spend plan
buys Intrusion while the softest thing on the board reads shut, reading
the board the way the nudge does. Patience is counted per host as well as
per door. A dispatched hunter on your host is answered before anything
else is typed. A walk stops when a scene fires, because five scenes and
two decisions arrived in one verb. The escort holding what they came for
is signalled out, not moved fifty-eight times. And a delivery of any
kind, package or person, gets the same honest ways out as the contract
walk when the route is hunted: the escort kind had fallen through to
"rest 1" for ever with somebody waiting to be walked to the Row.

**The honest career.** The buyout went from twenty-six thousand to seven
in fifty-seven shifts on the D95 terms, three Kagawa nights and the
review doing most of it, and then the story was the deck: two severed
nights left three parts at two of three, seven burned nights followed,
and nothing said the deck was why. The run card carries the deck's state
now, `jack in` says when the deck is worn, and the repair advice is only
for what can be paid: at nought credits it named the errand that pays it
instead of refusing forty times. A collection due within a shift that the
account cannot meet is a `now` step. Selling a loaded program takes it
off the deck (it stayed, and counted against memory). The lender posts
work you can do whenever the board has none, because running to afford
them needs somebody to run for.

**The corporate tester's rest.** The clock on the board reads at green,
amber and red, since no brief-following run stays green past tick five. A
multi-tick objective action on a host with something awake is answered
first (strike it, or mask), because a pull woke the black ICE and the
strike landed inside it. A push after the implant has taken is refused
for free. The shelf line reaches the wire. A payload built for the job is
advised before the walk when the local shelf has one.

### D101: The job itself

The fifth wave's corporate follower confirmed the pivot-first brief (two
clean corporate nights in two at posture forty-five once the objective
rank existed) and found the next gap in one sentence: a build that could
walk through every door in a corporate network typed `push` seventeen
times at ten per cent, green throughout, until the trace filled, and
every screen before the chair had said it was fine. The doors were
priced, the room was priced, and the job itself was not.

So the objective verb is priced everywhere the doors are. `board <id>`
has a third read ("the edit lands at 10% with what you carry: Sabotage
and the payload are the numbers"); the recommender treats a tight verb
as a lean and a shut one as a wall; the brief's patience covers `push`,
`wipe` and `pull` as it covers a crack, and after three refusals at under
even odds it names the rank and leaves; the drop reason reads the verb
before the chair. The named shelf's guaranteed mask and forger are tier
two exactly, because "best rating" had landed on a thirteen-thousand-
credit tier three. With a grudge awake on the route and a mask in the
deck, the mask goes on at the door.

And the regression pass on a new origin and seed: a collection errand
could be taken again and again in one shift (nine times, a thousand
credits and nine experience from one doorway), because the offers are
deterministic in the window and nothing marked one taken; each is now
once per window and a collection costs the shift a watch does. The
escort brief treated the job as a place to reach and left with the
escort still inside three nights running; an escort is their pace, and
the brief waits, says whose pace it is, and leaves when they are out.
Counting quiet ticks at lockdown summoned the hunter the tick after the
brief said wait: loud ticks only again at both levels, lockdown quicker
about it, and a watch under lockdown is over. When a bounty walls the
board and the fee is in the account, the fallback names `burn`. No `jack
in` follows a `drop`. The breaker nudge stopped saying "every door you
have failed" to somebody who had failed none. One posture line per run.
And quitting the game at a street question is standing there, settled
before it closes, because the street does not wait for a session either.

### D102: Pictures

Everything the game drew was text: one glyph, one colour, per cell. That
is the D16 ladder and it is right, and it meant the most a faction's
cyberspace ever got was an eleven-by-four mark. A terminal that can do
twenty-four-bit colour can also do two pixels a cell, because the upper
half block takes a foreground and a background and they need not agree.
`pixels.py` is that: a forty-by-sixteen picture in eight rows of text,
composed from a faction key and a seed, deterministically, in the
faction's own colours (a Kagawa terrace is pale green on an amber
terminal too, the way their mark is their mark). Twelve of them, one per
faction, procedural: terraces receding, vessels under glass, a figure in
a black room with one white point above it, a wireframe block with a
texture that never loaded and somebody's tag across it, drips and a hook,
brass jacks, a patrolled grid with a cone of lamp, stacked containers,
a ledger curve, voices converging, snow with a signal through it, depth.

On connect the picture arrives row by row out of noise in its own
colours, where the terminal can animate; where it cannot it is printed;
at 256 colours it is drawn in the cube; at sixteen or in ASCII it is not
drawn at all and the mark stands in for it. `render <faction>` draws any
of them from the city. `rice render` decides how it arrives: the picture,
a wider one earned at five contracts, the mark, or nothing. The flatline
has its own animation at last, the heart trace slowing and going flat
under the wordmark in the error colour, because the game is named after
the moment and the moment ended into a scoreboard. A severed connection
tears the last line on the screen for a moment. Nothing here matters
(D35): a picture is drawn or it is not, and a run is the same run.

### D103: The instrument

The markup can carry a colour now: `[#ff1744]` is a twenty-four-bit
colour beside the palette roles, drawn as itself in truecolour, in the
cube at 256, and as the nearest of sixteen below that, and nothing at
all with no colour. No content uses it; the code does, for the things a
palette role cannot say: a meter whose fill runs cool to hot by how far
along it is, and a sparkline whose every column is coloured by its own
level. The run card's trace history is drawn that way now. And `rice hud
panel`, earned at two contracts, is two lines of instrument after every
tick: the trace as that meter, the noise here as another, the alert in
its own colour, the tick, the focus and the free actions. The one-line
readout stays the default, because it is right for most people; the
panel is for the ones who want the deck to look like a deck. The trace's
own colour is still the trace's own colour everywhere the word appears.

### D104: The schematic

`map` inside a run was a tree: breadth-first from the entry, back edges
listed underneath. A tree is honest and a terminal is good at them, and
it is not a picture of a place. `schematic.py` is: the four zones as
columns from the perimeter on the left to the core on the right, every
host you know as a label in its column, every edge you know as wiring
between them (out along the row, a corner, along the column, a corner,
in), with you marked in the ready colour, the job in its own, anything
awake in the error colour, shut hosts dim, and the route to the job lit
where the rest is dim. It reads the same fields the tree reads and draws
them on a character canvas, so it knows nothing about play (D35). It is
`map`'s default now; `map --tree` is the old list-shaped view for a
narrow terminal or a habit, and `map --flat` is still the list by zone.
The city map is unchanged: it is a real map already.

### D105: Your icon, drawn

The fourth build axis (D18) is the shape you wear in cyberspace, and it
was a line of prose. It is a small picture now, drawn the same two-pixels-
to-a-cell way the faction renders are (D102) but smaller and centred, so
it reads as a figure arriving rather than a scene. Ten of them, one per
icon, each in its own colours: the plain grey outline, the suited
compliance shell with a badge, the person-shaped hole of the Null, the
scatter of the Swarm, the elongated dark of the Predator, the split
Mirror, the carefully-built Deadname, the Process as a titled task with a
progress bar, the low-resolution Night Cleaner with a cart, the Meter
Reader as a grey box with a number. It arrives on connect after the
faction's cyberspace, under "You arrive as something", and it is drawn on
the character's own `icon` screen and when you put a new one on. The
render string stays the caption, so a terminal that cannot draw it reads
exactly what it read before. `rice render` governs it with the faction
pictures, and nothing about it touches the coherence cost the icon
already carries (D35).

### D106: More colour, and a gallery

The palette is the axis people care about most, and it had the twelve
factions and three defaults. Six more, each earned by a different kind of
playing: Sendai (black, white, one red; earned by meeting black ICE and
living), Meridian (ink and gold; twenty-five thousand credits at once),
Chorus (violet and lavender and gold; five threads carried), Freeport
(sea and rust and ochre; twenty errands), Ember (the game's name as a
colour scheme, red on black; fifteen contracts), and Void (one blue a
long way down; all twelve districts). Two of them spend counters nothing
had used,  and . Every one passes the separation
check: no two roles collapse onto the same colour at truecolour or in
the 256 cube. And `rice gallery` renders the same handful of real lines,
a trace bar and a status row, under every palette you own at once, since
the only honest way to choose between colours is to see them next to each
other rendering the actual game rather than a swatch. It refuses a
colourless terminal rather than printing a page of nothing.

### D107: More prompts, and a gallery that renders them

Three more prompt shapes, the most-riced object in the practice: Angle
(guillemets and the trace inside them), Tag (place, hour and account as
labels, the way a log line reads), and Rail (segments divided by an
upright, like a rack readout). Each keeps the hard rule that a run prompt
shows the trace, checked against a live run by validate. And rice gallery,
which renders a status line under every earned scheme, renders the prompt
itself for the prompt axis, so a gallery of prompts is a gallery of
prompts rather than the same status line eleven times. The rice module
header caught up: eight axes now, not seven, and the piece count is
computed rather than remembered.

### D108: A portrait

Appearance is a build axis with a hundred and two features across eight
slots (D33), and on the sheet it was a sentence. `pixels.render_portrait`
composes a head-and-shoulders bust from the ones that can be drawn: the
build sets the shoulders, the dress the collar and its colour, the face
the head and its scars, the eyes their colour and whether they are optics
or blackout or mismatched, the hair its shape and colour, the marks the
ports and ink and subdermal panels. It is not a likeness of anybody; it
is a reading of the feature keys, deterministic from them, so the same
look always draws the same bust, and the skin is a neutral tone chosen
from the whole look's hash rather than from any one feature, because none
of the features name it and the picture should not invent one. It is
drawn on `char` and `self` where the terminal and the render mode allow,
above the written description, which stays the real content so a text
terminal loses nothing. `rice render` governs it with the faction
pictures and the icon, and nothing about it touches presence, heat, or
any other number (D35).

### D109: The way it arrives

The picture reveal on connect (D102) had one animation: rows of noise in
the picture's own colours, settling top to bottom. It is an axis now, the
ninth. Dissolve is that default; Scan sweeps a bright line down with the
picture building behind it, the way a sensor reads an image; Wipe reveals
row by row with no noise; Flash flickers dim and then shows the whole
thing; Instant skips the animation for people who have seen enough. Each
composes only from the finished picture, so no style can show a pixel the
picture does not have, and every one ends on the same image, which is the
whole of D35: the reveal is visible only where the terminal can animate,
and the picture that lands is identical either way. It governs the faction
render and the icon on connect; the portrait and the icon on the sheet
draw instantly, because a sheet is read, not watched.

### D110: The ICE, seen, and the screen disrupted

Two things, one beat. A construct winding up to act is the tensest moment
in a run and it was a line of text; now the thing is drawn. Seven
behaviours, one picture each in its own menace: the Sentry an eye, the
Probe a sweep of pings, the Hunter a locked reticle, the Trap a web, the
Warden a portcullis with a lock, the Herder arrows converging, and the
black kind a skull with a red glint in one socket. It arrives at the
tell, once per construct a run, only once it is identified, because the
shape is a thing you earn the same way you earn its name.

And the display does not stay calm about it. `anim.disrupt` fills the
space where the cursor is with a burst of static in the alarm colours,
shuddering side to side, and then clears it, so a lethal moment reads as
the terminal being interfered with rather than as another paragraph. A
short shudder every time black ICE winds up; a longer one as the trace
completes and the connection is cut; the longest before a flatline, ahead
of the name going flat. It obeys the one rule everything in `anim` obeys:
on anything that is not a live colour tty it does nothing at all, the
render mode turns it off with the pictures, and the words that follow it
are the whole of the content (D35).

### D111: A shape per host in the scan

A scan is the first thing a player reads, and it read as a wall of the
same word. `workstation`, `workstation`, `fileserver`, `workstation`.
Now each host type carries a one-cell glyph in front of its name, so the
table reads as a column of shapes before it reads as words: a door for
the gateway, a diamond for the relay, a house for the workstation, a
drawer of files for the fileserver, a dial for the controller, a lattice
for the auth server, and a locked square for the vault. Boxy things are
infrastructure, the round dial is the controller that reaches into the
world, and the house is somebody's desk. The eye sorts the segment in one
pass and only then reads the labels.

The honeypot is the point of the design, not an exception to it. It shows
as a workstation and it draws the workstation glyph, so the shape gives it
away no more than the word ever did; the disguise is one property read in
one place (`display_type`), and the glyph follows it without knowing the
difference. Every mark is a single cell in both a unicode and an ASCII
form, so the column stays true on a plain terminal (`> - . = * # X`) and
never goes ragged. It touches no number: the glyph rides the type cell and
nothing else, the host id a player types back stays clean, and `validate`
and `test_host_glyphs` hold both. `HOST_GLYPHS` lives with the node
content it describes, keyed by the name the player sees.

The glyph then carries everywhere a host shows its type, so a host reads
as the same shape wherever you meet it. `here` and `probe` put it in the
node header. `map --flat` carries it beside the type word exactly as the
scan does. And the schematic leads every label with it, so the map reads
as a field of shapes: you can see the vault sitting in the core before you
read one host id, marks and name following the glyph (`▣ !vt-core01`). The
schematic gains a second legend line, a key that names only the glyphs
actually on the map and grows as you find more, so nothing on screen is
ever a symbol you have not been shown. One helper, `_host_glyph(caps,
node)`, is the single place the caps decide unicode against ASCII, and the
scan, the two map views, the node header, and the rank-two `chart` all
read through it.

### D112: The boot draws a city

The opening was already the best cold start it could be as text: a
power-on self test that reads the deck you actually own, the wordmark
decrypting into place, and the heart trace beating and then going flat
under it. What it never did was use the one thing the visual layer was
built for. A terminal that can do the pictures (D102) can do a full
twenty-four-bit image, and the boot is the one moment where showing that
off is the whole point, because a player who has never seen a picture in a
terminal should not get to the prompt before they have seen one.

So the boot now comes up on a city. A night sky over a synthwave sun with
its scanlines, a skyline of towers with neon rims and windows that come on
a bank at a time as the machine powers up, dark water under it holding the
horizon glow and the lights thrown back. Then a sweep of light crosses the
water, and only then does the wordmark decrypt in beneath it and the trace
begin. The city is drawn in the player's own accent, so the palette they
earned themes the title. It obeys every rule the rest of the layer does:
it is composed from a fixed seed and touches no game stream (D35), it is
drawn or it is not (truecolour and 256 get it, sixteen and ASCII get the
wordmark alone), a terminal too narrow for the full mark gets the quiet
boot, and a minimal banner (none, small) reads as a request for a quiet
start and is honoured. `anim.scene` builds the pixel grid, `scene_rows`
blits it, and both sit above the wordmark in a shared `head` so the title
does not jump when the motion ends. `test_the_skyline` holds the power-on,
the theming, and the degradation; the existing boot matrix, which already
runs every banner at every rung and width, now runs it against the city
too.

### D113: The icons become a bestiary, and four more to buy

The player icons (D105) were drawn as little people seen from the chest
up, and at twenty-two by sixteen pixels a bust reads as a lump however it
is cut. Two rewrites in, the fix turned out to be a change of subject
rather than of craft: an icon is not a portrait of you, it is the thing
you choose to *be* in the net, so each is now its own creature or
character, read by silhouette. Plain is a plain person, and everything
else is what a runner wears instead of one: Compliance Shell a suit with a
briefcase, Predator a wolf in profile, Swarm a cloud of bats, Mirror a
figure and its reflection across a seam, Deadname a stranger worn with a
ghost of themselves behind, Process a boxed daemon, Night Cleaner a worker
with a broom, Meter Reader a gauge on legs, Null a person-shaped hole. A
shared `_biped` draws the standing figures and the specific ones hang
their details off it; the animals and machines are drawn bespoke.

And four more to carry, each its own shape and its own reason. **Wraith**,
a ghost: evade and quiet, too thin to feel a tell coming. **Ronin**, a
horned-helmet samurai with a drawn katana: damages ICE and slips a lunge,
loud about both. **Seraph**, a winged, haloed figure: reads as standing
nobody questions, and draws heat for the glow. **Reaper**, a hooded skull
with a scythe: steadies you against black ICE and frightens what watches,
at the cost of being the least deniable thing in the room.

The pictures are the surface. Underneath, an icon has always been a real
build axis (D105): `icon.effects` and `icon.penalty` merge straight into
the character's live modifier stack, and a coherence penalty stacks on top
when you wear a shape further from human than your Dissonance can carry.
Each new icon is a content entry with genuine effects and a genuine
penalty and no new engine rider, and each shows up in `icon` and at the
workshop with no other wiring, because the system was already keyed off
`ICON_KEYS`. `check_icons`, `test_player_icons`, and the effects
vocabulary hold all four.

### D114: A play-test of the story and the quests

Three play-testers, one brief each, on the story and quest layers only: a
story-follower who lives in `now` and chases threads, a completionist who
works the board and reads every job, and a lore-reader who talks to
everyone. All three landed on the same verdict, which is worth writing
down because it is a good problem to have: the story content and the world
writing are the strongest thing in the game (deep, interconnected, no
placeholder text, and still not one em dash in the whole corpus), and the
one real failure is that a new player following the game's own guidance
can miss it, because the story spine gates on two completed runs and the
signposting pointed the wrong way for that first window.

This decision is the honest, cheap half of the fix, verified in-game:

- The journal's empty state told a new player *"things start when you meet
  people, `look` around,"* which is the one thing that does not open a
  thread yet; it now says the truth, that the stories open as you run jobs
  and cross people who are mostly in other districts.
- `waiting_on` would name a far wall (*"waiting on What Deepwater Is"*)
  from a later stage while the actual next scene was one `ask` away, so a
  diligent reader walked away from content they could reach. It now stays
  quiet whenever a thread has a next scene the player can trigger where
  they stand, and only names a wall that is genuinely a wall.
- `ask <name> about <topic>` was rejected though the command calls itself
  "ask somebody about something"; a leading about/for/on/of/re is now
  skipped.
- Payload was documented on `exfiltrate` alone though `implant`,
  `corrupt` and `wipe` need one too, and wipe's *"does not need carrying
  out"* read as "needs no program"; all four now say it, and wipe says it
  plainly.
- The jack-in refusal said *"a exfiltrate contract"*; the article is
  vowel-aware now.

A second pass then took the harder half. `now` carries one quiet line for
the first two runs, before the spine has found the player (*"the city has
a story, and it starts to find you once you have a couple of runs behind
you"*), and `journal` is in its verb list so it is reachable. The board
caps any one faction at two of five, so a night is a choice of who to hit
rather than a theme. The guaranteed soft slot picks its faction from the
pool a young runner can actually start against rather than always the
single softest one, and its objective from what their kit can run rather
than the first ready, so it rotates instead of reading as a template. And
the board reads the objective's own name: surveil is `surveil`, not
`watch`, so one job stops wearing three words. What is left is smaller:
the shared job-name pool still repeats across unrelated jobs, `news` can
stack one rival, and the people table clips its taglines. `factions` is
now an alias for `rep` on the way past.

### D115: The cold open

Most people who try this have never played a text game, and the shape of
the opening was working against them: make a character, read a stat sheet,
spend points, then eventually run a job and, several runs after that, meet
the writing and the story that are the actual reason to be here. The best
of the game was the last thing a newcomer met, behind the most
paperwork-shaped part of it.

So the game now opens on a job, before there is a you. `begin` drops the
player into a short heist as somebody else, wearing a dead runner's deck
and her name, with a voice called Switchboard in their ear and the trace
climbing. Four beats, the real verbs (`scan`, `crack`, `grab`, `jack
out`), each taught by being made to do it once: the three hosts resolve
out of the dark with their type glyphs, the fileserver holds and then
gives, the grab wakes something and the screen takes a hit of static, and
the last beat is getting out alive. It ends on the hook the whole game
turns on, a word in the ledger nobody was paid to read (`Deepwater`), and
then the only question that was ever the point: the next one is yours, who
are you? Straight into guided creation.

It is a scripted scene, not a real run (`prologue.py`), and that is the
point of it: it never touches the combat maths, so it cannot stall or fail
on somebody who has never typed at a game. Whatever they type moves it
forward, with the word they were reaching for shown, because a hook that
punishes a wrong guess is not a hook; `skip` bails straight to creation.
It teaches the real vocabulary and shows the picture layer (D102) in the
first ninety seconds, drawn or degraded by exactly the same rules as
everything else, ascii-clean where it must be. The splash leads with it,
`new` and `tutorial` behind it. `test_the_cold_open` holds the rails, the
handover, and that it never gets stuck.

### D116: Two beats a run was missing

The run had grown visually rich over D102 to D111: a picture of the
faction on connect, the ICE drawn at its tell, the network as a drawn
schematic, a glyph per host, a static burst at the lethal moments. What it
still lacked were the two emotional tentpoles of a heist, the spike and
the payoff, and both were a line of text among other lines.

So the room turning red takes the screen now. `escalate` fires the static
burst (D110) on the crossing into red or lockdown, and only on the
crossing, so a run already red does not stutter on every further step. It
is the tensest moment in a run and it now feels like the terminal being
interfered with rather than another paragraph. And the objective coming
loose is a moment: pulling the thing the whole run was for prints a framed
`secured` beat rather than one grey line among the pulls. Small, rare, and
exactly where the run wanted a breath of punctuation.

### D117: Ambitions, the ladder between a job and the story

A run is a night; the thirty-five threads are the years. Between them the
game said nothing about what a player was building toward, so a newcomer
who had learned the loop had no next mountain, and the honest answer to
"why keep playing" lived in scenes they had not found. The story is the
long answer. Ambitions are the visible ladder to it.

Seven of them, in order: get on your feet with a job behind you, be
properly equipped with a payload of your own, make a name one faction
remembers, become somebody in particular with a skill three ranks deep,
find out what Deepwater is, sit on a stake worth keeping, be still
breathing on the seventh night. Each is a predicate over state the game
already tracks, so nothing new is stored except which ones are met, and
that rides in the story's own flag set (`won:<key>`), which already saves.
`ambitions` (also `aims`, `goals`) lists them with how far along you are,
and `now` names the next one still open once you have a run behind you, so
there is always a next thing worth wanting on the screen.

Meeting one prints a beat and, where money is the wrong reward, a small
recognition bounty; where the thing itself is the reward (the kit, the
skill, the answer) it is a line and no more. One lands per breath, so a
veteran's first load drips its back-catalogue rather than dumping it. The
manual's own topic says the quiet part out loud: the ladder is not the
story, and the good careers spend some nights on each. `ambitions.py` and
`test_ambitions` hold it.

### D118: The lifeline

The one thing a person who has never played a text game needs is to know
the blank prompt is not a test they can fail. The game already answered an
empty line with the next move (D50) and pointed at it from the splash, the
creation blurb and every unknown-command error, but all of those are one
line in a wall a newcomer skims, and the prompt itself said nothing. So a
brand-new runner now gets a fading reminder under the prompt: *lost? press
Enter, or type `now`, for what to do next.* It shows a handful of times and
then stops, and it stops for good the moment they use it or finish their
first run, and it never shows during a run, on top of a waiting question,
or while the tutorial is already holding their hand. A hand on the shoulder
for exactly as long as somebody is new, and gone before it could become
nag. `test_the_lifeline` holds the fade and every one of the silences.

### D119: The reckoning

The rival system already did the hard half well: run the board faster than
somebody for a campaign and you make an enemy of them by nothing more than
being quicker, disposition sinking three points at a time until it latches
into a nemesis with a scene of its own. What it had no second half of was
an ending. A nemesis was a weather system with no season: heat every few
shifts, and the only way to make it stop was to pay them off, which is a
transaction and not a resolution. A rivalry that cannot end is a chore,
not a story.

So once the grievance goes deeper than the declaration and stays there
(past `RECKON_AT`, which takes a campaign of being crossed to reach), the
nemesis stops working through the city and comes to find you in it, in the
same words the street already uses (D65): [fg]face[/] them, [fg]settle[/]
it, or [fg]walk[/] and leave it for a night you are readier for. Facing
them is a printed sum like any street check, nerve and your name and what
you can do against how good they are; win and something goes out of them
that does not come back, lose and they take the inch in front of people it
travels to, and either way the score is settled and the bond comes off,
because standing in it is the ending whichever way the roll goes. Settling
is real money and a clean peace. Walking leaves it for another night, and
it comes again.

It reuses the confrontation machinery whole (`world/rivals.reckoning_begin`
mirrors `world/street.begin`, the `Check`, the question), fires from the
city story hook only when nothing else is waiting on the next line, and
remembers itself in the story's flag set (`reckoned:<key>`), so a settled
score stays settled. `test_the_reckoning` holds the trigger, the three
answers, and the silences.

### D120: The nemesis in the run

The reckoning gave the rivalry an ending; this gives it a middle you can
feel. A nemesis was real on the board and in the wire and in the heat they
added on the shift boundary, but never in the one place the game actually
happens. D89 already let a rival turn up inside a network, chosen at
random and mostly atmosphere. Now, if you have a nemesis, the runner who
turns up in there is them, and they did not come second on purpose.

It is a race. A nemesis in the run is after the same thing you are, and
every tick you spend not securing it, they get closer. A few ticks in they
warn you they are ahead; a few more and, if the objective is still not
yours, they reach it first and take the part that was worth coming for,
leaving it worth sixty percent less and the alarm tripped behind them.
Beat them to it and it is a win they will not forget, which in this
business makes an enemy worse rather than better: the disposition drops
harder for having lost to you in their own back yard, which feeds straight
back into the reckoning. So the nemesis is the one rival whose arc runs
board, wire, network and confrontation, and every stage of it points at
the next.

`_rival_race_tick` rides the tick loop beside the response and the ICE, on
`objective_met` so it settles the same instant the job does; the outcome
rides out on the run summary the way the old company incident always did,
and the post-run disposition reads it. `test_the_nemesis_run` holds the
race, the warning, the theft, and beating them to it.

### D121: The partner, the other way

The nemesis got a whole arc: the board, the wire, the network, the
reckoning. Its mirror was already half-built and thin. A partner (the
positive end of the same disposition number) relieved heat on the shift
boundary and, if you signed them to a crew, ran beside you; but a partner
who turned up uninvited in a run was passive noise cover and no more, and
the relationship had no culmination the way the enmity now did. So the two
missing halves, to match.

In the run, an uninvited partner is a felt help, the exact mirror of the
race: they came for you the other way, and they hand you what the state
you are in most needs. Trace high, they make themselves the loudest thing
in the room and it turns to look at them instead of you; a room already
deciding about you, they walk something loud the wrong way and it loses
the thread; otherwise they leave you what they found on the map. It reads
off the same summary the company incident always did, deepening the bond
the way beating the nemesis deepens theirs.

And the culmination: a partner deep enough comes to you and offers to run
for good, the mirror of the reckoning coming to settle. Crewing was always
a thing you went and did to somebody willing (`crew take`); this is the
other direction, the one that reads as a relationship and not a hire. They
waive the retainer, because past a certain warmth the money was never the
thing, and `yes` signs them on for nothing, `no` leaves the ordinary door
open. That ties the whole ladder together: a [fg]hire[/] is one job, a
[fg]partner[/] is the bond that starts helping unpaid, and a [fg]crew[/] is
the partner who stays, reached now from both directions. `test_the_partner`
holds the boon, the offer, and both answers.

### D122: The ways in

Every job was one run. You took a contract, you jacked into its network,
and you cracked your way to the objective, and the only variable was which
programs you carried. The social and economic halves of the character
sheet, Guile and Subterfuge and money and who you know, barely touched the
job itself. So a job is three runs now, and you pick which before you go.

`approach` reads the contract and lays out the ways in. **Breach** is the
old loud way through the net, always there. **Social** talks you in on
Guile and Subterfuge, better the more of a face you wear (a Compliance
Shell is worth points here, D113 paying off), and a shift of being
somebody who belongs there brings you up *inside*, with the route to the
objective open in front of you and only the last thing left to do; blow
the con and your face is made, they harden, and you go in hot. **Inside**
buys a way past the perimeter through somebody who works there, on money
rather than skill, handing you the whole map and a door at the wall and
one thing put to sleep; on a corp or somebody who hates you, the door they
sell you is a door they can sell twice, and you can walk into a trap.

It is a head start, never a free win: the objective is always still yours
to do. The `Contract` carries the committed `approach` (saved), the city
command resolves the check or the payment and spends the shift, and
`_apply_approach` shapes the network at jack in from the same primitives
legwork already used, open nodes and a granted tier and a revealed map.
`now` points a held job at it. That is the biggest single lever on depth
in the game: a build now expresses itself in *how* a job is run, not only
in how well. `test_the_ways_in` holds the round-trip, the build-sensitive
odds, and all four grants.

### D123: The way back in

A run's decisions were all tactical and all spent inside the same hour:
which host, which service, when to run quiet. None of them reached past the
jack out. `plant` is a decision that does. Two ticks in a host you hold
leaves a quiet way back onto that faction, and it costs the one thing a run
does not otherwise let you spend on purpose: evidence. It leaves a lot of
residue, which is heat and a grudge later, and it is a bet that the future
is worth the present.

The payoff is a self-made version of the inside job (D122): the next run
against that faction comes up past the wall, on a map you already have,
through a door you left open. But a network that has been walked hardens,
and a way in you did not close is a way in they eventually find, so each
run on them rolls whether the backdoor still holds. Found, it burns, they
harden, and they look harder for a second one. It is the reason to run the
same people twice, a long game laid over the short one, and the first
in-run decision whose consequence is a different run entirely.

It rides on the persistent city the way grudges do (`City.backdoors`,
faction to the shift you planted it, saved), reads at jack in from the same
primitives the approaches use, and surfaces on the approach menu as a way
in you already own. `test_planting_a_way_in` holds the save, the grant, and
the burn.

### D124: The changing world

The city reacted, everywhere and always, but it never *moved*. A robbed
faction hardened and cooled again; nothing in it rose or fell over a
career. There was no shape to a campaign, no sense that being in this city
for thirty runs left it a different city. So factions have a grip on it
now, a hold that a campaign actually shifts.

Every faction sits somewhere on the power map, higher if it is a corp or
the law, lower if it is a gang or a cult, and its grip drops when it is
robbed, by you and by the other runners both, and climbs back toward its
place slowly, so a campaign against one target compounds into something
visible: rob the same people enough and you watch them lose their hold,
and the wire says so when it crosses the line, and the ones who watched it
happen move into the gap. `world` (also `state`) is where you see it: the
map ranked by grip with each faction rising or falling and how they feel
about you, then your own mark on it, the ways you have left open and the
grudges you hold and who you have cost the most, then where the tension
is, the spine and the nemesis and the partner. A dashboard of a city that
your career has bent, and a long-term reward that is not a number going up
but a shape you changed.

It rides the persistent city (`City.grip`, faction to its hold, saved),
drops in `apply_run` and in the rivals' own turn, recovers in
`_decay_posture` beside the posture it mirrors, and reads mostly off state
that already existed. `test_the_changing_world` holds the baselines, the
drift, the recovery, the save, and the dashboard.

### D125: Swagger, and the legend

The game was grim, and good at it, and it had a wry and an absurd streak
already, three named tones on a budget the build enforces. What it never
did was let the player feel like they were any good. Everything happened
*to* you. The one thing a heist fantasy has to give, that you are the best
in the room, was the one thing missing, and the grimdark carries better
with that light to throw its shadow. Not the light of a hacker in
sunglasses shouting a slogan, which would break this particular voice.
The light of a professional enjoying, quietly, being a professional.

So a run that goes clean now hands you, sometimes, a line to enjoy it by:
you were out before the log finished the sentence it was writing about
you; somewhere a very expensive system is generating a report that
concludes, at length, that everything is fine. And once you are worth a
story, the city starts telling one when you are not in the room: a name
that might be yours used as a verb by people who have never met you, a
fixer quoting a higher price for a job without you on the theory that
anybody who is not you is a downgrade. Kept dry, kept rare, and never
before you have earned it. A handful more of the wry and the absurd went
into the ambient weather on the same budget, because the answer to "does
the comedy hold up" is that it does, and there can be a little more of it.

`SWAGGER` fires off a clean run in `apply_run`, `LEGEND` off the shift's
ambient wire once `alias.runs` is past `LEGEND_AFTER`, both kept to one
beat and both in the deadpan key. `test_swagger_and_legend` holds that
they fire when earned and stay quiet before.

### D126: The lifepath

The twelve origins each already carried a complication, a promise printed
on the sheet at creation: the Sixes consider you theirs and will ask; the
Vertical wants the laptop back; Mara is owed something and has never said
what; there is a package you never delivered and the person who gave it to
you has been dead two years. Strong hooks, and until now they sat there as
prose, the way a lot of character-creation flavour does, true and inert.

So the complication comes to find you now. After your first job, once, the
origin you chose stops being a line on the sheet and becomes a thing that
is happening: a message that is worse for being polite, a drink you did
not order from somebody who does not sit down, a statement delivered by
hand because banks do not do that, a hymn from a doorway that stops when
you turn to look. Twelve openings, one a piece, each the first instalment
on the promise that origin was, fired off `runs >= 1` because a first job
is what puts you back on the radar of whatever you came from. It is the
cheap, honest half of a lifepath: not twelve separate campaigns, but the
thing you started as reaching into the thing you are becoming, so the
choice at creation has a consequence you meet in play rather than only a
number on the sheet. `ORIGIN_OPENING` holds them, `_check_origin_past`
fires them, `test_the_lifepath` holds that each is its own and each comes
once.

### D127: Tactic tools

Sixty-eight programs and forty-seven pieces of chrome, and every one of
them made you better at something you could already do. Not one taught
the deck a verb. The catalogue had breadth to spare; what it lacked was a
piece of gear that changed how a run was *played* rather than how well,
and the honest reason it lacked one is a design rule worth keeping (D10):
techniques come from trained rank only, because an implant that grants
Intrusion should make you better at cracking, not teach you to Pivot, or
the whole skill system becomes purchasable with money.

The way through is the way payloads already worked. A payload does not
teach you to exfiltrate; the tool does the work, it costs a memory slot,
and without it loaded the verb is not there. So two tools, each opening a
verb that otherwise does not exist. **Shroud** (mask, tier 3) enables
`ghost`: a few ticks off the network's read entirely, trace frozen and
every lock on you let go, the move a pure stealth deck is built around and
no use to one already seen. **Sledge** (weapon, tier 2) enables `crash`:
end the host you stand on rather than defeat it, every service open and
every countermeasure dead at once, at a price in alert the whole room
hears. Two decks, two ways to play, chosen at the market and paid for in
memory, and neither one a technique: `has_technique` still reads rank
only, and the tools are gated on carrying them (`_tool`), which is the
rule kept and the gap closed at once. The catalogue audit's loadout check
held the line too: a mask is silent by design, and the first draft's
Shroud broke the parity, so its cost lives in the verb and not the
signature. `test_tactic_tools` holds both verbs, both refusals, and that
neither is a skill.

### D128: The street can be fought

D2 said no guns and no street fights, and for a hundred and twenty-six
decisions it held, and the street layer (D65) was built under it: a
street that could kill you, under the same contract as black ICE, and
that you could only run from, talk to, pay, or stand in. The author,
reading that back on 2026-09-03, did not like the rule, and the honest
reason it deserved unliking is that danger without agency is weather. The
street could end a character and the character could never once push
back, which is fine for horror and wrong for the game this is trying to
be. Unlocked, then, at the author's call, with the half of D2 that
matters kept in writing at the top of this document: **combat is a way to
survive the street and never a way to do a job.** You cannot shoot your
way into a vault. The net stays the whole of the contract layer.

**Never the only thing on the menu.** `fight` is added to every encounter
with people in it, beside the answers the street already had, and it is
not added to a stair with a step missing or a pot of soup
(`NOBODY_TO_FIGHT`). Nobody is ever made to fight. `break` is on every
round of one, at a price, so starting a fight never removes the way out.

**Two routes in, which is two builds.** *Violence*, the fifteenth skill
line, Grit's fourth: hands, a blade, a gun. Its techniques, from rank
only per D10: *Finisher* at 2 (`finish`: one hard check that ends it once
they are below half, and leaves you wide open when it does not) and
*Menace* at 4 (`menace` on the street: let them see what it would cost,
and they leave, or they go first). And `jack`, the netrunner's fight,
which is the most on-brand thing in the pass: the deck against their
chrome, read by Warfare and the weapon program you have loaded, and no use
at all on four kids with one knife (`UNCHROMED`). A pure runner fights one
way, a bruiser another, and the player has to read whether there is chrome
in them before choosing.

**An exchange, not a check** (`world/fight.py`). Rounds: `strike`,
`guard` (sets up the next strike), `jack`, `finish`, `break`, each a
printed check, and then they hit you, less armour. Their pool and their
hit scale by tier (4/7/11/16 to get through; 1-2 up to 5-8 a hit), so an
untrained, unarmed runner can take a lean and cannot take a press, and a
trained one with a blade ends a press in a round or two. No round of a
fight kills you: a lost fight is the encounter's *worst* outcome, through
the same `_apply` as everything else, so at the top of the ladder it warns
first and then does not (D6). Eight rounds and the street has noticed;
they break off, and so should you.

**What you carry** (`content/weapons.py`, a fence's shelf): five things,
one axis. Knuckledusters, a blade and a shock baton (a hit halves their
next) are quiet; a pistol and a smartgun (needs neural chrome or it does
not know you) are loud, and a loud one drawn is a Nightwatch matter every
time, won or lost. `carry` shows, swaps, and puts it away for a street
where being seen with it is the problem. Dermal weave and subdermal
plating are chrome that eats a point or two of every hit (`armour`, a new
modifier key).

**What winning costs, which is what makes it a route and not a cheat
code.** Beat a faction's people: heat, standing, a flag, and the next of
theirs you meet is a tier up (`on_arrival`), all the way to the kind that
kills. Win at that rung and you have killed somebody: the *blooded* mark,
law heat, a `killer` flag. The Integrity you spend here is the number you
jack in with, so a runner who fought their way home runs bleeding, which
is the best cross-layer tension in the game and came free. The reckoning
(D119) can be settled the other way too.

Two things found on the way. `stand` read Nerve as a *skill* for the whole
life of the street layer and found nothing, and the ladder was tuned
around that; rather than rebalance twenty encounters by accident, the
third term is now Streetcraft, which is what it was in effect, and
`check_for` reads an attribute as an attribute for the answers that need
one (`fight`, `front`). And the tone piece from the consult lands here as
`front`: the bluff, Guile, Streetcraft and Nerve against the tier plus
two, once you have three runs to front with, standing when it lands and a
worse beating when it does not. `test_the_fight` holds the menu, both
routes, the way out, the contract at tier four, the kill, the escalation,
the bluff, the look, the shelf, the save, and the reckoning.

### D129: The rough street

The play-test for D128 was a fighter's campaign: thirty-six travels each
for a cold runner, a warm one, and two hot ones with a blade and a pistol
and heat in the fifties. The cold runner met the street once. The hot
fighters met it *never*. The author's original worry, that the overworld
was too safe, turned out to be true by construction rather than by
tuning: arrival danger was keyed entirely on faction heat, which decays
every shift and counts only in districts where that faction has people,
and the street's own texture fired at a fixed eighteen percent and only
ever at tier one. A runner nobody was looking for could cross the
Shambles at night three dozen times and be bothered once, by somebody who
was not good at following.

So the street has teeth of its own. `rough(game, district)` is a
district's danger on its own account: security inverted, by the hour, and
the hour runs the other way from the faction clock (an afternoon has more
people to recognise you; the street's own people come out at night).
`texture` scales by it, offers a press where it is rough and a taking
where it is worst, and now also fires in the middle band where a warm
runner used to get a warning and nothing else. A rough night's sleep
reads it too. And when somebody is paid to find you it is people four
times in five, not the old ladder, because a beating you cannot answer is
a worse thing in a game where you can.

Four encounters for it, nobody's: the toll on the walkway (six of them,
nineteen, a trolley and a card; nothing to jack), the man in the frame
(eleven thousand credits of crane and none of it a brain; chrome to reach,
at night), somebody who heard (a callout, for a runner with four runs to
have been heard about), and hired (three professionals with a van and your
handle spelt right). `test_the_rough_street` holds the roughness order,
the firing rates by place and hour, the tiers, and the four.

### D130: More of the shelf, more ways to fight

D128 shipped the exchange with a deliberately small shelf; the play-test
liked it and the direction was to widen it. The constraint that shaped the
pass: the skill system caps every line at two techniques, ranks 2 and 4
(`check_skills` enforces `[2, 4]`), so there is no third Violence
technique to add. New *ways to fight* therefore come the way D127's tactic
tools did, as gear that grants a tactic (a tool, not a technique, so D10
holds), and by wiring techniques that already exist into the new system.

**Three more carried, one fitted.** The cleaver (quiet, tier 1, cheap and
crude), the scattergun (loud, tier 2, rider `spread`: while they are still
bunched a hit reaches the ones behind), and the monowire (quiet, tier 3,
rider `reach`: a landed strike keeps them at the far end of the metre and
they do not hit back that round). And the wolvers: not carried but fitted,
a limb implant that grants a weapon (`weapons.CHROME_WEAPONS`), always in
hand, never dropped, read from `granted(installed)` when nothing is
carried. Nine weapons now, eight on the fence.

**Two more armours.** Bone lacing (tier 2, armour 1 and a lot of
Integrity, the durable middle) and milspec trauma plate (tier 3, armour 3,
the endgame, heavy in the chair). Armour now spans one to three across
four implants.

**A talker's way out of a fight.** A Face (Streetcraft rank 4), which made
talking on the street easier, now also puts `talk` on the fight: Guile and
Streetcraft against the tier, easier once they are hurting and would
rather stop, and a success ends it clean, with no heat and no grudge,
where a break-off is scrappy and remembered. It works once; a failed
talk-down is a beat you spent not covering up. That is an existing
technique reaching into the new system, which is the honest form of "more
techniques" the two-per-line rule allows.

`check_weapons` holds the shelf (a loud and a quiet option, every rider
read, a fitted weapon that never reaches the fence); `test_the_fight`
grew the reach, spread, fitted-weapon, and talk-down cases.

### D131: A fighter's living

The direction after D130: more armour, more weapons (a bat, a katana, a
switchblade were named), combat chrome, *style*, everything buyable or
findable, and then a balance check, because a route the game offers has
to be worth the points or it is a trap with a shelf.

**Styles.** Three weapons that each carry a way of fighting: the bat
(`stagger`: a landed blunt hit takes their next one down), the katana
(`edge`: a point on the swing and it crits sooner), the switchblade
(`concealed`: the first strike of a fight goes in easier, because there
was nothing to see). With the earlier riders (stun, spread, reach,
smartlink) and six pieces of chrome that fight (a targeting suite that
lands strikes, muscle grafts and hydraulic arms that make them count, a
reflex booster that covers up, an adrenal pump for the first second, a
pain editor that keeps you moving when hurt) the shelf and the clinic
sort into four styles, named in the manual: blunt, blade, gun, tank, and
the netrunner's `jack` beside them. Three new modifier keys
(`strike_bonus`, `strike_damage`, `guard_bonus`) and two riders
(`pain_editor`, `adrenal`), all read.

**Worn armour** (`content/armour.py`): a ballistic jacket, a riot vest, a
plate carrier, from a market or a fence, on and off with `wear`, and it
adds to the fitted kind to a cap of four, past which you are wearing a
room. `armour_of` is the one sum the engine and the sheet read.

**Found, not only bought.** Half the time, what the people you beat had in
their hand is in your bag afterwards (`street_content.LOOT`, by
encounter): a switchblade off the kids, a bat off the walkway, a pistol
off the hired, and somebody who heard carried a katana. A fence buys it
back, or you carry it.

**A living.** A won fight teaches (`FIGHT_XP`: a lean nothing, a press
one, a taking two, the kind that kills three, against a run's four to
seven), and in a district rough enough, `errands` offers *muscle*: stand
in a doorway for somebody, a fight at the tier the street deserves, paid
if you are the one still standing and half if you talked it down. A
partner (D121) stands beside you in a street fight and puts one down
some rounds. And the line under the district name says how rough the
street is at this hour before it has its say, which is the scouting a
runner does with their eyes.

**The balance check.** A simulation of eight builds against the ladder
(`stylesim.py`): at Violence 3 with a style's kit, every style ends a
press in a round, wins a taking at 94 to 98 percent, and loses to the
kind that kills, which is the endgame's rung; a runner with no points and
a katana wins a press but a taking at 9 percent, so the points are what
the third rung costs; the netrunner's route at Warfare 4 matches the
muscle styles at Violence 3; and the full kit (Violence 5, hydraulic
arms, trauma plate, a carrier, forty experience and twenty-seven thousand
credits) owns the top of the ladder at two rounds and a little blood,
after two nudges: crits are half again rather than double, and the kind
that kills wears something too (`FOE_ARMOUR`). Muscle pays 680 to 1,500 a
shift against a run's 1,400 to 9,000 every two or three; the street is a
living, and the net is still the money, which is the right relationship
for a netrunning game with a street you can fight.
`test_a_fighters_living` holds the shelf, the styles in the sum, the
armour cap, the chrome, the loot rate, the lesson, the partner, muscle
work and where it is offered, and the roughness line.

### D132: The help, current, and a clean-up

The direction after D131: run a clean-up and make sure the help is up to
date. An audit of the forty-four manual topics found nine that the combat
layer had made incomplete without touching: chrome (nothing about the
chrome that fights or that four implants are armour), heat (a loud weapon
and a kill are Nightwatch heat), rivals (a partner beside you; a reckoning
can be fought), death (a fight at the top of the ladder is the one that
can end you), money (a fighter's money), techniques (which of the thirty
matter in a fight), attributes (what each governs on the street), basics
(the other half of the game can be fought and never has to be), and
appearance (the blooded mark). Each got a paragraph. The tutorial's `help
street` line says "and the fights". The guide learned two fighter's nudges
(muscle work on offer here; you fight with nothing between you and the
hit). The README's counts were regenerated from content (fifteen skills,
thirty techniques, six for the street, twelve weapons, three things to
wear, twenty-four ways the street stops you) and it has a paragraph on the
street that can be fought. Two docstrings that still said nobody throws a
punch were amended, a helper renamed, a duplicated branch merged.

One rule learned on the way, now in the plan where the next author can
find it: in manual prose, backticks are for *shell commands*, and the
validator checks every one against the registry; an answer typed at a
prompt (`run`, `fight`, `strike`, `front`) is marked `[accent]` instead.
`test_help_is_current` holds the nine topics, the README's numbers
against the content, and the fighter's nudge.

### D133: The match

The direction after the combat pass: make the rest of the game meet it, so
it does not feel bolted on. An audit found where it was. The net had
conditions ("tonight, inside") and the street had none. Twelve drugs and
not one for the street, and the fight did not read your chem at all: you
could fight on a comedown at full strength. Twenty-nine traits and two
that touched the street; character creation did not know fighters exist.
And the clinic fitted chrome and took habits off you and would not patch a
cut.

**Chem.** Redline, a fighter's stimulant off the back of a fence: harder
strikes and a point on the swing, then a crash that takes aim, reflexes
and three Integrity. Numb, a clinic painkiller in a street dose: a point
of armour and Integrity to spend, and while it is in you being hurt does
not slow you, which it does by carrying the pain editor's rider (the drug
does what the chrome does, for a shift). Drug highs already reached the
fight through the attributes; what was missing was the fight *saying* so,
so any comedown in progress is a printed "coming down" term on every
strike, guard and break.

**Traits.** Raised Fighting (a rank of Violence and harder strikes; you
have never talked your way out of anything, a rider the fight reads),
Glass Jaw (hard to hit, and it goes all the way in), Thick-skinned (a
point of armour, slow to move), Bloody-minded (a point on the strike; you
do not cover up). And Cold, which was always here, makes a menace easier,
which is what it was for.

**Tonight, outside** (`conditions.NIGHTS`). The street's own weather,
drawn once when the night comes in the way a run's is drawn once a run,
announced, said on the arrival line, gone by morning, and read
everywhere the street rolls: a Nightwatch sweep (quieter, and a gun is
heard twice), fight night (rougher, a rung worse, muscle pays half again),
a curfew, a wake, the lights out (rougher, and what they carried is easier
to walk off with), payday. Held to the run's standard by the validator:
no night that changes nothing.

**The clinic patches.** `clinic patch`: Integrity back at forty-five a
point, no shift, which is how a fighter is back on the street the same
night. And the validator's rider check now reads the world layer, where
the street and the fight have lived since D65; the two riders it could not
find were being read the whole time. `test_the_match` holds the drugs in
the sum, the traits, a night drawn, read, saved and cleared, a gun on a
sweep, and the patch.

### D134: The pit, and a fixer's street jobs

The second of the three from the consult: places and work where combat is
the expected outcome, and a room to be a fighter in, with its own rewards
for a player who wants the physical city as much as the net.

**The pit** (`content/pit.py`, `pit`). Built the way the gambling rooms
are built (a venue, a house, an arrival line, a pitch that states the
odds): a loading bay under the fence in the Shambles, Carrion's, open at
night, sixty people on their feet around the tape and a wall with names.
Five named regulars, each a rung and a style (Bottle, hands; Hinge, a bat;
the Deacon, a blade and the book on you; Salt, a metre of wire and a
smile; Mother, who has held the wall for nine years and holds the
eightfold blade). You fight the next name up or reach past it, with a
stake on yourself at the house's odds (even money, two to one, three to
one; the house keeps a tenth). Win and your name goes above theirs and
the purse is yours; the top hands over a one-of-a-kind blade you can only
get by taking it. The pit's rules are its own: hands, blades and sticks
(the house holds the gun); nobody dies on the floor, whatever rung, so
the fight engine's round cap is the whole of the contract there and no
warning is ever needed; no Nightwatch, no grudge; one bout a night; and a
rank that fades a rung per eighteen idle shifts, so the wall is not a
trophy case. Named fighters carry `pool_bonus` and `hit_bonus` on the
`Foe`, which is how a rung is a person rather than a tier. The purse
reads the night (fight night pays half again).

**A fixer's street jobs** (`deal <fixer> muscle`). The three fixers who
hand out runs hand out the other kind of work too: two a window, of three
shapes (somebody needs hurting, something needs standing in front of,
something needs getting back), each a fight where the job is, at the
tier the fixer says, carried like an errand and met on arrival through
the same `deliver` hook a courier's package uses. Real pay, and for a
recovery the thing itself. Held to the rule: none of it is a run.

`check_pit` holds the ladder (rungs 1..n, tiers and purses that climb,
a house that is a faction, a place that exists, a blade that is unique
and never on a shelf). `test_the_pit` holds the card, the closure by
day, the gun refused, a bout won with purse and stake, one a night, the
save, reaching three rungs up at three to one and taking the blade, the
fade, the floor that never kills, and a fixer's job from list to pay.

### D135: The deck, in the city

The third of the three from the consult: things to do with the deck that
are not a run, so it feels like a system you live with rather than a tool
you pick up. The rule that shaped it: every feature needs a mechanical
hook, or the deck becomes a drawer of toys. Search finds real stock. Mail
points at real work and real debts. A watch saves a shift. A message moves
a disposition. An ad reads your state and says so.

**Mail** (`mail`). Composed from the state of the world each time you
read it, with stable ids per day so that unread is a real thing and the
read marks save: a partner checking in, a nemesis making a promise, a
fixer with something physical or a job off the board, a lender with a
number, a thread waiting on somebody (the story's own `waiting_on`), the
pit asking after you, a bounty somebody would like you to know they know
about, a watched thing landing, and one advertisement. Every line ends
with the command that acts on it.

**Search** (`search`, `locate`, `find`). The net knows where things are
sold: every shelf in the city that has a thing this cycle, cheapest
first. A one-of-a-kind thing is not sold, and the net says where people
stop asking about it (the spot with the `Find`). A search for a gun is a
record: a point of Nightwatch attention, which is the thesis applied to
the search bar.

**Watch** (`watch`). Six things at most; whenever time moves and one is
on a shelf, the deck says where and for how much, once a cycle, through
the same `_advance` hook everything else the world says goes through.

**Message** (`message`, `msg`). A line to another runner, answered by
what they think of you: a partner "here, where?", somebody who owes you
something true about where they are, a stranger "sure", somebody cold
"busy", somebody hostile "do not", and a nemesis who lets you watch it
show as read, and then as read again. Warm answers warm them a point;
hostile ones cool. Once a shift each.

**The ads** (`ads`, and one in every mail). The best joke available,
because it is the game's thesis in another key: everything you do is
loud and the city remembers, and so the ads know. Eighteen of them in the
absurd and wry registers, targeted by predicates the world layer
evaluates (shot at, hurt, drifting, a habit, a loud weapon in hand, a
kill, a veteran, a debt, the wall, the blooded mark, hunted, broke, rich,
chromed, clean) and three for everybody. Fillers are only ever the ones
for everybody: an ad that has read you and got you wrong is worse than no
ad. They change nothing, which is the one thing on the deck that does
not, and the manual says they are aware of it.

`check_feed` holds the predicates to `feed.WHEN` and `WHEN` to the world
layer that reads it, the tones to the vocabulary, and a reply for every
opinion a runner can hold. `test_the_deck_in_the_city` holds all five
and their hooks. A new manual topic, `help thedeck`, and the README has a
paragraph.

### D136: A real deck

The direction: one more look at the deck, so it feels like an integrated
real item and not a mechanic. D135 gave it mail, search, a watch, a line
to the other runners, and the ads. This gives it a body.

**It is a thing** (`world/deck.py`). The deck out here is the deck in
there. A cpu or an io destroyed and it is in pieces in the city too: no
mail, no search, nothing to sweep or tune with, until `repair`. A cpu
with a level of damage and the mail comes through with static in it, the
same words lost each time you read (deterministic in the shift). Memory
decides how many things it will watch for (half the memory, two at
least). The antenna decides how far it hears: a hardline-only deck hears
the district it is in, a longwire a shift out, a relay mesh two. A
Nightwatch serial is a Nightwatch serial. `deck` shows all of it under
the components, in a section called "in the city", beside `deck name`,
which was already there.

**Sweep** (`sweep [district]`). The street read off the air: how rough
at this hour and what tonight is, who here has your name near the top of
a list, whether their people carry chrome (so whether `jack` has anything
to reach in a fight, which is the read a fighter wants before choosing),
whether the Nightwatch is out, which postings on the board are for
networks here, and who keeps hours here. Listening is not a record;
searching is.

**Route** (`route <district>`). The walk, planned: each hop, the hour
you will reach it, how rough its street will be at that hour, and who
there is looking. `walk` previewed, so the runner who would rather cross
the Shambles in the morning can see that they will not.

**Tune** (`tune [district]`). The district heard: the scene at this
hour, the street's line, and any rumour going round it, which is how
one-of-a-kind things are found, because the rumour is the only breadcrumb
there is. It was going to be `listen`, and the registry refused it,
correctly: `listen` is the Signal technique inside a run, and the shell
does not allow the same word to mean two things.

`test_a_real_deck` holds the hub, the sweep here and its reach by
antenna, the route, the tune, the watch capacity by memory, the static,
the pieces, and the repair.

### D137: What the play-test found

Three play-tests of everything since D128, run the way D86 to D89 were
run: a brawler who commits to fighting on night one, a netrunner who
never throws a punch and lives on the deck, and a first-timer who does
only what `now` tells them, each driven through a real session with the
whole transcript kept. No crashes in any of them. Nine things worth
fixing, in the order they matter.

**The physical half was invisible.** The first-timer followed `now` for
twenty-two turns and was never once pointed at any of it: they finished
in the Shambles at night, broke, unarmed, standing about forty metres
from a room with a wall of names in it, with no way of knowing. Two
fixes. The pit is on the arrival line where the pit is, like every other
service. And the guide learned to say it: a runner the street has
stopped twice who has never had anything in their hand or anything
between them and the hit gets told, once, that it can be fought and that
it never has to be. The fighter nudges (D131) only ever fired for
somebody who had *already* committed, which is the same shape of bug as
D86's story layer that was gated on meeting people while nothing said to
meet anyone.

**`errands 2` reprinted the list.** A bare number acts on the row
everywhere else in the game (`board 3`, `buy 3`), and at the errand board
it silently did nothing, which reads as broken. It takes the errand now.

**Muscle out-earned the net.** A tier-three doorway in the Shambles at
night paid 1,580c against the softest contract on that board at 1,527c,
which inverts the relationship the whole design rests on. Retuned to
about 1,170c at the same worst corner: the street is a living, the net is
the money.

**The bottom rung died in one swing.** Bottle had four points of pool and
a trained fighter hits for four, so the first bout in the pit was a
single keystroke. Every name on the wall carries real weight now, checked
by a test that says each takes more than one swing from a fighter of
their own rung.

And four small ones the transcripts caught: the pit's own footer printed
`pit next ` because `[stake]` is markup to the console (the same bug
class as `[static]` in D136, and worth remembering: square brackets in a
console string are a tag); the lender wrote to you as "sixes" rather than
under a name; the sweep said "nobody's people never do"; a search for a
common thing printed eleven districts, so it prints the four cheapest and
summarises; and `carry` said "a fence sells them" while you were standing
at a fence with two weapons on the shelf, so it names the nearest one and
its price, which is what the deck is for. `test_the_play_test_found`
holds all nine.

### D138: The deck under pressure

Three more play-tests, aimed at the deck: one that hammers every verb with
bad input and broken hardware, one that lives sixty shifts with it, and one
entangled in everything the mail can carry. No crashes in any of them, and
the save round-tripped. Seven fixes, and the two that matter were only
visible over time.

**Mail was a status board, not news.** Sixty shifts with three watches on
common things produced an inbox of four every single morning, three of
them the same three watches saying the same three things, and it was never
once empty. A watch says something now when a thing *lands* where it was
not, or lands *cheaper* than the deck last called news, and says nothing
at all while it sits on a shelf; the mail entry carries the price the deck
last called news, so the inbox and the spoken ping agree about what is
new. Then the opposite test, a runner with a partner, a nemesis, a debt,
a rank on the wall and every fixer in the city on speaking terms, produced
*thirteen* messages at once, seven of them fixers. Each kind writes on its
own cadence now (a partner every three days, a fixer every two, the ad
daily because junk mail is daily by nature), the fixers are capped at two
and rotate on their own cadence rather than daily, and the inbox is capped
at eight with a priority order. A quiet life is now exactly one piece of
junk mail a day; an entangled one is a rhythm between one and seven.

**Three ads on a loop.** Only three of the eighteen were written for
everybody, so a character with no debt, no habit and no holes in them saw
those three for sixty days. Seven more general ones, and even when
something has read you, one morning in three is somebody who has not,
because a targeted ad every day is a targeted ad nobody reads. A quiet
month now sees nine of them.

And five smaller ones the hammering found. `search a` answered
confidently about Auspex, so a query that means more than one thing is now
a question that lists them, and a substring under three characters is not
a search at all. A watch could be set on a one-of-a-kind thing, which is a
slot spent on something no shelf will ever have. `message` printed the
name twice, because the transcript prefix already says who is talking.
`watch drop` would not take the partial name that `watch` had accepted.
And `ads` was the one deck verb with no hardware gate, which is now
deliberate rather than an oversight: the advertising arrives whatever
state the deck is in, and nobody has ever worked out how.
`test_the_deck_under_pressure` holds all of it.

### D139: The fight under pressure

The same treatment as D138, aimed at the fight and the pit: one play-test
that hammers every move with bad input, every weapon, every rider and
every edge state, and three sixty-shift campaigns that live on each of the
fighting routes and count what they earn. No crashes, and the input
handling came through clean (junk lists the moves, an aside reprints for
nothing, an empty line covers up, prefixes and case work, and three
answers that are not answers means they stop waiting). Three fixes.

**The wall had one thing on it you could not beat.** The pit campaign lost
fifteen hundred credits over forty-five shifts, and the transcript said
why: four wins, then eleven straight losses to Mother. A fighter who
climbs to the rung below somebody out of their depth had exactly one bout
available every night, and it was the one they could not win, because a
loss does not move your name and `pit next` always points up. The house
books a rematch now, with anybody you have already beaten, at half the
purse and with nobody moving on the wall, and says what it always says
about a bout the crowd has already seen. Fought that way, by a player who
reads the card, the pit turns +15,834c over the same forty-five shifts.

**The card did not say what you were walking into.** The pitch says the
house is not embarrassed about the odds, and then the card printed a purse
and nothing about the fighter. It prints what each name takes and what
they hit for, in the same numbers the fight will use, against what you hit
for and what you have to spend. Mother takes thirty and hits for eight to
twelve; a runner who hits for seven with twenty Integrity can read that
and go and do something else. Seven columns do not fit eighty characters,
so it is a row and a line under it, the way the deck lists what is loaded.

**And a typo lasted the whole fight.** The patience counter never reset,
so once you had fumbled three answers, every later slip forced a guard for
the rest of the bout. Answering properly buys it back.

The three campaigns also settled the economy, which is the thing a second
career has to get right, and it is in the right order: a run pays between
five hundred and three thousand a shift, the pit three hundred and fifty,
a doorway a hundred, and wandering the street about thirty. Experience the
same way: a run teaches fastest, the pit next, and about fifty shifts of
fighting buys one skill to rank five, which is a career and not a farm.
`test_the_fight_under_pressure` holds the forgiveness, every weapon
through a press, the tier-four guard that leaves you at one, the card, the
rematch and its half purse, the name below you that you have never
fought, and the earning order.

### D140: The story knows the street

A pressure test of the story layer, and then the thing it found. The
static side came out well: every one of the thirty-five threads had a
reachable opener and no stage was stranded, and a hundred-and-fifty-turn
career touched seventeen or eighteen threads out of the twenty-four any
one character can see (twelve are locked to an origin). The stall the
transcripts showed, seven threads waiting on `did:<thread>.posting`, was
the harness rather than the game: a posting stage puts a story contract on
the board, and the flag is set by finishing that run, which the persona
never did.

What the audit found instead was the real gap, and it was total. Three
combat words across two of thirty-five threads. Not one thread gated on
anything the fight, the pit, the deck in the city or a habit sets. The
story was written before D128 and could not see any of it, so half the
game had no fiction attached to it at all.

**The rule engine can read the other half now.** Seven kinds: `skill:<key>:<n>`
for a trained rank, `pit:<n>` for a rung on the wall (and `pit:champion`
for the flag the house sets), `habit:<drug>:<n>`, `carrying:<key|loud|any>`,
`mark:<key>` for what a fight left on you, and `fought:` and `job:` for the
flags the street already sets. Content can be written against the physical
half the same way it is written against runs, heat and reputation.

**Three people and three threads about it.** *Hollis* keeps the ledger
under the fence, has run Carrion's floor for eleven years, is the reason
nobody has died on it, and hands out doorway work as well as bouts. *The
Weight* opens when your name is two rungs up the wall and she starts
writing sentences after it, and its decision is the house asking you to
go down in the third: take it, refuse it at the table with the book open,
or say it on the tape to sixty people, which costs her the eleven years.
*Pell* cooks in the back of a clinic that pretends not to know, and has
the warmth of somebody who believes they are in a caring profession.
*Ninety Seconds* opens when you have a habit and they can see the last
fortnight in how you are standing, and offers a cleaner cut, a straight
answer about what getting off it costs, or a chance to give the back room
up and find out who cooks it next. *Marek Vig* sells the fact that you
exist. *The Slot* opens when an advertisement has read you correctly, and
lets you buy your own file, buy somebody else's, or put the whole
operation in the public log for eleven days.

Nine decisions, each with an epilogue line, because the ending has to
remember them. Thirty-eight storylines now, a hundred and twelve scenes,
a hundred and twenty-eight decisions, thirty-two named characters.
`test_the_story_knows_the_street` holds every new rule, the three
people, all three threads firing from their own gates, the decision
landing, and that nothing a new thread offers is forgotten at the end.

### D141: A thread for every way of working

D140 gave the story rules that could read the physical half. This is the
coverage pass: an audit of what the forty-three threads actually ask for,
and content for what nothing asked for.

**What the audit found.** Six gates with no thread behind them at all: a
trained skill, a trait, a fight with a faction, street work done, a relic
found, a place visited. Thirty-three threads asked only for runs and an
origin. And four factions were nearly story-less: Chorus appeared in one
thread, and the Sixes, the Switchboard and the Nightwatch in two each.
Ten of the thirty-two named characters had no story that needed them,
which is the same waste from the other end.

**Five threads, each closing a gap and deepening a faction**, all built on
people who were already in the city rather than new ones. *Nobody Saw It*
(Stealth 3, the Nightwatch): the desk sergeant has a folder of eleven
networks that had a bad month and cannot say what happened, because
leaving nothing behind is itself a signature, and he would like one of
them noisy on purpose. *Out of Order* (Subterfuge 3, the Switchboard): the
queue outside the exchange is a market in places, worth nine hundred at
the front on a Tuesday, and a man who cannot be seen queueing needs to be
at the front at eleven. *A Good Dog* (Daemonology 3, Freeport): a
scheduler somebody abandoned on the cranes eleven months ago, still
running, better at it than the office, which refused a lift last week that
would have killed somebody. *What Came Out of Somebody* (Warfare 3 and a
doorway held, Carrion): a construct on a Kagawa subnet has stopped
matching stolen chrome to manifests and started matching it to the people
wearing it. *The Demonstration* (a fight you won, or the reputation for
one, Sendai): the plating is genuinely rated, the tests are real, and they
would like it to look like it nearly did not hold.

Twenty-four decisions, each with its epilogue line. Every gate has content
behind it now, five skills have a thread that wants somebody good at them,
and every faction but the construct at the bottom of the water has at
least three decisions that move standing with them. Forty-three
storylines, a hundred and twenty-seven scenes, a hundred and forty-three
decisions. `test_a_thread_for_every_way_of_working` holds the coverage
itself, so the next system that ships without fiction fails the build
rather than the play-test.

### D142: The record

The author's brief: exploration matters, there should be a great deal to
do outside the main line, and completionists should have something. Read
against the Bartle axes the game came out lopsided. Killers were served
(D128 to D141). Socialisers were well served: thirty-two people, a hundred
and twenty-nine topics, seven rivals with bonds, favours, crew and
betrayal. Explorers had the *material* and no payoff: twelve districts,
seventy-two quarters, sixty places worth standing in, two hundred and four
ambient events, twenty-five one-of-a-kind things with fifteen of them
found at a place and a rumour as the only breadcrumb. Achievers had
nothing at all. There were cross-character counters in the profile, but
they existed to unlock terminal cosmetics and no screen ever showed them.

**`record`.** Four sections, because there are four reasons to play. *The
work*: runs finished, runs that left nothing behind, black ICE survived,
the best night, storylines carried, street work done. *The city*:
districts walked, places stood in, one-of-a-kind things found, the deepest
drift reached, nights the street had weather of its own, things the deck
found for you. *The people*: met, asked, runners who decided about you,
best standing, decisions taken in a story, and whether anybody has put a
number on your name. *The floor*: fights won, rungs of the wall, whether
you hold it, outfits who sent people and got them back, doorways held,
and the top of the street's ladder survived.

Twenty-four lines, six a section, and no two counting the same thing,
which `check_record` enforces along with the rule that matters: every line
counts something the engine actually writes. Five counters had to be made
real for it rather than faked, which is the point of the check: a decision
now leaves a `chose:` mark, the city counts fights won and doorways held
and saves both, a drawn night sets a flag (so content can also gate on the
weather), and a watch hit is counted where it fires.

**It is not a badge.** Crossing a line earns a *name*: something the city
starts calling you, said once when it lands, shown on `char`, and replaced
as you pass better ones. Finish a section and there is a name for that,
and finish all twenty-four and there is one for that, and it is not
flattering. The counts live in the profile beside the terminal you have
been earning, not in the save, because they are "has this player ever"
questions: a flatline takes the character, the money, the chrome and the
name, and does not take the record.

The line the whole feature is for is the last one on the screen: the main
line is twelve scenes of a hundred and twenty-seven, and the record is the
only thing in the game that will tell a player how much of the rest they
have actually seen.

### D143: After the water

The other half of the author's brief: finishing the main line should pay,
and then the player should still have a city. It did neither. The four
endings set a flag apiece, and the only thing in the engine that read them
was a contract weight, so a campaign's last decision changed the board and
not the world, and nothing anywhere said "that was the end of that".

**The reward is the one thing you cannot get another way.** The Deepwater
palette used to be behind Dissonance fifty, which meant the terminal that
is about not knowing what Deepwater is went to whoever drifted furthest.
It is behind the main line now: you have to have gone and found out. With
it, a line on the record and the name that comes with it, and both live in
the profile, so the reward outlives the character who earned it.

**The city settles it, once.** Each ending moves grip and says one thing,
and they are different things: a budget line appears for something in the
water and nobody will say whose; the Stacks run the nine logs and Static
climbs while Kagawa slips; or nothing happens about the water, which is
not the same as nothing having happened. Guarded by a flag, so the city
says it once and gets on with being a city.

**And it hands the city back.** *Afterwards* opens a few shifts later,
with a different scene for each way it ended, and closes on the only
paragraph in the game that talks to the player about the game: seventy-two
quarters, some of which you have stood in; people who have never asked you
for anything and would answer if you asked; a wall in the Shambles, a
queue outside the exchange that is not a queue, a thing running on the
Freeport cranes that nobody has explained, and a box under a counter that
somebody is worried about. None of it is the main thing. There is no main
thing any more, and that is the reward. The stage has no choices, because
it is not a decision.

`test_after_the_water` holds the palette's gate, the record line, each
ending settling the city differently and only once, an opening per ending,
and that the close names what is left and asks for nothing.

### D144: What the players said, again

The method from D86 and D137, turned on the two things the author had been
building toward: stories for the ways of playing the deck, the chem and the
fight had opened, and a record that reaches every corner of the Bartle
square. Three personas, scripted and driven through the real dispatcher
with the whole transcript kept, each in its own data directory so the real
profile was never touched: an achiever who read `record` first and then
chased it (every district, every person, every topic, every place, errands,
watches, fifteen runs in thirty-three shifts); the ending, played three
ways by three characters (read the log and take the job, archive it and
publish, burn it and hand it back); and a fighter who spent forty-two
shifts on muscle work and the wall at Carrion's, rung four, thirteen wins,
and then turned to the net and carried the main line to its end. Five
campaigns, about seventeen hundred turns, no crashes. All four offer
endings were reached by play, each settled the city once, the palette came
on the first shift after, the record announced every line exactly once,
and a second character on the same terminal saw it carried over. A fighter
build finished five of five runs at Intrusion 1 to 2, so the pivot is
viable. What they found, in order of size, and what was done about it.

**The posting outlived its own ending.** The offer takes `dw_pattern` *or*
`dw_carried`, so the three facts alone brought the offer while *Four
Hundred and Eight* sat on the board, held and non-expiring. After the
ending it stayed there, and if it had been taken it stayed the current job:
a character who refused the offer on shift seventeen was still being told
"On the job: Four Hundred and Eight, `jack in`" on day twelve, and the
fighter, who refused and then finished the posting later, got "You read
it, or you do not" as a stray scene after the ending. `City.withdraw_story`
takes a scene's contract off the board for good and clears it if it was the
job in hand; `choose` calls it when a choice sets one of the endings, and
the settle calls it too, for a save that answered before this existed. The
endings themselves now live in one place, `threads.SPINE_ENDINGS`, read by
the record, the settle, the ambition and the board. The carried and under
stages are foreclosed on that path, which is coherent: the offer came, you
answered, the record with your name goes away.

**Afterwards opened in the same breath as the ending.** D143 said it opens
a few shifts later, and `after=3` was on all three openers, and "On the
inside of it" printed directly under "9,000c in." in every campaign.
`Story._old_enough` measured a thread's first stage from a `met:` rule and
nothing else; the openers have none, so the wait was a no-op. A first stage
with no meeting to measure from now measures from the stamp of the thread
that set the flag it waits on, which `_flag_owners()` already knew. A save
with no stamp is not held back.

**The name the city called you was catalogue order.** `title_of` took the
last earned title in `ENTRIES` order, so the achiever was "who asks" on
`char` through six later names, and the fighter stayed "on the wall" after
earning "who went and looked". The announcement said one name and `char`
said another. The profile already keeps `recorded` in the order the lines
landed; the titles read it now, newest last, and a line earned but not yet
announced is newer than any that has been.

**The ambition "What Deepwater is" was done on hearing the name.** Its
predicate was `dw_heard`. Finding out is the three facts, or having gone
all the way, and the line it prints says so.

**A fighter's experience was advised as `spend`.** Forty-four shifts on the
wall at Violence 1 with twenty-two experience in hand, and every `now` said
`spend`, which proposes the origin's shape (Warfare and Forensics for an
ex-enforcement), and `travel ninth` for a payload. Fights behind you are a
shape too: with three or more (wins and rungs together) and the next rank
of Violence affordable, `city_steps` puts `train violence` first, with what
it buys (Finisher at two, menace at four, a point on every strike between).

**A fighter who never talked had no story, and the journal blamed the
deck.** Zero threads in forty-two shifts in the Shambles, and the empty
state read "the city's stories open as you run jobs". All eight of the
D140 and D141 threads gate on meeting somebody, which is right, and the
pit never introduced its own house: *The Weight* needs `met:hollis` and
rung two. The empty state names the street now, and at rung two Hollis
comes to the tape and writes your name in the ledger herself, so the pit's
own story opens without a `look` for its owner.

**Polish.** The `world` tension line reads the ending instead of the middle.
`now` lists `record` under *also* once a line has landed. What a shift
earned is said after what the shift did: a line of the record used to land
between "1 shift pass" and "you did not sleep well", and the unlocked box
between the walk and the street, because `record_progress` printed from
inside the tick; `Session.announce` queues those while a command is running
and `invoke` flushes them at the bottom of the block, the way footnotes
already worked. And the close of *Afterwards* knows the wall: a rung-four
fighter was told about "a wall in the Shambles with names on it" as if they
had never seen it, so there are two closes now, `rest` and `rest_wall`,
gated on `pit:deacon` and its `not:`, and `validate` learned that a stage
may use the world layer's one combinator.

Kept as observations rather than fixed: the posting is a posture-72
network at runs five, and two of three who took it came out with nothing
the first time (the pattern path got them the ending anyway); Dissonance
stayed at seven across thirty-three chrome-free shifts, so "Deepest drift"
and "Runners who decided about you" were the only lines the achiever could
not move; and the previous round's harness did not set `XDG_DATA_HOME`, so
its personas wrote into the real profile. This round's does, and the next
round's must: it lives at `tools/playtest/`, with the three personas, the
spine driver, the round's report and a README on the method.

`test_what_the_players_said` holds all of it: the posting down for each
answer and for the settle, the afterwards waiting three shifts and not
held back without a stamp, the two closes and never both, the newest name
on `char` and the record's header, the ambition, the training step and
its reasons, the journal's empty state, Hollis at the tape at rung two and
not before with the pit's story opening after, the tension line, `record`
under *also*, and a line of the record said after the rest it landed in.

### D145: The third round, and what it found

The method again, on the three corners of the game nobody had ever reached
by playing: the fourth ending (the one that is a door), the retirement, and
a bond with another runner. Six personas this time, driven through the real
dispatcher, each in its own data directory: a player who says yes to
everyone and takes the other door; a player who plays for retirement and
walks out on purpose; two campaigns hunting a partner and two hunting a
nemesis, measured to a bond; a player who goes as far into the net as chrome
and a habit will take them; a runner who gets a number put on their name on
purpose and then does only what `now` says; and a fighter who trains
Violence to the top and takes the last name on the wall. No crashes in any
of them. Three fixes came out of it, and two things were confirmed rather
than fixed.

**The advice looped on a loadout it could not afford to fix.** The clearest
find, from the hunted runner. A fresh gutter deck ships two Crowbars, and a
runner who accepts an exfiltrate job is told to load a payload there is no
room for. The advice said "a bigger bank, or carry less" thirty times
running to a broke runner with no bank to buy, and never once named the move
that was right in front of them: drop the second Crowbar. `_loadout_step`
counted a program as droppable only if the plan did not want its kind at
all, so a duplicate of a wanted program was invisible to it. It counts one
loaded program per plan slot now and treats the rest, duplicates included, as
spare, sheds the cheapest that make the room, and says which. The dead-end
line survives only for a deck that genuinely cannot fit the thing with
anything shed.

**A partner could almost never form.** The record's "runners who decided
about you" was zero in every campaign of every round, and the bonds personas
found why: a bond wants four jobs and a disposition past sixty, and
`rival.jobs` only ever counted the board work a rival took in competition
with you, each of which drops their disposition by three. The two gates
pulled against each other, so the only way to sixty was to keep a rival
sweet while they raced you, which sixty shifts of hiring never managed. A
job you actually run beside somebody counts now: an ally who comes through a
run with you advances the counter, the way the run already lifted their
disposition. Running with somebody is the thing that makes a partner, so it
is the thing that counts. The nemesis half is unchanged: you do not run
beside the people who come to hate you.

**`market chrome` dumped the whole market.** The filter knew `cyberware` and
`ware` and not the word most players would type. `chrome`, `implant`, `wire`
and `cyber` all reach the ware shelf now.

**Confirmed, not fixed: the fourth ending is complete.** Going under
(`dw_under`) ends the character the way the flatline does, with the epilogue
reading it back ("you went under, with nothing loaded and no contract"), and
no Afterwards, which is correct: there is no afterwards for somebody who did
not come back. Saying no (`dw_stayed`) shares the walked Afterwards. The
reason nobody had reached either by play is that the door stage needs the
log read, the Archivist's consent and Lark alive all at once, which is three
cooperating side-threads on top of finishing the posting, the hardest run in
the game. That is the most demanding content in the game to reach, by
design; D146's work on the posting is what makes it fairer.

**Confirmed, not fixed: retirement works and is well-gated.** All four gates
hold, the epilogue and the estate fire, and a fresh character inherits.
Nothing in `now` surfaces the door before you are close to it, which is the
intended shape (D95): the door has been there since the first shift and the
game does not nag about it, it just answers `retire` honestly when asked.

`test_the_third_round` holds the three fixes: the duplicate dropped rather
than a carry-less loop, the payload loading once the room is made, a bond
formed from four jobs run together, and `market chrome` filtered to ware.
`validate.py` clean, `test.py` green.

### D146: The signposts, and the counts held

The five additions the third round pointed at, one of them struck off before
it was written because the round found it already done (the fourth ending is
complete, D145). The four that remained.

**A clean runner can reach the drift line now.** The record's "deepest drift"
wants sixty, and the whole dissonance system is chrome you do not get back,
so a runner who wore none could never cross it, whatever else they did. The
one network in the game that is *about* the boundary going soft is Deepwater,
and a run against it now costs a point of drift, said in its own words: you
were somewhere with no edges, and a little less of you came back out than
went in. Small, and only theirs, so the chrome economy is untouched and the
explorer who keeps going back to the water has a slow way down that the
sheet did not give them before.

**The posting's brief names the way in that fits.** *Four Hundred and Eight*
is a posture-seventy-two exfiltrate handed to a five-run character, and two
of the three testers who took it came out with nothing the first time,
because they breached it the way you breach anything. The story has been
saying since the Archivist that there is nothing arranged around Deepwater,
and the brief says it now too: no perimeter to break, `approach` it as an
inside job or talk your way in and come up past the wall instead of through
it. The run was always winnable that way; nothing pointed at it.

**The fence and the demonstrator introduce themselves through the work**, the
way the pit introduced Hollis at rung two (D144). Two of the fighter's
new-systems threads gated on meeting people a fighter would never `look` for:
*Somebody in the Cabinets* on the fence under the Shambles, and *The
Demonstration* on Sendai's demonstrator at the Glasshouse. A fixer's street
job now gets word to the fence, who fronts that kind of work, and points you
down there; and the mark a killing blow leaves gets Sendai's attention, and
a card in your pocket with the Glasshouse on it. Both are the meeting the
thread needed, arrived at by doing the thing the thread is about.

**The counts cannot drift silently again.** The README was ten numbers behind
once because every one is typed by hand and read by nobody. `validate.py` has
a `catalogue()` now that reads every derivable count off the modules, and
`check_readme` holds the README's "What is in it" to it: a count that moves
fails the build until the line is regenerated. `tools/counts.py` prints the
current numbers for pasting. The one number not derivable in a line, "151
things to see in the street", is deliberately left out.

`test_the_signposts_and_the_counts` holds the drift branch, the perimeter
line, the fence met through a fixer job and the demonstrator through the
blooded mark (each once), and that the README states every count the
modules produce. `validate.py` clean, `test.py` green.

### D147: The walking, answered

A coverage audit across every playstyle, run the way D141's was but with a
wider brief: not just which gates have content, but whether every kind of
player has enough of a story, whether the tone holds, and what is missing.
The tone came out clean, which is worth writing down: no em dash anywhere in
the corpus, none of the tells that mark writing nobody wrote, no placeholder
text, the grim register holding from the character sheet to the epilogue. A
face persona played twenty jobs by talking and touched twenty-two threads
without a tone slip. The counts held, because D146 now makes them.

The gap was one playstyle, and it was total. Threads that demand a specific
activity beyond running jobs: face eight, fighter five, street four, drift
three, deck-specialist two, achiever one, and **explorer zero**. A persona
that stood in all sixty places and found what there was to find touched
eighteen threads and not one of them opened *because* of the walking. The
explorer had the richest material in the game, twelve districts and
seventy-two quarters and sixty places and twenty-five one-of-a-kind things,
each with a rumour and a person, and no arc that ever said "you are somebody
who knows this city." The record was their only payoff, and a record is a
scoreboard, not a story.

**The engine learned to count the walking.** `places:<n>` and `finds:<n>`
are rules now, the number of places stood in and one-of-a-kind things found,
the way `skill:<key>:<n>` reads a trained rank (D140). Small, and it is what
makes an explorer thread possible: a story can gate on having been to enough
of the city rather than on one named corner.

**Two threads read it.** *The Edges* opens once you have stood in a dozen
places: somebody else who stands where standing has no reason, keeping a map
not of the city but of where it stops, the water line and the boarded wards
and the fenced works, and asks for your count or leaves you to keep your
own, and closes when you have stood at enough of it that the city has a
shape in your head that is not the one on the transit map. *Kept Back* opens
on the first one-of-a-kind thing you find and reads the rumour they all
share, that the thing was kept back for somebody, and the somebody keeps
turning out to be whoever went and looked, which keeps turning out to be
you; the Archivist names it, that the city gives things to the people who go
and look and you have started to look like one of them, and it pays off on
the fifth find with the quietest of the game's rewards, that being the kind
of person the city hands things to is not a thing anybody can take off you.
Neither needs a new person the cast has to balance; the encounter is in the
scene.

The coverage test (D141) now asserts `places` and `finds` have content too,
so the explorer cannot silently go back to being the playstyle with material
and no story. `test_the_walking_answered` holds the count rules, both
threads opening on the right thresholds and closing on their payoffs, and the
walking surviving a save. `validate.py` clean, `test.py` green.

### D148: The hunt made visible

The explorer got a story in D147 and still could barely reach the far half
of it: the one-of-a-kind things gate on meeting a specific person at a
specific hour, and a persona that walked the whole city found one of fifteen.
The material was the best in the game, each thing with a rumour and a person
and a place, and it was nearly invisible.

**The rumour leads now.** It surfaced only once all of a find's rules held,
including the `met:` rule for the person who hands the thing over, which is
backwards: the rumour is the thing that is supposed to point you at that
person. It surfaces on the rest of the rules now (the runs, the standing, the
drift) and names the place, so it can send you to where the person is.

**Standing where a thing is makes you aware of it.** Visit a place that has
something to be found whose conditions you nearly meet, and you sense it,
even at the wrong hour or before you have met whoever hands it over. The
walking populates the board instead of relying on catching a line in
passing.

**`rumours` is the board.** The one-of-a-kind things you have found, checked
off with where they were; the ones you have heard of and not yet found, with
the place, the hour, and a nudge at who would know, without naming them; and
a count of the ones you have not heard of, because hearing of a thing is the
first half of finding it and the view keeps that. It is the explorer's hunt
made a thing you can see, the way the record is the achiever's.

`test_the_hunt_made_visible` holds the empty board reading as a hunt, a
runs-gated thing found by standing where it is at its hour, a thing sensed
without being given at the wrong hour, the board showing where and when, and
the rumour surfacing before the person is met. `validate.py` clean, `test.py`
green.

### D149: What only your line can open

The deck specialist, past the point of just running jobs, had two threads:
one that wants Daemonology, one that wants Stealth. Cryptography,
Architecture, Signal, Sabotage, Intrusion, Hardware and Forensics had none
between them. The specialist got all the run-gated content like everyone,
and nothing that was about being specifically, deeply good at the one thing
they had poured a career into.

Two threads, each about the thing only that specialist can do. **The Sealed
Thing** wants Cryptography three: Osei, behind the bar that has no front,
has kept a drive a dead runner paid a year to leave with him, locked in a
way that has beaten everybody he has shown it to, and you are the one who
can open it, and what is under the lock is a letter and a key and a name that
still drinks there Thursdays, and the choice is whether to deliver it, read
the file first because you are the one who can, or wipe it and tell Osei it
was nothing. **The Names on the Big Dish** wants Signal three: Pip catches
names on the big dish, between the channels where there is not supposed to be
a channel, and you are the one who can find where nowhere is, and the
arithmetic keeps returning the water, the harbour at Freeport, on no power
anybody pays for, carrying the names of runners, one of them yours. Each
closes on what it is to be the one who can open what is shut, or hear what
is not on a channel: the specialist's version of the thing the fighter and
the face already had.

`validate.py` clean, `test.py` green.

### D150: The unit

The achiever, the player who does a great deal of everything and reads the
record, had one thread that touched them and the record itself, which is a
scoreboard. Against the same measure the fighter had five threads and the
face eight, the completionist had the numbers going up and almost no story
about the going up.

**The record opens a story now.** A new rule, `record:<n>`, is how many of
the record's twenty-five lines this character has earned, live, so a thread
can gate on having done the lot rather than on any one thing. **The Unit**
opens at fifteen lines: you hear it in Marrow, two people who do not know you
are behind them, one describing a job and using your handle to say how much
of it there was, not as a person, as a unit, "half a" you, and the other
knows exactly how much that is. At twenty lines somebody who keeps the count
on purpose finds you, with a book, and you are most of it, and they want
nothing except to have got yours down right before the city closes over you
the way it closes over everybody, and the choice is whether to sit with them
and put it right or leave the book to say what it says. It is the quietest
achievement in the game and the one that lasts longest, which is the
register the record was always in.

`test_the_specialist_and_the_reckoner` holds the two specialist threads
opening on their skills and the right people, the `record:<n>` rule counting
earned lines, and the reckoner opening on a full record. `validate.py`
clean, `test.py` green.

### D151: The names, and choosing which to wear

Two halves, both about the titles the record gives. The first was a real
gap: once you earned a title, you could not choose it. The city called you
the newest one, always, so a quiet later line landing after a loud one read
as a downgrade, and there was no command to pin the one you would rather
wear. It is the one earned, persistent thing the game did not let you
select, when the terminal you read it on has let you choose since D103.

**`called` pins a title.** It lists every name you have earned, grouped by
where it came from, marks the one the city uses now, and lets you pin one;
`called auto` goes back to newest. The pin lives in the profile, like the
names themselves, so it survives the character. `char` and the record header
read it.

**And there are more names to choose from.** The record's titles are earned
by crossing a line, by doing enough of a thing. These are earned by doing
one particular thing, and they come in the three registers a city keeps a
person in: what it admires, what it will not forgive, and what it finds
funny. Twelve of them, four to a register, each reading a flag the engine
already sets. **Heroic**: who paid the blood price (you paid for somebody
else's life), who could not be bought (handed Deepwater back), the witness
(put the nine logs in print), who said no to the water. **Vile**: the one
they cross the street from (you have killed), who sells names (betrayed a
runner, which now leaves a mark), who reads the dead's post (opened a dead
runner's locked file), who lets them go under (let Lark drown with the
surgeon's price in your pocket). **Amusing**: who asked about the war (you
asked Ozymandias, despite the sign), the magpie (three one-of-a-kind things
off no shelf), a regular at a bar with no front (Osei pours yours before you
sit), who talks to children on towers (helped Pip point the dish at the
sea). Earned once, they go in the profile and announce themselves in their
own register, and they are pinnable alongside the record's names.

`test_the_names_the_city_gives` holds the twelve titles across three
registers, an extra earned by its deed and recorded, the pin honoured over
newest and refused for a name you have not earned, and the names outliving
the character. `validate.py` now enforces the three registers and that every
title reads a real rule. `test.py` green.

### D152: The one thing that is not for the work

A pet. The author asked for two kinds, real and digital, some silly and
some frightening, that need care and have their own food and water and play;
this is the first half, the real ones, the animals you keep meat-side. It is
the first thing built into the game on purpose to do nothing: no run helps
it and it helps no run, and `validate` holds that at the source, because the
whole point of it is to be the part of the game that is not about winning.

**It lives at your safehouse**, because you cannot keep a thing alive out of
a chair, so you take one on once you have somewhere of your own. Six of them,
across the registers a city keeps an animal in: a cat that decided about the
safehouse before it decided about you, a dog from nobody that thinks the
door is the best thing that has ever happened every time, a rat the Ninth
considers either sensible or a symptom, a pigeon with a bad foot and no
sense of self-preservation, a gecko run off the deck's waste heat, and the
thing that came out of Building Nine in somebody's pocket, which is a cat the
way anything Aoyama made is ever only mostly the animal it started as. You
take on a stray where strays are, or buy one, and you can name it.

**The care is real and so is the loss.** Food, water and play run down at a
rate the animal decides: a dog needs walking and a gecko needs almost
nothing and a cat needs you to believe it needs nothing. You keep them up by
hand, `pet feed` and `pet water` and `pet play`, feed bought in bags. Food
and water are what a thing lives on and play is what it lives for, so a
starving animal is lost and a bored one is only unhappy. And an animal
nobody feeds tells you so, for a long time, in the state it is in and the
things it does, the cat at the window more than the door, the dog that does
not get up, and then one shift it is not there. It is telegraphed all the
way down, the way the only real death in the net is, because it is the same
city and the same rule. Feeding it back from the brink forgives the neglect;
nothing about it is a trap.

**It belongs to the character**, and it is in the save, and when the
character ends, retired or flatlined, the ending says what became of it,
which reads differently for a pet that was kept than for one that was lost,
because a thing that depended on you is the truest account of what you were.

`test_the_one_that_is_not_for_the_work` holds the safehouse requirement, the
care loop, food and water losing it while play only saddens it, the
telegraphed warnings before a loss and the loss only after a run of shifts
at nothing, care forgiving neglect, the save round-trip, and the ending
coda; `check_pets` holds the spread and, at the source, that no run or fight
ever reads the pet. The digital pets, the ones that ride the deck into a run
and talk, are the next half. `validate.py` clean, `test.py` green.

### D153: The other kind of pet

The second half of the pets: the digital ones, the constructs that ride the
deck into a run and talk. Where the animal is meat-side and costs you food
and coming home, this one is software and costs you the one thing a deck
never has enough of, which is memory: a slot that could have been a breaker,
spent on a thing that only talks. That is the whole price of it, and it is a
real one, because the memory it eats is memory a program cannot have, held
by the same budget everything else on the deck fights over.

Five of them, across the registers the author asked for, silly to scary. A
pixel cat, eight pixels drawn in an afternoon and given a purr, that reacts
to the run with the confidence of a thing that understands none of it. A
chatter-bird that comments, always comments, and is not always wrong, and
stops talking exactly once, which is how you know. A good boy, a loyal-dog
construct that cannot do anything and comes with you glad to every single
time, and puts itself between you and the black ICE it cannot fight because
you are the whole of what there is. The tally, a counting daemon a runner who
did not come back left behind, that counts something it will not name and
counts down, once, on the nights that go wrong. And wormwood, which you did
not write and cannot remember loading, that says things it should not know in
a voice that is almost yours, and that you keep meaning to delete and keep
not.

**It rides in and speaks at every beat of the run**: the connect, the amber
and the red and the lockdown, the black ICE tell, the clean way out and the
burned one. It is cosmetic to the bone, and `validate` holds that by reading
the one method it has and failing the build if that method ever touches the
trace or the noise or the alert or a check: it prints a line and returns
nothing, and that is the entire contract. Left unrun too long it goes
dormant, quiet until you take it out again, because it is software and does
not die, it waits. It is on the deck, in the save, and `familiar get`, `drop`
and `name` are the whole of managing it.

`test_the_other_kind_of_pet` holds the spread and a line for every beat, the
memory cost and the refusal of one that does not fit, naming and dropping,
the voice being provably cosmetic, dormancy without loss, and the save
round-trip; `check_pets` reads the voice method's own body to hold the
no-mechanics rule. `validate.py` clean, `test.py` green.

### D154: A familiar needs feeding too

The digital pets shipped with only dormancy for care, where the animals got
a full loop, and the author's brief wanted both kinds tended. A familiar is
fed the way it exists: by being run. It carries a charge now, full when you
load it and full again every time it rides a run, that winds down over the
shifts it sits in a folder, faster if it is the needy kind (the good boy
loses it quickest, wanting you) and slower if it is the patient kind
(wormwood barely notices). Low charge it says so, in a line of its own. At
no charge it is dormant, quiet until you run it, which is not death, because
it is software and waits. `familiar tend` gives it a charge between runs, and
the status shows the charge as a bar. Still cosmetic to the bone: `validate`
reads the voice method and holds that the charge never reaches a check.

`test_the_other_kind_of_pet` gained the charge: it drains on an idle shift at
the familiar's own rate, a run and `familiar tend` restore it, and no charge
is dormant without loss. `validate.py` clean, `test.py` green.

### D155: More of the deck specialist, and a thread that could not open

The coverage audit found the deck specialist still thin past Cryptography and
Signal, and the honest-play sweep found something worse hiding under it: the
D149 cryptography thread, *The Sealed Thing*, gated on `met:osei`, and Osei's
NPC key is `bartender`, so meeting him set `met:bartender` and the thread
could never open by play. Its test had set the flag by hand and hidden it.
Fixed to `met:bartender`, and `validate` now holds every thread's `met:<key>`
to a real person the way it already held `asked:`, so a thread that waits on
nobody fails the build.

Then two more, for the two deck lines with nothing: **Architecture** gets
*The Shape of the Vertical*, where Mrs Achterberg, who fits the building and
knows its sums do not close, asks the one person who reads structure for a
living what is in the floors that are not on the board in the lobby, and the
architecture resolves into a building four floors taller than it admits,
below the lobby, on a car that only goes down. **Sabotage** gets *What the
Green Keeps*, where the Orderly cannot delete the aftercare records of the
patients who stopped coming, because they regenerate from a rule the schema
has no word for ending, and a saboteur can unmake the rule rather than
remove the records. Each closes on what it is to be the one who can read a
shape nobody else can, or unmake a thing instead of deleting it. The coverage
test now enforces a thread for Cryptography, Signal, Architecture and
Sabotage alike.

`validate.py` clean, `test.py` green.

### D156: Home, the other side of the deck

The net side of a runner is the `deck`, and the game has always had a good
screen for it. The other side, the one you have to come home to, was
scattered: the safehouse in one command, the pet in another, the familiar on
the deck, the arrangement and the debt and the crew each somewhere else, and
no way to see at a glance what you were keeping alive and what you were
keeping up. `home` gathers it: the safehouse and where it is, the pet and
whether it is well and what it needs, the familiar and its charge, any
standing arrangement and what it costs, a debt and who holds it, and anybody
crewed with you. It changes nothing and it points at the commands that do,
and when there is none of it the rows read as invitations rather than a wall
of "none". None of it wins a run; all of it is why you come back from one.

`test_home_is_what_you_keep` holds the empty life reading as invitations and
the full one filled without a crash and without changing anything.
`validate.py` clean, `test.py` green.

### D157: What the honest players found

The sweep of D144 to D146 was repeated on the build with the pets, the
titles and the specialist threads in it, this time with personas that
play the way a person does: pay for the hire, load the payload, follow the
brief, take the out the street names when it refuses a walk. Six of them
found nothing. Three found walls, and every wall was a rule that was right
for board work and wrong for the spine.

The Deepwater posting spawned black ICE on its objective, so the fourth
ending was walled behind Undertow for a runs-seven character: `generate`
takes `lethal` now and the posting, which guards nothing, passes it false;
every other network is unchanged. A crewed or hired runner raced you for
the board they were about to walk into with you: `_rival_turn` marks both
as busy. The reckoner opened on a record of fifteen lines that a full
career reaches late; it opens on ten and speaks on fifteen. A partner bond
climbed at six a job and landed nowhere inside a campaign; it is eight and
three now, and the bond persona crews at plus thirty and is a partner by
shift twenty-seven. And `now` advised `drop` on the posting with the
player's name in it, ten times running, by the same rule that drops a
board job after three failures or a hot route; on a story contract the
dead-to-you branch says `approach inside` while nothing is arranged and
the heat branch names the walk into them, and `drop` is board work only.
Deepwater noticed every one of those ten drops, which is how it was found.

Two things the round measured and left alone. A three-run explorer holds
one find of fifteen: the finds are career-gated by design and a longer
persona is the honest measure. And a hired runner's `with` reads empty
after the job because the hire is spent; that is the harness reading the
state a shift late, not the game.

The harness grew what the round needed: `drive_run` trusts the brief's
first concrete step (the driver that second-guessed it finished fewer
runs than one that did what the game said), and `do_step` takes a heat
refusal the way the refusal says to. `test_what_the_honest_players_found`
and `test_the_posting_is_never_dropped` hold all of it.

### D158: Five whole lives

D157 fixed what the honest personas found; this played the game the way
a person does for a whole career, five ways, and fixed what those found.
`tools/playtest/campaign.py` is the set of acts (the deck as a thing you
own, the deck in the city, jobs the long way, the people in the room, a
safehouse and both kinds of pet, money and the tables, the street and the
pit, chrome and a habit, every district walked, the record and the names,
save and restore, an arrangement and an alias, a crew, the main line, the
door), and five personas compose them: the netrunner, the fighter, the
face, the explorer, the drift. Each types between 86 and 96 of the 156
commands the game has and says which it never did. Zero crashes in any
round.

Every finding was the advice. `now` is the game's own competent player,
and a script that does what it says is the cheapest way to find where it
is wrong. Two branches answered a payload that did not fit with `deck`, a
screen, and the face typed it 420 times; both name a move now, and a test
holds that no branch of the advice returns a bare `deck` step. The loadout
plan took the best breaker first and crowded out the payload the job
needed, so the plan had no payload in it and the advice unloaded the
Siphon for the Lattice 390 times; the plan reserves the job's own category
and takes the best of each kind that fits. The familiar's memory (D153)
was invisible to the plan, so a Wormwood on two of four memory left the
Siphon nowhere and the drift was sent to a shelf it could not afford 419
times; the plan is built around the familiar, and when the job's program
fits the bank and not the bank less the familiar, the step is `familiar
drop`, said as the player's choice. An upgrade that did not fit was a
step over the adequate loaded program; it is not. The branch that swapped
one plan program for another is gone. A collection the account could not
meet said `debt`, a screen, 418 times; it names the fence or the errand
held first, and the first cut of that crashed on an unbound name, which
the netrunner caught and a test now runs. `called` takes a title's key.
The job screen ends its progress line with one full stop.

What the five did, on the fixed build: the netrunner and the face reach
the employed ending and live through the afterwards, the fighter and the
drift the refused one; the face is a partner to Vesper Okonkwo by play;
the explorer holds six of the fifteen finds and twenty-six threads, saves
and restores with both pets intact, and cannot retire because a bounty
costs more than it has, which is the door being honest. Three of five
were killed in the street in one round, every time a bounty street
entered `--anyway` and `cover` chosen over `give`: the harness being
reckless, not the street being unfair. `test_now_never_says_deck` holds
the advice; `SWEEP-2026-09-04-campaigns.md` is the full account.

### D159: The five suggestions

D158 ended with five suggestions and the author said do all five. In the
order they were built.

The street takes the money first. `give` was only ever the second
question, after a bad answer had already landed, and three of five
campaigns died on the fourth rung with the money in their pocket and
`cover` chosen. On the two rungs that put people in clinics, `give` is on
the first question when the money is there, at the flinch's price, and
never on the small ones, where the street is a skill. Three small text
things: the rice gallery's plain style is called Bare, not None; `deal`,
`talk` and `ask` with a runner's name say what a runner is for instead of
that nobody is called that; the job screen's "you will not make it in
time" is a warning, not an error; and `uninstall` says nothing is fitted
rather than available. The quiet door: a bounty and less than a new name
costs was the one state the door had nothing for, so the freight line is
a thread now (*The Freight Line*, on a `bounty:` rule the story engine
reads off the city): somebody who knows somebody offers a container out,
for nothing, which is the point, and taking it ends the character as
"left quietly" with its own epilogue line; staying is watched by the
docks. The follower fuzz: `test_the_follower_never_stalls` plays three
seeds by doing exactly what `now` says and what the brief says, and fails
if any step repeats more than twenty times running or anything raises.
It earned its keep the first time it ran: in Marrow `now` said `buy
lattice` and `buy lattice` asked which one, fifty-nine times, because the
market also sold a Kohler-Reyes Optic Lattice; an exact name or key wins
outright now. And the run-craft persona (`q6_runcraft.py`): rank four in
everything, every technique typed in a network in six batches over twelve
runs, the city-side commands nobody had typed, and then one character per
origin to type the verb only that origin has. Every refusal it met was an
honest one, said in the game's own voice; across the six campaigns the
only commands never typed are `begin` and `quit`.

### D160: What you keep, and the three that were left

The three suggestions D159 ended with, then a pass at what the transcripts
said was thin. The follower fuzz plays every origin now, ninety steps each,
and holds: no step repeats more than twenty times for any of the twelve.
`test_every_origin_has_its_verb` plays each origin's signature verb by
state (a network, the verb, the verb again) and holds that it is theirs to
type and that anybody else is told whose it is. `requisition` names what
the form covers when nothing matches.

Then what you keep. Every animal has the one thing it plays with (a wire
mouse, a rope, a wheel, a mirror, a warm stone, a bell): `pet toy` says
what, `pet toy buy` buys it, and `pet play` reads differently with it in
the flat and changes nothing else, which is the rule for pets. Three lines
on the record for the systems that had none: shifts you kept an animal
alive, runs with a familiar riding the deck (counted at the connect, the
familiar itself still reading nothing), and the names the city has given
you. Two titles for the freight line, one for each answer.

The regression of all six campaigns caught the door I had just built: the
first cut opened on a bounty at three runs, which is a bad week and not a
career, and its first answer was the one that ends you, so five of six
personas took the box out of the city by default. It opens on six runs and
twenty shifts now, staying is the first answer, and the harness never picks
an ending its brief did not name. On the fixed build the six are clean,
three endings and a partner bond by play, five personas offered the berth
and staying. `test.py` green at **19,413**.

### D161: The number came off, and what a runner says back

Two things the D160 regression read back. Five of six personas earned
"who stayed to be found" by saying no once, which made a heroic title the
price of a default; the freight line has a third scene now, *The number
came off*, for somebody who stayed and then turned the bounty, and the
title reads that. And every campaign typed `message` to a runner and got
one of two lines a band; there are four a band now, in the same voices,
so the same runner does not answer the same way every time. And the
toy shows where the animal does: on `pet` and on `home`.
`test.py` green at **19,417**.

### D162: The paper, and the first answer

The four suggestions D161 ended with. An ending is never the first answer
of a stage, held by `validate` now rather than by memory: the first cut of
the freight line put the box out of the city first and five of six
campaigns took it by default, and the same guard, run on the whole of the
content, found the spine's own under ending shaped the same way (`go`
before `stay`), which is reordered. The record's "names the city has
given you" counts the record's own names as well as the flavoured ones.
The other side of a bounty: *The Paper*, in which somebody has taken the
paper on your name and Mara says so, with the three things people do
about it (go to ground, buy it back through her, or sit in the Hall where
the collector can see you seeing them), on the `bounty:` rule the freight
line introduced. And `tools/playtest/run_all.sh`, the six-campaign
regression as one line, printing the four things that matter. On this
build: six clean, three endings and a partner bond by play, `begin` and
`quit` the only commands nobody typed. `test.py` green at **19,499**.

### D163: Coming back, and the line you are near

Two things for the player who is not a script. `restore` said the time
and the district and left the rest to be found out the hard way; it says
now what a player who has been away needs before `now`: the job they are
on and what is left on it, the money somebody is coming for, how the
animal is, a dormant familiar, the crew. And `now` ends, in the city,
with the record line you are closest to crossing when it is close (a
quarter of the target or less): one dim line, so everybody finds out
that the city keeps count and the achiever does not have to read `record`
to know they are one run short. The record is the profile's, so that is
what is read. The `familiar` screen says how many runs it has ridden.
`test.py` green at **19,506**.

### D164: The collector has a name, and the four corners

The four suggestions D163 ended with, then a look at each of Bartle's
four with the author's leave to build whatever was obvious.

The collector has a name: when the paper is taken, the runner who thinks
least of you is the one who took it; Mara does not say the name, the
book does, `who` shows it until the thing is settled, and the answer
settles it (bought back, they think a little more of you; seen seeing
them, a little less). `now` names the title with the record line ("and
the city will call you a working runner"). `python3 test.py --long`
follows two characters for four hundred steps each, past where the
briefs steer the campaigns, and is not in the default run. And the
familiar has two more beats: `done`, at the moment the job gets done
whichever verb did it (the session reads the flip, the familiar reads
nothing), and `home`, when you rest where you live.

Then the corners. The explorer's `visit` list marks where you have
stood and counts it in the header; it used to keep that to itself. The
socialiser's `people` says what is left to ask each person. The killer
has the collector. The achiever has the name with the line. `map` already
said "not been" and "1 of 12 walked", which is why it is unchanged. On
this build the six campaigns are clean, three endings and a partner bond
by play. `test.py` green at **19,514**.

### D165: What the long follower found

`python3 test.py --long` ran for the first time and found two things in
four hundred steps that ninety never reached. One was the advice: a
wrecked deck two shifts from the Ninth was told `travel ninth` seventy-six
times while Carrion had a number on the name and the street refused every
one, because the workshop advice never ran the heat check the contract
walk runs. It names the nearest workshop the street will let you reach
now, and when none will, the priced walk with the reason. The other was
the test: an escort is mostly waiting and every wait moves the clock, so
a long streak of `wait` is the one step that is not a stall, and the
follower counts it past forty only. And the killer's corner from D164
finished: `who` lists you first, against the field ("ahead of the
field", "2 behind the best"). `test.py` green at **19,519**,
`--long` green.

### D166: The five corners, built

The five design calls D165 ended with, all built. For the explorer, a
second way into the one-of-a-kind things: somebody you have asked
everything tells you where to look, once, and what they told you gets you
past the career the find would otherwise wait for; the other rules still
hold and the walking is still yours. For the socialiser, the runners
decide about each other: a partner hears who you crewed and thinks less
of you for it, and a nemesis buys your crew for a night now and then, at
a price that is about you, so you go in alone. For the killer, the top of
the wall does not stay empty: when a rank fades from the top, the one you
took it from is back on the wall above you, at full price, and `pit`
says so until you take it back. For the achiever, the record shows this
life beside the profile wherever they differ. And for all four,
`q7_long.py`, a life of every act in rotation, which is what D167 is
about. `test.py` green at **19,528**.

### D167: What the long life found

`q7_long.py` is a courier who lives two hundred shifts with every act in
rotation, the main line in the middle, the door at the end. The first
life died in the street at shift eighty-one, broke and hunted, and the
money trace said why: `now` had told them to buy a Lattice that could
never sit beside their Siphon, then a Sable to replace it, four thousand
credits in a week, on top of a street that took its pay-offs and a
bounty that closed the districts the work was in. The breaker advice
reads the room now, the bank less the familiar less everything the plan
wants that is not a breaker; a breaker that fits the bank but not the
plan is a purchase, not an upgrade. The second life reached shift two
hundred and one alive: forty runs, the employed ending at seventy-five,
thirty-four of fifty-three threads carried, three finds, the record at
fourteen of twenty-eight with the rest belonging to other ways of
playing, and `now` at shift two hundred still naming real moves (a
program to unload, a thread three shifts away, a technique the
experience will buy). The late game decides less than the early one,
which is what an ending is for; it does not go stale. One wording on the
way: a wrecked deck said "memory 1/3, memory 6/4", which were two
different things, and says "carrying 6 of 4 memory" for the second.
`test.py` green at **19,531**.

### D168: The door, the ask, the watch and the two scenes

The four things D167 ended with, with the author's call on the first:
the stake comes down, not a second door. Forty-five thousand was a
number no working runner held in two hundred shifts; fifteen thousand is
a few good contracts kept whole, a decision rather than an accident, and
`validate` prices it at four top contracts instead of five and says why.
A runner who thinks well of you (twelve or better, three jobs behind
them, no bond yet) asks you in on your next job now and then, their cut,
their idea, at most once in twelve shifts: the bond a solo player could
never start starts there. `now` says to watch the payload nobody sells
here when you own none, so the deck's watches hit and the line on the
record moves. And the two one-liners are scenes: the crew comes back
from the night the nemesis bought and says what it was paid and which
door it gave them (the wrong one), and the partner who hears who you
crewed asks how the new one is on a door, listens, and says nothing,
which is how they say it.

The harness learned three things a player already knew on the way: keep
a reserve before paying the street, do not gamble when poor, and do not
walk into a street with a number on your name when broke or hurt. With
those, all seven campaigns end alive. `test.py` green at **19,537**.

### D169: The long wash, and every thread opens

The four things D168 ended with, and the audit the author asked for. A
third way out from under a number, for the runner who cannot pay for a
name and will not take the box: *The Long Wash*, in which Mara launders
the name over ten shifts of work rather than money, and at the end of it
the numbers come off and the heat is halved. The first time a runner
asks you in it is a scene in their own style, once. `now` sets a watch
for the mask a hard job wants and the bank a small deck needs, not only
the payload. And the long persona takes the priced walk when it holds a
job, declining it only hurt or broke without one, so it works.

The audit: the seven campaigns' saves had reached forty-one of
fifty-four threads by play; the twelve unreached were gated by an origin
(seven), a specialist rank of three (three), a fight, and the record.
`test_every_thread_opens_for_the_right_life` builds the life each
thread's first scene asks for (the origin, the people, the runs, the
rank, the rung, the habit, the mark, the arrangement, the flags) and
holds that the scene becomes available: every one of the fifty-four
does. The one gate the audit moved was the reckoner's: the long life
had eight record lines of this character's own after two hundred shifts
and forty runs, so it opens on eight and speaks on twelve. Fifty-four
threads, a hundred and sixty scenes, a hundred and sixty-five decisions.
Seven campaigns alive, the long life to two hundred with four names.
`test.py` green at **19,614**, `--long` green.

### D170: What a release wants

The four things the release-candidate read said stood between here and
1.0, done where a script can do them. The Python floor the README
promises is held by `validate` now: every source file parses under the
3.11 grammar, so a machine that only has 3.14 cannot ship syntax the
floor lacks. The packaged build (`build.sh`, `dist/flatline.pyz`) was run
end to end through a pseudo-terminal with colour, at forty, sixty and a
hundred and thirty-two columns: no tracebacks anywhere; below eighty the
map and the tables wrap rather than break, and the game says so once at
startup now instead of leaving the player to wonder. The other half of
the story audit: `test_every_closing_stage_opens` builds, for every stage
after the first in every thread, the life its rules ask for with the
earlier stages seen and the clock far enough back, and holds that it
becomes available; the ten closings no persona had reached all do. The
door is a distance on `home` ("8,600c short of the stake, a number on
the name") rather than a number in `retire`. And the campaign personas
take a watch when `now` offers one, so the deck's finds line can move.
Seven campaigns clean; the long life alive at two hundred. What is left
for 1.0 is the author's: a read of the prose written since D157, an hour
in a real terminal, and two strangers. `test.py` green at **19,706**.

### D171: The Ninth Log

The second arc. The Archivist's nine logs belonged to nine runners; eight
are dead or gone; the ninth is on your board. Which runner is the city's
choice, made when the scene fires: the one you are bound to if you are
bound to anybody, else the one with the most work behind them, alive. The
engine learned to say a name: scenes and answers carry `{runner}` (and
`{partner}`, `{pet}`, `{familiar}`) and the world fills them at print
time, in the journal, the choose screen and the scene itself, with
`validate` holding that no text carries a token the world does not fill.
The arc opens once you have asked the Archivist about the logs and
finished your own posting. You know a thing about them that they do not:
tell them, keep it, or sell it to Static. Their posting comes through
Mara, and what you did with your own log decides what theirs is: read,
and they read theirs; archived, and the Archivist has two side by side
with the same Tuesday in them; wiped, and theirs comes out with a hole in
it the size of you. If you told them, two logs go on one table: run the
next one together (the tenth log with two handles in the header, and they
are in on your next job), keep it your own, or hand them to Deepwater for
the largest sum you ever saw cleared in one line. If you kept it or sold
it, they find out, and take the job you were going to take. If the ninth
runner dies at any point, the Archivist files the ninth with the eight and
says you are the one they have not filed. The answers land on the runner
(disposition, a bond either way), `who` shows whose log is the ninth, and
there are two names for it, one heroic and one vile.

And the first arc, read back through the systems that came after it: the
familiar on the deck reads your log when it comes out (a `log` beat for
all five), the partner reads the offer over your shoulder and asks what it
costs, the animal and the construct are there when the city is handed
back, and Mara, the Archivist and Osei have topics on the paper, the wash,
the ninth and the wall. `test.py` green at **19,838**.

### D172: The systems have stories

The author's note, that the game has developed a great deal since the
threads were written. Three rule kinds the story engine did not have:
`pet:` (any, kept for N shifts, a species), `familiar:` (any, N runs
ridden, dormant, a kind) and `titles:` (how many names this life has
earned). Four subplots on them. *The Thing You Keep*: a kid from the wet
end of the Ninth says the animal was theirs, and Tuck asks after it by
name; let them have it, keep it, or pay them twice. *The Thing That
Talks*: on the tenth run it rides, the construct says a name it should
not know, and Remnant goes very still, because it is the name that was on
a Sendai table; wipe it, keep it and write the names down, or give it to
Remnant, who sits with it and does not speak. *What They Call You*: Osei
uses one of the city's names for you across the bar; wear one (and the
city wears it after him), throw them all back, or ask what he calls you
when you are not there, which is shorter and worse and true, and a name
of its own. *The Stake*: Mara has noticed you counting; tell her, say you
are staying, or spend it on a night the Ninth talks about for a week. The
answers reach the systems: the flat is a flat again, the deck runs
cooler, the name is pinned. Every one of the five new threads was reached
by play in the six campaigns on the first run, and the fighter ran the
ninth log to its table. Fifty-nine threads, a hundred and seventy-seven
scenes, a hundred and eighty-three decisions, seventeen names.

### D173: The retrofit goes both ways

The four things D172 ended with. Lark, Ninety Seconds and the Weight each
close on a line the newer systems can read: who asks after Lark, who asks
whether you are clean, who was at the rail, with `{Partner}` (a runner's
name, or "Nobody") and `{called}` (the name the city uses for you, or "no
name yet"), the tokens capitalising at a sentence's start. The ninth
log's table has a branch for a runner already beside you, *Two logs, one
deck*, where the question is asked by somebody who has already answered
half of it, and its answers land on the same flags. Remnant has something
to say about the construct without a scene. The toy has a scene of its
own in the animal thread (the kid from the wet end sees it through the
door; Tuck says they had one for it). And the wash has a middle, *The
second line*, halfway through the ten shifts, where the book is open at
your page and the second line is a name that is not yours. Six campaigns
and the long life clean. `test.py` green at **19,875**.

### D174: A partner as a clause, and where the money goes

Two things from reading D173 back. The three closings listed "nobody"
twice when there was no partner, so the partner is a clause now,
`{Partner_or}`: "Vesper Okonkwo, who was beside you," or "nobody who was
beside you", and the sentences are written to take either. And the long
life's ledger, read off its transcript: of 57,443c earned in a hundred
and eighty-six shifts, 40,342c went to the street in seventy-seven
pay-offs, 19,550c to programs and chrome, 10,348c to the clinic, 6,552c
to arrangements. The street is a skill and the persona never used it; it
paid whenever it could. With a reserve on both answers that cost money it
still paid 25,517c of 46,303c. That is the persona walking every district
every rotation and answering every doorway with its wallet, not the price
list, and it is left as it is: a player who does that should end broke.
`test.py` green at **19,875**.

### D175: The four engineering items

While the author reads. The street already printed the odds beside
`talk`, `run` and `stand` on the first question, so that item was a
misreading of a transcript and needed nothing. The paper's collector is
named inside the scene now, "the book does, upside down across the
counter: Grieve", through a `{collector}` token filled before the scene
prints, instead of a line appended after it. The record marks the one
line only the profile keeps ("the profile's") beside its count. And
`q8_origins.py`: twelve characters, twenty shifts each, each following
the thread only their origin has, meeting who it asks for, running what
it asks for, taking its own posting, answering it. 11 of the twelve
played end to end by play, the rest of the way to the audit's
"verified by state". `test.py` green at **19,877**.

### D176: The ninth log finishes clean

The author's ask: the second arc cleans up and finishes clean, on every
branch. A runner handed to Deepwater is gone, not dead: a `gone` state on
the runner, read by `who` ("Gone. Filed to Deepwater. Their next posting
had no name in the header, and nobody has read one since.") and by
`betray`, distinct from the memorial a death gets, and a `ninth:gone`
rule beside `ninth:dead` so the two endings cannot both fire. Running the
next one together makes a partner of the runner outright (the
disposition is set to the bond's threshold and the bond latches on the
next turn, in their own words) rather than a number that might or might
not cross it. The generic closing is four closings, one per branch: ten
with two handles, ten in two bags, nine and a line cleared, ten and one
of them knows, each reading the runner as they are then. And the
afterwards knows: when the city is handed back, if there is a tenth log
being kept somewhere, the rest of it says so. `test.py` green at
**20,071**.

### D177: The city at leisure

The author's other ask: sub-quests deep enough to explore the city on
after the main arcs, or instead of them. Four long threads, six or seven
scenes each, on people the story had barely used, each with a job in the
middle and a decision the district remembers, opening on twelve runs or
the water settled, whichever comes first. *The Water Towers*, in the
Terraces: the Widow's third can fills slower because Kagawa has started
metering the hill, Mrs Adeyemi carries a jug up forty levels, the Man
With The Board has repainted it, and the schedule that says who gets water
when comes through the board as a job against the valve house; open the
hill, sell the file to Meridian, or give it back fixed. *The Valuation*,
on the Row: the Notary turns the ledger round and there is a number beside
your name that is not a bounty, Vig has sold it three times this week, and
Mr Sunday will buy the line; buy your own, let it stand, or take it out
of the ledger for Static. *The Second Edition*, in the Stacks: Ines Vale
has a proof with the city's name for you in the headline, Pip reads the
dishes, and the galley is yours for one job; correct it, pull the plate,
or let it run mostly true. *The Crane's Name*, in Freeport: the newest
crane was named by a vote for a dead runner and Carrion locked it out of
spite with Old Pike's own ICE; unlock it, and the docks ask whose name
goes on it, and one answer puts yours on a crane a metre high, facing the
water. Sixteen epilogue lines and a name. All four reached by play in
the six campaigns on the first run. Sixty-three threads, two hundred and
eleven scenes, two hundred and two decisions, eighteen names.

### D178: The small things, while the author reads

The animal and the construct fire twice now. After forty shifts kept,
the animal is off its food and the clinic will not see an animal; carry
it to the Blue Surgeon in a coat, sit with it for two shifts, or open the
door and do not close it, and the animal is brought back or is gone
accordingly. After twenty runs kept, the construct says a second name,
and it is yours; ask it what it remembers (a room, a table, a name, a
door), wipe it this time, or give it to the Archivist, who puts it in
the back room with the nine and says ten. The runners list marks whose
log is the ninth. And the origins persona takes a posting that beat it
once with a stronger life (rank four, a mask): eleven of twelve origin
threads end to end by play; the chorister's waits on a Kagawa exfiltrate
that even that life loses to lockdown by the fourteenth tick, which is
the driver's loudness and not the posting's, and the posting, which
does not expire, is content to wait. `test.py` green at **20,109**.

### D179: Networks with memory

The one thing. The city remembered everything you did and the networks,
where the player spends most of their minutes, forgot you the moment you
jacked out; every run was a fresh puzzle against a target that had never
met you. Now each faction's networks keep a memory of you on the city
(`world/memory.py`, plain dicts, every rule held by test), in four
parts, each built on something the game already had.

Doors stay cracked. What you cracked and left cracked comes up cracked
on their next network, the host known and held (a service, not a serial
number: the same door on the same kind of host in the same zone, or
failing that the same kind of host, or failing that anywhere), until the
faction patches it, one door a shift sometimes and more often the hotter
you are with them, which is a line on the wire and a ping to a `watch`
on the faction, which is a thing you can watch now. Residue teaches. A
trail you leave and do not scrub teaches them the techniques you used
(chain, keygrind, quiet, ghost, pretext, pivot, sidechannel,
impersonate, backdoor, nullsig, overclock); one seen twice is expected,
the connect says "they have seen you chain here before", and using it
again reads on every door; ghosting where they expect it is not nothing.
A scrubbed night teaches them nothing, which is what `scrub` is for now.
Back doors persist. A route found with `backdoor` is there next time; a
way left with `plant` ages, and a found one is closed, or, half the
time, left open for you, and you come up past the wall with somebody
watching the door you came in by. And the dossier: `render <faction>`
says what they know about you, the nights, the doors, what they have
seen you do and what they expect, what they patched, the traps.

On the first six campaigns and the long life with it in: no crashes,
four endings and a partner bond by play, and the memory speaking on its
own, a hundred and thirteen doors found still open, three hundred
patches on the wire, fifty connects told what they expected, five traps.
The runs are the game now, or the start of it. `test.py` green at
**20,120**.

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

**Shared:** `help`, `now` (D50: what an empty line means), `odds` (D14), `log`, `status`, `alias` (shell aliases, distinct from identity aliases; the collision is deliberate and the fiction absorbs it), `script`, `history`, `quit`.

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

### Phase 7: a world with a point in it

> **Status:** open, as of 2026-08-21. The foundation (D50, D51) is in. The
> items below are candidates, numbered so a session can pick one and say
> which; they are in the order I would do them, which is the order in which
> each makes the next one worth doing. Every one is held to the standing
> rules: D2 (the shell is the interface), D24/D51 (a claim the engine never
> reads is a lie), D34 (the tone budget), D38 (nothing cosmetic touches a
> number).

**Story and world**

1. ~~A decision must be read.~~ Done: D51.
2. ~~The spine.~~ Done: D52. Five acts, four endings, a door only crossings
   open.
3. ~~Story inside runs.~~ Done: D52, as `Posting` and `did:`. The
   mechanism is general; only the spine uses it so far. District and rival
   threads (4) should.
4. ~~Nine district threads, seven rival threads.~~ Done: D55 and D56 (the
   rivals as fourteen decisions at the bond latch, on top of D44's arc).
5. ~~Locations inside districts.~~ Done: D53, as `spots` and `visit`.
   Presence by shift is still open: the people are where they are at every
   hour, and a city where Mara is only in the bar in the mornings would be
   one more true thing.
6. ~~`news`.~~ Done: D53, and D56 writes scenes, decisions and what a run
   did to the city into it.
7. ~~`journal` as a real log.~~ Done: D62 (and `now` says when a choice
   is waiting, since D52).

**Accessibility and understanding**

8. ~~A HUD line after every tick-costing run action.~~ Done: D59, as the
   `hud` rice axis.
9. ~~"Previously" on resume.~~ Done: D62.
10. ~~Tutorial, second half.~~ Done: D60, nine more steps.
11. ~~`odds` for more verbs.~~ Done: D62: `odds strike`, and `odds <any
    verb>` for what it costs tonight.

**Visual**

12. ~~ICE portraits.~~ Done: D62.
13. ~~Attribute bars and a build label.~~ Done: D62.
14. ~~End-of-run card.~~ Done: D62.

**Fun and customisation**

15. ~~Run conditions.~~ Done: D61, eight of them.
16. ~~Scripts discoverable.~~ Done: D62.
17. ~~Naming things.~~ Done: D62.

**At the author's request, after the above**

18. ~~Map and navigation.~~ Done: D57. The city drawn, `walk`.
19. ~~The city large and full of stuff.~~ Done: D58. Forty-five places,
    twenty-two people, the street, a hundred and fifty-four events.

**Not on the list, on purpose**: a pager, numbered menus that replace verbs,
an alternate screen, a verb that acts for the player. (`walk` is `travel`
repeated and stops when the street stops you; it is the player's intention,
not the game's.)

---

### D180: The regular

The memory persona found the hole in D179 the same night it was built: a
runner who wanted to be one faction's regular got three jobs against them
in seventy-two shifts, because the board picked targets from the relations
table alone. The memory only matters if you go back, and nothing let you
choose to. Now the people who want a faction hit have heard who gets in:
`pick_target` weighs a faction by the nights you have spent inside their
networks (`KNOWN_PER_NIGHT` = 1.0 a night, five nights counted, on top of
the relations weight and under the D114 cap; measured over three hundred
boards, five nights takes a faction from 7% of postings to 24%, about one
a board, and no board is ever more than three of them), read off `city.memory` by
`City.known_networks()`. The board marks those names with `~` and says
what it means once; the manual's networks topic says a regular is a thing
you can choose to be. The memory now cuts both ways on purpose: the work
comes to the regular, and so does everything the target has learned.

### D181: The shutdown

The author's ask: an exit worth watching. `anim.shutdown` is the boot in
reverse and held to its rules: the deck reports itself off a line at a
time (the session closed, the link dropped, the buffer flushed, the dead
man handler stood down, the nerve cold, then each real component of the
deck you own, off), the city and the mark come back whole for a moment,
the windows go out a bank at a time, the mark decays from the right the
way it arrived from the left, and the trace beats slower until it does
not. Three seconds. It prints its last frame where it cannot animate,
Ctrl-C skips to the end, `--no-intro` skips it the way it skips the boot,
and it runs only after a clean quit (`Session.outro`, from `app.main` on
exit code zero), never on a crash. Tested the way the boot is: every rung,
every width, every banner style, no rng touched, nothing of the report
under the last frame.

### D182: The first hour, read back by strangers

The first testers on 1.0.1 said, in one line, that they were not certain
what was going on. Unpacked from their notes: almost nothing was
explained, not even the stats; the layout and the colours were confusing,
with colour "breaking mid-sentence"; the key/value lists read as text that
happened to wrap, and it took a while to see they were a grid ("background
colours on the keys, or a unicode line"); dense scrolling text felt clumsy
next to menus; somebody suggested a hundred and twenty columns instead of
eighty; and the pixel icons and network pictures were ugly, and good
descriptions would be better.

**What was true, checked against the code before anything moved.** `begin`
ran the prologue, handed the player to creation, and dropped them at `now`,
which said "buy siphon, take c007" with no framing; the tutorial that
explains all of it existed, twenty-five watching steps, and nothing started
it. `char` printed five attributes and five derived numbers with no gloss
anywhere on screen, and the tutorial's own step for it was stale (four
derived numbers, Integrity named, Composure and Cover not). Six colours
meant six things, and one paragraph of one manual topic said so. The
"breaking mid-sentence" was inline colour by meaning, which wrapping
preserves correctly, plus a few overuses (a whole warning paragraph on the
origin card in red). One real bug: a question's prompt bypassed the
renderer, so the prologue's last prompt arrived as `[err]it is coming[/]
>` in every mode, and readline was never told about escapes in a prompt.
`Console.kv` was a muted key, two spaces, and a plain value.

**What changed.**

1. **`legend`, and `help colours`.** `theme.MEANINGS` is the one place
   that says which idea is which colour, `legend` prints each in its own
   colour with what it means (and says so, in words, when colour is off),
   and it is on the lost-right-now list. `validate` holds every role in
   it to a palette field and the six game concepts to being in it.
2. **The grid.** A rule in the border colour between every key and value,
   carried down wrapped values. One change in `Console.kv`, so every
   screen has it, colour or not.
3. **The sheet says what every number is for.** `Attribute.gloss`, three
   or four words beside each attribute, and `DERIVED_GLOSS` beside each
   derived number with the attribute that feeds it; `validate` holds both
   sets complete and short.
4. **Question prompts rendered.** `ui.prompt_render`: the same rendering
   as everything else, with every escape fenced in `\001` and `\002` so
   readline does not count it.
5. **The tutorial turns itself on.** The first runner on a profile gets
   it at the end of creation, said plainly, with `tutorial stop` named.
   The sheet step teaches the screen (title, rule, grid, prompt) and the
   ten numbers correctly; a new step teaches `legend`; the current step
   is repeated as the first line of `now`, because a screenful of
   scrollback later that is where a newcomer looks. Twenty-six steps.
6. **Words where the pictures were.** The render mode defaults to the
   mark: the arrival paragraph on connect, the render string for the icon,
   the looks line on the sheet, the ICE's text mark, and no pixel art
   anywhere, the prologue's included. `rice render picture` brings all of
   it back; nothing was deleted. The origin card's complication is a
   warning lead and plain text rather than a red paragraph.
7. **Columns wider than prose.** `TABLE_WIDTH` is a hundred and twenty and
   `Caps.table_width` lets a table take it when the terminal has it;
   prose stays at seventy-six. Sixty to eighty characters a line is the
   readable range, and the tester's complaint was density, which width
   makes worse. The map's district list already used the full width.

**Not done, and why.** Menus: D2 stands, the shell is the game. Prose at a
hundred and twenty: declined, above. The title skyline: kept, it is the
title card and not an in-game picture. Held by `test_the_first_hour` and
the six-campaign regression.

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

### 2026-08-15 (c): the character is the address

**D49.** Reported as being dropped into a character without asking, which
turned out to be one of six problems with a single cause: characters were
addressed by slot, everybody shared the slot called `default`, and there was
no screen anywhere that listed who you had.

The serious one was silent and permanent. `new --force` did not abandon the
loaded character, it destroyed them: same slot, next autosave, gone. Each
character is filed under their own handle now, `new` saves whoever is here
first, and `delete` is the only thing in the game that removes anybody.

The oldest one was the first sentence a new player ever read. The splash said
`load` to continue a character; `load` puts a program on a deck; the command
is `restore` and is named that *because* of the collision. The general rule
that came out of it is that a verb the game offers has to work at the moment
it is offered, which is a stronger check than "does this command exist",
because `load` exists.

`characters`, `switch` and `delete` are the system. A finished character
stays on the roster and can be read but not played, which required noticing
that death previously changed nothing at all about what you could type.

`validate.py` clean, `test.py` green at **12,932 checks**. All seven soaks
clean.

### 2026-08-21: the onboarding layer

**D50.** Asked to make the game friendlier for people who have never played
a command-line game, without losing any of the depth. The diagnosis, from
playing it cold, was three silences rather than any missing system: a bare
prompt after the splash, `new` as a hundred-line list followed by flag
syntax, and no answer at all to pressing Enter.

What shipped, all inside D2: an empty line prints "what now", which is the
next real move computed from state plus the verbs that matter here (`now`,
`next`, `hint`, `menu`); `new` is three questions with a one-screen origin
table, `read <n>` and `random`; `spend` proposes and, if told to, makes the
origin's usual opening spend; row numbers work on every list (`take 2`,
`buy 3`, `travel 1`, `switch 2`); typos get "did you mean"; arrival and
`look` end with a `Here:` line of typeable verbs; the splash has a start-here
block for a first-timer. The question mechanism is `Session.ask`, and it is
deliberately small: one pending question, the next line is the answer, empty
backs out, `quit` is still quit, never inside a run, dropped with a warning
if a script trips it, and the tutorial waits for it to finish.

**Two things the harnesses caught while writing it.** `validate.Report.check`
returns `None`, so the first draft of `check_guide` broke out of its loop on
the first legal step and reported every origin as spending nothing; the
check now reads the boolean it already had. And the first `now` panel for a
fresh character named `spend` as the next move, which nagged anybody who
had said "keep them" a minute earlier; it is the last line now, after the
real move, and only while the character has not run.

**One deliberate non-feature.** The suggested spend is capped below the
attribute ceiling and at three new skill lines. Both caps are D10 and D12
saying the same thing from the other side: the origin is a starting shape
and not an optimum, and a suggestion that min-maxed would be a build
decision wearing a convenience's clothes.

`validate.py` clean, `test.py` green at **13,119 checks**, `./build.sh`
clean. 117 commands, 38 topics. The seven soak scripts from 2026-08-15 are
not in the repo and were not re-run; nothing here touches what they measure.

### 2026-08-21 (b): a decision must be read, and Phase 7

**D51.** Asked for a game with sub-stories worth doing and a main story with
paths and endings. Before writing any of that, measured what the story layer
already did with what it had, and the answer was nothing: forty-five choice
flags, and a grep found none of them read outside `threads.py`. So the first
thing was not a new scene, it was the rule that makes a scene worth writing.

Readers added, all as data the validator can see: `not:<flag>` in story
rules; story rules on NPC presence, work, favours and counters; forty-one
consequence events with `requires`; `STREET_RIDERS` on arrival risk;
`PATRON_RIDERS` on who posts work; the spine reading into `legacy.ending`;
an `EPILOGUE` of one line per decision printed at both endings; and
`Choice.gives`, because the courier's package contained a component the
engine never handed over. `check_consequences` requires every decision to
have a reader and an epilogue line, and every rule anywhere to name a flag
something sets.

**Two things the harnesses caught.** The event coverage check ("no district
and shift can ever show it") ran `eligible` with no story and so rejected
every gated event; it now grants the story and leaves the accounting to
`check_consequences`. And the first draft left `maint_asked` read by nothing
but the ending: the choice sets `vance_file` alongside it, which is read, but
the decision itself was not, which is exactly the distinction the rule
exists to draw. It has an event now.

**Phase 7** written into the phase list: seventeen numbered candidates,
story first, from the assessment that produced D50 and D51. The spine is
next.

`validate.py` clean, `test.py` green at **13,235 checks**, `./build.sh`
clean. 92 ambient events (51 weather, 41 consequences) at 55/34/11 against
the budget.

### 2026-08-21 (c): the spine

**D52.** Deepwater rewritten as the main arc: nine scenes in five acts, with
more than one way into each, three new decisions in the middle (read the
log, give it to the Archivist, wipe it) and a fourth ending at the end that
only opens through Lark and the archive. The mechanism underneath is
general: `Stage.posts` puts a held contract on the board, `label` names the
record so the run is about the thing the scene said, and `did:<thread.stage>`
is how the next scene knows. `Choice.ends` is the third exit.

**Two things found on the way.** Every origin thread had been printing
literal backslashes at its paragraph breaks since it shipped (`\\n\\n` in
the source); `test.py` now refuses a backslash in any scene. And the brief
named "the record they want" until the host was probed, which is right for
a board job and coy for a record the scene has already named: a labelled
record is named at the door.

**One thing deliberately left.** A scene unlocked by a scene arrives on the
next check rather than in the same breath. Cascading would be truer to
"the moment its condition holds" and would also dump three scenes in a
row on somebody who looked around once; the next `look`, `talk`, shift or
run brings it, which is soon enough and reads better.

`validate.py` clean, `test.py` green at **13,387 checks**, `./build.sh`
clean. 18 threads, 43 scenes, 50 decisions, 97 events at 55/34/11.

### 2026-08-21 (d): the city, deeper

**D53.** The tone pass the author asked for, done as ground rather than as
adjectives. Read the existing prose first and found the voice already
right, and the city thin underneath it: one paragraph per district at
every hour, nowhere inside a district to stand, danger below an incident a
single warning line, and `city.news` a scrollback nothing read.

Wrote twenty-seven district-by-hour scenes, twenty-seven places with night
variants and who is usually there (`visit`, free, counts as meeting), six
close calls that cost three attention, `news`, and fourteen events, eight of
them absurd, which lifts the absurd share from the floor of the D34 budget
to the middle of it. `check_city_texture` holds every district to every
hour and every place to being findable by its own name.

**One thing it turned up.** `city.news` was the project's bug class in a
world field: written on every shift, trimmed to forty, saved and loaded,
read by nobody. `news` reads it now, and the next pass should write thread
outcomes and posture moves into it, because a wire that only carries what
the shift tick happened to say is a wire with one correspondent.

`validate.py` clean, `test.py` green at **13,443 checks**. 111 events at
52/31/17.

### 2026-08-21 (e): voices, hours, and nine places with a thread in them

**D54, D55.** The first three of the four things the city was thin on, in
the order they were listed. Seventeen people went from three lines to six
and from two topics to four or five, each written in their own register,
and `validate.py` now holds that floor. Hours: fifteen of the seventeen
keep some, the machine and the dark room keep none, and `look` tells you
who is away and when they are back, once you have met them. And nine
threads rooted in the districts, in `content/arcs.py`, twenty-two
decisions, four postings, every decision read.

**One thing found.** The rivals did not need threads: D44 gave them an arc
(bonds) that I had not re-read before listing the work. What they lack is a
decision at the latch, and that is the next pass, not seven parallel
threads.

**One thing worth writing down about the tooling.** Patching seventeen
`Npc(...)` blocks by anchor, the anchor for "the end of the call" has to be
the last `),` in the block and not the last `),` followed by a newline,
because the block as sliced ends before its own newline. It took two
attempts and one syntax error, which `test.py` caught before anything
shipped, which is what it is for.

`validate.py` clean, `test.py` green at **13,619 checks**. 27 threads, 67
scenes, 72 decisions; 132 events at 52/32/16.

### 2026-08-21 (f): the other runners decide, and the wire

**D56.** The last of the four: the rivals, and `news`. D44's bond latch now
writes a story flag, fourteen scenes read it (seven runners, two sides,
each in their register), and the two answers each are read by something
real: half-price hires for a partner you said yes to, silence on the shift
boundary from a nemesis you paid, four events and twenty-eight epilogue
lines. `news` carries scenes, your decisions in your own words, and what a
run did to the city.

**One thing it turned up.** The bond test wanted to latch Vesper by warmth
alone and the latch refused, correctly: D44 gates on history as well as
disposition, and a test that forgets the second gate is a test of the wrong
thing. `rival.jobs` is the history.

`validate.py` clean, `test.py` green at **13,673 checks**. 28 threads, 81
scenes, 100 decisions; 136 events.

### 2026-08-21 (g): drawn, walked, larger, fuller

**D57, D58.** The author's two additions to the list: the map, and scale.
The map is drawn now, the same shape every time, with you and the job and
the danger on it, and `validate.py` holds the drawing to the graph so it
cannot lie. `walk` goes the whole way and stops when the street stops you.
And the city is larger where it counts: forty-five places, twenty-two
people, a street with three things in it at every hour, a hundred and
fifty-four events, all of it counted under the map rather than claimed.

**One thing found.** Dimming the map's connectors with a `replace` after
drawing broke the ASCII rung, because `/` is the character in `[/]`. Every
connector is dimmed at construction now. The width check caught it; the
picture would otherwise have rendered as markup soup for exactly the people
whose terminals cannot draw the Unicode one.

`validate.py` clean, `test.py` green at **13,757 checks**. 120 commands.

### 2026-08-21 (h): the readout

**D59.** One dim line after anything that spends a tick inside a run: the
trace as a bar, the noise here, the tick, the alert. The prompt has always
carried the trace and new players do not read the prompt. It is the seventh
rice axis, because the shell is the right place for a preference about how
much the stream says, and the catalogue's own rule (an axis with fewer than
four options is not a choice) is why there are four states and not two.

`validate.py` clean, `test.py` green at **13,766 checks**. 71 pieces across
7 axes.

### 2026-08-21 (i): the tutorial goes past the door

**D60.** Nine more steps after `jack out`: the residue landing, `rep`,
`look`, `talk`, `visit`, `journal`, the empty line, `retire`, and a second
contract. Same mechanism, same rules, and the closing now points at the
map, the walk and the wire.

**One thing the test taught.** A walk through the steps by `tutorial skip`
has to expect the steps that are already true to complete themselves on
the way past: `out` and `settle` are both satisfied for a character who has
run once and left nothing pending, so skipping toward `settle` lands on
`rep`. The tutorial was right and the first draft of the test was not.

`validate.py` clean, `test.py` green at **13,788 checks**. 25 tutorial
steps.

### 2026-08-21 (j): tonight, inside

**D61.** Eight run conditions: drawn at the door from their own stream,
announced with their numbers, shown on `status`, read by the engine in the
one place each applies, in the crack sum by name so `odds` prints them,
and held by `validate.py` to changing something and to staying inside
weather. The other runner is the one with a tick of its own.

**Two things found.** `Rng.STREAMS` is a declared list, correctly, so the
new stream had to be declared before the first draw, which the first test
run said plainly. And `odds` wants a probed host, which the test learned
by asking for the odds on a host it had only scanned.

`validate.py` clean, `test.py` green at **13,882 checks**. 39 manual
topics.

### 2026-08-21 (k): the rest of the list

**D62.** The eight remaining Phase 7 items, each a surface that was not
saying what it knew: the journal as a log of decisions and what they cost,
previously on resume, `odds` for strike and for any verb's cost tonight,
ICE portraits, attribute bars and a build label, the boxed end-of-run card,
a `now` line for the empty script library, and names for the deck and the
safehouse. With that the Phase 7 list is closed; the next list should come
from playing it.

**One thing worth writing down.** The batch patched seven files by anchor
in one script and the script stopped at an assertion that expected two
wake sites and found four. Two of the four were the escort's and the
ally's exposure to countermeasures, which wake the same way and deserve the
same mark, and the assertion was the only reason anybody looked.

`validate.py` clean, `test.py` green at **13,908 checks**.

### 2026-08-21 (l): the mechanics read back, part one

The author asked for a deep dive on the mechanics: stats, hacking, gear,
drugs, all of it, nothing thin or unread, balance fixed, and special items
to reward exploration. Four read-only audits went over the source first,
one per subsystem, and every one of them came back with the same class of
finding this project has been fighting since `presence`: numbers declared
and never read. **D63 (a)** is the engine half: the deck hears chrome and
bench work, Tempo banks free actions, multipliers bank their fractions
instead of rounding them away, a lock-on is a printed check, four chrome
riders and a drug rider do what they said, Architecture and Sabotage have
reads, Impersonate and Sidechannel and Script do what their text says,
black ICE names itself on the tell, Composure is read when the room turns.
`check_reads` now holds every effect key and every rider to having a
reader outside content, which is the guard this whole bug class wanted.

`validate.py` clean, `test.py` green at **13,980 checks**.

### 2026-08-21 (m): the mechanics read back, part two

**D63 (b)**, the intrusion layer: `mask` decays and has a floor, sealed
records can be taken shut for part of the fee and the door says so, armour
wears out, black ICE stays with the factions that have it, three riders
escalate by what they declare, Gallows cuts a route, the herder closes the
way back, and every faction's doctrine is a set of numbers the generator
and the run read. The soft-warden rule and the escort fallback close the
two ways a run could be generated unfinishable for a particular build.

`validate.py` clean, `test.py` green at **13,973 checks**.

### 2026-08-21 (n): the mechanics read back, part three

**D63 (c)**, the catalogue: `inspect` for any thing in any catalogue, a
bare `load` that lists the bag, `fit` in the city, components that sell,
passives that count once per kind, five program riders that do what their
notes said, honest notes everywhere else, six mid-tier parts, and an
antenna trade with two real ends.

`validate.py` clean, `test.py` green at **14,022 checks**.

### 2026-08-21 (o): the mechanics read back, part four

**D63 (d)**, the vices: Threes gets a stake term and faster learning, so
the card room is a few evenings for a build rather than an income; every
lender's visit now takes more than its interest put on; a hook-4 drug asks
before the first dose; Ash Tea says what it cost the other habits.

`validate.py` clean, `test.py` green at **14,034 checks**.

### 2026-08-21 (p): the mechanics read back, part five

**D63 (e)**, the relics: fifteen things there is one of, each with a
history, nine found at a place at an hour after something has happened and
six handed over by decisions in the story, with a rumour per find that is
weather until the thing is found and then stops. `check_relics` holds the
layer to exactly one route each and never a price tag. With that the deep
dive the author asked for is landed in five commits, and the thing worth
writing down is that all four audits found the same bug in different
clothes, numbers declared and never read, and the guard for it now lives
in `validate.py` rather than in anybody's memory.

`validate.py` clean, `test.py` green at **14,067 checks**.

### 2026-08-21 (q): the leftovers, one at a time

The author asked for the items the deep dive had left alone, one at a time.
First: the Switchboard lends a newcomer 1,200c rather than nothing.
Second: a trap springs on contact, and a crack from the next host over is
not contact; `crack` and `chain` only spring traps on the host you stand on.
Third: a lender's visit to an empty account counts the room at half
(`Debt.assess`/`settle`): the cash first, the incident for half of what the
cash did not cover. The debt used to drop by the whole visit whether or not
a credit changed hands, which made an empty account the cheapest way to pay.
Fourth: a runner's loan is a tab (`City.tabs`): they mention it every nine
shifts it stands, in front of people, at three disposition a mention; `ask
<name> repay` pays it down and clearing it gives half the favour's cost back.
Fifth, **(f)**: a program runs at full rating only for somebody who can
drive it. On every check that reads a rating, the rating is held to the
governing skill's rank plus two (`programs.held`, `HELD_BY`), and the term
prints as "held to N by Intrusion 2" when it bites. Training competes with
buying without the cheap programs getting worse; `inspect` says what a
program runs at for you.

Then, from the author's first play test: `unload` takes a row number and a
bare `unload` lists; `deck` and the bag print what each program is for under
its row; a new character's first board always has a job the kit can do
(surveil) when the origin shipped without a payload; Siphon is 900c so the
poorest origin can reach it; `now` names the cheapest payload, its price at
the nearest market, and `borrow` when that is more than you have; `new`'s
closing lines point at `load` and `inspect`.

### 2026-08-21 (r): the play test, and the city grows

The author played, and the list was: the leftovers from the deep dive
(done, one at a time: the Switchboard floor, traps on contact only, in-kind
collections at half, a runner's loan as a tab, programs held to rank + 2),
`unload` by row and programs that say what they are for, a first board the
kit can do, `reset`, networks in six shapes with the brief reading the
sums, and the city grown by three districts with four people, nine places,
three threads, fifteen events and a relic. `validate.py` clean, `test.py`
green at **14,814 checks**. Next, by the author's direction: physical
danger and skill in the real world (D65), then more to explore, meet, find
and do.

### 2026-08-21 (s): the street is real

**D65.** The street can hurt you, cost you, and at the top of its ladder
kill you, after it has told you so in as many words; you get out of it by
running, talking, paying or standing there, each a printed check on two
new skills; errands are the work that needs no deck. `validate.py` clean,
`test.py` green at **14,896 checks**.

### 2026-08-21 (t): the street reads back

Three encounters that are decisions coming to find you (Carrion's two from
the back of the queue, somebody from the Stacks with a paper, a courier
with an empty case), two events for what the street remembers, origins
that start with a street rank (gutter, protege and ex-enforcement with
Streetcraft 1, the courier with Fieldcraft 1), the sheet naming who has
warned you, three people with an opinion about the street, and three more
relics in the new districts (Pip's Dish, A Ledger Page, The Bell That Does
Not Ring). `test.py` green at **14,901 checks**.

### 2026-08-21 (u): more to meet, find and do

Two more partner relics (Saint's Reliquary, Moth's Lantern), two encounters
from the runners who decided against you (Hound's people, a word from
Vesper), three more people with offers (Osei at the back bar, Mrs
Achterberg who fits the Vertical, the Widow at the water point), the woman
who does not sing (a side thread of the Hall that crosses the spine, three
decisions, read back), and `help street` in the tutorial's closing. Counts:
21 relics, 32 threads across 95 scenes and 110 decisions,
29 people, 186 events, 14 encounters. `test.py` green at **14,940 checks**.

### 2026-08-21 (v): the street, second pass

A warning on the street lapses when the faction stops looking (no bounty,
attention under 25), so the telegraph tracks the threat. Two more kinds of
errand: walking somebody across the city at their pace (worth stopping),
and collecting a debt with your voice (a printed Guile check at a door; a
press in a doorway when it fails). An errands counter in the meta layer. A
soak test that does what `now` says for sixty commands across fourteen
seeds and four origins, answering the street when it stops them, and must
never crash. `test.py` green at **14,956 checks**.

### 2026-08-21 (w): paying the street

Standing arrangements with factions (`arrange`): a money sink that is a
real decision against heat and bounties, collected on the shift tick,
easing `arrival_risk` and capping the encounter tier. `now` says rest when
you are hurt. `test.py` green at **14,970 checks**.

### 2026-08-21 (x): the street pays back

Three traits that are the street on a sheet (Local, Carried Worse,
Unbothered), a rice mark set earned by street work (Kerbside: what a
courier chalks on a wall for the next courier, at twelve errands), and a
heavier offline soak: forty seeds, a hundred and fifty commands each,
random answers to the street, random verbs inside runs. Zero crashes, 393
encounters and 459 errands exercised, one flatline and nobody killed in the
street, which is about right for characters answering at random. 29 traits,
72 rice pieces. `test.py` green at **14,984 checks**.

### 2026-08-21 (y): the chain that ends in a run

D64 (c). Four dead ends in the advice, found by making a character do
exactly what `now` says for four hundred commands and watching where it
looped: the shop it could not afford, the buy nobody named, the load with
no memory, and the board's first row. Plus the tier ladder in generation.
A follower now goes take -> errand -> buy -> unload -> load -> travel ->
jack in and finishes runs. `test.py` green at **15,074 checks**.

### 2026-08-21 (z): something in every district

Three relics for the three districts that had nothing to find (Boxstep,
the Vertical's own gait model, from the tailor; Lost Property, the Watch's
retention schedule, from the desk; The Water Bearer, a shoulder brace that
has been up six floors every day for forty years, from the Widow), six
more places to stand in the new districts, and a validate rule that every
district has something in it to find. 24 relics, 60 places.
`test.py` green at **15,077 checks**.

### 2026-08-21 (aa): people are leads

Talking to somebody in a district where something can be found gets you
the rumour, once each (`heard:<item>`), with the place named, and it goes
on the wire. The ambient rumour is the city telling you when it feels like
it; this is the channel the player controls, and it is the payoff for
meeting people. `help relics` says so. `test.py` green at **15,082 checks**.

### 2026-08-21 (ab): the advice never loops

Campaign-scale simulation (fifteen hundred commands, a policy that trains,
rests, buys and pays) turned up three more advice loops behind the four
from (c): the refusing `spend`, the refused `travel`, and the multi-hop
walk whose danger was only checked one hop in. All closed, with
`test_advice` to keep them closed. `test.py` green at **15,293 checks**.

### 2026-08-21 (ac): streets that are only one street

Six encounters written for one district each (`Encounter.districts`, and
weighted at two and a half times an anywhere one when it fits): the
Vertical's lobby deciding about your gait, a coat on the Row walking
beside you for a hundred yards, somebody in the Hall's queue saying a name,
a checkpoint that was not there yesterday in the guarded districts, the
Terraces stairwell at shift change, and three of somebody's in the Stacks'
ink store stopping an edition. 20 encounters now. The street also stops
waiting: three non-answers and it takes the one you were giving it by
standing there (`PATIENCE`), and the re-ask keeps its own prompt instead of
degrading to a bare question mark. `test.py` green at **15,320 checks**.

### 2026-08-22 (a): size, the clock, and the fee

D66, measured rather than guessed: `scratchpad/sizes.py` ran 24 networks
per band across four factions and three sizes before and after each
change. Size is breadth now, the size itself is cover, quiet ticks are
cheap, the alert can come back down, `wait` exists, and the fee curve
matches what the attempt is actually worth. `test_scale` holds the lot.
`test.py` green at **15,350 checks**.

### 2026-08-22 (b): the city is a place

D67. Twelve districts written out with what they are built of, what they
work at, their quarters and what is past their edge; `district`; sixty
more street lines; twenty crossings; the map's own logic; and the service
difficulty curve fixed so the first job in the game is one a starting deck
can open. `test_place` and `test_ladder`. `test.py` green at **15,360
checks**.

### 2026-08-22 (c): breadth

D69. Eight programs, nine chrome, two icons, and the end of three pure
upgrades, all from an audit against the twelve playstyles. 68 programs,
47 chrome, 10 icons, 24 of everything one of a kind. `test.py` green at
**15,510 checks**.

### 2026-08-22 (d): help, breadth, and two more ways to be somebody

**D68**, the help: eleven stale claims corrected (the alert page still said
it never came down), a `networks` topic for the words `board` and `map`
print, an owned search word opens its own page, sub-headings drawn from the
prose's own shape, detail for twenty-five bare verbs, and the game's nouns
rendered in the game's colours. The board's table now carries size and a
`reads` column that says doors and room, because measuring showed the
doors open at corporate posture and the clock is what kills you.

**D69**, breadth: eight programs and nine chrome filling the gaps an audit
found (daemonology had no tier-one program at all; the two street skills
had no gear whatsoever; four declared skill keys were granted by nothing),
two icons wearable at zero drift, and the end of three pure upgrades.

**D70**, two origins from the new districts, with signature verbs, riders,
and origin threads that cross their districts' own.

`validate.py` clean, `test.py` green at **15,641 checks**.

### 2026-09-01 (a): three players, one afternoon

The method: three play-tests at once, each with a different brief, each
reporting problems with quoted evidence rather than impressions. A
first-timer who did exactly what `now` said for ten contracts (Rook, the
protege). An explorer who ignored `now`, walked all twelve districts and
talked to twenty-two people (Vesna, the defector). A run specialist who
typed every verb by hand across sixteen jack-ins and severed on purpose
(Sable, the chromed). Between them: thirty-eight numbered findings, four
of them blockers, and no crashes in roughly nine hundred commands.

### 2026-09-01 (b): the people are the story

D86. Scenes fire where they are set (forty-two of them declared a district
nothing read), `asked:` is a rule, talking is meeting, arrival names the
people, and `now` has a reason to go somewhere. Three scenes at most per
command, the ones for this street first. Bare `talk`, `ask` and `sell`
answer the question asked.

### 2026-09-01 (c): the advice reads the night before

D87. Every run is written down and `log` reads it back in the city. The
recommender declines a contract that has cut you loose twice and says
why in the history's own numbers; the plan buys the breaker's rank first;
one loadout plan replaces three fit steps that argued; nobody is told to
rest against a bounty; an arrangement is a passable street; real shop
prices in the advice; `walk` stops when the street does; a verb typed at
a yes-or-no question is a verb; late is late.

### 2026-09-01 (d): the wall and the clock, and what is remembered

D88 and D89. `native` walks through a warden, the impossible is refused
for free, `pivot` is offered on an open hop, the board reads a badge desk
against the build, the brief reads the clock for the whole night, and a
severed connection keeps you out of the chair for two shifts with a
wrecked deck refused at the door. Then the two additions: the construct
that cut you loose is on the route next time, awake and named, and the
other runners can turn up inside a network with what it means decided by
their opinion of you. Four new suites. `validate.py` clean, `test.py`
green at **16,843 checks**.

### 2026-09-02 (a): the second look

D90. The three second-wave testers were cut off by the session limit
before they could report, but one had already reproduced a loop the first
wave missed: `connect --present` advised twelve times at one warden, each
refusal stepping the alert. Fixed with memory and a floor on the odds.
Plus the cheap answers to the first wave's open list: `people`, honest
presence text, variety in the recommender, the scrap hint, the safehouse
ladder, the free-action line. `test_second_look`.

### 2026-09-02 (b): the second wave, and the response

D91 and D92. The resumed testers: a crash in the rival incident (the hook
line under the wrong `if`), two more advice loops (a sealed record, one
door), the recommender with no ceiling, `now` cutting the go step, scenes
narrating a history you did not have (`Stage.after`, one per thread per
command), grudges that never formed, and a loadout plan that evicted a
striker's weapon. Then the response: six loud ticks at red and a hunter
arrives. `test_second_wave`. `validate.py` clean, `test.py` green at
**16,901 checks**.

### 2026-09-02 (c): the way in

D93. The board reads the depth of the job in badges before the walk, and
`legwork intel` names the wardens on the route and whether you could
answer them. `test_the_way_in`.

### 2026-09-02 (d): more to say

D94. Topic variants keyed by flags, six of them on the spine.
`test_more_to_say`.

### 2026-09-02 (e): the door, the debt, and the systems

D95 and D96, from the third wave's endgame and systems testers. Origin
debts with their own terms and instalments, lender work that pays them
down, a review that moves the number, a name that has to have held, a
bench that lists again, a script that can leave. `test_the_door`.

### 2026-09-02 (f): the corporate night

D97, from the third wave's corporate tester: sixteen corporate runs, none
finished, the causes named. The exit priced with a tick for the exit,
the breaker's price in the clock and on the board, lockdown counting
toward the response, failure hardening the target less and saying the
number, the clock on the board, a hops column on `scan`.
`test_corporate_night`.

### 2026-09-02 (g): the named shelf

D98. One line of tier-two stock per market per cycle, turning through the
categories, said on the wire. `test_named_shelf`.

### 2026-09-02 (h): and in nights

D99. The epilogue reads the career. `test_and_in_nights`.

### 2026-09-02 (i): the fourth wave

D100. Pivot-first is the corporate answer (nine paid in fifteen against
one). The first-timer's dead ends, the honest career's deck spiral, the
lender's work on the board. `test_the_fourth_wave`.

### 2026-09-02 (j): the job itself

D101, from the fifth wave: the objective verb priced on the board, in
the recommender and in the brief's patience; the errand that paid nine
times; the escort waited for; the response counting loud ticks only;
burn named when a bounty walls the board. `test_the_job_itself`.

### 2026-09-02 (k): pictures

D102. Two pixels a cell: twelve procedural renders in the factions' own
colours, revealed on connect, a `render` command, a `rice render` axis,
the flatline animated, the sever torn. `test_pictures`.

### 2026-09-02 (l): the instrument

D103. A colour in the markup, gradient meters, the coloured sparkline on
the card, and `rice hud panel`. `test_the_instrument`.

### 2026-09-02 (m): the schematic

D104. `map` in a run draws the network as a schematic: zones as columns,
hosts as labels, edges as wiring, the route to the job lit.
`test_the_schematic`.

### 2026-09-03 (a): your icon, drawn

D105. The ten icons you can wear are pictures now, revealed on connect
after the faction's cyberspace and shown on the `icon` screen.
`test_player_icons`.

### 2026-09-03 (b): more colour, and a gallery

D106. Six new palettes (Sendai, Meridian, Chorus, Freeport, Ember, Void),
each earned differently, and `rice gallery` to see them all live.
`test_more_palettes`.

### 2026-09-03 (c): more prompts

D107. Angle, Tag and Rail prompt shapes, and `rice gallery` renders the
prompt for the prompt axis. `test_more_prompts`.

### 2026-09-03 (d): a portrait

D108. A bust drawn from the appearance features, on the `char` and `self`
screens. `test_the_portrait`.

### 2026-09-03 (e): the way it arrives

D109. Five reveal styles for how a picture lands on connect (dissolve,
scan, wipe, flash, instant), an earnable axis. `test_reveal_styles`.

### 2026-09-03 (f): the ICE, seen, and the screen disrupted

D110. A picture per ICE behaviour at the tell, and a static burst that
disrupts the display on the lethal beats. `test_ice_and_disruption`.

### 2026-09-03 (g): a shape per host

D111. A one-cell glyph per host type in front of its name on `scan`, so
the segment reads as shapes before it reads as words; the auth-server
lattice made legible against the boxes. `test_host_glyphs`.

### 2026-09-03 (h): the boot draws a city

D112. The boot comes up on a full-colour city, a synthwave sky over a
skyline, before the wordmark and the trace. `test_the_skyline`.

### 2026-09-03 (i): a bestiary

D113. The player icons redrawn three times (people, sigils, then the fix:
creatures and characters read by silhouette), and four more to buy.
`test_player_icons`.

### 2026-09-03 (j): the story, play-tested

D114. Three testers on the story and quest layers only (a follower of
`now`, a completionist, a lore-reader). Verdict: the writing is the
strongest thing in the game and a new player can miss it. The first-runs
signposting fixed, then a second pass: the story hook, board variety, one
name per job.

### 2026-09-03 (k): the cold open

D115. `begin` opens on a job before there is a you: four beats as a dead
runner, Switchboard in your ear, the real verbs taught by being used.
`test_the_cold_open`.

### 2026-09-03 (l): the spike and the payoff

D116. The two beats a run was missing: the static burst fires on the
crossing into red or lockdown, and only on the crossing, and the objective
landing takes the screen.

### 2026-09-03 (m): ambitions

D117. Seven ambitions, a visible ladder between a job and the story, each
a predicate over state the game already keeps. `test_ambitions`.

### 2026-09-03 (n): the lifeline

D118. A fading reminder under the prompt for a brand-new runner: press
Enter, or type `now`. Shows a handful of times, never in a run, and stops
for good once used. `test_the_lifeline`.

### 2026-09-03 (o): the reckoning

D119. The nemesis arc gets an ending past `RECKON_AT`: a scene, a choice,
a resolution that is not a payment. `test_the_reckoning`.

### 2026-09-03 (p): the nemesis in the run

D120. A nemesis inside the network is a race for the objective, warning
first and then taking it. `test_the_nemesis_run`.

### 2026-09-03 (q): the partner

D121. The mirror: an uninvited partner in the run hands you what your
state most needs, and a partner who has run beside you enough offers to
crew for good. `test_the_partner`.

### 2026-09-03 (r): the ways in

D122. `approach`: breach, talk your way in on Guile and Subterfuge, or buy
in, so the build matters for the run itself. `test_the_ways_in`.

### 2026-09-03 (s): the way back in

D123. `plant`: two ticks and a lot of residue leave a backdoor onto that
faction, and the next run comes up past the wall. `test_planting_a_way_in`.

### 2026-09-03 (t): the changing world

D124. Factions have a grip that a campaign actually moves, and `world`
shows the power map. `test_the_changing_world`.

### 2026-09-03 (u): swagger, and the legend

D125. A clean run sometimes hands you a line to enjoy it by, and a career
builds a legend the city repeats. `test_swagger_and_legend`.

### 2026-09-03 (v): the lifepath

D126. After the first job, once, the origin's complication comes to find
you. `test_the_lifepath`.

### 2026-09-03 (w): tactic tools

D127. Shroud and Sledge, gear that grants a tactic rather than a number,
the way payloads already worked, so D10 holds. `test_tactic_tools`.

### 2026-09-03 (x): the street can be fought

D128. The author's call, unlocking half of D2: a fifteenth skill, an
exchange in rounds, `jack` as a netrunner's route through their chrome,
and every encounter still offering the ways out that are not a fight.
`test_the_fight`.

### 2026-09-03 (y): the rough street

D129. A fighter's play-test found the overworld safe by construction
(danger keyed only on faction heat). Districts dangerous on their own
account now, by tier and by hour. `test_the_rough_street`.

### 2026-09-03 (z): more of the shelf

D130. Three more weapons carried and one fitted, riders (spread, stun,
reach, smartlink), and the existing techniques wired into the exchange.
`test_the_fight`.

### 2026-09-04 (a): a fighter's living

D131. Styles (stagger, edge, concealed), twelve weapons in four styles,
armour worn and fitted, six pieces of chrome that fight, loot, muscle work
and fights that teach, and a balance simulation across eight builds.
`test_a_fighters_living`.

### 2026-09-04 (b): the help, current

D132. Nine of forty-four manual topics brought up to the combat layer, and
a clean-up. `test_help_is_current`.

### 2026-09-04 (c): the match

D133. The rest of the game meets the fight: street conditions, Redline
and Numb, traits for a fighter at creation, the clinic patching a cut.
`test_the_match`.

### 2026-09-04 (d): the pit

D134. Carrion's, a loading bay in the Shambles with five named regulars
and a wall of names, and a fixer's street jobs. `test_the_pit`.

### 2026-09-04 (e): the deck, in the city

D135. Mail composed from the world, search that finds real stock, a watch
that saves a shift, a message that moves a disposition, ads that read your
state. `test_the_deck_in_the_city`.

### 2026-09-04 (f): a real deck

D136. The deck out here is the deck in there: condition, reach by
antenna, `sweep`, `route`, `tune`, `repair`. `test_a_real_deck`.

### 2026-09-04 (g): what the play-test found

D137. Three play-tests of everything since D128 (a brawler, a netrunner
who never throws a punch, a first-timer on `now`). No crashes; nine
fixes, the first of them the physical half being invisible to a newcomer.
`test_the_play_test_found`.

### 2026-09-04 (h): the deck under pressure

D138. Three play-tests aimed at the deck (bad input and broken hardware,
sixty shifts, everything the mail can carry). Seven fixes; mail is news
now, not a status board. `test_the_deck_under_pressure`.

### 2026-09-04 (i): the fight under pressure

D139. Every move under bad input, and three sixty-shift campaigns on the
fighting routes with the take per shift measured. Three fixes, the first
being a wall with one thing on it you could not beat.
`test_the_fight_under_pressure`.

### 2026-09-04 (j): the story knows the street

D140. A story pressure test (no stranded stages), and the real gap it
found: no thread read anything the fight, the pit, the deck or the chem
sets. New condition kinds, three people, three threads.
`test_the_story_knows_the_street`.

### 2026-09-04 (k): a thread for every way of working

D141. Six gates with nothing behind them and four near-storyless factions.
Five threads on existing people close them, and the test enforces the
coverage from here on. `test_a_thread_for_every_way_of_working`.

### 2026-09-04 (l): the record

D142. `record`: twenty-four lines across the work, the city, the people
and the floor, each counting something the engine writes, a crossing
earning a name shown on `char`. Five counters made real to hold it.
`test_the_record`.

### 2026-09-04 (m): after the water

D143. The main line pays: the Deepwater palette behind finishing it, the
city settling the water once and differently per ending, and *Afterwards*
handing the city back. `test_after_the_water`.

### 2026-09-04 (n): bookkeeping

No code. This document brought current: the START HERE block carried from
D132 to D143, this log backfilled from D111, and the escaped apostrophes
that a shell heredoc left in the D133 to D143 entries cleaned.

### 2026-09-04 (o): what the players said, again

D144. Three play-tests on the record, the ending three ways, and a fighter
who ends on the main line: five campaigns, no crashes, every ending reached
by play. Seven fixes, the largest being the posting that outlived its own
ending and an afterwards that opened in the same breath.
`test_what_the_players_said`.

### 2026-09-04 (p): the harness, kept

The D144 play-test harness moved from the ephemeral job directory into
`tools/playtest/` (harness, spine driver, three personas, the round's
report, a README). It sets `XDG_DATA_HOME` before importing the game, and
its data and logs directories are ignored by git.

### 2026-09-04 (q): the counts, current

Every number the README and START HERE state, read off the code and
corrected where it had drifted (the README was ten numbers behind: 70
programs, 14 drugs, 33 traits, 14 icons, 46 topics, 204 events, 25 one of
a kind, 91 pieces of terminal across 9 axes, 151 verbs). The build checked:
`./build.sh` produces `dist/flatline.pyz`.

### 2026-09-04 (r): the third round

D145. Six personas on the three corners nobody had played: the under ending,
retirement, and a bond. No crashes. Three fixes (a loadout dead-end on a
duplicate program, a partner bond that could not form, `market chrome`) and
two confirmations (the under ending is complete; retirement is sound).
`test_the_third_round`.

### 2026-09-04 (s): the signposts, and the counts

D146. Four additions from the third round: a Deepwater run costs a point of
drift (a non-chrome path to the record's line); the posting's brief names the
inside route that a network with no perimeter wants; the fence and the
demonstrator introduce themselves through street work and the blooded mark;
and `validate.catalogue()` + `check_readme` + `tools/counts.py` hold the
README's counts to the modules. `test_the_signposts_and_the_counts`.

### 2026-09-04 (t): the walking, answered

D147. A playstyle-coverage and tone audit found the tone clean and one
playstyle with no story at all: the explorer, with zero threads reading the
walking, against face 8 / fighter 5 / street 4 / drift 3. New engine rules
`places:<n>` and `finds:<n>`, two explorer threads (*The Edges* on places
stood in, *Kept Back* on things found), and the coverage test extended to
enforce them. `test_the_walking_answered`.

### 2026-09-04 (u): the hunt, the specialist, the unit

D148, D149, D150. The explorer's finds made a visible hunt: the rumour leads
on the non-met rules, standing where a thing is senses it, and `rumours` is
the board (found / heard-not-found with where and when / unheard count). Two
deck-specialist threads, *The Sealed Thing* (cryptography, Osei) and *The
Names on the Big Dish* (signal, Pip). And the achiever's *The Unit*, gated on
a new `record:<n>` rule (lines of the record earned), about your name
becoming the city's unit of measurement. `test_the_hunt_made_visible`,
`test_the_specialist_and_the_reckoner`.

### 2026-09-04 (v): the names, and choosing which to wear

D151. Title selection: `called` lists earned titles grouped by source, pins
one (profile-kept, survives the character), `called auto` for newest;
title_of honours the pin. Twelve extra titles earned by deeds in three
registers (heroic/vile/amusing), each reading a real flag; `betray` now sets
a flag so a title can read it. `test_the_names_the_city_gives`.

### 2026-09-04 (w): the one thing that is not for the work

D152. Real-world pets: six animals kept at the safehouse, food/water/play
that decay by the animal's rate, `pet` command (get/feed/water/play/name/let
go), feed bought in bags, telegraphed neglect and loss (vital needs lose it,
play only saddens), part of the save and the ending. `validate` holds that
no run or fight reads a pet. `test_the_one_that_is_not_for_the_work`. Digital
pets (deck-side, in-run phrases) are D153.

### 2026-09-04 (x): the other kind of pet

D153. Digital pets: five familiars (pixel cat, chatter-bird, good boy, the
tally, wormwood) that ride the deck (cost memory, on deck.familiar), follow
you into runs and speak at connect/amber/red/lockdown/black-ICE/clean/burned
via RunState.familiar_say, cosmetic (validate reads the method body to hold
it), go dormant unrun without dying, in the save. `familiar` command.
`test_the_other_kind_of_pet`.

### 2026-09-04 (y): a familiar needs feeding too

D154. Digital-pet care: familiars carry a charge fed by runs and drained by
idle shifts at a per-familiar rate, a low-charge line each, `familiar tend`
between runs, dormant at zero without loss. Closes the pets-spec gap the
honest-play round flagged.

### 2026-09-04 (z): more of the deck specialist

D155. Fixed a shipped thread that could not open (sealed gated on met:osei,
key is bartender) and added a validate guard for thread met: keys. Two new
deck-specialist threads: stack (architecture, the tailor, the Vertical's
hidden floors) and unmade (sabotage, the orderly, unmaking the Green's
records). Coverage test enforces architecture/sabotage/crypto/signal threads.

### 2026-09-04 (aa): home, the other side of the deck

D156. A `home` command (aliases keep, life) summarising the meat-side life
in one read-only screen: safehouse, pet and its need, familiar and its
charge, arrangements, debt, crew. Linked from the safehouse manual topic.
`test_home_is_what_you_keep`.

### 2026-09-04 (bb): what the honest players found

D157. The sweep repeated with honest personas: the posting carries no
black ICE (`generate(lethal=)`), a crewed or hired runner does not race
you for the board, the reckoner opens on ten record lines, the partner
bond gains eight and three a job and lands by shift twenty-seven, and
`now` never advises `drop` on a story posting (inside job or the walk
into them instead). Harness: `drive_run` follows the brief, `do_step`
takes heat refusals. Every persona clean, the under chain and the bond
both reached by play. `test.py` green at 19,309.

### 2026-09-04 (cc): five whole lives

D158. Five full-career personas over `campaign.py` (netrunner, fighter,
face, explorer, drift), 86 to 96 commands each, zero crashes. Eight
findings, all in `now`: the bare `deck` step (two branches), the loadout
plan crowding out the job's payload, the familiar's memory invisible to
the plan, an upgrade advised as a step, plan programs swapped for ever, a
collection answered with a screen (and the crash in the first fix), and
two small ones (`called` by key, one full stop). Four endings reached by
play, a partner bond by play, save and restore intact with both pets.
`test.py` green at 19,324.

### 2026-09-05 (dd): the five suggestions

D159. `give` on the first question of the bad rungs when the money is
there; Bare for None, a runner named as one, the deadline a warning,
`uninstall` says fitted; *The Freight Line*, a quiet door for a hunted
runner with nothing, on a new `bounty:` rule, ending the character as
"left quietly"; `test_the_follower_never_stalls`, which found `buy
lattice` ambiguous in Marrow (exact names win now); `q6_runcraft.py`,
every technique and every origin verb, 110 commands, all refusals honest.
Six campaigns leave only `begin` and `quit` untyped. `test.py` green at
19,356.

### 2026-09-05 (ee): what you keep

D160. The fuzz over every origin; each origin's verb played by state;
`requisition` names the form. Toys for every animal (`pet toy`), three
record lines (an animal kept, runs with a familiar, names given), two
freight-line titles. The six-campaign regression caught the quiet door
opening at three runs with the ending first; it opens on a career now,
staying first, and the harness never takes an ending by default.
`test.py` green at 19,413.

### 2026-09-05 (ff): the number came off

D161. The freight line's third scene (stayed, then the bounty turned),
and the `stayed` title reads it instead of the refusal. Four message
replies a band instead of two; the toy shows on `pet` and `home`.
`test.py` green at 19,417.

### 2026-09-05 (gg): the paper

D162. `validate` holds that an ending is never a stage's first answer
(and found the under ending shaped that way; reordered). The `named`
record line counts the record's own names. *The Paper*: somebody took
the paper on your name, three answers, on the `bounty:` rule.
`run_all.sh` runs the six campaigns and prints what matters. Fifty-three
threads. `test.py` green at 19,499.

### 2026-09-05 (hh): coming back

D163. `restore` recaps the job, the debt, the animal, the familiar, the
crew; `now` names the record line you are closest to crossing; `familiar`
counts its runs. `test.py` green at 19,506.

### 2026-09-05 (ii): the collector has a name

D164. The paper's collector is the runner who thinks least of you, on
`who` until settled; `now` names the title with the line; `--long`
follower; familiar `done` and `home` beats; `visit` marks where you have
stood; `people` says what is left to ask. Six campaigns clean.
`test.py` green at 19,514.

### 2026-09-05 (jj): what the long follower found

D165. The wrecked-deck advice runs the street's heat check and names a
workshop you can reach, or the priced walk; escort waiting is not a
stall; `who` lists you against the field. `test.py` green at 19,519, `--long` green.

### 2026-09-05 (kk): the five corners

D166. Told where to look (a `told:` flag past the career gate); the
partner reads who you crewed and the nemesis poaches the crew for a
night; the pit's usurper; the record's this-life column; the long
persona. `test.py` green at 19,528.

### 2026-09-05 (ll): what the long life found

D167. The breaker-buy advice reads the room the plan leaves (the first
long life spent four thousand on breakers that never fit and died broke
at eighty-one); the second long life reaches shift two hundred alive,
forty runs, the ending at seventy-five, the late game still deciding.
`test.py` green at 19,531.

### 2026-09-05 (mm): the door comes down

D168. The stake is fifteen thousand; a warm runner asks you in on a job
(`asked_in`, once in twelve shifts); `now` watches the payload nobody
sells here; the poach and the grudge are scenes. Seven campaigns alive,
0 crashes. `test.py` green at 19,537.

### 2026-09-05 (nn): the long wash

D169. *The Long Wash* (a bounty worked off through Mara, `wash_washed`
clears the numbers and halves the heat); the first ask-in a scene by
style; `now` watches for a mask and a bank; the reckoner on eight and
twelve; `test_every_thread_opens_for_the_right_life` holds all
fifty-four openers. `test.py` green at 19,614.

### 2026-09-05 (oo): what a release wants

D170. The 3.11 floor held by `validate`; the pyz run through a pty at
three widths, clean, with a one-line notice under eighty columns; every
closing stage held open by test; the door as a distance on `home`;
personas take the watches `now` offers. `test.py` green at 19,706.

### 2026-09-05 (pp): the ninth log, and the systems have stories

D171, D172. The second arc: the ninth log belongs to a runner the city
chooses, the prose carries `{runner}`, what you did with yours decides
theirs, the table's three answers land on them. The first arc read back
through the familiar, the partner, the animal, the construct, and four
NPC topics. Then `pet:`, `familiar:` and `titles:` rules and four
subplots for the animal, the construct, the names and the door. All five
reached by play. `test.py` green at 19,838.

### 2026-09-05 (qq): the retrofit goes both ways

D173. Three old threads close on lines that read the partner and the
name; capitalised tokens and `{called}`; the ninth log's crew branch;
Remnant on the construct; the toy's scene; the wash's middle.
`test.py` green at 19,875.

### 2026-09-05 (rr): a partner as a clause

D174. `{Partner_or}` carries its own clause so the closings read either
way; the long life's ledger read (seven tenths of its earnings to the
street, by its own choice). `test.py` green at 19,875.

### 2026-09-05 (ss): the four engineering items

D175. The collector named inside the paper's scene; the record marks the
profile's own line; `q8_origins.py` plays the origin threads by play
(11 of twelve end to end); the street already showed its odds.
`test.py` green at 19,877.

### 2026-09-05 (tt): the ninth log finishes clean, and the city at leisure

D176, D177. A runner handed over is gone, not dead; together makes a
partner; four closings, one per branch; the afterwards knows about the
tenth log. Then four long threads for after the main arcs: the Water
Towers, the Valuation, the Second Edition, the Crane's Name, all reached
by play. `test.py` green at 20,071.

### 2026-09-05 (uu): the small things

D178. Second scenes for the animal (ill, after forty shifts) and the
construct (your name, after twenty runs); the ninth marked on the
runners list; the origins persona stronger for a posting that beat it.
`test.py` green at 20,109.

### 2026-09-05 (vv): networks with memory

D179. `world/memory.py`: doors stay cracked until patched (news, and a
`watch` on the faction); a trail teaches them your techniques and one
seen twice reads on every door; routes persist and a planted way ages
into a trap half the time; `render` says what they know. Six campaigns
and the long life clean with it in. `test.py` green at 20,120.

### 2026-09-05 (ww): 1.0

Tagged `v1.0` on the build with the networks' memory in it, and the
repository made public for testers. The README says what it needs to:
Python 3.11 or newer, eighty columns, the pyz from the release or a
clone, three evenings worth trying, and what a useful report contains
(the world seed is on `char` now). `test.py` green at 20,120.

### 2026-09-05 (xx): testing on, every fix pushed

The author's brief: keep testing, push every fix. The six campaigns, the
long life and the origins persona are clean on 1.0. Two fixes pushed on
their own: the story types in their own module, because whichever of
`arcs` and `threads` was imported first failed on the cycle; and D180,
from a ninth persona (`q9_memory`, the regular) that worked one faction
and found the board would not let it. `test.py` green at 20,120 before
D180.
Then, still pushing each on its own: the networks' memory paragraph found
in the topic's summary slot where `help networks` never printed it, and
five more sentences from this week in the same place (rivals, threads,
street, record, relics), all moved into their bodies with a guard in
`validate`; and D181, the shutdown, because the author asked for an exit
worth watching. Release `v1.0.1` carries all of it.

### 2026-09-06 (a): the testers' first hour

D182. The first strangers' notes on 1.0.1, sorted into what was true and
answered on the build: the legend, the grid, the glossed sheet, the
rendered prompt, the tutorial that turns itself on and stays under `now`,
the words in place of the pictures, and tables allowed a hundred and
twenty columns while prose stays at seventy-six. The README's screenshots
regenerated on the new default. `test.py` green at 20,356.
