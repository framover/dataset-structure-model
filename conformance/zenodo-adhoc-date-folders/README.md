# zenodo-adhoc-date-folders

An ad-hoc deposit (layout of Zenodo record 10558021, hippocampal astrocyte imaging): the landing page says the raw data are in the folder `2023-05-11` and that each subfolder holds the three simultaneously acquired imaging planes as `.tif` files. The recording folder names (`spontaneous_1`, `opto_1`, …), the README, the processed traces file and the stray `Thumbs.db` are reconstructed, not transcribed; see `docs/validation/foreign-datasets.md`.

What it checks:

- A dataset with a single entity type and no subject: the recording is the root of its own hierarchy.
- A structural date level as the top level, read into `recording_date`.
- `condition` with an `enum` validation and `recording_number` as an integer, both parsed from one folder name.
- **Gap G11 (exact cardinality):** every recording should have exactly three planes. `cardinality` is `one` or `many`, so `spontaneous_2` with two planes is complete and carries no issue.
- `stim_times.csv` inside `opto_1/` matches no pattern and is covered silently; `Thumbs.db`, `README.txt` and `processed_traces.mat` are `no-match` (gap **G1**).
