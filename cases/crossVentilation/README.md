# Cross-ventilation: one window wide open, against two on opposite walls, in a light breeze

Does a second window on the opposite wall air a room faster than one window of the same size?
This case airs [`windowAiring`](../windowAiring)'s room on a 0 °C morning with its 60 W radiator
on, once through that case's single window turned wide open and once through two windows of half
its width, one in the window wall and one opposite it, the same 1.2 m² of opening in both. It
does so twice: in a light breeze of 2.5 m/s blowing straight at the window wall, over the first
three minutes, and on a still morning, over the first five. The numbers it reports are **the
share of the room's own air replaced** and **the air coming in through the windows**. It is not
about heat loss, heating costs or comfort.

One OpenFOAM case, four runs:

    ./Allrun one         # one 1.0 x 1.2 m window on the windward wall, in the breeze, 0-180 s
    ./Allrun two         # two 0.5 x 1.2 m windows on opposite walls, in the breeze, 0-180 s
    ./Allrun stillOne    # one window, still air, 0-300 s
    ./Allrun stillTwo    # two windows, still air, 0-300 s

**The breeze is a pressure on each wall, steady and square to the window wall.** It is not a
flow of outdoor air past the house, and it has no gusts. A steady pressure gives a single window
nothing that still air does not, so the single-window run in the breeze airs the room as on a
still morning, and a real single window in wind does somewhat better. **It is an empty room**,
its surfaces held at 20 °C, and only the first minutes. Read [What it cannot](#what-it-cannot)
before any number here.

## The rooms and the breeze

| | `one`, `stillOne` | `two`, `stillTwo` | from |
|---|---|---|---|
| room | 4.0 × 3.5 × 2.4 m, 33.6 m³, between the window wall and the wall opposite, both 24 cm thick | the same | windowAiring |
| windows | windowAiring's: a clear opening 1.0 × 1.2 m, sill 0.90 m, centred in the window wall; the wall opposite solid | a clear opening 0.5 × 1.2 m, sill 0.90 m, centred in each wall, so that one section through the room's middle cuts both | windowAiring; the halves ours |
| sashes, wide open | turned at 90° to the wall on the hinge side, 1.0 m into the room (windowAiring's `open`) | each 0.5 m sash the same way, on the same side of the room | windowAiring |
| radiator | windowAiring's box under the window wall's window, 1.0 m long, 60 W | the same, under the window wall's window only | windowAiring |
| outside | still 0 °C air beyond each wall: 1.5 m deep off its outer face, from 1 m below the floor to 3.4 m up, 2.5 m either side of the room's middle, open on every face. In `one` the air beyond the solid wall is a second region of the mesh, joined to nothing | the same, both joined to the room through their windows | windowAiring; the second side as roofWindowAiring's `wall` |
| surfaces | the room's floor, ceiling and walls held at 20 °C; the walls' outer faces, the reveals and the sashes adiabatic | the same | windowAiring |
| breeze (`one`, `two`) | +2.41 Pa on the air in front of the window wall, −1.45 Pa on the air behind the wall opposite | the same | below |
| start | the room's air at rest at 20 °C, the outdoor air at rest at 0 °C in its own barometric pressure and the breeze's; at t = 0 the windows are open | the same | windowAiring |

**The breeze.** 2.5 m/s at window height, blowing at right angles to the window wall. Chicago
O'Hare's mean December wind, 1961-1990, is 9.77 kt (5.0 m/s) at the airport's 10 m anemometer
(Illinois State Water Survey, wind rose for station 94846). ASHRAE's profile, as the EnergyPlus
Engineering Reference gives it (station α 0.14 and δ 270 m, suburbs α 0.22 and δ 370 m), brings
that to 2.4 m/s at 1.5 m and 2.9 m/s at 4 m, a ground-floor and a first-floor window. A house
turns the wind aside, and what reaches its windows is the pressure the wind puts on each wall,
C_p ½ρV², the way envelope models such as EnergyPlus's AirflowNetwork put wind on a building.
For a low-rise building with a square plan, Swami and Chandra's wall-averaged coefficients are
+0.60 on the windward wall and −0.36 on the leeward one. With ½ρV² = 3.99 Pa at 0 °C, that is
+2.41 Pa in front of the window wall and −1.45 Pa behind the wall opposite, 3.86 Pa across the
room, several times the half pascal of stack pressure across a window on a still morning.

Each outdoor volume stands for the thin layer of air against its wall, where the wind has already
been turned aside. It holds still apart from what the windows draw. Its open faces hold the still
0 °C air's barometric pressure scaled by its wall's pressure, p0(y) = (1e5 Pa + c) exp(−g y/(R T)),
c = +2.41 Pa in front and −1.45 Pa behind, as `prghTotalPressure` less the dynamic head on inflow,
and every cell starts at its own side's pressure (`scripts/wind_p.py`). The room and the openings
start at c = 0. On a still morning c = 0 on both sides, which is
[`roofWindowAiring`](../roofWindowAiring)'s barometric boundary.

## The model

`scripts/make_case.py <run> <dir>` writes every dictionary, the initial fields and the run's own
Allrun, with windowAiring's generator (`../windowAiring/scripts/make_case.py`).

- **Solver and physics, windowAiring's:** buoyantPimpleFoam (OpenFOAM v2512), air as a perfect
  gas (c_p 1005 J/kgK, μ 1.82e-5 Pa s, Pr 0.71), k-omega SST with wall functions and the buoyancy
  source on k, PIMPLE with 2 outer and 2 pressure correctors, Euler in time at Courant 1,
  limitedLinear for energy and turbulence and limitedLinearV for momentum, p_rgh to 1e-7. The
  radiator is an enthalpy source of 60 W spread over its box, through which the air passes freely
  (`radiatorUnderWindow`'s reasons for 60 W, about a tenth of a real radiator).
- **The mesh** is roofWindowAiring's `wall` box: windowAiring's blockMesh box run on past the
  room's inner wall, refined there as at the window wall, with 13 cells of 19.2 mm in each quarter
  of the 1.0 m window's width, so that the half-width windows' edges fall on cell faces; then
  subsetMesh to the air, the walls' outer faces and the reveals as a patch, and each sash as a
  zero-thickness baffle. 1,052,456 cells in every run, `checkMesh` OK, non-orthogonality 0;
  two regions in `one`, one in `two`. Each opening is 1.200 m² (2,080 faces) or 0.600 m² (1,040).
- **The room's own air** is a passive scalar s, 1 in the room at the start and 0 outside, carried
  with T's diffusivity (alphaD = 1/Pr, alphaDt = 1/Prt). The share replaced is 1 − ∫ρs over the
  room / the room's mass at the first step, windowAiring's definition.
- **Monitors, every step:** ∫ρs over the room, its mass and its mass-average T and s, the gross
  mass flow each way through each opening in its frame's plane (`opening1` at x = 0 in the window
  wall, `opening2` at x = 4 m opposite), the room's own air leaving (Σφs), and the scalar's budget
  through the openings (`fluxBudget`, s's own face flux as the scalar transport discretises it).
  Two planes every 1.25 s for the clip: the mid-plane through the windows, and a floor plane
  0.1 m up.
- **The breeze runs' alphaD and alphaDt** are 1.40845 and 1.17647, against the still runs'
  1.4084507 and 1.1764706. The breeze runs' end time was set with foamDictionary, which wrote the
  function objects into their controlDict with six figures. The generator writes them as they
  ran. The difference is 4e-6 of the scalar's diffusivity.

## How the case got here

The still-morning runs came first. With no wind the second window bought nothing (below), as the
orifice formula expects, so the two layouts were solved again in the breeze. The breeze runs are
the still runs' setup with the wall pressures added, the end time changed and the scalar's
diffusivity written to six figures (above).

The first breeze pilots added the wall pressure to the barometric profile,
p = 1e5 exp(−g y/(R T)) + c. A constant carries no weight, so that column is out of balance by
c g/(R T) per metre, and the leeward air in `one`, joined to nothing, sped up by about 1.4e-4 m/s
every second. The profile is now scaled, as above, which is hydrostatic on each side. Run again
for 2.5 s, the same air held a median 2.3e-7 m/s at 1.25 s, against 1.8e-4 m/s with the pressure
added. Both breeze runs were solved from the corrected start.

At 30 s the `two` pilot projected 13 h for 0-300 s on 16 ranks. Its jets, 1.6-2.0 m/s through
the 10-12 mm cells of the reveals, held its step at 0.0062 s, against 0.0147 s in `one`. So the
breeze runs were solved over 0-180 s, by which time `two` has replaced 98% of the room's air.

## Checks

- **The generator against the solved runs.** From a clean copy, `./Allrun --setup-only one` and
  `--setup-only two` wrote the solved runs' meshes (points, faces, owner, neighbour, boundary,
  cell, face and point zones) and every initial field, p and p_rgh with the wall pressures
  included, byte for byte, at 1,052,456 cells each. Their `0.orig`, `constant/`, blockMeshDict,
  topoSet, createPatch and createBaffles dictionaries and fvSolution are byte for byte too.
  controlDict, the function objects, fvSchemes, planesT0, decomposeParDict and setFieldsDict
  differ only in comments and layout: expanded with `foamDictionary -expand -precision 15`, each
  equals the solved run's. The t = 0 planes written from `two`'s setup are its solved run's, byte
  for byte. `--setup-only stillOne` and `stillTwo` wrote the still runs' meshes and initial fields
  byte for byte, and their dictionaries compare the same way.
- **The scalar's budget** closes to 0.14% (`one`), 0.14% (`two`), 0.63% (`stillOne`) and 0.24%
  (`stillTwo`) of what has left the room at the end, and within 0.14%, 0.16%, 0.63% and 0.33% at
  every step from 30 s.
- **Still air outside.** In `one` the air beyond the solid wall, which nothing feeds, held a
  median 2.3e-7 m/s on the mid-plane at 1.25 s.
- **`stillOne` is the same solve as roofWindowAiring's `wall`**: their histories agree to every
  printed figure.
- **All four runs ended cleanly**, each alone on 16 ranks: `one` in 9,832 steps and 8,410 s of
  wall time, `two` in 28,361 steps and 27,264 s, `stillOne` in 14,808 steps and 13,595 s,
  `stillTwo` in 14,413 steps and 13,149 s.

## Results

From `results/summary.txt` and `results/<run>/history.csv`, which `scripts/extract_results.py`
writes from the runs' per-step monitors. The air in is the gross mass flow into the room through
all its openings; room volumes an hour are that flow as 0 °C air (1.275 kg/m³) over 33.6 m³.

### In the breeze, 0-180 s

| | `one` | `two` |
|---|---:|---:|
| **share of the room's own air replaced, at 60 / 120 / 180 s** | 41.5 / 67.6 / **80.3%** | 69.6 / 91.8 / **97.7%** |
| **air in, mean over 0-180 s** | **0.255 kg/s**, 21 room volumes an hour | **0.908 kg/s**, 76 an hour |
| air in, mean over 120-180 s | 0.213 kg/s | 0.929 kg/s |
| the room's mass-average temperature at 180 s | 9.05 °C | 5.71 °C |

**With two windows the breeze drives a through-draught.** Air comes in by the window-wall window
and leaves by the one opposite, and almost nothing goes the other way. Over 0-180 s the windward
window took in 0.908 kg/s and let out 0.019 kg/s, 2% as much; the leeward window let out
0.878 kg/s and took in 4 mg/s. 97% of the air coming in crossed the room and left by the other
window. The room took in 3.6 times the single window's air and replaced 98% of its air in three
minutes, against 80%.

**A single window on the windward wall feels one pressure,** so in this model the breeze does
nothing for it. `one` and `stillOne` agree to a tenth of a point: 41.5% and 41.6% at 60 s, 80.3%
and 80.4% at 180 s, 0.2553 and 0.2549 kg/s over 0-180 s.

**Against the orifice formula.** Two openings of 0.6 m² in series with a discharge coefficient of
0.6 pass 0.799 kg/s of 0 °C air under 3.86 Pa. The run takes in 0.929 kg/s over 120-180 s, 16%
more, which is an effective coefficient of 0.70 through 24 cm reveals. A well-mixed room fed
0.929 kg/s (a time constant of 46 s) would be 72.8%, 92.6% and 98.0% replaced at 60, 120 and
180 s; the run gives 69.6%, 91.8% and 97.7%.

### On a still morning, 0-300 s

| | `stillOne` | `stillTwo` |
|---|---:|---:|
| **share of the room's own air replaced, at 60 / 120 / 300 s** | 41.6 / 67.7 / **92.0%** | 41.4 / 65.0 / **88.1%** |
| **air in, mean over 0-300 s** | **0.235 kg/s**, 19.8 room volumes an hour | **0.226 kg/s**, 19.0 an hour |
| air in, mean over 240-300 s | 0.204 kg/s | 0.193 kg/s |
| the room's mass-average temperature at 300 s | 8.32 °C | 8.14 °C |

**On a still morning the second window bought nothing.** The two half-width windows took in 96% of
the single window's air and replaced 88% of the room's air against 92%. Each worked as a window on
its own, cold air in through its lower half and warm air out through its upper half, at 0.112
and 0.114 kg/s in. Half the difference of their net flows, the air crossing the room from one to
the other, stayed between −1.1% and +2.0% of the air coming in over every 10 s, and was 0.46%
over the last 90 s. Two openings at the same height on opposite walls see no pressure difference
between them unless wind makes one. A single opening swaps air by buoyancy at a rate that goes as
its width (Linden 1999; BS 5925), so two halves add up to about one whole, less a little at their
extra edges.

`stillOne` is windowAiring's wide-open window with the outdoor air at its barometric pressure:
19.8 room volumes an hour and 92% replaced at 300 s, against windowAiring's `open`, 19.8 and 91%.

## What the clip shows, and what it does not

**It shows** the mid-plane through the windows, the single window above and the two windows below,
both in the breeze, from the moment the windows open to 180 s, 9× fast, on one temperature scale,
with parcels of air carried by the solved flow in the plane; the walls, the sashes and the
radiator are drawn over it, and the window wall's outside is labelled as the breeze's side. Each
panel has one number, the share of the room's own air replaced, in whole percent: it ends at 80%
for one window and 98% for two.

**It does not show** the flow across the room's width, the air through the parts of each opening
off the mid-plane, flow rates, heat loss or the still runs.

## What it cannot

- **Gusts and wind at an angle.** The breeze is a steady pressure on each wall, square to the
  window wall. A steady pressure gives a single window none of the exchange that gusts and eddies
  drive (Jiang and Chen 2001: in a steady wind "the mean velocity at the opening could be
  calculated to be zero"), so the single-window run airs the room as in still air. A real single
  window in wind does somewhat better than that, though it does not approach a through-draught.
  Wind along the wall, or at an angle, would weaken the draught.
- **The breeze as wall-averaged pressures** from a correlation for a square low-rise plan, one
  value on each whole wall, not the pressure at the window of a resolved house; one wind speed.
- **Openings at the same height.** Openings at different heights (a roof window, a stairwell)
  make a stack across the room even in still air.
- **One room.** No door instead of the second window, no other rooms, furniture or people; the
  surfaces held at 20 °C, so no heat lost into the walls or stored in them
  ([`airingRadiatorValve`](../airingRadiatorValve) takes those up); no humidity or radiation.
- **The radiator** is 60 W, about a tenth of a real one's, and only the window wall has one.
- **The first minutes,** from a room uniformly at 20 °C: three in the breeze, where `one` has
  not settled (80% and rising) and `two` has (98%), and five on a still morning.
- **One mesh,** URANS with k-omega SST and wall functions, no mesh or time-step study, one
  realization of each run.
- **A stratified room reads high against a well-mixed decay,** as in windowAiring, for the still
  runs and `one`; the inflow is the figure to set beside measured air-change rates.

## Sources

- Illinois State Water Survey, wind rose for Chicago O'Hare (station 94846), December, 1961-1990:
  https://climate.isws.illinois.edu/statecli/Roses/ord_freq_12.pdf
- EnergyPlus Engineering Reference (23.1), "Local Wind Speed Calculation" (ASHRAE's profile, from
  the 2005 ASHRAE Handbook - Fundamentals, ch. 16):
  https://bigladdersoftware.com/epx/docs/23-1/engineering-reference/outside-surface-heat-balance.html
- EnergyPlus Engineering Reference (23.1), AirflowNetwork model, "Wind pressure calculations",
  quoting M. V. Swami and S. Chandra, "Correlations for pressure distribution on buildings and
  calculation of natural-ventilation airflow", ASHRAE Transactions 94 (1988), pp. 243-266:
  https://bigladdersoftware.com/epx/docs/23-1/engineering-reference/airflownetwork-model.html
- Y. Jiang and Q. Chen, "Study of natural ventilation in buildings by large eddy simulation",
  Journal of Wind Engineering and Industrial Aerodynamics 89 (2001):
  https://engineering.purdue.edu/~yanchen/paper/2001-9.pdf
- P. F. Linden, "The fluid mechanics of natural ventilation", Annual Review of Fluid Mechanics 31
  (1999); BS 5925, the single-opening formula.
- Umweltbundesamt, poster "Richtig Lüften" ("Querlüften: Wenn möglich, gegenüberliegende Fenster
  gleichzeitig weit öffnen"):
  https://www.umweltbundesamt.de/system/files/medien/2294/dokumente/poster_richtigluften_uba_a3_cc.pdf

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with NumPy
for `scripts/extract_results.py`. The case uses `../windowAiring/scripts/make_case.py`, so keep
the two cases side by side.

    cd cases/crossVentilation
    ./Allrun two                     # [nProcs], default 16
    ./Allrun one
    ./Allrun stillTwo
    ./Allrun stillOne
    python3 scripts/extract_results.py runs results

`Allrun <run>` writes the run into `runs/<run>/` with `scripts/make_case.py`, then runs the
Allrun written there: blockMesh, subsetMesh to the air, the outer walls as a patch, the sashes as
baffles, the zones, the initial fields, each cell's and outdoor face's pressure (`wind_p.py`),
checkMesh and decomposePar. It then writes the t = 0 planes from the initial fields and solves,
writing the planes every 1.25 s and the fields every 60 s (the last one kept).
`./Allrun --setup-only <run>` stops before the t = 0 planes and the solve, in under a minute.
`./Allclean` removes the runs.

Each run was solved from rest in one go on 16 ranks; the wall times are under Checks. `two` is
the slow one, about 7.6 h for its three minutes. `results/` holds each run's history, every step's
monitors sampled at the plane writes, and the summary; no fields, meshes, planes or logs.

The runs were built by an agent on our own machine from a written brief, and checked and solved
there.
