"""Write one run of the penguin case: its mesh, its fields and its dictionaries.

    python3 scripts/make_case.py lift50|lift64|swim|fly <runDir> [--nprocs N] [--from <lift50 runDir>]

Needs OpenFOAM (v2512) sourced, Python 3 with NumPy, and for the 2-D runs the gmsh Python module
(and PyVista for swim's pressure). The bird's surface, geometry/penguin.stl, is drawn by
scripts/penguin_geometry.py, which this script runs if the file is missing (it needs trimesh,
scipy, shapely, manifold3d and matplotlib); the 2-D runs need only geometry/penguin_profile.csv.

lift50, lift64   the 3-D steady half model of the whole bird, flippers included, pitched 10 deg
                 nose-up about x = 0.30 m, air along +x, y = 0 a symmetry plane. The STL is
                 rotated and split into the regions body and flipper (the flipper band in
                 config/caseSettings.json) and written to constant/triSurface/penguin.stl as
                 ASCII; blockMesh (template/lift/system/blockMeshDict, the background grid) and
                 snappyHexMesh -overwrite (template/lift/system/snappyHexMeshDict) mesh it, in
                 serial. 0/ is template/lift/0.orig/ at 50 m/s.
                 lift64 takes lift50's mesh and lift50's last written fields as its 0/ and sets
                 the inflow (inlet, farfield, the outlet's inletValue) to 64 m/s with its k and
                 omega, as the solved 64 m/s run started (README.md, "The 3-D runs").
swim, fly        the 2-D side section, the bird's outline in its plane of symmetry pitched
                 10 deg, one cell (0.01 m) deep, meshed by gmsh from geometry/penguin_profile.csv
                 (every second point) as the study's build_clipmesh.py did: 0.7 mm first cell,
                 seven quad layers, 2-3 mm on the bird, a 0.022 m box over the clip window; fly
                 adds a 0.008 m wake box (x 0.30-3.00 m, z -0.40 to 0.25 m). gmshToFoam, the
                 patch types, then the far field padded by 0.1 m at the top and the bottom
                 (z < -1.5 and z > 3 m stretched, nothing near the bird moved). swim's 0/p is the
                 pressure potential of its falling frame, 9.81 (10.6 - z), written from PyVista's
                 cell centres as the study's swim_pressure_init.py did.

The files under template/<lift|swim|fly>/ and template/<run>/ are copied in unchanged;
system/decomposeParDict is rewritten when --nprocs differs from the solved run's.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CASE = HERE.parent
TEMPLATE = CASE / "template"
CFG = json.loads((CASE / "config/caseSettings.json").read_text())
RUNS = list(CFG["runs"])


def H(obj, cls="dictionary"):
    return f"FoamFile\n{{version 2.0; format ascii; class {cls}; object {obj};}}\n"


def run(cmd, cwd, log):
    with open(Path(cwd) / log, "w") as f:
        r = subprocess.run(cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT)
    if r.returncode:
        sys.exit(f"{' '.join(cmd)} failed in {cwd}, see {log}")


def md5(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def copy_tree(src, dst):
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)


def inflow_kw(V):
    """k and omega at the inflow, as the study's configure.py wrote them (str() of the float)."""
    t = CFG["inflowTurbulence"]
    k = 1.5 * (t["intensity"] * V) ** 2
    om = np.sqrt(k) / (t["Cmu"] ** .25 * t["lengthScale_m"])
    return str(k), str(om)


def rotate(x, z):
    a = np.deg2rad(CFG["bird"]["pitch_deg"])
    x0 = CFG["bird"]["pitch_pivot_x_m"]
    return x0 + np.cos(a) * (x - x0) + np.sin(a) * z, -np.sin(a) * (x - x0) + np.cos(a) * z


# ---------------------------------------------------------------------------------------------
# 3-D
# ---------------------------------------------------------------------------------------------

def penguin_stl():
    stl = CASE / CFG["bird"]["stl"]
    if not stl.exists():
        subprocess.run([sys.executable, str(HERE / "penguin_geometry.py"), str(stl.parent)], check=True,
                       stdout=subprocess.DEVNULL)
    if md5(stl) != CFG["bird"]["stl_md5"]:
        print(f"warning: {stl} differs from the solved run's surface (md5 {CFG['bird']['stl_md5']})",
              file=sys.stderr)
    return stl


def write_trisurface(r):
    """The study's setup_meshes.py: rotate, split into body and flipper, write ASCII."""
    raw = np.fromfile(penguin_stl(), dtype=np.dtype([("n", "<f4", (3,)), ("v", "<f4", (3, 3)), ("attr", "<u2")]),
                      offset=84)
    v = raw["v"].astype(float)
    orig = v.copy()
    v[:, :, 0], v[:, :, 2] = rotate(v[:, :, 0], v[:, :, 2].copy())
    b = CFG["flipperBand"]
    c = orig.mean(1)
    flip = ((np.abs(c[:, 1]) > b["abs_y_min_m"]) & (np.abs(c[:, 2] - b["z_centre_m"]) < b["abs_dz_max_m"])
            & (c[:, 0] > b["x_min_m"]) & (c[:, 0] < b["x_max_m"]))
    (r / "constant/triSurface").mkdir(parents=True, exist_ok=True)
    with open(r / "constant/triSurface/penguin.stl", "w") as f:
        for name, mask in [("body", ~flip), ("flipper", flip)]:
            f.write("solid " + name + "\n")
            for t in v[mask]:
                n = np.cross(t[1] - t[0], t[2] - t[0])
                n /= max(np.linalg.norm(n), 1e-30)
                f.write("facet normal " + " ".join(map(str, n)) + "\nouter loop\n")
                for p in t:
                    f.write("vertex " + " ".join(map(str, p)) + "\n")
                f.write("endloop\nendfacet\n")
            f.write("endsolid " + name + "\n")


def latest_time(d):
    times = [(float(p.name), p) for p in d.iterdir() if p.is_dir() and re.fullmatch(r"[0-9.eE+-]+", p.name)]
    times = [t for t in times if t[0] > 0 and (t[1] / "U").exists()]
    if not times:
        sys.exit(f"{d}: no reconstructed time with fields (run reconstructPar -latestTime there)")
    return max(times)[1]


def set_inflow(r, V):
    """lift64: the inflow to V, with its k and omega, on fields copied from lift50."""
    k, om = inflow_kw(V)
    U = f"uniform ({V:g} 0 0)"
    sets = [("U", "boundaryField.inlet.value", U), ("U", "boundaryField.farfield.value", U),
            ("U", "boundaryField.outlet.inletValue", U)]
    for fld, val in (("k", k), ("omega", om)):
        sets += [(fld, "boundaryField.inlet.value", f"uniform {val}"),
                 (fld, "boundaryField.farfield.value", f"uniform {val}"),
                 (fld, "boundaryField.outlet.inletValue", f"uniform {val}")]
    for fld, entry, val in sets:
        subprocess.run(["foamDictionary", f"0/{fld}", "-entry", entry, "-set", val], cwd=r, check=True,
                       stdout=subprocess.DEVNULL)


def make_lift(name, r, src):
    copy_tree(TEMPLATE / "lift/system", r / "system")
    copy_tree(TEMPLATE / "lift/constant", r / "constant")
    copy_tree(TEMPLATE / name / "system", r / "system")
    (r / f"{name}.foam").touch()
    if name == "lift50":
        write_trisurface(r)
        run(["blockMesh"], r, "log.blockMesh")
        run(["snappyHexMesh", "-overwrite"], r, "log.snappyHexMesh")
        shutil.copytree(TEMPLATE / "lift/0.orig", r / "0")
    else:
        src = Path(src or r.parent / "lift50")
        shutil.copytree(src / "constant/polyMesh", r / "constant/polyMesh")
        shutil.copytree(src / "constant/triSurface", r / "constant/triSurface")
        last = latest_time(src)
        (r / "0").mkdir()
        for fld in ("U", "p", "k", "omega", "nut"):
            shutil.copy(last / fld, r / "0" / fld)
        set_inflow(r, CFG["runs"][name]["speed_m_s"])
        print(f"{r}: 0/ from {last} with the inflow at {CFG['runs'][name]['speed_m_s']:g} m/s")


# ---------------------------------------------------------------------------------------------
# 2-D
# ---------------------------------------------------------------------------------------------

def clip_mesh(r, wake):
    """The study's build_clipmesh.py (and rework_sas/build_clipmesh_sas.py with the wake box)."""
    import gmsh
    prof = CASE / CFG["bird"]["profile"]
    if md5(prof) != CFG["bird"]["profile_md5"]:
        print(f"warning: {prof} differs from the solved runs' profile", file=sys.stderr)
    q = np.loadtxt(prof, delimiter=",", skiprows=1)
    if np.linalg.norm(q[-1] - q[0]) < 1e-8:
        q = q[:-1]
    q = q[::2]
    q = np.column_stack(rotate(q[:, 0], q[:, 1]))
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("penguin_section")
    g = gmsh.model.geo
    p = [g.addPoint(x, 0, z, .002) for x, z in q]
    bird = [g.addLine(p[i], p[(i + 1) % len(p)]) for i in range(len(p))]
    bl = g.addCurveLoop(bird)
    pout = [g.addPoint(x, 0, z, .5) for x, z in [(-5.6, -5.6), (11.2, -5.6), (11.2, 10.5), (-5.6, 10.5)]]
    outer = [g.addLine(pout[i], pout[(i + 1) % 4]) for i in range(4)]
    s = g.addPlaneSurface([g.addCurveLoop(outer), bl])
    g.synchronize()
    f = gmsh.model.mesh.field
    b = f.add("BoundaryLayer")
    f.setNumbers(b, "CurvesList", bird)
    f.setNumber(b, "Size", .0007)
    f.setNumber(b, "Ratio", 1.18)
    f.setNumber(b, "Thickness", .010)
    f.setNumber(b, "Quads", 1)
    f.setAsBoundaryLayer(b)
    d = f.add("Distance")
    f.setNumbers(d, "CurvesList", bird)
    f.setNumber(d, "Sampling", 15)
    th = f.add("Threshold")
    f.setNumber(th, "InField", d)
    f.setNumber(th, "SizeMin", .003)
    f.setNumber(th, "SizeMax", .5)
    f.setNumber(th, "DistMin", .012)
    f.setNumber(th, "DistMax", 1.5)
    box = f.add("Box")
    for k, v in dict(VIn=.022, VOut=.5, XMin=-.7, XMax=2.8, YMin=-.1, YMax=.1, ZMin=-1, ZMax=2.5,
                     Thickness=.4).items():
        f.setNumber(box, k, v)
    fields = [th, box]
    if wake:
        wk = f.add("Box")
        for k, v in dict(VIn=.008, VOut=.5, XMin=.30, XMax=3.00, YMin=-.1, YMax=.1, ZMin=-.40, ZMax=.25,
                         Thickness=1.5).items():
            f.setNumber(wk, k, v)
        fields.append(wk)
    m = f.add("Min")
    f.setNumbers(m, "FieldsList", fields)
    f.setAsBackgroundMesh(m)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    out = g.extrude([(2, s)], 0, CFG["section"]["span_m"], 0, numElements=[1], recombine=True)
    g.synchronize()
    gmsh.model.addPhysicalGroup(2, [s, out[0][1]], name="frontBack")
    gmsh.model.addPhysicalGroup(3, [out[1][1]], name="internal")
    for name, curves in [("bottom", [outer[0]]), ("right", [outer[1]]), ("top", [outer[2]]), ("left", [outer[3]]),
                         ("bird", bird)]:
        sides = []
        for dim, tag in out[2:]:
            edges = [abs(v) for _, v in gmsh.model.getBoundary([(dim, tag)], oriented=False)]
            if any(e in edges for e in curves):
                sides.append(tag)
        gmsh.model.addPhysicalGroup(2, sides, name=name)
    gmsh.model.mesh.generate(3)
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.write(str(r / "clip.msh"))
    gmsh.finalize()
    run(["gmshToFoam", "clip.msh"], r, "log.gmshToFoam")
    (r / "clip.msh").unlink()
    for n, typ in [("bird", "wall"), ("frontBack", "empty")]:
        subprocess.run(["foamDictionary", "constant/polyMesh/boundary", "-entry", f"entry0.{n}.type", "-set", typ],
                       cwd=r, check=True, stdout=subprocess.DEVNULL)
    pad_far_field(r / "constant/polyMesh/points")


def pad_far_field(f):
    """The study's pad_clip_domain.py: z from -5.6..10.5 to -5.7..10.6 m by stretching z < -1.5 and
    z > 3 m only. Handles ASCII points (as the cloud wrote them, %.12g) and binary."""
    b = f.read_bytes()
    head = b[:1000]
    if b"binary" in head.split(b"}")[0]:
        mt = re.search(rb"\n(\d+)\n\(", b)
        n, start = int(mt.group(1)), mt.end()
        p = np.frombuffer(b, dtype="<f8", count=n * 3, offset=start).reshape(n, 3).copy()
        write = lambda p: f.write_bytes(b[:start] + p.tobytes() + b[start + n * 24:])
    else:
        s = b.decode()
        ms = list(re.finditer(r"\(([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\)", s))
        p = np.array([[float(m.group(i)) for i in (1, 2, 3)] for m in ms])
        write = lambda p: f.write_text(s[:ms[0].start()] + "\n".join(
            "(" + " ".join(f"{v:.12g}" for v in q) + ")" for q in p) + s[ms[-1].end():])
    assert abs(p[:, 2].min() + 5.6) < 1e-7 and abs(p[:, 2].max() - 10.5) < 1e-7, "unexpected far field"
    z = p[:, 2]
    lo, hi = z < -1.5, z > 3
    p[lo, 2] = -1.5 + (z[lo] + 1.5) * 4.2 / 4.1
    p[hi, 2] = 3 + (z[hi] - 3) * 7.6 / 7.5
    write(p)


def swim_pressure(r):
    """The study's swim_pressure_init.py: p = 9.81 (10.6 - z) inside and on the right outlet."""
    import pyvista as pv
    rd = pv.OpenFOAMReader(str(r / "swim.foam"))
    rd.skip_zero_time = False
    rd.set_active_time_value(0)
    d = rd.read()
    m, bd = d["internalMesh"], d["boundary"]
    vals = 9.81 * (10.6 - m.cell_centers().points[:, 2])
    right = 9.81 * (10.6 - bd["right"].cell_centers().points[:, 2])

    def seq(v):
        return "nonuniform List<scalar>\n" + str(len(v)) + "\n(\n" + "\n".join(f"{x:.12g}" for x in v) + "\n)"
    s = ("FoamFile {version 2.0; format ascii; class volScalarField; object p;}\ndimensions [0 2 -2 0 0 0 0];\n"
         "internalField " + seq(vals) + ";\nboundaryField\n{\nleft {type fixedFluxPressure; value uniform 0;}\n"
         "bottom {type fixedFluxPressure; value uniform 0;}\nright {type fixedValue; value " + seq(right) + ";}\n"
         "top {type fixedValue; value uniform 0;}\nfrontBack {type empty;}\nbird {type zeroGradient;}\n}\n")
    (r / "0/p").write_text(s)


def make_2d(name, r):
    copy_tree(TEMPLATE / name / "system", r / "system")
    copy_tree(TEMPLATE / name / "constant", r / "constant")
    (r / f"{name}.foam").touch()
    clip_mesh(r, CFG["runs"][name]["wakeBox"])
    shutil.copytree(TEMPLATE / name / "0.orig", r / "0")
    if name == "swim":
        swim_pressure(r)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("run", choices=RUNS)
    ap.add_argument("runDir")
    ap.add_argument("--nprocs", type=int)
    ap.add_argument("--from", dest="src", help="lift64: the solved lift50 run (default <runDir>/../lift50)")
    a = ap.parse_args()
    r = Path(a.runDir).resolve()
    if r.exists():
        sys.exit(f"{r} exists; ./Allclean or remove it first")
    r.mkdir(parents=True)
    if CFG["runs"][a.run]["dims"] == 3:
        make_lift(a.run, r, a.src)
    else:
        make_2d(a.run, r)
    n = a.nprocs or CFG["runs"][a.run]["nProcs"]
    if n != CFG["runs"][a.run]["nProcs"]:
        (r / "system/decomposeParDict").write_text(H("decomposeParDict") + f"numberOfSubdomains {n}; method scotch;\n")
    print(f"written: {r}")


if __name__ == "__main__":
    main()
