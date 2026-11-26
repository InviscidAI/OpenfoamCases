# A furnace against a heat pump: the same living room, the same heat

A US living room on a cold evening, and the heating comes on. One camp says the heat pump is the more comfortable:
"properly designed heat pumps can provide more comfortable heating than furnaces", because "the furnace blasts you
with hot air for a short time and then goes off. Then it comes back on a while later and blasts you again" (Allison
Bailes, Energy Vanguard), and readers under his post agree: "There is no question for me that the heat pumps are way
more comfortable." The other camp says the furnace is: "They are more comfortable then heat pumps" (an installer in
Atlanta, under the same post), 95 °F air is not "comfortable in winter? Of course not!" (another reader), and even a
maker that sells both calls heat pump air "Warm, but not as 'toasty' as gas heat" (Trane). Each has a reason to
expect to win: the furnace's air is hotter, the heat pump's never stops. This case heats the same room twice with the
same heat over every cycle, once with a single-stage furnace blowing hot air in bursts and once with a heat pump
blowing cooler air at a higher flow nonstop, and asks how warm the air is at the head and at the feet of someone on
the sofa, second by second for the first 25 minutes. It is about the air in the room, not bills, efficiency, radiant
warmth or the whole house.

    ./Allrun furnace     # 0.0566 kg/s (full room) at 32 K above the return, 7:18 on and 5:06 off, twice, 0-1488 s
    ./Allrun heatPump    # 0.0711 kg/s at 15 K above the return, nonstop, 0-1488 s

**The result.** **The heat pump's room is the more even from head to feet; the furnace's swings.** Both rooms start
at rest at 66 °F (292.04 K) with 27 °F (270.35 K) outside, and each register gives the same heat above the return's
air over every 744 s cycle, 398.64 and 398.64 kJ for the furnace in the half room solved against 398.19 and
398.72 kJ for the heat pump (797 kJ a cycle for the whole room, 0.11% and 0.02% apart). With the heat pump the seated feet are
**about 4 °F colder than the head almost throughout**: 3.7-4.5 °F over the last cycle, 3.8 °F on average over the
run. With the furnace they are 7-8 °F colder while it blows, **8-9 °F colder about a minute after each switch-off**
(8.3 °F at 500 s, 9.2 °F at 1240 s) and 4-5 °F late in each off phase: **6.0 °F on average over the run**, from 4.4
to 9.3 °F over the last cycle. At the head the furnace's room is often the warmer: its seated head swings between
72 and 79 °F once it has warmed, while the heat pump's climbs steadily, 71.6 °F at 7:15 and 75.1 °F at 24:47. Read
[What it cannot](#what-it-cannot) before any number here: **nothing radiates and no air leaks**, so the head-to-feet
gaps run high and both rooms warm about 8 °F in 25 minutes, far more than a real room would; **the furnace's cycle is
imposed**, with no thermostat; **the seated person is drawn, not modelled**; the same heat over each cycle is **built
in by design**; and there is **no mesh or time-step study**.

The room, the sofa and the two heaters are this case's. The buoyant model, the schemes and solution settings, the
storing walls, the energy-flux observer and the monitor's form are [`closedRegister`](../closedRegister)'s, with a
film added on the back of the storing layer for the outer wall and the ceiling.

**The posted furnace run is a re-solve.** The first furnace run let air back in through the return at a fixed
66 °F while its blower was off, which cooled the floor behind the sofa by 3.0 and 4.7 °F within 10 s of the two
switch-offs; it was solved again with the backflow at the return's own outward mean temperature (below), and its files
are not here. The heat pump's run, whose return never flows inward, was kept.

## The room

x runs from the window wall's inner face to the inner wall, y up from the floor and z from the symmetry plane through
the register to the side wall; metres. The model is the half room z ≥ 0; all flows, heats and areas below are the half
room's unless they say full room, and doubling them gives the whole.

| | value | from |
|---|---|---|
| the room | 4.5 m from the window wall to the inner wall, 4.8 m wide, 2.4 m high (15 x 16 ft, 233 sq ft), closed but for the register and the return: no doorway, no leaks; 25.48 m³ of air in the half | ours |
| half model | z 0-2.4 m, a symmetry plane at z = 0 through the register, the window's middle and the sofa's | ours |
| the window | x = 0, y 0.9-2.1, z 0-1.2 m (2.4 x 1.2 m in the full room, 1.44 m² in the half) | ours |
| the register | in the floor under the window, x 0.10-0.20, z 0-0.10 m: 0.10 x 0.20 m in the full room, the free area of a 4 x 12 in floor register; blowing straight up, uniform | ours |
| the return | low on the inner wall, x = 4.5, y 0.10-0.30, z 0-0.30 m (0.6 x 0.2 m in the full room) | ours |
| the sofa | a solid block: the seat x 3.0-3.9, y 0-0.4 m and its back x 3.7-3.9, y 0.4-0.8 m, both z 0-1.0 m (2 m wide), facing the window 0.6 m from the inner wall | ours |
| outer wall and ceiling | 12.7 mm gypsum (k 0.1587 W/m K, ρc 723,991 J/m³ K) in 24 layers, losing heat through their backs to 270.35 K through a film of 0.544 W/m² K (outer wall) and 0.317 W/m² K (ceiling), so U 0.52 and 0.31 W/m² K with the gypsum | gypsum: `closedRegister`'s; the back films ours, roughly an insulated wall and a better-insulated ceiling |
| inner wall and side wall | the same gypsum, adiabatic behind | `closedRegister`'s |
| floor | 19 mm wood (k 0.106, ρc 1,237,411), 24 layers, adiabatic behind | `closedRegister`'s |
| sofa | 50 mm foam (k 0.04, ρc 49,000), 24 layers, adiabatic behind | ours |
| the window's glass | no layers; its surface loses heat to 270.35 K through a film of 4.403 W/m² K, a double pane's U of 2.8 W/m² K without its inside film | `closedRegister`'s |
| outside | 270.35 K (-2.8 °C, 27 °F) | ours, the design-day kind of cold evening at which the heat pump below runs nonstop |
| start | the air at rest at 292.04 K (66 °F), hydrostatic cell by cell, p = 1e5 exp(-9.81 y / (287.1 x 292.04)) Pa, and every layer at 292.04 K | ours |

**There are no people.** The seated person in the clip is drawn. "The head" and "the feet" are two boxes of air on the
centreline at the sofa: **the head** x 3.3-3.7, y 1.0-1.2, z 0-0.6 m, above the seat, and **the feet** x 2.6-3.0,
y 0.05-0.15, z 0-0.6 m, on the floor in front of it; the number is the volume mean of the head box less that of the
feet box. The occupied zone, x 1.0-4.2, z 0-1.8 m with the sofa left out, is also monitored at ankle (y 0.05-0.15),
seated head (1.0-1.2), standing head (1.6-1.8) and under the ceiling (y > 2.2 m).

## The two heaters

Each heater is one register and one return, with the machine left out. **The register blows a fixed mass flow at a
fixed rise above the return's air**, so each gives a fixed heat whatever the room does, and the supply warms with the
room (the furnace's from 123.6 °F at 15 s to 132.3 °F at its warmest, the heat pump's from 93.0 to 100.7 °F):

| | furnace | heat pump |
|---|---|---|
| supply, at the start | 32 K above the return: 124 °F (50.9 °C) | 15 K above: 93 °F (33.9 °C) |
| mass flow, full room (half) | 0.0566 (0.02830) kg/s, about 100 cfm | 0.0711 (0.03555) kg/s, about 126 cfm |
| out of the register | about 2.6 m/s | about 3.1 m/s |
| heat while on, full room (half) | 1.82 kW (910.1 W) | 1.07 kW (535.9 W) |
| on | 0-438 s and 744-1182 s; off 438-744 s and 1182-1488 s | from t = 0 to the end |
| heat over a 744 s cycle, full room | 797 kJ | 797 kJ |

- **The two temperatures** are Bailes's: furnace air "is about 125 F (There's some variation, but this is typical.)",
  heat pump air "only about 95 F". A 40,000 Btu/h single-stage 80% furnace (an American Standard S8X1B040M2PSC, the
  furnace of `closedRegister`) gives 32,500 Btu/h, and its own table rises 59 °F at 500 CFM and 49 °F at 600, so 32 K
  (57.6 °F) at 520 CFM. A 2-ton heat pump (Carrier 25HPA324) at 700 CFM gives 17.67 MBtu/h at 27 °F outdoors, air at
  93 °F, so on this evening it runs all the time at about 95 °F. The flows here are the half room's share of a room
  with one register; only the rises and the ratio of the flows are from the machines.
- **Equal heat fixes the airflow ratio**: 0.0283 x 32 x 438 = 0.03555 x 15 x 744 to within 0.1%, so the heat pump
  blows 1.26 times the furnace's air. The same heat over each cycle is therefore designed in, not found.
- **The furnace's cycle** is the US furnace test procedure's (NBSIR 78-1543): a furnace 70% oversized has a load
  factor X = 1/1.7 = 0.588 at the design condition, and a thermostat set to N = 5 cycles an hour, the setting for a gas
  furnace under 90% (Honeywell's installer guide), gives t_on = 60 X/(4 N X (1 - X)) = 7.3 min on and 5.1 min off: **438 s
  on and 306 s off, 7:18 and 5:06**. Wisconsin's field furnaces averaged about 10 minutes a cycle (Pigg 2003). The
  cycle is imposed, the same twice, not driven by a thermostat; each switch is a 2 s linear ramp of the flow, with no
  blower delay and no heat left in the heat exchanger after it stops.

**The register** (`scripts/supply.C`, a `codedFixedValue` for T, and a `flowRateInletVelocity` table for U, the
schedule the same in both): its temperature is the return's outward mass-flux-weighted mean temperature plus the rise,
or, while nothing flows out through the return, the mean of the cells next to it; while the scheduled flow is under
1e-6 kg/s it takes the cells next to the register, so that the shut register neither heats nor cools. k and ω are fixed
at 5% intensity and a 0.01 m mixing length, off phases included; p_rgh is `fixedFluxPressure`. **The return** holds
still air's hydrostatic pressure at 292.04 K face by face (`prghPressure`, U `pressureInletOutletVelocity`), so the air
leaves as the room asks: about 0.029-0.030 kg/s while the furnace blows (its 0.0283 and the room's expansion), and
while it is off air trades places through it, 0.0026-0.0054 kg/s in and 0.0018-0.0044 kg/s out. **Air coming back in
through the furnace's return** carries the return's own outward flux-weighted mean temperature, the last such value
while nothing flows out (`src/returnMeanTemperature`, an `inletOutlet` whose inlet value is reset every step, and the
quantity the register already uses). The heat pump's return is a plain `inletOutlet` at 292.04 K, and no air came
back through it after the first step.

## The model

`buoyantPimpleFoam` (OpenFOAM v2512), air as a perfect gas (Cp 1005 J/kg K, molar mass 28.96, μ 1.82e-5 Pa s, Pr 0.71,
its enthalpy referred to 292.04 K), k-ω SST with `buoyancyTurbSource` and wall functions (`kLowReWallFunction`,
`omegaWallFunction`, `nutkWallFunction`, `compressible::alphatJayatillekeWallFunction` with Prt 0.85), no-slip
everywhere. Euler in time, adaptive steps at Courant 1 with maxDeltaT 0.05 s from a first deltaT of 5e-4 s; limitedLinearV 1 for
U, limitedLinear 1 for h and bounded upwind for k and ω; two outer and two pressure correctors; p_rgh by GAMG to 1e-7
(relTol 0.01) and the final solve to 1e-7 (relTol 0, at most 100 iterations). **No radiation.**

**The storing walls** (`src/radLayerWall85`, registered as `radLayerWall`): `closedRegister`'s `storedLayerWall`, whose
surface balances the heat from the first air cell against an implicit 1-D layer behind it advanced from the step's
starting state at every evaluation, with one addition: a film on the layer's back, `h_back` to `Tback`, the last node
losing heat through half a slice of the layer in series with it, so that the steady flux is (T - Tback)/(thickness/k +
1/h_back). `h_back 0` is the adiabatic back. The window is the same condition with no layers and the film on its room
side.

**The mesh** (`scripts/make_mesh.py`): one blockMesh box of graded lines, structured hexahedra with no snapping and no
split faces, 2.5 cm over x 0-0.3, 5 cm over 0.3-0.6, 10 cm over 0.6-4.3 and 5 cm over 4.3-4.5 m (59 cells); 5 cm over
y 0-0.4, 10 cm over 0.4-2.2 and 5 cm over 2.2-2.4 m (30); 2.5 cm over z 0-0.2, 5 cm over 0.2-0.4 and 10 cm over
0.4-2.4 m (32). topoSet and subsetMesh take out the sofa's 1,440 cells, their faces becoming the sofa patch, and
createPatch moves the register, the window and the return out of the floor, the window wall and the inner wall.
**55,200 hexahedral cells**, every edge of the sofa, the openings and the window on a grid line, the register 4 x 4
faces and the return 4 x 10; `checkMesh` OK, non-orthogonality 0, aspect ratio at most 4. One mesh, no mesh study.

**The monitor** (`scripts/monitor.C`, a coded function object run at every step, a row at the first step, every
0.625 s and at each field write into `postProcessing/metrics/metrics.csv`, 104 columns named in `scripts/columns.json`):
the register's and the return's gross flow each way, flux-weighted temperature and enthalpy above 292.04 K, the
register's heat above the return's air and its running sum; the air's mass, enthalpy and integral of p; the coldest
and hottest air and where they are; the mean, coldest and hottest temperature and the mean and largest speed of the
whole air, the occupied zone's four layers and the sofa's two boxes; the heat into each surface, both with the energy
equation's own diffusivity (a do-nothing `scalarCodedSource` in `constant/fvOptions` catches the wall flux before the
turbulence model updates αt) and as `wallHeatFlux` gives it, with its running sum and the mean surface temperature;
the fastest and hottest air in the layers at y 0.5, 1.0, 1.5 and 2.2 m; and the twelve cells of highest Courant number
in `courant.csv`. The **planes** are the section z = 0.0125 m (the first cell layer off the symmetry plane, through the
register, the window and the sofa, cell values) every 0.625 s, plans at y 0.11, 1.12 and 1.72 m (interpolated) and the
window and floor patches every 2.5 s, all from t = 0, VTK.

## Results

`results/summary.txt` and `results/<run>/history.csv` (every 2.5 s), from `scripts/extract_results.py`.

| sofa, °F | 1:00 | 5:00 | 7:15 | 8:20 | 10:00 | 12:20 | 13:20 | 19:40 | 20:40 | 21:40 | 24:47 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| furnace on or off | on | on | on | off | off | off | on | on | off | off | off |
| furnace, head | 66.5 | 74.7 | 76.7 | 75.7 | 74.0 | 72.2 | 72.9 | 79.2 | 78.4 | 77.1 | 74.0 |
| furnace, feet | 65.3 | 66.8 | 69.5 | 67.4 | 69.0 | 67.7 | 67.2 | 72.4 | 69.2 | 70.6 | 69.1 |
| furnace, feet colder than head by | 1.2 | 7.9 | 7.2 | **8.3** | 5.0 | 4.5 | 5.6 | 6.8 | **9.2** | 6.5 | **4.9** |
| heat pump, head | 67.7 | 70.6 | 71.6 | 71.9 | 72.5 | 73.1 | 73.4 | 74.5 | 74.6 | 74.7 | 75.1 |
| heat pump, feet | 65.2 | 66.5 | 67.8 | 68.2 | 68.7 | 69.4 | 69.3 | 70.2 | 70.3 | 70.4 | 70.7 |
| heat pump, feet colder than head by | 2.5 | 4.2 | 3.8 | 3.7 | 3.8 | 3.7 | 4.0 | 4.3 | 4.4 | 4.3 | **4.4** |

(The times are 60, 300, 435, 500, 600, 740, 800, 1180, 1240, 1300 and 1487.5 s.)

| | furnace | heat pump |
|---|---:|---:|
| feet colder than head, mean over the run (0-1487.5 s), °F | **6.02** | **3.80** |
| the same over the last cycle (744-1487.5 s), °F | 6.51 | 4.21 |
| the same, smallest and largest over the last cycle, °F | 4.41 / 9.35 | 3.70 / 4.45 |
| seated head, mean over the last cycle, °F | 76.51 | 74.22 |
| feet, mean over the last cycle, °F | 70.00 | 70.01 |
| seated head over the last cycle, coldest / warmest, °F | 72.2 / 79.4 | 73.2 / 75.1 |
| the room's mean air at 1487.5 s, °F | 73.67 (up 7.67) | 74.93 (up 8.93) |
| heat above the return's air, 0-744 s / 744-1488 s, kJ (half room) | 398.64 / 398.64 | 398.19 / 398.72 |
| fastest air in the sofa's boxes over the run, m/s | 0.180 | 0.175 |
| mean speed over the run at the head / the feet, m/s | 0.039 / 0.021 | 0.067 / 0.017 |

**How the two rooms heat.** Both jets rise from the floor up the window and turn along the ceiling; by 15 s both
are under the ceiling, and by 60 s the furnace's warm layer reaches the far wall (the heat pump's by 150 s), the
study's own reading of its sections. The furnace's room fills from the top down with hotter air, which is why its
head is warmer than the heat pump's while it blows (76.7 against 71.6 °F at 7:15); the floor stays near the start's
66 °F in both, because nothing radiates to it (66.0-66.3 °F at its surface in the furnace's room, 66.0-66.4 in the heat
pump's), so the feet follow the air that settles onto it. The heat pump's larger, cooler flow mixes the room more
evenly and keeps on doing so: its head-to-feet gap is 3.7-4.5 °F from 2 minutes on, and 4 °F once rounded at 2,013 of
the 2,188 monitor rows after 2 minutes, against the furnace's 4 to 9 °F, mostly 5 to 8.

**Why the feet dip after each switch-off.** When the furnace stops, the warm layer at the ceiling has nothing driving
it and the air under the window keeps cooling on the glass and sinking. The layer within about 5 cm of the floor, near
67 °F over the cold floor, then moves towards the sofa (+2 to +7 cm/s at 490-500 s and at 1240 s in the section) and
piles up against the sofa's front, where it lifts into the feet box; the ankle plan shows no colder air between the
window and the sofa's front than at it. The feet fall from 69.5 to 67.4 °F between 7:15 and 8:20, and from 72.4 to
69.2 °F between 19:40 and 20:40, while the head falls only about 1 °F, so the gap peaks at 8.4 °F (497.5 s) and 9.3 °F (1241.9 s), a minute after
each switch-off. **It does not come from the return**: the first furnace run, with its 66 °F backflow, had the same dip
(8.3 °F at 500 s in both solves, 9.5 against 9.2 °F at 1240 s), and its blue pool behind the sofa is what the
re-solve took away.

**Where the heat goes.** Of the 910 W the furnace blows in while it is on (the half room's), 694 W goes into the
surfaces at 7:15, 353 W of it into the ceiling under its hot layer and 80 W out through the window; of the heat pump's
steady 536 W, 502 W goes into the surfaces at 24:47, 82 W of it through the window. Over the whole run the two rooms
get 797.3 and 796.6 kJ, and the furnace's gives more of it to the ceiling (317 against 282 kJ) and less to the window
(99 against 115 kJ), and keeps less in its air (128 against 149 kJ above the start), which is why its mean air ends
the cooler, at 73.7 against 74.9 °F, with the furnace off. With the walls storing and nothing leaking, both rooms are
still warming at 24:47.

**Checks.** The air's heat budget over 10-1487.5 s, the change of its enthalpy less that of its integral of p against
the register's and the return's enthalpy and the heat into every surface, each summed at every step, closes to
**+0.0035% (furnace) and +0.0140% (heat pump)** of the register's heat over that time; the air's mass to
-2.4e-5 kg in both, 8e-7 of itself. The heat over each cycle is the furnace's 398.64 and 398.64 kJ against the heat
pump's 398.19 and 398.72 kJ, apart by 0.113% and 0.020%. While the furnace is off, the air that comes in through its
return is within 0.018 K of the return's outward mean (976 inflow rows over 439.4-1487.5 s). The final pressure solve
reached its 100-iteration cap at 39 steps (furnace) and 38 (heat pump), all before 0.14 s, with final residuals of at
most 4.9e-7; no tolerance was relaxed. SST's k and ω never needed bounding. The coldest air was 288.16 K (furnace) and
288.15 K (heat pump), at 5 s beside the window's lower edge, and the hottest 328.98 and 311.32 K, just above the
registers. The air in the furnace's jet can run a little above its own supply: 0.18 K in the re-solve's test of the
switch, with the old return condition as with the new, and up to 0.15 K in the first run's on phases, which the agent
put down to the scheme's overshoot in the jet; no scheme was changed for it. The runs took about 71,700 (furnace) and 102,200
(heat pump) steps.

## What the clip shows, and what it does not

The clip shows the section z = 0.0125 m, the whole half room from the window wall to the inner wall and floor to
ceiling in both panels on every frame, stacked, "furnace" above and "heat pump" below, **from the moment the heating
comes on to 24:47 of the solve** at 75 times speed, every fifth section write, 477 frames at 24 fps. It is coloured by
air temperature on a 62-90 °F scale, with air parcels, a clock, the furnace's on/off sign on its schedule, and the
question "Home heating: furnace or heat pump?". Each panel carries one number: how much colder the feet are than the
head, in whole °F, from the two boxes above.

- **The seated figure is drawn, not solved**, on the sofa's hole; so are the outdoors, the window's frame, the
  grilles, the arrows and the labels.
- **Both vents blow hotter than the scale's 90 °F**, so both jets' cores show as its top colour. The cap changes no
  number.
- **The parcels are drawn, not solved**: moved through the section's velocity after the solve, 0.375 s of flow a frame
  where a frame is 3.125 s, so they show direction, not distance.
- At frame 0 the two rooms are one colour; from the first moving frame the furnace's jet is the hotter. In mean colour
  the panels come close twice, at 10:37-11:15 and 23:07-23:45, late in each off phase, when what differs is the jet
  and the floor layer.

## What it cannot

- **No radiation, no air leakage.** Nothing radiates between the window, the walls, the floor, the ceiling and the sofa,
  and no cold air leaks in. So the floor stays near its starting 66 °F under a warm ceiling, which makes the
  head-to-feet gap larger in both rooms than in a real one: the run's means of 6.0 and 3.8 °F are on the high side,
  against ISO 7730's usual limit of 3 K (5.4 °F) between head and ankles. Their order, the heat pump's the smaller, is
  what to read, not their size. And with no leaks and the walls storing, **both rooms warm far faster than a real one**,
  7.7 °F (furnace) and 8.9 °F (heat pump) in 25 minutes, against the 2-3 °F our brief expected; neither room has
  settled, and no thermostat stops either.
- **The furnace's cycle is imposed.** 7:18 on and 5:06 off, twice, from the test procedure's oversized furnace on a
  design day, with no thermostat in the model, no blower delay and no heat after the burner stops. A thermostat would
  set its own cycle as the room warms, a two-stage or modulating furnace would cycle less, and a furnace sized to the
  room would run longer; the furnace's 72-79 °F swing at the head is the model's upper end, not a forecast. The heat
  pump runs nonstop because this is a cold evening; on a mild one it would cycle too.
- **The seated person is drawn, not modelled.** The head and the feet are boxes of air where they would be; there is no
  body heat, no plume off a person and no blocking of the flow by one. The number is air temperature only: not radiant
  warmth, which Bailes says matters more ("Mean radiant temperature is more important"), and not the draught on skin,
  which the heat pump's larger flow adds to. The head box's mean speed over the run is 0.067 m/s with the heat pump
  against 0.039 m/s with the furnace, and the fastest air in either box is under 0.18 m/s.
- **The same heat over each cycle is by design.** The two flows are chosen so that each cycle gets the same heat above
  the return's air (398.6 kJ in the half room, 0.11% and 0.02% apart); it is not a finding. Nor does the same heat in
  mean the same heat kept: the furnace's room gives more of it to the ceiling and keeps less in its air (above).
- **The re-solve.** The first furnace run's return let air back in at a fixed 66 °F while the blower was off (1.1 and
  1.3 kg of it per off phase), which cooled the floor behind the sofa by 3.0 and 4.7 °F within 10 s of the two
  switch-offs. The re-solve changed only that, the return's backflow at its own outward mean, and the behind-the-sofa
  strip then fell 0.9 and 0.6 °F. Before the first switch-off nothing differs between the two, but the re-solve's
  first 438 s matched the first run only to **4.4e-4 K at most (at the feet, 2.9e-4 K at the register and 1.0e-4 K at
  the head)**, not to the 1e-6 K asked, while an unchanged copy of the first run's inputs on the re-solve's machine
  also differed from the first run by up to **3.2e-4 K**. The differences are of one size, and far below the 1 °F of
  the clip's number, but what makes them is not identified.
- **The feet dip after each switch-off comes from the floor layer, not from the return.** As above: the cold air on
  the floor piles against the sofa's front once the jet stops, in the first run and in the re-solve alike.
- **No mesh or time-step independence.** One graded mesh, 2.5-10 cm, with wall functions on 5-10 cm cells over most
  of the walls, at Courant 1. No finer mesh or smaller step was solved, and no uncertainty bar is put on the 6.0 and
  3.8 °F.
- **Nothing about bills or efficiency.** The case says nothing about running costs, efficiency, heat pump COP, gas
  against electricity, defrost, or a whole house. It is one room, one cold evening and 25 minutes.
- **One room, one register, half of it.** The half room on a symmetry plane through the register keeps the jet on the
  plane; a register off the centreline, a second register, a return elsewhere, a door or furniture would change where
  the air goes. The sofa is a solid block.
- **RANS, one run each.** k-ω SST with wall functions; the jet and the layers it drives are unsteady and these are
  single realisations.

## Sources

- Allison Bailes, Energy Vanguard, "Heat Pump or Furnace: Which Is Better for Comfort?"
  (https://www.energyvanguard.com/blog/heat-pump-or-furnace-which-is-better-for-comfort/), opened 25 Nov 2026: "The
  reality is that properly designed heat pumps can provide more comfortable heating than furnaces"; "With
  high-temperature air, the furnace blasts you with hot air for a short time and then goes off. Then it comes back on
  a while later and blasts you again"; furnace air "is about 125 F (There's some variation, but this is typical.)",
  heat pump air "only about 95 F"; "Mean radiant temperature is more important". Readers' comments under it: "There is
  no question for me that the heat pumps are way more comfortable"; "I do prefer heat pumps when it comes to comfort";
  an installer in Atlanta, "if customer has gas just get gas furnace ... They are more comfortable then heat pumps"; and
  "Do you think blowing 95F air from heat pump ... is comfortable in winter? Of course not!"
- Trane, "Heat Pump vs Furnace"
  (https://www.trane.com/residential/en/resources/blog/furnace-heat-vs-heat-pump-heat/), opened 25 Nov 2026: heat pump
  air is "Warm, but not as 'toasty' as gas heat."
- American Standard, S8X1B040M2PSCA/C product submittal (S8X1B040M2-SUB-2D-EN): 40,000 Btu/h single-stage gas furnace,
  32,500 Btu/h output; temperature rise 59 °F at 500 CFM and 49 °F at 600 CFM, 30-60 °F allowed.
- Carrier, 25HPA3 Performance Series heat pump, product data, heating performance of the 25HPA324 at 70 °F indoors:
  17.67 MBtu/h at 700 CFM and 27 °F outdoors, 21.03 at 37 °F.
- NBSIR 78-1543 (National Bureau of Standards, the basis of the US furnace test procedure), appendix: a unit 70%
  oversized at the design outdoor temperature and t_on = 60 X / (4 N X (1 - X)) min with N = 5 cycles an hour for
  furnaces, giving the procedure's 3.87 min on and 13.3 min off at 42 °F outdoors.
- Honeywell FocusPRO installer guide 69-2695: 5 cycles an hour for gas or oil furnaces under 90% efficiency.
- S. Pigg, "Electricity Use by New Furnaces", *Home Energy*, Nov/Dec 2003: 31 Wisconsin furnaces, about 1,000 hours
  and 6,000 cycles a season, "most furnaces are considerably oversized".
- ISO 7730: the usual 3 K limit of the air temperature difference between head and ankles for a seated person, quoted
  as the usual value, not read from the standard here.
- The buoyant model, the schemes, the storing walls, the observer and the monitor's form:
  [`closedRegister`](../closedRegister).

## How the case got here

**The solve.** The case was set up and solved by an agent on a cloud workspace of four cores and checked by us, on
25 Nov 2026. Before production it tested the back film's steady flux against the 1-D hand value (to 3e-12 and 4e-12
for the outer wall's and the ceiling's), 200 steps of each run (the register's flow within 7e-8 of its target and its
heat within 1.1e-6 of 535.9 and 910.1 W), the furnace's switch-off and switch-on on a shifted clock (no flow and no
heat from the shut register) and 50 steps of still air (under 1e-4 m/s), and fixed its own mistakes before any
production: parentheses in topoSet's box entries, a header for the test-step reader, a scalar lookup of U and a needless
cast in the register's code, and the switch test's table, which first shifted only the temperature. No physics, mesh,
scheme, step or corrector setting was changed by any of them. Both runs went from rest to 1488 s in one segment each,
one after the other on all four cores; with the tests that took 5.95 h of the 10 h we allow a solve.

**The re-solve of the furnace**, the same day in the same study, changed the return's temperature condition and
loaded its library, and nothing else: the diff of every input of the two furnace runs is those two lines. A test in a
room started at 296.04 K, 4 K from the old fixed 292.04 K, brought the backflow in within 2e-5 K of the return's mean.
Its first launch was stopped at its 120 s write because its rows were not the first run's to 1e-6 K; the unchanged
inputs, run on the same machine, and a repeat of the new ones differed by as much, so it was relaunched from 0 and
went **straight through from rest to 1488 s in one segment, with no restart**: one `Starting time loop` and the log
ends in `End`. It took 7,219 s of wall time on four ranks against the first run's 7,971 s, and 4.02 h with its tests
and the unchanged control, under its own 10 h. The heat pump's run took 11,904 s. The solved runs carried an abort
function object, which was never used and is left out here.

**A straight run with this case's `Allrun` is the same run**, but **it will not repeat the solved runs bit for bit**:
scotch's decomposition can differ from machine to machine, parallel sums round differently, and in a turbulent
buoyant flow that round-off grows, as the re-solve's own first 438 s show (above).

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI and `wmake`, and Python 3 with NumPy.

    cd cases/furnaceVsHeatPump
    ./Allrun furnace             # [nProcs], default 4; compiles both conditions and builds the mesh first
    ./Allrun heatPump            # default 4
    python3 scripts/extract_results.py runs results

The first `Allrun` compiles `src/radLayerWall85` and `src/returnMeanTemperature` into `$FOAM_USER_LIBBIN` as
`libwall85.so` and `libreturn85.so`, and builds the mesh in `runs/mesh/` with `scripts/make_mesh.py` (blockMesh, topoSet,
subsetMesh, topoSet, createPatch, in a few seconds; `cells.npz` keeps the cell centres for the start) and checkMesh.
`scripts/make_case.py` then writes `runs/<run>/`: the mesh, `0/` (the hydrostatic start, the walls, the register with
`scripts/supply.C`), `constant/` and `system/` from `template/`, and the monitor from `scripts/monitor.C`, which the
solver compiles when it starts, as it does the register's code. `Allrun` writes the t = 0 planes, decomposes by
scotch and solves from 0 to 1488 s, and once both runs have solved writes `results/`. The two runs differ in the
register's flow, rise and schedule, the return's temperature condition and the furnace's extra library.
`./Allrun --setup-only <run> [nProcs]` stops before the solve; `./Allclean` removes the runs and the mesh. The solved
runs took about 2.0 h (furnace) and 3.3 h (heat pump) on four ranks.

Each run writes 2,381 sections, 596 times of three plans and of the window and floor (VTK; the solved runs gzipped
them, about 350 MB a run), the fields every 120 s (the last three kept), and monitor files of about 6 MB. `results/`
holds the summary and each run's history every 2.5 s; no fields, meshes, planes or logs.

The files in `results/` are what `scripts/extract_results.py` wrote from the solved runs' monitors and logs (the
re-solve's for the furnace).

**Rebuilt, and how it was checked.** The agent's meshing script and the source of its back-film wall library
(`libwall85.so`) did not come back from the cloud; `scripts/make_mesh.py` and `src/radLayerWall85` are ours, rebuilt
from the solve's specification and its archived files. `scripts/make_case.py` is the agent's own case writer with
relative paths, and `scripts/monitor.C`, `scripts/supply.C` and `src/returnMeanTemperature` are the solved runs' code.
Checked from a clean copy of this folder on 26 Nov 2026, with both conditions compiled into a scratch library folder:
`make_mesh.py` rebuilds the solved mesh's `boundary` byte for byte (55,200 cells, every patch's faces and start face),
its cell centres agree with the solved mesh's, which were kept only as float32, to 1.4e-7 m, and `checkMesh` says
Mesh OK, non-orthogonality 0, aspect ratio 4.00. `make_case.py` writes the furnace's `0/T` byte for byte (the only
field file archived), and `system/fvSchemes`, `fvSolution`, `decomposeParDict`, `functions`, `planesT0` and
`controlDict` of both runs byte for byte but for the libraries' paths and the unused abort function object; the t = 0
planes are the solved runs' byte for byte once theirs are unzipped. The starting `p` and `p_rgh` were not archived;
they come from exact cell centres here and from float32 ones in the solve, about 3e-6 Pa apart. Both runs were then
solved from the clean copy on four ranks of another machine, the furnace to 450 s (through its first switch-off) and
the heat pump to 300 s, and their monitors compared row by row with the solved runs': the row times are identical
throughout, and the largest differences are 2.6e-4 K at the feet, 8.2e-5 K at the head, 1.1e-5 K in the room's mean
air and 2.0e-4 K at the register (furnace), and 3.7e-5, 3.4e-5, 2.5e-6 and 2.2e-4 K (heat pump), the size of the
re-solve's own differences from the first run and from its unchanged control (above). The ceiling's and outer wall's
heat into the surface differ from the solved runs' by at most 2.1e-3 and 5.1e-3 W, where leaving out the back film
would change them by about 39 and 27 W at 300 s (a 1-D estimate from the solved surface temperatures), so the rebuilt
film is the solved one. After the switch-off the rebuilt furnace's backflow comes in within 0.018 K of the return's
outward mean, as in the solve, and within 2.7e-4 K of the solved re-solve's backflow temperature, against 3.5 K from
the first run's fixed 66 °F. No full rebuilt run was solved. `scripts/extract_results.py` on the solved runs'
monitors gives the study's own figures: the 398,641.69 and 398,191.87 J of the first cycle and 398,721.18 J of the heat
pump's second, the +3.515e-5 and +1.398e-4 budgets, and the whole-run and last-cycle means of the head and the feet to within 0.003 K (the study carries
them to 1488 s and starts the last cycle at exactly 744 s; `extract_results.py` stops at the last monitor row, 1487.5 s).
