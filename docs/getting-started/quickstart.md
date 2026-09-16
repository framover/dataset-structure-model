# Quick Start

Create a minimal valid DSM config and validate it.

## Prerequisites

- A text editor
- Python 3.9+ with `jsonschema` (for validation):

```bash
pip install jsonschema
```

## Step 1: Get the schema

```bash
git clone https://github.com/framover/dataset-structure-model.git
```

The schema is `schema/DatasetStructureModel.schema.json`.

## Step 2: Describe your data

Suppose your data looks like this:

```
/data/raw/
├── m110/                    ← subject folder
│   ├── 20250523_session1/   ← session folder
│   └── 20250601_session2/
└── m220/
    └── 20250524_session1/
```

Create `my-dataset.json`:

```json
{
  "schemaVersion": "1.0.0",
  "entityTypes": [
    { "name": "subject", "identifierRef": "subject_id" },
    { "name": "session", "identifierRef": "session_id" }
  ],
  "metadataDefinitions": {
    "subject_id": { "name": "subject_id", "title": "Subject ID", "ofEntity": "subject", "dataType": "string", "validation": { "pattern": "^m\\d{3}$" } },
    "session_id": { "name": "session_id", "title": "Session ID", "ofEntity": "session", "dataType": "string" },
    "session_date": { "name": "session_date", "title": "Session date", "ofEntity": "session", "dataType": "date" }
  },
  "dataLocations": [
    {
      "identifier": "raw",
      "displayName": "Raw data",
      "dataCategory": "raw",
      "access": "read",
      "sourceType": "filesystem",
      "filesystemSource": {
        "rootStoragePaths": [
          { "identifier": "my-machine", "path": "/data/raw" }
        ],
        "entityLayout": [
          { "name": "subjects", "entityType": "subject", "matchPattern": "^m\\d{3}$" },
          { "name": "sessions", "entityType": "session", "matchPattern": "^\\d{8}_.+$" }
        ],
        "metadataMapping": [
          { "metadataRef": "subject_id",   "extraction": { "method": "substring", "pattern": ":",   "entityLayoutLevel": "subjects" } },
          { "metadataRef": "session_id",   "extraction": { "method": "regex",     "pattern": "^\\d{8}_(.+)$", "entityLayoutLevel": "sessions" } },
          { "metadataRef": "session_date", "extraction": { "method": "substring", "pattern": "0:8", "valueFormat": "yyyyMMdd", "entityLayoutLevel": "sessions" } }
        ]
      }
    }
  ]
}
```

Reading it top to bottom: two entity types, each identified by a metadata field; three fields; one data location whose root is `/data/raw`, with subject folders at the first level and session folders at the second; and three rules that read the fields out of the folder names. There is no `preferences` block — that is per-machine and goes in a local overlay when you need one.

## Step 3: Validate

```bash
pip install -e .                 # once, from the clone; adds the `dsm` command
dsm validate my-dataset.json
```

Then see what the config finds in your data:

```bash
dsm listing raw my-machine /data/raw -o listing.json
dsm walk my-dataset.json listing.json
```

The report lists entities per type, incomplete entities, and any file or folder no rule accounts for.

## Step 4: Add more detail

- Add a processed location with [`derivedFrom`](../reference/data-locations.md#derivedfrom), `access: readwrite` and [`pathComponentTemplate`](../reference/entity-layout.md#pathcomponenttemplate)
- Describe the files inside each session with [`filePatterns`](../reference/entity-layout.md#filepatterns)
- Handle a folder where all sessions' files are mixed together with a [file level](../reference/entity-layout.md#filesystemtype)
- Add [environment-specific root paths](../reference/data-locations.md#filesystemsource)

Then read the [examples](../examples/index.md) or the [Usage Guide](../guides/usage-guide.md).
