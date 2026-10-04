# A reversed ceiling fan under a 20 ft ceiling

[`ceilingFanWinter`](../ceilingFanWinter) found that a reversed fan (blowing up) in a
heated 10 ft room leaves the heater's heat lying along the floor. This case asks whether
that survives a ceiling twice as high. It is `ceilingFanWinter`'s case with the ceiling
raised from 3.05 to 6.10 m and the mesh extended at the same resolution. For the
published comparison the heater is also doubled, 1300 to 2600 W, so that each cubic metre
of air gets the same heat as in the 10 ft room. Everything else is unchanged.

One OpenFOAM case, one `config.sh`, the heater power as an optional third argument:

    ./Allrun up medium            # 2600 W, fan reversed         (the clip)
    ./Allrun up medium 1300       # 1300 W, fan reversed         (the first comparison)
    ./Allrun down medium 1300     # 1300 W, fan blowing down     (the first comparison)

The clip sets `ceilingFanWinter`'s `./Allrun up medium` (top, 10 ft) against this case's
`./Allrun up medium` (bottom, 20 ft).

## What changed from ceilingFanWinter

`config.sh` differs from `ceilingFanWinter/config.sh` in four lines:

- `ROOM_HEIGHT` 3.05 to 6.10 m.
- `Z_BREAKS` and `Z_CELLS` add a block from 3.05 to 5.85 m at the bulk's 40 mm (70 cells)
  and give the new ceiling the old one's 13-cell layer at 19.2 mm (5.85 to 6.10 m).
- `HEATER_W` 1300 to 2600 W (see below; `./Allrun ... 1300` puts it back).

The fan, its swirl, the heater's ring, the wall loss, the uniform 20 C start, the numerics
and the 0 to 180 s window are `ceilingFanWinter`'s. The fan stays where it was, its disk
at 2.60 to 2.74 m, so it now hangs 3.4 m below the ceiling.

**The mesh.** 20,720 cells (185 x 112) against 11,424. Below 3.05 m it is the old mesh
cell for cell: all 11,424 cell centres are found, the largest difference 8e-16 m, and the
fan zone (217 cells) and heater zone (325 cells) are the same cells.
`checkMesh -allGeometry -allTopology` passes: aspect ratio at most 4.0, no
non-orthogonality, skewness at most 0.33 (`results/vs_ceilingFanWinter/mesh_vs_ceilingFanWinter.txt`).

`makeCase.py` gains two things. It takes the heater power as an optional fourth argument.
Its `controlDict` has one more function object, `heatBudget`, which only reads the
solution and prints at every step the wedge's integral of T and the conductive loss
through floor, ceiling and outer wall; `heat_budget.py` turns those lines into a budget.
The 1300 W runs were solved without that function object; their dictionaries are
otherwise byte-identical to what this `makeCase.py` writes, and the 2600 W run's are
identical in full.

## Why 2600 W

At 1300 W the tall room has twice the air to heat with the same heater, so it warms more
slowly everywhere, and a comparison of the two rooms mostly shows that. Scaling the
heater with the air volume keeps the heat per cubic metre the same.

Both rooms have the same floor, 37.21 m2 (radius 6.10/sqrt(pi) = 3.441 m):

- 10 ft: 37.21 m2 x 3.05 m = 113.49 m3, and 1300 / 113.49 = **11.45 W per m3 of air**
- 20 ft: 37.21 m2 x 6.10 m = 226.98 m3, and 11.45 x 226.98 = **2600 W**,
  which is 1300 W x (6.10 / 3.05)

With rho c_p = 1.2 x 1005 = 1206 J/(m3 K), either room would warm at 0.57 K a minute if
nothing left through the walls. On the 5-degree wedge the heater's source on T is
2600 x (5/360) / 1206 = 0.029943 K m3/s, twice the 1300 W run's 0.014971. The ring is the
same 0.25 x 0.50 m against the wall, so its power density doubles, 499 to 998 W/m3.

Equal heat per volume does not make the rooms alike. The tall room has 206.3 m2 of floor,
ceiling and wall, 0.91 m2 per m3 of air, against 140.4 m2 and 1.24 m2 per m3, so at the
same temperature difference it loses less heat per cubic metre. And the heater puts out
120 W per metre of wall instead of 60, so its plume is twice as strong.

**The heat budget closes.** Over each 7.5 s interval, the change in the room's stored heat
against 2600 W in minus the wall loss is out by at most 17.8 W, 0.7% of the heater; the
first 30 s close to within 0.02 W. By 180 s the walls take 586 W (floor 118, ceiling 93,
outer wall 375) (`results/heater2600W/up_medium/heat_budget.txt`).

## Results

Temperatures are r-weighted means across the room at `ceilingFanWinter`'s heights, from
both cases' r-z faces with `ceilingFanWinter`'s own method
(`results/vs_ceilingFanWinter/heater2600W.md`; both sides reproduce their own
`history.csv` to 0.00002 K). Fan reversed in both rooms, 10 ft / 20 ft:

| t | 0.10 m | 1.09 m | 1.70 m | 2.75 m | 20 ft, 12 in below its ceiling |
|---:|---:|---:|---:|---:|---:|
| 60 s | 21.29 / 21.01 C | 20.28 / 20.44 C | 20.18 / 20.40 C | 20.24 / 20.61 C | 20.47 C |
| 120 s | 21.97 / 22.34 C | 20.64 / 20.85 C | 20.47 / 20.93 C | 20.64 / 20.92 C | 20.89 C |
| 180 s | 23.06 / 22.01 C | 20.78 / 21.55 C | 20.62 / 21.49 C | 20.72 / 21.57 C | 21.24 C |

The two rooms warm by nearly the same amount on average: over each room's whole
cross-section, r-weighted, 20.51 and 20.51 C at 60 s, 20.93 and 20.98 C at 120 s, 21.32
and 21.42 C at 180 s. The heat ends up in different places.

**In the 10 ft room** the reversed fan's air comes down the wall onto the heater and
carries its warm air inward along the floor, as `ceilingFanWinter` describes. At 180 s
the floor is 2.3 K above body height (1.09 m), which has warmed by 0.8 K.

**In the 20 ft room** the heat is spread through the height. At 180 s body height is
21.55 C, **0.77 K warmer than in the 10 ft room**, and the floor is 0.46 K above it. The
floor reading is not steady: warm patches from the heater's plume drift across it and are
swept away (22.34 C at 0.10 m at 120 s, 21.31 C at 150 s, 22.01 C at 180 s). Body height
also jumps early, to about 20.9 C between 17 and 45 s, when the head of the plume first
rolls across the room, then falls back.

The air does reach the heater in the tall room: over 60 to 180 s, 2.97 m3/s flows into
the heater's section through its top and room-side face, and 9.0 m3/s each way through
the 1.70 m plane, against the fan's 1.72 m3/s through its disk. Nothing short-circuits.

Histories: `results/*/*/history.csv`, `results/vs_ceilingFanWinter/*.csv`, and
`results/four_height_histories.png` (drawn by `plot_histories.py` from those CSVs). In
the `vs_ceilingFanWinter` files "07" is `ceilingFanWinter` and "10" is this case, the
numbers of the clips they back.

One trap in `summary.txt`: `postprocess.py` is `ceilingFanWinter`'s, so `T275` is 2.75 m,
which here is not near the ceiling, and `deltaT_275_minus_010_K` is not top minus bottom.
The 12 in below the 6.10 m ceiling is in the comparison files (`T580`, at 5.7952 m).

### At 1300 W

The first comparison kept 1300 W in the tall room
(`results/vs_ceilingFanWinter/heater1300W.md`). The tall room warmed less: 20.71 C over
its cross-section at 180 s. Fan reversed, body height was 20.65 C at 180 s against
20.78 C in the 10 ft room, a little cooler, and the floor stayed within 0.3 K of body
height from 90 s on.

Blowing down against reversed in the tall room was a tie. Over 60 to 180 s, reversed was
warmer at body height by 0.03 to 0.08 K and blowing down warmer at the floor by 0.2 K. In
the 10 ft room blowing down was warmer at body height by 0.14 to 0.25 K. Nothing in the
tall room at 1300 W gives either direction an advantage a person would feel.

## What the clip shows, and what it does not

**It shows** the full cross-section through each room, the solved half and its mirror
image, from switch-on to 180 s, 10 ft above 20 ft at one scale in metres and one
temperature scale (20 to 23.5 C, `ceilingFanWinter`'s), with streamlines of the in-plane
air. The fan and the heater are drawn over the cells where the case applies them, and the
arrows on the fan show the direction the solved fan drives the air.

**It does not show** swirl, or any number. On the clip's scale the 2600 W heater's plume
runs off the top of the scale against the tall room's wall up to about 1.3 m.

## What it cannot

- **A ring heater on a wedge, not a heater in a corner.** The room is axisymmetric, so the
  heater is a ring against the whole wall, and the reversed fan's air comes down onto it
  everywhere. The 10 ft result depends on that (see `ceilingFanWinter`), and so does this
  one. A heater standing somewhere in a real room would meet that air somewhere else.
- **A narrow room for its height.** A 37 m2 floor with a 6.10 m ceiling is 6.9 m across and
  6.1 m tall, so the circulation the fan drives turns in a column about as wide as it is
  tall, with the walls as close to the axis as in the 10 ft room. The fan was left at the
  10 ft room's height, 3.4 m below the ceiling, rather than raised.
- **180 seconds from a uniform start.** Neither room has settled; both are still warming at
  180 s. The window is `ceilingFanWinter`'s so the two can be set side by side, not one
  chosen for this room.
- **The swirl core on the axis.** Blowing up, a swirling core of about 1 m/s forms within
  10 cm of the axis. At 1300 W it left a faint cool line by 180 s, 0.15 to 0.3 K below the
  air at r = 0.3 m from the floor to about 2 m, smooth across the axis rather than a spike
  in one cell. It is the solved flow of an axisymmetric model with an unforced hub, and
  nothing here tests whether a real fan's wake holds such a line. It also holds the time
  step to 0.5 to 0.8 ms, which is why the reversed runs are slow.
- **At 1300 W the ceiling comparison was a near tie**, and at 2600 W the tall room's heater plume
  is twice as strong per metre of wall. The headline difference, body height 0.8 K warmer
  in the tall room, belongs to equal heat per volume; it is not what happens if the same
  heater is moved into a taller room. With the same heater, the tall room is slightly
  cooler at body height.
- **Everything `ceilingFanWinter` cannot**: estimated airflow, swirl ratio and wall
  conductance, an actuator disk instead of blades, URANS on one mesh with no mesh or
  time-step study, draft areas well above measurement, and a 0.10 m statistics line that
  passes through the heater.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, a C++ compiler
for the `heatBudget` coded function object, and Python 3 with NumPy, pandas, Matplotlib
and PyVista.

    cd cases/ceilingFanHighCeiling
    ./Allrun up medium

`Allrun` writes the case into `runs/heater<W>W/<direction>_<speed>/`, meshes it, checks
the mesh, samples t = 0, solves to 180 s on 4 MPI ranks, and writes `results/` in the
run with `postprocess.py`. On 4 ranks the solver took 9,559 s for the 2600 W reversed
run, and 12,521 s (reversed) and 7,051 s (blowing down) for the 1300 W runs
(`results/*/*/wallclock.txt`).

Then:

    python3 heat_budget.py runs/heater2600W/up_medium/log.solver            # --heater-w 1300 for the others
    python3 compare_07.py runs/heater2600W out --runs up_medium             # needs ceilingFanWinter's up run
    python3 compare_07.py runs/heater1300W out --runs down_medium up_medium
    python3 plot_histories.py

`compare_07.py` reads `ceilingFanWinter`'s faces from `../ceilingFanWinter/runs` (or
`--ref`), so run that case's `./Allrun up medium` (and `down medium`) first. The swirl
check in `ceilingFanWinter/verification/swirl` covers this case's wedge too; it does not
depend on the ceiling. `./Allclean` removes the runs.

The case was built by an agent from `ceilingFanWinter`'s files and checked by us. The
2600 W run's dictionaries are what this directory writes, byte for byte; the 1300 W runs'
differ only by the read-only `heatBudget` monitor.
