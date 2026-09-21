`run.conf` is sourced by Allrun and read by `scripts/make_mesh_dicts.py`. Change policy
there, not in Allrun. A changed policy is a different comparison and requires revalidating
stock. `snappyHexMeshDict.template` contains region geometry and quality settings;
`make_mesh_dicts.py` inserts the levels from `run.conf` deterministically.
