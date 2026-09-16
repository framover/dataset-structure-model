# Dataset Structure Model

[![CI](https://github.com/framover/dataset-structure-model/actions/workflows/ci.yml/badge.svg)](https://github.com/framover/dataset-structure-model/actions/workflows/ci.yml)

**A declarative, language-neutral mapping between the physical layout of a dataset across one or more stores and a semantic entity model.** A reader applies the mapping to derive entity tables — which entities exist, how each is identified across stores, which items belong to it, and what attributes its location encodes — and, in reverse, to place a new entity's data. The mapping describes layouts as they are; it does not prescribe them.

Think of it as an ORM whose "relational" side is a file store and whose "object" side is entity tables: the mapping is declared once and serves both reading and writing, with identity keys and relationships — except that the tables are derived views, recomputed from the store. The store stays the truth.

## The idea

A scientific dataset is a set of entities — subjects, sessions, recordings, trials — whose data sits in stores that were organised by whatever produced them: an acquisition program's `{date}/{timestamp}_{session}` folders, an analysis tool's `subject-{id}/session-{id}` folders, an export that dumped every file into one directory. Every tool that wants an entity table from such a store hard-codes assumptions about the layout.

DSM replaces those assumptions with a mapping:

```
stores, as they are                          mapping, declared once              entity tables, derived
raw/2025_05_23/2025_05_23_10_00_00_m110-…-001/   session_id ← regex on folder      subject   m110
raw/2025_05_23/…                                 session_date ← the date folder     session   m110-20250523-001
processed/subject-m110/session-m110-…-001/       session_id ← "session-{id}"          raw:       2025_05_23/…/   date 2025-05-23
processed/subject-m110/…                         identity: session_id                 processed: subject-m110/…/
```

What the mapping expresses:

- **Entity types and their identity** — the field that identifies an instance across every store, so that a raw folder and a processed folder with different naming conventions become one row.
- **Per-store layout** — which level of a folder tree represents which entity type, which levels are merely structural (a date folder), and when entities are groups of files in a shared folder rather than folders.
- **Extraction rules** — how attributes are read from names and hierarchy: slices, regular expressions, templates, constants, or a registered function. Attributes encoded in the *addressing* of items, not in file contents; that boundary is what separates DSM from data-format standards.
- **Membership** — which files belong to an entity, including required ones and expected cardinality, so a reader can report an incomplete entity.
- **Generation** — templates that produce a location for a new entity in a writable store, using the same vocabulary that parses it.
- **Environments** — one mapping, different root paths per machine.

What comes out is defined too: an [entity record](docs/reference/entity-record.md) per entity, with identity, parents, locations and files per store, attributes, and any problems found. Two readers given the same mapping and the same directory snapshot produce the same records — the [conformance fixtures](docs/guides/conformance.md) make that checkable, and both readers in this repository pass them.

## What it is not

- Not a data standard: it never requires a layout (contrast BIDS).
- Not a metadata schema: it does not say what a subject *is* scientifically (contrast openMINDS, NWB).
- Not a pipeline definition: it records provenance between stores, not processing steps.
- Not a database: the entity tables are views, unless a consumer chooses to persist them.

Every mechanism here exists somewhere already — regex extraction of entities from paths (pybids, NeuroConv), path templates driven by metadata (PEP, Snakemake), attributes encoded in directory names (Hive-style partitioning). [Related Work](docs/guides/related-work.md) sets out where each stops, and when to use one of them instead of this.

## Repository contents

| Path | Contents |
|------|----------|
| `schema/DatasetStructureModel.schema.json` | The mapping language |
| `schema/EntityRecord.schema.json` | The derived view: what readers emit |
| `schema/DirectoryListing.schema.json` | A store snapshot, so the mapping can be applied without a live filesystem |
| `conformance/` | The mapping's semantics made executable: config + listing + expected records per case |
| `src/python/dsm/` | The Python reference reader and `dsm` command (validate, listing, walk, compare, conformance) |
| `src/matlab/+dsm/` | The MATLAB reader, passing the same cases |
| `examples/` | Example mappings |
| `docs/` | The documentation site |
| `tests/` | Schema, fixture self-consistency, reader and docs-snippet tests |

## Quick start

Python (3.9+):

```bash
pip install -e .
dsm validate examples/flat_session_files.json
dsm listing raw lab-nas /path/to/data -o listing.json        # snapshot a real directory
dsm walk examples/flat_session_files.json listing.json       # the dry run: entities found, files unaccounted for
```

MATLAB (R2021a+):

```matlab
addpath("src/matlab")
config = dsm.loadConfig("conformance/flat-session-files/config.json");
result = dsm.walk(config, dsm.loadListing("conformance/flat-session-files/listing.json"));
disp(dsm.renderReport(config, result))
```

Then: the [Quick Start](docs/getting-started/quickstart.md), [Core Concepts](docs/getting-started/concepts.md), the [Usage Guide](docs/guides/usage-guide.md), the [examples](examples/), and the [Schema Reference](docs/reference/index.md) — [Metadata Extraction](docs/reference/metadata-extraction.md) and [Entity Record](docs/reference/entity-record.md) are the parts readers implement.

## Status

Version **0.1.0**. The core is what both readers implement and the conformance fixtures pin: the `filesystem` store, the extraction methods `substring`, `regex`, `template`, `fixed` and `function`, declared identity, file-level entities, and the entity record. A field enters the core only when a reader consumes it. Blocks marked DRAFT in the schema (`spreadsheet`, `database` and `api` stores, `sidecar` extraction) are reserved and may change at any time. See [CHANGELOG.md](CHANGELOG.md).

The schema is not yet stable. It has been exercised on the authors' own layouts and one toy dataset. Until 1.0, a change to the core bumps the minor version, and a config written for one minor version is not guaranteed to validate against the next.

**1.0 waits for evidence.** It follows once the mapping has been applied to datasets from outside the authors' lab and the core has stopped changing across them. Each such dataset adds an example config and, where it exposed a gap, a conformance case.

Both readers pass every conformance case; CI runs the Python suite, the Python conformance run, and the MATLAB suite on each change. Neither reader is published on a package index yet.

## Contributing

Issues and pull requests are welcome. A change to the mapping language goes with a conformance case, a changelog entry and the reference page; see the [Development Guide](docs/contributing/development.md).

## License

MIT — see [LICENSE](LICENSE).
