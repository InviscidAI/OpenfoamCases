# An air conditioner's vane aimed up, against aimed down

A wall-mounted split air conditioner has a vane on its outlet, and the remote sets where it points. In
cooling, Daikin's and Mitsubishi's manuals send the cold air up or level: Daikin's COMFORT AIRFLOW sends it
"in the upward direction while in COOL and DRY operation", and Mitsubishi asks for its highest position in
COOL. Some of the shops that sell the units say the opposite: "Angled downward is usually preferable in
cooling mode" (Boldr), "you point the vents down or straight ahead to push cool air where you need it
most" (Pioneer). Both sides agree that cold air sinks. This case switches the same unit on in the same hot
living room twice, once with the jet aimed 15° up along the ceiling and once 60° down toward the floor, and
asks where the cold air goes in the first three minutes and what reaches a person sitting on the sofa
against the far wall. It is about where the cold goes, not running cost, noise, humidity or the unit's
thermostat.

    ./Allrun up      # the vane up, the jet 15 degrees above horizontal, 0-180 s from switch-on
    ./Allrun down    # the vane down, the jet 60 degrees below horizontal, 0-180 s

**The result.** **The two rooms cool equally; the difference is where the cold goes.** The unit removes
the same 1354 W from each half room throughout, and the rooms' mean temperatures end 0.13 K apart, 24.20 °C
with the vane up and 24.07 °C with it down at 180 s (24.71 against 24.58 °C over 120-180 s, and never more
than 0.14 K apart at any write). Aimed up, the jet stays on the ceiling all the way to the far wall, turns
down the wall behind the sofa, and the room fills with cold from the top. Aimed down, it falls to the floor
about 1.1 m out from the wall and runs along it to the sofa, leaving a cold layer on the floor under warmer
air. **So the seated person's ankles are colder with the vane down and their head is not:** over 120-180 s
the air at the ankles is **24.53 °C up and 22.97 °C down, 1.56 K apart**, with 0.16 against 0.54 m/s of air
across them, and at the head **24.81 against 24.68 °C, 0.13 K apart**. The air at the ankles falls from 30
to 24 °C up and from 30 to 22 °C down in the three minutes. Read [What it cannot](#what-it-cannot) before
any number here: **humidity and condensation are left out**, **the walls are held at 30 °C**, **the cooling
is a fixed sensible load**, and **it is half a room on a symmetry plane**.

The room, the unit and the sofa are new. The way the unit's air is put back into the room at a fixed
cooling is [`fanHeaterVsOilRadiator`](../fanHeaterVsOilRadiator)'s fan heater run in reverse, and the
castellated mesh with the solids cut out on cell faces is [`airPurifierCorner`](../airPurifierCorner)'s
method. [`portableAcHoses`](../portableAcHoses) is the other cooling case.

## The room

x runs from the unit's wall into the room, y up from the floor, z across the room from its centreline;
metres.

| | value | from |
|---|---|---|
| room | 4.64 m from the unit's wall to the far wall, 4.00 m wide, 2.40 m high: about 15 x 13 ft with an 8 ft ceiling, a US living room | ours |
| half model | z = 0 to 2.00 m, a symmetry plane at z = 0 through the middle of the unit and the sofa | ours |
| walls, floor, ceiling | held at 30 °C (303.15 K) from t = 0, the room hot all day; no window, no sun, no radiation | ours |
| sofa | against the far wall facing the unit, 2.0 m long (z -1.00 to 1.00), 0.88 m deep (x 3.76-4.64): a seat 0.44 m high, a back 0.20 m thick to 0.84 m, arms 0.16 m wide to 0.64 m; adiabatic | ours |
| start | the air at rest at 30 °C in isothermal hydrostatic balance, 1e5 Pa at y = 1.2 m | |

**There is no person.** A seated adult's head and ankles are two boxes of air the monitor averages over:
the **head** at x 3.96-4.24, y 1.00-1.20, z 0-0.30 m, and the **ankles** just in front of the seat at x
3.40-3.76, y 0.04-0.16, z 0-0.30 m. A person's heat and shape would add a plume the question does not need.
They are air temperatures and speeds, not skin temperatures. Three more zones are averaged: the occupied
zone (x 0.6-4.0, y 0.1-1.1, z 0-1.4 m), the floor layer (y < 0.1 m) and the ceiling layer (y > 2.2 m).

**Holding the surfaces at 30 °C** is close for three minutes and errs toward more heat into the room: a
plasterboard surface under air 10 K colder at about 3 W/m²K loses under 1 K in 180 s (q = 30 W/m², surface
drop 2q√(t/π)/e with e ≈ 500 W s½/m²K, about 0.9 K). By 180 s the walls give back 1074 W (up) and 1103 W
(down) of the 1354 W.

## The unit

**A Mitsubishi MSZ-GS12NA-U1**, a common US 12,000 BTU/h wall unit, from its submittal sheet:

| | value | from |
|---|---|---|
| size | 798 x 232 x 295 mm (W x D x H), drawn as a box 0.80 x 0.24 x 0.30 m so its edges lie on the mesh; in the half model x 0-0.24, y 2.00-2.30, z 0-0.40 m, its top 0.10 m below the ceiling | the submittal sheet, rounded |
| air | 343 CFM, the top of its wet-coil cooling range (121-144-200-276-343 CFM), as a unit starting in a hot room runs: 0.162 m³/s, **0.09425 kg/s in the half room** at 30 °C | the submittal sheet |
| cooling | 12,000 BTU/h (3.52 kW) at a sensible heat factor of 0.77: **2.71 kW sensible for the whole unit, 1354 W in the half room** | the submittal sheet |
| intake | the grille on its top, x 0.02-0.22 m, z < 0.38 m (0.076 m² in the half room) | ours |

**The cooling is a fixed sensible load.** The air leaves at the intake's mean temperature less
Q/(ṁ cp) = 1354/(0.09425 x 1005) = 14.29 K, by OpenFOAM's `outletMappedUniformInletHeatAddition` with
Q = -1354 W, from t = 0: at 30 °C in, it leaves at about 15.7 °C, a normal supply temperature for a split
unit, and by 180 s at 10.7 °C (up) and 10.3 °C (down) as the room cools. The intake draws 0.09425 kg/s out
(`flowRateOutletVelocity`), and the active slot blows the same mass back in. The unit is taken as running
at its rating from switch-on with its coil already cold; the 23% of its capacity that is moisture removal
is not modelled.

## The vane: up and down

The two runs differ only in the vane. A vane turns the jet without changing the fan's flow, so each run
has the same mass flow, through a slot sized so the jet leaves at nearly the same speed. Neither slot
resolves the vane's blade: the direction is imposed at the slot.

- **up**: the jet leaves **15° above horizontal**, toward the ceiling, through a slot in the unit's front
  face, x = 0.24 m, y 2.00-2.06 m, 0.60 m wide (z < 0.30 m in the half room, 0.018 m²). This is Daikin's
  COMFORT AIRFLOW in COOL and Mitsubishi's position (1), of which its manual notes "Air blows out upper than
  position (1)".
- **down**: the jet leaves **60° below horizontal**, toward the floor in front of the unit, through a slot
  in the unit's underside at its front edge, y = 2.00 m, x 0.16-0.24 m, 0.52 m wide (z < 0.26 m, 0.0208
  m²). This is the vane at its lowest cooling setting; Daikin's sketch of its flaps shows the cooling range
  ending about this steep, though it gives the angles from the closed flap, not from the horizontal.

The jet is a `codedFixedValue` that points the velocity along the vane and scales it every evaluation to
0.09425 kg/s at the patch's own density, about 4.5 m/s (up) and 4.3 m/s (down) at the start. Both slots are
in the one mesh; in each run the other slot is an adiabatic no-slip wall. The flow-weighted direction of
the air over the first 4 cm outside the slot is **15.4-16.0° up** and **60.5-60.6° down** over the runs.

## The model

`buoyantPimpleFoam` (OpenFOAM v2512), compressible air as a perfect gas (Cp 1005 J/kg K, molar mass
28.96, μ 1.82e-5 Pa s, Pr 0.71), k-ω SST with `buoyancyTurbSource` and wall functions (`kLowReWallFunction`,
`omegaWallFunction`, `nutkWallFunction`, `alphatJayatillekeWallFunction`); the jet at 5% intensity and a
1 cm mixing length. Euler in time, adaptive steps at Courant 1 (maxDeltaT 0.05 s; about 3.3 ms throughout),
limitedLinearV for U and limitedLinear for h, k and ω, two outer and two pressure correctors, p_rgh by GAMG
to 1e-7 with the final solve capped at 100 iterations (no step reached it), the pressure reference in the
middle of the room at (2.32, 1.20, 1.00) m with pRefValue 1e5 Pa. No radiation, no solids.

**The mesh** (`template/mesh/system`, `scripts/make_mesh.py`, `scripts/unit_patches.py`): a background of
8 cm cubes (blockMesh, 58 x 30 x 25), refined by snappyHexMesh, castellated only, without snapping or
layers: 2 cm round the unit (its surface and a box x < 0.56, y > 1.76, z < 0.56 m), 4 cm along both jets'
paths (a layer under the ceiling, y > 2.0; the region in front of the unit, x < 1.92, z < 0.8; the floor
layer, y < 0.24; and round the sofa, x > 3.2, y < 1.36, z < 1.2) and on the sofa, 8 cm elsewhere, two
cells between levels. The unit and the sofa are each one closed STL, the union of their boxes, written by
`make_mesh.py` on the mesh's own faces, so they are cut out exactly. snappyHexMesh leaves the unit as one
patch; `unit_patches.py` moves its faces into `intake`, `slotUp` and `slotDown` by face centre and checks
their areas and the sofa's (2.4592 m², exposed) to 1%. **198,832 hexahedral cells**, an air volume of
21.75424 m³ (the half room less the unit's 0.0288 and the sofa's 0.4890 m³); `checkMesh` OK,
non-orthogonality at most 25.2°, skewness at most 0.33, aspect ratio 1. One mesh, no mesh study.

**The monitors** (`scripts/monitor.C`, a coded function object, one row every 0.375 s into
`postProcessing/metrics/metrics.csv`): the slot's and the intake's mass flows and temperatures, the jet's
direction, the air's mass and internal energy (cv/R)∫p dV, its coldest and warmest cell and where they are,
the mean temperature and mean speed |U| of the six zones, and the heat into the air through each wall
(`wallHeatFlux`). And (`planes`) the section, which is the symmetry plane z = 0, and plans at ankle height
(0.10 m), seated head height (1.10 m) and under the ceiling (2.30 m), each with T and U, every 0.375 s from
t = 0, 481 a run.

## Results

`results/summary.txt`, `results/zones.csv` and `results/<run>/history.csv` (every 1.5 s), from
`scripts/extract_results.py`. Means over an interval are time-weighted.

| °C | 30 s | 60 s | 90 s | 120 s | 150 s | 180 s | 120-180 s |
|---|---:|---:|---:|---:|---:|---:|---:|
| room, up | 28.32 | 27.08 | 26.10 | 25.32 | 24.68 | 24.20 | 24.71 |
| room, down | 28.28 | 26.98 | 25.99 | 25.18 | 24.56 | 24.07 | 24.58 |
| head, up | 28.67 | 26.75 | 26.28 | 25.53 | 24.85 | 24.24 | **24.81** |
| head, down | 28.22 | 27.21 | 26.23 | 25.30 | 24.65 | 24.15 | **24.68** |
| ankles, up | 27.72 | 26.50 | 25.70 | 25.01 | 24.38 | 24.16 | **24.53** |
| ankles, down | 27.06 | 25.54 | 24.47 | 23.61 | 22.92 | 22.41 | **22.97** |

| over 120-180 s | up | down |
|---|---:|---:|
| air speed at the head, m/s | 0.104 | 0.122 |
| air speed at the ankles, m/s | 0.157 | 0.545 |
| floor layer, y < 0.1 m, °C | 24.82 | 23.11 |
| ceiling layer, y > 2.2 m, °C | 24.52 | 25.56 |
| occupied zone, °C | 24.33 | 24.05 |

**Where the cold goes.** The walls' heat into the air shows it: at 180 s the ceiling gives 414 W to the up
room's air and 104 W to the down room's, the floor 204 against 578 W, and the far wall behind the sofa 179
against 63 W. In the up room the jet's cold core runs along the ceiling and reaches the far wall about 6 s after
switch-on, and from then to the end it stays on the ceiling to x = 4.50-4.62 m (a diagnostic on the up
run's section planes, the coldest cell across the height in 4 cm bins). In the down room the floor layer is 1.7 K colder than the up room's over the last
minute and its ceiling layer 1.0 K warmer. The section planes differ by more than 1 K over 52% of the
section at 9 s, 45% at 30 s and 60% at 180 s, with an rms difference of 2.4-2.8 K away from the unit.

**The number at the ankles.** The clip's number is the ankles' air temperature rounded to the degree. Both
rooms start at 30 °C; the up room ends at 24 (24.16 °C) and the down room at 22 (22.41 °C). At no write is
the down room's rounded number above the up room's.

**Checks.** The slot and the intake carry 0.09425 kg/s, to within 5e-7 of it in both runs, and the
cooling holds at 1354.0 W throughout both runs. The air's heat budget over 10-180 s, the change in its
internal energy against the walls' heat less the cooling, closes to **0.038%** (up) and **0.0067%**
(down) of the cooling. The air's mass reads 24.9947848130 kg at the first and last write of both runs. No
air is colder than the supply by more than 0.03 K or warmer than 30 °C by more than 0.007 K. No final
pressure solve reached its 100-iteration cap.

## What the clip shows, and what it does not

The clip shows the section, the symmetry plane through the middle of the unit and the sofa, the whole room
in both panels on every frame, stacked, "aimed up" above and "aimed down" below, **from switch-on to 3:00
of the solve** at nine times speed in 20 s, one frame a plane write. It is coloured by air temperature on a
cool 16-30 °C scale, with moving air parcels, a seated figure on the sofa, a clock and the question "Air
conditioner: cold air up or down?". Each panel carries one rounded number, the air at the seated person's
ankles, falling from 30 to 24 °C aimed up and from 30 to 22 °C aimed down.

- **The number is the ankles, not the head.** The head differs by only 0.13 K over the last minute, too
  little to show as a rounded number or to present as a difference. A viewer who reads "aimed down is
  colder" off the numbers is reading the feet; the clip does not say that either setting cools the room
  faster or the person's head more.
- The unit, its vane, the sofa and the seated figure are drawn; the figure is not in the model. The parcels
  are moved through the planes' velocity after the solve; they are not solved particles. Only the jet's core
  near the slot is colder than the scale's 16 °C.

## What it cannot

- **The two rooms cool equally.** Both remove the same 1354 W, and their means stay within 0.14 K of each
  other at every write (0.13 K at 180 s). The case compares where the cold goes, not how fast the room cools,
  and says nothing about a thermostat that would cut the unit back sooner in one room than the other.
- **The ankles, not the head.** The 1.56 K between the rooms over 120-180 s is at the ankles (and 30 to 24
  °C against 30 to 22 °C by 180 s); at the head it is 0.13 K, which on one mesh with no mesh or time-step
  study is not a robust difference, and is not claimed as one.
- **Humidity and condensation are left out.** The model has no moisture and removes only the unit's
  sensible cooling. Half of the manuals' reason for keeping the vane up in cooling is condensation: Daikin's
  European manual moves flaps left pointing down on their own after about an hour "in order to prevent dew
  condensation", and Mitsubishi's returns its vane to position (1) after about an hour. The case says
  nothing for or against that reason.
- **The walls are held at 30 °C**, with no sun, no window and no radiation. That is close for three minutes
  ([The room](#the-room)) and errs toward more heat into the room. Nothing else in the room, furniture,
  people or electronics, adds heat; the sofa is adiabatic.
- **The cooling is a fixed sensible load**: 2.71 kW for the whole unit, 1354 W in each half room, at the top
  fan speed from t = 0, the coil already cold. A real unit takes a minute or two to bring its coil down,
  and its compressor modulates; neither is modelled.
- **It is a half model on a symmetry plane**, z = 0 through the middle of the unit and the sofa. The jets
  cannot wander sideways, which a real jet does slowly, and the clip's section is that plane, which keeps
  the jet's core.
- **The vane is a fixed direction at a slot**, 15° up or 60° down, not a maker's vane: no blade, no swing,
  no auto mode. The unit is a box with Mitsubishi's dimensions, not its shape.
- **One room, one layout, three minutes.** The sofa is on the far wall facing the unit. A sofa under the
  unit, or a bed beside it, could change which setting reaches the person first, and the rooms are still
  cooling at 180 s.
- **RANS, one mesh.** k-ω SST on a stepped castellated mesh of 198,832 cells, 2-8 cm, with wall functions.
  No mesh or time-step study.
- **The draught's chill on skin** is not modelled: moving air feels colder than still air at the same
  temperature, and the case gives air temperature and speed only.

## Sources

- Mitsubishi MSZ-GS12NA-U1 / MUZ-GS12NA-U1 submittal sheet, as hosted by Gemaire
  (resource.gemaire.com/is/content/Watscocom/Gemaire/mitsubishi_muz-gs12na-u1_article_1604089111890477_en_subs.pdf),
  read 11 Nov 2026: 12,000 BTU/h rated, sensible heat factor 0.77, wet-coil cooling airflow 121-144-200-276-343
  CFM, the indoor unit 798 x 232 x 295 mm.
- Mitsubishi MSZ-A09/12/15/17NA operating instructions (inspectapedia.com/aircond/MItsubishi-Operating-Instructions-MSZ-A09-12-15-17NA.pdf):
  "Use position (1) in the COOL or DRY mode and use positions (2) to (4) in the HEAT mode"; "Air blows out
  upper than position (1)"; the vane moved back to position (1) after about an hour.
- Daikin FTXV30AVJU9 operation manual (US) (gotductless.com/cdn/shop/files/FTXV30AVJU9_Operation_Manual.pdf):
  COMFORT AIRFLOW, "The flow of air will be in the upward direction while in COOL and DRY operation".
  Daikin FTXJ20-50MW/MS operation manual (EU), pp. 14-15 (daikin.fr): the flaps' angles in cooling, and the
  flaps that start moving after about an hour if left down in COOL or DRY "in order to prevent dew
  condensation".
- Boldr, "Mini split swing setting" (shopboldr.com/blogs/news/mini-split-swing-setting): "Angled downward is
  usually preferable in cooling mode. Cold air discharged horizontally tends to hug the ceiling".
- Pioneer Mini Split, "Why airflow direction settings matter for your mini split" (pioneerminisplit.com):
  "During cooling, you point the vents down or straight ahead to push cool air where you need it most."
- The fixed cooling at the outlet: [`fanHeaterVsOilRadiator`](../fanHeaterVsOilRadiator)'s fan heater,
  reversed. The castellated room mesh: [`airPurifierCorner`](../airPurifierCorner).
- The question came from a viewer, who asked in a message what the best position or angle is for an air
  conditioner's air.

## How the case got here

**The solve.** On 11 Nov 2026 both runs were set up as here, tested for 200 steps each on the real mesh
(mass flows to 1e-7 kg/s, the supply 14.29 K below the intake, the jets at 15.9° and 60.5°), and launched
side by side on our own machine from rest, 8 ranks each, one physical core a rank.

**Both runs were stopped near 30 s.** The script running the pair compared the two runs' section planes at
30 s, failed because the two planes listed their faces in different orders, and stopped both runs: up at
35.68 s and down at 30.02 s. Both were continued from their 30 s fields.

**A first continuation was discarded.** It restarted with the pressure reference at its from-rest 1e5 Pa.
On start-up `buoyantPimpleFoam` shifts p so that the reference cell reads pRefValue; in this closed room,
cooling, that cell held 99,446 Pa (up) and 99,432 Pa (down) at 30 s, so p rose by about 554 and 568 Pa,
and the energy equation's dp/dt term took V·Δp = 12.05 and 12.36 kJ out of the room in one step: the room's
mean fell 0.67 K in a single write, against the original segment. None of it is in this case.

**The continuation used.** On 13 Nov both runs were continued again from the same 30 s fields with
`PIMPLE { pRefValue <p at the reference cell in the run's 30 s write>; }`: 99,446.093 Pa (up) and 99,431.979
Pa (down), at global cell 20637 on the retained decomposition. `foamDictionary` wrote them into `fvSolution`
rounded to six digits, as 99446.1 and 99432, so the restarts held 0.007 and 0.021 Pa off, which is
V·Δp = 0.15 and 0.46 J. The checks: the first p_rgh initial residual after the restart is 0.0071 (up) and
0.0170 (down), against 0.99 on the discarded restart; the energy no budget term accounts for over
30-30.375 s is 0.22 J and -0.13 J, against 12 kJ; and the up run's restarted rows from 30.375 to 35.625 s,
which its first segment had also solved, match that segment's in every monitor column to 7.1e-5 relative,
the room's mean to 6e-6 K. Nothing else was changed. The monitors are the first segment's rows to 30 s and
the continuation's after it, with the continuation's clock column offset by the first segment's run time.
The runs took 53,445 (up) and 54,700 (down) steps, about 4.1 h and 4.8 h of wall time on 8 ranks each.

**A straight run needs none of this.** `Allrun` runs both from rest to 180 s in one go with the template's
pRefValue 1e5, which is right for a start from rest: at t = 0 the hydrostatic field already holds about 1e5
Pa at the reference point, so the start-up shift is under 1 Pa and no restart follows. A straight run
differs from the solved 0-30 s + 30-180 s pair only by the 0.15 and 0.46 J of the rounded pRefValue at 30
s and by whatever the solver sets up afresh on a restart rather than carrying on; the up run's overlap
above bounds that at 7e-5 of any monitor. **A rebuilt run will not repeat the solved runs bit for bit in
any case**, because scotch gives a different 8-rank decomposition on every call on our machine (three
calls gave 24,606, 24,608 and 24,719 cells on rank 0, against the solved runs' 25,052), so parallel sums
round differently; in a turbulent buoyant flow that round-off grows, and the zone means of a rebuilt run
should be expected to agree with these to a few hundredths of a kelvin, not to the last digit. No rebuilt
run was solved.

**The restart of a closed room** must set pRefValue to the pressure at the reference cell at the restart
time; the template's `fvSolution` has the usual 1e5, right for a start from rest.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with NumPy.

    cd cases/acLouvreAngle
    ./Allrun up                  # [nProcs], default 8; builds the mesh first
    ./Allrun down                # default 8; start it once runs/mesh/ is built
    python3 scripts/extract_results.py runs results

The first `Allrun` builds the shared mesh in `runs/mesh/`: `scripts/make_mesh.py` writes the meshing
dictionaries (`template/mesh/system/`) and the unit's and sofa's STLs, then blockMesh, a serial
snappyHexMesh of a few seconds, `scripts/unit_patches.py` (the unit's ports, and the cell centres for the
hydrostatic start) and checkMesh. Then `scripts/make_case.py` writes `runs/<run>/`: the mesh with its unused
slot made a wall, `0/`, `constant/` and `system/` from `template/` and `config/case.json`, and the monitor
from `scripts/monitor.C`. `Allrun` writes the reference cells' face set (topoSet), decomposes by scotch with
those cells kept on one rank, writes the t = 0 planes, solves from 0 to 180 s, and once both runs have
solved writes `results/`. The two runs differ in the active slot's boundary conditions (`0/`), the unused
slot's patch type and the monitor's slot. `./Allrun --setup-only <run> [nProcs]` stops before the solve;
`./Allclean` removes the runs. The solved runs took about 4.1 h (up) and 4.8 h (down) on 8 ranks each.

Each run writes 481 section and 3 x 481 plan planes (VTK, about 0.75 GB a run, 0.36 GB gzipped),
the fields every 30 s and a monitor file of about 0.3 MB. `results/` holds the summary, the zones and each
run's history every 1.5 s; no fields, meshes, planes or logs.

The case was set up and solved by an agent on our own machine and checked by us. The files in `results/`
are what `scripts/extract_results.py` wrote from the solved runs' monitors.

Checked from a clean copy of this folder on 13 Nov 2026: `make_mesh.py`, blockMesh, snappyHexMesh and
`unit_patches.py` rebuild the solved mesh byte for byte (the two STLs, and `points`, `faces`, `owner`,
`neighbour`, `boundary` and snappyHexMesh's level and zone files), and `checkMesh` gives the solved mesh's
report line for line: Mesh OK at 198,832 cells, non-orthogonality 25.2394° at most, skewness 0.333333.
`make_case.py` writes both runs' `0/` and `constant/polyMesh` byte for byte, their `constant/` and
`system/` byte for byte as launched from rest (the solved runs' `controlDict` and `fvSolution` were changed
afterwards only for the restart, above), and `system/functions` but for the clock offset the continuation
added; the t = 0 planes are the solved runs' byte for byte. The decomposition is not (above). No solve was
run from the clean copy. `scripts/extract_results.py` on the solved runs' monitors gives the study's own
figures: the 120-180 s head and ankle means (24.814/24.682 and 24.529/22.974 °C), the room means at 180 s,
the walls' heat and the 0.0376% and 0.0067% heat budgets.
