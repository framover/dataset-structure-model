# allen-ecephys-cache

The directory an AllenSDK `EcephysProjectCache` builds for the Visual Coding Neuropixels data: `manifest.json` and the tables `sessions.csv`, `probes.csv`, `channels.csv`, `units.csv` at the root, one folder `session_<id>/` per downloaded session holding `session_<id>.nwb` and one `probe_<id>_lfp.nwb` per probe whose LFP was fetched. Provenance: the AllenSDK data-access documentation and the cache manifest keys (`session_%d`, `session_%d.nwb`, `probe_%d_lfp.nwb`); see `docs/validation/foreign-datasets.md`.

What it checks:

- Integer identities (`session_id`, `probe_id`), a folder level above a file level, and a session with probe files but no session file (`721123822` → `missing-required-file`).
- **Gap G2 (files of an outer entity):** `session_715093703.nwb` is the session's required file *and* `no-match` at the probe file level, where every file is expected to be a probe. Two entity types share one folder, one as the folder's owner and one as files, and the model cannot say so.
- The root tables are `no-match` (gap **G1**).
