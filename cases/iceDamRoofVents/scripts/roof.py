"""Geometry and published inputs of the roof section, shared by the mesh, the case and the
readout. Every number is in the README's tables with its source.

x runs across the house with the ridge at x = 0; y is up from the top of the ceiling (the
insulation's underside). The mesh is one cell deep, 1 m thick in z, so a patch's flux is per
metre of house.
"""
import math

# CRREL's worked example (Tobiasson, Buska and Greatorex 2001)
W2 = 4.572            # half the 30 ft attic: the wall's outer face at x = +-W2
SLOPE = 0.25          # 3 in 12
T_OUT = 273.15 - 5.6  # 22 F
T_ROOM = 273.15 + 21.1  # 70 F
R_CEIL = 4.4          # R25 at full depth, m2K/W
SOFFIT_SLOT = 0.0152  # 7.3 in2/ft per eave = 15.2 mm2/mm
RIDGE_SLOT = 0.0304   # 14.6 in2/ft = 30.4 mm2/mm
SNOW_D, SNOW_RES = 0.24, 6.1   # m, m K/W

# other published guidance
OH = 0.3048           # 12 in overhang (Buska et al. 1998)
CH = 0.0508           # 2 in airway under the baffle (Buska et al. 1998; BASC)
HEEL = 0.1016         # 4 in standard truss heel (SBCA)
D_INS = 0.254         # R25 of loose-fill fibreglass at R2.5/in (BASC)

# layers and films (ASHRAE Fundamentals values, OSB at k = 0.13)
R_OSB, R_SHINGLE, R_FILM = 0.0111 / 0.13, 0.077, 0.107
R_SNOW = SNOW_D * SNOW_RES
R_ROOF = R_OSB + R_SHINGLE + R_SNOW + R_FILM          # deck underside to the night air
F_BASE = (R_SNOW + R_FILM) / R_ROOF                    # snow base: T_out + F_BASE (T_deck - T_out)
R_BOARD = 0.019 / 0.12                                 # soffit and fascia boards

# our choices of detail, each stated in the README
SOFFIT_Y = HEEL - SLOPE * OH - 0.144   # soffit at the bottom of a 2x6 rafter tail at the fascia
BOARD = 0.019                          # soffit board the vent slot passes through
RIDGE_TOP = 1.30                       # top of the ridge vent's slot (outlet face)
WEDGE_GAP = 0.010                      # buried: the air wedge ends where it is 10 mm high


def deck(x):
    """Height of the deck's underside."""
    return HEEL + SLOPE * (W2 - abs(x))


def x_full_vented():
    """|x| inside which the vented insulation reaches its full depth below the baffle."""
    return W2 - (D_INS + CH - HEEL) / SLOPE


def x_wedge_buried():
    """|x| of the buried attic's end wall, where the air wedge over the insulation is WEDGE_GAP high."""
    return W2 - (D_INS + WEDGE_GAP - HEEL) / SLOPE


def ins_depth(x, variant):
    """Insulation depth under a point of the insulation's upper surface (vented) or under the deck."""
    if variant == "vented":
        return min(D_INS, deck(x) - CH)
    return min(D_INS, deck(x))


def h_ceiling(depth):
    """Room (21.1 C) to the insulation's upper surface: the room film and the insulation's local R."""
    return 1.0 / (R_FILM + R_CEIL * depth / D_INS)


def polygon(variant):
    """The air region's outline as (x, y, patch of the segment from this point to the next)."""
    xr = RIDGE_SLOT / 2
    xs0, xs1 = W2 + OH / 2 - SOFFIT_SLOT / 2, W2 + OH / 2 + SOFFIT_SLOT / 2
    if variant == "vented":
        xf = x_full_vented()
        left = [
            (-xr, RIDGE_TOP, "ridgeSides"),
            (-xr, deck(xr), "deck"),
            (-(W2 + OH), deck(W2 + OH), "fascia"),
            (-(W2 + OH), SOFFIT_Y, "soffit"),
            (-xs1, SOFFIT_Y, "soffit"),
            (-xs1, SOFFIT_Y - BOARD, "soffitVent"),
            (-xs0, SOFFIT_Y - BOARD, "soffit"),
            (-xs0, SOFFIT_Y, "soffit"),
            (-W2, SOFFIT_Y, "wall"),
            (-W2, HEEL - CH, "insulation"),
            (-xf, D_INS, "insulation"),
        ]
    else:
        xw = x_wedge_buried()
        left = [
            (-xr, RIDGE_TOP, "ridgeSides"),
            (-xr, deck(xr), "deck"),
            (-xw, deck(xw), "wall"),
            (-xw, D_INS, "insulation"),
        ]
    # mirror: the right half traversed back up to the ridge; each segment keeps its patch
    right = []
    pts = left[1:]
    for i in range(len(pts) - 1, -1, -1):
        x, y, _ = pts[i]
        name_next = pts[i - 1][2] if i > 0 else "ridgeSides"
        right.append((-x, y, name_next))
    poly = left + right
    # the last point (xr, deck) runs up the slot side to (xr, RIDGE_TOP), then the outlet back to the start
    poly.append((xr, RIDGE_TOP, "ridge"))
    return poly


if __name__ == "__main__":
    print(f"R_roof {R_ROOF:.3f} m2K/W, h_deck {1 / R_ROOF:.4f}, F_base {F_BASE:.4f}, "
          f"deck underside above {T_OUT - 273.15 + (0 - (T_OUT - 273.15)) / F_BASE:.3f} C melts the base")
    print(f"vented full depth inside |x| {x_full_vented():.4f}; buried wedge ends at |x| {x_wedge_buried():.4f}")
    print(f"soffit at y {SOFFIT_Y:.4f}, ridge at y {deck(0):.4f}, slope length wall to ridge "
          f"{W2 / math.cos(math.atan(SLOPE)):.4f} m")
    for v in ("vented", "buried"):
        print(v)
        for p in polygon(v):
            print(f"  {p[0]:8.4f} {p[1]:7.4f}  {p[2]}")
