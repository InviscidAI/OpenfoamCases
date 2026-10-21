"""Every physical number of the cabin case, with where it comes from. The README gives the full sources.

Per-metre values: the section is one cell deep and 1 m thick, and stands for a cabin 1.45 m wide
(VW Golf 8: 1,471 mm front and 1,440 mm rear interior width), so a whole-car rate is divided by
WIDTH to give the rate per metre of section.
"""
import math

C2K = 273.15
WIDTH = 1.45                      # m, cabin width

# ---------------------------------------------------------------- the morning
T_OUT = 3.0 + C2K                 # Met Office 1991-2020, Heathrow: mean daily minimum Dec 3.1, Jan 2.7, Feb 2.7 C
RH_OUT = 0.90                     # a damp winter morning; assumed, no climate figure found
P_ATM = 1.0e5

# ---------------------------------------------------------------- the occupants (two, seated)
OCC_MOIST = 70.0 / 3600e3         # kg/s each: EU Regulation 672/2010, Annex II 2.2.6 (70 +/- 5 g/h per
                                  # observer); ASHRAE "seated, very light work" latent 45 W is 66 g/h
OCC_HEAT = 72.0                   # W each, sensible: ASHRAE Fundamentals Table 1, seated very light work
N_OCC = 2
# Where the water goes: a share at the breath, the rest through the skin of the upper
# body. The share is ISO 7730's (Fanger 1970) split of a person's latent heat, as implemented in Berkeley
# CBE's pythermalcomfort (_pmv_ppd_optimized.py): skin diffusion 3.05e-3 (5733 - 6.99 M - pa), sweating
# 0.42 (M - 58.15), respiration 1.7e-5 M (5867 - pa), W/m2 with pa in Pa. M is the ASHRAE table's
# 72 + 45 W over the 1.8 m2 of a standard adult.
MET_W_M2 = (72.0 + 45.0) / 1.8


def breath_share(pa):
    skin = 3.05e-3 * (5733 - 6.99 * MET_W_M2 - pa) + 0.42 * max(MET_W_M2 - 58.15, 0)
    resp = 1.7e-5 * MET_W_M2 * (5867 - pa)
    return resp / (resp + skin)


BREATH_SHARE = 0.25               # breath_share(): 0.253 in the starting cabin (pa 0.79 kPa), 0.248 at
                                  # 2.2 kPa (recirculation's cabin at ten minutes)
# the breath leaves the nose and mouth into a disc of air in front of the face (no jet), and the skin's
# water into the cells touching the torso, neck and head (geometry.py's primitives, with a margin)
BREATH_R = 0.03                   # m, the disc's radius; its centre 0.04 m ahead of the face at mouth height
BREATH = {"driver": (1.405 - 0.105 - 0.04, 0.975), "passenger": (2.185 - 0.10 - 0.04, 0.99)}
UPPER = {  # (segment or centre, radius) of the upper body's primitives, geometry.py
    "driver": [((1.21, 0.40), (1.37, 0.80), 0.115), ((1.38, 0.82), (1.40, 0.92), 0.05), ((1.405, 1.005), None, 0.105)],
    "passenger": [((2.05, 0.43), (2.16, 0.82), 0.11), ((2.17, 0.84), (2.18, 0.93), 0.05), ((2.185, 1.02), None, 0.10)],
}
UPPER_MARGIN = 0.03               # m beyond the surface: the touching cells' centres lie within 10-20 mm of it
# Skin against a seat back or headrest gives its water to the seat, not to the air: the skin cells within
# SEAT_GAP of these surfaces carry none (without this, a pilot put a still pocket of mist behind the
# driver's head and another behind the rear passenger's back). (segment, radius) of geometry.py's seat primitives.
SEAT_GAP = 0.025
SEATS = [((1.565, 1.00), (1.585, 1.09), 0.05),      # front headrest
         ((1.36, 0.32), (1.55, 0.93), 0.065),       # front backrest
         ((2.32, 0.90), (2.10, 0.34), 0.0)]         # rear seat back (the outline's face)

# ---------------------------------------------------------------- the defroster
Q_DEFROST = 0.100                 # m3/s through the HVAC unit in defrost mode: Volvo V40, SAE J902A test
                                  # (Sadananda, Chalmers MSc thesis 2016: "approximately 100 l/s")
T_COOLANT = 85.0 + C2K            # warm engine; heater-core coolant 80-95 C in normal running
EPS_HEATER = 0.6                  # heater-core effectiveness: outside air at 3 C leaves at 52 C, inside the
                                  # 46-60 C (115-140 F) usual at the vents on full heat
DUCT_W = 0.025                    # m, the defrost slot across its jet (geometry.py)

# ---------------------------------------------------------------- the glass
# windscreen: 2.1 mm glass + 0.76 mm PVB + 2.6 mm glass (Volvo's, Chalmers thesis), glass 2500 kg/m3,
# 750 J/kgK, 0.8 W/mK; PVB 1000 kg/m3, 1980 J/kgK, 0.2 W/mK (the thesis's table 3.3)
R_WIND = (0.0021 + 0.0026) / 0.8 + 0.00076 / 0.2
C_WIND = 2500 * 750 * (0.0021 + 0.0026) + 1000 * 1980 * 0.00076
# rear screen: one 3.2 mm toughened pane, the same glass (assumed thickness)
R_REAR = 0.0032 / 0.8
C_REAR = 2500 * 750 * 0.0032
H_OUT = 25.0                      # W/m2K outside: ISO 6946's external surface resistance Rse = 0.04 m2K/W
R_SI = 0.13                       # m2K/W inside, ISO 6946 Rsi for horizontal flow: only for the glass's
                                  # starting temperature in still air

# ---------------------------------------------------------------- the trim
# dash, seats, headliner, floor: a 3 mm skin of polypropylene (900 kg/m3, 1900 J/kgK) on insulation,
# so it stores heat and passes none outward
C_TRIM = 900 * 1900 * 0.003

# ---------------------------------------------------------------- the fog
FILM0 = 0.010                     # kg/m2 at t = 0 (10 um of water) on both screens; see the README
FILM_CLEAR = 1e-5                 # kg/m2: a face counts as misted while more than this is left (0.1% of FILM0)

# ---------------------------------------------------------------- the start
T0 = T_OUT + 2.0                  # cabin air and trim at t = 0

# ---------------------------------------------------------------- what the section does not hold
# The section is the cabin averaged across its width, so the two side walls lie against every cell of
# air, 2/WIDTH m2 of wall per m3 of cabin. Above the beltline and between the pillars they are side
# glass, elsewhere door and pillar trim. Surface resistances are ISO 6946's (via secondary sources; the
# standard is paywalled): Rsi 0.13 m2K/W for horizontal heat flow (convective part 2.5 W/m2K), 0.10
# upward; Rse 0.04; an unventilated air layer of 25 mm or more 0.18 horizontal, 0.16 upward.
SIDE_PER_VOL = 2 / WIDTH          # m2 of side wall per m3 of cabin
H_SI = 1 / 0.13                   # W/m2K, heat between the cabin's air and a side wall
H_CI = 2.5                        # W/m2K, its convective part: the vapour to the side glass, h_c/cp
# side glass: one toughened pane, 3.1 mm (US 9,950,945 B2: air-quenched side glass 2.5-3.1 mm)
C_SIDEGLASS = 2500 * 750 * 0.0031
R_SIDEGLASS = 0.0031 / 0.8 + 1 / H_OUT
# doors and pillars: the 3 mm trim skin, the cavity behind it, the steel skin, the outside air
C_DOOR = C_TRIM
R_DOOR = 0.003 / 0.2 + 0.18 + 1 / H_OUT
# the roof: the headliner, the cavity above it, the steel roof (heat flowing up)
R_ROOF = 0.003 / 0.2 + 0.16 + 1 / H_OUT
R_SI_UP = 0.10
# the beltline and the pillars in side view (x rearward from the windscreen's foot, y up from the floor)
BELT = ((0.03, 0.80), (2.58, 0.94))   # from the windscreen's foot to the rear screen's foot
A_PILLAR = 0.07                   # m behind the windscreen's line
C_PILLAR = 0.30                   # m ahead of the rear screen's line (a hatchback's broad C-pillar)
B_PILLAR = (1.28, 1.36)           # x range of the B-pillar
FRAME = 0.04                      # m of door frame below the headliner
# the cabin's contents the section cannot hold (seats across the width, carpet, console, door
# pockets, the headliner's fabric): a heat capacity per m3 of cabin, spread over the whole cabin as
# Brusey et al.'s single cabin node is, in step with the air within TAU_CONTENTS. (Put below the
# beltline only, it left the upper cabin 3.5 K too warm at 10 s in a pilot.)
# Its size is set so the section's mean air temperature over the first two minutes follows Brusey et
# al.'s cabin model, fitted to a Jaguar XJ's measured warm-up in MIRA's climatic wind tunnel
# (Mechatronics 50, 2018; arXiv 1704.07899): their cabin node holds k = 8 times its air's capacity.
# scripts/warmup_reference.py writes the reference; the README gives the pilots that set the size.
CONTENTS_X = 10.0                 # times the air's heat capacity, over the whole cabin's volume (pilots: README)
TAU_CONTENTS = 10.0               # s
CONTENTS_ZONE = "all"             # "low": below the beltline only; "all": the whole cabin
RHO_CP_AIR = 1.27 * 1005.0
TS0_GLASS = T_OUT + (T0 - T_OUT) * R_SIDEGLASS / (R_SIDEGLASS + 1 / H_SI)
TS0_DOOR = T_OUT + (T0 - T_OUT) * R_DOOR / (R_DOOR + 1 / H_SI)
TS0_ROOF = T_OUT + (T0 - T_OUT) * R_ROOF / (R_ROOF + R_SI_UP)


def e_sat(T):
    """Saturation vapour pressure over water, Pa (Buck 1981), T in K."""
    t = T - C2K
    return 611.21 * math.exp((18.678 - t / 234.5) * (t / (257.14 + t)))


def w_sat(T, p=P_ATM):
    """Specific humidity at saturation, kg vapour per kg of moist air."""
    e = e_sat(T)
    return 0.622 * e / (p - 0.378 * e)


def w_of(T, rh, p=P_ATM):
    e = rh * e_sat(T)
    return 0.622 * e / (p - 0.378 * e)


R_GAS = 8314.47 / 28.96
RHO_OUT = P_ATM / (R_GAS * T_OUT)
MDOT = Q_DEFROST * RHO_OUT / WIDTH                # kg/s per metre of section
T_SUP_OUT = T_OUT + EPS_HEATER * (T_COOLANT - T_OUT)
W_OUT = w_of(T_OUT, RH_OUT)
TG0_WIND = T_OUT + (T0 - T_OUT) * (R_WIND + 1 / H_OUT) / (R_WIND + 1 / H_OUT + R_SI)
TG0_REAR = T_OUT + (T0 - T_OUT) * (R_REAR + 1 / H_OUT) / (R_REAR + 1 / H_OUT + R_SI)
W0 = w_sat(TG0_WIND)                              # the cabin air is saturated at the windscreen: it has just fogged
MOIST_PER_M = N_OCC * OCC_MOIST / WIDTH           # kg/s per metre, both occupants
BREATH_PER_M_EACH = BREATH_SHARE * OCC_MOIST / WIDTH          # kg/s per metre, each occupant's breath
SKIN_PER_M_EACH = (1 - BREATH_SHARE) * OCC_MOIST / WIDTH      # kg/s per metre, each occupant's upper body

# ---------------------------------------------------------------- mist
# Air above saturation condenses into droplets in the air: in liquid clouds the supersaturation relaxes
# with a "time of phase relaxation" of 1-10 s (Korolev and Mazin, J. Atmos. Sci. 60, 2003, section 8),
# short against the cabin's flow, so each step any vapour above saturation becomes mist at once
# (saturation adjustment, with the latent heat given to the air), and mist evaporates again wherever the
# air is below saturation. The mist is carried with the air (droplets of a few micrometres follow it), and
# is not deposited on the trim. A heater evaporates the mist it draws in on recirculation.
R_VAP = 461.5
CP_AIR = 1005.0
HEAT_PER_M_EACH = OCC_HEAT / WIDTH                # W per metre for each drawn occupant

# vapour in air: D = 2.5e-5 m2/s at about 20 C; mu = 1.8e-5 Pa s, rho 1.2 -> Sc = 0.60
MU = 1.8e-5
ALPHA_D = 1 / 0.60                # D rho = alphaD mu
ALPHA_DT = 1 / 0.85               # turbulent Schmidt number as T's Prandtl, 0.85

if __name__ == "__main__":
    print(f"outside {T_OUT - C2K:.1f} C RH {RH_OUT:.0%}: w {W_OUT * 1e3:.3f} g/kg")
    print(f"defroster {Q_DEFROST * 1e3:.0f} l/s -> {MDOT:.5f} kg/s per m, outside-air supply {T_SUP_OUT - C2K:.1f} C, "
          f"slot speed {MDOT / (1.08 * DUCT_W):.2f} m/s at 52 C")
    print(f"windscreen R {R_WIND:.5f} m2K/W C {C_WIND:.0f} J/m2K; rear R {R_REAR:.5f} C {C_REAR:.0f}; trim C {C_TRIM:.0f}")
    print(f"start: air {T0 - C2K:.1f} C, windscreen {TG0_WIND - C2K:.2f} C, rear {TG0_REAR - C2K:.2f} C, "
          f"w0 {W0 * 1e3:.3f} g/kg (RH {W0 / w_sat(T0):.0%} at {T0 - C2K:.0f} C)")
    print(f"occupants: {MOIST_PER_M * 3600e3:.1f} g/h per m, {HEAT_PER_M_EACH:.1f} W per m each")
    for pa in (790.0, 1500.0, 2200.0):
        print(f"breath share at pa {pa:.0f} Pa: {breath_share(pa):.3f}")
    print(f"each occupant: breath {BREATH_PER_M_EACH * 3600e3:.2f} g/h per m, upper body {SKIN_PER_M_EACH * 3600e3:.2f} g/h per m")
