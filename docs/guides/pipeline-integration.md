# Pipeline Integration

The Dataset Structure Model is a **data contract**, not a pipeline definition. It says where data lives and how it is organised; pipeline tools (Nextflow, Snakemake, …) say how data is processed. This page explains how the two fit together.

---

## Separation of concerns

| Responsibility | Tool |
|---------------|------|
| Where is the data? | DSM (`rootStoragePaths`) |
| How is it organised? | DSM (`entityLayout`, `metadataMapping`, `filePatterns`) |
| What are the entities and which files belong to each? | DSM → [entity records](../reference/entity-record.md) |
| May a tool write here? | DSM (`access`) |
| How was it produced? | DSM (`derivedFrom`) |
| What processing steps ran, with what parameters? | Pipeline tool |

A pipeline reads entity records to find its inputs, writes outputs into a location declared `access: readwrite`, and the DSM records the lineage.

---

## Declaring an output location

```json
{
  "identifier": "motion-corrected",
  "displayName": "Motion-corrected imaging",
  "dataCategory": "processed",
  "access": "readwrite",
  "derivedFrom": ["raw"],
  "sourceType": "filesystem",
  "filesystemSource": {
    "rootStoragePaths": [
      { "identifier": "analysis-server", "path": "/data/processed/motion-corrected", "storageType": "local", "environment": "linux-server" }
    ],
    "entityLayout": [
      { "name": "subjects", "entityType": "subject", "pathComponentTemplate": "subject-{subject_id}" },
      { "name": "sessions", "entityType": "session", "pathComponentTemplate": "session-{session_id}",
        "filePatterns": [ { "name": "movie", "pattern": "^{session_id}_motion_corrected\\.tif$", "cardinality": "one" } ] }
    ],
    "metadataMapping": [
      { "metadataRef": "subject_id", "extraction": { "method": "regex", "pattern": "^subject-(.+)$", "entityLayoutLevel": "subjects" } },
      { "metadataRef": "session_id", "extraction": { "method": "regex", "pattern": "^session-(.+)$", "entityLayoutLevel": "sessions" } }
    ]
  }
}
```

Three things make this location writable and round-trippable: `access: readwrite`, a `pathComponentTemplate` on every variable level (so output names are generated, and `matchPattern` is derived from the same template), and `metadataMapping` rules that read the generated names back.

---

## Resolving inputs

1. Read the output location's `derivedFrom` to find the source location.
2. Have a reader walk the source location; it yields one entity record per session with `paths` and `files` per named pattern.
3. Select the root path whose `environment` matches the active environment (from `preferences` or the local overlay).

No paths are hardcoded in the pipeline; the config is the single source of truth.

---

## Generating output paths

For each source entity record:

1. Take its `identity` and `parents` (e.g. `session_id`, `subject_id`).
2. Substitute into each level's `pathComponentTemplate`: `subject-m110/session-m110-20250523-001/`.
3. Name output files so they match the level's `filePatterns` — `{session_id}_motion_corrected.tif` — so the next reader finds them under the pattern's name.

Reading back works through the same templates and patterns, so generation and parsing cannot drift apart.

Both readers implement steps 1 and 2: `dsm.generate_path(config, location, entity_type, values)` in Python and `dsm.generatePath(config, location, entityType, values)` in MATLAB return the entity's path relative to the location's root (folders end with `/`). `values` is an entity record's `metadata`, or the same fields for an entity that does not exist yet. A structural level contributes its `fixedName`, or its `pathComponentTemplate` when it is variable. Every generated component must match its level's pattern, so the next walk finds what was written. Generation fails with a code:

| Code | When |
|------|------|
| `unknown-location` | The data location does not exist |
| `not-writable` | The location's `access` is not `readwrite` |
| `no-level` | The entity type has no level in the location |
| `no-template` | A variable level on the way has no `pathComponentTemplate` |
| `missing-value` | A template token has no value |
| `name-mismatch` | A generated component does not match its level's pattern |

File names (step 3) stay with the tool: `filePatterns` are regular expressions, not templates, so a tool names its files and checks them against the pattern.

---

## Matching outputs to sources

After a run, tools connect processed entities to their sources through identity: two sessions are the same when their `session_id` (and parent `subject_id`) are equal, in any location. No pairwise configuration.

---

## What not to store in the DSM

Job ids, completion timestamps, error logs, whether a root path is currently mounted — runtime state belongs to the pipeline tool or the reader's report. The config describes structure; it does not change because a job ran.
