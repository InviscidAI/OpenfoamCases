#!/usr/bin/env python3
"""results/ from the two runs' monitors: each run's history every 60 s and a summary.

    python3 scripts/extract_results.py RUNS RESULTS

RUNS holds shut/ and ajar/, each with postProcessing/monitor87/monitor.csv as system/monitor87
writes it: a row at the first time step on or after every 5 s of flow, and at the writes. The
history is that monitor linearly interpolated to every whole minute, 60-28,800 s (at 0 s
all the air is at rest at 18 C and 500 ppm). Everything in the
monitor is per metre of the section's depth; the flows and heat here are for the whole 3.5 m deep
room (times 3.5). "Heads" is the air 10-40 cm above both sleepers' faces, x 1.00-2.50 m,
y 0.90-1.20 m: the number each panel of the clip shows, rounded to 50 ppm.
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd

DEPTH = 3.5            # m, the room's depth: the section is per metre of it
LEAK = 0.20            # air changes an hour with the outside, a well-mixed exchange (constant/fvOptions)
BREATH = 1.0971 + .85143   # ppm m3/s per metre: both sleepers
TIMES_H = [0, .1, .5, 1, 2, 3, 4, 5, 6, 7, 8]
REGIONS = ['heads', 'bedroom', 'bedroomUpper', 'bedroomLower', 'hall', 'hallUpper']


def load(runs, run):
    d = pd.read_csv(Path(runs) / run / 'postProcessing/monitor87/monitor.csv')
    return d.sort_values('time', kind='stable').drop_duplicates('time', keep='last').reset_index(drop=True)


def derived(d):
    o = pd.DataFrame({'time_s': d.time})
    for r in REGIONS:
        o[f'{r}_CO2_ppm'] = d[f'{r}_VC'] / d[f'{r}_V']
    for r in ['heads', 'bedroom', 'hall']:
        o[f'{r}_T_C'] = d[f'{r}_VT'] / d[f'{r}_V'] - 273.15
    o['bedroom_minus_hall_K'] = o.bedroom_T_C - o.hall_T_C
    for band in ['doorPlane', 'doorUnder', 'doorLeaf', 'doorHead']:
        name = 'door' if band == 'doorPlane' else band
        o[f'{name}_out_L_s'] = d[f'{band}_Qout'] * DEPTH * 1000   # bedroom to hall, at x = 3.55 m
        o[f'{name}_in_L_s'] = d[f'{band}_Qin'] * DEPTH * 1000
    excess = (o.bedroom_CO2_ppm - 425) * d.bedroom_V
    # CO2 the door takes out of the bedroom (flow and diffusion, at its bedroom face x = 3.50 m)
    # against the bedroom's excess over outdoors, as air changes an hour
    o['door_CO2_ACH'] = (d.bedroomSide_CadvNet + d.bedroomSide_CdiffNet) / excess * 3600
    o['door_diffusion_share'] = d.bedroomSide_CdiffNet.abs() / (d.bedroomSide_Cout + d.bedroomSide_Cin).replace(0, np.nan)
    for w in ['window', 'outsideWall', 'floor', 'ceiling', 'doorWallBedroom', 'sleeperMan', 'sleeperWoman']:
        o[f'{w}_heat_out_W'] = d[f'{w}_heatOut'] * DEPTH
    for w in ['window', 'outsideWall', 'floor', 'ceiling']:
        o[f'{w}_UA_dT_W'] = d[f'{w}_UA_deltaT'] * DEPTH
    o['air_T_min_C'] = d.airTmin - 273.15
    o['air_T_max_C'] = d.airTmax - 273.15
    o['air_CO2_max_ppm'] = d.airCmax
    o['air_U_max_m_s'] = d.airUmax
    o['dt_s'] = d.dt
    return o


def at(o, t):
    return {c: float(np.interp(t, o.time_s, o[c])) for c in o if c != 'time_s'}


def main(runs, results):
    res = Path(results); out = {}
    for run in ['shut', 'ajar']:
        o = derived(load(runs, run)); out[run] = o
        grid = np.arange(60, min(28800, o.time_s.iloc[-1]) + 1e-6, 60.0)
        h = pd.DataFrame({'time_s': grid})
        for c in o:
            if c != 'time_s':
                h[c] = np.interp(grid, o.time_s, o[c])
        (res / run).mkdir(parents=True, exist_ok=True)
        h.to_csv(res / run / 'history.csv', index=False, float_format='%.6g')
    s, a = out['shut'], out['ajar']
    L = ['Bedroom door shut or ajar: two sleepers from lights-out, 0-28,800 s (8 h).',
         'From the monitors of the runs (system/monitor87), by scripts/extract_results.py. Flows and heat for the',
         'whole 3.5 m deep room; CO2 in ppm by volume; "heads" is x 1.00-2.50 m, y 0.90-1.20 m.', '',
         'CO2 at the heads (the clip\'s number, rounded to 50) and in the whole bedroom:']
    for th in TIMES_H:
        t = th * 3600
        if t > min(s.time_s.iloc[-1], a.time_s.iloc[-1]) + 1e-6:
            continue
        ps, pa = (at(s, t), at(a, t)) if t > 0 else ({'heads_CO2_ppm': 500, 'bedroom_CO2_ppm': 500}, {'heads_CO2_ppm': 500, 'bedroom_CO2_ppm': 500})
        L.append(f'  {th:4g} h   heads shut {ps["heads_CO2_ppm"]:7.1f} ({50 * round(ps["heads_CO2_ppm"] / 50):5d})'
                 f'   ajar {pa["heads_CO2_ppm"]:7.1f} ({50 * round(pa["heads_CO2_ppm"] / 50):5d})'
                 f'   shut - ajar {ps["heads_CO2_ppm"] - pa["heads_CO2_ppm"]:7.1f}'
                 f'   bedroom shut {ps["bedroom_CO2_ppm"]:7.1f} ajar {pa["bedroom_CO2_ppm"]:7.1f}')
    L += ['', 'The air and the door:']
    for th in [.5, 1, 2, 4, 6, 8]:
        t = th * 3600
        for run, o in out.items():
            if t > o.time_s.iloc[-1] + 1e-6:
                continue
            p = at(o, t)
            L.append(f'  {run:4s} {th:3g} h   bedroom {p["bedroom_T_C"]:.3f} C, hall {p["hall_T_C"]:.3f} C ({p["bedroom_minus_hall_K"]:+.3f} K);'
                     f' hall CO2 {p["hall_CO2_ppm"]:.0f} ppm; through the door {p["door_out_L_s"]:.3f} L/s out and {p["door_in_L_s"]:.3f} in;'
                     f' the door\'s CO2 removal {p["door_CO2_ACH"]:.3f} air changes an hour (+ {LEAK} leakage)')
    L += ['', 'Heat out of the bedroom air, W (negative: into it):']
    for th in [1, 2, 8]:
        t = th * 3600
        for run, o in out.items():
            if t > o.time_s.iloc[-1] + 1e-6:
                continue
            p = at(o, t)
            L.append(f'  {run:4s} {th:3g} h   window {p["window_heat_out_W"]:.2f} (U A dT {p["window_UA_dT_W"]:.2f}), outside wall {p["outsideWall_heat_out_W"]:.2f}'
                     f' ({p["outsideWall_UA_dT_W"]:.2f}), floor {p["floor_heat_out_W"]:.2f} ({p["floor_UA_dT_W"]:.2f}), ceiling {p["ceiling_heat_out_W"]:.2f}'
                     f' ({p["ceiling_UA_dT_W"]:.2f}), door wall {p["doorWallBedroom_heat_out_W"]:.2f}, sleepers {p["sleeperMan_heat_out_W"] + p["sleeperWoman_heat_out_W"]:.1f}')
    L += ['', 'Across the restart at 7,200 s (the monitor rows either side, not interpolated):']
    for run, o in out.items():
        i = int(np.searchsorted(o.time_s.to_numpy(), 7200 - 1e-6))
        if i + 1 >= len(o):
            continue
        for j in [i, i + 1]:
            r = o.iloc[j]
            L.append(f'  {run:4s} t = {r.time_s:.6f} s   heads {r.heads_CO2_ppm:.6f} ppm, bedroom {r.bedroom_T_C:.9f} C,'
                     f' window {r.window_heat_out_W:.4f} W, floor {r.floor_heat_out_W:.4f} W, door out {r.door_out_L_s:.5f} L/s')
    L += ['', 'Checks:']
    for run, o in out.items():
        late = o[o.time_s > 60]
        L.append(f'  {run:4s} {len(o)} monitor rows, {o.time_s.iloc[0]:g}-{o.time_s.iloc[-1]:g} s; air {late.air_T_min_C.min():.3f} to'
                 f' {late.air_T_max_C.max():.3f} C after 60 s; highest CO2 in a cell {o.air_CO2_max_ppm.max():.0f} ppm; fastest air'
                 f' {o.air_U_max_m_s.max():.3f} m/s; time step {o.dt_s.iloc[len(o) // 2]:.4f} s at mid-run;'
                 f' the window\'s heat at most {100 * (o.window_heat_out_W / o.window_UA_dT_W - 1).abs()[o.time_s > 60].max():.1f}% off U A dT after 60 s')
    (res / 'summary.txt').write_text('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('usage: extract_results.py RUNS RESULTS')
    main(*sys.argv[1:])
