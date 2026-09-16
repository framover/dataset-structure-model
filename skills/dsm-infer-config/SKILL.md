---
name: dsm-infer-config
description: Infer a Dataset Structure Model (DSM) config from a data directory or a file listing - which folders and files are which entities, and how subject/session/date metadata is read from their names. Use when someone wants a dataset's layout described as a machine-readable config, asks to generate or write a DSM config or dataset-structure-model JSON, wants a session or entity table derived from a folder tree, or needs one description covering a dataset spread across raw and processed locations. The config is verified against the real listing with the `dsm` CLI before it is handed over.
---

# Infer a DSM config from a directory listing

You produce **one JSON file** that validates against `DatasetStructureModel.schema.json` 0.1.0 and describes how an existing dataset is laid out: which path components are which entities, and how metadata is read from their names.

The config is **descriptive**. Record what is there. Never invent a layout, a field the names do not carry, or a tidier convention than the one the dataset uses.

You do not have to guess whether you got it right. Step 8 runs the config back over the real listing and tells you what it found. **Do not hand over a config you have not walked.**

---

## Step 0 - Is DSM the right answer?

Say so and stop if:

- **It is BIDS.** A `dataset_description.json` at the root, or `sub-*/ses-*/` folders. Use `pybids`; it indexes BIDS properly and a DSM config buys nothing.
- **The goal is NWB conversion** and the paths encode only subject, session and time. NeuroConv's `LocalPathExpander` is a shorter road.
- **A database already owns the entities** (DataJoint or similar). DSM describes data nobody will reorganise; it does not replace a pipeline that already has a schema.

DSM is the right answer when the data sits in **more than one place, laid out differently**, or an **entity table** is wanted from a tree nobody will restructure, or **more than one language** has to read the description. `reference/related-work.md` has the full comparison if the user asks why.

## Step 1 - Get the `dsm` CLI

```bash
command -v dsm
```

If it is missing, install it from a clone of the `dataset-structure-model` repository:

```bash
pip install -e /path/to/dataset-structure-model      # or: pipx install /path/to/...
```

Ask the user where the clone is rather than searching the whole disk. A clone also runs without installing, which is the right choice when the repository must not be touched:

```bash
PYTHONPATH=/path/to/dataset-structure-model/src/python python3 -m dsm --help
```

If there is no clone and they do not want one, say plainly that you can write a config but cannot verify it, and that an unverified config is a guess.

## Step 2 - Build a listing

```bash
dsm listing raw main /data/raw -o listing.json
```

Triplets are `LOCATION ROOT DIRECTORY`. Several locations go in **one** listing, because identity has to be consistent across them and that is only checkable together:

```bash
dsm listing raw main /data/raw processed main /data/proc -o listing.json
```

With no filesystem access, one relative path per line in a text file works instead:

```bash
dsm listing raw main paths.txt --text -o listing.json
```

Always build the **full** listing, however large. It costs only paths, and Step 8 needs all of it.

**Write down the identifiers you used.** The `LOCATION` and `ROOT` you type here are what the listing records, and the config's `dataLocations[].identifier` and `rootStoragePaths[].identifier` must be the *same strings*. Choosing prettier names in the config than you typed here means the walk cannot resolve the listing's roots. Pick the names you want in the config first, then build the listing with them.

## Step 3 - Survey the listing, do not read it

Never page through a large listing. Aggregate it:

```bash
python scripts/survey.py listing.json
```

Per location and depth, this prints each **name shape** with its count and examples. Shapes collapse runs of one character class and keep the run lengths: `m110-20250510-001` becomes `A1#3-#8-#3`.

Read the output like this:

- **One shape at a depth, high count** - a clean level. The shape is the `matchPattern`.
- **Two shapes, both with high counts** - usually a structural level beside an entity level, or two entity kinds. Look closer with `--depth N`.
- **A shape with count 1 beside a near-identical high-count shape** - the outlier. Either a stray file to exclude, or the case that breaks a careless pattern. `A1#3-#8-#4_A3.A3` next to `A1#3-#8-#3_A3.A3` is a four-digit running number among three-digit ones: a pattern that does not pin the width will merge them.
- **Extension histogram at file depths** - the raw material for `filePatterns`.

Use `--depth N` to see every name at one depth, and `--loose` to drop run lengths when you want broader families. File depths often explode into dozens of shapes because a parameter in the name varies (`IV(-70mV)`, `IV(-80mV)`, `Cc_step(100pA)`); run `--loose` there first and use the widths view only for the levels you are writing patterns for.

**Read the dataset's own documentation before you decide anything.** A `README`, a data descriptor (`.docx`, `.pdf`, `.md`), a `dataset_description.json` or a `MANIFEST` in the listing was written by the people who made the layout. It usually states what the folder levels are, what each name token means and which subfolders are expected, and that settles most of the semantic questions Step 9 would otherwise put to the user. Read it, quote it in the config's `description` fields, and add an `excludePatterns` entry for it on the level where it sits. Check its claims against the survey; a descriptor that promises a per-entity notes file the listing does not contain is a finding worth reporting.

## Step 4 - Decide what each level is

Walk outward-in. For each depth, in order:

**Is it an entity level or a structural level?** A level is an **entity** level when its name identifies a thing the user would want a row for - a subject, a session, a recording. It is **structural** when it only groups: a date folder, a fixed `data/` or `processed/`, a rig name shared by everything under it.

Omit `entityType` for a structural level. Do not write `"other"`; there is no such entity type. A structural level is still walked and its name is still readable by extraction rules - a date folder's date belongs to the sessions inside it.

When unsure, default to **structural**. A level wrongly made an entity puts a junk row in every table; a level wrongly left structural still yields its metadata.

**Folder level or file level?** Use `fileSystemType: "file"` when many entities' files share one folder, so the entity is identified by the **file name** rather than a folder. A file level must be last. Otherwise the default `folder` is right.

**Fixed-name level?** A level that is the same literal string everywhere (`processed/`) takes `isVariable: false` with `fixedName`, and no `matchPattern`.

A location need not contain every level. If `raw/` has only date and session folders while `processed/` has subject and session folders, say exactly that in each location's layout. Identity reconciles them (Step 5).

## Step 5 - Declare identity

Every `entityType` needs `identifierRef` (or `identifierRefs`). There is **no** fallback to the folder name. Two rules matter more than anything else in this skill:

**1. The identity value must not depend on which location you found it in.** This is the property DSM exists for. If `raw` names a session `2025_05_23_10_00_00_m110-20250523-001` and `processed` names it `session-m110-20250523-001`, both extraction rules must yield `m110-20250523-001`. Get this wrong and the same session becomes two rows that never join - the single worst failure available to you, and silent.

**2. Identity must be stable under names you have not seen.** Identity scoped by a parent is fine (`session_id` unique within a subject); identity that depends on a zero-padding width you happened to observe is not.

Pick the longest substring that is genuinely the identifier and strip decoration: drop a `session-` prefix, drop an acquisition timestamp that is metadata rather than identity. If a folder name is *only* an identifier, `substring` with `":"` takes all of it.

## Step 6 - Write the rules

`metadataMapping` is an array of `{ metadataRef, extraction }`.

**Choosing a method** - simplest that works:

| Situation | Method |
|---|---|
| The value is the whole path component | `substring`, pattern `":"` |
| A fixed-width slice of a fixed-width component | `substring`, e.g. `"0:8"` |
| Position depends on content, or you need part of a group | `regex`, first capture group |
| The value is built from other fields | `template` |
| A constant that is genuinely a property of the location | `fixed` with `value` |

Slices are **Python slices**: `"0:8"`, `"9:"`, `":-4"`, `":"`. Never `"0:end"`. At a file level the slice covers the file name including its extension.

Regex must stay portable: **unnamed groups only**, no lookbehind, no inline flags but `(?i)`. Escape dots. The value is the first capture group, or the whole match when there is none.

**Writing a pattern that generalises.** From the shapes in Step 3:

- Pin a run length you saw consistently: `\d{8}` for a date, `\d{3}` for a running number. This is what keeps `-001` and `-0010` apart.
- Use `+` only where the length genuinely varies across siblings.
- Keep separators literal, escaped where the regex needs it.
- Anchor with `^` and `$`.

Two failure modes, equally bad. **Over-fitting**: `^(m110|m220)$` enumerates today's subjects and breaks on the next one - never enumerate observed values. **Under-fitting**: `^.+$` matches the stray folders too, and the noise lands in the tables.

Dates and times take `valueFormat` in **LDML**: `"yyyyMMdd"`, `"yyyy_MM_dd"`, `"HH_mm_ss"`, `"yyMMdd"`. Only the tokens `yyyy yy MM dd HH mm ss` and quoted literals are portable; a two-digit year lands in 1969–2068. Give a date field `dataType: "date"` so the reader emits ISO 8601.

Reference levels by **name**, not by index. `entityLayoutLevel: null` means the whole relative path.

## Step 7 - File patterns and exclusions

`filePatterns` on a level names the files an entity is expected to have. Candidates are the **direct children** of the entity folder only: a file inside a subfolder of the entity (`<cell>/recordings/*.abf`) cannot be named by a pattern, so completeness cannot be checked for it. Name such subfolders in `additionalFolders` and say in the location's `description` what they hold. Use `{field}` tokens rather than bare substrings - `"^{session_id}_raw\\.tif$"`, not `"raw.tif"` - so membership means "instantiates this template for this entity". Set `isRequired` only where a missing file genuinely means incomplete data, and `cardinality: "one"` only where a second match is an error.

Every entry the survey showed that is not data needs an `excludePatterns` entry on its level: `^\\..*` for dotfiles, and explicit patterns for `temp/`, `scratch/`, `calibration/`, `README.txt`. An excluded entry is accounted for; an unexplained one is a defect you will see in Step 8.

## Step 8 - Verify, and keep going until it is right

```bash
dsm validate config.json
dsm walk config.json listing.json
```

`validate` checks the schema and every cross-reference. `walk` reports what the config actually finds. Read all of it:

- **Entities per type.** Compare against the counts the survey implied. Too few means a pattern is too tight; too many means noise is being counted as data.
- **`(N without a folder or files of their own)`.** An entity inferred from a descendant's name. Correct for a subject that has no folder; a mistake if that subject does have one and your layout missed the level. Such an entity still gets every field you declared for it: a cell's date read from its recording file names lands on the cell record, and a `metadata-conflict` there means its descendants disagree about it.
- **`Unmatched`.** `excluded` is a success - you wrote that rule. `no-match` is unfinished work: the detail names the level that rejected the entry. Drive `no-match` to zero, or be able to say why each remaining one is genuinely not data.
- **Issues.** `missing-required-file` usually means `isRequired` is too strict. `cardinality-violation` means `one` was wrong, or the pattern is catching a backup file. `duplicate-entity` means two folders produced one identity - decide whether they are the same entity or the pattern is too loose. `extraction-failed` means a rule matched nothing.

Then check the thing the report does not print - that entities found in two locations came out as **one** record:

```bash
dsm walk config.json listing.json --json | python -c "
import collections, json, sys
records = json.load(sys.stdin)['records']
counts = collections.Counter(
    (r['entityType'], len({l['dataLocationIdentifier'] for l in r['locations']}))
    for r in records)
for (entity_type, n), count in sorted(counts.items()):
    print(f'{entity_type}: {count} record(s) spanning {n} location(s)')
"
```

If you described two locations that overlap and nothing spans two, your identity rules disagree. Fix them before anything else.

Iterate Steps 4-8 until the counts match the dataset. This loop is the whole reason the config can be trusted.

## Step 9 - Confirm what the listing cannot tell you

Only now, and in one pass, put the **semantic** choices to the user. Show the counts from Step 8 as evidence, and ask about:

- **What the entities are.** You inferred a level is a subject from naming. It could be a rig, a cage, a cohort. Names drive every downstream table.
- **`dataCategory`** per location: `raw`, `processed`, `derived`, `imported`, `reference`, `temporary`, `archive`, `custom`. A folder called `proc/` could be `processed` or `derived`, and `derivedFrom` only makes sense once that is settled.
- **`isPrimary`** - which entity type the dataset is really organised around.
- **`entityRelationships`** - these are semantic, not structural. Only state relations the user confirms.
- **`access`** - `read` unless the user says a tool writes there.
- **Anything with one observed value.** A single rig name in every folder might be a constant or might be the first of five. Ask before writing `fixed`.

Do not ask about layout, patterns or extraction methods. Those you verified in Step 8.

## Hard rules

- **Never emit `function` extractors.** `extractorFunction` is a registry key needing an implementation in every reader. If a value truly cannot be expressed declaratively, say so and leave the field out. Nearly always a regex will do.
- **Never emit DRAFT parts of the schema**: `sourceType` other than `filesystem` (`spreadsheet`, `database`, `api`), the `sidecar` method, and the `filePattern`, `contentPath` and `fileFormat` extraction fields.
- **Never emit `pathTemplate`.** It describes how to *write* new paths, and a read-only listing cannot confirm a write convention. `pathComponentTemplate` is fine where a literal prefix is plainly there (`subject-{subject_id}`).
- **Never emit `preferences`.** It is per-machine and belongs in a `<config>.local.json` overlay.
- **Every object is strict** (`additionalProperties: false`). A key you half-remember is a validation error. There is no `isAvailable`, no `role`, no `groupKey`, no `metadataExtractors`.
- **`metadataDefinitions` is an object** keyed by identifier; `metadataMapping` and `entityTypes` are arrays.
- **Say what you sampled.** If you surveyed rather than inspected every leaf, put that in the location's `description`.

## Reference

- `reference/config-syntax.md` - every key, its required fields, and the eight mistakes that actually happen. Read it before writing the JSON.
- `reference/reader-rules.md` - what a reader does with a config: how entities are grouped, when `files` and `isComplete` appear, how ancestors are inferred, every issue code.
- `scripts/survey.py` - the listing survey from Step 3.
- The schema itself is the final authority and ships with the CLI, so it is readable wherever `dsm` is installed:
  `python -c "from dsm.schemas import schema_path, CONFIG_SCHEMA; print(schema_path(CONFIG_SCHEMA))"`
