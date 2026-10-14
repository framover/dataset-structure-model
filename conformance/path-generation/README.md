# path-generation

Generating where a new entity goes (`generate.json`), the inverse of the walk.

What it checks:

- **Templates per level**: `sub-{subject_id}`, then the fixed structural level `data`, then `{session_date}_s{session_number}`. An integer token is written in decimal; a date token as its ISO string.
- **File-level entities**: a `trial` level with `fileSystemType: file` gives a path without a trailing `/`.
- **Round trip**: the listing holds paths generated this way, and the walk reads them back to the same records.
- **Errors**: `name-mismatch` (the generated name fails the level's pattern), `missing-value` (a token has no value), `no-template` (a variable level without `pathComponentTemplate`, here the `dates` level of `dated`), `no-level` (the entity type has no level in the location).
