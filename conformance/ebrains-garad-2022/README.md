# ebrains-garad-2022

An EBRAINS dataset in a bucket of its own whose name is not the dataset version id: dataset version `07554ebd-95a2-46f0-8065-d961d56ce098` (Garad and Lessmann, excitability of mouse hippocampal CA1 pyramidal neurons during sustained strong depolarization) is stored in bucket `d-cc88a377-b456-4673-a449-07b0e7960ffd`, which the dataset version's file repository in the Knowledge Graph names. The bucket is flat: 35 Axon Binary Format files `<yyMMdd>_<slice><repeat>.ABF`, the data descriptor and the licence.

Provenance: the complete object listing of the public bucket (37 objects). The meaning of each name token is quoted from the data descriptor in the bucket. See `docs/validation/foreign-datasets.md`.

What it checks:

- One `file` level at the root, with the recording as the file entity, and the cell and the animal inferred from the file name (`locations: []`).
- A cell id that is itself composite (date and slice number) read as one string, with the date and the slice number as separate fields of the cell.
- The walk yields 2 animals, 7 cells and 35 recordings. The descriptor reports 7 cells from two mice and 350 traces, which is 35 files of 10 current steps each.
- The descriptor lists the files as `<yyMMdd>_<slice>a-e.abf`; the bucket has `.ABF`. The config follows the bucket.
- The descriptor says the slices of one day come from one animal, so the animal is identified by the recording date. The EBRAINS Knowledge Graph lists the two animals of the dataset version under the same identifiers (`170518`, `170529`), which is why the animal is the subject entity here rather than the cell.
- The data descriptor and the licence are `no-match` (gap **G1**).
