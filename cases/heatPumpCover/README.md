# A heat pump's outdoor unit in the open, and inside a slatted cover with a lid

People box in the outdoor unit of a heat pump or a mini-split with a slatted cover to hide
it, and installers say the unit then breathes its own exhaust. In heating mode the unit
blows out air colder than the outside air. This case asks where that air goes: in the open,
does it blow clear while the coil draws in outside air, and inside a louvred cover with a
lid, how much of it comes back through the coil? The number it reports is **how much colder
than the outside air the air entering the coil is**. It is not about the heat pump's
efficiency, frosting or noise, though a colder coil inlet means more of the first two and
less heat.

The same unit, a Daikin ERGA06EV-class air-to-water outdoor unit, is switched on twice on a
cold, still day (2 °C), once standing in the open and once inside a louvred cover with a
solid lid, and followed for 60 s from the fan's switch-on. One OpenFOAM case, one mesh, two
runs:

    ./Allrun open        # the unit alone
    ./Allrun covered     # the same mesh less the cover's cells, which become walls

## The unit

From Daikin's documents for the Altherma 3 R outdoor unit ERGA06EV, a common European
air-to-water split with a single propeller fan blowing out of the front and its coil across
the back, the shape of most mini-split outdoor units in the US too:

| | value | from |
|---|---|---|
| casing | 740 mm tall, 884 mm wide, 388 mm deep | technical data book ERGA04-08EV (EEDEN20) |
| coil | 0.658 m² face area over a length of 920 mm, so about 0.715 m tall | the same |
| fan | one propeller fan, horizontal discharge, 2,520 m³/h rated outdoor airflow (ERGA06) | the same |
| grille | square, over most of the front, from 15 mm above the casing's bottom to 80 mm below its top | scaled from the dimensional drawing 3D130871, p. 15 |
| clearances | more than 250 mm from the wall to the air inlet, more than 350 mm in front of the outlet, at least 300 mm free below the unit | installer reference guide 4P629085-1, pp. 56, 58 and 65 |
| the coil's drop | 3.3 K (below) | the data book, EN 14825 condition B |

At EN 14825 condition B (2 °C dry bulb, 1 °C wet bulb), for an average climate and 35 °C
water, the data book gives the ERGA06 Pdh = 3.9 kW at COPd = 4.25. The heat taken from the
outside air is 3.9 × (1 − 1/4.25) = 2.98 kW. Through 2,520 m³/h of air at 2 °C
(ρ c_p V̇ = 1.283 × 1005 × 0.700 = 903 W/K) that is a drop of **3.3 K**. It is all taken as
sensible heat. Some of it is really latent (moisture and frost on the fins), so 3.3 K is an
upper bound.

The same page of the installer guide names the effect this case is about: wind blowing
against the outlet "causes short circuit (suction of discharge air)", which may result in
"deterioration of the operational capacity" and "frequent frost acceleration in heating
operation".

So the unit stands 250 mm from the house wall on 300 mm feet, at x 0.250-0.638 m from the
wall and y 0.300-1.040 m up.

## The cover

No single seller publishes every dimension of a cover, so it is put together from covers
sold to hide outdoor units and one published plan:

- **Depth:** Decoclim's aluminium cover, size L, "internal dimension H 95 x W 110 x D
  55-70 cm", with louvres "to facilitate incoming and outgoing air flows", the rear panel an
  option for units away from a wall, and adjustable feet of 1-3 cm. A unit 250 mm off the
  wall and 388 mm deep needs the full 70 cm.
- **Height:** Sentimo's Breezebox is sold for heat pumps up to "Height: maximum 108 cm". A
  unit raised 300 mm stands 1.04 m tall, which Decoclim's 95 cm does not clear, so the lid
  is at 1.10 m inside.
- **Louvres:** Kreg's published plan for a louvred screen for AC units: 1/2" × 3 1/2"
  boards (12.7 × 89 mm) at 3 1/4" (82.6 mm) pitch, each 2 1/2" lower at the front than at
  the back across a 3 1/2" post, a slope of about 35° down outward.
- **Sides:** Decoclim's size L drawing and photographs show a solid top, a louvred front and
  louvred sides with corner posts, and an open back. Its internal width, 1.10 m, puts the
  side louvres 0.108 m from the unit's ends. The side boards are taken to be the front's.

So the lid is solid, 20 mm thick, from the wall to the front at 1.10-1.12 m. The front and
the side are louvred, 13 boards each, from 30 mm above the ground (the feet) to the lid,
with their inner edges 0.70 m from the wall and 0.55 m from the symmetry plane, and a
corner post between them. The back is open and the house wall closes it. The grille ends up
62 mm from the louvres, against the 350 mm Daikin asks for. The top board of each panel is
filled out to the lid with a 7 × 10 mm wedge, so that it meets the lid on a face rather than
an edge.

## The model

- **A 3-D half model.** A symmetry plane cuts the unit through the middle of its width and
  the centre of its fan. The domain runs from the house wall out to 5 m (x), from the ground
  up to 3.5 m (y) and along the wall to 3 m (z). The far side, the top and the far end are
  open to still air at 2 °C at hydrostatic pressure; the wall and the ground are adiabatic
  no-slip walls. In the half model the unit is at x 0.250-0.638, y 0.300-1.040, z 0-0.442.
- **Air:** `buoyantBoussinesqPimpleFoam` (OpenFOAM v2512), Boussinesq about 2 °C,
  k-omega SST with wall functions. PISO (one outer corrector, two pressure correctors),
  Euler in time, linear-upwind for U and limitedLinear for T, a Courant number up to 1 and
  no step longer than 10 ms.
- **The unit's casing** is a closed box of wall (`unitWalls`) from the coil to the grille.
  Its only openings are the coil's back face and the grille.
- **The fan** is a momentum source in a duct of the grille's cross-section (below).
- **The coil** is a porous zone across the unit's back, 40 mm deep, with a Darcy drag of
  610 1/s and a capped cooling (below).
- **Start:** everything at rest at 2 °C; the fan and the coil come on at t = 0, and the run
  goes to 60 s.

`constant/fvOptions` is the one file that sets up the fan and the coil, and both runs read it
unchanged.

### The mesh

One snappyHexMesh mesh serves both runs (`mesh/system/`). The background blockMesh has cells
of about 0.15 m, laid out so that the refined faces fall on the coil's and the fan's faces.
It is refined to level 2 (about 40 mm) in x 0-2.5, y 0-1.6, z 0-1.2 m, level 3 (about 20 mm)
in x 0-0.85, y 0-1.2, z 0-0.7 m, and level 4 (about 10 mm) at the casing's and the cover's
surfaces and through the coil. The casing's plates are 12.5 mm thick and the boards 12.7 mm
(15.5 mm measured vertically), so at level 3 the cells that keep them solid would have
holes. At level 4 each 55 mm gap between boards has about six cells across it.

The casing is cut out of the mesh as the wall patch `unitWalls`. The cover is kept in it as
the cell zone `coverCells`, snapped to its surface. `open` is this mesh as it is, with the
cover's cells as air. `covered` is the same mesh less `coverCells` (`subsetMesh`), whose
exposed faces are the wall patch `coverWalls`. Every cell of `covered` is a cell of `open`,
with identical points; the only cost of sharing the mesh is that the open run keeps the
cover's snapped cells, and the jet crossing them sets its time step.

- Cells: `open` 447,914 (95% hexahedra); `covered` 409,361.
- `checkMesh` passes `open` (non-orthogonality at most 64.8, skewness at most 1.46).
  `covered` fails one check: 19 faces of `coverWalls` with skewness 4.1-6.0, all on the
  underside of front boards near their outer edge. It ran without trouble.
- The coil zone is 14,720 cells, 0.012425 m³, four cells deep; its outflow face is 0.30745 m²,
  exactly 0.715 × 0.430 m. The fan zone is 6,889 cells, 0.020781 m³, with a cross-section of
  0.20801 m².

**A rebuilt mesh is not the solved one to the cell.** snappyHexMesh runs on 8 ranks and
rebalances the mesh between them with scotch several times while it refines, and scotch on
our machine splits the mesh differently every time. Three rebuilds from a clean copy with
the committed dictionaries and byte-identical surfaces gave `open` 447,662, 447,543 and
448,068 cells (solved: 447,914) and `covered` 409,109, 408,990 and 409,515 (409,361), all
within 0.1%. The cover was 38,553 cells and the coil zone 14,720 every time; the fan zone
was 6,896 cells against the solved 6,889. Each rebuilt `open` passed `checkMesh`; each
`covered` failed only the skewness check, on 12-19 faces of `coverWalls`, as the solved one
did. The run dictionaries and initial fields `Allrun` writes are those of the solved runs;
only the fan's and coil's comments in `fvOptions` were rewritten for this repository.

### The fan

The fan holds half the rated 2,520 m³/h, 0.350 m³/s in the half model, in both runs,
whatever the cover does to the pressure. It reaches full flow over the first 2 s. It is
`rampedMeanVelocityForce` (`src/rampedMeanVelocityForce`, compiled by `Allrun`), OpenFOAM's
`meanVelocityForce` with its target velocity ramped linearly from zero over `rampTime`.

The fan zone as meshed gives a target of 1.6826 m/s for 0.350 m³/s. But the duct's
cell-centred velocity is checkerboarded along x: a body force that starts and stops at a
face excites the odd-even pressure mode in the flux interpolation, and the zone mean of the
cell values runs above the flow the face fluxes actually carry. A 3 s pilot with that target
moved 0.3234 m³/s at full flow, 92.4% of the rated flow, through the coil and the fan's
downstream face alike. The target was therefore scaled by 0.350 / 0.32338 to 1.82113 m/s,
with which the pilots moved 0.3515 m³/s (open) and 0.3482 m³/s (covered), within 0.5% of the
rated flow. The long runs held 0.3515 and 0.3490 m³/s over 50-60 s. The checkerboard stays
inside the duct; the plenum upstream and the jet beyond the grille are smooth.

### The coil

A coil cannot cool air below its refrigerant's evaporating temperature. US 10,815,409 B2
(Honeywell, 2020), Example 5, gives a residential air-to-water heat pump evaporating at
about 0.5 °C in about 8.3 °C outdoor air, an approach of 7.8 K. The same approach at 2 °C
gives about -5.8 °C, taken as **Ts = -6 °C**. Using the refrigerant's temperature for the
surface's is the coldest choice, so the cap is a lower bound.

The coil relaxes the air towards Ts as it crosses: dT/dx = -(NTU/L)(T - Ts), so a pass at any
speed leaves at T_in - ε(T_in - Ts), with ε = 3.3 / (2 + 6) = 0.4125, and no air can be cooled
below -6 °C. A 2 °C inlet loses the data book's 3.3 K; air that is already colder loses less.
The source is implicit in T (a coded `scalarCodedSource`), so it is stable at any step.

The source uses the cell's Ux, which in the coil runs at about 87% of the face flux, so with
the nominal NTU/L of 13.297 1/m the pilot's flow-weighted drop was 88.9% of ε(T_in - Ts) at
full flow. NTU/L was scaled by 1.1643 to 15.482 1/m. On the verifying pilots the drop was
1.001 of the design value at full flow, and over 50-60 s of the long runs it was 3.199 K
against 3.199 K (open) and 2.882 K against 2.913 K (covered).

Nothing else in `fvOptions` changed after the pilots; each of the two values carries a
comment saying why.

## Checks before the runs

- **Still air.** `open` with the fan and coil off, for 5 s on the production settings: the
  largest speed anywhere was 1.4e-11 m/s at 5 s, and at most 3.2e-12 m³/s crossed each open
  boundary each way.
- **Signs.** `open` with the sources on, 100 fixed steps of 4 ms from rest: the fan held its
  ramp exactly; no coil cell had Ux < 0; the coldest air was -0.44 °C, in the coil's last
  cells, and the warmest 0.0045 K above 2 °C. Every bit of the fan's air went through the
  coil and out of the grille; no other face of the casing carried any flow. On an earlier
  2-D mesh, with the cooling 20 times stronger, no coil cell fell below -6 °C.
- **Pilots,** both runs to 3 s, which fixed the fan's target and NTU/L above.
- **The warmest air** in the long runs is 2.02-2.06 °C (open) and 2.15-2.17 °C (covered)
  over 50-60 s, in the shear layer at the jet's cold lower edge. That is limitedLinear
  overshooting; the sources cannot heat.

## Results

Means over 50-60 s, in the half model, from `results/<run>/summary.csv` (the face-flux
monitors), `results/<run>/plane_integrals.csv` (cut planes, which read about 10% low next to
walls) and `results/coil_number.csv`:

| | open | covered |
|---|---:|---:|
| **air entering the coil, below the outside air** | **0.004 K (0.0)** | **0.717 K (0.7)** |
| the run's coilInT monitor, uncorrected (see below) | 0.246 K | 0.937 K |
| fan flow | 0.3515 m³/s | 0.3490 m³/s |
| coil's drop per pass (design) | 3.199 K (3.199) | 2.882 K (2.913) |
| air entering the space behind the unit from above / below / its open end | 0.101 / 0.078 / 0.168 m³/s | 0.042 / 0.120 / 0.182 m³/s |
| air coming in under the unit, its temperature (cut plane) | 1.99 °C | 0.80 °C |
| air coming back in through the cover's front: under the lowest board / through the boards | (no cover) | 0.018 / 0.058 m³/s |
| coldest air anywhere, 0-60 s | -2.09 °C | -3.39 °C |

**In the open the coil breathes outside air: 0.0 °C.** The jet blows clear, and the air
entering the space behind the unit is at 2 °C from every side. Only between about 6.5 and
11 s from switch-on, while the start-up flow settles, does the shown value read 0.1 (at
most 0.12 K).

**Under the cover the air entering the coil is 0.7 °C colder than the outside air.** The
louvres, sloping 35° down outward, turn the jet down onto the ground. The lid traps a cold
layer under itself, and some of the exhaust comes back in through the lowest boards and
under the unit: 0.075 of the coil's 0.349 m³/s comes back in through the cover's front,
most of it below 0.2 m, and the air arriving under the unit is 1.2 K colder than outside.
**About a fifth of the coil's air is exhaust it has already cooled once**: 0.075 of
0.349 m³/s is 21%, and the 0.72 K deficit is 20% of the 3.6 K by which the exhaust leaves
colder than outside (0.72 K + the coil's 2.88 K). Because the air arrives colder, the coil
takes 2.88 K off it rather than 3.20 K.

Both runs settle quickly: `open` holds its value from about 2 s, and `covered` from about
5 s, after which its number moves by no more than ±0.03 K to 60 s.

### The run's own number reads 0.24 K too cold

`coilInT`, the face-flux-weighted temperature on the coil's inflow faces, gives 0.246 K below
outside in `open` over 50-60 s. It already gave 0.225 K at 0.25 s, before any exhaust could
have reached the back of the unit. The face values are interpolated between the outside cell
and the first coil cell, which the coil has already cooled, so the monitor reads part of the
coil's own cooling.

Sampled from the cell values one cell upstream of the inlet face (x = 0.2445 m,
`system/inletUpwindDict`, `interpolate false`, weighted by positive Ux) at 50, 55 and 60 s,
the air entering is 0.005 K below outside in `open` and 0.71 K below in `covered`; three
cells upstream (x = 0.22 m) gives 0.002 K and 0.80 K (`results/inlet_upwind.txt`). So the
monitor's offset is a fixed fraction F of the air's distance from the coil's -6 °C surface:
0.0301 in `open` and 0.0304-0.0305 in `covered`. `scripts/coil_number.py` takes it out of
every write with F = 0.0302:

    T_in = (T_face - F Ts) / (1 - F)

which agrees with the upstream cells to within 0.002 K at those three times in both runs,
and gives 0.004 K and 0.717 K over 50-60 s. The correction is 0.24 K in `open` and 0.22 K in
`covered`. It corrects the measurement only; nothing in the solve changes. `summary.csv`'s
column `number_K_below_outside_air` is the uncorrected monitor, and `coil_number.csv` has
both.

## What the clip shows, and what it does not

**It shows** the symmetry plane, the vertical section through the middle of the unit and its
fan, over x -0.10 to 2.25 m and y -0.06 to 1.50 m, twice: the open unit on top and the covered
one below, from switch-on, 60 s of flow at 3×. The colour is the air temperature on one
scale, -2.5 to 2 °C, with parcels carried by the solved in-plane velocity. The cover's lid and
boards are drawn where the solved plane has no air. The unit is drawn as a solid box with the
coil, the fan and the open grille, because the cell values inside the duct are checkerboarded
(above). Each panel has one number, "coil air X °C below outside": the corrected value, as a
2 s running mean to 0.1 K (`results/coil_number.csv`, `shown`). It ends at 0.0 in the open
and 0.7 under the cover.

**It does not show** the flow off the symmetry plane, where about half the air reaches the
back of the unit round its end, or anything about the heat pump's capacity, efficiency, frost or
running cost.

## What it cannot

- **Half a unit.** The model is cut by a symmetry plane through the middle of the unit, so
  the unit, the cover and the flow are mirror images about it. On the real ERGA06 the fan's
  grille sits towards one end of the front and the coil wraps round that end (data book
  drawing 3D130871); here the grille is centred and the whole coil lies flat across the back
  (0.615 m² against the real 0.658 m²). Any flow that would cross the middle of the unit from
  one side to the other cannot.
- **The coil.** It cools every pass by the same fraction of its distance from -6 °C, at any
  speed. A real coil's effectiveness falls a little as the air speeds up, and some of its
  heat is latent (moisture and frost), so the real drop is a little smaller.
- **The fan.** Its flow is held fixed. A real fan would lose some flow against the louvres,
  and its inverter would change speed with the load.
- **Wind and frost.** The air is still, and the coil does not frost up. Daikin names wind on
  the outlet as another cause of the same short circuit.
- **The start.** The coil cools from switch-on. A real compressor takes minutes to come up to
  speed, and the unit defrosts from time to time.
- **One mesh, one model, 60 s.** No mesh or time-step study, and URANS with k-omega SST. The
  60 s was shortened from 120 s for cost; both runs had settled well before it.

## Sources

- Daikin, technical data book ERGA04-08EV (EEDEN20): casing, coil, fan, airflow, Pdh and COPd
  at condition B, dimensional drawing 3D130871. Copy read on 12 Oct 2026 at
  https://cdn.byggtjeneste.no/nobb/e4283d79-2785-40d8-811f-cafde332b037
- Daikin, installer reference guide ERGA04~08EAV3(A) + EHBH/X (4P629085-1, 2020.08),
  pp. 56, 58 and 65: clearances and the short circuit; the older guide for the ERGA04~08DAV3
  (4P499573-1, 2017.12, p. 21) gives the same figures.
- EN 14825, part-load condition B: 2 °C dry bulb, 1 °C wet bulb.
- US 10,815,409 B2, *Heat transfer compositions, methods and systems* (Honeywell
  International, 2020), Example 5: https://patents.google.com/patent/US10815409B2/en
- Decoclim, aluminium cover size L, read 12 and 16 Oct 2026:
  https://www.decoclim.fr/en/decoclim/511-decoclim-alu-umbra-grey-ral-7022-size-l.html
- Sentimo, choosing a cover for a heat pump:
  https://www.sentimo.com/inspiration/blog/how-do-you-choose-the-right-cover-for-your-heat-pump/
- Kreg Tool, louvered screen for AC units and pool equipment:
  https://learn.kregtool.com/plans/louvered-screen-for-ac-units-pool-equipment/

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI and `wmake`, and
Python 3 with gmsh (the Python module), NumPy and PyVista.

    cd cases/heatPumpCover
    ./Allrun mesh                    # the shared mesh, about a minute on 8 ranks
    ./Allrun open                    # [nProcs], default 7
    ./Allrun covered
    python3 scripts/extract_results.py runs/open results/open
    python3 scripts/extract_results.py runs/covered results/covered
    python3 scripts/inlet_upwind.py runs > results/inlet_upwind.txt
    python3 scripts/coil_number.py > results/coil_number.txt

`Allrun mesh` writes the casing's and the cover's surfaces with `scripts/make_stl.py` and
meshes them in `runs/mesh/` (blockMesh, surfaceFeatureExtract, snappyHexMesh on 8 ranks, the
coil and fan zones by topoSet). `Allrun <run>` copies that mesh to `runs/<run>/`, takes the
cover's cells out for `covered`, adds the monitors' face zones, checks the mesh, decomposes it
and solves 0-60 s, writing the cut planes and monitors every 0.25 s and the fields every 5 s
(the last three kept). After the solve it samples the cells upstream of the coil at 50, 55
and 60 s. `./Allrun --setup-only <run>` stops before the solve. `scripts/make_open_faces.py`
rewrites the behind-the-unit face zones' dictionaries in `template/system/`. `./Allclean`
removes the mesh and the runs.

The runs took 27,072 s (`open`) and 14,457 s (`covered`) of wall time on 7 ranks each, side
by side; the open run's step is the shorter because the jet crosses the cover's snapped cells.
Each writes about 0.6 GB of cut planes.

The case was set up by an agent, then meshed, checked and run on our own machine after the
agent's tetrahedral mesh proved too slow; the 2-D versions before it were set aside because
in a vertical section the open unit could only draw air from above or below itself. The
files in `results/` are what `extract_results.py`, `inlet_upwind.py` and `coil_number.py`
wrote from the two solved runs.
