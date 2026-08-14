# flatline

A text-based cyberpunk netrunning game, played by typing at a fake terminal.

You take contracts from people who want a corporate network interfered with,
break into it while a trace runs against you, and leave before it finishes.
Then the part most games in this genre skip: **the city remembers**. The
evidence you left becomes that faction's attention on you a shift later, their
networks harden every time you succeed against them, and the other runners in
this city are taking the work you did not.

Python, standard library only. No dependencies, no install, no network access
at runtime.

## Running it

```bash
python3 -m flatline              # play
python3 -m flatline --seed 8829  # a specific world; seeds reproduce exactly
python3 -m flatline --theme ansi # inherit your terminal's own colours
python3 -m flatline --ascii      # no Unicode
```

At the prompt, `tutorial` walks you through a first run one instruction at a
time, and `help` explains both the verbs and the systems behind them.

Saves live in `$XDG_DATA_HOME/flatline` (usually `~/.local/share/flatline`),
not beside the code.

## Building a single file

```bash
./build.sh          # produces dist/flatline.pyz
python3 dist/flatline.pyz
```

`zipapp` ships with Python, so the result runs anywhere Python does, with
nothing installed.

## Working on it

```bash
python3 validate.py   # what the content says
python3 test.py       # what the game does
```

Run both after any change. They are split on purpose: most of what goes wrong
in a content-heavy game is a dangling reference or a rule quietly broken in one
entry out of two hundred, and that is cheap to catch in `validate.py` and
expensive to catch by playing.

`validate.py` is unusually opinionated. As well as checking that every
reference resolves, it enforces design rules: every implant must have an honest
mechanical drawback, every attribute must govern at least two skills, a
collection on a debt must outpace its interest, and any content declaring an
ability the engine never reads is a build failure. **That last one is the
recurring bug class in this project**: a passive, an ICE rider or a technique
flag that validates, ships, and does nothing.

## The design

`FLATLINE-PLAN.md` is the long version: thirty-two numbered locked decisions,
the systems design, and a session log. **Read it first** before changing
anything structural.

The three ideas everything else hangs off:

- **Noise, trace and residue are three different quantities and are never
  conflated.** Noise is local and decays, trace is the run clock and never
  does, and residue outlives the run entirely. Cleaning up costs time and time
  feeds the trace, so getting out clean and getting out at all pull against
  each other.
- **Failure is a state change, not a game over.** Only black ICE ends a
  character, it only guards cores, and it always telegraphs first.
- **No hidden dice.** `odds` prints the entire sum and the exact percentage
  before you commit, and a failed check names the term that sank it.

## What is in it

12 skills with 24 techniques · 26 traits · 10 origins, each with a signature
verb nobody else can use · 34 implants · 46 programs · 28 countermeasures ·
9 districts · 12 factions · 17 named characters · 18 storylines across 39
scenes · 26 manual topics · 95 commands.
