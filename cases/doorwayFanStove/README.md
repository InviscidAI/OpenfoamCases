# A fan in the doorway to move a wood stove's heat into the next room: high or low

A wood stove heats its own room and the room next door stays cold. A fan in the doorway is the usual fix,
and owners argue about where it goes. On hearth.com most say put it on the floor and blow the cold room's
air at the stove: "many of us have better luck moving the cooler denser air near the floor towards the
stove/stove room", "I've tried both, and moving the cold air works better". Others mount a fan high in the
doorway and blow the warm air out ("I use 1 to move the hot air to the cold room. It helps the convection
loop"), which is what the corner doorway fans sold for the job do: they are "shaped to fit in upper corner
of the door". This case puts the same box fan in the same doorway twice, once in the top of the doorway
blowing the stove room's warm air into the cold room and once on the floor blowing the cold room's air
towards the stove, with the stove giving the same fixed heat in both, and asks how the cold room warms in
the first three minutes after the door is opened and the fan switched on, and how warm the air is at a
seated person's head. It is about where the heat goes, not fuel, the stove's draught or the fan's noise.

    ./Allrun high    # the fan in the top of the doorway, warm air out, 0-190 s from the fan coming on
    ./Allrun low     # the fan on the floor in the doorway, cold air in, 0-190 s

**The result.** **The high fan carries more heat through the doorway; the low fan leaves the next room
warmer.** Both stoves give the same 2.5 kW to the half house throughout. Over 160-190 s the high fan drives
**0.30 m³/s each way through the doorway against 0.23 m³/s** with the fan low, and carries a net **1.87 kW
into the next room against 1.41 kW**. But the high jet runs into the cold room under its ceiling, turns down
its far wall and stirs the whole room (0.61 against 0.16 m/s of mean air speed), and the walls, floor and
ceiling there are held at 14 °C, so the stirred air gives them **1.76 kW against 1.14 kW**. With the fan
low the warm air comes in over the top of the doorway without being pushed and fills the room from the
ceiling down. So over 160-190 s **the air at a seated person's head in the next room is 20.4 °C with the fan
high and 23.1 °C with it low**, 2.7 K apart; the high fan leaves that room mixed, floor to ceiling within
0.4 K at 190 s, and the low fan leaves a layer 4.5 K warmer under the ceiling than at the floor. Read
[What it cannot](#what-it-cannot) before any number here: **the walls are held at 14 °C**, and real ones
would warm and narrow the gap; **there is no radiation**; **the stove's output is fixed**; and **it is half a
house on a symmetry plane**.

The house, the stove and the doorway are new. The fan as a zone of held mean velocity is
[`tallRoomFan`](../tallRoomFan)'s, the castellated room mesh with the solids cut out on cell faces is
[`airPurifierCorner`](../airPurifierCorner)'s and [`acLouvreAngle`](../acLouvreAngle)'s method, and the
monitor follows `acLouvreAngle`'s. [`doorGapExcluder`](../doorGapExcluder) is the other case with air moving
between two rooms.

## The house

x runs from the stove room's end wall through the doorway into the cold room, y up from the floor, z across
the house from the doorway's centreline; metres. Every edge lies on the 4 cm grid of the refined mesh, so
the sizes are rounded to it.

| | value | from |
|---|---|---|
| two rooms | side by side, each 4.00 m along x, 4.00 m across (z) and 2.40 m high, about 13 x 13 ft with an 8 ft ceiling: the stove room x 0-4.00, the cold room x 4.08-8.08 | ours |
| partition | 0.08 m thick, x 4.00-4.08, to the ceiling | ours |
| doorway | 0.88 m wide (z -0.44 to 0.44) and 2.04 m high, a US 36 x 80 in interior door opening rounded to the grid; the door is open flat against the wall and not modelled | ours |
| half model | z = 0 to 2.00 m, a symmetry plane at z = 0 through the middle of the doorway, the fan and the stove | ours |
| walls, floor, ceiling | held at each room's starting temperature from t = 0: 24 °C in the stove room, 14 °C in the cold room, the partition's two faces with their rooms; the doorway's jambs and lintel adiabatic | ours |
| start | the air at rest, 24 °C in the stove room and 14 °C in the cold room (split at x = 4.04 m, the middle of the doorway's depth), in hydrostatic balance with 1e5 Pa at y = 1.02 m: the door had been shut while the stove burned. At t = 0 the door is open and the fan is on | |

**There is no person.** A seated adult's head and ankles in the cold room are two boxes of air the monitor
averages over, 2.3-2.7 m from the partition: the **head** at x 6.40-6.80, y 1.00-1.20, z 0-0.32 m, and the
**ankles** at the same x and z, y 0.04-0.16 m. They are air temperatures and speeds, not skin temperatures.
Each room's air is also averaged whole, in the seated zone (y 0.1-1.1 m), the floor layer (y < 0.1 m) and
the ceiling layer (y > 2.2 m).

**Holding the walls at 14 °C** keeps the cold room's surfaces cold, as real ones stay over minutes, but errs
towards more heat out of its air, and more so in the stirred room ([What it cannot](#what-it-cannot)).

## The stove

**A medium steel wood stove**, a box x 0.60-1.12 m, y 0.12-0.84 m, z -0.28 to 0.28 m (0.52 m deep, 0.56 m
wide, 0.72 m tall, raised 0.12 m off the floor with no legs modelled), 0.60 m from the stove room's end wall
on the centreline, with a flue 0.16 x 0.16 m from its top to the ceiling. Both are boxes of our own; no
maker's geometry is used.

**Its heat output is fixed**, the same in both runs: **5 kW for the whole stove**, the declared nominal
output on wood of Charlton & Jenrick's Go Eco 5, a small steel-firebox stove tested to EN 13240 (its
installation and operating instructions, issue 08 09/23, p. 13: "Declared nominal output: (kW) 5"). Halved
for the half house, **2.5 kW: 2000 W on the stove's faces and 500 W on the flue's**, each a uniform heat flux
(`externalWallHeatFluxTemperature` in flux mode, 1893.94 W/m² over the stove's 1.056 m² and 1001.60 W/m²
over the flue's 0.4992 m² in the half model). The surface temperature follows from the air. With no
radiation all 2.5 kW leave by convection where a real stove radiates about half, so on this mesh the stove's
faces run far hotter than steel: over 160-190 s their area mean is about 1,200 °C with the fan high and
380 °C with it low (the flue's 490 and 210 °C). These are numerical values on 4 cm wall cells and say
nothing about a real stove's surface; the heat into the air is what the case holds fixed.

## The fan: high and low

**One 20-inch box fan, a Lasko 3733, on its lowest speed, 1250 CFM** (0.590 m³/s; Lasko's support answer on
the product's Best Buy page, which gives 1800 CFM on high), **0.295 m³/s through the half fan**. Owners stress
running it slow ("I did find a box fan was too much air too fast"), so the lowest speed is the fair setting
for both camps. It is a zone of cells in the doorway's plane, the partition's thickness (x 4.00-4.08 m),
0.52 m high and 0.26 m across in the half model, with `meanVelocityForce` holding the zone's mean velocity
along x. The two runs differ only in which zone is active and which way it blows:

- **high**: the zone `fanHigh`, y 1.52-2.04 m, in the top of the doorway, blowing from the stove room into
  the cold room, Ubar = +2.0840 m/s.
- **low**: the zone `fanLow`, y 0.04-0.56 m, on the floor in the doorway, blowing from the cold room into the
  stove room, Ubar = -2.0271 m/s.

The held velocities were set in two 0-10 s pilots of each run on this mesh so that 0.295 m³/s crosses the
zone's downstream face (by face flux, 0.2949 and 0.2947 m³/s over 5-10 s), and frozen. Over 160-190 s of the
runs here the downstream face carries **0.2988 m³/s (high) and 0.2955 m³/s (low)**. The zone has no casing,
no blades and no swirl: air reaches it through its top, bottom and sides as well as its upstream face, so its
upstream face carries less than its downstream face.

## The model

`buoyantPimpleFoam` (OpenFOAM v2512), compressible air as a perfect gas (Cp 1005 J/kg K, molar mass 28.96,
μ 1.82e-5 Pa s, Pr 0.71), k-ω SST with `buoyancyTurbSource` and wall functions (`kLowReWallFunction`,
`omegaWallFunction`, `nutkWallFunction`, `alphatJayatillekeWallFunction`). Euler in time, adaptive steps at
Courant 1 (maxDeltaT 0.05 s; 3.6-4.1 ms at the end), limitedLinearV for U and limitedLinear for h, k and ω,
two outer and two pressure correctors, p_rgh by GAMG to 1e-7 with the final solve capped at 100 iterations
(no step reached it), the pressure reference in the cold room at (6.00, 1.70, 1.80) m with pRefValue
99,991.909 Pa, the starting hydrostatic pressure there. No radiation, no solids: the walls are held
temperatures and the stove and flue fixed fluxes.

**The mesh** (`template/mesh/system`, `scripts/make_mesh.py`, `scripts/house_patches.py`): a background of
8 cm cubes (blockMesh, 101 x 30 x 25), refined by snappyHexMesh, castellated only, without snapping or
layers: 2 cm round the doorway and the fan (x 3.84-4.24, z < 0.56 m, floor to ceiling), 4 cm on the solids,
round the stove and its plume (x 0.40-1.36, z < 0.48 m), through the doorway's depth (x 3.52-4.56,
z < 0.72 m), under both ceilings (y > 2.16 m) and along both floors (y < 0.16 m), 8 cm elsewhere, two cells
between levels. The partition, the stove and the flue are one closed STL, the union of their boxes, written
by `make_mesh.py` on the mesh's own faces, so they are cut out exactly. `house_patches.py` sorts the
boundary faces by face centre into `symmetry`, `stove`, `flue`, `stoveRoomWalls`, `coldRoomWalls` and
`doorwayReveal`, writes the two fan zones and the oriented face zones the monitor sums the flux over, and
checks the stove's (1.056 m²), the flue's (0.4992 m²), the doorway's (0.8976 m²) and each fan face's
(0.1352 m²) areas to 1%. **254,506 hexahedral cells**, an air volume of 38.347 m³; `checkMesh` OK,
non-orthogonality at most 25.2°, skewness at most 0.33, aspect ratio 1. One mesh, no mesh study.

**The monitors** (`scripts/monitor.C`, a coded function object, one row every 0.625 s into
`postProcessing/metrics/metrics.csv`): through each fan face, the whole doorway (at x = 4.08 m) and its
halves above and below 1.02 m, the gross flow each way in kg/s and m³/s and the enthalpy cp (T - 14 °C)
carried each way; the air's mass and internal energy (cv/R)∫p dV; its coldest and warmest cell and where
they are; the mean temperature and mean speed |U| of the ten zones (each room whole, seated, floor and
ceiling, and the head and ankles); and the heat into the air through each wall patch (`wallHeatFlux`). Also
the stove's and flue's face temperature (`surfaceFieldValue`, area mean and maximum), and (`planes`) the
section, which is the symmetry plane z = 0, and plans at ankle height (0.10 m), seated head height (1.10 m)
and under the ceiling (2.30 m), each with T and U, every 0.625 s from t = 0, 305 a run.

## Results

`results/summary.txt`, `results/zones.csv` and `results/<run>/history.csv` (every 2.5 s), from
`scripts/extract_results.py`. Means over an interval are time-weighted. All flows and powers are for the
half house; double them for the whole.

| the cold room, °C | 30 s | 60 s | 90 s | 120 s | 150 s | 190 s | 160-190 s |
|---|---:|---:|---:|---:|---:|---:|---:|
| head, high | 16.24 | 17.87 | 18.82 | 19.66 | 19.96 | 20.63 | **20.45** |
| head, low | 17.55 | 20.27 | 21.54 | 22.54 | 22.59 | 23.14 | **23.13** |
| room mean, high | 16.89 | 18.39 | 19.36 | 20.03 | 20.51 | 20.87 | 20.76 |
| room mean, low | 17.47 | 20.01 | 21.69 | 22.76 | 23.57 | 24.35 | 24.07 |
| seated zone, high | 16.75 | 18.37 | 19.34 | 20.03 | 20.49 | 20.95 | 20.77 |
| seated zone, low | 15.37 | 18.52 | 20.87 | 21.95 | 22.74 | 23.49 | 23.23 |
| floor layer, high | 17.21 | 18.40 | 19.31 | 19.96 | 20.36 | 20.62 | 20.56 |
| floor layer, low | 14.53 | 15.08 | 16.45 | 18.76 | 20.21 | 21.30 | 20.81 |
| ceiling layer, high | 17.51 | 18.72 | 19.51 | 20.09 | 20.63 | 21.00 | 20.83 |
| ceiling layer, low | 21.07 | 22.67 | 23.37 | 24.43 | 25.13 | 25.83 | 25.58 |

| over 160-190 s | high | low |
|---|---:|---:|
| stove + flue, W | 2000.0 + 500.0 | 2000.0 + 500.0 |
| fan's downstream face, m³/s | 0.2988 | 0.2955 |
| doorway, into the cold room, m³/s | 0.2989 | 0.2344 |
| doorway, into the stove room, m³/s | 0.2934 | 0.2305 |
| net heat through the doorway into the cold room, W | **1,867** | **1,414** |
| the cold room's walls, floor and ceiling, from the air, W | **1,761** | **1,136** |
| the stove room's, from the air, W | 370 | 756 |
| mean air speed in the cold room, m/s | 0.61 | 0.16 |
| air speed at the head, m/s | 0.13 | 0.06 |
| ankles, °C | 21.45 | 20.43 |

**Where the heat goes.** With the fan high the doorway's whole upper half runs into the cold room (0.299 m³/s)
and the return comes back mostly through its lower half (0.187 m³/s) and partly over the fan (0.106 m³/s):
the jet takes the stove room's warm upper air and leaves along the cold room's ceiling. With the fan low the
fan pushes 0.22 m³/s of the cold room's floor air through the lower half into the stove room, and the warm
air goes back over the top of the doorway (0.17 m³/s), more slowly and with no jet behind it. Over 0-190 s
the high fan carries 383 kJ net into the cold room and the low fan 337 kJ; the cold room's walls take 261
and 156 kJ of it. Of the 450 kJ the stove and flue give over 10-190 s, the air of the whole house keeps 139
kJ with the fan high and 235 kJ with it low: the stirred rooms lose more to their held walls. At 190 s the
high run's cold room is mixed, 0.38 K from floor to ceiling layer, and the low run's has 4.53 K between them.

**The number at the head.** The clip's number is the head's air temperature rounded to the degree. Both
start at 14 °C; high ends at 21 (20.63 °C) and low at 23 (23.14 °C). Low's rounded number is above high's at
265 of the 304 writes and below it at 13, from 14 to 22 s, when the high jet has reached the far wall and
the low run's warm layer has not yet come down to head height.

**Checks.** The stove gives 1996-2005 W and the flue 499-501 W at every write from 10 s in both runs,
474.2 kJ each over 0-190 s. The air's heat budget over 10-190 s, the change in its internal energy against
the stove's, the flue's and the walls' heat, closes to **-0.012%** (high) and **-0.007%** (low) of the
stove's heat. The air's mass reads 45.73321953 kg at the first and last row of both runs. No final pressure
solve reached its 100-iteration cap. The coldest air is 13.57 °C (high) and 13.74 °C (low), up to 0.44 K
below the cold room's 14 °C, an undershoot in the first seconds; the warmest, 275 °C and 139 °C, is the air
in the cells on the stove's faces.

## What the clip shows, and what it does not

The clip shows the section, the symmetry plane through the doorway, the fan and the stove, with both rooms
whole in both panels on every frame, stacked, "high: warm air out" above and "low: cold air in" below,
**from the fan coming on to 3:10 of the solve** at 9.5 times speed in 20 s, a frame every 0.396 s of flow.
It is coloured by air temperature on a 14-30 °C scale, with moving air parcels, a clock and the question
"Wood stove heat: fan high or low?". Each panel carries one rounded number, the air at the seated person's
head in the cold room, rising from 14 to 21 °C with the fan high and from 14 to 23 °C with it low.

- **The number is the head, not the heat moved.** The high fan moves more heat through the doorway; its room
  is cooler at the head because more of that heat goes into the walls. A viewer reading "low is better" off
  the numbers is reading the air at one seated head over three minutes against walls that do not warm.
- The stove, the flue, the partition, the fan and the seated figure are drawn; the figure is not in the
  model. Near the stove and flue the air is far above the scale's 30 °C; for the picture the temperatures
  are capped at 30 °C before a 2 cm blur, so the stove's hot faces do not bleed a halo into the air. The cap
  changes no number. The parcels are moved through the planes' velocity after the solve; they are not
  solved particles.

## What it cannot

- **The walls are held at 14 °C**, and they take more heat from the stirred room: 1.76 kW with the fan high
  against 1.14 kW with it low over 160-190 s. Real walls warm under that heat. A rough estimate for
  plasterboard (effusivity about 450 J/(m² K s^½), about 35 m² of the cold room's surfaces in the half house)
  gives **a 1-2 K rise at the surface over three minutes**, which would take something like a quarter off
  the high run's loss and less off the low's, and **narrow the 2.7 K gap**, probably not close it. It has
  not been solved; treat it as an estimate.
- **No radiation**, so all of the stove's output leaves by convection. A real stove radiates about half of
  it to the stove room's walls and furniture, which over minutes barely reach the air; the case puts it all
  into the air at the stove instead, the same in both runs.
- **The stove's output is fixed** at 5 kW for the whole stove, the declared nominal output of Charlton &
  Jenrick's Go Eco 5 (the maker's installation and operating instructions, issue 08 09/23, p. 13), 2.5 kW
  in the half house, 80% on the stove and 20% on the flue. A real stove's output follows its fire, and its
  surface temperature is set by the steel, not by the air; here the surface temperature is whatever the
  fixed flux needs.
- **It is half a house on a symmetry plane**, z = 0 through the middle of the doorway, the fan and the
  stove. The jets cannot wander sideways, as real ones do slowly, and the clip's section is that plane.
- **The fan is a Lasko 3733 on low, 1250 CFM**, as a zone of held mean velocity: no blades, no casing, no
  swirl. It draws air through its edges as well as its face. One fan speed, one fan; the thread's "one high
  up one low" is not tried.
- **The 10 h cap ended it at 190 s.** The runs were planned to 300 s, and both rooms are still warming at
  190 s, the low run's cold room faster; the case says nothing about the evening after.
- **One house, one door, one stove.** A door at the other end of the wall, a stove nearer the doorway or a
  cold room with an outside wall losing heat could change which placement wins.
- **RANS, one mesh.** k-ω SST on a stepped castellated mesh of 254,506 cells, 2-8 cm, with wall functions.
  SST's k needed bounding at 7,588 (high) and 19,276 (low) of the 46,441 and 48,775 steps, to minima of
  -0.015 and -0.017 m²/s² before bounding. No mesh or time-step study.
- **The draught's chill on skin** is not modelled, and is the floor camp's other point: a slow fan on the
  floor is felt less. The case gives air temperature and speed only.

## Sources

- Charlton & Jenrick, Go Eco 5 installation and operating instructions, issue 08 09/23, p. 13: "Declared
  nominal output: (kW) 5" on wood, tested 5.1 kW, efficiency 82.5%, EN 13240.
- Lasko 3733 20-inch box fan: Lasko's support answer on the product's Best Buy page, 1250 CFM on its lowest
  speed and 1800 CFM on high.
- hearth.com, "Room to Room OR Doorway Fan?" (thread 146185, Sep 2015): "many of us have better luck moving
  the cooler denser air near the floor towards the stove/stove room"; "I've tried both, and moving the cold
  air works better". "Warm air in or cold air out?" (thread 205350, Nov 2024). "Is a doorway corner fan good
  for anything?" (thread 194048, Oct 2022): "I use 1 to move the hot air to the cold room. It helps the
  convection loop"; corner doorway fans "shaped to fit in upper corner of the door".
- The fan zone: [`tallRoomFan`](../tallRoomFan). The castellated room mesh: [`airPurifierCorner`](../airPurifierCorner)
  and [`acLouvreAngle`](../acLouvreAngle).
- The question came from a viewer, who suggested under the `tallRoomFan` clip a fan to move heat between
  rooms where one has a fireplace.

## How the case got here

**A first solve was replaced.** It held the stove's faces at 250 °C and the flue's at 150 °C. The two fan
placements then drew different heat from the stove, the cold floor air blown at it with the fan low drawing
about twice as much, so its result came from the boundary condition rather than the fan. On 13 Nov 2026 the
pair was solved again with the fixed output above, everything else unchanged. Nothing from the first solve's
runs is in this case. Both solves share the mesh and the fan's held velocities, which were set before the
first solve's production runs, in 0-10 s pilots that had its hot stove; the fan's flow in the runs here is
measured afresh (0.2988 and 0.2955 m³/s over 160-190 s, against the 0.295 target).

**The solve.** Both runs were launched in the night of 13 to 14 Nov 2026 side by side on our own machine from rest, 8 ranks
each, one physical core a rank. A first launch stopped after 3 s when the driver's check on the flue's
instantaneous heat tripped, and both runs were started again from rest; nothing of that attempt is in the
monitors. The runs were planned to 200 s with fields every 10 s; the driver projected each run's cost from
its own rate and stopped both at the last common write that fitted the 10 h cap for the pair, **190 s**, by
an abort file read at the next write. **Each run went straight through from rest to 190 s in one segment,
with no restart**: one `Starting time loop`, and the log ends in `End` at `Time = 190`. The runs took 46,441
(high) and 48,775 (low) steps, about 4.6 h and 4.9 h of wall time on 8 ranks each.

**A straight run with this case's `Allrun` is the same run**, ending at its `endTime` of 190 s instead of by
the abort file at its 190 s write. **It will not repeat the solved runs bit for bit**, because scotch gives
a different 8-rank decomposition on each call on our machine (32,123 cells on rank 0 in a rebuild against
the solved runs' 31,973), so parallel sums round differently; in a turbulent buoyant flow that round-off
grows, and the zone means of a rebuilt run should be expected to agree with these to a few hundredths of a
kelvin, not to the last digit. No rebuilt run was solved.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with NumPy.

    cd cases/doorwayFanStove
    ./Allrun high                # [nProcs], default 8; builds the mesh first
    ./Allrun low                 # default 8; start it once runs/mesh/ is built
    python3 scripts/extract_results.py runs results

The first `Allrun` builds the shared mesh in `runs/mesh/`: `scripts/make_mesh.py` writes the meshing
dictionaries (`template/mesh/system/`) and the solids' STL, then blockMesh, a serial snappyHexMesh of under a
minute, `scripts/house_patches.py` (the patches, the fan and doorway zones, and the cell centres for the
starting fields) and checkMesh. Then `scripts/make_case.py` writes `runs/<run>/`: the mesh, `0/`,
`constant/` and `system/` from `template/` and `config/case.json`, the fan's `fvOptions`, and the monitor
from `scripts/monitor.C`. `Allrun` writes the reference cells' face set (topoSet), decomposes by scotch with
those cells kept on one rank, writes the t = 0 planes, solves from 0 to 190 s, and once both runs have
solved writes `results/`. The two runs differ only in `constant/fvOptions`. `./Allrun --setup-only <run>
[nProcs]` stops before the solve; `./Allclean` removes the runs. The solved runs took about 4.6 h (high) and
4.9 h (low) on 8 ranks each.

Each run writes 305 section and 3 x 305 plan planes (VTK, about 0.36 GB a run gzipped), the fields every 10
s and a monitor file of about 0.45 MB. `results/` holds the summary, the zones and each run's history every
2.5 s; no fields, meshes, planes or logs.

The case was set up and solved by an agent on our own machine and checked by us. The files in `results/`
are what `scripts/extract_results.py` wrote from the solved runs' monitors.

Checked from a clean copy of this folder on 14 Nov 2026: `make_mesh.py`, blockMesh, snappyHexMesh and
`house_patches.py` rebuild the solved mesh byte for byte (the STL, and `points`, `faces`, `owner`,
`neighbour`, `boundary`, `cellZones`, `faceZones` and snappyHexMesh's level and zone files), and `checkMesh`
gives the solved mesh's report line for line: Mesh OK at 254,506 cells, non-orthogonality 25.2394° at most,
skewness 0.333333. `make_case.py` writes both runs' `0/`, `constant/` and `system/` byte for byte, but for
`controlDict`'s `endTime` (190 against the solved runs' 200) and the abort function object in
`system/functions`, which is left out; the t = 0 planes are the solved runs' byte for byte. The
decomposition is not (above). No solve was run from the clean copy. `scripts/extract_results.py` on the
solved runs' monitors gives the study's own figures: the 160-190 s head means (20.448 and 23.125 °C), the
doorway's exchange (0.299/0.293 and 0.234/0.231 m³/s), the cold room at 190 s, the wall and doorway heat,
and the -0.012% and -0.007% heat budgets.
