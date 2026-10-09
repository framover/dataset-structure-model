# entityLayout

`entityLayout` is an ordered array inside `filesystemSource`. Each item is one level of the hierarchy below the root, outermost first. Together they say how folders and files map to entities.

`additionalProperties` is `false` on `entityLayoutLevel`.

## Required fields

### `name`

| | |
|--|--|
| Type | `string`, `^[A-Za-z][A-Za-z0-9_-]*$` |
| Example | `"subjects"`, `"sessions"`, `"dates"` |

Name of the level, unique within the layout. Extraction rules reference levels by this name.

---

## Optional fields

### `entityType`

| | |
|--|--|
| Type | `string` |
| Example | `"subject"`, `"session"` |

The entity type that entries at this level represent; must match a name in `entityTypes`.

**Omit it for a structural level** — a folder that is part of the path but not an entity, such as a date folder above the sessions or a fixed `processed/` folder. Structural levels are walked and can be read by extraction rules, but they are skipped when building entity identity:

```json
"entityLayout": [
  { "name": "dates",    "matchPattern": "^\\d{4}_\\d{2}_\\d{2}$" },
  { "name": "sessions", "entityType": "session", "matchPattern": "^\\d{4}_\\d{2}_\\d{2}_\\d{6}_m\\d{3}-.+$" }
]
```

---

### `matchPattern`

| | |
|--|--|
| Type | `string` (regex, [portable subset](metadata-extraction.md#regex-portability)) |

Entries whose names match are entries at this level; others are ignored. Required for a variable level unless `pathComponentTemplate` is present.

---

### `pathComponentTemplate`

| | |
|--|--|
| Type | `string` |
| Example | `"session-{session_id}"`, `"{subject_id}_{acquisition_date}"` |

How an entry name is composed from metadata fields. Tokens in braces reference keys in `metadataDefinitions`. Two uses:

1. **Generation** — when writing to a `readwrite` location, tools substitute the source entity's metadata to build the folder name.
2. **Matching** — when `matchPattern` is absent, it is derived: each `{token}` becomes the referenced definition's `validation.pattern` if it has one, otherwise `[^/\\]+`; a token with a format (below) becomes `\d{N,}`; the result is anchored with `^` and `$`. Literal text between tokens is regex-escaped.

With `session_id` validated by `^m\d{3}-\d{8}-\d{3}$`, the template `session-{session_id}` derives `^session-m\d{3}-\d{8}-\d{3}$`.

**Token formats.** A token may carry a format, `{name:0Nd}`: the referenced field must be an `integer`, and the value is written zero-filled to `N` digits. This is the whole format grammar, width and zero-fill, which is what counters in file names need. `{acquisition_number:05d}` writes `1` as `00001` when a name is generated, matches `\d{5,}` when `matchPattern` is derived, and substitutes `00001` into `filePatterns` and `template` rules, so the counter stays a number in entity records and still round-trips into names. A format on a non-integer field is refused (`reference-integrity`).

---

### `fileSystemType`

| | |
|--|--|
| Type | `string` (enum) |
| Values | `"folder"` (default) \| `"file"` |

Whether entries at this level are folders or files. A file level must be the last level.

**At a file level, entities are groups of files.** Entity instances are keyed by the entity type's identity extracted from the file name: every file whose extracted identity is equal belongs to the same entity. The entity resolves to that set of files plus their parent folder. This is how a folder of files dumped together — `m110-20250510-001_raw.tif`, `m110-20250510-001_meta.json`, `m110-20250510-002_raw.tif`, … — becomes one session per id rather than one per file. Declare which files belong to an entity with `filePatterns`.

---

### `filePatterns`

| | |
|--|--|
| Type | `array` of file pattern objects |

The kinds of files that belong to an entity at this level. For a folder level: files inside the entity folder. For a file level: files in the parent folder that belong to the entity.

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `pattern` | Yes | string (regex) | Matched against file names. May contain `{token}` references to the entity's metadata fields; each token is replaced by the regex-escaped value for the entity being resolved. A token may carry a format, `{counter:05d}`, for an integer written zero-filled (see [token formats](#pathcomponenttemplate)). |
| `name` | No | string | Name of this file kind, unique within the level. Readers report matched files under it in entity records. |
| `isRequired` | No | boolean | At least one match must exist for the entity to be complete (default `false`). |
| `cardinality` | No | `"one"` \| `"many"` | Exactly one file or any number (default `"many"`). |
| `description` | No | string | What the file contains. |

```json
"filePatterns": [
  { "name": "raw_movie", "pattern": "^{session_id}_raw\\.tif$",          "isRequired": true, "cardinality": "one" },
  { "name": "behavior",  "pattern": "^{session_id}_behavior_\\d{2}\\.csv$", "cardinality": "many" }
]
```

Because the token is substituted with the exact identity, `m110-20250510-001` never claims the files of `m110-20250510-0010`. Braces that contain only digits and commas (`\d{2}`, `{1,3}`) are regex quantifiers, not tokens.

---

### `excludePatterns`

| | |
|--|--|
| Type | `array` of `string` |
| Default | `[]` |
| Example | `["^\\..*", "^temp$", "^backup$"]` |

Regular expressions for entry names to skip. Applied before `matchPattern`.

---

### `isRequired`

| | |
|--|--|
| Type | `boolean` |
| Default | `true` |

Whether this level must exist. A location need not contain every ancestor level of its entities — a processed location may hold session folders directly, with subject identity extracted from the session name. See [Metadata Extraction → Which entity a value belongs to](metadata-extraction.md#which-entity-a-value-belongs-to).

---

### `isVariable` and `fixedName`

| | |
|--|--|
| `isVariable` | `boolean`, default `true` |
| `fixedName` | `string`, required when `isVariable` is `false` |

`isVariable: false` marks a level whose single folder always has the same name, e.g. `"fixedName": "processed"`. Such a level is usually structural (no `entityType`).

---

### `customProperties`

| | |
|--|--|
| Type | `object` |

Tool-specific data about this level — a configuration UI's example folder, for instance. Preserved, not interpreted.

---

## Constraints

- A variable level (`isVariable` absent or `true`) needs `matchPattern` or `pathComponentTemplate`.
- A fixed level (`isVariable: false`) needs `fixedName`.
- A `file` level must be last.
- Level names are unique within the layout; `filePatterns` names are unique within the level.
