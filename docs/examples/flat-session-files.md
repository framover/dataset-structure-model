# Flat Session Files

Source: [`examples/flat_session_files.json`](https://github.com/framover/dataset-structure-model/blob/main/examples/flat_session_files.json). Expected reader output, with a listing: [`conformance/flat-session-files/`](https://github.com/framover/dataset-structure-model/tree/main/conformance/flat-session-files).

The layout that "one folder per session" models cannot describe: an acquisition system exported every file of every session into a single folder.

```
/Volumes/lab-nas/export/
├── m110-20250510-001_raw.tif
├── m110-20250510-001_meta.json
├── m110-20250510-001_behavior_01.csv
├── m110-20250510-001_behavior_02.csv
├── m110-20250510-002_raw.tif
└── ...
```

## One file level

```json
"entityLayout": [
  {
    "name": "session-files",
    "entityType": "session",
    "fileSystemType": "file",
    "matchPattern": "^m\\d{3}-\\d{8}-\\d{3}_.+$",
    "excludePatterns": ["^\\..*"],
    "filePatterns": [
      { "name": "raw_movie", "pattern": "^{session_id}_raw\\.tif$",            "isRequired": true, "cardinality": "one" },
      { "name": "metadata",  "pattern": "^{session_id}_meta\\.json$",           "cardinality": "one" },
      { "name": "behavior",  "pattern": "^{session_id}_behavior_\\d{2}\\.csv$", "cardinality": "many" }
    ]
  }
]
```

`fileSystemType: "file"` says entries at this level are files. The reader extracts `session_id` from each file name, and **every file with the same id is one session**. The session then resolves to the set of its files.

`filePatterns` say which files belong to a session. The `{session_id}` token is replaced by the exact id of the session being resolved before the pattern is applied, so `m110-20250510-001` never picks up `m110-20250510-0010_raw.tif`. `raw_movie` is required and single; `behavior` is a numbered series.

## Extraction from file names

```json
"metadataMapping": [
  { "metadataRef": "session_id",   "extraction": { "method": "regex",     "pattern": "^(m\\d{3}-\\d{8}-\\d{3})_",  "entityLayoutLevel": "session-files" } },
  { "metadataRef": "subject_id",   "extraction": { "method": "substring", "pattern": "0:4",                         "entityLayoutLevel": "session-files" } },
  { "metadataRef": "session_date", "extraction": { "method": "regex",     "pattern": "^m\\d{3}-(\\d{8})-", "valueFormat": "yyyyMMdd", "entityLayoutLevel": "session-files" } }
]
```

The component at a file level is the file name including its extension. `subject_id` belongs to `subject`, which has no level of its own here, so the value read from the session file identifies the session's parent subject.

## What a reader produces

For `m110-20250510-001` the [entity record](../reference/entity-record.md) lists the four files, groups them under the pattern names, and reports the session complete:

```json
{
  "entityType": "session",
  "identity": { "session_id": "m110-20250510-001" },
  "parents": [ { "entityType": "subject", "identity": { "subject_id": "m110" } } ],
  "locations": [
    {
      "dataLocationIdentifier": "recorded",
      "rootStoragePathIdentifier": "lab-nas",
      "fileSystemType": "file",
      "paths": ["m110-20250510-001_raw.tif", "m110-20250510-001_meta.json", "m110-20250510-001_behavior_01.csv", "m110-20250510-001_behavior_02.csv"],
      "files": {
        "raw_movie": ["m110-20250510-001_raw.tif"],
        "metadata":  ["m110-20250510-001_meta.json"],
        "behavior":  ["m110-20250510-001_behavior_01.csv", "m110-20250510-001_behavior_02.csv"]
      },
      "isComplete": true
    }
  ],
  "metadata": { "session_id": "m110-20250510-001", "subject_id": "m110", "session_date": "2025-05-10" }
}
```

A session with only a `_raw.tif` is still complete (`metadata` and `behavior` are not required) and its `files` entries for those patterns are empty arrays. A file that carries a session's id but matches no pattern (`_extra.bin`) is still in the session's `paths`. Subjects, which have no folder of their own here, get records with `locations: []`.
