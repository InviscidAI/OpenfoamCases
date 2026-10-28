#!/usr/bin/env python3
"""Write results/ from the solved runs: the vapour monitors' histories, the flows, the budgets,
the outdoor-air tracer, the still outdoor air, the fan's Courant check and the relative humidity
on the clip's section.

    python3 extract_results.py <runs_dir> <results_dir>

<runs_dir> holds shower, fan and window (and fanCo1, if it has been run). Needs NumPy only.

The share of the vapour removed is 1 - W(t)/W(600 s), W the room's integral of the shower's
vapour (the monitor's `water`), each branch over its own 600 s inventory: the fan run's is the
shower's at 600 s, the window run's 1.6 g less, the vapour that sat where the tilted sash's cells
are (README, "The share"). Flows are time-weighted means over each interval of the per-step
monitor. Relative humidity is computed on the section z = 0.455 m (the clip's plane) from each
face's temperature, the shower's vapour s, and in the window run the outdoor air's share f: the
water's mass fraction is q = s + f q_out + (1 - s - f) q_in, q_in 7 g per kg of dry air (room and
hall), q_out 0 C at 95% (outdoors); the vapour's partial pressure is p r/(r + M_w/M_air) with
r = q/(1 - q) at p = 1e5 Pa, over Magnus' 610.94 exp(17.625 t/(t + 243.04)) Pa, the monitor's
own formula. Shares of the section are by face area over the room (face centres at x > 0).
"""
import base64
import csv
import gzip
import re
import sys
from pathlib import Path

import numpy as np

M_W = 18.0153
M_AIR = 1 / (0.2314 / 31.9988 + 0.7686 / 28.0134)     # the runs' O2/N2 air
P = 1e5


def magnus(t):
    return 610.94 * np.exp(17.625 * t / (t + 243.04))


Q_IN = 0.007 / 1.007                                   # 7 g per kg of dry air
_E_OUT = 0.95 * magnus(0.0)
_R_OUT = (M_W / M_AIR) * _E_OUT / (P - _E_OUT)
Q_OUT = _R_OUT / (1 + _R_OUT)                          # 0 C at 95%
DRY_KG_M3_0C = P / (8314.46261815324 / M_AIR * 273.15)  # outdoor air, for volume flows


def rh(T_C, s, f):
    q = s + f * Q_OUT + (1 - s - f) * Q_IN
    r = q / (1 - q)
    return 100 * P * r / (r + M_W / M_AIR) / magnus(T_C)


# ---------------------------------------------------------------- the per-step monitor
def history(run_dir):
    path = Path(run_dir) / "postProcessing/moistureBudget/budget.dat"
    lines = path.read_text().splitlines()
    names = lines[0].lstrip("# ").split()
    rows = np.array([[float(x) for x in l.split()] for l in lines[1:] if l and not l.startswith("#")])
    # a run continued from saved fields appends from its start time on: its rows replace the
    # earlier ones from that time
    kept = []
    for r in rows:
        while kept and kept[-1][0] >= r[0]:
            kept.pop()
        kept.append(r)
    rows = np.array(kept)
    h = {n: rows[:, i] for i, n in enumerate(names)}
    return h


def at(h, key, t):
    return float(np.interp(t, h["time"], h[key]))


def tmean(h, key, a, b):
    """time-weighted mean of a per-step value over (a, b]: each row holds over the step ending at it"""
    t = h["time"]
    m = (t > a + 1e-9) & (t <= b + 1e-9)
    return float((h[key][m] * h["dt"][m]).sum() / h["dt"][m].sum())


def integral(h, key, a, b):
    t = h["time"]
    m = (t > a + 1e-9) & (t <= b + 1e-9)
    return float((h[key][m] * h["dt"][m]).sum())


def out_vapour(h, patch):
    return h[patch + "_conv"] + h[patch + "_diff"]


# ---------------------------------------------------------------- the planes
_DT = {"Float32": "<f4", "Float64": "<f8", "Int32": "<i4", "Int64": "<i8", "UInt32": "<u4", "UInt64": "<u8"}


def read_vtp(path):
    """OpenFOAM's binary (base64, UInt64 headers, uncompressed) VTK PolyData, plain or gzipped."""
    b = Path(path).read_bytes()
    if str(path).endswith(".gz"):
        b = gzip.decompress(b)
    text = b.decode("ascii")
    if "header_type='UInt64'" not in text or "LittleEndian" not in text or "compressor" in text:
        raise SystemExit(f"{path}: not the VTP layout this reader knows")
    out, sec = {}, None
    for m in re.finditer(r"<(\w+)\s*>|<DataArray([^>]*)>([^<]*)</DataArray>", text):
        if m.group(1):
            sec = m.group(1)
            continue
        attrs = dict(re.findall(r"(\w+)='([^']*)'", m.group(2)))
        raw = base64.b64decode(m.group(3).strip())
        n = int(np.frombuffer(raw[:8], "<u8")[0])
        a = np.frombuffer(raw[8:8 + n], _DT[attrs["type"]]).astype(float if "Float" in attrs["type"] else np.int64)
        k = int(attrs.get("NumberOfComponents", 1))
        out[(sec, attrs["Name"])] = a.reshape(-1, k) if k > 1 else a
    return out


def plane_geometry(d):
    """each polygon's area and mean x (the plane is z = const)"""
    pts = d[("Points", "Points")][:, :2]
    conn, offs = d[("Polys", "connectivity")], d[("Polys", "offsets")]
    starts = np.r_[0, offs[:-1]]
    nxt = np.arange(1, len(conn) + 1)
    nxt[offs - 1] = starts
    a, b = pts[conn], pts[conn[nxt]]
    area = 0.5 * np.abs(np.add.reduceat(a[:, 0] * b[:, 1] - b[:, 0] * a[:, 1], starts))
    cx = np.add.reduceat(a[:, 0], starts) / (offs - starts)
    return area, cx


def plane_file(run_dir, t, name="clip"):
    d = Path(run_dir) / "postProcessing/planes" / f"{t:g}"
    for f in (d / f"{name}.vtp", d / f"{name}.vtp.gz"):
        if f.exists():
            return f
    return None


def section(run_dir, t):
    f = plane_file(run_dir, t)
    if f is None:
        return None
    d = read_vtp(f)
    area, cx = plane_geometry(d)
    T = d[("CellData", "T")] - 273.15
    s = d[("CellData", "H2O")]
    f_out = np.clip(d[("CellData", "outdoorAir")], 0, 1) if ("CellData", "outdoorAir") in d else np.zeros_like(s)
    R = rh(T, s, f_out)
    room = cx > 0
    w = area[room] / area[room].sum()
    return dict(saturated=float(w[R[room] >= 100].sum()), mean_rh=float((w * R[room]).sum()),
                max_rh=float(R[room].max()), below50=float(w[R[room] < 50].sum()),
                outdoor=float((w * f_out[room]).sum()), T=float((w * T[room]).sum()))


# ---------------------------------------------------------------- main
def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    runs, res = Path(sys.argv[1]), Path(sys.argv[2])
    S, F, Wn = (history(runs / r) for r in ("shower", "fan", "window"))
    for h in (S, F, Wn):
        h["mean_T_C"] = h["rhoT"] / h["mass"] - 273.15
    lines = []
    say = lines.append
    say("== the meshes, from the monitor's first row")
    say(f"   room air: {S['volume'][0]:.4f} m3 (shower and fan), {Wn['volume'][0]:.4f} m3 (window: the sash's cells out)")
    say(f"   grille {F['fan_area'][0]:.4f} m2, undercut {S['undercut_area'][0]:.4f} m2; the tilted sash's gaps: top "
        f"{Wn['gapTop_area'][0]:.4f}, left {Wn['gapLeft_area'][0]:.4f}, right {Wn['gapRight_area'][0]:.4f} m2; "
        f"the window's clear opening at x = 0 {Wn['opening_area'][0]:.4f} m2")
    say("")

    # ---- the shower
    released = integral(S, "source", 0, 600)
    W600 = at(S, "water", 600)
    under_out_shower = integral({"time": S["time"], "dt": S["dt"], "v": out_vapour(S, "undercut")}, "v", 0, 600)
    res_shower = S["water"][-1] - S["water"][0] - released + under_out_shower
    say("== shower, 0-600 s: the shower on, the door shut, the window shut, the fan off")
    say(f"   vapour released by the source {1e3 * released:.3f} g (0.2833 g/s for 600 s); in the room at 600 s "
        f"{1e3 * W600:.3f} g; out under the door {1e3 * under_out_shower:.4f} g")
    say(f"   vapour budget closes to {100 * abs(res_shower) / released:.4f}% of the release")
    say(f"   room's mean air temperature (mass-weighted) at 600 s {at(S, 'mean_T_C', 600):.2f} C; "
        f"at 300 s {at(S, 'mean_T_C', 300):.2f} C")
    say(f"   room air mass {at(S, 'mass', 0):.4f} kg at 0 s, {at(S, 'mass', 600):.4f} kg at 600 s; "
        f"air out under the door over 0-600 s {integral(S, 'undercut_out', 0, 600):.4f} kg, in "
        f"{integral(S, 'undercut_in', 0, 600):.4f} kg")
    say("")

    # ---- the branches
    base = {"fan": W600, "window": at(Wn, "water", 600)}
    H = {"fan": F, "window": Wn}
    say("== fan (15 l/s, window shut) and window (on tilt, fan off), 600-1500 s from the shower's 600 s")
    say(f"   vapour in the room at 600 s: fan {1e3 * base['fan']:.3f} g (the shower's), window "
        f"{1e3 * base['window']:.3f} g ({1e3 * (W600 - base['window']):.3f} g sat where the sash's cells are)")
    say("   share of that vapour removed since 600 s, %:")
    say("     min after 600 s      fan    window")
    shares = {}
    for m in (1, 3, 5, 6, 10, 15):
        t = 600 + 60 * m
        sf = 1 - at(F, "water", t) / base["fan"]
        sw = 1 - at(Wn, "water", t) / base["window"]
        shares[m] = (sf, sw)
        say(f"     {m:>2d} ({t:4d} s)       {100 * sf:6.2f}  {100 * sw:6.2f}")
    sw_rel = 1 - at(Wn, "water", 1500) / released
    sf_rel = 1 - at(F, "water", 1500) / released
    say(f"   at 1500 s as a share of the 170 g released instead: fan {100 * sf_rel:.2f}%, window {100 * sw_rel:.2f}%")
    for run, h in H.items():
        paths = ["fan", "undercut"] if run == "fan" else ["opening", "undercut"]
        outs = {p: integral({"time": h["time"], "dt": h["dt"], "v": out_vapour(h, p)}, "v", 600, 1500) for p in paths}
        resid = h["water"][-1] - base[run] + sum(outs.values())
        say(f"   {run}: vapour out by 1500 s " + ", ".join(f"through the {p} {1e3 * v:.3f} g" for p, v in outs.items())
            + f"; budget closes to {100 * abs(resid) / base[run]:.4f}% of the 600 s inventory")
    say("   the room's mean air temperature (mass-weighted), C:")
    for t in (600, 660, 780, 900, 1200, 1500):
        say(f"     {t:4d} s   fan {at(F, 'mean_T_C', t) if t > 600 else at(S, 'mean_T_C', 600):6.2f}   "
            f"window {at(Wn, 'mean_T_C', t):6.2f}")
    say("")

    # ---- flows
    say("== flows, kg/s, time-weighted means (in = into the room)")
    rho_out = DRY_KG_M3_0C
    for a, b in ((600, 660), (600, 900), (900, 1200), (1200, 1500), (600, 1500)):
        fan = (f"fan out {tmean(F, 'fan_out', a, b):.5f} ({1e3 * tmean(F, 'fan_vol', a, b):.2f} l/s), "
               f"undercut in {tmean(F, 'undercut_in', a, b):.5f} out {tmean(F, 'undercut_out', a, b):.5f}")
        win = (f"sash in {tmean(Wn, 'opening_in', a, b):.5f} out {tmean(Wn, 'opening_out', a, b):.5f} "
               f"(top gap in {tmean(Wn, 'gapTop_in', a, b):.5f} out {tmean(Wn, 'gapTop_out', a, b):.5f}; "
               f"side gaps in {tmean(Wn, 'gapLeft_in', a, b) + tmean(Wn, 'gapRight_in', a, b):.5f} "
               f"out {tmean(Wn, 'gapLeft_out', a, b) + tmean(Wn, 'gapRight_out', a, b):.5f}), "
               f"undercut in {tmean(Wn, 'undercut_in', a, b):.5f} out {tmean(Wn, 'undercut_out', a, b):.5f}; "
               f"room {tmean(Wn, 'mean_T_C', a, b):.2f} C")
        say(f"   {a}-{b} s  fan: {fan}")
        say(f"   {a}-{b} s  window: {win}")
    sash_in = tmean(Wn, "opening_in", 600, 1500)
    und_in = tmean(Wn, "undercut_in", 600, 1500)
    say(f"   window, 600-1500 s: {sash_in * 3600 / rho_out:.1f} m3/h of 0 C outdoor air in through the sash "
        f"({rho_out:.4f} kg/m3), {sash_in * 3600 / rho_out / 11.2589:.2f} room volumes an hour; hall air under "
        f"the door {und_in / (und_in + sash_in) * 100:.1f}% of the air coming in")
    fan_rho = tmean(F, "fan_out", 600, 1500) / tmean(F, "fan_vol", 600, 1500)
    say(f"   fan, 600-1500 s: {tmean(F, 'fan_vol', 600, 1500) * 3600:.1f} m3/h out, "
        f"{tmean(F, 'fan_vol', 600, 1500) * 3600 / 11.3455:.2f} room volumes an hour (mean density out {fan_rho:.4f} kg/m3)")
    # the undercut in the window run, minute by minute
    t = Wn["time"]
    net = [tmean(Wn, "undercut_in", a, a + 60) - tmean(Wn, "undercut_out", a, a + 60) for a in range(600, 1500, 60)]
    t_below = t[(Wn["mean_T_C"] < 20) & (t > 600)].min()
    und_vap = integral({"time": t, "dt": Wn["dt"], "v": out_vapour(Wn, "undercut")}, "v", 600, 1500)
    say("   window: net hall air in under the door, minute by minute, g/s: " + " ".join(f"{1e3 * v:.2f}" for v in net))
    say(f"   window: the room's mean below the hall's 20 C from {t_below:.1f} s; vapour into the hall by 1500 s "
        f"{1e3 * und_vap:.3f} g, {100 * und_vap / base['window']:.2f}% of the 600 s inventory")
    say("")

    # ---- how moist the air leaving is
    say("== the vapour fraction of the air leaving through the grille (fan) or the sash (window), over the room's mean")
    for run, face in (("fan", "fan"), ("window", "opening")):
        h = H[run]
        parts = []
        for a, b in ((600, 660), (660, 780), (780, 900), (900, 1200), (1200, 1500), (600, 1500)):
            m = (h["time"] > a + 1e-9) & (h["time"] <= b + 1e-9)
            dt = h["dt"][m]
            y_out = (h[face + "_conv"][m] * dt).sum() / (h[face + "_out"][m] * dt).sum()
            y_room = ((h["water"][m] / h["mass"][m]) * dt).sum() / dt.sum()
            parts.append(f"{a}-{b} s {y_out / y_room:.2f}")
        say(f"   {run}: " + ", ".join(parts))
    say("")

    # ---- the tracer
    win = runs / "window"
    say("== window: the outdoor-air tracer")
    rng = []
    for fmm in sorted((win / "postProcessing/outdoorAirRange").glob("*/fieldMinMax*.dat")):
        for line in fmm.read_text().splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            tok = re.sub(r"\([^)]*\)", " ", line).split()
            if float(tok[0]) > 600:      # time field min [processor] max [processor]
                rng.append((float(tok[2]), float(tok[4] if len(tok) == 6 else tok[3])))
    rng = np.array(rng)
    say(f"   range over 600-1500 s (every tenth step): {rng[:, 0].min():.3g} to {rng[:, 1].max():.7f}")
    room = []
    for vfv in sorted((win / "postProcessing/outdoorAirRoom").glob("*/volFieldValue*.dat")):
        for line in vfv.read_text().splitlines():
            if line.strip() and not line.startswith("#"):
                room.append([float(x) for x in line.split()])
    room = np.array(sorted({r[0]: r for r in room}.values()))
    for t in (660, 900, 1200, 1500):
        say(f"   outdoor air's share of the room's air mass at {t} s: "
            f"{np.interp(t, room[:, 0], room[:, 1]) / at(Wn, 'mass', t):.3f}")
    say("")

    # ---- still outdoor air
    f = None
    for name in ("horizontal.vtp", "horizontal.vtp.gz"):
        p = win / "postProcessing/earlyStillness/601.25" / name
        if p.exists():
            f = p
    if f is not None:
        d = read_vtp(f)
        pts, conn, offs = d[("Points", "Points")], d[("Polys", "connectivity")], d[("Polys", "offsets")]
        starts = np.r_[0, offs[:-1]]
        c = np.array([pts[conn[a:b]].mean(0) for a, b in zip(starts, offs)])
        sel = (c[:, 0] < -0.24) & ((c[:, 2] < -1.3) | (c[:, 2] > 1.7))
        v = np.linalg.norm(d[("CellData", "U")][sel], axis=1)
        say(f"== the outdoor air at 601.25 s on y = 1.5 m, beyond the wall and clear of the window "
            f"(x < -0.24 m, z < -1.3 or > 1.7 m), {int(sel.sum())} faces: median {np.median(v):.2g} m/s, largest {v.max():.2g} m/s")
        say("")

    # ---- the fan's Courant check
    if (runs / "fanCo1/postProcessing/moistureBudget/budget.dat").exists():
        C1 = history(runs / "fanCo1")
        say("== the fan run (Courant 2) against fanCo1 (Courant 1), 600-615 s")
        for name, h in (("Courant 1", C1), ("Courant 2", F)):
            rem = (integral({"time": h["time"], "dt": h["dt"], "v": out_vapour(h, "fan") + out_vapour(h, "undercut")}, "v", 600, 615))
            m = (h["time"] > 600) & (h["time"] <= 615 + 1e-9)
            say(f"   {name}: vapour out {1e3 * rem:.5f} g, fan {tmean(h, 'fan_out', 600, 615):.7f} kg/s, undercut in "
                f"{tmean(h, 'undercut_in', 600, 615):.7f} kg/s, in the room at 615 s {1e3 * at(h, 'water', 615):.4f} g, "
                f"{int(m.sum())} steps")
        say("")

    # ---- relative humidity on the section
    times = np.round(np.arange(600, 1500 + 1e-6, 15), 6)
    rows = []
    for t in times:
        a, b = section(runs / "fan", t), section(runs / "window", t)
        if a is None or b is None:
            continue
        rows.append([t, a, b])
    res.mkdir(parents=True, exist_ok=True)
    with open(res / "section_rh.csv", "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["t_s", "fan_saturated_pct", "fan_mean_rh_pct", "fan_max_rh_pct", "fan_below50_pct", "fan_mean_T_C",
                    "window_saturated_pct", "window_mean_rh_pct", "window_max_rh_pct", "window_below50_pct",
                    "window_mean_T_C", "window_outdoor_air_share"])
        for t, a, b in rows:
            w.writerow([f"{t:g}", f"{100 * a['saturated']:.2f}", f"{a['mean_rh']:.2f}", f"{a['max_rh']:.1f}",
                        f"{100 * a['below50']:.2f}", f"{a['T']:.2f}", f"{100 * b['saturated']:.2f}", f"{b['mean_rh']:.2f}",
                        f"{b['max_rh']:.1f}", f"{100 * b['below50']:.2f}", f"{b['T']:.2f}", f"{b['outdoor']:.3f}"])
    say("== relative humidity on the section z = 0.455 m (the clip's), the room's faces (x > 0) by area")
    say(f"   background: room and hall {1e3 * Q_IN:.4f} g/kg of moist air (7 g/kg of dry air), outdoors "
        f"{1e3 * Q_OUT:.4f} (0 C at 95%); p = 1e5 Pa")
    say("     t (s)  min    fan: saturated  mean RH  max     window: saturated  mean RH  max   outdoor share")
    for t, a, b in rows:
        if (t - 600) % 60 == 0:
            say(f"     {t:5.0f} {(t - 600) / 60:4.0f}     {100 * a['saturated']:6.1f}%  {a['mean_rh']:6.1f}  {a['max_rh']:5.0f}"
                f"         {100 * b['saturated']:6.1f}%  {b['mean_rh']:6.1f}  {b['max_rh']:5.0f}   {b['outdoor']:.3f}")
    for name, k in (("fan", 1), ("window", 2)):
        sat = [(r[0], r[k]["saturated"]) for r in rows]
        last = max((t for t, s in sat if s > 0), default=None)
        say(f"   {name}: saturated air on the section until {last:g} s (15 s sampling)")
    say("")

    # ---- histories every 5 s
    grid_s = np.arange(0, 600 + 1e-6, 5)
    grid_b = np.arange(600, 1500 + 1e-6, 5)
    write_history(res / "shower/history.csv", S, grid_s, released, None, "shower")
    write_history(res / "fan/history.csv", F, grid_b, released, base["fan"], "fan", start_row=(600, S))
    write_history(res / "window/history.csv", Wn, grid_b, released, base["window"], "window", tracer=room)

    (res / "summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def write_history(path, h, grid, released, base, run, start_row=None, tracer=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    t = h["time"]
    cols = ["t_s", "vapour_g", "mean_T_C", "air_mass_kg"]
    if run == "shower":
        cols += ["released_g", "undercut_in_kg_s", "undercut_out_kg_s"]
    else:
        cols += ["removed_pct"]
        cols += (["fan_out_kg_s", "undercut_in_kg_s", "undercut_out_kg_s", "vapour_out_fan_g", "vapour_out_undercut_g"]
                 if run == "fan" else
                 ["sash_in_kg_s", "sash_out_kg_s", "top_gap_in_kg_s", "top_gap_out_kg_s", "side_gaps_in_kg_s",
                  "side_gaps_out_kg_s", "undercut_in_kg_s", "undercut_out_kg_s", "vapour_out_sash_g",
                  "vapour_out_undercut_g", "outdoor_air_share"])
    hh = dict(h)
    hh["side_in"] = h["gapLeft_in"] + h["gapRight_in"]
    hh["side_out"] = h["gapLeft_out"] + h["gapRight_out"]
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(cols)
        for i, g in enumerate(grid):
            if start_row is not None and g == start_row[0]:
                src = start_row[1]
            else:
                src = h
            row = [f"{g:g}", f"{1e3 * at(src, 'water', g):.4f}", f"{at(src, 'mean_T_C', g):.3f}", f"{at(src, 'mass', g):.5f}"]
            prev = grid[i - 1] if i else None
            mean = (lambda k: tmean(hh, k, prev, g)) if prev is not None else (lambda k: float("nan"))
            cum = lambda p: 1e3 * integral({"time": t, "dt": h["dt"], "v": out_vapour(h, p)}, "v", grid[0], g)
            if run == "shower":
                row += [f"{1e3 * integral(h, 'source', 0, g):.4f}"] + [f"{mean(k):.6f}" for k in ("undercut_in", "undercut_out")]
            else:
                row += [f"{100 * (1 - at(src, 'water', g) / base):.3f}"]
                if run == "fan":
                    row += [f"{mean(k):.6f}" for k in ("fan_out", "undercut_in", "undercut_out")]
                    row += [f"{cum('fan'):.4f}", f"{cum('undercut'):.4f}"]
                else:
                    row += [f"{mean(k):.6f}" for k in ("opening_in", "opening_out", "gapTop_in", "gapTop_out",
                                                       "side_in", "side_out", "undercut_in", "undercut_out")]
                    row += [f"{cum('opening'):.4f}", f"{cum('undercut'):.4f}",
                            f"{np.interp(g, tracer[:, 0], tracer[:, 1]) / at(h, 'mass', g):.4f}"]
            w.writerow([x.replace("nan", "") for x in row])


if __name__ == "__main__":
    main()
