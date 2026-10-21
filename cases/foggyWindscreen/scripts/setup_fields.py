#!/usr/bin/env python3
"""Write each cell's starting pressure into 0/p, and where the surfaces the section cannot hold lie.

Run in the case directory after `postProcess -funcs "(writeCellCentres writeCellVolumes)" -time 0`. The cabin's air starts
still at physics.T0, at its barometric pressure 1e5 exp(-g y/(R T0)) (the exp form, so still air
stays still). The rear vent's p0 is written by make_case.py.
"""
import math
import re
import struct

import physics as ph

G = 9.81


def read_list(raw, start):
    m = re.compile(rb"nonuniform\s+List<scalar>\s*(\d+)\s*\(").search(raw, start)
    n = int(m.group(1))
    if re.search(rb"format\s+(\w+);", raw).group(1) == b"binary":
        v = struct.unpack(f"<{n}d", raw[m.end():m.end() + 8 * n])
    else:
        v = [float(x) for x in raw[m.end():raw.index(b")", m.end())].split()]
    assert len(v) == n
    return list(v)


cy = open("0/Cy", "rb").read()
yc = read_list(cy, cy.index(b"internalField"))
p = [ph.P_ATM * math.exp(-G * yy / (ph.R_GAS * ph.T0)) for yy in yc]
src = open("0/p").read()
old = "internalField   uniform 1e5;"
assert src.count(old) == 1
open("0/p", "w").write(src.replace(old, "internalField   nonuniform List<scalar> %d\n(\n%s\n)\n;"
                                   % (len(p), "\n".join("%.10g" % v for v in p))))
print(f"cells: {len(p)}, p {min(p):.4f} to {max(p):.4f} Pa")


# ---------------------------------------------------------------- the surfaces the section cannot hold
# Each cell of air has the cabin's two side walls beside it, 2/W m2 per m3: side glass above the
# beltline, behind the A-pillar, ahead of the C-pillar, below the door frame and off the B-pillar;
# door and pillar trim everywhere else. The cabin's contents add their heat capacity, physics.CONTENTS_X
# times the whole cabin air's, spread by volume over every cell (contents_zone all, as solved) or over
# the cells below the beltline (low).
def line(p0, p1, along, val):
    """The other coordinate on the segment p0-p1 where `along` (0 = x, 1 = y) equals val."""
    a, b = p0[along], p1[along]
    s = (val - a) / (b - a)
    return p0[1 - along] + s * (p1[1 - along] - p0[1 - along])


W0, W1, R1, RF = (0.03, 0.795), (0.98, 1.27), (2.30, 1.235), (2.58, 0.94188)   # geometry.py
cx = open("0/Cx", "rb").read()
xc = read_list(cx, cx.index(b"internalField"))
vv = open("0/V", "rb").read()
vol = read_list(vv, vv.index(b"internalField"))
info = dict(l.split() for l in open("caseInfo") if l.strip())
contents_x = float(info.get("contents_x", ph.CONTENTS_X))
contents_zone = info.get("contents_zone", ph.CONTENTS_ZONE)
glass, low = [], []
for x, y in zip(xc, yc):
    belt = line(ph.BELT[0], ph.BELT[1], 0, x)
    roof = line(W1, R1, 0, min(max(x, W1[0]), R1[0])) if x >= W1[0] else 9.0
    is_glass = (y > belt
                and x > line(W0, W1, 1, y) + ph.A_PILLAR
                and x < line(R1, RF, 1, y) - ph.C_PILLAR
                and y < roof - ph.FRAME
                and not (ph.B_PILLAR[0] <= x <= ph.B_PILLAR[1]))
    glass.append(1.0 if is_glass else 0.0)
    low.append(1.0 if (y <= belt or contents_zone == "all") else 0.0)
v_all = sum(vol)
v_low = sum(v for v, l in zip(vol, low) if l)
c_low = contents_x * ph.RHO_CP_AIR * v_all / v_low
fields = {
    "hidASg": ("[0 -1 0 0 0 0 0]", [ph.SIDE_PER_VOL * g for g in glass]),
    "hidADr": ("[0 -1 0 0 0 0 0]", [ph.SIDE_PER_VOL * (1 - g) for g in glass]),
    "hidCCt": ("[1 -1 -2 -1 0 0 0]", [c_low * l for l in low]),
}
for name, (dims, vals) in fields.items():
    with open(f"0/{name}", "w") as f:
        f.write("FoamFile { version 2.0; format ascii; class volScalarField; object %s; }\n" % name)
        f.write("dimensions %s;\ninternalField nonuniform List<scalar> %d\n(\n%s\n)\n;\n" % (dims, len(vals), "\n".join("%.8g" % v for v in vals)))
        f.write("boundaryField\n{\n    frontAndBack { type empty; }\n    \".*\" { type calculated; value uniform 0; }\n}\n")
a_glass = sum(v * g for v, g in zip(vol, glass)) / v_all
print(f"side glass against {a_glass:.1%} of the air ({ph.SIDE_PER_VOL * a_glass * v_all:.3f} m2 per m of section, "
      f"{ph.SIDE_PER_VOL * a_glass * v_all * ph.WIDTH:.2f} m2 in the car); below the beltline {v_low / v_all:.1%}; "
      f"contents {contents_x:g} x air over {contents_zone}: {c_low:.0f} J/m3K there, {c_low * v_low:.0f} J/K per m")
