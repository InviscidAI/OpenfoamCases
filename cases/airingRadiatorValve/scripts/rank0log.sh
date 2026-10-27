#!/bin/bash
# One MPI rank of buoyantPimpleFoam, with rank 0 writing its own log, log.buoyantPimpleFoam<suffix>
# in the run, and the other ranks' output dropped. Run by ../Allrun as
#   mpirun -np N scripts/rank0log.sh .open
# The solved runs were launched this way: through mpirun's own output relay, one launch on our
# machine ran at an eighth of its speed with rank 0 blocked writing to it.
if [ "${OMPI_COMM_WORLD_RANK:-${PMI_RANK:-0}}" = 0 ]; then
    exec buoyantPimpleFoam -parallel -fileHandler collated > "log.buoyantPimpleFoam$1" 2>&1
else
    exec buoyantPimpleFoam -parallel -fileHandler collated > /dev/null 2>&1
fi
