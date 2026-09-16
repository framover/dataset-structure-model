# flat-session-files

Listing from `conformance/flat-session-files`. Every entity's files sit in one flat folder, so the layout needs a `fileSystemType: "file"` level and identity must come out of the file name.

The case exists for one trap. `m110-20250510-0010_raw.tif` differs from `m110-20250510-001_raw.tif` by one digit. A pattern matched by containment puts both under `m110-20250510-001`; a `{token}` or anchored pattern does not. `pathsMustNotShareRecord` fails any config that groups them — this is the `m1001_s1` vs `m1001_s10` confusion the core decision on file-level grouping was written to prevent.

Graded: two subjects, sessions parented by subject, the four session dates, and the trap.

**Not graded.** Session count is `[4, 5]`: the reference's strict three-digit pattern leaves `-0010` unmatched, while a skill whose pattern accepts a variable digit count makes it a fifth session. Both are defensible; grouping it with `-001` is not.
