# Top-Level Structure

A DSM config is a JSON object. `additionalProperties` is `false` — no keys outside this list are permitted.

## Required properties

### `schemaVersion`

| | |
|--|--|
| Type | `string` |
| Pattern | `^\d+\.\d+\.\d+$` |
| Example | `"0.1.0"` |

The version of the DSM schema this config conforms to, using [semantic versioning](https://semver.org/). Readers use it to decide compatibility.

---

### `dataLocations`

| | |
|--|--|
| Type | `array` of [`dataLocation`](data-locations.md) |
| Min items | 1 |

The core of the config. Each item describes one folder tree — its category, access, root paths, entity hierarchy and metadata extraction rules.

---

## Optional properties

### `entityTypes`

| | |
|--|--|
| Type | `array` of entity type objects |

Declares the semantic entity types present in this dataset. Every entity type referenced by an `entityLayout` level or by a metadata definition's `ofEntity` must be declared here. Each item:

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | Yes | string | Entity type name (e.g. `"subject"`, `"session"`) |
| `identifierRef` | One of | string | Key in `metadataDefinitions` that identifies an instance of this type |
| `identifierRefs` | One of | array of strings | Composite identity key; all listed fields must belong to this entity type |
| `description` | No | string | What this entity represents |
| `isPrimary` | No | boolean | Whether this is the primary entity type |
| `color` | No | string | UI hint colour (e.g. `"#FF0000"`) |

**Identity is required**: exactly one of `identifierRef` and `identifierRefs` must be present. The identity of an instance is its own key plus the keys of its entity-typed ancestors; structural levels are skipped. There is no fallback to folder names — that would make identity depend on which location an entity was found in. See [Core Concepts → Cross-location entity matching](../getting-started/concepts.md#cross-location-entity-matching).

---

### `entityRelationships`

| | |
|--|--|
| Type | `array` of [`entityRelationship`](entity-relationships.md) |

Semantic relationships between entity types, independent of physical storage.

---

### `metadataDefinitions`

| | |
|--|--|
| Type | `object` (identifier keys → metadata definition objects) |

Global dictionary of metadata fields. Keys match `^[A-Za-z_][A-Za-z0-9_]*$` and are what `identifierRef`, `metadataRef` and `{token}` references point to. See [metadataDefinitions](metadata-definitions.md).

---

### `preferences`

| | |
|--|--|
| Type | `object` |

Runtime context: which environment is active and which data location to use by default. Optional in the shared config, and readers prefer a sibling `<config>.local.json` overlay when one exists. See [preferences](preferences.md).
