# The same wall unit heating: its vane aimed up, against aimed down

A wall-mounted split unit heats as well as cools, and in heating the remote's vane button still sets where the air
goes. The makers' manuals send the warm air lower than the cold: Daikin's COMFORT AIRFLOW blows "in the upward
direction while in COOL and DRY operation and in the downward direction while in HEAT operation", and Mitsubishi
says to "use position (1) in the COOL or DRY mode and use positions (2) to (4) in the HEAT mode", position (1)
being the highest. A seller's guide says the opposite: "When you direct air toward the ceiling during heating mode,
warm air spreads across the room before naturally settling downward" (Pioneer). This case is
[`acLouvreAngle`](../acLouvreAngle)'s unit, now heating, switched on in a cold home office twice, once with the jet
aimed 15° up along the ceiling and once 60° down toward the floor, and asks where the warm air goes in the first
three minutes and what reaches a person sitting at a desk against the far wall with their back to the unit. It is
about where the heat goes, not running cost, noise, defrost or the unit's thermostat.

    ./Allrun up      # the vane up, the jet 15 degrees above horizontal, 0-180 s from switch-on
    ./Allrun down    # the vane down, the jet 60 degrees below horizontal, 0-180 s

**The result.** **Aimed down warms the floor and the feet; at the seated person's chest aimed up is warmer for most
of the three minutes.** Aimed up, the jet runs along the ceiling to the far wall, turns down it, and comes down
over the desk, which is where the person sits; by 3:00 the band under the ceiling is the warmest air in that room.
Aimed down, it lands on the floor about 1.2 m out from the unit's wall and spreads along it to under the desk; by
3:00 the air along the floor is the warmest in that room. Over 1:30-3:00 **the air at the chest (the torso zone) is
0.65 K warmer aimed up**, 27.26 against 26.61 °C (81.1 against 79.9 °F), **and at the head 0.34 K**, 26.99 against
26.66 °C; it is warmer aimed up from 6 s to 2:34, the lead then changes hands five times, and **aimed down holds it
from 2:55 and ends ahead at 3:00**, 29.43 against 29.13 °C (85.0 against 84.4 °F, 85 against 84 rounded). **At the
feet aimed down is warmer throughout**, by **2.83 K** over 1:30-3:00 (29.49 against 26.66 °C) and **89 against 84
°F at 3:00** (31.88 against 28.63 °C), with 0.81 against 0.32 m/s of air across them. The rooms do not warm alike
either: the up jet gives more of its heat to the ceiling, so the down room's air is 0.91 K warmer on average at
3:00 and its occupied zone 1.81 K warmer over the last 90 s. Read [What it cannot](#what-it-cannot) before any
number here: **the room is sealed and loses nothing**, **the unit runs flat out with no thermostat**, so **the
warm-up, from 59 to 84-85 °F at the chest in three minutes, is far faster than a real room's**; **the person is
drawn, not modelled**; **it is half a room on a symmetry plane**; and **the chest result depends on the desk being
against the far wall**.

The unit, its two slots and the way its heat is put into the air are [`acLouvreAngle`](../acLouvreAngle)'s with the
heat's sign reversed. The room and the desk are new. The walls, floor and ceiling that store heat are
[`closedRegister`](../closedRegister)'s `storedLayerWall`, with a read-only accessor added for the monitor, and the
castellated mesh with the solids cut out on cell faces is [`airPurifierCorner`](../airPurifierCorner)'s method, as
in `acLouvreAngle`.

## The room

x runs from the unit's wall into the room, y up from the floor, z across the room from its centreline; metres.

| | value | from |
|---|---|---|
| room | 3.60 m from the unit's wall to the far wall, 3.20 m wide, 2.40 m high: about 11.8 x 10.5 ft (124 sq ft) with an 8 ft ceiling, a small US bedroom used as an office | ours |
| half model | z = 0 to 1.60 m, a symmetry plane at z = 0 through the middle of the unit and the desk | ours |
| desk | against the far wall, facing it: a top 1.44 m wide, 0.60 m deep and 4 cm thick, its upper face 0.76 m (30 in) above the floor; in the half model x 3.00-3.60, y 0.72-0.76, z 0-0.72 m; no legs; adiabatic | ours |
| walls, ceiling | 12.7 mm gypsum board, k 0.1587 W/m K, ρc 723,991 J/m³ K, in 24 layers behind the surface, adiabatic back | ρ and c_p from the California Energy Commission, as [`ceilingVsFloorVent`](../ceilingVsFloorVent) |
| floor | 19 mm wood, k 0.106 W/m K, ρc 1,237,411.2 J/m³ K, the same way | the same |
| start | the air at rest at 15 °C (59 °F), every surface and layer at 15 °C, in isothermal hydrostatic balance with 1e5 Pa at y = 1.21 m: an office left unheated all day on a winter evening | |

**There is no person.** A seated adult with their back to the unit is three boxes of air the monitor averages over,
on the symmetry plane: the **torso** at x 2.48-2.80, y 0.80-1.04, z 0-0.24 m, the **head** at x 2.52-2.76, y
1.12-1.32, z 0-0.16 m, and the **feet** under the desk's front edge at x 2.76-3.08, y 0.04-0.16, z 0-0.24 m. A
person's heat and shape would add a plume of their own that the question does not need. They are air temperatures
and speeds, not skin temperatures. Three more zones are averaged: the occupied zone (x 0.60-3.00, y 0.10-1.40, z
0-1.20 m), the floor layer (y < 0.10 m) and the ceiling layer (y > 2.20 m), and the whole room.

**The surfaces store heat** (`src/storedLayerWall79`): each face of the walls, floor and ceiling is a massless
surface over a 1-D layer of 24 slices with its heat capacity and an adiabatic back, all at 15 °C at the start. A
room cold all day has cold surfaces, and a 5 m/s warm jet along a ceiling held at 15 °C would lose far more heat
than a real plasterboard ceiling takes in three minutes; with the layers the ceiling's surface warms as the jet
heats it (by 3:00 to a mean of 20.16 °C in the up room). In 180 s heat reaches about √(αt) ≈ 6 mm into the gypsum
and 4 mm into the wood, so what lies behind them hardly matters. There is no window, no outside loss and no
radiation.

## The unit

**A Mitsubishi MSZ-GS12NA-U1**, the same 12,000 BTU/h wall unit as `acLouvreAngle`'s, now heating, from its
submittal sheet:

| | value | from |
|---|---|---|
| size | 798 x 232 x 295 mm (W x D x H), drawn as a box 0.80 x 0.24 x 0.30 m so its edges lie on the mesh; in the half model x 0-0.24, y 2.00-2.30, z 0-0.40 m, its top 0.10 m below the ceiling | the submittal sheet, rounded |
| air | 390 CFM, the top of its dry-coil heating range (134-160-222-307-390 CFM), as a unit starting in a cold room runs: 0.184 m³/s, **0.1112 kg/s in the half room** at 15 °C | the submittal sheet |
| heat | 14,400 BTU/h (4.22 kW) rated at 47 °F outdoors, the maximum 18,100: **2,110 W into the half room** at the rating | the submittal sheet |
| intake | the grille on its top, x 0.02-0.22 m, z < 0.38 m (0.076 m² in the half room) | ours |

**The heat is a fixed load.** The air leaves at the intake's mean temperature plus Q/(ṁ cp) = 2110/(0.1112 x 1005)
= 18.88 K, by OpenFOAM's `outletMappedUniformInletHeatAddition` with Q = +2110 W, from t = 0: at 15 °C in, it
leaves at about 34 °C (93 °F), and by 180 s at 46.4 °C (up) and 46.6 °C (down) as the room warms. The intake draws
0.1112 kg/s out (`flowRateOutletVelocity`), and the active slot blows the same mass back in. The unit is taken as
running at its rating and top fan from switch-on with its coil already warm. A real heat pump holds its fan until
the coil is warm, modulates its compressor and defrosts; none of that is modelled.

## The vane: up and down

The two runs differ only in the vane, at `acLouvreAngle`'s two angles and through its two slots. A vane turns the
jet without changing the fan's flow, so each run has the same mass flow, through a slot sized so the jet leaves at
nearly the same speed. Neither slot resolves the vane's blade: the direction is imposed at the slot.

- **up**: the jet leaves **15° above horizontal**, toward the ceiling, through a slot in the unit's front face, x =
  0.24 m, y 2.00-2.06 m, 0.60 m wide (z < 0.30 m in the half room, 0.018 m²). This is Pioneer's "toward the
  ceiling", and the highest setting.
- **down**: the jet leaves **60° below horizontal**, toward the floor in front of the unit, through a slot in the
  unit's underside at its front edge, y = 2.00 m, x 0.16-0.24 m, 0.52 m wide (z < 0.26 m, 0.0208 m²). This stands
  for the makers' heating range, Mitsubishi's lower positions and Daikin's COMFORT AIRFLOW in HEAT; neither gives
  its angle from the horizontal in the text quoted here.

The jet is a `codedFixedValue` that points the velocity along the vane and scales it every evaluation to 0.1112
kg/s at the patch's own density, about 5.6 m/s (up) and 5.4 m/s (down) at the start. Both slots are in the one
mesh; in each run the other slot is an adiabatic no-slip wall. The flow-weighted direction of the air over the
first 4 cm outside the slot is **15.7-16.5° up** and **60.3-60.6° down** over the runs (from 0.375 s on).

## The model

`buoyantPimpleFoam` (OpenFOAM v2512), compressible air as a perfect gas (Cp 1005 J/kg K, molar mass 28.96, μ
1.82e-5 Pa s, Pr 0.71), k-ω SST with `buoyancyTurbSource` and wall functions (`kLowReWallFunction`,
`omegaWallFunction`, `nutkWallFunction`, `alphatJayatillekeWallFunction`); the jet at 5% intensity and a 1 cm
mixing length. Euler in time, adaptive steps at Courant 1 (maxDeltaT 0.05 s; 2.65 ms on average, 67,993 and 68,216
steps), limitedLinearV for U, limitedLinear for h and bounded upwind for k and ω, two outer and two pressure
correctors, p_rgh by GAMG to 1e-7 with the final solve capped at 100 iterations (no step reached it), the pressure
reference at (1.81, 1.21, 0.81) m with pRefValue 1e5 Pa. No radiation. The unit's casing and the desk are
adiabatic; the walls, floor and ceiling are `storedLayerWall79` (above).

**The mesh** (`template/mesh/system`, `scripts/make_mesh.py`, `scripts/unit_patches.py`): a background of 8 cm
cubes (blockMesh, 45 x 30 x 20), refined by snappyHexMesh, castellated only, without snapping or layers: 2 cm round
the unit (its surface and a box x < 0.48, y > 1.84, z < 0.48 m), 4 cm under the ceiling (y > 2.08), in front of and
below the unit (x < 1.60, z < 0.64), along the floor (y < 0.16), round the desk and the person (x > 2.40, y < 1.36,
z < 0.80) and on the desk, 8 cm elsewhere, two cells between levels. The desk's box runs to z = 0.80 m so the
desk's edge at z = 0.72 m lies on a cell face. The unit and the desk top are each one closed STL written by
`make_mesh.py` on the mesh's own faces, so they are cut out exactly. snappyHexMesh leaves the unit as one patch;
`unit_patches.py` moves its faces into `intake`, `slotUp` and `slotDown` by face centre and checks their areas and
the desk's (0.9168 m², exposed) to 1%. **117,672 cells** (114,647 hexahedra and 3,025 polyhedra where the levels
meet), an air volume of 13.77792 m³ (the half room less the unit's 0.0288 and the desk's 0.01728 m³); `checkMesh`
OK, non-orthogonality at most 25.2°, skewness at most 0.33, aspect ratio 1. One mesh, no mesh study.

**The monitors** (`scripts/monitor.C`, a coded function object, every step, one row at the first step and then
every 0.375 s into `postProcessing/metrics/metrics.csv`): the slot's and the intake's mass flows and temperatures,
the jet's direction, the air's mass and internal energy (cv/R)∫p dV, its coldest and warmest cell and where they
are, the mean temperature and mean speed |U| of the seven zones, and for each wall, the floor and the ceiling the
heat into it, its mean surface temperature, the heat its layers hold (read from the layers themselves) and the heat
into it summed step by step; and the unit's heat and its sum. The wall heat is the energy equation's own flux,
captured by a diagnostic `fvOptions` entry that changes nothing. The twelve cells of highest Courant number go to
`courant.csv`. And (`planes`) the section, which is the symmetry plane z = 0, and plans at the feet (0.10 m), the
torso (0.90 m), the seated head (1.18 m) and under the ceiling (2.30 m), each with T and U, every 0.375 s from t =
0, 481 a run.

## Results

`results/summary.txt`, `results/zones.csv` and `results/<run>/history.csv` (every 1.5 s), from
`scripts/extract_results.py`. Means over an interval are time-weighted.

| °C | 9 s | 30 s | 60 s | 90 s | 120 s | 150 s | 180 s | 90-180 s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| torso, up | 17.42 | 20.13 | 23.01 | 25.11 | 26.24 | 28.40 | 29.13 | **27.26** |
| torso, down | 15.40 | 18.54 | 21.70 | 23.91 | 25.89 | 27.48 | 29.43 | **26.61** |
| head, up | 17.16 | 21.10 | 23.11 | 24.95 | 25.80 | 28.11 | 28.54 | **26.99** |
| head, down | 15.40 | 18.66 | 21.84 | 23.92 | 25.94 | 27.54 | 29.44 | **26.66** |
| feet, up | 15.37 | 20.04 | 22.23 | 24.71 | 26.65 | 27.04 | 28.63 | **26.66** |
| feet, down | 19.36 | 21.70 | 24.50 | 26.56 | 28.91 | 30.44 | 31.88 | **29.49** |
| room, up | 16.34 | 18.88 | 21.70 | 23.79 | 25.42 | 26.70 | 27.74 | 25.99 |
| room, down | 16.41 | 19.01 | 21.83 | 23.96 | 25.60 | 27.18 | 28.65 | 26.38 |

| over 90-180 s | up | down |
|---|---:|---:|
| air speed at the torso, m/s | 0.378 | 0.305 |
| air speed at the head, m/s | 0.453 | 0.428 |
| air speed at the feet, m/s | 0.324 | 0.811 |
| floor layer, y < 0.1 m, °C | 24.73 | 27.98 |
| ceiling layer, y > 2.2 m, °C | 28.82 | 25.68 |
| occupied zone, °C | 25.32 | 27.13 |

**Where the heat goes.** The surfaces' heat shows it: at 180 s the ceiling takes 742 W from the up room's air and
299 W from the down room's, the floor 203 against 554 W, and the far wall behind the desk 264 against 218 W. All
the surfaces together take 1716 W of the 2110 W in the up room and 1545 W in the down room at 180 s, and by then
their layers hold 228 and 217 kJ, the up room's ceiling 109 kJ of it against 35 kJ. So the up room's air ends
cooler on average, 27.74 against 28.65 °C at 180 s, though its chest zone was the warmer one for most of the run.
At 180 s the floor layer is 25.96 °C up and 29.67 °C down, and the ceiling layer 30.56 °C up and 27.89 °C down. The
section planes differ by more than 1 K over 65.9% of the section at 9 s, 67.5% at 90 s and 60.2% at 180 s, with an
rms difference of 3.2-3.9 K beyond 0.5 m from the unit at 9, 30, 90 and 180 s.

**The chest and the head.** The torso is warmer aimed up from 5.6 s to 153.75 s; from there the lead changes hands
five times (down from 153.75 s, up from 156.4 s, down from 166.5 s, up from 171 s) and aimed down holds it from
174.75 s to the end. The head behaves the same way with a smaller gap, and changes hands more often (down for
118.9-120.75 s, then five times from 153.75 s); at 180 s it is 28.54 °C up against 29.44 °C down (83.4 against 85.0
°F). The feet are warmer aimed down at every row.

**The number on the clip.** The clip's number is the torso's air temperature in °F, rounded to the degree, "at the
chest". Both rooms start at 59; then up against down, 63/60 at 0:09, 68/65 at 0:30, 73/71 at 1:00, 77/75 at 1:30,
83/81 at 2:30 and 84/85 at 3:00. Of the 481 writes, the up room's rounded number is higher at 408, equal at 52 and
lower at 21, all of those from 167.25 s on.

**Checks.** The slot and the intake carry 0.1112 kg/s, to within 1e-7 of it in both runs, the unit's heat holds at
2109.99-2110.01 W, and the supply is 18.88 K above the intake throughout. The heat budget over 10-180 s, the rise
of the air's internal energy and of the heat in the surfaces' layers against the unit's heat, closes to **0.073%**
(up) and **0.059%** (down) of the unit's heat. The air's mass reads 16.654423620 kg at every row of both runs (the
first step took it 9.0e-7 below the t = 0 fields' 16.6544385 kg, and it did not move after). No air is warmer than
the supply by more than 0.051 K, and from 0.375 s on none is colder than the 15 °C start; at the very first step it
was, briefly (below). No final pressure solve reached its 100-iteration cap, and no field was bounded.

**A start-up blip.** At the first step, 0.0006 s, the air in one cell just above the intake, at (0.07, 2.31, 0.01)
m, dips 0.353 K (up) and 0.357 K (down) below 15 °C. Every-step tests show it gone by 0.13 s (up) and 0.11 s
(down). Its cause was not isolated and nothing was tuned for it. It is above the 0.2 K the study set itself for
reporting such an excursion, so it is reported here; it is invisible at the first plane write and changes none of
the numbers above.

## What the clip shows, and what it does not

The clip shows the section, the symmetry plane through the middle of the unit, the desk and the seated person, the
whole office in both panels on every frame, stacked, "aimed up" above and "aimed down" below, **from switch-on to
3:00 of the solve** at nine times speed in 20 s, one frame a plane write. It is coloured by air temperature on a
59-95 °F scale (the 15-35 °C of the study), with moving air parcels, a desk, a chair and a seated figure facing the
far wall, a clock, the question "Heating mode: warm air up or down?" and under it "a follow-up: the same wall unit,
now heating". Each panel carries one rounded number, the air at the seated person's chest in °F.

- **The number is the chest, not the feet.** The feet, where aimed down wins clearly, are not on screen. A viewer
  who reads "aimed up is warmer" off the numbers is reading the chest in this room, where the ceiling jet comes
  down the far wall over the desk; the clip does not say that aimed up warms the room more, and in these runs it
  does not: the down room's air is the warmer on average.
- The unit, its vane, the desk's legs, the chair and the seated figure are drawn; only the desk top is in the
  model. The parcels are moved through the planes' velocity after the solve; they are not solved particles. The air
  leaving the unit is hotter than the scale's 95 °F, so the jet's core near the slot saturates.

## What it cannot

- **The warm-up is far too fast for a real room.** The chest goes from 59 to 84-85 °F (15 to 29.1-29.4 °C) in three
  minutes, and the rooms' mean air passes 70 °F at 52 s (down) and 53 s (up). **The room is sealed and loses
  nothing**: no window, no leakage, no outside wall loss (the layers' backs are adiabatic), no furniture but the
  desk top, and no radiation. **The unit runs flat out** at its rated 14,400 BTU/h and top fan, in a 124 sq ft
  office, with **no thermostat**: a real unit would throttle back near its set point. A sealed room also warms its
  air at constant volume, about 40% faster than a leaky one at constant pressure. Both runs share all of this, so
  the comparison between them should hold better than the absolute temperatures, which are not what a real room
  reaches.
- **The person is drawn, not modelled.** There is no body heat and no body in the flow: no plume off the person, no
  blocking of the jet coming down the far wall, no chair. The torso, head and feet are boxes of air.
- **The chest result depends on the desk being against the far wall**, where the up jet comes down. A desk in the
  middle of the room, or a chair under the unit, might come out otherwise; this room does not say. The feet's
  result, under a down jet that spreads along the whole floor, depends on that less.
- **The differences at the chest and head are small** (0.65 K and 0.34 K over 1:30-3:00) and change sign in the
  last half minute; on one mesh with no mesh or time-step study they are not a robust ranking.
- **It is a half model on a symmetry plane**, z = 0 through the middle of the unit and the desk. The jets cannot
  wander sideways, which a real jet does slowly, and the clip's section is that plane, which keeps the jet's core.
- **The heat is a fixed load at the rating** from t = 0, the coil already warm; no fan delay, no compressor
  modulation, no defrost.
- **The vane is a fixed direction at a slot**, 15° up or 60° down, not a maker's vane: no blade, no swing, no auto
  mode. The unit is a box with Mitsubishi's dimensions, not its shape.
- **One room, one layout, three minutes.** Over an hour both rooms warm through, and the difference is in where the
  person sits in cooler air for how long, not where the room ends up.
- **RANS, one mesh.** k-ω SST on a stepped castellated mesh of 117,672 cells, 2-8 cm, with wall functions. No mesh
  or time-step study.
- **The draught on skin** is not modelled: warm air moving at 0.8 m/s, as at the feet aimed down, can feel cooler
  than still air at the same temperature, and the case gives air temperature and speed only.

## Sources

- Mitsubishi MSZ-GS12NA-U1 / MUZ-GS12NA-U1 submittal sheet, as hosted by Gemaire
  (resource.gemaire.com/is/content/Watscocom/Gemaire/mitsubishi_muz-gs12na-u1_article_1604089111890477_en_subs.pdf),
  read 11 and 19 Nov 2026: heating rated 14,400 BTU/h at 47 °F outdoors, maximum 18,100; dry-coil heating airflow
  134-160-222-307-390 CFM; the indoor unit 798 x 232 x 295 mm.
- Mitsubishi MSZ-A09/12/15/17NA operating instructions
  (inspectapedia.com/aircond/MItsubishi-Operating-Instructions-MSZ-A09-12-15-17NA.pdf): "Use position (1) in the
  COOL or DRY mode and use positions (2) to (4) in the HEAT mode", position (1) the highest.
- Daikin FTXV30AVJU9 operation manual (US) (gotductless.com/cdn/shop/files/FTXV30AVJU9_Operation_Manual.pdf):
  COMFORT AIRFLOW, "The flow of air will be in the upward direction while in COOL and DRY operation and in the
  downward direction while in HEAT operation, which will provide a comfortable airflow that will not come in direct
  contact with people."
- Pioneer Mini Split, "Why airflow direction settings matter for your mini split"
  (pioneerminisplit.com/blogs/news/why-airflow-direction-settings-matter-for-your-mini-split): "When you direct air
  toward the ceiling during heating mode, warm air spreads across the room before naturally settling downward."
- Gypsum board and wood: ρ and c_p from the California Energy Commission, as in
  [`ceilingVsFloorVent`](../ceilingVsFloorVent).
- The unit, its slots, the coded jet and the fixed heat at the outlet: [`acLouvreAngle`](../acLouvreAngle), the
  heat's sign reversed. The heat-storing surfaces: [`closedRegister`](../closedRegister)'s `storedLayerWall`. The
  castellated room mesh: [`airPurifierCorner`](../airPurifierCorner).
- The question came from viewers of `acLouvreAngle`'s clip: its most-liked comment on heating was "Cooling - up,
  heating - down", and several asked what happens with hot air.

## How the case got here

**The solve.** On 19 Nov 2026 the mesh was built serially, and both runs were set up as here and tested for 200
steps each on the real mesh: the slots and the intake at 0.1112 kg/s, the supply 18.88 K above the intake, 2,110.0
W, the jets at 15.97° and -60.52°, and the up room's ceiling already taking heat (65 W at 0.51 s) with its surface
warming, so the layered walls work with the right sign. The first pair of tests failed before its first step,
compiling the monitor (an include path for the thermo headers was missing); only the monitor's compile options were
changed and both tests were run again from rest. Both runs were then launched side by side on our own machine from
rest, 8 ranks each, one physical core a rank.

**Two checks at 30 s**, set before the solve, would have stopped both runs if the two pictures were converging:
under 5% of the section more than 1 K apart at 9 s, or under 1 K rms difference away from the unit at 30 s. They
read 65.9% and 3.18 K, and the runs went on.

**Both runs reached 180 s in one segment**, with no restart and nothing changed while they ran: 67,993 steps in
10,889 s (up) and 68,216 steps in 12,168 s (down), about 3.0 h and 3.4 h of wall time on 8 ranks each. Each run's
fields were written every 30 s, so a stopped run could have been continued; a continuation of a closed room must
set pRefValue to the pressure at the reference point at the restart time (`acLouvreAngle`, "How the case got
here"). None was needed.

**A rebuilt run will not repeat the solved runs bit for bit**, because scotch gives a different 8-rank
decomposition on every call on our machine (three calls gave 14,856, 14,836 and 14,744 cells on rank 0, against the
solved runs' 14,820), so parallel sums round differently; in a turbulent buoyant flow that round-off grows, and the
zone means of a rebuilt run should be expected to agree with these to a few hundredths of a kelvin, not to the last
digit. No rebuilt run was solved to 180 s.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI and `wmake`, and Python 3 with NumPy.

    cd cases/acHeatingLouvre
    ./Allrun up                  # [nProcs], default 8; compiles src/ and builds the mesh first
    ./Allrun down                # default 8; start it once runs/mesh/ is built
    python3 scripts/extract_results.py runs results

The first `Allrun` compiles the wall condition, `src/storedLayerWall79`, into `$FOAM_USER_LIBBIN` as
`libstoredLayerWall79.so`, and builds the shared mesh in `runs/mesh/`: `scripts/make_mesh.py` writes the meshing
dictionaries (`template/mesh/system/`) and the unit's and desk's STLs, then blockMesh, a serial snappyHexMesh of a
few seconds, `scripts/unit_patches.py` (the unit's ports, and the cell centres for the hydrostatic start) and
checkMesh. Then `scripts/make_case.py` writes `runs/<run>/`: the mesh with its unused slot made a wall, `0/`,
`constant/` and `system/` from `template/` and `config/case.json`, and the monitor from `scripts/monitor.C`.
`Allrun` decomposes by scotch, writes the t = 0 planes, solves from 0 to 180 s, and once both runs have solved
writes `results/`. The two runs differ in the active slot's boundary conditions (`0/`), the unused slot's patch
type and the monitor's slot. `./Allrun --setup-only <run> [nProcs]` stops before the solve; `./Allclean` removes
the runs. The solved runs took about 3.0 h (up) and 3.4 h (down) on 8 ranks each.

Each run writes 481 section and 4 x 481 plan planes (VTK; the solved runs' came to about 0.28 GB a run once
gzipped, which the study did as it went and `Allrun` does not), the fields every 30 s and monitor files of about
0.9 MB. `results/` holds the summary, the zones and each run's history every 1.5 s; no fields, meshes, planes or
logs.

The case was set up and solved by an agent on our own machine and checked by us. The files in `results/` are what
`scripts/extract_results.py` wrote from the solved runs' monitors.

Checked from a clean copy of this folder on 19 Nov 2026: `make_mesh.py`, blockMesh, snappyHexMesh and
`unit_patches.py` rebuild the solved mesh byte for byte (the two STLs, and `points`, `faces`, `owner`, `neighbour`,
`boundary` and snappyHexMesh's level and zone files), and `checkMesh` gives the solved mesh's report line for line:
Mesh OK at 117,672 cells, non-orthogonality 25.2394° at most, skewness 0.333333. `make_case.py` writes both runs'
`0/`, `constant/` and `constant/polyMesh` byte for byte, and `system/` byte for byte but for two lines and one
entry: `controlDict` loads the library by name where the solved runs gave its full path on our machine, the monitor
includes the wall condition's header from `src/` where the solved runs gave the study's path, and
`system/functions` leaves out an abort function object (stop at the next write if a file appears) that the solved
runs had and never used. `src/storedLayerWall79` is the solved runs' source but for its comments. `./Allrun
--setup-only up` compiled the library, decomposed the run and wrote the t = 0 planes, which are the solved run's
byte for byte. A four-step serial solve of the up run compiled the coded jet, the monitor and the wall-flux
observer and wrote a first monitor row that agrees with the solved run's in every column to 1.3e-6, but for the
near-zero zone speeds of the first step (to 0.2%). No solve was run to 180 s from the clean copy.
