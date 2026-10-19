# A man falling down a shaft onto a big cooling fan, and hanging in a wind-tunnel blast

In *Mission: Impossible – Ghost Protocol* (2011) a man jumps about 25 ft (7.62 m) down a
server room's cooling shaft onto a large spinning fan. A viewer asked whether the fan's air
could have caught him. This case drops a man belly-down from rest down a 3 m square shaft
twice and measures how much of his weight the air holds up: once over a big cooling fan
blowing 10 m/s up the shaft, and once in the updraft that holds his whole weight, which is
what an indoor skydiving tunnel blows.

    ./Allrun curve     # the man in steady updrafts of 8, 20, 40 and 55 m/s: his drag curve
    ./Allrun fan       # the fall over the fan, from letting go to reaching it
    ./Allrun float     # the same 1.30 s in the updraft that holds him

**In the film the air does not stop him.** A magnetic suit and a robot carrying a magnet
under him do (TV Tropes, below). The case asks what the air alone would have done. Nothing
from the film is used: the man is a MakeHuman figure and the shaft is ours.

**He is fixed and the air comes at him.** Nothing moves in the mesh. He is held still in the
middle of the shaft and the air enters from below at the updraft plus his fall speed, which
comes from a drag curve worked out first. **The fan is not in the solve**: the clip draws it.
**The mesh is coarse**, 104,646 cells. Read [What it cannot](#what-it-cannot) before any
number here.

## The man

The pacer of [`marathonDrafting`](../marathonDrafting), posed as a skydiver. He is built from
[MakeHuman](https://github.com/makehumancommunity/makehuman)'s assets (base mesh, targets,
skeleton and skin weights), which the project releases under CC0, the same way as that case's
runners and [`cyclistBehindLorry`](../cyclistBehindLorry)'s rider: `scripts/build_runners.py`
is marathonDrafting's builder, and `scripts/build_faller.py` uses its functions to pose him by
our own linear blend skinning, not by the MakeHuman application. The CC0 files are downloaded
from the MakeHuman repository at commit `a8bc2d54ff0ac92e78ff71431b1023eda42bf482`;
`geometry/LICENSE.ASSETS.md` is the licence, copied from it.

- **A 1.75 m male** with marathonDrafting's pacer's build, in a skydiver's stable belly-down
  spread (the "box"): back arched 20°, head raised 30°, upper arms out 10° above the shoulder
  line with the elbows bent about 90°, thighs spread 22° each side, knees bent 50°, feet
  pointed. He is turned face down and levelled so his trunk is horizontal.
- **One closed surface**, `geometry/faller.stl`: 50,000 triangles, watertight, one body, no
  self-intersections. Unclothed, bald, no shoes.
- **Volume 0.0621 m³, so 62.1 kg** at 1000 kg/m³, and a weight of 609.5 N. The area seen from
  below is 0.501 m², the drag coefficient's reference area.
- **Axes**: metres, x towards his head, y to his left, z up, so his belly faces −z and he
  falls along −z. The origin is his volume centroid. He spans x −0.75 to 0.86 m, y ±0.57 m
  and z −0.20 to 0.65 m.

`geometry/faller_build.json` is the builder's record of all of these. Allrun builds the
surface if it is not there; a rebuild wrote it again byte for byte.

## The shaft and the fan

| | value | from |
|---|---|---|
| shaft | 3.0 × 3.0 m, square, from 3.25 m below his centroid to 8.5 m above it, he on its axis; he blocks 5.6% of it | ours |
| fall | 7.62 m from letting go to the fan | the film's 25 ft (TV Tropes) |
| the fan's updraft | **10 m/s**, uniform across the shaft, 90 m³/s | about twice the mean through ebm-papst's 910 mm A3G910 at its rated speed, 5.0-5.7 m/s; generous to the fan |
| the blast | **49.4 m/s**, his own terminal speed from the drag curve | the case; indoor tunnels blow about 55 m/s for a belly-down flyer |
| air | 20 °C, ρ = 1.204 kg/m³, ν = 1.516e-5 m²/s | |

The film does not show which way the fan blows. The vents are hot and the fan cools the room,
so it is taken as blowing up the shaft, the reading that helps him most. The fan, its hub,
blades, swirl and the uneven jet off a real disc are not modelled: for nearly all of the fall
he is metres above it, and the clip draws it.

## The model

**His frame.** He is fixed and the air comes up at him at U_in(t) = w + v(t), where w is the
updraft and v(t) his fall speed. His fall obeys m dv/dt = m g − D(w + v). In his accelerating
frame the air also feels a uniform pressure gradient, which pushes on his displaced 0.062 m³
with about 1.2 × 0.062 × 10 < 1 N, against his 609.5 N; it is left out, and nothing else is
added for the frame.

**A drag curve first, then a tabulated inflow**, not coupling the force back step by step:

- He is about a thousand times denser than the air, so the air's added mass and the history of
  his wake change his motion by about 0.1%, and a quasi-steady drag curve is accurate.
- The float run's updraft is the curve's own answer, his terminal speed, so the curve has to
  exist before that run can be set.
- A table keeps the wake's force fluctuations out of the inflow. Coupling every step would feed
  his shedding back into the whole domain's inflow.

After the fan run, its own force history is used to integrate his fall again, and the
difference is reported ([Results](#results)).

**Stage 1, the drag curve** (`runs/curve/U8`, `U20`, `U40`, `U55`): steady inflow at 8, 20, 40
and 55 m/s, each run for 8 m of air past him (endTime 8/U), the drag averaged over the second
half, the last 4 m, a window fixed before the runs. CdA is interpolated linearly in speed
between the four. `scripts/analyse_curve_motion.py` finds his terminal speed u* (drag equal to
his weight, by bisection) and integrates the fall from rest over the 10 m/s updraft (RK4 at
0.1 ms) until he has fallen 7.62 m, and writes it as a 481-row table.

**Stage 2, the clip runs**: `fan`, with the inlet at 10 m/s plus v(t) from that table from
letting go (t = 0) to reaching the fan; `float`, with the inlet at u* throughout the same
1.3018 s. At t = 0 the whole domain starts at the inflow's speed and his wake builds from
there: the moment he lets go is the start of the calculation.

- **pimpleFoam with k-omega SST-SAS**, a scale-resolving model, as in marathonDrafting, whose
  plain SST froze the runners' wakes. Bounded linearUpwind for momentum, limitedLinear for k
  and omega, backward in time, one outer and two pressure correctors; the time step adjusts
  to a Courant number of 3.
- **Boundaries**: the inlet uniform; the outlet at fixed pressure; **the shaft's walls slip**,
  so there is no wall boundary layer to resolve, which takes a little blockage drag away; the
  man no-slip with wall functions and no prism layers.
- **Inlet turbulence** 10% intensity with a 0.09 m length scale, for air off a fan. In the fan
  run k and omega stay at their 10 m/s values as the inflow speeds up: the turbulence is the
  fan's, not the fall's.

### The mesh

blockMesh, 0.15 m cells across the shaft, then snappyHexMesh: 75 mm in a box round him and in
a box 3.5 m up his wake, 37.5 mm and 19 mm at his skin (4,697 faces on him), no layers.
**104,646 cells.** `checkMesh` says Mesh OK: non-orthogonality up to 45.6°, skewness up to
2.11, aspect ratio up to 4.38. The stricter `checkMesh -allGeometry -allTopology`, which Allrun
also runs, finds 4,437 concave cells from snapping and six edges where his surface on the mesh
meets itself; they are kept, and they are one reason this is not a mesh to take loads from.

The four curve runs and both clip runs share this one mesh.

## How the case got here

The case was set up by an agent on our own 16-core machine. Its first mesh had 1.46 million
cells, 9.4-19 mm at his skin and 19 mm round him, at a Courant number of 0.9. It started the
four drag-curve runs on it, timed them while they ran, and remeshed at 105 k cells with the
Courant number raised to 3. What it timed was slowed by a placement fault, not by the mesh:
`mpirun --bind-to core` had put all four runs' sixteen ranks on the same four cores, while
twelve stood idle. Moved by hand to four cores each, the same runs went twelve times faster
and finished within two minutes. The fine mesh's logs were deleted when it relaunched, so how
fast it would have run on its own cores is not known. Every run here is on the coarse mesh.
Allrun now runs the curve's runs one after another instead of side by side.

## Checks

- **The drag against the literature.** The figure skydivers quote for a belly-down fall is
  about 55 m/s (Wikipedia, "Terminal velocity", citing Huang 1998), and tunnels float belly
  flyers at about 195 km/h, 55 m/s (Wikipedia, "Vertical wind tunnel"). He is light for a
  skydiver. With his CdA of 0.415 m², 55 m/s is the terminal speed of a 77 kg flyer, and his
  62.1 kg falls at 49.4 m/s; terminal speed goes with the square root of mass over CdA. Those
  sources give no mass or CdA for their 55 m/s, so this says his drag is the right size, not
  that it is right to a few percent.
- **Is the wake frozen?** A coarse mesh at a Courant number of 3 might damp the shedding
  away. On the side plane, each write's speed was divided by its inflow, a linear trend
  taken out, and the spread over 0.4-1.3 s measured. In the wake above him (|x| < 1 m,
  0.7 < z < 4 m) it is 3.9% of the inflow in the fan run and 5.9% in the float run, against
  0.01% in the free stream below him. Both wakes move. The fan run's force on him barely
  fluctuates, though: sideways, a standard deviation of 0.0-0.8 N on means of 2-7 N in 0.1 s
  windows, against 2.0-4.5 N on 33-42 N in the float run. That is the coarse mesh's cost.
  The planes these were read from are not committed.
- **Settled means.** Over each curve run's window the force's coefficient of variation is
  0.73-0.78% and its second half 0.78-0.85% below its first: settled to about 1%, not a
  converged wake statistic.
- **The fall again from the run's own force.** Integrating m dv/dt = m g − D from the fan
  run's force history instead of the curve puts him 7.565 m down at the curve's 1.3018 s.
  Holding the last force for another 4.85 ms brings him to the fan at 1.3066 s and 11.383 m/s:
  +0.37% on the fall time and −0.09% on the impact speed. The inflow was not iterated.
- **Reproduced from a clean copy.** `--setup-only curve`, `fan` and `float` wrote the solved
  mesh byte for byte (104,646 cells) and every run's initial fields and dictionaries byte for
  byte, but for the curve runs' `turbulenceProperties`, which the solved runs have laid out on
  more lines with the same entries; the t = 0 force evaluation of both clip runs matched to
  the byte. `analyse_curve_motion.py results` on the committed force histories writes the
  drag curve, the motion table, the summary and both inlet tables byte for byte, and
  `postprocess_clip.py` on the solved force files writes both committed histories and
  summaries byte for byte.

## Results

### The drag curve

Mean drag over the second half of each steady run (`results/drag_curve.csv`), Cd on his
0.501 m² seen from below:

| updraft | Re on 1.75 m | drag | CdA | Cd | CV | second half against first |
|---:|---:|---:|---:|---:|---:|---:|
| 8 m/s | 9.2e5 | 16.03 N | 0.4162 m² | 0.830 | 0.73% | −0.78% |
| 20 m/s | 2.3e6 | 99.93 N | 0.4150 m² | 0.828 | 0.78% | −0.85% |
| 40 m/s | 4.6e6 | 399.25 N | 0.4145 m² | 0.827 | 0.77% | −0.83% |
| 55 m/s | 6.3e6 | 754.41 N | 0.4143 m² | 0.826 | 0.78% | −0.83% |

**CdA 0.415 m²** at every speed, to within 0.5%. From it (`results/motion_summary.json`):

- **Terminal speed 49.4 m/s** (178 km/h) for his 62.1 kg. That is the float run's updraft.
- **Over the 10 m/s fan he takes 1.30 s to fall the 7.62 m and reaches it at 11.4 m/s**
  (41 km/h). With no air at all he would take 1.25 s and arrive at 12.2 m/s (44 km/h).
- On the curve, the fan's air holds up 4.1% of his weight as he lets go (10 m/s relative) and
  18.8% as he reaches it (21.4 m/s relative).

### The clip runs

The air's upward force on him as a share of his weight, from every solver step
(`results/fan/` and `results/float/`, `forces_with_inlet_and_weight_share.csv`):

| | at t = 0 | first step | 0.05 s means after 0.1 s | at the fan | time-weighted mean, whole fall |
|---|---:|---:|---:|---:|---:|
| fan | 0.1% | 167% | 6.3% rising to 18.2% | 18.5% | 11.1% |
| float | 2.7% | 2,725% | 99.5-102.2% | 101.8% | 102.0% |

The first step's spike is the impulsive start, the whole domain's air set going at once
pushing on him, and the next step swings negative; both are kept in the files. After that the
fan run reads 4-6% at once, and the float run reads 110-130% for a few hundredths of a second
and settles by 0.1 s. Over the fan the air holds up 5-6% of his weight in the first 0.1 s and
18% when he reaches it, as the curve predicts. In the blast it holds 99.5-102% after the first
0.1 s: he hangs.

**So the fan's air could not have caught him.** It slows him from 12.2 to 11.4 m/s. To hold
him it would have to blow about 49 m/s, five times the generous 10 m/s used here.

## What the clip shows, and what it does not

**It shows** two shafts side by side on one 0-60 m/s colour scale, labelled "a big cooling
fan" and "a wind-tunnel blast", the side plane through him (y = 0) with moving streamlines and
his silhouette drawn over the hole he cuts in it. It is drawn in the shaft's frame, though the
solve is in his: each write's velocities have his fall speed added back, which is exact
because his frame only adds a uniform pressure gradient, and the solved window, 3 m below him
to 6 m above, is placed in the shaft at his height and moves down with him. Outside it the
shaft shows the plain updraft, and over the window's top 1.5 m its field is blended into the
updraft so no edge shows; air that passed him earlier is not drawn. The fan is drawn at the
bottom of both shafts, turning at a display rate, not an rpm.

It plays at about 5x slow motion, every third write, easing to 3x before the end, one solved
write a frame with nothing interpolated, and ends on the frame before contact, his lowest
point 0.15 m above the blades, so it loops. Each panel's number is "holds N% of his weight":
the force from the run's history averaged over the 0.05 s of flow before each update, four
updates a second of video, rounded. In the first 0.01 s it shows a dash, so the start-up spike
is not read as air holding him. The left number stops updating a second of video before the
end, on 15%, while the share rises to 18% at contact; the right ends on 101%. The numbers are
the mean force on him, which the drag check above sets against the literature, not the
fluctuations the coarse mesh may have smoothed.

**It does not show** the fan's own flow, his arms and legs off the plane (44% of the drawn
silhouette lies over solved air for that reason), the magnets, or what happens when he
arrives.

## What it cannot

- **A drawn fan.** The updraft is uniform across the shaft. A real fan's jet is uneven, swirls
  and is strongest near the blade tips; as he gets close, it would push on him unevenly. The
  last few tenths of a metre are not modelled.
- **He is fixed, and rigid.** One pose for the whole fall, no tumbling, no limbs moving. A
  skydiver steers and stabilises; a falling stuntman would not hold the box.
- **A coarse mesh**: 105 k cells, 75 mm round him, no prism layers, wall functions on a body
  whose separation lines are not fixed by sharp edges, a Courant number of 3 for a
  scale-resolving model. The drag sits where the literature puts it; the wake's detail and the
  force's fluctuations are not to be trusted, nor surface pressures or shear.
- **One mesh, one model, short windows.** No mesh study, no other turbulence model, 4 m of air
  averaged per curve point, no measurements of this figure.
- **Slip walls and an impulsive start.** The shaft's walls carry no boundary layer, and the
  whole domain starts moving at once, which is a convenient start, not a developed shaft flow.
- **A body of water's density.** 62.1 kg from his volume at 1000 kg/m³; a heavier man falls a
  little faster and needs more air to float.
- **Unclothed and bald.** A suit adds drag, and a suit cut to catch air adds a lot.
- **Not a safety finding.** It says nothing about injury, about a real fan's blades or loads,
  or whether the stunt could be done.

## Sources

- The scene: TV Tropes, "Deadly Rotary Fan" (Brandt "leaping 25 feet into a vertical shaft at
  the bottom of which is a large cooling fan", held up by "his metallic suit" and "a
  remote-controlled robot with a large magnet"): https://tvtropes.org/pmwiki/pmwiki.php/Main/DeadlyRotaryFan
- Wikipedia, "Terminal velocity" (a belly-down skydiver at about 55 m/s, citing Huang, J.,
  "Speed of a skydiver (terminal velocity)", *The Physics Factbook*, 1998):
  https://en.wikipedia.org/wiki/Terminal_velocity
- Wikipedia, "Vertical wind tunnel" (about 195 km/h, 55 m/s, for a belly-down flyer; tunnels
  run 130-300 km/h): https://en.wikipedia.org/wiki/Vertical_wind_tunnel
- ebm-papst A3G910 axial fan, 910 mm: 11,680 m³/h at 610 rpm (A3G910-AO83-01) and 13,445 m³/h
  at 640 rpm (A3G910-BG02-51), from distributors' listings (TME, SOS Electronic) as search
  results showed them; the pages themselves would not load.
- MakeHuman, CC0 assets: https://github.com/makehumancommunity/makehuman (commit
  `a8bc2d54ff0ac92e78ff71431b1023eda42bf482`)

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with
NumPy and trimesh (and PyVista, for the figure's previews and for cropping the planes).

    cd cases/fanShaftFall
    ./Allrun curve
    ./Allrun fan
    ./Allrun float

`Allrun` builds the figure into `geometry/` if it is not there (the first build downloads
about 23 MB of MakeHuman files into `~/.cache/makehuman-cc0/`), meshes the shaft once in
`runs/mesh/` (blockMesh, surfaceFeatureExtract, snappyHexMesh, checkMesh), and links that mesh
into every run. `curve` writes `runs/curve/U8` ... `U55` (`scripts/make_case.py`), solves them
one after another on 4 ranks each and runs `scripts/analyse_curve_motion.py`, which writes the
drag curve, the motion and both inlet tables to `runs/`. `fan` and `float` run the curve first
if `runs/` has none, write the run (`scripts/make_clips.py`), sample t = 0, solve on 8 ranks
writing both planes 481 times, and run `scripts/postprocess_clip.py`, which writes the force
history with the inflow and the share of his weight, refigures the fall from it, and crops
the planes to z = −3 to +6 m. `./Allrun --setup-only <stage>` stops before the solve, and for
a clip takes the curve from `results/curve/` if `runs/` has none. `./Allclean` removes `runs/`.

The solves took 164-173 s each for the curve and 205 s (`fan`) and 392 s (`float`) of wall
time, the curve's four side by side on four cores each and the clips side by side on eight.
Each clip run writes about 160 MB of planes.

`results/` holds what the runs wrote: the curve runs' force histories as OpenFOAM wrote them
(`curve/U*/force.dat`), the drag curve, the motion table and summary, and for each clip run
the force on him every step with the inflow and his weight's share, and its summary. No
fields, meshes, planes or logs.
