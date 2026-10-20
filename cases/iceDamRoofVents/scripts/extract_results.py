#!/usr/bin/env python3
"""Histories, the snow base along the roof and the summary from the solved runs.

    python3 scripts/extract_results.py runs results

Reads each run's deck readout (postProcessing/deckT/<t>/T_deck.raw, the deck underside's
temperature face by face at every write, 7.5 s apart) and its monitors (atticT, wallHeatFlux,
flowSum_<opening>, flowSummag_<opening>), joining their start folders: a run continued from a
later time writes a second folder named after that time, whose rows replace the first's from
then on. Writes:

- results/<run>/history.csv, one row per write: the share of the roof over the attic with its
  snow base above 0 C, over both slopes and over each; the deck underside's warmest face over
  the attic; the attic air's mean temperature; the heat through the ceiling (in), the deck
  (out) and, vented, the soffit and fascia boards, W per metre of house; and the mass flow in
  and out at each opening, g/s per metre of house;
- results/<run>/snowbase.csv: the snow base along the roof, face by face, averaged over the
  number's window (and, buried, over the clip's last five minutes too);
- results/summary.txt.

The share is the slope length from each wall's outer face (|x| = 4.572 m) to the ridge where
the snow base, T_out + F (T_deck - T_out) with F = (R_snow + R_film)/R_roof, is above 0 C; the
overhangs are left out. Each solved face counts for half the distance to its neighbours on its
side. Where the buried insulation touches the deck (|x| from 3.922 to 4.572 m) there is no
air, and the base comes from the one-dimensional path from the room through the insulation's
local depth and up through the roof. The number is the mean over the writes of a five-minute
window, both ends included (41 writes).

Needs NumPy.
"""
import glob
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import roof  # noqa: E402

RUNS, OUT = sys.argv[1], sys.argv[2]
SEC = 1.0 / math.cos(math.atan(roof.SLOPE))
T_MELT_DECK = roof.T_OUT + (273.15 - roof.T_OUT) / roof.F_BASE   # deck underside at which the base melts
CP, R_GAS, P0 = 1005.0, 8314.47 / 28.96, 1e5
WINDOW = {"vented": (3300.0, 3600.0), "buried": (6900.0, 7200.0)}
lines = []


def say(s=""):
    print(s)
    lines.append(s)


def base(t_deck):
    return roof.T_OUT + roof.F_BASE * (t_deck - roof.T_OUT)


def joined(run, name, fname):
    """Rows of a monitor from every start folder, a later start replacing rows from its start on."""
    rows = []
    for d in sorted(glob.glob(f"{RUNS}/{run}/postProcessing/{name}/*"), key=lambda p: float(os.path.basename(p))):
        t0 = float(os.path.basename(d))
        rows = [r for r in rows if float(r[0]) < t0]
        rows += [l.split() for l in open(os.path.join(d, fname)) if l.strip() and not l.startswith("#")]
    return rows


def contact(variant):
    """Per side: (length along the slope with the base above 0 C, length) of the contact strip,
    and the snow base at the wall and where the air wedge begins."""
    if variant != "buried":
        return 0.0, 0.0, None, None
    x0, x1, n = roof.x_wedge_buried(), roof.W2, 400

    def b(x):
        q = (roof.T_ROOM - roof.T_OUT) / (roof.R_FILM + roof.R_CEIL * roof.deck(x) / roof.D_INS + roof.R_ROOF)
        return roof.T_OUT + q * (roof.R_SNOW + roof.R_FILM)
    above = sum((x1 - x0) / n for i in range(n) if b(x0 + (i + 0.5) * (x1 - x0) / n) > 273.15)
    return above * SEC, (x1 - x0) * SEC, b(x1) - 273.15, b(x0) - 273.15


def lengths(variant, a):
    """Slope length each face over the attic stands for."""
    L = np.zeros(len(a))
    for s in (-1, 1):
        i = np.where(a[:, 0] * s > 0)[0]
        i = i[np.argsort(np.abs(a[i, 0]))]
        ax = np.abs(a[i, 0])
        hi_end = roof.W2 if variant == "vented" else ax[-1] + (ax[-1] - ax[-2]) / 2
        e = np.concatenate([[ax[0] - (ax[1] - ax[0]) / 2], (ax[1:] + ax[:-1]) / 2, [hi_end]])
        L[i] = np.diff(e) * SEC
    return L


def shares(variant, a):
    """(both slopes, left, right) share with the snow base above 0 C."""
    a = a[np.abs(a[:, 0]) <= roof.W2]
    L = lengths(variant, a)
    melt = base(a[:, 3]) > 273.15
    ca, cl = contact(variant)[:2]
    out = []
    for m in (np.ones(len(a), bool), a[:, 0] < 0, a[:, 0] > 0):
        n = 1 if m.all() else 0.5
        out.append(((L * melt * m).sum() + 2 * n * ca) / ((L * m).sum() + 2 * n * cl))
    return out


def deck(run, t):
    a = np.loadtxt(f"{RUNS}/{run}/postProcessing/deckT/{t:g}/T_deck.raw")
    return a[np.lexsort((a[:, 0],))]


def wmean(ts, v, t0, t1):
    m = (ts >= t0) & (ts <= t1)
    return v[m].mean(), int(m.sum())


summary = {}
for run in ("vented", "buried"):
    if not os.path.isdir(f"{RUNS}/{run}"):
        continue
    variant = open(f"{RUNS}/{run}/caseInfo").read().split()[1]
    openings = ("soffitVent", "ridge") if variant == "vented" else ("ridge",)
    ts = np.array(sorted(float(os.path.basename(d)) for d in glob.glob(f"{RUNS}/{run}/postProcessing/deckT/*")
                         if os.path.exists(os.path.join(d, "T_deck.raw"))))
    sh = np.array([shares(variant, deck(run, t)) for t in ts])
    dmax = np.array([deck(run, t)[np.abs(deck(run, t)[:, 0]) <= roof.W2, 3].max() for t in ts])

    at = np.array([[float(r[0]), float(r[1])] for r in joined(run, "atticT", "volFieldValue.dat")])
    hf = {}
    for r in joined(run, "wallHeatFlux", "wallHeatFlux.dat"):
        hf.setdefault(r[1], []).append((float(r[0]), float(r[4])))
    hf = {k: np.array(v) for k, v in hf.items()}
    fl = {}
    for o in openings:
        s = np.array([[float(r[0]), float(r[1])] for r in joined(run, f"flowSum_{o}", "surfaceFieldValue.dat")])
        g = np.array([[float(r[0]), float(r[1])] for r in joined(run, f"flowSummag_{o}", "surfaceFieldValue.dat")])
        fl[o] = (s, g)

    def at_t(arr, t):
        return np.interp(t, arr[:, 0], arr[:, 1])

    cols = ["t_s", "share_pct", "share_left_pct", "share_right_pct", "deck_max_C", "attic_air_C",
            "ceiling_in_W", "deck_out_W"] + (["boards_out_W"] if variant == "vented" else [])
    for o in openings:
        cols += [f"{o}_in_g_s", f"{o}_out_g_s"]
    rows = []
    for k, t in enumerate(ts):
        row = [t, *(100 * sh[k]), dmax[k] - 273.15, at_t(at, t) - 273.15, at_t(hf["insulation"], t),
               -at_t(hf["deck"], t)]
        if variant == "vented":
            row.append(-(at_t(hf["soffit"], t) + at_t(hf["fascia"], t)))
        for o in openings:
            net, gross = at_t(fl[o][0], t), at_t(fl[o][1], t)
            row += [1e3 * (gross - net) / 2, 1e3 * (gross + net) / 2]
        rows.append(row)
    os.makedirs(f"{OUT}/{run}", exist_ok=True)
    with open(f"{OUT}/{run}/history.csv", "w") as f:
        f.write(",".join(cols) + "\n")
        for r in rows:
            f.write(",".join(f"{v:.6g}" for v in r) + "\n")

    # the snow base along the roof over the number's window (and the clip's last five minutes)
    wins = [WINDOW[variant]] + ([(3300.0, 3600.0)] if variant == "buried" else [])
    prof = []
    for t0, t1 in wins:
        d = [deck(run, t) for t in ts if t0 <= t <= t1]
        prof.append(np.mean([q[:, 3] for q in d], axis=0))
    x = deck(run, ts[-1])[:, 0]
    with open(f"{OUT}/{run}/snowbase.csv", "w") as f:
        f.write("x_m,over_attic," + ",".join(f"snow_base_{t0:g}_{t1:g}_s_C" for t0, t1 in wins) + "\n")
        for i in range(len(x)):
            f.write(f"{x[i]:.6g},{int(abs(x[i]) <= roof.W2)}," + ",".join(f"{base(p[i]) - 273.15:.6g}" for p in prof) + "\n")

    # polygon area for the heat the attic's air stores
    p = np.array([(px, py) for px, py, _ in roof.polygon(variant)])
    A = 0.5 * abs(np.dot(p[:, 0], np.roll(p[:, 1], 1)) - np.dot(p[:, 1], np.roll(p[:, 0], 1)))
    summary[run] = dict(variant=variant, ts=ts, sh=sh, dmax=dmax, at=at, hf=hf, fl=fl, A=A, openings=openings)

# ------------------------------------------------------------------------------ summary
say("iceDamRoofVents: figures from the solved runs (scripts/extract_results.py)")
say()
ca, cl, bw, bx = contact("buried")
say(f"roof to the night air {roof.R_ROOF:.3f} m2K/W; the snow base is above 0 C where the deck's underside is above "
    f"{T_MELT_DECK - 273.15:+.3f} C")
say(f"roof over the attic, wall to ridge: {roof.W2 * SEC:.3f} m a side along the slope")
say(f"buried, where the insulation touches the deck: |x| {roof.x_wedge_buried():.4f}-{roof.W2:.3f} m, {cl:.3f} m a side "
    f"along the slope ({100 * cl / (roof.W2 * SEC):.1f}% of the roof over the attic); snow base {bw:+.2f} C at the wall, "
    f"{bx:+.2f} C where the air begins; {100 * ca / cl:.0f}% of it above 0 C at every write")
for run, s in summary.items():
    ts, sh, at = s["ts"], s["sh"], s["at"]
    say()
    say(f"{run}: {len(ts)} writes, {ts[0]:g}-{ts[-1]:g} s")
    t0, t1 = WINDOW[run]
    m, n = wmean(ts, sh[:, 0], t0, t1)
    ml, _ = wmean(ts, sh[:, 1], t0, t1)
    mr, _ = wmean(ts, sh[:, 2], t0, t1)
    say(f"  THE NUMBER: share of the roof over the attic with its snow base above 0 C, mean of {t0:g}-{t1:g} s "
        f"({n} writes): {100 * m:.2f}% -> {round(100 * m)}%   (left slope {100 * ml:.1f}%, right {100 * mr:.1f}%)")
    say("  share in five-minute windows (mean of the writes, both ends included):")
    w = []
    for a0 in np.arange(0, ts[-1], 300.0):
        v, k = wmean(ts, sh[:, 0], a0, a0 + 300)
        vl, _ = wmean(ts, sh[:, 1], a0, a0 + 300)
        vr, _ = wmean(ts, sh[:, 2], a0, a0 + 300)
        w.append(f"    {a0:6g}-{a0 + 300:<6g} s {100 * v:6.2f}%  (left {100 * vl:5.1f}%, right {100 * vr:5.1f}%)")
    for l in w:
        say(l)
    say(f"  share at single writes: largest {100 * sh[:, 0].max():.2f}% (at {ts[sh[:, 0].argmax()]:g} s), "
        f"smallest {100 * sh[:, 0].min():.2f}% (at {ts[sh[:, 0].argmin()]:g} s); at 3600 s {100 * sh[ts == 3600, 0][0]:.2f}%")
    say(f"  deck underside over the attic, warmest face: {s['dmax'][ts >= ts[-1] - 300].max() - 273.15:+.2f} C over the last 300 s; "
        f"largest at any write {s['dmax'].max() - 273.15:+.2f} C")
    # the attic air: where it ends, and when it got within 0.1 K of that
    fin = at[at[:, 0] >= ts[-1] - 300, 1].mean()
    off = np.abs(at[:, 1] - fin) > 0.1
    t_in = at[np.where(off)[0][-1] + 1, 0] if off.any() else at[0, 0]
    say(f"  attic air, mean: {at[np.argmin(abs(at[:, 0] - 3600)), 1] - 273.15:+.3f} C at 3600 s; "
        f"{fin - 273.15:+.2f} C over the last 300 s, within 0.1 K of it for good from {t_in:.0f} s")
    say("  heat and flow per metre of house, five-minute time means:")
    for a0 in (1500, 3300) + ((6900,) if ts[-1] >= 7200 else ()):
        a1 = a0 + 300
        mm = (at[:, 0] >= a0) & (at[:, 0] <= a1)
        k = np.polyfit(at[mm, 0], at[mm, 1], 1)[0]
        store = P0 / (R_GAS * at[mm, 1].mean()) * CP * s["A"] * k
        hf = {p: v[(v[:, 0] >= a0) & (v[:, 0] <= a1), 1].mean() for p, v in s["hf"].items()}
        qin, qdeck = hf["insulation"], -hf["deck"]
        qb = -sum(v for p, v in hf.items() if p not in ("insulation", "deck"))
        fls = []
        for o in s["openings"]:
            sm, g = s["fl"][o]
            net = sm[(sm[:, 0] >= a0) & (sm[:, 0] <= a1), 1].mean()
            gr = g[(g[:, 0] >= a0) & (g[:, 0] <= a1), 1].mean()
            fls.append(f"{o} in {1e3 * (gr - net) / 2:.2f} g/s, out {1e3 * (gr + net) / 2:.2f} g/s")
        say(f"    {a0}-{a1} s: attic air {at[mm, 1].mean() - 273.15:+.2f} C, rising {1e4 * k:+.2f}e-4 K/s; ceiling in "
            f"{qin:.2f} W, deck out {qdeck:.2f} W" + (f", boards out {qb:.3f} W" if run == "vented" else "")
            + f", stored {store:.2f} W, so the openings carry {qin - qdeck - qb - store:.2f} W; " + "; ".join(fls))
    if ts[-1] > 3600:
        say("  across the restart at 3600 s (share, attic air):")
        for t in ts[(ts >= 3585) & (ts <= 3615)]:
            say(f"    {t:7.1f} s  {100 * sh[ts == t, 0][0]:6.2f}%  {np.interp(t, at[:, 0], at[:, 1]) - 273.15:+.3f} C")
        late = (ts >= ts[-1] - 1200)
        k = np.polyfit(ts[late], sh[late, 0], 1)[0]
        say(f"  share over the last 20 minutes: linear trend {100 * k * 600:+.2f} points per 10 minutes")
open(f"{OUT}/summary.txt", "w").write("\n".join(lines) + "\n")
