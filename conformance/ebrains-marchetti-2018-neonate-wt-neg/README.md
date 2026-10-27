# ebrains-marchetti-2018-neonate-wt-neg

Marchetti et al., Spike time dependent plasticity (STDP) data from neonate C57BL/6 (wild-type) mice, negative pairing (dataset version `fc79175a-e044-4377-83ce-3401a9046f1a`). Same layout as `ebrains-marchetti-2018-adult-wt-pos`, in folder `MF-CA3-STDP-neonate-WT-negPairing/` of the shared bucket `p63ea6-hbp-00005`.

Provenance: the complete object listing of the dataset's folder (14 entries). See `docs/validation/foreign-datasets.md`.

What it checks:

- The walk yields 3 subjects and 3 samples without issues, and the samples equal the ones the descriptor's data registry lists.
- The part of a file name after `__` is the acquisition file name (`B18815010_C.txt`, `A2207150001_C.txt`), not the sample id, so the file patterns match only the `_C`/`_P` suffix the descriptor defines.
- The data descriptor is `no-match` (gap **G1**).
