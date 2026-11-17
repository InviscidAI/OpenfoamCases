# Welding fume at a bench: an overhead canopy hood against an extractor at the back of the bench

A welder at a bench strikes an arc, and the fume rises off the weld in a hot plume. One camp hangs a hood over the
bench and ducts it outside: "Commercially they use a hood and exhaust fan, not a lot different from a commercial
kitchen exhaust hood" (GarageJournal forum, 2017), and hood makers sell overhead hoods for manual welding. The other
camp says take it off at the work, below the face: "It's now considered best practice to extract fumes below the
breathing zone" and "An overhead hood draws the fumes upwards, past the person welding" (the same thread); "Use an
extracted bench or extracted booth which draws fume away from the welder and towards the air inlet at the back" (HSE,
WL3). This case strikes the same arc at the same bench, with the same welder leaning over the work, twice: once under
a canopy hood and once with an extractor drawing through a grille at the back of the bench, and asks how much of the
fume rises past the welder's face in the first 40 s, and how much each extractor takes out of the bay.

    ./Allrun canopy    # the canopy hood over the bench, 0-40 s from the strike (the solved run stopped at 38.505 s)
    ./Allrun bench     # the extractor at the back of the bench, 0-40 s from the strike

**The result.** **Under the hood the plume runs up the front of the helmet to the hood; at the bench it never reaches
the face.** Of the fume made since the strike, the share that has risen through a 30 x 30 cm square just below the
welder's face is 43% at 1 s, 80% at 3 s, 88% at 10 s and **95% at 38 s** under the hood, and **0% throughout** at the
bench: the grille, 25 cm from the arc and drawing 0.93 m/s over its face, bends the plume flat along the bench top
before it can rise. **Both keep the bay clean**: by 38 s the hood has taken out 95.1% of the fume made and the bench
extractor 98.6%, so the comparison is about the welder's face, not the room. Read [What it cannot](#what-it-cannot)
before any number here: **neither number is an exposure**, the bench's zero in particular (the plume is a steady RANS
plume with no puffs to break away towards the face), **the welder never moves and leans the same way throughout**, and
**the two runs stopped on different fume-negativity guards** ([below](#the-two-runs-stop-rules)).

The bay, the welder and both extractors are new. The buoyant model, buoyantPimpleFoam with k-ω SST and buoyancy
production, is the one our room cases use ([`acLouvreAngle`](../acLouvreAngle), [`doorwayFanStove`](../doorwayFanStove)),
and `template/system/fvSolution` keeps [`radiatorUnderWindow`](../radiatorUnderWindow)'s notes. The passive tracer
carried with the temperature's own diffusivity is [`airCurtain`](../airCurtain)'s.

## The bay

A 3-D bay of a larger workshop, x from the back wall into the room, y up from the floor, z along the bench; metres.
The bay is 5 m deep, 3.5 m to the ceiling and 4 m wide between side walls, and its far side, x = 5, is open to the rest
of the shop (`open`). The whole bay is solved, with no symmetry.

| | where | |
|---|---|---|
| bench | x 0-0.75, y 0.86-0.90, z 1.40-2.60 | a steel top 1.2 x 0.75 m against the back wall, on four 5 cm legs |
| plate | x 0.35-0.55, y 0.90-0.91, z 1.90-2.10 | the work |
| arc | x 0.42-0.48, y 0.91-0.95, z 1.97-2.03 | a cell zone giving the air 500 W and 5 mg/s of fume |
| welder | standing at the bench's front, leaning 25° over the work | legs block x 0.85-1.10, y 0-0.95, z 1.82-2.18; torso 0.24 x 0.36 x 0.58 m tilted 25° from the hip at (0.975, 0.95) to the shoulders at (0.73, 1.476); a neck of radius 6.5 cm; a helmet, a sphere of radius 0.14 m at (0.604, 1.656, 2.0); arms of radius 4.5 cm to the hands at (0.53, 1.03, 2.06) and (0.52, 0.97, 1.86). The surface held at 30 °C |
| **canopy** | x 0-1.10, z 1.20-2.80, skirts' lower edge at y 2.10 | a sheet-metal hood 0.4 m deep against the back wall, 1.2 m above the work and 30 cm above the helmet, drawing **1.701 m³/s** (6,100 m³/h) through its top (`canopyExhaust`, y = 2.47, 1.648 m²) |
| **bench** | x 0-0.20, y 0.90-1.40, z 1.40-2.60 | a hollow plenum on the back of the bench top, its grille facing the welder (0.5 x 1.2 m), the fan drawing **0.5556 m³/s** (2,000 m³/h) from the plenum's back (`benchExhaust`, x = 0, 0.6 m²) |

The canopy's flow is ACGIH's canopy rule, Q = 1.4 P D Vc, with the bench's open perimeter P = 2.7 m, D = 1.2 m and
Vc = 75 fpm, the middle of the rule's 50-100 fpm. The bench's is the middle of the makers' figures for a bench this
size (Plymoth 1,500-2,200 m³/h for a 1.4 m table, Geovent about 2,500 m³/h for a 1.2 m one). The canopy moves three
times the bench's air. Each run has only its own extractor.

**The bench's grille** is a perforated face 2.5 cm thick, x 0.175-0.2 m, solved as a porous cell zone (`grillePanel`,
Darcy-Forchheimer with d = 4.75e7 1/m² in every direction, about 20 Pa at the face's 0.93 m/s; 15.1 Pa measured in a
test), which spreads the draw evenly over the face. Behind it the plenum is open air, 0.105 m³, and the fan draws from
its back, 20 cm from the plume's path.

**The arc** is lumped: 500 W of heat on h and 5 mg/s (0.3 g/min) of fume, both absolute, in the 48 cells whose centres
lie in the arc's box, 91.9 cm³ against the box's 144 cm³ (the sources are absolute, so the 500 W and 5 mg/s are
unchanged and simply sit in a smaller volume). The fume rate is within the 0.2-0.8 g/min measured for steady MIG welding
of mild steel. No measured figure for the plume's heat was found: 500 W is an estimate, about 0.2 kW carried by 15 L/min
of shielding gas heated by about 1,000 K and 0.2-0.3 kW convected off the hot bead and plate.

**The fume** is a passive tracer (`fume`, a `scalarTransport` function object, kg of fume per kg of air), released in
the arc zone: particles this small follow the air, and the plume's lift comes from its heat. It is carried by the mass
flux with the temperature's own diffusivity, alphaD 1/0.71 and alphaDt 1.0, the bulk turbulent Prandtl number of SST in
v2512 (the wall functions' Prt 0.85 is theirs only), by one scalar corrector a step to 1e-12, and is not bounded.

**The start.** At t = 0 the air is at rest at 20 °C, hydrostatic, with no fume; the arc and the extractor start
together, as with an extractor that switches on with the welding set. Air comes in through the open side at 20 °C with
no fume, its total pressure hydrostatic face by face (`prghTotalPressure`). Every surface but the welder is adiabatic
and no-slip.

**The numbers.** "Fume rising past the face" is the fume carried upward through the square y = 1.45 m,
x 0.30-0.60, z 1.85-2.15, just below the helmet's lower front edge (the mouth, at about (0.514, 1.549, 2.0)), summed from
the strike, as a share of the fume made so far. The breathing zone is the air within 15 cm of the mouth on the bench's
side of the helmet (x < 0.604 m), 9.3 L; its concentration is ρ times the tracer, in mg/m³.

## The model

`buoyantPimpleFoam` (OpenFOAM v2512), compressible air as a perfect gas (Cp 1005 J/kg K, molar mass 28.96,
μ 1.82e-5 Pa s, Pr 0.71, the sensible enthalpy referenced at 20 °C), k-ω SST with `buoyancyTurbSource` and wall
functions (`kLowReWallFunction`, `omegaWallFunction`, `nutkWallFunction`, `alphatJayatillekeWallFunction`). Euler in
time, adaptive steps at Courant 1 (maxDeltaT 0.02 s), limitedLinearV for U and limitedLinear for h, the fume, k and ω.
Two outer and two pressure correctors, p_rgh by GAMG to 1e-7 with the final solve capped at 100 iterations. The
extractors are `flowRateOutletVelocity` with p_rgh `fixedFluxPressure`. No radiation.

**The mesh** (`template/system/blockMeshDict`, `template/<run>/system/snappyHexMeshDict`): a background of 10 cm cubes
(blockMesh, 50 x 35 x 40), refined by snappyHexMesh, snapped, without layers: 5 cm in the bay near the bench, 2.5 cm
round the bench, the welder and the hood or the plenum and on their surfaces, and 1.25 cm over the arc, the plume, the
breathing zone and the plate (x 0.2-0.8, y 0.88-1.85, z 1.82-2.18) and through the whole plenum on bench. The bench,
plate, welder (`constant/triSurface/torso.stl` for the torso, searchable shapes for the rest) and the hood's or the
plenum's sheets are cut out of the mesh. `scripts/merge_patches.py` gathers snappyHexMesh's surface patches into
`bench`, `welder` and `canopyBody` or `plenumBody`; `topoSet` makes the arc's cell zone, the grille's porous zone and
the grille's face zone, and selects the extractor's faces, which `createPatch` makes the outlet. On bench, snappy's
snapping bows the internal planes of the grille panel by up to 2.86 mm, so `scripts/pin_panel_planes.py` moves those
points back onto x = 0.175, 0.1875 and 0.2 m along x only, and the zones are taken again from the pinned mesh.
**356,801 cells (canopy) and 411,317 (bench)**; `checkMesh` OK for both, non-orthogonality at most 55.7°, skewness at
most 3.26. With `-allGeometry` the bench mesh still flags concave cells, which we did not try to remove. One mesh a run,
no mesh study.

**The diagnostics** (a coded function object in `template/<run>/system/controlDict`, run at every step, a row every
0.1 s into `postProcessing/diagnostics/diagnostics.csv`): the bay's fume and enthalpy, the breathing zone's fume and
temperature, the arc zone's temperature, each extractor's flow, fume and enthalpy, the open side's flows each way, the
heat from the welder, the fume up and down through the square below the face, the gross flow and fume through the
grille's face both ways and the pressure across the panel, the hottest air, the fume's minimum, where it is and the air
volume below -1e-6, the fastest air outside the arc, and the running integrals of these, summed at every step; with
the twelve cells of highest Courant number and, on bench, the guard's own record (`fume_guard.csv`). `fumeMass` and
`fumeMinMax` write the fume's integral and extremes at every step, `probes` three points over the plate, `clip` the
section z = 2.0 (T, U, fume and ρ, as point and as cell values) every 0.1 s, and `frontClip` the section x = 0.45 every
0.5 s.

## The two runs' stop rules

The diagnostics stop a run, writing the fields at the next step, if the air outside the arc moves faster than 4 m/s,
or if the fume goes too far negative. The fume's negativity limit is not the same in the two runs:

- **canopy** stops when the fume's raw minimum, kg of fume per kg of air, falls below -1e-4. **The canopy run stopped
  on it at 38.505 s**, with a clean `End`: the minimum reached -1.057e-4 at (0.508, 1.080, 2.044) m, at the plume's edge 13 cm
  above the arc. **It was accepted to that time** and not restarted; its results are reported to 38 s and its last
  diagnostic row is at 38.5 s.
- **bench** stops when the fume's concentration, ρ times the tracer, falls below **-1.0 mg/m³ absolute, or below -1% of
  the breathing zone's mean once that mean exceeds 10 mg/m³**, and also if the signed fume budget leaves 1% after the
  first 0.05 s. **The bench run ran to 40 s under that revised guard** without a stop: its breathing-zone mean never
  reached 10 mg/m³, so the absolute -1.0 mg/m³ applied throughout, and its worst minimum was -0.078 mg/m³
  (-6.5e-8 of the tracer) at 9.97 s, next to the plate. Before it, a bench run under a purely relative limit (-1% of
  the breathing zone's mean) stopped itself at 0.0026 s, when the mean was about 1e-115 mg/m³; that run is not
  reported.

The two limits are in different units. At room density, -1e-4 of the tracer is about -120 mg/m³ and -1.0 mg/m³ is
about -8.4e-7 of the tracer, so **in concentration the canopy's limit is the looser of the two**, by about a hundred
times. The canopy run's negatives are real undershoots of that size, of order -100 mg/m³ at the worst cell beside a
plume whose core holds 1,000-4,000 mg/m³, but they sit in small pockets: the air below -1e-6 of the tracer (about
-1.2 mg/m³) never exceeded 0.21 L in any sampled field, against the breathing zone's 9.3 L. The bench run's never
reached -1e-6. The clip draws negative fume as clean air, and the budgets keep the signed field. The physics and
numerics of the two runs are otherwise the same. The comparisons below are over 5-38 s or at 38 s, the window both runs
have.

## Results

`results/canopy_report.csv` and `bench_report.csv`, at 0.5-30 s (canopy) and 0.5-40 s (bench): each extractor's flow
and its share of the fume, the bay's fume and the fume budget, the breathing zone's fume and temperature, the share
rising past the face, the welder's heat, the heat budget, the hottest air and the arc zone's mean, the fume's minimum,
the open side's flows and, on bench, the grille's flows and pressure drop.

| | 1 s | 3 s | 10 s | 20 s | 30 s | 38 s |
|---|---:|---:|---:|---:|---:|---:|
| fume rising past the face, canopy | 43% | 80% | 88% | 93% | 95% | **95%** |
| fume rising past the face, bench | 0% | 0% | 0% | 0% | 0% | **0%** |
| fume taken out so far, canopy | 0% | 51% | 82% | 91% | 94% | **95.1%** |
| fume taken out so far, bench | 53% | 82% | 95% | 97% | 98% | **98.6%** |
| breathing zone, canopy, mg/m³ | 29 | 145 | 133 | 140 | 131 | |
| breathing zone, canopy / bench, °C | 23.0 / 20.7 | 34.2 / 21.5 | 32.5 / 22.0 | 33.2 / 22.2 | 32.5 / 22.2 | **33.7 / 22.2** |

| over 5-38 s, or at 38 s | canopy | bench |
|---|---:|---:|
| breathing zone, mean fume, 5-38 s | 131 mg/m³ | about 1e-14 mg/m³, i.e. none |
| fume rising past the face, share of all made, at 38 s | 95% | 0% |
| fume taken out by the extractor, at 38 s | 95.1% | 98.6% |
| air at the breathing zone, at 38 s | 33.7 °C | 22.2 °C |
| fastest air outside the arc | 2.57 m/s | 1.96 m/s |
| the welder's heat to the air, after 10 s | about 20 W | about 70 W |

**Under the hood** the plume leaves the arc, runs up the front of the torso and the helmet, past the face by 1 s, and
fills the space from the arc to the hood by 2 s; it has about its final shape by 4 s and keeps wavering to the end,
with filaments beside the main plume. The breathing zone sits in it: 131 mg/m³ on average over 5-38 s, at 33.7 °C at
38 s. **At the bench** the plume lies along the bench top into the grille from the first half second and barely moves
after about 9 s; the air round the welder's head stays at 22 °C and clean. The bench's extractor starts taking fume at
once (53% of what was made by 1 s), the hood only once the plume has reached it (the first fume arrives after 1 s).
The bench run's welder, held at 30 °C, gives the air more heat, about 70 W against 20 W, because the air round it
stays near 22 °C instead of in the warm plume.

**Checks.** Both runs ended cleanly, canopy on its guard at 38.505 s and bench at 40 s. The extractors drew 1.701 and
0.5556 m³/s throughout. The signed fume budget, the bay's fume plus all that left against all that was made, closes to
**1.6e-5 (canopy) and 7.8e-10 (bench)** of the fume made at every sampled time. The full energy budget, with the
kinetic energy, its outflow and the gravitational work counted, closes to **+0.023% (canopy, 5-38.5 s) and -0.0096%
(bench, 5-40 s)** of the heat put in by the arc and the welder; the enthalpy and pressure terms alone close only to
-3.1% and +0.58%, which is why the full budget is the one to read. In an isolated test (arc on, no extractor, the welder
at 20 °C, steps of at most 0.2 ms) the arc zone gave the air 499.1 W, 0.18% under 500 W, once the pressure work,
kinetic energy and gravity were counted. Every final pressure solve met 1e-7 and none reached its cap. SST bounded k
2,533 times (canopy) and 147 times (bench) and ω 21 and 56 times; where, before bounding, was not recorded. In a
still-air check (no arc, no extractor) the air reached 0.00043 m/s in 17 steps, 0.1 s; its pressure solves sat at
1,000 iterations on a round-off floor near 4e-7, and it was ended there.

## What the clip shows, and what it does not

The clip shows the section z = 2.0 through the arc and the welder's centreline twice, side by side, the hood on the left
and the bench on the right, each the whole bench and welder with the hood or the plenum, **in real time from rest at the
strike to 0:15 of the solve**, then the last frame held for half a second, under the question "Welding fume: hood above
or at the bench?". The fume is drawn as smoke, from near white for clean air to a dark brown-grey for thick fume, on a
log scale from 1 to 2,000 mg/m³, with "clean air" and "thick fume" on the legend and no numbers. Each panel carries one
rounded number, "fume rising past the face": under the hood 43% at 0:01, 80% at 0:03, 88% at 0:10 and 91% at the end;
at the bench 0% throughout.

- **The number is the share of the fume made that has risen past the face, not an exposure.** It counts fume moving
  up through a square below the face, not fume breathed.
- The frames between the planes, written every 0.1 s, are drawn from the two writes' fields, not cross-faded; the fume
  is drawn from the cell values, smoothed within the cell size. The bench's legs, the arms (which run beside the plane),
  the helmet's lens, the arc's glow, a duct above the hood, one up the back wall from the plenum and slats over the
  porous face are drawn and are not in the plane. The negative fume is drawn as clean air.

## What it cannot

- **The clip does not give an exposure, and the bench's zero is too clean.** The hood's 131 mg/m³ at the breathing
  zone over 5-38 s is the concentration inside the plume, with no cross-draught and a welder who never moves. **The
  bench's near-zero, about 1e-14 mg/m³, is a steady RANS plume without puffs, not an exposure rating**: k-ω SST averages
  out the plume's puffing, so nothing breaks away from it towards the face, and a real bench extractor leaks some fume
  to the face. The case can say the plume goes past the face under the hood and not at the bench. It does not say the
  bench gives zero exposure, and neither number should be read as an exposure or set against a limit.
- **Both keep the shop clean.** By 38 s the hood has taken out 95.1% of the fume made and the bench 98.6%. The
  comparison is about the welder's face, not the room, and nothing here says the hood fails the shop.
- **The posture, the arc and the flows are fixed by the brief.** The welder leans 25° over the work and never moves;
  **how far the welder leans matters a good deal to the answer**, and a welder standing back or welding to the side
  breathes less under both. The arc's plume carries 500 W, an estimate (no measured figure was found). The hood draws
  1.70 m³/s with its skirts 1.2 m above the work and the bench extractor 0.556 m³/s, with the work 25 cm from the
  grille, as HSE's "position the workpiece correctly" asks; big or awkward work cannot always go there.
- **The two runs' stop rules differ** ([above](#the-two-runs-stop-rules)): canopy stopped at 38.505 s on -1e-4 of the
  tracer and was accepted to that time; bench ran to 40 s under -1.0 mg/m³ absolute, or -1% of the breathing-zone mean
  once that exceeds 10 mg/m³. The canopy run's fume undershoots below zero by up to about -100 mg/m³ in pockets of at
  most 0.21 L. The clip shows 0-15 s of both.
- **The arc is lumped, hot and without radiation.** Its 500 W sit in 48 cells of constant-property air with no
  radiation, so the arc zone's air reads 330-670 °C on average and its hottest cell 2,110 K (canopy) and 1,494 K (bench).
  That is the lumped source's own temperature, not a picture of an arc; the plume above it is what the case uses.
- **The welder is made of boxes, cylinders and a sphere**, and the helmet is solid, so the breathing zone is the air
  just in front of and below its lower edge, where a real helmet draws its air from. The neck was added during the build:
  the helmet, as first given, sat 7.6 cm clear of the torso; the neck joins them in both runs.
- **No cross-draughts, no other extraction, no shop.** Still air, no fan arm or on-torch extraction, no respirator, no
  welding in other positions, nothing about any one product, and the first 40 s, not a shift.
- **RANS, one mesh, one run each.** k-ω SST on snapped meshes of 356,801 and 411,317 cells, 1.25-10 cm, with wall
  functions and no layers. The fine box ends at y = 1.85 m, and the plume's flanks step in the cell values across it
  (6 against 21 mg/m³ at x = 0.46 m at 5.8 s), from the mesh rather than the flow. No mesh or time-step study, and no
  uncertainty bar on the 95%.

## Sources

- GarageJournal forum, "Venting for welding station", Aug 2017
  (https://www.garagejournal.com/forum/threads/venting-for-welding-station.367669/): #4, "Commercially they use a hood
  and exhaust fan, not a lot different from a commercial kitchen exhaust hood"; #6, "This is not considered the best
  practice any longer. It's now considered best practice to extract fumes below the breathing zone with a smoke sucker
  of some sort"; #7, "Extract the fumes at the work surface level, towards the back or downwards, away from the person
  welding. ... An overhead hood draws the fumes upwards, past the person welding."
- Nederman, Modular Hood: "designed to manage welding fumes in both manual and automated welding"; Imperial Systems'
  Air-Port fume exhaust hood, sold for manual and robotic welders.
- HSE, "Controlling the risks from welding" (https://www.hse.gov.uk/welding/welding-controls.htm): "The most effective
  way to reduce welding fume is to capture it at source, protecting the welder and preventing fume spreading."
- HSE, WL3 (https://www.hse.gov.uk/PUBNS/guidance/wl3.pdf): "Use an extracted bench or extracted booth which draws fume
  away from the welder and towards the air inlet at the back, when welding small to medium sized articles."
- OSHA, 29 CFR 1910.252(c)(3): a fixed enclosure with "a velocity away from the welder of not less than 100 linear feet
  (30 m) per minute".
- Bakers Gas, "Welding fume info: ventilation": "Overhead hoods (canopies), for example, capture most of the fume, but
  care must be taken to be sure fume is not pulled through the breathing zone of the operator." RoboVent, welding booth
  FAQ: "an overhead receiving hood may not do a good job of keeping weld fumes out of the breathing zone."
- ACGIH's high-canopy rule, Q = 1.4 P D Vc with Vc 50-100 fpm (as given in CIH study guides; the ACGIH manual itself was
  not read). Plymoth and Geovent for back-draught bench flows. OSTI 115455 for the 0.2-0.8 g/min fume rate of steady
  MIG welding on mild steel.
- The buoyant model: [`acLouvreAngle`](../acLouvreAngle) and [`doorwayFanStove`](../doorwayFanStove).

## How the case got here

**The build.** The case was set up and solved by an agent on a cloud workspace of four cores and checked by us. Its
fixes before production: the neck (above); the bench's extractor, which first had its outlet on the grille's face
itself, where a spurious circulation of 13-15 m/s formed where the face met the bench top and held the step at 0.6 ms,
projecting the study at 12-14 h, and was rebuilt as the hollow plenum behind a porous face with the fan on its back
(the box, the flow and the grille's position unchanged); and the fume's correctors, first three a step, then one in
both runs once profiling showed the extra ones cost more than 5% of a step, checked over 50 steps on the rebuilt bench
(the fume budget to 3e-10). A 0-5 s probe of the canopy run on all four cores ran at 231 wall-seconds per second of flow
over 3-5 s (a 4.5 ms step), and a 0-2 s probe of the rebuilt bench at 245 over 1-2 s. A check at 20 s, which would have
stopped both runs had their breathing zones been within a factor of two of each other, passed.

**The solve.** Production ran canopy then bench, one after the other on all four ranks. **The canopy run went straight
from rest to its guard's stop at 38.505 s in one segment**: 7,674 steps, 8,129 s of wall time. **The bench run, under
its revised guard, went straight from rest to 40 s in one segment**: 8,010 steps, 8,493 s. With the meshing, the tests,
the probes, the bench's rebuild and its first, stopped restart, the study recorded 6.45 h of the 10 h we allow. The
solved runs carried an abort function object, read at each write, which was never used; it is left out here. A
supervising script outside the solver watched the 10 h cap and the pressure solves' iteration limits and was never
triggered; it is not included, and the bench's coded guard still reads a `STOP_NOW` file it could have written.

**A straight run with this case's `Allrun` is the same run**, but it will not repeat the solved runs bit for bit: the
starting pressure differs in its last figures (below), and the scotch decomposition and the parallel sums need not
match on another machine (the solved runs pinned each rank to one core); in a turbulent buoyant flow that round-off
grows. A rebuilt canopy run may stop on its -1e-4 guard at a different time, or not before 40 s. No rebuilt run was
solved through.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with NumPy.

    cd cases/weldingFumeExtraction
    ./Allrun canopy              # [nProcs], default 4
    ./Allrun bench               # default 4

Each `Allrun` builds its run's own mesh in `runs/<run>/` from `template/` (blockMesh, a serial snappyHexMesh of about a
minute, the patch merge, topoSet and the extractor's patch, and on bench the grille's pinning), writes `0/`
(`scripts/make_fields.py`, from OpenFOAM's cell and face centres, `scripts/centres.py`), puts the run's
`system/controlDict` in place, checks the mesh, writes the t = 0 sections, decomposes by scotch and solves from 0 to
40 s. `./Allrun --setup-only <run> [nProcs]` stops before the solve; `./Allclean` removes the runs. The solved runs took
about 2.3 h (canopy) and 2.4 h (bench) on 4 ranks each.

Each run writes the section every 0.1 s and the front section every 0.5 s (VTK), the fields every 10 s and the
diagnostics. `results/` holds the tables at the report times; no fields, meshes, planes or logs. The files in `results/`
are what the agent's report script wrote from the solved runs' diagnostics; that script is not included.

Checked from a clean copy of this folder on 17 Nov 2026: blockMesh, snappyHexMesh, the patch merge, topoSet, the
extractor's createPatch and, on bench, the pinning give the solved meshes' 356,801 and 411,317 cells and their
`boundary` patch for patch, face counts and start faces, and checkMesh OK; the pinning moves 3,977 points on each of the
three planes, by at most 0.97, 1.48 and 2.86 mm. `make_fields.py` writes both runs' `0/` byte for byte for U, T, k,
omega, nut, alphat, fume and phi. `p` and `p_rgh` differ from the solved runs' by at most 0.075 Pa and 1.1e-5 Pa: the
solved runs took the cell centres from a VTK reader whose version is not recorded, and the reader here computes some
polyhedral cells' centres far off (up to 1.5 m), so `make_fields.py` takes OpenFOAM's own centres instead. The run's
`controlDict`, `fvSchemes`, `fvSolution`, `fvOptions`, `topoSetDict`, `snappyHexMeshDict` and `blockMeshDict` are the
solved runs' byte for byte, but for the diagnostics' name (`diagnostics`, which the solved runs called by a number of
ours) and the unused abort function object. Two serial steps of the bench run from there gave the solved run's time
steps to the last digit and its first-step residuals for Ux (1, then 6.29986e-4 against 6.29981e-4) and p_rgh (0.9930
against 0.9908), the latter's difference the starting pressure's and a serial against a parallel solve's, and the
diagnostics wrote their rows.
