# ebrains-marchetti-2018-adult-wt-pos

One of six EBRAINS dataset versions that share one bucket, each in its own folder (Marchetti et al., Spike time dependent plasticity (STDP) data from adult C57BL/6 (wild-type) mice, positive pairing; dataset version `7de840bb-78f3-41e1-b061-8f7f9e53ba76`). The dataset version's file repository in the Knowledge Graph is `p63ea6-hbp-00005?prefix=MF-CA3-STDP-adult-WT-posPairing/`, and cloning it creates only that folder. The layout is `MF-CA3-STDP-adult-WT-posPairing/Sbj<NNN>/<sample>/` with one control and one pairing recording per sample.

Provenance: the complete object listing of the dataset's folder in the public bucket (20 entries; the bucket's empty folder objects are listed as folders). Entity meanings are quoted from the data descriptor in the folder. See `docs/validation/foreign-datasets.md`.

What it checks:

- A dataset rooted at a folder of a shared bucket: the folder is a fixed level, and the other five datasets' folders are outside this listing.
- Subject and sample folders, with two required single-file kinds per sample (`_C.txt` control, `_P.txt` pairing).
- The walk yields 3 subjects and 5 samples without issues, and the samples equal the ones the descriptor's data registry lists.
- A sample id that carries the recording date in five or six digits (`A30216` in another of the six datasets, `A260216` here) is kept as a string; the date is not extracted.
- The data descriptor is `no-match` (gap **G1**).
