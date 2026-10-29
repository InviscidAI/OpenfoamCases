"""The air temperatures and the heat budget of both runs, from their monitors.

    python3 scripts/extract_results.py <runsDir> <resultsDir>

reads <runsDir>/floor and <runsDir>/ceiling: bedroomMonitor's postProcessing/monitor/*/
budget.csv (one row a time step) and zones.csv (one row every 0.625 s), and the initial
air mass that bedroomTools -prepare printed in log.prepare. It writes
<resultsDir>/<run>/history.csv (every 0.625 s), <resultsDir>/minutes.csv and
<resultsDir>/summary.txt. Heat is J (or kJ) per metre of section.

The zones are bedroomMonitor's: the air temperature averaged over x = 1.0-3.7 m (the
occupied zone, more than 1.0 m from the window and 0.3 m from the inner wall) at 0.1 m
(ankle), 0.6 m (knee), 1.1 m (seated head) and 1.7 m (standing head), each cell weighted by
its overlap with the line; the room's volume mean; the share of the air's sensible heat
gain since t = 0 that lies below 1.8 m; and the coldest and warmest cell.

The budget is the setup agent's (its analyze.py). With h_s = cp (T - 293.15) and the air's
E_s = cv integral of rho (T - 293.15), the open room's balance is

    H_in - H_out - Q_glass - dE_layers = dE_s - R T0 dM + dKE - K_in + K_out - W_gravity

where H and K are the enthalpy and kinetic energy carried through the supply slot and the
undercut, Q_glass the heat through the glass, E_layers the heat stored in the floor, ceiling
and inner-wall layers, and -R T0 dM the reference flow work of the air the room loses. Each
flux is summed over the steps with its own step (backward Euler, as the solver integrates);
the residual is the closure, given as a share of the supplied heat H_in. In history.csv,
air_kJ is E_s and flow_work_kJ is -R T0 dM; the summary's "air" is their sum, the heat the
room's air has kept on an enthalpy footing, so that its row of shares adds up to 100% less
the closure and the air's kinetic energy.
"""
import csv
import re
import sys
from pathlib import Path

R = 8314.46261815324 / 28.96
T0 = 293.15
RUNS = ['floor', 'ceiling']
FLUXES = ['supplyHIn', 'supplyHOut', 'returnHIn', 'returnHOut', 'supplyKIn', 'supplyKOut', 'returnKIn', 'returnKOut',
          'glassPower', 'floorPower', 'ceilingPower', 'innerWallPower', 'gravityPower',
          'supplyVolumeIn', 'supplyVolumeOut', 'returnVolumeIn', 'returnVolumeOut',
          'supplyMassIn', 'supplyMassOut', 'returnMassIn', 'returnMassOut']


def F(kelvin):
    return (kelvin - 273.15) * 9 / 5 + 32


def read(case, name):
    rows = []
    for f in sorted((case / 'postProcessing/monitor').glob('*/' + name)):
        with f.open() as stream:
            for r in csv.DictReader(stream):
                if None in r or any(v is None for v in r.values()):
                    continue
                rows.append({k: float(v) for k, v in r.items()})
    return sorted({r['t']: r for r in rows}.values(), key=lambda r: r['t'])


def run(case):
    budget, zones = read(case, 'budget.csv'), read(case, 'zones.csv')
    M0 = float(re.search(r'INITIAL_MASS ([\d.eE+-]+)', (case / 'log.prepare').read_text())[1])
    integ = {k: 0. for k in FLUXES}
    at = {}  # the budget at each zone time
    times = [z['t'] for z in zones]
    i = 0
    for row in budget:
        for k in integ:
            integ[k] += row[k] * row['dt']
        while i < len(times) and times[i] <= row['t'] + 1e-9:
            if abs(times[i] - row['t']) < 1e-6:
                netH = integ['supplyHIn'] - integ['supplyHOut'] + integ['returnHIn'] - integ['returnHOut']
                netK = integ['supplyKIn'] - integ['supplyKOut'] + integ['returnKIn'] - integ['returnKOut']
                stored = row['floorStored'] + row['ceilingStored'] + row['innerWallStored']
                flowWork = -R * T0 * (row['mass'] - M0)
                closure = netH + netK + integ['gravityPower'] - integ['glassPower'] - stored - row['Esensible'] - flowWork - row['KE']
                at[times[i]] = dict(supplied=integ['supplyHIn'], netH=netH, glass=integ['glassPower'],
                                    floor=row['floorStored'], ceiling=row['ceilingStored'], innerWall=row['innerWallStored'],
                                    air=row['Esensible'], flowWork=flowWork, closure=closure,
                                    supplyVolumeIn=integ['supplyVolumeIn'], returnVolumeOut=integ['returnVolumeOut'],
                                    returnVolumeIn=integ['returnVolumeIn'])
            i += 1
    last = budget[-1]
    at[0.0] = dict(supplied=0., netH=0., glass=0., floor=0., ceiling=0., innerWall=0., air=0., flowWork=0., closure=0.,
                   supplyVolumeIn=0., returnVolumeOut=0., returnVolumeIn=0.)
    return dict(zones=zones, at=at, steps=len(budget), t=last['t'], clock=last['clock'])


def main(runs, out):
    runs, out = Path(runs), Path(out)
    data = {k: run(runs / k) for k in RUNS}
    cols = ['t_s', 'ankle_F', 'ankle_C', 'knee_C', 'seated_head_C', 'standing_head_C', 'room_C', 'share_below_1p8m',
            'coldest_C', 'coldest_x_m', 'coldest_y_m', 'supplied_kJ', 'glass_kJ', 'floor_kJ', 'ceiling_kJ', 'inner_wall_kJ',
            'air_kJ', 'flow_work_kJ', 'closure_J']
    for k, d in data.items():
        (out / k).mkdir(parents=True, exist_ok=True)
        with (out / k / 'history.csv').open('w', newline='') as f:
            w = csv.writer(f, lineterminator='\n')
            w.writerow(cols)
            for z in d['zones']:
                b = d['at'].get(z['t'])
                if b is None:
                    continue
                w.writerow([f"{z['t']:g}", f"{F(z['ankleK']):.3f}"] +
                           [f"{z[c] - 273.15:.4f}" for c in ['ankleK', 'kneeK', 'seatedK', 'standingK', 'roomK']] +
                           [f"{z['shareBelow1p8']:.4f}", f"{z['Tmin'] - 273.15:.3f}", f"{z['minX']:g}", f"{z['minY']:g}"] +
                           [f"{b[c] / 1000:.4f}" for c in ['supplied', 'glass', 'floor', 'ceiling', 'innerWall', 'air', 'flowWork']] +
                           [f"{b['closure']:.3f}"])

    def zone(k, t):
        return min(data[k]['zones'], key=lambda z: abs(z['t'] - t))

    with (out / 'minutes.csv').open('w', newline='') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['run', 't_s', 'ankle_F', 'knee_F', 'seated_head_F', 'standing_head_F', 'room_F',
                    'ankle_C', 'knee_C', 'seated_head_C', 'standing_head_C', 'room_C'])
        for k in RUNS:
            for t in [0, 60, 120, 180, 240, 300]:
                z = zone(k, t)
                w.writerow([k, f"{z['t']:g}"] + [f"{F(z[c]):.2f}" for c in ['ankleK', 'kneeK', 'seatedK', 'standingK', 'roomK']] +
                           [f"{z[c] - 273.15:.2f}" for c in ['ankleK', 'kneeK', 'seatedK', 'standingK', 'roomK']])

    L = ['Ceiling vent against floor register, 0-300 s from switch-on (per metre of section)', '']
    L.append('steps: ' + ', '.join(f"{k} {data[k]['steps']}" for k in RUNS) +
             '; last monitored time ' + ' and '.join(f"{data[k]['t']:g}" for k in RUNS) + ' s')
    L.append('wall time: ' + ', '.join(f"{k} {data[k]['clock']:.0f} s ({data[k]['clock'] / 3600:.2f} h)" for k in RUNS) + ', 8 ranks each, side by side')
    L += ['', 'Air at the ankles, 0.1 m, occupied zone x = 1.0-3.7 m (F, C)']
    L.append('  time s     floor            ceiling')
    for t in [0, 30, 60, 120, 180, 240, 300]:
        a, c = zone('floor', t)['ankleK'], zone('ceiling', t)['ankleK']
        L.append(f'  {t:6d}   {F(a):6.2f} F {a - 273.15:6.2f} C   {F(c):6.2f} F {c - 273.15:6.2f} C')
    L += ['', 'At 300 s, occupied zone (C)', '  run       ankle  knee  seated  standing  room   heat below 1.8 m']
    for k in RUNS:
        z = zone(k, 300)
        L.append(f"  {k:8s}  {z['ankleK'] - 273.15:5.2f} {z['kneeK'] - 273.15:5.2f}  {z['seatedK'] - 273.15:5.2f}   "
                 f"{z['standingK'] - 273.15:5.2f}   {z['roomK'] - 273.15:5.2f}  {100 * z['shareBelow1p8']:5.1f}%")
    L += ['', 'Where the supplied heat is at 300 s (kJ/m, and share of the supplied)']
    L.append('  run       supplied   air     glass   floor   ceiling  inner wall  under the door')
    for k in RUNS:
        b = data[k]['at'][zone(k, 300)['t']]
        door = b['supplied'] - b['netH']
        air = b['air'] + b['flowWork']
        s = b['supplied']
        L.append(f"  {k:8s}  {s / 1000:7.2f}  {air / 1000:6.2f}  {b['glass'] / 1000:6.2f}  {b['floor'] / 1000:6.2f}  "
                 f"{b['ceiling'] / 1000:6.2f}   {b['innerWall'] / 1000:6.2f}      {door / 1000:6.2f}")
        L.append(f"  {'':8s}  {'':7s}  {100 * air / s:5.1f}%  {100 * b['glass'] / s:5.1f}%  {100 * b['floor'] / s:5.1f}%  "
                 f"{100 * b['ceiling'] / s:5.1f}%   {100 * b['innerWall'] / s:5.1f}%      {100 * door / s:5.1f}%")
    L += ['  air: the rise of the air\'s internal energy above 20 C plus the flow work of the air the room',
          '  pushes out as it warms (-R T0 dM); under the door: the enthalpy above 20 C carried out through',
          '  the undercut less what came in (negative: the air leaving is colder than 20 C); a wall\'s',
          '  figure is the heat its layer has taken in (negative: given up to the air). The rest is the',
          '  closure below and the air\'s kinetic energy.', '']
    L.append('The heat budget, residual over 0-300 s')
    for k in RUNS:
        b = data[k]['at'][zone(k, 300)['t']]
        L.append(f"  {k:8s}  {b['closure']:9.2f} J  = {100 * b['closure'] / b['supplied']:+.4f}% of the supplied {b['supplied']:.1f} J "
                 f"(reference flow work {b['flowWork']:.1f} J)")
    L += ['', 'Air through the openings over 0-300 s (m3/m)']
    for k in RUNS:
        b = data[k]['at'][zone(k, 300)['t']]
        L.append(f"  {k:8s}  in at the supply {b['supplyVolumeIn']:.4f}; out under the door {b['returnVolumeOut']:.4f}, "
                 f"in under the door {b['returnVolumeIn']:.4f}")
    L += ['', 'Coldest air in the room (C, cell centre x, y in m)']
    for k in RUNS:
        for t in [60, 300]:
            z = zone(k, t)
            L.append(f"  {k:8s} {t:3d} s  {z['Tmin'] - 273.15:6.2f} at {z['minX']:g}, {z['minY']:g}")
    (out / 'summary.txt').write_text('\n'.join(L) + '\n')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
