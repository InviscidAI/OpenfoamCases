#!/usr/bin/env python3
"""Start a run at rest in the still 0 C outdoor air's barometric pressure, with the breeze's
pressure on each wall, and hold the open faces at it.

    python3 wind_p.py <windward Pa> <leeward Pa>      (in the run, after setFields and
                                                       postProcess -func writeCellCentres)

Every cell's p = (1e5 + c) exp(-g y/(R T0)), T0 = 273.15 K, with the wall pressure c = windward
in the outdoor volume in front of the window wall (x < -0.24 m), leeward in the one behind the
opposite wall (x > 4.24 m), and 0 in the room and the openings. p_rgh = p + rho g y with
rho = p/(R T) of the cell's own T. The `outside` patch's p0 is set face by face the same way
from the face centres' x and y. With 0 and 0 it is windowAiring's barometric_p.py, the still runs'.

The pressure scales the barometric column rather than being added to it: a constant added to
1e5 exp(-g y/(R T0)) carries no weight of its own, leaves the column out of balance by
c g/(R T0) per metre and drives still outdoor air (README, "How the case got here").
"""
import gzip
import math
import re
import struct
import sys
from pathlib import Path

G = 9.81
R = 8314.47 / 28.96
T0 = 273.15
X_WINDWARD, X_LEEWARD = -0.24, 4.24     # the walls' outer faces
DP_WINDWARD, DP_LEEWARD = float(sys.argv[1]), float(sys.argv[2])


def read(name):
    p = Path("0/" + name)
    return p.read_bytes() if p.exists() else gzip.open(str(p) + ".gz", "rb").read()


def values(raw, chunk):
    m = re.search(rb"(?:value|internalField)\s+nonuniform\s+List<scalar>\s*(\d+)\s*\(", chunk)
    n, a = int(m[1]), m.end()
    if re.search(rb"format\s+binary", raw):
        return struct.unpack("<%dd" % n, chunk[a:a + 8 * n])
    return [float(v) for v in chunk[a:chunk.index(b")", a)].split()]


def internal_and_outside(name):
    raw = read(name)
    inside = values(raw, raw[:raw.index(b"boundaryField")])
    out = values(raw, raw[re.search(rb"\n\s*outside\s*\n\s*\{", raw).start():])
    return inside, out


def wind(x):
    return DP_WINDWARD if x < X_WINDWARD else DP_LEEWARD if x > X_LEEWARD else 0.0


x, xo = internal_and_outside("Cx")
y, yo = internal_and_outside("Cy")
traw = read("T")
T = values(traw, traw[:traw.index(b"boundaryField")])
assert len(x) == len(y) == len(T) and len(xo) == len(yo)
assert all(v < X_WINDWARD or v > X_LEEWARD for v in xo), "an outside face between the walls"

p = [(1e5 + wind(xx)) * math.exp(-G * yy / (R * T0)) for xx, yy in zip(x, y)]
p_rgh = [v + v / (R * t) * G * yy for v, t, yy in zip(p, T, y)]
p0 = [(1e5 + wind(xx)) * math.exp(-G * yy / (R * T0)) for xx, yy in zip(xo, yo)]


def nonuniform(v):
    return "nonuniform List<scalar>\n%d\n(\n" % len(v) + "\n".join(format(e, ".14g") for e in v) + "\n)"


for field, v in (("p", p), ("p_rgh", p_rgh)):
    path = Path("0/" + field)
    txt = path.read_text()
    assert txt.count("internalField uniform 1e5;") == 1
    txt = txt.replace("internalField uniform 1e5;", "internalField " + nonuniform(v) + ";")
    if field == "p_rgh":
        assert txt.count("p0 uniform 1e5;") == 1
        txt = txt.replace("p0 uniform 1e5;", "p0 " + nonuniform(p0) + ";")
    path.write_text(txt)

nw = sum(xx < X_WINDWARD for xx in xo)
nl = sum(xx > X_LEEWARD for xx in xo)
print("barometric p and p_rgh with wall pressures in", len(p), "cells;", len(xo), "outdoor faces,",
      nw, "windward (%+.2f Pa)," % DP_WINDWARD, nl, "leeward (%+.2f Pa)" % DP_LEEWARD)
