# bids-multimodal-sessions

A BIDS dataset with sessions and several datatypes (layout of OpenNeuro ds000117, multimodal face processing): `sub-XX/ses-YY/<datatype>/sub-XX_ses-YY[_task-..][_run-..][_acq-..]_<suffix>.<ext>` with sidecar `.json` and `_events.tsv` files sharing the stem, `sub-XX_ses-YY_scans.tsv` in the session folder, `dataset_description.json`, `participants.tsv`, `README`, `CHANGES` at the root, and `derivatives/` beside the subjects. Provenance: the BIDS specification (common principles) and the ds000117 dataset page; see `docs/validation/foreign-datasets.md`.

What it checks:

- A structural `datatypes` level with an alternation pattern between the session and the file level.
- File-level entities keyed by the file-name stem, so a data file and its sidecars are one acquisition.
- `datatype` read from the structural level above; `suffix`, `task` and `run` read from the file name.
- **Gap G4 (optional fields):** `task` and `run` are legitimately absent from anatomical scans, but a field with a rule and no `defaultValue` raises `extraction-failed`. The T1w acquisitions carry that issue although nothing is wrong.
- **Gap G2 (files of an outer entity):** `sub-01_ses-meg_scans.tsv` is in the session's `files` and also `no-match`.
- **Gap G6 (files belonging to an ancestor inside a descendant folder):** `sub-01_ses-meg_coordsystem.json` and `_headshape.pos` are session-level MEG files placed in `meg/`. They become an acquisition `sub-01_ses-meg` with `missing-required-file`, because the file level can only assign files to entities of its own type.
- `derivatives/` and the root files are `no-match` (gaps **G1**, **G5**).
