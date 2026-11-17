#!/usr/bin/env python3
"""Write system/createPatchDict to merge snappyHexMesh's surface patches into named walls.

    python3 scripts/merge_patches.py canopy|bench runs/<run>

snappyHexMesh names each surface's patch after its region in snappyHexMeshDict (the table, the
legs and the plate as `bench`, the legs block, torso, helmet, neck and arms as `welder`, the hood's
or the plenum's sheets as `canopyBody` or `plenumBody`), and leaves `open` and `walls` from
blockMesh. This groups whatever patches are there into those three walls; `createPatch -overwrite`
then applies it.
"""
import re
import sys
from pathlib import Path


def hdr(obj, cls='dictionary'):
    return f'FoamFile {{version 2.0; format ascii; class {cls}; object {obj};}}\n'


def main(n, c):
    c = Path(c)
    bound = (c / 'constant/polyMesh/boundary').read_text()
    entries = re.findall(r'(\w+)\s*\{[^}]*nFaces\s+(\d+);[^}]*startFace\s+(\d+);[^}]*\}', bound)
    body = 'canopyBody' if n == 'canopy' else 'plenumBody'
    groups = {'bench': [], 'welder': [], body: []}
    for p, count, start in entries:
        if p in ('open', 'walls', 'canopyExhaust', 'benchExhaust'):
            continue
        group = (p if p in groups else 'bench' if p.startswith(('table', 'leg', 'plate')) else 'welder'
                 if p.startswith(('bodyLegs', 'torso', 'helmet', 'neck', 'rightArm', 'leftArm')) else body)
        groups[group].append(p)
    blocks = [f'{{name {p}; patchInfo {{type wall;}} constructFrom patches; patches ({" ".join(old)});}}'
              for p, old in groups.items()]
    (c / 'system/createPatchDict').write_text(hdr('createPatchDict') + 'pointSync false; patches (\n' + '\n'.join(blocks) + '\n);')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
