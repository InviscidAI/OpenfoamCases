#!/usr/bin/env python3
"""Turn the monitor's raw planes into one NPZ a write.

    python3 scripts/convert_planes.py runs/<run>

Reads runs/<run>/analysis/planes_raw/<plane>_<index>.bin (written with ./Allrun --planes by
src/hallMonitor/planeExporter.H) and writes runs/<run>/analysis/planes/<plane>_<index>.npz with
time_s (float64), fields (float32 [n0, n1, 4]: T in K, Ux, Uy, Uz in m/s; NaN in the racks and the
cooling units) and mask (True in air), and planes_metadata.json. Every plane is on a 0.05 m grid
from the hall's corner. Each point takes the T and U of the cell that holds it, linearly
interpolated in time between the solver's steps to the plane's exact time; t = 0 is the air at rest.
The contained hall's panels and doors have no thickness and do not show in the mask.
"""
import json
import pathlib
import sys

import numpy as np

PLANES = {
    'plan':       dict(axis_constant=2, coordinate_m=2.0, array_axes_xyz=[0, 1], shape=[313, 325], interval_s=0.125),
    'plan1m':     dict(axis_constant=2, coordinate_m=1.0, array_axes_xyz=[0, 1], shape=[313, 325], interval_s=0.5),
    'acrossMid':  dict(axis_constant=1, coordinate_m=8.1, array_axes_xyz=[0, 2], shape=[313, 65], interval_s=0.125),
    'acrossFall': dict(axis_constant=1, coordinate_m=6.8, array_axes_xyz=[0, 2], shape=[313, 65], interval_s=0.125),
    'acrossEnd':  dict(axis_constant=1, coordinate_m=2.4, array_axes_xyz=[0, 2], shape=[313, 65], interval_s=0.5),
    'alongCold':  dict(axis_constant=0, coordinate_m=5.4, array_axes_xyz=[1, 2], shape=[325, 65], interval_s=0.5),
}


def main():
    root = pathlib.Path(sys.argv[1])
    raw, out = root / 'analysis/planes_raw', root / 'analysis/planes'
    out.mkdir(parents=True, exist_ok=True)
    meta = {k: dict(v, spacing_m=0.05, origin_m=[0, 0], fields=['temperature_K', 'velocity_x_m_s', 'velocity_y_m_s', 'velocity_z_m_s'])
            for k, v in PLANES.items()}
    total = 0
    for name, m in meta.items():
        n = int(np.prod(m['shape']))
        times = []
        for f in sorted(raw.glob(name + '_*.bin')):
            buf = f.read_bytes()
            t = float(np.frombuffer(buf, '<f8', 1)[0])
            fields = np.frombuffer(buf, '<f4', 4 * n, 8).reshape(*m['shape'], 4).copy()
            mask = np.frombuffer(buf, np.uint8, n, 8 + 16 * n).reshape(m['shape']).astype(bool)
            fields[~mask] = np.nan
            np.savez_compressed(out / (f.stem + '.npz'), time_s=np.float64(t), fields=fields, mask=mask)
            times.append(t)
        if times:
            assert np.allclose(times, np.arange(len(times)) * m['interval_s'], atol=1e-8), name
        total += len(times)
        print(f'{name}: {len(times)} writes', flush=True)
    (root / 'analysis/planes_metadata.json').write_text(json.dumps(meta, indent=2))
    print(root, total, 'NPZ files')


if __name__ == '__main__':
    main()
