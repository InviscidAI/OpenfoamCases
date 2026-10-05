#!/usr/bin/env python3
"""Draw results/histories.png from results/hour/*_history.csv.

    python3 plot_histories.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent
COLOR = {"window": "#eb6834", "opposite": "#2a78d6"}
LABEL = {"window": "radiator under the window", "opposite": "radiator on the opposite wall"}


def load(run):
    return np.genfromtxt(HERE / "results/hour" / f"{run}_history.csv", delimiter=",", names=True)


def main():
    d = {run: load(run) for run in COLOR}
    fig, axs = plt.subplots(3, 1, figsize=(8, 9), sharex=True)
    for run, h in d.items():
        t, c = h["time_s"] / 60, COLOR[run]
        axs[0].plot(t, h["head_height_C"], c, lw=1.2, ls="--", label=f"{LABEL[run]}: head height, 1.0-1.2 m")
        axs[0].plot(t, h["floor_layer_C"], c, lw=1.5, label=f"{LABEL[run]}: floor layer, below 0.1 m")
        axs[1].plot(t, h["sill_down"] * 1000, c, lw=1.2, label=f"{LABEL[run]}: down")
        axs[1].plot(t, h["sill_up"] * 1000, c, lw=1.2, ls="--", label=f"{LABEL[run]}: up")
        axs[2].plot(t, h["floor_away"] * 1000, c, lw=1.2, label=f"{LABEL[run]}: away from the window")
        axs[2].plot(t, h["floor_toward"] * 1000, c, lw=1.2, ls="--", label=f"{LABEL[run]}: toward it")
    axs[0].set_ylabel("air temperature, C\n(x 0.3-2.0 m from the glass)")
    axs[1].set_ylabel("flow past the sill, L/s per m\n(y = 0.90 m, x < 0.30 m)")
    axs[2].set_ylabel("flow across the floor line,\nL/s per m (x = 1.0 m, y < 0.30 m)")
    axs[2].set_xlabel("minutes from switch-on")
    axs[2].set_xlim(0, 60)
    for ax in axs:
        ax.grid(color="#dddddd", lw=0.6)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(fontsize=7, frameon=False, loc="best")
    fig.suptitle("A radiator under a cold window or opposite it: the hour from switch-on", fontsize=11)
    fig.tight_layout()
    fig.savefig(HERE / "results/histories.png", dpi=100)


if __name__ == "__main__":
    main()
