#!/usr/bin/env python3
"""Write `system/blockMeshDict` for a 2-D room with two openings and fitted furniture.

The room is a 4.00 x 3.00 m plan, one cell thick with `empty` front and back. Fitted
solids are *removed from the mesh* rather than drawn over the result: the block grid is
split at every feature coordinate, blocks whose centre lies inside a solid are dropped,
and the faces newly exposed by dropping them become the `furniture` patch.

Splitting at feature coordinates is what makes the openings and the furniture land on
exact cell boundaries, so `fan` spans precisely y = 0.99..2.01 and not the nearest cell
edge to it. Everything the case claims about geometry is therefore true of the mesh.

Only floor-to-ceiling furniture appears here, and that is a constraint rather than a
preference: in a 2-D plan view every obstacle is full height by construction, which is a
fair model of a fitted wardrobe and a bad one of a bed.

Usage:  python3 scripts/generate_room_mesh.py [--case DIR] [--spacing 0.02]
"""
import argparse
from pathlib import Path

ROOM_X, ROOM_Y, THICKNESS = 4.00, 3.00, 0.02

# Floor-to-ceiling fitted solids, as (x0, x1, y0, y1) in metres.
FURNITURE = {
    "wardrobe": (0.40, 1.40, 0.00, 0.60),
    "kitchen": (0.30, 1.80, 2.50, 3.00),
    "bookcase": (3.70, 4.00, 0.20, 0.80),
}
FAN_Y = (0.99, 2.01)        # opening in the x = 0 wall
VENT_X = (2.90, 3.92)       # opening in the y = 3 wall

# Every coordinate any feature starts or ends on, so features land on cell boundaries.
XS = [0.0, 0.30, 0.40, 1.40, 1.80, 2.90, 3.70, 3.92, 4.00]
YS = [0.0, 0.20, 0.60, 0.80, 0.99, 2.01, 2.50, 3.00]

PATCH_TYPE = {"fan": "patch", "vent": "patch", "walls": "wall",
              "furniture": "wall", "frontAndBack": "empty"}


def inside_solid(x: float, y: float) -> bool:
    return any(x0 < x < x1 and y0 < y < y1
               for x0, x1, y0, y1 in FURNITURE.values())


def build(spacing: float) -> str:
    nx = [max(1, round((b - a) / spacing)) for a, b in zip(XS[:-1], XS[1:])]
    ny = [max(1, round((b - a) / spacing)) for a, b in zip(YS[:-1], YS[1:])]
    zs = [0.0, THICKNESS]

    fluid = {(i, j): not inside_solid((XS[i] + XS[i + 1]) / 2, (YS[j] + YS[j + 1]) / 2)
             for j in range(len(YS) - 1) for i in range(len(XS) - 1)}

    verts: list[tuple[float, float, float]] = []
    vid: dict[tuple[int, int, int], int] = {}

    def V(i: int, j: int, k: int) -> int:
        if (i, j, k) not in vid:
            vid[(i, j, k)] = len(verts)
            verts.append((XS[i], YS[j], zs[k]))
        return vid[(i, j, k)]

    def face(ids) -> str:
        return "(" + " ".join(map(str, ids)) + ")"

    blocks: list[str] = []
    patches: dict[str, list[str]] = {k: [] for k in PATCH_TYPE}

    for (i, j), is_fluid in fluid.items():
        if not is_fluid:
            continue
        v000, v100, v110, v010 = V(i, j, 0), V(i + 1, j, 0), V(i + 1, j + 1, 0), V(i, j + 1, 0)
        v001, v101, v111, v011 = V(i, j, 1), V(i + 1, j, 1), V(i + 1, j + 1, 1), V(i, j + 1, 1)
        blocks.append(f"    hex ({v000} {v100} {v110} {v010} {v001} {v101} {v111} {v011}) "
                      f"({nx[i]} {ny[j]} 1) simpleGrading (1 1 1)")

        sides = [(-1, 0, [v000, v001, v011, v010]), (1, 0, [v100, v110, v111, v101]),
                 (0, -1, [v000, v100, v101, v001]), (0, 1, [v010, v011, v111, v110])]
        for di, dj, f in sides:
            neighbour = (i + di, j + dj)
            if fluid.get(neighbour):
                continue                                   # internal fluid-fluid face
            if neighbour in fluid:
                patch = "furniture"                        # exposed by a dropped block
            elif i == 0 and di == -1 and YS[j] >= FAN_Y[0] - 1e-12 \
                    and YS[j + 1] <= FAN_Y[1] + 1e-12:
                patch = "fan"
            elif j == len(YS) - 2 and dj == 1 and XS[i] >= VENT_X[0] - 1e-12 \
                    and XS[i + 1] <= VENT_X[1] + 1e-12:
                patch = "vent"
            else:
                patch = "walls"
            patches[patch].append(face(f))
        patches["frontAndBack"] += [face([v000, v010, v110, v100]),
                                    face([v001, v101, v111, v011])]

    def num(v: float) -> str:
        """`0` rather than `0.0`, so the written dict is byte-identical to the one the
        published results were produced from."""
        return str(int(v)) if v == int(v) and abs(v) < 1 else str(v)

    out = ("FoamFile\n{\n    format ascii;\n    class dictionary;\n"
           "    object blockMeshDict;\n}\n\nconvertToMeters 1;\nvertices\n(\n")
    out += "".join(f"    ({num(x)} {num(y)} {num(z)})\n" for x, y, z in verts)
    out += ");\nblocks\n(\n" + "\n".join(blocks) + "\n);\nedges ();\nboundary\n(\n"
    for name, typ in PATCH_TYPE.items():
        out += f"    {name}\n    {{\n        type {typ};\n        faces\n        (\n"
        out += "".join("            " + f + "\n" for f in patches[name])
        out += "        );\n    }\n"
    out += ");\nmergePatchPairs ();\n"

    print(f"fluid blocks {sum(fluid.values())} of {len(fluid)}; "
          f"cells per interval x={nx} y={ny}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--case", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--spacing", type=float, default=0.02,
                    help="nominal in-plane cell size in metres")
    a = ap.parse_args()
    target = a.case / "system" / "blockMeshDict"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build(a.spacing))
    print("wrote", target)
