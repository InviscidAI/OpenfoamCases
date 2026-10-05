"""A generic mid-tower PC, built from public form-factor sizes -> STLs, a dimension file, previews.

No downloaded model. Every part is a box or a disc at the size the relevant standard or a
typical current part gives it, at the level of detail electronics-cooling CFD uses: the
air sees a part's outside, not its capacitors.

Coordinates, millimetres in this file, metres in the STLs:
  x  front panel (0) -> rear panel (DEPTH)
  y  floor (0) -> top panel (HEIGHT)
  z  motherboard tray (0) -> glass side panel (WIDTH)

The case is the inside of the box; its six walls are the domain boundary and are not
written as STLs. What is written:

  solids/      parts the air goes around (motherboard, I/O stack, RAM, PSU shroud, and the
               graphics card and CPU cooler as closed bodies)
  faces/       flat patches on those bodies or on the case walls where air crosses:
               fan_*         a case-fan opening (annulus, hub blocked)
               vent_*        dust-filter mesh with no fan behind it (the leak paths)
               gpu_in_*      the card's three fan openings, on its underside
               gpu_out_*     where the card's fin stack is open
               cpu_in        the tower cooler's fan face
               cpu_out       the cooler fin stack's rear face

A vent rectangle covers the whole mesh area of its panel; the fans mounted on that panel
are cut out of it in the mesh by giving fan patches priority, so one vent file serves
every fan layout.

The "viewer" layout is a viewer's build from the clip's comments and needs a slightly
different PC, so it has its own geometry, written by --viewer to geometry/viewer/ as the
files that differ from geometry/ (everything else is shared):

  - the CPU tower cooler turned round on its socket to blow toward the front: the same fin
    stack in the same place, its 120 mm fan moved from the stack's front face to its rear
    face, so cpu_in is the fan's rear face and cpu_out the stack's front face (the RAM
    stays where it was; memory slots do not move when a cooler is turned);
  - two 120 mm bottom fans, fan_bottom_front and fan_bottom_rear, in the top of the PSU
    shroud, in its front 265 mm; the rear 175 mm is left for an ATX power supply.

    python3 build_geometry.py [--layout positive|negative|even] [--out ../geometry]
    python3 build_geometry.py --viewer [--out ../geometry/viewer]
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pyvista as pv

HERE = Path(__file__).resolve().parent

# --- the case (inside dimensions) -------------------------------------------------------
DEPTH, HEIGHT, WIDTH = 440.0, 460.0, 210.0
SHROUD_TOP = 100.0          # PSU shroud: closed floor box over the full depth and width

# --- motherboard, ATX 305 x 244 mm (ATX 2.2), on 6 mm standoffs -------------------------
BOARD = dict(x0=DEPTH - 12 - 244, x1=DEPTH - 12, y0=135.0, y1=440.0, z0=6.0, z1=7.6)
IO_STACK = dict(x0=DEPTH - 30, x1=DEPTH, y0=275.0, y1=440.0, z0=7.6, z1=45.0)

# --- CPU: tower cooler, 120 mm fan in front of a 52 mm fin stack, 160 mm tall ----------
CPU_C = (318.0, 330.0)       # socket centre (x, y): ~110 mm from the board's rear and top
CPU_STACK = dict(x0=CPU_C[0] - 26, x1=CPU_C[0] + 26, y0=CPU_C[1] - 62, y1=CPU_C[1] + 62,
                 z0=12.0, z1=165.0)
CPU_FAN = dict(x0=CPU_STACK["x0"] - 25, x1=CPU_STACK["x0"], y0=CPU_C[1] - 60,
               y1=CPU_C[1] + 60, z0=45.0, z1=165.0)

# --- RAM: four DIMMs (133 mm) at 9.5 mm pitch, 44 mm tall, read as one block -----------
RAM = dict(x0=CPU_FAN["x0"] - 46, x1=CPU_FAN["x0"] - 8, y0=CPU_C[1] - 66,
           y1=CPU_C[1] + 67, z0=7.6, z1=52.0)

# --- graphics card: 300 mm long, 140 mm tall, 2.75 slots (55 mm), fans facing down -----
GPU = dict(x0=DEPTH - 300, x1=DEPTH, y0=190.0, y1=245.0, z0=12.0, z1=152.0)
GPU_FAN_D, GPU_HUB_D = 88.0, 30.0
GPU_FAN_X = [GPU["x0"] + 52, GPU["x0"] + 148, GPU["x0"] + 244]
GPU_FLOW_THROUGH = 80.0      # PCB stops this far short of the card's front end

# --- case fans --------------------------------------------------------------------------
FAN_120, FAN_140, HUB = (120.0, 114.0), (140.0, 134.0), 42.0     # frame, blade diameter
FAN_Z = 105.0                                                    # centred across the width
FRONT_FANS = [("front_low", 160.0), ("front_mid", 280.0), ("front_high", 400.0)]   # y
TOP_FANS = [("top_front", 220.0), ("top_rear", 360.0)]                             # x
REAR_FAN = ("rear", 375.0, 100.0)                                                  # y, z

# --- dust-filter mesh with nothing behind it ---------------------------------------------
VENTS = {
    "vent_front": dict(wall="x0", a=(SHROUD_TOP, HEIGHT), b=(0.0, WIDTH)),     # y, z
    "vent_top": dict(wall="y1", a=(150.0, 430.0), b=(30.0, 180.0)),            # x, z
    "vent_slots": dict(wall="x1", a=(SHROUD_TOP + 5, GPU["y0"] - 5), b=(12.0, 152.0)),
}

LAYOUTS = {
    "positive": dict(intake=["front_low", "front_mid", "front_high"], exhaust=["rear"]),
    "negative": dict(intake=["front_mid"], exhaust=["rear", "top_front", "top_rear"]),
    "even": dict(intake=["front_low", "front_mid", "front_high"],
                     exhaust=["rear", "top_front", "top_rear"]),
}


# The viewer layout's PC (see the docstring); applied by turn_for_viewer().
VIEWER_BOTTOM_FANS = [("bottom_front", 75.0), ("bottom_rear", 205.0)]               # x
VIEWER_LAYOUTS = {"viewer": dict(intake=["bottom_front", "bottom_rear", "rear", "top_rear"],
                                 exhaust=["top_front"])}
VIEWER_FILES = ["solids/cpu_cooler.stl", "faces/cpu_in.stl", "faces/cpu_out.stl",
                "faces/fan_bottom_front.stl", "faces/fan_bottom_rear.stl"]
cooler_turned = False


def turn_for_viewer():
    """Turn the cooler round and add the bottom fans; the rest of the PC is unchanged."""
    global CPU_FAN, BOTTOM_FANS, LAYOUTS, cooler_turned
    CPU_FAN = dict(CPU_FAN, x0=CPU_STACK["x1"], x1=CPU_STACK["x1"] + 25)
    BOTTOM_FANS = VIEWER_BOTTOM_FANS
    LAYOUTS = VIEWER_LAYOUTS
    cooler_turned = True


def box(d):
    return pv.Box(bounds=(d["x0"], d["x1"], d["y0"], d["y1"], d["z0"], d["z1"])).triangulate()


def annulus(centre, normal, outer, inner):
    return pv.Disc(center=centre, inner=inner / 2, outer=outer / 2, normal=normal,
                   r_res=2, c_res=72).triangulate()


def rect(wall, a, b):
    """A rectangle on one case wall; a, b are its ranges in the wall's two other axes."""
    (a0, a1), (b0, b1) = a, b
    if wall in ("x0", "x1"):
        x = 0.0 if wall == "x0" else DEPTH
        pts = [(x, a0, b0), (x, a1, b0), (x, a1, b1), (x, a0, b1)]
    else:
        y = 0.0 if wall == "y0" else HEIGHT
        pts = [(a0, y, b0), (a1, y, b0), (a1, y, b1), (a0, y, b1)]
    return pv.PolyData(np.array(pts), faces=[4, 0, 1, 2, 3]).triangulate()


def face(d, side, eps=0.0):
    """One face of a box, as its own patch; side is e.g. "z1" (the box's +z face).

    eps pushes it outward off the box, for drawing only."""
    axis, end = "xyz".index(side[0]), side[1]
    lo = [d["x0"], d["y0"], d["z0"]]
    hi = [d["x1"], d["y1"], d["z1"]]
    fixed = (lo if end == "0" else hi)[axis] + (eps if end == "1" else -eps)
    u, v = [i for i in range(3) if i != axis]
    pts = []
    for cu, cv in ((lo[u], lo[v]), (hi[u], lo[v]), (hi[u], hi[v]), (lo[u], hi[v])):
        q = [0.0, 0.0, 0.0]
        q[axis], q[u], q[v] = fixed, cu, cv
        pts.append(q)
    return pv.PolyData(np.array(pts), faces=[4, 0, 1, 2, 3]).triangulate()


def parts(eps=0.0):
    """eps > 0 lifts patches that lie on a part off its surface, for drawing only."""
    solids = {
        "motherboard": box(BOARD),
        "io_stack": box(IO_STACK),
        "ram": box(RAM),
        "psu_shroud": box(dict(x0=0, x1=DEPTH, y0=0, y1=SHROUD_TOP, z0=0, z1=WIDTH)),
        "gpu": box(GPU),
        "cpu_cooler": box(CPU_STACK).merge(box(CPU_FAN)),
    }
    faces = {}
    for name, y in FRONT_FANS:
        faces[f"fan_{name}"] = annulus((0.0, y, FAN_Z), (1, 0, 0), FAN_120[1], HUB)
    for name, x in TOP_FANS:
        faces[f"fan_{name}"] = annulus((x, HEIGHT, FAN_Z), (0, 1, 0), FAN_140[1], HUB)
    faces["fan_rear"] = annulus((DEPTH, REAR_FAN[1], REAR_FAN[2]), (1, 0, 0), FAN_120[1], HUB)
    for name, x in globals().get("BOTTOM_FANS", []):
        faces[f"fan_{name}"] = annulus((x, SHROUD_TOP, FAN_Z), (0, 1, 0), FAN_120[1], HUB)
    for name, v in VENTS.items():
        faces[name] = rect(v["wall"], v["a"], v["b"])
    zc = (GPU["z0"] + GPU["z1"]) / 2
    for i, x in enumerate(GPU_FAN_X):
        faces[f"gpu_in_{i + 1}"] = annulus((x, GPU["y0"] - eps, zc), (0, 1, 0), GPU_FAN_D, GPU_HUB_D)
    faces["gpu_out_glass_side"] = face(GPU, "z1", eps)
    faces["gpu_out_board_side"] = face(GPU, "z0", eps)
    faces["gpu_out_front_end"] = face(GPU, "x0", eps)
    ft = dict(GPU, x1=GPU["x0"] + GPU_FLOW_THROUGH)
    faces["gpu_out_flow_through"] = face(ft, "y1", eps)
    if cooler_turned:       # air in at the fan's rear face, out of the stack's front face
        faces["cpu_in"] = face(CPU_FAN, "x1", eps)
        faces["cpu_out"] = face(CPU_STACK, "x0", eps)
    else:
        faces["cpu_in"] = face(CPU_FAN, "x0", eps)
        faces["cpu_out"] = face(CPU_STACK, "x1", eps)
    return solids, faces


def render(solids, faces, layout, path, view):
    pl = pv.Plotter(off_screen=True, window_size=(1600, 1400))
    pl.set_background("white")
    shell = pv.Box(bounds=(0, DEPTH, 0, HEIGHT, 0, WIDTH))
    pl.add_mesh(shell.extract_feature_edges(), color="black", line_width=2)
    tray = pv.PolyData(np.array([(0, 0, 0), (DEPTH, 0, 0), (DEPTH, HEIGHT, 0), (0, HEIGHT, 0)],
                                float), faces=[4, 0, 1, 2, 3])
    pl.add_mesh(tray, color=(0.85, 0.86, 0.88))
    colours = {"motherboard": (0.30, 0.42, 0.34), "io_stack": (0.35, 0.35, 0.38),
               "ram": (0.25, 0.25, 0.30), "psu_shroud": (0.55, 0.56, 0.60),
               "gpu": (0.45, 0.47, 0.52), "cpu_cooler": (0.70, 0.72, 0.75)}
    for k, m in solids.items():
        pl.add_mesh(m, color=colours[k], smooth_shading=False, show_edges=False)
    used = LAYOUTS[layout]
    for k, m in faces.items():
        name = k.removeprefix("fan_")
        if k.startswith("fan_"):
            if name in used["intake"]:
                pl.add_mesh(m, color=(0.15, 0.45, 0.95))
            elif name in used["exhaust"]:
                pl.add_mesh(m, color=(0.90, 0.30, 0.15))
            else:
                pl.add_mesh(m.extract_feature_edges(), color=(0.4, 0.4, 0.4), line_width=1)
        elif k.startswith("vent_"):
            pl.add_mesh(m, color=(0.2, 0.7, 0.3), opacity=0.25)
        elif k.endswith("_in") or "_in_" in k:
            pl.add_mesh(m, color=(0.0, 0.75, 0.85))
        else:
            pl.add_mesh(m, color=(1.0, 0.65, 0.0), opacity=0.85)
    labels = {
        "graphics card (300 W)": ((GPU["x0"] + GPU["x1"]) / 2, GPU["y1"] + 5, GPU["z1"]),
        "CPU cooler (150 W)": (CPU_C[0], CPU_STACK["y1"] + 5, CPU_STACK["z1"]),
        "RAM": ((RAM["x0"] + RAM["x1"]) / 2, RAM["y1"] + 5, RAM["z1"]),
        "PSU shroud (closed)": (DEPTH / 2, SHROUD_TOP, WIDTH),
        "motherboard": (BOARD["x0"] + 20, BOARD["y1"] - 15, BOARD["z1"]),
    }
    pl.add_point_labels(np.array(list(labels.values())), list(labels.keys()), font_size=22,
                        point_size=1, shape_opacity=0.6, always_visible=True)
    c = (DEPTH / 2, HEIGHT / 2, WIDTH / 2)
    if view == "iso":
        pl.camera_position = [(-650, 750, 1150), c, (0, 1, 0)]
    elif view == "side":
        pl.camera_position = [(c[0], c[1], 2000), c, (0, 1, 0)]
        pl.camera.parallel_projection = True
        pl.camera.parallel_scale = 0.62 * HEIGHT
    elif view == "front":
        pl.camera_position = [(-2000, c[1], c[2]), c, (0, 1, 0)]
        pl.camera.parallel_projection = True
        pl.camera.parallel_scale = 0.62 * HEIGHT
    elif view == "top":
        pl.camera_position = [(c[0], 2000, c[2]), c, (0, 0, -1)]
        pl.camera.parallel_projection = True
        pl.camera.parallel_scale = 0.62 * DEPTH
    pl.add_text(f"{view}  |  {layout}: blue = intake, red = exhaust, grey ring = no fan, "
                "green = open filter mesh", font_size=12, color="black")
    pl.screenshot(str(path))
    pl.close()


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--layout", default="positive", choices=list(LAYOUTS) + list(VIEWER_LAYOUTS))
    p.add_argument("--viewer", action="store_true",
                   help="write the viewer layout's PC, only the files that differ")
    p.add_argument("--out", default=None)
    p.add_argument("--previews", default=str(HERE.parent / "previews"))
    a = p.parse_args()
    if a.viewer:
        turn_for_viewer()
        a.layout = "viewer"
    elif a.layout not in LAYOUTS:
        p.error("the viewer layout's geometry is written with --viewer")
    out = Path(a.out or HERE.parent / "geometry" / ("viewer" if a.viewer else ""))
    prev = Path(a.previews)
    solids, faces = parts()
    for sub, group in (("solids", solids), ("faces", faces)):
        (out / sub).mkdir(parents=True, exist_ok=True)
        for k, m in group.items():
            if a.viewer and f"{sub}/{k}.stl" not in VIEWER_FILES:
                continue
            m.scale(1e-3, inplace=False).save(out / sub / f"{k}.stl")
    dims = {k: v for k, v in globals().items()
            if k.isupper() and not k.startswith("VIEWER_")
            and isinstance(v, (int, float, dict, list, tuple))}
    (out / "dimensions_mm.json").write_text(json.dumps(dims, indent=1, default=list))
    prev.mkdir(parents=True, exist_ok=True)
    for layout in LAYOUTS:
        for view in ("iso", "side", "front", "top"):
            if view != "iso" and layout != a.layout:
                continue
            render(*parts(eps=0.8), layout, prev / f"{layout}_{view}.png", view)
    print(f"{len(solids)} solids, {len(faces)} faces -> {out}; previews -> {prev}")


if __name__ == "__main__":
    main()
