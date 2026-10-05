#!/usr/bin/env python3
"""Summarize the dust runs (./Allrun <layout> dust) and the dust's numerics check.

For each layout with a runs/<layout>_dust, from its 0.02 s records and the every-step
DUSTCSV lines in its log.pimpleFoam:

- the dust in the air entering the graphics card, flow-weighted over its fan openings, as a
  share of the room's, at filter captures 0.5, 0.8 and 0.9, over the settled window, each
  half of it, and from the every-step record as a check; and the case's mean dust at 8 s;
- the one-way air flows through each panel opening (in and out separately) and the share
  of the entering air that came through an unfiltered opening;
- the dust budget over 0-8 s: what each field holds at the end against what came in less
  what left through every boundary, advection and diffusion, as a share of what came in.

-> results/dust_summary.csv, results/dust_budget.csv, results/dust_card.png.

With runs/<layout>_dust_upwind and _asT (scripts/dust_scheme_check.sh), it also compares
the two: the card's dust over 8.5-9.0 and 9.0-9.5 s, and on the card-middle section at
8.5, 9.0 and 9.5 s the mean and 95th percentile of the difference and the mean magnitude
of the dust's gradient, which numerical diffusion lowers -> results/dust_scheme_check.csv.

Dust is (1 - capture) * dustF + dustU throughout (scripts/make_case.py).
"""
import csv
import json
from pathlib import Path

import numpy as np

R = Path(__file__).resolve().parents[1]
C = json.loads((R / 'config/model.json').read_text())
CAPTURES = (0.5, 0.8, 0.9)
CLIP_CAPTURE = 0.5          # a woven-mesh case filter (README)
SETTLED = tuple(C['settledWindow_s'])
END = C['endTime_s']
GPU_FLOW = C['gpuFlow_m3_s']
VENTS = ('vent_front', 'vent_top', 'vent_slots')
OUT = R / 'results'


def openings(layout):
    """The openings in the order of the run's DUSTCSV lines, as make_case.py writes them."""
    bottom = ['bottom_front', 'bottom_rear'] if C['layouts'][layout].get('geometry') == 'viewer' else []
    fans = ['front_low', 'front_mid', 'front_high'] + bottom + ['rear', 'top_front', 'top_rear']
    return list(VENTS) + ['fan_' + x for x in fans]


def record(run, name):
    f = next((run / 'postProcessing' / name).glob('*/*FieldValue.dat'))
    return np.loadtxt(f, comments='#')


def window(t, v, lo, hi):
    """Mean over [lo, hi] of a sampled record, on a 0.002 s grid."""
    tg = np.arange(lo, hi + 1e-9, 0.002)
    return float(np.interp(tg, t, v).mean())


def history(run, layout):
    cols = ['time_s', 'integral_dustF_m3', 'integral_dustU_m3', 'volume_m3', 'gpu_dustF',
            'gpu_dustU', 'cpu_dustF', 'cpu_dustU', 'netOut_dustF_m3_s', 'netOut_dustU_m3_s']
    for p in openings(layout):
        cols += [f'{p}_dustF_in_m3_s', f'{p}_dustF_out_m3_s', f'{p}_dustU_in_m3_s', f'{p}_dustU_out_m3_s']
    rows = {}
    for line in (run / 'log.pimpleFoam').read_bytes().decode(errors='ignore').splitlines():
        if line.startswith('DUSTCSV,'):
            v = [float(x) for x in line.split(',')[1:]]
            if len(v) != len(cols):
                raise SystemExit(f'{run}: a DUSTCSV line has {len(v)} values, expected {len(cols)}')
            rows[v[0]] = v          # a restart keeps the last record of a time
    a = np.array([rows[t] for t in sorted(rows)])
    return {c: a[:, j] for j, c in enumerate(cols)}


def dust_runs():
    summary, budget, cards = [], [], {}
    for layout in C['layouts']:
        run = R / 'runs' / f'{layout}_dust'
        if not (run / 'log.pimpleFoam').exists():
            continue
        H = history(run, layout)
        th = H['time_s']
        flows = {}
        for o in VENTS:
            net, mag = record(run, f'{o}_net'), record(run, f'{o}_absolute')
            flows[f'{o}_in_L_s'] = 1000 * window(net[:, 0], 0.5 * (mag[:, 1] - net[:, 1]), *SETTLED)
            flows[f'{o}_out_L_s'] = 1000 * window(net[:, 0], 0.5 * (mag[:, 1] + net[:, 1]), *SETTLED)
        fans_in = 1000 * sum(window(th, H[k], *SETTLED) for k in H
                             if k.startswith('fan_') and k.endswith('_in_m3_s'))
        vents_in = sum(flows[f'{o}_in_L_s'] for o in VENTS)
        unfiltered = 100 * flows['vent_slots_in_L_s'] / (vents_in + fans_in)
        g = record(run, 'gpuIntake')
        tg = g[:, 0]
        for c in CAPTURES:
            dg = 100 * ((1 - c) * g[:, 2] + g[:, 3])
            dh = 100 * ((1 - c) * H['gpu_dustF'] + H['gpu_dustU'])
            row = {'layout': layout, 'filter_capture': c,
                   'card_dust_pct': window(tg, dg, *SETTLED),
                   'card_dust_pct_first_half': window(tg, dg, SETTLED[0], sum(SETTLED) / 2),
                   'card_dust_pct_second_half': window(tg, dg, sum(SETTLED) / 2, SETTLED[1]),
                   'card_dust_pct_every_step': window(th, dh, *SETTLED),
                   'case_mean_dust_pct_at_end': 100 * ((1 - c) * H['integral_dustF_m3'][-1]
                                                       + H['integral_dustU_m3'][-1]) / H['volume_m3'][-1]}
            if c == CLIP_CAPTURE:
                cards[layout] = (tg, dg)
                row['card_reaches_half_at_s'] = float(tg[np.argmax(dg >= 0.5 * row['card_dust_pct'])])
            else:
                row['card_reaches_half_at_s'] = ''
            row.update(flows)
            row['unfiltered_share_of_entering_air_pct'] = unfiltered
            summary.append(row)
        t0 = np.r_[0.0, th]     # the fields start at zero dust and nothing crossing
        for s in ('dustF', 'dustU'):
            held = H[f'integral_{s}_m3'][-1]
            out = np.trapezoid(np.r_[0.0, H[f'netOut_{s}_m3_s']], t0)
            inflow = sum(np.trapezoid(np.r_[0.0, H[k]], t0) for k in H if k.endswith(f'_{s}_in_m3_s'))
            budget.append({'layout': layout, 'field': s, 'held_at_end_m3': held, 'net_in_m3': -out,
                           'came_in_m3': inflow, 'residual_pct_of_inflow': 100 * abs(held + out) / inflow})
    return summary, budget, cards


def plane(run, t):
    import pyvista as pv
    rd = pv.get_reader(str(run / 'postProcessing/planes/cardMid/cardMid.case'))
    tv = np.asarray(rd.time_values)
    j = int(np.argmin(abs(tv - t)))
    rd.set_active_time_value(tv[j])
    m = rd.read()[0]
    c = 100 * ((1 - CLIP_CAPTURE) * np.asarray(m.point_data['dustF']) + np.asarray(m.point_data['dustU']))
    return m, c, float(tv[j])


def gradient_mean(m, c):
    """Area-weighted mean |grad c| over the section's triangles, % per mm."""
    s = m.extract_surface(algorithm='dataset_surface').triangulate()
    f = s.faces.reshape(-1, 4)[:, 1:]
    tris = np.asarray(s.point_data['vtkOriginalPointIds'])[f] if 'vtkOriginalPointIds' in s.point_data else f
    P = m.points[:, :2]
    a, b, d = P[tris[:, 0]], P[tris[:, 1]], P[tris[:, 2]]
    ca, cb, cd = c[tris[:, 0]], c[tris[:, 1]], c[tris[:, 2]]
    e1, e2 = b - a, d - a
    det = e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]
    ok = abs(det) > 1e-14
    gx = ((cb - ca) * e2[:, 1] - (cd - ca) * e1[:, 1])[ok] / det[ok]
    gy = (-(cb - ca) * e2[:, 0] + (cd - ca) * e1[:, 0])[ok] / det[ok]
    area = 0.5 * abs(det[ok])
    return float((np.hypot(gx, gy) * area).sum() / area.sum()) / 1000


def scheme_check():
    rows = []
    for layout in C['layouts']:
        runs = {v: R / 'runs' / f'{layout}_dust_{v}' for v in ('upwind', 'asT')}
        if not all((r / 'postProcessing/gpuIntake').is_dir() for r in runs.values()):
            continue
        card = {}
        for v, r in runs.items():
            g = record(r, 'gpuIntake')
            dg = 100 * ((1 - CLIP_CAPTURE) * g[:, 2] + g[:, 3])
            card[v] = [window(g[:, 0], dg, END + 0.5, END + 1.0), window(g[:, 0], dg, END + 1.0, END + 1.5)]
        for k, (lo, hi) in enumerate([(END + 0.5, END + 1.0), (END + 1.0, END + 1.5)]):
            rows.append({'layout': layout, 'quantity': f'card dust %, {lo:g}-{hi:g} s',
                         'upwind': card['upwind'][k], 'asT': card['asT'][k]})
        for t in (END + 0.5, END + 1.0, END + 1.5):
            (mu, cu, tu), (ma, ca, _) = plane(runs['upwind'], t), plane(runs['asT'], t)
            d = abs(cu - ca)
            rows += [
                {'layout': layout, 'quantity': f'section, mean |upwind - asT|, points, {tu:.2f} s', 'difference': d.mean()},
                {'layout': layout, 'quantity': f'section, 95th percentile |upwind - asT|, points, {tu:.2f} s',
                 'difference': np.percentile(d, 95)},
                {'layout': layout, 'quantity': f'section, mean |grad dust|, % per mm, {tu:.2f} s',
                 'upwind': gradient_mean(mu, cu), 'asT': gradient_mean(ma, ca)},
                {'layout': layout, 'quantity': f'section, mean dust %, {tu:.2f} s', 'upwind': cu.mean(), 'asT': ca.mean()}]
    return rows


def write(name, rows):
    rows = [{k: (float(v) if isinstance(v, np.floating) else v) for k, v in r.items()} for r in rows]
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with (OUT / name).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        w.writeheader()
        for r in rows:
            w.writerow({k: (f'{v:.6g}' if isinstance(v, float) else v) for k, v in r.items()})
    print(f'results/{name}')
    for r in rows:
        print('  ' + ', '.join(f'{k} {v:.4g}' if isinstance(v, float) else f'{k} {v}' for k, v in r.items()))


def main():
    OUT.mkdir(exist_ok=True)
    summary, budget, cards = dust_runs()
    if summary:
        write('dust_summary.csv', summary)
        write('dust_budget.csv', budget)
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 3.6))
        for layout, (t, d) in cards.items():
            ax.plot(t, d, lw=1, label=layout)
        ax.axvspan(*SETTLED, color='0.9')
        ax.set_xlim(0, END)
        ax.set_ylim(0, 100)
        ax.set_xlabel('time after switch-on (s)')
        ax.set_ylabel("dust into the card (% of room's)")
        ax.set_title(f"Dust in the air entering the card, filter capture {CLIP_CAPTURE:g}; "
                     f"{SETTLED[0]:g}-{SETTLED[1]:g} s shaded", fontsize=9)
        ax.legend()
        fig.tight_layout()
        fig.savefig(OUT / 'dust_card.png', dpi=120)
        print('results/dust_card.png')
    check = scheme_check()
    if check:
        write('dust_scheme_check.csv', check)
    if not summary and not check:
        print('no dust runs: ./Allrun positive dust (or another layout) first')


if __name__ == '__main__':
    main()
