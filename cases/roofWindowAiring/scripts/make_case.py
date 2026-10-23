#!/usr/bin/env python3
"""Write one run of roofWindowAiring: an attic room aired through a centre-pivot roof window, or
windowAiring's room through its wall window, wide open on a still 0 C morning.

    python3 make_case.py <run> <dir> [--tend 300] [--write 1.25] [--fields 60] [--nprocs 16]

run is `roof` (the attic room and its VELUX GGL PK08 roof window, its sash turned wide open the
VELUX way) or `wall` (windowAiring's room and window with its sash turned wide open). Both are
written with ../../windowAiring/scripts/make_case.py's model, the same fields, thermophysics,
turbulence, radiator, schemes and solution settings, with the barometric outdoor boundary and
the per-step scalar budget of its double-hung runs (barometric_system); only the room, the
window and the mesh differ.

roof: the mesh is build_roof.py's (gmsh, swept across the room's width); the run's Allrun runs it
with $PYTHON (default python3), which needs gmsh 4.15.2 and NumPy.

wall: windowAiring's `open` (its blockMesh box cut down with subsetMesh and the sash a baffle
at 90 degrees on its hinge side), on a box that runs on past the room's inner wall and is
refined there as at the window: 20 mm across the window's width (52 cells) instead of
windowAiring's graded 28, and 1.5 m of outdoor air beyond the inner wall, which is solid, so
that air is a second, separate region the room never touches (README, "The wall window").
"""
import argparse
import importlib.util
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "windowAiring_make_case", os.path.join(HERE, "..", "..", "windowAiring", "scripts", "make_case.py"))
wa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wa)

# the roof window's opening on the roof's inner face, into the room: the inner face's normal
# (the roof is at 45 degrees, the room below it)
INTO_ROOM = "(0.7071067811865476 -0.7071067811865476 0)"
ROOF_HZ = (1.3065, 2.1935)   # the opening's width across the room, z (PK08: 887 mm)

# the wall run's box: windowAiring's XS mirrored about the room (the refinement at the window
# repeated at the inner wall, the wall 0.24 m thick there too, then 1.5 m of outdoor air), and
# ZS with 13 cells of 19.2 mm in each quarter of the window's width
WALL_XS = [(-1.74, -.24, 18, .1), (-.24, 0, 12, 1), (0, .3, 15, 1), (.3, 1, 16, 3.5), (1, 3, 24, 1),
           (3, 3.7, 16, 1 / 3.5), (3.7, 4, 15, 1), (4, 4.24, 12, 1), (4.24, 5.74, 18, 10)]
WALL_ZS = [(-2.5, -1.75, 4, .4), (-1.75, -.5, 20, .2), (-.5, -.25, 13, 1), (-.25, 0, 13, 1),
           (0, .25, 13, 1), (.25, .5, 13, 1), (.5, 1.75, 20, 5), (1.75, 2.5, 4, 2.5)]


def box(lo, hi):
    return "box (" + " ".join(map(str, lo)) + ") (" + " ".join(map(str, hi)) + ");"


def wall_dicts(case):
    wa.XS, wa.ZS = WALL_XS, WALL_ZS
    n = wa.block_mesh(case)
    p = f"{case}/system/blockMeshDict"
    t = open(p).read()
    for a, b in (("(4 5 6 7));", "(4 5 6 7) (1 2 6 5));"), ("faces ((1 2 6 5));", "faces ();"),
                 ("// the inner wall here; subsetMesh adds every face it exposes",
                  "// none here; subsetMesh adds every face it exposes")):
        assert t.count(a) == 1, a
        t = t.replace(a, b)
    open(p, "w").write(t)
    # createPatchDict as windowAiring's open; its other dictionaries are written below
    wa.topo_dicts(case, "open")
    w, big = wa.WIN_HZ, 100
    keep = [f"{{ name keep; type cellSet; action new; source boxToCell; {box((-big, -big, -big), (big, big, big))} }}",
            "// the window wall, apart from the opening"]
    for lo, hi in (((-.24, -big, -big), (0, .9, big)), ((-.24, 2.1, -big), (0, big, big)),
                   ((-.24, -big, -big), (0, big, -w)), ((-.24, -big, w), (0, big, big)),
                   ("// the inner wall, solid", None),
                   ((4, -big, -big), (4.24, big, big)),
                   ("// beyond the room's floor, ceiling and side walls", None),
                   ((0, -big, -big), (4, 0, big)), ((0, 2.4, -big), (4, big, big)),
                   ((0, -big, -big), (4, big, -1.75)), ((0, -big, 1.75), (4, big, big))):
        keep.append(lo if hi is None else
                    f"{{ name keep; type cellSet; action subtract; source boxToCell; {box(lo, hi)} }}")
    wa.write(f"{case}/system/topoSetDict.keep", "dictionary", "topoSetDict",
             "actions\n(\n" + "\n".join(keep) + "\n);\n")
    # the exposed faces beyond the room on either side -> outerWalls, adiabatic
    wa.write(f"{case}/system/topoSetDict.split", "dictionary", "topoSetDict", f"""
    actions
    (
        {{ name outerFaces; type faceSet; action new; source patchToFace; patch walls; }}
        {{ name outerFaces; type faceSet; action subset; source boxToFace; {box((-big, -big, -big), (-.0001, big, big))} }}
        {{ name outer2; type faceSet; action new; source patchToFace; patch walls; }}
        {{ name outer2; type faceSet; action subset; source boxToFace; {box((4.0001, -big, -big), (big, big, big))} }}
        {{ name outerFaces; type faceSet; action add; source faceToFace; set outer2; }}
    );
    """)
    # the sash turned wide open, as windowAiring's open: a baffle in the plane z = +0.5 m
    wa.baffle_dicts(case, f"{{ name sashFaces; type faceSet; action new; source boxToFace; "
                          f"box (0 .9 {w - .0001}) ({2 * w} 2.1 {w + .0001}); }}")
    wa.write(f"{case}/system/topoSetDict.zones", "dictionary", "topoSetDict", f"""
    actions
    (
        {{ name radiatorCells; type cellSet; action new; source boxToCell; {box((.04, .15, -.5), (.123, .75, .5))} }}
        {{ name radiator; type cellZoneSet; action new; source setToCellZone; set radiatorCells; }}
        {{ name roomCells; type cellSet; action new; source boxToCell; {box((0, 0, -1.75), (4, 2.4, 1.75))} }}
        {{ name room; type cellZoneSet; action new; source setToCellZone; set roomCells; }}
        {{ name indoor; type cellZoneSet; action new; source setToCellZone; set roomCells; }}
        // the opening, in the frame's plane x = 0, oriented into the room
        {{ name opening1Faces; type faceSet; action new; source boxToFace; {box((-.0001, .90001, -w + .00001), (.0001, 2.09999, w - .00001))} }}
        {{ name outdoor1; type cellSet; action new; source boxToCell; {box((-big, -big, -big), (0, big, big))} }}
        {{ name opening1; type faceZoneSet; action new; source setsToFaceZone; faceSet opening1Faces; cellSet outdoor1; }}
    );
    """)
    # the room only: the outdoor air beyond the inner wall stays at 0 C
    wa.write(f"{case}/system/setFieldsDict", "dictionary", "setFieldsDict", f"""
    defaultFieldValues ( volScalarFieldValue T {wa.TOUT} volScalarFieldValue s 0 );
    regions
    (
        // the room: 20 C, all of it the room's own air; the reveal and outdoors: 0 C
        boxToCell {{ {box((0, 0, -1.75), (4, 2.4, 1.75))}
                    fieldValues ( volScalarFieldValue T {wa.TAMB} volScalarFieldValue s 1 ); }}
    );
    """)
    wa.fields(case, "open", "hydrostatic")
    return n


ALLRUN_ROOF = """#!/bin/bash
# Mesh, set up and decompose this run; ./Allrun solve then runs it on NPROCS ranks.
cd "${0%/*}" || exit 1
. "$WM_PROJECT_DIR/bin/tools/RunFunctions"
set -e
if [ "$1" != solve ]; then
    "${PYTHON:-python3}" build_roof.py . > log.build_roof 2>&1
    runApplication checkMesh -constant
    rm -rf 0 && cp -r 0.orig 0
    runApplication setFields
    runApplication postProcess -func writeCellCentres -time 0
    python3 barometric_p.py > log.barometricP 2>&1
    rm -f 0/C 0/Cx 0/Cy 0/Cz
    runApplication decomposePar
    exit 0
fi
runParallel -n NPROCS buoyantPimpleFoam
"""


def roof_dicts(case):
    os.makedirs(f"{case}/constant", exist_ok=True)
    shutil.copy(os.path.join(HERE, "build_roof.py"), f"{case}/build_roof.py")
    # windowAiring's fields with one `sash` patch, as its tilted run
    wa.fields(case, "tilted", "hydrostatic")
    for fn in os.listdir(f"{case}/0.orig"):
        fp = f"{case}/0.orig/{fn}"
        text = open(fp).read().replace("sashA|sashB", "sash")
        open(fp, "w").write(text)
    wa.write(f"{case}/system/setFieldsDict", "dictionary", "setFieldsDict", f"""
    defaultFieldValues ( volScalarFieldValue T {wa.TOUT} volScalarFieldValue s 0 );
    regions
    (
        // the room (build_roof.py's zone): 20 C, all of it the room's own air
        zoneToCell {{ zone room; fieldValues ( volScalarFieldValue T {wa.TAMB} volScalarFieldValue s 1 ); }}
    );
    """)


def roof_monitors():
    txt = "\n// the opening's two sides of the sash, on the roof's inner face: eaves (below), ridge (above)\n"
    for n in ("eaves", "ridge"):
        txt += f"{n}In {{ $opening1In; name {n}; }}\n{n}Out {{ $opening1Out; name {n}; }}\n{n}Net {{ $opening1Net; name {n}; }}\n"
    return txt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", choices=["roof", "wall"])
    ap.add_argument("dir")
    ap.add_argument("--tend", type=float, default=300)
    ap.add_argument("--write", type=float, default=1.25)
    ap.add_argument("--fields", type=float, default=60)
    ap.add_argument("--nprocs", type=int, default=16)
    a = ap.parse_args()
    case = a.dir
    args = (f"{a.tend:g}", f"{a.write:g}", a.nprocs, f"{a.fields:g}")
    if a.run == "roof":
        roof_dicts(case)
        wa.constant(case)
        wa.barometric_system(case, "roof", *args, extra=roof_monitors(), into_room=INTO_ROOM,
                             mid=f"(0 1.2 {sum(ROOF_HZ) / 2:g})", label="roofWindowAiring")
        allrun = ALLRUN_ROOF.replace("NPROCS", str(a.nprocs))
        note = "mesh by build_roof.py"
    else:
        n = wall_dicts(case)
        wa.constant(case)
        wa.barometric_system(case, "wall", *args, label="roofWindowAiring")
        allrun = wa.ALLRUN.replace("NPROCS", str(a.nprocs)).replace("HYDROSTATIC", wa.ALLRUN_BAROMETRIC)
        note = f"background box {n} cells"
    with open(f"{case}/barometric_p.py", "w") as f:
        f.write(wa.BAROMETRIC_P.replace("TOUT", f"{wa.TOUT}"))
    with open(f"{case}/Allrun", "w") as f:
        f.write(allrun)
    os.chmod(f"{case}/Allrun", 0o755)
    print(f"{a.run}: {case}, {note}")


if __name__ == "__main__":
    main()
