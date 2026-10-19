# A radiator under a cold window, or on the opposite wall; and a curtain over it

Radiators go under windows because cold air falls off the glass, and the radiator's warm
air is meant to stop it. This case asks what that does to the room: in a 2-D vertical
section through a window and a radiator, does the radiator under the window stop the cold
air falling off the glass, and where does that air go when the same radiator stands on the
wall opposite? It is about where the cold air goes, not about heat loss through the window
or energy use.

One OpenFOAM case, two runs that differ only in where the radiator box is:

    ./Allrun window              # radiator under the window, 0-3600 s
    ./Allrun opposite            # radiator on the inner wall, 0-3600 s
    ./Allrun window start300     # the first 300 s again, written every 0.625 s (the clip)
    ./Allrun opposite start300

Three more runs put a curtain over the radiator under the window, hanging in front of it to
the floor, tucked in at the sill, and cut short at the sill, and ask how much of the
radiator's heat reaches the room in the first five minutes:

    ./Allrun hanging             # the curtain hangs from the rail to the floor, 0.15 m out
    ./Allrun tucked              # the same curtain tucked in at the sill
    ./Allrun sill 2              # the same curtain ending at the sill, 0.14 m above the radiator

They have their own section, [Curtains](#curtains), with their own limits.

Opening the window above the radiator, wide open or on tilt, is a case of its own on this
room made 3-D and 3.5 m wide: [`windowAiring`](../windowAiring).

## The room

| | value | from |
|---|---|---|
| section | 4.0 m from the window wall to the inner wall, 2.4 m high, 1 m deep (every flux is per metre of window and radiator) | ours |
| window | glass 1.2 m tall, sill 0.90 m above the floor | ours |
| glass | ordinary double glazing, air-filled 12 mm gap, PVC-U frame: U = 2.8 W/m2K | UK SAP default U-values (Scottish Government, *Tables of U-values and thermal conductivity*, Part 6.A) |
| outside | 0 C beyond the glass | ours |
| radiator | a box 0.085 m deep and 0.60 m tall, bottom 0.15 m above the floor, 0.04 m off the wall, at 60 W/m (see below) | the box is a Stelrad Compact K1 600 x 1000 (83 mm deep); the output is derived below |
| other surfaces | ceiling and inner wall held at 20 C (the rest of the house); floor and the outside wall below and above the glass adiabatic | ours |
| start | air at rest at a uniform 20 C; at t = 0 the glass sees 0 C outside and the radiator comes on | ours |

The glass loses heat through `externalWallHeatFluxTemperature` with h = 4.403 W/m2K to
0 C. That is U = 2.8 W/m2K less the standard 0.13 m2K/W inside surface resistance; the
inside film is left to the solver.

The radiator is an enthalpy source spread evenly over the cells of its box
(`constant/fvOptions`, `volumeMode absolute`, so the total is exactly the set output). Air
passes freely up through the box, as it does through a convector's fins.

## Why 60 W per metre

A real radiator heats a room 3.6 m or so wide, together with its air, walls and furniture.
The section has none of that: its only real loss is 1.2 m of double glazing, plus whatever
the 20 C ceiling and inner wall take when the air is warmer than they are. The radiator's
output is therefore set to the section's own steady heat loss at a normal room
temperature, 20.5 C, so that the room holds near 20-21 C. There is no thermostat; the
output is constant from switch-on.

The two conductances come from heat flows measured in the case's first two solves
(described under "What it cannot"), and `derive_output.py` turns them into the output
(`results/output_derivation.json`):

- **The glass.** Its loss per kelvin of room-to-outside difference was 2.67 W/m K
  (opposite) and 2.85 W/m K (window) in the second solve's 39-40 C rooms. With no plume on
  the pane the figure hardly moved between that solve and the first (2.61 W/m K in a
  21.7 C room). Under the window it depends on the plume washing the pane, so the second
  solve's 2.85, the closer of the two to an unwashed pane, is used.
- **The ceiling and inner wall.** Together they took 498.3 W/m (window) and 506.1 W/m
  (opposite) at 20.1 K and 19.0 K above them: 24.8 and 26.6 W/m K. For natural convection
  the coefficient grows as the cube root of the temperature difference, so at a difference
  dT they take K (dT/dT_ref)^(1/3) dT, about 3.6 W/m at 0.5 K.

The steady loss at room mean T is then

    Q(T) = K_glass T + K_walls ((T - 20)/dT_ref)^(1/3) (T - 20)

| room mean | 20.00 | 20.25 | 20.50 | 20.75 | 21.00 C |
|---|---:|---:|---:|---:|---:|
| window | 57.1 | 59.2 | 62.1 | 65.4 | 69.1 W/m |
| opposite | 53.3 | 55.6 | 58.6 | 62.1 | 66.0 W/m |

At 20.5 C the two lose 62.1 and 58.6 W/m. Their mean, 60.4 W/m, rounds to **60 W/m**, the
same in both runs. With that output the same model predicts the rooms settle at 20.3 C
(window) and 20.6 C (opposite).

60 W/m is a tenth of the 620 W/m the Stelrad K1 gives at a 55 C mean water temperature in
a 20 C room (980 W at dT50 to EN 442, scaled to dT35 by EN 442's exponent of 1.3). By the
same exponent it is that radiator about 6 K above the room. That is the price of a section
with no outside wall, no ventilation and no rest of the room to heat: the plume carries only
a little more heat than the glass takes out.

## The model

- `buoyantPimpleFoam` (OpenFOAM v2512), air as a perfect gas, k-omega SST with the
  buoyancy production term in k (`buoyancyTurbSource`), wall functions on every wall.
- **Mesh.** blockMesh, 290 x 230 cells, one cell thick (66,700 cells): 5 mm across the
  first and last 0.20 m (the glass, the radiators, the inner wall), widening to about
  22 mm mid-room; about 3 mm at the floor and ceiling, 10 mm through the radiator and sill
  band, 12 mm over the window. `checkMesh`: aspect ratio at most 7.3, no non-orthogonality.
  The radiator zone is 1,020 cells in either run.
- **Time step.** Courant number at most 1, two outer and two pressure corrections, the
  pressure reference point in the middle of the room (at a corner cell, with the floor
  adiabatic, the reference cell's imbalance acted as a heat source). The final pressure
  solve is capped at 100 iterations: at 60 W/m it stalls at its round-off floor,
  1.2-1.4e-8 against the 1e-8 tolerance, and without the cap spent 1000 iterations a step
  there. The cap changes only the wall time: the stalled solves' final residuals had a
  median of 1.42e-8 before it and 1.58e-8 after. At Courant 1 it acts only at start-up
  (24 times, all before 0.5 s).
- **Why Courant 1, not 5.** The first attempt at this output ran at Courant 5. Its window
  run lost 10.4 W/m of heat, a sixth of the radiator, in bursts about a minute apart, while
  the opposite run closed its budget. Two 0-120 s tests of the window run, each changing
  one setting, settled it: at Courant 1 every 7.5 s interval closed to within 0.2 W/m
  (mean 0.01 W/m); with four outer correctors at Courant 5 the bursts went, but the budget
  still swung by -7 to +4 W/m from one interval to the next. Both runs use Courant 1, so
  the two panels have the same numerics.
- **Output.** The mid-plane section (T and U) at every write, the sill line and the floor
  line, the probes, and monitors of the room mean (`roomMeanT`), the glass's inside surface
  (`glassTs`), each wall's heat flux, the extremes of T, and the room's internal energy at
  every step (`energyCheck`, (cv/R) times the integral of p, which for a closed perfect-gas
  box is its internal energy).

**The heat budget closes.** The room is closed, so 60 W/m plus the wall heat flux must
equal the rise in internal energy. Over every 7.5 s interval of the hour it does, to within
0.20 W/m in the window run and 0.14 W/m in the opposite run (means -0.004 and -0.001 W/m;
`results/hour/*_heat_budget.csv`, `results/hour/summary.md`). Over the last 1200 s the
window room loses 50.5 W/m through the glass and 9.3 W/m to the ceiling and inner wall;
the opposite room 48.0 and 12.0 W/m.

## Results

Means over 3000-3600 s, after the hour from switch-on (`results/hour/summary.md`). The
floor layer is the air below 0.1 m and head height 1.0-1.2 m, both from 0.3 to 2.0 m from
the glass.

| | floor layer | head height | room mean | floor below room mean |
|---|---:|---:|---:|---:|
| radiator under the window | 20.57 C | 20.94 C | 20.96 C | 0.38 K |
| radiator opposite | 18.43 C | 21.13 C | 20.58 C | 2.15 K |

(The room means are the monitor at 3600 s; averaged over 3000-3600 s they are 20.955 and
20.581 C.)

**With the radiator opposite, the floor a metre or two from the glass is 2.1 C colder**,
though that room's air at head height is 0.2 C warmer. The cold air off the glass runs
across the floor and fills a pool about 0.5 m deep across the whole room, which the
radiator draws in at its foot on the far wall. Under the window the room is nearly even
from floor to head height.

**At the sill** (y = 0.90 m, from the glass to 0.30 m out; m3/s per metre, gross one way):

| | up | down | air falling past the sill |
|---|---:|---:|---:|
| under the window | 0.0193 | 0.0085 | 17.9 C |
| opposite | 0.0000 | 0.0260 | 19.8 C |

Under the window the radiator turns the flow at the sill upward, 2.3 to 1. The air that
still falls past the sill stays by the radiator: across the floor line 1.0 m from the
glass (y < 0.30 m) only 0.0003 m3/s per metre moves each way. With the radiator opposite
all the flow at the sill is downward. At the floor line it is 0.0018 away from the window
and 0.0071 toward it, because the line sits where the cold current lifts off the floor in
a standing roll at about 0.9 m from the glass, and the roll's return flow passes under it.

**It settles into one regime.** From 600 to 3600 s, in successive 600 s windows, the
opposite floor layer averages 18.28, 18.39, 18.42, 18.42 and 18.43 C and its floor-line
fluxes hardly move (`results/hour/summary.md`). The window run is slower: its floor layer
rises 20.13, 20.34, 20.46, 20.53 and 20.57 C. The room means:

| room mean | 120 s | 600 s | 1200 s | 2400 s | 3600 s |
|---|---:|---:|---:|---:|---:|
| under the window | 20.20 | 20.58 | 20.79 | 20.93 | 20.96 C |
| opposite | 20.13 | 20.38 | 20.52 | 20.57 | 20.58 C |

The opposite room lands on the derivation's 20.6 C. The window room settles 0.7 K above
its 20.3 C, because the derivation took that glass's conductance from a plume ten times
stronger; here the window glass loses 2.41 W/m K (50.5 W/m at 20.96 K), close to the
opposite run's 2.33. Both finish inside 20-21 C.

**The start-up** (`results/hour/*_history.csv`). With the radiator opposite, the cold
current off the glass crosses the floor in the first minute: air at least 0.5 K below the
room mean in the bottom row of cells reaches 2.5 m from the glass at 30 s and the far wall
by 60 s (`cold_floor_reach_m`), and the pool thickens until about 480 s. Under the window
the floor stays within about 0.2 K of the room mean for the first two and a half minutes;
the cold layer reaches the floor at about 180 s, and the plume has pushed it back by about
480 s. Taking each write's temperature less its own room mean, its RMS distance from the
settled pattern (`pattern_rms_K`) falls to the settled scatter (0.02 K under the window,
0.07-0.10 K opposite) by about 480 s under the window and 720 s opposite:

| t | 120 | 240 | 360 | 480 | 600 | 720 | 960 | 1200 s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| under the window | 0.29 | 0.17 | 0.10 | 0.10 | 0.09 | 0.08 | 0.08 | 0.07 K |
| opposite | 0.59 | 0.33 | 0.25 | 0.19 | 0.15 | 0.10 | 0.10 | 0.08 K |

After that the pictures change only by a slow, even warming: the room means rise a further
0.3 K (window) and 0.2 K (opposite) between 720 and 3600 s.

### Against Heiselberg

P. Heiselberg, "Draught risk from cold vertical surfaces", *Building and Environment* 29
(1994) 297-301, gives the largest velocity in the cold flow along the floor from the glass
height, the room-to-glass temperature difference and the distance from the wall. Here the
room mean less the glass's inside surface (3000-3600 s) is 11.5 K opposite and 11.4 K under
the window, inside the 5-15 K the correlation was fitted over. The model figure is the
largest |Ux| below 0.3 m in the velocity profile averaged over 3000-3600 s, m/s:

| x from the glass | Heiselberg | opposite | ratio | under the window | ratio |
|---|---:|---:|---:|---:|---:|
| 0.5 m | 0.194 | 0.175 | 0.90 | 0.005 | 0.03 |
| 1.0 m | 0.152 | 0.068 | 0.44 | 0.007 | 0.05 |
| 2.0 m | 0.104 | 0.061 | 0.58 | 0.005 | 0.05 |

(Heiselberg's figure is for the opposite run's 11.5 K; at the window run's 11.4 K it is
0.193 / 0.151 / 0.104.) At 0.5 m, where the downdraught off the glass lands on the floor,
the opposite run is within 10% of Heiselberg. Further out it runs at about half, because
the current lifts off the floor into the standing roll at about 0.9 m instead of running
on. Our explanation is that the roll is where the falling air meets the cold pool, which is
nearly its own temperature, so the current has little buoyancy left to hold it to the
floor; Heiselberg's rooms were mixed above the floor and had no such pool. **That
explanation has not been tested.** Under the window the correlation does not apply: the
plume removes the downdraught, and 0.005-0.007 m/s is what is left on the floor.

## The 0-300 s re-solve

The clip shows the first 300 s at 15 times real time, one frame per write, so it needs
writes every 0.625 s instead of 7.5 s. `./Allrun <run> start300` is the same case with
only `tEnd` 3600 -> 300 and `writeInt` 7.5 -> 0.625. With `writeControl adjustableRunTime`
the solver spreads the time to the next write over equal steps, so the two solves' steps
differ from the first (0.012 s against 0.012019 s) and their planes cannot be identical.
`compare_start300.py` compares them at the 40 times both wrote
(`results/start300/vs_hour.txt`):

- **Opposite** tracks the hour run throughout: an RMS temperature difference of
  0.004-0.021 K to 270 s with no cell off by 0.5 K. An eddy separates them a little at
  277.5-292.5 s (RMS up to 0.07 K, at most 1.45 K in one cell); by 300 s the RMS is 0.027 K.
- **Under the window** the eddies by the glass and the radiator part from about 60 s. The
  worst stretch is 90-127.5 s, with 0.5-1.2% of cells off by more than 0.5 K and single
  cells at the glass up to 8.3 K apart. From 135 to 225 s the difference spreads but is
  shallower, 6-15% of cells off by more than 0.1 K and at most 1.3 K. After 225 s the two
  come back together: from 232.5 to 285 s no cell is off by 0.5 K.
- The room means agree within 0.0013 K at every common time, and both solves' heat budgets
  close within 0.2 W/m in every 7.5 s interval (means 0.038 and 0.041 W/m under the window,
  0.015 and 0.014 W/m opposite).

So it is the same flow, with the same budgets and room means, but for roughly 60-230 s the
window panel's eddies are not the hour run's. Over the clip's 300 s
(`results/start300/summary.md`, 30 s means), the opposite floor is 0.57 K below its room
mean in the first 30 s, 1.45-2.07 K below from 30 to 270 s and 2.10 K below at 270-300 s
(settled: 2.15 K). Under the window the floor is at most 0.21 K below the room mean until
150 s, then 0.55-0.77 K below it to the end, still more than its settled 0.38 K because
the plume pushes the cold layer back later.

The re-solve behind the clip was stopped partway (window at 176.875 s, opposite at
116.25 s) and continued from its last complete writes. For the continuation, `pRefValue`
in `system/fvSolution` was set to that run's own pressure at the reference point at the
restart time (100096.135289 Pa and 100043.152897 Pa), because on startup the solver shifts
the pressure to `pRefValue`, and at 1e5 the shift put 888 J/m (window) and 414 J/m
(opposite) of spurious heat into the rooms in a first attempt, which was discarded. With
each run's own value the continued runs took the stopped runs' time steps exactly. That
is the only dictionary difference from what `./Allrun <run> start300` writes, and a run
straight through from t = 0 needs no such change.

## What the clip shows, and what it does not

**It shows** the whole 4.0 x 2.4 m section twice, the radiator under the window above and
opposite below, from switch-on to 300 s of the start300 runs: air temperature on one fixed
scale (17-24 C, centred on the 20 C start) with moving streamlines, and the window, the
radiator and the outside drawn and labelled. Frame 0 is the room at rest at 20 C, which
the solver does not write.

**It does not show** any number, or the settled hour: at 300 s the window room's floor is
still colder than it will settle.

## What it cannot

- **A 2-D section.** The window and radiator are infinitely long here. A real window and
  radiator are 1.0-1.2 m long, and air goes round their ends; a real room is wider than the
  section, so it has more air and surfaces per metre of radiator.
- **The floor is adiabatic**, and so is the outside wall below and above the glass. A real
  floor exchanges heat with the cold pool, and a real outside wall loses heat. The ceiling
  and inner wall are held at 20 C to stand for the rest of the house. No radiation: the
  glass's inside film is convection only, which is why it loses 2.41 (window) and
  2.33 W/m K (opposite) here, an effective U of about 2 W/m2K over its 1.2 m2, rather
  than 2.8.
- **A fixed output with no thermostat.** 60 W/m is the section's own loss at 20.5 C,
  derived from the earlier solves, constant from switch-on. It is a tenth of a real K1 at
  normal water temperatures, so the plume is weak. A real radiator under a real window
  would run hotter, and its plume would push harder against the glass's downdraught.
- **The first two solves were set aside.** The first held the floor at 20 C and relaxed
  every cell toward 20 C with a distributed sink standing for the rest of the room's air
  and fabric, at 620 W/m. Both floors then read 20.06 C, and the difference showed only in
  velocity (the floor draught 0.20 m/s opposite against 0.07 m/s under the window, within
  5-12% of Heiselberg). The second freed the floor and removed the sink, with nothing else
  changed; at 620 W/m the rooms warmed by 19-20 K, to 40.1 C (window) and 39.0 C
  (opposite), both floors stratified cold, and the opposite run's floor flow changed regime
  at about 1230 s, which that solve did not run long enough to follow. Against Heiselberg it
  gave 1.58 / 1.35 / 0.86 at 0.5 / 1.0 / 2.0 m, with a 19 K difference outside the
  correlation's range. This case is the second solve's with the output set to 60 W/m, the
  hour, a write every 7.5 s, Courant 1, the pressure-iteration cap and the `energyCheck`
  monitor. Its heat flows are the inputs to `derive_output.py`; its dictionaries are not
  kept here, but setting `radPowerPerM 620`, `tEnd 1440`, `writeInt 1.5` and `maxCoNum 5`
  in `config/caseSettings` gives them, apart from the cap and the monitor.
- **The standing-roll explanation is untested.** Why the opposite run's floor draught is
  about half Heiselberg's beyond 1 m is our reading of the flow, not something checked
  (for example with a mixed room or a floor that exchanges heat).
- **URANS on one mesh.** No mesh or time-step study beyond the Courant test above. Under the
  window the eddies by the glass are sensitive to the time step: two solves of the same
  case whose first steps differ by 0.2% part there for minutes (see the re-solve above).
- **An hour from a uniform start.** The window room's floor layer is still rising slowly at
  3600 s (an exponential fitted from 600 s settles at 20.64 C, 0.06 K above its 3600 s
  value).

## Curtains

Interior designers like curtains that reach the floor; energy advice in Britain and Germany says a
curtain should not hang over the radiator. The UK's (the Centre for Sustainable Energy, Age
UK) is to tuck long curtains behind it, Germany's (the Verbraucherzentrale, co2online) to end
them above it. These three runs take the window run's room and radiator from switch-on and add
one curtain, in three shapes. Where does the radiator's plume go, and how much of its heat has
crossed into the room after five minutes?

- **hanging.** The curtain hangs straight down in front of the radiator and the window, from
  the rail to just above the floor.
- **tucked.** The same curtain from the same rail, its hem tucked in at the bottom of the
  glass, so it drapes as one straight sheet from the rail to the sill and the radiator below
  it faces the room.
- **sill.** The same curtain from the same rail, hanging straight down as in `hanging` but cut
  at sill length, so the radiator below its hem faces the room. This is the German advice, and
  what a viewer asked for under the first curtain clip.

Everything else is the window run's `start300`: the room, the glass at U = 2.8 W/m2K to 0 C,
the radiator box at 60 W/m, the mesh, the numerics, Courant 1, the pressure-iteration cap, the
start from rest at 20 C and 0-300 s with a write every 0.625 s. All three read the same
`runs/start300/config/caseSettings` as the window and opposite runs.

### The curtain

In the case's coordinates (x from the outside wall into the room, y up from the floor; the
glass is x = 0 from y = 0.90 to 2.10, the radiator box x = 0.040-0.123, y = 0.15-0.75):

| | value | from |
|---|---|---|
| rail | y = 2.20 m, 0.10 m above the top of the glass | Dunelm's fitting guide: "We recommend that your curtain pole sits 10cm above the window" |
| distance from the wall | 0.15 m, about 27 mm in front of the radiator | a standard 99 mm bracket would not clear the radiator, so an extendable one of the kind sold to hang curtains past radiators (Hallis Hudson Neo, 124 to 165 mm from the wall); Orłowska et al. (below) hung theirs 2 cm from the radiator |
| hem, hanging | 0.01 m above the floor | B&Q's measuring guide: "subtract 1cm for clearance" |
| tucked | a straight sheet from (0.15, 2.20) to (0, 0.90), the bottom of the glass | ours; the room has no window board |
| hem, sill | 0.89 m, 1 cm below the bottom of the glass and 0.14 m above the radiator's top | B&Q's measuring guide: windowsill curtains "sit just above the sill ... Aim for about 1cm above the sill"; this room has no window board, so the sill is the bottom of the glass |
| fabric | impermeable, a conducting layer of 0.03 m2K/W with no thermal mass | ours, a lined curtain; it is small next to the air films on its two faces, which the solver resolves |
| above the curtain | open: nothing closes the gap to the ceiling or to the wall | as over a curtain heading with no pelmet |

The curtain is a baffle in the unchanged blockMesh mesh, 66,700 cells. `make_curtain_faces.py`
picks the internal cell faces along the sheet into a face set, `topoSet` (`system/faceZoneDict`)
makes it a face zone, and `createBaffles` (`system/createBafflesDict`) splits it into two
coincident `mappedWall` patches, `curtainA` and `curtainB`. No air crosses them (no-slip on
both faces). Heat crosses through `compressible::turbulentTemperatureRadCoupledMixed` with
one layer 0.9 mm thick at 0.03 W/m K, which is 0.03 m2K/W, and `qr none`: no radiation.
The ends are snapped to whole cell faces rather than remeshed (`results/curtains/*_curtain_geometry.txt`):

- **hanging**: 212 vertical faces at x = 0.15, from y = 0.0076 to 2.196 m (asked for: 0.01
  and 2.20).
- **tucked**: 144 faces in a staircase of vertical and horizontal faces that separates the
  cells either side of the straight line, from (0, 0.90) exactly to y = 2.206 m. It is a
  staircase, not a diagonal wall; its faces add up to 1.456 m of sheet per metre.
- **sill**: `hanging`'s faces with the lower limit raised to 0.89 m, 114 vertical faces at
  x = 0.15 from y = 0.890 to 2.196 m, 1.306 m of sheet per metre.

The first 0.20 m of the mesh has 5 mm columns, so 30 cells span the wall to the curtain and
5-6 the 27 mm between the radiator's front and the curtain; the glass's cold film and the
plume each have cells of their own in the gap. `checkMesh` passes all three runs.

The curtain runs' files are in `curtains/`, laid over `template/` by `Allrun`: the fields
with the curtain's two patches (`curtains/0.orig`), `controlDict` with the curtain's heat
flux monitored, and the two dictionaries above; `sill` uses them unchanged. In `controlDict` the probes are at x = 1, 2
and 3 m, at 0.1 and 1.1 m up (12's were at 0.5, 1 and 2 m), and 12's sill and floor lines
are not written. The window and opposite runs are unchanged.

### The heat that reaches the room

The heat reaching the room is what crosses the line x = 0.15 from the floor to the ceiling,
the curtain's line in `hanging` and `sill`: the advected enthalpy, net, rho Ux cp (T - 293.15 K)
as the solver's sensible enthalpy is referenced, plus in `hanging` and `sill` the heat conducted
through the curtain (the wall heat flux on `curtainB`, its room face). On the curtain's own rows no air
crosses, so only the rows above and below it carry air. In `tucked` the sheet lies behind
that line and only air crosses it. The density is 1e5/(R T), since the section has T and U
but not p. The cumulative heat from t = 0 (trapezoidal, from a still room) over the
radiator's 60 t J/m is the share. `postprocess_curtains.py` writes it, the 7.5 s heat
budgets as `postprocess.py` does them, the probes, and the gross flows over the curtain's
top (y = 2.20, x = 0-0.15) and, in `hanging` and `sill`, under its hem (x = 0.15, below the
hem: y < 0.01 and y < 0.89), to `results/curtains/`.

**The heat budget closes.** Over every 7.5 s interval the radiator, the wall heat flux and
the rise in internal energy agree to within -0.28 to +0.20 W/m (`hanging`), -0.04 to
+0.21 W/m (`tucked`) and -0.21 to +0.44 W/m (`sill`) (`results/curtains/*_heat_budget.csv`).

### Results

At 300 s (`results/curtains/summary.md`, `*_history.csv`):

| | hanging | sill | tucked |
|---|---:|---:|---:|
| share of the radiator's heat that has reached the room, 0-300 s | **14%** (13.9%) | **19%** (18.8%) | **56%** (55.7%) |
| heat into the room, cumulative | 2.51 kJ/m | 3.39 kJ/m | 10.03 kJ/m |
| heat crossing into the room at 300 s | 7.7 W/m | 10.3 W/m | 34.3 W/m |
| of which conducted through the curtain | 3.8 W/m | -0.1 W/m | (none: only air crosses x = 0.15) |
| glass loss at 300 s | 48.0 W/m | 47.3 W/m | 24.6 W/m |
| room side (x > 0.15), mean | 20.24 C | 20.42 C | 21.01 C |
| behind the curtain, mean | 21.66 C | 19.96 C | 12.89 C |

Behind the curtain is x < 0.15 for `hanging`, x < 0.15 between the hem and the curtain's top
for `sill`, and the pocket between the glass and the drape for `tucked`.

For comparison, the window run's `start300` with no curtain loses 49.5 W/m through the glass
over 285-300 s (`results/start300/window_heat_budget.csv`).

**Hanging in front,** the plume rises in the 0.15 m gap between the curtain and the glass,
washes the glass, and leaves over the curtain's top: 0.0031 m3/s per metre into the room
over the top and 0.0004 back, means over 150-300 s, while 0.0024 m3/s per metre is drawn in
under the hem from the room. The glass loses about what it does with no curtain, the gap
fills with warm air, and by 300 s 14% of the radiator's heat has crossed into the room.

**Tucked in at the sill,** the plume runs up the curtain's room face, along the ceiling and
round the room. The curtain shields the room from the glass, whose loss halves, and the
pocket between the glass and the drape cools to 12.9 C. 63% of the heat has reached the
room by 30 s and 56% by 300 s; over the top of the drape, a ledge here, about 0.002 m3/s
per metre moves each way.

**Ending at the sill gains little over hanging to the floor, and far less than tucking in.**
The radiator's plume no longer rises behind the curtain. Instead the gap between the curtain
and the glass becomes a channel for cold air: air cooled on the glass falls down it, out under
the hem and over the radiator, and room air is drawn into the gap over the curtain's top.
Over 150-300 s, 0.0118 m3/s per metre comes down into the gap over the top (y = 2.20) and
0.0009 goes up, and under the hem 0.0249 m3/s per metre goes into the room and 0.0136 back.
The plume is turned into the room below the hem, 0.3-0.6 m up, level with the middle of the
radiator, and room air is drawn back towards it along the floor. The flow down into the gap
over the top starts between 15 and 20 s after switch-on and keeps this pattern to 300 s. The
glass loses 47.3 W/m, close to the 48.0 W/m with the curtain hanging to the floor and the
49.5 W/m with no curtain, because the shortened curtain no longer stands between the room and
the glass: it feeds the glass with room air. The share peaks at 33% at about 22 s, as the
plume first rolls into the room under the hem, and falls as the channel sets in: 23% at
30 s, 20% at 180 s and 18.8% at 300 s.

### Is the curtain too good an insulator?

A viewer asked whether the curtain in this model insulates like a sheet of styrofoam. It does
not. The sheet is a conducting layer of 0.03 m2K/W, 0.9 mm at 0.03 W/m K. A 25 mm board of
expanded polystyrene, at about 0.035 W/m K, is about 0.7 m2K/W, more than twenty times as
much. The curtain does not hold the heat back by insulating. It is airtight, so it holds the
warm air back. Heat goes through it readily: in `hanging` at 300 s, 3.8 of the 7.7 W/m
crossing into the room came through the fabric by conduction
(`results/curtains/hanging_history.csv`, `curtain_conduction_into_room_W_per_m`). A real
fabric also lets some air through, which this sheet does not (see What it cannot, below).

### Against Orłowska

The one measurement of a curtain over a radiator we found is J. Orłowska, M. Szałański and
W. Cepiński, "Testing the Temperature Fields and Power of a Flat Radiator Covered With and
Without a Curtain", *Rocznik Ochrona Środowiska* 27 (2025) 705-721,
doi:10.54740/ros.2025.057. A cotton curtain hung 2 cm in front of the radiator cut its
output by 13.4% (319.8 W to 277.0 W; open-weave guipure, 0.1%). Their rig had **no window**:
the curtain could only hold the heat back from the radiator. Here the radiator's output is
fixed, and the curtain sends the heat it holds back to the cold glass instead of the room.
The two numbers measure different things and should not be set side by side: the 14% here
is the share of a fixed output that reached the room in five minutes, not a loss of output.

### What the clip shows

The section twice, the hanging curtain above and the tucked one below, from switch-on to
300 s: air temperature on 12's scale (17-24 C) with moving air parcels, and each panel's
share of the heat that has reached the room as a whole percent. The air behind the tucked
curtain (12.9 C) and the hottest air in the hanging gap (up to 28 C) are off that scale and
are drawn at its ends.

A second clip shows the section three times, the hanging curtain at the top, the curtain
ending at the sill in the middle and the tucked one at the bottom, in the same way and on the
same scale, each with its one number: 14%, 19% and 56% at 300 s.

### What it cannot

- **A 2-D section, so no air goes round the curtain's ends.** The curtain, the radiator and
  the window are infinitely long. A real curtain has sides, and a gap between two curtains,
  and the plume can leave round them; the section cannot show it.
- **No radiation.** The radiator, the glass and the curtain exchange heat by convection
  only. A real radiator gives part of its heat as radiation, which a curtain in front of it
  would intercept; the case leaves that out, as it leaves out radiation at the glass (see
  [What it cannot](#what-it-cannot) above).
- **An impermeable sheet.** No air passes through the fabric. Real curtains let some through,
  open weaves a lot (Orłowska's guipure cost 0.1%). The sheet is also rigid and smooth, with
  no folds, no thermal mass, and its ends snapped to whole cell faces; the tucked drape is a
  staircase of faces.
- **A 60 W/m plume.** The radiator's output is the section's own heat loss, a tenth of a real
  panel radiator's at normal water temperatures (see [Why 60 W per metre](#why-60-w-per-metre)).
  A real radiator would run hotter and its plume would be stronger; how that would change
  the two shares is not tested.
- **Five minutes from switch-on.** The shares are of the heat over 0-300 s, not a steady
  state, and they are still moving at 300 s (`hanging` 12.2% at 180 s and 13.9% at 300 s,
  `tucked` 56.8% and 55.7%, `sill` 20.3% and 18.8%). No run was continued.
- **Orłowska's 13.4% was measured on a rig with no window**, so it cannot check the shares
  here, and nothing here checks it.
- **One mesh, one run per shape.** URANS with no mesh or time-step study and no repeat; the
  window run's eddies by the glass are sensitive to small changes (see
  [The 0-300 s re-solve](#the-0-300-s-re-solve)).
- **No window board.** The tucked hem meets the wall at the bottom of the glass; a real sill
  overhangs by a few centimetres. Under the sill curtain's hem, 0.14 m above the radiator, a
  real window board would overhang the radiator and could turn the plume, or the cold air off
  the glass, either side of the hem. It was not modelled.
- **Three lengths only.** The shorter "apron" lengths that end at or just below the radiator's
  top (B&Q: "about 10-15cm below the sill") were not run; each would be a run of its own.

### Running the curtains

    ./Allrun hanging             # [nProcs], default 6
    ./Allrun tucked
    ./Allrun sill 2              # solved on 2 ranks
    python3 postprocess_curtains.py   # runs/start300 -> results/curtains

`./Allrun --setup-only hanging|tucked|sill` stops before the solve. The mesh is written in ASCII
for `make_curtain_faces.py` to read, and the controlDict is set back to binary before the
solve. `postprocess_curtains.py` also writes the t = 0 plane, a still room at 20 C, into
each run's `postProcessing/clip/0/`, which the solver does not write. Like the others the
runs keep full fields for the last four writes only; the 481 sections take about 2 GB a run.

`hanging` and `tucked` were solved side by side on our own machine, 6 ranks each on separate
cores, in 3,192 s (`hanging`) and 1,622 s (`tucked`) of wall time. The case was set up by an agent and
checked by us. From a clean copy, `./Allrun --setup-only` gave both runs the solved runs'
meshes (undecomposed and decomposed), initial fields and curtain faces byte for byte, and
dictionaries whose values are identical (`runConfig` and the `start300` comments differ only
in layout). `postprocess_curtains.py` on the solved runs' planes and monitors reproduces
every file in `results/curtains/` byte for byte, `final_fields.png` included.

`sill` was solved later on its own, on 2 ranks, in 6,586 s of wall time, from a copy of the
case whose rebuilt `hanging` setup matched the solved one byte for byte. From a clean copy of
this repository, `./Allrun --setup-only sill 2` gives the solved run's mesh (undecomposed and
decomposed), initial fields, curtain faces and every dictionary byte for byte but `runConfig`,
whose values are the same. `postprocess_curtains.py` on all three runs reproduces the
`hanging` and `tucked` CSV files byte for byte and adds the `sill` rows; `summary.md` and
`final_fields.png` now have three runs. The planes can be `clip.vtp` or gzipped.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with
NumPy, PyVista and Matplotlib for the post-processing.

    cd cases/radiatorUnderWindow
    ./Allrun window              # [hour|start300] [nProcs], default hour on 6 ranks
    ./Allrun opposite
    python3 postprocess.py runs/hour results/hour
    python3 plot_histories.py

`Allrun` writes the run into `runs/<variant>/<window|opposite>/` with its
`config/caseSettings` beside it in `runs/<variant>/config/`, meshes it, sets the radiator
zone, checks the mesh, decomposes it, solves and reconstructs the last time.
`./Allrun --setup-only <run> [variant]` stops before the solve. For the re-solve:

    ./Allrun window start300; ./Allrun opposite start300
    python3 postprocess.py runs/start300 results/start300 --settled 0 0
    python3 compare_start300.py runs/hour runs/start300 > results/start300/vs_hour.txt

`python3 derive_output.py` recomputes the 60 W/m. `./Allclean` removes the runs.

The hour runs took 24,622 s (window) and 43,418 s (opposite) of wall time on 6 ranks
each, side by side. Each writes 480 sections of about 4.3 MB, so allow about 3 GB a run;
the start300 runs write as many sections, about 2 GB each. Fields are kept only for the last
few writes (`purgeWrite 4`).

The case was set up by an agent and checked by us over three solves; the third solve and
the 0-300 s re-solve were run on our own machine. The files in `results/` are what
`postprocess.py`, `compare_start300.py` and `derive_output.py` wrote from those runs.
Checked from a clean copy: `./Allrun --setup-only` produces, for both runs, a mesh
identical to the hour runs' and dictionaries whose expanded values are identical to theirs
and, apart from `pRefValue` above, to the re-solve's.
