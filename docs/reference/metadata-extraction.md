# Metadata Extraction

`metadataMapping` on a `filesystemSource` is an array of `{ metadataRef, extraction }` items. Each says how one globally defined field is read from this location's paths. The extraction object is defined once (`metadataExtraction`) and this page is its contract — the part of the schema that must behave identically in every reader.

```json
"metadataMapping": [
  { "metadataRef": "session_id",
    "extraction": { "method": "regex", "pattern": "_(m\\d{3}-\\d{8}-\\d{3})$", "entityLayoutLevel": "sessions" } }
]
```

## How a rule is evaluated

A rule is evaluated **per entity instance**, over that instance's path relative to the root. `entityLayoutLevel` selects the path component the rule reads:

| `entityLayoutLevel` | Reads |
|---|---|
| a level name (preferred) | the component at that level |
| a 0-based integer | the component at that index |
| `null` or omitted | the whole relative path, `/`-separated |

The selected level may be above the entity's own level — a session reads its date from a structural date folder — or, for an ancestor entity type with no level of its own, below it (see next section). At a `file` level the component is the file name including its extension.

## Which entity a value belongs to

A field belongs to the entity type in its definition's `ofEntity`, and the value attaches to that entity:

- If the location has a level for that entity type, the rule runs once per instance at that level.
- If it does not (a processed location holding sessions directly, with no subject folders), the rule runs on the descendants that do have a level, and the value attaches to the **parent** entity. This is how `subject_id` extracted from a session folder name creates and identifies the subject that session belongs to. It holds for every field of the parent's type, not only its identity: a subject's sex or a cell's recording date written into the descendant names lands on the parent's record. Values are pooled across all the descendants; when they disagree the reader keeps the first in walk order and reports `metadata-conflict`.

Identity of an instance = its own `identifierRef(s)` value(s) + the identities of its entity-typed ancestors, wherever those were extracted. Structural levels contribute nothing.

## Methods

### `substring`

`pattern` is a **Python-style slice** of the component: `start:stop`, 0-based, half-open, either bound may be omitted, negative indices count from the end, no step. The schema enforces `^-?\d*:-?\d*$`.

| Pattern | On `m110-20250510-001_raw.tif` | Meaning |
|---|---|---|
| `0:4` | `m110` | first four characters |
| `5:13` | `20250510` | characters 6–13 |
| `:-4` | `m110-20250510-001_raw` | drop the extension |
| `:` | whole component | |

MATLAB readers convert (`start+1`, omitted stop → `end`, negative → `end+n+1`). The `end` keyword is not part of the syntax. Use `substring` for fixed positions; anything structural ("after the first underscore") is a regex.

### `regex`

`pattern` is a regular expression in the portable subset below. The value is the **first capture group**, or the whole match when there is none. No match yields no value (the definition's `defaultValue` applies).

### `template`

`pattern` is a string with `{token}` references to other fields of the same entity or its ancestors, e.g. `"{session_date}_{subject_id}"`. Readers evaluate templates after the fields they reference and reject cycles. This replaces "combine folder names from several levels" rules: extract each part with its own rule, then compose.

### `fixed`

`value` is the constant to assign (string, number or boolean).

### `function`

`extractorFunction` is a **registry key** (`^[A-Za-z_][A-Za-z0-9_]*$`), not a language symbol. Each reader resolves it through its own extractor registry and calls the implementation with

```
(fullPath, levelName, dataLocationIdentifier) -> value of the field's dataType, or null
```

A config that uses `function` needs an implementation in every reader that consumes it; a reader's dry-run report lists unresolved keys. Prefer the declarative methods — a config with only those runs anywhere without code.

### `sidecar` — DRAFT

Read the value from a file inside the entity folder (`filePattern`, `contentPath`, `fileFormat`). Outside the core; readers may reject it.

## `valueFormat`

For `date`, `time` and `datetime` fields: the pattern the extracted text is parsed with, in **Unicode LDML** notation as used by MATLAB `datetime` and Java — `yyyyMMdd`, `yyyy_MM_dd`, `HH_mm_ss`, `yyyy-MM-dd'T'HHmmss`, `yyMMdd`. Python readers translate to `strftime` directives.

Readers support this token subset and nothing else; a format outside it is not portable:

| Token | Meaning | `strftime` |
|-------|---------|------------|
| `yyyy` | four-digit year | `%Y` |
| `yy` | two-digit year | `%y` |
| `MM` | month, two digits | `%m` |
| `dd` | day, two digits | `%d` |
| `HH` | hour 00–23 | `%H` |
| `mm` | minute | `%M` |
| `ss` | second | `%S` |
| `'…'` | literal text | as is |

**Two-digit years** fall in 1969–2068: `69` is 1969, `68` is 2068. This is the window Python's `strptime` uses; a MATLAB reader must pass `PivotYear` 1969 to `datetime`, because its default pivot moves with the current year and the two readers would otherwise disagree on the same config.

## `normalize`

Applied after extraction: `lowercase`, `uppercase`, `trim`, `strip_prefix`, `strip_suffix` (with `normalizePattern`), or `none`. Use it to make identity values converge when locations use different conventions (`sub-m110` vs `m110`).

## Regex portability

Patterns must behave the same in MATLAB `regexp` and Python `re`. Stay inside this subset:

- Character classes `\d \w \s .`, bracket classes, anchors `^ $`, alternation `|`, groups `( )`, quantifiers `* + ? {n} {n,m}`.
- **Unnamed capture groups only.** Named-group syntax differs (`(?<name>…)` in MATLAB, `(?P<name>…)` in Python).
- No lookbehind, no possessive or atomic groups, no inline flags other than `(?i)`.
- Escape literal dots: `\.tif$`, not `.tif$`.

Template tokens `{token}` are substituted before a pattern is used as a regex; braces containing only digits and commas are quantifiers.
