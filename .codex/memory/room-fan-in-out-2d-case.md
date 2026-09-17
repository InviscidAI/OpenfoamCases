---
category: case
triggers: [room, fan, ventilation, 2D, fanPressure, totalPressure, furniture, cold-start, blockMesh]
status: active
cases: [cases/roomFanInOut2D]
---

# Room Fan In vs Out 2-D Case Notes

Case path: `cases/roomFanInOut2D`. Two runs differing in one setting — fan direction —
backing a published clip, so the case exists to be checked against the video.

## Setup choices

- `4.00 x 3.00 m` plan, genuinely 2-D: one cell thick, `empty` front and back.
- ~26,175 fluid cells at `0.02 m` nominal spacing, `pimpleFoam`, k-epsilon,
  `nu = 1.5e-05`, momentum `Gauss limitedLinearV 1`.
- `fanPressure` on the fan with a curve in `constant/fanCurve.dat` (25 Pa shutoff,
  1.10 m^3/s free delivery); `totalPressure p0 = 0` on the vent. Both matter — see
  `boundary-energy-budget-guard.md`.
- Direction is an argument to `Allrun`, not a second copy of the case, so "differs in
  exactly one setting" is true by construction rather than by inspection.

## Why 2-D, and what it costs

The clip renders a plan view. In 3-D, a plan slice could not show this subject: of the air
turning from the fan toward the vent, only ~3% passed within 0.15 m of the rendered plane,
the rest going over and under. The flow was genuinely three-dimensional and no single
plane could show it. Going 2-D makes the plan view *be* the solution domain.

The cost is that 2-D removes floor and ceiling friction, which are the largest wall areas.
Expect a 2-D room to circulate more freely than the same room in 3-D.

## Mesh generation with cut-outs

`scripts/generate_room_mesh.py` splits the block grid at every feature coordinate, drops
blocks whose centre lies inside a fitted solid, and turns newly exposed faces into a
`furniture` patch. Splitting at feature coordinates is what puts the openings on exact
cell boundaries, so `fan` spans precisely `y 0.99..2.01` rather than the nearest cell edge.

Only floor-to-ceiling furniture is meshed, and that is a constraint, not a preference: a
2-D obstacle is full height by construction, which is fair for a fitted wardrobe and wrong
for a bed. Furnishing was not cosmetic — it cut circulation 4.7% supplying and 9.0%
extracting, and moved the headline difference from 19.7% to 14.2%.

## Cold start and the development window

The interesting artefact was the *development*, not the settled field: a settled 2-D room
here is visually static, with max speed varying 0.0-0.5% over 40 s. Starting from rest and
animating the flow establishing itself is what gave the clip something to show.

Window `t = 2..60 s`. Start at 2 s omits the uniform-`k`/`epsilon` startup artefact. End
chosen from pilots continued to `t = 240`: last monitored quantity to enter and remain
within 0.5% of its `t = 220..240` mean was supply mean speed at `t = 50.9 s`; RMS velocity
difference from `t = 240` at `t = 60` was 0.0011 m/s supply, 0.0003 extraction. The empty
room needed `t = 100` — furniture shortens settling, so do not inherit a window across a
geometry change.

## Results

| | supply | extraction |
|---|---|---|
| through-flow | 1.09510 m^3/s | 1.09555 m^3/s |
| domain-mean speed | 0.18834 m/s | 0.21509 m/s |

Through-flow equal to 0.04%; extraction mixes 14.2% more.

## Known weakness

The fan opening is 1.02 m^2, which is large. The curve fixes volume flow, so the
understated quantity is jet momentum — 1.1 m/s at the face where a smaller opening passing
the same air would be several times that. Jet momentum drives mixing, which is the one
result with a winner, so shrinking the opening to a realistic grille is the obvious next
change and would want its own paired comparison.
