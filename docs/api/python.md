# Python API

The reference reader. It validates configs, turns directory listings into [entity records](../reference/entity-record.md), and is the executable definition of the reader rules — it passes every [conformance case](../guides/conformance.md), and CI runs them on each change.

Source: [`src/python/dsm`](https://github.com/framover/dataset-structure-model/tree/main/src/python/dsm). Requires Python 3.9+; the only dependency is `jsonschema`.

## Install

```bash
pip install -e .            # from a clone; adds the `dsm` command
```

## Command line

| Command | Does |
|---------|------|
| `dsm validate CONFIG` | Schema validation, cross-reference rules, and rejection of DRAFT blocks (`--allow-draft` to accept them). Exit 1 with the problems listed. |
| `dsm listing LOC ROOT DIR [...] -o listing.json` | Snapshot real directories into a [listing](../guides/conformance.md#the-listing). `--text` reads `find`-style files instead (one path per line; directories are inferred). |
| `dsm walk CONFIG LISTING` | The dry run: a report of entities found per type, issues, unresolved extractors and unmatched entries. `--json` prints the records instead. `--extractors mod.py` registers `function` implementations. `--fail-on-issues` exits 3 when any record carries an issue. |
| `dsm compare EXPECTED ACTUAL` | Compare two results by the conformance rules. Any reader — the MATLAB one included — can emit records as JSON and be checked with this. |
| `dsm conformance [DIR]` | Run the cases against this reader. |

A typical loop when writing a config for an existing dataset:

```bash
dsm listing raw lab-nas /Volumes/lab-nas/export -o listing.json
dsm validate my-dataset.json
dsm walk my-dataset.json listing.json
```

The report says how many sessions were found, which files no rule accounts for, and which entities are incomplete — which is what a person, or an LLM writing the config, needs to fix the next iteration.

## API

```python
from dsm import load_config, load_listing, walk, render_report, ExtractorRegistry

config = load_config("my-dataset.json")        # raises ConfigError(code=...) when the config must be refused
listing = load_listing("listing.json")          # raises ListingError
registry = ExtractorRegistry({"session_number_from_folder_name": my_function})

result = walk(config, listing, registry)        # WalkResult
for record in result.records:                   # Record: entity_type, identity, parents, locations, metadata, issues
    print(record.entity_type, record.identity, [loc.paths for loc in record.locations])
print(render_report(config, result))
result.to_dict()                                # {"records": [...], "unmatched": [...]} in the schema's shape
```

| Piece | Module | Notes |
|-------|--------|-------|
| `load_config`, `validate_config`, `check_references`, `schema_errors` | `dsm.validate` | `load_config` also applies a sibling `<name>.local.json` overlay's `preferences` |
| `Config` | `dsm.config` | Accessors over the validated document; there are no typed models — the document is the model |
| `load_listing`, `root_from_directory`, `root_from_lines`, `Listing`, `Root` | `dsm.listing` | |
| `ExtractorRegistry`, `evaluate_fields` | `dsm.extract` | The extraction contract: slices, regex, templates, LDML formats, normalize, typing |
| `walk`, `Walker` | `dsm.walk` | The reader rules |
| `compare_results` | `dsm.compare` | The comparison rules |
| `run_cases`, `run_case` | `dsm.conformance` | Fixture runner; ships the fixture extractors |

### `function` extractors

An implementation is a callable `(full_path, level_name, data_location_identifier) -> value | None`, registered under its registry key. On the command line, `--extractors my_extractors.py` loads a module exposing `EXTRACTORS = {key: callable}`. An unregistered key yields `unresolved-extractor` on every affected record; the field is absent.

### Errors a reader raises

| `ConfigError.code` | Meaning |
|--------------------|---------|
| `schema-validation` | The config fails the JSON Schema |
| `reference-integrity` | It validates but a cross-reference does not resolve, a template cycles, or the layout's entity types are not in declaration order |
| `unsupported-draft` | It uses a DRAFT source type or `sidecar` extraction; pass `reject_draft=False` / `--allow-draft` to proceed |

## Design notes

- **No generated models.** The earlier `wip-python-api` branch generated pydantic classes from the pre-freeze draft. This reader works on the validated document directly; a typed layer will be added when something consumes it, not before.
- **The reader is not the harness.** `tests/test_conformance.py` re-derives every fixture expectation with its own small evaluator and never imports the reader, so the fixtures and the reader are two implementations that must agree.
