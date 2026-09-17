#!/bin/bash
# Verify the initial fields parse, using OpenFOAM's own reader rather than by eye.
#
# These are written by write_initial_fields.py rather than committed as the binary fields
# the published results came from, so "it looks right" is not enough -- the question is
# what OpenFOAM makes of them. This caught a real bug: a sub-dictionary emitted with a
# trailing semicolon.
#
# Usage: scripts/check_fields_parse.sh [case-dir]   (requires OpenFOAM in the environment)
if [ -z "$WM_PROJECT_DIR" ] || ! command -v foamDictionary >/dev/null 2>&1; then
    echo "Source your OpenFOAM environment first (e.g. . /path/to/OpenFOAM/etc/bashrc)" >&2
    exit 1
fi
CASE=${1:-$(cd "$(dirname "$0")/.." && pwd)}
fail=0
for f in U p k epsilon nut; do
    if out=$(foamDictionary "$CASE/0.orig/$f" -entry boundaryField -keywords 2>&1); then
        printf "%-8s parses; patches: %s\n" "$f" "$(echo "$out" | tr '\n' ' ')"
    else
        printf "%-8s FAILED TO PARSE\n%s\n" "$f" "$out"
        fail=1
    fi
done
echo "--- fan entry as OpenFOAM reads it ---"
foamDictionary "$CASE/0.orig/p" -entry 'boundaryField/fan' 2>&1 | head -20
exit $fail
