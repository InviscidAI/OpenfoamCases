#!/usr/bin/env python3
"""Write the face-by-face boundary values and the starting pressure into 0/, on the final mesh.

Run in the case directory after `postProcess -func writeCellCentres -time 0`, which writes 0/Cx
and 0/Cy with the face centres of every patch.

- insulation's h in 0/T: 1/(0.107 + 4.4 depth/0.254), depth from the face's x (roof.ins_depth)
- the openings' p0 in 0/p_rgh: the -5.6 C outdoor air's barometric pressure at each face's
  height, 1e5 exp(-g y/(R T)), the barometric form, which is rest for a compressible gas
  (1/(1 + g y/(R T)) is not; dryIceCauldron's README says what it did there)
- each cell's p in 0/p: the same formula at the cell's height, the air starting at -5.6 C
The gas constant is the case's, 8314.47/28.96.
"""
import math
import re
import struct
import roof

G, R = 9.81, 8314.47 / 28.96
VARIANT = open("caseInfo").read().split()[1]
OPEN = ("soffitVent", "ridge") if VARIANT == "vented" else ("ridge",)


def read_list(raw, start):
    m = re.compile(rb"nonuniform\s+List<scalar>\s*(\d+)\s*\(").search(raw, start)
    n = int(m.group(1))
    if re.search(rb"format\s+(\w+);", raw).group(1) == b"binary":
        v = struct.unpack(f"<{n}d", raw[m.end():m.end() + 8 * n])
    else:
        v = [float(x) for x in raw[m.end():raw.index(b")", m.end())].split()]
    assert len(v) == n
    return list(v)


def patch_list(raw, patch):
    i = raw.index(b"boundaryField")
    i = re.compile(rb"\n\s*" + patch.encode() + rb"\s*\n\s*\{").search(raw, i).end()
    j = raw.index(b"value", i)
    m = re.compile(rb"value\s+uniform\s+([-+.\deE]+)\s*;").match(raw, j)
    if m:
        # all faces equal: written as uniform, so the face count comes from the mesh
        b = open("constant/polyMesh/boundary").read()
        k = re.search(r"\n\s*" + patch + r"\s*\n\s*\{[^}]*nFaces\s+(\d+);", b)
        return [float(m.group(1))] * int(k.group(1))
    return read_list(raw, j)


def nonuniform(vals):
    return "nonuniform List<scalar> %d (%s)" % (len(vals), " ".join("%.10g" % v for v in vals))


cx, cy = open("0/Cx", "rb").read(), open("0/Cy", "rb").read()

# the insulation's h, face by face
x = patch_list(cx, "insulation")
d = [roof.ins_depth(xx, VARIANT) for xx in x]
h = [roof.h_ceiling(dd) for dd in d]
src = open("0/T").read()
old = "h               uniform 0.22;"
assert src.count(old) == 1
open("0/T", "w").write(src.replace(old, "h               " + nonuniform(h) + ";"))
print(f"insulation: {len(h)} faces, depth {min(d):.4f} to {max(d):.4f} m, h {min(h):.4f} to {max(h):.4f} W/m2K, "
      f"room to attic {sum(h) / len(h):.4f} W/m2K mean over faces")

# the openings' p0
src = open("0/p_rgh").read()
pat = '"(' + "|".join(OPEN) + ')" { type prghTotalPressure; rho rho; p0 uniform 1e5; value uniform 1e5; }'
assert src.count(pat) == 1
entries = []
for p in OPEN:
    y = patch_list(cy, p)
    p0 = [1e5 * math.exp(-G * yy / (R * roof.T_OUT)) for yy in y]
    entries.append(f"{p} {{ type prghTotalPressure; rho rho; p0 {nonuniform(p0)}; value uniform 1e5; }}")
    print(f"{p}: {len(y)} faces, y {min(y):.4f} to {max(y):.4f} m, p0 {min(p0):.4f} to {max(p0):.4f} Pa")
open("0/p_rgh", "w").write(src.replace(pat, "\n    ".join(entries)))

# each cell's starting p
yc = read_list(cy, cy.index(b"internalField"))
p = [1e5 * math.exp(-G * yy / (R * roof.T_OUT)) for yy in yc]
src = open("0/p").read()
old = "internalField   uniform 1e5;"
assert src.count(old) == 1
open("0/p", "w").write(src.replace(old, "internalField   nonuniform List<scalar> %d\n(\n%s\n)\n;"
                                   % (len(p), "\n".join("%.10g" % v for v in p))))
print(f"cells: {len(p)}, p {min(p):.4f} to {max(p):.4f} Pa")
