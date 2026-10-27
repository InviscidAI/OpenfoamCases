# Underfloor heating or a radiator under the window

Heat a room through its floor, or with a radiator under the window: where does the warm air
go, and how much warmer is it at a seated person's head than at their ankles? This case takes
[`windowAiring`](../windowAiring)'s room with its window shut on a still 0 °C morning and
heats it with the same 60 W twice, once from [`radiatorUnderWindow`](../radiatorUnderWindow)'s
radiator under the window and once spread evenly over the whole floor, and follows both rooms
for twenty minutes from switch-on. The number it reports is **the head-to-ankle difference**,
the occupied zone's mean air temperature at 1.1 m less that at 0.1 m. It is not about heating
bills, warm-up times or heat pumps.

One OpenFOAM case, two runs that differ only in where the 60 W goes:

    ./Allrun radiator    # 60 W from the radiator box under the window, the floor adiabatic, 0-1200 s
    ./Allrun floor       # no radiator, 60 W through the floor as 4.29 W/m², 0-1200 s

**Both rooms end about 0.3 °C warmer at the head than at the ankles**, well inside the limits
of EN 16798-1's best comfort category, for different reasons. **The load is small**: 60 W, with
only the glass losing heat and every other wall and the ceiling held at 20 °C. Read
[What it cannot](#what-it-cannot) before any number here.

## The room

| | value | from |
|---|---|---|
| room | 4.0 m from the window wall to the inner wall, 3.5 m wide, 2.4 m high: 14.0 m² of floor, 33.6 m³ | windowAiring |
| window | glass 1.0 m wide and 1.2 m tall, sill 0.90 m above the floor, centred in the wall, shut | windowAiring and radiatorUnderWindow |
| glass | ordinary air-filled double glazing, U = 2.8 W/m²K, to still air at 0 °C: `externalWallHeatFluxTemperature` with h = 4.403 W/m²K to 0 °C, the inside film left to the solver | radiatorUnderWindow (UK SAP default U-value) |
| radiator (`radiator` only) | windowAiring's box, a Stelrad Compact K1 600 × 1000: 1.0 m long under the window, bottom 0.15 m up, 0.04 m off the wall; on the mesh 2,240 cells from x 0.04 to 0.12 m and y 0.15 to 0.75 m. 60 W as an enthalpy source spread over the box, which the air passes up through as through a convector's fins | windowAiring, radiatorUnderWindow |
| warm floor (`floor` only) | the same 60 W through the whole floor as a uniform heat flux, 60/14.0 = 4.29 W/m² (`externalWallHeatFluxTemperature`, mode flux); its temperature is the result | ours |
| other surfaces | the ceiling, the inner wall and both side walls held at 20 °C, the rest of a heated house; the window wall around the glass adiabatic; in `radiator` the floor adiabatic | radiatorUnderWindow |
| start | the air at rest at 20 °C; at t = 0 the glass sees 0 °C outside and the heater is on at full output, constant, no thermostat | radiatorUnderWindow |

**Why 60 W.** It is radiatorUnderWindow's output, set there to its section's own steady heat
loss at a 20.5 °C room, and kept by windowAiring for its 1.0 m radiator; that case says why it
is about a tenth of what the same radiator gives at normal water temperatures. The warm floor
gives the same total, so the comparison is between equal heat. Spread over 14 m², 60 W is a
floor EN 1264's curve, q = 8.92 (θ_floor − θ_room)^1.1 W/m², puts 0.5 K above the room, far
below the standard's 29 °C limit for occupied floors: a floor heats through its area, not its
temperature.

## The model

`scripts/make_case.py <run> <dir>` writes every dictionary, the initial fields and the run's
own Allrun. Coordinates are windowAiring's: x from the window wall into the room, y up from
the floor, z across the room from the middle of the window.

- **Solver:** buoyantPimpleFoam (OpenFOAM v2512), air as a perfect gas with
  radiatorUnderWindow's properties (c_p 1005 J/kgK, μ 1.82e-5 Pa s, Pr 0.71), k-omega SST with
  the buoyancy source on k (`buoyancyTurbSource`), wall functions, PIMPLE with 2 outer and 2
  pressure correctors, Euler in time at Courant 1, windowAiring's schemes. No radiation.
- **Mesh:** the room part of windowAiring's graded blockMesh box, as one block of
  66 × 83 × 68 = 372,504 cells: 20 mm across the first 0.3 m from the window wall, 10 mm at the
  floor, 30 mm over the window band and under the ceiling, 20 mm at the window's side edges.
  There is no outdoor volume: the window is shut, and the glass's boundary condition carries
  the 0 °C. The glass is cut out of the window wall's patch by position (1,120 faces, 1.20 m²).
  Both runs have the same mesh; `radiator` adds the radiator's cell zone. `checkMesh`: OK, no
  non-orthogonality, largest aspect ratio 12.2.
- **The closed room** takes radiatorUnderWindow's pressure reference in mid-room and its cap
  of 100 iterations on the final pressure solve, with windowAiring's tolerance of 1e-7 (see
  [How the case got here](#how-the-case-got-here)).
- **The head-to-ankle difference.** EN 16798-1 and ISO 7730 call it the vertical air
  temperature difference, between 1.1 m and 0.1 m above the floor for a seated person, and put
  it under 2 °C for category I, 3 °C for II and 4 °C for III (Olesen, REHVA Journal 06/2024,
  Table 2). It is measured in the occupied zone, which ASHRAE 55 puts more than 1.0 m from
  outside walls and windows and 0.3 m from inside walls. Here it is the mean air temperature
  over the cells whose centres are 1.0-3.7 m from the window wall, within 1.45 m of the room's
  middle and within 0.02 m of each height (two layers of cells at 0.1 m, one at 1.1 m), at 1.1 m
  less that at 0.1 m.
- **Monitors, every step:** the occupied zone's mean at 0.1, 0.6, 1.1 and 1.7 m, the room's
  mean, the glass's and the floor's mean surface temperature and the floor's warmest face, the
  heat through every patch (`wallHeatFlux`) and the room's internal energy (`energyCheck`,
  (c_v/R) ∫p dV, which for a closed perfect-gas box is its internal energy), and eight probes.
  Three planes every 2.5 s: the mid plane through the window and the radiator (z = 0.005 m),
  which the clip shows, and the whole room at 0.1 m and 1.1 m.

## How the case got here

**The pressure tolerance.** The first pilot took radiatorUnderWindow's p_rgh tolerance of
1e-8. On this mesh the final pressure solve stalls at about 2.1e-8, so both final solves of
every step ran to the 100-iteration cap. With windowAiring's 1e-7 and nothing else changed,
the same 107 steps (2.0 to 9.25 s) of the radiator run took 0.58 s a step instead of 2.36 s.
The solved runs use 1e-7; their final pressure solves took 7 iterations on average, and reached
the cap only in the first half-second (12 times in `radiator`, 13 in `floor`). The 1e-8 pilot
is not kept.

**The end time.** The pilots' step rates put 1800 s at 5.6 hours (`radiator`) and 7.4 hours (`floor`), so the end was set at
1200 s before the runs started, to be continued if the head-to-ankle difference had not
settled. It had, to its first decimal (below), and neither run was continued.

## Checks

- **The generator against the solved runs.** From a clean copy, `./Allrun --setup-only
  radiator` and `--setup-only floor` wrote the solved runs' meshes (points, faces, owner,
  neighbour, boundary, cell, face and point zones, and every set) byte for byte, 372,504 cells,
  `checkMesh` OK, and the t = 0 planes byte for byte. Every initial field in `0/` is byte for
  byte the same but T, which differs only in one comment line naming the case it comes from;
  `constant/` and `system/` differ from the solved runs' only in comments. The decomposition was
  not compared: scotch splits the mesh differently from one call to the next, so a re-solve
  will not match the committed histories to the last digit.
- **The heat budget closes.** The room is closed, so its internal energy must change at the
  heater's 60 W plus the heat through the walls. Taken over 3.75 s about every step from 2 s to
  the end, it does to within 0.57 W (`radiator`) and 0.58 W (`floor`), 0.01 W on average.
- **The glass's loss** from its mean surface temperature, h (T_s − 0 °C) A, agrees with
  `wallHeatFlux` on the glass to within 0.07 W at every 2.5 s write.
- **Both runs ended cleanly** at 1200 s, in 20,935 steps (`radiator`, mean step 0.057 s) and
  25,037 (`floor`, 0.048 s).

## Results

From `results/summary.txt` and `results/<run>/history.csv`, which `scripts/extract_results.py`
writes from the runs' per-step monitors and the mid plane at 1200 s.

**The head-to-ankle difference ends at about 0.3 °C in both rooms.**

| head minus ankles, °C | 1-2 min | 5-6 min | 10-11 min | 15-16 min | 19-20 min | last 5 min | at 20 min |
|---|---:|---:|---:|---:|---:|---:|---:|
| radiator under the window | 0.00 | 0.08 | 0.21 | 0.27 | 0.29 | 0.28 | 0.29 |
| warm floor | 0.26 | 0.34 | 0.29 | 0.29 | 0.29 | 0.29 | 0.31 |

(Minute means, the mean over 900-1200 s, and the value at 1200 s.) Both are far inside the
2 °C of EN 16798-1's category I. The warm floor's difference is there within two minutes and
then wanders between 0.26 and 0.36 °C from minute to minute with no trend; over the last five
minutes it is 0.29 °C with a standard deviation of 0.02. The radiator's builds up slowly and is
still creeping up at the end: 0.275 °C over 900-1050 s and 0.287 °C over 1050-1200 s, about
0.004 °C a minute over the last five minutes and slowing.

**The rooms get there differently.**

| occupied zone at 1200 s, °C | 0.1 m (ankles) | 0.6 m | 1.1 m (seated head) | 1.7 m | room mean |
|---|---:|---:|---:|---:|---:|
| radiator under the window | 20.03 | 20.18 | 20.33 | 20.44 | 20.32 |
| warm floor | 20.10 | 20.40 | 20.41 | 20.42 | 20.40 |

- **With the radiator,** its plume climbs the glass, takes the cold air coming off the glass
  into itself, and spreads under the ceiling. The room fills with warm air from the top down:
  on the mid plane at 1200 s the air rises steadily from 20.0 °C at the floor to about 20.5 °C
  at 2 m, with the warmest air, 20.6 °C, just under the ceiling in the first 2 m from the
  window. There is no cold current along the floor: the air at the floor is 20.0 °C from 1 to
  3 m into the room. The radiator room's head-to-ankle difference is that warm air
  overhead, and it grows as the warm layer deepens.
- **With the warm floor,** the cold air off the glass falls to the floor and runs across the
  whole room as a current along it, about 0.15-0.2 m deep where it moves faster than
  0.03 m/s, coolest in its lowest few centimetres (18.8 °C 1 m from the window, 19.7 °C at
  2 m), warmed from below as it goes. Above it the room is close to one temperature: the
  occupied zone's mean is 20.40-20.42 °C from the knee to 1.7 m. The floor room's difference is that cool current under a
  seated person's ankles.

**Where the heat goes,** over the last minute (W, positive into the air):

| | heater | glass | ceiling | inner wall | side walls | stored in the air |
|---|---:|---:|---:|---:|---:|---:|
| radiator under the window | 60.0 | −36.9 | −12.9 | −3.4 | −3.4 | 3.5 |
| warm floor | 60.0 | −34.7 | −8.0 | −6.2 | −8.0 | 3.1 |

The glass takes more with the radiator, whose plume washes it (its inside surface 7.0 °C
against 6.6 °C, mean over the last five minutes), and the ceiling takes more under the radiator
room's warm layer. Both rooms still store about 5-6% of the heater's output at the end, their
mean air temperature rising about 0.04 °C in the last five minutes.

**The floor's surface** runs at 22.2 °C on average over the last five minutes, its warmest
face 25.2 °C: about 2 K above the room's air, where EN 1264's curve, which counts radiation,
puts a 4.29 W/m² floor 0.5 K above it. With no radiation in the model the floor passes all of
its heat by convection and has to run warmer to do so.

## What the clip shows, and what it does not

**It shows** the mid plane through the middle of the window and the radiator, radiator above
and warm floor below, from switch-on to 1200 s at 60×, coloured by temperature on one scale for
both, 18-22 °C, with the starting 20 °C in the middle. Air parcels are carried through the flow
on the plane as it stands at each moment, at a quarter of the clock's pace (15× real time), so
they trace the flow rather than keep up with the colours. The window, the outside beyond it,
the radiator and the warm floor are drawn. Each panel carries only its name.

**It shows no number.** Both rooms end at the same 0.3 °C, so a figure on screen said nothing
the colours do not. The figure is the result above.

**It does not show** anything off the mid plane. The run is 3-D, but the picture is one
vertical section through the window's middle, so it looks like a 2-D room. Off that plane the
radiator's plume ends at the radiator's ends and the floor current spreads sideways; the
head-to-ankle numbers are means over the 3-D occupied zone, not over the section.

## What it cannot

- **A real heating load.** 60 W is a small load because only the glass loses heat: the
  ceiling and every other wall are held at 20 °C, so they take heat from the warm air and give
  none to the cold. A real room with cold outside walls and a heater giving several hundred
  watts, as a real radiator does at normal water temperatures, may stratify more: a hotter
  plume makes a warmer layer under the ceiling, and cold walls add their own cold air along
  the floor. The 0.3 °C here is for this load and these walls, not a measure of the two
  systems in general. [`airingRadiatorValve`](../airingRadiatorValve) has a radiator sized for
  this room, with the window wall's conduction to outside and the leaks it is sized for.
- **Radiation.** A warm floor gives about half its heat as radiation, and a radiator some. Here
  every watt leaves by convection: the glass loses 35-37 W instead of the 57 W
  radiatorUnderWindow's section loses at 20 °C, and the floor runs about 2 K above the air
  instead of 0.5 K. The warmth a seated person feels from a warm floor is radiant and not in
  the model; the comparison is of air temperatures only.
- **The screed's warm-up.** The floor gives its full 60 W from t = 0. A real underfloor system
  takes hours to come up from cold.
- **Twenty minutes from a room already at 20 °C.** Both rooms are still warming slowly at the
  end, and the radiator's difference is still creeping up.
- **A 2-D-looking picture of a 3-D run,** as above.
- **An empty room.** No furniture, people, open door, thermostat, ventilation or leaks, no wind
  and no sun.
- **One mesh, unsteady RANS,** k-omega SST with wall functions, no mesh or time-step study, one
  realization of each run. The occupied zone's bands are two layers of cells at the ankles and
  one at the head.

## Sources

- B. W. Olesen, "European Standardisation on Thermal Environment", REHVA Journal 06/2024,
  Table 2 (EN 16798-1 and ISO 7730, vertical air temperature difference):
  https://www.rehva.eu/rehva-journal/chapter/european-standardisation-on-thermal-environment
- ASHRAE Standard 55, the occupied zone.
- Vogel & Noot, FLOORTEC technical information, after ÖNORM EN 1264 (the base curve and the
  29 °C surface limit):
  https://www.vogelundnoot.com/static_files/at/media/downloads/Floortec_technische_informationen.pdf
- The glass's U-value, the radiator and its 60 W: [`radiatorUnderWindow`](../radiatorUnderWindow)
  and [`windowAiring`](../windowAiring), with their sources.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3;
`scripts/extract_results.py` also needs NumPy, and PyVista for the mid-plane profiles.

    cd cases/underfloorVsRadiator
    ./Allrun radiator                # [nProcs], default 8
    ./Allrun floor
    python3 scripts/extract_results.py runs results

`Allrun <run>` writes the run into `runs/<run>/` with `scripts/make_case.py`, then runs the
Allrun written there: blockMesh, the glass cut out of the window wall (topoSet, createPatch),
the radiator's and the occupied zone's cell zones, the initial fields, checkMesh, the t = 0
planes from the initial fields and decomposePar, and then solves 0-1200 s, writing the planes
every 2.5 s and the fields every 7.5 s (the last two kept). `./Allrun --setup-only <run>` stops
before the solve, in about 10 s. `./Allclean` removes the runs.

The runs took 13,384 s (`radiator`) and 15,957 s (`floor`) of wall time on 8 ranks each, side
by side. Each writes about 0.9 MB of planes every 2.5 s, 450 MB in all. `results/` holds each
run's history every 2.5 s (the occupied zone's temperatures and the head-to-ankle difference,
the room's mean, the glass's and the floor's surface, the heat through every boundary and the
budget) and the summary; no fields, meshes, planes or logs.

The case was built, checked and solved by an agent on our own machine.
