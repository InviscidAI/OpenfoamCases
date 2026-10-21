#!/usr/bin/env python3
"""Figures from the two runs of underfloorVsRadiator.

    python3 scripts/extract_results.py <runs dir> <results dir>

Reads each run's per-step monitors (postProcessing/<monitor>/<start>/*.dat, joined over
restarts with the later start winning) and writes

  <results>/<run>/history.csv   every 2.5 s, at the planes' writes: the occupied zone's mean
                                air temperature at 0.1, 0.6, 1.1 and 1.7 m and the head-to-ankle
                                difference, the room's mean, the glass's and the floor's mean
                                surface temperature and the floor's warmest face, the heat
                                through each boundary and the heat budget's gap
  <results>/summary.txt         the figures the README quotes

The head-to-ankle difference is EN 16798-1 and ISO 7730's vertical air temperature
difference for a seated person, taken as the occupied zone's mean air temperature at 1.1 m
less that at 0.1 m (the occ_head and occ_ankle monitors: volume means over the cells 1.0-3.7 m
from the window wall and more than 0.3 m from the side walls, within 0.02 m of each height).

The heat budget: the room is closed, so its internal energy, (cv/R) times the integral of
p dV for a perfect gas (energyCheck, every step), changes at the radiator's 60 W (radiator run
only; the floor's 60 W is the floor patch's heat) plus the heat through every patch
(wallHeatFlux, every step, positive from the wall into the air). The rate of change is taken
over 3.75 s centred on each step.

If PyVista is installed, it also reads the mid plane (z = 0.005 m) at 1200 s and adds its
vertical profiles at x = 1, 2 and 3 m to the summary.
"""
import glob
import gzip
import os
import sys
import tempfile

import numpy as np

R = 8314.47 / 28.96
CV = 1005.0 - R
HEAT = 60.0
H_GLASS, T_OUT = 4.403, 273.15
K = 273.15
HEIGHTS = (("ankle", 0.1), ("knee", 0.6), ("head", 1.1), ("standing", 1.7))
PATCHES = ("glass", "floor", "ceiling", "innerWall", "sideWalls", "windowWall")
WINDOW = 3.75
DT_PLANES = 2.5


def table(run, fo, fname):
    rows = []
    for d in sorted(glob.glob(f"{run}/postProcessing/{fo}/*"), key=lambda p: float(os.path.basename(p))):
        f = f"{d}/{fname}"
        if not os.path.exists(f):
            continue
        a = np.loadtxt(f, comments="#", ndmin=2)
        if rows:
            rows = [r[r[:, 0] < a[0, 0]] for r in rows]
        rows.append(a)
    return np.vstack(rows)


def wall_heat(run):
    """{patch: (t, W)} from wallHeatFlux, every step."""
    out = {}
    starts = sorted(glob.glob(f"{run}/postProcessing/wallHeatFlux/*"), key=lambda p: float(os.path.basename(p)))
    for d in starts:
        rows = {}
        for line in open(f"{d}/wallHeatFlux.dat"):
            if line.startswith("#") or not line.strip():
                continue
            t, patch, _mn, _mx, integ = line.split()[:5]
            rows.setdefault(patch, []).append((float(t), float(integ)))
        for patch, v in rows.items():
            v = np.array(v)
            if patch in out:
                old = out[patch]
                out[patch] = np.vstack([old[old[:, 0] < v[0, 0]], v])
            else:
                out[patch] = v
    return out


def tmean(t, y, lo, hi):
    """Time mean of y over [lo, hi] (trapezoid on the per-step samples)."""
    ts = np.concatenate([[lo], t[(t > lo) & (t < hi)], [hi]])
    ys = np.interp(ts, t, y)
    return np.trapezoid(ys, ts) / (hi - lo) if hasattr(np, "trapezoid") else np.trapz(ys, ts) / (hi - lo)


def tstd(t, y, lo, hi):
    m = tmean(t, y, lo, hi)
    return np.sqrt(tmean(t, (y - m) ** 2, lo, hi))


def read_run(run):
    d = {}
    e = table(run, "energyCheck", "volFieldValue.dat")
    d["t_e"], d["U"] = e[:, 0], CV / R * e[:, 1]
    for name, _ in HEIGHTS:
        o = table(run, f"occ_{name}", "volFieldValue.dat")
        d[name] = (o[:, 0], o[:, 1] - K)
    rm = table(run, "roomMeanT", "volFieldValue.dat")
    d["room"] = (rm[:, 0], rm[:, 1] - K)
    gl = table(run, "surfaceT", "surfaceFieldValue.dat")
    d["glassT"] = (gl[:, 0], gl[:, 1] - K)
    gi = table(run, "glassIntT", "surfaceFieldValue.dat")
    d["glassLoss"] = (gi[:, 0], H_GLASS * (gi[:, 1] - T_OUT * 1.2))
    fl = table(run, "floorT", "surfaceFieldValue.dat")
    d["floorT"] = (fl[:, 0], fl[:, 1] - K)
    fm = table(run, "floorTmax", "surfaceFieldValue.dat")
    d["floorTmax"] = (fm[:, 0], fm[:, 1] - K)
    d["q"] = wall_heat(run)
    d["heat"] = HEAT if "radiator" in open(f"{run}/constant/fvOptions").read() else 0.0
    ta, ya = d["ankle"]
    th, yh = d["head"]
    assert np.array_equal(ta, th), "occ_head and occ_ankle were not written at the same steps"
    d["diff"] = (ta, yh - ya)
    return d


def budget(d):
    """dU/dt over WINDOW and the gap against the source plus the walls, at every wallHeatFlux step."""
    t, U = d["t_e"], d["U"]
    tq = d["q"]["glass"][:, 0]
    walls = sum(np.interp(tq, v[:, 0], v[:, 1]) for v in d["q"].values())
    ok = (tq - WINDOW / 2 >= t[0]) & (tq + WINDOW / 2 <= t[-1])
    tq, walls = tq[ok], walls[ok]
    dudt = (np.interp(tq + WINDOW / 2, t, U) - np.interp(tq - WINDOW / 2, t, U)) / WINDOW
    return tq, dudt, d["heat"] + walls, dudt - (d["heat"] + walls)


def at(series, tt):
    t, y = series
    return np.interp(tt, t, y)


def write_history(d, path):
    tend = d["t_e"][-1]
    tt = np.arange(0, tend + 1e-9, DT_PLANES)
    tq, dudt, src, gap = budget(d)
    cols = [("t_s", tt)]
    for name, y in HEIGHTS:
        cols.append((f"T_{name}_{y:g}m_C", at(d[name], tt)))
    cols += [("head_minus_ankle_K", at(d["diff"], tt)), ("T_room_C", at(d["room"], tt)),
             ("T_glass_surface_C", at(d["glassT"], tt)), ("glass_loss_W", at(d["glassLoss"], tt)),
             ("T_floor_surface_C", at(d["floorT"], tt)), ("T_floor_warmest_face_C", at(d["floorTmax"], tt))]
    for p in PATCHES:
        v = d["q"][p]
        cols.append((f"Q_{p}_W", np.interp(tt, v[:, 0], v[:, 1])))
    inside = (tt >= tq[0]) & (tt <= tq[-1])
    cols.append(("dU_dt_W", np.where(inside, np.interp(tt, tq, dudt), np.nan)))
    cols.append(("budget_gap_W", np.where(inside, np.interp(tt, tq, gap), np.nan)))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(",".join(c for c, _ in cols) + "\n")
        for i in range(len(tt)):
            f.write(",".join(("" if np.isnan(v[i]) else f"{v[i]:.4f}") if c != "t_s" else f"{v[i]:g}"
                             for c, v in cols) + "\n")


def read_vtp(path):
    import pyvista as pv
    if path.endswith(".gz"):
        with tempfile.NamedTemporaryFile(suffix=".vtp") as f:
            f.write(gzip.open(path).read())
            f.flush()
            return pv.read(f.name)
    return pv.read(path)


def profiles(run, t=1200):
    try:
        import pyvista  # noqa: F401
    except ImportError:
        return [f"  (PyVista not installed: no mid-plane profiles)"]
    base = f"{run}/postProcessing/planes/{t:g}/mid.vtp"
    path = base if os.path.exists(base) else base + ".gz"
    if not os.path.exists(path):
        return [f"  (no mid plane at {t:g} s)"]
    m = read_vtp(path)
    c = m.cell_centers().points
    T = np.asarray(m.cell_data["T"]) - K
    U = np.asarray(m.cell_data["U"])
    lines = []
    want = (0.005, 0.029, 0.062, 0.107, 0.165, 0.225, 0.375, 0.525, 0.825, 1.125, 1.425, 1.725, 2.025, 2.385)
    for x in (1.0, 2.0, 3.0):
        xc = c[np.argmin(np.abs(c[:, 0] - x)), 0]
        i = np.abs(c[:, 0] - xc) < 1e-6
        o = np.argsort(c[i, 1])
        y, tc, ux = c[i, 1][o], T[i][o], U[i][o, 0]
        k = [int(np.argmin(np.abs(y - w))) for w in want]
        lines.append(f"  x = {xc:.3f} m  y (m)  " + " ".join(f"{y[j]:6.3f}" for j in k))
        lines.append(f"                 T (C)  " + " ".join(f"{tc[j]:6.2f}" for j in k))
        lines.append(f"                Ux (m/s)" + " ".join(f"{ux[j]:+6.3f}" for j in k))
        # the current along the floor: the cells from the floor up while Ux > 0.03 m/s into the room
        j = 0
        while j < len(y) and ux[j] > 0.03:
            j += 1
        if j:
            lines.append(f"                along the floor faster than 0.03 m/s into the room up to "
                         f"the cell at y = {y[j - 1]:.3f} m; coolest {tc[:j].min():.2f} C at "
                         f"y = {y[int(np.argmin(tc[:j]))]:.3f} m; air at 0.375-2.025 m "
                         f"{tc[(y > 0.3) & (y < 2.1)].min():.2f}-{tc[(y > 0.3) & (y < 2.1)].max():.2f} C")
    return lines


def summary(name, run, d):
    L = [f"{name}"]
    t = d["t_e"]
    log = f"{run}/log.buoyantPimpleFoam"
    wall = ""
    if os.path.exists(log):
        with open(log, "rb") as f:
            f.seek(max(0, os.path.getsize(log) - 4000))
            for line in f.read().decode(errors="replace").splitlines():
                if line.startswith("ExecutionTime"):
                    wall = f", {line.split('ClockTime =')[1].strip()} of wall time"
    L.append(f"  to t = {t[-1]:g} s in {len(t)} steps, mean step {np.diff(t).mean():.4f} s{wall}")
    tq, dudt, src, gap = budget(d)
    L.append(f"  heat budget over {len(gap)} steps ({tq[0]:.2f}-{tq[-1]:.2f} s, dU/dt over {WINDOW:g} s): "
             f"gap mean {gap.mean():+.3f} W, largest {np.abs(gap).max():.2f} W")
    tdf, df = d["diff"]
    L.append("  head (1.1 m) minus ankles (0.1 m), occupied zone, minute means, K:")
    mins = [tmean(tdf, df, 60 * m, 60 * (m + 1)) for m in range(int(t[-1] // 60))]
    for r in range(0, len(mins), 10):
        L.append("    min " + " ".join(f"{60 * m:>4d}-{60 * (m + 1):<4d}" for m in range(r, min(r + 10, len(mins)))))
        L.append("        " + " ".join(f"{v:9.3f}" for v in mins[r:r + 10]))
    te = t[-1]
    L.append(f"    at {te:g} s {np.interp(te, tdf, df):.3f}; mean over the last 60 s {tmean(tdf, df, te - 60, te):.3f}, "
             f"last 300 s {tmean(tdf, df, te - 300, te):.3f} (sd {tstd(tdf, df, te - 300, te):.3f}); "
             f"900-1050 s {tmean(tdf, df, 900, 1050):.3f}, 1050-1200 s {tmean(tdf, df, 1050, 1200):.3f}")
    L.append("    range of the minute means from 120 s: "
             f"{min(mins[2:]):.3f} to {max(mins[2:]):.3f}")
    L.append("  occupied zone, C           " + "  ".join(f"{n} {y:g} m" for n, y in HEIGHTS) + "   room mean")
    for tt in (60, 300, 600, 900, te):
        L.append(f"    at {tt:6g} s             " + "  ".join(f"{at(d[n], tt):{len(n) + len(f'{y:g}') + 3}.2f}" for n, y in HEIGHTS)
                 + f"   {at(d['room'], tt):9.2f}")
    L.append(f"    room mean rose {at(d['room'], te) - at(d['room'], te - 300):.3f} K over the last 300 s")
    L.append(f"  glass inside surface over the last 300 s: mean {tmean(*d['glassT'], te - 300, te):.2f} C "
             f"(range {d['glassT'][1][d['glassT'][0] >= te - 300].min():.2f}-{d['glassT'][1][d['glassT'][0] >= te - 300].max():.2f}); "
             f"loss h (Ts - 0 C) A {tmean(*d['glassLoss'], te - 300, te):.2f} W")
    L.append(f"  floor surface over the last 300 s: mean {tmean(*d['floorT'], te - 300, te):.2f} C, "
             f"warmest face {d['floorTmax'][1][d['floorTmax'][0] >= te - 300].max():.2f} C; "
             f"at {te:g} s mean {at(d['floorT'], te):.2f} C against the room's {at(d['room'], te):.2f} C "
             f"and the ankles' {at(d['ankle'], te):.2f} C")
    L.append(f"  heat, W, mean over {te - 60:g}-{te:g} s (positive into the air):")
    parts = [f"source {d['heat']:.1f}"]
    for p in PATCHES:
        v = d["q"][p]
        parts.append(f"{p} {tmean(v[:, 0], v[:, 1], te - 60, te):+.2f}")
    sel = (tq >= te - 60 - WINDOW) & (tq <= te)
    parts.append(f"stored (dU/dt) {dudt[sel].mean():+.2f}")
    L.append("    " + ", ".join(parts))
    L.append(f"  mid plane (z = 0.005 m) at {te:g} s:")
    L += profiles(run, te)
    return L


def main():
    runs_dir, out = sys.argv[1], sys.argv[2]
    lines = ["underfloorVsRadiator: figures from the two runs (scripts/extract_results.py)", ""]
    for name in ("radiator", "floor"):
        run = f"{runs_dir}/{name}"
        d = read_run(run)
        write_history(d, f"{out}/{name}/history.csv")
        lines += summary(name, run, d) + [""]
    with open(f"{out}/summary.txt", "w") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
