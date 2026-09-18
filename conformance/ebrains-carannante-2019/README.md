# ebrains-carannante-2019

An EBRAINS dataset migrated from the old HBP object storage (dataset version `495de3d5-f9d5-4a4a-acd2-4ade0eaefb22`, Carannante et al., electrophysiological recordings of a striatal low-threshold spiking interneuron). Bucket `pc0a33-hbp-d000007_LTS-ephys_pub`. Same two-format layout as `ebrains-dorst-2019-ephys`, with the cell type `lts` and the one cell `Experiment-9862`.

Provenance: the complete object listing of the public bucket below the four roots (222 entries). Entity meanings from `HBP-DataDescriptor_LTS-ephys.txt`. See `docs/validation/foreign-datasets.md`.

What it checks:

- Four data locations, one per branch and format (gap **G5**), and the one cell as one record complete in all four.
- The descriptor lists itself as `HBP-DataDescriptor_SPN-mephys.txt`, the name used in the other striatal datasets; the bucket has `HBP-DataDescriptor_LTS-ephys.txt`.
- Here the original is a folder as the descriptor says (`original/Experiment-9862/20181211_7_8_slice_L4_long.pxp`). The recording date and slice are in that file's name only, not in the identity, so they are not extracted (gap **G10**).
