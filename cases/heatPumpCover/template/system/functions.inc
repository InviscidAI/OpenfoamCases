// All lightweight result data are written every 0.25 s independently of full-field writes.
velocityExtrema
{
    type fieldMinMax; libs (fieldFunctionObjects); fields (U); mode magnitude;
    writeToFile true; writeControl adjustableRunTime; writeInterval 0.25;
}
temperatureExtrema
{
    type fieldMinMax; libs (fieldFunctionObjects); fields (T); mode magnitude;
    writeToFile true; writeControl adjustableRunTime; writeInterval 0.25;
}
zoneMeans
{
    type volFieldValue; libs (fieldFunctionObjects); regionType cellZone;
    name fan; operation volAverage; writeFields false; fields (U T);
    writeToFile true; writeControl adjustableRunTime; writeInterval 0.25;
}
coilMeans
{
    type volFieldValue; libs (fieldFunctionObjects); regionType cellZone;
    name coil; operation volAverage; writeFields false; fields (U T);
    writeToFile true; writeControl adjustableRunTime; writeInterval 0.25;
}
resultPlanes
{
    type surfaces; libs (sampling); writeControl adjustableRunTime; writeInterval 0.25;
    surfaceFormat vtk; formatOptions { vtk { legacy true; compression false; } }
    fields (U T); interpolationScheme cellPoint;
    surfaces
    {
        coilIn  { type cuttingPlane; point (.2501 0 0); normal (1 0 0); bounds (.20 .300 -.01) (.34 1.040 .442); interpolate true; triangulate true; }
        coilOut { type cuttingPlane; point (.2899 0 0); normal (1 0 0); bounds (.20 .300 -.01) (.34 1.040 .442); interpolate true; triangulate true; }
        fanMid  { type cuttingPlane; point (.5500 0 0); normal (1 0 0); bounds (.45 .300 -.01) (.65 .975 .335); interpolate true; triangulate true; }
        unitTop { type cuttingPlane; point (0 1.040 0); normal (0 1 0); bounds (-.02 .95 -.02) (.80 1.13 .65); interpolate true; triangulate true; }
        unitBottom { type cuttingPlane; point (0 .300 0); normal (0 1 0); bounds (-.02 .20 -.02) (.80 .40 .65); interpolate true; triangulate true; }
        unitEnd { type cuttingPlane; point (0 0 .442); normal (0 0 1); bounds (-.02 -.02 .35) (.80 1.14 .54); interpolate true; triangulate true; }
        coverFrontLow { type cuttingPlane; point (.775 0 0); normal (1 0 0); bounds (.65 -.02 -.02) (.90 .040 .57); interpolate true; triangulate true; }
        coverFrontHigh { type cuttingPlane; point (.775 0 0); normal (1 0 0); bounds (.65 .020 -.02) (.90 1.14 .57); interpolate true; triangulate true; }
        coverSideLow { type cuttingPlane; point (0 0 .625); normal (0 0 1); bounds (-.02 -.02 .50) (.72 .040 .75); interpolate true; triangulate true; }
        coverSideHigh { type cuttingPlane; point (0 0 .625); normal (0 0 1); bounds (-.02 .020 .50) (.72 1.14 .75); interpolate true; triangulate true; }
    }
}
clipPlanes
{
    type surfaces; libs (sampling); writeControl adjustableRunTime; writeInterval .25;
    surfaceFormat vtk; formatOptions { vtk { legacy true; compression true; } }
    fields (T U); interpolationScheme cellPoint;
    surfaces
    {
        sym { type patch; patches (symmetry); interpolate false; }
        mid { type cuttingPlane; point (0 .670 0); normal (0 1 0); bounds (-.1 .5 -.1) (5.1 .8 3.1); interpolate false; triangulate true; }
    }
}
// Face-flux monitors (17 Oct 2026). On the hexahedral mesh the duct's cell-centred Ux is
// checkerboarded and its zone mean runs above the flow through it, so the fan's real flow and the
// coil's flow-weighted temperatures are taken from the face flux phi on oriented face zones.
fanFlux
{
    type surfaceFieldValue; libs (fieldFunctionObjects); regionType faceZone; name fanFaces;
    operation sum; fields (phi); writeFields false; writeToFile true;
    writeControl adjustableRunTime; writeInterval 0.25;
}
coilInFlux
{
    type surfaceFieldValue; libs (fieldFunctionObjects); regionType faceZone; name coilInFaces;
    operation sum; fields (phi); writeFields false; writeToFile true;
    writeControl adjustableRunTime; writeInterval 0.25;
}
coilInT
{
    type surfaceFieldValue; libs (fieldFunctionObjects); regionType faceZone; name coilInFaces;
    operation weightedAverage; weightField phi; fields (T); writeFields false; writeToFile true;
    writeControl adjustableRunTime; writeInterval 0.25;
}
coilOutT
{
    type surfaceFieldValue; libs (fieldFunctionObjects); regionType faceZone; name coilOutFaces;
    operation weightedAverage; weightField phi; fields (T); writeFields false; writeToFile true;
    writeControl adjustableRunTime; writeInterval 0.25;
}
#include "openFaces.inc"
#include "openBoundaryPlanes.inc"
