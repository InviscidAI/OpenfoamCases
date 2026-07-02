---
category: candidate-workflow
triggers: [post-run, validation, forceCoeffs, probes, Strouhal, recirculation, yPlus, sampling]
status: active
cases: [cases/cylinderRe3900_LES]
occurrences: 1
---

# Candidate Workflow: OpenFOAM Benchmark Run Wrap-Up

Reusable shape observed after the overnight `cases/cylinderRe3900_LES` production run.
Keep this as a candidate until it recurs in three separate cases or tasks.

## Candidate Inputs

- Completed OpenFOAM solver log and `run.status`.
- Function-object outputs such as `forceCoeffs`, `probes`, and `yPlus`.
- Final averaged fields when recirculation length or mean-flow metrics are required.
- Validation targets and the intended statistics window.

## Observed Steps

1. Confirm solver completion: no live workers, final `End`, finalising parallel run marker, final simulated time, and final `ClockTime`.
2. Scan fatal signatures with runtime patterns, avoiding false positives from normal `trapFpe` startup text.
3. Confirm retained field times and disk usage match output and `purgeWrite` expectations.
4. Parse force coefficients over the intended statistics window; report means, ranges, RMS/std, and spectral or zero-crossing Strouhal estimates.
5. Parse probes over the same window to cross-check shedding frequency and wake behavior.
6. Sample final averaged fields for spatial validation metrics, such as mean centerline reattachment length.
7. Summarize final `yPlus` and wall-resolution statistics.
8. Write compact analysis artifacts to `tmp/` and record the validation outcome in case memory.

## Evidence From cylinderRe3900_LES

- The run completed at `t=399.99899999872662` with `ClockTime = 32417 s` and no strict fatal signatures.
- `forceCoeffs` and probe samples over `t >= 150` gave `St ~= 0.183`, below the target near 0.208.
- Final `UMean` centerline sampling found reattachment about 0.589D downstream of the rear surface, far short of the 1.5-1.6D target.
- The run was therefore a clean numerical completion but a failed benchmark validation baseline.

## Reusable Lessons To Recheck

- For parallel `postProcess`, use absolute `-dict` paths because relative paths can resolve under `processor*/`.
- A temporary postProcess dictionary needs a `FoamFile` header and a `functions { ... }` wrapper for configured function objects.
- Use `-fields '(UMean)'` or equivalent when sampling fields that are not otherwise registered by the postProcess run.
- Parallel sampled-set output can duplicate points at processor boundaries; de-duplicate or average identical coordinates before zero-crossing analysis.

## Promotion Criteria

Promote only after post-run validation wrap-up recurs in at least three cases or tasks and the common metrics/field-sampling steps stabilize enough to justify reusable code or a skill.
