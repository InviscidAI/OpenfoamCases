# A fan bar on top of a radiator, against the bare radiator

Radiator fans are sold to sit under a radiator and blow up through its fins, and also as a bar that
stands on a double panel radiator's top grille, draws the warm air up out of the fins and blows it
level into the room. This case switches the same radiator on under a tall window in the same cold
study, once bare and once with such a bar on its top, and asks where the heat goes in the first
minutes: out into the room, or up the glass and out through the window. It is about where the heat
goes, not energy bills: the bar's own electricity is left out, and whether a boiler would burn less is
a question about the heating system.

    ./Allrun bare    # the radiator alone, 0-300 s from switch-on
    ./Allrun fan     # the same radiator with the fan bar on its top, 0-300 s

**The result.** Over the first two minutes, which the clip shows, the fan bar hardly changes how much
heat the radiator gives; it changes where the heat goes. From switch-on to 2:00 the radiator gives
**2.2% more** with the bar than bare (1129.1 against 1105.2 W/m), and over the second minute, 60-120 s,
**0.8% less** (1080.2 against 1089.2 W/m). Both are below the 6.5-12.6% that
[`radiatorCover`](../radiatorCover)'s fans under a radiator gained, and far below the "about 20%" quoted
second-hand from Milieu Centraal for radiator fans. But the bar sends the warm air out across the room
where the bare radiator's plume climbs the glass, and over those two minutes **26% less heat goes out
through the window** with the bar (11.43 against 15.46 kJ/m, 74% of the bare room's). Over the whole run,
0-300 s, the bar gives 3.4% more heat (307.8 against 297.8 kJ/m) and 8.5% more over the last minute
(908.3 against 836.9 W/m), because the bare radiator's own draught weakens as its room warms, while the
window's saving shrinks to 13% over the five minutes (36.3 against 41.7 kJ/m) and 5% over the last
minute. Read [What it cannot](#what-it-cannot) before any number here: **the fins' gap is a chosen
value, not a sourced one**, **the 2-D section warms far faster than a real room**, and **the bar is a
slot along the whole radiator, not a row of round fans**.

The room, the radiator and the bar are new. The fins are modelled as in `radiatorCover`'s `finsBare`
and `finsFans` runs, with a wider gap; the walls are [`sofaLegsVsFlat`](../sofaLegsVsFlat)'s layers that
store heat, and the glass is [`radiatorUnderWindow`](../radiatorUnderWindow)'s.

## The room

x runs from the window wall into the room, y up from the floor; the section is 1 m deep in z, one cell,
with empty front and back. All figures are per metre of section.

| | value | from |
|---|---|---|
| room | a study 3.4 m from the window wall to the inner wall, 2.7 m high, as a vertical section through the middle of the radiator and the bar | ours |
| window | at x = 0: glass from y = 0.85 to 2.45 m (`glass`), wall below and above (`outerWall`); no sill board | ours, a tall window as in an older house |
| glass | no layer; h = 4.403 W/m²K to 0 °C outside (U = 2.8 W/m²K double glazing less the inside film, which is the solver's), emissivity 0.84 | [`radiatorUnderWindow`](../radiatorUnderWindow)'s glass |
| inner wall | x = 3.4 m (`innerWall`) | |
| floor | 19 mm of wood, k = 0.106 W/m K, ρc = 1,237,411.2 J/m³K | as [`sofaLegsVsFlat`](../sofaLegsVsFlat) |
| ceiling, inner wall and the window wall's opaque parts | 12.7 mm of gypsum board, k = 0.1587 W/m K, ρc = 723,991 J/m³K | the same |
| start | the air at rest at 16 °C in hydrostatic balance (1e5 Pa at y = 1.35 m), every wall layer at 16 °C; 0 °C outside | a house cooled overnight |

**The walls store heat.** Every surface but the radiator's panels and the bar's housing is
`radLayerWall` (`src/radLayerWall`, the compiled condition of [`ceilingVsUnderfloor`](../ceilingVsUnderfloor)
and `sofaLegsVsFlat`, its code unchanged): convection and the radiation it absorbs on the room side,
emissivity 0.9 (0.84 the glass), and behind it a 1-D layer of 24 slices with its heat capacity and an
adiabatic back. Nothing leaves the room but through the glass. There is no furniture, no door and no
air leak.

## The radiator

**A Stelrad Compact K2, 600 mm high**: two steel panels with convector fins between them, rated **1732 W
per metre at ΔT50** (75/65/20 °C) with an exponent of **1.33** (Stelrad's Compact data sheet, its EN 442
table). A double panel is used because the bars stand on a double radiator's top grille. The sheet's
bracket drawing puts a K2's front 124 mm from the wall, so in the section the back panel is at
x = 0.024-0.042 m, the fins at 0.042-0.106 and the front panel at 0.106-0.124, from y = 0.10 to 0.70 m,
with 24 mm of open air behind. Both panels are left out of the mesh and held at 55 °C from t = 0
(`radiatorPanel`, emissivity 0.9), its water never cooling.

**The fins** are a zone of the air between the panels (`convector`, 660 cells, 0.0384 m³ per metre), in
`radiatorCover`'s fin-gap form (its README, "Fans under the radiator"):

- an upward resistance of laminar flow between vertical plates a gap s apart, with a 0.5 mm sheet 0.6 m
  tall: d_y = 12/(φ s²) and f_y = 0.674/(L φ²) (Shah and London's fRe = 24 and K_inf for plates;
  `scripts/fin_gap.py`), sideways closed (1e8);
- the fins heat the zone's air through a conductance, S = hv (55 °C - T) per unit volume, written for an
  enthalpy referenced at 16 °C as Su = hv (328.15 - 289.15), Sp = -hv/1005
  (`template/common/constant/fvOptions`).

**The fin gap, 6.86 mm, is chosen, not sourced.** Stelrad publishes no fin gap. `radiatorCover`'s 6.31 mm
(Calisir et al.'s optimum gap, as summarised by Dalkilic et al.) leaves this radiator short of its rating
whatever the conductance: at hv 250, 1000, 4000 and 16,000 W/m³K the bare K2 gave 32%, 16%, 7.4% and 4.7%
less than its rating, levelling off near 1,090 W/m, because the air already leaves the fins at nearly
55 °C and what is missing is the draught through them, about a tenth too little air. A radiator that draws
too little air would flatter a fan that adds air, so the gap was widened until the bare radiator met its
rating, and that gap is used in both runs. It is a value fitted to the catalogue, not Stelrad's or any
published figure.

**hv is held at a chosen 4000 W/m³K.** With two settings and one rating one has to be fixed. Between hv
4000 and 16,000 the output moved only 2.4%, so the gap is what governs it. 4000 is within 15% of the fully
developed laminar value for a 6.31 mm gap (4,650; Nu 7.54 on twice the gap, both faces wetted, fin
efficiency 1) and about 1% above it for 6.86 mm (3,957). At the bar's flow the fins' NTU is about 7.6, so
the bar's air also leaves near the fins' temperature, and hv does not cap the bar's gain.

**The fit**, bare pilots from rest to 40 s, their output over 25-40 s against 1732 ((55 - T)/50)^1.33 W/m at
that interval's mean room temperature T:

| gap (mm) | d_y (m⁻²) | f_y (m⁻¹) | output (W/m) | rating at T (W/m) | error |
|---:|---:|---:|---:|---:|---:|
| 6.31 | 325,267 | 1.308 | 1056.0 | 1140.1 | -7.37% |
| 7.00 | 262,391 | 1.290 | 1148.9 | 1128.7 | +1.79% |
| 8.00 | 199,219 | 1.268 | 1276.5 | 1113.4 | +14.64% |
| 9.50 | 139,962 | 1.245 | 1441.8 | 1094.2 | +31.77% |
| **6.86** (interpolated in log gap, confirmed) | **273,581** | **1.293** | **1130.3** | **1131.0** | **-0.06%** |

In each pilot the fins' heat from the source and from the zone air's own energy balance agree to 0.016%.

## The fan bar

**The housing** stands on the radiator's top, in the `fan` run only: a solid top plate (x = 0.024-0.124 m,
y = 0.72-0.73 m) and a back plate over the back panel (x = 0.024-0.042, y = 0.70-0.72), both left out of the
mesh as the patch `fanBar`, adiabatic (zeroGradient T) with emissivity 0.9. Under the top plate is a 20 mm
channel whose floor is the fins' open top and the front panel's top face, and whose outlet, 20 mm tall,
faces the room at x = 0.124 m. In the `bare` run the plates' 46 cells are plain air; every other cell is the
same in both meshes.

**The fan** is the cell zone `fan`, 12 cells in the channel over the front panel (x = 0.106-0.124,
y = 0.70-0.72 m), driven by OpenFOAM's `meanVelocityForce` along +x at **Ubar = 0.9074 m/s**
(`template/fan/constant/fanSettings`), from t = 0. In the bare run the zone is air and is not driven.

**Its air: 16.667 L/s per metre, SpeedComfort's figure.** We found no published airflow for any bar that
stands on top of a radiator. So the bar is given SpeedComfort's 30 m³/h a fan (speedcomfort.com, the Duo
set, two fans for a 70-120 cm radiator, as in `radiatorCover`), two fans on the 1 m radiator, 60 m³/h, which
is 16.667 L/s per metre. That makes the comparison with `radiatorCover`'s fans under the radiator one of
position, not of fan. Ubar was set from the air through the outlet face (the face zone `fanOut`), not the
zone's mean velocity: pilots from rest to 10 s gave 15.31 L/s per metre at 0.8333 m/s (-8.2%) and 16.60 at
0.9074 m/s (-0.42%) over 4-10 s; the force there was about 52.6 Pa/m over the zone, a pressure rise of about
0.95 Pa. In the solved run the outlet carried **16.46-16.56 L/s per metre** minute by minute, within 1.2% of
the target. The bar's own heat, about 1 W, is left out.

**All the bar's air comes through the fins**, because its channel has no other inlet: 14.7-15.2 L/s per
metre goes up into the fins' bottom, and expanded by its warming it is the 16.5 L/s out of the outlet. The
bare radiator's own draught through its fins is 12.8-13.2 L/s per metre over the first two minutes and falls
to 10.9 over the last minute as its room warms.

## The model

`buoyantPimpleFoam` (OpenFOAM v2512), compressible air as a perfect gas (Cp 1005 J/kg K, μ 1.82e-5 Pa s,
Pr 0.71), k-ω SST with `buoyancyTurbSource` and wall functions, Euler in time at Courant 1 (maxDeltaT
0.25 s), two outer and two pressure correctors, the final p_rgh solve to 1e-8 or 100 iterations, the
pressure reference in the middle of the room at (1.7, 1.35) m. Radiation is fvDOM, transparent air, 32
directions in the plane (nPhi 8, nTheta 0), solved every 10 steps, starting from the black-body intensity
at 16 °C. The numerics are `sofaLegsVsFlat`'s (`config/caseSettings`).

**The mesh** is written directly by `scripts/make_case.py`, `radiatorCover`'s writer with this room's grid:
**184 x 180 cells, 32,760 in the bare run and 32,714 with the bar** (the panels' cells and, with the bar, its
plates' left out), graded with lines on every edge of the panels, the fins, the bar and the glass: 6 mm in x
near the radiator, 5 mm in y through the bar and its outlet, up to 28 mm in the middle of the room; the
smallest cells 5.82 x 5.00 mm, the largest 28.0 x 27.9 mm, neighbours within 1.12 in x and 1.13 in y;
orthogonal, `checkMesh` OK. One mesh, no mesh study.

**The monitors** (`config/caseSettings`): `heatAccounting` every step, for the panels' convection and
radiation, the fin zone's energy balance, each wall's convection and absorbed radiation, the air's mass and
its internal energy (cv/R) ∫p dV; `diagnostics67` every step, for the gross flows through the fan's and the
fins' faces, the heat stored in every layer, the glass's mean temperature below and above 1.65 m, the mean
temperature along lines across the room (x = 0.5-3.3 m) at 0.1, 1.1 and 2.6 m, and the air beyond x =
0.424 m; `convT`, the integral of T over the fin zone, for the fins' heat; three probes at x = 1.7 m; and
(`scripts/planeFunctions`) the section and the glass every 0.625 s, 481 a run.

## Results

`results/summary.txt`, `results/minutes.csv` and `results/<run>/history.csv` (2.5 s windows), from
`scripts/extract_results.py`. The radiator's heat is the panels' convection and radiation plus the fins'
heat to the zone's air, hv (55 °C x V - ∫T dV).

| the radiator's heat, W/m | 0-60 s | 60-120 | 120-180 | 180-240 | 240-300 | 0-120 | 0-300 |
|---|---:|---:|---:|---:|---:|---:|---:|
| bare | 1121.1 | 1089.2 | 1003.5 | 912.0 | 836.9 | 1105.2 | 992.5 |
| with the fan bar | 1177.9 | 1080.2 | 1017.8 | 946.5 | 908.3 | 1129.1 | 1026.1 |
| **fan / bare** | 105.1% | **99.2%** | 101.4% | 103.8% | 108.5% | **102.2%** | 103.4% |

| heat out through the glass, W/m | 0-60 s | 60-120 | 120-180 | 180-240 | 240-300 | 0-120 | 0-300 |
|---|---:|---:|---:|---:|---:|---:|---:|
| bare | 121.4 | 136.3 | 142.9 | 147.2 | 147.3 | 128.8 | 139.0 |
| with the fan bar | 84.5 | 106.0 | 134.1 | 139.2 | 140.6 | 95.2 | 120.9 |
| **fan / bare** | 69.6% | 77.8% | 93.8% | 94.6% | 95.4% | **73.9%** | 86.9% |

**The gain is small and grows late.** In the first minute the bar adds 5.1%, all of it the fins' (651.4
against 569.3 W/m), while the panels give a little less (526.6 against 551.8 W/m). In the second minute it gives 0.8% less, and only from the third minute on does it pull ahead, to 8.5% over the last
minute, as the bare radiator's draught weakens in a room that has warmed by about 13 K. That growth is in part the
section's over-fast warming (below). Against the sources, the two-minute +2.2% and the second minute's -0.8%
are below `radiatorCover`'s fans under the radiator (6.5% with its fin-gap convector, 12.6% with the earlier
one held at 55 °C), and far below the "about 20%" attributed to Milieu Centraal, which we have only
second-hand. The five-minute +3.4% and the last minute's +8.5% are inside or near 6.5-12.6%. None of this was
tuned to those figures: the gap was fitted in still air to the catalogue and Ubar to the bar's own flow.

**Where the heat goes.** The bare radiator's plume rises up the glass and the bar's jet leaves level into the
room. At 60 s the bare room's glass is at 19.5 °C on average and the fan room's at 12.8 °C; at 2:00 the lower
glass has warmed in both (20.0 and 21.0 °C below 1.65 m) but the fan room's upper glass is still cooler (16.1
against 19.7 °C). The window took 26% less heat with the bar over the first two minutes and 13% less over five.
The fan room is warmer: at 2:00 its air is 25.8 against 24.1 °C, 21.7 against 18.4 °C along the line 0.1 m
above the floor and 26.1 against 23.7 °C at 1.1 m, desk height; at 300 s 31.4 against 29.3 °C. These are
differences between two rooms that both warm far too fast, not temperatures anyone would see.

**Checks.** The whole section's heat budget over 10-300 s, the radiator's heat against the rise of the air's
internal energy, the heat stored in the wall layers, the heat out through the glass and the bar's housing,
closes to 0.024% (bare) and 0.036% (fan) of the radiator's heat; the fins' heat and the zone air's own energy
balance agree to 0.07% (bare) and 0.023% (fan) in every minute; the air's mass holds to 9.0e-7 of the
hydrostatic start. 27 (bare, all before 60 s) and 40 (fan) final pressure solves stopped at the
100-iteration cap, at residuals of 1.0e-8 to 4.5e-8; the tolerance was left at 1e-8.

## What the clip shows, and what it does not

The clip shows the two rooms whole, the bare radiator above and the bar below, **from switch-on to 2:00 of
the 300 s solve**, 6 times real time in 20 s, the air's temperature on a jet scale of 10-38 °C with moving air
parcels and the glass drawn in its own surface temperature, the question "A fan on top of the radiator: does
it help?", a clock, and in each room one rounded number: the heat out through the window since switch-on,
the bare room's two-minute total as 100%, ending at 100% and 74%. The 300 s run's later minutes are not in it.

- **The bar is drawn taller than solved**, 0.18 m over its 30 mm housing so that it reads on a phone, with a
  wheel turning on its face; the solved bar is the channel and the zone above.
- The parcels are moved through the planes' velocity after the solve; they are not solved particles. The
  frames between the solved planes are blended along the flow.

## What it cannot

- **A 2-D section warms far faster than a real room.** A 1 m radiator gives its whole rating to one metre of
  the room's depth, far more radiator per cubic metre of air than one radiator in a real 3.4 m study. Both rooms
  warm from 16 °C to about 24-26 °C in two minutes and 29-31 °C in five, which no real room does, so no time
  here is a real time. The shares compare the two rooms under the same over-fast warming; the growth of the
  bar's gain after two minutes is partly that warming, as the bare radiator's draught weakens in its hot room.
- **The fin gap is chosen**, 6.86 mm, to bring the bare radiator to Stelrad's rating; it is not Stelrad's figure
  or any published one, and hv is held at a chosen 4000 W/m³K. The bar's gain depends on the gap: with 6.31 mm
  the bare radiator drew too little air and fell 7.4% short of its rating, which would have made the bar look
  better. A real K2's fins, their depth and their two rows are not modelled.
- **The fan is a slot, not round fans.** The section spreads the bar's air evenly along the whole metre of
  radiator, with no ends and no gaps between fans; a real bar's few round fans blow jets that spread and mix
  differently, and the radiator's ends are absent. It is driven at a free-air figure with no pressure curve,
  and that figure is SpeedComfort's for fans under a radiator, not a published one for a bar on top.
- **All the bar's air comes through the fins.** Its channel has no other inlet. A real bar may draw some room
  air round its ends or past the grille, which would leave it less of the fins' warm air.
- **The housing is an idealisation.** Its plates are adiabatic with no heat capacity, at the temperature of
  the warm air beside them, so they radiate more than they absorb: about 17.5 W/m into the room over the run,
  1.7% of the radiator's heat, which comes from nowhere. It is counted in the budget and not in the radiator's
  heat; it warms the fan room slightly, which if anything raises its window's loss.
- **The panels are held at 55 °C**, switched on instantly, the water never cooling; the bar runs from t = 0
  rather than switching on at its thermostat's temperature.
- **One mesh, k-ω SST with wall functions, grey diffuse radiation from a black-body start.** No mesh study was
  run. The room is ours, with no furniture, door gap, ventilation or people.

## Sources

- Stelrad Compact data sheet, its EN 442 table (CETIAT tested): the K2 at 600 mm, 1732 W/m at 75/65/20 with
  n = 1.33, and the bracket drawing's 124 mm from the wall to the front; the maker's PDF as hosted at
  plumbworld.co.uk/documents/stelrad-compact.pdf, read 9 Nov 2026. Stelrad publishes no fin gap.
- The fin model and the 6.31 mm gap: [`radiatorCover`](../radiatorCover) (Calisir, Baskaya, Yazar and Yucedag
  (2015) as summarised by Dalkilic, Acikgoz, Ekici and Wongwises (2019); Shah and London (1978) for fRe = 24,
  Nu = 7.54 and K_inf = 0.674 for parallel plates).
- The fan's air: SpeedComfort, the Duo set, 2 x 30 m³/h for radiators of 70-120 cm, speedcomfort.com, as read
  for [`radiatorCover`](../radiatorCover) on 31 Oct 2026. No airflow was found for a bar that stands on top
  of a radiator.
- The 6.5% and 12.6% gains with fans under a radiator: [`radiatorCover`](../radiatorCover), its `finsFans` run
  and its earlier fan runs.
- The "about 20%" for radiator fans: Milieu Centraal, through a secondary quote, not checked here.
- The glass: [`radiatorUnderWindow`](../radiatorUnderWindow). The wood and gypsum layers and the wall
  condition: [`sofaLegsVsFlat`](../sofaLegsVsFlat), [`ceilingVsUnderfloor`](../ceilingVsUnderfloor).
- The question came from a viewer of `radiatorCover`'s fans under the radiator, who asked for the fans on top
  of the radiator, facing the middle of the room.

## How the case got here

**A first solve stopped at the fins' fit.** On 9 Nov 2026 the case was built with `radiatorCover`'s 6.31 mm
gap and hv to be fitted to the rating. The four bare pilots at hv 250 to 16,000 W/m³K all fell short of the
rating (the figures above), so it stopped there, before the bar or either run. Nothing from it is used but
its mesh, which is this case's, and its hv 4000 pilot, the 6.31 mm row of the fit table.

**The re-solve** on 10 Nov 2026 changed only the fins' gap, `constant/convectorSettings`: the fit above, the
bar's calibration, then both runs from rest to 300 s side by side on our own machine, 7 ranks each, one
physical core a rank. `fan` ran 80,660 steps in 9,760 s (2.7 h).

**The bare run was solved in two pieces.** A fault in the controller that ran the pair left `bare` paused at
60 s while `fan` ran on to 300 s, and `bare` was later continued from its 60 s fields: 7,819 steps in 982 s to
60 s, then 27,142 steps in 3,056 s from 60 to 300 s. A first continuation was discarded. It restarted with the
pressure reference at its usual 1e5 Pa. On start-up `buoyantPimpleFoam` shifts p so that the reference cell
reads pRefValue; in this closed room at 60 s that cell held 101,561.95 Pa, so p dropped by 1,562 Pa, the first
pressure correction lifted it back to hold the room's mass, and the dp/dt term turned the lift into heat,
1.27 K in every cell in one step. **A restart of this closed room must set pRefValue to the pressure at the
reference cell at the restart time.** The run was continued again from the same 60 s fields with
`PIMPLE { pRefValue 101561.95418082419; }` (its own 60 s pressure at the reference cell). A serial two-step
test of that restart reproduced the uninterrupted run (the room's Σ ρVT 3239.7739 against 3239.7742 after one
step), and across the join the room's air moves from 20.5161 to 20.5165 °C and the radiator's heat from
1122.85 to 1122.84 W/m. `bare`'s monitors are the first piece's to 60 s and the second's after it
(`scripts/extract_results.py --earlier`). `Allrun` runs both runs straight through from 0 to 300 s, so none
of this is needed to rebuild them; the template's `fvSolution` has the usual 1e5, right for a start from rest.

No setting was changed after the fit and the calibration, and no time step, tolerance or mesh was relaxed.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with `wmake` and MPI, and Python 3 with NumPy.

    cd cases/radiatorFanBar
    ./Allrun bare                # [nProcs], default 7
    ./Allrun fan                 # default 7
    python3 scripts/extract_results.py runs results

`Allrun` compiles `src/radLayerWall` into `$FOAM_USER_LIBBIN` as `libradLayerWall.so` (the same code and
library name as `sofaLegsVsFlat`'s), writes the run into `runs/<run>/` with `scripts/make_case.py` (the mesh
with its cell zones `convector` and `fan` and the face zones `fanIn`, `fanOut`, `convIn` and `convOut`, and
the hydrostatic 0/p and 0/p_rgh; `template/common/`, then `template/<run>/` for the rest), checks the mesh,
writes the t = 0 planes with `system/initialPlanes`, decomposes it by scotch, solves, and once both runs have
solved writes `results/`. The two runs differ in the mesh (the housing), `0/T` and
`constant/boundaryRadiationProperties` (the `fanBar` patch) and `constant/fanSettings` (fanOn 1 and Ubar).
`./Allrun --setup-only <run> [nProcs]` stops before the solve; `./Allclean` removes the runs. On our machine the
solved runs took about 1.1 h (bare) and 2.7 h (fan) of wall time on 7 ranks each.

The dictionaries are the solved runs' at launch byte for byte, comments included; `bare`'s `controlDict` and
`fvSolution` were changed afterwards only for its continuation (above). Some comments are stale from
`sofaLegsVsFlat` and `radiatorCover`: `config/caseSettings` calls itself "the one settings file both runs, bare
and cover, read", calls `Tamb` "20 C" (it is 289.15 K, 16 °C, and every run reads it) and calls the 30 s field
writes "the fields once, at the end"; `thermophysicalProperties` says the enthalpy is referenced at 20 C (it is
`Tamb`). `heatAccounting` still writes `radiatorCover`'s cover and MDF columns, which are zero or unused here,
and fvOptions has an old `coordinateRotation` keyword that v2512 warns about.

Each run writes 481 section planes and 481 glass planes (about 0.4 GB a run, gzipped), the fields every 30 s,
and every-step monitors of up to about 80 MB (`fan`). `results/` holds the summary, the minutes and each run's history in 2.5 s windows; no fields,
meshes, planes or logs.

The case was set up and solved by an agent on our own machine and checked by us. The files in `results/` are
what `scripts/extract_results.py` wrote from the solved runs' monitors.

Checked from a clean copy of the case: `scripts/make_case.py` writes the solved runs' meshes (points, faces,
owner, neighbour, boundary and the cell, face and point zones) byte for byte, their 0/ fields byte for byte,
and their `constant/` and `system/` byte for byte (`bare`'s as launched, before its continuation); `checkMesh` is
OK at 32,760 and 32,714 cells, and the `fan` run's t = 0 section and glass planes are the solved run's byte for
byte. No solve was run from the clean copy. `scripts/extract_results.py` on the solved runs' monitors gives the
study's own figures: the +2.2%, -0.8%, +3.4% and +8.5% gains, the window's 73.9% and 86.9%, and the budgets.
