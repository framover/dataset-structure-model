# AI Agent Instructions

Rules for an LLM producing a valid Dataset Structure Model configuration from a directory listing. Self-contained: it does not require reading the schema. Every complete JSON example on this page is validated against the schema by the test suite.

---

## What a DSM config is

One JSON file describing how a dataset is laid out on disk: which folders and files represent which entities, and how metadata is read from their names. It is **descriptive** — record what exists, never invent a layout. It validates against `schema/DatasetStructureModel.schema.json` (draft-07) and must satisfy the cross-reference rules below.

## Top-level keys

| Key | Required | Notes |
|-----|----------|-------|
| `schemaVersion` | Yes | `"0.1.0"` |
| `dataLocations` | Yes | One entry per folder tree |
| `entityTypes` | Yes in practice | One per entity type used in any layout |
| `metadataDefinitions` | Yes in practice | Every field referenced anywhere |
| `entityRelationships` | No | Semantic relations only |
| `preferences` | No | Leave out; it is per-machine |

No other top-level keys. Every object in the schema is strict (`additionalProperties: false`): do not add keys that are not listed here.

## `entityTypes`

- Each entry: `name` (required), plus **exactly one** of `identifierRef` (string) or `identifierRefs` (array). Optional: `description`, `isPrimary`, `color`.
- `identifierRef` is a key of `metadataDefinitions` whose `ofEntity` is this type.
- `identifierRefs` lists only fields of this type; never include the parent's id.

```json
"entityTypes": [
  { "name": "subject", "isPrimary": true, "identifierRef": "subject_id" },
  { "name": "session", "identifierRef": "session_id" }
]
```

## `metadataDefinitions`

- An **object** keyed by identifier (`snake_case`), not an array.
- Each value: `name`, `dataType`, `ofEntity` (required); optional `title`, `description`, `unit`, `defaultValue`, `validation`.
- `dataType` ∈ `string, number, integer, date, time, datetime, boolean, array, object`.
- Give identity fields `validation.pattern`.
- Do not put extraction rules here.

## `dataLocations`

Each entry:

| Field | Required | Value |
|-------|----------|-------|
| `identifier` | Yes | `^[A-Za-z][A-Za-z0-9_-]*$`, unique |
| `displayName` | Yes | text |
| `dataCategory` | Yes | `raw, processed, derived, imported, reference, temporary, archive, custom` |
| `sourceType` | Yes | `"filesystem"` (the others are DRAFT — do not emit them) |
| `filesystemSource` | Yes | `{ rootStoragePaths, entityLayout, metadataMapping }` |
| `access` | No | `"read"` (default) or `"readwrite"`; emit `readwrite` only for locations a tool writes to |
| `derivedFrom` | No | identifiers of source locations |
| `description`, `tags`, `customProperties`, `uuid` | No | |

Never put `rootStoragePaths` or `entityLayout` directly on the location — they go inside `filesystemSource`. Never put `entityRelationships` inside a location.

## `rootStoragePaths`

Each: `identifier`, `path` (required); optional `environment`, `storageType` (`local, external, network, cloud, removable, virtual`), `volumeName`, `priority`, `uuid`, `customProperties`. There is no `isAvailable`.

## `entityLayout`

An array, outermost level first. Each level:

- `name` (required, unique, `^[A-Za-z][A-Za-z0-9_-]*$`).
- `entityType`: an `entityTypes` name — **omit it** for a structural level (a date folder, a fixed `processed` folder). Do not write `"other"`.
- `matchPattern` (regex) **or** `pathComponentTemplate` — one is required unless `isVariable: false`, which requires `fixedName` instead.
- `fileSystemType`: `"folder"` (default) or `"file"`. Use `"file"` when the files of many entities share one folder; it must be the last level.
- `excludePatterns`, `isRequired`, `filePatterns`, `customProperties` optional.

Reference levels by **name** from extraction rules.

## `filePatterns`

Each: `pattern` (required regex on the file name); optional `name`, `isRequired`, `cardinality` (`one` | `many`), `description`. The pattern may contain `{field_key}` tokens for the entity's own metadata: `"^{session_id}_raw\\.tif$"`. No `role`, `format`, `groupKey` or `metadataExtractors` — those do not exist.

## `metadataMapping`

An **array** of `{ "metadataRef": key, "extraction": {...} }`. The extraction object:

| `method` | Required fields | Rule |
|----------|-----------------|------|
| `substring` | `pattern` | A Python slice `start:stop` — `"0:8"`, `"9:"`, `":-4"`, `":"`. Never `"0:end"`. |
| `regex` | `pattern` | Value is the first capture group. Unnamed groups only; escape dots. |
| `template` | `pattern` | `"{session_date}_{subject_id}"` referencing other fields. |
| `fixed` | `value` | A constant. |
| `function` | `extractorFunction` | **Do not emit by default.** It needs code in every reader. Propose it only when no declarative rule can express the value, and say so. |

Plus `entityLayoutLevel` (a level **name**; `null` means the whole relative path), `valueFormat` for date/time fields in LDML notation (`"yyyyMMdd"`, `"yyyy_MM_dd"`, `"HH_mm_ss"`, `"yyMMdd"`; only the tokens `yyyy yy MM dd HH mm ss` are portable, and a two-digit year falls in 1969–2068), and optional `normalize`.

The methods `filename` and `filepath` do not exist; use `substring` with `":"`.

## Cross-reference rules (checked by readers)

- Every `identifierRef`, `metadataRef` and `{token}` names a key in `metadataDefinitions`.
- Every `ofEntity`, layout `entityType`, `sourceEntity`, `targetEntity` names an `entityTypes` entry.
- Every `derivedFrom` and `preferences.defaultDataLocationIdentifier` names a `dataLocations` identifier.
- Every extraction `entityLayoutLevel` string names a level in that location's layout.
- Identity extraction rules produce the **same value** for the same entity in every location.

## Common mistakes

1. Placing `rootStoragePaths`/`entityLayout` on the location instead of inside `filesystemSource`.
2. An entity type without `identifierRef`.
3. `"0:end"` — not a slice.
4. `"entityType": "other"` — omit the field instead.
5. Emitting `function` extractors for things a regex can do.
6. Adding `isAvailable`, `role`, `groupKey`, or any key not listed here.
7. Making `metadataMapping` an object, or `metadataDefinitions` an array.
8. Using named regex groups — dialects differ between MATLAB and Python.

## Complete example

Directory listing:

```
/data/raw/
├── m110/
│   ├── 20250523_baseline/
│   └── 20250601_stim/
└── m220/
    └── 20250524_baseline/
```

Config:

```json
{
  "schemaVersion": "0.1.0",
  "entityTypes": [
    { "name": "subject", "isPrimary": true, "identifierRef": "subject_id" },
    { "name": "session", "identifierRef": "session_id" }
  ],
  "entityRelationships": [
    { "sourceEntity": "subject", "targetEntity": "session", "relationType": "oneToMany", "relationName": "hasSessions" }
  ],
  "metadataDefinitions": {
    "subject_id": { "name": "subject_id", "title": "Subject ID", "dataType": "string", "ofEntity": "subject", "validation": { "pattern": "^m\\d{3}$" } },
    "session_id": { "name": "session_id", "title": "Session ID", "dataType": "string", "ofEntity": "session", "validation": { "pattern": "^\\d{8}_[a-z]+$" } },
    "session_date": { "name": "session_date", "title": "Session date", "dataType": "date", "ofEntity": "session" },
    "protocol": { "name": "protocol", "title": "Protocol", "dataType": "string", "ofEntity": "session" }
  },
  "dataLocations": [
    {
      "identifier": "raw",
      "displayName": "Raw data",
      "description": "One folder per subject, one folder per session named <date>_<protocol>.",
      "dataCategory": "raw",
      "access": "read",
      "sourceType": "filesystem",
      "filesystemSource": {
        "rootStoragePaths": [
          { "identifier": "server", "path": "/data/raw", "storageType": "network" }
        ],
        "entityLayout": [
          { "name": "subjects", "entityType": "subject", "matchPattern": "^m\\d{3}$" },
          { "name": "sessions", "entityType": "session", "matchPattern": "^\\d{8}_[a-z]+$", "excludePatterns": ["^\\..*"] }
        ],
        "metadataMapping": [
          { "metadataRef": "subject_id",   "extraction": { "method": "substring", "pattern": ":",   "entityLayoutLevel": "subjects" } },
          { "metadataRef": "session_id",   "extraction": { "method": "substring", "pattern": ":",   "entityLayoutLevel": "sessions" } },
          { "metadataRef": "session_date", "extraction": { "method": "substring", "pattern": "0:8", "valueFormat": "yyyyMMdd", "entityLayoutLevel": "sessions" } },
          { "metadataRef": "protocol",     "extraction": { "method": "regex",     "pattern": "^\\d{8}_([a-z]+)$", "entityLayoutLevel": "sessions" } }
        ],
        "pathTemplate": "{rootPath}/{subject_id}/{session_id}"
      }
    }
  ]
}
```

## Validate, then dry-run

```bash
pip install -e .                                  # from a clone of the repository
dsm validate my-dataset.json                      # schema + cross-reference rules
dsm listing raw main /path/to/data -o listing.json
dsm walk my-dataset.json listing.json             # what the config finds in the listing
```

`dsm validate` checks the schema and the cross-reference rules. `dsm walk` reports entities found per type, files no rule accounts for (`Unmatched`), incomplete entities and unresolved extractors — read it and revise the config until the counts match the dataset. A listing can also be built from `find` output with `dsm listing --text`, so no filesystem access is needed.
