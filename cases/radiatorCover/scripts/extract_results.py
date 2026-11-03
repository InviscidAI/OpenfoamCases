"""The radiator's heat, the cover's and the room's, from each run's per-step monitor.

    python3 scripts/extract_results.py <runsDir> <resultsDir>

reads <runsDir>/bare and <runsDir>/cover, postProcessing/heatAccounting/heat.csv (one row a
time step, written by the coded function object heatAccounting in config/caseSettings), and
writes <resultsDir>/<run>/history.csv (every 2.5 s), <resultsDir>/minutes.csv and
<resultsDir>/summary.txt. Every value is W (or J) per metre of section. If the sections at
60, 120, ... 300 s are there (postProcessing/clip/<t>/clip.vtp, or .vtp.gz) and PyVista is
installed, it also writes <resultsDir>/section_means.csv, the area-mean air temperature in
the whole room, round the radiator (x < 0.165 m, y < 0.8 m, the cover's inside, without the
convector) and under the convector (x = 0.040-0.103 m, y < 0.15 m).

The radiator's output is what it gives the air and the walls:
- the convector: the air in its zone is held at 55 C, so the heat it gives is the zone's
  energy balance, the sensible enthalpy carried out of it less what came in, plus what it
  conducts out of its faces, plus the rise of its stored energy (referenced to 20 C as the
  solver's enthalpy is) and of its kinetic energy;
- the steel front panel: its convection and its net radiation, off all its faces.
The heat crossing the cover's outside is the enthalpy carried out of the cover's region
(x < 0.165, y < 0.8, the panel excluded) less what is carried in, diffusion and radiation
across its openings, and convection and radiation off the MDF's room faces. The room's
budget: the radiator's output plus what the walls give the air must equal the rise of the
air's internal energy, (cv/R) times the integral of p over the closed room.

If <runsDir>/sofa has solved too, it also writes <resultsDir>/sofa/history.csv (every 2.5 s)
and <resultsDir>/sofa/summary.txt, the sofa run against the bare one; the files above do not
change. The sofa run's monitor has the sofa as a wall (sofaConv, sofaRad) and, in place of the
cover's region, the gap behind the sofa (x < 0.2731 m, y < 0.72 m; the gap* columns). The
sofa's surface stores heat: what it takes from the room, by convection and radiation, is what
it stores. The room's own air is the room's air outside the convector, whose air is held at
55 C.

Each step's value is held over the step that ends at its time, and a window's mean is the
integral over the window, partial steps included, over its length.
"""
import csv
import sys
from pathlib import Path

import numpy as np

R = 8314.46261815324 / 28.96  # J/kg K, air at 28.96 kg/kmol
CV = 1005 - R
TAMB = 293.15
TRAD = 328.15  # the radiator's steel and its convector air, 55 C
VOL = 4.0 * 2.4 - 0.020 * 0.60  # the room's air, m3 per metre
ZONE = 0.063 * 0.60  # the convector zone
COVER = 0.165 * 0.8 - 0.020 * 0.60  # the cover's region, the panel left out
WALLS = ["glass", "ceiling", "innerWall", "floor", "outerWall"]
# the sofa's cells, left out of the sofa run's air: the seat and base, the backrest frame and
# the back cushion, on the bare run's grid lines
SOFA = ((1.2222222222 - 0.2731255747) * (0.429 - 0.171) + (0.396494214 - 0.2731255747) * (0.72 - 0.429)
        + (0.6145573571 - 0.396494214) * (0.85 - 0.429))


def read(run):
    d = np.genfromtxt(Path(run) / "postProcessing/heatAccounting/heat.csv", delimiter=",", names=True)
    return d[np.r_[True, np.diff(d["time"]) > 0]]


def series(d):
    t = d["time"]
    dt = np.diff(np.r_[0, t])
    Mz0 = 1e5 / (R * TAMB) * ZONE
    Ez = d["Uzone"] - 1005 * TAMB * d["zoneMass"]
    Ez0 = CV / R * 1e5 * ZONE - 1005 * TAMB * Mz0
    zone = (d["zoneEnthalpy"] + d["zoneDiffusion"] + np.diff(np.r_[Ez0, Ez]) / dt
            + np.diff(np.r_[0, d["KEzone"]]) / dt)
    s = {
        "convection_W": zone + d["panelConvection"],
        "radiation_W": d["panelRadiation"],
    }
    s["output_W"] = s["convection_W"] + s["radiation_W"]
    s["room_K"] = d["massT"] / d["mass"]
    s["catalogue_W"] = 980 * np.maximum((TRAD - s["room_K"]) / 50, 0) ** 1.3
    s["wall_into_air_W"] = sum(d[w + "Conv"] + d[w + "Rad"] for w in WALLS)
    s["energy_rate_W"] = np.diff(np.r_[CV / R * 1e5 * VOL, d["Uroom"]]) / dt
    s["closure_W"] = s["output_W"] + s["wall_into_air_W"] - s["energy_rate_W"]
    s["glass_W"] = -(d["glassConv"] + d["glassRad"])
    s["crossing_W"] = (d["coverGrossOut"] - d["coverGrossIn"] + d["coverDiffusion"]
                       + d["coverOpeningRadiation"] + d["mdfConvection"] + d["mdfRadiation"])
    s["grossOut_W"] = d["coverGrossOut"]
    s["grossIn_W"] = d["coverGrossIn"]
    s["openingRadiation_W"] = d["coverOpeningRadiation"]
    s["mdf_W"] = d["mdfConvection"] + d["mdfRadiation"]
    return t, dt, s


def window(t, dt, a, lo, hi):
    w = np.maximum(0, np.minimum(t, hi) - np.maximum(t - dt, lo))
    return float(np.sum(a * w))


def means(t, dt, s, lo, hi):
    m = {k: window(t, dt, a, lo, hi) / (hi - lo) for k, a in s.items()}
    m["radiationShare"] = m["radiation_W"] / m["output_W"]
    m["overCatalogue"] = m["output_W"] / m["catalogue_W"]
    return m


def section_means(runs, out):
    try:
        import gzip
        import tempfile
        import pyvista as pv
    except ImportError:
        return None
    rows = []
    for r in ("bare", "cover"):
        for t in (60, 120, 180, 240, 300):
            d = runs / r / "postProcessing/clip" / str(t)
            src = d / "clip.vtp" if (d / "clip.vtp").exists() else d / "clip.vtp.gz"
            if not src.exists():
                return None
            with tempfile.TemporaryDirectory() as tmp:
                f = Path(tmp) / "clip.vtp"
                f.write_bytes(gzip.open(src).read() if src.suffix == ".gz" else src.read_bytes())
                m = pv.read(f)
                c = m.cell_centers().points
                T = m.cell_data["T"] - 273.15
                A = m.compute_cell_sizes()["Area"]
            conv = (c[:, 0] > .04) & (c[:, 0] < .103) & (c[:, 1] > .15) & (c[:, 1] < .75)
            masks = {"room": np.ones(len(T), bool),
                     "round_radiator": (c[:, 0] < .165) & (c[:, 1] < .8) & ~conv,
                     "under_convector": (c[:, 0] > .04) & (c[:, 0] < .103) & (c[:, 1] < .15)}
            rows.append([r, t] + [f"{(T[k] * A[k]).sum() / A[k].sum():.2f}" for k in masks.values()])
    with (out / "section_means.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["run", "time_s", "room_C", "round_radiator_C", "under_convector_C"])
        w.writerows(rows)
    return rows


def sofa_series(d):
    """The sofa run's terms: the radiator as series(), the sofa and the room's own air."""
    t = d["time"]
    dt = np.diff(np.r_[0, t])
    Mz0 = 1e5 / (R * TAMB) * ZONE
    Ez = d["Uzone"] - 1005 * TAMB * d["zoneMass"]
    Ez0 = CV / R * 1e5 * ZONE - 1005 * TAMB * Mz0
    zone = (d["zoneEnthalpy"] + d["zoneDiffusion"] + np.diff(np.r_[Ez0, Ez]) / dt
            + np.diff(np.r_[0, d["KEzone"]]) / dt)
    s = {"convection_W": zone + d["panelConvection"], "radiation_W": d["panelRadiation"]}
    s["output_W"] = s["convection_W"] + s["radiation_W"]
    s["room_K"] = d["massT"] / d["mass"]
    s["own_air_K"] = (d["massT"] - TRAD * d["zoneMass"]) / (d["mass"] - d["zoneMass"])
    s["catalogue_W"] = 980 * np.maximum((TRAD - s["room_K"]) / 50, 0) ** 1.3
    s["glass_W"] = -(d["glassConv"] + d["glassRad"])
    s["ceiling_inner_rad_W"] = -(d["ceilingRad"] + d["innerWallRad"])
    s["ceiling_inner_conv_W"] = -(d["ceilingConv"] + d["innerWallConv"])
    walls = WALLS + (["sofa"] if "sofaConv" in d.dtype.names else [])
    s["wall_into_air_W"] = sum(d[w + "Conv"] + d[w + "Rad"] for w in walls)
    vol = VOL - (SOFA if "sofaConv" in d.dtype.names else 0)
    s["energy_rate_W"] = np.diff(np.r_[CV / R * 1e5 * vol, d["Uroom"]]) / dt
    s["closure_W"] = s["output_W"] + s["wall_into_air_W"] - s["energy_rate_W"]
    if "sofaConv" in d.dtype.names:
        s["sofa_stored_W"] = -(d["sofaConv"] + d["sofaRad"])
        s["sofa_rad_W"] = -d["sofaRad"]
        s["gap_out_W"] = d["gapGrossOut"]
        s["gap_in_W"] = d["gapGrossIn"]
    return t, dt, s


def sofa_results(runs, out):
    """results/sofa/: the sofa run against the bare one."""
    b = sofa_series(read(runs / "bare"))
    f = sofa_series(read(runs / "sofa"))
    if f[0][-1] < 300 - 1e-6:
        raise SystemExit(f"sofa's monitor ends at {f[0][-1]} s")
    (out / "sofa").mkdir(parents=True, exist_ok=True)
    t, dt, s = f
    cols = ["output_W", "convection_W", "radiation_W", "room_K", "own_air_K", "glass_W", "ceiling_inner_rad_W",
            "ceiling_inner_conv_W", "sofa_stored_W", "sofa_rad_W", "gap_out_W", "gap_in_W", "wall_into_air_W",
            "energy_rate_W", "closure_W"]
    cum = cum_sofa = 0.0
    with (out / "sofa/history.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["start_s", "end_s"] + [c.replace("_K", "_C") for c in cols]
                   + ["output_since_0_kJ", "sofa_stored_since_0_kJ"])
        for lo in np.arange(0, 300, 2.5):
            m = means(t, dt, s, lo, lo + 2.5)
            cum += 2.5 * m["output_W"]
            cum_sofa += 2.5 * m["sofa_stored_W"]
            w.writerow([f"{lo:g}", f"{lo + 2.5:g}"]
                       + [f"{m[c] - 273.15:.3f}" if c.endswith("_K") else f"{m[c]:.2f}" for c in cols]
                       + [f"{cum / 1e3:.3f}", f"{cum_sofa / 1e3:.3f}"])

    def kJ(r, k, lo=0, hi=300):
        return window(r[0], r[1], r[2][k], lo, hi) / 1e3

    def at(r, k, time):
        return float(r[2][k][np.searchsorted(r[0], time - 1e-9)]) - 273.15

    lines = []
    say = lines.append
    say("A sofa 15 cm in front of the radiator against the bare radiator, 0-300 s from switch-on "
        "(W and J per metre of section)")
    say("")
    say(f"steps: bare {len(b[0])}, sofa {len(t)}; last monitored time {b[0][-1]:g} and {t[-1]:g} s")
    say("")
    say("The radiator's output from switch-on to 300 s, kJ/m")
    say("            output  convection  radiation")
    for name, r in (("bare", b), ("sofa", f)):
        say(f"  {name:5s}  {kJ(r, 'output_W'):7.1f}  {kJ(r, 'convection_W'):10.1f}  {kJ(r, 'radiation_W'):9.1f}")
    say(f"  sofa / bare  {100 * kJ(f, 'output_W') / kJ(b, 'output_W'):.1f}%")
    say("")
    say("Minute by minute (means, W/m)")
    say("  minute    bare: output   rad | sofa: output   rad  sofa stores | sofa/bare")
    for lo in range(0, 300, 60):
        mb, mf = means(*b, lo, lo + 60), means(*f, lo, lo + 60)
        say(f"  {lo:3d}-{lo + 60:3d}        {mb['output_W']:6.1f} {mb['radiation_W']:5.1f} |       {mf['output_W']:6.1f} "
            f"{mf['radiation_W']:5.1f}       {mf['sofa_stored_W']:6.1f} |   {100 * mf['output_W'] / mb['output_W']:5.1f}%")
    say("")
    say("Where the heat went, 0-300 s, kJ/m (into the air +, out of it -)")
    say("                                         bare    sofa")
    rows = [("the radiator's output", "output_W", 1),
            ("lost through the glass", "glass_W", -1),
            ("radiation into the ceiling and inner wall", "ceiling_inner_rad_W", -1),
            ("convection into the ceiling and inner wall", "ceiling_inner_conv_W", -1),
            ("stored in the sofa's surface", "sofa_stored_W", -1)]
    for label, k, sign in rows:
        vb = sign * kJ(b, k) if k in b[2] else 0.0
        say(f"  {label:42s} {vb:6.1f}  {sign * kJ(f, k):6.1f}")
    say(f"  {'rise of the air':42s} {kJ(b, 'energy_rate_W'):6.1f}  {kJ(f, 'energy_rate_W'):6.1f}")
    say(f"  {'residual (closure)':42s} {kJ(b, 'closure_W'):6.2f}  {kJ(f, 'closure_W'):6.2f}")
    say("  The floor and the window wall below and above the glass are adiabatic; what they absorb as")
    say("  radiation they give the air, so they are left out. The ceiling and inner wall are held at 20 C:")
    say("  what they take leaves the model.")
    say("")
    say("The sofa's surface, what it takes from the room and stores, W/m")
    for lo, hi in ((0, 10), (10, 60), (60, 120), (120, 180), (180, 240), (240, 300)):
        say(f"  {lo:3d}-{hi:3d} s  {means(t, dt, s, lo, hi)['sofa_stored_W']:6.1f}")
    say(f"  last step, {t[-1]:g} s: {s['sofa_stored_W'][-1]:+.1f}; radiation it absorbs over 0-300 s "
        f"{kJ(f, 'sofa_rad_W'):.1f} kJ/m")
    say("")
    say("The room's air, C (own air: outside the convector; room: all of it, as in summary.txt)")
    say("  time    own air: bare   sofa  sofa-bare | room: bare   sofa")
    for time in (10, 30, 60, 120, 180, 240, 300):
        ob, of_ = at(b, "own_air_K", time), at(f, "own_air_K", time)
        say(f"  {time:4d}           {ob:6.2f} {of_:6.2f}     {of_ - ob:+.2f} |      {at(b, 'room_K', time):6.2f} "
            f"{at(f, 'room_K', time):6.2f}")
    say("")
    say("The gap behind the sofa (x < 0.2731 m, y < 0.72 m): enthalpy carried out and in, W/m")
    for lo in range(0, 300, 60):
        m = means(t, dt, s, lo, lo + 60)
        say(f"  {lo:3d}-{lo + 60:3d} s  out {m['gap_out_W']:6.1f}  in {m['gap_in_W']:5.1f}")
    say("")
    iv = [means(t, dt, s, lo, lo + 7.5)["closure_W"] for lo in np.arange(0, 300, 7.5)]
    mn = [means(t, dt, s, lo, lo + 60)["closure_W"] for lo in range(0, 300, 60)]
    say("The sofa room's heat budget, radiator + walls + sofa - rise of the air's energy")
    say(f"  over each minute {min(mn):+.2f} to {max(mn):+.2f} W/m; over each 7.5 s, the first {iv[0]:+.2f}, "
        f"the rest {min(iv[1:]):+.2f} to {max(iv[1:]):+.2f} W/m; 0-300 s {window(t, dt, s['closure_W'], 0, 300) / 300:+.3f} W/m")
    (out / "sofa/summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    runs, out = Path(sys.argv[1]), Path(sys.argv[2])
    data = {r: series(read(runs / r)) for r in ("bare", "cover")}
    for r, (t, dt, s) in data.items():
        if t[-1] < 300 - 1e-6:
            raise SystemExit(f"{r}'s monitor ends at {t[-1]} s")
    lines = []
    say = lines.append

    # ---- each run's history, every 2.5 s
    for r, (t, dt, s) in data.items():
        (out / r).mkdir(parents=True, exist_ok=True)
        cols = ["output_W", "convection_W", "radiation_W", "room_K", "catalogue_W", "glass_W",
                "wall_into_air_W", "energy_rate_W", "closure_W"]
        if r == "cover":
            cols += ["crossing_W", "grossOut_W", "grossIn_W", "openingRadiation_W", "mdf_W"]
        cum_out = cum_cross = 0.0
        with (out / r / "history.csv").open("w", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["start_s", "end_s"] + [c.replace("room_K", "room_C") for c in cols]
                       + ["output_since_0_kJ"] + (["crossing_since_0_kJ"] if r == "cover" else []))
            for lo in np.arange(0, 300, 2.5):
                m = means(t, dt, s, lo, lo + 2.5)
                cum_out += 2.5 * m["output_W"]
                row = [f"{lo:g}", f"{lo + 2.5:g}"]
                row += [f"{m[c] - 273.15:.3f}" if c == "room_K" else f"{m[c]:.2f}" for c in cols]
                row.append(f"{cum_out / 1e3:.3f}")
                if r == "cover":
                    cum_cross += 2.5 * m["crossing_W"]
                    row.append(f"{cum_cross / 1e3:.3f}")
                w.writerow(row)

    # ---- minute by minute
    tb, dtb, sb = data["bare"]
    tc, dtc, sc = data["cover"]
    rows = []
    for lo in range(0, 300, 60):
        b, c = means(tb, dtb, sb, lo, lo + 60), means(tc, dtc, sc, lo, lo + 60)
        same = c["output_W"] * ((TRAD - b["room_K"]) / (TRAD - c["room_K"])) ** 1.3
        rows.append((lo, b, c, same))
    with (out / "minutes.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["start_s", "end_s",
                    "bare_output_W", "bare_convection_W", "bare_radiation_W", "bare_radiation_share",
                    "bare_room_C", "bare_over_catalogue", "bare_closure_W",
                    "cover_output_W", "cover_convection_W", "cover_radiation_W", "cover_radiation_share",
                    "cover_room_C", "cover_over_catalogue", "cover_closure_W",
                    "cover_crossing_W", "cover_gross_out_W", "cover_gross_in_W",
                    "crossing_over_bare", "cover_output_over_bare", "cover_output_over_bare_same_room"])
        for lo, b, c, same in rows:
            w.writerow([lo, lo + 60,
                        f"{b['output_W']:.2f}", f"{b['convection_W']:.2f}", f"{b['radiation_W']:.2f}",
                        f"{b['radiationShare']:.4f}", f"{b['room_K'] - 273.15:.3f}", f"{b['overCatalogue']:.4f}",
                        f"{b['closure_W']:.3f}",
                        f"{c['output_W']:.2f}", f"{c['convection_W']:.2f}", f"{c['radiation_W']:.2f}",
                        f"{c['radiationShare']:.4f}", f"{c['room_K'] - 273.15:.3f}", f"{c['overCatalogue']:.4f}",
                        f"{c['closure_W']:.3f}",
                        f"{c['crossing_W']:.2f}", f"{c['grossOut_W']:.2f}", f"{c['grossIn_W']:.2f}",
                        f"{c['crossing_W'] / b['output_W']:.4f}", f"{c['output_W'] / b['output_W']:.4f}",
                        f"{same / b['output_W']:.4f}"])

    # ---- the summary
    Eb = window(tb, dtb, sb["output_W"], 0, 300)
    Ec = window(tc, dtc, sc["output_W"], 0, 300)
    Ex = window(tc, dtc, sc["crossing_W"], 0, 300)
    dc = read(runs / "cover")
    stored = float(dc["Ucover"][-1] - 1005 * TAMB * dc["coverMass"][-1] + 1e5 * COVER)
    say("The radiator cover against the bare radiator, 0-300 s from switch-on (W and J per metre of section)")
    say("")
    say(f"steps: bare {len(tb)}, cover {len(tc)}; last monitored time {tb[-1]:g} and {tc[-1]:g} s")
    say("")
    say("Heat from switch-on to 300 s")
    say(f"  bare radiator's output                      {Eb / 1e3:7.1f} kJ/m  (mean {Eb / 300:.1f} W/m)")
    say(f"  covered radiator's output                   {Ec / 1e3:7.1f} kJ/m  = {100 * Ec / Eb:.1f}% of bare")
    say(f"  crossing the cover's outside into the room  {Ex / 1e3:7.1f} kJ/m  = {100 * Ex / Eb:.1f}% of bare")
    say(f"  held in the air inside the cover at 300 s   {stored / 1e3:7.2f} kJ/m  (relative to 20 C air)")
    say(f"  output less crossing                        {(Ec - Ex) / 1e3:7.2f} kJ/m")
    say("")
    say("Minute by minute (means; room = mass-weighted mean air temperature)")
    say("  minute    bare: output  conv   rad  rad%  room C  /cat   closure | cover: output  conv   rad  rad%  room C  /cat   crossing  out    in   closure | crossing/bare  output/bare  same-room")
    for lo, b, c, same in rows:
        say(f"  {lo:3d}-{lo + 60:3d}   {b['output_W']:6.1f} {b['convection_W']:6.1f} {b['radiation_W']:5.1f} {100 * b['radiationShare']:5.1f} "
            f"{b['room_K'] - 273.15:6.2f} {b['overCatalogue']:6.3f} {b['closure_W']:7.2f} |        {c['output_W']:6.1f} {c['convection_W']:6.1f} "
            f"{c['radiation_W']:5.1f} {100 * c['radiationShare']:5.1f} {c['room_K'] - 273.15:6.2f} {c['overCatalogue']:6.3f}   {c['crossing_W']:6.1f} "
            f"{c['grossOut_W']:5.1f} {c['grossIn_W']:5.1f} {c['closure_W']:7.2f} |   {100 * c['crossing_W'] / b['output_W']:5.1f}%       "
            f"{100 * c['output_W'] / b['output_W']:5.1f}%      {100 * same / b['output_W']:5.1f}%")
    say("  same-room: the cover's output rescaled to the bare room's temperature by EN 442's exponent, ((55 C - room)^1.3)")
    say("")
    say("The room's heat budget, radiator + walls - rise of the air's energy")
    for r, (t, dt, s) in data.items():
        iv = [means(t, dt, s, lo, lo + 7.5)["closure_W"] for lo in np.arange(0, 300, 7.5)]
        mn = [means(t, dt, s, lo, lo + 60)["closure_W"] for lo in range(0, 300, 60)]
        say(f"  {r:5s} over each minute {min(mn):+.2f} to {max(mn):+.2f} W/m; over each 7.5 s, the first {iv[0]:+.2f}, "
            f"the rest {min(iv[1:]):+.2f} to {max(iv[1:]):+.2f} W/m; 0-300 s {window(t, dt, s['closure_W'], 0, 300) / 300:+.3f} W/m")
    say("")
    say("Room mean air temperature")
    for r, (t, dt, s) in data.items():
        say(f"  {r:5s} {s['room_K'][-1] - 273.15:.2f} C at 300 s")
    sm = section_means(runs, out)
    if sm:
        say("")
        say("Area-mean air temperature in the mid-plane section, C (section_means.csv)")
        say("  run    time   room  round the radiator  under the convector")
        for r, t, a, b, c in sm:
            say(f"  {r:5s}  {t:4d}  {a:>6s}  {b:>8s}            {c:>8s}")
    (out / "summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    if (runs / "sofa/postProcessing/heatAccounting/heat.csv").exists():
        print()
        sofa_results(runs, out)


if __name__ == "__main__":
    main()
