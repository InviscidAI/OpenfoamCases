---
category: candidate-workflow
triggers: [OpenFOAM, wall-resolved, wall-function, yPlus, mesh, boundary-layer, startup-gate]
status: active
cases: [cases/cylinderRe3900_LES]
occurrences: 1
---

# Candidate Workflow: OpenFOAM Wall-Resolved Remediation

Reusable shape first observed while correcting `cases/cylinderRe3900_LES` after
benchmark validation indicated an inappropriate turbulent wall function on a
laminar/transitional separating boundary layer. Keep this as a candidate until
it recurs in three separate cases or tasks.

## Intended Promotion Target

Likely `subagent`, not an orchestrator skill. This is an isolated remediation
unit for one suspected wall-treatment defect inside a larger case investigation.
It can be short or mechanical in parts; its value is that inputs, outputs, and
acceptance checks are crisp.

## Subagent Contract

Inputs:

- Case path and current wall boundary-condition files.
- Evidence that wall treatment or near-wall resolution is suspect.
- Mesh generator or mesh-control files.
- Existing y+ or wall-shear estimate, target y+ range, and startup gate.

Outputs:

- Proposed wall-treatment change and mesh-spacing change, with y+ scaling
  rationale.
- Fresh-start/stale-output handling plan.
- `checkMesh` audit after remeshing.
- Measured y+ and stability result from the bounded startup proof.

Completion signal:

- Success: corrected wall treatment is applied, mesh passes quality gates, run
  clears startup gate, and measured y+ is inside the intended resolved-wall
  range.
- Failure: physics check rejects the wall-treatment premise, mesh quality fails,
  y+ misses the target materially, solver destabilizes, or stale outputs cannot
  be isolated.

## Candidate Inputs

- A completed or failed OpenFOAM run with validation evidence pointing to wall
  treatment, separation, or near-wall resolution as a likely cause.
- Current wall boundary conditions, SGS/RANS model settings, and mesh generator
  or mesh controls.
- Prior y+ output or another wall-shear estimate for scaling the corrected
  first wall-normal spacing.
- A startup/stability gate and y+ acceptance target for the corrected run.

## Observed Steps

1. Confirm the physics of the wall layer before changing numerics; avoid
   turbulent wall functions when the relevant boundary layer is laminar or
   transitional before separation.
2. Remove wall-function eddy-viscosity behavior at the affected wall, e.g.
   change cylinder `nut` to `fixedValue uniform 0` and initialize `nut` cleanly.
3. Retune mesh spacing from y+ evidence instead of blindly refining. For the
   cylinder case, scaling the old max y+ from about 16 at `dy1 ~= 0.0417D`
   selected `dy1 ~= 0.00255D`, predicted max y+ near 1, and preserved the same
   4.87M-cell budget by increasing radial clustering.
4. Force fresh-start semantics and archive stale outputs before relaunching so
   corrected fields and function-object data cannot mix with invalid prior-run
   artifacts.
5. Regenerate the mesh, run `checkMesh`, and audit quality metrics after the
   spacing change; do not assume clustering is harmless.
6. Launch a bounded startup proof with active polling to a case-specific gate,
   and check measured y+ from the `yPlus` function object as soon as a write is
   available.
7. Record whether measured y+ confirms the design target and whether the solver
   remains bounded past the initial startup/ramp.

## Evidence From cylinderRe3900_LES

- The wall-function baseline completed cleanly but failed validation: `St ~=
  0.183`, recirculation length about `0.6D` behind the rear surface, high drag,
  and high coherent lift.
- Diagnosis found the mesh/wall setup used `nutUSpaldingWallFunction` despite a
  laminar/transitional upstream cylinder boundary layer. The old first
  wall-normal spacing was about `0.0417D` and final y+ reached about 16.
- Correction changed `0/nut` to `fixedValue uniform 0`, set initial `nut` to
  zero, retuned `benchmark-5m` radial `stretch` to `4.6`, and kept the same
  `576 x 176 x 48` cell count.
- The regenerated mesh passed `checkMesh` with max aspect ratio `26.99`, max
  non-orthogonality `44.66`, max skewness `1.15`, min determinant `0.0218`, and
  `Mesh OK`.
- The corrected run was actively polled past startup to `t=10.203` with no
  fatal signatures. Measured cylinder y+ was `0.0345/1.486/0.661` at `t=5.001`
  and `0.0138/1.342/0.594` at `t=9.999` for min/max/average.

## Reusable Lessons To Recheck

- A y+ value in the wall-function-friendly range is not automatically correct;
  first decide whether the local boundary layer physics warrants a wall model.
- Scaling old y+ by proposed first-cell spacing is a useful first estimate, but
  measured y+ after the corrected launch remains the acceptance check because
  wall shear can change with the corrected wall treatment.
- Mesh clustering can preserve total cell count, but it must be followed by
  `checkMesh` because aspect ratio, volume ratio, and determinant can move
  substantially.
- Ignored OpenFOAM initial fields such as `0/nut` may carry important workspace
  changes that are not visible in `git status`.

## Promotion Criteria

Promote only after this remediation pattern recurs in at least three cases or
workflow tasks, preferably including one non-cylinder case and one case where the
corrected wall treatment changes the y+ target materially.
