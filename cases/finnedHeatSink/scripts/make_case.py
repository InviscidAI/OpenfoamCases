#!/usr/bin/env python3
"""Write runs/<variant>/ from case/ and the sink's dimensions below.

    python3 scripts/make_case.py base    the run of record
    python3 scripts/make_case.py fine    the same domain with 1.5 times the cells each way
    python3 scripts/make_case.py tight   the first study's domain, 15 mm beside and 20 mm over the sink

Half model: y = 0 is the sink's centre plane. Millimetres here, metres in the dictionaries.
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# The sink. Base 50 x 50 x 5 mm, ten fins 1 mm thick and 25 mm tall at a 5 mm pitch,
# running the full 50 mm in the flow direction (x). Fin centres at y = +-2.5, 7.5 ... 22.5.
SINK_L, SINK_HALF_W, BASE_T, FIN_TOP = 50.0, 25.0, 5.0, 30.0
FINS_Y = [(2.0 + 5.0 * i, 3.0 + 5.0 * i) for i in range(5)]   # half model: 5 of the 10

VARIANTS = {
    # domain (mm): upstream, downstream, half width, height; cell sizes in the sink (mm)
    "base":  dict(up=50, down=100, half_w=100, height=120, dx=1.0, dy=0.5, dz_base=0.5, dz_fin=1.0, far=1.0),
    "fine":  dict(up=50, down=100, half_w=100, height=120, dx=2 / 3, dy=1 / 3, dz_base=1 / 3, dz_fin=2 / 3, far=1.5),
    "tight": dict(up=30, down=30, half_w=40, height=50, dx=1.0, dy=0.5, dz_base=0.5, dz_fin=1.0, far=1.0),
}
# Stage 1 solves the flow and the heat together; stage 2 freezes the flow and solves the heat alone.
FLOW_ITERS, ENERGY_ITERS = 1500, 1500


def graded(length, d_near, d_far_max, far_scale):
    """Cells and end-to-end expansion for a segment whose cell next to the sink is d_near,
    growing by at most 20% a cell (13% on the fine mesh) up to d_far_max."""
    g_max = 1.2 if far_scale == 1.0 else 1.13
    n = 1
    while True:
        def f(g):
            return d_near * (n if abs(g - 1) < 1e-12 else (g ** n - 1) / (g - 1)) - length
        if f(1.0) >= 0:
            g = 1.0
        else:
            lo, hi = 1.0, 3.0
            for _ in range(200):
                mid = 0.5 * (lo + hi)
                lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
            g = 0.5 * (lo + hi)
        if g <= g_max and d_near * g ** (n - 1) <= d_far_max * 1.0001:
            return n, g ** (n - 1)
        n += 1


def uniform(length, d):
    return max(1, round(length / d))


def block_mesh(v):
    up, down, hw, ht, s = v["up"], v["down"], v["half_w"], v["height"], v["far"]
    nx_up, ex_up = graded(up, v["dx"], 5.0 / s, s)
    nx_s = uniform(SINK_L, v["dx"])
    nx_dn, ex_dn = graded(down, v["dx"], 10.0 / s, s)
    ny_s = uniform(SINK_HALF_W, v["dy"])
    ny_o, ey_o = graded(hw - SINK_HALF_W, v["dy"], 10.0 / s, s)
    nz_b = uniform(BASE_T, v["dz_base"])
    nz_f = uniform(FIN_TOP - BASE_T, v["dz_fin"])
    nz_o, ez_o = graded(ht - FIN_TOP, v["dz_fin"], 10.0 / s, s)
    nx, ny, nz = nx_up + nx_s + nx_dn, ny_s + ny_o, nz_b + nz_f + nz_o
    cells = nx * ny * nz
    x0, x1 = -up, SINK_L + down
    txt = f"""FoamFile {{ version 2.0; format ascii; class dictionary; object blockMeshDict; }}
// Written by scripts/make_case.py ({v['name']}). Half model, y = 0 is the sink's centre plane.
// {nx} x {ny} x {nz} = {cells} cells before the sink is cut out.
scale 0.001;
vertices
(
    ({x0} 0 0) ({x1} 0 0) ({x1} {hw} 0) ({x0} {hw} 0)
    ({x0} 0 {ht}) ({x1} 0 {ht}) ({x1} {hw} {ht}) ({x0} {hw} {ht})
);
blocks
(
    hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz})
    simpleGrading
    (
        (({up} {nx_up} {1 / ex_up:.6g}) ({SINK_L} {nx_s} 1) ({down} {nx_dn} {ex_dn:.6g}))
        (({SINK_HALF_W} {ny_s} 1) ({hw - SINK_HALF_W} {ny_o} {ey_o:.6g}))
        (({BASE_T} {nz_b} 1) ({FIN_TOP - BASE_T} {nz_f} 1) ({ht - FIN_TOP} {nz_o} {ez_o:.6g}))
    )
);
boundary
(
    inlet    {{ type patch; faces ((0 4 7 3)); }}
    outlet   {{ type patch; faces ((1 2 6 5)); }}
    symMid   {{ type symmetryPlane; faces ((0 1 5 4)); }}
    side     {{ type symmetry; faces ((3 7 6 2)); }}
    top      {{ type symmetry; faces ((4 5 6 7)); }}
    bottom   {{ type wall; faces ((0 3 2 1)); }}
);
"""
    return txt, cells


def topo_set():
    m = 0.001
    boxes = [f"(0 0 0) ({SINK_L * m:g} {SINK_HALF_W * m:g} {BASE_T * m:g})"]
    for y0, y1 in FINS_Y:
        boxes.append(f"(0 {y0 * m:g} {BASE_T * m:g}) ({SINK_L * m:g} {y1 * m:g} {FIN_TOP * m:g})")
    b = "\n".join("                " + x for x in boxes)
    return f"""FoamFile {{ version 2.0; format ascii; class dictionary; object topoSetDict; }}
// The sink: the base and five fins of the half model. Everything else is air.
actions
(
    {{
        name heatsink; type cellSet; action new;
        source boxToCell;
        sourceInfo
        {{
            boxes
            (
{b}
            );
        }}
    }}
    {{ name air; type cellSet; action new; source cellToCell; sourceInfo {{ set heatsink; }} }}
    {{ name air; type cellSet; action invert; }}
    {{ name heatsink; type cellZoneSet; action new; source setToCellZone; sourceInfo {{ set heatsink; }} }}
    {{ name air; type cellZoneSet; action new; source setToCellZone; sourceInfo {{ set air; }} }}
);
"""


EVERY = "executeControl timeStep; executeInterval 10; writeControl timeStep; writeInterval 10; log false;"


def plane(name, x, ops):
    """Monitors on a plane across the fin envelope, in the air region only."""
    m = 0.001
    sd = (f"sampledSurfaceDict {{ type plane; planeType pointAndNormal; "
          f"pointAndNormalDict {{ point ({x * m:g} 0 0); normal (1 0 0); }} "
          f"bounds ({x * m - 1e-4:g} -1e-4 {BASE_T * m:g}) ({x * m + 1e-4:g} {SINK_HALF_W * m:g} {FIN_TOP * m:g}); }}")
    out = []
    for suffix, body in ops:
        out.append(f"""    {name}{suffix}
    {{
        type surfaceFieldValue; libs (fieldFunctionObjects); region air;
        regionType sampledSurface; name {name}; {sd}
        {body}
        writeFields false; {EVERY}
    }}""")
    return "\n".join(out)


def control_dict(end):
    planes = []
    # x = 25.5 and 49.5 mm: off the cell faces of both meshes, where a cut comes out empty
    for nm, x in (("midPlane", SINK_L / 2 + 0.5), ("exitPlane", SINK_L - 0.5)):
        planes.append(plane(nm, x, [
            ("Q", "operation areaNormalIntegrate; fields (U);"),
            ("M", "operation weightedAreaIntegrate; weightField U; fields (rho);"),
            ("H", "operation weightedAreaIntegrate; weightFields (rho U); fields (T);"),
        ]))
    patches = []
    for p in ("inlet", "outlet"):
        patches.append(f"""    {p}Phi
    {{
        type surfaceFieldValue; libs (fieldFunctionObjects); region air;
        regionType patch; name {p}; operation sum; fields (phi);
        writeFields false; {EVERY}
    }}
    {p}PhiT
    {{
        type surfaceFieldValue; libs (fieldFunctionObjects); region air;
        regionType patch; name {p}; operation weightedSum; weightField phi; fields (T);
        writeFields false; {EVERY}
    }}""")
    nl = "\n"
    return f"""FoamFile {{ version 2.0; format ascii; class dictionary; object controlDict; }}
// Written by scripts/make_case.py. Steady: a "time" step is one SIMPLE iteration.
// Allrun runs it to endTime, then raises endTime for the energy-only stage.
application     chtMultiRegionSimpleFoam;
startFrom       latestTime;
startTime       0;
stopAt          endTime;
endTime         {end};
deltaT          1;
writeControl    timeStep;
writeInterval   {end};
purgeWrite      0;
writeFormat     binary;
writePrecision  8;
timeFormat      general;
runTimeModifiable false;
functions
{{
    cpuT
    {{
        type surfaceFieldValue; libs (fieldFunctionObjects); region heatsink;
        regionType patch; name cpu; operation areaAverage; fields (T);
        writeFields false; {EVERY}
    }}
    cpuTmax
    {{
        type surfaceFieldValue; libs (fieldFunctionObjects); region heatsink;
        regionType patch; name cpu; operation max; fields (T);
        writeFields false; {EVERY}
    }}
    sinkT
    {{
        type volFieldValue; libs (fieldFunctionObjects); region heatsink;
        operation max; fields (T);
        writeFields false; {EVERY}
    }}
    wallQ
    {{
        type wallHeatFlux; libs (fieldFunctionObjects); region air; patches (air_to_heatsink);
        executeControl timeStep; executeInterval 10; writeControl writeTime; log false;
    }}
{nl.join(patches)}
{nl.join(planes)}
}}
"""


def decompose(n):
    return f"""FoamFile {{ version 2.0; format ascii; class dictionary; object decomposeParDict; }}
numberOfSubdomains {n};
method scotch;
"""


def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "base"
    if variant not in VARIANTS:
        sys.exit(f"variant must be one of {', '.join(VARIANTS)}")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "runs", variant)
    nproc = int(os.environ.get("NP", "4"))
    v = dict(VARIANTS[variant], name=variant)
    if os.path.exists(out):
        shutil.rmtree(out)
    shutil.copytree(os.path.join(ROOT, "case"), out)
    bm, cells = block_mesh(v)
    files = {
        "system/blockMeshDict": bm,
        "system/topoSetDict": topo_set(),
        "system/controlDict": control_dict(FLOW_ITERS),
        "stages": f"{FLOW_ITERS} {FLOW_ITERS + ENERGY_ITERS}\n",
    }
    # decomposePar -allRegions reads each region's own copy
    for d in ("system", "system/air", "system/heatsink"):
        files[d + "/decomposeParDict"] = decompose(nproc)
    for k, txt in files.items():
        with open(os.path.join(out, k), "w") as f:
            f.write(txt)
    open(os.path.join(out, "case.foam"), "w").close()
    print(f"{out}: {variant}, {cells} cells before the split, {FLOW_ITERS} + {ENERGY_ITERS} iterations, {nproc} cores")


if __name__ == "__main__":
    main()
