# dandi-nwb-subject-folders

A DANDI dandiset as the `dandi` CLI downloads it (layout of DANDI:000006): `dandiset.yaml` at the root, one folder per subject `sub-<label>/`, one NWB file per session `sub-<label>_ses-<label>.nwb`. Provenance: the asset paths of dandiset 000006 (`sub-anm369962/sub-anm369962_ses-20170309.nwb`, …) as listed by the DANDI archive; see `docs/validation/foreign-datasets.md`.

What it checks:

- A folder level (subject) above a `file` level (session): the session entity is one NWB file, and `{subject_id}` from the parent is substituted into the file pattern alongside the session's own `{session_id}`.
- A `pathComponentTemplate` with no `matchPattern` on the subject level, derived from `subject_id`'s `validation.pattern`.
- One field (`session_date`) read from the same text as the identity with a `valueFormat`.
- `dandiset.yaml` is a dataset-level file: nothing in the mapping can claim it, so it is `no-match`. See gap **G1** in the validation report.
- `sub-anm369963_ses-20170314_notes.txt` does not match the file level's pattern and is `no-match`.
