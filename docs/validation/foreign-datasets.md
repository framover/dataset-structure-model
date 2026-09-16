# Validation Against Foreign Datasets

The mapping language was written around the authors' own layouts. Before 1.0 it has to be checked against layouts it was not designed for, so that the core stops changing for the right reason. This page records one such pass: fourteen public layouts plus the layout of one existing data-management tool, each written as a conformance case, and every place where the model could not say what the dataset means.

The pass changed **no schema file**. Every gap below is a proposal; the fixtures pin the *current* behaviour so that a change to the core is visible as a change to an expectation.

---

## Method

1. Each layout was reconstructed from public documentation and file listings (provenance in the table below) and reduced to a listing of a few entities, enough to exercise every rule the layout needs.
2. A config was written for it without bending the description: where the model has no way to say something, the closest honest config was used and the gap recorded.
3. `expected.json` was produced by the Python reader and reviewed against what the dataset means. Where the reader's output is wrong *for the dataset* but right *per the current rules*, the case pins the current rules and its README names the gap.
4. Every case passes the self-consistency suite (`tests/test_conformance.py`) and the Python reader (`dsm conformance`). The MATLAB reader was not run in this pass (no MATLAB in the validation environment); every pattern stays inside the portable regex subset.

**Provenance caveat.** The validation environment could not fetch dataset hosts directly (DANDI, OpenNeuro, GIN, CRCNS, Zenodo and the format documentation sites were blocked by the network policy). Layouts were reconstructed from the published format specifications and corroborated with search-engine excerpts of the landing pages, API paths and documentation. Names of real files are used where the source states them; where a case had to invent names to make a listing (recording folder names in a Zenodo deposit, session dates), its README says so. None of the gaps depends on an invented detail.

---

## Datasets

| Case | Layout | Provenance | Why it was chosen |
|------|--------|------------|-------------------|
| `dandi-nwb-subject-folders` | DANDI 000006: `sub-<id>/sub-<id>_ses-<date>.nwb`, `dandiset.yaml` | DANDI asset paths as cited in the DANDI user guide and NWB tutorials | One-file entities under subject folders; dataset-level file |
| `dandi-nwb-session-variants` | DANDI 000409 (IBL Brain Wide Map): several NWB files per session, `desc-raw`/`desc-processed`, `+` in names | Conversion repository (catalystneuro/IBL-to-nwb) and DANDI notebooks | Several files per entity distinguished by an entity in the name |
| `gin-blackrock-flat-files` | GIN `INT/multielectrode_grasp`: `datasets/<session>.nev/.ns2/.ns6/.ccf/.odml`, sorted `-03.nev`, `datasets_matlab/` | Repository listing; Brochier et al. 2018 (Sci. Data) | Flat files, two-digit years, sibling branch with the same entity |
| `crcns-hc3-numbered-extensions` | CRCNS hc-3: `ec013.15/ec013.156/ec013.156.{xml,eeg,whl,clu.N,res.N,fet.N,spk.N}` | hc-3 data description and download portal | Numbered extensions, four entity types, files at an outer level |
| `ibl-alf-session-path` | IBL ONE/ALF: `<lab>/Subjects/<subject>/<date>/<NNN>/{alf,raw_ephys_data,…}/probeNN/` | ALF specification (ONE docs); `data_structure` notebook | Deep path, composite identity, one entity in two branches |
| `bids-multimodal-sessions` | OpenNeuro ds000117: `sub-XX/ses-YY/<datatype>/…`, sidecars, `scans.tsv`, `derivatives/` | BIDS specification; ds000117 dataset page | The standard everyone compares with; optional entities |
| `allen-ecephys-cache` | AllenSDK `EcephysProjectCache`: `session_<id>/session_<id>.nwb`, `probe_<id>_lfp.nwb`, root CSVs | AllenSDK data-access docs and cache manifest keys | Two entity types in one folder |
| `open-ephys-binary` | Open Ephys binary: `Record Node N/experimentN/recordingN/continuous/<stream>/…`, `events/`, `structure.oebin` | Open Ephys GUI binary-format docs | Four levels, fixed level, branching under one entity |
| `spikeglx-folder-per-probe` | SpikeGLX: `<run>_g<N>/<run>_g<N>_imec<K>/<run>_g<N>_t<T>.imec<K>.ap.bin`, nidq files at gate level | SpikeGLX user manual, "Parsing data files" | Composite identity, tokens from two levels, series per trigger |
| `suite2p-output-planes` | suite2p: `<session>/suite2p/plane<N>/{F,Fneu,spks,stat,ops,iscell}.npy`, `combined/`, `ops1.npy` | suite2p output docs | Fixed level between entities; files inside a structural folder |
| `deeplabcut-project` | DeepLabCut project: `videos/<v>.avi` + `<v>DLC_…`, `labeled-data/<v>/CollectedData_<scorer>.csv` | DeepLabCut user guide | One tree with several branches; the multi-location workaround |
| `scanimage-caiman-two-photon` | ScanImage `<base>_<acq>_<file>.tif` series; CaImAn `memmap__d1_…_frames_N_.mmap`, `_results.hdf5` | ScanImage docs; CaImAn `mmapping.py` | File-level ↔ folder-level matching, metadata in member file names |
| `zenodo-adhoc-date-folders` | Zenodo 10558021: `2023-05-11/<recording>/plane{1,2,3}.tif` | Landing-page description (recording names reconstructed) | Ad-hoc, no subject, exact count of files |
| `zenodo-adhoc-flat-mat` | Zenodo 13941450: `Data_AC1.mat`, `Data_AC2.mat`, `Clusters_AC.mat`, `AnatInfo_ICE.mat` … | Landing-page description | Ad-hoc, flat, an entity split over numbered files |
| `nansen-project-layout` | NANSEN (VervaekeLab/NANSEN): raw `yyyy_mm_dd/yyyymmdd_HH_mm_ss_<sid>/`, processed `subject-<id>/session-<sid>/{motion_corrected,roi_data,roisignals}/<sid>_<var>.<ext>` | Source code: `initializeDataLocationModel.m`, `templates/datalocation/ophys/two_photon_sciscan.m`, `Session.generateFolderName`, `Session.getDataFilePath`, `templates/datavariables/+ophys/+twophoton/getVariableList.m` | The layout an existing tool already manages |

---

## Features exercised

`●` used and behaved as specified; `○` used and exposed a gap (see the gap id in the case README).

| Case | Folder levels | File level | Structural level | Fixed level | Composite identity | Inferred ancestor | Cross-location match | Several roots | `{token}` patterns | required / cardinality | `valueFormat` | Integer identity | `excludePatterns` | Template-derived match | Whole-path rule |
|------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| dandi-nwb-subject-folders | ● | ● | | | | | | | ● | ● | ● | | ● | ● | |
| dandi-nwb-session-variants | ● | ● | | | | | | | ● | ● | | | | | |
| gin-blackrock-flat-files | | ● | | ● | | ● | | | ● | ● | ● (yy) | | | | |
| crcns-hc3-numbered-extensions | ● | ○ | | | | ● | | | ● | ● | | ● | | | |
| ibl-alf-session-path | ○ | | ○ | ● | ● | | | | | ● | ● | ● | | | ● |
| bids-multimodal-sessions | ● | ○ | ● | | | | | | ● | ○ | | ○ | | | |
| allen-ecephys-cache | ● | ○ | | | | | | | ● | ● | | ● | | ● | |
| open-ephys-binary | ○ | | | ● | | | | | | ● | | ● | | | |
| spikeglx-folder-per-probe | ○ | | | | ● | | | | ● | ● | | ● | | | |
| suite2p-output-planes | ● | | | ○ | | ● | | | | ● | ● | ● | ● | ● | |
| deeplabcut-project | ● | ● | | | | | ● | | ● | ● | | | ● | | |
| scanimage-caiman-two-photon | ○ | ● | ● | | ● | | ● | ● (2 env.) | ● | ● | ● | | | ● | |
| zenodo-adhoc-date-folders | ● | | ● | | | | | | | ○ | ● | ● | | | |
| zenodo-adhoc-flat-mat | | ● | | | | | | | ● | ● | | | | | |
| nansen-project-layout | ○ | | ● | | | ● | ● | ● (2 roots) | ● | ● | ● | | ● | ● | |

What worked without friction, across all fifteen: identity declared once and matched across locations (raw timestamp folders against generated `session-` folders; a TIFF series against a CaImAn folder); composite identities whose parts come from structural levels above the entity; ancestors with no folder of their own; two-digit years; integer identities; `enum` and `minimum` validation; several roots and environments in one location; `{token}` substitution of parent and own identity into file patterns.

---

## Gaps

Kind: **concept** (the model has no way to say it), **cardinality** (it can say it, but not how many), **naming** (a field exists whose name or placement misleads), **ambiguity** (the spec text or the readers leave it undefined). Compatibility: **additive** (new optional field or enum value; existing configs and records unchanged; minor bump), **semantic** (no schema change, but readers produce different records for some existing configs; fixtures change; minor bump before 1.0, major after), **structural** (changes the shape of the core; major after 1.0).

| Id | Gap | Kind | Seen in | Proposed change | Compatibility |
|----|-----|------|---------|-----------------|---------------|
| G1 | **Dataset-level files and known non-entity siblings.** `dandiset.yaml`, `participants.tsv`, `manifest.json`, `sessions.csv`, `README`, `docs/`, `hc3-metadata-tables/` are expected parts of every downloaded dataset, and every one is `no-match`. The only alternative, `excludePatterns`, reports them as `excluded`, which says they are noise. | concept | 12 of 15 cases | `filesystemSource.additionalEntries` (or a per-level `knownPatterns`): regexes for entries that are part of the dataset but belong to no entity; reported as `unmatched` with a new reason `known`. `additionalFolders` becomes one instance of it. | additive; adds an `unmatched.reason` value |
| G2 | **Files of an outer entity are double-accounted.** A file that is a direct child of a non-innermost entity folder and matches that level's `filePatterns` is listed in the entity's `files` *and* reported `no-match` by the next level. Neither the schema nor the conformance rules say which wins. | ambiguity | hc-3 (`.xml/.eeg/.whl`), BIDS (`scans.tsv`), Allen (`session_<id>.nwb`), Open Ephys (`structure.oebin`, `settings.xml`), SpikeGLX (nidq files) | Rule: an entry that matches a `filePatterns` entry of the level whose folder it is in is claimed by that entity and is not offered to the next level. An entry that matches no pattern is offered to the next level as now. State it in `docs/guides/conformance.md`; update the five fixtures. | semantic (five new fixtures change; no existing fixture changes) |
| G3 | **A legitimate multi-folder entity is reported as `duplicate-entity`.** When a structural level sits above an entity level (a date above a subject) or alternates between branches (`alf`/`raw_ephys_data` above `probeNN`), the same entity has one folder per structural value by design. The reader reports `duplicate-entity` on every one of them. | ambiguity | IBL (`probe00` in two collections), ScanImage (`m0123` under two dates) | Rule: `duplicate-entity` fires only when two folders yield the same identity **under the same parent folder**. Folders under different parents are the entity's several locations, listed in `paths` without an issue. `folder-hierarchy-basic` (`_copy` sibling) still fires. | semantic (two new fixtures change) |
| G4 | **No optional fields.** A field whose rule legitimately matches nothing (`task`, `run` on an anatomical scan) raises `extraction-failed` unless a `defaultValue` is invented. BIDS optional entities and any "sometimes present" name part hit this. | concept | BIDS | `metadataDefinition.isRequired` (default `true`); when `false`, a missing value is absent without an issue. | additive |
| G5 | **Branching layouts.** One location is one linear list of levels. Datasets routinely have several sub-hierarchies under one entity (Open Ephys `continuous/` and `events/`; IBL `alf/`, `raw_ephys_data/`, `raw_video_data/`; DeepLabCut `videos/` and `labeled-data/`; GIN `datasets/` and `datasets_matlab/`). Only one branch can be described; the rest is `no-match`. | concept | Open Ephys, IBL, DeepLabCut, GIN, BIDS `derivatives/` | Two options. (a) Keep layouts linear and make the workaround the idiom: one data location per branch, rooted inside the tree (`deeplabcut-project` does this), and document it. (b) Let a level carry `children: [entityLayoutLevel…]`, turning the layout into a tree. (b) is the only structural change in this list and must be decided before 1.0; (a) needs G7 and G12 to be useful. | (a) documentation; (b) structural |
| G6 | **Files belonging to an ancestor inside a descendant's folder.** At a file level every file is an entity of that level's type. BIDS puts session-level `coordsystem.json`/`headshape.pos` in `meg/` next to the runs; they become a bogus acquisition with `missing-required-file`. | concept | BIDS | `fileGroupingPattern.ofEntity`: a pattern that claims matching files for a named ancestor type instead of the level's own type, evaluated before identity extraction. | additive |
| G7 | **Files inside a structural level.** `suite2p/ops1.npy` sits in a fixed structural folder between the session and the planes. A structural level may carry `filePatterns` per the schema, but no reader consumes them, and there is no entity to attach the files to. | ambiguity / concept | suite2p | Same field as G6: `filePatterns` on a structural level are allowed only with `ofEntity`, and readers attach the matches to the nearest ancestor of that type. Until then, state that `filePatterns` on a structural level is ignored (or forbid it). | additive (plus a validation rule) |
| G8 | **Several rules for one field in one location.** The schema says "one entry per field" but does not enforce it; both readers silently let the last rule win. DeepLabCut needed two naming forms for one identity and had to fold them into one regex with alternation. | ambiguity | DeepLabCut | Either enforce one rule per field (`reference-integrity`) or define several rules as an ordered fallback: first rule with a value wins. The fallback is more useful and costs nothing for configs with one rule. | semantic for configs that already have duplicates (none known) |
| G9 | **No formatting of tokens.** An integer identity substitutes as `1`, but folder and file names carry `00001`. Generation and pattern matching both need padding, so the fixture keeps the counter as a string. | concept | ScanImage/CaImAn | A format spec in tokens, `{acquisition_number:05d}` (Python format mini-language subset: width and zero padding), applied in `pathComponentTemplate`, `filePatterns` and `template` rules. | additive (token grammar extended) |
| G10 | **Metadata in member file names.** Rules read the entity's path components. Values written into the names of files that `filePatterns` match (CaImAn's frame count and image size, NANSEN's variable name) cannot be extracted without making the file itself an entity. | concept | CaImAn, NANSEN | `metadataExtraction.filePattern`: the name of a `filePatterns` entry; the rule reads the matched file's name (first match; `cardinality: one` expected). This is the surviving part of the withdrawn `fileClass.metadataExtractors`. | additive |
| G11 | **Exact or bounded file counts.** `cardinality` is `one` or `many`; "exactly three planes", "at least one per trigger", "at most one sorted file" cannot be said. | cardinality | Zenodo 10558021, SpikeGLX | `minCount` / `maxCount` integers on `fileGroupingPattern`; `cardinality: one` ≡ `maxCount: 1`. Reuse `cardinality-violation`. | additive |
| G12 | **Files in subfolders of the entity folder.** `filePatterns` match direct children only. NANSEN stores every variable in a named subfolder of the session folder (`motion_corrected/<sid>_two_photon_corrected.raw`); BIDS derivatives and most processed layouts do the same. Those files are covered silently, cannot be required, and do not appear in `files`. | concept | NANSEN, suite2p | `fileGroupingPattern.subfolder`: a relative folder path inside the entity folder (literal, or a template with tokens); candidates for that pattern are the direct children of that subfolder. `additionalFolders` is then redundant. | additive |
| G13 | **`entityLayoutLevel.isRequired` is in the core schema but no reader consumes it.** A variable-depth hierarchy (BIDS without `ses-`, DeepLabCut `iteration-N` present or not) cannot be described; a level marked `isRequired: false` is walked as if required. | ambiguity | BIDS (by the specification; ds000117 itself has sessions) | Either implement it (when the level's folder is absent, the next level is matched directly under the parent and the level's rules yield no value) with a conformance case, or mark the field DRAFT before 1.0. The field's description already promises the behaviour. | semantic if implemented |
| G14 | **Identity is always scoped by parent.** A session found under `sub-01/` in one location and directly under the root in another (no subject in the name) is two records, because the parent chain is part of the key. Processed folders named by session id alone are common. | concept | Probed during this pass on an in-memory listing (one location with subject folders, one with session folders only); not made a fixture, because the fixture would pin the undesired split | `entityType.identityScope`: `"parent"` (default, current) or `"global"`: a global identity matches across locations regardless of ancestors, and the record's `parents` is the union of what the locations yielded (conflict → `metadata-conflict`). | additive, but changes the record key for types that opt in |
| G15 | **`defaultValue` and identity.** The schema says a default is used "when the field cannot be extracted", but an entity whose identity field matched nothing is `no-match` even when the field has a `defaultValue`. So an optional component of a composite identity (BIDS `run-` absent ⇒ run 1) cannot be expressed. | ambiguity | BIDS | Decide and state it: either defaults apply before the identity check (then `run` with `defaultValue: 1` works), or identity fields may not carry a `defaultValue` (validation rule). The first is more useful. | semantic (only for configs with a default on an identity field; none in the repository) |
| G16 | **`additionalFolders` has no effect.** Everything under an innermost entity folder is covered whether or not it is listed. The field documents intent but changes no record. | naming | NANSEN, raw-processed example | Retire it when G12 lands, or give it meaning now: a subfolder not listed is reported (new issue code `unexpected-folder`). | additive either way |

Two smaller observations, not gaps:

- `dsm listing` and the fixtures handle names with spaces, dots and `+` without trouble; MATLAB-facing regexes only need the documented escapes.
- Partial downloads (`.nwb.part`), OS files (`Thumbs.db`, `.DS_Store`) and notes (`notes.txt`) are `no-match` unless excluded. That is correct: the config author decides what is noise. G1 is about entries the *dataset* defines, not these.

---

## Recommendation for 1.0

**Decide or fix before the freeze** (each either changes how existing records read, or is a promise the schema already makes):

| Id | Why it cannot wait |
|----|--------------------|
| G2 | Two readers can disagree today on whether an outer entity's file is unmatched; the rule must be pinned before records are relied on. Five of the new fixtures encode the ambiguous answer. |
| G3 | `duplicate-entity` is wrong for any layout with a structural level above an entity, which includes the repository's own raw/processed example if a subject level were added under the date. The fix is a one-line rule. |
| G13 | A core field with a documented meaning and no implementation. Implement or move to DRAFT. |
| G15 | Spec text and reader behaviour disagree. Pick one sentence. |
| G8 | Undefined behaviour that both readers happen to share. State it. |
| G12 | The first layout an existing tool (NANSEN) needs is not describable; the field is additive but shapes how `filePatterns` are read, so it belongs in the core the readers are validated against. |
| G5 | Only the tree-layout option is structural. Decide (a) or (b) now; if (a), write the idiom into the usage guide and keep `entityLayout` an array for good. |
| G14 | Changes the meaning of the record key for types that opt in; better to have it in the 1.0 key semantics than to add a second notion of identity later. |

**Can follow as minor releases** (purely additive, no existing record changes): G1, G4, G6, G7, G9, G10, G11, G16.

Nothing found argues for a different shape of the core: entity types with declared identity, per-location layouts, per-location extraction rules and the entity record held for every layout. What the layouts asked for is more ways to say *which files belong to whom* (G2, G6, G7, G10, G12) and a few rules the spec had left implicit (G3, G8, G13, G15).

---

## Fixtures added

Fifteen cases under `conformance/`, listed in the [conformance guide](../guides/conformance.md#cases). Each README states the layout, its provenance, what the case checks, and the gap ids it exhibits. The NANSEN layout was reconstructed from the tool's source only; the tool itself was not run.
