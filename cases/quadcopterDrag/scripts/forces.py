#!/usr/bin/env python3
"""Drag per part and in total, from the forces simpleFoam wrote.

    python3 scripts/forces.py [run]

Reads run/postProcessing/force_<part>/0/force.dat for body, arms, cans, hubs, legs and
total, resolves each force along the wind (drag) and at right angles to it, up (vertical),
and averages over the iterations after run/case.json's average_from. Prints the table and
writes run/forces_summary.json.

The +- column is the standard deviation of the drag over the averaging window: how much
the steady solve still wanders, not an error bar on the physics. The drift column is the
mean of the window's second half minus that of its first half.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

case = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "run")
cfg = json.load(open(case / "case.json"))
Q = 0.5 * cfg["rho"] * cfg["U_mag"] ** 2
DRAG, LIFT = np.array(cfg["drag_dir"]), np.array(cfg["lift_dir"])


def history(name):
    rows = []
    for d in sorted((case / "postProcessing" / f"force_{name}").iterdir(), key=lambda p: float(p.name)):
        for line in (d / "force.dat").read_text().splitlines():
            if not line.startswith("#"):
                rows.append([float(x) for x in re.sub(r"[()]", " ", line).split()[:10]])
    a = np.array(rows)
    _, keep = np.unique(a[:, 0], return_index=True)
    return a[keep]


tot = history("total")
last = int(tot[-1, 0])
if last < cfg["iterations"]:
    print(f"WARNING: the solve stopped at iteration {last} of {cfg['iterations']}")
start = cfg["average_from"]
print(f"\n{case.name}: {last} iterations, drag averaged over iterations {start + 1} to {last}")
print(f"wind {cfg['U_mag']} m/s at {cfg['pitch_deg']} deg nose-down, q = {Q:.2f} Pa\n")
print(f"{'part':6s} {'drag N':>8s} {'+-':>7s} {'drift':>7s} {'share':>6s} {'vert N':>8s} "
      f"{'CdA cm2':>8s} {'pressure':>9s}")
out = {"iterations": last, "average_from": start, "q_Pa": Q, "parts": {}}
total_drag = None
for name in cfg["parts"] + ["total"]:
    h = tot if name == "total" else history(name)
    w = h[h[:, 0] > start]
    drag = w[:, 1:4] @ DRAG
    half = len(drag) // 2
    dm = float(drag.mean())
    if name == "total":
        total_drag = dm
    out["parts"][name] = r = {
        "drag_N": dm, "drag_std_N": float(drag.std()),
        "drift_N": float(drag[half:].mean() - drag[:half].mean()),
        "vertical_N": float((w[:, 1:4] @ LIFT).mean()),
        "CdA_m2": dm / Q,
        "pressure_share": float((w[:, 4:7] @ DRAG).mean() / dm)}
parts_sum = sum(out["parts"][p]["drag_N"] for p in cfg["parts"])
for name in cfg["parts"] + ["total"]:
    r = out["parts"][name]
    r["share"] = r["drag_N"] / total_drag
    print(f"{name:6s} {r['drag_N']:8.3f} {r['drag_std_N']:7.3f} {r['drift_N']:+7.3f} "
          f"{r['share']*100:5.1f}% {r['vertical_N']:+8.3f} {r['CdA_m2']*1e4:8.1f} "
          f"{r['pressure_share']*100:8.1f}%")
print(f"\nsum of the parts {parts_sum:.3f} N against the total {total_drag:.3f} N")
print("vertical force is at right angles to the wind, positive up; negative is a download")

res = case / "postProcessing" / "residuals"
if res.is_dir():
    f = sorted(res.glob("*/solverInfo.dat"), key=lambda p: float(p.parent.name))[-1]
    lines = f.read_text().splitlines()
    head = [l for l in lines if l.startswith("# Time")][-1].lstrip("#").split()
    vals = lines[-1].split()
    init = {k.replace("_initial", ""): float(vals[i]) for i, k in enumerate(head) if k.endswith("_initial")}
    out["final_initial_residuals"] = init
    print("initial residuals at the last iteration: "
          + "  ".join(f"{k} {v:.1e}" for k, v in init.items()))

json.dump(out, open(case / "forces_summary.json", "w"), indent=2)
print(f"wrote {case / 'forces_summary.json'}")
