# An oven just switched off: its door left open, against kept shut

The roast comes out, the oven goes off, and someone drops the door open to let the warmth into the kitchen. One
camp says that is free heat: leaving the door shut "wastes that warmth at a time when your home could use it" (House
Digest), and "instead of letting the oven cool down on its own with the door shut, keep the door open and let that
warmth fill your kitchen" (the Spokesman-Review's Dwell Well NW). The other camp says it makes no difference: "Door
open or door shut, the kitchen receives the same amount of heat in the end. Only the speed changes" (Selectra), and
manufacturers ask for the door to be kept shut while the oven cools. Both can be right. This case switches off the
same electric oven in the same kitchen twice on a winter evening, once with its door dropped open and once with it
shut, and asks how fast the oven's stored heat reaches the kitchen in the first five minutes, where in the kitchen it
goes, and how much is still in the oven at the end. It is about where the heat goes, not the bill, gas ovens or
safety.

    ./Allrun open    # the door down from switch-off, 0-300 s
    ./Allrun shut    # the door kept shut, 0-300 s

**The result.** **The open door gives the kitchen the oven's heat about twice as fast, and it goes up first.** The
oven holds 442.6 kJ above the kitchen's 20 °C at switch-off in the half kitchen solved (885 kJ for the whole oven,
0.25 kWh). Five minutes later the open oven has given the half kitchen **76.4 kJ against 35.6 kJ** with the door
shut (2.4 times as much at 2:30 and 2.1 times at 5:00), and **82.7% of its heat is still in the oven against 92.0%**.
The hot cavity air leaves through the top half of the open mouth, rises up the range's front past the cooktop and
spreads under the ceiling, and cooler air goes back in through the bottom half. At 300 s **the air at standing head
height (1.5-1.8 m) through the kitchen is 24.60 °C with the door open against 22.76 °C shut** (76.3 against
73.0 °F), 1.84 K warmer, and the ceiling layer 25.51 against 23.36 °C; the floor layer is 20.39 against 20.31 °C,
barely changed in either. Read [What it cannot](#what-it-cannot) before any number here: **the shut oven's heat is
prescribed, not solved** (its stored heat given out evenly over an assumed hour, so "the same heat in the end" is
built into the shut run); **the open liner probably gives its heat too slowly** on this mesh, and **its radiation out
of the open mouth is left out**, so the open door's lead is if anything understated; **the oven's 13 kg of steel is
ours, not sourced**, and the open oven's 82.7% rests on it; and **it is half a kitchen on a symmetry plane**.

The kitchen and the oven are new. The buoyant model, the castellated room mesh with the solids cut out on cell faces
and the monitor are [`doorwayFanStove`](../doorwayFanStove)'s, and the walls, the floor, the ceiling and the oven's
liner that store heat are [`radiatorCabinetTop`](../radiatorCabinetTop)'s `radLayerWall` with its radiation taken
out, as in [`closedRegister`](../closedRegister).

## The kitchen

x runs across the kitchen from the symmetry plane through the range's centre, y up from the floor and z out from the
range's wall; metres. Every edge lies on the 4 cm grid of the mesh's solids, so the sizes are rounded to it.

| | value | from |
|---|---|---|
| kitchen | 3.68 m wide, 3.04 m from the range's wall to the opposite wall and 2.40 m high, close to a US 8 ft ceiling; sealed, with no doorway, window or hood running | ours |
| half model | x = 0 to 1.84 m, a symmetry plane at x = 0 through the range's centre | ours |
| the range | a 30-inch freestanding electric range with a GE JB645's dimensions: 0.76 m wide (29-7/8 in), its cooktop 0.92 m up (35-3/4 to 36-1/2 in), 0.64 m deep (25-3/8 in without the handle), its backguard 0.08 m deep to 1.20 m up (47 in), against the wall at z = 0 | GE's quick specs, rounded to the grid |
| the oven's cavity | 0.60 m wide, 0.48 m high and 0.54 m deep, its floor 0.24 m up (x < 0.30, y 0.24-0.72, z 0.10-0.64 m in the half model) | retailer listings give 24-1/8 x 19-1/4 x 19-1/2 in (0.61 x 0.49 x 0.50 m); the mesh's cavity is 4 cm deeper, see below |
| the door | hinged at the bottom and lying flat at the height of the oven's floor, 0.60 m long and 4 cm thick (y 0.20-0.24, z 0.64-1.24 m), the range's full width; open from t = 0, with no swing | ours; GE gives 47-5/8 in deep with the door open, 0.57 m in front of the range |
| base cabinets | beside the range, 0.92 m high and 0.64 m deep, to the kitchen's side wall | ours (36 x 25 in) |
| wall cabinets | beside the hood, y 1.36-2.08 m, 0.32 m deep | ours |
| the hood | over the range, y 1.68-1.84 m, 0.48 m deep, off; a solid block | ours |
| walls and ceiling | 12.7 mm gypsum (k 0.1587 W/m K, ρc 723,991 J/m³ K), the floor 19 mm wood (k 0.106, ρc 1,237,411.2), each in 24 layers behind its surface with an adiabatic back, starting at 20 °C | `closedRegister`'s layers |
| start | the air at rest at 20 °C (68 °F) in hydrostatic balance with 1e5 Pa at y = 1.2 m; in open, the cavity's air at 162.78 °C | ours |

The cavity in the mesh is 0.54 m deep, 4 cm more than the listings' 19-1/2 in, because its back is on the 4 cm grid
at z = 0.10 m; its liner is 0.7272 m² in the half model (1.454 m² whole, against the hand estimate's 1.39 m²). The
cabinets, the hood, the door, the range's casing and, in open, the range's front and cooktop are adiabatic: they
neither store nor give heat. Everything is a solid block with no handles, knobs, grates or racks.

**There are no people.** The temperatures are volume means of the air outside the cavity over the half kitchen's
slices: the whole kitchen, the floor layer (y < 0.1 m), the seated zone (y 0.1-1.1 m), **standing head height
(y 1.5-1.8 m)** and the ceiling layer (y > 2.2 m). Two boxes on the centreline stand for heads: a cook in front of the
range (x < 0.3, y 1.5-1.8, z 1.0-1.4 m, past the end of the open door) and a head across the kitchen (the same x and
y, z 2.0-2.4 m).

## The oven at switch-off

The oven has been roasting a turkey at 325 °F (162.78 °C), the USDA's minimum roasting temperature for one. The heat
stored in it is mostly in its steel: **13 kg for the whole oven, an enamelled liner of about 1 mm and two racks,
which is ours and not sourced**, 6.5 kg in the half model. With the cavity's air that is **442.56 kJ above 20 °C in
the half model**, 436.19 kJ in the steel (6.5 kg x 470 J/kg K x 142.78 K) and 6.37 kJ in the cavity's air. As a
check, the whole oven's 0.25 kWh is about a third of the 0.66-0.78 kWh Selectra gives for one oven cycle.

- **open.** The cavity's air and its liner start at 162.78 °C. The liner is a wall with a 1-D steel layer behind it
  that holds the steel's heat (`storedLayerWall73`, two layers, 1.139 mm thick so that they weigh 6.5 kg on the
  liner's meshed 0.7272 m², k 50 W/m K, ρc 7850 x 470 J/m³ K, adiabatic behind). Nothing else is set: how fast the
  heat leaves is what the solve finds. By hand, with a film coefficient of 3-5 W/m² K against 20 °C, the liner would
  give off 0.6-1.0 kW for the whole oven at first.
- **shut.** The range is a solid block, its cavity not meshed. Selectra says the shut oven's walls "give off what is
  left over the next hour or so". So the shut range gives the kitchen its stored heat at E0/τ with τ = 1 h, about
  247 W for the whole range, held at its 150 s value of 237 W for the five minutes (4% off at either end): **118.5 W
  in the half model as one even heat flux, 210.70 W/m², through the range's front (0.3496 m²) and its cooktop
  (0.2128 m²)** (`externalWallHeatFluxTemperature` in flux mode). The face temperature follows from the air. A real
  range lets more of it out of the vent at the back of the cooktop, through a cooling fan above the door, and through
  its sides into the cabinets.

**The two runs are not treated alike, and the differences favour the shut door.** In the open run the radiation out
of the open mouth is left out: the cavity is nearly black at 163 °C and would send about 490 W (whole oven) through
the mouth at first, mostly into the floor and the cabinet fronts. The open door's hot inner glass is left out (the
door is an adiabatic block that starts at the kitchen's temperature), and so is the heat through the open range's
casing. In the
shut run the release rate is fixed, and it cannot fall as the oven cools.

## The model

`buoyantPimpleFoam` (OpenFOAM v2512), compressible air as a perfect gas (Cp 1005 J/kg K, molar mass 28.96,
μ 1.82e-5 Pa s, Pr 0.71, its enthalpy referred to 293.15 K), k-ω SST with `buoyancyTurbSource` and wall functions
(`kLowReWallFunction`, `omegaWallFunction`, `nutkWallFunction`, `alphatJayatillekeWallFunction`). Euler in time,
adaptive steps at Courant 1 (maxDeltaT 0.05 s; 23.2 ms open and 27.2 ms shut at 300 s), limitedLinearV for U and
limitedLinear for h, k and ω, two outer and two pressure correctors, p_rgh by GAMG to 1e-7 with the final solve capped
at 100 iterations. The pressure reference is the cell centre nearest (1.2, 1.7, 2.4) m, which lies on cell faces:
(1.16, 1.72, 2.36) m, at 99,993.939 Pa, the starting hydrostatic pressure there. **No radiation.**

**The walls that store heat** (`src/storedLayerWall73`): `radiatorCabinetTop`'s `radLayerWall` with the radiation set
to zero. Each face's surface balances the heat from the first air cell against an implicit 1-D layer behind it,
advanced from the step's starting state at every evaluation. Two additions, both used by the monitor: after every
step the layer's nodes are solved again against the surface temperature the step ended with, and the heat stored in
the layer above 20 °C is read off for the monitor.

**The meshes** (`template/mesh/system`, `scripts/make_mesh.py`, `scripts/kitchen_patches.py`): a background of 8 cm
cubes (blockMesh, 23 x 30 x 38), refined by snappyHexMesh, castellated only, without snapping or layers, the same in
both runs: 2 cm round the range and its mouth (x < 0.48, y 0.16-1.24, z 0.04-1.32 m, and x < 0.40, y < 1.24,
z < 0.68 m), 4 cm in the plume over and in front of the range (x < 0.64, z < 1.60 m, floor to ceiling), under the
ceiling (y > 2.16 m), along the counter (x > 0.32, y 0.80-1.04, z < 0.72 m) and on the solids, 8 cm elsewhere, two
cells between levels. The cabinets, the hood, the backguard and the range are one closed STL, the union of their
boxes, written by `make_mesh.py` on the mesh's own faces, so they are cut out exactly; only the range's boxes differ
between the runs. `kitchen_patches.py` sorts the boundary faces by face centre into `walls`, `ceiling`, `floor`,
`cabinets`, `rangeFront`, `cooktop` and, in open, `liner` and `door`, writes the mouth's face zones (the whole mouth
and its halves above and below 0.48 m), and checks the range's patches' and the mouth's areas to 1%. **127,610
hexahedral cells (open) and 119,030 (shut)**, air volumes of 12.039 and 11.970 m³; `checkMesh` OK, non-orthogonality
at most 25.2°, skewness at most 0.33. One mesh each, no mesh study.

**The monitors** (`scripts/monitor.C`, a coded function object run at every step, one row at the first step and every
0.625 s into `postProcessing/metrics/metrics.csv`): the gross flow each way through the mouth and its halves, in kg/s
and m³/s, and the enthalpy cp (T - 20 °C) it carries; the air's mass and its internal energy (cv/R)∫p dV; its coldest
and warmest cell and where they are; the mean temperature and speed of the zones above and of the cavity; the heat
into the air through every patch, both with the energy equation's own diffusivity (a do-nothing `scalarCodedSource` in
`constant/fvOptions` catches the wall flux before the turbulence model updates αt) and as `wallHeatFlux` gives it,
and their running integrals, summed at every step; and the heat stored in each layered patch. `courant.csv` keeps the
twelve cells of highest Courant number at each row. The `planes` are the section, which is the symmetry plane x = 0
through the range, and a plan at standing head height (1.60 m), each with T and U every 0.625 s from t = 0, 481 a run.

## Results

`results/summary.txt` and `results/<run>/history.csv` (every 2.5 s), from `scripts/extract_results.py`. All heats and
flows are for the half kitchen; double them for the whole.

| | 15 s | 60 s | 150 s | 300 s |
|---|---:|---:|---:|---:|
| oven's heat still in it, open, % | 97.86 | 95.27 | 90.33 | **82.75** |
| oven's heat still in it, shut, % | 99.60 | 98.39 | 95.98 | **91.97** |
| heat the kitchen has gained, open, kJ | 9.47 | 20.95 | 42.78 | **76.36** |
| heat the kitchen has gained, shut, kJ | 1.78 | 7.11 | 17.78 | **35.55** |
| the oven's heat into the air, open, W | 259.7 | 247.0 | 235.9 | 213.6 |
| the oven's heat into the air, shut, W | 118.5 | 118.5 | 118.5 | 118.5 |

| air, °C | 15 s | 60 s | 150 s | 300 s |
|---|---:|---:|---:|---:|
| standing head height (1.5-1.8 m), open | 20.48 | 22.47 | 23.69 | **24.60** |
| standing head height, shut | 20.20 | 20.65 | 21.83 | **22.76** |
| ceiling layer (y > 2.2 m), open | 23.15 | 23.62 | 24.50 | 25.51 |
| ceiling layer, shut | 20.46 | 21.55 | 22.40 | 23.36 |
| seated zone (0.1-1.1 m), open | 20.12 | 20.33 | 21.05 | 22.33 |
| seated zone, shut | 20.09 | 20.20 | 20.40 | 20.95 |
| floor layer (y < 0.1 m), open | 20.06 | 20.22 | 20.38 | 20.39 |
| floor layer, shut | 20.06 | 20.14 | 20.24 | 20.31 |
| the cook's head, open | 20.20 | 23.50 | 25.59 | 25.55 |
| the cook's head, shut | 20.05 | 20.61 | 21.64 | 22.60 |
| the whole kitchen, open | 20.77 | 21.50 | 22.59 | 23.65 |
| the whole kitchen, shut | 20.17 | 20.55 | 21.20 | 22.01 |

**Where the heat goes.** In the open oven the cavity's hot air is gone within seconds: the mouth carries 5.5 kW of heat
out at 0.625 s and 0.83 kW at 2.5 s, the cavity's mean air is down to 28.4 °C by then, and from 10 s on it stays at
28.7-29.5 °C while the steel cools from 162.8 to 139.7 °C at 300 s. From then on the oven's heat comes off the liner, 259.7 W at 15 s, 257.0 W on
average over 20-30 s and 213.6 W at 300 s, and leaves through the top half of the mouth: 10.5 L/s out at 15 s, 11.1 at
60 s and 9.3 at 300 s, with 2.0-2.7 L/s coming back through the top half and 6.7-7.7 L/s through the bottom half,
through which nothing leaves. That is 85-102% of the textbook flow through an opening (discharge coefficient 0.6) at
the cavity's mean temperature, which the solve was not tuned to. The plume rises up the range's front and past the
cooktop and spreads under the ceiling, and the warm layer works down: at 300 s the open kitchen is 5.1 K warmer under
the ceiling than at the floor, the shut one 3.1 K. The shut range's 118.5 W goes into a thin warm film up its front
and a plume off its cooktop to the hood; it is 73.66 W through the front and 44.84 W through the cooktop. Of the
76.36 kJ the open kitchen has gained at 300 s, the ceiling's layers hold 26.55 kJ, the walls' 12.90 kJ, the floor's
0.28 kJ and the air 36.63 kJ; of the shut kitchen's 35.55 kJ, 9.66, 5.18, 0.21 and 20.50 kJ.

**The liner's coefficient.** Over 20-30 s the liner gives 257.04 W with the steel at about 160.7 °C and the cavity's
air at 29.1 °C: **2.69 W/m² K** over its 0.7272 m² (2.5 against the kitchen's 20 °C, as the hand estimate counts it).
The hand estimate took 3-5 W/m² K, so the open oven gives its heat more slowly here than by hand: 514 W for the whole
oven over 20-30 s against 0.6-1.0 kW.

**The two sections.** On the symmetry plane, over the 6.58 m² of air the two runs share (the cavity left out), the
open section is on average 3.64 K (rms) off the shut one at 15 s, 3.81 K at 60 s, 3.63 K at 150 s and 3.64 K at 300 s,
and more than 1 K off over 26% of it at 15 s, 47% at 60 s, 60% at 150 s and 73% at 300 s. These are the study's own
comparison of the section planes, which `extract_results.py` does not repeat.

**Checks.** The shut range gives 118.5000 W at every row. The air's heat budget over 10-300 s, the change of its
internal energy against the heat through every surface, each summed at every step, closes to **+0.223% (open) and
+0.029% (shut)** of the oven's heat given over that time. In open, the steel's loss of heat and the liner's heat into
the air differ by 0.987 J at 300 s, of 70 kJ. The air's mass moves by 8.96e-7 of itself at the first step from the
t = 0 fields, and not after. The final pressure solve reached its 100-iteration cap at 24 steps of the shut run
(final residuals about 1.3-2e-7) and none of the open run's; no tolerance was relaxed. The liner's surface rises
above its start by at most 1.5e-5 K (435.930015 K); the air by up to 0.037 K, 435.966548 K at 1.25 s inside the
cavity at (0.07, 0.69, 0.43) m, with pressure work and the scheme's overshoot both possible causes, not separated.
The coldest air is 19.886 °C (open, at 6.875 s, in front of the wall cabinets at (1.54, 2.02, 0.38) m) and 19.685 °C (shut, at
71.25 s, just above the backguard at (0.07, 1.23, 0.11) m), 0.11 and 0.32 K below the start.

## What the clip shows, and what it does not

The clip shows the section, the symmetry plane through the range, with the whole kitchen from the range's wall to the
opposite wall and floor to ceiling in both panels on every frame, stacked, "door open" above and "door shut" below,
**from switch-off to 5:00 of the solve** at 15 times speed, one solved write a frame, 481 frames in 20.04 s. It is
coloured by air temperature on a 20-28 °C scale, with air parcels moving through the planes' velocity, a clock and the
question "Oven off: door open or shut?". Neither panel carries a number.

- **The range is drawn, flat in its side elevation**, as a cutaway stainless range on the solved outlines: the
  backguard with a knob, two grates over the burners, the cavity with two racks, the door with its window and handle,
  a drawer and a kick plate. In the open panel the door lies on the solved door and the cut shows the solved hot
  cavity air; in the shut panel the door is closed and the cavity is dark. The handles, the knob, the grates and the
  racks are not in the solve; they cover 0.43% (open) and 0.35% (shut) of the section's air.
- **The air at the oven is far hotter than the scale's 28 °C.** For the picture the temperatures are capped at 28 °C
  before a 2 cm blur, so the cavity, the plume's root and the shut range's faces read as the scale's top colour
  without a halo. The cap changes no number.
- The parcels are moved through the planes' velocity after the solve, half of each frame's 0.625 s of flow a frame so
  that the plume's parcels do not jump; they are not solved particles, and where the air is nearly still they are not
  drawn.
  Those two are the assumptions' as much as the solve's: the shut one is the assumed hour's, and the open one rests on
  the unsourced steel mass.

## What it cannot

- **The shut oven's heat is prescribed, not solved.** 118.5 W for the half range, the stored heat given out over an
  hour (Selectra's "the next hour or so"), held for the five minutes. So the shut share falls in a straight line by
  construction, to about 92% at five minutes whatever the oven's mass, and "the kitchen receives the same heat in the
  end" is assumed for the shut door rather than shown. A real shut oven gives its heat through a cooling fan, the
  vent at the back of the cooktop and its sides as well as its front, at a rate that falls as it cools. The shut
  panel's air may be warmer, if anything, than a real one's in the first five minutes, which is fair to the "no
  difference" camp.
- **The open liner probably gives its heat too slowly.** Its 2.69 W/m² K is below the 3-5 W/m² K of the hand
  estimate; the castellated cavity, stepped on 2 cm cells with wall functions, probably under-resolves the film on
  the liner. No finer cavity was tried.
- **No radiation, and the open mouth's radiation would matter.** The open cavity at 163 °C would radiate about 490 W
  (whole oven) through its mouth at first, by the hand estimate, mostly into the floor and the cabinet fronts, which
  here get none; the open door's hot glass and the open range's casing give nothing either. With the liner's
  coefficient, these make the real open oven lose its heat faster than the 82.7% here, and the open door's lead
  larger. None of it is quantified beyond the hand estimate.
- **The steel's 13 kg is ours, not sourced**, and the two runs do not depend on it alike. The shut share is fixed by
  the hour. The open share is not: a heavier oven gives off about the same watts at first, so with twice the steel the
  open oven would end near 91% and the gap in the share would nearly close (an estimate, not solved). The order holds
  either way: the open kitchen gains its heat sooner and is warmer at head height.
- **It is half a kitchen on a symmetry plane** through the range's centre. The plume cannot wander sideways, and the
  clip's section is that plane.
- **Five minutes, a sealed kitchen.** The hour in which the shut oven gives the rest of its heat is not solved, nor
  the evening after. There are no draughts, no doorway, and no hood running (Selectra: a running hood extracts part of
  the warm air, door open or shut), and no food or moisture.
- **An electric range only.** Gas ovens, and whether any of this is safe, are outside it; the case gives no safety
  advice, and the manufacturers who ask for the door to be kept shut also have the cabinets beside the range in mind.
- **RANS, one mesh each, one run each.** k-ω SST on stepped castellated meshes of 127,610 and 119,030 cells, 2-8 cm,
  with wall functions. SST's k needed bounding: 6,634 messages (open) over 13,896 steps and 2,858 (shut) over 10,966,
  to minima of -2.84e-5 and -9.58e-6 m²/s² before bounding. No mesh or time-step study, and no uncertainty bar on the
  1.8 K at head height.

## Sources

- GE Appliances, JB645EK/RK/FK 30" free-standing electric range, dimensions and installation information (quick
  specs): 29-7/8 in wide, 47 in to the top of the backguard, the cooktop at 35-3/4 to 36-1/2 in, 25-3/8 in deep
  without the handle, 47-5/8 in deep with the door open. The oven's cavity, 24-1/8 x 19-1/4 x 19-1/2 in, is from
  retailer listings of the range.
- USDA Food Safety and Inspection Service: 325 °F, the minimum oven temperature for roasting a turkey (read from a
  search summary; the site refused a scripted fetch).
- Selectra, "Leaving the oven door open after cooking: false economy or genuinely free heating?", 14 Oct 2026, updated
  14 Nov 2026 (https://selectra.co.uk/energy/news/oven-door-open-after-cooking-free-heat): "Door open or door shut,
  the kitchen receives the same amount of heat in the end. Only the speed changes"; with the door shut "a cooling fan
  usually kicks in, pushes warm air out above the door, and the walls then give off what is left over the next hour
  or so"; a Bosch manual quoted as "let the oven cool with the door closed"; 0.66-0.78 kWh for one oven cycle.
- House Digest, "Stay Warm This Winter For No Extra Cost With The Help Of A Kitchen Essential", 11 Nov 2025
  (https://www.housedigest.com/2019744/stay-warm-no-extra-cost-kitchen-essential-oven-door-open-after-cooking):
  "leaving the door closed while it cools down wastes that warmth at a time when your home could use it".
- The Spokesman-Review, Dwell Well NW, "Tip: let your oven heat your house", 12 Feb 2009
  (https://spokesman.com/blogs/dwellwellnw/2009/feb/12/tip-let-your-oven-heat-your-house).
- Vienna.at, "Oven Door Open After Baking? That Can Be Expensive", 21 Oct 2026
  (https://www.vienna.at/oven-door-open-after-baking-that-can-be-expensive/10567892): "Some manufacturers recommend
  keeping the door closed during cooling."
- The walls that store heat: [`radiatorCabinetTop`](../radiatorCabinetTop)'s `src/radLayerWall`, and the layers'
  materials as in [`closedRegister`](../closedRegister). The buoyant model, the castellated mesh and the monitor:
  [`doorwayFanStove`](../doorwayFanStove).

## How the case got here

**The solve.** The case was set up and solved by an agent on our own machine on 14 Nov 2026 and checked by us. Before
production the agent ran 50-step tests of both runs from rest until they passed its checks: that the steel's loss of
heat matches the liner's heat into the air to 1%, that the shut range gives its 118.5 W to 0.5%, and that the passive
walls take heat from the air. Two of the fixes changed what the runs compute, both before any production step: the
layers' nodes are solved again against the surface temperature each step ends with (above), and the monitor reads the
wall heat flux with the diffusivity the energy equation used, through the do-nothing source in `constant/fvOptions`,
since `wallHeatFlux` reads it after the turbulence model has updated αt (that alone left a 1.22% mismatch at start-up;
with both, 0.51%). The others were the monitor's code (a `Foam::floor` for `std::floor`, the library's path at run
time, the observer's empty hooks and its loop over processor patches) and a temperature guard in the tests that
stopped them on the air's 0.007 K excursion in the cavity, which is reported instead. No physics, mesh, scheme, step
or corrector setting was changed by any of them.

Both runs were launched together at 11:13 UTC from rest, 8 ranks each, one physical core a rank. **Each run went
straight through from rest to 300 s in one segment, with no restart**: one `Starting time loop`, and the log ends in
`End`. The runs took 13,896 (open) and 10,966 (shut) steps, 3,358 s and 2,399 s of wall time on 8 ranks each, 1.83 h
for everything with the meshing and the tests, within the 10 h we allow a solve. The agent checked at 30 s that both
would finish inside the 10 h and that the open liner gave between 100 and 2,000 W, and at 60 s that the two sections
differed by at least 1 K rms; all passed. The solved runs carried an abort function object, read at each write, which
was never used; it is left out here.

**A straight run with this case's `Allrun` is the same run**, but **it will not repeat the solved runs bit for bit**,
because scotch gives a different 8-rank decomposition on each call on our machine (15,792 cells on rank 0 of the open
run in a rebuild against the solved run's 15,803, and 15,022 against 14,951 shut), so parallel sums round differently,
and in a turbulent buoyant flow that round-off grows. The zone means of a rebuilt run should be expected to agree with
these to a few hundredths of a kelvin, not to the last digit. No rebuilt run was solved.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI and `wmake`, and Python 3 with NumPy.

    cd cases/ovenDoorOpen
    ./Allrun open                # [nProcs], default 8; compiles the wall condition and builds the open mesh first
    ./Allrun shut                # default 8; builds the shut mesh first
    python3 scripts/extract_results.py runs results

The first `Allrun` compiles `src/storedLayerWall73` into `$FOAM_USER_LIBBIN`. Each run builds its own mesh in
`runs/mesh-<run>/`: `scripts/make_mesh.py` writes the meshing dictionaries (`template/mesh/system/`) and the solids'
STL, then blockMesh, a serial snappyHexMesh of under a minute, `scripts/kitchen_patches.py` (the patches, the mouth's
face zones, and the cell centres for the starting fields) and checkMesh. Then `scripts/make_case.py` writes
`runs/<run>/`: the mesh, `0/`, `constant/` and `system/` from `template/` and `config/case.json`, and the monitor from
`scripts/monitor.C`, which the solver compiles against `src/storedLayerWall73` when it starts. `Allrun` writes the
t = 0 planes, decomposes by scotch, solves from 0 to 300 s, and once both runs have solved writes `results/`. The two
runs differ in their meshes and in `0/`. `./Allrun --setup-only <run> [nProcs]` stops before the solve; `./Allclean`
removes the runs. The solved runs took about 0.9 h (open) and 0.7 h (shut) on 8 ranks each.

Each run writes 481 times of 2 planes (VTK, about 0.46 MB a write; the solved runs gzipped each finished plane with a
wrapper of the agent's, which is not here), the fields every 30 s and monitor files of about 1 MB. `results/` holds
the summary and each run's history every 2.5 s; no fields, meshes, planes or logs.

The files in `results/` are what `scripts/extract_results.py` wrote from the solved runs' monitors and logs.

Checked from a clean copy of this folder on 22 Nov 2026, with the wall condition compiled into a scratch library
folder: `make_mesh.py`, blockMesh, snappyHexMesh and `kitchen_patches.py` rebuild both solved meshes byte for byte
(the STL, and `points`, `faces`, `owner`, `neighbour`, `boundary`, `faceZones`, `cellZones`, `pointZones` and
snappyHexMesh's level and index files), and `checkMesh` gives the solved meshes' reports line for line: Mesh OK at
127,610 and 119,030 cells, non-orthogonality 25.2394° at most, skewness 0.333333. `make_case.py` writes both runs'
`0/`, `constant/` and `system/` byte for byte, but for the library's path in `controlDict` and `planesT0` and in the
monitor's compile options and include (the solved runs named the built library and its header by their full paths),
and the unused abort function object; the t = 0 planes are the solved runs' byte for byte once theirs are unzipped.
The monitor compiles and links against the built library. The decomposition is not the solved runs' (above). No
solve was run from the clean copy. `scripts/extract_results.py` on the solved runs' monitors gives the study's own
figures: the 442.56 kJ, the 76.36 and 35.55 kJ and the 82.75% and 91.97% at 300 s, the 24.60 and 22.76 °C at head
height, the 257.04 W over 20-30 s, and the +0.223% and +0.029% budgets.
