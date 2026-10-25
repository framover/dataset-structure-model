# allen-ecephys-cache

The directory an AllenSDK `EcephysProjectCache` builds for the Visual Coding Neuropixels data: `manifest.json` and the tables `sessions.csv`, `probes.csv`, `channels.csv`, `units.csv` at the root, one folder `session_<id>/` per downloaded session holding `session_<id>.nwb` and one `probe_<id>_lfp.nwb` per probe whose LFP was fetched. Provenance: the AllenSDK data-access documentation and the cache manifest keys (`session_%d`, `session_%d.nwb`, `probe_%d_lfp.nwb`); see `docs/validation/foreign-datasets.md`.

What it checks:

- Integer identities (`session_id`, `probe_id`), a folder level above a file level, and a session with probe files but no session file (`721123822` → `missing-required-file`).
- **Files of an outer entity (G2):** `session_715093703.nwb` is the session's required file. Two entity types share one folder, one as the folder's owner and one as files; the session's `filePatterns` claim its file first, so it is not offered to the probe level and is not `unmatched`.
- The root tables are `no-match` (gap **G1**).
