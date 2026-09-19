# ebrains-locatelli-2020-stellate

An EBRAINS dataset migrated from the old HBP object storage (dataset version `3ca4af33-64bd-437a-9c53-2dac19e10168`, Locatelli et al., whole cell patch-clamp recordings of cerebellar stellate cells). Bucket `p63ea6-hbp-d000020_PatchClamp-StellateCells_pub`. Same layout as `ebrains-locatelli-2020-golgi`: `SC_Subject<NN>_<ddMMyy>/` per animal, one ABF file per recording.

Provenance: the complete object listing of the public bucket (74 entries: 16 folders, 58 files; the bucket's empty folder objects are listed as folders). Entity meanings are quoted from `HBP-DataDescriptor_PatchStellateCs.txt`. See `docs/validation/foreign-datasets.md`.

What it checks:

- The file names follow at least four conventions within one dataset (`080517_iv.abf`, `120318-1203000-iv.abf`, `131117-A_ccstep.abf`, `140318-1403003-EPSC_20 pulses.abf`), with spaces in some names. The recording id is the whole file stem, and the protocol is found anywhere in the name: 12 `iv`, 13 `gapfree`, 10 `ccstep`, 6 `epsp`, 15 `epsc`.
- The number of pulses and the stimulation frequency of an EPSC recording (`20 pulses100Hz`) are in the name but only for some files, so they are not extracted (gap **G4**).
- The walk yields 16 subjects and 56 recordings without issues.
- The data descriptor places its files in a folder `bp00sp01/` that the bucket does not have.
- Cells are not an entity, for the reason given in `ebrains-locatelli-2020-golgi` (gap **G4**). The data descriptor and the licence are `no-match` (gap **G1**).
