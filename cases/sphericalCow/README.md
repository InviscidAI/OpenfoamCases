# The spherical cow

"Assume a spherical cow" is the physics joke about models simplified until they are
useless. This case takes it literally: a cow and a sphere of exactly the same volume, each
in the same 8 m/s wind, and what the air does around each.

One OpenFOAM case, five configurations, all from one `config.json`:

    ./Allrun cow-floating       # the cow in free air          (the published clip)
    ./Allrun sphere-floating    # the equal-volume sphere      (the published clip)
    ./Allrun cow                # the cow standing on the ground
    ./Allrun sphere             # the sphere resting on the ground
    ./Allrun isolated           # the free sphere under plain SST, the model check

## The cow

The cow is **Spot**, by Keenan Crane, released by its author into the public domain. It is
a cartoon, and the cow the spherical-cow joke is usually drawn from. The unmodified mesh and
its licence statement are in `geometry/spot/`. It is closed, manifold and genus 0, and is
not repaired, smoothed or edited.

It is scaled once, uniformly, so that its height at the withers is **1.411 m**, the mean of
1,054 Holstein-Friesian cows (Int. J. Morphol. 31(1):55-63, 2013). The withers is taken as
the highest point of the back just behind the neck; `scripts/process_spot.py` records the
vertex. Nothing else was fitted, so the rest of Spot is Spot:

| | scaled Spot | Holstein mean |
|---|---:|---:|
| withers height | 1.411 m | 1.411 m |
| rump height | 1.276 m | 1.442 m |
| chest floor above ground | 0.314 m | 0.763 m |
| trunk length | 1.057 m | 1.708 m |
| head length | 1.023 m | 0.519 m |
| chest width | 1.019 m | 0.483 m |
| thorax perimeter | 3.281 m | 2.068 m |

A big head, a broad body and short legs. At this scale Spot is **1.675 m3**, about 1.7
tonnes of cow, and 2.24 m tall at the horns. A real Holstein is nearer 0.65 m3. Scaling
to a real cow's mass instead would change the size and not the picture: both bodies are
past the sphere's drag crisis either way, and nothing on screen carries a scale.

**The sphere** has Spot's volume: **1.473 m** across.

## What the clip shows, and what it does not

**It shows the wake.** A vertical slice through each body's centreline, coloured by wind
speed on one scale, with streamlines through the solved flow. The sphere leaves one big,
slow wake that breaks up and wanders. The cow leaves a broader, messier one that starts at
the head and horns, and air runs fast under its belly, between the legs.

**It prints no number.** The drag, for the record:

| floating, 8 m/s, t = 5-25 s | drag coefficient | drag |
|---|---:|---:|
| Spot (frontal torso reference, 1.438 m2) | 0.70 +/- 0.03 | 39.3 N |
| equal-volume sphere | 0.33 +/- 0.02 | 22.2 N |

The sphere carries a bit over half the cow's drag. The absolute numbers are not to be
trusted: see the model check below.

## The model

- **Free air.** Both bodies float with their centres at 3 m in an 18 x 10 x 6 m domain, clear
  of every boundary by at least 1.88 m. The floor, top and sides are symmetry planes. A
  floating cow is the joke's own "in a vacuum", near enough.
- **Wind** 8 m/s, uniform, 1% turbulence intensity. Air at nu = 1.5e-5 m2/s. The sphere's
  Reynolds number is 7.9e5, past the smooth-sphere drag crisis near 3e5, so its boundary
  layer is turbulent before it separates, which is the regime a fully turbulent model is
  built for. A real cow's hide is rough, which pushes it the same way.
- **Turbulence: k-omega SST-SAS**, `pimpleFoam`, from rest. The scale-adaptive variant of
  SST lowers its eddy viscosity where the mesh can carry unsteadiness, so a free wake is
  allowed to shed. Bounded LUST for momentum, limitedLinear for k and omega, Courant number
  at most 1.
- **Mesh.** snappyHexMesh, 0.30 m background, 0.075 m through the wake, 0.0375 m at the
  body, the same cow-sized refinement box for both. Spot: 289,463 cells, two prism layers
  over 76% of its surface. Sphere: 262,640 cells, three layers everywhere. Wall functions
  on both. Both pass `checkMesh`.
- **Output.** The vertical centreline plane and the horizontal mid-height plane, written 24
  times per second of flow from 5 to 25 s. The first 5 s is start-up.

### Why SAS, and why the bodies float

The first published-candidate runs used plain SST with the bodies on the ground. The
grounded sphere shed strongly, but only because of the ground: the same sphere in free air
under plain SST (`./Allrun isolated`) was dead steady, drag 0.2172 +/- 0.0002 and side
force +/- 0.001. SST's eddy viscosity scales with the flow, so raising the Reynolds number
does not free the wake. SAS does: the free sphere's side force swings +/- 0.09 and keeps
swinging. The grounded runs stay in the case as a record, and are described at the end.

## Model check: the sphere against Achenbach

Achenbach (J. Fluid Mech. 54, 1972) measured smooth spheres through the drag crisis. At Re
7.9e5 his curve reads about **Cd 0.13 +/- 0.01**.

| free sphere | Cd | against 0.13 |
|---|---:|---:|
| SST (`isolated`) | 0.217 | 67% high |
| SST-SAS (`sphere-floating`) | 0.332 | 156% high |

**It fails, and SAS makes it worse.** Neither model resolves the laminar-to-turbulent
transition that sets a smooth sphere's separation line, and at 3.75 cm surface cells with
wall functions neither could. Freeing the wake widened it. The drag numbers above are
therefore not measurements of anything real; what the case supports is the difference in
the shape of the two wakes.

## Settling

Judged from the forces, not the residuals. Past 5 s, both bodies' side forces oscillate
with bounded amplitude, at about 0.30 Hz (Spot) and 0.35 Hz (sphere). The mean drag moved
2.3% between the first and second halves of the 20 s window, for both. Good enough for a
picture and a rough load; not a mean converged to 1%. The sphere's shedding is slower than
the Strouhal number of about 0.2 usually quoted for spheres, which would be about 1.1 Hz
here: another thing the model does not get right.

## Limits, which are the part worth reading

- **Spot is a cartoon**, scaled at one landmark. It is not the shape, size or mass of a
  real cow, and the table above says by how much.
- **The drag is not validated.** See the Achenbach check.
- **One mesh, one model per configuration.** No mesh study. Coarse surface cells, wall
  functions, incomplete prism cover on Spot.
- **Uniform wind**, no atmospheric shear, gusts, grass or hair. Spot does not move.
- **20 s of wake** after start-up. Enough for the shedding to show, not for tight means.
- **The clip slows time 4x** and blends between the 24-per-second writes for three of every
  four video frames. The CFD is not interpolated; the display is.

## The grounded runs

`./Allrun cow`, `./Allrun sphere`: the same bodies standing on a no-slip ground, plain SST,
maximum Courant number 4, sunk 4 cm (Spot) and 7.5 cm (sphere) so the contact meshes
cleanly. The sphere's cap below the ground is 0.75% of its volume. Spot 253,197 cells, the
sphere 224,610 with no prism layers (layers at the contact failed the mesh checks).

| grounded, SST, t = 5-25 s | Cd | drag |
|---|---:|---:|
| Spot | 0.93 +/- 0.02 | 52.4 N |
| sphere | 0.65 +/- 0.17 | 43.2 N |

The ground makes the sphere shed hard, at about 1.1 Hz: its drag swings by a quarter. It is
a different flow, a sphere sitting in a boundary layer, and not the one the clip shows.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it with MPI, and Python 3 with
NumPy, Matplotlib and PyVista.

    cd cases/sphericalCow
    ./Allrun cow-floating        # and ./Allrun sphere-floating

`Allrun` scales and places Spot from `config.json` (`scripts/process_spot.py`), writes the
case into `runs/<configuration>/` (`scripts/generate_transient_case.py`), meshes it, checks
the mesh, and solves to 25 s on 8 MPI ranks. The floating sphere takes about 20 minutes.
Spot takes over an hour: its smallest cells hold the time step near 1 ms. Two at once use
16 ranks. `scripts/analyse_floating.py` and
`scripts/analyse_transient.py` write the statistics and previews to `results/`, where the
published statistics already are. `./Allclean` removes the runs and generated geometry.

The case was set up by an agent and checked by us, over a first build and a series of
corrections: a primitive-shape cow and a low-poly model were tried and dropped before
Spot, the wind went from 2 to 8 m/s when the first sphere check failed, and the model went
from SST to SAS when the free wake would not shed.
