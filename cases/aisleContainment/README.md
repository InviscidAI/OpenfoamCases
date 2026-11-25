# A hall of AI server racks: hot aisles open, against closed off

Server halls are laid out in hot and cold aisles: the racks of a row face a cold aisle, draw their air from it and blow
their exhaust into the hot aisle behind them, back to back with the next row. Whether the hot aisle also needs closing
off is argued. The cooling guidance says it does: in a hall left open "hot exhaust air can still flow over the top of
servers, leading to higher server inlet temperatures at the upper portion of server racks" (ENERGY STAR), and of hot air
re-circulation, "It's bad. It causes hot spots" (Upsite Technologies, a containment vendor). Operators who leave it out
name cost, the hot aisle's working conditions and fire code: "if you don't have fire suppression heads in every aisle,
then the air barriers block sprinklers and/or fire suppression gas" (TechTarget). This case switches on the same hall of
120 air-cooled GPU racks twice from rest, once open and once with each hot aisle closed off by panels from the rack tops
to the ceiling and doors across its ends, and asks what air the servers draw over the first two minutes. It is about
where the exhaust goes, not about cost, sprinklers, working in a hot aisle or energy.

    ./Allrun open         # no containment, 0-120 s
    ./Allrun contained    # each hot aisle closed off to its ceiling return, 0-120 s

**The result.** **With the hot aisles open, the top servers draw air 5 K warmer, and the exhaust comes back over the
rack tops from the first second.** The servers' flow and heat come on at t = 0 with the air at rest at 20 °C (68 °F). In
the open hall the exhaust rises out of the hot aisles, spreads under the ceiling and falls into the cold aisles between
the row pairs, and 20.8 m³/s of it crosses back over the rack tops into the cold side, 15.4% of what the racks draw
(110-120 s). Over all 120 racks the top two servers of each rack draw **25.20 °C (77.4 °F) open against 19.99 °C (68.0
°F) contained** over 59-60 s, 5.21 K apart, and 25.59 against 19.99 °C over 110-120 s. At 30 s **167 of the 1,200
servers draw air above 27 °C (80.6 °F)**, the top of ASHRAE's recommended range, against none contained, and the hottest
open intake is 36.5 °C (97.8 °F); by 120 s it is 40.0 °C. In the contained hall every intake stays within 0.05 K of the
supply's 20 °C throughout, and within 0.02 K after the first second. Read [What it cannot](#what-it-cannot) before any
number here: **the 77 °F is a mean over all 120 racks, and the top servers of the four inner rows draw far more** (34.8
°C, 94.6 °F, in the racks the clip's section cuts); **the servers draw a fixed flow** whatever air reaches them; **the
cooling units supply exactly what the racks draw**, with nothing to spare, and the racks are sealed to the floor, both
by our brief; **the open hall has not settled by 120 s**; and there is one mesh of 0.2 m cells, first-order upwind, with
no mesh or time-step study.

The hall, its servers and its cooling are new. The buoyant model is the one the other room cases use, the servers are
fixed-flow pairs of standard boundary conditions with no code of their own, and the mesh is written directly as a
polyMesh, as in [`summerStoreCurtain`](../summerStoreCurtain); only the monitor is compiled.

## The hall

x runs across the rows, y along them and z up from the slab; metres. There is no raised floor.

| | value | from |
|---|---|---|
| hall | 15.6 m across the rows, 16.2 m along them and 3.2 m high, 1.0 m above the racks; sealed but for the supplies and the returns | ours |
| racks | 120 in six rows of 20, each 0.6 m wide, 1.2 m deep and 2.2 m tall (48U), the rows 12 m long (y 2.1-14.1 m); **solid from the floor to their tops**, with no gap under them, between them or at their ends | ours; the sealing is our brief (see [How the case got here](#how-the-case-got-here)) |
| aisles | 1.2 m. Across the hall: a cold aisle against the side wall, then three row pairs each of a row, a hot aisle and a row, back to back, the cold aisles between pairs shared, and a cold aisle against the far wall: cold x 0-1.2, row L00 1.2-2.4, hot 2.4-3.6, row R00 3.6-4.8, cold 4.8-6.0, and so on to 15.6 m | ours |
| servers | ten a rack, each 0.20 m tall (about 4.5U), from 0.1 to 2.1 m, **2 kW each (20 kW a rack, 2.4 MW in all)**; each a fixed **0.13267 kg/s** (2 kW at a 15 K rise; about 0.112 m³/s, 237 CFM, at the hall's density) drawn through its front face on the cold aisle and blown out of its back face at the same height **15 K warmer than the air it drew** | ours; 20 kW a rack is a density air cooling can still carry, and the newest GPU racks are liquid-cooled at several times that |
| cooling units | along both end walls, 0.9 m deep (y 0-0.9 and 15.3-16.2 m) and 1.95 m tall, the hall's whole width, each blowing **20 °C air along the rows** through a grille on its face from 0.1 to 1.9 m (28.08 m² each); a 1.2 m end gap between their faces and the row ends | ours: the operator's ruling of 24 Nov 2026 (end-wall units, no raised floor) |
| supply | **79.602 kg/s from each wall, 159.204 in all: exactly the racks' draw** (1,200 x 0.13267), about 2.39 m/s through the grilles | our brief, the operator's "just don't give it a surplus" |
| returns | the ceiling over each hot aisle, 1.2 m by the rows' 12 m (14.4 m² each), at a fixed 100,000 Pa; anything drawn back in through them enters at 35 °C | ours |
| containment | **contained only**: a panel of no thickness from each rack row's back top edge (z 2.2 m) to the ceiling along the whole row, and a door of no thickness across each end of each hot aisle (y 2.1 and 14.1 m) from the floor to the ceiling, so a hot aisle's air can leave only through its return | ours |
| walls | the floor, the ceiling, the walls, the racks' and the units' casings and the panels: no-slip and adiabatic | ours |
| start | the air at rest at 293.15 K (20 °C, 68 °F) in hydrostatic balance with 100,000 Pa at the ceiling; the servers' and the supplies' flows and the servers' heat on from the first step | ours |

The two halls have the same mesh, cell for cell, and the same boundary conditions; in contained, the panels and the
doors split the mesh's air into four parts that touch only through the servers: the cold side (90,696 cells), which the
supplies feed and the server intakes empty, and the three hot aisles (11,160 cells each), which the exhausts feed and
the returns empty. **The contained cold side has no fixed-pressure boundary.** Its inflow and outflow are equal fixed
mass flows, so its air mass stays what it was at rest, and that sets its pressure; a numerical mismatch between the two
would show as a drift of that mass, which the monitor reports at every row (and stops the run above 1%).

There are no people, no cables, no cable openings, no blanking panels to leave out and no gaps between racks. Each
server is a patch pair, not air inside the rack: the rack is a hole in the mesh, and what goes on inside it is not
solved.

## The model

`buoyantPimpleFoam` (OpenFOAM v2512), compressible air as a perfect gas (Cp 1005 J/kg K, molar mass 28.96546,
μ 1.825e-5 Pa s, Pr 0.71, sensible enthalpy), k-ω SST with `buoyancyTurbSource` (`constant/fvOptions`) and wall
functions (`kqRWallFunction`, `omegaWallFunction`, `nutkWallFunction`, `compressible::alphatWallFunction` with
Prt 0.85); k 0.02 m²/s² and ω 10 1/s on the supplies and the exhausts. Euler in time, adaptive steps at Courant 1
(maxDeltaT 0.05 s; 11.6 ms open and 12.4 ms contained at 120 s), **upwind for every convection term**, two outer and
two pressure correctors with the momentum predictor, p_rgh by GAMG to 1e-7. **No radiation, no heat into the walls.**

**The servers** are standard OpenFOAM conditions: each intake is `flowRateOutletVelocity` at 0.13267 kg/s, each exhaust
`flowRateInletVelocity` at the same 0.13267 kg/s with its temperature `outletMappedUniformInlet` from its own intake,
the intake's flux-weighted mean plus 15 K, at every step. So each server moves the same mass at every step and adds
1005 x 0.13267 x 15 = 2.0 kW to whatever air it draws, however hot. The supplies are `flowRateInletVelocity` at
79.602 kg/s and 20 °C; the returns `prghPressure` at 100,000 Pa with `pressureInletOutletVelocity` and `inletOutlet`
temperature. `scripts/make_case.py` writes the starting flux through every supply and server face into `0/phi`, so
the heat is on from the first step.

**The mesh** (`scripts/make_mesh.py`): a rectilinear grid written directly as a polyMesh, its cells inside the racks and
the cooling units left out. 0.2 m in x, 0.2 m in y (0.18 m inside the units), and in z 0.1 m from 0.1 to 2.1 m, the
servers' height, 0.1 m from 2.1 to 2.2 m and 0.2 m above the racks, with thinner layers at the floor (0.02, 0.02, 0.03
and 0.03 m) and in the top server (0.05, 0.05 and 0.1 m from 1.9 to 2.1 m): each server's face is 3 x 2 cells (3 x 3 for
s10). The floor layers and their 0.02 m cells were in the grid for a 4 cm gap under the racks in the solve this one
replaces, and are kept although the racks are now sealed, so as to change nothing else. The panels and the doors are
zero-thickness baffles on the grid's own faces at x 2.4 and 3.6 m (+4.8 m a pair), z > 2.2 m, and y 2.1 and 14.1 m.
**124,176 hexahedral cells** (145,634 points, 563.868 m³ of air) in both halls, 2,406 patches open and 2,418 contained;
`checkMesh` OK, non-orthogonality 0, skewness 9e-14, aspect ratio at most 10. One mesh, no mesh study.

**The monitor** (`src/hallMonitor`, a function object compiled into a library, run at every step, one row about every
0.125 s into `monitors/`): `ports.csv`, for every server port, supply and return, the mass flow each way, the
flux-weighted temperature, the enthalpy each way above 20 °C, the volume flow and the mean pressure; `regions.csv`, the
air's mass and internal energy (cv/R)∫p dV, the coldest and warmest cell and where, the largest Courant number and
where, the mean temperature and pressure of each cold aisle (and of its upper part, z 1.7-2.2 m), each hot aisle, the
end gaps, the space over the racks (z > 2.2 m) and the hall, and the contained cold side's air mass and its drift; and
`cuts.csv`, the gross flow each way, with its enthalpy, through the plane of each row's back face above the rack tops (y
2.1-14.1, z 2.2-3.2 m) and through each hot aisle's ends below and above 2.2 m. It prints a `HALL_MONITOR` line of the
servers' heat and mean rise at each row. With `./Allrun --planes` it also writes six planes on a 0.05 m grid, every
point the T and U of the cell holding it, interpolated in time to the plane's exact times (`scripts/convert_planes.py`
turns them into NPZ): a plan at 2.0 m and the sections across the rows at y 8.1 m (the rows' middle) and **y 6.8 m (the
clip's)** every 0.125 s, and a plan at 1.0 m, a section through the end racks (y 2.4 m) and one along a central cold
aisle (x 5.4 m) every 0.5 s.

## Results

`results/summary.txt` and `results/<run>/history.csv` (every 1 s), from `scripts/extract_results.py`. "The top
servers" are s09 and s10 of every rack, 240 servers, their intake temperatures averaged with each one's mass flow; over
a window, the ratio of the time integrals.

| air drawn by the servers | 1 s | 3 s | 5 s | 10 s | 15 s | 30 s | 60 s | 120 s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| top servers, open, °C | 20.03 | 21.78 | 22.94 | 24.47 | 25.03 | **25.14** | **25.22** | **25.58** |
| top servers, contained, °C | 20.00 | 20.00 | 20.00 | 20.00 | 19.99 | **19.99** | **19.99** | **19.99** |
| hottest intake, open, °C | 20.19 | 28.30 | 31.51 | 34.63 | 35.81 | 36.54 | 38.53 | 40.05 |
| hottest intake, contained, °C | 20.01 | 20.01 | 20.01 | 20.01 | 20.01 | 20.01 | 20.01 | 20.01 |
| servers above 27 °C, open (of 1,200) | 0 | 8 | 76 | 132 | 164 | **167** | 143 | 149 |
| servers above 27 °C, contained | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

| top servers' mean intake over | 14-15 s | 29-30 s | 59-60 s | 110-120 s |
|---|---:|---:|---:|---:|
| open | 25.00 °C (77.0 °F) | 25.14 °C (77.2 °F) | **25.20 °C (77.4 °F)** | 25.59 °C (78.1 °F) |
| contained | 19.99 °C (68.0 °F) | 19.99 °C (68.0 °F) | **19.99 °C (68.0 °F)** | 19.99 °C (68.0 °F) |
| difference | 5.01 K | 5.14 K | **5.21 K** | 5.59 K |

Over all 1,200 servers the mean intake is 22.23 °C (72.0 °F) open and 20.00 °C contained, at 29-30 s and at 110-120 s
alike. The hottest open intakes are the top servers of the four inner rows' middle racks (L01_r12_s10 at 30 s,
R01_r11_s10 at 120 s); in rack 08, the racks the clip's section cuts, the top servers of the four inner rows draw
34.80 °C (94.6 °F) over 29-30 s, those of the two outer rows, against the side walls, 21.22 °C (70.2 °F), and all six
30.27 °C (86.5 °F).

| air, °C | 1 s | 3 s | 10 s | 30 s | 60 s | 120 s |
|---|---:|---:|---:|---:|---:|---:|
| upper central cold aisle (x 4.8-6.0, z 1.7-2.2 m), open | 20.02 | 21.86 | 24.01 | 24.58 | 24.83 | 25.11 |
| upper central cold aisle, contained | 20.00 | 20.00 | 19.99 | 19.99 | 19.99 | 19.99 |
| upper outer cold aisle (x 0-1.2, z 1.7-2.2 m), open | 20.00 | 20.02 | 20.55 | 20.72 | 20.72 | 20.71 |
| central hot aisle (x 7.2-8.4, z < 2.2 m), open | 31.86 | 34.37 | 36.09 | 36.27 | 36.26 | 36.25 |
| central hot aisle, contained | 32.02 | 34.40 | 34.96 | 34.99 | 34.99 | 34.99 |
| over the racks (z > 2.2 m), open | 22.19 | 24.46 | 26.63 | 27.03 | 27.08 | 27.20 |
| over the racks, contained | 21.89 | 22.54 | 22.55 | 22.55 | 22.55 | 22.55 |
| the whole hall, open | 22.99 | 24.56 | 25.98 | 26.21 | 26.22 | 26.28 |
| the whole hall, contained | 22.87 | 23.56 | 23.66 | 23.67 | 23.67 | 23.67 |

**Where the exhaust goes.** The open hall's hot aisles fill with exhaust within a second, and it rises past the rack
tops, spreads under the ceiling and falls into the two central cold aisles; the two outer cold aisles, against the side
walls, take little (their upper air is 20.7 °C at the end). The flows over the rack tops and round the rows balance:
over 59-60 s, 14.5 m³/s of cold air is drawn into the open hot aisles round their ends and 6.2 m³/s over the rack tops,
and 20.8 m³/s of exhaust goes back over the tops into the cold side (15.45% of the racks' 134.9 m³/s; 15.51% at 29-30 s
and 15.45% at 110-120 s); 0.6 m³/s leaves the hot aisles round their ends. These are gross crossings of fixed planes,
not a tracer: air that crosses twice is counted twice. In contained nothing crosses. The hot aisles hold their exhaust
at 34.99 °C, 15 K over 20 °C. The zone over the racks (z > 2.2 m) includes the closed hot aisles' upper parts, 43 of its
253 m³, and its 22.55 °C is mostly their exhaust; outside the panels the air stays near 20 °C.

**Not a steady state.** The open hall keeps changing: the top servers' mean is 25.00 °C over 14-15 s, 25.14 over
29-30 s, 25.20 over 59-60 s and 25.59 over 110-120 s, and the hottest intake climbs from 36.5 to 40.0 °C between 30 and
120 s. By the study's test (every intake's and every zone's 5 s mean within 0.2 K of the next, from then to the end) the
open hall never settles by 120 s; the contained hall settles from 3.75 s.

**Checks.** The servers give 2.400000 MW over 20-30 s in both halls at a mean rise of 14.999997 K (open) and
15.000000 K (contained). The air's heat budget over 10-120 s, the servers' heat and the supplies' and returns' enthalpy
against the change of its internal energy (cv/R)∫p dV, closes to **+0.142% (open) and +0.192% (contained)** of the
servers' heat. Nothing comes back in through the ceiling returns after 1 s in either hall. The contained cold side's
air mass, 505.881007 kg at rest, drifts by at most +0.004547 kg (+0.00090%), at 67.1 s, and ends at 505.885515 kg; no
supply or leak correction was used. The coldest air after 1 s is 19.981 °C (open) and 19.975 °C (contained), 0.02 K
under the start; the largest Courant number after 1 s is 1.0008. Every step's final p_rgh residual is at most 1e-7,
with no bounding message and no fatal error in 10,351 (open) and 9,684 (contained) steps.

## What the clip shows, and what it does not

The clip shows the section across the rows at **y 6.8 m, 1.3 m off the rows' middle, through rack 08**, chosen by the
operator as where the exhaust falls into the open cold aisles: two strips of the whole hall's width, open above and
contained below, and a close view of each, **from switch-on to 30 s of the solve at 1.5 times speed** (20.04 s, then an
end card). It is coloured by air temperature from 68 to 95 °F (20-35 °C), with air parcels and the question "AI server
hall: close off the hot aisle?" and a clock of the solve's time. **Each panel's one number is the top servers' mean
intake over all 120 racks**, in whole °F: open 68 at 0:00, 71 at 0:03, 73 at 0:05, 76 at 0:09 and 77 from 0:12 to the
end (77.05 °F at 15 s and 77.25 °F at 30 s), and contained 68 throughout.

- **The number is milder than the picture.** The 77 °F is over all 120 racks. In the racks this section cuts, the top
  servers of the four inner rows draw 94.6 °F and those of the two outer rows 70.2 °F; the hottest intake is 97.8 °F. The
  section is where the spill is worst, not a typical one.
- **The colour scale stops at 95 °F.** At the section the open hall's air over the four inner rows is 100-103 °F on
  average at 30 s, up to 110 °F, and its hot aisles hotter; they read as the scale's top colour.
- **The parcels leave out the air moving through the section.** They are moved through the plane's in-plane velocity
  after the solve, while at 30 s the air also crosses the section at a mean 0.6 m/s open and 0.9 m/s contained, up to 2.9
  and 3.6 m/s, against in-plane means of 1.3 and 1.2 m/s. In the contained hall almost no parcel goes into the top
  servers of two rows for that reason: their air comes mainly along the row. They are not solved particles.
- **The parcels' path through the racks is drawn, not solved.** A parcel reaching a server's front leaves its back at
  the same height after the rack's transit time, about 1.3 s, coloured by the exhaust there; at the faces it moves at the
  port's solved speed (0.93 m/s in, 0.98 m/s out). The rack's inside is not in the mesh.
- The planes are the solve's cells sampled on a 0.05 m grid, piecewise constant, with the panels and doors drawn on.

## What it cannot

- **The servers draw a fixed flow.** Each moves 0.13267 kg/s and adds 15 K whatever it draws. Real server fans speed up
  as their intake warms, which draws more air, and more of it hot, in the open hall; and a server's rise falls as its
  flow grows. So the open hall's intakes, and how many servers would throttle, are not what a real hall's would be.
- **The printed 77 °F is a mean over all 120 racks**, while the top servers of the four inner rows draw about 95 °F in
  the racks the clip's section cuts (above). Neither is a measurement of any real hall.
- **The supply is exactly the racks' draw, and the racks are sealed.** Both are our brief, not a survey of halls. Real
  halls often supply more than they draw, and their racks leak under, between and round them. The solve this one
  replaced, with 15% more supply and a 4 cm gap under every rack, gave the open top servers 22.52 °C (72.5 °F) against
  19.99 °C (68.0 °F) over 59-60 s, with 10.3% of the racks' draw coming back over the tops and 7.2% under the racks.
  So the 5.2 K here is for a hall run at no margin; with the surplus and the gaps the open hall's lead was 2.52 K.
- **The cooling units are boundaries.** Supply along the end walls, the operator's choice, with no raised floor and no
  perforated tiles; a raised-floor hall, or units along the side walls, would mix differently. The returns are a fixed
  pressure over each hot aisle, without the ceiling plenum or the units' return paths; the end gap, the grilles' height
  and the returns' size are ours, the same in both halls.
- **Not a steady state.** The open hall is still warming at 120 s (25.59 °C over 110-120 s against 25.20 over 59-60 s);
  where it settles, and whether a thermostat would raise the supply, is not solved.
- **One mesh, first-order, RANS.** 124,176 cells of about 0.2 m across the hall, so a 1.2 m aisle is six cells wide and
  the plume off a rack top is a few; every convection term is upwind, which smears the exhaust's edge; k-ω SST with wall
  functions on no-slip walls, no y+ or inlet-turbulence study. There is no mesh or time-step study and no uncertainty bar
  on the 5.2 K.
- **Adiabatic, no radiation**: the walls, the slab and the racks' casings neither store nor pass heat. The panels and
  doors have no thickness and do not leak. There are no people, cables or cable openings.
- **Air-cooled.** Liquid-cooled racks, which the densest new GPU racks use, are not here, nor anything about cost,
  sprinklers, the heat of working in a closed hot aisle, or the hall's energy use.

## Sources

- ENERGY STAR, "Utilize Containment/Enclosures" (16 More Ways to Cut Energy Waste in the Data Center),
  https://www.energystar.gov/products/data_center_equipment/16-more-ways-cut-energy-waste-data-center/containmentenclosures,
  read on 15 and 24 Nov 2026: "hot exhaust air can still flow over the top of servers, leading to higher server inlet
  temperatures at the upper portion of server racks".
- Upsite Technologies, Ian Seaton, "Effects of Data Center Hot Air Re-Circulation", 25 Apr 2018
  (https://www.upsite.com/blog/effects-of-data-center-hot-air-re-circulation): "It's bad. It causes hot spots."
- TechTarget, Bob McFarlane, "Controversial hot aisle containment practices", 24 Jun 2014
  (https://www.techtarget.com/news/Controversial-hot-aisle-containment-practices/870709/): "if you don't have fire
  suppression heads in every aisle, then the air barriers block sprinklers and/or fire suppression gas"; the same article
  says isolating the aisles "significantly improves cooling and energy efficiency".
- ASHRAE's recommended server inlet range, 18-27 °C (64.4-80.6 °F), for the 27 °C count (as our brief gives it; not
  fetched for this case).
- The hall, the racks, the servers' 2 kW and 15 K, the supply and the returns are ours (above); no source gives the end
  gap or the grilles' height.

## How the case got here

**Earlier attempts.** The subject was chosen on 15 Nov 2026 and solved six ways before this one, each superseded: 2-D
sections across a raised-floor pod, a re-brief and a cooling-unit layout (15-16 Nov), which stopped at their checks, a
section having no row ends for the exhaust to come round; a two-row 3-D slice (16 Nov), whose render was sent back; a
whole hall on Inviscid's GPU solver, Felix, which never completed a step (16-23 Nov); and this hall on OpenFOAM with 15%
more supply than draw and a 4 cm gap under every rack (23 Nov), whose figures are in [What it cannot](#what-it-cannot).
On its section the exhaust was seen leaking under the racks into the cold aisles, and the operator's note of 24 Nov
("isn't that supposed to have blanking panels?", and "just don't give it a surplus") set this solve: the supply at
exactly the draw and the racks sealed to the floor in both halls, every other cell and setting as it was. None of the
earlier runs is in this folder.

**The solve.** The case was set up and solved by an agent on a cloud workspace of four cores (4 MPI ranks a run, the
two runs one after the other) and checked by us, on 24 Nov 2026. The mesh and the fields were built in a first session
that died during `checkMesh` with nothing solved, and rechecked in the second: one air region open and four contained,
every boundary's area, no cell under a rack. It then ran both halls from rest to 2 s as tests, from separate copies:
heat 2.39978 and 2.40000 MW, mean rise 14.999 and 15.000 K, no inflow through the returns, the contained cold side's
mass +0.0009% at 2 s; no test failed and nothing was changed. Production started again from rest. **Each run went 0-30,
30-60 and 60-120 s in three segments**, each restarting from the last one's binary write (`startFrom latestTime`), with
two checks on the way: at 30 s that nothing ran away (heat within 1%, the mean rise within 0.05 K, every zone's and
rack's 20-30 s slope under 0.2 K/s: at most 0.018 K/s; no intake's 1 s mean above 50 °C: at most 36.5 °C), and at 60 s
that the open top servers drew at least 2.0 K more than contained's over 59-60 s, else both would stop and the operator
decide: 5.21 K. The runs took 10,351 (open) and 9,684 (contained) steps and 4,171 and 4,066 s of solver time; the whole
solve, with the tests, the meshing and the export, took 2.51 h of the 10 h we allow a solve.

**The y 6.8 m re-run.** The clip's section was not among the planes the solve wrote, so both halls were run again from
rest to 30 s in one segment, on the same meshes and dictionaries, with that plane added to the monitor's exporter and
nothing else changed (`system/controlDict` named the new library). The re-runs took the same 2,599 and 2,433 steps at
the same times and Courant numbers, their top servers' intake, heat and rise are the solve's to every digit, and every
write of the planes both share (the plan, the section at y 8.1 m and the one along the cold aisle) is bit for bit the
solve's: the plane exporter does not touch the solve. 0.58 h, 3.14 h of the 10 h in all.

**A straight run with this case's `Allrun` is the same run**, but **it will not repeat the solved runs bit for bit** on
other hardware. The decomposition is simple (2 x 2 x 1), so it is the same on every machine, but floating point is not:
on our machine (below) the first 0.5 s from rest gives the solve's `HALL_MONITOR` lines to every printed digit and its
monitor rows to within 3e-9 of the region means (2e-5 in the smallest port fluxes), while the solver's residuals already
differ from about the eighth significant digit; in a turbulent buoyant flow that round-off grows. The zone means of a
rebuilt run should be expected to agree with these to a few hundredths of a kelvin, not to the last digit. No full
rebuilt run was solved.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI and `wmake`, and Python 3 with NumPy (and
pandas for `extract_results.py`).

    cd cases/aisleContainment
    ./Allrun open                 # [endTime [nProcs]]: 30, 60 or 120 (default), 4 ranks by default
    ./Allrun contained
    python3 scripts/extract_results.py runs results

The first `Allrun` compiles `src/hallMonitor` into `$FOAM_USER_LIBBIN`. Each run builds its own mesh in `runs/<run>/`:
`scripts/make_mesh.py` writes the polyMesh, `mesh.npz` and `mesh_report.json` (stopping if any air region lacks an
inflow or an outflow), `scripts/make_case.py` writes `0/`, `constant/` and `system/` from `template/` and
`config/case.json`, `checkMesh` must say Mesh OK, and `decomposePar` splits it. `Allrun` then solves 0-30, 30-60 and
60-120 s as the solved runs did, and once both runs reach 120 s writes `results/`. `./Allrun --setup-only <run>` stops
before the solve and `./Allclean` removes the runs. The solved runs took about 1.2 h (open) and 1.1 h (contained) of
solver time on 4 ranks each.

Each run writes the fields at 30, 60 and 120 s and monitor files of about 220 MB; `--planes` adds about 2.9 GB a run of
raw planes over 120 s. `results/` holds the summary and each run's history every 1 s; no fields, meshes, planes,
monitors or logs.

The files in `results/` are what `scripts/extract_results.py` wrote from the solved runs' monitors and logs.

Checked from a clean copy of this folder on 25 Nov 2026, with the monitor compiled into a scratch library folder against
OpenFOAM v2512: `make_mesh.py` writes both solved meshes' `boundary` files byte for byte (the solved runs' `points`,
`faces`, `owner` and `neighbour` were not exported, so those were checked through `checkMesh`, whose reports match the
solved meshes' line for line after the header: Mesh OK at 124,176 cells and 145,634 points in both, 563.868 m³).
`make_case.py` writes both runs' `0/T`, `k`, `omega`, `nut`, `alphat` and `phi`, `constant/` and `system/fvSchemes`,
`fvSolution` and `decomposeParDict` byte for byte, and the cold side's 505.88100728343534 kg the solved monitor was
given. `0/U`, `p` and `p_rgh` differ from the solved runs' in the last printed digit at the cells at two heights and the
faces beside them, by at most 2.4e-16 of the value: NumPy's `exp` on a different processor. `system/controlDict` differs
in the library's path (the solved runs named it by its full path on the workspace), in the planes being off unless asked
for, in its times, which `Allrun` sets for each segment, and in the solved runs having the `libs` and `functions`
entries twice, the same both times. The monitor here is the solve's with the y 6.8 m plane added; at 0.125 and 0.25 s
that plane matches the re-run's to 1.5e-8 K, and the plan and the section at y 8.1 m the solve's to the same. The short
tests from rest (0.5 s of both halls, above) are the only solving done with these files. `scripts/extract_results.py` on the solved runs'
monitors gives the study's own figures: the 25.1995 and 19.9941 °C over 59-60 s and their 5.2054 K, the 20.85 m³/s and
15.447% over the tops over 110-120 s, the 167 servers above 27 °C and the 36.53 °C hottest intake at 30 s, and the
+0.1416% and +0.1924% budgets.