# A radiator in a wooden radiator cover, against the same radiator bare

Radiator covers hide a radiator in a wooden box with a slatted front, and heating engineers
warn that boxing a radiator in costs some of its heat. This case switches the same radiator
on twice under a cold window, once bare and once inside a typical MDF cover, and asks how
much of the bare radiator's heat the covered one still gets into the room in the first five
minutes, and where its warm air goes. It is about the heat that reaches the room, not about
comfort or energy bills. A third run, added later, puts a sofa 15 cm in front of the bare
radiator and asks whether the room warms more slowly. A pair added after that gives the
radiator a more open convector and asks how much more heat a row of small fans under it adds.

    ./Allrun bare      # the radiator bare, 0-300 s from switch-on
    ./Allrun cover     # the same radiator inside the cover
    ./Allrun sofa      # the bare radiator with a sofa standing 15 cm in front of it
    ./Allrun finsBare  # the bare radiator with a fin-gap convector heated through a conductance
    ./Allrun finsFans  # the same with a row of small fans under the radiator

**The result.** Over the 300 s from switch-on, the heat that crossed the cover's outside
into the room was **114.9 kJ per metre, 69.9% of the 164.4 kJ/m the bare radiator gave**: on
these assumptions the cover held back about 30% of the heat. Minute by minute the share
rose from 65% to 75%, because the bare room warmed faster and a radiator held at 55 C gives
less into warmer air; corrected to the same room temperature it is 65-71% in every minute.
The limits below say why this is a comparison of two shapes in a 2-D section over five
minutes, not a measurement of a real cover's cost.

**With the sofa** the radiator gave 151.6 kJ/m over the five minutes, 92% of the bare
radiator's 164.4, and yet the room's air did not warm more slowly. It was the same as the bare
room's to within 0.05 K for the first minute, and then it pulled slightly ahead, to 27.9 C
against 27.5 C at five minutes. That rests above all on one assumption of this room: **the
ceiling and the inner wall are held at 20 C**. In the bare room they absorb 37 kJ/m of the
radiator's radiation over the five minutes, and that heat leaves the model. With the sofa they
absorb 10 kJ/m, because the sofa's back catches the radiation and gives most of it to the air.
In a room whose ceiling and walls warm up, part of that 37 kJ/m would come back, and the answer
could change. [The sofa in front of the radiator](#the-sofa-in-front-of-the-radiator) has the
run and its limits.

**With fans under the radiator** the radiator gave 173.1 kJ/m over the five minutes against
162.6 kJ/m without them, **106.45%**, and the room's air ended 0.78 K warmer. The gain is all
convection: radiation is a third of the output and the fans do not touch it. These two runs
have a convector of their own, with the resistance of a published 6.31 mm fin gap and a
fitted heat transfer from the fins to the air, so their bare radiator is not the `bare` run
above. [Fans under the radiator](#fans-under-the-radiator) has the runs and their limits, the
main one being that the fitted heat transfer is about a tenth of a physical fin's, which
probably understates the gain.

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

## The sofa in front of the radiator

The usual advice is to keep a sofa well away from a radiator so that its heat can reach the
room. The `sofa` run is the bare run with a sofa standing in front of the radiator: the same
room, the same radiator held at 55 C, the same numerics, and the same mesh with the sofa cut
out of it. It asks whether the room's air warms more slowly than in the bare run over the
first five minutes. The bare run is not solved again.

### The sofa and the gap

**An IKEA BACKSÄLEN 3-seat sofa**, from IKEA's product page (read 18 Oct 2026): depth 94 cm,
"Height including back cushions 85 cm", backrest 72 cm, seat height 43 cm, seat depth 60 cm,
"Free height under furniture 17 cm". In the section it is a solid side profile in three
blocks: the seat and base from 17 cm up to the 43 cm seat over the whole depth, a backrest
frame 12 cm thick up to 72 cm, and a back cushion 22 cm thick in front of it up to 85 cm. The
split of the 34 cm behind the seat into 12 and 22 cm is ours. The section is cut between the
legs, so the 17 cm under the sofa is open from back to front, as it is along most of a real
sofa's length.

**The gap is 15 cm** from the radiator's front to the sofa's back. It is the gap people say they
leave, and less than the advice asks for:

- a Mumsnet poster planned "about 15-17cm gap" in front of a radiator, and the one reply with a
  figure accepted it (26 Jul 2026);
- a MoneySavingExpert reply advises "just leave a 5" pr 6" gap for airflow", 13-15 cm, while
  other posters on the same page have theirs "rammed up to the radiator" or "normally right up
  against it" (page 3, read 31 Oct 2026);
- the advice asks for 30 cm: the Verbraucherzentrale, "Sofas und Schränke sollten mindestens 30
  Zentimeter Abstand zur Heizung haben", and EngineerFix, "at least 12 inches (30 cm) away from
  all sides of the radiator".

On the mesh every edge of the sofa is the bare run's nearest grid line
(`template/sofa/system/topoSetDict.sofa`): its back at x = 0.2731 m, 0.150 m in front of the
panel's front at x = 0.123 m; its underside at y = 0.171 m; the frame's top at 0.720 m and x =
0.3965 m; the cushion's top at 0.850 m and x = 0.6146 m; the seat at 0.429 m; its front at x =
1.2222 m, 0.949 m deep.

**The sofa's surface** is the patch `sofa`, a `compressible::thermalShell`: one thin layer, 12 mm
thick, 66.7 kg/m3, 1000 J/kg K and 0.05 W/m K, about 800 J/m2 K, standing for the fabric and
the foam just under it that a few minutes' heat reaches. Its room side is warmed by convection
and by the radiation it absorbs, with emissivity 0.9 like every other surface; its other side
is adiabatic, so nothing passes into the foam, the frame or the air inside the sofa. The
layer's figures are ours, not a measured sofa's.

**The mesh.** `subsetMesh` removes the sofa's 11,706 cells from the bare run's 148,240, leaving
136,534. On that mesh the sofa's faces sat in 7-22 mm cells, and the first solve diverged next to
the sofa (see the history below), so `refineMesh` splits in x and y the cells owning a sofa face
and every cell touching them (1,210 cells), and then the cells owning a sofa face again (1,198):
**143,758 cells**, the cells along the sofa a quarter of their first size, 2,400 sofa faces.
`checkMesh`: Mesh OK, maximum non-orthogonality 68 at the split faces. `makeFaMesh` makes the
layer's finite-area mesh on the patch `sofa`.

**The monitor** is `heatAccounting` with the sofa as a wall (`sofaConv`, `sofaRad`) and, in place
of the cover's region, the gap behind the sofa, from the window wall to the sofa's back and up
to its frame's top (x < 0.2731 m, y < 0.72 m, the `gap*` columns); `config/sofaSettings` holds the
change. The run writes its fields every 30 s, keeping the last two. It took 80,106 steps; after
10 s the cell setting the step was at the sofa's front lower corner (x = 1.225-1.231 m, y =
0.171 m) in 74% of steps and just below the convector in 20%.

### What the sofa run gives

`scripts/extract_results.py` writes `results/sofa/summary.txt` and `results/sofa/history.csv` (every
2.5 s) from the sofa run's monitor, set against the bare run's. The room's own air is its air
outside the convector, whose air is held at 55 C; the bare room's figures are those of the bare
run above.

| | 0-60 s | 60-120 | 120-180 | 180-240 | 240-300 |
|---|---:|---:|---:|---:|---:|
| bare: radiator's output, W/m | 605.8 | 576.5 | 546.0 | 519.2 | 492.9 |
| sofa: radiator's output, W/m | 592.2 | 540.3 | 499.8 | 461.2 | 433.4 |
| sofa / bare | 97.8% | 93.7% | 91.5% | 88.8% | 87.9% |
| sofa: panel's net radiation, W/m | 179.9 | 157.7 | 141.1 | 129.4 | 120.9 |
| stored in the sofa's surface, W/m | 85.3 | 52.6 | 24.2 | 9.1 | 1.0 |

| the room's own air, C | 30 s | 60 s | 120 s | 180 s | 240 s | 300 s |
|---|---:|---:|---:|---:|---:|---:|
| bare | 21.47 | 22.45 | 24.13 | 25.52 | 26.62 | 27.44 |
| sofa | 21.51 | 22.49 | 24.31 | 25.83 | 27.01 | 27.90 |
| sofa less bare, K | +0.04 | +0.04 | +0.18 | +0.31 | +0.39 | +0.46 |

These are the monitors' mass-weighted means. On the clip's mid-plane section the area mean of
the same air reads 27.91 C against 27.46 C at 300 s, so 27.9 against 27.5 C.

Over the whole 300 s, in kJ per metre (into the room's air +, out of it -):

| | bare | sofa |
|---|---:|---:|
| the radiator's output | 164.4 | 151.6 |
| of which the panel's net radiation | 57.4 | 43.7 |
| lost through the glass | -29.1 | -30.1 |
| **radiation absorbed by the ceiling and inner wall, held at 20 C** | **-37.3** | **-9.9** |
| convection into the ceiling and inner wall | -36.1 | -38.4 |
| stored in the sofa's surface | | -10.3 |
| rise of the air's energy | 61.7 | 62.9 |
| residual | 0.2 | 0.1 |

**Why the sofa room ends a little warmer.** The sofa cuts the radiator's output by 8% over the
five minutes, all of it radiation: the sofa's back, 15 cm in front of the panel, warms and
radiates back, and the panel's net radiation falls from 57.4 to 43.7 kJ/m, while the panel's
and the convector's convection together are about the same, 107.9 against 107.0 kJ/m. But in
the bare room most of the panel's radiation crosses the room to the ceiling and the inner wall,
and they are held at 20 C: whatever
radiation they absorb, 37.3 kJ/m in the five minutes, leaves the model at once and never warms
the air. With the sofa in the way they absorb 9.9 kJ/m. The sofa's back takes the radiation
instead, stores part of it (10.3 kJ/m, most of it in the first two minutes; by the last minute
it stores 1 W/m and at 300 s it gives a little back) and hands the rest to the air by
convection. So the sofa room's air gains 62.9 kJ/m against 61.7, and it holds 4% less air
(10.95 against 11.39 kg/m), because the sofa takes up its room. The difference, 0.46 K at five
minutes, is small, and it comes from where the radiation goes in a room whose ceiling and
inner wall cannot warm. It is not a finding that a sofa helps a radiator.

**What the air does.** The gap behind the sofa becomes a chimney: room air is drawn in under the
sofa and rises between the radiator and the sofa's back, and the plume leans over the sofa's
top. Out of the gap's region, the air carries 426-502 W/m of enthalpy above 20 C each minute,
and brings 19-124 W/m back in.

**The budget closes.** Radiator plus walls plus the sofa's surface less the rise of the air's
energy closes over 0-300 s to +0.39 W/m; to within 2.6 W/m in each minute, and after the first
7.5 s (+22.9 W/m, the convector's jump to 55 C, as in the other runs) to within 1.5 W/m in every
7.5 s. The solve ends in `End` at 300 s.

### How the sofa run got here

The sofa was first solved with no heat capacity: an adiabatic surface that radiates, the floor's
condition, on the unrefined mesh of 136,534 cells. That solve diverged twice, at 0.034 s and at
1.26 s, with a negative temperature on the seat's front face just below its top. The wall's
temperature is the cell's plus what it absorbs times the cell's depth over the air's
conductivity, its emission feeds back into the radiation, and radiation is solved every 10
steps; on 7-22 mm cells that loop has a gain above 1. Relaxing the sofa's wall temperature only
delayed the divergence; radiation every step held but would have taken about 27 h. Refining the
cells along the sofa, as above, cut the gain to about 0.6, and that run solved 0-300 s in 9.8 h
on 16 ranks. In it the sofa's back reached 36 C within 0.6 s and 42 C by 300 s, the radiator gave
148.9 kJ/m, and the room's air gained 7% more than the bare room's. A back that heats in under a
second hands the panel's radiation straight to the air, which a fabric back over foam would partly
store, so the sofa was given the heat capacity above and solved again. That run, without heat
capacity, is not in this case.

One thing is not explained. In the plane cells next to the sofa's back, the air at 300 s
averages about 3 K warmer in the run with heat capacity than in the run without it, where less
would be expected. The cause was not found. It does not enter the room's mean or the budget
above.

## Fans under the radiator

Small fans that clip under a radiator and blow room air up past it are sold to get more heat
from the same radiator. The `finsBare` and `finsFans` runs switch the same radiator on from
cold, bare and with a row of such fans under it, and ask how much more heat the radiator gives
the room in the first five minutes. Not energy bills: the fans' own electricity, about 1 W, is
left out, and whether a boiler would burn less is a question about the heating system.

### Why the convector is changed for these runs

The convector of the runs above is a porous zone whose air is held at 55 C, with one upward
resistance fitted to the catalogue rating (d_y = 1.63e7 1/m2). That resistance is about what
laminar flow between plates about a millimetre apart would give, which no convector has; it
passes almost no air, and forced air would go round the radiator rather than through its
fins. A first pair of fan runs with that convector gave 112.6% of the bare radiator's heat and
is not in this case. For these two runs the convector is rebuilt from a fin gap instead, with
two changes; the mesh, the room, the panel at 55 C, radiation and the numerics are `bare`'s.

1. **Its upward resistance is a 6.31 mm fin gap's.** That gap, with a 4 mm base and a 12 mm tip,
   is the optimum that Calisir, Baskaya, Yazar and Yucedag (2015) found when they started from a
   production panel radiator's convector and varied it for the most heat, as summarised by
   Dalkilic, Acikgoz, Ekici and Wongwises (2019, Journal of Thermal Engineering 5(4), p. 252):
   "the maximum heat transfer was achieved for 6.31 mm, 4 mm and 12 mm, correspondingly". **It
   is not Stelrad's figure**: Stelrad publishes no fin gap for the Compact K1 that we could
   find, and a gap tuned for output is, if anything, more open than a stock one. The fins are
   the zone as built, 63 mm deep and 600 mm tall. Laminar flow between parallel vertical plates
   6.31 mm apart, with a 0.5 mm sheet (ours, porosity 0.927), gives a Darcy resistance d_y =
   12/(phi s^2) = **325,267 1/m2**, 50 times less than the fitted one, and a Forchheimer f_y =
   0.674/(L phi^2) = **1.308 1/m** for the developing flow over the 0.6 m (Shah and London's
   K_inf for plates). Sideways the zone stays closed (1e8). The trapezoidal profile and the
   channels' finite depth are left out; a rectangular duct of aspect 0.1 would give a d_y about
   12% lower.
2. **The fins heat the air through a conductance instead of holding it at 55 C.** A
   `scalarSemiImplicitSource` on the zone's enthalpy gives S = hv (55 C - T) per unit volume,
   with **hv = 448.855 W/m3 K**. With the resistance now set by the gap, hv is the one fitted
   setting, fitted as d_y was: bare pilots from rest to 40 s, their output over 25-40 s against
   980 ((55 C - T_room)/50)^1.3 W/m at that interval's mean room temperature.

| hv (W/m3 K) | output (W/m) | rating at the room's temperature (W/m) | ratio |
|---:|---:|---:|---:|
| 20 | 354.3 | 600.3 | 0.590 |
| 100 | 415.7 | 595.0 | 0.699 |
| 500 | 595.1 | 582.2 | 1.022 |
| 2,500 | 803.8 | 565.1 | 1.422 |
| **448.855** (interpolated in log hv, a confirming pilot on 16 ranks) | **579.7** | **583.6** | **0.993** |

The four were run side by side on 4 ranks each. Fully developed laminar flow between plates at
55 C (Nu 7.54 on twice the gap, both faces of every fin wetted, fin efficiency 1) would give hv
of about 4,650 W/m3 K, **about ten times the fitted value**; at 2,500 the bare radiator already
gives 42% more than its rating. So the fit buys the catalogue output by making the fins heat the
air less well than real fins would. The radiator's output is defined as for the runs above; the
zone's energy balance now is the heat the fins give, and it matches hv V (55 C - the zone's
mean temperature) from the `convT` monitor to within 0.15 W/m in every minute of both runs.

### The fans

**SpeedComfort's Duo set**, two fans, the maker's recommendation for radiators 70 to 120 cm
long: 30 m3/h and 0.55 W per fan, each 34 x 7 x 2.2 cm, held under the radiator by magnets,
switching on at 33 C (speedcomfort.com, read 31 Oct 2026). Two fans on the 1 m radiator move
60 m3/h, **16.667 L/s per metre of section**. The maker gives no pressure curve, so the run
drives the fans at that free-air rating.

- **Where.** The cell zone `fan`, the 192 cells with centres at x = 0.0465-0.1165 m and y =
  0.126-0.150 m (`template/fins/system/topoSetDict.fan`): a bar 71 mm deep and 24 mm tall, eight
  rows of 3 mm cells, the nearest the mesh comes to 22 mm, its top against the radiator's bottom
  at y = 0.150 m, under the convector and the panel. The zone has no walls: the fans' housing is
  not in the model.
- **How.** OpenFOAM's `meanVelocityForce`, upward, holds the zone's mean cell velocity at
  `fanUbar` = **0.233898 m/s**. That is not the air the fans move, so the air through the zone's
  bottom face is measured from the face flux (`fanIn`) and Ubar was set from it: a 0-15 s pilot at
  0.143663 m/s and two production starts at 0.267093 and 0.221387 m/s, stopped at 30 s at 1.21
  and 0.92 of rated over 7.5-30 s, then 0.233898 m/s by interpolation, which gave 0.997 of rated
  over 7.5-30 s and was solved from rest; none of the stopped starts is in it.
- **When.** The radiator is at 55 C from t = 0, above the fans' 33 C, so they run from t = 0.
- **The fans' air was not held at the rating.** Through the fan's face it was 1.03, 1.00, 1.05,
  1.11 and 1.16 of rated minute by minute, **1.068 over 8-300 s**, rising as the room warmed:
  the controller holds the zone's mean velocity, not the air through it.
- In `finsBare` the zone is plain air and the monitors run the same.

`config/finsSettings` holds d_y, f_y, hv and fanUbar, replacing `caseSettings`' d_y, and the two
runs' field writes (every 30 s, the last two kept) and flow monitors: the net air through the fan
zone's bottom face (`fanInSum`, `fanInMag`, and the phi-weighted temperature and density on it,
`fanInT`), through the convector's bottom and top (`convInSum`, `convOutSum`) and the convector's
mean temperature (`convT`), every 5 steps. The two runs differ only in `constant/fanSettings`
(`fanOn 1` or `0`), which `scripts/make_case.py` writes. The run with fans took 78,360 steps
and the bare one 55,471.

### What the fans give

`scripts/extract_results.py` writes `results/finsBare/history.csv` and
`results/finsFans/history.csv` (every 2.5 s, with the flows) and `results/finsFans/summary.txt`,
the run with fans against the bare one.

| | 0-60 s | 60-120 | 120-180 | 180-240 | 240-300 |
|---|---:|---:|---:|---:|---:|
| bare: radiator's output, W/m | 583.6 | 571.4 | 551.2 | 514.4 | 489.5 |
| fans: radiator's output, W/m | 626.1 | 606.4 | 583.0 | 546.6 | 522.7 |
| **fans / bare** | **107.3%** | **106.1%** | **105.8%** | **106.3%** | **106.8%** |
| at the bare room's temperature | 108.1% | 108.0% | 108.4% | 109.6% | 110.6% |
| convection only, fans / bare | 111.0% | 109.4% | 109.2% | 110.4% | 111.3% |
| bare room, C | 21.31 | 23.36 | 25.09 | 26.46 | 27.41 |
| fans room, C | 21.50 | 23.78 | 25.66 | 27.12 | 28.15 |

Over the whole 300 s, in kJ per metre:

| | bare | fans |
|---|---:|---:|
| **the radiator's output** | **162.6** | **173.1 (106.45%)** |
| of which convection | 105.3 | 116.1 |
| of which the fins' zone | 71.3 | 79.1 |
| of which radiation | 57.3 | 57.0 |
| lost through the glass | -26.1 | -25.9 |
| into the ceiling and inner wall, held at 20 C | -72.8 | -77.1 |
| rise of the air's energy | 63.7 | 70.0 |

The rooms' mass-weighted mean air is 0.07 K apart at 10 s, 0.33 K at 60 s and **0.78 K at
300 s**, 28.56 against 27.79 C. The minute-by-minute share stays at 106-107% because the room
with fans warms faster and a radiator held at 55 C gives less into warmer air; rescaled to the
bare room's temperature by EN 442's exponent it rises from 108% to 111%.

**Why the gain is small.** The monitors give the air (litres per second per metre, net upward,
at the density on the fan's face):

| | 0-60 s | 60-120 | 120-180 | 180-240 | 240-300 |
|---|---:|---:|---:|---:|---:|
| through the fan's face: bare | 5.50 | 5.88 | 5.50 | 5.18 | 4.83 |
| through the fan's face: fans | 17.13 | 16.72 | 17.45 | 18.49 | 19.38 |
| into the convector: bare | 7.47 | 7.67 | 7.26 | 6.87 | 6.49 |
| into the convector: fans | 11.12 | 11.21 | 10.62 | 10.16 | 9.88 |
| out of its top: bare | 7.26 | 7.43 | 7.15 | 7.04 | 6.90 |
| out of its top: fans | 8.90 | 8.95 | 8.58 | 8.40 | 8.23 |

The bare radiator already draws its own air, about 7 L/s per metre into the convector's bottom
alone, and the fans add about 12 L/s per metre through their face. Of that extra air, 23-33%
enters the convector and 9-14% leaves its top; the rest turns back under the radiator or
leaves the zone through its sides (the monitors do not say where along them). The air that goes
through is warmed by fins that in this model heat it about ten times less well than real ones,
so the fins' zone gives only about 11% more heat with the fans (79.1 against 71.3 kJ/m, 10-12%
by minute), while the panel's convection rises from 34.0 to 37.0 kJ/m. And a third of the
output is radiation, which the fans leave alone: 57.0 against 57.3 kJ/m.

**The bare radiator against its rating.** 0.993 of it over 25-40 s, where it was fitted, and
then 1.06-1.10 as the room warms, much as the `bare` run's 1.04-1.09.

**Against the sources.** None is a measured figure we could read in full. Bayram and Koç
measured add-on fans under panel radiators in a test room (Case Studies in Thermal Engineering
50, 103432, 2023); their abstract says the fans raised the output while natural convection and
radiation fell, which agrees with these runs in kind, but we could not read the full text for a
figure.
Johansson and Wollerstrand's simulation of a flat panel with fans (Lund University, 2010), read
by eye from its Figure 9, needs about 57/42 C with their smallest fan, 25 L/s per metre, where
the radiator alone needs 60/45 C for the same output; with an exponent of 1.3 that is roughly
15% more at equal temperatures (our conversion), at 1.5 times the air here. The "about 20% more
heat" attributed to Milieu Centraal in Dutch retail blogs we have only second-hand.

**The budget closes.** Radiator plus walls less the rise of the air's energy closes over 0-300 s
to +0.13 W/m (bare) and +0.25 W/m (fans), to within 0.5 W/m in every minute and 1.3 W/m in every
7.5 s. With the convector's air no longer raised to 55 C at t = 0, the first 7.5 s close to
within about 1 W/m, where the other runs' are off by 22 W/m. Both solves end in `End` at 300 s
with no fatal error; `k` is held at its 1e-15 floor in some steps, as in the other runs.

### What the fins runs show, and what they cannot

They show that in this room, with this convector, a row of fans driven at about their rated
air adds about 6% to what a radiator held at 55 C gives the room in the first five minutes, and
8-11% at equal room temperature, all of it convection. They have all the limits of the runs
above but the fitted convector's, and more of their own:

- **A fin gap that is not Stelrad's.** 6.31 mm is Calisir et al.'s optimised gap as summarised
  by Dalkilic et al., not a measured K1. A tighter stock gap would pass less of the fans' air.
- **A fitted fin conductance, about a tenth of a physical fin's.** hv is fitted so the bare
  radiator gives the catalogue 980 W at dT50 in still air; a physical value gives far too much
  (804 W/m at hv 2,500 against a 565 W/m rating), so there is nothing sourced to put in its
  place. A real fin keeps more of its effect as the air through it rises, so the runs probably
  understate the fans' gain, by an amount no run here measures.
- **Fans above their rating.** On average about 7% above SpeedComfort Duo's rated 2 x 30 m3/h,
  16% above in the last minute, which flatters the fans.
- **Two fans spread over the whole metre.** The section spreads two 34 cm fans, which cover
  68 cm of the 1 m radiator, over its whole length, with no housing, driven at their free-air
  rating whatever the pressure, and without their own heat.
- **The radiator held at 55 C.** With fans more heat leaves it; a real radiator on a fixed water
  flow would cool a little and give back part of the gain. Holding it at 55 C is the boiler
  keeping up, so on this count the runs show the upper end of the gain, against the fitted
  conductance, which probably shows less than the whole.
- **Five minutes from cold.** The share by minute had settled near 106-107%, but the same-room
  share was still rising, and the rooms warm about 8 K in five minutes because the section has
  almost no losses.

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

The sofa's clip shows the bare room above and the sofa room below, each whole from floor to
ceiling, from switch-on, 300 s at 15 times real time, the air's temperature on a scale of
18-34 C with moving air parcels and the sofa as a plain grey solid. It asks "Sofa by a radiator:
is the room colder?" and shows a clock but no number. Rounded to whole degrees, the rooms would
read 27 against 28 C over the last 30 s and make a winner of 0.46 K, so the picture is left to
show that they warm alike. It does not show the walls held at 20 C, which that likeness rests on.

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

The sofa run has all of these, and more of its own:

- **A ceiling and an inner wall held at 20 C.** This decides the sofa run's answer. In the bare
  room they absorb 37 kJ/m of the panel's radiation over the five minutes and the heat leaves
  the model; with the sofa they absorb 10 kJ/m, because the sofa's back catches it and gives
  most of it to the air. That is why the sofa room ends slightly warmer, 27.9 against 27.5 C at
  five minutes. Real ceilings and walls warm and give some of that heat back to the room, so
  the bare room would lose less of its radiation, and the sofa room's lead could shrink or
  reverse. A real room also loses heat through its outside walls and air leaks, which this
  section does not beyond its glass. The run says that a sofa 15 cm away does not make the air
  colder in this room over these five minutes; it does not say a sofa helps a radiator.
- **A 2-D section through a sofa.** The sofa has no ends and no arms, so the radiator's plume
  cannot go round it as it would along a real room's wall, and the air under it is open from
  back to front over its whole length because the section is cut between the legs. Every number
  is per metre of sofa and radiator.
- **The sofa as a thin shell.** Its surface is one 12 mm layer of fabric over foam, about
  800 J/m2 K, adiabatic behind, with figures of ours. A real sofa has a frame, cushions and
  air inside it that would store more heat over a longer time and keep its back cooler at
  first; its fabric's emissivity is a handbook value, ours.
- **One gap, 15 cm.** It is the gap people say they leave (Mumsnet, MoneySavingExpert), not the
  30 cm the advice asks for, and not a sofa pushed against the radiator, which many have.
- **The room's air, not the person on the sofa.** The run compares the air's temperature. It
  says nothing of the radiation that would have reached someone sitting in the room, which the
  sofa's back blocks.
- **Five minutes.** The sofa's surface had all but stopped storing heat by 300 s; an evening
  would run on with walls, ceiling and sofa all warming, which this room does not have.

The fins runs' own limits are in [Fans under the radiator](#fans-under-the-radiator).

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
- IKEA, BACKSÄLEN 3-seat sofa, ikea.cn/cn/en/p/backsaelen-3-seat-sofa-hallarp-grey-s29393158
  (the sofa's dimensions), read 18 Oct 2026.
- Mumsnet, mumsnet.com/talk/property/5559171-how-much-gap-if-putting-a-sofa-bed-in-front-of-radiator
  (the 15-17 cm gap), 26 Jul 2026.
- MoneySavingExpert forums, forums.moneysavingexpert.com/discussion/4952482, page 3 (the 5-6 in
  gap, and sofas against the radiator), read 31 Oct 2026.
- Verbraucherzentrale, "Heizung: 10 einfache Tipps",
  verbraucherzentrale.de/wissen/energie/heizen-und-warmwasser/heizung-10-einfache-tipps-zum-heizkosten-sparen-13892
  (30 cm).
- EngineerFix, engineerfix.com/how-close-can-furniture-be-to-a-radiator (30 cm).
- M. K. Dalkilic, O. Acikgoz, B. Ekici, S. Wongwises, review of panel radiators, Journal of
  Thermal Engineering 5(4) (2019) 251-270, p. 252, open PDF at
  pdfs.semanticscholar.org/f6b5/33b077c4441620dd28a9d0d3dc2b008e7f31.pdf; it summarises
  Calisir, Baskaya, Yazar and Yucedag, "Parametric numerical investigation of heat transfer from
  convectors to improve efficiency of panel radiators" (2015, ICHMT Digital Library), the 6.31 mm
  gap.
- R. K. Shah, A. L. London, Laminar Flow Forced Convection in Ducts (1978): fRe = 24, Nu = 7.54 and
  K_inf = 0.674 for parallel plates.
- SpeedComfort, product pages of the Mono, Duo and Trio sets, speedcomfort.com, read 31 Oct 2026
  (30 m3/h and 0.55 W per fan, 34 x 7 x 2.2 cm, on at 33 C, the Duo set for 70-120 cm).
- Bayram and Koç, add-on fans under panel radiators in a test room, Case Studies in Thermal
  Engineering 50 (2023) 103432, doi:10.1016/j.csite.2023.103432 (abstract only).
- Johansson and Wollerstrand, a simulation of a panel radiator with fans, Lund University, 2010
  (Figure 9, read by eye).

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with
NumPy (PyVista too for `results/section_means.csv`).

    cd cases/radiatorCover
    ./Allrun bare            # [nProcs], default 16
    ./Allrun cover
    ./Allrun sofa
    ./Allrun finsBare
    ./Allrun finsFans
    python3 scripts/extract_results.py runs results

`Allrun` writes the run into `runs/<run>/` with `scripts/make_case.py`, checks the mesh,
decomposes it, writes the t = 0 section, solves and, once bare and cover have solved, writes
`results/`, and `results/sofa/` once sofa has solved too. For the sofa run it first cuts the
sofa out of the bare run's mesh and refines along it with OpenFOAM's `topoSet`, `subsetMesh`,
`foamDictionary` and `refineMesh`, then makes the shell's area mesh with `makeFaMesh`. For
the fins runs it makes the fan's cell zone and the face zones that measure the air with
`topoSet`, and once both have solved `scripts/extract_results.py` writes `results/finsBare/`
and `results/finsFans/`; they need neither `bare` nor `cover`.
`./Allrun --setup-only <run> [nProcs]` stops before the solve; `./Allclean`
removes the runs. The coded function object is compiled by OpenFOAM at the solve's start.

The bare run took 26,712 s (7.4 h), the covered run 36,896 s (10.2 h), the sofa run
29,974 s (8.3 h), finsBare 18,344 s (5.1 h) and finsFans 28,342 s (7.9 h) of wall time,
each alone on 16 ranks. Each writes 481 sections of about 10-11 MB, about 5 GB a run (gzip
takes them to about 2 MB each); the fields are written once, at 300 s, in bare and cover,
and every 30 s in sofa and the fins runs.

The case was set up by an agent and checked by us; the runs were solved on our own machine.
The files in `results/` are what `scripts/extract_results.py` wrote from those runs.
Checked from a clean clone: `./Allrun --setup-only bare` and `cover` write the solved runs'
meshes (points, faces, owner, neighbour, boundary and the cell, face and point zones) and
every 0/ field byte for byte, and their t = 0 sections byte for byte; `checkMesh` passes at
148,240 cells. The dictionaries' expanded values are the solved runs', the solved runs having
read the same settings through an older, longer `config/caseSettings` whose unused entries
are gone; the scotch decomposition differs. `scripts/extract_results.py` on the solved runs
writes `results/` byte for byte.

The sofa run was built by hand from the bare run and is checked the same way, from a clean
clone: `./Allrun --setup-only sofa` writes the solved run's mesh (points, faces, owner,
neighbour, boundary, the zones, `pointMesh/boundary` and the cell, face and point sets), the
shell's area mesh and every 0/ field byte for byte, but for the comment in `0/T`; `checkMesh`
passes at 143,758 cells; its t = 0 section is the solved run's byte for byte. Its dictionaries
are the solved run's once expanded, comments aside, with the unused entries of the older
`config/caseSettings` gone; the solved run read its monitor from its own copy of that file and
its field writes from a `system/stageSettings`, where this case has `config/sofaSettings`. The
scotch decomposition differs. `scripts/extract_results.py` on the solved monitors writes
`results/sofa/` byte for byte and leaves the bare and cover results as they were. Adding the
sofa run changes nothing that `./Allrun bare` or `cover` writes.

The fins runs were built by hand from the bare run and are checked the same way:
`./Allrun --setup-only finsBare` and `finsFans` write the solved runs' meshes (points, faces,
owner, neighbour, boundary, the cell, face and point zones and all eight sets) and every 0/
field byte for byte; `checkMesh` passes at 148,240 cells. Their dictionaries are the solved
runs' once expanded, comments aside, with the unused entries of the older `config/caseSettings`
gone; the solved runs read d_y and f_y from their own copy of that file, hv and the fan from
`constant/convectorSettings` and `constant/fanSettings`, and their field writes and monitors
from a `system/stageSettings`, where this case has `config/finsSettings`. The t = 0 section and
the decomposition were not compared. `scripts/extract_results.py` on the solved monitors writes
`results/finsBare/` and `results/finsFans/` and leaves the other results as they were. Adding
the fins runs changes nothing that `./Allrun bare`, `cover` or `sofa` writes.
