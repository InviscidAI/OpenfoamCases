# A steam radiator's cabinet: a solid top against a perforated top

Many pre-war New York apartments box their steam radiators in sheet-steel cabinets, and a viewer of
our [`radiatorCover`](../radiatorCover) clip asked: "How about a slotted or otherwise penetrable top?"
The old trade answer is sharp. Heating Help's chart of enclosures (Dan Holohan and Frank Wilsey,
heatinghelp.com/systems-help-center/radiator-covers, its text read 5 Nov 2026, its drawing not seen)
calls a solid top over a perforated front "the classic radiator enclosure", with "little or no chimney
effect", and says to size the radiator 30% larger; with "holes to the top so that's going to let the hot
air escape", 5% larger. Read as output, about 77% against 95% of the bare radiator. This case switches
the same steam radiator on three times in the same cold living room, bare, in the cabinet with a solid
top and in the same cabinet with a perforated top, and asks how much of the bare radiator's heat gets
out of each cabinet in the first two minutes, and where it goes. Not comfort, and not fuel bills.

    ./Allrun bare          # the radiator with no cabinet, 0-120 s from switch-on: the reference
    ./Allrun solid         # in the cabinet with a solid top
    ./Allrun perforated    # the same cabinet with 5 open strips in its top

**The result.** Over the 120 s from switch-on, the heat that crossed the cabinet's outside was **60.7%
(solid top) and 71.1% (perforated top) of the bare radiator's heat into the room**, counted like for like
(below): 258.5 and 302.4 kJ per metre against bare's 476.0 kJ/m less the 50.4 kJ/m that bare put into the
floor and wall where the cabinet stands. That is the count the clip shows, as 61% and 71%, "heat out vs no
cabinet". The holes get more heat out, about ten points more, against the chart's 18. They also send more
of it to the window: the glass lost 65.5 kJ/m with the perforated top against 51.2 with the solid one, 28%
more, and both plumes reach the glass. Net of the glass the perforated room still comes out ahead, by 5.5
points of bare's net heat rather than ten. At 120 s the air outside the cabinet is at **26.9 °C with the
solid top and 28.5 °C with the perforated top** (bare 34.4 °C), from 16 °C. Read
[What it cannot](#what-it-cannot) before any number here: the radiator steps to 215 F at t = 0, and this
section's room warms several times faster than a real one, so these are the first two minutes of a model,
not a settled share.

This is a new case, not further runs of `radiatorCover`: the room, the radiator and the cabinet are new.
Its numerics, its mesh writer and its heat accounting are `radiatorCover`'s, and its walls are
`fanHeaterVsOilRadiator`'s `radLayerWall`.

## The room

x runs from the window wall into the room, y up from the floor; the section is 1 m deep in z, one cell,
with empty front and back. All figures are per metre of section.

| | value | from |
|---|---|---|
| room | a pre-war living room 5.5 m from the window wall to the far wall, 2.9 m (9.5 ft) high, as a vertical section | ceilings "about 9 ft and upwards" (hgtv.com, All About Pre-War Architecture; thenewyorkcitybroker.com, 9 to 10 ft or more; both search summaries); the length ours |
| window wall | x = 0: single-glazed sash from y = 0.852 m to 2.500 m (`glass`), wall below and above (`outerWall`) | the glass's lower edge is the 6 mm grid line nearest the brief's 0.85 m |
| glass | no layer; h = 23.577 W/m²K to 0 °C outside (U = 5.8 W/m²K single glazing less the inside film's 0.13 m²K/W, which is the solver's), emissivity 0.84 | a handbook U, ours; no storm window |
| far wall | x = 5.5 m, `innerWall` | |
| floor | 19 mm of wood, k = 0.106 W/m K, ρc = 1,237,411 J/m³K | as [`sofaLegsVsFlat`](../sofaLegsVsFlat) |
| ceiling and walls | 12.7 mm of gypsum board, k = 0.1587 W/m K, ρc = 723,991 J/m³K | the same |
| start | the air at rest at 16 °C in hydrostatic balance (1e5 Pa at (2.75, 1.45) m), every wall layer at 16 °C; 0 °C outside | ours, as `sofaLegsVsFlat`'s |

**The walls store heat.** Every surface but the iron is `radLayerWall` (`src/radLayerWall`,
`fanHeaterVsOilRadiator`'s code, the same as the study compiled; its header comment is this repository's):
convection and the radiation it absorbs on the room side, emissivity 0.9 (0.84 the glass), and behind it a
1-D layer of 24 slices with its heat capacity and an adiabatic back. Over two minutes the heat reaches only
the first few millimetres of plaster, so a masonry wall's real thickness does not enter.

## The radiator

**A 3-column cast-iron radiator 26 in high and 9 in deep**, rated from the Burnham Heating Helper's table
of obsolete radiation and Columbia Heating Products' capacity guide: 3.75 sq ft a section, 240 Btu/h per
sq ft on steam, sections about 2.5 in long, so 263.8 W a section and **4,154 W per metre** at 215 F in a
70 F room. In the section the radiator spans the whole depth, so that is per metre of room.

It stands 60 mm off the window wall on 78 mm feet: x = 0.060-0.288 m, y = 0.078-0.660 m (ours). **Its iron
is held at 215 F, 101.67 °C, 374.82 K, from t = 0**, a low-pressure steam radiator's temperature (Columbia),
held fixed because a fixed output could not show what the cabinet costs. The front and rear columns
(x = 0.060-0.120 and 0.228-0.288 m) are left out of the mesh, their faces the patch `radiatorPanel` at
374.82 K, emissivity 0.9 (painted iron, ours). The middle (x = 0.120-0.228 m) stands for every passage
between columns and sections that one plane cannot show: a zone of air, the cellZone `convector`, held at
374.82 K (`fixedTemperatureConstraint`) with an upward Darcy resistance d_y and sideways closed
(`constant/fvOptions`), `radiatorCover`'s convector with new numbers.

**The fit.** d_y was set on bare pilots, 0-30 s, so that the bare radiator's output over 20-30 s matched the
rating at the air's mean temperature, 4,154 W/m x (ΔT/80.56)^1.3, and then frozen. It was fitted to the
rating, never to a cabinet:

| pilot | d_y (1/m²) | output W/m | rating W/m | ratio |
|---|---|---|---|---|
| fit01 | 3e5 | 5,208 | 4,049 | 1.286 |
| fit02 | 6e5 | 3,581 | 4,207 | 0.851 |
| fit03 | 470,488.94 (frozen) | 4,085 | 4,156 | 0.983 |

The production `bare` run gives 4,083 W/m over the same 20-30 s against 4,157 W/m, 98.2%
(`results/summary.txt`). Of it about 975 W/m is the iron's radiation, 571 W/m the outer columns' convection
and 2,539 W/m the zone; we found no source for a column radiator's radiation share to check its 24% against.

## The cabinet

Sheet steel standing on the floor against the window wall, from Holohan's description: a perforated front at
x = 0.330 m, 42 mm clear of the iron, closed at its foot by a rail, and a top at y = 0.756 m, 96 mm above the
iron, about 30 in high. Arsco, the US maker of such enclosures, builds each to the radiator and publishes no
standard sizes that we could find, so the sizes are ours.

**The perforation.** A plane through a sheet of round holes cuts some holes and misses others, so the section
stands for it with strips of the same open share: 40% open, a stock pattern of 1/4 in holes on 3/8 in staggered
centres (McNichols; McMaster-Carr's table), drawn as 24 mm strips at a 60 mm pitch, four cells each.

- **The front** has 11 strips, y = 0.084-0.708 m, in both runs, a solid bottom rail below (from the floor) and
  a top rail above (to 0.756 m).
- **The top** is plain sheet in `solid`. In `perforated` it has 5 strips, x = 0.036-0.300 m.
- That is the only difference between the two runs.

Every part is a zero-thickness baffle, internal faces split into coincident wall patches `<part>A` and
`<part>B` (`top`, `topRail`, `bottomRail`, `grille`), each pair a `compressible::thermalBaffle1D` that passes
neither air nor radiation: 1.2 mm thick, radiating from each face with emissivity 0.9, no heat capacity, and a
conductivity of **0.5 W/m K, not steel's 50**, so as not to tie the two explicitly coupled faces stiffly; 417
W/m²K across the sheet is still far above the air films on either side. There is no gap under the cabinet.

## The model

`buoyantPimpleFoam` (OpenFOAM v2512), compressible air as a perfect gas (Cp 1005 J/kg K, μ 1.82e-5 Pa s,
Pr 0.71), k-ω SST with `buoyancyTurbSource`, Euler in time at Courant 1 (maxDeltaT 0.05 s, the first step
1e-4 s), two outer and two pressure correctors, the final p_rgh solve to 1e-8 or 100 iterations. Radiation is
fvDOM, transparent air, 32 directions in the plane (nPhi 8, nTheta 0), solved every 10 steps, starting from the
black-body intensity at 16 °C. The numerics are `radiatorCover`'s (`config/caseSettings`).

**The mesh** is written directly by `scripts/make_case.py`, `radiatorCover`'s writer with this room's grid:
276 x 308 cells, 6 mm in x to 0.42 m and in y to 0.90 m (the iron, the cabinet and its strips, the flow cuts),
widening to 30 mm across the room and 15 mm up past the glass, 12 mm at the far wall and 6 mm under the
ceiling; neighbours within 7% in x and 12% in y. **83,068 cells in all three runs**, the same cells and the
same grid, the smallest 6.0 x 5.76 mm; orthogonal, `checkMesh` OK. One mesh, no mesh study.

**The monitors** (`config/caseSettings`, coded function objects compiled at the solve's start):
`heatAccounting` every step, `radiatorCover`'s with this cabinet's box (x < 0.330, y < 0.756 m): the iron's
convection and radiation, the convector zone's energy balance, every wall's convection and absorbed radiation,
the enthalpy carried, diffused and radiated through the front's and the top's strips each way, the sheet's
outer faces' convection and radiation, the air's mass and its internal energy (cv/R) ∫p dV; `diagnostics57`
every simulated second, for the gross flows through the front, the top, the line above the cabinet (y = 0.90 m)
and the line into the room (x = 0.45 m), the mass-weighted air in and outside the cabinet's box, the heat stored
in every layer, and the sheet's faces (and every step in `baffles.csv`); and the section's plane, every 0.25 s in
`solid` and `perforated` (481 a run) and every 1 s in `bare` (121).

## Results

`results/summary.txt`, `results/minutes.csv` (every half minute) and `results/<run>/history.csv` (every 2.5 s),
from `scripts/extract_results.py`.

| 0-120 s from switch-on, kJ/m | bare | solid | perforated |
|---|---|---|---|
| the radiator's heat | 476.02 | 330.93 | 367.94 |
| heat out of the cabinet | | 258.46 | 302.45 |
| stored in the floor and wall inside the cabinet's footprint | 50.42 | 63.52 | 57.45 |
| lost through the glass | 58.16 | 51.24 | 65.46 |

| share of bare | solid | perforated | gap |
|---|---|---|---|
| **heat out of the cabinet / bare's heat less its footprint (the clip's)** | **60.73%** | **71.06%** | 10.3 |
| heat out of the cabinet / bare's whole heat (the brief's) | 54.30% | 63.54% | 9.2 |
| the radiator's own output / bare's | 69.52% | 77.30% | 7.8 |
| the radiator's output less the glass / bare's less its glass | 66.93% | 72.39% | 5.5 |

**Why the clip's count leaves out bare's footprint.** The heat out of a cabinet is what crosses its outside: the
air carried out and in through its strips, the radiation and diffusion through them, and the sheet's outer faces.
The floor and the window wall inside the cabinet's footprint (x < 0.330 m, y < 0.756 m) lie inside that boundary,
so what the cabinet runs store there never counts. In `radiatorCover` the wall was adiabatic and the question did
not arise; here the walls store heat during the start-up, and bare's 476.0 kJ/m includes 50.4 kJ/m into that same
patch. Taking it out leaves 425.6 kJ/m and gives 60.7% and 71.1%. **This count was chosen after the result was
known**: the brief named the whole of bare's heat, 54.3% and 63.5%, 9.2 points apart, under the 10-point gap the
brief set for a clip, and the like-for-like count was found afterwards and happens to cross it. A third count, the
radiator's own output, puts them 7.8 points apart. The honest reading is about nine or ten points. The footprint's
heat is read from the layer temperatures in each run's T at 120 s, and each patch's whole matches the run's own
storage monitor to five figures. The cabinet's own balance closes: the radiator's output less the heat out and the
footprint's store leaves 8.9 and 8.0 kJ/m (2.7% and 2.2% of the output), the cabinet's air and what is not
accounted for, of which the planes put 4.4 and 3.4 kJ/m in the air.

| t (s) | 10 | 20 | 30 | 60 | 90 | 120 |
|---|---|---|---|---|---|---|
| the clip's count so far, solid / perforated | 4.3 / 5.6% | 9.5 / 11.8% | 14.8 / 17.9% | 30.3 / 36.0% | 45.6 / 53.7% | 60.7 / 71.1% |
| the brief's count against bare at the same time, gap (points) | 12.4 | 11.0 | 10.5 | 9.8 | 9.4 | 9.2 |
| the radiator now, bare / solid / perforated (W/m) | 4145 / 2809 / 3232 | 4101 / 2775 / 3112 | 4063 / 2762 / 3094 | 4082 / 2674 / 2968 | 3962 / 2646 / 2862 | 3736 / 2597 / 2884 |
| the air outside the cabinet, bare / solid / perforated (°C) | 18.0 / 17.2 / 17.4 | 19.8 / 18.2 / 18.5 | 21.7 / 19.1 / 19.6 | 26.8 / 22.0 / 23.0 | 30.5 / 24.5 / 25.8 | 34.4 / 26.9 / 28.5 |

The clip's count is the heat out so far against bare's figure at 120 s, so it counts up from 0; the brief's
running count sets each against bare's heat to the same time. The gap falls as the clip goes on and is 8.6 points
in each of the last two half minutes on their own, so nothing in the last minute points to it opening. The air
is mass-weighted outside the cabinet's box (in bare, the same box, the radiator's own air, is left out); the
clip's planes give 26.94 and 28.53 °C for the area mean outside the cabinet at 120 s, the same to a tenth.

**Where the air goes.** With the solid top the hot air leaves by the front's top strips, 226.3 kJ/m carried out
through the front against 14.2 in, about 0.031 kg/s per metre in and out by the front over 100-120 s. With the
perforated top it leaves by the top, 279.3 kJ/m out through the top, and the front becomes the cold return, 22.6
kJ/m carried in against 0.8 out, about 0.042 kg/s in by the front and out by the top, 35% more air. The chart's
picture, that the solid top turns the hot air out into the room while the holes send it straight up the window,
is half right: the jet out of the solid cabinet's front curls back to the window wall and climbs it too, so both
plumes reach the glass. The perforated top loses more there, 21.6% of the heat that left its cabinet against
19.8%.

**Checks.** The whole section's heat budget over 10-120 s, the radiator's heat against the rise of the air's
internal energy, the heat stored in the layers and the heat out through the glass, closes to -0.11% (bare),
-0.19% (solid) and -0.25% (perforated) of the radiator's heat. Each layer's stored heat matches minus its
integrated wall heat flux to 0.005% or better. The air's mass holds to 9.0e-7 of the hydrostatic start. No final
pressure solve reached its 100-iteration cap. The sheet's faces stay within 16.5-77.8 °C, and in the pilots and
the production runs no face's mean jumped back and forth by more than 0.5 K at the radiation updates. The step
was 4.3-5.1 ms at the end, set in solid by the jet out of the front's top strips and in perforated by the air
falling inside the cabinet near the floor.

## What the clip shows, and what it does not

The clip shows the two rooms whole, from the window wall to the far wall and from floor to ceiling, stacked,
"solid top" above and "perforated top" below, from switch-on, 120 s at 6 times real time, the air's temperature
on a linear scale of 16-36 °C with moving air parcels, the question "Radiator cabinet: do holes in the top
help?", a clock, the note "strips stand for round holes", and in each room one rounded number, the heat out of
the cabinet so far as a share of bare's like-for-like total, "heat out vs no cabinet", ending at 61% and 71%. The
last frame is held for 0.5 s.

- **What is drawn, not solved.** The sheet is drawn as a solid line or a dashed one over baffles that have no
  thickness in the solve; its strips sit on the solved strips. The two outer iron columns are drawn over the
  holes they leave in the plane. The middle column is drawn over the zone of air held at 215 F, which is not a
  solid in the solve, and the feet are drawn so that the iron does not hang in the air. The parcels are moved
  through the planes' velocity after the solve; they are not solved particles.
- **The picture looks more decided than the numbers.** On the 16-36 °C scale the perforated room looks plainly
  warmer where the mean gap at the end is 1.6 K, both plumes reach the top of the scale at the glass, and the
  picture does not show the 28% more lost through it.
- The 61% and 71% are the 60.7% and 71.1% above, this section's first two minutes.

## What it cannot

- **The step start.** The iron and the convector zone step to 215 F at t = 0, where a real steam radiator fills
  with steam over minutes. The cabinet's air expands at once: by 0.25 s the solid cabinet, which can vent only
  through its front, sends a jet along the floor at about 8 m/s (the perforated one vents upward as well), and it
  rolls up into a vortex that drifts to about 2.5 m from the window, slowing from about 1 m/s at 3 s to 0.3 m/s at
  10 s, until the room's own circulation overtakes it by about 18 s. In the clip it is a ring of parcels over air
  still at 16 °C in the solid room. It is the model's start, not the cabinet's doing. It does not touch the count:
  by 0.25 s 0.716 and 0.721 kJ/m have crossed the two cabinets, under 0.3% of their totals, and the air it moves
  is at 16 °C. The start also makes the first seconds' output nothing like a radiator's: bare's first 2.5 s
  average 6,119 W/m against a rating of 4,154, and the cabinets' 5,807 and 6,218 W/m.
- **The room warms far too fast.** The radiator runs the section's whole depth, so per metre of room it is a
  metre of a 4,154 W/m steam radiator, six times `radiatorCover`'s panel, in a sealed section. The air outside
  the cabinet goes from 16 °C to 26.9 and 28.5 °C in two minutes, and bare's to 34.4 °C; no room warms 11-18 K in
  two minutes. The walls are still filling at 120 s (the floor and wall inside the footprint alone take 12-13% of
  bare's heat), and the shares since switch-on are still moving: the brief's gap fell from 12.4 points at 10 s to
  8.6 over the last minute. So these are the shares of the first two minutes from cold, not settled ones, and
  the chart's 30% and 5%, sizing allowances for steady running, are neither confirmed nor refuted.
- **A 2-D section.** No ends to the cabinet or the radiator, no gaps between sections, nothing round the sides:
  the section stands for the middle of an endless radiator in an endless cabinet.
- **Strips stand for round holes.** 24 mm strips at the pattern's 40% open share, much wider than 1/4 in holes;
  a thin plate's resistance depends mostly on its open share, but the jets through real holes are not these.
- **A sheet with no heat capacity**, and a conductivity of 0.5 W/m K, not steel's: the real cabinet warms more
  slowly than this one over two minutes.
- **The count was chosen after the result**, as above; 61 and 71 sit in a spread of 54-77% by three counts.
- **One cabinet of our sizing, one mesh**, k-ω SST, radiation from a black-body start, the radiator's 24% of
  radiation unchecked against a source; no storm window, no draughts, no furniture, no people.

## Sources

- The claim tested: Heating Help, "Radiator covers", Dan Holohan and Frank Wilsey's chart of enclosures
  (heatinghelp.com/systems-help-center/radiator-covers), its text read 5 Nov 2026, the chart's drawing not seen.
  The likely source for such charts, Fahnestock's University of Illinois Bulletin 169 (1927), could not be read.
- The radiator: the Burnham Heating Helper's table of obsolete radiation and Columbia Heating Products'
  capacity guide (3.75 sq ft a section for a 3-column 26 in radiator; 240 Btu/h per sq ft on steam; 215 F).
- The perforation: McNichols and McMaster-Carr, 1/4 in holes on 3/8 in staggered centres, 40% open.
- The ceiling height: hgtv.com and thenewyorkcitybroker.com, through search summaries.
- The wall condition: [`fanHeaterVsOilRadiator`](../fanHeaterVsOilRadiator) (from
  [`ceilingVsUnderfloor`](../ceilingVsUnderfloor)); the wood and gypsum layers as
  [`sofaLegsVsFlat`](../sofaLegsVsFlat); the mesh writer, numerics and heat accounting
  [`radiatorCover`](../radiatorCover).
- The question came from svrtefternavn's comment on the `radiatorCover` clip.

## How the case got here

The subject was first named in `radiatorCover`'s room, with its panel and MDF cover and a slotted top; on 5 Nov
2026 it was moved to this new scene before anything was solved. The set-up was solved on our own machine, not the
cloud, where a similar job had projected 18.5 h a run on four cores. Three bare pilots, 0-30 s on 8 ranks, fitted
d_y (above); two cabinet pilots, 0-30 s on 8 ranks, checked the air's mass, the layers, the budget and the sheet's
faces at the radiation updates and projected 5.1 h a run on 5, and were discarded. A disk check then stopped the
launch at 2.37 GiB free; the pilots' duplicate meshes and compiled code were removed and the runs launched with no
setting changed. All three ran from rest to 120 s side by side, 5 ranks each, one physical core a rank: bare
27,016 steps in 13,151 s (3.7 h), solid 28,418 in 15,298 s (4.2 h), perforated 29,700 in 16,584 s (4.6 h). No
time step, tolerance or mesh was relaxed between the pilots and production.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with `wmake` and MPI, and Python 3 with NumPy.

    cd cases/radiatorCabinetTop
    ./Allrun bare                # [nProcs], default 5
    ./Allrun solid
    ./Allrun perforated
    python3 scripts/extract_results.py runs results

`Allrun` compiles `src/radLayerWall` into `$FOAM_USER_LIBBIN` as `libradLayerWall.so` (the same code and library
name as `ceilingVsUnderfloor`'s, `fanHeaterVsOilRadiator`'s and `sofaLegsVsFlat`'s), writes the run into
`runs/<run>/` with `scripts/make_case.py` (the mesh, 0/T, 0/IDefault, 0/G, 0/qr, the hydrostatic 0/p and 0/p_rgh,
and `initial.json`; `template/common/` and `template/cabinet/` or `template/bare/` for the rest), checks the mesh,
writes the t = 0 plane, decomposes it by scotch into the collated format, solves, and once all three have solved
writes `results/`. `extract_results.py` reads the footprint's heat from the collated `processors*/120/T`.
`./Allrun --setup-only <run> [nProcs]` stops before the solve; `./Allclean` removes the runs.

The dictionaries are the solved runs' byte for byte. `config/caseSettings` sets `dy 300000`, the first pilot's,
and every run's `constant/fvOptions` and `system/controlDict` set the frozen `dy 470488.9431331412` after including
it, which is the value the runs used. `thermophysicalProperties` says the enthalpy is referenced at 20 C, a comment
carried from `radiatorCover`; `Tamb` is 289.15 K, 16 °C. `system/planeFunctions`, used only for the t = 0 plane,
keeps `radiatorCover`'s point and interval; the plane is the same z = 0.5 m cut. bare's `controlDict` writes its
plane every 1 s instead of 0.25 s.

Each of solid and perforated writes 481 planes of about 2.3 MB gzipped (the solve writes them uncompressed), the
fields every 30 s keeping the last two, and a `heat.csv` of about 18-20 MB. `results/` holds the summary, the half
minutes and each run's history every 2.5 s; no fields, meshes, planes or logs.

The case was set up and solved by an agent on our own machine and checked by us. The files in `results/` are what
`scripts/extract_results.py` wrote from the solved runs' monitors and their last written T.

Checked from a clean copy of the case, with the wall condition compiled into a scratch library folder:
`./Allrun --setup-only bare`, `solid` and `perforated` write the solved runs' `constant/` (the mesh included),
`system/`, `0/` and `initial.json` byte for byte, `checkMesh` OK at 83,068 cells and 333,070, 333,207 and 333,187
faces as the solved runs had, and t = 0 planes identical to the solved runs'. Nine serial steps of each run from
there gave the 5-rank logs' first-step initial residuals for Ux and Uy (1), h (to nine figures or better) and the first p_rgh solve
(0.9999788224 against 0.9999788226), and the first adjusted time step to 5e-5 or better; later residuals differ in
the fourth figure or so, as serial and parallel solves do, and scotch's decomposition is not the same from one run
to the next, so a new solve will not repeat the solved runs bit for bit. No full solve was run from the clean copy.
`scripts/extract_results.py` on the solved runs gives the clip's figures: 258.46 and 302.45 kJ/m out of the
cabinets, bare's 476.02 kJ/m with 50.42 in the footprint, 60.73% and 71.06%, and the brief's 54.30% and 63.54%.
