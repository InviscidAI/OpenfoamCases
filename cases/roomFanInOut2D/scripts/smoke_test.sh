#!/bin/bash
# Prove the case runs from a clean checkout.
#
# Copies only what git tracks into a temp directory and runs Allrun there. Copying the
# working tree would hide exactly the failure this looks for: a file the case needs that
# is gitignored, which is how a repository ends up with cases nobody outside it can run.
#
# Usage: scripts/smoke_test.sh        (requires OpenFOAM in the environment)
if [ -z "$WM_PROJECT_DIR" ] || ! command -v pimpleFoam >/dev/null 2>&1; then
    echo "Source your OpenFOAM environment first (e.g. . /path/to/OpenFOAM/etc/bashrc)" >&2
    exit 1
fi
set -e
CASE_DIR=$(cd "$(dirname "$0")/.." && pwd)
REPO=$(git -C "$CASE_DIR" rev-parse --show-toplevel)
CASE=${CASE_DIR#"$REPO"/}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

cd "$REPO"
git ls-files "$CASE" | while read -r f; do
    mkdir -p "$TMP/$(dirname "${f#"$CASE"/}")"
    cp "$f" "$TMP/${f#"$CASE"/}"
done
chmod +x "$TMP/Allrun" "$TMP"/scripts/*.sh 2>/dev/null || true
echo "tracked files copied:"
find "$TMP" -type f | sed "s|$TMP/||" | sort | sed 's/^/  /'

# Two seconds of flow is enough to prove mesh, fields and boundary types all load.
python3 - "$TMP/system/controlDict" <<'PY'
import re, sys, pathlib
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = re.sub(r'endTime\s+[^;]+;', 'endTime         2;', s, count=1)
s = re.sub(r'writeInterval\s+[^;]+;', 'writeInterval   1;', s, count=1)
p.write_text(s)
PY

cd "$TMP"
./Allrun in > log.allrun 2>&1 || { echo "ALLRUN FAILED"; tail -25 log.allrun; exit 1; }
echo "--- checkMesh verdict ---"; grep -E "^Mesh OK|^\*\*\*" log.allrun | head -3
echo "--- solver reached ---";   grep -E "^Time = " log.allrun | tail -1
echo "SMOKE TEST PASSED"
