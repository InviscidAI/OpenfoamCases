# The OIIA cat, spinning

The spinning cat of the "OIIA" meme, taken literally: the cat turning on a floor at the
meme's rate, in a room of still air, from rest, and the air it stirs up.

One case, solved twice:

    ./Allrun long     # 0-10 s from rest, the planes written every 1/48 s
    ./Allrun clip     # 0-3.33 s from rest, the planes every 1/144 s: the clip is made from this

## The cat

The cat is **"Oiiaioooooiai Cat" by Zhuier**,
[sketchfab.com/3d-models/oiiaioooooiai-cat-30d27bf7fb224849b76e208a6eccdb36](https://sketchfab.com/3d-models/oiiaioooooiai-cat-30d27bf7fb224849b76e208a6eccdb36),
licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). `geometry/cat_spin.stl`
is our change of it, and `NOTICE` says so:

- **posed** as it spins: the model's spinning shape key at 1, which its animation holds while
  it turns, Z up, feet at z = 0, in metres as the model gives them: 0.27 x 0.43 x 0.31 m and
  16.0 litres;
- **remeshed** as one closed surface, because the original is 113 open pieces: voxel-remeshed
  at 4 mm and decimated to 64,000 faces, in Blender 4.2.3.

The original model, its animation and its texture are not here. The clip draws the cat from
the textured original; the solve only ever saw this surface.

**The spin rate is the meme's.** The model's animation turns the cat about the vertical at
3.9 revolutions a second on average (3.6 to 4.1, one way, counterclockwise seen from above),
read from its rotation keys, from rest to full rate at once, with a bob of about 5 cm. Here
the cat turns at a steady **24.5 rad/s** (3.9 rev/s) counterclockwise from above, from rest
to full rate at t = 0, and does not bob.

## The model

**The room.** A box 4 m square and 1.6 m tall, the cat standing at its centre. The floor is
a no-slip wall; the four sides and the top are open to still air at zero pressure, so air may
cross them either way. The floor is 5 mm below the cat's feet: the cat does not touch it,
and the gap is meshed finely (below).

**The cat turns with its own mesh.** The cells within 0.38 m of the axis, from below the floor
to 0.45 m up (a cylinder from `scripts/make_ami.py`), turn as a solid body with the cat, and
meet the still mesh outside through a sliding interface (`cyclicAMI`). The cat's surface is
a wall moving with the cells round it.

**Air:** `pimpleFoam`, incompressible, nu 1.5e-5 m2/s, k-omega SST-SAS, so the larger eddies
the cat sheds are resolved rather than averaged. First-order Euler in time, linear-upwind
convection, three PIMPLE outer correctors. An adaptive time step with a Courant number up to
4.0 and no step longer than 1 ms. 16 MPI ranks.

**Mesh:** snappyHexMesh from a 0.2 m background: 12.5 mm cells in the turning cylinder and on
the interface, 6-12.5 mm on the cat, 6 mm along its feature edges and in the 3.5 cm next to
the floor round its feet, and 25 mm and 50 mm out to 0.7 m and 1.2 m from the axis. 299,476
cells. `checkMesh` reports "Mesh OK" (non-orthogonality up to 70.0 degrees, skewness up to
3.61). The stricter `-allGeometry -allTopology` fails three checks: 31 faces with poor
face-tets, 133 low-determinant cells and 5,451 concave cells, at the cat's cut cells.

**Recorded:** two planes of velocity, the vertical one through the axis (x = 0) and a
horizontal one at the cat's head height (z = 0.20 m); the torque on the cat; and the kinetic
energy of the air in the box. Every 1/48 s in `long`, every 1/144 s in `clip`.

## How it was run

The case was set up and run by an agent, and checked by us from its planes and logs.

**The Courant limit was raised during the first attempt.** The agent started `long` with a
Courant limit of 0.8, raised it to 2.0 about ten minutes in, and to 4.0 about ten minutes
after that, to make 10 s affordable; nothing here tests whether 4.0 changes the answer.
That attempt then stalled, not on the physics: the solver was waiting on its own log output,
which went through a terminal that was read only every 30 s or so. It was stopped, and `long`
was **restarted from t = 0** with the settings as the agent had left them (Courant 4.0, 1 ms)
and its output going straight to a file, as `Allrun` does. So the 0-10 s solve here ran at
Courant 4.0 throughout. It ended at 10 s after 19,749 steps and 3.2 hours on 16 ranks. On
its last steps the largest Courant number was 2.2 and the sliding interface's weights summed
to 1.003 and 1.001 on its two sides.

**`clip` is the same case solved again** for a slower clip, with three settings changed and
nothing else: the end time (3.33 s), the field writes, and every recorded interval, 1/48 s
to 1/144 s, so the cat turns 9.75 degrees between writes. It ran 6,399 steps in 72 minutes.
Writing three times as often makes the solver take different time steps from the first
write on, so the two runs differ in detail: the side plane's velocity differs by an RMS of
0.002 m/s at 1/48 s and 0.5-0.6 m/s from 2 s, against an RMS speed of about 1.1 m/s, as the
shed eddies go their own way. In bulk they agree: the box's kinetic energy within 1.6% in
every third of a second, and the torque on the cat within its own fluctuation, 0.041-0.056 N m
in both.

A clean copy rebuilt both runs' mesh and wrote their dictionaries and initial fields exactly
as solved. Only the split of the mesh across the 16 ranks differs, because the partitioner
does not give the same split twice on this machine.

## Results

From `long`, 0-10 s, written by the scripts in `scripts/` to `results/`:

**The cat works as a centrifugal pump on the floor.** Air sinks onto it from above and leaves
along the floor. Over the last second, on the vertical plane (`results/swirl_side.txt`), air
comes down at 0.07 m/s at 1-1.6 m up and at 0.2-0.3 m/s just above the head near the axis,
and in the 5 cm above the floor it flows outward at 1.2-1.3 m/s 0.32-0.39 m from the axis,
about 0.9 m/s at 0.55 m and 0.4 m/s at 1.15 m.

**About 180 litres a second leave along the floor.** The outward radial velocity round the
cylinder 0.5 m from the axis gives 175 L/s for the mean profile over the last second and
179 L/s as the mean of each write's figure (`results/outflow.txt`); every half-second write
from 0.5 s on lies between 133 and 230 L/s. The outflow fills a layer 8 to 17 cm deep, its
fastest air, about 1 m/s, 2 cm above the floor. The net flow through the same cylinder swings
between -86 and +68 L/s from write to write: the plane gives it on only two lines and the
flow is not axisymmetric, so that figure carries no weight.

**The swirl stays with the cat.** At head height (`results/swirl_profile.txt`), the air
turning with the cat lies within about 0.3 m of the axis, at 1.1-2.1 m/s against the cat's
own 2-6 m/s there. It falls under 0.1 m/s beyond 0.39 m in the first second and beyond
0.34 m in the last, the same picture at 0-1 s and at 9-10 s.
Beyond the cat, the air at that height flows inward at about 0.1 m/s, so it brings no swirl
with it. Along the floor the jet carries some swirl out, 0.35-0.55 m/s at 0.3-0.46 m and down
to 0.1 m/s by 0.9 m. The sliding interface at 0.38 m does not hold the swirl in: at the floor
the swirl crosses it smoothly.

**It has not settled by 10 s.** The kinetic energy of the air in the box rises from 0.413 J at
6 s to 0.438 J at 9 s and 0.452 J at 10 s (`results/survey.txt`). At head height the farthest
air moving faster than 0.2 m/s is 0.4 m from the axis at the first write, 0.9 m at 1 s, 1.4 m
at 5 s and 1.7 m at 10 s, still moving out. Seen from above that front is somewhat octagonal,
probably the refinement cylinders laid on a square grid.

## What the clip shows, and what it does not

**It shows** the first 3.33 s of `clip` at 6x slow motion, from rest: the vertical plane
through the axis and the plane at head height seen from above, each 2 m wide, coloured by
air speed on one scale from 0 to 1.5 m/s, with streamlines, and the cat drawn from the
textured model at its solved angle. The air turning with the cat, which reaches 2-4 m/s, is
at the top of the scale.

**It does not show** the 10 s run, the flow settling (it does not settle in 10 s either), or
any number.

## What it cannot say

- **Nothing to check it against.** There is no measurement of a spinning cat, or of anything
  shaped like one, to compare with. That the flow is a floor pump, inflow at head height and
  outflow along the floor, is what a body spinning on a floor does, and no setting explains
  it otherwise; it was not tuned.
- **One mesh, one time step limit, one model.** No mesh study, no Courant study (4.0 was
  chosen for cost, mid-run), no turbulence-model study. A Courant number of 4 and 12.5 mm
  cells round the cat resolve only the larger eddies; the details of the shed flow differ
  between two runs of the same case, as above.
- **A rigid cat at a steady rate.** The animated cat changes rate between 3.6 and 4.1 rev/s
  and bobs; this one turns at 3.9 rev/s, starts at full rate, and stands 5 mm off the floor,
  a gap about one cell deep that a cat on the floor would close.
- **A small room, open at 2 m.** The open sides are 2 m from the axis and the top 1.6 m above
  the floor. By 10 s the stirred air reaches 1.7 m out; nothing here tests whether the
  boundaries shape the last seconds of `long`. The first 3.33 s, which the clip shows, stay
  well inside: from above, no air beyond 1.2 m moves faster than 0.11 m/s.
- **Ten seconds,** not settled.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with
NumPy, SciPy and PyVista for the scripts.

    cd cases/spinningCat
    ./Allrun long                   # or clip; ./Allrun --setup-only long meshes and stops
    python3 scripts/outflow.py runs/long > results/outflow.txt
    python3 scripts/survey.py runs/long > results/survey.txt
    python3 scripts/swirl_profile.py runs/long > results/swirl_profile.txt
    python3 scripts/swirl_side.py runs/long > results/swirl_side.txt

`Allrun` writes `runs/<run>/` from `template/` and `geometry/cat_spin.stl`, meshes it (about
1.5 minutes), decomposes it and solves on 16 ranks; a second argument sets another rank
count. `long` took 3.2 hours here and `clip` 72 minutes. The scripts read the planes and
monitors in `postProcessing/`; the solver writes the planes as VTK. `./Allclean` removes the
runs.
