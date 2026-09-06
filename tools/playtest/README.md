# Play-testing flatline

The method behind D86, D137 and D144: play it three ways with three briefs, keep
the whole transcript, fix what the players say. Every decision since D75 came out
of somebody playing rather than somebody guessing, and this directory is how the
playing is done when the player is a script.

## The rule

Import `harness` before anything from `flatline`. It sets `XDG_DATA_HOME` to a
directory under `tools/playtest/data/` first, so a persona's saves and profile
counters never reach `~/.local/share/flatline`. The round before this one did not
do that, and its personas wrote a `save-ptest.json` and their counters into the
real profile. Set `PT_DATA` before the import to give each persona its own
directory; the persona scripts here do.

## What is here

- `harness.py`: `Play`, a real `Session` over a captured console. `do(cmd)` types
  one line and logs everything the player would have seen; `settle()` answers
  whatever is pending, preferring the answers the persona would give; `auto_run()`
  does what the run brief says until the job is done or hopeless; `auto_city(k)`
  does the first thing `now` says, k times; `play_job()` is one job the way `now`
  would have you do it; `choose_open()` answers an open story decision.
- `spine.py`: the main line, played. `facts` finds the Archivist and Remnant,
  `to_ending` takes the posting and the offer through to one of the endings,
  `afterwards` lives through what comes after.
- `pa_record.py`: an achiever who reads `record` first and then chases it.
- `pb_ending.py`: the ending, three ways, by three characters.
- `pc_fighter.py`: a fighter who lives on the wall for forty shifts and then
  carries the main line to its end.
- `ROUND-2026-09-04.md`: what those three found, as it was reported. The plan's
  D144 entry is the version of record.

## Running one

```bash
cd tools/playtest
python3 pb_ending.py          # prints one line per campaign; the transcript is in logs/
grep -n "^--- " logs/pb_ending.log   # the marks: where each act started and what the flags were
grep -c "!!! CRASH" logs/*.log       # the first thing to read
```

A persona's log is the deliverable. Read it the way the D137 entry reads its
transcripts: what the player typed, what the game said, and what a person at the
keyboard would have thought at that moment. The findings go in the plan, in order
of size, with what was done about each.

## Writing a new one

Copy the shape of `pc_fighter.py`: a brief in the docstring, `p.mark(...)` at
every turn of the story, `p.do(...)` for what the persona types, `p.settle(...)`
after anything that asks, and `p.finish(...)` at the end. Prefer the automatic
helpers for the parts the brief does not care about, and type the rest by hand,
because the finding is nearly always in the part the persona reads rather than the
part it drives.

## Full campaigns (after D157)

`campaign.py` is a set of acts, each typing the real commands for one part
of a life in the city: `setup`, `deck_life`, `city_deck`, `jobs` (take,
legwork, approach, hire, walk, jack in, the run's reading commands, then the
brief to the end), `people`, `safehouse`, `pets` (both kinds), `money`,
`street`, `chrome_and_chem`, `walk_all`, `record_and_titles`, `save_restore`,
`appearance`, `heat_and_names`, `crew`, `story_end`, `retire_end`. Every act
runs under `act(p, fn, ...)`, which logs a persona-side exception as a
`!!! PERSONA ERROR` and carries on, because the finding is in the game's
transcript, not the script driving it.

The `q*` personas compose those acts, one life each: `q1_netrunner` (the
deck, in and out of the city), `q2_fighter` (the wall, a dog, a crew, the
burn ending), `q3_face` (everybody talked to, the offer taken), `q4_explorer`
(everything walked, the finds, save and restore, the door), `q5_drift`
(chrome, a habit, the scary familiar, the lender). Each prints one summary
line with the commands it typed out of everything the game registers
(`Play.coverage()`), and its log ends with `### never typed:`. Run them in
parallel; they take a few minutes each:

```bash
tools/playtest/run_all.sh     # q1 to q6 in parallel, then the lines that matter
# or by hand:
cd tools/playtest
for f in q1_netrunner q2_fighter q3_face q4_explorer q5_drift; do python3 $f.py & done; wait
grep -c "!!! CRASH\|!!! PERSONA ERROR" logs/q*_*.log
grep -h "^--- " logs/q*_*.log | grep -E "ENDING|jobs:|crew:|after the door"
```

`SWEEP-2026-09-04-campaigns.md` is what the first five rounds of them found.

`q6_runcraft.py` is the sixth: somebody trained to rank four in everything
types every run technique in a network, in context, in six batches spread over
twelve runs, then the city-side commands nobody else typed (`betray`,
`uninstall`, `script`, `bind`, `new`, `switch`, `delete`), and then becomes one
character per origin to type the verb only that origin has. Its refusals are
the deliverable: every one should be an honest answer, never a crash or a loop.

`q7_long.py` is one life for two hundred shifts, to see whether the late game
still decides anything; it takes a few minutes and is not in `run_all.sh`.
`q8_origins.py` plays one short life per origin and carries each origin's own
thread to its end. `SWEEP-2026-09-04-honest-play.md` and
`ROUND-2026-09-04-pets.md` are the notes from the rounds before the campaigns;
the plan's D158 to D179 entries are the version of record for everything the
campaigns found.

Run the suite (`python3 test.py`) on its own, not alongside the campaigns:
together they take longer than a comfortable sitting.
