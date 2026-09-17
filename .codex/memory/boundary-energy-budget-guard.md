---
category: guard
triggers: [boundary, pressure, opening, inlet, outlet, fan, totalPressure, fixedValue, energy, unphysical, overspeed]
status: active
cases: [cases/roomFanInOut2D]
---

# Boundary Energy Budget Guard

When a case produces speeds that the driving condition cannot account for, check what the
boundaries are doing to the mechanical energy before blaming turbulence, mesh, or the
time step. Two common boundary choices can do unbounded work on the fluid, and neither
looks wrong in a contour plot.

## The check

For each boundary patch, sum the mechanical energy flux leaving through it:

```text
sum over faces of  (p + 0.5 |U|^2) (U . n) dA      p kinematic, n outward
```

A patch with a negative total is giving energy to the fluid. In steady state the sum over
all patches equals minus the dissipation, so a large net negative total is the amount of
power being fed into the domain. Compare it against what the physical device could
deliver.

Mass conservation does not catch either failure below: in both, flux balances exactly.

## Failure 1: fixed-velocity inlet or outlet

`fixedValue` on `U` with `zeroGradient` on `p` is a pump with no stall curve. It delivers
its flow rate at any back pressure, so if interior pressure at the patch falls below
`-0.5 |U_patch|^2` the sign of its head flips and the boundary does net work on the fluid,
without limit.

Observed: a 3 m/s fixed-velocity fan extracting from a 2-D room held its flow against
-44.6 m^2/s^2 (-53.6 Pa) and drove the room to 21 m/s mean, 36 m/s peak. Replacing it with
`fanPressure` and a real pressure-flow curve cut the peak to 1.1 m/s. A pressure-flow curve
is what makes an extraction case bounded.

## Failure 2: fixedValue static pressure on an opening that has inflow

`fixedValue` `p = 0` pins *static* pressure while incoming air arrives carrying kinetic
energy, so the total head at the patch is `+0.5 |U|^2` instead of zero and every bit of
that is free. `totalPressure` with `p0 = 0` sets `p = p0 - 0.5 |U|^2` on inflow and pins
total head to zero, which is what an opening to still air actually does.

Observed on a 3-D room: the extraction case received 102.9 units of power against the
supply case's 14.5, and 91.4 of those came from the vent rather than the fan — roughly
124 W of air power into a room where a domestic fan delivers 5 to 15.

The asymmetry is the tell. An opening that is an outlet in one run and an inlet in the
other will only misbehave in one of them, so a supply/extraction pair that disagrees far
more than the geometry suggests is worth budgeting before it is worth explaining.

## Related trap

A steady `simpleFoam` solution can relax into a state that physical-time integration does
not reach. The same case gave a domain-mean speed of 0.484 m/s steady against 0.236 m/s
transient, a factor of two, while the supply direction agreed between solvers to 0.5%.
Where a transient answer is the one being published, verify it transiently — and prefer a
cold start, which inherits nothing from either solver.
