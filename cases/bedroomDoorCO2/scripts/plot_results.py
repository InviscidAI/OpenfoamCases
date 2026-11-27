#!/usr/bin/env python3
"""results/co2.png: the CO2 at the heads through the night in both runs, and the section's CO2 at
8 h in each.

    python3 scripts/plot_results.py RUNS RESULTS

Reads RESULTS/<run>/history.csv (scripts/extract_results.py) and the air cells' CO2 on the section
at 28,800 s, RUNS/<run>/postProcessing/planes_window6/28800/sectionCells.vtp (or .vtp.gz), as the
runs' function object planes_window6 writes it. Needs VTK's Python module and matplotlib.
"""
from pathlib import Path
import gzip, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Rectangle
from vtkmodules.vtkIOXML import vtkXMLPolyDataReader
from vtkmodules.util.numpy_support import vtk_to_numpy


def section(runs, run, t='28800'):
    d = Path(runs) / run / 'postProcessing/planes_window6' / t
    p = d / 'sectionCells.vtp'
    reader = vtkXMLPolyDataReader()
    if p.exists():
        reader.SetFileName(str(p))
    else:
        reader.ReadFromInputStringOn(); reader.SetInputString(gzip.open(str(p) + '.gz', 'rb').read().decode('utf-8'))
    reader.Update(); m = reader.GetOutput()
    pts = vtk_to_numpy(m.GetPoints().GetData())[:, :2]
    conn = vtk_to_numpy(m.GetPolys().GetConnectivityArray()); off = vtk_to_numpy(m.GetPolys().GetOffsetsArray())
    polys = [pts[conn[a:b]] for a, b in zip(off[:-1], off[1:])]
    return polys, vtk_to_numpy(m.GetCellData().GetArray('CO2'))


def main(runs, results):
    res = Path(results)
    fig = plt.figure(figsize=(12, 8.4))
    ax = fig.add_axes([.07, .53, .82, .41])
    for run, colour in [('shut', '#b5452a'), ('ajar', '#2a6fb5')]:
        h = pd.read_csv(res / run / 'history.csv')
        t = np.r_[0, h.time_s / 3600]; c = np.r_[500, h.heads_CO2_ppm]
        ax.plot(t, c, color=colour, lw=2, label=f'door {run}' + (' 10 cm (4 in)' if run == 'ajar' else ''))
        ax.annotate(f'{c[-1]:,.0f} ppm', (8, c[-1]), xytext=(6, 0), textcoords='offset points', va='center', color=colour)
    ax.axvline(2, color='0.6', lw=.8, ls='--')
    ax.text(2.05, 520, 'joint at 7,200 s: the original runs before, the repair runs after', color='0.4', fontsize=8.5)
    ax.set(xlim=(0, 8), ylim=(400, 4400), xlabel='hours after lights-out (11 pm)', ylabel='CO$_2$ at the heads, ppm')
    ax.set_xticks(range(9)); ax.grid(alpha=.3); ax.legend(loc='upper left', frameon=False)
    ax.set_title('Two sleepers, window shut, 0 C outside: CO$_2$ 10-40 cm above their faces', loc='left', fontsize=11)
    for k, run in enumerate(['shut', 'ajar']):
        a = fig.add_axes([.04 + .49 * k, .15, .45, .32])
        polys, co2 = section(runs, run)
        pc = PolyCollection(polys, array=co2, cmap='magma_r', clim=(500, 4500), edgecolors='none'); a.add_collection(pc)
        a.add_patch(Rectangle((.98, 0), 1.54, .55, color='0.75'))
        a.plot([0, 0], [.9, 2.2], color='#5fa8d3', lw=4)
        a.add_patch(Rectangle((3.5, 2.03), .1, .41, color='0.45'))
        if run == 'shut':
            a.add_patch(Rectangle((3.5, .02), .1, 1.99, color='#7a5230'))
        a.set(xlim=(-.05, 4.85), ylim=(-.03, 2.47), aspect='equal')
        a.set_xticks([0, 1, 2, 3, 3.5, 4.8]); a.set_yticks([0, 1, 2, 2.44]); a.tick_params(labelsize=8)
        a.text(.1, 2.3, f'door {run}, 8 h', fontsize=10, va='top')
        a.text(4.2, 2.3, 'hall', fontsize=9, va='top', ha='center')
        a.set_xlabel('x, m: the window wall at 0, the door at 3.5-3.6, the house beyond 4.8', fontsize=8.5)
    cb = fig.add_axes([.3, .065, .4, .018]); fig.colorbar(pc, cax=cb, orientation='horizontal', label='CO$_2$ on the section at 8 h, ppm')
    fig.savefig(res / 'co2.png', dpi=110)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('usage: plot_results.py RUNS RESULTS')
    main(*sys.argv[1:])
