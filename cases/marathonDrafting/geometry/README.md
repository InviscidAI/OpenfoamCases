# MakeHuman runner surfaces (CC0)

Two posed, closed triangle surfaces of human runners for the marathon-drafting
OpenFOAM case (snappyHexMesh) and for the side/top drawings.

| file | what |
|---|---|
| `runner_female.stl`, `runner_female.obj` | female, young adult (25 y), slim, 1.65 m standing |
| `pacer_male.stl`, `pacer_male.obj` | male, young adult (25 y), slim, 1.75 m standing |
| `preview_side.png`, `preview_top.png`, `preview_front.png` | orthographic previews, both figures |
| `preview_drafting.png` | runner 1.3 m (hip centre to hip centre) behind the pacer, side and top |
| `build_report.json` | every number below, machine readable |
| `LICENSE.ASSETS.md` | CC0 1.0, copied from the MakeHuman repository |

Build script: `cases/cyclistBehindLorry/scripts/build_runners.py` (re-runnable;
downloads into `~/.cache/makehuman-cc0/<commit>/`).

## Frame and units

Metres. z up, running direction +x, the figure's left is +y. x = 0 at the
centre of the two hip joints, y centred on the bounding box, z = 0 at the lowest
point of the grounded (right) foot. STL is binary; OBJ has the same vertices
and triangles.

## Source

- Repository: https://github.com/makehumancommunity/makehuman, commit `a8bc2d54ff0ac92e78ff71431b1023eda42bf482`
- Licence: `LICENSE.md` section on assets: base mesh, proxies, targets,
  modifiers, poses and rigs are CC0 1.0 (`LICENSE.ASSETS.md`).
- The `makehuman` application/PyPI package was not installed or run. Its
  algorithms were re-implemented from the source at this commit:
  `apps/humanmodifier.py` (MacroModifier, getTargetWeights), `apps/human.py`
  (`_set*Vals`, `getHeightCm`, `getWeightKg`), `lib/targets.py` (target-name
  factor categories), `core/algos3d.py` (target text format),
  `shared/skeleton.py` (joint positions, bone planes and `getMatrix`,
  `Bone.build/update`, `skinMesh`), `shared/animation.py`
  (`VertexBoneWeights` normalisation).
- Files fetched (raw text, not the compiled `.npz`):

- `makehuman/data/3dobjs/base.obj`
- `makehuman/data/rigs/default.mhskel`
- `makehuman/data/rigs/default_weights.mhw`
- `LICENSE.ASSETS.md`
- `LICENSE.md`
- `makehuman/data/targets/macrodetails/african-female-young.target`
- `makehuman/data/targets/macrodetails/asian-female-young.target`
- `makehuman/data/targets/macrodetails/caucasian-female-young.target`
- `makehuman/data/targets/macrodetails/universal-female-young-minmuscle-minweight.target`
- `makehuman/data/targets/macrodetails/height/female-young-minmuscle-minweight-minheight.target`
- `makehuman/data/targets/macrodetails/height/female-young-minmuscle-minweight-maxheight.target`
- `makehuman/data/targets/macrodetails/universal-female-young-minmuscle-averageweight.target`
- `makehuman/data/targets/macrodetails/height/female-young-minmuscle-averageweight-minheight.target`
- `makehuman/data/targets/macrodetails/height/female-young-minmuscle-averageweight-maxheight.target`
- `makehuman/data/targets/macrodetails/universal-female-young-minmuscle-maxweight.target`
- `makehuman/data/targets/macrodetails/height/female-young-minmuscle-maxweight-minheight.target`
- `makehuman/data/targets/macrodetails/height/female-young-minmuscle-maxweight-maxheight.target`
- `makehuman/data/targets/macrodetails/universal-female-young-averagemuscle-minweight.target`
- `makehuman/data/targets/macrodetails/height/female-young-averagemuscle-minweight-minheight.target`
- `makehuman/data/targets/macrodetails/height/female-young-averagemuscle-minweight-maxheight.target`
- `makehuman/data/targets/macrodetails/universal-female-young-averagemuscle-averageweight.target`
- `makehuman/data/targets/macrodetails/height/female-young-averagemuscle-averageweight-minheight.target`
- `makehuman/data/targets/macrodetails/height/female-young-averagemuscle-averageweight-maxheight.target`
- `makehuman/data/targets/macrodetails/universal-female-young-averagemuscle-maxweight.target`
- `makehuman/data/targets/macrodetails/height/female-young-averagemuscle-maxweight-minheight.target`
- `makehuman/data/targets/macrodetails/height/female-young-averagemuscle-maxweight-maxheight.target`
- `makehuman/data/targets/macrodetails/universal-female-young-maxmuscle-minweight.target`
- `makehuman/data/targets/macrodetails/height/female-young-maxmuscle-minweight-minheight.target`
- `makehuman/data/targets/macrodetails/height/female-young-maxmuscle-minweight-maxheight.target`
- `makehuman/data/targets/macrodetails/universal-female-young-maxmuscle-averageweight.target`
- `makehuman/data/targets/macrodetails/height/female-young-maxmuscle-averageweight-minheight.target`
- `makehuman/data/targets/macrodetails/height/female-young-maxmuscle-averageweight-maxheight.target`
- `makehuman/data/targets/macrodetails/universal-female-young-maxmuscle-maxweight.target`
- `makehuman/data/targets/macrodetails/height/female-young-maxmuscle-maxweight-minheight.target`
- `makehuman/data/targets/macrodetails/height/female-young-maxmuscle-maxweight-maxheight.target`
- `makehuman/data/targets/macrodetails/african-male-young.target`
- `makehuman/data/targets/macrodetails/asian-male-young.target`
- `makehuman/data/targets/macrodetails/caucasian-male-young.target`
- `makehuman/data/targets/macrodetails/universal-male-young-minmuscle-minweight.target`
- `makehuman/data/targets/macrodetails/height/male-young-minmuscle-minweight-minheight.target`
- `makehuman/data/targets/macrodetails/height/male-young-minmuscle-minweight-maxheight.target`
- `makehuman/data/targets/macrodetails/universal-male-young-minmuscle-averageweight.target`
- `makehuman/data/targets/macrodetails/height/male-young-minmuscle-averageweight-minheight.target`
- `makehuman/data/targets/macrodetails/height/male-young-minmuscle-averageweight-maxheight.target`
- `makehuman/data/targets/macrodetails/universal-male-young-minmuscle-maxweight.target`
- `makehuman/data/targets/macrodetails/height/male-young-minmuscle-maxweight-minheight.target`
- `makehuman/data/targets/macrodetails/height/male-young-minmuscle-maxweight-maxheight.target`
- `makehuman/data/targets/macrodetails/universal-male-young-averagemuscle-minweight.target`
- `makehuman/data/targets/macrodetails/height/male-young-averagemuscle-minweight-minheight.target`
- `makehuman/data/targets/macrodetails/height/male-young-averagemuscle-minweight-maxheight.target`
- `makehuman/data/targets/macrodetails/universal-male-young-averagemuscle-averageweight.target`
- `makehuman/data/targets/macrodetails/height/male-young-averagemuscle-averageweight-minheight.target`
- `makehuman/data/targets/macrodetails/height/male-young-averagemuscle-averageweight-maxheight.target`
- `makehuman/data/targets/macrodetails/universal-male-young-averagemuscle-maxweight.target`
- `makehuman/data/targets/macrodetails/height/male-young-averagemuscle-maxweight-minheight.target`
- `makehuman/data/targets/macrodetails/height/male-young-averagemuscle-maxweight-maxheight.target`
- `makehuman/data/targets/macrodetails/universal-male-young-maxmuscle-minweight.target`
- `makehuman/data/targets/macrodetails/height/male-young-maxmuscle-minweight-minheight.target`
- `makehuman/data/targets/macrodetails/height/male-young-maxmuscle-minweight-maxheight.target`
- `makehuman/data/targets/macrodetails/universal-male-young-maxmuscle-averageweight.target`
- `makehuman/data/targets/macrodetails/height/male-young-maxmuscle-averageweight-minheight.target`
- `makehuman/data/targets/macrodetails/height/male-young-maxmuscle-averageweight-maxheight.target`
- `makehuman/data/targets/macrodetails/universal-male-young-maxmuscle-maxweight.target`
- `makehuman/data/targets/macrodetails/height/male-young-maxmuscle-maxweight-minheight.target`
- `makehuman/data/targets/macrodetails/height/male-young-maxmuscle-maxweight-maxheight.target`

## Modelling

- Macro targets: weight of each target = product of the factors in its file
  name (gender, age, race, muscle, weight, height), exactly as
  `getTargetWeights`. Ethnicity is MakeHuman's default 1/3 each. Age 0.5 = 25
  years, so only the `young` targets are non-zero. Proportions, breast and all
  other modifiers stay at MakeHuman's defaults (no displacement).
- Height: the height slider is solved by bisection until `getHeightCm`
  (y-extent of the `body` group in the rest A-pose) equals 165.0 / 175.0 cm.
- Body only: the `body` face group of `base.obj` (13 378 quads). All helper
  geometry (joint cubes, eyes, eyelashes, eyebrows, teeth, tongue, genital,
  hair/skirt/tights helpers) is dropped. The body group is already a closed,
  genus-0 surface (eye sockets and mouth are closed in the base mesh), so no
  holes had to be closed. No proxy mesh was used: the base body is closed and
  is the mesh the default skeleton weights belong to.

## Pose

Linear blend skinning with `default.mhskel` and `default_weights.mhw`, using
MakeHuman's bone matrices (`matPoseVerts = matPoseGlobal . inv(matRestGlobal)`).
Bone rotations were set so that the limb segments point in target directions
measured from the vertical (MakeHuman's rest pose is an A-pose with the elbows
already bent about 50 deg and knees about 7 deg, so increments on the rest pose
would not give the stated angles). Inputs:

| parameter (deg) | value |
|---|---|
| trunk_lean_fwd | 5.0 |
| head_level | True |
| thigh_frontal | -5.0 |
| r_hip_flex | 30.0 |
| r_knee_flex | 40.0 |
| l_hip_ext | 20.0 |
| l_knee_flex | 65.0 |
| r_sole_toe_up | 5.0 |
| l_ankle_plantar | 0.0 |
| arm_abduction | 20.0 |
| l_shoulder_flex | 25.0 |
| r_shoulder_ext | 25.0 |
| elbow_flex | 85.0 |
| finger_curl | (45.0, 50.0, 35.0) |
| thumb_curl | (10.0, 20.0, 20.0) |
| finger_sign | 1.0 |

Notes: `trunk_lean_fwd` is a 5 deg forward rotation at the lumbar joint
(spine05); MakeHuman's standing trunk line is not exactly vertical, so the
measured neck-to-lumbar line ends at the value in the table below. Arm angles
are from the vertical in the world frame (the trunk lean is compensated).
`arm_abduction` was raised from 13 to 20 deg to keep the upper arm 2.5-4 cm off
the torso. The thighs are adducted 5 deg so the feet fall under the body
instead of MakeHuman's wide A-pose stance. Fingers are curled about each
phalanx bone's own hinge axis; the thumb is only lightly curled.

## Processing

1. Morph the full base mesh (all 19 158 vertices, helpers included because
   joint positions come from them), build the skeleton, pose by LBS.
2. Take the `body` quads, apply one Catmull-Clark subdivision (as MakeHuman's
   smooth display does), triangulate along the shorter diagonal.
3. Quadric edge-collapse decimation to 50000 triangles (pymeshlab,
   topology and normals preserved).
4. Convert MakeHuman's decimetres, y-up, +z-facing frame to metres, z-up, +x.
5. Self-intersection and fold repair: LBS makes the elbow and knee creases and
   the curled fingers interpenetrate. Every vertex within 3 rings of an
   intersecting face (pymeshlab face-face test) or of a fold (adjacent normals
   more than 150 deg apart) is relaxed with 5 umbrella-Laplacian steps, repeated
   until both counts are zero.
6. Place in the frame above and check.

## Results and checks

| quantity | runner_female | pacer_male |
|---|---|---|
| macro: gender / age / muscle / weight | 0.00 / 0.50 / 0.65 / 0.45 | 1.00 / 0.50 / 0.65 / 0.45 |
| macro: height slider (solved) | 0.5417 | 0.5136 |
| standing height, rest A-pose (m) | 1.650 | 1.750 |
| posed height (m) | 1.593 | 1.687 |
| bbox min x, y, z (m) | -0.598, -0.276, 0.000 | -0.655, -0.312, 0.000 |
| bbox max x, y, z (m) | 0.453, 0.276, 1.593 | 0.549, 0.312, 1.687 |
| bbox size (m) | 1.051, 0.552, 1.593 | 1.204, 0.623, 1.687 |
| surface area (m2) | 1.509 | 1.747 |
| volume (m3) | 0.0499 | 0.0613 |
| mass at 1000 kg/m3 (kg) | 49.9 | 61.3 |
| MakeHuman getWeightKg, standing (kg) | 51.9 | 66.6 |
| frontal area, y-z plane (m2) | 0.384 | 0.441 |
| side area, x-z plane (m2) | 0.360 | 0.421 |
| triangles / vertices | 50000 / 25002 | 50000 / 25002 |
| mean / max edge (mm) | 8.4 / 24.9 | 9.1 / 35.0 |
| min triangle angle (deg) | 2.39 | 3.77 |
| watertight / manifold / consistent / outward | True / True / True / True | True / True / True / True |
| genus / components / boundary edges | 0 / 1 / 0 | 0 / 1 / 0 |
| self-intersecting faces (final) | 0 | 0 |
| intersecting faces before repair, passes | 35, [(35, 50), (0, 0)] | 70, [(70, 22), (31, 6), (4, 4), (0, 0)] |
| max vertex move by repair (mm) | 4.8 | 6.8 |
| degenerate faces | 0 | 0 |
| left foot lowest z (m) | 0.213 | 0.234 |
| lowest point (x, y, z) / bone | 0.111, -0.026, 0.000 / foot.R | 0.109, -0.031, 0.000 / foot.R |
| clearance forearm_hand.L to torso/legs (m) | 0.105 | 0.121 |
| clearance upperarm_below_axilla.L to torso/legs (m) | 0.031 | 0.025 |
| clearance forearm_hand.R to torso/legs (m) | 0.091 | 0.101 |
| clearance upperarm_below_axilla.R to torso/legs (m) | 0.040 | 0.041 |
| measured: trunk_lean_fwd_change | 5.00 | 5.00 |
| measured: trunk_line_from_vertical | 2.37 | 5.85 |
| measured: head_pitch_change | -0.00 | 0.00 |
| measured: right_thigh_from_vertical | 30.00 | 30.00 |
| measured: right_knee_flex | 39.82 | 39.85 |
| measured: right_shank_from_vertical | -10.00 | -10.00 |
| measured: right_upperarm_from_vertical | -25.00 | -25.00 |
| measured: right_upperarm_abduction | 21.88 | 21.88 |
| measured: right_elbow_flex | 85.00 | 85.00 |
| measured: right_hand_height_m | 0.90 | 0.93 |
| measured: left_thigh_from_vertical | -20.00 | -20.00 |
| measured: left_knee_flex | 64.65 | 64.74 |
| measured: left_shank_from_vertical | -85.00 | -85.00 |
| measured: left_upperarm_from_vertical | 25.00 | 25.00 |
| measured: left_upperarm_abduction | 21.88 | 21.88 |
| measured: left_elbow_flex | 85.00 | 85.00 |
| measured: left_hand_height_m | 1.17 | 1.25 |
| measured: hip_joint_height_m | 0.79 | 0.87 |

Drafting arrangement (preview_drafting.png): with the runner's hip centre
1.3 m behind the pacer's, the pacer's rearmost point (trailing foot)
is at x = -0.655 m and the runner's frontmost point (leading
hand) at x = -0.847 m: a 0.192 m gap. Both figures are in the
same phase of the stride.

## Known limitations

- Runner mass and frontal area: with a slim weight slider (0.45) the female is
  about 50 kg (posed volume x 1000 kg/m3; MakeHuman's own Mosteller estimate on
  the standing body is about 52 kg) and her frontal area is about 0.38 m2,
  below the literature model's 55 kg and 0.44 m2. Reaching 55 kg needs weight
  about 0.7, which is above MakeHuman's average and no longer "low weight". The
  literature area probably also includes hair and clothing; these figures are
  bald and unclothed.
- LBS loses about 2-3 % of volume at the bent joints, and the repair locally
  smooths the elbow and knee creases and finger contacts (largest move in the
  table). The repair targets surface validity, not anatomical accuracy there.
- Fingers are separate with small gaps (millimetres) between them and against
  the palm. At a 1 cm surface cell snappyHexMesh will not resolve these and
  will treat the hand roughly as a closed fist; refine there if hands matter.
- The grounded foot is pitched 5 deg toe-up so the heel is one lowest point
  instead of a flat sole lying on z = 0; the sole is within a few millimetres of
  the ground near the heel, which gives thin cells against a moving-ground
  wall. Lift the figure by a few millimetres or cut a contact pad if
  snappyHexMesh struggles there.
- Self-intersection testing uses pymeshlab's face-face test plus the fold
  check above; no second independent intersection checker was run.
