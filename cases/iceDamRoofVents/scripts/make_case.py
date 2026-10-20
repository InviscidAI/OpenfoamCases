#!/usr/bin/env python3
"""Write one run of the roof section as an OpenFOAM v2512 case.

usage: make_case.py <vented|buried> <case dir> [--end T] [--write DT] [--ranks N] [--mesh-scale S]
                    [--no-heat]

The numerics are radiatorUnderWindow's curtain runs': buoyantPimpleFoam, k-omega SST with the
buoyancy source, a perfect gas, Euler in time, limitedLinear, PIMPLE 2 x 2. The boundaries are
the README's: the ceiling's heat from the 21.1 C room through the insulation's
local depth (h per face, written by setup_fields.py once the mesh exists), the deck to the
-5.6 C night through 1.733 m2K/W, the soffit and fascia boards, and the openings at the outdoor
air's barometric pressure face by face. --no-heat sets the room to the outdoor temperature, for
the check that still air stays still.
"""
import argparse
import os
import shutil
import stat
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import roof

ap = argparse.ArgumentParser()
ap.add_argument("variant", choices=("vented", "buried"))
ap.add_argument("case")
ap.add_argument("--end", type=float, help="default 3600 s vented, 7200 s buried (the solved runs)")
ap.add_argument("--write", type=float, default=7.5)
ap.add_argument("--ranks", type=int, default=4)
ap.add_argument("--mesh-scale", type=float, default=1.5)
ap.add_argument("--no-heat", action="store_true")
a = ap.parse_args()
if a.end is None:
    a.end = 3600.0 if a.variant == "vented" else 7200.0

V = a.variant
C = os.path.abspath(a.case)
T_OUT = roof.T_OUT
T_ROOM = roof.T_OUT if a.no_heat else roof.T_ROOM
OPEN = ("soffitVent", "ridge") if V == "vented" else ("ridge",)
WALLS = (("deck", "insulation", "wall", "fascia", "soffit", "ridgeSides") if V == "vented"
         else ("deck", "insulation", "wall", "ridgeSides"))
WALLRE = "(" + "|".join(WALLS) + ")"
OPENRE = "(" + "|".join(OPEN) + ")"
H_DECK = 1.0 / roof.R_ROOF
H_BOARD = 1.0 / (roof.R_BOARD + roof.R_FILM)

HDR = "FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n"


def write(rel, cls, body):
    path = os.path.join(C, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    obj = os.path.basename(rel)
    with open(path, "w") as f:
        f.write(HDR.format(cls=cls, obj=obj) + body)


def field(name, cls, dims, internal, walls, openings, extra=""):
    write(f"0.orig/{name}", cls, f"""dimensions      {dims};
internalField   {internal};
boundaryField
{{
    "{WALLRE}" {{ {walls} }}
    "{OPENRE}" {{ {openings} }}{extra}
    frontAndBack {{ type empty; }}
}}
""")


# ---------------------------------------------------------------- 0.orig
field("U", "volVectorField", "[0 1 -1 0 0 0 0]", "uniform (0 0 0)",
      "type noSlip;", "type pressureInletOutletVelocity; value uniform (0 0 0);")
field("p_rgh", "volScalarField", "[1 -1 -2 0 0 0 0]", "uniform 1e5",
      "type fixedFluxPressure; value uniform 1e5;",
      # p0 face by face (setup_fields.py): the -5.6 C outdoor air's barometric pressure at the face
      "type prghTotalPressure; rho rho; p0 uniform 1e5; value uniform 1e5;")
field("p", "volScalarField", "[1 -1 -2 0 0 0 0]", "uniform 1e5",
      "type calculated; value uniform 1e5;", "type calculated; value uniform 1e5;")
field("k", "volScalarField", "[0 2 -2 0 0 0 0]", "uniform 1e-4",
      "type kLowReWallFunction; value uniform 1e-4;",
      "type inletOutlet; inletValue uniform 1e-4; value uniform 1e-4;")
field("omega", "volScalarField", "[0 0 -1 0 0 0 0]", "uniform 1.0",
      "type omegaWallFunction; value uniform 1.0;",
      "type inletOutlet; inletValue uniform 1.0; value uniform 1.0;")
field("nut", "volScalarField", "[0 2 -1 0 0 0 0]", "uniform 0",
      "type nutkWallFunction; value uniform 0;", "type calculated; value uniform 0;")
field("alphat", "volScalarField", "[1 -1 -1 0 0 0 0]", "uniform 0",
      "type compressible::alphatJayatillekeWallFunction; Prt 0.85; value uniform 0;",
      "type calculated; value uniform 0;")

boards = "" if V == "buried" else f"""
    // 19 mm soffit and fascia boards to the outdoor air: 1/(0.158 + 0.107)
    "(soffit|fascia)"
    {{
        type            externalWallHeatFluxTemperature;
        mode            coefficient;
        h               uniform {H_BOARD:.6g};
        Ta              constant {T_OUT:.6g};
        kappaMethod     fluidThermo;
        value           uniform {T_OUT:.6g};
    }}"""
write("0.orig/T", "volScalarField", f"""dimensions      [0 0 0 1 0 0 0];
internalField   uniform {T_OUT:.6g};
boundaryField
{{
    // the deck's underside to the -5.6 C night through OSB, shingles, 0.24 m of snow and the
    // still-air film on the snow: 1/{roof.R_ROOF:.4f} W/m2K
    deck
    {{
        type            externalWallHeatFluxTemperature;
        mode            coefficient;
        h               uniform {H_DECK:.6g};
        Ta              constant {T_OUT:.6g};
        kappaMethod     fluidThermo;
        value           uniform {T_OUT:.6g};
    }}
    // the insulation's upper surface: the {T_ROOM - 273.15:.1f} C room through its film and the
    // insulation's local depth; h is written face by face by setup_fields.py
    insulation
    {{
        type            externalWallHeatFluxTemperature;
        mode            coefficient;
        h               uniform 0.22;
        Ta              constant {T_ROOM:.6g};
        kappaMethod     fluidThermo;
        value           uniform {T_OUT:.6g};
    }}{boards}
    "(wall|ridgeSides)" {{ type zeroGradient; }}
    "{OPENRE}" {{ type inletOutlet; inletValue uniform {T_OUT:.6g}; value uniform {T_OUT:.6g}; }}
    frontAndBack {{ type empty; }}
}}
""")

# ---------------------------------------------------------------- constant
write("constant/g", "uniformDimensionedVectorField", "dimensions [0 1 -2 0 0 0 0];\nvalue (0 -9.81 0);\n")
write("constant/thermophysicalProperties", "dictionary", f"""thermoType
{{
    type            heRhoThermo;
    mixture         pureMixture;
    transport       const;
    thermo          hConst;
    equationOfState perfectGas;
    specie          specie;
    energy          sensibleEnthalpy;
}}
pRef            100000;
mixture
{{
    specie          {{ molWeight 28.96; }}
    thermodynamics  {{ Cp 1005; Hf 0; Tref {T_OUT:.6g}; Href 0; }}
    transport       {{ mu 1.72e-05; Pr 0.71; }}
}}
""")
write("constant/turbulenceProperties", "dictionary", """simulationType  RAS;
RAS
{
    RASModel        kOmegaSST;
    turbulence      on;
    printCoeffs     on;
}
""")
write("constant/fvOptions", "dictionary", """buoyancyTurb
{
    type            buoyancyTurbSource;
    selectionMode   all;
}
""")

# ---------------------------------------------------------------- system
write("system/fvSchemes", "dictionary", """ddtSchemes      { default Euler; }
gradSchemes     { default Gauss linear; }
divSchemes
{
    default         none;
    div(phi,U)      Gauss limitedLinearV 1;
    energy          Gauss limitedLinear 1;
    div(phi,h)      $energy;
    div(phi,e)      $energy;
    div(phi,K)      Gauss linear;
    div(phi,Ekp)    Gauss linear;
    turbulence      Gauss limitedLinear 1;
    div(phi,k)      $turbulence;
    div(phi,omega)  $turbulence;
    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes    { default Gauss linear corrected; }
interpolationSchemes{ default linear; }
snGradSchemes       { default corrected; }
wallDist            { method meshWave; }
""")
write("system/fvSolution", "dictionary", """solvers
{
    "rho.*"
    {
        solver          PCG;
        preconditioner  DIC;
        tolerance       0;
        relTol          0;
    }
    p_rgh
    {
        solver          GAMG;
        smoother        DICGaussSeidel;
        tolerance       1e-7;       // windowAiring's and dryIceCauldron's: 1e-8 stalls near 5e-6 on a still, open 1e5 Pa field
        relTol          0.01;
        maxIter         100;
    }
    p_rghFinal
    {
        $p_rgh;
        relTol          0;
        maxIter         100;
    }
    "(U|h|e|k|omega)"
    {
        solver          PBiCGStab;
        preconditioner  DILU;
        tolerance       1e-7;
        relTol          0.1;
    }
    "(U|h|e|k|omega)Final"
    {
        $U;
        relTol          0;
    }
}
PIMPLE
{
    momentumPredictor           yes;
    nOuterCorrectors            2;
    nCorrectors                 2;
    nNonOrthogonalCorrectors    0;
}
relaxationFactors { equations { ".*" 1; } }
""")
write("system/decomposeParDict", "dictionary", f"numberOfSubdomains {a.ranks};\nmethod scotch;\n")

open_flows = "".join(f"""
    flow{op.capitalize()}_{p}
    {{
        // mass flow through the opening, kg/s per metre of house: net (sum, out positive) and
        // gross (sumMag); the inflow is (sumMag - sum)/2
        type            surfaceFieldValue;
        libs            (fieldFunctionObjects);
        writeControl    timeStep;
        writeInterval   20;
        writeFields     false;
        log             false;
        regionType      patch;
        name            {p};
        operation       {op};
        fields          (phi);
    }}""" for p in OPEN for op in ("sum", "sumMag"))
heat_patches = " ".join(WALLS[:2] + (("soffit", "fascia") if V == "vented" else ()))
write("system/controlDict", "dictionary", f"""application     buoyantPimpleFoam;
startFrom       latestTime;
startTime       0;
stopAt          endTime;
endTime         {a.end:g};
deltaT          0.002;
adjustTimeStep  yes;
maxCo           1;
maxDeltaT       0.1;
writeControl    adjustableRunTime;
writeInterval   {a.write:g};
purgeWrite      2;              // full fields: the last two only; the clip is the planes
writeFormat     binary;
writePrecision  8;
writeCompression off;
timeFormat      general;
timePrecision   8;
runTimeModifiable true;
functions
{{
    // the clip: the whole section, cell values, every write
    clip
    {{
        type            surfaces;
        libs            (sampling);
        writeControl    writeTime;
        surfaceFormat   vtk;
        formatOptions   {{ vtk {{ format binary; }} }}
        interpolate     false;
        fields          (T U);
        surfaces
        {{
            section {{ type cuttingPlane; point (0 0 0.5); normal (0 0 1); interpolate false; }}
        }}
    }}
    // the readout: the deck's underside temperature face by face, every write
    deckT
    {{
        type            surfaces;
        libs            (sampling);
        writeControl    writeTime;
        surfaceFormat   raw;
        interpolate     false;
        fields          (T);
        surfaces
        {{
            deck {{ type patch; patches (deck); interpolate false; }}
            insulation {{ type patch; patches (insulation); interpolate false; }}
        }}
    }}{open_flows}
    // heat through each thermal boundary, W per metre of house (integral column)
    wallHeatFlux
    {{
        type            wallHeatFlux;
        libs            (fieldFunctionObjects);
        writeControl    writeTime;
        writeFields     false;
        log             false;
        patches         ({heat_patches});
    }}
    atticT
    {{
        type            volFieldValue;
        libs            (fieldFunctionObjects);
        writeControl    timeStep;
        writeInterval   20;
        writeFields     false;
        log             false;
        regionType      all;
        operation       volAverage;
        fields          (T);
    }}
    minMaxT
    {{
        type            fieldMinMax;
        libs            (fieldFunctionObjects);
        writeControl    writeTime;
        fields          (T U);
        log             false;
    }}
}}
""")

walls_wall = " ".join(f"{w} {{ type wall; }}" for w in WALLS)
open_patch = " ".join(f"{p} {{ type patch; }}" for p in OPEN)
write("system/changeDictionaryDict", "dictionary", f"""boundary
{{
    {walls_wall}
    {open_patch}
    frontAndBack {{ type empty; }}
}}
""")

# ---------------------------------------------------------------- scripts
shutil.copy(os.path.join(HERE, "setup_fields.py"), C)
shutil.copy(os.path.join(HERE, "roof.py"), C)
shutil.copy(os.path.join(HERE, "make_mesh.py"), C)
# The run's Allrun: mesh, fields and decomposition; given `solve`, the solve. It expects the
# OpenFOAM environment and a Python with gmsh in $PYTHON (default python3). Planes are gzipped
# as they come (all but the newest), and the rest when the solver ends.
allrun = f"""#!/bin/bash
# {V}: written by scripts/make_case.py
#   ./Allrun                 mesh, fields, checkMesh, decomposePar
#   ./Allrun solve [cpu-set] the same, then buoyantPimpleFoam on {a.ranks} ranks (from the latest time)
. $WM_PROJECT_DIR/bin/tools/RunFunctions
set -e
cd "${{0%/*}}"
PYTHON=${{PYTHON:-python3}}
if [ ! -f constant/polyMesh/owner ]; then
    $PYTHON make_mesh.py {V} mesh.msh {a.mesh_scale:g} > log.gmsh 2>&1
    runApplication gmshToFoam mesh.msh
    rm -f mesh.msh
    runApplication changeDictionary -constant
    runApplication checkMesh
fi
if [ ! -d processor0 ]; then
    rm -rf 0 && cp -r 0.orig 0
    runApplication postProcess -func writeCellCentres -time 0
    python3 setup_fields.py > log.setupFields 2>&1
    rm -f 0/C 0/Cx 0/Cy 0/Cz 0/V
    runApplication decomposePar
fi
[ "${{1:-}}" = solve ] || exit 0
CPUS=${{2:-}}
gzip_planes() {{
    for d in postProcessing/clip/*/; do
        [ -d "$d" ] || continue
        newest=$(ls -d postProcessing/clip/*/ | sort -t/ -k3 -g | tail -1)
        if [ "$d" != "$newest" ] && [ -f "$d/section.vtp" ]; then gzip -f "$d/section.vtp"; fi
    done || true
}}
( while sleep 30; do gzip_planes; done ) &
LOOP=$!
if [ -n "$CPUS" ]; then
    mpirun -np {a.ranks} --cpu-set "$CPUS" --bind-to core buoyantPimpleFoam -parallel > log.buoyantPimpleFoam 2>&1 || status=$?
else
    mpirun -np {a.ranks} buoyantPimpleFoam -parallel > log.buoyantPimpleFoam 2>&1 || status=$?
fi
kill $LOOP 2>/dev/null || true
for f in postProcessing/clip/*/section.vtp; do [ -f "$f" ] && gzip -f "$f"; done || true
exit ${{status:-0}}
"""
with open(os.path.join(C, "Allrun"), "w") as f:
    f.write(allrun)
os.chmod(os.path.join(C, "Allrun"), 0o755)
with open(os.path.join(C, "caseInfo"), "w") as f:
    f.write(f"variant {V}\nmesh_scale {a.mesh_scale}\nno_heat {int(a.no_heat)}\n")
print(f"{V}: {C}, end {a.end:g} s, write {a.write:g} s, {a.ranks} ranks, room {T_ROOM - 273.15:.2f} C, "
      f"h_deck {H_DECK:.4f}, h_board {H_BOARD:.4f}")
