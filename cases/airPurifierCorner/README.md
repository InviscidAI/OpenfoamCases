# An air purifier in the corner of a bedroom, against the same purifier in the middle

Makers' and retailers' pages say an air purifier should not stand in a corner, where the air moves
least. The published work is more divided: a CFD study of 66 layouts in a meeting room (Ginestet et
al., AIVC 2024) found a corner behind a wall the worst place and the centre the best, but called the
differences across the room "weak at 5 vol/h", and Küpper et al. found the delivery rate in a 70 m³
room "largely independent of its position". Can a purifier in one corner clean the whole room? This
case fills a closed bedroom evenly with fine smoke, switches a small tower purifier on at full speed
and follows the first 20 minutes with the purifier in a corner and with the same purifier in the
middle of the room.

    ./Allrun corner     # the purifier 38 cm from both walls of a corner, 0-1200 s from rest
    ./Allrun middle     # the same purifier in the middle of the room, 0-1200 s

**The result.** The two rooms end close. At 20 minutes **81% of the smoke is gone with the purifier
in the corner and 84% with it in the middle**, where a perfectly mixed room would be at 84% (83.8%).
So the corner purifier does clean the whole room, about two minutes behind the middle one: 80% of the
room's smoke is gone at 19.3 minutes in the corner and 17.3 in the middle. The difference comes from
the corner's intake, which takes in air the purifier has just cleaned: averaged over the run it
breathes air at 0.92 of the room's mean smoke, against 1.02 for the middle one, and the rooms' own
decay agrees (a time constant of 719 s and 647 s against 658 s mixed). **The corner delivers about
92% of the purifier's rating to the room, the middle about 102%.** At the pillow of the bed on the far
side, **clean air first arrives at 1:35 from the corner and 0:36 from the middle**; half the smoke
there is gone at 8.7 and 6.9 minutes. All of this is for smoke and fine particles in a closed, still,
unheated room with no one in it. Read [What it cannot](#what-it-cannot) before any number here.

## The room and the purifier

x and z run along the floor from the corner the purifier stands in, y up. Metres.

| | value | from |
|---|---|---|
| room | 4.5 × 4.5 m, 2.4 m high, 48.6 m³; door and window closed and not modelled | ours; 20 m² is the purifier manual's rated room at 5 air changes an hour |
| bed | a solid block 1.6 × 2.0 × 0.55 m, x = 2.7-4.3, z = 2.5-4.5, its head against the far wall | ours (a double bed) |
| wardrobe | a solid block 0.6 × 2.0 × 2.0 m, x = 0-0.6, z = 2.4-4.4 | ours |
| air | 44.43 m³ once the bed, the wardrobe and the purifier are out | the mesh |
| purifier | a cylinder 22 cm across and 36 cm tall, standing on the floor | a small tower purifier's user manual (US edition), Specifications |
| intake | all round the housing, from 1 to 16 cm above the floor | measured off the manual's drawing (perforated lower housing), so ours to that accuracy |
| outlet | an upward ring on the top, 7 to 19 cm across | measured off the manual's drawing (top grille around the control panel) |
| flow | **0.0675 m³/s** in through the intake and out through the outlet, ramped from 0 over the first 2 s; about 2.75 m/s out of the ring | the manual's smoke CADR at the top speed, 143 CFM; the ramp is ours |
| corner | axis at x = z = 0.49, 38 cm clear of both walls | the manual's least clearance on all sides, 15 in / 38 cm |
| middle | axis at x = z = 2.257857, 39 cm clear of the bed's corner | 22 background cells from the corner's axis, 8 mm off the room's centre (below) |

The manual says to run the purifier at its top speed for 15-20 minutes against smoke, so the runs go
to 20 minutes. **The two runs differ only in where the purifier stands.**

**The start.** The air at rest at 20 °C, with a passive scalar C = 1 everywhere: the share of the
starting smoke left in the air. Everything leaving the outlet is clean (C = 0), which makes the CADR
the flow of clean air. With the 44.43 m³ of air, a perfectly mixed room would follow
C = exp(−t/658 s): half its smoke gone at 7.6 minutes and 16% left at 20.

## The model

- **Solver:** pimpleFoam (OpenFOAM v2512), incompressible and isothermal, ν = 1.5e-5 m²/s, no
  buoyancy, k-omega SST with wall functions, PIMPLE with 1 outer and 2 pressure correctors, Euler in
  time at **Courant 1** (steps of about 6.8 ms once the fan is up), `linearUpwind` for momentum,
  `upwind` for k and omega, p to 1e-7, a pressure reference at (4.1, 2.2, 0.5).
- **The smoke:** the `scalarTransport` function object (`smoke` in `system/controlDict`), C carried
  by the flow and diffusing with ν and ν_t/0.7 (`alphaD 1`, `alphaDt 1.43`), `limitedLinear01 1`,
  not clipped (`bounded01 false`). It follows the air, which is right for smoke and fine particles.
- **The purifier's patches:** the intake draws 0.0675 m³/s through `flowRateInletVelocity` with a
  negative flow; the outlet sends it back up at 10% turbulence intensity and a 1 cm mixing length,
  with C = 0. C at the intake and on every wall is zero gradient. Housing, bed, wardrobe and room
  walls are no-slip.
- **Mesh:** blockMesh's lattice of 56 × 30 × 56 cells (8 cm) over the room, cut by snappyHexMesh to
  the five surfaces in `constant/triSurface`, **castellated only: no snapping and no layers**, so the
  purifier and the furniture are stair-stepped. Cells halve to 4 cm on the purifier's housing and
  intake, in a 52 cm column above the purifier up to the ceiling and in a 1.2 m patch under the
  ceiling above it, and to 2 cm on the outlet and in a box over it: **98,840 cells** in the corner
  run, **99,260** in the middle one, checkMesh OK in both, the air 44.4276 m³ in each.
  The intake and outlet are made plain patches after meshing (`scripts/open_patches.py`), so the
  wall functions do not act on them.
- **The same purifier in both runs.** The middle run's purifier surfaces are the corner's, moved by
  exactly 22 background cells in x and z (`scripts/move_purifier.sh`), so both purifiers fall on the
  grid alike: 96, 60 and 362 faces on the intake, outlet and housing in both, 0.15429, 0.02421 and
  0.2042 m². That is why the middle purifier stands 8 mm off the room's centre. A first attempt at
  the exact centre, which falls on a cell boundary, gave an outlet 7% smaller than the corner's, and
  so a faster jet; it was dropped before any run finished.
- **Monitors** (all in `system/controlDict`, every 1 s): the room's volume-weighted mean, integral
  and coefficient of variation of C, the intake's flux-weighted C, the gross flow through each
  patch, and C and U at seven points: the pillow (3.5, 0.75, 4.2), 20 cm above the mattress, the far
  corner (4.2, 1.1, 4.2), near the corner purifier (0.8, 1.1, 0.8), the wardrobe's side (1.0, 1.1, 4.2),
  the door's side (4.2, 1.1, 0.3), the room's middle (2.25, 1.1, 2.25) and beside the bed low down
  (2.5, 0.2, 3.5). `smokeBounds` writes C's minimum and maximum over every cell at every time step.
- **Planes:** a vertical section along the room's diagonal from the purifier's corner to the far
  corner, which holds both purifier positions and crosses the bed, and a horizontal plane at 1.1 m,
  each with C and U, every 0.25 s to 30 s, every 1 s to 2 minutes and every 4 s to 20 minutes (481
  in all), as legacy VTK. The fields are written every 60 s, the last two kept.

## Results

`results/summary.txt`, from `scripts/extract_results.py`; each run's history every 5 s in
`results/<run>/history.csv` and the clean-air fractions every 30 s in `results/corner_vs_middle.csv`.

The clean-air fraction, 1 − C. The room is volume-weighted, the intake flux-weighted, the pillow a
single point:

| time | mixed | corner room | corner intake | corner pillow | middle room | middle intake | middle pillow |
|---|---|---|---|---|---|---|---|
| 30 s | 0.045 | 0.040 | 0.142 | 0.000 | 0.044 | 0.000 | 0.000 |
| 1 min | 0.087 | 0.078 | 0.180 | 0.000 | 0.089 | 0.037 | 0.129 |
| 2 min | 0.167 | 0.150 | 0.251 | 0.182 | 0.170 | 0.149 | 0.193 |
| 3 min | 0.239 | 0.219 | 0.300 | 0.191 | 0.244 | 0.228 | 0.272 |
| 5 min | 0.366 | 0.340 | 0.414 | 0.332 | 0.372 | 0.372 | 0.398 |
| 10 min | 0.598 | 0.562 | 0.619 | 0.585 | 0.605 | 0.597 | 0.619 |
| 15 min | 0.745 | 0.713 | 0.719 | 0.713 | 0.752 | 0.750 | 0.762 |
| **20 min** | **0.838** | **0.812** | 0.832 | 0.805 | **0.844** | 0.842 | 0.845 |

**Where the difference comes from.** The corner's jet climbs the corner, turns under the ceiling and
comes back down the walls beside it, and some of it reaches the intake within about 10 s: at 30 s
the corner's intake is 14% clean while the room is 4% clean, and the middle's intake has not yet seen
any clean air (it first does at 46 s). Over the whole run the corner's intake C is 0.916 of the
room's mean, and the middle's 1.018; the room's loss of smoke is the flow times C at the intake, so
that ratio is the share of the rated clean air the room really receives. The middle does slightly
better than a mixed room because its intake takes undiluted air for the first 45 s. The gap between
the rooms opens to 4.4 points at about 11 minutes and narrows to 3.2 at 20 because there is less smoke
left to differ over; the corner's penalty does not go away (its intake ratio is 0.914 over the last
minute).

**At the pillow** the first clean air (1%, from the 1 s readings) arrives at 1:35 from the corner and
0:36 from the middle, and the far corner at 1:42 and 0:40. Half the smoke at the pillow is gone at 8.7
and 6.9 minutes and 80% at 19.9 and 17.0. The pillow's gap is largest early, 17 points at 90 s, when
the middle's clean air has arrived and the corner's has not; from 2 minutes on it lies between 1 and
11 points, and ends at 4. It is one point in a moving flow, so its wiggles are local swings.

**Evenness.** The corner room is the less even of the two throughout: the room's standard deviation
of C peaks at 0.089 (at 79 s) against 0.060 (31 s), and ends at 0.021 against 0.008. At 20 minutes
the seven points read C = 0.17-0.20 in the corner room and 0.15-0.16 in the middle room, leaving out
the middle run's `roomMiddle` point, which stands 8 mm from that purifier's axis, in its jet (0.044).

**Checks.** The gross flow through both patches is 0.0675 m³/s from 3 s to the end in both runs.
Over 1-1200 s the room's loss of C matches the flow times the intake's C to 0.04% in both. C's
extremes at every step (177,931 steps corner, 177,575 middle) were −0.00177 and 1.00362 in the corner
run and −0.00187 and 1.00307 in the middle, all within 0.28 m of the purifier's axis and below
0.6 m; no step went above 1.0003 or below −0.001 after 76 s (corner) or 62 s (middle). The middle run
had 26 tiny k-bounding events between 22 and 46 s, the largest −2.5e-10 m²/s². The solves took 7,843 s
(corner) and 8,283 s (middle) on 8 ranks each.

## What it cannot

- **Smoke and fine particles only.** C follows the air. Coarser dust and pollen settle: at unit
  density a 10 µm particle falls 2.4 m in about 13 minutes and a 25 µm grain in about 2, and what lies
  on the floor never reaches any purifier. None of that is modelled, so the case says nothing about
  coarse dust or pollen.
- **A closed, still, isothermal, unheated room with no one in it**, so a hard case for reaching the
  far side. Real rooms have warm and cold surfaces, heating, sun and people that stir the air too, and
  doors that open. The purifier's own 56 W, about 0.7 K on its air, is left out. The 81% and 84% are
  what this model did in 20 minutes, not a measured real-room figure.
- **The corner keeps the manual's 38 cm clearance.** Pushed closer into the corner it would do worse;
  the corner here is the corner as the manual permits.
- **One mesh.** A finer corner run (6 cm background, 1.5 cm at the outlet, 239,892 cells) exists only
  to 27 s, not to the 60 s planned: there the room's mean agrees to 0.0001, but the intake differed by
  4.4 points at 10 s and 0.7 at 27 s. So the corner's shortfall of about 8% of its rating is not shown
  to be independent of the mesh.
- **C's band has no source.** The runs were set to stop if C left −0.01 to 1.01. That band was set
  after a first set of pilots had stopped on a ±0.001 tolerance (the corner pilot read 1.0019 at 17 s,
  in one floor cell 28 cm from the axis); the ±0.001 had no source either, and widening it is not a
  validation of the overshoot. The model was not changed between the pilots and these runs, and C is
  never clipped. Those pilots are not part of this case.
- **The purifier is stair-stepped** on an unsnapped mesh, and its intake and outlet are drawn from the
  manual's drawing to that drawing's accuracy. The stair-stepped intake is about 1.5 times the true
  band's area, so its face speed is 0.44 m/s rather than 0.65; the flow through it is the same. The
  stair-stepped outlet is 0.0242 m² against the ring's 0.0245. The mesh first built, snapped, with
  6 cm room cells and a 7.5 mm collar at the purifier's foot (269,740 cells), held the step to 0.9 ms,
  over a million steps for 20 minutes; its fastest cells were all at the foot, where a uniform suction
  patch meets the floor, a local effect that does not change the flow through the patch. So the
  snapping and the collar were dropped to fit the solve in our 10 h, not for accuracy.
- **CADR is treated as the clean flow**: the model passes 0.0675 m³/s and everything leaving is clean.
  A real purifier moves more air than its CADR and does not clean all of it; measured flows can also
  fall short of declared ones. CADR is a tested figure, so it is used as it stands.
- **The furniture is solid blocks** and the room is ours; there is no air under the bed. The middle
  run's floor surface (`template/middle/constant/triSurface/roomWalls.stl`) has its purifier hole at
  the first attempt's 2.25 m, not at 2.257857; the floor is the background mesh's own face, and built
  with the corner's floor surface instead the middle mesh comes out the same point for point (only
  snappyHexMesh's `surfaceIndex` record differs).

## Sources

- A small tower purifier's user manual (US edition), read 7 Nov 2026: size, intake and outlet
  (drawing, parts list), smoke CADR 143 CFM at the top speed, 15-20 minutes for smoke, 38 cm clearance
  on all sides, rated room 20 m². No brand is named here and the manual is not included.
- Ginestet et al., CFD of 66 purifier layouts in a meeting room, AIVC conference 2024.
- Küpper et al., delivery rate in a 70 m³ room, as cited in PMC8730331.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with NumPy for
`scripts/extract_results.py`.

    cd cases/airPurifierCorner
    ./Allrun corner              # [nProcs], default 8
    ./Allrun middle
    python3 scripts/extract_results.py runs results

`Allrun` copies `template/common/{constant,system}` and `template/<run>/` into `runs/<run>/`, moves
the corner's purifier surfaces for `middle`, runs blockMesh and snappyHexMesh, checks the mesh, opens
the intake and outlet patches, copies `template/common/0.orig` to `0`, writes the two planes at t = 0,
decomposes by scotch and solves; once both runs have solved it writes `results/`.
`./Allrun --setup-only <run> [nProcs]` stops before the solve; `./Allclean` removes the runs. Each
run took a little over 2 h on 8 cores and writes about 400 MB, mostly planes and the every-step log.

From a clean copy of this case, `./Allrun --setup-only corner` and `middle` write both solved runs'
`constant/polyMesh` (boundary included), purifier surfaces, `system/`, `constant/` and `0/` byte for
byte, checkMesh OK at 98,840 and 99,260 cells, and the t = 0 planes byte for byte. Three serial steps
of each from there (nice 19, to 4 ms) take the solved runs' time steps to ten figures and repeat the
first step's Ux, Uy and Uz solves of the 8-rank logs exactly; the pressure solves and the later
residuals differ by up to about 0.1%, as serial and parallel GAMG do. Scotch's decomposition is not fixed, so a new solve will not repeat the solved runs
bit for bit. No full solve was run from this copy.

`results/` holds each run's history every 5 s, the clean-air fractions every 30 s and `summary.txt`;
no fields, meshes, planes or logs. The fine-mesh comparison, the corner jet's path and the 12 s
mesh timings above were read from the study's pilots and planes, not written by
`extract_results.py`.

The case was set up and solved by an agent on our own machine and checked by us. The files in
`results/` are what `scripts/extract_results.py` wrote from those two runs.
