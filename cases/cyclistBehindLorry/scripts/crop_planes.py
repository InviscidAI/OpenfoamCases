#!/usr/bin/env python3
"""Crop a run's sampled planes in place to the window around the rider (rider coordinates,
metres): the side plane y = 0 to x = -8..14, z = 0..6; the top plane z = 1.15 to
x = -8..14, y = -4..4. The solver samples them over the whole domain.

    python3 scripts/crop_planes.py runs/<run>
"""
import glob
import sys
from pathlib import Path

import pyvista as pv

c = Path(sys.argv[1])
for kind, bounds in [('side', (-8, 14, -0.6, 0.6, 0, 6)), ('topPlane', (-8, 14, -4, 4, 0.65, 1.65))]:
    for f in glob.glob(str(c / 'postProcessing' / kind / '*' / '*.vtp')):
        m = pv.read(f).clip_box(bounds, invert=False).extract_surface(algorithm='dataset_surface')
        m.save(f, binary=True)
