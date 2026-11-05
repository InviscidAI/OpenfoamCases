# A fan heater against an oil radiator that is already hot

A cold bedroom on a 0 °C morning gets one plug-in heater under its window. Is a small fan heater
or an oil-filled radiator the quicker way to warm it? This case takes
[`ceilingVsUnderfloor`](../ceilingVsUnderfloor)'s room at its 16 °C night setback and switches
on a 1500 W ceramic fan heater in one copy of it and an oil-filled radiator, already hot at 95 °C,
in the other, and follows the first five minutes with radiation solved. It is about where the heat
goes and how fast the room's air warms, not about running cost, noise or safety.

    ./Allrun fan        # the fan heater, 1500 W into its air, 0-300 s from switch-on
    ./Allrun oilHot     # the oil radiator, its fins held at 95 C from t = 0, 0-300 s

**The result.** The fan heater gives the room **1500 W** from the first second, all of it carried
by its air. The radiator, already at 95 °C, gives it about **610 W**: 376 W by convection and
235 W by radiation at 300 s, 38% radiant. Over the five minutes the fan heater puts 450 kJ into
the room and the radiator 184 kJ. The fan heater's jet lifts into a plume about 1.5 m out and the
room fills with warm air from the ceiling down: its mean air goes from 16.0 to 23.5 °C and the
occupied zone's ankle band to 19.7 °C. The radiator's plume rises up the window and a warm layer
builds under the ceiling while the room stays cold low down: its mean air reaches 17.9 °C and the
ankle band 16.4 °C. Read [The 610 W](#the-610-w) and [What it cannot](#what-it-cannot) before
any number here. The two heaters do not give equal watts, and the two runs are on different
meshes.

## The room

The room, its glass, its walls and its radiation are `ceilingVsUnderfloor`'s, with nothing
heated but the heater.

| | value | from |
|---|---|---|
| room | 4.0 m from the window wall to the inner wall, 3.5 m wide, 2.4 m high | ceilingVsUnderfloor |
| window | glass 1.0 m wide and 1.2 m tall, sill 0.90 m above the floor, centred in the wall, shut; h = 4.403 W/m²K to 0 °C outside, no heat capacity, emissivity 0.837 | ceilingVsUnderfloor |
| walls | the window wall around the glass, the inner wall, both side walls and the ceiling 1/2 in (12.7 mm) gypsum board, the floor 3/4 in (19 mm) wood, each a 1-D layer of 24 slices with its heat capacity and an adiabatic back; emissivity 0.9 | ceilingVsUnderfloor (California Energy Commission, EN ISO 6946) |
| start | the air at rest, the air, every surface and every wall layer at **16 °C** (289.15 K); the radiation field the room's own at 16 °C (G 1585.5 W/m², each ray 126.18 W/m² sr) | ceilingVsUnderfloor (Energuide) |
| occupied zone | four bands of cells within 0.02 m of 0.1 (ankle), 0.6 (knee), 1.1 (seated head) and 1.7 m (standing head), more than 1.0 m from the window wall and 0.3 m from the others, so both heaters are outside it | ASHRAE 55 via ceilingVsUnderfloor |

Coordinates are `ceilingVsUnderfloor`'s: x into the room from the window wall's face, y up from
the floor, z across the room with z = 0 through the middle of the window.

## The heaters

Both stand on the floor under the window, their backs 15 cm from the window wall, x = 0.150 to
0.300 m.

**The fan heater** is built from a Lasko 754200's published size, 17.8 cm wide, 15.0 cm deep and
23.4 cm tall (z = −0.089 to 0.089 m, y = 0 to 0.234 m), as a solid casing with a grille on its
back (the intake) and one on its front (the outlet), each 11.5 cm wide and 16 cm tall from
y = 0.03 to 0.19 m, 0.0184 m². The grilles' size and height are ours, read off the maker's photo;
Lasko gives none, and no photo of the back was found.

- The intake draws **0.0301 kg/s** out of the room (`flowRateOutletVelocity`). That is 90 m³/h at
  16 °C, the air volume Dantherm lists for the Calesco Rondo 1500, a 1500 W ceramic fan heater of
  about the same size; Lasko publishes none.
- The outlet returns the same mass flow at the intake's mean temperature plus **1500 W**
  (`outletMappedUniformInletHeatAddition`), 49.6 K above the intake at that flow, about 1.6 m/s
  through the grille. An IEC 60335-2-30 test report on a larger fan heater read 49 K at its
  outlet. The outlet's turbulence is 5% intensity with a 1 cm mixing length.
- The casing is adiabatic and has no heat capacity; it radiates with emissivity 0.9, so it takes
  the radiation's balance temperature. The fan heater therefore gives the room exactly 1500 W, all
  by convection.

**The oil radiator** is built from a De'Longhi EW7707CM's published figures, seven fins and
15 × 35 × 63 cm, as seven flat fins 16 mm thick at a 36 mm pitch, so 20 mm apart, from
y = 0.06 to 0.63 m (centres at z = −0.126 + 0.036k m, k = 0 to 6, which puts the middle gap on
z = 0), with the control column, 9 cm wide (z = 0.098 to 0.188 m), joined to the last fin. It is
open below the fins to the floor. The pitch, the thickness, the 6 cm clearance and the column's
width are ours, read off the manual's photo; the castors and the oil channels are left out.

- **The fins are held at 95 °C (368.15 K) from t = 0** by the coded condition in
  `template/oilHot/system/radiatorLumped`, which `0.orig/T` includes for the `radiator` patch. It
  is a `codedFixedValue` named `radiatorHeld`; OpenFOAM compiles it into the run's `dynamicCode/`
  on the first read, so the run needs a working OpenFOAM build environment. At every step it logs
  what the fins give the room, `radiatorLumped: t <s> Ts <K> Qconv <W> Qrad <W>`, with Qconv the
  face flux κ_eff ∂T/∂n summed over the fins and Qrad minus the integral of the radiation's qr
  over them. `scripts/extract_results.py` reads those lines.
- 95 °C is within the 85-104 °C an owner measured on a 1500 W radiator after an hour on its
  highest setting, bottom fin to top fin. Holding it is the operator's choice of state: a radiator
  that has heated itself and whose thermostat now holds it. The run does not model the warm-up or
  the thermostat's cycling, and a real radiator that had warmed up would have warmed its room
  while it did.
- The column is adiabatic, with no heat capacity, and radiates (emissivity 0.9).

## The 610 W

The radiator's 610 W is what this model's flat fins give at 95 °C, not the radiator's 1500 W
rating. Holding 95 °C takes well under the 1500 W element, so a real one would be cycling on its
thermostat, and the run does not model that cycling. The figure sits close to Matthias Wandel's
report that every oil radiator he tried trips its overheat thermostat above about 600 W. It is
below a hand estimate of 0.8-1.1 kW at 85-104 °C (laminar convection, about 5 W/m²K, on the
seven 0.57 m fins' 1.4 m² or so, plus radiation from the radiator's envelope), and below the
870 W that an earlier pilot's conductance (1399 W at 141 °C, about 11 W/K) would give at 95 °C.
So the 1500 W against 610 W belongs to this room and this model, and is not a measured rating of
either product.

The very start is higher. On the first logged step the hot fins meet still air at 16 °C and give
745 W (500 W convection, 244 W radiation). As the air at the fins warms and starts to move, the
total falls below 700 W at 0.28 s and below 620 W at 0.87 s; it is 619 W at 5 s and 610-614 W from
a minute on.

## The model

Each run's mesh is a Cartesian background written straight into `constant/polyMesh` by a Python
builder, with the heater's solid cut out of it by `topoSet` and `subsetMesh` and the cut faces
sorted into the heater's patches by `topoSet` and `createPatch`. The builder and the cut are what
the solved runs used, and from a clean copy of this case `./Allrun --setup-only` writes both
solved runs' meshes byte for byte.

- **Solver:** buoyantPimpleFoam (OpenFOAM v2512), air as a perfect gas (c_p 1005 J/kg K,
  μ 1.82e-5 Pa s, Pr 0.71), k-omega SST with the buoyancy source on k (`buoyancyTurbSource`),
  wall functions, PIMPLE with 2 outer and 2 pressure correctors, Euler in time at **Courant 2**
  with steps of at most 0.1 s, `limitedLinear 1` for energy and turbulence and `limitedLinearV 1`
  for momentum, a pressure reference in mid-room, a p_rgh tolerance of 1e-7.
- **Radiation:** fvDOM, nPhi 3 and nTheta 4, 48 directions, solved every 10 steps, each ray's
  solve capped at 10 sweeps; grey, diffuse, opaque surfaces; the air neither absorbs nor emits.
- **Walls:** `radLayerWall` (`src/radLayerWall`), `ceilingVsUnderfloor`'s condition, the same
  code: each face balances the solver's convective flux, the radiation and the 1-D layer behind
  it, or for the glass a film to 0 °C outside.
- **Monitors** (`template/<run>/system/functions`), every 0.625 s: the room's mean air, the four
  bands, each surface's mean temperature and integrated qr, the walls' heat flux, the coldest and
  hottest air, and for the fan heater the two grilles' flows and flow-weighted temperatures. The
  radiator run also records every step the coldest and hottest air, the glass's coldest face, the
  fins' hottest face and the coldest air in front of the heater (x = 0.30-0.40 m, y = 0.06-0.70 m,
  |z| < 0.20 m), the checks the regraded mesh was built to pass. `airEnergy` integrates
  ρ c_p (T − 16 °C), which in a closed room reads c_p/c_v times the heat the air has taken in; it is
  kept as the runs wrote it and is not used in `results/`.
- **Planes** every 0.625 s: the vertical section at z = 0.005 m, in the radiator's middle gap and
  through the middle of the fan heater, and a horizontal plane at ankle height, y = 0.095 m, both on
  cell centres, as VTK.

### Two meshes

| run | builder | background | after the cut | non-orthogonality max | skewness max |
|---|---|---|---|---|---|
| `fan` | `scripts/mesh_rework.py` (1 Nov 2026) | 428,385 cells | **426,285** | 58.6° | 1.54 |
| `oilHot` | `scripts/mesh_regrade.py` (3 Nov 2026) | 445,671 cells | **442,671** | 27.9° | 1.09 |

Both builders share the x lines and the heaters' z lattice: two cells across each 16 mm fin and
each 20 mm gap, about 1 cm across the fan heater's grilles, behind its intake and along the jet's
first metre (x = 0.30-1.30 m, y < 0.30 m), 1 cm at the floor, 2 cm at the window wall and 9 cm
in the far room. They differ near the heaters. The rework mesh joins cells of very different size
through split faces; in front of the fins 36 mm cells met the fins' 8-10 mm lattice four to one,
and in an earlier production on that mesh the radiator held a column of air colder than anything it
touched, an undershoot of the energy scheme there. The regrade puts every column at x < 1.30 m on
one y lattice and nests four z lattices so that no interior face joins two cells that only partly
overlap and no cell side meets more than two neighbours along an edge; the builder checks this
and writes `levels_background.json`.

**Why the runs are on different meshes.** The regrade's fan heater run projected 14.8 h on this
machine, over the 10 h a run that our rules allow, so it was not solved past a 20 s pilot. The
fan heater's run here is the rework mesh's production, and the radiator's the regraded mesh's. The
pair is therefore not the like-for-like pair the case was planned as. What supports it:

- **The radiator held 95 °C.** Its log and both surface monitors read 95.000 °C at every step.
- **The radiator run's air stays in bounds.** At each of its 6,627 steps no air is colder than the
  glass's coldest face or hotter than the fins. The air spans 13.47-57.09 °C, the glass's coldest
  face is 9.10 °C and the air in front of the radiator never falls below 15.68 °C.
- **The fan heater run's air stays in bounds** on its monitors: 9.28-70.70 °C at every 0.625 s,
  against an outlet near 66 °C.
- **The fan heater run agrees with the regraded mesh as far as that was solved.** Against the
  regrade's 0-20 s fan pilot, the room's mean, the ankle, head and standing bands and the outlet
  temperature agree within 0.005 K at 5-20 s; the section differs by 0.23 K rms. Nothing was
  solved on the regraded mesh past 20 s, so this says nothing directly about the later minutes.

## Results

`results/summary.txt`, from `scripts/extract_results.py`:

| | 0:05 | 1:00 | 2:00 | 3:00 | 4:00 | 5:00 |
|---|---|---|---|---|---|---|
| fan heater, heat into the room (W) | 1500 | 1500 | 1500 | 1500 | 1500 | 1500 |
| oil radiator at 95 °C, heat into the room (W) | 619 | 614 | 613 | 613 | 612 | 610 |
| of which radiation (W) | 241 | 239 | 237 | 236 | 235 | 235 |
| room's mean air, fan heater (°C) | 16.3 | 18.3 | 20.1 | 21.6 | 22.7 | 23.5 |
| room's mean air, radiator (°C) | 16.1 | 16.5 | 17.0 | 17.4 | 17.7 | 17.9 |
| air at the ankles, fan heater (°C) | 16.08 | 16.62 | 17.04 | 17.44 | 18.27 | 19.69 |
| air at the ankles, radiator (°C) | 16.03 | 16.16 | 16.24 | 16.29 | 16.35 | 16.38 |

The fan heater's heat is what its air carries off the element, mass flow × c_p × (outlet −
intake), from its monitors: 1499.9 W on average over 10-300 s, within 1499.4-1500.3 W. Its seated
head band is 23.8 °C at 300 s, 4.2 K above the ankles. In the radiator's room the head band is
17.2 °C, 0.8 K above the ankles.

The runs took 49,676 steps and 46,897 s of wall time (13.0 h, `fan`, 10 ranks) and 6,627 steps
and 3,827 s (1.06 h, `oilHot`, 16 ranks). The fan heater's step is set by the 1 cm cells behind
its intake, 0.006 s on average; the radiator's by its plume, 0.045 s.

## What it cannot

- **Not equal watts, and not a warm-up.** The fan heater gives its full 1500 W at once; the
  radiator starts hot and gives what its fins shed at 95 °C. Starting it hot in a room still at
  16 °C is a constructed state. The case says how two heaters spend the first five minutes in this
  state, not which is the better buy.
- **Two meshes.** The heaters' surroundings are meshed differently in the two runs, which is where
  the regrade changed the grading. The comparison above covers the fan heater's first 20 s only.
- **The radiator.** Flat plates at one temperature, where real fins are pressed and hotter at the
  bottom than the top; its dimensions partly read off a photo; no castors, oil channels or
  thermostat.
- **The fan heater.** Grilles read off a photo, a flow taken from a similar heater, a casing that
  does not warm, no thermostat.
- **The room.** One room, one placement, five minutes, neither room settled; no people or
  furniture; a still morning with only the glass losing heat to the outside.

## Sources

- Lasko, 754200 ceramic heater product page (9.2 × 6.00 × 7.00 in; 900-1500 W), read 31 Oct 2026.
- Dantherm, Calesco Rondo 1500 (air volume 90 m³/h), read 31 Oct 2026.
- An Intertek IEC 60335-2-30 test report on a 2 kW fan heater ("Air outlet 49 K"), as published by
  its retailer.
- De'Longhi, EW7707CM product page (7 fins, 1500 W, 5.9 × 13.78 × 24.9 in) and its manual
  ("beneath the coldest window"), read 31 Oct 2026.
- A Garage Journal forum thread (2012): an owner's 1500 W radiator at 185-220 °F after an hour on
  its highest setting.
- Matthias Wandel, a video on oil-filled radiators: every one he tried tripped its overheat
  thermostat above about 600 W.
- The room, its walls, its glass and their sources: [`ceilingVsUnderfloor`](../ceilingVsUnderfloor),
  [`underfloorVsRadiator`](../underfloorVsRadiator) and [`windowAiring`](../windowAiring).

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with `wmake` and MPI (the
radiator's coded condition compiles on its first read), and Python 3 with NumPy for the mesh
builders and `scripts/extract_results.py`.

    cd cases/fanHeaterVsOilRadiator
    ./Allrun fan                 # [nProcs], default 16
    ./Allrun oilHot
    python3 scripts/extract_results.py runs results

`Allrun` compiles `src/radLayerWall` into `$FOAM_USER_LIBBIN`, copies `template/common/` and
`template/<run>/` into `runs/<run>/`, writes the background mesh with the run's builder (about a
minute), cuts the heater out and checks the mesh, writes the planes at t = 0 from the initial
fields, decomposes it by scotch, solves 0-300 s and, once both runs have solved, writes
`results/`. `./Allrun --setup-only <run> [nProcs]` stops before the solve; `./Allclean` removes
the runs. The solved runs used 10 (`fan`) and 16 (`oilHot`) ranks; another decomposition will not
reproduce them bit for bit.

Each run writes 481 pairs of planes, about 350 MB, a few MB of monitors and the fields every 30 s
(the last two kept, so an interrupted solve can be continued). `results/` holds each run's history
every 2.5 s, `minutes.csv` (the table above) and `summary.txt`; no fields, meshes, planes or logs.

The case was set up and solved by an agent on our own machine and checked by us. The files in
`results/` are what `scripts/extract_results.py` wrote from those two runs.
