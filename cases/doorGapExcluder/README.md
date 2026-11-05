# The gap under a door, left open and blocked with a draught excluder

UK building rules ask for a gap under an inner door: "a minimum free area equivalent to a 10mm
undercut in a 760mm wide door" (Approved Document F, volume 1, 2021 edition, paragraph 1.25;
2026 edition, paragraph 1.21). Draught-proofing advice says to block the gap between a heated and an
unheated room with a sausage-shaped excluder. How much air does that gap move between a warm room
and a cold hall, how far does the hall's air get across the floor, and what changes when it is
blocked? This case takes a vertical section through [`radiatorUnderWindow`](../radiatorUnderWindow)'s
room, a door and a hall, starts the room at 20 °C and the hall at 10 °C on a 0 °C day, and follows
the first four minutes with the gap open and with an excluder against it.

    ./Allrun open       # a 10 mm undercut and a 3 mm head gap, 0-240 s from rest
    ./Allrun blocked    # the same with an excluder 95 mm across against the leaf, 0-240 s

**The result.** With the gap open, the door moves **1.52 l/s per metre** of cold hall air in under
the leaf and the same back out over its head, steady to within 1.47-1.60 l/s from 10 s to 240 s. The
hall's air (at least 10% of it, by a tracer) crosses the floor: it is 0.75 m from the door at 10 s,
has reached 3.9 m by 55 s and the far wall, 4.0 m, by 3 minutes. With the excluder the through-flow
stops: what is left under the door is an eddy of 0.006 l/s each way in the stub on the hall's side,
under 1% of the open flow, and the hall's air gets **0 m** into the room. The heat the room loses through the door,
gaps and leaf together, falls from **36.0 to 18.6 W per metre**; 20.8 W of the open figure is the
leaf's, which an excluder does not touch. All of this is per metre of a door as wide as the room.
Read [What it cannot](#what-it-cannot) before any number here.

## The section

x runs from the window wall's inner face into the room, y up from the floor; the section is 1 m deep
in z, one cell, with empty front and back.

| | value | from |
|---|---|---|
| room | x = 0-4.0 m, 2.4 m high; at 20 °C | `radiatorUnderWindow` |
| window | glass from y = 0.9 to 2.1 m in the outer wall, h = 4.403 W/m²K to 0 °C outside (U = 2.8 W/m²K less the inside film); the rest of the outer wall adiabatic | `radiatorUnderWindow` |
| radiator | 60 W per metre released as heat in a box x = 0.040-0.123 m, y = 0.15-0.75 m (`constant/fvOptions`), the air passing freely through it | `radiatorUnderWindow` (a Stelrad K1's box, the section's own loss at 20.5 °C) |
| door leaf | a standard UK internal leaf, 1981 x 762 x 35 mm: x = 4.000-4.035 m, y = 0.010-1.991 m, on the room's side of a 100 mm wall | |
| undercut | **10 mm** (y = 0-0.010 m), 35 mm long | Approved Document F's figure |
| head gap | **3 mm** (y = 1.991-1.994 m), 35 mm long | ours: the middle of the 2-4 mm usual on UK fire doors (trade guidance); no figure for an ordinary door was found |
| wall above the door | x = 4.000-4.100 m, y = 1.994-2.4 m | |
| hall | x = 4.035-5.6 m (the 65 mm behind the leaf is the frame's reveal), 2.4 m high, unheated, at 10 °C; a front door 2.0 m tall in its far wall, h = 2.33 W/m²K to 0 °C, the wall above it adiabatic | ours |
| leaf and wall above | each face loses heat through h = 2.33 W/m²K to the other side's starting temperature (the room face to 10 °C, the hall face to 20 °C), U = 1.8 W/m²K with the solver's own film | ours (R = 0.30 m²K/W for the leaf) |
| floors and ceilings | 19 mm wood floors and 12.7 mm gypsum-board ceilings, each a 1-D layer of 24 cells with its heat capacity and an adiabatic back, starting at its own room's temperature | [`ceilingVsFloorVent`](../ceilingVsFloorVent)'s `bedroomLayer` |
| excluder (blocked only) | a solid circle 95 mm across on the floor against the leaf's room face, centre (3.9525, 0.0475) m, adiabatic, no-slip | listings of fabric excluders (30 cm round; 7 x 12 cm) |

The leaf and the wall are thermal reservoirs on each face, not a coupled solid: the rooms' means move
by under 1 K in four minutes, so a fixed far side is enough. The hall's 10 °C, the leaf's resistance
and the front door are ours.

**The start.** Both rooms at rest, each in its own hydrostatic balance (`doorTools -prepare`: perfect
gas at 20 °C for x < 4 m and 10 °C beyond, 1e5 Pa at y = 1.174 m in both), so the only thing that
drives the door is the stack between a 20 °C and a 10 °C column, about 0.8 Pa over the door's height.
The radiator is on and the outside at 0 °C from t = 0, and the undercut is open or blocked from
t = 0. The section is closed, with no imposed pressure difference, so what crosses the door one way
crosses it back the other.

**The tracer.** `hallAir`, a passive scalar 1 in the hall (x ≥ 4 m, the gaps included) and 0 in the
room at t = 0, carried by the flow and diffusing as heat does (`scalarTransport`, D = ν/Pr). It
separates the hall's own air from room air that the leaf or the window has merely chilled.

## The model

- **Solver:** buoyantPimpleFoam (OpenFOAM v2512), air a perfect gas (c_p 1005 J/kg K,
  μ 1.82e-5 Pa s, Pr 0.71), **laminar**, PIMPLE with 1 outer and 2 pressure correctors, Euler in
  time at **Courant 1** with steps of at most 0.25 s, `limitedLinearV 1` for momentum,
  `limitedLinear 1` for energy and `limitedLinear01 1` for the tracer, a pressure reference in
  mid-room at (1.503, 1.174) m, p_rgh to 1e-7. No radiation.
- **Mesh:** a conforming blockMesh lattice from `scripts/make_mesh.py`, **10 cells across each gap**
  (1.0 mm in the undercut, 0.3 mm in the head gap), cells growing by at most 1.2 to neighbours, up to
  20 mm in the far room: **139,030 cells** open. The excluder is cut out of the same mesh
  (`scripts/block_gap.py`, then `subsetMesh`): every cell whose box meets the circle and three
  one-cell tips the staircase leaves, 958 cells, **138,072** blocked, so the two runs differ by
  nothing else. checkMesh -allGeometry -allTopology passes both; every cell is a rectangle.
- **Walls:** `bedroomLayer` (`src/doorLayer/wallLayer.C`) on floors and ceilings: each face balances
  the air's flux against a 24-cell layer behind it (wood k = 0.106 W/m K, ρ = 656.8 kg/m³,
  c_p = 1884 J/kg K; gypsum k = 0.1587, ρ = 640.7, c_p = 1130). It is `ceilingVsFloorVent`'s condition
  with one change, an `initialTemperature` per patch so that the hall's floor and ceiling start at
  10 °C. The glass, the leaf, the wall above it and the front door are `externalWallHeatFluxTemperature`.
- **Monitor:** `doorMonitor` (`src/doorLayer/doorMonitor.C`) writes every step the gross flow each way
  through the plane x = 4.0175 m across each gap and the heat it carries relative to 20 °C, the leaf's
  heat on each face, both rooms' mean air, the air's extremes and mass, the layers' stored heat, the
  largest ν_t/ν in each gap, and the tracer's reach. `wallHeatFlux` writes every wall's heat.
- **Planes:** the section on cell centres every 0.625 s (T, U, hallAir) as compressed VTK, and the
  fields every 30 s (the last two kept).

### The gap's mesh study

The whole answer runs through two slots 10 mm and 3 mm high, so the gaps were refined together, at
5, 10 and 20 cells across each, and the gross flow through each compared over 10-20 s, by when it has
settled. The study's rule was to stop where one level to the next moves the flow by under 3%, with
at least 10 cells across in production.

| cells across each gap | cells | undercut into the room (l/s per m) | head gap into the hall (l/s per m) |
|---|---|---|---|
| 5 | 125,580 | 1.553 | 1.548 |
| **10** | **139,030** | **1.527** | **1.523** |
| 20 | 257,655 | 1.526 | 1.522 |

Laminar at Courant 1, the production settings. 5 to 10 cells moves the flow by 1.7%, 10 to 20 by
0.06-0.08%, and Richardson extrapolation gives 1.5258 l/s per metre, 0.06% from the 10-cell value.
The observed order, 4-5, is only a diagnostic, since the 20-cell mesh also changes some cells away
from the gaps. The velocity across both slots is close to a parabola. A slot estimate
before any solve (an entry loss and a laminar channel loss in each gap, driven by the stack) gave
1.66 l/s per metre, 9% high. With the excluder on the 10-cell mesh the undercut's gross flow, both
ways together, is 0.7% of the open flow over the same window, and at most 0.8% in production.

**Three settings differ from the plan, each by its own rule.**

- **Laminar.** The plan was k-omega SST with a rule to go laminar if ν_t/ν in a gap stayed above 0.2
  over 10-20 s. At 10 cells it was 0.18, but at 20 cells it reached 0.24 over 10-15 s and with two
  outer correctors 0.24 over 5-10 s, so production is laminar. Against SST at 10 cells, laminar moves the gross flow by 0.4% and the hall
  air's reach by 0.8% at 10 s and 2.5% at 20 s. Nothing compared them past 20 s; with no turbulent
  mixing the cold layer may stay more concentrated, which would flatter the reach.
- **Courant 1.** The plan was Courant 2. Its A/B on the open run passed (gross flow within 0.04%), but
  the blocked run and the 20-cell run both ended in floating-point exceptions at Courant 2, so
  production runs at Courant 1.
- **240 s, not 300 s.** At Courant 1 a 300 s run projected 11.5 h on 8 cores, over our 10 h a run, so
  the window was cut to the first that fitted. The runs took 7.46 h (open) and 3.21 h (blocked).

## Results

`results/summary.txt`, from `scripts/extract_results.py`. Means over 10-240 s, per metre of door:

| | open | blocked |
|---|---|---|
| undercut, into the room (l/s) | 1.522 | 0.006 |
| undercut, into the hall (l/s) | 0.000 | 0.006 |
| head gap, into the hall (l/s) | 1.530 | 0.000 |
| head gap, into the room (l/s) | 0.000 | 0.009 |
| heat the room loses through the gaps (W) | 15.20 | 0.04 |
| heat the room loses through the leaf (W) | 20.84 | 18.60 |
| **the door, gaps and leaf (W)** | **36.04** | **18.64** |
| the wall above the door (W) | 5.08 | 5.05 |

Gross flows are each direction on its own; the net through a closed section is zero by
construction. Blocked, the 0.009 l/s into the room over the head is most likely the hall's air
expanding as it warms by 0.3 K, against the room's 0.08 K. Heat through a gap is mass flow × c_p × (T − 20 °C).

The hall's air along the floor, 20 mm up, in metres from the leaf, at least 10% of it
(`results/<run>/history.csv`, the monitor's cells):

| t (s) | 10 | 30 | 60 | 120 | 180 | 240 |
|---|---|---|---|---|---|---|
| open, now | 0.75 | 2.75 | 2.99 | 2.07 | 3.99 | 3.66 |
| open, farthest so far | 0.75 | 2.75 | 3.92 | 3.92 | 3.99 | 4.00 |
| blocked | 0.01 | 0.01 | 0.01 | 0.01 | 0.01 | 0.01 |

The open run's front is not a flat layer advancing steadily: it passes 1 m at 12.7 s, 3 m at 33 s and
3.9 m at 55 s, then breaks up and re-forms, reaching the far wall at 179 s. The blocked run's 7 mm is a
wedge of hall air trapped at the excluder's foot when the undercut closed, not air past it. By 240 s,
0.366 m³ per metre of the hall's air has come in under the open door, 3.8% of the room's section.

**The floor is cool in both runs.** The leaf's chilled sheet and the window's downdraught lay cool
room air along the blocked room's floor too. The lowest 100 mm of the room averages 18.9, 19.0, 18.8
and 18.5 °C at 60, 120, 180 and 240 s open, against 19.4, 19.4, 19.3 and 19.4 °C blocked (from the
planes). So the excluder stops the hall's air and takes 0.5-1 K off the chill near the floor; it does
not make the floor warm, and a blocked floor reading 0 m of hall air is still cool room air.

**Checks.** The air's mass holds to 9e-7 of the prepared state and to 1e-14 from step to step. The
heat budget, air, layers and every wall, closes over 10-240 s to 0.05% (open) and 0.08% (blocked) of
the energy through the door. The tracer balances: 3.81% of the room's section came in by 240 s
and the room holds 3.85% hall air. No pressure solve reached its iteration cap. The air stays
within 1.95-28.45 °C (open) and 2.02-26.73 °C (blocked), the cold end at the hall's front door.

## What it cannot

- **Side gaps.** This is the largest limit. A real door also leaks down both jambs, which a section
  through its middle cannot have. With 3 mm plain jambs the slot estimate keeps about 40% of a real
  door's exchange going past an excluder, where this section shows almost none. A door stop would cut
  the jambs' and the head's flow by an amount that depends on the door. The case does not say that
  an excluder stops the exchange.
- **The 3 mm head gap is ours, and it sets the flow.** With a 10 mm undercut the neutral height sits
  about 0.1 m above the floor, so almost all the stack falls across the head gap. The estimate gives
  0.7 l/s per metre with a 2 mm head gap and 2.6 l/s with 4 mm.
- **The door is as wide as the room.** A real 0.76 m door's cold layer spreads sideways and thins, so
  the reach here is an upper limit for a real room. It also depends on the threshold: at 20% hall air
  the farthest it gets is 2.15 m, at 5% the whole floor.
- **The blocked floor is cool too**, from the leaf and the window (above). The leaf loses 18.6-20.8 W
  per metre whether or not the gap is blocked, more than the gap carries.
- **No whole-house pressure.** Wind, the stack through a house and extractor fans can exceed the
  0.8 Pa here and drive the gap one way. That is what the building rule's undercut is for, and this
  section says nothing about the rule's purpose.
- **The model.** One floor (wood; a carpet would warm the layer less), laminar flow, no radiation, a
  fixed radiator output, thermal reservoirs for the leaf, four minutes from a sudden start rather than
  a settled winter evening.

## Sources

- Approved Document F, *Ventilation*, volume 1: 2021 edition paragraph 1.25 and 2026 edition paragraph
  1.21 (gov.uk, read 4 Nov 2026).
- A standard UK internal door leaf, 1981 x 762 x 35 mm.
- Trade guidance on UK fire doors (2-4 mm gaps at head and jambs), through a search summary,
  4 Nov 2026.
- Fabric draught excluder listings (30 cm round; 7 x 12 cm), through a search summary.
- R. Bornoff, a modelled room with a 5 mm door gap (Siemens, 2010): with a single crack the cold
  "puddle" stayed near the door, with a second gap it covered "nearly all the floor surface".
- Cheng et al., a multi-zone study meshing a door gap with cells of half its height (CEUR Vol-2394,
  paper 10), for scale.
- The room, its window and radiator: [`radiatorUnderWindow`](../radiatorUnderWindow); the floor and
  ceiling layers: [`ceilingVsFloorVent`](../ceilingVsFloorVent).

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with `wmake` and MPI, and Python 3 with
NumPy for the mesh scripts and `scripts/extract_results.py`.

    cd cases/doorGapExcluder
    ./Allrun open                # [nProcs], default 8
    ./Allrun blocked
    python3 scripts/extract_results.py runs results

`Allrun` compiles `src/doorLayer` into `$FOAM_USER_LIBBIN` as `libdoorLayer.so` and `src/doorTools`
into `$FOAM_USER_APPBIN`, writes the blockMesh case into `runs/mesh` (`python3 scripts/make_mesh.py 10
runs/mesh`, under a minute), copies `template/common/` and `template/<run>/` into `runs/<run>/`, cuts the
excluder out for `blocked`, makes the radiator's zone, writes the hydrostatic start and the tracer,
checks the mesh, writes the plane at t = 0, decomposes by scotch and solves; once both runs have
solved it writes `results/`. `./Allrun --setup-only <run> [nProcs]` stops before the solve;
`./Allclean` removes the runs. `python3 scripts/make_mesh.py 5 <dir>` or `20` writes the mesh study's
other levels.

The wall layer's type is still called `bedroomLayer`, as in `ceilingVsFloorVent`; its library here is
`libdoorLayer.so`, so building one case does not replace the other's.

From a clean copy of this case, `./Allrun --setup-only open` and `blocked` write both solved runs'
points, faces, owner, neighbour, boundary and zones byte for byte, and their t = 0 T, p, p_rgh and
hallAir; the initial mass, 15.99471014354582 and 15.9857114563403 kg per metre, is the solved runs'.
Five serial steps of each from there (to 1 ms) take the solved runs' time steps to nine figures, and
the first step's initial residuals for Ux, Uy, h and the first p_rgh solve match the solved logs'
to 3e-9 or better; later residuals differ by up to a few per cent, as serial and parallel GAMG do. Scotch's decomposition is not the same from one decomposePar to the next on our machine, so a
new solve will not repeat the solved runs bit for bit.

Each run writes 385 planes, about 1.4 GB (open), the monitor's every-step history (about 200 MB open)
and wallHeatFlux.dat (about 500 MB open). `results/` holds each run's history every 2.5 s and
`summary.txt`; no fields, meshes, planes or logs. The floor temperatures and the threshold sensitivity
above were read from the planes and are not written by `extract_results.py`.

The case was set up and solved by an agent on our own machine and checked by us. The files in
`results/` are what `scripts/extract_results.py` wrote from those two runs.
