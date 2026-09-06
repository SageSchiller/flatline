# Five full campaigns, 2026-09-04 (after D157)

Five personas, one per way of playing, each a whole career composed from
`campaign.py`: the netrunner, the fighter, the face, the explorer, the drift.
Every one of them types the real commands for every system it touches (86
to 96 of the 156 the game registers), and the run was repeated until the
transcripts were clean. Zero crashes in any round. What the rounds found,
largest first, and what was done.

## Found in the game

1. **`now` said `deck`, a screen, for a payload that did not fit.** Two
   branches of the loadout advice returned a bare `deck` step; a player who
   does what `now` says typed it 420 times. Both name a move now (the spare
   program, then the bigger bank), and the test holds that no branch of the
   advice returns a bare `deck` step.
2. **The loadout plan crowded out the job's own program.** It took the best
   breaker first (a Lattice, three of a four-memory deck), so the Siphon the
   exfiltrate needed had no room, the plan had no payload in it, and the
   advice unloaded the Siphon for the Lattice, 390 times. The plan reserves
   the job's category first and picks the best of each kind *that fits*.
3. **The familiar's memory was invisible to the advice.** A Wormwood on two
   of four left a Siphon no room and `now` said a bigger bank 419 times to
   somebody who owned the answer. The plan is built around the familiar's
   memory; when the job's own program fits the bank and not the bank less the
   familiar, the step is `familiar drop`, said as the player's choice.
4. **An upgrade was a step.** A better breaker owned but not fitting was
   advised over the adequate loaded one. With something of the kind loaded
   and the better one not fitting, `now` has nothing to say about it.
5. **The advice swapped two plan programs for ever** (Siphon for Blink,
   Siphon for Pike) when the plan did not fit. The branch that unloaded a
   plan program for another is gone; with a plan that fits by construction,
   spare programs are all it ever unloads.
6. **A collection you could not meet said `debt`, a screen,** 418 times. It
   names the fence (a spare program to sell), or finishing the errand held,
   before the screen. The first version of that fix crashed `now` on an
   unbound name; the netrunner campaign caught it, and a test now runs the
   branch.
7. **`called` took a title's phrase, not its key.** `called bloodprice`
   works now, as well as `called who paid the blood price`.
8. **The job screen ended its progress line with two full stops.** One now.

## Measured and left alone

- Three of five personas were killed in the street in one round: every death
  was a bounty street entered `--anyway`, then `cover` chosen over `give`.
  The game warned each time. The harness now prefers `give`; the deaths were
  the harness being reckless, not the street being unfair.
- An explorer with a bounty and 55c cannot retire: a new name costs 1,800c.
  Consistent; the door says so.
- `chart` and `listen` want rank 2, `playbook` is ex-enforcement only, `odds`
  wants a service: all honest answers.
- The rice gallery's last style is called "None". Deliberate ("by then you
  know what it says"), reads oddly in a list.
- `deal` is for people you have met, not runners; `deal <runner>` says nobody
  called that.

## Where the five ended

- netrunner: employed ending, afterwards lived; 17 runs; 95 commands typed.
- fighter: refused ending, afterwards lived; `unbought`; 88 commands.
- face: employed ending, a partner bond by play (+63); 90 commands.
- explorer: 6 of 15 finds, 26 threads, save/restore intact with both pets;
  door closed by a bounty it could not afford to burn; 93 commands.
- drift: refused ending, chrome to the first band and back, a habit and a
  detox, the scary familiar; `unbought`; 93 commands.

## Never typed by any of them

The run techniques beyond the brief (`backdoor`, `backway`, `collapse`,
`crash`, `daemon`, `ghost`, `hotswap`, `mask`, `misdirect`, `overclock`,
`overload`, `pivot`, `plant`, `scrub`, `sidechannel`, `steady`, and the
rest of the defence verbs), `betray`, `vouch`, `requisition`, `uninstall`,
`script`, `bind`, `switch`, `new`, `delete`, `reset`, `quit`. A run-craft
persona that plays every technique is the next campaign worth writing.

## Round two, 2026-09-05 (D159): the five suggestions, and the sixth persona

- `q6_runcraft.py`: rank four in everything, every technique in six batches
  over twelve runs, then `betray`, `uninstall`, `script`, `bind`, `new`,
  `switch`, `delete`, then one character per origin for the origin verb.
  110 commands, 0 crashes. Every refusal honest: origin-gated verbs name
  the origin that has them, context refusals say what is missing ("nothing
  here is sealed", "you are running this one alone", "no daemon program
  loaded"), once-a-run verbs say so. One wording: `uninstall` said
  "available" for the fitted list; it says fitted now.
- The follower fuzz (`test_the_follower_never_stalls`) found `buy lattice`
  ambiguous in Marrow on its first run (the optic lattice): exact names win.
- Across all six campaigns the only commands never typed are `begin` and
  `quit`.

## Round three, 2026-09-05 (D160): the regression that caught the door

All six campaigns rerun on the D159/D160 build. First pass: five of six
ended "left quietly" at shifts 8 to 72, because *The Freight Line* opened
on a bounty at three runs and its first answer was the ending, and a
default chooser takes the first answer. Fixed in the content (six runs,
twenty shifts, staying first) and in the harness (never an ending the brief
did not name). Second pass: six clean, 0 crashes, refused/employed/refused
by play, a partner bond by play, five offered the berth and staying (the
`stayed` title), coverage 84 to 111.

## Round four, 2026-09-05 (D166, D167): the long life

`q7_long.py`, two hundred shifts. First life: dead in the street at 81,
broke and hunted; the money went on two breakers `now` advised that never
fit beside the payload (fixed: the advice reads the plan's room), street
pay-offs, and an arrangement the harness bought. Second life: shift 201,
40 runs, employed ending at 75, 34 of 53 threads, 3 finds, record 14 of
28, `now` still naming real moves at the end, 0 crashes, coverage 96.
The freight line was offered and refused by brief; the door stayed shut
on the stake (45,000c), which a courier who never keeps more than 8,000c
was never going to have.

## Round five, 2026-09-05 (D168): what the harness had to learn

Three deaths in a row across the runs of this round were the harness, not
the street: it paid every pay-off until broke, gambled when poor, and
walked `--anyway` into a street with a number on its name while hurt. It
keeps a reserve, does not gamble under 2,000c, and declines the hostile
walk when broke or hurt now. With that: seven campaigns alive, 0 crashes,
three endings and a partner bond by play, the long life to shift 211 (it
declined 3,978 hostile walks and ran less for it, which is the honest
cost of caution). The ask-in fired in four campaigns.

## Round six, 2026-09-05 (D169): the audit

Union of every campaign's save: 41 of 54 threads reached by play. Never
reached: seven origin threads (the campaigns use five origins), three
specialist-rank threads, the demonstration (a fight flag), the reckoner
(the record). All twelve open for the life they ask for, held by
`test_every_thread_opens_for_the_right_life`. The reckoner's gate moved to
eight lines because the long life's own record was eight after two
hundred shifts. Seven campaigns alive; the long life to shift 201, 36 runs,
employed at 92, four names.

## Round seven, 2026-09-05 (D171, D172): the second arc and the four subplots

Six campaigns and the long life on the build with *The Ninth Log* and the
four system subplots. 0 crashes. All five new threads reached by play on the
first run; the fighter took the ninth log to the table and earned "who wrote
the tenth log". The long life: shift 184, 66 runs, 42 of 59 threads.

## Round eight, 2026-09-05 (D175): one life per origin

`q8_origins.py`: twelve characters, twenty shifts each, each following its
origin's thread by play (meeting who it asks for, running what it asks for,
taking the thread's own posting). 11 of twelve end to end, 0 crashes.

## Round nine, 2026-09-05 (D176, D177): the arc closed, the city at leisure

Six campaigns and the long life on the build with the ninth log's four
closings and the four long threads. 0 crashes. All four long threads reached
by play on the first run (the Terraces, the Row, the Stacks, Freeport); the
ninth log closed on "Ten, with two handles" by play. The long life: shift
182, 55 runs, 45 of 63 threads.
