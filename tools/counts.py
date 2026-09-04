#!/usr/bin/env python3
"""Print the catalogue counts the README states, read off the modules.

The README's "What is in it" numbers drifted ten behind in four decisions
once (D146). This is the single source: `validate.py`'s `catalogue()` computes
every derivable count, `check_readme` holds the README to it, and this prints
them so a human can paste the current line. `--write` is not automatic on
purpose: the prose around the numbers is written by hand.

    python3 tools/counts.py          # print value and fragment, one per line
    python3 tools/counts.py --check   # exit non-zero if the README has drifted
"""
import os
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
os.environ.setdefault('XDG_DATA_HOME', '/tmp/flatline-counts')
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import validate  # noqa: E402


def main() -> int:
    rows = validate.catalogue()
    width = max(len(f'{v:,}') for v, _ in rows)
    for value, fragment in rows:
        print(f'{value:>{width},}  {fragment}')
    if '--check' in sys.argv:
        rep = validate.Report()
        validate.check_readme(rep)
        for e in rep.errors:
            print(f'DRIFT  {e}', file=sys.stderr)
        return 1 if rep.errors else 0
    return 0


if __name__ == '__main__':
    sys.exit(main())
