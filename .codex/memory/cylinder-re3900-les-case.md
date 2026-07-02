---
category: case
triggers: [cylinder, Re3900, LES, O-grid, WALE, dynamicKEqn, OpenFOAM]
status: active
cases: [cases/cylinderRe3900_LES]
---

# Re 3900 Cylinder LES Case Notes

Case path: `cases/cylinderRe3900_LES`.

Reference: Parnaudeau et al., Physics of Fluids 20, 085101 (2008).

Setup choices:

- Paper-matched domain: `20D x 20D x piD`.
- Scaling: `D = 1`, `Uinf = 1`, `nu = 1/3900`.
- Mesh: generated pure-hex O-grid. The startup preset is
  `512 x 128 x 64 = 4.19M` cells. The benchmark preset is
  `576 x 176 x 48 = 4.87M` cells to keep the paper's `Lz = piD`, spanwise
  count, and statistics window while staying near the preferred 5M-cell budget.
- Numerics: central `Gauss linear` velocity convection and off-centered
  `CrankNicolson 0.9` time integration for startup damping. Pure
  `CrankNicolson 1.0` produced strong odd-even force oscillations.
- Startup: inlet ramp from rest to `Uinf = 1` over `5 D/U`.

Observed during setup:

- An earlier `GAMG` pressure solve failed in the GAMG coarsest-level PCG path
  during the first pressure solve. A controlled scratch test on 2026-07-01 with
  the current mesh/dictionaries completed one serial step and one 24-rank
  parallel step using `GAMG` without `pRefCell/pRefValue`; the case already has
  pressure pinned by `p` fixedValue at `outlet`. Treat the earlier crash as not
  caused by pressure pinning unless reproduced with the current dictionary.
- `dynamicKEqn` was the preferred SGS model but became unstable during
  full-mesh startup; transported SGS `k` blew up and collapsed `deltaT`.
- WALE removed the transported-`k` failure mode and, with the inlet ramp,
  produced a stable startup smoke test, but the longer overnight run also
  failed early.
- Direct `potentialFoam` initialization produced unusable results on the
  O-grid/cyclic setup and should not be used without further diagnosis.
- Overnight ramped WALE run failed at `t ~= 0.043074836` with an FPE in
  `Foam::pow3` inside `libincompressibleTurbulenceModels`; force and probe
  outputs grew to nonphysical magnitudes before the crash. Treat all generated
  data from that run as failed-startup diagnostics, not CFD results.
- Tuning on 2026-07-01 with `GAMG/DIC` pressure and `CrankNicolson 0.9`
  completed a 24-rank full-mesh proof from `t=0` to `t=1.0`. Final max Courant
  was about `0.056`, `Cd` was smooth near `0.674`, probe values were bounded,
  and all 24 processor `1` directories were written. This proves startup past
  the prior `t~=0.043` crash and through 20% of the inlet ramp, but not the full
  `5 D/U` ramp or production statistics.
- Confidence gate recorded on 2026-07-01: do not call this case production-run
  credible until it has at least completed the full inlet ramp to `t=5` and
  entered post-ramp flow with bounded Courant number, bounded probes, no fatal
  solver signatures, and smooth force history. A stronger confidence target is
  `t=10-20`, which begins to exercise wake development after the ramp.
- The 2026-07-01 `GAMG/DIC` + `CrankNicolson 0.9` proof run completed the full
  inlet ramp and entered post-ramp flow. It wrote `t=5.0000817116` on all 24
  processor directories and was later interrupted cleanly after reaching
  `t~=5.262`. The tail showed `maxCo ~= 0.15`, bounded continuity errors,
  smooth force coefficients (`Cd` settling near `1.23` after ramp-end peak,
  tiny `Cl`), and no `FOAM FATAL`, floating-point, MPI, or GAMG crash
  signatures. This satisfies the recorded production-credibility ramp gate, but
  statistical validation still needs the longer `t=10-20` wake-development
  check and ultimately production averaging to `endTime=180`.
- On 2026-07-01, increasing `system/controlDict` to `maxCo 1` and
  `maxDeltaT 0.01` was picked up by the active 24-rank run. The run reached
  `maxCo ~= 0.9997` around `t=5.36-5.37` with `deltaT ~= 0.00411`, bounded
  continuity errors, and smooth force output in the observed log tail. This is
  a CFL-cap push, not a long statistical validation.
- A 2026-07-01 pre-HPC audit found the active CFL-1 run healthy at
  `t~=7.20`: `running=yes`, `fatal=no`, `maxCo ~= 0.99986`, bounded probes,
  bounded pressure history, and y+ on the cylinder roughly `0.5-6.3` through
  the latest write. Mesh quality remained clean (`Mesh OK`, max skewness
  `0.928`, max aspect ratio `8.64`). The main active force/probe output was
  under `postProcessing/.../1`; short `postProcessing/.../5.0000817116` files
  came from a stopped duplicate probe and should not be interpreted as the full
  run history.
- Benchmark setup adjustment on 2026-07-01: use `benchmark-5m`
  (`576 x 176 x 48 = 4.87M`) instead of an exact paper-HR-equivalent 44M-cell
  O-grid. Keep the paper HR statistics duration with `timeStart = 150` and
  `endTime = 400`, giving `250 D/U` after transient removal. A first
  `768 x 132 x 48` balanced-wake attempt started but failed `checkMesh` due to
  9216 low-determinant cells, so it was stopped and replaced by the more
  balanced `576 x 176 x 48`, `stretch=0.5` preset.
- The corrected `benchmark-5m` mesh passed `checkMesh` on 2026-07-01:
  `4,866,048` hex cells, max aspect ratio `11.61`, max non-orthogonality
  `44.68`, max skewness `1.54`, minimum cell determinant `0.00459`, `Mesh OK`.
  A bounded 24-rank start reached `t=0.039` with fixed `deltaT=0.003`,
  bounded continuity, and no fatal signatures before being stopped deliberately.
- Solver audit for the benchmark setup: use fixed `deltaT=0.003` to match the
  paper and avoid adaptive-CFL temporal bias. Keep `CrankNicolson 0.9` for
  startup because pure `CrankNicolson 1.0` previously caused odd-even force
  oscillations. `bounded Gauss linear` velocity convection is effectively the
  least-dissipative robust finite-volume choice currently proven stable in this
  case. `nNonOrthogonalCorrectors 1` is justified by max non-orthogonality near
  `45 deg`; dropping it would be faster but is not recommended for the
  benchmark baseline.
- HPC migration guards were added in `HPC_MIGRATION_GUARDS.md` rather than
  hard-coded runtime choices. On the target HPC machine, Codex should retune
  decomposition for that interconnect/node shape and retune force/probe/field
  output for that filesystem before the long production run.
- Future long runs should use `scripts/monitor_run.sh` or equivalent polling
  to leave an explicit status file.

- GCP H4D launch on 2026-07-01: benchmarked 48/96/192-rank Scotch decompositions on the `benchmark-5m` mesh. The 10-step startup wall times were about `14.5 s`, `8.5 s`, and `5.3 s`, respectively, so the production run was launched on all `192` cores. Final `decomposePar` balance was good: max cells `25704` (`1.42%` above the `25344` average), `478329` processor faces, and max interprocessor faces `6582`.
- For the GCP H4D production launch, field writes were changed to every `5 D/U` with `purgeWrite 2`; force and probe function objects were changed from every timestep to every `5` timesteps. At `deltaT=0.003`, this keeps about `320` samples per shedding period while reducing force/probe small-file writes by `5x`. The installed disk had about `238 GiB` free at launch; retained late-run binary checkpoint payload was estimated at about `1.23 GiB` for two post-average checkpoints, with mesh, logs, and dense samples well below the `256 GB` disk budget.
- The detached 192-rank GCP H4D run was started with `setsid -f` through `tmp/cylinder_re3900_launch_production.sh`, `OMP_NUM_THREADS=1`, log `cases/cylinderRe3900_LES/log.pimpleFoam`, status `run.status`, and launcher PID in `run.pid`. Initial active polling reached `t=1.347` with `running=yes`, `fatal=no`, max Courant about `0.238`, bounded continuity/solver output, and smooth force output. This is a startup-stability check, not the full `t=5` inlet-ramp gate.

- Follow-up polling on 2026-07-01 confirmed the GCP H4D production run cleared the startup ramp: status at `2026-07-01T14:57:46Z` was `running=yes`, `fatal=no`, `latest_time=11.811`, `ClockTime=1131 s`, and max Courant about `0.616`. The first post-ramp field writes were present at `processor0/5.001` and `processor0/9.999`; force and probe tails remained bounded. The then-current full-run ETA to `endTime=400` was about `2026-07-02T01:17Z` UTC if speed held.

- Overnight GCP H4D production run completed cleanly on 2026-07-01/02: final solver time `t=399.99899999872662`, `running=no`, `fatal=no`, strict fatal scan clean, final `ClockTime = 32417 s` (~`9.00 h`), and final max Courant about `0.876`. Retained field writes were `395.0009999987501` and `399.99899999872662` as expected from `purgeWrite 2`; final cylinder y+ was min `1.66`, max `16.04`, average `8.96`.
- Post-run analysis over the intended statistics window `t >= 150` did not validate against the recorded targets. Force analysis found mean `Cd = 1.635`, `Cl` mean near zero but `Cl_rms ~= 0.913`, and shedding `St ~= 0.183` from both spectral and zero-crossing estimates, below the target near `0.208`. Final `UMean` centerline sampling found mean reattachment at `x ~= 1.089` from cylinder center, or `0.589D` downstream of the rear surface, far shorter than the `Lr/D ~= 1.5-1.6` target. Treat the run as a clean numerical completion but a failed benchmark validation baseline. Analysis artifacts are under `tmp/cylinderRe3900_analysis/`.
- Follow-up diagnosis on 2026-07-02 found the failed benchmark does not look
  like simple global numerical over-dissipation. The force/probe signal remains
  highly energetic (`Cl` range about `-1.69..1.72`, `Cl_rms ~= 0.91`) and the
  SGS viscosity is modest in most cells (`nut/nu` median about `6e-4`, 95th
  percentile about `0.30`, max about `12.2`). The stronger suspect is local
  wall/near-separation modeling: the `benchmark-5m` mesh has first cylinder
  wall-normal spacing about `0.0417D`, much coarser than the circumferential
  spacing about `0.00545D`, giving final cylinder y+ around `1.66-16.04` while
  using `nutUSpaldingWallFunction` on a separating cylinder. A multi-z
  `UMean` centerline sample at `z/pi = 0.25, 0.5, 0.75` confirmed the short
  bubble is not a midspan artifact: reattachment was about `0.57-0.67D` behind
  the rear surface, with a three-line average about `0.60D`. Scratch sampling
  dictionary: `tmp/cylinderRe3900_analysis/spanCenterlineControlDict`.
- Wall-resolved correction on 2026-07-02: do not use a turbulent wall
  function on the cylinder because the upstream cylinder boundary layer is
  laminar/transitional before separation. The workspace `0/nut` cylinder patch
  was changed to `fixedValue uniform 0` and the tracked `benchmark-5m` mesh
  preset was retuned from radial `stretch=0.5` to `stretch=4.6`. This keeps the
  same `576 x 176 x 48 = 4.87M` cells but changes first wall-normal spacing to
  about `0.00255D`, near-wall radial growth ratio to about `1.0265`, and the
  old-run y+ scaling estimate to average `~0.55`, max `~0.98`. Actual y+ must
  be checked from the `yPlus` function object after a fresh startup/wake proof
  run because the corrected wall treatment can change wall shear. `controlDict`
  now starts from `startTime` to avoid accidental restart from the invalid
  wall-function latest time.
- Wall-resolved launch audit on 2026-07-02: stale wall-function run artifacts
  (`processor*`, `postProcessing`, `constant/polyMesh`, old launch/status/logs)
  were archived under `tmp/cylinderRe3900_wallFunction_archive_20260702T024927Z`
  before regenerating. The new `benchmark-5m` mesh passed `checkMesh`: 4,866,048
  hex cells, max aspect ratio `26.99`, max non-orthogonality `44.66`, max
  skewness `1.15`, min determinant `0.0218`, and `Mesh OK`. The 192-rank Scotch
  decomposition completed with average `25344` cells/rank and max `25928`
  cells/rank (`~2.3%` above average). The 192-rank wall-resolved run was then
  launched detached and actively polled to the startup gate `t >= 10`. At
  `t=10.203`, it was still running with no fatal signatures, max Courant about
  `0.849`, and `ClockTime = 890 s`. Measured cylinder y+ was `min/max/avg =
  0.0345/1.486/0.661` at `t=5.001` and `0.0138/1.342/0.594` at `t=9.999`,
  confirming resolved-wall behavior without extreme over-refinement.

Validation targets:

- Strouhal number near `0.208`.
- Recirculation length `Lr/D` near `1.5-1.6`.
- Statistics should not be judged before the ramp and transient have cleared.
