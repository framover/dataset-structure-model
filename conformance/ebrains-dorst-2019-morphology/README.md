# ebrains-dorst-2019-morphology

An EBRAINS dataset in the curated HBP folder format (dataset version `f25ec9c9-2348-4a62-a6af-907d389f263d`, Dorst et al., cholinergic interneurons in the striatum: single cell patch clamp recordings with morphological reconstructions). Bucket `p63ea6-hbp-00940`: `ephy-ChIN-STR/sbj<N>-<yymmdd>/cell<N>[_<M>]/{original,derived}/hbp-00940_ephy-ChIN-STR_<subject>_<cell>_<branch>__<original file name>`.

Provenance: the complete object listing of the public bucket (43 objects, one of them an empty folder object, so 42 files). Entity meanings and the file registry are quoted from `00_hbp-00940_ephy-ChIN-STR__DataDescriptor.md`. See `docs/validation/foreign-datasets.md`.

What it checks:

- A subject level whose name carries the subject number and the recording date (`sbj1-160504`), above a cell level. The whole name is the subject identity, as in the EBRAINS Knowledge Graph.
- Files in subfolders of the innermost entity folder (`cell3/original/*.pxp`, `cell3/derived/*.mat`). File patterns match direct children only, so the recording, the slice picture, the spatial registration and the MAT traces cannot be named or required; the folders are listed in `additionalFolders` and their files are covered without appearing in `files` (gap **G12**). The descriptor's registry promises a `.pxp`, `.tif`, `.DAT` and `.xml` in `original/` and a `.mat` in `derived/` for every cell. The bucket has a `.DAT` for `cell3` only and a `derived/` folder for 4 of the 10 cells, which a reader could only report if those patterns could be declared.
- The walk yields 4 subjects and 10 cells without issues.
- Names inside the cell folders disagree with the folders: in `sbj3-170627` the recordings are `md_20170524_cell_6_ChIN.pxp` and `md_20170524_cell_7_ChIN.pxp`, dated a month before the subject folder; `sbj2-160505/cell7` holds `md_20160505_cell_1_2_ChIN`; and `sbj4-170614/cell5` and `cell6` each hold a copy of `md_20170614_cell_5_6_ChIN.pxp`.
- `sbj4-170614/cell6` is the one cell of `ebrains-dorst-2019-ephys`, whose identity is `sbj4-170614_cell6_original__md_20170614_cell_5_6_ChIN`. The two dataset versions describe the same neuron under different identities, and no config can say so: identity is matched within one config only.
- The two copies of the data descriptor (`.md` and `.txt`) and the spatial metadata spreadsheet are `no-match` (gap **G1**).
