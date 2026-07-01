#!/usr/bin/env python3
"""Generate a pure-hex O-grid mesh for Re=3900 cylinder LES.

The x-y grid is an annular O-grid. The inner boundary is a circle of radius
0.5D and the outer boundary is the square used by Parnaudeau et al.:
Lx x Ly = 20D x 20D. The span is piD with cyclic z patches.
"""

from __future__ import annotations

import argparse
import math
from collections import defaultdict
from pathlib import Path


def foam_header(class_name: str, location: str, object_name: str) -> str:
    return f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2606                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       {class_name};
    location    "{location}";
    object      {object_name};
}}
// ************************************************************************* //
"""


def write_list(path: Path, class_name: str, object_name: str, entries: list[str]) -> None:
    with path.open("w", encoding="ascii") as f:
        f.write(foam_header(class_name, "constant/polyMesh", object_name))
        f.write(f"\n{len(entries)}\n(\n")
        f.write("\n".join(entries))
        f.write("\n)\n")


def outer_radius_to_square(theta: float, half_width: float) -> float:
    c = abs(math.cos(theta))
    s = abs(math.sin(theta))
    return half_width / max(c, s)


def radial_fraction(i: int, nr: int, stretch: float) -> float:
    if nr == 0:
        return 0.0
    eta = i / nr
    return (math.exp(stretch * eta) - 1.0) / (math.exp(stretch) - 1.0)


def point_id(i: int, j: int, k: int, ntheta: int, nz: int) -> int:
    return (i * ntheta + (j % ntheta)) * (nz + 1) + k


def face_key(face: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sorted(face))


def classify_outer_patch(x: float, y: float, half_width: float) -> str:
    tol = 1e-8
    if x > half_width - tol:
        return "outlet"
    if x < -half_width + tol:
        return "inlet"
    if y > half_width - tol:
        return "top"
    if y < -half_width + tol:
        return "bottom"
    raise RuntimeError(f"Outer face center ({x}, {y}) is not on the square boundary")


def make_mesh(case_dir: Path, ntheta: int, nr: int, nz: int, stretch: float) -> None:
    radius = 0.5
    half_width = 10.0
    span = math.pi

    mesh_dir = case_dir / "constant" / "polyMesh"
    mesh_dir.mkdir(parents=True, exist_ok=True)

    points: list[tuple[float, float, float]] = []
    for i in range(nr + 1):
        frac = radial_fraction(i, nr, stretch)
        for j in range(ntheta):
            theta = 2.0 * math.pi * j / ntheta
            r_outer = outer_radius_to_square(theta, half_width)
            r = radius + frac * (r_outer - radius)
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            for k in range(nz + 1):
                z = span * k / nz
                points.append((x, y, z))

    cells: list[tuple[int, int, int, int, int, int, int, int]] = []
    for i in range(nr):
        for j in range(ntheta):
            jp = (j + 1) % ntheta
            for k in range(nz):
                cells.append(
                    (
                        point_id(i, j, k, ntheta, nz),
                        point_id(i + 1, j, k, ntheta, nz),
                        point_id(i + 1, jp, k, ntheta, nz),
                        point_id(i, jp, k, ntheta, nz),
                        point_id(i, j, k + 1, ntheta, nz),
                        point_id(i + 1, j, k + 1, ntheta, nz),
                        point_id(i + 1, jp, k + 1, ntheta, nz),
                        point_id(i, jp, k + 1, ntheta, nz),
                    )
                )

    local_faces = (
        (0, 3, 2, 1),  # z-min
        (4, 5, 6, 7),  # z-max
        (0, 4, 7, 3),  # inner radial
        (1, 2, 6, 5),  # outer radial
        (0, 1, 5, 4),  # theta low
        (3, 7, 6, 2),  # theta high
    )

    seen: dict[tuple[int, ...], tuple[int, tuple[int, ...]]] = {}
    internal: list[tuple[tuple[int, ...], int, int]] = []
    boundary_faces: dict[str, list[tuple[tuple[int, ...], int]]] = defaultdict(list)

    for owner, cell in enumerate(cells):
        for lf in local_faces:
            face = tuple(cell[idx] for idx in lf)
            key = face_key(face)
            if key in seen:
                other_owner, other_face = seen.pop(key)
                internal.append((other_face, other_owner, owner))
                continue

            seen[key] = (owner, face)

    for key, (owner, face) in seen.items():
        cx = sum(points[p][0] for p in face) / len(face)
        cy = sum(points[p][1] for p in face) / len(face)
        cz = sum(points[p][2] for p in face) / len(face)
        r = math.hypot(cx, cy)
        if cz < 1e-10:
            patch = "front"
        elif cz > span - 1e-10:
            patch = "back"
        elif r < radius + 1e-6:
            patch = "cylinder"
        else:
            patch = classify_outer_patch(cx, cy, half_width)
        boundary_faces[patch].append((face, owner))

    faces: list[tuple[int, ...]] = []
    owners: list[int] = []
    neighbours: list[int] = []

    for face, owner, neighbour in internal:
        faces.append(face)
        owners.append(owner)
        neighbours.append(neighbour)

    patch_order = ["cylinder", "inlet", "outlet", "top", "bottom", "front", "back"]
    patch_start: dict[str, tuple[int, int]] = {}
    for patch in patch_order:
        start = len(faces)
        for face, owner in boundary_faces[patch]:
            faces.append(face)
            owners.append(owner)
        patch_start[patch] = (start, len(boundary_faces[patch]))

    write_list(
        mesh_dir / "points",
        "vectorField",
        "points",
        [f"({x:.12g} {y:.12g} {z:.12g})" for x, y, z in points],
    )
    write_list(
        mesh_dir / "faces",
        "faceList",
        "faces",
        [f"{len(face)}({ ' '.join(str(p) for p in face) })" for face in faces],
    )
    write_list(mesh_dir / "owner", "labelList", "owner", [str(o) for o in owners])
    write_list(mesh_dir / "neighbour", "labelList", "neighbour", [str(n) for n in neighbours])

    with (mesh_dir / "boundary").open("w", encoding="ascii") as f:
        f.write(foam_header("polyBoundaryMesh", "constant/polyMesh", "boundary"))
        f.write(f"\n{len(patch_order)}\n(\n")
        for patch in patch_order:
            start, count = patch_start[patch]
            if patch in {"front", "back"}:
                patch_type = "cyclic"
                neighbour = "back" if patch == "front" else "front"
                extra = f"        neighbourPatch  {neighbour};\n        transform        translational;\n        separationVector (0 0 {span if patch == 'front' else -span:.12g});\n"
            elif patch == "cylinder":
                patch_type = "wall"
                extra = ""
            else:
                patch_type = "patch"
                extra = ""
            f.write(
                f"    {patch}\n"
                "    {\n"
                f"        type            {patch_type};\n"
                f"        nFaces          {count};\n"
                f"        startFace       {start};\n"
                f"{extra}"
                "    }\n"
            )
        f.write(")\n")

    print(f"points {len(points)}")
    print(f"cells {len(cells)}")
    print(f"faces {len(faces)}")
    print(f"internalFaces {len(neighbours)}")
    for patch in patch_order:
        print(f"{patch} faces {patch_start[patch][1]}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", default=".")
    parser.add_argument("--ntheta", type=int, default=512)
    parser.add_argument("--nr", type=int, default=128)
    parser.add_argument("--nz", type=int, default=64)
    parser.add_argument("--stretch", type=float, default=2.9)
    args = parser.parse_args()
    make_mesh(Path(args.case), args.ntheta, args.nr, args.nz, args.stretch)


if __name__ == "__main__":
    main()
