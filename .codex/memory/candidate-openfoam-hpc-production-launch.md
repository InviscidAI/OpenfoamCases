---
category: candidate-workflow
triggers: [HPC, OpenFOAM, decomposition, output, disk, MPI, production-launch]
status: active
cases: [cases/cylinderRe3900_LES]
occurrences: 2
---

# Candidate Workflow: OpenFOAM HPC Production Launch Tuning

Reusable shape observed in `cases/cylinderRe3900_LES` on the GCP H4D node.
Keep this as a candidate until it recurs in three separate cases or tasks.

## Intended Promotion Target

Likely `subagent`, not an orchestrator skill. This unit is isolated around
pre-launch audit, decomposition/output tuning, launch, and bounded startup
polling. It can be called from a larger case-level orchestrator after the case
physics and dictionaries are prepared.

## Subagent Contract

Inputs:

- Case path and OpenFOAM environment setup command.
- Desired rank count or rank-candidate list.
- Startup gate, such as target time, fatal-signature rules, and y+/force/probe
  checks if applicable.
- Output and disk policy: write interval, function-object cadence, purge policy,
  and available disk budget.

Outputs:

- Updated or verified `decomposeParDict` and launch-relevant dictionaries.
- Mesh/decomposition audit summary.
- Started or deliberately not-started run, with `run.pid`, `run.status`, solver
  log path, and latest status.
- Pass/fail result for the startup gate.

Completion signal:

- Success: run is live or completed, startup gate is satisfied, and strict fatal
  scan is clean.
- Failure: mesh/decomposition/output audit fails, launch fails, fatal signature
  appears, solver exits early, or the bounded polling timeout is reached.

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
- Second occurrence on 2026-07-02: after wall-treatment remediation in the same
  cylinder case, stale prior outputs were archived, the regenerated mesh passed
  `checkMesh`, a 192-rank Scotch decomposition was accepted at about 2.3% max
  cell imbalance, and the detached MPI run was actively polled to `t=10.203`
  with no fatal signatures.

## Reusable Lessons To Recheck

- OpenFOAM bashrc can be incompatible with `set -u`; source it before strict shell mode or avoid strict mode in launch wrappers.
- The MPI launcher may show as `prterun` rather than `mpirun`; checking `pimpleFoam` worker count is more robust than only `pgrep mpirun`.
- Runtime markers such as `run.pid` and `run.status` should be ignored, not committed.
- Before relaunching a corrected case in-place, archive stale `processor*`,
  `postProcessing`, old mesh, and old logs/status so fresh output cannot append
  to or be mistaken for invalid prior-run artifacts.

## Promotion Criteria

Promote only after this launch-tuning pattern recurs in at least three cases or tasks, ideally with one non-cylinder case and one different node shape.
