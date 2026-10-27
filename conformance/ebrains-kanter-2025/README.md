# ebrains-kanter-2025

A recent EBRAINS dataset in a bucket named by its dataset version (`885b4936-9345-43bd-880e-eebc19898ded`, Kanter et al., electrophysiological recordings from entorhinal cortex and hippocampus in freely behaving adult male rats). Layout per the data descriptor: `data/<subject_id>/<subject_id>_<session-date_time>.nwb`, `scripts/`, `docs/index.json`.

Provenance: the complete object listing of the public bucket (58 objects). The layout and the file meanings are quoted from `data-descriptor_eebc19898ded.pdf`. See `docs/validation/foreign-datasets.md`.

What it checks:

- A fixed `data` level, a subject folder level and a file-level session entity, the `{subject_id}` and `{session_id}` tokens together in one pattern.
- A date written with an English month abbreviation (`26863_2020-Nov-04_12-46-06.nwb`). The portable `valueFormat` tokens have no month name, so `session_date` is kept as text; the time is typed with `HH-mm-ss` (gap **G19**). The same names do not sort in time order: `27285_2021-Jul-01…` sorts before `27285_2021-Jun-30…`.
- The walk yields 9 subjects and 53 sessions without issues. The descriptor reports nine rats.
- `docs/index.json` lists the tasks in each file, which is metadata of the session held in a file of the dataset (gap **G1**; a reader could only use it through the DRAFT `sidecar` method, and it covers all sessions in one file).
- The data descriptor, the licence, `docs/` and `scripts/` are `no-match` (gap **G1**).
