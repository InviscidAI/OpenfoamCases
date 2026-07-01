#!/bin/sh
set -eu

cd "${0%/*}/.."

python3 scripts/generate_ogrid_mesh.py --case .
checkMesh -allTopology -allGeometry > log.checkMesh 2>&1
decomposePar -force > log.decomposePar 2>&1
mpirun -np 24 pimpleFoam -parallel > log.pimpleFoam 2>&1
reconstructPar -latestTime > log.reconstructPar 2>&1
