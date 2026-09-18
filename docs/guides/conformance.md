# Conformance Fixtures

The schema says how a config is shaped. The fixtures in [`conformance/`](https://github.com/framover/dataset-structure-model/tree/main/conformance) say what a reader must *do* with one: given a config and a directory listing, produce exactly these [entity records](../reference/entity-record.md). They are language-neutral, so a MATLAB reader and a Python reader are checked against the same expectations, and a tool that writes configs (an LLM skill, a configuration UI) can check its output against a listing without a real filesystem.

---

## A case

One directory per case:

| File | Contents |
|------|----------|
| `config.json` | A DSM config |
| `listing.json` | A directory snapshot under one or more root paths — [`schema/DirectoryListing.schema.json`](https://github.com/framover/dataset-structure-model/blob/main/schema/DirectoryListing.schema.json) |
| `expected.json` | The records and unmatched entries a reader must produce, or the error it must raise |
| `README.md` | What the case checks |

## The listing

```json
{
  "environmentIdentifier": "mac-analysis",
  "roots": [
    {
      "dataLocationIdentifier": "raw",
      "rootStoragePathIdentifier": "analysis-mac",
      "entries": [
        "2025_05_23/",
        "2025_05_23/2025_05_23_10_00_00_m110-20250523-001/",
        "2025_05_23/2025_05_23_10_00_00_m110-20250523-001/rec.raw"
      ]
    }
  ]
}
```

- Entries are relative to the root, `/`-separated. A directory ends with `/`; a file does not.
- Every ancestor directory of an entry is itself listed; entries are unique and sorted.
- `environmentIdentifier` is the active environment; it overrides the config's `preferences`.

A listing is what `find` produces after a two-line transformation, so a dry-run tool can work from a text listing and a reader test can be written without touching a disk.

## The expectation

```json
{
  "records": [ ... entity records ... ],
  "unmatched": [
    { "dataLocationIdentifier": "raw", "rootStoragePathIdentifier": "main", "path": "temp/", "reason": "excluded" }
  ],
  "requiresExtractors": { "registry_key": "contract in prose" }
}
```

or, for a config the reader must refuse:

```json
{ "error": { "code": "reference-integrity", "message": "..." } }
```

`unmatched` lists the **topmost** entries no entity accounts for, with `reason` `excluded` (an `excludePatterns` hit) or `no-match` (anything else: wrong pattern, a file where folders are expected, a folder deeper than the layout). Descendants of an unmatched entry are implied.

`requiresExtractors` names the `function` registry keys the case needs. A harness registers an implementation of the described contract before running the case, or skips it.

Error codes: `schema-validation` (the config fails the JSON Schema) and `reference-integrity` (it validates but a cross-reference does not resolve — see the rules in [AI Agent Instructions](ai-agent-instructions.md#cross-reference-rules-checked-by-readers)).

## Comparison rules

A reader passes a case when:

1. **Records match by key.** The key of a record is `(entityType, identity, parents)`. Order of records is irrelevant; there must be no extra and no missing records.
2. **Locations match by `(dataLocationIdentifier, rootStoragePathIdentifier)`**, in any order. `paths` and each `files` array are compared as sorted sets.
3. **`metadata` is compared exactly.** Dates, times and datetimes are ISO 8601 strings; integers are JSON numbers.
4. **`issues` are compared by `code`** as a set; messages are free text, and how many times a reader repeats a code is not compared.
5. **`unmatched` is compared as a set** of `(location, root, path, reason)`.
6. **Error cases** compare only the error `code`.

## Reader rules the fixtures encode

These are the rules a reader implements; each is exercised by at least one case.

- **Folder entities.** A record's folder path ends with `/`. `files` and `isComplete` are present exactly when the level declares `filePatterns`; candidates for `files` are the direct children of the folder. Everything inside an innermost entity folder — including subfolders and `additionalFolders` — is covered by the entity, whether or not a pattern matches it.
- **File entities.** At a `file` level, an entity's `paths` are every file at that level whose extracted identity is the entity's, whether or not a pattern matches it; `files` are the named-pattern matches among them. `{token}` references in patterns are replaced by the regex-escaped identity value before matching.
- **Structural levels** are walked and readable by extraction rules but never appear in `parents`.
- **Ancestors inferred from descendants** — a subject whose id is read from session names in a location without subject folders — get a record with `locations: []`. An ancestor that has a folder somewhere lists only those locations. Every field of the ancestor's type that the inferring paths yield attaches to it, not only its identity: a subject's sex read from its session names lands on the subject record.
- **`metadata`** is the union of the entity's own fields across every path it was read from — its own paths where it has a level, and the descendant paths it was inferred from where it has none — plus the identity fields of its entity-typed ancestors (not their other fields). A field with a rule that matched nothing on any of those paths takes the definition's `defaultValue`; without one it is absent and the record carries `extraction-failed`. A field with no rule in any visited location is absent without an issue.
- **`duplicate-entity`**: several folders in one location yield the same identity → one record, all folder paths listed, files pooled.
- **`cardinality-violation`**: a `cardinality: one` pattern matched several files; all are reported. **`missing-required-file`**: an `isRequired` pattern matched none; `isComplete` is `false`.
- **`metadata-conflict`**: the paths an entity was read from disagree on a field's value — two locations, or two descendants that infer the same ancestor. The reader keeps the first value in walk order (locations in listing order, entries sorted) and reports the conflict.
- **`unresolved-extractor`**: a `function` key the reader has not registered; the field is absent.
- **Derived `matchPattern`**: when a level has only `pathComponentTemplate`, `{token}` becomes the referenced definition's `validation.pattern` (without its own `^`/`$`) or `[^/\\]+`; literal text is escaped; the result is anchored.
- **Level references** in extraction rules may be a name, a 0-based index, or `null` for the whole relative path (no trailing slash).

## Cases

| Case | Checks |
|------|--------|
| `folder-hierarchy-basic` | two folder levels, `substring`/`regex`, `excludePatterns`, required and single-cardinality patterns, duplicate folders, identity scoped by parent |
| `flat-session-files` | file-level grouping (mirrors `examples/flat_session_files.json`), token patterns, ancestors with no folder |
| `inferred-ancestor-fields` | non-identity fields of an inferred ancestor read from its descendants' names, `metadata-conflict` between descendants, `extraction-failed` on an inferred ancestor |
| `raw-processed-matching` | structural date level, cross-location matching, one-sided entities, derived `matchPattern`, `additionalFolders` (mirrors `examples/raw_processed_two_photon.json`) |
| `extraction-methods` | every declarative method and modifier: slices, groups, whole match, template, fixed, normalize, LDML formats including a two-digit year and its 1969–2068 pivot, integer typing, `defaultValue`, `extraction-failed`, fixed structural level |
| `function-extractor` | the registry-key contract, null return, `requiresExtractors` |
| `invalid-reference` | must be refused with `reference-integrity` |
| `invalid-schema` | must be refused with `schema-validation` |

The cases below describe layouts from outside the authors' lab; each README names the layout's provenance and the gaps it exposes. The gap ids refer to [Validation Against Foreign Datasets](../validation/foreign-datasets.md). Where a layout exposes a gap, the case pins the *current* rules, so a change to the core shows up as a change to an expectation.

| Case | Layout | Checks |
|------|--------|--------|
| `dandi-nwb-subject-folders` | DANDI dandiset (000006) | subject folder above a one-file session level, parent and own tokens in one pattern, dataset-level file (G1) |
| `dandi-nwb-session-variants` | DANDI dandiset (000409) | several NWB files per session distinguished by `desc-`, UUID identities, `+` in names, partial download unmatched |
| `gin-blackrock-flat-files` | GIN repository, Blackrock files | fixed level above a file level, subject from one character with `enum`, two-digit year, seven file kinds, sibling branch (G5) |
| `crcns-hc3-numbered-extensions` | CRCNS hc-3 | four entity types on three levels, file entities keyed by numeric extension, two ancestors' tokens in one pattern, outer-entity files double-accounted (G2) |
| `ibl-alf-session-path` | IBL ONE/ALF | fixed level between entities, composite identity from a structural date level, whole-path rule, one entity in two branches (G3), branching (G5) |
| `bids-multimodal-sessions` | BIDS (OpenNeuro ds000117) | structural datatype level with alternation, stem-keyed file entities, optional entities (G4), `scans.tsv` (G2), session-level files under `meg/` (G6) |
| `allen-ecephys-cache` | AllenSDK ecephys cache | integer identities, a session folder owning a file next to probe files (G2), root tables (G1) |
| `open-ephys-binary` | Open Ephys binary format | four entity levels, fixed `continuous` level, names with spaces, recording-level files (G2), `events/` and `spikes/` branches (G5) |
| `spikeglx-folder-per-probe` | SpikeGLX, folder per probe | composite gate identity, tokens from parent and own identity, per-trigger series, nidq files at the gate level (G2) |
| `suite2p-output-planes` | suite2p output | fixed level between entities, `combined/` excluded, seven fixed-name kinds, files inside a structural folder (G7) |
| `deeplabcut-project` | DeepLabCut project | one tree as two locations (the G5 workaround), file group in one and folder in the other, one regex for two naming forms (G8) |
| `scanimage-caiman-two-photon` | ScanImage TIFF series, CaImAn outputs | file-level ↔ folder-level matching on a three-field identity, two environments, subject under dates flagged `duplicate-entity` (G3), zero-padded counter as text (G9), metadata in member names (G10) |
| `zenodo-adhoc-date-folders` | ad-hoc Zenodo deposit | single entity type, date level on top, `enum` and integer from one name, exactly-three planes not expressible (G11) |
| `zenodo-adhoc-flat-mat` | ad-hoc Zenodo deposit | one file level at the root, an entity split over numbered files |
| `nansen-project-layout` | NANSEN data locations | two roots in one location, raw timestamp folders matched to generated `subject-`/`session-` folders, MATLAB index ranges as slices, variables in subfolders not describable (G12) |
| `ebrains-fiorilli-2022` | EBRAINS dataset, complete bucket listing | two fixed levels above a file level, several files per session in one flat folder, session key and subject from one name, two-digit year, a required kind beside two optional kinds, dataset-level files and a session table (G1), placeholder root path (G17) |

## Using the fixtures from a reader

```
for each case in conformance/:
    if expected has "error":
        assert reader.load(config) raises expected.error.code
        continue
    if expected has "requiresExtractors" and any key is not registered:
        skip
    result = reader.walk(config, listing)          # records + unmatched
    compare(result, expected)                       # rules above
```

The Python reader implements exactly this: `dsm conformance` runs every case and CI fails when one does not pass. The MATLAB reader does the same with `dsm.conformance.runCases()`, and `dsm.conformance.exportActual(dir)` writes its records so the Python comparator can judge them (`dsm compare expected.json <case>.actual.json`) — a reader in another language needs no comparison code of its own. See the [Python API](../api/python.md) and [MATLAB API](../api/matlab.md).

The repository's own suite (`tests/test_conformance.py`) checks that every case is self-consistent — the config validates, every expected path exists in the listing, every listing entry is accounted for, and every declarative extraction and file pattern re-evaluates to the expectation. It is not a reader; it is what makes the expectations trustworthy before one exists.

## Adding a case

1. Create `conformance/<kebab-name>/` with the four files. Keep listings small — a handful of entities is enough to pin a rule.
2. State in the README which rule the case exists for.
3. Run `pytest tests/test_conformance.py`. A case that fails self-consistency is wrong; fix the expectation, not the harness.
4. Add a row to the table above.
