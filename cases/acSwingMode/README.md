# The same wall unit cooling a bedroom: its vane on swing, against held still

A wall-mounted split unit's remote has a swing button, and owners split over it. One camp leaves the vane sweeping:
Mitsubishi's manual says to "use the swing operation for the air flow to reach all corners of the room", and Daikin's
Spanish site says "the swinging motion distributes the air evenly, eliminating excessively hot or cold areas". The
other camp picks one angle and leaves it there, and so do the makers' own cooling settings: on Mitsubishi's remote
AUTO in cooling means "The vane automatically moves to horizontal position. It will not swing.", Daikin's COMFORT
AIRFLOW holds the flow "in the upward direction while in COOL and DRY operation ... which will provide a comfortable
airflow that will not come in direct contact with people", and a seller's guide says to "lock them horizontally to
avoid blowing directly on a sofa or bed" (TURBRO). This case is [`acLouvreAngle`](../acLouvreAngle)'s unit, cooling
again, switched on in a bedroom closed up all day on a hot night, twice: once with the vane held 10° below horizontal
and once swinging between 10° and 40° down every 24 s. It asks where the cold air goes in the first three minutes and
what reaches someone lying on the bed, their head against the far wall. It is about where the cold air goes, not
running cost, noise, humidity, sleep modes or the unit's thermostat.

    ./Allrun held     # the vane held 10 degrees below horizontal, 0-180 s from switch-on
    ./Allrun swing    # the vane sweeping 10-40-10 degrees below horizontal, 24 s a cycle, 0-180 s

**The result.** **With the vane on swing the air at the sleeper's face is colder for most of the three minutes,
and it moves faster.** Held at 10° down, the cold jet runs high across the room under the ceiling, turns down the
headboard wall and washes back along the bed from the head end, so the face, at the head of the bed, sits where it
turns. On swing the jet sweeps between that path and the foot of the bed and back, once every 24 s, and crosses the
bed on the way down and on the way back. Over 1:30-3:00 **the air at the face is 1.12 K colder on swing**, 20.18
against 21.30 °C (68.3 against 70.3 °F), **and it moves at 0.61 against 0.39 m/s**; at the torso it is 1.74 K colder
(19.99 against 21.73 °C) at 0.78 against 0.35 m/s, and at the feet 1.52 K colder (20.36 against 21.88 °C).
Unrounded, the face is colder on swing for 89% of the run and at every write from 2:16.5 to the end; on the clip's
rounded number, held is the warmer on 320 of the 481 frames, the two are equal on 145, and swing is the warmer on 16.
Swing's numbers rise and fall with each sweep; held's fall almost steadily. **The brief expected the opposite**: it
left the answer open, but its guess was that the held stream, coming down the headboard wall onto the pillow end of
the bed, would make the face colder with the vane held. In this room it did not. **Nor does the run say whether
colder, draughtier air at a sleeper's face is better or worse**: it gives air
temperature and speed, not comfort. Read [What it cannot](#what-it-cannot) before any number here: **the room is
sealed, with no furniture, window, person or leakage, and cools at constant volume**; **the unit runs flat out at
its rated capacity with no thermostat and a coil cold from the first second**, so **the cool-down, from 32 to about
20 °C at the face in three minutes, is far faster than a real bedroom's**; **the sleeper is drawn in the video, not
modelled**; **it is half a room on a symmetry plane**; and **the swing's 24 s period comes from a Daikin patent,
since no maker publishes one, and its range is Daikin's 10-40° down**.

The unit, its box, its intake and the way its cooling is put into the air are [`acLouvreAngle`](../acLouvreAngle)'s,
at 32 °C instead of 30 °C. The outlet is new: one opening round the box's front-bottom corner that every vane angle
can use. The bedroom and the bed are new. The walls, floor and ceiling that store heat are
[`acHeatingLouvre`](../acHeatingLouvre)'s `storedLayerWall79` under a new name (from
[`closedRegister`](../closedRegister)'s `storedLayerWall`), and the castellated mesh with the solids cut out on cell
faces is [`airPurifierCorner`](../airPurifierCorner)'s method, as in both.

## The room

x runs from the unit's wall into the room, y up from the floor, z across the room from its centreline; metres.

| | value | from |
|---|---|---|
| room | 3.60 m from the unit's wall to the headboard wall, 3.36 m wide, 2.40 m high: about 11.8 x 11.0 ft with an 8 ft ceiling, a common bedroom | ours |
| half model | z = 0 to 1.68 m, a symmetry plane at z = 0 through the middle of the unit and the bed | ours |
| bed | a queen bed, 2.00 m long and 1.60 m wide, its head against the far wall, facing the unit: in the half model x 1.60-3.60, y 0-0.56, z 0-0.80 m, the mattress top 0.56 m (22 in) above the floor; a solid block to the floor (a divan base), no pillow, headboard or bedding; adiabatic | ours |
| walls, ceiling | 12.7 mm gypsum board, k 0.1587 W/m K, ρc 723,991 J/m³ K, in 24 layers behind the surface, adiabatic back | ρ and c_p from the California Energy Commission, as [`ceilingVsFloorVent`](../ceilingVsFloorVent) |
| floor | 19 mm wood, k 0.106 W/m K, ρc 1,237,411.2 J/m³ K, the same way | the same |
| start | the air at rest at 32 °C (89.6 °F), every surface and layer at 32 °C, in isothermal hydrostatic balance with 1e5 Pa at y = 1.21 m: a bedroom closed up all day on a hot night | |

**There is no person.** Someone lying on their back on the symmetry plane, head at the far wall and feet toward the
unit, is three boxes of air the monitor averages over: the **face** at x 3.16-3.40, y 0.64-0.88, z 0-0.12 m, the
**torso** at x 2.44-3.04, y 0.60-0.84, z 0-0.24 m, and the **feet** at x 1.68-1.96, y 0.60-0.76, z 0-0.20 m, at the
foot of the bed. A body's heat and shape would add a plume of their own that the question does not need. They are air
temperatures and speeds, not skin temperatures. Five more zones are averaged: the layer over the bed (x 1.60-3.60, y
0.56-0.96, z 0-0.80 m), the occupied zone (x 0.60-3.60, y 0.10-1.80, z 0-1.50 m), the floor layer (y < 0.10 m), the
ceiling layer (y > 2.20 m) and the whole room.

**The surfaces store heat** (`src/storedLayerWall80`): each face of the walls, floor and ceiling is a massless surface
over a 1-D layer of 24 slices with its heat capacity and an adiabatic back, all at 32 °C at the start. A room closed up
on a hot day has warm surfaces, and they give heat back to the air as it cools: by 3:00 the walls, floor and ceiling
give the air 1,021 W (held) and 1,022 W (swing), three quarters of what the unit takes out. In 180 s heat reaches
about √(αt) ≈ 6 mm into the gypsum and 4 mm into the wood, so what lies behind them hardly matters. There is no window,
no outside wall, no radiation and no furniture but the bed.

## The unit

**A Mitsubishi MSZ-GS12NA-U1**, [`acLouvreAngle`](../acLouvreAngle)'s 12,000 BTU/h wall unit, cooling, from its
submittal sheet:

| | value | from |
|---|---|---|
| size | 798 x 232 x 295 mm (W x D x H), drawn as a box 0.80 x 0.24 x 0.30 m so its edges lie on the mesh; in the half model x 0-0.24, y 2.00-2.30, z 0-0.40 m, its top 0.10 m below the ceiling | the submittal sheet, rounded |
| air | 343 CFM, the top of its wet-coil cooling range (121-144-200-276-343 CFM), as a unit starting in a hot room runs: **0.0924 kg/s in the half room** at 32 °C | the submittal sheet |
| cooling | 12,000 BTU/h (3.52 kW) at a sensible heat factor of 0.77: **2.71 kW sensible for the whole unit, 1,354 W in the half room** | the submittal sheet |
| intake | the grille on its top, x 0.02-0.22 m, z < 0.38 m (0.076 m² in the half room) | `acLouvreAngle` |
| outlet | one opening round the front-bottom corner: a strip of the front face, x = 0.24 m, y 2.00-2.06 m, z < 0.30 m (0.018 m²), and a strip of the underside at its front edge, y = 2.00 m, x 0.20-0.24 m, z < 0.24 m (0.0096 m²), one patch of 0.0276 m² in the half room | ours |

**The cooling is a fixed sensible load.** The air leaves at the intake's mean temperature less Q/(ṁ cp) =
1354/(0.0924 x 1005) = 14.58 K, by OpenFOAM's `outletMappedUniformInletHeatAddition` with Q = -1354 W, from t = 0:
at 32 °C in, it leaves at 17.30 °C (63.1 °F) at 3 s, and by 180 s at 7.82 °C (held) and 8.03 °C (swing) as the room
cools, since the model keeps the coil's 14.58 K drop all the way down. The intake draws 0.0924 kg/s out
(`flowRateOutletVelocity`), and the outlet blows the same mass back in. The unit is taken as running at its rating and
top fan from switch-on with its coil already cold; a real unit's fan, compressor and coil take time to get there, it
removes moisture as well as heat, and it throttles back near its set point. None of that is modelled.

## The vane: held and swinging

The two runs differ only in whether the vane moves. A vane turns the jet without changing the fan's flow, so both
runs carry the same mass flow through the same outlet.

- **held**: the jet leaves **10° below horizontal** for the whole run. This is the top of Daikin's cooling swing and
  Daikin's COMFORT AIRFLOW position, which its manual's figure puts at the swing's upper limit. It is a little below
  Mitsubishi's horizontal AUTO and TURBRO's "lock them horizontally".
- **swing**: the jet's angle sweeps **from 10° to 40° below horizontal and back** as a triangle wave, 12 s each way
  with no pause at either end, **a 24 s cycle** (2.5° a second), starting at the top at t = 0 and moving down; 7.5
  cycles in the run. The range is Daikin's CTXS/FTXS cooling auto-swing (10° to 40°, labels on a figure in its service
  manual, read as angles to the horizontal; the text does not define the reference). **No maker publishes a wall
  unit's swing period.** The 24 s is the one stated figure found, a Daikin patent's description of an unnamed
  commercial unit ("it takes 12 seconds for the flap to transition either from horizontal blowing to downward
  blowing or from downward blowing to horizontal blowing ... horizontal blowing and downward blowing are repeated in
  24 second cycles"). Other makers' ranges differ: Mitsubishi Heavy's SRK wall units sweep about 25° to 60° from
  horizontal in cooling, and Toshiba's RAS-10N3KV 35° about its stop position. A faster or slower sweep would change
  how often the jet passes, and this case does not say how much it would change where it goes.

A swinging jet needs one outlet that every angle can use. [`acLouvreAngle`](../acLouvreAngle) used a separate slot
for each angle, since its front slot alone would have blown 1.9 times faster at 60° down to carry the same flow. Here
the outlet wraps the corner, and the jet is a `codedFixedValue` that points the velocity along the vane, gives each
outlet face flow in proportion to d · n where d · n > 0 (d the vane's direction, n the face's normal into the room),
and scales it every evaluation to 0.0924 kg/s at the patch's own density. The area the jet sees, Σ A (d · n), is
0.0194 m² at 10°, 0.0204 m² at 25° and 0.0200 m² at 40°, within 5% over the sweep, so the jet leaves at about the same
speed, 3.8-4.0 m/s, at every angle and every face carries flow throughout. The vane's blade is not resolved: the
direction is imposed at the outlet. The flow-weighted direction of the air over the first 4 cm outside the outlet is
**9.11-9.64° down** in the held run from 0.375 s on, and from 1 s on it trails the imposed angle by 0.36-0.89° (held)
and 0.23-0.65° (swing), always a little shallower.

## The model

`buoyantPimpleFoam` (OpenFOAM v2512), compressible air as a perfect gas (Cp 1005 J/kg K, molar mass 28.96, μ
1.82e-5 Pa s, Pr 0.71), k-ω SST with `buoyancyTurbSource` and wall functions (`kLowReWallFunction`,
`omegaWallFunction`, `nutkWallFunction`, `alphatJayatillekeWallFunction`); the jet at 5% intensity and a 1 cm
mixing length. Euler in time, adaptive steps at Courant 1 (maxDeltaT 0.05 s; 4.26 ms (held) and 3.93 ms (swing) on
average, 42,251 and 45,824 steps), limitedLinearV for U, limitedLinear for h and bounded upwind for k and ω, two outer
and two pressure correctors, p_rgh by GAMG to 1e-7 with the final solve capped at 100 iterations (no step reached it),
the pressure reference at (1.21, 1.21, 1.21) m, strictly inside one cell, with pRefValue 1e5 Pa. No radiation. The
unit's casing and the bed are adiabatic; the walls, floor and ceiling are `storedLayerWall80` (above).

**One function object changes the boundaries, not only reads them.** `thermalBoundarySync` (in `system/functions`,
written by `make_case.py`) re-evaluates the intake's and the outlet's temperature at the end of every step and sets
their enthalpy from it, so that the next step's supply is the intake's current temperature less 14.58 K. Without it,
the second pair of 1 s tests removed 1,335-1,388 W at the start in place of 1,354 W (the pressure correction can
change the intake's temperature after the energy solve, as the object's own comment says); with it the heat removed
reads 1,354.000 W at every write of both runs. It changes no internal field, and no flow, heat or angle setting. Why
`acLouvreAngle`'s and `acHeatingLouvre`'s runs held their heat without it was not established.

**The mesh** (`template/mesh/system`, `scripts/make_mesh.py`, `scripts/unit_patches.py`): a background of 8 cm
cubes (blockMesh, 45 x 30 x 21), refined by snappyHexMesh, castellated only, without snapping or layers: 2 cm round
the unit (its surface and a box x < 0.48, y > 1.84, z < 0.48 m), 4 cm under the ceiling (y > 2.08), through the
sweep's region in front of and below the unit (x < 2.20, y > 0.56, z < 0.56), along the floor (y < 0.16), over the
bed (x > 1.60, y 0.56-1.04, z < 0.88), down the headboard wall (x > 3.44, y > 0.56, z < 0.64) and on the bed's
surface, 8 cm elsewhere, two cells between levels. The unit and the bed are each one closed STL written by
`make_mesh.py` on the mesh's own faces, so they are cut out exactly. snappyHexMesh leaves the unit as one patch;
`unit_patches.py` moves its faces into `intake` and `outlet` by face centre and checks their areas, each outlet
strip's normal and the bed's area (3.168 m² exposed: 1.600 top, 0.448 foot, 1.120 side) to 1%. **111,298 cells**
(108,027 hexahedra and 3,271 polyhedra where the levels meet), an air volume of 13.5904 m³ (the half room less the
unit's 0.0288 and the bed's 0.896 m³); `checkMesh` OK, non-orthogonality at most 25.24°, skewness at most 0.33,
aspect ratio 1. One mesh, no mesh study.

**The monitors** (`scripts/monitor.C`, a coded function object, every step, one row at the first step and then every
0.375 s into `postProcessing/metrics/metrics.csv`): the outlet's and the intake's mass flows each way and
temperatures, the outlet's largest face flux (to show no face ever draws air in), the vane's imposed angle and the
jet's measured direction, the air's mass and internal energy (cv/R)∫p dV, its coldest and warmest cell and where they
are, the mean temperature and mean speed |U| of the eight zones, and for each wall, the floor and the ceiling the heat
it gives the air, its mean surface temperature, the heat its layers hold relative to the start (read from the layers
themselves) and the heat summed step by step; and the heat the unit removes and its sum. The wall heat is the energy
equation's own flux, captured by a diagnostic `fvOptions` entry that changes nothing. The twelve cells of highest
Courant number go to `courant.csv`. And (`planes`) the section, which is the symmetry plane z = 0, and plans at the
floor (0.10 m), the sleeper's face (0.76 m), a standing person's head (1.60 m) and under the ceiling (2.30 m), each
with T and U, every 0.375 s from t = 0, 481 a run.

## Results

`results/summary.txt`, `results/zones.csv` and `results/<run>/history.csv` (every 1.5 s), from
`scripts/extract_results.py`. Means over an interval are time-weighted. The swing run's imposed angle at the times in
the table is 32.5° at 9 s, 25° at 30, 90 and 150 s, 40° at 60 and 180 s and 10° at 120 s.

| °C | 9 s | 30 s | 60 s | 90 s | 120 s | 150 s | 180 s | 90-180 s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| face, held | 28.66 | 28.02 | 25.19 | 22.89 | 21.77 | 20.90 | 19.72 | **21.30** |
| face, swing | 27.68 | 26.15 | 24.83 | 22.35 | 20.56 | 18.53 | 19.13 | **20.18** |
| torso, held | 29.81 | 28.60 | 25.62 | 23.47 | 22.20 | 21.24 | 20.13 | **21.73** |
| torso, swing | 26.91 | 27.05 | 24.32 | 21.29 | 20.12 | 18.35 | 18.78 | **19.99** |
| feet, held | 30.87 | 28.70 | 25.78 | 23.70 | 22.35 | 21.29 | 20.31 | **21.88** |
| feet, swing | 29.38 | 28.35 | 21.81 | 24.06 | 21.17 | 20.54 | 16.17 | **20.36** |
| room, held | 30.96 | 28.91 | 26.53 | 24.66 | 23.19 | 22.02 | 21.04 | 22.66 |
| room, swing | 30.95 | 28.89 | 26.46 | 24.55 | 23.02 | 21.79 | 20.76 | 22.46 |

| over 90-180 s | held | swing |
|---|---:|---:|
| air speed at the face, m/s | 0.395 | 0.613 |
| air speed at the torso, m/s | 0.346 | 0.784 |
| air speed at the feet, m/s | 0.280 | 0.469 |
| layer over the bed, y 0.56-0.96 m, °C | 21.78 | 20.66 |
| occupied zone, °C | 22.34 | 22.00 |
| floor layer, y < 0.1 m, °C | 23.30 | 22.84 |
| ceiling layer, y > 2.2 m, °C | 23.50 | 23.51 |

**Where the cold air goes.** Held, the jet leaves the corner at 10° down and sinks slowly as it crosses the room
under the ceiling. Of three streamlines traced through the section at 90 s and at 180 s, seeded just outside the
outlet, two come within 10 cm of the headboard wall at 0.90-1.11 m up and turn down it, and all three pass 8 cm above
the mattress at x 3.38-3.47 m, at the head of the bed, before running back along the bed toward its foot (they are
instantaneous streamlines on the plane, not the paths of parcels). At 30 s the stream still came down short of the
wall, crossing 8 cm above the mattress at x 2.83-3.00 m. On swing, the stream lands at the foot of the bed as the
vane reaches the bottom of its sweep: in each 24 s cycle the speed at the feet peaks at 1.29-1.41 m/s with the vane
at 34-40° down, against at most 0.37 m/s held over 90-180 s. On the way down and again on the way back up, as the
vane passes about 20-30°, the stream crosses the torso (up to 1.15-1.29 m/s in each cycle) and the face (up to
0.78-0.93 m/s in each cycle, against at most 0.46 m/s held over 90-180 s). At 12 s, the first time the vane reaches
40°, the feet are already at 25.93 °C and 1.20 m/s on swing against 30.11 °C and 0.15 m/s held. The section planes
differ by more than 1 K over 51.1% of the section at 9 s, 46.1% at 30 s, 50.8% at 90 s and 62.6% at 180 s, with an
rms difference of 2.2-2.9 K beyond 0.5 m from the unit.

**The face, the torso and the feet.** Unrounded, from the first write at 0.375 s, the face is colder on swing at 427
of the 480 writes, 88.9% of the time; the lead changes hands 18 times, held is as cold or colder at the other 53
writes, the last at 136.125 s, and swing holds it from there to the end. The torso is colder on swing at 469 writes
(97.7% of the time), held last as cold or colder at 110.625 s; the feet at 353 (73.5%), held last as cold or colder
at 147.375 s, since the feet warm back up between the stream's passes over the foot of the bed. The lowest face
reading is 19.72 °C at 180 s held (0.398 m/s), and 17.75 °C at 174 s on swing (0.779 m/s), sampled every 0.375 s.
At 180 s the face is 19.72 against 19.13 °C (67.5 against 66.4 °F), the torso 20.13 against 18.78 °C and the feet,
under the stream at the bottom of its sweep, 20.31 against 16.17 °C.

**The number on the clip.** The clip's number is the face's air temperature in °C, rounded to the degree. Both
rooms start at 32; then held against swing, 29/28 at 0:09, 28/26 at 0:30, 25/25 at 1:00, 23/22 at 1:30, 22/21 at
2:00, 21/19 at 2:30 and 20/19 at 3:00. The rounded numbers first differ at 4.875 s. Of the 481 writes, held's rounded
number is higher at 320, equal at 145 and lower at 16.

**The rooms and the surfaces.** The two rooms cool nearly alike: the room's mean air is 21.04 °C held and 20.76 °C on
swing at 180 s (0.28 K apart), and the occupied zone 0.34 K apart over 90-180 s. The walls, floor and ceiling give
the air 1,021 W (held) and 1,022 W (swing) of the 1,354 W at 180 s, and by then their layers have given up 121.7 and
118.6 kJ; the held room's ceiling gives more (210 against 152 W at 180 s) and the swinging room's floor more (226
against 171 W).

**Checks.** The outlet and the intake carry 0.0924000 kg/s at every write of both runs, the outlet's largest face
flux stays negative (into the room) at every write, so no outlet face ever drew air in, the swinging one included,
and the heat removed reads 1,354.000 W at every write from 0.375 s, the supply 14.58 K below the intake. The heat
budget over 10-180 s, the fall of the air's internal energy and of the heat in the surfaces' layers against the heat
the unit removed, closes to **-0.039%** (held) and **-0.057%** (swing) of the heat removed. The air's mass reads
15.512453194 kg at every row of both runs (the first step took it 9.0e-7 of itself away from the t = 0 fields, and it
did not move after). No air is warmer than the 32 °C start by more than 0.149 K, at the first step, in a cell just
above the outlet at (0.27, 2.07, 0.01) m; from 0.375 s on by at most 0.031 K (held) and 0.131 K (swing, at 9 s,
against the headboard wall beside the bed). No air is colder than the supply by more than 0.027 K (held) and 0.067 K
(swing). These are below the 0.2 K the study set itself for reporting such an excursion, are reported, and were not
tuned. No final pressure solve reached its 100-iteration cap, and no field was bounded.

## What the clip shows, and what it does not

The clip shows the section, the symmetry plane through the middle of the unit and the bed, the whole bedroom in both
panels on every frame, stacked, the fixed vane above and swing mode below, **from switch-on to 3:00 of the solve** at
nine times speed in 20 s, one frame a plane write. It is coloured by air temperature from 30 °C (red) to 20 °C (blue),
with moving air parcels, the bed, a drawn pillow and a sleeper lying on their back, a clock, the question "Air
conditioner: swing mode or fixed?" and under it "a follow-up: you asked for swing mode". The vane is drawn on every
frame at the run's own imposed angle, and a white arc in the swing panel shows its range from the first frame. Each
panel carries one rounded number, the air at the sleeper's face in °C.

- **The number is the face, not the feet or the torso.** The torso shows the larger gap; the face is the body
  height of someone lying in bed. The number does not say that swing is better, only that the air there is colder,
  and on swing it is also faster.
- **The colour scale is clipped at both ends.** The room starts at 32 °C and shows as the 30 °C red until it cools
  below 30, while the number reads 32 from the first frame; the jet near the unit is colder than 20 °C, so its core
  saturates.
- The unit, its vane, the pillow and the sleeper are drawn; only the bed's block is in the model. The parcels are
  moved through the planes' velocity after the solve; they are not solved particles.

## What it cannot

- **The cool-down is far too fast for a real bedroom.** The face goes from 32 to about 20 °C (89.6 to about 68 °F)
  in three minutes. **The room is sealed**: no window, no leakage, no outside wall loss (the layers' backs are
  adiabatic), **no furniture but the bed, no person**, no radiation. **The unit runs flat out** at its rated
  12,000 BTU/h and top fan, in a bedroom of 11.8 x 11.0 ft, **with no thermostat**, and **its coil is cold from the
  first second**: a real unit takes time to cool its coil and would throttle back near its set point. The supply
  falls to about 8 °C (46 °F) by 3:00 because the model keeps the coil's 14.58 K drop as the room cools. A sealed
  room also cools its air at constant volume, about 40% faster than a leaky one at constant pressure. Both runs share
  all of this, so the comparison between them should hold better than the absolute temperatures, which are not what
  a real room reaches.
- **The sleeper is drawn in the video, not modelled.** There is no body heat and no body in the flow: no plume off
  the person, no blocking of the stream, no pillow or bedding. The face, torso and feet are boxes of air.
- **It is half a room on a symmetry plane**, z = 0 through the middle of the unit and the bed. The jets cannot wander
  sideways, which a real jet does slowly, there is no left-right swing, and the clip's section is that plane, which
  keeps the jet's core.
- **The swing's period and range are borrowed.** No maker publishes a wall unit's swing period; the 24 s cycle is a
  Daikin patent's figure for an unnamed commercial unit, and the 10-40° range is Daikin's CTXS/FTXS cooling swing,
  both borrowed for a Mitsubishi unit. A different period or range would put the stream over the sleeper at different
  times and places.
- **The vane is a direction imposed at an outlet**, not a maker's vane: no blade, no auto mode, no
  dew-prevention change of angle. The held angle is the top of the swing, 10° down; [`acLouvreAngle`](../acLouvreAngle)
  compared held angles, and a held vane aimed lower would put its stream elsewhere.
- **It does not judge comfort.** The case gives air temperature and speed, not comfort or sleep. Air at 0.6-0.8 m/s feels
  cooler than still air at the same temperature, and whether a sleeper wants that draught on the face is not something
  the model shows.
- **The cooling is sensible only.** No humidity, no condensation, no moisture removed, though a real unit's latent
  load is 23% of its capacity at this rating (a sensible heat factor of 0.77).
- **One room, one layout, three minutes.** The bed's head is against the far wall, facing the unit. Over an hour
  both rooms cool through, and the difference is in how long the sleeper lies in moving cold air, not where the room
  ends up.
- **RANS, one mesh.** k-ω SST on a stepped castellated mesh of 111,298 cells, 2-8 cm, with wall functions. No mesh
  or time-step study, and the face, torso and feet differences (1.1-1.7 K over 1:30-3:00) are not a robust ranking
  beyond this model.

## Sources

- Mitsubishi MSZ-GS12NA-U1 / MUZ-GS12NA-U1 submittal sheet, as hosted by Gemaire
  (resource.gemaire.com/is/content/Watscocom/Gemaire/mitsubishi_muz-gs12na-u1_article_1604089111890477_en_subs.pdf),
  read 11 Nov 2026: 12,000 BTU/h rated, sensible heat factor 0.77, wet-coil cooling airflow 121-144-200-276-343
  CFM, the indoor unit 798 x 232 x 295 mm.
- Mitsubishi MSZ-A09/12/15/17NA operating instructions
  (inspectapedia.com/aircond/MItsubishi-Operating-Instructions-MSZ-A09-12-15-17NA.pdf), reread 20 Nov 2026: "SWING
  OPERATION Use the swing operation for the air flow to reach all corners of the room."; "Use the (AUTO) position
  usually."; and under AUTO in COOL/DRY, "The vane automatically moves to horizontal position. It will not swing."
- Daikin, "Fresh air for everyone: how your air conditioner's SWING mode works"
  (daikin.es/en_es/residential/inspiration/articles/swing-mode.html), read 19 Nov 2026: "The swinging motion
  distributes the air evenly, eliminating excessively hot or cold areas and creating a more comfortable, pleasant
  atmosphere."
- Daikin FTXV30AVJU9 operation manual (US) (gotductless.com/cdn/shop/files/FTXV30AVJU9_Operation_Manual.pdf):
  COMFORT AIRFLOW, "The flow of air will be in the upward direction while in COOL and DRY operation and in the
  downward direction while in HEAT operation, which will provide a comfortable airflow that will not come in direct
  contact with people." Daikin FTXJ20-50MW/MS operation manual (EU), p. 14 (daikin.fr): the cooling swing runs from
  "Upper limit / COMFORT AIRFLOW" to "Lower limit".
- TURBRO, "How Airflow Direction Affects Your Cooling Comfort"
  (turbro.com/blogs/blogs/how-airflow-direction-affects-your-cooling-comfort), read 19 Nov 2026: "Lock them
  horizontally to avoid blowing directly on a sofa or bed."
- Daikin CTXS/FTXS service manual SiUS12-928_B, 1.3 "Auto-Swing", printed p. 37
  (resource.ecmdi.com/is/content/Watscocom/Gemaire/daikin_ctxs12hvju_article_1395692849232_en_sm.pdf): in cooling
  the flap swings between 10 and 40 degrees (CTXS07JVJU, CTXS09/12HVJU, FTXS15/18HVJU).
- Daikin patent US20160231015A1 (patents.google.com/patent/US20160231015A1/en), Technical Problem: "it takes 12
  seconds for the flap to transition either from horizontal blowing to downward blowing or from downward blowing to
  horizontal blowing. Specifically, in this air conditioning apparatus, horizontal blowing and downward blowing are
  repeated in 24 second cycles." The unit is not named.
- Mitsubishi Heavy SRK20-50ZS-W technical manual '18 SRK-T-250, printed p. 65: swing in COOL, DRY and FAN from about
  25 to about 60 degrees from horizontal. Toshiba RAS-10N3KV-E service manual SVM-12029, p. 32: "Swing operation is
  performed in width 35 degrees with the stop position as the center".
- Gypsum board and wood: ρ and c_p from the California Energy Commission, as in
  [`ceilingVsFloorVent`](../ceilingVsFloorVent).
- The unit, its intake and the fixed cooling at the outlet: [`acLouvreAngle`](../acLouvreAngle). The heat-storing
  surfaces: [`acHeatingLouvre`](../acHeatingLouvre)'s `storedLayerWall79`, from [`closedRegister`](../closedRegister).
  The castellated room mesh: [`airPurifierCorner`](../airPurifierCorner).
- The question came from viewers of `acLouvreAngle`'s clip: its most-liked request was "Auto swing team ---->", and
  another viewer wrote "There's actually swing mode you know".

## How the case got here

**The tests.** On 19 Nov 2026 the mesh was built serially, and both runs were tested side by side from rest to 1 s on
the real mesh, with the swing at a 0.5 s test cycle so that the test passed every angle twice. The first pair failed
before its first step, compiling the jet: v2512 has no scalar `Foam::floor`, so `<cmath>` and `using std::floor` were
added to the jet's and the monitor's includes and the jet's code was left as it was. The second pair ran but failed
its start-up heat check, the heat removed reading 1,335-1,388 W in place of 1,354 W within 1%; the
`thermalBoundarySync` function object above was added, and nothing else was changed. The third pair passed every
check at every step to 1 s: 241 steps (held) and 266 (swing), the outlet's mass flow within 1% with no face drawing
air in, the heat 1,353.3-1,354.6 W and the supply 14.58 K below the intake, the jet within 0.66° (held) and 1.86°
(swing, at the 0.5 s test cycle, 48 times faster than the runs') of the imposed angle from 0.1 s, and the air's mass
within 9e-7.

**Both runs were then launched side by side from rest** on our own machine, 8 ranks each, one physical core a rank.
**Two checks at 30 s**, set before the solve, would have stopped both runs if the two pictures were converging: under
5% of the section more than 1 K apart at 9 s, or under 1 K rms difference away from the unit at 30 s. They read 51.1%
and 2.54 K, and the runs went on. **Both reached 180 s in one segment**, with no restart and nothing changed while
they ran: 42,251 steps in 6,622 s (held) and 45,824 steps in 7,458 s (swing), about 1.8 h and 2.1 h of wall time on
8 ranks each; the mesh, the tests and both runs came to 4.02 h. Each run's fields were written every 30 s, so a
stopped run could have been continued; a continuation of a closed room must set pRefValue to the pressure at the
reference point at the restart time (`acLouvreAngle`, "How the case got here"). None was needed.

**A rebuilt run will not repeat the solved runs bit for bit**, because scotch gives a different 8-rank
decomposition on every call on our machine (the solved runs had 13,827 and 13,773 cells on rank 0, two rebuilds
13,825 and 13,874), so parallel sums round differently; in a turbulent buoyant flow that round-off grows, and the
zone means of a rebuilt run should be expected to agree with these closely, not to the last digit. No rebuilt run
was solved to 180 s.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI and `wmake`, and Python 3 with NumPy.

    cd cases/acSwingMode
    ./Allrun held                # [nProcs], default 8; compiles src/ and builds the mesh first
    ./Allrun swing               # default 8; start it once runs/mesh/ is built
    python3 scripts/extract_results.py runs results

The first `Allrun` compiles the wall condition, `src/storedLayerWall80`, into `$FOAM_USER_LIBBIN` as
`libstoredLayerWall80.so`, and builds the shared mesh in `runs/mesh/`: `scripts/make_mesh.py` writes the meshing
dictionaries (`template/mesh/system/`) and the unit's and bed's STLs, then blockMesh, a serial snappyHexMesh of a few
seconds, `scripts/unit_patches.py` (the unit's ports, the checks, and the cell centres for the hydrostatic start) and
checkMesh. Then `scripts/make_case.py` writes `runs/<run>/`: the mesh, `0/`, `constant/` and `system/` from
`template/` and `config/case.json`, and the monitor from `scripts/monitor.C`. `Allrun` decomposes by scotch, writes
the t = 0 planes, solves from 0 to 180 s, and once both runs have solved writes `results/`. The two runs differ only
in the jet's and the monitor's `swinging` switch (and the coded objects' names). `./Allrun --setup-only <run>
[nProcs]` stops before the solve; `./Allclean` removes the runs. The solved runs took about 1.8 h (held) and 2.1 h
(swing) on 8 ranks each, side by side. The solved runs pinned each rank to its own core with a small wrapper and
`taskset`; `Allrun` leaves that to `mpirun`. The 1 s tests are not part of `Allrun`; they were these runs with the
swing's period set to 0.5 s and an end time of 1 s.

Each run writes 481 section and 4 x 481 plan planes (VTK, which the study gzipped as it went and `Allrun` does not),
the fields every 30 s and monitor files of about 0.9 MB. `results/` holds the summary, the zones and each run's
history every 1.5 s; no fields, meshes, planes or logs.

The case was set up and solved by an agent on our own machine and checked by us. The files in `results/` are what
`scripts/extract_results.py` wrote from the solved runs' monitors.

Checked from a clean copy of this folder on 20 Nov 2026: `make_mesh.py`, blockMesh, snappyHexMesh and
`unit_patches.py` rebuild the solved mesh byte for byte (the two STLs, and `points`, `faces`, `owner`, `neighbour`,
`boundary` and snappyHexMesh's level and zone files), and `checkMesh` reports Mesh OK at 111,298 cells,
non-orthogonality 25.2394° at most, skewness 0.333333. `make_case.py` writes both runs' `0/`, `constant/` and
`constant/polyMesh` byte for byte, and `system/` byte for byte but for two lines and one entry: `controlDict` loads
the library by name where the solved runs gave its full path on our machine, the monitor includes the wall
condition's header from `src/` where the solved runs gave the study's path, and `system/functions` leaves out an
abort function object (stop at the next write if a file appears) that the solved runs had and never used.
`src/storedLayerWall80` is the solved runs' source but for its comments. `./Allrun --setup-only` for both runs
compiled the library, built the mesh, decomposed the runs and wrote the t = 0 planes, which are the solved runs' byte
for byte. A four-step serial solve of each run compiled the coded jet, the monitor, the boundary sync and the
wall-flux observer and wrote a first monitor row that agrees with the solved run's in every column to 1.2e-6, but for
the near-zero zone speeds of the first step (to 0.9%). No solve was run to 180 s from the clean copy.
