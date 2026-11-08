#!/bin/sh
# Put the corner run's own purifier surfaces into the middle run, moved by exactly 22 background cells
# (22 x 4.5/56 m) in x and in z, so both purifiers sit alike on the grid and have the same patch faces.
# usage: move_purifier.sh <corner triSurface dir> <middle triSurface dir>; OpenFOAM's environment must be sourced.
set -eu
d=1.767857142857143
for s in purifierIn purifierOut purifierWall; do
  surfaceTransformPoints -translate "($d 0 $d)" "$1/$s.stl" "$2/$s.stl" > /dev/null
done
