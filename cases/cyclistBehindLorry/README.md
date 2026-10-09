# A cyclist alone, behind a lorry, and overtaken by it

Clips of road cyclists sitting a metre behind a lorry at motorway speed get millions of
views, and the argument under them is whether the lorry pulls the rider along or only
blocks the wind. This case puts one rider on a road bike at 90 km/h three ways, and
measures the air resistance on him:

    ./Allrun alone      # the rider on his own
    ./Allrun close      # a lorry ahead, its rear doors 1.5 m in front of his front tyre
    ./Allrun far        # the same lorry 10 m ahead

All three are in the clip, with the drag on him read live from each run.

A fourth run answers a viewer who felt "the initial pull and like 50ft later another one"
when big lorries pass him. It is the same lorry alone, overtaking a rider with a 1.5 m gap,
and the rider is read off the solve along his path rather than put in it:

    ./Allrun overtaking # the lorry alone in its own frame at 80 km/h

It has its own section, [Overtaken](#overtaken), with its own limits.

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

## Overtaken

**On safety.** The UK Highway Code (Rule 163) asks drivers to leave at least 1.5 m when
passing a cyclist at up to 30 mph and more at higher speeds; this pass is 1.5 m at 50 mph,
and nothing here says that is enough.

A rider at the edge of a single-carriageway road is overtaken by the same lorry, and the
case asks what the air does to him before, alongside and after: whether he is pulled
twice, about 50 ft apart, as the viewer felt.

- **The lorry** does 80 km/h (22.2 m/s), the limit for goods vehicles over 7.5 tonnes on
  single carriageways in England and Wales (gov.uk, "Speed limits").
- **The rider** rides at 20 km/h, the middle of the 15-25 km/h at which Llorca,
  Ángel-Domènech, Agustín-Gómez & García, *Safety Science* 92 (2017) 302-310,
  doi:10.1016/j.ssci.2015.11.005, recorded 2,928 overtakings on rural roads (abstract
  read). The lorry gains on him at 60 km/h.
- **The gap** is 1.5 m, from the lorry's side to the end of his handlebar, so his
  centreline is at y = -3.0 m: the lorry's half-width 1.275 m, the gap, and the
  handlebar's half-width 0.21 m. The lorry has no mirrors, which on a real lorry stand
  out about 0.25 m further.

### The rider as a probe

In the lorry's frame the lorry stands still, the air and the road come at it at 80 km/h,
and the rider moves backwards past its side at 60 km/h. Putting him in that solve would
take a mesh that moves with him. So the solve is the lorry alone, and he is a probe: the
air is sampled along his path, and what he meets is read off it.

That holds because he hardly changes the lorry's flow. His frontal area is 0.45 m2 against
the lorry's 9.78 m2, and his centreline is 1.7 m from its side; what a body does to the
air dies off within a couple of its own widths. The push ahead of the cab, the suction
along the trailer and the wake are the lorry's, at his place, whether he is there or not.

It costs the force. The air along his path is in the solve; the force on him is not, and
has to be estimated from that air (below).

### The model

- **The lorry's frame.** The lorry of the other three runs, unmoved: its doors at x = 0,
  its cab's front at x = 16.5 m. The air comes in from +x at 22.2 m/s and the ground is a
  wall moving with it; the wheels are stationary no-slip walls. The domain runs from
  x = -55 to 50 m, 30 m wide and 15 m tall, with symmetry sides and top: the inlet 33.5 m
  ahead of the cab, a blockage of 2.2%. Inflow as the other runs: 1% turbulence intensity,
  0.5 m length scale, nu = 1.5e-5 m2/s.
- **Mesh.** snappyHexMesh from a 1 m background, 0.125 m on the lorry and in a corridor
  along the rider's side (y = -4.5 to -1.5 m, up to 2 m, over his whole path), 0.25 m
  around the lorry and its wake, no prism layers, wall functions: 571,013 cells. The
  lorry's surface is half as fine as in the other runs (1/16 m). `checkMesh -meshQuality`
  flags 9 faces above its skewness warning (7.48 at worst), none above the mesh-quality
  limit of 8, and the run's log ends "Failed 1 mesh checks" for that.
- **Turbulence and time.** k-omega SST-SAS, `pimpleFoam`, as the other runs: backward in
  time, bounded linearUpwindV for momentum, Courant number 0.9. From rest to 8 s. By 4 s
  the start-up has been carried about 90 m downstream, so only 4-8 s is used: the flow
  around a lorry that has been driving for a while. Its drag coefficient over 4-8 s is
  0.650 (0.644-0.662, on 9.78 m2), against 0.68 and 0.79 in the close and far runs; a
  run diagnostic, not a validation.
- **What it writes.** Nine lines along x every 1/120 s over 4-8 s (481 writes), from x =
  -40 to 36.5 m every 5 cm: at y = -3.0 m (the 1.5 m gap), -2.25 m (0.75 m) and -4.0 m
  (2.5 m), each at z = 0.6, 1.0 and 1.3 m, his knees, hips and shoulders. Two horizontal
  planes over the whole domain, at his shoulders (1.3 m) and knees (0.6 m), for the clip.
  The lorry's forces every step. OpenFOAM's `foamDictionary` rewrote the solved
  `controlDict` to six figures, so the writes are every 0.00833333 s, not exactly 1/120 s;
  `scripts/makeOvertaking.py` writes it as solved.
- **His path.** His shoulders are 15 m ahead of the cab's front at 4 s and move back at
  60 km/h, to 35.2 m behind the doors at 8 s. At the start the air around him is still.

### The force, estimated

`scripts/overtaking_force.py` puts the rider of the other runs (`geometry/rider.stl` and
`bike_wheels.stl`) on his path and estimates the air's force on him quasi-steadily: the
force follows the air at each moment as if it were steady.

- **The air relative to him** is the solve's velocity plus 60 km/h along x. Far from the
  lorry that is his own 20 km/h headwind.
- **Over his body, not at one point.** His side silhouette, rasterised at 2.5 mm (0.72 m2
  with the bike), is cut into three height bands, one per line, with edges halfway between
  them (0.8 and 1.15 m): 60% of it in the knee band, 23% hip, 18% shoulder. Each 5 cm slice
  of a band takes the air of its line at its own x, weighted by its share of the
  silhouette. The fore-aft force weights the bands by their share of his frontal silhouette
  instead (37%, 37%, 26%).
- **The force.** Per direction, F = 0.5 rho |u_rel| u_rel CA, summed over the slices, with
  rho = 1.225 kg/m3. The drag areas are for a mannequin in the drops on a road bike, with a
  24° torso against this rider's 25.6°, from Fintelman, *Influence of cycling position and
  crosswinds on performance and aerodynamics*, PhD thesis, University of Birmingham, 2015
  (etheses.bham.ac.uk/6407):
  - frontal CA 0.34 m2: C_FX 0.61 at 0° yaw on 0.55 m2 (Table 8.1);
  - side CA 0.79 m2: C_FY 1.01 at 45° yaw gives 0.56 m2, which is CA sin 45° in this
    model (Table 8.1). His RANS at 90° gives 0.68-0.79 m2 (Table D.2), and RANS
    under-predicts the side force at 45° by 18% (p. 139);
  - vertical CA 0.36 m2: there is no published vertical drag area for a cyclist, so this is
    his plan area times 1.0, the order of a bluff body broadside on. It is an assumption.
- **The readout** in the clip, and the `shown` columns of `results/overtaking_force.csv`,
  is the mean over six writes (0.05 s of flow), updated every sixth write.

### Results

At his shoulders, 1.5 m from the lorry's side (`results/overtaking_side_wind.csv` and
`results/overtaking_summary.txt`):

- **The sideways wind** is still until the cab's front is about 8.5 m behind him. It then
  pushes him **away** from the lorry, at up to **17 km/h** as the cab's front passes him.
  From about 8 m behind the cab's front, two-fifths of the way along the trailer, it pulls
  him **towards** it, at up to **7 km/h** just behind the doors, and fades in the wake to
  under 1 km/h either way, to the end of his path 35 m behind the doors.

The air's force on him (`results/overtaking_force.csv`):

- **Before the lorry** it is 6 N backwards: his own drag, riding at 20 km/h in still air.
- **The push.** As the cab's front passes, it peaks at **21 N**: **17 N sideways away**
  from the lorry (17.3 N in a single write, 16.8 N in the readout's mean) and 12.5 N
  backwards. It stays above 14 N for 0.16 s of flow.
- **The pull.** Along the trailer to just behind its doors, it turns towards the lorry, at
  most **5 N sideways in**.
- **The wake.** It settles back to **5-6 N backwards**, slightly less than his riding drag,
  because the wake carries some air along with the lorry.

So the air pushes him once and pulls him once, not twice, and the push and the pull peak
about **16.5 m apart**: the lorry's length, 54 ft, close to the viewer's "like 50ft later".
A rider who feels the cab's push as a jolt and then the pull at the doors feels two events
about 50 ft apart, but only the second is a pull.

**No forward pull at this gap.** The force never points forwards: its fore-aft part stays
between 3.7 and 15.2 N backwards over the whole pass. At 1.5 m to the side he is outside the
near wake that sheltered the close rider of the other runs. The air the lorry drags along
there moves forwards over the road at under 6 km/h, less than a third of his own 20 km/h,
so he still rides into a headwind.

### Against the 17 N limit

Madkour, Lowry, Abdel-Rahim, Hammad, Durgesh & Paulo, *Transp. Res. Rec.* 2677(9) (2023)
340-352, doi:10.1177/03611981231159126 (abstract read), tested four vehicle types passing
a cyclist at 25, 40 and 60 mph and 2, 4 and 6 ft, in field tests, CFD and a scaled wind
tunnel, against a 17 N flipping limit taken from the literature. Their semi-trailer
exceeded it in every case except 25 mph at 6 ft.

Here the sideways push reaches that limit, 17.3 N at its peak, and does not go clearly
past it. This pass, 50 mph at 1.5 m (4.9 ft to the handlebar's end), lies between their 4
and 6 ft at 40 and 60 mph, where their semi-trailer exceeded 17 N, so the estimate agrees
with theirs in size and sits at the low side. Their abstract does not say whether the 17 N
is a sideways force or the total, or where they measured the gap from; the sideways part
is the one compared, as it is the part that would tip him over.

How much the peak sideways push depends on the assumptions
(`scripts/overtaking_sensitivity.py`, `results/overtaking_sensitivity.txt`), changing one
at a time:

| variant | sideways push | in-plane peak |
|---|---:|---:|
| the model | 17.3 N | 21.0 N |
| frontal CA 0.31 m2 (16° torso) / 0.40 m2 (more upright) | 17.3 | 20.4 / 22.5 |
| side CA 0.68 m2 (RANS at 90°) / 0.93 m2 (with RANS's 18%) | 14.9 / 20.3 | 19.3 / 23.5 |
| both areas × 0.82 (his 0.45 m2 frontal area against the mannequin's 0.55) | 14.1 | 17.1 |
| rider at 15 / 25 km/h | 14.9 / 19.8 | 17.0 / 25.9 |
| one point, his shoulders on the shoulder line | 17.8 | 21.5 |
| the three heights weighted equally | 17.4 | 21.2 |
| averaged across his width, ± 0.2 m | 17.4 | 21.1 |
| the force felt over 0.15 / 0.30 s | 16.2 / 13.8 | 20.3 / 18.3 |
| gap 0.75 m / 2.5 m (the other lines) | 29.3 / 10.0 | 32.5 / 14.4 |

- **The gap matters most.** At 2.5 m the push is about 10 N; at 0.75 m, 29 N.
- **Within the stated pass** it is 14-20 N, the side area and his own speed mattering most:
  a faster rider meets the same lorry with more headwind.
- **How the air is sampled over his body hardly matters**, 0.5 N between one point and the
  weighted bands. The vertical area moves only the vertical force, at most 1.7 N, upwards.
- **The push is brief**, 0.16 s above 14 N. Felt over 0.3 s, about the time the air takes
  to pass his 1.75 m, it falls to 14 N.

### What the clip shows, and what it does not

**It shows** the section at his shoulders seen from above, drawn in his frame: he is fixed
at the road's edge and the lorry comes up from the bottom and passes him, 4 s of flow in
20 s, coloured by the air's speed over the road, with parcels of air carried by the solved
flow. One number, the size of the air's force on him in the road's plane in whole newtons,
with an arrow for its direction, read live from `results/overtaking_force.csv`; a small
triangle shows when the vertical part is at least 1 N.

**It does not show** the force's estimate as anything other than an estimate, the knee
section, the other gaps, or the 17 N comparison.

### Limits of the overtaking run

- **The rider is not in the solve.** The air along his path is the solve's; the force is a
  model of how his body would take that air. He does not disturb the lorry's flow, and the
  lorry's flow does not meet his wake.
- **Quasi-steady.** The force follows the air instantly, with drag areas from steady flow.
  The push lasts about a quarter of a second, about as long as the air takes to pass him,
  and a body that responds more slowly feels less of it (the 0.30 s row above).
- **Borrowed drag areas.** From a mannequin on another bike, not this rider; the three
  directions independent, with no side force or lift from yaw beyond what the side area
  carries. The vertical area is an assumption.
- **A coarse mesh.** 0.125 m along his path and on the lorry, 0.25 m in most of its near
  wake, no prism layers, 9 skewed faces. One realization: no mesh study, and the wake's
  statistics are not converged.
- **One gap and one speed difference.** The 0.75 and 2.5 m lines are read from the same
  solve and give the table's gap rows; nothing else was varied. No crosswind, which would
  change the push and the suction on the two sides, a straight road, no oncoming traffic.
- **A box lorry with no mirrors and no side guards.** Real trailers in the UK and EU carry
  side guards (UN R73), which would change the air under the trailer at his legs more than
  at his shoulders.
- **The 17 N comparison** is with a limit from an abstract, whose definition is not given
  there.

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
and surfaces byte for byte, and meshed them to the same meshes, point for point.

The overtaking run:

    ./Allrun overtaking             # ./Allrun --setup-only overtaking meshes and stops
    python3 scripts/overtaking_force.py runs/overtaking > results/overtaking_summary.txt
    python3 scripts/overtaking_sensitivity.py runs/overtaking > results/overtaking_sensitivity.txt

`Allrun overtaking` builds the lorry, and the rider for the force script, if they are not
there, writes `runs/overtaking/` (`scripts/makeOvertaking.py`, with
`config_overtaking.sh`), meshes and checks it, and solves 0-8 s on 14 MPI ranks. The solve
took 33 minutes and writes about 1.5 GB, most of it the planes. The force script writes
`results/overtaking_force.csv` and `results/overtaking_side_wind.csv`, and needs PyVista
and Pillow. From a clean copy, `--setup-only overtaking` wrote the solved run's
dictionaries, initial fields and surfaces byte for byte and meshed it to the same mesh,
byte for byte; the two scripts, run on the solved run's lines, reproduced the clip's force
and wind histories to the last digit written, and every number in the sensitivity table.

`./Allclean` removes the runs.

The case was set up by an agent and checked by us. Its own summary averaged the far run's
drag over solver steps (109.3 N, 56%); the adjustable time step makes the steps unequal,
so the numbers above are means over time.
