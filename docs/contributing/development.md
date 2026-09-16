# Development Guide

This guide covers the tools and workflow for contributing to the Dataset Structure Model.

---

## Setup

**Requirements:** Python 3.9+, `pip`

```bash
# Clone the repository
git clone https://github.com/framover/dataset-structure-model.git
cd dataset-structure-model

# Install the Python reader (editable) with the test dependencies; adds the `dsm` command
pip install -e ".[test]"

# Install documentation dependencies
pip install -r requirements-docs.txt
```

`pytest tests/` also works without installing: the suite puts `src/python` on the path.

**MATLAB reader** (R2021a+, no toolboxes):

```bash
matlab -nouserpath -batch "addpath('src/matlab'); runMatlabTests()"
```

`-nouserpath` keeps a personal `startup.m` out of the run. The cross-language check — MATLAB records judged by the Python comparator — is described in the [MATLAB API](../api/matlab.md#verifying-the-reader).

---

## Validating examples

To check that an example file is valid against the schema:

```bash
python -m jsonschema -i examples/flat_session_files.json schema/DatasetStructureModel.schema.json
```

A zero exit code means the file is valid.

The test suite does more than schema validation:

```bash
pytest tests/ -v
```

| Test file | Checks |
|-----------|--------|
| `test_schema_validity.py` | The schema is valid draft-07 |
| `test_schema_completeness.py` | Every `$ref` resolves; no unused definitions |
| `test_examples.py` | Every example validates; documents that break the frozen-core rules are rejected |
| `test_reference_integrity.py` | Cross-references in every example resolve (identity fields, `ofEntity`, level names, `derivedFrom`, template tokens) |
| `test_entity_record.py` | `EntityRecord.schema.json` and `DirectoryListing.schema.json` are valid; every expected record validates |
| `test_conformance.py` | Every conformance case is self-consistent: config valid, paths exist, listing fully accounted for, extractions and file patterns re-evaluate to the expectation (independent of the reader) |
| `test_python_reader.py` | The Python reader passes every conformance case; extraction, listing, validation, comparison and CLI contracts |
| `test_walker_rules.py` | Reader rules with no fixture case, on in-memory listings |
| `src/matlab/tests/*.m` | The MATLAB reader: every conformance case, the extraction/listing/validation/comparison contracts, the walker rules |
| `test_docs_snippets.py` | Every complete JSON config embedded in `docs/` validates and is coherent |

---

## Building the documentation

**Serve locally with live reload:**

```bash
mkdocs serve
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser. Changes to `.md` files are reflected immediately.

**Build and check for warnings:**

```bash
mkdocs build --strict
```

`--strict` treats warnings as errors. The build must pass with zero warnings before a documentation change is merged.

The built site is written to `site/` (git-ignored).

---

## Schema update checklist

Follow these steps whenever making changes to `schema/DatasetStructureModel.schema.json`:

1. **A field enters the frozen core only when a reader consumes it.** Otherwise mark it DRAFT in its description.
2. **Update the schema** — `schema/DatasetStructureModel.schema.json`, and `schema/EntityRecord.schema.json` if the output changes.
3. **Bump `schemaVersion`** in all example files if the change is breaking.
4. **Add a CHANGELOG entry** under `## [Unreleased]` in `CHANGELOG.md`.
5. **Run `pytest tests/ -v`** — it must pass, including the docs-snippet test.
6. **Update the reference pages** in `docs/reference/` for every changed property; `docs/reference/metadata-extraction.md` is the extraction contract.
7. **Update `docs/guides/ai-agent-instructions.md`** — its complete example is validated by the tests, its rules are not; keep them in step.
8. **Add or update examples** in `examples/` with a walkthrough in `docs/examples/`, and a conformance case in `conformance/` for every rule readers must follow (see [Conformance Fixtures](../guides/conformance.md)).
9. **Add a design-decisions entry** when the change encodes a rule readers must follow.

---

## Schema versioning policy

This project uses [Semantic Versioning](https://semver.org/):

- **Patch** (`1.0.x`) — documentation fixes, description improvements, no schema changes.
- **Minor** (`1.x.0`) — additive schema changes: new optional fields, new enum values. Existing valid configs remain valid.
- **Major** (`x.0.0`) — breaking changes: removed or renamed fields, new required fields, changed `additionalProperties` rules.

The `schemaVersion` field in config files is the schema version they were written for (`"1.0.0"` for the current core). DRAFT blocks are exempt from this policy: they may change in a minor release.

---

## Repository structure

```
dataset-structure-model/
├── schema/
│   ├── DatasetStructureModel.schema.json   ← the config schema (source of truth)
│   ├── EntityRecord.schema.json            ← what readers emit
│   └── DirectoryListing.schema.json        ← what readers walk (conformance input)
├── examples/
│   ├── flat_session_files.json
│   ├── raw_processed_two_photon.json
│   └── sharebrain_toy_dataset.json
├── conformance/                             ← one case per dir: config, listing, expected records
├── docs/                                    ← MkDocs documentation source
│   ├── index.md
│   ├── getting-started/
│   ├── reference/
│   ├── guides/
│   ├── examples/
│   ├── api/
│   └── contributing/
├── tests/                                   ← pytest test suite
├── src/
│   ├── python/dsm/                          ← the Python reference reader (`dsm` command)
│   └── matlab/+dsm/                         ← the MATLAB reader (tests in src/matlab/tests, runner runMatlabTests.m)
├── pyproject.toml
├── mkdocs.yml
├── requirements-docs.txt
├── requirements-test.txt
├── CHANGELOG.md
└── LICENSE
```
