# Ceiling heating against underfloor heating, from a night setback

A heated ceiling and a heated floor can give a room the same heat, but a heated ceiling gives
almost all of it as radiation, and warm air stays up under a warm ceiling. Does that leave you
cold at the ankles? This case takes [`underfloorVsRadiator`](../underfloorVsRadiator)'s room on
a still 0 °C morning, starts it at a 16 °C night setback, and warms it for twenty minutes with
the same 1400 W, once through the whole ceiling and once through the whole floor, with
radiation solved. It is about where the heat goes and how warm the room is and feels in the
first twenty minutes, not about heating bills, water temperatures or what a screed does over
hours.

    ./Allrun ceiling     # 1400 W through the whole ceiling, 0-1200 s from switch-on
    ./Allrun floor       # 1400 W through the whole floor, 0-1200 s

**The result.** After twenty minutes the air in the occupied zone is **18.2 °C at the ankles
with the heated ceiling and 23.4 °C with the heated floor**. The heated ceiling gives 95% of
its heat as radiation. Most of that goes into the walls and the floor, which store it, and the air
in the ceiling room's occupied zone does not reach 20 °C in the twenty minutes. The radiation
still counts: the ceiling room's operative temperature, the mean of the air and the mean
radiant temperature, is 20.1 °C at the ankles and 20.8 °C at seated head height, 1.9 K and
2.6 K above its air. The floor-heated room's air passes 20 °C in the whole occupied zone at
410 s. At 1200 s the air at seated head height is within 0.4 °C of the ankles' in both
rooms. Read
[What it cannot](#what-it-cannot) before any number here: the heated surfaces have no heat
capacity, so both start giving their full output at once, which flatters the floor.

The room, its mesh, its glass and its monitors are `underfloorVsRadiator`'s. It is a case of
its own because radiation is solved, every wall stores heat, the room starts at 16 °C and the
heat is 1400 W instead of 60 W. None of `underfloorVsRadiator`'s runs changes.

## The room

| | value | from |
|---|---|---|
| room | 4.0 m from the window wall to the inner wall, 3.5 m wide, 2.4 m high: 14.0 m² of floor and of ceiling, 33.6 m³ | underfloorVsRadiator |
| window | glass 1.0 m wide and 1.2 m tall, sill 0.90 m above the floor, centred in the wall, shut | underfloorVsRadiator |
| glass | ordinary air-filled double glazing, U = 2.8 W/m²K, to still air at 0 °C: h = 4.403 W/m²K to 0 °C outside, the inside film left to the solver; no heat capacity; emissivity 0.837 | underfloorVsRadiator; Rubin (emissivity) |
| heated surface | the whole ceiling (`ceiling`) or the whole floor (`floor`), **1400 W**, 100 W/m², with no heat capacity, from t = 0 | EN 1264 via Warmup |
| the other one | the floor in `ceiling`: 3/4 in (19 mm) wood. The ceiling in `floor`: 1/2 in (12.7 mm) gypsum board | CEC Table 5 |
| walls | the window wall around the glass, the inner wall and both side walls: 1/2 in gypsum board | CEC Table 5 |
| emissivity | 0.9 for every surface but the glass | EN ISO 6946 |
| start | the air at rest, the air, every surface and every wall layer at **16 °C** (289.15 K). At t = 0 the glass sees 0 °C outside and the heater is on at full output, constant, with no thermostat | Energuide |

**Why 16 °C.** Energuide, the Brussels energy site of the distribution operator Sibelga,
advises lowering a boiler-heated home to "around 16°C" at night or when away. The same page
advises a much smaller setback for underfloor heating, at most 1 °C, because a screed floor
responds slowly. Here the setback is the same for both rooms, and the floor has no screed to
heat (see [What it cannot](#what-it-cannot)).

**Why 1400 W.** 100 W/m² over the 14.0 m² heated surface. EN 1264 limits a floor in the
occupied zone to a surface 9 K above a 20 °C room, 29 °C, which its characteristic curve puts
at 100 W/m². That is the most a floor panel is designed to give, which suits a warm-up. EN 1264
sets no such comfort limit for a ceiling, so the floor's limit sets both. With the same 1400 W
a heated ceiling runs hotter than a floor, because it loses little to the air by convection.

**The walls store heat.** Every wall, the unheated floor or ceiling included, is a 1-D layer
of 24 slices with its heat capacity and an adiabatic back, starting at 16 °C: gypsum board
k = 0.1587 W/m K, ρ = 640.7 kg/m³, c_p = 1130 J/kg K; wood k = 0.1060 W/m K, ρ = 656.8 kg/m³,
c_p = 1884 J/kg K (California Energy Commission). In `underfloorVsRadiator` the inner and side
walls were held at 20 °C and the rest were insulated with no heat capacity; an insulated
massless surface would sit at radiative balance from the first second and have no starting
temperature at all. Here every interior surface starts at 16 °C and warms only as fast as its
layer takes the heat in.

## The model

`scripts/make_mesh.py` writes the mesh case and `scripts/make_case.py <run>` writes the run
from the files in `template/`. Coordinates are `underfloorVsRadiator`'s: x from the window wall
into the room, y up from the floor, z across the room from the middle of the window.

- **Solver:** buoyantPimpleFoam (OpenFOAM v2512), air as a perfect gas (c_p 1005 J/kg K,
  μ 1.82e-5 Pa s, Pr 0.71), k-omega SST with the buoyancy source on k (`buoyancyTurbSource`),
  wall functions, PIMPLE with 2 outer and 2 pressure correctors, Euler in time at Courant 1
  with steps of at most 0.1 s, `underfloorVsRadiator`'s schemes, its pressure reference in
  mid-room and its p_rgh tolerance of 1e-7.
- **Radiation:** fvDOM with nPhi 3 and nTheta 4, 48 directions, solved every 10 steps, each
  ray's solve capped at 10 sweeps. Grey, diffuse, opaque surfaces; the air neither absorbs nor
  emits. An even nTheta puts a band edge in the plane of the two side walls: at nTheta 3 the
  same room held at a uniform temperature gave the side walls a net +6.7 W/m² and every other
  surface about −2.8 W/m², where it should be zero everywhere; at nTheta 4 every wall's qr is
  below 4e-13 W/m².
- **The walls (`src/radLayerWall`).** Every wall's surface balances, face by face, conduction
  to the first air cell, its source (Q/A on the heated surface), the glass's film to 0 °C, the
  net radiation it absorbs (qr from the last fvDOM solve), and conduction into its layer. The
  surface's own emission is linearised about the temperature the last radiation solve saw,
  4εσT_r³ (T_r − T_w), so that between solves the surface temperature is implicit in its own
  radiative loss. Without that, qr held fixed for ten steps against a moving surface made the
  ceiling's temperature swing with growing amplitude in an early test (12.5, 41.8, −57.0,
  178.1 °C at successive radiation solves). The layer is implicit, 24 slices, adiabatic at the
  back, advanced from the step's starting state at every evaluation. The layers are written
  into T at each field write, so a run restarts with them.
- **The radiation at t = 0.** A room at one temperature is in radiative equilibrium: every ray
  is σT⁴/π. The solved runs started from `underfloorVsRadiator`'s room converged by fvDOM at a
  uniform 293.15 K, scaled by (289.15/293.15)⁴: every ray 126.170333 W/m² sr, G = 1585.50 W/m²
  (4σT⁴ is 1585.49), qr = 0. `make_case.py` writes those values.
- **Mesh:** `underfloorVsRadiator`'s, unchanged: one graded block of 66 × 83 × 68 =
  372,504 cells, 20 mm across the first 0.3 m from the window wall, 10 mm at the floor, 30 mm
  over the window band and under the ceiling; the glass cut out of the window wall by position
  (1,120 faces, 1.20 m²). `checkMesh`: OK, no non-orthogonality, largest aspect ratio 12.2.
- **The occupied zone** (ASHRAE 55): cells more than 1.0 m from the window wall and 0.3 m from
  the other walls, in bands within 0.02 m of 0.1 m (ankles, two layers of cells), 0.6 m, 1.1 m
  (seated head, one layer) and 1.7 m. ISO 7730 and EN 16798-1 take the vertical air
  temperature difference between 0.1 and 1.1 m for a seated person.
- **Mean radiant and operative temperature.** In each band, the mean radiant temperature is
  (G/4σ)^¼ from the band's mean incident radiation G, and the operative temperature is the mean
  of that and the band's mean air temperature. This is the band's mean irradiation, not what a
  seated person's body sees of the ceiling, the floor and the glass.
- **Monitors:** every step, the air's internal energy ((c_v/R) ∫p dV, for a closed perfect-gas
  box), the room's and each band's mean air temperature, the glass's, the ceiling's and the
  floor's surface temperatures, and every wall's heat (`wallHeatFlux`, convection plus net
  radiation) and net absorbed radiation (∫qr). Every 1.25 s, each band's mean T and G, eight
  probes, and three planes of T, U and G: the mid plane through the window (z = 0.005 m) and
  the whole room at 0.1 m and 1.1 m. Fields every 7.5 s, the last two kept.

## How the case got here

The case was set up and solved by a local OpenReynolds agent on our machine; `src/` and the
scripts are its files, tidied. An earlier solve of this pair, 60 W into a room whose inner and
side walls were held at 20 °C, was reviewed and not used: both rooms stayed at 20 °C and showed
nothing happening. These runs replace it as a warm-up from a setback. The linearised wall, the
converged t = 0 radiation and nTheta 4 come from that earlier solve's tests, before which a
one-core test of the ceiling run with the original wall condition diverged at 0.105 s.

A lumped model (an air node, the surfaces on a mean-radiant star, the same layers) put the
floor room's mean air at 20 °C after about 8 minutes and the ceiling room's after about 19,
which is why the window is 0-1200 s. The ceiling room came out slower than that model. Pilots
of 0-20 s on 8 ranks each projected 3.8 h (ceiling) and 5.0 h (floor) for 1200 s. Production
ran from t = 0 on 29 Oct 2026, both runs side by side on 8 ranks each, in one go.

## Checks

- **The generator against the solved runs.** From a clean copy, `./Allrun --setup-only ceiling`
  and `--setup-only floor` wrote the solved runs' meshes byte for byte (points, faces, owner,
  neighbour, boundary, the zones and every set), 372,504 cells, `checkMesh` OK. Every
  dictionary in `constant/` and `system/` is the solved runs' byte for byte but the comment line
  naming the case in `controlDict`. In `0/`, T, U, p, p_rgh, k, omega, nut, alphat and IDefault
  are byte for byte; the 48 rays and G hold the same values, written as uniform where the
  solved runs listed them cell by cell, and qr is 0 where theirs was below 4e-13 W/m². The
  solved runs reused the earlier solve's scotch decomposition, so a re-solve will not match the
  committed histories to the last digit.
- **The air's heat budget closes.** Over 0-1200 s the rise of the air's internal energy and the
  sum of every wall's convection into the air differ by −0.024 W (`ceiling`) against 81.9 W
  stored, and by −0.89 W (`floor`) against 172.9 W.
- **The heat adds up.** In each run, what the layers took in, what the air stored and what
  left through the glass add up to 1.679 MJ, against the heated surface's 1.680 MJ (1400 W ×
  1200 s is 1.68 MJ). The layers' own stored heat, read from the layer temperatures in T at
  1200 s, agreed with the heat that crossed each wall to within 0.03%.
- **The heated surface gives its 1400 W:** 1399.8 W over the run in both. `wallHeatFlux`
  counts the radiation the last fvDOM solve saw, not the surface's own extra emission between
  solves, so while a surface warms it reads up to 0.4% low.
- **Radiation is conserved:** the sum of qr over all six walls averages −0.35 W (`ceiling`)
  and −0.13 W (`floor`) over the run, against 1337 W and 969 W radiated.
- **Both runs ended cleanly** at 1200 s, in 13,173 steps (`ceiling`, mean step 0.091 s) and
  22,857 (`floor`, 0.053 s).

## Results

From `results/summary.txt`, `results/minutes.csv` and `results/<run>/history.csv`, which
`scripts/extract_results.py` writes from the runs' monitors.

**At 1200 s, in the occupied zone:**

| °C | heated ceiling | heated floor |
|---|---:|---:|
| air at the ankles, 0.1 m | **18.15** | **23.41** |
| air at seated head height, 1.1 m | 18.22 | 23.09 |
| air at standing head height, 1.7 m | 18.55 | 23.14 |
| mean radiant temperature at the ankles / head | 22.00 / 23.46 | 26.43 / 23.05 |
| operative temperature at the ankles | 20.07 | 24.92 |
| operative temperature at seated head height | 20.84 | 23.07 |
| the room's mean air | 19.41 | 23.14 |
| the heated surface, mean (warmest face) | ceiling 37.68 (38.93) | floor 33.23 (36.41) |
| the unheated floor or ceiling, mean (warmest face) | floor 19.17 (20.44) | ceiling 20.02 (21.34) |
| the glass's inside surface | 14.32 | 13.93 |

**How fast**, the air at the ankles and at seated head height, °C:

| | 60 s | 120 s | 300 s | 600 s | 900 s | 1200 s |
|---|---:|---:|---:|---:|---:|---:|
| heated ceiling | 16.1 / 16.1 | 16.2 / 16.2 | 16.5 / 16.5 | 17.0 / 17.1 | 17.6 / 17.6 | 18.2 / 18.2 |
| heated floor | 16.7 / 16.9 | 18.2 / 17.6 | 19.8 / 19.3 | 21.5 / 21.1 | 22.5 / 22.2 | 23.4 / 23.1 |

- **The floor-heated room** warms from the floor up. Its ankle air passes 20 °C at 329 s and
  its head-height air at 410 s, and both stay above it; the operative temperature passes 20 °C
  at 82 s at the ankles and 317 s at the head. It then keeps going, to 23.4 °C at the ankles:
  1400 W with no thermostat overshoots. In the first minute the ankle air rises to 17.8 °C at
  30 s and falls back to 16.7 °C at 60 s as the first plumes mix the room.
- **The ceiling-heated room** warms slowly and evenly. Its occupied zone's air gains about
  2.1 K in twenty minutes and is within 0.07 K from ankles to seated head at 1200 s. The warm
  air stays above head height: 18.6 °C at 1.7 m, 23.2 °C at a probe 0.2 m under the middle of
  the ceiling, and a thin layer against the 37.7 °C ceiling. The air does not reach 20 °C in
  the twenty minutes, but its operative temperature passes 20 °C at 800 s at seated head height
  and at 1164 s at the ankles.
- **The floor under the heated ceiling** warms from 16 to 19.2 °C on average, 1.0 K above the
  ankle air over it at 1200 s: at that point it absorbs 450 W of the ceiling's radiation and
  passes part of it to the air. Its 19 mm of wood has taken in 0.48 MJ, 29% of the heat put in.

**Where the heated surface's heat goes**, W:

| | convection into the air | net radiation | radiation's share |
|---|---:|---:|---:|
| heated ceiling, run mean | 63 | 1337 | 95.5% |
| heated ceiling, at 1200 s | 44.5 | 1355.5 | 96.8% |
| heated floor, run mean | 431 | 969 | 69.2% |
| heated floor, at 1200 s | 410 | 990 | 70.7% |

**Where the 1.68 MJ is at 1200 s**, MJ:

| | air | unheated floor or ceiling | window wall | inner wall | side walls | all the layers | out through the glass |
|---|---:|---:|---:|---:|---:|---:|---:|
| heated ceiling | 0.098 (6%) | floor 0.479 (29%) | 0.204 | 0.243 | 0.570 | 1.496 (89%) | 0.085 (5%) |
| heated floor | 0.208 (12%) | ceiling 0.427 (25%) | 0.194 | 0.239 | 0.531 | 1.390 (83%) | 0.081 (5%) |

Most of the heat goes into the walls in both rooms; the floor-heated room puts about twice as
much into its air.

**The floor's surface against EN 1264.** The heated floor's mean passes 29 °C at 2.8 s, falls
back to 28.8 °C around 50 s as the first plumes sweep it, and stays above 29 °C from 60 s. It
is 30.9 °C (warmest face 34.1 °C) at 410 s, when the occupied zone reaches 20 °C, about 10.8 K
above the room's mean air, where EN 1264's curve, q = 8.92 ΔT^1.1 W/m², gives 9 K at
100 W/m². It ends at 33.2 °C (36.4 °C) once the room has overshot. The 100 W/m² is the input;
the surface temperature is the result.

## What the clip shows, and what it does not

The clip shows the mid plane through the middle of the window, the heated ceiling above and
the heated floor below, from switch-on to 1200 s, coloured by air temperature on one scale
from 16 to 28 °C, with moving air parcels and the ankle air in whole degrees on each panel. It
shows air temperature only: the ceiling room's radiant warmth, which puts its operative
temperature 1.9-2.6 K above its air, is not in the colours. It is one vertical section through
a 3-D run.

## What it cannot

- **A screed's warm-up.** Both heated surfaces have no heat capacity and give 1400 W from the
  first second. A real wet underfloor system has a screed to heat before its surface warms,
  which takes far longer than twenty minutes, and a real heated ceiling has its own panel to
  heat. This is a best case for the floor, which is why Energuide advises setting underfloor
  heating back by at most 1 °C rather than to 16 °C.
- **A thermostat.** Both run flat out; the floor room overshoots to 23 °C.
- **Comfort as a body feels it.** The mean radiant and operative temperatures are band means
  of the incident radiation, not a seated person's view of a hot ceiling, a warm floor and a
  cold window. The radiant asymmetry under a warm ceiling, which ISO 7730 limits separately,
  was not computed.
- **The floor's surface temperature.** It runs above EN 1264's 29 °C for nearly the whole run
  and 1-1.8 K warmer than the standard's curve gives for its output. A real floor at 100 W/m² is
  designed for a room at 20 °C, not one warming from 16 °C.
- **Only the glass loses heat outside.** Every wall stores heat behind an adiabatic back and
  loses none; real outside walls would lose more, and a real room more slowly reaches 20 °C.
- **Twenty minutes.** The ceiling room is still warming, about 0.11 K a minute at the ankles,
  and its air does not reach 20 °C in the run.
- **One cool cell.** On the mid plane one cell in the middle of the room, at x 2.04 m,
  y 1.19 m, sits 0.4-0.6 K below its neighbours in both runs. It is the pressure reference
  cell (`pRefPoint` in `system/fvSolution`); it shows on the plane as a faint dark dot.
- **An empty room.** No furniture, people, open door, ventilation or leaks, no wind and no sun.
- **One mesh, unsteady RANS,** k-omega SST with wall functions, 48 radiation directions solved
  every 10 steps, no mesh, angle or time-step study, one realization of each run.

## Sources

- Energuide (Sibelga), "How to set your thermostat efficiently?" (the 16 °C night setback for
  boilers; at most 1 °C for underfloor heating), opened 29 Oct 2026:
  https://energuide.be/en/questions-answers/how-do-i-set-my-thermostat/620
- Warmup PLC, "Floor Finishes" (BS EN 1264: a floor surface at most 9 K above a 20 °C room,
  29 °C, about 100 W/m²), opened 29 Oct 2026: https://pro.warmup.co.uk/?p=3536
- Vogel & Noot, FLOORTEC technical information, after ÖNORM EN 1264 (the base curve
  q = 8.92 ΔT^1.1): https://www.vogelundnoot.com/static_files/at/media/downloads/Floortec_technische_informationen.pdf
- California Energy Commission, Reference Appendices, "2.3 Building Materials and
  Construction", Table 5 (gypsum board 1/2 in and wood 3/4 in: k, ρ, c_p).
- M. Rubin, "Optical properties of soda lime silica glasses", Solar Energy Materials 12, 1985
  (the glass's emissivity, 0.837): https://eta-publications.lbl.gov/bibcite/reference/23873
- EN ISO 6946:2017, Annex C (emissivity 0.9 for ordinary building surfaces).
- ISO 7730, EN 16798-1 and ASHRAE 55 for the ankle and head heights and the occupied zone, as
  cited by B. W. Olesen, REHVA Journal 06/2024, Table 2:
  https://www.rehva.eu/rehva-journal/chapter/european-standardisation-on-thermal-environment
- The room, the glass and its U-value: [`underfloorVsRadiator`](../underfloorVsRadiator),
  [`windowAiring`](../windowAiring) and [`radiatorUnderWindow`](../radiatorUnderWindow), with
  their sources.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with `wmake` and MPI, and
Python 3; `scripts/extract_results.py` also needs NumPy.

    cd cases/ceilingVsUnderfloor
    ./Allrun ceiling             # [nProcs], default 8
    ./Allrun floor
    python3 scripts/extract_results.py runs results

`Allrun` compiles `src/radLayerWall` into `$FOAM_USER_LIBBIN`, writes and meshes the shared
mesh in `runs/mesh` once (blockMesh, the glass cut out of the window wall by topoSet and
createPatch, the occupied zone's bands, checkMesh), writes the run into `runs/<run>/` with
`scripts/make_case.py`, writes the planes at t = 0 from the initial fields, decomposes it,
solves 0-1200 s and, once both runs have solved, writes `results/`. `./Allrun --setup-only
<run> [nProcs]` stops before the solve, in under half a minute; `./Allclean` removes the runs.

The runs took 9,517 s (2.64 h, `ceiling`) and 20,386 s (5.66 h, `floor`) of wall time side
by side on 8 ranks each. Each writes 960 sets of three planes, about 1 MB a set, and about
20-30 MB of monitors. `results/` holds each run's history every 2.5 s (the occupied zone's
air, mean radiant and operative temperatures, the room's mean, the surfaces, the heated
surface's convection and radiation, the glass's loss and the heat in the air and in each
layer), the minutes and the summary; no fields, meshes, planes or logs.

The case was set up and solved by an agent on our own machine and checked by us. The files in
`results/` are what `scripts/extract_results.py` wrote from those two runs.
