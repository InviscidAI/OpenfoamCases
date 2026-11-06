# A wet towel over a radiator, against the same radiator bare

Is drying washing on a radiator a way of heating the room, or does the heat go into the clothes?
"The clothes will be getting hot but your room isn't" (Moral Fibres, *Why You Shouldn't Dry Clothes
On Your Radiator*); "drying clothes on radiators with heating on is likely to increase space
heating" (Menon and Porteous, *Design Guide: Healthy Low Energy Home Laundering*, MEARU, Glasgow
School of Art, 2011). We found no measurement of it. This case takes a vertical section through a
small bedroom on a 0 °C day, with [`radiatorCover`](../radiatorCover)'s Stelrad K1 held at 55 °C on
its inner wall, switches the radiator on with nothing on it in one copy of the room and with a wet
towel draped over it in the other, and follows the first ten minutes with humid air, radiation and
a window that can mist.

    ./Allrun bare       # the radiator bare, 0-600 s from switch-on
    ./Allrun clothes    # the same radiator under a wet towel, 0-600 s

**The result.** Over the first ten minutes the towelled radiator gives 251.4 kJ per metre against
the bare one's 367.2 (68.5%), and only 142.8 kJ of that reaches the room: the rest, 108.7 kJ, warms
the towel and leaves in its water. So **the towelled radiator's heat reaching the room is 38.9% of
the bare one's over the first ten minutes**. At ten minutes the rooms' air averages **27.9 °C bare
against 19.3 °C with the towel**, both from 16.0 °C. 41.5 g per metre of water leaves the towel, 36.0 g
of it still in the air at ten minutes and 5.4 g on the window, which mists over its whole height
within three minutes with the towel and not at all without it. The 38.9% is not a settled share: it rises
from 29.5% after one minute, and over the last minute alone it is 47%. Read
[What it cannot](#what-it-cannot) before any number here, first that this sealed section warms,
and its air gets humid and its window mists, about two and a half times as fast as a real room.

## The room

x runs from the inner wall (the radiator's) to the window wall, y up from the floor; the section is
1 m deep in z, one cell, with empty front and back. Everything is per metre of section.

| | value | from |
|---|---|---|
| room | x = 0-3.0 m, 2.4 m high, closed: door and window shut, no ventilation | a single bedroom, 7.5 m² by the Nationally Described Space Standard (2.5 m across) |
| start | air and every inner surface at 16 °C at rest, the pressure hydrostatic (1e5 Pa at y = 1.174 m), 7 g of water per kg of air (61%) | BS 5250:2011 D.3.4 for the water |
| window | glass from y = 0.9 to 2.1 m in the far wall, h = 4.403 W/m²K to 0 °C outside (U = 2.8 W/m²K less the inside film), its inner pane storing 8,400 J/m²K (4 mm), starting at 10.2 °C, emissivity 0.84 | `radiatorCover`'s glass; the pane's capacity from handbook values |
| wall round the window | massless, h = 1.863 W/m²K to 0 °C (U = 1.5 W/m²K, an unfilled cavity, ours), starting at 12.9 °C | |
| ceiling, inner wall | 12.7 mm gypsum board, the floor 19 mm wood, each a 1-D layer of 24 slices with its heat capacity and an adiabatic back; emissivity 0.9 | [`fanHeaterVsOilRadiator`](../fanHeaterVsOilRadiator)'s layers |
| bed | a single divan along the section, x = 0.75-2.65 m, 0.55 m high, its surface 50 mm of foam (k = 0.04 W/m K, ρc = 49,000 J/m³K) with an adiabatic back | ours |
| radiator | a Stelrad Compact K1 600 x 1000 on the inner wall: its steel front panel x = 0.103-0.123 m, y = 0.15-0.75 m, held at 55 °C; its convector behind, x = 0.040-0.103 m, a zone held at 55 °C with an upward resistance d_y = 1.63e7 m⁻² | [`radiatorCover`](../radiatorCover), unchanged (`config/caseSettings`) |
| towel | (`clothes`) one wet sheet over the top and 46 cm down the front and the back, standing 10 mm off the panel and its top, 17.5 mm off the wall behind and clear of the convector: an upturned U one cell thick, its legs x = 0.0175-0.021 and 0.1335-0.137 m from y = 0.30 m up, its top y = 0.7598-0.768 m, 1.047 m² of sheet per metre. 500 g/m² of cotton dry (670 J/m²K) holding 0.25 kg/m² of water, 262 g per metre, starting at 16 °C | ours; the water is the Glasgow figure of 2-2.5 litres for a 4-5 kg load |

The towel's top sits 0.2 mm lower than drawn (y = 0.7598, not 0.7600 m) so that the gap over the
panel's top is one whole cell.

## The model

`moistBuoyantFoam` (`src/moistBuoyantFoam`) is OpenFOAM's `rhoReactingBuoyantFoam` with one line
changed in `YEqn.H`: species diffuse with μ/0.60 + μ_t/0.85, water vapour's Schmidt number in air
and a turbulent one, where the stock solver uses μ_eff, a Schmidt number of 1, which would
evaporate about a third too slowly. The air is a mixture of O₂, N₂ and H₂O, perfect gases with JANAF
thermodynamics, so the vapour lightens the air it is in; no reactions. k-omega SST with
`buoyancyTurbSource` and wall functions, fvDOM radiation through the `radiation` fvOption (32
directions in the plane, solved every ten steps), Euler in time, Courant 1, two outer and two
pressure correctors, limitedLinear on h and the species.

**The towel and the window** are `system/wetWalls`, a coded function object (its parameters in
`system/wetWallsParameters.H`), which sets T and H₂O on the patches `cloth` and `glass` after every
step:

- The towel is cut into 8 mm lengths of sheet, each with one temperature shared by its two faces and
  the heat capacity of its cotton and its water. Each takes the air's heat and the radiation on both
  faces and pays the latent heat of what leaves it. Cotton in its constant-rate period dries as a
  wet surface does (Bengtsson, Segel, Havsteen-Mikkelsen and Padfield, *The physics of drying
  cloth*), so the air at its faces is saturated at its temperature (Buck, 1981) and the water that
  leaves is the solver's own diffusive flux of vapour at that face; there is no fabric coefficient
  to choose. It passes no air and conducts no heat along itself.
- Each glass face is its own node, with the pane's heat capacity and the film to outdoors. A face
  condenses where the next cell holds more vapour than saturation at the face, keeps the water as a
  film, evaporates it again when it can, and takes the latent heat either way; while wet its vapour
  is held at saturation, and while dry it is zero-gradient.

Both were tested on a small box before the runs: a light cloth in still air settled at 14.03 °C
against the air's psychrometric wet-bulb of 13.98 °C with nothing fitted, and the vapour balance
closed to 0.4% or better. In the bare run there is no towel and only the glass is wet-capable.
`wetWalls` writes its totals (`postProcessing/wetWalls/wet_0.dat`) and, every 1.25 s, each glass
face's film and temperature and each towel length's temperature and water (`faces_0.dat`).
`heatAccounting` logs, every step, the radiator's terms and every wall's heat
(`postProcessing/heatAccounting/heat.csv`); `diagnostics60` the room's air, the walls' stored heat,
the plume past y = 0.9 m and nine probes, every second; `surfaceStability60` the towel's mean,
lowest and highest temperature every step.

**The radiator's one fitted setting.** The convector's upward resistance is `radiatorCover`'s, fitted
there to Stelrad's 980 W at ΔT 50. Here a bare pilot over 25-40 s gave 712 W/m against 656 W/m from
the rating at the room's mean temperature, 8.6% high, and three more pilots that raised the
resistance 29 times moved it only to 7.1% high, so the resistance cannot close the gap and
`radiatorCover`'s value was kept. Most of the gap is the measure: in this short room a warm layer
under the ceiling lifts the mean to 18.3 °C while the air below the radiator is at 17.1 °C, and
against the rating at that air the output is 1.04 of it. Both runs have the same radiator, so the
comparison does not lean on this; the bare radiator's absolute watts may be a few per cent high.

**The mesh** is a Cartesian grid written directly as a polyMesh by `scripts/make_case.py`, with
lines on every edge of the panel, the convector, the towel and the bed: 46,559 cells bare and 46,415
with the towel (the towel's 144 cells out, no grid line moved), 3.3 mm across near the radiator, 6
mm vertically at the least, three cells across the 10.5 mm gap between the panel and the towel's
front, five across the 17.5 mm behind its back leg, and one across the 9.8 mm over the panel's top.
One mesh; no mesh study.

The two runs were solved from rest to 600 s on 8 ranks: `bare` 71,129 steps in 5.8 h, `clothes`
55,654 in 3.4 h.

## Results

`results/summary.txt` and `results/minutes.csv`, from `scripts/extract_results.py`; each run's history
every 2.5 s in `results/<run>/history.csv`.

| over 0-600 s, per metre | bare | towel | towel / bare |
|---|---|---|---|
| the radiator's heat (kJ) | 367.2 | 251.4 | 68.5% |
| kept warming the towel (kJ) | | 20.8 | |
| latent heat still in the vapour (kJ) | | 87.8 | |
| **the heat that reached the room (kJ)** | **367.2** | **142.8** | **38.9%** |
| the room's air at 600 s, mean (°C) | **27.9** | **19.3** | from 16.0 |
| the room's relative humidity at 600 s, mean (%) | 31 | 87 | from 61 |
| water: left the towel / in the air / on the glass (g) | | 41.5 / 36.0 / 5.4 | |

The radiator's heat is the panel's convection and radiation plus what the convector zone gives its
air, as `radiatorCover` measured it. The heat that reached the room is that less what the towel kept
warming itself and less the latent heat still held in vapour; latent heat given back where the
vapour condensed on the glass counts as reaching the room. Of the towelled radiator's own heat, 56.8%
reaches the room.

**By the minute** the towel room's share of the bare room's heat, cumulative from switch-on:

| t (s) | 60 | 120 | 180 | 240 | 300 | 360 | 420 | 480 | 540 | 600 |
|---|---|---|---|---|---|---|---|---|---|---|
| heat reached the room, % of bare | 29.5 | 29.1 | 30.8 | 32.5 | 33.9 | 35.2 | 36.2 | 37.2 | 38.1 | 38.9 |
| the radiator's heat, % of bare | 67.9 | 64.9 | 65.0 | 65.6 | 66.3 | 66.9 | 67.4 | 67.9 | 68.1 | 68.5 |

Two things move it. The towel stops taking heat to warm itself (it averages 27.8 °C at 600 s), and the
bare room warms so far that its radiator's output falls, from 766 W in the first minute to 548 W in
the last, against 521 to 394 W under the towel. Over the last minute alone the towel room gets 47% of
the bare room's heat. The second cause belongs to this sealed section (below).

**Where the air goes.** In the first seconds the towel's air leaves under its hem. After that the towel,
solid at its top, is an upturned cup: air heated beside the panel rises inside it and a slower, cooler
stream sinks down the sheet's inner faces and out at the hem. The air the room gets rises up the
outside of the towel. Past y = 0.9 m, within 0.6 m of the wall, 18.2 l/s rises at 600 s against 23.1
l/s bare, nearly as much air, carrying 139 W above 16 °C against 562 W (the monitor's values at 600 s),
a quarter of the heat, and all the water.

**The water.** The towel dries at 214-266 g per m² of sheet an hour after the first three minutes,
inside the 100-600 set before the runs as the range to accept without looking
for a reason (a balance of the hanging sheet gave about 230). At 600 s it still holds
0.21 of its 0.25 kg/m² on average, so ten minutes is a small part of its drying. The glass holds 0.1
g/m² of water over half its height from 148 s and over all of it from 159 s in the towel run, and none
in the bare run.

**Checks.** The air's mass holds to 1.0e-6 of the prepared state; the vapour budget (gain in the air
against evaporated less condensed) closes to 0.10%, each wall layer's stored heat to its integrated
wall heat flux to 0.09%, and the whole section's heat, air, layers, towel, glass, latent heat and the
losses outdoors, to -0.53% (bare) and -0.32% (towel) of the radiator's heat over 10-600 s. The air
stays within 11.2-55.0 °C. No temperature was limited.

## What it cannot

- **The section's towel spans its whole depth, and the section is sealed.** This is the largest
  limit. A real 1 m radiator in a 2.5 m wide room puts about 40% as much water and heat into each
  cubic metre of air as this section does, so here the room warms, and the humidity rises and the
  window mists, about two and a half times as fast as in a real room. The 12 K rise of the bare room,
  the humidities and the times to mist are this section's and not a real room's. It also bears on
  the 38.9%: the share going into the towel's own water and warming (57% of its radiator's heat
  reaching the room) depends on the section less, but the share against bare leans on how far the
  bare room has warmed and its radiator's output fallen. The 38.9% is this model's first ten minutes,
  not a general loss.
- **The evaporation model is ours,** and so are the towel's fall and its 10 mm gap; a real towel
  touches the panel in places. There is no measurement of a radiator's drying to compare with; the
  drying rate falls inside the range we expected before the runs, which is a check of size only.
- **The bare radiator's absolute watts are a few per cent high** (the fit, above). Quote shares
  between the runs, not watts.
- **The drawn views are drawings.** A clip made from this case shows the radiator, the towel and the
  window face on beside the section; those face-on views are drawings of the same objects, not
  solved, and the section's towel is drawn thicker than it is here.
- **The towel conducts no heat along itself and passes no air.** Its two folds, about 8 mm each of
  the 1.04 m sheet, lag the rest by up to 3 K because their lengths hold mostly outward faces.
- **Nothing else takes up water.** Only the glass condenses; walls, bedding and carpet absorb none,
  the cold wall round the window takes none, and air above saturation stays vapour (no mist in the
  air).
- **The radiator is held at 55 °C** in both runs; a real one's surface would shift a little with what
  it gives. One towel stands for a load of washing, and it covers the whole radiator.
- **Ten minutes from switch-on.** Over hours, the point of the argument, the runs say nothing
  directly: two litres a load is the Glasgow measurement, not ours. No ventilation, which over ten
  minutes is a small share. One mesh.
- **A reporting fault in `wetWalls`.** It sums the glass's latent heat on each rank and writes only
  the master's, which holds no glass faces, so the `glassLatCum_J` column of `wet_0.dat` is zero.
  The glass's own temperature took the latent heat correctly. `scripts/extract_results.py` recovers
  it from the film on each face at each 1.25 s write; at the 60 s field writes this agrees with the
  sum of the ranks' saved totals to 0.00025 J/m. The file is kept as the runs had it.

## Sources

- Moral Fibres, *Why You Shouldn't Dry Clothes On Your Radiator*.
- R. Menon and C. Porteous, *Design Guide: Healthy Low Energy Home Laundering*, Mackintosh
  Environmental Architecture Research Unit, Glasgow School of Art, 2011: 2-2.5 litres of water in a
  4-5 kg load.
- L. Bengtsson, S. Segel, M. Havsteen-Mikkelsen and T. Padfield, *The physics of drying cloth*:
  "water is evaporating at a constant rate almost until the end of the process".
- A. L. Buck, "New equations for computing vapor pressure and enhancement factor", J. Applied
  Meteorology 20 (1981): saturation over water.
- *Technical housing standards: nationally described space standard* (2015): a single bedroom of
  7.5 m², at least 2.15 m wide.
- BS 5250:2011, *Code of practice for control of condensation in buildings*, D.3.4.
- Stelrad Compact K1 600 x 1000, 980 W at ΔT 50; the radiator, its window and its fit:
  [`radiatorCover`](../radiatorCover); the wall layers and `radLayerWall`:
  [`fanHeaterVsOilRadiator`](../fanHeaterVsOilRadiator) and [`ceilingVsUnderfloor`](../ceilingVsUnderfloor).

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with `wmake` and MPI, and Python 3 with
NumPy for `scripts/make_case.py` and `scripts/extract_results.py`.

    cd cases/wetTowelRadiator
    ./Allrun bare                # [nProcs], default 8
    ./Allrun clothes
    python3 scripts/extract_results.py runs results

`Allrun` compiles `src/radLayerWall` into `$FOAM_USER_LIBBIN` as `libradLayerWall.so` (the same code as
`fanHeaterVsOilRadiator`'s, so building one case does not change the other) and `src/moistBuoyantFoam`
into `$FOAM_USER_APPBIN`, writes the run into `runs/<run>/` with `scripts/make_case.py` (the mesh, every
field of `0/`, `system/decomposeParDict`, and `template/common/` and `template/<run>/` copied in
unchanged), checks the mesh, decomposes it by scotch (collated) and solves; once both runs have solved
it writes `results/`. OpenFOAM compiles `system/wetWalls` and the three monitors into the run's
`dynamicCode/` when the solve starts, about a minute. `./Allrun --setup-only <run> [nProcs]` stops
before the solve; `./Allclean` removes the runs and the build logs. `constant/fvOptions` reads the
convector's resistance `dy` from `config/caseSettings`; the file is the one the runs read, and its
other entries are `radiatorCover`'s and unused here. The comments in `system/wetWalls` and
`src/moistBuoyantFoam/YEqn.H` are as the runs had them.

From a clean copy of this case, `./Allrun --setup-only bare` and `clothes` built `src/` and wrote both
solved runs' `constant/` (with `polyMesh`: points, faces, owner, neighbour, boundary and zones),
`system/` and `0/` byte for byte; checkMesh OK at 46,559 and 46,415 cells. A few serial steps of each
(to 0.01 s, 29 and 53 steps, the coded function objects compiled) give the first step's initial
residuals for h and the first p_rgh solve as the solved 8-rank logs to 3e-9 or better, and `wetWalls`'
first totals to four figures; after that the time steps differ in the fourth figure, as serial and
parallel solves do, so a new solve will not repeat the solved runs bit for bit. No full solve was run.

Each run writes 481 section planes of T, U and H₂O (`postProcessing/clip`, every 1.25 s, about 1.5 GB a
run uncompressed), field writes every 60 s (the last two kept) and every-step monitors (about 40 MB a
run). `results/` holds what `scripts/extract_results.py` wrote from the two solved runs' monitors; no
fields, meshes, planes or logs.

The case was set up and solved by an agent on our own machine and checked by us.
