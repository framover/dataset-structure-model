# ebrains-kozlov-2019-projection-neurons

An EBRAINS dataset migrated from the old HBP object storage (dataset version `e0cfa3fb-22d2-48c7-bb4c-a6374bfc848b`, Kozlov et al., electrophysiological recordings of striatal projection neurons). Bucket `pc0a33-hbp-d000003_SPN-ephys_pub`. The data descriptor's layout is `2019Q3/<cell type>/<analysis|derived|original>/<identity>/`, with the cell types `dspn` and `ispn`.

Provenance: the object listing of the public bucket, 6,131 entries below the six roots. The committed listing keeps every folder and the first 6 files of each folder (161 entries). The full listing walks to the same 8 cells and 6 experiments without issues or unmatched entries. Entity meanings are quoted from `HBP-DataDescriptor_SPN-ephys.txt`. See `docs/validation/foreign-datasets.md`.

What it checks:

- The branching workaround of gap **G5**: one data location per branch (`analysis`, `derived`, `original`), each with one root per cell-type folder (`dspn`, `ispn`). The descriptor, the licence and the `2019Q3/` level are outside every root.
- Cross-location matching: each cell is one record spanning `analysis` and `derived`, keyed by the folder name `<yymmdd>_c<N>_<D1|D2>`, with the date and the dopamine receptor read from it.
- Two entity types that name the same neurons differently. `analysis/` and `derived/` hold one folder per cell; `original/` holds one folder per experiment, named by the date, the range of cell numbers and the list of receptors (`150917_c9_11_D1_D1_D2` is cells 9, 10 and 11). The records of cell `150917_c10_D1` and experiment `150917_c9_11_D1_D1_D2` are not linked, because a cell's experiment cannot be read from the cell's name (gap **G18**).
- The same experiment stored twice: `150917_c9_11_D1_D1_D2` (888 files) is under both `dspn/original/` and `ispn/original/`, because it holds cells of both types. It is one experiment record with both roots in its `locations`, and no issue is raised.
- Folders of derived traces named `<condition>_<protocol>_ch<N>_<sweep>.dat` as a `cardinality: many` pattern; six named analysis outputs per cell (`<identity>-features.json`, `-protocols.json`, `-spec.json`, `-sum.json`, `-figs.pdf`, `<identity>.ipynb`).
