# Airing an attic room: a roof window wide open, against a wall window

Is a roof window as good for airing a room in winter as a window in the wall? This case airs an
attic room for five minutes on a still 0 °C morning through a VELUX GGL PK08 centre-pivot roof
window turned wide open, and sets it beside [`windowAiring`](../windowAiring)'s room aired through
its wall window turned wide open. The two rooms have the same 4.0 × 3.5 m floor and nearly the same
volume, the two openings nearly the same area, and the same 60 W radiator stands under each
window. The numbers it reports are **the share of the room's own air replaced** and **the air
coming in through the window**. It is not about heat loss, heating costs or comfort.

One OpenFOAM case, two runs:

    ./Allrun roof      # the attic room, the roof window's sash turned 45 degrees, 0-300 s
    ./Allrun wall      # windowAiring's room, its sash turned wide open at 90 degrees, 0-300 s

**It is a still morning: no wind.** The air moves by buoyancy alone, the room's air at 20 °C
against the outdoor air at 0 °C, from the moment the windows open. Wind would change the numbers:
over a roof it sucks at a roof window, and on a wall it presses on or draws at the window
depending on the side it blows from. **It is an empty room**, its surfaces held at 20 °C, and only
the first five minutes. Read [What it cannot](#what-it-cannot) before any number here.

## The rooms

| | `roof` | `wall` |
|---|---|---|
| floor | 4.0 × 3.5 m | 4.0 × 3.5 m |
| walls and ceiling | a 1.0 m knee wall under the window, then the roof's inner face at 45° up to a flat ceiling 2.8 m above the floor, 1.8 m in from the knee wall; the opposite wall vertical | 2.4 m high, the window in one of the 3.5 m walls |
| air volume | 33.50 m³ | 33.60 m³ |
| the wall or roof the window is in | the roof, 0.24 m thick | the wall, 0.24 m thick |
| window | VELUX GGL PK08, a clear opening at the lining 0.887 × 1.339 m (1.188 m²), its lower edge 0.30 m up the slope from the knee wall's top, centred in the room's width, its linings square to the roof; it spans 0.947 m of height, 1.21 to 2.16 m above the floor | windowAiring's: a clear opening 1.0 × 1.2 m (1.200 m²), sill 0.90 m above the floor, centred in the room's width |
| sash, wide open | turned 45° about its centre, the VELUX way, top edge into the room: horizontal (below) | turned on its side hinge to stand at 90° to the wall (windowAiring's `open`) |
| radiator | windowAiring's box, 0.083 × 0.60 × 1.0 m, 0.15 m above the floor and 0.04 m off the knee wall, under the window, 60 W | the same box under the window, 60 W |
| outside | still air at 0 °C over the roof, 1.5 m deep off its outer face, along the slope from 1.0 m below the opening to 1.5 m above it, and 0.75 m beyond each side wall, open on every face but the roof | windowAiring's: 1.5 m deep beyond the wall, from 1 m below the floor to 3.4 m up, 2.5 m either side of the window; and 1.5 m of still air beyond the inner wall, which the room never reaches (below) |
| surfaces | the room's floor, walls, roof and ceiling held at 20 °C; the roof's outer face, the opening's linings and the sash adiabatic | the same, windowAiring's |
| start | the room's air at rest at 20 °C, the outdoor air at rest at 0 °C in its own barometric pressure; at t = 0 the window is open | the same |

**The roof window.** VELUX's GGL is the common centre-pivot roof window: its sash turns about a
horizontal axis across its middle, operated from a control bar along its top. The PK08's clear
opening at the lining is 887 × 1339 mm (VELUX, *Product information: Centre-pivot roof window
GGL*, 2017, "Lining measurements", p. 2), 1.19 m², the same as the wall window's 1.2 m². The sash
"is frictioned to stay in a pivot position to maximise ventilation" and locks only "slightly ajar
or 180°" (VELUX Australia's GGL sheet, 2022); VELUX's motors for it open it at most 200 mm
(KMG 100K). **Which way it turns** is in VELUX's product sheet for the manual GGL, whose drawing of
the open window has the top edge, with the control bar, swung into the room and the bottom edge out
over the roof; the window is "top-operated" and leaves "the freedom to place furniture
underneath".

**Wide open** is the sash turned 45°, about as far as a manual sash goes in use (turned further it
heads for its cleaning position), and far more than the motor's 200 mm, about 17° on this sash.
In a 45° roof, turned the VELUX way, the sash then lies horizontal across the opening like a
shelf, its top half in the room and its bottom half out over the roof. It is a solid slab 80 mm
deep (windowAiring's sash depth; VELUX gives none), flush with the roof's outer face when shut,
1.338 m long, turned about its centre, 0.04 m inside the roof's outer face and halfway up the
opening. Turned, it runs from 0.43 m out over the roof (x −0.124 m) to 0.39 m below the sloped
ceiling (x 1.214 m), at y 1.787 to 1.867 m, across the opening's width. It splits the opening in
two: below it, on the eaves side, 0.721 m² open at the roof's inner face (0.508 m² at its outer
face), and above it, on the ridge side, 0.366 m² (0.579 m²), read off the mesh
(`results/roof/mesh.json`).

**The radiator under the roof window** stands where the wall window's stands, on the wall under
the window, so that only the window differs between the panels. That is our choice: in a real
attic the radiator often stands elsewhere.

### The wall window

The `wall` run is windowAiring's `open` run built again, with three changes:

- **the barometric outdoor boundary**, the same as `roof`'s (below), in place of windowAiring's
  p0 = 1e5/(1 + g y/(R T));
- **a finer mesh across the window's width**: 52 cells of 19.2 mm over its 1.0 m, where `open`
  has 28 graded ones; 1,052,456 cells in all against `open`'s 526,848;
- **the mesh runs on past the room's inner wall**, refined there as at the window, with 1.5 m of
  outdoor air beyond it. The inner wall is solid, so that air is a second region of the mesh,
  joined to nothing; it holds still (the room never reaches it) and only costs cells. It is
  kept so that the setup reproduces the solved run's mesh.

Everything else is `open`'s: the room, the window, the sash as a baffle at 90° on its hinge side,
the radiator, the surfaces, the model. The two builds agree: over the five minutes `wall` takes in
0.2351 kg/s on average and `open` 0.2351 kg/s (19.75 room volumes an hour both); at 300 s `wall`
has replaced 92.0% of the room's air and `open` 91.3%. That is two meshes and two forms of the
outdoor boundary, not a mesh study, but it puts the wall window's numbers to within about a
point.

## The model

`scripts/make_case.py <run> <dir>` writes every dictionary, the initial fields and the run's own
Allrun, with [`windowAiring`](../windowAiring)'s generator (`../windowAiring/scripts/make_case.py`)
for everything but the roof run's mesh.

- **Solver and physics, windowAiring's:** buoyantPimpleFoam (OpenFOAM v2512), air as a perfect
  gas (c_p 1005 J/kgK, μ 1.82e-5 Pa s, Pr 0.71), k-omega SST with wall functions and the
  buoyancy source on k, PIMPLE with 2 outer and 2 pressure correctors, Euler in time at
  Courant 1, limitedLinear for energy and turbulence and limitedLinearV for momentum, p_rgh to
  1e-7. The radiator is an enthalpy source of 60 W spread over its box, through which the air
  passes freely (`radiatorUnderWindow`'s reasons for 60 W, about a tenth of a real radiator).
- **The outdoor boundary, barometric:** the open faces hold the still 0 °C air's own pressure at
  each face's height, p0 = 1e5 exp(−g y/(R T)), as `prghTotalPressure` less the dynamic head on
  inflow; air coming in is at 0 °C. Every cell starts at that pressure, with its own density in
  p_rgh (`barometric_p.py`), so the solve starts at rest. Why this form and not 1e5/(1 + g y/(R
  T)) is in [`dryIceCauldron`](../dryIceCauldron), "How the case got here".
- **The room's own air** is a passive scalar s, 1 in the room at the start and 0 outside,
  carried with T's diffusivity. The share replaced is 1 − ∫ρs over the room / the room's mass at
  the first step, windowAiring's definition.
- **Monitors, every step:** ∫ρs over the room, its mass, its mass-average T and s, the gross mass
  flow each way through the opening (`opening1`, on the roof's inner face for `roof` and in the
  frame's plane x = 0 for `wall`), the room's own air leaving (Σφs), and the scalar's budget
  through the opening (`fluxBudget`, s's own face flux as the scalar transport discretises it).
  For `roof`, the gross flows through the eaves and ridge sides of the sash too. Two planes every
  1.25 s for the clip: the mid-plane through the window, and a floor plane 0.1 m up.
- **The roof run's mesh** (`scripts/build_roof.py`): gmsh 4.15.2 meshes the room's section with
  quads, 20 mm over the opening and within 0.30 m of it, growing to 90 mm in the room and
  outdoors (7,173 cells), and the section is swept across the room over 130 layers, 20 mm over the
  opening's width and 0.30 m either side; cells are kept in the air and in the opening's width
  where the slab is not. 819,902 cells, `checkMesh` OK, one region, non-orthogonality at most
  55.4°, skewness at most 0.89. The room's air volume on the mesh is 33.503 m³, and the
  radiator's box 1,100 cells.
- **The wall run's mesh**: windowAiring's blockMesh box cut down with subsetMesh, as above.
  1,052,456 cells, `checkMesh` OK, two regions.

## How the case got here

The roof run was first solved with the sash turned the other way, top edge out and bottom edge
in: the 2017 product information it was built from does not say which way the sash turns, and
the build assumed the top went out. Turned that way in a 45° roof the sash stands vertical, its lower half hanging in the room,
and the opening is split into two passages side by side. That run replaced 86% of the room's
air in five minutes and took in 0.227 kg/s on average. VELUX's product sheet for the manual GGL
shows the top edge going into the room, so the roof run was built again with only the sash
turned the other way about the same axis, and solved again from rest. Only that run is here;
the first is not kept.

## Checks

- **The generator against the solved runs.** From a clean copy, `./Allrun --setup-only roof`
  and `--setup-only wall` wrote the solved runs' meshes (points, faces, owner, neighbour,
  boundary, cell and face zones) and every initial field, the barometric p and p_rgh included,
  byte for byte, at 819,902 and 1,052,456 cells. Their `0.orig`, `constant/`, `fvSchemes`,
  `fvSolution` and `decomposeParDict` have the solved runs' values and differ only in comments
  and layout. Their monitors were tidied (the solved runs also had probes), and `fluxBudget`'s
  code was rewritten for one opening; a few steps of the new `roof` setup gave the solved run's
  first steps' monitors and budget to four or five figures.
- **The scalar's budget** closes to 0.30% (`roof`) and 0.63% (`wall`) of what has left the room at
  300 s, and within 0.74% and 0.63% at every write.
- **The outdoor air stays at 0 °C** where the roof window draws it in
  (`results/roof/outdoor_check.txt`, from the solved run's mid-plane, `scripts/outdoor_check.py`).
  The outdoor cells within 0.3 m of the roof below the sash and up to 0.44 m along the slope
  average 0.00 °C from 1.25 to 300 s, 0.47 °C at most. Further along, under the sash's outer
  half, a pocket of room air leaves along the slab's underside (the eaves side's own outflow,
  0.020 kg/s on average), at 6-11 °C on average from 30 s on. The warm plume leaves through the
  box's outer face at up to 1.4 m/s; the other open faces reach 1.04 °C at most.
- **Still air outside, with the window shut.** Every outdoor cell over the roof is fed by the
  window, so the outdoor air moves with its draw from the start: the outer half of the box,
  more than 0.99 m off the roof's inner face, at a median 9.4e-3 m/s on the mid-plane at 1.25 s.
  A copy of the first build of the roof run (the sash the other way, the same box and boundary)
  with the opening's faces made a wall held the same air at a median 2.1e-6 m/s at 1.25 s. In
  the `wall` run, the air beyond the solid inner wall, which nothing feeds, held a median
  7e-7 m/s at 1.25 s.
- **The sash on the mesh.** The sash patch spans x −0.124 to 1.214 m, y 1.787 to 1.867 m and z
  1.3065 to 2.1935 m exactly, since the section is fitted to the slab.
- **Both runs ended cleanly** at 300 s, in 25,233 steps (`roof`) and 14,808 (`wall`).

## Results

From `results/summary.txt` and `results/<run>/history.csv`, which `scripts/extract_results.py`
writes from the runs' per-step monitors. The air in is the gross mass flow into the room through
the opening, and as volume of 0 °C air (1.275 kg/m³).

| | `roof` | `wall` |
|---|---:|---:|
| **share of the room's own air replaced, at 60 / 120 / 300 s** | 22.9 / 43.7 / **72.7%** | 41.6 / 67.7 / **92.0%** |
| **air in, mean over 0-300 s** | **0.160 kg/s**, 451 m³/h, 13.5 room volumes an hour | **0.235 kg/s**, 664 m³/h, 19.8 an hour |
| air in at 300 s | 0.144 kg/s | 0.202 kg/s |
| the room's mass-average temperature at 300 s | 11.8 °C | 8.3 °C |
| over the last minute | 0.27 K cooler, 6.0 points more replaced | 0.24 K cooler, 4.5 points more replaced |

**The roof window takes in 68% of the wall window's air** over the five minutes, and replaces 73%
of the room's air against 92%.

The horizontal sash lies across the opening like a shelf. The cold air comes in below it, on the
eaves side, and falls down the knee wall past the radiator to the floor; the warm air leaves above
it, on the ridge side, and rises up the roof outside. Nearly all the flow follows that split: over
the five minutes the eaves side took in 0.157 kg/s and let out 0.020 kg/s, and the ridge side let
out 0.136 kg/s and took in 0.003 kg/s.

**Against the single-opening formula.** A single opening swaps air by buoyancy at a rate that
goes as its width times its height to the power 1.5 (Linden 1999; BS 5925). In a 45° roof the
1.339 m opening spans only 0.947 m of height, against the wall window's 1.2 m, so the formula
alone gives the roof window 0.887 × 0.947^1.5 / (1.0 × 1.2^1.5) = 0.62 of the wall window's flow.
The run gives 0.68. The formula was not made for a sloped opening with a sash across it, and the
two are close.

**The share replaced and the inflow part.** The roof window's share at 300 s is 79% of the wall
window's while its inflow is 68%: the wall room's share flattens as it nears all of its air.
The two rooms also let out air of different ages. Over the five minutes the air leaving the wall
window carries 1.56 times the room's mean share of its own air (`results/summary.txt`): the cold
air lies on the floor and the window lets out the room's old air from the top. The air leaving
the roof window is nearer the room's mean, 1.16 times it, so the roof room loses less of its own
air for each kilogram that leaves.

## What the clip shows, and what it does not

**It shows** each room's mid-plane through its window, the roof window above and the wall window
below, from the moment the windows open to 300 s, 15× fast, on one temperature scale, with
parcels of air carried by the solved flow in the plane; the walls, the roof, the sashes and the
radiators are drawn over it. Each panel has one number, the share of the room's own air
replaced, in whole percent: it ends at 73% for the roof window and 92% for the wall window.

**It does not show** the flow across the room's width, the air coming in through the parts of
each opening off the mid-plane, flow rates, heat loss or costs.

## What it cannot

- **A still morning at 0 °C.** No wind, which over a roof sucks at a roof window and on a wall
  presses on or draws at a window, and changes the exchange of both; one temperature difference,
  20 K at the start.
- **One opening of each window.** The roof window wide open, turned 45°; not ajar or tilted,
  whose gaps depend on how the sash sits in its frame, nor the ventilation flap, nor a motorised
  window stopped at 200 mm, nor a top-hung roof window, whose sash swings out from its top.
- **A drawn window.** The sash is a plain slab 80 mm deep with no frame, seals or control bar,
  and the linings are square to the roof; no flashing or outside detail.
- **The radiator's place and size.** Under the roof window by our choice, and 60 W, about a tenth
  of a real radiator's, which does not turn up as the room cools.
- **Warm surfaces and an empty room.** The floor, walls, roof and ceiling are held at 20 °C, as
  masonry nearly is over five minutes but a lightweight attic finish may not be, and there is no
  furniture, door gap or other leak.
- **The first five minutes,** from a room uniformly at 20 °C. Neither room has settled at 300 s.
- **Two rooms on two meshes,** URANS with k-omega SST and wall functions, no mesh or time-step
  study, one realization of each run. The wall window's two builds agree to within about a
  point.
- **A stratified room reads high against a well-mixed decay,** as in windowAiring; the inflow is
  the figure to set beside measured air-change rates.

## Sources

- VELUX, *Product information: Centre-pivot roof window GGL*, edition 2.0, 2017, "Lining
  measurements", p. 2:
  https://www.roofgiant.com/resources/files/external-product-information_ggl.pdf
- VELUX, product sheet for the manual centre-pivot roof window GGL, p. 1 (the open window's
  drawing, "top-operated"):
  https://contenthub.velux.com/api/public/content/5f8c1-28578-b14c5_downloadOriginal
- VELUX Australia, GGL product sheet (2022):
  https://afd-marketing.velux.com/-/media/marketing/au/downloads/factsheets/aust%20ggl%20product%20sheet%202022%20web.pdf
- VELUX, KMG 100K window motor, "Max 200 mm":
  https://contenthub.velux.com/api/public/content/c9320-8e306-5e478_downloadOriginal
- P. F. Linden, "The fluid mechanics of natural ventilation", Annual Review of Fluid Mechanics 31
  (1999); BS 5925, the single-opening formula.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with NumPy;
the roof run's mesh needs gmsh (`pip install gmsh==4.15.2 numpy`; set `PYTHON` to the interpreter
that has them if it is not `python3`). Another gmsh version will mesh the same outline but not to
the same cells. `scripts/outdoor_check.py` needs PyVista. The case uses
`../windowAiring/scripts/make_case.py`, so keep the two cases side by side.

    cd cases/roofWindowAiring
    ./Allrun roof                    # [nProcs], default 16
    ./Allrun wall
    python3 scripts/extract_results.py runs results
    python3 scripts/outdoor_check.py runs/roof > results/roof/outdoor_check.txt
    cp runs/roof/mesh_measurements.json results/roof/mesh.json

`Allrun <run>` writes the run into `runs/<run>/` with `scripts/make_case.py`, then runs the
Allrun written there. For `roof`: `build_roof.py` (the mesh, its zones and
`mesh_measurements.json`), checkMesh, the initial fields, each cell's and outdoor face's
barometric pressure, and decomposePar. For `wall`: blockMesh, subsetMesh to the air, the outer
walls as a patch, the sash as a baffle, the zones, the initial fields, the barometric pressure,
checkMesh and decomposePar. It then writes the t = 0 planes from the initial fields and solves
0-300 s, writing the planes every 1.25 s and the fields every 60 s (the last one kept).
`./Allrun --setup-only <run>` stops before the t = 0 planes and the solve, in under a minute.
`./Allclean` removes the runs.

The roof run was solved 0-30 s and then 30-300 s from the 30 s write, on 16 ranks, in 2,075 and
14,646 s of wall time; the wall run 0-300 s on 16 ranks in about 13,600 s. `results/` holds each
run's history, every step's monitors sampled at the plane writes, the summary, the roof mesh's
measurements and the outdoor-air check; no fields, meshes, planes or logs.

The roof run was built by an agent on our own machine from a written brief, and checked and
solved there; it was sent back once, when the sash was found turned the wrong way, and solved
again. The wall run was solved there too.
