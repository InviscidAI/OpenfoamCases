#!/usr/bin/env python3
"""Histories, the film along the windscreen and the summary from the solved runs.

    python3 scripts/extract_results.py runs results

Reads each run's two monitors, both written by the coded function object `walls`:

- postProcessing/glass/<t>/{windscreen,rearScreen}.dat at every write (1.25 s apart): each glass
  face's centre x, y, temperature (C) and film of water (kg/m2);
- postProcessing/walls/<t0>/walls.dat every 20 steps: each screen's misted share, film and mean
  temperature, the cabin's vapour, mist and mean temperature, the flows of air, vapour and mist
  through the defroster, the recirculation intake and the rear vent, the air at the two heads,
  and the side glass the section stands for.

The faces are sorted along each screen from its first point (the windscreen from its foot at the
dash to the header, the rear screen from its top to its lip), and each face's stretch runs half
way to its neighbours. A face is misted while its film is above 1e-5 kg/m2 (physics.FILM_CLEAR).
The windscreen's misted share is the misted length over the screen's 1.062 m; in a section, the
length share is the area share. The flows are per metre of section (the run is 1 m thick).

Writes:

- results/<run>/history.csv, one row per write: both screens' misted share, mean film and mean
  temperature from the face-by-face files, and, interpolated in time from walls.dat, the cabin's
  mean air and the air at the heads, the defroster's supply temperature, the intake's vapour and
  mist (recirc), the cabin's vapour and mist and the side glass's misted share;
- results/<run>/windscreen_film.csv: the film along the windscreen, face by face, every 30 s;
- results/summary.txt: every figure the README quotes from the runs.

Needs NumPy.
"""
import glob
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import physics as P  # noqa: E402
import warmup_reference as REF  # noqa: E402

W0, W1 = np.array([0.03, 0.795]), np.array([0.98, 1.27])        # geometry.py
R1, RF = np.array([2.30, 1.235]), np.array([2.58, 0.94188])
SCREENS = {"windscreen": (W0, W1), "rearScreen": (R1, RF)}
DT_WRITE = 1.25
S_EACH = 70.0 / 3600e3 / P.WIDTH          # kg/s per metre, each occupant
OPACITY = lambda film: np.where(film > P.FILM_CLEAR, np.minimum(film / P.FILM0, 1.0) ** (2 / 3), 0.0)


def load_walls(run):
    files = sorted(glob.glob(os.path.join(run, "postProcessing", "walls", "*", "walls.dat")),
                   key=lambda f: float(f.split(os.sep)[-2]))
    head, rows = None, []
    for f in files:
        with open(f) as fh:
            h = fh.readline().split()[1:]
            head = head or h
            assert h == head, f
            for line in fh:
                v = line.split()
                if len(v) == len(head) and (not rows or float(v[0]) > rows[-1][0]):
                    rows.append([float(x) for x in v])
    d = np.array(rows)
    return {k: d[:, i] for i, k in enumerate(head)}


def load_glass(run, name):
    p0, p1 = SCREENS[name]
    L = np.linalg.norm(p1 - p0)
    e = (p1 - p0) / L
    root = os.path.join(run, "postProcessing", "glass")
    times = sorted((float(t) for t in os.listdir(root)), key=float)
    first = None
    film, temp = [], []
    for t in times:
        d = np.loadtxt(os.path.join(root, f"{t:g}", f"{name}.dat"))
        if first is None:
            first = d[:, :2]
            s = (first - p0) @ e
            o = np.argsort(s)
        assert np.allclose(d[:, :2], first, atol=1e-9), (name, t)
        film.append(d[o, 3])
        temp.append(d[o, 2])
    s = s[o]
    edges = np.r_[0.0, (s[1:] + s[:-1]) / 2, L]
    return np.array(times), s, np.diff(edges), L, np.array(film), np.array(temp)


def share(film, dl, L, thresh=P.FILM_CLEAR):
    return ((film > thresh) * dl).sum(-1) / L


def main():
    src, dst = sys.argv[1], sys.argv[2]
    out = []
    pr = out.append
    pr("foggyWindscreen: figures from the solved runs (scripts/extract_results.py)")
    pr("")
    pr(f"starting film {P.FILM0 * 1e3:g} g/m2 on both screens; a face is misted while its film is above "
       f"{P.FILM_CLEAR * 1e3:g} g/m2 ({P.FILM_CLEAR / P.FILM0:.1%} of the start)")
    pr(f"occupants' water: {2 * 70} g/h in the car, {2 * S_EACH * 1e6:.4f} mg/s per metre of section")
    ref = {m: np.array(REF.run(m)) for m in ("outside", "recirc")}      # t, cabin, mass, supply every 10 s
    data = {}
    for run in ("outside", "recirc"):
        rd = os.path.join(src, run)
        W = load_walls(rd)
        tw, s, dl, L, film, temp = load_glass(rd, "windscreen")
        tr, sr, dlr, Lr, filmr, tempr = load_glass(rd, "rearScreen")
        assert np.array_equal(tw, tr)
        nf = len(s)
        data[run] = (W, tw, s, dl, L, film)
        os.makedirs(os.path.join(dst, run), exist_ok=True)

        # ---------------------------------------------------------------- history.csv
        it = lambda k: np.interp(tw, W["t"], W[k])
        F = lambda k: W[k] if k in W else np.zeros_like(W["t"])
        with np.errstate(divide="ignore", invalid="ignore"):
            iw = np.where(np.abs(F("recirc_kg_s")) > 0, F("recirc_vap_kg_s") / F("recirc_kg_s"), np.nan)
            il = np.where(np.abs(F("recirc_kg_s")) > 0, F("recirc_mist_kg_s") / F("recirc_kg_s"), np.nan)
        W["intake_w"], W["intake_L"] = iw, il
        cols = [
            ("t_s", tw, "%g"),
            ("windscreen_misted_pct", 100 * share(film, dl, L), "%.3f"),
            ("windscreen_film_g_m2", 1e3 * (film * dl).sum(1) / L, "%.5g"),
            ("windscreen_T_C", (temp * dl).sum(1) / L, "%.4f"),
            ("rearScreen_misted_pct", 100 * share(filmr, dlr, Lr), "%.3f"),
            ("rearScreen_film_g_m2", 1e3 * (filmr * dlr).sum(1) / Lr, "%.5g"),
            ("rearScreen_T_C", (tempr * dlr).sum(1) / Lr, "%.4f"),
            ("cabin_air_C", it("cabin_Tmean"), "%.4f"),
            ("air_at_heads_C", it("head_T"), "%.4f"),
            ("supply_C", it("defrost_T"), "%.4f"),
            ("intake_vapour_g_kg", 1e3 * np.interp(tw, W["t"], np.nan_to_num(iw)) if run == "recirc" else np.full(len(tw), np.nan), "%.4f"),
            ("intake_mist_g_kg", 1e3 * np.interp(tw, W["t"], np.nan_to_num(il)) if run == "recirc" else np.full(len(tw), np.nan), "%.4g"),
            ("cabin_vapour_g_per_m", 1e3 * it("cabin_vapour_kg"), "%.5f"),
            ("cabin_mist_g_per_m", 1e3 * it("cabin_mist_kg"), "%.5f"),
            ("sideglass_misted_pct", 100 * it("sideglass_misted"), "%.3f"),
        ]
        with open(os.path.join(dst, run, "history.csv"), "w") as f:
            f.write(",".join(c[0] for c in cols) + "\n")
            for i in range(len(tw)):
                f.write(",".join("" if np.isnan(c[1][i]) else (c[2] % c[1][i]) for c in cols) + "\n")

        # ---------------------------------------------------------------- windscreen_film.csv
        pick = [0] + [int(np.argmin(np.abs(tw - t))) for t in range(30, 601, 30)]
        with open(os.path.join(dst, run, "windscreen_film.csv"), "w") as f:
            f.write("s_from_foot_mm,length_mm," + ",".join(f"film_g_m2_{t}s" for t in range(0, 601, 30)) + "\n")
            for j in range(nf):
                vals = [P.FILM0 * 1e3] + [film[k, j] * 1e3 for k in pick[1:]]
                f.write(f"{s[j] * 1e3:.2f},{dl[j] * 1e3:.3f}," + ",".join(f"{v:.5g}" for v in vals) + "\n")

        # ---------------------------------------------------------------- summary
        at = lambda t: int(np.argmin(np.abs(tw - t)))
        sh = 100 * share(film, dl, L)
        pr("")
        pr(f"{run}: {len(tw)} writes, {tw[0]:g}-{tw[-1]:g} s; walls.dat {len(W['t'])} rows to {W['t'][-1]:.2f} s; "
           f"windscreen {nf} faces over {L:.4f} m, rear screen {len(sr)} faces over {Lr:.4f} m")
        pr("  windscreen still misted, % of its length (face by face at the write):")
        pr("    " + "  ".join(f"{t:>3d} s {sh[at(t)]:6.2f}%" if t else "  0 s 100.00%" for t in (0, 60, 120, 180, 240)))
        pr("    " + "  ".join(f"{t:>3d} s {sh[at(t)]:6.2f}%" for t in (300, 360, 420, 480, 540, 600)))
        pr("    the clip's rounded number: " + ", ".join(f"{m} min {sh[at(60 * m)]:.0f}%" for m in (2, 5, 7, 8, 9, 10)))
        wm = W["windscreen_misted"]
        start = W["t"][np.argmax(wm < 1)]
        pr(f"  every 20 steps (walls.dat): first face clears at {start:.2f} s")
        if (wm[-1] == 0):
            last = np.nonzero(wm > 0)[0][-1]
            pr(f"  windscreen clear from {W['t'][last + 1]:.2f} s (last misted at {W['t'][last]:.2f} s); "
               f"misted share {100 * wm[np.searchsorted(W['t'], 420)]:.2f}% at 420 s")
            mlate = wm[W["t"] >= 420]
            pr(f"    420 s to clearing: misted share {100 * mlate.min():.2f}-{100 * mlate.max():.2f}% "
               f"(the top face{'s' if mlate.max() * L > 0.01 else ''}, {mlate.max() * L * 1e3:.1f} mm)")
        else:
            pr(f"  still misted at {W['t'][-1]:.2f} s: {100 * wm[-1]:.2f}%")
        for a, b in ((480, 600), (540, 600)):
            pr(f"  windscreen clearing {a}-{b} s: {(sh[at(a)] - sh[at(b)]) / ((b - a) / 60):.2f} points a minute")
        # the film's shape along the glass (for the drawing)
        r = film / P.FILM0
        mk = film > P.FILM_CLEAR
        pr("  share of the windscreen's length by film, % (of the starting 10 g/m2):")
        pr("       t s   >=90%  50-90%  10-50%  <10% misted   clear   taper 90%->clear mm   drawn >50% fog  >5% fog")
        for t in (60, 120, 180, 240, 300, 360, 480, 600):
            k = at(t)
            bands = [r[k] >= 0.9, (r[k] < 0.9) & (r[k] >= 0.5), (r[k] < 0.5) & (r[k] >= 0.1), (r[k] < 0.1) & mk[k], ~mk[k]]
            v = [100 * (b * dl).sum() / L for b in bands]
            taper = 1e3 * (((r[k] < 0.9) & mk[k]) * dl).sum()
            op = OPACITY(film[k])
            pr(f"    {t:6d}  " + "  ".join(f"{x:6.1f}" for x in v) + f"   {taper:10.0f}            "
               f"{100 * ((op > 0.5) * dl).sum() / L:6.1f}      {100 * ((op > 0.05) * dl).sum() / L:6.1f}")
        first_below = lambda m: np.where(m.any(0), tw[np.argmax(m, 0)], np.nan)
        clear_t = first_below(~mk)
        ok = ~np.isnan(clear_t)
        if ok.any():
            half = clear_t - first_below(r < 0.5)
            tenth = clear_t - first_below(r < 0.1)
            pr(f"  faces cleared by {tw[-1]:g} s: {ok.sum()} of {nf}; per face, from half the starting film to clear: "
               f"median {np.nanmedian(half[ok]):.1f} s; from a tenth to clear: median {np.nanmedian(tenth[ok]):.2f} s, "
               f"90th percentile {np.nanpercentile(tenth[ok], 90):.2f} s, largest {np.nanmax(tenth[ok]):.2f} s "
               f"(write interval {DT_WRITE:g} s)")
        k = at(600)
        pr(f"  film at {tw[k]:g} s: largest {film[k].max() * 1e3:.2f} g/m2; largest at any write {film.max() * 1e3:.2f} g/m2")
        shr = 100 * share(filmr, dlr, Lr)
        pr("  rear screen still misted: " + ", ".join(f"{t} s {shr[at(t)]:.1f}%" for t in (120, 300, 420, 480, 540, 600)))
        pr(f"  side glass still misted (walls.dat): " + ", ".join(
            f"{t} s {100 * np.interp(t, W['t'], W['sideglass_misted']):.1f}%" for t in (120, 300, 600)))

        # warm-up against the reference cabin model (scripts/warmup_reference.py)
        R = ref[run]
        pr("  warm-up against the scaled Brusey et al. cabin model (reference every 10 s):")
        pr("       t s   ref cabin   heads   cabin mean   ref supply   supply")
        for t in (10, 20, 30, 60, 90, 120, 300, 600):
            j = int(np.argmin(np.abs(R[:, 0] - t)))
            pr(f"    {t:6d}   {R[j, 1]:8.2f}  {np.interp(t, W['t'], W['head_T']):6.2f}   {np.interp(t, W['t'], W['cabin_Tmean']):9.2f}"
               f"   {R[j, 3]:9.2f}   {np.interp(t, W['t'], W['defrost_T']):6.2f}")
        dh = np.interp(R[1:13, 0], W["t"], W["head_T"]) - R[1:13, 1]
        dsup = np.interp(R[1:13, 0], W["t"], W["defrost_T"]) - R[1:13, 3]
        pr(f"    10-120 s, heads less reference cabin: {dh.min():+.2f} (at {R[1 + np.argmin(dh), 0]:g} s) to "
           f"{dh.max():+.2f} K (at {R[1 + np.argmax(dh), 0]:g} s); "
           f"supply less reference supply: {dsup.min():+.2f} to {dsup.max():+.2f} K")
        j4 = int(np.argmin(np.abs(R[:, 0] - 40)))
        pr(f"    supply less reference at 40 s {np.interp(40, W['t'], W['defrost_T']) - R[j4, 3]:+.2f} K, "
           f"at 60 s {dsup[5]:+.2f} K, at 120 s {dsup[11]:+.2f} K; "
           f"cabin mean less reference at 60 s {np.interp(60, W['t'], W['cabin_Tmean']) - R[6, 1]:+.2f} K, "
           f"at 120 s {np.interp(120, W['t'], W['cabin_Tmean']) - R[12, 1]:+.2f} K")

        # water: the budget, the intake, the mist
        store = (W["cabin_vapour_kg"] + W["windscreen_film_kg"] + W["rearScreen_film_kg"]
                 + W["sideglass_film_kg"] + W["cabin_mist_kg"])
        net = -(W["defrost_vap_kg_s"] + F("recirc_vap_kg_s") + W["vent_vap_kg_s"]
                + F("recirc_mist_kg_s") + W["vent_mist_kg_s"]) + 2 * S_EACH
        pr("  water budget, per metre: change in vapour + mist + films against in - out + occupants:")
        worst = 0.0
        for a, b in ((0, 1), (1, 2), (2, 5), (5, 10), (10, 30), (30, 60), (60, 120), (120, 240),
                     (240, 360), (360, 480), (480, 540), (540, 600)):
            sel = (W["t"] >= a) & (W["t"] <= b)
            tt, ss, nn = W["t"][sel], store[sel], net[sel]
            dS = (ss[-1] - ss[0]) / (tt[-1] - tt[0])
            fl = np.trapezoid(nn, tt) / (tt[-1] - tt[0])
            res = (dS - fl) / max(abs(fl), abs(dS))
            if a >= 2:
                worst = max(worst, abs(res))
            pr(f"    {a:4d}-{b:4d} s  d(store)/dt {dS:+.4e}  in-out+S {fl:+.4e} kg/s  residual {res:+.2%}")
        pr(f"    largest residual from 2 s on: {worst:.2%}")
        if run == "recirc":
            pr(f"  intake: mist drawn in, largest at any logged step {np.nanmax(np.abs(F('recirc_mist_kg_s'))):.3g} kg/s; "
               "vapour " + ", ".join(f"{t} s {1e3 * np.interp(t, W['t'], np.nan_to_num(iw)):.2f} g/kg" for t in (30, 60, 120, 300, 600)))
            pr(f"    intake air at 120 s {np.interp(120, W['t'], W['recirc_T']):.2f} C against the cabin's mean "
               f"{np.interp(120, W['t'], W['cabin_Tmean']):.2f} C")
        pr("  cabin vapour and mist, g per metre: " + "; ".join(
            f"{t} s {1e3 * np.interp(t, W['t'], W['cabin_vapour_kg']):.2f} and {1e3 * np.interp(t, W['t'], W['cabin_mist_kg']):.3f}"
            for t in (0, 120, 300, 600)))
        pr(f"  supply temperature: {W['defrost_T'][W['t'] > 1][0]:.2f} C at {W['t'][W['t'] > 1][0]:.2f} s, "
           + ", ".join(f"{np.interp(t, W['t'], W['defrost_T']):.2f} C at {t} s" for t in (60, 120, 600)))
        pr(f"  air at the heads: " + ", ".join(f"{np.interp(t, W['t'], W['head_T']):.2f} C at {t} s" for t in (60, 120, 300, 600))
           + f"; cabin mean " + ", ".join(f"{np.interp(t, W['t'], W['cabin_Tmean']):.2f} C at {t} s" for t in (120, 600)))
        pr(f"  time step: {len(W['t']) * 20} steps to {W['t'][-1]:.0f} s, mean {W['t'][-1] / (len(W['t']) * 20) * 1e3:.2f} ms")

    # both runs at two minutes
    Wo, Wr = data["outside"][0], data["recirc"][0]
    pr("")
    pr("at 120 s: recirc's supply {:.2f} C against outside air's {:.2f} C ({:+.2f} K); air at the heads recirc {:.2f}, outside {:.2f} C; "
       "cabin mean recirc {:.2f}, outside {:.2f} C".format(
           np.interp(120, Wr["t"], Wr["defrost_T"]), np.interp(120, Wo["t"], Wo["defrost_T"]),
           np.interp(120, Wr["t"], Wr["defrost_T"]) - np.interp(120, Wo["t"], Wo["defrost_T"]),
           np.interp(120, Wr["t"], Wr["head_T"]), np.interp(120, Wo["t"], Wo["head_T"]),
           np.interp(120, Wr["t"], Wr["cabin_Tmean"]), np.interp(120, Wo["t"], Wo["cabin_Tmean"])))
    Rr, Ro = ref["recirc"], ref["outside"]
    pr("  the reference model's recirculated supply less its outside-air supply at 120 s: {:+.2f} K".format(Rr[12, 3] - Ro[12, 3]))
    with open(os.path.join(dst, "summary.txt"), "w") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
