"""results/ from the two solved runs: python3 scripts/extract_results.py runs results

Reads each run's door monitor (postProcessing/monitor/0/history.csv, every step, written by
doorMonitor in src/doorLayer) and the wall heat flux (postProcessing/wallHeatFlux/0/
wallHeatFlux.dat) for the room's face of the wall above the door, which the monitor does not
split out. Writes

  results/<run>/history.csv  every 2.5 s: room and hall mean air, the four gross flows through
                             the two gaps, the heat they carry, the leaf's and the wall's heat,
                             the hall air's reach along the floor, the air's extremes and mass
  results/summary.txt        the means over 10-240 s and the reach, both runs side by side

Everything is per metre of door (the section is 1 m deep). Flows are gross, each direction on
its own, through the plane x = 4.0175 m across each gap; their carried heat is mass flow x c_p x
(T - 20 C), so cold air coming in carries negative heat. "Out" heat is what leaves the air
through a face (the leaf's room face loses heat to the hall at 10 C behind h = 2.33 W/m2K).
Reach is the monitor's: the farthest cell centre from the leaf's room face (x = 4 m) whose
cell spans 20 mm (or 50 mm) above the floor and holds at least 10% of the hall's air.
"""
import sys
from pathlib import Path

import numpy as np

RUNS = ('open', 'blocked')
T0, T1 = 10.0, 240.0         # the averaging window, s
EVERY = 2.5                  # history spacing, s
CP = 1005.0
ROOM_AREA = 9.6007           # m2 of the room's section, x < 4 m (from the mesh)


def load_monitor(run):
    path = run / 'postProcessing/monitor/0/history.csv'
    with open(path) as f:
        names = f.readline().strip().split(',')
    a = np.loadtxt(path, delimiter=',', skiprows=1)
    # keep a strictly increasing time (a continued run would repeat its last steps)
    keep = np.r_[True, np.diff(a[:, 0]) > 0]
    return {n: a[keep, i] for i, n in enumerate(names)}


def load_wall(run, patches=('leafRoom', 'wallRoom', 'leafHall', 'wallHall')):
    """Each patch's integrated heat flux into the air (W per m), from wallHeatFlux.dat."""
    path = run / 'postProcessing/wallHeatFlux/0/wallHeatFlux.dat'
    t = {p: [] for p in patches}
    q = {p: [] for p in patches}
    with open(path) as f:
        for line in f:
            if line.startswith('#'):
                continue
            w = line.split()
            if len(w) == 5 and w[1] in t:
                tt = float(w[0])
                if t[w[1]] and tt <= t[w[1]][-1]:
                    continue
                t[w[1]].append(tt)
                q[w[1]].append(float(w[4]))
    return {p: (np.array(t[p]), np.array(q[p])) for p in patches}


def mean(t, y, t0=T0, t1=T1):
    m = (t >= t0) & (t <= t1)
    return np.trapezoid(y[m], t[m]) / (t[m][-1] - t[m][0])


def first_at(t, y, level):
    i = np.flatnonzero(y >= level)
    return t[i[0]] if len(i) else None


def main(runs, out):
    runs, out = Path(runs), Path(out)
    S = {}
    for name in RUNS:
        a = load_monitor(runs / name)
        w = load_wall(runs / name)
        t = a['t']
        marks = np.arange(0, T1 + 1e-9, EVERY)
        idx = np.unique([min(np.searchsorted(t, m - 1e-9), len(t) - 1) for m in marks])
        wq = {p: np.interp(t, *w[p]) for p in w}
        cols = [
            ('t_s', t, '%.4f'),
            ('room_C', a['roomK'] - 273.15, '%.4f'),
            ('hall_C', a['hallK'] - 273.15, '%.4f'),
            ('underToRoom_lps', 1e3 * a['underToRoom_m3s'], '%.5f'),
            ('underToHall_lps', 1e3 * a['underToHall_m3s'], '%.5f'),
            ('headToHall_lps', 1e3 * a['headToHall_m3s'], '%.5f'),
            ('headToRoom_lps', 1e3 * a['headToRoom_m3s'], '%.5f'),
            ('underToRoom_W', a['underToRoom_W'], '%.4f'),
            ('underToHall_W', a['underToHall_W'], '%.4f'),
            ('headToHall_W', a['headToHall_W'], '%.4f'),
            ('headToRoom_W', a['headToRoom_W'], '%.4f'),
            ('leafRoomOut_W', a['leafRoomOut'], '%.4f'),
            ('wallRoomOut_W', -wq['wallRoom'], '%.4f'),
            ('leafHallOut_W', a['leafHallOut'], '%.4f'),
            ('reach20_m', a['reach20_m'], '%.4f'),
            ('reach50_m', a['reach50_m'], '%.4f'),
            ('Tmin_C', a['Tmin'] - 273.15, '%.4f'),
            ('Tmax_C', a['Tmax'] - 273.15, '%.4f'),
            ('mass_kg', a['mass'], '%.10f'),
        ]
        d = out / name
        d.mkdir(parents=True, exist_ok=True)
        with open(d / 'history.csv', 'w') as f:
            f.write(','.join(c[0] for c in cols) + '\n')
            for i in idx:
                f.write(','.join(fmt % v[i] for _, v, fmt in cols) + '\n')

        s = {}
        for k in ('underToRoom', 'underToHall', 'headToHall', 'headToRoom'):
            s[k + '_lps'] = 1e3 * mean(t, a[k + '_m3s'])
            s[k + '_W'] = mean(t, a[k + '_W'])
        # heat the room's air gains from what crosses the gaps (cold in, warm out: negative)
        s['gapsIntoRoom_W'] = s['underToRoom_W'] + s['headToRoom_W'] - s['underToHall_W'] - s['headToHall_W']
        s['leafRoomOut_W'] = mean(t, a['leafRoomOut'])
        s['wallRoomOut_W'] = -mean(*w['wallRoom'])
        s['doorLoss_W'] = -s['gapsIntoRoom_W'] + s['leafRoomOut_W']
        s['underMin_lps'] = 1e3 * a['underToRoom_m3s'][(t >= T0) & (t <= T1)].min()
        s['underMax_lps'] = 1e3 * a['underToRoom_m3s'][(t >= T0) & (t <= T1)].max()
        m = t <= T1
        s['hallAirIn_m3'] = np.trapezoid(a['underToRoom_m3s'][m] + a['headToRoom_m3s'][m], t[m])
        run_reach = np.maximum.accumulate(a['reach20_m'])
        s['reach'] = {tt: (a['reach20_m'][min(np.searchsorted(t, tt - 1e-9), len(t) - 1)],
                           run_reach[min(np.searchsorted(t, tt - 1e-9), len(t) - 1)])
                      for tt in (10, 30, 60, 120, 180, 240)}
        s['reachFirst'] = {L: first_at(t, run_reach, L) for L in (0.5, 1, 2, 3, 3.9, 3.99)}
        s['massDrift'] = np.abs(a['mass'] / a['mass'][0] - 1).max()
        s['Tmin_C'] = a['Tmin'].min() - 273.15
        s['Tmax_C'] = a['Tmax'].max() - 273.15
        s['steps'] = len(t)
        s['wall_h'] = a['clock'][-1] / 3600
        s['end'] = t[-1]
        s['room_C'] = {tt: a['roomK'][min(np.searchsorted(t, tt - 1e-9), len(t) - 1)] - 273.15 for tt in (0, 240)}
        s['hall_C'] = {tt: a['hallK'][min(np.searchsorted(t, tt - 1e-9), len(t) - 1)] - 273.15 for tt in (0, 240)}
        S[name] = s

    o, b = S['open'], S['blocked']
    L = []
    p = L.append
    p('doorGapExcluder: a 10 mm undercut and a 3 mm head gap between a room at 20 C and a hall at')
    p('10 C on a 0 C day, open and blocked with a draught excluder; 2-D section, per metre of door.')
    p('From scripts/extract_results.py on runs/open and runs/blocked.')
    p('')
    p('Means over %g-%g s                                   open      blocked' % (T0, T1))
    p('  undercut, into the room (l/s per m)            %8.3f   %8.3f' % (o['underToRoom_lps'], b['underToRoom_lps']))
    p('  undercut, into the hall (l/s per m)            %8.3f   %8.3f' % (o['underToHall_lps'], b['underToHall_lps']))
    p('  head gap, into the hall (l/s per m)            %8.3f   %8.3f' % (o['headToHall_lps'], b['headToHall_lps']))
    p('  head gap, into the room (l/s per m)            %8.3f   %8.3f' % (o['headToRoom_lps'], b['headToRoom_lps']))
    p('  heat the room loses through the gaps (W per m) %8.2f   %8.2f' % (-o['gapsIntoRoom_W'], -b['gapsIntoRoom_W']))
    p('  heat the room loses through the leaf (W per m) %8.2f   %8.2f' % (o['leafRoomOut_W'], b['leafRoomOut_W']))
    p('  the door, gaps and leaf (W per m)              %8.2f   %8.2f' % (o['doorLoss_W'], b['doorLoss_W']))
    p('  the wall above the door (W per m)              %8.2f   %8.2f' % (o['wallRoomOut_W'], b['wallRoomOut_W']))
    p('')
    p('Open: the undercut takes %.3f-%.3f l/s per m into the room over %g-%g s; the leaf is %.0f%% of' % (
        o['underMin_lps'], o['underMax_lps'], T0, T1, 100 * o['leafRoomOut_W'] / o['doorLoss_W']))
    p('the door\'s loss. Blocked: the undercut\'s gross flow is %.2f%% of the open run\'s, a recirculation' % (
        100 * b['underToRoom_lps'] / o['underToRoom_lps']))
    p('in the stub on the hall\'s side of the excluder. Hall air into the room by %g s: %.4f m3 per m open,' % (T1, o['hallAirIn_m3']))
    p('%.2f%% of the room\'s section.' % (100 * o['hallAirIn_m3'] / ROOM_AREA))
    p('')
    p('Hall air (>= 10%) along the floor, 20 mm up, metres from the leaf, the monitor\'s cells:')
    p('  t (s)        ' + ''.join('%8g' % tt for tt in o['reach']))
    for n, s in (('open', o), ('blocked', b)):
        p('  %-8s now  ' % n + ''.join('%8.3f' % s['reach'][tt][0] for tt in s['reach']))
        p('  %-8s max  ' % n + ''.join('%8.3f' % s['reach'][tt][1] for tt in s['reach']))
    p('  open, farthest so far first passes ' + ', '.join(
        '%g m at %.2f s' % (L_, tt) for L_, tt in o['reachFirst'].items() if tt is not None))
    p('')
    for n, s in (('open', o), ('blocked', b)):
        p('%s: %d steps to %g s, %.2f h of wall time on 8 ranks; room %.3f -> %.3f C, hall %.3f -> %.3f C;' % (
            n, s['steps'], s['end'], s['wall_h'], s['room_C'][0], s['room_C'][240], s['hall_C'][0], s['hall_C'][240]))
        p('  air %.2f to %.2f C throughout; air mass within %.1e of its first step\'s.' % (s['Tmin_C'], s['Tmax_C'], s['massDrift']))
    (out / 'summary.txt').write_text('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main(*(sys.argv[1:3] if len(sys.argv) > 2 else ('runs', 'results')))
