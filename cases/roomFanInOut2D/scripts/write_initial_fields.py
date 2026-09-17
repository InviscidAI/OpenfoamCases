#!/usr/bin/env python3
"""Write `0.orig/` — the initial fields, as readable ASCII.

The published results were produced from binary fields, which are exactly as correct and
completely unreadable. A case is published so that someone can check the boundary
conditions; `fanPressure` and `totalPressure` buried in a binary blob check nothing. These
are written as ASCII with identical values, verified against the originals by comparing
what OpenFOAM parses rather than what the files look like.

The room starts from rest: U = 0, p = 0, k = 1e-4, epsilon = 1e-5, nut = 0. The clip is the
flow establishing itself, so the initial state is a real modelling choice and not a
formality.

`--direction in|out` sets the one setting that differs between the two runs.
"""
import argparse
from pathlib import Path

HEADER = """FoamFile
{{
    version     2.0;
    format      ascii;
    class       {cls};
    location    "0";
    object      {obj};
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      {dims};

internalField   uniform {internal};

boundaryField
{{
{body}}}

// ************************************************************************* //
"""

WALLS = "walls", "furniture"


def field(obj, cls, dims, internal, per_patch) -> str:
    body = ""
    for patch in ("fan", "vent", *WALLS, "frontAndBack"):
        entries = per_patch[patch]
        body += f"    {patch}\n    {{\n"
        for k, v in entries:
            if v.lstrip().startswith("{"):
                # A sub-dictionary is not a keyword-value pair and takes no semicolon.
                body += f"        {k}\n        {v.strip()}\n"
            else:
                body += f"        {k:<16}{v};\n"
        body += "    }\n"
    return HEADER.format(cls=cls, obj=obj, dims=dims, internal=internal, body=body)


def fan_pressure(direction: str):
    return [("type", "fanPressure"), ("rho", "rho"), ("psi", "none"), ("gamma", "1"),
            ("p0", "uniform 0"), ("value", "uniform 0"), ("fanCurve", "table"),
            ("fanCurveCoeffs",
             '{\n            file            "<constant>/fanCurve.dat";\n        }'),
            ("direction", direction)]


def build(direction: str) -> dict[str, str]:
    empty = [("type", "empty")]
    out = {}

    out["U"] = field(
        "U", "volVectorField", "[ 0 1 -1 0 0 0 0 ]", "( 0 0 0 )",
        {"fan": [("type", "pressureInletOutletVelocity"), ("value", "uniform ( 0 0 0 )")],
         "vent": [("type", "pressureInletOutletVelocity"), ("value", "uniform ( 0 0 0 )")],
         "walls": [("type", "noSlip")], "furniture": [("type", "noSlip")],
         "frontAndBack": empty})

    out["p"] = field(
        "p", "volScalarField", "[ 0 2 -2 0 0 0 0 ]", "0",
        {"fan": fan_pressure(direction),
         "vent": [("type", "totalPressure"), ("rho", "rho"), ("psi", "none"),
                  ("gamma", "1"), ("p0", "uniform 0"), ("value", "uniform 0")],
         "walls": [("type", "zeroGradient")], "furniture": [("type", "zeroGradient")],
         "frontAndBack": empty})

    inlet_outlet = lambda inlet, val: [("type", "inletOutlet"),
                                       ("inletValue", f"uniform {inlet}"),
                                       ("value", f"uniform {val}")]
    out["k"] = field(
        "k", "volScalarField", "[ 0 2 -2 0 0 0 0 ]", "0.0001",
        {"fan": inlet_outlet("0.0135", "0.0001"), "vent": inlet_outlet("0.0135", "0.0001"),
         "walls": [("type", "kqRWallFunction"), ("value", "uniform 0.0001")],
         "furniture": [("type", "kqRWallFunction"), ("value", "uniform 0.0001")],
         "frontAndBack": empty})

    out["epsilon"] = field(
        "epsilon", "volScalarField", "[ 0 2 -3 0 0 0 0 ]", "1e-05",
        {"fan": inlet_outlet("0.0027", "1e-05"), "vent": inlet_outlet("0.0027", "1e-05"),
         "walls": [("type", "epsilonWallFunction"), ("blending", "stepwise"),
                   ("value", "uniform 1e-05")],
         "furniture": [("type", "epsilonWallFunction"), ("blending", "stepwise"),
                       ("value", "uniform 1e-05")],
         "frontAndBack": empty})

    out["nut"] = field(
        "nut", "volScalarField", "[ 0 2 -1 0 0 0 0 ]", "0",
        {"fan": [("type", "calculated"), ("value", "uniform 0")],
         "vent": [("type", "calculated"), ("value", "uniform 0")],
         "walls": [("type", "nutkWallFunction"), ("blending", "stepwise"),
                   ("value", "uniform 0")],
         "furniture": [("type", "nutkWallFunction"), ("blending", "stepwise"),
                       ("value", "uniform 0")],
         "frontAndBack": empty})
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--direction", choices=("in", "out"), required=True)
    ap.add_argument("--case", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--into", default="0.orig")
    a = ap.parse_args()
    target = a.case / a.into
    target.mkdir(parents=True, exist_ok=True)
    for name, text in build(a.direction).items():
        (target / name).write_text(text)
    print(f"wrote {target} with fan direction '{a.direction}'")
