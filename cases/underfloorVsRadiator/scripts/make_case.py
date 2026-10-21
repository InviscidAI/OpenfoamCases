#!/usr/bin/env python3
"""Write one run of underfloorVsRadiator: windowAiring's room with its window shut, heated
with 60 W either by the radiator under the window or by the whole floor.

    python3 make_case.py <run> <dir> [--tend 1200] [--write 2.5] [--fields 7.5] [--nprocs 8]

run is `radiator` (the radiator box under the window gives 60 W as an enthalpy source; the
floor is adiabatic) or `floor` (no radiator; the floor gives 60 W as a uniform heat flux,
60 / 14.0 = 4.29 W/m2). Everything else is written identically, mesh included.

Coordinates follow ../windowAiring and ../radiatorUnderWindow: x from the window wall's
room face into the room, y up from the floor, z across the room with z = 0 through the
middle of the window. The clip's section is the plane z = 0.005 m, as windowAiring's.

There is no outdoor volume: the window is shut, and its glass loses heat to 0 C outside
through radiatorUnderWindow's boundary condition (overall U = 2.8 W/m2K with the inside film
left to the solver, h = 4.403 W/m2K to 0 C). The rest of the window wall is insulated; the
ceiling, the inner wall and the two side walls are held at 20 C as the rest of a heated house
(radiatorUnderWindow's ceiling and inner wall).

The mesh is the room part of windowAiring's graded blockMesh box (20 mm across the first
0.3 m from the window wall, 10 mm at the floor, 30 mm over the window band and under the
ceiling, 20 mm at the window's side edges), as one block; the glass is cut out of the window
wall's patch by position (createPatch from a boxToFace subset). The closed room takes
radiatorUnderWindow's pressure reference in mid-room and its p_rghFinal iteration cap.
The Allrun written into the run directory does the rest; ../Allrun drives it.
"""
import argparse
import os
import textwrap

# ---------------------------------------------------------------- geometry (m)
ROOM_X = 4.0            # window wall to inner wall (radiatorUnderWindow, windowAiring)
ROOM_Y = 2.4            # floor to ceiling (radiatorUnderWindow, windowAiring)
ROOM_HZ = 1.75          # half the room's width: 3.5 m (windowAiring)
WIN_Y0, WIN_Y1 = 0.90, 2.10   # radiatorUnderWindow's glass: sill 0.90 m, 1.2 m tall
WIN_HZ = 0.50           # 1.0 m wide (windowAiring)
RAD = dict(x0=0.040, x1=0.123, y0=0.15, y1=0.75)   # windowAiring's radiator box (Stelrad K1 600 x 1000)

TAMB, TOUT = 293.15, 273.15
HEAT_W = 60.0           # windowAiring's radiator; the floor gives the same
FLOOR_A = ROOM_X * 2 * ROOM_HZ
FLOOR_Q = HEAT_W / FLOOR_A    # 4.2857 W/m2
H_GLASS = 4.403         # radiatorUnderWindow: overall U 2.8 W/m2K less the inside film, which the solver resolves

# occupied zone (ASHRAE 55): more than 1.0 m from the window wall, 0.3 m from the other walls
OCC = dict(x0=1.0, x1=ROOM_X - 0.3, hz=ROOM_HZ - 0.3)
OCC_HEIGHTS = (("ankle", 0.1), ("knee", 0.6), ("head", 1.1), ("standing", 1.7))
BAND = 0.02             # half-height of each monitoring band of cells

# windowAiring's room part (its make_case.py XS, YS, ZS from x = 0 and between the floor and ceiling)
XS = [(0.0, 0.3, 15, 1.0), (0.3, 1.0, 16, 3.5), (1.0, 3.8, 31, 1.0), (3.8, ROOM_X, 4, 0.375)]
YS = [(0.0, 0.15, 8, 3.0), (0.15, 0.75, 20, 1.0), (0.75, WIN_Y0, 5, 1.0),
      (WIN_Y0, WIN_Y1, 40, 1.0), (WIN_Y1, ROOM_Y, 10, 1.0)]
ZS = [(-ROOM_HZ, -WIN_HZ, 20, 0.2), (-WIN_HZ, 0.0, 14, 2.5), (0.0, WIN_HZ, 14, 0.4),
      (WIN_HZ, ROOM_HZ, 20, 5.0)]

WALLS = "(glass|windowWall|floor|ceiling|innerWall|sideWalls)"
HDR = "FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n"


def grading(secs):
    return "(" + " ".join(f"({e - s:g} {n} {r:g})" for s, e, n, r in secs) + ")"


def write(path, cls, obj, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(HDR.format(cls=cls, obj=obj))
        f.write(textwrap.dedent(body).lstrip("\n"))


def block_mesh(case):
    x0, x1, y0, y1, z0, z1 = 0.0, ROOM_X, 0.0, ROOM_Y, -ROOM_HZ, ROOM_HZ
    nx, ny, nz = (sum(s[2] for s in a) for a in (XS, YS, ZS))
    write(f"{case}/system/blockMeshDict", "dictionary", "blockMeshDict", f"""
    scale 1;
    vertices
    (
        ({x0} {y0} {z0}) ({x1} {y0} {z0}) ({x1} {y1} {z0}) ({x0} {y1} {z0})
        ({x0} {y0} {z1}) ({x1} {y0} {z1}) ({x1} {y1} {z1}) ({x0} {y1} {z1})
    );
    blocks
    (
        hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz})
        simpleGrading
        (
            {grading(XS)}
            {grading(YS)}
            {grading(ZS)}
        )
    );
    boundary
    (
        windowWall {{ type wall; faces ((0 4 7 3)); }}   // the glass is cut out of it below
        innerWall  {{ type wall; faces ((1 2 6 5)); }}
        floor      {{ type wall; faces ((0 1 5 4)); }}
        ceiling    {{ type wall; faces ((3 7 6 2)); }}
        sideWalls  {{ type wall; faces ((0 3 2 1) (4 5 6 7)); }}
    );
    """)
    return nx * ny * nz


def topo_dicts(case, run):
    e = 1e-4
    write(f"{case}/system/topoSetDict.glass", "dictionary", "topoSetDict", f"""
    actions
    (
        {{ name glassFaces; type faceSet; action new; source patchToFace; patch windowWall; }}
        {{ name glassFaces; type faceSet; action subset; source boxToFace;
           box (-{e} {WIN_Y0 - e:g} -{WIN_HZ + e:g}) ({e} {WIN_Y1 + e:g} {WIN_HZ + e:g}); }}
    );
    """)
    write(f"{case}/system/createPatchDict", "dictionary", "createPatchDict", """
    pointSync false;
    patches
    (
        { name glass; patchInfo { type wall; } constructFrom set; set glassFaces; }
    );
    """)
    zones = ""
    if run == "radiator":
        zones += f"""
        {{ name radiatorCells; type cellSet; action new; source boxToCell;
           box ({RAD['x0']} {RAD['y0']} -{WIN_HZ}) ({RAD['x1']} {RAD['y1']} {WIN_HZ}); }}
        {{ name radiator; type cellZoneSet; action new; source setToCellZone; set radiatorCells; }}"""
    for name, y in OCC_HEIGHTS:
        zones += f"""
        {{ name occ_{name}Cells; type cellSet; action new; source boxToCell;
           box ({OCC['x0']} {y - BAND:g} -{OCC['hz']:g}) ({OCC['x1']:g} {y + BAND:g} {OCC['hz']:g}); }}
        {{ name occ_{name}; type cellZoneSet; action new; source setToCellZone; set occ_{name}Cells; }}"""
    write(f"{case}/system/topoSetDict.zones", "dictionary", "topoSetDict", f"""
    actions
    (
        {zones}
    );
    """)


def fields(case, run):
    write(f"{case}/0.orig/U", "volVectorField", "U", f"""
    dimensions [0 1 -1 0 0 0 0];
    internalField uniform (0 0 0);
    boundaryField
    {{
        "{WALLS}" {{ type noSlip; }}
    }}
    """)
    write(f"{case}/0.orig/p_rgh", "volScalarField", "p_rgh", f"""
    dimensions [1 -1 -2 0 0 0 0];
    internalField uniform 1e5;
    boundaryField
    {{
        "{WALLS}" {{ type fixedFluxPressure; value uniform 1e5; }}
    }}
    """)
    write(f"{case}/0.orig/p", "volScalarField", "p", """
    dimensions [1 -1 -2 0 0 0 0];
    internalField uniform 1e5;
    boundaryField
    {
        ".*" { type calculated; value uniform 1e5; }
    }
    """)
    if run == "floor":
        floor = (f"// the warm floor: {HEAT_W:g} W over its {FLOOR_A:g} m2 as a uniform heat flux\n"
                 f"        floor {{ type externalWallHeatFluxTemperature; mode flux; q uniform {FLOOR_Q:.7g};\n"
                 f"                kappaMethod fluidThermo; value uniform {TAMB}; }}")
    else:
        floor = "floor { type zeroGradient; }      // adiabatic"
    write(f"{case}/0.orig/T", "volScalarField", "T", f"""
    dimensions [0 0 0 1 0 0 0];
    internalField uniform {TAMB};
    boundaryField
    {{
        // radiatorUnderWindow's glass: overall U = 2.8 W/m2K with the inside film left to the solver
        glass {{ type externalWallHeatFluxTemperature; mode coefficient; h uniform {H_GLASS};
                Ta uniform {TOUT}; kappaMethod fluidThermo; value uniform {TAMB}; }}
        windowWall {{ type zeroGradient; }}      // insulated
        {floor}
        // the rest of a heated house
        "(ceiling|innerWall|sideWalls)" {{ type fixedValue; value uniform {TAMB}; }}
    }}
    """)
    for name, dim, val, wf in (("k", "[0 2 -2 0 0 0 0]", "1e-4", "kLowReWallFunction"),
                               ("omega", "[0 0 -1 0 0 0 0]", "1.0", "omegaWallFunction")):
        write(f"{case}/0.orig/{name}", "volScalarField", name, f"""
        dimensions {dim};
        internalField uniform {val};
        boundaryField
        {{
            "{WALLS}" {{ type {wf}; value uniform {val}; }}
        }}
        """)
    write(f"{case}/0.orig/nut", "volScalarField", "nut", f"""
    dimensions [0 2 -1 0 0 0 0];
    internalField uniform 0;
    boundaryField
    {{
        "{WALLS}" {{ type nutkWallFunction; value uniform 0; }}
    }}
    """)
    write(f"{case}/0.orig/alphat", "volScalarField", "alphat", f"""
    dimensions [1 -1 -1 0 0 0 0];
    internalField uniform 0;
    boundaryField
    {{
        "{WALLS}" {{ type compressible::alphatJayatillekeWallFunction; Prt 0.85; value uniform 0; }}
    }}
    """)


def constant(case, run):
    write(f"{case}/constant/g", "uniformDimensionedVectorField", "g", """
    dimensions [0 1 -2 0 0 0 0];
    value (0 -9.81 0);
    """)
    write(f"{case}/constant/thermophysicalProperties", "dictionary", "thermophysicalProperties", f"""
    // radiatorUnderWindow's and windowAiring's air
    thermoType
    {{
        type            heRhoThermo;
        mixture         pureMixture;
        transport       const;
        thermo          hConst;
        equationOfState perfectGas;
        specie          specie;
        energy          sensibleEnthalpy;
    }}
    mixture
    {{
        specie         {{ molWeight 28.96; }}
        thermodynamics {{ Cp 1005; Hf 0; Tref {TAMB}; Href 0; }}
        transport      {{ mu 1.82e-05; Pr 0.71; }}
    }}
    """)
    write(f"{case}/constant/turbulenceProperties", "dictionary", "turbulenceProperties", """
    simulationType  RAS;
    RAS { RASModel kOmegaSST; turbulence on; printCoeffs on; }
    """)
    radiator = ""
    if run == "radiator":
        radiator = f"""
    // windowAiring's radiator: {HEAT_W:g} W, an enthalpy source spread over the box, through which the air
    // passes freely as through a convector's fins
    radiator
    {{
        type            scalarSemiImplicitSource;
        selectionMode   cellZone;
        cellZone        radiator;
        volumeMode      absolute;
        sources {{ h ({HEAT_W:g} 0); }}
    }}"""
    write(f"{case}/constant/fvOptions", "dictionary", "fvOptions", f"""{radiator}
    buoyancyTurb {{ type buoyancyTurbSource; selectionMode all; }}
    """)


def system(case, run, tend, write_int, nprocs, field_int):
    occ = ""
    for name, _ in OCC_HEIGHTS:
        occ += f"""
    occ_{name}
    {{
        $roomMeanT;
        regionType      cellZone;
        name            occ_{name};
    }}"""
    write(f"{case}/system/controlDict", "dictionary", "controlDict", f"""
    // underfloorVsRadiator, run {run}
    application     buoyantPimpleFoam;
    startFrom       latestTime;
    startTime       0;
    stopAt          endTime;
    endTime         {tend};
    deltaT          0.005;
    adjustTimeStep  yes;
    maxCo           1;          // radiatorUnderWindow's and windowAiring's Courant number
    maxDeltaT       0.1;
    // full fields every {field_int} s, the last two kept: to continue an interrupted solve, and
    // so wallHeatFlux, which writes into a time directory whenever it writes, gives the heat
    // through each boundary every {field_int} s. The clip is the planes, every {write_int} s.
    writeControl    adjustableRunTime;
    writeInterval   {field_int};
    purgeWrite      2;
    writeFormat     binary;
    writePrecision  8;
    writeCompression off;
    timeFormat      general;
    timePrecision   8;
    // never re-read while running: a re-read with surfaces planes can crash every rank
    runTimeModifiable false;

    functions
    {{
        #include "functions"
    }}
    """)
    write(f"{case}/system/functions", "dictionary", "functions", f"""
    // ---- every time step ------------------------------------------------------------
    // the room's internal energy is (cv/R) times the integral of p dV for a perfect gas in a
    // closed box (radiatorUnderWindow's energyCheck): the heat budget without the mean temperature
    energyCheck
    {{
        type            volFieldValue;
        libs            (fieldFunctionObjects);
        fields          (p rho);
        operation       volIntegrate;
        regionType      all;
        writeFields     false;
        writeControl    timeStep;
        log             false;
    }}
    roomMeanT
    {{
        type            volFieldValue;
        libs            (fieldFunctionObjects);
        regionType      all;
        operation       volAverage;
        fields          (T);
        writeFields     false;
        writeControl    timeStep;
        log             false;
    }}
    // the occupied zone's mean air temperature in bands {2 * BAND:g} m tall at 0.1, 0.6, 1.1 and
    // 1.7 m (ASHRAE 55: 1.0 m from the window wall, 0.3 m from the others){occ}
    // the glass's and the floor's mean surface temperature; the glass's loss is
    // {H_GLASS} W/m2K times the area integral of (T - {TOUT})
    surfaceT
    {{
        type            surfaceFieldValue;
        libs            (fieldFunctionObjects);
        regionType      patch;
        name            glass;
        operation       areaAverage;
        fields          (T);
        writeFields     false;
        writeControl    timeStep;
        log             false;
    }}
    glassIntT
    {{
        $surfaceT;
        operation       areaIntegrate;
    }}
    floorT
    {{
        $surfaceT;
        name            floor;
    }}
    floorTmax
    {{
        $surfaceT;
        name            floor;
        operation       max;
    }}
    // the heat through every boundary, at the field writes only (see writeInterval)
    wallHeatFlux
    {{
        type            wallHeatFlux;
        libs            (fieldFunctionObjects);
        writeControl    writeTime;
        log             false;
    }}
    minMax
    {{
        type            fieldMinMax;
        libs            (fieldFunctionObjects);
        fields          (T U);
        writeControl    adjustableRunTime;
        writeInterval   {write_int};
        log             false;
    }}
    probes
    {{
        type            probes;
        libs            (sampling);
        fields          (T U);
        writeControl    adjustableRunTime;
        writeInterval   {write_int};
        probeLocations
        (
            (0.5 0.1 0.005) (1.0 0.1 0.005) (2.0 0.1 0.005) (3.0 0.1 0.005)
            (1.0 1.1 0.005) (2.0 1.1 0.005) (3.0 1.1 0.005) (2.0 2.2 0.005)
        );
    }}

    // ---- the clip: radiatorUnderWindow's section through the middle of the window and the radiator, and
    // the whole room at ankle and seated head height. No bounds on any plane.
    planes
    {{
        type            surfaces;
        libs            (sampling);
        writeControl    adjustableRunTime;
        writeInterval   {write_int};
        surfaceFormat   vtk;
        formatOptions   {{ vtk {{ format binary; }} }}
        interpolate     false;
        fields          (T U);
        surfaces
        {{
            mid     {{ type cuttingPlane; point (2 1.2 0.005); normal (0 0 1); interpolate false; }}
            ankle   {{ type cuttingPlane; point (2 0.1 0); normal (0 1 0); interpolate false; }}
            head    {{ type cuttingPlane; point (2 1.1 0); normal (0 1 0); interpolate false; }}
        }}
    }}
    """)
    # the planes at t = 0 from the initial fields, which the solver does not write
    fo = open(f"{case}/system/functions").read()
    with open(f"{case}/system/planesT0", "w") as f:
        f.write(HDR.format(cls="dictionary", obj="planesT0"))
        f.write("functions {\n" + fo[fo.index("\nplanes\n") + 1:] + "}\n")
    write(f"{case}/system/fvSchemes", "dictionary", "fvSchemes", """
    // radiatorUnderWindow's and windowAiring's schemes
    ddtSchemes      { default Euler; }
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
    write(f"{case}/system/fvSolution", "dictionary", "fvSolution", """
    solvers
    {
        "rho.*"     { solver PCG; preconditioner DIC; tolerance 0; relTol 0; }
        // windowAiring's tolerance. radiatorUnderWindow's 1e-8 is below this mesh's round-off
        // floor (about 2.1e-8): in a first pilot both final pressure solves of every step ran to
        // the cap, 2.4 s a step
        p_rgh       { solver GAMG; smoother DICGaussSeidel; tolerance 1e-7; relTol 0.01; }
        // radiatorUnderWindow's cap, kept in case the floor rises
        p_rghFinal  { $p_rgh; relTol 0; maxIter 100; }
        "(U|h|e|k|omega)"      { solver PBiCGStab; preconditioner DILU; tolerance 1e-7; relTol 0.1; }
        "(U|h|e|k|omega)Final" { $U; relTol 0; }
    }
    PIMPLE
    {
        momentumPredictor        yes;
        nOuterCorrectors         2;
        nCorrectors              2;
        nNonOrthogonalCorrectors 0;
        // a closed room: radiatorUnderWindow's reference in mid-room, not in a corner cell, where its
        // continuity error ran away against an adiabatic floor
        pRefPoint                (2.003 1.174 0.013);
        pRefValue                1e5;
    }
    relaxationFactors { equations { ".*" 1; } }
    """)
    write(f"{case}/system/decomposeParDict", "dictionary", "decomposeParDict", f"""
    numberOfSubdomains {nprocs};
    method scotch;
    """)


ALLRUN = """#!/bin/bash
# underfloorVsRadiator, run RUN: written by scripts/make_case.py.
#   ./Allrun        mesh, set up, check, write the t = 0 planes and decompose
#   ./Allrun solve  solve on NPROCS ranks
cd "${0%/*}" || exit 1
. "$WM_PROJECT_DIR/bin/tools/RunFunctions"
set -e
if [ "${1:-}" != solve ]; then
    runApplication blockMesh
    runApplication -s glass topoSet -dict system/topoSetDict.glass
    runApplication createPatch -overwrite
    runApplication -s zones topoSet -dict system/topoSetDict.zones
    rm -rf 0 && cp -r 0.orig 0
    runApplication checkMesh -constant
    runApplication postProcess -dict system/planesT0 -fields '(T U)' -time 0
    runApplication decomposePar
    exit 0
fi
runParallel -n NPROCS buoyantPimpleFoam
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", choices=["radiator", "floor"])
    ap.add_argument("dir")
    ap.add_argument("--tend", type=float, default=1200)
    ap.add_argument("--write", type=float, default=2.5)
    ap.add_argument("--fields", type=float, default=7.5)
    ap.add_argument("--nprocs", type=int, default=8)
    a = ap.parse_args()
    case = a.dir
    n = block_mesh(case)
    topo_dicts(case, a.run)
    fields(case, a.run)
    constant(case, a.run)
    system(case, a.run, f"{a.tend:g}", f"{a.write:g}", a.nprocs, f"{a.fields:g}")
    with open(f"{case}/Allrun", "w") as f:
        f.write(ALLRUN.replace("NPROCS", str(a.nprocs)).replace("RUN", a.run))
    os.chmod(f"{case}/Allrun", 0o755)
    print(f"{a.run}: {case}, {n} cells")


if __name__ == "__main__":
    main()
