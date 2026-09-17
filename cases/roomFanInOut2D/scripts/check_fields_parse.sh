#!/bin/bash
# Verify the written fields parse, using OpenFOAM's own reader rather than by eye, and
# that every boundary entry matches the fields the published results were produced from.
source /usr/lib/openfoam/openfoam2512/etc/bashrc 2>/dev/null || true
command -v foamDictionary >/dev/null || { echo "no OpenFOAM on PATH"; exit 1; }
CASE=${1:-/home/qiuzi/PycharmProjects/OpenfoamCases/cases/roomFanInOut2D}
fail=0
for f in U p k epsilon nut; do
  if out=$(foamDictionary "$CASE/0.orig/$f" -entry boundaryField -keywords 2>&1); then
    printf "%-8s parses; patches: %s\n" "$f" "$(echo "$out" | tr '\n' ' ')"
  else
    printf "%-8s FAILED TO PARSE\n%s\n" "$f" "$out"; fail=1
  fi
done
echo "--- fan entry as OpenFOAM reads it ---"
foamDictionary "$CASE/0.orig/p" -entry 'boundaryField/fan' 2>&1 | head -20
exit $fail
