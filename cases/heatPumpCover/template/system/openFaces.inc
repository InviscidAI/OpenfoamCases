// Exact gross flows (17 Oct 2026, written by scripts/make_open_faces.py): phi oriented outward,
// out = (sumMag + sum)/2, in = (sumMag - sum)/2.
behindTop_sum { type surfaceFieldValue; libs (fieldFunctionObjects); regionType faceZone; name behindTop; operation sum; fields (phi); writeFields false; writeToFile true; writeControl adjustableRunTime; writeInterval 0.25; }
behindTop_sumMag { type surfaceFieldValue; libs (fieldFunctionObjects); regionType faceZone; name behindTop; operation sumMag; fields (phi); writeFields false; writeToFile true; writeControl adjustableRunTime; writeInterval 0.25; }
behindBottom_sum { type surfaceFieldValue; libs (fieldFunctionObjects); regionType faceZone; name behindBottom; operation sum; fields (phi); writeFields false; writeToFile true; writeControl adjustableRunTime; writeInterval 0.25; }
behindBottom_sumMag { type surfaceFieldValue; libs (fieldFunctionObjects); regionType faceZone; name behindBottom; operation sumMag; fields (phi); writeFields false; writeToFile true; writeControl adjustableRunTime; writeInterval 0.25; }
behindEnd_sum { type surfaceFieldValue; libs (fieldFunctionObjects); regionType faceZone; name behindEnd; operation sum; fields (phi); writeFields false; writeToFile true; writeControl adjustableRunTime; writeInterval 0.25; }
behindEnd_sumMag { type surfaceFieldValue; libs (fieldFunctionObjects); regionType faceZone; name behindEnd; operation sumMag; fields (phi); writeFields false; writeToFile true; writeControl adjustableRunTime; writeInterval 0.25; }
