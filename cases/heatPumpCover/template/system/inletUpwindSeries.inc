// The cells one cell upstream of the coil's inlet face (x = 0.2445 m, cell values) at every write:
// the air entering the coil before the coil touches it. open and covered sampled this plane only
// at 50, 55 and 60 s, after the solve (system/inletUpwindDict); the three covers' runs include it.
inletUpwindSeries
{
    type surfaces; libs (sampling); writeControl adjustableRunTime; writeInterval 0.25;
    surfaceFormat vtk; formatOptions { vtk { legacy true; compression false; } }
    fields (T U); interpolationScheme cell;
    surfaces
    {
        up1 { type cuttingPlane; point (.2445 0 0); normal (1 0 0); bounds (.20 .3125 -.01) (.30 1.0275 .430); interpolate false; }
    }
}
