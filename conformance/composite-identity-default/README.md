# composite-identity-default

Task runs named BIDS-style, `sub-XX/sub-XX_task-<label>[_run-<index>]_bold.<ext>`, where the run index is written only when a task was run more than once. Subject `01` has `task-rest` with no index and `task-rest_run-02`; subject `02` writes both indices.

What it checks:

- **A `defaultValue` on one part of a composite identity applies before the identity is checked.** `acquisition` is identified by `[task, run]`; `run` has `defaultValue: 1`. The files with no `_run-` are the acquisition `(rest, 1)`, not `no-match`.
- The default and an explicit index are the same value: subject `02`'s `_run-01` files and subject `01`'s index-less files both have `run: 1`.
- The defaulted field appears in `metadata` as a number, and the record carries no issue for it.
- A file-level entity whose patterns use a parent token (`{subject_id}`) and an own token (`{task}`), with the optional index matched by the pattern itself.

A `defaultValue` on a *single-field* identity is refused; see `invalid-identity-default`.
