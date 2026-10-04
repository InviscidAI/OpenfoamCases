"""This case against ceilingFanWinter: the same times, the same heights, the same method.

Sets a run of this case (a 6.10 m ceiling) beside ceilingFanWinter's run of the same
direction (a 3.05 m ceiling) from the r-z faces each wrote, using ceilingFanWinter's own
measure (its postprocess.py): the r-weighted mean of T along a horizontal line from the
axis to R - 4 mm, sampled at 700 intervals, and the r-weighted fraction of that line where
|U| >= 0.15 m/s.

Heights are ceilingFanWinter's: 0.10, 1.09 and 1.70 m, and 2.75 m, 12 in below its
ceiling. For this case it adds the fan's mid-height (2.67 m) and 12 in below the 6.10 m
ceiling (5.7952 m). Every 4th write is read, which includes t = 30, 60, ... 180 s. Both
sides are checked against their own results/history.csv. In the output "07" is
ceilingFanWinter and "10" is this case (the numbers of the clips they back).

    python3 compare_07.py runs/heater2600W out --runs up_medium
    python3 compare_07.py runs/heater1300W out --runs down_medium up_medium

--ref defaults to ../ceilingFanWinter/runs, where that case's ./Allrun writes.
"""
import argparse
import gzip
import json
import os
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyvista as pv

REF = str(Path(__file__).resolve().parent.parent / "ceilingFanWinter" / "runs")
R = 3.441282078
H07 = {"010": 0.10, "109": 1.09, "170": 1.70, "275": 2.75}
H10 = {**H07, "267": 2.67, "580": 5.7952}
RUNS = {"down_medium": "blowing down", "up_medium": "reversed, blowing up"}
TABLE_T = [30, 60, 90, 120, 150, 180]


def read(path):
    with gzip.open(path) as f, tempfile.NamedTemporaryFile(suffix=".vtp", delete=False) as t:
        t.write(f.read())
        name = t.name
    try:
        return pv.read(name)
    finally:
        os.unlink(name)


def measure(m, heights):
    row = {}
    for lbl, h in heights.items():
        s = pv.Line((0, 0, h), (R - 0.004, 0, h), resolution=700).sample(m)
        ok = np.asarray(s["vtkValidPointMask"]).astype(bool)
        r = s.points[:, 0][ok]
        o = np.argsort(r)
        r, T, U = r[o], np.asarray(s["T"])[ok][o], np.asarray(s["U"])[ok][o]
        den = np.trapezoid(r, r)
        row[f"T{lbl}_C"] = np.trapezoid(T * r, r) / den - 273.15
        if h < 2:
            row[f"draft{lbl}"] = np.trapezoid((np.linalg.norm(U, axis=1) >= 0.15) * r, r) / den
    return row


def history(run_dir, heights, every):
    dirs = sorted((Path(run_dir) / "postProcessing/rzFace").glob("*"), key=lambda d: float(d.name))
    times = np.array([float(d.name) for d in dirs])
    rows = []
    for i in range(0, len(dirs), every):
        rows.append({"t": times[i], **measure(read(dirs[i] / "rz.vtp.gz"), heights)})
    return pd.DataFrame(rows), len(dirs), times


def check_against(df, csv):
    """Largest difference between our values and a history.csv's at the same times (K, or fraction)."""
    if not Path(csv).exists():
        return None
    h = pd.read_csv(csv).set_index("time_s")
    out = {}
    for c in df.columns:
        if c == "t":
            continue
        hc = c.replace("_C", "_K")
        if hc not in h.columns:
            continue
        ref = h[hc].reindex(df["t"].round(6), method="nearest", tolerance=1e-3).to_numpy()
        ours = df[c].to_numpy() + (273.15 if c.endswith("_C") else 0)
        out[c] = float(np.nanmax(np.abs(ours - ref)))
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("new")
    p.add_argument("out")
    p.add_argument("--ref", default=REF)
    p.add_argument("--every", type=int, default=4)
    p.add_argument("--runs", nargs="+", choices=list(RUNS), default=list(RUNS),
                   help="runs to compare (the 2600 W heater was run only up_medium)")
    p.add_argument("--ref-label", default="07, 3.05 m ceiling",
                   help="legend for --ref; the tables' '07' column is whatever --ref holds")
    a = p.parse_args()
    runs = {r: RUNS[r] for r in a.runs}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    report = {"method": "07's postprocess.py: r-weighted line means, axis to R - 4 mm, 700 intervals",
              "runs": {}}
    hist = {}
    for run, label in runs.items():
        d07, n07, t07 = history(Path(a.ref) / run, H07, a.every)
        d10, n10, t10 = history(Path(a.new) / run, H10, a.every)
        hist[run] = (d07, d10)
        d07.to_csv(out / f"compare_07_{run}_07.csv", index=False)
        d10.to_csv(out / f"compare_07_{run}_10.csv", index=False)
        table = []
        for t in TABLE_T:
            r07 = d07.iloc[np.argmin(abs(d07["t"] - t))]
            r10 = d10.iloc[np.argmin(abs(d10["t"] - t))]
            row = {"t": t}
            for lbl in H07:
                row[f"T{lbl} 07"] = float(r07[f"T{lbl}_C"])
                row[f"T{lbl} 10"] = float(r10[f"T{lbl}_C"])
                row[f"T{lbl} 10-07"] = row[f"T{lbl} 10"] - row[f"T{lbl} 07"]
                if f"draft{lbl}" in r07:
                    row[f"draft{lbl} 07"] = float(r07[f"draft{lbl}"])
                    row[f"draft{lbl} 10"] = float(r10[f"draft{lbl}"])
            row["T267 10"] = float(r10["T267_C"])
            row["T580 10"] = float(r10["T580_C"])
            table.append(row)
        report["runs"][run] = {
            "writes_07": n07, "writes_10": n10,
            "window_07": [float(t07[0]), float(t07[-1])], "window_10": [float(t10[0]), float(t10[-1])],
            "write_interval_10": sorted({round(float(x), 6) for x in np.diff(t10)}),
            "check_07_against_its_history_csv": check_against(d07, Path(a.ref) / run / "results/history.csv"),
            "check_10_against_its_history_csv": check_against(d10, Path(a.new) / run / "results/history.csv"),
            "table": table,
        }

    # One row per height, down and up side by side; 07 solid, 10 dashed.
    fig, ax = plt.subplots(4, len(runs), figsize=(6 * len(runs), 13), sharex=True, squeeze=False)
    for j, (run, label) in enumerate(runs.items()):
        d07, d10 = hist[run]
        for i, (lbl, h) in enumerate(H07.items()):
            x = ax[i, j]
            x.plot(d07["t"], d07[f"T{lbl}_C"], "-", color="C0", label=a.ref_label)
            x.plot(d10["t"], d10[f"T{lbl}_C"], "--", color="C3", label="10, 6.10 m ceiling")
            if lbl == "275":
                x.plot(d10["t"], d10["T580_C"], ":", color="C3", label="10, 12 in below its ceiling")
            x.set(title=f"{label}, z = {h:.2f} m", ylabel="T (°C)")
            x.grid(alpha=0.3)
            x.legend(fontsize=7)
    for x in ax[-1]:
        x.set_xlabel("t from switch-on (s)")
    fig.tight_layout()
    fig.savefig(out / "compare_07.png", dpi=110)

    lines = ["# This case (\"10\") against ceilingFanWinter (\"07\") at the same times and heights", "",
             "Horizontal r-weighted means in °C; draft is the r-weighted fraction of the line at "
             "|U| >= 0.15 m/s. Computed from both cases' r-z faces with ceilingFanWinter's own method.", ""]
    for run, label in runs.items():
        lines += [f"## {label}", "",
                  "| t (s) | 0.10 m 07 / 10 | 1.09 m 07 / 10 | 1.70 m 07 / 10 | 2.75 m 07 / 10 "
                  "| 10 at 2.67 m | 10 at 5.80 m | draft 1.09 m 07 / 10 |",
                  "|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for r in report["runs"][run]["table"]:
            cells = [f"{r[f'T{l} 07']:.2f} / {r[f'T{l} 10']:.2f}" for l in H07]
            lines.append(f"| {r['t']} | " + " | ".join(cells)
                         + f" | {r['T267 10']:.2f} | {r['T580 10']:.2f} "
                         f"| {100 * r['draft109 07']:.0f}% / {100 * r['draft109 10']:.0f}% |")
        lines.append("")
    (out / "compare_07.md").write_text("\n".join(lines))
    (out / "compare_07.json").write_text(json.dumps(report, indent=1, default=float))
    print("\n".join(lines))
    print(json.dumps({r: {k: v for k, v in report["runs"][r].items() if k != "table"}
                      for r in runs}, indent=1, default=float))


if __name__ == "__main__":
    main()
