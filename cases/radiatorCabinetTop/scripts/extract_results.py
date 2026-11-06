"""Figures from the solved runs' monitors.

    python3 scripts/extract_results.py <runsDir> <resultsDir>

Reads, for bare, solid and perforated, <runsDir>/<run>/postProcessing/heatAccounting/heat.csv (one
row a time step), diagnostics57/diagnostics.csv (one row a simulated second), initial.json (written
by scripts/make_case.py) and log.buoyantPimpleFoam; and the layer temperatures in the floor's and
the window wall's T at 120 s, from the run's collated processors*/120/T, for the heat those walls
stored inside the cabinet's footprint. Writes <resultsDir>/<run>/history.csv (every 2.5 s),
<resultsDir>/minutes.csv (every half minute) and <resultsDir>/summary.txt.

The radiator's heat is radiatorCover's total_W: the iron columns' convection and radiation plus
the energy balance of the convector zone held at 215 F, the enthalpy carried and diffused out of
it less the rise of its own energy and kinetic energy, with the sensible enthalpy referenced to
16 C, this room's start. Each step's heat is taken as constant over the step, from the previous
monitored time to its own; the heat since switch-on is their sum.

The heat out of the cabinet is what crosses its outside: the enthalpy carried out of and into its
open strips (the front at x = 0.330 m and the top at y = 0.756 m), the diffusion and the radiation
through them, and the convection and radiation off the sheet's outer faces (the B patches). The
floor and the window wall inside the cabinet's footprint (x < 0.330 m, y < 0.756 m) lie inside
that boundary. So the like-for-like share, the one the clip counts, sets the heat out of each
cabinet against bare's heat less what bare's own floor and wall stored in that same footprint;
the brief's share sets it against bare's whole heat, and both are written.
"""
import argparse
import csv
import json
import re
from pathlib import Path

import numpy as np

T0 = 289.15
CP = 1005
RUNS = ["bare", "solid", "perforated"]
CABINETS = ["solid", "perforated"]
WALLS = ["floor", "ceiling", "innerWall", "outerWall"]
PARTS = ["topA", "topB", "topRailA", "topRailB", "bottomRailA", "bottomRailB", "grilleA", "grilleB"]
TIMES = [10, 20, 30, 60, 90, 120]
END = 120.0
# the floor and the window wall inside the cabinet's footprint
FOOTPRINT = {"floor": lambda c: c[:, 0] < .330, "outerWall": lambda c: c[:, 1] < .756}


def read_heat(run):
    d = np.genfromtxt(run / "postProcessing/heatAccounting/heat.csv", delimiter=",", names=True)
    return d[np.r_[True, np.diff(d["time"]) > 0]]


def read_diag(run):
    d = np.atleast_1d(np.genfromtxt(run / "postProcessing/diagnostics57/diagnostics.csv", delimiter=",", names=True))
    return d[np.r_[True, np.diff(d["time"]) > 0]]


def log_stats(run):
    log = run / "log.buoyantPimpleFoam"
    if not log.exists():
        return None
    txt = log.read_text()
    steps = len(re.findall(r"^deltaT = ", txt, re.M))
    clock = re.findall(r"ClockTime = ([\d.eE+-]+) s", txt)
    nprocs = re.search(r"^nProcs : (\d+)", txt, re.M)
    caps = re.findall(r"Solving for p_rgh, Initial residual = [^,]+, Final residual = ([^,]+), No Iterations 100\b", txt)
    return steps, float(clock[-1]) if clock else float("nan"), int(nprocs[1]) if nprocs else 1, len(caps)


# ---- the heat stored in the footprint, from the layers in the written T --------------------
def _blocks(path):
    """The per-processor blocks of a collated file."""
    b = path.read_bytes()
    out, pos = [], 0
    pat = re.compile(rb"// processor(\d+)\n(\d+)\n\(")
    while True:
        m = pat.search(b, pos)
        if not m:
            return out
        n = int(m[2])
        out.append(b[m.end():m.end() + n])
        pos = m.end() + n


def _faces(run):
    """Every face's centre and area, from the undecomposed mesh."""
    pm = run / "constant/polyMesh"
    pts = np.array([list(map(float, a.split())) for a in re.findall(r"\(([-+\d.eE ]+)\)", (pm / "points").read_text())
                    if len(a.split()) == 3])
    faces = np.array([list(map(int, a.split())) for a in re.findall(r"4\(([^)]+)\)", (pm / "faces").read_text())])
    p = pts[faces]
    return p.mean(1), 0.5 * np.linalg.norm(np.cross(p[:, 2] - p[:, 0], p[:, 3] - p[:, 1]), axis=1)


def _layers(blk, patch, n):
    """radLayerWall's layer0..layerN-1 for one patch in one processor's block of T."""
    m = re.search(rb"\n    " + patch.encode() + rb"\n    \{", blk[blk.index(b"boundaryField"):])
    pos = blk.index(b"boundaryField") + m.end()
    nl = int(re.compile(rb"nLayers\s+(\d+);").search(blk, pos)[1])
    pos = re.compile(rb"nLayers\s+\d+;").search(blk, pos).end()
    d = {k: float(re.compile(k.encode() + rb"\s+([-+\d.eE]+);").search(blk, pos)[1]) for k in ("thickness", "rhoCp")}
    vals = np.full((nl, n), np.nan)
    pat = re.compile(rb"layer(\d+)\s+(?:nonuniform List<scalar>\s+(\d+)\s*(\(|;)|uniform\s+([-+\d.eE]+);)")
    for _ in range(nl):
        m = pat.search(blk, pos)
        j = int(m[1])
        if m[4] is not None:
            vals[j] = float(m[4])
            pos = m.end()
        elif m[3] == b";":
            pos = m.end()
        else:
            k = int(m[2])
            assert k == n, (k, n)
            vals[j] = np.frombuffer(blk, "<f8", k, m.end())
            pos = m.end() + 8 * k
    return vals, d["rhoCp"] * d["thickness"] / nl


def footprint_storage(run, time="120"):
    """Heat stored above 16 C in the floor's and the window wall's layers, J/m: each patch's
    whole, and the part inside the cabinet's footprint. None if the run has no collated write."""
    procs = sorted(p for p in run.glob("processors*") if (p / time / "T").exists())
    if not procs:
        return None
    p = procs[0]
    c, a = _faces(run)
    bnd = _blocks(p / "constant/polyMesh/boundary")
    fpa = _blocks(p / "constant/polyMesh/faceProcAddressing")
    Tb = _blocks(p / time / "T")
    res = {}
    for patch, inside in FOOTPRINT.items():
        tot = ins = 0.0
        for b, f, t in zip(bnd, fpa, Tb):
            m = re.search(patch.encode() + rb"\s*\{[^}]*?nFaces\s+(\d+);\s*startFace\s+(\d+);", b)
            n, s = int(m[1]), int(m[2])
            if n == 0:
                continue
            st = f.index(b"}") + 1 if f.lstrip().startswith(b"FoamFile") else 0
            h = re.compile(rb"\s*(\d+)\s*\(").match(f, st)
            addr = np.frombuffer(f, "<i4", int(h[1]), h.end())
            g = np.abs(addr[s:s + n]) - 1
            v, cap = _layers(t, patch, n)
            e = cap * a[g] * (v - T0).sum(0)
            tot += e.sum()
            ins += e[inside(c[g])].sum()
        res[patch] = {"patch": tot, "inside": ins}
    return res


# ---- the monitors ---------------------------------------------------------------------------
def run_results(run):
    d = read_heat(run)
    g = read_diag(run)
    init = json.loads((run / "initial.json").read_text())
    t = d["time"]
    dt = np.diff(np.r_[0, t])
    eref = d["Uzone"] - CP * T0 * d["zoneMass"]
    eref0 = init["initialZoneU_J"] - CP * T0 * init["initialZoneMass_kg"]
    zone = d["zoneEnthalpy"] + d["zoneDiffusion"] + np.diff(np.r_[eref0, eref]) / dt + np.diff(np.r_[0, d["KEzone"]]) / dt
    q = dict(total=zone + d["panelConvection"] + d["panelRadiation"], zone=zone, ironConv=d["panelConvection"],
             ironRad=d["panelRadiation"], glass=-(d["glassConv"] + d["glassRad"]),
             crossing=(d["coverGrossOut"] - d["coverGrossIn"] + d["coverDiffusion"] + d["coverOpeningRadiation"]
                       + d["mdfConvection"] + d["mdfRadiation"]))
    for k in ["frontOut_W", "frontIn_W", "topOut_W", "topIn_W", "frontDiffusion_W", "topDiffusion_W",
              "frontRadiation_W", "topRadiation_W", "mdfConvection", "mdfRadiation",
              "frontOut_kgs", "frontIn_kgs", "topOut_kgs", "topIn_kgs"]:
        q[k] = d[k]
    for p in WALLS:
        q[p + "In"] = -(d[p + "Conv"] + d[p + "Rad"])

    def at(key):
        E = np.r_[0, np.cumsum(q[key] * dt)]
        return lambda s: float(np.interp(s, np.r_[0, t], E))

    E = {k: at(k) for k in q}
    td = g["time"]

    def diag(key, s):
        return float(np.interp(s, td, g[key]))

    def mean(key, lo, hi):
        m = (t > lo + 1e-9) & (t <= hi + 1e-9)
        return float(np.sum(q[key][m] * dt[m]) / np.sum(dt[m]))

    # each layered patch: what it stored against minus its integrated wall heat flux
    lo, hi = max(1.0, float(td[0])), float(min(td[-1], t[-1]))
    layers = {p: (diag(p + "Storage_J", hi) - diag(p + "Storage_J", lo), E[p + "In"](hi) - E[p + "In"](lo)) for p in WALLS}
    # the whole section over 10-120 s: radiator in = air's internal energy + layers + glass out
    a, b = 10.0, hi
    budget = dict(inp=E["total"](b) - E["total"](a),
                  air=float(np.interp(b, t, d["Uroom"]) - np.interp(a, t, d["Uroom"])),
                  layers=sum(diag(p + "Storage_J", b) - diag(p + "Storage_J", a) for p in WALLS),
                  glass=E["glass"](b) - E["glass"](a))
    budget["residual"] = budget["inp"] - budget["air"] - budget["layers"] - budget["glass"]
    # the bare check: the output over 20-30 s against the rating at the mean of all the air
    m = (t > 20) & (t <= 30)
    Tm = np.sum((d["massT"] / d["mass"])[m] * dt[m]) / np.sum(dt[m])
    fit = dict(Tm=Tm, out=mean("total", 20, 30), rating=4154 * ((374.82 - Tm) / 80.56) ** 1.3)
    baffles = ({p: (float(g[p + "Min_K"].min()), float(g[p + "Max_K"].max())) for p in PARTS}
               if run.name != "bare" else {})
    return dict(name=run.name, t=t, last=float(t[-1]), q=q, E=E, diag=diag, mean=mean, layers=layers, span=(lo, hi),
                budget=budget, fit=fit, baffles=baffles,
                mass_drift=float(np.max(np.abs(d["mass"] / init["initialMass_kg"] - 1))),
                air=(float(g["airMin_K"].min()) - 273.15, float(g["airMax_K"].max()) - 273.15),
                storage=footprint_storage(run), log=log_stats(run))


def write_history(r, path, cabinet):
    path.parent.mkdir(parents=True, exist_ok=True)
    E, mean, diag = r["E"], r["mean"], r["diag"]
    with path.open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        head = ["start_s", "end_s", "output_W", "iron_convection_W", "iron_radiation_W", "convector_zone_W",
                "output_since_0_kJ", "glass_out_W", "glass_since_0_kJ"]
        if cabinet:
            head += ["out_of_cabinet_W", "out_of_cabinet_since_0_kJ", "front_out_kg_s", "front_in_kg_s",
                     "top_out_kg_s", "top_in_kg_s"]
        head += ["room_C", "cabinet_box_C"]
        w.writerow(head)
        for lo in np.arange(0, END, 2.5):
            hi = lo + 2.5
            row = [f"{lo:g}", f"{hi:g}", f"{mean('total', lo, hi):.2f}", f"{mean('ironConv', lo, hi):.2f}",
                   f"{mean('ironRad', lo, hi):.2f}", f"{mean('zone', lo, hi):.2f}", f"{E['total'](hi) / 1e3:.3f}",
                   f"{mean('glass', lo, hi):.2f}", f"{E['glass'](hi) / 1e3:.3f}"]
            if cabinet:
                row += [f"{mean('crossing', lo, hi):.2f}", f"{E['crossing'](hi) / 1e3:.3f}"]
                row += [f"{mean(k, lo, hi):.5f}" for k in ("frontOut_kgs", "frontIn_kgs", "topOut_kgs", "topIn_kgs")]
            row += [f"{diag('roomT_K', hi) - 273.15:.3f}", f"{diag('cabinetT_K', hi) - 273.15:.3f}"]
            w.writerow(row)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("runs")
    ap.add_argument("results")
    a = ap.parse_args()
    runs, out = Path(a.runs), Path(a.results)
    out.mkdir(parents=True, exist_ok=True)
    rr = {n: run_results(runs / n) for n in RUNS}
    for n, r in rr.items():
        write_history(r, out / n / "history.csv", n != "bare")
    B, S, P = rr["bare"], rr["solid"], rr["perforated"]
    bare = B["E"]["total"](END)
    patch = sum(v["inside"] for v in B["storage"].values()) if B["storage"] else None
    den = bare - patch if patch is not None else None

    with (out / "minutes.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["start_s", "end_s", "bare_output_W", "solid_output_W", "perforated_output_W",
                    "solid_out_of_cabinet_W", "perforated_out_of_cabinet_W",
                    "solid_out_over_bare_block", "perforated_out_over_bare_block",
                    "solid_out_since_0_kJ", "perforated_out_since_0_kJ",
                    "solid_like_for_like_since_0", "perforated_like_for_like_since_0",
                    "bare_glass_out_W", "solid_glass_out_W", "perforated_glass_out_W",
                    "bare_room_C_at_end", "solid_room_C_at_end", "perforated_room_C_at_end"])
        for lo in range(0, int(END), 30):
            hi = lo + 30
            mb = B["mean"]("total", lo, hi)
            row = [lo, hi] + [f"{r['mean']('total', lo, hi):.2f}" for r in (B, S, P)]
            row += [f"{r['mean']('crossing', lo, hi):.2f}" for r in (S, P)]
            row += [f"{r['mean']('crossing', lo, hi) / mb:.4f}" for r in (S, P)]
            row += [f"{r['E']['crossing'](hi) / 1e3:.3f}" for r in (S, P)]
            row += [f"{r['E']['crossing'](hi) / den:.4f}" if den else "" for r in (S, P)]
            row += [f"{r['mean']('glass', lo, hi):.2f}" for r in (B, S, P)]
            row += [f"{r['diag']('roomT_K', hi) - 273.15:.3f}" for r in (B, S, P)]
            w.writerow(row)

    s = []
    s.append("radiatorCabinetTop: figures from the runs' monitors (scripts/extract_results.py)")
    s.append("A steam radiator held at 215 F (374.82 K), bare, in a sheet-steel cabinet with a solid top and in the")
    s.append("same cabinet with a perforated top, 0-120 s from switch-on, W and J per metre of section")
    s.append("")
    for n, r in rr.items():
        lg = r["log"]
        extra = (f", {lg[0]} steps, {lg[1]:.0f} s of wall time on {lg[2]} ranks, {lg[3]} final pressure solves at 100 iterations"
                 if lg else "")
        s.append(f"{n}: monitored to t = {r['last']:g} s{extra}")
    s.append("")
    s.append("The radiator's heat from switch-on to 120 s, kJ/m")
    s.append("              output   iron conv.  iron rad.  convector zone   of bare")
    for n, r in rr.items():
        E = r["E"]
        s.append(f"  {n:10s} {E['total'](END) / 1e3:8.2f}   {E['ironConv'](END) / 1e3:8.2f}   {E['ironRad'](END) / 1e3:8.2f}"
                 f"   {E['zone'](END) / 1e3:8.2f}       {100 * E['total'](END) / bare:6.2f}%")
    s.append("")
    s.append("The heat out of the cabinet from switch-on to 120 s, kJ/m: carried out of and into the open strips,")
    s.append("radiation and diffusion through them, and convection and radiation off the sheet's outer faces")
    s.append("              front out  front in  top out  top in  strips rad.  strips diff.  sheet conv.  sheet rad.    net")
    for n in CABINETS:
        E = rr[n]["E"]
        s.append(f"  {n:10s}  {E['frontOut_W'](END) / 1e3:8.2f}  {E['frontIn_W'](END) / 1e3:8.2f}  {E['topOut_W'](END) / 1e3:7.2f}"
                 f"  {E['topIn_W'](END) / 1e3:6.2f}  {(E['frontRadiation_W'](END) + E['topRadiation_W'](END)) / 1e3:10.2f}"
                 f"  {(E['frontDiffusion_W'](END) + E['topDiffusion_W'](END)) / 1e3:11.2f}  {E['mdfConvection'](END) / 1e3:11.2f}"
                 f"  {E['mdfRadiation'](END) / 1e3:10.2f}  {E['crossing'](END) / 1e3:7.2f}")
    s.append("  The air through each cabinet over 100-120 s, kg/s per metre: "
             + "; ".join(f"{n} front out {rr[n]['mean']('frontOut_kgs', 100, 120):.4f}, in {rr[n]['mean']('frontIn_kgs', 100, 120):.4f},"
                         f" top out {rr[n]['mean']('topOut_kgs', 100, 120):.4f}, in {rr[n]['mean']('topIn_kgs', 100, 120):.4f}"
                         for n in CABINETS))
    s.append("")
    if B["storage"]:
        s.append("Heat stored in the floor and the window wall inside the cabinet's footprint (x < 0.330 m, y < 0.756 m)")
        s.append("at 120 s, kJ/m, from the layer temperatures in each run's T at 120 s; each patch's whole against its monitor")
        for n, r in rr.items():
            st = r["storage"]
            if not st:
                s.append(f"  {n:10s}  no write at 120 s")
                continue
            s.append(f"  {n:10s}  floor {st['floor']['inside'] / 1e3:6.2f}  wall {st['outerWall']['inside'] / 1e3:6.2f}"
                     f"  together {sum(v['inside'] for v in st.values()) / 1e3:6.2f}   (whole patches "
                     + ", ".join(f"{p} {v['patch'] / 1e3:.3f} against {r['diag'](p + 'Storage_J', END) / 1e3:.3f}" for p, v in st.items())
                     + ")")
        s.append("  The radiator's output less the heat out of the cabinet and the footprint's store, kJ/m (the cabinet's")
        s.append("  air, and what the balance does not account for): "
                 + ", ".join(f"{n} {(rr[n]['E']['total'](END) - rr[n]['E']['crossing'](END) - sum(v['inside'] for v in rr[n]['storage'].values())) / 1e3:.2f}"
                             f" ({100 * (rr[n]['E']['total'](END) - rr[n]['E']['crossing'](END) - sum(v['inside'] for v in rr[n]['storage'].values())) / rr[n]['E']['total'](END):.1f}% of its output)"
                             for n in CABINETS if rr[n]["storage"]))
        s.append("")
    s.append("Shares over 0-120 s")
    if den:
        s.append(f"  bare's heat {bare / 1e3:.2f} kJ/m, of it {patch / 1e3:.2f} into its own floor and wall in the cabinet's footprint,"
                 f" leaving {den / 1e3:.2f}")
    s.append("                                                              solid  perforated   gap (points)")

    def share(label, fs, fp):
        s.append(f"  {label:58s} {fs:6.2f}%   {fp:6.2f}%     {fp - fs:5.2f}")

    if den:
        share("heat out of the cabinet / bare's heat less its footprint", 100 * S["E"]["crossing"](END) / den,
              100 * P["E"]["crossing"](END) / den)
    share("heat out of the cabinet / bare's heat (the brief's count)", 100 * S["E"]["crossing"](END) / bare,
          100 * P["E"]["crossing"](END) / bare)
    share("the radiator's output / bare's", 100 * S["E"]["total"](END) / bare, 100 * P["E"]["total"](END) / bare)
    bnet = bare - B["E"]["glass"](END)
    share("heat out of the cabinet less the glass / bare's less its glass",
          100 * (S["E"]["crossing"](END) - S["E"]["glass"](END)) / bnet, 100 * (P["E"]["crossing"](END) - P["E"]["glass"](END)) / bnet)
    share("the radiator's output less the glass / bare's less its glass",
          100 * (S["E"]["total"](END) - S["E"]["glass"](END)) / bnet, 100 * (P["E"]["total"](END) - P["E"]["glass"](END)) / bnet)
    if den:
        s.append("The clip's count so far, heat out of the cabinet since switch-on / bare's heat at 120 s less its footprint")
        s.append("  " + "  ".join(f"{t:3d} s {100 * S['E']['crossing'](t) / den:5.2f} / {100 * P['E']['crossing'](t) / den:5.2f}%" for t in TIMES))
    s.append("The brief's count since switch-on, each against bare's heat to the same time, and the gap")
    s.append("  " + "  ".join(f"{t:3d} s {100 * S['E']['crossing'](t) / B['E']['total'](t):5.2f} / "
                              f"{100 * P['E']['crossing'](t) / B['E']['total'](t):5.2f}% ({100 * (P['E']['crossing'](t) - S['E']['crossing'](t)) / B['E']['total'](t):4.1f})"
                              for t in TIMES))
    s.append("Each half minute on its own, heat out of the cabinet / bare's heat in the same half minute")
    for lo in range(0, int(END), 30):
        mb = B["mean"]("total", lo, lo + 30)
        fs, fp = S["mean"]("crossing", lo, lo + 30) / mb, P["mean"]("crossing", lo, lo + 30) / mb
        s.append(f"  {lo:3d}-{lo + 30:3d} s  bare {mb:7.1f} W/m  solid {100 * fs:5.1f}%  perforated {100 * fp:5.1f}%  gap {100 * (fp - fs):4.1f}")
    s.append("")
    s.append("The glass, kJ/m lost from switch-on to 120 s, and as a share of the heat that left the cabinet (bare: the radiator's)")
    s.append("  " + "   ".join(f"{n} {r['E']['glass'](END) / 1e3:.2f} ({100 * r['E']['glass'](END) / r['E']['crossing' if n != 'bare' else 'total'](END):.1f}%)"
                               for n, r in rr.items()))
    s.append("")
    s.append("At each time: the radiator's output now (W/m) and the air outside the cabinet's box (x < 0.330 m,")
    s.append("y < 0.756 m), mass-weighted, C (in bare the same box, the radiator's own air, is left out)")
    s.append("     t      output                     room air")
    s.append("          bare   solid  perforated     bare   solid  perforated")
    for t in TIMES:
        o = [float(np.interp(t, r["t"], r["q"]["total"])) for r in (B, S, P)]
        a_ = [r["diag"]("roomT_K", t) - 273.15 for r in (B, S, P)]
        s.append(f"  {t:4d}  {o[0]:6.0f}  {o[1]:6.0f}  {o[2]:6.0f}      {a_[0]:6.2f}  {a_[1]:6.2f}  {a_[2]:6.2f}")
    s.append("")
    f = B["fit"]
    s.append(f"bare, the convector's check: over 20-30 s the radiator gives {f['out']:.1f} W/m with all the air at {f['Tm'] - 273.15:.3f} C,")
    s.append(f"  against the rating's {f['rating']:.1f} W/m at that temperature (4,154 W/m x (dT/80.56)^1.3), {100 * f['out'] / f['rating']:.2f}%")
    s.append("")
    s.append("Heat budget over 10-120 s, kJ/m: the radiator's heat = rise of the air's internal energy,")
    s.append("(cv/R) integral p dV, + heat stored in the wall layers + heat out through the glass")
    s.append("              radiator     air   layers   glass  residual")
    for n, r in rr.items():
        b = r["budget"]
        s.append(f"  {n:10s}  {b['inp'] / 1e3:7.3f} {b['air'] / 1e3:7.3f} {b['layers'] / 1e3:8.3f} {b['glass'] / 1e3:7.3f}"
                 f"  {b['residual'] / 1e3:+.4f} ({100 * b['residual'] / b['inp']:+.3f}%)")
    s.append("Each layer's stored heat against minus its integrated wall heat flux (convection and the")
    s.append(f"radiation it absorbs), {rr['bare']['span'][0]:g}-{rr['bare']['span'][1]:g} s, error %")
    for n, r in rr.items():
        s.append(f"  {n:10s} " + "  ".join(f"{p} {100 * (St - Fl) / Fl:+.4f}" for p, (St, Fl) in r["layers"].items()))
    s.append("")
    for n, r in rr.items():
        line = (f"{n}: air mass within {r['mass_drift']:.2e} of the start's; air {r['air'][0]:.2f} to {r['air'][1]:.2f} C "
                "(each second; the iron and the convector zone are held at 101.67)")
        if r["baffles"]:
            lo = min(v[0] for v in r["baffles"].values()) - 273.15
            hi = max(v[1] for v in r["baffles"].values()) - 273.15
            line += f"; the sheet's faces {lo:.2f} to {hi:.2f} C"
        s.append(line)
    (out / "summary.txt").write_text("\n".join(s) + "\n")
    print("\n".join(s))


if __name__ == "__main__":
    main()
