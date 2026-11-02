#!/usr/bin/env python3
"""Write one run of crossVentilation: windowAiring's room aired through one window wide open, or
through two half-width windows on opposite walls, in a light breeze or on a still morning.

    python3 make_case.py <run> <dir> [--nprocs 16]

run      windows                                         outdoor air           solved
one      the window wall's 1.0 x 1.2 m window             breeze, wall pressures 0-180 s
two      a 0.5 x 1.2 m window in the window wall and      breeze, wall pressures 0-180 s
         another opposite it, in the inner wall
stillOne as one                                           still                 0-300 s
stillTwo as two                                           still                 0-300 s

Everything is written with ../../windowAiring/scripts/make_case.py's model (its fields,
thermophysics, turbulence, 60 W radiator, schemes and solution settings) on the box that
roofWindowAiring's `wall` run uses, which runs on past the room's inner wall to 1.5 m of outdoor
air beyond it. Here that air is outdoors: in `two` the inner wall has a window, in `one` it is
solid and that air is a second region joined to nothing. The windows are sashes turned wide open
at 90 degrees on their hinge side (windowAiring's `open`), each a baffle as wide as its window.

The breeze is no inlet: it is a pressure on each wall's outdoor air, +2.41 Pa in front of the
window wall and -1.45 Pa behind the inner wall (README, "The breeze"), put in by wind_p.py.
"""
import argparse
import importlib.util
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "windowAiring_make_case", os.path.join(HERE, "..", "..", "windowAiring", "scripts", "make_case.py"))
wa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wa)

# the breeze: 2.5 m/s at window height straight at the window wall, 1/2 rho V^2 = 3.99 Pa at
# 0 C, times Swami and Chandra's wall-averaged Cp +0.60 (windward) and -0.36 (leeward)
DP_WINDWARD, DP_LEEWARD = 2.41, -1.45

# run: (windows, breeze, endTime, startFrom)
RUNS = {
    "one": (1, True, 180, "startTime"),
    "two": (2, True, 180, "startTime"),
    "stillOne": (1, False, 300, "latestTime"),
    "stillTwo": (2, False, 300, "latestTime"),
}

# roofWindowAiring's `wall` box: windowAiring's XS mirrored about the room (the refinement at the
# window repeated at the inner wall, which is 0.24 m thick too, then 1.5 m of outdoor air), and ZS
# with 13 cells of 19.2 mm in each quarter of the 1.0 m window's width, so that the half-width
# windows' edges at +-0.25 m fall on cell faces
XS = [(-1.74, -.24, 18, .1), (-.24, 0, 12, 1), (0, .3, 15, 1), (.3, 1, 16, 3.5), (1, 3, 24, 1),
      (3, 3.7, 16, 1 / 3.5), (3.7, 4, 15, 1), (4, 4.24, 12, 1), (4.24, 5.74, 18, 10)]
ZS = [(-2.5, -1.75, 4, .4), (-1.75, -.5, 20, .2), (-.5, -.25, 13, 1), (-.25, 0, 13, 1),
      (0, .25, 13, 1), (.25, .5, 13, 1), (.5, 1.75, 20, 5), (1.75, 2.5, 4, 2.5)]
BIG = 100


def box(lo, hi):
    return "box (" + " ".join(map(str, lo)) + ") (" + " ".join(map(str, hi)) + ");"


def act(name, typ, action, source, extra):
    return f"{{ name {name}; type {typ}; action {action}; source {source}; {extra} }}"


def topo(case, which, lines):
    wa.write(f"{case}/system/topoSetDict.{which}", "dictionary", "topoSetDict",
             "actions\n(\n" + "\n".join(lines) + "\n);\n")


def mesh_dicts(case, n, w):
    """blockMeshDict, the topoSet, createPatch and createBaffles dictionaries and setFieldsDict.
    n: one or two windows; w: each window's half-width, m."""
    wa.XS, wa.ZS, wa.WIN_HZ = XS, ZS, w
    cells = wa.block_mesh(case)
    # the box's far end is outdoors too: the inner wall is cut out of it below
    p = f"{case}/system/blockMeshDict"
    t = open(p).read()
    for a, b in (("(4 5 6 7));", "(4 5 6 7) (1 2 6 5));"), ("faces ((1 2 6 5));", "faces ();")):
        assert t.count(a) == 1, a
        t = t.replace(a, b)
    open(p, "w").write(t)
    # createPatchDict as windowAiring's open (outerFaces -> outerWalls); the rest is written here
    wa.topo_dicts(case, "open")

    # cells kept: all, less the window wall and the inner wall apart from their openings, and
    # everything beyond the room's floor, ceiling and side walls
    keep = [act("keep", "cellSet", "new", "boxToCell", box((-BIG, -BIG, -BIG), (BIG, BIG, BIG)))]
    for x0, x1, hw in ((-.24, 0, w), (4, 4.24, w if n == 2 else 0)):
        if hw == 0:
            keep.append(act("keep", "cellSet", "subtract", "boxToCell", box((x0, -BIG, -BIG), (x1, BIG, BIG))))
            continue
        for lo, hi in (((x0, -BIG, -BIG), (x1, .9, BIG)), ((x0, 2.1, -BIG), (x1, BIG, BIG)),
                       ((x0, -BIG, -BIG), (x1, BIG, -hw)), ((x0, -BIG, hw), (x1, BIG, BIG))):
            keep.append(act("keep", "cellSet", "subtract", "boxToCell", box(lo, hi)))
    for lo, hi in (((0, -BIG, -BIG), (4, 0, BIG)), ((0, 2.4, -BIG), (4, BIG, BIG)),
                   ((0, -BIG, -BIG), (4, BIG, -1.75)), ((0, -BIG, 1.75), (4, BIG, BIG))):
        keep.append(act("keep", "cellSet", "subtract", "boxToCell", box(lo, hi)))
    topo(case, "keep", keep)

    # the faces subsetMesh exposes outside the room, beyond either wall's inside face (the walls'
    # outer faces and the reveals) -> outerWalls, adiabatic; the room's own stay `walls`
    topo(case, "split", [
        act("outerFaces", "faceSet", "new", "patchToFace", "patch walls;"),
        act("outerFaces", "faceSet", "subset", "boxToFace", box((-BIG, -BIG, -BIG), (-.0001, BIG, BIG))),
        act("outer2", "faceSet", "new", "patchToFace", "patch walls;"),
        act("outer2", "faceSet", "subset", "boxToFace", box((4.0001, -BIG, -BIG), (BIG, BIG, BIG))),
        act("outerFaces", "faceSet", "add", "faceToFace", "set outer2;")])

    # each sash turned wide open: a baffle standing at 90 degrees to its wall on the hinge side,
    # z = +w, from the frame's plane a sash's width (2w) into the room
    sash = f"{{ name sashFaces; type faceSet; action new; source boxToFace; box (0 .9 {w - .0001}) ({2 * w} 2.1 {w + .0001}); }}"
    if n == 2:
        sash += f"\n{{ name sashFaces; type faceSet; action add; source boxToFace; box ({4 - 2 * w} .9 {w - .0001}) (4 2.1 {w + .0001}); }}"
    wa.baffle_dicts(case, sash)

    # the radiator (windowAiring's box, 1.0 m long, under the window wall's window in every run),
    # the room, and each opening in its frame's plane, oriented into the room
    zones = [act("radiatorCells", "cellSet", "new", "boxToCell", box((.04, .15, -.5), (.123, .75, .5))),
             act("radiator", "cellZoneSet", "new", "setToCellZone", "set radiatorCells;"),
             act("roomCells", "cellSet", "new", "boxToCell", box((0, 0, -1.75), (4, 2.4, 1.75))),
             act("room", "cellZoneSet", "new", "setToCellZone", "set roomCells;"),
             act("indoor", "cellZoneSet", "new", "setToCellZone", "set roomCells;")]
    for k, x in enumerate([0, 4][:n], 1):
        zones += [act(f"opening{k}Faces", "faceSet", "new", "boxToFace",
                      box((x - .0001, .90001, -w + .00001), (x + .0001, 2.09999, w - .00001))),
                  act(f"outdoor{k}", "cellSet", "new", "boxToCell",
                      box((-BIG, -BIG, -BIG), (0, BIG, BIG)) if x == 0 else box((4, -BIG, -BIG), (BIG, BIG, BIG))),
                  act(f"opening{k}", "faceZoneSet", "new", "setsToFaceZone",
                      f"faceSet opening{k}Faces; cellSet outdoor{k};")]
    topo(case, "zones", zones)

    # the room at 20 C and all of it the room's own air; the reveals and outdoors at 0 C
    wa.write(f"{case}/system/setFieldsDict", "dictionary", "setFieldsDict",
             f"defaultFieldValues (volScalarFieldValue T {wa.TOUT} volScalarFieldValue s 0);\n"
             f"regions (boxToCell {{box (0 0 -1.75) (4 2.4 1.75); fieldValues "
             f"(volScalarFieldValue T {wa.TAMB} volScalarFieldValue s 1);}});\n")
    return cells


def system_dicts(case, run, n, breeze, tend, start_from, nprocs):
    # windowAiring's fvSchemes, fvSolution and decomposeParDict; its controlDict and functions
    # are replaced below
    wa.system(case, "open", tend, 1.25, nprocs, 60)
    with open(f"{case}/system/fvSchemes", "a") as f:
        f.write("\n// fluxBudget rebuilds s's face flux from its matrix\nfluxRequired { s; }\n")
    wa.write(f"{case}/system/controlDict", "dictionary", "controlDict", f"""
    // crossVentilation, run {run}
    application     buoyantPimpleFoam;
    startFrom       {start_from};
    startTime       0;
    stopAt          endTime;
    endTime         {tend};
    deltaT          0.005;
    adjustTimeStep  yes;
    maxCo           1;          // radiatorUnderWindow's Courant number
    maxDeltaT       0.1;
    // full fields every 60 s, the last one kept; the clip is the planes, written every 1.25 s
    // by the function objects
    writeControl    adjustableRunTime;
    writeInterval   60;
    purgeWrite      1;
    writeFormat     binary;
    writePrecision  8;
    writeCompression off;
    timeFormat      general;
    timePrecision   8;
    runTimeModifiable false;

    functions
    {{
        #include "functions"
    }}
    """)
    t = open(os.path.join(HERE, "..", "template", "functions")).read()
    # the breeze runs' alphaD and alphaDt: 1/0.71 and 1/0.85 to six figures, as foamDictionary
    # wrote them into those runs' controlDict; the still runs had eight
    ad, adt = ("1.40845", "1.17647") if breeze else ("1.4084507", "1.1764706")
    t = t.replace("ALPHADT", adt).replace("ALPHAD", ad)
    if n == 1:
        for name in ("opening2In", "opening2Out", "opening2S"):
            t, k = re.subn(r"(// [^\n]*\n)*" + name + r"\n\{[^}]*\}\n", "", t)
            assert k == 1, name
        t, k = re.subn(r"\nopening2Net \{[^}]*\}\n", "", t)
        assert k == 1
    open(f"{case}/system/functions", "w").write(t)
    # the planes at t = 0 from the initial fields, which the solver does not write
    plane = t[t.index("\nplanes\n") + 1:t.index("\nroomMeanS")]
    wa.write(f"{case}/system/planesT0", "dictionary", "planesT0", "functions {\n" + plane + "\n}\n")


ALLRUN = wa.ALLRUN.replace("HYDROSTATIC", """    runApplication postProcess -func writeCellCentres -time 0
    python3 wind_p.py WINDWARD LEEWARD > log.windP 2>&1
    rm -f 0/C 0/Cx 0/Cy 0/Cz
""")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", choices=list(RUNS))
    ap.add_argument("dir")
    ap.add_argument("--nprocs", type=int, default=16)
    a = ap.parse_args()
    case = a.dir
    n, breeze, tend, start_from = RUNS[a.run]
    w = .5 if n == 1 else .25
    cells = mesh_dicts(case, n, w)
    wa.fields(case, "open", "hydrostatic")
    wa.constant(case)
    system_dicts(case, a.run, n, breeze, tend, start_from, a.nprocs)
    shutil.copy(os.path.join(HERE, "wind_p.py"), f"{case}/wind_p.py")
    dp = (DP_WINDWARD, DP_LEEWARD) if breeze else (0, 0)
    allrun = (ALLRUN.replace("NPROCS", str(a.nprocs))
              .replace("WINDWARD", f"{dp[0]:g}").replace("LEEWARD", f"{dp[1]:g}"))
    with open(f"{case}/Allrun", "w") as f:
        f.write(allrun)
    os.chmod(f"{case}/Allrun", 0o755)
    print(f"{a.run}: {case}, {n} window(s) {2 * w:g} m wide, "
          f"{'breeze %+g/%+g Pa' % dp if breeze else 'still air'}, 0-{tend} s; background box {cells} cells")


if __name__ == "__main__":
    main()
