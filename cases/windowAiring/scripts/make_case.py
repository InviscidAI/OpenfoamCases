#!/usr/bin/env python3
"""Write one run of windowAiring: a heated room aired through the window above its radiator.

    python3 make_case.py <run> <dir> [--tend 300] [--write 0.625] [--fields 25] [--nprocs 7]
                         [--outdoor hydrostatic|fixed]

run is `open` (the sash turned wide open, standing at 90 degrees on its hinge side) or
`tilted` (the sash on tilt, hinged at the bottom, a solid profile SASH_D deep whose top has
moved TILT_TOP into the room). The two runs differ only in the sash; everything else is
written identically.

Coordinates follow ../radiatorUnderWindow: x from the inside
face of the window wall into the room, y up from the floor, and z across the room, with
z = 0 through the middle of the window. radiatorUnderWindow's section is the plane z = 0.

The mesh is one graded blockMesh box over the outdoor air, the window wall and the room.
The cells that are not air (the wall around the opening, and everything beyond the room's
floor, ceiling and side walls) are removed with subsetMesh. The wide-open sash is a
zero-thickness baffle; the tilted sash is removed with the wall, as a solid profile, because
its depth is what closes most of the tilted window's side gaps (README, "The tilted sash").
The Allrun written into the run directory does the rest; ../Allrun drives it.

`tilted-thin` and `--outdoor fixed` rebuild the superseded first build (README, "How the
case got here"); the solved runs are `open` and `tilted` with the default hydrostatic boundary.

`doubleHungTop` and `doubleHungSplit` put a US double-hung window (README, "A US double-hung
window") in the same room, wall and radiator: two solid sashes, each 40 mm deep in its own
track, the top sash lowered 10 cm, or the top sash lowered 5 cm and the bottom one raised 5 cm.
They are written with the barometric outdoor boundary (`--outdoor barometric`, forced), a
uniform 10 mm band over the window's height and the per-step budget monitor; README, "The
double-hung runs' model", says what that changes against `open` and `tilted`.
"""
import argparse
import os
import textwrap

# ---------------------------------------------------------------- geometry (m)
ROOM_X = 4.0            # window wall to inner wall (radiatorUnderWindow)
ROOM_Y = 2.4            # floor to ceiling (radiatorUnderWindow)
ROOM_HZ = 1.75          # half the room's width: 3.5 m (this case's)
WALL_T = 0.24           # window wall thickness (this case's); the frame is at its inside face
WIN_Y0, WIN_Y1 = 0.90, 2.10   # radiatorUnderWindow's glass: sill 0.90 m, 1.2 m tall
WIN_HZ = 0.50           # 1.0 m wide, the radiator's length (Stelrad K1 600 x 1000)
# The tilted sash (README, "The tilted sash"): a solid profile
# across the clear opening, SASH_D deep, of which SASH_IN sits behind the frame's room face
# (x = 0) when shut, in the frame's rebate. On tilt it turns about its bottom edge, so a point
# a height y' up the sash moves TILT_TOP y'/h into the room. The side gaps open only where
# the sash's outer face has left the frame (TILT_TOP y'/h > SASH_IN), and the top gap is the
# frame-to-sash distance TILT_TOP - SASH_IN. The rebate clearance (Falzluft, about 12 mm)
# is below the 20 mm cells and is left shut.
# TILT_TOP: the standard tilt width of Roto NT (140 mm, every scissor size) and Winkhaus
# activPilot (scissor size 2, "Kippöffnungsweite 140 mm"). That width is the sash's swing at
# the top, not the clear gap: Maas, Schmidt and Hauser (wksb 42/98, Tabelle 2) measured a
# clear opening s = 10.4 cm on a 1.21 m sash whose fitting swung it a = 15.5 cm (7.30 deg),
# and 8.9 cm for 13.5 cm, about two thirds. SASH_IN = 50 mm leaves 90 mm clear at the top
# here, two thirds of 140 mm. SASH_D: profile depths of 70-85 mm (VEKA Softline 82,
# aluplast Ideal 4000 70/85), the sash standing 30 mm proud of the frame (Winkhaus's 20 mm
# overlap and its seal).
TILT_TOP = 0.140
SASH_IN = 0.050
SASH_D = 0.080
# the first build's tilted sash (run `tilted-thin`, superseded): a zero-thickness plate whose
# top stood 0.14 m from the frame, with the side triangles open from the hinge up
TILT_GAP = 0.14
RAD = dict(x0=0.040, x1=0.123, y0=0.15, y1=0.75)   # radiatorUnderWindow's radiator box
OUT_X = 1.50            # outdoor air beyond the wall's outer face
OUT_YLO, OUT_YHI = -1.0, 3.4
OUT_HZ = 2.5

TAMB, TOUT = 293.15, 273.15
RAD_W = 60.0            # radiatorUnderWindow's 60 W/m over the radiator's 1.0 m length

X0 = -WALL_T - OUT_X
# (start, end, cells, last/first cell size)
# 20 mm across the reveal and the first 0.3 m of the room (the wedge behind the tilted sash,
# the radiator, the inflow): a first pilot at 12.5 mm took the open run's step down to 0.011 s
# at Courant 1, about 9.5 h for 300 s on 7 ranks. The band under the ceiling is a uniform
# 30 mm, not graded to 13 mm: the grading runs outdoors too, where the warm air leaving the
# window rises up the facade at about 1 m/s, and set the step there (second pilot, 0.0104 s)
XS = [(X0, -WALL_T, 18, 0.1), (-WALL_T, 0.0, 12, 1.0), (0.0, 0.3, 15, 1.0),
      (0.3, 1.0, 16, 3.5), (1.0, 3.8, 31, 1.0), (3.8, ROOM_X, 4, 0.375)]
YS = [(OUT_YLO, 0.0, 10, 0.15), (0.0, 0.15, 8, 3.0), (0.15, 0.75, 20, 1.0),
      (0.75, WIN_Y0, 5, 1.0), (WIN_Y0, WIN_Y1, 40, 1.0), (WIN_Y1, ROOM_Y, 10, 1.0),
      (ROOM_Y, OUT_YHI, 10, 6.67)]
ZS = [(-OUT_HZ, -ROOM_HZ, 4, 0.4), (-ROOM_HZ, -WIN_HZ, 20, 0.2), (-WIN_HZ, 0.0, 14, 2.5),
      (0.0, WIN_HZ, 14, 0.4), (WIN_HZ, ROOM_HZ, 20, 5.0), (ROOM_HZ, OUT_HZ, 4, 2.5)]

# ---------------------------------------------------------------- the double-hung window
# Andersen 400 Series Tilt-Wash TW3042 (README, "A US double-hung window"): a clear opening
# 0.86 m wide (the table's 862 mm) and 1.24 m tall from a 0.95 m sill (the 1343 mm frame less a
# 47 mm head and sill, on this room's 0.90 m sill). Two sashes 0.65 m tall (the lower sash's
# 557 mm of glass plus its 97 mm of rails; the upper taken as tall), each DH_SASH_D deep: the upper in the
# outer track, x -0.08 to -0.04, the lower in the inner, x -0.04 to 0, at the wall's inside face.
# Shut, they overlap 0.06 m at the meeting rails.
DH_WIN = dict(y0=0.95, y1=2.19, hz=0.43)
DH_SASH_H = 0.65
DH_SASH_D = 0.04
# (upper sash's bottom, lower sash's bottom), m: the top sash lowered 10 cm, or the 10 cm split
DH_RUNS = {"doubleHungTop": (1.44, 0.95), "doubleHungSplit": (1.49, 1.00)}
# a uniform 10 mm band from 0.90 to 2.24 m, indoors and out, for the 5 cm slots; the rest of YS
# as above, with 8 cells graded 3:1 to the ceiling
DH_YS = [(OUT_YLO, 0.0, 10, 0.15), (0.0, 0.15, 8, 3.0), (0.15, 0.75, 20, 1.0),
         (0.75, 0.90, 5, 1.0), (0.90, 2.24, 134, 1.0), (2.24, ROOM_Y, 8, 3.0),
         (ROOM_Y, OUT_YHI, 10, 6.67)]
# ZS's breaks, counts and size progression, each 14-cell half-window section split 3 + 11 so
# that a cell face falls on the narrower window's edges, +-0.43 m
_q = 2.5 ** (1 / 13)
DH_ZS = [(-OUT_HZ, -ROOM_HZ, 4, 0.4), (-ROOM_HZ, -0.5, 20, 0.2), (-0.5, -0.43, 3, _q ** 2),
         (-0.43, 0.0, 11, _q ** 10), (0.0, 0.43, 11, _q ** -10), (0.43, 0.5, 3, _q ** -2),
         (0.5, ROOM_HZ, 20, 5.0), (ROOM_HZ, OUT_HZ, 4, 2.5)]

HDR = "FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n"


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


def topo_dicts(case, run):
    e = 1e-4
    big = 100
    h = WIN_Y1 - WIN_Y0
    solid_sash = sash_split = ""
    if run == "tilted":
        # the sash's cells: a box sheared with the tilt (right-handed axes: i x j along +k)
        solid_sash = (f"\n        // the tilted sash, a solid profile\n"
                      f"        {{ name keep; type cellSet; action subtract; source rotatedBoxToCell; "
                      f"origin (-{SASH_IN} {WIN_Y0} -{WIN_HZ}); i ({SASH_D} 0 0); j ({TILT_TOP} {h:g} 0); "
                      f"k (0 0 {2 * WIN_HZ}); }}")
        # its exposed faces: those in the room (x > 0) within the sash's height and width, and
        # those inside the reveal, away from the reveal's own faces
        sash_split = f"""
        {{ name sashFaces; type faceSet; action new; source patchToFace; patch walls; }}
        {{ name sashFaces; type faceSet; action subset; source boxToFace; box ({e} {WIN_Y0 - e:g} -{WIN_HZ + e:g}) ({TILT_TOP + SASH_D + 0.05:g} {WIN_Y1 + e:g} {WIN_HZ + e:g}); }}
        {{ name sashFacesR; type faceSet; action new; source patchToFace; patch walls; }}
        {{ name sashFacesR; type faceSet; action subset; source boxToFace; box (-{WALL_T - e:g} {WIN_Y0 + e:g} -{WIN_HZ - e:g}) ({e} {WIN_Y1 - e:g} {WIN_HZ - e:g}); }}
        {{ name sashFaces; type faceSet; action add; source faceToFace; set sashFacesR; }}
        {{ name outerFaces; type faceSet; action subtract; source faceToFace; set sashFaces; }}"""
    # cells kept: everything, less the wall around the opening and the space outside the room
    write(f"{case}/system/topoSetDict.keep", "dictionary", "topoSetDict", f"""
    actions
    (
        {{ name keep; type cellSet; action new; source boxToCell; box (-{big} -{big} -{big}) ({big} {big} {big}); }}
        // the wall slab, apart from the opening
        {{ name keep; type cellSet; action subtract; source boxToCell; box (-{WALL_T} -{big} -{big}) (0 {WIN_Y0} {big}); }}
        {{ name keep; type cellSet; action subtract; source boxToCell; box (-{WALL_T} {WIN_Y1} -{big}) (0 {big} {big}); }}
        {{ name keep; type cellSet; action subtract; source boxToCell; box (-{WALL_T} -{big} -{big}) (0 {big} -{WIN_HZ}); }}
        {{ name keep; type cellSet; action subtract; source boxToCell; box (-{WALL_T} -{big} {WIN_HZ}) (0 {big} {big}); }}
        // beyond the room's floor, ceiling and side walls
        {{ name keep; type cellSet; action subtract; source boxToCell; box (0 -{big} -{big}) ({big} 0 {big}); }}
        {{ name keep; type cellSet; action subtract; source boxToCell; box (0 {ROOM_Y} -{big}) ({big} {big} {big}); }}
        {{ name keep; type cellSet; action subtract; source boxToCell; box (0 -{big} -{big}) ({big} {big} -{ROOM_HZ}); }}
        {{ name keep; type cellSet; action subtract; source boxToCell; box (0 -{big} {ROOM_HZ}) ({big} {big} {big}); }}{solid_sash}
    );
    """)
    # the exposed faces outside the room (the wall's outer face and the reveal) -> outerWalls
    write(f"{case}/system/topoSetDict.split", "dictionary", "topoSetDict", f"""
    actions
    (
        {{ name outerFaces; type faceSet; action new; source patchToFace; patch walls; }}
        {{ name outerFaces; type faceSet; action subset; source boxToFace; box (-{big} -{big} -{big}) (-{e} {big} {big}); }}{sash_split}
    );
    """)
    sash_patch = ""
    if run == "tilted":
        sash_patch = """
        {
            name sash;
            patchInfo { type wall; }
            constructFrom set;
            set sashFaces;
        }"""
    write(f"{case}/system/createPatchDict", "dictionary", "createPatchDict", """
    pointSync false;
    patches
    (
        {
            name outerWalls;
            patchInfo { type wall; }
            constructFrom set;
            set outerFaces;
        }%s
    );
    """ % sash_patch)

    # the sash as a baffle: wide open, and the first build's thin tilted sash (the solid tilted
    # sash went with the wall, above)
    if run == "tilted-thin":
        # Hinged along the bottom of the opening (x = 0, y = WIN_Y0), its top TILT_GAP into
        # the room. A = the cells between the frame's plane and the sash (and the reveal and
        # outdoor cells behind it), B = the room's cells in front of it, both within the
        # sash's height and width. The faces between A and B are the sash: a staircase that
        # follows the line x = TILT_GAP (y - WIN_Y0)/(WIN_Y1 - WIN_Y0). Nothing closes the
        # top gap or the two side triangles. (A's box runs from 1 m behind the sash to the
        # sash; its axes must be right-handed, or rotatedBoxToCell selects nothing.)
        sash = f"""
        {{ name sashA; type cellSet; action new; source rotatedBoxToCell;
           origin (-1 {WIN_Y0} -{WIN_HZ}); i (1 0 0); j ({TILT_GAP} {h} 0); k (0 0 {2 * WIN_HZ}); }}
        {{ name sashB; type cellSet; action new; source rotatedBoxToCell;
           origin (0 {WIN_Y0} -{WIN_HZ}); i (1 0 0); j ({TILT_GAP} {h} 0); k (0 0 {2 * WIN_HZ}); }}
        // a cell centred exactly on the sash's line falls in both boxes and would be sealed
        // off; keep it on the room's side
        {{ name sashB; type cellSet; action subtract; source cellToCell; set sashA; }}
        {{ name sashFaces; type faceSet; action new; source cellToFace; set sashA; option all; }}
        {{ name sashBFaces; type faceSet; action new; source cellToFace; set sashB; option all; }}
        {{ name sashFaces; type faceSet; action subset; source faceToFace; set sashBFaces; }}
        """
    elif run == "open":
        # Turned wide open: the sash stands at 90 degrees to the wall on its hinge side,
        # a plate in the plane z = +WIN_HZ from the frame 1.0 m into the room.
        sash = f"""
        {{ name sashFaces; type faceSet; action new; source boxToFace;
           box (0 {WIN_Y0} {WIN_HZ - e}) ({2 * WIN_HZ} {WIN_Y1} {WIN_HZ + e}); }}
        """
    if run != "tilted":
        baffle_dicts(case, sash)
    zone_dicts(case, run, e, big, h)


def baffle_dicts(case, sash):
    write(f"{case}/system/topoSetDict.sash", "dictionary", "topoSetDict", f"""
    actions
    (
        {sash}
        {{ name sash; type faceZoneSet; action new; source setToFaceZone; faceSet sashFaces; }}
    );
    """)
    write(f"{case}/system/createBafflesDict", "dictionary", "createBafflesDict", """
    internalFacesOnly true;
    baffles
    {
        sash
        {
            type        faceZone;
            zoneName    sash;
            patches
            {
                owner     { name sashA; type wall; }
                neighbour { name sashB; type wall; }
            }
        }
    }
    """)


def zone_dicts(case, run, e, big, h):
    room_minus_wedge = gaps = ""
    if run == "tilted-thin":
        # createBaffles removes the sets, so the wedge is selected again
        room_minus_wedge = (f"{{ name roomCells; type cellSet; action subtract; source rotatedBoxToCell; "
                            f"origin (-1 {WIN_Y0} -{WIN_HZ}); i (1 0 0); j ({TILT_GAP} {h} 0); k (0 0 {2 * WIN_HZ}); }}")
    if run == "tilted":
        # the wedge between the frame's plane and the sash's outer face is outdoors' side
        room_minus_wedge = (f"{{ name roomCells; type cellSet; action subtract; source rotatedBoxToCell; "
                            f"origin (-{1 + SASH_IN} {WIN_Y0} -{WIN_HZ}); i (1 0 0); j ({TILT_TOP} {h:g} 0); k (0 0 {2 * WIN_HZ}); }}")
        # the tilted window's three gaps: the faces between the wedge (x > 0, behind the
        # sash's outer face) and the room, at the top and at each side
        gaps = f"""
        {{ name wedgeCells; type cellSet; action new; source rotatedBoxToCell;
           origin (-{1 + SASH_IN} {WIN_Y0} -{WIN_HZ}); i (1 0 0); j ({TILT_TOP} {h:g} 0); k (0 0 {2 * WIN_HZ}); }}
        {{ name wedgeCells; type cellSet; action subset; source boxToCell; box (0 -1 -{big}) ({big} {big} {big}); }}
        {{ name wedgeFaces; type faceSet; action new; source cellToFace; set wedgeCells; option all; }}
        {{ name roomFaces; type faceSet; action new; source cellToFace; set roomCells; option all; }}
        {{ name wedgeFaces; type faceSet; action subset; source faceToFace; set roomFaces; }}"""
        for zone, box in (("gapTop", f"(-{e} {WIN_Y1 - 0.05:g} -{WIN_HZ - e:g}) (1 {big} {WIN_HZ - e:g})"),
                          ("gapLeft", f"(-{e} 0 -{WIN_HZ + e:g}) (1 {big} -{WIN_HZ - e:g})"),
                          ("gapRight", f"(-{e} 0 {WIN_HZ - e:g}) (1 {big} {WIN_HZ + e:g})")):
            gaps += f"""
        {{ name {zone}Faces; type faceSet; action new; source faceToFace; set wedgeFaces; }}
        {{ name {zone}Faces; type faceSet; action subset; source boxToFace; box {box}; }}
        {{ name {zone}; type faceZoneSet; action new; source setsToFaceZone; faceSet {zone}Faces; cellSet wedgeCells; }}"""
    write(f"{case}/system/topoSetDict.zones", "dictionary", "topoSetDict", f"""
    actions
    (
        {{ name radiatorCells; type cellSet; action new; source boxToCell;
           box ({RAD['x0']} {RAD['y0']} -{WIN_HZ}) ({RAD['x1']} {RAD['y1']} {WIN_HZ}); }}
        {{ name radiator; type cellZoneSet; action new; source setToCellZone; set radiatorCells; }}
        // the room: everything inside the window wall (on tilt, less the wedge outside the sash)
        {{ name roomCells; type cellSet; action new; source boxToCell; box (0 -1 -{big}) ({big} {big} {big}); }}
        {room_minus_wedge}
        {{ name room; type cellZoneSet; action new; source setToCellZone; set roomCells; }}
        // everything inside the frame's plane, the wedge included: the volume whose budget of s
        // the opening's flux closes
        {{ name indoorCells; type cellSet; action new; source boxToCell; box (0 -1 -{big}) ({big} {big} {big}); }}
        {{ name indoor; type cellZoneSet; action new; source setToCellZone; set indoorCells; }}
        // the opening, in the frame's plane x = 0 (internal faces; on tilt the sash's lowest rows
        // lie in this plane and are wall)
        {{ name openingFaces; type faceSet; action new; source boxToFace;
           box (-{e} {WIN_Y0} -{WIN_HZ}) ({e} {WIN_Y1} {WIN_HZ}); }}
        {{ name outdoorCells; type cellSet; action new; source boxToCell; box (-{big} -{big} -{big}) (0 {big} {big}); }}
        {{ name opening; type faceZoneSet; action new; source setsToFaceZone;
           faceSet openingFaces; cellSet outdoorCells; }}{gaps}
    );
    """)
    write(f"{case}/system/setFieldsDict", "dictionary", "setFieldsDict", f"""
    defaultFieldValues ( volScalarFieldValue T {TOUT} volScalarFieldValue s 0 );
    regions
    (
        // the room: 20 C, all of it the room's own air; the reveal and outdoors: 0 C
        boxToCell {{ box (0 -1 -{big}) ({big} {big} {big});
                    fieldValues ( volScalarFieldValue T {TAMB} volScalarFieldValue s 1 ); }}
    );
    """)


def fields(case, run, outdoor):
    walls_room = "walls"
    adiab = '"(outerWalls|sashA|sashB)"'
    write(f"{case}/0.orig/U", "volVectorField", "U", f"""
    dimensions [0 1 -1 0 0 0 0];
    internalField uniform (0 0 0);
    boundaryField
    {{
        outside {{ type pressureInletOutletVelocity; value uniform (0 0 0); }}
        "(walls|outerWalls|sashA|sashB)" {{ type noSlip; }}
    }}
    """)
    if outdoor == "fixed":
        # the first build's: still outdoor air at a uniform 0 C is hydrostatic, so
        # p_rgh = p + rho g y is uniform there, and the open faces hold it at 1e5, less the
        # dynamic head on inflow. But a face that warm air leaves through then holds the
        # pressure of a column of that warm air, not the outdoor air's: 1-2 Pa too high where
        # the window's plume reaches the top, which pooled it there (README)
        outside = ("// still outdoor air at a uniform 0 C is hydrostatic, so p_rgh = p + rho g y is\n"
                   "        // uniform there: the open faces hold it at 1e5, less the dynamic head on inflow\n"
                   "        outside { type totalPressure; rho rho; psi none; gamma 1; p0 uniform 1e5; value uniform 1e5; }")
    else:
        # hydrostatic: p = p0(y), the 0 C outdoor air's own pressure at each face, less the
        # dynamic head on inflow, whatever the density of the air crossing it. p0 is written
        # per face by hydrostatic_p0.py once the mesh is final; on cold faces it gives the
        # fixed boundary's p_rgh exactly
        outside = "outside { type prghTotalPressure; rho rho; p0 uniform 1e5; value uniform 1e5; }"
    write(f"{case}/0.orig/p_rgh", "volScalarField", "p_rgh", """
    dimensions [1 -1 -2 0 0 0 0];
    internalField uniform 1e5;
    boundaryField
    {
        %s
        "(walls|outerWalls|sashA|sashB)" { type fixedFluxPressure; value uniform 1e5; }
    }
    """ % outside)
    write(f"{case}/0.orig/p", "volScalarField", "p", """
    dimensions [1 -1 -2 0 0 0 0];
    internalField uniform 1e5;
    boundaryField
    {
        ".*" { type calculated; value uniform 1e5; }
    }
    """)
    write(f"{case}/0.orig/T", "volScalarField", "T", f"""
    dimensions [0 0 0 1 0 0 0];
    internalField uniform {TAMB};
    boundaryField
    {{
        outside {{ type inletOutlet; inletValue uniform {TOUT}; value uniform {TOUT}; }}
        // the room's floor, ceiling and walls: masonry and screed, whose surfaces hardly
        // cool in minutes, held at 20 C
        {walls_room} {{ type fixedValue; value uniform {TAMB}; }}
        // the wall's outer face, the reveal and the sash: adiabatic
        {adiab} {{ type zeroGradient; }}
    }}
    """)
    write(f"{case}/0.orig/s", "volScalarField", "s", """
    dimensions [0 0 0 0 0 0 0];
    internalField uniform 0;
    boundaryField
    {
        outside { type inletOutlet; inletValue uniform 0; value uniform 0; }
        ".*" { type zeroGradient; }
    }
    """)
    for name, dim, val, wf in (("k", "[0 2 -2 0 0 0 0]", "1e-4", "kLowReWallFunction"),
                               ("omega", "[0 0 -1 0 0 0 0]", "1.0", "omegaWallFunction")):
        write(f"{case}/0.orig/{name}", "volScalarField", name, f"""
        dimensions {dim};
        internalField uniform {val};
        boundaryField
        {{
            outside {{ type inletOutlet; inletValue uniform {val}; value uniform {val}; }}
            "(walls|outerWalls|sashA|sashB)" {{ type {wf}; value uniform {val}; }}
        }}
        """)
    write(f"{case}/0.orig/nut", "volScalarField", "nut", """
    dimensions [0 2 -1 0 0 0 0];
    internalField uniform 0;
    boundaryField
    {
        outside { type calculated; value uniform 0; }
        "(walls|outerWalls|sashA|sashB)" { type nutkWallFunction; value uniform 0; }
    }
    """)
    write(f"{case}/0.orig/alphat", "volScalarField", "alphat", """
    dimensions [1 -1 -1 0 0 0 0];
    internalField uniform 0;
    boundaryField
    {
        outside { type calculated; value uniform 0; }
        "(walls|outerWalls|sashA|sashB)" { type compressible::alphatJayatillekeWallFunction; Prt 0.85; value uniform 0; }
    }
    """)


def constant(case):
    write(f"{case}/constant/g", "uniformDimensionedVectorField", "g", """
    dimensions [0 1 -2 0 0 0 0];
    value (0 -9.81 0);
    """)
    write(f"{case}/constant/thermophysicalProperties", "dictionary", "thermophysicalProperties", f"""
    // radiatorUnderWindow's air
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
    write(f"{case}/constant/fvOptions", "dictionary", "fvOptions", f"""
    // radiatorUnderWindow's radiator: 60 W per metre over its 1.0 m, an enthalpy source spread over the box,
    // through which the air passes freely as through a convector's fins
    radiator
    {{
        type            scalarSemiImplicitSource;
        selectionMode   cellZone;
        cellZone        radiator;
        volumeMode      absolute;
        sources {{ h ({RAD_W} 0); }}
    }}
    buoyancyTurb {{ type buoyancyTurbSource; selectionMode all; }}
    """)


def system(case, run, tend, write_int, nprocs, field_int):
    gap_monitors = ""
    if run == "tilted":
        # gross mass flow each way through the tilted window's top gap and side gaps, kg/s
        gap_monitors = "\n    // the tilted window's gaps: gross mass flow each way, kg/s"
        for name, zone, d in (("topDown", "gapTop", "(0 -1 0)"), ("topUp", "gapTop", "(0 1 0)"),
                              ("leftIn", "gapLeft", "(0 0 -1)"), ("leftOut", "gapLeft", "(0 0 1)"),
                              ("rightIn", "gapRight", "(0 0 1)"), ("rightOut", "gapRight", "(0 0 -1)")):
            gap_monitors += f"""
    {name}
    {{
        $openingIn;
        name            {zone};
        direction       {d};
    }}"""
    write(f"{case}/system/controlDict", "dictionary", "controlDict", f"""
    // windowAiring, run {run}
    application     buoyantPimpleFoam;
    startFrom       latestTime;
    startTime       0;
    stopAt          endTime;
    endTime         {tend};
    deltaT          0.005;
    adjustTimeStep  yes;
    maxCo           1;          // radiatorUnderWindow's Courant number
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
    // the share of the room's own air, carried as a passive scalar with T's diffusivity:
    // alpha + alphat = mu/Pr + mut/Prt with radiatorUnderWindow's Pr 0.71 and Prt 0.85 (no nut key)
    s
    {{
        type            scalarTransport;
        libs            (solverFunctionObjects);
        field           s;
        phi             phi;
        rho             rho;
        alphaD          1.4084507;
        alphaDt         1.1764706;
        writeControl    writeTime;
    }}

    // ---- every time step: the room's air and the opening -----------------------------
    roomAir
    {{
        type            volFieldValue;
        libs            (fieldFunctionObjects);
        regionType      cellZone;
        name            room;
        operation       weightedVolIntegrate;
        weightField     rho;
        fields          (s);
        writeFields     false;
        writeControl    timeStep;
        log             false;
    }}
    indoorAir
    {{
        $roomAir;
        name            indoor;
    }}
    roomMass
    {{
        type            volFieldValue;
        libs            (fieldFunctionObjects);
        regionType      cellZone;
        name            room;
        operation       volIntegrate;
        fields          (rho);
        writeFields     false;
        writeControl    timeStep;
        log             false;
    }}
    roomMeanT
    {{
        type            volFieldValue;
        libs            (fieldFunctionObjects);
        regionType      cellZone;
        name            room;
        operation       weightedVolAverage;
        weightField     rho;
        fields          (T);
        writeFields     false;
        writeControl    timeStep;
        log             false;
    }}
    // gross mass flow each way through the frame's plane, kg/s: in = into the room (+x)
    openingIn
    {{
        type            surfaceFieldValue;
        libs            (fieldFunctionObjects);
        regionType      faceZone;
        name            opening;
        operation       sumDirection;
        direction       (1 0 0);
        fields          (phi);
        writeFields     false;
        writeControl    timeStep;
        log             false;
    }}
    openingOut
    {{
        $openingIn;
        direction       (-1 0 0);
    }}
    // the room's own air leaving: sum of phi s over the opening (net, + into the room)
    openingS
    {{
        type            surfaceFieldValue;
        libs            (fieldFunctionObjects);
        regionType      faceZone;
        name            opening;
        operation       weightedSum;
        weightField     phi;
        fields          (s T);
        writeFields     false;
        writeControl    timeStep;
        log             false;
    }}
    wallHeatFlux
    {{
        type            wallHeatFlux;
        libs            (fieldFunctionObjects);
        patches         (walls);
        // it writes its field into a time directory whenever it writes, which would leave
        // field-less time directories for startFrom latestTime: so only at the field writes
        writeControl    writeTime;
        log             false;
    }}
    minMax
    {{
        type            fieldMinMax;
        libs            (fieldFunctionObjects);
        fields          (T s U);
        writeControl    adjustableRunTime;
        writeInterval   {write_int};
        log             false;
    }}
    probes
    {{
        type            probes;
        libs            (sampling);
        fields          (T U s);
        writeControl    adjustableRunTime;
        writeInterval   {write_int};
        probeLocations
        (
            (0.5 0.1 0.01) (1.0 0.1 0.01) (2.0 0.1 0.01) (3.0 0.1 0.01)
            (1.0 1.1 0.01) (2.0 1.1 0.01) (3.0 1.1 0.01) (2.0 2.2 0.01)
        );
    }}{gap_monitors}

    // ---- the clip: radiatorUnderWindow's section through the middle of the window, the floor, and beside
    // the window ----
    // No bounds on any plane: in an earlier case a plane with a thin bounds box wrote nothing.
    planes
    {{
        type            surfaces;
        libs            (sampling);
        writeControl    adjustableRunTime;
        writeInterval   {write_int};
        surfaceFormat   vtk;
        formatOptions   {{ vtk {{ format binary; }} }}
        interpolate     false;
        fields          (T U s);
        surfaces
        {{
            mid     {{ type cuttingPlane; point (0 1.2 0.005); normal (0 0 1); interpolate false; }}
            ankle   {{ type cuttingPlane; point (2 0.1 0); normal (0 1 0); interpolate false; }}
            // beside the window, on the side away from the open sash: on tilt the cold air
            // comes in through the side triangles and falls down the wall here
            side    {{ type cuttingPlane; point (0 1.2 -0.65); normal (0 0 1); interpolate false; }}
        }}
    }}
    """)
    # the planes at t = 0 from the initial fields, which the solver does not write:
    # postProcess -dict system/planesT0 -fields '(T U s)' -time 0
    fo = open(f"{case}/system/functions").read()
    with open(f"{case}/system/planesT0", "w") as f:
        f.write(HDR.format(cls="dictionary", obj="planesT0"))
        f.write("functions {\n" + fo[fo.index("\nplanes\n") + 1:] + "}\n")
    write(f"{case}/system/fvSchemes", "dictionary", "fvSchemes", """
    // radiatorUnderWindow's schemes; s is convected with T's
    ddtSchemes      { default Euler; }
    gradSchemes     { default Gauss linear; }
    divSchemes
    {
        default         none;
        div(phi,U)      Gauss limitedLinearV 1;
        energy          Gauss limitedLinear 1;
        div(phi,h)      $energy;
        div(phi,e)      $energy;
        div(phi,s)      $energy;
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
        p_rgh       { solver GAMG; smoother DICGaussSeidel; tolerance 1e-7; relTol 0.01; }
        p_rghFinal  { $p_rgh; relTol 0; maxIter 100; }
        "(U|h|e|k|omega|s)"      { solver PBiCGStab; preconditioner DILU; tolerance 1e-7; relTol 0.1; }
        "(U|h|e|k|omega|s)Final" { $U; relTol 0; }
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


# ---------------------------------------------------------------- the double-hung runs
def use_double_hung_window():
    """The double-hung window's opening and mesh bands, in place of the turn-tilt window's."""
    global WIN_Y0, WIN_Y1, WIN_HZ, YS, ZS
    WIN_Y0, WIN_Y1, WIN_HZ = DH_WIN["y0"], DH_WIN["y1"], DH_WIN["hz"]
    YS, ZS = DH_YS, DH_ZS


def double_hung_dicts(case, run):
    big = 100
    uy, ly = DH_RUNS[run]
    xo, xm = -2 * DH_SASH_D, -DH_SASH_D     # the outer track's outer face, the tracks' boundary
    # cells kept: as topo_dicts, less the two sashes, each a solid 40 mm deep in its own track
    write(f"{case}/system/topoSetDict.keep", "dictionary", "topoSetDict", f"""
    actions
    (
        {{ name keep; type cellSet; action new; source boxToCell; box (-{big} -{big} -{big}) ({big} {big} {big}); }}
        // the wall slab, apart from the opening
        {{ name keep; type cellSet; action subtract; source boxToCell; box (-{WALL_T} -{big} -{big}) (0 {WIN_Y0} {big}); }}
        {{ name keep; type cellSet; action subtract; source boxToCell; box (-{WALL_T} {WIN_Y1} -{big}) (0 {big} {big}); }}
        {{ name keep; type cellSet; action subtract; source boxToCell; box (-{WALL_T} -{big} -{big}) (0 {big} -{WIN_HZ}); }}
        {{ name keep; type cellSet; action subtract; source boxToCell; box (-{WALL_T} -{big} {WIN_HZ}) (0 {big} {big}); }}
        // beyond the room's floor, ceiling and side walls
        {{ name keep; type cellSet; action subtract; source boxToCell; box (0 -{big} -{big}) ({big} 0 {big}); }}
        {{ name keep; type cellSet; action subtract; source boxToCell; box (0 {ROOM_Y} -{big}) ({big} {big} {big}); }}
        {{ name keep; type cellSet; action subtract; source boxToCell; box (0 -{big} -{big}) ({big} {big} -{ROOM_HZ}); }}
        {{ name keep; type cellSet; action subtract; source boxToCell; box (0 -{big} {ROOM_HZ}) ({big} {big} {big}); }}
        // the upper sash in the outer track, the lower sash in the inner
        {{ name keep; type cellSet; action subtract; source boxToCell; box ({xo} {uy} -{WIN_HZ}) ({xm} {uy + DH_SASH_H:.2f} {WIN_HZ}); }}
        {{ name keep; type cellSet; action subtract; source boxToCell; box ({xm} {ly} -{WIN_HZ}) (0 {ly + DH_SASH_H:.2f} {WIN_HZ}); }}
    );
    """)
    # the exposed faces outside the room (the wall's outer face, the reveal and the sashes) and
    # the lower sash's face in the frame's plane, x = 0 -> outerWalls, adiabatic
    write(f"{case}/system/topoSetDict.split", "dictionary", "topoSetDict", f"""
    actions
    (
        {{ name outerFaces; type faceSet; action new; source patchToFace; patch walls; }}
        {{ name outerFaces; type faceSet; action subset; source boxToFace; box (-{big} -{big} -{big}) (-0.0001 {big} {big}); }}
        {{ name sashRoom; type faceSet; action new; source patchToFace; patch walls; }}
        {{ name sashRoom; type faceSet; action subset; source boxToFace; box (-0.0001 {WIN_Y0 + 1e-5:g} -{WIN_HZ - 1e-5:g}) (0.0001 {WIN_Y1 - 1e-5:g} {WIN_HZ - 1e-5:g}); }}
        {{ name outerFaces; type faceSet; action add; source faceToFace; set sashRoom; }}
    );
    """)
    write(f"{case}/system/createPatchDict", "dictionary", "createPatchDict", """
    pointSync false;
    patches
    (
        {
            name outerWalls;
            patchInfo { type wall; }
            constructFrom set;
            set outerFaces;
        }
    );
    """)

    def zone(name, x, y0, y1, oriented=True):
        # the internal faces in the plane x between y0 and y1 across the opening's width;
        # oriented into the room (from the outdoor cells) where the plane has outdoor cells on
        # one side, and +x otherwise
        src = ("setsToFaceZone; faceSet {0}Faces; cellSet outdoorCells;" if oriented
               else "setToFaceZone; faceSet {0}Faces;").format(name)
        return f"""
        {{ name {name}Faces; type faceSet; action new; source boxToFace; box ({x - .0001} {y0 + .000001} -0.429999) ({x + .0001} {y1 - .000001} 0.429999); }}
        {{ name {name}Faces; type faceSet; action subtract; source faceToFace; set boundaryFaces; }}
        {{ name {name}; type faceZoneSet; action new; source {src} }}"""
    zones = (zone("opening1", 0, WIN_Y0, WIN_Y1) + zone("lower", 0, WIN_Y0, 1.30)
             + zone("upper", 0, 1.30, WIN_Y1) + zone("clearOpening", -WALL_T, WIN_Y0, WIN_Y1, False)
             + zone("slotHead", -0.06, uy + DH_SASH_H, WIN_Y1, False))
    if ly > WIN_Y0:
        zones += zone("slotSill", -0.02, WIN_Y0, ly, False)
    write(f"{case}/system/topoSetDict.zones", "dictionary", "topoSetDict", f"""
    actions
    (
        // the radiator as in open and tilted, 1.0 m long, wider than this window
        {{ name radiatorCells; type cellSet; action new; source boxToCell; box ({RAD['x0']} {RAD['y0']} -0.5) ({RAD['x1']} {RAD['y1']} 0.5); }}
        {{ name radiator; type cellZoneSet; action new; source setToCellZone; set radiatorCells; }}
        {{ name roomCells; type cellSet; action new; source boxToCell; box (0 0 -{ROOM_HZ}) ({ROOM_X:g} {ROOM_Y} {ROOM_HZ}); }}
        {{ name room; type cellZoneSet; action new; source setToCellZone; set roomCells; }}
        {{ name indoor; type cellZoneSet; action new; source setToCellZone; set roomCells; }}
        {{ name outdoorCells; type cellSet; action new; source boxToCell; box (-{big} -{big} -{big}) (0 {big} {big}); }}
        {{ name boundaryFaces; type faceSet; action new; source patchToFace; patches (".*"); }}
        // opening1: the frame's plane x = 0 (the monitored opening, in front of the sashes);
        // lower and upper: its parts below and above 1.30 m; clearOpening: the reveal's outer
        // face; slotHead and slotSill: the gaps above the upper sash and below the lower one{zones}
    );
    """)
    write(f"{case}/system/setFieldsDict", "dictionary", "setFieldsDict", f"""
    defaultFieldValues ( volScalarFieldValue T {TOUT} volScalarFieldValue s 0 );
    regions
    (
        // the room: 20 C, all of it the room's own air; the reveal and outdoors: 0 C
        boxToCell {{ box (0 -1 -{big}) ({big} {big} {big});
                    fieldValues ( volScalarFieldValue T {TAMB} volScalarFieldValue s 1 ); }}
    );
    """)


def double_hung_monitors(run):
    """The opening's parts and the slots: gross flow each way and net, kg/s, + into the room."""
    names = ["upper", "slotHead"] + (["lower", "slotSill"] if DH_RUNS[run][1] > WIN_Y0 else [])
    txt = "\n// the window's parts: the frame's plane below and above 1.30 m, and the slots\n"
    for n in names:
        txt += f"{n}In {{ $opening1In; name {n}; }}\n{n}Out {{ $opening1Out; name {n}; }}\n{n}Net {{ $opening1Net; name {n}; }}\n"
    return txt + "clearOpeningIn { $opening1In; name clearOpening; }\n"


# ---------------------------------------------------------------- the barometric outdoor boundary
def barometric_system(case, run, tend, write_int, nprocs, field_int, extra="",
                      into_room="(1 0 0)", mid="(0 1.2 0)", label="windowAiring"):
    """controlDict, functions and planesT0 for the barometric boundary; fvSchemes, fvSolution and
    decomposeParDict as system(). The functions: system()'s, with the opening's zone `opening1`,
    its net flow, the room's mean s and the per-step scalar budget (fluxBudget), and without
    wallHeatFlux and the plane beside the window. into_room is the opening's inward normal and
    mid a point of the clip's mid-plane, normal z; extra is appended."""
    system(case, run, tend, write_int, nprocs, field_int)
    cd = open(f"{case}/system/controlDict").read()
    for a, b in (("// windowAiring, run", f"// {label}, run"), ("the last two kept", "the last one kept"),
                 ("purgeWrite      2", "purgeWrite      1"),
                 ("runTimeModifiable true", "runTimeModifiable false")):
        assert cd.count(a) == 1, a
        cd = cd.replace(a, b)
    open(f"{case}/system/controlDict", "w").write(cd)
    with open(f"{case}/system/fvSchemes", "a") as f:
        f.write("\n// fluxBudget rebuilds s's face flux from its matrix\nfluxRequired { s; }\n")
    out_dir = into_room.replace("(", "").replace(")", "").split()
    out_dir = "(" + " ".join(v[1:] if v.startswith("-") else ("0" if v == "0" else "-" + v) for v in out_dir) + ")"
    write(f"{case}/system/functions", "dictionary", "functions", f"""
    // the share of the room's own air, carried as a passive scalar with T's diffusivity:
    // alpha + alphat = mu/Pr + mut/Prt with radiatorUnderWindow's Pr 0.71 and Prt 0.85 (no nut key)
    s
    {{
        type            scalarTransport;
        libs            (solverFunctionObjects);
        field           s;
        phi             phi;
        rho             rho;
        alphaD          1.4084507;
        alphaDt         1.1764706;
        writeControl    writeTime;
    }}

    // ---- every time step: the room's air and the opening -----------------------------
    roomAir
    {{
        type            volFieldValue;
        libs            (fieldFunctionObjects);
        regionType      cellZone;
        name            room;
        operation       weightedVolIntegrate;
        weightField     rho;
        fields          (s);
        writeFields     false;
        writeControl    timeStep;
        log             false;
    }}
    indoorAir
    {{
        $roomAir;
        name            indoor;
    }}
    roomMass
    {{
        type            volFieldValue;
        libs            (fieldFunctionObjects);
        regionType      cellZone;
        name            room;
        operation       volIntegrate;
        fields          (rho);
        writeFields     false;
        writeControl    timeStep;
        log             false;
    }}
    roomMeanT
    {{
        type            volFieldValue;
        libs            (fieldFunctionObjects);
        regionType      cellZone;
        name            room;
        operation       weightedVolAverage;
        weightField     rho;
        fields          (T);
        writeFields     false;
        writeControl    timeStep;
        log             false;
    }}
    roomMeanS {{ $roomMeanT; fields (s); }}
    // gross mass flow each way through the opening, kg/s: in = into the room
    opening1In
    {{
        type            surfaceFieldValue;
        libs            (fieldFunctionObjects);
        regionType      faceZone;
        name            opening1;
        operation       sumDirection;
        direction       {into_room};
        fields          (phi);
        writeFields     false;
        writeControl    timeStep;
        log             false;
    }}
    opening1Out
    {{
        $opening1In;
        direction       {out_dir};
    }}
    opening1Net {{ $opening1In; operation sumDirectionBalance; }}
    // the room's own air leaving: sum of phi s over the opening (net, + into the room)
    opening1S
    {{
        type            surfaceFieldValue;
        libs            (fieldFunctionObjects);
        regionType      faceZone;
        name            opening1;
        operation       weightedSum;
        weightField     phi;
        fields          (s T);
        writeFields     false;
        writeControl    timeStep;
        log             false;
    }}
    // the scalar's budget: s's own face flux, convection and diffusion as the scalarTransport
    // discretises them, summed over opening1 into the room every step; processor faces once
    fluxBudget
    {{
        type            coded;
        libs            (utilityFunctionObjects);
        name            fluxBudget;
        executeControl  timeStep;
        writeControl    none;
        codeInclude
        #{{
            #include "fvCFD.H"
            #include "turbulentFluidThermoModel.H"
            #include "coupledPolyPatch.H"
            #include <fstream>
        #}};
        codeOptions
        #{{
            -I$(LIB_SRC)/finiteVolume/lnInclude -I$(LIB_SRC)/meshTools/lnInclude -I$(LIB_SRC)/TurbulenceModels/turbulenceModels/lnInclude -I$(LIB_SRC)/TurbulenceModels/compressible/lnInclude -I$(LIB_SRC)/transportModels/compressible/lnInclude -I$(LIB_SRC)/thermophysicalModels/basic/lnInclude
        #}};
        codeLibs
        #{{
            -lfiniteVolume -lmeshTools -lcompressibleTurbulenceModels
        #}};
        codeExecute
        #{{
            const fvMesh& m = mesh();
            const auto& s = m.lookupObject<volScalarField>("s");
            const auto& phi = m.lookupObject<surfaceScalarField>("phi");
            const auto& turb = m.lookupObject<compressible::turbulenceModel>("turbulenceProperties");
            volScalarField D("DsBudget", turb.mu()/0.71 + turb.mut()/0.85);
            fvScalarMatrix adv(fvm::div(phi, s, "div(phi,s)"));
            fvScalarMatrix diff(fvm::laplacian(D, s));
            surfaceScalarField flux("sFluxBudget", adv.flux() - diff.flux());
            scalar q = 0;
            forAll(m.faceZones(), zi)
            {{
                const faceZone& z = m.faceZones()[zi];
                if (z.name() != "opening1") continue;
                forAll(z, j)
                {{
                    const label f = z[j];
                    scalar value = 0;
                    if (f < m.nInternalFaces()) value = flux[f];
                    else
                    {{
                        const label patch = m.boundaryMesh().whichPatch(f);
                        const polyPatch& pp = m.boundaryMesh()[patch];
                        const auto* cpp = isA<coupledPolyPatch>(pp);
                        if (cpp && !cpp->owner()) continue;
                        value = flux.boundaryField()[patch][pp.whichFace(f)];
                    }}
                    q += (z.flipMap()[j] ? -1 : 1)*value;
                }}
            }}
            reduce(q, sumOp<scalar>());
            if (Pstream::master())
            {{
                fileName dir = m.time().globalPath()/"postProcessing"/"fluxBudget";
                mkDir(dir);
                std::ofstream os((dir/"budget.dat").c_str(), std::ios_base::app);
                os.precision(12);
                // t, net s entering through opening1 (kg/s), a second opening's (none: 0), the radiator (W)
                os << m.time().value() << " " << q << " 0 {RAD_W:g}\\n";
            }}
        #}};
    }}
    minMax
    {{
        type            fieldMinMax;
        libs            (fieldFunctionObjects);
        fields          (T s U);
        writeControl    adjustableRunTime;
        writeInterval   {write_int};
        log             false;
    }}

    // ---- the clip: the section through the middle of the window, and the floor ----
    // No bounds on any plane: in an earlier case a plane with a thin bounds box wrote nothing.
    planes
    {{
        type            surfaces;
        libs            (sampling);
        writeControl    adjustableRunTime;
        writeInterval   {write_int};
        surfaceFormat   vtk;
        formatOptions   {{ vtk {{ format binary; }} }}
        interpolate     false;
        fields          (T U s);
        surfaces
        {{
            mid     {{ type cuttingPlane; point {mid}; normal (0 0 1); interpolate false; }}
            ankle   {{ type cuttingPlane; point (2 0.1 0); normal (0 1 0); interpolate false; }}
        }}
    }}
    """)
    if extra:
        with open(f"{case}/system/functions", "a") as f:
            f.write(extra)
    fo = open(f"{case}/system/functions").read()
    plane = fo[fo.index("\nplanes\n") + 1:]
    plane = plane[:plane.index("\n}\n") + 3]
    with open(f"{case}/system/planesT0", "w") as f:
        f.write(HDR.format(cls="dictionary", obj="planesT0"))
        f.write("functions {\n" + plane + "}\n")


# p and p_rgh at rest in the still outdoor air's barometric pressure, and p0 on the open faces
BAROMETRIC_P = '''#!/usr/bin/env python3
"""Start the run at rest in the still TOUT K outdoor air's barometric pressure, and hold the open
faces at it: each cell's p = 1e5 exp(-g y/(R TOUT)), its p_rgh = p + rho g y with its own
rho = p/(R T), and p0 on 0/p_rgh's `outside` patch at each face's height. Heights from 0/Cy,
which `postProcess -func writeCellCentres` writes in the case's format, binary or ascii."""
import math
import re
import struct

G, R = 9.81, 8314.47 / 28.96


def values(raw, chunk):
    m = re.search(rb"(?:value|internalField)\\s+nonuniform\\s+List<scalar>\\s*(\\d+)\\s*\\(", chunk)
    n, a = int(m[1]), m.end()
    if re.search(rb"format\\s+binary", raw):
        return struct.unpack("<%dd" % n, chunk[a:a + 8 * n])
    return [float(v) for v in chunk[a:chunk.index(b")", a)].split()]


raw = open("0/Cy", "rb").read()
y = values(raw, raw[:raw.index(b"boundaryField")])
face_y = values(raw, raw[re.search(rb"\\n\\s*outside\\s*\\n\\s*\\{", raw).start():])
traw = open("0/T", "rb").read()
T = values(traw, traw[:traw.index(b"boundaryField")])
assert len(y) == len(T)
p = [1e5 * math.exp(-G * v / (R * TOUT)) for v in y]
p_rgh = [v + v / (R * t) * G * yy for v, t, yy in zip(p, T, y)]
p0 = [1e5 * math.exp(-G * v / (R * TOUT)) for v in face_y]


def nonuniform(v):
    return "nonuniform List<scalar>\\n%d\\n(\\n" % len(v) + "\\n".join(format(x, ".14g") for x in v) + "\\n)"


for name, v in (("p", p), ("p_rgh", p_rgh)):
    src = open("0/" + name).read()
    assert src.count("internalField uniform 1e5;") == 1
    src = src.replace("internalField uniform 1e5;", "internalField " + nonuniform(v) + ";")
    if name == "p_rgh":
        assert src.count("p0 uniform 1e5;") == 1
        src = src.replace("p0 uniform 1e5;", "p0 " + nonuniform(p0) + ";")
    open("0/" + name, "w").write(src)
print("barometric p and p_rgh in %d cells; p0 on %d outdoor faces, y %.3f to %.3f m"
      % (len(p), len(p0), min(face_y), max(face_y)))
'''


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
    runApplication -s sash topoSet -dict system/topoSetDict.sash
    runApplication createBaffles -overwrite
    runApplication -s zones topoSet -dict system/topoSetDict.zones
    rm -rf 0 && cp -r 0.orig 0
    runApplication setFields
HYDROSTATIC    runApplication checkMesh -constant
    runApplication decomposePar
    exit 0
fi
runParallel -n NPROCS buoyantPimpleFoam
"""

# the outdoor faces' p0 for the hydrostatic boundary, from the final mesh's face centres
ALLRUN_HYDROSTATIC = """    runApplication postProcess -func writeCellCentres -time 0
    python3 hydrostatic_p0.py > log.hydrostaticP0 2>&1
    rm -f 0/C 0/Cx 0/Cy 0/Cz
"""

# the barometric boundary: each cell's p and p_rgh and the outdoor faces' p0, on the final mesh
ALLRUN_BAROMETRIC = """    runApplication postProcess -func writeCellCentres -time 0
    python3 barometric_p.py > log.barometricP 2>&1
    rm -f 0/C 0/Cx 0/Cy 0/Cz
"""

HYDROSTATIC_P0 = '''#!/usr/bin/env python3
"""Write p0 on 0/p_rgh's `outside` patch: the pressure of still outdoor air at TOUT K at each
face's height y, p0 = 1e5/(1 + g y/(R TOUT)), which is what a uniform p_rgh of 1e5 gives in
air of that temperature (p_rgh = p - rho g.x, hRef 0). Face heights from 0/Cy, which
`postProcess -func writeCellCentres` writes in the case's format, binary or ascii."""
import re
import struct

G, R, T = 9.81, 8314.47 / 28.96, TOUT
raw = open("0/Cy", "rb").read()
fmt = re.search(rb"format\\s+(\\w+);", raw).group(1)
i = raw.index(b"boundaryField")
i = re.compile(rb"\\n\\s*outside\\s*\\n\\s*\\{").search(raw, i).end()
m = re.compile(rb"value\\s+nonuniform\\s+List<scalar>\\s*(\\d+)\\s*\\(").search(raw, i)
n = int(m.group(1))
if fmt == b"binary":
    y = struct.unpack(f"<{n}d", raw[m.end():m.end() + 8 * n])
else:
    y = [float(v) for v in raw[m.end():raw.index(b")", m.end())].split()]
assert len(y) == n
p0 = " ".join("%.10g" % (1e5 / (1 + G * yy / (R * T))) for yy in y)
src = open("0/p_rgh").read()
old = "outside { type prghTotalPressure; rho rho; p0 uniform 1e5;"
assert src.count(old) == 1
open("0/p_rgh", "w").write(src.replace(old, f"outside {{ type prghTotalPressure; rho rho; p0 nonuniform List<scalar> {n} ({p0});"))
print(f"{n} outside faces, y {min(y):.3f} to {max(y):.3f} m, p0 {1e5 / (1 + G * max(y) / (R * T)):.3f} to {1e5 / (1 + G * min(y) / (R * T)):.3f} Pa")
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", choices=["open", "tilted", "tilted-thin"] + list(DH_RUNS))
    ap.add_argument("dir")
    ap.add_argument("--tend", type=float, default=300)
    ap.add_argument("--write", type=float, default=None,
                    help="plane interval, s: 0.625 (open, tilted), 1.25 (the double-hung runs)")
    ap.add_argument("--fields", type=float, default=None,
                    help="field-write interval, s: 25 (open, tilted), 60 (the double-hung runs)")
    ap.add_argument("--nprocs", type=int, default=None, help="7 (open, tilted), 16 (double-hung)")
    # the outdoor boundary: hydrostatic (open's and tilted's), fixed (the superseded first build's
    # open and tilted-thin, and the fixed-boundary tilted control) or barometric (the double-hung
    # runs', which always use it)
    ap.add_argument("--outdoor", choices=["hydrostatic", "fixed", "barometric"], default=None)
    a = ap.parse_args()
    case = a.dir
    dh = a.run in DH_RUNS
    outdoor = "barometric" if dh else (a.outdoor or "hydrostatic")
    if dh and a.outdoor not in (None, "barometric"):
        ap.error("the double-hung runs use the barometric outdoor boundary")
    if outdoor == "barometric" and not dh:
        ap.error("--outdoor barometric is written for the double-hung runs only")
    write_int = a.write if a.write is not None else (1.25 if dh else 0.625)
    field_int = a.fields if a.fields is not None else (60 if dh else 25)
    nprocs = a.nprocs if a.nprocs is not None else (16 if dh else 7)
    if dh:
        use_double_hung_window()
    n = block_mesh(case)
    if dh:
        double_hung_dicts(case, a.run)
    else:
        topo_dicts(case, a.run)
    # the double-hung runs' 0.orig is open's: no sash patch (the sashes' faces are outerWalls)
    fields(case, "open" if dh else a.run, "hydrostatic" if outdoor == "barometric" else outdoor)
    if a.run == "tilted":
        # one sash patch, not a baffle's two sides
        for root, _, files in os.walk(f"{case}/0.orig"):
            for fn in files:
                fp = os.path.join(root, fn)
                t = open(fp).read().replace("sashA|sashB", "sash")
                open(fp, "w").write(t)
    constant(case)
    if dh:
        barometric_system(case, a.run, f"{a.tend:g}", f"{write_int:g}", nprocs, f"{field_int:g}",
                          extra=double_hung_monitors(a.run))
    else:
        system(case, a.run, f"{a.tend:g}", f"{write_int:g}", nprocs, f"{field_int:g}")
    allrun = ALLRUN.replace("NPROCS", str(nprocs))
    allrun = allrun.replace("HYDROSTATIC", {"hydrostatic": ALLRUN_HYDROSTATIC, "fixed": "",
                                            "barometric": ALLRUN_BAROMETRIC}[outdoor])
    if outdoor == "hydrostatic":
        with open(f"{case}/hydrostatic_p0.py", "w") as f:
            f.write(HYDROSTATIC_P0.replace("TOUT", f"{TOUT}"))
    if outdoor == "barometric":
        with open(f"{case}/barometric_p.py", "w") as f:
            f.write(BAROMETRIC_P.replace("TOUT", f"{TOUT}"))
    if a.run == "tilted" or dh:
        # no baffle: the solid sashes went with subsetMesh
        allrun = allrun.replace("    runApplication -s sash topoSet -dict system/topoSetDict.sash\n", "")
        allrun = allrun.replace("    runApplication createBaffles -overwrite\n", "")
    with open(f"{case}/Allrun", "w") as f:
        f.write(allrun)
    os.chmod(f"{case}/Allrun", 0o755)
    print(f"{a.run}: {case}, background box {n} cells")


if __name__ == "__main__":
    main()
