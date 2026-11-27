#!/usr/bin/env python3
"""results/ from the two solved runs' monitors: python3 scripts/extract_results.py <runs> <results>

Reads <runs>/{vents,noVents}/postProcessing/metrics/metrics.csv (one row a time step, columns named
in scripts/metrics_columns.json) and writes <results>/<run>/history.csv every 0.5 s and
<results>/summary.txt. Every share is a percentage of the tracer the cough released in that run.
"""
from pathlib import Path
import json, sys
import numpy as np

here = Path(__file__).resolve().parents[1]
runs, results = Path(sys.argv[1]), Path(sys.argv[2])
names = json.loads((here / 'scripts/metrics_columns.json').read_text())
regions = [('row', 'row_tracer_kg', "the cougher's row, x 0.92-1.72 m, whole section"),
           ('gap', 'gap_tracer_kg', 'between the cougher\'s seat back and the seat back ahead, x 1.20-1.72 m'),
           ('seatR', 'seatR_tracer_kg', "the row's block at z > 0.28 m (the cougher's)"),
           ('aisle', 'aisle_tracer_kg', "the row's aisle, |z| < 0.28 m"),
           ('seatL', 'seatL_tracer_kg', "the row's other block, z < -0.28 m"),
           ('ahead', 'ahead_tracer_kg', 'the row ahead, x > 1.72 m'),
           ('behind', 'behind_tracer_kg', 'the row behind, x < 0.92 m'),
           ('exhaustR', 'exhaustR_tracer_kg', "out through the exhaust on the cougher's side"),
           ('exhaustL', 'exhaustL_tracer_kg', 'out through the other exhaust'),
           ('endLayers', 'sink_remainder_kg', 'taken by the two end layers (the account\'s remainder)')]
lines = []
for run in ['vents', 'noVents']:
    d = np.loadtxt(runs / run / 'postProcessing/metrics/metrics.csv', delimiter=',')
    col = {n: d[:, i] for i, n in enumerate(names)}
    t = col['time']
    release = col['release_kg'][-1]
    share = {k: 100 * col[c] / release for k, c, _ in regions}
    targets = np.arange(0.5, t[-1] + 1e-9, 0.5)
    rows = [int(np.argmin(abs(t - x))) for x in targets]
    out = results / run
    out.mkdir(parents=True, exist_ok=True)
    with open(out / 'history.csv', 'w') as f:
        f.write('time_s,' + ','.join(k + '_pct' for k, _, _ in regions) + ',max_speed_m_s\n')
        for i in rows:
            f.write(f'{t[i]:.4f},' + ','.join(f'{share[k][i]:.3f}' for k, _, _ in regions) + f',{col["maxU_m_s"][i]:.4f}\n')
    below = np.flatnonzero((share['row'] < 50) & (t >= 1))  # after the cough, not before it has released anything
    j = below[0]
    half = t[j - 1] + (50 - share['row'][j - 1]) * (t[j] - t[j - 1]) / (share['row'][j] - share['row'][j - 1])
    lines.append(f'== {run} ==')
    lines.append(f'cough released {1e3 * col["mouth_volume_m3"][-1]:.5f} L of air, {release:.6e} kg of tracer; solved to {t[-1]:g} s in {len(t)} steps')
    lines.append(f'half of it has left the row by {half:.2f} s')
    lines.append('share of the release, %   ' + ''.join(f'{x:>8g} s' for x in [1, 2, 3, 5, 10, 20, 30, 45, 60]))
    for k, _, what in regions:
        vals = [share[k][int(np.argmin(abs(t - x)))] for x in [1, 2, 3, 5, 10, 20, 30, 45, 60]]
        lines.append(f'{k:<26}' + ''.join(f'{v:10.2f}' for v in vals) + f'   {what}')
    i = len(t) - 1
    noz = sum(col[f'nozzle{k}_in_kg_s'][i] for k in 'ABCDEF')
    lines.append(f'at {t[i]:g} s: the six nozzles {1e3 * noz:.2f} g/s in, side slots {1e3 * (col["sideSlotR_in_kg_s"][i] + col["sideSlotL_in_kg_s"][i]):.1f} g/s, ceiling {1e3 * col["ceilingSlot_in_kg_s"][i]:.1f} g/s, exhausts {1e3 * col["exhaustR_out_kg_s"][i]:.1f} and {1e3 * col["exhaustL_out_kg_s"][i]:.1f} g/s out')
    lines.append(f'largest speed over 1-60 s {col["maxU_m_s"][t >= 1].max():.2f} m/s, Courant at most {col["maxCo"][t >= 1].max():.3f}' if 'maxCo' in col else '')
    lines.append('')
(results / 'summary.txt').write_text('\n'.join(lines))
print('\n'.join(lines))
