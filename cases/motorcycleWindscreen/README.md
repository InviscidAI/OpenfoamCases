# Motorcycle windscreen: does a taller screen calm the rider, or batter him?

Three OpenFOAM cases that differ in one thing — how tall the windscreen is — and measure how
much the air on the rider's helmet fluctuates.

## The question

A windscreen's top edge sheds a shear layer. Where that layer lands relative to your helmet
decides whether you sit in a calm pocket or get beaten about the head, and riders disagree
loudly about whether a taller screen fixes buffeting or causes it.

The screen's top edge is at **1.001 m** (short), **1.121 m** (stock) and **1.400 m** (tall).
The rider's helmet spans **1.001 to 1.352 m**, so the three put the shear layer's origin
below the helmet, across it, and clear above it.

## What the clip shows, and what it does not

**It shows three wakes and declares no winner.** As the screen gets taller the disturbed
region grows: the short screen leaves the flow attached with a tight wake, the stock screen
broadens it, and the tall screen throws a large turbulent region over the rider's back and
well downstream. That is geometry, and it looks the same at every mesh we tried.

**It does not rank the screens by the number**, because the number will not support it:

| case | screen edge | helmet pressure RMS | cells |
|---|---|---|---|
| short | 1.001 m | 13.11 Pa | 3,986,985 |
| stock | 1.121 m | 19.52 Pa | 3,983,815 |
| tall | 1.400 m | 19.58 Pa | 4,046,112 |

Stock and tall differ by 0.06 Pa. See the limits — that is far inside the error.

## Physics

Incompressible, isothermal, 20 m/s freestream, SST-DDES. The road is a moving wall at 20 m/s,
which is what a road does relative to a bike travelling through still air. Steady k-omega SST
initialises the field for 3000 iterations, then the transient runs at a fixed 1/4800 s step
and averages over **t = 0.2 to 1.2 s**, roughly twenty shedding cycles.

The helmet metric, defined once and computed the same way for all three:

    p_RMS = rho * areaAverage_helmet( sqrt( timeAverage( (p - timeAverage(p))^2 ) ) )

with rho = 1.225 kg/m^3. The helmet is a separate patch, split out of the bike surface by
`case/scripts/split_geometry.py`, so the average is over the thing it names.

## Limits, which are the part worth reading

**The mesh does not resolve this number, and we could not afford one that does.** Refining
the helmet and near-wake from 15.6 mm to 7.8 mm changed the stock result from **10.9 Pa to
20.2 Pa** — an 86% change for 4.2x the cells — and finer was out of reach.
`validation/mesh-convergence.csv` has both points. **Differences below about 9 Pa are not
resolved**, which is every pair in the table above.

**The ranking is not stable either.** An earlier set of runs on independently chosen meshes
put short at 18.0 Pa and stock at 10.9 — the opposite order to the table above. A quantity
whose ordering reverses when the mesh changes cannot order the screens, and more sampling
does not fix it, because this is discretization and not statistics.

**The bike is not identical between the three cases.** The windscreen in the source geometry
is fused into the fairing: 150 of its 2,069 vertices also belong to `frt-fairing`,
`frt-fairing:001` and `fairing-inner-plate`, and they reach 74% of the screen's height rather
than sitting along its base. Scaling the screen therefore carries the fairing's top lip with
it — about **+206 mm in the tall case and -89 mm in the short**. Holding those points instead
tears the screen, because faces span held and moved vertices. A clean parametric screen would
avoid both and is the right answer for a study; this is a twenty-second clip, so the coupling
is stated rather than removed.

**It is a sportbike with a tucked rider.** The buffeting argument is mostly about touring
bikes — tall screens, upright riding position, helmet high in the shear layer. This rider's
helmet sits low behind the fairing, and the non-monotonic "the mid-height screen is worst"
story belongs to the upright case, not this one.

**Mesh quality.** `checkMesh` passes cell volumes, openness, face pyramids and
non-orthogonality; `-allGeometry` flags localised skewness, some low-determinant cells and
concave cells around the triangulated geometry. The transient ran stably throughout.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it.

```sh
cd cases/motorcycleWindscreen
./Allrun stock          # or: short, tall
```

**The geometry is not in this repository.** It is derived from the bike that ships with
OpenFOAM (`$FOAM_TUTORIALS/resources/geometry/motorBike.obj.gz`), which is GPL, and this
repository is MIT — so `Allrun` builds it from your own installation on first use.
`scripts/build_geometry.py` does that: it drops the 13 duplicate `*-shadow` groups, separates
the windscreen onto its own surface so it can be meshed four times finer than the rest, and
scales it about its base to the three heights.

Everything else the run decides is in `case/config/run.conf` — refinement sizes, the time
step, the sampling window — in one file, so the three runs cannot drift apart.

`AGENT_NOTES.md` is the setup write-up from the agent that built the case, kept as it was
written.
