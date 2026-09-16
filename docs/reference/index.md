# Schema Reference

Complete reference for every property in the Dataset Structure Model schema, version **1.0.0** (the frozen core).

The schema file is [`schema/DatasetStructureModel.schema.json`](https://github.com/framover/dataset-structure-model/blob/main/schema/DatasetStructureModel.schema.json). Readers emit [entity records](entity-record.md) defined by [`schema/EntityRecord.schema.json`](https://github.com/framover/dataset-structure-model/blob/main/schema/EntityRecord.schema.json), and take directory snapshots defined by [`schema/DirectoryListing.schema.json`](https://github.com/framover/dataset-structure-model/blob/main/schema/DirectoryListing.schema.json) — see [Conformance Fixtures](../guides/conformance.md).

## Top-level structure

| Property | Required | Type | Description |
|----------|----------|------|-------------|
| `schemaVersion` | Yes | string (semver) | Schema version, `"1.0.0"` |
| `dataLocations` | Yes | array | One or more data location definitions |
| `entityTypes` | No | array | Semantic entity type declarations, each with an identity key |
| `entityRelationships` | No | array | Relationships between entity types |
| `metadataDefinitions` | No | object | Global metadata field dictionary |
| `preferences` | No | object | Active environment and default location (instance-level; may live in a local overlay) |

## Reference pages

- [Top-Level Structure](overview.md)
- [dataLocations](data-locations.md)
- [entityLayout](entity-layout.md)
- [metadataDefinitions](metadata-definitions.md)
- [Metadata Extraction](metadata-extraction.md)
- [entityRelationships](entity-relationships.md)
- [preferences](preferences.md)
- [Entity Record](entity-record.md)

## What "frozen core" means

Version 1.0.0 fixes the parts of the schema that readers implement and that configs can rely on: the `filesystem` source type, the extraction methods `substring`, `regex`, `template`, `fixed` and `function`, entity identity, file-level entities, and the entity record. Blocks marked **DRAFT** in the schema (`spreadsheet`, `database` and `api` sources; the `sidecar` extraction method) are placeholders: they validate, but readers may reject them, and they can change without a major version bump.
