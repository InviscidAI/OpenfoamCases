# A quadcopter airframe in forward flight, and which part costs the drag

A small quadcopter flies forward at 15 m/s, pitched 10 degrees nose-down. Its rotors are
left out, so what is solved is the airframe on its own: a body, four arms, four motor
cans, four hub discs and four landing legs. The case asks how much air drag the airframe
has, and how that drag splits between its parts.

One run:

    ./Allrun

It builds the airframe, meshes it, solves it steadily and prints the drag of each part
and of the whole.

## The airframe

`scripts/build_airframe.py` draws it in build123d (OpenCASCADE) and fuses it into one
watertight solid. We drew it ourselves, to round numbers for a small quad; it is not a
model of any product.

| part | what it is |
|---|---|
| body | a box 160 mm long, 100 mm wide and 50 mm tall, edges rounded 4 mm |
| arms | four round tubes 20 mm across, in an X at 45 degrees, horizontal at the body's mid-height, 180 mm of tube outboard of the body's side |
| motor cans | four vertical cylinders 28 mm across and 30 mm tall, at the arm ends |
| hubs | four discs 60 mm across and 4 mm thick, flat on top of the cans |
| legs | four rods 8 mm across, 60 mm below the body's corners |

The arm tips are 501 mm apart across the diagonal. The solid is 1137.7 cm3, and its
silhouette seen along the wind is 238.1 cm2. **There are no rotor blades.** The hubs stand
where the rotor discs would be.

Each triangle of the fused surface is given to the part whose shape it lies on, and each
part becomes its own wall patch, so the forces are split by part directly.

## The flight

- **Wind** 15 m/s, sea-level air, rho = 1.225 kg/m3, nu = 1.5e-5 m2/s. q = 137.8 Pa.
- **Attitude.** A quad tilts nose-down to fly forward. The airframe is built level and
  the wind is turned instead: in the airframe's frame it comes from ahead and 10 degrees
  above, U = (14.772, 0, -2.605) m/s.
- **Drag** is the force along that wind. The **vertical force** is the force at right
  angles to it, positive up.
- **Reynolds numbers.** 1.6e5 on the body's length. 2.0e4 on an arm's diameter, 2.8e4
  on a can's and 8.0e3 on a leg's.

## The model

- **Steady RANS**: `simpleFoam`, k-omega SST, 2000 SIMPLE iterations from a uniform
  field. Linear-upwind momentum, limited-linear k and omega.
- **Walls**: Spalding's wall function for the eddy viscosity, which covers the viscous
  sublayer and the log layer alike. That matters here because y+ runs from below 1 to
  about 80.
- **Domain**: a box 5.0 x 2.8 x 2.4 m, 1.2 m of air ahead of the arm tips and 3.4 m
  behind. The airframe blocks 0.35% of its cross-section. Free-stream conditions on all
  six faces. 0.5% free-stream turbulence.
- **Mesh**: snappyHexMesh from a 50 mm background. 1.6 to 3.1 mm cells on the airframe,
  6.25 mm cells within 25 mm of it, and 12.5 mm cells through a wake box 1.6 m long.
  Three prism layers. 1,470,365 cells in the run of record. `checkMesh` passes.

## What it finds

The run of record, on a Reynolds instance with 4 physical cores, forces averaged over
iterations 1001 to 2000:

| part | drag | +- | share | vertical | CdA | pressure |
|---|---:|---:|---:|---:|---:|---:|
| body | 0.584 N | 0.003 | 26.4% | -0.260 N | 42.4 cm2 | 98.5% |
| arms | 0.990 N | 0.010 | 44.7% | -0.210 N | 71.8 cm2 | 95.7% |
| cans | 0.288 N | 0.002 | 13.0% | -0.127 N | 20.9 cm2 | 98.3% |
| hubs | 0.186 N | 0.001 | 8.4% | -0.240 N | 13.5 cm2 | 91.8% |
| legs | 0.165 N | 0.004 | 7.5% | +0.009 N | 12.0 cm2 | 98.1% |
| total | 2.213 N | 0.015 | 100.0% | -0.829 N | 160.6 cm2 | 96.6% |

The +- column is the standard deviation of the drag over the averaging window. The
pressure column is the share of each part's drag carried by pressure. The sum of the parts
is 2.213 N, the same as the total.

**The arms carry the most drag**, 44.7% of the whole. The body comes second.
The cans, hubs and legs share the rest. The arms present the largest area to the wind,
103.6 cm2 against the body's 75.9 cm2. They are also round tubes at a Reynolds number where
round tubes are draggy.

**The airframe is pushed down, not lifted.** The vertical force is a download of
0.829 N. The body carries 0.260 N of it and the hubs 0.240 N, which take the wind on
their tops. The arms carry 0.210 N.

Pressure carries 96.6% of the drag. Skin friction is a small share on so bluff a shape.

## Against a hand estimate

`scripts/hand_estimate.py` adds the drag up the textbook way. Each part is an isolated
shape in the same wind: the body a rounded box (Cd 0.90 on its silhouette), the arms,
cans and legs cylinders in crossflow (Cd 1.20 on the velocity across their axes), the
hubs a disc at 10 degrees plus its rim. No part shelters or disturbs another.

| part | hand CdA | hand drag | CFD drag | CFD / hand |
|---|---:|---:|---:|---:|
| body | 68.3 cm2 | 0.94 N | 0.584 N | 0.62 |
| arms | 63.9 cm2 | 0.88 N | 0.990 N | 1.12 |
| cans | 38.5 cm2 | 0.53 N | 0.288 N | 0.54 |
| hubs | 12.0 cm2 | 0.17 N | 0.186 N | 1.12 |
| legs | 22.0 cm2 | 0.30 N | 0.165 N | 0.54 |
| total | 204.8 cm2 | 2.82 N | 2.213 N | 0.78 |

The CFD's total is 21.6% below the hand estimate, 2.213 N against 2.82 N. The parts do not move together.
The body, cans and legs come out well under their textbook numbers, and the arms and hubs
come out above theirs. Two things push the CFD low and cannot be told apart here. Parts sit in each
other's wakes: the legs under the body, the rear arms and cans behind the front ones. And
a fully turbulent RANS model is not reliable for a cylinder at these Reynolds numbers.
There the real boundary layer is laminar when it separates, and the model has no
transition. The second is a limit on the CFD, not a reason to prefer it.

## Settling

The residuals do not fall to a converged level. The cross-stream velocity's initial
residual stalls near 1e-2, the pressure's near 6e-3. The wake behind a bluff body is not
steady, and a steady solver does not settle on one answer. What settles is the mean force.
Over iterations 1001 to 2000 the total drag has a standard deviation of 0.015 N, 0.7% of
the total. The second half of the window is 0.001 N above the first. The means over the
four quarters of the window are 2.214, 2.212, 2.216 and 2.212 N.

A first run of this setup, solved to 3000 iterations on 16 cores during the study the
case came from, gave a total drag of 2.213 N over iterations 2001 to 3000 and 2.213 N
over 1001 to 2000. Its parts: arms 1.000 N, body 0.576 N, cans 0.289 N, hubs 0.188 N,
legs 0.159 N.

## Limits, which are the part worth reading

- **No rotors.** The case is the bare airframe. A flying quad's rotors pull air down
  through the arms and over the body. That propwash changes the flow over every part, and
  probably the ranking too. These numbers are the airframe's drag in the wind it would
  meet with its rotors stopped.
- **One mesh.** No mesh study was run. A finer mesh was set up in the original study and
  never solved. The drag is not shown to be independent of the mesh.
- **Steady RANS on a bluff body.** The wake is unsteady and is solved as if it were not.
  The reported drag is a mean over a solver that keeps wandering, by about 0.7% of the
  total. It is not a time-averaged unsteady solution.
- **No transition.** The model treats every boundary layer as turbulent. The arms, cans
  and legs sit at Reynolds numbers of 8e3 to 3e4, where a real cylinder's boundary layer
  separates laminar. The drag on the round parts is the number most likely to be wrong.
- **Not validated.** There is no measurement of this airframe to compare with. The hand
  estimate is a sanity check, not a reference.
- **A drawn shape.** Sharp-edged, smooth, no cameras, batteries, wiring, antennas or
  propeller guards. Real quads differ in all of these.
- **One attitude, one speed.** 10 degrees nose-down at 15 m/s, no sideslip, still air.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3
with NumPy, PyVista, Pillow and build123d.

    cd cases/quadcopterDrag
    ./Allrun                 # one MPI rank per physical core
    NPROCS=8 ./Allrun        # or say how many

`Allrun` calls `Allmesh`, which builds the airframe into `geometry/` if it is not there,
writes the case into `run/` (`scripts/make_case.py`, where every number lives), and meshes
it with snappyHexMesh in parallel. Then it adds up the hand estimate, solves 2000
iterations, and prints the forces (`scripts/forces.py`, which also writes
`run/forces_summary.json`). It writes the horizontal section through the arms, the
vertical centreline section and the airframe's surface at the last iteration, in
`run/postProcessing/sections/`. Wall times go to `run/wallclock.txt`. On the 4-core
Reynolds instance of the run of record it took 3 h 10 min: 163 s to mesh and 11,239 s to solve. `results/` holds that run's
printed output. `./Allclean` removes the run and the built geometry.

The airframe and the case were set up by an agent for a staff study, and rebuilt here from
its scripts. The study stopped before its write-up, and its fine mesh was never solved.
