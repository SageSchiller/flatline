# Play-test: titles, real-world pets, digital familiars (2026-09-04)

Three personas (pl_titles, pm_pet, pn_familiar) through the real dispatcher,
each in its own data dir. No crashes in any of them. All three systems work
and the tone holds. Details below.

## Titles (pl_titles): clean

- `called` with nothing earned reads as an invitation, not a blank.
- Earned five titles across the registers (a working runner / who paid the
  blood price / the one they cross the street from / who sells names / who
  could not be bought / who asked about the war). The board groups them:
  "for the record / for what it admires / for what it will not forgive /
  for what it finds funny", with the current one ticked.
- Default is the newest; pinning with `called <name>` sticks and `char`'s
  called row follows it; `called auto` returns to newest; an unearned name
  is refused.
- Persistence confirmed: a second runner on the same terminal saw all the
  titles and the pin carried over.
- The flavoured-title announcement ("a name to carry / The city has a name
  for you now: the one they cross the street from") fires in real play, at
  the end of the command whose shift-tick earns it (verified via `rest`).
  NOTE for the harness: calling `record_progress()` directly queues the
  announcement but does not flush it; only a real command invocation does.

## Real-world pets (pm_pet): clean

- Adopt (needs a safehouse first, refused without), name, and the full care
  loop (feed needs a bought bag; water and play are free) all read right.
- The greeting on `rest` at the home district works (the cat and its bottle
  cap).
- Neglect is telegraphed: the decline lines fire on the way down and the
  loss lands ("the flat is a flat again. Biscuit is gone.") only after a run
  of shifts at nothing.
- `pet let go` works with its confirm and coda.
- The retire epilogue carries the pet: "and in the one that was not for the
  work / The cat outlived you, which cats do..."

## Digital familiars (pn_familiar): clean

- `familiar get` lists the five with their memory cost; a 2-memory one is
  refused on a full deck ("wants 2 memory and the deck has 1 it could give a
  familiar"); unloading a program makes room. Name, dormant, and drop all
  work.
- Every in-run beat speaks, verified directly on a live run: connect, amber,
  red, lockdown, black ICE, clean and burned jack-outs, idle and dormant.
  The chatter-bird's connect ("Ooh. Their taste is all over this") through
  its black-ICE silence ("The chatter-bird stops talking. The chatter-bird
  never stops talking. That is how you know.") to its burned exit ("We do
  not talk about this one") all land.
- Left unrun it goes dormant and is not lost, as designed.

## Harness note, not a game bug

The pn_familiar persona's own run did not fire because its city_steps
navigation did not travel to the job's district before `jack in`, and
`jack in --force` was tried from the wrong place. The in-run voice was
verified with a controlled run that placed the character in the job district
and forced the escalations. A better run-driver in the harness would catch
this class; the game is correct.

## One mild observation

When you check `pet` repeatedly on a failing animal, the status shows the
same failing line each time, because a failing animal is in the same state.
The `advance` warnings themselves vary (window, then door). Defensible as
is; if it ever grates, cycle the failing greeting.
