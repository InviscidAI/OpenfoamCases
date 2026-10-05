#!/bin/bash
# The dust's numerics against the temperature's, on one flow.
#
#     scripts/dust_scheme_check.sh positive     # after ./Allrun positive dust
#
# The dust runs carry the dust with bounded first-order upwind and D = 1e-6 nu + nut/0.85;
# the temperature in the same runs uses bounded limitedLinear 1 and, through "nut nut",
# D = nut. This restarts runs/<layout>_dust from its 8 s flow with the dust set to zero
# (and T to the room's) and carries the dust to 9.5 s twice: runs/<layout>_dust_upwind
# exactly as solved, and runs/<layout>_dust_asT with the temperature's scheme and
# diffusivity. The flow equations are untouched, so the two share one flow and differ only
# in the dust's numerics. Filling a clean case on a developed flow gives the steepest fronts
# the dust ever has. Both run at once, 8 MPI ranks each. scripts/summarize_dust.py compares
# them.
set -euo pipefail
cd "$(dirname "$0")/.."
layout=${1:-}
SRC=runs/${layout}_dust
[ -n "$layout" ] && [ -d "$SRC/processors8/8" ] || {
  echo "usage: scripts/dust_scheme_check.sh <layout>, after ./Allrun <layout> dust" >&2; exit 2; }
pids=()
for V in upwind asT; do
  D=runs/${layout}_dust_$V
  rm -rf "$D"; mkdir -p "$D"
  cp -r "$SRC/constant" "$SRC/system" "$SRC/dynamicCode" "$D/"
  cp -r "$SRC/processors8" "$D/"
  rm -rf "$D/processors8/0"
  for f in T dustF dustU; do cp "$SRC/processors8/0/$f" "$D/processors8/8/$f"; done
  sed -i 's/startTime 0;/startTime 8;/; s/endTime 8.0;/endTime 9.5;/; s/writeInterval 8.0;/writeInterval 100;/' "$D/system/controlDict"
  if [ $V = asT ]; then
    sed -i 's/div(phi,dustF) bounded Gauss upwind;/div(phi,dustF) bounded Gauss limitedLinear 1;/; s/div(phi,dustU) bounded Gauss upwind;/div(phi,dustU) bounded Gauss limitedLinear 1;/' "$D/system/fvSchemes"
    sed -i 's/field dustF; alphaD 1e-6; alphaDt 1.1764705882352942;/field dustF; nut nut;/; s/field dustU; alphaD 1e-6; alphaDt 1.1764705882352942;/field dustU; nut nut;/' "$D/system/controlDict"
  fi
  grep -o 'div(phi,dust[FU])[^;]*;' "$D/system/fvSchemes"
  grep -o 'field dust[FU];[^}]*bounded01' "$D/system/controlDict"
  (cd "$D" && mpirun -np 8 --bind-to none pimpleFoam -parallel -fileHandler collated > log.pimpleFoam 2>&1) &
  pids+=($!)
done
rc=0
for p in "${pids[@]}"; do wait "$p" || rc=$?; done
exit "$rc"
