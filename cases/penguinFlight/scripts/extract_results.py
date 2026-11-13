"""Write results/ from the solved runs' force records.

    python3 scripts/extract_results.py <runsDir> <resultsDir>

Reads <runsDir>/<run>/postProcessing/<forces|bodyForces|flipperForces>/<startTime>/force*.dat for
whichever of lift50, lift64, swim and fly are there. A run that was restarted has one folder
per start; each folder's rows are kept up to the next folder's start time, so the record is
the trajectory the solver ended on. (OpenFOAM names a second file in the same folder
force_0.dat; both are read.)

lift50, lift64  the 3-D half model: forces doubled for the whole bird, lift = Fz, drag = Fx (air
                along +x, z up). Whole bird, body and flippers; the mean over the last 300
                iterations, its peak-to-peak range and the drift between its two halves. The
                flying speed is V50 sqrt(weight / L50).
fly             the 2-D section, per metre (force / 0.01 m): lift = Fz, drag = Fx; time-weighted
                mean and standard deviation over 0.1-0.5 s, and the spectrum of lift and drag
                (resampled every 0.1 ms over 0.1-0.5 s, mean removed, Hann window, no detrend),
                its peak and the Strouhal number on the bird's depth, 0.145 m.
swim            the 2-D section in its falling frame, per metre. The solver's pressure carries
                the frame's potential, so rho g A (A the section's area) is taken off Fz, and
                lift and drag are taken across and along the relative wind (2, 9.81 t) m/s, as
                the study's forces_physical.csv did.

Writes results/summary.txt, results/lift_history.csv (every 10th iteration and the last),
results/<fly|swim>_forces.csv (1 ms window means) and results/fly_spectrum.csv.
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CASE = HERE.parent
CFG = json.loads((CASE / "config/caseSettings.json").read_text())
RHO = CFG["air"]["rho_kg_m3"]
SPAN = CFG["section"]["span_m"]
DEPTH = CFG["bird"]["depth_m"]
W = CFG["bird"]["weight_N"]
NWIN = CFG["liftWindow_iterations"]
T0, T1 = CFG["flyForceWindow_s"]
DIMS = json.loads((CASE / "geometry/penguin_dims.json").read_text())
SREF = DIMS["planform_area_whole_bird_m2"]
SFLIP = 2 * DIMS["flipper_area_each_m2"]


def force_record(run, fo="forces"):
    """time, Fx, Fy, Fz (total) from every start folder, later starts overriding earlier rows."""
    base = run / "postProcessing" / fo
    if not base.is_dir():
        return None
    dirs = sorted((float(d.name), d) for d in base.iterdir() if d.is_dir())
    parts = []
    for i, (t0, d) in enumerate(dirs):
        rows = [np.loadtxt(f, comments="#", ndmin=2)[:, :4] for f in sorted(d.glob("force*.dat"))]
        rows = [r for r in rows if len(r)]
        if not rows:
            continue
        a = np.vstack(rows)
        a = a[np.argsort(a[:, 0], kind="stable")]
        if i + 1 < len(dirs):
            a = a[a[:, 0] <= dirs[i + 1][0] + 1e-15]
        parts.append(a)
    a = np.vstack(parts)
    a = a[np.argsort(a[:, 0], kind="stable")]
    keep = np.r_[np.diff(a[:, 0]) > 0, True]       # one row per time, the last written
    return a[keep]


# ---------------------------------------------------------------------------------------------

def window(x):
    w = x[-NWIN:]
    m = w.mean()
    return dict(mean=m, p2p=100 * (w.max() - w.min()) / abs(m),
                drift=100 * (w[NWIN // 2:].mean() - w[:NWIN // 2].mean()) / abs(m))


def lift_runs(runs, out, rows):
    res = {}
    for name in ("lift50", "lift64"):
        r = runs / name
        if not (r / "postProcessing/forces").is_dir():
            continue
        d = {}
        for fo in ("forces", "bodyForces", "flipperForces"):
            a = force_record(r, fo)
            d[fo] = dict(it=a[:, 0], drag=2 * a[:, 1], lift=2 * a[:, 3])
        res[name] = d
    if not res:
        return res
    with open(out / "lift_history.csv", "w") as f:
        f.write("run,iteration,lift_N,drag_N,body_lift_N,flipper_lift_N,body_drag_N,flipper_drag_N\n")
        for name, d in res.items():
            it = d["forces"]["it"]
            idx = sorted(set(np.where(it % 10 == 0)[0]) | {len(it) - 1})
            for i in idx:
                f.write(f"{name},{it[i]:.0f},{d['forces']['lift'][i]:.4f},{d['forces']['drag'][i]:.4f},"
                        f"{d['bodyForces']['lift'][i]:.4f},{d['flipperForces']['lift'][i]:.4f},"
                        f"{d['bodyForces']['drag'][i]:.4f},{d['flipperForces']['drag'][i]:.4f}\n")
    rows.append("The 3-D half model, whole bird (forces doubled), lift Fz and drag Fx in N; the last "
                f"{NWIN} iterations")
    rows.append(f"  {'run':7s} {'iters':>6s} {'lift':>9s} {'drag':>9s} {'body L':>9s} {'flipper L':>9s} "
                f"{'flipper share':>13s} {'L p-p':>7s} {'L drift':>7s} {'L/weight':>8s}")
    for name, d in res.items():
        L, D = window(d["forces"]["lift"]), window(d["forces"]["drag"])
        Lb, Lf = window(d["bodyForces"]["lift"]), window(d["flipperForces"]["lift"])
        d["window"] = dict(L=L["mean"], D=D["mean"], Lb=Lb["mean"], Lf=Lf["mean"])
        rows.append(f"  {name:7s} {d['forces']['it'][-1]:6.0f} {L['mean']:9.4f} {D['mean']:9.4f} {Lb['mean']:9.4f} "
                    f"{Lf['mean']:9.4f} {100 * Lf['mean'] / (Lb['mean'] + Lf['mean']):12.2f}% {L['p2p']:6.2f}% "
                    f"{L['drift']:6.2f}% {100 * (L['mean'] / W - 1):+7.2f}%")
    if "lift50" in res:
        V50 = CFG["runs"]["lift50"]["speed_m_s"]
        V = V50 * np.sqrt(W / res["lift50"]["window"]["L"])
        rows.append(f"  flying speed from lift50: {V50:g} sqrt({W:g} / {res['lift50']['window']['L']:.4f}) = "
                    f"{V:.4f} m/s ({3.6 * V:.1f} km/h); run at {CFG['runs']['lift64']['speed_m_s']:g} m/s")
    for name, d in res.items():
        V = CFG["runs"][name]["speed_m_s"]
        q = 0.5 * RHO * V ** 2
        rows.append(f"  {name}: lift coefficient on the whole bird's planform, {SREF:.4f} m2: {d['window']['L'] / (q * SREF):.4f}; "
                    f"the flippers' lift on their own {SFLIP:.4f} m2: {d['window']['Lf'] / (q * SFLIP):.4f}")
    rows.append("")
    return res


def section_area():
    """The 2-D bird's area, from the profile as the mesh takes it (every second point, closed)."""
    q = np.loadtxt(CASE / CFG["bird"]["profile"], delimiter=",", skiprows=1)
    if np.linalg.norm(q[-1] - q[0]) < 1e-8:
        q = q[:-1]
    q = q[::2]
    x, z = q[:, 0], q[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(z, -1)) - np.dot(z, np.roll(x, -1)))


def per_ms(t, cols, tend):
    """Time-weighted means over each 1 ms, the force held over each step (it is the step's)."""
    edges = np.arange(0, tend + 5e-7, 1e-3)
    dt = np.diff(np.r_[0.0, t])
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        lo = np.r_[0.0, t[:-1]]
        ov = np.clip(np.minimum(t, b) - np.maximum(lo, a), 0, None)
        out.append([a, b] + [float(np.sum(c * ov) / max(ov.sum(), 1e-30)) for c in cols])
    return out


def tw_stats(t, x, t0, t1):
    tt = np.linspace(t0, t1, 400001)
    y = np.interp(tt, t, x)
    m = np.trapezoid(y, tt) / (t1 - t0)
    s = np.sqrt(np.trapezoid((y - m) ** 2, tt) / (t1 - t0))
    return m, s


def spectrum(t, x, t0, t1, dt=1e-4):
    n = int(round((t1 - t0) / dt))
    tt = t0 + dt * np.arange(n)
    y = np.interp(tt, t, x)
    y = (y - y.mean()) * np.hanning(n)
    a = np.abs(np.fft.rfft(y)) * 2 / np.hanning(n).sum()
    return np.fft.rfftfreq(n, dt), a


def two_d(runs, out, rows):
    res = {}
    for name in ("fly", "swim"):
        r = runs / name
        a = force_record(r) if r.is_dir() else None
        if a is None:
            continue
        a = a[a[:, 0] > 0]
        t, Fx, Fz = a[:, 0], a[:, 1] / SPAN, a[:, 3] / SPAN
        if name == "swim":
            A = section_area()
            Fz = Fz - RHO * 9.81 * A
            sx, sz = 2.0, 9.81 * t
            n = np.hypot(sx, sz)
            drag, lift = (Fx * sx + Fz * sz) / n, (-Fx * sz + Fz * sx) / n
            rows.append(f"swim: rho g A = {RHO * 9.81 * A:.4f} N/m taken off Fz (A = {A:.6f} m2, the profile's "
                        "polygon as meshed); lift and drag across and along the relative wind (2, 9.81 t) m/s")
            te = CFG["runs"]["swim"]["endTime_s"]
            g = CFG["runs"]["swim"]["fall_g_m_s2"]
            rows.append(f"swim: the prescribed fall at {te:g} s is 0.5 g t^2 = {0.5 * g * te ** 2:.4f} m; the relative wind "
                        f"then comes from {np.degrees(np.arctan2(g * te, 2.0)):.1f} deg below horizontal")
        else:
            drag, lift = Fx, Fz
        tend = CFG["runs"][name]["endTime_s"]
        with open(out / f"{name}_forces.csv", "w") as f:
            f.write("t_from_s,t_to_s,Fx_N_per_m,Fz_N_per_m,drag_N_per_m,lift_N_per_m\n")
            for w in per_ms(t, [Fx, Fz, drag, lift], tend):
                f.write(f"{w[0]:.3f},{w[1]:.3f}," + ",".join(f"{v:.4f}" for v in w[2:]) + "\n")
        res[name] = (t, drag, lift)
        rows.append(f"{name}: {len(t)} steps to t = {t[-1]:.9f} s; 1 ms window means in results/{name}_forces.csv")
    if "fly" in res:
        t, D, L = res["fly"]
        V = CFG["runs"]["fly"]["speed_m_s"]
        mL, sL = tw_stats(t, L, T0, T1)
        mD, sD = tw_stats(t, D, T0, T1)
        f, aL = spectrum(t, L, T0, T1)
        _, aD = spectrum(t, D, T0, T1)
        pL, pD = f[1:][np.argmax(aL[1:])], f[1:][np.argmax(aD[1:])]
        with open(out / "fly_spectrum.csv", "w") as fh:
            fh.write("frequency_Hz,lift_amplitude_N_per_m,drag_amplitude_N_per_m\n")
            for i in range(len(f)):
                if f[i] <= 1000:
                    fh.write(f"{f[i]:.1f},{aL[i]:.4f},{aD[i]:.4f}\n")
        rows.append(f"fly, {T0:g}-{T1:g} s, time-weighted, per metre of section:")
        rows.append(f"  lift {mL:.3f} N/m, standard deviation {sL:.3f} ({100 * sL / abs(mL):.2f}% of the mean)")
        rows.append(f"  drag {mD:.3f} N/m, standard deviation {sD:.3f} ({100 * sD / abs(mD):.2f}% of the mean)")
        rows.append(f"  spectrum (0.1 ms resampling, Hann, {f[1]:.1f} Hz bins): lift peaks at {pL:.1f} Hz, drag at {pD:.1f} Hz;"
                    f" Strouhal number on the {DEPTH:g} m depth at {V:g} m/s: {pL * DEPTH / V:.4f}")
        rows.append("  (the section's lift per metre is not the bird's lift and is not used for the flying speed)")
    rows.append("")
    return res


def main():
    runs, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    rows = ["penguinFlight: figures from the runs' force records (scripts/extract_results.py)",
            f"Adelie penguin, {CFG['bird']['mass_kg']:g} kg ({W:g} N), pitched {CFG['bird']['pitch_deg']:g} deg nose-up; "
            f"air {RHO:g} kg/m3, nu {CFG['air']['nu_m2_s']:g} m2/s", ""]
    lift_runs(runs, out, rows)
    two_d(runs, out, rows)
    (out / "summary.txt").write_text("\n".join(rows))
    print("\n".join(rows))


if __name__ == "__main__":
    main()
