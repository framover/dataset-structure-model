# dandi-nwb-session-variants

A dandiset whose sessions are several NWB files distinguished by a BIDS-style `desc-` entity (layout of DANDI:000409, the IBL Brain Wide Map): `sub-<subject>/sub-<subject>_ses-<uuid>_desc-processed_behavior+ecephys+image.nwb` and, for sessions with raw data, `…_desc-raw_ecephys+image.nwb`. Provenance: the dandiset's asset naming as described by its conversion repository and the DANDI notebooks; see `docs/validation/foreign-datasets.md`.

What it checks:

- File-level entities whose identity is a 36-character UUID with hyphens, substituted regex-escaped into `{session_id}` tokens.
- Literal `+` in file names, escaped in the patterns.
- A required kind (`processed`) and an optional one (`raw`): session `3e6a97d3-…` has only the processed file and is complete; `c99d53e6-…` and `aad23144-…` have both.
- A partial download `….nwb.part` does not match the level and is `no-match`.
- `dandiset.yaml` at the root is `no-match` (gap **G1**).
