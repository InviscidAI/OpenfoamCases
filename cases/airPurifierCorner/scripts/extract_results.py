#!/usr/bin/env python3
"""Read both solved runs' monitors and write results/.

usage: extract_results.py <runs dir> <results dir>

Writes <results>/<run>/history.csv every 5 s, <results>/corner_vs_middle.csv every 30 s, and
<results>/summary.txt. Everything is read from the function objects in system/controlDict:
roomMean, roomCoV, roomIntegral (volume-weighted over the fluid), intakeC (the intake's
flux-weighted C), flow_purifierIn and flow_purifierOut (sum of |phi|), points (C at seven probes)
and smokeBounds (C's minimum and maximum over every cell at every time step). C is the share of
the starting smoke left; 1 - C is the clean-air fraction.
"""
import math, sys
from pathlib import Path
import numpy as np

runs, out = Path(sys.argv[1]), Path(sys.argv[2])
Q = 0.0675                       # m3/s through each patch after the 2 s ramp: the smoke CADR
POINTS = ['pillow', 'farCorner', 'nearCorner', 'wardrobeGap', 'doorSide', 'roomMiddle', 'underBedSide']
REPORT = [30, 60, 120, 180, 300, 600, 900, 1200]


def table(p):
    return np.loadtxt(p, comments='#')


def volume(p):
    for line in open(p):
        if line.startswith('# Volume'):
            return float(line.split(':')[1])
    raise ValueError(f'no volume in {p}')


def bounds(p):
    """C's extremes at every step: time, min, location, max, location."""
    rows = []
    for line in open(p):
        if line.startswith('#'):
            continue
        f = line.replace('(', ' ').replace(')', ' ').split()
        # time C min x y z proc max x y z proc
        rows.append([float(f[0]), float(f[2]), float(f[3]), float(f[4]), float(f[5]),
                     float(f[7]), float(f[8]), float(f[9]), float(f[10])])
    return np.array(rows)


def read(run):
    pp = runs / run / 'postProcessing'
    m = table(pp / 'roomMean/0/volFieldValue.dat')
    d = dict(t=m[:, 0], mean=m[:, 1],
             cov=table(pp / 'roomCoV/0/volFieldValue.dat')[:, 1],
             integral=table(pp / 'roomIntegral/0/volFieldValue.dat')[:, 1],
             intake=table(pp / 'intakeC/0/surfaceFieldValue.dat')[:, 1],
             fin=table(pp / 'flow_purifierIn/0/surfaceFieldValue.dat')[:, 1],
             fout=table(pp / 'flow_purifierOut/0/surfaceFieldValue.dat')[:, 1],
             pts=table(pp / 'points/0/C')[:, 1:],
             V=volume(pp / 'roomMean/0/volFieldValue.dat'),
             bounds=bounds(pp / 'smokeBounds/0/fieldMinMax.dat'))
    n = len(d['t'])
    for k in ('cov', 'integral', 'intake', 'fin', 'fout', 'pts'):
        assert len(d[k]) == n, (run, k, len(d[k]), n)
    d['std'] = d['cov'] * d['mean']
    return d


def cross(t, y, level):
    """First time y falls to level, linear between the 1 s readings; nan if it never does."""
    below = np.nonzero(y <= level)[0]
    if len(below) == 0:
        return float('nan')
    k = below[0]
    if k == 0:
        return float(t[0])
    return float(t[k - 1] + (y[k - 1] - level) / (y[k - 1] - y[k]) * (t[k] - t[k - 1]))


def mmss(s):
    return 'never' if math.isnan(s) else f'{int(s // 60)}:{int(round(s % 60)):02d}'


R = {r: read(r) for r in ('corner', 'middle')}
c, m = R['corner'], R['middle']
assert np.array_equal(c['t'], m['t']), 'the two runs have different monitor times'
t = c['t']
tau = c['V'] / Q
mixed = np.exp(-t / tau)

for run, d in R.items():
    (out / run).mkdir(parents=True, exist_ok=True)
    with open(out / run / 'history.csv', 'w') as f:
        f.write('time_s,room_C,room_std_C,intake_C,intake_to_room,flow_in_m3s,flow_out_m3s,'
                + ','.join(f'C_{n}' for n in POINTS) + ',mixed_C\n')
        for k in range(len(t)):
            if t[k] % 5:
                continue
            row = [d['mean'][k], d['std'][k], d['intake'][k], d['intake'][k] / d['mean'][k], d['fin'][k], d['fout'][k],
                   *d['pts'][k], mixed[k]]
            f.write(f'{t[k]:g},' + ','.join(f'{x:.6g}' for x in row) + '\n')

with open(out / 'corner_vs_middle.csv', 'w') as f:
    f.write('time_s,mixed_clean,corner_room_clean,corner_intake_clean,corner_pillow_clean,'
            'middle_room_clean,middle_intake_clean,middle_pillow_clean\n')
    for k in range(len(t)):
        if t[k] % 30:
            continue
        row = [1 - mixed[k], 1 - c['mean'][k], 1 - c['intake'][k], 1 - c['pts'][k, 0],
               1 - m['mean'][k], 1 - m['intake'][k], 1 - m['pts'][k, 0]]
        f.write(f'{t[k]:g},' + ','.join(f'{x:.4f}' for x in row) + '\n')

L = []
w = L.append
w('airPurifierCorner: a small tower purifier, 0.0675 m3/s of clean air, in the corner or the middle of a closed')
w('4.5 x 4.5 x 2.4 m bedroom, the air starting evenly full of smoke (C = 1), isothermal, from rest.')
w(f'Fluid volume {c["V"]:.4f} (corner) and {m["V"]:.4f} m3 (middle); a perfectly mixed room: C = exp(-t/{tau:.0f} s).')
w(f'Monitors every 1 s from {t[0]:g} to {t[-1]:g} s, {len(t)} rows in each run.')
w('')
w('Clean-air fraction, 1 - C. Room volume-weighted, intake flux-weighted, pillow the probe at (3.5, 0.75, 4.2).')
w('  time   mixed | corner room intake pillow | middle room intake pillow')
for T in REPORT:
    k = int(np.nonzero(t == T)[0][0])
    w(f'  {T:5d}  {1 - mixed[k]:.3f} | {1 - c["mean"][k]:.3f}  {1 - c["intake"][k]:.3f}  {1 - c["pts"][k, 0]:.3f} '
      f'| {1 - m["mean"][k]:.3f}  {1 - m["intake"][k]:.3f}  {1 - m["pts"][k, 0]:.3f}')
w('')
w(f'At {t[-1]:g} s: room C {c["mean"][-1]:.4f} corner, {m["mean"][-1]:.4f} middle, {mixed[-1]:.4f} mixed: '
  f'{100 * (1 - c["mean"][-1]):.1f}%, {100 * (1 - m["mean"][-1]):.1f}% and {100 * (1 - mixed[-1]):.1f}% of the smoke gone.')
w('')
w('First time C falls to a level, min:s (room corner, middle | pillow corner, middle | mixed)')
for lvl in (0.9, 0.5, 0.25, 0.2):
    w(f'  {100 * (1 - lvl):3.0f}% clean: {mmss(cross(t, c["mean"], lvl))} {mmss(cross(t, m["mean"], lvl))} '
      f'| {mmss(cross(t, c["pts"][:, 0], lvl))} {mmss(cross(t, m["pts"][:, 0], lvl))} | {mmss(-tau * math.log(lvl))}')
w('')
w('First 1 s reading at which each probe is 1% clean (C <= 0.99), s: corner, middle')
for j, n in enumerate(POINTS):
    fc = np.nonzero(c['pts'][:, j] <= 0.99)[0]
    fm = np.nonzero(m['pts'][:, j] <= 0.99)[0]
    w(f'  {n:13s} {t[fc[0]] if len(fc) else float("nan"):5.0f} {t[fm[0]] if len(fm) else float("nan"):5.0f}')
w('  (roomMiddle stands 8 mm off the middle purifier\'s axis, in its jet: not room air in the middle run)')
w('')
w('Share of the rated clean air the room receives')
for run, d in R.items():
    ratio = d['intake'] / d['mean']
    tc = -t[-1] / math.log(d['mean'][-1])
    w(f'  {run}: time mean of C_intake/C_room {ratio.mean():.4f} (300-1200 s {ratio[t >= 300].mean():.4f}); '
      f'room decay time constant over the run {tc:.0f} s against {tau:.0f} mixed, {tau / tc:.3f} of the rating')
w('')
w('Room standard deviation of C: peak (time), and at the end')
for run, d in R.items():
    k = int(np.argmax(d['std']))
    w(f'  {run}: {d["std"][k]:.4f} ({t[k]:g} s), {d["std"][-1]:.4f}')
w(f'C at the seven probes at {t[-1]:g} s')
for run, d in R.items():
    w(f'  {run}: ' + ', '.join(f'{n} {x:.3f}' for n, x in zip(POINTS, d['pts'][-1])))
w('')
w('Checks')
for run, d in R.items():
    ramp = t >= 3
    ferr = max(np.abs(d['fin'][ramp] / Q - 1).max(), np.abs(d['fout'][ramp] / Q - 1).max())
    lost = d['integral'][0] - d['integral'][-1]
    taken = np.trapezoid(Q * d['intake'], t) if hasattr(np, 'trapezoid') else np.trapz(Q * d['intake'], t)
    w(f'  {run}: flow in/out at the end {d["fin"][-1]:.6f}/{d["fout"][-1]:.6f} m3/s, largest departure from {Q} after 3 s {ferr:.2e}; '
      f'budget {t[0]:g}-{t[-1]:g} s: room lost {lost:.4f} m3 of C, intake took {taken:.4f}, {100 * (lost - taken) / taken:+.3f}%')
w('')
w('C at every time step (smokeBounds); the solved runs were to stop if C left -0.01..1.01')
for run, d in R.items():
    b = d['bounds']
    i, j = int(np.argmin(b[:, 1])), int(np.argmax(b[:, 5]))
    w(f'  {run}: {len(b)} steps; min {b[i, 1]:.6g} at {b[i, 0]:.4g} s at ({b[i, 2]:.3f}, {b[i, 3]:.3f}, {b[i, 4]:.3f}); '
      f'max {b[j, 5]:.6g} at {b[j, 0]:.4g} s at ({b[j, 6]:.3f}, {b[j, 7]:.3f}, {b[j, 8]:.3f}); '
      f'inside the band: {bool((b[:, 1] >= -0.01).all() and (b[:, 5] <= 1.01).all())}')
    for name, sel in (('above 1.0003', b[:, 5] > 1.0003), ('above 1.001', b[:, 5] > 1.001), ('below -0.001', b[:, 1] < -0.001)):
        k = np.nonzero(sel)[0]
        w(f'    steps {name}: {len(k)}' + (f', the last at {b[k[-1], 0]:.4g} s' if len(k) else ''))
(out / 'summary.txt').write_text('\n'.join(L) + '\n')
print('\n'.join(L))
