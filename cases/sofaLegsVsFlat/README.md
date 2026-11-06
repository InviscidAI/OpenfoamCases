# A sofa on legs against the same sofa flat on the floor, in front of a radiator

A sofa often stands with its back to a radiator, and heating guides say that what matters is the
gap underneath: "Ensure the furniture has legs or a base that doesn't block the air intake at the
bottom of the radiator", because "If the cold air cannot get in, the warm air cannot get out"
(bathroommountain.co.uk, furniture placement guide, read 5 Nov 2026; it cites no source, and we found
no measurement). This case switches the same radiator on twice in the same cold living room, with a
sofa's back 15 cm in front of it, once with the sofa standing on legs and once with its base carried
down to the floor, and asks whether the air gets in, and what happens to the radiator's heat if it
cannot. It is about the heat that reaches the room in the first five minutes, not comfort on the sofa
or energy bills.

    ./Allrun legs    # the sofa on legs, 15 cm of open air under it, 0-300 s from switch-on
    ./Allrun flat    # the same sofa with its base flat on the floor
    ./Allrun bare    # the room with no sofa, 0-40 s: the convector's check against the catalogue

**The result.** Over the 300 s from switch-on the radiator behind the flat sofa gave the room
**173.9 kJ per metre, 88.7% of the 196.0 kJ/m it gave behind the sofa on legs**, 11.3% less. Nearly
all of the loss is convection: 108.8 against 129.2 kJ/m (84.2%), while the radiation is 65.1 against
66.8 kJ/m (97.5%). On legs, the room's cold floor air streams under the sofa to the radiator,
23-31 l/s per metre at the times read. Flat, nothing passes underneath; the radiator draws its air
down from above, between the sofa's back and the wall, and the slot behind the sofa runs warm. The
radiator still heats the room: closing the gap cost it about a ninth of its heat in this section, not
most of it. The flat run's share since switch-on stays between 87.3% and 89.8% from 30 s on. Read
[What it cannot](#what-it-cannot) before any number here: a 2-D section has no sofa ends, so it
stands for the middle of a long sofa and **overstates how shut the flat sofa's slot is**. The 88.7%
is this closed section's figure, not a real sofa's.

This room, its walls and the sofa are new, and the case is separate from
[`radiatorCover`](../radiatorCover), whose `sofa` run stood a different sofa in front of the radiator
under a window, in a room whose ceiling and inner wall were held at 20 C. Only the radiator is
`radiatorCover`'s, with its convector's resistance unchanged.

## The room

x runs from the radiator's wall into the room, y up from the floor; the section is 1 m deep in z, one
cell, with empty front and back. All figures are per metre of section.

| | value | from |
|---|---|---|
| room | a through-lounge 5.5 m from end to end, 2.4 m high, as a vertical section along its length | ours, a plain shape: the radiator then has no window over it, and the cold air arrives along the floor towards the sofa |
| radiator's wall | x = 0, the patch `innerWall` | |
| patio doors | x = 5.5 m: glass from the floor to y = 2.10 m (`glass`), wall above (`outerWall`) | ours |
| glass | no layer; h = 4.403 W/m²K to 0 °C outside (U = 2.8 W/m²K double glazing less the inside film, which is the solver's), emissivity 0.84 | `radiatorUnderWindow`'s glass |
| floor | 19 mm of wood, k = 0.106 W/m K, ρc = 1,237,411 J/m³K | ASHRAE values, as [`ceilingVsFloorVent`](../ceilingVsFloorVent) and [`ceilingVsUnderfloor`](../ceilingVsUnderfloor) |
| ceiling and both end walls | 12.7 mm of gypsum board, k = 0.1587 W/m K, ρc = 723,991 J/m³K | the same |
| start | the air at rest at 16 °C in hydrostatic balance (1e5 Pa at y = 1.174 m), every wall layer at 16 °C; 0 °C outside | ours, a house cooled overnight, as `ceilingVsUnderfloor`'s setback |

**The walls store heat.** Every surface but the radiator's panel is `radLayerWall`
(`src/radLayerWall`, `ceilingVsUnderfloor`'s compiled condition, the code unchanged): convection and the
radiation it absorbs on the room side, emissivity 0.9 (0.84 the glass), and behind it a 1-D layer of 24
slices with its heat capacity and an adiabatic back. Nothing leaves the room but through the glass.
This is the difference from `radiatorCover`'s sofa run, whose answer rested on a ceiling and inner wall
held at 20 C that took the bare panel's radiation out of the model.

## The radiator

`radiatorCover`'s radiator, a Stelrad Compact K1 600 x 1000, in the same place against its wall: its
steel front panel (x = 0.103-0.123 m, y = 0.15-0.75 m) left out of the mesh and held at 55 °C
(`radiatorPanel`, emissivity 0.9), and behind it the convector, a zone of the air (x = 0.040-0.103 m, same
y) held at 55 °C (`fixedTemperatureConstraint`) with an upward Darcy resistance d_y = 16,308,374.67 m⁻²
and sideways closed (`constant/fvOptions`, `config/caseSettings`). Both from t = 0. `radiatorCover`'s
README gives the sources and how d_y was fitted there, to Stelrad's 980 W at ΔT50 on its own finer mesh.

**The check on this mesh.** The `bare` run (no sofa, 0-40 s) gave **688.9 W/m over 25-40 s, against the
catalogue's 686.3 W/m** at the room's mean air temperature then (16.985 °C; 980 W x ((55 - T)/50)^1.3),
+0.38%. The plan was to refit d_y only if this fell more than 5% short, so d_y stands unchanged. The bare
run is used for nothing else, and its 40 s are not a third result.

## The sofa

**An IKEA EKHOLMA 3-seat sofa**, from IKEA's product page (ikea.com/be/en, EKHOLMA 3-seat sofa, Hakebo
beige, read 5 Nov 2026): depth 85 cm, "Free height under furniture 15 cm", "Height backrest 70 cm",
"Height including back cushions 94 cm", seat height 49 cm, seat depth 55 cm, width 207 cm, "visible
wooden legs". In the section it is a solid side profile in three blocks:

- the seat and base, x = 0.273-1.123 m, up to the 49 cm seat;
- the backrest frame, 12 cm thick (x = 0.273-0.393 m), up to 70 cm;
- the back cushion in front of it, 18 cm thick (x = 0.393-0.573 m), from the seat to 94 cm.

The 12 and 18 cm split of the 30 cm behind the seat is ours.

**The two runs differ only in the base.** `legs`: the base's underside is at y = 0.15 m, and the section
is cut between the legs, so the 15 cm is open from back to front. `flat`: the same outline carried down to
the floor, as a skirted or plinth-based sofa is; its cells under the sofa are left out of the same grid,
and it has no floor faces under the sofa. We found no matching flat-based sofa with published figures, and
a second model would change other things, so this is one outline with one change.

**The gap.** The sofa's back is 15 cm from the radiator's front (x = 0.273 m), the gap people say they
leave: a Mumsnet poster's "about 15-17cm" and a MoneySavingExpert reply's "5" pr 6"", against the 30 cm
the advice asks (Verbraucherzentrale, EngineerFix), as `radiatorCover` gives them.

**Its surface** is the patch `sofa`, `radLayerWall` with a 50 mm layer of upholstery foam under fabric,
k = 0.04 W/m K, ρc = 49,000 J/m³K (35 kg/m³ at 1400 J/kg K, handbook values, ours), emissivity 0.9, an
adiabatic back. So the sofa warms as fabric over foam does, and nothing passes through it.

## The model

`buoyantPimpleFoam` (OpenFOAM v2512), compressible air as a perfect gas (Cp 1005 J/kg K, μ 1.82e-5 Pa s,
Pr 0.71), k-ω SST with `buoyancyTurbSource`, Euler in time at Courant 1 (maxDeltaT 0.25 s), two outer and
two pressure correctors, the final p_rgh solve to 1e-8 or 100 iterations. Radiation is fvDOM, transparent
air, 32 directions in the plane (nPhi 8, nTheta 0), solved every 10 steps, starting from the black-body
intensity at 16 °C rather than a solved field. The numerics are `radiatorCover`'s
(`config/caseSettings`).

**The mesh** is written directly by `scripts/make_case.py`, `radiatorCover`'s writer with this room's
grid: 288 x 241 cells graded with lines on every edge of the radiator and the sofa and on both flow cuts,
7 mm to 0.3 m from the radiator's wall widening to 25 mm from 1.3 m to 5.2 m and 12 mm at the doors, 8 mm
up to 1.1 m, 15 mm to 2.25 m and 6 mm under the ceiling; the smallest cells 6.67 x 6.00 mm, neighbours
within 7% in x and 11% in y. **64,835 cells** in `legs`, **63,543** in `flat`, 69,183 in `bare`; 19 cells
under the sofa and 21 across the slot behind it; orthogonal, `checkMesh` OK. One mesh, no mesh study.

**The monitors** (`config/caseSettings`, coded function objects compiled at the solve's start):
`heatAccounting` every step, radiatorCover's with the sofa added as a wall, for the radiator's output, each
wall's convection and absorbed radiation, the air's mass and its internal energy (cv/R) ∫p dV;
`diagnostics59` every simulated second, for the gross flows under the sofa (x = 0.70 m, y = 0-0.15 m) and
across the slot's top (y = 0.70 m, x = 0.123-0.273 m), the room's mass-weighted air temperature without
the convector's cells, the sofa's back, and the heat stored in every layer; `surfaceStability59`
every step, the sofa's surface temperature (`scripts/surfaceStability59.txt`); six temperature probes;
and the section's plane every 0.625 s, 481 a run.

## Results

`results/summary.txt`, `results/minutes.csv` and `results/<run>/history.csv` (every 2.5 s), from
`scripts/extract_results.py`. The radiator's heat is the panel's convection and radiation plus the
energy balance of the convector's air, as in `radiatorCover`.

| 0-300 s from switch-on, kJ/m | legs | flat | flat / legs |
|---|---|---|---|
| the radiator's heat | 196.05 | 173.94 | **88.7%** |
| of it convection | 129.24 | 108.82 | 84.2% |
| of it radiation | 66.81 | 65.13 | 97.5% |

| t (s) | 10 | 30 | 60 | 120 | 180 | 240 | 300 |
|---|---|---|---|---|---|---|---|
| flat / legs since switch-on | 96.2% | 88.0% | 89.4% | 88.5% | 88.5% | 89.3% | 88.7% |
| radiator now, legs (W/m) | 690 | 669 | 669 | 654 | 645 | 618 | 594 |
| radiator now, flat (W/m) | 623 | 531 | 600 | 628 | 551 | 551 | 538 |
| under the legged sofa, towards the radiator (l/s) | 31.3 | 24.0 | 25.1 | 26.8 | 27.3 | 24.3 | 23.2 |
| up the slot's top, legs / flat (l/s) | 17.1 / 9.8 | 11.6 / 8.4 | 12.6 / 7.7 | 13.5 / 4.4 | 14.0 / 6.8 | 12.0 / 8.0 | 11.8 / 5.7 |
| down the slot's top, legs / flat (l/s) | 0.0 / 16.5 | 1.4 / 15.2 | 1.3 / 17.7 | 0.6 / 18.4 | 0.6 / 20.2 | 0.8 / 17.8 | 0.7 / 18.1 |
| the room's air, legs / flat (°C) | 16.40 / 16.36 | 16.96 / 16.71 | 17.67 / 17.29 | 18.97 / 18.21 | 20.19 / 19.06 | 21.20 / 19.85 | 22.00 / 20.36 |

Flows are gross, each direction on its own, per metre. The slot's top is the line from the panel's front
to the sofa's back at the frame's top; the convector's own passage behind the panel is not on it, so its
up and down need not balance. The room's air is mass-weighted without the convector's cells.

**What the air does.** On legs the radiator's plume leaves over the sofa's back, and the floor's cold air,
from the patio doors, runs in under the sofa to the radiator; the slot carries air up and almost none down.
Flat, the slot is closed at the floor, so the radiator draws its air down the slot from above, 15-20 l/s
down against 4-10 up, and the air it heats partly comes round again. The radiator then works in warmer air
and gives less. Read from the planes (the clip's pipeline, not `extract_results.py`; the planes are not
committed), the open part of the slot (x = 0.123-0.273 m, y = 0-0.70 m) is 20.0 °C on legs and 24.5 °C
flat at 300 s, and over 60-300 s it is 1.2 K below the room's mean on legs and 5.0 K above it flat. The air
near the floor away from the sofa (x > 1.2 m, y < 0.5 m) is 18.7 °C on legs and 16.2 °C flat at 300 s. The
monitor's `slotT_K` averages a box that takes in the convector at 55 °C and reads far too warm for the
slot's air, so it is not quoted.

**The flat slot fills and empties.** It reaches 27.2 °C at 30 s and falls back, and the flat radiator's
output swings between about 470 and 640 W/m (2.5 s means after the first 10 s; legs 595-705 W/m), so minute
by minute the flat run's share moves between 86% and 92% (`results/minutes.csv`), where the share since
switch-on stays within 87.3-89.8% from 30 s on.
Whether that swing survives in 3-D or on another mesh is not tested.

**A hand estimate before the solve was wrong in size.** It put the settled slot about 6 K above the room on
legs and 16-23 K flat, on an exchange coefficient bracketed between 0.1 and 0.3. The flat slot exchanges far
more with the room than that, by the air coming down from above, and on legs the floor's cold air runs
through it.

**Checks.** The whole section's heat budget over 10-300 s, the radiator's heat against the rise of the air's
internal energy, the heat stored in the layers and the heat out through the glass, closes to -0.03% (legs)
and -0.10% (flat) of the radiator's heat. Each layer's stored heat matches minus its integrated wall heat
flux to 0.03% or better. The air's mass holds to 9.0e-7 of the hydrostatic start. The sofa's surface stays
within 15.3-38.1 °C with no oscillation at the radiation updates (largest jump of its mean at an update
0.005 K after the first second, in the 0-30 s pilots). 124 (legs) and 111 (flat) of the 33,621 and 30,024
final pressure solves stopped at the 100-iteration cap, at residuals of 1.0e-8 to 1.12e-8; the tolerance was left at
1e-8. We set a range before the solve: if the flat run's heat fell outside about 10-60% below the
legged run's, the reason would be looked for before any number went on screen. 11.3% is inside it, near
its lower end; the range came from CIBSE Guide B's 10% for a shelf and 20% or more for an enclosure and
`radiatorCover`'s 30% for a cover, not from a measurement of a sofa.

## What the clip shows, and what it does not

The clip shows the two rooms whole, from the radiator's wall to the patio doors and from floor to ceiling,
one above the other, legs above and flat below, from switch-on, 300 s at 15 times real time, the air's
temperature on a scale of 15-30 °C with moving air parcels, the question "Sofa by a radiator: do its legs
matter?", a clock, and in each room one rounded number, the heat into the room so far as a share of the
legged run's 300 s total, ending at 100% and 89%. The last frame is held for 0.5 s.

- **The legs are drawn, not solved.** The section is cut between the legs, so the solved sofa has none and
  its 15 cm is open from back to front. The clip draws solid legs, 80 mm wide at the top and 50 mm at the
  floor, wider than the real ones so that they read on a phone, so that the sofa does not hang in the air.
- The sofa and the radiator's panel are drawn as plain solids over the holes they leave in the plane; their
  outlines match the mesh's solid cells. The parcels are moved through the planes' velocity after the solve;
  they are not solved particles.
- The 89% is the 88.7% above, this closed section's figure.

## What it cannot

- **A 2-D section, with no sofa ends.** This is the biggest limit. A real 2.07 m sofa behind a 1 m
  radiator lets air in round its ends, and down the gaps between a skirted base and the floor; a real
  sofa's back is not a sealed surface either. The section stands for the middle of an endless sofa in
  front of an endless radiator and **overstates how shut the flat sofa's slot is**, so the 11.3% is no
  estimate of what a real flat-based sofa costs a real radiator. What it shows is what the air does when
  the bottom is shut.
- **A radiator as deep as the section.** The radiator runs the section's whole depth, so per metre of
  room the heat is a whole metre of radiator's, and the room warms faster than a real one with a 1 m
  radiator in a wider room.
- **A radiator held at 55 °C**, its panel and its convector's air, from t = 0: switched on instantly, the
  same at top and bottom, its water never cooling. A real radiator on a slowed flow would lose less than
  this one by running cooler.
- **One gap and one height.** 15 cm behind the sofa and 15 cm under it. Nothing here says how the result
  moves with either.
- **Five minutes from a cold start.** The shares are of the heat since switch-on, not a settled output.
- **One mesh, k-ω SST, radiation from a black-body start.** No mesh study was run. The flat run's swing
  between about 470 and 640 W/m is not tested on another mesh or in 3-D.
- **The sofa's surface** is our layer of foam under fabric with an adiabatic back; the room is ours, not a
  surveyed one, with no furniture but the sofa, no people and no air leaks.

## Sources

- The claim tested: bathroommountain.co.uk, furniture placement guide, read 5 Nov 2026.
- The sofa: IKEA EKHOLMA 3-seat sofa, product page (ikea.com/be/en), read 5 Nov 2026.
- The gap: Mumsnet (26 Jul 2026), MoneySavingExpert (read 31 Oct 2026), Verbraucherzentrale and
  EngineerFix on 30 cm, as quoted in [`radiatorCover`](../radiatorCover).
- The radiator and its convector's resistance: [`radiatorCover`](../radiatorCover) (Stelrad Compact K1
  600 x 1000, 980 W at ΔT50, EN 442's exponent 1.3).
- The glass: [`radiatorUnderWindow`](../radiatorUnderWindow); the wood and gypsum layers and the wall
  condition: [`ceilingVsFloorVent`](../ceilingVsFloorVent), [`ceilingVsUnderfloor`](../ceilingVsUnderfloor).
- The range set before the solve: CIBSE Guide B (a shelf over a radiator about 10%, an enclosure 20% or
  more), through a search summary.
- The question came from viewers of the `radiatorCover` sofa clip, who asked whether the gap under a
  sofa makes a difference.

## How the case got here

The set-up was built first on a cloud workspace of four cores, whose bare pilot projected 18.5 h a run,
past the 10 h a run allowed, and was stopped there at 1.04 s; it was solved on our own machine from that
set-up, the mesh and dictionaries unchanged. There the bare check ran 0-40 s on 8 ranks; then legs and flat
ran side by side 0-30 s as pilots (projecting 1.9 and 1.4 h), checked for the air's mass, every layer's
stored heat, the budget and the sofa's surface at radiation updates, and were discarded; then both ran from
rest to 300 s, 8 ranks each, one physical core a rank: legs 33,621 steps in 6,905 s (1.9 h), flat 30,024
steps in 5,276 s (1.5 h). No setting was changed between the pilots and production, and no time step,
tolerance or mesh was relaxed.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with `wmake` and MPI, and Python 3 with
NumPy.

    cd cases/sofaLegsVsFlat
    ./Allrun legs                # [nProcs], default 8
    ./Allrun flat
    ./Allrun bare                # optional: the convector's check, 0-40 s
    python3 scripts/extract_results.py runs results

`Allrun` compiles `src/radLayerWall` into `$FOAM_USER_LIBBIN` as `libradLayerWall.so` (the same code
and library name as `ceilingVsUnderfloor`'s and `fanHeaterVsOilRadiator`'s), writes the run into
`runs/<run>/` with `scripts/make_case.py` (the mesh, 0/T, 0/IDefault, the hydrostatic 0/p and 0/p_rgh;
`template/common/` and `template/sofa/` or `template/bare/` for the rest), checks the mesh, writes the
t = 0 plane (legs and flat), decomposes it by scotch, solves, and once legs and flat have solved writes
`results/`; `extract_results.py` adds the bare check to `summary.txt` if `runs/bare` has run.
`./Allrun --setup-only <run> [nProcs]` stops before the solve; `./Allclean` removes the runs.

The dictionaries are the solved runs' byte for byte, comments included, and some comments are stale from
`radiatorCover`: `config/caseSettings` calls `Tamb` "20 C" and its runs "bare and cover", and
`thermophysicalProperties` says the enthalpy is referenced at 20 C; `Tamb` is 289.15 K, 16 °C, and every
run here reads it. `system/controlDict` has two `functions` blocks, the probes and `surfaceStability59`,
which OpenFOAM merges with those in `config/caseSettings`. `bare`'s `controlDict` turns the plane off.

Each of legs and flat writes 481 planes of about 4.9 MB (about 1.7 MB gzipped), the fields every 30 s
keeping the last two, and a `heat.csv` of about 19 MB. `results/` holds the summary, the minutes and each
run's history every 2.5 s; no fields, meshes, planes or logs.

The case was set up and solved by an agent on our own machine and checked by us. The files in `results/`
are what `scripts/extract_results.py` wrote from the solved runs' monitors.

Checked from a clean copy of the case: `./Allrun --setup-only legs`, `flat` and `bare` compile the wall
condition and write the solved runs' meshes (points, faces, owner, neighbour, boundary and the cell, face
and point zones) byte for byte, `checkMesh` OK at 64,835, 63,543 and 69,183 cells, and their `constant/`
and `system/` byte for byte (the study kept its pilot and production controlDicts beside the one it ran,
which is the production one). Every 0/ field is the solved runs' byte for byte but p and p_rgh, which
differ in the last bit in 2,304 cells, eight rows of the grid: the set-up's NumPy on another machine
rounded `exp` the other way there, a relative 1.5e-16. The t = 0 planes of legs and flat are the solved
runs' byte for byte. Nine serial steps of each from there gave the first step's initial residuals for Ux
and Uy (1), h (to 2e-9 legs, 1e-5 flat) and the first p_rgh solve (to 1e-9) of the 8-rank logs, and the
second step's time step to 1e-5 (legs) and 2e-4 (flat); later residuals differ by up to a few per cent,
as serial and parallel solves do, and scotch's decomposition is not the same from one run to the next, so
a new solve will not repeat the solved runs bit for bit. No full solve was run from the clean copy.
`scripts/extract_results.py` on the solved runs' monitors gives the study's own figures: 196.05 and
173.94 kJ/m, the budgets, the layer balances, the flows and the bare check.
