# Case notes and stock validation

## Physics and numerics

* Stationary motorcycle, uniform 20 m/s flow in +x, +x moving ground, symmetry side/top,
  12 x 6 x 4 m domain.
* Air: incompressible, `nu=1.5e-5 m2/s`; pressure conversion uses 1.225 kg/m3.
* Initialization: steady k-omega SST, SIMPLE, 3000 iterations. This separated flow
  plateaus rather than reaching machine-zero residuals; the stock L4 final initial
  residuals were approximately 7e-4 (Ux), 4e-3 (Uy), 1.7e-3 (Uz), 1.4e-2 (first p),
  3e-4 (omega), and 1e-3 (k). It is a settled RANS field, not a mathematically exact
  steady state.
* Transient: kOmegaSSTDDES (`useSigma true`), second-order backward time, bounded
  linear-upwind velocity, fixed dt = 1/4800 = 0.0002083333 s. Stock L4 had mean Co about
  0.041 and isolated max Co up to about 3.4; the 1.2 s run completed stably. Fixed dt is
  intentional so all geometries have exactly the same temporal filter and frame times.
* DDES warm-up 0--0.2 s; statistics 0.2--1.2 s, about 20 cycles at the expected 20 Hz.

## Mesh actually selected

The production policy in `case/config/run.conf` is L4:

| region | nominal size |
|---|---:|
| background | 125 mm |
| general bike | 31.25 mm |
| wake | 31.25 mm |
| helmet + near-wake/shear-layer box | 7.8125 mm |
| screen surface and extracted edges | 3.90625 mm |

Stock L4 has **3,983,815 cells**, 7,590 screen boundary faces and 2,873 helmet boundary
faces. The screen edge remains at the same fine size in all runs, while the fairing/bike
is much cheaper. No prism layers are used: failed layers on this open, highly intricate
OBJ created sliver cells and much worse all-geometry checks. That trades detailed wall
shear/drag accuracy for stable separated-shear-layer and pressure-fluctuation prediction.

## Refinement evidence -- important negative result

A controlled stock comparison was made; domain, geometry, screen resolution, schemes,
model, dt, initialization length, warm-up, 1.0 s sample window and metric definition were
unchanged. Only helmet and near-wake resolution changed:

| mesh | helmet / near wake | cells | helmet RMS |
|---|---:|---:|---:|
| L3 | 15.625 mm | 943,140 | 10.898 Pa |
| L4 | 7.8125 mm | 3,983,815 | **20.235 Pa** |

Evidence is retained in `validation/stock-L3`, `validation/stock-L4`, and
`validation/mesh-convergence.csv`. L3 is a completed immediately preceding local stock
run whose source dictionaries, logs and surface output were inspected and copied; L4 was
built and run in this delivered case. The L4 metric is also in
`case/results/helmet_metric.json`.

**The helmet metric has not stopped moving with refinement.** It changed by +86% when
cell count rose 4.2x. Refining again would put most of the 1.7 x 1.2 x 0.9 m near-wake box
near 3.9 mm and push this beyond the affordable scope of a short comparison clip. L4 was
therefore selected as the highest tested affordable common policy, not as a
mesh-independent answer. The stock number is useful for screening large differences and
making an identically discretized short/stock/tall ranking. It is not suitable as an
absolute buffeting prediction, and screen differences of order 9 Pa or less (the observed
L3--L4 shift) should not be claimed as resolved. Geometry-dependent discretization error
can still affect even the ranking.

The one-second window is the requested ~20 nominal cycles, not a statistical convergence
study. Sampling uncertainty is additional to the demonstrated mesh error.

## Mesh quality and geometry limitations

`checkMesh -allGeometry -allTopology` does **not** report `Mesh OK`: on stock L4 it flags
one duplicate non-baffle face from the supplied complex/open OBJ, 50 highly skew faces,
54 low-determinant cells and 42,254 concave cells among 3.98 million. Cell volumes,
openness, face pyramids and non-orthogonality pass (max non-orthogonality 69.99 degrees).
The full transient completed without divergence, but these defects are retained and stated,
not hidden behind the basic check.

As supplied, the windscreen is fused into the fairing. Consequently `bike.obj` changes
slightly with windscreen height: the tall fairing lip is about +206 mm and the short lip
about -89 mm relative to stock. This is documented in `README-geometry.txt`; it prevents a
strict screen-only geometry control.

Other deliberate economy choices: wall-modelled RANS/DDES with no layers, symmetry rather
than a crosswind/open lateral far field, fixed density/incompressible air, and no attempt at
acoustic or structural helmet response. The scalar measures aerodynamic surface-pressure
unsteadiness only.
