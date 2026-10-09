# Single source of numerical and physical choices (SI units)
U=22.2
nu=1.5e-5
endTime=8
maxCo=0.9
maxDeltaT=0.0041666667   # >=2 solver steps per 120-fps sample interval
nRanks=14
# Domain and base grid (1 m cubes)
xmin=-55
xmax=50
ymin=-15
ymax=15
zmin=0
zmax=15
nx=105
ny=30
nz=15
# snappy levels: base 1 m / 2^level
surfaceLevel=3           # 0.125 m body nominal
nearLevel=2              # 0.25 m around vehicle/wake
pathLevel=3              # 0.125 m cyclist-side sampling corridor
rho=1.225
Aref=9.78
