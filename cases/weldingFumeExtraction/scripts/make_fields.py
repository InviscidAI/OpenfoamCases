#!/usr/bin/env python3
"""Write 0/ for one run of the welding bay, at rest when the arc strikes.

    python3 scripts/make_fields.py canopy|bench runs/<run>

Reads the finished mesh's cell centres and boundary face centres (after snappyHexMesh, the patch merge,
topoSet and the extractor patch) from OpenFOAM's writeCellCentres (scripts/centres.py), and writes U, T, p, p_rgh, rho, k,
omega, nut, alphat, fume and phi:

  internal  the air at rest at 20 C (293.15 K), p hydrostatic, 1e5 exp(-g y / (287.1 x 293.15)),
            rho = p / (R T) with R from molWeight 28.96, p_rgh = p + rho g y; k 1e-4, omega
            0.1826 (a 0.1 m mixing length), no fume; phi zero.
  open      the bay's open side (x = 5 m): pressureInletOutletVelocity, prghTotalPressure with the
            hydrostatic p0 on each face, air coming in at 20 C with no fume.
  walls, bench, the hood's or the plenum's body   no-slip and adiabatic, with wall functions.
  welder    no-slip, held at 30 C (303.15 K).
  canopyExhaust / benchExhaust   flowRateOutletVelocity, 1.701 m3/s under the canopy, 0.5556 m3/s
            from the back of the bench's plenum; p_rgh fixedFluxPressure.

The arc's 500 W and 5 mg/s are sources on the arc cell zone (constant/fvOptions and the fume's
scalarTransport in system/controlDict), not boundary conditions.
"""
import sys
from pathlib import Path

import numpy as np

from centres import centres as mesh_centres

R = 8314.46261815324 / 28.96


def hdr(obj, cls='dictionary'):
    return f'FoamFile {{version 2.0; format ascii; class {cls}; object {obj};}}\n'


def scalar_list(a):
    return 'nonuniform List<scalar>\n' + str(len(a)) + '\n(\n' + '\n'.join(f'{v:.13g}' for v in a) + '\n)'


def hydro(y):
    return 1e5 * np.exp(-9.81 * y / (287.1 * 293.15))


def main(n, c):
    c = Path(c)
    ext = 'canopyExhaust' if n == 'canopy' else 'benchExhaust'
    q = 1.701 if n == 'canopy' else .5556
    for old in ['cellLevel', 'pointLevel']:
        (c / '0' / old).unlink(missing_ok=True)
    centres, faces = mesh_centres(c)
    pnames = list(faces)

    p = hydro(centres[:, 1])
    rho = p / (R * 293.15)
    pr = p + rho * 9.81 * centres[:, 1]
    fields = {'U': ('[0 1 -1 0 0 0 0]', 'uniform (0 0 0)', 'volVectorField'),
              'T': ('[0 0 0 1 0 0 0]', 'uniform 293.15', 'volScalarField'),
              'p': ('[1 -1 -2 0 0 0 0]', scalar_list(p), 'volScalarField'),
              'p_rgh': ('[1 -1 -2 0 0 0 0]', scalar_list(pr), 'volScalarField'),
              'rho': ('[1 -3 0 0 0 0 0]', scalar_list(rho), 'volScalarField'),
              'k': ('[0 2 -2 0 0 0 0]', 'uniform .0001', 'volScalarField'),
              'omega': ('[0 0 -1 0 0 0 0]', 'uniform .1825741858', 'volScalarField'),
              'nut': ('[0 2 -1 0 0 0 0]', 'uniform 0', 'volScalarField'),
              'alphat': ('[1 -1 -1 0 0 0 0]', 'uniform 0', 'volScalarField'),
              'fume': ('[0 0 0 0 0 0 0]', 'uniform 0', 'volScalarField')}
    (c / '0').mkdir(exist_ok=True)
    for f, (dim, internal, cls) in fields.items():
        b = []
        for patch in pnames:
            iswall = patch not in ('open', ext)
            if f == 'U':
                s = ('type noSlip;' if iswall else 'type pressureInletOutletVelocity; value uniform (0 0 0);'
                     if patch == 'open' else f'type flowRateOutletVelocity; volumetricFlowRate {q}; value uniform (0 0 0);')
            elif f == 'T':
                s = ('type fixedValue; value uniform 303.15;' if patch == 'welder' else
                     'type inletOutlet; inletValue uniform 293.15; value uniform 293.15;' if patch == 'open' else 'type zeroGradient;')
            elif f == 'p_rgh':
                y = faces[patch][:, 1]
                pf = hydro(y)
                prf = pf + pf / (R * 293.15) * 9.81 * y
                s = ('type prghTotalPressure; p0 ' + scalar_list(pf) + '; value ' + scalar_list(prf) + ';' if patch == 'open'
                     else 'type fixedFluxPressure; value ' + scalar_list(prf) + ';')
            elif f in ('p', 'rho'):
                y = faces[patch][:, 1]
                s = 'type calculated; value ' + scalar_list(hydro(y) / (R * 293.15) if f == 'rho' else hydro(y)) + ';'
            elif f == 'fume':
                s = 'type inletOutlet; inletValue uniform 0; value uniform 0;' if patch == 'open' else 'type zeroGradient;'
            elif f in ('k', 'omega'):
                val = '.0001' if f == 'k' else '.1825741858'
                typ = 'kLowReWallFunction' if f == 'k' else 'omegaWallFunction'
                s = (f'type {typ}; value uniform {val};' if iswall else
                     f'type inletOutlet; inletValue uniform {val}; value uniform {val};' if patch == 'open' else 'type zeroGradient;')
            else:
                typ = 'nutkWallFunction' if f == 'nut' else 'compressible::alphatJayatillekeWallFunction'
                s = (f'type {typ}; ' + ('Prt .85; ' if f == 'alphat' else '') + 'value uniform 0;' if iswall
                     else 'type calculated; value uniform 0;')
            b.append(patch + '\n{\n' + s + '\n}')
        (c / '0' / f).write_text(hdr(f, cls) + 'dimensions ' + dim + ';\ninternalField ' + internal
                                 + ';\nboundaryField\n{\n' + '\n'.join(b) + '\n}\n')
    phi = hdr('phi', 'surfaceScalarField') + 'dimensions [1 0 -1 0 0 0 0]; internalField uniform 0; boundaryField {\n'
    for patch in pnames:
        phi += patch + ' {type calculated; value uniform 0;}\n'
    (c / '0/phi').write_text(phi + '}\n')
    print(f'{n}: {len(centres)} cells, patches {", ".join(pnames)}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
