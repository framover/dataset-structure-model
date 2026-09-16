# dataLocations

`dataLocations` is a required array of data location objects. Each entry describes one logical collection of data — typically one category (raw, processed, derived, …) with its own folder tree.

`additionalProperties` is `false` on the `dataLocation` object.

## Required fields

### `identifier`

| | |
|--|--|
| Type | `string`, `^[A-Za-z][A-Za-z0-9_-]*$` |
| Example | `"two-photon-raw"` |

Unique identifier of this location within the config. Used in cross-references (`derivedFrom`, `preferences.defaultDataLocationIdentifier`) and in [entity records](entity-record.md). Treat it as stable; tools that must survive renames should use `uuid`.

---

### `displayName`

| | |
|--|--|
| Type | `string` |

Human-readable name shown in UIs and reports.

---

### `dataCategory`

| | |
|--|--|
| Type | `string` (enum) |
| Default | `"raw"` |

The role of this location in the data lifecycle. See [Data Location Categories](../guides/data-location-categories.md).

| Value | Meaning |
|-------|---------|
| `raw` | Original unprocessed data from instruments |
| `processed` | Cleaned or reformatted data |
| `derived` | Analysis results and extracted features |
| `imported` | Data from external sources |
| `reference` | Standard or normative comparison data |
| `temporary` | Intermediate processing outputs |
| `archive` | Historical or completed project data |
| `custom` | Project-specific category |

The category says nothing about permission; that is `access`.

---

### `sourceType`

| | |
|--|--|
| Type | `string` (enum) |
| Values | `"filesystem"` \| `"spreadsheet"` \| `"database"` \| `"api"` |

`filesystem` is the core and requires `filesystemSource`. The other three are **DRAFT**: they require their source block plus `entityType`, and readers may reject them.

---

## Optional fields

### `access`

| | |
|--|--|
| Type | `string` (enum) |
| Values | `"read"` (default) \| `"readwrite"` |

Whether tools may create folders and write files here. Independent of `dataCategory`: an `imported` location can be writable, a `processed` mirror can be read-only. The default is `read` because describing existing data does not grant write access — set `readwrite` explicitly on locations a tool is allowed to populate.

---

### `uuid`

| | |
|--|--|
| Type | `string` |

Optional stable identifier for tools that persist references to this location outside the config (a metadata table that records where each entity was found, for example). Unlike `identifier`, a `uuid` never changes once assigned.

---

### `filesystemSource`

| | |
|--|--|
| Type | `object` |
| Required when | `sourceType` is `"filesystem"` |

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `rootStoragePaths` | Yes | array (≥1) | Root of the tree, one entry per environment. See below. |
| `entityLayout` | Yes | array (≥1) of `entityLayoutLevel` | Hierarchy below the root. See [entityLayout](entity-layout.md). |
| `metadataMapping` | No | array | How global metadata fields are extracted here. See [Metadata Extraction](metadata-extraction.md). |
| `pathTemplate` | No | string | Informational path template, e.g. `"{rootPath}/{subject_id}/{session_id}"`. |
| `additionalFolders` | No | array of string | Folder names inside an innermost entity folder that are not entities. |

**`rootStoragePaths`** — each entry:

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `identifier` | Yes | string | Unique within the location; referenced from entity records |
| `path` | Yes | string | Absolute file system path |
| `uuid` | No | string | Stable identifier for tools that persist references |
| `environment` | No | string | Environment this path is for (matches `preferences.environmentIdentifier`); omit for single-environment configs |
| `storageType` | No | enum | `local` \| `external` \| `network` \| `cloud` \| `removable` \| `virtual` |
| `volumeName` | No | string | Disk/volume name; readers may use it to re-resolve a root whose mount point or drive letter changed |
| `priority` | No | integer | Selection order when several paths match the environment (lower wins, default 1) |
| `customProperties` | No | object | Tool-specific data |

There is no availability flag: whether a path is reachable is runtime state, not configuration. Readers report it.

---

### `description`, `tags`, `customProperties`

Free text, free-form tags, and a free-form object for anything the schema does not model. Readers preserve `customProperties` but do not interpret it.

---

### `derivedFrom`

| | |
|--|--|
| Type | `array` of location identifiers |

The locations this one was produced from. Provenance only — it does not say how. Tools also use it to find the source entities whose metadata fills `pathComponentTemplate` tokens when generating output paths in a `readwrite` location.

```json
{
  "identifier": "processed",
  "dataCategory": "processed",
  "access": "readwrite",
  "derivedFrom": ["raw"]
}
```

---

### `entityType`, `spreadsheetSource`, `databaseSource`, `apiSource` — DRAFT

Placeholders for entity records that come from a spreadsheet, a database table, or an API rather than a folder tree. They validate but are outside the core; readers may reject them and their shape may change at any time.
