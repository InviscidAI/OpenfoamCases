#!/usr/bin/env python3
"""Write one run of airingRadiatorValve: windowAiring's room aired wide open for five minutes and
then shut, its radiator behind a thermostatic valve turned off while the window is open, or left on.

    python3 make_case.py <run> <dir> [--nprocs 16]

run is `off` (the valve held shut from 0 to 300 s, while the window is open, and set back to its
setting as the window shuts) or `on` (left at its setting throughout). The two runs differ only in
that line of constant/fvOptions.

The room, the window, the mesh, the fields, the air, the turbulence model, the schemes and the
solution settings are ../../windowAiring/scripts/make_case.py's run `open`, written by its own
functions with field writes every 60 s and planes every 1.25 s. On top of it:

- the radiator box gives the heat of a radiator behind a thermostatic valve (fv option
  trvRadiator, design.py's numbers), the room's air leaks at 0.5 an hour (infiltration) and the
  window wall's inner face takes radiation from the room's other surfaces (windowRadiation);
- every room surface is a 1-D layer that stores heat (T's boundary condition wallLayer on the
  patch walls), the window wall's through its 24 cm to the 0 C outdoor air;
- the outdoor faces hold still 0 C air's barometric pressure, p0 = 1e5 exp(-g y/(R T)), and every
  cell starts at rest in that pressure (initial_fields.py, written into the run), where
  windowAiring's open run used 1e5/(1 + g y/(R T));
- the per-step heat budget (function object airingBudget) and the planes the clip is drawn from.

The fv options, the boundary condition and the function object are ../src/airingLoss, compiled by
../Allrun. The run's own Allrun meshes the run and sets it up; ../Allrun solves it in two stages,
open 0-300 s and shut 300-900 s, with close_window.py between them.
"""
import argparse
import importlib.util
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "windowAiring_make_case", os.path.join(HERE, "..", "..", "windowAiring", "scripts", "make_case.py"))
wa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wa)
import design as design_module  # noqa: E402  (this directory)

TEND_OPEN = 300         # the window shuts at 300 s; ../Allrun sets 900 for the shut stage
FIELDS = 60             # full fields every 60 s, so that there is one at 300 s
PLANES = 1.25           # the clip's planes every 1.25 s (every 2.5 s once shut)

FV_OPTIONS = """FoamFile {{ version 2.0; format ascii; class dictionary; object fvOptions; }}
// A Stelrad Compact K1 600 x 1000 (980 W at 75/65/20 C, n 1.29) sized for the room's design heat
// loss on a 0 C day ({phi:.0f} W), behind a Danfoss RA 2000 head on an RA-N valve at setting 3:
// 20 C on the scale at Xp = 2 K, shut at 22 C, at most kvs/kv = 0.90/0.73 of the nominal flow.
// Its heat is spread over the radiator's box, through which the air passes as through a
// convector's fins. {note}
radiator
{{
    type            trvRadiator;
    selectionMode   cellZone;
    cellZone        radiator;
    Q50             {Q50};          // W at a 50 K log-mean difference (EN 442)
    n               {n};
    Crad            {Crad};         // J/K: 3.25 kg of water, 19.70 kg of steel at 450 J/kg K
    Tsupply         {Ts:.6f};       // K, flow water: {TsC:.2f} C, the design point's
    qNom            {qNom:.8f};     // kg/s at Xp = 2 K: the design loss with a 10 K water drop
    Tclose          {Tclose};       // K, setting 3 shuts at 22 C
    Xp              {Xp};
    fMax            {fMax:.6f};
    tauSen          {tau};          // s, the gas-filled RA 2000 head's 10 min
    offUntil        {off};          // s, valve held shut before this time
    sensorPoint     ({sp});         // the head, beside the radiator's top corner on the valve
    sensorRadius    {sr};
    TsenInit        {Tsen};         // the room at 20 C, the valve at its nominal flow
    TradInit        {Trad:.8f};     // steady at the design loss
}}
// EN 12831's minimum air change, 0.5 /h for a living room, as a sink on the room's air (x > 0):
// 113 W from the room at 20 C on a 0 C day
infiltration {{ type infiltration; selectionMode all; airChangesPerHour 0.5; Cp 1005; Tout 273.15; }}
// EN ISO 6946's radiation onto the window wall's cold inner face (hr = 5.14 W/m2K, from the
// room's other surfaces), its heat taken from the room's air
windowRadiation {{ type windowRadiation; selectionMode all; }}
buoyancyTurb {{ type buoyancyTurbSource; selectionMode all; }}
"""

# the planes the clip is drawn from and the walls' surface temperature, in place of windowAiring's
# planes, then the per-step heat budget
PLANES_AND_BUDGET = '''
planes
{
 type surfaces; libs (sampling);
 writeControl adjustableRunTime; writeInterval 1.25;
 surfaceFormat vtk;
 formatOptions { vtk { format binary; } }
 interpolate false; fields (T U s);
 surfaces
 {
  mid { type cuttingPlane; point (0 1.2 0.005); normal (0 0 1); interpolate false; bounds (-2 0 -10) (4.1 2.4 10); }
  ankle { type cuttingPlane; point (2 0.1 0); normal (0 1 0); interpolate false; bounds (0 -10 -1.75) (4 10 1.75); }
 }
}
wallSurfaces
{
 type surfaces; libs (sampling);
 writeControl adjustableRunTime; writeInterval 7.5;
 surfaceFormat vtk; formatOptions { vtk { format binary; } }
 fields (T); interpolate false;
 surfaces { walls { type patch; patches (walls); interpolate false; } }
}

budget { type airingBudget; libs ("libairingLoss.so"); watts 0; executeControl timeStep; writeControl timeStep; }
'''

# T's boundary condition on the room's surfaces, put in by initial_fields.py once setFields has
# written 0/T (setFields writes the patch as it reads it; the layers are built by the condition)
WALLS_T = (b"    walls\n    {\n        type            wallLayer;\n        refValue        uniform 293.15;\n"
           b"        refGradient     uniform 0;\n        valueFraction   uniform 1;\n        source          uniform 0;\n"
           b"        value           uniform 293.15;\n        kappaMethod     fluidThermo;\n    }\n")

INITIAL_FIELDS = r'''#!/usr/bin/env python3
"""Start the run at rest in still 0 C air's barometric pressure, put the wall layers' boundary
condition on the room's surfaces, and write the room air's starting energy for the heat budget.

- p = 1e5 exp(-g y/(R T0)) in every cell and p0 on 0/p_rgh's `outside` faces at their heights,
  T0 = 273.15 K; p_rgh = p + rho g y with each cell's own rho = p/(R T), T 20 C in the room
  (x > 0) and 0 C outdoors. Heights and x from 0/Cy and 0/Cx (postProcess writeCellCentres).
- 0/T's `walls` patch becomes wallLayer (src/airingLoss), which builds its layers itself.
- initial_air.json: the room's (x > 0) mass, integral of p dV and the air's internal energy above
  0 C, (cv/R) integral(p dV) - cv 273.15 m, as the airingBudget function object counts them.
"""
import json
import re
from pathlib import Path

import numpy as np

p = Path(".")
raw = p.joinpath("0/Cy").read_bytes()
fmt = re.search(rb"format\s+(\w+);", raw).group(1)


def arr(raw, start):
    m = re.search(rb"nonuniform\s+List<scalar>\s*(\d+)\s*\(", raw[start:])
    n = int(m.group(1)); i = start + m.end()
    if fmt == b"binary":
        return np.frombuffer(raw, dtype="<f8", count=n, offset=i).copy()
    return np.array(raw[i:raw.index(b")", i)].split(), dtype=float)


y = arr(raw, raw.index(b"internalField"))
yo = arr(raw, raw.index(b"outside", raw.index(b"boundaryField")))
rx = p.joinpath("0/Cx").read_bytes()
x = arr(rx, rx.index(b"internalField"))
R = 8314.46261815324 / 28.96; g = 9.81; To = 273.15
T = np.where(x > 0, 293.15, To)
pc = 1e5 * np.exp(-g * y / (R * To))
pr = pc + pc / (R * T) * g * y


def ls(a):
    return "nonuniform List<scalar>\n%d\n(\n%s\n)" % (len(a), "\n".join("%.17g" % v for v in a))


f = p / "0/p"; t = f.read_text()
assert t.count("internalField uniform 1e5") == 1
f.write_text(t.replace("internalField uniform 1e5", "internalField " + ls(pc)))
f = p / "0/p_rgh"; t = f.read_text()
assert t.count("internalField uniform 1e5") == 1 and t.count("p0 uniform 1e5") == 1
t = t.replace("internalField uniform 1e5", "internalField " + ls(pr))
f.write_text(t.replace("p0 uniform 1e5", "p0 " + ls(1e5 * np.exp(-g * yo / (R * To)))))
print("barometric p: cells", len(pc), "outside faces", len(yo), "range", pc.min(), pc.max())

f = p / "0/T"; b = f.read_bytes()
m = re.search(rb"\n    walls\n    \{\n        type            fixedValue;\n        value           uniform 293.15;\n    \}\n", b)
assert m and b.count(b"\n    walls\n") == 1, "0/T: the walls patch is not the fixedValue setFields wrote"
f.write_bytes(b[:m.start() + 1] + WALLS_T + b[m.end():])
print("0/T: walls -> wallLayer")

rt = p.joinpath("0/T").read_bytes()
Tc = arr(rt, rt.index(b"internalField"))
rv = p.joinpath("0/V").read_bytes()
Vc = arr(rv, rv.index(b"internalField"))
room = x > 0
cv = 1005 - R
mass = float(np.sum(pc[room] / (R * Tc[room]) * Vc[room]))
intP = float(np.sum(pc[room] * Vc[room]))
p.joinpath("initial_air.json").write_text(json.dumps(dict(
    mass=mass, intP=intP, Eair=cv / R * intP - cv * To * mass, volume=float(np.sum(Vc[room]))), indent=1))
print("initial_air.json written")
'''

ALLRUN = """#!/bin/bash
# Mesh and set up this run (windowAiring's open run, its wall layers and barometric start) and
# decompose it on NPROCS ranks; ../../Allrun solves it.
cd "${0%/*}" || exit 1
. "$WM_PROJECT_DIR/bin/tools/RunFunctions"
set -e
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
runApplication postProcess -funcs '(writeCellCentres writeCellVolumes)' -time 0
python3 initial_fields.py > log.initialFields 2>&1
rm -f 0/C 0/Cx 0/Cy 0/Cz 0/V
runApplication checkMesh -constant
# the planes at t = 0 from the initial fields, which the solver does not write
runApplication -s planesT0 postProcess -dict system/planesT0 -fields '(T U s)' -time 0
# collated, as the solved runs; decomposePar writes the window wall's 72 layers of its steady
# start profile into processors*/0
runApplication decomposePar -fileHandler collated
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", choices=["off", "on"])
    ap.add_argument("dir")
    ap.add_argument("--nprocs", type=int, default=16)
    a = ap.parse_args()
    case = a.dir
    d = design_module.design()

    # windowAiring's open run, as its generator writes it
    n = wa.block_mesh(case)
    wa.topo_dicts(case, "open")
    wa.fields(case, "open", "hydrostatic")
    wa.constant(case)
    wa.system(case, "open", f"{TEND_OPEN:g}", f"{PLANES:g}", a.nprocs, f"{FIELDS:g}")

    # controlDict: the library, the last field write kept, no edits while running
    c = f"{case}/system/controlDict"
    t = open(c).read()
    for old, new in (("runTimeModifiable true", "runTimeModifiable false"), ("purgeWrite      2", "purgeWrite      1")):
        assert t.count(old) == 1, old
        t = t.replace(old, new)
    t = re.sub(r"endTime\s+[^;]+;", f"endTime {TEND_OPEN};", t)
    t = re.sub(r"\nwriteInterval\s+[^;]+;", f"\nwriteInterval {FIELDS};", t)
    t += '\nlibs ("libairingLoss.so");\n'
    open(c, "w").write(t)

    # functions: windowAiring's monitors, the planes for the clip and the heat budget
    f = f"{case}/system/functions"
    t = open(f).read()
    ix = t.index("\nplanes\n")
    t = t[:ix] + PLANES_AND_BUDGET
    open(f, "w").write(t)
    with open(f"{case}/system/planesT0", "w") as g:
        g.write(wa.HDR.format(cls="dictionary", obj="planesT0"))
        g.write("functions {\n" + t[ix + 1:t.index("\nwallSurfaces")] + "\n}\n")

    # the radiator behind its valve, the leaks and the radiation onto the window wall
    note = ("Turned off: the valve is held shut until the window shuts at 300 s, then set back to 3."
            if a.run == "off" else "Left on at setting 3 throughout.")
    with open(f"{case}/constant/fvOptions", "w") as g:
        g.write(FV_OPTIONS.format(
            phi=d["design_heat_loss_W"], note=note, Q50=d["Q50_W"], n=d["n"], Crad=d["Crad_J_per_K"],
            Ts=d["Tsupply_K"], TsC=d["Tsupply_C"], qNom=d["qNom_kg_s"], Tclose=d["Tclose_K"], Xp=d["Xp_K"],
            fMax=d["fMax"], tau=d["tauSen_s"], off=TEND_OPEN if a.run == "off" else -1,
            sp=" ".join(map(str, d["sensorPoint"])), sr=d["sensorRadius"], Tsen=d["TsenInit_K"],
            Trad=d["TradInit_K"]))

    with open(f"{case}/initial_fields.py", "w") as g:
        g.write(INITIAL_FIELDS.replace("WALLS_T", repr(WALLS_T)))
    with open(f"{case}/Allrun", "w") as g:
        g.write(ALLRUN.replace("NPROCS", str(a.nprocs)))
    os.chmod(f"{case}/Allrun", 0o755)
    print(f"{a.run}: {case}, background box {n} cells")


if __name__ == "__main__":
    main()
