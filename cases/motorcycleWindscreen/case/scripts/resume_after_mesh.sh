#!/usr/bin/env bash
set -euo pipefail
source config/run.conf
rm -rf 0; cp -a 0.orig 0
cells=$(awk '/cells:/{print $2;exit}' logs/checkMesh.basic.log); echo "$cells" > results/cell_count.txt
cp constant/turbulenceProperties.steady constant/turbulenceProperties
cp system/fvSchemes.steady system/fvSchemes; cp system/fvSolution.steady system/fvSolution; cp system/controlDict.steady system/controlDict
rm -rf processors*
decomposePar -force -fileHandler collated > logs/decomposeSteady.log 2>&1
mpirun --oversubscribe -np "$NPROCS" simpleFoam -parallel -fileHandler collated > logs/simpleFoam.log 2>&1
rm -rf processors${NPROCS}/0; mv processors${NPROCS}/${STEADY_ITERS} processors${NPROCS}/0; rm -rf processors${NPROCS}/0/uniform
cp constant/turbulenceProperties.transient constant/turbulenceProperties
cp system/fvSchemes.transient system/fvSchemes; cp system/fvSolution.transient system/fvSolution; cp system/controlDict.transient system/controlDict
mpirun --oversubscribe -np "$NPROCS" pimpleFoam -parallel -fileHandler collated > logs/pimpleFoam.log 2>&1
reconstructPar -latestTime -fileHandler collated > logs/reconstruct.log 2>&1
python3 scripts/extract_metric.py | tee logs/metric.log
printf '%s\n' stock > results/geometry_name.txt
printf 'case=stock cells=%s dt=%s sample=[%s,%s] nProcs=%s\n' "$cells" "$DELTA_T" "$WARMUP" "$SAMPLE_END" "$NPROCS" > results/run_summary.txt
find postProcessing/centreline -name '*.vtp' | wc -l > results/centreline_frame_count.txt
