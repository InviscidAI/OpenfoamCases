# HPC Migration Guards

Before launching the production benchmark on a new HPC machine, retune these
machine-dependent settings. Do not assume the local workstation values are
optimal.

## Decomposition Guard

Tune `NP`, `system/decomposeParDict`, and the MPI launcher for the target
machine before the long run.

- Run a short decomposition/solver-start benchmark on the target node type.
- Inspect `log.decomposePar` for cell balance, processor faces, and processor
  patch counts.
- Avoid over-decomposition: do not spend the run on MPI traffic instead of
  cells. Prefer fewer ranks if wall time per step does not improve.
- Record the chosen rank count and rationale in the run notes before production.

## Output-I/O Guard

Tune output frequency on the target filesystem before the long run.

- Force/probe output must remain dense enough for Strouhal and spectra.
- Field writes should remain sparse enough to avoid filesystem bottlenecks.
- Run a short test with representative force/probe and field output enabled.
- Inspect log growth, postProcessing write rate, and wall time per step.
- Update `system/controlDict` for the selected machine and record the rationale
  in the run notes before production.
