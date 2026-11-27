#!/usr/bin/env python3
"""The clip's cut, sectionClear, of both houses at a few times, coloured by air temperature.

    python3 scripts/plot_planes.py RUNS OUT.png [t1 t2 ...]

RUNS holds open/ and insert/ with postProcessing/planes/<t>/sectionClear.vtp (or .vtp.gz). The
cut is vertical, through (0, y, 2.75) with normal (0.33872, 0, 0.94089): from the fireplace
opening diagonally across the living room, clear of the sofa, under the hall doorway's lintel and
across the hall to the front wall. It is drawn against s, the distance along it from x = 0, and
y, the height; the colour is the cut's own point values, 44-84 F as in the clip. Needs pyvista and
matplotlib.
"""
from pathlib import Path
import gzip, sys, tempfile
import numpy as np
import pyvista as pv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.tri as mtri

T_ALONG = np.array([0.94089, 0, -0.33872])   # the cut's horizontal direction, x and z


def read(path):
    if path.suffix == '.gz':
        with tempfile.NamedTemporaryFile(suffix='.vtp') as f:
            f.write(gzip.open(path).read()); f.flush(); return pv.read(f.name)
    return pv.read(path)


def find(runs, run, t):
    d = Path(runs) / run / 'postProcessing/planes'
    best = min((p for p in d.iterdir() if p.is_dir()), key=lambda p: abs(float(p.name) - t))
    for n in ['sectionClear.vtp', 'sectionClear.vtp.gz']:
        if (best / n).exists():
            return best / n, float(best.name)
    sys.exit(f'no sectionClear in {best}')


def main(runs, out, times):
    fig, axes = plt.subplots(len(times), 2, figsize=(13, 1.95 * len(times) + .6), squeeze=False, constrained_layout=True)
    for j, run in enumerate(['open', 'insert']):
        for i, t in enumerate(times):
            path, tt = find(runs, run, t); m = read(path).triangulate()
            P = m.points; s = (P[:, [0, 2]] - [0, 2.75]) @ T_ALONG[[0, 2]]; y = P[:, 1]
            tri = mtri.Triangulation(s, y, m.faces.reshape(-1, 4)[:, 1:])
            TF = (np.asarray(m.point_data['T']) - 273.15) * 9 / 5 + 32
            ax = axes[i, j]
            pc = ax.tripcolor(tri, TF, shading='gouraud', cmap='jet', vmin=44, vmax=84)
            ax.set_aspect('equal'); ax.set_xlim(-.45, 8.15); ax.set_ylim(0, 2.4)
            ax.set_title(f'{"open fire" if run == "open" else "stove insert"}, {tt:g} s', fontsize=10)
            ax.set_yticks([0, 1.2, 2.4]); ax.tick_params(labelsize=8)
            if i == len(times) - 1:
                ax.set_xlabel('distance along the cut from the fireplace wall, m (hall doorway at 5.5-5.6, front wall at 8.1)', fontsize=8)
    cb = fig.colorbar(pc, ax=axes, shrink=.6, pad=.01); cb.set_label('air, F', fontsize=9)
    fig.savefig(out, dpi=110)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit('usage: plot_planes.py RUNS OUT.png [t1 t2 ...]')
    main(sys.argv[1], sys.argv[2], [float(a) for a in sys.argv[3:]] or [30, 150, 300])
