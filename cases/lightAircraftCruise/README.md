# A light aircraft in cruise: lift and drag

A small conventional aeroplane, wing, tailplane, fin and fuselage, flying straight and
level at 45 m/s (87 knots) at sea level. The case solves the steady flow round it at
4 degrees angle of attack and at 0 degrees, and reports the lift and the drag of the whole
aircraft and of each part.

    ./Allrun            # mesh once, then 4 deg and 0 deg
    ./Allrun 2          # mesh once (or reuse it), then 2 deg

It is a check case more than a finding. Every number it prints sits next to something to
check it against: the weight a light aircraft of this size carries, the lift slope of
lifting-line theory, and a drag build-up from flat-plate friction. The lift carries a light
aircraft's weight and its slope is within 5 to 9% of theory, but its zero-lift angle is 0.75
degrees off. The drag comes out about a quarter too high, and the README says where.

## The aircraft

Our own airframe, built from NACA equations by `scripts/build_aircraft.py` with NumPy alone.
Nose at x = 0, x aft, z up. Everything is at zero incidence; the angle of attack is set by
the inflow.

| part | shape |
|---|---|
| fuselage | body of revolution, 8.0 m long, 0.96 m across; elliptical nose to 1.4 m, parallel to 3.6 m, cosine taper to a 0.24 m blunt tail |
| wing | NACA 2412, span 9.6 m, root chord 1.40 m, tip chord 0.88 m, unswept quarter-chord line at x = 3.2 m, mid-wing, no twist, no dihedral |
| tailplane | NACA 0012, span 3.6 m, chord 0.72 m, quarter chord at x = 7.0 m, in the plane z = 0, no incidence |
| fin | NACA 0012, chord 0.80 m, trailing edge at x = 7.92 m, 1.28 m above the fuselage top |

Wing area 10.944 m2, mean aerodynamic chord 1.160 m, aspect ratio 8.42, taper 0.63. The
script measures its own sections: t/c 0.1201 at 30% chord, and on the 2412 a camber of
0.0200 at 40% chord. The trailing edge is left open by 0.25% of the chord, as the equations
give it, and closed with a flat edge.

The four parts are separate closed surfaces that overlap where they join. snappyHexMesh
keeps only the air outside all of them, so each part's patch is its own wetted surface and
no boolean is needed. The junctions are as sharp as the mesh makes them; there are no
fillets.

**Where the dimensions come from.** Our first study of this airframe drew it at a
quarter of this size, a 2.4 m span, at the same 45 m/s. Its own lift there would hold up
about 45 kg at a Reynolds number of 0.87 million. That is a large model, not a light
aircraft. This case multiplies every dimension by 4. The span becomes 9.6 m and the wing
loading at 600 kg is 55 kg/m2, which puts it among two-seat light-sport aircraft. Tecnam's
P2002 Sierra is built to the 600 kg light-sport limit, with an 8.6 m span and 11.5 m2 of
wing. Our fuselage is longer than its. The proportions are the first study's, not any
type's.

## The model

- **Half model.** No sideslip, so the solve is the starboard half, with a symmetry plane
  at y = 0. Forces are doubled for the whole aircraft.
- **Flow.** 45 m/s, air at rho = 1.225 kg/m3 and nu = 1.5e-5 m2/s. Reynolds number on the
  mean aerodynamic chord 3.5 million. The inflow is U = 45 (cos a, 0, sin a);
  `scripts/flight.py` writes it, with the lift and drag directions, for each angle.
- **Domain.** x from -24 to 56 m (3 fuselage lengths ahead, 6 behind the tail), 24 m to the
  side, 24 m above and below. Free-stream conditions on every outer face, 0.1% turbulence
  intensity.
- **Turbulence: k-omega SST**, `simpleFoam`, SIMPLEC, linearUpwind for momentum,
  limitedLinear for k and omega. Fully turbulent from every leading edge. Initialised with
  `potentialFoam`, then 500 iterations.
- **Mesh.** snappyHexMesh from a 2 m background. 15.6 mm cells on the wing (74 across the
  mean chord), 31 to 16 mm on the tail surfaces, 31 mm on the fuselage, boxes of 0.5, 0.25
  and 0.125 m around the aircraft and its near wake, and 62.5 mm along the starboard tip
  vortex to 11 m. Six prism layers, the first 0.7 mm thick, growing by 1.3. Wall
  functions (Spalding). 824,628 cells on the run of record. The layers mostly grow as
  asked: on average 5.5 of 6 on the wing, 5.2 on the tailplane, 5.0 on the fin
  and 4.1 on the fuselage. Area-mean y+ is 50 on the wing, 54 on the tail surfaces and 104 on
  the fuselage.

## Results

The run of record, `./Allrun` on four cores of a Reynolds instance. Means over iterations
300 to 500, for the whole aircraft, on the wing's 10.944 m2. Dynamic pressure 1240 Pa.

| | 0 deg | 4 deg |
|---|---:|---:|
| CL | 0.2116 | 0.5600 |
| CD | 0.02249 | 0.03497 |
| L/D | 9.4 | 16.0 |
| lift | 2873 N | 7602 N |
| drag | 305 N | 475 N |

By part at 4 degrees:

| part | CL | CD | of which pressure | of which friction |
|---|---:|---:|---:|---:|
| wing | 0.4794 | 0.02100 | 0.01564 | 0.00535 |
| fuselage | 0.0626 | 0.00784 | 0.00424 | 0.00360 |
| tailplane | 0.0175 | 0.00485 | 0.00361 | 0.00125 |
| fin | 0.0005 | 0.00128 | 0.00069 | 0.00059 |
| total | 0.5600 | 0.03497 | 0.02418 | 0.01079 |

The wing carries 86% of the lift and 60% of the drag. The fuselage carries 11%. Most of
that is the wing's lift carried over onto it. The tailplane, at no incidence, lifts up at 4 degrees
(CL 0.018) and pushes down at 0 degrees (CL -0.013).

## Checks

**Lift against weight.** At 45 m/s the 4 degree lift would hold up 775 kg. A 600 kg
aircraft needs CL 0.434. On the line through the two runs that comes at 2.6 degrees. Held at
4 degrees, 600 kg flies at 39.6 m/s. Both are what a light aircraft of this size does.

**Lift slope against lifting-line theory.** `scripts/forces.py` solves Glauert's lifting-line
equation for this planform with a thin-aerofoil section (slope 2 pi per radian). It gives
0.0870 per degree for the wing alone, with a span efficiency of 0.97.

| per degree, 0 to 4 deg | slope |
|---|---:|
| lifting line, wing alone | 0.0870 |
| solve, wing and fuselage | 0.0794 |
| solve, whole aircraft | 0.0871 |

The whole aircraft matches theory to three figures, but that is partly luck. Wing and
fuselage together come out 9% below the theory. The tailplane adds 0.0077 per degree and
makes up the gap. Measured NACA 2412 sections (Abbott and von Doenhoff) have a slope of
about 0.105 per degree, a little under thin-aerofoil theory's 0.110. With that section the
same lifting-line solution gives 0.084. Against that the wing and fuselage are 5% low.

**Zero-lift angle.** Thin-aerofoil theory puts the NACA 2412's at -2.08 degrees, close to
the measured section. The solve's wing and fuselage reach zero lift at -2.83 degrees and the
whole aircraft at -2.43. So at 0 degrees the solve carries about 0.04 more CL than theory.
At 4 degrees the wing and fuselage are 2.5% above it. We did not establish why the line is
shifted.

**Drag against a build-up.** Turbulent flat-plate friction (Schlichting's fit) on each
part's wetted area as the mesh measures it, times Raymer's form factors, gives CD0 = 0.0162.
Add CL^2/(pi AR e) with the lifting-line e:

| | build-up | solve | solve high by |
|---|---:|---:|---:|
| 0 deg | 0.0179 | 0.0225 | 26% |
| 4 deg | 0.0284 | 0.0350 | 23% |

The friction is not where the excess lies. The solve's viscous drag is 0.0108 at 4 degrees,
81% of flat-plate friction on the same wetted area (0.0133). All of the excess is pressure
drag, about 0.005 to 0.007, which on a mesh this coarse is mostly numerical. The drag rise
between the two runs gives an aircraft efficiency of 0.81 (CD = CD0 + CL^2/(pi AR e) fitted
through both). That is a usual value for a light aircraft.

A complete light aircraft has a CD near 0.025 to 0.035 in cruise. This one lands in that
range, but it has no landing gear, engine, propeller, cooling, struts or gaps. A clean
airframe like it should sit lower, near the build-up. The drag here is the solve's weakest
number. Read it as about a quarter too high.

## Settling

Judged from the forces. Between iterations 300 to 400 and 400 to 500, CL moved by 1.1e-5 at
4 degrees and 6e-8 at 0 degrees, CD by less than 2e-7. A first run of the same case on another
instance was meshed separately and came out 127 cells smaller, at 824,501; parallel
snappyHexMesh does not repeat bit for bit. It was stopped at iteration 400 with CL 0.55984
and CD 0.034962 at 4 degrees. That is the run of record's 0.5600 and 0.03497 to 0.03%. It
is why the case stops at 500 iterations and not 1200.

## Limits, which are the part worth reading

- **One mesh, no refinement study.** The 0.03% above is repeatability, not mesh
  independence. The drag is about a quarter above a flat-plate build-up, and the excess is in
  the pressure drag, where a coarse mesh puts its error. A finer mesh is the first thing to
  try before quoting a drag.
- **Wall functions, fully turbulent.** The first cell's y+ averages 50 to 104 by part.
  Nothing is laminar. A real wing at Re 3.5 million keeps some laminar flow near its leading
  edge and has less friction.
- **No trim.** The tailplane has no incidence and no elevator, so the aircraft is not
  balanced in pitch. A trimmed aircraft's tailplane would push down and the wing would carry
  more. The case reports no pitching moment.
- **A clean airframe.** No propeller, slipstream, engine, cooling flow, landing gear,
  struts, fillets or control-surface gaps.
- **Two angles, attached flow.** Nothing near stall is solved. The lift slope is a two-point
  slope.
- **The zero-lift angle is off by 0.75 degrees** against theory and the measured section,
  for a reason not found.
- **Our own airframe.** Its proportions come from our first study, scaled. It is not a
  type, and its numbers compare with light aircraft only in size and weight.
- **Plain checkMesh fails one check.** It finds 445 faces with skewness up to 10.3 where the
  symmetry plane cuts through the fin. `Allrun` gates instead on snappyHexMesh's own quality
  criteria (`system/meshQualityDict`), which the mesh passes with zero faces in error.
- **A half model.** No sideslip, so no side force and nothing asymmetric in the wake.

## How it came about

The first study of this airframe, at 2.4 m span and 45 m/s, ran about 900 iterations on a
193,000-cell half model and was never written up. Its last forces were CL 0.526 and CD 0.061
at Reynolds number 0.87 million. Rebuilding it as a template, we scaled it to a light
aircraft's size, refined the wing to 74 cells across the chord, set the prism layers for
wall functions at the new Reynolds number, added the 0 degree run for the slope, and checked
every number above. The first rebuild asked `nproc` for its rank count, which on the instance
counts hardware threads, and Open MPI refused to start; `Allrun` now counts physical cores.
The 1200-iteration first solve settled by 300 and was cut to 500.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it, with MPI, and Python 3 with
NumPy.

    cd cases/lightAircraftCruise
    ./Allrun

`Allrun` builds the four STLs into `geometry/`, meshes the half model in `runs/mesh/`, checks
the mesh, and solves each angle in `runs/aoa<angle>/` on one MPI rank per physical core
(`NPROCS=n ./Allrun` to choose). On four cores of a Reynolds instance the run of record took
1 h 46 min: 7 min to mesh, 53 min at 4 degrees and 47 min at 0 degrees. The mesh is reused
when it is there, so `./Allrun 2` after a first run solves only the new angle.
`scripts/forces.py` prints the tables above and the checks into `runs/forces.txt`; it can
be run again on any set of runs. `./Allclean` removes the runs and the STLs.
