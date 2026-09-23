# Air fryer vs convection oven: where does the fan's air go?

Two OpenFOAM cases with the same fan supply and the same four pieces of food. The only
difference is the appliance around them. Each case measures how fast the air moves over the
food and how much of the fan's air actually reaches it.

## The question

People argue about whether an air fryer is anything more than a small convection oven with
a fan. Cooking is heat transfer, and **these cases carry no temperature**, so they cannot
say which one cooks better. They answer the flow half of that argument: with the same fan
and the same food, how does the air move through each one?

## What the clip shows, and what it does not

**It shows two circuits that differ in kind.** In the fryer, the fan pushes air down the
channels between the basket and the tank, under the basket, and up through the perforated
base and the food. Then it returns to the fan. The geometry forces every bit of the air
along that path. In the oven, the air leaves the back wall as two jets, crosses the cavity
and the food bank, and loops back.

**The clip prints no numbers.** Here they are, with the reason they carry no verdict:

| case | food-envelope mean speed | fan air reaching the food | cells |
|---|---|---|---|
| air fryer | 1.040 m/s | 92.4% | 5,733 |
| convection oven | 0.675 m/s | 81.0% | 9,845 |

Both are time means over **t = 5 to 25 s**, 481 samples at 1/24 s.
`results/*.json` has full precision and the standard deviations.

## Physics

Incompressible, isothermal air (nu = 1.5e-5 m²/s), `pimpleFoam` with k-omega SST URANS, 25 s
from rest. Both are 2-D: one cell thick (0.01 m) with `empty` front and back.

**What is held identical:**
- four no-slip food blocks, each 0.050 × 0.025 m
- the fan supply, 0.12 m²/s per unit depth
- the inlet turbulence (k = 0.00375 m²/s², omega = 120 1/s)
- the schemes, the solver settings and the averaging window

**What is deliberately different is the appliance itself:**

- **Air fryer**, 0.32 × 0.34 m. It supplies 1.5 m/s downward through two openings at the top
  sides. Their open width is 0.04 m each, because the basket walls take 0.01 m of each
  0.05 m span. The central top opening, 0.10 m wide, is the return to the fan.
- **Convection oven**, 0.45 × 0.40 m. It supplies 1.0 m/s through two 0.06 m openings in the
  back wall, and air leaves through a 0.06 m return in the front wall.

The two metrics are defined once:

- **Food-envelope mean speed**: the cell-volume-weighted mean of |U| over the rectangle that
  encloses all four food blocks, then averaged over time. The rectangle is x = 0.075–0.245,
  y = 0.095–0.225 m in the fryer, and x = 0.13–0.32, y = 0.095–0.265 m in the oven.
- **Fan air reaching the food**: *gross* one-way flux through a gate, with reverse flow
  clipped to zero, divided by the 0.12 m²/s supply. In the fryer the gate is the upward flux
  through the perforated base. In the oven it is the flux toward the front through
  x = 0.225 m, over y = 0.08–0.32 m. The flux is gross, not net, on purpose: in a closed loop
  net flux across many lines is zero by construction, and it hid a short circuit in an
  earlier version of these cases.

## Limits, which are the part worth reading

**The oven's return is in the wrong place, on purpose.** A real convection oven draws air
back in at the centre of its rear baffle. Its fan throws air out radially and with swirl, so
the air travels round the cavity before coming back. A 2-D section cannot carry that swirl.
With the return on the back wall, the supply jets turned straight round into it: only 9–12%
of the fan's air crossed the food, and the result moved 81% depending on whether small
separator plates were modelled. Moving the return to the front wall reproduces the
*consequence* of the real path, air crossing the cavity before it returns. It does not
reproduce the path itself or where the air returns. The oven's numbers depend on that
choice.

**Neither appliance's swirl is modelled.** That biases both speeds low, by an amount this
setup cannot quantify. It biases the oven more, because the fryer's walls force the long
path anyway.

**There is one mesh and one turbulence model per case, and no grid convergence.** There is no
uncertainty bound on either number, so the 1.54 speed ratio does not mean one appliance
moves air 54% faster.

**The fan is a fixed velocity.** There is no fan curve, blades, grille or motor. Both
appliances get the same supply whatever resistance they present, which a real fan would not.

**There is no temperature, radiation, conduction into food, or moisture.** So there is no
claim about cooking rate, crispness or cooking time, and no claim about every air fryer or
convection oven on the market.

## Running it

You need [OpenFOAM](https://www.openfoam.com) v2512 or near it, Python 3, and the `gmsh`
Python module (`pip install gmsh`).

```sh
cd cases/airFryerVsOven/airFryer        # or: convectionOven
./Allrun
```

`Allrun` cleans the directory and runs `build.py`, which writes the geometry, the mesh (gmsh,
then `gmshToFoam`), the dictionaries and the initial fields. It then checks the mesh and solves
on four ranks. `./Allclean` returns the directory to source-only. The oven runs with
`maxCo 1.5` and the fryer with `maxCo 0.7`. Everything else is the same.

`system/centreline` is the sampling function the clip's frames were cut from, a mid-plane
slice with `U`, `p` and `k`. Run it after the solve with
`pimpleFoam -postProcess -func centreline` if you want the same slices.

The cases were set up by an agent and checked by us. The fryer's air circuit was reversed in
an earlier version, and the oven's return was moved after the first build short-circuited.
Both corrections are described above; this directory holds only the version the clip shows.
