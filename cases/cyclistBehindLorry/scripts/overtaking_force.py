#!/usr/bin/env python3
"""The air on the rider as the lorry overtakes him, read off the overtaking run's lines:
the sideways wind at his shoulders, and the air's force on him, estimated quasi-steadily.

He is not in the solve. The run is the lorry alone in its own frame, and he is a probe
moving backwards past its side at the speed difference. Its riderLines
(postProcessing/riderLines/<t>/l_y*_z*_p_U.csv, x -40..36.5 m every 5 cm, every write over
4-8 s) give the air at his centreline y = -3.0 m (1.5 m from the lorry's side to the end
of his handlebar) at knee, hip and shoulder heights (z 0.6, 1.0 and 1.3 m), and at y =
-2.25 and -4.0 m (gaps of 0.75 and 2.5 m).

- **His path.** The lorry does 80 km/h and he rides at 20 km/h, so in the lorry's frame
  his shoulders move at -60 km/h: x = 31.5 m (15 m ahead of the cab's front, which is at
  16.5 m; the doors are at 0) at t = 4 s, to 35.2 m behind the doors at 8 s.
- **The sideways wind** is U_y at his shoulders (+ towards the lorry), the same over the
  road as in the lorry's frame.
- **The air relative to him** is u_rel = U + (V, 0, 0), V the closing speed. Far from the
  lorry that is his own 20 km/h headwind.
- **Over his body, not at one point.** His side silhouette (geometry/rider.stl and
  bike_wheels.stl, 2.5 mm cells) is cut into three height bands, one per line: below
  0.8 m (the knee line), 0.8-1.15 m (hip) and above 1.15 m (shoulder), and along x into
  the lines' 5 cm points. Each cell takes u_rel from its band's line at its own x, weighted
  by its share of the silhouette. The fore-aft force weights the bands by their share of
  the frontal silhouette instead.
- **The force**, per cell and summed: F_i = 0.5 rho |u_rel| u_rel,i CA_i, with the drag
  areas in FORCE_AREAS (sources there). + x is forwards, + y towards the lorry, + z up.

The clip's readout is the mean over the six writes (0.05 s of flow) up to each update,
updated every sixth write; the `shown` columns are that mean.

    python3 scripts/overtaking_force.py runs/overtaking > results/overtaking_summary.txt

writes results/overtaking_force.csv and results/overtaking_side_wind.csv. Reading the
4,329 line files takes a minute or two; --cache <file.npz> keeps them for the next run.
"""
import argparse
import glob
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

CASE = Path(__file__).resolve().parent.parent
GEO = CASE / "geometry"
EVERY = 6                      # the readout's update, in writes
RHO = 1.225                    # the solve's rhoInf (config_overtaking.sh)
LORRY = 22.2                   # m/s, 80 km/h: the solve's U
CAB_FRONT = 16.5               # m; the doors are at x = 0
LINE_Z = (0.6, 1.0, 1.3)       # the line heights; band edges halfway between
BAND_EDGES = (0.8, 1.15)
LINE_Y = (-2.25, -3.0, -4.0)
GRID = np.round(np.linspace(-40.0, 36.5, 1531), 4)   # the lines' 5 cm points
CELL = 0.0025                  # silhouette raster, metres

# His path through the lorry's frame: his shoulders at X0 at T0, moving back at the
# closing speed, 60 km/h (an 80 km/h lorry, a 20 km/h rider: Llorca, Angel-Domenech,
# Agustin-Gomez & Garcia, Safety Science 92 (2017) 302-310, recorded overtakings of riders
# at 15-25 km/h on rural roads).
RIDER = {"x0": 31.5, "t0": 4.0, "closing_speed": 16.6667, "y": -3.0}

# Drag areas, m^2. Fintelman, "Influence of cycling position and crosswinds on performance
# and aerodynamics", PhD thesis, University of Birmingham, 2015 (etheses.bham.ac.uk/6407):
# a mannequin in the drops on a road bike at a 24 deg torso angle (this rider: 25.6 deg),
# coefficients on 0.55 m^2. Measured CFX at 0 deg yaw 0.61 (0.56 at 16 deg), Table 8.1:
# 0.34 m^2. Measured CFY at 45 deg 1.01, Table 8.1: 0.56 m^2, which is CA_y sin 45 in this
# model, so CA_y = 0.79 m^2; RANS at 90 deg gives CFY 1.235-1.430 (Table D.2), 0.68-0.79
# m^2, and RANS under-predicts the side force at 45 deg by 18% (p. 139). There is no
# published vertical drag area for a cyclist: CA_z is his plan area (0.36 m^2,
# body_weights) times 1.0, the order of a bluff body's drag broadside on. An assumption,
# varied 0.5-1.2 times in scripts/overtaking_sensitivity.py.
FORCE_AREAS = {"x": 0.34, "y": 0.79, "z": 0.36}


def shoulder_x_own():
    """His shoulders' x in the rider's own coordinates (front tyre at 0), from the build:
    0.754 m behind the front tyre. Rounded to 0.1 mm, as the clip used it."""
    b = json.loads((GEO / "rider_build.json").read_text())
    return round(b["shoulder_centre_m"][0], 4)


def silhouettes():
    """Side (x-z), front (y-z) and top (x-y) silhouettes of the rider and bike, as boolean
    rasters at CELL, each with its lower-left corner."""
    import pyvista as pv
    m = pv.read(GEO / "rider.stl").merge(pv.read(GEO / "bike_wheels.stl"))
    m = m.extract_surface(algorithm="dataset_surface").triangulate()
    pts = np.asarray(m.points)
    tri = np.asarray(m.faces).reshape(-1, 4)[:, 1:]
    out = {}
    for name, (a, b) in {"side": (0, 2), "front": (1, 2), "top": (0, 1)}.items():
        lo = (pts[:, a].min(), pts[:, b].min())
        nw = int(np.ceil((pts[:, a].max() - lo[0]) / CELL)) + 1
        nh = int(np.ceil((pts[:, b].max() - lo[1]) / CELL)) + 1
        im = Image.new("1", (nw, nh), 0)
        d = ImageDraw.Draw(im)
        P = np.stack([(pts[:, a] - lo[0]) / CELL, (pts[:, b] - lo[1]) / CELL], axis=1)
        for t in tri:
            d.polygon([tuple(P[i]) for i in t], fill=1)
        out[name] = (np.asarray(im, dtype=bool), lo)
    return out


def body_weights(sx):
    """Per band (3) and per x offset from his shoulders: the side-area weights w[b, j]
    (summing to 1), the frontal shares f[b] (summing to 1), the x offsets, and the areas."""
    sil = silhouettes()
    side, (sx0, sz0) = sil["side"]
    front, (fy0, fz0) = sil["front"]
    top, _ = sil["top"]
    zc_side = sz0 + (np.arange(side.shape[0]) + 0.5) * CELL
    zc_front = fz0 + (np.arange(front.shape[0]) + 0.5) * CELL
    xc = sx0 + (np.arange(side.shape[1]) + 0.5) * CELL - sx
    band_s = np.digitize(zc_side, BAND_EDGES)
    band_f = np.digitize(zc_front, BAND_EDGES)
    xs = np.round(np.arange(np.floor(xc.min() / 0.05), np.ceil(xc.max() / 0.05) + 1) * 0.05, 3)
    w = np.zeros((3, len(xs)))
    jx = np.clip(np.round((xc - xs[0]) / 0.05).astype(int), 0, len(xs) - 1)
    for b in range(3):
        np.add.at(w[b], jx, side[band_s == b].sum(axis=0))
    w /= w.sum()
    f = np.array([front[band_f == b].sum() for b in range(3)], float)
    areas = {"side": side.sum() * CELL ** 2, "front": front.sum() * CELL ** 2,
             "top": top.sum() * CELL ** 2}
    return w, f / f.sum(), xs, areas


def write_dirs(run):
    return sorted((d for d in glob.glob(f"{run}/postProcessing/riderLines/*")
                   if Path(d).is_dir()), key=lambda d: float(Path(d).name))


def line_name(y, z):
    def tag(v):
        return f"{v:g}".replace(".", "p")
    return f"l_ym{tag(abs(y))}_z{tag(z)}_p_U.csv"


def on_grid(xa, Ua):
    """A line's samples onto GRID. A point on a cell face is written twice, once for each
    cell, so a line has a few repeated x (1535-1537 rows for 1531 points): average them."""
    xu, inv = np.unique(np.round(xa, 4), return_inverse=True)
    Um = np.zeros((len(xu), 3))
    np.add.at(Um, inv, Ua)
    Um /= np.bincount(inv)[:, None]
    return np.stack([np.interp(GRID, xu, Um[:, c]) for c in range(3)], 1)


def load_lines(run, cache=None):
    """All writes of the nine lines -> times (n), x (1531), U[n, y, z, x, 3]."""
    if cache and Path(cache).exists():
        q = np.load(cache)
        return q["times"], q["x"], q["U"]
    times, U = [], []
    for d in write_dirs(run):
        times.append(float(Path(d).name))
        block = []
        for y in LINE_Y:
            row = []
            for z in LINE_Z:
                a = np.loadtxt(Path(d) / line_name(y, z), delimiter=",", skiprows=1)
                row.append(on_grid(a[:, 0], a[:, 2:5]))     # columns x, p, U_0, U_1, U_2
            block.append(row)
        U.append(block)
    times, U = np.array(times), np.array(U)
    if cache:
        np.savez(cache, times=times, x=GRID, U=U)
    return times, GRID, U


def path_x(times, r=RIDER):
    return r["x0"] - r["closing_speed"] * (times - r["t0"])


def forces(times, x, U, r=RIDER, areas=FORCE_AREAS, closing=None, weights=None, iy=1,
           y_spread=None):
    """Raw force per write, [n, 3] in N, for one set of assumptions.

    weights = (w, f, xs) from body_weights. closing overrides the closing speed (his own
    speed changes it, the lorry's being fixed). iy picks the line (0: y -2.25, 1: -3.0,
    2: -4.0). y_spread = (half-width, n) averages the force across his width by
    interpolating quadratically between the three lines.
    """
    w, f, xs = weights
    V = r["closing_speed"] if closing is None else closing
    xr = path_x(times, r)                                      # the path, as the clip draws it
    CA = np.array([areas["x"], areas["y"], areas["z"]])
    F = np.zeros((len(times), 3))
    ys = [0.0] if not y_spread else np.linspace(-y_spread[0], y_spread[0], y_spread[1])
    for k in range(len(times)):
        X = xr[k] + xs                                         # cell x in the lorry's frame
        acc = np.zeros(3)
        for dy in ys:
            for b in range(3):
                if dy == 0.0:
                    Ub = np.stack([np.interp(X, x, U[k, iy, b, :, c]) for c in range(3)], 1)
                else:
                    yy = LINE_Y[iy] + dy
                    Ul = np.stack([np.stack([np.interp(X, x, U[k, j, b, :, c]) for c in range(3)], 1)
                                   for j in range(3)])
                    L = [np.prod([(yy - LINE_Y[m]) / (LINE_Y[j] - LINE_Y[m])
                                  for m in range(3) if m != j]) for j in range(3)]
                    Ub = sum(L[j] * Ul[j] for j in range(3))
                u = Ub + np.array([V, 0.0, 0.0])
                q = np.linalg.norm(u, axis=1)[:, None] * u      # |u| u per cell
                fx = f[b] * (w[b] / max(w[b].sum(), 1e-12)) @ q[:, 0]
                acc += np.array([fx, w[b] @ q[:, 1], w[b] @ q[:, 2]])
        F[k] = 0.5 * RHO * CA * acc / len(ys)
    return F


def shown(raw):
    """The readout: at each write, the mean of the six writes up to the last update."""
    out = np.empty_like(raw)
    for k in range(len(raw)):
        k_upd = k - k % EVERY
        out[k] = raw[max(0, k_upd - EVERY + 1):k_upd + 1].mean(axis=0)
    return out


def side_wind(run, times, r=RIDER, line="l_ym3_z1p3_p_U.csv"):
    """The sideways wind at his shoulders per write, km/h (+ towards the lorry), straight
    off the shoulder line at his x."""
    raw = []
    for d, t in zip(write_dirs(run), times):
        z = np.genfromtxt(Path(d) / line, delimiter=",", names=True)
        x = r["x0"] - r["closing_speed"] * (t - r["t0"])
        if not z["x"][0] <= x <= z["x"][-1]:
            raise SystemExit(f"rider at x = {x:.2f} m is off the line at t = {t}")
        raw.append(float(np.interp(x, z["x"], z["U_1"])) * 3.6)
    return np.array(raw)


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("run", nargs="?", default=str(CASE / "runs" / "overtaking"))
    p.add_argument("--out", default=str(CASE / "results"))
    p.add_argument("--cache", default=None)
    a = p.parse_args()
    times, x, U = load_lines(a.run, a.cache)
    xr = path_x(times)
    behind = CAB_FRONT - xr
    w, f, xs, ar = body_weights(shoulder_x_own())
    if (xr + xs[-1]).max() > x[-1] or (xr + xs[0]).min() < x[0]:
        raise SystemExit("his body runs off the lines")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    # The sideways wind.
    wind = side_wind(a.run, times)
    wsh = shown(wind[:, None])[:, 0]
    with open(out / "overtaking_side_wind.csv", "w") as fh:
        fh.write("t_s,shoulders_x_m,behind_cab_front_m,side_wind_kmh,shown_kmh\n")
        for k in range(len(times)):
            fh.write(f"{times[k]:.7g},{xr[k]:.4f},{behind[k]:.4f},{wind[k]:.3f},"
                     f"{int(round(wsh[k]))}\n")
    print("Sideways wind at his shoulders (+ towards the lorry), 1.5 m gap")
    i_out, i_in = int(np.argmin(wind)), int(np.argmax(wind))
    print(f"  per write: away {-wind[i_out]:.1f} km/h with the cab's front {behind[i_out]:+.2f} m "
          f"behind him; towards {wind[i_in]:.1f} km/h at {behind[i_in]:.2f} m behind the cab's "
          f"front ({behind[i_in] - CAB_FRONT:+.2f} m from the doors)")
    sign = np.sign(np.where(np.abs(wsh) < 0.5, 0, wsh))
    runs, cur = [], None
    for k, s_ in enumerate(sign):
        if s_ != cur:
            runs.append([s_, k, k])
            cur = s_
        runs[-1][2] = k
    print("  as shown (0.05 s means), by where his shoulders are, in m behind the cab's front:")
    for s_, k0, k1 in runs:
        what = {1: "towards", -1: "away", 0: "under 0.5 km/h"}[int(s_)]
        print(f"    {behind[k0]:6.2f} to {behind[k1]:6.2f}: {what}, peak "
              f"{np.abs(wsh[k0:k1 + 1]).max():.1f} km/h")

    # The force.
    F = forces(times, x, U, weights=(w, f, xs))
    sh = shown(F)
    values = np.array([int(round(float(np.hypot(*v[:2])))) for v in sh])
    with open(out / "overtaking_force.csv", "w") as fh:
        fh.write("t_s,shoulders_x_m,behind_cab_front_m,Fx_N,Fy_N,Fz_N,"
                 "Fx_shown_N,Fy_shown_N,Fz_shown_N,in_plane_shown_N\n")
        for k in range(len(times)):
            fh.write(f"{times[k]:.7g},{xr[k]:.4f},{behind[k]:.4f},"
                     + ",".join(f"{v:.3f}" for v in F[k]) + ","
                     + ",".join(f"{v:.3f}" for v in sh[k]) + f",{values[k]}\n")
    print("\nThe air's force on him, N: + x forwards, + y towards the lorry, + z up")
    print(f"  silhouettes: side {ar['side']:.3f} m^2, front {ar['front']:.3f}, top {ar['top']:.3f}; "
          f"side shares (knee, hip, shoulder bands) {np.round(w.sum(1), 3).tolist()}, "
          f"frontal shares {np.round(f, 3).tolist()}")
    print(f"  before the lorry (first write): {F[0].round(2).tolist()}")
    ia, it = int(np.argmin(F[:, 1])), int(np.argmax(F[:, 1]))
    hp = np.hypot(F[:, 0], F[:, 1])
    ih = int(np.argmax(hp))
    print(f"  per write: sideways away {-F[ia, 1]:.1f} with the cab's front {behind[ia]:+.2f} m "
          f"behind him; towards {F[it, 1]:.1f} at {behind[it]:.2f} m behind the cab's front; "
          f"in-plane peak {hp[ih]:.1f} {F[ih].round(1).tolist()} at {behind[ih]:+.2f} m; "
          f"vertical {F[:, 2].min():+.2f} to {F[:, 2].max():+.2f}")
    print(f"  push and pull peaks {behind[it] - behind[ia]:.1f} m apart")
    print(f"  as shown: in-plane {values.min()} to {values.max()}; sideways "
          f"{sh[:, 1].min():+.1f} to {sh[:, 1].max():+.1f}; fore-aft {sh[:, 0].min():+.1f} to "
          f"{sh[:, 0].max():+.1f}")
    print(f"  fore-aft per write {F[:, 0].min():+.1f} to {F[:, 0].max():+.1f}: never forwards")
    for b, zname in enumerate(("knee", "hip", "shoulder")):
        ux = np.array([np.interp(xr[k], x, U[k, 1, b, :, 0]) for k in range(len(times))]) + LORRY
        print(f"  air along the road at his {zname} line ({LINE_Z[b]} m): "
              f"{ux.min() * 3.6:+.1f} to {ux.max() * 3.6:+.1f} km/h (+ with the lorry)")
    for thr in (10, 14):
        idx = np.where(-F[:, 1] >= thr)[0]
        print(f"  sideways push above {thr} N for {(idx[-1] - idx[0] + 1) / 120:.3f} s of flow")


if __name__ == "__main__":
    main()
