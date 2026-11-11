# A tall room heated with a floor fan aimed at the ceiling, against without

Old flats in Berlin and elsewhere have ceilings well over 3 m, and the warm air from the radiator
goes up there first. A common piece of advice is to run a small fan with the heating to bring that
warmth down, and fan makers suggest two places for it in winter: in "a place with unobstructed upward
air movement", run "as fast as necessary to lower the heated air from the ceiling", or with the heat
source, "to circulate their warmth" (Vornado owner's guide, p. 9). This case switches the same
radiator on in the same cold Altbau room, 3.3 m high, once on its own and once with a small floor
fan blowing straight up at the ceiling, and asks where in the room the warmth ends up in the first
five minutes. A third run aims the fan at the radiator instead; it is kept, but it is not in the
clip, for the reason given under [The fan aimed at the radiator](#the-fan-aimed-at-the-radiator). It
is about where the warmth goes, not comfort or energy bills.

    ./Allrun nofan          # the radiator alone, 0-300 s from switch-on
    ./Allrun fan_ceiling    # the same with the fan on the floor blowing straight up
    ./Allrun fan_radiator   # the same with the fan on the floor blowing at the radiator (not in the clip)
    ./Allrun bare           # nofan to 40 s: the convector's check against the catalogue

**The result.** The fan aimed at the ceiling does not warm the room at standing height; it moves the
warmth to the floor. At 300 s from switch-on, against the room with no fan, its air is **3.3 K warmer at
the ankles** (the mean along a line across the room 0.1 m above the floor, 20.84 against 17.53 °C),
**0.7 K cooler at 1.5 m** (20.41 against 21.11 °C) and 1.7 K cooler just under the ceiling at 3.2 m
(21.39 against 23.09 °C); the room's air as a whole is 0.2 K cooler (20.87 against 21.07 °C). With no
fan the warmth stacks up in a layer under the ceiling above a cold floor; with the fan the room turns
over in one big loop and is within about a kelvin from floor to ceiling. The fan also draws more heat
from the radiator, **12.0% more over the last minute** (729.4 against 651.5 W/m), inside the 6.5-20%
that a real radiator gains with a fan (below). Read [What it cannot](#what-it-cannot) before any number
here: **the fan is a 2-D slot, not a round fan**, so it mixes the room more evenly than a real one, and
**the section warms about four times as fast as the room it stands for**, so no time here is a real time.

This room, its window and the fan are new. The radiator is [`radiatorCover`](../radiatorCover)'s Stelrad
Compact K1 with the fin-gap convector of its `finsBare` and `finsFans` runs (fans under the radiator),
its conductance unchanged, and the walls are [`sofaLegsVsFlat`](../sofaLegsVsFlat)'s layers that store
heat.

## The room

x runs from the window wall into the room, y up from the floor; the section is 1 m deep in z, one cell,
with empty front and back. All figures are per metre of section.

| | value | from |
|---|---|---|
| room | an Altbau room 5.0 m from the window wall to the inner wall, 3.30 m high, as a vertical section across it | ours, from a viewer's 3.3 m; Altbau rooms 4.5-6 m deep are usual |
| window | at x = 0: glass from y = 0.90 to 2.90 m (`glass`), wall below and above (`outerWall`) | ours, a tall window as such rooms have |
| glass | an old box window (Kastenfenster), "einen U-Wert zwischen 2,5 und 3,0 W/(m²K)"; carried as U = 2.8 W/m²K: no layer, h = 4.403 W/m²K to 0 °C outside, the inside film the solver's, emissivity 0.84 | aroundhome.de on Kastenfenster; the series' glass, [`radiatorUnderWindow`](../radiatorUnderWindow)'s |
| inner wall | x = 5.0 m (`innerWall`) | |
| floor | 19 mm of wood, k = 0.106 W/m K, ρc = 1,237,411 J/m³K | as [`sofaLegsVsFlat`](../sofaLegsVsFlat) |
| ceiling, inner wall and the window wall's opaque parts | 12.7 mm of gypsum board, k = 0.1587 W/m K, ρc = 723,991 J/m³K | the same |
| start | the air at rest at 16 °C in hydrostatic balance (1e5 Pa at y = 1.65 m), every wall layer at 16 °C; 0 °C outside | a house cooled overnight, as [`ceilingVsUnderfloor`](../ceilingVsUnderfloor)'s setback |

**The walls store heat.** Every surface but the radiator's panel is `radLayerWall` (`src/radLayerWall`,
`ceilingVsUnderfloor`'s compiled condition, the code unchanged): convection and the radiation it absorbs
on the room side, emissivity 0.9 (0.84 the glass), and behind it a 1-D layer of 24 slices with its heat
capacity and an adiabatic back. Nothing leaves the room but through the glass. There is no sill, no
furniture, no door and no air leak: in 2-D a sill would span the whole room and turn the plume off the
glass, which no real 1.2 m sill does.

## The radiator

`radiatorCover`'s Stelrad Compact K1 600 x 1000, rated 980 W at ΔT50, under the window: its steel front
panel (x = 0.103-0.123 m, y = 0.15-0.75 m) left out of the mesh and held at 55 °C (`radiatorPanel`,
emissivity 0.9), and behind it the convector, a zone of the air (x = 0.040-0.103 m, same y, 378 cells,
0.0378 m³ per metre). Both from t = 0.

**The convector is `radiatorCover`'s fin-gap one** (its README, "Fans under the radiator"), because the
convector of the earlier runs in the series, a zone held at 55 °C with a fitted resistance, passes almost
no air and gave far too much heat once a fan blew past it (see [How the case got here](#how-the-case-got-here)):

- an upward resistance of laminar flow between fins 6.31 mm apart, Calisir et al.'s optimum gap, d_y =
  325,267 m⁻² and f_y = 1.308 m⁻¹, sideways closed (1e8);
- the fins heat the zone's air through a conductance, S = hv (55 °C - T) per unit volume, with
  **hv = 448.855 W/m³K**, the value `radiatorCover` fitted to the catalogue rating on its own mesh. This
  case's enthalpy is referenced at 16 °C, not 20 °C, so the source is written Su = hv (328.15 - 289.15),
  Sp = -hv/1005 (`template/*/constant/fvOptions`).

**The check on this mesh.** The `bare` run (nofan to 40 s) gave **701.4 W/m over 25-40 s, against the
catalogue's 691.3 W/m** at the room's mean air temperature then (16.771 °C; 980 W x ((55 - T)/50)^1.3),
1.015. The plan was to refit hv only if this was more than 5% out, so hv stands unchanged. The bare run is
used for nothing else.

## The fan

**A Honeywell TurboForce HT900E**, an 11-inch table air circulator, the fan the question was asked about.
Its retail listings give 185 CFM (0.0873 m³/s), three blades of about 193 mm and a housing about 0.28 m
tall; Honeywell's own sheet was not found. Through a 0.19 m outlet that is 3.1 m/s and a momentum flux
ρQU of 0.32 N.

**In 2-D the fan is a slot, not a round jet.** A section cannot hold a round jet. It is one metre deep and
holds the 1 m radiator, so the fan is given its full momentum, 0.32 N per metre, which keeps the real ratio
of one fan's push to one 1 m radiator's heat. Across a 0.19 m slot that is **1.19 m/s and 0.226 m³/s per
metre**. A plane jet of the same momentum moves about two and a half times the air of the round one at
under half its speed, spans the whole section and decays more slowly, so the section's fan reaches
further and stirs the room more evenly than a real one.

- **Where.** `fan_ceiling`: on the floor 1.0 m from the inner wall, tilted straight up (the HT900E's head
  tilts 90°), the cell zone `fan_ceiling` (centres x = 3.905-4.095 m, y = 0.22-0.28 m, 91 cells), its
  outlet at y = 0.28 m. `fan_radiator`: on the floor 0.83 m in front of the radiator's face, blowing at
  it, the cell zone `fan_radiator` (centres x = 0.95-1.01 m, y = 0.055-0.245 m, 72 cells), its outlet at
  x = 0.95 m. Both zones are in every run's mesh, as plain air unless that run's `constant/fvOptions`
  drives one. The housing is not modelled: in 2-D a solid housing would be a wall across the room.
- **How.** OpenFOAM's `meanVelocityForce` holds the zone's mean velocity along its direction, at
  **Ubar = 1.0345 m/s** (`fan_ceiling`, +y) and **1.0955 m/s** (`fan_radiator`, -x). That is not the air
  the fan moves, so the air out through the outlet face was measured from the face flux (the face zones
  `fan_ceilingOut`, `fan_ceilingIn`, `fan_radiatorOut`, `fan_radiatorIn`) and Ubar set from it: pilots
  from rest to 10 s at 1.19 m/s gave 1.150 and 1.086 of the target over 4-10 s, and the scaled values
  above gave 1.000 and 0.997. In the solved runs the outlet carried 226.1 and 223.7 l/s per metre over
  4-10 s.
- **The fan's air was not held at the target.** Over 240-300 s the outlet carried 195.0 l/s per metre
  (`fan_ceiling`) and 216.7 (`fan_radiator`): the force holds the zone's mean velocity, not the air
  through its face, and the room's own circulation changes the outlet's profile.
- **When.** From t = 0, with the radiator.

## The model

`buoyantPimpleFoam` (OpenFOAM v2512), compressible air as a perfect gas (Cp 1005 J/kg K, μ 1.82e-5 Pa s,
Pr 0.71), k-ω SST with `buoyancyTurbSource` and wall functions, Euler in time at Courant 1 (maxDeltaT
0.25 s), two outer and two pressure correctors, the final p_rgh solve to 1e-8 or 100 iterations, the
pressure reference in the middle of the room. Radiation is fvDOM, transparent air, 32 directions in the
plane (nPhi 8, nTheta 0), solved every 10 steps, starting from the black-body intensity at 16 °C. The
numerics are `sofaLegsVsFlat`'s (`config/caseSettings`).

**The mesh** is written directly by `scripts/make_case.py`, `radiatorCover`'s writer with this room's
grid: **240 x 183 cells, 43,812** without the panel's, graded with lines on every edge of the radiator,
the window and both fans and on the monitored heights, 10 mm near the radiator, 15 mm around each fan,
up to 29 mm between, 12 mm near the floor and under the ceiling; the smallest cells 9.0 x 8.25 mm, the
largest 28.8 x 28.9 mm, neighbours within 1.11 in x and 1.15 in y; orthogonal, `checkMesh` OK. It is
coarser than `sofaLegsVsFlat`'s, because the room is 40% larger and the three runs had 10 h between
them. One mesh, no mesh study.

**The monitors** (`config/caseSettings` and `system/controlDict`, coded function objects compiled at the
solve's start): `heatAccounting` every step, `sofaLegsVsFlat`'s, for the radiator panel's convection and
radiation, the convector zone's energy balance, each wall's convection and absorbed radiation, the air's
mass and its internal energy (cv/R) ∫p dV; `diagnostics66` every step, for the mean temperature along
lines across the room (x = 0.5-4.5 m) at 0.1, 1.1, 1.5 and 3.2 m, the room's mass-weighted air without
the convector's cells, both fans' gross flows in and out, the gross flows up and down across 1.5 m, and
the heat stored in every layer; `convectorT`, the integral of T over the convector zone, for the fins'
heat; `convectorAir`, the zone's air and its gross flows in at the bottom and out at the top; and the
section's plane every 0.625 s, 481 a run.

## Results

`results/summary.txt`, `results/minutes.csv` and `results/<run>/history.csv` (2.5 s windows), from
`scripts/extract_results.py`. The radiator's heat is the panel's convection and radiation plus the fins'
heat to the convector's air, hv (55 °C x V - ∫T dV); the convector air's own energy balance agrees with
the fins' heat to 0.032% or better in every minute after the first 10 s.

| at 300 s, °C | no fan | fan aimed at the ceiling | difference |
|---|---|---|---|
| 0.1 m, the ankles | 17.53 | 20.84 | **+3.31** |
| 1.1 m | 20.77 | 20.44 | -0.33 |
| 1.5 m, standing height | 21.11 | 20.41 | **-0.69** |
| 3.2 m, under the ceiling | 23.09 | 21.39 | -1.70 |
| the room's air | 21.07 | 20.87 | -0.20 |

| t (s) | 10 | 30 | 60 | 120 | 180 | 240 | 300 |
|---|---|---|---|---|---|---|---|
| 0.1 m, no fan / fan (°C) | 16.07 / 16.09 | 16.21 / 16.94 | 16.37 / 17.75 | 16.66 / 18.98 | 16.93 / 19.80 | 17.22 / 20.38 | 17.53 / 20.84 |
| 1.5 m, no fan / fan (°C) | 16.09 / 16.30 | 16.21 / 16.49 | 16.81 / 17.09 | 17.73 / 18.18 | 19.29 / 19.12 | 20.37 / 19.84 | 21.11 / 20.41 |
| 3.2 m, no fan / fan (°C) | 16.07 / 16.07 | 18.32 / 17.02 | 18.97 / 18.27 | 20.29 / 19.60 | 21.64 / 20.40 | 22.50 / 20.95 | 23.09 / 21.39 |

Lines are means along x = 0.5-4.5 m, instantaneous. **At the ankles the fan room is never colder** than the
no-fan room: over every step the difference is at least -0.002 K, at t = 0. At 1.5 m the fan room is ahead,
by up to 0.9 K, for a little over two minutes, while the no-fan room's warm layer is still above that height,
and behind from about 132 s, as the layer comes down (`results/<run>/history.csv`); over 240-300 s the 1.5 m
line averages 20.14 °C with the fan and 20.76 °C without.

| the radiator's heat, W/m | 0-60 s | 60-120 | 120-180 | 180-240 | 240-300 |
|---|---:|---:|---:|---:|---:|
| no fan | 692.9 | 692.0 | 685.0 | 672.5 | 651.5 |
| fan aimed at the ceiling | 770.4 | 822.8 | 760.2 | 740.8 | 729.4 |
| **fan / no fan** | **111.2%** | **118.9%** | **111.0%** | **110.2%** | **112.0%** |

Over 240-300 s the fan adds 42 W/m to the panel's convection (159.8 against 117.8), 38 W/m to the
convector (314.5 against 276.6) and takes 2 W/m from its radiation (255.1 against 257.2). The fins pass
more air with the fan running (12.0 against 9.3 g/s per metre in at the bottom), and their air is cooler,
36.3 against 38.5 °C. From switch-on to 300 s the radiator gave 229.4 kJ/m with the fan and 203.6 without.

**The gain is inside the range a real radiator gets.** `radiatorCover`'s fans under the same radiator gave
6.5% with the same convector (and 12.6% with the earlier one held at 55 °C), and Milieu Centraal is quoted,
second-hand, at about 20% for radiator fans. The 12.0% here is inside 6.5-20%. It is not tuned to that
range: hv was fitted in still air and the fan's Ubar to its own flow.

**Where the extra heat goes.** The fan room's air ends 0.2 K cooler than the no-fan room's although its
radiator gave 26 kJ/m more: its walls took more. Over 10-300 s the wall layers stored 124.2 kJ/m with the
fan and 91.2 without, the air gained 65.7 and 69.2, and the glass lost 32.1 and 36.6. The fan drives the
room's air along every wall and the floor, where without it the warm air sits still under the ceiling.

**Checks.** The whole section's heat budget over 10-300 s, the radiator's heat against the rise of the air's
internal energy, the heat stored in the layers and the heat out through the glass, closes to 0.002% (no
fan) and 0.048% (fan) of the radiator's heat; each layer's stored heat matches its integrated wall heat flux
to 0.006% or better; the air's mass holds to 9.0e-7 of the hydrostatic start. 58 (no fan) and 89 (fan) final
pressure solves stopped at the 100-iteration cap, at residuals of 1.0e-8 to 2.5e-7; the tolerance was left
at 1e-8. The coldest cell of air in each run falls a little below the 12 °C set as a screen before the solve,
11.5 °C at 13.5 s with no fan and 11.8 °C at 79 s with the fan, and comes back above it.

### The fan aimed at the radiator

`fan_radiator` is kept as solved, with its results (`results/fan_radiator/`, `summary.txt`), and is **not
used** for the clip or for any claim. Its model radiator gave **33.2% more heat** with the fan than without
over 240-300 s (867.9 against 651.5 W/m), **against about 20% for a real radiator** with a fan. Of the extra
216 W/m, 122 W/m is the panel's front face, held at 55 °C however much heat the jet draws from it, 97 W/m
the convector, and the radiation falls by 3 W/m. A real panel cools where a jet scrubs it, and a real round
fan 0.83 m away reaches only part of a 1 m radiator, where the 2-D slot jet covers all of it. Its room is
warmer everywhere, 0.78 K at 1.5 m and 1.43 K over the whole room at 300 s, and that lead rests on the part
of the gain above what a real radiator gets, so this case does not say whether aiming the fan at the radiator
beats aiming it at the ceiling. A panel that cools under the jet needs a water-side model that has not been
built.

## What the clip shows, and what it does not

The clip shows the two rooms whole, from the window wall to the inner wall and from floor to ceiling, no fan
above and the fan aimed at the ceiling below, from switch-on, 300 s in 20 s, the air's temperature on a
scale of 15-30 °C with moving air parcels, the question "High ceiling: does a fan help the heating?", a clock,
and in each room one rounded number, the air at the ankles: the 0.1 m line above, rounded to the whole degree,
counting up from 16 °C to 18 °C with no fan (17.53) and to 21 °C with the fan (20.84). The number is the ankles'
and not 1.5 m's because the fan does not warm the room at standing height.

- **The fan is drawn, not solved.** It is drawn at 1.5 times the HT900E's head, 0.44 m, so that it reads on a
  phone, seen a little from above with three turning blades. The solved fan is the slot of cells above, with no
  housing.
- Half a metre of drawn wall either side of the section carries the names of the box window and the
  radiator; short white ticks on both walls mark 0.1 m. The parcels are moved through the planes' velocity after the
  solve; they are not solved particles.
- The fan aimed at the radiator is not in it.

## What it cannot

- **The fan is a 2-D slot, not a round jet.** This is the biggest limit. It carries the real fan's push per
  metre of radiator, but moves about two and a half times the air at under half the speed, spans the
  section's whole depth and reaches further. A real fan mixes a room less evenly than this one, most of all far
  from its jet. The direction of the result, a warmer floor and a slightly cooler head, holds better than any
  temperature the fan room reaches.
- **The radiator spans the section.** A 1 m radiator gives its whole rating to one metre of room, about four
  times what a real 4 m wide room with one such radiator gets per metre. The section warms about four times as
  fast as the room it stands for, so the 300 s here are not five real minutes, and the times at which the 1.5 m
  line crosses over are not real times.
- **The walls are thin layers** of gypsum and wood with adiabatic backs. A real Altbau's plastered brick and
  beamed ceiling store more heat, most of all the ceiling under a warm layer, which would favour the fan a
  little more than here.
- **The panel is held at 55 °C**, switched on instantly, its water never cooling. That is why the fan aimed at
  the radiator draws too much from it. The fan aimed at the ceiling scrubs the panel far less, and its gain is
  inside a real radiator's range, but the same panel is in its result too.
- **The HT900E's figures are retailers'**, 185 CFM at its top speed; Honeywell's own sheet was not found. It runs
  at that speed throughout, faster than "only as fast as necessary".
- **Five minutes from a cold start.** Nothing here is a settled room.
- **One mesh, k-ω SST with wall functions, grey diffuse radiation from a black-body start.** No mesh study was run.
  The room is ours, with no sill, furniture, door gap, ventilation or people. Floor heating is not modelled; an
  underfloor-heated room warms nearly evenly on its own ([`ceilingVsUnderfloor`](../ceilingVsUnderfloor)), so a
  fan there would have little to stir.

## Sources

- The fan's two winter places: Vornado owner's guide, p. 9 (sharperimage.com/cdn/shop/files/202562.pdf).
- The fan: Honeywell TurboForce HT900E, retail listings (185 CFM, 11-inch, three blades of about 193 mm, a
  housing about 0.28 m tall), read 9 Nov 2026.
- The window: aroundhome.de, "Kastenfenster" (U 2.5-3.0 W/m²K), read 9 Nov 2026; the glass as
  [`radiatorUnderWindow`](../radiatorUnderWindow).
- The radiator and its fin-gap convector: [`radiatorCover`](../radiatorCover) (Stelrad Compact K1 600 x 1000,
  980 W at ΔT50, EN 442's exponent 1.3; the 6.31 mm gap from Calisir, Baskaya, Yazar and Yucedag (2015) as
  summarised by Dalkilic et al. (2019); hv and the 6.5% gain with fans under the radiator).
- The 20% for radiator fans: Milieu Centraal, through a secondary quote, not checked here.
- The wood and gypsum layers and the wall condition: [`sofaLegsVsFlat`](../sofaLegsVsFlat),
  [`ceilingVsFloorVent`](../ceilingVsFloorVent), [`ceilingVsUnderfloor`](../ceilingVsUnderfloor).
- The question came from viewers, who asked whether a fan running with the heating gets the warmth down to body
  height in a 3.3 m Berlin room, and where the fan should stand.

## How the case got here

**A first solve, not in this case.** The three runs were first solved on 9 Nov 2026 on the same mesh with the
series' earlier convector, a zone held at 55 °C with an upward resistance fitted in still air (d_y = 1.63e7 m⁻²).
Its radiator gave 70% more heat with the fan aimed at it and 42% more with the fan aimed at the ceiling, nearly all
of it diffusing out of a zone held at 55 °C in every cell; that is no real radiator's, and nothing from it is used.
The fans' Ubar was set on that solve's pilots, from rest to 10 s, and kept: over the first 10 s the convector
does not change the fan's own flow, and the solved runs carried 1.000 and 0.990 of the target over 4-10 s.

**The re-solve** on 10 Nov 2026 changed only the convector, to `radiatorCover`'s fin gap and hv; the room, mesh,
walls, fans and numerics are the first solve's. On our own machine the bare check ran 0-40 s on 8 ranks (416 s);
then the three runs ran side by side from rest to 300 s, one physical core a rank: `nofan` on 3 ranks, 21,272
steps in 6,197 s (1.7 h); `fan_radiator` on 5, 49,508 steps in 10,367 s (2.9 h); `fan_ceiling` on 7, 116,359
steps in 14,472 s (4.0 h). No setting was changed after the bare check, and no time step, tolerance or mesh was
relaxed.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with `wmake` and MPI, and Python 3 with NumPy.

    cd cases/tallRoomFan
    ./Allrun nofan               # [nProcs], default 3
    ./Allrun fan_ceiling         # default 7
    ./Allrun fan_radiator        # optional, default 5
    ./Allrun bare                # optional: the convector's check, 0-40 s, default 8
    python3 scripts/extract_results.py runs results

`Allrun` compiles `src/radLayerWall` into `$FOAM_USER_LIBBIN` as `libradLayerWall.so` (the same code and library
name as `sofaLegsVsFlat`'s), writes the run into `runs/<run>/` with `scripts/make_case.py` (the mesh with its cell
zones `convector`, `fan_radiator`, `fan_ceiling` and `fan` and the fans' face zones, 0/T, 0/IDefault, the
hydrostatic 0/p and 0/p_rgh; `template/common/`, then `template/<run>/` for the rest, `bare` taking
`template/nofan/` and `template/bare/`), checks the mesh, writes the t = 0 plane with `system/clip` (not bare),
decomposes it by scotch, solves, and once `nofan` and `fan_ceiling` have solved writes `results/`, with
`fan_radiator` once it has reached 300 s and the bare check if `runs/bare` has run. The three runs differ only in
`constant/fvOptions` (the `fanForce` on one zone, or none). `./Allrun --setup-only <run> [nProcs]` stops before the
solve; `./Allclean` removes the runs.

The dictionaries are the solved runs' byte for byte, comments included, but for the `#include` of
`config/caseSettings`, which the study kept beside each run as `system/caseSettings`. Some comments are stale from
`radiatorCover` and `sofaLegsVsFlat`: `config/caseSettings` calls itself "the one settings file both runs, bare and
cover, read", calls `Tamb` "20 C" (it is 289.15 K, 16 °C, and every run reads it), describes `dy` as the one fitted
setting (here `dy` and `fy` are the fin gap's and `hv` is the fitted one), and calls the 30 s field writes "the fields
once, at the end"; `thermophysicalProperties` says the enthalpy is referenced at 20 C (it is `Tamb`).
`heatAccounting` still writes `radiatorCover`'s cover columns, which are zero or unused here. The solved runs also
had a `constant/fanSettings` holding Ubar, which nothing read, and `sofaLegsVsFlat`'s `controlDict.pilot`,
`controlDict.production` and `planeFunctions`, which nothing read either; they are left out.

Each run writes 481 planes of about 1.2 MB gzipped, the fields every 30 s keeping the last two, and every-step
monitors of up to about 150 MB (`fan_ceiling`). `results/` holds the summary, the minutes and each run's history in
2.5 s windows; no fields, meshes, planes or logs.

The case was set up and solved by an agent on our own machine and checked by us. The files in `results/` are what
`scripts/extract_results.py` wrote from the solved runs' monitors.

Checked from a clean copy of the case: `scripts/make_case.py` writes the solved runs' meshes (points, faces, owner,
neighbour, boundary, the cell, face and point zones and the fans' cell sets) byte for byte, their 0/ fields byte for
byte, and their `constant/` and `system/` byte for byte but for the `#include` line; `checkMesh` is OK at 43,812
cells and the t = 0 plane of `nofan` is the solved run's byte for byte. No solve was run from the clean copy.
`scripts/extract_results.py` on the solved runs' monitors gives the study's own figures: the 11.95% and 33.20%
gains, the line temperatures, the budgets and the bare check.
