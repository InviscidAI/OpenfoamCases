# Closing the heat register in a spare room, against leaving it open

Many owners of a house with forced-air heating close the register (the floor vent) in a room nobody uses and
shut its door. One camp says the heat goes to the rooms they use instead: "just close the vent in that room and
keep the door closed ... saving money on your energy bill" (The Simple Dollar), "I have a spare bedroom that's not
used so it gets the vent shut off, that redirects the heated air to the rest of the house". The other camp says a
system is built to run with every register open: "Closing off the registers actually makes your system less
efficient" (Puget Sound Energy), and Lawrence Berkeley National Laboratory's study of register closing found that
"the reduction in building thermal loads due to conditioning only a part of the house was offset by increased duct
system losses; mostly due to increased duct leakage" (LBNL-54005). This case heats the same small one-storey house
twice from its night setback, once with every register open and once with the spare bedroom's register closed, its
door shut in both, and asks where the spare room's share of the heat goes in the first five minutes after the
blower starts, and how warm the air is at head height in the spare room and in the rest of the house. It is about
where the heat goes, not the heating bill: that turns on hours and a whole winter, which five minutes cannot show.

    ./Allrun open      # every register open, 0-300 s from the blower's start
    ./Allrun closed    # the spare room's register closed, 0-300 s

**The result.** **The closed room stays at its setback, and the rest of the house gains under a kelvin.** The
registers carry what a hand calculation of the ducts gives them (`scripts/ducts.py`): with every register open
8,086 W, of which 1,400 W goes to the spare room; with the spare room's register closed 7,665 W, all of it to the
other five rooms, which get **0.98 kW more**. That **70% of the spare room's heat reaches the other rooms and 30%
is lost to the extra duct leakage is the hand calculation's**, not the solve's: the ducts are not in the mesh. In the
solve, the closed spare room's air at head height holds **16.67 °C (62.0 °F) to the end**, while with its register
open it reaches 22.13 °C at 150 s and **23.84 °C (74.9 °F) at 300 s**. The rest of the house at head height is
**0.54 K warmer at 150 s and 0.68 K warmer at 300 s** with the spare room's register closed (23.91 against 23.23 °C,
75.0 against 73.8 °F, at 300 s). Read [What it cannot](#what-it-cannot) before any number here: **the ducts and
their leaks are a calculation**, **the house warms far faster than a real one** (no furniture, no framing, no
infiltration, no radiation), and **nothing here says what happens to the bill**.

The house and the duct calculation are new. The buoyant model is [`acLouvreAngle`](../acLouvreAngle)'s and
[`doorwayFanStove`](../doorwayFanStove)'s, the castellated mesh with the solids cut out on cell faces is theirs and
[`airPurifierCorner`](../airPurifierCorner)'s, and the walls that store heat are
[`radiatorCabinetTop`](../radiatorCabinetTop)'s `radLayerWall` with its radiation taken out. The monitor follows
`doorwayFanStove`'s. [`ceilingVsFloorVent`](../ceilingVsFloorVent) is the other forced-air register case.

## The house

A one-storey ranch house of 10.0 x 8.8 m (88 m², about 950 sq ft), two bedrooms and a bath, its ducts in a
crawlspace and a floor register under each window. The layout and sizes are ours. x runs east from the west wall, y
up from the floor, z north from the front wall; metres. The whole house is solved, with no symmetry.

| | where | |
|---|---|---|
| living room | x 0-5.6, z 0-4.4 | two registers, under two front windows |
| kitchen | x 5.7-10.0, z 0-4.4 | one register under its front window; open to the living room by a 1.6 m opening, 2.1 m high |
| hall | x 2.1-7.6, z 4.5-5.4 | open to the living room by a 1.0 m opening, 2.1 m high; the return grille at its east end |
| bedroom closet, furnace closet | x 0-2.1 and 7.6-10.0, z 4.5-5.4 | solid; the return grille, 0.6 x 0.6 m, low on the furnace closet's west face (x = 7.6 m, y 0.2-0.8 m) |
| bedroom | x 0-4.0, z 5.5-8.8 | register under its back window; door open, 0.8 x 2.0 m |
| bath | x 4.1-6.1, z 5.5-8.8 | register under its window; door open, 0.8 x 2.0 m |
| spare bedroom | x 6.2-10.0, z 5.5-8.8 | register under its back window; **door shut in both runs, with a 5 cm gap under it** |

Interior walls are 0.1 m thick and the ceiling 2.4 m high (8 ft is 2.44 m). The doors that are open are not
modelled. The registers are 0.30 x 0.10 m (12 x 4 in, 0.03 m²), blowing straight up from the floor. The windows are
double glazed, 1.0 x 1.2 m from 0.9 m up, the bath's 0.8 x 0.6 m from 1.4 m up, 6.48 m² in all. The room volumes on
the mesh are 59.1 (living room), 45.4 (kitchen), 11.9 (hall), 31.7 (bedroom), 15.8 (bath) and 30.1 m³ (spare room).

**The walls store heat.** The outer and inner walls and the ceiling are 12.7 mm gypsum (k 0.1587 W/m K, ρc
723,991 J/m³ K) and the floor 19 mm wood (k 0.106, ρc 1,237,411), each in 24 layers behind its surface with an
adiabatic back (`src/storedLayerWall`). In five minutes the heat reaches only millimetres into them, so what lies
behind does not matter, and no heat leaves through the outer walls. The windows have no layers: their surface loses
heat to 20 °F (-6.67 °C) outdoors through a film of 4.4 W/m² K, a double-glazed U-value of 2.8 W/m² K without its
inside film.

**The start.** The air at rest at 62 °F (16.67 °C, 289.82 K), the night setback, the walls, floor and ceiling at
the same temperature through their thickness, the pressure in hydrostatic balance with 1e5 Pa at y = 0.5 m. At
t = 0 the blower starts and the registers blow at their full flow and supply temperature.

**There are no people.** The temperatures are volume means of the air over each room's box: the whole room, the
ankles (y < 0.2 m), the seated zone (0.9-1.2 m), **head height (1.5-1.8 m)** and under the ceiling (y > 2.2 m).
"The rest of the house" is the whole house but the spare room's box, the air in the doorways included.

## The furnace and the ducts, by hand

The ducts are not in the mesh. Each register is an inlet with the flow and temperature that a simple duct network
gives (`scripts/ducts.py`, its output in `config/ducts.txt`):

- **The furnace** is an American Standard S8X1B040M2PSC, 40,000 Btu/h input and 32,500 Btu/h (9,525 W) output.
  Its blower on tap 3 moves 820, 662 and 504 CFM at 0.1, 0.3 and 0.5 in w.c. (the furnace's submittal, airflow
  table). The calculation uses that line's slope, 790 CFM per inch, shifted to pass through its own design point of
  612 CFM at 0.50 in. The furnace's heat goes into the whole air stream, so less air means a larger temperature rise.
- **The ducts** are a return side and a supply trunk, each taking 0.25 in at the design flow, and six branches, one
  to each register, with 10 Pa at each boot. With every register open the blower sits at 0.50 in w.c., the usual
  rated maximum (Energy Vanguard reports that real systems typically run near 0.8).
- **The leaks** are sized as LBNL-54005's "supply plenum and registers" case: 10% of the air handler's flow at the
  supply plenum and 5% over the boots, as power laws with exponent 0.6 (the report's calibrated leaks had 0.61).
  They leak into the crawlspace, so their heat is lost to the house. A closed register passes nothing; its boot then
  sits near the trunk's pressure and leaks more.

| | air handler | static | registers, CFM (living W, living E, kitchen, bedroom, bath, spare) | supply | leaks |
|---|---|---|---|---|---|
| open | 612 CFM | 0.50 in | 95, 95, 95, 100, 45, 90 | 111.0 °F (43.90 °C) | 92 CFM, 15.0% |
| closed | 586 CFM | 0.53 in | 104.4, 104.4, 104.4, 109.9, 49.4, 0 | 113.1 °F (45.08 °C) | 114 CFM, 19.4% |

With every register open the spare room's register carries 1,401 W. Closed, the other five rooms get 978 W more
(14.6% more heat, 9.9% more air), and the other 423 W goes out of the extra leakage: **70% of the spare room's heat
reaches the other rooms and 30% leaks out, on these leaks.** With tight ducts nearly all of it would reach the
other rooms, and with leakier ducts less would.

In the solve each register is a `flowRateInletVelocity` of the calculation's L/s times 1.204 kg/m³, at its supply
temperature (`config/case.json`, "runs"): 0.05398 kg/s for each living-room register and the kitchen's, 0.05682
(bedroom), 0.02557 (bath) and 0.05115 (spare), 0.29548 kg/s in all, at 317.05 K, open; 0.05931, 0.06244, 0.02808
and none, 0.26845 kg/s, at 318.23 K, closed. The closed spare register is a no-slip, adiabatic wall. Over 20-30 s
the registers carry **8,086.15 W open and 7,664.80 W closed** above the starting 62 °F (cp 1005 J/kg K), 0.12% and
0.11% under the calculation's 8,096 and 7,673 W, which use cp 1006 and unrounded flows. The return grille is a fixed
pressure, 1e5 Pa (`prghPressure`), the house's only way out.

## The model

`buoyantPimpleFoam` (OpenFOAM v2512), compressible air as a perfect gas (Cp 1005 J/kg K, molar mass 28.96,
μ 1.82e-5 Pa s, Pr 0.71), k-ω SST with `buoyancyTurbSource` and wall functions (`kLowReWallFunction`,
`omegaWallFunction`, `nutkWallFunction`, `alphatJayatillekeWallFunction`). Euler in time, adaptive steps at
Courant 1 (maxDeltaT 0.05 s; 13.6 ms open and 18.4 ms closed at 300 s), limitedLinearV for U and limitedLinear for h,
and bounded upwind for k and ω, the one change from `doorwayFanStove`'s schemes, made before the solve against the
negative k that SST needed bounding for there. Two outer and two pressure correctors, p_rgh by GAMG to 1e-7 with
the final solve capped at 100 iterations (no step reached it). The return's fixed pressure sets the pressure level,
so there is no reference point. No radiation.

**The mesh** (`template/mesh/system`, `scripts/make_mesh.py`, `scripts/house_patches.py`): a background of 10 cm
cubes (blockMesh, 100 x 24 x 88), refined by snappyHexMesh, castellated only, without snapping or layers: 5 cm in a
0.5 x 0.6 x 0.25 m box over each register and 2.5 cm round the gap under the spare room's door (x 6.5-7.5,
y < 0.15, z 5.3-5.6 m), so the gap is two cells high, with two cells between levels. The interior walls, the two
closets and the spare room's door are one closed STL, the union of their boxes, written by `make_mesh.py` on the
mesh's own faces, so they are cut out exactly. `house_patches.py` sorts the boundary faces by face centre into
`floor`, `ceiling`, `walls`, `windows`, `return` and the six `register_<room>` patches, writes the face zones the
monitor sums the flow over (the gap under the spare room's door, the bedroom's and the bath's doors, the hall's and
the kitchen's openings), and checks each register's (0.03 m²), the windows' (6.48 m²), the return's (0.36 m²) and
the gap's (0.04 m²) areas to 1%. **202,274 hexahedral cells**, an air volume of 194.910 m³; `checkMesh` OK,
non-orthogonality at most 25.2°, skewness at most 0.33, aspect ratio 1. One mesh, no mesh study.

**The monitors** (`scripts/monitor.C`, a coded function object run at every step, one row at the first step and
every 0.625 s into `postProcessing/metrics/metrics.csv`): each register's and the return's mass flow each way, its
temperature and the enthalpy cp (T - 289.82 K) it carries; the gross flow each way through each opening and its
enthalpy; the air's mass, its enthalpy ∫ρ cp (T - 289.82 K) dV and ∫p dV; its coldest and warmest cell and where
they are; the mean temperature of each room's five zones and of the rest of the house; the heat out of the air into
the floor, the ceiling, the walls and the windows, both with the energy equation's own diffusivity (a do-nothing
`scalarCodedSource` in `constant/fvOptions` catches it before the turbulence model updates αt) and as
`wallHeatFlux` gives it; and the running integrals of these heats and flows, summed at every step. `courant.csv`
keeps the twelve cells of highest Courant number at each row. The `planes` are plans at head height (1.62 m), seated
height (1.12 m) and the ankles (0.12 m), and sections through the spare room's door (x = 7.02 m), through its
register (x = 8.52 m) and across the back rooms (z = 7.12 m), each with T and U every 0.625 s from t = 0, 481 a run.

## Results

`results/summary.txt`, `results/rooms.csv` (every room's five zones at 15-300 s) and `results/<run>/history.csv`
(every 2.5 s), from `scripts/extract_results.py`.

| air at head height, °C (°F) | 15 s | 60 s | 150 s | 300 s |
|---|---:|---:|---:|---:|
| spare room, open | 17.02 (62.6) | 19.57 (67.2) | 22.13 (71.8) | **23.84 (74.9)** |
| spare room, closed | 16.67 (62.0) | 16.67 (62.0) | 16.67 (62.0) | **16.67 (62.0)** |
| rest of the house, open | 16.97 (62.5) | 19.09 (66.4) | 21.71 (71.1) | **23.23 (73.8)** |
| rest of the house, closed | 17.01 (62.6) | 19.60 (67.3) | 22.25 (72.0) | **23.91 (75.0)** |
| rest, closed less open, K | +0.05 | +0.51 | **+0.54** | **+0.68** |

| | open | closed |
|---|---:|---:|
| registers, W (20-30 s) | 8,086 | 7,665 |
| the spare room's register, W | 1,400 | 0 |
| the other five registers, W | 6,686 | 7,665 |
| the other five, MJ by 150 s / 300 s | 1.003 / 2.006 | 1.150 / 2.299 |
| whole-room mean at 300 s, rest of the house, °C | 21.57 | 22.26 |
| whole-room mean at 300 s, spare room, °C | 22.70 | 16.61 |
| under the spare room's door at 150 s, out / in, kg/s | 0.0536 / 0 | 0.0035 / 0.0035 |
| into the ceiling / walls / windows / floor, W, 10-300 s mean | 1,943 / 1,307 / 444 / 7 | 1,829 / 1,247 / 404 / 5 |
| share of the supply's heat still in the air at 300 s | 48% | 47% |

**Where the heat goes.** With its register open, the spare room's whole supply, about 0.053 kg/s, leaves under its
door into the hall and nothing comes back. With the register closed a few grams a second swap each way under the
door, and the room's air does not move off its starting temperature: its head zone reads 16.666-16.670 °C at every
time above, its whole mean 16.61 °C at 300 s, a little colder as its window draws on it. The five other
registers carry 15% more heat, and the rest of the house is warmer by half a kelvin from a minute on, by 0.68 K at
head height and 0.69 K in its whole mean at 300 s. In both houses the warm air rises from the registers and spreads
under the ceiling: at 300 s the rest of the house is 24.5 °C (open) and 25.2 °C (closed) under the ceiling and
still 16.8 and 17.0 °C at the ankles. The ceiling and walls take most of the heat that leaves the air, the floor
almost none. At 60 s the closed house's rest of the house is 2.93 K warmer at head height than its spare room; in
the open house the spare room is the warmer by 0.48 K.

**The number at the head.** The clip's number is the rest of the house's head-height air in °F, rounded: 62, 71 and
74 °F at 0, 150 and 300 s with every register open, 62, 72 and 75 °F with the spare room's closed. The two first
differ at 11.25 s, and the closed house's is never the lower at any of the 481 rows.

**Checks.** The registers' flows and the supply's heat are constant from the first step. The air's enthalpy budget
over 10-300 s, its rise against the registers' heat less the return's and the surfaces', each summed at every step,
closes to **-0.022% (open) and -0.005% (closed)** of the registers' heat; ∫p dV varies by 3.1e-5 and 3.4e-5 of its
start. No final pressure solve reached its 100-iteration cap. The air warms and expands at the return's fixed
pressure, so the return carries more mass out than the registers bring in, up to 7.37% (open) and 7.64% (closed) at
the rows after 10 s and 0.0130 and 0.0121 kg/s on average, and the house's air falls from 234.23 kg to 230.22 and
230.51 kg; the integrated flows agree with the change of mass. The coldest air sampled is 15.38 °C, by the bath's
window; the warmest 44.20 °C (open) and 45.41 °C (closed), in a register's jet, the closed run's at 1.875 s 0.33 K
above its supply temperature (below).

## What the clip shows, and what it does not

The clip shows the head-height plan, the whole house seen from above at y = 1.62 m, twice on every frame, stacked,
"every vent open" above and "spare room's vent closed" below, **from the blower's start to 5:00 of the solve** at 15
times speed in 20 s, a frame every 0.625 s of flow. It is coloured by air temperature on a 61-78 °F scale, with a
clock and the question "Spare room: close its heat vent?". Each panel carries one rounded number, the rest of the
house's air at head height, captioned "other rooms": 62, 71, 74 °F at 0:00, 2:30 and 5:00 with every vent open
against 62, 72, 75 °F with the spare room's closed. The spare room's own contrast, 74.9 against 62.0 °F at the end,
is left to the colour.

- **The number is the rest of the house, not the spare room or the heat moved.** It is a volume mean of the air
  1.5-1.8 m up, not a thermostat's reading, and it carries a difference of under a kelvin, 1 °F.
- The outer walls and the glass in them, the room names, the door leaves of the open doors (not modelled) and the
  registers are drawn; the registers are drawn 0.72 x 0.28 m, larger than their solved 0.30 x 0.10 m, so they read
  on a phone, and the closed one as a dark plate with a red cross. The plane's points on the walls and windows carry
  the surfaces' temperatures, not the air's, so the picture gives them the nearest air point's value, and it is
  blurred over 4 cm. The air in the jets over the registers is hotter than the scale's top (up to about 92 °F at
  head height) and is drawn at the top colour.

## What it cannot

- **The ducts are not in the mesh, and the 70/30 split is the hand calculation's, not the solve's.** Each register
  is a fixed inlet carrying `scripts/ducts.py`'s flow and temperature, from the American Standard furnace's blower
  line and LBNL-54005's leak sizes, and the solve is given the result: that closing the register sends 978 W (70%)
  of the spare room's 1,401 W to the other five rooms and 423 W (30%) out of the extra leakage, on these leaks.
  Tighter ducts would send more to the other rooms, leakier ones less. The calculation is ours and simple: its blower
  is tap 3's slope shifted through its own design point, the furnace's output is constant from t = 0 (its warm-up and
  the blower's delay are over), the supply temperature is held although the return air warms (to 18.5-18.7 °C by
  300 s), the ducts lose no heat through their walls, a closed register passes no air where real ones leak a little,
  and the leaked air pulls no outdoor air into the house.
- **The absolute warm-up is too fast for a real house.** The air at head height goes from 62 to about 74-75 °F in
  five minutes, because the model has no furniture or framing to soak up heat, no infiltration, and no radiation;
  48% of the registers' heat by 300 s is still in the air. **The 75 °F is probably several degrees high.** Both
  houses share these limits, so the gap between them should hold better than either number.
- **No radiation.** The walls, ceiling and floor take their heat by convection alone, so the floor under the warm
  layer takes almost none (5-18 W) and the ankles stay near 62 °F; in a real room the warm ceiling would radiate to
  the floor. The windows' inside film is convection alone too, so the glass is uneven: on the 300 s fields it runs
  from -2.7 to 20.3 °C (open) and -4.3 to 21.7 °C (closed), area means 9.8 and 8.4 °C, coldest where the air beside
  it is still. Together the six windows lose 444 W (open) and 404 W (closed) on average over 10-300 s, about what
  their U-value of 2.8 W/m² K gives against the starting 62 °F air (about 425 W) and less than it would give against
  the warmer air later.
- **Nothing here is about the bill or the furnace's efficiency.** Five minutes of one furnace cycle are solved. The
  bill turns on how long the furnace runs over a winter, and on the heat the cold spare room then draws through its
  inside walls from the rest of the house over hours, which five minutes do not show; the walls here store heat and
  lose none outdoors. How the blower's power and the furnace's efficiency change with the higher static pressure is
  not modelled; the duct leakage that the other camp counts against closing is the hand calculation's.
- **The gap under the spare room's door is 5 cm, against a real door's 2 cm or so (3/4 in).** It is 5 cm so that
  the mesh carries the spare room's air out under the door when its register is open, on two 2.5 cm cells; it lets
  that air out at a lower speed than a real gap would, and changes nothing that matters when the register is closed,
  with a few grams a second swapping each way. The spare room's door is shut in both runs; the case does not try it
  open.
- **The return grille is a fixed pressure**, the house's only way out, so the air that expands as it warms leaves by
  it, up to 7.6% more than the registers bring in. A real house would lose it through its cracks.
- **RANS, one mesh, one run each.** k-ω SST on a stepped castellated mesh of 202,274 cells, 2.5-10 cm, with wall
  functions. Even with bounded upwind for k and ω, SST's k needed bounding: 3,404 messages (open) over 22,953
  steps and 1,338 (closed) over 15,008, to minima of -9.0e-8 and -1.6e-7 m²/s² before bounding. No mesh or
  time-step study, and no uncertainty bar on the rest of the house's 0.5-0.7 K.
- **The closed run's air briefly ran hotter than its supply.** At 1.875 s the warmest air sampled was 45.41 °C, in
  the bedroom register's jet, 0.33 K above the 45.08 °C supply; its cause was not isolated. The extremes are sampled
  every 0.625 s, not at every step.
- **One house, one layout, one setback.** A register nearer the furnace, a spare room with more outside wall, a
  two-storey house or a variable-speed blower could change the numbers.

## Sources

- American Standard, S8X1B040M2PSCA/C product submittal (S8X1B040M2-SUB-2D-EN): 40,000 Btu/h single-stage gas
  furnace, airflow table, tap 3: 820, 662, 504, 346 and 188 CFM at 0.1, 0.3, 0.5, 0.7 and 0.9 in w.c.
- I. S. Walker, "Register Closing Effects on Forced Air Heating System Performance", LBNL-54005, Lawrence Berkeley
  National Laboratory, Nov 2003, for the U.S. Department of Energy's Building Technologies Program
  (https://eta-publications.lbl.gov/sites/default/files/54005.pdf): "register closing led to increased energy use for
  a typical California house over a wide combination of climate, duct leakage and number of closed registers. The
  reduction in building thermal loads due to conditioning only a part of the house was offset by increased duct
  system losses; mostly due to increased duct leakage." The leak exponent of about 0.6 and the "supply plenum and
  registers" leakage case.
- A. Bailes, "Can You Save Money by Closing HVAC Vents in Unused Rooms?", Energy Vanguard, 25 Jul 2014: "Although
  most systems are rated for 0.5 iwc, the National Comfort Institute ... finds the typical system to be pushing
  against a static pressure of about 0.8 iwc."
- The Simple Dollar, "Extra rooms lying empty? Close them off and save money", reprinted by the Christian Science
  Monitor, 14 Jun 2012: "If you have forced air heating and cooling, just close the vent in that room and keep the
  door closed."
- Grassroots Motorsports forum, "HVAC: Does closing ducts reduce a heating bill?" (thread 78383, opened 31 Jan 2014):
  the opening post quotes Puget Sound Energy, "Closing off the registers actually makes your system less efficient.
  ... closing the registers creates additional static pressure in the duct systems reducing the efficiency of the
  furnace and air handler"; replies "I have a spare bedroom that's not used so it gets the vent shut off, that
  redirects the heated air to the rest of the house and thus saves me money" and "everyone i know has always blocked
  off vents to rooms and levels that aren't being used to save money".
- The walls that store heat: [`radiatorCabinetTop`](../radiatorCabinetTop)'s `src/radLayerWall`. The buoyant model and
  the castellated room mesh: [`acLouvreAngle`](../acLouvreAngle) and [`doorwayFanStove`](../doorwayFanStove).

## How the case got here

**The solve.** Both runs were launched together at 12:41 UTC on 14 Nov 2026 on our own machine from rest, 8 ranks
each, one physical core a rank, after two 50-step tests of each. The first launch of the tests stopped before its
first step because the coded monitor did not compile (a bare `return` in a function returning a value); only the
monitor was changed, and both tests were run again from rest and passed, with the registers' flows and heat as
above. **Each run went straight through from rest to 300 s in one segment, with no restart**: one `Starting time
loop`, and the log ends in `End` at `Time = 300`. The runs took 22,953 (open) and 15,008 (closed) steps, 6,400 s
and 4,751 s of wall time on 8 ranks each, 3.2 h for everything with the meshing and the tests, within the 10 h we
allow a solve. The open run's steps are the shorter because the air leaving under the spare room's door sets them:
its cell of highest Courant number sits at the gap's east end, on the spare room's side, at every row checked from
30 to 300 s. The closed run's sits on the same 2.5 cm cells on the hall's side. The solved runs
carried an abort function object, read at each write, which was never used; it is left out here.

**A straight run with this case's `Allrun` is the same run**, but **it will not repeat the solved runs bit for bit**,
because scotch gives a different 8-rank decomposition on each call on our machine (25,040 cells on rank 0 in a
rebuild against the solved runs' 25,272), so parallel sums round differently, and in a turbulent buoyant flow that
round-off grows. The zone means of a rebuilt run should be expected to agree with these to a few hundredths of a
kelvin, not to the last digit. No rebuilt run was solved through.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI and `wmake`, and Python 3 with NumPy
(and SciPy for `scripts/ducts.py`).

    cd cases/closedRegister
    ./Allrun open                # [nProcs], default 8; compiles the wall condition and builds the mesh first
    ./Allrun closed              # default 8; start it once runs/mesh/ is built
    python3 scripts/extract_results.py runs results
    python3 scripts/ducts.py     # the duct calculation, as config/ducts.txt

The first `Allrun` compiles `src/storedLayerWall` into `$FOAM_USER_LIBBIN` and builds the shared mesh in
`runs/mesh/`: `scripts/make_mesh.py` writes the meshing dictionaries (`template/mesh/system/`) and the solids' STL,
then blockMesh, a serial snappyHexMesh of about ten seconds, `scripts/house_patches.py` (the patches, the openings'
face zones, and the cell centres for the starting pressure) and checkMesh. Then `scripts/make_case.py` writes
`runs/<run>/`: the mesh, `0/`, `constant/` and `system/` from `template/` and `config/case.json`, and the monitor from
`scripts/monitor.C`. `Allrun` writes the t = 0 planes, decomposes by scotch, solves from 0 to 300 s, and once both
runs have solved writes `results/`. The two runs differ only in `0/` and in the spare register's patch type in
`constant/polyMesh/boundary`. `./Allrun --setup-only <run> [nProcs]` stops before the solve; `./Allclean` removes the
runs. The solved runs took about 1.8 h (open) and 1.3 h (closed) on 8 ranks each.

Each run writes 481 times of 6 planes (VTK), the fields every 30 s and monitor files of about 1.3 MB. `results/`
holds the summary, the rooms and each run's history every 2.5 s; no fields, meshes, planes or logs.

The case was set up and solved by an agent on our own machine and checked by us. The files in `results/` are what
`scripts/extract_results.py` wrote from the solved runs' monitors; `config/ducts.txt` is what `scripts/ducts.py`
prints.

Checked from a clean copy of this folder on 15 Nov 2026, with the wall condition compiled into a scratch library
folder: `make_mesh.py`, blockMesh, snappyHexMesh and `house_patches.py` rebuild the solved mesh byte for byte (the
STL, and `points`, `faces`, `owner`, `neighbour`, `boundary`, `faceZones` and snappyHexMesh's level and zone files),
and `checkMesh` gives Mesh OK at 202,274 cells, non-orthogonality 25.2394° at most, skewness 0.333333.
`make_case.py` writes both runs' `0/`, `constant/` and `system/` byte for byte, but for the wall condition's name
(`storedLayerWall`, which the solved runs named with a number of ours), the library's path in `controlDict` and
`planesT0`, the names of the two coded objects, and the unused abort function object; the t = 0 planes are the
solved runs' byte for byte. The decomposition is not (above). Two serial steps of the open run from there gave the
solved run's time steps (0.6 and 0.71999712 ms) and its first-step initial residuals for Ux and h (1) and p_rgh
(0.9775697675 against 0.9775701865), and the second step's first Ux, h and p_rgh residuals to eight figures; the
later solves within a step differ from the second to the fourth figure, as a serial and a parallel solve do.
`scripts/extract_results.py` on the solved runs' monitors gives the study's own figures: the 8,086.15 and
7,664.80 W, the +0.537 and +0.682 K at head height, the 16.67 °C closed spare room, and the -0.022% and -0.005%
budgets. `scripts/ducts.py` prints `config/ducts.txt` unchanged.
