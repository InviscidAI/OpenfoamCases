#!/usr/bin/env python3
"""The cabin section: a generic compact hatchback cut lengthwise at the driver's centreline.

usage: $PYTHON geometry.py <out.json> [png]   (needs shapely)

x runs rearward from the foot of the windscreen's inner surface, y up from the cabin floor, metres.
The air is the cabin outline less the solids (the driver on the front seat, the rear passenger on
the rear seat, the steering wheel's rim and column). Every boundary segment carries the name of the
patch it belongs to, found from the primitive it lies on. The JSON holds each ring of the air
region (the outline first, then the islands) as [x, y, patch] points: the segment from point i to
point i + 1 belongs to point i's patch.

The dimensions are the README's ("The car and the morning").
"""
import json
import sys

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

# ---------------------------------------------------------------- the outline, explicit
# windscreen: inner surface from its foot at the dash to the roof's header, 27 degrees to the
# horizontal, 1.07 m along the slope
# its foot sits 15 mm above the dash top behind a short lip, so no thin wedge of air is left under it
W0, W1 = (0.03, 0.795), (0.98, 1.27)
R1, RF = (2.30, 1.235), (2.58, 0.94188)     # rear screen: top, and foot at its lip
# the defrost duct: 25 mm across, leaving the dash top at 63 degrees, rearward and up
DUCT_TOP_FRONT, DUCT_TOP_REAR = (0.056, 0.78), (0.084, 0.78)
DUCT_DIR = (0.4472, 0.8944)            # unit vector up the duct
DUCT_LEN = 0.06
db = lambda p: (round(p[0] - DUCT_LEN * DUCT_DIR[0], 6), round(p[1] - DUCT_LEN * DUCT_DIR[1], 6))
DUCT_BOT_FRONT, DUCT_BOT_REAR = db(DUCT_TOP_FRONT), db(DUCT_TOP_REAR)

OUTLINE = [
    # (point, patch of the segment that starts here)
    ((-0.30, 0.00), "trim"),           # toe board
    ((-0.10, 0.30), "trim"),           # firewall under the dash
    ((-0.05, 0.42), "trim"),           # underside of the dash, to the recirculation intake
    ((0.02, 0.428), "recirc"),         # recirculation intake: 120 mm of the dash's underside
    ((0.14, 0.442), "trim"),
    ((0.52, 0.50), "trim"),            # dash face
    ((0.60, 0.56), "trim"),
    ((0.62, 0.66), "trim"),
    ((0.58, 0.74), "trim"),
    ((0.45, 0.78), "trim"),            # dash top, forward to the duct
    ((0.30, 0.783), "trim"),
    (DUCT_TOP_REAR, "trim"),           # rear wall of the duct, down
    (DUCT_BOT_REAR, "defrost"),        # the duct's inlet face: the heater's air comes in here
    (DUCT_BOT_FRONT, "trim"),          # front wall of the duct, up
    (DUCT_TOP_FRONT, "trim"),          # dash top to the windscreen's foot
    ((0.0375, 0.78), "trim"),          # the lip below the glass, square to it, so the wall layer's
                                       # last row runs along the lip instead of fanning into the corner
    (W0, "windscreen"),
    (W1, "roof"),                      # headliner, straight to the rear screen's top
    (R1, "rearScreen"),     # rear screen down to its lip on the parcel shelf
    (RF, "trim"),                      # the lip, square to the rear screen
    ((2.536, 0.90), "trim"),           # parcel shelf, forward
    ((2.52, 0.90), "rearVent"),        # gap at the shelf into the boot and its pressure-relief vents
    ((2.40, 0.90), "trim"),
    ((2.32, 0.90), "trim"),            # rear seat back, down
    ((2.10, 0.34), "trim"),            # rear cushion, forward
    ((1.66, 0.40), "trim"),
    ((1.62, 0.33), "trim"),
    ((1.62, 0.00), "trim"),            # floor, forward
]

# ---------------------------------------------------------------- solids
cap = lambda a, b, r: LineString([a, b]).buffer(r, quad_segs=12)
circ = lambda c, r: Point(c).buffer(r, quad_segs=24)

FRONT_SEAT = unary_union([
    Polygon([(1.02, 0.0), (1.30, 0.0), (1.30, 0.26), (1.02, 0.26)]),       # pedestal and rails
    cap((0.94, 0.33), (1.30, 0.28), 0.065),                                  # cushion
    cap((1.36, 0.32), (1.55, 0.93), 0.065),                                  # backrest
    cap((1.565, 1.00), (1.585, 1.09), 0.05),                                 # headrest
    cap((1.55, 0.93), (1.565, 1.00), 0.02),                                  # headrest post
])
DRIVER = unary_union([
    cap((1.21, 0.40), (1.37, 0.80), 0.115),        # torso
    cap((1.38, 0.82), (1.40, 0.92), 0.05),         # neck
    circ((1.405, 1.005), 0.105),                   # head
    cap((1.20, 0.40), (0.78, 0.47), 0.08),         # thigh
    cap((0.78, 0.47), (0.52, 0.13), 0.055),        # shin
    cap((0.52, 0.10), (0.40, 0.17), 0.04),         # foot on the pedal
])
REAR_SEAT_EXTRA = unary_union([])
PASSENGER = unary_union([
    cap((2.05, 0.43), (2.16, 0.82), 0.11),         # torso
    cap((2.17, 0.84), (2.18, 0.93), 0.05),         # neck
    circ((2.185, 1.02), 0.10),                     # head
    cap((2.04, 0.44), (1.64, 0.49), 0.075),        # thigh
    cap((1.64, 0.49), (1.53, 0.12), 0.055),        # shin
    cap((1.53, 0.09), (1.42, 0.06), 0.035),        # foot
])
# steering wheel, 370 mm across, its plane 25 degrees back from vertical, centre ahead of the chest
WHEEL_C = (0.84, 0.80)
WHEEL_AX = (0.4226, 0.9063)
RIM_R = 0.018
RIM_TOP = (WHEEL_C[0] + 0.185 * WHEEL_AX[0], WHEEL_C[1] + 0.185 * WHEEL_AX[1])
RIM_BOT = (WHEEL_C[0] - 0.185 * WHEEL_AX[0], WHEEL_C[1] - 0.185 * WHEEL_AX[1])
WHEEL = unary_union([
    circ(RIM_TOP, RIM_R),
    circ(RIM_BOT, RIM_R),
    cap((0.60, 0.69), (0.82, 0.79), 0.03),         # column and hub, from the dash face
])
SOLIDS = {"driver": DRIVER, "passenger": PASSENGER, "trim": unary_union([FRONT_SEAT, WHEEL])}


def build():
    outline = Polygon([p for p, _ in OUTLINE])
    assert outline.is_valid, "outline self-intersects"
    solids = unary_union(list(SOLIDS.values()))
    air = outline.difference(solids)
    if air.geom_type == "MultiPolygon":
        # pockets sealed between a body and its seat (behind the driver's neck, under the rear
        # passenger's thigh) hold no moving air: they count as solid
        air = max(air.geoms, key=lambda g: g.area)
    assert air.geom_type == "Polygon", air.geom_type
    # no simplify(): it merges collinear segments of different patches (the shelf and its vent)

    segs = [(LineString([OUTLINE[i][0], OUTLINE[(i + 1) % len(OUTLINE)][0]]), OUTLINE[i][1])
            for i in range(len(OUTLINE))]
    bounds = {k: v.boundary for k, v in SOLIDS.items()}

    def label(a, b):
        m = Point((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        best, name = 1e9, None
        for s, nm in segs:
            d = s.distance(m)
            if d < best:
                best, name = d, nm
        # a solid's surface: the person primitives get the occupant's name, seats and wheel "trim"
        for nm, bd in bounds.items():
            d = bd.distance(m)
            if d < best - 1e-9:
                best, name = d, nm
        assert best < 2e-3, (a, b, best)
        return name

    rings = []
    for ring in [air.exterior] + list(air.interiors):
        pts = list(ring.coords)[:-1]
        if ring.is_ccw is False and ring is air.exterior:
            pts = pts[::-1]
        out = [[round(x, 6), round(y, 6), label(pts[i], pts[(i + 1) % len(pts)])]
               for i, (x, y) in enumerate(pts)]
        rings.append(out)
    return air, rings


def main():
    air, rings = build()
    json.dump({"rings": rings, "area_m2": air.area,
               "windscreen": [W0, W1], "duct": [DUCT_BOT_FRONT, DUCT_BOT_REAR],
               "layer": [W0, W1, R1, RF]},
              open(sys.argv[1], "w"), indent=0)
    names = {}
    for r in rings:
        for i, (x, y, n) in enumerate(r):
            x2, y2, _ = r[(i + 1) % len(r)]
            names[n] = names.get(n, 0) + ((x2 - x) ** 2 + (y2 - y) ** 2) ** 0.5
    print(f"air {air.area:.4f} m2, {len(rings)} rings, {sum(len(r) for r in rings)} points")
    for n, L in sorted(names.items()):
        print(f"  {n:11s} {L:.4f} m")
    if len(sys.argv) > 2:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        col = {"windscreen": "tab:blue", "rearScreen": "tab:cyan", "roof": "tab:gray", "trim": "k",
               "driver": "tab:red", "passenger": "tab:orange", "defrost": "tab:green",
               "recirc": "tab:purple", "rearVent": "tab:pink"}
        fig, ax = plt.subplots(figsize=(14, 7))
        for r in rings:
            for i, (x, y, n) in enumerate(r):
                x2, y2, _ = r[(i + 1) % len(r)]
                ax.plot([x, x2], [y, y2], color=col[n], lw=2.5 if n not in ("trim",) else 1)
        for n, c in col.items():
            ax.plot([], [], color=c, label=n)
        ax.legend(loc="lower right")
        ax.set_aspect("equal")
        ax.grid(alpha=0.3)
        fig.savefig(sys.argv[2], dpi=110, bbox_inches="tight")


if __name__ == "__main__":
    main()
