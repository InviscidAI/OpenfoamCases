# A dry-ice cauldron in the living room, front door shut or open

Every Halloween, poison centres warn that the carbon dioxide from dry ice sinks and pools near
the floor, where it could be dangerous to small children and pets. This case puts a cauldron of
dry ice in warm water on a coffee table in a 5 × 4 m living room with an 8 ft ceiling and
follows the room for the first ten minutes after the dry ice goes in, once with the front door
shut and once with it open to a still 10 °C evening, as it would be for trick-or-treaters. The
number it reports is **the CO2 at a toddler's nose, 0.6 m up, as a multiple of normal air**
(425 ppm), set beside published exposure limits. It is not a verdict that a cauldron is safe or
dangerous.

One OpenFOAM case, two runs that differ only in the front door:

    ./Allrun shut       # the front door (and the room's other door) shut, 0-600 s
    ./Allrun open       # the front door open to the evening, 0-600 s

**Nobody is in the room, the dry ice never slows, and the open door stays open.** The toddler
is a place in the solved air, not a body in it, and the source is held at a steady rate for the
whole ten minutes. The exposure limits are workplace limits for healthy adults. Read
[What it cannot](#what-it-cannot) before any number here.

## The room

| | value | from |
|---|---|---|
| room | 5.0 m from the front wall to the back wall, 4.0 m wide, 2.4 m (8 ft) high: 20 m² (215 sq ft), 48 m³ | between the UK's average new living room, 17.09 m² (LABC Warranty, via Which?, 2018), and NAHB's 27.4 m² family room (Spaces in New Homes, 2019) |
| front door | 36 × 80 in (0.914 × 2.032 m), in a front wall 0.15 m thick, centred on the room's middle line | the usual US slab; the IRC's minimum clear opening is 32 × 78 in, the UK's common door 838 × 1981 mm |
| shut / open | shut, a door across the doorway at the wall's inside face; open, the doorway clear, the leaf left out as if swung back against the wall | ours |
| coffee table | a top 1.0 × 0.5 m, 18 in (0.45 m) high, its near edge 2.25 m from the front wall on the door's middle line; no legs | the top of the usual 16-18 in |
| cauldron | 16 in across and 12 in deep, modelled as a 0.36 m square box of the same area standing on the table, its top at 0.75 m | Lowe's Union Products witch's cauldron |
| the dry ice | pure CO2 leaving the cauldron's top at 2.5 g/s for the whole cauldron, from t = 0 for the ten minutes: 1.5 kg (3.3 lb) | the low end of the sellers' recipes, below |
| the gas leaving the water | 5 °C | no measurement found; a flowvis.org student report's assumption |
| indoors | 21 °C (70 °F); the room's floor, ceiling and walls held there | ours |
| outside | still air at 10 °C (50 °F), 2.0 m deep beyond the wall, up to 3.4 m and 2.5 m to the side of the door's middle, above a ground at the floor's level | NOAA's 1991-2020 hourly normals for 31 Oct, 6-8 pm: 48-50 °F at Chicago O'Hare, 55-57 °F at LaGuardia, 61-66 °F at Atlanta; Heathrow's October mean minimum 8.8 °C (Met Office) |
| the room's other door | shut in both runs; a 5 cm square in the ceiling's back corner of the half model, 50 cm² in the whole room (a 7 cm square's worth), stands for the room's leaks, open to the outdoor air's pressure | ours |
| normal air | 425 ppm CO2 indoors and out at the start | NOAA's 2025 global mean, 425.62 ppm |

**How fast the dry ice goes.** No measured rate was found, so the rate is the one the sellers'
own recipes imply. Chillistick's instructions: "Boil a full 1.5 litre kettle and let it stand
for 3 minutes. Place 500g of dry ice into the container"; the effect "will last for 3 - 4
minutes and will fill most living rooms", and "adding a few pellets every 5 minutes or so the
fog effect can continue". That is 2.1-2.8 g/s while the water is hot. dryiceinfo.com: "For
every fifteen minutes, put 5 to 10 pounds of dry ice into a 4 to 8-gallon container of hot
water", 2.5-5 g/s. The case takes 2.5 g/s, held for the ten minutes as if topped up. A stage
fog machine runs about 2.3 kg a minute (Knight's FAQ), fifty times more.

**What the gas is like when it leaves the water.** Rutgers' demonstration notes say the fog
first rises off hot water and then sinks once "the cold carbon dioxide cools the air to the
point that it becomes more dense than the air around the basin". Its temperature matters
little here: 5 °C against 21 °C makes the gas 6% denser, while CO2 is 53% denser than air at
the same temperature.

**A rough figure.** 1.5 kg of CO2 is 0.82 m³ at 21 °C. Mixed evenly through the shut 48 m³
room it would be 1.7%, about 17,500 ppm, 41 times normal air. The solve's point is that it does
not mix evenly.

## The model

`scripts/make_case.py <run> <dir>` writes every dictionary, the initial fields and the run's
own Allrun. Coordinates: x from the front wall's inside face into the room, y up from the
floor, z across the room from the middle of the door.

- **A 3-D half room.** The model is the half of the room on one side of the vertical plane
  through the middle of the front door and the cauldron, a symmetry plane, which is also the
  clip's section. The cauldron's 2.5 g/s is 1.25 g/s in the half model.
- **The gas:** O2, N2 and CO2 with their real molar masses, perfect gases with JANAF
  thermodynamics and Sutherland viscosity (the coefficients of the v2512 tutorials'
  `thermo.compressibleGas`), argon lumped into N2. The solver is rhoReactingBuoyantFoam
  (OpenFOAM v2512) with no reactions: the CO2 only moves and mixes, but the density is the
  mixture's, so air carrying CO2 is heavier. Species diffuse with the solver's μ_eff, a
  Schmidt number of 1 (CO2 in air is 0.94). Water vapour and fog droplets are not modelled.
- **The source:** the cauldron's top is an inlet of pure CO2 at 5 °C and a fixed mass flow
  (`flowRateInletVelocity`).
- **Turbulence and numbers:** k-omega SST with the buoyancy source on k
  (`buoyancyTurbSource`), PIMPLE with 2 outer and 2 pressure correctors, Euler in time at
  Courant 1, limitedLinearV for momentum, limitedLinear for energy and turbulence and
  limitedLinear01 for the species, as [`windowAiring`](../windowAiring).
- **Mesh:** one graded blockMesh box of 484,120 cells over the outdoor air, the front wall and
  the room, cut down with subsetMesh to the air: 384,867 cells. Cells are 10 mm tall at the
  floor, growing to 25 mm at 0.2 m, 30 mm round the cauldron and across the doorway,
  and 40-53 mm elsewhere in the room. Shut, the door is a baffle on the doorway's faces at
  x = 0, so the mesh is two regions, the room and the outdoor air, each with an open boundary
  (the room's is the leak).
- **Surfaces:** the room's floor, ceiling and walls are held at 21 °C; the table, the
  cauldron's sides, the door, the wall's outer face, the doorway's reveal and the ground
  outdoors are adiabatic. Walls are no-slip with wall functions.
- **The outside's open faces and the leak** hold the still 10 °C air's barometric pressure
  face by face, p0 = 1e5 exp(−g y / (R T)), as `prghTotalPressure` less the dynamic head on
  inflow; air coming in is outdoor air at 10 °C and 425 ppm. `hydrostatic.py`, written into
  the run, sets those p0 once the mesh is final and starts every cell at its own temperature's
  barometric pressure, so the solve starts at rest.
- **The start:** at t = 0 the room is still at 21 °C, the outdoor air still at 10 °C, the dry
  ice goes in and, in `open`, the door is open.
- **Monitors, every step:** the room's CO2 mass, the CO2 at 0.6 m averaged over the room (the
  `nose` zone, the two cell layers between 0.57 and 0.63 m) and its largest cell, the gross
  mass flow each way through the doorway and the CO2 through it, and what the cauldron and the
  leak pass. Three planes every 1.25 s: the mid plane (z = 0.005 m) through the door and the
  cauldron, which the clip shows, a plane at 0.6 m and one at 0.1 m.

## How the case got here

The first build set the open faces' pressure to 1e5/(1 + g y/(R T)). That makes p_rgh uniform
but is not rest for a compressible gas, and in the shut run the still outdoor air, which
nothing drives, sank through the outdoor box at up to 0.06 m/s, in at the top and out low on
the outer faces. A 0-30 s test on the shut run's mesh with only the pressure formula changed to
the barometric one kept the outdoor air at a median of 0.0000 m/s and left the room's CO2
unchanged to 0.01 g. Both runs were solved again with the barometric pressure; those are the
runs here. The shut room, cut off from the outdoor air by its door, gave the same number to
0.1% (105.3 against 105.4 times normal air at 0.6 m at 600 s); the open room's moved by
between 10% down and 8% up through the ten minutes and ended 7% lower (20.3 against 21.8).
The first build's runs are not kept.

## Checks

- **The generator against the solved runs.** From a clean copy, `./Allrun --setup-only shut`
  and `--setup-only open` wrote the solved runs' meshes (points, faces, owner, neighbour,
  boundary, cell and face zones and sets) and every initial field, the barometric p and p_rgh
  included, byte for byte: 384,867 cells each, `checkMesh` OK, one region open and two shut.
  Their dictionaries have the solved values and differ only in comments. The decomposition on
  8 ranks is scotch's, which splits the mesh differently from one call to the next, so the
  processor directories differ and a re-solve will not match the committed histories to the
  last digit.
- **The CO2 budget closes once diffusion through the source is counted.** At ten minutes the
  shut room holds 1,570 g more CO2 than at the start (whole room), against 1,500 g convected in
  at the cauldron. The open room holds 672 g more, after 1,500 g in, 876 g out through the
  doorway and 11 g through the leak. The residual, 0.05-0.06 g/s in the half model and steady
  through both runs, is the CO2 diffusing in through the cauldron's face, where it is held at
  1 against diluted cells next to it, on top of what the flow carries: by hand,
  μ ∂Y/∂n × area ≈ 1.8e-5 × (0.7/0.015) × 0.065 m² ≈ 0.055 g/s. So the cauldron in effect
  delivers about 2.6 g/s, within the sourced 2.1-5 g/s, and the masses above are what the room
  actually received.
- **The open doorway's exchange** is 0.41 kg/s each way through the whole door at 10-30 s,
  falling to 0.21 kg/s by five minutes as the room cools to about 14 °C on the section (its
  walls are held at 21 °C). That is 14-23% more than the doorway formula
  Cd/3 W √(g H³ ΔT/T) with Cd 0.6 over the first minute, and 14-19% less from five minutes on:
  within the formula's range, which assumes a mixed room.
- **The still outdoor air stays still.** In the shut run, where nothing drives it, the outdoor
  air on the mid plane has a median speed of 0.00005 m/s and a largest of 0.0024 m/s at 600 s.
- **Both runs ended cleanly** at 600 s, in 9,532 steps shut and 14,306 open.

## Results

From `results/summary.txt` and `results/<run>/history.csv`, which `scripts/extract_results.py`
writes from the runs' per-step monitors and mid planes.

**The toddler.** The model has no one in the room, so where the toddler stands is a choice: on
the floor, 0.5 m behind the coffee table on the mid plane, facing the cauldron, the tip of its
nose 3.25 m from the front wall and 0.6 m up. The number is the CO2 in the plane's four cells at
that nose (x 3.20-3.30 m, y 0.56-0.64 m), averaged over the last 10 seconds, a few breaths,
because a single moment's value jumps by up to 7 between writes in the open room as eddies
pass.

| at the toddler's nose, × normal air | 1 min | 2 min | 3 min | 5 min | 10 min | ten-minute average |
|---|---:|---:|---:|---:|---:|---:|
| front door shut | 1 | 2 | 12 | 43 | **103** | 43 |
| front door open | 9 | 17 | 19 | 23 | **38** | 26 |

With the door shut the gas spills over the cauldron's rim, runs down its sides and off the
table, and spreads over the floor as a layer that thickens through the ten minutes. For the
first three minutes the air at the toddler's nose stays at 1-3 times normal while the floor
layer is already far richer, and only then does the layer's top rise past the nose. At ten
minutes the toddler breathes about 103 times normal air, about 4.4% CO2.

With the door open, the cold evening air comes in along the floor under the warm room air
leaving through the top of the doorway. It does not drain the CO2 out under the door. It runs
in beneath the gas, lifts it off the floor and mixes it up through the room, so for the first
four minutes the open room has the higher number (17 against 2 at two minutes). Some of the
mixed gas then leaves through the top of the door, and the open room's number climbs more
slowly, to about 38 times normal air (1.6% CO2) at ten minutes, while the shut room's goes on
climbing. The two cross at 4 min 4 s and do not cross again.

**The room average at 0.6 m** tells the same story with the door shut and a milder one with it
open:

| room average at 0.6 m, × normal air | 1 min | 2 min | 3 min | 5 min | 10 min | ten-minute average |
|---|---:|---:|---:|---:|---:|---:|
| front door shut | 2 | 3 | 11 | 47 | 105 | 46 |
| front door open | 8 | 12 | 15 | 17 | 20 | 16 |

Shut, the toddler's value is 0.95 of the room average (median over the last nine minutes).
Open, it is 1.6 times the room average (median; 1.0-2.4 times), because the mid plane is the
line from the doorway to the cauldron, where the cold inflow lifts the gas. The toddler stands
on that line, so its number is its own, and a toddler elsewhere in the open room would breathe
less.

### Against exposure limits

The limits below are for healthy adults at work, averaged over 15 minutes or 8 hours. There are
none for toddlers, and none of them is a line between safe and harmful at a moment in time.

| limit | ppm | × normal air |
|---|---:|---:|
| OSHA PEL and NIOSH REL, 8-hour average | 5,000 | 12 |
| UK HSE workplace limit, 15-minute average (EH40) | 15,000 | 35 |
| NIOSH short-term limit, 15 minutes | 30,000 | 71 |
| NIOSH immediately dangerous to life or health | 40,000 | 94 |

The Minnesota Department of Health puts headache and dizziness above 5,000 ppm for many hours
and its indoor ventilation target below 1,000 ppm. The often-quoted drowsiness bands at
1,000-2,000 ppm come only from vendors and are not used.

- **Shut,** the air at the toddler's nose passes the 8-hour workplace level at about
  3 min 20 s, the UK's 15-minute level at 4 min 35 s, the NIOSH short-term level at about
  7 minutes, and by 9 min 10 s it is at the level NIOSH calls immediately dangerous for a
  working adult. Averaged over the ten minutes it is 43 times normal air, above the UK's
  15-minute limit.
- **Open,** it passes the 8-hour workplace level after about a minute, and its ten-minute
  average, 26 times normal air, stays below every 15-minute limit, although from about
  5 min 40 s on it is above 35 times for 44% of the time.
- **Beside the cauldron** it is far higher. In the 0.57-0.63 m layer the richest cells, in the
  gas running down the cauldron's sides, are 230-350 times normal air in both rooms from two
  minutes on. A child leaning over the cauldron breathes that, not the value half a metre away.

These are values at one spot in a model of one room with a steady source; nobody is in it, the
source never slows, and the room's other door stays shut. They say that a cauldron of dry ice
left bubbling in a small shut room puts a lot of CO2 at a small child's or a dog's height
within minutes, which is the poison centres' warning; they do not say that harm follows at any
particular moment.

0.6 m stands for a younger toddler, about a year old, a child sitting on the floor or a dog. A
two-year-old's nose is nearer 0.75 m (CDC's median standing height at 24 months is 85-87 cm).

## What the clip shows, and what it does not

**It shows** the mid plane through the door and the cauldron, shut above and open below, from
the moment the dry ice goes in to 600 s, 30× fast, coloured by the CO2 as a multiple of normal
air on one linear scale from 1 to 100 times, saturating above, with parcels of air carried by
the solved flow in the plane. The wall, the table, a drawn iron cauldron with lumps of dry ice
in its mouth, the shut door and a toddler standing behind the table are drawn over it. Each
panel has one number, the CO2 at the toddler's nose from the table above, in whole multiples:
it ends at 103 shut and 38 open.

**It does not show** fog. Real dry ice makes white fog, water droplets condensed out of the room
air by the cold gas, which evaporate as the gas warms and mixes while the CO2 goes on spreading
unseen. The fog is neither solved nor drawn; the colour is the CO2. The gas pouring over the rim
and down the cauldron's sides, at 200-650 times normal air on the section, is above the scale's
top and shows in its top colour, as does the shut room's floor layer late in the clip. The
clip shows no exposure limits, and nothing off the mid plane.

## What it cannot

- **The fog's droplets and the water vapour,** which are neither simulated nor drawn.
- **People.** The toddler is drawn, and the air is solved as if it were not there. Nobody walks
  through the room, opens and shuts the door between visitors or breathes out CO2 of their own,
  and the open door stays open for the whole ten minutes.
- **The dry ice slowing down** as the water cools. The rate is held at the topped-up value, with
  no measured sublimation rate behind it, only the sellers' recipes.
- **The rest of the house.** The room's other door is shut and its leaks are one small opening.
  The room has no furniture but the table, and the table has no legs.
- **Wind.** The evening is still, at one temperature.
- **Workplace limits for a child.** The limits are for adults over 15 minutes or 8 hours; the
  case sets its numbers beside them and does not turn them into a risk.
- **One mesh, unsteady RANS,** k-omega SST with wall functions, a Schmidt number of 1, no mesh
  or time-step study, one realization of each run. The toddler's number is four cells on one
  plane, averaged over 10 s.

## Sources

- UVA Blue Ridge Poison Center, Halloween safety: "Carbon dioxide will sink and "pool" in low
  places, which could be dangerous to pets, small children, or people laying or sitting near
  the floor. Never use dry ice in an unventilated room or car."
  https://med.virginia.edu/brpc/wp-content/uploads/sites/274/2015/10/Halloween.pdf
- Chillistick, dry ice instructions: https://www.chillistick.com/user/downloads/dryiceinstructions.pdf
- dryiceinfo.com, fog: https://dryiceinfo.com/fog/
- Rutgers, demonstration notes on fog formation:
  https://chem.rutgers.edu/cldf-demos/1029-cldf-demo-fog-formation
- NIOSH Pocket Guide, carbon dioxide: https://www.cdc.gov/niosh/npg/npgd0103.html
- HSE, carbon dioxide: https://www.hse.gov.uk/coshh/basics/carbondioxide.htm
- Minnesota Department of Health, carbon dioxide indoors.
- NOAA Global Monitoring Laboratory, global annual mean CO2:
  https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_annmean_gl.txt
- NOAA 1991-2020 hourly climate normals (Chicago O'Hare, LaGuardia, Atlanta); Met Office
  station data (Heathrow).
- LABC Warranty, via Which? (2018), the UK's average new living room; NAHB, Spaces in New Homes
  (2019).
- Lowe's, Union Products witch's cauldron, 16 in; CDC growth charts, stature for age.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3;
`scripts/extract_results.py` also needs NumPy and PyVista.

    cd cases/dryIceCauldron
    ./Allrun shut                    # [nProcs], default 8
    ./Allrun open
    python3 scripts/extract_results.py runs results

`Allrun <run>` writes the run into `runs/<run>/` with `scripts/make_case.py`, then runs the
Allrun written there: blockMesh, subsetMesh to the air, the cauldron's top, the leak, the
furniture and the outer walls as patches, shut the door as a baffle, the zones, the initial
fields, the barometric pressure in the cells and on the open faces, checkMesh and decomposePar.
It then writes the t = 0 planes from the initial fields and solves 0-600 s, writing the planes
every 1.25 s and the fields every 50 s (the last two kept). `./Allrun --setup-only <run>` stops
before the t = 0 planes and the solve, in about 10 s. `./Allclean` removes the runs.

The runs took 5,656 s (`shut`) and 8,440 s (`open`) of wall time on 8 ranks each, side by side.
Each writes about 0.7 GB of planes. `results/` holds each run's history at every plane write
(the budget, the room average and largest cell at 0.6 m, the toddler's number, the open
doorway's flow and the outdoor air's speed) and the summary; no fields, meshes, planes or logs.

The case was built, checked and solved by an agent on our own machine, which caught the outdoor
pressure fault above at packaging and solved both runs again before the clip was made.
