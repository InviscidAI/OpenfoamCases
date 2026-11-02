#!/usr/bin/env python3
"""Write one run of ceilingVsUnderfloor into <runDir>.

    python3 scripts/make_case.py ceiling|floor <runDir> <meshDir> [--nprocs N]

copies <meshDir>'s polyMesh and its four mesh dictionaries (scripts/make_mesh.py, then
blockMesh, topoSet, createPatch and topoSet in Allrun) and template/'s files into <runDir>
unchanged, and writes:

- 0.orig/T, the one file that differs between the runs. Every wall is radLayerWall
  (src/radLayerWall) starting at the 16 C setback, 289.15 K, with emissivity 0.9 (the glass
  0.837):
    the heated surface (the ceiling in `ceiling`, the floor in `floor`): massless, Q = 1400 W,
      100 W/m2 over 14.0 m2;
    the other one: the floor a 3/4 in (19 mm) wood layer, the ceiling a 1/2 in (12.7 mm) gypsum
      layer;
    the window wall, the inner wall and the side walls: 1/2 in gypsum layers;
    each layer 24 slices with an adiabatic back; gypsum k 0.1587 W/m K, rho 640.7 kg/m3,
      cp 1130 J/kg K; wood k 0.1060, rho 656.8, cp 1884 (California Energy Commission);
    the glass: massless, h = 4.403 W/m2K to 0 C outside (U = 2.8 W/m2K with the inside film
      left to the solver).
- 0.orig/G, 0.orig/qr and the 48 rays 0.orig/ILambda_<i>_0 (fvDOM nPhi 3, nTheta 4): the room
  at 16 C in radiative equilibrium, every ray 126.170333 W/m2 sr, G = 1585.503256 W/m2 and
  qr = 0. These are the values the solved runs started from: underfloorVsRadiator's room
  converged by fvDOM at a uniform 293.15 K, with every ray and G scaled by (289.15/293.15)^4.
  That converged field was uniform to the 9 digits written; its qr was below 4e-13 W/m2.
  (template/0.orig/IDefault is the solved runs' too; with the rays given it is not used.)
- system/controlDict from template/, with the run's name in its comment.
- system/decomposeParDict: N subdomains by scotch (the solved runs used 8).
"""
import argparse
import math
import shutil
from pathlib import Path

CASE = Path(__file__).resolve().parents[1]
TEMPLATE = CASE / "template"

T0 = 289.15             # the night setback, 16 C
Q = 1400.0              # W, 100 W/m2 over the 14.0 m2 heated surface
GYPSUM = dict(nLayers=24, thickness=0.0127, conductivity=0.1587, rhoCp=640.7 * 1130)
WOOD = dict(nLayers=24, thickness=0.019, conductivity=0.1060, rhoCp=656.8 * 1884)
H_GLASS, T_OUT = 4.403, 273.15
I0 = "126.170333"       # W/m2 sr, each ray at t = 0
G0 = "1585.503256"      # W/m2
N_PHI, N_THETA = 3, 4   # constant/radiationProperties
WALLS = "(glass|windowWall|floor|ceiling|innerWall|sideWalls)"
MESH_DICTS = ("blockMeshDict", "topoSetDict.glass", "createPatchDict", "topoSetDict.zones")


def bc(patch, eps, Q=0.0, h=0.0, Ta=0.0, layer=None):
    s = (f"    {patch}\n    {{\n        type radLayerWall;\n        kappaMethod fluidThermo;\n"
         f"        Q {Q!r};\n        h {h!r};\n        Ta {Ta!r};\n        emissivity {eps!r};\n        Tinit {T0!r};\n")
    for k, v in (layer or {}).items():
        s += f"        {k} {v!r};\n"
    return s + f"        value uniform {T0!r};\n    }}\n"


def T_file(heated):
    other = "floor" if heated == "ceiling" else "ceiling"
    body = (bc(heated, 0.9, Q=Q) + bc(other, 0.9, layer=WOOD if other == "floor" else GYPSUM)
            + bc("windowWall", 0.9, layer=GYPSUM) + bc("innerWall", 0.9, layer=GYPSUM)
            + bc("sideWalls", 0.9, layer=GYPSUM) + bc("glass", 0.837, h=H_GLASS, Ta=T_OUT))
    return ("FoamFile { version 2.0; format ascii; class volScalarField; object T; }\n"
            f"dimensions [0 0 0 1 0 0 0];\ninternalField uniform {T0!r};\nboundaryField\n{{\n{body}}}\n")


def scalar_field(obj, value, wall_type):
    return (f"FoamFile {{ version 2.0; format ascii; class volScalarField; object {obj}; }}\n"
            "dimensions [1 0 -3 0 0 0 0];\n"
            f"internalField uniform {value};\n"
            f'boundaryField {{ "{WALLS}" {{ type {wall_type}; value uniform {value}; }} }}\n')


def main(run, rundir, meshdir, nprocs):
    p, m = Path(rundir), Path(meshdir)
    if p.exists():
        raise SystemExit(f"{p} exists; remove it first")
    shutil.copytree(TEMPLATE, p)
    shutil.copytree(m / "constant" / "polyMesh", p / "constant" / "polyMesh")
    for name in MESH_DICTS:
        shutil.copy(m / "system" / name, p / "system" / name)
    o = p / "0.orig"
    o.mkdir(exist_ok=True)
    (o / "T").write_text(T_file(run))
    (o / "G").write_text(scalar_field("G", G0, "calculated"))
    (o / "qr").write_text(scalar_field("qr", 0, "calculated"))
    for i in range(4 * N_PHI * N_THETA):
        (o / f"ILambda_{i}_0").write_text(scalar_field(f"ILambda_{i}_0", I0, "greyDiffusiveRadiation"))
    cd = p / "system" / "controlDict"
    cd.write_text(cd.read_text().replace("run RUN", f"run {run}"))
    (p / "system" / "decomposeParDict").write_text(
        "FoamFile { version 2.0; format ascii; class dictionary; object decomposeParDict; }\n"
        f"numberOfSubdomains {nprocs};\nmethod scotch;\n")
    (p / "room.foam").touch()
    print(f"{run}: {p}, heated {run}, {Q:g} W, start {T0} K")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("run", choices=["ceiling", "floor"])
    ap.add_argument("rundir")
    ap.add_argument("meshdir")
    ap.add_argument("--nprocs", type=int, default=8)
    a = ap.parse_args()
    main(a.run, a.rundir, a.meshdir, a.nprocs)
