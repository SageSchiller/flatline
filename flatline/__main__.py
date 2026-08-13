"""`python3 -m flatline` and the zipapp entry point both land here."""

import sys

from .app import main

if __name__ == '__main__':
    sys.exit(main())
