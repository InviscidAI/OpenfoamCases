# How fast a penguin would have to go to fly

Penguins are birds that gave up flying for swimming, and their flippers are wings made for water:
short, stiff and flat. So how fast would an Adélie penguin have to go through the air, flippers held
straight out like a glider's wings, before it made as much lift as it weighs? This case answers that
with a steady 3-D run of the whole bird, flippers included, and then shows the air round the bird in
two 2-D side sections from a standing start: the bird at the speed it swims, which in air simply
falls, and the bird at the speed the 3-D run found, held level. It does not ask whether a penguin
could fly: its muscles, flipper joints and feathers could neither hold the flippers out at that speed
nor flap them in air. It asks only what speed the bird's shape would need.

    ./Allrun lift50    # 3-D, the whole bird at 50 m/s, 10 degrees nose-up, steady
    ./Allrun lift64    # 3-D, the same at 64 m/s, from lift50's fields (needs lift50)
    ./Allrun swim      # 2-D section, 2 m/s (7 km/h) and falling freely, 0-0.5 s
    ./Allrun fly       # 2-D section, 64 m/s (230 km/h) and held level, 0-0.5 s

**The result.** At a fixed 10° nose-up, the whole bird makes **29.0 N of lift at 50 m/s**, so lift
equals its weight of **47.1 N (4.8 kg)** at 50 √(47.1 / 29.0) = 63.7 m/s, rounded to **64 m/s, 230
km/h**, 32 times the 2 m/s it swims at. A second run at 64 m/s confirms it: **48.1 N, 2.1% over
the weight**. The flippers carry **72%** of the lift and the body 28%; over 81% of the upper flipper
surface the flow has separated. The flippers' lift coefficient on their own area, 0.67, sits near the
0.75 that lifting-line theory gives a flat plate of their aspect ratio (4.25) at 10°, which is why the
answer comes out above the 160-190 km/h a bird's-wing estimate gives. In the 2-D sections the flying
bird's wake sheds a vortex street at **97.5 Hz, a Strouhal number of 0.22** on its depth, while the
swimming bird drops 1.23 m in half a second under a growing swirl of stirred air. Read [What it
cannot](#what-it-cannot) before any picture from this case: **the 2-D panels are side sections with no
flippers, whose lift is not the bird's**, **the fall and the level hold are prescribed, not solved**,
and **the two sections use different turbulence models**.

## The bird

| | value | from |
|---|---|---|
| species | Adélie penguin, the classic black-backed, white-bellied penguin of the Antarctic, with the white eye-ring | |
| mass | **4.8 kg**, weight 47.1 N: the mean of adult males (5.0 ± 0.8 kg) and females (4.6 ± 0.7 kg) at Cape Crozier | Jennings et al. 2016, PLOS ONE (pmc.ncbi.nlm.nih.gov/articles/PMC4775033); Palmer Station's adults ran 2.85-4.78 kg (Palmer LTER, structural size measurements of Adélie penguins) |
| length | 0.70 m bill tip to tail tip | Wikipedia and Britannica give 70-73 cm |
| body | 0.145 m deep and 0.140 m wide at 0.30 m from the bill tip, fineness ratio 4.8 | ours, near the 4.5 usually quoted for penguins |
| bill | 40 mm long, 20 mm deep at its base | Palmer LTER: culmen 32-46 mm long, 15.5-21.5 mm deep |
| flipper | 0.205 m root to tip, root chord 65 mm, mean chord 48 mm, aspect ratio 4.25, a thin rounded-nosed section 10% thick at the root and 7% at the tip | length: Cape Crozier means 210.9 mm (males), 203.8 mm (females), Palmer 172-210 mm; aspect ratio: 4.0-4.5 for most species ("Flipping Through Penguin Flippers: An Ecomorphological Approach", SICB meeting abstract). **No source gives an Adélie flipper's width; the chord is chosen to give that aspect ratio.** |
| volume | 5.57 L, a mean density of 0.86 kg/L | measured off the drawing; penguins are near neutral in water with the air in their plumage |
| feet | tucked under the tail, not modelled | |
| swimming speed | **2.0 m/s** | Culik and Wilson (1991), "Swimming energetics and performance of instrumented Adélie penguins", J. Exp. Biol. 158, 355: birds without instruments in a 21 m canal preferred 1.9-2.1 m/s |
| posture | pitched **10° nose-up** about x = 0.30 m, flippers straight out in their chord plane, held fixed | a glider's angle, chosen before any solve and not tuned |

**The bird is drawn by us**, from those dimensions, by `scripts/penguin_geometry.py`: a body of
elliptic sections through 14 stations, two flippers lofted from a NACA 00xx thickness form, joined
into one closed surface with manifold's boolean union. It was not traced from a photograph or a scan.
The script writes `geometry/penguin.stl` (75,556 triangles, 3.8 MB, not committed; md5
`eaa1768ed745f60f295c5c7a59dda4d8`, which the script reproduces byte for byte with trimesh, SciPy,
Shapely and manifold3d), `geometry/penguin_profile.csv` (the outline in the plane of symmetry, the 2-D
section's input) and `geometry/penguin_dims.json` (its measurements); the last two are committed.

**The air** is 0 °C at sea level and 99.5 kPa: ρ = 1.269 kg/m³, ν = 1.35e-5 m²/s, incompressible (Mach
0.19 at 64 m/s).

## The 3-D runs: the flying speed

A half model of the whole bird in a box x = -7 to 14.7 m (the bill near x = 0, air along +x), y = 0 to
7.35 m with y = 0 a symmetry plane, z = -7.2 to 7.2 m; about 10 body lengths upstream, 20 behind and 10
to each side. `simpleFoam` (OpenFOAM v2512), k-ω SST with wall functions, inflow turbulence 0.5% with a
length scale of 0.049 m (7% of the body), a no-slip bird. Inlet and the far-field faces fixed at the
stream; outlet inletOutlet with p = 0. Forces are doubled for the whole bird; lift is the force along z,
drag along x.

**The surface** is the STL rotated 10° about x = 0.30 m and split into two patches: `flipper`, the
triangles of the exposed flipper band (|y| > 0.058 m, |z - 0.015| < 0.0045 m, 0.15 < x < 0.25 m in the
unrotated bird), and `body`, the rest (`scripts/make_case.py`, as the study's `setup_meshes.py`). The
blended root has some classification uncertainty.

**The mesh**: a graded background of 3 × 2 × 3 blocks (`template/lift/system/blockMeshDict`) and
`snappyHexMesh` (`template/lift/system/snappyHexMeshDict`): the body at level 3, about 2.73 mm, the
flippers at level 5, about 0.68 mm, some 70 cells across their mean chord (a measured midspan section at
y = 0.161 m has a 49.4 mm chord with 75 upper and 74 lower wall faces), refinement by distance from the
bird (level 2 within 15 mm, 1 within 50 mm), three layers on the body only, which came out at 2.68 on
average and 88% of the target thickness. **607,535 cells**, `checkMesh` OK, non-orthogonality 65.0° at
most, skewness 3.90, aspect ratio 99. Two earlier meshes, about 94,000 cells (too coarse on the
flippers) and about 875,000 (failed its quality check), were not solved.

**The numerics** at the end of the runs (`template/lift/system/`): bounded linearUpwind for U, bounded
upwind for k and ω, consistent SIMPLE with one non-orthogonal corrector, relaxation p 0.15, U 0.3, k 0.7,
ω 0.5.

**The flying speed** was found as planned before any solve: one run at 50 m/s, V_fly = 50
√(47.1 N / L₅₀), then a run at V_fly rounded to check that lift is within 3% of the weight.

| | 50 m/s | 64 m/s |
|---|---:|---:|
| iterations | 4421 | 1200, from the 50 m/s fields |
| lift, mean of the last 300 iterations | **28.998 N** | **48.104 N** |
| drag | 6.968 N | 11.418 N |
| body lift | 8.235 N | 13.645 N |
| flipper lift | 20.763 N | 34.459 N |
| flippers' share of the lift | 71.6% | **71.6%** |
| lift's range over the last 300 iterations | 0.88% | 2.31% |
| lift against the weight, 47.1 N | | **+2.13%** |
| lift coefficient on the whole bird's planform, 0.0845 m² | 0.216 | 0.219 |
| the flippers' lift on their own area, 2 × 0.00989 m² | 0.66 | 0.67 |

The 50 m/s run met its stopping rule, a range of under 1% in lift over its last 300 iterations, at
iteration 4421: V_fly = 50 √(47.1 / 28.998) = **63.72 m/s**, rounded up to 64 m/s (230.4 km/h). At 64
m/s, **81% of the sampled upper flipper surface has reversed wall shear** (at the saved field, iteration
1129 of that run, where lift was 47.59 N): the flippers are largely stalled, as a flat, thin plate of
aspect ratio 4.25 at 10° and Re ≈ 2 × 10⁵ on its chord would be.

**Is it believable?** The estimate made before any solve counted as wing the two flippers and the
strip of body between them, 0.0273 m², and gave lift equal to weight at 44-52 m/s, 160-190 km/h, with
the lift coefficients of 1.0-1.4 a gliding bird's wing reaches. The solved flippers do not reach that:
on their own area their lift coefficient is 0.67, against 2π α AR / (AR + 2) = 0.75 from lifting-line
theory for a flat plate of aspect ratio 4.25 at 10°. On the estimate's own area the whole bird's is
0.68. So the higher speed comes from the flipper being a short flat plate, not from a wrong input, and
230 km/h is believable to within what a steady RANS run of a stalled flipper can say.

## The 2-D runs: the swimming bird and the flying bird

The bird's outline in its plane of symmetry (`geometry/penguin_profile.csv`, every second point),
pitched 10° as in the 3-D runs, in a box x = -5.6 to 11.2 m and z = -5.7 to 10.6 m, one cell, 0.01 m,
deep with empty front and back. **These sections have no flippers, and they are not the bird**: a 2-D
section is an endless slab, whose lift per metre says nothing about the bird's. They show the air.

Both start impulsively: still air in the ground's frame at t = 0, which in the bird's frame is the
interior already moving at the stream. In the bird's frame:

- **fly**: the air comes at (64, 0, 0) m/s throughout. The bird is held at its height, because at 64 m/s
  its 3-D lift equals its weight; the section is not asked to hold it up.
- **swim**: the bird moves at 2.0 m/s and falls freely. Its lift at 2 m/s is (2/64)² of its weight, 0.1%,
  so in its frame the air comes at (2, 0, 9.81 t) m/s, from ahead and more and more from below, 67.8°
  from horizontal at 0.5 s; the bird has fallen 0.5 g t² = **1.226 m** by then and moved 1 m along.
  A uniform acceleration of the frame only adds a pressure gradient in incompressible flow, so no body
  force is needed: the solver's kinematic pressure carries the frame's potential, 0/p = 9.81 (10.6 - z)
  inside and on the right outlet, 0 on the top. The fall is not coupled to the air's force on the bird.

| | swim | fly |
|---|---|---|
| inflow, left and bottom | U = (2, 0, 9.81 t) m/s (`uniformFixedValue`), p `fixedFluxPressure` | U = (64, 0, 0) m/s, p zero gradient |
| outflow, right and top | U `inletOutlet`; p = 9.81 (10.6 - z) on the right, 0 on the top | U `inletOutlet`, p = 0 |
| t = 0 inside | U = (2, 0, 0), p the frame's potential | U = (64, 0, 0), p = 0 |
| turbulence | **k-ω SST**, inflow k and ω at 0.5% and 0.049 m | **k-ω SST-SAS** (`kOmegaSSTSAS`, delta `cubeRootVol`), the same inflow |
| mesh | **72,366 cells** (solved; see below) | **130,504 cells**, 67,496 of them in a 0.008 m wake box |
| ranks when solved | 4 | 8 |
| steps to 0.5 s, largest Courant number | 5,951, 0.941 | 97,433, 0.937 |
| wall time | 926 s | 11,500 s (3.2 h) plus a 463 s probe |

**The mesh** is gmsh's, from `scripts/make_case.py` (the study's `build_clipmesh.py`): 706 faces on the
bird, about 2 mm long, with seven quad layers from a 0.70 mm first cell growing by 1.18 to 10 mm; 3 mm
cells within 12 mm of it, growing to 0.5 m by 1.5 m; a 0.022 m box over the clip window (x = -0.7 to
2.8 m, z = -1 to 2.5 m); and for fly a 0.008 m wake box over x = 0.30-3.00 m, z = -0.40 to 0.25 m, from
the rear half of the body to about 3.3 body lengths behind the tail. The far field is then padded by
0.1 m at the top and the bottom, stretching only z < -1.5 and z > 3 m. `checkMesh` OK: fly's
non-orthogonality 63.2° at most and skewness 3.57; swim's 64.2° and 3.57 as solved.

**Swim's mesh does not rebuild exactly.** The same script and profile gave 72,366 cells (78,148 points)
in the cloud on 9 Nov 2026. Here gmsh 4.15.2 gives 72,578 (78,360 points), with the same 706 faces on
the bird and the same far-field patches, but its nodes near the bird are not those of the solved planes;
gmsh 4.11.1 to 4.15.1 gave 72,296-72,578, none 72,366, and the solved swim mesh itself was not kept. A
rebuilt swim is therefore a near copy of the solved run, not the run itself. Fly's 130,504-cell mesh,
built with the same script and the wake box, rebuilds with gmsh 4.15.2 to the solved run's point set
exactly (gmsh lists the points in a different order from one run to the next).

**The numerics**: `pimpleFoam`, backward in time, linearUpwind for U, limitedLinear for k and ω,
cell-limited gradients, two outer and two pressure correctors with one non-orthogonal corrector, Courant
0.75 (maxDeltaT 0.2 ms). The plane y = 0.005 m is sampled every 1 ms with U, p and vorticity over x =
-0.7 to 2.8 m and z = -1 to 1 m (fly) or 2.5 m (swim), 501 planes a run, the clip's input. In this
one-cell-deep mesh v2512 takes SAS's delta as √(V / thickness), a median of 5.3 mm in the wake, and
warns that the LES delta is not strictly applicable in 2-D.

**Why fly is SAS and swim SST.** Both were first solved with k-ω SST on the same 72,366-cell mesh. Fly's
wake then barely moved: its vorticity above 50 s⁻¹ spanned the same height at 0.25 and 0.5 s, and its
lift varied by 1.5% (standard deviation) over 0.1-0.5 s, because SST's eddy viscosity smeared the thin
wake. Fly alone was re-solved with SAS and the wake box, and now sheds. Swim was not re-solved: at a
Reynolds number 32 times lower, its picture is a leading-edge vortex that forms above the falling bird as
its wind turns broadside, which SST already resolves. **The two sections therefore differ in turbulence
model and in wake mesh.**

**The flying section's wake**, 0.1-0.5 s, per metre of section (`results/summary.txt`):

| | SAS, this case's `fly` | SST, the first fly run, not in this case |
|---|---:|---:|
| lift, mean | 823.1 N/m | 1154.0 N/m |
| lift, standard deviation | 204.7 N/m, **24.9%** of the mean | 17.4 N/m, 1.5% |
| drag, mean and standard deviation | 253.9, 25.3 N/m | 137.4, 2.9 N/m |
| strongest frequency of lift and drag | **97.5 Hz** | 80 Hz |
| Strouhal number, f × 0.145 m / 64 m/s | **0.22** | 0.18 |

The spectrum is of the force record resampled every 0.1 ms over 0.1-0.5 s, mean removed, Hann window, so
its bins are 2.5 Hz wide. Uz at three points in the wake, at x = 1, 1.5 and 2 m, peaks at 95.6 Hz on its
coarser 4 Hz bins, and the vorticity at 0.25 and 0.5 s shows alternating vortices. A Strouhal number of
0.22 is the usual value behind a blunt-tailed body. That the section's mean lift moved by 29% with the
model and the mesh is one more reason it is not used: the bird's lift is the 3-D runs'.

## What it cannot

- **The panels are 2-D side sections without flippers.** They show the air in the bird's plane of
  symmetry, with no flippers in it and no flow round the sides. The section's lift per metre is not the
  bird's and is not shown or used; the 230 km/h is the 3-D runs'.
- **The fall and the level hold are prescribed, not solved.** The swimming bird's 1.23 m is a free fall
  written into its frame, which leaves out a broadside drag estimated at up to about 4% of its weight by
  0.5 s (about 2% less fall). The flying bird holds its height because the 3-D lift equals its weight at
  64 m/s.
- **2-D shedding is more regular than a real wake.** A 2-D section sheds straight, coherent vortices in
  strict alternation, so fly's street is tidier and stronger than a real bird's wake, which breaks up in
  three dimensions; swim's swirl is probably overstated for the same reason.
- **The two 2-D runs use different turbulence models** (fly SAS on 130,504 cells with a wake box, swim
  SST on 72,366 cells), and a 2-D SAS run is outside what the model is built for.
- **A fixed angle.** 10° is held fixed. At a larger angle short of stall the speed would be somewhat
  lower; at 10° the flippers are already largely stalled.
- **One mesh, no mesh study**, and steady RANS with wall functions on a stalled flipper, so the flying
  speed is model-sensitive. The 3-D lift at 64 m/s still moved by 2.3% over its last 300 iterations.
  No transient 3-D run was made.
- **The flying run's planes after 0.010 s are interpolated in time.** A restart of the solved run at
  0.0100421 s shifted its plane clock by 42 µs, so the 1 ms planes from 0.011 to 0.499 s are linear in
  time between the solver's own samples, and the 0.500 s plane was recovered by continuing the last saved
  fields; at one plane a millisecond this does not show. The forces and the spectrum use the solver's
  own record. A run of this case straight through writes its planes on the clock.
- **Not a flying penguin.** The bird is our drawing from published sizes, with an invented flipper chord;
  no muscle, joint or feather could do this, and no flapping is modelled.

## How the case got here

The study ran on 9-11 Nov 2026, partly on a cloud workspace (4 cores) and partly on our own machine.

**The 3-D runs** were solved once, on 4 ranks: 150 iterations as a timing probe, then on to 3600 and to
4421 at 50 m/s (6,030 s in all), then 1200 iterations at 64 m/s (3,255 s). They started from the
study's `configure.py` settings, bounded limitedLinear for k and ω and relaxation of 0.3 (p) and 0.7 (U,
k, ω), and after startup overshoots in ω the schemes and relaxation were changed while the 50 m/s run
went on (its log re-reads them at iterations 438 and 705) to those in `template/lift/system/`.
`Allrun lift50` runs straight through from the final settings. It is not the solved path; a converged steady state should not depend on it, but that has not been checked here. The
64 m/s run started from the 50 m/s run's last fields as they were, with the inflow, and its k and ω,
raised to 64 m/s: its first residuals for Uy and Uz (2.5e-6, 2.4e-6) are the 50 m/s run's last ones,
and `scripts/make_case.py lift64` does the same.

**The first 2-D runs started wrong** and were discarded. They began with the air at rest in the bird's
frame, so the first pressure solve sent the inflow up through the top outlet: at 1 ms the air 0.5 m
ahead of the bird was 73% of the stream's speed and 21° off it, fly's whole plane sat at +5.3 kPa, and
swim's arriving air stayed 8-22° off until 0.3 s. Both were re-solved with the interior at the stream and
no other change to the physics or numerics. At 1 ms the mean velocity along the clip window's left, top and bottom edges is now
within 0.46% and 0.24° of the stream in swim, and within 0.7% and 0.3° in fly, whose plane's median
pressure is +30.7 Pa.

**Fly was re-solved a second time, with SAS and the wake box** (above). A first SAS run in the cloud was
lost with its workspace at 0.259 s; the same case was rebuilt here from the cloud run's dictionaries and
mesh script, checked against it (130,504 cells, settings byte for byte, the 1 ms check), and run 0-0.5 s
on 8 ranks. That run is the one in `results/`.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with NumPy; the 2-D
runs need the gmsh Python module (and swim PyVista); the 3-D runs need `geometry/penguin.stl`, which
`scripts/make_case.py` draws with `scripts/penguin_geometry.py` (trimesh, SciPy, Shapely, manifold3d,
matplotlib) if it is missing.

    cd cases/penguinFlight
    ./Allrun lift50              # [nProcs], default 4
    ./Allrun lift64              # default 4; reconstructs lift50's last iteration first
    ./Allrun swim                # default 4
    ./Allrun fly                 # default 8
    python3 scripts/extract_results.py runs results

`Allrun` writes the run into `runs/<run>/` with `scripts/make_case.py` (`template/lift/` and
`template/lift50|lift64/` for the 3-D runs, `template/swim|fly/` for the 2-D runs; the mesh, `0/` and,
for swim, the frame's pressure), checks the mesh, writes the 2-D runs' t = 0 planes
(`pimpleFoam -postProcess -time 0`), decomposes by scotch, solves, and once all four have solved writes
`results/`. `./Allrun --setup-only <run> [nProcs]` stops before the solve; `./Allclean` removes the runs.
The four runs are independent but for lift64 starting from lift50. On the machines used, lift50 took
about 1.7 h and lift64 0.9 h on 4 cores, swim 15 minutes on 4 and fly 3.2 h on 8.

The dictionaries are the solved runs' byte for byte, with two exceptions: lift50's `controlDict` is the
64 m/s run's with `endTime 4421` (the 50 m/s run's own ended in `stopAt writeNow`, the way it was
stopped), and swim's and lift50's `0/` fields are those the study's `configure.py` writes (swim's with
the corrected start), not copies of the solved runs' files, which are not kept (fly's `0/` is the
solved run's, and `configure.py` writes it byte for byte apart from the corrected start). fly's `controlDict` keeps the 48.44 ms volume-write
interval and `startFrom latestTime` of the restarted run; both are harmless from t = 0. The comments in
`snappyHexMeshDict` are the study's template's and name helper scripts that are not part of this case.

Each 2-D run writes 501 ASCII VTK planes, of the order of 1-2 GB a run, and a force row every step.
`results/` holds the summary, the 3-D force history every 10th iteration, the 2-D forces in 1 ms
windows and fly's spectrum, from `scripts/extract_results.py` on the solved runs' force records. No
fields, meshes, planes or logs.

Checked from a clean copy of the case, with no solve run, on OpenFOAM v2512 with gmsh 4.15.2:
`scripts/make_case.py` for lift50, swim and fly, then `checkMesh`. **fly**: 130,504 cells, Mesh OK,
non-orthogonality 63.2° at most, skewness 3.57, the solved mesh's point set. **swim**: 72,578 cells
against 72,366 solved (above), Mesh OK, non-orthogonality 80.3° at one face (64.2° solved), skewness
3.57. **lift50**, snappyHexMesh in serial (5.4 minutes on one core): 607,368 cells against 607,535
solved, Mesh OK; the bird's 13,675 body and 42,691 flipper faces, the layers (2.68 on average, 88% of
the target thickness), the largest non-orthogonality (64.96°), skewness (3.90) and aspect ratio (99.3)
are the solved mesh's; the 167 cells' difference is probably in the layers by the symmetry plane, which
has 12,070 faces against 12,073. Whether the solved mesh was made in serial or on 4 ranks is
not recorded. lift64 was not built, since it needs lift50's solved fields. `geometry/penguin.stl` drawn
by `scripts/penguin_geometry.py` is the solved runs' surface byte for byte. `scripts/extract_results.py`
on the solved runs' force records gives the study's own figures: 28.998 and 48.104 N, 71.6% on the
flippers, V_fly 63.72 m/s, fly's 823.1 ± 204.7 N/m and 97.5 Hz.
