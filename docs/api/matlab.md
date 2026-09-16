# MATLAB API

The MATLAB reader: the same rules as the [Python reference reader](python.md), implemented in a `+dsm` package. It passes every [conformance case](../guides/conformance.md), and its output is checked against the Python comparator (`dsm compare`) so the two readers are known to agree on the [entity record](../reference/entity-record.md) format.

Source: [`src/matlab/+dsm`](https://github.com/framover/dataset-structure-model/tree/main/src/matlab). Requires MATLAB R2021a or later (tested on R2024b and R2025b); no toolboxes.

## Install

```matlab
addpath("path/to/dataset-structure-model/src/matlab")
```

The package reads the schemas from the repository's `schema/` folder, so keep it inside a checkout (or a copy that keeps `schema/` two levels above `src/matlab`).

## Quick start

```matlab
config  = dsm.loadConfig("my-dataset.json");      % throws dsm.ConfigError when the config must be refused

% a listing: from a file, a real directory, or find-style lines
listing = dsm.loadListing("listing.json");
root    = dsm.listing.fromDirectory("raw", "lab-nas", "/Volumes/lab-nas/export");
listing = dsm.Listing({root}, "mac-lab");

result = dsm.walk(config, listing);               % dsm.WalkResult
disp(dsm.renderReport(config, result))            % the dry-run report
result.write("records.json")                      % {records, unmatched} in the schema's JSON shape

for record = result.Records                       % cell array of structs in the EntityRecord shape
    fprintf("%s %s\n", record{1}.entityType, jsonencode(record{1}.identity));
end
```

Records are plain structs: `entityType`, `identity` (struct), `parents` (cell of structs), `locations` (cell of structs whose `files` is a `containers.Map` from pattern name to file paths), `metadata` (struct), `issues` (cell of `{code, message}` structs). `jsonencode` on `result.toStruct()` produces the interchange JSON.

## `function` extractors

```matlab
registry = dsm.ExtractorRegistry();
registry.register("session_number_from_folder_name", @(fullPath, levelName, locationId) ...);
result = dsm.walk(config, listing, registry);
```

An implementation returns a value of the field's `dataType`, or `[]` when it cannot extract. An unregistered key yields `unresolved-extractor` on every affected record.

## API

| Function / class | Purpose |
|------------------|---------|
| `dsm.loadConfig(path, RejectDraft=true)` | Read, validate, apply a sibling `<name>.local.json` overlay's preferences; returns `dsm.Config` |
| `dsm.validateConfig(doc)`, `dsm.schemaErrors(doc)`, `dsm.referenceProblems(doc)` | Validation pieces; `validateConfig` throws `dsm.ConfigError` with `Code` `schema-validation`, `reference-integrity` or `unsupported-draft` (identifier `dsm:config:<codeInCamelCase>`) |
| `dsm.Config` | Accessors over the validated document (`layout`, `mapping`, `rulesFor`, `identityKeys`, `matchRegex`, …) |
| `dsm.Listing`, `dsm.loadListing`, `dsm.listing.fromDirectory`, `dsm.listing.fromLines` | Listings; `Listing.makeRoot` normalises entries (ancestors added, sorted) |
| `dsm.walk(config, listing, registry)` | The reader rules; returns `dsm.WalkResult` |
| `dsm.compareResults(expected, actual)` | The conformance comparison rules |
| `dsm.renderReport(config, result)` | Dry-run report text |
| `dsm.conformance.runCases()`, `runCase`, `exportActual(dir)` | Run the fixtures; export this reader's records for `dsm compare` |
| `runMatlabTests()` (in `src/matlab`) | The test suite |

## Verifying the reader

```matlab
addpath("src/matlab")
runMatlabTests()                                  % unit tests + every conformance case
dsm.conformance.exportActual("/tmp/matlab-actual") % then, in a shell:
```

```bash
for c in conformance/*/; do c=$(basename $c); [ -f /tmp/matlab-actual/$c.actual.json ] && dsm compare conformance/$c/expected.json /tmp/matlab-actual/$c.actual.json; done
```

The second step is the cross-language check: the Python comparator, not MATLAB's own, judges the MATLAB output. CI runs the MATLAB suite on every change.

## How validation works here

MATLAB has no JSON Schema validator, so `dsm.schemaErrors` interprets the schema files themselves — a small draft-07 interpreter covering the keywords the DSM schemas use (`$ref`, `type`, `required`, `properties`, `additionalProperties`, `enum`, `const`, `pattern`, `items`, `oneOf`/`anyOf`/`allOf`/`not`, `if`/`then`/`else`, …). It refuses unknown keywords rather than ignoring them, so it cannot silently fall behind the schema. Two consequences of `jsondecode` being lossy: a one-element array of objects is indistinguishable from an object, and `[]` from `null`, so a malformed config that puts an object where an array is required can pass here; the Python reader is the reference validator.

## Limitations

- Metadata keys must be valid MATLAB identifiers: `jsondecode` renames a key that starts with `_`, and records use struct fields for `identity` and `metadata`.
- `files` in a location entry is a `containers.Map` because pattern names may contain `-`.
- Records are structs, not classes. A typed layer belongs to the consumer (NANSEN's facade), not to the reader.
- Error messages differ from the Python reader's; error *codes* are identical.
