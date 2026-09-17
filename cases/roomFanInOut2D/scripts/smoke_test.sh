#!/bin/bash
# Prove the case runs from a clean checkout: copy only what git tracks into a temp dir,
# run Allrun briefly, and confirm the solver advances. Copying the working tree would
# hide exactly the failure this is looking for -- a file the case needs that is gitignored.
source /usr/lib/openfoam/openfoam2512/etc/bashrc 2>/dev/null || true
command -v pimpleFoam >/dev/null || { echo "no OpenFOAM on PATH"; exit 1; }
set -e
REPO=/home/qiuzi/PycharmProjects/OpenfoamCases
CASE=cases/roomFanInOut2D
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

cd "$REPO"
git ls-files "$CASE" | while read -r f; do
  mkdir -p "$TMP/$(dirname "${f#$CASE/}")"
  cp "$f" "$TMP/${f#$CASE/}"
done
chmod +x "$TMP/Allrun" "$TMP"/scripts/*.sh 2>/dev/null || true
echo "tracked files copied:"; find "$TMP" -type f | sed "s|$TMP/||" | sort | sed 's/^/  /'

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
echo "--- patches the solver loaded ---"
grep -A7 "Selecting finite volume" log.allrun | head -3 || true
echo "SMOKE TEST PASSED"
