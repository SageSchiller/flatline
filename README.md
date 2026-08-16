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
python3 -m flatline --no-intro   # skip the cold start
```

It boots. If you are on a colour terminal you get the animated version, and
`title` replays it; everywhere else you get the last frame and the game is
identical. Ctrl-C during it means "get on with it", not "quit".

At the prompt, `tutorial` walks you through a first run one instruction at a
time. `help` is one screen: what to read first, the verbs that answer "what
now", and where the rest lives. `help commands` is all 106 verbs, `help
topics` is all 35 explanations, and `help <anything>` finds a verb, a system,
or searches both, including every proper noun in the game.

Two verbs are worth knowing before anything else. **`job`** says what you are
trying to do, where it is, how far along you are, and the next command to
type, in the city and inside a run alike. **`map`** draws the shape of
wherever you are: the nine districts and the walk to each of them, or every
host you have found and what connects to what. Neither costs any time and
both are always safe to ask.

Saves live in `$XDG_DATA_HOME/flatline` (usually `~/.local/share/flatline`),
not beside the code, so moving or reinstalling the game does not touch a
character. That location is correct and is also the one place nobody thinks to
back up, so:

```
save --export ~/backups/keeper.json      # a copy anywhere you like
restore --import ~/backups/keeper.json   # bring it back, here or elsewhere
```

An export is an ordinary save, migrations included: a copy made today still
opens after the format moves on.

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
collection on a debt must outpace its interest, no point inside an attribute's
range may be a point you can buy that does nothing, and any content declaring
an ability the engine never reads is a build failure. **That last one is the
recurring bug class in this project**: a passive, an ICE rider or a technique
flag that validates, ships, and does nothing. Its worst form is a rate that is
declared as a float and applied to a value stored as an int, which is not a
slow effect but no effect, and looks identical to a slow one from outside.

## The design

`FLATLINE-PLAN.md` is the long version: forty-nine numbered locked decisions,
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
- **Being memorable cuts both ways.** What you look like is a build decision
  with 102 options behind it. A face worth describing earns more standing per
  job and turns more of the evidence you left into somebody's heat, and chrome
  puts a floor under it that no haircut gets below.
- **The city is grim on a budget.** Most of what happens around you is
  somebody having a worse day than you in a way nobody records. About one
  event in six comes up for air, because unrelenting bleakness stops landing
  after an hour. The ratio is enforced by `validate.py`, not hoped for.
- **The shell is yours and the city does not get it.** Six axes of terminal
  customisation, sixty-seven pieces, most of them earned by playing. It is
  stored outside the save, so it survives a flatline: you lose everything
  else, and the terminal you spent a week getting right is still there when
  you sit down with somebody new. None of it touches a single number.
- **Everything good is a loan.** Residue becomes heat a shift after you
  thought you got away with it, and the three vices are the same shape said
  three ways: borrow money and it compounds, take something and the comedown
  outlasts and outcosts the high, sit down at a table and the edge is painted
  on the wall before you play. What you are ever buying is when the bill
  arrives, and the trap is never any one of them, it is taking the second to
  pay for the first.
- **There is a door, and something goes through it.** `retire` wants nothing
  owed, nothing in you that you need, nobody paying for your name, and enough
  put away: four things the city spends the whole campaign making harder.
  Whichever way you go out, retired or flatlined, you leave exactly one thing
  to whoever you make next, and afterwards the city mentions your name to
  somebody who never met you.
- **The street and the net want opposite hours.** At peak the walkways are
  full, which is bad for you out there and good for you in here, because all
  those people are generating the traffic you hide in. At night nobody is
  looking at you on the street and your session is the only session in the
  network. There is no correct shift to work, and waiting for the right one
  costs the only thing this city actually charges in.

## What is in it

12 skills with 24 techniques · 26 traits · 10 origins, each with a signature
verb nobody else can use and its own starting face · 34 implants · 46 programs
· 28 countermeasures · 9 pieces of bench work · 9 districts, each with a mark for the faction that
holds it · 12 factions · 7 rival runners who decide about you, and one you can keep · 17 named characters who hand out work, keep private stock and do favours on a tab · 18 storylines across 39 scenes ·
102 appearance features · 51 ambient city events · 38 manual topics ·
10 drugs · 3 lenders · 2 games of chance in 5 rooms ·
112 commands · 67 unlockable pieces of terminal across 6 axes.

Footnotes are a real feature of the console. `{{like this}}` in any content
string gets lifted out and printed under the block, and they nest, because the
whole reason to have a footnote is the writer who gets halfway through an aside
and needs an aside about the aside.
