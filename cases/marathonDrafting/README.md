# Running alone, or behind a pacer

Elite marathoners run world-record attempts tucked in behind pacemakers, and how much that
helps is an old argument. This case puts one runner at women's world-record marathon pace
through the air three ways, and measures the air resistance on her:

    ./Allrun alone       # the runner on her own
    ./Allrun behind      # one pacer directly ahead, 1.3 m hip to hip      (the published clip)
    ./Allrun pair        # two pacers side by side ahead, 1.3 m axial       (the published clip)

All three are in the published clip, with the drag on her read live from each run.

## The runners

Two figures built from [MakeHuman](https://github.com/makehumancommunity/makehuman)'s
assets (base mesh, targets, skeleton and skin weights), which the project releases under
CC0; `geometry/README.md` has the commit, every setting and every check, and
`geometry/LICENSE.ASSETS.md` the licence. They were posed by our own script, not exported
from the MakeHuman application.

| | runner | pacer |
|---|---:|---:|
| standing height | 1.650 m | 1.750 m |
| frontal area | 0.384 m2 | 0.441 m2 |
| volume | 0.050 m3 | 0.061 m3 |

Both hold one mid-stride pose: right foot down, left foot back and up, arms swinging
opposite. Closed, manifold, no self-intersections, 50,000 triangles each, unclothed and
bald.

**They stand still.** The literature does the same: a static figure in a running pose over
a ground that moves at the running speed. Schickhofer & Hanson (2021, below) cite Crouch et
al. (2016) for limb motion changing a cyclist's drag only slightly, and Inoue et al. (2016)
for about 10% more drag on a runner over a moving belt than over a still floor.

## The model

- **Speed 5.41 m/s**, the women's marathon world record (2:09:56). Air at nu =
  1.5e-5 m2/s; Reynolds number 6.0e5 on the runner's height.
- **Runner-fixed frame.** The wind blows from +x; the ground is a wall moving with it. The
  domain runs 4 m upstream of the runner and 7 m downstream, 6 m wide, 3.5 m tall, with
  symmetry sides and top. Blockage about 2% for one figure, 6% for three.
- **Placement.** Each figure's origin is the centre of its hip joints. The pacer is 1.3 m
  ahead, on the same line; the pair is 1.3 m ahead at y = +/-0.46 m, about 0.3 m between
  shoulders. Both spacings are Polidori et al.'s, taken from Berlin 2019. Every figure is
  lifted 5 mm so the grounded heel meshes cleanly.
- **Mesh.** snappyHexMesh, 0.20 m background, 0.05 m around the bodies, 0.025 m through the
  wake, 12.5 mm at the skin, no prism layers, wall functions. 0.80 M cells alone, 0.84 M
  behind, 0.88 M for the pair; the runner's surface is the same 8,114 faces in all three.
  `checkMesh -allGeometry -allTopology` (which Allrun runs) flags one face slightly over
  the default skewness limit (4.03 against 4), 19 cells with a small determinant and
  24,321 concave cells, the last two typical of snappyHexMesh's cut cells; no negative
  volumes. A clean copy rebuilt the "behind" mesh to the same 841,668 cells.
- **Turbulence: k-omega SST-SAS**, `pimpleFoam`, bounded LUST for momentum, limitedLinear
  for k and omega, backward in time, Courant number 1. The wind is switched on at t = 0
  and the run goes to 4 s; both sampled planes (horizontal at 1.05 m, vertical along the
  centreline) are written 120 times per second of flow.

### Why SAS

The first build used plain SST. It gave the lone drag closest to the literature, but
after about 2 s every wake was a smooth, steady stripe: the model's eddy viscosity damped
the unsteadiness out. SAS lets the wakes shed and break up, which is what a runner's wake
does, at the cost of a lone drag 12% higher. Both are reported below.

## Results

Drag on the runner and the pacers, mean over the settled window 2.5-4.0 s, coefficients on
the runner's 0.384 m2:

| | Cd | drag | swing (1 SD) | against running alone |
|---|---:|---:|---:|---:|
| runner alone | 0.80 | 5.49 N | 0.24 N | |
| runner behind one pacer | 0.47 | 3.25 N | 0.30 N | **41% less** |
| that pacer | 0.80 | 5.51 N | 0.22 N | |
| runner behind two pacers | 0.70 | 4.84 N | 0.31 N | **12% less** |
| the two pacers | 0.89, 0.88 | 6.15, 6.03 N | 0.14, 0.13 N | |

The two halves of the window agree within 3.3% for every runner. "Settled" means bounded,
not steady: SAS keeps the forces moving, and the window is short.

**Two pacers side by side shelter her less than one.** She runs in line with the gap
between them, and the air squeezed through that gap reaches her faster than open air
would. Their wakes pass either side of her.

### Plain SST, for the record

| runner | SST | SST-SAS |
|---|---:|---:|
| alone | 4.86 N | 5.49 N |
| behind one pacer | 2.56 N (47% less) | 3.25 N (41% less) |

## Against the literature

Schickhofer & Hanson, *Aerodynamic effects and performance improvements of running in
drafting formations*, J. Biomech. 122 (2021) 110457 (arXiv 2104.11976): a static 1.65 m
female runner model, frontal area 0.44 m2, moving ground, SST steady RANS on 40-107
million cells with y+ about 1.

- **Alone.** Their 6.52 N at 5.83 m/s, scaled to this speed and this runner's frontal
  area, is 4.90 N. SST here gives 4.86 N (1% low), SAS 5.49 N (12% high). Agreement this
  close at a hundredth of their cell count is partly luck.
- **One pacer ahead.** They find 70% less drag at 1.2 m. This case finds 41% at 1.3 m
  (47% under plain SST). The direction holds; the size does not. A coarse wake with no
  prism layers mixes the pacer's slow air back up faster than theirs.
- **Wake.** Theirs ends about 1.1 m behind the runner (negative total pressure). Here the
  centreline speed stays below half the wind speed for 1.4 m (plain SST); the two
  measures are not the same.

## What the clip shows, and what it does not

**It shows** the horizontal section at torso height from above, wind from the right, from
the moment the wind starts, at 5x slow motion, with the bodies drawn as grey mannequins
over the holes they cut in the section. The number on each strip is the drag on her as
the solve computed it, the mean over the last 0.05 s of flow, updated four times a
second of video.

**It does not show** the legs and arms moving, or anything below or above the section.

## Limits, which are the part worth reading

- **Less shelter than the literature finds.** 41% against their 70% behind one pacer. The
  size of the saving is the number most likely to move with a finer mesh.
- **Static figures.** No swinging limbs, no stride; one moment of the gait for the whole
  run.
- **No clothing or hair**, a smaller frontal area than the literature runner, and no
  shoes.
- **One mesh, one model.** No mesh study; wall functions without prism layers on a
  surface where separation is not fixed by sharp edges.
- **Four seconds of flow**, 1.5 s of it averaged. Enough for the shelter to show, not for
  tight means or shedding frequencies.
- **One pace, one spacing, still air.** No crosswind, which in a race moves the best place
  to stand.
- **The clip runs 5x slower than real time**, one frame per write; nothing is interpolated.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with
NumPy and pandas.

    cd cases/marathonDrafting
    ./Allrun behind

`Allrun` writes the case into `runs/<configuration>/` (`scripts/makeCase.py`, from
`config.sh`), places the figures, meshes with snappyHexMesh, checks the mesh, and solves
to 4 s on 8 MPI ranks; it then adds the t = 0 planes. Each run took 2.6-2.9 hours with
all three going at once. `python3 scripts/analyse_sas.py` writes the drag statistics to
`results/summary.json`, where the published ones already are. `./Allclean` removes the
runs.

The case was set up by an agent and checked by us, over a build and one correction: the
first build ran plain SST, whose wakes froze, and wrote its planes 25 times per second of
flow, too few for a clip.
