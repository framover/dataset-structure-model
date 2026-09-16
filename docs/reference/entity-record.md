# Entity Record

A DSM config says how to *read* a dataset. The **entity record** says what comes out: the object a reader emits for each entity it discovers. It is defined by [`schema/EntityRecord.schema.json`](https://github.com/framover/dataset-structure-model/blob/main/schema/EntityRecord.schema.json) and is the interchange format between readers in different languages and the tools that build entity tables from them. Two readers given the same config and the same directory listing produce the same records — that is what the [conformance fixtures](../guides/conformance.md) check.

```json
{
  "entityType": "session",
  "identity": { "session_id": "m110-20250510-001" },
  "parents": [
    { "entityType": "subject", "identity": { "subject_id": "m110" } }
  ],
  "locations": [
    {
      "dataLocationIdentifier": "recorded",
      "rootStoragePathIdentifier": "lab-nas",
      "fileSystemType": "file",
      "paths": ["m110-20250510-001_meta.json", "m110-20250510-001_raw.tif"],
      "files": {
        "raw_movie": ["m110-20250510-001_raw.tif"],
        "metadata": ["m110-20250510-001_meta.json"]
      },
      "isComplete": true
    }
  ],
  "metadata": {
    "session_id": "m110-20250510-001",
    "session_date": "2025-05-10",
    "subject_id": "m110"
  },
  "issues": []
}
```

## Fields

| Field | Required | Description |
|-------|----------|-------------|
| `entityType` | Yes | Name from `entityTypes` |
| `identity` | Yes | The entity's own identity field(s) and value(s) |
| `parents` | No | Identity of each entity-typed ancestor, outermost first; structural levels do not appear. `identity` + `parents` is the full key. |
| `locations` | Yes | Where the entity has a folder or files of its own, one entry per data location. Empty for an ancestor inferred from descendants. |
| `metadata` | No | The entity's own fields, unioned across every path it was read from (its own paths, and the descendant paths it was inferred from where it has no level), plus its ancestors' identity fields |
| `issues` | No | Problems found for this entity, each `{ "code", "message" }` |

Each `locations` entry:

| Field | Required | Description |
|-------|----------|-------------|
| `dataLocationIdentifier` | Yes | `identifier` of the data location |
| `rootStoragePathIdentifier` | Yes | `identifier` of the root path the entity was found under |
| `fileSystemType` | No | `folder` (default) or `file` |
| `paths` | Yes | Relative to the root, `/`-separated; folder paths end with `/`. One folder path (more only with `duplicate-entity`), or every file at the level that carries this entity's identity |
| `files` | No | Files matched per **named** `filePatterns` entry; present exactly when the level declares `filePatterns` |
| `isComplete` | No | `true` when every `isRequired` pattern matched; present exactly when the level declares `filePatterns` |

`date`, `time` and `datetime` values are ISO 8601 strings; `integer` and `number` values are JSON numbers.

## Issue codes

| Code | Meaning |
|------|---------|
| `missing-required-file` | An `isRequired` pattern matched nothing |
| `cardinality-violation` | A `cardinality: one` pattern matched several files |
| `duplicate-entity` | Several folders in one location yield this identity |
| `extraction-failed` | A rule matched nothing and the field has no `defaultValue` |
| `metadata-conflict` | Locations disagree on a field's value |
| `validation-failed` | A value violates its definition's `validation` |
| `unresolved-extractor` | A `function` rule's registry key is not implemented by this reader |

Readers are compared by code; messages are free text.

## Why it is part of the spec

Without a defined output, "supports multiple entity tables" and "portable across languages" are claims nobody can check. With it, conformance is a fixture: a listing plus the records a reader must produce. A tool that stores where each entity lives (a session table, for example) stores exactly this object.
