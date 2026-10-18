# A lorry passing a cyclist at 1.5 m and at 30 cm, in 2-D

A lorry overtaking a cyclist pushes him away as its cab goes by and pulls him towards it at
its rear doors. `cyclistBehindLorry`'s overtaking run estimated that at a 1.5 m gap, with the
rider read off the solve rather than put in it. This case asks what happens when the gap
closes to 30 cm, where the air squeezed between him and the trailer depends on him being
there, so he has to be in the flow. It sets the 30 cm pass beside the 1.5 m pass, the same
lorry, speeds and model, and reports how many times harder the close pass pushes and pulls.
The numbers it reports are **ratios**, not newtons.

One mesh, a precursor and two runs from it:

    ./Allrun precursor   # the lorry alone, from rest to 3.4 s
    ./Allrun gap150      # the rider added at 3.4 s, 1.5 m from the lorry's side, to 8.0 s
    ./Allrun gap030      # the same rider 30 cm from it, to 6.4 s

**It is a 2-D slice.** The solve is one horizontal section through the lorry and the rider
at z = 1.3 m, his shoulder height, with no height to it. Air cannot go over the roof or
under the trailer, so it is squeezed harder round the lorry's sides than real air is, and
the wake behind the doors comes out much stronger and more regular than a real lorry's.
Read [What it cannot](#what-it-cannot) before any number here.

**On safety.** The UK Highway Code (Rule 163) asks drivers to leave at least 1.5 m when
passing a cyclist at up to 30 mph and more at higher speeds. Nothing here says that either
gap is safe.

## The pass

The lorry, the rider and the speeds are those of `cyclistBehindLorry`'s overtaking run
([`../cyclistBehindLorry`](../cyclistBehindLorry#overtaken)):

- **The lorry** is that case's generic box lorry (`scripts/build_truck.py` there), cut at
  z = 1.3 m: a 13.6 m trailer and a 2.3 m cab, 2.55 m wide, its doors at x = 0 and its
  cab's front at x = 16.5 m. It does 80 km/h (22.2 m/s).
- **The rider** is that case's MakeHuman rider on his road bike (`scripts/build_rider.py`
  there), cut at the same height, 4 cm above his shoulder centre: a section 0.47 m long and
  0.42 m wide, 0.0988 m2. He rides at 20 km/h, so in the lorry's frame he moves back along
  its side at 60 km/h (16.667 m/s).
- **The gaps** are from the lorry's side (y = -1.275 m) to his section's inner edge: his
  shoulder centre is at y = -2.985 m for 1.5 m (`gap150`, 1.501 m) and y = -1.785 m for
  30 cm (`gap030`, 0.301 m). The lorry has no mirrors.
- **His path.** He appears at t = 3.4 s with his shoulder centre at x = 41.5 m, 25 m ahead
  of the cab's front, and moves at x = 41.5 - 16.667 (t - 3.4). The cab's front reaches him
  at 4.90 s and the doors at 5.89 s; at 6.4 s he is 8.5 m behind the doors, at 8.0 s 35 m.

`scripts/sections.py` cuts the two sections from `cyclistBehindLorry`'s STLs and resamples
them by arc length, the lorry at 1 cm and the rider at 4 mm, keeping every corner sharper
than 30 degrees, within 0.6 mm of the raw cut and with the same areas
(`geometry/sections.json`). A raw cut leaves vertices 0.04 mm apart, which the mesher would
turn into slivers that hold the time step at 2e-5 s.

## The model

- **Domain.** The lorry's frame: x = -70 to 62 m (the inlet 45.5 m ahead of the cab, the
  outlet 70 m behind the doors), y = -35 to 35 m with slip sides, one cell from z = 0.8 to
  1.8 m with empty faces. The air comes in at 22.2 m/s with 1% turbulence intensity and a
  0.5 m length scale, nu = 1.5e-5 m2/s, rho = 1.225 kg/m3. There is no road: it is a
  horizontal slice.
- **Mesh.** `scripts/make_mesh.py`, gmsh, quads where they fit and triangles elsewhere,
  extruded one cell: 2 cm in a corridor x = -38 to 43 m, y = -3.6 to -1.275 m, through
  which both riders pass, 1 cm in a band 0.28 m wide along the lorry's passing side, 1 cm
  on the lorry, growing to 1 m far away: **787,842 cells**. `checkMesh -allGeometry
  -allTopology` passes (maximum skewness 0.88, minimum determinant 0.061). Under the rider
  the cells are 9-26 mm across (the square root of their area), median about 18 mm; a
  vertical line through his shoulders at 30 cm crosses 44-46 cells between him and the
  trailer. The lorry's y+ on the passing side is 19-446, mean 136: wall functions, not a
  resolved boundary layer.
- **Turbulence and time.** `pimpleFoam`, incompressible URANS with k-omega SST and wall
  functions, backward in time, bounded linearUpwindV for momentum, Courant number 0.8; the
  step settles near 5.1e-5 s.
- **The precursor.** The lorry alone from an impulsive start (uniform 22.2 m/s) to 3.4 s,
  by when the start-up has been carried about 75 m downstream. Both runs start from its
  last write, 3.399976553327491 s, copied whole with its old-time fields, on the same mesh.
- **The rider as a drag term.** He is not a meshed body. In the cells his outline covers at
  time t, the momentum equation gains a drag S = -K m (U - U_r), with K = 1e6 1/s and
  U_r = (-16.667, 0, 0) m/s, which holds the air there at his velocity
  (`constant/fvOptions`, `riderPenalty`, a coded source). m is the share of the cell
  inside his outline (`constant/riderOutline`), from the signed distance d of the cell
  centre to the outline, m = clamp(0.5 - d/h, 0, 1) with h the cell's size. So his edge is
  **blurred over one cell, 1-3 cm**, and he has **no boundary layer of his own**, no wall
  function and no k or omega held inside him. His position is a function of absolute
  time, so a restart puts him back in the right place. The term is implicit, in the
  matrix's diagonal, and costs nothing measurable per step.
- **The force on him** is the reaction to that drag, F = rho sum K m (U - U_r) V, per metre
  of height, written every step by the coded function object `system/riderForceIB`. It is
  a total: there is no split into pressure and friction. + x is forwards, his direction of
  travel, and + y is towards the lorry.
- **What else it writes.** The lorry's forces every step, and a 1581 x 201 grid of U and the
  rider's mask every 1/120 s from 4.0 s for the clip (`panelGrid`, about 11 MB a write as
  VTK: 5.5 GB for `gap150` and 3.3 GB for `gap030`).

The rider was first put on an overset mesh moving with him. On this background one step
took 100-135 s on one core, because the overset stencil keeps multigrid from converging the
pressure, about 180-250 hours a run on 14 ranks; overset was dropped for the drag term, at
5.0-7.5 s a step on one core.

## Checks before the runs

- **The drag term holds the air at his speed.** In a 2 cm box with the air at 22.2 m/s and
  him moving at 16.667 m/s, the air in his fully covered cells was within 5.3e-4 m/s of his
  velocity after 0.5 s, his masked area 0.0990 against his outline's 0.0988 m2, and his drag
  16.7 +- 1.7 N/m, a drag coefficient of about 2.1 on his 0.42 m width: a bluff section.
- **Against a body-fitted rider** fixed in a 5.56 m/s stream, the drag term gave 12.3 N/m
  with walls nearby, against 10.1-11.4 N/m for a meshed rider with wall functions before it
  began to shed. The meshed rider then sheds at 3 Hz and its drag rises to 20.7 N/m; the
  drag-term rider never sheds, because the one-cell shear at his edge makes turbulence that
  keeps the eddy viscosity in his near wake high. A real rider's wake is three-dimensional
  and far less regular than either.
- **His cells on the real mesh**, at four positions along his path for each gap: masked
  area within 0.16% of his outline's, 269-291 cells fully covered and 72-85 partly.
- **A restart** from an intermediate write reproduced 20 steps' times, step sizes, Courant
  numbers and rider forces at printed precision, and his mask cell for cell.
- **The first look** at 3.5-3.6 s, with the 1.5 m rider still 22-23 m ahead of the cab:
  the lorry's drag 958 N/m, a 2-D drag coefficient of 1.24 on its 2.55 m width, against
  the 3-D lorry's 0.65 on its frontal area (a section that air cannot pass over takes more
  drag), and the rider's drag 14.1 +- 2.4 N/m.

## Results

The force on the rider every step is in `results/rider_force_gap150.csv` and
`results/rider_force_gap030.csv`. Single steps jitter by about a cell's worth as his edge
crosses cells, so every peak below is read after smoothing, and over twelve smoothings
(`scripts/pull_ratio.py`, `results/pull_ratio.txt`): running means of 0.02, 0.05 and
0.10 s of flow, centred and trailing; 2 m bins of his position at four phases; and 1 m bins
at two. Peaks are taken inside the clip's window, t = 4.4167-6.0417 s, from 8.1 m ahead of
the cab's front to 19.0 m behind it, 2.5 m past the doors.

- **The push** away from the lorry, as the cab's front passes him: the 30 cm pass's peak is
  **2.9-4.1 times** the 1.5 m pass's (median 3.6), 56-86 N/m against 17-21 N/m.
- **The pull** towards the lorry, as the doors pass him: the 30 cm pass's peak is
  **5.4-8.3 times** the 1.5 m pass's (median 6.0), 91-104 N/m against 11-19 N/m. The 2 m
  bins give the high end, because they average the 1.5 m pass's short peak with its fall.
- **With the clip's own smoothing**, the mean over the 0.05 s of flow up to each frame,
  updated every 6 frames, the ratios are 3.96 for the push and **5.56 for the pull**
  (102.3 against 18.4 N/m). The clip says "6x the pull".
- Between them, along the trailer, the sideways force on both riders stays under about
  10 N/m and the force on him is mostly his drag, backwards.

So at 30 cm the push is about 3-4 times and the pull about 6 times what they are at 1.5 m,
in this model.

### Against the 3-D overtaking run

The 1.5 m pass is `cyclistBehindLorry`'s overtaking pass, which has a force in newtons, so
the two can be compared, the 2-D force per metre and the 3-D one an estimate over his whole
body (`scripts/compare_27.py`, `results/compare_27.txt`). In 1 m bins of his position:

- **The push**, about 1 m after the cab's front passes his shoulders (0.5-1.5 m):
  **-17.8 N/m** here against **-17.1 N** in 3-D.
- **The pull along the trailer**, 1.5 m before the doors (14.5-15.5 m): **+4.7 N/m** against
  **+4.1 N**.
- **At the doors** the two part: the pull here is 15.7 N/m in the bin from the doors
  (11-19 N/m over the twelve smoothings), about **3 times** the 3-D run's peak of 5.3 N.
- **The drag backwards** along the trailer is 20-25 N/m here against 10-15 N in 3-D, about
  **twice**, as for the lorry's own drag.

A test of the shape was written down before the 1.5 m pass had a force, on 0.05 s means:
the push first and the pull after, the push's peak within 2 m of the 3-D one's, the sign
change within 3 m, the pull's peak within 4 m, and the two curves, each scaled by its own
push peak, correlating at r of at least 0.7. Over 4-6.4 s, the stretch the 30 cm pass was
solved over, it passes all five: the push peaks 1.9 m behind the cab's front (3-D 1.7 m),
the sign changes at 10.5 m (10.7 m), the pull peaks at 16.6 m (17.5 m), r = 0.80. Over
4-8 s, the window as written, it fails all five, because behind the doors the 2-D wake
takes over (below), and its largest force comes 35 m past the doors, at the run's end.
The 30 cm pass was solved on the strength of the agreement alongside the lorry, and only to
6.4 s.

**Behind the doors** the 2-D wake is an artefact. At 1.5 m it pulls the rider at 6-42 N/m
(2 m bins) for about 25 m past the doors and then swings into a push of up to 38 N/m by the
run's end, 35 m past them: a regular vortex street, which a slice with no air over the roof
makes. In 3-D the pull fades from 5 N to nothing about 8 m past the doors, and the push
after it stays under 2 N. At 30 cm it pulls him at 79-96 N/m to 6.4 s. That is why the
clip stops 2.5 m past the doors, just as the pull peaks, and why the 30 cm run ends at
6.4 s.

**For the force in newtons** on a real rider, use `cyclistBehindLorry`'s overtaking run:
at 1.5 m, about 21 N in the road's plane at the peak, 17 N of it sideways. This case gives
only how that changes at 30 cm, as a ratio.

## What the clip shows, and what it does not

**It shows** the two passes side by side, from above at his shoulder height, in his frame:
he is fixed and the lorry comes up from below and passes him, coloured by the air's speed
over the road, with parcels of air carried by the solved flow. An arrow at his shoulders
shows the air's force on him in the plane, sideways and fore-aft together, at one scale in
both panels, so their lengths compare directly. The close panel's one number is its pull as
a multiple of the 1.5 m pull, "6x". The push and the pull play 12x slow; the 0.7 s of flow
along the trailer between them plays faster, with a mark on screen while it does. It runs
from 4.4167 to 6.0417 s of flow, showing 3 m of road behind him, so the wake fills about a
third of each field at the end.

**It does not show** newtons, the push's ratio as a number, or anything after 2.5 m past
the doors.

## What it cannot

- **A 2-D slice at z = 1.3 m.** Air cannot go over the roof or under the trailer, or over or
  round the rider; everything is per metre of height. Round the lorry's sides it is squeezed
  harder than real air, and the wake behind the doors is far stronger and more regular.
  Alongside the lorry the 1.5 m pass's sideways force matches the 3-D estimate's within
  15%, but its pull at the doors is three times the 3-D one and its drag twice. Only ratios
  between the two passes, on the same model and mesh, are reported.
- **The rider is a drag term**, blurred over one cell of 1-3 cm, with no boundary layer, no
  wall function and no turbulence of his own, a steady wake where a meshed 2-D rider sheds,
  and a total force with no pressure and friction parts. At 30 cm the gap holds about 45
  cells, so his blurred edge is a few per cent of it.
- **Only the shoulders.** One section of his body stands for all of it; his legs and the bike,
  most of his side area, are at heights where the lorry's flow differs.
- **URANS, one mesh.** k-omega SST with wall functions, the lorry's boundary layer at
  y+ 19-446, no mesh or time-step study, one realization of each pass.
- **One speed, two gaps.** No mirrors, side guards, crosswind, road, road curve or oncoming
  traffic, and the rider does not respond to the force.
- **Not advice.** Nothing here says either gap is safe.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with
gmsh (the Python module) and NumPy; `scripts/sections.py` also needs trimesh and shapely.

    cd cases/lorryClosePass2D
    ./Allrun mesh                    # the background mesh, about 2.5 minutes on one core
    ./Allrun precursor               # 0-3.4 s on 14 ranks
    ./Allrun gap150                  # 3.4-8.0 s; --setup-only gap150 stops before the solve
    ./Allrun gap030                  # 3.4-6.4 s
    python3 scripts/rider_force.py runs/gap150 results/rider_force_gap150.csv
    python3 scripts/rider_force.py runs/gap030 results/rider_force_gap030.csv
    python3 scripts/pull_ratio.py results > results/pull_ratio.txt
    python3 scripts/compare_27.py results/rider_force_gap150.csv \
        ../cyclistBehindLorry/results/overtaking_force.csv > results/compare_27.txt

The outlines in `geometry/` are committed. To cut them again, build `cyclistBehindLorry`'s
lorry and rider (`python3 scripts/build_truck.py` and `build_rider.py` there; the rider
downloads about 23 MB of MakeHuman files) and run `python3 scripts/sections.py`.

`Allrun mesh` meshes the lorry's outline with `scripts/make_mesh.py` in `runs/mesh/`,
imports it with gmshToFoam, makes the z faces empty and the lorry a wall, deletes the .msh
(about 190 MB) and checks the mesh. `Allrun precursor` copies it to `runs/precursor/` with
`template/`, decomposes it and solves. `Allrun gap150|gap030` copies the mesh and the
precursor's last write into `runs/<gap>/`, writes `constant/riderOutline`
(`scripts/rider_outline.py`), sets the gap's yShoulder and endTime, checks and decomposes
it, and solves. Running a gap again once it is decomposed continues it from its latest write
into `log.pimpleFoam.restart1`. `./Allclean` removes the runs.

The solves took 5.3 hours for the precursor, 5.3 hours for `gap030`, and for `gap150` 5.8
hours to 6.28 s, where one rank's memory grew to 26 GB and the run hung, then 3.6 hours
restarted from its 6.2 s write to 8.0 s, all on 14 ranks. `rider_force.py` keeps the
restart's rows from 6.2 s.

From a clean copy, `Allrun mesh` wrote the solved mesh byte for byte (787,842 cells),
`--setup-only precursor` wrote the precursor's dictionaries and initial fields byte for byte,
and `--setup-only gap150` and `gap030`, given the precursor's solved 3.4 s write, wrote both
runs' dictionaries, rider outline, mesh and starting fields byte for byte. `sections.py` on
`cyclistBehindLorry`'s rebuilt STLs wrote both outlines byte for byte. `pull_ratio.py` on the
committed force histories reproduces the clip's ratios. The histories are rounded to 1 ns and
0.1 mN/m from the runs' `force.dat`, which is all that is kept of the solves: no fields,
meshes, panels or logs.

The case was set up and solved by an agent on our own machine, the rider first on an overset
mesh and then, for cost, as the drag term; the mesh, the outlines and the comparison with
the 3-D run were checked and the clip's numbers computed afterwards.
