#!/usr/bin/env python3
"""Turn the purifier's intake and outlet from walls into plain patches after snappyHexMesh.

usage: open_patches.py <run>

snappyHexMesh writes every surface as a wall (patchInfo { type wall; } in snappyHexMeshDict). The intake
and the outlet carry a flow, so they must not take the wall functions that k, omega and nut give to the
wall group. This is the edit the solved runs' mesh had, the same substitution, applied to
constant/polyMesh/boundary in place; it leaves the solved runs' boundary file byte for byte.
"""
import re, sys
from pathlib import Path

p = Path(sys.argv[1]) / 'constant/polyMesh/boundary'
b = p.read_text()
for name in ('purifierIn', 'purifierOut'):
    b, n = re.subn(r'(' + name + r'\s*\{)([^{}]+)',
                   lambda m: m[1] + re.sub(r'inGroups\s+1\s*\(wall\)\s*;', '', re.sub(r'type\s+wall;', 'type patch;', m[2])), b)
    assert n == 1, f'{name} not found in {p}'
p.write_text(b)
