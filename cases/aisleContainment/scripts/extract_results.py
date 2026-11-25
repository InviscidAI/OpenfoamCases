#!/usr/bin/env python3
"""Summarise the two solved halls from their monitors.

    python3 scripts/extract_results.py runs results

Reads runs/<run>/monitors/{ports,regions,cuts}.csv (src/hallMonitor's rows, every 0.125 s) and,
if they are there, runs/<run>/log.buoyantPimpleFoam* (for the steps and the solver's messages),
and writes

  results/summary.txt         the top servers' intake, the hottest intakes, the servers above
                              27 C, the zones, the flow back over the rack tops, the checks
  results/<run>/history.csv   every 1 s from 0 to the end

Definitions, the study's own:
  intake temperature   a port's flux-weighted mean face temperature (the monitor's T_K)
  top servers          s09 and s10 of every rack, 240 servers over all 120 racks; their mean
                       is weighted by each intake's mass flow. Over a window it is the ratio of
                       the time integrals of mass flow x temperature and of mass flow.
  over the rack tops   the gross flow from the hot aisle to the cold side through the plane of
                       each row's back face above the racks (x on the row's hot side, y 2.1-14.1,
                       z 2.2-3.2 m), summed over the six rows; it is not tracer-resolved
  round the ends       the gross flow out of each hot aisle's ends (y 2.1 and 14.1 m), floor to
                       ceiling, into the end zones the supplies blow through
  heat budget          servers' heat + the supplies' enthalpy - the returns' enthalpy
                       + cp T0 (supply - return mass) - the change of the air's internal energy
                       (cv/R) integral p dV, over 10 s to the end, as a share of the servers' heat
Times are interpolated linearly between the monitor's rows.
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CP, T0, K = 1005.0, 293.15, 273.15
ROWS = ['L00', 'R00', 'L01', 'R01', 'L02', 'R02']
F = lambda c: c * 9 / 5 + 32


def interval(t, v, a, b):
    """Mean of each column of v over [a, b], trapezoids on the monitor's times."""
    v = np.atleast_2d(np.asarray(v, float).T).T
    ts = np.r_[a, t[(t > a) & (t < b)], b]
    vv = np.stack([np.interp(ts, t, v[:, i]) for i in range(v.shape[1])], 1)
    return np.trapezoid(vv, ts, axis=0) / (b - a)


def load(root):
    with open(root / 'monitors/ports.csv') as f:
        head = f.readline().strip().split(',')
    names = sorted(c[:-len(':T_K')] for c in head if c.endswith('_intake:T_K'))
    ex = [n.replace('_intake', '_exhaust') for n in names]
    want = ['time_s'] + [n + s for n in names for s in (':T_K', ':out_kg_s', ':out_m3_s', ':Hout_W')] \
        + [n + s for n in ex for s in (':T_K', ':Hin_W')] \
        + [f'return_{k:02}:{s}' for k in range(3) for s in ('Hout_W', 'Hin_W', 'net_kg_s', 'in_kg_s')] \
        + [f'supply_{q}:{s}' for q in ('south', 'north') for s in ('Hin_W', 'Hout_W', 'in_kg_s', 'out_kg_s')]
    P = pd.read_csv(root / 'monitors/ports.csv', usecols=want, dtype=np.float64)
    R = pd.read_csv(root / 'monitors/regions.csv')
    C = pd.read_csv(root / 'monitors/cuts.csv')
    return names, ex, P, R, C


def summarise(run, root):
    names, ex, P, R, C = load(root)
    t = P.time_s.to_numpy()
    T = P[[n + ':T_K' for n in names]].to_numpy()
    m = P[[n + ':out_kg_s' for n in names]].to_numpy()
    top = np.array([n.split('_')[2] in ('s09', 's10') for n in names])
    heat = (P[[n + ':Hin_W' for n in ex]].to_numpy() - P[[n + ':Hout_W' for n in names]].to_numpy()).sum(axis=1)
    rise = (P[[n + ':T_K' for n in ex]].to_numpy() - T).mean(1)
    mT_top, m_top = (T[:, top] * m[:, top]).sum(axis=1), m[:, top].sum(axis=1)
    mT_all, m_all = (T * m).sum(axis=1), m.sum(axis=1)
    draw_m3 = P[[n + ':out_m3_s' for n in names]].sum(axis=1).to_numpy()
    topcut = sum(C[r + '_top:minus_m3_s'] for r in ROWS).to_numpy()       # hot to cold over the tops
    topcut_in = sum(C[r + '_top:plus_m3_s'] for r in ROWS).to_numpy()     # cold to hot over the tops
    endout = sum(C[f'hot_{k}_{s}_{z}:plus_m3_s'] for k in range(3) for s in ('north', 'south') for z in ('lower', 'upper')).to_numpy()
    endin = sum(C[f'hot_{k}_{s}_{z}:minus_m3_s'] for k in range(3) for s in ('north', 'south') for z in ('lower', 'upper')).to_numpy()
    tc = C.time_s.to_numpy()
    tr = R.time_s.to_numpy()
    hs = (P[['supply_south:Hin_W', 'supply_north:Hin_W']].sum(axis=1) - P[['supply_south:Hout_W', 'supply_north:Hout_W']].sum(axis=1)).to_numpy()
    hr = (P[[f'return_{k:02}:Hout_W' for k in range(3)]].sum(axis=1) - P[[f'return_{k:02}:Hin_W' for k in range(3)]].sum(axis=1)).to_numpy()
    ms = (P[['supply_south:in_kg_s', 'supply_north:in_kg_s']].sum(axis=1) - P[['supply_south:out_kg_s', 'supply_north:out_kg_s']].sum(axis=1)).to_numpy()
    mr = P[[f'return_{k:02}:net_kg_s' for k in range(3)]].sum(axis=1).to_numpy()
    rin = P[[f'return_{k:02}:in_kg_s' for k in range(3)]].sum(axis=1).to_numpy()
    end = float(np.floor(t[-1] + 1e-6))

    def budget(a, b):
        q, s, r, ref = interval(t, np.c_[heat, hs, hr, CP * T0 * (ms - mr)], a, b)
        stored = (np.interp(b, tr, R.internalEnergy_J) - np.interp(a, tr, R.internalEnergy_J)) / (b - a)
        return (q + s - r + ref - stored) / q, q, stored

    def window_top(a, b):
        x, y = interval(t, np.c_[mT_top, m_top], a, b)
        return x / y - K

    def window_all(a, b):
        x, y = interval(t, np.c_[mT_all, m_all], a, b)
        return x / y - K

    hist = []
    for tm in np.arange(0, end + 1e-9, 1.0):
        if tm == 0:
            # at rest, before the first step: every intake at 293.15 K
            ti = np.full(len(names), T0)
        else:
            ti = np.array([np.interp(tm, t, T[:, i]) for i in range(len(names))])
        mi = np.array([np.interp(tm, t, m[:, i]) for i in range(len(names))])
        hi = int(ti.argmax())
        row = dict(time_s=tm,
                   top_servers_C=float((ti[top] * mi[top]).sum() / mi[top].sum() - K),
                   all_intakes_C=float((ti * mi).sum() / mi.sum() - K),
                   hottest_intake_C=float(ti[hi] - K), hottest_server=names[hi][:-7] if tm else '',
                   servers_above_27C=int((ti > 300.15).sum()))
        if tm:
            row.update(heat_MW=float(np.interp(tm, t, heat)) / 1e6, mean_rise_K=float(np.interp(tm, t, rise)))
            for z in ('cold_upper_1', 'cold_1', 'cold_upper_0', 'hot_1', 'overhead', 'hall'):
                row[z + '_C'] = float(np.interp(tm, tr, R[z + ':T_K'])) - K
            row.update(over_tops_hot_to_cold_m3_s=float(np.interp(tm, tc, topcut)),
                       over_tops_cold_to_hot_m3_s=float(np.interp(tm, tc, topcut_in)),
                       ends_out_of_hot_aisles_m3_s=float(np.interp(tm, tc, endout)),
                       ends_into_hot_aisles_m3_s=float(np.interp(tm, tc, endin)),
                       racks_draw_m3_s=float(np.interp(tm, t, draw_m3)),
                       returns_inflow_kg_s=float(np.interp(tm, t, rin)),
                       Tmin_air_C=float(np.interp(tm, tr, R.Tmin_K)) - K, Tmax_air_C=float(np.interp(tm, tr, R.Tmax_K)) - K,
                       maxCo=float(np.interp(tm, tr, R.maxCo)))
            if run == 'contained':
                # the closed cold side's air mass against its mass at rest (open has no closed cold side)
                row['cold_side_mass_drift_pct'] = 100 * float(np.interp(tm, tr, R['cold_side:mass_drift_fraction']))
        hist.append(row)
    H = pd.DataFrame(hist)

    # every server's intake over 29-30 s, and the racks the clip's section cuts (r08, y 6.3-6.9 m)
    m29 = interval(t, T * m, 29, 30) / interval(t, m, 29, 30)
    r08 = np.array(['_r08_' in n for n in names])
    inner = np.array([n[:3] in ('R00', 'L01', 'R01', 'L02') for n in names])

    def wmean(sel, a=29, b=30):
        x, y = interval(t, np.c_[(T[:, sel] * m[:, sel]).sum(axis=1), m[:, sel].sum(axis=1)], a, b)
        return x / y - K
    s = dict(run=run, end=end, monitor_rows=len(t), max_spacing=float(np.diff(t).max()),
             top=[(w, window_top(*w)) for w in [(14, 15), (29, 30), (59, 60), (110, 120)] if w[1] <= end],
             all=[(w, window_all(*w)) for w in [(29, 30), (110, 120)] if w[1] <= end],
             r08_top_inner=wmean(r08 & top & inner), r08_top_outer=wmean(r08 & top & ~inner), r08_top=wmean(r08 & top),
             hottest_29_30=(float(m29.max() - K), names[int(m29.argmax())][:-7]),
             above27_29_30=int((m29 > 300.15).sum()),
             heat_20_30=float(interval(t, heat, 20, 30)[0]), rise_20_30=float(interval(t, rise, 20, 30)[0]),
             budget=budget(10, end),
             over_tops=[(w, float(interval(tc, topcut, *w)[0]), float(interval(tc, topcut_in, *w)[0]),
                         float(interval(tc, endout, *w)[0]), float(interval(tc, endin, *w)[0]),
                         float(interval(t, draw_m3, *w)[0])) for w in [(29, 30), (59, 60), (110, 120)] if w[1] <= end],
             returns_inflow_max=float(rin[t >= 1].max()),
             tmin_after1=float(R.Tmin_K[tr >= 1].min()) - K, tmax=float(R.Tmax_K.max()) - K,
             drift=(float(R['cold_side:mass_drift_fraction'].abs().max()) * 100,
                    float(R['cold_side:mass_kg'].iloc[0]), float(R['cold_side:mass_kg'].iloc[-1])),
             maxCo=float(R.maxCo[tr > 1].max()))
    logs = sorted(root.glob('log.buoyantPimpleFoam*'))
    if logs:
        steps = bounding = fatal = 0
        pmax = 0.0
        for lp in logs:
            txt = lp.read_text(errors='replace')
            steps += len(re.findall(r'^ExecutionTime =', txt, re.M))
            bounding += len(re.findall('bounding ', txt))
            fatal += len(re.findall('FOAM FATAL', txt))
            for block in re.split(r'\nTime = ', txt)[1:]:
                v = re.findall(r'Solving for p_rgh, Initial residual = \S+, Final residual = ([0-9.eE+-]+)', block)
                if v:
                    pmax = max(pmax, float(v[-1]))
        s['log'] = dict(files=[p.name for p in logs], steps=steps, bounding=bounding, fatal=fatal, pmax=pmax)
    return H, s


def main():
    if len(sys.argv) != 3:
        raise SystemExit('usage: extract_results.py runs results')
    runs, out = Path(sys.argv[1]), Path(sys.argv[2])
    S = {}
    for run in ('open', 'contained'):
        H, S[run] = summarise(run, runs / run)
        (out / run).mkdir(parents=True, exist_ok=True)
        H.to_csv(out / run / 'history.csv', index=False, float_format='%.6g')
    o, c = S['open'], S['contained']
    L = ['Aisle containment: an open hall against hot aisles closed off, the same 120 racks from rest.',
         'From the monitors of the solved runs (src/hallMonitor), by scripts/extract_results.py.',
         'C and F; flows in m3/s; window means are ratios of time integrals.', '']
    L.append('The top servers (s09-s10 of all 120 racks), flux-weighted mean intake:')
    for (w, a), (_, b) in zip(o['top'], c['top']):
        L.append(f'  {w[0]:>3}-{w[1]:<3} s   open {a:8.4f} C ({F(a):5.1f} F)   contained {b:8.4f} C ({F(b):5.1f} F)   difference {a - b:6.4f} K')
    L.append('Every intake, flux-weighted mean:')
    for (w, a), (_, b) in zip(o['all'], c['all']):
        L.append(f'  {w[0]:>3}-{w[1]:<3} s   open {a:8.4f} C ({F(a):5.1f} F)   contained {b:8.4f} C ({F(b):5.1f} F)')
    L.append('29-30 s:')
    for r in (o, c):
        L.append(f"  {r['run']:<9} hottest intake {r['hottest_29_30'][0]:.4f} C ({F(r['hottest_29_30'][0]):.1f} F) at {r['hottest_29_30'][1]};"
                 f" servers drawing above 27 C (80.6 F): {r['above27_29_30']} of 1200")
        L.append(f"            rack 08 (the clip's section, y 6.3-6.9 m), top servers: the four inner rows {r['r08_top_inner']:.2f} C ({F(r['r08_top_inner']):.1f} F),"
                 f" the two outer rows {r['r08_top_outer']:.2f} C ({F(r['r08_top_outer']):.1f} F), all six {r['r08_top']:.2f} C ({F(r['r08_top']):.1f} F)")
    L.append('')
    L.append('Gross flows over the rack tops and round the hot aisles\' ends (six rows, three aisles):')
    for r in (o, c):
        for w, hc, ch, eo, ei, d in r['over_tops']:
            L.append(f"  {r['run']:<9} {w[0]:>3}-{w[1]:<3} s   over the tops hot to cold {hc:7.3f} ({100 * hc / d:5.2f}% of the racks' draw {d:.2f}),"
                     f" cold to hot {ch:7.3f};  ends out of the hot aisles {eo:7.3f}, into them {ei:7.3f}")
    L.append('')
    L.append('Checks:')
    for r in (o, c):
        b = r['budget']
        L.append(f"  {r['run']:<9} 0-{r['end']:.0f} s, {r['monitor_rows']} monitor rows, at most {r['max_spacing']:.4f} s apart")
        L.append(f"            servers' heat over 20-30 s {r['heat_20_30'] / 1e6:.6f} MW, mean rise {r['rise_20_30']:.6f} K")
        L.append(f"            heat budget over 10-{r['end']:.0f} s closes to {100 * b[0]:+.4f}% of the servers' heat ({b[1] / 1e6:.6f} MW; stored {b[2]:+.2f} W)")
        L.append(f"            largest inflow through the ceiling returns after 1 s {r['returns_inflow_max']:.3g} kg/s")
        L.append(f"            coldest air after 1 s {r['tmin_after1']:.4f} C, warmest air {r['tmax']:.4f} C, largest Courant number after 1 s {r['maxCo']:.4f}")
        if r['run'] == 'contained':
            L.append(f"            the closed cold side's air mass {r['drift'][1]:.6f} kg at the first row, {r['drift'][2]:.6f} kg at the end, largest drift {r['drift'][0]:.6f}%")
        if 'log' in r:
            g = r['log']
            L.append(f"            logs {', '.join(g['files'])}: {g['steps']} steps, {g['bounding']} bounding messages, {g['fatal']} fatal errors,"
                     f" largest final p_rgh residual at a step's end {g['pmax']:.3g}")
    (out / 'summary.txt').write_text('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
