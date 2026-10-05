# Results of the `hour` runs

Made by `postprocess.py`. Temperatures are area-weighted means over the section: the
floor layer is y < 0.1 m and head height y 1.0-1.2 m, both over x 0.3-2.0 m from the
glass. Fluxes are gross, one way, in m3/s per metre of section: the sill line is
y = 0.90 m for x < 0.30 m, the floor line x = 1.0 m for y < 0.30 m.

## Settled, means over 3000-3600 s

| | floor layer | head height | room mean | floor below room mean |
|---|---:|---:|---:|---:|
| window | 20.57 C | 20.94 C | 20.955 C | 0.38 K |
| opposite | 18.43 C | 21.13 C | 20.581 C | 2.15 K |

| | sill up | sill down | air falling past the sill | floor line away | floor line toward |
|---|---:|---:|---:|---:|---:|
| window | 0.0193 | 0.0085 | 17.9 C | 0.0003 | 0.0003 |
| opposite | 0.0000 | 0.0260 | 19.8 C | 0.0018 | 0.0071 |

Heat flows over the last 1200 s, W/m (negative leaves the air):

| | radiator | glass | ceiling | inner wall | stored | unaccounted |
|---|---:|---:|---:|---:|---:|---:|
| window | 60.0 | -50.5 | -6.4 | -2.9 | 0.23 | -0.005 |
| opposite | 60.0 | -48.0 | -9.6 | -2.4 | 0.07 | -0.003 |

## The floor draught against Heiselberg (1994), 3000-3600 s

dT is the room mean (roomMeanT) less the glass's inside surface (glassTs). The model
figure is the largest |Ux| below y = 0.3 m in the velocity profile averaged over
the window, m/s.

| x from the glass | window: Heiselberg | window: model | ratio | opposite: Heiselberg | opposite: model | ratio |
|---|---:|---:|---:|---:|---:|---:|
| 0.5 m | 0.193 | 0.005 | 0.03 | 0.194 | 0.175 | 0.90 |
| 1 m | 0.151 | 0.007 | 0.05 | 0.152 | 0.068 | 0.44 |
| 2 m | 0.104 | 0.005 | 0.05 | 0.104 | 0.061 | 0.58 |

dT: window 11.39 K, opposite 11.50 K

## Successive windows

| window (s) | window: room | window: floor layer | window: floor line away / toward | opposite: room | opposite: floor layer | opposite: floor line away / toward |
|---|---:|---:|---:|---:|---:|---:|
| 600-1200 | 20.70 | 20.13 | 0.0005 / 0.0018 | 20.46 | 18.28 | 0.0021 / 0.0068 |
| 1200-1800 | 20.85 | 20.34 | 0.0005 / 0.0012 | 20.54 | 18.39 | 0.0020 / 0.0070 |
| 1800-2400 | 20.91 | 20.46 | 0.0004 / 0.0005 | 20.57 | 18.42 | 0.0019 / 0.0072 |
| 2400-3000 | 20.94 | 20.53 | 0.0004 / 0.0003 | 20.58 | 18.42 | 0.0019 / 0.0071 |
| 3000-3600 | 20.95 | 20.57 | 0.0003 / 0.0003 | 20.58 | 18.43 | 0.0018 / 0.0071 |

## The floor layer against the room mean, 30 s windows (first 600 s)

| window (s) | window: floor below room mean (K) | opposite: floor below room mean (K) |
|---|---:|---:|
| 0-30 | 0.01 | 0.77 |
| 30-60 | 0.05 | 1.67 |
| 60-90 | 0.08 | 1.50 |
| 90-120 | 0.12 | 1.82 |
| 120-150 | 0.22 | 1.73 |
| 150-180 | 0.63 | 1.72 |
| 180-210 | 0.79 | 1.90 |
| 210-240 | 0.62 | 1.97 |
| 240-270 | 0.55 | 2.07 |
| 270-300 | 0.61 | 2.11 |
| 300-330 | 0.58 | 2.17 |
| 330-360 | 0.59 | 2.20 |
| 360-390 | 0.58 | 2.20 |
| 390-420 | 0.57 | 2.22 |
| 420-450 | 0.57 | 2.21 |
| 450-480 | 0.57 | 2.23 |
| 480-510 | 0.56 | 2.26 |
| 510-540 | 0.57 | 2.26 |
| 540-570 | 0.57 | 2.27 |
| 570-600 | 0.57 | 2.26 |

## Heat budget

Heat unaccounted for over each 7.5 s interval, W/m: the radiator plus the wall heat flux
less the rise in internal energy, (cv/R) times the integral of p (energyCheck).

| | mean | min | max |
|---|---:|---:|---:|
| window | -0.004 | -0.20 | +0.20 |
| opposite | -0.001 | -0.04 | +0.14 |
