# Warm air from a ceiling vent against a floor register under the window

Most American houses are heated by forced air from a furnace, and where the ducts run decides
where the warm air comes in: through a register in the ceiling when the ducts are in the attic,
through a register in the floor under the window when they are in a basement. This case blows
the same furnace air into the same bedroom on a 0 F night from each place, for the first five
minutes after the furnace comes on, and asks how warm the air is at your ankles. It is about
where the heat goes in the room, not about the heating bill, duct losses or the furnace.

    ./Allrun floor       # a floor register under the window, 0-300 s from switch-on
    ./Allrun ceiling     # a ceiling register near the inner wall, blowing towards the window

**The result.** Both rooms start at 68 F (20 C). After five minutes the air at the ankles,
0.1 m above the floor in the occupied zone, is **74.0 F (23.3 C) with the floor register and
63.4 F (17.4 C) with the ceiling vent**. The two rooms get the same heat and lose almost the
same heat through the glass, but the ceiling vent's room keeps its warm air above head height,
puts 46% of the supplied heat into the gypsum ceiling, and lets the cold air off the glass lie
along the floor; the floor register's jet meets that cold air at the window and the room turns
over as one loop. The limits below say why this is a 2-D section over five minutes, with
slots across the room for registers, and not a measurement of a real bedroom.

The room is [`radiatorUnderWindow`](../radiatorUnderWindow)'s 2-D section, its window and its
glass, with the radiator taken out. It is a case of its own: the heat comes in with the air
through a slot, the floor, the ceiling and the inner wall are layers that store heat instead of
walls held at 20 C or adiabatic, the room has a door, and the mesh is its own. None of
`radiatorUnderWindow`'s runs changes.

## The room

`radiatorUnderWindow`'s section: 4.0 m from the window wall to the inner wall, 2.4 m (8 ft)
high, 1 m deep. Every heat and flow below is per metre of section.

- **The glass**, y = 0.90 to 2.10 m on the window wall, loses heat to 0 F (255.37 K, -17.8 C)
  outside air through h = 4.403 W/m2K outside and the solver's own inside film
  (`externalWallHeatFluxTemperature`), U = 2.8 W/m2K as in `radiatorUnderWindow`, ordinary
  air-filled double glazing. 0 F is Chicago O'Hare's 99% heating design temperature, the night
  ACCA Manual J sizes a furnace for. The outside air is still.
- **The rest of the window wall** is adiabatic.
- **The floor** is a 3/4 in (19 mm) wood floor, and **the ceiling and the inner wall** are 1/2 in
  (12.7 mm) gypsum board, each a 1-D layer of 24 cells with its heat capacity, starting at 20 C
  with an adiabatic back (`bedroomLayer`, `src/bedroomLayer/wallLayer.C`): wood k = 0.106 W/m K,
  rho = 656.8 kg/m3, cp = 1884 J/kg K; gypsum k = 0.1587 W/m K, rho = 640.7 kg/m3,
  cp = 1130 J/kg K (California Energy Commission). Over five minutes the heat soaks about 8 mm
  into gypsum and 5 mm into wood, so what lies behind them does not matter. This matters for the
  ceiling vent: a ceiling held at 20 C would draw the warm air's heat off as fast as it came, and
  one with no heat capacity would take none.
- **The door**: the bedroom door's 1 in undercut, a 25 mm slot at the foot of the inner wall
  (`undercut`, x = 4.0 m, y = 0 to 0.025 m), onto the hall's still 20 C air at its hydrostatic
  pressure (`prghTotalPressure`). The air leaves at whatever rate the supply pushes it out; none
  came back in in either run.
- **The start**: the air at rest at a uniform 20 C, the pressure hydrostatic with 1e5 Pa at
  y = 1.174 m (`bedroomTools -prepare`). At t = 0 the glass sees 0 F and the furnace starts.

## The two registers

The supply is the same in both runs: **100 CFM at 117 F**. A Goodman ADSH80 two-stage furnace
moves 909 CFM with a 49 F rise on its medium-low speed, so with the return at 68 F the air
leaves it at 117 F (320.37 K, 47.2 C); 100 CFM, 11% of that, is a common register rating. In
2-D a register becomes a slot across the whole section, so each slot gets the room's 100 CFM
spread over a 12 ft (3.66 m) wide room, **0.012903 m3/s per metre**, at its register's own
velocity, ramped up linearly over the first 2 s as a blower does. The room keeps its real air
change, about 4.8 an hour, and its real heat per cubic metre.

- **`floor`**: a TRUaire 157 floor register, 4 x 10 in, 100 CFM at 600 fpm (3.05 m/s) through
  24 sq in of free area. Its slot, `floorSlot`, is that free area over 3.66 m: 4.2 mm wide,
  x = 0.1479 to 0.1521 m, its centre 0.15 m from the window wall, blowing **straight up** at
  0.012903/0.0042 = 3.072 m/s.
- **`ceiling`**: a TRUaire 301 curved-blade ceiling register, 10 x 6 in, 100 CFM at a face
  velocity of 500 fpm (2.54 m/s). Its slot, `ceilingSlot`, is 7.2 mm wide, x = 3.5464 to
  3.5536 m, its centre 0.45 m from the inner wall, blowing **45 degrees down towards the window**
  at 2.534 m/s (1.792 m/s each way). The 45 degrees is ours.

Both slots are in both runs' mesh; in each run the one not in use is a wall with the layer of
its surface. The catalogues give the two registers about the same throw at 100 CFM, 9 and
8.5 ft.

## The model

- `buoyantPimpleFoam` (OpenFOAM v2512), air a perfect gas (28.96 kg/kmol, cp 1005 J/kg K, mu
  1.82e-5 Pa s, Pr 0.71), k-omega SST with the buoyancy production term in k
  (`buoyancyTurbSource`), wall functions on every wall; schemes and solvers from
  `radiatorUnderWindow`. No radiation.
- **Mesh**: `scripts/make_mesh.py` writes a graded blockMesh of the section, one cell thick:
  405 x 251, **101,655 cells**, the same in both runs. 5 mm at the window wall, 1.05 mm across
  the floor slot and 1.8 mm across the ceiling slot (four cells each), widening to 20 mm between
  x = 1 and 3 m; 2.5 mm in the lowest 25 mm (ten cells up the undercut), 10 mm to the glass,
  12 mm up it and 3 mm at the ceiling. `checkMesh`: Mesh OK, no non-orthogonality, largest
  aspect ratio 11.6.
- **Time step**: Courant number at most 1, **one outer corrector** and two pressure correctors,
  the p_rgh solve to **1e-7** (see "How the case got here"), the pressure reference in the
  middle of the room. The floor run took 389,126 steps and the ceiling run 549,076; in both the
  step is set by the cell at the supply slot.
- **Output**: `bedroomMonitor` (`src/bedroomLayer/bedroomMonitor.C`) writes the heat budget at
  every step to `postProcessing/monitor/*/budget.csv` and the zones every 0.625 s to
  `zones.csv`; the mid-plane section (T, U) every 0.625 s to `postProcessing/clip`; the fields
  every 30 s, the last two kept.

### The number

The air temperature at the ankles is the occupied zone's mean at 0.1 m above the floor, the
ankle height of the vertical-gradient criterion in ISO 7730 and EN 16798-1, over x = 1.0 to
3.7 m, ASHRAE 55's occupied zone in this section (more than 1.0 m from the window and 0.3 m
from the inner wall), each cell weighted by its overlap with the line. The monitor writes it
with the knee (0.6 m), seated head (1.1 m) and standing head (1.7 m) the same way.

## Results

`scripts/extract_results.py` writes, from the two runs' monitors, `results/summary.txt`,
`results/minutes.csv` and each run's history every 0.625 s, `results/<run>/history.csv`.

The air at the ankles:

| | 0 s | 30 | 60 | 120 | 180 | 240 | 300 |
|---|---:|---:|---:|---:|---:|---:|---:|
| floor register, F | 68.0 | 68.0 | 69.7 | 70.9 | 71.8 | 72.7 | **74.0** |
| ceiling vent, F | 68.0 | 65.3 | 64.9 | 63.8 | 63.4 | 63.3 | **63.4** |

At 300 s, in the occupied zone:

| C | ankle 0.1 m | knee 0.6 m | seated head 1.1 m | standing head 1.7 m | room mean |
|---|---:|---:|---:|---:|---:|
| floor register | 23.3 | 24.1 | 24.6 | 24.7 | 24.5 |
| ceiling vent | 17.4 | 19.6 | 20.2 | 27.6 | 23.7 |

Where the supplied heat is at 300 s, kJ per metre and share of what was supplied:

| | supplied | the air | glass | floor | ceiling | inner wall | out under the door |
|---|---:|---:|---:|---:|---:|---:|---:|
| floor register | 114.8 | 50.6 (44%) | 31.9 (28%) | 8.2 (7%) | 11.7 (10%) | 3.9 (3%) | 8.5 (7%) |
| ceiling vent | 114.7 | 40.2 (35%) | 32.1 (28%) | -6.4 (-6%) | **52.9 (46%)** | 3.0 (3%) | -6.7 (-6%) |

"The air" is the rise of the air's internal energy above 20 C plus the flow work of the air
the room pushes out under the door as it warms; "out under the door" is the enthalpy above
20 C the leaving air carries, so a negative figure means it leaves colder than 20 C. A negative
wall has given heat up to the air.

**The ceiling vent.** In the sections the jet runs along the ceiling to the window wall and the
warm air stays high: at 300 s the air across the occupied zone is 34 C just under the ceiling,
24 C at 1.5 m and 20-21 C at 1.1-1.3 m. The gypsum ceiling under that layer has taken in
52.9 kJ, 46% of the supplied heat. The cold air falling off the glass spreads along the floor:
at 300 s the occupied zone is 17.5-18 C from just above the floor to about 0.4 m. The ankles
fall below
63.5 F at 169 s, reach 63.2 F at 232 s and stay there; the wood floor gives 6.4 kJ to the cold
layer, and the air that leaves under the door is that layer, 6.7 kJ colder than 20 C air.

**The floor register.** In the sections the jet rises along the wall below the sill, meets the
cold air coming down the glass at the sill and leaves the wall diagonally into the room, which
turns over as one large loop. At 300 s the ankles are within 1.4 C of a standing head and 73% of
the air's heat gain lies below 1.8 m (16% in the ceiling vent's room). The ankles are still
warming, 1.3 F over the last minute. Neither room has settled at 300 s; that is the furnace's
on-cycle on a design night, after which a thermostat would stop it.

**The glass** loses about the same in both runs, 31.9 and 32.1 kJ. The coldest air sits in the
cell at the glass's foot (x = 0.0025 m, y = 0.906 m); in the floor run it dips to -4.9 C at
60 s, where the jet leaves the wall below it, and recovers to 6.1 C by 300 s, 1 m from the
occupied zone.

**The heat budget closes.** With h_s = cp (T - 20 C), the open room's balance is
H_in - H_out - Q_glass - dE_layers = dE_s - R T0 dM + dKE - K_in + K_out - W_gravity, each flux
summed over the steps as the solver integrates (`scripts/extract_results.py`). Over 0-300 s it
closes to -2.8 J, **-0.0024%** of the 114.76 kJ supplied (floor), and -312 J, **-0.27%** of
114.73 kJ (ceiling). The ceiling run's residual is steady at -0.8 to -1.6 W/m over every
2.5 s from its first seconds, against about 380 W/m supplied, as in the pilots with the
original settings; the floor run's stays within 0.3 W/m. Both solves end in `End` at 300 s;
the floor run bounded nothing, and the ceiling run held k at its 1e-15 floor in some cells in
many steps from 129 s on.

## How the case got here

The case was set up by a local OpenReynolds agent from a written brief and
`radiatorUnderWindow`'s files: the mesh generator, the setup script, the wall layer, the
monitor and the pressure tool are its own (`scripts/make_mesh.py` and `scripts/make_case.py`
are its scripts, tidied, writing the same files). Before any solve it ran a layer test, the
floor and ceiling layers under air held at 40 C for 60 s: the heat taken in matched the heat
stored to 1e-10, and the surface rise came within 4.2-4.3% of a semi-infinite solid's. Its
driver tested for a solver log ending in `End`, which a parallel log does not (it ends
`Finalising parallel run`), and was corrected before anything solved.

Its 10 s pilots, 8 ranks each side by side, with `radiatorUnderWindow`'s two outer correctors
and the p_rgh solve to 1e-8, projected 14.0 h (floor) and 21.1 h (ceiling) for 300 s, over our
10 h limit. Five variants were tried on copies. **One outer corrector and the p_rgh solve to
1e-7**, nothing else changed, projected 5.1 h and 8.3 h; its planes matched the pilots' to
0.015-0.036 K rms at 5 and 10 s and its budgets closed as theirs did (-0.038% and -0.419% over
0-10 s). A coarser mesh moved the ceiling jet and was dropped; Courant 2, matching to
0.0035 F at 20 s, was not used, because `radiatorUnderWindow` measured a heat loss at Courant 5.
Production ran from rest with those settings on 28-29 Oct 2026, both runs side by side on 8
ranks each, in one go: 4.27 h (floor) and 5.60 h (ceiling). The pilots' settings are not in
this case.

## What the clip shows, and what it does not

The clip shows the two sections one above the other, the floor register on top, from
switch-on, 300 s at 15 times real time, coloured by air temperature on one scale from 52 to
84 F with moving air parcels, and the ankle temperature live in whole F on each panel. Each
register is drawn over its real width with "117 F, 100 CFM" and an arrow the way it blows; the
solved slot is inside it. The clip says the vents are slots across the room.

## What it cannot

- **A 2-D section.** The registers are slots across the whole section with the room's 100 CFM
  spread along them. A real 10 in register's jet spreads sideways and slows sooner; a plane jet
  does neither, so these jets reach farther than a real register's.
- **A 2-D jet clings to the wall.** A plane jet next to a wall has no air coming in round its
  ends, so the wall pulls it on (the Coanda effect) more strongly than a real register's jet:
  the floor jet runs up the wall below the sill, and the ceiling jet along the ceiling. Where
  the floor jet leaves the wall, at the sill, is set by the cold air off the glass; a real
  register's jet may leave sooner.
- **The ceiling register's 45 degrees** is ours and generous to it: a curved-blade register
  throwing along the ceiling, as it is designed to, keeps its air higher.
- **The same 117 F at both registers.** Ducts in an attic lose more on the way to a ceiling
  register than ducts in a basement do on the way to a floor one, so equal temperatures favour
  the ceiling vent.
- **No radiation.** The cold glass, the warm ceiling and the floor exchange no heat by
  radiation; the warm ceiling would warm the floor and the people a little.
- **The thermostat and the cycle.** The furnace runs flat out for five minutes from a room at
  68 F; a real one cycles, and its fan may run on.
- **Only the glass loses heat outside.** The other surfaces store heat and lose none behind.
- **No furniture, people, open door, wind or air leaks.**
- **One mesh, URANS, one realization each**, no mesh study; k-omega SST with wall functions.
  The production settings, one outer corrector and the p_rgh solve to 1e-7, were checked
  against the original settings over the first 10 s only.

## Sources

- University of Wisconsin State Climatology Office, "Engineering Weather Data",
  Chicago/O'Hare IL, WMO 725300 (0 F, the 99% heating design temperature), read 28 Oct 2026.
- Goodman ADSH8 specification sheet, "Airflow Data" (ADSH80 0603: 909 CFM, 49 F rise),
  apps.goodmanmfg.com, read 28 Oct 2026.
- TRUaire, "Performance Data, 157 Delux Floor Register" and "Performance Data, 301
  Wall/Ceiling Register" (100 CFM, face velocities, free area, throw), read 28 Oct 2026.
- California Energy Commission, Reference Appendices, "2.3 Building Materials and
  Construction", Table 5 (gypsum board and wood: k, rho, cp).
- UK SAP default U-values for the glass, as in `radiatorUnderWindow`.
- ISO 7730, EN 16798-1 and ASHRAE 55 for the ankle height and the occupied zone, as cited by
  B. W. Olesen, REHVA Journal 06/2024, Table 2.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with `wmake` and MPI, and
Python 3 (no packages).

    cd cases/ceilingVsFloorVent
    ./Allrun floor           # [nProcs], default 8
    ./Allrun ceiling
    python3 scripts/extract_results.py runs results

`Allrun` compiles `src/bedroomLayer` into `$FOAM_USER_LIBBIN` and `src/bedroomTools` into
`$FOAM_USER_APPBIN`, writes and meshes the shared mesh in `runs/mesh` once, writes the run into
`runs/<run>/` with `scripts/make_case.py`, sets its fields (`setFields`) and its hydrostatic
pressure (`bedroomTools -prepare`), decomposes it, writes the t = 0 section, solves and, once
both runs have solved, writes `results/`. `./Allrun --setup-only <run> [nProcs]` stops before
the solve; `./Allclean` removes the runs.

The two runs took 15,379 s (4.27 h, floor) and 20,174 s (5.60 h, ceiling) of wall time side
by side on 8 ranks each. Each writes 481 sections of about 6.5 MB (gzip takes them to about
2.5 MB); its monitor's budget.csv is 180-260 MB.

The case was set up by an agent and checked by us; the runs were solved on our own machine.
The files in `results/` are what `scripts/extract_results.py` wrote from those two runs.
