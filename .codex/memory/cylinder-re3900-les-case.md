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
- Mesh: generated pure-hex O-grid, default `512 x 128 x 64 = 4.19M`
  cells.
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
- Future long runs should use `scripts/monitor_run.sh` or equivalent polling
  to leave an explicit status file.

Validation targets:

- Strouhal number near `0.208`.
- Recirculation length `Lr/D` near `1.5-1.6`.
- Statistics should not be judged before the ramp and transient have cleared.
