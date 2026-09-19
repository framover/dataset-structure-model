# zenodo-adhoc-flat-mat

An ad-hoc flat deposit (layout of Zenodo record 13941450, mouse auditory responses): `Data_<area><part>.mat` with the responses of every ROI or unit of a brain area (the AC data split in `Data_AC1.mat` and `Data_AC2.mat` because of the upload size limit), `Clusters_<area>.mat`, `AnatInfo_<area>.mat`. Provenance: the record's landing-page description; see `docs/validation/foreign-datasets.md`.

What it checks:

- The smallest possible layout: one `file` level at the root, entities keyed by a code in the middle of the file name, with an `enum` validation.
- A required kind split across numbered parts (`cardinality: many`) next to single-file kinds.
- `README.md` at the root is `no-match` (gap **G1**).
