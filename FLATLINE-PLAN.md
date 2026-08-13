---
tags:
  - flatline
  - project-plan
  - game
created: 2026-08-12
updated: 2026-08-12
---

# flatline: Build Plan and Progress Log

> Resumable build plan for **flatline**, a text-based cyberpunk intrusion game. **Read this file first** when picking the project back up. Every locked decision and every completed step is recorded here so work can pause and resume without re-deriving context.

> [!tip] Picking this back up: START HERE
> **State as of 2026-08-12.** **The game is playable end to end.** Phases 0, 1, 2 and most of 3 are done. `python3 validate.py` is clean with zero warnings, `python3 test.py` is green at **4615 checks**, and `./build.sh` produces a `dist/flatline.pyz` that runs standalone with nothing installed. About 11,600 lines.
>
> You can create a character six ways, spend an attribute and experience budget, take a contract, travel, do legwork, jack in, break into a procedurally generated network, steal something, and get out, and the residue you left turns into faction heat a shift later.
>
> **What is not done yet:** rivals acting on their own, bounties making districts dangerous, and the `escort` and `surveil` objectives are stubs that resolve as "did you take anything". Those are Phase 4. See the phase list.
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
cd "$HOME/Documents/Main/flatline"
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
| **Guile** | Social engineering, forging credentials, passing as someone with a badge | Every door needs to be broken because none of them will open for you |
| **Grit** | Stamina across a long run, recovery, absorbing damage to deck and body | You are fine right up until you are not, and then the run is over |

**Derived:**

- **Bandwidth** = 8 + Grit. The capacity budget cyberware spends.
- **Integrity** = 10 + (2 x Grit). Damage you can take before the run ends badly.
- **Focus** = 3 + floor(Logic / 2). A per-run resource spent on precision actions: retries, forced successes, careful work that reduces residue.
- **Tempo** = 1 + floor(Reflex / 4). Actions per tick during real-time ICE engagement.

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

`validate.py` clean, `test.py` green at **4987 checks**.
