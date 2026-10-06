#!/usr/bin/env python3
"""The aio layouts' settled statistics and heat budget -> results/aio_summary.csv, and where
across the case's depth each filter mesh passes air at 8 s -> results/aio_vent_depth.csv.

For each of runs/aioFrontIn and runs/aioFrontBottomIn that has been solved, over the settled
window (6-8 s), from the monitors make_case.py writes for these layouts:

- the air entering the card (gpuIntake) and the radiator (radiatorBoundaryTemperature, the
  three top fans' flow-weighted air), as rises above the room, over the window, over each
  half of it, and its standard deviation;
- the case's mean gauge pressure;
- each panel opening's one-way flows, in and out separately, from sum(phi) and sumMag(phi);
- the heat carried out through every fan and opening, rho cp sum(phi (T - T_room)), outward
  positive, and their sum, which should be the card's 300 W: the radiator is outside the air
  volume, so the CPU's 150 W never enters the case air.

Means over the window are taken on a 2 ms grid, the 0.02 s records interpolated linearly.

Then, from the 8 s fields (the only full fields written after the start), each filter mesh's
flow split into 30 mm bands across the case's depth (z), out and in separately. The card-middle
section is at z = 0.082 m and the fan column (120 mm fans centred at z = 0.105 m) spans
z 0.045-0.165 m, so this shows how much of each mesh's flow passes beside the fans, off the
section. Needs PyVista with its OpenFOAM reader.

    python3 scripts/summarize_aio.py [--runs runs]
"""
import argparse
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[1]
C = json.loads((R / "config/model.json").read_text())
LAYOUTS = [x for x in C["layouts"] if C["layouts"][x].get("geometry") == "aio"]
T_ROOM, RHO, CP = C["roomTemperature_K"], C["rhoReference_kg_m3"], C["cp_J_kgK"]
LO, HI = C["settledWindow_s"]
OPENINGS = ("vent_front", "vent_top", "vent_slots")
FANS = ("fan_front_low", "fan_front_mid", "fan_front_high", "fan_rear", "fan_top_front",
        "fan_top_mid", "fan_top_rear", "fan_bottom_front", "fan_bottom_rear")


def record(run, name):
    d = Path(run) / "postProcessing" / name
    f = next(d.glob("*/surfaceFieldValue.dat"), None) or next(d.glob("*/volFieldValue.dat"))
    return np.loadtxt(f, comments="#")


def window(t, v, lo, hi):
    """Mean over [lo, hi] of a record sampled every 0.02 s, on a 2 ms grid."""
    tg = np.arange(lo, hi + 1e-9, 0.002)
    return float(np.interp(tg, t, v).mean())


def settled(run):
    row = {}
    for part, rec in (("card", "gpuIntake"), ("radiator", "radiatorBoundaryTemperature")):
        g = record(run, rec)
        t, rise = g[:, 0], g[:, 1] - T_ROOM
        row[f"{part}_intake_rise_K"] = round(window(t, rise, LO, HI), 3)
        row[f"{part}_intake_rise_first_half_K"] = round(window(t, rise, LO, (LO + HI) / 2), 3)
        row[f"{part}_intake_rise_second_half_K"] = round(window(t, rise, (LO + HI) / 2, HI), 3)
        row[f"{part}_intake_rise_std_K"] = round(float(rise[(t >= LO) & (t <= HI)].std()), 3)
        row[f"{part}_intake_C"] = round(window(t, rise, LO, HI) + T_ROOM - 273.15, 2)
    p = record(run, "casePressure")
    # the record is kinematic (volAverage(p), m2/s2); times rho for Pa
    row["case_gauge_pressure_Pa"] = round(RHO * window(p[:, 0], p[:, 1], LO, HI), 4)
    for o in OPENINGS:
        net, mag = record(run, f"{o}_net"), record(run, f"{o}_absolute")
        t = net[:, 0]
        row[f"{o}_in_L_s"] = round(1000 * window(t, 0.5 * (mag[:, 1] - net[:, 1]), LO, HI), 2)
        row[f"{o}_out_L_s"] = round(1000 * window(t, 0.5 * (mag[:, 1] + net[:, 1]), LO, HI), 2)
    heat = {}
    for n in FANS + OPENINGS:
        if not (Path(run) / "postProcessing" / f"heatFlow_{n}").exists():
            continue        # the bottom fans in aioFrontIn are walls
        q, qt = record(run, f"heatFlow_{n}"), record(run, f"heatPhiT_{n}")
        heat[n] = round(window(q[:, 0], RHO * CP * (qt[:, 1] - T_ROOM * q[:, 1]), LO, HI), 2)
    for n in FANS + OPENINGS:
        row[f"{n}_heat_out_W"] = heat.get(n, np.nan)
    row["heat_out_net_W"] = round(sum(heat.values()), 2)
    return row


def vent_depth(run, time=8):
    """Each mesh patch's flow at `time`, split into 30 mm bands of z, in L/s."""
    import pyvista as pv
    tmp = Path(tempfile.mkdtemp(prefix="aio_depth_"))
    for d in ("constant", "system", str(time)):
        os.symlink(Path(run).resolve() / d, tmp / d)
    (tmp / "c.foam").touch()
    r = pv.OpenFOAMReader(str(tmp / "c.foam"))
    r.disable_all_point_arrays()
    r.enable_all_patch_arrays()
    r.disable_patch_array("internalMesh")
    r.disable_all_cell_arrays()
    r.enable_cell_array("U")
    r.set_active_time_value(float(time))
    b = r.read()["boundary"]
    rows = []
    for v in OPENINGS:
        s = b[v].extract_surface(algorithm="dataset_surface").compute_normals(
            cell_normals=True, point_normals=False, auto_orient_normals=False,
            consistent_normals=False, split_vertices=False)
        A = s.compute_cell_sizes(length=False, volume=False)["Area"]
        q = np.einsum("ij,ij->i", s.cell_data["U"], s.cell_data["Normals"]) * A
        z = s.cell_centers().points[:, 2]
        rows.append(dict(opening=v, z_from_m="all", z_to_m="all",
                         out_L_s=round(1000 * float(q[q > 0].sum()), 2),
                         in_L_s=round(-1000 * float(q[q < 0].sum()), 2)))
        for z0 in np.arange(0.0, 0.21, 0.03):
            m = (z >= z0) & (z < z0 + 0.03)
            if m.any():
                rows.append(dict(opening=v, z_from_m=f"{z0:.2f}", z_to_m=f"{z0 + 0.03:.2f}",
                                 out_L_s=round(1000 * float(q[m & (q > 0)].sum()), 2),
                                 in_L_s=round(-1000 * float(q[m & (q < 0)].sum()), 2)))
    for p in tmp.iterdir():
        p.unlink()
    tmp.rmdir()
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--runs", default=str(R / "runs"))
    a = p.parse_args()
    rows, depth = [], []
    for L in LAYOUTS:
        run = Path(a.runs) / L
        if not (run / "postProcessing").is_dir():
            continue
        rows.append(dict(layout=L, window_s=f"{LO:g}-{HI:g}", **settled(run)))
        if (run / "8").is_dir():
            depth += [dict(layout=L, **r) for r in vent_depth(run)]
    (R / "results").mkdir(exist_ok=True)
    s = pd.DataFrame(rows)
    s.to_csv(R / "results/aio_summary.csv", index=False)
    print(s.T.to_string())
    if depth:
        pd.DataFrame(depth).to_csv(R / "results/aio_vent_depth.csv", index=False)
        print(pd.DataFrame(depth).to_string(index=False))


if __name__ == "__main__":
    main()
