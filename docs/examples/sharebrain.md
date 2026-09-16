# SHAREbrain Toy Dataset

Source: [`examples/sharebrain_toy_dataset.json`](https://github.com/framover/dataset-structure-model/blob/main/examples/sharebrain_toy_dataset.json).

A three-level hierarchy written by the Begonia acquisition software: session → recording → trial, with the subject encoded in the session folder name.

```
/Volumes/Data HD/Data/SHAREbrain/Luca_Toy_Dataset/
└── 20250312_MelFibra#03_Bilateral_Opto_Day01/     ← session (date, subject, protocol, day)
    ├── Log.csv
    └── 2025-03-12_101500/                          ← recording (start date-time)
        ├── Log.csv
        └── trial_001/                              ← trial
            ├── eeg_4_ch.csv    (required)
            ├── Diode.csv
            ├── Wheel.csv
            └── ...
```

## Identity

```json
"entityTypes": [
  { "name": "subject",   "isPrimary": true, "identifierRef": "subject_id" },
  { "name": "session",   "identifierRefs": ["session_date", "protocol", "day_number"] },
  { "name": "recording", "identifierRef": "recording_datetime" },
  { "name": "trial",     "identifierRef": "trial_number" }
]
```

A session has no single id field; it is identified by the combination of date, protocol and day — `identifierRefs`. The subject is not part of that key: it is the session's parent, identified by `subject_id` extracted from the same folder name. A recording is identified by its start time within its session; a trial by its number within its recording.

## Layout and extraction

The three levels are folder levels with `matchPattern`s and `filePatterns` (only `eeg_4_ch.csv` is `isRequired`). All metadata comes from regex capture groups on the session, recording and trial folder names; `session_date` and `recording_datetime` carry `valueFormat`s (`yyyyMMdd`, `yyyy-MM-dd_HHmmss`) so readers parse them as dates.

```json
{ "metadataRef": "subject_id",
  "extraction": { "method": "regex", "pattern": "^\\d{8}_([A-Za-z0-9#]+)_[A-Za-z0-9_]+_Day\\d+$", "entityLayoutLevel": 0 } }
```

This example still references levels by 0-based index; by name (`"sessions"`) is preferred.
