# Raw and Processed Two-Photon

Source: [`examples/raw_processed_two_photon.json`](https://github.com/framover/dataset-structure-model/blob/main/examples/raw_processed_two_photon.json). Expected reader output, with a listing: [`conformance/raw-processed-matching/`](https://github.com/framover/dataset-structure-model/tree/main/conformance/raw-processed-matching).

The case the DSM was designed for: the same sessions in two locations with different hierarchies and different naming.

```
Raw (as written by the microscope software)         Processed (written by the analysis tool)
D:\Data\TwoPhoton\                                  /Volumes/DATA/Processed/TwoPhoton/
└── 2025_05_23/                                     └── subject-m110/
    └── 2025_05_23_10_00_00_m110-20250523-001/          └── session-m110-20250523-001/
        ├── *.raw                                           ├── m110-20250523-001_two_photon_motion_corrected.tif
        └── *.ini                                           └── m110-20250523-001_roi_signals_*.mat
```

## Raw: a structural date level

```json
"entityLayout": [
  { "name": "dates",    "matchPattern": "^\\d{4}_\\d{2}_\\d{2}$", "customProperties": { "examplePath": "2025_05_23" } },
  { "name": "sessions", "entityType": "session",
    "matchPattern": "^\\d{4}_\\d{2}_\\d{2}_\\d{2}_\\d{2}_\\d{2}_m\\d{3}-\\d{8}-\\d{3}$",
    "filePatterns": [
      { "name": "two_photon_movie",   "pattern": "\\.raw$", "isRequired": true, "cardinality": "one" },
      { "name": "acquisition_config", "pattern": "\\.ini$", "cardinality": "one" }
    ] }
]
```

`dates` has no `entityType`: it is a structural level. It is walked, a session can read its date from it, but it plays no part in identity — which is what lets a raw session match a processed one whose path has no date folder at all. `customProperties` carries a configuration UI's example folder; the schema preserves it without interpreting it.

```json
"metadataMapping": [
  { "metadataRef": "session_id",   "extraction": { "method": "regex",     "pattern": "_(m\\d{3}-\\d{8}-\\d{3})$", "entityLayoutLevel": "sessions" } },
  { "metadataRef": "subject_id",   "extraction": { "method": "regex",     "pattern": "_(m\\d{3})-\\d{8}-\\d{3}$",  "entityLayoutLevel": "sessions" } },
  { "metadataRef": "session_date", "extraction": { "method": "substring", "pattern": ":", "valueFormat": "yyyy_MM_dd", "entityLayoutLevel": "dates" } },
  { "metadataRef": "session_time", "extraction": { "method": "regex",     "pattern": "^\\d{4}_\\d{2}_\\d{2}_(\\d{2}_\\d{2}_\\d{2})_", "valueFormat": "HH_mm_ss", "entityLayoutLevel": "sessions" } }
]
```

There is no subject level in the raw location. `subject_id` is read from the session folder name and identifies the session's parent subject.

## Processed: generated names, `readwrite`, `derivedFrom`

```json
{
  "identifier": "processed",
  "uuid": "b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e",
  "dataCategory": "processed",
  "access": "readwrite",
  "derivedFrom": ["raw"],
  "filesystemSource": {
    "entityLayout": [
      { "name": "subjects", "entityType": "subject", "pathComponentTemplate": "subject-{subject_id}", "matchPattern": "^subject-m\\d{3}$" },
      { "name": "sessions", "entityType": "session", "pathComponentTemplate": "session-{session_id}",
        "filePatterns": [
          { "name": "motion_corrected", "pattern": "^{session_id}_two_photon_motion_corrected\\.tif$", "cardinality": "one" },
          { "name": "roi_signals",      "pattern": "^{session_id}_roi_signals_.+\\.mat$",             "cardinality": "many" }
        ] }
    ]
  }
}
```

- `access: readwrite` — the analysis tool may create session folders here; the raw location is `read`.
- `pathComponentTemplate` on both levels — a tool writing session `m110-20250523-001` of subject `m110` creates `subject-m110/session-m110-20250523-001/`. The `sessions` level has no `matchPattern`; it is derived from the template and `session_id`'s `validation.pattern`: `^session-m\d{3}-\d{8}-\d{3}$`.
- `uuid` on the location and on root paths — a tool that records where each session lives stores these, and survives a rename of `identifier`.

## Matching across locations

Both locations extract `session_id` and `subject_id` with the same values. Because `session` declares `identifierRef: "session_id"`, the raw folder `2025_05_23_10_00_00_m110-20250523-001` and the processed folder `session-m110-20250523-001` are the same session, and a reader emits one entity record with two `locations` entries.

## Environments

Raw has root paths for `windows-lab` and `mac-analysis`; processed exists only on `mac-analysis`. The active environment comes from `preferences` — kept in a git-ignored `raw_processed_two_photon.local.json` on each machine rather than in the shared config.
