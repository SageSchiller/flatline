#!/usr/bin/env bash
# Build the distributable single file.
#
# Stdlib only: zipapp ships with Python, so this needs nothing installed and
# produces something a stranger can run with `python3 flatline.pyz`.
#
# The staging step is not decoration. `flatline/` carries its own __main__.py so
# that `python3 -m flatline` works from the source tree, and zipapp refuses to
# take an entry point when the source already has one. Staging keeps `flatline`
# a real package inside the archive, which relative imports need, and puts the
# archive's entry point beside it rather than inside it.
set -euo pipefail
cd "$(dirname "$0")"

OUT="${OUT:-dist}"
mkdir -p "$OUT"

stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT

cp -r flatline "$stage/flatline"
find "$stage" -name '__pycache__' -type d -prune -exec rm -rf {} +

cat > "$stage/__main__.py" <<'PY'
import sys

from flatline.app import main

sys.exit(main())
PY

python3 -m zipapp "$stage" -p '/usr/bin/env python3' -o "$OUT/flatline.pyz"
chmod +x "$OUT/flatline.pyz"
echo "built $OUT/flatline.pyz"
