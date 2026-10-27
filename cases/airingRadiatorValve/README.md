# Airing a heated room: the radiator's valve turned off, or left on

German advice on airing a room in winter is to open the window wide for a few minutes and to
turn the radiator's thermostatic valve down while it is open. The Verbraucherzentrale's reason is
the valve: it reads the room's air, and as the cold air reaches it, it opens. This case takes
[`windowAiring`](../windowAiring)'s room on a still 0 °C morning, opens its window wide for five
minutes and then shuts it for ten, once with the valve turned off while the window is open and
once left on. The radiator under the window is sized for the room, behind a thermostatic valve,
and the room's walls, ceiling and floor store heat. The number it reports is **the heat the room
has lost since the window opened**, in watt-hours.

One OpenFOAM case, two runs that differ only in the valve during the five open minutes:

    ./Allrun off    # the valve shut from 0 to 300 s while the window is open, then set back, 0-900 s
    ./Allrun on     # the valve left at its setting throughout, 0-900 s

**On these assumptions, leaving the valve on while airing for 5 minutes costs about 1% more
heat over 15 minutes: 353 Wh lost against 348 Wh.** Turning the valve off saves little because
the radiator does not go off with it. Its body, 22.5 kJ/K of water and steel at 52 °C, keeps
giving the room 570-685 W through the five minutes with its valve shut, after its starting
546 W, against up to 800 W left on. Most of the extra heat the boiler puts in when the valve is
left on is not lost by the end: it is in the radiator's body, which the other run let cool, and in
the warmer room and walls.

It is one room, one five-minute airing on a still 0 °C day, with the valve and its lag as the
maker gives them. Read [What it cannot](#what-it-cannot) before any number here.

## The room, the window and the timing

| | value | from |
|---|---|---|
| room | 4.0 m from the window wall to the inner wall, 3.5 m wide, 2.4 m high, 33.6 m³ | windowAiring |
| window | a clear opening 1.0 m wide and 1.2 m tall, sill 0.90 m up, centred, at the inside face of a 24 cm wall; the sash turned wide open at 90° on its hinge side (a baffle) | windowAiring's `open` |
| outside | still air at 0 °C, 1.5 m deep beyond the wall, open on every face, holding its own barometric pressure, p0 = 1e5 exp(−g y/(R T)) | windowAiring; the barometric form roofWindowAiring's and the double-hung runs' |
| start | the room's air at rest at 20 °C in that pressure; the walls at 20 °C, the window wall in its steady state; the radiator steady at its design output; at t = 0 the window opens | ours |
| shut | at 300 s the window shuts: the outside air is dropped, the opening becomes double glazing, U = 2.8 W/m²K to 0 °C (h = 4.403 W/m²K, the inside film left to the solver), and the room carries on to 900 s | radiatorUnderWindow, underfloorVsRadiator |

`off` turns the valve shut as the window opens and sets it back as the window shuts, which is
what the advice says to do. `on` leaves it alone. Nothing else differs.

## The radiator and its valve

`scripts/design.py` writes these numbers (`results/design.json`) into each run's
`constant/fvOptions`.

| | value | source |
|---|---|---|
| radiator | the box under windowAiring's window, a Stelrad Softline Compact K1 600 × 1000: 980 W at 75/65/20 °C (ΔT 50 K), n = 1.29 | Stelrad's EN 442 table |
| heat capacity | 22.5 kJ/K: 3.25 l of water and 19.70 kg of steel at 450 J/kg K | same table |
| design heat loss | 546 W on a 0 °C day at 20 °C: 366 W through the window wall's opaque 7.2 m² (U = 2.54 W/m²K), 67 W through the glazing's 1.2 m² (U = 2.8), and 113 W for EN 12831's minimum air change of 0.5 an hour. The other walls, the floor and the ceiling face heated rooms | EN 12831 style; EN ISO 6946's surface resistances, 0.13 and 0.04 m²K/W |
| water | 57.0 °C flow and 47.0 °C return at the design loss, a nominal flow of 46.9 kg/h | the K1's EN 442 output at 546 W with a 10 K drop |
| valve | proportional, shut with the head at 22 °C and at its nominal flow at 20 °C (setting 3, Xp = 2 K), opening on to 1.23 times the nominal flow (kvs 0.90 against kv 0.73 m³/h at Xp = 2 K) | Danfoss RA 2000 data sheet; RA-N DN 15 |
| head | gas-filled, time constant 10 min; at (0.10, 0.69, 0.57) m, on the valve beside the radiator's top corner, reading the mean air over the 16 cells within 4 cm | Danfoss |
| model | the head lags the air at its position by its time constant; the valve's flow follows the head; the radiator is one lumped body, heated by its water through an effectiveness 1 − exp(−KA/(c q)) and giving Q50 (ΔT/50)^n to the room's mean air | Xu, Fu and Di (2007), eqs 4-14 |

There are no gains to tune: the band and the flows are the valve maker's, and the head's 10 min
and the body's 22.5 kJ/K are the loop's damping. At full flow the radiator gives 565 W into 20 °C
air, 662 W at 15 °C and 801 W at 8 °C. With its valve shut its body cools with a time constant of
about 17 min. A liquid-filled head reacts more slowly than this gas-filled one: DIN CERTCO's
EN 215 data sheet for one gives a response time of 28 min.

The radiator's heat goes to the air in its box, through which the air passes as through a
convector's fins (fv option `trvRadiator`), all of it, the radiant share included.

## The walls, the leaks and the radiation

- **Every room surface stores heat.** Each face of the floor, ceiling and walls carries its own
  1-D conduction layer, solved implicitly with the air each step (T's boundary condition
  `wallLayer`): 13 mm of dense plaster (1300 kg/m³, 0.57 W/m K) on medium-density concrete
  (1800 kg/m³, 1.13 W/m K), the floor bare cast concrete (2000 kg/m³, 1.35 W/m K), all at
  1000 J/kg K, in cells of 1 mm to 30 mm and 5 mm after. The floor, the ceiling, the inner wall
  and the side walls go 150 mm deep, their backs held at 20 °C by the rooms next door. In 15
  minutes heat reaches about 2-3 cm into these materials, so 150 mm behaves as any thickness
  would. The reveal, the wall's outer face and the sash are adiabatic and store nothing.
- **The window wall conducts to the outdoor air.** Its opaque 7.2 m² goes through its whole
  24 cm, 13 mm of plaster on 227 mm of concrete in 72 cells, the back through EN ISO 6946's
  external surface resistance, 0.04 m²K/W, to 0 °C. It starts in its steady state with 20 °C
  inside and the internal resistance 0.13 m²K/W: 50.8 W/m², the inner surface at 13.4 °C, and
  365.8 W out of the back. In 15 minutes the room's changes reach only the first few centimetres
  of the concrete, so the back loses 365.8 W throughout, whatever the room does.
- **The leaks.** EN 12831's minimum air change for a living room, 0.5 an hour, as a sink on the
  room's air, 0.5/3600 ρ c_p (T − 0 °C) in every room cell (fv option `infiltration`): 111 W from
  the room at 20 °C, less as it cools. While the window is open it adds under 3% to what the
  opening loses.
- **Radiation onto the window wall.** EN ISO 6946's internal resistance of 0.13 m²K/W, on which the
  366 W rests, is convection and radiation together. The CFD gives the convection, about
  2.6 W/m²K on this wall, close to the 2.5 the standard takes, and nothing else. So the window
  wall's inner face also takes h_r (T_mrt − T_face), with h_r = 0.9 × 4σ(293.15 K)³ = 5.14 W/m²K
  (an emissivity of 0.9) and T_mrt the area-weighted mean temperature of the room's other
  surfaces. The same heat is taken out of the room's air evenly by volume (fv option
  `windowRadiation`), since the model gives the air all the radiator's heat. 1/(2.6 + 5.14) is
  the standard's 0.13. It is about 250 W throughout. No other surface exchanges radiation.

## The model

`scripts/make_case.py <run> <dir>` writes every dictionary, the initial fields and the run's own
Allrun. Underneath is windowAiring's generator, `../windowAiring/scripts/make_case.py`, run
`open`, called through its own functions: the mesh, the zones, the fields, the air, the
turbulence model, the schemes and the solution settings are its. `src/airingLoss` is the library
the runs load: the boundary condition `wallLayer`, the fv options `trvRadiator`, `infiltration`
and `windowRadiation`, and the function object `airingBudget`. `../Allrun` compiles it with
`wmake` into `$FOAM_USER_LIBBIN`.

- **Solver:** buoyantPimpleFoam (OpenFOAM v2512), air as a perfect gas (c_p 1005 J/kgK,
  μ 1.82e-5 Pa s, Pr 0.71), k-omega SST with the buoyancy source on k, wall functions, PIMPLE
  with 2 outer and 2 pressure correctors, Euler in time at Courant 1, windowAiring's schemes.
- **Mesh:** windowAiring's wide-open mesh, 526,848 cells over the outside air, the reveal and the
  room, the sash a baffle; `checkMesh` OK, no non-orthogonality, largest aspect ratio 27.6.
- **The window shuts at 300 s** (`scripts/close_window.py`). The solve stops at 300 s, the sash's
  baffle is merged and the mesh cut down to the room's 372,504 cells with subsetMesh; the faces it
  exposes in the window's frame become the glass. Nothing is interpolated: every kept cell's
  values, volume and centre and all 72 arrays of the wall layers are checked identical before and
  after, and they were in both runs. The shut room is closed, so its pressure reference is set to a
  kept cell's own centre and 300 s pressure, in the room's far upper corner, 1.57 m off the clip's
  section, and the restart adds no jump. The radiator, its body and its head carry on from their
  300 s state. The shut stage runs 300-900 s.
- **The room's own air** is windowAiring's passive scalar s, 1 in the room at the start.
- **The heat lost** since the window opened is the room's whole heat bill: the radiator's heat to
  the air so far, less the change in the heat in the room's air (its internal energy above 0 °C)
  and in the wall layers (each face's from its starting profile). The rooms next door give the
  layers' backs under 0.001 Wh. It includes the heat the room loses with its window shut too:
  91.4 Wh through the window wall's back and 20-21 Wh through the leaks over the 15 minutes. It
  is checked against what crosses the room's boundary, step by step: the enthalpy carried out
  through the opening and the heat diffused across it, then the glass, the wall's back and the
  leaks.
- **Monitors, every step** (`airingBudget`, `trvRadiator`): the room's mass, mean temperature and
  mean s, ∫p dV and its internal energy, the gross mass flow each way through the frame's plane
  and the enthalpy and diffusion through it, the heat through each group of surfaces, the layers'
  stored heat, the glass, the wall's back, the leaks and the radiation; the head's air and its own
  temperature, the valve's flow, the body's temperature, its output and the water's heat. Planes
  for the clip every 1.25 s while open and every 2.5 s once shut: the section through the middle
  of the window and the radiator (z = 0.005 m) and a floor plane 0.1 m up; the walls' surface
  temperature every 7.5 s.

## How the case got here

The first version had windowAiring's radiator, 60 W with no valve. It made leaving the radiator on
cost almost nothing, about 3 Wh of 238 Wh by 900 s, because 60 W is about a tenth of what this
radiator gives at a normal water temperature, so the radiator was resized for the room and put
behind a valve. The first version with the valve had no steady losses: the window wall was
adiabatic at its back and nothing leaked, so the 546 W radiator heated a sealed room. Both rooms
ended warmer than they started, 21.3 °C (off) and 22.2 °C (on) ten minutes after the shut. The
wall's conduction to outside and the leaks were then put in, and a pilot of the shut room from
rest at 20 °C, with the valve at its steady opening, checked that the sized radiator now held it.
It did not: the room warmed, 20.44 °C at 100 s and still rising 0.18 K a minute, because the air
gave the window wall only 125-145 W by convection and the wall's stored heat made up the rest of
the 366 W its back loses. With the radiation onto the window wall added, on the same mesh, fields
and decomposition, the air gave the wall about 360 W and the room held within half a kelvin: 19.58
°C at 180 s, its cooling easing to 0.11 K a minute as the valve opened, the radiator giving
555 W against 539 W lost to outside. What remained of that drift was the ceiling taking heat from
the warm layer the radiator's plume lays under it, as a ceiling that starts at 20 °C does. Only
the runs with the steady losses and the radiation are here; none of the earlier runs or pilots is
kept.

## Checks

- **The generator against the solved runs.** From a clean copy, `./Allrun --setup-only off` and
  `--setup-only on` compiled the library and wrote the solved runs' mesh (points, faces, owner,
  neighbour, boundary, cell, face and point zones) and every initial field in `0/` byte for byte,
  526,848 cells, `checkMesh` OK. `system/` is the same byte for byte, and `constant/` too but for
  two comment lines in `fvOptions`. The t = 0 planes are byte for byte those of the 60 W version,
  whose initial air is the same. The decomposition was not compared. Two steps of `on` from the
  setup, on one rank, gave the solved run's first-step radiator output, wall-back loss, leaks and
  radiation to seven or more figures.
- **The heat budget closes.** From 30 s on, the heat lost and what crossed the boundary agree to
  within 0.073% at every step in both runs, and to 0.05% at 900 s.
- **The switch kept the state.** In both runs every kept cell's values, volume and centre, all 72
  layer arrays and the room's internal energy were identical before and after the window shut.
- **The window wall's back** gave 365.8 W at every step in both runs, as designed.
- **The valve is smooth.** In `on` it changes direction four times in the first 4.3 s, every
  time within 0.4% of its nominal flow, as warm and cold puffs reach the head, then opens steadily
  to its stop at 1.23 times the nominal flow by 52 s and stays there to 900 s. Its largest change
  in a step is 1.3e-4 of the nominal flow. In `off` it moves only when it is turned, and is at its
  stop from 300 s. The head, lagging 10 min, falls to about 16 °C by the shut and is at 14.9-15.2 °C
  at 900 s, below the 19.5 °C at which it would begin to close from its stop, so the valve never
  throttles.
- **Both runs ended cleanly** at 900 s, in 38,854 steps (`off`) and 41,675 (`on`), the largest
  0.043 s.

## Results

From `results/summary.txt` and `results/<run>/history.csv`, which `scripts/extract_results.py`
writes from the runs' per-step monitors.

| | valve turned off while open | left on |
|---|---:|---:|
| heat lost by 300 s, as the window shuts | 263.3 Wh | 265.8 Wh |
| heat lost by 900 s, ten minutes after shutting | 348.1 Wh | 352.5 Wh |
| of which out of the walls, ceiling and floor, by 900 s | 199.8 Wh | 180.5 Wh |
| heat the radiator gave the air by 300 s / 900 s | 54.1 / 137.2 Wh | 62.2 / 167.9 Wh |
| heat the boiler's water gave the radiator by 900 s | 103.8 Wh | 168.2 Wh |
| radiator's body at 300 s | 43.1 °C | 51.6 °C |
| room's mean air at 300 s / 900 s | 8.5 / 17.9 °C | 8.8 / 18.7 °C |
| room's own air replaced by 300 s | 92.4% | 92.5% |

**Leaving the valve on cost 2.5 Wh more by 300 s and 4.4 Wh more by 900 s,** 0.9% and 1.3% of
the bill. Through the first minute the two runs are the same to 0.1 Wh. Of the 352.5 Wh the
left-on room lost by 900 s, 229.8 Wh left through the open window, 91.4 Wh through the window
wall's back, 20.8 Wh through the leaks and 10.3 Wh through the glass once shut; the extra 4.4 Wh
went out of the window (2.4 Wh), the glass (1.1 Wh) and the leaks (0.8 Wh), because the left-on
room was a little warmer.

**Why turning the valve off saves so little.** The valve stops the water, not the radiator. Its
body holds about 200 Wh above the room at 52 °C, and as the room's air cools around it, it gives
more, not less: 611 W at 30 s with the valve shut, rising to 685 W at 120 s and still 609 W at
300 s, never under its starting 546 W in the five minutes. Left on, the valve opens to its stop
and the radiator gives 629 W at 30 s, 780 W at 150 s and 802 W at 300 s. So in the five open
minutes the shut radiator gives 54 Wh and the open one 62 Wh, and what the left-on room gains is
partly carried out of the window and partly kept.

**Where the boiler's extra heat went.** Left on, the water gave the radiator 64.4 Wh more by
900 s. Of that, 33.7 Wh is in the radiator's body, which in `off` cooled to 43 °C while the
window was open and is still at 46.4 °C at 900 s, against 51.8 °C; 19.3 Wh is in the walls, which
gave up less; 7.0 Wh is in the room's air, 0.9 K warmer; and 4.4 Wh was lost. The heating makes
most of that up for `off` after 900 s, as its body and walls warm back, which is why the heat
lost, not the boiler's heat by 900 s, is the bill.

**The rooms recover.** Both rooms bottom out as the window shuts, 8.5 °C and 8.8 °C mean air,
and are back to 17.9 °C (`off`) and 18.7 °C (`on`) by 900 s, still warming about 0.3 K a minute.
The walls, ceiling and floor gave 121 and 117 Wh by 300 s and 200 and 181 Wh by 900 s: most of
what warms the air back after the shut comes out of them.

## What the clip shows, and what it does not

**It shows** the section through the middle of the window and the radiator, valve turned off
above and left on below, from the moment the window opens: the five open minutes at 30× real
time and the ten shut at 60×, so each takes half of the 20 s. Temperature is on one scale for
both, 0-24 °C with the room's starting 20 °C green in the middle, and air parcels are carried by
the solved flow on the section. The window (open, then shut), the radiator and its valve ('off',
'on'), the wall and the outside are drawn. Once shut, the outside is no longer solved and is
drawn at its 0 °C. The number on each strip is the heat lost so far, in whole Wh.

**While the window is open the two strips look alike,** because the shut radiator keeps heating.
The heat lost in the two rooms is within 1 Wh until 245 s, eight seconds into the clip, so the
two whole-Wh counts read the same or one apart until then. The left-on room's warmer layer under
the ceiling shows after the shut.

**It does not show** anything off the section. The run is 3-D, but the picture is one vertical
section, so it looks like a 2-D room; the heat lost and the temperatures in the tables are the
whole room's.

## What it cannot

- **One room and one airing.** One 33.6 m³ room with one window, wide open for five minutes on a
  still 0 °C day, then shut. A longer airing, a colder or windy day, a larger window or a cross
  draught would change how much air goes and how cold the room gets, and so the radiator's share.
  No wind, no furniture, no people, no humidity, the door shut.
- **Fifteen minutes.** Both rooms are still recovering at 900 s, about 0.3 K a minute, and the
  heat the walls and the shut radiator have to make up is made up after the runs end. Hours of
  airing, tilted windows, condensation and mould are not here.
- **One valve and one radiator, as the maker gives them.** A Danfoss RA 2000 gas-filled head
  (10 min) on an RA-N valve at setting 3, proportional over 2 K, on a K1 sized for exactly the
  design loss with 57/47 °C water. A slower liquid head, another setting, an oversized radiator, a
  hotter flow or a valve that is turned fully off rather than to a closed setting would give
  other numbers. The radiator is one lumped body with one temperature, and its heat goes to the
  air in its box.
- **Steady losses from a design calculation.** The window wall conducts to 0 °C from its steady
  profile and the leaks are EN 12831's minimum 0.5 an hour, the values the radiator is sized
  for, not a measured room. The other walls, the floor and the ceiling face rooms held at 20 °C.
- **Radiation only onto the window wall,** from the room's other surfaces as one mean
  temperature, taken out of the air. The radiator's radiant share, the glass and every other
  surface exchange heat with the air alone.
- **A 2-D-looking picture of a 3-D run,** as above.
- **One mesh, unsteady RANS,** k-omega SST with wall functions, no mesh or time-step study, one
  realization of each run. The two runs differ by about 1%, and their flows are not the same
  eddy by eddy.

## Sources

- Umweltbundesamt, "Richtiges Heizen schützt das Klima und den Geldbeutel": "Heizkörper bei
  geöffnetem Fenster abdrehen":
  https://www.umweltbundesamt.de/umwelttipps-fuer-den-alltag/heizen-bauen/heizen-raumtemperatur
- Verbraucherzentrale, "Heizkosten sparen: Thermostat richtig einstellen und wechseln" (16 Feb
  2026): "Drehen Sie das Ventil ganz zu, wenn Sie zum Lüften kurzzeitig das Fenster öffnen":
  https://www.verbraucherzentrale.de/wissen/energie/heizen-und-warmwasser/heizkosten-sparen-thermostat-richtig-einstellen-und-wechseln-7940
- Stelrad, Softline Compact, EN 442 output table (980 W at ΔT 50 K, n 1.29, kg and litres per
  metre): https://www.stelrad.com/wp-content/uploads/2015/04/Softline-Compact_Web-OCT-19.pdf
- Danfoss, Data Sheet, Thermostatic Sensors Type RA 2000 (VD51A602): the scales stated at
  Xp = 2 °C, the sensor closing 2 °C above the scale, setting 3 at 20 °C; RA-N kv and kvs.
- Danfoss Spain, "The inner workings of the thermostatic radiator valve" (the RA 2000's gas
  reacting in 10 minutes):
  https://www.danfoss.com/es-es/about-danfoss/news/dhs/the-inner-workings-of-the-thermostatic-radiator-valve/
- DIN CERTCO, EN 215 data sheet 011-6T0040 (a liquid head's response time, 28 min):
  https://www.dincertco.de/logos/011-6T0040.pdf
- Xu Baoping, Fu Lin and Di Hongfa, "Simulation on hydraulic heating system of building under
  the control of thermostat radiator valves", Building Simulation 2007, eqs 4-14:
  https://www.aivc.org/sites/default/files/p824_final.pdf
- EN 12831, minimum air change of 0.5 an hour for living rooms (its Table 8), as quoted by
  haustechnikdialog.de: https://www.haustechnikdialog.de/SHKwissen/1306/Mindestluftwechsel
- ISO 6946:2007, Table 1, surface resistances: 0.13 m²K/W inside for horizontal heat flow,
  0.04 m²K/W outside (the standard's public preview pages).
- Scottish Government, Technical Handbook 2020, Domestic, Table 6.A.18 (densities and
  conductivities of dense plaster, medium-density concrete and cast concrete):
  https://www.gov.scot/publications/tables-of-u-values-and-thermal-conductivity/
- The room, the window, the glass and their sources: [`windowAiring`](../windowAiring),
  [`radiatorUnderWindow`](../radiatorUnderWindow) and
  [`underfloorVsRadiator`](../underfloorVsRadiator).

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI and `wmake`, and Python 3
with NumPy. The case uses `../windowAiring/scripts/make_case.py`, so keep the two side by side.

    cd cases/airingRadiatorValve
    ./Allrun off                     # [nProcs], default 16
    ./Allrun on
    python3 scripts/extract_results.py runs results

`Allrun <run>` compiles `src/airingLoss` into `$FOAM_USER_LIBBIN` (if it is not up to date),
writes the run into `runs/<run>/` with `scripts/make_case.py` and runs the Allrun written there:
blockMesh, subsetMesh to the air, the outer walls as a patch, the sash as a baffle, the zones, the
initial fields, the barometric pressure and the wall layers' boundary condition
(`initial_fields.py`), checkMesh, the t = 0 planes and decomposePar. It then solves the open
stage, 0-300 s, shuts the window (`scripts/close_window.py`) and solves the shut stage,
300-900 s, writing the fields every 60 s (the last one kept), and, once both runs are there,
writes `results/`. `./Allrun --setup-only <run>` stops before the solve, in about a minute.
`./Allclean` removes the runs and the library's build files.

Each run took about 5.2-5.4 h of wall time on 16 ranks alone, 1.7-1.8 h open and 3.5-3.6 h shut,
and writes about 0.4 GB of planes. The solved runs had rank 0 write its own log
(`scripts/rank0log.sh`), after one launch through mpirun's output relay ran at an eighth of its
speed on our machine. `results/` holds each run's history every 2.5 s (the room's air, the
radiator, valve and head, every heat flow and the running totals) and the summary; no fields,
meshes, planes or logs.

The case was built, checked and solved by an agent on our own machine, and sent back twice: once
for a radiator sized for the room behind a valve, in place of the 60 W one, and once for the
steady losses the first valve runs lacked.
