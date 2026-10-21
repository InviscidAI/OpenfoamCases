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

Viewers of the clip asked whether the cover can be fixed: would the slats be better pointing
up, and, against the rain that would let in, could the cover be moved further out with its
bottom left open? Three more runs answer that with nothing changed but the cover, each from
the fan's switch-on ([Fixing the cover](#fixing-the-cover-slats-up-or-the-front-moved-out)):

    ./Allrun slatsDown   # the cover above, rebuilt and run again to 90 s, as the control
    ./Allrun slatsUp     # the same boards turned to rise 35 degrees outward, to 90 s
    ./Allrun movedOut    # the front moved out to 350 mm from the grille, the bottom open, to 60 s

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

## Fixing the cover: slats up, or the front moved out

Viewers of the clip offered two fixes. One asked whether the slats would be better pointing
up. Another answered that boards sloping up would let rain into the unit, and the first then
suggested moving the cover further from the unit and leaving its bottom open for drainage.
Does either of them take the coil's air back towards the open unit's 0.0 °C?

Everything but the cover is the model above, unchanged: the unit, the fan's target of
1.82113 m/s, the coil's -6 °C surface, effectiveness and NTU/L of 15.482 1/m, the mesh
dictionaries and refinement levels, the schemes and solver settings, still air at 2 °C, from
rest. `constant/`, `0.orig/`, `fvSchemes` and `fvSolution` are the files `covered` ran with; no
setting was adjusted after these runs started.

### The three covers

- **`slatsDown`** is `covered`'s cover, rebuilt. A snappyHexMesh rebuild is not the same mesh to
  the cell (above), so the cover the fixes are measured against was meshed and solved again
  beside them.
- **`slatsUp`** has the same lid, corner post and boards, each board mirrored across its own
  panel: it fills the same span (x 0.6927-0.775 m for the front) at the same heights, but rises
  35° outward instead of falling. The two covers' volumes agree (0.037610 m³). Nothing else moves;
  this is the one-change test.
- **`movedOut`** keeps the downward boards, with two changes, because the viewer offered them as
  one fix. *Further out:* Daikin's installer guide asks for more than 350 mm in front of the
  outlet (p. 56), so the front panel's inner edge moves from 0.700 m to 0.988 m from the wall
  (0.638 + 0.350), and the lid and the side panel run out to the new front at 1.063 m. The side
  stays 0.108 m from the unit's end. That is 0.99 m of inside depth, more than any cover found for
  sale (Decoclim's L is 55-70 cm), so it is a cover built to measure. *Bottom open:* the boards
  whose lower edge would fall below 0.29 m are left off, which leaves 10 boards in each panel
  instead of 13, the lowest edge at 0.294 m, about the unit's base (0.300 m, the free space Daikin
  asks for under the unit). The corner post still reaches down to the feet. The level-3
  refinement box runs out to x = 1.14 m instead of 0.85 m, keeping its 0.075 m margin past the
  front, and the cover's front and side cut planes move with the cover; its low strip is the open
  band below 0.29 m.

Each cover has its own mesh, built as above, with its cells taken out as in `covered`:

| | cells with the cover | cells in the run | cover's cells | `checkMesh` of the run |
|---|---:|---:|---:|---|
| `slatsDown` | 447,753 | 409,200 | 38,553 | fails skewness only: 16 faces of `coverWalls`, at most 5.56 |
| `slatsUp` | 447,396 | 408,643 | 38,753 | fails skewness only: 13 faces, at most 4.29 |
| `movedOut` | 490,894 | 448,758 | 42,136 | fails skewness only: 2 faces, at most 4.21 |

The coil zone is 14,720 cells and the fan zone 6,896 in all three. `covered` failed the same
check on 19 faces and ran without trouble; so did these.

One monitor is added to the three runs, `inletUpwindSeries`
(`template/system/inletUpwindSeries.inc`): the cells one cell upstream of the coil's inlet face,
the plane `inlet_upwind.py` reads, at every 0.25 s write instead of only after the solve. It is
the direct check on the correction `F` in each new cover, and `extract_results.py` adds it to
`summary.csv` as `upstream_K_below_outside_air`.

`slatsUp`'s number was still rising at 60 s, so `slatsUp` and `slatsDown` were continued from
their 60 s fields to 90 s (`startFrom latestTime`, `endTime 90`, nothing else changed). Neither
steps at 60 s: slats up's corrected number reads 0.2848, 0.2855 and 0.2857 K at 59.75, 60 and
60.25 s, and the fan's flow 0.3482-0.3488 m³/s either side. `Allrun` runs the two straight to 90
s; the solved runs' restart is the only difference. `movedOut` was not continued.

### Results

The number is the one above: the coilInT monitor corrected with the same F = 0.0302, in K below
the outside air, from `results/coil_number_covers.csv` (`scripts/coil_number.py`) and
`results/<run>/summary.csv`:

| air entering the coil, K below the outside air | 50-60 s | 80-90 s |
|---|---:|---:|
| `covered` (above) | 0.717 | not run |
| **`slatsDown`**, the same cover rebuilt | **0.729** | **0.739** |
| **`slatsUp`** | **0.247** | **0.242** |
| **`movedOut`** | **0.551** | not run |

- **The rebuilt cover agrees with the first.** `slatsDown` reads 0.729 K over 50-60 s against
  `covered`'s 0.717 K on the other mesh, and 0.739 K over 80-90 s, so the comparison with the
  first clip stands. From 20 s on its number stays between 0.705 and 0.757 K.
- **The upstream cells agree with the corrected monitor** to within 0.012 K in every 10 s window
  of all three runs (50-60 s: 0.727, 0.235 and 0.547 K; 80-90 s: 0.736 and 0.233 K), so the F
  found on the first runs holds for the new covers. At the six times `inlet_upwind.py` reads
  (`results/inlet_upwind_covers.txt`) F is 0.0305-0.0318.
- **Turning the slats up is the better fix: about 0.5 K better than the cover as it was.** The
  jet leaves upward and out under the lid's edge rather than down onto the ground. Almost none of
  it comes back in under the lowest board (0.002 m³/s, against 0.018 m³/s at -1.2 °C with the
  slats down), and the air arriving under the unit is 1.57 °C against 0.79 °C (cut planes,
  50-60 s). The coil takes 3.08 K off its air against the cover's 2.88 K.
- **Moving the front out with the bottom open helps less: 0.55 K.** The jet crosses 350 mm of air
  before the boards, and cold air spills out along the ground through the open bottom; some
  comes back in through that open band (0.038 m³/s at 0.4 °C over 50-60 s). The run joins two
  changes, so it cannot say how much each gives alone, and only one distance was tried.

| over 50-60 s | `slatsDown` | `slatsUp` | `movedOut` |
|---|---:|---:|---:|
| fan flow, m³/s | 0.3487 | 0.3483 | 0.3488 |
| coil's drop per pass (design), K | 2.876 (2.909) | 3.081 (3.102) | 2.950 (2.980) |
| air entering the space behind the unit from above / below / its open end, m³/s | 0.040 / 0.122 / 0.181 | 0.052 / 0.100 / 0.217 | 0.032 / 0.126 / 0.189 |
| coldest air anywhere, whole run | -3.41 °C | -2.79 °C | -3.23 °C |

### Slats up does not settle on one number

From 20 s on, `slatsDown` stays within 0.705-0.757 K and `movedOut` within 0.522-0.589 K.
`slatsUp` does not settle. Over 20-90 s its number drifts between 0.17 and 0.30 K, with a mean
of 0.23 K: 0.17-0.19 K over 20-45 s, rising from about 47 s to a plateau of 0.29-0.30 K over
62-78 s, then falling to 0.21 K by 90 s (1 s means). Shown as a 2 s mean to 0.1 K it reads 0.2
until 56 s, 0.3 from 56 s to 85 s, and 0.2 again from 85.25 s to 90 s. The flow into the space
behind the unit is steady through the whole run (about 0.05 m³/s from above, 0.10 from below and
0.22 round its end). What changes is how cold the air coming round the unit's end is: 0.03 K
below the outside air over 25-45 s, 0.20 K over 60-65 s, and back to 0.04 K at 90 s (cut plane
`unitEnd`). A pocket of colder air reaches the unit's end, is drawn into the coil and drains
away again. Where it comes from was not traced, and whether it comes back in a longer run was
not tested. At its highest, slats up is still 0.4 K better than the cover with its slats down.

### What the second clip shows

The symmetry plane over the same window and on the same scale as the first clip, in two panels:
the cover with its slats down (`slatsDown`) and with its slats up (`slatsUp`), from switch-on to
8 s of flow at 0.4× speed, about 20 s, marked "0.4x speed" on screen, so that the jets can be
seen forming and turning down or up. The runs wrote the plane every 0.25 s, 15 video frames at
this speed; the frames between are blended along the flow, so the cold air moves between writes
rather than fading from one place to the next, and the parcels move with the flow at the same
0.4×. Each panel's number is the corrected value as a 2 s running mean to 0.1 K
(`results/coil_number_covers.csv`, `shown`), so it climbs as the cold air reaches the coil: slats
down reads 0.7 from 5.25 s and slats up 0.2 from 4.25 s, and at 8 s, the clip's last frame, they
read **0.7 °C** and **0.2 °C**. It does not show the drift above, which comes after 45 s, or the
moved cover, whose number is in the table.

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

The three covers' runs carry all of these, and:

- **Rain and snow.** Boards sloping up outward catch rain on their top faces and drain it
  inward, towards the unit, and a drop driven in at about the boards' slope, 35° below the
  horizontal, goes straight through a gap. Downward boards shed rain outward, and a drop has to
  travel upward to get past them. This was the objection to slats up under the first clip, and
  the model has no rain in it. In the moved cover, the open bottom lets drifting snow in under
  the boards as well as letting meltwater out.
- **One fix, two changes; one gap.** The moved cover and its open bottom are one run, and the
  front was moved only to Daikin's 350 mm.
- **Slats up's number does not settle.** It drifts between 0.17 and 0.30 K over 20-90 s as colder
  air comes and goes round the unit's end, so its figure is a range, not a settled value; a
  longer run was not tried.
- **Two runs, restarted.** `slatsDown` and `slatsUp` were solved to 60 s and continued from their
  60 s fields; `movedOut` ends at 60 s.

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

and for the three covers:

    ./Allrun mesh up                 # runs/mesh-up/; slatsDown uses runs/mesh/
    ./Allrun mesh out                # runs/mesh-out/
    ./Allrun slatsDown               # [nProcs], default 7
    ./Allrun slatsUp
    ./Allrun movedOut
    for r in slatsDown slatsUp movedOut; do python3 scripts/extract_results.py runs/$r results/$r; done
    python3 scripts/inlet_upwind.py runs slatsDown slatsUp movedOut > results/inlet_upwind_covers.txt
    python3 scripts/coil_number.py results -o coil_number_covers.csv slatsDown slatsUp movedOut \
        > results/coil_number_covers.txt

`Allrun mesh` writes the casing's and the cover's surfaces with `scripts/make_stl.py` and
meshes them in `runs/mesh/` (blockMesh, surfaceFeatureExtract, snappyHexMesh on 8 ranks, the
coil and fan zones by topoSet). `Allrun <run>` copies that mesh to `runs/<run>/`, takes the
cover's cells out for `covered`, adds the monitors' face zones, checks the mesh, decomposes it
and solves 0-60 s, writing the cut planes and monitors every 0.25 s and the fields every 5 s
(the last three kept). After the solve it samples the cells upstream of the coil at 50, 55
and 60 s. `slatsDown` and `slatsUp` run to 90 s and are sampled at 80, 85 and 90 s instead;
`slatsUp` and `movedOut` build their own meshes first if they are not there, with
`make_stl.py`'s second argument (`up`, `out`). `./Allrun --setup-only <run>` stops before the
solve. `scripts/make_open_faces.py`
rewrites the behind-the-unit face zones' dictionaries in `template/system/`. `./Allclean`
removes the mesh and the runs.

The runs took 27,072 s (`open`) and 14,457 s (`covered`) of wall time on 7 ranks each, side
by side; the open run's step is the shorter because the jet crosses the cover's snapped cells.
Each writes about 0.6 GB of cut planes. The covers' runs took 13,014 s to 60 s and 6,442 s more
to 90 s (`slatsDown`, 8 ranks), 30,916 s and 14,743 s (`slatsUp`, 4 ranks) and 29,547 s
(`movedOut`, 4 ranks), sharing the machine with other runs.

**A rebuild is not the solved mesh to the cell**, for the covers as for the first two runs. From a
clean copy, `./Allrun --setup-only` wrote byte for byte the solved runs' surfaces (`cover.stl`,
`casing.stl`), mesh dictionaries, `constant/` apart from the mesh, and initial fields in `0/`;
`fvSchemes`, `fvSolution` and `decomposeParDict` were identical, and `controlDict` with its
function objects expanded differed only in the restarted runs' `startFrom latestTime`. The
meshes came out at 447,676 / 409,123 cells (`slatsDown`), 447,319 / 408,566 (`slatsUp`) and
491,181 / 449,045 (`movedOut`), within 0.06% of the solved counts, with the same cover cells
(38,553, 38,753 and 42,136) and coil zone (14,720) in each, the fan zone 6,882-6,896 cells, and
`checkMesh` failing only skewness on 28, 17 and 1 faces. The points, faces and decompositions
differ. On one mesh, `--setup-only open` and `covered` write every file outside the
`processor*` folders exactly as they did before the three covers were added (decomposePar
splits the mesh differently from one call to the next, even on the same mesh).

The case was set up by an agent, then meshed, checked and run on our own machine after the
agent's tetrahedral mesh proved too slow; the 2-D versions before it were set aside because
in a vertical section the open unit could only draw air from above or below itself. The
files in `results/` are what `extract_results.py`, `inlet_upwind.py` and `coil_number.py`
wrote from the solved runs. `extract_results.py` joins a restarted run's monitor files, so
`results/slatsDown/` and `results/slatsUp/` hold one series from 0.25 s to 90 s.
