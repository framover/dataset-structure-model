# ebrains-kozlov-2019-fast-spiking

An EBRAINS dataset migrated from the old HBP object storage (dataset version `02f1aec9-c709-4dd3-8929-3833569078eb`, Kozlov et al., electrophysiological recordings of striatal fast-spiking interneurons). Bucket `pc0a33-hbp-d000005_FS-ephys_pub`. Same layout as `ebrains-kozlov-2019-projection-neurons`, with one cell type, `fs`, and the same identity `<yymmdd>_FS<N>` in all three branches.

Provenance: the object listing of the public bucket, 1,782 entries below the three roots. The committed listing keeps every folder and the first 6 files of each folder (84 entries). The full listing walks to the same 4 cells without issues or unmatched entries. The data descriptor is `EBRAINS-DataDescriptor_02f1aec9-c709-4dd3-8929-3833569078eb.pdf`. See `docs/validation/foreign-datasets.md`.

What it checks:

- Three data locations (`analysis`, `derived`, `original`), one per branch (gap **G5**), and each of the 4 cells as one record complete in all three.
- The descriptor calls the cells "the 4 subjects FS1, FS2, FS5, FS16" and lists itself as `HBP-DataDescriptor_SPN-mephys.txt`, the name of another dataset's descriptor.
