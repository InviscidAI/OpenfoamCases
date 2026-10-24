#!/usr/bin/env python3
"""Write one run of dryIceCauldron: a dry-ice cauldron in a living room, front door shut or open.

    python3 make_case.py <run> <dir> [--tend 600] [--write 1.25] [--fields 50] [--nprocs 8]

run is `shut` (the front door and the room's other door shut), `open` (the front door open
to the cold evening outside) or `raised` (shut, with the cauldron on a counter-height table).
`shut` and `open` differ only in the door: `shut` puts a baffle across the doorway at the
wall's inside face; everything else is written identically. `raised` is `shut` with the table's
top and the cauldron 0.46 m higher and the mesh's y bands above 0.75 m re-spaced round them;
everything else, the bands below 0.75 m included, is written as `shut`'s.

Coordinates: x from the inside face of the front wall into the room, y up from the floor,
z across the room. The model is the half of the room on one side of the vertical plane
z = 0 through the middle of the front door and the cauldron, which is a symmetry plane and
the clip's section.

The gas is a mixture of O2, N2 and CO2 with real molar masses and JANAF thermodynamics, solved
with rhoReactingBuoyantFoam (OpenFOAM v2512) with no reactions. The CO2 is a passive species
(it only moves and mixes), but the density is the mixture's, so CO2-laden air is heavier than
air. The cauldron's water surface is an inlet of pure CO2 at the dry ice's sublimation rate.

The mesh is one graded blockMesh box over the outdoor air, the front wall and the room, cut
down with subsetMesh, as in ../windowAiring. The Allrun written into the run directory does
the rest; ../Allrun drives it.
"""
import argparse
import os
import textwrap

# ---------------------------------------------------------------- geometry (m)
ROOM_X = 5.0            # front wall to back wall
ROOM_Y = 2.4            # floor to ceiling (8 ft)
ROOM_HZ = 2.0           # half the room's width: 4.0 m, so 20 m2 and 48 m3
WALL_T = 0.15           # front wall thickness
DOOR_HZ = 0.457         # front door 36 in (0.914 m) wide (the usual US slab)
DOOR_Y1 = 2.032         # and 80 in tall
TABLE = dict(x0=2.25, x1=2.75, y0=0.42, y1=0.45, hz=0.50)   # coffee table top, 1.0 x 0.5 m
CAUL = dict(x0=2.32, x1=2.68, y0=0.45, y1=0.75, hz=0.18)    # cauldron, 0.36 m square (16 in round), 12 in tall
# raised: the same table top at counter height, 0.91 m (a US counter's 36 in, the UK's "around
# 900mm"; README), and the same cauldron on it, its water surface at 1.21 m
TABLE_RAISED = dict(TABLE, y0=0.88, y1=0.91)
CAUL_RAISED = dict(CAUL, y0=0.91, y1=1.21)
NOSE_Y = 0.60           # a toddler's nose: a younger toddler, a child sitting or a dog (README)
LEAK = dict(x0=4.95, hz0=1.95)   # one 5 cm ceiling face in the back corner (the half model's)
OUT_X = 2.0             # outdoor air beyond the wall's outer face
OUT_YHI = 3.4
OUT_HZ = 2.5

# ---------------------------------------------------------------- conditions
TAMB = 294.15           # 21 C (70 F) indoors
# 10 C (50 F) outdoors: NOAA 1991-2020 hourly normals for 31 Oct, 6-8 pm, are 48-50 F at
# Chicago O'Hare and 55-57 F at LaGuardia; Heathrow's October mean minimum is 8.8 C
TOUT = 283.15
# the CO2 leaving the water: no measurement found; 5 C is the flowvis.org report's assumption
# (README, "The room"). Its density matters far less than the CO2's own: 5 C against 21 C makes gas 6%
# denser, CO2 against air 53%
T_GAS = 278.15
# 2.5 g/s, held for the ten minutes (1.5 kg, 3.3 lb): Chillistick's 500 g in a kettle of hot
# water gives fog for 3-4 minutes (2.1-2.8 g/s), topped up "every 5 minutes or so", and
# dryiceinfo.com's 5-10 lb in hot water every fifteen minutes is 2.5-5 g/s
MDOT = 2.5e-3
CO2_PPM = 425.0         # normal outdoor air: NOAA's 2025 global mean, 425.62 ppm
W = dict(O2=31.9988, N2=28.0134, CO2=44.01)
Y_O2_DRY = 0.2314       # oxygen's mass fraction in dry air (argon is lumped into N2)


def ambient():
    """Mass fractions of normal air holding CO2_PPM of CO2 by volume."""
    x_co2 = CO2_PPM * 1e-6
    # O2 and N2 in dry air's mass ratio, CO2 replacing its share by moles
    w_on = 1 / (Y_O2_DRY / W["O2"] + (1 - Y_O2_DRY) / W["N2"])
    w_mix = x_co2 * W["CO2"] + (1 - x_co2) * w_on
    y_co2 = x_co2 * W["CO2"] / w_mix
    y_o2 = (1 - y_co2) * Y_O2_DRY
    return dict(CO2=y_co2, O2=y_o2, N2=1 - y_co2 - y_o2), w_mix


Y_AMB, W_AMB = ambient()

X0 = -WALL_T - OUT_X
# (start, end, cells, last/first cell size)
XS = [(X0, -WALL_T, 16, 0.3), (-WALL_T, 0.0, 3, 1.0), (0.0, 1.0, 25, 1.0),
      (1.0, TABLE["x0"], 28, 1.0), (TABLE["x0"], CAUL["x0"], 2, 1.0), (CAUL["x0"], CAUL["x1"], 12, 1.0),
      (CAUL["x1"], TABLE["x1"], 2, 1.0), (TABLE["x1"], ROOM_X, 45, 1.0)]
YS = [(0.0, 0.2, 12, 2.5), (0.2, TABLE["y0"], 8, 1.0), (TABLE["y0"], TABLE["y1"], 1, 1.0),
      (TABLE["y1"], CAUL["y1"], 10, 1.0), (CAUL["y1"], DOOR_Y1, 24, 1.0), (DOOR_Y1, ROOM_Y, 7, 1.0),
      (ROOM_Y, OUT_YHI, 8, 3.0)]
# raised: YS's bands up to 0.75 m kept as they are, so the floor layer and the nose height are
# meshed as in shut; above them 4 cells to the table, 1 across its top, 10 up the cauldron and
# 15 (55 mm, against shut's 53 mm) to the door's head
YS_RAISED = [(0.0, 0.2, 12, 2.5), (0.2, 0.42, 8, 1.0), (0.42, 0.45, 1, 1.0), (0.45, 0.75, 10, 1.0),
             (0.75, 0.88, 4, 1.0), (0.88, 0.91, 1, 1.0), (0.91, 1.21, 10, 1.0), (1.21, DOOR_Y1, 15, 1.0),
             (DOOR_Y1, ROOM_Y, 7, 1.0), (ROOM_Y, OUT_YHI, 8, 3.0)]
ZS = [(0.0, CAUL["hz"], 6, 1.0), (CAUL["hz"], DOOR_HZ, 9, 1.0), (DOOR_HZ, TABLE["hz"], 1, 1.0),
      (TABLE["hz"], ROOM_HZ, 30, 1.0), (ROOM_HZ, OUT_HZ, 6, 3.0)]

HDR = "FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n"
WALLS = '"(walls|outerWalls|furniture|doorA|doorB)"'


def grading(secs):
    return "(" + " ".join(f"({e - s:g} {n} {r:g})" for s, e, n, r in secs) + ")"


def write(path, cls, obj, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(HDR.format(cls=cls, obj=obj))
        f.write(textwrap.dedent(body).lstrip("\n"))


def block_mesh(case):
    x0, x1 = XS[0][0], XS[-1][1]
    y0, y1 = YS[0][0], YS[-1][1]
    z0, z1 = ZS[0][0], ZS[-1][1]
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
        outside   // the outdoor air's open faces; the parts beyond the room go with subsetMesh
        {{
            type patch;
            faces ((0 4 7 3) (3 7 6 2) (4 5 6 7));
        }}
        symmetry  // z = 0, through the middle of the door and the cauldron
        {{
            type symmetryPlane;
            faces ((0 3 2 1));
        }}
        walls     // the back wall and the floor here; subsetMesh adds every face it exposes
        {{
            type wall;
            faces ((1 2 6 5) (0 1 5 4));
        }}
    );
    """)
    return nx * ny * nz


def topo_dicts(case, run):
    e = 1e-4
    big = 100
    t, c = TABLE, CAUL
    write(f"{case}/system/topoSetDict.keep", "dictionary", "topoSetDict", f"""
    actions
    (
        {{ name keep; type cellSet; action new; source boxToCell; box (-{big} -{big} -{big}) ({big} {big} {big}); }}
        // the front wall, apart from the doorway
        {{ name keep; type cellSet; action subtract; source boxToCell; box (-{WALL_T} -{big} -{big}) (0 {big} {big}); }}
        {{ name keep; type cellSet; action add; source boxToCell; box (-{WALL_T} 0 0) (0 {DOOR_Y1} {DOOR_HZ}); }}
        // beyond the room's ceiling and side wall
        {{ name keep; type cellSet; action subtract; source boxToCell; box (0 {ROOM_Y} -{big}) ({big} {big} {big}); }}
        {{ name keep; type cellSet; action subtract; source boxToCell; box (0 -{big} {ROOM_HZ}) ({big} {big} {big}); }}
        // the coffee table's top and the cauldron
        {{ name keep; type cellSet; action subtract; source boxToCell; box ({t['x0']} {t['y0']} 0) ({t['x1']} {t['y1']} {t['hz']}); }}
        {{ name keep; type cellSet; action subtract; source boxToCell; box ({c['x0']} {c['y0']} 0) ({c['x1']} {c['y1']} {c['hz']}); }}
    );
    """)
    # split the exposed faces: the cauldron's water surface, the ceiling leak, the furniture,
    # and the faces outside the room (the wall's outer face, the reveal, the ground outdoors)
    write(f"{case}/system/topoSetDict.split", "dictionary", "topoSetDict", f"""
    actions
    (
        {{ name waterFaces; type faceSet; action new; source patchToFace; patch walls; }}
        {{ name waterFaces; type faceSet; action subset; source boxToFace; box ({c['x0'] - e} {c['y1'] - e} -{e}) ({c['x1'] + e} {c['y1'] + e} {c['hz'] + e}); }}
        {{ name leakFaces; type faceSet; action new; source patchToFace; patch walls; }}
        {{ name leakFaces; type faceSet; action subset; source boxToFace; box ({LEAK['x0'] + e} {ROOM_Y - e} {LEAK['hz0'] + e}) ({ROOM_X + e} {ROOM_Y + e} {ROOM_HZ + e}); }}
        {{ name furnFaces; type faceSet; action new; source patchToFace; patch walls; }}
        {{ name furnFaces; type faceSet; action subset; source boxToFace; box ({t['x0'] - e} {t['y0'] - e} -{e}) ({t['x1'] + e} {c['y1'] + e} {t['hz'] + e}); }}
        {{ name furnFaces; type faceSet; action subtract; source faceToFace; set waterFaces; }}
        {{ name outerFaces; type faceSet; action new; source patchToFace; patch walls; }}
        {{ name outerFaces; type faceSet; action subset; source boxToFace; box (-{big} -{big} -{big}) (-{e} {big} {big}); }}
    );
    """)
    write(f"{case}/system/createPatchDict", "dictionary", "createPatchDict", """
    pointSync false;
    patches
    (
        { name cauldron;   patchInfo { type patch; } constructFrom set; set waterFaces; }
        { name leak;       patchInfo { type patch; } constructFrom set; set leakFaces; }
        { name furniture;  patchInfo { type wall; }  constructFrom set; set furnFaces; }
        { name outerWalls; patchInfo { type wall; }  constructFrom set; set outerFaces; }
    );
    """)
    if run in ("shut", "raised"):
        # the front door, shut: a baffle across the doorway at the wall's inside face
        write(f"{case}/system/topoSetDict.door", "dictionary", "topoSetDict", f"""
        actions
        (
            {{ name doorFaces; type faceSet; action new; source boxToFace; box (-{e} 0 0) ({e} {DOOR_Y1} {DOOR_HZ}); }}
            {{ name door; type faceZoneSet; action new; source setToFaceZone; faceSet doorFaces; }}
        );
        """)
        write(f"{case}/system/createBafflesDict", "dictionary", "createBafflesDict", """
        internalFacesOnly true;
        baffles
        {
            door
            {
                type        faceZone;
                zoneName    door;
                patches
                {
                    owner     { name doorA; type wall; }
                    neighbour { name doorB; type wall; }
                }
            }
        }
        """)
    write(f"{case}/system/topoSetDict.zones", "dictionary", "topoSetDict", f"""
    actions
    (
        // the room: everything inside the front wall's inside face
        {{ name roomCells; type cellSet; action new; source boxToCell; box (0 -1 -{big}) ({big} {big} {big}); }}
        {{ name room; type cellZoneSet; action new; source setToCellZone; set roomCells; }}
        // the room's air at a toddler's nose height: the two cell layers either side of {NOSE_Y} m
        {{ name noseCells; type cellSet; action new; source boxToCell; box (0 {NOSE_Y - 0.03:g} -{big}) ({big} {NOSE_Y + 0.03:g} {big}); }}
        {{ name nose; type cellZoneSet; action new; source setToCellZone; set noseCells; }}
        // the doorway, in the wall's inside face (in the shut run these faces are the door)
        {{ name doorwayFaces; type faceSet; action new; source boxToFace; box (-{e} 0 0) ({e} {DOOR_Y1} {DOOR_HZ}); }}
        {{ name outdoorCells; type cellSet; action new; source boxToCell; box (-{big} -{big} -{big}) (0 {big} {big}); }}
        {{ name doorway; type faceZoneSet; action new; source setsToFaceZone; faceSet doorwayFaces; cellSet outdoorCells; }}
    );
    """)
    write(f"{case}/system/setFieldsDict", "dictionary", "setFieldsDict", f"""
    defaultFieldValues ( volScalarFieldValue T {TOUT} );
    regions
    (
        // the room at {TAMB - 273.15:g} C; the reveal and outdoors at {TOUT - 273.15:g} C
        boxToCell {{ box (0 -1 -{big}) ({big} {big} {big}); fieldValues ( volScalarFieldValue T {TAMB} ); }}
    );
    """)


def fields(case, run):
    open_bc = "(outside|leak)"
    half = MDOT / 2
    write(f"{case}/0.orig/U", "volVectorField", "U", f"""
    dimensions [0 1 -1 0 0 0 0];
    internalField uniform (0 0 0);
    boundaryField
    {{
        "{open_bc}" {{ type pressureInletOutletVelocity; value uniform (0 0 0); }}
        // the dry ice's CO2 leaving the water: {MDOT * 1e3:g} g/s for the whole cauldron, half of it here
        cauldron {{ type flowRateInletVelocity; massFlowRate constant {half:.6g}; rho rho; rhoInlet 1.90; value uniform (0 0 0); }}
        symmetry {{ type symmetryPlane; }}
        {WALLS} {{ type noSlip; }}
    }}
    """)
    # the open faces and the leak hold the still outdoor air's own pressure face by face
    # (p0 written by hydrostatic_p0.py once the mesh is final), less the dynamic head on inflow
    write(f"{case}/0.orig/p_rgh", "volScalarField", "p_rgh", f"""
    dimensions [1 -1 -2 0 0 0 0];
    internalField uniform 1e5;
    boundaryField
    {{
        outside {{ type prghTotalPressure; rho rho; p0 uniform 1e5; value uniform 1e5; }}
        leak {{ type prghTotalPressure; rho rho; p0 uniform 1e5; value uniform 1e5; }}
        symmetry {{ type symmetryPlane; }}
        "(cauldron|walls|outerWalls|furniture|doorA|doorB)" {{ type fixedFluxPressure; value uniform 1e5; }}
    }}
    """)
    write(f"{case}/0.orig/p", "volScalarField", "p", """
    dimensions [1 -1 -2 0 0 0 0];
    internalField uniform 1e5;
    boundaryField
    {
        symmetry { type symmetryPlane; }
        ".*" { type calculated; value uniform 1e5; }
    }
    """)
    write(f"{case}/0.orig/T", "volScalarField", "T", f"""
    dimensions [0 0 0 1 0 0 0];
    internalField uniform {TAMB};
    boundaryField
    {{
        "{open_bc}" {{ type inletOutlet; inletValue uniform {TOUT}; value uniform {TOUT}; }}
        cauldron {{ type fixedValue; value uniform {T_GAS}; }}
        symmetry {{ type symmetryPlane; }}
        // the room's floor, ceiling and walls hardly cool or warm in ten minutes
        walls {{ type fixedValue; value uniform {TAMB}; }}
        // the wall's outer face, the reveal, the ground outdoors, the furniture and the door
        "(outerWalls|furniture|doorA|doorB)" {{ type zeroGradient; }}
    }}
    """)
    for sp in ("CO2", "O2", "N2"):
        inlet = 1.0 if sp == "CO2" else 0.0
        write(f"{case}/0.orig/{sp}", "volScalarField", sp, f"""
        dimensions [0 0 0 0 0 0 0];
        internalField uniform {Y_AMB[sp]:.12g};
        boundaryField
        {{
            "{open_bc}" {{ type inletOutlet; inletValue uniform {Y_AMB[sp]:.12g}; value uniform {Y_AMB[sp]:.12g}; }}
            cauldron {{ type fixedValue; value uniform {inlet:g}; }}
            symmetry {{ type symmetryPlane; }}
            {WALLS} {{ type zeroGradient; }}
        }}
        """)
    for name, dim, val, wf in (("k", "[0 2 -2 0 0 0 0]", "1e-4", "kLowReWallFunction"),
                               ("omega", "[0 0 -1 0 0 0 0]", "1.0", "omegaWallFunction")):
        write(f"{case}/0.orig/{name}", "volScalarField", name, f"""
        dimensions {dim};
        internalField uniform {val};
        boundaryField
        {{
            "{open_bc}" {{ type inletOutlet; inletValue uniform {val}; value uniform {val}; }}
            cauldron {{ type fixedValue; value uniform {val}; }}
            symmetry {{ type symmetryPlane; }}
            {WALLS} {{ type {wf}; value uniform {val}; }}
        }}
        """)
    write(f"{case}/0.orig/nut", "volScalarField", "nut", f"""
    dimensions [0 2 -1 0 0 0 0];
    internalField uniform 0;
    boundaryField
    {{
        "({open_bc[1:-1]}|cauldron)" {{ type calculated; value uniform 0; }}
        symmetry {{ type symmetryPlane; }}
        {WALLS} {{ type nutkWallFunction; value uniform 0; }}
    }}
    """)
    write(f"{case}/0.orig/alphat", "volScalarField", "alphat", f"""
    dimensions [1 -1 -1 0 0 0 0];
    internalField uniform 0;
    boundaryField
    {{
        "({open_bc[1:-1]}|cauldron)" {{ type calculated; value uniform 0; }}
        symmetry {{ type symmetryPlane; }}
        {WALLS} {{ type compressible::alphatJayatillekeWallFunction; Prt 0.85; value uniform 0; }}
    }}
    """)


THERMO = {
    "O2": ("( 3.69758 0.00061352 -1.25884e-07 1.77528e-11 -1.13644e-15 -1233.93 3.18917 )",
           "( 3.21294 0.00112749 -5.75615e-07 1.31388e-09 -8.76855e-13 -1005.25 6.03474 )", "O 2;"),
    "N2": ("( 2.92664 0.00148798 -5.68476e-07 1.0097e-10 -6.75335e-15 -922.798 5.98053 )",
           "( 3.29868 0.00140824 -3.96322e-06 5.64152e-09 -2.44486e-12 -1020.9 3.95037 )", "N 2;"),
    "CO2": ("( 4.45362 0.00314017 -1.27841e-06 2.394e-10 -1.66903e-14 -48967 -0.955396 )",
            "( 2.27572 0.00992207 -1.04091e-05 6.86669e-09 -2.11728e-12 -48373.1 10.1885 )", "C 1; O 2;"),
}


def constant(case):
    write(f"{case}/constant/g", "uniformDimensionedVectorField", "g", """
    dimensions [0 1 -2 0 0 0 0];
    value (0 -9.81 0);
    """)
    write(f"{case}/constant/thermophysicalProperties", "dictionary", "thermophysicalProperties", """
    // O2, N2 and CO2 as perfect gases with JANAF thermodynamics and Sutherland viscosity (the
    // coefficients of the v2512 tutorials' thermo.compressibleGas); no reactions
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
    write(f"{case}/constant/reactions", "dictionary", "reactions", """
    species ( O2 N2 CO2 );
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
    write(f"{case}/constant/thermo.compressibleGas", "dictionary", "thermo.compressibleGas", body)
    write(f"{case}/constant/combustionProperties", "dictionary", "combustionProperties", """
    combustionModel none;
    """)
    write(f"{case}/constant/chemistryProperties", "dictionary", "chemistryProperties", """
    chemistryType { solver none; }
    chemistry off;
    initialChemicalTimeStep 1;
    """)
    write(f"{case}/constant/turbulenceProperties", "dictionary", "turbulenceProperties", """
    simulationType  RAS;
    RAS { RASModel kOmegaSST; turbulence on; printCoeffs on; }
    """)
    write(f"{case}/constant/fvOptions", "dictionary", "fvOptions", """
    // buoyancy's production and damping of turbulence, as in windowAiring
    buoyancyTurb { type buoyancyTurbSource; selectionMode all; }
    """)


def system(case, run, tend, write_int, nprocs, field_int):
    write(f"{case}/system/controlDict", "dictionary", "controlDict", f"""
    // dryIceCauldron, run {run}
    application     rhoReactingBuoyantFoam;
    startFrom       latestTime;
    startTime       0;
    stopAt          endTime;
    endTime         {tend};
    deltaT          0.002;
    adjustTimeStep  yes;
    maxCo           1;
    maxDeltaT       0.1;
    // full fields every {field_int} s, the last two kept, to continue an interrupted solve;
    // the clip is the planes, written every {write_int} s by the function objects below
    writeControl    adjustableRunTime;
    writeInterval   {field_int};
    purgeWrite      2;
    writeFormat     binary;
    writePrecision  8;
    writeCompression off;
    timeFormat      general;
    timePrecision   8;
    runTimeModifiable true;

    functions
    {{
        #include "functions"
    }}
    """)
    write(f"{case}/system/functions", "dictionary", "functions", f"""
    // ---- every time step: the CO2 in the room and what crosses the doorway ------------
    // the room's CO2 mass, kg (half the room)
    roomCO2
    {{
        type            volFieldValue;
        libs            (fieldFunctionObjects);
        regionType      cellZone;
        name            room;
        operation       weightedVolIntegrate;
        weightField     rho;
        fields          (CO2);
        writeFields     false;
        writeControl    timeStep;
        log             false;
    }}
    // the CO2's mass fraction at a toddler's nose height, volume-averaged over the room
    noseCO2
    {{
        type            volFieldValue;
        libs            (fieldFunctionObjects);
        regionType      cellZone;
        name            nose;
        operation       volAverage;
        fields          (CO2 T);
        writeFields     false;
        writeControl    timeStep;
        log             false;
    }}
    noseCO2max
    {{
        $noseCO2;
        operation       max;
        fields          (CO2);
    }}
    // gross mass flow each way through the doorway, kg/s: in = into the room (+x)
    doorIn
    {{
        type            surfaceFieldValue;
        libs            (fieldFunctionObjects);
        regionType      faceZone;
        name            doorway;
        operation       sumDirection;
        direction       (1 0 0);
        fields          (phi);
        writeFields     false;
        writeControl    timeStep;
        log             false;
    }}
    doorOut
    {{
        $doorIn;
        direction       (-1 0 0);
    }}
    // net CO2 mass flow through the doorway (+ into the room), kg/s
    doorCO2
    {{
        type            surfaceFieldValue;
        libs            (fieldFunctionObjects);
        regionType      faceZone;
        name            doorway;
        operation       weightedSum;
        weightField     phi;
        fields          (CO2);
        writeFields     false;
        writeControl    timeStep;
        log             false;
    }}
    // what the cauldron and the leak pass, kg/s (outward normal: negative = into the room)
    inflow
    {{
        type            surfaceFieldValue;
        libs            (fieldFunctionObjects);
        regionType      patch;
        name            cauldron;
        operation       sum;
        fields          (phi);
        writeFields     false;
        writeControl    timeStep;
        log             false;
    }}
    inflowCO2
    {{
        $inflow;
        operation       weightedSum;
        weightField     phi;
        fields          (CO2);
    }}
    leakFlow
    {{
        $inflow;
        name            leak;
    }}
    leakCO2
    {{
        $inflowCO2;
        name            leak;
    }}
    minMax
    {{
        type            fieldMinMax;
        libs            (fieldFunctionObjects);
        fields          (T CO2 U);
        writeControl    adjustableRunTime;
        writeInterval   {write_int};
        log             false;
    }}
    probes
    {{
        type            probes;
        libs            (sampling);
        fields          (T U CO2);
        writeControl    adjustableRunTime;
        writeInterval   {write_int};
        probeLocations
        (
            // at a toddler's nose height: by the table, mid-room, by the door, at the back
            (2.0 {NOSE_Y} 0.01) (1.5 {NOSE_Y} 1.0) (0.5 {NOSE_Y} 0.01) (4.5 {NOSE_Y} 1.5)
            // ankle height and the ceiling
            (2.0 0.1 0.01) (0.5 0.1 0.01) (4.5 0.1 1.5) (2.5 2.3 0.01)
        );
    }}

    // ---- the clip: the section through the door and the cauldron, the floor, the nose
    // height. No bounds on any plane: in an earlier case a plane with a thin bounds box wrote nothing.
    planes
    {{
        type            surfaces;
        libs            (sampling);
        writeControl    adjustableRunTime;
        writeInterval   {write_int};
        surfaceFormat   vtk;
        formatOptions   {{ vtk {{ format binary; }} }}
        interpolate     false;
        fields          (T U CO2 O2);
        surfaces
        {{
            mid     {{ type cuttingPlane; point (0 1.2 0.005); normal (0 0 1); interpolate false; }}
            nose    {{ type cuttingPlane; point (2 {NOSE_Y} 0); normal (0 1 0); interpolate false; }}
            ankle   {{ type cuttingPlane; point (2 0.1 0); normal (0 1 0); interpolate false; }}
        }}
    }}
    """)
    # the planes at t = 0 from the initial fields, which the solver does not write:
    # postProcess -dict system/planesT0 -fields '(T U CO2 O2)' -time 0
    fo = open(f"{case}/system/functions").read()
    with open(f"{case}/system/planesT0", "w") as f:
        f.write(HDR.format(cls="dictionary", obj="planesT0"))
        f.write("functions {\n" + fo[fo.index("\nplanes\n") + 1:] + "}\n")
    species = "\n".join(f"            {sp} limitedLinear01 1;" for sp in W)
    write(f"{case}/system/fvSchemes", "dictionary", "fvSchemes", f"""
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
        div(phi,K)      Gauss linear;
        turbulence      Gauss limitedLinear 1;
        div(phi,k)      $turbulence;
        div(phi,omega)  $turbulence;
        div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
    }}
    laplacianSchemes    {{ default Gauss linear corrected; }}
    interpolationSchemes{{ default linear; }}
    snGradSchemes       {{ default corrected; }}
    wallDist            {{ method meshWave; }}
    // the solver takes p_rgh's flux and does not register it itself
    fluxRequired        {{ default no; p_rgh; }}
    """)
    write(f"{case}/system/fvSolution", "dictionary", "fvSolution", """
    solvers
    {
        "rho.*"     { solver PCG; preconditioner DIC; tolerance 0; relTol 0; }
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
    write(f"{case}/system/decomposeParDict", "dictionary", "decomposeParDict", f"""
    numberOfSubdomains {nprocs};
    method scotch;
    """)


ALLRUN = """#!/bin/bash
# Mesh, set up and decompose this run; ./Allrun solve then runs it on NPROCS ranks.
cd "${0%/*}" || exit 1
. "$WM_PROJECT_DIR/bin/tools/RunFunctions"
set -e
if [ "$1" != solve ]; then
    runApplication blockMesh
    runApplication -s keep topoSet -dict system/topoSetDict.keep
    runApplication subsetMesh keep -patch walls -overwrite
    runApplication -s split topoSet -dict system/topoSetDict.split
    runApplication createPatch -overwrite
DOOR    runApplication -s zones topoSet -dict system/topoSetDict.zones
    rm -rf 0 && cp -r 0.orig 0
    runApplication setFields
    runApplication postProcess -func writeCellCentres -time 0
    python3 hydrostatic.py > log.hydrostatic 2>&1
    rm -f 0/C 0/Cx 0/Cy 0/Cz
    runApplication checkMesh -constant
    runApplication decomposePar
    exit 0
fi
runParallel -n NPROCS rhoReactingBuoyantFoam
"""

ALLRUN_DOOR = """    runApplication -s door topoSet -dict system/topoSetDict.door
    runApplication createBaffles -overwrite
"""

HYDROSTATIC = '''#!/usr/bin/env python3
"""Start every cell and open face from hydrostatic rest.

p0 on the `outside` and `leak` patches of 0/p_rgh: the pressure of still outdoor air at TOUT K
at each face's height y, the isothermal barometric p0 = 1e5 exp(-g y/(R TOUT)), from
dp/dy = -rho g with rho = p/(R T). The cells' p in 0/p: the same formula with each cell's own
temperature from 0/T (the solver sets p_rgh = p - rho g.x from p at start-up). The first build
used 1e5/(1 + g y/(R T)), which makes p_rgh uniform but is not rest for a compressible gas: its
still outdoor air sank at 0.06 m/s (README, "How the case got here"). Heights from 0/Cy, which
`postProcess -func writeCellCentres` writes in the case's format, binary or ascii. The gas
constant is normal air's, R = 8314.47/W_AMB."""
import math
import re
import struct

G, R, TO = 9.81, 8314.47 / W_AMB, TOUT


def read_list(raw, start, kind="scalar"):
    m = re.compile(rb"nonuniform\\s+List<scalar>\\s*(\\d+)\\s*\\(").search(raw, start)
    n = int(m.group(1))
    if re.search(rb"format\\s+(\\w+);", raw).group(1) == b"binary":
        v = struct.unpack(f"<{n}d", raw[m.end():m.end() + 8 * n])
    else:
        v = [float(x) for x in raw[m.end():raw.index(b")", m.end())].split()]
    assert len(v) == n
    return list(v)


def patch_list(raw, patch):
    """A patch's face values; a patch of one face is written as `value uniform <y>`."""
    i = raw.index(b"boundaryField")
    i = re.compile(rb"\\n\\s*" + patch.encode() + rb"\\s*\\n\\s*\\{").search(raw, i).end()
    j = raw.index(b"value", i)
    m = re.compile(rb"value\\s+uniform\\s+([-+.\\deE]+)\\s*;").match(raw, j)
    if m:
        return [float(m.group(1))]
    return read_list(raw, j)


cy = open("0/Cy", "rb").read()
src = open("0/p_rgh").read()
for patch in ("outside", "leak"):
    y = patch_list(cy, patch)
    p0 = " ".join("%.10g" % (1e5 * math.exp(-G * yy / (R * TO))) for yy in y)
    old = patch + " { type prghTotalPressure; rho rho; p0 uniform 1e5;"
    assert src.count(old) == 1
    src = src.replace(old, f"{patch} {{ type prghTotalPressure; rho rho; p0 nonuniform List<scalar> {len(y)} ({p0});")
    print(f"{patch}: {len(y)} faces, y {min(y):.3f} to {max(y):.3f} m")
open("0/p_rgh", "w").write(src)

yc = read_list(cy, cy.index(b"internalField"))
traw = open("0/T", "rb").read()
tc = read_list(traw, traw.index(b"internalField"))
assert len(tc) == len(yc)
p = [1e5 * math.exp(-G * yy / (R * tt)) for yy, tt in zip(yc, tc)]
psrc = open("0/p").read()
old = "internalField uniform 1e5;"
assert psrc.count(old) == 1
psrc = psrc.replace(old, "internalField nonuniform List<scalar> %d\\n(\\n%s\\n)\\n;" % (len(p), "\\n".join("%.10g" % v for v in p)))
open("0/p", "w").write(psrc)
print(f"cells: {len(p)}, p {min(p):.3f} to {max(p):.3f} Pa")
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", choices=["shut", "open", "raised"])
    ap.add_argument("dir")
    ap.add_argument("--tend", type=float, default=600)
    ap.add_argument("--write", type=float, default=1.25)
    ap.add_argument("--fields", type=float, default=50)
    ap.add_argument("--nprocs", type=int, default=8)
    a = ap.parse_args()
    global TABLE, CAUL, YS
    if a.run == "raised":
        TABLE, CAUL, YS = TABLE_RAISED, CAUL_RAISED, YS_RAISED
    case = a.dir
    n = block_mesh(case)
    topo_dicts(case, a.run)
    fields(case, a.run)
    constant(case)
    system(case, a.run, f"{a.tend:g}", f"{a.write:g}", a.nprocs, f"{a.fields:g}")
    allrun = ALLRUN.replace("NPROCS", str(a.nprocs))
    allrun = allrun.replace("DOOR", ALLRUN_DOOR if a.run != "open" else "")
    with open(f"{case}/Allrun", "w") as f:
        f.write(allrun)
    os.chmod(f"{case}/Allrun", 0o755)
    with open(f"{case}/hydrostatic.py", "w") as f:
        f.write(HYDROSTATIC.replace("W_AMB", f"{W_AMB:.6f}").replace("TOUT", f"{TOUT}"))
    print(f"{a.run}: {case}, background box {n} cells; normal air Y_CO2 {Y_AMB['CO2']:.4e}, "
          f"W {W_AMB:.4f}; cauldron {MDOT * 1e3:g} g/s")


if __name__ == "__main__":
    main()
