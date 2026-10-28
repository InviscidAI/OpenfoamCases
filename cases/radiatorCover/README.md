# A radiator in a wooden radiator cover, against the same radiator bare

Radiator covers hide a radiator in a wooden box with a slatted front, and heating engineers
warn that boxing a radiator in costs some of its heat. This case switches the same radiator
on twice under a cold window, once bare and once inside a typical MDF cover, and asks how
much of the bare radiator's heat the covered one still gets into the room in the first five
minutes, and where its warm air goes. It is about the heat that reaches the room, not about
comfort or energy bills.

    ./Allrun bare      # the radiator bare, 0-300 s from switch-on
    ./Allrun cover     # the same radiator inside the cover

**The result.** Over the 300 s from switch-on, the heat that crossed the cover's outside
into the room was **114.9 kJ per metre, 69.9% of the 164.4 kJ/m the bare radiator gave**: on
these assumptions the cover held back about 30% of the heat. Minute by minute the share
rose from 65% to 75%, because the bare room warmed faster and a radiator held at 55 C gives
less into warmer air; corrected to the same room temperature it is 65-71% in every minute.
The limits below say why this is a comparison of two shapes in a 2-D section over five
minutes, not a measurement of a real cover's cost.

The room is [`radiatorUnderWindow`](../radiatorUnderWindow)'s 2-D section, its window and
its radiator box, but this is a case of its own, not a third run of that case: the radiator
is held at a water-like surface temperature instead of giving a fixed 60 W/m, radiation is
solved, and the mesh is a finer one written by a script of its own so that the cover's
12 mm slots have four cells each. None of `radiatorUnderWindow`'s runs changes.

## Why the radiator is held at a temperature

`radiatorUnderWindow` and its [curtain runs](../radiatorUnderWindow#curtains) give the
radiator a fixed output, 60 W/m, the section's own steady loss. A fixed output cannot answer
this question: whatever is put round the radiator, the same heat comes out, and a cover could
only delay it. A real radiator's
output is set by its water temperature and by the air and surfaces round it. Here every
steel surface is held at **55 C**, the mean of a 60 C flow and a 50 C return. 60 C is the
flow that Nesta's Money Saving Boiler Challenge, the UK campaign since 2022, asks owners of
combi boilers to set or go below; the 10 K drop is ours, the drop of EN 442's 75/65 rating.
Held at 55 C, the covered radiator gives less if the air and the cover round it are warmer,
or if less air passes it, and the cut is whatever the solve gives.

## The radiator

A **Stelrad Compact K1 600 x 1000**, a single steel panel with one convector of vertical
fins behind it, in `radiatorUnderWindow`'s box: x = 0.040 to 0.123 m from the window wall,
y = 0.15 to 0.75 m up from the floor. Stelrad rates it at 980 W at a 50 K mean water-to-air
difference to EN 442; with EN 442's exponent of 1.3 that is 616 W at 55 C in a 20 C room.
The section is 1 m deep and the radiator 1 m long, so these are per metre of section.

- **The front panel** is solid steel, x = 0.103 to 0.123 m: its cells are left out of the
  mesh and its faces are the patch `radiatorPanel`, held at 55 C, convecting and radiating.
- **The convector** behind it, x = 0.040 to 0.103 m, is the cell zone `convector`: its air is
  held at 55 C (`fixedTemperatureConstraint`), and a Darcy resistance
  (`explicitPorositySource`, `constant/fvOptions`) gives it channel friction upward and closes
  it sideways, d = (1e8, d_y, 1e8) 1/m2. Its output is the heat the air carries out of it, so
  it falls when the air coming in is warmer or slower, as a real convector's does. Nothing
  sets its power.

### The one fitted setting

Stelrad does not publish the fins' spacing and depth, so the channels' upward resistance d_y
was fitted once, on the bare radiator alone, to the catalogue rating, and then frozen for
both runs. Each pilot ran the bare run from rest to 40 s on 4 ranks; its output over
25-40 s (convection and radiation, the panel's and the convector's) was set against
980 ((55 C - T_room)/50)^1.3 W/m at that interval's mean room temperature:

| d_y (1/m2) | output (W/m) | rating at the room's temperature (W/m) | ratio |
|---:|---:|---:|---:|
| 120,000 | 1403.2 | 520.1 | 2.698 |
| 480,000 | 860.1 | 558.1 | 1.541 |
| 1,900,000 | 648.9 | 573.0 | 1.132 |
| 7,600,000 | 586.6 | 577.1 | 1.017 |
| 30,400,000 | 572.7 | 580.5 | 0.987 |
| **16,308,374.67** (a separate confirming pilot) | **578.1** | **577.9** | **1.0003** |

Linear interpolation of output less rating in log d_y between the last two gave
d_y = 1.630837467e7 1/m2 (`config/caseSettings`). In the confirming pilot radiation gave
195.0 W/m, 33.7% of the output. That makes the bare radiator a K1 by its data sheet; the
cover's effect is not fitted to anything.

## The cover

A **B&Q "Horizontal Grill" radiator cover by Jack Stonehouse**, white MDF with a slotted
front and a solid top (diy.com, product 5060176866065 and its other sizes, read on 23 Oct
2026): internal W67 x H80 x D16.5 cm, external W78 x H81.5 x D19 cm, "constructed from 13mm
thick MDF and the grill from 3mm MDF", "a front grill panel with horizontal slots", and
"Please allow for a 3-4cm gap around your radiator". The width does not enter a section. In
the section, with x from the window wall and y up from the floor:

| part | in the model | from |
|---|---|---|
| back | none: the cover stands against the wall, open to the radiator and the wall behind it | ours; the listing does not say, and covers of this kind fit over the radiator from the front |
| top | solid, at y = 0.800 m from the wall to x = 0.190 m, so it overhangs the front by 25 mm; 15 mm of MDF | the 80 cm inside height; 15 mm is 81.5 less 80 cm |
| front | at x = 0.165 m, the 16.5 cm inside depth, from y = 0.04 to 0.80 m | the listing |
| rails | the front's top rail y = 0.72-0.80 m and bottom rail y = 0.04-0.12 m, 13 mm MDF | ours, the heights; the listing does not give them |
| gap | 4 cm open under the bottom rail to the floor, no base | ours |
| grille | between the rails, 3 mm MDF cut with 25 horizontal slots 12 mm tall at a 24 mm pitch, half open (the first slot y = 0.126-0.138 m) | ours, the slot size and pitch; no listing gives them |
| MDF | conducts at 0.13 W/m K through its thickness, emissivity 0.9, **no heat capacity** | 0.13 and 0.9 handbook values, ours |

The radiator's front is 42 mm behind the cover's front, inside B&Q's 3-4 cm. Every part is
a **zero-thickness baffle** on the mesh's cell faces: the internal faces along the part are
split into two coincident wall patches (`topA`/`topB`, `topRailA`/`B`, `bottomRailA`/`B`,
`grilleA`/`B`) that `compressible::thermalBaffle1D` couples by steady 1-D conduction through
the part's thickness, with each face's own radiation. The MDF's thickness enters only its
conduction: the rails, frame and grille are one plane at x = 0.165 m, and the top is a plane
at y = 0.800 m. No air crosses a baffle, and no radiation: air and radiation pass between the
cover's inside and the room only through the slots and the gap under the cover. With no heat
capacity the cover is as it would be once warmed through, while the air starts from rest;
a real cover takes far longer than five minutes to warm.

## The room

`radiatorUnderWindow`'s section, unchanged but for the radiator: 4.0 m from the window wall
to the inner wall, 2.4 m high, 1 m deep; glass from 0.90 to 2.10 m above the floor, U =
2.8 W/m2K to 0 C outside (`externalWallHeatFluxTemperature`, h = 4.403 W/m2K outside, the
inside film the solver's); the ceiling and inner wall held at 20 C; the floor and the window
wall below and above the glass, including the wall behind the radiator, adiabatic. The air
starts at rest at 20 C, and at t = 0 the radiator is at 55 C.

**The room warms.** About 600 W/m into a section whose own steady loss at 20.5 C is 60 W/m
(`radiatorUnderWindow`, "Why 60 W per metre") warms the air: the bare room's mean is 27.5 C
and the covered room's 25.4 C at 300 s. A real room, with outside walls, air leaking out
and furniture to heat, would warm far more slowly. The heat that reaches the room is counted
before it is lost, so the count is not changed by where it goes afterwards, but a radiator
held at 55 C gives less into a warmer room, and this is why the share moves over the five
minutes (see the results).

## The model

- `buoyantPimpleFoam` (OpenFOAM v2512), air a perfect gas (28.96 kg/kmol, cp 1005 J/kg K, mu
  1.82e-5 Pa s, Pr 0.71), k-omega SST with the buoyancy production term in k
  (`buoyancyTurbSource`), wall functions on every wall; from `radiatorUnderWindow`.
- **Radiation**: surface to surface through transparent air, `fvDOM` with 32 directions in the
  plane (`nPhi 8`, `nTheta 0`), solved every 10 steps; grey, diffuse surfaces with emissivity
  0.9 (painted steel, painted MDF, walls, floor, ceiling) and 0.84 for the inside face of the
  uncoated glass (handbook values, ours).
- **Mesh**: `scripts/make_case.py` writes the polyMesh directly from a Cartesian grid, one
  cell thick: a 348 x 430 grid, **148,240 cells** in both runs once the steel panel's 1,400 are
  left out; 2.5-3 mm cells from the window wall to x = 0.25 m and from the floor to 0.83 m,
  with grid lines on every edge of the radiator, the cover, its rails and its slots (4 cells
  to a slot, 14 up the 4 cm gap under the cover, 14 across the 42 mm between the
  radiator's front and the cover's), widening to about 22-25 mm in the middle of the room; 5 mm to the bottom of the
  glass, 12 mm up the glass, narrowing to 4.8 mm at the ceiling. The convector zone is 4,200
  cells. The bare run's mesh has the same cells and no cover patches. `checkMesh`: Mesh OK, no
  non-orthogonality.
- **Time step**: Courant number at most 1, two outer and two pressure correctors, the pressure
  reference in the middle of the room, the final pressure solve capped at 100 iterations; all
  from `radiatorUnderWindow`. The bare run took 63,519 steps and the covered run 91,526. After
  10 s the cell setting the step was, in the covered run, just outside the top slot (x =
  0.166-0.170 m, y = 0.70 m) in 95% of steps, and in the bare run just below the convector, in
  the 4 cm between it and the wall, in 90%.
- **Output**: `heatAccounting`, a coded function object in `config/caseSettings`, writes the
  heat flows below at every step to `postProcessing/heatAccounting/heat.csv`; the mid-plane
  section (T, U, the incident radiation G and qr) every 0.625 s to `postProcessing/clip`; the
  fields once, at 300 s.

### The heat that reaches the room

- **The radiator's output** is what it gives the air and the room's surfaces: the convector
  zone's energy balance (the enthalpy its air carries out less what came in, what it conducts
  across its faces, and the rise of its stored and kinetic energy) plus the steel panel's
  convection and its net radiation off all its faces.
- **The heat crossing the cover's outside** is the enthalpy carried out of the cover's
  region (x < 0.165 m, y < 0.8 m, the panel excluded) less what is carried in, diffusion and
  radiation across its openings, and the convection and radiation off the MDF's faces that
  look into the room. With no heat capacity in the MDF and an adiabatic wall behind it,
  everything the radiator gives crosses the cover except what the air inside still holds.
- **For the bare radiator** the heat reaching the room is its output.

The share is the heat crossing the cover from t = 0 to 300 s over the bare radiator's output
over the same time. The sensible enthalpy is referenced to 20 C, as the solver's is.

## Results

`scripts/extract_results.py` writes, from the two runs' monitors, `results/summary.txt`,
`results/minutes.csv` and each run's history every 2.5 s, `results/<run>/history.csv`
(W per metre of section; room = the mass-weighted mean air temperature):

| | 0-60 s | 60-120 | 120-180 | 180-240 | 240-300 |
|---|---:|---:|---:|---:|---:|
| bare: output, W/m | 605.8 | 576.5 | 546.0 | 519.2 | 492.9 |
| of which radiation | 195.5 (32%) | 192.7 (33%) | 191.8 (35%) | 189.6 (37%) | 187.6 (38%) |
| bare room, C | 21.5 | 23.4 | 25.0 | 26.2 | 27.1 |
| bare output / rating at the room's temperature | 1.041 | 1.069 | 1.080 | 1.085 | 1.076 |
| cover: radiator's output, W/m | 435.5 | 390.0 | 386.5 | 377.0 | 368.7 |
| of which radiation | 160.0 (37%) | 155.7 (40%) | 155.0 (40%) | 152.8 (41%) | 151.2 (41%) |
| crossing the cover, W/m | 394.8 | 389.8 | 386.1 | 376.7 | 368.4 |
| covered room, C | 21.2 | 22.6 | 23.5 | 24.4 | 25.1 |
| **crossing / bare output** | **65.2%** | **67.6%** | **70.7%** | **72.5%** | **74.7%** |
| cover's output / bare, at the bare room's temperature | 71.1% | 65.4% | 66.7% | 67.1% | 68.3% |

Over the whole 300 s:

| | kJ per metre | of the bare radiator's |
|---|---:|---:|
| the bare radiator's output | 164.4 | 100% |
| the covered radiator's output | 117.5 | 71.4% |
| **heat crossing the cover into the room** | **114.9** | **69.9%** |
| left in the air inside the cover at 300 s | 2.4 | |

**Why it comes out at 70%.** The cover takes heat from both of the radiator's paths. Its solid
top stops the plume from rising straight up the glass: in the sections at 120 s and 300 s room
air comes in through the floor gap and the lower slots, and nearly all the warm air leaves
through the slots in the top 0.1 m of the grille, under the top's overhang. Each minute the
air leaving carries 312-328 W/m of enthalpy above 20 C and the air coming in brings back 26-60
W/m. The slats and rails stand in the way of the panel's radiation. In the first minute the
covered radiator's convection was 276 W/m against the bare one's 410 (a third less) and its
radiation 160 against 196 (a fifth less), so radiation's share of what is left rises from a
third to about 40%. The air round the radiator is warmer inside the cover: area-means in the
section (`results/section_means.csv`) put the air in the box x < 0.165 m, y < 0.8 m at
31.1-32.6 C in the covered run at 60-300 s, against 28.7-31.2 C round the bare radiator, while
the air under the convector, which it draws in, is within 1.2 K between the runs. The monitors
do not split the convection's cut between less air passing through the fins and warmer air
round the panel.

**Why the share moves.** The covered radiator's output hardly changes after the first minute
(390 to 369 W/m), while the bare radiator's falls (577 to 493 W/m) as its room warms faster
(27.1 against 25.1 C in the last minute), since a radiator held at 55 C gives less into warmer
air. That moves the minute-by-minute share from 65% to 75%. Rescaled to the bare room's
temperature by EN 442's exponent, which is how the rating itself scales and is only an
approximation for the covered radiator, the covered one gives 65-68% of the bare one's output
in each minute after the first, 68.3% in the last. Every form of the ratio over these five
minutes lies between 65% and 75%, and the total, the one the case reports, is 69.9%. The
ratio had not settled by 300 s; for a room whose temperature is held, the same-room figures
are the closer guide.

**The bare radiator against its rating.** The fit was made at 25-40 s. Over the whole run
the bare radiator gives 4-9% more than its rating at the room's mean temperature (1.041 in
the first minute, at most 1.085). A likely reason, not tested, is that the room's mean
includes the warm layer under the ceiling while the radiator draws in the cooler air at the
floor (under the convector it was 2.7 K below the room's area-mean at 300 s). It gives
32-38% of its heat by radiation, falling from 196 to 188 W/m as the room's surfaces warm.

**Against the sources.** CIBSE Guide B (2005), as Brady et al. quote it: "encasing radiators
reduces heat output by 20% or more". The model's 30% agrees. Brady, Abdellatif, Cullen,
Maddocks and Al-Shamma'a measured, at Liverpool John Moores University, a timber cover over a
radiator at steady state cutting its output "up to 40%" (their Figure 8's means: 318 W bare,
191 W covered, a 40% cut; their Table 4 puts the wooden cover at 53% of the bare radiator, a
47% cut). The model's cut is smaller. Several of its assumptions favour the cover (the
adiabatic wall behind it, a half-open grille of our choosing, the MDF at once warm), and the
cover and radiator they tested are not this one, so the case does not explain the difference.
The same paper quotes CIBSE's "a radiator shelf could reduce heat output by 10%"; no shelf
was run here.

**The heat budget closes.** The room is closed, so the radiator's output plus what the walls
give the air must equal the rise of the air's internal energy, (cv/R) times the integral of p.
Over each minute it closes to within 2.8 W/m in the first minute and 0.72 W/m after, over
0-300 s to +0.66 W/m (bare) and +0.49 W/m (cover), against outputs of 370-610 W/m. The first
minute's residual is the first 7.5 s (+22 W/m): at t = 0 the convector's air is raised to 55 C
at once (about 1.6 kJ/m for its 0.0378 m3; the radiators give 1287 and 1308 W/m over the first
2.5 s, against 594 and 405 W/m over the next 2.5 s), and the budget does not follow that jump
exactly. After the first 7.5 s every 7.5 s interval closes to within 1.5 W/m (bare) and 0.7
W/m (cover). Both solves end in `End` at 300 s with no fatal error; `omega` was bounded once,
at the first step, and `k` is held at its 1e-15 floor in some steps.

## How the case got here

The first attempt solved both runs 0-30 s side by side on 8 ranks each and restarted them
from the 30 s and 35 s fields on 16 ranks. The joined histories showed jumps in the room's
stored energy at each restart, 3.8-5.4 kJ/m within 0.1 s, that no recorded heat flow
accounted for. Their cause was not found. Both runs were therefore solved again from rest
to 300 s, each in one uninterrupted run on 16 ranks, and the results here are those two
runs alone; the case writes its fields only at 300 s, and restarting it from saved fields is
not tested. A run with a deep windowsill over the bare radiator was set up but not solved.

## What the clip shows, and what it does not

The clip shows the two sections one above the other from switch-on, 300 s at 15 times real
time, the air's temperature with moving air parcels, and a count in each panel of the heat that has
reached the room so far as a share of the bare radiator's 300 s total, ending at 100% and 70%.
In the clip the cover is drawn about twice its true thickness so that it reads on a phone;
the solve's cover is the baffles above.

## What it cannot

- **A 2-D section.** The radiator and the cover run endlessly along the wall: no ends, no
  side panels, no air round the cover's sides, and the cover's width plays no part. Every
  number is per metre of section.
- **A radiator held at one temperature.** Every steel surface and the convector's air are at
  55 C from top to bottom, from t = 0. A real radiator is cooler at the bottom than at the top,
  takes minutes to warm, and on a fixed water flow runs a little warmer when a cover cuts its
  output, which would win back part of the cut. The convector is a
  porous zone, not fins, and its one setting is fitted to the bare radiator's rating; the
  bare radiator then runs 4-9% above that rating through the run.
- **One cover.** One design, B&Q's horizontal grille, with rails, slot size and pitch, the
  floor gap and the open back chosen by us. A cover with a closed back, a metal grille, a
  deeper top or narrower slots would give another number.
- **A thin, weightless cover.** Each part is a zero-thickness baffle that conducts as its MDF
  thickness and stores no heat: the cover as it is once warmed through, which a real one
  reaches only after far longer than five minutes. Its frame and grille are one plane.
- **An adiabatic wall behind the radiator.** Brady et al. measured a little more heat lost
  into the wall behind a wooden cover than behind the bare radiator (a few watts against
  190-320 W); leaving it out favours the cover slightly.
- **Five minutes from switch-on, not a steady state.** The share was still moving, 65% to 75%
  minute by minute, and the rooms warm 5-7.5 K in the five minutes because the section has
  almost no losses. The 69.9% belongs to these five minutes in these rooms.
- **Grey radiation in the plane**, with emissivities that are handbook values, and
  transparent air.
- **One mesh and one realization each.** No mesh study; k-omega SST URANS with wall
  functions on every surface.

## Sources

- Stelrad Compact K1 600 x 1000: 980 W at dT50 to EN 442, and EN 442's exponent of 1.3, as in
  [`radiatorUnderWindow`](../radiatorUnderWindow).
- Nesta, Money Saving Boiler Challenge, evidence summary:
  nesta.org.uk/documents/2662/Boiler_Campaign_-_Evidence_Summary_.pdf (the 60 C flow).
- B&Q, Jack Stonehouse "Horizontal Grill" radiator cover, diy.com, products 5060176866065 and
  5060176863514 (the dimensions, the 13 mm and 3 mm MDF, the 3-4 cm gap), read 23 Oct 2026.
- S. Brady, A. Abdellatif, J. Cullen, I. Maddocks, A. Al-Shamma'a, "An investigation into the
  effect of decorative covers on the heat output from LPHW radiators", Energy and Buildings
  133 (2016) 414-422; accepted manuscript at researchonline.ljmu.ac.uk/id/eprint/4222/. It
  quotes CIBSE Guide B (2005).
- UK SAP default U-values for the glass, as in `radiatorUnderWindow`.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with
NumPy (PyVista too for `results/section_means.csv`).

    cd cases/radiatorCover
    ./Allrun bare            # [nProcs], default 16
    ./Allrun cover
    python3 scripts/extract_results.py runs results

`Allrun` writes the run into `runs/<run>/` with `scripts/make_case.py`, checks the mesh,
decomposes it, writes the t = 0 section, solves and, once both runs have solved, writes
`results/`. `./Allrun --setup-only <run> [nProcs]` stops before the solve; `./Allclean`
removes the runs. The coded function object is compiled by OpenFOAM at the solve's start.

The bare run took 26,712 s (7.4 h) and the covered run 36,896 s (10.2 h) of wall time, each
alone on 16 ranks. Each writes 481 sections of about 11 MB, about 5.3 GB a run (gzip takes
them to about 2 MB each); the fields are written once, at 300 s.

The case was set up by an agent and checked by us; the runs were solved on our own machine.
The files in `results/` are what `scripts/extract_results.py` wrote from those two runs.
Checked from a clean clone: `./Allrun --setup-only bare` and `cover` write the solved runs'
meshes (points, faces, owner, neighbour, boundary and the cell, face and point zones) and
every 0/ field byte for byte, and their t = 0 sections byte for byte; `checkMesh` passes at
148,240 cells. The dictionaries' expanded values are the solved runs', the solved runs having
read the same settings through an older, longer `config/caseSettings` whose unused entries
are gone; the scotch decomposition differs. `scripts/extract_results.py` on the solved runs
writes `results/` byte for byte.
