# Dataset Structure Model

**A JSON Schema standard for declaratively describing the structure of scientific datasets.**

The Dataset Structure Model (DSM) is a machine-actionable configuration format that captures how a scientific dataset is organised on disk — its folder hierarchy, entity types (subjects, sessions, recordings), naming conventions, and metadata extraction rules. It acts as a shared contract between researchers, tools, and AI agents.

---

## What problem does it solve?

Scientific datasets are notoriously heterogeneous. Raw data might live at `D:\Data\TwoPhoton\m110\20250523_session1\rec01\`, while processed data for the same session is at `/Volumes/DataDrive/Processed/m110\20250523_session1\processed\`. Tools need to understand both, know they refer to the same session, and know where to write derived outputs.

Without a formal description, every tool hardcodes assumptions about folder structure. With DSM, tools read a single config file that answers:

- **Where** is the data? (per environment, per storage type)
- **What** is the folder hierarchy? (subjects → sessions → recordings)
- **How** are entity identities extracted from folder and file names? (regex, substring, template)
- **How** do entities in different locations correspond to each other?
- **Which** files belong to each entity — even when many entities share one folder?

---

## Key features

- **Descriptive, not prescriptive** — describes your data as it exists; no reorganisation required
- **Multi-location** — a single config describes raw, processed, and derived data in separate folder trees
- **Cross-location entity matching** — declares how entities (e.g. sessions) are linked across locations with different naming conventions
- **Metadata-aware** — extraction rules pull metadata from folder and file names via regex, substring and templates
- **Multi-environment** — same dataset, different root paths for Windows lab, Mac analysis station, HPC cluster
- **LLM-ready** — strict, self-describing and small; an agent can write a config from a directory listing
- **Defined output** — readers emit [entity records](reference/entity-record.md), the same in every language
- **Pipeline-friendly** — integrates naturally with Nextflow, Snakemake, and similar tools

---

## Quick example

```json
{
  "schemaVersion": "0.1.0",
  "entityTypes": [
    { "name": "subject", "identifierRef": "subject_id" },
    { "name": "session", "identifierRef": "session_id" }
  ],
  "metadataDefinitions": {
    "subject_id": { "name": "subject_id", "ofEntity": "subject", "dataType": "string" },
    "session_id": { "name": "session_id", "ofEntity": "session", "dataType": "string" }
  },
  "dataLocations": [{
    "identifier": "raw",
    "displayName": "Raw data",
    "dataCategory": "raw",
    "sourceType": "filesystem",
    "filesystemSource": {
      "rootStoragePaths": [{ "identifier": "lab", "path": "/data/raw" }],
      "entityLayout": [
        { "name": "subjects", "entityType": "subject", "matchPattern": "^[A-Za-z0-9]+$" },
        { "name": "sessions", "entityType": "session", "matchPattern": "^\\d{8}_.*$" }
      ],
      "metadataMapping": [
        { "metadataRef": "subject_id", "extraction": { "method": "substring", "pattern": ":", "entityLayoutLevel": "subjects" } },
        { "metadataRef": "session_id", "extraction": { "method": "regex", "pattern": "^\\d{8}_(.+)$", "entityLayoutLevel": "sessions" } }
      ]
    }
  }]
}
```

---

## Navigation

<div class="grid cards" markdown>

- :material-rocket-launch: **[Quick Start](getting-started/quickstart.md)**

    Get a valid DSM config in minutes

- :material-book-open: **[Core Concepts](getting-started/concepts.md)**

    Understand entities, layouts, and metadata extraction

- :material-file-code: **[Schema Reference](reference/index.md)**

    Complete reference for every field and definition

- :material-lightbulb: **[Examples](examples/index.md)**

    A toy dataset, a flat folder of session files, and raw/processed two-photon data

</div>

---

## How this relates to existing tools

Almost every mechanism in DSM exists somewhere already — entities pulled out of paths by regex (pybids, NeuroConv), `{token}` templates that build a path from metadata (PEP, Snakemake), attributes read from directory names (Hive-style partitioning), portable dataset descriptions (Frictionless, RO-Crate), entity tables for neuroscience (DataJoint).

What we have not found in one artefact is the combination: a description that is **descriptive** (it never asks you to reorganise), **bidirectional** (the same rules parse a location and generate one), **cross-store** (identity declares when two differently-named folders are the same entity), and **portable** (readers in different languages provably agree, via a defined output object and conformance fixtures).

[Related Work](guides/related-work.md) sets out where each neighbouring tool stops, and when you should use one of them instead. [Design Decisions](guides/design-decisions.md) explains the choices inside the schema.
