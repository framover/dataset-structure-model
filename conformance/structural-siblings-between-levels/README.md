# structural-siblings-between-levels

A scanning day whose files are split by kind into sibling folders (the layout of the fMRI part of `ebrains-murris-2021`): `<monkey>/d<N>/funct/` holds each run as a NIfTI and a JSON sidecar, `timing/` one SPM timing file per run, `struct/` the day's anatomical scan, and `logs/` is empty.

What it checks:

- **Files of one entity pooled across sibling structural folders.** The structural level `kinds` sits between the session and the file level. Run 1's `paths` are its two files in `funct/` and its timing file in `timing/`: the record key `(entityType, identity, parents)` does not see structural levels, so files with one identity under one session are one entity wherever the structural folder puts them. `files` candidates are the entity's own paths, so the `timing` pattern finds the `.mat` in `timing/`.
- **A structural folder with nothing an entity accounts for is `no-match` itself.** `struct/` matches the `kinds` level but its scan does not match the run level; the folder is the topmost unmatched entry and the scan is implied. `logs/` is empty and is reported the same way.
- A run with no timing file (run 2) is complete, since `timing` is optional.
