# A cyclist alone, and behind a lorry

Clips of road cyclists sitting a metre behind a lorry at motorway speed get millions of
views, and the argument under them is whether the lorry pulls the rider along or only
blocks the wind. This case puts one rider on a road bike at 90 km/h three ways, and
measures the air resistance on him:

    ./Allrun alone      # the rider on his own
    ./Allrun close      # a lorry ahead, its rear doors 1.5 m in front of his front tyre
    ./Allrun far        # the same lorry 10 m ahead

All three are in the clip, with the drag on him read live from each run.

**A word on safety.** The case shows what the air does. Riding in a lorry's slipstream is
dangerous, and illegal in many places. Nothing here is advice to try it.

## The rider and the bike

The rider is built from [MakeHuman](https://github.com/makehumancommunity/makehuman)'s
assets (base mesh, targets, skeleton and skin weights), which the project releases under
CC0, the same way as the runners of [`marathonDrafting`](../marathonDrafting):
`scripts/build_runners.py` is that case's builder, and `scripts/build_rider.py` uses its
functions to pose a seated rider by our own linear blend skinning, not by the MakeHuman
application. The CC0 files are downloaded from the MakeHuman repository at commit
`a8bc2d54ff0ac92e78ff71431b1023eda42bf482`; `geometry/LICENSE.ASSETS.md` is the licence,
copied from it.

- **The rider.** A 1.75 m male in the drops: hands on the lower part of the bar, elbows
  bent 25°, cranks horizontal with the right foot forward, trunk 26° above horizontal
  from hip to shoulder, head raised to look ahead, and a simple helmet. The pose is solved
  from the bike: the hip from the saddle (buttocks pressed 15 mm into it), the ankles from
  the pedals by two-link inverse kinematics, the trunk's flexion from the elbow bend.
  Head top 1.53 m, hip joint 1.07 m, saddle top 0.956 m. Unclothed, bald, no shoes.
- **The bike.** Built in the same script from size-56 road geometry: stack 565 mm, reach
  385, head tube 73°, seat tube 73.5°, chainstay 410, bottom-bracket drop 70, fork offset
  45, 172.5 mm cranks, 700x25c tyres. The head tube is 120 mm, shorter than a real 56's
  160 mm, so the fork crown clears the tyre by 2 cm. The tubes are capsules; the wheels
  are rim-and-tyre rings without spokes, sunk 3 mm into the ground for a contact patch.
  1.66 m from the front tyre's leading point to the rear tyre's trailing point.
- Rider, helmet and frame are one closed surface (83,526 triangles, watertight, no
  self-intersections); the two wheels are separate solids that touch nothing. Frontal
  area with the wheels 0.448 m2. MakeHuman's figure is broad, so this is at the high end
  for a rider in the drops.

## The lorry

A generic European articulated lorry with no brand, built by `scripts/build_truck.py`
from these numbers:

- **16.5 m long, 2.55 m wide, 4.0 m tall**: the limits for an articulated vehicle in
  Council Directive 96/53/EC, Annex I.
- **A rear underrun bar** 0.45-0.57 m above the ground, 0.12 m in from the doors: UN
  Regulation No. 58 allows at most 450 mm of ground clearance.
- **Tyres** 385/65 R22.5 (1.072 m) singles on the trailer and 315/80 R22.5 (1.076 m) on
  the tractor, twin on the drive axle; the diameters follow from the size designations.
- **Typical values, not from a single cited source:** a 13.6 m box trailer with its deck
  at 1.20 m and the box 2.8 m tall, three axles 1.31 m apart with the rear one 3.0 m from
  the doors, landing legs, no side skirts; a 4x2 cab-over tractor with a 2.3 m cab, its
  roof deflector up to 3.95 m, a 3.7 m wheelbase, fuel tanks, and a 0.6 m gap to the
  trailer.

The body is one closed surface; the wheels are one solid per axle, overlapping their
axles and sunk 10 mm into the ground. Frontal area 9.78 m2, twenty-two times the rider's.

The STLs are not committed: `Allrun` builds them on the first run (Python 3 with NumPy,
manifold3d, trimesh and shapely; PyVista for the preview images, which are skipped
without it). From a clean copy, both scripts rebuilt all four STLs byte for byte the same
as the ones the runs were meshed from.

## The model

- **90 km/h (25 m/s)**, the highest speed a lorry's speed limiter allows in the EU
  (Directive 92/6/EEC as amended). Air at nu = 1.5e-5 m2/s.
- **Rider-fixed frame.** The rider and the lorry stand still; the air comes in from +x
  at 25 m/s and the ground is a wall moving with it, which is the same as both vehicles
  moving through still air. Everything starts at once at t = 0 and the wakes build from
  nothing. The rider's front tyre is at x = 0; the lorry's doors are at x = 1.5 m or
  10 m. The domain runs from x = -14 to 32 m, 16 m wide and 10 m tall, with symmetry
  sides and top; uniform inflow with 1% turbulence intensity and a 0.5 m length scale,
  fixed pressure at the outlet. The lorry blocks 6% of the domain's cross-section.
- **Wheels and ground.** The ground moves with the air; the wheels, the bike's and the
  lorry's, are stationary no-slip walls, neither turning nor moving with the ground.
- **Mesh.** snappyHexMesh from a 1 m background: about 1/16 m cells on the rider and the
  lorry, 1/32 m on the bike's wheels, 0.25 m in boxes around the rider's wake and the
  lorry, no prism layers, wall functions. 63,611 cells alone, 286,921 with the lorry.
  `checkMesh` passes all three. `checkMesh -allGeometry -allTopology` flags concave cells
  (3,204 alone, 17,426 close and 17,286 far, typical of snappyHexMesh's cut cells) and,
  with the lorry, 83 cells with a small determinant; no negative volumes.
- **Turbulence: k-omega SST-SAS**, `pimpleFoam`, bounded linearUpwindV for momentum,
  limitedLinear for k and omega, backward in time, Courant number 0.9 and at most 1 ms a
  step. 0-4 s of flow. The vertical centreline plane is written every 1/120 s, a
  horizontal plane at 1.15 m every 1/30 s, and the forces on the rider and the lorry every
  step.

## Results

Drag on the rider and his bike, the time mean over 2.5-4.0 s (`results/forces.txt`,
written by `scripts/forces.py`):

| | drag | against riding alone |
|---|---:|---:|
| alone | 193.6 N | |
| 1.5 m behind the doors | 2.6 N | **1.3%, about 1%** |
| 10 m behind the doors | 106.6 N | **55%** |

**Shelter, not a pull.** Just behind the doors the rider has almost no air resistance,
and 19% of the time it is slightly negative, a push of up to 1.7 N. But averaged over any
0.5 s it never falls below zero: the lowest 0.5 s mean is +0.01% of riding alone. The
lorry hides him from the wind almost completely; it does not, on average, pull him along.

**At 10 m he keeps 55%.** The near wake has closed long before him, but he rides in the
lorry's long, slow far wake, and his drag swings between 68 and 163 N.

**The near wake** behind the doors, the time-mean side plane over 2.5-4 s in the far run,
read at the box's mid-height (`results/recirculation.txt` and
`results/centreline_mean_Ux.csv`, from `scripts/recirculation.py`), closes **2.40 m**
behind the doors: X/H = 0.86 on the 2.8 m box. The close rider, 1.5 m back, sits inside it.

The lorry's own drag coefficient is 0.68 in the close run and 0.79 in the far run (on
9.78 m2; see the limits).

## Against the literature

No published measurement of a cyclist behind a lorry turned up. The nearest are behind a
car and a motorcycle, and a lorry is much larger than either, so these bound the direction
of the result, not its size.

- **Behind a car.** Blocken, Gillmeier, Malizia & van Druenen, *J. Wind Eng. Ind.
  Aerodyn.* 234 (2023) 105353, wind tunnel and CFD: in line 10 m behind a car the rider's
  drag falls about 20%. Here, 10 m behind a lorry, it falls 45%.
- **Behind a motorcycle.** Blocken, Malizia, van Druenen & Gillmeier, *Sports
  Engineering* (2020), doi:10.1007/s12283-020-00332-z: the rider keeps 52%, 77%, 88% and
  93% of his drag at 2.64, 10, 30 and 50 m. Here he keeps 55% at 10 m.
- **The lorry's near wake.** McArthur, Burton, Thompson & Sheridan, *J. Fluids Struct.*
  66 (2016) 293-314, PIV behind the Ground Transportation System model: the mean
  recirculation's saddle point at X/H = 0.88-0.895. Here 0.86. Their body is a simplified
  model lorry, not this one, and this is one line in one plane from one run.

A 9.8 m2 lorry should shelter more, and further back, than a car or a motorcycle, and it
does here. How much more is the part to doubt, on a mesh this coarse. The Blocken numbers
above are from the papers' abstracts.

## What the clip shows, and what it does not

**It shows** the vertical section through the centreline in three strips (alone, just
behind the lorry, further back) on one 0-30 m/s scale, from the moment the air starts to
move: 4 s of flow in 20 s, 5x slow motion. The rider and the lorry are drawn over the
holes they cut in the section, the lorry's wheels faded because they stand beside the
plane. Each strip carries a live readout of his air resistance as a share of riding alone,
from the run's force history; at the end of the clip they read 100%, 2% and 51%.

**It does not show** the legs pedalling, the air beside the centreline, or anything after
4 s.

## Limits, which are the part worth reading

- **A coarse mesh.** About 1/16 m on the rider and 1/32 m on the wheels, no prism layers,
  63,611 and 286,921 cells. The bike's tubes survive only in pieces. The shares of riding
  alone are what the case carries; the newtons are rough.
- **The lone rider's drag is too high.** Cd A = 0.51 m2 (Cd 1.13 on 0.448 m2), high for
  the drops: an unclothed, broad figure on a coarse mesh. And his wake is steady: at this
  resolution SST-SAS resolves no shedding behind him, and his drag stays within
  186.6-195.5 N from 0.5 s on.
- **The rider is fixed.** No pedalling, one moment of the stroke with the cranks
  horizontal, as is usual for a static rider; no clothing, hair or shoes.
- **The wheels do not turn.** Stationary walls on the bike and the lorry alike, over a
  moving ground. It adds some drag at the rider's wheels in all three runs.
- **A box lorry.** One generic tractor and box trailer, no side skirts, no load, no tail
  devices; a curtain-sider or a tanker would leave another wake.
- **The lorry sits near the inlet in the far run.** The domain is fixed to the rider, so
  the cab's front is 5.5 m from the inflow in the far run and 14 m in the close run. That
  is the likely reason the lorry's drag coefficient differs (0.79 against 0.68). The
  trailer's near wake, 10-16 m downstream of the cab, should be affected less; its length
  was measured in the far run only.
- **Four seconds of flow**, 1.5 s of it averaged. Enough for the shelter to show; not
  enough for tight means on the far run, whose drag swings with the wake.
- **One speed, two gaps, still air.** No crosswind, which moves the shelter sideways, no
  overtaking traffic, no road gradient.
- **The clip runs 5x slower than real time**, one frame per write; nothing is interpolated.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3
with NumPy, manifold3d, trimesh and shapely (PyVista too, for the previews, the plane
crop and `scripts/recirculation.py`).

    cd cases/cyclistBehindLorry
    ./Allrun far                    # or alone, close; ./Allrun --setup-only far meshes and stops
    python3 scripts/forces.py runs > results/forces.txt                  # after all three
    python3 scripts/recirculation.py runs/far results/centreline_mean_Ux.csv

`Allrun` builds the geometry into `geometry/` if it is not there (the first build
downloads about 23 MB of MakeHuman files into `~/.cache/makehuman-cc0/`), writes
`runs/<run>/` (`scripts/makeCase.py`, with `config.sh`), meshes and checks it, writes the
t = 0 planes and forces, and solves to 4 s on 5 MPI ranks; it then crops the planes to
the part around the rider (`scripts/crop_planes.py`). With all three running at once on
five cores each, the solves took 30 minutes alone, 64 minutes close and 1.9 hours far.
From a clean copy, `--setup-only` wrote all three solved runs' dictionaries, initial fields
and surfaces byte for byte, and meshed them to the same meshes, point for point. `./Allclean` removes the runs.

The case was set up by an agent and checked by us. Its own summary averaged the far run's
drag over solver steps (109.3 N, 56%); the adjustable time step makes the steps unequal,
so the numbers above are means over time.
