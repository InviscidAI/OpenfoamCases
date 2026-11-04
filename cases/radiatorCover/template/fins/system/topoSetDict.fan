FoamFile { version 2.0; format ascii; class dictionary; object topoSetDict.fan; }
// The fan bar under the radiator and the face zones that measure the air through it and
// through the convector. Both fins runs have them; in finsBare the fan zone is plain air.
// Fan: cells with centres x 0.0465-0.1165 m (edges 0.046-0.11729), y 0.126-0.150 m (8 rows of 3 mm).
actions
(
    { name fanCells; type cellSet; action new; source boxToCell;
      box (0.0465 0.126 -1) (0.1165 0.150 2); }
    { name fan; type cellZoneSet; action new; source setToCellZone; set fanCells; }

    // Bottom face of the fan zone: all the fan's air enters through it (normal +y).
    { name fanInFaces; type faceSet; action new; source boxToFace;
      box (0.0465 0.1255 -1) (0.1165 0.1265 2); }
    { name fanIn; type faceZoneSet; action new; source setToFaceZone; faceSet fanInFaces; }

    // Bottom and top of the convector zone, x 0.040-0.103 (normal +y).
    { name convInFaces; type faceSet; action new; source boxToFace;
      box (0.0401 0.1495 -1) (0.1029 0.1505 2); }
    { name convIn; type faceZoneSet; action new; source setToFaceZone; faceSet convInFaces; }
    { name convOutFaces; type faceSet; action new; source boxToFace;
      box (0.0401 0.7495 -1) (0.1029 0.7505 2); }
    { name convOut; type faceZoneSet; action new; source setToFaceZone; faceSet convOutFaces; }
);
