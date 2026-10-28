# A Tesla valve in water: forward against reverse

Nikola Tesla's valvular conduit (US patent 1,329,559, 1920) has no moving parts. Water
passes one way along a channel past a row of loops. The other way, the loops turn
water back into the channel against the oncoming flow. How much harder the second way is, at the same flow rate,
is its diodicity: the reverse pressure drop over the forward one.

One OpenFOAM case, run two ways. `./Allrun forward` and `./Allrun reverse` differ only
in which end the water comes in at.

    ./Allrun forward     # the easy way: in at the right end, out at the left
    ./Allrun reverse     # the blocking way: in at the left, against the loops

## The valve

| | value |
|---|---|
| channel | 5 mm wide, 130 mm long: 15 mm in, four loops at 25 mm pitch, 15 mm out |
| loops | each leaves the channel at 30 degrees, turns 50 degrees up and 230 degrees back on a 6 mm centreline radius, and comes back into the channel 12.4 mm further on, heading 150 degrees off +x |
| tongues | a trapezoid on the bottom wall between each loop's two mouths, necking the channel to a 2.0 mm throat |
| height | 16.6 mm overall, the loops rising 14.1 mm above the channel's centreline |
| span | 1 mm, one cell, front and back `empty`: a 2-D section |

`build_valve.py` builds it from these parameters with gmsh. The loops and the tongues
are named at the top of the file; change one there and both directions are rebuilt the
same way.

The tongues matter. The same loops on a plain straight channel gave a diodicity of 0.98
in the staff study this case comes from: the water ran straight past the loops' mouths
both ways. Necking the channel between the mouths is what made the difference there.
This case does not test why.

## The flow

- Water, nu = 1e-6 m2/s, rho = 1000 kg/m3, incompressible and isothermal.
- 0.5 m/s uniform at the upstream end: Re = 2500 on the 5 mm channel.
- The downstream end held at p = 0, its velocity free to flow in or out.
- From rest to 0.5 s, about two flow-throughs. `pimpleFoam`, k-omega SST, second-order
  backward time steps at Courant 2 (a mean of 1.7e-4 s forward and 1.4e-4 s reverse),
  two outer correctors.
- Inflow turbulence 5% intensity (k = 9.4e-4 m2/s2, omega = 160 1/s).

## The mesh

gmsh, triangles 0.18 to 0.30 mm extruded one cell: 32,196 prisms, about 17 across the
channel. `checkMesh`: non-orthogonality at most 33.3 degrees, skewness at most 0.57,
aspect ratio at most 2.6. There are no wall layers.

## What it finds

The pressure drop is rho times the difference of the two ends' mean pressures,
upstream minus downstream, averaged over 0.3 to 0.5 s. `postprocess.py` prints it for
each direction solved and the diodicity once both are.

| | pressure drop | spread (sd) | means of 0.3-0.35, ..., 0.45-0.5 s |
|---|---:|---:|---|
| forward, the easy way | **462.0 Pa** | 14.6 Pa | 458.8, 460.4, 464.0, 464.7 Pa |
| reverse, the blocking way | **723.6 Pa** | 43.7 Pa | 719.6, 718.4, 730.6, 723.4 Pa |
| **diodicity** | **1.57** | | |

**At the same flow, the blocking way costs 1.57 times the pressure of the easy way.**
Both runs carry exactly 0.5 m/s out of the far end, so the two drops are at the same
flow rate.

**The blocking way does not send more water round the loops. It sends less, and
brings it back the wrong way.** `loop_split.py` cuts through the top of each loop and
measures the share of the flow going round it. At 0.3, 0.4 and 0.5 s:

| | loop 1 | loops 2 to 4 |
|---|---:|---:|
| forward, the easy way | 36 to 37% | 33 to 37% |
| reverse, the blocking way | 45% | 18 to 24% |

In the easy direction a third of the water goes round each loop and rejoins the
channel at the far mouth heading 30 degrees off the channel's own direction, alongside
it. In the blocking direction a fifth goes round each loop after the first, and the
loop's geometry turns it back into the channel heading 150 degrees off, into the
oncoming jet. The rest is squeezed through the 2 mm throat. These are snapshots, not
time averages; the cut's two parts add up to within 1 to 3.5% of the inflow.

The staff study this case comes from gave 462 Pa, 722 Pa and 1.56 on the same mesh
and settings, sampling every 20th step. This directory, run as written on a Reynolds
workspace, gave the numbers above.

## Limits, which are the part worth reading

- **One mesh.** There is no mesh-independence study. A diodicity from one mesh is
  indicative. The staff study that set this case up expected about 10% from refining it.
- **A turbulence model at a transitional Reynolds number.** Re 2500 is where a channel
  flow is changing from laminar to turbulent. k-omega SST is applied to all of it. A
  laminar run or an LES would be the more defensible check, and either could move the
  diodicity. y+ on the walls at 0.5 s is at most 9.4 forward and 11.0 reverse (means
  3.2 and 3.6), below the wall functions' switch to the log law at about 11.5, so the
  near-wall flow is resolved rather than modelled. The core flow is not.
- **2-D.** A real valve has side walls. Their drag adds to both directions and is
  expected to lower the diodicity.
- **0.5 s.** That is about two flow-throughs. The blocking direction still swings by
  6% about its mean at the end, so the mean carries that spread; its 50 ms means wander
  by 12 Pa with no trend. The easy direction swings by 3%, and its 50 ms means rise
  1.3% across the window. Before 0.3 s the blocking drop is still falling from its
  start-up, 914 Pa at 0.1 s, which is why the average starts at 0.3 s.
- **One flow rate.** Diodicity depends on Reynolds number. This is one point on that
  curve, at 0.5 m/s, and says nothing about the valve at a trickle or at full pressure.
- **One geometry.** The loops and tongues were drawn for this case, not taken from
  Tesla's patent drawing or a published design. The diodicity belongs to this shape.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it, Python 3 with numpy, and
the `gmsh` Python package (`pip install gmsh`).

```sh
cd cases/teslaValve
./Allrun forward        # or: ./Allrun reverse; a second argument sets the MPI ranks, default 2
```

`Allrun` writes `runs/<direction>/` from `template/`, meshes it with `Allmesh`, solves
from rest to 0.5 s and runs `postprocess.py`. On 2 ranks of a Reynolds workspace
with 4 physical cores the forward run took 5.6 min and the reverse 6.7 min, one after the other.
`./Allclean` removes the runs.

The pressures at both ends and the flow out of each are written every time step to
`postProcessing/`, and y+ on the walls at each write. `python3 postprocess.py 0.4` averages
from 0.4 s instead. `python3 loop_split.py` prints the share of the flow going round each
loop at the last written time; it needs `pyvista`. Fields are written every 0.1 s.

The case was set up by an agent in a staff study and rebuilt here; the numbers above are
from rerunning this directory as it stands.
