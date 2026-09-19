# ebrains-locatelli-2020-golgi

An EBRAINS dataset migrated from the old HBP object storage (dataset version `17196b79-04db-4ea4-bb69-d20aab6f1d62`, Locatelli et al., whole cell patch-clamp recordings of cerebellar Golgi cells). Bucket `p63ea6-hbp-d000018_PatchClamp-GolgiCells_pub`, named by the dataset version's file repository in the Knowledge Graph. One folder per animal, `GoC_Subject<NN>_<ddMMyy>`, holds one ABF file per recording; the text data descriptor and the licence sit at the root.

Provenance: the complete object listing of the public bucket. The bucket also holds one empty object per folder, named like the folder without a trailing `/`; those are folders, not files, and the listing lists them as folders (26 entries: 7 folders, 19 files). Entity meanings are quoted from `HBP-DataDescriptor_PatchGolgCs.txt`. See `docs/validation/foreign-datasets.md`.

What it checks:

- A subject folder level above a `file` level where every file is its own entity.
- A `ddMMyy` date read from the folder name. The file names repeat the date but drop leading zeros in some files (`80419_0007_IV.abf` in `GoC_Subject01_080419`, `18419-A_0001_IV.abf` in `GoC_Subject05_180419`), so the folder is the source.
- The protocol read from the file name with a case-insensitive alternation and `normalize: lowercase`, validated by an `enum`: 8 `iv`, 9 `epsc`.
- The walk yields 7 subjects and 17 recordings without issues.
- Cells are not an entity. The descriptor marks a second cell of one animal with an `A`/`B` prefix, and a single cell with no prefix; a cell id with an optional part cannot be extracted without an `extraction-failed` issue on every unprefixed file (gap **G4**).
- The data descriptor and the licence are `no-match` (gap **G1**).
