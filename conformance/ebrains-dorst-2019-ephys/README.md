# ebrains-dorst-2019-ephys

An EBRAINS dataset migrated from the old HBP object storage (dataset version `7d545473-405d-45f9-b0c4-05b627bf793a`, Dorst et al., electrophysiological recordings of a striatal cholinergic interneuron). Bucket `pc0a33-hbp-d000009_ChIN-ephys_pub`. Two copies of the same data in two formats: `2019Q3/` (ASCII `.dat` traces and the Igor Pro original) and `2019Q3_NWB/` (NWB), each laid out as `<release>/chin/<derived|original>/`.

Provenance: the complete object listing of the public bucket below the four roots (268 entries). Entity meanings from `HBP-DataDescriptor_ChIn-ephys.txt`. See `docs/validation/foreign-datasets.md`.

What it checks:

- Four data locations, one per branch and format (`derived`, `original`, `derived-nwb`, `original-nwb`; gap **G5**), and the one cell as one record complete in all four.
- One entity that is a folder in two locations and a file in the other two: `derived/<identity>/` holds the traces, while the original is a single file `original/<identity>.pxp` (or `.nwb`), where the descriptor promises a folder `original/<identity>/`.
- An identity with no parts the descriptor explains (`sbj4-170614_cell6_original__md_20170614_cell_5_6_ChIN`), used whole for the cell. Its start, `sbj4-170614`, is the subject: the EBRAINS Knowledge Graph lists it as the dataset version's subject, and `ebrains-dorst-2019-morphology` has a subject folder of that name.
- The descriptor lists itself as `HBP-DataDescriptor_SPN-mephys.txt`; the bucket has `HBP-DataDescriptor_ChIn-ephys.txt`.
