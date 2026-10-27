# ebrains-tognolina-2020

An EBRAINS dataset migrated from the old HBP object storage (dataset version `7dc5d5d5-4323-41d6-bdfd-0b841cfe7000`, Tognolina et al., whole cell patch-clamp recordings of cerebellar granule cells). Bucket `p63ea6-hbp-d000017_PatchClamp-GranuleCells_pub`. Same layout as `ebrains-locatelli-2020-golgi`: `GrC_Subject<NN>_<ddMMyy>/` per animal, one ABF file per recording.

Provenance: the complete object listing of the public bucket (93 entries: 27 folders, 66 files; the bucket's empty folder objects are listed as folders). Entity meanings are quoted from `HBP-DataDescriptor_PatchGrCs.txt`. See `docs/validation/foreign-datasets.md`.

What it checks:

- File names with spaces, including two consecutive spaces (`090216_0002  IV -70.abf`), as the recording id and in a `{recording_id}` file pattern.
- The protocol read with a case-insensitive alternation that contains a space (`cc step`): 29 `cc step`, 20 `iv`, 15 `epsp`.
- Subject numbers with a gap: `Subject26` does not exist, so the walk yields 27 subjects (1-25, 27, 28) and 64 recordings without issues.
- File-name dates with dropped zeros (`18118007 CC step.abf` in `GrC_Subject16_180118`); the date is read from the folder.
- The data descriptor names a root folder `PatchClamp-Granule cells/`, a file `HBP_DataDescriptor_PatchGrCs.txt` and a licence `Licence (CCBY-SA).pdf`. The bucket has no such folder, and has `HBP-DataDescriptor_PatchGrCs.txt` and `Licence (CCBY-NC-SA).pdf`.
- Cells are not an entity, for the reason given in `ebrains-locatelli-2020-golgi` (gap **G4**). The data descriptor and the licence are `no-match` (gap **G1**).
