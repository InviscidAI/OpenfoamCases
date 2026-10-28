#!/usr/bin/env python3
"""Write one run of showerFanVsWindow: a small bathroom after a ten-minute shower, cleared by a
ceiling extractor fan or by the window on tilt.

    python3 make_case.py write <run> <dir> [--nprocs 16]
    python3 make_case.py init <dir>
    python3 make_case.py branch <run> <dir> <showerDir>
    python3 make_case.py tracer <dir>

run is
  shower   0-600 s from rest: the shower on, the door shut, the window shut, the fan off;
  fan      600-1500 s from the shower's 600 s state: the fan extracting 15 l/s, the window shut;
  fanCo1   the fan run at Courant number 1 instead of 2, 600-615 s, the check of its time step;
  window   600-1500 s from the shower's 600 s state: the window on tilt, the fan off, with a
           passive tracer of the outdoor air.

`write` writes the dictionaries and the t = 0 fields (shower, window) or the 600 s field
template (fan, fanCo1). `init` puts the barometric pressure and the outdoor 0 C into the t = 0
fields from the cell centres (postProcess -func writeCellCentres -time 0 first). `branch` fills
a branch's 600 s fields from the shower's: fan and fanCo1 copy the shower's mesh (the fan's
grille made an outlet) and its 600 s fields cell for cell; window, after mapFields has mapped the
shower's 600 s fields onto the window mesh's 600, puts the outdoor box and the reveal back to their
rest and checks the room's cells against the shower's. `tracer` writes window's 600/outdoorAir.
../Allrun runs these and OpenFOAM's utilities in order.

Coordinates as ../windowAiring: x into the room from the inside face of the window wall, y up
from the floor, z across the room. The bathroom is x = 0 to 2.5, y = 0 to 2.4, z = -1 to 1.
"""
import argparse
import gzip
import os
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------- the model
G = 9.81
W = {"O2": 31.9988, "N2": 28.0134, "H2O": 18.0153}
Y_AIR = {"O2": 0.2314, "N2": 0.7686, "H2O": 0}       # the room, the hall and outdoors: dry air
R = 8314.46261815324 / (1 / (0.2314 / W["O2"] + 0.7686 / W["N2"]))   # dry air, J/kg K
T_ROOM, T_OUT = 293.15, 273.15
Y_HALL = 1.5                    # the hall's pressure equals the still outdoor air's at the window's mid-height

# One graded box over the outdoor air, the window wall and the room, cut down with subsetMesh as in
# ../windowAiring; (start, end, cells, grading). Every edge of the bath, the spray, the fan's
# grille, the undercut, the window and its sash falls on a grid line.
XS = [(-1.74, -.24, 18, .1), (-.24, 0, 12, 1), (0, .1, 5, 1), (.1, .15, 3, 1), (.15, .3, 8, 1),
      (.3, .4, 5, 1), (.4, .55, 7, 1), (.55, .7, 4, 1), (.7, 2.5, 45, 1)]
YS = [(-1, 0, 10, .15), (0, .01, 1, 1), (.01, .15, 7, 2.5), (.15, .55, 10, 1), (.55, .9, 12, 1),
      (.9, 1.95, 35, 1), (1.95, 2.1, 5, 1), (2.1, 2.4, 10, 1), (2.4, 3.4, 10, 6.67)]
ZBREAK = [-1, -.7, -.3, .07, .25, .4, .5, .65, .7, .83, 1]
ZS = ([(-2.3, -1, 8, .25)]
      + [(a, b, int(np.ceil(round((b - a) / (.02 if (a >= -.3 and b <= .7) else .04), 8))), 1)
         for a, b in zip(ZBREAK, ZBREAK[1:])]
      + [(1, 2.7, 9, 4)])

H2O_JANAF = ("(2.67215 0.00305629 -8.73026e-07 1.201e-10 -6.39162e-15 -29899.2 6.86282)",
             "(3.38684 0.00347498 -6.3547e-06 6.96858e-09 -2.50659e-12 -30208.1 2.59023)", "H 2; O 1;")
THERMO = {
    "O2": ("( 3.69758 0.00061352 -1.25884e-07 1.77528e-11 -1.13644e-15 -1233.93 3.18917 )",
           "( 3.21294 0.00112749 -5.75615e-07 1.31388e-09 -8.76855e-13 -1005.25 6.03474 )", "O 2;"),
    "N2": ("( 2.92664 0.00148798 -5.68476e-07 1.0097e-10 -6.75335e-15 -922.798 5.98053 )",
           "( 3.29868 0.00140824 -3.96322e-06 5.64152e-09 -2.44486e-12 -1020.9 3.95037 )", "N 2;"),
    "H2O": H2O_JANAF,
}

# Each run: end time, Courant limit, field writes (s), plane writes (s).
RUNS = {
    "shower": dict(tend=600, maxco=1, fields=60, planes=5),
    "fan": dict(tend=1500, maxco=2, fields=60, planes=1.25),
    "fanCo1": dict(tend=615, maxco=1, fields=15, planes=1.25),
    "window": dict(tend=1500, maxco=1, fields=60, planes=1.25),
}
SPECIES_FIELDS = ["U", "T", "p", "p_rgh", "O2", "N2", "H2O", "k", "omega", "nut", "alphat"]

HDR = "FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n"


def write(case, rel, body, cls="dictionary", obj=None):
    path = Path(case) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(HDR.format(cls=cls, obj=obj or path.name))
        f.write(textwrap.dedent(body).lstrip("\n"))


def grading(secs):
    return "(" + " ".join(f"({e - s:g} {n} {r:g})" for s, e, n, r in secs) + ")"


def block_mesh(case):
    x0, x1 = XS[0][0], XS[-1][1]
    y0, y1 = YS[0][0], YS[-1][1]
    z0, z1 = ZS[0][0], ZS[-1][1]
    nx, ny, nz = (sum(s[2] for s in a) for a in (XS, YS, ZS))
    write(case, "system/blockMeshDict", f"""
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
        outside   // the outdoor air's open faces; the parts beyond the room go with subsetMesh
        {{
            type patch;
            faces ((0 4 7 3) (0 1 5 4) (3 7 6 2) (0 3 2 1) (4 5 6 7));
        }}
        walls     // the inner wall here; subsetMesh adds every face it exposes
        {{
            type wall;
            faces ((1 2 6 5));
        }}
    );
    """)
    return nx * ny * nz


# ---------------------------------------------------------------- the mesh's sets, patches, zones
def _box(lo, hi):
    return "(" + " ".join(map(str, lo)) + ") (" + " ".join(map(str, hi)) + ")"


def _action(n, t, a, s, extra):
    return f"{{ name {n}; type {t}; action {a}; source {s}; {extra} }}\n"


def _cs(n, a, lo, hi):
    return _action(n, "cellSet", a, "boxToCell", "box " + _box(lo, hi) + ";")


def _fs(n, a, lo, hi):
    return _action(n, "faceSet", a, "boxToFace", "box " + _box(lo, hi) + ";")


def topo(case, run):
    """topoSetDict.keep (the air), .split and createPatchDict (the patches), .zones."""
    window = run == "window"
    if window:
        # the outdoor box, the reveal and the room, less the tilted sash: its 80 mm profile
        # turned about its bottom edge until its top is 140 mm into the room (windowAiring)
        keep = (_cs("keep", "new", (-100, -100, -100), (-.24, 100, 100))
                + _cs("keep", "add", (-.24, .9, -.3), (0, 2.1, .7))
                + _cs("keep", "add", (0, 0, -1), (2.5, 2.4, 1)))
        keep += _action("keep", "cellSet", "subtract", "rotatedBoxToCell",
                        "origin (-0.05 0.9 -0.3); i (0.08 0 0); j (0.14 1.2 0); k (0 0 1);")
    else:
        keep = _cs("keep", "new", (0, 0, -1), (2.5, 2.4, 1))
    keep += _cs("keep", "subtract", (0, 0, -.7), (.7, .55, 1))          # the bath
    write(case, "system/topoSetDict.keep", "actions (\n" + keep + ");\n")
    splits, patches = "", ""

    def patch(n, lo, hi, typ="wall"):
        nonlocal splits, patches
        splits += _action(n + "Faces", "faceSet", "new", "patchToFace", "patch walls;") + _fs(n + "Faces", "subset", lo, hi)
        patches += f"{{ name {n}; patchInfo {{ type {typ}; }} constructFrom set; set {n}Faces; }}\n"

    patch("bath", (-.00001, -.00001, -.70001), (.70001, .55001, 1.00001))
    patch("fan", (.29999, 2.39999, .39999), (.40001, 2.40001, .50001))     # the grille; shut, a wall
    patch("undercut", (2.49999, -.00001, .06999), (2.50001, .01001, .83001), "patch")
    if window:
        patch("outerWalls", (-100, -100, -100), (-.00001, 100, 100))
        patch("sash", (.00001, .89999, -.30001), (.27001, 2.10001, .70001))
        # the sash's faces within the reveal, taken from outerWalls
        splits += (_action("sashReveal", "faceSet", "new", "patchToFace", "patch walls;")
                   + _fs("sashReveal", "subset", (-.23999, .90001, -.29999), (.00001, 2.09999, .69999)))
        splits += _action("sashFaces", "faceSet", "add", "faceToFace", "set sashReveal;")
        splits += _action("outerWallsFaces", "faceSet", "subtract", "faceToFace", "set sashFaces;")
    write(case, "system/topoSetDict.split", "actions (\n" + splits + ");\n")
    write(case, "system/createPatchDict", "pointSync false;\npatches (\n" + patches + ");\n")
    zones = (_cs("roomCells", "new", (0, 0, -1), (2.5, 2.4, 1))
             + _action("room", "cellZoneSet", "new", "setToCellZone", "set roomCells;"))
    zones += (_cs("sprayCells", "new", (.15, .55, .25), (.55, 1.95, .65))
              + _action("spray", "cellZoneSet", "new", "setToCellZone", "set sprayCells;"))
    if window:
        # the room is every cell at x >= 0, the wedge behind the tilted sash included, so the
        # faces at x = 0 close its budget; the gaps are the wedge's faces onto the rest of the room
        zones += (_action("wedgeCells", "cellSet", "new", "rotatedBoxToCell",
                          "origin (-1.05 0.9 -0.3); i (1 0 0); j (0.14 1.2 0); k (0 0 1);")
                  + _cs("wedgeCells", "subset", (0, -100, -100), (100, 100, 100)))
        zones += _action("wedgeFaces", "faceSet", "new", "cellToFace", "set wedgeCells; option all;")
        zones += (_action("innerCells", "cellSet", "new", "cellToCell", "set roomCells;")
                  + _action("innerCells", "cellSet", "subtract", "cellToCell", "set wedgeCells;"))
        zones += (_action("roomFaces", "faceSet", "new", "cellToFace", "set innerCells; option all;")
                  + _action("wedgeFaces", "faceSet", "subset", "faceToFace", "set roomFaces;"))
        for n, lo, hi in [("gapTop", (-.00001, 2.05, -.29999), (1, 100, .69999)),
                          ("gapLeft", (-.00001, 0, -.30001), (1, 100, -.29999)),
                          ("gapRight", (-.00001, 0, .69999), (1, 100, .70001))]:
            zones += (_action(n + "Faces", "faceSet", "new", "faceToFace", "set wedgeFaces;")
                      + _fs(n + "Faces", "subset", lo, hi)
                      + _action(n, "faceZoneSet", "new", "setsToFaceZone", f"faceSet {n}Faces; cellSet wedgeCells;"))
        zones += _cs("outdoorCells", "new", (-100, -100, -100), (0, 100, 100))
        zones += _fs("openingFaces", "new", (-.00001, .9, -.3), (.00001, 2.1, .7))
        zones += (_action("boundaryFaces", "faceSet", "new", "patchToFace", 'patches (".*");')
                  + _action("openingFaces", "faceSet", "subtract", "faceToFace", "set boundaryFaces;"))
        zones += _action("opening", "faceZoneSet", "new", "setsToFaceZone", "faceSet openingFaces; cellSet outdoorCells;")
    write(case, "system/topoSetDict.zones", "actions (\n" + zones + ");\n")


# ---------------------------------------------------------------- fields
def fields(case, run, tdir):
    window = run == "window"
    fan = run in ("fan", "fanCo1")
    walls = ["walls", "bath"] + (["outerWalls", "sash"] if window else []) + ([] if fan else ["fan"])
    wall = '"(' + "|".join(walls) + ')"'
    opens = ["undercut"] + (["outside"] if window else []) + (["fan"] if fan else [])

    def field(n, dim, val, bcs, cls="volScalarField"):
        write(case, f"{tdir}/{n}", f"dimensions {dim};\ninternalField uniform {val};\nboundaryField\n{{\n{bcs}\n}}\n", cls, n)

    bcs = "undercut { type pressureInletOutletVelocity; value uniform (0 0 0); }\n"
    if window:
        bcs += "outside { type pressureInletOutletVelocity; value uniform (0 0 0); }\n"
    if fan:
        bcs += "fan { type flowRateOutletVelocity; volumetricFlowRate constant 0.015; value uniform (0 1.5 0); }\n"
    field("U", "[0 1 -1 0 0 0 0]", "(0 0 0)", bcs + wall + " { type noSlip; }", "volVectorField")
    bcs = "\n".join(n + " { type prghTotalPressure; rho rho; p0 uniform 1e5; value uniform 1e5; }" for n in opens if n != "fan")
    if fan:
        bcs += "\nfan { type fixedFluxPressure; value uniform 1e5; }"
    field("p_rgh", "[1 -1 -2 0 0 0 0]", "1e5", bcs + "\n" + wall + " { type fixedFluxPressure; value uniform 1e5; }")
    field("p", "[1 -1 -2 0 0 0 0]", "1e5", '".*" { type calculated; value uniform 1e5; }')
    bcs = f"undercut {{ type inletOutlet; inletValue uniform {T_ROOM}; value uniform {T_ROOM}; }}\n"
    if window:
        bcs += f"outside {{ type inletOutlet; inletValue uniform {T_OUT}; value uniform {T_OUT}; }}\n"
    if fan:
        bcs += "fan { type zeroGradient; }\n"
    else:
        bcs += f"fan {{ type fixedValue; value uniform {T_ROOM}; }}\n"
    bcs += f"walls {{ type fixedValue; value uniform {T_ROOM}; }}\nbath {{ type zeroGradient; }}\n"
    if window:
        bcs += '"(outerWalls|sash)" { type zeroGradient; }\n'
    field("T", "[0 0 0 1 0 0 0]", f"{T_ROOM}", bcs)
    for sp, val in Y_AIR.items():
        bcs = "\n".join(f"{n} {{ type inletOutlet; inletValue uniform {val}; value uniform {val}; }}" for n in opens if n != "fan")
        if fan:
            bcs += "\nfan { type zeroGradient; }"
        field(sp, "[0 0 0 0 0 0 0]", str(val), bcs + "\n" + wall + " { type zeroGradient; }")
    for n, dim, val, wf in [("k", "[0 2 -2 0 0 0 0]", "1e-4", "kLowReWallFunction"),
                            ("omega", "[0 0 -1 0 0 0 0]", "1", "omegaWallFunction"),
                            ("nut", "[0 2 -1 0 0 0 0]", "0", "nutkWallFunction"),
                            ("alphat", "[1 -1 -1 0 0 0 0]", "0", "compressible::alphatJayatillekeWallFunction; Prt 0.85")]:
        bcs = ""
        for o in opens:
            bc = f"inletOutlet; inletValue uniform {val};" if n in ("k", "omega") else "calculated;"
            if o == "fan" and n in ("k", "omega"):
                bc = "zeroGradient;"
            bcs += f"{o} {{ type {bc} value uniform {val}; }}\n"
        field(n, dim, val, bcs + wall + f" {{ type {wf}; value uniform {val}; }}")


# ---------------------------------------------------------------- constant/ and system/
SHOWER = """
// buoyancy's production and damping of turbulence, as in windowAiring and dryIceCauldron
buoyancyTurb { type buoyancyTurbSource; selectionMode all; }

// the shower, t = 0 to 600 s: water vapour and sensible heat spread evenly over the spray box.
// volumeMode absolute: Su is the total for the zone, in kg/s for H2O (its equation is in rho Y)
// and W for h; a positive Su adds.
showerVapour
{
    type            scalarSemiImplicitSource;
    timeStart       0;
    duration        600;
    selectionMode   cellZone;
    cellZone        spray;
    volumeMode      absolute;
    injectionRateSuSp
    {
        H2O         (2.833e-4 0);
    }
}
showerHeat
{
    type            scalarSemiImplicitSource;
    timeStart       0;
    duration        600;
    selectionMode   cellZone;
    cellZone        spray;
    volumeMode      absolute;
    injectionRateSuSp
    {
        h           (300 0);
    }
}
"""


def constant(case):
    write(case, "constant/g", """
    dimensions [0 1 -2 0 0 0 0];
    value (0 -9.81 0);
    """, "uniformDimensionedVectorField")
    write(case, "constant/thermophysicalProperties", """
    // O2, N2 and H2O as perfect gases with JANAF thermodynamics and Sutherland viscosity (the
    // coefficients of the v2512 tutorials' thermo.compressibleGas; H2O given air's viscosity),
    // no reactions; as ../dryIceCauldron with its CO2 replaced by water vapour
    thermoType
    {
        type            heRhoThermo;
        mixture         reactingMixture;
        transport       sutherland;
        thermo          janaf;
        energy          sensibleEnthalpy;
        equationOfState perfectGas;
        specie          specie;
    }
    inertSpecie         N2;
    chemistryReader     foamChemistryReader;
    foamChemistryFile   "<constant>/reactions";
    foamChemistryThermoFile "<constant>/thermo.compressibleGas";
    """)
    write(case, "constant/reactions", """
    species ( O2 N2 H2O );
    reactions { }
    """)
    body = ""
    for sp, (hi, lo, el) in THERMO.items():
        body += f"""
    {sp}
    {{
        specie {{ molWeight {W[sp]}; }}
        elements {{ {el} }}
        thermodynamics {{ Tlow 200; Thigh 5000; Tcommon 1000; highCpCoeffs {hi}; lowCpCoeffs {lo}; }}
        transport {{ As 1.67212e-06; Ts 170.672; }}
    }}
"""
    write(case, "constant/thermo.compressibleGas", body)
    write(case, "constant/combustionProperties", "combustionModel none;\n")
    write(case, "constant/chemistryProperties", """
    chemistryType { solver none; }
    chemistry off;
    initialChemicalTimeStep 1;
    """)
    write(case, "constant/turbulenceProperties", """
    simulationType  RAS;
    RAS { RASModel kOmegaSST; turbulence on; printCoeffs on; }
    """)
    write(case, "constant/fvOptions", SHOWER)


def planes(interval, fields_):
    return f"""planes
{{
 type surfaces; libs (sampling);
 writeControl adjustableRunTime; writeInterval {interval};
 surfaceFormat vtk;
 formatOptions {{ vtk {{ format binary; }} }}
 interpolate false; fields ({fields_});
 surfaces
 {{
  clip {{ type cuttingPlane; point (0 1.2 0.455); normal (0 0 1); interpolate false; }}
  windowMid {{ type cuttingPlane; point (0 1.2 0.205); normal (0 0 1); interpolate false; }}
 }}
}}
"""


EARLY_STILLNESS = """
// the outdoor air's speed on a horizontal plane at the window's mid-height, 600-605 s: is it still?
earlyStillness
{
 type surfaces; libs (sampling); writeControl adjustableRunTime; writeInterval 1.25;
 timeStart 600; timeEnd 605;
 surfaceFormat vtk; formatOptions { vtk { format binary; } }
 interpolate false; fields (T U H2O);
 surfaces { horizontal { type cuttingPlane; point (0 1.5 0); normal (0 1 0); interpolate false; } }
}
"""

TRACER = """
// The outdoor air's share of each cell's mass: 1 outdoors and flowing in from the outdoor box, 0 in
// the room at 600 s and under the door. Carried with the solver's phi and rho and diffusivity
// mu + mu_t, the mu_eff that the species equation gives H2O, with H2O's scheme. It changes
// nothing the solver solves. writeControl writeTime: without it the field is written at every
// time step.
outdoorAir
{
 type scalarTransport; libs (solverFunctionObjects);
 field outdoorAir; phi phi; rho rho;
 alphaD 1; alphaDt 1; nCorr 0;
 writeControl writeTime;
}
// its rho-weighted integral over the room (kg of outdoor air) and its range, every ten steps
outdoorAirRoom
{
 type volFieldValue; libs (fieldFunctionObjects);
 regionType cellZone; name room; operation weightedVolIntegrate; weightField rho;
 fields (outdoorAir); writeFields false;
 executeControl timeStep; writeControl timeStep; writeInterval 10;
}
outdoorAirRange
{
 type fieldMinMax; libs (fieldFunctionObjects); mode component; fields (outdoorAir);
 executeControl timeStep; writeControl timeStep; writeInterval 10;
}
"""


def system(case, run, nprocs):
    s = RUNS[run]
    window = run == "window"
    write(case, "system/controlDict", f"""
    // showerFanVsWindow, run {run}
    application     rhoReactingBuoyantFoam;
    startFrom       latestTime;
    startTime       0;
    stopAt          endTime;
    endTime         {s['tend']};
    deltaT          0.002;
    adjustTimeStep  yes;
    maxCo           {s['maxco']};
    maxDeltaT       0.1;
    // full fields every {s['fields']} s, the last two kept, to continue an interrupted solve
    // and to start the branches from the shower's 600 s; the clip is the planes
    writeControl    adjustableRunTime;
    writeInterval   {s['fields']};
    purgeWrite      2;
    writeFormat     ascii;
    writePrecision  14;
    writeCompression on;
    timeFormat      general;
    timePrecision   8;
    runTimeModifiable false;

    functions
    {{
        #include "functions"
    }}
    """)
    flds = "T U H2O outdoorAir" if window else "T U H2O"
    body = (HERE / "moistureBudget").read_text() + "\n"
    if window:
        body += TRACER
    body += planes(s["planes"], flds)
    if window:
        body += EARLY_STILLNESS
    write(case, "system/functions", body)
    # the planes at t = 0 from the initial fields, which the solver does not write
    write(case, "system/planesT0", "functions {\n" + planes(s["planes"], "T U H2O") + "}\n")
    species = "\n".join(f"            {sp} limitedLinear01 1;" for sp in W)
    tracer_scheme = "    div(phi,outdoorAir) Gauss limitedLinear01 1;\n" if window else ""
    write(case, "system/fvSchemes", f"""
    // windowAiring's schemes; the species bounded to 0-1
    ddtSchemes      {{ default Euler; }}
    gradSchemes     {{ default Gauss linear; }}
    divSchemes
    {{
        default         none;
        div(phi,U)      Gauss limitedLinearV 1;
        div(phi,Yi_h)   Gauss multivariateSelection
        {{
{species}
            h   limitedLinear 1;
        }};
{tracer_scheme}        div(phi,K)      Gauss linear;
        turbulence      Gauss limitedLinear 1;
        div(phi,k)      $turbulence;
        div(phi,omega)  $turbulence;
        div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
    }}
    laplacianSchemes    {{ default Gauss linear corrected; }}
    interpolationSchemes{{ default linear; }}
    snGradSchemes       {{ default corrected; }}
    wallDist            {{ method meshWave; }}
    // p_rgh's flux for the solver; H2O's for the vapour monitor
    fluxRequired        {{ default no; p_rgh; H2O; }}
    """)
    tracer_solver = "    outdoorAir  { solver PBiCGStab; preconditioner DILU; tolerance 1e-10; relTol 0; }\n" if window else ""
    write(case, "system/fvSolution", """
    solvers
    {
        "rho.*"     { solver PCG; preconditioner DIC; tolerance 0; relTol 0; }
    """ + textwrap.indent(tracer_solver, "    ") + """\
        p_rgh       { solver GAMG; smoother DICGaussSeidel; tolerance 1e-7; relTol 0.01; }
        p_rghFinal  { $p_rgh; relTol 0; maxIter 100; }
        "(U|h|k|omega|Yi)"      { solver PBiCGStab; preconditioner DILU; tolerance 1e-8; relTol 0.1; }
        "(U|h|k|omega|Yi)Final" { $U; relTol 0; }
    }
    PIMPLE
    {
        momentumPredictor        yes;
        nOuterCorrectors         2;
        nCorrectors              2;
        nNonOrthogonalCorrectors 0;
    }
    relaxationFactors { equations { ".*" 1; } }
    """)
    write(case, "system/decomposeParDict", f"""
    numberOfSubdomains {nprocs};
    method scotch;
    """)
    if window:
        write(case, "system/mapFieldsDict", "patchMap ();\ncuttingPatches ();\n")


# ---------------------------------------------------------------- reading and writing fields
def raw(path):
    p = Path(path)
    return p.read_bytes() if p.exists() else gzip.open(str(p) + ".gz", "rb").read()


def field_values(b, key=b"internalField", components=1):
    pos = b.index(key) + len(key)
    m = re.compile(rb"\s*uniform\s+([^;]+);").match(b, pos)
    if m:
        return np.array([float(x) for x in m[1].strip(b"() ").split()]) if components > 1 else float(m[1])
    m = re.compile(rb"\s*nonuniform\s+List<\w+>\s*(\d+)\s*\(").match(b, pos)
    if not m:
        raise ValueError((key, b[pos:pos + 100]))
    n, i = int(m[1]), m.end()
    if re.search(rb"format\s+(\w+)", b)[1] == b"binary":
        raise SystemExit("binary fields are not read here")
    v = np.array(b[i:b.index(b")\n;", i)].replace(b"(", b" ").replace(b")", b" ").split(), float)
    return v.reshape(n, components) if components > 1 else v


def patch_values(b, name):
    bf = b.index(b"boundaryField")
    m = re.search(rb"\b" + name.encode() + rb"\s*\{", b[bf:])
    return np.atleast_1d(field_values(b[:bf] + b[bf + m.end():], b"value"))


def put_internal(path, values, components=1):
    """Replace a field's internalField with a nonuniform list, %.14g, keeping the rest."""
    p = Path(path)
    b = raw(p)
    i = b.index(b"internalField")
    j = b.index(b"boundaryField", i)
    v = np.array(values).reshape(-1, components)
    typ = b"vector" if components == 3 else b"scalar"
    payload = ("\n" + "\n".join(("(" + " ".join(f"{x:.14g}" for x in a) + ")") if components == 3 else f"{a[0]:.14g}"
                                for a in v) + "\n").encode()
    p.write_bytes(b[:i] + b"internalField nonuniform List<" + typ + b">\n" + str(len(v)).encode()
                  + b"\n(" + payload + b")\n;\n" + b[j:])
    Path(str(p) + ".gz").unlink(missing_ok=True)


def full(v, n, components):
    if components == 1:
        return np.full(n, v) if np.ndim(v) == 0 else v
    return np.tile(v, (n, 1)) if v.ndim == 1 else v


def gzip_dir(d):
    """Compress a time directory's fields (gzip level 3, no time stamp), as the solver reads them."""
    for f in sorted(Path(d).iterdir()):
        if f.is_file() and f.suffix != ".gz":
            with open(f, "rb") as a, open(str(f) + ".gz", "wb") as o, \
                    gzip.GzipFile(filename="", mode="wb", compresslevel=3, fileobj=o, mtime=0) as z:
                shutil.copyfileobj(a, z)
            f.unlink()


def centres(case):
    """Cell centres from postProcess -func writeCellCentres -time 0; the files are removed."""
    c = Path(case) / "0"
    xyz = np.c_[[field_values(raw(c / n)) for n in ("Cx", "Cy", "Cz")]].T
    for n in ("C", "Cx", "Cy", "Cz"):
        for f in (c / n, c / (n + ".gz")):
            f.unlink(missing_ok=True)
    return xyz


# ---------------------------------------------------------------- the steps
def cmd_write(run, case, nprocs):
    case = Path(case)
    case.mkdir(parents=True, exist_ok=True)
    if run in ("shower", "window"):
        n = block_mesh(case)
        topo(case, run)
        fields(case, run, "0")
        print(f"{run}: background box {n} cells")
    else:
        fields(case, run, "600")
    constant(case)
    system(case, run, nprocs)
    (case / "case.foam").touch()


def cmd_init(case):
    """t = 0: still air, 20 C in the room, 0 C outdoors, each at its barometric pressure; the
    hall's column meets the outdoor one at y = 1.5 m. Also the undercut's and the outdoor box's
    total pressure p0, face by face."""
    case = Path(case)
    run = "window" if (case / "system/mapFieldsDict").exists() else "shower"
    cy = raw(case / "0/Cy")              # its patch values are the face centres
    xyz = centres(case)
    x, y = xyz[:, 0], xyz[:, 1]
    T = np.where(x >= 0, T_ROOM, T_OUT)
    po = lambda y: 1e5 * np.exp(-G * y / (R * T_OUT))
    ph = lambda y: po(Y_HALL) * np.exp(-G * (y - Y_HALL) / (R * T_ROOM))
    p = np.where(x >= 0, ph(y), po(y))
    rho = p / (R * T)
    put_internal(case / "0/T", T)
    put_internal(case / "0/p", p)
    put_internal(case / "0/p_rgh", p + rho * G * y)
    b = raw(case / "0/p_rgh").decode()
    for patch, fun in [("undercut", ph)] + ([("outside", po)] if run == "window" else []):
        v = fun(patch_values(cy, patch))
        new = "p0 nonuniform List<scalar>\n" + str(len(v)) + "\n(\n" + "\n".join(f"{vv:.14g}" for vv in v) + "\n);"
        b, count = re.subn(r"(" + patch + r"\s*\{[^}]*?)p0 uniform 1e5;", lambda m: m[1] + new, b)
        assert count == 1, patch
        print(f"{patch}: {len(v)} faces, p0 {v.min():.3f}-{v.max():.3f} Pa")
    (case / "0/p_rgh").write_text(b)
    gzip_dir(case / "0")
    print(f"{run}: {len(x)} cells, T {T.min()}-{T.max()} K, p {p.min():.3f}-{p.max():.3f} Pa")


def cmd_branch(run, case, shower):
    case, shower = Path(case), Path(shower)
    src = shower / "600"
    if not src.is_dir():
        raise SystemExit(f"{src} is missing: solve the shower (./Allrun shower) first")
    if run in ("fan", "fanCo1"):
        # the shower's mesh, its grille an outlet
        shutil.copytree(shower / "constant/polyMesh", case / "constant/polyMesh", dirs_exist_ok=True)
        p = case / "constant/polyMesh/boundary"
        b, n = re.subn(rb"(\bfan\s*\{\s*type\s+)wall;", rb"\1patch;", p.read_bytes())
        assert n == 1
        p.write_bytes(b)
        # The hall under the door stays at the template's p0 = 1e5 Pa, as in the solved fan runs,
        # not the shower's barometric 99,998.67 Pa (README, "How the case got here").
        n = None
        for name in SPECIES_FIELDS:
            comp = 3 if name == "U" else 1
            v = field_values(raw(src / name), components=comp)
            if n is None:
                n = len(field_values(raw(src / "T")))
            put_internal(case / "600" / name, full(v, n, comp), comp)
        gzip_dir(case / "600")
        print(f"{run}: the shower's mesh and its 600 s fields, {n} cells")
    elif run == "window":
        # after mapFields: outdoor box and reveal (x < 0) back to their rest, the room checked
        xyz = centres(case)
        out = xyz[:, 0] < 0
        base = centres(shower)
        lookup = {tuple(c): i for i, c in enumerate(np.round(base, 8))}
        idx = np.array([lookup[tuple(c)] for c in np.round(xyz[~out], 8)])
        nb = len(base)
        for name in SPECIES_FIELDS:
            comp = 3 if name == "U" else 1
            f = case / "600" / name
            a = full(field_values(raw(f), components=comp), len(xyz), comp).copy()
            a[out] = full(field_values(raw(case / "0" / name), components=comp), len(xyz), comp)[out]
            orig = full(field_values(raw(src / name), components=comp), nb, comp)
            err = float(np.max(np.abs(a[~out] - orig[idx])))
            assert err < 1e-8, (name, err)
            put_internal(f, a, comp)
        gzip_dir(case / "600")
        print(f"window: {len(xyz)} cells, {int(out.sum())} outdoors and in the reveal put back to rest; "
              f"the room's {len(idx)} cells equal the shower's at 600 s")
    else:
        raise SystemExit(f"no branch {run}")


def cmd_tracer(case):
    """600/outdoorAir: 1 in every cell outside the room (x < 0), 0 in the room."""
    case = Path(case)
    subprocess.run(["postProcess", "-func", "writeCellCentres", "-time", "0"], cwd=case, check=True,
                   stdout=open(case / "log.writeCellCentres.tracer", "w"), stderr=subprocess.STDOUT)
    x = centres(case)[:, 0]
    s = (x < 0).astype(int)
    header = '''FoamFile
{
    version     2.0;
    format      ascii;
    class       volScalarField;
    location    "600";
    object      outdoorAir;
}
// Mass fraction of the air that came from outdoors (0 C, 95% RH): 1 outside the room at 600 s
dimensions      [0 0 0 0 0 0 0];
'''
    body = "internalField   nonuniform List<scalar>\n%d\n(\n%s\n)\n;\n" % (len(s), "\n".join(map(str, s)))
    bc = '''
boundaryField
{
    outside     { type inletOutlet; inletValue uniform 1; value uniform 1; }
    undercut    { type inletOutlet; inletValue uniform 0; value uniform 0; }
    walls       { type zeroGradient; }
    bath        { type zeroGradient; }
    fan         { type zeroGradient; }
    outerWalls  { type zeroGradient; }
    sash        { type zeroGradient; }
}
'''
    p = case / "600/outdoorAir"
    p.unlink(missing_ok=True)
    with open(str(p) + ".gz", "wb") as o, gzip.GzipFile(filename="", mode="wb", compresslevel=3, fileobj=o, mtime=0) as z:
        z.write((header + body + bc).encode())
    print(f"window: outdoorAir 1 in {int(s.sum())} of {len(s)} cells")


def main():
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = a.add_subparsers(dest="step", required=True)
    w = sub.add_parser("write")
    w.add_argument("run", choices=list(RUNS))
    w.add_argument("dir")
    w.add_argument("--nprocs", type=int, default=16)
    i = sub.add_parser("init")
    i.add_argument("dir")
    b = sub.add_parser("branch")
    b.add_argument("run", choices=["fan", "fanCo1", "window"])
    b.add_argument("dir")
    b.add_argument("shower")
    t = sub.add_parser("tracer")
    t.add_argument("dir")
    a = a.parse_args()
    if a.step == "write":
        cmd_write(a.run, a.dir, a.nprocs)
    elif a.step == "init":
        cmd_init(a.dir)
    elif a.step == "branch":
        cmd_branch(a.run, a.dir, a.shower)
    else:
        cmd_tracer(a.dir)


if __name__ == "__main__":
    main()
