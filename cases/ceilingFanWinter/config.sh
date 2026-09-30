#!/bin/bash
# One configuration file for all down/up/off wedge cases. SI units.
ROOM_RADIUS=3.441282078          # 6.10/sqrt(pi): same 37.21 m2 floor area
ROOM_HEIGHT=3.05
WEDGE_DEG=5.0                   # one-cell rotational wedge; exact axisymmetric equations
# Piecewise uniform r blocks: [0,.76],[.76,3.20],[3.20,R]
R_BREAKS="0 0.76 3.191282078 3.441282078"
R_CELLS="38 61 13"             # dr = 20, 39.9, 19.2 mm; 13 cells through new heater width
# z blocks refine floor/heater, fan slab, and ceiling
Z_BREAKS="0 0.50 2.54 2.80 3.05"
Z_CELLS="25 51 13 13"          # dz = 20, 40, 20, 19.2 mm; 25 cells through new heater height
FAN_RADIUS=0.76
FAN_HUB_RADIUS=0.15             # no tangential forcing at singular axis; physical motor hub
FAN_Z0=2.60
FAN_Z1=2.74
FLOW_MEDIUM=1.70
FLOW_LOW=0.57
SWIRL_RATIO=0.50                # estimated area-mean Utheta/|Uz|; moderate ceiling-fan exit swirl
HEATER_W=1300
HEATER_R0=3.191282078           # 0.25 m radial width against wall
HEATER_R1=3.441282078
HEATER_Z0=0
HEATER_Z1=0.50                  # ring cross-section 0.25 m x 0.50 m
RHO=1.20
CP=1005
NU=1.5e-5
BETA=0.00341
PR=0.71
PRT=0.85
T0=293.15
TREF=293.15
T_AMBIENT=293.15
WALL_H=3.0                      # W/m2/K effective plywood+hall conductance
END_TIME=180                    # 3 min, chosen from 600 s fan-off screening peak at 172.5 s
SAMPLE_DT=0.375                  # 480 intervals, 481 faces including t=0
DT=0.04
MAX_CO=0.9
NPROCS=4
K0=1e-4
EPSILON0=1e-4
