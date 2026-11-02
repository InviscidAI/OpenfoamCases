#!/usr/bin/env python3
"""Write the mesh case both runs share: underfloorVsRadiator's room, unchanged.

    python3 scripts/make_mesh.py <meshDir>

writes <meshDir>/system/blockMeshDict, topoSetDict.glass, createPatchDict and
topoSetDict.zones, and a controlDict, fvSchemes and fvSolution for the mesh tools. Allrun then
runs blockMesh, cuts the glass out of the window wall (topoSet, createPatch), makes the
occupied zone's four bands (topoSet) and runs checkMesh there; scripts/make_case.py copies the
polyMesh and these four dictionaries into each run.

The room is underfloorVsRadiator's (windowAiring's room with its window shut): x from the
window wall into the room (4.0 m), y up from the floor (2.4 m), z across the room (3.5 m)
with z = 0 through the middle of the window. One graded block of 66 x 83 x 68 = 372,504 cells:
20 mm across the first 0.3 m from the window wall, 10 mm at the floor, 30 mm over the window
band and under the ceiling, 20 mm at the window's side edges. The glass, 1.0 m wide and 1.2 m
tall from a 0.90 m sill, is cut out of the window wall by position (1,120 faces, 1.20 m2).
The bands are the cells whose centres lie within 0.02 m of 0.1, 0.6, 1.1 and 1.7 m and in
ASHRAE 55's occupied zone, more than 1.0 m from the window wall and 0.3 m from the others.

These are the functions of underfloorVsRadiator's scripts/make_case.py, without its radiator,
and they write the solved runs' dictionaries byte for byte.
"""
import os
import sys
import textwrap
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / "template"

ROOM_X = 4.0            # window wall to inner wall
ROOM_Y = 2.4            # floor to ceiling
ROOM_HZ = 1.75          # half the room's width: 3.5 m
WIN_Y0, WIN_Y1 = 0.90, 2.10   # the glass: sill 0.90 m, 1.2 m tall
WIN_HZ = 0.50           # 1.0 m wide

# occupied zone (ASHRAE 55): more than 1.0 m from the window wall, 0.3 m from the other walls
OCC = dict(x0=1.0, x1=ROOM_X - 0.3, hz=ROOM_HZ - 0.3)
OCC_HEIGHTS = (("ankle", 0.1), ("knee", 0.6), ("head", 1.1), ("standing", 1.7))
BAND = 0.02             # half-height of each band of cells

# (start, end, cells, last/first cell) along x, y and z
XS = [(0.0, 0.3, 15, 1.0), (0.3, 1.0, 16, 3.5), (1.0, 3.8, 31, 1.0), (3.8, ROOM_X, 4, 0.375)]
YS = [(0.0, 0.15, 8, 3.0), (0.15, 0.75, 20, 1.0), (0.75, WIN_Y0, 5, 1.0),
      (WIN_Y0, WIN_Y1, 40, 1.0), (WIN_Y1, ROOM_Y, 10, 1.0)]
ZS = [(-ROOM_HZ, -WIN_HZ, 20, 0.2), (-WIN_HZ, 0.0, 14, 2.5), (0.0, WIN_HZ, 14, 0.4),
      (WIN_HZ, ROOM_HZ, 20, 5.0)]

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
    return nx, ny, nz


def topo_dicts(case):
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


def tools(case):
    # the mesh tools need a controlDict; binary at 8 digits, as the solved runs wrote their mesh
    write(f"{case}/system/controlDict", "dictionary", "controlDict", """
    application     blockMesh;
    startFrom       startTime;
    startTime       0;
    stopAt          endTime;
    endTime         1200;
    deltaT          0.005;
    writeControl    timeStep;
    writeInterval   1;
    writeFormat     binary;
    writePrecision  8;
    writeCompression off;
    timeFormat      general;
    timePrecision   8;
    runTimeModifiable false;
    """)
    for name in ("fvSchemes", "fvSolution"):
        (Path(case) / "system" / name).write_text((TEMPLATE / "system" / name).read_text())


def main(case):
    nx, ny, nz = block_mesh(case)
    topo_dicts(case)
    tools(case)
    print(f"{case}: {nx} x {ny} x {nz} = {nx * ny * nz} cells")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
