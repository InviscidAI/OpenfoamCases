openBoundaryPlanes
{
    type surfaces; libs (sampling); writeControl adjustableRunTime; writeInterval .25;
    surfaceFormat vtk; formatOptions { vtk { legacy true; compression false; } }
    fields (U T); interpolationScheme cellPoint;
    surfaces
    {
        openFarX { type patch; patches (openFarX); interpolate false; }
        openTop  { type patch; patches (openTop); interpolate false; }
        openFarZ { type patch; patches (openFarZ); interpolate false; }
    }
}
