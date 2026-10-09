# metadataDefinitions

`metadataDefinitions` is a top-level object whose keys are metadata field identifiers (`^[A-Za-z_][A-Za-z0-9_]*$`). Each value is a metadata definition. The keys are the shared vocabulary every data location, identity declaration and template token refers to.

`additionalProperties` is `false` on a definition and on its `validation` object.

```json
"metadataDefinitions": {
  "session_id": {
    "name": "session_id",
    "title": "Session ID",
    "ofEntity": "session",
    "dataType": "string",
    "validation": { "pattern": "^m\\d{3}-\\d{8}-\\d{3}$" }
  },
  "imaging_depth": {
    "name": "imaging_depth",
    "title": "Imaging depth",
    "ofEntity": "recording",
    "dataType": "number",
    "unit": "um",
    "validation": { "minimum": 0, "maximum": 1000 }
  }
}
```

## Fields

### `name` *(required)*

Human-readable name. Conventionally the same as the key.

### `ofEntity` *(required)*

The entity type this field belongs to. Must match a name in `entityTypes`. A field is extracted once per instance of that entity type.

### `dataType` *(required)*

| Value | Description |
|-------|-------------|
| `string` | Text |
| `number` | Floating-point number |
| `integer` | Whole number |
| `date` | Calendar date — parsed with the extraction rule's `valueFormat` |
| `time` | Time of day — parsed with `valueFormat` |
| `datetime` | Date and time — parsed with `valueFormat` |
| `boolean` | True/false |
| `array` | List of values |
| `object` | Structured object |

In [entity records](entity-record.md), `date`, `time` and `datetime` values are ISO 8601 strings.

### `title`, `description`, `unit`, `defaultValue`

Display name, prose, unit of measurement (UCUM notation recommended: `"um"`, `"Hz"`, `"s"`), and the value to use when extraction yields nothing.

On an identity field, `defaultValue` is applied before the identity is checked, so an optional part of a composite identity can default: a BIDS-style run index that is absent when the task was run once defaults to `1`, and the files become the acquisition `(task, 1)` rather than `no-match`. A default on a single-field identity is refused (`reference-integrity`), because every entry that matched the level but yielded no value would become one entity and nothing would be reported `no-match`.

### `validation`

| Field | Type | Applies to | Description |
|-------|------|-----------|-------------|
| `pattern` | string (regex) | string | Value must match |
| `minLength` / `maxLength` | integer | string | Length bounds |
| `minimum` / `maximum` | number | number, integer | Inclusive bounds |
| `enum` | array | any | Allowed values |

`validation.pattern` has a second job: when a level has a `pathComponentTemplate` but no `matchPattern`, each `{token}` in the template matches the referenced field's `validation.pattern`. Give identity fields a pattern.

---

## Relationship to metadataMapping

`metadataDefinitions` declares *what* a field is. Each data location's `metadataMapping` declares *how* to extract it from that location's naming convention. The same field is extracted differently in each location:

```
metadataDefinitions.session_id
    ├── raw       metadataMapping: regex "_(m\d{3}-\d{8}-\d{3})$" on level "sessions"
    └── processed metadataMapping: regex "^session-(.+)$"          on level "sessions"
```

Both produce the same `session_id`, so the two locations' sessions can be matched. See [Metadata Extraction](metadata-extraction.md).

## Relationship to identifierRef

When an entity type declares `"identifierRef": "session_id"`, the value extracted for `session_id` is the identity of `session` entities across all locations. Extraction rules for identity fields must therefore produce identical values everywhere; use `normalize` where conventions differ.
