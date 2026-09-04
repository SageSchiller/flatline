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
