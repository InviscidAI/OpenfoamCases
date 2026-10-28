#!/usr/bin/env python3
"""Build the light aircraft as four closed STL surfaces, with NumPy only.

    python3 scripts/build_aircraft.py

Writes geometry/{wing,fuselage,tailplane,fin}.stl and geometry/geometry.json.

Axes: x aft from the nose, y to starboard, z up. The symmetry plane is y = 0. The
aircraft is built at zero incidence; the angle of attack is set by the inflow.

The parts are separate closed solids that overlap where they join: the wing and the
tailplane run through the fuselage, and the fin's root sits inside it. snappyHexMesh
keeps only the cells outside every surface, so each part's patch is the part's own
wetted surface, and no boolean is needed.

The dimensions are those of the airframe drawn in our first study of this aircraft,
all multiplied by SCALE = 4, which turns a 2.4 m model into a 9.6 m light aircraft.
"""
from __future__ import annotations

import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
GEO = os.path.join(HERE, "..", "geometry")

SCALE = 4.0
# Fuselage: a body of revolution about the x axis.
L_FUS, R_FUS = 2.000 * SCALE, 0.120 * SCALE
X_NOSE_END, X_MID_END, R_TAIL = 0.35 * SCALE, 0.90 * SCALE, 0.030 * SCALE
# Wing: NACA 2412, straight taper, unswept quarter-chord line, no twist or dihedral.
B_WING, C_ROOT, C_TIP, X_QC_WING = 2.400 * SCALE, 0.350 * SCALE, 0.220 * SCALE, 0.800 * SCALE
# Tailplane: NACA 0012, constant chord, in the plane z = 0, no incidence.
B_TAIL, C_TAIL, X_QC_TAIL = 0.900 * SCALE, 0.180 * SCALE, 1.750 * SCALE
# Fin: NACA 0012, constant chord, trailing edge just ahead of the fuselage's end.
C_FIN, H_FIN, X_TE_FIN = 0.200 * SCALE, 0.320 * SCALE, 1.980 * SCALE

NSEC = 121      # points on each surface of an aerofoil section, LE to TE
NSPAN = 41      # stations across each half span


def naca4(code: str, n: int = NSEC):
    """NACA 4-digit section from its equations, unit chord, LE at 0, TE at 1.
    Points are offset normal to the camber line. The open trailing edge (0.25% of the
    chord) is kept and closed with a short straight edge."""
    m, p, t = int(code[0]) / 100.0, int(code[1]) / 10.0, int(code[2:]) / 100.0
    x = 0.5 * (1.0 - np.cos(np.linspace(0.0, np.pi, n)))
    yt = 5 * t * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x**2
                  + 0.2843 * x**3 - 0.1015 * x**4)
    if m == 0.0:
        yc = np.zeros_like(x)
        dyc = np.zeros_like(x)
    else:
        yc = np.where(x < p, m / p**2 * (2 * p * x - x**2),
                      m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * x - x**2))
        dyc = np.where(x < p, 2 * m / p**2 * (p - x), 2 * m / (1 - p) ** 2 * (p - x))
    th = np.arctan(dyc)
    return (x - yt * np.sin(th), yc + yt * np.cos(th),
            x + yt * np.sin(th), yc - yt * np.cos(th))


def section_check(code: str):
    """Thickness and camber measured off the generated points."""
    xu, yu, xl, yl = naca4(code, 801)
    xs = np.linspace(0.0, 1.0, 4001)
    up, lo = np.interp(xs, xu, yu), np.interp(xs, xl, yl)
    i, j = int(np.argmax(up - lo)), int(np.argmax(np.abs(0.5 * (up + lo))))
    return {"t/c": round(float(up[i] - lo[i]), 5), "x(t max)/c": round(float(xs[i]), 3),
            "camber/c": round(float(0.5 * (up[j] + lo[j])), 5),
            "x(camber max)/c": round(float(xs[j]), 3),
            "TE gap/c": round(float(yu[-1] - yl[-1]), 5)}


def ring2d(code: str):
    """The section as one closed loop: upper surface TE to LE, then lower LE to TE.
    The loop closes across the blunt trailing edge. Returns (x, y), 2N-1 points."""
    xu, yu, xl, yl = naca4(code)
    return (np.concatenate([xu[::-1], xl[1:]]), np.concatenate([yu[::-1], yl[1:]]))


def cap(n_sec: int, offset: int):
    """Triangles closing a section loop, pairing the upper and lower point at the
    same index from the leading edge, so the cap is valid for any positive thickness."""
    N = n_sec
    le = offset + N - 1
    tris = [(le, le - 1, le + 1)]
    for i in range(1, N - 1):
        u0, u1 = le - i, le - i - 1
        l0, l1 = le + i, le + i + 1
        tris += [(u0, u1, l1), (u0, l1, l0)]
    return tris


def loft(rings):
    """A closed tube through a list of (M, 3) loops, capped at both ends."""
    M = len(rings[0])
    pts = np.concatenate(rings)
    tris = []
    for s in range(len(rings) - 1):
        a, b = s * M, (s + 1) * M
        for k in range(M):
            k1 = (k + 1) % M
            tris += [(a + k, a + k1, b + k1), (a + k, b + k1, b + k)]
    tris += cap(NSEC, 0)
    tris += [t[::-1] for t in cap(NSEC, (len(rings) - 1) * M)]
    return orient(pts, np.array(tris))


def orient(pts, tris):
    """Flip every triangle if the enclosed volume comes out negative."""
    if signed_volume(pts, tris) < 0:
        tris = tris[:, ::-1]
    return pts, tris


def signed_volume(pts, tris):
    a, b, c = pts[tris[:, 0]], pts[tris[:, 1]], pts[tris[:, 2]]
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)


def area(pts, tris):
    a, b, c = pts[tris[:, 0]], pts[tris[:, 1]], pts[tris[:, 2]]
    return float(0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1).sum())


def closed_and_manifold(tris):
    """Every edge used by exactly two triangles, once in each direction."""
    e = np.concatenate([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    fwd = {tuple(x) for x in e}
    return len(fwd) == len(e) and all((b, a) in fwd for a, b in fwd)


def wing():
    rx, rz = ring2d("2412")
    rings = []
    for y in np.linspace(-B_WING / 2, B_WING / 2, 2 * NSPAN - 1):
        c = C_ROOT + (C_TIP - C_ROOT) * abs(y) / (B_WING / 2)
        x_le = X_QC_WING - 0.25 * c
        rings.append(np.column_stack([x_le + c * rx, np.full_like(rx, y), c * rz]))
    return loft(rings)


def tailplane():
    rx, rz = ring2d("0012")
    x_le = X_QC_TAIL - 0.25 * C_TAIL
    rings = [np.column_stack([x_le + C_TAIL * rx, np.full_like(rx, y), C_TAIL * rz])
             for y in np.linspace(-B_TAIL / 2, B_TAIL / 2, 2 * NSPAN - 1)]
    return loft(rings)


def fus_radius(x):
    x = np.asarray(x, dtype=float)
    r = np.full_like(x, R_FUS)
    nose, tail = x < X_NOSE_END, x >= X_MID_END
    r[nose] = R_FUS * np.sqrt(np.clip(1.0 - ((X_NOSE_END - x[nose]) / X_NOSE_END) ** 2, 0, 1))
    s = (x[tail] - X_MID_END) / (L_FUS - X_MID_END)
    r[tail] = R_TAIL + (R_FUS - R_TAIL) * 0.5 * (1.0 + np.cos(np.pi * s))
    return r


def fin():
    rx, ry = ring2d("0012")
    x_le = X_TE_FIN - C_FIN
    z_top = float(fus_radius(X_TE_FIN - 0.5 * C_FIN)) + H_FIN
    rings = [np.column_stack([x_le + C_FIN * rx, C_FIN * ry, np.full_like(rx, z)])
             for z in np.linspace(0.0, z_top, NSPAN)]
    return loft(rings), z_top


def fuselage():
    nth = 128
    beta = np.linspace(0.0, np.pi / 2, 40)[1:]
    xs = np.concatenate([X_NOSE_END * (1 - np.cos(beta)),          # clustered at the nose
                         np.linspace(X_NOSE_END, X_MID_END, 30)[1:],
                         np.linspace(X_MID_END, L_FUS, 90)[1:]])
    rs = fus_radius(xs)
    th = np.linspace(0.0, 2 * np.pi, nth, endpoint=False)
    rings = [np.column_stack([np.full(nth, x), r * np.cos(th), r * np.sin(th)])
             for x, r in zip(xs, rs)]
    pts = np.concatenate(rings + [np.array([[0.0, 0.0, 0.0], [L_FUS, 0.0, 0.0]])])
    nose, tail = len(pts) - 2, len(pts) - 1
    tris = []
    for s in range(len(rings) - 1):
        a, b = s * nth, (s + 1) * nth
        for k in range(nth):
            k1 = (k + 1) % nth
            tris += [(a + k, a + k1, b + k1), (a + k, b + k1, b + k)]
    last = (len(rings) - 1) * nth
    for k in range(nth):
        k1 = (k + 1) % nth
        tris += [(nose, k1, k), (tail, last + k, last + k1)]
    return orient(pts, np.array(tris))


def write_stl(path, name, pts, tris):
    a, b, c = pts[tris[:, 0]], pts[tris[:, 1]], pts[tris[:, 2]]
    n = np.cross(b - a, c - a)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-300)
    with open(path, "w") as f:
        f.write(f"solid {name}\n")
        for k in range(len(tris)):
            f.write(f" facet normal {n[k,0]:.6e} {n[k,1]:.6e} {n[k,2]:.6e}\n  outer loop\n")
            for p in (a[k], b[k], c[k]):
                f.write(f"   vertex {p[0]:.7f} {p[1]:.7f} {p[2]:.7f}\n")
            f.write("  endloop\n endfacet\n")
        f.write(f"endsolid {name}\n")


def main():
    os.makedirs(GEO, exist_ok=True)
    (fin_pts, fin_tris), z_fin_top = fin()
    parts = {"wing": wing(), "fuselage": fuselage(), "tailplane": tailplane(),
             "fin": (fin_pts, fin_tris)}
    report = {}
    for name, (pts, tris) in parts.items():
        ok = closed_and_manifold(tris)
        vol = signed_volume(pts, tris)
        if not ok or vol <= 0:
            raise SystemExit(f"{name}: closed and manifold = {ok}, volume = {vol}")
        write_stl(os.path.join(GEO, f"{name}.stl"), name, pts, tris)
        report[name] = {"triangles": int(len(tris)), "volume_m3": round(vol, 5),
                        "surface_area_m2 (overlaps included)": round(area(pts, tris), 4),
                        "bbox_m": [round(float(v), 4) for v in
                                   np.concatenate([pts.min(0), pts.max(0)])]}
        print(f"{name:10s} {len(tris):7d} triangles, closed, volume {vol:.4f} m3")

    S = 0.5 * (C_ROOT + C_TIP) * B_WING
    lam = C_TIP / C_ROOT
    mac = 2.0 / 3.0 * C_ROOT * (1 + lam + lam**2) / (1 + lam)
    geom = {
        "scale_from_first_study": SCALE,
        "wing_reference_area_m2": S,
        "wing_reference_area_half_m2": S / 2,
        "mean_aerodynamic_chord_m": mac,
        "span_m": B_WING,
        "aspect_ratio": B_WING**2 / S,
        "taper_ratio": lam,
        "tailplane_area_m2": B_TAIL * C_TAIL,
        "tail_arm_quarter_chords_m": X_QC_TAIL - X_QC_WING,
        "fin_top_z_m": z_fin_top,
        "fuselage_length_m": L_FUS,
        "fuselage_diameter_m": 2 * R_FUS,
        "sections": {"2412": section_check("2412"), "0012": section_check("0012")},
        "parts": report,
    }
    with open(os.path.join(GEO, "geometry.json"), "w") as f:
        json.dump(geom, f, indent=2)
    print(f"wing S = {S:.4f} m2, MAC = {mac:.4f} m, AR = {B_WING**2 / S:.3f}")
    print("NACA 2412 measured:", geom["sections"]["2412"])
    print("NACA 0012 measured:", geom["sections"]["0012"])


if __name__ == "__main__":
    main()
