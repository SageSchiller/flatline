# Honest-play sweep findings (for D157)

Five personas, no crashes. Findings, by severity.

## 1. Partner bonds are still unreachable by play (px_bond) — REAL, needs fix
Crewed/hired Vesper and ran 40 jobs beside them over 117 shifts. rival.jobs
reached 9 (the D145 counter fix works), but disposition only reached +6,
nowhere near the +60 a partner needs. Cause: the rival keeps taking board
work in competition with you (-3 disposition each), which swamps the +6 a
cooperative run gives. A CREWED ally should not also be competing with you
on the board and losing disposition for it. Fix in D157: pause the rival's
board competition (and its -3) while they are on your crew, and/or a bigger
disposition gain from running together.

## 2. The reckoner (record:15, then 20) is too steep (pv_achiever) — tune
A 204-shift, 26-run completionist campaign earned 11 of 25 record lines and
never reached record:15. Lines out of reach for a netrunner-explorer:
fights/wall/champion/stood_up/blooded/doorways (all floor/combat), drift
(needs chrome), bonds (see #1), spine (the ending), haul (20k night). So the
reckoner effectively demands playing every playstyle at once. Fix in D157:
lower the reckoner opener to ~10 and the payoff to ~15, or gate on
sections-done rather than raw line count; and/or have The Unit's opener hint
which lines are short.

## 3. The under ending's posting is walled to a breach build (pu_under) — verify/ease
A capable academic (Intrusion+Crypto trained, Siphon loaded) could not
finish the posture-72 Deepwater posting by breaching, so never reached
dw_carried/read/offer/under. D146 added a brief hint to approach it as an
inside job; the driver did not use `approach social`. Confirm the inside/
social approach actually makes the posting winnable for a runs-7 character;
if not, ease it, because the whole under path is gated behind this one run.

## 4. The drift ladder is unverified by play (pw_chem) — driver gap, check
The chem persona built a redline habit and played Ninety to its close
(ninety_noticed/stopped/closed all fired — that system works), and detox
worked. But the drift climb failed: the driver could not install chrome
(guessed ware keys), so Dissonance stayed at 12 (Grounded) and the
Submerged/Dissolved bands were never reached by play. Likely a driver gap,
not a game bug; verify the bands with a proper chrome install.

## 5. Balance is broadly fine; pet feed is negligible (py_balance) — minor
End 1,163c, range 95-6,436c, 6 of 50 cycles under 500c: money stays a real
constraint. Sinks: pet feed 360c and clinic 585c over 50 cycles. Pet feed
(7.5c/feed) is trivial, which is acceptable (a pet should not bankrupt you).
No action needed unless you want feed to matter economically.

## Resolution (D157, same day)

Every wall above is closed on the build after D157, by play:

- Under: the posting completes (`pu_under.py`, posting DONE, chain on to
  the offer and settled, 0 crashes). Three causes, all fixed in the game:
  the posting network spawned black ICE on the objective (`generate(lethal=)`),
  the persona's route was heat-blocked and it ignored the refusal
  (harness `do_step` now takes the out the refusal names), and `now`
  advised `drop` on the posting ten times running (`now` never advises
  `drop` on a story contract now; inside job or the walk into them).
- Bond: partner by shift 27 after 10 jobs at +67 (`px_bond.py` pays the
  retainer for real; cooperative gains +8/+3; crew excluded from board
  competition).
- Reckoner: opens on 10 record lines, speaks on 15.
- Finds: left as designed (career-gated); a longer persona is the measure.
- Harness: `drive_run` trusts the brief's first concrete step; the driver
  that second-guessed it finished fewer runs.
