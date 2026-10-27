# ebrains-salgueiro-pereira-2020

An EBRAINS dataset migrated from the old HBP object storage (dataset version `bd5f91ff-e829-4b85-92eb-fc56991541f1`, Salgueiro-Pereira and Marie, excitability profile of CA1 pyramidal neurons in APP-PS1 Alzheimer disease mice and control littermates). Bucket `pc0a33-ext-d000001_ADNeuronModel_pub`: one folder per group (`APPPS1_mouse_model_3-4_months`, `control_9-10_months`, …) holding flat ABF files `<yyMMdd><NNN>[_rita]_S<NN>.abf`.

Provenance: the complete object listing of the public bucket (79 entries; the bucket's three empty folder objects are listed as folders). Meanings are quoted from `HBP-DataDescriptor_ADNeuronModel_v2.pdf`. See `docs/validation/foreign-datasets.md`.

What it checks:

- A structural group level whose name carries two fields of the subject (genotype and age group). The subject has no folder; it is inferred from the `_S<NN>` part of the file names, and the group folder's fields attach to it.
- `defaultValue` on a field that is not part of an identity: the descriptor says `_rita` marks one experimenter and all other traces were recorded by the other. The rule matches `_rita_` and the definition defaults to `marie`: 43 `rita`, 30 `marie`, no `extraction-failed`.
- The walk yields 13 subjects and 73 recordings without issues. The descriptor lists 73 files.
- The descriptor lists the files without the `_S<NN>` part (`191129000_rita.abf`; the bucket has `191129000_rita_S24.abf`) and does not say what `S<NN>` is. The config reads it as the mouse because each group has 3 or 4 values and the descriptor says each group was recorded from at least 3 mice. That reading is an inference, stated in the entity description.
- The data descriptor and the licence are `no-match` (gap **G1**).
