# Codex Memory Routing Index

This is the checked-in routing index for project workflow memory. It is not
Codex's generated user-memory store. Codex agents must read this file before
case work, workflow/tooling changes, or tasks that may touch CFD process.

Use this file to decide which detailed memories to read. Keep entries short,
trigger-oriented, and cheap to scan. Do not paste full workflow bodies here.

## How To Use

1. Identify the current task's nouns, files, and workflow stage.
2. Scan `Always Recall` first.
3. Scan `Triggered Recall` for matching triggers.
4. Read every referenced memory file whose trigger matches.
5. If no trigger matches, proceed and record new discovery only if the task
   reveals a distinct reusable pattern, guard, or candidate workflow.

## Entry Format

Use one line per memory:

```text
- triggers: <comma-separated trigger words> | category: <case|guard|candidate-workflow> | file: <relative path> | recall: <why this matters>
```

Detailed memory files should use frontmatter like this:

```yaml
---
category: guard
triggers: [mesh, boundary, output]
status: active
cases: []
---
```

## Always Recall

- triggers: long-run, overnight, solver, OpenFOAM, polling, monitor, blocking-wait | category: guard | file: .codex/memory/long-run-blocking-wait-guard.md | recall: Long solver runs need active blocking waits or bounded polling; status files alone do not wake Codex.
- triggers: boundary, pressure, opening, inlet, outlet, fan, totalPressure, fixedValue, energy, unphysical, overspeed | category: guard | file: .codex/memory/boundary-energy-budget-guard.md | recall: Fixed-velocity fans and fixedValue pressure openings can do unbounded work on the fluid while mass still balances; budget the boundaries before blaming turbulence or mesh.

## Triggered Recall

- triggers: cylinder, Re3900, LES, O-grid, WALE, dynamicKEqn, OpenFOAM | category: case | file: .codex/memory/cylinder-re3900-les-case.md | recall: Paper-matched Re=3900 cylinder LES setup choices and startup stability findings.
- triggers: room, fan, ventilation, 2D, fanPressure, totalPressure, furniture, cold-start, blockMesh | category: case | file: .codex/memory/room-fan-in-out-2d-case.md | recall: 2-D room ventilation pair: why 2-D at all, block cut-outs for furniture, cold-start development window, and why the settled field had nothing to show.

## Candidate Workflow Counters

- triggers: HPC, OpenFOAM, decomposition, output, disk, MPI, production-launch | category: candidate-workflow | file: .codex/memory/candidate-openfoam-hpc-production-launch.md | recall: First observed reusable workflow for node-specific rank/output/disk tuning before long OpenFOAM MPI production runs.
- triggers: post-run, validation, forceCoeffs, probes, Strouhal, recirculation, yPlus, sampling | category: candidate-workflow | file: .codex/memory/candidate-openfoam-benchmark-wrapup.md | recall: First observed reusable workflow for clean-completion checks and benchmark metrics after long OpenFOAM runs.

- triggers: OpenFOAM, wall-resolved, wall-function, yPlus, mesh, boundary-layer, startup-gate | category: candidate-workflow | file: .codex/memory/candidate-openfoam-wall-resolved-remediation.md | recall: First observed reusable workflow for replacing inappropriate wall modeling with resolved-wall mesh/y+ startup validation.

## Retired Memories

No memories have been retired yet.
