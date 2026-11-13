# Four riders in a pace line, against one rider alone

Riders in a club pace line take turns at the front because the front is where the work is. The riders
behind are said to save anything from a fifth to a half of their effort, and whether the leader gains
anything from the rider on their wheel is argued over in every club. This case puts four identical road
riders in single file at 40 km/h, each front tyre 0.3 m behind the rear tyre ahead, next to the same
rider riding alone at the same speed, and asks how much air resistance each rider in the line has
against the lone rider: the front, the middle and the back. It is about air resistance, not power: the
rolling resistance and the drivetrain, which are the same in the line, are left out.

    ./Allrun line     # four riders in single file, 0-1.71 s from rest
    ./Allrun alone    # the same rider alone, 0-1.71 s

**The result.** Over 1.0-1.71 s of flow the lone rider's air resistance, rider, bike and both wheels,
is **36.1 N** (Cd 1.07 on 0.448 m²). In the line the leader has **96.8%** of it (34.97 N), a 3.2%
saving, and the three riders behind him have **61.8%, 52.5% and 56.6%** (22.33, 18.97 and 20.44 N),
savings of **38.2%, 47.5% and 43.4%**, inside the 23-48% published for riders sheltered behind
another: 23% for a second rider in Blocken et al.'s two-rider study and 42-48% for positions 2-4 of a
team pursuit (below). The leader's 3.2% sits beside those sources' 1.7% and 4%. The wake sheds: the
side-to-side velocity at all 24 wake probes, twelve behind the lone rider and twelve in and behind the
line, fluctuates at 0.18-1.38 m/s rms, with spectral peaks at 4-13 Hz at 23 of them. Read
[What it cannot](#what-it-cannot) before any number here: **the averaging window is 0.71 s**, about
one passage of the air along the line, so the order of the riders behind, rider 3 lowest, then 4, then
2, is not statistically resolved, and the case does not name a best seat; over the two halves of the
window riders 2 and 3 each move by 0.68 N, about two points of share. And it is **one mesh**, with
prism layers on only about a third of the riders' surface.

The rider and his bike are [`cyclistBehindLorry`](../cyclistBehindLorry)'s, unchanged, and the case
is that case's recipe made finer: pimpleFoam with k-ω SST-SAS, the rider fixed and the air and road
moving past him. [`marathonDrafting`](../marathonDrafting) asks the same question of runners behind a
pacer.

## The riders and the line

x runs forward along the line (the air comes from +x), y across, z up from the road; metres.

| | value | from |
|---|---|---|
| rider | a 1.75 m male in the drops on a size-56 road bike, static, cranks horizontal, wheels not turning; one closed surface for rider, helmet and frame, and two separate wheels; 1.66 m from the front tyre's leading point to the rear tyre's trailing point; frontal area 0.448 m² with the wheels | [`cyclistBehindLorry`](../cyclistBehindLorry), "The rider and the bike" |
| the line | four copies on y = 0, 0.3 m from each rear tyre to the next front tyre, so 1.96 m from rider to rider; the leader's front tyre at x = 0, the line 7.54 m long | ours: half a wheel or closer, a club pace line's gap |
| alone | one copy at the leader's place, in the same domain with the same refinement boxes | ours |
| speed | 40 km/h, 11.1111 m/s, a brisk club pace line; still air, no crosswind | ours |
| air | ν = 1.5e-5 m²/s, ρ = 1.225 kg/m³ for the forces; Re = 1.3e6 on 1.75 m | ISA sea level |

**The geometry is not in this folder.** `Allrun` builds it with `cyclistBehindLorry`'s
`scripts/build_rider.py` into `../cyclistBehindLorry/geometry/` if it is not there (NumPy, manifold3d,
trimesh and shapely; PyVista only for previews). That script poses MakeHuman's base mesh and targets,
which the MakeHuman project releases under CC0 (`../cyclistBehindLorry/geometry/LICENSE.ASSETS.md`),
downloaded from MakeHuman's repository at a pinned commit, so the surfaces can be redistributed, but
at 17 MB (`rider.stl`) and 5.7 MB (`bike_wheels.stl`) as ASCII STL they are rebuilt rather than
committed. Built from a clean copy of `cyclistBehindLorry` on 13 Nov 2026, both files were the solved
runs' byte for byte (SHA-256 `29e19bea...` and `99df747d...`).

## The model

- **Domain.** x = -30 to 20 m, y = -8 to 8 m, z = 0 to 10 m, from a 1 m background (`blockMeshDict`),
  the rider 20 m from the inlet; the riders block 0.3% of its cross-section. Inlet at x = 20 m, outlet
  at x = -30 m, symmetry planes at the sides and the top.
- **Boundary conditions.** Inlet: U = (-11.1111, 0, 0) m/s, k = 0.0185 m²/s² (1% intensity) and
  ω = 0.497 1/s (0.5 m length scale). Outlet: p = 0, inletOutlet for U, k and ω. The road is a wall
  moving with the air (`movingWallVelocity`), the riders and wheels no-slip walls with Spalding's wall
  function (`nutUSpaldingWallFunction`), which holds from the buffer layer to the log layer, the road with
  `nutkWallFunction`. The air and everything else start at the free stream at t = 0, an impulsive start.
- **Mesh** (`template/system`, `scripts/make_case.py`, `config/case.json`). snappyHexMesh: rider and
  wheel surfaces at level 5, 1/32 m; refinement boxes at 1/4 m (x -22 to 4, |y| < 3, z < 5), 1/8 m
  (x -16 to 2, |y| < 1.5, z < 2.2), 1/16 m (x -14 to 0.6, |y| < 1, z < 1.9) and 1/32 m around the
  riders and their near wakes (x -10.5 to 0.2, |y| < 0.5, z 0.15-1.6, about 13 cells across a 0.4 m
  wake). Three prism layers are asked for on the riders' bodies (expansion 1.25, final layer 0.3 of
  the cell), none on wheels or road. **Line 770,356 cells, alone 771,336**, both `checkMesh` OK
  (non-orthogonality up to 63.1° and 61.9°, skewness up to 3.76).
- **The layers cover about a third of the rider.** The normal quality checks of snappyHexMesh's layer
  stage kept layers on 31.2% of the line's rider faces and 31.0% of the lone rider's, a face-weighted
  0.64 and 0.63 of the three asked for (0.54-0.77 by rider). y+ on the rider bodies averages 260-350
  (`yPlus` at 1.5 s), so the walls are carried by the wall function. See
  [How the case got here](#how-the-case-got-here) for why the layers were not pushed further.
- **Turbulence and numerics.** pimpleFoam (OpenFOAM v2512), k-ω SST-SAS (`kOmegaSSTSAS`, cubeRootVol
  delta), a scale-adaptive model that resolves the large eddies of the wakes where the mesh allows and
  falls back on SST elsewhere; plain SST froze the runners' wakes in `marathonDrafting`'s first build.
  Backward in time, adaptive steps at Courant 0.9 (about 2.5e-4 s), linearUpwind for U, limitedLinear
  for k and ω, cell-limited gradients; PIMPLE with two outer and two pressure correctors and one
  non-orthogonal corrector, GAMG for p.
- **Monitors.** The force on each rider with his wheels every step (`rider<i>Forces`, `rider<i>Coeffs`
  on Aref 0.448 m², lRef 1.75 m); U at 12 probes at hip height, z = 1.0 m, on the centreline and
  0.25 m to the side at x = -1.87, -3.83 and -5.79 m (the gaps between the line's riders), -7.75 m
  (0.21 m behind the back rider) and -10 and -12 m (`wakeProbes`); the horizontal plane at z = 1 m
  every 1/120 s for the clip; y+, cell Courant numbers and field extrema.

## Results

`results/summary.txt`, `results/means.csv`, `results/history.csv` (each rider's drag in 0.01 s bins from
t = 0) and `results/wake_probes.csv`, written by `scripts/extract_results.py` from the solved runs'
monitors. Means are time-weighted over **1.0-1.71 s**, the window's ends interpolated.

| | drag (N) | Cd | share of alone | saving | 1.0-1.355 s (N) | 1.355-1.71 s (N) |
|---|---:|---:|---:|---:|---:|---:|
| alone | 36.136 | 1.067 | 100% | | 36.152 | 36.120 |
| line 1, the leader | 34.974 | 1.032 | **96.8%** | 3.2% | 34.977 | 34.972 |
| line 2 | 22.331 | 0.659 | **61.8%** | 38.2% | 22.671 | 21.992 |
| line 3 | 18.975 | 0.560 | **52.5%** | 47.5% | 19.314 | 18.636 |
| line 4, the back | 20.438 | 0.603 | **56.6%** | 43.4% | 20.360 | 20.516 |

Pressure drag is 98.4-98.6% of each rider's drag (35.61 of 36.14 N alone). The force and coefficient records
agree to 5e-6 in Cd.

- **The leader's saving is resolved.** His two half-window means differ by 0.006 N against the 1.16 N
  between him and the lone rider.
- **The riders behind are not ranked.** In both halves of the window rider 3 is lowest and rider 2
  highest, but riders 2 and 3 each drop 0.68 N from the first half to the second, rider 4 rises
  0.16 N, and 0.71 s is a single sample of a wake that sheds at 4-13 Hz. Riders 3 and 4 are 1.46 N
  apart, about four points of share. That the one-but-last seat is the best, which a paper on longer
  lines is said to report (Sources), would need a longer window to show.
- **Against the sources.** 38-48% saved by the riders behind and 3% by the leader: Blocken et al.
  (2013) give 23.1% for the second of two riders and 1.7% for the leader in the dropped position; the team
  pursuit summary gives 4%, 42%, 48% and 47% for positions 1-4. The case's riders are not those riders,
  and nothing here was tuned to these figures.
- **The wake** (`results/wake_probes.csv`). Behind the lone rider the side-to-side velocity fluctuates
  at up to 1.3 m/s rms within 2.2 m of his rear tyre and still 0.18-0.27 m/s 10 m back, with a
  spectral peak at 7.0 Hz at 8 of the 12 probes; his wake has recovered to a mean 9.9-10.7 m/s of the
  stream's 11.1 from 4 m behind him on. In the line's gaps the air moves at 3.6-5.9 m/s and sideways
  at 0.9-1.4 m/s rms, peaks at 4-8 Hz; behind the back rider it is still 6.9-9.7 m/s at 0.2-4.5 m. The peaks pass a
  test in the script (a local maximum over 25% of the power and ten times the median, at a resolution
  of 1.41 Hz) and are indicators, not measured shedding frequencies. On the planes, followed for the
  clip, the centre of the lone rider's wake wanders with a standard deviation of 8-12 cm, the rider
  behind holds each gap's wake to about 2 cm, and behind the back rider it swings again, about 10 cm.

## What the clip shows, and what it does not

The clip shows the two plan sections at hip height, z = 1 m, side by side and seen from above with the
wind coming down the screen, the rider alone on the left and the four in a line on the right, the
leader level with the lone rider. Colour is the wind speed on one 0-50 km/h scale, with streamline
dashes, a bar of air resistance beside every rider and one number per panel, ending at "air resistance
100%" on the left and "leader's air resistance 97%" on the right, under the question "A pace line: who
does the work?". It runs 0-1.71 s of flow from rest at 12x slow motion.

- The bars are each rider's trailing 0.5 s mean as a share of the lone rider's, and stay empty for the
  first 1.2 s of video, while the start-up pressure spike passes.
- Frames between two plane writes blend the planes' velocities linearly in time; the riders are drawn
  as top-view outlines of the STL; the dashes are traced through the planes after the solve.
- The clip names no best seat.

## What it cannot

- **The averaging window is 0.71 s.** The case was briefed for 2-4 s; the study's 10 h of machine time
  allowed 1.0-1.71 s (see [How the case got here](#how-the-case-got-here)). The air needs 0.68 s to pass
  the 7.5 m line, so the window holds about one passage, and the means of the riders behind move by up
  to 0.68 N between its halves. The shares behind are good to a few points, not better; their order is
  not resolved. Short spikes in the force histories are in the means; whether they are physical or from
  the time step was not resolved.
- **One mesh.** No mesh or time-step study. The prism layers cover about 31% of the riders' surface, y+
  is 260-350, and on this layer setting the extended checks flagged concave cells and 20 (the five-rider
  line's mesh) and 5 (the lone rider's) low-determinant cells; the lone rider's Cd of 1.07 (CdA 0.48 m²) is high for a rider in the drops, though below
  `cyclistBehindLorry`'s 1.13 on a coarser mesh with no layers. The shares compare the same rider on the
  same refinement, so less of that error reaches them than reaches the newtons.
- **Identical static riders.** No pedalling, cranks level, wheels not turning (the road moves), no
  clothing, hair or shoes. MakeHuman's figure is broad. Real lines mix sizes and positions.
- **Single file, 0.3 m apart, in still air.** No crosswind, no echelon, no sideways offset, no change of
  gap. Real riders ride a few centimetres to the side of the wheel ahead and the gap opens and closes.
- **Four riders, not five.** The brief asked for five; the line was cut to four to fit the 10 h, and so
  has a front, a middle and a back, but not the one-but-last of a longer line.
- **From rest.** The window starts 1.0 s after an impulsive start, when the air has passed the line about
  one and a half times.

## Sources

- Blocken, Defraeye, Koninckx, Carmeliet and Hespel, "CFD simulations of the aerodynamic drag of two
  drafting cyclists", *Computers & Fluids* 71 (2013) 435-445: with two riders the leader gains 1.7% in
  the dropped position and the trailing rider loses 23.1% of his drag.
- Four-rider team pursuit, Manchester Velodrome, as cited in *Proc. IMechE Part P* (2017),
  doi:10.1177/1754337117692280: average drag reductions of 4%, 42%, 48% and 47% in positions 1-4. From a
  search summary; the paper was not read.
- Blocken et al., *J. Wind Eng. Ind. Aerodyn.* 179 (2018) 319-337 (abstract read): in the mid-rear of a
  121-rider peloton a rider's drag falls to 5-10% of riding alone. Context only; a peloton is not a line.
- That the one-but-last position of a longer line saves most: one unverified copy of a Defraeye et al.
  paper. Not used for any number.
- The rider and the bike: [`cyclistBehindLorry`](../cyclistBehindLorry), built from MakeHuman's CC0 assets.
- The question came from a viewer, under the clip of `cyclistBehindLorry`, who asked about the lead,
  the middle and the back of a group of cyclists.

## How the case got here

**A first solve, not in this case.** On 9 Nov 2026 five riders and the lone rider were solved 0-4 s on
`cyclistBehindLorry`'s recipe: rider surfaces at 1/16 m, wheels at 1/32 m, no prism layers, 1/8 m around
the line (line 145,169 cells, alone 121,105). Its riders behind saved 57-63%, beyond the published
23-48%, and its wakes, three cells across, settled into steady tubes. Nothing from it is used.

**The fine mesh.** The re-solve made the rider surfaces 1/32 m, added the 1/16 m and 1/32 m wake boxes
and asked for prism layers on the riders. A first layer setting with snappyHexMesh's relaxed quality
limits from its first iteration (`nRelaxedIter 0`) kept layers on 82% of rider faces, but both runs
broke down in their first time steps, the time step collapsing. The cause was traced to distorted prism
cells at body-layer junctions, on rider 3 at (-4.36, 0.15, 0.74) m in the line and on the lone rider at
(-0.96, -0.01, 0.39) m, and the one change made was **`nRelaxedIter 0 -> 50`**: the layer stage keeps its
normal quality limits for its 50 iterations, and drops the extrusions that fail them. That is why the
layers cover about 31% of the riders. Euler time stepping, upwind convection and other gradient schemes
were tried on the broken mesh and did not cure it, and are not used. The relaxed limits are still in
`snappyHexMeshDict`, unused within 50 iterations.

**The solve.** On 8 ranks of our own machine, about 6,100 (line) and 5,900 (alone) wall-seconds per
second of flow, some 3 h a run. The five-rider line did not fit the study's 10 h at that rate, so the
line was cut to four riders, and the end and the averaging window were cut from 2-4 s to 1.0-1.71 s.
Both runs were stopped and restarted from their written fields (both at 0.5 and 1.0 s) with nothing changed but the start and end times; their monitors hold one directory per
start, and the rows of an interrupted stretch after the restart point were removed, so each history is
one unbroken run. The lone rider ran on to 1.8 s; the 0.09 s after 1.71 s is not used.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with NumPy (and,
for the first build of the rider, manifold3d, trimesh and shapely; see `cyclistBehindLorry`).

    cd cases/cyclistPaceLine
    ./Allrun line                # [nProcs], default 8
    ./Allrun alone               # default 8
    python3 scripts/extract_results.py runs results

`Allrun` builds the rider if `../cyclistBehindLorry/geometry/` lacks him, writes `runs/<run>/` with
`scripts/make_case.py` (the riders translated into `constant/triSurface` with `surfaceTransformPoints`,
`system/` and `constant/` from `template/`, `0/` from `template/0.orig`, and the snappyHexMeshDict and
controlDict that list the riders), meshes it with blockMesh and a serial snappyHexMesh (about 4-5 minutes
each), checks the mesh, writes the forces and plane at t = 0, decomposes it by scotch, solves from 0 to
1.71 s, and once both runs have solved writes `results/`. `./Allrun --setup-only <run>` stops before the
solve; `./Allclean` removes the runs.

The dictionaries are the solved runs', byte for byte, but for two things in `controlDict`: the solved runs'
`startFrom latestTime` and end time were their restart controls, and an abort function object that stopped
them at the time cap is left out. The lone rider's controlDict listed the same function objects in a
different order. Each run writes about 200 plan planes (about 250 MB), fields every 0.5 s keeping the last
two, and every-step monitors of a few MB. `results/` holds the summaries only: no fields, meshes, planes or
logs.

The case was set up and solved by an agent on our own machine and checked by us. Checked from this folder on
13 Nov 2026: `scripts/make_case.py` writes both runs' `system/`, `constant/` and `0/` as solved but for the
controlDict lines above, and their eight and two translated STLs byte for byte; `checkMesh` on the solved
meshes gives Mesh OK at 770,356 and 771,336 cells. **snappyHexMesh was not rerun from this folder**, because
the machine's cores were busy with another solve, so that it rebuilds those meshes cell for cell is not
checked. `scripts/extract_results.py` on the solved runs' monitors gives the study's own means, half-window
means and probe statistics.
