#!/usr/bin/env bash
# Single source of numerical choices for all three configurations.
export SPEED=25
export END_TIME=4
export DELTA_T=0.001
export MAX_CO=0.9
export NPROCS=5
export NU=1.5e-5
export RHO=1.225
export KINLET=0.09375       # 1% turbulence intensity
export OMEGAINLET=1.12      # 0.5 m turbulence length scale
export AVG_START=2.5        # fixed before examining results
export AVG_END=4.0
# Mesh: 1 m background; nominal surface sizes rider 0.0625 m, wheels 0.03125 m,
# truck 0.0625 m; wake/refinement boxes 0.25 m.
# Geometry/domain shared by all runs
export DOMAIN_XMIN=-14 DOMAIN_XMAX=32 DOMAIN_YHALF=8 DOMAIN_ZMAX=10
export BASE_CELL=1.0 WAKE_CELL=0.25 RIDER_CELL=0.0625 WHEEL_CELL=0.03125 TRUCK_CELL=0.0625
export INLET_TURB_INTENSITY=0.01 INLET_LENGTH_SCALE=0.5
export RHO=1.225 RIDER_AREF=0.448 TRUCK_AREF=9.78
export SIDE_INTERVAL=0.008333333333333 TOP_INTERVAL=0.033333333333333
export SIDE_XMIN=-8 SIDE_XMAX=14 SIDE_ZMIN=0 SIDE_ZMAX=6 TOP_YHALF=4 TOP_Z=1.15
export PIMPLE_OUTER=2 PIMPLE_PRESSURE_CORRECTORS=2 PIMPLE_NONORTH_CORRECTORS=1
export TURBULENCE_MODEL=kOmegaSSTSAS
export ADD_LAYERS=false
