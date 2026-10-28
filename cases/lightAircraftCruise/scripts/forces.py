#!/usr/bin/env python3
"""Lift and drag of each run, split by part, with the checks the README quotes.

    python3 scripts/forces.py runs/aoa4 runs/aoa0 ...

For each run: CL, CD and L/D of the whole aircraft over the last AVG iterations, how
much they moved between the last two halves of that window, and each part's share split
into pressure and viscous drag. Coefficients use the full wing's planform area and the
full aircraft; the solve is a half model and its forces are doubled.

Then the checks: the lift against the weight of a 600 kg light aircraft; the lift
slope and zero-lift angle between runs against lifting-line theory for this planform
(Glauert's solution with the thin-aerofoil section, computed here); the drag against
a component build-up from flat-plate friction and form factors.
"""
import json
import math
import os
import re
import sys

import numpy as np

AVG = 200                 # iterations averaged
RHO, U, NU, G = 1.225, 45.0, 1.5e-5, 9.81
MASS = 600.0              # kg, the light-sport aircraft weight limit (EASA CS-LSA, FAA LSA)
PARTS = ("wing", "fuselage", "tailplane", "fin")
HERE = os.path.dirname(os.path.abspath(__file__))
geo = json.load(open(os.path.join(HERE, "..", "geometry", "geometry.json")))
S, B, MAC = geo["wing_reference_area_m2"], geo["span_m"], geo["mean_aerodynamic_chord_m"]
AR = B * B / S
Q = 0.5 * RHO * U * U


def table(path):
    """A postProcessing .dat file as {column name: array}."""
    head, rows = None, []
    for line in open(path):
        if line.startswith("#"):
            if re.match(r"#\s*Time", line):
                head = line[1:].split()
            continue
        if line.strip():
            rows.append([float(v) for v in line.replace("(", " ").replace(")", " ").split()])
    a = np.array(rows)
    return {h: a[:, i] for i, h in enumerate(head)} if head and len(head) == a.shape[1] \
        else {str(i): a[:, i] for i in range(a.shape[1])}


def latest(dirpath, name):
    """The file `name` in the latest start-time directory under dirpath."""
    times = sorted(os.listdir(dirpath), key=float)
    return os.path.join(dirpath, times[-1], name)


def flight(run):
    d = {}
    for line in open(os.path.join(run, "system", "flightCondition")):
        m = re.match(r"(\w+)\s+\(?([-\d.eE+ ]+)\)?;", line)
        if m:
            v = [float(x) for x in m.group(2).split()]
            d[m.group(1)] = np.array(v) if len(v) > 1 else v[0]
    return d


def window(x):
    """Mean of the last AVG values, and the change between its two halves."""
    w = x[-AVG:]
    h = len(w) // 2
    return float(w.mean()), float(w[h:].mean() - w[:h].mean())


def thin_aerofoil_alpha0(m=0.02, p=0.4):
    """Zero-lift angle of a NACA 4-digit camber line, thin-aerofoil theory, rad."""
    th = np.linspace(0, np.pi, 20001)
    x = 0.5 * (1 - np.cos(th))
    dyc = np.where(x < p, 2 * m / p**2 * (p - x), 2 * m / (1 - p) ** 2 * (p - x))
    f = dyc * (np.cos(th) - 1)
    return -float(np.sum(0.5 * (f[1:] + f[:-1]) * np.diff(th))) / np.pi


def lifting_line(alpha_rad, alpha0, a0=2 * np.pi, n=40):
    """Glauert's monoplane equation for the straight-tapered, untwisted wing.
    Returns (CL, CDi, e) of the wing alone, based on its own planform area."""
    cr = 2 * S / (B * (1 + geo["taper_ratio"]))
    ct = cr * geo["taper_ratio"]
    k = np.arange(1, 2 * n, 2)                        # odd terms, symmetric loading
    th = np.linspace(0, np.pi / 2, n + 1)[1:]
    c = cr + (ct - cr) * np.abs(np.cos(th))
    mu = c * a0 / (4 * B)
    A = np.sin(np.outer(th, k)) * (mu[:, None] * k[None, :] + np.sin(th)[:, None])
    An = np.linalg.solve(A, mu * (alpha_rad - alpha0) * np.sin(th))
    CL = np.pi * AR * An[0]
    CDi = np.pi * AR * float(np.sum(k * An**2))
    return CL, CDi, (CL * CL / (np.pi * AR * CDi) if CDi > 0 else float("nan"))


def friction(re):
    """Turbulent flat plate, Schlichting's fit."""
    return 0.455 / math.log10(re) ** 2.58


def run_result(run):
    fl = flight(run)
    ld, dd = fl["liftDir"], fl["dragDir"]
    c = table(latest(os.path.join(run, "postProcessing", "coeffs"), "coefficient.dat"))
    CL, dCL = window(c["Cl"])
    CD, dCD = window(c["Cd"])
    parts = {}
    for p in PARTS:
        f = table(latest(os.path.join(run, "postProcessing", f"force_{p}"), "force.dat"))
        vec = lambda kind: np.array([window(f[f"{kind}_{ax}"])[0] for ax in "xyz"])
        pr, vi = vec("pressure"), vec("viscous")
        # half model: double the force, divide by the full area
        parts[p] = {"CL": 2 * float((pr + vi) @ ld) / (Q * S),
                    "CD_pressure": 2 * float(pr @ dd) / (Q * S),
                    "CD_viscous": 2 * float(vi @ dd) / (Q * S)}
    yp = {}
    for p in PARTS:
        d = os.path.join(run, "postProcessing", f"yPlus_{p}")
        if os.path.isdir(d):
            t = table(latest(d, "surfaceFieldValue.dat"))
            cols = {k.lower(): v for k, v in t.items()}
            yp[p] = {"area_half_m2": float(cols["area"][-1]) if "area" in cols else None,
                     "yPlus_mean": float([v for k, v in cols.items()
                                          if "yplus" in k][0][-1])}
    return {"run": run, "alpha": float(fl["alphaDeg"]), "iterations": int(c["Time"][-1]),
            "CL": CL, "CD": CD, "dCL": dCL, "dCD": dCD, "parts": parts, "yPlus": yp}


def main(runs):
    res = [run_result(r) for r in runs]
    a0 = thin_aerofoil_alpha0()
    print(f"Half model doubled. q = {Q:.1f} Pa, S = {S:.3f} m2, MAC = {MAC:.4f} m, "
          f"AR = {AR:.3f}, Re(MAC) = {U * MAC / NU:.3g}")
    print(f"Means over the last {AVG} iterations; 'moved' is the last {AVG // 2} "
          f"against the {AVG // 2} before.\n")
    for r in res:
        L = r["CL"] * Q * S
        D = r["CD"] * Q * S
        print(f"== {r['run']}: alpha {r['alpha']:g} deg, {r['iterations']} iterations")
        print(f"   CL {r['CL']:.4f} (moved {r['dCL']:+.1e})   CD {r['CD']:.5f} "
              f"(moved {r['dCD']:+.1e})   L/D {r['CL'] / r['CD']:.1f}")
        print(f"   lift {L:.0f} N = weight of {L / G:.0f} kg; drag {D:.0f} N")
        print(f"   {'part':10s} {'CL':>8s} {'CD':>9s} {'pressure':>9s} {'viscous':>9s}")
        sp = {k: 0.0 for k in ("CL", "CD", "p", "v")}
        for p, v in r["parts"].items():
            cd = v["CD_pressure"] + v["CD_viscous"]
            print(f"   {p:10s} {v['CL']:8.4f} {cd:9.5f} {v['CD_pressure']:9.5f} "
                  f"{v['CD_viscous']:9.5f}")
            sp["CL"] += v["CL"]; sp["CD"] += cd
            sp["p"] += v["CD_pressure"]; sp["v"] += v["CD_viscous"]
        print(f"   {'sum':10s} {sp['CL']:8.4f} {sp['CD']:9.5f} {sp['p']:9.5f} {sp['v']:9.5f}")
        if r["yPlus"]:
            print("   y+ (area mean): " + ", ".join(
                f"{p} {v['yPlus_mean']:.0f}" for p, v in r["yPlus"].items()))
        print()

    print("== Checks")
    W = MASS * G
    for r in res:
        print(f"   alpha {r['alpha']:g}: CL needed to carry {MASS:.0f} kg at {U:g} m/s "
              f"= {W / (Q * S):.3f}; the solve gives {r['CL']:.3f}")
    print(f"   lifting line (thin-aerofoil section: slope 2 pi, zero lift at "
          f"{math.degrees(a0):.2f} deg), wing alone:")
    for r in res:
        CLt, CDi, e = lifting_line(math.radians(r["alpha"]), a0)
        wf = r["parts"]["wing"]["CL"] + r["parts"]["fuselage"]["CL"]
        print(f"     alpha {r['alpha']:g}: theory CL {CLt:.4f}, e {e:.3f}, CDi {CDi:.5f}; "
              f"solve: wing + fuselage CL {wf:.4f}, whole aircraft {r['CL']:.4f}")
    if len(res) >= 2:
        r1, r2 = sorted(res, key=lambda r: r["alpha"])[:2]
        da = r2["alpha"] - r1["alpha"]
        slope = (r2["CL"] - r1["CL"]) / da
        wf = lambda r: r["parts"]["wing"]["CL"] + r["parts"]["fuselage"]["CL"]
        slope_wf = (wf(r2) - wf(r1)) / da
        th = (lifting_line(math.radians(r2["alpha"]), a0)[0]
              - lifting_line(math.radians(r1["alpha"]), a0)[0]) / da
        print(f"   lift slope {r1['alpha']:g} to {r2['alpha']:g} deg, per degree: whole aircraft "
              f"{slope:.4f}, wing + fuselage {slope_wf:.4f}; lifting line {th:.4f}")
        print(f"   zero-lift angle: whole aircraft {r1['alpha'] - r1['CL'] / slope:.2f} deg, "
              f"wing + fuselage {r1['alpha'] - wf(r1) / slope_wf:.2f} deg; "
              f"thin aerofoil {math.degrees(a0):.2f} deg")
    # Component build-up of the zero-lift drag: flat-plate friction on each part's
    # wetted area (measured off the mesh when the y+ files carry it), times a form factor.
    r = res[0]
    if all(r["yPlus"].get(p, {}).get("area_half_m2") for p in PARTS):
        ff_wing = 1 + 0.6 / 0.3 * 0.12 + 100 * 0.12**4      # Raymer, t/c 0.12 at 0.3c
        fr = geo["fuselage_length_m"] / geo["fuselage_diameter_m"]
        ff_fus = 1 + 60 / fr**3 + fr / 400
        lens = {"wing": MAC, "tailplane": 0.18 * 4, "fin": 0.2 * 4,
                "fuselage": geo["fuselage_length_m"]}
        cd0 = 0.0
        for p in PARTS:
            sw = 2 * r["yPlus"][p]["area_half_m2"]
            ff = ff_fus if p == "fuselage" else ff_wing
            cd0 += friction(U * lens[p] / NU) * ff * sw / S
        print(f"   drag build-up, flat-plate friction x form factor on the wetted areas: "
              f"CD0 {cd0:.5f}")
        for r in res:
            CDi = lifting_line(math.radians(r["alpha"]), a0)[1]
            e = lifting_line(math.radians(r["alpha"]), a0)[2]
            cdi = r["CL"] ** 2 / (math.pi * AR * e)
            print(f"     alpha {r['alpha']:g}: CD0 + CL^2/(pi AR e) = {cd0 + cdi:.5f} "
                  f"(induced {cdi:.5f}); the solve {r['CD']:.5f}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: forces.py runs/aoa4 [runs/aoa0 ...]")
    main(sys.argv[1:])
