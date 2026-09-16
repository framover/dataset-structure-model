# Schema Design Decisions

The rationale behind the choices in the Dataset Structure Model, for contributors and tool builders who need the *why*, not just the *what*.

---

## The DSM is descriptive, not prescriptive

Most data standards (BIDS, ISA, NWB) require you to conform your data to a specified structure. The DSM does the opposite: you describe your data as it exists on disk. This supports the large volume of heterogeneous, legacy and instrument-specific datasets that will never be reorganised. The DSM is a *recipe for reading*, not a schema for the data itself.

---

## A core, DRAFT blocks outside it, and no 1.0 before the evidence

A schema without an implementation drifts — the repository's own history shows it. Version 0.1.0 names what readers implement and configs rely on: the `filesystem` source, the extraction methods `substring`, `regex`, `template`, `fixed` and `function`, entity identity, file-level entities and the entity record. `spreadsheet`, `database` and `api` sources and the `sidecar` method stay in the schema as **DRAFT** so their place is reserved, but readers may reject them and they may change at any time. The rule from here: a field enters the core when a reader consumes it, not before.

Version 1.0 is a promise that breaking changes become major versions. The core has been exercised on the authors' own layouts and one toy dataset, which is not evidence for that promise. So 1.0 waits until the mapping has been applied to datasets from outside the authors' lab and the core has stopped changing across them. Until then a change to the core bumps the minor version.

---

## `dataCategory` is per location; `access` is a separate field

A dataset commonly has several locations with different lifecycle roles, so category belongs on the location. Permission is a different axis — an `imported` location can be writable, a `processed` mirror read-only — and inferring it from category is fragile. `access` says whether tools may write; it defaults to `read` because describing existing data grants nothing.

---

## `metadataDefinitions` is global; `metadataMapping` is per location

Fields are defined once and extracted differently per location. This keeps names consistent (no aliasing), lets each location have its own naming convention, and gives cross-location matching a shared vocabulary.

---

## Identity is declared on `entityType` and is required

`identifierRef` (or a composite `identifierRefs`) on the entity type is the cross-location key. It is declared once per type rather than per location pair, so it scales to N locations and any new location that extracts the field is automatically linkable. Hierarchical context is implicit: a session is identified by its own key and its ancestors' keys.

Identity is **required**. Earlier drafts fell back to comparing raw folder names, which made identity depend on which location an entity was found in — the opposite of what a cross-location table needs. Requiring the declaration costs one line per entity type.

---

## Structural levels instead of an `"other"` entity type

Folders that are part of the path but are not entities — date folders, a fixed `processed/` — are levels without `entityType`. Earlier docs suggested a magic `"other"` type; a missing field is more honest than a fake type, and it states the rule that matters: structural levels are skipped when building identity. Without that rule the motivating case, raw `{date}/{session}` against processed `{subject}/{session}`, would never match because the ancestor chains differ.

---

## Ancestor levels may be missing; ancestor identity may come from a descendant

A processed location that holds session folders with no subject folder above them is common. The subject still exists — its id is in the session name — so extraction rules for an ancestor type run on the nearest descendant level and identify the parent. Requiring every location to mirror the full hierarchy would exclude most real processed-data layouts.

---

## File-level entities are groups keyed by identity

A folder full of files from many sessions is the layout that "session = folder" models cannot represent. At a `file` level, entities are keyed by the identity extracted from the file name: N files with equal identity are one entity. Membership is declared by `filePatterns` whose patterns may embed `{token}` references to the entity's identity, so `m110-…-001` never claims files of `m110-…-0010`. The alternative — "files whose name contains the id" — is exactly the ambiguity this replaces.

---

## `substring` is a Python slice

Indices are how people specify fixed positions, and configuration UIs let users click characters, so the method stays. Its syntax needed one unambiguous definition across languages: `start:stop`, 0-based, half-open, negative indices, no step — a Python slice verbatim, enforced by the schema. The `end` keyword was MATLAB-only and cannot round-trip; MATLAB readers convert instead. A regex covers every case a slice does (`^.{4}(.{14})` is characters 5–18) but nobody should have to write that.

---

## `function` names a registry key, with a fixed call contract

A function extractor is portable when two things hold: the name is language-neutral, and every implementation receives the same inputs. So `extractorFunction` is a registry key resolved by each reader, and the call is `(fullPath, levelName, dataLocationIdentifier)` returning a value of the field's `dataType`. Whether two implementations agree is checked by conformance fixtures, not by the schema. A config that uses `function` does not run until someone writes code, so LLM-generated configs should prefer the declarative methods.

---

## `filename` and `filepath` were removed

`filename` was `substring` with pattern `:`; `filepath` was the same with `entityLayoutLevel: null`. Two spellings of one thing is a cost for every reader and for LLMs choosing between them.

---

## `pathComponentTemplate` serves double duty, and the derivation is defined

The template documents the naming convention, generates names when writing, and derives `matchPattern` when that is absent. "Tools may derive a regex" is not a rule; the rule is: a `{token}` matches the referenced definition's `validation.pattern`, else `[^/\\]+`, anchored `^…$`. Configs that rely on templates — LLM-written ones will — now behave identically everywhere.

---

## `derivedFrom` is provenance, not a pipeline definition

It records which locations fed this one. How the processing ran belongs to the pipeline tool (Nextflow, Snakemake, …).

---

## `fileGroupingPattern` stays simple

A pattern, an optional name, `isRequired`, `cardinality`. A richer *file class* with role, MIME format, co-occurrence `groupKey` and per-file extractors was drafted and withdrawn: no reader consumed it, and roles can be expressed by `name` and `description`. Co-occurrence groups may return when a reader needs them.

---

## `preferences` is instance state, so it is optional and may live in an overlay

Active environment and default location describe a machine, not the dataset. Keeping them only in a shared, version-controlled file means every checkout edits the same line. The overlay convention (`<config>.local.json`) keeps the shared config machine-independent. For the same reason there is no `isAvailable` on root paths: reachability is runtime state that readers report.

---

## `uuid` alongside `identifier`

Identifiers are human-chosen and may be renamed. Tools that persist references to a location or root path outside the config (a table recording where each entity was found) need something that never changes. Both exist; the config uses identifiers, persistence uses uuids.

---

## Regex portable subset and LDML date formats

Patterns run in MATLAB `regexp` and Python `re`, whose dialects differ (named groups, for one). The schema documents the common subset rather than picking a language. Date formats use Unicode LDML because MATLAB and Java are native to it and the translation to `strftime` is mechanical.

Only a fixed token subset is portable (`yyyy`, `yy`, `MM`, `dd`, `HH`, `mm`, `ss`, quoted literals), because each reader translates or validates them itself, and a token one reader understands and the other does not yields a value in one and an `extraction-failed` issue in the other. Two-digit years take a fixed pivot, 1969–2068, so that both readers place `69` in 1969: `strptime` has this window built in, while MATLAB's default pivot is fifty years before the current year and would give a different century as time passes. Real datasets carry six-digit dates such as `170518`, so `yy` had to be in the subset.

---

## Inferred ancestors carry every field their descendants' names hold

An entity type with no level of its own in a location is inferred from the names below it: a subject from its session folders, a cell from its recording files. The names that carry the ancestor's identity usually carry other properties of it too — a date, a sex, a slice number — and the config author declares them with `ofEntity` pointing at the ancestor. Keeping only the identity would drop those values with nothing to show for it, and the only workaround would be to redeclare them on the descendant, where they repeat on every row and no longer describe the thing they belong to. So an inferred ancestor's metadata is the union of its fields over every descendant path that inferred it, with `metadata-conflict` when those paths disagree, exactly as fields are pooled across locations. It is the same principle as a session reading its date from a structural date folder above it, with the value flowing upward instead of downward.

---

## The entity record is part of the spec

Without a defined output, "supports multiple entity tables" and "portable across languages" cannot be checked. The entity record is the object readers emit and tools store; a conformance fixture is a listing plus the records it must produce.

---

## No dataset-level metadata in the schema

Name, creator, DOI, licence belong to existing standards (BIDS `dataset_description.json`, NWB attributes, openMINDS, schema.org Dataset, DCAT). The DSM describes structure only.
