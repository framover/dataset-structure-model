# Changelog

All notable changes to the Dataset Structure Model schema are documented here.
This project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Fifteen conformance cases describing layouts from outside the authors' lab: DANDI dandisets (subject folders; session variants), a GIN repository of Blackrock files, CRCNS hc-3, IBL ONE/ALF, BIDS (OpenNeuro ds000117), the AllenSDK ecephys cache, Open Ephys binary, SpikeGLX folder-per-probe, suite2p output, a DeepLabCut project, ScanImage series with CaImAn outputs, two ad-hoc Zenodo deposits, and the data locations of the NANSEN toolbox. Each README states the layout, its provenance and the gaps it exposes.
- `docs/validation/foreign-datasets.md`: the dataset list with provenance, the features each exercised, sixteen gaps (G1–G16) with a proposed change and its compatibility impact, and the recommendation on what to settle before a 1.0 freeze. The schema is unchanged by this pass; the new cases pin current behaviour where a gap was found.

### Changed
- The version is 0.1.0, not 1.0.0. The 1.0.0 label was applied before the mapping had met any dataset outside the authors' lab, and no tag, release or consumer ever carried it. Under semantic versioning, 1.0 promises that breaking changes become major versions; that promise waits for the evidence described in the README. The `schemaVersion` in every config, fixture and example, the Python package version and the schema default now read `0.1.0`.
- An ancestor inferred from its descendants' names now carries every field of its type those names yield, not only its identity. A cell with no folder gets the recording date and slice number read from its ABF file names; descendants that disagree raise `metadata-conflict`. Both readers implement it; the new `inferred-ancestor-fields` conformance case pins it. Previously the values were evaluated and discarded without an issue.

### Fixed
- `valueFormat` accepts a two-digit year (`yy`). The Python reader translated only `yyyy`, so `yyMMdd` failed with `extraction-failed` while the MATLAB reader parsed it; the readers disagreed on the same config.
- Two-digit years take a fixed pivot, 1969–2068, in both readers. MATLAB's `datetime` default pivot moves with the current year; the reader now passes `PivotYear` 1969.
- The portable `valueFormat` token subset (`yyyy yy MM dd HH mm ss`, quoted literals) is stated in the schema description and `docs/reference/metadata-extraction.md`; the `extraction-methods` conformance case pins the two-digit year and the pivot.

## [0.1.0] - 2026-09-09

The first numbered version. The core is what both readers implement and the conformance fixtures pin; blocks marked DRAFT may change at any time. The schema is not stable before 1.0, and what 1.0 waits for is stated in the README.

Earlier drafts (from 2025-07-02; labelled `1.0.0` in their files but never tagged, released or consumed) are superseded. The lists below are relative to those drafts.

### The core
- `filesystem` source type, with `rootStoragePaths`, `entityLayout` and `metadataMapping` nested under `filesystemSource`
- Extraction methods `substring`, `regex`, `template`, `fixed` and `function`
- Declared entity identity, structural levels, file-level entities
- `schema/EntityRecord.schema.json` — the object readers emit, with coded `issues` and empty `locations` for ancestors inferred from descendants
- `schema/DirectoryListing.schema.json` — the directory snapshot readers walk
- Python reference reader `dsm` (`src/python/dsm`, `pip install -e .`): `dsm validate`, `dsm listing`, `dsm walk` (dry run), `dsm compare`, `dsm conformance`; passes every conformance case
- MATLAB reader `+dsm` (`src/matlab`, `addpath src/matlab`): `loadConfig` with a schema interpreter that reads the schema files, listings, `walk`, `compareResults`, `renderReport`, conformance runner and `exportActual` for the cross-language check; passes every conformance case on R2024b and R2025b
- Conformance fixtures in `conformance/`: seven cases (folder hierarchy, flat session files, raw/processed matching, every extraction method, function extractors, two invalid configs) with the comparison rules in `docs/guides/conformance.md`

### Added (relative to the drafts)
- `access` (`read` | `readwrite`, default `read`) on `dataLocation` — permission, separate from `dataCategory`
- `uuid` on `dataLocation` and `rootStoragePath` for tools that persist references
- `customProperties` on `entityLayoutLevel` and `rootStoragePath`
- Structural levels: `entityLayoutLevel.entityType` is optional; a level without it is walked but skipped in identity
- File-level entities: at `fileSystemType: "file"`, files are grouped into one entity per extracted identity; the entity resolves to its set of files
- `{token}` references in `filePatterns[].pattern`, substituted with the entity's identity before matching
- `name` and `cardinality` (`one` | `many`) on `fileGroupingPattern`
- `value` on `metadataExtraction` for method `fixed`
- Schema-enforced constraints: exactly one of `identifierRef`/`identifierRefs` per entity type; `matchPattern` or `pathComponentTemplate` on a variable level; `fixedName` on a fixed level; per-method required fields; `substring` pattern must be a slice
- Defined `pathComponentTemplate` → `matchPattern` derivation (`validation.pattern` of the token's field, else `[^/\\]+`, anchored)
- Defined `function` call contract: `extractorFunction` is a registry key; readers call `(fullPath, levelName, dataLocationIdentifier)`
- Local overlay convention `<config>.local.json` for `preferences`
- Examples `flat_session_files.json` and `raw_processed_two_photon.json`, mirrored by conformance cases
- Tests: rejection cases for every constraint, cross-reference integrity, entity records, self-consistency of every conformance case, and validation of every complete JSON snippet in the docs
- Reference pages `metadata-extraction.md` and `entity-record.md`

### Changed (relative to the drafts)
- `preferences` is optional and has no required fields
- `entityLayoutLevel` requires only `name`
- `substring` pattern is a Python slice (`start:stop`, 0-based, half-open, negative indices, no step); the `end` keyword is gone
- `regex` value is the first capture group, else the whole match; portable subset documented
- `valueFormat` is Unicode LDML notation
- Level references by name are preferred over 0-based indices
- `identifier` on `dataLocation`, `rootStoragePath`, `entityLayoutLevel` and `fileGroupingPattern` constrained to `^[A-Za-z][A-Za-z0-9_-]*$`; `metadataDefinitions` keys to `^[A-Za-z_][A-Za-z0-9_]*$`
- `metadataDefinition` and its `validation` object are strict (`additionalProperties: false`)
- Draft configs that declared `schemaVersion: "0.1.0"` do not validate against this release (identity, level and method constraints)

### Removed (relative to the drafts)
- `rootStoragePath.isAvailable` — runtime state, reported by readers
- Extraction methods `filename` and `filepath` — use `substring` with `":"` (and `entityLayoutLevel: null` for the whole path)
- The `"other"` entity type convention — omit `entityType` instead
- Fallback of entity identity to the raw folder name — identity is declared
- The `fileClass` proposal (`role`, `format`, `groupKey`, `metadataExtractors`) that appeared in a draft changelog and design note but never in the schema

### DRAFT (outside the core)
- `spreadsheet`, `database` and `api` source types; the `sidecar` extraction method. They validate, readers may reject them, and they may change in a minor release.

## Pre-release drafts (never tagged)

- 2025-07-02 — initial draft: `dataLocations` with `entityLayout`, `metadataMapping`, `rootStoragePaths`; `entityTypes` and `entityRelationships`; `metadataDefinitions` with validation rules; `preferences`; 8 `dataCategory` values; 7 extraction methods including `filename` and `filepath`; a neuroscience example.
- Later drafts: `identifierRef`/`identifierRefs`, `derivedFrom`, `tags`, `customProperties`, `priority` and `isAvailable`, `unit`; `filesystemSource` nesting with symmetric source types; a `fileClass` proposal (withdrawn); mkdocs documentation.
