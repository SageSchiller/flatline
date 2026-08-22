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

If you have never played a game by typing at it, three things carry you.
**Enter on an empty line** always says what to do next: the one real move,
the reason, and the handful of verbs that matter where you are standing
(`now` is the same thing typed). **`new`** asks three questions, one line
each: which origin, what to call them, and whether to put the opening points
where that origin usually does; `new <handle> --origin <key>` is the same in
one line when you have picked. And **row numbers are names**: wherever the
game shows you a list, `take 2`, `buy 3`, `travel 1` and `switch 2` mean the
row you just read. A typo gets "did you mean", and arriving anywhere ends
with a line of the verbs that district makes possible.

At the prompt, `tutorial` walks you through a first run one instruction at a
time. `help` is one screen: what to read first, the verbs that answer "what
now", and where the rest lives. `help commands` is all 120 verbs, `help
topics` is all 39 explanations, and `help <anything>` finds a verb, a system,
or searches both, including every proper noun in the game.

Two verbs are worth knowing before anything else. **`job`** says what you are
trying to do, where it is, how far along you are, and the next command to
type, in the city and inside a run alike. **`map`** draws wherever you are:
the city, with you and the job marked on it and the walk to anywhere, or
every host you have found and what connects to what. Neither costs any time
and both are always safe to ask. `walk <district>` goes the whole way, a
shift a step, and stops if the street stops you.

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

`FLATLINE-PLAN.md` is the long version: fifty-three numbered locked decisions,
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
  before you commit, for a crack or a strike, and `odds <any verb>` prints
  what that verb costs tonight; a failed check names the term that sank it. The
  same goes for the weather: about one run in two has a condition tonight,
  announced at the door with its numbers, and one that touches a check is a
  named term in the sum.
- **Being memorable cuts both ways.** What you look like is a build decision
  with 102 options behind it. A face worth describing earns more standing per
  job and turns more of the evidence you left into somebody's heat, and chrome
  puts a floor under it that no haircut gets below.
- **The city is grim on a budget.** Most of what happens around you is
  somebody having a worse day than you in a way nobody records. About one
  event in six comes up for air, because unrelenting bleakness stops landing
  after an hour. The ratio is enforced by `validate.py`, not hoped for.
- **The shell is yours and the city does not get it.** Seven axes of terminal
  customisation, seventy-one pieces, most of them earned by playing. It is
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
- **A decision is read.** Every choice in every storyline sets a flag, and
  every flag is read by something other than the ending: somebody stops
  being in the city, a counter closes, a favour opens, the streets of one
  faction get safer, a patron stops posting, an ambient event arrives a few
  shifts later happening to somebody else. And every one has a line in the
  ending, whichever ending it is. `validate.py` fails the build on a
  decision nothing reads, because a choice that changes nothing is prose
  with a flag on it.
- **The street and the net want opposite hours.** At peak the walkways are
  full, which is bad for you out there and good for you in here, because all
  those people are generating the traffic you hide in. At night nobody is
  looking at you on the street and your session is the only session in the
  network. There is no correct shift to work, and waiting for the right one
  costs the only thing this city actually charges in.

## What is in it

14 skills with 28 techniques, two of them for the street · 29 traits · 10 origins, each with a signature
verb nobody else can use and its own starting face · 38 implants · 60 programs
· 34 deck components · 24 of all of those one of a kind, never sold, found at a place at an hour or handed over by a decision, each with a history · 28 countermeasures · 9 pieces of bench work · 12 districts, each with a mark for the faction that
holds it · 12 factions · 7 rival runners who decide about you, and one you can keep · 29 named characters who keep hours, hand out work, keep private stock and do favours on a tab · 32 storylines across 95 scenes and 110 decisions, every one of them read back by the world, with a spine through the middle that has four endings and one of them is a door ·
102 appearance features · 12 districts, drawn, with a scene for every hour and 60 places in them to go and stand · 189 ambient city events, 80 of them consequences of something you decided and 12 of them rumours that stop when the thing is found · 41 manual topics · networks in six shapes · the street in four tiers and 20 ways it stops you, six of them written for one street only ·
12 drugs · 3 lenders · 2 games of chance in 5 rooms ·
122 commands · 72 pieces of terminal across 7 axes.

Every number on every one of those is read by the engine, and `validate.py`
holds it to that: every modifier key and every rider string in the content
has to appear in the code that is not content, or the build fails. `inspect`
anything before you pay for it.

The street is real. Walk into a district where your name is worth money and
some of them are waiting: a price on a kerb, a photograph in a doorway, a
van, and, at the top of the ladder, people who have stopped asking. You run,
talk, pay, or stand there, each a printed check on two street skills, and the
street can kill you, after it has warned you in so many words. `errands` is
the work that needs no deck.

Footnotes are a real feature of the console. `{{like this}}` in any content
string gets lifted out and printed under the block, and they nest, because the
whole reason to have a footnote is the writer who gets halfway through an aside
and needs an aside about the aside.
