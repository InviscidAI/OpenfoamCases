#!/bin/sh
set -eu

cd "${0%/*}/.."

np="${NP:-24}"
log="${LOG:-log.pimpleFoam}"
mesh_preset="${MESH_PRESET:-benchmark-5m}"

if [ "${GENERATE_MESH:-0}" = "1" ]; then
    python3 scripts/generate_ogrid_mesh.py --case . --preset "$mesh_preset"
fi

foamDictionary system/decomposeParDict -entry numberOfSubdomains -set "$np" >/dev/null
checkMesh -allTopology -allGeometry > log.checkMesh 2>&1
decomposePar -force > log.decomposePar 2>&1

if [ -n "${MPI_RUN:-}" ]; then
    $MPI_RUN pimpleFoam -parallel > "$log" 2>&1
else
    mpirun -np "$np" pimpleFoam -parallel > "$log" 2>&1
fi

if [ "${RECONSTRUCT_LATEST:-0}" = "1" ]; then
    reconstructPar -latestTime > log.reconstructPar 2>&1
fi
