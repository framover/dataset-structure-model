# ebrains-marchetti-2018-neonate-wt-pos

Marchetti et al., Spike time dependent plasticity (STDP) data from neonate C57BL/6 (wild-type) mice, positive pairing (dataset version `49c02949-c98d-407b-ac20-732bccf0ea68`). Same layout as `ebrains-marchetti-2018-adult-wt-pos`, in folder `MF-CA3-STDP-neonate-WT-posPairing/` of the shared bucket `p63ea6-hbp-00005`.

Provenance: the complete object listing of the dataset's folder (20 entries). See `docs/validation/foreign-datasets.md`.

What it checks:

- The walk yields 3 subjects and 5 samples without issues, and the samples equal the ones the descriptor's data registry lists.
- The part of a file name after `__` is the acquisition file name (`A150715016_C.txt`), and one sample's files repeat the sample id as `B2107150` in folder `B210715`. The file patterns therefore match only the `_C`/`_P` suffix the descriptor defines.
- The data descriptor is `no-match` (gap **G1**).
