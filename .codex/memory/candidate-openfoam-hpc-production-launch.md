---
category: candidate-workflow
triggers: [HPC, OpenFOAM, decomposition, output, disk, MPI, production-launch]
status: active
cases: [cases/cylinderRe3900_LES]
occurrences: 1
---

# Candidate Workflow: OpenFOAM HPC Production Launch Tuning

Reusable shape observed in `cases/cylinderRe3900_LES` on the GCP H4D node.
Keep this as a candidate until it recurs in three separate cases or tasks.

## Candidate Inputs

- A decomposable OpenFOAM case with a known mesh and production `controlDict`.
- Target node CPU topology and available disk space.
- Validation or startup gate for bounded polling after launch.
- Case-specific output requirements for fields, probes, forces, and averages.

## Observed Steps

1. Load project memory and guards before touching dictionaries or launching MPI.
2. Check for existing solver/MPI processes outside the sandbox before launching.
3. Confirm OpenFOAM environment, MPI launcher behavior, node core count, and disk.
4. Validate mesh quality on the target setup before benchmarking rank counts.
5. Benchmark a small set of plausible rank counts with a short temporary `endTime`, restoring production dictionaries afterward.
6. Tune `numberOfSubdomains`, field write interval, function-object cadence, and `purgeWrite` from measured performance and disk estimates.
7. Re-run final `decomposePar -force`, launch detached with a persistent session, and write `run.pid`, `log.launch`, solver log, and `run.status`.
8. Actively poll until the case-specific startup gate is satisfied; leave status files but do not rely on them to wake Codex.

## Evidence From cylinderRe3900_LES

- 48/96/192-rank startup benchmarks gave about 14.5 s, 8.5 s, and 5.3 s for the short solve; 192 ranks was selected.
- Final 192-rank decomposition balance was acceptable: max cells were about 1.42% above average.
- Field writes every 5 D/U with `purgeWrite 2` and force/probe writes every 5 timesteps kept disk use well inside the 256 GB installed disk.
- `setsid -f` was needed for a detached run that survived the command runner; simple background jobs exited.

## Reusable Lessons To Recheck

- OpenFOAM bashrc can be incompatible with `set -u`; source it before strict shell mode or avoid strict mode in launch wrappers.
- The MPI launcher may show as `prterun` rather than `mpirun`; checking `pimpleFoam` worker count is more robust than only `pgrep mpirun`.
- Runtime markers such as `run.pid` and `run.status` should be ignored, not committed.

## Promotion Criteria

Promote only after this launch-tuning pattern recurs in at least three cases or tasks, ideally with one non-cylinder case and one different node shape.
