# Schema Usage Guide

This guide explains how to write a Dataset Structure Model (DSM) configuration for your dataset. It walks through each section with practical examples and links to the reference pages.

---

## Overview

A DSM configuration is a single JSON file that describes:

- **What entity types** exist in your dataset (subjects, sessions, recordings, …) and what identifies each
- **How entities relate** to each other (a subject has many sessions)
- **Where data lives** on disk (one or more storage roots per environment)
- **How folders and files are laid out** within each data location
- **How metadata is extracted** from folder and file names
- **Which files belong to an entity**

The configuration is purely descriptive: it tells tools how to read your data, not how to organise it. Your files do not need to move.

A minimal valid configuration:

```json
{
  "schemaVersion": "0.1.0",
  "entityTypes": [
    { "name": "subject", "identifierRef": "subject_id" }
  ],
  "metadataDefinitions": {
    "subject_id": { "name": "subject_id", "dataType": "string", "ofEntity": "subject" }
  },
  "dataLocations": [
    {
      "identifier": "raw",
      "displayName": "Raw data",
      "dataCategory": "raw",
      "sourceType": "filesystem",
      "filesystemSource": {
        "rootStoragePaths": [{ "identifier": "main", "path": "/data/raw" }],
        "entityLayout": [
          { "name": "subjects", "entityType": "subject", "matchPattern": "^[A-Za-z0-9]+$" }
        ],
        "metadataMapping": [
          { "metadataRef": "subject_id", "extraction": { "method": "substring", "pattern": ":", "entityLayoutLevel": "subjects" } }
        ]
      }
    }
  ]
}
```

See [Schema Reference → Top-Level Structure](../reference/overview.md) for the full property table.

---

## Entity Types

[Entity types](../reference/overview.md#entitytypes) are the semantic categories of things in your dataset. Declare them once at the top level, and give each one an identity:

```json
"entityTypes": [
  { "name": "subject", "description": "A research subject (mouse)", "isPrimary": true, "identifierRef": "subject_id" },
  { "name": "session", "description": "A single recording session", "identifierRef": "session_id" }
]
```

`identifierRef` names the `metadataDefinitions` key whose value identifies an instance of this type — across all data locations. It is required (or `identifierRefs` for a composite key). There is no fallback to folder names: that would make identity depend on where an entity was found. See [Cross-location entity matching](#cross-location-entity-matching).

`isPrimary: true` marks the top-level unit of the dataset (typically subject or participant).

---

## Entity Relationships

[Entity relationships](../reference/entity-relationships.md) are declared at the top level and hold in every data location:

```json
"entityRelationships": [
  { "sourceEntity": "subject", "targetEntity": "session", "relationType": "oneToMany", "relationName": "hasSessions" }
]
```

They describe semantics, not folders. If all sessions of all subjects sit in one flat folder, `oneToMany` still holds.

---

## Metadata Definitions

[Metadata definitions](../reference/metadata-definitions.md) are the global vocabulary. Define each field once; everything else references it by key.

```json
"metadataDefinitions": {
  "subject_id": {
    "name": "subject_id", "title": "Subject ID", "ofEntity": "subject", "dataType": "string",
    "validation": { "pattern": "^m\\d{3}$" }
  },
  "session_id": {
    "name": "session_id", "title": "Session ID", "ofEntity": "session", "dataType": "string",
    "validation": { "pattern": "^m\\d{3}-\\d{8}-\\d{3}$" }
  },
  "session_date": {
    "name": "session_date", "title": "Session date", "ofEntity": "session", "dataType": "date"
  }
}
```

Give identity fields a `validation.pattern`: it makes values checkable, and it is what a `pathComponentTemplate` token matches when a level has no `matchPattern`.

---

## Data Locations

A [data location](../reference/data-locations.md) is one logical collection of data: its role, its permission, its root paths, its layout, and how to read metadata from it.

```json
{
  "identifier": "raw",
  "displayName": "Raw two-photon data",
  "dataCategory": "raw",
  "access": "read",
  "sourceType": "filesystem",
  "filesystemSource": {
    "rootStoragePaths": [ ... ],
    "entityLayout": [ ... ],
    "metadataMapping": [ ... ]
  }
}
```

### Category and access are separate

`dataCategory` is the location's role in the data lifecycle (`raw`, `processed`, `derived`, …). `access` is permission: `read` (default) or `readwrite`. A tool may only create folders and write files in a `readwrite` location. Describing existing data does not grant write access, so set `readwrite` explicitly on the locations a pipeline populates. See [Data Location Categories](data-location-categories.md).

### Root storage paths

One entry per computing environment; `preferences.environmentIdentifier` selects one at runtime.

```json
"rootStoragePaths": [
  { "identifier": "lab-windows",  "path": "D:\\Data\\TwoPhoton",     "volumeName": "DATA", "storageType": "local",    "environment": "windows-lab" },
  { "identifier": "analysis-mac", "path": "/Volumes/DATA/TwoPhoton", "volumeName": "DATA", "storageType": "external", "environment": "mac-analysis" }
]
```

`volumeName` lets a reader re-resolve a root whose drive letter or mount point moved. Whether a path is reachable right now is not stored in the config.

### Provenance with `derivedFrom`

```json
{ "identifier": "processed", "dataCategory": "processed", "access": "readwrite", "derivedFrom": ["raw"], "sourceType": "filesystem", "filesystemSource": { ... } }
```

A backwards-looking record. It also tells tools which source entities supply the metadata for generated output paths. See [Pipeline Integration](pipeline-integration.md).

---

## Entity Layout

The [entity layout](../reference/entity-layout.md) is the hierarchy below the root, outermost first. Each level either represents an entity type or is structural.

```json
"entityLayout": [
  { "name": "dates",    "matchPattern": "^\\d{4}_\\d{2}_\\d{2}$" },
  { "name": "sessions", "entityType": "session",
    "matchPattern": "^\\d{4}_\\d{2}_\\d{2}_\\d{2}_\\d{2}_\\d{2}_m\\d{3}-\\d{8}-\\d{3}$",
    "excludePatterns": ["^\\..*"] }
]
```

### Structural levels

A level without `entityType` is structural: part of the path, not an entity. Date folders, a fixed `processed/` folder, an `auxiliary/` folder. Structural levels can still be read by extraction rules (a session's date from the date folder above it) but do not contribute to identity.

### Fixed levels

```json
{ "name": "processed", "isVariable": false, "fixedName": "processed" }
```

### Missing ancestor levels

A location does not need every ancestor level. A processed location may hold session folders with no subject folders above them; `subject_id` is then extracted from the session name and identifies the parent subject, and any other subject field the session name carries attaches to that subject as well. See [Metadata Extraction → Which entity a value belongs to](../reference/metadata-extraction.md#which-entity-a-value-belongs-to).

### File levels: entities that are groups of files

When all files of all sessions are in one folder, declare a `file` level. Files are grouped into entities by their extracted identity — every file whose `session_id` is the same belongs to the same session:

```json
"entityLayout": [
  {
    "name": "session-files",
    "entityType": "session",
    "fileSystemType": "file",
    "matchPattern": "^m\\d{3}-\\d{8}-\\d{3}_.+$",
    "filePatterns": [
      { "name": "raw_movie", "pattern": "^{session_id}_raw\\.tif$",  "isRequired": true, "cardinality": "one" },
      { "name": "metadata",  "pattern": "^{session_id}_meta\\.json$", "cardinality": "one" }
    ]
  }
]
```

The `{session_id}` token is replaced by the exact identity of the entity being resolved, so membership never leaks between `…-001` and `…-0010`. A file level must be the last level. See the [Flat Session Files example](../examples/flat-session-files.md).

---

## File Patterns

`filePatterns` on a level lists the kinds of files that belong to an entity there — inside the entity folder for a folder level, in the shared folder for a file level.

| Field | Meaning |
|-------|---------|
| `pattern` | Regex on the file name; may contain `{token}` references to the entity's metadata |
| `name` | Reported in entity records under this name |
| `isRequired` | At least one match must exist for the entity to be complete |
| `cardinality` | `one` or `many` (a numbered series) |

Readers report matched files per named pattern and flag incomplete entities. This is where a tool finds "the raw movie of session X" without knowing the naming convention.

---

## Metadata Mapping

`metadataMapping` says how each global field is read from this location's paths. Full contract: [Metadata Extraction](../reference/metadata-extraction.md).

```json
"metadataMapping": [
  { "metadataRef": "session_id",   "extraction": { "method": "regex",     "pattern": "_(m\\d{3}-\\d{8}-\\d{3})$", "entityLayoutLevel": "sessions" } },
  { "metadataRef": "subject_id",   "extraction": { "method": "regex",     "pattern": "_(m\\d{3})-\\d{8}-\\d{3}$",  "entityLayoutLevel": "sessions" } },
  { "metadataRef": "session_date", "extraction": { "method": "substring", "pattern": ":", "valueFormat": "yyyy_MM_dd", "entityLayoutLevel": "dates" } }
]
```

| Method | Use for |
|--------|---------|
| `substring` | Fixed character positions. `pattern` is a Python-style slice: `0:8`, `9:`, `:-4`, `:` |
| `regex` | Anything structural. Value = first capture group |
| `template` | Compose from other fields: `"{session_date}_{subject_id}"` |
| `fixed` | A constant `value` |
| `function` | A reader-registered extractor by registry key. Needs code in every reader; avoid when a declarative rule will do |

Reference levels by **name**. Dates and times need `valueFormat` in LDML notation (`yyyyMMdd`, `HH_mm_ss`).

---

## Cross-Location Entity Matching

With raw and processed locations, tools must know which processed folder corresponds to which raw session. Declare identity once:

```json
"entityTypes": [
  { "name": "subject", "identifierRef": "subject_id" },
  { "name": "session", "identifierRef": "session_id" }
]
```

Two sessions from different locations are the same session when their `session_id` is equal **and** their parent subjects match. Parent identity is implicit — do not put `subject_id` in the session's key. Every location that extracts `session_id` is automatically linkable, and every location must extract the same value for the same session (use `normalize` where conventions differ). See the [Raw and Processed example](../examples/raw-processed-two-photon.md).

---

## Preferences

```json
"preferences": {
  "defaultDataLocationIdentifier": "processed",
  "environmentIdentifier": "mac-analysis"
}
```

These describe a machine, not the dataset. Leave them out of a shared config and put them in a git-ignored `<config>.local.json` next to it; readers prefer the overlay. See [preferences](../reference/preferences.md).

---

## What comes out: entity records

Readers turn a config plus a directory tree into [entity records](../reference/entity-record.md): one object per entity with its identity, parents, the paths and matched files in each location, and its metadata. That is the contract tools build tables from, and it is identical across readers.

---

## Best practices

1. **Define every field once** in `metadataDefinitions`; give identity fields a `validation.pattern`.
2. **Declare identity on every entity type.** Extraction rules for identity fields must agree across locations.
3. **Reference levels by name**, not index.
4. **Prefer `regex` and `substring` over `function`.** A config without `function` runs in any reader without code.
5. **Set `access: readwrite`** only on locations tools may populate, and give those levels a `pathComponentTemplate` so generated and parsed names stay in sync.
6. **Use `filePatterns` with names and `isRequired`** so tools can find files by role and report incomplete entities.
7. **Keep `preferences` in a local overlay.**
8. **Write `description` fields.** They are the primary surface for people and LLMs reading the config.
